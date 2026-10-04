#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
import threading
import time
import tkinter as tk
from tkinter import filedialog

from moduli.spinner_animato import crea_spinner_animato

class _QuotaGiornaliera(Exception):
    pass

def _attesa_quota(msg):
    m = re.search(r"riprova tra ([0-9hms]+)", msg)
    return f"Riprova tra {m.group(1)}." if m else "Riprova domani o abilita la fatturazione su ai.google.dev."

def _estrai_json(raw):
    raw = (raw or "").strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
    try:
        return json.loads(raw)
    except Exception:
        i, j = raw.find("["), raw.rfind("]")
        if i != -1 and j > i:
            return json.loads(raw[i:j + 1])
        raise

# Importazione universale IA: invia CSV o PDF a Gemini che estrae i movimenti e apre la finestra di revisione
def apri_finestra_importa(self, path=None):
    import __main__ as _app
    API_KEY = _app.API_KEY
    GEMINI = _app.GEMINI
    genai = _app.genai
    types = _app.types
    if not self._licenza_valida():
        self.show_toast("Funzione disponibile solo con licenza attiva.", duration=3000)
        return
    from datetime import datetime
    if getattr(self, "_importa_in_corso", False):
        self.show_toast("Importazione già in corso.", duration=3000)
        return
    for _w in self.winfo_children():
        try:
            if isinstance(_w, tk.Toplevel) and _w.title() == "Revisione Movimenti IA Gemini":
                _w.deiconify()
                _w.lift()
                _w.focus_force()
                self.show_toast("Chiudi prima la finestra di revisione aperta.", duration=3000)
                return
        except Exception:
            pass
    if not API_KEY:
        self.show_custom_warning("Configurazione AI Necessaria",
            "L'Analisi Smart richiede una chiave API Gemini (gratuita).\n\n"
            "Vai nella sezione Impostazioni e clicca sul pulsante 'Ottieni'.\n")
        return
    if not path:
        path = filedialog.askopenfilename(
            title="Importazione Universale IA",
            filetypes=[
                ("File Supportati", "*.csv *.pdf *.png *.jpg *.jpeg *.webp"),
                ("File CSV", "*.csv"),
                ("File PDF", "*.pdf"),
                ("Immagini", "*.png *.jpg *.jpeg *.webp")
            ]
        )
    if not path: return
    self._importa_in_corso = True
    attesa = tk.Toplevel(self)
    def _fine_attesa(e):
        if e.widget is attesa:
            self._importa_in_corso = False
    attesa.bind("<Destroy>", _fine_attesa)
    attesa.withdraw()
    attesa.overrideredirect(True)
    attesa.configure(background=self.COLOR_WIDGET_BG)
    attesa.resizable(False, False)
    l_att, h_att = 300, 90
    x_att = (attesa.winfo_screenwidth() // 2) - (l_att // 2)
    y_att = (attesa.winfo_screenheight() // 2) - (h_att // 2)
    attesa.geometry(f"{l_att}x{h_att}+{x_att}+{y_att}")
    frame_a = tk.Frame(attesa, bg=self.COLOR_WIDGET_BG,
                       highlightbackground=self.COLOR_HIGHLIGHT, highlightthickness=1)
    frame_a.pack(expand=True, fill="both")
    inner = tk.Frame(frame_a, bg=self.COLOR_WIDGET_BG)
    inner.pack(expand=True)
    cvs, _ = crea_spinner_animato(inner, self.COLOR_WIDGET_BG, size=28, tick_ms=30)
    cvs.pack(side="left", padx=(0, 8))
    tk.Label(inner, text="Gemini sta analizzando...",
             font=("Segoe UI", 9, "bold"),
             bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HIGHLIGHT).pack(side="left")
    attesa.deiconify()
    def _chiudi_attesa():
        try:
            if attesa.winfo_exists():
                attesa.destroy()
        except Exception:
            pass
    def _apri_revisione(movimenti):
        try:
            self.apri_finestra_revisione_universale(movimenti)
        except Exception as e_rev:
            self.show_custom_warning("Errore", f"Impossibile aprire la revisione:\n{str(e_rev)[:200]}")
    def elabora_ia():
        try:
            try:
                client = genai.Client(api_key=API_KEY,
                                      http_options=types.HttpOptions(timeout=120000))
            except Exception:
                client = genai.Client(api_key=API_KEY)
            _mime = "application/json"
            _cfgs = []
            try:
                _m_ver = re.search(r"gemini-(\d+)(?:\.(\d+))?", str(GEMINI).lower())
                _maj = int(_m_ver.group(1)) if _m_ver else 0
                _min = int(_m_ver.group(2) or 0) if _m_ver else 0
                if _maj >= 3:
                    for _lv in ("minimal", "low"):
                        _cfgs.append(types.GenerateContentConfig(
                            response_mime_type=_mime,
                            thinking_config=types.ThinkingConfig(thinking_level=_lv)))
                elif _maj == 2 and _min >= 5:
                    _cfgs.append(types.GenerateContentConfig(
                        response_mime_type=_mime,
                        thinking_config=types.ThinkingConfig(thinking_budget=0)))
            except Exception:
                _cfgs = []
            _cfgs.append(types.GenerateContentConfig(response_mime_type=_mime))
            _cfg = {"i": 0}
            def _chiedi(contents, etichetta):
                ultimo = None
                tentativi = 0
                while tentativi < 3:
                    try:
                        risposta = client.models.generate_content(
                            model=GEMINI, contents=contents, config=_cfgs[_cfg["i"]])
                        return _estrai_json(risposta.text)
                    except Exception as e_ia:
                        ultimo = e_ia
                        _m_att = re.search(r"retry in (\d+h[0-9hms.]*)", str(e_ia))
                        if "429" in str(e_ia) and (_m_att or "PerDay" in str(e_ia)):
                            raise _QuotaGiornaliera(
                                "429 quota giornaliera Gemini esaurita" +
                                (f" (riprova tra {_m_att.group(1).split('.')[0]}s)" if _m_att else ""))
                        if "400" in str(e_ia) or "INVALID_ARGUMENT" in str(e_ia):
                            if _cfg["i"] < len(_cfgs) - 1:
                                _cfg["i"] += 1
                                continue
                            break
                        tentativi += 1
                        if tentativi < 3:
                            time.sleep(3 * tentativi)
                raise ultimo
            estensione = os.path.splitext(path)[1].lower()

            lista_cat = ", ".join(f'"{c}"' for c in self.categorie) if self.categorie else "Generica"
            regola_cat = (
                f"Assegna a ogni movimento la categoria più adatta scegliendo SOLO tra: [{lista_cat}]. "
                "Se nessuna corrisponde usa 'Generica'."
            )
            prompt_testo = (
                f"Analizza questo documento e convertilo in JSON.\n"
                f"REGOLE:\n"
                f"1. Determina se il documento è un DOCUMENTO SINGOLO (fattura, ricevuta, "
                f"bolletta, cedolino, pensione, busta paga: un solo importo da pagare o "
                f"ricevere, anche se mostra voci di dettaglio, trattenute o imposte) oppure "
                f"un ESTRATTO (lista di movimenti bancari o più transazioni distinte).\n"
                f"2. Se ESTRATTO o LISTA MOVIMENTI: ogni movimento separato, "
                f"importo negativo per uscite e positivo per entrate.\n"
                f"3. Se DOCUMENTO SINGOLO: una sola voce con il totale o l'importo netto finale "
                f"(non elencare le singole voci di dettaglio), "
                f"descrizione = nome fornitore, importo sempre negativo (uscita), "
                f"estrai anche numero fattura (campo fattura) e scadenza fattura(GG-MM-AAAA o null). "
                f"Se nel documento compaiono più date etichettate 'scadenza' (es. scadenza del "
                f"pagamento dovuto E scadenza di un'offerta/contratto/promozione), usa SOLO la "
                f"scadenza dell'importo da pagare indicato in bolletta, ignorando le altre.\n"
                f"4. Se la data non è leggibile usa la data di oggi.\n"
                f"5. {regola_cat}\n"
                f"6. Restituisci SOLO un array JSON dove il PRIMO elemento ha anche "
                f'il campo \"tipo_documento\": \"fattura\" oppure \"estratto\": '
                f'[{{"tipo_documento": "fattura|estratto", "data": "YYYY-MM-DD", "desc": "stringa", '
                f'"importo": float, "categoria": "stringa", '
                f'"fattura": "stringa o null", "scadenza": "GG-MM-AAAA o null"}}].'
            )
            if estensione == ".pdf":
                with open(path, "rb") as f:
                    doc_data = f.read()
                prompt = [
                    types.Part.from_bytes(data=doc_data, mime_type="application/pdf"),
                    prompt_testo
                ]
            elif estensione in (".png", ".jpg", ".jpeg", ".webp"):
                mime_map = {".png": "image/png", ".jpg": "image/jpeg",
                            ".jpeg": "image/jpeg", ".webp": "image/webp"}
                with open(path, "rb") as f:
                    img_data = f.read()
                prompt = [
                    types.Part.from_bytes(data=img_data, mime_type=mime_map[estensione]),
                    prompt_testo
                ]
            else:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        righe = f.readlines()
                except Exception:
                    with open(path, "r", encoding="latin-1") as f:
                        righe = f.readlines()
                if not righe:
                    raise ValueError("Il file CSV è vuoto o illeggibile.")
                intestazione_csv = righe[0]
                righe_dati = righe[1:]
                RECENTI_PRIMA = True
                def _data_riga(riga):
                    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", riga)
                    if m:
                        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
                    m = re.search(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})", riga)
                    if m:
                        return (int(m.group(3)), int(m.group(2)), int(m.group(1)))
                    return None
                _chiavi = [_data_riga(_r) for _r in righe_dati]
                righe_future = 0
                if righe_dati and all(_k is not None for _k in _chiavi):
                    _oggi = datetime.now().date()
                    _coppie = [(_k, _r) for _k, _r in zip(_chiavi, righe_dati)
                               if _k <= (_oggi.year, _oggi.month, _oggi.day)]
                    righe_future = len(righe_dati) - len(_coppie)
                    righe_dati = [_r for _, _r in sorted(
                        _coppie, key=lambda t: t[0], reverse=RECENTI_PRIMA)]
                DIMENSIONE_BLOCCO_CSV = 100
                blocchi_csv = [
                    righe_dati[i:i + DIMENSIONE_BLOCCO_CSV]
                    for i in range(0, len(righe_dati), DIMENSIONE_BLOCCO_CSV)
                ] or [[]]
                dati_csv = []
                blocchi_falliti = []
                quota_msg = None
                righe_elaborate = 0
                for indice_blocco, blocco in enumerate(blocchi_csv, start=1):
                    if not blocco:
                        continue
                    campione_blocco = intestazione_csv + "".join(blocco)
                    prompt_blocco = (
                        f"Analizza queste righe di un CSV bancario e convertile in JSON.\n"
                        f"REGOLE:\n"
                        f"1. Identifica Data, Descrizione e Importo.\n"
                        f"2. Negativi = uscite, Positivi = entrate.\n"
                        f"3. {regola_cat}\n"
                        f"4. Restituisci SOLO un array JSON, senza testo attorno: "
                        f'[{{"data": "YYYY-MM-DD", "desc": "stringa", "importo": float, "categoria": "stringa"}}].\n'
                        f"CAMPIONE:\n{campione_blocco}"
                    )
                    try:
                        dati_blocco = _chiedi(prompt_blocco, f"CSV blocco {indice_blocco}")
                    except _QuotaGiornaliera as e_q:
                        quota_msg = str(e_q)
                        blocchi_falliti.extend(range(indice_blocco, len(blocchi_csv) + 1))
                        break
                    except Exception:
                        dati_blocco = None
                    if dati_blocco is None:
                        blocchi_falliti.append(indice_blocco)
                        continue
                    dati_csv.extend(dati_blocco)
                    righe_elaborate += len(blocco)
                movimenti = []
                righe_scartate = 0
                for d in dati_csv:
                    try:
                        desc = d["desc"]
                        fattura  = d.get("fattura")
                        scadenza = d.get("scadenza")
                        if fattura and str(fattura).lower() not in ("null", "", "none"):
                            desc += f" {fattura}"
                        if scadenza and str(scadenza).lower() not in ("null", "", "none"):
                            desc += f" SCD:{scadenza}"
                        movimenti.append({
                            "data":        datetime.strptime(d["data"], "%Y-%m-%d").date(),
                            "descrizione": desc,
                            "importo":     float(str(d["importo"]).replace(",", ".")),
                            "categoria":   d.get("categoria", "Generica")
                        })
                    except Exception as _e_r:
                        righe_scartate += 1
                        continue
                _n_tot = len(movimenti)
                movimenti = [m for m in movimenti if m["data"] <= datetime.now().date()]
                righe_future += _n_tot - len(movimenti)
                self.after(0, lambda: attesa.destroy() if attesa.winfo_exists() else None)
                if quota_msg and not movimenti:
                    _att = _attesa_quota(quota_msg)
                    self.after(0, lambda a=_att: self.show_custom_warning(
                        "Errore IA", "Quota giornaliera Gemini esaurita.\n" + a))
                    return
                if blocchi_falliti and not movimenti:
                    self.after(0, lambda: self.show_custom_warning(
                        "Errore IA",
                        "Gemini non ha risposto correttamente per nessun blocco del CSV.\nRiprova tra qualche minuto."))
                    return
                if not movimenti:
                    self.after(0, lambda: self.show_custom_warning(
                        "Importazione", "Nessun movimento con data fino a oggi nel file."))
                    return
                self.after(0, lambda m=movimenti: _apri_revisione(m))
                if righe_future and not (blocchi_falliti or righe_scartate):
                    self.after(300, lambda n=righe_future: self.show_toast(
                        f"{n} movimenti con data futura ignorati.", duration=4000))
                if blocchi_falliti or righe_scartate:
                    _n_falliti = len(blocchi_falliti)
                    _n_scartate = righe_scartate
                    _parti = []
                    if _n_falliti:
                        _parti.append(f"{_n_falliti} blocco/i")
                    if _n_scartate:
                        _parti.append(f"{_n_scartate} riga/e")
                    _msg = " e ".join(_parti) + " del CSV non importate (errore Gemini o dati incompleti)."
                    if quota_msg:
                        _msg = (f"Quota giornaliera Gemini esaurita: importate solo le prime "
                                f"{righe_elaborate} righe del CSV. " + _attesa_quota(quota_msg))
                    self.after(300, lambda m=_msg: self.show_toast(m, duration=8000))
                return
            dati = _chiedi(prompt, "documento")
            _cedolino = False
            if estensione == ".pdf":
                try:
                    import pymupdf as _fz
                    _dz = _fz.open(path)
                    _tz = "".join(p.get_text() for p in _dz)
                    _dz.close()
                    _e_pens = re.search(r"prestazione\s+rata\s+\d{1,2}[/\-]\d{2,4}", _tz, re.I)
                    if _e_pens or (re.search(r"trattenut[ae]", _tz, re.I) and re.search(r"\bnetto\b", _tz, re.I)):
                        _cedolino = True
                        _d0 = dict(dati[0]) if dati else {}
                        _m_net = (
                            re.search(r"importo\s+netto\s+del\s+pagamento\s*=?\s*([\d.]+,\d{2})", _tz, re.I)
                            or re.search(r"netto\s+(?:in\s+busta|a\s+pagare|da\s+pagare|del\s+mese|pagato)\D{0,15}([\d.]+,\d{2})", _tz, re.I)
                        )
                        _m_dv = re.search(r"data\s+valuta\D{0,5}(\d{2})/(\d{2})/(\d{4})", _tz, re.I)
                        if _m_net:
                            _d0["importo"] = float(_m_net.group(1).replace(".", "").replace(",", "."))
                        if _m_dv:
                            _d0["data"] = f"{_m_dv.group(3)}-{_m_dv.group(2)}-{_m_dv.group(1)}"
                        _d0["tipo_documento"] = "fattura"
                        dati = [_d0]
                except Exception:
                    pass
            movimenti = []
            tipo_doc = dati[0].get("tipo_documento", "estratto") if dati else "estratto"
            e_fattura_singola = (tipo_doc == "fattura" and len(dati) == 1)
            if e_fattura_singola:
                d0 = dati[0]
                imp   = float(d0.get("importo") or 0.01)
                cat   = d0.get("categoria", "")
                fattura  = d0.get("fattura")
                scadenza = d0.get("scadenza")
                data_str = d0.get("data", datetime.now().strftime("%Y-%m-%d"))
                direzione = "Entrata" if _cedolino else "Uscita"
                _testo_self = ""
                try:
                    import pymupdf as _fitz_self
                    _doc_self = _fitz_self.open(path)
                    _testo_self = "".join(p.get_text() for p in _doc_self).lower()
                    _doc_self.close()
                except Exception:
                    pass
                _m_pens = re.search(r"prestazione\s+rata\s+(\d{1,2})[/\-](\d{2,4})", _testo_self) if _testo_self else None
                if _m_pens:
                    _mm_p, _aaaa_p = _m_pens.groups()
                    if len(_aaaa_p) == 2:
                        _aaaa_p = "20" + _aaaa_p
                    desc = f"prestazione rata {int(_mm_p):02d}/{_aaaa_p}"
                    direzione = "Entrata"
                else:
                    desc = str(d0.get("desc") or "Documento").strip()
                    if fattura and str(fattura).lower() not in ("null", "", "none"):
                        desc += f" {fattura}"
                    if scadenza and str(scadenza).lower() not in ("null", "", "none"):
                        desc += f" SCD:{scadenza}"
                        try:
                            data_str = datetime.strptime(str(scadenza), "%d-%m-%Y").strftime("%Y-%m-%d")
                        except Exception:
                            pass
                try:
                    data_fmt = datetime.strptime(data_str, "%Y-%m-%d").strftime("%d-%m-%Y")
                except Exception:
                    data_fmt = datetime.now().strftime("%d-%m-%Y")
                self.after(0, lambda: attesa.destroy() if attesa.winfo_exists() else None)
                self.after(0, lambda d=desc, i=imp, c=cat, dt=data_fmt, t=direzione: self.gestisci_archivi_pdf(
                    categoria_iniziale=c,
                    data_iniziale=dt,
                    importo_iniziale=f"{abs(i):.2f}".replace(".", ","),
                    tipo_iniziale=t,
                    descrizione_iniziale=d,
                    pdf_path_iniziale=path
                ))
            else:
                righe_scartate_estratto = 0
                for d in dati:
                    try:
                        desc = str(d.get("desc") or "Movimento").strip()
                        fattura  = d.get("fattura")
                        scadenza = d.get("scadenza")
                        if fattura and str(fattura).lower() not in ("null", "", "none"):
                            desc += f" {fattura}"
                        if scadenza and str(scadenza).lower() not in ("null", "", "none"):
                            desc += f" SCD:{scadenza}"
                        movimenti.append({
                            "data":        datetime.strptime(d["data"], "%Y-%m-%d").date(),
                            "descrizione": desc,
                            "importo":     float(str(d["importo"]).replace(",", ".")),
                            "categoria":   d.get("categoria", "Generica")
                        })
                    except Exception as _e_r:
                        righe_scartate_estratto += 1
                        continue
                _n_tot_e = len(movimenti)
                movimenti = [m for m in movimenti if m["data"] <= datetime.now().date()]
                _future_e = _n_tot_e - len(movimenti)
                self.after(0, _chiudi_attesa)
                if righe_scartate_estratto and not movimenti:
                    self.after(0, lambda: self.show_custom_warning(
                        "Errore IA",
                        "Gemini non ha restituito dati utilizzabili per questo documento.\nRiprova o controlla il file."))
                    return
                if not movimenti:
                    self.after(0, lambda: self.show_custom_warning(
                        "Importazione", "Nessun movimento con data fino a oggi nel documento."))
                    return
                self.after(0, lambda m=movimenti: _apri_revisione(m))
                if _future_e and not righe_scartate_estratto:
                    self.after(300, lambda n=_future_e: self.show_toast(
                        f"{n} movimenti con data futura ignorati.", duration=4000))
                if righe_scartate_estratto:
                    _n_scartate_e = righe_scartate_estratto
                    self.after(300, lambda n=_n_scartate_e: self.show_toast(
                        f"{n} movimento/i non importato/i (dati incompleti nella risposta IA).", duration=5000))
        except Exception as e:
            err_m = str(e)
            if "429" in err_m or "RESOURCE_EXHAUSTED" in err_m:
                msg_m = "Limite API Gemini raggiunto (quota giornaliera esaurita).\nRiprova domani o controlla il tuo piano su ai.google.dev."
            elif "503" in err_m or "UNAVAILABLE" in err_m:
                msg_m = "Gemini temporaneamente non disponibile.\nRiprova tra qualche minuto."
            elif "400" in err_m or "INVALID_ARGUMENT" in err_m:
                msg_m = "File non supportato o danneggiato."
            else:
                msg_m = err_m[:200]
            self.after(0, _chiudi_attesa)
            self.after(0, lambda er=msg_m: self.show_custom_warning(
                "Errore IA", er))
    threading.Thread(target=elabora_ia, daemon=True).start()
