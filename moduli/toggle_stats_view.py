#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
from collections import defaultdict
import tkinter as tk
from tkinter import ttk

def toggle_stats_view(self, tipo="grafico"):
    parent_frame = None
    try:
        if hasattr(self, 'vsb_stats'): self.vsb_stats.config(command="")
        if hasattr(self, 'hsb_stats'): self.hsb_stats.config(command="")
    except: pass
    if hasattr(self, 'stats_table') and self.stats_table and self.stats_table.winfo_exists():
        parent_frame = self.stats_table.master
        self.stats_table.destroy()
    if hasattr(self, 'stats_canvas') and self.stats_canvas and self.stats_canvas.winfo_exists():
        if parent_frame is None:
            parent_frame = self.stats_canvas.master
        self.stats_canvas.destroy()
    if hasattr(self, 'stats_pf_container') and self.stats_pf_container and self.stats_pf_container.winfo_exists():
        self.stats_pf_container.destroy()
    parent_frame = self.stats_table_container if hasattr(self, 'stats_table_container') else self.stats_frame_ref
    for btn in self.filtri_temporali:
        btn.pack_forget()
    if hasattr(self, 'stats_label'):
        self.stats_label.grid_remove()
    if hasattr(self, 'totali_label'):
        self.totali_label.pack_forget()
    if tipo == "proiezione_fondo":
        if hasattr(self, 'stats_hint_label'):
            self.stats_hint_label.grid_remove()
        self.stats_view_mode.set("proiezione_fondo")
        MESI_BREVI  = ["Gen","Feb","Mar","Apr","Mag","Giu","Lug","Ago","Set","Ott","Nov","Dic"]
        MESI_ESTESI = ["Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno",
                       "Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"]
        today_pf     = datetime.date.today()
        anno_c_pf    = today_pf.year
        anno_prec_pf = anno_c_pf - 1
        inizio_pf    = today_pf - datetime.timedelta(days=364)
        entrate_tot_pf = 0.0; uscite_tot_pf = 0.0; mesi_dati_pf = {}
        for d, sp in self.spese.items():
            if inizio_pf <= d <= today_pf:
                for entry in sp:
                    cat_pf, desc_pf, imp_pf, tipo_v_pf = entry[:4]
                    key_pf = (d.year, d.month)
                    if key_pf not in mesi_dati_pf:
                        mesi_dati_pf[key_pf] = {"e": 0.0, "u": 0.0}
                    if tipo_v_pf == "Entrata":
                        entrate_tot_pf += imp_pf; mesi_dati_pf[key_pf]["e"] += imp_pf
                    else:
                        uscite_tot_pf += imp_pf; mesi_dati_pf[key_pf]["u"] += imp_pf
        n_mesi_pf  = len(mesi_dati_pf) if mesi_dati_pf else 1
        media_e_pf = entrate_tot_pf / n_mesi_pf
        media_u_pf = uscite_tot_pf  / n_mesi_pf
        mesi_reali_pf = {m: v for (y, m), v in mesi_dati_pf.items() if y == anno_c_pf}
        mesi_prec_pf  = {}
        for d, sp in self.spese.items():
            if d.year == anno_prec_pf:
                if d.month not in mesi_prec_pf:
                    mesi_prec_pf[d.month] = {"e": 0.0, "u": 0.0}
                for entry in sp:
                    imp2_pf, tipo_v2_pf = entry[2], entry[3]
                    if tipo_v2_pf == "Entrata":
                        mesi_prec_pf[d.month]["e"] += imp2_pf
                    else:
                        mesi_prec_pf[d.month]["u"] += imp2_pf
        proj_pf = []
        for m in range(1, 13):
            if m in mesi_reali_pf:
                e_pf, u_pf, futuro_pf = mesi_reali_pf[m]["e"], mesi_reali_pf[m]["u"], False
            else:
                e_pf = mesi_prec_pf[m]["e"] if m in mesi_prec_pf else media_e_pf
                u_pf = mesi_prec_pf[m]["u"] if m in mesi_prec_pf else media_u_pf
                futuro_pf = True
            proj_pf.append({"m": m, "e": e_pf, "u": u_pf, "r": e_pf - u_pf, "futuro": futuro_pf})
        self.stats_pf_container = tk.Frame(parent_frame, bg=self.COLOR_BACKGROUND)
        self.stats_pf_container.pack(fill=tk.BOTH, expand=True)
        frm_kpi_pf = tk.Frame(self.stats_pf_container, bg=self.COLOR_BACKGROUND)
        frm_kpi_pf.pack(fill="x", padx=4, pady=(2, 0))
        def _kpi_pf(parent, label, valore, colore=None):
            f = tk.Frame(parent, bg=self.COLOR_WIDGET_BG,
                         highlightbackground=self.COLOR_HIGHLIGHT, highlightthickness=1)
            f.pack(side="left", expand=True, fill="both", padx=2)
            tk.Label(f, text=label, font=("Arial", 7),
                     bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR).pack(pady=(3, 0))
            def _fmt_pf(v):
                return f"€ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            tk.Label(f, text=_fmt_pf(valore), font=("Arial", 9, "bold"),
                     bg=self.COLOR_WIDGET_BG,
                     fg=colore or self.TEXT_COLOR).pack(pady=(1, 3))
        risparmio_pf = entrate_tot_pf - uscite_tot_pf
        col_r_pf = self.COLOR_GREEN if risparmio_pf >= 0 else self.COLOR_RED
        _kpi_pf(frm_kpi_pf, "Entrate 365gg",   entrate_tot_pf)
        _kpi_pf(frm_kpi_pf, "Uscite 365gg",    uscite_tot_pf)
        _kpi_pf(frm_kpi_pf, "Risparmio 365gg", risparmio_pf, col_r_pf)
        self.stats_canvas = tk.Canvas(self.stats_pf_container, bg=self.COLOR_WIDGET_BG,
                                      highlightbackground=self.COLOR_HIGHLIGHT,
                                      highlightthickness=1)
        self.stats_canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=(2, 4))
        def _scelta_anno_pf(mese, nome_mese, tipo_filt, futuro):
            if not futuro:
                self.mostra_transazioni_popup(
                    {"anno": str(anno_c_pf), "mese": mese, "categoria": None, "tipo": tipo_filt},
                    f"Transazioni {nome_mese} {anno_c_pf}" + (f" — Solo {tipo_filt}" if tipo_filt else ""))
                return
            dlg = tk.Toplevel(self, bg=self.COLOR_BACKGROUND)
            dlg.withdraw()
            dlg.title(f"{nome_mese} — Scegli anno")
            dlg.configure(bg=self.COLOR_BACKGROUND)
            dlg.transient(self)
            dlg.resizable(False, False)
            dlg.bind("<Escape>", lambda e: dlg.destroy())
            tipo_label = f" — Solo {tipo_filt}" if tipo_filt else ""
            img_cal = self.icone_gui.get("calendario")
            lbl_intro = tk.Label(dlg,
                     image=img_cal, compound="left",
                     text=f"  {nome_mese} è in proiezione.\n  Vuoi vedere i movimenti di:",
                     bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
                     font=("Arial", 10), justify="left")
            if img_cal:
                lbl_intro.image = img_cal
            lbl_intro.pack(padx=24, pady=(18, 12))
            def _apri(anno):
                dlg.destroy()
                self.mostra_transazioni_popup(
                    {"anno": str(anno), "mese": mese, "categoria": None, "tipo": tipo_filt},
                    f"Transazioni {nome_mese} {anno}{tipo_label}")
            frm_btn = tk.Frame(dlg, bg=self.COLOR_BACKGROUND)
            frm_btn.pack(pady=(0, 18))
            for testo, ico, anno_target in [
                (f"  {anno_c_pf} (anno corrente)",   "oggi",       anno_c_pf),
                (f"  {anno_prec_pf} (anno scorso)",  "calendario", anno_prec_pf),
            ]:
                img_ico = self.icone_gui.get(ico)
                b = tk.Label(frm_btn, image=img_ico, text=testo,
                             compound="left", bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                             cursor="hand2", font=("Arial", 10, "bold"))
                if img_ico:
                    b.image = img_ico
                b.pack(side="left", padx=8)
                b.bind("<Button-1>", lambda e, a=anno_target: _apri(a))
            img_chiudi = self.icone_gui.get("chiudi")
            btn_chiudi = tk.Label(dlg,
                     image=img_chiudi, compound="left",
                     text="  Chiudi",
                     bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                     cursor="hand2", font=("Arial", 9, "bold"))
            if img_chiudi:
                btn_chiudi.image = img_chiudi
            btn_chiudi.pack(pady=(0, 12))
            btn_chiudi.bind("<Button-1>", lambda e: dlg.destroy())
            dlg.update_idletasks()
            w = dlg.winfo_reqwidth()
            h = dlg.winfo_reqheight()
            x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
            y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
            dlg.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")
            dlg.deiconify()
            dlg.lift()
            dlg.focus_force()
        def _draw_proj_inline(event=None):
            cvs_pf = self.stats_canvas
            if not cvs_pf.winfo_exists():
                return
            cvs_pf.delete("all")
            W_pf = cvs_pf.winfo_width()
            H_pf = cvs_pf.winfo_height()
            if W_pf < 20 or H_pf < 20:
                return
            PL_pf, PR_pf, PT_pf, PB_pf = 44, 12, 20, 24
            aw_pf = W_pf - PL_pf - PR_pf
            ah_pf = H_pf - PT_pf - PB_pf
            max_v_pf = max((max(p["e"], p["u"], abs(p["r"])) for p in proj_pf), default=1.0) or 1.0
            max_v_pf *= 1.12
            min_r_pf = min((p["r"] for p in proj_pf), default=0.0)
            neg_space = (abs(min_r_pf) / max_v_pf) if min_r_pf < 0 else 0.0
            baseline_y = PT_pf + ah_pf - ah_pf * neg_space * 1.12 / (1.0 + neg_space * 1.12)
            usable_h   = baseline_y - PT_pf
            cvs_pf.create_line(PL_pf, PT_pf, PL_pf, PT_pf + ah_pf, fill="#DDDDDD")
            cvs_pf.create_line(PL_pf, PT_pf + ah_pf, PL_pf + aw_pf, PT_pf + ah_pf, fill="#DDDDDD")
            cvs_pf.create_line(PL_pf, baseline_y, PL_pf + aw_pf, baseline_y, fill="#888888", dash=(3, 3))
            for tick in range(0, 6):
                v_tick = max_v_pf * tick / 5
                y_tick = baseline_y - usable_h * tick / 5
                lbl_tick = (f"{v_tick/1000:.1f}k" if v_tick >= 1000 else f"{v_tick:.0f}")
                cvs_pf.create_text(PL_pf - 5, y_tick, anchor="e", text=lbl_tick,
                                   font=("Arial", 7), fill="gray")
            bar_gw_pf = aw_pf / 12
            bar_w_pf  = max(3, min(bar_gw_pf * 0.22, 12))
            def _fmt_eur(v):
                return f"€ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            for i, p in enumerate(proj_pf):
                xc_pf  = PL_pf + i * bar_gw_pf + bar_gw_pf / 2
                nm_pf  = MESI_ESTESI[p["m"] - 1]
                he_pf  = min(usable_h * (p["e"] / max_v_pf), usable_h)
                col_e_pf = "#A5D6A7" if p["futuro"] else "#4CAF50"
                tag_e_pf = f"pe_{i}"
                cvs_pf.create_rectangle(xc_pf - bar_w_pf * 1.5 - 1, baseline_y - he_pf,
                                        xc_pf - bar_w_pf * 0.5 - 1, baseline_y,
                                        fill=col_e_pf, outline="", tags=tag_e_pf)
                hu_pf  = min(usable_h * (p["u"] / max_v_pf), usable_h)
                col_u_pf = "#FFCDD2" if p["futuro"] else "#EF5350"
                tag_u_pf = f"pu_{i}"
                cvs_pf.create_rectangle(xc_pf - bar_w_pf * 0.5 + 1, baseline_y - hu_pf,
                                        xc_pf + bar_w_pf * 0.5 + 1, baseline_y,
                                        fill=col_u_pf, outline="", tags=tag_u_pf)
                hr_pf  = min(usable_h * (abs(p["r"]) / max_v_pf), ah_pf)
                yr_pf  = baseline_y - hr_pf if p["r"] >= 0 else baseline_y
                yb_pf  = baseline_y          if p["r"] >= 0 else baseline_y + hr_pf
                col_r_pf = "#90CAF9" if p["futuro"] else "#1976D2"
                tag_r_pf  = f"pr_{i}"
                cvs_pf.create_rectangle(xc_pf + bar_w_pf * 0.5 + 3, yr_pf,
                                        xc_pf + bar_w_pf * 1.5 + 3, yb_pf,
                                        fill=col_r_pf, outline="", tags=tag_r_pf)
                fill_lbl_pf = "gray" if p["futuro"] else self.TEXT_COLOR
                cvs_pf.create_text(xc_pf, PT_pf + ah_pf + 13, anchor="center",
                                   text=MESI_BREVI[p["m"] - 1],
                                   font=("Arial", 7, "bold"), fill=fill_lbl_pf)
                segno_pf = "+" if p["r"] >= 0 else ""
                tip_e = f"{nm_pf} — Entrate: {_fmt_eur(p['e'])}"
                tip_u = f"{nm_pf} — Uscite: {_fmt_eur(p['u'])}"
                tip_r = f"{nm_pf} — Risparmio: {segno_pf}{_fmt_eur(p['r'])}"
                cvs_pf.tag_bind(tag_e_pf, "<Enter>", lambda e, t=tip_e: self.show_tooltip(e, t))
                cvs_pf.tag_bind(tag_e_pf, "<Leave>", lambda e: self.hide_tooltip())
                cvs_pf.tag_bind(tag_u_pf, "<Enter>", lambda e, t=tip_u: self.show_tooltip(e, t))
                cvs_pf.tag_bind(tag_u_pf, "<Leave>", lambda e: self.hide_tooltip())
                cvs_pf.tag_bind(tag_r_pf, "<Enter>", lambda e, t=tip_r: self.show_tooltip(e, t))
                cvs_pf.tag_bind(tag_r_pf, "<Leave>", lambda e: self.hide_tooltip())
                for tag_pf, tipo_filt_pf in [(tag_e_pf, "Entrata"), (tag_u_pf, "Uscita"), (tag_r_pf, None)]:
                    cvs_pf.tag_bind(tag_pf, "<Double-1>",
                        lambda e, m=p["m"], n=nm_pf, tf=tipo_filt_pf, fut=p["futuro"]:
                            _scelta_anno_pf(m, n, tf, fut))
            lx_pf, ly_pf = PL_pf + 8, PT_pf + 10
            for colore_pf, testo_pf in [("#4CAF50","Entrate"),("#EF5350","Uscite"),("#1976D2","Risparmio")]:
                cvs_pf.create_rectangle(lx_pf, ly_pf - 4, lx_pf + 8, ly_pf + 4, fill=colore_pf, outline="")
                cvs_pf.create_text(lx_pf + 11, ly_pf, anchor="w", text=testo_pf,
                                   font=("Arial", 7), fill=self.TEXT_COLOR)
                lx_pf += 65
            cvs_pf.create_text(lx_pf, ly_pf, anchor="w", text="(sbiadito=proiezione)",
                               font=("Arial", 7), fill="gray")
        self.stats_canvas.bind("<Configure>", _draw_proj_inline)
        self.stats_canvas.after(100, _draw_proj_inline)
    elif tipo in ("grafico", "grafico_mensile", "grafico_saldo"):
        if hasattr(self, 'stats_hint_label'):
            self.stats_hint_label.grid_remove()
        self.stats_canvas = tk.Canvas(parent_frame, bg=self.COLOR_WIDGET_BG, highlightthickness=0)
        self.stats_canvas.pack(fill=tk.BOTH, expand=True)
        nomi_mesi_italiano = [
            "", "Gen", "Feb", "Mar", "Apr", "Mag", "Giu", 
            "Lug", "Ago", "Set", "Ott", "Nov", "Dic"
        ]
        oggi = datetime.date.today()
        anno_corrente = oggi.year
        if tipo == "grafico":
            self.stats_view_mode.set("grafico")
            category_totals = defaultdict(float)
            for giorno, entries in self.spese.items():
                if giorno.year != anno_corrente: 
                    continue
                for entry in entries:
                    if isinstance(entry, dict):
                        categoria = entry.get("categoria", "Altro")
                        importo = entry.get("importo", 0)
                        tipo_voce = entry.get("tipo", "")
                    elif isinstance(entry, tuple) and len(entry) >= 4:
                        categoria = entry[0]
                        importo = entry[2]
                        tipo_voce = entry[3]
                    else:
                        continue
                    if tipo_voce == "Uscita" and importo > 0:
                        category_totals[categoria] += importo
            self.data_for_chart = [{'label': cat, 'value': val} for cat, val in category_totals.items()]
            self.data_for_chart.sort(key=lambda x: x['value'], reverse=True)
            self.total_value = sum(item['value'] for item in self.data_for_chart)
            if not self.data_for_chart:
                self.stats_canvas.after(50, lambda: self.stats_canvas.create_text(
                    self.stats_canvas.winfo_width() // 2, self.stats_canvas.winfo_height() // 2,
                    text="Nessuna spesa da visualizzare", font=("Helvetica", 16), fill="gray"
                ))
                return
            self.stats_canvas.bind("<Configure>", self.draw_bar_chart)
            self.stats_canvas.after(100, self.draw_bar_chart) 
        elif tipo == "grafico_mensile":
            self.visualizza_tutti_gli_anni = False
            self.stats_view_mode.set("grafico_mensile")
            mensili = defaultdict(lambda: {"Entrata": 0.0, "Uscita": 0.0})
            for giorno, entries in self.spese.items():
                if giorno.year != anno_corrente: continue
                for entry in entries:
                    if isinstance(entry, dict):
                        imp = entry.get("importo", 0)
                        tipo_voce = entry.get("tipo", "")
                    elif isinstance(entry, tuple) and len(entry) >= 4:
                        imp = entry[2]
                        tipo_voce = entry[3]
                    else: continue
                    mese = giorno.month
                    if tipo_voce in ("Entrata", "Uscita"):
                        mensili[mese][tipo_voce] += imp
            self.data_for_chart = []
            for mese in range(1, 13):
                self.data_for_chart.append({
                    "label": nomi_mesi_italiano[mese],
                    "entrata": mensili[mese]["Entrata"],
                    "uscita": mensili[mese]["Uscita"]
                })
            self.stats_canvas.bind("<Configure>", self.draw_mensile_chart)
            self.stats_canvas.after(100, self.draw_mensile_chart) 
        elif tipo == "grafico_saldo":
            self.visualizza_tutti_gli_anni = False
            self.stats_view_mode.set("grafico_saldo")
            mensili = defaultdict(lambda: {"Entrata": 0.0, "Uscita": 0.0})
            for giorno, entries in self.spese.items():
                if giorno.year != anno_corrente: continue
                for entry in entries:
                    if isinstance(entry, dict):
                        imp = entry.get("importo", 0)
                        tipo_voce = entry.get("tipo", "")
                    elif isinstance(entry, tuple) and len(entry) >= 4:
                        imp = entry[2]
                        tipo_voce = entry[3]
                    else: continue
                    mese = giorno.month
                    if tipo_voce == "Entrata":
                        mensili[mese]["Entrata"] += imp
                    elif tipo_voce == "Uscita":
                        mensili[mese]["Uscita"] += imp
            self.data_for_chart = []
            max_abs_val = 0
            for mese in range(1, 13):
                saldo = mensili[mese]["Entrata"] - mensili[mese]["Uscita"]
                self.data_for_chart.append({
                    "label": nomi_mesi_italiano[mese],
                    "saldo": saldo
                })
                if abs(saldo) > max_abs_val:
                    max_abs_val = abs(saldo)
            if max_abs_val == 0:
                self.stats_canvas.after(50, lambda: self.stats_canvas.create_text(
                    self.stats_canvas.winfo_width() // 2, self.stats_canvas.winfo_height() // 2,
                    text="Nessun saldo disponibile (tutti i saldi sono zero).",
                    font=("Helvetica", 12), fill="gray"
                ))
                return
            self.stats_canvas.bind("<Configure>", self.draw_saldo_chart)
            self.stats_canvas.after(100, self.draw_saldo_chart) 
    else:
        if hasattr(self, 'stats_hint_label'):
            self.stats_hint_label.grid()
        self.stats_table = ttk.Treeview(parent_frame, columns=("A", "B", "C", "D", "E", "F"), show="headings")
        headers = {
            "A": "Data", "B": "Categoria", "C": "Descrizione",
            "D": "Importo", "E": "Tipo", "F": "Conto/Varia"
        }
        for col in headers:
            self.stats_table.heading(col, text=headers[col], command=lambda _col=col: self.treeview_sort_column(self.stats_table, _col, False))
        self.stats_table.column("A", width=100, anchor="center")
        self.stats_table.column("B", width=150, anchor="center")
        self.stats_table.column("C", width=250, anchor="w")
        self.stats_table.column("D", width=100, anchor="e")
        self.stats_table.column("E", width=70, anchor="center")
        self.stats_table.column("F", width=100, anchor="center")
        if self.chiamato_da_carosello:
            self.set_stats_mode("mese")
        else:
            self.set_stats_mode("giorno")
        self.stats_table.tag_configure("uscita", foreground="red")
        self.stats_table.tag_configure("entrata", foreground="green")
        self.stats_table.tag_configure("futuro", foreground="#E5C07B", font=("Arial", 9, "italic"))
        self.stats_table.bind("<Double-1>", self.on_stats_table_double_click)
        self.stats_table.bind("<ButtonRelease-1>", self.on_table_click)
        self._bind_tooltip_metodo(self.stats_table, col_desc=2)
        self.stats_table.bind("<Button-3>", self.on_stats_table_right_click)
        self.stats_table.pack(fill=tk.BOTH, expand=True) 
        if hasattr(self, 'stats_label'):
            self.stats_label.grid()
        if hasattr(self, 'totali_label'):
            self.totali_label.pack(side=tk.LEFT)
        self.stats_view_mode.set("tabella")
        for btn in self.filtri_temporali:
            btn.pack(side=tk.LEFT, padx=1) 
            
