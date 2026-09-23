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
    return hashlib.sha1(chiave.encode("utf-8")).hexdigest()[:16]

def _leggi_messaggi_visti(path_file):
    try:
        if os.path.exists(path_file):
            with open(path_file, "r", encoding="utf-8") as f:
                return set(json.load(f))
    except Exception:
        pass
    return set()

def _scrivi_messaggi_visti(path_file, visti):
    try:
        os.makedirs(os.path.dirname(path_file), exist_ok=True)
        with open(path_file, "w", encoding="utf-8") as f:
            json.dump(sorted(visti), f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore scrittura messaggi visti: {e}")

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

def _aggiorna_badge_messaggi_servizio(self):
    badge = getattr(self, "badge_messaggi_servizio", None)
    if badge is None or not badge.winfo_exists():
        return
    badge.delete("all")
    if getattr(self, "_messaggi_servizio_pendenti", []):
        badge.create_oval(0, 0, 10, 10, fill="#E65100", outline="")
        badge.place(x=30, y=4)
        tk.Misc.lift(badge)
    else:
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
        for msg in elenco:
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
            _scrivi_messaggi_visti(MESSAGGI_VISTI_FILE, visti)
        if nuovi:
            def _applica():
                notificati = getattr(self, "_messaggi_servizio_notificati", set())
                da_notificare = [m for m in nuovi if m["_id"] not in notificati]
                self._messaggi_servizio_pendenti = nuovi
                self._messaggi_servizio_notificati = notificati | {m["_id"] for m in nuovi}
                _aggiorna_badge_messaggi_servizio(self)
                if da_notificare:
                    self.show_toast("📬 Nuovo messaggio di servizio: clicca il pallino arancione sull'icona", duration=5000)
            self.after(0, _applica)
    threading.Thread(target=_check, daemon=True).start()

# Popup che elenca i messaggi di servizio pendenti; alla chiusura li marca come visti
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
    popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    self._messaggi_servizio_popup = popup
    popup.bind("<Destroy>", lambda e: setattr(self, '_messaggi_servizio_popup', None) if e.widget is popup else None)
    popup.transient(self)
    popup.withdraw()
    popup.title(" Messaggi di Servizio")
    popup.resizable(False, False)
    width = 520
    def _chiudi(event=None):
        visti = _leggi_messaggi_visti(MESSAGGI_VISTI_FILE)
        for msg in pendenti:
            visti.add(msg["_id"])
        _scrivi_messaggi_visti(MESSAGGI_VISTI_FILE, visti)
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
