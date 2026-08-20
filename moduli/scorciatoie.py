#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk

SCORCIATOIE = [
    ("<Control-u>",       "Ctrl+U",       "utenze",                   "Utenze"),
    ("<Control-r>",       "Ctrl+R",       "rubrica_app",              "Rubrica"),
    ("<Control-y>",       "Ctrl+Y",       "gestisci_promemoria",      "Promemoria"),
    ("<Control-p>",       "Ctrl+P",       "anteprima_e_stampa_txt",   "Stampa TXT"),
    ("<Control-s>",       "Ctrl+S",       "open_saldo_conto",         "Portafoglio Bancario"),
    ("<Control-z>",       "Ctrl+Z",       "calcola_mancanti",         "Mancanti"),
    ("<Control-e>",       "Ctrl+E",       "apri_calcolatrice",        "Calcolatrice"),
    ("<Control-q>",       "Ctrl+Q",       "_on_close",                "Esci"),
    ("<Control-x>",       "Ctrl+X",       "iconify",                  "Iconizza"),
    ("<Control-t>",       "Ctrl+T",       "mostra_ricorrenza_popup",  "Nuova Ricorr."),
    ("<Control-l>",       "Ctrl+L",       "mostra_lista_ricorrenze",  "Lista Ricorr."),
    ("<Control-j>",       "Ctrl+J",       "scadenze_mese",            "Scadenze Mese"),
    ("<Control-f>",       "Ctrl+F",       "cerca_operazioni",         "Cerca Operaz."),
    ("<Control-n>",       "Ctrl+N",       "open_compare_window",      "Confronto Dati"),
    ("<Control-w>",       "Ctrl+W",       "time_machine",             "Time Machine"),
    ("<Control-g>",       "Ctrl+G",       "gruppo_categorie",         "Gruppo Cat."),
    ("<Control-a>",       "Ctrl+A",       "apri_fondo_risparmio",     "Stat. Annuali"),
    ("<Alt-h>",           "Alt+H",        "mostra_analisi_grafici",   "Analisi Grafici"),
    ("<Control-o>",       "Ctrl+O",       "calcolo_mutuo_prestito",   "Mutuo/Prestito"),
    ("<Alt-j>",           "Alt+J",        "export_giorno_forzato",    "Export Giorno"),
    ("<Alt-k>",           "Alt+K",        "export_month_detail",      "Export Mese"),
    ("<Alt-l>",           "Alt+L",        "export_anno_dettagliato",  "Export Anno"),
    ("<Alt-g>",           "Alt+G",        "export_storico_totale",    "Export Storico"),
    ("<Alt-e>",           "Alt+E",        "popup_scelta_estratto",    "Analisi e Bilanci"),
    ("<Control-k>",       "Ctrl+K",       "open_analisi_categoria",   "Analisi Cat."),
    ("<Control-Shift-K>", "Ctrl+Shift+K", "apri_categorie_suggerite", "Suggerim. Cat."),
    ("<Control-Shift-T>", "Ctrl+Shift+T", "mostra_categorie_popup",   "Popup Cat."),
    ("<Control-Shift-S>", "Ctrl+Shift+S", "apri_cancella_multiplo",   "Canc. Multiplo"),
    ("<Control-i>",       "Ctrl+I",       "show_info_app",            "Info App"),
    ("<Control-m>",       "Ctrl+M",       "scarica_manuale",          "Manuale"),
    ("<Control-d>",       "Ctrl+D",       "mostra_dare_avere",        "FairShare"),
    ("<Control-b>",       "Ctrl+B",       "apri_finestra_importa",    "Importa AI"),
    ("<Control-Shift-G>", "Ctrl+Shift+G", "avvia_sincronizzazione",   "Sync Gmail"),
    ("<Alt-r>",           "Alt+R",        "genera_report_pdf",        "Report PDF"),
    ("<F5>",              "F5",           "goto_today",               "Torna a Oggi"),
]

SCORCIATOIA_ESC = ("Esc", "Chiudi")

# Scorciatoie Tasti
def configura_scorciatoie(self):
    for tk_key, _label, metodo_nome, _descr in SCORCIATOIE:
        try:
            metodo = getattr(self, metodo_nome)
        except AttributeError:
            print(f"[Scorciatoie] Metodo non trovato: {metodo_nome} ({tk_key})")
            continue
        self.bind_all(tk_key, lambda e, f=metodo: f())

def mostra_popup_scorciatoie(self, event=None):
    if hasattr(self, '_scorciatoie_popup') and self._scorciatoie_popup and self._scorciatoie_popup.winfo_exists():
        self._scorciatoie_popup.lift()
        self._scorciatoie_popup.focus_force()
        return
    popup = tk.Toplevel(self)
    self._scorciatoie_popup = popup
    popup.bind("<Destroy>", lambda e: setattr(self, '_scorciatoie_popup', None) if e.widget is popup else None)
    popup.title("Scorciatoie")
    popup.withdraw()
    popup.configure(background=self.COLOR_WIDGET_BG)
    popup.resizable(False, False)
    popup.transient(self)
    popup.update_idletasks()
    w, h = 900, 500
    x = self.winfo_x() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_y() + (self.winfo_height() // 2) - (h // 2)
    popup.geometry(f"{w}x{h}+{x}+{y}")
    popup.deiconify()
    popup.wait_visibility()
    popup.bind("<Escape>", lambda e: popup.destroy())
    tk.Label(popup, text="⌨️ SHORTCUT RAPIDI", font=("Arial", 11, "bold"),
             foreground="#61AFEF", background=self.COLOR_WIDGET_BG).pack(pady=15)
    main_container = tk.Frame(popup, background=self.COLOR_WIDGET_BG)
    main_container.pack(fill="both", expand=True, padx=20)
    for col in range(4):
        main_container.columnconfigure(col, weight=1)
    voci_popup = [(label, descr) for _, label, _metodo, descr in SCORCIATOIE]
    voci_popup.append(SCORCIATOIA_ESC)
    metà = (len(voci_popup) + 1) // 2
    for i, (k, d) in enumerate(voci_popup):
        colonna_base = 0 if i < metà else 2
        riga = i if i < metà else i - metà
        tk.Label(main_container, text=k, font=("Consolas", 9, "bold"),
                 foreground="#98C379", background=self.COLOR_WIDGET_BG,
                 anchor="e").grid(row=riga, column=colonna_base, padx=(10, 10), pady=1, sticky="e")
        tk.Label(main_container, text=d, font=("Arial", 9),
                 foreground=self.TEXT_COLOR, background=self.COLOR_WIDGET_BG,
                 anchor="w").grid(row=riga, column=colonna_base + 1, padx=(0, 20), pady=1, sticky="w")
    btn_chiudi_scorciatoie = tk.Label(
        popup,
        image=self.icone_gui.get("chiudi"),
        text=" Chiudi",
        compound="left",
        cursor="hand2",
        background=self.COLOR_WIDGET_BG,
        foreground=self.TEXT_COLOR,
        font=("Arial", 9, "bold")
    )
    btn_chiudi_scorciatoie.image = self.icone_gui.get("chiudi")
    btn_chiudi_scorciatoie.pack(pady=(15, 20))
    btn_chiudi_scorciatoie.bind("<Button-1>", lambda e: popup.destroy())
