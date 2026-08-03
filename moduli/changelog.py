#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog

# Visualizzazione Dettagliata dello Storico Modifiche (Changelog Manuale)
def visualizza_changelog(self):
    threading.Thread(target=self._visualizza_changelog_thread, daemon=True).start()

def _visualizza_changelog_thread(self):
    import __main__ as _app
    requests = _app.requests
    REPO_OWNER = _app.REPO_OWNER
    REPO_NAME = _app.REPO_NAME
    NOME_FILE = _app.NOME_FILE

    from datetime import datetime
    api_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/commits"
    percorsi = [NOME_FILE, "moduli"]
    changelog_text = ""
    try:
        commits_per_sha = {}
        for percorso in percorsi:
            params = {"path": percorso, "per_page": 20}
            response = requests.get(api_url, params=params, timeout=10)
            response.raise_for_status()
            for commit in response.json():
                commits_per_sha[commit["sha"]] = commit
        if not commits_per_sha:
            self.after(0, lambda: self.show_toast("Nessuno storico di commit trovato per questo file."))
            return
        commits = sorted(
            commits_per_sha.values(),
            key=lambda c: c["commit"]["committer"]["date"],
            reverse=True
        )[:30]
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
        self.after(0, lambda ct=changelog_text: self._mostra_popup_changelog(ct))
    except requests.exceptions.RequestException as e:
        self.after(0, lambda err=e: self.show_custom_warning("Errore Connessione",
                   f"Impossibile connettersi a GitHub:\n{err}"))
    except Exception as e:
        self.after(0, lambda err=e: self.show_custom_warning("Errore",
                   f"Errore generico durante la visualizzazione dello storico:\n{err}"))

def _mostra_popup_changelog(self, changelog_text):
    import __main__ as _app
    NOME_FILE = _app.NOME_FILE
    NAME = _app.NAME
    EXPORT_FILES = _app.EXPORT_FILES

    import os, tempfile, subprocess, platform
    win = tk.Toplevel(self, bg=self.COLOR_BACKGROUND)
    win.withdraw()
    win.title(f"Storico Modifiche: {NOME_FILE}")
    win.configure(bd=0)
    win.bind('<Escape>', lambda e: win.destroy())
    header = tk.Frame(win, bg=self.COLOR_BACKGROUND, height=42)
    header.pack(fill="x")
    header.pack_propagate(False)
    dot_canvas = tk.Canvas(header, width=10, height=10,
                           bg=self.COLOR_HEADER_BG, highlightthickness=0)
    dot_canvas.create_oval(0, 0, 10, 10, fill=self.COLOR_HIGHLIGHT, outline="")
    dot_canvas.pack(side="left", padx=(16, 8), pady=16)
    tk.Label(header, text="STORICO MODIFICHE",
             bg=self.COLOR_BACKGROUND, fg=self.COLOR_HEADER,
             font=("Segoe UI", 8, "bold")).pack(side="left")
    tk.Frame(win, bg=self.COLOR_BACKGROUND, height=1).pack(fill="x")
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
        height=20, width=80,
        font=("Consolas", 9),
        bg=self.COLOR_WHITE,
        fg=self.COLOR_BLACK,
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
    frame_bottoni = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    frame_bottoni.pack(pady=14)

    def salva():
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("File di testo", "*.txt")],
            initialfile=f"Changelog_{NAME}.txt",
            initialdir=EXPORT_FILES,
            title="Esporta risultati",
            confirmoverwrite=False,
            parent=win
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(changelog_text.strip())
                self.show_toast(f"Salvato in {os.path.basename(path)}", duration=2000)
            except Exception as e:
                self.show_custom_warning("Errore", f"Impossibile salvare:\n{e}")

    def stampa():
        try:
            tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt",
                                              delete=False, encoding="utf-8")
            tmp.write(changelog_text.strip())
            tmp.close()
            if platform.system() == "Windows":
                os.startfile(tmp.name, "print")
            elif platform.system() == "Darwin":
                subprocess.Popen(["lp", tmp.name])
            else:
                subprocess.Popen(["lp", tmp.name])
            self.show_toast("Inviato alla stampante", duration=2000)
        except Exception as e:
            self.show_custom_warning("Errore Stampa", f"Impossibile stampare:\n{e}")

    img_salva = self.icone_gui.get("salva")
    btn_salva = ttk.Label(
        frame_bottoni, compound="left", image=img_salva,
        text=" Salva" if img_salva else "Salva",
        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
        cursor="hand2", padding=(10, 5)
    )
    btn_salva.image = img_salva
    btn_salva.pack(side="left", padx=5)
    btn_salva.bind("<Button-1>", lambda e: salva())
    img_stampa = self.icone_gui.get("stampa")
    btn_stampa = ttk.Label(
        frame_bottoni, compound="left", image=img_stampa,
        text=" Stampa" if img_stampa else "Stampa",
        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
        cursor="hand2", padding=(10, 5)
    )
    btn_stampa.image = img_stampa
    btn_stampa.pack(side="left", padx=5)
    btn_stampa.bind("<Button-1>", lambda e: stampa())
    img_chiudi_win = self.icone_gui.get("chiudi")
    btn_chiudi_win = ttk.Label(
        frame_bottoni, compound="left", image=img_chiudi_win,
        text=" Chiudi" if img_chiudi_win else "Chiudi",
        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
        cursor="hand2", padding=(10, 5)
    )
    btn_chiudi_win.image = img_chiudi_win
    btn_chiudi_win.pack(side="left", padx=5)
    btn_chiudi_win.bind("<Button-1>", lambda e: win.destroy())
    win.update()
    min_w, min_h = 1000, 480
    w = max(win.winfo_reqwidth(), min_w)
    h = max(win.winfo_reqheight(), min_h)
    sx = self.winfo_screenwidth()
    sy = self.winfo_screenheight()
    h = min(h, sy - 80)
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    y = max(40, min(y, sy - h - 40))
    win.geometry(f"{w}x{h}+{x}+{y}")
    win.minsize(min_w, min_h)
    win.deiconify()
    win.transient(self)
    win.grab_set()
    win.focus_set()
    win.wait_window()
