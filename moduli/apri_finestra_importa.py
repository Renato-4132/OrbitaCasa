#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import math
import os
import re
import threading
import tkinter as tk
from tkinter import filedialog

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
    attesa = tk.Toplevel(self)
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
    gemini_colors = ["#0055FF", "#AA00FF", "#FF0055", "#00C853"]
    cvs_size = 28
    cvs = tk.Canvas(inner, width=cvs_size, height=cvs_size,
                    bg=self.COLOR_WIDGET_BG, highlightthickness=0, bd=0)
    cvs.pack(side="left", padx=(0, 8))
    tk.Label(inner, text="Gemini sta analizzando...",
             font=("Segoe UI", 9, "bold"),
             bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HIGHLIGHT).pack(side="left")
    state = {"angle": 0, "color_step": 0}
    def animate_attesa():
        try:
            if not attesa.winfo_exists(): return
            if not cvs.winfo_exists(): return
            cvs.delete("all")
        except tk.TclError:
            return
        state["angle"] = (state["angle"] + 15) % 360
        state["color_step"] += 1
        color = gemini_colors[(state["color_step"] // 5) % len(gemini_colors)]
        c = cvs_size // 2; r = 8
        cvs.create_oval(c-r, c-r, c+r, c+r, outline=self.COLOR_HIGHLIGHT, width=1)
        rad = math.radians(state["angle"])
        cvs.create_arc(c-r, c-r, c+r, c+r, start=state["angle"]-40, extent=40,
                       outline=color, width=3, style="arc")
        cvs.create_oval(c+r*math.cos(rad)-3, c+r*math.sin(rad)-3,
                        c+r*math.cos(rad)+3, c+r*math.sin(rad)+3,
                        fill=color, outline=color)
        attesa.after(20, animate_attesa)
    animate_attesa()
    def elabora_ia():
        try:
            client = genai.Client(api_key=API_KEY)
            estensione = os.path.splitext(path)[1].lower()

            lista_cat = ", ".join(f'"{c}"' for c in self.categorie) if self.categorie else "Generica"
            regola_cat = (
                f"Assegna a ogni movimento la categoria più adatta scegliendo SOLO tra: [{lista_cat}]. "
                "Se nessuna corrisponde usa 'Generica'."
            )
            prompt_testo = (
                f"Analizza questo documento e convertilo in JSON.\n"
                f"REGOLE:\n"
                f"1. Determina se il documento è una FATTURA/RICEVUTA SINGOLA "
                f"(un solo fornitore, un solo importo totale) oppure un ESTRATTO "
                f"(lista di movimenti bancari o più transazioni).\n"
                f"2. Se ESTRATTO o LISTA MOVIMENTI: ogni movimento separato, "
                f"importo negativo per uscite e positivo per entrate.\n"
                f"3. Se FATTURA/RICEVUTA SINGOLA: una sola voce con il totale, "
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
                DIMENSIONE_BLOCCO_CSV = 40
                blocchi_csv = [
                    righe_dati[i:i + DIMENSIONE_BLOCCO_CSV]
                    for i in range(0, len(righe_dati), DIMENSIONE_BLOCCO_CSV)
                ] or [[]]
                dati_csv = []
                for blocco in blocchi_csv:
                    if not blocco:
                        continue
                    campione_blocco = intestazione_csv + "".join(blocco)
                    prompt_blocco = (
                        f"Analizza queste righe di un CSV bancario e convertile in JSON.\n"
                        f"REGOLE:\n"
                        f"1. Identifica Data, Descrizione e Importo.\n"
                        f"2. Negativi = uscite, Positivi = entrate.\n"
                        f"3. {regola_cat}\n"
                        f"4. Restituisci SOLO un array JSON: "
                        f'[{{"data": "YYYY-MM-DD", "desc": "stringa", "importo": float, "categoria": "stringa"}}].\n'
                        f"CAMPIONE:\n{campione_blocco}"
                    )
                    risposta_blocco = client.models.generate_content(
                        model=GEMINI, contents=prompt_blocco)
                    raw_blocco = risposta_blocco.text.strip()
                    if "```json" in raw_blocco:
                        raw_blocco = raw_blocco.split("```json")[1].split("```")[0].strip()
                    elif "```" in raw_blocco:
                        raw_blocco = raw_blocco.split("```")[1].split("```")[0].strip()
                    dati_csv.extend(json.loads(raw_blocco))
                movimenti = []
                for d in dati_csv:
                    desc = d["desc"]
                    fattura  = d.get("fattura")
                    scadenza = d.get("scadenza")
                    if fattura and str(fattura).lower() not in ("null", "", "none"):
                        desc += f" {fattura}"
                    if scadenza and str(scadenza).lower() not in ("null", "", "none"):
                        desc += f" ⏰{scadenza}"
                    movimenti.append({
                        "data":        datetime.strptime(d["data"], "%Y-%m-%d").date(),
                        "descrizione": desc,
                        "importo":     float(d["importo"]),
                        "categoria":   d.get("categoria", "Generica")
                    })
                if attesa.winfo_exists(): attesa.destroy()
                self.after(0, lambda: self.apri_finestra_revisione_universale(movimenti))
                return
            response = client.models.generate_content(
                model=GEMINI, contents=prompt)
            raw_json = response.text.strip()
            if "```json" in raw_json:
                raw_json = raw_json.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_json:
                raw_json = raw_json.split("```")[1].split("```")[0].strip()
            dati = json.loads(raw_json)
            movimenti = []
            tipo_doc = dati[0].get("tipo_documento", "estratto") if dati else "estratto"
            estensione_path = os.path.splitext(path)[1].lower()
            e_fattura_singola = (estensione_path == ".pdf" and len(dati) == 1)
            if e_fattura_singola:
                d0 = dati[0]
                imp   = float(d0.get("importo") or 0.01)
                cat   = d0.get("categoria", "")
                fattura  = d0.get("fattura")
                scadenza = d0.get("scadenza")
                data_str = d0.get("data", datetime.now().strftime("%Y-%m-%d"))
                direzione = "Uscita"
                _testo_self = ""
                try:
                    import fitz as _fitz_self
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
                        desc += f" ⏰{scadenza}"
                        try:
                            data_str = datetime.strptime(str(scadenza), "%d-%m-%Y").strftime("%Y-%m-%d")
                        except Exception:
                            pass
                try:
                    data_fmt = datetime.strptime(data_str, "%Y-%m-%d").strftime("%d-%m-%Y")
                except Exception:
                    data_fmt = datetime.now().strftime("%d-%m-%Y")
                if attesa.winfo_exists(): attesa.destroy()
                self.after(0, lambda d=desc, i=imp, c=cat, dt=data_fmt, t=direzione: self.gestisci_archivi_pdf(
                    categoria_iniziale=c,
                    data_iniziale=dt,
                    importo_iniziale=str(abs(i)).replace(".", ","),
                    tipo_iniziale=t,
                    descrizione_iniziale=d,
                    pdf_path_iniziale=path
                ))
            else:
                for d in dati:
                    desc = d["desc"]
                    fattura  = d.get("fattura")
                    scadenza = d.get("scadenza")
                    if fattura and str(fattura).lower() not in ("null", "", "none"):
                        desc += f" {fattura}"
                    if scadenza and str(scadenza).lower() not in ("null", "", "none"):
                        desc += f" ⏰{scadenza}"
                    movimenti.append({
                        "data":        datetime.strptime(d["data"], "%Y-%m-%d").date(),
                        "descrizione": desc,
                        "importo":     float(d["importo"]),
                        "categoria":   d.get("categoria", "Generica")
                    })
                if attesa.winfo_exists(): attesa.destroy()
                self.after(0, lambda: self.apri_finestra_revisione_universale(movimenti))
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
            if attesa.winfo_exists(): attesa.destroy()
            self.after(0, lambda er=msg_m: self.show_custom_warning(
                "Errore IA", er))
    threading.Thread(target=elabora_ia, daemon=True).start()
