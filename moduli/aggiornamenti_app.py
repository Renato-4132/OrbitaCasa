#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import shutil
import platform
import subprocess
import threading
import urllib.request
import webbrowser
import datetime
import tkinter as tk
from tkinter import ttk

import requests

# Controllo Manuale Forzato dell'Aggiornamento Software (conferma utente + riavvio)
def forza_aggiorna(self):
    import __main__ as _app
    GITHUB_FILE_URL = _app.GITHUB_FILE_URL
    NOME_FILE = _app.NOME_FILE
    if not getattr(self, '_lic_ok', False):
        self.show_toast("Nessuna licenza attiva.", duration=3000)
        return
    messaggio_conferma = (
        "Forzare l'aggiornamento del software?\n\n"
        "L'applicazione verrà chiusa e riavviata\n"
    )
    risposta = self.show_custom_askyesno(
        title="Aggiornamento",
        message=messaggio_conferma
    )
    if risposta:
        self.aggiorna(GITHUB_FILE_URL, NOME_FILE)
    else:
        self.show_custom_warning("Annullato", "❌ Aggiornamento forzato annullato dall'utente.")

# Esecuzione dell'Aggiornamento del Software con Backup e Riavvio Automatico
def aggiorna(self, url, nome_file):
    import __main__ as _app
    APRI_BROWSER = _app.APRI_BROWSER
    URL_QST = _app.URL_QST
    import subprocess, sys, os
    import time
    self.update()
    nome_backup = f"{nome_file}.bak"
    try:
        if os.path.exists(nome_file):
            try:
                shutil.copy2(nome_file, nome_backup)
            except Exception as backup_err:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ERRORE backup: {backup_err}")
                self.show_custom_warning("Attenzione", "Impossibile creare il backup. Aggiornamento annullato.")
                return
        try:
            urllib.request.urlretrieve(url, nome_file)
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Download completato! {nome_file} è stato aggiornato.")
        except Exception as download_err:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ERRORE download: {download_err}")
            if os.path.exists(nome_backup):
                shutil.copy2(nome_backup, nome_file)
                os.remove(nome_backup)
            self.show_custom_warning("Attenzione", "❌ Aggiornamento NON completato! \n\n Problema di rete/download. 😕")
            return
        if APRI_BROWSER:
            webbrowser.open(URL_QST) 
            _app.APRI_BROWSER = False
        self.save_db()
        self._on_close_lock() 
        messaggio = "Riavvio in corso. File aggiornato! ATTENDERE..."
        duration_s = 2
        width = 350
        height = 80
        parent = self
        parent.update_idletasks()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        x_pos = (parent_width // 2) - (width // 2)
        y_pos = (parent_height // 2) - (height // 2)
        popup_frame = tk.Frame(parent, bg="orange", bd=3, relief="raised")
        popup_frame.place(x=x_pos, y=y_pos, width=width, height=height)
        popup_frame.lift()
        label = tk.Label(popup_frame, text=messaggio, font=("Arial", 10, "bold"), 
                          justify="center", padx=10, pady=10, bg="orange", fg="black")
        label.pack(expand=True, fill='both')
        parent.update() 
        time.sleep(duration_s)
        try:
           popup_frame.destroy()
        except:
           pass
        script_path = os.path.abspath(sys.argv[0])
        args = [sys.executable, script_path] + sys.argv[1:]
        if os.name == 'nt':
            subprocess.Popen(args, creationflags=0x00000008, shell=False, close_fds=True)
        else:
            subprocess.Popen(args, start_new_session=True, close_fds=True)
        os._exit(0)           
    except Exception as e:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ERRORE FATALE nell'aggiornamento: {str(e)}")
        self.show_custom_warning("Errore Grave", "Si è verificato un errore inatteso durante l'aggiornamento.")
        return

# Verifica in background se ci sono librerie pip aggiornabili (mostra bottone se sì)
def _check_librerie_in_background(self):
    import importlib.metadata as metadata
    import urllib.request, json as _json, threading
    LIBRERIE = [
        "tkcalendar", "flask", "requests", "google-genai",
        "Pillow", "PyMuPDF", "pystray", "segno",
        "cryptography", "yfinance", "tkinterdnd2",
    ]
    def _check():
        aggiornabili = 0
        falliti = 0
        for pkg in LIBRERIE:
            try:
                ver_inst = metadata.version(pkg)
            except metadata.PackageNotFoundError:
                continue
            try:
                with urllib.request.urlopen(
                    f"https://pypi.org/pypi/{pkg}/json", timeout=5
                ) as resp:
                    ver_pypi = _json.loads(resp.read().decode())["info"]["version"]
                if ver_pypi != ver_inst:
                    aggiornabili += 1
            except Exception:
                falliti += 1
                continue
        def _aggiorna_ui():
            if not self.winfo_exists():
                return
            if aggiornabili > 0:
                self.btn_aggiorna_lib.pack(side=tk.LEFT, padx=(4, 0))
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] "
                      f"{aggiornabili} librer{'ia' if aggiornabili == 1 else 'ie'} aggiornabil{'e' if aggiornabili == 1 else 'i'}")
            elif falliti == len(LIBRERIE):
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] "
                      f"Check librerie fallito (offline?)")
            else:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] "
                      f"Librerie tutte aggiornate.")
            self.after(21600000, self._check_librerie_in_background)
        self.after(0, _aggiorna_ui)
    threading.Thread(target=_check, daemon=True).start()

# Controllo automatico degli Aggiornamenti Software
def check_aggiornamento_con_api(self):
    if getattr(self, '_splash_reg', None) and self._splash_reg.winfo_exists():
         return
    if not self._licenza_valida():
        return
    threading.Thread(target=self.check_aggiornamento_thread, daemon=True).start()
    self._job_aggiornamento = self.after(43200000, self.check_aggiornamento_con_api)

def check_aggiornamento_thread(self):
    import __main__ as _app
    RIMANDA_FILE = _app.RIMANDA_FILE
    REPO_OWNER = _app.REPO_OWNER
    REPO_NAME = _app.REPO_NAME
    NOME_FILE = _app.NOME_FILE
    BRANCH_PRINCIPALE = _app.BRANCH_PRINCIPALE
    _boot_git_blob_sha1 = _app._boot_git_blob_sha1
    ConnectionError = _app.ConnectionError
    RequestException = _app.RequestException
    import os
    from datetime import datetime, timezone, timedelta
    try:
        if os.path.exists(RIMANDA_FILE):
            with open(RIMANDA_FILE, "r") as f:
                data = json.load(f)
                rimanda = datetime.strptime(data.get("rimanda_fino", ""), "%Y-%m-%d")
                if datetime.today() < rimanda:
                    data_visiva = rimanda.strftime("%d-%m-%Y")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Aggiornamento Rimandato fino al {data_visiva}")
                    return
        api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/commits"
        params = {"path": NOME_FILE, "per_page": 1}
        response = requests.get(api_url, params=params, timeout=5)
        response.raise_for_status()
        commits = response.json()
        if not commits:
            self.after(0, lambda: self.show_custom_warning("Controllo Aggiornamento",
                                     "Nessun commit trovato. Impossibile verificare lo stato."))
            return
        commit_date = commits[0]["commit"]["committer"]["date"]
        remote_time = datetime.strptime(commit_date, "%Y-%m-%dT%H:%M:%SZ").replace(microsecond=0)
        try:
            contents_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{NOME_FILE}"
            contents_resp = requests.get(contents_url, params={"ref": BRANCH_PRINCIPALE}, timeout=5)
            contents_resp.raise_for_status()
            sha_remoto = contents_resp.json().get("sha", "")
            sha_locale = _boot_git_blob_sha1(NOME_FILE) if os.path.exists(NOME_FILE) else None
            if sha_locale == sha_remoto:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Software allineato all'ultimo commit (hash identico).")
                return
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Impossibile verificare lo SHA remoto, fallback su data: {e}")
        changelog_text = ""
        for commit in commits:
            date_str = commit["commit"]["committer"]["date"]
            commit_dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
            message = commit["commit"]["message"].strip().replace('\r', '')
            lines = message.split('\n')
            subject = lines[0]
            body_lines = lines[1:]
            start_index = 0
            while start_index < len(body_lines):
                current_line = body_lines[start_index].strip()
                if not current_line or current_line == subject.strip():
                    start_index += 1
                else:
                    break
            body_lines = body_lines[start_index:]
            changelog_entry = f"▸ [{commit_dt.strftime('%d/%m/%y %H:%M')}] {subject}\n"
            if body_lines:
                for line in body_lines:
                    if line.strip():
                        changelog_entry += f"   → {line}\n"
                    else:
                        changelog_entry += "\n"
            changelog_entry += "\n"
            changelog_text += changelog_entry
        if not os.path.exists(NOME_FILE):
            def _avvisa_mancante():
                if self.state() == 'iconic':
                    self.deiconify()
                    self.lift()
                    self.focus_force()
                self.show_custom_warning(
                    "File mancante",
                    f"⚠️ File '{NOME_FILE}' non trovato (rinominato o rimosso).\n\n"
                    "Vai in 'Opzioni' -> 'Forza Aggiornamento Software' per ripristinarlo."
                )
            self.after(0, _avvisa_mancante)
            return
        local_time = datetime.fromtimestamp(
            os.path.getmtime(NOME_FILE), timezone.utc
        ).replace(microsecond=0)
        if remote_time.date() > local_time.date():
            self.after(0, lambda rt=remote_time, lt=local_time, ct=changelog_text:
                       self._mostra_popup_aggiornamento(rt, lt, ct))
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Software allineato all'ultimo commit.")
    except ConnectionError:
        self.after(0, lambda: self.show_toast("Connessione assente o GitHub non raggiungibile."))
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Connessione assente o GitHub non raggiungibile.")
    except RequestException as e:
        self.after(0, lambda err=e: self.show_toast(f"Limite GitHub superato o Errore API: {err}"))
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Errore HTTP o API: {e}")
    except Exception as e:
        self.after(0, lambda err=e: self.show_toast(f"Errore generico: {err}"))
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Errore generico durante il controllo aggiornamento: {e}")

def _mostra_popup_aggiornamento(self, remote_time, local_time, changelog_text):
    import __main__ as _app
    REPO_OWNER = _app.REPO_OWNER
    REPO_NAME = _app.REPO_NAME
    NOME_FILE = _app.NOME_FILE
    RIMANDA_FILE = _app.RIMANDA_FILE
    VERSION = _app.VERSION
    import time, subprocess, sys, os
    from datetime import datetime, timedelta
    if self.state() == 'iconic':
        self.deiconify()
        self.lift()
        self.focus_force()
    def make_separator(parent):
        tk.Frame(parent, bg=self.COLOR_BACKGROUND, height=1).pack(fill="x")
    def make_label_row(parent, label_text, value_text):
        row = tk.Frame(parent, bg=self.COLOR_WIDGET_BG)
        row.pack(fill="x", pady=3)
        tk.Label(row, text=label_text, bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                 font=("Segoe UI", 8), width=18, anchor="w").pack(side="left")
        tk.Label(row, text=value_text, bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
                 font=("Segoe UI", 9), anchor="w").pack(side="left")
    win = tk.Toplevel(self, bg=self.COLOR_BACKGROUND)
    win.withdraw()
    win.title("Aggiornamento Disponibile")
    win.configure(bd=0)
    win.bind('<Escape>', lambda e: win.destroy())
    header = tk.Frame(win, bg=self.COLOR_HEADER_BG, height=42)
    header.pack(fill="x")
    header.pack_propagate(False)
    dot_canvas = tk.Canvas(header, width=10, height=10,
                           bg=self.COLOR_HEADER_BG, highlightthickness=0)
    dot_canvas.create_oval(0, 0, 10, 10, fill=self.COLOR_HIGHLIGHT, outline="")
    dot_canvas.pack(side="left", padx=(16, 8), pady=16)
    tk.Label(header, text="AGGIORNAMENTO DISPONIBILE",
             bg=self.COLOR_HEADER_BG, fg=self.COLOR_HEADER,
             font=("Segoe UI", 8, "bold")).pack(side="left")
    make_separator(win)
    frame_timer = tk.Frame(win, bg=self.COLOR_WIDGET_BG)
    frame_timer.pack(fill="x")
    timer_inner = tk.Frame(frame_timer, bg=self.COLOR_WIDGET_BG)
    timer_inner.pack(fill="x", padx=16, pady=8)
    timer_dot = tk.Canvas(timer_inner, width=8, height=8,
                          bg=self.COLOR_WIDGET_BG, highlightthickness=0)
    timer_dot.create_oval(0, 0, 8, 8, fill=self.COLOR_RED_SMOOTH, outline="")
    timer_dot.pack(side="left", padx=(0, 8))
    label_timer = tk.Label(timer_inner,
                           text="⏱  Chiusura automatica tra 60 secondi",
                           bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                           font=("Segoe UI", 9))
    label_timer.pack(side="left")
    make_separator(win)
    info_outer = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    info_outer.pack(fill="x", padx=16, pady=(14, 0))
    tk.Frame(info_outer, bg=self.COLOR_HIGHLIGHT, width=3).pack(side="left", fill="y")
    info_card = tk.Frame(info_outer, bg=self.COLOR_WIDGET_BG)
    info_card.pack(side="left", fill="both", expand=True)
    inner_pad = tk.Frame(info_card, bg=self.COLOR_WIDGET_BG)
    inner_pad.pack(fill="x", padx=12, pady=10)
    make_label_row(inner_pad, "VERSIONE ONLINE", f"📡  {remote_time.strftime('%d/%m/%Y   %H:%M')}")
    make_label_row(inner_pad, "VERSIONE LOCALE",  f"🖥️  {local_time.strftime('%d/%m/%Y   %H:%M')}")
    cl_header = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    cl_header.pack(fill="x", padx=16, pady=(14, 4))
    tk.Label(cl_header, text="CHANGELOG",
             bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
             font=("Segoe UI", 8, "bold")).pack(side="left")
    frame_changelog = tk.Frame(win, bg=self.COLOR_WIDGET_BG,
                               highlightbackground=self.COLOR_HEADER_BG,
                               highlightthickness=1)
    frame_changelog.pack(padx=16, pady=(0, 6), fill='both', expand=True)
    scrollbar = ttk.Scrollbar(frame_changelog, style="Vertical.TScrollbar")
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_area = tk.Text(
        frame_changelog,
        wrap=tk.WORD,
        yscrollcommand=scrollbar.set,
        height=7, width=60,
        font=("Consolas", 9),
        bg=self.COLOR_WIDGET_BG,
        fg=self.TEXT_COLOR,
        insertbackground=self.COLOR_HIGHLIGHT,
        selectbackground=self.COLOR_HIGHLIGHT,
        selectforeground=self.COLOR_WHITE,
        relief="flat", bd=0,
        padx=10, pady=8
    )
    text_area.insert(tk.END, changelog_text.strip())
    text_area.config(state=tk.DISABLED)
    text_area.pack(side=tk.LEFT, fill='both', expand=True)
    scrollbar.config(command=text_area.yview)
    make_separator(win)
    tk.Label(win,
             text="Vuoi procedere con l'aggiornamento adesso?",
             bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
             font=("Segoe UI", 9)).pack(pady=(10, 0))
    frame_bottoni = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    frame_bottoni.pack(pady=14)
    def aggiorna_timer(secondi_rimasti):
        try:
            win.attributes('-topmost', True)
        except Exception:
            pass
        if secondi_rimasti > 0:
            label_timer.config(
                text=f"⏱  Chiusura automatica tra {secondi_rimasti} secondi",
                fg=self.COLOR_RED_SMOOTH if secondi_rimasti <= 10 else self.TEXT_COLOR
            )
            win.after(1000, aggiorna_timer, secondi_rimasti - 1)
        else:
            label_timer.config(text="⏱  Chiusura in corso...", fg=self.COLOR_RED_SMOOTH)
            win.destroy()
    timeout_id = win.after(60000, win.destroy)
    aggiorna_timer(60)
    def annulla_timeout():
        win.after_cancel(timeout_id)
    def aggiorna():
        annulla_timeout()
        url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/{NOME_FILE.replace(' ', '%20')}"
        try:
            nome_backup = f"{NOME_FILE}.bak"
            if os.path.exists(NOME_FILE):
                shutil.copy2(NOME_FILE, nome_backup)
            urllib.request.urlretrieve(url, NOME_FILE)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Download completato! {NOME_FILE} è stato aggiornato.")
            threading.Thread(
                target=lambda: self.verify_environment_update(f"UPDATED_to_{VERSION}"),
                daemon=True
            ).start()
            if os.path.exists(RIMANDA_FILE):
                try:
                    os.remove(RIMANDA_FILE)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] File rimando eliminato dopo aggiornamento.")
                except Exception as err:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Errore durante l'eliminazione del file rimando: {err}")
            self.show_toast("Riavvio in corso. File aggiornato! ATTENDERE...", duration=2000)
            win.destroy()
            try:
                win.attributes('-topmost', True)
            except Exception:
                pass
            self.update()
            time.sleep(2)
            script_path = os.path.abspath(sys.argv[0])
            args = [sys.executable, script_path] + sys.argv[1:]
            if os.name == 'nt':
                subprocess.Popen(args, creationflags=0x00000008, shell=False, close_fds=True)
            else:
                subprocess.Popen(args, start_new_session=True, close_fds=True)
            os._exit(0)
        except Exception as e:
            if 'shutil' in sys.modules and os.path.exists(nome_backup):
                shutil.copy2(nome_backup, NOME_FILE)
                os.remove(nome_backup)
            self.show_custom_warning(
                "Attenzione",
                f"Aggiornamento fallito durante il download/riavvio:\n{e}"
            )
    def chiudi():
        annulla_timeout()
        win.destroy()
    def rimanda():
        annulla_timeout()
        win.destroy()
        nuova_data = datetime.today() + timedelta(days=15)
        with open(RIMANDA_FILE, "w") as f:
            json.dump({"rimanda_fino": nuova_data.strftime("%Y-%m-%d")}, f)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Aggiornamento Rimandato fino al {nuova_data.date()}")
        data_formattata = nuova_data.date().strftime("%d/%m/%Y")
        self.show_toast(f"Aggiornamento Rimandato fino al {data_formattata}", duration=2500)
    img_aggiorna = self.icone_gui.get("reset_campo")
    btn_aggiorna = ttk.Label(
        frame_bottoni, compound="left", image=img_aggiorna,
        text=" AGGIORNA" if img_aggiorna else "AGGIORNA",
        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
        cursor="hand2", padding=(10, 5)
    )
    btn_aggiorna.image = img_aggiorna
    btn_aggiorna.pack(side="left", padx=5)
    btn_aggiorna.bind("<Button-1>", lambda e: aggiorna())
    img_chiudi_btn = self.icone_gui.get("chiudi")
    btn_chiudi_btn = ttk.Label(
        frame_bottoni, compound="left", image=img_chiudi_btn,
        text=" CHIUDI" if img_chiudi_btn else "CHIUDI",
        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
        cursor="hand2", padding=(10, 5)
    )
    btn_chiudi_btn.image = img_chiudi_btn
    btn_chiudi_btn.pack(side="left", padx=5)
    btn_chiudi_btn.bind("<Button-1>", lambda e: chiudi())
    img_rimanda = self.icone_gui.get("calendario")
    btn_rimanda = ttk.Label(
        frame_bottoni, compound="left", image=img_rimanda,
        text=" RIMANDA" if img_rimanda else "RIMANDA",
        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
        cursor="hand2", padding=(10, 5)
    )
    btn_rimanda.image = img_rimanda
    btn_rimanda.pack(side="left", padx=5)
    btn_rimanda.bind("<Button-1>", lambda e: rimanda())
    win.update()
    min_w = 1000
    w = max(win.winfo_reqwidth(), min_w)
    h = win.winfo_reqheight()
    sx = self.winfo_screenwidth()
    sy = self.winfo_screenheight()
    h = min(h, sy - 80)
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    y = max(40, min(y, sy - h - 40))
    win.geometry(f"{w}x{h}+{x}+{y}")
    win.resizable(False, False)
    win.deiconify()
    win.focus_set()

# Controllo Manuale Forzato degli Aggiornamenti Software
def forza_check_aggiornamento_con_api(self):
    import __main__ as _app
    RIMANDA_FILE = _app.RIMANDA_FILE
    if not self._licenza_valida():
        self.show_toast("Nessuna licenza attiva.", duration=3000)
        return
    import os
    if os.path.exists(RIMANDA_FILE):
        try:
            os.remove(RIMANDA_FILE)
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] File rimando cancellato per la verifica manuale forzata.")
        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore durante la cancellazione del file rimando: {e}")
    threading.Thread(target=self._forza_check_thread, daemon=True).start()

def _forza_check_thread(self):
    import __main__ as _app
    REPO_OWNER = _app.REPO_OWNER
    REPO_NAME = _app.REPO_NAME
    NOME_FILE = _app.NOME_FILE
    BRANCH_PRINCIPALE = _app.BRANCH_PRINCIPALE
    _boot_git_blob_sha1 = _app._boot_git_blob_sha1
    ConnectionError = _app.ConnectionError
    RequestException = _app.RequestException
    import os
    from datetime import datetime, timezone, timedelta
    try:
        api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/commits"
        params = {"path": NOME_FILE, "per_page": 1}
        response = requests.get(api_url, params=params, timeout=5)
        response.raise_for_status()
        commits = response.json()
        if not commits:
            self.after(0, lambda: self.show_custom_warning("Controllo Aggiornamento",
                                     "Nessun commit trovato. Impossibile verificare lo stato."))
            return
        commit_date = commits[0]["commit"]["committer"]["date"]
        remote_time = datetime.strptime(commit_date, "%Y-%m-%dT%H:%M:%SZ").replace(microsecond=0)
        try:
            contents_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{NOME_FILE}"
            contents_resp = requests.get(contents_url, params={"ref": BRANCH_PRINCIPALE}, timeout=5)
            contents_resp.raise_for_status()
            sha_remoto = contents_resp.json().get("sha", "")
            sha_locale = _boot_git_blob_sha1(NOME_FILE) if os.path.exists(NOME_FILE) else None
            if sha_locale == sha_remoto:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Software allineato all'ultimo commit (hash identico).")
                self.after(0, lambda: self.show_toast("Sei gia' aggiornato all'ultima versione.", duration=2500))
                return
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Impossibile verificare lo SHA remoto, fallback su data: {e}")
        changelog_text = ""
        for commit in commits:
            date_str = commit["commit"]["committer"]["date"]
            commit_dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
            message = commit["commit"]["message"].strip().replace('\r', '')
            lines = message.split('\n')
            subject = lines[0]
            body_lines = lines[1:]
            start_index = 0
            while start_index < len(body_lines):
                current_line = body_lines[start_index].strip()
                if not current_line or current_line == subject.strip():
                    start_index += 1
                else:
                    break
            body_lines = body_lines[start_index:]
            changelog_entry = f"▸ [{commit_dt.strftime('%d/%m/%y %H:%M')}] {subject}\n"
            if body_lines:
                for line in body_lines:
                    if line.strip():
                        changelog_entry += f"   → {line}\n"
                    else:
                        changelog_entry += "\n"
            changelog_entry += "\n"
            changelog_text += changelog_entry
        if not os.path.exists(NOME_FILE):
            def _avvisa():
                if self.state() == 'iconic':
                    self.deiconify()
                    self.lift()
                    self.focus_force()
                self.show_custom_warning(
                    "File mancante",
                    f"⚠️ File '{NOME_FILE}' non trovato (rinominato o rimosso).\n\n"
                    "Vai in 'Opzioni' -> 'Forza Aggiornamento Software' per ripristinarlo."
                )
            self.after(0, _avvisa)
            return
        local_time = datetime.fromtimestamp(
            os.path.getmtime(NOME_FILE), timezone.utc
        ).replace(microsecond=0)
        if remote_time.date() > local_time.date():
            self.after(0, lambda rt=remote_time, lt=local_time, ct=changelog_text:
                       self._mostra_popup_forza_aggiornamento(rt, lt, ct))
        else:
            self.after(0, lambda: self.show_custom_warning(
                "Controllo Manuale",
                "Nessun nuovo aggiornamento software disponibile."
            ))
    except ConnectionError:
        self.after(0, lambda: self.show_toast("Connessione assente o GitHub non raggiungibile."))
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Connessione assente o GitHub non raggiungibile.")
    except RequestException as e:
        self.after(0, lambda err=e: self.show_toast(f"Limite GitHub superato o Errore API: {err}"))
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Errore HTTP o API: {e}")
    except Exception as e:
        self.after(0, lambda err=e: self.show_toast(f"Errore generico: {err}"))
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Errore generico durante il controllo aggiornamento: {e}")

def _mostra_popup_forza_aggiornamento(self, remote_time, local_time, changelog_text):
    import __main__ as _app
    REPO_OWNER = _app.REPO_OWNER
    REPO_NAME = _app.REPO_NAME
    NOME_FILE = _app.NOME_FILE
    RIMANDA_FILE = _app.RIMANDA_FILE
    VERSION = _app.VERSION
    import subprocess, sys, os
    from datetime import datetime, timedelta
    def make_separator(parent):
        tk.Frame(parent, bg=self.COLOR_BACKGROUND, height=1).pack(fill="x")
    def make_label_row(parent, label_text, value_text):
        row = tk.Frame(parent, bg=self.COLOR_WIDGET_BG)
        row.pack(fill="x", pady=3)
        tk.Label(row, text=label_text, bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                 font=("Segoe UI", 8), width=18, anchor="w").pack(side="left")
        tk.Label(row, text=value_text, bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
                 font=("Segoe UI", 9), anchor="w").pack(side="left")
    win = tk.Toplevel(self, bg=self.COLOR_BACKGROUND)
    win.withdraw()
    win.title("Aggiornamento Disponibile")
    win.configure(bd=0)
    win.bind('<Escape>', lambda e: win.destroy())
    header = tk.Frame(win, bg=self.COLOR_HEADER_BG, height=42)
    header.pack(fill="x")
    header.pack_propagate(False)
    dot_canvas = tk.Canvas(header, width=10, height=10,
                           bg=self.COLOR_HEADER_BG, highlightthickness=0)
    dot_canvas.create_oval(0, 0, 10, 10, fill=self.COLOR_HIGHLIGHT, outline="")
    dot_canvas.pack(side="left", padx=(16, 8), pady=16)
    tk.Label(header, text="AGGIORNAMENTO DISPONIBILE",
             bg=self.COLOR_HEADER_BG, fg=self.COLOR_HEADER,
             font=("Segoe UI", 8, "bold")).pack(side="left")
    make_separator(win)
    frame_timer = tk.Frame(win, bg=self.COLOR_WIDGET_BG)
    frame_timer.pack(fill="x")
    timer_inner = tk.Frame(frame_timer, bg=self.COLOR_WIDGET_BG)
    timer_inner.pack(fill="x", padx=16, pady=8)
    timer_dot = tk.Canvas(timer_inner, width=8, height=8,
                          bg=self.COLOR_WIDGET_BG, highlightthickness=0)
    timer_dot.create_oval(0, 0, 8, 8, fill=self.COLOR_RED_SMOOTH, outline="")
    timer_dot.pack(side="left", padx=(0, 8))
    label_timer = tk.Label(timer_inner,
                           text="⏱  Chiusura automatica tra 60 secondi",
                           bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                           font=("Segoe UI", 9))
    label_timer.pack(side="left")
    make_separator(win)
    info_outer = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    info_outer.pack(fill="x", padx=16, pady=(14, 0))
    tk.Frame(info_outer, bg=self.COLOR_HIGHLIGHT, width=3).pack(side="left", fill="y")
    info_card = tk.Frame(info_outer, bg=self.COLOR_WIDGET_BG)
    info_card.pack(side="left", fill="both", expand=True)
    inner_pad = tk.Frame(info_card, bg=self.COLOR_WIDGET_BG)
    inner_pad.pack(fill="x", padx=12, pady=10)
    make_label_row(inner_pad, "VERSIONE ONLINE", f"📡  {remote_time.strftime('%d/%m/%Y   %H:%M')}")
    make_label_row(inner_pad, "VERSIONE LOCALE",  f"🖥️  {local_time.strftime('%d/%m/%Y   %H:%M')}")
    cl_header = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    cl_header.pack(fill="x", padx=16, pady=(14, 4))
    tk.Label(cl_header, text="CHANGELOG",
             bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
             font=("Segoe UI", 8, "bold")).pack(side="left")
    frame_changelog = tk.Frame(win, bg=self.COLOR_WIDGET_BG,
                               highlightbackground=self.COLOR_HEADER_BG,
                               highlightthickness=1)
    frame_changelog.pack(padx=16, pady=(0, 6), fill='both', expand=True)
    scrollbar = ttk.Scrollbar(frame_changelog, style="Vertical.TScrollbar")
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    text_area = tk.Text(
        frame_changelog,
        wrap=tk.WORD,
        yscrollcommand=scrollbar.set,
        height=7, width=60,
        font=("Consolas", 9),
        bg=self.COLOR_WIDGET_BG,
        fg=self.TEXT_COLOR,
        insertbackground=self.COLOR_HIGHLIGHT,
        selectbackground=self.COLOR_HIGHLIGHT,
        selectforeground=self.COLOR_WHITE,
        relief="flat", bd=0,
        padx=10, pady=8
    )
    text_area.insert(tk.END, changelog_text.strip())
    text_area.config(state=tk.DISABLED)
    text_area.pack(side=tk.LEFT, fill='both', expand=True)
    scrollbar.config(command=text_area.yview)
    make_separator(win)
    tk.Label(win,
             text="Vuoi procedere con l'aggiornamento adesso?",
             bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
             font=("Segoe UI", 9)).pack(pady=(10, 0))
    frame_bottoni = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    frame_bottoni.pack(pady=14)
    def aggiorna_timer(secondi_rimasti):
        try:
            win.attributes('-topmost', True)
        except Exception:
            pass
        if secondi_rimasti > 0:
            label_timer.config(
                text=f"⏱  Chiusura automatica tra {secondi_rimasti} secondi",
                fg=self.COLOR_RED_SMOOTH if secondi_rimasti <= 10 else self.TEXT_COLOR
            )
            win.after(1000, aggiorna_timer, secondi_rimasti - 1)
        else:
            label_timer.config(text="⏱  Chiusura in corso...", fg=self.COLOR_RED_SMOOTH)
            win.destroy()
    timeout_id = win.after(60000, win.destroy)
    aggiorna_timer(60)
    def annulla_timeout():
        win.after_cancel(timeout_id)
    def aggiorna():
        annulla_timeout()
        url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/{NOME_FILE.replace(' ', '%20')}"
        try:
            nome_backup = f"{NOME_FILE}.bak"
            if os.path.exists(NOME_FILE):
                shutil.copy2(NOME_FILE, nome_backup)
            urllib.request.urlretrieve(url, NOME_FILE)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Download completato! {NOME_FILE} è stato aggiornato.")
            threading.Thread(
                target=lambda: self.verify_environment_update(f"UPDATED_to_{VERSION}"),
                daemon=True
            ).start()
            if os.path.exists(RIMANDA_FILE):
                try:
                    os.remove(RIMANDA_FILE)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] File rimando eliminato dopo aggiornamento.")
                except Exception as err:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Errore durante l'eliminazione del file rimando: {err}")
            win.destroy()
            self.show_toast("Riavvio in corso. File aggiornato! ATTENDERE...", duration=2000)
            script_path = os.path.abspath(sys.argv[0])
            args = [sys.executable, script_path] + sys.argv[1:]
            if os.name == 'nt':
                subprocess.Popen(args, creationflags=0x00000008, shell=False, close_fds=True)
            else:
                subprocess.Popen(args, start_new_session=True, close_fds=True)
            os._exit(0)
        except Exception as e:
            if 'shutil' in sys.modules and os.path.exists(nome_backup):
                shutil.copy2(nome_backup, NOME_FILE)
                os.remove(nome_backup)
            self.show_custom_warning(
                "Attenzione",
                f"❌ Aggiornamento fallito durante il download/riavvio:\n{e}"
            )
    def chiudi():
        annulla_timeout()
        win.destroy()
    def rimanda():
        annulla_timeout()
        win.destroy()
        nuova_data = datetime.today() + timedelta(days=15)
        with open(RIMANDA_FILE, "w") as f:
            json.dump({"rimanda_fino": nuova_data.strftime("%Y-%m-%d")}, f)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Aggiornamento Rimandato fino al {nuova_data.date()}")
        data_formattata = nuova_data.date().strftime("%d/%m/%Y")
        self.show_toast(f"Aggiornamento Rimandato fino al {data_formattata}", duration=2500)
    img_aggiorna = self.icone_gui.get("reset_campo")
    btn_aggiorna = ttk.Label(
        frame_bottoni, compound="left", image=img_aggiorna,
        text=" AGGIORNA" if img_aggiorna else "AGGIORNA",
        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
        cursor="hand2", padding=(10, 5)
    )
    btn_aggiorna.image = img_aggiorna
    btn_aggiorna.pack(side="left", padx=5)
    btn_aggiorna.bind("<Button-1>", lambda e: aggiorna())
    img_chiudi_btn = self.icone_gui.get("chiudi")
    btn_chiudi_btn = ttk.Label(
        frame_bottoni, compound="left", image=img_chiudi_btn,
        text=" CHIUDI" if img_chiudi_btn else "CHIUDI",
        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
        cursor="hand2", padding=(10, 5)
    )
    btn_chiudi_btn.image = img_chiudi_btn
    btn_chiudi_btn.pack(side="left", padx=5)
    btn_chiudi_btn.bind("<Button-1>", lambda e: chiudi())
    img_rimanda = self.icone_gui.get("calendario")
    btn_rimanda = ttk.Label(
        frame_bottoni, compound="left", image=img_rimanda,
        text=" RIMANDA" if img_rimanda else "RIMANDA",
        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
        cursor="hand2", padding=(10, 5)
    )
    btn_rimanda.image = img_rimanda
    btn_rimanda.pack(side="left", padx=5)
    btn_rimanda.bind("<Button-1>", lambda e: rimanda())
    win.update()
    min_w = 1000
    w = max(win.winfo_reqwidth(), min_w)
    h = win.winfo_reqheight()
    sx = self.winfo_screenwidth()
    sy = self.winfo_screenheight()
    h = min(h, sy - 80)
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    y = max(40, min(y, sy - h - 40))
    win.geometry(f"{w}x{h}+{x}+{y}")
    win.resizable(False, False)
    win.deiconify()
    win.focus_set()

# Gestione Aggiornamento Dipendenze Software (libreria pip)
def aggiorna_librerie_pip(self):
    import subprocess, sys, threading, os, platform, json as _json
    import importlib.metadata as metadata
    import urllib.request
    LIBRERIE = [
        ("tkcalendar",   "Calendario"),
        ("flask",        "Web Server (flask)"),
        ("requests",     "Richieste HTTP"),
        ("google-genai", "Google Gemini AI"),
        ("Pillow",       "Immagini (PIL)"),
        ("PyMuPDF",      "Visualizzatore PDF"),
        ("pystray",      "System Tray (solo Windows)"),
        ("segno",        "Generatore QR"),
        ("cryptography", "Crittografia SSL"),
        ("yfinance",     "Mercati Finanziari"),
        ("tkinterdnd2",  "Drag & Drop documenti"),
    ]
    if platform.system() == "Windows":
        LIBRERIE.append(("pywin32", "Stampa Windows"))
    def _versione_installata(pkg):
        try:
            return metadata.version(pkg)
        except metadata.PackageNotFoundError:
            return None
    def _versione_disponibile(pkg):
        try:
            with urllib.request.urlopen(f"https://pypi.org/pypi/{pkg}/json", timeout=5) as resp:
                data = _json.loads(resp.read().decode("utf-8"))
                return data.get("info", {}).get("version")
        except Exception:
            return None
    popup = tk.Toplevel(self)
    popup.title("Aggiornamento Librerie Python")
    popup.configure(bg=self.COLOR_BACKGROUND)
    popup.resizable(False, False)
    popup.transient(self)
    popup.bind("<Escape>", lambda e: popup.destroy())
    w, h = 980, 620
    sw, sh = popup.winfo_screenwidth(), popup.winfo_screenheight()
    popup.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
    header = tk.Frame(popup, bg=self.COLOR_HEADER_BG, height=40)
    header.pack(fill=tk.X)
    header.pack_propagate(False)
    img_h = self.icone_gui.get("sync")
    tk.Label(header, compound="left", image=img_h,
             text="  Aggiornamento Librerie Python",
             bg=self.COLOR_HEADER_BG, fg=self.COLOR_HEADER,
             font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=14, pady=10)
    body = tk.Frame(popup, bg=self.COLOR_BACKGROUND, padx=20, pady=12)
    body.pack(fill=tk.BOTH, expand=True)

    frame_top = tk.Frame(body, bg=self.COLOR_BACKGROUND)
    frame_top.pack(fill=tk.X, pady=(0, 2))
    tk.Label(frame_top, text="Seleziona le librerie da aggiornare:",
             bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
             font=("Segoe UI", 9)).pack(side=tk.LEFT)
    var_tutti = tk.BooleanVar(value=True)
    chk_tutti = ttk.Checkbutton(frame_top, variable=var_tutti, style="TCheckbutton")
    chk_tutti.pack(side=tk.LEFT, padx=(16, 4))
    lbl_tutti = tk.Label(frame_top, text="Tutto / Nessuno",
                         bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
                         font=("Segoe UI", 8), cursor="hand2")
    lbl_tutti.pack(side=tk.LEFT)
    lbl_check_ver = tk.Label(frame_top, text="🔄 Verifica versioni PyPI...",
                             bg=self.COLOR_BACKGROUND, fg="gray60",
                             font=("Segoe UI", 8, "italic"))
    lbl_check_ver.pack(side=tk.RIGHT)
    frame_pyver = tk.Frame(body, bg=self.COLOR_BACKGROUND)
    frame_pyver.pack(anchor="w", pady=(0, 8))
    tk.Label(frame_pyver, text=f"Interprete: Python {sys.version.split()[0]}  —  {sys.executable}",
             bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
             font=("Consolas", 8)).pack(side=tk.LEFT)
    lnk = tk.Label(frame_pyver, text="  🌐 python.org",
                   bg=self.COLOR_BACKGROUND, fg=self.COLOR_HIGHLIGHT,
                   font=("Segoe UI", 9, "bold"), cursor="hand2")
    lnk.pack(side=tk.LEFT)
    lnk.bind("<Button-1>", lambda e: __import__("webbrowser").open("https://www.python.org"))
    lbl_py_stato = tk.Label(frame_pyver, text="  🔄 verifica...",
                            bg=self.COLOR_BACKGROUND, fg="gray60",
                            font=("Consolas", 8, "italic", "bold"))
    lbl_py_stato.pack(side=tk.LEFT)
    def _verifica_python():
        ver_corrente = sys.version_info
        ciclo = f"{ver_corrente.major}.{ver_corrente.minor}"
        ver_installata = sys.version.split()[0]
        try:
            with urllib.request.urlopen("https://endoflife.date/api/python.json", timeout=8) as resp:
                data = _json.loads(resp.read().decode("utf-8"))
            info_ciclo = next((r for r in data if r.get("cycle") == ciclo), None)
            if info_ciclo is None:
                esito = ("  n/d", "gray50")
            else:
                eol = info_ciclo.get("eol")
                ultima = info_ciclo.get("latest")
                eol_scaduto = isinstance(eol, str) and eol < datetime.date.today().isoformat()
                if eol_scaduto:
                    esito = (f"  Python {ciclo} non è più supportato (EOL {eol})", "#C62828")
                elif ultima and ultima != ver_installata:
                    esito = (f"  Disponibile Python {ultima}", "#E65100")
                else:
                    esito = ("  Aggiornato", "#2E7D32")
        except Exception:
            esito = ("  n/d (offline)", "gray50")
        def _aggiorna_py():
            if popup.winfo_exists():
                lbl_py_stato.config(text=esito[0], fg=esito[1])
        self.after(0, _aggiorna_py)
    threading.Thread(target=_verifica_python, daemon=True).start()
    frame_checks = tk.Frame(body, bg=self.COLOR_WIDGET_BG,
                            highlightbackground=self.COLOR_HEADER_BG, highlightthickness=1)
    frame_checks.pack(fill=tk.X)
    vars_lib = []
    righe_ver = {}
    meta = len(LIBRERIE) // 2 + len(LIBRERIE) % 2
    col_sx = tk.Frame(frame_checks, bg=self.COLOR_WIDGET_BG)
    col_dx = tk.Frame(frame_checks, bg=self.COLOR_WIDGET_BG)
    col_sx.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=6)
    col_dx.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=6)
    for i, (pkg, desc) in enumerate(LIBRERIE):
        var = tk.BooleanVar(value=True)
        vars_lib.append((pkg, var))
        parent = col_sx if i < meta else col_dx
        row = tk.Frame(parent, bg=self.COLOR_WIDGET_BG)
        row.pack(fill=tk.X, pady=2)
        ttk.Checkbutton(row, variable=var, style="TCheckbutton").pack(side=tk.LEFT)
        tk.Label(row, text=pkg, bg=self.COLOR_WIDGET_BG,
                 fg=self.COLOR_HIGHLIGHT, font=("Consolas", 8, "bold"),
                 width=18, anchor="w").pack(side=tk.LEFT)
        ver_installata = _versione_installata(pkg)
        lbl_inst = tk.Label(row, text=f"v{ver_installata}" if ver_installata else "n/d",
                            bg=self.COLOR_WIDGET_BG, fg="gray60",
                            font=("Consolas", 7), width=9, anchor="w")
        lbl_inst.pack(side=tk.LEFT)
        tk.Label(row, text="→", bg=self.COLOR_WIDGET_BG, fg="gray50",
                 font=("Consolas", 7), width=2, anchor="center").pack(side=tk.LEFT)
        lbl_disp = tk.Label(row, text="...", bg=self.COLOR_WIDGET_BG, fg="gray60",
                            font=("Consolas", 7, "italic"), width=9, anchor="w")
        lbl_disp.pack(side=tk.LEFT)
        righe_ver[pkg] = (lbl_inst, lbl_disp, ver_installata)
        tk.Label(row, text=f"— {desc}", bg=self.COLOR_WIDGET_BG,
                 fg=self.TEXT_COLOR, font=("Segoe UI", 8)).pack(side=tk.LEFT)
    def _toggle_tutti():
        stato = var_tutti.get()
        for _, v in vars_lib:
            v.set(stato)
    var_tutti.trace_add("write", lambda *_: _toggle_tutti())
    lbl_tutti.bind("<Button-1>", lambda e: var_tutti.set(not var_tutti.get()))
    def _carica_versioni_disponibili():
        for pkg, (lbl_inst, lbl_disp, ver_inst) in righe_ver.items():
            ver_pypi = _versione_disponibile(pkg)
            def _aggiorna_lbl(lbl=lbl_disp, v=ver_pypi, vi=ver_inst):
                if not popup.winfo_exists():
                    return
                if v is None:
                    lbl.config(text="n/d", fg="gray50")
                elif vi is not None and v != vi:
                    lbl.config(text=f"v{v}", fg="#E65100")
                elif vi is not None:
                    lbl.config(text=f"v{v}", fg="#2E7D32")
                else:
                    lbl.config(text=f"v{v}", fg="gray60")
            self.after(0, _aggiorna_lbl)
        self.after(0, lambda: lbl_check_ver.config(text="✓ Versioni verificate") if popup.winfo_exists() else None)
    threading.Thread(target=_carica_versioni_disponibili, daemon=True).start()
    tk.Label(body, text="Output:", bg=self.COLOR_BACKGROUND,
             fg=self.TEXT_COLOR, font=("Segoe UI", 8)).pack(anchor="w", pady=(10, 2))
    frame_txt = tk.Frame(body, bg=self.COLOR_WIDGET_BG,
                         highlightbackground=self.COLOR_HEADER_BG, highlightthickness=1)
    frame_txt.pack(fill=tk.BOTH, expand=True)
    sb = ttk.Scrollbar(frame_txt, style="Vertical.TScrollbar")
    sb.pack(side=tk.RIGHT, fill=tk.Y)
    txt = tk.Text(frame_txt, height=7, bg=self.COLOR_HEADER_BG, fg=self.TEXT_COLOR,
                  font=("Consolas", 8), relief="flat", bd=0, padx=6, pady=4,
                  yscrollcommand=sb.set, state=tk.DISABLED)
    txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.config(command=txt.yview)
    frame_btn = tk.Frame(popup, bg=self.COLOR_BACKGROUND, pady=10)
    frame_btn.pack(fill=tk.X, padx=20)
    img_avvia   = self.icone_gui.get("sync")
    img_riavvia = self.icone_gui.get("reset")
    img_chiudi  = self.icone_gui.get("chiudi")
    btn_avvia = tk.Label(frame_btn, compound="left", image=img_avvia,
                         text=" Aggiorna", bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                         cursor="hand2", padx=14, pady=7, font=("Arial", 9, "bold"))
    btn_riavvia = tk.Label(frame_btn, compound="left", image=img_riavvia,
                           text=" Riavvia App", bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                           cursor="X_cursor", padx=14, pady=7, font=("Arial", 9, "bold"))
    btn_chiudi_l = tk.Label(frame_btn, compound="left", image=img_chiudi,
                            text=" Chiudi", bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                            cursor="hand2", padx=14, pady=7, font=("Arial", 9, "bold"))
    btn_avvia.pack(side=tk.LEFT, expand=True)
    btn_riavvia.pack(side=tk.LEFT, expand=True)
    btn_chiudi_l.pack(side=tk.LEFT, expand=True)
    btn_chiudi_l.bind("<Button-1>", lambda e: popup.destroy())
    def _log(msg):
        txt.config(state=tk.NORMAL)
        txt.insert(tk.END, msg + "\n")
        txt.see(tk.END)
        txt.config(state=tk.DISABLED)
    def _riavvia(e=None):
        self.show_toast("Riavvio In Corso !", duration=3000)
        def esegui_kill():
            if popup.winfo_exists():
                popup.destroy()
            script_path = os.path.abspath(sys.argv[0])
            args = [sys.executable, script_path] + sys.argv[1:]
            if os.name == 'nt':
                subprocess.Popen(args, creationflags=0x00000008, shell=False, close_fds=True)
            else:
                subprocess.Popen(args, start_new_session=True, close_fds=True)
            self.destroy()
            os._exit(0)
        self.after(800, esegui_kill)

    def _abilita_riavvia():
        btn_riavvia.config(cursor="hand2")
        btn_riavvia.bind("<Button-1>", _riavvia)
        self.btn_aggiorna_lib.pack_forget()

    def _esegui():
        btn_avvia.config(cursor="X_cursor")
        btn_avvia.unbind("<Button-1>")
        selezionate = [(pkg, var) for pkg, var in vars_lib if var.get()]
        if not selezionate:
            self.after(0, lambda: _log("⚠️ Nessuna libreria selezionata."))
            self.after(0, lambda: btn_avvia.config(cursor="hand2", fg=self.TEXT_COLOR))
            self.after(0, lambda: btn_avvia.bind("<Button-1>", lambda e: threading.Thread(target=_esegui, daemon=True).start()))
            return
        self.after(0, lambda: _log(f"Avvio aggiornamento {len(selezionate)} librerie...\n"))
        errori = 0
        for pkg, _ in selezionate:
            self.after(0, lambda l=pkg: _log(f"⏳ {l}..."))
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-U", pkg, "--break-system-packages"],
                    capture_output=True, text=True, timeout=120
                )
                if result.returncode == 0:
                    nuova_ver = _versione_installata(pkg)
                    self.after(0, lambda l=pkg, v=nuova_ver: _log(f"✓ {l} aggiornato → v{v}" if v else f"✓ {l} aggiornato"))
                    if pkg in righe_ver:
                        lbl_inst_w = righe_ver[pkg][0]
                        self.after(0, lambda lbl=lbl_inst_w, v=nuova_ver: lbl.config(text=f"v{v}" if v else "n/d", fg="#2E7D32"))
                else:
                    errori += 1
                    err = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "errore"
                    self.after(0, lambda l=pkg, e=err: _log(f"⚠️ {l}: {e[:80]}"))
            except subprocess.TimeoutExpired:
                errori += 1
                self.after(0, lambda l=pkg: _log(f"❌ {l}: timeout"))
            except Exception as ex:
                errori += 1
                self.after(0, lambda l=pkg, e=str(ex): _log(f"❌ {l}: {e}"))
        msg = f"\n✅ Completato. {len(selezionate)-errori} ok, {errori} errori." if errori else "\n✅ Completato. Tutte le librerie aggiornate."
        self.after(0, lambda: _log(msg))
        self.after(0, _abilita_riavvia)
    btn_avvia.bind("<Button-1>", lambda e: threading.Thread(target=_esegui, daemon=True).start())
