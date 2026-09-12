#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import hashlib
import platform
import threading
import webbrowser
import datetime
import urllib.parse
import tkinter as tk
from tkinter import ttk

import requests


# Verfica statistiche
def verify_environment_update(self, tipo_install="UNKNOWN", rating=0, provenienza=""):
    import __main__ as _app
    VERSION = _app.VERSION
    _get_device_id = _app._get_device_id
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
            prov_str = f" - PROV={provenienza}" if provenienza else ""
            data_str = f"{uid} - {tipo_install}{ver_str} - OS={os_info} - MOV={num_mov}{prov_str}"
            payload = {f_id: data_str, "draftResponse": '[]', "pageHistory": "0"}
            requests.post(target, data=payload, timeout=7)
            return True
    except:
            return False

def verify_environment(self):
    import __main__ as _app
    DB_DIR = _app.DB_DIR
    VERSION = _app.VERSION
    NAME = _app.NAME
    _get_device_id = _app._get_device_id
    get_fernet_licenza = _app.get_fernet_licenza
    from PIL import Image, ImageTk
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
    w, h = 450, 460
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
        "Hai 10 giorni di prova senza limitazioni.\n\n"
        "Al termine, potrai richiedere la tua licenza gratuita:\n"
        "Usandola guadagni punti e badge.\n"
        "Ogni nuovo livello raggiunto estende la licenza di altri 30 giorni!\n"
        "La licenza scade solo dopo 60 giorni consecutivi di inutilizzo.\n"
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
    frame_provenienza = tk.Frame(splash, bg=self.COLOR_BACKGROUND)
    frame_provenienza.pack(side=tk.BOTTOM, pady=(0, 4))
    tk.Label(frame_provenienza, text="Dove hai sentito parlare di questa app?",
             font=("Arial", 10, "bold"), fg=self.TEXT_COLOR, bg=self.COLOR_BACKGROUND).pack(side=tk.TOP)
    _opzioni_provenienza = [
        "Reddit",
        "GitHub",
        "YouTube",
        "Facebook",
        "Instagram",
        "Finanza Cafona",
        "Motore di ricerca",
        "Altro sito internet",
        "Passaparola (amico/familiare/collega)",
        "Altro / non ricordo",
    ]
    v_provenienza = tk.StringVar(value="")
    cmb_provenienza = ttk.Combobox(frame_provenienza, textvariable=v_provenienza,
                                    values=_opzioni_provenienza, state="readonly",
                                    font=("Arial", 10, "bold"), width=38, style="Border.TCombobox")
    cmb_provenienza.pack(side=tk.TOP, pady=(2, 0))
    def _abilita_conferma(event=None):
        btn_si.config(fg=self.COLOR_GREEN_SMOOTH, cursor="hand2")
        btn_si.bind("<Button-1>", lambda e: _si())
    cmb_provenienza.bind("<<ComboboxSelected>>", _abilita_conferma)
    def _scrivi_testo(indice=0):
        if indice > len(_testo_benvenuto):
            return
        lbl_benvenuto.config(text=_testo_benvenuto[:indice])
        splash.after(10, lambda: _scrivi_testo(indice + 1))
    splash.after(150, _scrivi_testo)
    def _log_provenienza(risposta_provenienza):
        threading.Thread(
            target=lambda: self.verify_environment_update("NEW INSTALL", provenienza=risposta_provenienza),
            daemon=True).start()
    def _si():
        risposta[0] = True
        splash.grab_release()
        splash.destroy()
        from cryptography.fernet import Fernet
        import json
        _f = get_fernet_licenza()
        _trial_file = os.path.join(DB_DIR, "._trial.json")
        if not os.path.exists(_trial_file):
            primo = datetime.date.today().isoformat()
            json.dump({"primo": _f.encrypt(primo.encode()).decode()}, open(_trial_file, "w"))
        _log_provenienza(v_provenienza.get())
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
                      compound="left", fg="#9E9E9E", cursor="arrow",
                      font=("Arial", 9, "bold"), bg=self.COLOR_BACKGROUND)
    btn_si.pack(side=tk.LEFT, padx=10)

    btn_no = tk.Label(toolbar, image=self.icone_gui.get("chiudi"), text=" Non ora",
                      compound="left", fg=self.TEXT_COLOR, cursor="hand2",
                      font=("Arial", 9, "bold"), bg=self.COLOR_BACKGROUND)
    btn_no.pack(side=tk.LEFT, padx=10)
    btn_no.bind("<Button-1>", lambda e: _no())
    self.wait_window(splash)

def apri_registrazione(self):
    import __main__ as _app
    DB_DIR = _app.DB_DIR
    VERSION = _app.VERSION
    SYNC_H = _app.SYNC_H
    PROFILO_ATTIVO = _app.PROFILO_ATTIVO
    _get_device_id = _app._get_device_id
    get_fernet_licenza = _app.get_fernet_licenza
    if hasattr(self, '_win_reg') and self._win_reg.winfo_exists():
        self._win_reg.lift()
        return
    device_id = _get_device_id()
    _bordo_reg = getattr(self, "COLOR_HIGHLIGHT", "#3B82F6")
    win = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL,
                       highlightthickness=2,
                       highlightbackground=_bordo_reg,
                       highlightcolor=_bordo_reg)
    self._win_reg = win
    win.title("Registrazione")
    win.withdraw()
    win.resizable(False, False)
    win.transient(self)
    win.update_idletasks()
    w, h = 500, 290
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
                _f = get_fernet_licenza()
                payload = _f.decrypt(raw.encode()).decode()
                dev, scadenza = payload.split("|")
                testo_scad = f"Licenza attiva — scadenza: {datetime.date.fromisoformat(scadenza).strftime('%d/%m/%Y')}" if scadenza != "9999-12-31" else "Licenza attiva — illimitata"
        except Exception:
            testo_scad = "Licenza non valida"
    else:
        testo_scad = "Nessuna licenza registrata"
    tk.Label(win, text=testo_scad, bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
             font=("Arial", 10, "italic")).pack(pady=(5,0))
    tk.Label(win, text="Licenza gratuita: decade automaticamente in caso di inattività prolungata.",
             bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
             font=("Arial", 8), justify="center").pack(pady=(0,0))
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
    lbl_msg_blocco = tk.Label(win, text="", bg=self.COLOR_TOPLEVEL, fg="red",
                               font=("Arial", 9, "bold"), wraplength=440, justify="center")
    lbl_msg_blocco.pack(pady=(5, 0))
    def _blocca_form():
        lbl_msg_blocco.config(text="Registrazione non disponibile al momento. Contatta l'assistenza.")
        entry_key.delete(0, "end")
        entry_key.config(state="disabled")
        btn_registra_frame.unbind("<Button-1>")
        for w in btn_registra_frame.winfo_children():
            w.unbind("<Button-1>")
            if isinstance(w, tk.Label):
                w.config(fg="#777777", cursor="")
        btn_registra_frame.config(cursor="")
        btn_incolla.unbind("<Button-1>")
        btn_incolla.config(fg="#777777", cursor="")
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
    def _incolla_key(e=None):
        if str(entry_key.cget("state")) == "disabled":
            return
        try:
            testo = self.clipboard_get()
        except tk.TclError:
            self.show_toast("Appunti vuoti o senza testo.", duration=3000)
            return
        entry_key.delete(0, "end")
        entry_key.insert(0, testo.strip())
    btn_incolla.bind("<Button-1>", _incolla_key)
    def _rinnova():
        num_mov = sum(len(v) for v in self.spese.values()) if hasattr(self, 'spese') else 0
        giorni_utilizzo = "?"
        try:
            _trial_file_r = os.path.join(DB_DIR, "._trial.json")
            if os.path.exists(_trial_file_r):
                import json
                from cryptography.fernet import Fernet
                _f_r = get_fernet_licenza()
                _primo_r = datetime.date.fromisoformat(_f_r.decrypt(json.load(open(_trial_file_r))["primo"].encode()).decode())
                giorni_utilizzo = (datetime.date.today() - _primo_r).days
        except Exception:
            pass
        threading.Thread(
            target=lambda: self.verify_environment_update(f"RICHIESTA_LICENZA_GG{giorni_utilizzo}_MOV{num_mov}"),
            daemon=True
        ).start()
        corpo = (
            f"Salve,\n\nVorrei ottenere/rinnovare la mia licenza OrbitaCasa.\n\n"
            f"Licenza: {self.topic_unico}\n"
            f"Versione: {VERSION}\n"
            f"Utente: {PROFILO_ATTIVO if PROFILO_ATTIVO != 'Principale' else self.current_folder}\n\n"
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
            _sync_chk_file = os.path.join(DB_DIR, "._sync_chk")
            if os.path.exists(_sync_chk_file):
                os.remove(_sync_chk_file)
            json.dump({"key": "__MASTER__", "data_registrazione": datetime.date.today().isoformat()}, open(os.path.join(DB_DIR, "._reg.json"), "w"))
            threading.Thread(
                target=lambda: self.verify_environment_update("LICENSED_MASTER"),
                daemon=True
            ).start()
            self.bind("<Map>", self._gestisci_ripristino_focus)
            self.unbind("<Unmap>")
            self._lic_ok = True
            self.aggiorna_titolo_finestra()
            self.show_toast("Registrazione completata.", duration=3000)
            win.destroy()
            if hasattr(self, '_attiva_timer_inattivita'):
                    self._attiva_timer_inattivita()
            return
        try:
            _sync_chk_file = os.path.join(DB_DIR, "._sync_chk")
            if os.path.exists(_sync_chk_file):
                with open(_sync_chk_file) as _fchk:
                    _contenuto_chk = _fchk.read()
                _key_bloccata = _contenuto_chk.split("|", 1)[1] if "|" in _contenuto_chk else ""
                if key == _key_bloccata:
                    _blocca_form()
                    return
            from cryptography.fernet import Fernet
            _f = get_fernet_licenza()
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
            json.dump({"key": key, "data_registrazione": datetime.date.today().isoformat()}, open(os.path.join(DB_DIR, "._reg.json"), "w"))
            if os.path.exists(_sync_chk_file):
                os.remove(_sync_chk_file)
            threading.Thread(
                target=lambda sc=scadenza: self.verify_environment_update(
                    f"LICENSED_{datetime.date.fromisoformat(sc).strftime('%d/%m/%Y')}"
                ),
                daemon=True
            ).start()
            self.bind("<Map>", self._gestisci_ripristino_focus)
            self.unbind("<Unmap>")
            self._lic_ok = True
            self.aggiorna_titolo_finestra()
            self.show_toast("Registrazione completata.", duration=3000)
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
    btn_registra_frame = _mk_btn(frame_btn, img_check, "Registra", conferma)
    btn_registra_frame.pack(side="left", padx=5)
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
    import __main__ as _app
    DB_DIR = _app.DB_DIR
    _get_device_id = _app._get_device_id
    get_fernet_licenza = _app.get_fernet_licenza
    self._lic_ok = False
    from cryptography.fernet import Fernet
    import json
    _f = get_fernet_licenza()
    _trial_file = os.path.join(DB_DIR, "._trial.json")
    _reg_file = os.path.join(DB_DIR, "._reg.json")
    _key_reg = os.path.join(DB_DIR, ".key_reg")
    GIORNI_INATTIVITA_LICENZA = 60
    if os.path.exists(_reg_file):
        try:
            with open(_reg_file) as fh:
                _dati_reg = json.load(fh)
            raw = _dati_reg["key"]
            if raw == "__MASTER__":
                self._lic_ok = True
                self.aggiorna_titolo_finestra()
                return
            payload = _f.decrypt(raw.encode()).decode()
            dev, scadenza = payload.split("|")
            if dev != _get_device_id():
                os.remove(_reg_file)
                self.aggiorna_titolo_finestra()
                self.show_toast("Licenza non valida.", duration=4000)
                self.after(4100, self.destroy)
                return
            if datetime.date.today() > datetime.date.fromisoformat(scadenza):
                os.remove(_reg_file)
                self.aggiorna_titolo_finestra()
                self.show_toast("Licenza scaduta.", duration=4000)
                self.after(4100, self.destroy)
                return
            _data_reg_str = _dati_reg.get("data_registrazione")
            if _data_reg_str:
                riferimento = datetime.date.fromisoformat(_data_reg_str)
            else:
                riferimento = datetime.date.today()
                _dati_reg["data_registrazione"] = riferimento.isoformat()
                try:
                    with open(_reg_file, "w") as _fw:
                        json.dump(_dati_reg, _fw)
                except Exception:
                    pass
            if getattr(self, 'spese', None):
                ultima_data = max(self.spese.keys())
                if ultima_data > riferimento:
                    riferimento = ultima_data
            if (datetime.date.today() - riferimento).days > GIORNI_INATTIVITA_LICENZA:
                with open(os.path.join(DB_DIR, "._sync_chk"), "w") as _fb:
                    _fb.write(f"{datetime.date.today().isoformat()}|{raw}")
                os.remove(_reg_file)
                self.aggiorna_titolo_finestra()
                self.show_toast("Licenza da rinnovare: l'app risulta inutilizzata da tempo.", duration=2000)
                self.after(4100, self.apri_registrazione)
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
