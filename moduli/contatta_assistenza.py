#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import datetime
import platform
import smtplib
import webbrowser
import urllib.parse
import tkinter as tk
from tkinter import ttk, filedialog
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from __main__ import DB_DIR, VERSION, EMAIL_USER, APP_PASSWORD

# Compila Modulo Email per Assistenza
def apri_pannello_topic(self, topic):
    if hasattr(self, '_pannello_assistenza_popup') and self._pannello_assistenza_popup.winfo_exists():
        self._pannello_assistenza_popup.lift()
        self._pannello_assistenza_popup.focus_force()
        return
    popup = tk.Toplevel(self)
    self._pannello_assistenza_popup = popup
    popup.title("Contatta Assistenza")
    popup.withdraw()
    popup.update_idletasks()
    width, height = 1000, 630
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (width // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (height // 2)
    popup.geometry(f"{width}x{height}+{x}+{y}")
    popup.resizable(True, True)
    popup.minsize(width, height)
    popup.configure(bg=self.COLOR_BACKGROUND)
    popup.columnconfigure(0, weight=1)
    tk.Label(popup, text="Numero Licenza:", bg=self.COLOR_BACKGROUND, fg=self.COLOR_HEADER,
             font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", padx=15, pady=(15, 0))
    tk.Label(popup, text=topic, bg=self.COLOR_BACKGROUND, fg=self.COLOR_HIGHLIGHT,
             font=("Arial", 9, "italic")).grid(row=1, column=0, sticky="w", padx=15)
    tk.Label(popup, text="Tipo di problema:", bg=self.COLOR_BACKGROUND, fg=self.COLOR_HEADER,
             font=("Arial", 9, "bold")).grid(row=2, column=0, sticky="w", padx=15, pady=(10, 0))
    categoria_var = tk.StringVar(value="Seleziona...")
    combo_cat = ttk.Combobox(popup, textvariable=categoria_var, state="readonly", style="Border.TCombobox",
                              values=[
                                  "🐛 Bug / Errore applicazione",
                                  "💾 Problema salvataggio dati",
                                  "🌐 Problema WebServer",
                                  "📧 Problema Email / Notifiche",
                                  "📊 Problema Report / Grafici",
                                  "🔑 Problema Licenza",
                                  "💡 Suggerimento / Miglioramento",
                                  "❓ Altro"
                              ], width=25)
    combo_cat.grid(row=3, column=0, sticky="w", padx=15, pady=(2, 0))
    tk.Label(popup, text="Descrizione:", bg=self.COLOR_BACKGROUND, fg=self.COLOR_HEADER,
             font=("Arial", 9, "bold")).grid(row=4, column=0, sticky="nw", padx=15, pady=(10, 0))
    frame_txt = tk.Frame(popup, bg=self.COLOR_HIGHLIGHT, padx=1, pady=1)
    frame_txt.grid(row=5, column=0, sticky="nsew", padx=15, pady=(2, 0))
    frame_txt.columnconfigure(0, weight=1)
    frame_txt.rowconfigure(0, weight=1)
    popup.rowconfigure(5, weight=1)
    txt = tk.Text(frame_txt, font=("Arial", 9),
                  bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                  insertbackground=self.TEXT_COLOR, relief="flat",
                  highlightthickness=0)
    txt.grid(row=0, column=0, sticky="nsew")
    allegato_path = {"file": None}
    allegato_frame = tk.Frame(popup, bg=self.COLOR_BACKGROUND)
    allegato_frame.grid(row=6, column=0, sticky="ew", padx=15, pady=(8, 0))
    lbl_allegato = tk.Label(allegato_frame, text="📎 Nessun file allegato",
                             bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
                             font=("Arial", 8, "italic"))
    lbl_allegato.pack(side="left")

    def scegli_file():
        path = filedialog.askopenfilename(
            parent=popup,
            title="Seleziona file da allegare",
            filetypes=[
                ("Immagini", "*.png *.jpg *.jpeg *.bmp"),
                ("Log / Testo", "*.txt *.log"),
                ("Tutti i file", "*.*")
            ]
        )
        if path:
            allegato_path["file"] = path
            nome = os.path.basename(path)
            lbl_allegato.config(text=f"📎 {nome}", fg=self.COLOR_GREEN_SMOOTH)

    def rimuovi_file():
        allegato_path["file"] = None
        lbl_allegato.config(text="📎 Nessun file allegato", fg=self.TEXT_COLOR)

    ttk.Label(allegato_frame, text=" ", background=self.COLOR_BACKGROUND).pack(side="left")
    ttk.Label(allegato_frame, image=self.icone_gui.get("carica"), text=" Allega",
              compound="left", cursor="hand2", background=self.COLOR_BACKGROUND,
              foreground=self.COLOR_HEADER, font=("Arial", 8, "bold")
              ).pack(side="left", padx=(10, 2))
    allegato_frame.winfo_children()[-1].bind("<Button-1>", lambda e: scegli_file())
    ttk.Label(allegato_frame, image=self.icone_gui.get("cancella"), text=" Rimuovi",
              compound="left", cursor="hand2", background=self.COLOR_BACKGROUND,
              foreground=self.COLOR_RED_SMOOTH, font=("Arial", 8, "bold")
              ).pack(side="left", padx=2)
    allegato_frame.winfo_children()[-1].bind("<Button-1>", lambda e: rimuovi_file())
    includi_info_var = tk.BooleanVar(value=True)
    tk.Checkbutton(popup, text="Includi info sistema (OS, versione Python)",
                   variable=includi_info_var,
                   bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
                   selectcolor=self.COLOR_WIDGET_BG,
                   activebackground=self.COLOR_BACKGROUND,
                   activeforeground=self.TEXT_COLOR,
                   highlightthickness=0,
                   highlightbackground=self.COLOR_BACKGROUND,
                   highlightcolor=self.COLOR_BACKGROUND,
                   font=("Arial", 8), relief="flat", borderwidth=0
                   ).grid(row=7, column=0, sticky="w", padx=15, pady=(6, 0))
    log_path = os.path.join(DB_DIR, "error_log.txt")
    log_exists = os.path.exists(log_path) and os.path.getsize(log_path) > 0
    allega_log_var = tk.BooleanVar(value=False)
    tk.Checkbutton(popup, text="Allega Registro Anomalie",
                   variable=allega_log_var,
                   bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
                   selectcolor=self.COLOR_WIDGET_BG,
                   activebackground=self.COLOR_BACKGROUND,
                   activeforeground=self.TEXT_COLOR,
                   highlightthickness=0,
                   highlightbackground=self.COLOR_BACKGROUND,
                   highlightcolor=self.COLOR_BACKGROUND,
                   font=("Arial", 8), relief="flat", borderwidth=0,
                   state="normal" if log_exists else "disabled"
                   ).grid(row=8, column=0, sticky="w", padx=15, pady=(2, 0))
    if not log_exists:
        tk.Label(popup, text="  (nessun registro disponibile)", bg=self.COLOR_BACKGROUND,
                 fg=self.TEXT_COLOR, font=("Arial", 7, "italic")).grid(row=9, column=0, sticky="w", padx=15)
    btns_frame = tk.Frame(popup, bg=self.COLOR_BACKGROUND)
    btns_frame.grid(row=10, column=0, sticky="ew", padx=20, pady=12)
    btns_frame.columnconfigure(0, weight=1)
    btns_frame.columnconfigure(1, weight=1)

    def invia():
        testo = txt.get("1.0", "end").strip()
        categoria = categoria_var.get()
        if categoria == "Seleziona...":
            self.show_toast("Seleziona il tipo di problema.", duration=2000)
            return
        if not testo:
            self.show_toast("Scrivi una descrizione prima di inviare.", duration=2000)
            return
        corpo = (
            f"Numero di registrazione: {topic}\n"
            f"Categoria: {categoria}\n\n"
            f"Descrizione:\n{testo}\n"
        )
        if includi_info_var.get():
            corpo += (
                f"\n--- Info Sistema ---\n"
                f"C.F. Pro: v{VERSION}\n"
                f"OS: {platform.system()} {platform.release()} ({platform.version()})\n"
                f"Architettura: {platform.architecture()[0]}\n"
                f"Machine: {platform.machine()}\n"
                f"Hostname: {platform.node()}\n"
                f"Python: {platform.python_version()}\n"
            )
        if allegato_path["file"]:
            corpo += f"\nFile allegato: {os.path.basename(allegato_path['file'])}\n"
        if allega_log_var.get() and log_exists:
            corpo += f"Registro anomalie: allegato\n"
        b1.unbind("<Button-1>")
        b1.config(text=" Invio in corso...")

        def _al_termine(ok):
            if not popup.winfo_exists():
                return
            if ok:
                popup.destroy()
            else:
                b1.config(text=" Invia")
                b1.bind("<Button-1>", lambda e: invia())

        self.invia_email_assistenza(
            titolo=f"[{categoria}] Assistenza O.C. - Licenza {topic}",
            messaggio=corpo,
            allegato=allegato_path["file"],
            allegati_extra=[log_path] if allega_log_var.get() and log_exists else None,
            on_done=_al_termine
        )

    b1 = ttk.Label(btns_frame, image=self.icone_gui.get("qr_code"), text=" Invia",
                    compound="left", cursor="hand2", background=self.COLOR_BACKGROUND,
                    foreground=self.COLOR_HEADER, font=("Arial", 10, "bold"), anchor="center")
    b1.image = self.icone_gui.get("qr_code")
    b1.grid(row=0, column=0, padx=5, sticky="nsew")
    b1.bind("<Button-1>", lambda e: invia())
    b2 = ttk.Label(btns_frame, image=self.icone_gui.get("chiudi"), text=" Annulla",
                    compound="left", cursor="hand2", background=self.COLOR_BACKGROUND,
                    foreground=self.COLOR_HEADER, font=("Arial", 10, "bold"), anchor="center")
    b2.image = self.icone_gui.get("chiudi")
    b2.grid(row=0, column=1, padx=5, sticky="nsew")
    b2.bind("<Button-1>", lambda e: popup.destroy())
    popup.bind("<Escape>", lambda e: popup.destroy())
    popup.deiconify()

# Invia Modulo Email per Assistenza
def invia_email_assistenza(self, titolo, messaggio, allegato=None, allegati_extra=None, on_done=None):
    if not EMAIL_USER or not APP_PASSWORD:
        corpo_mailto = messaggio
        if allegato or allegati_extra:
            corpo_mailto += "\n\n(Allega manualmente i file: il client email non li include automaticamente da questo link.)"
        url = "mailto:helporbitacasa@gmail.com?subject=" + urllib.parse.quote(titolo) + "&body=" + urllib.parse.quote(corpo_mailto)
        webbrowser.open(url)
        self.show_toast("Email non configurata: apro il tuo client di posta predefinito.", duration=3000)
        if on_done:
            on_done(True)
        return

    def _invia_in_background():
        ok = False
        try:
            msg = MIMEMultipart("mixed")
            msg["Subject"] = titolo
            msg["From"] = EMAIL_USER
            msg["To"] = "helporbitacasa@gmail.com"
            alt_part = MIMEMultipart("alternative")
            alt_part.attach(MIMEText(messaggio, "plain"))
            alt_part.attach(MIMEText(f"<html><body><pre>{messaggio}</pre></body></html>", "html"))
            msg.attach(alt_part)
            tutti_allegati = []
            if allegato and os.path.exists(allegato):
                tutti_allegati.append(allegato)
            if allegati_extra:
                for a in allegati_extra:
                    if a and os.path.exists(a):
                        tutti_allegati.append(a)
            for path in tutti_allegati:
                with open(path, "rb") as f:
                    parte = MIMEBase("application", "octet-stream")
                    parte.set_payload(f.read())
                encoders.encode_base64(parte)
                parte.add_header("Content-Disposition", f"attachment; filename={os.path.basename(path)}")
                msg.attach(parte)
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(EMAIL_USER, APP_PASSWORD)
                server.sendmail(EMAIL_USER, "helporbitacasa@gmail.com", msg.as_string())
            ok = True
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ASSISTENZA INVIATA → helporbitacasa@gmail.com")
        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore invio assistenza: {e}")

        def _fine():
            if ok:
                self.show_toast("Richiesta assistenza inviata!", duration=2000)
            else:
                self.show_toast("Errore invio: controlla connessione e credenziali.", duration=3000)
            if on_done:
                on_done(ok)
        self.after(0, _fine)

    import threading
    threading.Thread(target=_invia_in_background, daemon=True).start()
