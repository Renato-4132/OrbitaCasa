#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import io
import requests
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from __main__ import NAME, VERSION, DB_DIR

def _avvia_tutorial(self):
    num_mov = sum(len(v) for v in self.spese.values()) if hasattr(self, 'spese') else 0
    if num_mov > 0:
        return
    ACCENTI = [
        ("#E8F4FD", "#1565C0"),
        ("#E8F5E9", "#2E7D32"),
        ("#F3E5F5", "#6A1B9A"),
        ("#FFF3E0", "#E65100"),
        ("#E0F2F1", "#00695C"),
        ("#FCE4EC", "#880E4F"),
        ("#F9FBE7", "#558B2F"),
        ("#E8EAF6", "#283593"),
    ]
    BASE_URL = "https://raw.githubusercontent.com/Renato-4132/OrbitaCasa/main/screenshots/"
    IMG_W, IMG_H = 390, 210
    passi = [
        {
            "screenshot": None,
            "titolo": "Benvenuto in OrbitaCasa!",
            "intro": "Il tuo assistente finanziario personale.\nIntelligente, offline, sempre tuo.",
            "punti": [
                "Registra spese ed entrate in pochi secondi",
                "Grafici e statistiche in tempo reale",
                "Intelligenza artificiale integrata",
                "100% locale — i tuoi dati non lasciano mai il PC",
                "Accesso da smartphone via web server",
            ],
            "btn_azione": None,
        },
        {
            "screenshot": "calendario.png",
            "titolo": "Il calendario che capisce i tuoi soldi",
            "intro": "Ogni giorno si colora in base ai movimenti.\nUn colpo d'occhio e sai tutto.\n\nConfigura subito le tue categorie — è il primo passo!",
            "punti": [
                "Verde → giorno con entrate",
                "Rosso → giorno con uscite",
                "Giallo → entrambe nello stesso giorno",
                "SmartCat suggerisce la categoria automaticamente",
                "Doppio clic sul giorno → inserimento rapido",
            ],
            "btn_azione": ("Apri Categorie Suggerite", lambda: self.apri_categorie_suggerite(parent=win)),
        },
        {
            "screenshot": "importa.png",
            "titolo": "L'AI importa tutto al posto tuo",
            "intro": "Trascina un PDF sull'app.\nGemini AI legge, estrae e compila da solo.",
            "punti": [
                "Estratti conto bancari — qualsiasi formato",
                "Scontrini fotografati con lo smartphone",
                "Bollette da Gmail — importate in automatico",
                "Revisione prima del salvataggio ",
                "Basta configurare la API key Gemini una volta sola",
            ],
            "btn_azione": None,
        },
        {
            "screenshot": "grafici.png",
            "titolo": "Grafici che parlano da soli",
            "intro": "Capisci dove vanno i tuoi soldi\ncon un colpo d'occhio.",
            "punti": [
                "Andamento entrate vs uscite mese per mese",
                "Spesa per categoria con drill-down interattivo",
                "Saldo progressivo cumulativo nel tempo",
                "Carosello automatico — si aggiorna da solo",
                "Esporta il bilancio completo in PDF",
            ],
            "btn_azione": None,
        },
        {
            "screenshot": "archivio.png",
            "titolo": "Archivio documenti personali e contabili",
            "intro": "Fatture, ricevute, contratti, referti.\nTutto archiviato, tutto trovabile in secondi.",
            "punti": [
                "Archivio contabile con viewer PDF integrato",
                "Archivio personale fino a 5 profili familiari",
                "Ricerca istantanea su tutti i campi",
                "Backup automatico ",
                "Drag & Drop + AI precompila i metadati",
            ],
            "btn_azione": None,
        },
        {
            "screenshot": "backup.png",
            "titolo": "Tutto si configura da qui",
            "intro": "Backup, sincronizzazione, sicurezza.\nApri il menu Impostazioni quando vuoi per personalizzare tutto.",
            "punti": [
                "Backup automatico copie configurabili",
                "Imposta Gmail e App Password",
                "API Key Gemini per l'importazione automatica",
                "Tema, timeout inattività e notifiche a tuo piacere",
                "Impostazioni  →  icona ⚙️ in basso a sinistra",
            ],
            "btn_azione": None,
        },
        {
            "screenshot": "wifi.png",
            "titolo": "Con te ovunque, da qualsiasi dispositivo",
            "intro": "Il tuo PC diventa un server.\nIl tuo telefono, uno sportello bancario.",
            "punti": [
                "Scansiona il QR code — accedi dal browser",
                "Inserisci movimenti dal divano",
                "Consulta statistiche in mobilità",
                "Carica PDF direttamente dal telefono",
                "Tutto cifrato con SSL — solo tu puoi accedere",
            ],
            "btn_azione": None,
        },
        {
            "screenshot": "proiezione.png",
            "titolo": "Un ecosistema completo",
            "intro": "Molto più di un registro spese.\nUn sistema che cresce con te.",
            "punti": [
                "FairShare — dividi le spese tra coinquilini",
                "ImmoBil — gestisci immobili e affitti",
                "MyBuisness — clienti, fatture, magazzino",
                "Portafoglio — azioni, ETF e crypto live",
                "Dieta & Benessere — calorie, peso, passi",
                "Movimenti Ricorrenti — bollette automatiche",
                "Fondo Risparmio — proiezioni e obiettivi",
                "Time Machine — quanto risparmieresti senza X?",
                "Confronta Periodi — analizza & confronta",
                "Gestione Utenze — acqua, luce, gas, Storico",
                "Lista Spesa Intelligente — confronto supermercati",
                "Calcolo Mutuo/Prestiti — Ammortamento",
                "Sincronizzazione multi-postazione in rete locale",
            ],
            "btn_azione": None,
        },
        {
            "screenshot": "saldo.png",
            "titolo": "Tutto pronto. Si parte!",
            "intro": "Setup iniziale: meno di 5 minuti.\nPoi OrbitaCasa lavora per te.\n\nUsa il pulsante qui sotto per scaricare e aprire il manuale PDF completo, una guida dettagliata sempre a portata di mano.",
            "punti": [
                "Crea le tue categorie  →  Ctrl+Shift+T",
                "Imposta il saldo iniziale  →  Ctrl+S",
                "Inserisci il primo movimento dal form in basso",
                "Manuale completo sempre disponibile  →  Ctrl+M",
                "Assistenza:  helporbitacasa@gmail.com",
            ],
            "btn_azione": ("Apri il Manuale Completo", lambda: [win.destroy(), self.scarica_manuale()]),
        },
    ]
    stato = {"passo": 0, "imgs": {}}
    try:
        path_logo = os.path.join(DB_DIR, "resources", "info_image.png")
        img_logo = Image.open(path_logo)
        img_logo.thumbnail((IMG_W, IMG_H), Image.LANCZOS)
        stato["imgs"][0] = ImageTk.PhotoImage(img_logo)
    except Exception:
        stato["imgs"][0] = None
    W, H = 980, 560
    win = tk.Toplevel(self)
    win.title(f"{NAME} — Benvenuto!")
    win.resizable(False, False)
    win.attributes("-topmost", True)
    win.configure(bg=self.COLOR_BACKGROUND)
    win.withdraw()
    win.update_idletasks()
    win.geometry(f"{W}x{H}+{(win.winfo_screenwidth()//2)-(W//2)}+{(win.winfo_screenheight()//2)-(H//2)}")
    win.deiconify()
    accent_bar = tk.Frame(win, height=5)
    accent_bar.pack(fill="x")
    accent_bar.pack_propagate(False)
    frm_main = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    frm_main.pack(fill="both", expand=True)
    frm_sx = tk.Frame(frm_main, bg=self.COLOR_BACKGROUND, width=420)
    frm_sx.pack(side="left", fill="y", padx=(16, 0), pady=12)
    frm_sx.pack_propagate(False)
    lbl_num = tk.Label(frm_sx, text="", font=("Arial", 8), bg=self.COLOR_BACKGROUND, fg="gray60", anchor="w")
    lbl_num.pack(anchor="w", pady=(0, 4))
    lbl_screenshot = tk.Label(frm_sx, bg=self.COLOR_BACKGROUND, anchor="w", text="")
    lbl_screenshot.pack(anchor="w", pady=(0, 10))
    lbl_titolo = tk.Label(frm_sx, text="", font=("Arial", 14, "bold"), bg=self.COLOR_BACKGROUND,
                          fg=self.COLOR_HIGHLIGHT, wraplength=400, justify="left", anchor="w")
    lbl_titolo.pack(anchor="w", pady=(0, 6))
    sep_sx = tk.Frame(frm_sx, height=2, bg=self.COLOR_HIGHLIGHT)
    sep_sx.pack(fill="x", pady=(0, 8))
    lbl_intro = tk.Label(frm_sx, text="", font=("Arial", 9, "italic"), bg=self.COLOR_BACKGROUND,
                         fg=self.TEXT_COLOR, wraplength=400, justify="left", anchor="nw")
    lbl_intro.pack(anchor="nw", fill="x")
    tk.Frame(frm_sx, bg=self.COLOR_BACKGROUND).pack(fill="both", expand=True)
    frm_azione = tk.Frame(frm_sx, bg=self.COLOR_BACKGROUND)
    btn_azione = tk.Label(frm_azione, text="", font=("Arial", 9, "bold"),
                          bg=self.COLOR_BACKGROUND, fg=self.COLOR_HIGHLIGHT, cursor="hand2")
    btn_azione.pack(side="left")
    frm_dx = tk.Frame(frm_main, bg="#E8F4FD", highlightthickness=0, bd=0)
    frm_dx.pack(side="left", fill="both", expand=True, padx=(12, 14), pady=12)
    lbl_dx_head = tk.Label(frm_dx, text="COSA PUOI FARE", font=("Arial", 7, "bold"),
                           bg="#E8F4FD", fg="#555555", anchor="w")
    lbl_dx_head.pack(anchor="w", padx=14, pady=(12, 4))
    sep_dx = tk.Frame(frm_dx, height=1, bg="#BBBBBB")
    sep_dx.pack(fill="x", padx=14, pady=(0, 6))
    frm_scroll_container = tk.Frame(frm_dx, bg="#E8F4FD")
    frm_scroll_container.pack(fill="both", expand=True, padx=(8, 0))
    canvas_punti = tk.Canvas(frm_scroll_container, bg="#E8F4FD", highlightthickness=0, bd=0)
    scroll_punti = ttk.Scrollbar(frm_scroll_container, orient="vertical", command=canvas_punti.yview)
    frm_punti = tk.Frame(canvas_punti, bg="#E8F4FD")
    frm_punti.bind("<Configure>", lambda e: canvas_punti.configure(scrollregion=canvas_punti.bbox("all")))
    canvas_punti.create_window((0, 0), window=frm_punti, anchor="nw")
    canvas_punti.configure(yscrollcommand=scroll_punti.set)
    scroll_punti.pack(side="right", fill="y", padx=(0, 4))
    canvas_punti.pack(side="left", fill="both", expand=True)
    for widget in (canvas_punti, frm_punti):
        widget.bind("<MouseWheel>", lambda e: canvas_punti.yview_scroll(int(-1*(e.delta/120)), "units"))
        widget.bind("<Button-4>",   lambda e: canvas_punti.yview_scroll(-1, "units"))
        widget.bind("<Button-5>",   lambda e: canvas_punti.yview_scroll(1,  "units"))
    MAX_PUNTI = max(len(p["punti"]) for p in passi)
    righe_punti = []
    for _ in range(MAX_PUNTI):
        r = tk.Frame(frm_punti, bg="#E8F4FD")
        r.pack(fill="x", pady=3)
        lb = tk.Label(r, text="▶", font=("Arial", 8, "bold"), bg="#E8F4FD", fg="#1565C0", width=2, anchor="center")
        lb.pack(side="left", padx=(6, 6))
        lt = tk.Label(r, text="", font=("Arial", 10), bg="#E8F4FD", fg="#222222",
                      anchor="w", justify="left", wraplength=300)
        lt.pack(side="left", fill="x", expand=True)
        righe_punti.append((r, lb, lt))
    sep_nav = tk.Frame(win, height=1, bg=self.COLOR_HIGHLIGHT)
    sep_nav.pack(side="bottom", fill="x")
    frm_nav = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    frm_nav.pack(side="bottom", fill="x", padx=20, pady=(6, 8))
    btn_chiudi = tk.Label(frm_nav, text="Salta tutorial", font=("Arial", 8),
                          bg=self.COLOR_BACKGROUND, fg="gray50", cursor="hand2")
    btn_chiudi.pack(side="left")
    frm_dots = tk.Frame(frm_nav, bg=self.COLOR_BACKGROUND)
    frm_dots.pack(side="left", expand=True)
    dots = []
    for i in range(len(passi)):
        d = tk.Label(frm_dots, text="●", font=("Arial", 8), bg=self.COLOR_BACKGROUND, fg="gray70")
        d.pack(side="left", padx=2)
        dots.append(d)
    frm_btns = tk.Frame(frm_nav, bg=self.COLOR_BACKGROUND)
    frm_btns.pack(side="right")
    btn_prec = tk.Label(frm_btns, text="◀  Indietro", font=("Arial", 9, "bold"),
                        bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR, cursor="hand2")
    btn_next = tk.Label(frm_btns, text="Avanti  ▶", font=("Arial", 9, "bold"),
                        bg=self.COLOR_BACKGROUND, fg=self.COLOR_GREEN, cursor="hand2")
    btn_next.pack(side="left", padx=(8, 0))
    def _scarica_immagini():
        for i, p in enumerate(passi):
            if p["screenshot"] is None or i in stato["imgs"]:
                continue
            try:
                resp = requests.get(BASE_URL + p["screenshot"], timeout=8)
                resp.raise_for_status()
                img = Image.open(io.BytesIO(resp.content))
                img.thumbnail((IMG_W, IMG_H), Image.LANCZOS)
                def _crea_photo_e_mostra(pil_img=img, idx=i):
                    if not win.winfo_exists():
                        return
                    photo = ImageTk.PhotoImage(pil_img)
                    stato["imgs"][idx] = photo
                    if stato["passo"] == idx:
                        lbl_screenshot.config(image=photo, text="")
                        lbl_screenshot.image = photo
                win.after(0, _crea_photo_e_mostra)
            except Exception:
                stato["imgs"][i] = None
    import threading
    threading.Thread(target=_scarica_immagini, daemon=True).start()
    def _aggiorna():
        p = stato["passo"]
        d = passi[p]
        tot = len(passi)
        bg_dx, col_titolo = ACCENTI[p % len(ACCENTI)]
        accent_bar.config(bg=col_titolo)
        frm_dx.config(bg=bg_dx)
        frm_scroll_container.config(bg=bg_dx)
        lbl_dx_head.config(bg=bg_dx)
        sep_dx.config(bg=col_titolo)
        frm_punti.config(bg=bg_dx)
        canvas_punti.config(bg=bg_dx)
        img = stato["imgs"].get(p)
        if img:
            lbl_screenshot.config(image=img, text="")
            lbl_screenshot.image = img
        elif p not in stato["imgs"]:
            lbl_screenshot.config(image="", text="Caricamento...", fg="gray60", font=("Arial", 8, "italic"))
            lbl_screenshot.image = None
        else:
            lbl_screenshot.config(image="", text="")
            lbl_screenshot.image = None
        lbl_num.config(text=f"Passo {p+1} di {tot}")
        lbl_titolo.config(text=d["titolo"], fg=col_titolo)
        sep_sx.config(bg=col_titolo)
        lbl_intro.config(text=d["intro"])
        for i, (r, lb, lt) in enumerate(righe_punti):
            r.config(bg=bg_dx)
            lb.config(bg=bg_dx, fg=col_titolo)
            lt.config(bg=bg_dx)
            if i < len(d["punti"]):
                lt.config(text=d["punti"][i], fg="#222222")
                r.pack(fill="x", pady=3)
            else:
                r.pack_forget()
        canvas_punti.yview_moveto(0)
        for i, dot in enumerate(dots):
            if i == p:
                dot.config(fg=col_titolo, font=("Arial", 12, "bold"))
            else:
                dot.config(fg="gray70", font=("Arial", 8))
        if p == 0:
            btn_prec.pack_forget()
        else:
            btn_prec.pack(side="left", before=btn_next)
        if p < tot - 1:
            btn_next.config(text="Avanti  ▶", fg=self.COLOR_GREEN)
        else:
            btn_next.config(text="  Inizia!  ✔", fg=col_titolo)
        btn_azione.unbind("<Button-1>")
        if d["btn_azione"]:
            etichetta, cmd = d["btn_azione"]
            btn_azione.config(text=f"▶  {etichetta}", fg=col_titolo)
            btn_azione.bind("<Button-1>", lambda e, c=cmd: c())
            frm_azione.pack(anchor="w", pady=(8, 0))
        else:
            frm_azione.pack_forget()
        win.attributes("-topmost", True)
        win.lift()
    def _avanti():
        if stato["passo"] < len(passi) - 1:
            stato["passo"] += 1
            _aggiorna()
        else:
            win.destroy()
    def _indietro():
        if stato["passo"] > 0:
            stato["passo"] -= 1
            _aggiorna()
    btn_next.bind("<Button-1>",   lambda e: _avanti())
    btn_prec.bind("<Button-1>",   lambda e: _indietro())
    btn_chiudi.bind("<Button-1>", lambda e: win.destroy())
    win.bind("<Escape>", lambda e: win.destroy())
    win.bind("<Right>",  lambda e: _avanti())
    win.bind("<Left>",   lambda e: _indietro())
    for btn in (btn_next, btn_prec, btn_azione):
        btn.bind("<Enter>", lambda e, b=btn: b.config(font=("Arial", 9, "bold", "underline")))
        btn.bind("<Leave>", lambda e, b=btn: b.config(font=("Arial", 9, "bold")))
    btn_chiudi.bind("<Enter>", lambda e: btn_chiudi.config(font=("Arial", 8, "underline")))
    btn_chiudi.bind("<Leave>", lambda e: btn_chiudi.config(font=("Arial", 8)))
    win.focus_force()
    _aggiorna()

