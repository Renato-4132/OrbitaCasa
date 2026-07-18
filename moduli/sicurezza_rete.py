#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import socket
import hashlib
import shutil
import tempfile
import datetime
import tkinter as tk
from tkinter import ttk, filedialog

import requests
import fitz

# Cambio Password Manuale
def apri_cambio_password(self):
    import __main__ as _app
    PW_FILE = _app.PW_FILE
    NAME = _app.NAME
    VERSION = _app.VERSION
    def hash_pw(pw):
        return hashlib.sha256(pw.encode()).hexdigest()
    def salva_hash(pw):
        with open(PW_FILE, "w") as f:
            json.dump({"hash": hash_pw(pw)}, f)
    def leggi_hash():
        if not os.path.exists(PW_FILE): return None
        try:
            with open(PW_FILE) as f:
                return json.load(f).get("hash")
        except: return None
    def crea_campo_password_moderno(parent, etichetta=""):
        if etichetta:
            tk.Label(parent, text=etichetta, bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
                     font=("Arial", 9, "bold")).pack(pady=(10, 2), anchor="w", padx=40)
        frame_border = tk.Frame(parent, bg=self.COLOR_HIGHLIGHT, bd=0)
        frame_border.pack(pady=5, padx=40, fill="x")
        frame_container = tk.Frame(frame_border, bg=self.COLOR_WIDGET_BG, bd=0)
        frame_container.pack(padx=1, pady=1, fill="both", expand=True)
        visibile = tk.BooleanVar(value=False)
        entry_pw = tk.Entry(frame_container, show="*", bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                            insertbackground=self.TEXT_COLOR, font=("Arial", 11),
                            relief="flat", bd=0, highlightthickness=0)
        entry_pw.pack(side="left", padx=10, pady=6, fill="x", expand=True)
        def toggle_visibilita():
            img_aperto = self.icone_gui.get("occhio")
            img_chiuso = self.icone_gui.get("occhio_chiuso")
            if visibile.get():
                entry_pw.config(show="*")
                lbl_occhio.config(image=img_aperto, text="") if img_aperto else lbl_occhio.config(text="👁️", fg=self.TEXT_COLOR)
            else:
                entry_pw.config(show="")
                lbl_occhio.config(image=img_chiuso, text="") if img_chiuso else lbl_occhio.config(text="🔒", fg=self.COLOR_HIGHLIGHT)
            visibile.set(not visibile.get())
        lbl_occhio = tk.Label(frame_container, font=("Arial", 12), bg=self.COLOR_WIDGET_BG,
                              fg=self.TEXT_COLOR, cursor="hand2")
        img_init = self.icone_gui.get("occhio")
        if img_init:
            lbl_occhio.config(image=img_init)
            lbl_occhio.image = img_init
        else:
            lbl_occhio.config(text="👁️")
        lbl_occhio.pack(side="right", padx=10)
        lbl_occhio.bind("<Button-1>", lambda e: toggle_visibilita())
        entry_pw.bind("<FocusIn>", lambda e: frame_border.config(bg=self.COLOR_HIGHLIGHT))
        entry_pw.bind("<FocusOut>", lambda e: frame_border.config(bg=self.COLOR_WIDGET_BG))
        return entry_pw
    win = tk.Toplevel(self)
    win.transient(self)
    win.title(f"Password - {NAME} v.{VERSION}")
    win.configure(bg=self.COLOR_BACKGROUND)
    win.resizable(False, False)
    w_win, h_win = 350, 380
    x_win = self.winfo_screenwidth() // 2 - w_win // 2
    y_win = self.winfo_screenheight() // 2 - h_win // 2
    win.geometry(f"{w_win}x{h_win}+{x_win}+{y_win}")
    win.protocol("WM_DELETE_WINDOW", win.destroy)
    win.wait_visibility()
    win.grab_set()
    tk.Label(win, text="🔄", font=("Arial", 20), bg=self.COLOR_BACKGROUND, fg=self.COLOR_HIGHLIGHT).pack(pady=(2, 0))
    tk.Label(win, text="CAMBIO PASSWORD", font=("Arial", 10, "bold"), bg=self.COLOR_BACKGROUND, fg=self.COLOR_RED_SMOOTH).pack(pady=(0, 2))
    mess = tk.Label(win, text="", fg=self.COLOR_RED_SMOOTH, bg=self.COLOR_BACKGROUND, font=("Arial", 9))
    entry_attuale  = crea_campo_password_moderno(win, "Password Vecchia")
    entry_nuova    = crea_campo_password_moderno(win, "Nuova Password (vuota per disattivare.)")
    entry_conferma = crea_campo_password_moderno(win, "Conferma Nuova")
    win.update_idletasks()
    win.after(200, lambda: entry_attuale.focus_force())
    mess.pack(pady=0)
    def esegui_conferma_cambio(event=None):
        attuale  = entry_attuale.get()
        nuova    = entry_nuova.get()
        conferma = entry_conferma.get()
        if hash_pw(attuale) != leggi_hash():
            mess.config(text="Password attuale errata!", fg=self.COLOR_RED_SMOOTH)
            entry_attuale.delete(0, tk.END)
            entry_nuova.delete(0, tk.END)
            entry_conferma.delete(0, tk.END)
            entry_attuale.focus_set()
            return
        if not nuova:
            salva_hash("")
            def lampeggia(n=6):
                if n <= 0:
                    win.destroy()
                    return
                attuale_txt = mess.cget("text")
                mess.config(text="" if attuale_txt else "Protezione Password disattivata!", fg=self.COLOR_GREEN)
                win.after(300, lambda: lampeggia(n-1))
            lampeggia()
            return
        if nuova != conferma:
            mess.config(text="Le password non corrispondono!", fg=self.COLOR_RED_SMOOTH)
            entry_attuale.delete(0, tk.END)
            entry_nuova.delete(0, tk.END)
            entry_conferma.delete(0, tk.END)
            entry_attuale.focus_set()
            return
        salva_hash(nuova)
        mess.config(text="Password Aggiornata!", fg=self.COLOR_GREEN_SMOOTH)
        win.after(1200, win.destroy)
    for entry in [entry_attuale, entry_nuova, entry_conferma]:
        entry.bind("<Return>", esegui_conferma_cambio)
        entry.bind("<KP_Enter>", esegui_conferma_cambio)
    frame_btn = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    frame_btn.pack(pady=(10, 0), fill="x", padx=40)
    img_annulla_pw = self.icone_gui.get("chiudi")
    btn_annulla = tk.Label(frame_btn, compound="left", image=img_annulla_pw,
            text=" ANNULLA" if img_annulla_pw else "ANNULLA",
            bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
            font=("Arial", 9, "bold"), cursor="hand2", padx=15, pady=8)
    btn_annulla.pack(side="left", expand=True)
    btn_annulla.bind("<Button-1>", lambda e: win.destroy())
    img_conferma_pw = self.icone_gui.get("api_key")
    btn_conferma = tk.Label(frame_btn, compound="left", image=img_conferma_pw,
            text=" CONFERMA" if img_conferma_pw else "CONFERMA",
            bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
            font=("Arial", 9, "bold"), cursor="hand2", padx=15, pady=8)
    btn_conferma.pack(side="right", expand=True)
    btn_conferma.bind("<Button-1>", lambda e: esegui_conferma_cambio())

# Download del manuale CertBot SSL (PDF remoto)
def scarica_manuale_ssl(self):
    import __main__ as _app
    URL_PDF_SSL = _app.URL_PDF_SSL
    try:
        response = requests.get(URL_PDF_SSL, timeout=15)
        response.raise_for_status()
        temp_path = os.path.join(tempfile.gettempdir(), "manuale_ssl.pdf")
        with open(temp_path, "wb") as f:
            f.write(response.content)
        self._apri_viewer_ssl(temp_path)
    except Exception as e:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore nel download del manuale SSL:", e)
        self.show_custom_warning("Attenzione", "Download NON completato!\n\nSembra ci sia stato un problema. 😕")

# Viewer PDF interno per il manuale CertBot SSL (indice, zoom, stampa, salvataggio)
def _apri_viewer_ssl(self, temp_path):
    import __main__ as _app
    NAME = _app.NAME
    EXPORT_FILES = _app.EXPORT_FILES
    doc = fitz.open(temp_path)
    pagina_corrente = [0]
    zoom_level = [1.5]
    toc = doc.get_toc()
    win = tk.Toplevel(self, bg=self.COLOR_BACKGROUND)
    win.title(f"Manuale CertBot SSL — {NAME}")
    win.configure(bd=0)
    win.bind('<Escape>', lambda e: win.destroy())
    header = tk.Frame(win, bg=self.COLOR_HEADER_BG, height=42)
    header.pack(fill="x")
    header.pack_propagate(False)
    dot_canvas = tk.Canvas(header, width=10, height=10,
                           bg=self.COLOR_HEADER_BG, highlightthickness=0)
    dot_canvas.create_oval(0, 0, 10, 10, fill=self.COLOR_HIGHLIGHT, outline="")
    dot_canvas.pack(side="left", padx=(16, 8), pady=16)
    tk.Label(header, text="Manuale CertBot SSL",
             bg=self.COLOR_HEADER_BG, fg=self.COLOR_HEADER,
             font=("Segoe UI", 8, "bold")).pack(side="left")
    tk.Frame(win, bg=self.COLOR_BACKGROUND, height=1).pack(fill="x")
    frame_corpo = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    frame_corpo.pack(padx=16, pady=(12, 0), fill='both', expand=True)
    if toc:
        frame_indice = tk.Frame(frame_corpo, bg=self.COLOR_WIDGET_BG,
                                highlightbackground=self.COLOR_HEADER_BG,
                                highlightthickness=1)
        frame_indice.pack(side="left", fill="y", padx=(0, 8))

        tk.Label(frame_indice, text="Indice",
                 bg=self.COLOR_HEADER_BG, fg=self.COLOR_HEADER,
                 font=("Segoe UI", 8, "bold"),
                 padx=8, pady=6).pack(fill="x")
        sb_indice = ttk.Scrollbar(frame_indice, style="Vertical.TScrollbar")
        sb_indice.pack(side="right", fill="y")
        listbox = tk.Listbox(frame_indice,
                             yscrollcommand=sb_indice.set,
                             bg=self.COLOR_WIDGET_BG,
                             fg=self.TEXT_COLOR,
                             selectbackground=self.COLOR_HIGHLIGHT,
                             selectforeground=self.COLOR_WHITE,
                             font=("Segoe UI", 8),
                             relief="flat", bd=0,
                             activestyle="none",
                             width=60,
                             highlightthickness=0)
        listbox.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)
        sb_indice.config(command=listbox.yview)
        toc_pagine = []
        for livello, titolo, pagina in toc:
            indent = "  " * (livello - 1)
            listbox.insert(tk.END, f"{indent}{titolo}")
            toc_pagine.append(pagina - 1)
        def vai_a_voce(event):
            sel = listbox.curselection()
            if sel:
                pagina_corrente[0] = max(0, min(toc_pagine[sel[0]], len(doc) - 1))
                render_pagina()

        listbox.bind("<<ListboxSelect>>", vai_a_voce)
    frame_pdf = tk.Frame(frame_corpo, bg=self.COLOR_WIDGET_BG,
                         highlightbackground=self.COLOR_HEADER_BG,
                         highlightthickness=1)
    frame_pdf.pack(side="left", fill='both', expand=True)
    scrollbar_y = ttk.Scrollbar(frame_pdf, style="Vertical.TScrollbar")
    scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
    scrollbar_x = ttk.Scrollbar(frame_pdf, orient="horizontal")
    scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
    canvas_pdf = tk.Canvas(frame_pdf,
                           bg=self.COLOR_WIDGET_BG,
                           yscrollcommand=scrollbar_y.set,
                           xscrollcommand=scrollbar_x.set,
                           highlightthickness=0)
    canvas_pdf.pack(side=tk.LEFT, fill='both', expand=True)
    scrollbar_y.config(command=canvas_pdf.yview)
    scrollbar_x.config(command=canvas_pdf.xview)
    tk.Frame(win, bg=self.COLOR_BACKGROUND, height=1).pack(fill="x", pady=(10, 0))
    frame_ctrl = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    frame_ctrl.pack(pady=10)
    img_prev = self.icone_gui.get("indietro")
    btn_prev = ttk.Label(frame_ctrl, compound="left", image=img_prev,
                         text=" Indietro" if img_prev else "◀ Indietro",
                         background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                         cursor="hand2", padding=(10, 5))
    btn_prev.image = img_prev
    btn_prev.pack(side="left", padx=5)
    lbl_pagina = tk.Label(frame_ctrl,
                          text=f"Pagina 1 / {len(doc)}",
                          bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
                          font=("Segoe UI", 9))
    lbl_pagina.pack(side="left", padx=12)
    img_next = self.icone_gui.get("avanti")
    btn_next = ttk.Label(frame_ctrl, compound="left", image=img_next,
                         text=" Avanti" if img_next else "Avanti ▶",
                         background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                         cursor="hand2", padding=(10, 5))
    btn_next.image = img_next
    btn_next.pack(side="left", padx=5)
    tk.Frame(frame_ctrl, bg=self.COLOR_BACKGROUND, width=20).pack(side="left")
    btn_zoom_out = ttk.Label(frame_ctrl, text="  −  ",
                             background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                             cursor="hand2", padding=(8, 5), font=("Segoe UI", 11, "bold"))
    btn_zoom_out.pack(side="left", padx=2)
    lbl_zoom = tk.Label(frame_ctrl, text="150%",
                        bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
                        font=("Segoe UI", 9), width=5)
    lbl_zoom.pack(side="left")
    btn_zoom_in = ttk.Label(frame_ctrl, text="  +  ",
                            background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                            cursor="hand2", padding=(8, 5), font=("Segoe UI", 11, "bold"))
    btn_zoom_in.pack(side="left", padx=2)
    tk.Frame(frame_ctrl, bg=self.COLOR_BACKGROUND, width=20).pack(side="left")
    img_stampa = self.icone_gui.get("stampa")
    btn_stampa = ttk.Label(frame_ctrl, compound="left", image=img_stampa,
                           text=" Stampa" if img_stampa else "Stampa",
                           background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                           cursor="hand2", padding=(10, 5))
    btn_stampa.image = img_stampa
    btn_stampa.pack(side="left", padx=5)
    img_salva = self.icone_gui.get("salva")
    btn_salva = ttk.Label(frame_ctrl, compound="left", image=img_salva,
                          text=" Salva" if img_salva else "Salva",
                          background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                          cursor="hand2", padding=(10, 5))
    btn_salva.image = img_salva
    btn_salva.pack(side="left", padx=5)
    tk.Frame(frame_ctrl, bg=self.COLOR_BACKGROUND, width=20).pack(side="left")
    img_chiudi = self.icone_gui.get("chiudi")
    btn_chiudi = ttk.Label(frame_ctrl, compound="left", image=img_chiudi,
                           text=" Chiudi" if img_chiudi else "Chiudi",
                           background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                           cursor="hand2", padding=(10, 5))
    btn_chiudi.image = img_chiudi
    btn_chiudi.pack(side="left", padx=5)
    img_ref = [None]
    def render_pagina():
        page = doc[pagina_corrente[0]]
        mat = fitz.Matrix(zoom_level[0], zoom_level[0])
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("ppm")
        img = tk.PhotoImage(data=img_data)
        img_ref[0] = img
        canvas_pdf.delete("all")
        canvas_pdf.create_image(0, 0, anchor="nw", image=img)
        canvas_pdf.config(scrollregion=(0, 0, pix.width, pix.height))
        canvas_pdf.yview_moveto(0)
        lbl_pagina.config(text=f"Pagina {pagina_corrente[0] + 1} / {len(doc)}")
        lbl_zoom.config(text=f"{int(zoom_level[0] * 100)}%")
        if toc:
            pagina_att = pagina_corrente[0]
            voce_attiva = 0
            for i, p in enumerate(toc_pagine):
                if p <= pagina_att:
                    voce_attiva = i
            listbox.selection_clear(0, tk.END)
            listbox.selection_set(voce_attiva)
            listbox.see(voce_attiva)
    def vai_prev():
        if pagina_corrente[0] > 0:
            pagina_corrente[0] -= 1
            render_pagina()
    def vai_next():
        if pagina_corrente[0] < len(doc) - 1:
            pagina_corrente[0] += 1
            render_pagina()
    def zoom_in():
        if zoom_level[0] < 3.0:
            zoom_level[0] = round(zoom_level[0] + 0.25, 2)
            render_pagina()
    def zoom_out():
        if zoom_level[0] > 0.5:
            zoom_level[0] = round(zoom_level[0] - 0.25, 2)
            render_pagina()
    def stampa():
        import subprocess, os
        if os.name == 'nt':
            os.startfile(temp_path, "print")
        else:
            subprocess.run(["lp", temp_path])
    def salva():
        from tkinter import filedialog
        dest = filedialog.asksaveasfilename(
            parent=win,
            title="Salva Manuale",
            confirmoverwrite=False,
            initialdir=EXPORT_FILES,
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="Manuale_CertBot_SSL.pdf"
        )
        if dest:
            import shutil
            try:
                shutil.copy2(temp_path, dest)
                self.show_custom_info("Salvataggio", f"✅ Manuale salvato in:\n{dest}")
            except Exception as e:
                self.show_custom_warning("Errore", f"❌ Salvataggio fallito:\n{e}")
    btn_stampa.bind("<Button-1>", lambda e: stampa())
    btn_salva.bind("<Button-1>", lambda e: salva())
    btn_prev.bind("<Button-1>", lambda e: vai_prev())
    btn_next.bind("<Button-1>", lambda e: vai_next())
    btn_zoom_in.bind("<Button-1>", lambda e: zoom_in())
    btn_zoom_out.bind("<Button-1>", lambda e: zoom_out())
    btn_chiudi.bind("<Button-1>", lambda e: win.destroy())
    win.bind("<Left>", lambda e: vai_prev())
    win.bind("<Right>", lambda e: vai_next())
    canvas_pdf.bind("<MouseWheel>", lambda e: canvas_pdf.yview_scroll(int(-1*(e.delta/120)), "units"))
    canvas_pdf.bind("<Button-4>", lambda e: canvas_pdf.yview_scroll(-1, "units"))
    canvas_pdf.bind("<Button-5>", lambda e: canvas_pdf.yview_scroll(1, "units"))
    win.withdraw()
    win.update_idletasks()
    min_w, min_h = 1300, 650
    w = max(win.winfo_width(), min_w)
    h = max(win.winfo_height(), min_h)
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")
    win.resizable(True, True)
    win.minsize(min_w, min_h)
    win.deiconify()
    win.attributes('-topmost', True)
    win.update_idletasks()
    win.attributes('-topmost', False)
    win.transient(self)
    win.grab_set()
    win.focus_force()
    render_pagina()
    win.wait_window()
    doc.close()
    try:
        os.remove(temp_path)
    except Exception:
        pass

# Thread watchdog: verifica periodicamente che il webserver risponda su /ping, forza riavvio se non risponde
def start_watchdog_server(self):
    import __main__ as _app
    USA_SSL = _app.USA_SSL
    PORTA = _app.PORTA
    import urllib.request, ssl as ssl_mod
    time.sleep(15)
    consecutive_failures = 0
    while getattr(self, "_server_running", True):
        try:
            proto = "https" if USA_SSL else "http"
            ctx   = ssl_mod._create_unverified_context() if USA_SSL else None
            urllib.request.urlopen(f"{proto}://localhost:{PORTA}/ping",
                           timeout=10, context=ctx)
            consecutive_failures = 0
        except Exception as e:
            if not getattr(self, "_server_running", True):
                break
            consecutive_failures += 1
            if consecutive_failures >= 3:
                consecutive_failures = 0
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Watchdog: server non risponde, forzo riavvio...")
                try:
                    if hasattr(self, "server") and self.server:
                        self.server.shutdown()
                except Exception:
                    pass
        time.sleep(30)

# Genera certificato SSL self-signed (cert.pem/key.pem) se non esiste già
def genera_certificati_auto(self):
    import __main__ as _app
    DB_DIR = _app.DB_DIR
    NAME = _app.NAME
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from datetime import datetime, timedelta, timezone
    cert_path = os.path.join(DB_DIR, "cert.pem")
    key_path = os.path.join(DB_DIR, "key.pem")
    if os.path.exists(cert_path) and os.path.exists(key_path):
        return True
    try:
        print(f"Generazione certificati SSL di sicurezza...")
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)            
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, f"{NAME} Local Server"),
        ])
        now = datetime.now(timezone.utc)
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            now
        ).not_valid_after(
            now + timedelta(days=3650)
        ).add_extension(
            x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
            critical=False,
        ).sign(key, hashes.SHA256())
        with open(key_path, "wb") as f:
            f.write(key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            ))
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))            
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Certificati generati con successo in DB_DIR.")
        return True
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Errore generazione certificati: {e}")
        return False

# Legge l'hash della password salvata su file
def leggi_hash(self):
    import __main__ as _app
    PW_FILE = _app.PW_FILE
    if not os.path.exists(PW_FILE):
        return None
    try:
        with open(PW_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("hash")
    except:
        return None


# Salva l'hash della password su file
def salva_hash(self, pw):
    import __main__ as _app
    PW_FILE = _app.PW_FILE
    import hashlib, json
    with open(PW_FILE, "w") as f:
        json.dump({"hash": hashlib.sha256(pw.encode()).hexdigest()}, f)

# Verifica la password inserita, gestendo contatore tentativi e ban temporaneo
def verifica_password(self, password):
    import __main__ as _app
    ACCESS_CONTROL_WEB = _app.ACCESS_CONTROL_WEB
    ora = time.time()
    data = {"web_user": {"count": 0, "ban_until": 0, "last_attempt": 0}}
    if os.path.exists(ACCESS_CONTROL_WEB):
        try:
            with open(ACCESS_CONTROL_WEB, "r") as f:
                data = json.load(f)
        except: pass
    user = data.get("web_user", {"count": 0, "ban_until": 0, "last_attempt": 0})
    if ora < user.get("ban_until", 0):
        return False
    salvato = self.leggi_hash()
    if salvato is None: return False
    inserito = hashlib.sha256(password.encode()).hexdigest()
    if salvato == inserito:
        user["count"] = 0
        user["ban_until"] = 0
        user["last_attempt"] = 0
        user["notificato"] = False
        data["web_user"] = user
        with open(ACCESS_CONTROL_WEB, "w") as f: json.dump(data, f)
        return True
    else:
        user["count"] += 1
        user["last_attempt"] = ora
        if user["count"] >= 3:
            user["ban_until"] = ora + 300
        data["web_user"] = user
        with open(ACCESS_CONTROL_WEB, "w") as f: json.dump(data, f)
        return False

# Html registra data accesso web
def registra_accesso(self, ip="sconosciuto", user_agent="sconosciuto"):
    import __main__ as _app
    LOGIN_WEB = _app.LOGIN_WEB
    from datetime import datetime
    nuovo_log = {
        "data_ora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "ip": ip,
        "browser": user_agent
    }
    logs = []
    if os.path.exists(LOGIN_WEB):
        try:
            with open(LOGIN_WEB, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except:
            logs = []
    logs.insert(0, nuovo_log)
    logs = logs[:10]
    with open(LOGIN_WEB, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=4)

def registra_accesso_fallito(self, ip="sconosciuto", pwd_tentata="", user_agent="sconosciuto"):
    import __main__ as _app
    LOGIN_WEB_FAIL = _app.LOGIN_WEB_FAIL
    ACCESS_CONTROL_WEB = _app.ACCESS_CONTROL_WEB
    from datetime import datetime
    nuovo_log = {
        "data_ora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "ip": ip,
        "pwd_tentata": pwd_tentata,
        "browser": user_agent
    }
    logs = []
    if os.path.exists(LOGIN_WEB_FAIL):
        try:
            with open(LOGIN_WEB_FAIL, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except:
            logs = []
    logs.insert(0, nuovo_log)
    logs = logs[:20]
    with open(LOGIN_WEB_FAIL, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=4)
    try:
        if os.path.exists(ACCESS_CONTROL_WEB):
            with open(ACCESS_CONTROL_WEB, "r") as f:
                data = json.load(f)
            web_user = data.get("web_user", {})
            count = web_user.get("count", 0)
            if count >= 3 and not web_user.get("notificato", False):
                self.invia_notifica_fallimento(ip=ip, pwd_tentata=pwd_tentata, user_agent=user_agent)
                web_user["notificato"] = True
                data["web_user"] = web_user
                with open(ACCESS_CONTROL_WEB, "w") as f:
                    json.dump(data, f)
    except:
        pass

def invia_notifica_fallimento(self, ip="sconosciuto", pwd_tentata="", user_agent="sconosciuto"):
    import __main__ as _app
    MANDA_MAIL_FAIL = _app.MANDA_MAIL_FAIL
    EMAIL_USER = _app.EMAIL_USER
    APP_PASSWORD = _app.APP_PASSWORD
    from datetime import datetime
    if not MANDA_MAIL_FAIL:
        return
    try:
        if not EMAIL_USER or not APP_PASSWORD:
            return
        ora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        oggetto = "🚫 Accesso Bloccato - OrbitaCasa Web"
        corpo = (
            f"Dopo 3 tentativi falliti l'accesso è stato bloccato per 5 minuti.\n\n"
            f"🕐 Data/Ora: {ora}\n"
            f"🌐 IP: {ip}\n"
            f"🔑 Password tentata: {pwd_tentata or '—'}\n"
            f"🖥️ Browser: {user_agent}\n\n"
            f"Se non riconosci questo accesso, verifica la sicurezza del tuo pannello web."
        )
        import smtplib
        from email.mime.text import MIMEText
        msg = MIMEText(corpo, "plain", "utf-8")
        msg["Subject"] = oggetto
        msg["From"] = EMAIL_USER
        msg["To"] = EMAIL_USER
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, APP_PASSWORD)
            server.sendmail(EMAIL_USER, EMAIL_USER, msg.as_string())
    except Exception as ex:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [NOTIFICA FAIL] Errore invio mail: {ex}")

# INFO IP: Recupera l'indirizzo IP privato (192.168.x.x)
def get_ip_locale_reale(self):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

# Estrae il dominio SSL (SAN) dal certificato self-signed, se presente
def get_dominio_ssl(self):
    import __main__ as _app
    DB_DIR = _app.DB_DIR
    cert_path = os.path.join(DB_DIR, "cert.pem")
    try:
        from cryptography import x509
        with open(cert_path, "rb") as f:
            cert = x509.load_pem_x509_certificate(f.read())
        san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        nomi = san.value.get_values_for_type(x509.DNSName)
        nomi_validi = [n for n in nomi if n != "localhost" and "." in n]
        return nomi_validi[0] if nomi_validi else ""
    except:
        return ""

# Popup gestione certificati SSL: elenca i file .pem/.crt/.key presenti, permette generazione self-signed, importazione ed eliminazione
def gestisci_certificati(self):
    import __main__ as _app
    DB_DIR = _app.DB_DIR
    EXP_DB = _app.EXP_DB
    if hasattr(self, '_certificati_popup') and self._certificati_popup and self._certificati_popup.winfo_exists():
                self._certificati_popup.lift()
                self._certificati_popup.focus_force()
                return
    popup = tk.Toplevel(self)
    popup.transient(self)
    self._certificati_popup = popup
    popup.bind("<Destroy>", lambda e: setattr(self, '_certificati_popup', None))
    popup.title("Gestione Certificati SSL")
    popup.configure(bg=self.COLOR_WIDGET_BG)
    popup.resizable(False, False)
    popup.withdraw()
    popup.update_idletasks()
    w, h = 600, 420
    sw, sh = popup.winfo_screenwidth(), popup.winfo_screenheight()
    popup.geometry(f'{w}x{h}+{(sw-w)//2}+{(sh-h)//2}')
    popup.deiconify()
    popup.bind('<Escape>', lambda e: popup.destroy())
    main_frame = tk.Frame(popup, padx=15, pady=15, bg=self.COLOR_WIDGET_BG)
    main_frame.pack(fill=tk.BOTH, expand=True)
    tk.Label(main_frame, text="Gestione Certificati SSL ",
             compound="left", font=("Arial", 11, "bold"),
             bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HIGHLIGHT).pack(pady=(0, 10))
    tree_frame = tk.Frame(main_frame, bg=self.COLOR_WIDGET_BG, height=180)
    tree_frame.pack(fill=tk.BOTH, expand=False)
    tree_frame.pack_propagate(False)
    self.tree_ssl = ttk.Treeview(tree_frame, columns=("n", "t"), show="headings", selectmode="extended")
    self.tree_ssl.heading("n", text="Nome File")
    self.tree_ssl.heading("t", text="Tipo")
    self.tree_ssl.column("n", width=380, anchor="w")
    self.tree_ssl.column("t", width=80, anchor="center")
    sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_ssl.yview)
    self.tree_ssl.configure(yscrollcommand=sb.set)
    self.tree_ssl.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sb.pack(side=tk.RIGHT, fill=tk.Y)
    nota_frame = ttk.LabelFrame(main_frame, text="ℹ️  Certificati Self-Signed", padding=(10, 6))
    nota_frame.pack(fill=tk.X, pady=(10, 0))
    ttk.Label(
        nota_frame,
        text=(
            "Il certificato generato automaticamente è self-signed (auto-firmato).\n"
            "Il browser mostrerà un avviso di sicurezza al primo accesso: è normale e atteso.\n"
            "Clicca 'Avanzate' → 'Procedi comunque' per aggiungere l'eccezione permanente.\n\n"
            "Per eliminare l'avviso definitivamente puoi:\n"
            "  • Importare il file cert.pem come 'Autorità di certificazione attendibile' nel browser\n"
            "  • Oppure usare una VPN (WireGuard, Tailscale) e accedere in HTTP sulla LAN"
        ),
        font=("Arial", 8),
        justify=tk.LEFT,
        wraplength=540,
    ).pack(fill=tk.X)
    def refresh_list():
        for i in self.tree_ssl.get_children():
            self.tree_ssl.delete(i)
        if os.path.exists(DB_DIR):
            ext = ('.crt', '.key', '.pem', '.p12')
            files = [f for f in os.listdir(DB_DIR) if f.lower().endswith(ext)]
            for f in sorted(files):
                t = os.path.splitext(f)[1].upper().replace(".", "")
                self.tree_ssl.insert("", tk.END, values=(f, t))
    def on_import(e=None):
        paths = filedialog.askopenfilenames(
            parent=popup, title="Importa SSL",
            filetypes=[("Certificati", "*.crt *.key *.pem *.p12"), ("Tutti", "*.*")],
            initialdir=EXP_DB)
        if paths:
            for p in paths:
                try:
                    shutil.copy(p, os.path.join(DB_DIR, os.path.basename(p)))
                except Exception as err:
                    self.show_custom_warning("Errore", str(err))
            refresh_list()
    def on_delete(e=None):
        items = self.tree_ssl.selection()
        if not items:
            self.show_custom_warning("Nessuna selezione", "Seleziona almeno un file da eliminare.")
            return
        count = len(items)
        msg = (f"Eliminare definitivamente {count} file selezionati?"
               if count > 1
               else f"Eliminare {self.tree_ssl.item(items[0])['values'][0]}?")
        if self.show_custom_askyesno("Sicurezza", msg):
            for i in items:
                name = self.tree_ssl.item(i)['values'][0]
                try:
                    os.remove(os.path.join(DB_DIR, name))
                except Exception as err:
                    self.show_custom_warning("Errore", f"Errore su {name}: {err}")
            refresh_list()
    def on_genera(e=None):
        cert_path = os.path.join(DB_DIR, "cert.pem")
        key_path  = os.path.join(DB_DIR, "key.pem")
        if os.path.exists(cert_path) and os.path.exists(key_path):
            if not self.show_custom_askyesno(
                "Certificato già presente",
                "Esiste già un certificato SSL.\nVuoi rigenerarlo sovrascrivendo quello attuale?"
            ):
                return
            try:
                os.remove(cert_path)
                os.remove(key_path)
            except Exception as err:
                self.show_custom_warning("Errore", f"Impossibile rimuovere i file esistenti:\n{err}")
                return
        ok = self.genera_certificati_auto()
        if ok:
            self.show_custom_info(
                "Certificato Generato",
                "Certificato SSL self-signed generato con successo.\n\n"
                "Il browser mostrerà un avviso di sicurezza al primo accesso.\n"
                "Clicca 'Avanzate' → 'Procedi comunque' per aggiungere l'eccezione.\n\n"
                "Il server si avvierà in HTTPS al prossimo riavvio dell'applicazione."
            )
        else:
            self.show_custom_warning(
                "Errore Generazione",
                "Impossibile generare il certificato SSL.\n"
                "Verificare che la libreria 'cryptography' sia installata:\n"
                "pip install cryptography"
            )
        refresh_list()
    toolbar = tk.Frame(main_frame, bg=self.COLOR_WIDGET_BG)
    toolbar.pack(fill=tk.X, pady=(12, 5))
    l_gen = tk.Label(toolbar, image=self.icone_gui.get("check"), text=" Genera Self-Signed",
                     compound="left", fg=self.COLOR_GREEN_SMOOTH, cursor="hand2",
                     font=("Arial", 9, "bold"), bg=self.COLOR_WIDGET_BG)
    l_gen.pack(side=tk.LEFT, padx=10)
    l_gen.bind("<Button-1>", on_genera)

    l_imp = tk.Label(toolbar, image=self.icone_gui.get("carica"), text=" Importa",
                     compound="left", fg=self.COLOR_GREEN_SMOOTH, cursor="hand2",
                     font=("Arial", 9, "bold"), bg=self.COLOR_WIDGET_BG)
    l_imp.pack(side=tk.LEFT, padx=10)
    l_imp.bind("<Button-1>", on_import)

    l_del = tk.Label(toolbar, image=self.icone_gui.get("delete"), text=" Elimina",
                     compound="left", fg=self.COLOR_RED_SMOOTH, cursor="hand2",
                     font=("Arial", 9, "bold"), bg=self.COLOR_WIDGET_BG)
    l_del.pack(side=tk.LEFT, padx=10)
    l_del.bind("<Button-1>", on_delete)
    def _riavvia_app(e=None):
        self.show_toast("Riavvio In Corso !", duration=3000)
        def esegui_kill():
            if popup.winfo_exists():
                popup.destroy()
            import subprocess, sys, os
            script_path = os.path.abspath(sys.argv[0])
            args = [sys.executable, script_path] + sys.argv[1:]
            if os.name == 'nt':
                subprocess.Popen(args, creationflags=0x00000008, shell=False, close_fds=True)
            else:
                subprocess.Popen(args, start_new_session=True, close_fds=True)
            self.destroy()
            os._exit(0)
        self.after(800, esegui_kill)

    img_riavvia = self.icone_gui.get("reset")
    btn_riavvia = tk.Label(toolbar, image=img_riavvia, text=" Riavvia App",
                           compound="left", cursor="hand2", bg=self.COLOR_WIDGET_BG,
                           fg=self.TEXT_COLOR, font=("Arial", 9, "bold"))
    btn_riavvia.pack(side=tk.LEFT, padx=10)
    btn_riavvia.bind("<Button-1>", _riavvia_app)
    btn_c = tk.Label(toolbar, image=self.icone_gui.get("chiudi"), text=" Chiudi",
                     compound="left", cursor="hand2", bg=self.COLOR_WIDGET_BG,
                     fg=self.TEXT_COLOR, font=("Arial", 9, "bold"))
    btn_c.pack(side=tk.RIGHT, padx=10)
    btn_c.bind("<Button-1>", lambda e: popup.destroy())
    refresh_list()

# Log degli Accessi Locali / Web
def mostra_log_accessi(self):
    import __main__ as _app
    LOGIN_WEB = _app.LOGIN_WEB
    LOGIN_WEB_FAIL = _app.LOGIN_WEB_FAIL
    LOGIN_LCL = _app.LOGIN_LCL
    ACCESS_CONTROL_WEB = _app.ACCESS_CONTROL_WEB
    from datetime import datetime
    popup = tk.Toplevel(self)
    popup.title(" Log Accessi")
    popup.withdraw()
    popup.update_idletasks()
    width, height = 1200, 550
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (width // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (height // 2)
    popup.geometry(f"{width}x{height}+{x}+{y}")
    popup.resizable(True, True)
    popup.minsize(width, height)
    popup.configure(bg=self.COLOR_BACKGROUND)
    popup.columnconfigure(0, weight=1)
    popup.rowconfigure(1, weight=1)
    tk.Label(popup, text="Log Accessi", bg=self.COLOR_BACKGROUND,
             fg=self.COLOR_HEADER, font=("Arial", 11, "bold")).grid(
             row=0, column=0, pady=(12, 5), padx=15, sticky="w")
    nb = ttk.Notebook(popup)
    nb.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
    def carica_json(path):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return []
    def carica_access_control():
        if os.path.exists(ACCESS_CONTROL_WEB):
            try:
                with open(ACCESS_CONTROL_WEB, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}
    def crea_tab_lista(parent, dati, colonne, larghezze=None):
        frame = ttk.Frame(parent)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        ttk.Separator(frame, orient="horizontal").grid(row=0, column=0, columnspan=2, sticky="ew")
        tree = ttk.Treeview(frame, columns=colonne, show="headings")
        for i, col in enumerate(colonne):
            w = larghezze[i] if larghezze and i < len(larghezze) else 200
            tree.column(col, width=w, minwidth=w, stretch=(i == len(colonne) - 1), anchor="w")
            tree.heading(col, text=col, anchor="w",
                         command=lambda c=col: self.treeview_sort_column(tree, c, False))
        for row in dati:
            if isinstance(row, dict):
                valori = [row.get(c, "") for c in colonne]
            else:
                valori = [str(row)] + [""] * (len(colonne) - 1)
            tree.insert("", "end", values=valori)
        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.grid(row=1, column=0, sticky="nsew")
        sb.grid(row=1, column=1, sticky="ns")
        if not dati:
            tree.insert("", "end", values=["Nessun record"] + [""] * (len(colonne) - 1))
        return frame
    def crea_tab_access_control(parent, dati):
        frame = ttk.Frame(parent)
        frame.columnconfigure(0, weight=1)
        ttk.Separator(frame, orient="horizontal").grid(row=0, column=0, sticky="ew")
        user = dati.get("web_user", {})
        count = user.get("count", 0)
        ban_until = user.get("ban_until", 0)
        ora = time.time()
        if ban_until > ora:
            restanti = int(ban_until - ora)
            stato_ban = f"🔴 Bannato — sblocco tra {restanti // 60}m {restanti % 60}s"
        else:
            stato_ban = "🟢 Libero"
        tk.Label(frame, text=f"Tentativi falliti correnti: {count}",
                 font=("Arial", 10), bg=self.COLOR_WIDGET_BG,
                 fg=self.TEXT_COLOR).grid(row=1, column=0, sticky="w", padx=15, pady=(15, 5))
        tk.Label(frame, text=f"Stato ban: {stato_ban}",
                 font=("Arial", 10), bg=self.COLOR_WIDGET_BG,
                 fg=self.TEXT_COLOR).grid(row=2, column=0, sticky="w", padx=15, pady=5)
        return frame
    dati_web_ok = [{"Timestamp": r.get("data_ora",""), "Indirizzo IP": r.get("ip",""), "Browser": r.get("browser","")} for r in carica_json(LOGIN_WEB) if isinstance(r, dict)]
    tab_ok = crea_tab_lista(nb, dati_web_ok, ["Timestamp", "Indirizzo IP", "Browser"], larghezze=[240, 220, 700])
    nb.add(tab_ok, text="✅ Accessi WEB OK")
    dati_web_fail = [{"Timestamp": r.get("data_ora",""), "Indirizzo IP": r.get("ip",""), "Tentativo": r.get("pwd_tentata",""), "Browser": r.get("browser","")} for r in carica_json(LOGIN_WEB_FAIL) if isinstance(r, dict)]
    tab_fail = crea_tab_lista(nb, dati_web_fail, ["Timestamp", "Indirizzo IP", "Tentativo", "Browser"])
    nb.add(tab_fail, text="❌ Accessi WEB Falliti")
    dati_lcl = carica_json(LOGIN_LCL)
    if isinstance(dati_lcl, dict):
        dati_lcl = dati_lcl.get("eventi", [])
    dati_lcl = [{"Timestamp": r.get("timestamp",""), "Tipo": r.get("tipo",""), "Utente": r.get("utente",""), "Session ID": r.get("session_id",""), "Tentativo": r.get("tentativo",""), "Password Tentata": r.get("password_tentata","")} for r in dati_lcl if isinstance(r, dict)]
    tab_lcl = crea_tab_lista(nb, dati_lcl, ["Timestamp", "Tipo", "Utente", "Session ID", "Tentativo", "Password Tentata"])
    nb.add(tab_lcl, text="🖥️ Login Locali")
    tab_ac = crea_tab_access_control(nb, carica_access_control())
    nb.add(tab_ac, text="🛡️ Ban Status")
    btns = tk.Frame(popup, bg=self.COLOR_BACKGROUND)
    btns.grid(row=2, column=0, pady=10, padx=15, sticky="ew")
    btns.columnconfigure(0, weight=1)
    btns.columnconfigure(1, weight=1)
    btns.columnconfigure(2, weight=1)
    def azzera_tutto():
        if not self.show_custom_askyesno("Conferma", "Azzerare tutti i log di accesso?"):
            return
        for path in [LOGIN_WEB, LOGIN_WEB_FAIL, LOGIN_LCL]:
            with open(path, "w", encoding="utf-8") as f:
                json.dump([], f)
        with open(ACCESS_CONTROL_WEB, "w", encoding="utf-8") as f:
            json.dump({"web_user": {"count": 0, "ban_until": 0, "last_attempt": 0}}, f)
        ricarica()
        self.show_toast("Log azzerati.", duration=2000)
    def azzera_ban():
        with open(ACCESS_CONTROL_WEB, "w", encoding="utf-8") as f:
            json.dump({"web_user": {"count": 0, "ban_until": 0, "last_attempt": 0}}, f)
        ricarica()
        self.show_toast("Ban rimosso.", duration=2000)
    def ricarica():
        for tab in nb.tabs():
            nb.forget(tab)
        dati_web_ok = [{"Timestamp": r.get("data_ora",""), "Indirizzo IP": r.get("ip",""), "Browser": r.get("browser","")} for r in carica_json(LOGIN_WEB) if isinstance(r, dict)]
        tab_ok = crea_tab_lista(nb, dati_web_ok, ["Timestamp", "Indirizzo IP", "Browser"], larghezze=[140, 120, 700])
        nb.add(tab_ok, text="✅ Accessi WEB OK")
        dati_web_fail = [{"Timestamp": r.get("data_ora",""), "Indirizzo IP": r.get("ip",""), "Tentativo": r.get("pwd_tentata",""), "Browser": r.get("browser","")} for r in carica_json(LOGIN_WEB_FAIL) if isinstance(r, dict)]
        tab_fail = crea_tab_lista(nb, dati_web_fail, ["Timestamp", "Indirizzo IP", "Tentativo", "Browser"], larghezze=[100, 100, 150, 600])
        nb.add(tab_fail, text="❌ Accessi WEB Falliti")
        dati_lcl = carica_json(LOGIN_LCL)
        if isinstance(dati_lcl, dict):
            dati_lcl = dati_lcl.get("eventi", [])
        dati_lcl = [{"Timestamp": r.get("timestamp",""), "Tipo": r.get("tipo",""), "Utente": r.get("utente",""), "Session ID": r.get("session_id",""), "Tentativo": r.get("tentativo",""), "Password Tentata": r.get("password_tentata","")} for r in dati_lcl if isinstance(r, dict)]
        tab_lcl = crea_tab_lista(nb, dati_lcl, ["Timestamp", "Tipo", "Utente", "Session ID", "Tentativo", "Password Tentata"])
        nb.add(tab_lcl, text="🖥️ Login Locali")
        tab_ac = crea_tab_access_control(nb, carica_access_control())
        nb.add(tab_ac, text="🛡️ Ban Status")
    lbl_azzera = ttk.Label(btns, image=self.icone_gui.get("delete"),
            text=" Azzera Tutti i Log", compound="left", cursor="hand2",
            background=self.COLOR_BACKGROUND, foreground=self.COLOR_RED_SMOOTH,
            font=("Arial", 9, "bold"))
    lbl_azzera.grid(row=0, column=0, padx=5, sticky="ew")
    lbl_azzera.bind("<Button-1>", lambda e: azzera_tutto())
    lbl_ban = ttk.Label(btns, image=self.icone_gui.get("reset"),
            text=" Rimuovi Ban", compound="left", cursor="hand2",
            background=self.COLOR_BACKGROUND, foreground=self.COLOR_HEADER,
            font=("Arial", 9, "bold"))
    lbl_ban.grid(row=0, column=1, padx=5, sticky="ew")
    lbl_ban.bind("<Button-1>", lambda e: azzera_ban())

    lbl_ricarica = ttk.Label(btns, image=self.icone_gui.get("sync"),
            text=" Ricarica", compound="left", cursor="hand2",
            background=self.COLOR_BACKGROUND, foreground=self.COLOR_HEADER,
            font=("Arial", 9, "bold"))
    lbl_ricarica.grid(row=0, column=2, padx=5, sticky="ew")
    lbl_ricarica.bind("<Button-1>", lambda e: ricarica())
    lbl_chiudi = ttk.Label(btns, image=self.icone_gui.get("chiudi"),
            text=" Chiudi", compound="left", cursor="hand2",
            background=self.COLOR_BACKGROUND, foreground=self.COLOR_HEADER,
            font=("Arial", 9, "bold"))
    lbl_chiudi.grid(row=0, column=3, padx=5, sticky="ew")
    lbl_chiudi.bind("<Button-1>", lambda e: popup.destroy())
    btns.columnconfigure(0, weight=1)
    btns.columnconfigure(1, weight=1)
    btns.columnconfigure(2, weight=1)
    btns.columnconfigure(3, weight=1)
    popup.bind("<Escape>", lambda e: popup.destroy())
    popup.deiconify()
