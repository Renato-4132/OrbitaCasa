#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import datetime
import tkinter as tk
from tkinter import ttk, Toplevel

def gestisci_configurazione(self):
    import __main__ as _app
    CONFIG_FILE    = _app.CONFIG_FILE
    DEFAULT_CONFIG = _app.DEFAULT_CONFIG
    PATH_LOCALE    = _app.PATH_LOCALE
    DB_DIR         = _app.DB_DIR
    DB_CONDIVISO   = _app.DB_CONDIVISO
    if hasattr(self, 'ferma_scorrimento_automatico'):
        try: self.ferma_scorrimento_automatico()
        except: pass
    if hasattr(self, 'btn_ciclico_carosello'):
        self.btn_ciclico_carosello.configure(variable="") 
        self.btn_ciclico_carosello.state(['!active', '!selected', '!alternate'])
        self.btn_ciclico_carosello.update_idletasks()
    if not self.winfo_exists():
        return
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        config = DEFAULT_CONFIG.copy()
    use_wait_window_iniziale = config.get("use_wait_window", DEFAULT_CONFIG.get("use_wait_window", False))
    warn_timeout_ms_iniziale = config.get("warn_timeout_ms", DEFAULT_CONFIG.get("warn_timeout_ms", 20000))
    timeout_sec_iniziale = round(warn_timeout_ms_iniziale / 1000)
    timeout_sec_iniziale = max(5, min(60, timeout_sec_iniziale))
    ico_set_date_iniziale = config.get("ico_set_date", DEFAULT_CONFIG["ico_set_date"])
    recurring_reminder_iniziale = config.get("enable_recurring_reminder", DEFAULT_CONFIG["enable_recurring_reminder"])
    max_backup_iniziale = config.get("max_backup", DEFAULT_CONFIG.get("max_backup", 5))
    max_backup_iniziale = max(1, min(10, max_backup_iniziale))
    soglia_giorni_ricorrenti_iniziale = config.get("soglia_giorni_ricorrenti", DEFAULT_CONFIG.get("soglia_giorni_ricorrenti", 5))
    soglia_giorni_ricorrenti_iniziale = max(1, min(10, soglia_giorni_ricorrenti_iniziale))
    timeout_ms_iniziale = config.get("inactivity_timeout_ms", DEFAULT_CONFIG["inactivity_timeout_ms"])
    timeout_minuti_iniziale = round(timeout_ms_iniziale / 60000)
    timeout_minuti_iniziale = max(5, min(60, timeout_minuti_iniziale))
    anni_da_mantenere_iniziale = config.get("anni_da_mantenere", DEFAULT_CONFIG["anni_da_mantenere"])
    anni_da_mantenere_iniziale = max(2, min(10, anni_da_mantenere_iniziale))
    iconizza_inattivita_iniziale = config.get("iconizza_inattivita", DEFAULT_CONFIG["iconizza_inattivita"])
    smartcat_enabled_iniziale = config.get("smartcat_enabled", DEFAULT_CONFIG.get("smartcat_enabled", True))
    smartcat_toll_iniziale = config.get("smartcat_toll", DEFAULT_CONFIG.get("smartcat_toll", 15))
    smartcat_toll_iniziale = max(5, min(100, smartcat_toll_iniziale))
    beep_enabled_iniziale = config.get("beep_enabled", DEFAULT_CONFIG.get("beep_enabled", True))
    bank_link_iniziale = config.get("bank_link", DEFAULT_CONFIG.get("bank_link", ""))
    thema_iniziale = config.get("thema", DEFAULT_CONFIG.get("thema", "MATERIAL"))
    carosello_enabled_iniziale = config.get("carosello_enabled", DEFAULT_CONFIG.get("carosello_enabled", True))
    carosello_intervallo_iniziale = config.get("carosello_intervallo", DEFAULT_CONFIG.get("carosello_intervallo", 10000))
    carosello_intervallo_sec_iniziale = round(carosello_intervallo_iniziale / 1000)
    carosello_intervallo_sec_iniziale = max(5, min(30, carosello_intervallo_sec_iniziale))
    udp_port_1_iniziale = config.get("udp_port_1", 5555)
    udp_port_2_iniziale = config.get("udp_port_2", 5556)
    target_mese_iniziale = config.get("target_mese", 0)
    target_anno_iniziale = config.get("target_anno", 0)
    sync_enabled_iniziale = config.get("sync_dati_enabled", DEFAULT_CONFIG.get("sync_dati_enabled", False))
    manda_push_enabled_iniziale = config.get("manda_push_enabled", DEFAULT_CONFIG.get("manda_push_enabled", False))
    email_user_iniziale = config.get("email_user", DEFAULT_CONFIG.get("email_user", ""))
    app_password_iniziale = config.get("app_password", DEFAULT_CONFIG.get("app_password", ""))
    gemini_api_key_iniziale = config.get("gemini_api_key", DEFAULT_CONFIG.get("gemini_api_key", ""))
    gemini_model_iniziale = config.get("gemini_model", DEFAULT_CONFIG.get("gemini_model", "gemini-2.5-flash"))
    check_double_iniziale = config.get("check_double", DEFAULT_CONFIG.get("check_double", False))
    close_behavior_iniziale = config.get("close_behavior", DEFAULT_CONFIG.get("close_behavior", False))
    anima_tot_iniziale = config.get("anima_tot_enabled", DEFAULT_CONFIG.get("anima_tot_enabled", True))
    if isinstance(close_behavior_iniziale, str):
            close_behavior_iniziale = True if close_behavior_iniziale.lower() == "true" else False
    if not isinstance(close_behavior_iniziale, bool):
            close_behavior_iniziale = False
    pk_raw = config.get("parole_chiave", DEFAULT_CONFIG.get("parole_chiave", "no-reply-ML@aceaenergia.it, no-reply.acque@acque.net, contotelefonico@fatturazione.windtre.it"))
    if isinstance(pk_raw, list):
        parole_chiave_iniziale = ", ".join(pk_raw)
    else:
        parole_chiave_iniziale = pk_raw
        
    sync_intervallo_iniziale = config.get("sync_intervallo_min", DEFAULT_CONFIG.get("sync_intervallo_min", 720))
    
    config_window = Toplevel(self)
    config_window.transient(self)
    config_window.title("⚙️ Configurazione Applicazione")
    config_window.bind('<Escape>', lambda e: config_window.destroy())
    config_window.resizable(False, False)
    self.var_use_wait_window = tk.BooleanVar(value=use_wait_window_iniziale)
    self.var_warn_timeout_sec = tk.DoubleVar(value=timeout_sec_iniziale)
    self.var_ico_set_date = tk.BooleanVar(value=ico_set_date_iniziale)
    self.var_recurring_reminder = tk.BooleanVar(value=recurring_reminder_iniziale)
    self.var_max_backup = tk.IntVar(value=max_backup_iniziale)
    self.var_soglia_ricorrenti = tk.IntVar(value=soglia_giorni_ricorrenti_iniziale)
    self.var_smartcat_enabled = tk.BooleanVar(value=smartcat_enabled_iniziale)
    self.var_smartcat_toll = tk.IntVar(value=smartcat_toll_iniziale)
    self.var_beep_enabled = tk.BooleanVar(value=beep_enabled_iniziale)
    self.var_auto_login = tk.BooleanVar(value=config.get("enable_auto_login_flow", DEFAULT_CONFIG["enable_auto_login_flow"]))
    self.var_webserver_enabled = tk.BooleanVar(value=config.get("webserver_enabled", DEFAULT_CONFIG["webserver_enabled"]))
    self.var_usa_ssl = tk.BooleanVar(value=config.get("usa_ssl", DEFAULT_CONFIG.get("usa_ssl", True)))
    self.var_timeout_minuti = tk.DoubleVar(value=timeout_minuti_iniziale)
    self.var_port = tk.IntVar(value=config.get("webserver_port", DEFAULT_CONFIG["webserver_port"]))
    self.var_bank_link = tk.StringVar(value=bank_link_iniziale)
    self.var_load_geometry = tk.BooleanVar(value=config.get("load_saved_geometry", DEFAULT_CONFIG["load_saved_geometry"]))
    self.var_anni_da_mantenere = tk.IntVar(value=anni_da_mantenere_iniziale)
    self.var_iconizza_inattivita = tk.BooleanVar(value=iconizza_inattivita_iniziale)
    self.var_thema = tk.StringVar(value=thema_iniziale.capitalize())
    self.var_carosello_enabled = tk.BooleanVar(value=carosello_enabled_iniziale)
    self.var_carosello_intervallo_sec = tk.DoubleVar(value=carosello_intervallo_sec_iniziale)
    self.var_cal_tooltips = tk.BooleanVar(value=config.get("cal_tooltips_enabled", True))
    self.var_anima_tot = tk.BooleanVar(value=anima_tot_iniziale)
    self.var_shared_db = tk.BooleanVar(value=config.get("shared_db", DEFAULT_CONFIG.get("shared_db", False)))
    self.var_shared_db_path = tk.StringVar(value=config.get("shared_db_path", DEFAULT_CONFIG.get("shared_db_path", "")))
    self.var_udp_port_1 = tk.IntVar(value=udp_port_1_iniziale)
    self.var_udp_port_2 = tk.IntVar(value=udp_port_2_iniziale)
    self.var_target_mese = tk.DoubleVar(value=target_mese_iniziale)
    self.var_target_anno = tk.DoubleVar(value=target_anno_iniziale)
    self.var_sync_enabled = tk.BooleanVar(value=sync_enabled_iniziale)
    self.var_manda_push = tk.BooleanVar(value=manda_push_enabled_iniziale)
    self.var_email_user = tk.StringVar(value=email_user_iniziale)
    self.var_app_password = tk.StringVar(value=app_password_iniziale)
    self.var_gemini_api_key = tk.StringVar(value=gemini_api_key_iniziale)
    self.var_gemini_model = tk.StringVar(value=gemini_model_iniziale)
    self.var_parole_chiave = tk.StringVar(value=parole_chiave_iniziale)
    self.var_sync_intervallo = tk.IntVar(value=sync_intervallo_iniziale)
    self.var_check_double = tk.BooleanVar(value=check_double_iniziale)
    self.var_close_behavior = tk.BooleanVar(value=close_behavior_iniziale)
    self.var_beep_enabled = tk.BooleanVar(value=beep_enabled_iniziale)
    
    main_frame = ttk.Frame(config_window, padding="10 10 10 5")
    main_frame.pack(fill="both", expand=True)
    main_frame.columnconfigure(0, weight=1, uniform="col")
    main_frame.columnconfigure(1, weight=1, uniform="col")
    main_frame.columnconfigure(2, weight=1, uniform="col")
    warn_timeout_label = ttk.Label(main_frame, text="")
    timeout_label = ttk.Label(main_frame, text="")
    anni_label = ttk.Label(main_frame, text="")
    max_backup_label = ttk.Label(main_frame, text="")
    soglia_ricorrenti_label = ttk.Label(main_frame, text="")
    carosello_intervallo_label = ttk.Label(main_frame, text="")
    target_mese_label = ttk.Label(main_frame, text="")
    target_anno_label = ttk.Label(main_frame, text="")

    def update_warn_timeout_label(value):
        current_sec = int(round(self.var_warn_timeout_sec.get()))
        warn_timeout_label.config(text=f"{current_sec} Sec.")
    def update_timeout_label(value):
        current_minuti = int(round(self.var_timeout_minuti.get()))
        timeout_label.config(text=f"{current_minuti} Min.")
    def update_anni_label(value):
        current_anni = int(round(self.var_anni_da_mantenere.get()))
        anni_label.config(text=f"{current_anni} Anni")
    def update_max_backup_label(value):
        current_val = int(round(self.var_max_backup.get()))
        max_backup_label.config(text=f"{current_val} Copie")
    def update_soglia_ricorrenti_label(value):
        current_val = int(round(self.var_soglia_ricorrenti.get()))
        soglia_ricorrenti_label.config(text=f"{current_val} Giorni")
    def update_carosello_intervallo_label(value):
        current_sec = int(round(self.var_carosello_intervallo_sec.get()))
        carosello_intervallo_label.config(text=f"{current_sec} Sec.")      
    def update_target_mese_label(*args):
        val = self.var_target_mese.get()
        target_mese_label.config(text=f"{val:,.2f} €")
    def update_target_anno_label(*args):
        val = self.var_target_anno.get()
        target_anno_label.config(text=f"{val:,.2f} €")
    
    def reset_defaults():
        self.var_auto_login.set(DEFAULT_CONFIG["enable_auto_login_flow"])
        self.var_webserver_enabled.set(DEFAULT_CONFIG["webserver_enabled"])
        self.var_usa_ssl.set(DEFAULT_CONFIG.get("usa_ssl", True))
        self.var_port.set(DEFAULT_CONFIG["webserver_port"])
        self.var_bank_link.set(DEFAULT_CONFIG.get("bank_link", ""))
        self.var_load_geometry.set(DEFAULT_CONFIG["load_saved_geometry"])
        self.var_use_wait_window.set(DEFAULT_CONFIG.get("use_wait_window", False))
        default_timeout_min = round(DEFAULT_CONFIG["inactivity_timeout_ms"] / 60000)
        self.var_timeout_minuti.set(max(5, default_timeout_min))
        update_timeout_label(self.var_timeout_minuti.get())
        self.var_anni_da_mantenere.set(DEFAULT_CONFIG["anni_da_mantenere"])
        update_anni_label(self.var_anni_da_mantenere.get())
        self.var_iconizza_inattivita.set(DEFAULT_CONFIG["iconizza_inattivita"])
        self.var_ico_set_date.set(DEFAULT_CONFIG["ico_set_date"])
        self.var_recurring_reminder.set(DEFAULT_CONFIG.get("enable_recurring_reminder", False))
        self.var_max_backup.set(max(1, min(10, DEFAULT_CONFIG.get("max_backup", 5))))
        update_max_backup_label(self.var_max_backup.get())
        self.var_soglia_ricorrenti.set(max(1, min(10, DEFAULT_CONFIG.get("soglia_giorni_ricorrenti", 5))))
        update_soglia_ricorrenti_label(self.var_soglia_ricorrenti.get())
        self.var_smartcat_enabled.set(DEFAULT_CONFIG.get("smartcat_enabled", True))
        self.var_smartcat_toll.set(DEFAULT_CONFIG.get("smartcat_toll", 15))
        self.var_beep_enabled.set(DEFAULT_CONFIG.get("beep_enabled", True))
        self.var_thema.set(DEFAULT_CONFIG.get("thema", "OBSIDIAN").capitalize())
        self.var_carosello_enabled.set(DEFAULT_CONFIG.get("carosello_enabled", True))
        default_carosello_sec = round(DEFAULT_CONFIG.get("carosello_intervallo", 10000) / 1000)
        self.var_carosello_intervallo_sec.set(max(5, min(30, default_carosello_sec)))
        update_carosello_intervallo_label(self.var_carosello_intervallo_sec.get())
        self.var_cal_tooltips.set(DEFAULT_CONFIG.get("cal_tooltips_enabled", True))
        self.var_anima_tot.set(DEFAULT_CONFIG.get("anima_tot_enabled", True))
        self.var_shared_db.set(DEFAULT_CONFIG.get("shared_db", False))
        self.var_shared_db_path.set(DEFAULT_CONFIG.get("shared_db_path", PATH_LOCALE))
        self.var_udp_port_1.set(DEFAULT_CONFIG.get("udp_port_1", 5555))
        self.var_udp_port_2.set(DEFAULT_CONFIG.get("udp_port_2", 5556))
        self.var_target_mese.set(DEFAULT_CONFIG.get("target_mese", 0))
        self.var_target_anno.set(DEFAULT_CONFIG.get("target_anno", 0))
        self.var_sync_enabled.set(DEFAULT_CONFIG.get("sync_dati_enabled", False))
        self.var_email_user.set(DEFAULT_CONFIG.get("email_user", "@gmail.com"))
        self.var_app_password.set(DEFAULT_CONFIG.get("app_password", ""))
        self.var_gemini_api_key.set(DEFAULT_CONFIG.get("gemini_api_key", ""))
        self.var_gemini_model.set(DEFAULT_CONFIG.get("gemini_model", "gemini-2.5-flash"))
        self.var_parole_chiave.set(", ".join(DEFAULT_CONFIG.get("parole_chiave", ["no-reply-ML@aceaenergia.it, no-reply.acque@acque.net, contotelefonico@fatturazione.windtre.it"])))
        self.show_custom_info("Reset", "Impostazioni ripristinate ai valori predefinite. Clicca su Salva per applicare.")
        self.var_sync_intervallo.set(DEFAULT_CONFIG.get("sync_intervallo_min", 720))
        self.var_check_double.set(DEFAULT_CONFIG.get("check_double", False))
        default_close = DEFAULT_CONFIG.get("close_behavior", False)
        if isinstance(default_close, str):
            default_close = default_close.lower() == "true"
        self.var_close_behavior.set(default_close)
        
    def chiudi_config():
        config_window.destroy()
        
    def salva_e_chiudi():
        if not self._licenza_valida():
            self.show_toast("Salvataggio non disponibile senza licenza attiva.", duration=3000)
            return
        try:
            anni = self.var_anni_da_mantenere.get()
            if anni < 2 or anni > 10:
                raise ValueError("Anni da mantenere deve essere tra 2 e 10.")
            max_backup = self.var_max_backup.get()
            if max_backup < 1 or max_backup > 10:
                raise ValueError("Il numero massimo di backup deve essere tra 1 e 10.")
            soglia_giorni = self.var_soglia_ricorrenti.get()
            if soglia_giorni < 1 or soglia_giorni > 10:
                raise ValueError("La soglia giorni ricorrenti deve essere tra 1 e 10.")
            timeout_minuti = round(self.var_timeout_minuti.get())
            if timeout_minuti < 5 or timeout_minuti > 60:
                raise ValueError("Timeout Inattività deve essere tra 5 e 60 minuti.")
            timeout_ms = int(timeout_minuti * 60000)
            warn_timeout_sec = round(self.var_warn_timeout_sec.get())
            if warn_timeout_sec < 5 or warn_timeout_sec > 60:
                raise ValueError("Timeout Avviso Popup deve essere tra 5 e 60 secondi.")
            warn_timeout_ms = int(warn_timeout_sec * 1000)
            webserver_port = self.var_port.get()
            if webserver_port < 1024 or webserver_port > 65535:
                raise ValueError("La porta Webserver non è valida (range 1024-65535).")
            udp_1 = self.var_udp_port_1.get()
            udp_2 = self.var_udp_port_2.get()
            if udp_1 < 1024 or udp_1 > 65535 or udp_2 < 1024 or udp_2 > 65535:
                raise ValueError("Le porte UDP devono essere comprese tra 1024 e 65535.")
            carosello_intervallo_sec = round(self.var_carosello_intervallo_sec.get())
            if carosello_intervallo_sec < 5 or carosello_intervallo_sec > 30:
                raise ValueError("L'intervallo Carosello deve essere tra 5 e 30 secondi.")
            carosello_intervallo_ms = int(carosello_intervallo_sec * 1000)
            try:
                target_mese = float(str(self.var_target_mese.get()).replace(",", ".") or 0)
            except Exception:
                target_mese = 0.0
                self.var_target_mese.set(0.0)
            try:
                target_anno = float(str(self.var_target_anno.get()).replace(",", ".") or 0)
            except Exception:
                target_anno = 0.0
                self.var_target_anno.set(0.0)
            if target_mese < 0 or target_anno < 0:
                raise ValueError("I Target di spesa non possono essere negativi.")
            sync_enabled = self.var_sync_enabled.get()
            check_double = self.var_check_double.get()
            manda_push_enabled = self.var_manda_push.get()
            email_user = self.var_email_user.get().strip()
            app_password = self.var_app_password.get().strip()
            parole_chiave_raw = self.var_parole_chiave.get()
            gemini_api_key_attuale = self.var_gemini_api_key.get().strip()
            gemini_model_attuale = self.var_gemini_model.get().strip()
            beep_enabled = self.var_beep_enabled.get()
            if sync_enabled:
                if not email_user or "@gmail.com" not in email_user.lower():
                    raise ValueError("Inserire un indirizzo Gmail valido per la sincronizzazione.")
                if not app_password:
                    raise ValueError("L'App Password di Google è obbligatoria per il sync.")
                if len(app_password.replace(" ", "")) != 16:
                    raise ValueError("La Password Google deve essere di 16 caratteri.")
                if not parole_chiave_raw:
                    raise ValueError("Inserire almeno una parola chiave (es: Amazon, Enel) per il sync.")
                if not gemini_api_key_attuale:
                    raise ValueError("La API Key di Gemini è necessaria per il parsing intelligente.")
            lista_chiavi = [k.strip() for k in parole_chiave_raw.split(",") if k.strip()]
            parole_chiave_pulite = ", ".join(lista_chiavi)   
                             
            nuova_config = {
                "enable_auto_login_flow": self.var_auto_login.get(),
                "webserver_enabled": self.var_webserver_enabled.get(),
                "usa_ssl": self.var_usa_ssl.get(),
                "inactivity_timeout_ms": timeout_ms,
                "webserver_port": webserver_port,
                "bank_link": self.var_bank_link.get(),
                "load_saved_geometry": self.var_load_geometry.get(),
                "anni_da_mantenere": anni,
                "iconizza_inattivita": self.var_iconizza_inattivita.get(),
                "ico_set_date": self.var_ico_set_date.get(),
                "enable_recurring_reminder": self.var_recurring_reminder.get(),
                "max_backup": max_backup,
                "soglia_giorni_ricorrenti": soglia_giorni,
                "smartcat_enabled": self.var_smartcat_enabled.get(),
                "smartcat_toll": self.var_smartcat_toll.get(),
                "beep_enabled": beep_enabled,
                "check_double": self.var_check_double.get(),
                "use_wait_window": self.var_use_wait_window.get(),
                "warn_timeout_ms": warn_timeout_ms,
                "thema": self.var_thema.get().upper(),
                "carosello_enabled": self.var_carosello_enabled.get(),
                "carosello_intervallo": carosello_intervallo_ms,
                "cal_tooltips_enabled": self.var_cal_tooltips.get(),
                "anima_tot_enabled": self.var_anima_tot.get(),
                "shared_db": self.var_shared_db.get(),
                "shared_db_path": self.var_shared_db_path.get(),
                "udp_port_1": self.var_udp_port_1.get(),
                "udp_port_2": self.var_udp_port_2.get(),
                "target_mese": self.var_target_mese.get(),
                "target_anno": self.var_target_anno.get(),
                "sync_dati_enabled": self.var_sync_enabled.get(),
                "manda_push_enabled": manda_push_enabled,
                "email_user": self.var_email_user.get().strip(),
                "app_password": self.var_app_password.get().strip(),
                "gemini_api_key": self.var_gemini_api_key.get().strip(),
                "gemini_model": self.var_gemini_model.get().strip(),
                "parole_chiave": ", ".join([k.strip() for k in self.var_parole_chiave.get().split(",") if k.strip()]),
                "sync_intervallo_min": int(self.var_sync_intervallo.get() or 720),
                "close_behavior": self.var_close_behavior.get(),
            }
            if not os.path.exists(DB_DIR):
                os.makedirs(DB_DIR)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(nuova_config, f, indent=4)
            try:
                global ANNI_DA_MANTENERE
                ANNI_DA_MANTENERE = int(nuova_config.get("anni_da_mantenere", 10))
                self.save_db()
                self.load_db()
                self.refresh_gui()
                if DB_CONDIVISO:
                    self.notifica_modifica_web()
                    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 📡 Notifica di aggiornamento inviata .")    
            except Exception as e:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⚠️ Errore durante la pulizia database pre-riavvio: {e}")    
            self.suggerimenti_attivi = self.var_smartcat_enabled.get()
            if config_window.winfo_exists():
                config_window.destroy()
            riavvia_subito = self.show_custom_askyesno(
                title="Riavvio Necessario",
                message="Per applicare completamente alcune modifiche\n(es. porta WebServer, timeout, pulizia database, tema)\nè necessario riavviare l'applicazione.\n\nRiavviare ora?"
            )
            if riavvia_subito:
                riavvia_app_definitivo()
            else:
                self.show_custom_warning("Riavvio in Sospeso", "Riavvio posticipato. Le modifiche saranno applicate al prossimo avvio manuale.")
        except ValueError as e:
            self.show_custom_info("Errore di Validazione", str(e))
        except Exception as e:
            self.show_custom_info("Errore di Salvataggio", f"Impossibile salvare la configurazione: {e}")                
    def riavvia_app_definitivo():
        import subprocess, sys, os
        if self.winfo_exists():
            self.destroy()
        script_path = os.path.abspath(sys.argv[0])
        args = [sys.executable, script_path] + sys.argv[1:]
        if os.name == 'nt':
            subprocess.Popen(args, creationflags=0x00000008, shell=False, close_fds=True)
        else:
            subprocess.Popen(args, start_new_session=True, close_fds=True)
        os._exit(0)
        
    def mostra_help_configurazione():
        fixed_width = 1000
        fixed_height = 600
        help_window = Toplevel(config_window)
        help_window.title("❓ Aiuto Dettagliato Configurazione")
        help_window.resizable(False, False)
        help_window.configure(bg=self.COLOR_TOPLEVEL)
        help_window.withdraw()
        screen_w = help_window.winfo_screenwidth()
        screen_h = help_window.winfo_screenheight()
        x = (screen_w - fixed_width) // 2
        y = (screen_h - fixed_height) // 2
        help_window.geometry(f"{fixed_width}x{fixed_height}+{x}+{y}")
        help_window.transient(config_window)
        help_window.bind('<Escape>', lambda e: help_window.destroy())
        main_container = ttk.Frame(help_window, padding="10")
        main_container.pack(fill="both", expand=True)
        help_window.update_idletasks()
        help_window.deiconify()
        help_window.focus_set()
        help_window.grab_set()
        ttk.Label(main_container, text="Manuale d'uso - Opzioni di Configurazione", 
                  font=("Arial", 12, "bold"), foreground="#00529B").pack(pady=(0, 10))
        notebook = ttk.Notebook(main_container)
        notebook.pack(fill="both", expand=True, pady=(0, 10))
        def _add_tab(frame, ico_key, testo):
            img = self.icone_gui.get(ico_key)
            if img:
                notebook.add(frame, image=img, text=f" {testo} ", compound="left")
            else:
                notebook.add(frame, text=testo)
        def crea_tab_bianco(titolo, contenuto_testo, ico_key=None):
            frame_tab = ttk.Frame(notebook)
            _add_tab(frame_tab, ico_key, titolo)
            container = tk.Frame(frame_tab, bg=self.COLOR_WHITE, 
                                 highlightbackground=self.COLOR_TOPLEVEL, 
                                 highlightthickness=4, bd=0)
            container.pack(fill="both", expand=True, padx=15, pady=15)
            lbl = tk.Label(container, text=contenuto_testo, 
                           font=("Arial", 10), 
                           bg=self.COLOR_WHITE, 
                           fg=self.COLOR_BLACK, 
                           justify=tk.LEFT, 
                           anchor='nw', 
                           wraplength=900)
            lbl.pack(fill='both', expand=True, padx=15, pady=15)
            return frame_tab
        testo_tab1 = (
            "• FLUSSO LOGIN/ICONIZZA: Se attivo, l'applicazione si riduce automaticamente a icona nella tray bar dopo l'accesso.\n\n"
            "• COMPORTAMENTO TASTO (X): Scegli se chiudere definitivamente l'app o iconizzarla nella barra delle applicazioni per mantenerla attiva.\n\n"
            "• ATTIVA SMARTCAT: Sistema di intelligenza artificiale che suggerisce la categoria più probabile in base alle tue abitudini di movimenti.\n\n"
            "• TOLLERANZA SMARTCAT: Margine entro cui SmartCat cerca corrispondenze nello storico. Valori più alti = più suggerimenti, meno precisi.\n\n"
            "• CONTROLLO DUPLICATI: Se attivo, il Web Server ti avviserà se stai inserendo un movimento con stesso importo e categoria nello stesso mese.\n\n"
            "• WEB SERVER: Abilita il portale HTTP/HTTPS per consultare i dati da remoto (es. smartphone, Tablet, PC).\n\n"
            "  ----------------------------------------------------------------------------------------------------------------------------------\n"
            "  🛡️ NOTA SICUREZZA HTTPS:\n"
            "  Il sistema genera un certificato SSL privato per proteggere i tuoi dati.\n"
            "  Al primo accesso il browser mostrerà un avviso di sicurezza: 'Connessione non privata'.\n"
            "  È NORMALE (certificato autofirmato dall'app, non acquistato ed autogenerato).\n"
            "  COSA FARE: Puoi procedere con fiducia, Clicca su 'Avanzate' e poi su 'Procedi' per navigare protetto al 100%.\n"
            "  TUNNEL VPN: Sempre consigliato per l'accesso da fuori casa (WAN).\n"
            "  ----------------------------------------------------------------------------------------------------------------------------------\n\n"
            "• PORTA WEB SERVER: Specifica la porta di ascolto (default 8080). Assicurati che non sia usata da altri programmi.\n\n"
            "• LINK BANCA: Inserisci l'URL diretto della tua home banking per aprirlo rapidamente con l'icona dedicata nella schermata principale."
        )
        testo_tab2 = (
            "• CARICA POSIZIONE: All'avvio, l'app si riposiziona esattamente dove l'avevi chiusa l'ultima volta.\n\n"
            "• ABILITA SMART INFO-POINT: Passando il mouse sopra i giorni del calendario, apparirà un popup con il riepilogo istantaneo dei movimenti.\n\n"
            "• ANIMAZIONI: Abilita l'effetto scorrimento sui totali e le icone dinamiche.\n\n"
            "• AGGIORNA DATA AL RIPRISTINO: Se l'app rimane aperta per molto tempo, al ripristino dalla tray bar imposta il calendario sulla data odierna.\n\n"
            "• AVVISI BLOCCANTI: Se attivo, i messaggi di conferma (es. 'Salvataggio completato') rimarranno a schermo finché non clicchi OK.\n\n"
            "• TIMER AUTO-CHIUSURA: Durata in secondi dei messaggi informativi prima che scompaiano automaticamente.\n\n"
            "• ICONIZZA PER INATTIVITÀ: Riduce l'app a icona dopo un periodo di inutilizzo impostabile per proteggere la tua privacy.\n\n"
            "• TEMA UI: Passa dalla modalità Chiara classica a quella Material Design (colori più moderni).\n\n"
            "• BEEP ACUSTICO: Se attivo, l'applicazione emette un segnale sonoro in corrispondenza degli avvisi e delle notifiche di sistema."
        )
        testo_tab3 = (
            "• ABILITA CAROSELLO: Mostra a rotazione i grafici delle spese mensili e dei saldi quando non stai usando l'applicazione.\n\n"
            "• INTERVALLO CAROSELLO: Tempo di permanenza (5-30 secondi) di ogni schermata statistica prima di passare alla successiva.\n\n"
            "• PROMEMORIA MENSILE: Ti avvisa se ci sono categorie di movimenti ricorrenti che non hai ancora registrato nel mese corrente.\n\n"
            "• SOGLIA ANTICIPO: Specifica quanti giorni prima della fine del mese deve iniziare a mostrarti l'avviso dei promemoria.\n\n"
            "• TARGET (MESE/ANNO): Imposta i margini in uscita. Se > 0, attiva il calcolo del margine residuo attuale nei riepiloghi."
        )
        testo_tab4 = (
            "• DATABASE CONDIVISO: Permette di spostare il database su una cartella di rete (NAS o Cloud locale) per condividere i dati tra più PC.\n\n"
            "• PATH DATABASE: Il percorso completo (es. Z:\\Dati\\mio_db.db) dove risiede la cartella condivisa.\n\n"
            "• PORTE UDP (1 & 2): Porte utilizzate per la sincronizzazione istantanea dei dati tra più postazioni nella stessa rete locale.\n\n"
            "• ANNI STORICO: Determina quanti anni di dati mantenere nel database prima della pulizia automatica (Range: 2-10 anni).\n\n"
            "• MAX COPIE BACKUP: Numero di file di sicurezza salvati nella cartella backup. Raggiunto il limite, il più vecchio viene eliminato.\n\n"
        )

        testo_tab5 = (
            "• INFO NOTIFICHE SMARTPHONE (Email) \n"
            "  1. Assicurati di aver inserito la tua Gmail e l'App Password nelle impostazioni.\n"
            "  2. Quando il server è attivo, riceverai automaticamente una email con l'IP e il link diretto.\n"
            "  3. Clicca sul link nell'email per accedere al WebServer dal tuo smartphone.\n"
            "  👉 Clicca su 'Leggi Email' nella Dashboard per aprire direttamente la tua casella Gmail.\n\n"
            "• SYNC EMAIL: Attiva la lettura automatica della posta per scaricare i movimenti ricevuti via Gmail.\n\n"
            "• APP PASSWORD: Non è la password della mail, ma il codice a 16 cifre generato nelle impostazioni di sicurezza Google.\n"
            "  🌐 Generala qui: https://myaccount.google.com/apppasswords\n\n"
            "• PAROLE CHIAVE: Filtri (separati da virgola) usati per identificare le Email pertinenti (Es. contotelefonico@fatturazione.windtre.it).\n\n"
            "• API KEY GEMINI: Inserisci la tua chiave personale di Google AI per abilitare l'analisi automatica dei documenti.\n\n"
            "• MODELLO GEMINI: Seleziona il modello AI da utilizzare per l'analisi (es. gemini-2.5-flash, gemini-2.0-flash).\n\n"
            "• FREQUENZA SYNC: Imposta ogni quanti minuti il programma deve controllare la posta.\n"
            "----------------------------------------------------------------------\n\n"
            "** ESEMPIO EMAIL RICONOSCIUTA **\n"
            "Da: Mario Rossi <m.rossi@gmail.com>\n"
            "Data: mar 3 feb, 08:12\n"
            "Testo: Avviso di accredito: è stato ricevuto un bonifico a vostro favore "
            "di 1200,00 € disposto da AZIENDA ROSSI SPA. I fondi sono disponibili."
        )

        crea_tab_bianco("Automatismo & Web", testo_tab1, "tools")
        crea_tab_bianco("Interfaccia & Window", testo_tab2, "filtri")
        crea_tab_bianco("Carosello & Alert", testo_tab3, "alert")
        crea_tab_bianco("Database & Backup", testo_tab4, "salva")
        crea_tab_bianco("Connettività & Sync", testo_tab5, "sync")
        footer_frame = ttk.Frame(main_container)
        footer_frame.pack(fill="x", side="bottom")
        ttk.Separator(footer_frame, orient='horizontal').pack(fill="x", pady=5)                  
        img_chiudi_help = self.icone_gui.get("chiudi")
        btn_chiudi_help = ttk.Label(
            footer_frame,
            compound="left",
            image=img_chiudi_help,
            text=" Chiudi" if img_chiudi_help else "Chiudi",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2",
            padding=(15, 5)
        )
        btn_chiudi_help.image = img_chiudi_help
        btn_chiudi_help.pack(pady=5, expand=True)
    
        btn_chiudi_help.bind("<Button-1>", lambda e: help_window.destroy())
        help_window.update_idletasks()
        c_x = config_window.winfo_rootx() + (config_window.winfo_width() // 2) - (fixed_width // 2)
        c_y = config_window.winfo_rooty() + (config_window.winfo_height() // 2) - (fixed_height // 2)
        help_window.geometry(f"{fixed_width}x{fixed_height}+{c_x}+{c_y}")
        help_window.deiconify()
    row_counter = 0
    
    def create_checkbutton(container, text, variable, row, column=0):
        cb = ttk.Checkbutton(container, text=text, variable=variable)
        cb.grid(row=row, column=column, sticky="w", padx=10, pady=2)
        return cb
        
    def create_combobox(container, text, variable, values, row, column=0):
        f = ttk.Frame(container)
        f.grid(row=row, column=column, sticky="w", padx=10, pady=2)
        ttk.Label(f, text=text).pack(side="left")
        cb = ttk.Combobox(
            f, 
            textvariable=variable, 
            values=values, 
            state="readonly", 
            width=15,
            style="Border.TCombobox"
        )
        cb.pack(side="left", padx=5)
        return cb
        
    def create_entry(parent, label_text, variable, row, column=0, width=30):
        f = ttk.Frame(parent)
        f.grid(row=row, column=column, sticky="we", pady=1, padx=(10, 10))
        lbl = ttk.Label(f, text=label_text, width=25, anchor="w")
        lbl.pack(side="left")
        ent = ttk.Entry(f, textvariable=variable, width=width)
        ent.pack(side="left", fill="x", expand=True, padx=5)
        return f
        
    def create_slider_row(container, text, min_val, max_val, variable, update_func, label_obj, row, column=0, colspan=1):
        f = ttk.Frame(container)
        f.grid(row=row, column=column, columnspan=colspan, sticky="we", padx=10, pady=2)
        lbl = ttk.Label(f, text=text)
        lbl.grid(row=0, column=0, sticky="w")
        slider = ttk.Scale(
            f, from_=min_val, to=max_val, 
            variable=variable, 
            command=update_func, 
            orient='horizontal'
        )
        slider.grid(row=0, column=1, sticky="ew", padx=10)
        f.columnconfigure(1, weight=1)
        label_obj.lift() 
        label_obj.grid(in_=f, row=0, column=2, sticky="e", padx=5)
        update_func(variable.get())
        return slider
    
    create_checkbutton(main_frame, "Abilita Flusso Login/Iconizza Automatica", self.var_auto_login, row_counter, column=0)
    create_checkbutton(main_frame, "Iconizza alla pressione della (X) invece di chiudere", self.var_close_behavior, row_counter, column=1)
    create_checkbutton(main_frame, "Attiva SmartCat (Suggerimento Categorie)", self.var_smartcat_enabled, row_counter, column=2)
    row_counter += 1
    create_checkbutton(main_frame, "Data Odierna alla Riapertura", self.var_ico_set_date, row_counter, column=0)
    create_checkbutton(main_frame, "Abilita Notifiche Push (Gmail)", self.var_manda_push, row_counter, column=1)
    create_checkbutton(main_frame, "Carica Posizione Finestra Salvata", self.var_load_geometry, row_counter, column=2)
    row_counter += 1
    create_checkbutton(main_frame, "Abilita Smart Info-Point su Calendario", self.var_cal_tooltips, row_counter, column=0)
    create_checkbutton(main_frame, "Animazioni Totalizzatori e Icone Dinamiche", self.var_anima_tot, row_counter, column=1)
    create_checkbutton(main_frame, "Controllo Movimenti Duplicati", self.var_check_double, row_counter, column=2)
    row_counter += 1
    f_bank = ttk.Frame(main_frame)
    f_bank.grid(row=row_counter, column=0, columnspan=2, sticky="we", padx=10, pady=2)
    ttk.Label(f_bank, text="Link Banca:").pack(side="left")
    ent_bank = ttk.Entry(f_bank, textvariable=self.var_bank_link, width=40)
    ent_bank.pack(side="left", fill="x", expand=False, padx=5)
    f_toll = ttk.Frame(main_frame)
    f_toll.grid(row=row_counter, column=1, sticky="we", padx=10, pady=2)
    ttk.Label(f_toll, text="Tolleranza SmartCat (€):").pack(side="left")
    ttk.Spinbox(f_toll, from_=5, to=100, increment=1, width=5, textvariable=self.var_smartcat_toll, justify="center", state="readonly", style="Custom.TSpinbox").pack(side="left", padx=4)
    create_checkbutton(main_frame, "Abilita Beep Acustico Avvisi", self.var_beep_enabled, row_counter, column=2)
    row_counter += 1
    create_combobox(main_frame, "Tema UI:", self.var_thema, ["Chiaro", "Material", "Blu", "Obsidian", "Gold"], row_counter, column=2)
    row_counter += 1
    ttk.Separator(main_frame, orient='horizontal', style="Rosso.TSeparator").grid(row=row_counter, column=0, columnspan=3, sticky="ew", pady=5)
    row_counter += 1
    create_checkbutton(main_frame, "Abilita Web Server all'avvio", self.var_webserver_enabled, row_counter, column=0)
    create_entry(main_frame, "Porta Web Server (8080 default)", self.var_port, row_counter, column=1)
    create_checkbutton(main_frame, "Usa SSL (HTTPS)", self.var_usa_ssl, row_counter, column=2)
    row_counter += 1
    ttk.Separator(main_frame, orient='horizontal', style="Rosso.TSeparator").grid(row=row_counter, column=0, columnspan=3, sticky="ew", pady=5)
    row_counter += 1
    create_checkbutton(main_frame, "Abilita Database Condiviso (Rete)", self.var_shared_db, row_counter, column=0)
    f_path = ttk.Frame(main_frame)
    f_path.grid(row=row_counter, column=1, columnspan=2, sticky="we", padx=10, pady=2)
    ttk.Label(f_path, text="Path Database Condiviso (UNC o Unità)").pack(side="left")
    ttk.Entry(f_path, textvariable=self.var_shared_db_path, width=40).pack(side="left", fill="x", expand=True, padx=5)
    row_counter += 1
    create_entry(main_frame, "Porta UDP 1", self.var_udp_port_1, row_counter, column=0)
    create_entry(main_frame, "Porta UDP 2", self.var_udp_port_2, row_counter, column=1)
    row_counter += 1
    ttk.Separator(main_frame, orient='horizontal', style="Rosso.TSeparator").grid(row=row_counter, column=0, columnspan=3, sticky="ew", pady=5)
    row_counter += 1
    create_checkbutton(main_frame, "Avvisi Bloccanti (Richiedono Interazione)", self.var_use_wait_window, row_counter, column=0)
    create_slider_row(main_frame, "Timer Auto-Chiusura Avvisi (5-60 secondi)", 5, 60, self.var_warn_timeout_sec, update_warn_timeout_label, warn_timeout_label, row_counter, column=1, colspan=2)
    row_counter += 1
    create_checkbutton(main_frame, "Iconizza App in caso di Inattività", self.var_iconizza_inattivita, row_counter, column=0)
    create_slider_row(main_frame, "Timeout Inattività (5-60 minuti)", 5, 60, self.var_timeout_minuti, update_timeout_label, timeout_label, row_counter, column=1, colspan=2)
    row_counter += 1
    create_checkbutton(main_frame, "Attiva Promemoria Mensile Categorie Mancanti", self.var_recurring_reminder, row_counter, column=0)
    create_slider_row(main_frame, "Soglia Giorni Anticipo Promemoria (1-10 giorni)", 1, 10, self.var_soglia_ricorrenti, update_soglia_ricorrenti_label, soglia_ricorrenti_label, row_counter, column=1, colspan=2)
    row_counter += 1
    create_checkbutton(main_frame, "Abilita Carosello Statistiche", self.var_carosello_enabled, row_counter, column=0)
    create_slider_row(main_frame, "Intervallo Carosello (5-30 secondi)", 5, 30, self.var_carosello_intervallo_sec, update_carosello_intervallo_label, carosello_intervallo_label, row_counter, column=1, colspan=2)
    row_counter += 1
    ttk.Separator(main_frame, orient='horizontal', style="Rosso.TSeparator").grid(row=row_counter, column=0, columnspan=3, sticky="ew", pady=5)
    row_counter += 1       
    def formatta_target(sb, var):
        try:
            val = float(str(sb.get()).replace(",", "."))
            var.set(val)
            sb.set(f"{val:.2f}")
        except:
            var.set(0.0)
            sb.set("0.00")
    create_slider_row(main_frame, "Anni di Storico Dati (periodo di conservazione - 2-10 anni)", 2, 10, self.var_anni_da_mantenere, update_anni_label, anni_label, row_counter, column=0)
    main_frame.grid_slaves(row=row_counter, column=0)[0].grid(columnspan=2, sticky="we")
    f_target_m = ttk.Frame(main_frame)
    f_target_m.grid(row=row_counter, column=2, sticky="we", padx=10, pady=2)
    ttk.Label(f_target_m, text="Target Mese (€):", width=16, anchor="e").pack(side="left", padx=(0,4))
    sb_m = ttk.Spinbox(f_target_m, from_=0, to=9999, increment=50, width=7, textvariable=self.var_target_mese, justify="center", style="Custom.TSpinbox")
    sb_m.pack(side="left")
    sb_m.set(f"{self.var_target_mese.get():.2f}")
    sb_m.bind("<FocusOut>", lambda e: formatta_target(sb_m, self.var_target_mese))
    row_counter += 1
    create_slider_row(main_frame, "Max. Copie Backup da Mantenere (1-10)", 1, 10, self.var_max_backup, update_max_backup_label, max_backup_label, row_counter, column=0)
    main_frame.grid_slaves(row=row_counter, column=0)[0].grid(columnspan=2, sticky="we")
    f_target_a = ttk.Frame(main_frame)
    f_target_a.grid(row=row_counter, column=2, sticky="we", padx=10, pady=2)
    ttk.Label(f_target_a, text="Target Anno (€):", width=16, anchor="e").pack(side="left", padx=(0,4))
    sb_a = ttk.Spinbox(f_target_a, from_=0, to=99999, increment=500, width=7, textvariable=self.var_target_anno, justify="center", style="Custom.TSpinbox")
    sb_a.pack(side="left")
    sb_a.set(f"{self.var_target_anno.get():.2f}")
    sb_a.bind("<FocusOut>", lambda e: formatta_target(sb_a, self.var_target_anno))
    row_counter += 1
    ttk.Separator(main_frame, orient='horizontal', style="Rosso.TSeparator").grid(row=row_counter, column=0, columnspan=3, sticky="ew", pady=5)
    row_counter += 1
    create_checkbutton(main_frame, "Abilita Lettura Automatica Movimenti (Solo Gmail):", self.var_sync_enabled, row_counter)
    row_counter += 1
    self.icon_occhio = self.icone_gui.get("occhio")
    f_email = ttk.Frame(main_frame)
    f_email.grid(row=row_counter, column=0, columnspan=3, sticky="we", padx=10, pady=2)
    ttk.Label(f_email, text="Indirizzo Gmail:", width=25, anchor="w").pack(side="left")
    ent_email = ttk.Entry(f_email, textvariable=self.var_email_user, show="•")
    ent_email.config(width=60)
    ent_email.pack(side="left", fill="x", expand=False, padx=(5, 5))
    self.email_visible = False
    def toggle_email():
        self.email_visible = not self.email_visible
        ent_email.config(show="" if self.email_visible else "•")
    tk.Button(f_email, image=self.icon_occhio, command=toggle_email,
              bd=0, relief="flat", cursor="hand2", bg="#f0f0f0").pack(side="left", padx=(0, 5))
    ttk.Label(f_email, text="Modello Gemini:", anchor="w", width=15).pack(side="left", padx=(20, 0))
    ttk.Entry(f_email, textvariable=self.var_gemini_model, width=32).pack(side="left", padx=(5, 0))
    lbl_fetch = ttk.Label(f_email, text="🔍", cursor="hand2")
    lbl_fetch.pack(side="left", padx=(5, 0))
    lbl_fetch.bind("<Button-1>", lambda e: self.fetch_gemini_models())
    row_counter += 1
    f_pass = ttk.Frame(main_frame)
    f_pass.grid(row=row_counter, column=0, columnspan=3, sticky="we", padx=10, pady=2)
    ttk.Label(f_pass, text="App Password (16 cifre):", width=25, anchor="w").pack(side="left")
    ent_pass = ttk.Entry(f_pass, textvariable=self.var_app_password, width=115, show="•")
    ent_pass.pack(side="left", padx=5, fill="x", expand=True)
    self.icon_occhio = self.icone_gui.get("occhio")
    self.pass_visible = False
    def toggle_password():
            self.pass_visible = not self.pass_visible
            ent_pass.config(show="" if self.pass_visible else "•")
    tk.Button(f_pass, image=self.icon_occhio, command=toggle_password,
            bd=0, relief="flat", cursor="hand2", bg="#f0f0f0").pack(side="left", padx=(0, 5))
    import webbrowser
    img_google = self.icone_gui.get("google")
    btn_google = ttk.Label(
            f_pass,
            compound="left",
            image=img_google,
            text=" Genera" if img_google else "Genera",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2",
            padding=(10, 5)
    )
    btn_google.image = img_google
    btn_google.pack(side="left", padx=(0, 5))
    btn_google.bind(
            "<Button-1>",
            lambda e: webbrowser.open("https://myaccount.google.com/apppasswords")
    )
    row_counter += 1
    f_keys = ttk.Frame(main_frame)
    f_keys.grid(row=row_counter, column=0, columnspan=3, sticky="we", padx=10, pady=2)
    ttk.Label(f_keys, text="Filtri Email (Enel, Wind)").pack(side="left")
    ent_keys = ttk.Entry(f_keys, textvariable=self.var_parole_chiave, show="•")
    ent_keys.config(width=115)
    ent_keys.pack(side="left", fill="x", expand=False, padx=(58, 5))
    self.keys_visible = False
    def toggle_keys():
            self.keys_visible = not self.keys_visible
            ent_keys.config(show="" if self.keys_visible else "•")
    tk.Button(f_keys, image=self.icon_occhio, command=toggle_keys,
            bd=0, relief="flat", cursor="hand2", bg="#f0f0f0").pack(side="left", padx=(0, 5))
    row_counter += 1

    f_api = ttk.Frame(main_frame)
    f_api.grid(row=row_counter, column=0, columnspan=3, sticky="we", padx=10, pady=2)
    ttk.Label(f_api, text="Gemini API Key:", width=25, anchor="w").pack(side="left")
    ent_api = ttk.Entry(f_api, textvariable=self.var_gemini_api_key, width=115, show="•")
    ent_api.pack(side="left", padx=5, fill="x", expand=False)

    self.api_visible = False
    def toggle_api():
            self.api_visible = not self.api_visible
            ent_api.config(show="" if self.api_visible else "•")
    tk.Button(f_api, image=self.icon_occhio, command=toggle_api,
            bd=0, relief="flat", cursor="hand2", bg="#f0f0f0").pack(side="left", padx=(0, 5))

    img_api = self.icone_gui.get("filtri")
    btn_api = ttk.Label(
            f_api,
            compound="left",
            image=img_api,
            text=" Ottieni" if img_api else "Ottieni",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2",
            padding=(10, 5)
    )
    btn_api.image = img_api
    btn_api.pack(side="left", padx=(0, 5))
    btn_api.bind(
            "<Button-1>",
            lambda e: webbrowser.open("https://aistudio.google.com/app/apikey")
    )
    row_counter += 1
    def aggiorna_label_sync(*args):
        minuti = int(self.var_sync_intervallo.get())
        ore = minuti // 60
        min_residui = minuti % 60
        if min_residui == 0:
            testo = f"Sincronizza ogni: {ore} ore"
        else:
            testo = f"Sincronizza ogni: {ore} ore e {min_residui} min"
        sync_intervallo_label.config(text=testo)
    sync_intervallo_label = ttk.Label(main_frame, text="")
    sync_intervallo_label.grid(row=row_counter, column=0, sticky="w", padx=10)
    scale_sync = ttk.Scale(
        main_frame,
        from_=720,
        to=1440,
        variable=self.var_sync_intervallo,
        orient="horizontal",
        command=aggiorna_label_sync
    )
    scale_sync.grid(row=row_counter, column=1, columnspan=2, sticky="we", padx=10, pady=5)
    aggiorna_label_sync()
    row_counter += 1
    ttk.Separator(main_frame, orient='horizontal', style="Rosso.TSeparator").grid(row=row_counter, column=0, columnspan=3, sticky="ew", pady=(3, 3))
    row_counter += 1
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=row_counter, column=0, columnspan=3, pady=(4, 5), sticky="n")
    img_salva_cfg = self.icone_gui.get("salva")
    save_button = ttk.Label(
            button_frame,
            compound="left",
            image=img_salva_cfg,
            text=" Salva" if img_salva_cfg else "Salva",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2",
            padding=(10, 5)
    )
    save_button.image = img_salva_cfg
    save_button.grid(row=0, column=0, padx=5)
    save_button.bind("<Button-1>", lambda e: salva_e_chiudi())
    img_reset_cfg = self.icone_gui.get("reset")
    defaults_button = ttk.Label(
            button_frame,
            compound="left",
            image=img_reset_cfg,
            text=" Defaults" if img_reset_cfg else "Defaults",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2",
            padding=(10, 5)
    )
    defaults_button.image = img_reset_cfg
    defaults_button.grid(row=0, column=1, padx=5)
    defaults_button.bind("<Button-1>", lambda e: reset_defaults())
    img_chiudi_cfg = self.icone_gui.get("chiudi")
    close_button = ttk.Label(
            button_frame,
            compound="left",
            image=img_chiudi_cfg,
            text=" Chiudi" if img_chiudi_cfg else "Chiudi",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2",
            padding=(10, 5)
    )
    close_button.image = img_chiudi_cfg
    close_button.grid(row=0, column=2, padx=5)
    close_button.bind("<Button-1>", lambda e: chiudi_config())
    img_help_cfg = self.icone_gui.get("help")
    help_button = ttk.Label(
            button_frame,
            image=img_help_cfg,
            text="?" if not img_help_cfg else "",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2",
            padding=(5, 5)
    )
    help_button.image = img_help_cfg
    help_button.grid(row=0, column=3, padx=5)
    help_button.bind("<Button-1>", lambda e: mostra_help_configurazione())
    config_window.protocol("WM_DELETE_WINDOW", chiudi_config)
    config_window.bind_all("<Escape>", lambda e: chiudi_config())
    row_counter += 1
    config_window.withdraw()
    config_window.update_idletasks()
    width = max(config_window.winfo_reqwidth(), 1300)
    height = max(config_window.winfo_reqheight(), 650)
    config_window.minsize(width, height)
    screen_w = self.winfo_screenwidth()
    screen_h = self.winfo_screenheight()
    center_x = (screen_w // 2) - (width // 2)
    center_y = (screen_h // 2) - (height // 2)
    config_window.geometry(f"{width}x{height}+{center_x}+{center_y}")
    config_window.deiconify()
    config_window.lift()
    self.wait_window(config_window)
    
def fetch_gemini_models(self):
    import __main__ as _app
    genai = _app.genai
    if getattr(self, "_fetching_gemini", False):
        return
    self._fetching_gemini = True
    modelli = []
    try:
        api_key_pulita = self.var_gemini_api_key.get().strip()
        if not api_key_pulita:
            self.show_toast("Errore: La API Key inserita è vuota.")
            self._fetching_gemini = False
            return
        client = genai.Client(api_key=api_key_pulita)
        for m in client.models.list():
            actions = getattr(m, 'supported_actions', []) or []
            if "generateContent" in actions:
                modelli.append(m.name.replace("models/", ""))
    except Exception as ex:
        msg_completo = str(ex).strip()
        msg_breve = msg_completo.split('\n')[0]
        if len(msg_breve) > 60:
            msg_breve = msg_breve[:57] + "..."
        self.show_toast(f"Errore API: {msg_breve}")
        self.after(1000, lambda: setattr(self, "_fetching_gemini", False))
        return
    self._fetching_gemini = False
    if not modelli:
        self.show_toast("Nessun modello di generazione trovato.")
        return
    top = tk.Toplevel(self)
    top.withdraw()
    top.title("Modelli Gemini")
    top.configure(bg=self.COLOR_WIDGET_BG)
    top.transient(self)
    top.attributes("-topmost", True)
    top.grab_set()
    top.resizable(True, True)
    top.bind("<Escape>", lambda e: top.destroy())
    tk.Label(top, text="Seleziona modello:", bg=self.COLOR_WIDGET_BG,
             fg=self.TEXT_COLOR).pack(padx=10, pady=(10, 4), anchor="w")
    frame_lb = tk.Frame(top, bg=self.COLOR_WIDGET_BG)
    frame_lb.pack(padx=10, pady=(0, 6), fill="both", expand=True)
    scrollbar = ttk.Scrollbar(frame_lb, orient="vertical")
    lb = tk.Listbox(frame_lb, bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                    selectbackground=self.COLOR_HIGHLIGHT, width=40,
                    height=min(len(modelli), 14), yscrollcommand=scrollbar.set)
    scrollbar.config(command=lb.yview)
    lb.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="left", fill="y")
    for m in modelli:
        lb.insert(tk.END, m)
    cur = self.var_gemini_model.get().strip()
    if cur in modelli:
        idx = modelli.index(cur)
        lb.selection_set(idx)
        lb.see(idx)
    def conferma():
        sel = lb.curselection()
        if sel:
            self.var_gemini_model.set(modelli[sel[0]])
        top.destroy()
    lb.bind("<Double-Button-1>", lambda e: conferma())
    frame_btn = tk.Frame(top, bg=self.COLOR_WIDGET_BG)
    frame_btn.pack(fill="x", padx=10, pady=(4, 10))
    img_conferma = self.icone_gui.get("salva")
    btn_conferma = ttk.Label(frame_btn, compound="left", image=img_conferma,
                             text=" Seleziona" if img_conferma else "Seleziona",
                             background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                             cursor="hand2", padding=(10, 5))
    btn_conferma.image = img_conferma
    btn_conferma.pack(side="left")
    btn_conferma.bind("<Button-1>", lambda e: conferma())
    img_chiudi = self.icone_gui.get("chiudi")
    btn_chiudi = ttk.Label(frame_btn, compound="left", image=img_chiudi,
                           text=" Chiudi" if img_chiudi else "Chiudi",
                           background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                           cursor="hand2", padding=(10, 5))
    btn_chiudi.image = img_chiudi
    btn_chiudi.pack(side="right")
    btn_chiudi.bind("<Button-1>", lambda e: top.destroy())
    top.update_idletasks()
    top.minsize(500, 420)
    x = self.winfo_rootx() + (self.winfo_width() - 500) // 2
    y = self.winfo_rooty() + (self.winfo_height() - 420) // 2
    top.geometry(f"500x420+{x}+{y}")
    top.deiconify()
    top.update_idletasks()
    top.attributes("-topmost", False)
    
