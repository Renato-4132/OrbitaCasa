#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import hashlib
import datetime
import threading
import tkinter as tk
import requests

def _calcola_id_messaggio(msg):
    chiave = f"{msg.get('target', '')}|{msg.get('livello', '')}|{msg.get('testo', '')}|{msg.get('scadenza', '')}"
    if msg.get("enc"):
        chiave = f"{msg.get('to', '')}|{msg['enc']}"
    return hashlib.sha1(chiave.encode("utf-8")).hexdigest()[:16]

def _leggi_messaggi_visti(path_file):
    try:
        if os.path.exists(path_file):
            with open(path_file, "r", encoding="utf-8") as f:
                return set(json.load(f))
    except Exception:
        pass
    return set()

_LOCK_VISTI = threading.RLock()

def _scrivi_messaggi_visti(path_file, visti):
    try:
        with _LOCK_VISTI:
            os.makedirs(os.path.dirname(path_file), exist_ok=True)
            with open(path_file, "w", encoding="utf-8") as f:
                json.dump(sorted(visti), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore scrittura messaggi visti: {e}")

def _aggiungi_messaggi_visti(path_file, ids):
    with _LOCK_VISTI:
        v = _leggi_messaggi_visti(path_file)
        v.update(ids)
        _scrivi_messaggi_visti(path_file, v)

def _scadenza_valida(msg):
    scad = msg.get("scadenza")
    if not scad:
        return True
    scad = str(scad).strip()
    for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.date.today() <= datetime.datetime.strptime(scad, fmt).date()
        except ValueError:
            continue
    return True

def _norm_id(valore):
    v = str(valore or "").strip().lower()
    return v[3:] if v.startswith("id_") else v

def _messaggio_per_me(msg, device_id):
    target = msg.get("target", "all")
    if str(target).strip().lower() == "all":
        return True
    return bool(device_id) and _norm_id(target) == _norm_id(device_id)

def _registra_licenza_da_messaggio(self, msg):
    import __main__ as _app
    try:
        key = str(msg.get("licenza", "")).strip()
        if not key.startswith("OC2."):
            return "formato key non valido"
        try:
            if os.path.exists(_app.SYNC_CHK_FILE):
                with open(_app.SYNC_CHK_FILE) as fh:
                    _cont = fh.read()
                if "|" in _cont and key == _cont.split("|", 1)[1]:
                    return "licenza bloccata per inattivita', ne serve una nuova"
        except Exception:
            pass
        from moduli.attivazione import _decodifica_licenza
        try:
            dev, scadenza = _decodifica_licenza(key, _app.get_fernet_licenza())
        except Exception as e:
            return str(e) if isinstance(e, ValueError) else "firma non valida"
        if dev != _app._get_device_id():
            return "key per un altro dispositivo"
        if datetime.date.today() > datetime.date.fromisoformat(scadenza):
            return "licenza scaduta"
        if os.path.exists(_app.REG_FILE):
            try:
                with open(_app.REG_FILE) as fh:
                    _attuale = json.load(fh)
                if _attuale.get("key") == key:
                    return "gia"
                if _attuale.get("key") == "__MASTER__":
                    import hmac
                    from moduli.attivazione import _token_master
                    if hmac.compare_digest(str(_attuale.get("master_token", "")), _token_master(_app._get_device_id())):
                        return "gia"
            except Exception:
                pass
        with open(_app.REG_FILE, "w") as fh:
            json.dump({"key": key, "data_registrazione": datetime.date.today().isoformat()}, fh)
        if os.path.exists(_app.SYNC_CHK_FILE):
            os.remove(_app.SYNC_CHK_FILE)
        threading.Thread(
            target=lambda sc=scadenza: self.verify_environment_update(
                f"LICENSED_{datetime.date.fromisoformat(sc).strftime('%d/%m/%Y')}"
            ),
            daemon=True
        ).start()
        self._lic_ok = True
        self.aggiorna_titolo_finestra()
        win_reg = getattr(self, "_win_reg", None)
        if win_reg is not None and win_reg.winfo_exists():
            from moduli.attivazione import _ripristina_binding_registrazione
            _ripristina_binding_registrazione(self)
            win_reg.destroy()
        if hasattr(self, "_attiva_timer_inattivita"):
            self._attiva_timer_inattivita()
        self.show_toast("Registrazione completata.", duration=3000)
        return "ok"
    except Exception as e:
        return f"errore: {e}"

def _lampeggia_badge_messaggi_servizio(self):
    badge = getattr(self, "badge_messaggi_servizio", None)
    if badge is None or not badge.winfo_exists() or not getattr(self, "_messaggi_servizio_pendenti", []):
        self._badge_blink_job = None
        return
    acceso = not getattr(self, "_badge_blink_acceso", False)
    self._badge_blink_acceso = acceso
    badge.delete("all")
    colore = "#E65100" if acceso else self.MENU_BG_DARK
    badge.create_oval(0, 0, 10, 10, fill=colore, outline="")
    self._badge_blink_job = self.after(500, lambda: _lampeggia_badge_messaggi_servizio(self))

def _aggiorna_badge_messaggi_servizio(self):
    badge = getattr(self, "badge_messaggi_servizio", None)
    if badge is None or not badge.winfo_exists():
        return
    if getattr(self, "_messaggi_servizio_pendenti", []):
        badge.place(relx=1.0, x=-8, y=4, anchor="ne")
        tk.Misc.lift(badge)
        if not getattr(self, "_badge_blink_job", None):
            _lampeggia_badge_messaggi_servizio(self)
    else:
        job = getattr(self, "_badge_blink_job", None)
        if job:
            try:
                self.after_cancel(job)
            except Exception:
                pass
            self._badge_blink_job = None
        badge.delete("all")
        badge.place_forget()

# Intervallo tra un controllo e il successivo (ms); GitHub raw ha comunque una cache di ~5 minuti
INTERVALLO_CONTROLLO_MS = 60 * 60 * 1000

def _check_messaggi_servizio_in_background(self):
    import __main__ as _app
    MESSAGGI_SERVIZIO_URL = _app.MESSAGGI_SERVIZIO_URL
    MESSAGGI_VISTI_FILE = _app.MESSAGGI_VISTI_FILE
    _get_device_id = _app._get_device_id
    installazione_vuota = not any(getattr(self, "spese", {}).values())
    try:
        self.after(INTERVALLO_CONTROLLO_MS, lambda: _check_messaggi_servizio_in_background(self))
    except Exception:
        pass
    def _check():
        try:
            resp = requests.get(MESSAGGI_SERVIZIO_URL, timeout=8)
            resp.raise_for_status()
            elenco = resp.json()
        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Messaggi di servizio non raggiungibili: {e}")
            return
        try:
            device_id = _get_device_id()
        except Exception:
            device_id = None

        prima_esecuzione = installazione_vuota and not os.path.exists(MESSAGGI_VISTI_FILE)
        visti = _leggi_messaggi_visti(MESSAGGI_VISTI_FILE)
        nuovi = []
        da_registrare = []
        try:
            from moduli.attivazione import _identita_dispositivo, _decifra_per_dispositivo
            tag_mio = _identita_dispositivo()[2]
        except Exception:
            tag_mio = None
        for msg in elenco:
            if msg.get("enc") or msg.get("licenza"):
                if not msg.get("enc") or not tag_mio or msg.get("to") != tag_mio:
                    continue
                id_msg = _calcola_id_messaggio(msg)
                gia_visto = id_msg in visti
                if gia_visto and os.path.exists(_app.REG_FILE):
                    continue
                try:
                    interno = json.loads(_decifra_per_dispositivo(msg["enc"]).decode("utf-8"))
                except Exception:
                    if not gia_visto:
                        visti.add(id_msg)
                        _aggiungi_messaggi_visti(MESSAGGI_VISTI_FILE, [id_msg])
                        self.after(0, lambda: self.show_toast(
                            "Messaggio riservato ricevuto ma non decifrabile (blob alterato o chiave diversa).", duration=6000))
                    continue
                interno["_id"] = id_msg
                if interno.get("licenza"):
                    interno["_silenzioso"] = gia_visto
                    da_registrare.append(interno)
                elif not gia_visto and _scadenza_valida(interno):
                    nuovi.append(interno)
                continue
            if not _messaggio_per_me(msg, device_id) or not _scadenza_valida(msg):
                continue
            id_msg = _calcola_id_messaggio(msg)
            if prima_esecuzione and str(msg.get("target", "all")).strip().lower() == "all":
                visti.add(id_msg)
                continue
            if id_msg not in visti:
                msg = dict(msg)
                msg["_id"] = id_msg
                nuovi.append(msg)
        if prima_esecuzione:
            _aggiungi_messaggi_visti(MESSAGGI_VISTI_FILE, visti)
        if da_registrare:
            def _registra():
                ids_ok = None
                for m in reversed(da_registrare):
                    esito = _registra_licenza_da_messaggio(self, m)
                    if esito in ("ok", "gia"):
                        ids_ok = [x["_id"] for x in da_registrare]
                        break
                    elif not m.get("_silenzioso"):
                        self.show_toast(f"Licenza ricevuta ma non registrata: {esito}", duration=6000)
                if ids_ok:
                    _aggiungi_messaggi_visti(MESSAGGI_VISTI_FILE, ids_ok)
            self.after(0, _registra)
        if nuovi:
            def _applica():
                notificati = getattr(self, "_messaggi_servizio_notificati", set())
                da_notificare = [m for m in nuovi if m["_id"] not in notificati]
                self._messaggi_servizio_pendenti = nuovi
                self._messaggi_servizio_notificati = notificati | {m["_id"] for m in nuovi}
                _aggiorna_badge_messaggi_servizio(self)
                if da_notificare:
                    self.show_toast("📬 Nuovo messaggio di servizio\n\nClicca sul pallino arancione lampeggiante in alto a sinistra per leggerlo", duration=6000)
            self.after(0, _applica)
    threading.Thread(target=_check, daemon=True).start()

def mostra_messaggi_servizio(self):
    import __main__ as _app
    from tkinter import ttk
    MESSAGGI_VISTI_FILE = _app.MESSAGGI_VISTI_FILE
    if hasattr(self, '_messaggi_servizio_popup') and self._messaggi_servizio_popup and self._messaggi_servizio_popup.winfo_exists():
        self._messaggi_servizio_popup.lift()
        self._messaggi_servizio_popup.focus_force()
        return
    pendenti = getattr(self, "_messaggi_servizio_pendenti", [])
    if not pendenti:
        self.show_toast("Nessun nuovo messaggio di servizio.", duration=2500)
        return
    toast_id = getattr(self, "_toast_after_id", None)
    if toast_id:
        try:
            self.after_cancel(toast_id)
        except Exception:
            pass
        self._toast_after_id = None
    toast_win = getattr(self, "_toast_win", None)
    if toast_win:
        try:
            toast_win.destroy()
        except Exception:
            pass
        self._toast_win = None
    popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    self._messaggi_servizio_popup = popup
    popup.bind("<Destroy>", lambda e: setattr(self, '_messaggi_servizio_popup', None) if e.widget is popup else None)
    popup.transient(self)
    popup.withdraw()
    popup.title(" Messaggi di Servizio")
    popup.resizable(False, False)
    width = 520
    def _chiudi(event=None):
        _aggiungi_messaggi_visti(MESSAGGI_VISTI_FILE, [msg["_id"] for msg in pendenti])
        mostrati = {msg["_id"] for msg in pendenti}
        self._messaggi_servizio_pendenti = [
            m for m in getattr(self, "_messaggi_servizio_pendenti", []) if m["_id"] not in mostrati
        ]
        _aggiorna_badge_messaggi_servizio(self)
        popup.destroy()
    popup.protocol("WM_DELETE_WINDOW", _chiudi)
    popup.bind("<Escape>", _chiudi)
    tk.Label(popup, text="Messaggi di Servizio", font=("Arial", 11, "bold"),
             bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR).pack(pady=(12, 5), padx=15, anchor="w")
    corpo = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    corpo.pack(fill="both", expand=True, padx=10)
    for msg in pendenti:
        colore = self.COLOR_RED if msg.get("livello") == "warning" else self.TEXT_COLOR
        riga = tk.Frame(corpo, bg=self.COLOR_WIDGET_BG)
        riga.pack(fill="x", padx=5, pady=4)
        tk.Label(
            riga, text=msg.get("testo", ""), bg=self.COLOR_WIDGET_BG, fg=colore,
            font=("Arial", 10), wraplength=width - 70, justify="left", anchor="w"
        ).pack(fill="x", padx=10, pady=8)
    btn_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    btn_frame.pack(pady=(8, 12))
    img_chiudi = self.icone_gui.get("chiudi")
    btn_chiudi = ttk.Label(
        btn_frame, compound="left", image=img_chiudi, text=" Chiudi" if img_chiudi else "Chiudi",
        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5)
    )
    btn_chiudi.pack()
    btn_chiudi.bind("<Button-1>", _chiudi)
    def centra():
        if not popup.winfo_exists():
            return
        popup.update_idletasks()
        altezza = min(max(popup.winfo_reqheight(), 200), int(popup.winfo_screenheight() * 0.8))
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (width // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (altezza // 2)
        popup.geometry(f"{width}x{altezza}+{x}+{y}")
        popup.minsize(width, altezza)
        popup.deiconify()
        popup.lift()
        popup.focus_force()
    popup.after(0, centra)
