#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw, ImageTk

# Gestione e Visualizzazione Guida Utente (Help) - Piramide 3D interattiva dei moduli
def mostra_piramide(self):
    LIVELLI = [
            {
                    "label": "Cuore dell'app",
                    "fill": "#DBEAFE", "outline": "#3B82F6", "fg": "#1E3A5F",
                    "moduli": [
                            ("Main", "Registro movimenti principale", lambda win=None: win.destroy() if win else None),
                            ("Main", "Registro movimenti principale", lambda win=None: win.destroy() if win else None),
                            ("Main", "Registro movimenti principale", lambda win=None: win.destroy() if win else None),
                            ("Main", "Registro movimenti principale", lambda win=None: win.destroy() if win else None),
                    ],
            },
            {
                    "label": "Patrimonio",
                    "fill": "#DCFCE7", "outline": "#22C55E", "fg": "#14532D",
                    "moduli": [
                            ("Banca",    "Conti, saldi, trasferimenti",   getattr(self, "open_saldo_conto", None)),
                            ("Invest.",  "yfinance, P&L, AI Gemini",      getattr(self, "apri_portafoglio", None)),
                            ("Risparmi", "Proiezioni stagionali",         getattr(self, "apri_fondo_risparmio", None)),
                            ("Punti",    "Gamification",                  getattr(self, "mostra_dettaglio_gamification", None)),
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

    LIVELLI_BASE_APICE = list(reversed(LIVELLI))
    N_LIV = len(LIVELLI_BASE_APICE)

    CANVAS_W, CANVAS_H = 900, 550
    BASE_HALF = 200.0
    LEVEL_H   = 70.0 
    MARGINE_V = 0.06 
    CAM_D, FOCAL = 900.0, 760.0 
    ELEV = math.radians(22)
    VEL_TRASCINAMENTO = 0.008 
    AUTO_ROTATE = True 
    VEL_AUTO = 0.05
    SUPERSAMPLE = 2

    bg       = self.COLOR_BACKGROUND
    fg_title = self.TEXT_COLOR

    win = tk.Toplevel(self)
    win.withdraw()
    win.title("Panoramica Moduli")
    win.configure(bg=bg)
    win.resizable(False, False)
    win.bind("<Escape>", lambda e: win.destroy())
    win.bind("<FocusOut>", lambda e: _tooltip_hide())
    win.bind("<Unmap>", lambda e: _tooltip_hide())

    canvas = tk.Canvas(win, width=CANVAS_W, height=CANVAS_H, bg=bg, highlightthickness=0)
    canvas.pack(padx=0, pady=0)

    canvas.create_text(40, 25,
                       text="Panoramica Moduli",
                       font=("Arial", 15, "bold"), fill=fg_title, anchor="w")

    canvas.create_text(CANVAS_W - 40, 25,
                       text="Trascina per ruotare la piramide  ·  Clicca su un modulo per aprirlo",
                       font=("Arial", 9), fill="#888888", anchor="e")

    def _shade(hex_color, factor):
        hex_color = hex_color.lstrip("#")
        r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        r = max(0, min(255, int(r * factor)))
        g = max(0, min(255, int(g * factor)))
        b = max(0, min(255, int(b * factor)))
        return f"#{r:02X}{g:02X}{b:02X}"

    def _blend(hex_a, hex_b, t):
        t = max(0.0, min(1.0, t))
        ha, hb = hex_a.lstrip("#"), hex_b.lstrip("#")
        ra, ga, ba = (int(ha[i:i+2], 16) for i in (0, 2, 4))
        rb, gb, bb = (int(hb[i:i+2], 16) for i in (0, 2, 4))
        r = int(ra + (rb - ra) * t)
        g = int(ga + (gb - ga) * t)
        b = int(ba + (bb - ba) * t)
        return f"#{r:02X}{g:02X}{b:02X}"

    TOTAL_H = LEVEL_H * N_LIV
    Y_BOUND = [i * LEVEL_H - TOTAL_H / 2 for i in range(N_LIV + 1)]
    W_BOUND = [BASE_HALF * (1 - i / N_LIV) for i in range(N_LIV + 1)]

    FACCE = ["front", "right", "back", "left"]
    NORMALI = {"front": (0.0, 0.0, 1.0), "right": (1.0, 0.0, 0.0),
               "back": (0.0, 0.0, -1.0), "left": (-1.0, 0.0, 0.0)}

    def _punto_faccia(direzione, u, y, rhb, rht, ry_bot, ry_top):
        t = (y - ry_bot) / (ry_top - ry_bot)
        s = rhb + (rht - rhb) * t
        if direzione == "front": return (u * s, y, s)
        if direzione == "back":  return (-u * s, y, -s)
        if direzione == "right": return (s, y, -u * s)
        return (-s, y, u * s)

    elementi = []
    for liv_idx, livello in enumerate(LIVELLI_BASE_APICE):
        y_bot, y_top = Y_BOUND[liv_idx], Y_BOUND[liv_idx + 1]
        hb, ht = W_BOUND[liv_idx], W_BOUND[liv_idx + 1]
        dy = (y_top - y_bot) * MARGINE_V
        ry_bot, ry_top = y_bot + dy, y_top - dy

        def _size_at(y, y_bot=y_bot, y_top=y_top, hb=hb, ht=ht):
            t = (y - y_bot) / (y_top - y_bot)
            return hb + (ht - hb) * t
        rhb, rht = _size_at(ry_bot), _size_at(ry_top)

        gruppi = {f: [] for f in FACCE}
        for idx, mod in enumerate(livello["moduli"]):
            gruppi[FACCE[idx % 4]].append(mod)

        for direzione in FACCE:
            mods = gruppi[direzione]
            k = len(mods)
            segmenti = [(-1 + 2 * i / k, -1 + 2 * (i + 1) / k) for i in range(k)] if k else [(-1, 1)]
            mods_seg = mods if k else [None]
            for (u0, u1), mod in zip(segmenti, mods_seg):
                corners = [
                    _punto_faccia(direzione, u0, ry_bot, rhb, rht, ry_bot, ry_top),
                    _punto_faccia(direzione, u1, ry_bot, rhb, rht, ry_bot, ry_top),
                    _punto_faccia(direzione, u1, ry_top, rhb, rht, ry_bot, ry_top),
                    _punto_faccia(direzione, u0, ry_top, rhb, rht, ry_bot, ry_top),
                ]
                elementi.append({
                    "corners": corners,
                    "normal": NORMALI[direzione],
                    "fill": livello["fill"],
                    "outline": livello["outline"],
                    "fg": livello["fg"],
                    "mod": mod,
                })

    CX, CY = 350, 200
    theta = [-0.55] 

    _pop_anim = {"active_el": None, "offset": 0.0, "animating": False}

    def _ruota_normale(n):
        nx, ny, nz = n
        ct, st = math.cos(theta[0]), math.sin(theta[0])
        return -nx * st + nz * ct

    def _proietta(pt):
        x, y, z = pt
        ct, st = math.cos(theta[0]), math.sin(theta[0])
        xr = x * ct + z * st
        zr = -x * st + z * ct
        ce, se = math.cos(ELEV), math.sin(ELEV)
        yr = y * ce - zr * se
        zr2 = y * se + zr * ce
        depth = CAM_D - zr2
        scale = FOCAL / depth
        return CX + xr * scale, CY - yr * scale, depth

    _tip_win = [None, None]

    def _tooltip_show(event, txt):
        if _tip_win[0]:
            try: _tip_win[0].destroy()
            except: pass
            _tip_win[0] = None
        if _tip_win[1]:
            try: event.widget.after_cancel(_tip_win[1])
            except: pass
            _tip_win[1] = None
        x, y = event.x_root, event.y_root
        widget = event.widget
        def _mostra():
            tw = tk.Toplevel(widget)
            tw.wm_overrideredirect(True)
            tw.withdraw()
            ttk.Label(tw, text=txt, style="Tooltip.TLabel").pack()
            tw.update_idletasks()
            tw_w = tw.winfo_reqwidth()
            tw_h = tw.winfo_reqheight()
            win_x0 = win.winfo_rootx()
            win_y0 = win.winfo_rooty()
            win_x1 = win_x0 + win.winfo_width()
            win_y1 = win_y0 + win.winfo_height()
            tx, ty = x + 12, y + 10
            if tx + tw_w > win_x1:
                tx = win_x1 - tw_w
            if tx < win_x0:
                tx = win_x0
            if ty + tw_h > win_y1:
                ty = y - tw_h - 10
            if ty < win_y0:
                ty = win_y0
            tw.wm_geometry(f"+{tx}+{ty}")
            tw.deiconify()
            _tip_win[0] = tw
        _tip_win[1] = widget.after(400, _mostra)

    def _tooltip_hide(event=None):
        if _tip_win[1]:
            try: canvas.after_cancel(_tip_win[1])
            except: pass
            _tip_win[1] = None
        if _tip_win[0]:
            try: _tip_win[0].destroy()
            except: pass
            _tip_win[0] = None

    _hit_tiles = []
    _hover_state = {"el": None}
    _render_state = {"photo": None}

    def _point_in_poly(px, py, pts):
        dentro = False
        n = len(pts)
        x1, y1 = pts[-1]
        for x2, y2 in pts:
            if ((y1 > py) != (y2 > py)) and (px < (x2 - x1) * (py - y1) / (y2 - y1) + x1):
                dentro = not dentro
            x1, y1 = x2, y2
        return dentro

    def _tile_sotto_cursore(x, y):
        for pts, el in _hit_tiles:
            if _point_in_poly(x, y, pts):
                return el
        return None

    SOGLIA_FACCIA       = 0.05 
    SOGLIA_TESTO_MIN    = 0.05 
    SOGLIA_TESTO_PIENA  = 0.30 

    def _render():
        canvas.delete("scena")
        visibili = []
        for el in elementi:
            if el == _pop_anim["active_el"] and _pop_anim["offset"] > 0:
                nx, ny, nz = el["normal"]
                d = _pop_anim["offset"]
                corners_3d = [(x + nx * d, y + ny * d, z + nz * d) for (x, y, z) in el["corners"]]
            else:
                corners_3d = el["corners"]

            nzr = _ruota_normale(el["normal"])
            if nzr <= SOGLIA_FACCIA:
                continue
            proiez = [_proietta(c) for c in corners_3d]
            depth_media = sum(p[2] for p in proiez) / 4
            visibili.append((depth_media, el, proiez, nzr))
        visibili.sort(key=lambda t: t[0], reverse=True) 

        tutti_i_punti = [p for _d, _el, proiez, _n in visibili for p in proiez]
        if tutti_i_punti:
            min_x = max(0, math.floor(min(p[0] for p in tutti_i_punti)) - 2)
            max_x = min(CANVAS_W, math.ceil(max(p[0] for p in tutti_i_punti)) + 2)
            min_y = max(0, math.floor(min(p[1] for p in tutti_i_punti)) - 2)
            max_y = min(CANVAS_H, math.ceil(max(p[1] for p in tutti_i_punti)) + 2)
        else:
            min_x = min_y = 0
            max_x, max_y = CANVAS_W, CANVAS_H
        box_w, box_h = max(1, max_x - min_x), max(1, max_y - min_y)

        img = Image.new("RGBA", (box_w * SUPERSAMPLE, box_h * SUPERSAMPLE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        _hit_tiles.clear()
        for depth_media, el, proiez, nzr in visibili:
            pts = [((sx - min_x) * SUPERSAMPLE, (sy - min_y) * SUPERSAMPLE) for sx, sy, _d in proiez]
            fattore = 0.55 + 0.45 * min(1.0, nzr)
            colore = _shade(el["fill"], fattore)
            outline_col = "#FFFFFF" if el == _pop_anim["active_el"] else el["outline"]
            width_val = 2.5 if el == _pop_anim["active_el"] else 1.3
            draw.polygon(pts, fill=colore, outline=outline_col, width=max(1, round(width_val * SUPERSAMPLE)))

            if el["mod"] is not None:
                pts_2d = [(sx, sy) for sx, sy, _d in proiez]
                _hit_tiles.append((pts_2d, el))

        img_small = img.resize((box_w, box_h), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img_small)
        _render_state["photo"] = photo   # riferimento vivo, altrimenti la GC la cancella
        canvas.create_image(min_x, min_y, anchor="nw", image=photo, tags="scena")

        _hit_tiles.reverse()

        for depth_media, el, proiez, nzr in visibili:
            if el["mod"] is not None:
                dissolvenza = (nzr - SOGLIA_TESTO_MIN) / (SOGLIA_TESTO_PIENA - SOGLIA_TESTO_MIN)
                if dissolvenza > 0.02:
                    nome, desc, cmd = el["mod"]
                    cx = sum(p[0] for p in proiez) / 4
                    cy = sum(p[1] for p in proiez) / 4
                    dx_bordo = proiez[1][0] - proiez[0][0]
                    dy_bordo = proiez[1][1] - proiez[0][1]
                    larghezza = max(1.0, math.hypot(dx_bordo, dy_bordo))
                    dim_font = 8 if larghezza > 110 else (7 if larghezza > 65 else 6)
                    etichetta = nome if larghezza > 130 else nome.split()[0]
                    colore_testo = _blend(bg, el["fg"], dissolvenza)
                    angolo = math.degrees(math.atan2(-dy_bordo, dx_bordo))
                    if angolo > 90:
                        angolo -= 180
                    elif angolo <= -90:
                        angolo += 180
                    canvas.create_text(cx, cy, text=etichetta, font=("Arial", dim_font, "bold"),
                                        fill=colore_testo, tags="scena", width=max(30, larghezza - 6),
                                        justify="center", angle=angolo)

    _drag = {"active": False, "start_x": 0, "last_x": 0, "moved": False}
    _auto = {"on": AUTO_ROTATE, "resume_id": None}

    def _ferma_auto():
        _auto["on"] = False
        if _auto["resume_id"]:
            try: win.after_cancel(_auto["resume_id"])
            except: pass
            _auto["resume_id"] = None

    def _riprendi_auto_tra_poco():
        def _riattiva():
            if not _pop_anim["animating"]:
                _auto["on"] = True
        _auto["resume_id"] = win.after(2500, _riattiva)

    def _avvia_animazione_pop(el, cmd):
        _pop_anim["active_el"] = el
        _pop_anim["offset"] = 0.0
        _pop_anim["animating"] = True
        canvas.config(cursor="")

        TARGET_POP = 45.0
        STEP = 4.5

        def _step():
            if _pop_anim["offset"] < TARGET_POP:
                _pop_anim["offset"] += STEP
                _render()
                win.after(16, _step)
            else:
                def _esegui():
                    win.withdraw()
                    if cmd:
                        cmd()
                win.after(100, _esegui)

        _step()

    def _on_press(event):
        if _pop_anim["animating"]:
            return
        _drag["active"] = True
        _drag["moved"] = False
        _drag["start_x"] = event.x
        _drag["last_x"] = event.x
        _ferma_auto()

    def _on_motion(event):
        if not _drag["active"] or _pop_anim["animating"]:
            return
        dx = event.x - _drag["last_x"]
        if abs(event.x - _drag["start_x"]) > 3:
            _drag["moved"] = True
        theta[0] += dx * VEL_TRASCINAMENTO
        _drag["last_x"] = event.x
        _render()

    def _on_release(event):
        if _pop_anim["animating"]:
            return
        _drag["active"] = False
        if not _drag["moved"]:
            el = _tile_sotto_cursore(event.x, event.y)
            if el is not None:
                _nome, _desc, cmd = el["mod"]
                _tooltip_hide()
                _hover_state["el"] = None
                _ferma_auto()
                _avvia_animazione_pop(el, cmd)
        if not _pop_anim["animating"]:
            _riprendi_auto_tra_poco()

    def _on_hover(event):
        if _drag["active"] or _pop_anim["animating"]:
            return
        el = _tile_sotto_cursore(event.x, event.y)
        if el is _hover_state["el"]:
            return
        _hover_state["el"] = el
        if el is not None:
            nome, desc, cmd = el["mod"]
            _tooltip_show(event, f"{nome}\n{desc}")
            canvas.config(cursor="hand2" if cmd else "")
        else:
            _tooltip_hide()
            canvas.config(cursor="")

    canvas.bind("<ButtonPress-1>", _on_press)
    canvas.bind("<B1-Motion>", _on_motion)
    canvas.bind("<ButtonRelease-1>", _on_release)
    canvas.bind("<Motion>", _on_hover)

    def _auto_step():
        if _auto["on"] and not _drag["active"] and not _pop_anim["animating"]:
            theta[0] += VEL_AUTO
            _render()
        win.after(40, _auto_step)

    legend_x, legend_y = 730, 100
    canvas.create_text(legend_x, legend_y - 26, text="Livelli", font=("Arial", 10, "bold"),
                        fill=fg_title, anchor="w")
    for i, liv in enumerate(LIVELLI):
        ly = legend_y + i * 27
        canvas.create_rectangle(legend_x, ly, legend_x + 14, ly + 14, fill=liv["fill"], outline=liv["outline"])
        canvas.create_text(legend_x + 22, ly + 7, text=f'{liv["label"]}  ({len(liv["moduli"])})',
                            font=("Arial", 9), fill=fg_title, anchor="w")

    totale_moduli = sum(len(l["moduli"]) for l in LIVELLI)
    canvas.create_text(CANVAS_W // 2, CANVAS_H - 18,
                        text=f"{N_LIV} livelli  ·  {totale_moduli} moduli e tool  ·  Python · Tkinter · Flask · Gemini AI",
                        font=("Arial", 8), fill="#BBBBBB", anchor="center")

    img_chiudi = self.icone_gui.get("chiudi")
    btn_chiudi = tk.Label(win, compound="left", image=img_chiudi, text=" Chiudi",
                           background=bg, foreground=fg_title, cursor="hand2",
                           padx=15, pady=6, font=("Arial", 9, "bold"))
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

    _render()
    _auto_step()
