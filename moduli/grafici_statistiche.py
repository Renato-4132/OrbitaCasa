#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tkinter as tk
from tkinter import ttk
import datetime
import json
from collections import defaultdict
from moduli.modello_spesa import campo
from moduli.mappa_conti_trasferimenti import e_trasferimento_virtuale

HOUSEHOLD_LABEL = "Patrimonio Complessivo"

def _carica_db_conti():
    try:
        from __main__ import PORTAFOGLIO_BANCARIO
        if os.path.exists(PORTAFOGLIO_BANCARIO):
            with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"conti": [], "trasferimenti": []}

def formatta_italiano(numero, segno=False, decimali=2):
    fmt = "{:+,.%df}" % decimali if segno else "{:,.%df}" % decimali
    return fmt.format(numero).replace(',', 'X').replace('.', ',').replace('X', '.')

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
        db_conti = _carica_db_conti()
        conti_disponibili = db_conti.get("conti", [])
        nomi_conti = [HOUSEHOLD_LABEL] + [c.get("nome", "") for c in conti_disponibili]
        if not hasattr(self, 'bar_grafico_conto_filtro'):
            self.bar_grafico_conto_filtro = HOUSEHOLD_LABEL
        if self.bar_grafico_conto_filtro not in nomi_conti:
            self.bar_grafico_conto_filtro = HOUSEHOLD_LABEL
        conto_sel = None
        if self.bar_grafico_conto_filtro != HOUSEHOLD_LABEL:
            conto_sel = next((c for c in conti_disponibili if c.get("nome", "") == self.bar_grafico_conto_filtro), None)
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
                        if conto_sel is not None and campo(entry, "conto", "") != conto_sel.get("nome", ""):
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
        testi_btn = [" Storico", " Anno", " Storico", " Categorie"]
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
        canvas.update_idletasks()
        btn_bbox = canvas.bbox(self.win_btn)
        combo_x_bar = (btn_bbox[0] - 8) if btn_bbox else (c_width - 200)
        def on_cambio_conto_bar(event=None):
            self.bar_grafico_conto_filtro = combo_conto_bar.get()
            self.draw_bar_chart()
        def reset_conto_bar(event=None):
            self.bar_grafico_conto_filtro = HOUSEHOLD_LABEL
            self.draw_bar_chart()
        combo_conto_bar = ttk.Combobox(canvas, values=nomi_conti, state="readonly", width=24, font=("Arial", 8), style="Border.TCombobox")
        combo_conto_bar.set(self.bar_grafico_conto_filtro)
        combo_conto_bar.bind("<<ComboboxSelected>>", on_cambio_conto_bar)
        self.win_combo_conto_bar = canvas.create_window(combo_x_bar, 10, window=combo_conto_bar, anchor="ne")
        canvas.update_idletasks()
        bbox_combo_bar = canvas.bbox(self.win_combo_conto_bar)
        icon_x_bar = (bbox_combo_bar[0] - 4) if bbox_combo_bar else (combo_x_bar - 160)
        img_reset_bar = self.icone_gui.get("reset")
        btn_reset_bar = tk.Label(canvas, image=img_reset_bar if img_reset_bar else None,
                                  text="" if img_reset_bar else "↺", bg=self.COLOR_WIDGET_BG,
                                  fg=self.TEXT_COLOR, cursor="hand2")
        if img_reset_bar:
            btn_reset_bar.image = img_reset_bar
        btn_reset_bar.bind("<Button-1>", reset_conto_bar)
        self.win_reset_conto_bar = canvas.create_window(icon_x_bar, 10, window=btn_reset_bar, anchor="ne")
        t_in, t_out = sum(x['value'] for x in data_in), sum(x['value'] for x in data_out)
        saldo = t_in - t_out
        col_saldo = "#28a745" if saldo >= 0 else "#dc3545"
        text_y_tot = c_height - 10
        font_tot = ("Arial", 10, "bold")
        if self.stats_step < 2:
            self.win_totale = (canvas.create_text(0, 0, text=f"Totale Uscite: € {formatta_italiano(t_out)}",
                                anchor="sw", font=font_tot, fill="#dc3545"),)
        else:
            id_entrate = canvas.create_text(0, 0, text=f"Totale Entrate: € {formatta_italiano(t_in)}",
                                anchor="sw", font=font_tot, fill="#28a745")
            id_uscite = canvas.create_text(0, 0, text=f"Totale Uscite: € {formatta_italiano(t_out)}",
                                anchor="sw", font=font_tot, fill="#dc3545")
            id_saldo = canvas.create_text(0, 0, text=f"Saldo Complessivo: € {formatta_italiano(saldo, segno=True)}",
                                anchor="sw", font=font_tot, fill=col_saldo)
            self.win_totale = (id_entrate, id_uscite, id_saldo)
        visible_vals = [x['value'] for x in data_out] if self.stats_step < 2 else [x['value'] for x in data_out + data_in]
        max_v = max(visible_vals) if visible_vals else 1
        canvas.create_line(CHART_LEFT, CHART_BOTTOM, total_draw_width - 100, CHART_BOTTOM, width=2, fill="#AAAAAA")
        COLORS = ["#36A2EB", "#FF6384", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40"]
        def draw_item(x, val, label, color, tipo, budget=None):
            h_barra = max((val / max_v) * CHART_HEIGHT, 4)
            tag = f"bar_{x}"
            sfora = budget is not None and budget > 0 and val > budget
            canvas.create_rectangle(
                x-18, CHART_BOTTOM-h_barra, x+18, CHART_BOTTOM,
                fill="#ffc107" if sfora else color,
                outline="#dc3545" if sfora else "#333",
                width=2 if sfora else 1, tags=tag
            )
            canvas.create_text(x, CHART_BOTTOM + 5, text=label, anchor="ne", angle=45, font=("Arial", 7, "bold"), fill=color)
            canvas.create_text(x, CHART_BOTTOM-h_barra-5, text=f"€ {formatta_italiano(val, decimali=0)}", anchor="s", font=("Arial", 7, "bold"), fill=self.TEXT_COLOR)
            tooltip_txt = f"{label}: € {formatta_italiano(val)}"
            if budget is not None and budget > 0:
                tooltip_txt += f"\nBudget annuo: € {formatta_italiano(budget)}" + (" — Budget superato" if sfora else "")
            canvas.tag_bind(tag, "<Enter>", lambda e, t=tooltip_txt: self.show_tooltip(e, t))
            canvas.tag_bind(tag, "<Leave>", lambda e: self.hide_tooltip())
            conto_bar_attivo = None if self.bar_grafico_conto_filtro == HOUSEHOLD_LABEL else self.bar_grafico_conto_filtro
            filtro = {"anno": None if self.visualizza_tutti_gli_anni else str(anno_corrente), "categoria": label, "tipo": tipo, "conto": conto_bar_attivo}
            canvas.tag_bind(tag, "<Double-1>", lambda e, f=filtro, l=label: self.mostra_transazioni_popup(f, f"Dettaglio {l}"))
        budget_annuale_cat = getattr(self, 'budget_annuale_categorie', {})
        mostra_budget = not self.visualizza_tutti_gli_anni
        if self.stats_step < 2:
            for i, item in enumerate(data_out):
                budget_cat = budget_annuale_cat.get(item['label']) if mostra_budget else None
                draw_item(CHART_LEFT + (i * BAR_SPACE) + 20, item['value'], item['label'], COLORS[i % len(COLORS)], "Uscita", budget=budget_cat)
        else:
            for i, item in enumerate(data_in):
                draw_item(CHART_LEFT + (i * BAR_SPACE) + 20, item['value'], item['label'], "#28a745", "Entrata")
            sep_x = CHART_LEFT + (len(data_in) * BAR_SPACE) + 20
            canvas.create_line(sep_x, CHART_BOTTOM, sep_x, CHART_TOP, dash=(4,4), fill="#ccc")
            for i, item in enumerate(data_out):
                budget_cat = budget_annuale_cat.get(item['label']) if mostra_budget else None
                draw_item(sep_x + 40 + (i * BAR_SPACE), item['value'], item['label'], COLORS[i % len(COLORS)], "Uscita", budget=budget_cat)
        def update_sticky(event=None):
            if not canvas.winfo_exists(): return
            ox = canvas.canvasx(0)
            canvas.coords(self.win_titolo, ox + 10, 10)
            canvas.coords(self.win_btn, ox + canvas.winfo_width() - 10, 10)
            vw = canvas.winfo_width()
            y_tot = canvas.winfo_height() - 10
            if len(self.win_totale) == 1:
                canvas.coords(self.win_totale[0], ox + 10, y_tot)
            else:
                canvas.coords(self.win_totale[0], ox + vw * 0.05, y_tot)
                canvas.coords(self.win_totale[1], ox + vw * 0.38, y_tot)
                canvas.coords(self.win_totale[2], ox + vw * 0.68, y_tot)
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
        db_conti = _carica_db_conti()
        conti_disponibili = db_conti.get("conti", [])
        nomi_conti = [HOUSEHOLD_LABEL] + [c.get("nome", "") for c in conti_disponibili]
        if not hasattr(self, 'mensile_grafico_conto_filtro'):
            self.mensile_grafico_conto_filtro = HOUSEHOLD_LABEL
        if self.mensile_grafico_conto_filtro not in nomi_conti:
            self.mensile_grafico_conto_filtro = HOUSEHOLD_LABEL
        conto_sel = None
        if self.mensile_grafico_conto_filtro != HOUSEHOLD_LABEL:
            conto_sel = next((c for c in conti_disponibili if c.get("nome", "") == self.mensile_grafico_conto_filtro), None)
        if self.visualizza_tutti_gli_anni_mensile:
            aggregati = {}
            for giorno, entries in self.spese.items():
                if hasattr(giorno, "year"):
                    anno = giorno.year
                    if anno not in aggregati:
                        aggregati[anno] = {"label": str(anno), "entrata": 0.0, "uscita": 0.0}
                    for entry in entries:
                        if conto_sel is not None and campo(entry, "conto", "") != conto_sel.get("nome", ""):
                            continue
                        tipo = entry[3] if not isinstance(entry, dict) else entry.get("tipo", "")
                        importo = float(entry[2]) if not isinstance(entry, dict) else float(entry.get("importo", 0))
                        if not self.considera_ricorrenze_var.get() and giorno > datetime.date.today():
                            continue
                        if tipo == "Entrata":
                            aggregati[anno]["entrata"] += importo
                        elif tipo == "Uscita":
                            aggregati[anno]["uscita"] += importo
            if conto_sel is not None:
                for t in db_conti.get("trasferimenti", []):
                    if e_trasferimento_virtuale(t):
                        continue
                    try:
                        data_t = datetime.datetime.strptime(t["data"], "%d-%m-%Y").date()
                    except Exception:
                        continue
                    if not self.considera_ricorrenze_var.get() and data_t > oggi:
                        continue
                    try:
                        imp = round(float(t.get("importo", 0)), 2)
                    except Exception:
                        continue
                    anno_t = data_t.year
                    if anno_t not in aggregati:
                        aggregati[anno_t] = {"label": str(anno_t), "entrata": 0.0, "uscita": 0.0}
                    if t.get("da") == conto_sel.get("id"):
                        aggregati[anno_t]["uscita"] += imp
                    elif t.get("a") == conto_sel.get("id"):
                        aggregati[anno_t]["entrata"] += imp
            self.data_for_chart = [aggregati[anno] for anno in sorted(aggregati)]
        else:
            mesi_brevi = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
            mensili = [{"label": m, "entrata": 0.0, "uscita": 0.0} for m in mesi_brevi]
            for giorno, entries in self.spese.items():
                if hasattr(giorno, "year") and giorno.year == anno_corrente:
                    mese_index = giorno.month - 1
                    for entry in entries:
                        if conto_sel is not None and campo(entry, "conto", "") != conto_sel.get("nome", ""):
                            continue
                        tipo = entry[3] if not isinstance(entry, dict) else entry.get("tipo", "")
                        importo = float(entry[2]) if not isinstance(entry, dict) else float(entry.get("importo", 0))
                        if not self.considera_ricorrenze_var.get() and giorno > datetime.date.today():
                            continue
                        if tipo == "Entrata":
                            mensili[mese_index]["entrata"] += importo
                        elif tipo == "Uscita":
                            mensili[mese_index]["uscita"] += importo
            if conto_sel is not None:
                for t in db_conti.get("trasferimenti", []):
                    if e_trasferimento_virtuale(t):
                        continue
                    try:
                        data_t = datetime.datetime.strptime(t["data"], "%d-%m-%Y").date()
                    except Exception:
                        continue
                    if data_t.year != anno_corrente:
                        continue
                    if not self.considera_ricorrenze_var.get() and data_t > oggi:
                        continue
                    try:
                        imp = round(float(t.get("importo", 0)), 2)
                    except Exception:
                        continue
                    mese_idx_t = data_t.month - 1
                    if t.get("da") == conto_sel.get("id"):
                        mensili[mese_idx_t]["uscita"] += imp
                    elif t.get("a") == conto_sel.get("id"):
                        mensili[mese_idx_t]["entrata"] += imp
            self.data_for_chart = mensili
        c_width = canvas.winfo_width() if canvas.winfo_width() > 10 else 800
        c_height = canvas.winfo_height() if canvas.winfo_height() > 10 else 400
        CHART_LEFT = 50
        CHART_RIGHT = c_width - 10
        CHART_TOP = 60
        CHART_BOTTOM = c_height - 80
        CHART_AREA_WIDTH = CHART_RIGHT - CHART_LEFT
        CHART_HEIGHT = CHART_BOTTOM - CHART_TOP
        img_mensile = self.icone_gui.get("oggi" if not self.visualizza_tutti_gli_anni_mensile else "calendario")
        btn_text = " Tutti gli anni" if not self.visualizza_tutti_gli_anni_mensile else " Anno attuale"
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
        canvas.update_idletasks()
        btn_bbox_mensile = canvas.bbox(self.win_btn_mensile)
        combo_x_mensile = (btn_bbox_mensile[0] - 8) if btn_bbox_mensile else (c_width - 200)
        def on_cambio_conto_mensile(event=None):
            self.mensile_grafico_conto_filtro = combo_conto_mensile.get()
            self.draw_mensile_chart()
        def reset_conto_mensile(event=None):
            self.mensile_grafico_conto_filtro = HOUSEHOLD_LABEL
            self.draw_mensile_chart()
        combo_conto_mensile = ttk.Combobox(canvas, values=nomi_conti, state="readonly", width=24, font=("Arial", 8), style="Border.TCombobox")
        combo_conto_mensile.set(self.mensile_grafico_conto_filtro)
        combo_conto_mensile.bind("<<ComboboxSelected>>", on_cambio_conto_mensile)
        self.win_combo_conto_mensile = canvas.create_window(combo_x_mensile, 10, window=combo_conto_mensile, anchor="ne")
        canvas.update_idletasks()
        bbox_combo_mensile = canvas.bbox(self.win_combo_conto_mensile)
        icon_x_mensile = (bbox_combo_mensile[0] - 4) if bbox_combo_mensile else (combo_x_mensile - 160)
        img_reset_mensile = self.icone_gui.get("reset")
        btn_reset_mensile = tk.Label(canvas, image=img_reset_mensile if img_reset_mensile else None,
                                      text="" if img_reset_mensile else "↺", bg=self.COLOR_WIDGET_BG,
                                      fg=self.TEXT_COLOR, cursor="hand2")
        if img_reset_mensile:
            btn_reset_mensile.image = img_reset_mensile
        btn_reset_mensile.bind("<Button-1>", reset_conto_mensile)
        self.win_reset_conto_mensile = canvas.create_window(icon_x_mensile, 10, window=btn_reset_mensile, anchor="ne")
        if not self.data_for_chart or all(item["entrata"] == 0 and item["uscita"] == 0 for item in self.data_for_chart):
            canvas.create_text(c_width // 2, c_height // 2, text="Nessun dato disponibile.", font=("Arial", 12), fill="#AAAAAA")
            return
        titolo_g = f"Movimenti Mensili ({anno_corrente})"
        if self.visualizza_tutti_gli_anni_mensile:
            anni_p = [item["label"] for item in self.data_for_chart]
            label_p = f"({anni_p[0]} - {anni_p[-1]})" if anni_p else ""
            titolo_g = f"Movimenti Annuali {label_p}"
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
                canvas.create_text(x_center - bar_width/2, CHART_BOTTOM-h_e-5, text=formatta_italiano(item['entrata'], decimali=0), 
                                    anchor="s", font=("Arial", 7), fill="green")
            if item['uscita'] > 0:
                canvas.create_text(x_center + bar_width/2, CHART_BOTTOM-h_u-5, text=formatta_italiano(item['uscita'], decimali=0), 
                                    anchor="s", font=("Arial", 7), fill="red")
            if self.visualizza_tutti_gli_anni_mensile:
                f_anno, f_mese = item["label"], None
                p_text = f"Anno {item['label']}"
            else:
                f_anno, f_mese = str(anno_corrente), i + 1
                p_text = f"{mesi_completi[i]} {anno_corrente}"
            conto_mensile_attivo = None if self.mensile_grafico_conto_filtro == HOUSEHOLD_LABEL else self.mensile_grafico_conto_filtro
            canvas.tag_bind(tag_e, "<Double-1>", lambda e, a=f_anno, m=f_mese, t=p_text, c=conto_mensile_attivo: 
                self.mostra_transazioni_popup({"anno": a, "mese": m, "categoria": None, "tipo": "Entrata", "conto": c}, f"Transazioni {t} - Solo Entrate"))
            canvas.tag_bind(tag_u, "<Double-1>", lambda e, a=f_anno, m=f_mese, t=p_text, c=conto_mensile_attivo: 
                self.mostra_transazioni_popup({"anno": a, "mese": m, "categoria": None, "tipo": "Uscita", "conto": c}, f"Transazioni {t} - Solo Uscite"))
            canvas.tag_bind(tag_e, "<Enter>", lambda e, v=item['entrata'], l=item['label']: self.show_tooltip(e, f"{l} - Entrata: € {formatta_italiano(v)}"))
            canvas.tag_bind(tag_e, "<Leave>", self.hide_tooltip)
            canvas.tag_bind(tag_u, "<Enter>", lambda e, v=item['uscita'], l=item['label']: self.show_tooltip(e, f"{l} - Uscita: € {formatta_italiano(v)}"))
            canvas.tag_bind(tag_u, "<Leave>", self.hide_tooltip)
        canvas.create_text(CHART_LEFT - 5, CHART_TOP, text=formatta_italiano(max_value, decimali=0), anchor="e", font=("Arial", 8), fill=self.TEXT_COLOR)
        canvas.create_text(CHART_LEFT - 5, CHART_BOTTOM, text="0", anchor="e", font=("Arial", 8), fill=self.TEXT_COLOR)
        tot_e = sum(it["entrata"] for it in self.data_for_chart)
        tot_u = sum(it["uscita"] for it in self.data_for_chart)
        saldo = tot_e - tot_u
        id_entrate_m = canvas.create_text(0, 0, text=f"Totale Entrate: € {formatta_italiano(tot_e)}",
                            anchor="s", font=("Arial", 9, "bold"), fill="green")
        id_uscite_m = canvas.create_text(0, 0, text=f"Totale Uscite: € {formatta_italiano(tot_u)}",
                            anchor="s", font=("Arial", 9, "bold"), fill="red")
        id_saldo_m = canvas.create_text(0, 0, text=f"Saldo Complessivo: € {formatta_italiano(saldo, segno=True)}",
                            anchor="s", font=("Arial", 9, "bold"), fill=("green" if saldo >= 0 else "red"))
        self.win_footer_mensile = (id_entrate_m, id_uscite_m, id_saldo_m)
        def update_sticky_mensile(event=None):
            ox = canvas.canvasx(0)
            cw, ch = canvas.winfo_width(), canvas.winfo_height()
            canvas.coords(self.win_titolo_mensile, ox + 10, 10)
            canvas.coords(self.win_btn_mensile, ox + cw - 10, 10)
            canvas.coords(self.win_footer_mensile[0], ox + cw * 0.18, ch - 10)
            canvas.coords(self.win_footer_mensile[1], ox + cw * 0.5, ch - 10)
            canvas.coords(self.win_footer_mensile[2], ox + cw * 0.82, ch - 10)
        update_sticky_mensile()
        canvas.bind("<Configure>", lambda e: (update_sticky_mensile(), self.draw_mensile_chart() if not hasattr(self, '_resizing') else None))
    finally:
        self._drawing_mensile = False

def show_tooltip(self, event, text):
    self.hide_tooltip()
    self.tooltip_window = tk.Toplevel(event.widget)
    self.tooltip_window.withdraw()
    self.tooltip_window.wm_overrideredirect(True)
    self.tooltip_window.config(
        highlightthickness=1,
        highlightbackground=self.COLOR_HIGHLIGHT,
        bg=self.COLOR_TOOLTIP
    )
    label = ttk.Label(self.tooltip_window, text=text, style="Tooltip.TLabel",
                       justify="left", font=("Courier New", 9, "bold"))
    label.pack()
    self.tooltip_window.update_idletasks()
    tw = self.tooltip_window.winfo_reqwidth()
    th = self.tooltip_window.winfo_reqheight()
    win_owner = event.widget.winfo_toplevel()
    sw_x = win_owner.winfo_rootx()
    sw_y = win_owner.winfo_rooty()
    sw_w = win_owner.winfo_width()
    sw_h = win_owner.winfo_height()
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
        if not hasattr(self, 'saldo_grafico_conto_filtro'):
            self.saldo_grafico_conto_filtro = HOUSEHOLD_LABEL
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
            btn_text = " Anno attuale"
            icona_saldo = self.icone_gui.get("calendario")
        elif self.visualizza_saldo_totale:
            btn_text = " Cumulativo"
            icona_saldo = self.icone_gui.get("grafico_linea")
        else:
            btn_text = " Tutti gli anni"
            icona_saldo = self.icone_gui.get("saldo")
        btn_toggle = tk.Label(canvas, image=icona_saldo if icona_saldo else None, text=btn_text, compound="left", cursor="hand2", bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR, font=("Arial", 9, "bold"))
        if icona_saldo: btn_toggle.image = icona_saldo
        btn_toggle.bind("<Button-1>", lambda e: toggle_saldo_mode())
        self.win_btn_saldo = canvas.create_window(canvas_width - 10, 2, window=btn_toggle, anchor="ne")
        canvas.update_idletasks()
        btn_bbox = canvas.bbox(self.win_btn_saldo)
        combo_x = (btn_bbox[0] - 8) if btn_bbox else (canvas_width - 200)
        db_conti = _carica_db_conti()
        conti_disponibili = db_conti.get("conti", [])
        nomi_conti = [HOUSEHOLD_LABEL] + [c.get("nome", "") for c in conti_disponibili]
        if self.saldo_grafico_conto_filtro not in nomi_conti:
            self.saldo_grafico_conto_filtro = HOUSEHOLD_LABEL
        def on_cambio_conto_saldo(event=None):
            self.saldo_grafico_conto_filtro = combo_conto_saldo.get()
            self.draw_saldo_chart()
        def reset_conto_saldo(event=None):
            self.saldo_grafico_conto_filtro = HOUSEHOLD_LABEL
            self.draw_saldo_chart()
        combo_conto_saldo = ttk.Combobox(canvas, values=nomi_conti, state="readonly", width=24, font=("Arial", 8), style="Border.TCombobox")
        combo_conto_saldo.set(self.saldo_grafico_conto_filtro)
        combo_conto_saldo.bind("<<ComboboxSelected>>", on_cambio_conto_saldo)
        self.win_combo_conto_saldo = canvas.create_window(combo_x, 2, window=combo_conto_saldo, anchor="ne")
        canvas.update_idletasks()
        bbox_combo_saldo = canvas.bbox(self.win_combo_conto_saldo)
        icon_x_saldo = (bbox_combo_saldo[0] - 4) if bbox_combo_saldo else (combo_x - 160)
        img_reset_saldo = self.icone_gui.get("reset")
        btn_reset_saldo = tk.Label(canvas, image=img_reset_saldo if img_reset_saldo else None,
                                    text="" if img_reset_saldo else "↺", bg=self.COLOR_WIDGET_BG,
                                    fg=self.TEXT_COLOR, cursor="hand2")
        if img_reset_saldo:
            btn_reset_saldo.image = img_reset_saldo
        btn_reset_saldo.bind("<Button-1>", reset_conto_saldo)
        self.win_reset_conto_saldo = canvas.create_window(icon_x_saldo, 2, window=btn_reset_saldo, anchor="ne")
        conto_sel = None
        if self.saldo_grafico_conto_filtro != HOUSEHOLD_LABEL:
            conto_sel = next((c for c in conti_disponibili if c.get("nome", "") == self.saldo_grafico_conto_filtro), None)
        if self.visualizza_saldo_10_anni:
            limite_10anni = oggi - datetime.timedelta(days=365 * 10)
            transazioni_totali = []
            for giorno, entries in self.spese.items():
                if hasattr(giorno, "year") and giorno >= limite_10anni:
                    for entry in entries:
                        if conto_sel is not None and campo(entry, "conto", "") != conto_sel.get("nome", ""):
                            continue
                        importo = float(entry[2]) if not isinstance(entry, dict) else float(entry.get("importo", 0))
                        tipo = entry[3] if not isinstance(entry, dict) else entry.get("tipo", "")
                        if not self.considera_ricorrenze_var.get() and giorno > datetime.date.today():
                            continue
                        variazione = importo if tipo == "Entrata" else -importo
                        transazioni_totali.append({"data": giorno, "variazione": variazione})
            if conto_sel is not None:
                for t in db_conti.get("trasferimenti", []):
                    if e_trasferimento_virtuale(t):
                        continue
                    try:
                        data_t = datetime.datetime.strptime(t["data"], "%d-%m-%Y").date()
                    except Exception:
                        continue
                    if data_t < limite_10anni:
                        continue
                    try:
                        imp = round(float(t.get("importo", 0)), 2)
                    except Exception:
                        continue
                    if t.get("da") == conto_sel.get("id"):
                        transazioni_totali.append({"data": data_t, "variazione": -imp})
                    elif t.get("a") == conto_sel.get("id"):
                        transazioni_totali.append({"data": data_t, "variazione": imp})
            tot_entrata_precalc = sum(t["variazione"] for t in transazioni_totali if t["variazione"] > 0)
            tot_uscita_precalc = -sum(t["variazione"] for t in transazioni_totali if t["variazione"] < 0)
            transazioni_totali.sort(key=lambda x: x["data"])
            saldo_cumulativo_corrente = float(conto_sel.get("saldo", 0)) if conto_sel is not None else 0.0
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
                        if conto_sel is not None and campo(entry, "conto", "") != conto_sel.get("nome", ""):
                            continue
                        tipo = entry[3] if not isinstance(entry, dict) else entry.get("tipo", "")
                        importo = float(entry[2]) if not isinstance(entry, dict) else float(entry.get("importo", 0))
                        if not self.considera_ricorrenze_var.get() and giorno > datetime.date.today():
                            continue
                        variazione = importo if tipo == "Entrata" else -importo
                        aggregati_anno[anno] += variazione
            if conto_sel is not None:
                for t in db_conti.get("trasferimenti", []):
                    if e_trasferimento_virtuale(t):
                        continue
                    try:
                        data_t = datetime.datetime.strptime(t["data"], "%d-%m-%Y").date()
                    except Exception:
                        continue
                    if not self.considera_ricorrenze_var.get() and data_t > oggi:
                        continue
                    try:
                        imp = round(float(t.get("importo", 0)), 2)
                    except Exception:
                        continue
                    anno_t = data_t.year
                    if anno_t not in aggregati_anno:
                        aggregati_anno[anno_t] = 0.0
                    if t.get("da") == conto_sel.get("id"):
                        aggregati_anno[anno_t] -= imp
                    elif t.get("a") == conto_sel.get("id"):
                        aggregati_anno[anno_t] += imp
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
                        if conto_sel is not None and campo(entry, "conto", "") != conto_sel.get("nome", ""):
                            continue
                        tipo = entry[3] if not isinstance(entry, dict) else entry.get("tipo", "")
                        importo = float(entry[2]) if not isinstance(entry, dict) else float(entry.get("importo", 0))
                        if not self.considera_ricorrenze_var.get() and giorno > datetime.date.today():
                            continue
                        variazione = importo if tipo == "Entrata" else -importo
                        mensili_saldo[mese_index]["saldo"] += variazione
            if conto_sel is not None:
                for t in db_conti.get("trasferimenti", []):
                    if e_trasferimento_virtuale(t):
                        continue
                    try:
                        data_t = datetime.datetime.strptime(t["data"], "%d-%m-%Y").date()
                    except Exception:
                        continue
                    if data_t.year != anno_corrente:
                        continue
                    if not self.considera_ricorrenze_var.get() and data_t > oggi:
                        continue
                    try:
                        imp = round(float(t.get("importo", 0)), 2)
                    except Exception:
                        continue
                    mese_index_t = data_t.month - 1
                    if t.get("da") == conto_sel.get("id"):
                        mensili_saldo[mese_index_t]["saldo"] -= imp
                    elif t.get("a") == conto_sel.get("id"):
                        mensili_saldo[mese_index_t]["saldo"] += imp
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
            canvas.create_text(CHART_LEFT - 5, scale_y(max_saldo), text=f"€ {formatta_italiano(max_saldo, decimali=0)}", anchor="e", font=("Arial", 8), fill=self.TEXT_COLOR, tags="y_labels")
            canvas.create_text(CHART_LEFT - 5, scale_y(min_saldo), text=f"€ {formatta_italiano(min_saldo, decimali=0)}", anchor="e", font=("Arial", 8), fill=self.TEXT_COLOR, tags="y_labels")
            ZERO_LINE_Y = scale_y(0)
            zero_bar_y = min(max(ZERO_LINE_Y, CHART_TOP), CHART_BOTTOM)
            if y_min < 0 < y_max:
                canvas.create_line(CHART_LEFT, ZERO_LINE_Y, CHART_RIGHT, ZERO_LINE_Y, fill="#AAAAAA", width=1, dash=(5, 5), tags="axis")
                canvas.create_text(CHART_LEFT - 5, ZERO_LINE_Y, text="0", anchor="e", font=("Arial", 8), fill=self.TEXT_COLOR, tags="y_labels")
            num_bars = len(self.data_for_chart)
            bar_space_total = CHART_AREA_WIDTH / num_bars
            bar_width = max(1, bar_space_total * BAR_RATIO)
            for i, item in enumerate(self.data_for_chart):
                saldo = item["saldo"]
                x_center = CHART_LEFT + (i + 0.5) * bar_space_total
                x1 = x_center - bar_width / 2
                x2 = x_center + bar_width / 2
                y_val = scale_y(saldo)
                y1 = min(zero_bar_y, y_val)
                y2 = max(zero_bar_y, y_val)
                color = "green" if saldo >= 0 else "red"
                rect_id = canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
                d_data = item['data']
                popup_title = f"Transazioni {d_data.strftime('%m %Y')}"
                d_filter = {
                    "anno": str(d_data.year),
                    "mese": d_data.month,
                    "categoria": None,
                    "tipo": None,
                    "conto": None if self.saldo_grafico_conto_filtro == HOUSEHOLD_LABEL else self.saldo_grafico_conto_filtro
                }
                canvas.tag_bind(rect_id, "<Double-1>", 
                                lambda e, f=d_filter, t=popup_title: self.mostra_transazioni_popup(f, t))
                tooltip_text = f"Data:  {item['label']}\nSaldo: € {formatta_italiano(item['saldo'], segno=True)}"
                canvas.tag_bind(rect_id, "<Enter>", lambda e, txt=tooltip_text: self.show_tooltip(e, txt))
                canvas.tag_bind(rect_id, "<Leave>", self.hide_tooltip)
                if i == 0 or (item['data'].month == 1 and item['data'].day == 1) or i == len(self.data_for_chart) - 1:
                    canvas.create_text(x_center, CHART_BOTTOM + NUOVO_OFFSET_TESTO, text=item['data'].strftime("%Y"), anchor="n", angle=45, font=("Arial", 8), fill=self.TEXT_COLOR)
        else:
            max_positive = max((item["saldo"] for item in self.data_for_chart if item["saldo"] >= 0), default=0) or 1
            max_negative = min((item["saldo"] for item in self.data_for_chart if item["saldo"] < 0), default=0) or -1
            ZERO_LINE_Y = CHART_TOP + CHART_HEIGHT / 2 
            canvas.delete("y_labels", "axis")
            canvas.create_line(CHART_LEFT, CHART_BOTTOM, CHART_LEFT, CHART_TOP, fill=self.TEXT_COLOR, width=2, tags="axis")
            canvas.create_line(CHART_LEFT, ZERO_LINE_Y, CHART_RIGHT, ZERO_LINE_Y, fill="#AAAAAA", width=2, tags="axis")
            canvas.create_text(CHART_LEFT - 5, CHART_TOP, text=f"€ {formatta_italiano(max_positive, decimali=0)}", anchor="e", font=("Arial", 8), fill="green", tags="y_labels")
            canvas.create_text(CHART_LEFT - 5, ZERO_LINE_Y, text="0", anchor="e", font=("Arial", 8), fill=self.TEXT_COLOR, tags="y_labels")
            canvas.create_text(CHART_LEFT - 5, CHART_BOTTOM, text=f"€ {formatta_italiano(max_negative, decimali=0)}", anchor="e", font=("Arial", 8), fill="red", tags="y_labels")
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
                            "tipo": None,
                            "conto": None if self.saldo_grafico_conto_filtro == HOUSEHOLD_LABEL else self.saldo_grafico_conto_filtro
                        }
                    else:
                        mese_index = i + 1
                        mese_nome = mesi_completi[i]
                        anno = str(anno_corrente)
                        popup_title = f"Transazioni per {mese_nome} {anno} (Entrate e Uscite)"
                        data_filter = {
                            "anno": anno,
                            "mese": mese_index,
                            "categoria": None,
                            "tipo": None,
                            "conto": None if self.saldo_grafico_conto_filtro == HOUSEHOLD_LABEL else self.saldo_grafico_conto_filtro
                        }
                    canvas.tag_bind(rect_id, "<Double-1>", 
                                    lambda e, f=data_filter, t=popup_title: 
                                        self.mostra_transazioni_popup(f, t))
                canvas.tag_bind(rect_id, "<Enter>", lambda e, txt=f"{item['label']}: € {formatta_italiano(saldo, segno=True)}": self.show_tooltip(e, txt))
                canvas.tag_bind(rect_id, "<Leave>", self.hide_tooltip)
                canvas.create_text(x_center, CHART_BOTTOM + NUOVO_OFFSET_TESTO, text=item["label"], anchor="n", angle=45, font=("Arial", 8), fill=self.TEXT_COLOR)
                canvas.create_text(x_center, text_y, text=f"€ {formatta_italiano(abs(saldo), decimali=0)}", anchor=text_anchor, font=("Arial", 8, "bold"), fill=color)
        total_entrata = 0.0
        total_uscita = 0.0
        anni_da_includere = set()
        data_min_vis = None
        data_max_vis = None
        if self.visualizza_saldo_10_anni and self.data_for_chart:
              total_entrata = tot_entrata_precalc
              total_uscita = tot_uscita_precalc
        elif self.visualizza_saldo_totale:
            anni_da_includere = set([int(item["label"]) for item in self.data_for_chart if item["label"].isdigit()])
        else:
            anni_da_includere = {anno_corrente}
        if not self.visualizza_saldo_10_anni:
            for giorno, entries in self.spese.items():
                include_entry = hasattr(giorno, "year") and giorno.year in anni_da_includere
                if include_entry:
                    for entry in entries:
                        if conto_sel is not None and campo(entry, "conto", "") != conto_sel.get("nome", ""):
                            continue
                        tipo = entry[3] if not isinstance(entry, dict) else entry.get("tipo", "")
                        importo = float(entry[2]) if not isinstance(entry, dict) else float(entry.get("importo", 0))
                        if not self.considera_ricorrenze_var.get() and giorno > oggi:
                            continue
                        if tipo == "Entrata":
                            total_entrata += importo
                        elif tipo == "Uscita":
                            total_uscita += importo
            if conto_sel is not None:
                for t in db_conti.get("trasferimenti", []):
                    if e_trasferimento_virtuale(t):
                        continue
                    try:
                        data_t = datetime.datetime.strptime(t["data"], "%d-%m-%Y").date()
                    except Exception:
                        continue
                    if data_t.year not in anni_da_includere:
                        continue
                    if not self.considera_ricorrenze_var.get() and data_t > oggi:
                        continue
                    try:
                        imp = round(float(t.get("importo", 0)), 2)
                    except Exception:
                        continue
                    if t.get("da") == conto_sel.get("id"):
                        total_uscita += imp
                    elif t.get("a") == conto_sel.get("id"):
                        total_entrata += imp
        total_saldo = total_entrata - total_uscita
        saldo_color = "green" if total_saldo >= 0 else "red"
        if self.visualizza_saldo_10_anni and self.data_for_chart:
            primo_anno = self.data_for_chart[0]['data'].year
            ultimo_anno = self.data_for_chart[-1]['data'].year
            label_periodo = f"({primo_anno} - {ultimo_anno})"
            titolo_grafico = f"Saldo Cumulativo {label_periodo}"
        elif self.visualizza_saldo_totale:
            anni_presenti = sorted(list(set([int(item["label"]) for item in self.data_for_chart if item["label"].isdigit()])))
            label_periodo = f"({anni_presenti[0]} - {anni_presenti[-1]})" if anni_presenti else "(N.D.)"
            titolo_grafico = f"Saldo Netto Annuale {label_periodo}"
        else:
            label_periodo = f"({anno_corrente})"
            titolo_grafico = f"Saldo Netto Mensile {label_periodo}"

        tid = canvas.create_text(10, 14,
                            text=titolo_grafico,
                            font=("Arial", 8, "bold"), fill=self.TEXT_COLOR, anchor="w")
        bbox = canvas.bbox(tid)
        img_mouse = self.icone_gui.get("mouse")
        lbl_hint = tk.Label(canvas, text="  •  Doppio clic → Mostra Dettaglio ",
                            image=img_mouse, compound="right",
                            bg=self.COLOR_WIDGET_BG, fg="gray", font=("Arial", 8, "italic"))
        lbl_hint.image = img_mouse
        canvas.create_window(bbox[2] + 6, 14, window=lbl_hint, anchor="w")
        text_y_pos = canvas_height - 20 
        x_pos_1 = CHART_LEFT + CHART_AREA_WIDTH * 0.15 
        x_pos_2 = CHART_LEFT + CHART_AREA_WIDTH * 0.5  
        x_pos_3 = CHART_LEFT + CHART_AREA_WIDTH * 0.85 
        font_style = ("Arial", 10, "bold")
        canvas.create_text(x_pos_1, text_y_pos, 
                            text=f"Totale Entrate: € {formatta_italiano(total_entrata)}", 
                            anchor="center", font=font_style, fill="green")
        canvas.create_text(x_pos_2, text_y_pos, 
                            text=f"Totale Uscite: € {formatta_italiano(total_uscita)}", 
                            anchor="center", font=font_style, fill="red")
        canvas.create_text(x_pos_3, text_y_pos, 
                            text=f"Saldo Complessivo: € {formatta_italiano(total_saldo, segno=True)}", 
                            anchor="center", font=font_style, fill=saldo_color)
        canvas.bind("<Configure>", lambda e: self.draw_saldo_chart() if not hasattr(self, '_resizing') else None)
    finally:
        self._drawing_saldo = False

