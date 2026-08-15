#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import tkinter as tk
from tkinter import Toplevel, Label
from moduli.modello_spesa import SpesaEntry

def avvia_sincronizzazione(self, manuale=False):
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
    if not self._licenza_valida():
        self.show_toast("Funzione disponibile solo con licenza attiva.", duration=3000)
        return
    if manuale:
        if not EMAIL_USER or "@gmail.com" not in EMAIL_USER.lower():
            self.show_custom_warning("Dati Mancanti", "Gmail non valida o mancante!")
            return
        if not APP_PASSWORD or len(APP_PASSWORD.replace(" ", "")) != 16:
            self.show_custom_warning("Dati Mancanti", "Password App Google deve essere di 16 cifre!")
            return
        if not API_KEY:
            self.show_custom_warning("Dati Mancanti", "Chiave API Gemini mancante!")
            return
        if not PAROLE_CHIAVE:
            self.show_custom_warning("Dati Mancanti", "Inserire almeno una Email!")
            return
    kw_data = app_config_globale.get("parole_chiave", [])
    if isinstance(kw_data, str):
        parole_chiave = [k.strip().lower() for k in kw_data.replace(",", " ").split() if k.strip()]
    else:
        parole_chiave = [str(k).strip().lower() for k in kw_data if str(k).strip()]
    if not EMAIL_USER or not APP_PASSWORD or not API_KEY:
        if manuale: self.show_custom_warning("Errore", "Credenziali mancanti!")
        return
    CATEGORIA_TEMPORANEA = "Zona @Web/Bank"
    if CATEGORIA_TEMPORANEA not in self.categorie:
        self.categorie.append(CATEGORIA_TEMPORANEA)
        self.categorie_tipi[CATEGORIA_TEMPORANEA] = "Uscita"
        self.aggiorna_combobox_categorie()
    import time, json, re, imaplib, email
    cartella_pdf = os.path.join(os.getcwd(), "Fatture_GMail")
    if not os.path.exists(cartella_pdf):
        os.makedirs(cartella_pdf)
    try:
        is_iconified = self.wm_state() == 'iconic'
        popup = None
        if not is_iconified:
            popup = Toplevel(self)
            popup.withdraw()
            popup.overrideredirect(True)
            popup.attributes("-topmost", True)
            popup.configure(bg=self.COLOR_WIDGET_BG, highlightbackground=self.COLOR_HIGHLIGHT, highlightthickness=2)
            w, h = 400, 100
            self.update_idletasks()
            win_x = self.winfo_x()
            win_y = self.winfo_y()
            win_w = self.winfo_width()
            win_h = self.winfo_height()
            cx = win_x + (win_w // 2) - (w // 2)
            cy = win_y + (win_h // 2) - (h // 2)
            popup.geometry(f"{w}x{h}+{cx}+{cy}")
            lbl_status = Label(popup, text="Ricerca mail in corso...", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER, font=("Arial", 10, "bold"))
            lbl_status.pack(pady=(10, 4))
            BAR_W, BAR_H = 340, 12
            bar_cv = tk.Canvas(popup, width=BAR_W, height=BAR_H, bg=self.COLOR_HEADER_BG, highlightthickness=0)
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
            lbl_cont = Label(popup, text="In attesa...", bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR)
            lbl_cont.pack(pady=(4, 0))
            popup.deiconify()
            popup.lift()
            popup.focus_force()
            popup.update()
        def aggiorna_UI(testo, val=None, nuovi=None, dettaglio=None):
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
                popup.update()
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, APP_PASSWORD.replace(" ", ""))
        from datetime import datetime, timedelta
        data_limite = (datetime.now() - timedelta(days=30)).strftime("%d-%b-%Y")
        data_it = (datetime.now() - timedelta(days=30)).strftime("%d/%m/%Y")
        status, cartelle = mail.list()
        lista_nomi = str(cartelle)
        nome_cartella = '"[Gmail]/Tutti i messaggi"'
        if "All Mail" in lista_nomi: nome_cartella = '"[Gmail]/All Mail"'
        mail.select(nome_cartella)
        tutti_ids = []
        self.operazioni_scaricate_sessione = 0
        for i, kw in enumerate(parole_chiave):
            kw = kw.strip().lower()
            if not kw: continue
            perc_ricerca = int(((i + 1) / len(parole_chiave)) * 100)
            aggiorna_UI(f"🔍 Ricerca in corso dal {data_it}...", perc_ricerca, dettaglio=kw)
            time.sleep(0.5)
            status, messages = mail.search(None, f'(UNSEEN SINCE "{data_limite}" FROM {kw})')
            if status == 'OK':
                ids_trovati = messages[0].split()
                for m_id in ids_trovati:
                    if m_id not in tutti_ids: 
                        tutti_ids.append(m_id)
        if not tutti_ids:
            if popup: popup.destroy()
            mail.logout()
            return
        client = genai_client.Client(api_key=API_KEY)
        for i, m_id in enumerate(tutti_ids):
            percentuale = int(((i + 1) / len(tutti_ids)) * 100)
            res, data = mail.fetch(m_id, "(BODY[HEADER.FIELDS (SUBJECT)])")
            msg_temp = email.message_from_bytes(data[0][1])
            oggetto = str(msg_temp.get("Subject", "Nessun Oggetto"))
            aggiorna_UI(f"📩 Analisi {i+1}/{len(tutti_ids)}", percentuale, dettaglio=oggetto)
            data_oggi = datetime.now().date()
            res, msg_data = mail.fetch(m_id, "(BODY.PEEK[])")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    oggetto = str(msg.get("Subject", ""))
                    data_dt = data_oggi
                    try:
                        data_dt = email.utils.parsedate_to_datetime(msg.get("Date")).date()
                    except Exception:
                        pass
                    corpo = ""
                    pdf_data = None
                    for part in msg.walk():
                        if part.get_content_type() in ["text/plain", "text/html"]:
                            try:
                                raw = part.get_payload(decode=True).decode(errors='ignore')
                                corpo += re.sub(r'<[^<]+?>', ' ', raw)
                            except: pass
                        elif "pdf" in part.get_content_type():
                            pdf_data = part.get_payload(decode=True)
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
                            for d in json.loads(raw_e):
                                try:
                                    cat_ia = d.get("categoria", "")
                                    cat = cat_ia if cat_ia in self.categorie else "Generica"
                                    data_mov = datetime.strptime(d["data"], "%Y-%m-%d").date()
                                    importo_mov = float(d["importo"])
                                    tipo = "Entrata" if importo_mov >= 0 else "Uscita"
                                    esiste_mov = False
                                    for s in self.spese.get(data_mov, []):
                                        if s[1] == d["desc"] and abs(s[2] - abs(importo_mov)) < 0.01:
                                            esiste_mov = True
                                            break
                                    if not esiste_mov:
                                        self.spese.setdefault(data_mov, []).append(SpesaEntry.nuova(cat, "🤖 " + d["desc"], abs(importo_mov), tipo))
                                        self.operazioni_scaricate_sessione += 1
                                        with open(LOG_IMPORTAZIONI, "a", encoding="utf-8") as log:
                                            log.write(f"{datetime.now().strftime('%d/%m/%Y %H:%M'):<17} | {'ESTRATTO':<8} | {data_mov.strftime('%d/%m/%Y'):<10} | {d['desc']:<50} | {abs(importo_mov):>10.2f} € | {tipo:<7} | {cat}\n")
                                except Exception as _e_mov:
                                    print(f"Movimento estratto scartato (dati incompleti): {_e_mov}")
                                    continue
                            mail.store(m_id, '+FLAGS', '\\Seen')
                            aggiorna_UI(f"📊 Estratto acquisito", percentuale, self.operazioni_scaricate_sessione)
                            time.sleep(5)
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
                        direzione = dati.get("direzione", "Uscita")
                        scadenza_raw = dati.get("scadenza")
                        desc = f"{azienda}"
                        if dati.get("fattura"): desc += f" {dati['fattura']}"
                        if scadenza_raw and scadenza_raw != "null": desc += f" SCD:{scadenza_raw}"
                        esiste = False
                        for d_chiave in self.spese:
                            for s in self.spese[d_chiave]:
                                if s[1] in (desc, f"ALL· {desc}") and abs(s[2] - importo) < 0.01:
                                    esiste = True
                                    break
                            if esiste: break
                        if not esiste:
                            desc_spesa = f"ALL· {desc}" if pdf_data else desc
                            self.spese.setdefault(data_dt, []).append(SpesaEntry.nuova(CATEGORIA_TEMPORANEA, desc_spesa, importo, direzione))
                            self.operazioni_scaricate_sessione += 1
                            with open(LOG_IMPORTAZIONI, "a", encoding="utf-8") as log:
                                log.write(f"{datetime.now().strftime('%d/%m/%Y %H:%M'):<17} | {'MAIL':<8} | {data_dt.strftime('%d/%m/%Y'):<10} | {desc_spesa:<50} | {importo:>10.2f} € | {direzione:<7} | {CATEGORIA_TEMPORANEA}\n")
                            if pdf_data:
                                azienda_safe = re.sub(r'[\\/*?:"<>|]', "-", azienda).strip()
                                fattura_safe = re.sub(r'[\\/*?:"<>|]', "-", str(dati.get('fattura') or 'mancante')).strip()
                                nome_file = f"{data_dt.strftime('%d-%m-%Y')}_{azienda_safe}_fatt_{fattura_safe}.pdf"
                                percorso_completo = os.path.join(cartella_pdf, nome_file)
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
                                    nome_reg = f"{data_ggmmaaaa}_{_san(desc)}_{direzione}_{_san(CATEGORIA_TEMPORANEA)}_{imp_centesimi}.pdf"
                                    shutil.copy2(percorso_completo, os.path.join(DOC_DIR, nome_reg))
                                    try:
                                        with open(REGISTRY_FILE, 'r', encoding='utf-8') as rf:
                                            registry = json.load(rf)
                                    except Exception:
                                        registry = {}
                                    registry[nome_reg] = {
                                        "data_raw":           data_ggmmaaaa,
                                        "categoria_esatta":   CATEGORIA_TEMPORANEA,
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
                                self.lbl_sync_count_widget.config(text=f"📡 Sync {self.operazioni_scaricate_sessione}")
                        mail.store(m_id, '+FLAGS', '\\Seen')
                        if pdf_data:
                            aggiorna_UI(f"ALL· PDF salvato: {azienda}", percentuale, self.operazioni_scaricate_sessione)
                        else:
                            aggiorna_UI(f"✓ OK: {azienda}", percentuale, self.operazioni_scaricate_sessione)
                        time.sleep(5) 
                    except Exception as e_ai:
                        err_msg = str(e_ai)
                        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                            msg_stop = "Limite Giornaliero AI raggiunto."
                            print(msg_stop)
                            aggiorna_UI(msg_stop)
                            self.save_db()
                            if 'mail' in locals():
                                try: mail.logout()
                                except: pass
                            time.sleep(2)
                            if popup: popup.destroy()
                            self.after(0, lambda: self.show_toast("Limite giornaliero AI raggiunto."))
                            return
                        if "503" in err_msg or "UNAVAILABLE" in err_msg:
                            msg_stop = "Gemini sovraccarico (503)"
                            print(msg_stop)
                            aggiorna_UI(msg_stop)
                            self.save_db()
                            if 'mail' in locals():
                                try: mail.logout()
                                except: pass
                            time.sleep(2)
                            if popup: popup.destroy()
                            self.after(0, lambda: self.show_toast("Gemini sovraccarico (503). Riprova tra poco."))
                            return
                        print(f"Errore minore (salto mail): {err_msg}")
                        continue
        mail.logout()
        self.save_db()
        self.refresh_gui()
        if self.operazioni_scaricate_sessione > 0:
            self.riproduci_beep()
        if popup: popup.destroy()
    except Exception as e:
        print(f"Errore Generale: {e}")
        if 'popup' in locals() and popup: popup.destroy()

