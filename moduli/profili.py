#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import shutil
import subprocess
import zipfile
import tkinter as tk
from tkinter import ttk, filedialog
from datetime import datetime

MAX_LUNGHEZZA_NOME_PROFILO = 30
MAX_PROFILI = 8

def _restart_application():
    script_path = os.path.abspath(sys.argv[0])
    args = [sys.executable, script_path] + sys.argv[1:]
    if os.name == 'nt':
        subprocess.Popen(args, creationflags=0x00000008, shell=False, close_fds=True)
    else:
        subprocess.Popen(args, start_new_session=True, close_fds=True)
    os._exit(0)

def elenco_profili(self):
    import __main__ as _app
    profili = ["Principale"]
    if os.path.isdir(_app.PROFILI_DIR):
        for nome in sorted(os.listdir(_app.PROFILI_DIR), key=str.lower):
            if os.path.isdir(os.path.join(_app.PROFILI_DIR, nome)):
                profili.append(nome)
    return profili

def _copia_certificati_e_licenza(db_sorgente, db_destinazione):
    for nome_file in ("cert.pem", "key.pem", "._reg.json", "._trial.json", ".key_reg"):
        src = os.path.join(db_sorgente, nome_file)
        dst = os.path.join(db_destinazione, nome_file)
        if os.path.isfile(src) and not os.path.exists(dst):
            try:
                shutil.copy2(src, dst)
            except Exception:
                pass


_CHIAVI_WEBSERVER_DA_PROPAGARE = ("webserver_enabled", "webserver_port", "usa_ssl")

def _propaga_config_webserver(db_sorgente, db_destinazione):
    src = os.path.join(db_sorgente, "config.json")
    dst = os.path.join(db_destinazione, "config.json")
    if os.path.exists(dst) or not os.path.isfile(src):
        return
    try:
        with open(src, "r", encoding="utf-8") as f:
            config_sorgente = json.load(f)
        valori = {k: config_sorgente[k] for k in _CHIAVI_WEBSERVER_DA_PROPAGARE if k in config_sorgente}
        if valori:
            with open(dst, "w", encoding="utf-8") as f:
                json.dump(valori, f, indent=4)
    except Exception:
        pass

def _nome_profilo_valido(nome):
    nome = (nome or "").strip()
    if not nome or nome.lower() == "principale":
        return None
    if len(nome) > MAX_LUNGHEZZA_NOME_PROFILO:
        return None
    caratteri_ok = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_- ")
    if any(c not in caratteri_ok for c in nome):
        return None
    return nome

def _etichetta_profilo(self, nome_profilo):
    import __main__ as _app
    if nome_profilo == "Principale":
        return getattr(_app, "current_folder", "Principale")
    return nome_profilo

def cambia_profilo(self, nome_profilo, nuovo=False):
    import __main__ as _app
    from moduli.costanti import salva_profilo_attivo

    if nome_profilo == _app.PROFILO_ATTIVO:
        self.show_toast("Questo profilo è già attivo")
        return

    if nome_profilo != "Principale":
        cartella = os.path.join(_app.PROFILI_DIR, nome_profilo)
        db_profilo = os.path.join(cartella, "db")
        os.makedirs(db_profilo, exist_ok=True)
        if nuovo:
            _copia_certificati_e_licenza(_app.DB_DIR, db_profilo)
            _propaga_config_webserver(_app.DB_DIR, db_profilo)

    if not self.show_custom_askyesno(
        "Cambio Profilo",
        f"Passare al profilo '{_etichetta_profilo(self, nome_profilo)}'?\n\nL'app verrà riavviata per caricare i dati del nuovo profilo."
    ):
        return

    try:
        self.save_db()
    except Exception as e:
        self.show_toast(f"Impossibile salvare i dati correnti, cambio profilo annullato: {e}")
        return

    salva_profilo_attivo(_app.PATH_LOCALE, nome_profilo)
    self.show_toast(f"Passaggio al profilo '{_etichetta_profilo(self, nome_profilo)}'...")
    try:
        self._on_close_lock()
    except Exception:
        pass
    self.after(900, _restart_application)


def rinomina_profilo(self, vecchio_nome, nuovo_nome):
    import __main__ as _app

    if vecchio_nome == "Principale":
        self.show_toast("Il profilo Principale non può essere rinominato")
        return False

    if vecchio_nome == _app.PROFILO_ATTIVO:
        self.show_toast("Non puoi rinominare il profilo attivo: passa prima a un altro profilo")
        return False

    nuovo_nome = _nome_profilo_valido(nuovo_nome)
    if not nuovo_nome:
        self.show_toast("Nuovo nome profilo non valido")
        return False

    vecchio_path = os.path.join(_app.PROFILI_DIR, vecchio_nome)
    nuovo_path = os.path.join(_app.PROFILI_DIR, nuovo_nome)

    if os.path.exists(nuovo_path):
        self.show_toast("Esiste già un profilo con questo nome")
        return False

    try:
        if os.path.isdir(vecchio_path):
            os.rename(vecchio_path, nuovo_path)
            self.show_toast(f"Profilo rinominato in '{nuovo_nome}'")
            return True
    except Exception as e:
        self.show_toast(f"Errore durante la rinomina: {e}")
        return False
    return False


def cancella_profilo(self, nome_profilo):
    import __main__ as _app

    if nome_profilo == "Principale":
        self.show_toast("Il profilo Principale non può essere eliminato")
        return False

    if nome_profilo == _app.PROFILO_ATTIVO:
        self.show_toast("Non puoi eliminare il profilo attivo: passa prima a un altro profilo")
        return False

    if not self.show_custom_askyesno(
        "Elimina Profilo",
        f"Eliminare definitivamente il profilo '{nome_profilo}'?\n\n"
        "Tutti i dati associati (movimenti, database, impostazioni) verranno "
        "cancellati e NON potranno essere recuperati."
    ):
        return False

    cartella = os.path.join(_app.PROFILI_DIR, nome_profilo)
    try:
        if os.path.isdir(cartella):
            shutil.rmtree(cartella)
        self.show_toast(f"Profilo '{nome_profilo}' eliminato")
        return True
    except Exception as e:
        self.show_toast(f"Errore durante l'eliminazione del profilo: {e}")
        return False


# Export / Import profili

_FILE_ESCLUSI_EXPORT = ("cert.pem", "key.pem", "._reg.json", "._trial.json", ".key_reg", "._sync_chk")
_PATTERN_ESCLUSI_EXPORT = (".lock", "-journal", ".db-wal", ".tmp")
_CARTELLE_ESCLUSE_EXPORT = ("resources",)


def _percorso_db_profilo(nome_profilo):
    import __main__ as _app
    if nome_profilo == "Principale":
        radice_dati = os.path.dirname(_app.PROFILI_DIR)
        return os.path.join(radice_dati, "db")
    return os.path.join(_app.PROFILI_DIR, nome_profilo, "db")


def esporta_profilo(self, nome_profilo):
    db_sorgente = _percorso_db_profilo(nome_profilo)
    if not os.path.isdir(db_sorgente):
        self.show_toast("Nessun dato da esportare per questo profilo")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_pulito = "".join(c if c.isalnum() else "_" for c in nome_profilo)
    percorso_output = filedialog.asksaveasfilename(
        title=f"Esporta profilo '{_etichetta_profilo(self, nome_profilo)}'",
        initialdir=os.path.expanduser('~'),
        initialfile=f"OrbitaCasa_{nome_pulito}_{timestamp}.zip",
        defaultextension=".zip",
        filetypes=[("Archivio Profilo OrbitaCasa", "*.zip")]
    )
    if not percorso_output:
        return

    try:
        with zipfile.ZipFile(percorso_output, "w", zipfile.ZIP_DEFLATED) as zf:
            for radice, cartelle, file_list in os.walk(db_sorgente):
                cartelle[:] = [c for c in cartelle if c not in _CARTELLE_ESCLUSE_EXPORT]
                for nome_file in file_list:
                    if nome_file in _FILE_ESCLUSI_EXPORT:
                        continue
                    if any(p in nome_file for p in _PATTERN_ESCLUSI_EXPORT):
                        continue
                    percorso_assoluto = os.path.join(radice, nome_file)
                    arcname = os.path.relpath(percorso_assoluto, db_sorgente)
                    zf.write(percorso_assoluto, arcname)
        self.show_custom_warning("Esporta Profilo",
            f"Profilo '{_etichetta_profilo(self, nome_profilo)}' esportato con successo!")
    except Exception as e:
        self.show_custom_warning("Errore", f"Errore durante l'esportazione:\n{e}")


def _estrai_zip_sicuro(percorso_zip, cartella_destinazione):
    cartella_destinazione = os.path.normpath(cartella_destinazione)
    with zipfile.ZipFile(percorso_zip, "r") as zf:
        for member in zf.namelist():
            dest = os.path.normpath(os.path.join(cartella_destinazione, member))
            if dest != cartella_destinazione and not dest.startswith(cartella_destinazione + os.sep):
                raise ValueError(f"Percorso non sicuro nell'archivio: {member}")
        zf.extractall(cartella_destinazione)


def importa_profilo(self):
    import __main__ as _app

    percorso_zip = filedialog.askopenfilename(
        title="Seleziona archivio profilo da importare",
        initialdir=os.path.expanduser('~'),
        filetypes=[("Archivio Profilo OrbitaCasa", "*.zip")]
    )
    if not percorso_zip:
        return
    if not zipfile.is_zipfile(percorso_zip):
        self.show_toast("Il file selezionato non è un archivio valido")
        return

    win = tk.Toplevel(self)
    win.title("Importa Profilo")
    win.configure(bg=self.COLOR_BACKGROUND)
    win.transient(self)
    win.resizable(False, False)
    w, h = 300, 110
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    win.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")
    win.bind("<Escape>", lambda e: win.destroy())

    tk.Label(win, text="Nome del profilo da creare:", bg=self.COLOR_BACKGROUND,
             fg=self.TEXT_COLOR, font=("Arial", 9)).pack(padx=14, pady=(14, 4))
    vcmd_nome_profilo_imp = (win.register(lambda P: len(P) <= 30), '%P')
    entry = ttk.Entry(win, font=("Arial", 10), width=32,
                       validate="key", validatecommand=vcmd_nome_profilo_imp)
    entry.pack(padx=14, pady=(0, 10), fill="x")
    entry.focus_set()

    def _conferma():
        nome = _nome_profilo_valido(entry.get())
        if not nome:
            self.show_toast("Nome profilo non valido")
            return
        profili_esistenti = elenco_profili(self)
        if nome.lower() in (p.lower() for p in profili_esistenti):
            self.show_toast("Esiste già un profilo con questo nome")
            return
        if len(profili_esistenti) >= MAX_PROFILI:
            self.show_toast(f"Limite massimo di {MAX_PROFILI} profili raggiunto")
            return

        cartella = os.path.join(_app.PROFILI_DIR, nome)
        db_profilo = os.path.join(cartella, "db")
        try:
            os.makedirs(db_profilo, exist_ok=True)
            _estrai_zip_sicuro(percorso_zip, db_profilo)
            _copia_certificati_e_licenza(_app.DB_DIR, db_profilo)
            _propaga_config_webserver(_app.DB_DIR, db_profilo)
        except Exception as e:
            self.show_toast(f"Errore durante l'importazione: {e}")
            return

        win.destroy()
        if self.show_custom_askyesno("Importa Profilo",
                f"Profilo '{nome}' importato con successo.\n\nPassare subito al nuovo profilo?"):
            cambia_profilo(self, nome)

    entry.bind("<Return>", lambda e: _conferma())
    btnf = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    btnf.pack(pady=(0, 14))
    _crea_bottone_icona(self, btnf, "check", "Importa", _conferma).pack(side="left", padx=6)
    _crea_bottone_icona(self, btnf, "chiudi", "Annulla", win.destroy).pack(side="left", padx=6)


def _crea_bottone_icona(self, parent, icon_key, testo, comando):
    img = self.icone_gui.get(icon_key)
    lbl = tk.Label(parent, compound="left", image=img, text=f" {testo}",
            bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR, cursor="hand2",
            padx=14, pady=7, font=("Arial", 9, "bold"))
    lbl.bind("<Button-1>", lambda e: comando())
    return lbl

def mostra_selettore_profilo(self):
    import __main__ as _app

    win = tk.Toplevel(self)
    win.title("Profili Utente")
    win.configure(bg=self.COLOR_BACKGROUND)
    win.transient(self)
    win.resizable(False, False)
    w, h = 640, 440
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    win.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")
    win.bind("<Escape>", lambda e: win.destroy())
    
    tk.Label(win, text="Profilo attivo:", bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
             font=("Arial", 9, "bold")).pack(anchor="w", padx=14, pady=(14, 0))
    tk.Label(win, text=_etichetta_profilo(self, _app.PROFILO_ATTIVO), bg=self.COLOR_BACKGROUND,
             fg=self.MENU_ACT_BG_COLOR, font=("Arial", 11, "bold")).pack(anchor="w", padx=14, pady=(0, 10))

    lista_frame = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    lista_frame.pack(fill="both", expand=True, padx=14)
    lb = tk.Listbox(lista_frame, activestyle="dotbox", font=("Arial", 10),
                    bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT,
                    selectbackground=self.MENU_ACT_BG_COLOR, exportselection=False)
    lb.pack(fill="both", expand=True, side="left")
    scrollbar = ttk.Scrollbar(lista_frame, orient="vertical", command=lb.yview)
    scrollbar.pack(side="right", fill="y")
    lb.config(yscrollcommand=scrollbar.set)

    profili = elenco_profili(self)
    etichette = [_etichetta_profilo(self, nome) for nome in profili]
    for etichetta in etichette:
        lb.insert("end", etichetta)
    if _app.PROFILO_ATTIVO in profili:
        lb.selection_set(profili.index(_app.PROFILO_ATTIVO))

    info_frame = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    info_frame.pack(fill="x", padx=14, pady=(6, 0))
    lbl_info_utente = tk.Label(info_frame, text="", bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
                                font=("Arial", 8), anchor="w", justify="left")
    lbl_info_utente.pack(fill="x")
    lbl_info_cartella = tk.Label(info_frame, text="", bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
                                  font=("Arial", 8), anchor="w", justify="left", wraplength=600)
    lbl_info_cartella.pack(fill="x")

    def _aggiorna_info(event=None):
        sel = lb.curselection()
        if not sel:
            lbl_info_utente.config(text="")
            lbl_info_cartella.config(text="")
            return
        nome = profili[sel[0]]
        lbl_info_utente.config(text=f"Utente: {_etichetta_profilo(self, nome)}")
        lbl_info_cartella.config(text=f"Cartella: {_percorso_db_profilo(nome)}")

    lb.bind("<<ListboxSelect>>", _aggiorna_info)
    _aggiorna_info()

    def _switch():
        sel = lb.curselection()
        if not sel:
            return
        cambia_profilo(self, profili[sel[0]])

    def _nuovo():
        popup = tk.Toplevel(win)
        popup.title("Nuovo Profilo")
        popup.configure(bg=self.COLOR_BACKGROUND)
        popup.transient(win)
        popup.resizable(False, False)
        w, h = 300, 110
        x = win.winfo_rootx() + (win.winfo_width() // 2) - (w // 2)
        y = win.winfo_rooty() + (win.winfo_height() // 2) - (h // 2)
        popup.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")
        popup.bind("<Escape>", lambda e: popup.destroy())
        
        tk.Label(popup, text="Nome del nuovo profilo:", bg=self.COLOR_BACKGROUND,
                 fg=self.TEXT_COLOR, font=("Arial", 9)).pack(padx=14, pady=(14, 4))
        vcmd_nome_profilo = (popup.register(lambda P: len(P) <= 30), '%P')
        entry = ttk.Entry(popup, font=("Arial", 10), width=32,
                           validate="key", validatecommand=vcmd_nome_profilo)
        entry.pack(padx=14, pady=(0, 10), fill="x")
        entry.focus_set()

        def _conferma():
            nome = _nome_profilo_valido(entry.get())
            if not nome:
                self.show_toast("Nome profilo non valido")
                return
            if nome.lower() in (p.lower() for p in profili):
                self.show_toast("Esiste già un profilo con questo nome")
                return
            if len(profili) >= MAX_PROFILI:
                self.show_toast(f"Limite massimo di {MAX_PROFILI} profili raggiunto")
                return
            popup.destroy()
            win.destroy()
            cambia_profilo(self, nome, nuovo=True)

        entry.bind("<Return>", lambda e: _conferma())
        btnf = tk.Frame(popup, bg=self.COLOR_BACKGROUND)
        btnf.pack(pady=(0, 14))
        _crea_bottone_icona(self, btnf, "check", "Crea", _conferma).pack(side="left", padx=6)
        _crea_bottone_icona(self, btnf, "chiudi", "Annulla", popup.destroy).pack(side="left", padx=6)

    def _rinomina():
        sel = lb.curselection()
        if not sel:
            return
        vecchio_nome = profili[sel[0]]
        
        if vecchio_nome == "Principale":
            self.show_toast("Il profilo Principale non può essere rinominato")
            return

        popup = tk.Toplevel(win)
        popup.title("Rinomina Profilo")
        popup.configure(bg=self.COLOR_BACKGROUND)
        popup.transient(win)
        popup.resizable(False, False)
        w, h = 300, 110
        x = win.winfo_rootx() + (win.winfo_width() // 2) - (w // 2)
        y = win.winfo_rooty() + (win.winfo_height() // 2) - (h // 2)
        popup.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")
        popup.bind("<Escape>", lambda e: popup.destroy())

        tk.Label(popup, text=f"Nuovo nome per '{vecchio_nome}':", bg=self.COLOR_BACKGROUND,
                 fg=self.TEXT_COLOR, font=("Arial", 9)).pack(padx=14, pady=(14, 4))
        entry = ttk.Entry(popup, font=("Arial", 10))
        entry.insert(0, vecchio_nome)
        entry.pack(padx=14, pady=(0, 10), fill="x")
        entry.focus_set()
        entry.selection_range(0, "end")

        def _conferma_rinomina():
            nuovo_nome = entry.get()
            if rinomina_profilo(self, vecchio_nome, nuovo_nome):
                popup.destroy()
                win.destroy()
                mostra_selettore_profilo(self)

        entry.bind("<Return>", lambda e: _conferma_rinomina())
        btnf = tk.Frame(popup, bg=self.COLOR_BACKGROUND)
        btnf.pack(pady=(0, 14))
        _crea_bottone_icona(self, btnf, "check", "Rinomina", _conferma_rinomina).pack(side="left", padx=6)
        _crea_bottone_icona(self, btnf, "chiudi", "Annulla", popup.destroy).pack(side="left", padx=6)

    def _elimina():
        sel = lb.curselection()
        if not sel:
            return
        idx = sel[0]
        nome = profili[idx]
        if cancella_profilo(self, nome):
            profili.remove(nome)
            lb.delete(idx)
            if profili:
                lb.selection_set(min(idx, len(profili) - 1))
            _aggiorna_info()

    def _esporta():
        sel = lb.curselection()
        if not sel:
            return
        esporta_profilo(self, profili[sel[0]])

    def _importa():
        win.destroy()
        importa_profilo(self)

    btn_frame = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    btn_frame.pack(fill="x", padx=14, pady=(14, 6))
    btn_frame.columnconfigure((0, 1, 2, 3, 4), weight=1)

    _crea_bottone_icona(self, btn_frame, "sync",      "Attiva",    _switch).grid(row=0, column=0, padx=(0, 3), sticky="ew")
    _crea_bottone_icona(self, btn_frame, "salva",     "Nuovo",     _nuovo).grid(row=0, column=1, padx=3, sticky="ew")
    _crea_bottone_icona(self, btn_frame, "modifica",  "Rinomina",  _rinomina).grid(row=0, column=2, padx=3, sticky="ew")
    _crea_bottone_icona(self, btn_frame, "delete",    "Elimina",   _elimina).grid(row=0, column=3, padx=(3, 0), sticky="ew")
    _crea_bottone_icona(self, btn_frame, "chiudi",    "Chiudi",    win.destroy).grid(row=0, column=4, padx=(3, 0), sticky="ew")

    btn_frame2 = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    btn_frame2.pack(fill="x", padx=14, pady=(0, 14))
    btn_frame2.columnconfigure((0, 1), weight=1)

    _crea_bottone_icona(self, btn_frame2, "documenti", "Esporta", _esporta).grid(row=0, column=0, padx=(0, 3), sticky="ew")
    _crea_bottone_icona(self, btn_frame2, "carica",    "Importa", _importa).grid(row=0, column=1, padx=(3, 0), sticky="ew")
