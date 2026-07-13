#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
import datetime
from collections import defaultdict

def draw_bar_chart(self, event=None):
    if self.stats_view_mode.get() != "grafico":
        return
    if getattr(self, '_drawing_bar', False) or not self.stats_canvas.winfo_exists():
        return
    if event is not None and not hasattr(self, '_interno_ciclo'):
        self.stats_step = 0
        self.visualizza_tutti_gli_anni = False
    self._drawing_bar = True
    try:
        canvas = self.stats_canvas
        canvas.xview_moveto(0)
        canvas.update_idletasks()
        canvas.delete("all")
        for child in canvas.winfo_children():
            child.destroy()
        def ciclo_viste():
            if not canvas.winfo_exists(): return
            self.stats_step = (self.stats_step + 1) % 4
            self.visualizza_tutti_gli_anni = self.stats_step in [1, 3]
            self._interno_ciclo = True
            self.draw_bar_chart()
            if hasattr(self, '_interno_ciclo'): del self._interno_ciclo
        category_totals = defaultdict(float)
        income_totals = defaultdict(float)
        oggi = datetime.date.today()
        anno_corrente = oggi.year
        anni_presenti = [g.year for g in self.spese.keys() if hasattr(g, 'year')]
        min_anno = min(anni_presenti) if anni_presenti else anno_corrente
        periodo_str = f"{min_anno} - {anno_corrente}" if self.visualizza_tutti_gli_anni else str(anno_corrente)
        for giorno, entries in self.spese.items():
            if hasattr(giorno, "year") and (self.visualizza_tutti_gli_anni or giorno.year == anno_corrente):
                for entry in entries:
                        if isinstance(entry, dict):
                            cat, imp, tipo = entry.get("categoria", "Altro"), entry.get("importo", 0), entry.get("tipo", "")
                        elif not isinstance(entry, dict) and len(entry) >= 4:
                            cat, imp, tipo = entry[0], entry[2], entry[3]
                        else:
                            continue
                        if not self.considera_ricorrenze_var.get() and giorno > datetime.date.today():
                            continue
                        try: imp = float(str(imp).replace(",", ".").replace("€", "").strip())
                        except: imp = 0
                        if str(tipo).lower() == "uscita" and imp > 0:
                            category_totals[cat] += imp
                        elif str(tipo).lower() == "entrata" and imp > 0:
                            income_totals[cat] += imp
        data_out = sorted([{'label': k, 'value': v} for k, v in category_totals.items() if v > 0], key=lambda x: x['value'], reverse=True)
        data_in = sorted([{'label': k, 'value': v} for k, v in income_totals.items() if v > 0], key=lambda x: x['value'], reverse=True)
        BAR_SPACE, CHART_LEFT = 40, 50
        c_height = canvas.winfo_height()
        if c_height < 200: c_height = 400
        c_width = canvas.winfo_width() if canvas.winfo_width() > 10 else 800
        CHART_TOP, CHART_BOTTOM = 80, c_height - 120 
        CHART_HEIGHT = CHART_BOTTOM - CHART_TOP
        num_bars = len(data_out) if self.stats_step < 2 else (len(data_out) + len(data_in))
        total_draw_width = CHART_LEFT + (num_bars * BAR_SPACE) + 150
        canvas.config(scrollregion=(0, 0, total_draw_width, c_height))
        titoli = [" Uscite per Categoria", " Uscite Storico", " Bilancio Anno", "Bilancio Storico"]
        testi_btn = [" Passa a Storico", " Bilancio Anno", " Bilancio Storico", " Torna a Categorie"]
        lbl_titolo = tk.Label(canvas, text=f"{titoli[self.stats_step]} ({periodo_str})", font=("Arial", 9, "bold"), bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR, padx=5)
        img_mouse = self.icone_gui.get("mouse")
        lbl_hint = tk.Label(
            canvas,
            text="Doppio clic → Mostra Dettaglio ",
            image=img_mouse,
            compound="right",
            fg="grey",
            bg=self.COLOR_WIDGET_BG,
            font=("Arial", 9, "italic")
        )
        self.win_titolo = canvas.create_window(10, 10, window=lbl_titolo, anchor="nw")
        self.win_hint = canvas.create_window(220, 10, window=lbl_hint, anchor="nw")
        icone_step = ["grafico_linea", "saldo", "documenti", "report"]
        img_btn = self.icone_gui.get(icone_step[self.stats_step])
        btn_toggle = tk.Label(
            canvas,
            image=img_btn if img_btn else None,
            text=testi_btn[self.stats_step],
            compound="left",
            cursor="hand2",
            bg=self.COLOR_WIDGET_BG,
            fg=self.TEXT_COLOR,
            font=("Arial", 9, "bold")
        )
        if img_btn:
            btn_toggle.image = img_btn
        btn_toggle.bind("<Button-1>", lambda e: ciclo_viste())
        self.win_btn = canvas.create_window(c_width - 10, 10, window=btn_toggle, anchor="ne")
        t_in, t_out = sum(x['value'] for x in data_in), sum(x['value'] for x in data_out)
        saldo = t_in - t_out
        col_saldo = "#28a745" if saldo >= 0 else "#dc3545"
        frame_tot = tk.Frame(canvas, bg=self.COLOR_WIDGET_BG)
        if self.stats_step < 2:
            tk.Label(frame_tot, text=f"Totale Uscite: € {t_out:,.2f}", font=("Arial", 9, "bold"), fg="#dc3545", bg=self.COLOR_WIDGET_BG).pack(side="left")
        else:
            tk.Label(frame_tot, text=f"Entrate: € {t_in:,.2f}", font=("Arial", 9, "bold"), fg="#28a745", bg=self.COLOR_WIDGET_BG).pack(side="left")
            tk.Label(frame_tot, text=" | ", font=("Arial", 9), bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR).pack(side="left")
            tk.Label(frame_tot, text=f"Uscite: € {t_out:,.2f}", font=("Arial", 9, "bold"), fg="#dc3545", bg=self.COLOR_WIDGET_BG).pack(side="left")
            tk.Label(frame_tot, text=" | Saldo: ", font=("Arial", 9, "bold"), bg=self.COLOR_WIDGET_BG, fg=col_saldo).pack(side="left")
            col_saldo = "#28a745" if saldo >= 0 else "#dc3545"
            tk.Label(frame_tot, text=f"€ {saldo:,.2f}", font=("Arial", 9, "bold"), fg=col_saldo, bg=self.COLOR_WIDGET_BG).pack(side="left")
        self.win_totale = canvas.create_window(10, c_height - 10, window=frame_tot, anchor="sw")
        visible_vals = [x['value'] for x in data_out] if self.stats_step < 2 else [x['value'] for x in data_out + data_in]
        max_v = max(visible_vals) if visible_vals else 1
        canvas.create_line(CHART_LEFT, CHART_BOTTOM, total_draw_width - 100, CHART_BOTTOM, width=2, fill="#AAAAAA")
        COLORS = ["#36A2EB", "#FF6384", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40"]
        def draw_item(x, val, label, color, tipo):
            h_barra = max((val / max_v) * CHART_HEIGHT, 4)
            tag = f"bar_{x}"
            canvas.create_rectangle(x-18, CHART_BOTTOM-h_barra, x+18, CHART_BOTTOM, fill=color, outline="#333", tags=tag)
            canvas.create_text(x, CHART_BOTTOM + 5, text=label, anchor="ne", angle=45, font=("Arial", 7, "bold"), fill=color)
            canvas.create_text(x, CHART_BOTTOM-h_barra-5, text=f"€{val:.0f}", anchor="s", font=("Arial", 7, "bold"), fill=self.TEXT_COLOR)
            tooltip_txt = f"{label}: €{val:,.2f}"
            canvas.tag_bind(tag, "<Enter>", lambda e, t=tooltip_txt: self.show_tooltip(e, t))
            canvas.tag_bind(tag, "<Leave>", lambda e: self.hide_tooltip())
            filtro = {"anno": None if self.visualizza_tutti_gli_anni else str(anno_corrente), "categoria": label, "tipo": tipo}
            canvas.tag_bind(tag, "<Double-1>", lambda e, f=filtro, l=label: self.mostra_transazioni_popup(f, f"Dettaglio {l}"))
        if self.stats_step < 2:
            for i, item in enumerate(data_out):
                draw_item(CHART_LEFT + (i * BAR_SPACE) + 20, item['value'], item['label'], COLORS[i % len(COLORS)], "Uscita")
        else:
            for i, item in enumerate(data_in):
                draw_item(CHART_LEFT + (i * BAR_SPACE) + 20, item['value'], item['label'], "#28a745", "Entrata")
            sep_x = CHART_LEFT + (len(data_in) * BAR_SPACE) + 20
            canvas.create_line(sep_x, CHART_BOTTOM, sep_x, CHART_TOP, dash=(4,4), fill="#ccc")
            for i, item in enumerate(data_out):
                draw_item(sep_x + 40 + (i * BAR_SPACE), item['value'], item['label'], COLORS[i % len(COLORS)], "Uscita")
        def update_sticky(event=None):
            if not canvas.winfo_exists(): return
            ox = canvas.canvasx(0)
            canvas.coords(self.win_titolo, ox + 10, 10)
            canvas.coords(self.win_btn, ox + canvas.winfo_width() - 10, 10)
            canvas.coords(self.win_totale, ox + 10, canvas.winfo_height() - 10)
        canvas.config(xscrollcommand=lambda f, l: (self.hsb_stats.set(f, l), update_sticky() if canvas.winfo_exists() else None))
        self.hsb_stats.config(command=lambda *args: (canvas.xview(*args), update_sticky()) if canvas.winfo_exists() else None)
        update_sticky()
    finally:
        self._drawing_bar = False

def draw_mensile_chart(self, event=None):
    if self.stats_view_mode.get() != "grafico_mensile":
        return
    if getattr(self, '_drawing_mensile', False):
        return
    self._drawing_mensile = True
    try:
        canvas = self.stats_canvas
        canvas.xview_moveto(0)
        canvas.update_idletasks()
        canvas.delete("all")
        for child in canvas.winfo_children():
            child.destroy()
        mesi_completi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                         "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
        if not hasattr(self, 'visualizza_tutti_gli_anni_mensile'):
            self.visualizza_tutti_gli_anni_mensile = False
        def toggle_anni():
            self.visualizza_tutti_gli_anni_mensile = not self.visualizza_tutti_gli_anni_mensile
            self.draw_mensile_chart()
        oggi = datetime.date.today()
        anno_corrente = oggi.year
        if self.visualizza_tutti_gli_anni_mensile:
            aggregati = {}
            for giorno, entries in self.spese.items():
                if hasattr(giorno, "year"):
                    anno = giorno.year
                    if anno not in aggregati:
                        aggregati[anno] = {"label": str(anno), "entrata": 0.0, "uscita": 0.0}
                    for entry in entries:
                        tipo = entry[3] if not isinstance(entry, dict) else entry.get("tipo", "")
                        importo = float(entry[2]) if not isinstance(entry, dict) and len(entry) >= 4 else float(entry.get("importo", 0))
                        if not self.considera_ricorrenze_var.get() and giorno > datetime.date.today():
                            continue
                        if tipo == "Entrata":
                            aggregati[anno]["entrata"] += importo
                        elif tipo == "Uscita":
                            aggregati[anno]["uscita"] += importo
            self.data_for_chart = [aggregati[anno] for anno in sorted(aggregati)]
        else:
            mesi_brevi = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
            mensili = [{"label": m, "entrata": 0.0, "uscita": 0.0} for m in mesi_brevi]
            for giorno, entries in self.spese.items():
                if hasattr(giorno, "year") and giorno.year == anno_corrente:
                    mese_index = giorno.month - 1
                    for entry in entries:
                        tipo = entry[3] if not isinstance(entry, dict) else entry.get("tipo", "")
                        importo = float(entry[2]) if not isinstance(entry, dict) and len(entry) >= 4 else float(entry.get("importo", 0))
                        if not self.considera_ricorrenze_var.get() and giorno > datetime.date.today():
                            continue
                        if tipo == "Entrata":
                            mensili[mese_index]["entrata"] += importo
                        elif tipo == "Uscita":
                            mensili[mese_index]["uscita"] += importo
            self.data_for_chart = mensili
        c_width = canvas.winfo_width() if canvas.winfo_width() > 10 else 800
        c_height = canvas.winfo_height() if canvas.winfo_height() > 10 else 400
        CHART_LEFT = 50
        CHART_RIGHT = c_width - 10
        CHART_TOP = 60
        CHART_BOTTOM = c_height - 80
        CHART_AREA_WIDTH = CHART_RIGHT - CHART_LEFT
        CHART_HEIGHT = CHART_BOTTOM - CHART_TOP
        if not self.data_for_chart or all(item["entrata"] == 0 and item["uscita"] == 0 for item in self.data_for_chart):
            canvas.create_text(c_width // 2, c_height // 2, text="Nessun dato disponibile.", font=("Arial", 12), fill="#AAAAAA")
            return
        img_mensile = self.icone_gui.get("oggi" if not self.visualizza_tutti_gli_anni_mensile else "calendario")
        btn_text = " Tutti gli anni" if not self.visualizza_tutti_gli_anni_mensile else " Solo anno corrente"
        btn_toggle = tk.Label(
            canvas,
            image=img_mensile if img_mensile else None,
            text=btn_text,
            compound="left",
            cursor="hand2",
            bg=self.COLOR_WIDGET_BG,
            fg=self.TEXT_COLOR,
            font=("Arial", 9, "bold")
        )
        if img_mensile:
            btn_toggle.image = img_mensile
        btn_toggle.bind("<Button-1>", lambda e: toggle_anni())
        self.win_btn_mensile = canvas.create_window(c_width - 10, 10, window=btn_toggle, anchor="ne")
        titolo_g = f"Movimenti Entrate/Uscite per Mese ({anno_corrente})"
        if self.visualizza_tutti_gli_anni_mensile:
            anni_p = [item["label"] for item in self.data_for_chart]
            label_p = f"({anni_p[0]} - {anni_p[-1]})" if anni_p else ""
            titolo_g = f"Movimenti Entrate/Uscite Aggregate per Anno {label_p}"
        frame_titolo = tk.Frame(canvas, bg=self.COLOR_WIDGET_BG)
        tk.Label(frame_titolo, text=titolo_g, font=("Arial", 9, "bold"),
                 bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR, padx=5).pack(side="left")
        img_mouse = self.icone_gui.get("mouse")
        tk.Label(frame_titolo,
                 text="  •  Doppio clic → Mostra Dettaglio ",
                 image=img_mouse,
                 compound="right",
                 background=self.COLOR_WIDGET_BG,
                 foreground="gray",
                 font=("Arial", 9, "italic")).pack(side="left")
        canvas.create_window(canvas.winfo_reqwidth() // 2, 10, window=frame_titolo, anchor="n")
        self.win_titolo_mensile = canvas.create_window(10, 10, window=frame_titolo, anchor="nw")
        max_value = max(max(item["entrata"], item["uscita"]) for item in self.data_for_chart)
        if max_value == 0: max_value = 1
        num_bars = len(self.data_for_chart)
        bar_space_total = CHART_AREA_WIDTH / num_bars
        bar_width = (bar_space_total * 0.95) / 2
        canvas.create_line(CHART_LEFT, CHART_BOTTOM, CHART_LEFT, CHART_TOP, fill=self.TEXT_COLOR, width=2)
        canvas.create_line(CHART_LEFT, CHART_BOTTOM, CHART_RIGHT, CHART_BOTTOM, fill=self.TEXT_COLOR, width=2)
        for i, item in enumerate(self.data_for_chart):
            x_center = CHART_LEFT + (i + 0.5) * bar_space_total
            h_e = max((item["entrata"] / max_value) * CHART_HEIGHT, 4 if item["entrata"] > 0 else 0)
            h_u = max((item["uscita"] / max_value) * CHART_HEIGHT, 4 if item["uscita"] > 0 else 0)         
            tag_e, tag_u = f"e_{i}", f"u_{i}"
            rect_e = canvas.create_rectangle(x_center-bar_width, CHART_BOTTOM-h_e, x_center, CHART_BOTTOM, 
                                             fill="green", outline="black", tags=tag_e)
            rect_u = canvas.create_rectangle(x_center, CHART_BOTTOM-h_u, x_center+bar_width, CHART_BOTTOM, 
                                             fill="red", outline="black", tags=tag_u)
            canvas.create_text(x_center, CHART_BOTTOM + 5, text=item["label"], anchor="ne", angle=45, font=("Arial", 8), fill=self.TEXT_COLOR)
            if item['entrata'] > 0:
                canvas.create_text(x_center - bar_width/2, CHART_BOTTOM-h_e-5, text=f"{item['entrata']:.0f}", 
                                    anchor="s", font=("Arial", 7), fill="green")
            if item['uscita'] > 0:
                canvas.create_text(x_center + bar_width/2, CHART_BOTTOM-h_u-5, text=f"{item['uscita']:.0f}", 
                                    anchor="s", font=("Arial", 7), fill="red")
            if self.visualizza_tutti_gli_anni_mensile:
                f_anno, f_mese = item["label"], None
                p_text = f"Anno {item['label']}"
            else:
                f_anno, f_mese = str(anno_corrente), i + 1
                p_text = f"{mesi_completi[i]} {anno_corrente}"
            canvas.tag_bind(tag_e, "<Double-1>", lambda e, a=f_anno, m=f_mese, t=p_text: 
                self.mostra_transazioni_popup({"anno": a, "mese": m, "categoria": None, "tipo": "Entrata"}, f"Transazioni {t} - Solo Entrate"))
            canvas.tag_bind(tag_u, "<Double-1>", lambda e, a=f_anno, m=f_mese, t=p_text: 
                self.mostra_transazioni_popup({"anno": a, "mese": m, "categoria": None, "tipo": "Uscita"}, f"Transazioni {t} - Solo Uscite"))
            canvas.tag_bind(tag_e, "<Enter>", lambda e, v=item['entrata'], l=item['label']: self.show_tooltip(e, f"{l} - Entrata: €{v:,.2f}"))
            canvas.tag_bind(tag_e, "<Leave>", self.hide_tooltip)
            canvas.tag_bind(tag_u, "<Enter>", lambda e, v=item['uscita'], l=item['label']: self.show_tooltip(e, f"{l} - Uscita: €{v:,.2f}"))
            canvas.tag_bind(tag_u, "<Leave>", self.hide_tooltip)
        canvas.create_text(CHART_LEFT - 5, CHART_TOP, text=f"{max_value:,.0f}", anchor="e", font=("Arial", 8), fill=self.TEXT_COLOR)
        canvas.create_text(CHART_LEFT - 5, CHART_BOTTOM, text="0", anchor="e", font=("Arial", 8), fill=self.TEXT_COLOR)
        tot_e = sum(it["entrata"] for it in self.data_for_chart)
        tot_u = sum(it["uscita"] for it in self.data_for_chart)
        saldo = tot_e - tot_u
        lbl_footer = tk.Label(canvas, text=f"Entrate: €{tot_e:,.2f}  |  Uscite: €{tot_u:,.2f}  |  Saldo: €{saldo:,.2f}", 
                               font=("Arial", 9, "bold"), fg=("green" if saldo >= 0 else "red"), bg=self.COLOR_WIDGET_BG, padx=5)
        self.win_footer_mensile = canvas.create_window(c_width // 2, c_height - 10, window=lbl_footer, anchor="s")
        def update_sticky_mensile(event=None):
            ox = canvas.canvasx(0)
            cw, ch = canvas.winfo_width(), canvas.winfo_height()
            canvas.coords(self.win_titolo_mensile, ox + 10, 10)
            canvas.coords(self.win_btn_mensile, ox + cw - 10, 10)
            canvas.coords(self.win_footer_mensile, ox + cw // 2, ch - 10)
        update_sticky_mensile()
        canvas.bind("<Configure>", lambda e: (update_sticky_mensile(), self.draw_mensile_chart() if not hasattr(self, '_resizing') else None))
    finally:
        self._drawing_mensile = False

def show_tooltip(self, event, text):
    self.hide_tooltip()
    self.tooltip_window = tk.Toplevel(self.stats_canvas)
    self.tooltip_window.withdraw()
    self.tooltip_window.wm_overrideredirect(True)
    label = ttk.Label(self.tooltip_window, text=text, style="Tooltip.TLabel")
    label.pack()
    self.tooltip_window.update_idletasks()
    tw = self.tooltip_window.winfo_reqwidth()
    th = self.tooltip_window.winfo_reqheight()
    sw_x = self.winfo_rootx()
    sw_y = self.winfo_rooty()
    sw_w = self.winfo_width()
    sw_h = self.winfo_height()
    x = event.x_root + 15
    y = event.y_root + 10
    if x + tw > sw_x + sw_w:
        x = event.x_root - tw - 10
    if y + th > sw_y + sw_h:
        y = event.y_root - th - 10
    if x < sw_x:
        x = sw_x + 5
    if y < sw_y:
        y = sw_y + 5
    self.tooltip_window.wm_geometry(f"+{int(x)}+{int(y)}")
    self.tooltip_window.deiconify()
    self.tooltip_window.attributes("-alpha", 1.0)

def hide_tooltip(self, event=None):
    if hasattr(self, 'tooltip_window') and self.tooltip_window:
        self.tooltip_window.destroy()
        self.tooltip_window = None

def draw_saldo_chart(self, event=None):
    if self.stats_view_mode.get() != "grafico_saldo":
        return
    if getattr(self, '_drawing_saldo', False):
        return
    self._drawing_saldo = True
    try:
        oggi = datetime.date.today()
        anno_corrente = oggi.year
        canvas = self.stats_canvas
        canvas.delete("all")
        canvas.update_idletasks()
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        CHART_LEFT = 80
        CHART_RIGHT = canvas_width - 20
        CHART_TOP = 50
        NUOVO_SPAZIO_LEGENDA = 80  
        CHART_BOTTOM = canvas_height - NUOVO_SPAZIO_LEGENDA
        CHART_AREA_WIDTH = CHART_RIGHT - CHART_LEFT
        CHART_HEIGHT = CHART_BOTTOM - CHART_TOP
        NUOVO_OFFSET_TESTO = 30
        BAR_RATIO = 0.8
        mesi_completi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                          "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
        if not hasattr(self, 'visualizza_saldo_totale'):
            self.visualizza_saldo_totale = False
        if not hasattr(self, 'visualizza_saldo_10_anni'):
            self.visualizza_saldo_10_anni = False
        if CHART_AREA_WIDTH < 100 or CHART_HEIGHT < 50:
            canvas.create_text(canvas_width // 2, canvas_height // 2,
                                text="Area di disegno insufficiente.",
                                font=("Arial", 12), fill="#AAAAAA")
            return
        def toggle_saldo_mode():
            if not self.visualizza_saldo_totale and not self.visualizza_saldo_10_anni:
                self.visualizza_saldo_totale = True
                self.visualizza_saldo_10_anni = False
            elif self.visualizza_saldo_totale and not self.visualizza_saldo_10_anni:
                self.visualizza_saldo_totale = False
                self.visualizza_saldo_10_anni = True
            else:
                self.visualizza_saldo_totale = False
                self.visualizza_saldo_10_anni = False
            self.draw_saldo_chart()
        if self.visualizza_saldo_10_anni:
            btn_text = " Solo anno corrente"
            icona_saldo = self.icone_gui.get("calendario")
        elif self.visualizza_saldo_totale:
            btn_text = " 10 anni (Linea)"
            icona_saldo = self.icone_gui.get("grafico_linea")
        else:
            btn_text = " Tutti gli anni"
            icona_saldo = self.icone_gui.get("saldo")
        btn_toggle = tk.Label(canvas, image=icona_saldo if icona_saldo else None, text=btn_text, compound="left", cursor="hand2", bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR, font=("Arial", 9, "bold"))
        if icona_saldo: btn_toggle.image = icona_saldo
        btn_toggle.bind("<Button-1>", lambda e: toggle_saldo_mode())
        self.win_btn_saldo = canvas.create_window(canvas_width - 10, 2, window=btn_toggle, anchor="ne")
        if self.visualizza_saldo_10_anni:
            transazioni_totali = []
            for giorno, entries in self.spese.items():
                if hasattr(giorno, "year"):
                    for entry in entries:
                        importo = float(entry[2]) if not isinstance(entry, dict) else float(entry.get("importo", 0))
                        tipo = entry[3] if not isinstance(entry, dict) else entry.get("tipo", "")
                        if not self.considera_ricorrenze_var.get() and giorno > datetime.date.today():
                            continue
                        variazione = importo if tipo == "Entrata" else -importo
                        transazioni_totali.append({"data": giorno, "variazione": variazione})
            transazioni_totali.sort(key=lambda x: x["data"])
            saldo_cumulativo_corrente = 0.0
            saldi_mensili_cumulativi = {}
            ultima_data_registrata = datetime.date.min
            for transazione in transazioni_totali:
                data_transazione = transazione["data"]
                if data_transazione.year != ultima_data_registrata.year or data_transazione.month != ultima_data_registrata.month:
                    ultima_data_registrata = data_transazione
                saldo_cumulativo_corrente += transazione["variazione"]
                if data_transazione.month == 12:
                    data_fine_mese = datetime.date(data_transazione.year + 1, 1, 1) - datetime.timedelta(days=1)
                else:
                    data_fine_mese = datetime.date(data_transazione.year, data_transazione.month + 1, 1) - datetime.timedelta(days=1)
                saldi_mensili_cumulativi[data_fine_mese] = saldo_cumulativo_corrente
            self.data_for_chart = []
            for data, saldo in sorted(saldi_mensili_cumulativi.items()):
                 self.data_for_chart.append({
                     "label": data.strftime("%m/%Y"),
                     "saldo": saldo,
                     "data": data
                 })
        elif self.visualizza_saldo_totale:
            aggregati_anno = {}
            for giorno, entries in self.spese.items():
                if hasattr(giorno, "year"):
                    anno = giorno.year
                    if anno not in aggregati_anno:
                        aggregati_anno[anno] = 0.0
                    for entry in entries:
                        tipo = entry[3] if not isinstance(entry, dict) else entry.get("tipo", "")
                        importo = float(entry[2]) if not isinstance(entry, dict) else float(entry.get("importo", 0))
                        if not self.considera_ricorrenze_var.get() and giorno > datetime.date.today():
                            continue
                        variazione = importo if tipo == "Entrata" else -importo
                        aggregati_anno[anno] += variazione
            self.data_for_chart = [
                {"label": str(anno), "saldo": saldo}  
                for anno, saldo in sorted(aggregati_anno.items())
            ]          
        else:
            mesi = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
            mensili_saldo = [{"label": m, "saldo": 0.0} for m in mesi]
            for giorno, entries in self.spese.items():
                if hasattr(giorno, "year") and giorno.year == anno_corrente:
                    mese_index = giorno.month - 1
                    for entry in entries:
                        tipo = entry[3] if not isinstance(entry, dict) else entry.get("tipo", "")
                        importo = float(entry[2]) if not isinstance(entry, dict) else float(entry.get("importo", 0))
                        if not self.considera_ricorrenze_var.get() and giorno > datetime.date.today():
                            continue
                        variazione = importo if tipo == "Entrata" else -importo
                        mensili_saldo[mese_index]["saldo"] += variazione
            self.data_for_chart = mensili_saldo
        if not hasattr(self, 'data_for_chart') or not self.data_for_chart:
            canvas.create_text(canvas_width // 2, canvas_height // 2,
                                text="Nessun dato saldo disponibile.",
                                font=("Arial", 12), fill="#AAAAAA")
            return
        saldi = [item["saldo"] for item in self.data_for_chart]
        max_saldo = max(saldi)
        min_saldo = min(saldi)
        buffer = (max_saldo - min_saldo) * 0.1 or 100 
        y_max = max_saldo + buffer
        y_min = min_saldo - buffer
        y_range = y_max - y_min
        def scale_y(saldo):
            if y_range == 0:
                return CHART_TOP + CHART_HEIGHT / 2
            return CHART_BOTTOM - ((saldo - y_min) / y_range) * CHART_HEIGHT
        if self.visualizza_saldo_10_anni:
            canvas.delete("y_labels", "axis")
            canvas.create_line(CHART_LEFT, CHART_BOTTOM, CHART_LEFT, CHART_TOP, fill=self.TEXT_COLOR, width=2, tags="axis")
            canvas.create_text(CHART_LEFT - 5, scale_y(max_saldo), text=f"€{max_saldo:,.0f}", anchor="e", font=("Arial", 8), fill=self.TEXT_COLOR, tags="y_labels")
            canvas.create_text(CHART_LEFT - 5, scale_y(min_saldo), text=f"€{min_saldo:,.0f}", anchor="e", font=("Arial", 8), fill=self.TEXT_COLOR, tags="y_labels")
            if y_min < 0 < y_max:
                ZERO_LINE_Y = scale_y(0)
                canvas.create_line(CHART_LEFT, ZERO_LINE_Y, CHART_RIGHT, ZERO_LINE_Y, fill="#AAAAAA", width=1, dash=(5, 5), tags="axis")
                canvas.create_text(CHART_LEFT - 5, ZERO_LINE_Y, text="0", anchor="e", font=("Arial", 8), fill=self.TEXT_COLOR, tags="y_labels")
            data_min = self.data_for_chart[0]['data']
            data_max = self.data_for_chart[-1]['data']
            data_range_days = (data_max - data_min).days or 1
            def scale_x(date):
                if data_range_days == 0:
                    return CHART_LEFT + CHART_AREA_WIDTH / 2
                days_since_start = (date - data_min).days
                return CHART_LEFT + (days_since_start / data_range_days) * CHART_AREA_WIDTH
            points = []
            for i, item in enumerate(self.data_for_chart):
                x = scale_x(item['data'])
                y = scale_y(item['saldo'])
                points.append((x, y))

                point_radius = 4
                point_id = canvas.create_oval(x - point_radius, y - point_radius, 
                                               x + point_radius, y + point_radius, 
                                               fill="blue", outline="")
                d_data = item['data']
                popup_title = f"Transazioni {d_data.strftime('%m %Y')}"
                d_filter = {
                    "anno": str(d_data.year),
                    "mese": d_data.month,
                    "categoria": None,
                    "tipo": None
                }
                canvas.tag_bind(point_id, "<Double-1>", 
                                lambda e, f=d_filter, t=popup_title: self.mostra_transazioni_popup(f, t))
                tooltip_text = f"Data: {item['label']}\nSaldo: €{item['saldo']:,.2f}"
                canvas.tag_bind(point_id, "<Enter>", lambda e, txt=tooltip_text: self.show_tooltip(e, txt))
                canvas.tag_bind(point_id, "<Leave>", self.hide_tooltip)
                if i == 0 or (item['data'].month == 1 and item['data'].day == 1) or i == len(self.data_for_chart) - 1:
                    canvas.create_text(x, CHART_BOTTOM + NUOVO_OFFSET_TESTO, text=item['data'].strftime("%Y"), anchor="n", angle=45, font=("Arial", 8), fill=self.TEXT_COLOR)
            if len(points) > 1:
                canvas.create_line(points, fill="blue", width=2, tags="line_chart")
        else:
            max_positive = max((item["saldo"] for item in self.data_for_chart if item["saldo"] >= 0), default=0) or 1
            max_negative = min((item["saldo"] for item in self.data_for_chart if item["saldo"] < 0), default=0) or -1
            ZERO_LINE_Y = CHART_TOP + CHART_HEIGHT / 2 
            canvas.delete("y_labels", "axis")
            canvas.create_line(CHART_LEFT, CHART_BOTTOM, CHART_LEFT, CHART_TOP, fill=self.TEXT_COLOR, width=2, tags="axis")
            canvas.create_line(CHART_LEFT, ZERO_LINE_Y, CHART_RIGHT, ZERO_LINE_Y, fill="#AAAAAA", width=2, tags="axis")
            canvas.create_text(CHART_LEFT - 5, CHART_TOP, text=f"€{max_positive:,.0f}", anchor="e", font=("Arial", 8), fill="green", tags="y_labels")
            canvas.create_text(CHART_LEFT - 5, ZERO_LINE_Y, text="0", anchor="e", font=("Arial", 8), fill=self.TEXT_COLOR, tags="y_labels")
            canvas.create_text(CHART_LEFT - 5, CHART_BOTTOM, text=f"€{max_negative:,.0f}", anchor="e", font=("Arial", 8), fill="red", tags="y_labels")
            num_bars = len(self.data_for_chart)
            bar_space_total = CHART_AREA_WIDTH / num_bars
            bar_width = bar_space_total * BAR_RATIO
            for i, item in enumerate(self.data_for_chart):
                saldo = item["saldo"]
                if saldo >= 0:
                    bar_height = max((saldo / max_positive) * (CHART_HEIGHT / 2), 4 if saldo > 0 else 0)
                else:
                    bar_height = max((abs(saldo) / abs(max_negative)) * (CHART_HEIGHT / 2), 4 if saldo < 0 else 0)
                x_center = CHART_LEFT + (i + 0.5) * bar_space_total
                x1 = x_center - bar_width / 2
                x2 = x_center + bar_width / 2
                if saldo >= 0:
                    y1 = ZERO_LINE_Y - bar_height
                    y2 = ZERO_LINE_Y
                    color = "green"
                    text_anchor = "s"
                    text_y = y1 - 5
                else:
                    y1 = ZERO_LINE_Y
                    y2 = ZERO_LINE_Y + bar_height
                    color = "red"
                    text_anchor = "n"
                    text_y = y2 + 5
                rect_id = canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="black")
                if saldo != 0:
                    if self.visualizza_saldo_totale:
                        anno = item["label"]
                        popup_title = f"Transazioni per l'Anno {anno} (Entrate e Uscite)"
                        data_filter = {
                            "anno": anno,
                            "mese": None,
                            "categoria": None,
                            "tipo": None
                        }
                    else:
                        mese_index = i + 1  # 1-12
                        mese_nome = mesi_completi[i]
                        anno = str(anno_corrente)
                        popup_title = f"Transazioni per {mese_nome} {anno} (Entrate e Uscite)"
                        data_filter = {
                            "anno": anno,
                            "mese": mese_index,
                            "categoria": None,
                            "tipo": None
                        }
                    canvas.tag_bind(rect_id, "<Double-1>", 
                                    lambda e, f=data_filter, t=popup_title: 
                                        self.mostra_transazioni_popup(f, t))
                canvas.tag_bind(rect_id, "<Enter>", lambda e, txt=f"{item['label']}: €{saldo:,.2f}": self.show_tooltip(e, txt))
                canvas.tag_bind(rect_id, "<Leave>", self.hide_tooltip)
                canvas.create_text(x_center, CHART_BOTTOM + NUOVO_OFFSET_TESTO, text=item["label"], anchor="n", angle=45, font=("Arial", 8), fill=self.TEXT_COLOR)
                canvas.create_text(x_center, text_y, text=f"€{saldo:.0f}", anchor=text_anchor, font=("Arial", 8, "bold"), fill=color)
        total_entrata = 0.0
        total_uscita = 0.0
        anni_da_includere = set()
        data_min_vis = None
        data_max_vis = None
        if self.visualizza_saldo_10_anni and self.data_for_chart:
              data_min_vis = self.data_for_chart[0]['data']
              data_max_vis = self.data_for_chart[-1]['data']
        elif self.visualizza_saldo_totale:
            anni_da_includere = set([int(item["label"]) for item in self.data_for_chart if item["label"].isdigit()])
        else:
            anni_da_includere = {anno_corrente}
        for giorno, entries in self.spese.items():
            include_entry = False
            if self.visualizza_saldo_10_anni and data_min_vis and data_max_vis:
                  if hasattr(giorno, "year") and giorno <= data_max_vis:
                      include_entry = True
            elif hasattr(giorno, "year") and giorno.year in anni_da_includere:
                  include_entry = True
            if include_entry:
                for entry in entries:
                    tipo = entry[3] if not isinstance(entry, dict) else entry.get("tipo", "")
                    importo = float(entry[2]) if not isinstance(entry, dict) else float(entry.get("importo", 0))
                    if tipo == "Entrata":
                        total_entrata += importo
                    elif tipo == "Uscita":
                        total_uscita += importo
        total_saldo = total_entrata - total_uscita
        saldo_color = "green" if total_saldo >= 0 else "red"
        if self.visualizza_saldo_10_anni and self.data_for_chart:
            primo_anno = self.data_for_chart[0]['data'].year
            ultimo_anno = self.data_for_chart[-1]['data'].year
            label_periodo = f"({primo_anno} - {ultimo_anno})"
            titolo_grafico = f"Saldo Conto Corrente Cumulativo {label_periodo}"
        elif self.visualizza_saldo_totale:
            anni_presenti = sorted(list(set([int(item["label"]) for item in self.data_for_chart if item["label"].isdigit()])))
            label_periodo = f"({anni_presenti[0]} - {anni_presenti[-1]})" if anni_presenti else "(N.D.)"
            titolo_grafico = f"Saldo Netto Annuale Aggregato {label_periodo}"
        else:
            label_periodo = f"({anno_corrente})"
            titolo_grafico = f"Saldo Netto Mensile {label_periodo}"

        tid = canvas.create_text(canvas_width // 2, CHART_TOP / 3,
                            text=titolo_grafico,
                            font=("Arial", 8, "bold"), fill=self.TEXT_COLOR, anchor="e")
        bbox = canvas.bbox(tid)
        img_mouse = self.icone_gui.get("mouse")
        lbl_hint = tk.Label(canvas, text="  •  Doppio clic → Mostra Dettaglio ",
                            image=img_mouse, compound="right",
                            bg=self.COLOR_WIDGET_BG, fg="gray", font=("Arial", 8, "italic"))
        lbl_hint.image = img_mouse
        canvas.create_window(bbox[2] + 6, CHART_TOP / 3, window=lbl_hint, anchor="w")
        text_y_pos = canvas_height - 20 
        x_pos_1 = CHART_LEFT + CHART_AREA_WIDTH * 0.15 
        x_pos_2 = CHART_LEFT + CHART_AREA_WIDTH * 0.5  
        x_pos_3 = CHART_LEFT + CHART_AREA_WIDTH * 0.85 
        font_style = ("Arial", 10, "bold")
        canvas.create_text(x_pos_1, text_y_pos, 
                            text=f"Totale Entrate: €{total_entrata:,.2f}", 
                            anchor="center", font=font_style, fill="green")
        canvas.create_text(x_pos_2, text_y_pos, 
                            text=f"Totale Uscite: €{total_uscita:,.2f}", 
                            anchor="center", font=font_style, fill="red")
        canvas.create_text(x_pos_3, text_y_pos, 
                            text=f"Saldo Complessivo: €{total_saldo:,.2f}", 
                            anchor="center", font=font_style, fill=saldo_color)
        canvas.bind("<Configure>", lambda e: self.draw_saldo_chart() if not hasattr(self, '_resizing') else None)
    finally:
        self._drawing_saldo = False

