#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import threading
import datetime
import tkinter as tk
from tkinter import ttk

from __main__ import NOME_EDITOR_LOCALE, GITHUB_SUPERMARKET, requests, _boot_git_blob_sha1

def _ottieni_sha_remoto_supermarket(repo_owner, repo_name, branch, path):
    api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{path}?ref={branch}"
    response = requests.get(api_url, timeout=5, headers={"Accept": "application/vnd.github+json"})
    response.raise_for_status()
    dati = response.json()
    return dati.get("sha")

# Aggiornamenti Github Supermarket.pyw
def check_supermarket_update(self):
    import datetime
    from datetime import timedelta
    nome_file_locale = NOME_EDITOR_LOCALE
    try:
        url_parts = GITHUB_SUPERMARKET.split('/')
        REPO_OWNER = url_parts[3] 
        REPO_NAME = url_parts[4]
        BRANCH = url_parts[5]
        PATH_REMOTO = "/".join(url_parts[6:])
        titolo_popup = "🔄 Aggiornamento Disponibile"
    except IndexError:
        print(f"Errore nel parsing dell'URL GITHUB_SUPERMARKET.")
        return
    except NameError:
        print(f"Errore: Costanti GITHUB_SUPERMARKET o NOME_EDITOR_LOCALE non definite.")
        return
    try:
        api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/commits"
        params = {"path": nome_file_locale, "per_page": 1} 
        response = requests.get(api_url, params=params, timeout=5)
        response.raise_for_status()
        commits = response.json()
        if not commits: return
        commit_date = commits[0]["commit"]["committer"]["date"]
        remote_time = datetime.datetime.strptime(commit_date, "%Y-%m-%dT%H:%M:%SZ").replace(microsecond=0)
        changelog_text = ""
        for commit in commits:
            date_str = commit["commit"]["committer"]["date"]
            commit_dt = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
            message = commit["commit"]["message"].strip()
            message = message.replace('\r', '') 
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
            changelog_entry = f"📝 [{commit_dt.strftime('%d/%m/%y %H:%M')}] {subject}\n"
            if body_lines:
                for line in body_lines:
                    if line.strip(): 
                        changelog_entry += f" ➡️ {line}\n"
                    else:
                         changelog_entry += "\n"
            changelog_entry += "\n" 
            changelog_text += changelog_entry
        if not os.path.exists(nome_file_locale):
            # self.show_custom_warning("File Editor Mancante", f"⚠️ L'editor locale ({nome_file_locale}) non esiste. Aggiornamento consigliato.")
            return
        local_time = datetime.datetime.fromtimestamp(os.path.getmtime(nome_file_locale), datetime.timezone.utc).replace(microsecond=0)
        try:
            sha_remoto = _ottieni_sha_remoto_supermarket(REPO_OWNER, REPO_NAME, BRANCH, PATH_REMOTO)
            sha_locale = _boot_git_blob_sha1(nome_file_locale)
            necessita_aggiornamento = sha_remoto is not None and sha_remoto != sha_locale
        except Exception:
            necessita_aggiornamento = remote_time.date() > local_time.date()
        if necessita_aggiornamento:
            win = tk.Toplevel(self, bg=self.COLOR_BACKGROUND)
            win.withdraw()
            win.title("Aggiornamento Editor Disponibile")
            win.configure(bd=0)
            win.bind('<Escape>', lambda e: win.destroy())
            header = tk.Frame(win, bg=self.COLOR_HEADER_BG, height=42)
            header.pack(fill="x")
            header.pack_propagate(False)
            dot_canvas = tk.Canvas(header, width=10, height=10,
                                   bg=self.COLOR_HEADER_BG, highlightthickness=0)
            dot_canvas.create_oval(0, 0, 10, 10, fill=self.COLOR_HIGHLIGHT, outline="")
            dot_canvas.pack(side="left", padx=(16, 8), pady=16)
            tk.Label(header, text="AGGIORNAMENTO EDITOR DISPONIBILE",
                     bg=self.COLOR_HEADER_BG, fg=self.COLOR_HEADER,
                     font=("Segoe UI", 8, "bold")).pack(side="left")
            tk.Frame(win, bg=self.COLOR_BACKGROUND, height=1).pack(fill="x")
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
            tk.Frame(win, bg=self.COLOR_BACKGROUND, height=1).pack(fill="x")
            info_outer = tk.Frame(win, bg=self.COLOR_BACKGROUND)
            info_outer.pack(fill="x", padx=16, pady=(14, 0))
            tk.Frame(info_outer, bg=self.COLOR_HIGHLIGHT, width=3).pack(side="left", fill="y")
            info_card = tk.Frame(info_outer, bg=self.COLOR_WIDGET_BG)
            info_card.pack(side="left", fill="both", expand=True)
            inner_pad = tk.Frame(info_card, bg=self.COLOR_WIDGET_BG)
            inner_pad.pack(fill="x", padx=12, pady=10)
            row1 = tk.Frame(inner_pad, bg=self.COLOR_WIDGET_BG)
            row1.pack(fill="x", pady=3)
            tk.Label(row1, text="VERSIONE ONLINE", bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                     font=("Segoe UI", 8), width=18, anchor="w").pack(side="left")
            tk.Label(row1, text=f"📡  {remote_time.strftime('%d/%m/%Y   %H:%M')}",
                     bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
                     font=("Segoe UI", 9), anchor="w").pack(side="left")
            row2 = tk.Frame(inner_pad, bg=self.COLOR_WIDGET_BG)
            row2.pack(fill="x", pady=3)
            tk.Label(row2, text="VERSIONE LOCALE", bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                     font=("Segoe UI", 8), width=18, anchor="w").pack(side="left")
            tk.Label(row2, text=f"🖥️  {local_time.strftime('%d/%m/%Y   %H:%M')}",
                     bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
                     font=("Segoe UI", 9), anchor="w").pack(side="left")
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
            tk.Frame(win, bg=self.COLOR_BACKGROUND, height=1).pack(fill="x")
            tk.Label(win,
                     text="Vuoi procedere con l'aggiornamento adesso?",
                     bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
                     font=("Segoe UI", 9)).pack(pady=(10, 0))
            frame_bottoni = tk.Frame(win, bg=self.COLOR_BACKGROUND)
            frame_bottoni.pack(pady=14)
            _timer_id = [None]
            def aggiorna_timer(secondi_rimasti):
                if secondi_rimasti > 0:
                    label_timer.config(
                        text=f"⏱  Chiusura automatica tra {secondi_rimasti} secondi",
                        fg=self.COLOR_RED_SMOOTH if secondi_rimasti <= 10 else self.TEXT_COLOR
                    )
                    _timer_id[0] = win.after(1000, aggiorna_timer, secondi_rimasti - 1)
                else:
                    label_timer.config(text="⏱  Chiusura in corso...", fg=self.COLOR_RED_SMOOTH)
                    win.destroy()
            aggiorna_timer(60)
            def annulla_timeout():
                if _timer_id[0] is not None:
                    win.after_cancel(_timer_id[0])
            def aggiorna():
                annulla_timeout()
                win.destroy()
                if self.aggiorna(GITHUB_SUPERMARKET, nome_file_locale):
                    self.show_custom_info("Editor Aggiornato", f"L'editor {nome_file_locale} è stato aggiornato!")
            def chiudi():
                annulla_timeout()
                win.destroy()
            img_aggiorna = self.icone_gui.get("reset_campo")
            btn_aggiorna = ttk.Label(
                frame_bottoni,
                compound="left",
                image=img_aggiorna,
                text=" AGGIORNA" if img_aggiorna else "AGGIORNA",
                background=self.COLOR_WIDGET_BG,
                foreground=self.TEXT_COLOR,
                cursor="hand2",
                padding=(10, 5)
            )
            btn_aggiorna.image = img_aggiorna
            btn_aggiorna.pack(side="left", padx=5)
            btn_aggiorna.bind("<Button-1>", lambda e: aggiorna())
            img_chiudi = self.icone_gui.get("chiudi")
            btn_chiudi = ttk.Label(
                frame_bottoni,
                compound="left",
                image=img_chiudi,
                text=" CHIUDI" if img_chiudi else "CHIUDI",
                background=self.COLOR_WIDGET_BG,
                foreground=self.TEXT_COLOR,
                cursor="hand2",
                padding=(10, 5)
            )
            btn_chiudi.image = img_chiudi
            btn_chiudi.pack(side="left", padx=5)
            btn_chiudi.bind("<Button-1>", lambda e: chiudi())
            win.update_idletasks()
            min_w, min_h = 1000, 440
            w = max(win.winfo_reqwidth(), min_w)
            h = max(win.winfo_reqheight(), min_h)
            x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
            y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
            win.geometry(f"{w}x{h}+{x}+{y}")
            win.resizable(False, False)
            win.deiconify()
            win.grab_set()
            win.transient(self.master)
            win.focus_set()
            win.wait_window()
    except requests.exceptions.ConnectionError:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Connessione assente o GitHub non raggiungibile per {nome_file_locale}.")
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore HTTP o API per {nome_file_locale}: {e}")
    except Exception as e:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore generico durante il controllo aggiornamento per {nome_file_locale}: {e}")

def check_supermarket_update_manuale(self):
    import datetime
    from datetime import timedelta
    nome_file_locale = NOME_EDITOR_LOCALE
    try:
        url_parts = GITHUB_SUPERMARKET.split('/')
        REPO_OWNER = url_parts[3]
        REPO_NAME = url_parts[4]
        BRANCH = url_parts[5]
        PATH_REMOTO = "/".join(url_parts[6:])
        titolo_popup = "🔄 Aggiornamento Disponibile"
    except IndexError:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore nel parsing dell'URL GITHUB_SUPERMARKET.")
        return
    except NameError:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore: Costanti GITHUB_SUPERMARKET o NOME_EDITOR_LOCALE non definite.")
        return
    try:
        api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/commits"
        params = {"path": nome_file_locale, "per_page": 1}
        response = requests.get(api_url, params=params, timeout=5)
        response.raise_for_status()
        commits = response.json()
        if not commits: return
        commit_date = commits[0]["commit"]["committer"]["date"]
        remote_time = datetime.datetime.strptime(commit_date, "%Y-%m-%dT%H:%M:%SZ").replace(microsecond=0)
        changelog_text = ""
        for commit in commits:
            date_str = commit["commit"]["committer"]["date"]
            commit_dt = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
            message = commit["commit"]["message"].strip()
            message = message.replace('\r', '')
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
            changelog_entry = f"📝 [{commit_dt.strftime('%d/%m/%y %H:%M')}] {subject}\n"
            if body_lines:
                for line in body_lines:
                    if line.strip():
                        changelog_entry += f" ➡️ {line}\n"
                    else:
                         changelog_entry += "\n"
            changelog_entry += "\n"
            changelog_text += changelog_entry
        if not os.path.exists(nome_file_locale):
            # self.show_custom_warning("File Editor Mancante", f"⚠️ L'editor locale ({nome_file_locale}) non esiste. Aggiornamento consigliato.")
            return
        local_time = datetime.datetime.fromtimestamp(os.path.getmtime(nome_file_locale), datetime.timezone.utc).replace(microsecond=0)
        try:
            sha_remoto = _ottieni_sha_remoto_supermarket(REPO_OWNER, REPO_NAME, BRANCH, PATH_REMOTO)
            sha_locale = _boot_git_blob_sha1(nome_file_locale)
            necessita_aggiornamento = sha_remoto is not None and sha_remoto != sha_locale
        except Exception:
            necessita_aggiornamento = remote_time.date() > local_time.date()
        if necessita_aggiornamento:
            win = tk.Toplevel(self, bg=self.COLOR_BACKGROUND)
            win.withdraw()
            win.title("Aggiornamento Editor Disponibile")
            win.configure(bd=0)
            win.bind('<Escape>', lambda e: win.destroy())
            header = tk.Frame(win, bg=self.COLOR_HEADER_BG, height=42)
            header.pack(fill="x")
            header.pack_propagate(False)
            dot_canvas = tk.Canvas(header, width=10, height=10,
                                   bg=self.COLOR_HEADER_BG, highlightthickness=0)
            dot_canvas.create_oval(0, 0, 10, 10, fill=self.COLOR_HIGHLIGHT, outline="")
            dot_canvas.pack(side="left", padx=(16, 8), pady=16)
            tk.Label(header, text="AGGIORNAMENTO EDITOR DISPONIBILE",
                     bg=self.COLOR_HEADER_BG, fg=self.COLOR_HEADER,
                     font=("Segoe UI", 8, "bold")).pack(side="left")
            tk.Frame(win, bg=self.COLOR_BACKGROUND, height=1).pack(fill="x")
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
            tk.Frame(win, bg=self.COLOR_BACKGROUND, height=1).pack(fill="x")
            info_outer = tk.Frame(win, bg=self.COLOR_BACKGROUND)
            info_outer.pack(fill="x", padx=16, pady=(14, 0))
            tk.Frame(info_outer, bg=self.COLOR_HIGHLIGHT, width=3).pack(side="left", fill="y")
            info_card = tk.Frame(info_outer, bg=self.COLOR_WIDGET_BG)
            info_card.pack(side="left", fill="both", expand=True)
            inner_pad = tk.Frame(info_card, bg=self.COLOR_WIDGET_BG)
            inner_pad.pack(fill="x", padx=12, pady=10)
            row1 = tk.Frame(inner_pad, bg=self.COLOR_WIDGET_BG)
            row1.pack(fill="x", pady=3)
            tk.Label(row1, text="VERSIONE ONLINE", bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                     font=("Segoe UI", 8), width=18, anchor="w").pack(side="left")
            tk.Label(row1, text=f"📡  {remote_time.strftime('%d/%m/%Y   %H:%M')}",
                     bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
                     font=("Segoe UI", 9), anchor="w").pack(side="left")
            row2 = tk.Frame(inner_pad, bg=self.COLOR_WIDGET_BG)
            row2.pack(fill="x", pady=3)
            tk.Label(row2, text="VERSIONE LOCALE", bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                     font=("Segoe UI", 8), width=18, anchor="w").pack(side="left")
            tk.Label(row2, text=f"🖥️  {local_time.strftime('%d/%m/%Y   %H:%M')}",
                     bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
                     font=("Segoe UI", 9), anchor="w").pack(side="left")
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
            tk.Frame(win, bg=self.COLOR_BACKGROUND, height=1).pack(fill="x")
            tk.Label(win,
                     text="Vuoi procedere con l'aggiornamento adesso?",
                     bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
                     font=("Segoe UI", 9)).pack(pady=(10, 0))
            frame_bottoni = tk.Frame(win, bg=self.COLOR_BACKGROUND)
            frame_bottoni.pack(pady=14)
            _timer_id = [None]
            def aggiorna_timer(secondi_rimasti):
                if secondi_rimasti > 0:
                    label_timer.config(
                        text=f"⏱  Chiusura automatica tra {secondi_rimasti} secondi",
                        fg=self.COLOR_RED_SMOOTH if secondi_rimasti <= 10 else self.TEXT_COLOR
                    )
                    _timer_id[0] = win.after(1000, aggiorna_timer, secondi_rimasti - 1)
                else:
                    label_timer.config(text="⏱  Chiusura in corso...", fg=self.COLOR_RED_SMOOTH)
                    win.destroy()
            aggiorna_timer(60)
            def annulla_timeout():
                if _timer_id[0] is not None:
                    win.after_cancel(_timer_id[0])
            def aggiorna():
                annulla_timeout()
                win.destroy()
                if self.aggiorna(GITHUB_SUPERMARKET, nome_file_locale):
                    self.show_custom_info("Editor Aggiornato", f"L'editor {nome_file_locale} è stato aggiornato!")
            def chiudi():
                annulla_timeout()
                win.destroy()
            img_aggiorna = self.icone_gui.get("reset_campo")
            btn_aggiorna = ttk.Label(
                frame_bottoni,
                compound="left",
                image=img_aggiorna,
                text=" AGGIORNA" if img_aggiorna else "AGGIORNA",
                background=self.COLOR_WIDGET_BG,
                foreground=self.TEXT_COLOR,
                cursor="hand2",
                padding=(10, 5)
            )
            btn_aggiorna.image = img_aggiorna
            btn_aggiorna.pack(side="left", padx=5)
            btn_aggiorna.bind("<Button-1>", lambda e: aggiorna())
            img_chiudi = self.icone_gui.get("chiudi")
            btn_chiudi = ttk.Label(
                frame_bottoni,
                compound="left",
                image=img_chiudi,
                text=" CHIUDI" if img_chiudi else "CHIUDI",
                background=self.COLOR_WIDGET_BG,
                foreground=self.TEXT_COLOR,
                cursor="hand2",
                padding=(10, 5)
            )
            btn_chiudi.image = img_chiudi
            btn_chiudi.pack(side="left", padx=5)
            btn_chiudi.bind("<Button-1>", lambda e: chiudi())
            win.update_idletasks()
            min_w, min_h = 1000, 440
            w = max(win.winfo_reqwidth(), min_w)
            h = max(win.winfo_reqheight(), min_h)
            x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
            y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
            win.geometry(f"{w}x{h}+{x}+{y}")
            win.resizable(False, False)
            win.deiconify()
            win.grab_set()
            win.transient(self.master)
            win.focus_set()
            win.wait_window()
        else:
            self.show_custom_info(
                "Aggiornamento Editor",
                f"L'editor '{nome_file_locale}' è già aggiornato.\n"
                f"Ultima versione locale: {local_time.strftime('%d/%m/%Y %H:%M')}"
            )
    except requests.exceptions.ConnectionError:
        self.show_custom_warning(
             "Connessione Assente",
             f"🌐 Connessione assente o GitHub non raggiungibile per il controllo di {nome_file_locale}."
        )
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore HTTP o API per {nome_file_locale}: {e}")
        self.show_custom_warning(
             "Errore GitHub",
             f"⚠️ Errore nel controllo della versione su GitHub per {nome_file_locale}."
        )
    except Exception as e:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore generico durante il controllo aggiornamento per {nome_file_locale}: {e}")

def _rimuovi_editor_esterno(self):
    try:
        nome_file = NOME_EDITOR_LOCALE
        nome_backup = f"{nome_file}.bak"
        rimossi = []
        if os.path.exists(nome_file):
            try:
                os.remove(nome_file)
                rimossi.append(nome_file)
            except PermissionError:
                self.show_custom_warning(
                    "Errore Permessi", 
                    f"⚠️ Impossibile rimuovere '{nome_file}'. Il file potrebbe essere in uso."
                )
                return
            except Exception as e:
                self.show_custom_warning("Errore Rimozione", f"❌ Errore durante la rimozione di '{nome_file}': {e}")
                return
        if os.path.exists(nome_backup):
            try:
                os.remove(nome_backup)
                rimossi.append(nome_backup)
            except Exception as e:
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Attenzione: Impossibile rimuovere il file di backup '{nome_backup}': {e}")
        if rimossi:
            messaggio_successo = "\n".join(f"✓ Rimosso: {f}" for f in rimossi)
            self.show_custom_info(
                "Rimozione Editor Completata", 
                f"I seguenti file sono stati rimossi con successo:\n{messaggio_successo}"
            )
        elif not os.path.exists(nome_file) and not os.path.exists(nome_backup):
            self.show_custom_info(
                "Rimozione Editor", 
                "L'editor scontrini e il suo backup non erano presenti."
            )
    except NameError:
        self.show_custom_warning(
            "Errore Configurazione", 
            "La costante NOME_EDITOR_LOCALE non è definita. Impossibile procedere."
        )
    except Exception as e:
        self.show_custom_warning("Errore Sconosciuto", f"Errore fatale: {e}")

# Forza Installazione Editor Scontrini
def _scarica_editor_esterno(self):
    url = GITHUB_SUPERMARKET
    filename = NOME_EDITOR_LOCALE
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        self.show_custom_info(
            "Download Editor", 
            f"Editor scaricato con successo come '{filename}'."
        )
    except requests.exceptions.RequestException as e:
        self.show_custom_warning(
            "Errore Download", 
            f"Impossibile scaricare l'editor. Errore: {e}"
        )

# Avvia Editor Scontrini
def _avvia_editor_esterno(self):
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    script_path = os.path.join(base_dir, "supermarket.pyw") 
    if not os.path.exists(script_path):
        self._scarica_editor_esterno()
        return
    try:
        if sys.platform.startswith('win'):
            comando = [sys.executable.replace('python.exe', 'pythonw.exe'), script_path]
        else:
            comando = [sys.executable, script_path]
        if hasattr(self, '_popup_spesa_active') and self._popup_spesa_active is not None and self._popup_spesa_active.winfo_exists():
            self._popup_spesa_active.destroy()
        root = self.winfo_toplevel() if hasattr(self, 'winfo_toplevel') else self
        proc = subprocess.Popen(comando, close_fds=True)
        root.iconify()
        def _ripristina():
            root.deiconify()
            root.lift()
            root.focus_force()
        def _attendi_chiusura():
            proc.wait()
            root.after(0, _ripristina)
        threading.Thread(target=_attendi_chiusura, daemon=True).start()
    except Exception as e:
        self.show_custom_warning(
            "Errore Esecuzione", 
            f"Impossibile avviare il tool ({comando[0]}). Errore: {e}"
        )
