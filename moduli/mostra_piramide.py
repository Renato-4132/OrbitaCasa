#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk

# Gestione e Visualizzazione Guida Utente (Help)
def mostra_piramide(self):
    LIVELLI = [
            {
                    "label": "Cuore dell'app",
                    "fill": "#DBEAFE", "outline": "#3B82F6", "fg": "#1E3A5F",
                    "moduli": [
                            ("Finanze & Spese", "Registro movimenti principale", lambda win=None: win.destroy() if win else None),
                    ],
            },
            {
                    "label": "Patrimonio",
                    "fill": "#DCFCE7", "outline": "#22C55E", "fg": "#14532D",
                    "moduli": [
                            ("Portafoglio Bancario",  "Conti, saldi, trasferimenti",   getattr(self, "open_saldo_conto", None)),
                            ("Portafoglio Invest.",   "yfinance, P&L, AI Gemini",      getattr(self, "apri_portafoglio", None)),
                            ("Fondo Risparmio",       "Proiezioni stagionali",         getattr(self, "apri_fondo_risparmio", None)),
                    ],
            },
            {
                    "label": "Moduli casa",
                    "fill": "#FEF9C3", "outline": "#EAB308", "fg": "#713F12",
                    "moduli": [
                            ("Gestione Utenze",  "Consumi e grafici",         getattr(self, "utenze", None)),
                            ("FairShare",        "Spese condivise e debiti",  getattr(self, "mostra_riepilogo_fairshare_periodo", None)),
                            ("Dieta & Salute",   "Pasti, BMI, export PDF",    getattr(self, "apri_dieta", None)),
                            ("Rubrica",          "Contatti, vCard, CRUD",     getattr(self, "rubrica_app", None)),
                    ],
            },
            {
                    "label": "Strumenti",
                    "fill": "#EDE9FE", "outline": "#8B5CF6", "fg": "#2E1065",
                    "moduli": [
                            ("Gmail Sync",       "Import AI, Gemini",         lambda: self.avvia_sincronizzazione(manuale=True)),
                            ("Schedulatore",     "Task, email, tick",         getattr(self, "apri_schedulatore", None)),
                            ("MyBusiness",       "Clienti, fatture, cassa",   getattr(self, "apri_studio", None)),
                            ("Lista Spesa",      "Supermercato, quantita",    getattr(self, "spesa_supermercato", None)),
                            ("Archivi Doc.",     "PDF contabili",             getattr(self, "gestisci_archivi_pdf", None)),
                            ("Doc. Personali",   "PDF personali",             getattr(self, "gestisci_documenti_personali", None)),
                    ],
            },
            {
                    "label": "Utility",
                    "fill": "#FEE2E2", "outline": "#EF4444", "fg": "#7F1D1D",
                    "moduli": [
                            ("Calcolatrice",     "Integrata",                 getattr(self, "apri_calcolatrice", None)),
                            ("Calc. Inflazione", "ISTAT NIC 2000-2025",       getattr(self, "apri_calcolatore_inflazione", None)),
                            ("Scadenziario",     "Scadenze del mese",         getattr(self, "calcola_mancanti", None)),
                            ("Backup",           "ZIP / JSON restore",        getattr(self, "gestisci_backup_popup", None)),
                            ("Web Server",       "Flask, PWA, SSL",           getattr(self, "apri_webserver", None)),
                            ("Report PDF",       "Bilancio annuo",            getattr(self, "genera_report_pdf", None)),
                            ("QR & Timer",       "Generatore QR",             getattr(self, "launch_qr_svg_generator", None)),
                    ],
            },
            {
                    "label": "Analisi",
                    "fill": "#F3F4F6", "outline": "#9CA3AF", "fg": "#111827",
                    "moduli": [
                            ("Banca Online",   "Accesso esterno",       getattr(self, "chiama_banca", None)),
                            ("Analisi Grafici","Andamento risparmio",   getattr(self, "mostra_analisi_grafici", None)),
                            ("Analisi IA",     "Gemini bilancio",       getattr(self, "analizza_andamento_ia", None)),
                            ("Ricorrenze",     "Scadenze, notifiche",   getattr(self, "mostra_lista_ricorrenze", None)),
                            ("Immobili",       "Gestione Immobili",     getattr(self, "immobil", None)),
                            ("Veicoli",        "Scadenze e consumi",    getattr(self, "veicoli", None)),
                    ],
            },
    ]
    CANVAS_W  = 1180
    PADDING   = 28
    LABEL_W   = 80
    GAP_X     = 8
    GAP_Y     = 12
    CARD_H    = 60
    CORNER    = 10
    TOP_Y     = 70
    bg        = self.COLOR_BACKGROUND
    fg_title  = self.COLOR_TEXT
    win = tk.Toplevel(self)
    win.withdraw()
    win.title("Mappa Moduli")
    win.configure(bg=bg)
    win.resizable(False, False)
    win.bind("<Escape>", lambda e: win.destroy())
    total_h = TOP_Y + len(LIVELLI) * (CARD_H + GAP_Y) + 60
    canvas = tk.Canvas(win, width=CANVAS_W, height=total_h,
                       bg=bg, highlightthickness=0)
    canvas.pack(padx=0, pady=0)
    def rounded_rect(c, x1, y1, x2, y2, r, **kw):
            pts = [
                    x1+r, y1,   x2-r, y1,
                    x2,   y1,   x2,   y1+r,
                    x2,   y2-r, x2,   y2,
                    x2,   y2,   x2-r, y2,
                    x1+r, y2,   x1,   y2,
                    x1,   y2,   x1,   y2-r,
                    x1,   y1+r, x1,   y1,
                    x1,   y1,   x1+r, y1,
            ]
            return c.create_polygon(pts, smooth=True, **kw)
    def _schiarisci(hex_color, factor=0.88):
            hex_color = hex_color.lstrip("#")
            r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            r = int(r * factor)
            g = int(g * factor)
            b = int(b * factor)
            return f"#{r:02X}{g:02X}{b:02X}"
    canvas.create_text(CANVAS_W // 2, 22,
                       text="Best modules  –  OrbitaCasa 2.2",
                       font=("Arial", 15, "bold"), fill=fg_title, anchor="center")
    canvas.create_text(CANVAS_W // 2, 44,
                       text="Clicca su un modulo per aprirlo",
                       font=("Arial", 9), fill="#888888", anchor="center")
    y = TOP_Y
    for liv_idx, livello in enumerate(LIVELLI):
            moduli  = livello["moduli"]
            n       = len(moduli)
            fill_n  = livello["fill"]
            fill_h  = _schiarisci(fill_n)
            outline = livello["outline"]
            fg      = livello["fg"]
            avail   = CANVAS_W - 2 * PADDING - (n - 1) * GAP_X - LABEL_W
            card_w  = avail // n
            canvas.create_text(CANVAS_W - 4, y + CARD_H // 2,
                               text=livello["label"],
                               font=("Arial", 8), fill="#AAAAAA",
                               anchor="e")
            for i, (nome, desc, cmd) in enumerate(moduli):
                    x1 = PADDING + i * (card_w + GAP_X)
                    x2 = x1 + card_w
                    y1 = y
                    y2 = y + CARD_H
                    rid = rounded_rect(canvas, x1, y1, x2, y2, CORNER,
                                       fill=fill_n, outline=outline,
                                       width=1.2)
                    canvas.create_text((x1+x2)//2, y1 + CARD_H//2 - 8,
                                       text=nome,
                                       font=("Arial", 9, "bold"),
                                       fill=fg, anchor="center")
                    canvas.create_text((x1+x2)//2, y1 + CARD_H//2 + 10,
                                       text=desc,
                                       font=("Arial", 7),
                                       fill=fg, anchor="center")
                    hit = canvas.create_rectangle(x1, y1, x2, y2,
                                                   fill="", outline="",
                                                   width=0)
                    def make_handlers(rect_id=rid, fn=fill_n, fh=fill_h, cmd=cmd):
                            def on_enter(e):
                                    canvas.itemconfig(rect_id, fill=fh)
                                    if cmd:
                                            canvas.config(cursor="hand2")
                            def on_leave(e):
                                    canvas.itemconfig(rect_id, fill=fn)
                                    canvas.config(cursor="")
                            def on_click(e):
                                    if cmd:
                                            win.withdraw()
                                            win.after(100, cmd)
                            return on_enter, on_leave, on_click
                    on_enter, on_leave, on_click = make_handlers()
                    canvas.tag_bind(hit, "<Enter>", on_enter)
                    canvas.tag_bind(hit, "<Leave>", on_leave)
                    canvas.tag_bind(hit, "<Button-1>", on_click)
            y += CARD_H + GAP_Y
    canvas.create_text(CANVAS_W // 2, total_h - 18,
                       text="6 livelli  ·  26 moduli e tool  ·  Python · Tkinter · Flask · Gemini AI",
                       font=("Arial", 8), fill="#BBBBBB", anchor="center")
    btn_chiudi = tk.Label(win, compound="left", image=self.icone_gui.get("chiudi"), text=" Chiudi", background=bg, foreground=fg_title, cursor="hand2", padx=15, pady=6, font=("Arial", 9, "bold"))
    btn_chiudi.pack(side=tk.BOTTOM, pady=10)
    btn_chiudi.bind("<Button-1>", lambda e: win.destroy())
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    ww = win.winfo_reqwidth()
    wh = win.winfo_reqheight()
    win.geometry(f"{ww}x{wh}+{(sw-ww)//2}+{(sh-wh)//2}")
    win.deiconify()
    win.focus_force()
    
