#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import tkinter as tk
from tkinter import ttk

from moduli.modello_spesa import campo

MESI_ABBR = ["Gen","Feb","Mar","Apr","Mag","Giu","Lug","Ago","Set","Ott","Nov","Dic"]
MESI_FULL = ["Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno",
             "Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"]

def formatta_italiano(numero, segno=False, decimali=2):
    fmt = "{:+,.%df}" % decimali if segno else "{:,.%df}" % decimali
    return fmt.format(numero).replace(',', 'X').replace('.', ',').replace('X', '.')

def apri_andamento_risparmio(self):
    if hasattr(self, "win_risparmio") and self.win_risparmio and self.win_risparmio.winfo_exists():
        self.win_risparmio.lift()
        self.win_risparmio.focus_force()
        return

    oggi = datetime.date.today()
    anno_corrente = oggi.year
    _tip_win = [None, None]

    def _calcola_mese(anno, includi_futuri):
        entrate_m = [0.0] * 12
        uscite_m  = [0.0] * 12
        for d, voci in self.spese.items():
            if d.year != anno:
                continue
            if not includi_futuri and d > oggi:
                continue
            m = d.month - 1
            for voce in voci:
                try:
                    imp  = float(campo(voce, "importo", 0.0))
                    tipo = campo(voce, "tipo", "")
                except Exception:
                    continue
                if tipo == "Entrata":
                    entrate_m[m] += imp
                else:
                    uscite_m[m] += imp
        saldi_m = [entrate_m[i] - uscite_m[i] for i in range(12)]
        return entrate_m, uscite_m, saldi_m

    def _anni_presenti():
        anni = {d.year for d in self.spese}
        anni.add(anno_corrente)
        return sorted(anni)

    def _calcola_anno_totale(anno, includi_futuri):
        e, u, s = _calcola_mese(anno, includi_futuri)
        return sum(e), sum(u), sum(e) - sum(u)

    def _calcola_tutti_anni(includi_futuri):
        anni = _anni_presenti()
        entrate_a, uscite_a, saldi_a = [], [], []
        for a in anni:
            e, u, s = _calcola_anno_totale(a, includi_futuri)
            entrate_a.append(e); uscite_a.append(u); saldi_a.append(s)
        etichette = [str(a) for a in anni]
        return etichette, entrate_a, uscite_a, saldi_a

    def _calcola_tutti_mensile(includi_futuri):
        anni = _anni_presenti()
        etichette, entrate_t, uscite_t, saldi_t = [], [], [], []
        for a in anni:
            e, u, s = _calcola_mese(a, includi_futuri)
            for i in range(12):
                etichette.append(f"{MESI_ABBR[i]} {a}")
                entrate_t.append(e[i]); uscite_t.append(u[i]); saldi_t.append(s[i])
        return etichette, entrate_t, uscite_t, saldi_t

    def _apri_dettaglio(anno, mese=None, tipo=None, titolo=""):
        data_filter = {"anno": str(anno), "tipo": tipo}
        if mese is not None:
            data_filter["mese"] = mese
        self.mostra_transazioni_popup(data_filter, titolo)

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
        _tip_win[1] = widget.after(500, _mostra)

    def _tooltip_hide(event):
        if _tip_win[1]:
            try: event.widget.after_cancel(_tip_win[1])
            except: pass
            _tip_win[1] = None
        if _tip_win[0]:
            try: _tip_win[0].destroy()
            except: pass
            _tip_win[0] = None

    win = tk.Toplevel(self)
    self.win_risparmio = win
    win.withdraw()
    win.title("Andamento Risparmio")
    win.configure(bg=self.COLOR_TOPLEVEL)
    W_WIN, H_WIN = 1400, 680
    self.update_idletasks()
    px = self.winfo_rootx() + (self.winfo_width()  - W_WIN) // 2
    py = self.winfo_rooty() + (self.winfo_height() - H_WIN) // 2
    win.geometry(f"{W_WIN}x{H_WIN}+{max(0,px)}+{max(0,py)}")
    win.minsize(W_WIN, H_WIN)
    win.transient(self)
    win.bind("<Escape>", lambda e: win.destroy())

    bar_globale = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    bar_globale.pack(fill="x", padx=14, pady=(10, 4))
    includi_futuri_var = tk.BooleanVar(value=True)

    leg = tk.Frame(bar_globale, bg=self.COLOR_TOPLEVEL)
    leg.pack(side="right", padx=10)
    tk.Label(leg, text="■ Entrate", bg=self.COLOR_TOPLEVEL,
             fg=self.COLOR_GREEN_SMOOTH, font=("Arial", 9)).pack(side="left", padx=6)
    tk.Label(leg, text="■ Uscite", bg=self.COLOR_TOPLEVEL,
             fg=self.COLOR_RED_SMOOTH, font=("Arial", 9)).pack(side="left", padx=6)
    tk.Label(leg, text="● Saldo", bg=self.COLOR_TOPLEVEL,
             fg=self.COLOR_HIGHLIGHT, font=("Arial", 9)).pack(side="left", padx=6)

    ttk.Checkbutton(bar_globale, text="Includi movimenti futuri",
                     variable=includi_futuri_var,
                     command=lambda: _aggiorna_tutto()).pack(side="left", padx=16)

    img_mouse = self.icone_gui.get("mouse")
    tk.Label(bar_globale, text="Doppio clic su una barra / punto / riga → dettaglio transazioni",
             image=img_mouse, compound="right",
             bg=self.COLOR_TOPLEVEL, fg="gray", font=("Arial", 8, "italic")).pack(side="left", padx=20)

    notebook = ttk.Notebook(win)
    notebook.pack(fill="both", expand=True, padx=14, pady=(4, 4))

    tab1 = tk.Frame(notebook, bg=self.COLOR_TOPLEVEL)
    tab2 = tk.Frame(notebook, bg=self.COLOR_TOPLEVEL)
    tab3 = tk.Frame(notebook, bg=self.COLOR_TOPLEVEL)
    img_tab_barre = self.icone_gui.get("report")
    img_tab_linea = self.icone_gui.get("grafico_linea")
    img_tab_tabella = self.icone_gui.get("anagrafica")
    notebook.add(tab1, image=img_tab_barre, text="  Grafico a Barre  ", compound="left")
    notebook.add(tab2, image=img_tab_linea, text="  Grafico a Linea  ", compound="left")
    notebook.add(tab3, image=img_tab_tabella, text="  Tabella  ", compound="left")

    anni_disp = sorted(_anni_presenti(), reverse=True)
    valori_anno_tab1 = [str(a) for a in anni_disp] + ["Tutti"]

    top1 = tk.Frame(tab1, bg=self.COLOR_TOPLEVEL)
    top1.pack(fill="x", padx=4, pady=(6, 2))
    tk.Label(top1, text="Anno:", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 10, "bold")).pack(side="left")
    combo_anno1 = ttk.Combobox(top1, values=valori_anno_tab1, width=8,
                                state="readonly", font=("Arial", 10), style="Border.TCombobox")
    combo_anno1.set(str(anno_corrente))
    combo_anno1.pack(side="left", padx=8)

    canvas1 = tk.Canvas(tab1, bg=self.COLOR_BACKGROUND, highlightthickness=0)
    canvas1.pack(fill="both", expand=True, padx=10, pady=(4, 4))

    footer1 = tk.Frame(tab1, bg=self.COLOR_TOPLEVEL)
    footer1.pack(fill="x", padx=10, pady=(0, 8))
    lbl_tot_e1 = tk.Label(footer1, text="", bg=self.COLOR_TOPLEVEL, fg=self.COLOR_GREEN, font=("Arial", 9, "bold"))
    lbl_tot_e1.pack(side="left", padx=16)
    lbl_tot_u1 = tk.Label(footer1, text="", bg=self.COLOR_TOPLEVEL, fg=self.COLOR_RED, font=("Arial", 9, "bold"))
    lbl_tot_u1.pack(side="left", padx=16)
    lbl_tot_s1 = tk.Label(footer1, text="", bg=self.COLOR_TOPLEVEL, font=("Arial", 9, "bold"))
    lbl_tot_s1.pack(side="left", padx=16)

    def _disegna_barre(categorie, entrate_v, uscite_v, saldi_v, ctx_annuale, anno_ctx=None):
        if _tip_win[0]:
            try: _tip_win[0].destroy()
            except: pass
            _tip_win[0] = None
        canvas1.delete("all")
        canvas1.update_idletasks()
        W = canvas1.winfo_width()
        H = canvas1.winfo_height()
        if W < 10:
            canvas1.after(80, lambda: _disegna_barre(categorie, entrate_v, uscite_v, saldi_v, ctx_annuale, anno_ctx))
            return
        MARG_L, MARG_R, MARG_T, MARG_B = 60, 20, 30, 55
        n = len(categorie)
        slot_w = (W - MARG_L - MARG_R) / n
        bar_w = slot_w * 0.30
        tutti_val = entrate_v + uscite_v + [abs(s) for s in saldi_v]
        max_val = max(tutti_val) if max(tutti_val) > 0 else 1
        y_base = H - MARG_B
        area_h = H - MARG_T - MARG_B
        canvas1.create_line(MARG_L, y_base, W - MARG_R, y_base, fill=self.TEXT_COLOR, width=1)
        for pct in (0.25, 0.5, 0.75, 1.0):
            gy = y_base - area_h * pct
            canvas1.create_line(MARG_L, gy, W - MARG_R, gy, fill="#444444", dash=(3, 6))
            canvas1.create_text(MARG_L - 6, gy, text=formatta_italiano(max_val * pct, decimali=0),
                                 font=("Arial", 7, "bold"), fill=self.TEXT_COLOR, anchor="e")
        for i in range(n):
            cx = MARG_L + slot_w * i + slot_w / 2
            e_val, u_val, s_val = entrate_v[i], uscite_v[i], saldi_v[i]
            gap = 2
            if ctx_annuale:
                titolo_ctx = f"Anno {categorie[i]}"
                anno_i = int(categorie[i])
                mese_i = None
            else:
                titolo_ctx = f"{categorie[i]} {anno_ctx}"
                anno_i = anno_ctx
                mese_i = i + 1
            tip_txt = (f"{titolo_ctx}\nEntrate:  {formatta_italiano(e_val)} €\n"
                       f"Uscite:   {formatta_italiano(u_val)} €\nSaldo:    {formatta_italiano(s_val, segno=True)} €")

            e_h = (e_val / max_val) * area_h if e_val > 0 else 0
            x0e, x1e = cx - bar_w * 1.5 - gap, cx - bar_w * 0.5 - gap
            if e_val > 0:
                rid = canvas1.create_rectangle(x0e, y_base - e_h, x1e, y_base,
                                                fill=self.COLOR_GREEN_SMOOTH, outline="")
                canvas1.tag_bind(rid, "<Enter>", lambda e, t=tip_txt: _tooltip_show(e, t))
                canvas1.tag_bind(rid, "<Leave>", _tooltip_hide)
                canvas1.tag_bind(rid, "<Double-Button-1>",
                                  lambda e, a=anno_i, m=mese_i, tt=titolo_ctx: _apri_dettaglio(
                                      a, m, "Entrata", f"Dettaglio Entrate - {tt}"))
                canvas1.create_text((x0e+x1e)/2, y_base - e_h - 8, text=formatta_italiano(e_val, decimali=0),
                                     font=("Arial", 7, "bold"), fill=self.COLOR_GREEN_SMOOTH)

            u_h = (u_val / max_val) * area_h if u_val > 0 else 0
            x0u, x1u = cx - bar_w * 0.5, cx + bar_w * 0.5
            if u_val > 0:
                rid = canvas1.create_rectangle(x0u, y_base - u_h, x1u, y_base,
                                                fill=self.COLOR_RED_SMOOTH, outline="")
                canvas1.tag_bind(rid, "<Enter>", lambda e, t=tip_txt: _tooltip_show(e, t))
                canvas1.tag_bind(rid, "<Leave>", _tooltip_hide)
                canvas1.tag_bind(rid, "<Double-Button-1>",
                                  lambda e, a=anno_i, m=mese_i, tt=titolo_ctx: _apri_dettaglio(
                                      a, m, "Uscita", f"Dettaglio Uscite - {tt}"))
                canvas1.create_text((x0u+x1u)/2, y_base - u_h - 8, text=formatta_italiano(u_val, decimali=0),
                                     font=("Arial", 7, "bold"), fill=self.COLOR_RED_SMOOTH)

            s_col = self.COLOR_HIGHLIGHT if s_val >= 0 else self.COLOR_RED
            s_h = (abs(s_val) / max_val) * area_h if s_val != 0 else 0
            x0s, x1s = cx + bar_w * 0.5 + gap, cx + bar_w * 1.5 + gap
            if abs(s_val) > 0:
                rid = canvas1.create_rectangle(x0s, y_base - s_h, x1s, y_base, fill=s_col, outline="")
                canvas1.tag_bind(rid, "<Enter>", lambda e, t=tip_txt: _tooltip_show(e, t))
                canvas1.tag_bind(rid, "<Leave>", _tooltip_hide)
                canvas1.tag_bind(rid, "<Double-Button-1>",
                                  lambda e, a=anno_i, m=mese_i, tt=titolo_ctx: _apri_dettaglio(
                                      a, m, None, f"Dettaglio Saldo - {tt}"))
                canvas1.create_text((x0s+x1s)/2, y_base - s_h - 8, text=formatta_italiano(s_val, segno=True, decimali=0),
                                     font=("Arial", 7, "bold"), fill=s_col)

            canvas1.create_text(cx, y_base + 14, text=categorie[i],
                                 font=("Arial", 8), fill=self.TEXT_COLOR)

        tot_e, tot_u = sum(entrate_v), sum(uscite_v)
        tot_s = tot_e - tot_u
        col_s = self.COLOR_GREEN if tot_s >= 0 else self.COLOR_RED
        lbl_tot_e1.config(text=f"Entrate Totali:  {formatta_italiano(tot_e)} €")
        lbl_tot_u1.config(text=f"Uscite Totali:   {formatta_italiano(tot_u)} €")
        lbl_tot_s1.config(text=f"Saldo Totale:    {formatta_italiano(tot_s, segno=True)} €", fg=col_s)

    def _aggiorna_tab1(event=None):
        sel = combo_anno1.get()
        futuri = includi_futuri_var.get()
        if sel == "Tutti":
            etichette, e, u, s = _calcola_tutti_anni(futuri)
            _disegna_barre(etichette, e, u, s, ctx_annuale=True)
        else:
            anno = int(sel)
            e, u, s = _calcola_mese(anno, futuri)
            _disegna_barre(MESI_ABBR, e, u, s, ctx_annuale=False, anno_ctx=anno)

    combo_anno1.bind("<<ComboboxSelected>>", _aggiorna_tab1)
    canvas1.bind("<Configure>", lambda e: _aggiorna_tab1())

    top2 = tk.Frame(tab2, bg=self.COLOR_TOPLEVEL)
    top2.pack(fill="x", padx=4, pady=(6, 2))
    tk.Label(top2, text="Vista:", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 10, "bold")).pack(side="left")
    combo_vista2 = ttk.Combobox(top2, values=["Mese", "Anno", "Tutti"], width=8,
                                 state="readonly", font=("Arial", 10), style="Border.TCombobox")
    combo_vista2.set("Mese")
    combo_vista2.pack(side="left", padx=8)

    lbl_anno2 = tk.Label(top2, text="Anno:", bg=self.COLOR_TOPLEVEL,
                          fg=self.TEXT_COLOR, font=("Arial", 10, "bold"))
    lbl_anno2.pack(side="left", padx=(16, 0))
    combo_anno2 = ttk.Combobox(top2, values=[str(a) for a in anni_disp], width=8,
                                state="readonly", font=("Arial", 10), style="Border.TCombobox")
    combo_anno2.set(str(anno_corrente))
    combo_anno2.pack(side="left", padx=8)

    canvas2 = tk.Canvas(tab2, bg=self.COLOR_BACKGROUND, highlightthickness=0)
    canvas2.pack(fill="both", expand=True, padx=10, pady=(4, 4))

    footer2 = tk.Frame(tab2, bg=self.COLOR_TOPLEVEL)
    footer2.pack(fill="x", padx=10, pady=(0, 8))
    lbl_tot_e2 = tk.Label(footer2, text="", bg=self.COLOR_TOPLEVEL, fg=self.COLOR_GREEN, font=("Arial", 9, "bold"))
    lbl_tot_e2.pack(side="left", padx=16)
    lbl_tot_u2 = tk.Label(footer2, text="", bg=self.COLOR_TOPLEVEL, fg=self.COLOR_RED, font=("Arial", 9, "bold"))
    lbl_tot_u2.pack(side="left", padx=16)
    lbl_tot_s2 = tk.Label(footer2, text="", bg=self.COLOR_TOPLEVEL, font=("Arial", 9, "bold"))
    lbl_tot_s2.pack(side="left", padx=16)

    def _disegna_linea(categorie, entrate_v, uscite_v, saldi_v):
        if _tip_win[0]:
            try: _tip_win[0].destroy()
            except: pass
            _tip_win[0] = None
        canvas2.delete("all")
        canvas2.update_idletasks()
        W = canvas2.winfo_width()
        H = canvas2.winfo_height()
        if W < 10:
            canvas2.after(80, lambda: _disegna_linea(categorie, entrate_v, uscite_v, saldi_v))
            return
        n = len(categorie)
        MARG_L, MARG_R, MARG_T, MARG_B = 60, 20, 20, 55
        area_w = W - MARG_L - MARG_R
        slot_w = area_w / max(n - 1, 1) if n > 1 else area_w
        tutti_val = entrate_v + uscite_v + saldi_v + [0]
        max_val = max(tutti_val) if max(tutti_val) > 0 else 1
        min_val = min(tutti_val + [0])
        rng = (max_val - min_val) if (max_val - min_val) != 0 else 1
        y_base = H - MARG_B
        area_h = H - MARG_T - MARG_B

        def _y(val):
            return y_base - ((val - min_val) / rng) * area_h

        for pct in (0, 0.25, 0.5, 0.75, 1.0):
            gy = MARG_T + area_h * (1 - pct)
            val = min_val + rng * pct
            canvas2.create_line(MARG_L, gy, W - MARG_R, gy, fill="#444444", dash=(3, 6))
            canvas2.create_text(MARG_L - 6, gy, text=formatta_italiano(val, decimali=0),
                                 font=("Arial", 7, "bold"), fill=self.TEXT_COLOR, anchor="e")
        canvas2.create_line(MARG_L, _y(0), W - MARG_R, _y(0), fill=self.TEXT_COLOR, width=1)

        step = max(1, n // 20)
        for i in range(n):
            cx = MARG_L + slot_w * i
            if i % step == 0 or i == n - 1:
                canvas2.create_text(cx, y_base + 14, text=categorie[i],
                                     font=("Arial", 7), fill=self.TEXT_COLOR, angle=45 if n > 12 else 0)

        serie = [
            (entrate_v, self.COLOR_GREEN_SMOOTH, "Entrate"),
            (uscite_v,  self.COLOR_RED_SMOOTH,  "Uscite"),
            (saldi_v,   self.COLOR_HIGHLIGHT,   "Saldo"),
        ]
        for valori, colore, nome in serie:
            punti = []
            for i in range(n):
                cx = MARG_L + slot_w * i
                cy = _y(valori[i])
                punti.extend([cx, cy])
            if n > 1:
                canvas2.create_line(*punti, fill=colore, width=2, smooth=False)
            for i in range(n):
                cx = MARG_L + slot_w * i
                cy = _y(valori[i])
                rid = canvas2.create_oval(cx-3, cy-3, cx+3, cy+3, fill=colore, outline="")
                tip = (f"{categorie[i]}\n{nome}: {formatta_italiano(valori[i])} €\n"
                       f"Entrate:  {formatta_italiano(entrate_v[i])} €\nUscite:   {formatta_italiano(uscite_v[i])} €\n"
                       f"Saldo:    {formatta_italiano(saldi_v[i], segno=True)} €")
                canvas2.tag_bind(rid, "<Enter>", lambda e, t=tip: _tooltip_show(e, t))
                canvas2.tag_bind(rid, "<Leave>", _tooltip_hide)

        tot_e, tot_u = sum(entrate_v), sum(uscite_v)
        tot_s = tot_e - tot_u
        col_s = self.COLOR_GREEN if tot_s >= 0 else self.COLOR_RED
        lbl_tot_e2.config(text=f"Entrate Totali:  {formatta_italiano(tot_e)} €")
        lbl_tot_u2.config(text=f"Uscite Totali:   {formatta_italiano(tot_u)} €")
        lbl_tot_s2.config(text=f"Saldo Totale:    {formatta_italiano(tot_s, segno=True)} €", fg=col_s)

    def _aggiorna_tab2(event=None):
        vista = combo_vista2.get()
        futuri = includi_futuri_var.get()
        if vista == "Mese":
            lbl_anno2.pack(side="left", padx=(16, 0))
            combo_anno2.pack(side="left", padx=8)
            anno = int(combo_anno2.get())
            e, u, s = _calcola_mese(anno, futuri)
            _disegna_linea(MESI_ABBR, e, u, s)
        elif vista == "Anno":
            lbl_anno2.pack_forget()
            combo_anno2.pack_forget()
            etichette, e, u, s = _calcola_tutti_anni(futuri)
            _disegna_linea(etichette, e, u, s)
        else:  # Tutti
            lbl_anno2.pack_forget()
            combo_anno2.pack_forget()
            etichette, e, u, s = _calcola_tutti_mensile(futuri)
            _disegna_linea(etichette, e, u, s)

    combo_vista2.bind("<<ComboboxSelected>>", _aggiorna_tab2)
    combo_anno2.bind("<<ComboboxSelected>>", _aggiorna_tab2)
    canvas2.bind("<Configure>", lambda e: _aggiorna_tab2())

    top3 = tk.Frame(tab3, bg=self.COLOR_TOPLEVEL)
    top3.pack(fill="x", padx=4, pady=(6, 2))
    tk.Label(top3, text="Vista:", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 10, "bold")).pack(side="left")
    combo_vista3 = ttk.Combobox(top3, values=["Mese", "Anno", "Tutti"], width=8,
                                 state="readonly", font=("Arial", 10), style="Border.TCombobox")
    combo_vista3.set("Mese")
    combo_vista3.pack(side="left", padx=8)

    lbl_anno3 = tk.Label(top3, text="Anno:", bg=self.COLOR_TOPLEVEL,
                          fg=self.TEXT_COLOR, font=("Arial", 10, "bold"))
    lbl_anno3.pack(side="left", padx=(16, 0))
    combo_anno3 = ttk.Combobox(top3, values=[str(a) for a in anni_disp], width=8,
                                state="readonly", font=("Arial", 10), style="Border.TCombobox")
    combo_anno3.set(str(anno_corrente))
    combo_anno3.pack(side="left", padx=8)

    tree_frame = tk.Frame(tab3, bg=self.COLOR_TOPLEVEL)
    tree_frame.pack(fill="both", expand=True, padx=10, pady=(4, 8))
    cols = ("periodo", "entrate", "uscite", "saldo")
    tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
    intestazioni_tab3 = {"periodo": "Periodo", "entrate": "Entrate", "uscite": "Uscite", "saldo": "Saldo"}

    def _ordina_tab3(col, reverse):
        self.treeview_sort_column(tree, col, reverse)
        if tree.exists("totale"):
            tree.move("totale", "", "end")
        for c in cols:
            nuovo_reverse = (not reverse) if c == col else False
            tree.heading(c, command=lambda _c=c, _r=nuovo_reverse: _ordina_tab3(_c, _r))

    for col in cols:
        tree.heading(col, text=intestazioni_tab3[col],
                     command=lambda c=col: _ordina_tab3(c, False))
    tree.column("periodo", width=140, anchor="w")
    tree.column("entrate", width=140, anchor="e")
    tree.column("uscite", width=140, anchor="e")
    tree.column("saldo", width=140, anchor="e")
    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    tree.tag_configure("totale", font=("Arial", 9, "bold"))

    _tab3_ctx = {"righe": []}

    def _popola_tabella(categorie, entrate_v, uscite_v, saldi_v, righe_ctx):
        for item in tree.get_children():
            tree.delete(item)
        _tab3_ctx["righe"] = righe_ctx
        for i, cat in enumerate(categorie):
            tree.insert("", "end", iid=str(i), values=(
                cat, formatta_italiano(entrate_v[i]), formatta_italiano(uscite_v[i]), formatta_italiano(saldi_v[i], segno=True)
            ))
        tot_e, tot_u = sum(entrate_v), sum(uscite_v)
        tot_s = tot_e - tot_u
        tree.insert("", "end", iid="totale", values=(
            "TOTALE", formatta_italiano(tot_e), formatta_italiano(tot_u), formatta_italiano(tot_s, segno=True)
        ), tags=("totale",))

    def _doppio_clic_tabella(event):
        iid = tree.identify_row(event.y)
        if not iid or iid == "totale":
            return
        idx = int(iid)
        anno_i, mese_i, titolo_ctx = _tab3_ctx["righe"][idx]
        _apri_dettaglio(anno_i, mese_i, None, f"Dettaglio movimenti - {titolo_ctx}")

    tree.bind("<Double-Button-1>", _doppio_clic_tabella)

    def _aggiorna_tab3(event=None):
        vista = combo_vista3.get()
        futuri = includi_futuri_var.get()
        if vista == "Mese":
            lbl_anno3.pack(side="left", padx=(16, 0))
            combo_anno3.pack(side="left", padx=8)
            anno = int(combo_anno3.get())
            e, u, s = _calcola_mese(anno, futuri)
            righe_ctx = [(anno, i + 1, f"{MESI_FULL[i]} {anno}") for i in range(12)]
            _popola_tabella([f"{MESI_FULL[i]} {anno}" for i in range(12)], e, u, s, righe_ctx)
        elif vista == "Anno":
            lbl_anno3.pack_forget()
            combo_anno3.pack_forget()
            etichette, e, u, s = _calcola_tutti_anni(futuri)
            righe_ctx = [(int(a), None, f"Anno {a}") for a in etichette]
            _popola_tabella(etichette, e, u, s, righe_ctx)
        else:
            lbl_anno3.pack_forget()
            combo_anno3.pack_forget()
            etichette, e, u, s = _calcola_tutti_mensile(futuri)
            righe_ctx = []
            for et in etichette:
                nome_mese, anno_str = et.split(" ")
                mese_idx = MESI_ABBR.index(nome_mese) + 1
                righe_ctx.append((int(anno_str), mese_idx, et))
            _popola_tabella(etichette, e, u, s, righe_ctx)

    combo_vista3.bind("<<ComboboxSelected>>", _aggiorna_tab3)
    combo_anno3.bind("<<ComboboxSelected>>", _aggiorna_tab3)

    def _aggiorna_tutto():
        _aggiorna_tab1()
        _aggiorna_tab2()
        _aggiorna_tab3()

    img_chiudi = self.icone_gui.get("chiudi")
    frame_chiudi = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    frame_chiudi.pack(pady=(0, 12))
    btn_chiudi = tk.Label(frame_chiudi, compound="left", image=img_chiudi,
                           text="Chiudi" if img_chiudi else "✖ Chiudi",
                           background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                           cursor="hand2", padx=15, pady=6, font=("Arial", 9, "bold"))
    btn_chiudi.pack()
    btn_chiudi.bind("<Button-1>", lambda e: win.destroy())

    win.deiconify()
    win.after(80, _aggiorna_tutto)
