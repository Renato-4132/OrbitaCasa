#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#testa
import time
import tkinter as tk

class MenuPersonalizzato(tk.Frame):
    def __init__(self, master, bg, fg, active_bg, border_color, font=("Arial", 9)):
        super().__init__(master, bg=border_color, bd=0)
        self._master_ref = master
        self._bg = bg
        self._fg = fg
        self._active_bg = active_bg
        self._font = font
        self._inner = tk.Frame(self, bg=bg, bd=0)
        self._inner.pack(fill="both", expand=True, padx=1, pady=1)

    def add_command(self, label="", image=None, compound="left", command=None, accelerator=""):
        row = tk.Frame(self._inner, bg=self._bg)
        row.pack(fill="x")
        widgets = [row]
        if image:
            l_icona = tk.Label(row, image=image, bg=self._bg)
            l_icona.image = image
            l_icona.pack(side="left", padx=(10, 6), pady=2)
            widgets.append(l_icona)
        l_testo = tk.Label(row, text=label, bg=self._bg, fg=self._fg,
                            font=self._font, anchor="w")
        l_testo.pack(side="left", fill="x", expand=True, pady=2)
        widgets.append(l_testo)
        if accelerator:
            l_acc = tk.Label(row, text=accelerator, bg=self._bg, fg=self._fg,
                              font=self._font)
            l_acc.pack(side="right", padx=(6, 12))
            widgets.append(l_acc)

        def _esegui(event=None, _c=command):
            self.unpost()
            if _c:
                _c()

        def _enter(event=None, _w=widgets):
            for w in _w:
                w.configure(bg=self._active_bg)

        def _leave(event=None, _w=widgets):
            for w in _w:
                w.configure(bg=self._bg)

        for w in widgets:
            w.bind("<Button-1>", _esegui)
            w.bind("<Enter>", _enter)
            w.bind("<Leave>", _leave)

    def add_separator(self):
        sep = tk.Frame(self._inner, bg=self._fg, height=1)
        sep.pack(fill="x", padx=8, pady=5)

    def post(self, x, y):
        self.update_idletasks()
        altezza = self.winfo_reqheight()
        larghezza = self.winfo_reqwidth()
        root = self._master_ref.winfo_toplevel()
        root_top = root.winfo_rooty()
        root_bottom = root_top + root.winfo_height()
        root_right = root.winfo_rootx() + root.winfo_width()
        if y + altezza > root_bottom:
            y = max(root_top, root_bottom - altezza)
        if x + larghezza > root_right:
            x = max(root.winfo_rootx(), root_right - larghezza)
        rel_x = int(x) - root.winfo_rootx()
        rel_y = int(y) - root.winfo_rooty()
        self.place(x=rel_x, y=rel_y)
        self.lift()

    def unpost(self):
        try:
            self.place_forget()
            self.destroy()
        except Exception:
            pass

def setup_sidebar(self):
    import __main__ as _app
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
    self.lbl_logo_container = tk.Frame(self.sidebar, bg=self.MENU_BG_DARK, height=43)
    self.lbl_logo_container.pack(fill="x")
    self.lbl_logo_container.pack_propagate(False)
    self._logo_img = _carica_icona_scintille(self)
    self._busta_img = _carica_icona_scintille(self, nome="scadenze_B")
    self._busta_img_dim = _carica_icona_scintille(self, nome="scadenze_B", alpha=0.3)
    self._pool_img = _carica_icona_scintille(self, nome="utenti_B")
    self._pool_img_dim = _carica_icona_scintille(self, nome="utenti_B", alpha=0.3)
    self._agenda_img = _carica_icona_scintille(self, nome="promemoria_B")
    self._agenda_img_dim = _carica_icona_scintille(self, nome="promemoria_B", alpha=0.3)
    self.lbl_logo = tk.Label(self.lbl_logo_container, bg=self.MENU_BG_DARK)
    if self._logo_img:
        self.lbl_logo.configure(image=self._logo_img)
        self.lbl_logo.image = self._logo_img
    self.lbl_logo.pack(side="left", pady=12, padx=(13, 4))
    self.lbl_logo_container.bind("<Button-1>", lambda e: self.mostra_piramide())
    VERSION = getattr(_app, 'VERSION', '')
    self.lbl_logo_testo = tk.Label(
        self.lbl_logo_container, text=f"O.C. v.{VERSION}", font=("Arial", 9, "bold"),
        bg=self.MENU_BG_DARK, fg=self.COLOR_GREEN
    )
    self.lbl_logo_testo.bind("<Button-1>", lambda e: self.mostra_piramide())
    from moduli.messaggi_servizio import _aggiorna_badge_messaggi_servizio, click_logo_sidebar
    self.lbl_logo.bind("<Button-1>", lambda e: click_logo_sidebar(self, e))
    if getattr(self, "_messaggi_servizio_pendenti", []) or getattr(self, "_pool_novita_pendenti", 0) or getattr(self, "_agenda_novita_pendenti", 0):
        _aggiorna_badge_messaggi_servizio(self)
    self._search_var = tk.StringVar()
    self._search_entry = tk.Entry(
        self.sidebar, textvariable=self._search_var,
        font=("Arial", 8), bg=self.COLOR_WIDGET_BG, fg=self.MENU_FG_LIGHT,
        insertbackground=self.MENU_FG_LIGHT, relief="flat", bd=4,
        highlightthickness=1, highlightbackground=self.COLOR_HIGHLIGHT, highlightcolor=self.COLOR_HIGHLIGHT
    )
    self._search_var.trace_add("write", self._filtra_sidebar)
    self._search_results_frame = tk.Frame(self.sidebar, bg=self.MENU_BG_DARK)
    self._search_overlay = None
    self._search_results_frame.pack_propagate(False)
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
    
def _carica_icona_scintille(self, size=(20, 20), nome="scintille_B", alpha=1.0):
    import os
    import __main__ as _app
    from PIL import Image, ImageTk
    p = os.path.join(_app.DB_DIR, "resources", f"{nome}.png")
    if not os.path.exists(p):
        return None
    try:
        img = Image.open(p).convert("RGBA").resize(size, Image.LANCZOS)
        if alpha < 1.0:
            img.putalpha(img.getchannel("A").point(lambda a: int(a * alpha)))
        return ImageTk.PhotoImage(img)
    except Exception:
        return None

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
    self.sidebar_espansa = False
    if hasattr(self, 'lbl_logo_testo'):
        self.lbl_logo_testo.pack_forget()
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
        (self.btn_importa_popup, "Import IA"),
        (self.btn_chiedi_ia_popup, "Chiedi IA"),
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
    l_icona.pack(side="left", pady=9, padx=(13, 4))          
    l_testo = tk.Label(f, text=testo, font=("Arial", 9, "bold"), 
                       bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT) 
    l_testo.pack(side="left", padx=(2, 6)) 
    for w in (f, l_icona, l_testo): 
        w.bind("<Button-1>", lambda e, c=comando: c())
        
    def _on_enter(e):
        f.config(bg=self.MENU_BG_DARK)
        l_icona.config(bg=self.MENU_BG_DARK)
        l_testo.config(bg=self.MENU_BG_DARK, fg=self.COLOR_HIGHLIGHT)
        l_icona.pack_configure(pady=(5, 13))
        f.after(120, lambda: l_icona.pack_configure(pady=9) if f.winfo_exists() else None)
        
    def _on_leave(e):
        f.config(bg=self.MENU_BG_DARK)
        l_icona.config(bg=self.MENU_BG_DARK)
        l_testo.config(bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT)
        l_icona.pack_configure(pady=9)
    for w in (f, l_icona, l_testo):
        w.bind("<Enter>", _on_enter)
        w.bind("<Leave>", _on_leave)
    self.widgets_voci.append(f)
    
def pop_gestione(self): 
    m = MenuPersonalizzato(
        self, bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT,
        active_bg=self.MENU_ACT_BG_COLOR, border_color=self.COLOR_HIGHLIGHT,
        font=("Arial", 9)
    ) 
    self._add_m_item(m, "Gestione SuperMarket", "spesa", self.spesa_supermercato) 
    self._add_m_item(m, "Gestione Documenti", "documenti", self.gestisci_archivi_pdf) 
    self._add_m_item(m, "Gestione Documenti Personali", "documenti", self.gestisci_documenti_personali)
    self._add_m_item(m, "Scansiona e salva PDF", "scansiona", self.scansiona_e_salva)
    self._add_m_item(m, "Gestione Utenze", "mobile", self.utenze) 
    self._add_m_item(m, "ImmoBil — Gestione Immobili", "home", self.immobil)
    self._add_m_item(m, "CasaCare — Manutenzione e Risparmio Casa", "auto_manutenzione", self.manutenzione_casa)
    self._add_m_item(m, "AutoPark — Gestione Veicoli", "veicoli", self.veicoli)
    self._add_m_item(m, "PetCare — Gestione Animali", "animali", self.animali)
    self._add_m_item(m, "StockBox — Magazzino e Scorte", "documenti", self.magazzino_app)
    m.add_separator() 
    self._add_m_item(m, "Sincronizza Acquisti Email (Gmail)", "sync", self.avvia_sincronizzazione) 
    self._add_m_item(m, "Importa Documento AI (Gemini)", "documenti", self.apri_finestra_importa)
    self._add_m_item(m, "Log Importazioni", "sync", self.mostra_log_importazioni)
    m.add_separator() 
    self._add_m_item(m, "Rubrica", "oggi", self.rubrica_app) 
    self._add_m_item(m, "Promemoria", "promemoria", self.gestisci_promemoria) 
    self._add_m_item(m, "GCalendar", "calendario", self.launch_qr_svg_generator)
    self._add_m_item(m, "Piano Dieta", "spesa", self.apri_dieta) 
    self._add_m_item(m, "MyBusiness", "lavoro", self.apri_studio)
    m.add_separator() 
    self._add_m_item(m, "Stampa", "stampa", self.anteprima_e_stampa_txt) 
    self._add_m_item(m, "Pannello Controllo", "timer", self.calcola_mancanti) 
    self._add_m_item(m, "Calcolatrice", "calcolatrice", self.apri_calcolatrice) 
    m.add_separator() 
    self._add_m_item(m, "Salva ed Esci", "chiudi", self._on_close) 
    self._add_m_item(m, "Riduci a Icona", "iconizza", self.iconify) 
    self._mostra_popup(m, 50) 
    
def pop_analisi(self): 
    m = MenuPersonalizzato(
        self, bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT,
        active_bg=self.MENU_ACT_BG_COLOR, border_color=self.COLOR_HIGHLIGHT,
        font=("Arial", 9)
    ) 
    self._add_m_item(m, "Ricerca Globale", "search", self.cerca_operazioni)
    self._add_m_item(m, "Gestione Tag #", "filtri", self.apri_gestione_tag)
    self._add_m_item(m, "Confronta Periodi", "report", self.open_compare_window)
    self._add_m_item(m, "FairShare Partecipanti", "utenti", self.mostra_dare_avere)
    self._add_m_item(m, "CommunityPool", "utenti", self.apri_community_pool) 
    m.add_separator() 
    self._add_m_item(m, "Proiezione - Fondo Risparmio", "ccv", self.apri_fondo_risparmio)
    self._add_m_item(m, "Grafici Interattivi", "grafico_linea", self.mostra_analisi_grafici)
    self._add_m_item(m, "Andamento Risparmio", "grafico_linea", self.apri_andamento_risparmio)
    self._add_m_item(m, "Schedulatore Notifiche", "timer_sync", self.apri_schedulatore) 
    self._add_m_item(m, "Calcolatore Inflazione", "calcolatrice", self.apri_calcolatore_inflazione)
    self._add_m_item(m, "Bilancio Grafico PDF", "grafico_linea", self.genera_report_pdf) 
    self._mostra_popup(m, 100) 
    
def pop_finanze(self): 
    m = MenuPersonalizzato(
        self, bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT,
        active_bg=self.MENU_ACT_BG_COLOR, border_color=self.COLOR_HIGHLIGHT,
        font=("Arial", 9)
    ) 
    self._add_m_item(m, "Portafoglio Bancario", "saldo", self.open_saldo_conto)
    self._add_m_item(m, "Portafoglio Investimenti", "lavoro", self.apri_portafoglio) 
    self._add_m_item(m, "Fondo Pensione", "badge_maestro", self.apri_fondo_pensione) 
    self._add_m_item(m, "Calcolo Mutuo/Prestiti", "banca", self.calcolo_mutuo_prestito) 
    m.add_separator() 
    self._add_m_item(m, "Bilancio Giorno", "calendario", self.export_giorno_forzato) 
    self._add_m_item(m, "Bilancio Mese", "calendario", self.export_month_detail) 
    self._add_m_item(m, "Bilancio Anno", "report", self.export_anno_dettagliato) 
    self._add_m_item(m, "Bilancio Storico Totale", "report", self.export_storico_totale)
    self._add_m_item(m, "Analisi e Bilanci", "report", self.popup_scelta_estratto)
    self._add_m_item(m, "Estratti per Metodo e Conti", "ccv", self.apri_estratti_metodo)
    self._add_m_item(m, "Analisi Andamento Bilancio OpenAI", "report", self.analizza_andamento_ia)
    self._add_m_item(m, "Analisi e Confronto Documenti OpenAI", "report", self.confronta_bollette_ia)
    self._add_m_item(m, "Chiedi al Database (Gemini AI)", "sparkles", self.chiedi_ia_database)
    self._mostra_popup(m, 140)
    
def pop_ricorrenze(self): 
    m = MenuPersonalizzato(
        self, bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT,
        active_bg=self.MENU_ACT_BG_COLOR, border_color=self.COLOR_HIGHLIGHT,
        font=("Arial", 9)
    ) 
    self._add_m_item(m, "Gestione Ricorrenze", "descrizione", self.mostra_ricorrenza_popup) 
    self._add_m_item(m, "Lista Ricorrenze", "descrizione", self.mostra_lista_ricorrenze) 
    self._add_m_item(m, "Scadenze Mese", "scadenze", self.scadenze_mese)
    self._add_m_item(m, "Pianifica", "timer", self.apri_gestione_spese_pianificate)
    self._mostra_popup(m, 180) 

def pop_opzioni(self): 
    m = MenuPersonalizzato(
        self, bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT,
        active_bg=self.MENU_ACT_BG_COLOR, border_color=self.COLOR_HIGHLIGHT,
        font=("Arial", 9)
    )
    self._add_m_item(m, "Impostazioni App", "filtri", self.gestisci_configurazione)
    self._add_m_item(m, "Personalizza Icone", "tools", self.apri_personalizza_icone)
    m.add_separator()
    self._add_m_item(m, "Gestisci Profili Utenti", "api_key", self.mostra_selettore_profilo)
    import __main__ as _app
    if _app.PROFILO_ATTIVO == _app.NOME_PROFILO_DEMO:
        self._add_m_item(m, "Esci da Modalità Demo", "reset", self.esci_modalita_demo)
    else:
        self._add_m_item(m, "Attiva Modalità Demo", "sync", self.attiva_modalita_demo)
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

def pop_categorie(self):
    m = MenuPersonalizzato(
        self, bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT,
        active_bg=self.MENU_ACT_BG_COLOR, border_color=self.COLOR_HIGHLIGHT,
        font=("Arial", 9)
    )
    self._add_m_item(m, "Analisi Categorie", "timer", self.analisi_categorie)
    self._add_m_item(m, "Gestione Categorie", "filtri", self.mostra_categorie_popup)
    self._add_m_item(m, "Editor Categorie", "documenti", self.apri_gestione_categorie)
    self._add_m_item(m, "Editor Categorie Estratti", "filtri", self.mostra_editor_memoria_categorie)
    self._mostra_popup(m, 220)

def web_info(self):
    m = MenuPersonalizzato(
        self, bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT,
        active_bg=self.MENU_ACT_BG_COLOR, border_color=self.COLOR_HIGHLIGHT,
        font=("Arial", 9)
    )
    self._add_m_item(m, "Visualizza Interfaccia Web Locale", "google", self.apri_webserver)
    self._add_m_item(m, "Gestisci Certificati SSL", "google", self.gestisci_certificati)
    self._add_m_item(m, "QRcode Connessioni Gateway Remoti", "qr_code", self.mostra_qr_popup_label)
    self._add_m_item(m, "Manuale CertBot SSL", "info", self.scarica_manuale_ssl)
    self._mostra_popup(m, 340)

def pop_info(self): 
    m = MenuPersonalizzato(
        self, bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT,
        active_bg=self.MENU_ACT_BG_COLOR, border_color=self.COLOR_HIGHLIGHT,
        font=("Arial", 9)
    )
    self._add_m_item(m, "Esporta DB Transazioni", "carica", self.export_db) 
    self._add_m_item(m, "Importa DB Transazioni", "archivia", self.import_db)
    m.add_separator() 
    self._add_m_item(m, "Reset Database", "reset", self.show_reset_dialog) 
    self._add_m_item(m, "Cancella Voci Bulk", "delete", self.apri_cancella_spese_treeview_unica)
    m.add_separator() 
    self._add_m_item(m, "Gestisci Backup e Ripristino", "archivia", self.gestisci_backup_popup)
    self._add_m_item(m, "Esegui Backup Completo Zip", "archivia", self.esegui_backup_zip)
    m.add_separator() 
    self._add_m_item(m, "Apri Manuale", "documenti", self.scarica_manuale) 
    self._mostra_popup(m, 300)

def _mostra_popup(self, menu, y_offset): 
    if self.menu_aperto == menu: return 
    if self.menu_aperto: 
        try: self.menu_aperto.unpost() 
        except Exception: pass 
    self.menu_aperto = menu 
    self._menu_opened_at = time.monotonic()
    x = self.sidebar.winfo_rootx() + self.sidebar.winfo_width() 
    y = self.sidebar.winfo_rooty() + y_offset 
    try: 
        menu.post(x, y) 
        self.unbind_all("<Button-1>")
        self.unbind_all("<FocusIn>")
        self.bind_all("<Button-1>", self._verifica_chiusura_menu, add="+")
        self.bind_all("<FocusIn>", self._verifica_chiusura_menu, add="+")
        root = self.winfo_toplevel()
        root.bind("<Escape>", self._chiudi_menu_orfano)
    except Exception as e: 
        print(f"Errore apertura menu: {e}")

def _chiudi_menu_orfano(self, event=None):
    if self.menu_aperto:
        try:
            self.menu_aperto.unpost()
        except Exception:
            pass
        self.menu_aperto = None
        self.unbind_all("<Button-1>") 
        self.unbind_all("<FocusIn>")
        root = self.winfo_toplevel()
        root.unbind("<Escape>")

def _verifica_chiusura_menu(self, event): 
    if time.monotonic() - getattr(self, '_menu_opened_at', 0) < 0.2:
        return
    if self.menu_aperto: 
        w = event.widget
        try:
            if w == self.menu_aperto or str(w).startswith(str(self.menu_aperto)):
                return
        except Exception:
            pass
        try: self.menu_aperto.unpost() 
        except Exception: pass
        self.menu_aperto = None
        self.unbind_all("<Button-1>")
        self.unbind_all("<FocusIn>")
            
def espandi_sidebar(self):
    self.sidebar.configure(width=120) 
    if hasattr(self, 'lbl_logo_testo'):
        self.lbl_logo_testo.pack(side="left", padx=(0, 6))

    if hasattr(self, 'lbl_tipo_percentuale'): 
        self.lbl_tipo_percentuale.pack_forget()
    if hasattr(self, '_search_entry'):
        self._search_entry.pack(after=self.lbl_logo_container, fill="x", padx=6, pady=(2, 4))
    if hasattr(self, '_search_results_frame'):
        self._search_results_frame.pack(after=self._search_entry, fill="x")
    if hasattr(self, '_search_var'):
        self._search_var.set("")
    self.after(100, lambda: self._search_entry.focus_set() if hasattr(self, '_search_entry') else None)
    for btn, testo in [(self.btn_oggi_stats, " Oggi"), (self.btn_giorno, " Giorno"), (self.btn_mese, " Mese"), (self.btn_anno, " Anno"), (self.btn_totali, " Totali"), (self.btn_importa_popup, "Import IA"), (self.btn_chiedi_ia_popup, "Chiedi IA")]:
        btn.configure(text="")
            
def _add_m_item(self, target, label, icon_key, command, acc=""): 
    img = self.icone_gui.get(icon_key) 
    from moduli.scorciatoie import etichetta_per_metodo
    acc = etichetta_per_metodo(getattr(command, "__name__", "")) or acc
    def wrapped(c=command):
        if self.menu_aperto:
            try: self.menu_aperto.unpost()
            except Exception: pass
            self.menu_aperto = None
            self.unbind_all("<Button-1>")
            self.unbind_all("<FocusIn>")
        c()
    target.add_command(label=f" {label}", image=img, compound="left",  
                        command=wrapped, accelerator=acc)
                        
def _filtra_sidebar(self, *_):
    import __main__ as _app
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
        ("Scansiona e salva PDF",                 self.scansiona_e_salva),
        ("Gestione Utenze",                       self.utenze),
        ("ImmoBil — Gestione Immobili",           self.immobil),
        ("AutoPark",                              self.veicoli),
        ("Pet Care",                              self.animali),
        ("StockBox",                              self.magazzino_app),
        ("Sincronizza Acquisti Email",            self.avvia_sincronizzazione),
        ("Importa Documento AI",                  self.apri_finestra_importa),
        ("Log Importazioni",                      self.mostra_log_importazioni),
        ("Rubrica",                               self.rubrica_app),
        ("Promemoria",                            self.gestisci_promemoria),
        ("GCalendar",                             self.launch_qr_svg_generator),
        ("Piano Dieta",                           self.apri_dieta),
        ("MyBusiness",                            self.apri_studio),
        ("Portafoglio Bancario",                  self.open_saldo_conto),
        ("Stampa",                                self.anteprima_e_stampa_txt),
        ("Pannello Controllo",                    self.calcola_mancanti),
        ("Calcolatrice",                          self.apri_calcolatrice),
        ("Cancella Voci Bulk",                    self.apri_cancella_spese_treeview_unica),
        ("Ricerca Globale",                       self.cerca_operazioni),
        ("Gestione Tag #",                        self.apri_gestione_tag),
        ("Confronta Periodi",                     self.open_compare_window),
        ("FairShare Dare & Avere",                self.mostra_dare_avere),
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
        ("Chiedi al Database (Gemini AI)",        self.chiedi_ia_database),
        ("Gestione Ricorrenze",                   self.mostra_ricorrenza_popup),
        ("Lista Ricorrenze",                      self.mostra_lista_ricorrenze),
        ("Scadenze Mese",                         self.scadenze_mese),
        ("Pianifica",                             self.apri_gestione_spese_pianificate),
        ("Controlla Ricorrenti",                  self.controlla_ricorrenti_manual),
        ("Analisi Categorie",                     self.analisi_categorie),
        ("Gestione Categorie",                    self.mostra_categorie_popup),
        ("Editor Categorie",                       self.apri_gestione_categorie),
        ("Editor Memoria Categorie",              lambda: self.mostra_editor_memoria_categorie()),
        ("Impostazioni App",                      self.gestisci_configurazione),
        ("Personalizza Icone",                    self.apri_personalizza_icone),
        ("Cambia Password",                       self.apri_cambio_password),
        ("Registra Prodotto",                     self.apri_registrazione),
        ("Gamification",                          self.mostra_dettaglio_gamification),
        ("Gestisci Profili Utenti",               self.mostra_selettore_profilo),
        ("Modalità Demo",                         lambda: self.esci_modalita_demo() if _app.PROFILO_ATTIVO == _app.NOME_PROFILO_DEMO else self.attiva_modalita_demo()),
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
        ("Community Pool",                        self.apri_community_pool),
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

