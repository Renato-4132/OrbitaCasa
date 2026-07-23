#!/usr/bin/env python3

# OrbitaCasa - Copyright © 2026 Renato-4132
# Tutti i diritti riservati. Vietata la riproduzione o distribuzione
# senza autorizzazione scritta dell'autore.

import os
import re
import sys
import ssl
def _crea_contesto_https_sicuro():
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
ssl._create_default_https_context = _crea_contesto_https_sicuro

if sys.platform.startswith("linux"):
    os.environ["XMODIFIERS"] = "@im=none"
    os.environ["GTK_IM_MODULE"] = "none"
    os.environ["QT_IM_MODULE"] = "none"
import json
import math
import time
import uuid
import base64
import random
import socket
import shutil
import secrets
import hashlib
import platform
import calendar
import datetime
import tempfile
import threading
import subprocess
import webbrowser
import http.client
import urllib.parse
import urllib.error  
import urllib.request
import tkinter as tk
from tkinter import ttk, filedialog

current_folder = os.path.basename(os.getcwd())   
def show_warning_popup(titolo=None, titolo_fg="#FF3333",
                        corpo=None, corpo_fg="#AAAAAA", corpo_font_size=9, corpo_expand=False,
                        riga_extra=None, riga_extra_fg="#FF6666",
                        bg="#0D0D0D", accent="#FF0000",
                        width=420, height=160, durata_ms=4000,
                        spinner=False, spinner_testo=None):
    splash = tk.Tk()
    splash.overrideredirect(True)
    splash.attributes("-topmost", True)
    x = (splash.winfo_screenwidth() // 2) - (width // 2)
    y = (splash.winfo_screenheight() // 2) - (height // 2)
    splash.geometry(f"{width}x{height}+{x}+{y}")
    splash.configure(bg=bg, highlightthickness=2, highlightbackground=accent)
    if spinner:
        gemini_colors = ["#0055FF", "#AA00FF", "#FF0055", "#00C853"]
        container = tk.Frame(splash, bg=bg)
        container.pack(expand=True)
        cvs_size = 40
        cvs = tk.Canvas(container, width=cvs_size, height=cvs_size, bg=bg, highlightthickness=0, bd=0)
        cvs.pack(side="left", padx=15)
        tk.Label(
            container,
            text=spinner_testo or "",
            font=("Arial", 12, "bold"),
            fg=accent,
            bg=bg,
            justify="left"
        ).pack(side="left")
        state = {"angle": 0, "color_step": 0}
        def animate():
            if not splash.winfo_exists():
                return
            cvs.delete("all")
            state["angle"] = (state["angle"] + 10) % 360
            state["color_step"] += 1
            c_idx = (state["color_step"] // 10) % len(gemini_colors)
            color = gemini_colors[c_idx]
            center = cvs_size // 2
            r = 12
            rad = math.radians(state["angle"])
            px = center + r * math.cos(rad)
            py = center + r * math.sin(rad)
            cvs.create_oval(center-r, center-r, center+r, center+r, outline="#333333", width=1)
            cvs.create_arc(center-r, center-r, center+r, center+r,
                           start=state["angle"]-60, extent=60,
                           outline=color, width=3, style="arc")
            cvs.create_oval(px-3, py-3, px+3, py+3, fill=color, outline=color)
            splash.after(30, animate)
        animate()
        splash.after(1000, splash.destroy)
    else:
        if titolo:
            tk.Label(splash, text=titolo, font=("Arial", 13, "bold"),
                     fg=titolo_fg, bg=bg).pack(pady=(18, 4))
        if corpo:
            tk.Label(
                splash, text=corpo,
                font=("Arial", corpo_font_size, "bold") if corpo_font_size >= 11 else ("Arial", corpo_font_size),
                fg=corpo_fg, bg=bg, justify="center", padx=10
            ).pack(pady=(0, 8) if riga_extra else (0, 10), expand=corpo_expand, fill="both" if corpo_expand else "none")
        if riga_extra:
            tk.Label(splash, text=riga_extra, font=("Arial", 9, "italic"),
                     fg=riga_extra_fg, bg=bg).pack()
        splash.after(durata_ms, splash.destroy)
    splash.mainloop()

# Nome cartella Massimo Caratteri
if len(current_folder) > 35:
    show_warning_popup(
        titolo="ATTENZIONE", titolo_fg="red",
        corpo="Nome cartella troppo lungo!\nRinomina la cartella e rilancia l'app.",
        corpo_fg="#61AFEF", corpo_font_size=11, corpo_expand=True,
        bg="#000000", accent="#61AFEF", width=380, height=120
    )
    sys.exit(1)
# Verifica la connessione internet contattando Google; mostra popup di errore e termina l'app se non raggiungibile    
def check_network_connection():      
    url_test = "https://www.google.com"
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Verifica connessione in corso...")
    try:
        with urllib.request.urlopen(url_test, timeout=3) as response:
            if response.status != 200:
                show_warning_popup(
                    titolo="ATTENZIONE", titolo_fg="red",
                    corpo="Non è presente una connessione internet.\nImpossibile installare le risorse necessarie.\nIl programma verrà chiuso.",
                    corpo_fg="#61AFEF", corpo_font_size=11, corpo_expand=True,
                    bg="#000000", accent="#61AFEF", width=380, height=120
                )
                sys.exit(1)
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Connessione internet: OK")
        return True
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore di rete: {e}")
            show_warning_popup(
                    titolo="ATTENZIONE", titolo_fg="red",
                    corpo="Non è presente una connessione internet.\nImpossibile installare le risorse necessarie.\nIl programma verrà chiuso.",
                    corpo_fg="#61AFEF", corpo_font_size=11, corpo_expand=True,
                    bg="#000000", accent="#61AFEF", width=380, height=120
                )
            sys.exit(1)
    except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore imprevisto durante il check rete: {e}")
            show_warning_popup(
                    titolo="ATTENZIONE", titolo_fg="red",
                    corpo="Non è presente una connessione internet.\nImpossibile installare le risorse necessarie.\nIl programma verrà chiuso.",
                    corpo_fg="#61AFEF", corpo_font_size=11, corpo_expand=True,
                    bg="#000000", accent="#61AFEF", width=380, height=120
                )
            sys.exit(1)

# Disabilita Sync        
DISABILITA_SYNC_MODULI_TEST = False
                    
check_network_connection()            
PATH_LOCALE = os.path.dirname(os.path.abspath(__file__))
current_folder = os.path.basename(os.getcwd())

# BOOTSTRAP
MODULI_DIR = os.path.join(PATH_LOCALE, "moduli")
_COSTANTI_PATH = os.path.join(MODULI_DIR, "costanti.py")
_MODELLO_SPESA_PATH = os.path.join(MODULI_DIR, "modello_spesa.py")

def _boot_scarica_file_singolo(nome_file, percorso_dest):
    print(f"[{time.strftime('%H:%M:%S')}] Prima esecuzione: scarico {nome_file} da GitHub...")
    try:
        os.makedirs(MODULI_DIR, exist_ok=True)
        _url = f"https://raw.githubusercontent.com/Renato-4132/OrbitaCasa/main/moduli/{nome_file}"
        _req = urllib.request.Request(_url, headers={"User-Agent": "OrbitaCasa-Bootstrap"})
        with urllib.request.urlopen(_req, timeout=20) as resp:
            _dati = resp.read()
        with open(percorso_dest, "wb") as f:
            f.write(_dati)
        print(f"[{time.strftime('%H:%M:%S')}] {nome_file} scaricato.")
    except Exception as _e:
        print(f"[{time.strftime('%H:%M:%S')}] Errore durante il download di {nome_file}: {_e}")
        show_warning_popup(
                    titolo="ATTENZIONE", titolo_fg="red",
                    corpo="Non è presente una connessione internet.\nImpossibile installare le risorse necessarie.\nIl programma verrà chiuso.",
                    corpo_fg="#61AFEF", corpo_font_size=11, corpo_expand=True,
                    bg="#000000", accent="#61AFEF", width=380, height=120
                )
        sys.exit(1)

def _boot_carica_moduli_iniziali():
    
    global carica_costanti, SpesaEntry, campo, METODI_PAGAMENTO_EMOJI, METODI_PAGAMENTO_FILTRO
    global VOCE_FILTRO_MOVIMENTI, SEPARATORE_FILTRO_MOVIMENTI, SIMBOLI_METODO, NOME_DA_EMOJI, metodo_pagamento_pulito
    if not os.path.isfile(_COSTANTI_PATH):
        _boot_scarica_file_singolo("costanti.py", _COSTANTI_PATH)
    if not os.path.isfile(_MODELLO_SPESA_PATH):
        _boot_scarica_file_singolo("modello_spesa.py", _MODELLO_SPESA_PATH)
    from moduli.costanti import carica_costanti
    from moduli.modello_spesa import (
        SpesaEntry, campo, METODI_PAGAMENTO_EMOJI, METODI_PAGAMENTO_FILTRO,
        VOCE_FILTRO_MOVIMENTI, SEPARATORE_FILTRO_MOVIMENTI,
        SIMBOLI_METODO, NOME_DA_EMOJI, metodo_pagamento_pulito,
    )
    globals().update(carica_costanti(PATH_LOCALE))

os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
current_folder = os.path.basename(os.getcwd())

class GestioneSpese(tk.Tk):
    CATEGORIA_RIMOSSA = "Categoria Rimossa"
    def __init__(self):
        super().__init__()
        # Debug_log
        self.abilita_log_tkinter()
        # Hash per LC
        self.topic_unico = _get_device_id()
        self.ip_attuale = ""
        # Id Sessione
        self.SESSION_ID = str(random.randint(1000, 9999))
        # Web Token
        self.web_token = secrets.token_hex(16)
        self.ultimo_accesso_web = time.time()
        self.timeout_sessione = 3600 #(1 ora)
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] SESSION TOKEN GENERATO: {self.web_token}")
        # Caricamento Icone
        self.setup_resources()
        
        self.CHECK_DOPPI_MOV = CHECK_DOPPI_MOV 
        
        self.salva_geometria = SALVA_GEOMETRIA_INIZIALE
        self.withdraw()
        self.update_idletasks()
        initial_width = 1366
        initial_height = 660
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self._window_geometry = None
        self.load_window_geometry()
        if self._window_geometry:
            self.geometry(self._window_geometry)
        else:
            x = (screen_width // 2) - (initial_width // 2)
            y = (screen_height // 2) - (initial_height // 2)
            self.geometry(f"{initial_width}x{initial_height}+{x}+{y}")
        
        if not self.gestione_login():
            sys.exit()
            return

        self.resizable(True, True)
        self.minsize(1366, 660)
        self.lift()
        self.focus_force()
        self.after(250, self.deiconify)

        # Carica Icona App
        self.set_app_icon()
        # Variabili Backup Completo
        self.current_folder = current_folder
        self.backup_formato = 'zip'
        # Variabile Tabella Iniziale
        self.stats_view_mode = tk.StringVar(value="tabella")
        self.stats_step = 0
        self.visualizza_tutti_gli_anni = False
        # Timer Carosello
        self.chiamato_da_carosello = True
        self.intervallo_scorrimento = 10000  # 10 secondi 
        self.id_scorrimento_automatico = None
        self.intervallo_scorrimento = CAROSELLO_INTERVALLO
        # Timer Countdown Minimizza
        self._countdown_delay = 5000 
        self._countdown_splash = None
        self._countdown_timer_id = None
        # Intervallo Lampeggio Cursore
        self.blinking_interval = 500
        # Variabili Lampeggio Widget Riepilogo Mese/Anno
        self.blinking_widgets = set()
        self._blink_phase = True
        
        if not os.path.exists(DB_DIR):
            os.makedirs(DB_DIR)
        if not os.path.exists(EXP_DB):
            os.makedirs(EXP_DB)
            
        # Backup Incrementale threading    
        self.pianifica_backup_orario()
        # Schedulatore eventi 
        self.after(60000, self._tick_scheduler)
        # Aggiorna titolo finestra  
        self.aggiorna_titolo_finestra()
        # Aggiorna data automatico 
        self._auto_refresh_mezzanotte()
        
        self.categoria_bloccata = False
        
        # Sync dati esterni
        if SYNC_DATI:
            self.after(30000, self.pianifica_sincro_web)
        # Inizializzazione variabili per il Monitor Sync
        self.operazioni_scaricate_sessione = 0 
        # Suggerimento categorie
        self.suggerimenti_attivi = SMARTCAT
        # Timeout Iconizza
        if ICONIZZA_INATTIVITA:
            self._timeout_inattivita = TIMEOUT_INATTIVITA_MS
            self._timer_inattivita = None
            self._attiva_timer_inattivita()
        # Check Movimenti mancanti fine mese    
        if CHECK_MESE:
            self._last_dismiss_date = self._carica_dismiss_fm()
            self.after(8000, self.controlla_ricorrenti_a_fine_mese)  
        
        self.categorie = ["Generica", self.CATEGORIA_RIMOSSA]
        self.categorie_tipi = {"Generica": "Uscita", self.CATEGORIA_RIMOSSA: "Uscita"}
        self.spese = {}
        self.ricorrenze = {}  
        self.modifica_idx = None
        self.stats_refdate = datetime.date.today()
        self.load_db()
        self.carica_memoria_descrizioni()
        # Valiabili iniziali Target 
        self.budget_mensile = TARGET_MESE
        self.budget_annuale = TARGET_ANNO
        self.var_budget_cat = tk.StringVar(value="")
        self.save_lock = threading.Lock()
       
        # Themi
        self.applica_temi(THEMA)
                       
        # Menu Principale
        self.setup_sidebar()
        # Menu Copia Incolla
        if CONTEXT_MENU:
            self.configura_menu_contestuale_globale()
        # Main
        main_frame = ttk.Frame(self, style="BlackFrame.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        cal_frame = ttk.Frame(main_frame, style="BlackFrame.TFrame")
        cal_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        today = datetime.date.today()
        
        self.cal = Calendar(
            cal_frame,
            selectmode="day",
            year=today.year,
            month=today.month,
            day=today.day,
            locale="it_IT",
            date_pattern="dd-mm-yyyy",
            font=("Arial", 10),
            cursor="hand2",
            background=self.cal_header_bg,
            foreground=self.cal_header_fg,
            headersbackground=self.cal_header_bg,
            headersforeground=self.cal_header_fg,
            normalbackground=self.cal_bg,
            normalforeground=self.cal_fg,
            weekendbackground=self.cal_weekend_bg,
            weekendforeground=self.cal_weekend_fg,
            selectbackground=self.cal_select_bg,
            selectforeground=self.cal_select_fg,
            bordercolor=self.cal_bg,            
            showothermonthdays=False
        )
        self.cal.pack(fill="both", expand=False)
        self.cal.configure(borderwidth=0)
        try:
            prefisso = self.cal._style_prefixe
            style = ttk.Style()
            colore_hover = self.COLOR_RED
            for s in [f"L.{prefisso}.TButton", f"R.{prefisso}.TButton"]:
                style.configure(s, arrowcolor=self.cal_weekend_fg, background=self.cal_header_bg, borderwidth=0, relief="flat", focuscolor=self.cal_header_bg)
                style.map(s,
                    arrowcolor=[("active", colore_hover), ("pressed", self.cal_weekend_fg)],
                    background=[("active", self.cal_header_bg), ("pressed", self.cal_header_bg)],
                    relief=[("active", "flat"), ("pressed", "flat")]
                )
        except:
            pass
        # Creazione del tooltip Calendario
        self.tooltip_win = tk.Toplevel(self)
        self.tooltip_win.withdraw()
        self.tooltip_win.overrideredirect(True)
        self.tooltip_win.attributes("-topmost", True)
        self.tooltip_win.config(
                highlightthickness=1, 
                highlightbackground=self.COLOR_HIGHLIGHT,
                bg=self.COLOR_TOOLTIP
        )
        self.tooltip_timer = None
        # Collega il calendario ai movimenti del mouse
        if CAL_TOOLTIPS:
            self.applica_ricorsivo_tooltip(self.cal)
        # Disattiva Tooltip tkcalendar
        self.cal.configure(tooltipdelay=999999)
        
        def _mostra_tooltip_legenda(widget, testo):
            def entra(e):
                x = widget.winfo_rootx()
                y = widget.winfo_rooty() + widget.winfo_height() + 4
                tip = tk.Toplevel(widget)
                tip.overrideredirect(True)
                tip.attributes("-topmost", True)
                tip.wm_geometry(f"+{x}+{y}")
                tip.config(
                    highlightthickness=1,
                    highlightbackground=self.COLOR_HIGHLIGHT,
                    bg=self.COLOR_TOOLTIP
                )
                tk.Label(tip, text=testo, background=self.COLOR_TOOLTIP,
                         foreground=self.TEXT_COLOR, font=("Arial", 8),
                         padx=4, pady=2).pack()
                widget._tooltip = tip
            def esce(e):
                if hasattr(widget, "_tooltip"):
                    widget._tooltip.destroy()
                    del widget._tooltip
            widget.bind("<Enter>", entra)
            widget.bind("<Leave>", esce)
        legenda = ttk.Frame(cal_frame, style="BlackFrame.TFrame")
        legenda.pack(side=tk.TOP, anchor="w")
        self.btn_oggi = tk.Label(
            legenda, 
            text=" Oggi", 
            image=self.icone_gui.get("filtri"),
            compound="left",
            cursor="hand2",
            font=("Arial", 9, "bold"),
            foreground="#D4A017",
            background=self.COLOR_WIDGET_BG
        )
        self.btn_oggi.image = self.icone_gui.get("reset")
        self.btn_oggi.pack(side="left", padx=3)
        self.btn_oggi.bind("<Button-1>", lambda e: self.after(10, self.goto_today))
        self.after(500, self._avvia_rotazione_oggi)
        _mostra_tooltip_legenda(self.btn_oggi, "Torna al giorno di oggi")

        lbl_entrata = ttk.Label(legenda, text="Entrata", background=self.COLOR_WIDGET_BG, foreground="lightgreen", width=7, anchor="center", font=("Arial", 10, "bold"))
        lbl_entrata.pack(side="left", padx=3)
        _mostra_tooltip_legenda(lbl_entrata, "Giorno con almeno un'entrata")

        lbl_uscita = ttk.Label(legenda, text="Uscita", background=self.COLOR_WIDGET_BG, foreground="lightcoral", width=6, anchor="center", font=("Arial", 10, "bold"))
        lbl_uscita.pack(side="left", padx=3)
        _mostra_tooltip_legenda(lbl_uscita, "Giorno con almeno un'uscita")

        lbl_misto = ttk.Label(legenda, text="Entrata+Uscita", background=self.COLOR_WIDGET_BG, foreground="khaki", width=14, anchor="center", font=("Arial", 10, "bold"))
        lbl_misto.pack(side="left", padx=3)
        _mostra_tooltip_legenda(lbl_misto, "Giorno con entrate e uscite")

        lbl_weekend = ttk.Label(legenda, text="Weekend", background=self.cal_weekend_bg, foreground=self.cal_weekend_fg, font=("Arial", 10, "bold"), width=9, anchor="center")
        lbl_weekend.pack(side="left", padx=3)
        _mostra_tooltip_legenda(lbl_weekend, "Sabato e Domenica")

        lbl_sel = ttk.Label(legenda, text="Selezionato", background=self.COLOR_WIDGET_BG, foreground="dodgerblue", font=("Arial", 10, "bold"), width=12, anchor="center")
        lbl_sel.pack(side="left", padx=3)
        _mostra_tooltip_legenda(lbl_sel, "Giorno selezionato")

        legenda2 = ttk.Frame(cal_frame, style="BlackFrame.TFrame")
        legenda2.pack(side=tk.TOP, anchor="w")
        img_mouse2 = self.icone_gui.get("mouse")
        ttk.Label(legenda2,
           text="  2×→Aggiunta rapida  |  1×→Vai al giorno  |  Dx→HUD  |  Hover→Tooltip",
           image=img_mouse2,
           compound="left",
           background=self.COLOR_WIDGET_BG,
           foreground="gray",
           font=("Arial", 7, "italic")).pack(side="left", padx=3)

        oggi = datetime.date.today()
        self.cal.calevent_create(oggi, "Oggi", "today")
        self.cal.tag_config("today", background="gold", foreground="black")

        try:
           self.cal._header_month.config(font=("Arial", 14, "bold"))
           self.cal._header_year.config(font=("Arial", 14, "bold"))
        except:
           pass

        self.cal.tag_config("verde", background=self.COLOR_LIGHTGREEN, foreground=self.COLOR_BLACK)
        self.cal.tag_config("rosso", background=self.COLOR_LIGHTCORAL, foreground=self.COLOR_BLACK)
        self.cal.tag_config("misto", background=self.COLOR_KHAKI, foreground=self.COLOR_BLACK)
        self.cal.tag_config("today", background=self.COLOR_YELLOW, foreground=self.COLOR_BLACK)

        self.cal.bind("<<CalendarSelected>>", self.on_calendar_change)
        self.cal.bind("<<CalendarMonthChanged>>", self.on_month_changed)
        def applica_bind_ricorsivo(widget):
           widget.bind("<Button-3>", self.quick_add)
           widget.bind("<Double-1>", self.apri_inserimento_rapido)
           for child in widget.winfo_children():
               applica_bind_ricorsivo(child)
        applica_bind_ricorsivo(self.cal)
        
        self.colora_giorni_spese()
        
        self.estratto_month_var = tk.StringVar(value=f"{today.month:02d}")
        self.estratto_year_var = tk.StringVar(value=str(today.year))

        current_year = today.year
        self.years = [str(y) for y in range(current_year - 15, current_year + 11)]
        self.months = [
            "01 - Gennaio", "02 - Febbraio", "03 - Marzo", "04 - Aprile", "05 - Maggio", "06 - Giugno",
            "07 - Luglio", "08 - Agosto", "09 - Settembre", "10 - Ottobre", "11 - Novembre", "12 - Dicembre"
        ]
        riepilogo_frame = ttk.Frame(cal_frame)
        riepilogo_frame.pack(fill=tk.X, padx=2, pady=(2, 2))
        icona_sole = self.icone_gui.get("meteo_sole")
        lbl_mese_container = tk.Frame(riepilogo_frame, bg=self.COLOR_WIDGET_BG, width=195, height=22)
        lbl_mese_container.pack_propagate(False)
        self.lbl_titolo_mese = tk.Label(
                lbl_mese_container,
                text=" Riepilogo Mese Attuale",
                image=icona_sole,
                compound="left",
                font=("Arial", 10, "bold"),
                bg=self.COLOR_WIDGET_BG,
                fg="red"
        )
        self.lbl_titolo_mese.image = icona_sole
        self.lbl_titolo_mese.pack(side="left")
        self.totalizzatore_mese_frame = ttk.LabelFrame(
                riepilogo_frame,
                labelwidget=lbl_mese_container,
                style="RedBold.TLabelframe"
        )
        self.totalizzatore_mese_frame.pack(side="left", fill="both", expand=True, padx=(0, 4)) 
        self.totalizzatore_mese_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(self.totalizzatore_mese_frame, text="Totale Entrate mese:", foreground="green", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", padx=(6,0), pady=(2, 0))
        self.totalizzatore_mese_entrate_label = ttk.Label(self.totalizzatore_mese_frame, text="0.00 €", foreground="green", font=("Arial", 10, "bold"))
        self.totalizzatore_mese_entrate_label.grid(row=0, column=1, sticky="e", padx=(0,6), pady=(2, 0))
        ttk.Label(self.totalizzatore_mese_frame, text="Totale Uscite mese:", foreground="red", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", padx=(6,0), pady=(2, 0))
        self.totalizzatore_mese_uscite_label = ttk.Label(self.totalizzatore_mese_frame, text="0.00 €", foreground="red", font=("Arial", 10, "bold"))
        self.totalizzatore_mese_uscite_label.grid(row=1, column=1, sticky="e", padx=(0,6), pady=(2, 0))
        ttk.Label(self.totalizzatore_mese_frame, text="Differenza mese:", foreground="dodgerblue", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", padx=(6,0), pady=(2, 4))
        self.totalizzatore_mese_diff_label = ttk.Label(self.totalizzatore_mese_frame, text="0.00 €", foreground="dodgerblue", font=("Arial", 10, "bold"))
        self.totalizzatore_mese_diff_label.grid(row=2, column=1, sticky="e", padx=(0,6), pady=(2, 4))
        lbl_anno_container = tk.Frame(riepilogo_frame, bg=self.COLOR_WIDGET_BG, width=195, height=22)
        lbl_anno_container.pack_propagate(False)
        self.lbl_titolo_anno = tk.Label(
                lbl_anno_container,
                text=" Riepilogo Anno Attuale",
                image=icona_sole,
                compound="left",
                font=("Arial", 10, "bold"),
                bg=self.COLOR_WIDGET_BG,
                fg="red"
        )
        self.lbl_titolo_anno.image = icona_sole
        self.lbl_titolo_anno.pack(side="left")
        self.totalizzatore_frame = ttk.LabelFrame(
                riepilogo_frame,
                labelwidget=lbl_anno_container,
                style="RedBold.TLabelframe"
        )
        self.totalizzatore_frame.pack(side="left", fill="both", expand=True, padx=(4, 0))
        self.totalizzatore_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(self.totalizzatore_frame, text="Totale Entrate:", foreground="green", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", padx=(6,0), pady=(2, 0))
        self.totalizzatore_entrate_label = ttk.Label(self.totalizzatore_frame, text="0.00 €", foreground="green", font=("Arial", 10, "bold"))
        self.totalizzatore_entrate_label.grid(row=0, column=1, sticky="e", padx=(0,6), pady=(2, 0))
        ttk.Label(self.totalizzatore_frame, text="Totale Uscite:", foreground="red", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", padx=(6,0), pady=(2, 0))
        self.totalizzatore_uscite_label = ttk.Label(self.totalizzatore_frame, text="0.00 €", foreground="red", font=("Arial", 10, "bold"))
        self.totalizzatore_uscite_label.grid(row=1, column=1, sticky="e", padx=(0,6), pady=(2, 0))
        ttk.Label(self.totalizzatore_frame, text="Differenza:", foreground="dodgerblue", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", padx=(6,0), pady=(2, 4))
        self.totalizzatore_diff_label = ttk.Label(self.totalizzatore_frame, text="0.00 €", foreground="dodgerblue", font=("Arial", 10, "bold"))
        self.totalizzatore_diff_label.grid(row=2, column=1, sticky="e", padx=(0,6), pady=(2, 4))
        self.lbl_titolo_target_m = ttk.Label(
                self.totalizzatore_mese_frame, 
                text="Target Mese:", 
                font=("Arial", 10, "bold"), 
                foreground=self.COLOR_HEADER
        )
        self.lbl_titolo_target_m.grid(row=3, column=0, sticky="w", padx=(6,0), pady=(2, 2))
        self.lbl_budget_mese = ttk.Label(
                self.totalizzatore_mese_frame, 
                text="0.00 €", 
                font=("Arial", 10, "bold")
        )
        self.lbl_budget_mese.grid(row=3, column=1, sticky="e", padx=(0,6), pady=(2, 2))
        self.lbl_titolo_target_a = ttk.Label(
                self.totalizzatore_frame, 
                text="Target Anno:", 
                font=("Arial", 10, "bold"), 
                foreground=self.COLOR_HEADER
        )
        self.lbl_titolo_target_a.grid(row=3, column=0, sticky="w", padx=(6,0), pady=(2, 2))
        self.lbl_budget_anno = ttk.Label(
                self.totalizzatore_frame, 
                text="0.00 €", 
                font=("Arial", 10, "bold")
        )
        self.lbl_budget_anno.grid(row=3, column=1, sticky="e", padx=(0,6), pady=(2, 2))
        self.lbl_titolo_analisi = tk.Label(
                cal_frame,
                text=" Analisi Mese Attuale",
                image=self.icone_gui.get("meteo_sole"),
                compound="left",
                font=("Arial", 10, "bold"),
                bg=self.COLOR_WIDGET_BG,
                fg="red"
        )
        self.lbl_titolo_analisi.image = self.icone_gui.get("meteo_sole")
        lbl_analisi_frame = tk.Frame(cal_frame, bg=self.COLOR_WIDGET_BG, width=460, height=22)
        lbl_analisi_frame.pack_propagate(False)
        self.lbl_titolo_analisi = tk.Label(
                lbl_analisi_frame,
                text=" Analisi Mese Attuale",
                image=self.icone_gui.get("meteo_sole"),
                compound="left",
                font=("Arial", 10, "bold"),
                bg=self.COLOR_WIDGET_BG,
                fg="red"
        )
        self.lbl_titolo_analisi.image = self.icone_gui.get("meteo_sole")
        self.lbl_titolo_analisi.pack(side="left")
        tk.Frame(lbl_analisi_frame, bg="gray", height=1, width=1).pack(side="left", padx=4, pady=6)
        img_mouse = self.icone_gui.get("mouse")
        hint_label = ttk.Label(
                lbl_analisi_frame,
                text=" Doppio clic → Dashboard  |  Clic destro → Copia nel form",
                image=img_mouse,
                compound="right",
                foreground="gray",
                font=("Arial", 7, "italic"),
                background=self.COLOR_WIDGET_BG
        )
        if img_mouse:
                hint_label.image = img_mouse
        hint_label.pack(side="left", padx=4)
        self._hint_label_analisi = hint_label
        self._cruscotto_attivo = False
        self.btn_ciclo_cruscotto = tk.Label(
            lbl_analisi_frame, text="▼",
            font=("Arial", 9, "bold"), bg=self.COLOR_WIDGET_BG,
            fg=self.COLOR_RED, cursor="hand2"
        )
        self.btn_ciclo_cruscotto.pack(side="right", padx=4)
        self.btn_ciclo_cruscotto.bind("<Button-1>", lambda e: self._cicla_cruscotto())
        self.spese_mese_frame = ttk.LabelFrame(
                cal_frame,
                labelwidget=lbl_analisi_frame,
                style="RedBold.TLabelframe"
        )
        self.spese_mese_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=(0, 4))

        self.mese_notebook = ttk.Notebook(self.spese_mese_frame)
        self.mese_notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.cruscotto_canvas = tk.Canvas(
            self.spese_mese_frame,
            bg=self.COLOR_WIDGET_BG,
            highlightthickness=0
        )
        self.conti_canvas = tk.Canvas(
            self.spese_mese_frame,
            bg=self.COLOR_WIDGET_BG,
            highlightthickness=0
        )
        self._cruscotto_stato = 0
        def aggiorna_hint(e):
            tab = self.mese_notebook.index(self.mese_notebook.select())
            if tab == 0:
                hint_label.config(text=" Doppio clic → Dashboard | Clic destro → Copia nel form")
            elif tab == 1:
                hint_label.config(text=" Doppio clic → Dettaglio | Clic destro → Storico categoria")
            elif tab == 2:
                hint_label.config(text=" Doppio clic → Dettaglio giorno")
            elif tab == 3:
                hint_label.config(text=" Doppio clic → Dettaglio | Clic destro → Copia nel form")
            elif tab == 4:
                hint_label.config(text=" Doppio clic → Dettaglio | Clic destro → Estratti Metodo")
            elif tab == 5:
                hint_label.config(text=" Doppio clic → Dettaglio | Clic destro → Portafoglio Banca")
            elif tab == 6:
                hint_label.config(text=" Doppio clic → Dettaglio | Clic destro → Copia nel form")
        self.mese_notebook.bind("<<NotebookTabChanged>>", aggiorna_hint)
        tab_movimenti = ttk.Frame(self.mese_notebook)
        self.mese_notebook.add(tab_movimenti, text="Movimenti")
        vsb = ttk.Scrollbar(tab_movimenti, orient="vertical", style="Vertical.TScrollbar")
        self.spese_mese_tree = ttk.Treeview(
            tab_movimenti,
            columns=("Data", "Categoria", "Descrizione", "Importo", "Tipo"),
            show="headings",
            height=30,
            yscrollcommand=vsb.set
        )
        vsb.config(command=self.spese_mese_tree.yview)
        vsb.pack(side="right", fill="y")
        self.spese_mese_tree.pack(side="left", fill=tk.BOTH, expand=True)
        self.spese_mese_tree.bind("<Double-1>", self.on_spese_mese_tree_double_click)
        def on_spese_mese_tree_right_click(event):
            item = self.spese_mese_tree.identify_row(event.y)
            if not item:
                return
            self.spese_mese_tree.selection_set(item)
            entry = getattr(self.spese_mese_tree, '_entry_lookup', {}).get(item)
            if entry is None:
                return
            categoria   = campo(entry, "categoria", "").strip()
            descrizione = campo(entry, "descrizione", "").strip()
            importo     = campo(entry, "importo", 0.0)
            tipo        = campo(entry, "tipo", "").strip()
            metodo      = campo(entry, "metodo_pagamento", "")
            conto       = campo(entry, "conto", "")
            hashtag     = campo(entry, "hashtag", [])
            cat_match = next(
                (c for c in self.categorie if c.strip().lower() == categoria.lower()),
                None
            )
            if cat_match:
                self.cat_sel.set(cat_match)
                self.cat_menu.set(cat_match)
                self.on_categoria_changed(manuale=False)
            try:
                self.imp_entry.delete(0, tk.END)
                self.imp_entry.insert(0, f"{float(importo):.2f}")
            except (ValueError, TypeError):
                pass
            self.desc_entry.delete(0, tk.END)
            if "RIC·" not in descrizione:
                desc_pulita = descrizione.replace("ALL·", "").strip()
                self.desc_entry.insert(0, desc_pulita[:30])
            if self.tipo_spesa_var.get() != tipo:
                self.toggle_tipo_spesa()
            if hasattr(self, 'metodo_pagamento_var'):
                self.metodo_pagamento_var.set(self._metodo_pagamento_a_combo(metodo))
            if hasattr(self, 'v_conto_movimento'):
                self.v_conto_movimento.set(conto or "(nessuno)")
            if hasattr(self, 'tag_entry'):
                self.tag_entry.delete(0, tk.END)
                self.tag_entry.insert(0, " ".join(hashtag))
            self.show_toast("Movimento copiato nel form")
        self.spese_mese_tree.bind("<Button-3>", on_spese_mese_tree_right_click)
        self.spese_mese_tree.heading("Data",        text="Data")
        self.spese_mese_tree.heading("Categoria",   text="Categoria")
        self.spese_mese_tree.heading("Descrizione", text="Descrizione")
        self.spese_mese_tree.heading("Importo",     text="Importo")
        self.spese_mese_tree.heading("Tipo",        text="Tipo")
        self.spese_mese_tree.column("Data",        width=80,  anchor="center")
        self.spese_mese_tree.column("Categoria",   width=125, anchor="center")
        self.spese_mese_tree.column("Descrizione", width=105, anchor="center")
        self.spese_mese_tree.column("Importo",     width=80,  anchor="e")
        self.spese_mese_tree.column("Tipo",        width=50,  anchor="center")
        self.spese_mese_tree.tag_configure('entrata', foreground='green')
        self.spese_mese_tree.tag_configure('uscita',  foreground='red')
        self.spese_mese_tree.tag_configure("futuro", foreground="#E5C07B", font=("Arial", 9, "italic"))
        for col in self.spese_mese_tree["columns"]:
            self.spese_mese_tree.heading(col, command=lambda _col=col: self.treeview_sort_column(self.spese_mese_tree, _col, False))
            self._bind_tooltip_metodo(self.spese_mese_tree)
        tab_categorie = ttk.Frame(self.mese_notebook)
        self.mese_notebook.add(tab_categorie, text="Categorie")
        frm_top_cat = ttk.Frame(tab_categorie)
        frm_top_cat.pack(fill=tk.BOTH, expand=True)
        sb_top_cat = ttk.Scrollbar(frm_top_cat, orient="vertical")
        sb_top_cat.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas_top_cat = tk.Canvas(frm_top_cat, bg=self.COLOR_WIDGET_BG, highlightthickness=0, yscrollcommand=sb_top_cat.set)
        self.canvas_top_cat.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_top_cat.config(command=self.canvas_top_cat.yview)
        self.canvas_top_cat.bind("<Configure>", lambda e: self.draw_top_categorie())
        self.after(100, self.draw_heatmap_mese)
        tab_spark = ttk.Frame(self.mese_notebook)
        self.mese_notebook.add(tab_spark, text="Sparkline")
        self.canvas_spark = tk.Canvas(tab_spark, bg=self.COLOR_WIDGET_BG, highlightthickness=0)
        self.canvas_spark.pack(fill=tk.BOTH, expand=True)
        self.canvas_spark.bind("<Configure>", lambda e: self.draw_spark_mese())
        self.after(100, self.draw_heatmap_mese)
        tab_heatmap = ttk.Frame(self.mese_notebook)
        self.mese_notebook.add(tab_heatmap, text="Heatmap")
        self.canvas_heatmap = tk.Canvas(tab_heatmap, bg=self.COLOR_WIDGET_BG, highlightthickness=0)
        self.canvas_heatmap.pack(fill=tk.BOTH, expand=True)
        self.canvas_heatmap.bind("<Configure>", lambda e: self.draw_heatmap_mese())
        tab_metodo = ttk.Frame(self.mese_notebook)
        self.mese_notebook.add(tab_metodo, text="Metodo")
        frm_estr_metodo = ttk.Frame(tab_metodo)
        frm_estr_metodo.pack(fill=tk.BOTH, expand=True)
        sb_estr_metodo = ttk.Scrollbar(frm_estr_metodo, orient="vertical")
        sb_estr_metodo.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas_estratto_metodo = tk.Canvas(frm_estr_metodo, bg=self.COLOR_WIDGET_BG, highlightthickness=0, yscrollcommand=sb_estr_metodo.set)
        self.canvas_estratto_metodo.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_estr_metodo.config(command=self.canvas_estratto_metodo.yview)
        self.canvas_estratto_metodo.bind("<Configure>", lambda e: self.draw_estratto_metodo())
        tab_conto = ttk.Frame(self.mese_notebook)
        self.mese_notebook.add(tab_conto, text="Conto")
        frm_estr_conto = ttk.Frame(tab_conto)
        frm_estr_conto.pack(fill=tk.BOTH, expand=True)
        sb_estr_conto = ttk.Scrollbar(frm_estr_conto, orient="vertical")
        sb_estr_conto.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas_estratto_conto = tk.Canvas(frm_estr_conto, bg=self.COLOR_WIDGET_BG, highlightthickness=0, yscrollcommand=sb_estr_conto.set)
        self.canvas_estratto_conto.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_estr_conto.config(command=self.canvas_estratto_conto.yview)
        self.canvas_estratto_conto.bind("<Configure>", lambda e: self.draw_estratto_conto())
        tab_ricorrenti = ttk.Frame(self.mese_notebook)
        self.mese_notebook.add(tab_ricorrenti, text="Checkout")
        frm_ricorrenti = ttk.Frame(tab_ricorrenti)
        frm_ricorrenti.pack(fill=tk.BOTH, expand=True)
        sb_ricorrenti = ttk.Scrollbar(frm_ricorrenti, orient="vertical")
        sb_ricorrenti.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_ricorrenti = ttk.Treeview(
            frm_ricorrenti, 
            columns=("Categoria", "Ultima", "Frequenza"), 
            show="headings", 
            height=15
        )
        def on_ricorrenti_right_click(event):
            item = self.tree_ricorrenti.identify_row(event.y)
            if not item: return
            self.tree_ricorrenti.selection_set(item)
            valori = self.tree_ricorrenti.item(item, "values")
            if not valori: return
            categoria = str(valori[0]).strip()
            importo_str = str(valori[1]).replace("€", "").replace(",", ".").strip()
            cat_match = next((c for c in self.categorie if c.strip().lower() == categoria.lower()), None)
            if cat_match:
                self.cat_sel.set(cat_match)
                if hasattr(self, 'cat_menu'): self.cat_menu.set(cat_match)
                self.on_categoria_changed(manuale=False)
            try:
                self.imp_entry.delete(0, tk.END)
                self.imp_entry.insert(0, f"{float(importo_str):.2f}")
            except ValueError: pass
            self.desc_entry.delete(0, tk.END)
        columns_info = {"Categoria": "Spese da riconfermare", "Ultima": "Ultima (€)", "Frequenza": "Frequenza"}
        for col in self.tree_ricorrenti["columns"]:
            self.tree_ricorrenti.heading(
                col, 
                text=columns_info[col],
                command=lambda _col=col: self.treeview_sort_column(self.tree_ricorrenti, _col, False)
            )
        self.tree_ricorrenti.column("Categoria", width=150)
        self.tree_ricorrenti.column("Ultima", width=80, anchor="e")
        self.tree_ricorrenti.column("Frequenza", width=100, anchor="center")
        self.tree_ricorrenti.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_ricorrenti.config(command=self.tree_ricorrenti.yview)
        self.tree_ricorrenti.configure(yscrollcommand=sb_ricorrenti.set)
        self.tree_ricorrenti.bind("<Double-1>", lambda e: self.calcola_mancanti())
        self.tree_ricorrenti.bind("<Button-3>", on_ricorrenti_right_click)
        self.aggiorna_vista_ricorrenti()
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        _lbl_frame_avanzato = tk.Frame(right_frame, bg=self.COLOR_WIDGET_BG)
        self.lbl_titolo_avanzato = tk.Label(
                _lbl_frame_avanzato,
                text=" Riepilogo Avanzato",
                image=self.icone_gui.get("meteo_sole"),
                compound="left",
                font=("Arial", 10, "bold"),
                bg=self.COLOR_WIDGET_BG,
                fg="darkgreen"
        )
        self.lbl_titolo_avanzato.image = self.icone_gui.get("meteo_sole")
        self.lbl_titolo_avanzato.pack(side=tk.LEFT)
        self.lbl_mov_count = tk.Label(
                _lbl_frame_avanzato,
                text="",
                font=("Arial", 8),
                bg=self.COLOR_WIDGET_BG,
                fg=self.COLOR_TEXT
        )
        self.lbl_mov_count.pack(side=tk.LEFT, padx=(6, 0))
        frame_licence = tk.Frame(_lbl_frame_avanzato, bg=self.COLOR_WIDGET_BG)
        frame_licence.pack(side=tk.RIGHT, padx=(0, 6))
        self.lbl_topic = ttk.Label(
                frame_licence,
                image=self.icone_gui.get("api_key"),
                text=f"  Licence: {self.topic_unico}",
                compound="left",
                font=("Arial", 8, "italic"),
                cursor="hand2",
                foreground="#61AFEF",
                background=self.COLOR_WIDGET_BG
        )
        self.lbl_topic.image = self.icone_gui.get("api_key")
        self.lbl_topic.pack(side=tk.LEFT)
        self.lbl_topic.bind("<Button-1>", lambda e: self.apri_pannello_topic(self.topic_unico))
        self.btn_aggiorna_lib = tk.Label(
                frame_licence,
                image=self.icone_gui.get("carica"),
                text="🔄" if not self.icone_gui.get("carica") else "",
                compound="left",
                font=("Arial", 8, "italic"),
                cursor="hand2",
                bg=self.COLOR_WIDGET_BG,
                fg="#E65100"
        )
        self.btn_aggiorna_lib.image = self.icone_gui.get("carica")
        self.btn_aggiorna_lib.bind("<Button-1>", lambda e: self.aggiorna_librerie_pip())
        tk.Frame(_lbl_frame_avanzato, height=1, bg="gray50").pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=2)
        self.lbl_server_start = tk.Label(
                _lbl_frame_avanzato,
                image=self.icone_gui.get("timer"),
                text=f"  Avviato: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}",
                compound="left",
                font=("Arial", 8, "italic"),
                bg=self.COLOR_WIDGET_BG,
                fg=self.TEXT_COLOR
        )
        self.lbl_server_start.pack(side=tk.RIGHT)
        tk.Frame(_lbl_frame_avanzato, height=1, bg="gray50").pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=2)
        self.lbl_orologio = tk.Label(
                _lbl_frame_avanzato,
                text="",
                font=("Arial", 8, "italic"),
                bg=self.COLOR_WIDGET_BG,
                fg=self.TEXT_COLOR
        )
        self.lbl_orologio.pack(side=tk.RIGHT)
        tk.Frame(_lbl_frame_avanzato, height=1, bg="gray50").pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=2)
        stat_frame = ttk.LabelFrame(
                right_frame,
                labelwidget=_lbl_frame_avanzato,
                style="RedBold.TLabelframe"
        )
        stat_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=(0, 8))
        stat_frame.rowconfigure(3, weight=1) 
        stat_frame.columnconfigure(0, weight=1)
        self.stats_frame_ref = stat_frame 
        self.bind("<Escape>", lambda e: self._esc_torna_treeview())
        self.stats_mode = tk.StringVar(value="giorno")        
        mode_frame = ttk.Frame(stat_frame)
        mode_frame.grid(row=0, column=0, sticky="ew", padx=6, pady=(4, 0))
        mode_frame.pack_propagate(False)
        mode_frame.configure(height=24)        
        self.STATO_CORRENTE = 0
        self.STATI_VISTA = ["tabella", "grafico", "grafico_mensile", "grafico_saldo", "proiezione_fondo"]
        self.ICONE_STATI = ["banca_B", "saldo_B", "documenti_B", "report_B", "sparkles_B"] 
        idx_next = (self.STATO_CORRENTE + 1) % len(self.STATI_VISTA)        
        img_obj = self.icone_gui.get(self.ICONE_STATI[idx_next])
        self.btn_ciclico = ttk.Label(
            mode_frame, 
            image=img_obj,
            cursor="hand2",
            background=self.COLOR_WIDGET_BG
        )        
        self.btn_ciclico.image = img_obj 
        self.btn_ciclico.pack(side=tk.LEFT, padx=(5, 2))        
        self.btn_ciclico.bind("<Button-1>", lambda e: self.after(50, self.cicla_visualizzazione_statistiche))
        self.bind("<Right>", lambda e: self._cicla_se_nel_frame(self.cicla_visualizzazione_statistiche))
        self.bind("<Left>", lambda e: self._cicla_se_nel_frame(self.cicla_indietro))
        self.btn_analisi = ttk.Label(
            mode_frame, 
            image=self.icone_gui.get("report_B"),
            cursor="hand2", 
            background=self.COLOR_WIDGET_BG
        )
        self.btn_analisi.pack(side=tk.LEFT, padx=5)
        self.btn_analisi.bind("<Button-1>", lambda e: self.mostra_analisi_grafici())
        self.btn_help = ttk.Label(
            mode_frame, 
            image=self.icone_gui.get("occhio_B"),
            cursor="hand2",
            background=self.COLOR_WIDGET_BG
        )
        self.btn_help.pack(side=tk.LEFT, padx=(5, 2))
        self.btn_help.bind("<Button-1>", lambda e: self.mostra_piramide())
        self.btn_oggi_stats = ttk.Label(
            mode_frame, text=" Oggi", image=self.icone_gui.get("filtri"),
            compound="left", cursor="hand2", font=("Arial", 9, "bold"),
            background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR
        )
        self.btn_oggi_stats.pack(side=tk.LEFT, padx=(0, 0))
        self.btn_oggi_stats.bind("<Button-1>", lambda e: self.after(10, self.goto_today))
        self.btn_giorno = ttk.Label(
            mode_frame, text=" Giorno", image=self.icone_gui.get("timer_B"),
            compound="left", cursor="hand2", font=("Arial", 9, "bold"),
            background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR
        )
        self.btn_giorno.pack(side=tk.LEFT, padx=5)
        self.btn_giorno.bind("<Button-1>", lambda e: self.goto_dettaglio_mese())
        self.btn_mese = ttk.Label(
            mode_frame, text=" Mese", image=self.icone_gui.get("scadenze_B"),
            compound="left", cursor="hand2", font=("Arial", 9, "bold"),
            background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR
        )
        self.btn_mese.pack(side=tk.LEFT, padx=5)
        self.btn_mese.bind("<Button-1>", lambda e: self.set_stats_mode("mese"))
        self.btn_anno = ttk.Label(
            mode_frame, text=" Anno", image=self.icone_gui.get("report_B"),
            compound="left", cursor="hand2", font=("Arial", 9, "bold"),
            background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR
        )
        self.btn_anno.pack(side=tk.LEFT, padx=5)
        self.btn_anno.bind("<Button-1>", lambda e: self.set_stats_mode("anno"))
        self.btn_totali = ttk.Label(
            mode_frame, text=" Totali", image=self.icone_gui.get("saldo_B"),
            compound="left", cursor="hand2", font=("Arial", 9, "bold"),
            background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR
        )
        self.btn_totali.pack(side=tk.LEFT, padx=5)
        self.btn_totali.bind("<Button-1>", lambda e: self.set_stats_mode("totali"))
        def add_tt(w, txt):
            get_txt = txt if callable(txt) else (lambda: txt)
            def _show(e):
                def _create():
                    self.hide_tooltip()
                    self.tooltip_window = tk.Toplevel(self)
                    self.tooltip_window.withdraw()
                    self.tooltip_window.wm_overrideredirect(True)
                    label = ttk.Label(self.tooltip_window, text=get_txt(), style="Tooltip.TLabel")
                    label.pack()
                    self.tooltip_window.update_idletasks()
                    tw, th = self.tooltip_window.winfo_reqwidth(), self.tooltip_window.winfo_reqheight()
                    wx, wy = w.winfo_rootx(), w.winfo_rooty()
                    ww, wh = w.winfo_width(), w.winfo_height()
                    swx, swy = self.winfo_rootx(), self.winfo_rooty()
                    sww, swh = self.winfo_width(), self.winfo_height()
                    tw, th = self.tooltip_window.winfo_reqwidth(), self.tooltip_window.winfo_reqheight()
                    x = wx + (ww // 2) - (tw // 2)
                    y = wy - th - 15 
                    if x < swx: 
                        x = swx + 5
                    elif x + tw > swx + sww: 
                        x = swx + sww - tw - 5
                    if y < swy:
                        y = wy + wh + 5
                    elif y + th > swy + swh:
                        y = swy + swh - th - 5
                    self.tooltip_window.wm_geometry(f"+{int(x)}+{int(y)}")
                    self.tooltip_window.wm_geometry(f"+{int(x)}+{int(y)}")
                    self.tooltip_window.deiconify()
                    self.tooltip_window.attributes("-alpha", 1.0)
                if hasattr(self, 'tooltip_after_id') and self.tooltip_after_id:
                    self.after_cancel(self.tooltip_after_id)
                self.tooltip_after_id = self.after(1000, _create)
            def _cancel(e):
                if hasattr(self, 'tooltip_after_id') and self.tooltip_after_id:
                    self.after_cancel(self.tooltip_after_id)
                    self.tooltip_after_id = None
                self.hide_tooltip()
            w.bind("<Enter>", _show)
            w.bind("<Leave>", _cancel)
        add_tt(self.btn_oggi_stats, "Torna al giorno di oggi")
        add_tt(self.btn_giorno, "Statistiche dettagliate del mese selezionato")
        add_tt(self.btn_mese, "Statistiche raggruppate del mese selezionato")
        add_tt(self.btn_anno, "Statistiche raggruppate dell'anno selezionato")
        add_tt(self.btn_totali, "Totali generali raggruppati di tutti i movimenti")
        add_tt(self.btn_ciclico, "Cicla la visualizzazione delle statistiche")
        add_tt(self.btn_analisi, "Mostra analisi grafiche dettagliate")
        add_tt(self.btn_help, "Hub Pannello Moduli Principali")
        add_tt(self.btn_aggiorna_lib, "Aggiornamenti librerie disponibili — clicca per aggiornare")    
        def crea_icona_nav(chiave, comando, tooltip, emoji):
                img = self.icone_gui.get(chiave)
                lbl = tk.Label(
                        mode_frame, 
                        image=img, 
                        text=emoji if not img else "", 
                        bg=self.COLOR_WIDGET_BG, 
                        fg=self.TEXT_COLOR, 
                        cursor="hand2"
                )
                lbl.pack(side="right", anchor="e", padx=(0, 1))
                lbl.bind('<Button-1>', lambda e: comando())
                add_tt(lbl, tooltip)
                return lbl
        self.btn_saldo = crea_icona_nav("saldo_B", self.open_saldo_conto, "Apri Portafoglio Bancario", "💰")        
        self.btn_shortcuts = crea_icona_nav("tastiera_B", self.mostra_popup_scorciatoie, "Visualizza Scorciatoie da Tastiera", "⌨️")
        self.btn_shortcuts.pack(side=tk.RIGHT, padx=1)  
        self.btn_iconizza = crea_icona_nav("iconizza_B", self.iconify, "Riduci a icona", "🗗")
        self.btn_report_html = crea_icona_nav("report_B", self.genera_report_pdf, "Genera un Bilancio Annuo PDF", "📊")
        self.btn_web_qr = crea_icona_nav("qr_B", self.mostra_qr_popup_label, "Genera QR per accesso Web", "🌐")
        self.btn_promemoria = crea_icona_nav("promemoria_B", self.gestisci_promemoria, "Gestione Promemoria", "📌")
        self.btn_qr_generator = crea_icona_nav("timer_B", self.launch_qr_svg_generator, "Generatore QR e Timer", "⏰")
        self.btn_controlla_ricorrenze = crea_icona_nav("scadenze_B", self.controlla_ricorrenti_manual, "Controlla scadenze e ricorrenze", "📢")
        self.btn_documenti_icona = crea_icona_nav("documenti_B", self.gestisci_archivi_pdf, "Archivio Documenti Contabili", "📁")
        self.btn_documenti_icona = crea_icona_nav("documentiP_B", self.gestisci_documenti_personali, "Archivio Documenti Personali", "📁")
        self.btn_spesa_super_icon = crea_icona_nav("spesa_B", self.spesa_supermercato, "Gestione Lista della Spesa", "🛒")
        self.btn_banca = crea_icona_nav("banca_B", self.chiama_banca, "Accedi ai servizi bancari", "🏦")
        self.btn_analisi_ia = crea_icona_nav("sparkles_B", self.analizza_andamento_ia, "Analisi Bilancio OpenAI", "✨")
        self.btn_scadenze_mese = crea_icona_nav("calendario_B", self.scadenze_mese, "Scadenze del mese", "📅")
        self._ricerca_globale_var = tk.StringVar()
        self._ricerca_globale_var.trace_add("write", self._filtra_stats_table_globale)
        self.ricerca_globale_entry = ttk.Entry(mode_frame, textvariable=self._ricerca_globale_var, width=16)
        self._ricerca_globale_aperta = False
        self.btn_ricerca_globale = crea_icona_nav("search_B", self._toggle_ricerca_globale, "Ricerca Globale Movimenti", "🔍")
        self.stats_label = ttk.Label(stat_frame, text="")
        self.stats_label.grid(row=1, column=0, sticky="w", padx=(0, 6), pady=(2, 0))
        img_mouse = self.icone_gui.get("mouse")
        self.stats_hint_label = ttk.Label(
                stat_frame,
                text="", 
                image=img_mouse,
                compound="right",
                foreground="gray",
                font=("Arial", 7, "italic")
        )
        if img_mouse:
                self.stats_hint_label.image = img_mouse
        self.stats_hint_label.grid(row=1, column=0, sticky="e", padx=6, pady=(2, 0))
        totali_row = ttk.Frame(stat_frame)
        totali_row.grid(row=2, column=0, sticky="ew", padx=6, pady=(2, 0))
        self.totali_label = ttk.Label(totali_row, text="", font=("Arial", 11))
        self.totali_label.pack(side=tk.LEFT)
        self.considera_ricorrenze_var = tk.BooleanVar(value=True)
        self.considera_futuri_portafoglio_var = tk.BooleanVar(value=True)
        chk_container_frame = ttk.Frame(totali_row)
        chk_container_frame.pack(side=tk.RIGHT, padx=12)
        # Pulsante Carosello
        if CAROSELLO:
            self.var_carosello_enabled = tk.BooleanVar(self, value=True)
            img_reset = self.icone_gui.get("reset")
            self.btn_ciclico_carosello = ttk.Checkbutton(
                chk_container_frame,
                image=img_reset if img_reset else "",
                variable=self.var_carosello_enabled,
                command=self.toggle_carosello
            )
            if img_reset:
                self.btn_ciclico_carosello.image = img_reset
            self.btn_ciclico_carosello.pack(side=tk.LEFT, padx=0)
        def _refresh_con_grafici():
            if hasattr(self, 'stats_label') and "Dettaglio Giornaliero" in self.stats_label.cget("text"):
                self.goto_dettaglio_mese()
                return
            self.refresh_gui()
            mode = self.stats_view_mode.get() if hasattr(self, 'stats_view_mode') else ""
            if mode == "grafico":
                self.draw_bar_chart()
            elif mode == "grafico_mensile":
                self.draw_mensile_chart()
            elif mode == "grafico_saldo":
                self.draw_saldo_chart()
            elif mode == "proiezione_fondo":
                self.toggle_stats_view("proiezione_fondo")
        self.chk_ricorrenze = ttk.Checkbutton(
            chk_container_frame,
            text="Includi movimenti futuri nei totali",
            variable=self.considera_ricorrenze_var,
            command=_refresh_con_grafici
        )
        self.chk_ricorrenze.pack(side=tk.LEFT, padx=0) 
        self.filtri_temporali = [self.btn_giorno, self.btn_mese, self.btn_anno, self.btn_totali]
        table_container = ttk.Frame(stat_frame)
        table_container.grid(row=3, column=0, sticky="nsew", padx=4, pady=4)
        self.stats_table_container = table_container
        self.vsb_stats = ttk.Scrollbar(table_container, orient="vertical")
        self.vsb_stats.pack(side=tk.RIGHT, fill=tk.Y)
        self.hsb_stats = ttk.Scrollbar(table_container, orient="horizontal")
        self.hsb_stats.pack(side=tk.BOTTOM, fill=tk.X)
        self.stats_canvas = tk.Canvas(
            table_container, 
            bg=self.COLOR_WIDGET_BG, 
            highlightthickness=0
        )
        self.stats_canvas.config(xscrollcommand=self.hsb_stats.set)
        self.hsb_stats.config(command=self.stats_canvas.xview)
        self.stats_table = ttk.Treeview(
            table_container, 
            columns=("A", "B", "C", "D", "E", "F"), 
            show="headings",
            yscrollcommand=self.vsb_stats.set,
            xscrollcommand=self.hsb_stats.set
        )
        self.stats_table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.vsb_stats.config(command=self.stats_table.yview)
        self.stats_text_area = tk.Text(stat_frame, wrap=tk.WORD, state=tk.DISABLED, bg="#F0F0F0")
        headers = {
            "A": "Data",
            "B": "Categoria",
            "C": "Descrizione",
            "D": "Importo",
            "E": "Tipo",
            "F": "Conto/Varia"
        }
        for col in ("A", "B", "C", "D", "E", "F"):
            self.stats_table.heading(col, text=headers[col], command=lambda _col=col: self.treeview_sort_column(self.stats_table, _col, False))            
        self.stats_table.column("A", width=100, anchor="center")
        self.stats_table.column("B", width=150, anchor="center")
        self.stats_table.column("C", width=250, anchor="w")
        self.stats_table.column("D", width=100, anchor="e")
        self.stats_table.column("E", width=70, anchor="center")
        self.stats_table.column("F", width=100, anchor="center")        
        self.set_stats_mode("giorno")
        self.stats_table.tag_configure("uscita", foreground="red")
        self.stats_table.tag_configure("entrata", foreground="green")        
        self.stats_table.bind("<Double-1>", self.on_stats_table_double_click)
        self.stats_table.bind("<ButtonRelease-1>", self.on_table_click)
        self.stats_table.bind("<Button-3>", self.on_stats_table_right_click)
        self._bind_tooltip_metodo(self.stats_table, col_desc=2)
        lbl_form_container = tk.Frame(right_frame, bg=self.COLOR_WIDGET_BG)
        lbl_form_icon = tk.Label(lbl_form_container, text="⚙️ Registra o Modifica Movimento",
                font=("Arial", 10, "bold"), bg=self.COLOR_WIDGET_BG, fg="red")
        lbl_form_icon.pack(side="left")
        self._form_collapsed = False
        def _toggle_form():
            self._form_collapsed = not self._form_collapsed
            for w in form_frame.winfo_children():
                if self._form_collapsed:
                    w.grid_remove()
                else:
                    w.grid()
            if self._form_collapsed:
                form_frame.pack_propagate(False)
                form_frame.config(height=28)
            else:
                form_frame.pack_propagate(True)
            btn_collapse.config(text="▶" if self._form_collapsed else "▼")
        btn_collapse = tk.Label(
            lbl_form_container, text="▼",
            font=("Arial", 9, "bold"), bg=self.COLOR_WIDGET_BG,
            fg="red", cursor="hand2"
        )
        btn_collapse.pack(side=tk.RIGHT, padx=(0, 6))
        btn_collapse.bind("<Button-1>", lambda e: _toggle_form())
        if ABILITA_WEBSERVER:
            _protocollo_titolo = " (HTTPS)" if USA_SSL and os.path.exists(os.path.join(DB_DIR, "cert.pem")) else " (HTTP)"
            tk.Frame(lbl_form_container, height=1, bg="gray50").pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=2)
            self.lbl_webport = ttk.Label(
                lbl_form_container,
                image=self.icone_gui.get("mobile"),
                text=f" Port: {PORTA}{_protocollo_titolo}",
                compound="left",
                font=("Arial", 7, "italic"),
                foreground=self.TEXT_COLOR,
                background=self.COLOR_WIDGET_BG,
                cursor="hand2"
            )
            self.lbl_webport.pack(side=tk.RIGHT, padx=(0, 4))
            self.lbl_webport.bind("<Button-1>", lambda e: self.mostra_qr_popup_label())
            add_tt(self.lbl_webport, "Mostra QR accesso web")
            tk.Frame(lbl_form_container, height=1, bg="gray50").pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=2)
        if _HAS_DND:
            img_mouse_form = self.icone_gui.get("mouse")
            lbl_form_hint = ttk.Label(lbl_form_container,
                text=" Trascina qui un documento per importarlo ",
                image=img_mouse_form, compound="left",
                foreground="gray", font=("Arial", 7, "italic"),
                background=self.COLOR_WIDGET_BG)
            lbl_form_hint.image = img_mouse_form
            lbl_form_hint.pack(side=tk.LEFT, padx=(6, 0))
        form_frame = ttk.LabelFrame(right_frame, labelwidget=lbl_form_container, style="RedBold.TLabelframe")
        form_frame.pack(fill=tk.X, padx=2, pady=(8, 8))
        form_frame.grid_columnconfigure(1, weight=1)
        row = 0  
        right_info_container = tk.Frame(form_frame, bd=2, relief="flat", bg=self.COLOR_WIDGET_BG)
        right_info_container.grid(row=0, column=2, rowspan=4, sticky="nsew", padx=10, pady=5)
        txt_m = f"Target Mese: € {TARGET_MESE:.2f}" if TARGET_MESE > 0 else "Target Mese: N/D"
        txt_a = f"Target Anno: € {TARGET_ANNO:.2f}" if TARGET_ANNO > 0 else "Target Anno: N/D"
        self.lbl_budget_mese_widget = ttk.Label(right_info_container, text=txt_m, font=("Arial", 8, "bold"), style="TLabel")
        self.lbl_budget_mese_widget.pack(anchor="w", padx=5, pady=2)
        self.lbl_budget_anno_widget = ttk.Label(right_info_container, text=txt_a, font=("Arial", 8, "bold"), style="TLabel")
        self.lbl_budget_anno_widget.pack(anchor="w", padx=5, pady=2)
        self.lbl_budget_cat_sforati = ttk.Label(right_info_container, text="", font=("Arial", 8, "bold"), foreground=self.COLOR_RED, style="TLabel", cursor="hand2")
        self.lbl_budget_cat_sforati.pack(anchor="w", padx=5, pady=2)
        add_tt(self.lbl_budget_cat_sforati, lambda: getattr(self, '_tt_budget_sforati_txt', ''))
        self.lbl_budget_cat_sforati.bind("<Button-1>", lambda e: self.mostra_transazioni_popup(
            {"categorie": list(self._budget_sforati), "anno": str(datetime.date.today().year), "mese": datetime.date.today().month},
            f"Movimenti oltre soglia – {['','Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno','Luglio','Agosto','Settembre','Ottobre','Novembre','Dicembre'][datetime.date.today().month]} {datetime.date.today().year}"
        ) if getattr(self, '_budget_sforati', None) else None)
        add_tt(self.lbl_budget_cat_sforati, lambda: getattr(self, '_tt_budget_sforati_txt', ''))
        btns_row = tk.Frame(right_info_container, bg=self.COLOR_WIDGET_BG)
        btns_row.pack(fill="x", padx=5, pady=2)
        self.lbl_sync_count_widget = ttk.Label(
            btns_row,
            image=self.icone_gui.get("sync"),
            text=f" Sync: {self.operazioni_scaricate_sessione}",
            compound="left",
            font=("Arial", 9, "bold"),
            foreground=self.TEXT_COLOR,
            background=self.COLOR_WIDGET_BG
        )
        self.lbl_sync_count_widget.pack(side="left", padx=(0, 6))
        def apri_cartella_pdf(event=None):
            import os, subprocess, platform
            cartella = getattr(self, 'cartella_export_pdf', 'Fatture_GMail')
            if not os.path.exists(cartella):
                os.makedirs(cartella)
            try:
                if platform.system() == "Windows": os.startfile(cartella)
                elif platform.system() == "Darwin": subprocess.Popen(["open", cartella])
                else: subprocess.Popen(["xdg-open", cartella])
            except Exception as e: print(f"Errore: {e}")
        self.btn_open_pdf_folder = ttk.Label(
            btns_row, image=self.icone_gui.get("documenti"), 
            cursor="hand2", background=self.COLOR_WIDGET_BG
        )
        self.btn_open_pdf_folder.pack(side="left", padx=(0, 5))
        self.btn_open_pdf_folder.bind("<Button-1>", apri_cartella_pdf)
        add_tt(self.btn_open_pdf_folder, "Apri cartella PDF Gmail")
        self.btn_avvia_sync = ttk.Label(
            btns_row, image=self.icone_gui.get("qr"), 
            cursor="hand2", background=self.COLOR_WIDGET_BG
        )
        self.btn_avvia_sync.pack(side="left", padx=5)
        self.btn_avvia_sync.bind("<Button-1>", lambda e: self.avvia_sincronizzazione(manuale=True))
        add_tt(self.btn_avvia_sync, "Avvia sincronizzazione manuale")
        self.btn_reset_sync = ttk.Label(
            btns_row, image=self.icone_gui.get("reset"), 
            cursor="hand2", background=self.COLOR_WIDGET_BG
        )
        self.btn_reset_sync.pack(side="left", padx=5)
        self.btn_reset_sync.bind("<Button-1>", lambda e: self.ricalcola_operazioni_web())
        add_tt(self.btn_reset_sync, "Ricalcola operazioni web")
        self.btn_apri_log = ttk.Label(
            btns_row, 
            image=self.icone_gui.get("archivia"), 
            compound="left",
            cursor="hand2", 
            background=self.COLOR_WIDGET_BG,
            font=("Arial", 9, "bold"),
            foreground=self.TEXT_COLOR
        )
        self.btn_apri_log.pack(side="left", padx=5) 
        self._tick_orologio()
        self.btn_apri_log.bind("<Button-1>", lambda e: self.mostra_log_importazioni())
        add_tt(self.btn_apri_log, "Log importazioni")
        add_tt(self.lbl_topic, "Clicca per contattare il supporto via email")
        self.label_data_spesa = ttk.Label(
            form_frame, 
            text=" Data Movimento:", 
            image=self.icone_gui.get("timer"),
            compound="left",
            font=("Arial", 10, "bold"),
            style="BlinkAllarme.TLabel" 
        )
        self.label_data_spesa.grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.data_spesa_var = tk.StringVar(value=today.strftime("%d-%m-%Y"))
        data_frame = ttk.Frame(form_frame)
        data_frame.grid(row=row, column=1, columnspan=2, sticky="w")
        self.data_spesa_entry = ttk.Entry(
            data_frame,
            width=15,
            font=("Arial", 10, "bold"),
            textvariable=self.data_spesa_var
        )
        self.data_spesa_entry.pack(side="left")
        self.btn_cal_data_spesa = ttk.Label(
            data_frame,
            image=self.icone_gui.get("calendario"),
            cursor="hand2",
            background=self.COLOR_WIDGET_BG
        )
        self.btn_cal_data_spesa.pack(side="left", padx=2)
        self.btn_cal_data_spesa.bind(
            "<Button-1>", 
            lambda e: self.mostra_calendario_popup(self.data_spesa_entry, self.data_spesa_var)
        )   
        self.btn_reset_data_spesa = ttk.Label(
            data_frame,
            image=self.icone_gui.get("reset"),
            cursor="hand2",
            background=self.COLOR_WIDGET_BG
        )
        self.btn_reset_data_spesa.pack(side="left", padx=5)
        self.btn_reset_data_spesa.bind("<Button-1>", lambda e: self.reset_data_spesa())
        self.blocca_data_var = tk.BooleanVar(value=False)
        self.checkbox_blocca_data = ttk.Checkbutton(
            data_frame,
            text="Blocca data",
            variable=self.blocca_data_var,
            command=self.on_blocca_data_changed
        )
        self.checkbox_blocca_data.pack(side="left", padx=4)
        self.btn_importa_popup = ttk.Label(
            data_frame,
            text="Import IA",
            image=self.icone_gui.get("carica"),
            compound="left",
            cursor="hand2",
            font=("Arial", 9, "bold"),
            background=self.COLOR_WIDGET_BG,
            foreground=self.COLOR_GREEN
        )
        self.btn_importa_popup.pack(side="left", padx=6)
        self.btn_importa_popup.bind("<ButtonRelease-1>", lambda e: self.apri_finestra_importa())
        add_tt(self.btn_importa_popup, "Importa dati tramite IA")
        row += 1
        self.label_categoria_form = ttk.Label(
            form_frame, 
            text=" Seleziona categoria:", 
            image=self.icone_gui.get("documenti"),
            compound="left",
            font=("Arial", 10, "bold")
        )
        self.label_categoria_form.grid(row=row, column=0, sticky="e", padx=5, pady=2)
        combo_frame = ttk.Frame(form_frame)
        combo_frame.grid(row=row, column=1, sticky="w", columnspan=2, pady=(2, 2))
        self.cat_sel = tk.StringVar(value=self.categorie[0])        
        self.cat_menu = ttk.Combobox(combo_frame, textvariable=self.cat_sel, values=sorted(self.categorie, key=lambda c: c.lower()), state="readonly", width=25, style="Border.TCombobox", font=("Arial", 10, "bold"))
        self.cat_menu.pack(side="left")
        def _val_filter(p):
            return len(p) <= 3
        _vf = combo_frame.register(_val_filter)
        self.cat_filter_entry = ttk.Entry(combo_frame, width=3, font=("Arial", 9, "bold"), validate="key", validatecommand=(_vf, "%P"))
        self.cat_filter_entry.pack(side="left", padx=(4, 0))
        self.btn_reset_cat = tk.Label(
            combo_frame,
            text="✕",
            font=("Arial", 9, "bold"),
            foreground=self.COLOR_RED if hasattr(self, "COLOR_RED") else "red",
            background=self.COLOR_WIDGET_BG,
            cursor="hand2"
        )
        self.btn_reset_cat.pack(side="left", padx=(2, 0))
        def _on_reset_cat(e=None):
            _reset_filtro_cat()
            self.cat_sel.set(self.categorie[0])
            self.on_categoria_changed(manuale=False)
        self.btn_reset_cat.bind("<Button-1>", _on_reset_cat)
        self._filter_after_id = None
        def _filtra_cat(event):
            if event.keysym in ("Return", "KP_Enter", "Escape", "Tab"):
                return
            if self._filter_after_id:
                self.after_cancel(self._filter_after_id)
            typed = self.cat_filter_entry.get().strip()
            if not typed:
                self.cat_menu.config(values=sorted(self.categorie, key=lambda c: c.lower()))
                self.cat_sel.set("Generica")
                self.on_categoria_changed(manuale=False)
                return
            filtrate = sorted([c for c in self.categorie if c.lower().split()[0].startswith(typed.lower())], key=lambda c: c.lower())
            if not filtrate:
                filtrate = sorted([c for c in self.categorie if typed.lower() in c.lower()], key=lambda c: c.lower())
            if not filtrate:
                return
            self.cat_menu.config(values=filtrate)
            self.cat_sel.set(filtrate[0])
            self.on_categoria_changed(manuale=True)
            if len(filtrate) == 1:
                self.cat_filter_entry.delete(0, "end")
                self.cat_menu.config(values=sorted(self.categorie, key=lambda c: c.lower()))
                self.categoria_bloccata = True
                self.imp_entry.focus_set()
                return
            if len(typed) >= 3:
                self.cat_menu.event_generate("<Button-1>")
            self.cat_filter_entry.config(foreground=self.COLOR_RED)
        def _reset_filtro_cat():
            if self._filter_after_id:
                self.after_cancel(self._filter_after_id)
            self.cat_filter_entry.delete(0, "end")
            self.cat_filter_entry.config(foreground=self.TEXT_COLOR)
            self.cat_menu.config(values=sorted(self.categorie, key=lambda c: c.lower()))
        self._reset_filtro_cat = _reset_filtro_cat
        self.cat_filter_entry.bind("<KeyRelease>", _filtra_cat)
        self.cat_filter_entry.bind("<Escape>", lambda e: _reset_filtro_cat())      
        self.label_smartcat = ttk.Label(
            combo_frame, 
            text=" SmartCat On", 
            foreground="red", 
            font=("Arial", 9, "bold")
        )
        self.label_smartcat.pack(side="left", padx=5)
        self.btn_spese_simili = ttk.Label(
            combo_frame, 
            image=self.icone_gui.get("filtri"),
            compound="left",
            cursor="hand2",
            font=("Arial", 9, "italic"),
            background=self.COLOR_WIDGET_BG,
            foreground=self.COLOR_GREEN
        )
        self.btn_spese_simili.bind("<Button-1>", lambda e: self.mostra_spese_simili())
        self.btn_spese_simili.pack(side="left", padx=(6, 0))
        self.btn_spese_simili.pack_forget()
        if not self.suggerimenti_attivi:
            self.label_smartcat.config(text="💡 SmartCat Off", foreground="green")
            self.aggiorna_bottone_spese_simili(visibile=False)
        else:
             self.label_smartcat.config(text="💡 SmartCat On", foreground="red")
        self.cat_menu.bind("<<ComboboxSelected>>", lambda e: (
                self._reset_filtro_cat(),
                self.on_categoria_changed(e),
                self.cat_menu.selection_clear(),
                setattr(self, "categoria_bloccata", True),
                self.imp_entry.focus_set()
        ))
        row += 1
        self.label_descrizione_form = ttk.Label(
            form_frame, 
            text=" Descrizione:", 
            image=self.icone_gui.get("descrizione"),
            compound="left",
            font=("Arial", 10, "bold")
        )
        self.label_descrizione_form.grid(row=row, column=0, sticky="w", padx=5, pady=(2, 2))
        def convalida_descrizione(nuovo_valore_1):
         return len(nuovo_valore_1) <= 35         
        vdesc = form_frame.register(convalida_descrizione)
        desc_frame = ttk.Frame(form_frame)
        desc_frame.grid(row=row, column=1, sticky="w")
        self.desc_entry = ttk.Entry(desc_frame, width=22, validate="key", validatecommand=(vdesc, "%P"))
        self.desc_entry.pack(side=tk.LEFT)
        self.nomi_con_icone = []
        self.nomi_partecipanti.sort(key=lambda x: (
                0 if x.get("tipo") == "contenitore" else
                (2 if x.get("tipo") == "personale" else 1),
                x.get("nome", "").lower()
        ))
        _gestore_init = os.path.basename(os.getcwd())
        _nomi_init    = [p.get("nome", "") for p in self.nomi_partecipanti]
        if self._gestore_partecipa() and _gestore_init not in _nomi_init:
            self.nomi_con_icone.append(f"PER· {_gestore_init}")
        for p in self.nomi_partecipanti:
                n = p.get("nome", "")
                t = p.get("tipo", "persona")
                ico = "CNT·" if t == "contenitore" else ("CTP·" if t == "personale" else "PER·")
                self.nomi_con_icone.append(f"{ico} {n}")
        img_partecipante = self.icone_gui.get("utenti")
        lbl_part = ttk.Label(desc_frame, image=img_partecipante,
                             text=" 👥" if not img_partecipante else "",
                             compound="left", cursor="hand2",
                             background=self.COLOR_WIDGET_BG)
        lbl_part.pack(side=tk.LEFT, padx=(4, 0))
        lbl_part.bind("<Button-1>", lambda e: self.mostra_dare_avere())
        self.partecipante_var = tk.StringVar(value="")
        self.partecipante_combobox = ttk.Combobox(
                desc_frame,
                textvariable=self.partecipante_var,
                values=[""] + self.nomi_con_icone + ["⚙️ Gestisci Partecipanti"],
                state="readonly",
                style="Border.TCombobox",
                width=25
        )
        self.partecipante_combobox.pack(side=tk.LEFT, padx=(0, 4))
        self.partecipante_combobox.bind("<<ComboboxSelected>>", lambda e: (
                self._on_partecipante_selected(),
                self.partecipante_combobox.selection_clear(),
                self.partecipante_var.set(""),
                self.imp_entry.focus_set()
        ))
        add_tt(self.partecipante_combobox, "Seleziona partecipante FairShare")
        row += 1
        importo_label_frame = ttk.Frame(form_frame)
        importo_label_frame.grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.calc_button = ttk.Label(
            importo_label_frame, image=self.icone_gui.get("calcolatrice"),
            cursor="hand2", background=self.COLOR_WIDGET_BG
        )
        self.calc_button.pack(side=tk.LEFT, padx=(0, 4))
        self.calc_button.bind("<Button-1>", lambda e: self.apri_calcolatrice())
        self.label_importo_form = ttk.Label(
            importo_label_frame, 
            text=" Importo (€):", 
            image=self.icone_gui.get("saldo"), 
            compound="left",
            font=("Arial", 10, "bold")
        )
        self.label_importo_form.pack(side=tk.LEFT)
        importo_frame = ttk.Frame(form_frame)
        importo_frame.grid(row=row, column=1, sticky="w", pady=5)        
        def convalida_input(nuovo_valore_2):
         if nuovo_valore_2 == "":
              return True  
         import re
         # Imposta massimo
         return len(nuovo_valore_2) <= 8 and re.match(r"^\d*[.,]?\d{0,2}$", nuovo_valore_2) is not None
        vcmd = form_frame.register(convalida_input)       
        self.imp_entry = ttk.Entry(importo_frame, width=12, validate="key", validatecommand=(vcmd, "%P"))  
        self.imp_entry.pack(side=tk.LEFT)      
        self.imp_entry.bind("<KeyRelease>", self.aggiorna_categoria_automatica)
        self.imp_entry.bind("<Return>", lambda event: self.add_spesa()) 
        self.imp_entry.bind("<KP_Enter>", lambda event: self.add_spesa())         
        def start_blinking_callback(event):
            self.start_blinking(self.label_data_spesa)
            if self.STATO_CORRENTE != 0:
                self.mostra_treeview_statistiche()           
        def stop_blinking_callback(event):
            self.stop_blinking(self.label_data_spesa)        
        self.imp_entry.bind('<FocusIn>', start_blinking_callback)
        self.imp_entry.bind('<FocusOut>', stop_blinking_callback)        
        self.bind("<Map>", self._gestisci_ripristino_focus)        
        importo_frame.grid(row=row, column=1, sticky="w")
        if hasattr(self, 'imp_entry'):
            self.after(0, self.imp_entry.focus_set)
        row += 1
        conto_sel_frame = ttk.Frame(form_frame)
        conto_sel_frame.grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        self.lbl_conto_movimento = ttk.Label(
                conto_sel_frame,
                text=" Conto: ",
                image=self.icone_gui.get("saldo"),
                compound="left",
                font=("Arial", 10, "bold")
        )
        self.lbl_conto_movimento.pack(side="left")
        self.v_conto_movimento = tk.StringVar(value="(nessuno)")
        try:
                with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _f:
                        _db_c = json.load(_f)
                _nomi_conti = ["(nessuno)", "📂 Portafoglio", "───────────"] + [c.get("nome", "?") for c in _db_c.get("conti", [])]
                _principale = next((c.get("nome", "") for c in _db_c.get("conti", []) if c.get("principale")), "(nessuno)")
                self.v_conto_movimento.set(_principale)
        except Exception:
                _nomi_conti = ["(nessuno)"]
        self.cb_conto_movimento = ttk.Combobox(
                conto_sel_frame,
                textvariable=self.v_conto_movimento,
                values=_nomi_conti,
                state="readonly",
                width=18,
                style="Border.TCombobox"
        )
        self.cb_conto_movimento.pack(side="left")
        add_tt(self.cb_conto_movimento, "Conto bancario")
        def gestisci_selezione_conto(event):
                scelta = self.v_conto_movimento.get()
                if scelta == "📂 Portafoglio":
                        self.open_saldo_conto()
                        self.v_conto_movimento.set("(nessuno)")
        self.cb_conto_movimento.bind("<<ComboboxSelected>>", gestisci_selezione_conto)
        lbl_ico_pagamento = ttk.Label(
                conto_sel_frame, 
                image=self.icone_gui.get("banca"),
                compound="left"
        )
        lbl_ico_pagamento.pack(side="left", padx=(12, 4))
        self.metodo_pagamento_var = tk.StringVar(value="") 
        metodi = METODI_PAGAMENTO_FILTRO
        self.metodo_pagamento_combobox = ttk.Combobox(
                conto_sel_frame, 
                textvariable=self.metodo_pagamento_var, 
                values=metodi,
                state="readonly",
                style="Border.TCombobox",
                width=16,
        )
        self.metodo_pagamento_combobox.pack(side="left", padx=4) 
        def gestisci_selezione_metodo(event):
                scelta = self.metodo_pagamento_var.get()
                if scelta == SEPARATORE_FILTRO_MOVIMENTI:
                        self.metodo_pagamento_var.set("")
                        return
                if scelta == VOCE_FILTRO_MOVIMENTI:
                        self.apri_estratti_metodo()
                        self.metodo_pagamento_var.set("")
                else:
                        self.aggiorna_descrizione_con_simbolo(event)
                self.metodo_pagamento_combobox.selection_clear()
                self.imp_entry.focus_set()
        self.metodo_pagamento_combobox.bind("<<ComboboxSelected>>", gestisci_selezione_metodo)
        add_tt(self.metodo_pagamento_combobox, "Metodo di pagamento")
        lbl_hash = ttk.Label(conto_sel_frame, text="#", compound="left", cursor="hand2", 
                     background=self.COLOR_WIDGET_BG, font=("Arial", 14, "bold"))
        lbl_hash.pack(side="left", padx=(8, 2))
        lbl_hash.bind("<Button-1>", lambda e: self.apri_gestione_tag())
        add_tt(lbl_hash, "Gestione Tag #")
        _vcmd_tag = (self.register(lambda P: len(P) <= 15), "%P")
        self.tag_entry = ttk.Entry(conto_sel_frame, width=15, style="Border.TEntry",
                                   validate="key", validatecommand=_vcmd_tag)
        self.tag_entry.pack(side="left")
        add_tt(self.tag_entry, "Inserimento Tag #")
        self._ac_lb = None
        def _get_tutti_tag():
            if not hasattr(self, '_cache_tutti_tag'):
                tutti = set()
                for lista in self.spese.values():
                    for voce in lista:
                        for t in campo(voce, "hashtag", []):
                            tutti.add(t.lstrip("#"))
                self._cache_tutti_tag = sorted(tutti)
            return self._cache_tutti_tag
        def _chiudi_ac():
            if self._ac_lb and self._ac_lb.winfo_exists():
                self._ac_lb.destroy()
            self._ac_lb = None
        def _on_tag_keyrelease(event):
            if event.keysym in ("Return", "Escape", "Tab"):
                _chiudi_ac()
                return
            testo = self.tag_entry.get()
            parole = testo.replace(",", " ").split()
            ultima = parole[-1].lstrip("#") if parole else ""
            if len(ultima) < 1:
                _chiudi_ac()
                return
            suggerimenti = [t for t in _get_tutti_tag() if t.lower().startswith(ultima.lower()) and t.lower() != ultima.lower()]
            if not suggerimenti:
                _chiudi_ac()
                return
            if not self._ac_lb or not self._ac_lb.winfo_exists():
                self._ac_lb = tk.Listbox(
                    self.master,
                    height=min(5, len(suggerimenti)),
                    font=("Arial", 9),
                    relief="solid", bd=1,
                    bg=self.COLOR_WIDGET_BG,
                    fg=self.TEXT_COLOR,
                    selectbackground="#4a90d9"
                )
                x = self.tag_entry.winfo_rootx() - self.winfo_rootx()
                y = self.tag_entry.winfo_rooty() - self.winfo_rooty() + self.tag_entry.winfo_height()
                self._ac_lb.place(x=x, y=y, width=self.tag_entry.winfo_width())
                def _seleziona(e):
                    if not self._ac_lb:
                        return
                    sel = self._ac_lb.curselection()
                    if not sel:
                        return
                    scelto = self._ac_lb.get(sel[0])
                    parole_attuali = self.tag_entry.get().replace(",", " ").split()
                    if parole_attuali:
                        parole_attuali[-1] = scelto
                    self.tag_entry.delete(0, tk.END)
                    self.tag_entry.insert(0, " ".join(parole_attuali))
                    _chiudi_ac()
                self._ac_lb.bind("<ButtonRelease-1>", _seleziona)
            self._ac_lb.delete(0, tk.END)
            self._ac_lb.config(height=min(5, len(suggerimenti)))
            for s in suggerimenti:
                self._ac_lb.insert(tk.END, s)
        self.tag_entry.bind("<KeyRelease>", _on_tag_keyrelease)
        self.tag_entry.bind("<FocusOut>", lambda e: self.after(300, _chiudi_ac))
        row += 1
        pannello_bottoni = ttk.Frame(form_frame)
        pannello_bottoni.grid(row=row, column=0, columnspan=10, sticky="w", pady=4, padx=(5, 5))
        self.btn_aggiungi = ttk.Label(
                pannello_bottoni, text=" Aggiungi", image=self.icone_gui.get("carica"),
                compound="left", cursor="hand2", font=("Arial", 10, "bold"),
                background=self.COLOR_WIDGET_BG, foreground=self.COLOR_GREEN
        )
        self.btn_aggiungi.pack(side="left", padx=8)
        self.btn_aggiungi.bind(
                "<Button-1>", 
                lambda e: self.add_spesa() if "disabled" not in self.btn_aggiungi.state() else None
        )
        self.btn_reset_form = ttk.Label(
                pannello_bottoni, image=self.icone_gui.get("reset"),
                cursor="hand2", background=self.COLOR_WIDGET_BG
        )
        self.btn_reset_form.pack(side="left", padx=4)
        self.btn_reset_form.bind("<Button-1>", lambda e: self.reset_form() if "disabled" not in self.btn_reset_form.state() else None)
        self.btn_modifica_sel = ttk.Label(
                pannello_bottoni, text=" Modifica",
                image=self.icone_gui.get("modifica"),
                compound="left",
                background=self.COLOR_WIDGET_BG,
                foreground=self.COLOR_ORANGE,
                cursor="X_cursor", padding=(8, 4)
        )
        self.btn_modifica_sel.pack(side=tk.LEFT, padx=4)
        self.btn_modifica_sel.bind("<Button-1>", lambda e: self.avvia_modifica_da_selezione()
                               if self.stats_table.selection() and self.stats_mode.get() == "giorno"
                               else None)
        self.stats_table.bind("<ButtonRelease-1>", lambda e: self.btn_modifica_sel.config(
                cursor="hand2" if self.stats_table.selection() and self.stats_mode.get() == "giorno"
                else "X_cursor"
        ), add="+")
        self.btn_annulla_modifica = ttk.Label(
                pannello_bottoni, text=" Annulla",
                image=self.icone_gui.get("reset"),
                compound="left", cursor="X_cursor",
                font=("Arial", 9, "bold"),
                background=self.COLOR_WIDGET_BG, foreground=self.COLOR_RED
        )
        self.btn_annulla_modifica.pack(side="left", padx=8)
        self.btn_annulla_modifica.bind("<Button-1>", lambda e: self.reset_modifica_form())
        self.btn_modifica = ttk.Label(
                pannello_bottoni, text=" Salva", image=self.icone_gui.get("salva"),
                compound="left", cursor="X_cursor", font=("Arial", 9, "bold"),
                background=self.COLOR_WIDGET_BG, foreground=self.COLOR_GREEN
        )
        self.btn_modifica.pack(side="left", padx=8)
        self.btn_modifica.bind("<Button-1>", lambda e: self.salva_modifica() if "disabled" not in self.btn_modifica.state() else None)
        self.btn_cancella = ttk.Label(
                pannello_bottoni, text=" Cancella", image=self.icone_gui.get("chiudi"),
                compound="left", cursor="X_cursor", font=("Arial", 9, "bold"),
                background=self.COLOR_WIDGET_BG, foreground=self.COLOR_RED
        )
        self.btn_cancella.pack(side="left", padx=8)
        self.btn_cancella.bind("<Button-1>", lambda e: self.cancella_voce() if "disabled" not in self.btn_cancella.state() else None)
        btn_ricorrenze = ttk.Label(
                pannello_bottoni, text=" Ricorrenze", image=self.icone_gui.get("timer_sync"),
                compound="left", cursor="hand2", font=("Arial", 9),
                background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR
        )
        btn_ricorrenze.pack(side="left", padx=8)
        btn_ricorrenze.bind("<Button-1>", lambda e: self.mostra_ricorrenza_popup())
        self.btn_gestisci_categorie = ttk.Label(
                pannello_bottoni, text=" Categorie", image=self.icone_gui.get("check"),
                compound="left", cursor="hand2", font=("Arial", 9),
                background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR
        )
        self.btn_gestisci_categorie.pack(side="left", padx=8)
        self.btn_gestisci_categorie.bind("<Button-1>", lambda e: self.mostra_categorie_popup())
        row += 1
        cat_default_type = self.categorie_tipi.get(self.cat_sel.get(), "Uscita")
        self.tipo_spesa_var = tk.StringVar(value=cat_default_type)
        btn_style = 'GreenOutline.TButton' if self.tipo_spesa_var.get() == "Entrata" else 'RedOutline.TButton'
        self.btn_tipo_spesa = ttk.Button(
                importo_frame,
                text=self.tipo_spesa_var.get(),
                width=7,
                command=self.toggle_tipo_spesa,
                style=btn_style,
                takefocus=0
        )
        self.btn_tipo_spesa.pack(side=tk.LEFT, padx=8)
        self.btn_tipo_spesa.config(cursor="hand2")
        row += 1
        self.lbl_tipo_percentuale = ttk.Label(importo_frame, text="", font=("Arial", 9, "bold"))
        self.lbl_tipo_percentuale.pack(side=tk.LEFT, padx=4)
        self.on_categoria_changed(manuale=False)
        self.refresh_gui()
        self.after(1000, self.check_aggiornamento_con_api)
        self.after(5000, self._check_librerie_in_background)
        if CLOSE:
                self.protocol("WM_DELETE_WINDOW", self._iconizza_finestra_x)
        else:
                self.protocol("WM_DELETE_WINDOW", self._on_close)
                
        if SYS_BUF_CHECK:
            self.after(500, lambda: self.verify_environment())
        
        self.after(300, self._c_r)    
        
        # Start Carosello
        if CAROSELLO:
            self.after(1000, self.riavvia_scorrimento_automatico)
            
        if _HAS_DND:
            def _main_on_drop(event):
                raw = event.data.strip()
                if raw.startswith("{") and raw.endswith("}"):
                    raw = raw[1:-1]
                paths = [p.strip() for p in raw.split("} {") if p.strip()]
                dropped = paths[0] if paths else raw
                ext = os.path.splitext(dropped)[1].lower()
                if ext not in (".pdf", ".csv", ".png", ".jpg", ".jpeg", ".webp"):
                    self.show_toast("Formato non supportato. Usa PDF, CSV o immagine.")
                    return
                self.apri_finestra_importa(path=dropped)
            try:
                self.drop_target_register(_DND_FILES)
                self.dnd_bind("<<Drop>>", _main_on_drop)
            except Exception:
                pass
                
        self.after(500, lambda: self._controlla_sforamento_budget(mostra_toast=False))

    def aggiorna_vista_ricorrenti(self, includi_futuri=False):
        from datetime import datetime
        oggi = datetime.today().date()
        for i in self.tree_ricorrenti.get_children():
            self.tree_ricorrenti.delete(i)
        mancanti = self.get_lista_categorie_mancanti()
        for cat in mancanti:
            importi = []
            ultima = None
            for d, sp in self.spese.items():
                if isinstance(d, str):
                    try:
                        dd = datetime.strptime(d, "%d-%m-%Y").date()
                    except:
                        continue
                else:
                    dd = d
                diff_mesi = (oggi.year - dd.year) * 12 + (oggi.month - dd.month)
                if diff_mesi < 1 or diff_mesi > 12:
                    continue
                if not includi_futuri and dd > oggi:
                    continue
                for voce in sp:
                    if len(voce) > 2 and str(voce[0]).strip().title() == cat:
                        try:
                            imp = float(voce[2])
                            importi.append(imp)
                            if ultima is None or dd > ultima[0]:
                                ultima = (dd, imp)
                        except:
                            continue
            ultima_spesa = f"€{ultima[1]:.2f}" if ultima else "N/D"
            freq = len(importi)
            self.tree_ricorrenti.insert("", "end", values=(cat, ultima_spesa, f"{freq} volte/anno"))

    def _avvia_rotazione_oggi(self):
        path = os.path.join(PATH_LOCALE, "db", "resources", "filtri.png")
        if not os.path.exists(path):
            return
        self._pil_oggi_orig = Image.open(path).convert("RGBA")
        self._rotazione_oggi_angolo = 0
        self._rotazione_oggi_attiva = True
        self._ruota_oggi()
    def _ruota_oggi(self):
        if not getattr(self, "_rotazione_oggi_attiva", False):
            return
        self._rotazione_oggi_angolo = (self._rotazione_oggi_angolo + 20) % 360
        img = self._pil_oggi_orig.rotate(self._rotazione_oggi_angolo, resample=Image.BICUBIC, expand=False)
        self._foto_oggi_ruotata = ImageTk.PhotoImage(img)
        self.btn_oggi.configure(image=self._foto_oggi_ruotata)
        if hasattr(self, "btn_oggi_stats"):
            self.btn_oggi_stats.configure(image=self._foto_oggi_ruotata)
        self._rotazione_oggi_job = self.after(100, self._ruota_oggi)
                  
    def aggiorna_descrizione_con_simbolo(self, event=None):
        desc_attuale = self.desc_entry.get().strip()
        for simbolo in SIMBOLI_METODO.values():
            if desc_attuale.startswith(simbolo):
                desc_attuale = desc_attuale[len(simbolo):].lstrip()
                break
        self.desc_entry.delete(0, tk.END)
        self.desc_entry.insert(0, desc_attuale)
        self.desc_entry.icursor(tk.END)

    def _metodo_pagamento_pulito(self, valore_combo):
        return metodo_pagamento_pulito(valore_combo)

    def _metodo_pagamento_a_combo(self, nome_pulito):
        if not nome_pulito or not hasattr(self, 'metodo_pagamento_combobox'):
            return ""
        for valore in self.metodo_pagamento_combobox["values"]:
            if self._metodo_pagamento_pulito(valore) == nome_pulito:
                return valore
        return ""
        
    # Cicla Statistiche/Grafici
    def mostra_treeview_statistiche(self):
        self.STATO_CORRENTE = 0
        self.toggle_stats_view("tabella")
        img_next = self.icone_gui.get(self.ICONE_STATI[1])
        if img_next:
            self.btn_ciclico.config(image=img_next)
            self.btn_ciclico.image = img_next
        if hasattr(self, 'imp_entry'):
            self.after(0, self.imp_entry.focus_set)
    
    def _esc_torna_treeview(self):
        if self.stats_view_mode.get() != "tabella":
            self.mostra_treeview_statistiche()
        if hasattr(self, 'mese_notebook') and self.mese_notebook.winfo_exists():
            self.mese_notebook.select(0)
        if getattr(self, '_cruscotto_stato', 0) != 0:
            self._cruscotto_stato = 0
            self.mese_notebook.pack_forget()
            self.cruscotto_canvas.pack_forget()
            if hasattr(self, 'conti_canvas'):
                self.conti_canvas.pack_forget()
            self.mese_notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            self.btn_ciclo_cruscotto.config(text="▼")
            if hasattr(self, '_hint_label_analisi'):
                self._hint_label_analisi.config(text=" Doppio clic → Dashboard  |  Clic destro → Copia nel form")
        if getattr(self, 'sidebar_espansa', False):
            self.contrai_sidebar_manuale()
            self.btn_toggle.configure(text="➤")
            self.sidebar_espansa = False
                        
    def cicla_visualizzazione_statistiche(self, event=None):
        if hasattr(self, 'btn_modifica_sel'):
            self.reset_modifica_form()
        self.STATO_CORRENTE = (self.STATO_CORRENTE + 1) % len(self.STATI_VISTA)
        tipo_vista = self.STATI_VISTA[self.STATO_CORRENTE]
        self.toggle_stats_view(tipo_vista)
        idx_icona_successiva = (self.STATO_CORRENTE + 1) % len(self.STATI_VISTA)
        img_next = self.icone_gui.get(self.ICONE_STATI[idx_icona_successiva])
        if img_next:
            self.btn_ciclico.config(image=img_next)
            self.btn_ciclico.image = img_next
    def cicla_indietro(self, event=None):
        if hasattr(self, 'btn_modifica_sel'):
            self.reset_modifica_form()
        self.STATO_CORRENTE = (self.STATO_CORRENTE - 1) % len(self.STATI_VISTA)
        tipo_vista = self.STATI_VISTA[self.STATO_CORRENTE]
        self.toggle_stats_view(tipo_vista)
        idx_icona_successiva = (self.STATO_CORRENTE + 1) % len(self.STATI_VISTA)
        img_next = self.icone_gui.get(self.ICONE_STATI[idx_icona_successiva])
        if img_next:
            self.btn_ciclico.config(image=img_next)
            self.btn_ciclico.image = img_next   
    def _cicla_se_nel_frame(self, func):
        fw = self.focus_get()
        if fw is not None and fw is not self:
            cls = fw.winfo_class()
            if cls in ("Entry", "TEntry", "TCombobox", "Text", "TSpinbox", "Spinbox"):
                return
        func()
    
    # Start Carosello
    def attiva_binding_stop(self):
        root = self.winfo_toplevel()
        handler = self.handle_stop_carosello
        root.bind('<Motion>', handler)
        root.bind('<Any-KeyPress>', handler)
        root.bind('<Button-1>', handler)
    def disattiva_binding_stop(self):
        root = self.winfo_toplevel()
        try: root.unbind('<Motion>') 
        except: pass
        try: root.unbind('<Any-KeyPress>') 
        except: pass
        try: root.unbind('<Button-1>')
        except: pass
    def esegui_scorrimento_e_riprogramma(self):
        self.chiamato_da_carosello = True
        if not hasattr(self, 'STATI_VISTA'): return
        NUOVO_STATO = (self.STATO_CORRENTE + 1) % len(self.STATI_VISTA)
        tipo_vista = self.STATI_VISTA[NUOVO_STATO]
        self.toggle_stats_view(tipo_vista)   
        idx_next = (NUOVO_STATO + 1) % len(self.STATI_VISTA)
        nome_icona = self.ICONE_STATI[idx_next]
        nuova_img = self.icone_gui.get(nome_icona)
        if hasattr(self, 'btn_ciclico_carosello') and nuova_img:
            self.btn_ciclico_carosello.config(image=nuova_img)
            self.btn_ciclico_carosello.image = nuova_img 
        self.STATO_CORRENTE = NUOVO_STATO
        self.id_scorrimento_automatico = self.after(
            self.intervallo_scorrimento, 
            self.esegui_scorrimento_e_riprogramma
        )
    def handle_stop_carosello(self, event=None):
        try:
            self.ferma_scorrimento_automatico()
        except Exception as e:
            pass
    def ferma_scorrimento_automatico(self):
        self.chiamato_da_carosello = False
        img_reset = self.icone_gui.get("reset")
        if hasattr(self, 'btn_ciclico_carosello'):
            self.btn_ciclico_carosello.config(image=img_reset if img_reset else "", text="")
            if img_reset:
                self.btn_ciclico_carosello.image = img_reset
        if hasattr(self, 'id_scorrimento_automatico') and self.id_scorrimento_automatico is not None:
            try:
                self.after_cancel(self.id_scorrimento_automatico) 
            except Exception:
                pass
            self.id_scorrimento_automatico = None
            self.STATO_CORRENTE = 0
            if hasattr(self, 'mostra_treeview_statistiche'):
                try:
                    self.mostra_treeview_statistiche()
                except Exception:
                    pass
            if hasattr(self, 'var_carosello_enabled'):
                self.var_carosello_enabled.set(False)
        if hasattr(self, 'imp_entry'):
            self.after(0, self.imp_entry.focus_set)
        self.disattiva_binding_stop()
        
    def riavvia_scorrimento_automatico(self):
        self.ferma_scorrimento_automatico() 
        self.id_scorrimento_automatico = self.after(
            self.intervallo_scorrimento, 
            self.esegui_scorrimento_e_riprogramma
        )
        self.attiva_binding_stop()
    def riavvia_scorrimento_manuale(self):
        self.ferma_scorrimento_automatico() 
        self.id_scorrimento_automatico = self.after(
            self.intervallo_scorrimento, 
            self.esegui_scorrimento_e_riprogramma
        )
    def toggle_carosello(self):
        if self.var_carosello_enabled.get():
            self.chiamato_da_carosello = True
            self.STATO_CORRENTE = -1 
            self.riavvia_scorrimento_manuale()
        else:
            self.chiamato_da_carosello = False
            self.ferma_scorrimento_automatico()
            img_reset = self.icone_gui.get("reset")
            if hasattr(self, 'btn_ciclico_carosello') and img_reset:
                self.btn_ciclico_carosello.config(
                    image=img_reset, 
                    text="", 
                    compound="image"
                )
                self.btn_ciclico_carosello.image = img_reset

    def _bind_tooltip_metodo(self, tree, col_desc=2):
        _simboli_tooltip = NOME_DA_EMOJI
        _simbolo_di_nome = SIMBOLI_METODO
        _tt = [None]
        _after = [None]
        _item_cur = [None]
        def _distruggi(event=None):
            if _after[0]:
                self.after_cancel(_after[0])
                _after[0] = None
            if _tt[0]:
                try:
                    _tt[0].destroy()
                except Exception:
                    pass
                _tt[0] = None
            _item_cur[0] = None
        def _mostra(event):
            item = tree.identify_row(event.y)
            if not item:
                _distruggi()
                return
            if item == _item_cur[0]:
                return
            _distruggi()
            _item_cur[0] = item
            metodo = None
            _lookup = getattr(tree, '_metodo_lookup', None)
            _info = _lookup.get(item, {}) if _lookup else {}
            if isinstance(_info, str):
                _info = {"metodo": _info}
            _metodo_pulito = _info.get("metodo", "")
            if _metodo_pulito:
                _sim = _simbolo_di_nome.get(_metodo_pulito, "")
                metodo = f"{_sim} {_metodo_pulito}".strip()
            else:
                valori = tree.item(item, "values")
                if valori and len(valori) > col_desc:
                    desc = str(valori[col_desc]).strip()
                    for simbolo, nome in _simboli_tooltip.items():
                        if simbolo in desc:
                            metodo = f"{simbolo} {nome}"
                            break
            righe = []
            _data_info = _info.get("data", "")
            if _data_info:
                righe.append(f"Data: {_data_info}")
            _ora = _info.get("ora", "")
            if _ora:
                righe.append(f"Orario: {_ora}")
            _categoria_info = _info.get("categoria", "")
            if _categoria_info:
                righe.append(f"Categoria: {_categoria_info}")
            if metodo:
                righe.append(f"Pagamento: {metodo}")
            _conto = _info.get("conto", "")
            if _conto:
                righe.append(f"Conto: {_conto}")
            _importo_info = _info.get("importo", None)
            if _importo_info is not None and _importo_info != "":
                try:
                    righe.append(f"Importo: € {float(_importo_info):.2f}")
                except (TypeError, ValueError):
                    righe.append(f"Importo: {_importo_info}")
            _partecipante_nome = _info.get("partecipante", "")
            if _partecipante_nome:
                _partecipante_tipo = _info.get("partecipante_tipo", "")
                _etichetta_partecipante = (
                    "Contenitore" if _partecipante_tipo == "contenitore" else
                    "Personale" if _partecipante_tipo == "personale" else
                    "Partecipante"
                )
                righe.append(f"{_etichetta_partecipante}: {_partecipante_nome}")
            _id_ric = _info.get("id_ricorrenza", "")
            if _id_ric:
                _ric = self.ricorrenze.get(_id_ric, {})
                _freq = _ric.get("tipo", "")
                righe.append(f"Ricorrente: {_freq}" if _freq else "Ricorrente: Sì")
            _hashtag = _info.get("hashtag", [])
            if isinstance(_hashtag, str):
                _hashtag = [_hashtag] if _hashtag else []
            if _hashtag:
                _tag_fmt = ", ".join(f"#{t.lstrip('#')}" for t in _hashtag if t)
                if _tag_fmt:
                    righe.append(f"Tag: {_tag_fmt}")
            if not righe:
                return
            testo_tooltip = "\n".join(righe)
            def _crea():
                _tt[0] = tk.Toplevel(self)
                _tt[0].wm_overrideredirect(True)
                _tt[0].attributes("-topmost", True)
                ttk.Label(_tt[0], text=testo_tooltip, style="Tooltip.TLabel", justify="left").pack()
                _tt[0].update_idletasks()
                tw = _tt[0].winfo_reqwidth()
                th = _tt[0].winfo_reqheight()
                px = self.winfo_pointerx() + 12
                py = self.winfo_pointery() + 12
                sw = self.winfo_screenwidth()
                sh = self.winfo_screenheight()
                x = px
                y = py
                if x + tw > sw:
                    x = sw - tw - 5
                if y + th > sh:
                    y = sh - th - 5
                _tt[0].wm_geometry(f"+{int(x)}+{int(y)}")
                _tt[0].deiconify()
            _after[0] = self.after(800, _crea)
        tree.bind("<Motion>", _mostra)
        tree.bind("<Leave>", _distruggi)
        tree.winfo_toplevel().bind("<Escape>", _distruggi, add="+")
        tree.winfo_toplevel().bind("<Destroy>", _distruggi, add="+")                
        
    # Colora Giorni Cal in base al Movimento
    def colora_giorni_spese(self):
        self.cal.calevent_remove('all')
        if not self.spese: return
        for data, entries in self.spese.items():
            if not entries: continue
            try:
                e_voci, u_voci = [], []
                tot_e, tot_u = 0.0, 0.0
                for e in entries:
                    cat, imp, tipo = e[0] or "Varie", float(e[2]), str(e[3]).lower()
                    if tipo == "entrata":
                        tot_e += imp
                        e_voci.append((cat, imp))
                    else:
                        tot_u += imp
                        u_voci.append((cat, imp))
                linee = []
                W = 38
                if e_voci:
                    ve = f"€ {tot_e:.2f}"
                    linee.append(f"{'▲ SALDO (+):'.ljust(W - len(ve))}{ve}")
                    for c, v in e_voci:
                        vs = f"{v:.2f}"
                        linee.append(f"{f' {c}'.ljust(W - len(vs))}{vs}")
                if u_voci:
                    if linee: linee.append("─" * W)
                    vu = f"€ {tot_u:.2f}"
                    linee.append(f"{'▼ SALDO (-):'.ljust(W - len(vu))}{vu}")
                    for c, v in u_voci:
                        vs = f"{v:.2f}"
                        linee.append(f"{f' {c}'.ljust(W - len(vs))}{vs}")
                testo_tooltip = "\n" + "\n".join(linee)
                if tot_e > 0 and tot_u > 0: tag = "misto"
                elif tot_e > 0: tag = "verde"
                elif tot_u > 0: tag = "rosso"
                else: continue
                self.cal.calevent_create(data, testo_tooltip, tag)
            except Exception as e:
                print(f"Errore colore giorno {data}: {e}"); continue
        self.cal.calevent_create(datetime.date.today(), "Oggi", "today")

    # Sincronizza Calendari    
    def on_calendar_change(self, event=None):
        self.after(0, self.imp_entry.focus_set)
        try:
            data = self.cal.selection_get()
            if not data:
                return
            mese_corrente = self.estratto_month_var.get()
            anno_corrente = self.estratto_year_var.get()
            mese_da_cal = f"{data.month:02d}"
            anno_da_cal = str(data.year)
            if mese_corrente != mese_da_cal:
                self.estratto_month_var.set(mese_da_cal)
                self.estratto_month_var.set(self.months[data.month - 1])
            if anno_corrente != anno_da_cal:
                self.estratto_year_var.set(anno_da_cal)
                self.estratto_year_var.set(anno_da_cal)
            self.after(100, lambda: self.apply_estratto("giorno"))
        except Exception as e:
            print(f"Errore durante il cambio data: {e}")
    
    # Sincronizza Calendari/imposta data inizio mese
    def on_month_changed(self, event=None):
        m, y = self.cal.get_displayed_month()
        self._view_year = y
        self._view_month = m
        primo = datetime.date(y, m, 1)
        self._changing_month = True
        if self.cal.selection_get() != primo:
            self.cal.selection_set(primo)
        self._changing_month = False
        if not self.blocca_data_var.get():
            self.data_spesa_var.set(primo.strftime("%d-%m-%Y"))
        self.estratto_month_var.set(self.months[m-1])
        self.estratto_year_var.set(str(y))
        if getattr(self, 'stats_view_mode', None) and self.stats_view_mode.get() != "tabella":
            self.mostra_treeview_statistiche()
        modalita_corrente = getattr(self, 'stats_mode', None)
        modalita = modalita_corrente.get() if modalita_corrente else "giorno"
        self.apply_estratto(modalita)
        m_nomi = ["Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno",
                  "Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"]
        now = datetime.date.today()
        if y == now.year and m == now.month:
            self.lbl_titolo_analisi.config(text=" Analisi Mese Attuale")
        else:
            self.lbl_titolo_analisi.config(text=f" Analisi {m_nomi[m-1]} {y}")
        self.update_spese_mese_corrente(year=y, month=m)
        self.update_totalizzatore_mese_corrente(year=y, month=m)
        self.update_totalizzatore_anno_corrente(year=y)
        self.aggiorna_monitoraggio_budget(year=y, month=m)
        
    # Imposta Titolo Finestra
    def aggiorna_titolo_finestra(self):
        stato_db = "📡 [RETE]" if DB_CONDIVISO else "🏠 [LOCALE]"
        current_folder = os.path.basename(os.getcwd())
        scad_str = ""
        try:
            from cryptography.fernet import Fernet
            import json
            _f = Fernet(base64.urlsafe_b64encode(hashlib.sha256("OrbitaCasa|GestioneSpese|2026|∞".encode()).digest()))
            _reg_file   = os.path.join(DB_DIR, "._reg.json")
            _trial_file = os.path.join(DB_DIR, "._trial.json")
            if os.path.exists(_reg_file):
                with open(_reg_file) as fh:
                    raw = json.load(fh)["key"]
                if raw == "__MASTER__":
                    scad_str = " — Licenza: Illimitata"
                else:
                    payload = _f.decrypt(raw.encode()).decode()
                    _, scadenza = payload.split("|")
                    scad_str = " — Licenza: Illimitata" if scadenza == "9999-12-31" else f" — Lic: {datetime.date.fromisoformat(scadenza).strftime('%d/%m/%Y')}"
            elif os.path.exists(_trial_file):
                with open(_trial_file) as fh:
                    primo = datetime.date.fromisoformat(_f.decrypt(json.load(fh)["primo"].encode()).decode())
                giorni = 10 - (datetime.date.today() - primo).days
                scad_str = f" — 🕐 Trial: {max(0, giorni)} gg rimasti"
        except Exception:
            pass
        self.title(f"💰 {NAME} v.{VERSION} — {stato_db} S-ID: {self.SESSION_ID} — Email: helporbitacasa@gmail.com —  Utente:► {current_folder}{scad_str}")
    
    # Bottone Movimenti Simili
    def aggiorna_bottone_spese_simili(self, visibile=True):
        if visibile:
            if not self.btn_spese_simili.winfo_ismapped():
                self.btn_spese_simili.pack(side="left", padx=(6, 0))
                self._avvia_rotazione_spese_simili()
        else:
            if self.btn_spese_simili.winfo_ismapped():
                self._ferma_rotazione_spese_simili()
                self.btn_spese_simili.pack_forget()
    def _avvia_rotazione_spese_simili(self):
        path = os.path.join(PATH_LOCALE, "db", "resources", "filtri.png")
        if not os.path.exists(path):
            return
        self._pil_alert_orig = Image.open(path).convert("RGBA")
        self._rotazione_angolo = 0
        self._rotazione_attiva = True
        self._rotazione_job = None
        self._ruota_alert()
    def _ferma_rotazione_spese_simili(self):
        self._rotazione_attiva = False
        if hasattr(self, "_rotazione_job") and self._rotazione_job:
            self.after_cancel(self._rotazione_job)
            self._rotazione_job = None
        icona = self.icone_gui.get("filtri")
        if icona:
            self.btn_spese_simili.configure(image=icona)

    def _ruota_alert(self):
        if not self._rotazione_attiva:
            return
        self._rotazione_angolo = (self._rotazione_angolo + 20) % 360
        img = self._pil_alert_orig.rotate(self._rotazione_angolo, resample=Image.BICUBIC, expand=False)
        self._foto_alert_ruotata = ImageTk.PhotoImage(img)
        self.btn_spese_simili.configure(image=self._foto_alert_ruotata)
        self._rotazione_job = self.after(100, self._ruota_alert)
         
    # Carica Geometria Finestra
    def load_window_geometry(self):
        self._window_geometry = None 
        if not self.salva_geometria:
            return 
        if not os.path.exists(DB_FILE):
            return
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._window_geometry = data.get("_window_geometry", None)
        except Exception:
            self._window_geometry = None
    # Salva Geometria Finestra
    def save_window_geometry(self):
        if not self.salva_geometria:
            return
        geometry = self.geometry()
        self._window_geometry = geometry
        try:
            data = {}
            if os.path.exists(DB_FILE):
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f) 
            data["_window_geometry"] = geometry 
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Errore salvataggio geometria finestra:", e)

    # Rilascio del lock file e pulizia all'uscita (Non-Windows)
    def _on_close_lock(self):
            if sys.platform.startswith("win"):
                if _mutex_handle:
                    import ctypes
                    ctypes.windll.kernel32.CloseHandle(_mutex_handle)
                return
            try:
                if _lock_file_handle:
                    _lock_file_handle.close()
                    lock_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
                    lock_file_path = os.path.join(lock_dir, 'Orbita_Casa.lock')
                    if os.path.exists(lock_file_path):
                        os.remove(lock_file_path)
                        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] File di lock cancellato.")
            except Exception as e:
                    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore durante la pulizia del lock file: {e}")
            
    def _on_close(self):
        if getattr(self, "_chiusura_in_corso", False):
            return
        self._chiusura_in_corso = True
        splash = self.show_exit_popup()
        splash.update()
        def worker_chiusura():
            for job_attr in ("_job_ricorrenti", "_job_aggiornamento"):
                job = getattr(self, job_attr, None)
                if job:
                    self.after(0, lambda j=job: self.after_cancel(j))
            self._server_running = False
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Chiusura dell'app in corso...")
            self.save_window_geometry()
            self.save_db()
            self._esegui_backup_json()
            self.backup_documenti()
            self.backup_documenti_personali()
            try:
                if hasattr(self, "server") and self.server:
                    self.server.shutdown()
                    self.server.server_close()
                    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Web server chiuso.")
                else:
                    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Nessun web server attivo.")
            except Exception as e:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore chiusura server: {e}")
            self.after(0, lambda: self.finale_chiusura(splash))
        import threading
        t = threading.Thread(target=worker_chiusura, daemon=True)
        t.start()

    def finale_chiusura(self, splash):
        try:
            if splash.winfo_exists():
                splash.destroy()
            self.destroy()
        except: pass
        self._on_close_lock()
        sys.exit(0)

    # Splash screen di chiusura: mostra logo e messaggio di attesa durante il backup finale
    def show_exit_popup(self):
        resources_dir = os.path.join(DB_DIR, "resources")
        logo_path = os.path.join(resources_dir, "info_image.png")
        splash = tk.Toplevel(self)
        splash.overrideredirect(True)
        splash.attributes("-topmost", True)
        w, h = 400, 260
        x = (splash.winfo_screenwidth() // 2) - (w // 2)
        y = (splash.winfo_screenheight() // 2) - (h // 2)
        splash.geometry(f"{w}x{h}+{x}+{y}")
        splash.configure(bg=self.COLOR_BACKGROUND, highlightthickness=2, highlightbackground=self.COLOR_HIGHLIGHT)
        if os.path.exists(logo_path):
            try:
                img_logo = Image.open(logo_path).convert("RGBA")
                img_logo = img_logo.resize((200, 100), Image.Resampling.LANCZOS)
                self.exit_logo_img = ImageTk.PhotoImage(img_logo)
                tk.Label(splash, image=self.exit_logo_img, bg=self.COLOR_BACKGROUND, bd=0).pack(pady=(20, 5))
            except Exception as e:
                print(f"Errore rendering logo: {e}")
        tk.Label(
            splash,
            text=f"{NAME} \nOperazioni di chiusura e backup in corso...\nAttendere prego.",
            font=("Arial", 10, "bold"),
            fg=self.COLOR_HIGHLIGHT,
            bg=self.COLOR_BACKGROUND
        ).pack(pady=5)
        cvs_size = 36
        cvs = tk.Canvas(splash, width=cvs_size, height=cvs_size, bg=self.COLOR_BACKGROUND, highlightthickness=0, bd=0)
        cvs.pack(pady=5)
        gemini_colors = ["#0055FF", "#AA00FF", "#FF0055", "#00C853"]
        state = {"angle": 0, "color_step": 0}
        def animate():
            if not splash.winfo_exists():
                return
            cvs.delete("all")
            state["angle"] = (state["angle"] + 15) % 360
            state["color_step"] += 1
            c_idx = (state["color_step"] // 4) % len(gemini_colors)
            color = gemini_colors[c_idx]
            center = cvs_size // 2
            r = 10
            rad = math.radians(state["angle"])
            px = center + r * math.cos(rad)
            py = center + r * math.sin(rad)
            cvs.create_arc(
                center-r, center-r, center+r, center+r, 
                start=state["angle"]-50, extent=50, 
                outline=color, width=3, style="arc"
            )
            cvs.create_oval(px-2, py-2, px+2, py+2, fill=color, outline=color)
            splash.after(40, animate)
        animate()
        return splash
                
    # Memoria Categorie per importazione Estratto
    def carica_memoria_descrizioni(self):
        if os.path.exists(MEM_CAT):
            try:
                with open(MEM_CAT, "r", encoding="utf-8") as f:
                    self.memoria_descrizioni_categoria = json.load(f)
            except Exception as e:
                print(f"Errore lettura memoria categorie: {e}. Ripristino a vuoto.")
                self.memoria_descrizioni_categoria = {}
        else:
            self.memoria_descrizioni_categoria = {}

    # Caricamento del database JSON e inizializzazione dei dati applicativi 
    def load_db(self):
        if os.path.exists(PARTECIPANTI):
            try:
                with open(PARTECIPANTI, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                if isinstance(raw, dict):
                    lista = raw.get("partecipanti", [])
                else:
                    lista = raw
                self.nomi_partecipanti = [
                    p if isinstance(p, dict) else {"nome": p, "tipo": "persona"}
                    for p in lista
                ]
            except Exception:
                self.nomi_partecipanti = []
        else:
            self.nomi_partecipanti = []
        self.carica_memoria_descrizioni()
        if not os.path.exists(DB_FILE):
            self.db = {
                "categorie": ["Generica"],
                "categorie_tipi": {"Generica": "Uscita"},
                "spese": [],
                "ricorrenze": {},
                "budget_categorie": {},
                "_window_geometry": None
            }
            self.categorie = self.db["categorie"]
            self.categorie_tipi = self.db["categorie_tipi"]
            self.spese = {}
            self.ricalcola_operazioni_web()
            self.ricorrenze = self.db["ricorrenze"]
            self.budget_categorie = self.db["budget_categorie"]
            self._window_geometry = self.db["_window_geometry"]
            return
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                self.db = json.load(f)
            self.categorie = self.db.get("categorie", ["Generica"])
            self.categorie_tipi = self.db.get("categorie_tipi", {"Generica": "Uscita"})
            self.spese = {}
            for obj in self.db.get("spese", []):
                d = datetime.datetime.strptime(obj["date"], "%d-%m-%Y").date()
                entries = []
                for e in obj.get("entries", []):
                    entries.append(SpesaEntry.da_dict(e))
                self.spese[d] = entries
            self.ricorrenze = self.db.get("ricorrenze", {})
            self.budget_categorie = self.db.get("budget_categorie", {})
            self._window_geometry = self.db.get("_window_geometry", None)
            self.ricalcola_operazioni_web()
        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore critico caricamento DB:", e)
            bak_file = DB_FILE + ".bak"
            if os.path.exists(bak_file):
                domanda_bak = (
                    f"Il database principale è illeggibile ({e}).\n\n"
                    "È stato trovato un file di backup (.bak) dell'ultima sessione valida.\n"
                    "Vuoi tentare il ripristino automatico dei dati?"
                )
                style = ttk.Style()
                self.COLOR_RED = "#e06c75"
                style.configure("Giallo.TButton", background="#E5C07B", foreground="black", font=("Arial", 8, "bold"))
                style.map("Giallo.TButton", background=[("pressed", "#B89B62"), ("active", "#CFB076")])
                style.configure("Verde.TButton", background="green", foreground="black", font=("Arial", 8, "bold"))
                style.map("Verde.TButton", background=[("pressed", "#7A9A5F"), ("active", "#8AAB6F")], foreground=[('disabled', "yellow")])
                if self.show_custom_askyesno("Recupero Database", domanda_bak):
                    try:
                        import shutil
                        os.replace(DB_FILE, DB_FILE + ".corrotto") 
                        shutil.copy2(bak_file, DB_FILE)
                        migrazione_emoji_ok = True
                        try:
                            from moduli.migrazione_emoji_dati import migra_emoji_nei_dati
                            migra_emoji_nei_dati([(DB_FILE, 2)])
                        except Exception as _e:
                            migrazione_emoji_ok = False
                            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Migrazione emoji dati (ripristino .bak) fallita: {_e}")
                        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Ripristino completato dal file .bak")
                        risultato = self.load_db()
                        if not migrazione_emoji_ok:
                            self.show_custom_warning(
                                "Attenzione",
                                "Database ripristinato dal backup .bak, ma la migrazione emoji→testo non è riuscita.\n"
                                "Alcuni dati potrebbero restare nel vecchio formato. Riavvia l'app: "
                                "la migrazione viene ritentata automaticamente ad ogni avvio."
                            )
                        return risultato
                    except Exception as err_bak:
                        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Ripristino fallito: {err_bak}")
            self.db = {"categorie": ["Generica"], "categorie_tipi": {"Generica": "Uscita"}, "spese": [], "ricorrenze": {}, "budget_categorie": {}, "_window_geometry": None}
            CATEGORIA_PRIORITARIA = "Generica"
            cat_raw = self.db.get("categorie", ["Generica"])
            self.categorie = (
                [CATEGORIA_PRIORITARIA] if CATEGORIA_PRIORITARIA in cat_raw else []
            ) + sorted([c for c in cat_raw if c != CATEGORIA_PRIORITARIA], key=lambda c: c.lower())

            self.categorie_tipi = dict(
                sorted(self.db.get("categorie_tipi", {"Generica": "Uscita"}).items(), key=lambda x: x[0].lower())
            )
            self.spese = {}
            self.ricorrenze = {}
            self.budget_categorie = {}
            self._window_geometry = None
            self.ricalcola_operazioni_web()
            msg_errore = (
                f"ATTENZIONE: Il database ({DB_FILE}) è corrotto.\n\n"
                f"Dettaglio: {e}\n\n"
                "Il programma è stato avviato con un database vuoto.\n"
                "Puoi importare un backup manualmente dal menu Opzioni."
            )
            self.show_custom_warning("Attenzione", msg_errore)

    def _chiave_tag(self, data, cat, desc, imp):
        return f"{data.strftime('%d-%m-%Y')}|{cat}|{desc}|{imp}"
    def _normalizza_tags(self, testo):
        tag_list = [t.strip().lstrip("#") for t in testo.replace(",", " ").split() if t.strip()]
        return [f"#{t}" for t in tag_list if t]

    def _entry_a_dict(self, entry):
        if isinstance(entry, SpesaEntry):
            return entry.a_dict()
        c, desc, imp, tipo, *rest = entry
        d = {"categoria": c, "descrizione": desc, "importo": imp, "tipo": tipo}
        if rest:
            d["id_ricorrenza"] = rest[0]
        return d

    # Salvataggio del database JSON e dei dati applicativi
    def save_db(self):
        self.config(cursor="watch")
        self.update_idletasks()
        try:
            with self.save_lock:
                limite = datetime.date.today() - datetime.timedelta(days=365 * ANNI_DA_MANTENERE)
                spese_da_rimuovere = [d for d in self.spese.keys() if d < limite]
                if spese_da_rimuovere:
                    if os.path.exists(DB_FILE):
                        cartella_storico = os.path.join(os.path.dirname(os.path.abspath(DB_FILE)), "storico")
                        try:
                            if not os.path.exists(cartella_storico):
                                os.makedirs(cartella_storico)
                            timestamp = datetime.datetime.now().strftime("%d%m%Y_%H%M")
                            nome_base = os.path.basename(DB_FILE)
                            backup_storico = os.path.join(cartella_storico, f"{nome_base}_{timestamp}.storico")
                            shutil.copy2(DB_FILE, backup_storico)
                            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ARCHIVIAZIONE: Backup creato in /storico/{os.path.basename(backup_storico)}")
                            lista_storici = sorted([
                                os.path.join(cartella_storico, f) for f in os.listdir(cartella_storico) 
                                if f.endswith(".storico")
                            ], key=os.path.getmtime)
                            while len(lista_storici) > 2:
                                vecchio = lista_storici.pop(0) 
                                os.remove(vecchio)
                                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ROTAZIONE: Rimosso archivio datato: {os.path.basename(vecchio)}")
                        except Exception as e:
                            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore durante l'archiviazione: {e}")
                    else:
                        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Primo salvataggio: DB_FILE non ancora presente, salto creazione storico.")
                    conteggio_giorni = len(spese_da_rimuovere)
                    for d in spese_da_rimuovere:
                        del self.spese[d]
                    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] PULIZIA: Rimosse {conteggio_giorni} giornate di dati antecedenti al {limite.strftime('%d-%m-%Y')}.")
                categorie_tipi_ordinati = dict(sorted(self.categorie_tipi.items(), key=lambda x: x[0].lower()))
                CATEGORIA_PRIORITARIA = "Generica"
                categorie_temporanee = sorted([c for c in self.categorie if c != CATEGORIA_PRIORITARIA], key=lambda c: c.lower())
                categorie_ordinate = ([CATEGORIA_PRIORITARIA] if CATEGORIA_PRIORITARIA in self.categorie else []) + categorie_temporanee
                data = {
                    "categorie": categorie_ordinate,
                    "categorie_tipi": categorie_tipi_ordinati,
                    "spese": [
                        {"date": d.strftime("%d-%m-%Y"), "entries": [
                            self._entry_a_dict(entry) for entry in sp
                        ]} for d, sp in sorted(self.spese.items())
                    ],
                    "ricorrenze": self.ricorrenze,
                    "budget_categorie": self.budget_categorie,
                    "_window_geometry": self._window_geometry or (self.geometry() if hasattr(self, 'geometry') else None)
                }
                if os.path.exists(DB_FILE):
                    shutil.copy2(DB_FILE, DB_FILE + ".bak")
                temp_file = DB_FILE + ".tmp"
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(temp_file, DB_FILE)
                self.ricalcola_operazioni_web()
                with open(MEM_CAT, "w", encoding="utf-8") as f:
                    json.dump(self.memoria_descrizioni_categoria, f, indent=2, ensure_ascii=False)
                if DB_CONDIVISO:
                    self.notifica_modifica_web()
                    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Notifica di aggiornamento inviata e backup .bak creato.")
                self._controlla_sforamento_budget()
        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}]Errore critico durante il salvataggio: {e}")
        finally:
            self.config(cursor="")
             
    # Controlla se qualche categoria con budget impostato ha superato il limite nel mese corrente
    def _controlla_sforamento_budget(self, mostra_toast=True):
        if not hasattr(self, 'budget_categorie') or not self.budget_categorie:
            return
        if not hasattr(self, 'show_toast'):
            return
        oggi = datetime.date.today()
        totali = {}
        for data_reg, voci in self.spese.items():
            if data_reg.year == oggi.year and data_reg.month == oggi.month:
                for v in voci:
                    if len(v) >= 4 and v[3] == "Uscita":
                        cat = v[0]
                        try:
                            totali[cat] = totali.get(cat, 0.0) + float(v[2])
                        except (ValueError, TypeError):
                            pass
        if not hasattr(self, '_budget_sforati_mese'):
            self._budget_sforati_mese = (oggi.year, oggi.month)
            self._budget_sforati = set()
        elif self._budget_sforati_mese != (oggi.year, oggi.month):
            self._budget_sforati_mese = (oggi.year, oggi.month)
            self._budget_sforati = set()
        categorie_in_sforamento = []
        for cat, budget in self.budget_categorie.items():
            if budget and budget > 0:
                tot = totali.get(cat, 0.0)
                if tot > budget:
                    categorie_in_sforamento.append(cat)
                    if cat not in self._budget_sforati:
                        self._budget_sforati.add(cat)
                        if mostra_toast:
                            self.show_toast(f"Budget '{cat}' superato: €{tot:.2f} / €{budget:.2f}")
                else:
                    self._budget_sforati.discard(cat)
        if hasattr(self, 'lbl_budget_cat_sforati'):
            n = len(categorie_in_sforamento)
            if n > 0:
                self.lbl_budget_cat_sforati.config(text=f"{n} Categori{'a' if n == 1 else 'e'} oltre soglia")
            else:
                self.lbl_budget_cat_sforati.config(text="")
            self._tt_budget_sforati_txt = "\n".join(
                f"{c}: €{totali.get(c, 0.0):.2f} / €{self.budget_categorie.get(c, 0):.2f}"
                for c in sorted(categorie_in_sforamento)
            ) if categorie_in_sforamento else "Nessuna categoria oltre soglia"

    # Ripristino dello stato predefinito del modulo di inserimento spesa
    def reset_form(self):
        if self.modifica_idx is not None:
            return
        today = datetime.date.today()
        self.data_spesa_var.set(today.strftime("%d-%m-%Y"))
        self.desc_entry.delete(0, tk.END)
        self.imp_entry.delete(0, tk.END)
        self.blocca_data_var.set(False)
        self.metodo_pagamento_var.set("")
        if hasattr(self, 'tag_entry'):
            self.tag_entry.delete(0, tk.END)
        self.cat_sel.set(self.categorie[0])
        self.cat_filter_entry.delete(0, tk.END)
        self.cat_filter_entry.config(foreground=self.TEXT_COLOR)
        self.suggerimenti_attivi = True
        self.categoria_bloccata = False 
        self.on_categoria_changed(manuale=False) 
        self.btn_aggiungi["state"] = tk.NORMAL
        self.after(0, self.imp_entry.focus_set)
    
    # Toggle tra tipo 'Entrata' e 'Uscita' con aggiornamento visivo
    def toggle_tipo_spesa(self):
        v = self.tipo_spesa_var.get()
        nuovo = "Entrata" if v == "Uscita" else "Uscita"
        self.tipo_spesa_var.set(nuovo)
        self.btn_tipo_spesa.config(text=nuovo)
        new_style = 'GreenOutline.TButton' if nuovo == "Entrata" else 'RedOutline.TButton'
        self.btn_tipo_spesa.config(style=new_style)

    # Ripristino del campo Data Spesa alla data odierna
    def reset_data_spesa(self):
        today = datetime.date.today()
        self.data_spesa_var.set(today.strftime("%d-%m-%Y"))
        
    # Ripristino della Data di Inizio Ricorrenza alla data
    def reset_ric_data_inizio(self):
        oggi = datetime.date.today()
        self.ricorrenza_data_inizio.set(oggi.strftime("%d-%m-%Y"))

    # Programmazione e Registrazione di Transazioni Ricorrenti (Ricorrenza)
    def add_ricorrenza(self, event=None):
        self.mostra_treeview_statistiche()
        self.after(0, self.imp_entry.focus_set)
        ric_type = self.ricorrenza_tipo.get()
        if ric_type == "Nessuna":
            self.show_toast("Errore: Seleziona un tipo di ricorrenza valido.")
            return
        try:
            n = int(self.ricorrenza_n.get())
            if n <= 0 or n > 365:
                raise ValueError
        except Exception:
            self.show_toast("Errore: Numero ripetizioni non valido (1-365).")
            return
        try:
            data_inizio = datetime.datetime.strptime(self.ricorrenza_data_inizio.get(), "%d-%m-%Y").date()
        except Exception:
            self.show_custom_warning("Errore", "Data inizio ricorrenza non valida")
            return
        cat = self.ricorrenza_cat_sel.get()
        desc = self.ricorrenza_desc.get().strip()
        if not cat or cat.strip() == "" or cat == "Categoria Rimossa" or cat not in self.categorie:
            self.ricorrenza_cat_sel.set("Generica")
            self.ric_cat_menu.focus_set()
            self.show_custom_warning("Categoria Riservata", 
                "Questa categoria non permette inserimenti.\n"
                "Il sistema ha impostato 'Generica'. Seleziona un'altra voce se necessario.")
            return 
        try:
            imp_str = self.ricorrenza_imp.get().replace(",", ".")
            imp = float(imp_str)
            if imp <= 0:
                self.show_toast("Errore: L'importo non può essere negativo.")
                return
        except Exception:
            self.show_toast("Errore: Importo mancante o non valido.")
            return
        tipo = self.ricorrenza_tipo_voce.get()
        ric_id = str(uuid.uuid4())
        id_visibile = ric_id[:8]
        simbolo_ricorrenza = "RIC·"
        if desc:
                desc = f"{simbolo_ricorrenza} {desc} ID:{id_visibile}"
        else:
                desc = f"{simbolo_ricorrenza} ID:{id_visibile}"
        date_list = []
        for i in range(n):
            if ric_type == "Ogni giorno":
                d = data_inizio + datetime.timedelta(days=i)
            elif ric_type == "Ogni mese":
                month = (data_inizio.month - 1 + i) % 12 + 1
                year = data_inizio.year + (data_inizio.month - 1 + i) // 12
                day = min(data_inizio.day, [31,
                    29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                    31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
                try:
                    d = datetime.date(year, month, day)
                except Exception:
                    d = datetime.date(year, month, 1)
            elif ric_type == "Ogni anno":
                year = data_inizio.year + i
                try:
                    d = datetime.date(year, data_inizio.month, data_inizio.day)
                except Exception:
                    d = datetime.date(year, data_inizio.month, 1)
            else:
                break
            date_list.append(d)
        _tags_ric = self._normalizza_tags(self.ricorrenza_tag.get()) if hasattr(self, 'ricorrenza_tag') else []
        _nome_c_ric = self.v_conto_movimento.get() if hasattr(self, 'v_conto_movimento') else "(nessuno)"
        _conto_ric = _nome_c_ric if _nome_c_ric and _nome_c_ric != "(nessuno)" else ""
        _metodo_ric = self._metodo_pagamento_pulito(self.ricorrenza_metodo.get()) if hasattr(self, 'ricorrenza_metodo') else ""
        for d in date_list:
            if d not in self.spese:
                self.spese[d] = []
            self.spese[d].append(SpesaEntry.nuova(cat, desc, imp, tipo, hashtag=list(_tags_ric), conto=_conto_ric, id_ricorrenza=ric_id, metodo_pagamento=_metodo_ric))
        self.ricorrenze[ric_id] = {
            "tipo": ric_type,
            "n": n,
            "data_inizio": data_inizio.strftime("%d-%m-%Y"),
            "cat": cat,
            "desc": desc,
            "imp": imp,
            "tipo_voce": tipo,
            "conto": _conto_ric,
            "metodo_pagamento": _metodo_ric,
            "hashtag": list(_tags_ric),
            "date_list": [d.strftime("%d-%m-%Y") for d in date_list]
        }
        self.save_db()
        self.refresh_gui()
        self.riproduci_beep()
        self.show_custom_info("Ricorrenza Programmata", f"Sono state generate e registrate {n} nuove transazioni future in base alla ricorrenza definita.")
        oggi = datetime.date.today().strftime("%d-%m-%Y")
        self.importo_ricorrenza.set("")
        self.ricorrenza_tipo.set("Nessuna")
        self.ricorrenza_n.set(1)
        self.ricorrenza_data_inizio.set(oggi)
        self.ricorrenza_cat_sel.set(self.categorie[0])
        self.ricorrenza_desc.set("")
        self.ricorrenza_imp.set("")
        self.ricorrenza_tipo_voce.set("Uscita")
        if hasattr(self, 'ricorrenza_metodo'):
            self.ricorrenza_metodo.set("")
        if hasattr(self, 'ricorrenza_tag'):
            self.ricorrenza_tag.set("")
        self.btn_tipo_voce.configure(
            text="Uscita", 
            style="RedOutline.TButton"
        )

    # Gestore dell'Inserimento di una Singola Transazione
    def add_spesa(self, event=None):
        if self.modifica_idx is not None:
            return
        self.after(0, self.imp_entry.focus_set)
        if hasattr(self, 'ricorrenza_tipo') and self.ricorrenza_tipo.get() != "Nessuna":
            self.add_ricorrenza()
            return
        data = self.data_spesa_var.get()
        cat = self.cat_sel.get()
        desc = self.desc_entry.get().strip()
        if not cat or cat.strip() == "" or cat == "Categoria Rimossa" or cat not in self.categorie:
            self.cat_sel.set("Generica")
            self.cat_menu.focus_set()
            self.show_custom_warning("Categoria Riservata", 
                "Questa categoria non permette inserimenti.\n"
                "Il sistema ha impostato 'Generica'. Seleziona un'altra voce se necessario.")
            return           
        try:
            imp = float(self.imp_entry.get().replace(",", "."))
        except ValueError:
            self.show_toast("Errore: Importo mancante o non valido.")
            return
        tipo = self.tipo_spesa_var.get()
        try:
            d = datetime.datetime.strptime(data, "%d-%m-%Y").date()
        except ValueError:
            self.show_custom_warning("Errore", "Formato data non valido.")
            return           
        if self.CHECK_DOPPI_MOV: 
            mese_target = d.month
            anno_target = d.year
            for data_registrata, lista_voci in self.spese.items():
                if data_registrata.month == mese_target and data_registrata.year == anno_target:
                    for s in lista_voci:
                        if s[0] == cat and s[2] == imp and s[3] == tipo:
                            data_str = data_registrata.strftime("%d-%m-%Y")
                            risposta = self.show_custom_askyesno("Duplicato Mensile", 
                                f"Attenzione: esiste già un movimento identico in data {data_str}.\n"
                                f"Vuoi procedere comunque?")
                            if not risposta:
                                return
        if d not in self.spese:
            self.spese[d] = []
        _tags = self._normalizza_tags(self.tag_entry.get()) if hasattr(self, 'tag_entry') else []
        _nome_c = self.v_conto_movimento.get() if hasattr(self, 'v_conto_movimento') else "(nessuno)"
        _conto_per_voce = _nome_c if _nome_c and _nome_c != "(nessuno)" else ""
        _metodo_per_voce = self._metodo_pagamento_pulito(self.metodo_pagamento_var.get()) if hasattr(self, 'metodo_pagamento_var') else ""
        self.spese[d].append(SpesaEntry.nuova(cat, desc, imp, tipo, hashtag=_tags, conto=_conto_per_voce, metodo_pagamento=_metodo_per_voce))
        if _tags and hasattr(self, '_cache_tutti_tag'):
            del self._cache_tutti_tag
        self.tag_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.imp_entry.delete(0, tk.END)
        self.save_db()
        self.mostra_treeview_statistiche()
        self.goto_today() if d == datetime.date.today() else None
        self.reset_modifica_form()
        self.refresh_gui()
        self.riproduci_beep()
        if not self.blocca_data_var.get():
            self.data_spesa_var.set(datetime.date.today().strftime("%d-%m-%Y"))
        self.categoria_bloccata = False
        self.label_smartcat.config(text="💡 SmartCat On", foreground="red")
        self.metodo_pagamento_var.set("")
        if hasattr(self, 'v_conto_movimento'):
            try:
                with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _f:
                    _db_reset = json.load(_f)
                _principale_reset = next(
                    (c.get("nome", "") for c in _db_reset.get("conti", []) if c.get("principale")),
                    "(nessuno)"
                )
            except Exception:
                _principale_reset = "(nessuno)"
            self.v_conto_movimento.set(_principale_reset)
        def destroy_window_and_cleanup():
            if hasattr(self, 'lista_window_ref') and self.lista_window_ref.winfo_exists():
                self.lista_window_ref.destroy() 
                delattr(self, 'lista_window_ref')
            self.refresh_gui() 
            self.ricorrenza_cat_sel.set(self.categorie[0]) 
            self.ricorrenza_tipo_voce.set("Uscita")
            self.btn_tipo_voce.configure(
                text="Uscita", 
                style="RedOutline.TButton"
            )
        
    # Abilita/Disabilita l'interazione con il pulsante Tipo Transazione    
    def set_tipo_spesa_editable(self, editable=True):
        if editable:
            self.btn_tipo_spesa.state(["!disabled"])
        else:
            self.btn_tipo_spesa.state(["disabled"])
            
    # Inserimento forzato del valore Importo (bypassando la validazione)
    def _inserisci_importo_senza_validazione(self, imp_value):
        self.imp_entry.config(validate="none") 
        self.imp_entry.delete(0, tk.END)
        self.imp_entry.insert(0, imp_value)
        vcmd = self.imp_entry.cget('validatecommand')
        self.imp_entry.config(validate="key", validatecommand=vcmd)

    # Popola il form di modifica con la voce selezionata nella tabella, equivalente al click sulla colonna Modifica
    def avvia_modifica_da_selezione(self):
        if getattr(self, '_form_collapsed', False):
            self.show_toast("Apri il pannello inserimento per modificare.")
            return
        if len(self.stats_table.selection()) > 1:
            self.show_toast("Modifica disponibile solo per selezione singola.")
            return
        if self.stats_mode.get() != "giorno":
            return
        sel = self.stats_table.selection()
        if not sel:
            return
        rowid = sel[0]
        vals = self.stats_table.item(rowid, "values")
        if len(vals) < 6:
            return
        giorno_str, cat, desc, imp, tipo, _ = vals
        giorno = datetime.datetime.strptime(giorno_str, "%d-%m-%Y").date()
        idx = self._idx_reale_da_riga(rowid)
        voce = self.spese[giorno][idx]
        self.label_smartcat.config(text="💡 SmartCat Off", foreground="green")
        self.aggiorna_bottone_spese_simili(visibile=False)
        self.suggerimenti_attivi = False
        self.modifica_idx = (giorno, idx)
        self.cat_sel.set(cat)
        self.desc_entry.delete(0, tk.END)
        self.desc_entry.config(validate="none")
        self.desc_entry.insert(0, desc[:35])
        self.desc_entry.config(validate="key")
        self.imp_entry.delete(0, tk.END)
        self.imp_entry.insert(0, imp)
        self.after(0, lambda: self._inserisci_importo_senza_validazione(imp))
        self.tipo_spesa_var.set(tipo)
        self.btn_tipo_spesa.config(text=tipo)
        self.data_spesa_var.set(giorno.strftime("%d-%m-%Y"))
        self.btn_modifica.config(cursor="hand2")
        self.btn_aggiungi.config(cursor="X_cursor")
        self.btn_cancella.config(cursor="hand2")
        self.btn_modifica_sel.config(cursor="X_cursor")
        self.btn_reset_form.config(cursor="X_cursor")
        self.btn_annulla_modifica.config(cursor="hand2")
        self.set_tipo_spesa_editable(True)
        new_style = 'GreenOutline.TButton' if tipo == "Entrata" else 'RedOutline.TButton'
        self.btn_tipo_spesa.config(style=new_style)
        if hasattr(self, 'v_conto_movimento'):
            self.v_conto_movimento.set(campo(voce, "conto", "") or self._trova_conto_da_portafoglio(giorno, float(imp), tipo, self._ordine_in_gruppo_chiave(giorno, idx)))
        if hasattr(self, 'metodo_pagamento_var'):
            self.metodo_pagamento_var.set(self._metodo_pagamento_a_combo(campo(voce, "metodo_pagamento", "")))
        if hasattr(self, 'tag_entry'):
            self.tag_entry.delete(0, tk.END)
            _tags = campo(voce, "hashtag", [])
            self.tag_entry.insert(0, " ".join(_tags))
        if len(voce) == 5:
            ric_id = voce[4]
            if ric_id in self.ricorrenze:
                ric = self.ricorrenze[ric_id]
                self.show_custom_info(
                    "Voce ricorrente",
                    f"Questa voce è parte di una ricorrenza: {ric['tipo']} x{ric['n']} da {ric['data_inizio']}.\n"
                    "Puoi cancellare tutta la ricorrenza dal pannello Ricorrenze sotto.\n"
                    "In alternativa puoi modificare la singola voce o cancellarla"
                )
            
    # Caricamento Voce di Spesa nel Modulo (Preparazione per Modifica/Cancellazione)
    def on_table_click(self, event):
        self.label_smartcat.config(text="💡 SmartCat Off", foreground="green")
        self.aggiorna_bottone_spese_simili(visibile=False)
        mode = self.stats_mode.get()            
        if mode != "giorno":
            return
        region = self.stats_table.identify("region", event.x, event.y)
        if region != "cell":
            return
        if self.stats_table.selection():
            self.btn_modifica_sel.config(cursor="hand2")
        else:
            self.btn_modifica_sel.config(cursor="X_cursor")
        col = self.stats_table.identify_column(event.x)
        if col != "#6":
            return
        if getattr(self, '_form_collapsed', False):
            self.show_toast("Apri il pannello inserimento per modificare.")
            return
        self.suggerimenti_attivi = False 
        rowid = self.stats_table.identify_row(event.y)
        if not rowid:
            return
        vals = self.stats_table.item(rowid, "values")
        giorno_str, cat, desc, imp, tipo, _ = vals
        giorno = datetime.datetime.strptime(giorno_str, "%d-%m-%Y").date()
        idx = self._idx_reale_da_riga(rowid)
        voce = self.spese[giorno][idx]
        self.modifica_idx = (giorno, idx)
        self.cat_sel.set(cat)
        self.desc_entry.delete(0, tk.END)
        self.desc_entry.config(validate="none")
        self.desc_entry.insert(0, desc[:35])
        self.desc_entry.config(validate="key")
        self.imp_entry.delete(0, tk.END)
        self.imp_entry.insert(0, imp)
        self.after(0, lambda: self._inserisci_importo_senza_validazione(imp))
        self.tipo_spesa_var.set(tipo)
        self.btn_tipo_spesa.config(text=tipo)
        self.data_spesa_var.set(giorno.strftime("%d-%m-%Y"))
        self.btn_modifica.config(cursor="hand2")
        self.btn_aggiungi.config(cursor="X_cursor")
        self.btn_cancella.config(cursor="hand2")
        self.btn_reset_form.config(cursor="X_cursor")
        self.btn_modifica_sel.config(cursor="X_cursor")
        self.btn_annulla_modifica.config(cursor="hand2")
        self.set_tipo_spesa_editable(True) 
        new_style = 'GreenOutline.TButton' if tipo == "Entrata" else 'RedOutline.TButton'
        self.btn_tipo_spesa.config(style=new_style)
        if hasattr(self, 'v_conto_movimento'):
            self.v_conto_movimento.set(campo(voce, "conto", "") or self._trova_conto_da_portafoglio(giorno, float(imp), tipo, self._ordine_in_gruppo_chiave(giorno, idx)))
        if hasattr(self, 'metodo_pagamento_var'):
            self.metodo_pagamento_var.set(self._metodo_pagamento_a_combo(campo(voce, "metodo_pagamento", "")))
        if hasattr(self, 'tag_entry'):
            self.tag_entry.delete(0, tk.END)
            _tags = campo(voce, "hashtag", [])
            self.tag_entry.insert(0, " ".join(_tags))
        if len(voce) == 5:
            ric_id = voce[4]
            if ric_id in self.ricorrenze:
                ric = self.ricorrenze[ric_id]
                self.show_custom_info(
                    "Voce ricorrente", 
                    f"Questa voce è parte di una ricorrenza: {ric['tipo']} x{ric['n']} da {ric['data_inizio']}.\n"
                    "Puoi cancellare tutta la ricorrenza dal pannello Ricorrenze sotto.\n"
                    "In alternativa puoi modificare la singola voce o cancellarla"
                )
                
    # Sincronizzazione visiva (colore/testo) del pulsante Tipo Spesa
    def aggiorna_stile_tipo_spesa(self):
        tipo = self.tipo_spesa_var.get()
        btn_style = 'GreenOutline.TButton' if tipo == "Entrata" else 'RedOutline.TButton'
        self.btn_tipo_spesa.config(
            text=tipo,
            style=btn_style
        )
        
    # Gestione delle Transazioni Esistenti (Modifica e Cancellazione di Singole Voci)
    def reset_modifica_form(self):
        self.suggerimenti_attivi = True  
        self.label_smartcat.config(text="💡 SmartCat On", foreground="red")
        self.modifica_idx = None
        self.btn_modifica.config(cursor="X_cursor")
        self.btn_aggiungi.config(cursor="hand2")
        self.btn_cancella.config(cursor="X_cursor")
        self.btn_reset_form.config(cursor="hand2")
        self.btn_annulla_modifica.config(cursor="X_cursor")
        self.desc_entry.delete(0, tk.END)
        self.imp_entry.delete(0, tk.END)
        self.cat_sel.set("Generica")
        self.metodo_pagamento_var.set("")
        self.on_categoria_changed()
        self.set_tipo_spesa_editable(True)
        if not self.blocca_data_var.get():
            self.data_spesa_var.set(datetime.date.today().strftime("%d-%m-%Y"))
        self.categoria_bloccata = False
        if hasattr(self, 'btn_modifica_sel'):
            self.btn_modifica_sel.config(cursor="X_cursor")
        if hasattr(self, 'v_conto_movimento'):
            try:
                with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _f:
                    _db_reset = json.load(_f)
                _principale_reset = next(
                    (c.get("nome", "") for c in _db_reset.get("conti", []) if c.get("principale")),
                    "(nessuno)"
                )
            except Exception:
                _principale_reset = "(nessuno)"
            self.v_conto_movimento.set(_principale_reset)
        if hasattr(self, 'tag_entry'):
            self.tag_entry.delete(0, tk.END)
                
    def _idx_reale_da_riga(self, rowid):
        try:
            for _tg in self.stats_table.item(rowid, "tags"):
                if "|" in _tg:
                    _gg, _ii = _tg.rsplit("|", 1)
                    return int(_ii)
        except Exception:
            pass
        return self.stats_table.index(rowid)

    def _ordine_in_gruppo_chiave(self, giorno, idx):
        lista = self.spese.get(giorno, [])
        if idx >= len(lista):
            return 0
        corrente = lista[idx]
        imp_c, tipo_c = round(float(corrente[2]), 2), corrente[3]
        conteggio = 0
        for i in range(idx):
            v = lista[i]
            if round(float(v[2]), 2) == imp_c and v[3] == tipo_c:
                conteggio += 1
        return conteggio

    def _trova_conto_da_portafoglio(self, data, imp, tipo, ordinale=0):
        try:
            with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _f:
                _db_p = json.load(_f)
            data_s = data.strftime("%d-%m-%Y")
            id_to_nome = {c["id"]: c.get("nome", "?") for c in _db_p.get("conti", [])}
            candidati = []
            for t in _db_p.get("trasferimenti", []):
                if t.get("data") == data_s and abs(float(t.get("importo", 0)) - imp) < 0.01:
                    if tipo == "Uscita" and t.get("a") in ("__spese__", "Contabilità"):
                        candidati.append(t)
                    elif tipo == "Entrata" and t.get("da") in ("__spese__", "Contabilità"):
                        candidati.append(t)
            if not candidati:
                return "(nessuno)"
            if ordinale >= len(candidati):
                return "(nessuno)"
            t = candidati[ordinale]
            if tipo == "Uscita":
                return id_to_nome.get(t.get("da"), "(nessuno)")
            else:
                return id_to_nome.get(t.get("a"), "(nessuno)")
        except Exception:
            pass
        return "(nessuno)"

    def salva_modifica(self):
        if not self.modifica_idx:
            return
        old_dt, idx = self.modifica_idx
        new_data = self.data_spesa_var.get()
        new_dt = datetime.datetime.strptime(new_data, "%d-%m-%Y").date()
        cat = self.cat_sel.get()
        desc = self.desc_entry.get().strip()
        try:
            imp = float(self.imp_entry.get().replace(",", "."))
        except Exception:
            self.show_toast("Errore: Importo mancante o non valido.")
            return
        tipo = self.tipo_spesa_var.get()
        if old_dt not in self.spese or idx >= len(self.spese[old_dt]):
            self.show_custom_warning("Errore", "La voce selezionata non esiste più.")
            self.reset_modifica_form()
            return
        voce_old = self.spese[old_dt][idx]
        id_ric = voce_old[4] if len(voce_old) == 5 else None
        if "ALL·" in str(voce_old[1]):
            if self.show_custom_askyesno("Documento Allegato", "Aggiornare anche il registro?"):
                try:
                    if os.path.exists(REGISTRY_FILE):
                        with open(REGISTRY_FILE, 'r', encoding='utf-8') as f: r = json.load(f)
                        o_s, o_i, o_t = old_dt.strftime("%d%m%Y"), str(int(round(float(voce_old[2])*100))), voce_old[3]
                        d_p = desc.replace("ALL·", "").strip()
                        def _sn(s, n=None):
                            s = re.sub(r'[^\w\.-]', '', s.strip().replace(' ', '_'))
                            return (s[:n] if n else s).upper()
                        n_s, n_i = new_dt.strftime("%d%m%Y"), str(int(round(imp*100)))
                        n_f = f"{n_s}_{_sn(d_p,30)}_{tipo}_{_sn(cat,20)}_{n_i}.pdf"
                        ok = False
                        for f_k in list(r.keys()):
                            if f_k.startswith(o_s) and o_i in f_k and o_t in f_k:
                                o_p, n_p = os.path.join(DOC_DIR, f_k), os.path.join(DOC_DIR, n_f)
                                if f_k != n_f and os.path.exists(o_p):
                                    os.rename(o_p, n_p)
                                    val = r.pop(f_k)
                                else: val = r[f_k]
                                val.update({'data_raw':n_s, 'categoria_esatta':cat, 'descrizione_esatta':f"ALL· {d_p}", 'importo_raw':int(n_i), 'tipo_esatto':tipo})
                                r[n_f], ok = val, True
                                break 
                        if ok:
                            with open(REGISTRY_FILE, 'w', encoding='utf-8') as f: json.dump(r, f, indent=4, ensure_ascii=False)
                except Exception as e: self.show_custom_warning("Errore", f"Registro non aggiornato: {e}")
        del self.spese[old_dt][idx]
        if not self.spese[old_dt]:
            del self.spese[old_dt]
        if new_dt not in self.spese:
            self.spese[new_dt] = []
        _tags = self._normalizza_tags(self.tag_entry.get()) if hasattr(self, 'tag_entry') else []
        _nome_c = self.v_conto_movimento.get() if hasattr(self, 'v_conto_movimento') else "(nessuno)"
        _conto_nuovo = _nome_c if _nome_c and _nome_c != "(nessuno)" else ""
        _metodo_nuovo = self._metodo_pagamento_pulito(self.metodo_pagamento_var.get()) if hasattr(self, 'metodo_pagamento_var') else campo(voce_old, "metodo_pagamento", "")
        voce_new = SpesaEntry(
            cat, desc, imp, tipo,
            id_ricorrenza=id_ric,
            id_spesa=campo(voce_old, "id_spesa", None),
            conto=_conto_nuovo,
            ora=campo(voce_old, "ora", ""),
            metodo_pagamento=_metodo_nuovo,
            hashtag=_tags,
        )
        self.spese[new_dt].append(voce_new)
        if hasattr(self, '_cache_tutti_tag'):
                del self._cache_tutti_tag
        if hasattr(self, 'tag_entry'):
            self.tag_entry.delete(0, tk.END)
        self.save_db()
        if hasattr(self, '_saldo_popup') and self._saldo_popup and self._saldo_popup.winfo_exists():
            self._saldo_refresh() if hasattr(self, "_saldo_refresh") else None
            self._saldo_refresh_movimenti() if hasattr(self, "_saldo_refresh_movimenti") else None
        self.refresh_gui()
        self.reset_modifica_form()
        self.suggerimenti_attivi = True
        self.btn_aggiungi["state"] = tk.NORMAL
    
    def cancella_voce(self):
        if not self.modifica_idx: return
        old_dt, idx = self.modifica_idx
        if old_dt in self.spese and 0 <= idx < len(self.spese[old_dt]):
            voce_old = self.spese[old_dt][idx]
            if "ALL·" in str(voce_old[1]):
                if self.show_custom_askyesno("Elimina Allegato", "Vuoi eliminare anche il file PDF?"):
                    try:
                        if os.path.exists(REGISTRY_FILE):
                            with open(REGISTRY_FILE, 'r', encoding='utf-8') as f: r = json.load(f)
                            o_s = old_dt.strftime("%d%m%Y")
                            o_i = str(int(round(float(str(voce_old[2]).replace(',','.'))*100)))
                            o_t = voce_old[3]
                            ok = False
                            for f_k in list(r.keys()):
                                if f_k.startswith(o_s) and o_i in f_k and o_t in f_k:
                                    o_p = os.path.join(DOC_DIR, f_k)
                                    if os.path.exists(o_p): os.remove(o_p)
                                    r.pop(f_k)
                                    ok = True
                                    break
                            if ok:
                                with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
                                    json.dump(r, f, indent=4, ensure_ascii=False)
                    except Exception as e: self.show_custom_warning("Errore", f"Registro: {e}")
            del self.spese[old_dt][idx]
            if hasattr(self, '_cache_tutti_tag'):
                del self._cache_tutti_tag
            if not self.spese[old_dt]: del self.spese[old_dt]
            self.save_db()
            if hasattr(self, '_saldo_popup') and self._saldo_popup and self._saldo_popup.winfo_exists():
                self._saldo_refresh() if hasattr(self, "_saldo_refresh") else None
                self._saldo_refresh_movimenti() if hasattr(self, "_saldo_refresh_movimenti") else None
            self.refresh_gui()
        self.reset_modifica_form()
        self.colora_giorni_spese()
        self.suggerimenti_attivi = True
        self.btn_aggiungi["state"] = tk.NORMAL
        
    def refresh_documenti(self):        
        if hasattr(self, 'pdf_window') and self.pdf_window.winfo_exists():
                tabella = getattr(self, 'tabella_documenti', None)
                funzione_load = getattr(self, 'funzione_carica_documenti', None)
                if tabella and funzione_load:
                    self.filtri_avanzati = {}
                    self.after(800, lambda: funzione_load(tabella, {}))
        if hasattr(self, '_win_doc_pers') and self._win_doc_pers.winfo_exists():
                if hasattr(self, '_doc_pers_load_tree'):
                    self.after(800, self._doc_pers_load_tree)
                    
    # Popolamento della Tabella Riepilogo Transazioni del Mese Corrente    
    def update_spese_mese_corrente(self, year=None, month=None):
        for i in self.spese_mese_tree.get_children():
            self.spese_mese_tree.delete(i)
        self.spese_mese_tree._metodo_lookup = {}
        self.spese_mese_tree._entry_lookup = {}
        now = datetime.date.today()
        if year is None or month is None:
            year, month = now.year, now.month
        spese_mese = []
        for d in sorted(self.spese.keys()):
            if d.year == year and d.month == month:
                for entry in self.spese[d]:
                    cat, desc, imp, tipo = entry[:4]
                    spese_mese.append((d, cat, desc, imp, tipo, entry))
        for d, cat, desc, imp, tipo, entry in spese_mese:
            tag = "futuro" if d > datetime.date.today() else ("entrata" if tipo == "Entrata" else "uscita")
            item_id = self.spese_mese_tree.insert("", "end", values=(
                d.strftime("%d-%m-%Y"), cat, desc, f"{imp:.2f}", tipo
            ), tags=(tag,))
            _desc_low = str(desc).lower()
            _partecipante_nome = ""
            _partecipante_tipo = ""
            for _p in getattr(self, "nomi_partecipanti", []):
                _p_nome = _p.get("nome", "") if isinstance(_p, dict) else _p
                if not _p_nome:
                    continue
                if any(f"{_ico}{_p_nome}".lower() in _desc_low for _ico in ("PER·", "CTP·", "CNT·")):
                    _partecipante_nome = _p_nome
                    _partecipante_tipo = _p.get("tipo", "persona") if isinstance(_p, dict) else "persona"
                    break
            self.spese_mese_tree._metodo_lookup[item_id] = {
                "metodo": campo(entry, "metodo_pagamento", ""),
                "conto": campo(entry, "conto", ""),
                "ora": campo(entry, "ora", ""),
                "hashtag": campo(entry, "hashtag", []),
                "id_ricorrenza": campo(entry, "id_ricorrenza", ""),
                "data": d.strftime("%d-%m-%Y"),
                "categoria": cat,
                "importo": imp,
                "partecipante": _partecipante_nome,
                "partecipante_tipo": _partecipante_tipo,
            }
            self.spese_mese_tree._entry_lookup[item_id] = entry
        self.after(100, self.draw_top_categorie)
        self.after(100, self.draw_spark_mese)
        self.after(100, self.draw_heatmap_mese)
        self.after(100, self.draw_estratto_metodo)
        self.after(100, self.draw_estratto_conto)
        self.after(100, lambda: self.aggiorna_vista_ricorrenti(self.considera_ricorrenze_var.get()))
        

    # Applicazione Filtro Mese/Anno (Estratto Conto) e Aggiornamento Viste Statistiche
    def apply_estratto(self, forza_modalita=None):
        try:
            month_str = self.estratto_month_var.get()
            match = re.match(r'(\d+)\s*-\s*', month_str)
            if match:
                m = int(match.group(1))
            else:
                try:
                    m = int(month_str)
                except ValueError:
                    raise ValueError("Il formato del mese non è corretto o è vuoto.")
            y = int(self.estratto_year_var.get())
            d = datetime.date(y, m, 1)
            self.stats_refdate = d
            self._view_year  = y
            self._view_month = m
            if not forza_modalita:
                self.toggle_stats_view("tabella")
            if not hasattr(self, 'stats_table') or not self.stats_table.winfo_exists():
                return 
            if forza_modalita:
                self.set_stats_mode(forza_modalita)
            self.update_totalizzatore_anno_corrente(year=y)
            self.update_totalizzatore_mese_corrente(year=y, month=m)
            self.update_spese_mese_corrente(year=y, month=m)
        except Exception:
            self.show_custom_warning("Errore", "Mese o anno non validi")
            
    # Reconfigurazione Dinamica della Tabella Statistiche per Modalità di Visualizzazione
    def set_stats_mode(self, mode):
        if hasattr(self, 'btn_modifica_sel'):
            self.reset_modifica_form()
        if not hasattr(self, 'stats_table') or not self.stats_table.winfo_exists():
            return 
        if hasattr(self, 'stats_mode'):
            self.stats_mode.set(mode)
        if hasattr(self, 'stats_hint_label'):
            if mode == "giorno":
                 nuova_guida = "Doppio clic → Documenti  |  Tasto destro → Promemoria"
            else:
                 nuova_guida = "Doppio clic → Dettaglio  |  Tasto destro → Grafico"
            self.stats_hint_label.config(text=nuova_guida)
        self.stats_table["displaycolumns"] = ("A", "B", "C", "D", "E", "F")
        if mode == "giorno":
            try:
                data_corrente = self.cal.selection_get()
            except:
                data_corrente = datetime.date.today()
            
            self.stats_label.config(
                text=f"Riepilogo Giornaliero - {data_corrente.strftime('%d-%m-%Y')}",
                foreground="purple", font=("Arial", 10, "bold"))
            if data_corrente != datetime.date.today():
                self.blink_label_colors(self.stats_label, "purple", "orange")
            else:
                self.stop_blink_label_colors(self.stats_label, final_color="purple")
                
            cols = {
                "A": (80, "center", "Data"),
                "B": (150, "w", "Categoria"),
                "C": (240, "w", "Descrizione"),
                "D": (100, "center", "Importo"),
                "E": (70, "center", "Tipo"),
                "F": (100, "center", "Conto/Varia")
            }
        else:
            if mode == "mese":
                ref = getattr(self, 'stats_refdate', datetime.date.today())
                m_name = self.get_month_name(ref.month) if hasattr(self, 'get_month_name') else str(ref.month)
                self.stats_label.config(text=f"Riepilogo Mensile {m_name} {ref.year}", foreground="dodgerblue", font=("Arial", 10, "bold"))
                if ref.month != datetime.date.today().month or ref.year != datetime.date.today().year:
                    self.blink_label_colors(self.stats_label, "dodgerblue", "orange")
                else:
                    self.stop_blink_label_colors(self.stats_label, final_color="dodgerblue")
            elif mode == "anno":
                ref = getattr(self, 'stats_refdate', datetime.date.today())
                self.stats_label.config(text=f"Riepilogo Annuale {ref.year}", foreground="forest green", font=("Arial", 10, "bold"))
                if ref.year != datetime.date.today().year:
                    self.blink_label_colors(self.stats_label, "forest green", "orange")
                else:
                    self.stop_blink_label_colors(self.stats_label, final_color="forest green")
            else:
                self.stats_label.config(text="Riepilogo Totale Categorie", foreground="firebrick", font=("Arial", 10, "bold"))
                self.stop_blink_label_colors(self.stats_label, final_color="firebrick")
            self.stats_table["displaycolumns"] = ("A", "B", "C")
            cols = {
                "A": (300, "w", "Categoria"),
                "B": (200, "center", "Totale (€)"),
                "C": (150, "center", "Tipo")
            }
        for col_id, (width, anchor, txt) in cols.items():
            self.stats_table.column(col_id, width=width, anchor=anchor)
            self.stats_table.heading(col_id, text=txt)
        funcs = [self.update_stats, 
                 lambda: self.update_totalizzatore_anno_corrente(year=getattr(self, '_view_year', None)),
                 lambda: self.update_totalizzatore_mese_corrente(year=getattr(self, '_view_year', None), month=getattr(self, '_view_month', None)),
                 lambda: self.update_spese_mese_corrente(year=getattr(self, '_view_year', None), month=getattr(self, '_view_month', None))]
        for f in funcs:
            try: f()
            except: pass
        if hasattr(self, 'vsb_stats'):
            self.stats_table.configure(yscrollcommand=self.vsb_stats.set)
            self.vsb_stats.config(command=self.stats_table.yview)
            self.vsb_stats.lift() 
            self.stats_table.yview_moveto(0)
    
    # Ordina una colonna del Treeview: tenta ordinamento numerico, ricade su alfabetico in caso di errore        
    def treeview_sort_column(self, tv, col, reverse):
        items = [(tv.set(k, col), k) for k in tv.get_children("")]

        def to_float(v):
            s = str(v).replace("€", "").strip()
            s = s.replace(".", "").replace(",", ".")
            return float(s or 0)
        def to_date(v):
            from datetime import datetime
            return datetime.strptime(str(v).strip(), "%d-%m-%Y")
        try:
            items.sort(key=lambda t: to_float(t[0]), reverse=reverse)
        except Exception:
            try:
                items.sort(key=lambda t: to_date(t[0]), reverse=reverse)
            except Exception:
                items.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)
        for index, (_, k) in enumerate(items):
            tv.move(k, "", index)
        for c in tv["columns"]:
            cur = tv.heading(c, "text")
            clean = cur.replace(" ▲", "").replace(" ▼", "")
            arrow = (" ▲" if not reverse else " ▼") if c == col else ""
            tv.heading(c, text=clean + arrow, command=lambda _c=c: self.treeview_sort_column(tv, _c, not reverse if _c == col else False))
    
    # Restituisce il nome del mese in italiano dal numero, o il numero come stringa se fuori range    
    def get_month_name(self, month):
        mesi = [
            "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
            "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
        ]
        return mesi[month-1] if 1 <= month <= 12 else str(month)

    # Apre/Chiude l'entry di Ricerca Globale, nascondendo le altre icone a destra per fare spazio
    def _toggle_ricerca_globale(self):
        self._ricerca_globale_aperta = not self._ricerca_globale_aperta
        if self._ricerca_globale_aperta:
            for btn, testo in [
                (self.btn_oggi_stats, ""),
                (self.btn_giorno, ""),
                (self.btn_mese, ""),
                (self.btn_anno, ""),
                (self.btn_totali, ""),
                ]:
                btn.configure(text=testo)   
            self.ricerca_globale_entry.pack(side=tk.RIGHT, padx=(2, 4))
            self.ricerca_globale_entry.focus_set()
        else:
            is_expanded = getattr(self, "sidebar_espansa", False)
            for btn, testo in [
                (self.btn_oggi_stats, "" if is_expanded else " Oggi"),
                (self.btn_giorno, "" if is_expanded else " Giorno"),
                (self.btn_mese, "" if is_expanded else " Mese"),
                (self.btn_anno, "" if is_expanded else " Anno"),
                (self.btn_totali, "" if is_expanded else " Totali"),
            ]:
                btn.configure(text=testo)
            self._ricerca_globale_var.set("")
            self.ricerca_globale_entry.pack_forget()
            
    # Ricerca Globale nella Tabella Riepilogo Avanzato
    def _filtra_stats_table_globale(self, *_):
        if not hasattr(self, 'stats_table') or not self.stats_table.winfo_exists():
            return
        testo = self._ricerca_globale_var.get().strip().lower()
        if not testo:
            self.update_stats()
            return
        for i in self.stats_table.get_children():
            self.stats_table.delete(i)
        self.stats_table._metodo_lookup = {}
        oggi = datetime.date.today()
        tot_entrate, tot_uscite = 0.0, 0.0
        righe_trovate = []
        for d, lista in self.spese.items():
            for entry in lista:
                cat, desc, imp, tipo = entry[:4]
                if testo in f"{cat} {desc}".lower():
                    righe_trovate.append((d, cat, desc, imp, tipo, entry))
        righe_trovate.sort(key=lambda r: r[0], reverse=True)
        if not righe_trovate:
            self.stats_table.insert("", "end", values=("", "Nessun movimento trovato", "", "", "", ""), tags=("vuoto",))
        for d, cat, desc, imp, tipo, entry in righe_trovate:
            tag = "futuro" if d > oggi else ("entrata" if tipo == "Entrata" else "uscita")
            nome_conto_g = campo(entry, "conto", "")
            item_id = self.stats_table.insert(
                "", "end",
                values=(d.strftime("%d-%m-%Y"), cat, desc, f"{imp:.2f}", tipo, nome_conto_g),
                tags=(tag,)
            )
            self.stats_table._metodo_lookup[item_id] = {
                "metodo": campo(entry, "metodo_pagamento", ""),
                "conto": nome_conto_g,
                "ora": campo(entry, "ora", ""),
                "hashtag": campo(entry, "hashtag", []),
                "id_ricorrenza": campo(entry, "id_ricorrenza", ""),
                "data": d.strftime("%d-%m-%Y"),
                "categoria": cat,
                "importo": imp,
            }
            if tipo == "Entrata":
                tot_entrate += imp
            else:
                tot_uscite += imp
        diff = tot_entrate - tot_uscite
        colore_fg = "dodgerblue" if diff >= 0 else "red"
        self.totali_label.config(
            text=f"Totale Entrate: {tot_entrate:.2f}    Totale Uscite: {tot_uscite:.2f}    Differenza: {diff:.2f}",
            foreground=colore_fg, font=("Arial", 10, "bold")
        )
        if hasattr(self, 'lbl_mov_count'):
            self.lbl_mov_count.config(text=f"  ·  Ricerca: {len(righe_trovate)} mov.")

    def update_stats(self):
        if not hasattr(self, 'stats_table') or not self.stats_table.winfo_exists():
            return
        for i in self.stats_table.get_children():
            self.stats_table.delete(i)
        self.stats_table._metodo_lookup = {}
        mode = self.stats_mode.get()
        tot_entrate, tot_uscite = 0.0, 0.0
        oggi = datetime.date.today()
        ref = self.stats_refdate
        if mode == "giorno":
            try:
                giorno = datetime.datetime.strptime(self.cal.get_date(), "%d-%m-%Y").date()
            except Exception:
                giorno = oggi
            spese = self.spese.get(giorno, [])
            if not spese:
                self.stats_table.insert("", "end", values=("", "Nessun movimento", "", "", "", ""), tags=("vuoto",))
                self.totali_label.config(text="Totale Entrate: 0.00    Totale Uscite: 0.00    Differenza: 0.00", foreground="dodgerblue", font=("Arial", 10, "bold"))
                if hasattr(self, 'lbl_mov_count'):
                    cur_text = self.stats_label.cget("text").split("  ·")[0]
                    self.stats_label.config(text=cur_text)
                self.after(150, lambda: self.aggiorna_meteo_avanzato_auto(mode))
                return
            _agganci_st = {}
            _agganci_uso_st = {}
            try:
                with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
                    _db_p_st = json.load(_pf)
                _id_a_nome_st = {c["id"]: c.get("nome","") for c in _db_p_st.get("conti",[])}
                for _t in _db_p_st.get("trasferimenti", []):
                    if _t.get("da") in ("__spese__","Contabilità") or _t.get("a") in ("__spese__","Contabilità"):
                        _data_t = _t.get("data","")
                        _imp_t  = round(float(_t.get("importo",0)), 2)
                        _tipo_t = "Entrata" if _t.get("da") in ("__spese__","Contabilità") else "Uscita"
                        _cnome  = _id_a_nome_st.get(_t.get("a") if _tipo_t=="Entrata" else _t.get("da"), "")
                        _agganci_st.setdefault((_data_t, _imp_t, _tipo_t), []).append(_cnome)
            except Exception:
                _agganci_st = {}
                _agganci_uso_st = {}
            for idx, entry in enumerate(spese):
                cat, desc, imp, tipo = entry[:4]
                tag = "futuro" if giorno > datetime.date.today() else ("entrata" if tipo == "Entrata" else "uscita")
                nome_conto_st = campo(entry, "conto", "")
                if not nome_conto_st:
                    _key_st = (giorno.strftime("%d-%m-%Y"), round(float(imp), 2), tipo)
                    _lista_conti = _agganci_st.get(_key_st, [])
                    _uso = _agganci_uso_st.get(_key_st, 0)
                    nome_conto_st = _lista_conti[_uso] if _uso < len(_lista_conti) else ""
                    _agganci_uso_st[_key_st] = _uso + 1
                _item_st = self.stats_table.insert(
                    "", "end",
                    values=(giorno.strftime("%d-%m-%Y"), cat, desc, f"{imp:.2f}", tipo, nome_conto_st),
                    tags=(f"{giorno.strftime('%d-%m-%Y')}|{idx}", tag)
                )
                _desc_low_st = str(desc).lower()
                _partecipante_nome_st = ""
                _partecipante_tipo_st = ""
                for _p in getattr(self, "nomi_partecipanti", []):
                    _p_nome = _p.get("nome", "") if isinstance(_p, dict) else _p
                    if not _p_nome:
                        continue
                    if any(f"{_ico}{_p_nome}".lower() in _desc_low_st for _ico in ("PER·", "CTP·", "CNT·")):
                        _partecipante_nome_st = _p_nome
                        _partecipante_tipo_st = _p.get("tipo", "persona") if isinstance(_p, dict) else "persona"
                        break
                self.stats_table._metodo_lookup[_item_st] = {
                    "metodo": campo(entry, "metodo_pagamento", ""),
                    "conto": nome_conto_st,
                    "ora": campo(entry, "ora", ""),
                    "hashtag": campo(entry, "hashtag", []),
                    "id_ricorrenza": campo(entry, "id_ricorrenza", ""),
                    "data": giorno.strftime("%d-%m-%Y"),
                    "categoria": cat,
                    "importo": imp,
                    "partecipante": _partecipante_nome_st,
                    "partecipante_tipo": _partecipante_tipo_st,
                }
                if tipo == "Entrata":
                    tot_entrate += imp
                else:
                    tot_uscite += imp
        else:
            totali = {}
            future_cats = set()
            for d, sp in self.spese.items():
                if mode == "mese":
                    if not (d.year == ref.year and d.month == ref.month):
                        continue
                elif mode == "anno":
                    if d.year != ref.year:
                        continue
                for entry in sp:
                    data_voce = d
                    if not self.considera_ricorrenze_var.get():
                        if mode == "totali":
                            if data_voce > oggi:
                                continue
                        elif mode == "anno":
                            if ref.year == oggi.year:
                                if data_voce > oggi:
                                    continue
                        elif mode == "mese":
                            if ref.year == oggi.year and ref.month == oggi.month:
                                if data_voce > oggi:
                                    continue
                    cat, desc, imp, tipo = entry[:4]
                    if data_voce > oggi:
                        future_cats.add(cat)
                    if cat not in totali:
                        totali[cat] = {"Entrata": 0.0, "Uscita": 0.0}
                    totali[cat][tipo] += imp
            if not totali:
                self.stats_table.insert("", "end", values=("Nessun movimento", "", ""), tags=("vuoto",))
                self.totali_label.config(text="Totale Entrate: 0.00    Totale Uscite: 0.00    Differenza: 0.00", foreground="dodgerblue", font=("Arial", 10, "bold"))
                if hasattr(self, 'lbl_mov_count'):
                    cur_text = self.stats_label.cget("text").split("  ·")[0]
                    self.stats_label.config(text=cur_text)
                self.after(150, lambda: self.aggiorna_meteo_avanzato_auto(mode))
                return
            for cat in sorted(totali.keys()):
                for tipo in ("Entrata", "Uscita"):
                    if totali[cat][tipo] > 0:
                        tag = "futuro" if cat in future_cats else ("entrata" if tipo == "Entrata" else "uscita")
                        self.stats_table.insert(
                            "", "end",
                            values=(cat, f"{totali[cat][tipo]:.2f}", tipo),
                            tags=(tag,)
                        )
                        if tipo == "Entrata":
                            tot_entrate += totali[cat][tipo]
                        else:
                            tot_uscite += totali[cat][tipo]
        diff = tot_entrate - tot_uscite
        colore_fg = "dodgerblue" if diff >= 0 else "red"
        txt_tot = f"Totale Entrate: {tot_entrate:.2f}    Totale Uscite: {tot_uscite:.2f}    Differenza: {diff:.2f}"
        self.totali_label.config(text=txt_tot, foreground=colore_fg, font=("Arial", 10, "bold"))
        if hasattr(self, 'lbl_mov_count'):
            if mode == "giorno":
                n = len(self.stats_table.get_children())
            else:
                n = 0
                for d, sp in self.spese.items():
                    if mode == "mese":
                        if not (d.year == ref.year and d.month == ref.month):
                            continue
                    elif mode == "anno":
                        if d.year != ref.year:
                            continue
                    for entry in sp:
                        if not self.considera_ricorrenze_var.get():
                            if mode == "totali" and d > oggi:
                                continue
                            elif mode == "anno" and ref.year == oggi.year and d > oggi:
                                continue
                            elif mode == "mese" and ref.year == oggi.year and ref.month == oggi.month and d > oggi:
                                continue
                        n += 1
            cur_text = self.stats_label.cget("text").split("  ·")[0]
            if n:
                self.stats_label.config(text=f"{cur_text}  ·  {n} mov.")
        self.after(150, lambda: self.aggiorna_meteo_avanzato_auto(mode))
        
    # Calcolo e Visualizzazione Totali Riassuntivi (Annuali e Mensili)
    def update_totalizzatore_anno_corrente(self, year=None):
        now = datetime.date.today()
        if year is None:
            year = now.year
        if year == now.year:
            self.lbl_titolo_anno.config(text=" Riepilogo Anno Attuale")
        else:
            self.lbl_titolo_anno.config(text=f" Riepilogo Anno {year}")
        totale_entrate = 0.0
        totale_uscite = 0.0
        for d, sp in self.spese.items():
            if d.year == year:
                for entry in sp:
                    if hasattr(self, "considera_ricorrenze_var") and not self.considera_ricorrenze_var.get():
                        if d > now:
                            continue
                    tipo = entry[3]
                    imp = entry[2]
                    if tipo == "Entrata":
                        totale_entrate += imp
                    else:
                        totale_uscite += imp
        differenza_anno = totale_entrate - totale_uscite
        self._diff_anno_reale = differenza_anno
        self._anima_label_valore(self.totalizzatore_entrate_label, totale_entrate)
        self._anima_label_valore(self.totalizzatore_uscite_label,  totale_uscite)
        self._anima_label_valore(self.totalizzatore_diff_label,    differenza_anno)
        if differenza_anno < 0:
            self.start_blinking_colors(self.totalizzatore_diff_label)
        else:
            self.stop_blinking_colors(self.totalizzatore_diff_label)
            self.totalizzatore_diff_label.config(foreground="dodgerblue")
        diff_mese = getattr(self, '_diff_mese_reale', 0.0)
        self.aggiorna_meteo_saldo(diff_mese, differenza_anno)

    def update_totalizzatore_mese_corrente(self, year=None, month=None):
        now = datetime.date.today()
        if year is None or month is None:
            year, month = now.year, now.month
        m_nomi = ["Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno",
                  "Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"]
        if year == now.year and month == now.month:
            self.lbl_titolo_mese.config(text=" Riepilogo Mese Attuale")
        else:
            self.lbl_titolo_mese.config(text=f" Riepilogo {m_nomi[month-1]} {year}")
        totale_entrate = 0.0
        totale_uscite = 0.0
        for d, sp in self.spese.items():
            if d.year == year and d.month == month:
                for entry in sp:
                    if hasattr(self, "considera_ricorrenze_var") and not self.considera_ricorrenze_var.get():
                        if d > now:
                            continue
                    tipo = entry[3]
                    imp = entry[2]
                    if tipo == "Entrata":
                        totale_entrate += imp
                    else:
                        totale_uscite += imp
        differenza_mese = totale_entrate - totale_uscite
        self._diff_mese_reale = differenza_mese
        self._anima_label_valore(self.totalizzatore_mese_entrate_label, totale_entrate)
        self._anima_label_valore(self.totalizzatore_mese_uscite_label,  totale_uscite)
        self._anima_label_valore(self.totalizzatore_mese_diff_label,    differenza_mese)
        if differenza_mese < 0:
            self.start_blinking_colors(self.totalizzatore_mese_diff_label)
        else:
            self.stop_blinking_colors(self.totalizzatore_mese_diff_label)
            self.totalizzatore_mese_diff_label.config(foreground="dodgerblue")
        diff_anno = getattr(self, '_diff_anno_reale', 0.0)
        self.aggiorna_meteo_saldo(differenza_mese, diff_anno)
        self.aggiorna_cruscotto(year=year, month=month)
        
    def _anima_label_valore(self, label, valore_finale, steps=20, step_ms=30):
        if ANIMAZIONI:
            try:
                testo_attuale = label.cget("text").replace("€", "").replace(",", ".").strip()
                valore_iniziale = float(testo_attuale) if testo_attuale else 0.0
            except:
                valore_iniziale = 0.0
            delta = valore_finale - valore_iniziale
            def _step(i):
                if not label.winfo_exists():
                    return
                t = i / steps
                t_ease = t * t * (3 - 2 * t)
                valore = valore_iniziale + delta * t_ease
                label.config(text=f"{valore:.2f} €")
                if i < steps:
                    self.after(step_ms, lambda: _step(i + 1))
                else:
                    label.config(text=f"{valore_finale:.2f} €")
            _step(0)
        else:
            label.config(text=f"{valore_finale:.2f} €")
                        
    # Gestione del Database: Importazione e Esportazione del File di Dati    
    def import_db(self):
        file = filedialog.askopenfilename(
            title="Importa Database",
            defaultextension=".json",
            initialdir=EXP_DB,
            filetypes=[("File JSON", "*spese_db.json"), ("Tutti i file", "*.*")]
        )
        if file:
            try:
                with open(file, "r", encoding="utf-8") as fsrc:
                    dbdata = fsrc.read()
                with open(DB_FILE, "w", encoding="utf-8") as fdst:
                    fdst.write(dbdata)
                migrazione_emoji_ok = True
                try:
                    from moduli.migrazione_emoji_dati import migra_emoji_nei_dati
                    migra_emoji_nei_dati([(DB_FILE, 2)])
                except Exception as _e:
                    migrazione_emoji_ok = False
                    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Migrazione emoji dati (import DB) fallita: {_e}")
                self.load_db()
                if hasattr(self, 'cat_menu'):
                    self.cat_menu["values"] = self.categorie
                    if self.categorie:
                        self.cat_sel.set(self.categorie[0])
                if hasattr(self, 'cat_mod_menu'):
                    self.cat_mod_menu["values"] = self.categorie
                    if self.categorie:
                        self.cat_mod_sel.set(self.categorie[0])
                self.update_stats()
                self.update_totalizzatore_anno_corrente()
                self.update_totalizzatore_mese_corrente()
                self.update_spese_mese_corrente()
                msg_importazione = f"Database importato da {file}"
                if not migrazione_emoji_ok:
                    msg_importazione += (
                        "\n\nATTENZIONE: la migrazione emoji→testo non è riuscita su questo import.\n"
                        "Alcuni dati potrebbero restare nel vecchio formato. Riavvia l'app: "
                        "la migrazione viene ritentata automaticamente ad ogni avvio."
                    )
                self.show_custom_warning("Importazione completata", msg_importazione)
            except Exception as e:
                print(f"Errore durante l'importazione: {e}")
                self.show_custom_warning("Errore", f"Errore durante l'importazione: {e}")
    def export_db(self):
        now = datetime.date.today()
        default_dir = EXP_DB
        default_filename = f"{now.day:02d}-{now.month:02d}-{now.year}-spese_db.json"
        file = filedialog.asksaveasfilename(
            title="Esporta Database",
            defaultextension=".json",
            initialdir=default_dir,
            initialfile=default_filename,
            confirmoverwrite=False,
            filetypes=[("File JSON", "*spese_db.json"), ("Tutti i file", "*.*")]
        )
        if file:
            try:
                with open(DB_FILE, "r", encoding="utf-8") as fsrc:
                    dbdata = fsrc.read()
                with open(file, "w", encoding="utf-8") as fdst:
                    fdst.write(dbdata)
                self.show_custom_warning("Esportazione completata", f"Database esportato in {file}")
            except Exception as e:
                self.show_custom_warning("Errore", f"Errore durante l'esportazione: {e}")

    def _saldo_effettivo(self, conto, db):
        oggi = datetime.date.today()
        include_futuri = self.considera_futuri_portafoglio_var.get()
        nome = conto.get("nome", "")
        saldo = float(conto.get("saldo", 0))
        for d, voci in self.spese.items():
            if not include_futuri and d > oggi:
                continue
            for v in voci:
                if campo(v, "conto", "") == nome:
                    try:
                        imp = float(v[2])
                        saldo += imp if str(v[3]) == "Entrata" else -imp
                    except Exception:
                        pass
        for t in db.get("trasferimenti", []):
            if t.get("da") == "__spese__" or t.get("a") == "__spese__":
                continue
            try:
                data_t = datetime.datetime.strptime(t["data"], "%d-%m-%Y").date()
            except Exception:
                continue
            if not include_futuri and data_t > oggi:
                continue
            try:
                imp = round(float(t.get("importo", 0)), 2)
            except Exception:
                continue
            if t.get("da") == conto.get("id"):
                saldo -= imp
            elif t.get("a") == conto.get("id"):
                saldo += imp
        return saldo

    # Apertura Diretta del Link Bancario nel Browser di Sistema
    def chiama_banca(self):
        if not LINK_BANCA or LINK_BANCA.strip() == "":
            messaggio_istruzioni = (
                "L'indirizzo del link bancario non è stato configurato.\n\n"
                "Per risolvere:\n"
                "1. Vai al menu *Opzioni*.\n"
                "2. Seleziona *Impostazioni App*.\n"
                "3. Inserisci l'URL completo della tua banca nel campo dedicato."
            )
            self.show_custom_warning(
                "Link Bancario Mancante", 
                messaggio_istruzioni
            )
            return
        try:
            webbrowser.open_new_tab(LINK_BANCA)
        except Exception as e:
            self.show_custom_warning(
                "Errore di Apertura", 
                f"Impossibile aprire il link: {LINK_BANCA}\nErrore: {e}"
            )
            print(f"Errore durante l'apertura del link: {e}")

    # goto_dettaglio_mese ora vive in moduli/goto_dettaglio_mese.py (registrato da registra_tutti_i_moduli)

    # Ripristino della Visualizzazione alla Data Attuale        
    def goto_today(self):
        self.mostra_treeview_statistiche()
        today = datetime.date.today()
        if hasattr(self, "cal"):
            self.cal.selection_set(today)
            self.cal._sel_date = today
        self.stats_refdate = today
        mesi = [
            "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
            "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
        ]
        self.estratto_month_var.set(mesi[today.month - 1])
        self.estratto_year_var.set(str(today.year))
        self.set_stats_mode("giorno")
        self.after_idle(self.update_stats)
        self.update_totalizzatore_anno_corrente()
        self.update_totalizzatore_mese_corrente()
        self._view_year  = today.year
        self._view_month = today.month
        self.update_spese_mese_corrente()
        self.aggiorna_monitoraggio_budget()
        self.stats_label.config(
            text=f"Riepilogo Giornaliero - {today.strftime('%d-%m-%Y')}",
            foreground="purple", font=("Arial", 10, "bold"))
        self.stop_blink_label_colors(self.stats_label, final_color="purple")
        self.lbl_titolo_analisi.config(text=" Analisi Mese Attuale")
        self.lbl_titolo_mese.config(text=" Riepilogo Mese Attuale")
        self.lbl_titolo_anno.config(text=" Riepilogo Anno Attuale")

    # Cruscotto
    def _cicla_cruscotto(self):
        self._cruscotto_stato = (getattr(self, '_cruscotto_stato', 0) + 1) % 3
        stato = self._cruscotto_stato
        self.mese_notebook.pack_forget()
        self.cruscotto_canvas.pack_forget()
        self.conti_canvas.pack_forget()
        self._cruscotto_attivo = False
        if stato == 0:
            self.mese_notebook.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            self.btn_ciclo_cruscotto.config(text="▼")
            if hasattr(self, '_hint_label_analisi'):
                self._hint_label_analisi.config(text=" Doppio clic → Dashboard  |  Clic destro → Copia nel form")
        elif stato == 1:
            self._cruscotto_attivo = True
            self.cruscotto_canvas.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            self.btn_ciclo_cruscotto.config(text="▶")
            now = datetime.date.today()
            self.aggiorna_cruscotto(year=now.year, month=now.month)
            def _on_cruscotto_click(e):
                W = self.cruscotto_canvas.winfo_width() or 460
                H = self.cruscotto_canvas.winfo_height() or 300
                col = 0 if e.x < W // 2 else 1
                row = 0 if e.y < H // 2 else 1
                filtri = [("Entrata", None), (None, "Uscita"), (None, None), (None, None)]
                idx = row * 2 + col
                tipo_f, _ = filtri[idx]
                now2 = datetime.date.today()
                self.stats_refdate = datetime.date(now2.year, now2.month, 1)
                self.stats_mode.set("mese")
                self.update_stats()
            def _on_cruscotto_resize(e):
                if getattr(self, '_cruscotto_resize_job', None):
                    self.after_cancel(self._cruscotto_resize_job)
                self._cruscotto_resize_job = self.after(150, lambda: self.aggiorna_cruscotto(
                    year=datetime.date.today().year,
                    month=datetime.date.today().month))
            self.cruscotto_canvas.bind("<Double-1>", _on_cruscotto_click)
            self.cruscotto_canvas.bind("<Button-3>", lambda e: self.apri_fondo_risparmio())
            self.cruscotto_canvas.bind("<Configure>", _on_cruscotto_resize)
            if hasattr(self, '_hint_label_analisi'):
                self._hint_label_analisi.config(text=" Doppio clic → Dettaglio  |  Clic destro → Fondo Risparmio")
        else:
            self.conti_canvas.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
            self.btn_ciclo_cruscotto.config(text="■")
            self.aggiorna_conti_canvas()
            def _on_conti_resize(e):
                if getattr(self, '_conti_resize_job', None):
                    self.after_cancel(self._conti_resize_job)
                self._conti_resize_job = self.after(150, self.aggiorna_conti_canvas)
            self.conti_canvas.bind("<Configure>", _on_conti_resize)
            if hasattr(self, '_hint_label_analisi'):
                self._hint_label_analisi.config(text=" Saldi Portafoglio Bancario")

    def aggiorna_conti_canvas(self):
        c = self.conti_canvas
        c.update_idletasks()
        W = c.winfo_width() or 460
        H = c.winfo_height() or 300
        if W < 10 or H < 10:
            return
        c.delete("all")
        bg_color = getattr(self, 'COLOR_WIDGET_BG', "#1E1E1E")
        testo_color = getattr(self, 'TEXT_COLOR', '#E8E8E8')
        try:
            with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as f:
                db_p = json.load(f)
            conti = db_p.get("conti", [])
            trasferimenti = db_p.get("trasferimenti", [])
        except Exception:
            conti = []
            trasferimenti = []
        TIPO_COLORI = {
            "personale": "#4A90D9",
            "comune":    "#50C878",
            "figli":     "#C45E00",
            "altro":     "#A78BFA",
        }
        c.create_text(W // 2, 14, text="Portafoglio Bancario",
                      fill=testo_color, font=("Arial", 10, "bold"), anchor="n")
        if not conti:
            c.create_text(W // 2, H // 2, text="Nessun conto registrato",
                          fill="#888888", font=("Arial", 10), anchor="center")
            return
        saldi_visualizzati = {}
        id_a_nome = {}
        for conto in conti:
            cid = conto.get("id", "")
            nome = conto.get("nome", "?")
            id_a_nome[cid] = nome
            try:
                saldi_visualizzati[cid] = float(conto.get("saldo", 0))
            except:
                saldi_visualizzati[cid] = 0.0
        if not self.considera_ricorrenze_var.get():
            oggi = datetime.date.today()
            for tf in trasferimenti:
                try:
                    data_str = tf.get("data", "")
                    d_parti = data_str.split("-")
                    giorno = datetime.date(int(d_parti[2]), int(d_parti[1]), int(d_parti[0]))
                except:
                    continue
                if giorno > oggi:
                    try:
                        imp = float(tf.get("importo", 0))
                    except:
                        imp = 0.0
                    id_da = tf.get("da", "")
                    id_a = tf.get("a", "")
                    if id_da in saldi_visualizzati:
                        saldi_visualizzati[id_da] += imp
                    if id_a in saldi_visualizzati:
                        saldi_visualizzati[id_a] -= imp
        totale = sum(saldi_visualizzati.values())
        n = len(conti)
        PAD_TOP  = 34
        PAD_BOT  = 22
        PAD_SIN  = 10
        NOME_W   = 110
        IMP_W    = 80
        BAR_X    = PAD_SIN + NOME_W + 6
        BAR_MAX_W = W - BAR_X - IMP_W - 10
        area_h   = H - PAD_TOP - PAD_BOT
        row_h    = area_h // n if n > 0 else 25
        BAR_H    = max(8, min(18, row_h - 8))
        max_saldo = max((abs(v) for v in saldi_visualizzati.values()), default=1.0) or 1.0
        for i, conto in enumerate(conti):
            cid    = conto.get("id", "")
            nome   = conto.get("nome", "?")
            saldo  = saldi_visualizzati.get(cid, 0.0)
            tipo   = conto.get("tipo", "altro")
            colore = TIPO_COLORI.get(tipo, "#A78BFA")
            princ  = "⭐ " if conto.get("principale") else ""
            y_center = PAD_TOP + i * row_h + row_h // 2
            nome_trunc = (princ + nome)[:14]
            c.create_text(PAD_SIN, y_center, text=nome_trunc,
                          fill=testo_color, font=("Arial", 9, "bold"), anchor="w")
            bar_y1 = y_center - BAR_H // 2
            bar_y2 = y_center + BAR_H // 2
            c.create_rectangle(BAR_X, bar_y1, BAR_X + BAR_MAX_W, bar_y2,
                               fill="#2a2a2a", outline="")
            bar_w = max(4, int(abs(saldo) / max_saldo * BAR_MAX_W))
            col_bar = colore if saldo >= 0 else "#CC3333"
            c.create_rectangle(BAR_X, bar_y1, BAR_X + bar_w, bar_y2,
                               fill=col_bar, outline="")
            saldo_txt = f"€ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            col_txt = self.COLOR_GREEN if saldo >= 0 else self.COLOR_RED
            c.create_text(BAR_X + BAR_MAX_W + 4, y_center, text=saldo_txt,
                          fill=col_txt, font=("Arial", 9, "bold"), anchor="w")
        tot_txt = f"Totale: € {totale:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        col_tot = self.COLOR_GREEN if totale >= 0 else self.COLOR_RED
        c.create_text(W // 2, H - 8, text=tot_txt,
                      fill=col_tot, font=("Arial", 9, "bold"), anchor="s")
    
    # Aggiorna Cruscotto Pil                  
    def aggiorna_cruscotto(self, year=None, month=None):
        import math
        from PIL import Image, ImageDraw, ImageTk, ImageFont
        now = datetime.date.today()
        if year is None or month is None:
            year, month = now.year, now.month
        if not getattr(self, '_cruscotto_attivo', False):
            return
        c = self.cruscotto_canvas
        c.update_idletasks()
        W = c.winfo_width() or 460
        H = c.winfo_height() or 300
        SCALE = 2
        def _carica_font(size):
            candidati = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "arial.ttf",
                "/Library/Fonts/Arial.ttf", 
                "/System/Library/Fonts/Helvetica.ttc", 
            ]
            for path in candidati:
                try:
                    return ImageFont.truetype(path, size)
                except:
                    continue
            return ImageFont.load_default()
        font_titolo = _carica_font(14*SCALE)
        font_valore = _carica_font(13*SCALE)
        font_small  = _carica_font(10*SCALE)
        entrate = uscite = 0.0
        for d, sp in self.spese.items():
            if d.year == year and d.month == month:
                for entry in sp:
                    if hasattr(self, "considera_ricorrenze_var") and not self.considera_ricorrenze_var.get():
                        if d > now:
                            continue
                    if entry[3] == "Entrata":
                        entrate += entry[2]
                    else:
                        uscite += entry[2]
        saldo = entrate - uscite
        target = getattr(self, 'budget_mensile', 0.0) or 1.0
        budget_pct = min(uscite / target, 1.0) if target > 0 else 0.0
        massimo = max(entrate, uscite, 1.0)
        saldo_colore_hex  = "#00AA00" if saldo >= 0 else "#CC0000"
        budget_colore_hex = "#00AA00" if budget_pct < 0.8 else ("#FF8800" if budget_pct < 1.0 else "#CC0000")
        SW, SH = W * SCALE, H * SCALE
        bg_color = getattr(self, 'COLOR_WIDGET_BG', "#1E1E1E")
        img = Image.new("RGB", (SW, SH), bg_color)
        draw = ImageDraw.Draw(img)
        def disegna_gauge_pil(draw, cx, cy, r, valore, massimo, colore_hex, titolo, formato="€"):
            cx, cy, r = cx*SCALE, cy*SCALE, r*SCALE
            pct = min(valore / massimo, 1.0) if massimo > 0 else 0
            bbox = [cx-r, cy-r, cx+r, cy+r]
            draw.arc(bbox, start=180, end=360, fill="#444444", width=10)
            if pct > 0:
                draw.arc(bbox, start=180, end=180+int(pct*180), fill=colore_hex, width=10)
            angolo = math.radians(pct * 180)
            lung = r - 28
            lx = cx - lung * math.cos(angolo)
            ly = cy - lung * math.sin(angolo)
            for offset in range(-2, 3):
                ox = offset * math.sin(angolo)
                oy = offset * math.cos(angolo)
                draw.line([(cx+ox, cy+oy), (lx+ox, ly+oy)], fill=colore_hex, width=2)
            rc = 10
            draw.ellipse([cx-rc, cy-rc, cx+rc, cy+rc], fill=colore_hex)
            if formato == "€":
                testo = f"{valore:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
            else:
                testo = f"{valore*100:.0f}%"
            draw.text((cx, cy + 36), testo, fill=colore_hex, anchor="mm", font=font_valore)
            draw.text((cx, cy - r - 26), titolo, fill=getattr(self, 'TEXT_COLOR', 'white'), anchor="mm", font=font_titolo)
            draw.text((cx - r - 20, cy + 10), "0", fill="#888888", anchor="mm", font=font_small)
            if formato == "€":
                draw.text((cx + r + 20, cy + 10),
                    f"{massimo:,.0f}".replace(",", "."),
                    fill="#888888", anchor="mm", font=font_small)
            else:
                draw.text((cx + r + 20, cy + 10), "100%", fill="#888888", anchor="mm", font=font_small)
        gw = W // 2
        gh = H // 2
        TITOLO_H = 30
        VALORE_H = 30
        LATO_H   = 35
        r = min(gw - LATO_H * 2, gh - TITOLO_H - VALORE_H) // 2
        r = max(r, 20)
        cy_top = TITOLO_H + r
        cy_top = min(cy_top, gh - VALORE_H - 5)
        cy_bot = gh + TITOLO_H + r
        cy_bot = min(cy_bot, H - VALORE_H - 5)
        positions = [
            (gw // 2,     cy_top, entrate,    massimo, "#00CC66",        "Entrate", "€"),
            (W - gw // 2, cy_top, uscite,     massimo, "#CC3333",        "Uscite",  "€"),
            (gw // 2,     cy_bot, abs(saldo), massimo, saldo_colore_hex, "Saldo",   "€"),
            (W - gw // 2, cy_bot, budget_pct, 1.0,    budget_colore_hex,"Budget %","%"),
        ]
        for cx, cy, val, mx, col, tit, fmt in positions:
            disegna_gauge_pil(draw, cx, cy, r, val, mx, col, tit, fmt)
        draw.line([(W//2*SCALE, 5*SCALE), (W//2*SCALE, (H-5)*SCALE)], fill="#333333", width=2)
        draw.line([(10*SCALE, H//2*SCALE), ((W-10)*SCALE, H//2*SCALE)], fill="#333333", width=2)
        img = img.resize((W, H), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        c.delete("all")
        c.create_image(0, 0, anchor="nw", image=photo)
        c._cruscotto_photo = photo
                      
    def on_stats_table_right_click(self, event):
        try:
            item_id = self.stats_table.identify_row(event.y)
            selezioni_correnti = self.stats_table.selection()
            if item_id and item_id not in selezioni_correnti:
                self.stats_table.selection_set(item_id)
            final_selections = self.stats_table.selection()
            if not final_selections:
                return
            mode = self.stats_mode.get() 
            if mode == "giorno":
                first_item_id = final_selections[0] 
                values = self.stats_table.item(first_item_id, "values") 
                if values and len(values) >= 5:
                    initial_date_str = str(values[0]).strip()
                    initial_category = str(values[1]).strip()
                    initial_description = str(values[2]).strip()
                    initial_amount = str(values[3]).strip().replace('€', '').replace(',', '.')
                    initial_type = str(values[4]).strip().lower()
                    self.launch_qr_svg_generator(
                        initial_category=initial_category,
                        initial_amount=initial_amount,
                        initial_date=initial_date_str,
                        initial_description=initial_description, 
                        initial_type=initial_type                
                    )
                    return 
            self.after(1, lambda: self.crea_grafico_categorie(final_selections))
        except Exception as e:
            print(f"Errore critico durante l'elaborazione del click destro: {e}")
        
    # Popup Gestione Utenze          
    def check_UTENZE_DB(self):
         if not os.path.exists(UTENZE_DB):
            with open(UTENZE_DB, "w") as file:
                file.write("")  
                self.utenze()

    # Gestore Doppio Click su Movimento Mensile (Navigazione Giornaliera)
    def on_spese_mese_tree_double_click(self, event):
        self.mostra_treeview_statistiche()
        self.after(0, self.imp_entry.focus_set)
        item_id = self.spese_mese_tree.identify_row(event.y)
        if not item_id:
            return
        values = self.spese_mese_tree.item(item_id, "values")
        if not values:
            return
        data_str = str(values[0]).strip()
        try:
            giorno = datetime.datetime.strptime(data_str, "%d-%m-%Y").date()
        except Exception:
            try:
                giorno = datetime.datetime.strptime(data_str, "%d/%m/%Y").date()
            except Exception:
                return
        self.set_stats_mode("giorno")
        if hasattr(self, "cal"):
            self.cal.selection_set(giorno)
            self.cal._sel_date = giorno
        self.update_stats()
        self.stats_label.config(
            text=f"Riepilogo Giornaliero - {giorno.strftime('%d-%m-%Y')}",
            foreground="purple", font=("Arial", 10, "bold"))
        if giorno != datetime.date.today():
            self.blink_label_colors(self.stats_label, "purple", "yellow")
        else:
            self.stop_blink_label_colors(self.stats_label, final_color="purple")

    # Navigazione al Giorno (Da Finestra di Dettaglio)
    def goto_day_from_popup(self, tree, popup):
        if self.stats_view_mode.get() != "tabella":
                self.mostra_treeview_statistiche()
        item_id = tree.focus()
        if not item_id:
                return
        vals = tree.item(item_id, "values")
        if not vals or len(vals) < 1:
                return
        data_str = vals[0]
        try:
                giorno = datetime.datetime.strptime(data_str, "%d-%m-%Y").date()
        except Exception:
                return
        self.set_stats_mode("giorno")
        if hasattr(self, "cal"):
                self.cal.selection_set(giorno)
                self.cal._sel_date = giorno
        self.stats_refdate = giorno
        self.estratto_month_var.set(f"{giorno.month:02d}")
        self.estratto_year_var.set(str(giorno.year))
        self.stats_label.config(text=f"Riepilogo Giornaliero - {giorno.strftime('%d-%m-%Y')}", 
                                foreground="purple", font=("Arial", 10, "bold"))
        if giorno != datetime.date.today():
            self.blink_label_colors(self.stats_label, "purple", "yellow")
        else:
            self.stop_blink_label_colors(self.stats_label, final_color="purple")
        def chiudi_e_aggiorna():
            try:
                popup.destroy()
            except Exception:
                pass
            if hasattr(self, 'confronto_popup') and self.confronto_popup is not None:
                 try:
                    if self.confronto_popup.winfo_exists():
                         self.confronto_popup.destroy()
                         self.confronto_popup = None
                 except Exception:
                         pass
            if hasattr(self, 'grafico_analisi_popup') and self.grafico_analisi_popup is not None:
                try:
                    self.grafico_analisi_popup.destroy()
                    self.grafico_analisi_popup = None
                except Exception:
                    pass
            if hasattr(self, 'popup_grafico') and self.popup_grafico and self.popup_grafico.winfo_exists():
                self.popup_grafico.destroy()
                del self.popup_grafico
            if hasattr(self, 'storico_cat_popup') and self.storico_cat_popup is not None:
                try:
                    if self.storico_cat_popup.winfo_exists():
                        self.storico_cat_popup.destroy()
                        self.storico_cat_popup = None
                except Exception:
                    pass
            if hasattr(self, 'win_risparmio') and self.win_risparmio is not None:
                try:
                    if self.win_risparmio.winfo_exists():
                        self.win_risparmio.destroy()
                        self.win_risparmio = None
                except Exception:
                    pass
            self.update_stats() 
            self.after_idle(lambda: self.forza_scroll_e_pulizia_selezione() if hasattr(self, 'forza_scroll_e_pulizia_selezione') else None)
        self.after(50, chiudi_e_aggiorna)
        
    # Gestore Cambio Stato Blocco Data
    def on_blocca_data_changed(self):
        if not self.blocca_data_var.get():
            self.data_spesa_var.set(datetime.date.today().strftime("%d-%m-%Y"))

    def scarica_manuale(self):
        try:
            response = requests.get(URL_PDF, timeout=15)
            response.raise_for_status()
            temp_path = os.path.join(tempfile.gettempdir(), "manuale_Orbita_casa.pdf")
            with open(temp_path, "wb") as f:
                f.write(response.content)
            self._apri_viewer_pdf(temp_path)
        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore nel download del manuale:", e)
            self.show_custom_warning("Attenzione", "Download NON completato!\n\nSembra ci sia stato un problema. 😕")

    def _esegui_aggiornamento_gui(self):
        try:
            self.load_db()
            if hasattr(self, 'aggiorna_combobox_categorie'):
                try:
                    self.aggiorna_combobox_categorie()
                except Exception:
                    pass
            if hasattr(self, 'carica_voci_treeview'):
                try:
                    self.carica_voci_treeview()
                except Exception:
                    pass
            if hasattr(self, 'ricorrenza_popup') and self.ricorrenza_popup.winfo_exists():
                if hasattr(self, 'ric_cat_menu'):
                    self.ric_cat_menu['values'] = sorted(self.categorie)
            if hasattr(self, 'refresh_gui'):
                try:
                    self.refresh_gui()
                except Exception:
                    pass
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] GUI: Aggiornamento completato (anche in background).")
        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Nota: Aggiornamento grafico parziale (app iconizzata o occupata): {e}")

    def salva_modifica_voce(self, params):
        from datetime import datetime
        v_data_str = params.get("vecchia_data", [""])[0]
        v_idx = int(params.get("vecchio_idx", ["0"])[0])
        provenienza = params.get("provenienza", ["/lista"])[0]
        n_data_html = params.get("nuova_data", [""])[0]
        cat = params.get("categoria", [""])[0]
        descr = params.get("descrizione", [""])[0]
        imp = float(params.get("importo", ["0"])[0])
        tipo = params.get("tipo", ["Uscita"])[0]
        d_vecchia_obj = datetime.strptime(v_data_str, "%d-%m-%Y").date()
        d_nuova_obj = datetime.strptime(n_data_html, "%Y-%m-%d").date()
        originale = self.spese[d_vecchia_obj][v_idx]
        if "ALL·" in str(originale[1]):
            try:
                if os.path.exists(REGISTRY_FILE):
                    with open(REGISTRY_FILE, 'r', encoding='utf-8') as rf:
                        r = json.load(rf)
                    o_s = d_vecchia_obj.strftime("%d%m%Y")
                    o_i = str(int(round(float(originale[2]) * 100)))
                    o_t = originale[3]
                    d_p = descr.replace("ALL·", "").strip()
                    def _sn(s, n=None):
                        s = re.sub(r'[^\w\.-]', '', s.strip().replace(' ', '_'))
                        return (s[:n] if n else s).upper()
                    n_s = d_nuova_obj.strftime("%d%m%Y")
                    n_i = str(int(round(imp * 100)))
                    n_f = f"{n_s}_{_sn(d_p, 30)}_{tipo}_{_sn(cat, 20)}_{n_i}.pdf"
                    for f_k in list(r.keys()):
                        if f_k.startswith(o_s) and o_i in f_k and o_t in f_k:
                            o_p = os.path.join(DOC_DIR, f_k)
                            n_p = os.path.join(DOC_DIR, n_f)
                            if f_k != n_f and os.path.exists(o_p):
                                os.rename(o_p, n_p)
                                val = r.pop(f_k)
                            else:
                                val = r[f_k]
                            val.update({
                                'data_raw':           n_s,
                                'categoria_esatta':   cat,
                                'descrizione_esatta': f"ALL· {d_p}",
                                'importo_raw':        int(n_i),
                                'tipo_esatto':        tipo
                            })
                            r[n_f] = val
                            break
                    with open(REGISTRY_FILE, 'w', encoding='utf-8') as rf:
                        json.dump(r, rf, indent=4, ensure_ascii=False)
            except Exception as e:
                print(f"[salva_modifica_voce] Errore aggiornamento registro: {e}")
        _imp_old = round(float(originale[2]), 2)
        _tipo_old = originale[3]
        _conto_form_raw = params.get("conto", None)
        if _conto_form_raw is not None:
            _conto_form = _conto_form_raw[0].strip()
            _nome_c_web = _conto_form if _conto_form and _conto_form != "(nessuno)" else ""
        else:
            _nome_c_web = campo(originale, "conto", "") or self._trova_conto_da_portafoglio(d_vecchia_obj, _imp_old, _tipo_old)
        _metodo_form = params.get("metodo", None)
        if _metodo_form is not None:
            _metodo_web = _metodo_form[0].strip()
        else:
            _metodo_web = campo(originale, "metodo_pagamento", "")
        _id_ric_old = originale[4] if len(originale) == 5 else None
        nuova_voce = SpesaEntry(
            cat, descr, imp, tipo,
            id_ricorrenza=_id_ric_old,
            id_spesa=campo(originale, "id_spesa", None),
            conto=_nome_c_web if _nome_c_web and _nome_c_web != "(nessuno)" else "",
            ora=campo(originale, "ora", ""),
            metodo_pagamento=_metodo_web,
            hashtag=campo(originale, "hashtag", []),
        )
        if d_vecchia_obj == d_nuova_obj:
            self.spese[d_nuova_obj][v_idx] = nuova_voce
        else:
            self.spese[d_vecchia_obj].pop(v_idx)
            if not self.spese[d_vecchia_obj]:
                del self.spese[d_vecchia_obj]
            if d_nuova_obj not in self.spese:
                self.spese[d_nuova_obj] = []
            self.spese[d_nuova_obj].append(nuova_voce)
        self.save_db()
        self.carica_db_web()
        if hasattr(self, 'refresh_gui'):
            self.refresh_gui()
        return provenienza
        
    def _refresh_portafoglio_se_aperto(self):
        if getattr(self, '_cruscotto_stato', 0) == 2:
            self.after(150, self.aggiorna_conti_canvas)
        try:
            if not (hasattr(self, '_saldo_popup') and self._saldo_popup and self._saldo_popup.winfo_exists()):
                return
            if hasattr(self, '_saldo_refresh'):
                self.after(0, self._saldo_refresh)
            if hasattr(self, '_saldo_refresh_movimenti'):
                self.after(0, self._saldo_refresh_movimenti)
            if hasattr(self, '_saldo_refresh_storico'):
                self.after(0, self._saldo_refresh_storico)
        except Exception:
            pass

    # Aggiorna tutti i componenti visivi della GUI se la finestra non è minimizzata
    def refresh_gui(self):
        try:
            if self.state() == 'iconic':
                return
        except:
                return
        try:
                anno, mese = None, None
                if hasattr(self, 'cal'):
                    try:
                            dt_cal = datetime.datetime.strptime(self.cal.get_date(), "%d-%m-%Y").date()
                            anno, mese = dt_cal.year, dt_cal.month
                    except:
                            pass
                self.update_stats()
                self.update_totalizzatore_anno_corrente(year=anno)
                self.update_totalizzatore_mese_corrente(year=anno, month=mese)
                self.update_spese_mese_corrente(year=anno, month=mese)
                self.colora_giorni_spese()
                self.aggiorna_monitoraggio_budget()
                self.refresh_documenti()
                self._refresh_portafoglio_se_aperto()
        except Exception:
                pass

    # Gestisci ripristino focus Blinker
    def _gestisci_ripristino_focus(self, event):
        if event.widget == self: 
            if hasattr(self, 'imp_entry'):
                self.after(0, self.imp_entry.focus_set)
            if ICO_SET_DATE:
                today_date = datetime.datetime.now().strftime("%d-%m-%Y") 
                self.data_spesa_var.set(today_date)
            if hasattr(self, 'ricorrenza_data_inizio'):
                self.ricorrenza_data_inizio.set(today_date)
            if hasattr(self, 'cal'):
                self.goto_today()
        self._reset_inattivita()
                     
    # Gestione Avanzata di Inattività e Minimizzazione (Auto-Lock)                 
    def _attiva_timer_inattivita(self):
        if hasattr(self, '_timer_inattivita') and self._timer_inattivita:
            self.after_cancel(self._timer_inattivita)
            self._timer_inattivita = None
        timeout = getattr(self, '_timeout_inattivita', 1200000)
        self._timer_inattivita = self.after(timeout, self._iconizza_finestra)
    def _reset_inattivita(self, cancel_countdown=False): 
        if cancel_countdown:
            if getattr(self, '_countdown_timer_id', None):
                self.after_cancel(self._countdown_timer_id)
                self._countdown_timer_id = None
            if getattr(self, '_countdown_splash', None):
                try: self._countdown_splash.destroy()
                except: pass
                self._countdown_splash = None
            self._attiva_timer_inattivita() 
            return 
        if self.state() == "iconic":
            self._attiva_timer_inattivita()
            return
        self._attiva_timer_inattivita()
    def _iconizza_finestra(self):
        if self.state() == "iconic":
            self._attiva_timer_inattivita()
            return
        if getattr(self, '_win_reg', None) and self._win_reg.winfo_exists():
            self._attiva_timer_inattivita()
            return    
        toplevel_active = False
        for widget in self.winfo_children():
            if isinstance(widget, tk.Toplevel) and widget.winfo_ismapped():
                if widget != getattr(self, '_countdown_splash', None):
                    toplevel_active = True
                    break
        if toplevel_active:
            self._attiva_timer_inattivita() 
            return
        self._mostra_avviso_countdown()
    def _finalizza_iconizzazione(self):
        if getattr(self, '_win_reg', None) and self._win_reg.winfo_exists():
                if getattr(self, '_countdown_splash', None):
                        try: self._countdown_splash.destroy()
                        except: pass
                        self._countdown_splash = None
                self._attiva_timer_inattivita()
                return
        if getattr(self, '_countdown_splash', None):
            try: self._countdown_splash.destroy()
            except: pass
            self._countdown_splash = None
        self.iconify()
        self.mostra_avviso_iconizzata()
        self._attiva_timer_inattivita()
    def mostra_avviso_iconizzata(self):
        splash = tk.Toplevel(self)
        splash.overrideredirect(True)
        splash.attributes("-topmost", True)
        splash.configure(
            bg=self.COLOR_WIDGET_BG, 
            highlightthickness=1, 
            highlightbackground=self.COLOR_HIGHLIGHT
        )
        width, height = 300, 145
        sw = splash.winfo_screenwidth()
        sh = splash.winfo_screenheight()
        splash.geometry(f"{width}x{height}+{(sw - width) // 2}+{(sh - height) // 2}")
        tk.Frame(splash, bg=self.COLOR_HIGHLIGHT, height=1).pack(fill="x", side="top")
        container = tk.Frame(splash, bg=self.COLOR_WIDGET_BG, padx=15, pady=10)
        container.pack(fill="both", expand=True)
        label = tk.Label(
            container,
            text=f"{NAME} v.{VERSION}\n\nFinestra minimizzata per inattività.",
            font=("Arial", 9, "bold"),
            fg=self.TEXT_COLOR,
            bg=self.COLOR_WIDGET_BG,
            justify="center"
        )
        label.pack(expand=True, fill="x")
        cvs_size = 36
        cvs = tk.Canvas(
            container, 
            width=cvs_size, 
            height=cvs_size, 
            bg=self.COLOR_WIDGET_BG, 
            highlightthickness=0, 
            bd=0
        )
        cvs.pack(side="top", pady=(5, 0))
        gemini_colors = ["#0055FF", "#AA00FF", "#FF0055", "#00C853"]
        state = {"angle": 0, "color_step": 0}
        def animate():
            if not splash.winfo_exists():
                return
            cvs.delete("all")
            state["angle"] = (state["angle"] + 12) % 360
            state["color_step"] += 1
            c_idx = (state["color_step"] // 8) % len(gemini_colors)
            color = gemini_colors[c_idx]
            center = cvs_size // 2
            r = 10
            rad = math.radians(state["angle"])
            x = center + r * math.cos(rad)
            y = center + r * math.sin(rad)
            cvs.create_arc(
                center-r, center-r, center+r, center+r, 
                start=state["angle"]-50, extent=50, 
                outline=color, width=3, style="arc"
            )
            cvs.create_oval(x-2, y-2, x+2, y+2, fill=color, outline=color)
            splash.after(25, animate)
        animate()
        splash.update()
        splash.after(1000, splash.destroy)
    def _mostra_avviso_countdown(self):
        if getattr(self, '_win_reg', None) and self._win_reg.winfo_exists():
                self._attiva_timer_inattivita()
                return
        for attr in ('_timer_inattivita', '_countdown_timer_id'):
            timer = getattr(self, attr, None)
            if timer:
                self.after_cancel(timer)
                setattr(self, attr, None)
        if self._countdown_splash:
            self._countdown_splash.destroy()
            self._countdown_splash = None
        splash = tk.Toplevel(self)
        splash.overrideredirect(True)
        splash.attributes("-topmost", True)
        splash.configure(
            bg=self.COLOR_WIDGET_BG,
            highlightthickness=1,
            highlightbackground=self.COLOR_HIGHLIGHT
        )
        width, height = 300, 140
        sw = splash.winfo_screenwidth()
        sh = splash.winfo_screenheight()
        splash.geometry(f"{width}x{height}+{(sw - width) // 2}+{(sh - height) // 2}")
        tk.Frame(splash, bg=self.COLOR_HIGHLIGHT, height=1).pack(fill="x", side="top")
        container = tk.Frame(splash, bg=self.COLOR_WIDGET_BG, padx=15, pady=10)
        container.pack(fill="both", expand=True)
        label = tk.Label(
            container,
            text="",
            font=("Arial", 9, "bold"),
            fg=self.TEXT_COLOR,
            bg=self.COLOR_WIDGET_BG,
            justify="center"
        )
        label.pack(expand=True, fill="x")
        cvs_size = 32
        cvs = tk.Canvas(container, width=cvs_size, height=cvs_size, bg=self.COLOR_WIDGET_BG, highlightthickness=0, bd=0)
        cvs.pack(side="top", pady=(5, 0))
        gemini_colors = ["#0055FF", "#AA00FF", "#FF0055", "#00C853"]
        state = {"angle": 0, "color_step": 0}
        def animate():
            if not splash.winfo_exists():
                return
            cvs.delete("all")
            state["angle"] = (state["angle"] + 12) % 360
            state["color_step"] += 1
            c_idx = (state["color_step"] // 8) % len(gemini_colors)
            color = gemini_colors[c_idx]
            center = cvs_size // 2
            r = 10
            rad = math.radians(state["angle"])
            x = center + r * math.cos(rad)
            y = center + r * math.sin(rad)
            cvs.create_arc(
                center-r, center-r, center+r, center+r, 
                start=state["angle"]-50, extent=50, 
                outline=color, width=3, style="arc"
            )
            cvs.create_oval(x-2, y-2, x+2, y+2, fill=color, outline=color)
            splash.after(25, animate)
        animate()
        splash.update()
        self._countdown_splash = splash
        self._countdown_label = label
        
        for widget in (splash, container, label, cvs):
            widget.bind("<Motion>", lambda e: self._reset_inattivita(cancel_countdown=True))
        self._aggiorna_countdown(self._countdown_delay)

    def _aggiorna_countdown(self, remaining_ms):
        if getattr(self, '_win_reg', None) and self._win_reg.winfo_exists():
                if self._countdown_splash:
                        try: self._countdown_splash.destroy()
                        except: pass
                        self._countdown_splash = None
                self._attiva_timer_inattivita()
                return
        if not self._countdown_splash:
            return
        if remaining_ms <= 0:
            self._finalizza_iconizzazione()
            return
        seconds = remaining_ms // 1000
        self._countdown_label.config(
            text=f"{NAME} v.{VERSION}\n\nNessuna attività rilevata.\nMinimizzazione tra {seconds} secondi."
        )
        self._countdown_timer_id = self.after(
            1000,
            lambda: self._aggiorna_countdown(remaining_ms - 1000)
        )
        
    def _iconizza_finestra_startup(self):
        if getattr(self, '_win_reg', None) and self._win_reg.winfo_exists():
                return 
        toplevel_active = False
        for widget in self.winfo_children():
            if isinstance(widget, tk.Toplevel) and widget.winfo_ismapped():
                toplevel_active = True
                break
        if toplevel_active:
            return 
        self.iconify()
        self.mostra_avviso_x()
        
    def _iconizza_finestra_x(self):
        if getattr(self, '_win_reg', None) and self._win_reg.winfo_exists():
                try:
                        self._on_close()
                except tk.TclError:
                        pass
                return
        stato = self.wm_state()
        if CLOSE and stato == "normal":
            try:
                self.save_db()
            except:
                pass
            if hasattr(self, "_splash_reg"):
                try:
                    if self._splash_reg.winfo_exists():
                        self._splash_reg.withdraw()
                except:
                    pass
            self.mostra_avviso_x()
            self.iconify()
        else:
            try:
                self._on_close()
            except tk.TclError:
                pass
    def mostra_avviso_x(self):
        splash = tk.Toplevel(self)
        splash.overrideredirect(True)
        splash.attributes("-topmost", True)
        splash.configure(
            bg=self.COLOR_WIDGET_BG,
            highlightthickness=1,
            highlightbackground=self.COLOR_HIGHLIGHT
        )
        width, height = 340, 160
        sw = splash.winfo_screenwidth()
        sh = splash.winfo_screenheight()
        splash.geometry(f"{width}x{height}+{(sw - width) // 2}+{(sh - height) // 2}")
        tk.Frame(splash, bg=self.COLOR_HIGHLIGHT, height=1).pack(fill="x", side="top")
        container = tk.Frame(splash, bg=self.COLOR_WIDGET_BG, padx=22, pady=10)
        container.pack(fill="both", expand=True)
        tk.Label(
            container,
            text=f"{NAME} — Attivo in background",
            font=("Arial", 10, "bold"),
            fg=self.TEXT_COLOR,
            bg=self.COLOR_WIDGET_BG
        ).pack(side="top")
        tk.Frame(container, bg=self.COLOR_HEADER_BG, height=1).pack(fill="x", pady=(8, 8))
        tk.Label(
            container,
            text="Tasto destro sull'icona Tray per chiudere\n"
                 "(disponibile solo quando l'app è minimizzata)",
            font=("Arial", 8),
            fg=self.TEXT_COLOR,
            bg=self.COLOR_WIDGET_BG,
            justify="center"
        ).pack(side="top")
        cvs_size = 36
        cvs = tk.Canvas(container, width=cvs_size, height=cvs_size, bg=self.COLOR_WIDGET_BG, highlightthickness=0, bd=0)
        cvs.pack(side="top", pady=(10, 0))
        gemini_colors = ["#0055FF", "#AA00FF", "#FF0055", "#00C853"]
        state = {"angle": 0, "color_step": 0}
        def animate():
            if not splash.winfo_exists():
                return
            cvs.delete("all")
            state["angle"] = (state["angle"] + 12) % 360
            state["color_step"] += 1
            c_idx = (state["color_step"] // 8) % len(gemini_colors)
            color = gemini_colors[c_idx]
            center = cvs_size // 2
            r = 10
            rad = math.radians(state["angle"])
            x = center + r * math.cos(rad)
            y = center + r * math.sin(rad)
            cvs.create_arc(
                center-r, center-r, center+r, center+r, 
                start=state["angle"]-50, extent=50, 
                outline=color, width=3, style="arc"
            )
            cvs.create_oval(x-2, y-2, x+2, y+2, fill=color, outline=color)
            splash.after(25, animate)
        animate()
        splash.update()
        splash.after(1000, splash.destroy)

    # Gestione Icona Applicazione con Fallback e Download Remoto
    def set_app_icon(self):
        import platform, os
        import PIL.Image, PIL.ImageTk
        resources_dir = os.path.join(DB_DIR, "resources")
        icon_path = os.path.join(resources_dir, "info_image.png")
        if os.path.exists(icon_path):
            try:
                pil_img = PIL.Image.open(icon_path)
                tk_icon = PIL.ImageTk.PhotoImage(pil_img)
                self.iconphoto(True, tk_icon)
                self.icon_ref = tk_icon
                if platform.system() == "Windows":
                    import ctypes, threading
                    try:
                        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"{NAME}")
                    except:
                        pass
                    def run_tray():
                        try:
                            tray_img = pil_img.resize((32, 32), PIL.Image.Resampling.LANCZOS).convert('RGBA')
                            self.tray_icon = pystray.Icon(f"{NAME}", tray_img, f"{NAME}")
                            self.tray_icon.run()
                        except ImportError:
                            print(f"Pystray mancante: pip install pystray")
                        except Exception as tray_e:
                            print(f"Errore Tray: {tray_e}")
                    threading.Thread(target=run_tray, daemon=True).start()
            except Exception as e:
                print(f"Errore caricamento icona: {e}")
        else:
            print(f"Icona non trovata: {icon_path}")

    # Implementazione di Effetti di Lampeggio Ricorsivo per Widget Tkinter
    def start_blinking(self, label):
        if hasattr(label, "_blinking_timer_id"):
            self.after_cancel(label._blinking_timer_id)
        label._is_blinking_on = True 
        label.state(['!disabled']) 
        self._blink_recursive(label)
    def _blink_recursive(self, label):
        try:
            label.winfo_exists()
        except:
            return
        if not hasattr(label, "_is_blinking_on"):
             label._is_blinking_on = True 
        label._is_blinking_on = not label._is_blinking_on
        if label._is_blinking_on:
            label.state(['!disabled'])
        else:
            label.state(['disabled'])
        try:
            interval = self.blinking_interval
            timer_id = self.after(interval, lambda: self._blink_recursive(label))
            label._blinking_timer_id = timer_id
        except Exception:
            print("Errore nel scheduling del timer. Controllare self.blinking_interval.")
            pass
    def stop_blinking(self, label):
        if hasattr(label, "_blinking_timer_id"):
            try:
                self.after_cancel(label._blinking_timer_id)
            except ValueError:
                pass 
            del label._blinking_timer_id
        try:
            label.state(['disabled'])
        except Exception:
            pass
        if hasattr(label, "_is_blinking_on"):
            del label._is_blinking_on

    # Implementazione di Effetti di Lampeggio Ricorsivo per Widget Totalizzatore mese/anno        
    def _global_blink_loop(self):
        if not hasattr(self, "blinking_widgets") or not self.blinking_widgets:
            self._blink_loop_active = False
            return
        self._blink_loop_active = True
        if not hasattr(self, "_blink_phase"):
            self._blink_phase = True
        self._blink_phase = not self._blink_phase
        color = "red" if self._blink_phase else "dodgerblue"
        for label in list(self.blinking_widgets):
            try:
                if label.winfo_exists():
                    label.config(foreground=color)
                else:
                    self.blinking_widgets.discard(label)
            except Exception:
                self.blinking_widgets.discard(label)
        interval = getattr(self, "blinking_interval", 500)
        self.after(interval, self._global_blink_loop)
    def start_blinking_colors(self, label):
        if not hasattr(self, "blinking_widgets"):
            self.blinking_widgets = set()
        self.blinking_widgets.add(label)
        if not getattr(self, "_blink_loop_active", False):
            self._global_blink_loop()
    def stop_blinking_colors(self, label):
        if hasattr(self, "blinking_widgets"):
            self.blinking_widgets.discard(label)
        try:
            if label.winfo_exists():
                label.config(foreground="dodgerblue")
        except Exception:
            pass

    def blink_label_colors(self, label, color1, color2, interval=500):
        self.stop_blink_label_colors(label)
        label._blink_colors_active = True
        label._blink_colors_phase = True
        def _loop():
            if not getattr(label, '_blink_colors_active', False):
                return
            try:
                if not label.winfo_exists():
                    return
            except Exception:
                return
            label._blink_colors_phase = not label._blink_colors_phase
            label.config(foreground=color1 if label._blink_colors_phase else color2)
            label._blink_colors_id = self.after(interval, _loop)
        _loop()
    def stop_blink_label_colors(self, label, final_color=None):
        label._blink_colors_active = False
        if hasattr(label, '_blink_colors_id'):
            try:
                self.after_cancel(label._blink_colors_id)
            except Exception:
                pass
        if final_color:
            try:
                if label.winfo_exists():
                    label.config(foreground=final_color)
            except Exception:
                pass
            
    # Carica tutte le icone PNG dalla cartella resources in self.icone_gui come PhotoImage, None se mancanti
    def setup_resources(self):
        from PIL import Image, ImageTk
        import os
        resources_dir = os.path.join(DB_DIR, "resources")
        self.map_icone = dict(MAP_ICONE)
        self.icone_gui = {}
        for nome in self.map_icone.keys():
                path = os.path.join(resources_dir, f"{nome}.png")
                if os.path.exists(path):
                        try:
                                img = Image.open(path)
                                self.icone_gui[nome] = ImageTk.PhotoImage(img)
                        except Exception:
                                self.icone_gui[nome] = None
                else:
                        self.icone_gui[nome] = None
                        
    # Gestione Budget Calcolo Mese/Anno
    def aggiorna_monitoraggio_budget(self, year=None, month=None):
        entrate_mese = 0.0
        entrate_anno = 0.0
        import datetime
        oggi = datetime.date.today()
        anno_curr = year if year is not None else oggi.year
        mese_curr = month if month is not None else oggi.month
        budget_m = getattr(self, 'budget_mensile', 0.0)
        budget_a = getattr(self, 'budget_annuale', 0.0)
        uscite_mese = 0.0
        uscite_anno = 0.0
        if self.budget_mensile > 0:
                self.lbl_titolo_target_m.grid()
                self.lbl_budget_mese.grid()
        else:
                self.lbl_titolo_target_m.grid_remove()
                self.lbl_budget_mese.grid_remove()
        if self.budget_annuale > 0:
                self.lbl_titolo_target_a.grid()
                self.lbl_budget_anno.grid()
        else:
                self.lbl_titolo_target_a.grid_remove()
                self.lbl_budget_anno.grid_remove()
        for giorno, entries in self.spese.items():
            if giorno.year == anno_curr:
                for entry in entries:
                    try:
                        tipo = str(entry[3]).lower()
                        importo = float(entry[2])
                    except (IndexError, ValueError):
                        continue
                    if not self.considera_ricorrenze_var.get() and giorno > oggi:
                        continue
                    if tipo == "uscita":
                        uscite_anno += importo
                        if giorno.month == mese_curr:
                            uscite_mese += importo
                    elif tipo == "entrata":
                        entrate_anno += importo
                        if giorno.month == mese_curr:
                            entrate_mese += importo
        rimanente_m = budget_m - uscite_mese + entrate_mese
        rimanente_a = budget_a - uscite_anno + entrate_anno
        self.lbl_budget_mese.config(
                text=f"{rimanente_m:,.2f} €",
                foreground=self.COLOR_GREEN if rimanente_m >= 0 else self.COLOR_RED
        )
        self.lbl_budget_anno.config(
                text=f"{rimanente_a:,.2f} €",
                foreground=self.COLOR_GREEN if rimanente_a >= 0 else self.COLOR_RED
        )
        if ANIMAZIONI:
            self._anima_label_valore(self.lbl_budget_mese, rimanente_m)
            self._anima_label_valore(self.lbl_budget_anno, rimanente_a)
            
    # Mostra i Tooltip Movimenti in TkCalendar 
    def mostra_tooltip(self, event):
        if self.tooltip_timer:
            self.after_cancel(self.tooltip_timer)
            self.tooltip_timer = None
        def safe_withdraw():
            if self.tooltip_win and self.tooltip_win.winfo_exists():
                self.tooltip_win.withdraw()
        if event.type == '11':
            safe_withdraw()
            return
        x_abs, y_abs = self.winfo_pointerxy()
        if hasattr(self, 'popup_rapido_attivo') and self.popup_rapido_attivo:
            try:
                if self.popup_rapido_attivo.winfo_exists():
                    safe_withdraw()
                    return
            except: pass
        x_abs, y_abs = self.winfo_pointerxy()
        try:
            widget = self.winfo_containing(x_abs, y_abs)
            if not widget or "!menu" in str(widget):
                safe_withdraw()
                return
            if "label" in str(widget) and widget.cget("text").isdigit():
                g = int(widget.cget("text"))
                m, a = self.cal.get_displayed_month()
                data = datetime.date(a, m, g)
                evs = self.cal.get_calevents(data)
                spese = "".join([self.cal.calevent_cget(i, "text") + "\n" for i in evs if self.cal.calevent_cget(i, "text") != "Oggi"]).strip()
                if spese:
                    testo = spese
                elif data == datetime.date.today():
                    testo = "Oggi"
                else:
                    testo = ""
                if testo:
                    self.tooltip_timer = self.after(1000, lambda: self.esegui_disegno(testo, x_abs, y_abs))
                    return
        except (KeyError, Exception):
            pass
        safe_withdraw()
        
    def esegui_disegno(self, testo, x, y):
        if not self.tooltip_win or not self.tooltip_win.winfo_exists():
            self.tooltip_win = tk.Toplevel(self)
            self.tooltip_win.overrideredirect(True)
            self.tooltip_win.withdraw()
        self.tooltip_win.withdraw()
        for c in self.tooltip_win.winfo_children(): 
            c.destroy()
        main_frame = tk.Frame(self.tooltip_win, bg=self.COLOR_TOOLTIP, 
                              relief="solid", borderwidth=1)
        main_frame.pack(fill="both", expand=True)
        righe = testo.split('\n')
        for riga in righe:
            if not riga.strip(): continue
            colore_testo = self.COLOR_TEXT_TOOLTIP
            if "-" in riga:
                colore_testo = self.COLOR_RED_SMOOTH
            elif "+" in riga:
                colore_testo = self.COLOR_GREEN_SMOOTH
            if riga.strip() == "Oggi":
                colore_testo = self.COLOR_TEXT_TOOLTIP
                fnt = ("Courier New", 9, "bold")
            else:
                fnt = ("Courier New", 9, "bold")
            tk.Label(
                main_frame, 
                text=riga, 
                fg=colore_testo, 
                bg=self.COLOR_TOOLTIP,
                font=fnt, 
                justify="left",
                padx=10, 
                pady=2
            ).pack(anchor="w")
        self.tooltip_win.geometry(f"+{x+15}+{y+10}")
        self.tooltip_win.update_idletasks()
        self.tooltip_win.deiconify()
        self.tooltip_win.attributes("-topmost", True)
        
    def applica_ricorsivo_tooltip(self, widget):
        widget.bind("<Motion>", self.mostra_tooltip)
        widget.bind("<Leave>", self.mostra_tooltip)
        for child in widget.winfo_children():
            self.applica_ricorsivo_tooltip(child)
                              
    # Riproduci suono conferma        
    def riproduci_beep(self):
        if not BEEP:
            return
        def _suona():
            try:
                if sys.platform.startswith("win"):
                    import winsound
                    winsound.MessageBeep(winsound.MB_OK)
                    return
            except:
                pass
            try:
                import numpy as np
                import wave, tempfile, os
                sr = 44100
                t = np.linspace(0, 0.3, int(sr * 0.3))
                onda = (np.sin(2 * np.pi * 880 * t) * 0.5 +
                        np.sin(2 * np.pi * 1108 * t) * 0.3 +
                        np.sin(2 * np.pi * 1320 * t) * 0.15)
                fade = np.exp(-8 * t)
                onda = (onda * fade * 32767).astype(np.int16)
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    nome = f.name
                with wave.open(nome, "w") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(sr)
                    wf.writeframes(onda.tobytes())
                if sys.platform.startswith("linux"):
                    subprocess.run(["aplay", nome], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif sys.platform == "darwin":
                    subprocess.run(["afplay", nome], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                os.unlink(nome)
            except:
                pass
        threading.Thread(target=_suona, daemon=True).start()

    # Refresh Remoto per Sincronizzazione Condivisa        
    def refresh_remote(self):
        try:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Segnale ricevuto: avvio ricaricamento dati...")
            self.load_db()
            self.mostra_treeview_statistiche()
            if hasattr(self, 'update_stats'):
                self.update_stats()
            self.update_totalizzatore_anno_corrente()
            self.update_totalizzatore_mese_corrente()
            self.update_spese_mese_corrente()
            self.colora_giorni_spese()
            self.aggiorna_monitoraggio_budget()
            self._controlla_sforamento_budget(mostra_toast=False)
            if hasattr(self, 'pdf_window') and self.pdf_window.winfo_exists():
                tabella = getattr(self, 'tabella_documenti', None)
                funzione_load = getattr(self, 'funzione_carica_documenti', None)
                if tabella and funzione_load:
                    self.filtri_avanzati = {}
                    self.after(800, lambda: funzione_load(tabella, {}))
            if hasattr(self, '_win_doc_pers') and self._win_doc_pers.winfo_exists():
                if hasattr(self, '_doc_pers_load_tree'):
                    self.after(800, self._doc_pers_load_tree)
            self.update_idletasks()
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Refresh completato con successo!")
        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore durante il refresh: {e}")
            
    def _esegui_sincro_thread(self):
        from datetime import datetime
        try:
            self.avvia_sincronizzazione()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Sincronizzazione completata con successo.")
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Sincro fallita: {e}")
        
    # Refresh Gui dopo mezzanotte
    def _auto_refresh_mezzanotte(self):
        adesso = datetime.datetime.now()
        mezzanotte = (adesso + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=5, microsecond=0)
        ms = int((mezzanotte - adesso).total_seconds() * 1000)
        def _scatta():
            self.refresh_gui()
            self.show_toast(f"Nuovo giorno! {datetime.date.today().strftime('%d/%m/%Y')}", duration=4000)
            self._auto_refresh_mezzanotte()
        self.after(ms, _scatta)
        
    # Orologio DashBoard    
    def _tick_orologio(self):
        adesso = datetime.datetime.now()
        self.lbl_orologio.config(text=f"  {adesso.strftime('%d/%m/%Y  %H:%M:%S')}")
        if adesso.hour == 0 and adesso.minute == 0 and adesso.second == 0:
            self.refresh_gui()
        self.after(1000, self._tick_orologio)
 
    # Verfica statistiche
    def verify_environment_update(self, tipo_install="UNKNOWN", rating=0):
        import requests, platform
        try:
                u1 = "68747470733a2f2f646f63732e676f6f676c65"
                u2 = "2e636f6d2f666f726d732f642f652f3146414970514c53635849524b7736786b5f503645347366"
                u3 = "49324e5f4342524342766a46426561777664536e7961464163797172646d4f512f666f726d526573706f6e7365"
                f1, f2, f3 = "656e74", "72792e323235", "393234343632"
                target = bytes.fromhex(u1 + u2 + u3).decode()
                f_id = bytes.fromhex(f1 + f2 + f3).decode()
                uid = "ID_" + _get_device_id()
                rating_str = f"{rating}/5" if rating else "?"
                os_info = f"{platform.system()} {platform.release()}"
                num_mov = sum(len(v) for v in self.spese.values()) if hasattr(self, 'spese') else 0
                ver_str = f" v{VERSION}" if VERSION not in tipo_install else ""
                data_str = f"{uid} - {tipo_install}{ver_str} - OS={os_info} - MOV={num_mov}"
                payload = {f_id: data_str, "draftResponse": '[]', "pageHistory": "0"}
                requests.post(target, data=payload, timeout=7)
                return True
        except:
                return False

    def verify_environment(self):
        flag_versione = os.path.join(DB_DIR, ".key_reg")
        ha_licenza = os.path.exists(os.path.join(DB_DIR, "._reg.json"))
        uid = _get_device_id()
        if os.path.exists(flag_versione):
            _trial_file_chk = os.path.join(DB_DIR, "._trial.json")
            _reg_file_chk   = os.path.join(DB_DIR, "._reg.json")
            ha_files = os.path.exists(_trial_file_chk) or os.path.exists(_reg_file_chk)
            try:
                contenuto = open(flag_versione).read().strip()
                if VERSION not in contenuto:
                    vecchia = contenuto.split("|")[1] if "|" in contenuto else "?"
                    tipo = f"UPGRADE_{vecchia}_to_{VERSION}"
                    try:
                        with open(flag_versione, "w") as f:
                            f.write(f"{uid}|{VERSION}|UPGRADE")
                    except:
                        pass
                    threading.Thread(
                        target=lambda: self.verify_environment_update(tipo),
                        daemon=True).start()
            except:
                pass
            if ha_files:
                return
        if ha_licenza:
            try:
                with open(flag_versione, "w") as f:
                    f.write(f"{uid}|{VERSION}|NEW INSTALL")
            except:
                pass
            threading.Thread(
                target=lambda: self.verify_environment_update("NEW INSTALL"),
                daemon=True).start()
            return
        _trial_solo = os.path.join(DB_DIR, "._trial.json")
        if os.path.exists(_trial_solo):
            try:
                with open(flag_versione, "w") as f:
                    f.write(f"{uid}|{VERSION}|NEW INSTALL")
            except:
                pass
            self.after(100, self._c_r)
            return
        if getattr(self, '_in_error_state', False):
            return    
        if self.wm_state() == "iconic":
            self.deiconify()
        resources_dir = os.path.join(DB_DIR, "resources")
        logo_path = os.path.join(resources_dir, "info_image.png")
        risposta = [False]
        splash = tk.Toplevel(self)
        self._splash_reg = splash
        splash.overrideredirect(True)
        splash.attributes("-topmost", True)
        w, h = 450, 400
        x = (splash.winfo_screenwidth() // 2) - (w // 2)
        y = (splash.winfo_screenheight() // 2) - (h // 2)
        splash.geometry(f"{w}x{h}+{x}+{y}")
        splash.configure(bg=self.COLOR_BACKGROUND)
        splash.configure(
            highlightthickness=2,
            highlightbackground="#0078D7",
            highlightcolor="#0078D7"
        )
        splash.grab_set()
        if os.path.exists(logo_path):
            try:
                img_logo = Image.open(logo_path).convert("RGBA")
                img_logo = img_logo.resize((200, 100), Image.Resampling.LANCZOS)
                self._reg_logo_img = ImageTk.PhotoImage(img_logo)
                tk.Label(splash, image=self._reg_logo_img,
                         bg=self.COLOR_BACKGROUND, bd=0).pack(pady=(20, 5))
            except Exception as e:
                print(f"Errore rendering logo: {e}")

        _testo_benvenuto = (
            f"Grazie per aver installato {NAME}!\n\n"
            "Spese, documenti, scadenze e fondo risparmio in un'unica app:\n"
            "tutto in locale, senza cloud e senza pubblicità.\n\n"
            "L'import automatico con AI riconosce estratti e fatture da solo.\n\n"
            "Hai a disposizione una prova gratuita di 10 giorni,\n"
            "con accesso completo a tutte le funzionalità del programma.\n\n"
            "Al termine del periodo di prova sarà necessaria la registrazione\n"
            "per continuare ad utilizzare l'applicazione."
        )
        splash.pack_propagate(False)
        toolbar = tk.Frame(splash, bg=self.COLOR_BACKGROUND)
        toolbar.pack(side=tk.BOTTOM, pady=12)
        lbl_benvenuto = tk.Label(
            splash,
            text="",
            font=("Arial", 9, "bold"),
            fg=self.TEXT_COLOR,
            bg=self.COLOR_BACKGROUND,
            justify="center",
            wraplength=380,
            anchor="n",
            height=8
        )
        lbl_benvenuto.pack(padx=20, pady=20, fill="both", expand=True)
        def _scrivi_testo(indice=0):
            if indice > len(_testo_benvenuto):
                return
            lbl_benvenuto.config(text=_testo_benvenuto[:indice])
            splash.after(10, lambda: _scrivi_testo(indice + 1))
        splash.after(150, _scrivi_testo)
        def _si():
            risposta[0] = True
            splash.grab_release()
            splash.destroy()
            from cryptography.fernet import Fernet
            import json
            _f = Fernet(base64.urlsafe_b64encode(hashlib.sha256("OrbitaCasa|GestioneSpese|2026|∞".encode()).digest()))
            _trial_file = os.path.join(DB_DIR, "._trial.json")
            if not os.path.exists(_trial_file):
                primo = datetime.date.today().isoformat()
                json.dump({"primo": _f.encrypt(primo.encode()).decode()}, open(_trial_file, "w"))
            try:
                with open(flag_versione, "w") as f:
                    f.write(f"{uid}|{VERSION}|NEW INSTALL")
            except:
                pass
            self.aggiorna_titolo_finestra()
            self.after(100, self._c_r)
            self.after(800, self._avvia_tutorial)
        def _no():
            risposta[0] = False
            splash.grab_release()
            splash.destroy()
            self.destroy()
        btn_si = tk.Label(toolbar, image=self.icone_gui.get("check"), text=" Ok, procedi",
                          compound="left", fg=self.COLOR_GREEN_SMOOTH, cursor="hand2",
                          font=("Arial", 9, "bold"), bg=self.COLOR_BACKGROUND)
        btn_si.pack(side=tk.LEFT, padx=10)
        btn_si.bind("<Button-1>", lambda e: _si())

        btn_no = tk.Label(toolbar, image=self.icone_gui.get("chiudi"), text=" Non ora",
                          compound="left", fg=self.TEXT_COLOR, cursor="hand2",
                          font=("Arial", 9, "bold"), bg=self.COLOR_BACKGROUND)
        btn_no.pack(side=tk.LEFT, padx=10)
        btn_no.bind("<Button-1>", lambda e: _no())
        self.wait_window(splash)
        if risposta[0]:
            threading.Thread(
                target=lambda: self.verify_environment_update("NEW INSTALL"),
                daemon=True).start()

    def apri_registrazione(self):
        if hasattr(self, '_win_reg') and self._win_reg.winfo_exists():
            self._win_reg.lift()
            return
        device_id = _get_device_id()
        win = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
        self._win_reg = win
        win.title("Registrazione")
        win.withdraw()
        win.resizable(False, False)
        win.transient(self)
        win.update_idletasks()
        w, h = 500, 240
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
        win.geometry(f"{w}x{h}+{x}+{y}")
        win.deiconify()
        win.focus_force()
        win.grab_set()
        _reg_file = os.path.join(DB_DIR, "._reg.json")
        if os.path.exists(_reg_file):
            try:
                import json
                from cryptography.fernet import Fernet
                raw = json.load(open(_reg_file))["key"]
                if raw == "__MASTER__":
                    testo_scad = "Licenza attiva — illimitata"
                else:
                    _f = Fernet(base64.urlsafe_b64encode(hashlib.sha256("OrbitaCasa|GestioneSpese|2026|∞".encode()).digest()))
                    payload = _f.decrypt(raw.encode()).decode()
                    dev, scadenza = payload.split("|")
                    testo_scad = f"Licenza attiva — scadenza: {datetime.date.fromisoformat(scadenza).strftime('%d/%m/%Y')}" if scadenza != "9999-12-31" else "Licenza attiva — illimitata"
            except Exception:
                testo_scad = "Licenza non valida"
        else:
            testo_scad = "Nessuna licenza registrata"
        tk.Label(win, text=testo_scad, bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                 font=("Arial", 10, "italic")).pack(pady=(5,0))
        img_mobile = self.icone_gui.get("mobile")
        tk.Label(win, image=img_mobile, text=" Il tuo Device ID:", compound="left",
                 bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR, font=("Arial", 10)).pack(pady=(20, 5))
        img_key = self.icone_gui.get("api_key")
        frame_id = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
        frame_id.pack()
        entry_id = ttk.Entry(frame_id, width=30, font=("Arial", 11, "bold"),
                             justify="center")
        entry_id.pack(side="left", padx=5)
        entry_id.insert(0, device_id)
        entry_id.config(state="readonly")
        btn_copia = tk.Label(frame_id, text="📋", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                             cursor="hand2", font=("Arial", 12))
        btn_copia.pack(side="left")
        btn_copia.bind("<Button-1>", lambda e: self.clipboard_clear() or self.clipboard_append(device_id))
        tk.Label(win, image=img_key, text=" Inserisci la tua KEY:", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR, compound="left").pack(pady=(15,5))
        entry_key = ttk.Entry(win, width=60, justify="center")
        entry_key.pack(padx=20)
        win.after(100, entry_key.focus_set)
        def _sync_iconify(e):
            if self.state() == 'iconic':
                win.withdraw()
            else:
                win.deiconify()
                win.grab_set()
                win.focus_force()
                win.after(100, entry_key.focus_set)
        self.bind("<Map>", _sync_iconify)
        self.bind("<Unmap>", _sync_iconify)
        frame_key_btn = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
        frame_key_btn.pack(pady=(2,0))
        btn_copia = tk.Label(frame_key_btn, text="📋 Copia", bg=self.COLOR_TOPLEVEL,
                             fg=self.TEXT_COLOR, cursor="hand2", font=("Arial", 9))
        btn_copia.pack(side="left", padx=5)
        btn_copia.bind("<Button-1>", lambda e: self.clipboard_clear() or self.clipboard_append(entry_key.get()))
        btn_incolla = tk.Label(frame_key_btn, text="📌 Incolla", bg=self.COLOR_TOPLEVEL,
                               fg=self.TEXT_COLOR, cursor="hand2", font=("Arial", 9))
        btn_incolla.pack(side="left", padx=5)
        btn_incolla.bind("<Button-1>", lambda e: entry_key.delete(0, "end") or entry_key.insert(0, self.clipboard_get()))
        def _rinnova():
            corpo = (
                f"Salve,\n\nVorrei ottenere/rinnovare la mia licenza OrbitaCasa.\n\n"
                f"Licenza: {self.topic_unico}\n"
                f"Versione: {VERSION}\n"
                f"Utente: {self.current_folder}\n\n"
                f"In attesa di istruzioni.\n\nGrazie"
            )
            url = "mailto:helporbitacasa@gmail.com?subject=" + urllib.parse.quote("Licenza OrbitaCasa") + "&body=" + urllib.parse.quote(corpo)
            webbrowser.open(url)
        def conferma():
            import json
            key = entry_key.get().strip()
            if not key:
                self.show_toast("Inserisci una KEY prima di procedere.", duration=3000)
                return
            if hashlib.sha256(key.encode()).hexdigest() == SYNC_H:
                json.dump({"key": "__MASTER__"}, open(os.path.join(DB_DIR, "._reg.json"), "w"))
                threading.Thread(
                    target=lambda: self.verify_environment_update("LICENSED_MASTER"),
                    daemon=True
                ).start()
                self.bind("<Map>", self._gestisci_ripristino_focus)
                self.unbind("<Unmap>")
                self._c_r()
                self.show_toast("Registrazione completata.", duration=3000)
                win.destroy()
                if hasattr(self, '_attiva_timer_inattivita'):
                        self._attiva_timer_inattivita()
                return
            try:
                from cryptography.fernet import Fernet
                _f = Fernet(base64.urlsafe_b64encode(
                    hashlib.sha256("OrbitaCasa|GestioneSpese|2026|∞".encode()).digest()))
                payload = _f.decrypt(key.encode()).decode()
                dev, scadenza = payload.split("|")
                if dev != device_id:
                    self.show_toast("Key non valida per questo dispositivo.", duration=3000)
                    entry_key.delete(0, "end")
                    return
                if datetime.date.today() > datetime.date.fromisoformat(scadenza):
                    self.show_toast("Key scaduta.", duration=3000)
                    entry_key.delete(0, "end")
                    return
                json.dump({"key": key}, open(os.path.join(DB_DIR, "._reg.json"), "w"))
                threading.Thread(
                    target=lambda sc=scadenza: self.verify_environment_update(
                        f"LICENSED_{datetime.date.fromisoformat(sc).strftime('%d/%m/%Y')}"
                    ),
                    daemon=True
                ).start()
                self.bind("<Map>", self._gestisci_ripristino_focus)
                self.unbind("<Unmap>")
                self.show_toast("Registrazione completata.", duration=3000)
                self._c_r()
                win.destroy()
                if hasattr(self, '_attiva_timer_inattivita'):
                        self._attiva_timer_inattivita()
            except Exception:
                self.show_toast("Key non valida.", duration=3000)
                entry_key.delete(0, "end")
        entry_key.bind("<Return>",   lambda e: conferma())
        entry_key.bind("<KP_Enter>", lambda e: conferma())
        img_check = self.icone_gui.get("check")
        img_chiudi = self.icone_gui.get("chiudi")
        def _mk_btn(parent, img, testo, cmd):
            f = tk.Frame(parent, bg=self.COLOR_TOPLEVEL, cursor="hand2")
            tk.Label(f, image=img, bg=self.COLOR_TOPLEVEL, cursor="hand2").pack(side="left")
            tk.Label(f, text=testo, bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                     font=("Arial", 10, "bold"), cursor="hand2").pack(side="left")
            f.bind("<Button-1>", lambda e: cmd())
            for w in f.winfo_children():
                w.bind("<Button-1>", lambda e: cmd())
            return f
        frame_btn = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
        frame_btn.pack(pady=15)
        _mk_btn(frame_btn, img_check,  "Registra", conferma).pack(side="left", padx=5)
        _mk_btn(frame_btn, img_check,  "Ottieni",  _rinnova).pack(side="left", padx=5)
        def _chiudi():
            self.bind("<Map>", self._gestisci_ripristino_focus)
            self.unbind("<Unmap>")
            win.destroy()
            if hasattr(self, '_attiva_timer_inattivita'):
                    self._attiva_timer_inattivita()
            if not os.path.exists(os.path.join(DB_DIR, "._reg.json")):
                self._on_close()
        _mk_btn(frame_btn, img_chiudi, "Chiudi", _chiudi).pack(side="left", padx=5)
        _mk_btn(frame_btn, img_chiudi, "Esci",   lambda: (self.bind("<Map>", self._gestisci_ripristino_focus), self.unbind("<Unmap>"), win.destroy(), self._on_close())).pack(side="left", padx=5)
        win.bind("<Escape>", lambda e: _chiudi())
        win.protocol("WM_DELETE_WINDOW", _chiudi)
        win.img_check  = img_check
        win.img_chiudi = img_chiudi
        
    def _licenza_valida(self):
        return getattr(self, '_lic_ok', False)
        
    def _c_r(self):
        self._lic_ok = False
        from cryptography.fernet import Fernet
        import json
        _f = Fernet(base64.urlsafe_b64encode(hashlib.sha256("OrbitaCasa|GestioneSpese|2026|∞".encode()).digest()))
        _trial_file = os.path.join(DB_DIR, "._trial.json")
        _reg_file = os.path.join(DB_DIR, "._reg.json")
        _key_reg = os.path.join(DB_DIR, ".key_reg")
        if os.path.exists(_reg_file):
            try:
                with open(_reg_file) as fh:
                    raw = json.load(fh)["key"]
                if raw == "__MASTER__":
                    self._lic_ok = True
                    self.aggiorna_titolo_finestra()
                    return
                payload = _f.decrypt(raw.encode()).decode()
                dev, scadenza = payload.split("|")
                if dev != _get_device_id():
                    os.remove(_reg_file)
                    self.show_toast("Licenza non valida.", duration=4000)
                    self.after(4100, self.destroy)
                    return
                if datetime.date.today() > datetime.date.fromisoformat(scadenza):
                    os.remove(_reg_file)
                    self.show_toast("Licenza scaduta.", duration=4000)
                    self.after(4100, self.destroy)
                    return
                self._lic_ok = True
                self.aggiorna_titolo_finestra()
                return
            except Exception:
                os.remove(_reg_file)
                self.show_toast("Licenza Corrotta.", duration=4000)
                self.after(4100, self.destroy)
                return
        try:
            if not os.path.exists(_trial_file):
                return
            with open(_trial_file) as fh:
                primo = datetime.date.fromisoformat(_f.decrypt(json.load(fh)["primo"].encode()).decode())
            giorni_rimasti = 10 - (datetime.date.today() - primo).days
            if giorni_rimasti <= 0:
                self.show_toast("Periodo di prova scaduto. Registrati.", duration=4000)
                self.after(4100, self.apri_registrazione)
                return
            self._lic_ok = True
            if giorni_rimasti <= 3:
                self.show_toast(f"Periodo di prova: {giorni_rimasti} giorni rimasti.", duration=3000)
            self.aggiorna_titolo_finestra()
        except Exception:
            self._in_error_state = True
            if os.path.exists(_trial_file):
                os.remove(_trial_file)
            if os.path.exists(_key_reg):
                os.remove(_key_reg)
            self.show_toast("Licenza Trial Corrotta.", duration=4000)
            self.after(4100, self.apri_registrazione)
            return
            
    # Debug Log
    def abilita_log_tkinter(self):
        import traceback
        import datetime
        import os
        def gestore_errori_tkinter(type, value, tb):
            error_info = "".join(traceback.format_exception(type, value, tb))
            percorso_log = os.path.join(DB_DIR, "error_log.txt")                
            try:
                if os.path.exists(percorso_log) and os.path.getsize(percorso_log) > 50 * 1024:
                    with open(percorso_log, "w", encoding="utf-8") as f_clear:
                        f_clear.write(f"--- LOG RESETTATO PER DIMENSIONI ECCESSIVE ({datetime.datetime.now()}) ---\n")
                with open(percorso_log, "a", encoding="utf-8") as f:
                    ora = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                    f.write(f"⚠️ ERRORE CALLBACK ({ora})\n")
                    f.write(f"{error_info}\n")
                    f.write("-" * 50 + "\n\n")
            except:
                    pass
            print(error_info)
        self.report_callback_exception = gestore_errori_tkinter
        
    # Aggiorna Meteo Labels
    def _genera_frames_sole(self, n=12, size=(16, 16)):
        from PIL import Image, ImageTk; import math
        p = os.path.normpath(os.path.join(PATH_LOCALE, "db", "resources", "meteo_sole.png"))
        if not os.path.exists(p): return []
        try:
            b = Image.open(p).convert("RGBA").resize(size, Image.LANCZOS)
            return [ImageTk.PhotoImage(b.rotate(360/n*i, resample=Image.BICUBIC)) for i in range(n)]
        except Exception as e: print(f"[Meteo] {e}"); return []
    def _genera_frames_temporale(self, n=8, size=(16, 16)):
        from PIL import Image, ImageTk, ImageEnhance; import math
        p = os.path.normpath(os.path.join(PATH_LOCALE, "db", "resources", "meteo_temporale.png"))
        if not os.path.exists(p): return []
        try:
            b = Image.open(p).convert("RGBA").resize(size, Image.LANCZOS)
            return [ImageTk.PhotoImage(ImageEnhance.Brightness(b).enhance(0.5 + 0.5*math.sin(math.pi*i/(n-1)))) for i in range(n)]
        except Exception as e: print(f"[Meteo] {e}"); return []
    def _loop_animazione(self, wid):
        info = self._animazioni.get(wid)
        if not info: return
        w = info["widget"]
        try:
            if not w.winfo_exists(): self.ferma_animazione_meteo(w); return
        except: return
        f = info["frames"][info["idx"] % len(info["frames"])]
        w.config(image=f); w.image = f
        info["idx"] += 1
        info["job"] = self.after(info["interval"], self._loop_animazione, wid)
    def avvia_animazione_meteo(self, widget, tipo, interval_ms=None):
        if not hasattr(self, "_animazioni"): self._animazioni = {}
        self.ferma_animazione_meteo(widget)
        if not ANIMAZIONI:
            from PIL import Image, ImageTk
            p = os.path.normpath(os.path.join(PATH_LOCALE, "db", "resources", f"meteo_{tipo}.png"))
            if not os.path.exists(p): return
            try:
                img = ImageTk.PhotoImage(Image.open(p).convert("RGBA").resize((16, 16), Image.LANCZOS))
                widget.config(image=img); widget.image = img
            except Exception as e: print(f"[Meteo] {e}")
            return
        frames = self._genera_frames_sole() if tipo == "sole" else self._genera_frames_temporale()
        if not frames: return
        interval = interval_ms or (80 if tipo == "sole" else 120)
        self._animazioni[id(widget)] = {"widget": widget, "frames": frames, "idx": 0, "interval": interval, "job": None}
        self._loop_animazione(id(widget))
    def ferma_animazione_meteo(self, widget):
        if not hasattr(self, "_animazioni"): return
        info = self._animazioni.pop(id(widget), None)
        if info and info["job"]: self.after_cancel(info["job"])
    def aggiorna_meteo_saldo(self, saldo_mese, saldo_anno):
        tm = "sole" if saldo_mese > 0 else "temporale"; cm = "darkgreen" if saldo_mese > 0 else "red"
        for lbl in (self.lbl_titolo_mese, self.lbl_titolo_analisi):
            lbl.config(fg=cm); self.avvia_animazione_meteo(lbl, tm)
        ta = "sole" if saldo_anno > 0 else "temporale"; ca = "darkgreen" if saldo_anno > 0 else "red"
        p = os.path.normpath(os.path.join(PATH_LOCALE, "db", "resources", f"meteo_{ta}.png"))
        if os.path.exists(p):
            try: ic = tk.PhotoImage(file=p); self.iconphoto(True, ic); self.icon_ref = ic
            except tk.TclError: print(f"Errore icona taskbar: {p}")
        self.lbl_titolo_anno.config(fg=ca); self.avvia_animazione_meteo(self.lbl_titolo_anno, ta)
    def aggiorna_meteo_avanzato_auto(self, mode):
        try:
            if not hasattr(self, 'stats_table') or not self.stats_table.winfo_exists(): return
            tot = 0.0
            for riga in self.stats_table.get_children():
                v = self.stats_table.item(riga)["values"]
                if not v or len(v) < 2: continue
                try:
                    raw, tipo = (str(v[3]), str(v[4]).lower()) if mode == "giorno" else (str(v[1]), str(v[2]).lower())
                    num = float(raw.replace('€','').replace('.','').replace(',','.').strip())
                    tot += -abs(num) if "usc" in tipo or "spes" in tipo else abs(num)
                except: continue
            if hasattr(self, 'lbl_titolo_avanzato'):
                t = "sole" if tot >= 0 else "temporale"
                self.lbl_titolo_avanzato.config(fg="darkgreen" if tot >= 0 else "red")
                self.avvia_animazione_meteo(self.lbl_titolo_avanzato, t)
        except Exception as e: print(f"Errore Meteo: {e}")
                          
    # Timing Backup Incrementale threading
    def pianifica_backup_orario(self):
        from datetime import datetime
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Avvio backup automatico...")
            threading.Thread(target=self._esegui_backup_json).start()
            threading.Thread(target=self.backup_documenti).start()
            threading.Thread(target=self.backup_documenti_personali).start()
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Errore durante il trigger del backup: {e}")
        # Backup Ogni 12 ore
        self.after(43200000, self.pianifica_backup_orario)
              
    # Snapshot automatico DB post-backup
    def _esegui_snapshot_db(self):
        import zipfile, glob
        try:
            cartella_backup = os.path.join(BASE_DIR, "backup")
            os.makedirs(cartella_backup, exist_ok=True)
            data = datetime.datetime.today().strftime("%d-%m-%Y")
            nome_snapshot = f"{data}-snapshot_db.zip"
            percorso_snapshot = os.path.join(cartella_backup, nome_snapshot)
            nome_cartella_db = os.path.basename(DB_DIR)
            with zipfile.ZipFile(percorso_snapshot, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
                for root, _, fnames in os.walk(DB_DIR):
                    for fn in fnames:
                        percorso_completo = os.path.join(root, fn)
                        percorso_nello_zip = os.path.join(nome_cartella_db, os.path.relpath(percorso_completo, DB_DIR))
                        zf.write(percorso_completo, percorso_nello_zip)
            snapshots = sorted(
                glob.glob(os.path.join(cartella_backup, "*-snapshot_db.zip")),
                key=os.path.getmtime,
                reverse=True
            )
            for vecchio in snapshots[MAX_BACKUP:]:
                try:
                    os.remove(vecchio)
                except Exception:
                    pass
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Snapshot DB salvato: {nome_snapshot}")
        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore snapshot DB: {e}")        
               
    # Backup Incrementale threading
    def _esegui_backup_json(self):
        from datetime import datetime
        lista_file = [
            DB_FILE, DATI_FILE, UTENZE_DB, REGISTRY_FILE,
            PW_FILE, MEM_CAT, CONFIG_FILE, RIMANDA_FILE, 
            PROMEMORIA_FILE, SUPERMERCATI_DB, DEFAULT_API, CONTROLLO_F_M,
            PARTECIPANTI, FAIRSHARE_STATE, PORTAFOGLIO_AZIONI, DIETA_FILE,
            CUSTOM_FILE, PESO_FILE, FABB_FILE, PEDOMETRO_FILE, STUDIO_CLIENTI,
            STUDIO_APPUNTAMENTI, STUDIO_PRESTAZIONI, STUDIO_FATTURE, STUDIO_EMITTENTE,
            STUDIO_CASSA, STUDIO_MAGAZZINO, IMMOBIL_FILE, FR_FILE, PORTAFOGLIO_BANCARIO,
            SCHEDULE_FILE, VEICOLI_FILE
        ]
        file_copiati = 0
        for f in lista_file:
            try:
                if os.path.exists(f):
                    backup_incrementale(f)
                    file_copiati += 1
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Errore backup nel thread per {f}: {e}")
        self._esegui_snapshot_db()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Backup Database terminato ({file_copiati} file salvati).")

def _get_device_id():
    import platform, hashlib, subprocess
    try:
        sys = platform.system()
        if sys == "Windows":
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography")
            raw = winreg.QueryValueEx(key, "MachineGuid")[0]
        elif sys == "Darwin":
            out = subprocess.check_output(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                stderr=subprocess.DEVNULL).decode()
            for line in out.splitlines():
                if "IOPlatformUUID" in line:
                    raw = line.split('"')[-2]
                    break
        else:
            with open("/etc/machine-id") as f:
                raw = f.read().strip()
    except:
        import uuid
        raw = str(uuid.getnode())
    return hashlib.md5(raw.encode()).hexdigest()[:12]
    
# Backup Incrementale
def backup_incrementale(file_path, cartella_backup=None, max_backup=None):
    if max_backup is None:
        max_backup = MAX_BACKUP
    if cartella_backup is None:
        cartella_backup = os.path.join(BASE_DIR, "backup")
    if not os.path.exists(file_path):
        return
    os.makedirs(cartella_backup, exist_ok=True)
    nome_completo = os.path.basename(file_path)
    data = datetime.datetime.today().strftime("%d-%m-%Y") 
    backup_file_name = f"{data}-{nome_completo}"
    backup_file_path = os.path.join(cartella_backup, backup_file_name)
    shutil.copy2(file_path, backup_file_path)
    stringa_filtro = f"-{nome_completo}"
    files_to_check = [f for f in os.listdir(cartella_backup) if f.endswith(stringa_filtro)]
    if not files_to_check:
        return
    def get_sort_key(filename):
        date_str = filename[:10] 
        return datetime.datetime.strptime(date_str, "%d-%m-%Y")
    files_ordinati = sorted(
        files_to_check,
        key=get_sort_key,
        reverse=True 
    )
    files_da_cancellare = files_ordinati[max_backup:]
    if files_da_cancellare:
        for f in files_da_cancellare:
            os.remove(os.path.join(cartella_backup, f))

_APP_REF = None
def _rb():
    try:
        import requests
        uid = _get_device_id()
        bn_cache = os.path.join(DB_DIR, "._bn_cache")
        URL = "68747470733a2f2f646f63732e676f6f676c652e636f6d2f7370726561647368656574732f642f652f32504143582d3176546562377770477874356972357347714d5044616145314e574a5a545a566c364e625f5258355144456a4738356e324e6f4247737141316f684a6b333169716e616163456870426e61435457482d2f7075623f6f75747075743d637376"
        url = bytes.fromhex(URL).decode()
        CACHE_MAX_AGE = 24 * 3600
        bn_local = []
        cache_valida = False
        if os.path.exists(bn_cache):
            if time.time() - os.path.getmtime(bn_cache) < CACHE_MAX_AGE:
                cache_valida = True
                with open(bn_cache) as f:
                    bn_local = [r.strip() for r in f.read().splitlines() if r.strip()]
        if uid in bn_local:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] BAN ATTIVATO")
            show_warning_popup(
                titolo="⛔  LICENZA BLOCCATA",
                corpo=f"L'utilizzo di {NAME} è stato sospeso.\nContatta l'assistenza per ulteriori informazioni.",
                riga_extra="helporbitacasa@gmail.com"
            )
            sys.exit(1)
        def _blocca_per_ban():
            try:
                if _APP_REF is not None:
                    _APP_REF.destroy()
            except Exception:
                pass
            show_warning_popup(
                titolo="⛔  LICENZA BLOCCATA",
                corpo=f"L'utilizzo di {NAME} è stato sospeso.\nContatta l'assistenza per ulteriori informazioni.",
                riga_extra="helporbitacasa@gmail.com"
            )
            os._exit(1)
        def _aggiorna_cache():
            try:
                resp = requests.get(url, timeout=5)
                bn = [r.strip() for r in resp.text.splitlines()[1:] if r.strip()]
                with open(bn_cache, "w") as f:
                    f.write("\n".join(bn))
                if uid in bn:
                    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] BAN ATTIVATO (background)")
                    if _APP_REF is not None:
                        _APP_REF.after(0, _blocca_per_ban)
                    else:
                        _blocca_per_ban()
            except Exception:
                pass
        if not cache_valida:
            threading.Thread(target=_aggiorna_cache, daemon=True).start()
    except Exception:
        pass
def _rc():
    try:
        E_H_B = "449111d929705d02f7467d1922064a4958baa7a391cdd2a83c5d612c89552cad"
        righe = open(__file__, "rb").readlines()
        contenuto = b"".join(r for r in righe if b"E_H_B" not in r)
        _h = hashlib.sha256(contenuto).hexdigest()
        if _h != E_H_B:
            show_warning_popup(
                    titolo="⛔  VIOLAZIONE DI INTEGRITÀ",
                    corpo=f"{NAME} ha rilevato una modifica non autorizzata del file.\nL'esecuzione è stata bloccata per motivi di sicurezza.",
                    riga_extra="Reinstalla l'applicazione da una fonte ufficiale."
                )
            sys.exit(1)
    except Exception:
        pass
                
# Installazione Automatica e Gestione Condizionale delle Dipendenze Python
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*urllib3.*")
warnings.filterwarnings("ignore", message=".*chardet.*")
warnings.filterwarnings("ignore", message=".*charset_normalizer.*")
_sw_win    = None 
_sw_canvas = None 
_sw_segmenti = []
_sw_pct    = None 
_sw_cur    = None 
_sw_labels = []
_sw_step   = 0 

_SW_PKGS = [
    ("tkcalendar",   "Calendario date"),
    ("requests",     "Connessione internet"),
    ("flask",        "Server web"),
    ("google-genai", "Intelligenza artificiale"),
    ("Pillow",       "Gestione immagini"),
    ("PyMuPDF",      "Lettura PDF"),
    ("pystray",      "Icona nella barra"),
    ("yfinance",     "Mercati finanziari"),
    ("segno",        "Generazione QR code"),
    ("cryptography", "Sicurezza SSL"),
    ("pywin32",      "Stampa su Windows"),
    ("tkinterdnd2",  "Trascina documenti"),
]
_SW_TOTAL = len(_SW_PKGS)
_SW_BAR_W = 360
_sw_root = None
def _sw_crea():
    global _sw_win, _sw_canvas, _sw_segmenti, _sw_pct, _sw_cur, _sw_labels, _sw_step, _sw_root
    if _sw_win is not None:
        return
    _sw_root = tk.Tk()
    _sw_root.withdraw()
    W, H = 444, 334
    win = tk.Toplevel(_sw_root)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.configure(bg="#61AFEF")
    x = (win.winfo_screenwidth()  // 2) - (W // 2)
    y = (win.winfo_screenheight() // 2) - (H // 2)
    win.geometry(f"{W}x{H}+{x}+{y}")
    inner = tk.Frame(win, bg="#1E1E2E")
    inner.place(x=2, y=2, width=W-4, height=H-4)
    tk.Label(win,
             text=f"{NAME} – Setup",
             font=("Arial", 13, "bold"),
             fg="#FFFFFF", bg="#1E1E2E").pack(pady=(18, 2))
    tk.Label(win,
             text="Verifica e installazione dipendenze in corso…",
             font=("Arial", 9),
             fg="#FFFFFF", bg="#1E1E2E").pack()
    cv = tk.Canvas(win,
                   width=_SW_BAR_W, height=14,
                   bg="#1E1E2E", highlightthickness=0)
    cv.pack(pady=(14, 2))
    cv.create_rectangle(0, 0, _SW_BAR_W, 14, fill="#2D2D3F", outline="")
    segmenti = []
    for i in range(_SW_BAR_W):
        t = i / _SW_BAR_W
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
        seg = cv.create_rectangle(i, 0, i+1, 14, fill=f"#{r:02x}{g:02x}{b:02x}", outline="", state="hidden")
        segmenti.append(seg)
    pct_lbl = tk.Label(win, text="0%",
                       font=("Arial", 9, "bold"),
                       fg="#61AFEF", bg="#1E1E2E")
    pct_lbl.pack(pady=(2, 6))
    cur_lbl = tk.Label(win, text="",
                       font=("Arial", 9, "italic"),
                       fg="#ABB2BF", bg="#1E1E2E", width=50)
    cur_lbl.pack(pady=(0, 10))
    grid = tk.Frame(win, bg="#1E1E2E")
    grid.pack(anchor="center")
    grid.columnconfigure(0, minsize=180)
    grid.columnconfigure(1, minsize=180)
    labels = []
    for i, (pkg, desc) in enumerate(_SW_PKGS):
        r, c = divmod(i, 2)
        lbl = tk.Label(grid,
                       text=f"○  {desc}",
                       font=("Arial", 9),
                       fg="#4B5263", bg="#1E1E2E",
                       anchor="w", width=22)
        lbl.grid(row=r, column=c, sticky="w", pady=1, padx=(0, 8))
        labels.append(lbl)
    _sw_win      = win
    _sw_canvas   = cv
    _sw_segmenti = segmenti
    _sw_pct      = pct_lbl
    _sw_cur      = cur_lbl
    _sw_labels   = labels
    _sw_step     = 0
    win.update()

def _sw_avanza(nome_pkg):
    global _sw_step
    _sw_crea()
    idx_corrente = next((i for i, (p, _) in enumerate(_SW_PKGS) if p == nome_pkg), None)
    desc_corrente = _SW_PKGS[idx_corrente][1] if idx_corrente is not None else nome_pkg
    for i in range(idx_corrente if idx_corrente is not None else 0):
        _sw_labels[i].config(text=f"✓  {_SW_PKGS[i][1]}", fg="#98C379")
    if idx_corrente is not None:
        _sw_labels[idx_corrente].config(text=f"▶  {desc_corrente}", fg="#61AFEF")
    step = idx_corrente if idx_corrente is not None else 0
    soglia = int(_SW_BAR_W * step / _SW_TOTAL)
    for idx, seg in enumerate(_sw_segmenti):
        _sw_canvas.itemconfig(seg, state="normal" if idx < soglia else "hidden")
    _sw_pct.config(text=f"{int(step / _SW_TOTAL * 100)}%")
    _sw_cur.config(text=f"Installazione: {desc_corrente}…", fg="#FFFFFF")
    _sw_step = idx_corrente + 1 if idx_corrente is not None else _sw_step + 1
    _sw_win.update()

def _sw_chiudi():
    global _sw_win, _sw_root
    if _sw_win is None:
        if _sw_root is not None:
            _sw_root.destroy()
            _sw_root = None
        return
    if _sw_step > 0:
        idx = _sw_step - 1
        if idx < len(_sw_labels):
            _sw_labels[idx].config(text=f"✓  {_SW_PKGS[idx][1]}", fg="#98C379")
    for seg in _sw_segmenti:
        _sw_canvas.itemconfig(seg, state="normal")
    _sw_pct.config(text="100%")
    _sw_cur.config(text="✅  Tutte le dipendenze sono pronte.")
    _sw_win.update()
    import time; time.sleep(0.9)
    _sw_win.withdraw()
    _sw_win.destroy()
    _sw_win = None
    import time; time.sleep(0.3)
    if _sw_root is not None:
        try:
            _sw_root.destroy()
        except Exception:
            pass
        _sw_root = None
        
def _pip_install(pkg):
    import platform as _pl
    kwargs = dict(stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
    if _pl.system() == "Windows":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    proc = subprocess.Popen([sys.executable, "-m", "pip", "install", pkg], **kwargs)
    while proc.poll() is None:
        if _sw_win is not None:
            try:
                if _sw_win.winfo_exists():
                    _sw_win.update()
            except Exception:
                pass
        import time; time.sleep(0.1)
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, "pip")
    import importlib; importlib.invalidate_caches()

def install_tkcalendar():
    try:
        from tkcalendar import Calendar, DateEntry
        return Calendar, DateEntry
    except ImportError:
        _sw_avanza("tkcalendar")
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 'tkcalendar' non trovato. Installazione in corso...")
        try:
            _pip_install("tkcalendar")
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 'tkcalendar' installato con successo.")
            from tkcalendar import Calendar, DateEntry
            return Calendar, DateEntry
        except subprocess.CalledProcessError as e:
            print(f"ERRORE: Installazione di 'tkcalendar' fallita. Dettagli: {e}")
            sys.exit(1)
        except ImportError:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ERRORE: Impossibile importare 'tkcalendar' dopo l'installazione.")
            sys.exit(1)
Calendar, DateEntry = install_tkcalendar()

def install_requests():
    try:
        import requests
        from requests.exceptions import ConnectionError, RequestException
        return requests, ConnectionError, RequestException
    except ImportError:
        _sw_avanza("requests")
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 'requests' non trovato. Installazione in corso...")
        try:
            _pip_install("requests")
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 'requests' installato con successo.")
            import requests
            from requests.exceptions import ConnectionError, RequestException
            return requests, ConnectionError, RequestException
        except (subprocess.CalledProcessError, ImportError) as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ERRORE CRITICO: 'requests' fallito: {e}")
            sys.exit(1)
requests, ConnectionError, RequestException = install_requests()

def install_flask():
    try:
        import flask
        from werkzeug.serving import make_server
        return flask, make_server
    except ImportError:
        _sw_avanza("flask")
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 'flask' non trovato. Installazione in corso...")
        try:
            _pip_install("flask")
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 'flask' installato con successo.")
            import flask
            from werkzeug.serving import make_server
            return flask, make_server
        except (subprocess.CalledProcessError, ImportError) as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ERRORE CRITICO: 'flask' fallito: {e}")
            sys.exit(1)
flask_module, werkzeug_make_server = install_flask()

def install_genai():
    import importlib.util
    if importlib.util.find_spec("google") is None:
        _sw_avanza("google-genai")
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 'google-genai' non trovato. Installazione in corso...")
        try:
            _pip_install("google-genai")
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 'google-genai' installato con successo.")
        except (subprocess.CalledProcessError, ImportError) as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ERRORE CRITICO: 'google-genai' fallito: {e}")
            sys.exit(1)

class _LazyGenai:
    _genai = None
    _types = None
    def _load(self):
        if _LazyGenai._genai is None:
            from google import genai as _g
            from google.genai import types as _ty
            _LazyGenai._genai = _g
            _LazyGenai._types = _ty
    def Client(self, **kw):
        self._load()
        return _LazyGenai._genai.Client(**kw)
    def __getattr__(self, name):
        self._load()
        return getattr(_LazyGenai._genai, name)

class _LazyTypes:
    def __getattr__(self, name):
        if _LazyGenai._genai is None:
            _LazyGenai()._load()
        return getattr(_LazyGenai._types, name)
class _DummyAPIError(Exception):
    pass

install_genai()
genai_client = _LazyGenai()
genai = genai_client
types = _LazyTypes()
APIError = _DummyAPIError

def install_pillow():
    try:
        from PIL import Image, ImageTk
        return Image, ImageTk
    except ImportError:
        _sw_avanza("Pillow")
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 'Pillow' non trovato. Installazione in corso...")
        try:
            _pip_install("Pillow")
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 'Pillow' installato con successo.")
            from PIL import Image, ImageTk
            return Image, ImageTk
        except subprocess.CalledProcessError as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ERRORE: 'Pillow' fallito: {e}")
            sys.exit(1)
        except ImportError:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ERRORE: Impossibile importare 'Pillow' dopo l'installazione.")
            sys.exit(1)
Image, ImageTk = install_pillow()

def install_pymupdf():
    try:
        import fitz
        return fitz
    except ImportError:
        _sw_avanza("PyMuPDF")
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 'PyMuPDF' non trovato. Installazione in corso...")
        try:
            _pip_install("pymupdf")
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 'PyMuPDF' installato con successo.")
            import fitz
            return fitz
        except subprocess.CalledProcessError as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ERRORE: 'PyMuPDF' fallito: {e}")
            sys.exit(1)
        except ImportError:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ERRORE: Impossibile importare 'fitz' dopo l'installazione.")
            sys.exit(1)
fitz = install_pymupdf()

def install_pystray():
    if platform.system() != "Windows":
        return None
    try:
        import pystray  # type: ignore
        return pystray
    except ImportError:
        _sw_avanza("pystray")
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 'pystray' non trovato. Installazione su Windows...")
        try:
            _pip_install("pystray")
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 'pystray' installato con successo.")
            import pystray  # type: ignore
            return pystray
        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ERRORE: 'pystray' fallito: {e}")
            return None
pystray = install_pystray()

def install_yfinance():
    import importlib.util
    if importlib.util.find_spec("yfinance") is None:
        _sw_avanza("yfinance")
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 'yfinance' non trovato. Installazione in corso...")
        try:
            _pip_install("yfinance")
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 'yfinance' installato con successo.")
        except (subprocess.CalledProcessError, ImportError) as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ERRORE CRITICO: 'yfinance' fallito: {e}")
            sys.exit(1)

class _LazyYFinance:
    _yf = None
    def _load(self):
        if _LazyYFinance._yf is None:
            import yfinance as _y
            _LazyYFinance._yf = _y
    def Ticker(self, *a, **kw):
        self._load()
        return _LazyYFinance._yf.Ticker(*a, **kw)
    def download(self, *a, **kw):
        self._load()
        return _LazyYFinance._yf.download(*a, **kw)
    def Search(self, *a, **kw):
        self._load()
        return _LazyYFinance._yf.Search(*a, **kw)
    def __getattr__(self, name):
        self._load()
        return getattr(_LazyYFinance._yf, name)
install_yfinance()
yf = _LazyYFinance()

def install_segno():
    try:
        import segno
        return segno
    except ImportError:
        _sw_avanza("segno")
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 'segno' non trovato. Installazione in corso...")
        try:
            _pip_install("segno")
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 'segno' installato con successo.")
            import segno
            return segno
        except subprocess.CalledProcessError as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ERRORE: 'segno' fallito: {e}")
            sys.exit(1)
        except ImportError:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ERRORE: Impossibile importare 'segno' dopo l'installazione.")
            sys.exit(1)
segno = install_segno()

def install_cryptography():
    try:
        import cryptography
        return cryptography
    except ImportError:
        _sw_avanza("cryptography")
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 'cryptography' non trovato. Installazione in corso...")
        try:
            _pip_install("cryptography")
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 'cryptography' installato con successo.")
            import cryptography
            return cryptography
        except subprocess.CalledProcessError as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ERRORE: 'cryptography' fallito: {e}")
            return None
        except ImportError:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ERRORE: Impossibile importare 'cryptography' dopo l'installazione.")
            return None
crypto_module = install_cryptography()

def install_win32_libraries():
    if platform.system() != "Windows":
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Sistema non Windows: pywin32 non necessario.")
        return None, None, None
    try:
        import win32print  # type: ignore
        import win32api    # type: ignore
        import win32con    # type: ignore
        return win32print, win32api, win32con
    except ImportError:
        _sw_avanza("pywin32")
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 'pywin32' non trovato. Installazione in corso...")
        try:
            _pip_install("pywin32")
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 'pywin32' installato con successo.")
            import win32print  # type: ignore
            import win32api    # type: ignore
            import win32con    # type: ignore
            return win32print, win32api, win32con
        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ERRORE: 'pywin32' fallito: {e}")
            return None, None, None
win32print, win32api, win32con = install_win32_libraries()

def install_tkinterdnd2():
    try:
        from tkinterdnd2 import DND_FILES, TkinterDnD as _TkDnD
        return DND_FILES, _TkDnD, True
    except ImportError:
        _sw_avanza("tkinterdnd2")
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 'tkinterdnd2' non trovato. Installazione in corso...")
        try:
            _pip_install("tkinterdnd2")
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 'tkinterdnd2' installato con successo.")
            from tkinterdnd2 import DND_FILES, TkinterDnD as _TkDnD
            return DND_FILES, _TkDnD, True
        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ATTENZIONE: 'tkinterdnd2' non disponibile: {e}")
            return None, None, False
_DND_FILES, _TkDnD_Class, _HAS_DND = install_tkinterdnd2()
if _HAS_DND and _TkDnD_Class:
    GestioneSpese.__bases__ = (_TkDnD_Class.Tk,)

_sw_chiudi()

# Controllo dell'Istanza Unica (Single Instance Check) Tramite Mutex o File Lock
def check_single_instance():
    global _lock_file_handle
    global _mutex_handle
    _lock_file_handle = None 
    _mutex_handle = None
    if sys.platform.startswith("win"):
        import ctypes
        LAST_ERROR_ALREADY_EXISTS = 183
        mutex_name = "Global\\OrbitaCasaWeb_Mutex_34A5B6C7"
        mutex = ctypes.windll.kernel32.CreateMutexW(None, True, mutex_name)
        if ctypes.windll.kernel32.GetLastError() == LAST_ERROR_ALREADY_EXISTS:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Un'altra istanza è già in esecuzione! (Windows)")
            show_warning_popup(
                    spinner=True, spinner_testo=f"{NAME} \nL'applicazione è già in esecuzione",
                    bg="#000000", accent="#61AFEF", width=400, height=150
                )
            sys.exit(1)
        _mutex_handle = mutex
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Avvio riuscito. Acquisito il Mutex (Windows).")
        return
    else:
        import fcntl
        lock_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        lock_file_path = os.path.join(lock_dir, 'Orbita_Casa.lock')
        try:
            lock_file = open(lock_file_path, 'a')
            fcntl.lockf(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            _lock_file_handle = lock_file
            lock_file.write(f"{os.getpid()}\n") 
            lock_file.flush()
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Avvio riuscito. Acquisito il lock (Linux/Unix).")
            return
        except BlockingIOError:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Un'altra istanza è già in esecuzione! (Linux/Unix)")
            show_warning_popup(
                    spinner=True, spinner_testo=f"{NAME} \nL'applicazione è già in esecuzione",
                    bg="#000000", accent="#61AFEF", width=400, height=150
                )
            sys.exit(1)
        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore critico durante la creazione del lock: {e}")
            sys.exit(1)

# Legge config.json fondendolo con DEFAULT_CONFIG, crea il file se mancante e riallinea le chiavi se cambiate
def aggiorna_configurazione_globale():
    final_config = DEFAULT_CONFIG.copy()
    if not os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(final_config, f, indent=4)
        except Exception:
            pass
        return final_config
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            config_data = json.loads(content) if content else {}
        for key, value in config_data.items():
            if key in DEFAULT_CONFIG:
                final_config[key] = value
        if set(config_data.keys()) != set(DEFAULT_CONFIG.keys()):
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(final_config, f, indent=4)
    except Exception as e:
        print(f"Errore lettura config.json: {e}")
    return final_config

# Gestione Dati Partecipanti
def _leggi_gestore_partecipa():
    try:
        if os.path.exists(PARTECIPANTI):
            with open(PARTECIPANTI, 'r', encoding='utf-8') as _f:
                _raw = json.load(_f)
            if isinstance(_raw, dict):
                return _raw.get("gestore_partecipa", True)
    except Exception:
        pass
    return True
def _scrivi_gestore_partecipa(valore):
    try:
        raw = []
        if os.path.exists(PARTECIPANTI):
            with open(PARTECIPANTI, 'r', encoding='utf-8') as _f:
                raw = json.load(_f)
        if isinstance(raw, list):
            raw = {"gestore_partecipa": valore, "partecipanti": raw}
        elif isinstance(raw, dict):
            raw["gestore_partecipa"] = valore
        with open(PARTECIPANTI, 'w', encoding='utf-8') as _f:
            json.dump(raw, _f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Errore salvataggio gestore_partecipa: {e}")
    
# DataBase Condiviso
def ascolta_aggiornamenti_rete(app_istanza):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    port = UDP_PORT_1
    try:
        sock.bind(('', port))
    except Exception:
        port = UDP_PORT_2
        try:
            sock.bind(('', port))
        except Exception:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ERRORE: Entrambe le porte ({UDP_PORT_1}, {UDP_PORT_2}) sono occupate!")
            return
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Ricevitore attivo sulla porta: {port}")
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            messaggio = data.decode('utf-8')
            if "REFRESH_NOW" in messaggio:
                parti = messaggio.split("|")
                mittente_id = parti[1] if len(parti) > 1 else ""
                if mittente_id == str(app_istanza.SESSION_ID):
                    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Rimbalzo locale ignorato (ID: {mittente_id})")
                    continue
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Segnale da ALTRO PC ({addr}): avvio ricaricamento...")
                app_istanza.after(100, app_istanza.refresh_remote)
        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore ricezione: {e}")
# Scarica Logo
def scarica_logo():
    base_resources_dir = os.path.join(DB_DIR, "resources")
    if not os.path.exists(base_resources_dir):
        os.makedirs(base_resources_dir)
    logo_path = os.path.join(base_resources_dir, "info_image.png")
    if os.path.exists(logo_path):
        return
    import requests
    for tentativo in range(3):
        try:
            r = requests.get(URL_LOGO, timeout=15)
            if r.status_code == 200:
                with open(logo_path, 'wb') as f:
                    f.write(r.content)
                return
            else:
                print(f"[{time.strftime('%H:%M:%S')}] Download logo ({tentativo+1}/3): HTTP {r.status_code}")
        except Exception as _e:
            print(f"[{time.strftime('%H:%M:%S')}] Download logo ({tentativo+1}/3): {_e}")
        
# Scarica da internet le icone emoji e il logo mancanti nella cartella resources mostrando uno splash con barra di avanzamento            
_PALETTE_BOOT = {
    "CHIARO": {
        "bg": "#FFFFFF", "widget_bg": "#F9F9F9", "text": "black",
        "text_secondary": "#333333", "highlight": "#007ACC",
        "success": "green", "tooltip": "#F9F9F9",
    },
    "MATERIAL": {
        "bg": "#20232A", "widget_bg": "#2A273F", "text": "white",
        "text_secondary": "#ABB2BF", "highlight": "#61AFEF",
        "success": "#98C379", "tooltip": "#4B4673",
    },
    "BLU": {
        "bg": "#B3E5FC", "widget_bg": "#B3E5FC", "text": "#002F6C",
        "text_secondary": "#004B8D", "highlight": "#0091EA",
        "success": "#2ed573", "tooltip": "#E1F5FE",
    },
    "OBSIDIAN": {
        "bg": "#000000", "widget_bg": "#000000", "text": "white",
        "text_secondary": "#ABB2BF", "highlight": "#61AFEF",
        "success": "#98C379", "tooltip": "#1A1A1A",
    },
    "GOLD": {
        "bg": "#0A0800", "widget_bg": "#0D0A00", "text": "#F5E6C8",
        "text_secondary": "#D4B896", "highlight": "#C9A84C",
        "success": "#98C379", "tooltip": "#1A1200",
    },
}

def _leggi_tema_boot():
    tema_nome = "OBSIDIAN"
    try:
        c_file = os.path.join(DB_DIR, "config.json")
        if os.path.exists(c_file):
            with open(c_file, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            tema_nome = cfg.get("thema", "OBSIDIAN")
    except Exception:
        pass
    return _PALETTE_BOOT.get(tema_nome, _PALETTE_BOOT["OBSIDIAN"])

def inizializza_risorse_icone(lista_icone):
    import os, time, tkinter as tk
    import requests
    from PIL import Image, ImageTk
    base_resources_dir = os.path.join(DB_DIR, "resources")
    if not os.path.exists(base_resources_dir):
        os.makedirs(base_resources_dir)
    icone_mancanti = [
        (n, c[0]) for n, c in lista_icone
        if not os.path.exists(os.path.join(base_resources_dir, f"{n}.png"))]
    if not icone_mancanti:
        return
    tema = _leggi_tema_boot()
    sp = tk.Tk()
    sp.overrideredirect(True)
    sp.attributes("-topmost", True)
    width, height = 380, 160
    x = (sp.winfo_screenwidth() // 2) - (width // 2)
    y = (sp.winfo_screenheight() // 2) - (height // 2)
    sp.geometry(f"{width}x{height}+{x}+{y}")
    sp.configure(bg=tema["bg"], highlightthickness=2, highlightbackground=tema["highlight"])
    logo_path = os.path.join(base_resources_dir, "info_image.png")
    if os.path.exists(logo_path):
        try:
            img_logo = Image.open(logo_path).convert("RGBA")
            img_logo = img_logo.resize((90, 45), Image.Resampling.LANCZOS)
            sp._logo_img = ImageTk.PhotoImage(img_logo)
            tk.Label(sp, image=sp._logo_img, bg=tema["bg"], bd=0).pack(pady=(15, 0))
            tk.Label(sp, text=f"{NAME} – Risorse", font=("Arial", 12, "bold"),
                     fg=tema["highlight"], bg=tema["bg"]).pack(pady=(2, 0))
        except Exception as e:
            print(f"Errore rendering logo risorse: {e}")
    else:
        tk.Label(sp, text=f"{NAME} – Risorse", font=("Arial", 12, "bold"),
                 fg=tema["highlight"], bg=tema["bg"]).pack(pady=(15, 0))
    lbl_status = tk.Label(sp, text="Preparazione risorse...", font=("Arial", 9),
                           fg=tema["text_secondary"], bg=tema["bg"])
    lbl_status.pack(pady=5)
    totale_task = len(icone_mancanti)
    BAR_W, BAR_H = 300, 10
    bar_cv = tk.Canvas(sp, width=BAR_W, height=BAR_H, bg=tema["widget_bg"], highlightthickness=0)
    bar_cv.pack(pady=6)
    _segmenti = []
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
        seg = bar_cv.create_rectangle(i, 0, i+1, BAR_H, fill=f"#{r:02x}{g:02x}{b:02x}", outline="", state="hidden")
        _segmenti.append(seg)
    sp.update()
    def aggiorna_bar(valore):
        soglia = int(BAR_W * max(0.0, min(valore, totale_task)) / totale_task)
        for idx, seg in enumerate(_segmenti):
            bar_cv.itemconfig(seg, state="normal" if idx < soglia else "hidden")
        sp.update()
    url_b = "https://fonts.gstatic.com/s/e/notoemoji/latest/{code}/512.png"
    for i, (nome, code) in enumerate(icone_mancanti):
        path = os.path.join(base_resources_dir, f"{nome}.png")
        lbl_status.config(text=f"Download: {nome}.png")
        aggiorna_bar(i + 1)
        scaricata_ok = False
        for tentativo in range(3):
            try:
                r = requests.get(url_b.format(code=code), timeout=8)
                if r.status_code == 200:
                    with open(path, 'wb') as f:
                        f.write(r.content)
                    sz = (20, 20) if "_B" in nome else (16, 16)
                    with Image.open(path) as img:
                        img.resize(sz, Image.Resampling.LANCZOS).save(path)
                    scaricata_ok = True
                    break
                else:
                    print(f"[{time.strftime('%H:%M:%S')}] Icona '{nome}' ({tentativo+1}/3): HTTP {r.status_code}")
            except Exception as _e:
                print(f"[{time.strftime('%H:%M:%S')}] Icona '{nome}' ({tentativo+1}/3): {_e}")
        if not scaricata_ok:
            lbl_status.config(text=f"Fallito: {nome}.png")
            sp.update()
            time.sleep(0.5)
    lbl_status.config(text="✅ Risorse pronte !", fg=tema["success"])
    aggiorna_bar(totale_task)
    time.sleep(1)
    sp.destroy()

#  Sincronizzazione Moduli
def _boot_pulisci_pycache():
    for radice, cartelle, _file in os.walk(PATH_LOCALE):
        if "__pycache__" in cartelle:
            shutil.rmtree(os.path.join(radice, "__pycache__"), ignore_errors=True)
def _boot_crea_splash_barra(testo_iniziale):
    try:
        tema = _leggi_tema_boot()

        sp = tk.Tk()
        sp.overrideredirect(True)
        sp.attributes("-topmost", True)
        width, height = 380, 160
        x = (sp.winfo_screenwidth() // 2) - (width // 2)
        y = (sp.winfo_screenheight() // 2) - (height // 2)
        sp.geometry(f"{width}x{height}+{x}+{y}")
        sp.configure(bg=tema["bg"], highlightthickness=2, highlightbackground=tema["highlight"])
        logo_path = os.path.join(DB_DIR, "resources", "info_image.png")
        if os.path.exists(logo_path):
            try:
                from PIL import Image, ImageTk
                img_logo = Image.open(logo_path).convert("RGBA")
                img_logo = img_logo.resize((90, 45), Image.Resampling.LANCZOS)
                sp._boot_logo_img = ImageTk.PhotoImage(img_logo)
                tk.Label(sp, image=sp._boot_logo_img, bg=tema["bg"], bd=0).pack(pady=(10, 0))
            except Exception as e:
                print(f"Errore rendering logo splash moduli: {e}")
        tk.Label(sp, text=f"{NAME} - Moduli", font=("Arial", 12, "bold"),
         fg=tema["highlight"], bg=tema["bg"]).pack(pady=(5, 0))
        lbl_status = tk.Label(sp, text=testo_iniziale, font=("Arial", 9),
                               fg=tema["text_secondary"], bg=tema["bg"])
        lbl_status.pack(pady=5)
        BAR_W, BAR_H = 300, 10
        bar_cv = tk.Canvas(sp, width=BAR_W, height=BAR_H, bg=tema["widget_bg"], highlightthickness=0)
        bar_cv.pack(pady=6)
        _segmenti = []
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
            seg = bar_cv.create_rectangle(i, 0, i + 1, BAR_H, fill=f"#{r:02x}{g:02x}{b:02x}",
                                           outline="", state="hidden")
            _segmenti.append(seg)
        sp.update()
        def aggiorna_bar(percento, testo=None):
            soglia = int(BAR_W * max(0.0, min(percento, 100.0)) / 100.0)
            for idx, seg in enumerate(_segmenti):
                bar_cv.itemconfig(seg, state="normal" if idx < soglia else "hidden")
            if testo is not None:
                lbl_status.config(text=testo)
            sp.update()
        return sp, lbl_status, aggiorna_bar
    except Exception:
        return None, None, None
def _boot_git_blob_sha1(percorso_locale):
    with open(percorso_locale, "rb") as f:
        dati = f.read()
    intestazione = f"blob {len(dati)}\0".encode("utf-8")
    return hashlib.sha1(intestazione + dati).hexdigest()
def _boot_lista_moduli_remoti():
    api_url = (f"https://api.github.com/repos/{REPO_OWNER}/"
               f"{REPO_NAME}/contents/moduli?ref={BRANCH_PRINCIPALE}")
    req = urllib.request.Request(api_url, headers={
        "User-Agent": "OrbitaCasa-Bootstrap",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        dati = json.loads(resp.read().decode("utf-8"))
    if not isinstance(dati, list):
        raise RuntimeError(f"Risposta inattesa dalla Contents API: {dati}")
    return [f for f in dati if f.get("type") == "file" and f.get("name", "").endswith(".py")]
def _boot_lista_font_remoti():
    api_url = (f"https://api.github.com/repos/{REPO_OWNER}/"
               f"{REPO_NAME}/contents/moduli/assets/fonts?ref={BRANCH_PRINCIPALE}")
    req = urllib.request.Request(api_url, headers={
        "User-Agent": "OrbitaCasa-Bootstrap",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        dati = json.loads(resp.read().decode("utf-8"))
    if not isinstance(dati, list):
        raise RuntimeError(f"Risposta inattesa dalla Contents API: {dati}")
    return [f for f in dati if f.get("type") == "file" and f.get("name", "").endswith(".ttf")]
def _boot_sincronizza_font():
    fonts_dir = os.path.join(MODULI_DIR, "assets", "fonts")
    try:
        elenco_remoto = _boot_lista_font_remoti()
        os.makedirs(fonts_dir, exist_ok=True)
        for voce in elenco_remoto:
            nome = voce["name"]
            dest = os.path.join(fonts_dir, nome)
            sha_remoto = voce.get("sha", "")
            sha_locale = _boot_git_blob_sha1(dest) if os.path.isfile(dest) else None
            if sha_locale == sha_remoto:
                continue
            url_raw = voce.get("download_url")
            if not url_raw:
                continue
            for tentativo in range(3):
                try:
                    req = urllib.request.Request(url_raw, headers={"User-Agent": "OrbitaCasa-Bootstrap"})
                    with urllib.request.urlopen(req, timeout=20) as resp, open(dest, "wb") as out:
                        shutil.copyfileobj(resp, out)
                    break
                except Exception as e:
                    if tentativo == 2:
                        print(f"[{time.strftime('%H:%M:%S')}] Download font '{nome}' fallito: {e}")
        return True
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Sincronizzazione font non riuscita: {e}")
        return True
def _boot_pyw_allineato():
    try:
        percorso_pyw = os.path.join(PATH_LOCALE, NOME_FILE)
        if not os.path.isfile(percorso_pyw):
            return True
        sha_locale = _boot_git_blob_sha1(percorso_pyw)
        api_url = (f"https://api.github.com/repos/{REPO_OWNER}/"
                   f"{REPO_NAME}/contents/{NOME_FILE}?ref={BRANCH_PRINCIPALE}")
        req = urllib.request.Request(api_url, headers={
            "User-Agent": "OrbitaCasa-Bootstrap",
            "Accept": "application/vnd.github+json",
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            dati = json.loads(resp.read().decode("utf-8"))
        sha_remoto = dati.get("sha", "")
        return sha_locale == sha_remoto
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Verifica allineamento .pyw non riuscita: {e}")
        return True
def _boot_sincronizza_moduli():
    sp, lbl_status, aggiorna_bar = _boot_crea_splash_barra("Verifica aggiornamenti...")
    try:
        elenco_remoto = _boot_lista_moduli_remoti()
        os.makedirs(MODULI_DIR, exist_ok=True)
        totale = len(elenco_remoto) or 1
        aggiornati = 0
        for indice, voce in enumerate(elenco_remoto, start=1):
            nome = voce["name"]
            dest = os.path.join(MODULI_DIR, nome)
            sha_remoto = voce.get("sha", "")
            sha_locale = _boot_git_blob_sha1(dest) if os.path.isfile(dest) else None
            percento = (indice / totale) * 100
            if sha_locale == sha_remoto:
                if aggiorna_bar:
                    aggiorna_bar(percento, f"Verificato: {nome}")
                continue
            if aggiorna_bar:
                aggiorna_bar(percento, f"Download: {nome}")
            url_raw = voce.get("download_url")
            if not url_raw:
                continue
            tentativi_falliti = 0
            scaricato_ok = False
            while tentativi_falliti < 3 and not scaricato_ok:
                try:
                    req = urllib.request.Request(url_raw, headers={"User-Agent": "OrbitaCasa-Bootstrap"})
                    with urllib.request.urlopen(req, timeout=20) as resp, open(dest, "wb") as out:
                        shutil.copyfileobj(resp, out)
                    aggiornati += 1
                    scaricato_ok = True
                except Exception as e:
                    tentativi_falliti += 1
                    if isinstance(e, urllib.error.HTTPError) and e.code in (403, 429):
                        motivo = "limite richieste GitHub raggiunto"
                    else:
                        motivo = "Nessuna Connessione"
                    print(f"[{time.strftime('%H:%M:%S')}] Download '{nome}' ({tentativi_falliti}/3): {motivo}")
                    if aggiorna_bar:
                        aggiorna_bar(percento, f"fallito: {motivo}. ({tentativi_falliti}/3)")
                        if sp:
                            sp.update()
                            time.sleep(1.5)
            if not scaricato_ok and not os.path.isfile(dest):
                if aggiorna_bar:
                    aggiorna_bar(percento, f"'{nome}' non disponibile. Impossibile avviare.")
                    if sp:
                        sp.update()
                        time.sleep(2.5)
                if sp:
                    try:
                        sp.destroy()
                    except Exception:
                        pass
                show_warning_popup(
                    titolo="ATTENZIONE", titolo_fg="red",
                    corpo="Non è presente una connessione internet.\nImpossibile installare le risorse necessarie.\nIl programma verrà chiuso.",
                    corpo_fg="#61AFEF", corpo_font_size=11, corpo_expand=True,
                    bg="#000000", accent="#61AFEF", width=380, height=120
                )
                return False
        if aggiorna_bar:
            testo_finale = "Moduli gia' aggiornati!" if aggiornati == 0 else f"{aggiornati} moduli aggiornati!"
            aggiorna_bar(100, testo_finale)
            time.sleep(0.6)
        if sp:
            try:
                sp.destroy()
            except Exception:
                pass
        if aggiornati:
            print(f"[{time.strftime('%H:%M:%S')}] {aggiornati} file in 'moduli' aggiornati da GitHub.")
        else:
            print(f"[{time.strftime('%H:%M:%S')}] Moduli gia' aggiornati, nessuna modifica necessaria.")
        _boot_sincronizza_font()
        return True
    except Exception as e:
        if sp:
            try:
                sp.destroy()
            except Exception:
                pass
        print(f"[{time.strftime('%H:%M:%S')}] Verifica aggiornamento moduli non riuscita: {e}")
        if os.path.isdir(MODULI_DIR) and os.listdir(MODULI_DIR):
            print(f"[{time.strftime('%H:%M:%S')}] Si prosegue con la copia locale dei moduli gia' presente.")
            return True
        try:
            show_warning_popup(
                    titolo="ATTENZIONE", titolo_fg="red",
                    corpo="Non è presente una connessione internet.\nImpossibile installare le risorse necessarie.\nIl programma verrà chiuso.",
                    corpo_fg="#61AFEF", corpo_font_size=11, corpo_expand=True,
                    bg="#000000", accent="#61AFEF", width=380, height=120
                )
        except Exception:
            pass
        return False

# Entry point: installa dipendenze, inizializza directory e config, lancia l'app e scrive crashlog in caso di errore critico            
if __name__ == "__main__":
    import traceback
    log_file = os.path.join(PATH_LOCALE, "db", "error_log.txt")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    try:
        _boot_carica_moduli_iniziali()
        log_file = os.path.join(DB_DIR, "error_log.txt")

        # Sequenza di Inizializzazione e Controllo di Avvio
        check_single_instance()
        scarica_logo()
        inizializza_risorse_icone(MAP_ICONE)
        _boot_pulisci_pycache()
        if _boot_pyw_allineato():
           if DISABILITA_SYNC_MODULI_TEST:
               print(f"[{time.strftime('%H:%M:%S')}] [TEST] Sync moduli disattivata manualmente")
           elif not _boot_sincronizza_moduli():
               sys.exit(1)
        else:
            print(f"[{time.strftime('%H:%M:%S')}] .pyw locale non allineato all'ultimo commit: sincronizzazione moduli saltata per questo avvio.")
            show_warning_popup(
                titolo="Aggiornamento disponibile", titolo_fg="#c9a84c",
                corpo="È disponibile una nuova versione di OrbitaCasa.\n\nI moduli non verranno sincronizzati\n\n finché non aggiorni anche il programma.",
                corpo_fg="#61AFEF", corpo_font_size=9, corpo_expand=True,
                bg="#000000", accent="#c9a84c", width=420, height=140
            )
        _boot_pulisci_pycache()
        try:
            import importlib
            import moduli.costanti as _costanti_mod
            importlib.reload(_costanti_mod)
            globals().update(_costanti_mod.carica_costanti(PATH_LOCALE))
            inizializza_risorse_icone(MAP_ICONE)
        except Exception as _e:
            print(f"[{time.strftime('%H:%M:%S')}] Ricarica costanti.py post-sync fallita: {_e}")
        try:
            import importlib
            import moduli.modello_spesa as _modello_mod
            importlib.reload(_modello_mod)
            for _nome in ("SpesaEntry", "campo", "METODI_PAGAMENTO_EMOJI", "METODI_PAGAMENTO_FILTRO",
                          "VOCE_FILTRO_MOVIMENTI", "SEPARATORE_FILTRO_MOVIMENTI",
                          "SIMBOLI_METODO", "NOME_DA_EMOJI", "metodo_pagamento_pulito"):
                globals()[_nome] = getattr(_modello_mod, _nome)
        except Exception as _e:
            print(f"[{time.strftime('%H:%M:%S')}] Ricarica modello_spesa.py post-sync fallita: {_e}")
            
        # Inizializzazione Struttura delle Directory e dei File di Sistema
        if not os.path.exists(EXPORT_FILES):
            os.makedirs(EXPORT_FILES)
        if not os.path.exists(DB_DIR):
            os.makedirs(DB_DIR)
        if not os.path.exists(EXP_DB):
            os.makedirs(EXP_DB)
        if not os.path.exists(UTENZE_DB):
            with open(UTENZE_DB, "w") as file:
                file.write("")  
        if not os.path.exists(DOC_PERS_DIR):
            os.makedirs(DOC_PERS_DIR)

        try:
            from moduli.migrazione_emoji_dati import migra_emoji_nei_dati
            migra_emoji_nei_dati([(DB_FILE, 2), (REGISTRY_FILE, 4)])
        except Exception as _e:
            print(f"[{time.strftime('%H:%M:%S')}] Migrazione emoji dati fallita: {_e}")
        
        # Caricamento Finale dei Parametri di Configurazione Globali
        app_config_globale = aggiorna_configurazione_globale()
        AUTO_ICONIZE_STARTUP = app_config_globale.get("enable_auto_login_flow", False)
        ICONIZZA_INATTIVITA = app_config_globale.get("iconizza_inattivita", True)
        TIMEOUT_INATTIVITA_MS = app_config_globale.get("inactivity_timeout_ms", 1200000)
        SALVA_GEOMETRIA_INIZIALE = app_config_globale.get("load_saved_geometry", False)
        ABILITA_WEBSERVER = app_config_globale.get("webserver_enabled", False)
        USA_SSL = app_config_globale.get("usa_ssl", False)
        PORTA = app_config_globale.get("webserver_port", 8080)
        ANNI_DA_MANTENERE = app_config_globale.get("anni_da_mantenere", 10)
        ICO_SET_DATE = app_config_globale.get("ico_set_date", True)
        CHECK_MESE = app_config_globale.get("enable_recurring_reminder", True)
        SOGLIA_GIORNI_RICORRENTI = app_config_globale.get("soglia_giorni_ricorrenti", 5)
        MAX_BACKUP = app_config_globale.get("max_backup", 5)
        SMARTCAT = app_config_globale.get("smartcat_enabled", True)
        TOLL = app_config_globale.get("smartcat_toll", 15)
        USE_WAIT_WINDOW = app_config_globale.get("use_wait_window", False)
        WARN_TIMEOUT = app_config_globale.get("warn_timeout_ms", 20000)
        LINK_BANCA = app_config_globale.get("bank_link", "")
        THEMA = app_config_globale.get("thema", "OBSIDIAN")
        CAROSELLO = app_config_globale.get("carosello_enabled", True)
        CAROSELLO_INTERVALLO = app_config_globale.get("carosello_intervallo", 10000)
        CAL_TOOLTIPS = app_config_globale.get("cal_tooltips_enabled", True)
        ANIMAZIONI = app_config_globale.get("anima_tot_enabled", True)
        DB_CONDIVISO = app_config_globale.get("shared_db", False)
        PATH_RETE = app_config_globale.get("shared_db_path", PATH_LOCALE)
        UDP_PORT_1 = app_config_globale.get("udp_port_1", 5555)
        UDP_PORT_2 = app_config_globale.get("udp_port_2", 5556)
        TARGET_MESE = app_config_globale.get("target_mese", 0)
        TARGET_ANNO = app_config_globale.get("target_anno", 0)         
        SYNC_DATI = app_config_globale.get("sync_dati_enabled", False)
        SYNC_INT_MIN = app_config_globale.get("sync_intervallo_min", 720)
        MANDA_PUSH = app_config_globale.get("manda_push_enabled", False)
        EMAIL_USER = app_config_globale.get("email_user", "")
        APP_PASSWORD = app_config_globale.get("app_password", "")
        API_KEY = app_config_globale.get("gemini_api_key", "")
        CHECK_DOPPI_MOV = app_config_globale.get("check_double", False)
        GEMINI = app_config_globale.get("gemini_model", "gemini-2.5-flash")
        CLOSE = app_config_globale.get("close_behavior", False)
        BEEP = app_config_globale.get("beep_enabled", True)
        if isinstance(CLOSE, str):
            CLOSE = CLOSE.lower() == "true"
        kw_raw = app_config_globale.get("parole_chiave", "")
        if isinstance(kw_raw, list):
            PAROLE_CHIAVE = kw_raw
        else:
            PAROLE_CHIAVE = [k.strip() for k in str(kw_raw).split(",") if k.strip()]
                     
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Modalità: {'RETE' if DB_CONDIVISO else 'LOCALE'}")
        
        from moduli.registrazione_moduli import registra_tutti_i_moduli
        registra_tutti_i_moduli(GestioneSpese)

        # Lancio dell'Applicazione Principale e Ciclo di Eventi (Main Loop)
        _rc()
        _rb()
        app = GestioneSpese()
        _APP_REF = app

        # DataBase Condiviso
        if DB_CONDIVISO:
            t = threading.Thread(target=ascolta_aggiornamenti_rete, args=(app,), daemon=True)
            t.start()
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Modalità Rete Attiva")
            
        app.mainloop()

    except Exception as e:
        error_info = traceback.format_exc()
        print(f"\nERRORE CRITICO (v{VERSION})\n{error_info}")
        try:
            if os.path.exists(log_file) and os.path.getsize(log_file) > 50 * 1024:
                open(log_file, "w").close()
            with open(log_file, "a", encoding="utf-8") as f:
                timestamp = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                f.write(f"CRASH RILEVATO IL: {timestamp}\n")
                f.write(f"VERSIONE APP: {VERSION}\n")
                f.write(f"CONFIGURAZIONE ATTIVA:\n")
                if 'app_config_globale' in locals():
                    for chiave, valore in app_config_globale.items():
                        f.write(f"{chiave}: {valore}\n")
                else:
                    f.write("Configurazione non ancora caricata al momento del crash.\n")
                f.write(f"TRACEBACK:\n{error_info}\n\n")
        except Exception as log_err:
            print(f"Impossibile scrivere il log: {log_err}")
        sys.exit(1)
