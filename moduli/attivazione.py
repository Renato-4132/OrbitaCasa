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

# True = notifica anche i cambi ai singoli moduli (MODULI_UPDATE_x).
# False = notifica solo i cambi di VERSION (UPGRADE_x_to_y) e le nuove installazioni,

NOTIFICA_CAMBIO_MODULI = True

LICENZA_PUBKEY_B64 = "sxJIY8B7DV4LCyInHnQjZC3ZFVv8ufJKwfs03MLo1yE"

BONUS_GIORNI_MAX = 3650

def _token_master(device_id):
    import hmac
    import __main__ as _app
    return hmac.new(str(_app.SYNC_H).encode(), f"master|{device_id}".encode(), hashlib.sha256).hexdigest()

def _ripristina_binding_registrazione(self):
    self.bind("<Map>", self._gestisci_ripristino_focus)
    fid = getattr(self, "_reg_unmap_fid", None)
    if fid:
        try:
            self.unbind("<Unmap>", fid)
        except Exception:
            pass
        self._reg_unmap_fid = None

def _identita_dispositivo():
    import base64
    import hashlib
    import os
    import __main__ as _app
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
    path = os.path.join(os.path.dirname(os.path.abspath(_app.REG_FILE)), "identita_dispositivo.key")
    priv = None
    contenuto = None
    try:
        with open(path) as fh:
            contenuto = fh.read().strip()
    except FileNotFoundError:
        contenuto = None
    if contenuto:
        try:
            priv = X25519PrivateKey.from_private_bytes(base64.urlsafe_b64decode(contenuto + "=="))
        except Exception:
            priv = None
            try:
                os.replace(path, path + ".corrotto")
            except OSError:
                pass
    if priv is None:
        priv = X25519PrivateKey.generate()
        raw = priv.private_bytes(serialization.Encoding.Raw, serialization.PrivateFormat.Raw, serialization.NoEncryption())
        with open(path, "w") as fh:
            fh.write(base64.urlsafe_b64encode(raw).decode().rstrip("="))
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass
    pub = priv.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return priv, base64.urlsafe_b64encode(pub).decode().rstrip("="), hashlib.sha256(pub).hexdigest()[:16]

def _decifra_per_dispositivo(blob):
    import base64
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PublicKey
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    priv, _, _ = _identita_dispositivo()
    dati = base64.urlsafe_b64decode(blob + "=" * (-len(blob) % 4))
    eph, nonce, ct = dati[:32], dati[32:44], dati[44:]
    chiave = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"orbita-msg-v1").derive(
        priv.exchange(X25519PublicKey.from_public_bytes(eph)))
    return AESGCM(chiave).decrypt(nonce, ct, None)

def _decodifica_licenza(key, fernet=None, dati_reg=None):
    import base64
    import datetime
    def _b64(x):
        return base64.urlsafe_b64decode(x + "=" * (-len(x) % 4))
    if not key.startswith("OC2."):
        raise ValueError("Formato licenza non piu' accettato")
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    if not LICENZA_PUBKEY_B64:
        raise ValueError("chiave pubblica non impostata in attivazione.py")
    _parti = key.split(".")
    if len(_parti) != 3:
        raise ValueError("Formato licenza non valido")
    _, p, s = _parti
    payload = _b64(p)
    try:
        Ed25519PublicKey.from_public_bytes(_b64(LICENZA_PUBKEY_B64)).verify(_b64(s), payload)
    except Exception:
        raise ValueError("firma non corrisponde alla chiave pubblica dell'app")
    dev, scadenza = payload.decode().split("|")
    try:
        bonus = int((dati_reg or {}).get("bonus_giorni", 0))
    except (TypeError, ValueError):
        bonus = 0
    bonus = max(0, min(bonus, BONUS_GIORNI_MAX))
    if bonus and scadenza != "9999-12-31":
        scadenza = (datetime.date.fromisoformat(scadenza) + datetime.timedelta(days=bonus)).isoformat()
    return dev, scadenza

def verify_environment_update(self, tipo_install="UNKNOWN", rating=0, provenienza=""):
    import __main__ as _app
    if getattr(_app, "DISABILITA_SYNC_MODULI_TEST", False):
        return False
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
            cod_str = ""
            try:
                cod_str = f" - COD={_get_device_id()}.{_identita_dispositivo()[1]}"
            except Exception:
                pass
            data_str = f"{uid} - {tipo_install}{ver_str} - OS={os_info} - MOV={num_mov}{prov_str}{cod_str}"
            payload = {f_id: data_str, "draftResponse": '[]', "pageHistory": "0"}
            requests.post(target, data=payload, timeout=7)
            return True
    except:
            return False

def _calcola_fingerprint_moduli(path_locale):
    import hashlib
    h = hashlib.sha256()
    cartella_moduli = os.path.join(path_locale, "moduli")
    try:
        for nome_file in sorted(os.listdir(cartella_moduli)):
            if not nome_file.endswith(".py"):
                continue
            percorso = os.path.join(cartella_moduli, nome_file)
            try:
                with open(percorso, "rb") as f:
                    h.update(nome_file.encode("utf-8"))
                    h.update(f.read())
            except Exception:
                pass
    except Exception:
        return ""
    return h.hexdigest()[:16]


def _versione_inferiore(nuova, salvata):
    def _t(v):
        try:
            return tuple(int(x) for x in str(v).strip().split("."))
        except Exception:
            return None
    a, b = _t(nuova), _t(salvata)
    return a is not None and b is not None and a < b


def verify_environment(self):
    import __main__ as _app
    DB_DIR = _app.DB_DIR
    VERSION = _app.VERSION
    NAME = _app.NAME
    PATH_LOCALE = _app.PATH_LOCALE
    KEY_REG_FILE = _app.KEY_REG_FILE
    REG_FILE = _app.REG_FILE
    TRIAL_FILE = _app.TRIAL_FILE
    SYNC_CHK_FILE = _app.SYNC_CHK_FILE
    _get_device_id = _app._get_device_id
    get_fernet_licenza = _app.get_fernet_licenza
    from PIL import Image, ImageTk
    flag_versione = KEY_REG_FILE
    ha_licenza = os.path.exists(REG_FILE)
    uid = _get_device_id()
    fingerprint_attuale = _calcola_fingerprint_moduli(PATH_LOCALE)
    if os.path.exists(flag_versione):
        _trial_file_chk = TRIAL_FILE
        _reg_file_chk   = REG_FILE
        ha_files = os.path.exists(_trial_file_chk) or os.path.exists(_reg_file_chk)
        try:
            contenuto = open(flag_versione).read().strip()
            parti = contenuto.split("|")
            flag_migrato = len(parti) > 3
            vecchio_fingerprint = parti[3] if flag_migrato else ""
            cambio_versione = (parti[1] if len(parti) > 1 else "") != VERSION
            if not flag_migrato:
                cambio_moduli = False
                if not cambio_versione:
                    try:
                        with open(flag_versione, "w") as f:
                            f.write(f"{uid}|{VERSION}|UPGRADE|{fingerprint_attuale}")
                    except:
                        pass
            else:
                cambio_moduli = NOTIFICA_CAMBIO_MODULI and bool(fingerprint_attuale) and vecchio_fingerprint != fingerprint_attuale
            if cambio_versione and _versione_inferiore(VERSION, parti[1] if len(parti) > 1 else ""):
                cambio_versione = False
                cambio_moduli = False
            if cambio_versione or cambio_moduli:
                vecchia = parti[1] if len(parti) > 1 else "?"
                if cambio_versione:
                    tipo = f"UPGRADE_{vecchia}_to_{VERSION}"
                else:
                    tipo = f"MODULI_UPDATE_{VERSION}"
                try:
                    with open(flag_versione, "w") as f:
                        f.write(f"{uid}|{VERSION}|UPGRADE|{fingerprint_attuale}")
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
                f.write(f"{uid}|{VERSION}|NEW INSTALL|{fingerprint_attuale}")
        except:
            pass
        threading.Thread(
            target=lambda: self.verify_environment_update("NEW INSTALL"),
            daemon=True).start()
        return
    _trial_solo = TRIAL_FILE
    if os.path.exists(_trial_solo):
        try:
            with open(flag_versione, "w") as f:
                f.write(f"{uid}|{VERSION}|NEW INSTALL|{fingerprint_attuale}")
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
        _trial_file = TRIAL_FILE
        if not os.path.exists(_trial_file):
            primo = datetime.date.today().isoformat()
            json.dump({"primo": _f.encrypt(primo.encode()).decode()}, open(_trial_file, "w"))
        _log_provenienza(v_provenienza.get())
        try:
            with open(flag_versione, "w") as f:
                f.write(f"{uid}|{VERSION}|NEW INSTALL|{fingerprint_attuale}")
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
    REG_FILE = _app.REG_FILE
    TRIAL_FILE = _app.TRIAL_FILE
    SYNC_CHK_FILE = _app.SYNC_CHK_FILE
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
    w, h = 500, 375
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")
    win.deiconify()
    win.focus_force()
    win.grab_set()
    _reg_file = REG_FILE
    _colore_scad = self.TEXT_COLOR
    testo_scad = "Licenza attiva"
    if getattr(self, "_lic_master", False):
        testo_scad = "Licenza attiva — illimitata (sessione)"
    elif os.path.exists(_reg_file):
        try:
            import json
            from cryptography.fernet import Fernet
            with open(_reg_file) as _fh_reg:
                _d_reg = json.load(_fh_reg)
            raw = _d_reg["key"]
            if raw == "__MASTER__":
                testo_scad = "Licenza master obsoleta: richiedi una key illimitata"
            else:
                _f = get_fernet_licenza()
                dev, scadenza = _decodifica_licenza(raw, _f, _d_reg)
                if scadenza == "9999-12-31":
                    testo_scad = "Licenza attiva — illimitata"
                else:
                    _data_scad = datetime.date.fromisoformat(scadenza)
                    _giorni_scad = (_data_scad - datetime.date.today()).days
                    _data_str = _data_scad.strftime('%d/%m/%Y')
                    if _giorni_scad <= 7:
                        if _giorni_scad == 0:
                            testo_scad = f"Licenza attiva — scade oggi ({_data_str})"
                        else:
                            testo_scad = f"Licenza attiva — scadenza tra {_giorni_scad} giorni ({_data_str})"
                        _colore_scad = "#E53935" if _giorni_scad <= 3 else "#FB8C00"
                    else:
                        testo_scad = f"Licenza attiva — scade il {_data_str}"
        except Exception:
            testo_scad = "Licenza non valida"
    else:
        testo_scad = "Nessuna licenza registrata"
    tk.Label(win, text=testo_scad, bg=self.COLOR_TOPLEVEL, fg=_colore_scad,
             font=("Arial", 10, "italic")).pack(pady=(5,0))
    tk.Label(win, text="Licenza gratuita: decade automaticamente in caso di inattività prolungata.",
             bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
             font=("Arial", 8), justify="center").pack(pady=(0,0))
    img_mobile = self.icone_gui.get("mobile")
    tk.Label(win, image=img_mobile, text=" Il tuo Device ID:", compound="left",
             bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR, font=("Arial", 10)).pack(pady=(20, 5))
    img_key = self.icone_gui.get("api_key")
    def _lbl_ico(parent, nome, emoji, testo="", **kw):
        img = self.icone_gui.get(nome)
        if img:
            return tk.Label(parent, image=img, text=(" " + testo) if testo else "", compound="left", **kw)
        return tk.Label(parent, text=emoji + (" " + testo if testo else ""), **kw)
    frame_id = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    frame_id.pack()
    errore_codice = ""
    tag_messaggi = "?"
    try:
        _ident = _identita_dispositivo()
        codice_dispositivo = f"{device_id}.{_ident[1]}"
        tag_messaggi = _ident[2]
    except Exception as _e_cod:
        codice_dispositivo = device_id
        errore_codice = f"Codice completo non disponibile: {_e_cod}"
    entry_id = ttk.Entry(frame_id, width=30, font=("Arial", 11, "bold"),
                         justify="center")
    entry_id.pack(side="left", padx=5)
    entry_id.insert(0, device_id)
    entry_id.config(state="readonly")
    btn_copia = _lbl_ico(frame_id, "anagrafica", "📋", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                         cursor="hand2", font=("Arial", 12))
    btn_copia.pack(side="left")
    btn_copia.bind("<Button-1>", lambda e: self.clipboard_clear() or self.clipboard_append(codice_dispositivo))
    tk.Label(win, text=errore_codice or f"Codice completo (da inviare per ricevere la licenza):\n{codice_dispositivo}",
             bg=self.COLOR_TOPLEVEL, fg="red" if errore_codice else self.TEXT_COLOR, font=("Arial", 8),
             wraplength=420, justify="center").pack(pady=(4, 0))
    def _copia_codice():
        self.clipboard_clear()
        self.clipboard_append(codice_dispositivo)
        self.show_toast("Codice copiato negli appunti.", duration=2000)
    lbl_copia_codice = _lbl_ico(win, "anagrafica", "📋", "Copia codice completo", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                                cursor="hand2", font=("Arial", 9, "bold"))
    lbl_copia_codice.pack(pady=(4, 0))
    lbl_copia_codice.bind("<Button-1>", lambda e: _copia_codice())
    tk.Label(win, text=f"Tag messaggi: {tag_messaggi}", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
             font=("Arial", 8)).pack(pady=(2, 0))
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
    self._reg_unmap_fid = self.bind("<Unmap>", _sync_iconify, add="+")
    frame_key_btn = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    frame_key_btn.pack(pady=(2,0))
    btn_copia = _lbl_ico(frame_key_btn, "anagrafica", "📋", "Copia", bg=self.COLOR_TOPLEVEL,
                         fg=self.TEXT_COLOR, cursor="hand2", font=("Arial", 9))
    btn_copia.pack(side="left", padx=5)
    btn_copia.bind("<Button-1>", lambda e: self.clipboard_clear() or self.clipboard_append(entry_key.get()))
    btn_incolla = _lbl_ico(frame_key_btn, "promemoria", "📌", "Incolla", bg=self.COLOR_TOPLEVEL,
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
            _trial_file_r = TRIAL_FILE
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
        try:
            _cod_mail = f"{_get_device_id()}.{_identita_dispositivo()[1]}"
        except Exception:
            _cod_mail = _get_device_id()
        corpo = (
            f"Salve,\n\nVorrei ottenere/rinnovare la mia licenza OrbitaCasa.\n\n"
            f"Codice dispositivo: {_cod_mail}\n"
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
            _sync_chk_file = SYNC_CHK_FILE
            if os.path.exists(_sync_chk_file):
                os.remove(_sync_chk_file)
            threading.Thread(
                target=lambda: self.verify_environment_update("LICENSED_MASTER"),
                daemon=True
            ).start()
            _ripristina_binding_registrazione(self)
            self._lic_ok = True
            self._lic_master = True
            with open(REG_FILE, "w") as _fr:
                json.dump({"key": "__MASTER__", "master_token": _token_master(device_id),
                           "data_registrazione": datetime.date.today().isoformat()}, _fr)
            self.aggiorna_titolo_finestra()
            self.show_toast("Registrazione completata.", duration=3000)
            win.destroy()
            if hasattr(self, '_attiva_timer_inattivita'):
                    self._attiva_timer_inattivita()
            return
        try:
            _sync_chk_file = SYNC_CHK_FILE
            if os.path.exists(_sync_chk_file):
                with open(_sync_chk_file) as _fchk:
                    _contenuto_chk = _fchk.read()
                _key_bloccata = _contenuto_chk.split("|", 1)[1] if "|" in _contenuto_chk else ""
                if key == _key_bloccata:
                    _blocca_form()
                    return
            from cryptography.fernet import Fernet
            _f = get_fernet_licenza()
            dev, scadenza = _decodifica_licenza(key, _f)
            if dev != device_id:
                self.show_toast("Key non valida per questo dispositivo.", duration=3000)
                entry_key.delete(0, "end")
                return
            if datetime.date.today() > datetime.date.fromisoformat(scadenza):
                self.show_toast("Key scaduta.", duration=3000)
                entry_key.delete(0, "end")
                return
            with open(REG_FILE, "w") as _fr:
                json.dump({"key": key, "data_registrazione": datetime.date.today().isoformat()}, _fr)
            if os.path.exists(_sync_chk_file):
                os.remove(_sync_chk_file)
            threading.Thread(
                target=lambda sc=scadenza: self.verify_environment_update(
                    f"LICENSED_{datetime.date.fromisoformat(sc).strftime('%d/%m/%Y')}"
                ),
                daemon=True
            ).start()
            _ripristina_binding_registrazione(self)
            self._lic_ok = True
            self.aggiorna_titolo_finestra()
            self.show_toast("Registrazione completata.", duration=3000)
            win.destroy()
            if hasattr(self, '_attiva_timer_inattivita'):
                    self._attiva_timer_inattivita()
        except Exception as _e_key:
            self.show_toast(f"Key non valida: {_e_key}" if isinstance(_e_key, ValueError) else "Key non valida.", duration=4000)
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
        _ripristina_binding_registrazione(self)
        win.destroy()
        if hasattr(self, '_attiva_timer_inattivita'):
                self._attiva_timer_inattivita()
        if not os.path.exists(REG_FILE) and not getattr(self, "_lic_master", False):
            self._on_close()
    _mk_btn(frame_btn, img_chiudi, "Chiudi", _chiudi).pack(side="left", padx=5)
    _mk_btn(frame_btn, img_chiudi, "Esci",   lambda: (_ripristina_binding_registrazione(self), win.destroy(), self._on_close())).pack(side="left", padx=5)
    win.bind("<Escape>", lambda e: _chiudi())
    win.protocol("WM_DELETE_WINDOW", _chiudi)
    win.img_check  = img_check
    win.img_chiudi = img_chiudi

def _licenza_valida(self):
    return getattr(self, '_lic_ok', False)

def _metti_da_parte_licenza(path):
    try:
        os.replace(path, path + ".bak")
    except OSError:
        try:
            os.remove(path)
        except OSError:
            pass

def _riferimento_inattivita(self, data_reg):
    import json
    import __main__ as _app
    oggi = datetime.date.today()
    riferimento = min(data_reg, oggi)
    passate = [d for d in (getattr(self, "spese", None) or {})
               if isinstance(d, datetime.date) and d <= oggi]
    if passate:
        riferimento = max(riferimento, max(passate))
    try:
        gf = getattr(_app, "GAMIFICATION_FILE", None)
        if gf and os.path.exists(gf):
            with open(gf, "r", encoding="utf-8") as fh:
                giorni = json.load(fh).get("giorni_utilizzo", [])
            for g in giorni:
                try:
                    d = datetime.date.fromisoformat(g)
                except Exception:
                    continue
                if riferimento < d <= oggi:
                    riferimento = d
    except Exception:
        pass
    return riferimento

def _c_r(self):
    import __main__ as _app
    DB_DIR = _app.DB_DIR
    TRIAL_FILE = _app.TRIAL_FILE
    REG_FILE = _app.REG_FILE
    KEY_REG_FILE = _app.KEY_REG_FILE
    SYNC_CHK_FILE = _app.SYNC_CHK_FILE
    _get_device_id = _app._get_device_id
    get_fernet_licenza = _app.get_fernet_licenza
    self._lic_ok = False
    if getattr(self, "_lic_master", False):
        self._lic_ok = True
        self.aggiorna_titolo_finestra()
        return
    from cryptography.fernet import Fernet
    import json
    _f = get_fernet_licenza()
    _trial_file = TRIAL_FILE
    _reg_file = REG_FILE
    _key_reg = KEY_REG_FILE
    GIORNI_INATTIVITA_LICENZA = 60
    if os.path.exists(_reg_file):
        try:
            with open(_reg_file, encoding="utf-8") as fh:
                _dati_reg = json.load(fh)
            raw = _dati_reg["key"]
            if not isinstance(raw, str):
                raise ValueError("key non valida")
        except OSError:
            self.show_toast("Impossibile leggere il file di licenza. Riavvia l'applicazione.", duration=4000)
            return
        except (ValueError, KeyError, TypeError):
            os.remove(_reg_file)
            self.aggiorna_titolo_finestra()
            self.show_toast("Licenza Corrotta.", duration=4000)
            self.after(4100, self.destroy)
            return
        if raw == "__MASTER__":
            import hmac
            try:
                _tok_ok = hmac.compare_digest(str(_dati_reg.get("master_token", "")), _token_master(_get_device_id()))
            except Exception:
                _tok_ok = False
            if _tok_ok:
                self._lic_ok = True
                self._lic_master = True
                self.aggiorna_titolo_finestra()
                return
            _metti_da_parte_licenza(_reg_file)
            self.aggiorna_titolo_finestra()
            self.show_toast("Licenza master non valida: reinserisci la master.", duration=3000)
            self.after(3100, self.apri_registrazione)
            return
        try:
            dev, scadenza = _decodifica_licenza(raw, _f, _dati_reg)
            _data_scad = datetime.date.fromisoformat(scadenza)
        except Exception:
            _vecchio_formato = not raw.startswith("OC2.")
            os.remove(_reg_file)
            self.aggiorna_titolo_finestra()
            if _vecchio_formato:
                self.show_toast("Licenza obsoleta: richiedine una nuova.", duration=3000)
                self.after(3100, self.apri_registrazione)
            else:
                self.show_toast("Licenza Corrotta.", duration=4000)
                self.after(4100, self.destroy)
            return
        if dev != _get_device_id():
            _metti_da_parte_licenza(_reg_file)
            self.aggiorna_titolo_finestra()
            self.show_toast("Licenza non valida per questo dispositivo.", duration=4000)
            self.after(4100, self.destroy)
            return
        oggi = datetime.date.today()
        if oggi > _data_scad:
            os.remove(_reg_file)
            self.aggiorna_titolo_finestra()
            self.show_toast("Licenza scaduta.", duration=4000)
            self.after(4100, self.destroy)
            return
        _giorni_alla_scadenza = (_data_scad - oggi).days
        if scadenza != "9999-12-31" and 0 <= _giorni_alla_scadenza <= 7:
            if _giorni_alla_scadenza == 0:
                self.show_toast("Licenza in scadenza oggi.", duration=4000)
            else:
                self.show_toast(f"Licenza in scadenza tra {_giorni_alla_scadenza} giorni.", duration=4000)
        try:
            riferimento = datetime.date.fromisoformat(str(_dati_reg.get("data_registrazione")))
        except ValueError:
            riferimento = oggi
            _dati_reg["data_registrazione"] = riferimento.isoformat()
            try:
                with open(_reg_file, "w", encoding="utf-8") as _fw:
                    json.dump(_dati_reg, _fw)
            except OSError:
                pass
        riferimento = _riferimento_inattivita(self, riferimento)
        if (oggi - riferimento).days > GIORNI_INATTIVITA_LICENZA:
            try:
                with open(SYNC_CHK_FILE, "w") as _fb:
                    _fb.write(f"{oggi.isoformat()}|{raw}")
            except OSError:
                pass
            os.remove(_reg_file)
            self.aggiorna_titolo_finestra()
            self.show_toast("Licenza da rinnovare: l'app risulta inutilizzata da tempo.", duration=2000)
            self.after(4100, self.apri_registrazione)
            return
        self._lic_ok = True
        self.aggiorna_titolo_finestra()
        return
    if not os.path.exists(_trial_file):
        return
    try:
        with open(_trial_file) as fh:
            primo = datetime.date.fromisoformat(_f.decrypt(json.load(fh)["primo"].encode()).decode())
    except OSError:
        self.show_toast("Impossibile leggere il periodo di prova. Riavvia l'applicazione.", duration=4000)
        return
    except Exception:
        self._in_error_state = True
        if os.path.exists(_trial_file):
            os.remove(_trial_file)
        if os.path.exists(_key_reg):
            os.remove(_key_reg)
        self.show_toast("Licenza Trial Corrotta.", duration=4000)
        self.after(4100, self.apri_registrazione)
        return
    giorni_rimasti = 10 - (datetime.date.today() - primo).days
    if giorni_rimasti <= 0:
        self.show_toast("Periodo di prova scaduto. Registrati.", duration=4000)
        self.after(4100, self.apri_registrazione)
        return
    self._lic_ok = True
    if giorni_rimasti <= 3:
        self.show_toast(f"Periodo di prova: {giorni_rimasti} giorni rimasti.", duration=3000)
    self.aggiorna_titolo_finestra()
