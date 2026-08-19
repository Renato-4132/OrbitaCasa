#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import os
import tkinter as tk
from tkinter import ttk

from __main__ import DB_DIR, NAME, USA_SSL, PORTA, requests, segno, Image, ImageTk

def mostra_qr_popup_label(self):
    import webbrowser
    cert_file = os.path.join(DB_DIR, "cert.pem")
    key_file = os.path.join(DB_DIR, "key.pem")
    prot = "https" if USA_SSL and os.path.exists(cert_file) and os.path.exists(key_file) else "http"
    ip_locale = self.get_ip_locale_reale()
    try:
        r = requests.get('https://api.myip.com', timeout=2).json()
        ip_remoto = r.get('ip', "N/A")
    except:
        ip_remoto = "N/A"
    dominio = self.get_dominio_ssl() if USA_SSL else ""
    if USA_SSL and dominio:
        url_locale = f"https://{ip_locale}:{PORTA}"
        url_remoto = f"https://{dominio}:{PORTA}"
    else:
        url_locale = f"{prot}://{ip_locale}:{PORTA}"
        url_remoto = f"{prot}://{ip_remoto}:{PORTA}"
    top = tk.Toplevel(self)
    top.transient(self)
    top.title("Gestione Accessi Remoti")
    top.withdraw()
    window_width = 900
    window_height = 620
    app_x = self.winfo_rootx()
    app_y = self.winfo_rooty()
    app_width = self.winfo_width()
    app_height = self.winfo_height()
    center_x = app_x + (app_width // 2) - (window_width // 2)
    center_y = app_y + (app_height // 2) - (window_height // 2)
    top.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    colore_web = "#007ACC" 
    top.configure(bg=self.COLOR_WIDGET_BG)
    top.attributes("-topmost", True)
    top.resizable(False, False)
    def apri_url(url):
        webbrowser.open_new_tab(url)
    def gen_qr(u):
        q = segno.make(u, error='L', version=4)
        b = io.BytesIO()
        q.save(b, kind='png', scale=5, dark="black", light="white")
        b.seek(0)
        return ImageTk.PhotoImage(Image.open(b))
    try:
        main = tk.Frame(top, bg=self.COLOR_WIDGET_BG)
        main.pack(expand=True, fill="both", padx=20, pady=10)
        lbl_titolo = ttk.Label(main, text="Gestione Accessi Remoti", style="White.TLabel")
        lbl_titolo.configure(font=("Arial", 22, "bold")) 
        lbl_titolo.pack(pady=(10, 0))
        ttk.Label(main, text="Inquadra il QR Code con un altro smartphone o tablet per connetterti al sistema", style="WhiteSmall.TLabel").pack(pady=(0, 20))
        card = tk.Frame(main, bg=self.COLOR_WIDGET_BG)
        card.pack(expand=True)
        col_l = tk.Frame(card, bg=self.COLOR_WIDGET_BG)
        col_l.pack(side="left", padx=40)
        ttk.Label(col_l, text="Connessione Locale", font=("Arial", 14, "bold"), style="White.TLabel").pack()
        ttk.Label(col_l, text="(Stesso Wi-Fi / LAN)", style="WhiteSmall.TLabel").pack(pady=(0, 5))
        img_l = gen_qr(url_locale)
        lbl_img_l = tk.Label(col_l, image=img_l, bg=self.COLOR_WIDGET_BG) 
        lbl_img_l.image = img_l
        lbl_img_l.pack(pady=10)
        lbl_url_l = tk.Label(col_l, text=url_locale, font=("Arial", 11, "bold", "underline"), 
                                         bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR, cursor="hand2")
        lbl_url_l.pack()
        lbl_url_l.bind("<Button-1>", lambda e: apri_url(url_locale))
        tk.Frame(card, width=1, bg=self.COLOR_HEADER_BG).pack(side="left", fill="y", padx=10, pady=10)
        col_r = tk.Frame(card, bg=self.COLOR_WIDGET_BG)
        col_r.pack(side="left", padx=40)
        lbl_web_t = ttk.Label(col_r, text="Connessione Web", font=("Arial", 14, "bold"), style="White.TLabel")
        lbl_web_t.configure(foreground=colore_web)
        lbl_web_t.pack()
        lbl_web_sub = ttk.Label(col_r, text="(Accesso Remoto)", style="WhiteSmall.TLabel")
        lbl_web_sub.configure(foreground=colore_web)
        lbl_web_sub.pack(pady=(0, 5))
        img_r = gen_qr(url_remoto)
        lbl_img_r = tk.Label(col_r, image=img_r, bg=self.COLOR_WIDGET_BG)
        lbl_img_r.image = img_r
        lbl_img_r.pack(pady=10)
        lbl_url_r = tk.Label(col_r, text=url_remoto, font=("Arial", 11, "bold", "underline"), 
                                         bg=self.COLOR_WIDGET_BG, fg=colore_web, cursor="hand2")
        lbl_url_r.pack()
        lbl_url_r.bind("<Button-1>", lambda e: apri_url(url_remoto))
        protocollo_attivo = "HTTPS (Cifrato)" if prot == "https" else "HTTP (Non cifrato)"

        footer_text = (
              f"STATO CONNESSIONE: Il server opera attualmente su protocollo {protocollo_attivo}.\n"
              f"{NAME} predilige connessioni HTTPS per garantire la massima riservatezza dei dati nella LAN.\n"
              "⚠️ NOTA SUL CERTIFICATO: Essendo un certificato autogenerato, il browser mostrerà un avviso di sicurezza.\n"
              "Puoi procedere con fiducia (clicca 'Avanzate'): la connessione è cifrata e sicura al 100%.\n"
              "SICUREZZA WAN: Per accessi remoti, si raccomanda l'uso di una VPN per un tunnel end-to-end protetto."
          )
        lbl_footer = ttk.Label(main, text=footer_text, style="WhiteSmall.TLabel", justify="center")
        lbl_footer.pack(pady=20)
        btn_chiudi_qr = ttk.Label(
            main, 
            image=self.icone_gui.get("chiudi"), 
            text=" Chiudi", 
            compound="left",
            cursor="hand2", 
            background=self.COLOR_WIDGET_BG,
            font=("Arial", 9, "bold")
        )
        btn_chiudi_qr.image = self.icone_gui.get("chiudi")
        btn_chiudi_qr.pack(pady=(0, 10))
        btn_chiudi_qr.bind("<Button-1>", lambda e: top.destroy())
        top.deiconify()
        top.update_idletasks()
        top.attributes("-topmost", False)
        top.grab_set()
        top.bind("<Escape>", lambda e: top.destroy())
    except Exception as e:
        print(f"Errore UI: {e}")
        top.bind("<Escape>", lambda e: top.destroy())
        top.deiconify()
        top.attributes("-topmost", False)
        if hasattr(self, "show_custom_warning"):
            self.show_custom_warning("Errore", f"Impossibile completare la finestra QR: {e}")
