#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import threading
import time
import tkinter as tk
from tkinter import Toplevel, Label
from moduli.modello_spesa import SpesaEntry
from moduli.sync_mail_opzioni import (
    leggi_opzioni, leggi_regole, normalizza_mittenti, CAT_BOLLETTE_DEFAULT,
)

_MESI_IMAP = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _data_imap(dt):
    return f"{dt.day:02d}-{_MESI_IMAP[dt.month - 1]}-{dt.year}"

def _decodifica_header(valore, default=""):
    if not valore:
        return default
    try:
        from email.header import decode_header, make_header
        return str(make_header(decode_header(str(valore))))
    except Exception:
        return str(valore)

def _parse_scadenza(testo):
    import datetime as _dt
    if not testo or str(testo).strip().lower() in ("null", "none", ""):
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d"):
        try:
            return _dt.datetime.strptime(str(testo).strip(), fmt).date()
        except ValueError:
            continue
    return None

def _carica_elaborate(percorso):
    try:
        with open(percorso, "r", encoding="utf-8") as f:
            dati = json.load(f)
        return dati if isinstance(dati, dict) else {}
    except Exception:
        return {}

def _salva_elaborate(percorso, elaborate, giorni_conserva):
    import datetime as _dt
    limite = (_dt.datetime.now() - _dt.timedelta(days=giorni_conserva)).isoformat()
    potato = {k: v for k, v in elaborate.items() if str(v) >= limite}
    elaborate.clear()
    elaborate.update(potato)
    try:
        with open(percorso, "w", encoding="utf-8") as f:
            json.dump(elaborate, f, indent=0, ensure_ascii=False)
    except Exception as e:
        print(f"Impossibile salvare l'elenco mail elaborate: {e}")

_SYNC_LOCK = threading.Lock()
_SYNC_STATO = {"in_corso": False, "iniziata": 0.0, "terminata": 0.0,
               "errore": False, "messaggio": ""}

def _sync_imposta(messaggio, errore=False):
    _SYNC_STATO["messaggio"] = messaggio
    _SYNC_STATO["errore"] = errore

def stato_sincronizzazione(app=None):
    s = dict(_SYNC_STATO)
    s["acquisite"] = (getattr(app, "operazioni_scaricate_sessione", 0) or 0) if app is not None else 0
    s["adesso"] = time.time()
    return s

def _prenota():
    if not _SYNC_LOCK.acquire(blocking=False):
        return False
    _SYNC_STATO.update(in_corso=True, iniziata=time.time(), errore=False, messaggio="")
    return True

def _esegui_protetta(self, manuale, mostra_popup=False):
    self.operazioni_scaricate_sessione = 0
    try:
        _avvia_sincronizzazione_interna(self, manuale, mostra_popup)
        if not _SYNC_STATO["messaggio"]:
            n = getattr(self, "operazioni_scaricate_sessione", 0) or 0
            _sync_imposta(f"Completata: {n} nuove operazioni acquisite" if n
                          else "Completata: nessuna nuova operazione", False)
    except Exception as e:
        _sync_imposta(f"Errore: {e}", True)
    finally:
        _SYNC_STATO["terminata"] = time.time()
        _SYNC_STATO["in_corso"] = False
        _SYNC_LOCK.release()

def avvia_in_background(app, mostra_popup=False):
    if not _prenota():
        return False
    try:
        threading.Thread(target=_esegui_protetta, args=(app, False, mostra_popup), daemon=True).start()
    except Exception:
        _SYNC_STATO["in_corso"] = False
        _SYNC_LOCK.release()
        raise
    return True

def avvia_sincronizzazione(self, manuale=False):
    if not _prenota():
        if manuale:
            try:
                self.after(0, lambda: self.show_toast("Sincronizzazione già in corso.", duration=2500))
            except Exception:
                pass
        return
    _esegui_protetta(self, manuale)

def _avvia_sincronizzazione_interna(self, manuale=False, mostra_popup=False):
    import __main__ as _app
    DOC_DIR = _app.DOC_DIR
    REGISTRY_FILE = _app.REGISTRY_FILE
    EMAIL_USER = _app.EMAIL_USER
    APP_PASSWORD = _app.APP_PASSWORD
    API_KEY = _app.API_KEY
    LOG_IMPORTAZIONI = _app.LOG_IMPORTAZIONI
    GEMINI = _app.GEMINI
    PAROLE_CHIAVE = _app.PAROLE_CHIAVE
    app_config_globale = _app.app_config_globale
    genai_client = _app.genai_client
    types = _app.types

    _principale = threading.current_thread() is threading.main_thread()

    def _ui(fn, *a, **kw):
        if _principale:
            return fn(*a, **kw)
        try:
            self.after(0, lambda: fn(*a, **kw))
        except Exception:
            pass

    if not self._licenza_valida():
        _sync_imposta("Funzione disponibile solo con licenza attiva.", True)
        _ui(self.show_toast, "Funzione disponibile solo con licenza attiva.", duration=3000)
        return
    if manuale:
        if not EMAIL_USER or "@gmail.com" not in EMAIL_USER.lower():
            _sync_imposta("Gmail non valida o mancante", True)
            self.show_custom_warning("Dati Mancanti", "Gmail non valida o mancante!")
            return
        if not APP_PASSWORD or len(APP_PASSWORD.replace(" ", "")) != 16:
            _sync_imposta("Password App Google non valida (16 cifre)", True)
            self.show_custom_warning("Dati Mancanti", "Password App Google deve essere di 16 cifre!")
            return
        if not API_KEY:
            _sync_imposta("Chiave API Gemini mancante", True)
            self.show_custom_warning("Dati Mancanti", "Chiave API Gemini mancante!")
            return
        if not PAROLE_CHIAVE:
            _sync_imposta("Nessuna email mittente configurata", True)
            self.show_custom_warning("Dati Mancanti", "Inserire almeno una Email!")
            return
    if not EMAIL_USER or not APP_PASSWORD or not API_KEY:
        _sync_imposta("Credenziali mancanti", True)
        if manuale: self.show_custom_warning("Errore", "Credenziali mancanti!")
        return

    opz = leggi_opzioni(app_config_globale)
    regole = leggi_regole(app_config_globale)
    mappa_regole = {r["mittente"]: r for r in regole}
    parole_chiave = normalizza_mittenti(app_config_globale.get("parole_chiave", []))
    if not parole_chiave:
        _sync_imposta("Nessuna email mittente configurata", True)
        if manuale: self.show_custom_warning("Dati Mancanti", "Inserire almeno una Email!")
        return

    cat_bollette_def = (opz["cat_bollette"] or CAT_BOLLETTE_DEFAULT).strip()
    cat_estratti_def = (opz["cat_estratti"] or "Generica").strip()
    categorie_nuove = []

    def _assicura_categoria(nome, tipo="Uscita"):
        nome = (nome or "").strip()
        if not nome:
            return
        if nome not in self.categorie:
            self.categorie.append(nome)
            self.categorie_tipi[nome] = tipo
            categorie_nuove.append(nome)

    def _tags_regola(regola):
        testo = (regola or {}).get("tag", "")
        if not testo:
            return []
        try:
            return self._normalizza_tags(testo)
        except Exception:
            return []

    import time, re, imaplib, email, email.utils
    from datetime import datetime, timedelta
    cartella_pdf = os.path.join(os.getcwd(), "Fatture_GMail")
    if opz["copia_fatture_gmail"] and not os.path.exists(cartella_pdf):
        os.makedirs(cartella_pdf)
    file_elaborate = _app.MAIL_ELABORATE_FILE
    elaborate = _carica_elaborate(file_elaborate)
    giorni_conserva = max(90, opz["giorni_indietro"] * 2)

    def _log_riga(tipo_log, data_mov, desc, importo, direzione, categoria):
        try:
            with open(LOG_IMPORTAZIONI, "a", encoding="utf-8") as log:
                log.write(f"{datetime.now().strftime('%d/%m/%Y %H:%M'):<17} | {tipo_log:<8} | {data_mov.strftime('%d/%m/%Y'):<10} | {desc:<50} | {_app._fmt_it(abs(importo)):>10} € | {direzione:<7} | {categoria}\n")
        except Exception as e_log:
            print(f"Log importazioni non scritto: {e_log}")

    popup = None
    lbl_status = bar_cv = lbl_cont = None
    _segmenti = []
    BAR_W = BAR_H = 0

    def _main(fn, default=None, timeout=10):
        if _principale:
            return fn()
        fatto = threading.Event()
        out = {}
        def _run():
            try:
                out["v"] = fn()
            except Exception as e_run:
                out["e"] = e_run
            finally:
                fatto.set()
        try:
            self.after(0, _run)
        except Exception:
            return default
        if not fatto.wait(timeout):
            return default
        if "e" in out:
            raise out["e"]
        return out.get("v", default)

    def _distruggi(p):
        try:
            p.destroy()
        except Exception:
            pass

    def _chiudi_popup():
        p = popup
        if not p:
            return
        if _principale:
            _distruggi(p)
        else:
            try:
                self.after(0, lambda: _distruggi(p))
            except Exception:
                pass

    try:
        if _principale:
            is_iconified = self.wm_state() == 'iconic'
        elif mostra_popup:
            is_iconified = bool(_main(lambda: self.wm_state() == 'iconic', True))
        else:
            is_iconified = True

        def _crea_popup():
            nonlocal popup, lbl_status, bar_cv, lbl_cont, BAR_W, BAR_H, _segmenti
            popup = Toplevel(self)
            popup.withdraw()
            popup.overrideredirect(True)
            popup.attributes("-topmost", True)
            popup.configure(bg=self.COLOR_HIGHLIGHT)
            corpo_popup = tk.Frame(popup, bg=self.COLOR_WIDGET_BG)
            corpo_popup.pack(fill="both", expand=True, padx=1, pady=1)
            w, h = 400, 100
            self.update_idletasks()
            win_x = self.winfo_x()
            win_y = self.winfo_y()
            win_w = self.winfo_width()
            win_h = self.winfo_height()
            cx = win_x + (win_w // 2) - (w // 2)
            cy = win_y + (win_h // 2) - (h // 2)
            popup.geometry(f"{w}x{h}+{cx}+{cy}")
            lbl_status = Label(corpo_popup, text="Ricerca mail in corso...", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER, font=("Arial", 10, "bold"))
            lbl_status.pack(pady=(10, 4))
            BAR_W, BAR_H = 340, 12
            bar_cv = tk.Canvas(corpo_popup, width=BAR_W, height=BAR_H, bg=self.COLOR_HEADER_BG, highlightthickness=0)
            bar_cv.pack(pady=2)
            _segmenti = []
            _colori_base = []
            for i in range(BAR_W):
                t = i / BAR_W
                if t < 0.5:
                    t2 = t / 0.5
                    r = int(0x00 + (0xFF - 0x00) * t2)
                    g = int(0xC8 + (0xD7 - 0xC8) * t2)
                    b = 0x00
                else:
                    t2 = (t - 0.5) / 0.5
                    r = int(0xFF + (0xE0 - 0xFF) * t2)
                    g = int(0xD7 + (0x6C - 0xD7) * t2)
                    b = int(0x00 + (0x75 - 0x00) * t2)
                _colori_base.append((r, g, b))
                seg = bar_cv.create_rectangle(i, 0, i+1, BAR_H, fill=f"#{r:02x}{g:02x}{b:02x}", outline="", state="hidden")
                _segmenti.append(seg)
            lbl_cont = Label(corpo_popup, text="In attesa...", bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR)
            lbl_cont.pack(pady=(4, 0))
            popup.deiconify()
            popup.lift()
            popup.focus_force()
            popup.update() if _principale else popup.update_idletasks()
        if not is_iconified:
            if _principale:
                _crea_popup()
            else:
                try:
                    _main(_crea_popup)
                except Exception as e_pop:
                    print(f"Popup di avanzamento non creato: {e_pop}")
                    _chiudi_popup()
                    is_iconified = True
        def _aggiorna_UI_main(testo, val=None, nuovi=None, dettaglio=None):
            if is_iconified: return
            if popup and popup.winfo_exists():
                lbl_status.config(text=testo)
                if val is not None:
                    soglia = int(BAR_W * max(0.0, min(val, 100.0)) / 100.0)
                    for idx, seg in enumerate(_segmenti):
                        bar_cv.itemconfig(seg, state="normal" if idx < soglia else "hidden")
                if dettaglio is not None:
                    testo_pulito = str(dettaglio).strip()
                    if len(testo_pulito) > 50:
                        testo_pulito = testo_pulito[:47] + "..."
                    lbl_cont.config(text=testo_pulito)
                elif nuovi is not None:
                    lbl_cont.config(text=f"✓ Acquisite: {nuovi}")
                popup.update() if _principale else popup.update_idletasks()
        def aggiorna_UI(testo, val=None, nuovi=None, dettaglio=None):
            if is_iconified: return
            if _principale:
                _aggiorna_UI_main(testo, val, nuovi, dettaglio)
                return
            def _sicuro():
                try:
                    _aggiorna_UI_main(testo, val, nuovi, dettaglio)
                except Exception:
                    pass
            try:
                self.after(0, _sicuro)
            except Exception:
                pass

        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, APP_PASSWORD.replace(" ", ""))
        data_inizio = datetime.now() - timedelta(days=opz["giorni_indietro"])
        data_limite = _data_imap(data_inizio)
        data_it = data_inizio.strftime("%d/%m/%Y")
        status, cartelle = mail.list()
        lista_nomi = str(cartelle)
        nome_cartella = '"[Gmail]/Tutti i messaggi"'
        if "All Mail" in lista_nomi: nome_cartella = '"[Gmail]/All Mail"'
        esito_sel, _ = mail.select(nome_cartella)
        if esito_sel != 'OK':
            mail.select("INBOX")
        tutti_ids = []
        id_mittente = {}
        self.operazioni_scaricate_sessione = 0
        criterio_base = ("UNSEEN " if opz["solo_non_lette"] else "") + f'SINCE "{data_limite}"'
        for i, kw in enumerate(parole_chiave):
            kw = kw.strip().lower()
            if not kw: continue
            perc_ricerca = int(((i + 1) / len(parole_chiave)) * 100)
            aggiorna_UI(f"🔍 Ricerca in corso dal {data_it}...", perc_ricerca, dettaglio=kw)
            time.sleep(0.5)
            kw_q = kw.replace("\\", "").replace('"', "")
            status, messages = mail.search(None, f'({criterio_base} FROM "{kw_q}")')
            if status == 'OK':
                ids_trovati = messages[0].split()
                for m_id in ids_trovati:
                    if m_id not in tutti_ids:
                        tutti_ids.append(m_id)
                        id_mittente[m_id] = kw
            else:
                print(f"Ricerca IMAP non riuscita per '{kw}': {status} {messages}")
        if not tutti_ids:
            _chiudi_popup()
            mail.logout()
            return
        client = genai_client.Client(api_key=API_KEY)
        for i, m_id in enumerate(tutti_ids):
            percentuale = int(((i + 1) / len(tutti_ids)) * 100)
            regola = mappa_regole.get(id_mittente.get(m_id, ""), {})
            res, data = mail.fetch(m_id, "(BODY.PEEK[HEADER.FIELDS (SUBJECT MESSAGE-ID)])")
            raw_h = data[0][1] if data and isinstance(data[0], tuple) else b""
            msg_temp = email.message_from_bytes(raw_h)
            oggetto = _decodifica_header(msg_temp.get("Subject"), "Nessun Oggetto")
            message_id = str(msg_temp.get("Message-ID") or "").strip()
            if message_id and message_id in elaborate:
                continue
            aggiorna_UI(f"📩 Analisi {i+1}/{len(tutti_ids)}", percentuale, dettaglio=oggetto)
            data_oggi = datetime.now().date()
            res, msg_data = mail.fetch(m_id, "(BODY.PEEK[])")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    oggetto = _decodifica_header(msg.get("Subject"), "")
                    data_mail = data_oggi
                    try:
                        data_mail = email.utils.parsedate_to_datetime(msg.get("Date")).date()
                    except Exception:
                        pass
                    corpo = ""
                    pdf_data = None
                    for part in msg.walk():
                        ctype = part.get_content_type()
                        nome_all = (part.get_filename() or "").lower()
                        if ctype in ["text/plain", "text/html"] and not nome_all:
                            try:
                                raw = part.get_payload(decode=True).decode(errors='ignore')
                                corpo += re.sub(r'<[^<]+?>', ' ', raw)
                            except Exception: pass
                        elif "pdf" in ctype or nome_all.endswith(".pdf"):
                            pdf_data = part.get_payload(decode=True)
                    def _chiudi_mail():
                        if opz["segna_letta"]:
                            mail.store(m_id, '+FLAGS', '\\Seen')
                        if message_id:
                            elaborate[message_id] = datetime.now().isoformat()
                            _salva_elaborate(file_elaborate, elaborate, giorni_conserva)
                    try:
                        is_estratto = False
                        if pdf_data:
                            r_check = client.models.generate_content(
                                model=GEMINI,
                                contents=[
                                    types.Part.from_bytes(data=pdf_data, mime_type="application/pdf"),
                                    "Questo PDF è un estratto conto bancario con più movimenti? Rispondi SOLO: SI oppure NO."
                                ]
                            )
                            is_estratto = "SI" in r_check.text.strip().upper()
                        if is_estratto:
                            lista_cat = ", ".join(f'"{c}"' for c in self.categorie)
                            regola_cat = (
                                f"4. Assegna a ogni movimento la categoria più adatta tra: [{lista_cat}]. "
                                "Se nessuna corrisponde, proponi una categoria sintetica in italiano."
                            )
                            r_estratto = client.models.generate_content(
                                model=GEMINI,
                                contents=[
                                    types.Part.from_bytes(data=pdf_data, mime_type="application/pdf"),
                                    (
                                        "Analizza questo estratto conto e convertilo in JSON.\n"
                                        "REGOLE:\n1. Identifica Data, Descrizione e Importo.\n"
                                        '2. Restituisci SOLO un array JSON: [{"data": "YYYY-MM-DD", "desc": "stringa", "importo": float, "categoria": "stringa"}].\n'
                                        f"3. Negativi = uscite, Positivi = entrate.\n{regola_cat}"
                                    )
                                ]
                            )
                            raw_e = r_estratto.text.strip()
                            if "```json" in raw_e: raw_e = raw_e.split("```json")[1].split("```")[0].strip()
                            elif "```" in raw_e: raw_e = raw_e.split("```")[1].split("```")[0].strip()
                            cat_ripiego = (regola.get("categoria") or cat_estratti_def).strip()
                            conto_estr = regola.get("conto") or opz["conto_estratti"]
                            metodo_estr = regola.get("metodo") or opz["metodo_estratti"]
                            tag_estr = _tags_regola(regola) or _tags_regola({"tag": opz["tag_estratti"]})
                            for d in json.loads(raw_e):
                                try:
                                    importo_mov = float(d["importo"])
                                    tipo = "Entrata" if importo_mov >= 0 else "Uscita"
                                    cat_ia = d.get("categoria", "")
                                    cat = cat_ia if cat_ia in self.categorie else cat_ripiego
                                    _assicura_categoria(cat, tipo)
                                    data_mov = datetime.strptime(d["data"], "%Y-%m-%d").date()
                                    esiste_mov = False
                                    if opz["controllo_doppioni"]:
                                        for s in self.spese.get(data_mov, []):
                                            if s[1] in (d["desc"], "🤖 " + d["desc"]) and abs(s[2] - abs(importo_mov)) < 0.01:
                                                esiste_mov = True
                                                break
                                    if not esiste_mov:
                                        self.spese.setdefault(data_mov, []).append(SpesaEntry.nuova(
                                            cat, "🤖 " + d["desc"], abs(importo_mov), tipo,
                                            conto=conto_estr, metodo_pagamento=metodo_estr, hashtag=list(tag_estr)))
                                        self.operazioni_scaricate_sessione += 1
                                        _log_riga("ESTRATTO", data_mov, d["desc"], importo_mov, tipo, cat)
                                except Exception as _e_mov:
                                    print(f"Movimento estratto scartato (dati incompleti): {_e_mov}")
                                    continue
                            if opz["copia_fatture_gmail"]:
                                try:
                                    mitt_safe = re.sub(r'[\\/*?:"<>|@]', "-", id_mittente.get(m_id, "") or "mittente").strip()
                                    base_nome = f"{data_mail.strftime('%d-%m-%Y')}_ESTRATTO_{mitt_safe}"
                                    percorso_estr = os.path.join(cartella_pdf, base_nome + ".pdf")
                                    n_copia = 2
                                    while os.path.exists(percorso_estr):
                                        percorso_estr = os.path.join(cartella_pdf, f"{base_nome}_{n_copia}.pdf")
                                        n_copia += 1
                                    with open(percorso_estr, "wb") as f_estr:
                                        f_estr.write(pdf_data)
                                    print(f"Estratto salvato: {os.path.basename(percorso_estr)}")
                                except Exception as e_pdf_estr:
                                    print(f"Salvataggio PDF estratto fallito: {e_pdf_estr}")
                            _chiudi_mail()
                            aggiorna_UI("📊 Estratto acquisito", percentuale, self.operazioni_scaricate_sessione)
                            time.sleep(opz["pausa_sec"])
                            continue
                        prompt = f"""Analizza questa mail/bolletta. 
                        Le parole chiave di riferimento sono: {', '.join(parole_chiave)}.
                        Estrai in JSON:
                        {{"importo": float, "azienda": "nome", "fattura": "numero", "direzione": "Entrata/Uscita", "scadenza": "GG/MM/YYYY o null"}}
                        REGOLE: 
                        1. Se non trovi l'importo, scrivi 0.01. 
                        2. Determina Entrata/Uscita. 
                        3. Il campo "azienda" deve contenere SOLO il nome, senza icone, emoji o prefissi tipo '🤖'."""
                        response = client.models.generate_content(
                            model=GEMINI,
                            contents=[prompt, f"Oggetto: {oggetto}\nCorpo: {corpo}"] + 
                                     ([types.Part.from_bytes(data=pdf_data, mime_type="application/pdf")] if pdf_data else [])
                        )
                        res_text = response.text.strip().replace("```json", "").replace("```", "")
                        dati = json.loads(res_text)
                        importo = float(dati.get("importo") or 0.01)
                        azienda = dati.get("azienda") or "Fattura"
                        direzione_raw = dati.get("direzione") or "Uscita"
                        _dir = str(direzione_raw).strip().lower()
                        direzione = "Entrata" if (_dir.startswith("entr") and "uscit" not in _dir) else "Uscita"
                        if regola.get("tipo") in ("Entrata", "Uscita"):
                            direzione = regola["tipo"]
                        scadenza_raw = dati.get("scadenza")
                        scadenza_dt = _parse_scadenza(scadenza_raw)
                        data_dt = data_mail
                        if opz["data_movimento"] == "oggi":
                            data_dt = data_oggi
                        elif opz["data_movimento"] == "scadenza" and scadenza_dt:
                            data_dt = scadenza_dt
                        desc = f"{azienda}"
                        if dati.get("fattura"): desc += f" {dati['fattura']}"
                        if scadenza_raw and scadenza_raw != "null": desc += f" SCD:{scadenza_raw}"
                        if importo <= 0.011 and opz["importo_mancante"] == "salta":
                            _log_riga("SALTATA", data_dt, desc, 0.0, direzione, "importo non trovato")
                            if message_id:
                                elaborate[message_id] = datetime.now().isoformat()
                                _salva_elaborate(file_elaborate, elaborate, giorni_conserva)
                            aggiorna_UI(f"⏭ Importo non trovato: {azienda}", percentuale, self.operazioni_scaricate_sessione)
                            time.sleep(opz["pausa_sec"])
                            continue
                        categoria = (regola.get("categoria") or cat_bollette_def).strip()
                        esiste = False
                        if opz["controllo_doppioni"]:
                            for d_chiave in self.spese:
                                for s in self.spese[d_chiave]:
                                    if s[1] in (desc, f"ALL· {desc}") and abs(s[2] - abs(importo)) < 0.01:
                                        esiste = True
                                        break
                                if esiste: break
                        if not esiste:
                            _assicura_categoria(categoria, direzione)
                            desc_spesa = f"ALL· {desc}" if pdf_data else desc
                            self.spese.setdefault(data_dt, []).append(SpesaEntry.nuova(
                                categoria, desc_spesa, abs(importo), direzione,
                                conto=regola.get("conto", ""), metodo_pagamento=regola.get("metodo", ""),
                                hashtag=_tags_regola(regola)))
                            self.operazioni_scaricate_sessione += 1
                            _log_riga("MAIL", data_dt, desc_spesa, importo, direzione, categoria)
                            if pdf_data:
                                azienda_safe = re.sub(r'[\\/*?:"<>|]', "-", azienda).strip()
                                fattura_safe = re.sub(r'[\\/*?:"<>|]', "-", str(dati.get('fattura') or 'mancante')).strip()
                                nome_file = f"{data_dt.strftime('%d-%m-%Y')}_{azienda_safe}_fatt_{fattura_safe}.pdf"
                                percorso_completo = os.path.join(cartella_pdf, nome_file)
                                if opz["copia_fatture_gmail"]:
                                    with open(percorso_completo, "wb") as f:
                                        f.write(pdf_data)
                                    print(f"File salvato: {nome_file}")
                                try:
                                    if not os.path.exists(DOC_DIR):
                                        os.makedirs(DOC_DIR)
                                    data_ggmmaaaa = data_dt.strftime("%d%m%Y")
                                    imp_centesimi = int(round(importo * 100))
                                    def _san(s, n=30):
                                        return re.sub(r'[^\w\.-]', '', s.strip().replace(' ', '_').upper())[:n]
                                    nome_reg = f"{data_ggmmaaaa}_{_san(desc)}_{direzione}_{_san(categoria)}_{imp_centesimi}.pdf"
                                    with open(os.path.join(DOC_DIR, nome_reg), "wb") as f:
                                        f.write(pdf_data)
                                    try:
                                        with open(REGISTRY_FILE, 'r', encoding='utf-8') as rf:
                                            registry = json.load(rf)
                                    except Exception:
                                        registry = {}
                                    registry[nome_reg] = {
                                        "data_raw":           data_ggmmaaaa,
                                        "categoria_esatta":   categoria,
                                        "descrizione_esatta": f"ALL· {desc}",
                                        "importo_raw":        imp_centesimi,
                                        "tipo_esatto":        direzione,
                                        "timestamp":          datetime.now().isoformat()
                                    }
                                    with open(REGISTRY_FILE, 'w', encoding='utf-8') as rf:
                                        json.dump(registry, rf, indent=4, ensure_ascii=False)
                                    print(f"Documento registrato: {nome_reg}")
                                except Exception as e_reg:
                                    print(f"Registrazione documento fallita: {e_reg}")
                            if hasattr(self, 'lbl_sync_count_widget'):
                                _ui(self.lbl_sync_count_widget.config, text=f"📡 Sync {self.operazioni_scaricate_sessione}")
                        _chiudi_mail()
                        if pdf_data:
                            aggiorna_UI(f"ALL· PDF salvato: {azienda}", percentuale, self.operazioni_scaricate_sessione)
                        else:
                            aggiorna_UI(f"✓ OK: {azienda}", percentuale, self.operazioni_scaricate_sessione)
                        time.sleep(opz["pausa_sec"])
                    except Exception as e_ai:
                        err_msg = str(e_ai)
                        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                            msg_stop = "Limite Giornaliero AI raggiunto."
                            _sync_imposta(msg_stop, True)
                            print(msg_stop)
                            aggiorna_UI(msg_stop)
                            _ui(self.save_db)
                            if categorie_nuove:
                                _ui(self.aggiorna_combobox_categorie)
                            try: mail.logout()
                            except Exception: pass
                            time.sleep(2)
                            _chiudi_popup()
                            _ui(self.show_toast, "Limite giornaliero AI raggiunto.")
                            return
                        if "503" in err_msg or "UNAVAILABLE" in err_msg:
                            msg_stop = "Gemini sovraccarico (503)"
                            _sync_imposta(msg_stop, True)
                            print(msg_stop)
                            aggiorna_UI(msg_stop)
                            _ui(self.save_db)
                            if categorie_nuove:
                                _ui(self.aggiorna_combobox_categorie)
                            try: mail.logout()
                            except Exception: pass
                            time.sleep(2)
                            _chiudi_popup()
                            _ui(self.show_toast, "Gemini sovraccarico (503). Riprova tra poco.")
                            return
                        print(f"Errore minore (salto mail): {err_msg}")
                        continue
        mail.logout()
        if categorie_nuove:
            _ui(self.aggiorna_combobox_categorie)
        _ui(self.save_db)
        _ui(self.refresh_gui)
        if self.operazioni_scaricate_sessione > 0:
            _ui(self.riproduci_beep)
        _chiudi_popup()
    except Exception as e:
        print(f"Errore Generale: {e}")
        _sync_imposta(f"Errore: {e}", True)
        _chiudi_popup()
