#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageDraw, ImageTk

# Gestione e Visualizzazione Guida Utente (Help) - Piramide 3D interattiva dei moduli
def mostra_piramide(self):

    def _g(nome):
        return getattr(self, nome, None)

    PAGINE = [
        [
            {
                "label": "Cuore dell'app",
                "fill": "#DBEAFE", "outline": "#3B82F6", "fg": "#1E3A5F",
                "moduli": [
                    ("Main",       "Registro movimenti principale",
                     lambda win=None: win.destroy() if win else None),

                    ("Cat.", "Grafico spese per categoria",
                     (lambda: self.toggle_stats_view(tipo="grafico")) if _g("toggle_stats_view") else None),

                    ("Mese",    "Entrate/uscite mese per mese",
                     (lambda: self.toggle_stats_view(tipo="grafico_mensile")) if _g("toggle_stats_view") else None),

                    ("Saldo",      "Andamento saldo mensile",
                     (lambda: self.toggle_stats_view(tipo="grafico_saldo")) if _g("toggle_stats_view") else None),
                ],
            },
            {
                "label": "Patrimonio",
                "fill": "#DCFCE7", "outline": "#22C55E", "fg": "#14532D",
                "moduli": [
                    ("Banca",            "Conti, saldi, trasferimenti",   _g("open_saldo_conto")),
                    ("Invest.",          "yfinance, P&L, AI Gemini",      _g("apri_portafoglio")),
                    ("Risparmi",         "Proiezioni stagionali",         _g("apri_fondo_risparmio")),
                    ("Punti",            "Gamification",                  _g("mostra_dettaglio_gamification")),
                ],
            },
            {
                "label": "Moduli casa",
                "fill": "#FEF9C3", "outline": "#EAB308", "fg": "#713F12",
                "moduli": [
                    ("Utenze",           "Consumi e grafici",         _g("utenze")),
                    ("FairShare",        "Spese condivise e debiti",  _g("mostra_riepilogo_fairshare_periodo")),
                    ("Dieta",            "Pasti, BMI, export PDF",    _g("apri_dieta")),
                    ("Rubrica",          "Contatti, vCard, CRUD",     _g("rubrica_app")),
                ],
            },
            {
                "label": "Strumenti",
                "fill": "#EDE9FE", "outline": "#8B5CF6", "fg": "#2E1065",
                "moduli": [
                    ("Gmail",            "Import AI, Gemini",      (lambda: self.avvia_sincronizzazione(manuale=True)) if _g("avvia_sincronizzazione") else None),
                    ("Schedulatore",     "Task, email, tick",         _g("apri_schedulatore")),
                    ("MyBusiness",       "Clienti, fatture, cassa",   _g("apri_studio")),
                    ("Spesa",            "Spesa Supermercato",        _g("spesa_supermercato")),
                    ("Archivi",          "PDF contabili",             _g("gestisci_archivi_pdf")),
                    ("Personali",        "PDF personali",             _g("gestisci_documenti_personali")),
                ],
            },
            {
                "label": "Utility",
                "fill": "#FEE2E2", "outline": "#EF4444", "fg": "#7F1D1D",
                "moduli": [
                    ("Calcolatrice",     "Integrata",                 _g("apri_calcolatrice")),
                    ("Inflazione",       "ISTAT NIC 2000-2025",       _g("apri_calcolatore_inflazione")),
                    ("Scadenziario",     "Scadenze del mese",         _g("calcola_mancanti")),
                    ("Backup",           "ZIP / JSON restore",        _g("gestisci_backup_popup")),
                    ("Web",              "Flask, PWA, SSL",           _g("apri_webserver")),
                    ("Report",           "Bilancio annuo",            _g("genera_report_pdf")),
                    ("QR",               "Generatore QR",             _g("launch_qr_svg_generator")),
                ],
            },
            {
                "label": "Analisi",
                "fill": "#F3F4F6", "outline": "#9CA3AF", "fg": "#111827",
                "moduli": [
                    ("Online",          "Accesso esterno",       _g("chiama_banca")),
                    ("Grafici",         "Andamento risparmio",   _g("mostra_analisi_grafici")),
                    ("Bilancio IA",     "Bilancio IA Gemini",    _g("analizza_andamento_ia")),
                    ("Ricorrenze",      "Scadenze, notifiche",   _g("mostra_lista_ricorrenze")),
                    ("Immobili",        "Gestione Immobili",     _g("immobil")),
                    ("Veicoli",         "Scadenze e consumi",    _g("veicoli")),
                ],
            },
        ],
        [
            {
                "label": "Finanze extra",
                "fill": "#DCFCE7", "outline": "#22C55E", "fg": "#14532D",
                "moduli": [
                    ("Mutuo",   "Piano di ammortamento", _g("calcolo_mutuo_prestito")),
                    ("Giorno",  "Estratto giornaliero",  _g("export_giorno_forzato")),
                    ("Mese",    "Estratto mensile",      _g("export_month_detail")),
                    ("Anno",    "Estratto annuale",      _g("export_anno_dettagliato")),
                ],
            },
            {
                "label": "Ricerca & Filtri",
                "fill": "#DBEAFE", "outline": "#3B82F6", "fg": "#1E3A5F",
                "moduli": [
                    ("Ricerca",      "Cerca tra tutte le operazioni", _g("cerca_operazioni")),
                    ("Tag",          "Tag delle operazioni",          _g("apri_gestione_tag")),
                    ("Confronta",    "Analisi comparativa",           _g("open_compare_window")),
                    ("Aggrega",      "Raggruppa categorie",           _g("gruppo_categorie")),
                ],
            },
            {
                "label": "Gestione extra",
                "fill": "#FEF9C3", "outline": "#EAB308", "fg": "#713F12",
                "moduli": [
                    ("Promemoria",    "Note e avvisi",          _g("gestisci_promemoria")),
                    ("Importa AI",    "Import Gemini",          _g("apri_finestra_importa")),
                    ("Log Import",    "Storico import",         _g("mostra_log_importazioni")),
                    ("Stampa",        "Anteprima e stampa",     _g("anteprima_e_stampa_txt")),
                ],
            },
            {
                "label": "Analisi extra",
                "fill": "#EDE9FE", "outline": "#8B5CF6", "fg": "#2E1065",
                "moduli": [
                    ("Time Machine",  "Stato storico dati",  _g("time_machine")),
                    ("Andamento",     "Grafico proiezioni",  _g("apri_andamento_risparmio")),
                    ("Fairshare",     "Dare e avere",        _g("mostra_dare_avere")),
                    ("Ricorrenze",    "Crea/modifica",       _g("mostra_ricorrenza_popup")),
                ],
            },
            {
                "label": "Bilanci & Report",
                "fill": "#FEE2E2", "outline": "#EF4444", "fg": "#7F1D1D",
                "moduli": [
                    ("Storico",    "Storico totale",     _g("export_storico_totale")),
                    ("Bilanci",    "Estratti su misura", _g("popup_scelta_estratto")),
                    ("Estratti",   "Filtro per metodo",  _g("apri_estratti_metodo")),
                    ("Confronto",  "OpenAI bollette",    _g("confronta_bollette_ia")),
                ],
            },
            {
                "label": "Ricorrenze & Categ.",
                "fill": "#F3F4F6", "outline": "#9CA3AF", "fg": "#111827",
                "moduli": [
                    ("Scadenze",        "Riepilogo scadenze",         _g("scadenze_mese")),
                    ("Controlla",       "Check manuale",              _g("controlla_ricorrenti_manual")),
                    ("Editor",          "Regole di categorizzazione", _g("mostra_editor_memoria_categorie")),
                    ("Categorie",       "Spesa per categoria",        _g("open_analisi_categoria")),
                ],
            },
        ],
        [
            {
                "label": "Database",
                "fill": "#EDE9FE", "outline": "#8B5CF6", "fg": "#2E1065",
                "moduli": [
                    ("Esporta",     "Esporta transazioni",    _g("export_db")),
                    ("Importa",     "Importa transazioni",    _g("import_db")),
                    ("Reset",       "Azzera database",        _g("show_reset_dialog")),
                    ("Bulk",        "Elimina voci multiple",  _g("apri_cancella_spese_treeview_unica")),
                ],
            },
            {
                "label": "Aggiornamenti",
                "fill": "#DCFCE7", "outline": "#22C55E", "fg": "#14532D",
                "moduli": [
                    ("Update",          "Verifica nuova versione", _g("forza_check_aggiornamento_con_api")),
                    ("Forza Agg.",      "Aggiorna subito",         _g("forza_aggiorna")),
                    ("Annulla Agg.",    "Ripristina backup",       _g("ripristina_da_backup")),
                    ("Storico Upd.",    "Changelog",               _g("visualizza_changelog")),
                ],
            },
            {
                "label": "Log & Diagnostica",
                "fill": "#FEF9C3", "outline": "#EAB308", "fg": "#713F12",
                "moduli": [
                    ("Anomalie",   "Errori applicativi",    _g("mostra_registro_errori")),
                    ("Log Accessi","Accessi web",           _g("mostra_log_accessi")),
                    ("Librerie",   "Aggiorna dipendenze",   _g("aggiorna_librerie_pip")),
                    ("Verifica",   "Controllo GitHub",      _g("verifica_moduli_git")),
                ],
            },
            {
                "label": "App",
                "fill": "#DBEAFE", "outline": "#3B82F6", "fg": "#1E3A5F",
                "moduli": [
                    ("Impostazioni",      "Configurazione app",      _g("gestisci_configurazione")),
                    ("Password",          "Sicurezza account",       _g("apri_cambio_password")),
                    ("Profili",           "Gestisci Profili Utenti", _g("mostra_selettore_profilo")),
                    ("Registra",          "Attivazione licenza",     _g("apri_registrazione")),
                    ("Assistenza",        "Supporto",               (lambda: self.apri_pannello_topic(self.topic_unico)) if _g("apri_pannello_topic") else None),
                ],
            },
            {
                "label": "Backup & Web",
                "fill": "#FEE2E2", "outline": "#EF4444", "fg": "#7F1D1D",
                "moduli": [
                    ("Backup Zip",            "Backup completo",           _g("esegui_backup_zip")),
                    ("Gestione Certificati",  "Gestione certificati",      _g("gestisci_certificati")),
                    ("Connessione Web",       "QR per accesso web",        _g("mostra_qr_popup_label")),
                    ("Manuale certificati",   "Guida CertBot",             _g("scarica_manuale_ssl")),
                ],
            },
            {
                "label": "Categorie avanzate",
                "fill": "#F3F4F6", "outline": "#9CA3AF", "fg": "#111827",
                "moduli": [
                    ("Suggerisci Categorie",     "Suggerimenti automatici categorie",  _g("apri_categorie_suggerite")),
                    ("Categorie",                "CRUD categorie",                     _g("mostra_categorie_popup")),
                    ("Cancella Multiplo",        "Eliminazione multipli movimenti",    _g("apri_cancella_multiplo")),
                    ("Apri Manuale",             "Guida utente",                       _g("scarica_manuale")),
                ],
            },
        ],
    ]

    NOMI_PAGINE = ["Panoramica", "Gestione & Analisi", "Sistema & Database"]
    NOMI_PAGINE_BREVI = ["Panoramica", "Gestione", "Sistema"]
    N_PAGINE = len(PAGINE)

    CANVAS_W, CANVAS_H = 900, 615
    BASE_HALF = 200.0
    LEVEL_H   = 65.0
    MARGINE_V = 0.06
    CAM_D, FOCAL = 900.0, 760.0
    ELEV = math.radians(22)
    VEL_TRASCINAMENTO = 0.008
    AUTO_ROTATE = True
    VEL_AUTO = 0.05
    SUPERSAMPLE = 2

    N_LIV = len(PAGINE[0])
    SPACER_FRAC_APICE = 0.6

    bg       = self.COLOR_BACKGROUND
    fg_title = self.TEXT_COLOR
    color_hi = getattr(self, "COLOR_HIGHLIGHT", "#3B82F6")

    win = tk.Toplevel(self)
    win.withdraw()
    win.title("Panoramica Moduli")
    win.configure(bg=bg)
    win.resizable(False, False)
    win.overrideredirect(True)
    win.bind("<Escape>", lambda e: win.destroy())
    win.bind("<Unmap>", lambda e: _tooltip_hide())

    _focus_stato = {"pronto": False}

    def _on_focus_out(event):
        if event.widget is not win or not _focus_stato["pronto"]:
            return
        _tooltip_hide()
        win.after(60, _verifica_focus_e_chiudi)

    def _verifica_focus_e_chiudi():
        if not _focus_stato["pronto"]:
            return
        try:
            focus_attuale = win.focus_get()
        except tk.TclError:
            focus_attuale = None
        if focus_attuale is None or not str(focus_attuale).startswith(str(win)):
            try:
                win.destroy()
            except tk.TclError:
                pass

    win.bind("<FocusOut>", _on_focus_out)

    canvas = tk.Canvas(win, width=CANVAS_W, height=CANVAS_H, bg=bg, highlightthickness=0)
    canvas.pack(padx=0, pady=0)

    titolo_id = canvas.create_text(40, 25,
                       text="Panoramica Moduli",
                       font=("Arial", 15, "bold"), fill=fg_title, anchor="w")

    canvas.create_text(CANVAS_W - 40, 25,
                       text="Trascina per ruotare  ·  Clicca per aprire  ·  Cerca per orientare",
                       font=("Arial", 9), fill="#888888", anchor="e")

    canvas.create_text(40, 52, text="Cerca modulo:", font=("Arial", 9), fill="#888888", anchor="w")
    search_var = tk.StringVar()
    entry_ricerca = ttk.Entry(canvas, textvariable=search_var, width=18, font=("Arial", 9))
    canvas.create_window(120, 52, anchor="w", window=entry_ricerca)

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

    TOTAL_H = LEVEL_H * (N_LIV + SPACER_FRAC_APICE)
    Y_BOUND = [i * LEVEL_H - TOTAL_H / 2 for i in range(N_LIV + 1)]
    Y_BOUND.append(Y_BOUND[-1] + SPACER_FRAC_APICE * LEVEL_H)  # vera punta (cappuccio cieco)
    W_BOUND = [BASE_HALF * (1 - i / (N_LIV + SPACER_FRAC_APICE)) for i in range(N_LIV + 1)]
    W_BOUND.append(0.0)

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

    def _costruisci_elementi(livelli):
        livelli_base_apice = list(reversed(livelli))
        elementi_pagina = []
        for liv_idx, livello in enumerate(livelli_base_apice):
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
                    elementi_pagina.append({
                        "corners": corners,
                        "normal": NORMALI[direzione],
                        "fill": livello["fill"],
                        "outline": livello["outline"],
                        "fg": livello["fg"],
                        "mod": mod,
                    })
        ultimo = livelli_base_apice[-1]
        y_bot, y_top = Y_BOUND[N_LIV], Y_BOUND[N_LIV + 1]
        hb, ht = W_BOUND[N_LIV], W_BOUND[N_LIV + 1]
        dy = (y_top - y_bot) * MARGINE_V
        ry_bot, ry_top = y_bot + dy, y_top - dy

        def _size_at_apice(y, y_bot=y_bot, y_top=y_top, hb=hb, ht=ht):
            t = (y - y_bot) / (y_top - y_bot)
            return hb + (ht - hb) * t
        rhb, rht = _size_at_apice(ry_bot), _size_at_apice(ry_top)

        for direzione in FACCE:
            corners = [
                _punto_faccia(direzione, -1, ry_bot, rhb, rht, ry_bot, ry_top),
                _punto_faccia(direzione, 1, ry_bot, rhb, rht, ry_bot, ry_top),
                _punto_faccia(direzione, 1, ry_top, rhb, rht, ry_bot, ry_top),
                _punto_faccia(direzione, -1, ry_top, rhb, rht, ry_bot, ry_top),
            ]
            elementi_pagina.append({
                "corners": corners,
                "normal": NORMALI[direzione],
                "fill": ultimo["fill"],
                "outline": ultimo["outline"],
                "fg": ultimo["fg"],
                "mod": None,
            })
        return elementi_pagina

    _elementi_per_pagina = [_costruisci_elementi(p) for p in PAGINE]

    stato = {"pagina": 0, "livelli": PAGINE[0], "elementi": _elementi_per_pagina[0]}

    CX, CY = 350, 270
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

    def _tooltip_show(x, y, widget, txt):
        if _tip_win[0]:
            try: _tip_win[0].destroy()
            except: pass
            _tip_win[0] = None
        if _tip_win[1]:
            try: widget.after_cancel(_tip_win[1])
            except: pass
            _tip_win[1] = None
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
        for el in stato["elementi"]:
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
            if el == _pop_anim["active_el"]:
                outline_col, width_val = "#FFFFFF", 2.5
            elif el == _search_state["el"]:
                impulso = 0.5 + 0.5 * math.sin(_blink_state["fase"])
                outline_col = _blend(el["outline"], "#FFFFFF", 0.45 + 0.55 * impulso)
                width_val = 1.8 + 1.6 * impulso
            else:
                outline_col, width_val = el["outline"], 1.3
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
                    cx = proiez[0][0] * 0.35 + proiez[1][0] * 0.35 + proiez[2][0] * 0.15 + proiez[3][0] * 0.15
                    cy = proiez[0][1] * 0.35 + proiez[1][1] * 0.35 + proiez[2][1] * 0.15 + proiez[3][1] * 0.15
                    dx_bordo = proiez[1][0] - proiez[0][0]
                    dy_bordo = proiez[1][1] - proiez[0][1]
                    larghezza = max(1.0, math.hypot(dx_bordo, dy_bordo))
                    dx_top = proiez[2][0] - proiez[3][0]
                    dy_top = proiez[2][1] - proiez[3][1]
                    larghezza_top = math.hypot(dx_top, dy_top)
                    larghezza_min = min(larghezza, larghezza_top if larghezza_top > 0.5 else larghezza)
                    if larghezza_top < 18:
                        continue
                    larghezza = larghezza_min
                    dim_font = 8 if larghezza > 110 else (7 if larghezza > 65 else 6)
                    etichetta = nome if larghezza > 130 else nome.split()[0]
                    colore_testo = _blend(bg, el["fg"], dissolvenza)
                    angolo = math.degrees(math.atan2(-dy_bordo, dx_bordo))
                    if angolo > 90:
                        angolo -= 180
                    elif angolo <= -90:
                        angolo += 180
                    canvas.create_text(cx, cy, text=etichetta, font=("Arial", dim_font, "bold"),
                                        fill=colore_testo, tags="scena", width=max(12, larghezza - 4),
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

    _search_state = {"el": None, "anim_id": 0}
    _blink_state = {"fase": 0.0}

    def _cerca_modulo_globale(testo):
        testo = testo.strip().lower()
        if not testo:
            return None
        for pagina_idx, elementi_pagina in enumerate(_elementi_per_pagina):
            for el in elementi_pagina:
                if el["mod"] is None:
                    continue
                nome, desc, _cmd = el["mod"]
                if testo in nome.lower() or testo in desc.lower():
                    return pagina_idx, el
        return None

    def _theta_per_normale(n):
        nx, _ny, nz = n
        return -math.atan2(nx, nz)

    def _ruota_verso(theta_target, el):
        if _pop_anim["animating"]:
            return
        _ferma_auto()
        _search_state["el"] = el
        _search_state["anim_id"] += 1
        id_animazione = _search_state["anim_id"]
        theta_iniziale = theta[0]
        delta = theta_target - theta_iniziale
        delta = (delta + math.pi) % (2 * math.pi) - math.pi
        n_frame = 14
        frame = [0]

        def _step():
            if id_animazione != _search_state["anim_id"]:
                return
            frame[0] += 1
            t = min(1.0, frame[0] / n_frame)
            ease = 1 - (1 - t) ** 3
            theta[0] = theta_iniziale + delta * ease
            _render()
            if t < 1.0:
                win.after(16, _step)

        _step()

    def _on_ricerca_cambiata(*_args):
        testo = search_var.get()
        trovato = _cerca_modulo_globale(testo)
        if trovato is not None:
            pagina_idx, el = trovato
            if el is not _search_state["el"]:
                if pagina_idx != stato["pagina"]:
                    _vai_a_pagina(pagina_idx)
                _ruota_verso(_theta_per_normale(el["normal"]), el)
        else:
            if _search_state["el"] is not None:
                _search_state["el"] = None
                _render()
            if not testo.strip():
                _riprendi_auto_tra_poco()

    def _apri_da_ricerca(event=None):
        el = _search_state["el"]
        if el is not None and not _pop_anim["animating"]:
            _nome, _desc, cmd = el["mod"]
            _avvia_animazione_pop(el, cmd)

    def _pulisci_ricerca(event=None):
        if search_var.get():
            search_var.set("")
            return "break"
        return None

    def _blink_step():
        if _search_state["el"] is not None:
            _blink_state["fase"] += 0.18
            _render()
        win.after(50, _blink_step)

    search_var.trace_add("write", _on_ricerca_cambiata)
    entry_ricerca.bind("<Return>", _apri_da_ricerca)
    entry_ricerca.bind("<Escape>", _pulisci_ricerca)
    entry_ricerca.bind(
        "<FocusOut>",
        lambda e: _riprendi_auto_tra_poco() if not search_var.get().strip() else None,
    )

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

    _mouse_pos = {"x": None, "y": None}

    def _aggiorna_hover(x, y):
        el = _tile_sotto_cursore(x, y)
        if el is _hover_state["el"]:
            return
        _hover_state["el"] = el
        if el is not None:
            nome, desc, cmd = el["mod"]
            x_root = canvas.winfo_rootx() + x
            y_root = canvas.winfo_rooty() + y
            _tooltip_show(x_root, y_root, canvas, f"{nome}\n{desc}")
            canvas.config(cursor="hand2" if cmd else "")
        else:
            _tooltip_hide()
            canvas.config(cursor="")

    def _on_hover(event):
        _mouse_pos["x"], _mouse_pos["y"] = event.x, event.y
        if _drag["active"] or _pop_anim["animating"]:
            return
        _aggiorna_hover(event.x, event.y)

    def _on_leave(event):
        _mouse_pos["x"] = _mouse_pos["y"] = None
        _hover_state["el"] = None
        _tooltip_hide()
        canvas.config(cursor="")

    canvas.bind("<ButtonPress-1>", _on_press)
    canvas.bind("<B1-Motion>", _on_motion)
    canvas.bind("<ButtonRelease-1>", _on_release)
    canvas.bind("<Motion>", _on_hover)
    canvas.bind("<Leave>", _on_leave)

    def _auto_step():
        if _auto["on"] and not _drag["active"] and not _pop_anim["animating"]:
            theta[0] += VEL_AUTO
            _render()
            if _mouse_pos["x"] is not None:
                _aggiorna_hover(_mouse_pos["x"], _mouse_pos["y"])
        win.after(40, _auto_step)

    SEL_Y, SEL_BTN_W, SEL_BTN_H, SEL_GAP = 50, 100, 22, 8
    sel_tot_w = N_PAGINE * SEL_BTN_W + (N_PAGINE - 1) * SEL_GAP
    sel_x0 = (CANVAS_W - sel_tot_w) / 2

    def _disegna_selettore():
        canvas.delete("selettore")
        for i in range(N_PAGINE):
            x0 = sel_x0 + i * (SEL_BTN_W + SEL_GAP)
            x1 = x0 + SEL_BTN_W
            attiva = (i == stato["pagina"])
            fill = color_hi if attiva else "#E5E7EB"
            fg_txt = "#FFFFFF" if attiva else "#4B5563"
            tag = f"pgbtn_{i}"
            canvas.create_rectangle(x0, SEL_Y, x1, SEL_Y + SEL_BTN_H,
                                     fill=fill, outline="", tags=("selettore", tag))
            canvas.create_text((x0 + x1) / 2, SEL_Y + SEL_BTN_H / 2,
                                text=f"{i + 1}. {NOMI_PAGINE_BREVI[i]}",
                                font=("Arial", 8, "bold"), fill=fg_txt,
                                tags=("selettore", tag))
            canvas.tag_bind(tag, "<Button-1>", lambda e, i=i: _vai_a_pagina(i))
            canvas.tag_bind(tag, "<Enter>", lambda e: canvas.config(cursor="hand2"))
            canvas.tag_bind(tag, "<Leave>", lambda e: canvas.config(cursor=""))

    def _disegna_legenda_e_conteggio():
        canvas.delete("legenda")
        legend_x, legend_y = 730, 135
        canvas.create_text(legend_x, legend_y - 26, text="Livelli", font=("Arial", 10, "bold"),
                            fill=fg_title, anchor="w", tags="legenda")
        for i, liv in enumerate(stato["livelli"]):
            ly = legend_y + i * 27
            canvas.create_rectangle(legend_x, ly, legend_x + 14, ly + 14,
                                     fill=liv["fill"], outline=liv["outline"], tags="legenda")
            canvas.create_text(legend_x + 22, ly + 7, text=f'{liv["label"]}  ({len(liv["moduli"])})',
                                font=("Arial", 9), fill=fg_title, anchor="w", tags="legenda")

        totale_moduli = sum(len(l["moduli"]) for l in stato["livelli"])
        canvas.create_text(CANVAS_W // 2, CANVAS_H - 18,
                            text=f"{N_LIV} livelli  ·  {totale_moduli} moduli in questa pagina  ·  "
                                 f"Pagina {stato['pagina'] + 1}/{N_PAGINE}: {NOMI_PAGINE[stato['pagina']]}",
                            font=("Arial", 8), fill="#BBBBBB", anchor="center", tags="legenda")

    def _vai_a_pagina(nuova):
        if nuova == stato["pagina"] or _pop_anim["animating"] or not (0 <= nuova < N_PAGINE):
            return
        stato["pagina"] = nuova
        stato["livelli"] = PAGINE[nuova]
        stato["elementi"] = _elementi_per_pagina[nuova]
        _search_state["el"] = None
        _tooltip_hide()
        _hover_state["el"] = None
        _disegna_selettore()
        _disegna_legenda_e_conteggio()
        canvas.itemconfigure(titolo_id, text=f"Panoramica Moduli — {NOMI_PAGINE[nuova]}")
        _render()

    def _pagina_successiva(event=None):
        _vai_a_pagina((stato["pagina"] + 1) % N_PAGINE)

    def _pagina_precedente(event=None):
        _vai_a_pagina((stato["pagina"] - 1) % N_PAGINE)

    win.bind("<Right>", _pagina_successiva)
    win.bind("<Left>", _pagina_precedente)
    for i in range(N_PAGINE):
        win.bind(str(i + 1), lambda e, i=i: _vai_a_pagina(i))

    _disegna_selettore()
    _disegna_legenda_e_conteggio()

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
    win.after(350, lambda: _focus_stato.__setitem__("pronto", True))

    _render()
    _auto_step()
    _blink_step()
