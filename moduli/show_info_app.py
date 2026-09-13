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

    def apri_manuale(event):
        self.scarica_manuale()

    testo_filtri = f"💰 {NAME} - Guida Rapida Interattiva\n\n"
    testo_filtri += (
            "💰 FILTRI TEMPORALI (Controllo Statistiche)\n"
            "• Totali: Aggrega tutto il periodo storico disponibile.\n"
            "• Anno: Aggrega i dati dell'ANNO selezionato.\n"
            "• Mese: Aggrega i dati del MESE selezionato.\n"
            "• Giorno: Mostra i movimenti singoli del GIORNO selezionato.\n"
            "\n 📈 INTERAZIONI TABELLE (Treeview)\n"
            "• Scroll: Usa la rotella del mouse.\n"
            "• Ordinamento: Clicca sull'intestazione di colonna.\n"
            "• Selezione: CTRL o SHIFT per selezioni multiple.\n"
            "• Doppio Clic (Mese/Anno/Tot): Apre il pop-up Dettaglio.\n"
            "\n 📅 DETTAGLIO E CALENDARI SMART\n"
            "• Doppio Clic nel Dettaglio: Vai alla transazione principale.\n"
            "• Modalità Giorno: Doppio Clic apre PDF, Destro su Google Calendar.\n"
            "• Doppio Clic Calendario: Apre l'interfaccia di inserimento rapido.\n"
            "• Hover Calendario: Visualizza Smart Info-Point e riepiloghi.\n"
            "• Tasto Destro Calendario: Gestione avanzata Smart-HUD.\n"
            "\n 📈 GRAFICI A BARRE E ANALISI\n"
            "• Navigazione: Frecce Destra/Sinistra. ESC per uscire.\n"
            "• Grafico Aggregato: Seleziona più categorie + Tasto Destro.\n"
            "• Drill-Down: Doppio clic sulla barra per i dettagli.\n"
            "• Tooltip: Passa il mouse sopra le barre (Hover).\n"
    )
    testo_icone = (
            "💰 PULSANTI & ICONE \n\n"
            "• 📅 OGGI: Ritorna immediatamente alla data odierna.\n"
            "• 📅 GIORNO / MESE / ANNO: Filtra i movimenti in base al periodo.\n"
            "• 💰 TOTALI: Riepilogo complessivo Entrate/Uscite/Saldo.\n"
            "• 📈 GRAFICI: Pannello analisi visiva e statistiche.\n"
            "• 👁️ HUB PANNELLO: Hub pannello moduli principali.\n"
            "• ⌨️ SCORCIATOIE: Tasti rapidi da tastiera.\n"
            "• 📊 BILANCIO PDF: Genera bilancio completo in formato PDF.\n"
            "• 🌐 PORTALE WEB: Genera QR per accesso da Smartphone.\n"
            "• 📌 PROMEMORIA: Gestione note e post-it rapidi.\n"
            "• ⏰ QR & TIMER: QRCode Promemoria Google e Timer sessione.\n"
            "• 📢 RICORRENZE: Controllo movimenti periodici e scadenze.\n"
            "• ✨ ANALISI IA (Gemini): Analizza l'andamento del bilancio e genera proiezioni/consigli.\n"
            "• 🔍 RICERCA GLOBALE: Cerca un movimento in tutto lo storico per descrizione/categoria/importo.\n"
            "• 📅 SCADENZE DEL MESE: Elenco rapido delle scadenze/ricorrenze del mese corrente.\n"
            "• 📁 DOCUMENTI CONTABILI PDF: Gestione documenti e scontrini digitali.\n"
            "• 📁 DOCUMENTI PERSONALI PDF: Gestione documenti Personali.\n"
            "• 🛒 LISTA SPESA: Lista intelligente divisa per Supermercato.\n"
            "• 🏦 BANCA: Accesso diretto ai servizi web bancari.\n"
            "• ⌨️ SCORCIATOIE TASTIERA: Tasti rapidi per l'utilizzo senza mouse.\n"
            "• 💳 PORTAFOGLIO BANCARIO: Gestione e riepilogo dei conti e delle carte di credito.\n"
            "• 🔄 CAROSELLO: Rotazione automatica statistiche live.\n"
            "• 🗗 RIDUCI: Riduce l'applicazione nella barra di sistema.\n"
            "• 📡 SYNC: Sincronizzazione Intelligente Gemini\n"
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
            "• 📂 CARTELLA PDF: Apre la directory locale dei file elaborati.\n"
            "• 🔙 RESET SYNC: Ricarica i contatori e forza il controllo file.\n"
            "• 📄 APRI PDF: Visualizza l'ultimo documento PDF elaborato.\n"
            "• 👥 FAIR SHARE: Gestione spese condivise tra più partecipanti. (Anche Ricorrenti)\n"
            "\n TAB 'ANALISI MESE ATTUALE' (sotto il calendario)\n"
            "• 📋 Movimenti: Elenco dettagliato dei movimenti del mese.\n"
            "• 🏷️ Categorie: Riepilogo spese per categoria nel mese.\n"
            "• ✨ Sparkline: Andamento giornaliero del mese in miniatura.\n"
            "• 🔥 Heatmap: Mappa di calore delle spese sul calendario del mese.\n"
            "• 💳 Metodo: Riepilogo spese per metodo di pagamento.\n"
            "• 🏦 Conto: Riepilogo spese per conto/carta utilizzati.\n"
            "• 🔁 Checkout: Movimenti ricorrenti/pianificati in scadenza nel mese.\n"
            "\n LEGENDA COLORI CALENDARIO (sopra il calendario)\n"
            "• 🟢 Entrata: giorno con almeno un'entrata registrata.\n"
            "• 🔴 Uscita: giorno con almeno un'uscita registrata.\n"
            "• 🟡 Entrata+Uscita: giorno con entrate e uscite.\n"
            "• ⬛ Weekend: sabato e domenica.\n"
            "• 🔵 Selezionato: giorno attualmente selezionato nel calendario.\n"
            "\n PANNELLO \"REGISTRA O MODIFICA MOVIMENTO\"\n"
            "• ➕ AGGIUNGI: Registra il movimento compilato nel form.\n"
            "• 🔄 RESET (form): Svuota tutti i campi del form.\n"
            "• ✏️ MODIFICA: Carica in modifica il movimento selezionato (solo in modalità Giorno).\n"
            "• ❌ ANNULLA: Annulla la modifica in corso senza salvare.\n"
            "• 💾 SALVA: Salva le modifiche al movimento in modifica.\n"
            "• ❌ CANCELLA: Elimina il movimento selezionato.\n"
            "• ⏳ RICORRENZE (form): Apre la gestione dei movimenti ricorrenti.\n"
            "• ✅ CATEGORIE (form): Apre la gestione delle categorie.\n"
            "• 📅 PIANIFICA: Crea un Fondo di Ammortamento per la spesa futura selezionata,\n"
            "            distribuendo l'accantonamento nei mesi precedenti alla scadenza.\n"
            "• 📡 SYNC (contatore): Numero di operazioni scaricate da Gmail nella sessione corrente.\n"
            "• 📁 Cartella PDF (form): Apre la cartella locale delle fatture scaricate da Gmail.\n"
            "• 🌐 Sync manuale (form): Avvia subito una sincronizzazione con Gmail.\n"
            "• 🔄 Ricalcola (form): Ricalcola le operazioni web già scaricate.\n"
            "• 📥 Log Importazioni: Storico di cosa è stato importato/sincronizzato.\n"
            "• 📅 Calendario data: Apre il selettore data per il movimento da registrare.\n"
            "• 🔄 Reset data: Riporta la data del movimento a oggi.\n"
            "• ☑️ Blocca data: Impedisce che la data si aggiorni automaticamente a oggi.\n"
            "• 📥 IMPORT IA: Importa un movimento da PDF/immagine/testo tramite intelligenza artificiale.\n"
            "• 💡 SMARTCAT ON/OFF: Indica se il suggerimento automatico di categoria è attivo.\n"
    )
    testo_menu = (
            f"🪐 {NAME} - Menu Laterale (Barra Sinistra)\n\n"
            "🪐 COMANDI GENERALI DELLA BARRA\n"
            "• ➤ / ◀ : Espande o comprime le etichette di testo del menu.\n"
            "• Logo / Nome App: Apre la Piramide, l'hub di navigazione 3D di tutti i moduli.\n"
            "• Campo di ricerca (a barra espansa): Ricerca rapida tra tutte le funzioni dell'app.\n"
            "\n 📁 GESTIONE\n"
            "• Gestione SuperMarket — Lista della spesa intelligente\n"
            "• Gestione Documenti (Contabili)\n"
            "• Gestione Documenti Personali\n"
            "• Gestione Utenze — Acqua, Luce, Gas (Ctrl+U)\n"
            "• ImmoBil — Gestione Immobili\n"
            "• AutoPark — Gestione Veicoli\n"
            "• PetCare — Gestione Animali Domestici\n"
            "• Sincronizza Acquisti Email (Gmail)\n"
            "• Importa Documento con IA (Gemini)\n"
            "• Log Importazioni\n"
            "• Rubrica Contatti (Ctrl+R)\n"
            "• Promemoria (Ctrl+Y)\n"
            "• GCalendar — Generatore QR e Timer promemoria\n"
            "• Piano Dieta\n"
            "• MyBusiness\n"
            "• Stampa (Ctrl+P)\n"
            "• Pannello Controllo (Ctrl+Z)\n"
            "• Calcolatrice (Ctrl+E)\n"
            "\n 📊 ANALISI\n"
            "• Ricerca Globale (Ctrl+F)\n"
            "• Gestione Tag # (categorie multiple)\n"
            "• Confronta Periodi (Ctrl+N)\n"
            "• FairShare — Dare/Avere tra Partecipanti (Ctrl+D)\n"
            "• Time Machine (Ctrl+W)\n"
            "• Aggrega Categorie (Ctrl+G)\n"
            "• Proiezione - Fondo Risparmio (Ctrl+A)\n"
            "• Grafici Interattivi (Alt+H)\n"
            "• Andamento Risparmio\n"
            "• Schedulatore Notifiche\n"
            "• Calcolatore Inflazione\n"
            "• Bilancio Grafico PDF (Alt+R)\n"
            "\n 🏦 FINANZE\n"
            "• Portafoglio Bancario (Ctrl+S)\n"
            "• Portafoglio Investimenti\n"
            "• Fondo Pensione\n"
            "• Calcolo Mutuo/Prestiti (Ctrl+O)\n"
            "• Bilancio Giorno (Alt+J)  |  Bilancio Mese (Alt+K)\n"
            "• Bilancio Anno (Alt+L)  |  Bilancio Storico Totale (Alt+G)\n"
            "• Analisi e Bilanci — scelta estratto (Alt+E)\n"
            "• Estratti per Metodo e Conti\n"
            "• Analisi Andamento Bilancio con IA (Gemini)\n"
            "• Analisi e Confronto Documenti con IA (Gemini)\n"
            "\n ⏰ RICORRENZE\n"
            "• Gestione Ricorrenze (Ctrl+T)\n"
            "• Lista Ricorrenze (Ctrl+L)\n"
            "• Scadenze Mese (Ctrl+J)\n"
            "• Pianifica — spese pianificate future\n"
            "\n 📅 CATEGORIE\n"
            "• Analisi Categorie (Ctrl+K)\n"
            "• Suggerisci Categorie — SmartCat (Ctrl+Shift+K)\n"
            "• Gestione Categorie (Ctrl+Shift+T)\n"
            "• Gestione Categorie Bulk (Ctrl+Shift+S)\n"
            "• Editor Categorie Estratti\n"
            "\n 🔧 SISTEMA\n"
            "• Impostazioni App\n"
            "• Gestisci Profili Utenti\n"
            "• Cambia Password\n"
            "• Registra Prodotto\n"
            "• Gamification — punti, livelli e badge\n"
            "• Controlla / Forza Aggiornamento Software\n"
            "• Annulla Ultimo Aggiornamento\n"
            "• Visualizza Storico Aggiornamenti\n"
            "• Storico Anomalie  |  Log Accessi\n"
            "• Aggiorna Librerie Python\n"
            "• Verifica Moduli (GitHub)\n"
            "• Contatta Assistenza\n"
            "\n 📁 DATABASE\n"
            "• Esporta DB Transazioni  |  Importa DB Transazioni\n"
            "• Reset Database\n"
            "• Cancella Voci Bulk\n"
            "• Gestisci Backup e Ripristino\n"
            "• Esegui Backup Completo Zip\n"
            "• Apri Manuale (Ctrl+M)\n"
            "\n 🌐 WEBUI\n"
            "• Visualizza Interfaccia Web Locale\n"
            "• Gestisci Certificati SSL\n"
            "• QRcode Connessioni Gateway Remoti\n"
            "• Manuale CertBot SSL\n"
            "\n 🔧 ALTRE VOCI DELLA BARRA\n"
            "• 💼 Portafoglio — Accesso rapido al Fondo Risparmio\n"
            "• ❓ Info — Apre questa guida\n"
            "• ⚙️ Configura — Impostazioni complete dell'applicazione\n"
            "• 🔌 Esci — Salva ed esce dal programma (anche Ctrl+Q dal menu Gestione)\n"
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
    btn_stampa.bind("<Button-1>", lambda e: self._stampa_lista_diretta(testo_filtri + "\n" + testo_icone + "\n" + testo_menu, self.show_custom_warning))
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
    for ico_key, txt, cmd in [("email", " Email", apri_email), ("github", " GitHub", apri_github), ("studio", " Manuale Online", apri_manuale), ("python", " Python", apri_link_python)]:
        img = self.icone_gui.get(ico_key)
        lbl = tk.Label(links_frame, text=txt, image=img, compound="left", fg="#3498db", bg=self.COLOR_TOPLEVEL, cursor="hand2", font=("Arial", 9))
        lbl.image = img
        lbl.pack(side=tk.LEFT, padx=10)
        lbl.bind("<Button-1>", cmd)
    def _crea_tab_scrollabile(parent_tab, testo):
        container = tk.Frame(parent_tab, bg=self.COLOR_WHITE, highlightbackground=self.COLOR_TOPLEVEL, highlightthickness=4, bd=0)
        container.pack(fill="both", expand=True, padx=15, pady=2)
        canvas = tk.Canvas(container, bg=self.COLOR_WHITE, highlightthickness=0, bd=0)
        scroll = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        frm_testo = tk.Frame(canvas, bg=self.COLOR_WHITE)
        frm_testo.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=frm_testo, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        tk.Label(frm_testo, text=testo, font=("Arial", 10),
                 bg=self.COLOR_WHITE, fg=self.COLOR_BLACK, justify=tk.LEFT, anchor='nw',
                 wraplength=890).pack(fill='both', expand=True, padx=15, pady=5)
        for widget in (canvas, frm_testo):
            widget.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
            widget.bind("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))
            widget.bind("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))
    tab_filtri = ttk.Frame(notebook)
    _add_tab(tab_filtri, "filtri", "Filtri e Tabelle")
    _crea_tab_scrollabile(tab_filtri, testo_filtri)
    tab_icone = ttk.Frame(notebook)
    _add_tab(tab_icone, "tools", "Pulsanti Icone")
    _crea_tab_scrollabile(tab_icone, testo_icone)
    tab_menu = ttk.Frame(notebook)
    _add_tab(tab_menu, "home", "Menu Laterale")
    _crea_tab_scrollabile(tab_menu, testo_menu)
    info_win.update_idletasks()
    w, h = info_win.winfo_reqwidth(), info_win.winfo_reqheight()
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    info_win.geometry(f"1000x660+{x}+{y}")
    info_win.deiconify()
    info_win.grab_set()
    info_win.bind("<Escape>", lambda e: info_win.destroy())
