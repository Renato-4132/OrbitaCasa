#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import threading
import datetime

def _log(msg):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {msg}")

def _cambio_percorso_con_riavvio(self, nuova, prec):
    import __main__ as _app
    from moduli.costanti import carica_costanti
    from moduli.profili import _restart_application
    def _ripristina():
        try:
            with open(_app.CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            cfg["shared_db"] = prec.get("shared_db", False)
            cfg["shared_db_path"] = prec.get("shared_db_path", _app.PATH_LOCALE)
            with open(_app.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=4)
        except Exception as e:
            _log(f"Ripristino config condiviso: {e}")
        return False
    if not self.show_custom_askyesno(
        "Database condiviso",
        "Il cambio del database condiviso richiede il riavvio dell'app.\n\nRiavviare ora?"
    ):
        return _ripristina()
    if nuova.get("shared_db") and nuova.get("shared_db_path"):
        try:
            os.makedirs(nuova["shared_db_path"], exist_ok=True)
        except Exception as e:
            self.show_toast(f"Impossibile creare la cartella condivisa, cambio annullato: {e}")
            return _ripristina()
    try:
        self.save_db()
    except Exception as e:
        self.show_toast(f"Impossibile salvare i dati correnti, cambio annullato: {e}")
        return _ripristina()
    boot_dir = os.path.join(_app.PATH_LOCALE, "db")
    os.makedirs(boot_dir, exist_ok=True)
    boot_file = os.path.join(boot_dir, "config.json")
    try:
        with open(boot_file, "r", encoding="utf-8") as f:
            boot_cfg = json.load(f)
    except Exception:
        boot_cfg = {}
    boot_cfg["shared_db"] = nuova.get("shared_db", False)
    boot_cfg["shared_db_path"] = nuova.get("shared_db_path", _app.PATH_LOCALE)
    with open(boot_file, "w", encoding="utf-8") as f:
        json.dump(boot_cfg, f, ensure_ascii=False, indent=2)
    nuovo_cfg_file = carica_costanti(_app.PATH_LOCALE)["CONFIG_FILE"]
    os.makedirs(os.path.dirname(nuovo_cfg_file), exist_ok=True)
    try:
        with open(nuovo_cfg_file, "r", encoding="utf-8") as f:
            cfg_dest = json.load(f)
    except Exception:
        cfg_dest = dict(nuova)
    cfg_dest["shared_db"] = nuova.get("shared_db", False)
    cfg_dest["shared_db_path"] = nuova.get("shared_db_path", _app.PATH_LOCALE)
    with open(nuovo_cfg_file, "w", encoding="utf-8") as f:
        json.dump(cfg_dest, f, indent=4)
    self.show_toast("Riavvio per applicare il database condiviso...")
    try:
        self._on_close_lock()
    except Exception:
        pass
    self.after(900, _restart_application)
    return True

def _avvia_udp_rete(self):
    import __main__ as _app
    ev_old = getattr(self, "_udp_stop", None)
    if ev_old is not None:
        ev_old.set()
    if not _app.DB_CONDIVISO:
        self._udp_stop = None
        return
    ev = threading.Event()
    self._udp_stop = ev

    def _parti():
        if getattr(self, "_udp_stop", None) is ev:
            threading.Thread(target=_app.ascolta_aggiornamenti_rete, args=(self, ev), daemon=True).start()

    if ev_old is not None:
        self.after(1300, _parti)
    else:
        _parti()

def _riavvia_webserver_a_caldo(self):
    import __main__ as _app
    abilitato = bool(_app.ABILITA_WEBSERVER)
    self._web_gen = getattr(self, "_web_gen", 0) + 1
    srv = getattr(self, "server", None)
    if abilitato:
        self._crea_lbl_webport()
    else:
        self._rimuovi_lbl_webport()

    def _lavoro():
        try:
            if srv is not None:
                srv.shutdown()
                srv.server_close()
        except Exception as e:
            _log(f"Arresto web server: {e}")
        if abilitato:
            self._server_running = True
            threading.Thread(target=self.start_web_server, daemon=True).start()
            threading.Thread(target=self.start_watchdog_server, daemon=True).start()
            _log("Web server riavviato con la nuova configurazione.")
        else:
            _log("Web server disattivato.")

    threading.Thread(target=_lavoro, daemon=True).start()

def applica_configurazione_a_caldo(self):
    import __main__ as _app
    esito = "ok"

    DEFAULT = _app.DEFAULT_CONFIG
    prec = dict(getattr(_app, "app_config_globale", {}) or {})
    errori = []

    def _norm(k, v):
        if k == "parole_chiave":
            if isinstance(v, str):
                v = v.split(",")
            return [x.strip() for x in (v or []) if str(x).strip()]
        return v

    def vecchio(k):
        return _norm(k, prec.get(k, DEFAULT.get(k)))

    def passo(nome, funzione):
        try:
            funzione()
        except Exception as e:
            errori.append(f"{nome}: {e}")
            _log(f"⚠️ Applicazione '{nome}' non riuscita: {e}")

    nuova = _app.aggiorna_configurazione_globale()

    def cambiato(*chiavi):
        return any(vecchio(k) != _norm(k, nuova.get(k, DEFAULT.get(k))) for k in chiavi)

    _pr = nuova.get("shared_db_path") or ""
    _atteso = _pr if nuova.get("shared_db") and os.path.exists(_pr) else _app.PATH_LOCALE
    _np = lambda p: os.path.normcase(os.path.normpath(p))
    percorsi_cambiati = cambiato("shared_db", "shared_db_path") or _np(_app.RADICE_DATI) != _np(_atteso)
    if percorsi_cambiati:
        if _cambio_percorso_con_riavvio(self, nuova, prec):
            return "riavvio"
        nuova = _app.aggiorna_configurazione_globale()
        percorsi_cambiati = False
        esito = "percorso_non_cambiato"

    def _globali():
        _app._applica_globali_da_config(nuova)
        _app.app_config_globale = nuova
        self.CHECK_DOPPI_MOV = _app.CHECK_DOPPI_MOV
        self.salva_geometria = _app.SALVA_GEOMETRIA_INIZIALE
        self.suggerimenti_attivi = _app.SMARTCAT
        self.intervallo_scorrimento = _app.CAROSELLO_INTERVALLO
        self._timeout_inattivita = _app.TIMEOUT_INATTIVITA_MS
    passo("variabili globali", _globali)

    if cambiato("thema"):
        passo("tema", lambda: self.cambia_tema_a_caldo(nuova.get("thema", "OBSIDIAN")))

    def _chiusura():
        self.protocol("WM_DELETE_WINDOW", self._iconizza_finestra_x if _app.CLOSE else self._on_close)
    passo("pulsante chiusura", _chiusura)

    if cambiato("iconizza_inattivita", "inactivity_timeout_ms"):
        def _inattivita():
            for attr in ("_timer_inattivita", "_countdown_timer_id"):
                t = getattr(self, attr, None)
                if t:
                    try:
                        self.after_cancel(t)
                    except Exception:
                        pass
                    setattr(self, attr, None)
            spl = getattr(self, "_countdown_splash", None)
            if spl:
                try:
                    spl.destroy()
                except Exception:
                    pass
                self._countdown_splash = None
            if _app.ICONIZZA_INATTIVITA:
                self._attiva_timer_inattivita()
        passo("timer inattività", _inattivita)

    def _carosello():
        if _app.CAROSELLO:
            self._crea_btn_carosello()
            if self.var_carosello_enabled.get():
                self.riavvia_scorrimento_automatico()
        else:
            self._rimuovi_btn_carosello()
    passo("carosello", _carosello)

    if cambiato("cal_tooltips_enabled"):
        def _tooltip():
            def _slega(w):
                for seq in ("<Motion>", "<Leave>"):
                    w.unbind(seq)
                for c in w.winfo_children():
                    _slega(c)
            if _app.CAL_TOOLTIPS:
                self.applica_ricorsivo_tooltip(self.cal)
            else:
                _slega(self.cal)
                try:
                    self.tooltip_win.withdraw()
                except Exception:
                    pass
        passo("tooltip calendario", _tooltip)

    if cambiato("sync_dati_enabled", "sync_intervallo_min"):
        def _sync():
            job = getattr(self, "_job_sincro", None)
            if job:
                try:
                    self.after_cancel(job)
                except Exception:
                    pass
                self._job_sincro = None
            if _app.SYNC_DATI:
                if vecchio("sync_dati_enabled"):
                    attesa = int(_app.SYNC_INT_MIN) * 60 * 1000
                else:
                    attesa = 5000
                self._job_sincro = self.after(attesa, self.pianifica_sincro_web)
        passo("sincronizzazione", _sync)

    if cambiato("enable_recurring_reminder"):
        def _ricorrenti():
            job = getattr(self, "_job_ricorrenti", None)
            if job:
                try:
                    self.after_cancel(job)
                except Exception:
                    pass
                self._job_ricorrenti = None
            if _app.CHECK_MESE:
                if not hasattr(self, "_last_dismiss_date"):
                    self._last_dismiss_date = self._carica_dismiss_fm()
                self._job_ricorrenti = self.after(3000, self.controlla_ricorrenti_a_fine_mese)
        passo("promemoria ricorrenti", _ricorrenti)

    if percorsi_cambiati or cambiato("webserver_enabled", "usa_ssl", "webserver_port", "gemini_api_key", "email_user",
                "app_password", "parole_chiave", "shared_db", "shared_db_path"):
        passo("web server", lambda: self._riavvia_webserver_a_caldo())

    if percorsi_cambiati or cambiato("udp_port_1", "udp_port_2"):
        passo("rete condivisa", lambda: self._avvia_udp_rete())

    if cambiato("target_mese", "target_anno"):
        def _target():
            self.budget_mensile = _app.TARGET_MESE
            self.budget_annuale = _app.TARGET_ANNO
            fmt = _app._fmt_it
            if hasattr(self, "lbl_budget_mese_widget"):
                self.lbl_budget_mese_widget.config(
                    text=f"Target Mese: € {fmt(_app.TARGET_MESE)}" if _app.TARGET_MESE > 0 else "Target Mese: N/D")
            if hasattr(self, "lbl_budget_anno_widget"):
                self.lbl_budget_anno_widget.config(
                    text=f"Target Anno: € {fmt(_app.TARGET_ANNO)}" if _app.TARGET_ANNO > 0 else "Target Anno: N/D")
        passo("target di spesa", _target)

    def _dati():
        if not percorsi_cambiati:
            self.save_db()
        self.load_db()
        if percorsi_cambiati:
            self.carica_memoria_descrizioni()
            self.aggiorna_titolo_finestra()
        self.refresh_gui()
        if _app.DB_CONDIVISO:
            self.notifica_modifica_web()
            _log("📡 Notifica di aggiornamento inviata.")
    passo("dati e interfaccia", _dati)

    if errori:
        raise RuntimeError("; ".join(errori))
    _log("Configurazione applicata senza riavvio.")
    return esito
