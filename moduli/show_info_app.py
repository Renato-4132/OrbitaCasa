#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import webbrowser
import tkinter as tk
from tkinter import ttk

from __main__ import NAME, VERSION, DB_DIR

# Finestra Informativa e Dettagli dell'Applicazione (About Box)
def show_info_app(self):
    def apri_email(event):
        webbrowser.open("mailto:helporbitacasa@gmail.com")

    def apri_link_python(event):
        webbrowser.open("https://www.python.org/downloads/")

    def apri_github(event):
        webbrowser.open("https://github.com/Renato-4132/OrbitaCasa")

    testo_filtri = f"💰 {NAME} - Guida Rapida Interattiva\n\n"
    testo_filtri += (
            "# FILTRI TEMPORALI (Controllo Statistiche)\n"
            "• Totali: Aggrega tutto il periodo storico disponibile.\n"
            "• Anno: Aggrega i dati dell'ANNO selezionato.\n"
            "• Mese: Aggrega i dati del MESE selezionato.\n"
            "• Giorno: Mostra i movimenti singoli del GIORNO selezionato.\n"
            "\n# INTERAZIONI TABELLE (Treeview)\n"
            "• Scroll: Usa la rotella del mouse.\n"
            "• Ordinamento: Clicca sull'intestazione di colonna.\n"
            "• Selezione: CTRL o SHIFT per selezioni multiple.\n"
            "• Doppio Clic (Mese/Anno/Tot): Apre il pop-up Dettaglio.\n"
            "\n# DETTAGLIO E CALENDARI SMART\n"
            "• Doppio Clic nel Dettaglio: Vai alla transazione principale.\n"
            "• Modalità Giorno: Doppio Clic apre PDF, Destro su Google Calendar.\n"
            "• Doppio Clic Calendario: Apre l'interfaccia di inserimento rapido.\n"
            "• Hover Calendario: Visualizza Smart Info-Point e riepiloghi.\n"
            "• Tasto Destro Calendario: Gestione avanzata Smart-HUD.\n"
            "\n# GRAFICI A BARRE E ANALISI\n"
            "• Navigazione: Frecce Destra/Sinistra. ESC per uscire.\n"
            "• Grafico Aggregato: Seleziona più categorie + Tasto Destro.\n"
            "• Drill-Down: Doppio clic sulla barra per i dettagli.\n"
            "• Tooltip: Passa il mouse sopra le barre (Hover).\n"
    )
    testo_icone = (
            "📅 OGGI: Ritorna immediatamente alla data odierna.\n"
            "📅 GIORNO / MESE / ANNO: Filtra i movimenti in base al periodo.\n"
            "💰 TOTALI: Riepilogo complessivo Entrate/Uscite/Saldo.\n"
            "📈 GRAFICI: Pannello analisi visiva e statistiche.\n"
            "👁️ HUB PANNELLO: Hub pannello moduli principali.\n"
            "⌨️ SCORCIATOIE: Tasti rapidi da tastiera.\n"
            "📊 BILANCIO PDF: Genera bilancio completo in formato PDF.\n"
            "🌐 PORTALE WEB: Genera QR per accesso da Smartphone.\n"
            "📌 PROMEMORIA: Gestione note e post-it rapidi.\n"
            "⏰ QR & TIMER: QRCode Promemoria Google e Timer sessione.\n"
            "📢 RICORRENZE: Controllo movimenti periodici e scadenze.\n"
            "📁 DOCUMENTI CONTABILI PDF: Gestione documenti e scontrini digitali.\n"
            "📁 DOCUMENTI PERSONALI PDF: Gestione documenti Personali.\n"
            "🛒 LISTA SPESA: Lista intelligente divisa per Supermercato.\n"
            "🏦 BANCA: Accesso diretto ai servizi web bancari.\n"
            "⌨️ SCORCIATOIE TASTIERA: Tasti rapidi per l'utilizzo senza mouse.\n"
            "💳 PORTAFOGLIO BANCARIO: Gestione e riepilogo dei conti e delle carte di credito.\n"
            "🔄 CAROSELLO: Rotazione automatica statistiche live.\n"
            "🗗 RIDUCI: Riduce l'applicazione nella barra di sistema.\n"
            "📡 SYNC: Sincronizzazione Intelligente Gemini\n"
            "            L'integrazione con l'intelligenza artificiale di Gemini eleva il sistema ben oltre il semplice\n"
            "            download delle fatture. Grazie all'analisi semantica delle email e degli allegati, l'IA è in\n"
            "            grado di riconoscere, estrarre e catalogare automaticamente ogni tipologia di documento che\n"
            "            costituisce un 'modulo contabile'.\n"
            "            Il sistema identifica ed elabora autonomamente:\n"
            "            * Estratti Contabili: Analisi completa dei movimenti bancari e dei saldi.\n"
            "            * Liste Spese: Identificazione di distinte e rendiconti periodici.\n"
            "            * Estratti Carte di Credito: Elaborazione dei fogli riepilogativi delle transazioni card.\n"
            "            * Fatture Varie: Non solo le elettroniche, ma anche proforma e ricevute fiscali.\n"
            "            * Documentazione Finanziaria: Qualsiasi modulo con rilevanza per la gestione della contabilità.\n"
            "📂 CARTELLA PDF: Apre la directory locale dei file elaborati.\n"
            "🔙 RESET SYNC: Ricarica i contatori e forza il controllo file.\n"
            "📄 APRI PDF: Visualizza l'ultimo documento PDF elaborato.\n"
            "👥 FAIR SHARE: Gestione spese condivise tra più partecipanti. (Anche Ricorrenti)\n"
    )
    resources_dir = os.path.join(DB_DIR, "resources")
    logo_path = os.path.join(resources_dir, "info_image.png")
    info_win = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    info_win.transient(self)
    info_win.title(f"Info & Guida - {NAME}")
    info_win.resizable(False, False)
    info_win.withdraw()
    bottom_frame = ttk.Frame(info_win)
    bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5, padx=10)
    img_stampa = self.icone_gui.get("stampa")
    btn_stampa = tk.Label(bottom_frame, compound="left", image=img_stampa, text=" Stampa Guida",
                          background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                          cursor="hand2", padx=15, pady=6, font=("Arial", 9, "bold"))
    btn_stampa.image = img_stampa
    btn_stampa.pack(side=tk.LEFT)
    btn_stampa.bind("<Button-1>", lambda e: self._stampa_lista_diretta(testo_filtri + "\n" + testo_icone, self.show_custom_warning))
    img_chiudi = self.icone_gui.get("chiudi")
    btn_chiudi = tk.Label(bottom_frame, compound="left", image=img_chiudi, text=" Chiudi (ESC)",
                          background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                          cursor="hand2", padx=15, pady=6, font=("Arial", 9, "bold"))
    btn_chiudi.image = img_chiudi
    btn_chiudi.pack(side=tk.RIGHT)
    btn_chiudi.bind("<Button-1>", lambda e: info_win.destroy())
    notebook = ttk.Notebook(info_win)
    notebook.pack(fill="both", expand=True, padx=10, pady=(2, 0))
    def _add_tab(frame, ico_key, testo):
        img = self.icone_gui.get(ico_key)
        if img:
            notebook.add(frame, image=img, text=f" {testo} ", compound="left")
        else:
            notebook.add(frame, text=f" {testo} ")
    tab_info = ttk.Frame(notebook)
    _add_tab(tab_info, "info", "Info App")
    main_frame = tk.Frame(tab_info, bg=self.COLOR_TOPLEVEL)
    main_frame.pack(expand=True, fill="both", padx=20, pady=10)
    if os.path.exists(logo_path):
        try:
            from PIL import Image, ImageTk
            pil_logo = Image.open(logo_path)
            img_logo = ImageTk.PhotoImage(pil_logo)
            lbl_logo = tk.Label(main_frame, image=img_logo, bg=self.COLOR_TOPLEVEL)
            lbl_logo.image = img_logo
            lbl_logo.pack(pady=2)
        except Exception:
            tk.Label(main_frame, text="🏠", font=("Arial", 30), bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR).pack()
    tk.Label(main_frame, text=f"{NAME}", font=("Arial", 16, "bold"), bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR).pack()
    tk.Label(main_frame, text=f"Versione {VERSION} © 2026 Renato-4132 — Tutti i diritti riservati", font=("Arial", 9), bg=self.COLOR_TOPLEVEL, fg="gray").pack()
    links_frame = tk.Frame(main_frame, bg=self.COLOR_TOPLEVEL)
    links_frame.pack(pady=5)
    for ico_key, txt, cmd in [("email", " Email", apri_email), ("github", " GitHub", apri_github), ("python", " Python", apri_link_python)]:
        img = self.icone_gui.get(ico_key)
        lbl = tk.Label(links_frame, text=txt, image=img, compound="left", fg="#3498db", bg=self.COLOR_TOPLEVEL, cursor="hand2", font=("Arial", 9))
        lbl.image = img
        lbl.pack(side=tk.LEFT, padx=10)
        lbl.bind("<Button-1>", cmd)
    tab_filtri = ttk.Frame(notebook)
    _add_tab(tab_filtri, "filtri", "Filtri e Tabelle")
    container_f = tk.Frame(tab_filtri, bg=self.COLOR_WHITE, highlightbackground=self.COLOR_TOPLEVEL, highlightthickness=4, bd=0)
    container_f.pack(fill="both", expand=True, padx=15, pady=2)
    tk.Label(container_f, text=testo_filtri, font=("Arial", 10),
             bg=self.COLOR_WHITE, fg=self.COLOR_BLACK, justify=tk.LEFT, anchor='nw',
             wraplength=920).pack(fill='both', expand=True, padx=15, pady=5)
    tab_icone = ttk.Frame(notebook)
    _add_tab(tab_icone, "tools", "Pulsanti Icone")
    container_i = tk.Frame(tab_icone, bg=self.COLOR_WHITE, highlightbackground=self.COLOR_TOPLEVEL, highlightthickness=4, bd=0)
    container_i.pack(fill="both", expand=True, padx=15, pady=2)
    tk.Label(container_i, text=testo_icone, font=("Arial", 10),
             bg=self.COLOR_WHITE, fg=self.COLOR_BLACK, justify=tk.LEFT, anchor='nw',
             wraplength=920).pack(fill='both', expand=True, padx=15, pady=5)
    info_win.update_idletasks()
    w, h = info_win.winfo_reqwidth(), info_win.winfo_reqheight()
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    info_win.geometry(f"1000x660+{x}+{y}")
    info_win.deiconify()
    info_win.grab_set()
    info_win.bind("<Escape>", lambda e: info_win.destroy())
