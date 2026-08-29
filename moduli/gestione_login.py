#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import hashlib
import datetime
import threading
import tkinter as tk
from tkinter import ttk

def gestione_login(self):
    import __main__ as _app
    THEMA = _app.THEMA
    NAME = _app.NAME
    VERSION = _app.VERSION
    PW_FILE = _app.PW_FILE
    PROFILO_ATTIVO = _app.PROFILO_ATTIVO
    DB_DIR = _app.DB_DIR
    LOGIN_LCL = _app.LOGIN_LCL
    AUTO_ICONIZE_STARTUP = getattr(_app, "AUTO_ICONIZE_STARTUP", False)
    ABILITA_WEBSERVER = getattr(_app, "ABILITA_WEBSERVER", False)
    current_folder = os.path.basename(os.getcwd())

    TEMI = {
        "CHIARO":   {"BG": "#FFFFFF",  "BG_W": "white",    "FG": "black",    "ACCENT": "#007ACC", "FG_ERR": "red",     "FG_OK": "green",    "FG_DIM": "#555555", "FG_WARN": "#D19A66"},
        "MATERIAL": {"BG": "#20232A",  "BG_W": "#2A273F",  "FG": "white",    "ACCENT": "#61AFEF", "FG_ERR": "#E06C75", "FG_OK": "#98C379",  "FG_DIM": "#555555", "FG_WARN": "#D19A66"},
        "BLU":      {"BG": "#B3E5FC",  "BG_W": "#B3E5FC",  "FG": "#002F6C",  "ACCENT": "#0091EA", "FG_ERR": "red",     "FG_OK": "#2ed573",  "FG_DIM": "#004B8D", "FG_WARN": "#D19A66"},
        "OBSIDIAN": {"BG": "#000000",  "BG_W": "#000000",  "FG": "white",    "ACCENT": "#61AFEF", "FG_ERR": "#E06C75", "FG_OK": "#98C379",  "FG_DIM": "#555555", "FG_WARN": "#D19A66"},
        "GOLD":     {"BG": "#0A0800",  "BG_W": "#0D0A00",  "FG": "#F5E6C8",  "ACCENT": "#C9A84C", "FG_ERR": "#E06C75", "FG_OK": "#98C379",  "FG_DIM": "#555555", "FG_WARN": "#D19A66"},
    }
    t = TEMI.get(THEMA, TEMI["OBSIDIAN"])
    BG      = t["BG"]
    BG_W    = t["BG_W"]
    FG      = t["FG"]
    ACCENT  = t["ACCENT"]
    FG_ERR  = t["FG_ERR"]
    FG_OK   = t["FG_OK"]
    FG_DIM  = t["FG_DIM"]
    FG_WARN = t["FG_WARN"]
    def hash_pw(pw):
        return hashlib.sha256(pw.encode()).hexdigest()
    def salva_hash(pw):
        with open(PW_FILE, "w") as f:
            json.dump({"hash": hash_pw(pw)}, f)
    def leggi_hash():
        if not os.path.exists(PW_FILE): return None
        try:
            with open(PW_FILE) as f: 
                return json.load(f).get("hash")
        except: return None
    login_riuscito = [False]
    salvata = leggi_hash()
    def crea_campo_password_moderno(parent, etichetta=""):
        if etichetta:
            tk.Label(parent, text=etichetta, bg=BG, fg=FG,
                     font=("Arial", 9, "bold")).pack(pady=(10, 2), anchor="w", padx=40)
        frame_border = tk.Frame(parent, bg=ACCENT, bd=0)
        frame_border.pack(pady=5, padx=40, fill="x")
        frame_container = tk.Frame(frame_border, bg=BG_W, bd=0)
        frame_container.pack(padx=1, pady=1, fill="both", expand=True)
        visibile = tk.BooleanVar(value=False)
        entry_pw = tk.Entry(frame_container, show="*", bg=BG_W, fg="white" if THEMA != "CHIARO" else "black",
                            insertbackground="white" if THEMA != "CHIARO" else "black",
                            font=("Arial", 11), relief="flat", bd=0, highlightthickness=0)
        entry_pw.pack(side="left", padx=10, pady=6, fill="x", expand=True)
        def toggle_visibilita():
            img_aperto = self.icone_gui.get("occhio")
            img_chiuso = self.icone_gui.get("occhio_chiuso")
            if visibile.get():
                entry_pw.config(show="*")
                lbl_occhio.config(image=img_aperto, text="") if img_aperto else lbl_occhio.config(text="👁️", fg=FG)
            else:
                entry_pw.config(show="")
                lbl_occhio.config(image=img_chiuso, text="") if img_chiuso else lbl_occhio.config(text="🔒", fg=ACCENT)
            visibile.set(not visibile.get())
        lbl_occhio = tk.Label(frame_container, font=("Arial", 12), bg=BG_W, fg=FG, cursor="hand2")
        img_init = self.icone_gui.get("occhio")
        if img_init:
            lbl_occhio.config(image=img_init)
            lbl_occhio.image = img_init
        else:
            lbl_occhio.config(text="👁️")
        lbl_occhio.pack(side="right", padx=10)
        lbl_occhio.bind("<Button-1>", lambda e: toggle_visibilita())
        entry_pw.bind("<FocusIn>",  lambda e: frame_border.config(bg=ACCENT))
        entry_pw.bind("<FocusOut>", lambda e: frame_border.config(bg=FG_DIM))
        return entry_pw
    def cambia_password(parent_login, field_pw, lbl_timeout, reset_fn):
        parent_login.withdraw()
        win = tk.Toplevel(self)
        win.title(f"Password - {NAME} v.{VERSION}")
        win.configure(bg=BG)
        win.resizable(False, False)
        w_win, h_win = 350, 380
        x_win = self.winfo_screenwidth() // 2 - w_win // 2
        y_win = self.winfo_screenheight() // 2 - h_win // 2
        win.geometry(f"{w_win}x{h_win}+{x_win}+{y_win}")
        win.attributes("-topmost", True)
        win.lift()
        def on_close_cambio():
            if _cp_timeout_id[0]:
                win.after_cancel(_cp_timeout_id[0])
            reset_fn()
            win.destroy()
            parent_login.deiconify()
            parent_login.lift()
            parent_login.focus_force()
            field_pw.focus_force()
        win.protocol("WM_DELETE_WINDOW", on_close_cambio)
        win.wait_visibility()
        win.grab_set()
        lbl_cp_timeout = tk.Label(win, text="⏱ Chiusura automatica tra 60s",
                                  font=("Arial", 8), bg=BG, fg=FG_DIM)
        lbl_cp_timeout.place(x=0, y=362, relwidth=1.0)
        _cp_timeout_id = [None]
        _cp_timeout_sec = [60]
        def _cp_timeout_tick():
            if not win.winfo_exists():
                return
            _cp_timeout_sec[0] -= 1
            if _cp_timeout_sec[0] <= 0:
                on_close_cambio()
                return
            colore = FG_ERR if _cp_timeout_sec[0] <= 10 else FG_DIM
            lbl_cp_timeout.config(text=f"⏱ Chiusura automatica tra {_cp_timeout_sec[0]}s", fg=colore)
            _cp_timeout_id[0] = win.after(1000, _cp_timeout_tick)
        def _cp_reset_timeout(event=None):
            try:
                if not win.winfo_exists():
                    return
            except Exception:
                return
            if _cp_timeout_id[0]:
                win.after_cancel(_cp_timeout_id[0])
            _cp_timeout_sec[0] = 60
            lbl_cp_timeout.config(text="⏱ Chiusura automatica tra 60s", fg=FG_DIM)
            _cp_timeout_id[0] = win.after(1000, _cp_timeout_tick)
        win.bind("<Key>",    _cp_reset_timeout)
        win.bind("<Motion>", _cp_reset_timeout)
        win.bind("<Button>", _cp_reset_timeout)
        _cp_reset_timeout()
        tk.Label(win, text="🔄", font=("Arial", 20), bg=BG, fg=ACCENT).pack(pady=(2, 0))
        tk.Label(win, text="CAMBIO PASSWORD", font=("Arial", 10, "bold"), bg=BG, fg=FG_ERR).pack(pady=(0, 2))
        mess = tk.Label(win, text="", fg=FG_ERR, bg=BG, font=("Arial", 9))
        entry_attuale  = crea_campo_password_moderno(win, "Password Vecchia")
        entry_nuova    = crea_campo_password_moderno(win, "Nuova Password (vuota per disattivare.)")
        entry_conferma = crea_campo_password_moderno(win, "Conferma Nuova")
        win.update_idletasks()
        win.after(200, lambda: entry_attuale.focus_force())
        mess.pack(pady=0)
        def esegui_conferma_cambio(event=None):
            attuale  = entry_attuale.get()
            nuova    = entry_nuova.get()
            conferma = entry_conferma.get()
            if hash_pw(attuale) != leggi_hash():
                mess.config(text="Password attuale errata!", fg=FG_ERR)
                entry_attuale.delete(0, tk.END)
                entry_nuova.delete(0, tk.END)
                entry_conferma.delete(0, tk.END)
                entry_attuale.focus_set()
                return
            if not nuova:
                salva_hash("")
                def lampeggia(n=6):
                    if n <= 0:
                        on_close_cambio()
                        return
                    attuale_txt = mess.cget("text")
                    mess.config(text="" if attuale_txt else "Protezione Password disattivata!", fg=FG_OK)
                    win.after(300, lambda: lampeggia(n-1))
                lampeggia()
                return
            if nuova != conferma:
                mess.config(text="Le password non corrispondono!", fg=FG_ERR)
                entry_attuale.delete(0, tk.END)
                entry_nuova.delete(0, tk.END)
                entry_conferma.delete(0, tk.END)
                entry_attuale.focus_set()
                return
            salva_hash(nuova)
            mess.config(text="Password Aggiornata!", fg=FG_OK)
            win.after(1200, lambda: [win.destroy(), parent_login.deiconify(), parent_login.lift(), parent_login.focus_force(), field_pw.focus_force()])
        for entry in [entry_attuale, entry_nuova, entry_conferma]:
            entry.bind("<Return>", esegui_conferma_cambio)
            entry.bind("<KP_Enter>", esegui_conferma_cambio)
        frame_btn = tk.Frame(win, bg=BG)
        frame_btn.pack(pady=(10, 0), fill="x", padx=40)
        img_annulla_pw = self.icone_gui.get("chiudi")
        btn_annulla = tk.Label(frame_btn, compound="left", image=img_annulla_pw,
                text=" ANNULLA" if img_annulla_pw else "ANNULLA",
                bg=BG, fg=FG, font=("Arial", 9, "bold"), cursor="hand2", padx=15, pady=8)
        btn_annulla.pack(side="left", expand=True)
        btn_annulla.bind("<Button-1>", lambda e: on_close_cambio())
        img_conferma_pw = self.icone_gui.get("api_key")
        btn_conferma = tk.Label(frame_btn, compound="left", image=img_conferma_pw,
                text=" CONFERMA" if img_conferma_pw else "CONFERMA",
                bg=BG, fg=FG, font=("Arial", 9, "bold"), cursor="hand2", padx=15, pady=8)
        btn_conferma.pack(side="right", expand=True)
        btn_conferma.bind("<Button-1>", lambda e: esegui_conferma_cambio())

    def _cambia_profilo_da_login(nome_profilo, login_win):
        import __main__ as _app
        from moduli.costanti import salva_profilo_attivo
        from moduli.profili import _restart_application
        if nome_profilo != "Principale":
            os.makedirs(os.path.join(_app.PROFILI_DIR, nome_profilo, "db"), exist_ok=True)
        salva_profilo_attivo(_app.PATH_LOCALE, nome_profilo)
        try:
            login_win.destroy()
        except Exception:
            pass
        try:
            self._on_close_lock()
        except Exception:
            pass
        _restart_application()

    def mostra_finestra_login():
        tentativi_falliti = 0
        MAX_TENTATIVI = 3
        is_primo_accesso = not os.path.exists(PW_FILE)
        ultimo_login_str = "Nessun accesso precedente"
        bloccato_fino = None
        if os.path.exists(LOGIN_LCL):
            try:
                with open(LOGIN_LCL, "r") as f:
                    dati = json.load(f)
                ultimo_login_str = dati.get("ultimo_login", "N/D")
                bf = dati.get("bloccato_fino")
                if bf:
                    bloccato_fino = datetime.datetime.strptime(bf, "%Y-%m-%d %H:%M:%S")
            except: pass
        login = tk.Toplevel(self)
        self.set_app_icon()
        login.title(f"Accesso {NAME} v.{VERSION}")
        login.configure(bg=BG)
        login.resizable(False, False)
        def chiusura():
            self._on_close_lock()
            os._exit(0)
        login.protocol("WM_DELETE_WINDOW", chiusura)
        w, h = 350, 380
        x = self.winfo_screenwidth() // 2 - w // 2
        y = self.winfo_screenheight() // 2 - h // 2
        login.geometry(f"{w}x{h}+{x}+{y}")
        login.update_idletasks()
        login.attributes("-topmost", True)
        login.lift()
        login.focus_force()
        login.grab_set()
        _timeout_id = [None]
        _timeout_sec = [60]
        lbl_timeout = tk.Label(login, text="⏱ Chiusura automatica tra 60s",
                               font=("Arial", 8), bg=BG, fg=FG_DIM)
        lbl_timeout.place(x=0, y=360, relwidth=1.0)
        def _reset_timeout(event=None):
            try:
                if not login.winfo_exists():
                    return
            except Exception:
                return
            if _timeout_id[0]:
                login.after_cancel(_timeout_id[0])
            _timeout_sec[0] = 60
            lbl_timeout.config(text="⏱ Chiusura automatica tra 60s", fg=FG_DIM)
            _timeout_id[0] = login.after(1000, _timeout_tick)
        def _timeout_tick():
            try:
                if not login.winfo_exists():
                    return
            except Exception:
                return
            _timeout_sec[0] -= 1
            if _timeout_sec[0] <= 0:
                chiusura()
                return
            colore = FG_ERR if _timeout_sec[0] <= 10 else FG_DIM
            lbl_timeout.config(text=f"⏱ Chiusura automatica tra {_timeout_sec[0]}s", fg=colore)
            _timeout_id[0] = login.after(1000, _timeout_tick)
        _reset_timeout()
        login.bind_all("<Key>",    _reset_timeout)
        login.bind_all("<Motion>", _reset_timeout)
        login.bind_all("<Button>", _reset_timeout)
        tk.Label(login, text="🔒", font=("Arial", 30), bg=BG, fg=FG).pack(pady=(10, 0))
        if is_primo_accesso:
            tk.Label(login, text="BENVENUTO!", font=("Arial", 16, "bold"), bg=BG, fg=FG_OK).pack(pady=(10, 0))
            tk.Label(login, text="Configurazione Iniziale:\nImposta una password per proteggere i tuoi dati,\no premi INVIO per continuare senza protezione.",
                     font=("Arial", 10), bg=BG, fg=FG, justify="center").pack(pady=5)
        else:
            tk.Label(login, text="AREA RISERVATA", font=("Arial", 16, "bold"), bg=BG, fg=FG_ERR).pack(pady=(10, 0))
            tk.Label(login, text=f"Ultimo accesso: {ultimo_login_str}", font=("Arial", 9, "italic"),
                     bg=BG, fg=FG_WARN).pack(pady=5)
            tk.Label(login, text=f"S-ID: {self.SESSION_ID}", font=("Arial", 8),
                     bg=BG, fg=FG_WARN).place(x=290, y=20)

        from moduli.profili import elenco_profili, _etichetta_profilo
        profili_disponibili = elenco_profili(self)
        if len(profili_disponibili) > 1:
            mappa_etichette = {_etichetta_profilo(self, nome): nome for nome in profili_disponibili}
            etichetta_corrente = _etichetta_profilo(self, PROFILO_ATTIVO)
            frame_sel = tk.Frame(login, bg=BG)
            frame_sel.pack(pady=(0, 4))
            tk.Label(frame_sel, text="Profilo:", font=("Arial", 9, "bold"), bg=BG, fg=FG_DIM).pack(side="left", padx=(0, 6))

            img_profilo_icon = self.icone_gui.get("promemoria")

            var_profilo = tk.StringVar(value=etichetta_corrente)

            def _on_profilo_selezionato(etichetta_scelta):
                nome_scelto = mappa_etichette.get(etichetta_scelta)
                if nome_scelto and nome_scelto != PROFILO_ATTIVO:
                    _cambia_profilo_da_login(nome_scelto, login)

            menu_profilo = tk.OptionMenu(frame_sel, var_profilo, *mappa_etichette.keys(),
                              command=_on_profilo_selezionato)
            menu_profilo.config(bg=BG_W, fg=FG, activebackground=ACCENT, activeforeground=BG_W,
                     highlightthickness=1, highlightbackground=ACCENT, highlightcolor=ACCENT,
                     bd=0, relief="flat", font=("Arial", 9), cursor="hand2",
                     padx=10, pady=4, indicatoron=0,
                     compound="left", image=img_profilo_icon if img_profilo_icon else "")
            menu_profilo["menu"].config(bg=BG_W, fg=FG, activebackground=ACCENT, activeforeground=BG_W,
                             font=("Arial", 9))
            menu_profilo.pack(side="left")
        elif not is_primo_accesso:
            tk.Label(login, text=f"Utente: {PROFILO_ATTIVO if PROFILO_ATTIVO != 'Principale' else current_folder}", font=("Arial", 11), bg=BG, fg=FG_DIM).pack()
        entry_pw = crea_campo_password_moderno(login, "Inserisci Password")
        login.update_idletasks()
        login.after(200, lambda: entry_pw.focus_force())
        messaggio_errore = tk.Label(login, text="", fg=FG_ERR, font=("Arial", 9), bg=BG)
        messaggio_errore.pack(pady=5)
        testo_da_mostrare = "⚠️ AVVISO LEGALE L'accesso non autorizzato a questo sistema è perseguibile ai sensi dell'Art. 615-ter del Codice Penale. Ogni tentativo di intrusione sarà perseguito nei termini di legge a tutela della riservatezza dei dati contenuti. "
        frame_marquee = tk.Frame(login, bg=BG, width=250, height=20)
        frame_marquee.pack_propagate(False)
        frame_marquee.place(x=50, y=2)
        lbl_scroll = tk.Label(frame_marquee, text=testo_da_mostrare + "          " + testo_da_mostrare,
                             font=("Courier new", 8, "bold"), bg=BG, fg="orange")
        lbl_scroll.place(x=0, y=0)
        login.update_idletasks()
        larghezza_testo_singolo = lbl_scroll.winfo_reqwidth() // 2
        self.x_pos = 0
        def anima_fluida():
            if not login.winfo_exists(): return
            self.x_pos -= 1
            if abs(self.x_pos) >= larghezza_testo_singolo:
                self.x_pos = 0
            lbl_scroll.place(x=self.x_pos, y=0)
            login.after(30, anima_fluida)
        anima_fluida()
        def esegui_conferma_login(event=None):
            nonlocal tentativi_falliti
            if bloccato_fino and (bloccato_fino - datetime.datetime.now()).total_seconds() > 0:
                return
            inserita = entry_pw.get()
            salvata = leggi_hash()
            adesso = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            if salvata is None:
                salva_hash(inserita)
                try:
                    with open(LOGIN_LCL, "r") as f: log = json.load(f)
                except: log = {}
                log_eventi = log.get("eventi", []) if isinstance(log, dict) else []
                log_eventi.append({"timestamp": adesso, "tipo": "PRIMO_ACCESSO", "utente": current_folder, "session_id": getattr(self, "SESSION_ID", "N/D")})
                try:
                    with open(LOGIN_LCL, "w") as f: json.dump({"ultimo_login": adesso, "eventi": log_eventi[-20:]}, f, indent=2)
                except: pass
                login_riuscito[0] = True
                login.destroy()
                return
            if hash_pw(inserita) == salvata:
                try:
                    with open(LOGIN_LCL, "r") as f: log = json.load(f)
                except: log = []
                log_eventi = log.get("eventi", []) if isinstance(log, dict) else []
                log_eventi.append({"timestamp": adesso, "tipo": "LOGIN_OK", "utente": current_folder, "session_id": getattr(self, "SESSION_ID", "N/D")})
                try:
                    with open(LOGIN_LCL, "w") as f: json.dump({"ultimo_login": adesso, "eventi": log_eventi[-20:]}, f, indent=2)
                except: pass
                login_riuscito[0] = True
                login.destroy()
            else:
                tentativi_falliti += 1
                entry_pw.delete(0, tk.END)
                try:
                    with open(LOGIN_LCL, "r") as f: log = json.load(f)
                except: log = {}
                log_eventi = log.get("eventi", []) if isinstance(log, dict) else []
                log_eventi.append({"timestamp": adesso, "tipo": "LOGIN_FAIL", "tentativo": f"{tentativi_falliti}/{MAX_TENTATIVI}", "utente": current_folder, "session_id": getattr(self, "SESSION_ID", "N/D"), "password_tentata": inserita})
                try:
                    with open(LOGIN_LCL, "w") as f: json.dump({"ultimo_login": adesso, "eventi": log_eventi[-20:]}, f, indent=2)
                except: pass
                if tentativi_falliti >= MAX_TENTATIVI:
                    messaggio_errore.config(text=f"Password Errata ({tentativi_falliti}/{MAX_TENTATIVI})")
                    login.update()
                    self.invia_notifica_fallimento("Login Locale")
                    try:
                        with open(LOGIN_LCL, "r") as f: log = json.load(f)
                    except: log = {}
                    log["bloccato_fino"] = (datetime.datetime.now() + datetime.timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
                    try:
                        with open(LOGIN_LCL, "w") as f: json.dump(log, f, indent=2)
                    except: pass
                    chiusura()
                else:
                    messaggio_errore.config(text=f"Password Errata ({tentativi_falliti}/{MAX_TENTATIVI})")
        entry_pw.bind("<Return>", esegui_conferma_login)
        entry_pw.bind("<KP_Enter>", esegui_conferma_login)
        frame_login_btn = tk.Frame(login, bg=BG)
        frame_login_btn.pack(pady=(1, 0), fill="x", padx=40)
        img_entra = self.icone_gui.get("api_key")
        btn_entra = ttk.Label(frame_login_btn, compound="left", image=img_entra,
                text=" ENTRA" if img_entra else "ENTRA",
                background=BG, foreground=FG, cursor="hand2",
                padding=(10, 3), width=8, anchor="center", font=("Arial", 9, "bold"))
        btn_entra.pack(side="left")
        def aggiorna_blocco():
            if bloccato_fino is None: return
            restanti = (bloccato_fino - datetime.datetime.now()).total_seconds()
            if restanti > 0:
                minuti = int(restanti // 60)
                secondi = int(restanti % 60)
                messaggio_errore.config(text=f"🔒 Bloccato — riprova tra {minuti:02d}:{secondi:02d}")
                btn_entra.config(cursor="X_cursor")
                if not is_primo_accesso:
                    btn_cambio_pw.config(cursor="X_cursor", fg=FG_DIM)
                login.after(1000, aggiorna_blocco)
            else:
                messaggio_errore.config(text="")
                btn_entra.config(cursor="hand2")
                if not is_primo_accesso:
                    btn_cambio_pw.config(cursor="hand2", fg=ACCENT)
        btn_entra.bind("<Button-1>", lambda e: esegui_conferma_login())
        img_chiudi_log = self.icone_gui.get("chiudi")
        btn_chiudi_log = ttk.Label(frame_login_btn, compound="left", image=img_chiudi_log,
                text=" CHIUDI" if img_chiudi_log else "CHIUDI",
                background=BG, foreground=FG, cursor="hand2",
                padding=(10, 3), width=8, anchor="center", font=("Arial", 9, "bold"))
        btn_chiudi_log.pack(side="right")
        btn_chiudi_log.bind("<Button-1>", lambda e: chiusura())
        if not is_primo_accesso:
            btn_cambio_pw = tk.Label(login, text="Cambio Password", bg=BG, fg=ACCENT,
                    font=("Arial", 8, "underline"), cursor="hand2")
            btn_cambio_pw.pack(pady=(30, 0))
            def cambio_pw_se_non_bloccato(e):
                if bloccato_fino and (bloccato_fino - datetime.datetime.now()).total_seconds() > 0:
                    return
                entry_pw.delete(0, tk.END)
                cambia_password(login, entry_pw, lbl_timeout, _reset_timeout)
            btn_cambio_pw.bind("<Button-1>", cambio_pw_se_non_bloccato)
        aggiorna_blocco()
        login.wait_window()

    _web_switch_marker = os.path.join(DB_DIR, ".web_switch_pending")
    _da_switch_web = os.path.exists(_web_switch_marker)
    if _da_switch_web:
        try:
            os.remove(_web_switch_marker)
        except Exception:
            pass

    if AUTO_ICONIZE_STARTUP or _da_switch_web:
        login_riuscito[0] = True
        motivo = "AUTO_ICONIZE_STARTUP" if AUTO_ICONIZE_STARTUP else "switch profilo da web"
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Login bypassato ({motivo}).")
    if not login_riuscito[0]:
        mostra_finestra_login()
    if login_riuscito[0]:
        if ABILITA_WEBSERVER:
            threading.Thread(target=self.start_web_server, daemon=True).start()
            threading.Thread(target=self.start_watchdog_server, daemon=True).start()
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Server web avviato.")
        if AUTO_ICONIZE_STARTUP:
            self.after(500, self._iconizza_finestra_startup)
        return True
    return False

