#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk

def setup_sidebar(self):
    import __main__ as _app
    ANIMAZIONI = _app.ANIMAZIONI
    self.menu_aperto = None 
    self.sidebar_espansa = False
    if not hasattr(self, 'icone_gui'): self.icone_gui = {} 
    self.sidebar = tk.Frame(self, bg=self.MENU_BG_DARK, width=45, bd=0) 
    self.sidebar.pack(side="left", fill="y") 
    self.sidebar.pack_propagate(False) 
    self.btn_toggle = tk.Button(self.sidebar, text="➤", font=("Arial", 11),
                               bg=self.MENU_BG_DARK, fg=self.COLOR_GREEN,
                               bd=0, activebackground=self.MENU_ACT_BG_COLOR,
                               command=self.toggle_sidebar, cursor="hand2")
    self.btn_toggle.pack(fill="x", pady=5)
    self.lbl_logo = tk.Label(
        self.sidebar, 
        text="O.C.", 
        font=("Arial", 10, "bold"),
        bg=self.MENU_BG_DARK, 
        fg=self.COLOR_GREEN, 
        pady=10
    )
    self.lbl_logo.pack(fill="x")
    self._search_var = tk.StringVar()
    self._search_entry = tk.Entry(
        self.sidebar, textvariable=self._search_var,
        font=("Arial", 8), bg="#2a2a2a", fg="white",
        insertbackground="white", relief="flat", bd=4,
        highlightthickness=1, highlightbackground="#4a4a4a", highlightcolor=self.COLOR_GREEN
    )
    self._search_var.trace_add("write", self._filtra_sidebar)
    self._search_results_frame = tk.Frame(self.sidebar, bg=self.MENU_BG_DARK)
    self._search_overlay = None
    self._search_results_frame.pack_propagate(False)
    if ANIMAZIONI:
        self._animate_logo_text() 
    self.menu_sidebar_data = [ 
        ("documenti_B", "Gestione", self.pop_gestione), 
        ("report_B", "Analisi", self.pop_analisi), 
        ("banca_B", "Finanze", self.pop_finanze), 
        ("timer_B", "Ricorrenze", self.pop_ricorrenze), 
        ("calendario_B", "Categorie", self.pop_categorie), 
        ("tools_B", "Sistema", self.pop_opzioni), 
        ("documenti_B", "Database", self.pop_info), 
        ("qr_B", "WebUI", self.web_info),
        ("lavoro_B", "Portafoglio", self.apri_fondo_risparmio), 
    ] 
    self.widgets_voci = [] 
    for icon_key, testo, comando in self.menu_sidebar_data: 
        self._crea_voce_sidebar(icon_key, testo, comando) 
    self.spacer = tk.Frame(self.sidebar, bg=self.MENU_BG_DARK) 
    self.spacer.pack(fill="both", expand=True)
    self._crea_voce_sidebar("help_B", "Info", self.show_info_app)
    self._crea_voce_sidebar("filtri_B", "Configura", self.gestisci_configurazione)
    self._crea_voce_sidebar("spina_B", "Esci", self._on_close, icon_fallback="✖") 
    self.configura_scorciatoie() 
def _animate_logo_text(self, color_idx=0, sub_step=0):
    if not hasattr(self, 'lbl_logo') or not self.lbl_logo.winfo_exists():
        return
    palette = [
        (0, 200, 83),
        (0, 85, 255),
        (170, 0, 255),
        (255, 0, 85)
    ]
    def lerp(c1, c2, t):
        return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
    next_idx = (color_idx + 1) % len(palette)
    t = sub_step / 15.0
    current_rgb = lerp(palette[color_idx], palette[next_idx], t)
    color_hex = f'#{current_rgb[0]:02x}{current_rgb[1]:02x}{current_rgb[2]:02x}'
    try:
        self.lbl_logo.configure(fg=color_hex)
        new_sub_step = sub_step + 1
        new_color_idx = color_idx
        if new_sub_step > 15:
            new_sub_step = 0
            new_color_idx = next_idx
        self.after(60, lambda: self._animate_logo_text(new_color_idx, new_sub_step))
    except Exception:
        pass
def toggle_sidebar(self):
    if not self.sidebar_espansa:
        self.espandi_sidebar()
        self.btn_toggle.configure(text="◀")
        self.sidebar_espansa = True
    else:
        self.contrai_sidebar_manuale()
        self.btn_toggle.configure(text="➤")
        self.sidebar_espansa = False
def contrai_sidebar_manuale(self):
    self.sidebar.configure(width=45)
    self.lbl_logo.config(text="OC", font=("Arial", 10, "bold"), pady=15)
    self.sidebar_espansa = False
    if hasattr(self, 'lbl_tipo_percentuale'): 
        self.lbl_tipo_percentuale.pack(side=tk.LEFT, padx=4)
    if hasattr(self, '_search_entry'):
        self._search_entry.pack_forget()
    if hasattr(self, '_search_results_frame'):
        self._search_results_frame.pack_forget()
        for w in self._search_results_frame.winfo_children():
            w.destroy()
    if hasattr(self, '_search_var'):
        self._search_var.set("")
    for btn, testo in [
        (self.btn_oggi_stats, " Oggi"),
        (self.btn_giorno, " Giorno"),
        (self.btn_mese, " Mese"),
        (self.btn_anno, " Anno"),
        (self.btn_totali, " Totali"),
    ]:
        btn.configure(text=testo)
    self._ricerca_globale_var.set("")
    self.ricerca_globale_entry.pack_forget()    
def _crea_voce_sidebar(self, icon_key, testo, comando, icon_fallback="•"): 
    f = tk.Frame(self.sidebar, bg=self.MENU_BG_DARK, cursor="hand2") 
    f.pack(fill="x", side="top" if testo != "Esci" else "bottom") 
    img = self.icone_gui.get(icon_key) 
    l_icona = tk.Label(f, bg=self.MENU_BG_DARK) 
    if img: 
        l_icona.configure(image=img) 
        l_icona.image = img  
    else: 
        l_icona.configure(text=icon_fallback, fg=self.MENU_FG_LIGHT) 
    l_icona.pack(side="left", pady=12, padx=(13, 4))          
    l_testo = tk.Label(f, text=testo, font=("Arial", 9, "bold"), 
                       bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT) 
    l_testo.pack(side="left", padx=(2, 6)) 
    for w in (f, l_icona, l_testo): 
        w.bind("<Button-1>", lambda e, c=comando: c())
    def _on_enter(e):
        f.config(bg=self.MENU_BG_DARK)
        l_icona.config(bg=self.MENU_BG_DARK)
        l_testo.config(bg=self.MENU_BG_DARK, fg=self.COLOR_HIGHLIGHT)
        l_icona.pack_configure(pady=(8, 16))
        f.after(120, lambda: l_icona.pack_configure(pady=12) if f.winfo_exists() else None)
    def _on_leave(e):
        f.config(bg=self.MENU_BG_DARK)
        l_icona.config(bg=self.MENU_BG_DARK)
        l_testo.config(bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT)
        l_icona.pack_configure(pady=12)
    for w in (f, l_icona, l_testo):
        w.bind("<Enter>", _on_enter)
        w.bind("<Leave>", _on_leave)
    self.widgets_voci.append(f)
def pop_gestione(self): 
    m = tk.Menu(self, tearoff=0, bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT,  
                activebackground=self.MENU_ACT_BG_COLOR, font=("Arial", 9)) 
    self._add_m_item(m, "Gestione SuperMarket", "spesa", self.spesa_supermercato) 
    self._add_m_item(m, "Gestione Documenti", "documenti", self.gestisci_archivi_pdf) 
    self._add_m_item(m, "Gestione Documenti Personali", "documenti", self.gestisci_documenti_personali)
    self._add_m_item(m, "Gestione Utenze", "mobile", self.utenze, "Ctrl+U") 
    self._add_m_item(m, "ImmoBil — Gestione Immobili", "home", self.immobil)
    self._add_m_item(m, "AutoPark — Gestione Veicoli", "veicoli", self.veicoli)
    m.add_separator() 
    self._add_m_item(m, "Sincronizza Acquisti Email (Gmail)", "sync", self.avvia_sincronizzazione) 
    self._add_m_item(m, "Importa Documento AI (Gemini)", "documenti", self.apri_finestra_importa)
    self._add_m_item(m, "Log Importazioni", "sync", self.mostra_log_importazioni)
    m.add_separator() 
    self._add_m_item(m, "Rubrica", "oggi", self.rubrica_app, "Ctrl+R") 
    self._add_m_item(m, "Promemoria", "promemoria", self.gestisci_promemoria, "Ctrl+Y") 
    self._add_m_item(m, "GCalendar", "calendario", self.launch_qr_svg_generator)
    self._add_m_item(m, "Piano Dieta", "spesa", self.apri_dieta) 
    self._add_m_item(m, "MyBusiness", "lavoro_B", self.apri_studio)
    m.add_separator() 
    self._add_m_item(m, "Stampa", "stampa", self.anteprima_e_stampa_txt, "Ctrl+P") 
    self._add_m_item(m, "Pannello Controllo", "timer", self.calcola_mancanti, "Ctrl+Z") 
    self._add_m_item(m, "Calcolatrice", "calcolatrice", self.apri_calcolatrice, "Ctrl+E") 
    m.add_separator() 
    self._add_m_item(m, "Salva ed Esci", "chiudi", self._on_close, "Ctrl+Q") 
    self._add_m_item(m, "Riduci a Icona", "iconizza", self.iconify, "Ctrl+X") 
    self._mostra_popup(m, 50) 
def pop_analisi(self): 
    m = tk.Menu(self, tearoff=0, bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT,  
                activebackground=self.MENU_ACT_BG_COLOR, font=("Arial", 9)) 
    self._add_m_item(m, "Ricerca Globale", "search", self.cerca_operazioni, "Ctrl+F")
    self._add_m_item(m, "Gestione Tag #", "filtri", self.apri_gestione_tag)
    self._add_m_item(m, "Confronta Periodi", "report", self.open_compare_window, "Ctrl+N")
    self._add_m_item(m, "FairShare Partecipanti", "utenti", self.mostra_dare_avere, "Ctrl+D")
    m.add_separator() 
    self._add_m_item(m, "Time Machine", "timer_sync", self.time_machine, "Ctrl+W") 
    self._add_m_item(m, "Aggrega Categorie", "filtri", self.gruppo_categorie, "Ctrl+G")
    m.add_separator()  
    self._add_m_item(m, "Proiezione - Fondo Risparmio", "ccv", self.apri_fondo_risparmio, "Ctrl+A")
    self._add_m_item(m, "Grafici Interattivi", "grafico_linea", self.mostra_analisi_grafici, "Alt+H")
    self._add_m_item(m, "Andamento Risparmio", "grafico_linea", self.apri_andamento_risparmio)
    self._add_m_item(m, "Schedulatore Notifiche", "timer_sync", self.apri_schedulatore) 
    self._add_m_item(m, "Calcolatore Inflazione", "calcolatrice", self.apri_calcolatore_inflazione)
    self._add_m_item(m, "Bilancio Grafico PDF", "grafico_linea", self.genera_report_pdf, "Alt+R") 
    self._mostra_popup(m, 100) 
def pop_finanze(self): 
    m = tk.Menu(self, tearoff=0, bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT,  
                activebackground=self.MENU_ACT_BG_COLOR, font=("Arial", 9)) 
    self._add_m_item(m, "Portafoglio Bancario", "saldo", self.open_saldo_conto, "Ctrl+S")
    self._add_m_item(m, "Portafoglio Investimenti", "lavoro", self.apri_portafoglio) 
    self._add_m_item(m, "Calcolo Mutuo/Prestiti", "banca", self.calcolo_mutuo_prestito, "Ctrl+O") 
    m.add_separator() 
    self._add_m_item(m, "Bilancio Giorno", "calendario", self.export_giorno_forzato, "Alt+J") 
    self._add_m_item(m, "Bilancio Mese", "calendario", self.export_month_detail, "Alt+K") 
    self._add_m_item(m, "Bilancio Anno", "report", self.export_anno_dettagliato, "Alt+L") 
    self._add_m_item(m, "Bilancio Storico Totale", "report", self.export_storico_totale, "Alt+G")
    self._add_m_item(m, "Analisi e Bilanci", "report", self.popup_scelta_estratto, "Alt+E")
    self._add_m_item(m, "Estratti per Metodo e Conti", "ccv", self.apri_estratti_metodo, "")
    self._add_m_item(m, "Analisi Andamento Bilancio OpenAI", "report", self.analizza_andamento_ia)
    self._add_m_item(m, "Analisi e Confronto Documenti OpenAI", "report", self.confronta_bollette_ia)
    self._mostra_popup(m, 140)
def pop_ricorrenze(self): 
    m = tk.Menu(self, tearoff=0, bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT,  
                activebackground=self.MENU_ACT_BG_COLOR, font=("Arial", 9)) 
    self._add_m_item(m, "Gestione Ricorrenze", "descrizione", self.mostra_ricorrenza_popup, "Ctrl+T") 
    self._add_m_item(m, "Lista Ricorrenze", "descrizione", self.mostra_lista_ricorrenze, "Ctrl+L") 
    self._add_m_item(m, "Scadenze Mese", "scadenze", self.scadenze_mese, "Ctrl+J") 
    self._mostra_popup(m, 180) 

def pop_opzioni(self): 
    m = tk.Menu(self, tearoff=0, bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT,  
                activebackground=self.MENU_ACT_BG_COLOR, font=("Arial", 9))
    self._add_m_item(m, "Impostazioni App", "filtri", self.gestisci_configurazione)
    m.add_separator()
    self._add_m_item(m, "Cambia Password", "api_key", self.apri_cambio_password)
    m.add_separator()
    self._add_m_item(m, "Registra Prodotto", "api_key", self.apri_registrazione)
    m.add_separator()
    self._add_m_item(m, "Gamification", "badge_novizio", self.mostra_dettaglio_gamification)
    m.add_separator()
    self._add_m_item(m, "Controlla Aggiornamento Software", "sync", self.forza_check_aggiornamento_con_api) 
    self._add_m_item(m, "Forza Aggiornamento Software", "sync", self.forza_aggiorna) 
    self._add_m_item(m, "Annulla Ultimo Aggiornamento", "reset", self.ripristina_da_backup) 
    self._add_m_item(m, "Visualizza Storico Aggiornamenti", "descrizione", self.visualizza_changelog) 
    m.add_separator() 
    self._add_m_item(m, "Storico Anomalie", "scadenze", self.mostra_registro_errori)
    self._add_m_item(m, "Log Accessi", "scadenze", self.mostra_log_accessi) 
    m.add_separator()
    self._add_m_item(m, "Aggiorna Librerie Python", "sync", self.aggiorna_librerie_pip)
    self._add_m_item(m, "Verifica Moduli (GitHub)", "sync", self.verifica_moduli_git)
    m.add_separator()
    self._add_m_item(m, "Contatta Assistenza", "help", lambda: self.apri_pannello_topic(self.topic_unico))
    self._mostra_popup(m, 260) 
def pop_info(self): 
    m = tk.Menu(self, tearoff=0, bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT,  
                activebackground=self.MENU_ACT_BG_COLOR, font=("Arial", 9))
    self._add_m_item(m, "Esporta DB Transazioni", "carica", self.export_db) 
    self._add_m_item(m, "Importa DB Transazioni", "archivia", self.import_db)
    m.add_separator() 
    self._add_m_item(m, "Reset Database", "reset", self.show_reset_dialog) 
    self._add_m_item(m, "Cancella Voci Bulk", "delete", self.apri_cancella_spese_treeview_unica)
    m.add_separator() 
    self._add_m_item(m, "Gestisci Backup e Ripristino", "archivia", self.gestisci_backup_popup)
    self._add_m_item(m, "Esegui Backup Completo Zip", "archivia", self.esegui_backup_zip)
    m.add_separator() 
    self._add_m_item(m, "Apri Manuale", "documenti", self.scarica_manuale, "Ctrl+M") 
    self._mostra_popup(m, 300)
def _mostra_popup(self, menu, y_offset): 
    if self.menu_aperto == menu: return 
    if self.menu_aperto: 
        try: self.menu_aperto.unpost() 
        except: pass 
    self.menu_aperto = menu 
    x = self.sidebar.winfo_rootx() + self.sidebar.winfo_width() 
    y = self.sidebar.winfo_rooty() + y_offset 
    try: 
        menu.post(x, y) 
        self.bind_all("<Button-1>", self._verifica_chiusura_menu, add="+") 
        root = self.winfo_toplevel()
        root.bind("<FocusOut>", lambda e: self._chiudi_menu_orfano(e))
    except Exception as e: 
        print(f"Errore apertura menu: {e}")
def _chiudi_menu_orfano(self, event=None):
    if self.menu_aperto:
        try:
            self.menu_aperto.unpost()
        except:
            pass
        self.menu_aperto = None
        root = self.winfo_toplevel()
        root.unbind("<FocusOut>")
        self.unbind_all("<Button-1>") 
def _verifica_chiusura_menu(self, event): 
    if self.menu_aperto: 
        if not isinstance(event.widget, tk.Menu): 
            try: self.menu_aperto.unpost() 
            except: pass
            self.menu_aperto = None
            self.unbind_all("<Button-1>")
            
def espandi_sidebar(self):
    import __main__ as _app
    VERSION = _app.VERSION
    self.sidebar.configure(width=120) 
    self.lbl_logo.config( 
        text=f" O.C. v.{VERSION} ",  
        font=("Arial", 10, "bold"), 
        bg=self.MENU_BG_DARK, 
        fg=self.COLOR_GREEN, 
        padx=10, 
        pady=2
    )
    if hasattr(self, 'lbl_tipo_percentuale'): 
        self.lbl_tipo_percentuale.pack_forget()
    if hasattr(self, '_search_entry'):
        self._search_entry.pack(after=self.lbl_logo, fill="x", padx=6, pady=(2, 4))
    if hasattr(self, '_search_results_frame'):
        self._search_results_frame.pack(after=self._search_entry, fill="x")
    if hasattr(self, '_search_var'):
        self._search_var.set("")
    self.after(100, lambda: self._search_entry.focus_set() if hasattr(self, '_search_entry') else None)
    for btn, testo in [(self.btn_oggi_stats, " Oggi"), (self.btn_giorno, " Giorno"), (self.btn_mese, " Mese"), (self.btn_anno, " Anno"), (self.btn_totali, " Totali")]:
        btn.configure(text="")
            
def _add_m_item(self, target, label, icon_key, command, acc=""): 
    img = self.icone_gui.get(icon_key) 
    def wrapped(c=command):
        if self.menu_aperto:
            try: self.menu_aperto.unpost()
            except: pass
            self.menu_aperto = None
            self.unbind_all("<Button-1>")
        c()
    target.add_command(label=f" {label}", image=img, compound="left",  
                        command=wrapped, accelerator=acc)
def _filtra_sidebar(self, *_):
    testo = self._search_var.get().strip().lower()
    if hasattr(self, '_search_overlay') and self._search_overlay and self._search_overlay.winfo_exists():
        self._search_overlay.place_forget()
        self._search_overlay.destroy()
        self._search_overlay = None
    if not testo:
        return
    TUTTE = [
        ("Gestione SuperMarket",                  self.spesa_supermercato),
        ("Gestione Documenti",                    self.gestisci_archivi_pdf),
        ("Gestione Documenti Personali",          self.gestisci_documenti_personali),
        ("Gestione Utenze",                       self.utenze),
        ("ImmoBil — Gestione Immobili",           self.immobil),
        ("Veicoli",                               self.veicoli),
        ("Sincronizza Acquisti Email",            self.avvia_sincronizzazione),
        ("Importa Documento AI",                  self.apri_finestra_importa),
        ("Log Importazioni",                      self.mostra_log_importazioni),
        ("Rubrica",                               self.rubrica_app),
        ("Promemoria",                            self.gestisci_promemoria),
        ("GCalendar",                             self.launch_qr_svg_generator),
        ("Piano Dieta",                           self.apri_dieta),
        ("Studio Professionale",                  self.apri_studio),
        ("Portafoglio Bancario",                  self.open_saldo_conto),
        ("Stampa",                                self.anteprima_e_stampa_txt),
        ("Pannello Controllo",                    self.calcola_mancanti),
        ("Calcolatrice",                          self.apri_calcolatrice),
        ("Cancella Voci Bulk",                    self.apri_cancella_spese_treeview_unica),
        ("Ricerca Globale",                       self.cerca_operazioni),
        ("Gestione Tag #",                        self.apri_gestione_tag),
        ("Confronta Periodi",                     self.open_compare_window),
        ("FairShare Dare & Avere",                self.mostra_dare_avere),
        ("Time Machine",                          self.time_machine),
        ("Aggrega Categorie",                     self.gruppo_categorie),
        ("Fondo Risparmio",                       self.apri_fondo_risparmio),
        ("Grafici Interattivi",                   self.mostra_analisi_grafici),
        ("Andamento Risparmio",                   self.apri_andamento_risparmio),
        ("Schedulatore Notifiche",                self.apri_schedulatore),
        ("Calcolatore Inflazione",                self.apri_calcolatore_inflazione),
        ("Bilancio Grafico PDF",                  self.genera_report_pdf),
        ("Calcolo Mutuo/Prestiti",                self.calcolo_mutuo_prestito),
        ("Portafoglio Investimenti",              self.apri_portafoglio),
        ("Bilancio Giorno",                       self.export_giorno_forzato),
        ("Bilancio Mese",                         self.export_month_detail),
        ("Bilancio Anno",                         self.export_anno_dettagliato),
        ("Bilancio Storico Totale",               self.export_storico_totale),
        ("Analisi e Bilanci",                     self.popup_scelta_estratto),
        ("Estratti per Metodo e Conti",           self.apri_estratti_metodo),
        ("Analisi Andamento OpenAI",              self.analizza_andamento_ia),
        ("Confronto Bollette OpenAI",             self.confronta_bollette_ia),
        ("Gestione Ricorrenze",                   self.mostra_ricorrenza_popup),
        ("Lista Ricorrenze",                      self.mostra_lista_ricorrenze),
        ("Scadenze Mese",                         self.scadenze_mese),
        ("Controlla Ricorrenti",                  self.controlla_ricorrenti_manual),
        ("Analisi Categorie",                     self.open_analisi_categoria),
        ("Suggerisci Categorie",                  self.apri_categorie_suggerite),
        ("Gestione Categorie",                    self.mostra_categorie_popup),
        ("Cancella Categorie Bulk",               self.apri_cancella_multiplo),
        ("Editor Memoria Categorie",              lambda: self.mostra_editor_memoria_categorie()),
        ("Impostazioni App",                      self.gestisci_configurazione),
        ("Cambia Password",                       self.apri_cambio_password),
        ("Registra Prodotto",                     self.apri_registrazione),
        ("Controlla Aggiornamenti",               self.forza_check_aggiornamento_con_api),
        ("Forza Aggiornamento",                   self.forza_aggiorna),
        ("Annulla Ultimo Aggiornamento",          self.ripristina_da_backup),
        ("Storico Aggiornamenti",                 self.visualizza_changelog),
        ("Storico Anomalie",                      lambda: self.mostra_registro_errori()),
        ("Log Accessi Web",                       self.mostra_log_accessi),
        ("Aggiorna Librerie Python",              self.aggiorna_librerie_pip),
        ("Verifica Moduli (GitHub)",              self.verifica_moduli_git),
        ("Contatta Assistenza",                   lambda: self.apri_pannello_topic(self.topic_unico)),
        ("Esporta DB Transazioni",                self.export_db),
        ("Importa DB Transazioni",                self.import_db),
        ("Reset DB",                              self.show_reset_dialog),
        ("Backup Completo Zip",                   self.esegui_backup_zip),
        ("Apri Manuale",                          self.scarica_manuale),
        ("Interfaccia Web Locale",                self.apri_webserver),
        ("Certificati SSL",                       self.gestisci_certificati),
        ("QR Code Connessioni",                   self.mostra_qr_popup_label),
        ("Manuale CertBot SSL",                   self.scarica_manuale_ssl),
        ("Gestisci Backup e Ripristino",          self.gestisci_backup_popup),
    ]
    trovati = [(label, cmd) for label, cmd in TUTTE if testo in label.lower()][:10]
    if not trovati:
        return
    self.update_idletasks()
    entry_abs_x = self._search_entry.winfo_rootx()
    entry_abs_y = self._search_entry.winfo_rooty()
    self_abs_x  = self.winfo_rootx()
    self_abs_y  = self.winfo_rooty()
    self_h      = self.winfo_height()
    overlay_x = entry_abs_x - self_abs_x + self._search_entry.winfo_width() + 2
    entry_y   = entry_abs_y - self_abs_y
    row_h     = 26
    popup_w   = 260
    popup_h   = len(trovati) * row_h
    overlay_y = entry_y
    if overlay_y + popup_h > self_h - 10:
        overlay_y = self_h - popup_h - 10
    overlay = tk.Frame(self, bg=self.MENU_BG_DARK, bd=1, relief="solid")
    overlay.place(x=overlay_x, y=overlay_y, width=popup_w, height=popup_h)
    self._search_overlay = overlay
    def _chiudi():
        if hasattr(self, '_search_overlay') and self._search_overlay and self._search_overlay.winfo_exists():
            self._search_overlay.place_forget()
            self._search_overlay.destroy()
            self._search_overlay = None
    for i, (label, cmd) in enumerate(trovati):
        bg = self.MENU_BG_DARK
        def _esegui(c=cmd):
            _chiudi()
            self._search_var.set("")
            for w in self._search_results_frame.winfo_children():
                w.destroy()
            self.contrai_sidebar_manuale()
            self.btn_toggle.configure(text="➤")
            self.sidebar_espansa = False
            try:
                c()
            except Exception as ex:
                print(f"[SEARCH] {ex}")
        row = tk.Frame(overlay, bg=bg, height=row_h)
        row.pack(fill="x")
        row.pack_propagate(False)
        lbl = tk.Label(
            row, text=label,
            font=("Arial", 9), bg=bg, fg=self.MENU_FG_LIGHT,
            anchor="w", padx=8, cursor="hand2"
        )
        lbl.pack(fill="both", expand=True)
        def _on_enter(e, w=row, l=lbl):
            w.config(bg=self.COLOR_HIGHLIGHT)
            l.config(bg=self.COLOR_HIGHLIGHT, fg="#ffffff")
        def _on_leave(e, w=row, l=lbl, b=bg):
            w.config(bg=b)
            l.config(bg=b, fg=self.MENU_FG_LIGHT)
        lbl.bind("<Button-1>", lambda e, f=_esegui: f())
        lbl.bind("<Enter>", _on_enter)
        lbl.bind("<Leave>", _on_leave)
        row.bind("<Button-1>", lambda e, f=_esegui: f())

