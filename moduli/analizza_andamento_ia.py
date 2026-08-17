#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import threading
import tkinter as tk
from tkinter import ttk

from __main__ import API_KEY, GEMINI, PATH_LOCALE, genai_client
from moduli.modello_spesa import campo
from moduli.spinner_animato import crea_spinner_animato

# Analisi AI Gemini: invia entrate/uscite/categorie degli ultimi 365gg e mostra proiezione e consigli strategici a fine anno
def analizza_andamento_ia(self):
    if getattr(self, '_analisi_ia_in_corso', False):
        self.show_toast("Analisi AI già in corso, attendi il risultato...", duration=2000)
        return
    api_key_check = API_KEY
    if not api_key_check:
        self.show_custom_warning("Configurazione AI Necessaria",
            "L'Analisi Smart richiede una chiave API Gemini (gratuita).\n\n"
            "Vai nella sezione Impostazioni e clicca sul pulsante 'Ottieni'.\n")
        return
    nome_app = os.path.basename(PATH_LOCALE)
    from datetime import datetime, timedelta
    import datetime as dt_mod
    oggi = datetime.now().date()
    limite_365 = oggi - timedelta(days=365)
    e_tot, u_tot = 0.0, 0.0
    dettaglio_categories = {}
    data_piu_vecchia = None
    for data_op, lista_movimenti in self.spese.items():
        if isinstance(data_op, str):
            try:
                d_obj = datetime.strptime(data_op, "%d-%m-%Y").date()
            except: continue
        elif isinstance(data_op, (datetime, dt_mod.date)):
            d_obj = data_op if isinstance(data_op, dt_mod.date) else data_op.date()
        else: continue
        if d_obj >= limite_365:
            for mov in lista_movimenti:
                try:
                    cat = campo(mov, "categoria", "")
                    importo = float(campo(mov, "importo", 0.0))
                    tipo = campo(mov, "tipo", "")
                    if tipo == "Entrata":
                        e_tot += importo
                    else:
                        u_tot += importo
                        dettaglio_categories[cat] = dettaglio_categories.get(cat, 0) + importo
                    if data_piu_vecchia is None or d_obj < data_piu_vecchia:
                        data_piu_vecchia = d_obj
                except Exception as err_mov:
                    print(f"[analizza_andamento_ia] Voce scartata: {err_mov}")
                    continue
    if not dettaglio_categories and e_tot == 0:
        self.show_custom_warning("Nessun Dato", "Dati insufficienti negli ultimi 365 giorni.")
        return
    self._analisi_ia_in_corso = True
    if data_piu_vecchia:
        giorni_coperti = (oggi - data_piu_vecchia).days + 1
        mesi_coperti = max(1, round(giorni_coperti / 30.44))
    else:
        mesi_coperti = 1
    cat_ordinate = dict(sorted(dettaglio_categories.items(), key=lambda item: item[1], reverse=True))
    stringa_categorie = "\n".join([f"   - {c:.<25} {v:>10.2f}€" for c, v in cat_ordinate.items()])
    anno_corrente = oggi.year
    fine_anno = f"31/12/{anno_corrente}"
    mesi_rimanenti = 12 - oggi.month if oggi.month < 12 else 0
    prompt = f"""
    Analizza l'andamento finanziario di {nome_app} e fai una proiezione per fine anno:
    DATI STORICI (Ultimi 365 giorni):
    - Entrate Totali: {e_tot:.2f}€
    - Uscite Totali: {u_tot:.2f}€
    - Media Uscite Mensile: {u_tot/mesi_coperti:.2f}€ (calcolata su {mesi_coperti} mesi di dati disponibili)
    - Categorie: {stringa_categorie}
    SITUAZIONE ATTUALE:
    - Oggi è il: {oggi.strftime('%d/%m/%Y')}
    - Mesi alla fine del {anno_corrente}: {mesi_rimanenti}
    REGOLE DI RISPOSTA:
    1. NON usare simboli Markdown (*, #, ecc.).
    2. Usa il minuscolo per il corpo del testo. Usa le MAIUSCOLE esclusivamente per i titoli delle sezioni.
    3. TASK 1: Analisi breve dei dati storici.
    4. TASK 2: PREDIZIONE FINE ANNO. Stima quanto sarà il totale uscite al {fine_anno}.
    5. TASK 3: Suggerimento per chiudere l'anno in attivo.
    """
    splash = tk.Toplevel(self, bg=self.COLOR_WIDGET_BG)
    splash.overrideredirect(True)
    splash.attributes('-topmost', True)
    width, height = 320, 70
    x = self.winfo_rootx() + (self.winfo_width()  // 2) - (width  // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (height // 2)
    splash.geometry(f"{width}x{height}+{x}+{y}")
    frame_s = tk.Frame(splash, bg=self.COLOR_WIDGET_BG, bd=0,
                       highlightbackground=self.COLOR_HIGHLIGHT,
                       highlightthickness=1)
    frame_s.pack(expand=True, fill='both')
    inner = tk.Frame(frame_s, bg=self.COLOR_WIDGET_BG)
    inner.pack(expand=True)
    cvs, _ = crea_spinner_animato(inner, self.COLOR_WIDGET_BG, size=28, tick_ms=30)
    cvs.pack(side="left", padx=(0, 8))
    tk.Label(inner, text="Analisi AI in corso...",
             font=("Segoe UI", 9, "bold"),
             bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HIGHLIGHT).pack(side="left")
    splash.update()
    def _on_iconify(event):
        if splash.winfo_exists():
            splash.withdraw()
    def _on_deiconify(event):
        if splash.winfo_exists():
            splash.deiconify()
    _funcid_unmap = self.bind("<Unmap>", _on_iconify, add="+")
    _funcid_map   = self.bind("<Map>",   _on_deiconify, add="+")
    def _mostra_risultato(testo):
        self._analisi_ia_in_corso = False
        self.unbind("<Unmap>", _funcid_unmap)
        self.unbind("<Map>", _funcid_map)
        if splash.winfo_exists():
            splash.destroy()
        popup = tk.Toplevel(self, bg=self.COLOR_WIDGET_BG)
        popup.withdraw()
        popup.title(f"Bilancio Strategico {nome_app}")
        w, h = 1200, 600
        x = self.winfo_rootx() + (self.winfo_width()  // 2) - (w // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
        popup.geometry(f"{w}x{h}+{x}+{y}")
        popup.minsize(w, h)
        popup.bind("<Escape>", lambda e: popup.destroy())
        ttk.Label(popup, text=f"Analisi Categorie {nome_app} (365gg)",
                  style="Header.TLabel", font=("Consolas", 12, "bold")).pack(side="top", pady=15)
        pannello_bottom = tk.Frame(popup, bg=self.COLOR_WIDGET_BG)
        pannello_bottom.pack(side="bottom", fill="x", pady=10)
        lbl_chiudi = ttk.Label(pannello_bottom, text=" Chiudi",
                               image=self.icone_gui.get("chiudi"), compound="left",
                               cursor="hand2", font=("Arial", 9, "bold"),
                               background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR)
        lbl_chiudi.pack(pady=5)
        lbl_chiudi.bind("<Button-1>", lambda e: popup.destroy())
        container = tk.Frame(popup, bg=self.COLOR_WIDGET_BG)
        container.pack(side="top", expand=True, fill="both", padx=20, pady=5)
        scrollbar = ttk.Scrollbar(container, orient="vertical", style="Vertical.TScrollbar")
        scrollbar.pack(side="right", fill="y")
        text_area = tk.Text(container, bg=self.COLOR_WHITE, fg=self.COLOR_BLACK,
                            font=("Consolas", 11), wrap="word", padx=25, pady=25,
                            borderwidth=0, yscrollcommand=scrollbar.set, spacing1=6)
        text_area.pack(side="left", expand=True, fill="both")
        scrollbar.config(command=text_area.yview)
        text_area.insert("1.0", testo)
        text_area.config(state="disabled")
        if self.state() == 'iconic':
            self.deiconify()
            self.lift()
        popup.deiconify()
        popup.focus_set()
    def run_analysis():
        try:
            client = genai_client.Client(api_key=api_key_check)
            response = client.models.generate_content(model=GEMINI, contents=prompt)
            testo = response.text if response.text else "Nessun testo generato."
        except Exception as err:
            testo = f"ERRORE API:\n{str(err)}"
        self.after(0, lambda: _mostra_risultato(testo))
    threading.Thread(target=run_analysis, daemon=True).start()
