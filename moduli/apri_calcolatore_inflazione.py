#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk

from moduli.modello_spesa import campo

def apri_calcolatore_inflazione(self):
    if hasattr(self, '_win_inflazione') and self._win_inflazione and self._win_inflazione.winfo_exists():
        self._win_inflazione.lift()
        self._win_inflazione.focus_force()
        return
    ISTAT_NIC = {
        2000: 2.6,  2001: 2.3,  2002: 2.6,  2003: 2.8,  2004: 2.3,
        2005: 2.2,  2006: 2.2,  2007: 2.0,  2008: 3.5,  2009: 0.8,
        2010: 1.6,  2011: 2.9,  2012: 3.3,  2013: 1.2,  2014: 0.2,
        2015: 0.1,  2016: -0.1, 2017: 1.3,  2018: 1.2,  2019: 0.6,
        2020: -0.1, 2021: 1.9,  2022: 8.1,  2023: 5.7,  2024: 1.0,
        2025: 1.5,
    }
    ANNI = sorted(ISTAT_NIC.keys())
    try:
        uscite_per_mese = {}
        for d, voci in self.spese.items():
            key = (d.year, d.month)
            for v in voci:
                if campo(v, "tipo", "") == "Uscita":
                    uscite_per_mese[key] = uscite_per_mese.get(key, 0.0) + float(campo(v, "importo", 0.0))
        imp_default = str(int(round(sum(uscite_per_mese.values()) / len(uscite_per_mese), 0))) if uscite_per_mese else "1000"
    except Exception:
        imp_default = "1000"
    try:
        primo_anno_db = min(d.year for d in self.spese)
        if primo_anno_db in ISTAT_NIC and primo_anno_db < max(ANNI):
            anno_da_default = str(primo_anno_db)
        else:
            anno_da_default = str(max(ANNI) - 5)
    except Exception:
        anno_da_default = str(max(ANNI) - 5)
    win = tk.Toplevel(self)
    self._win_inflazione = win
    win.transient(self)
    win.withdraw()
    win.title("Calcolatore Inflazione — ISTAT NIC")
    win.configure(bg=self.COLOR_TOPLEVEL)
    win.resizable(False, False)
    W, H = 1200, 600
    self.update_idletasks()
    pos_x = self.winfo_rootx() + (self.winfo_width()  // 2) - (W // 2)
    pos_y = self.winfo_rooty() + (self.winfo_height() // 2) - (H // 2)
    win.geometry(f"{W}x{H}+{max(0, pos_x)}+{max(0, pos_y)}")
    def _chiudi():
        self.unbind("<Map>")
        self.unbind("<Unmap>")
        win.destroy()
    win.bind("<Escape>", lambda e: _chiudi())
    win.protocol("WM_DELETE_WINDOW", _chiudi)
    def _on_iconify(e):
        if self.state() == "iconic":
            win.withdraw()
        else:
            win.deiconify()
    self.bind("<Map>",   _on_iconify)
    self.bind("<Unmap>", _on_iconify)
    def fmt_eur(v):
        return f"€ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    def fmt_pct(v):
        return f"{v:+.1f} %"
    hdr = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    hdr.pack(fill=tk.X, padx=15, pady=(12, 4))
    img_calc = self.icone_gui.get("calcolatrice")
    tk.Label(hdr, image=img_calc, text="  Calcolatore Inflazione — ISTAT NIC",
             compound="left", bg=self.COLOR_TOPLEVEL, fg=self.COLOR_HEADER,
             font=("Arial", 13, "bold")).pack(side=tk.LEFT)
    ttk.Separator(win, orient="horizontal").pack(fill=tk.X, padx=15, pady=(0, 10))
    corpo = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    corpo.pack(fill=tk.BOTH, expand=True, padx=15)
    col_sx = tk.Frame(corpo, bg=self.COLOR_TOPLEVEL, width=340)
    col_sx.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
    col_sx.pack_propagate(False)
    col_dx = tk.Frame(corpo, bg=self.COLOR_TOPLEVEL,
                      highlightbackground=self.COLOR_TOPLEVEL, highlightthickness=1)
    col_dx.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    def _lbl(parent, testo):
        tk.Label(parent, text=testo, bg=self.COLOR_TOPLEVEL,
                 fg=self.TEXT_COLOR, font=("Arial", 9, "bold")).pack(anchor="w", pady=(8, 1))
    _lbl(col_sx, f"Importo iniziale (€)  —  media mensile uscite: {imp_default} €")
    var_imp = tk.StringVar(value=imp_default)
    ent_imp = ttk.Entry(col_sx, textvariable=var_imp, font=("Arial", 11), width=22, justify="center")
    ent_imp.pack(fill=tk.X, pady=(0, 2))
    riga_anni = tk.Frame(col_sx, bg=self.COLOR_TOPLEVEL)
    riga_anni.pack(fill=tk.X, pady=(4, 0))
    f_da = tk.Frame(riga_anni, bg=self.COLOR_TOPLEVEL)
    f_da.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 6))
    tk.Label(f_da, text="Anno di partenza:", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 9, "bold")).pack(anchor="w")
    var_da = tk.StringVar(value=anno_da_default)
    cb_da = ttk.Combobox(f_da, textvariable=var_da, values=[str(a) for a in ANNI],
                         state="readonly", width=8, font=("Arial", 10), style="Border.TCombobox")
    cb_da.pack(fill=tk.X)
    f_a = tk.Frame(riga_anni, bg=self.COLOR_TOPLEVEL)
    f_a.pack(side=tk.LEFT, expand=True, fill=tk.X)
    tk.Label(f_a, text="Anno di arrivo:", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 9, "bold")).pack(anchor="w")
    var_a = tk.StringVar(value=str(max(ANNI)))
    cb_a = ttk.Combobox(f_a, textvariable=var_a, values=[str(a) for a in ANNI],
                        state="readonly", width=8, font=("Arial", 10), style="Border.TCombobox")
    cb_a.pack(fill=tk.X)
    ttk.Separator(col_sx, orient="horizontal").pack(fill=tk.X, pady=14)
    def _metrica(parent, etichetta):
        f = tk.Frame(parent, bg=self.COLOR_TOPLEVEL,
                     highlightbackground=self.TEXT_COLOR, highlightthickness=1)
        f.pack(fill=tk.X, pady=3)
        tk.Label(f, text=etichetta, bg=self.COLOR_TOPLEVEL,
                 fg=self.TEXT_COLOR, font=("Arial", 9), anchor="w").pack(fill=tk.X, padx=8, pady=(5, 0))
        val_lbl = tk.Label(f, text="—", bg=self.COLOR_TOPLEVEL,
                           fg=self.COLOR_HEADER, font=("Arial", 14, "bold"), anchor="w")
        val_lbl.pack(fill=tk.X, padx=8, pady=(0, 5))
        sub_lbl = tk.Label(f, text="", bg=self.COLOR_TOPLEVEL,
                           fg=self.TEXT_COLOR, font=("Arial", 8), anchor="w")
        sub_lbl.pack(fill=tk.X, padx=8, pady=(0, 4))
        return val_lbl, sub_lbl
    lbl_riv,  sub_riv  = _metrica(col_sx, "Valore rivalutato")
    lbl_perd, sub_perd = _metrica(col_sx, "Potere d'acquisto perso")
    riga_stat = tk.Frame(col_sx, bg=self.COLOR_TOPLEVEL)
    riga_stat.pack(fill=tk.X, pady=(6, 0))
    def _stat(parent, etichetta):
        f = tk.Frame(parent, bg=self.COLOR_TOPLEVEL,
                     highlightbackground=self.TEXT_COLOR, highlightthickness=1)
        f.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Label(f, text=etichetta, bg=self.COLOR_TOPLEVEL,
                 fg=self.TEXT_COLOR, font=("Arial", 8), anchor="center").pack(pady=(4, 0))
        v = tk.Label(f, text="—", bg=self.COLOR_TOPLEVEL,
                     fg=self.COLOR_HEADER, font=("Arial", 11, "bold"), anchor="center")
        v.pack(pady=(0, 4))
        return v
    lbl_tot   = _stat(riga_stat, "Inflazione totale")
    lbl_nanni = _stat(riga_stat, "Anni")
    lbl_media = _stat(riga_stat, "Media annua")
    lbl_badge = tk.Label(col_sx, text="", bg=self.COLOR_TOPLEVEL,
                         fg=self.TEXT_COLOR, font=("Arial", 9, "italic"))
    lbl_badge.pack(anchor="w", pady=(8, 0))
    cv = tk.Canvas(col_dx, bg=self.COLOR_TOPLEVEL, highlightthickness=0)
    cv.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
    _dati_grafico = [None]
    def _disegna_grafico(labels, valori):
        cv.delete("all")
        if not valori or len(valori) < 2:
            return
        cw = cv.winfo_width()
        ch = cv.winfo_height()
        if cw < 10 or ch < 10:
            return
        pad_l, pad_r, pad_t, pad_b = 65, 20, 20, 40
        n   = len(valori)
        mn  = min(valori)
        mx  = max(valori)
        rng = mx - mn if mx != mn else 1
        def px(i):
            return pad_l + (i / (n - 1)) * (cw - pad_l - pad_r)
        def py(v):
            return pad_t + (1 - (v - mn) / rng) * (ch - pad_t - pad_b)
        grid_color  = "#444444" if self.COLOR_TOPLEVEL != "white" else "#DDDDDD"
        area_color  = "#1a3a2a" if self.COLOR_TOPLEVEL != "white" else "#D6EFE6"
        label_color = self.TEXT_COLOR
        for k in range(5):
            yy = pad_t + k * (ch - pad_t - pad_b) / 4
            cv.create_line(pad_l, yy, cw - pad_r, yy, fill=grid_color, dash=(3, 4))
            vv = mx - k * rng / 4
            cv.create_text(pad_l - 4, yy,
                           text=f"€{vv:,.0f}".replace(",", "."),
                           anchor="e", font=("Arial", 8), fill=label_color)
        pts = [pad_l, ch - pad_b]
        for i, v in enumerate(valori):
            pts += [px(i), py(v)]
        pts += [px(n - 1), ch - pad_b]
        cv.create_polygon(pts, fill=area_color, outline="")
        for i in range(n - 1):
            cv.create_line(px(i), py(valori[i]), px(i + 1), py(valori[i + 1]),
                           fill="#1D9E75", width=2)
        step = max(1, n // 10)
        for i, v in enumerate(valori):
            cv.create_oval(px(i) - 3, py(v) - 3, px(i) + 3, py(v) + 3,
                           fill="#1D9E75", outline=self.COLOR_TOPLEVEL, width=1)
            if i % step == 0 or i == n - 1:
                cv.create_text(px(i), ch - pad_b + 14, text=labels[i],
                               font=("Arial", 8), fill=label_color, anchor="center")
    def _calcola(*_):
        try:
            imp = float(var_imp.get().replace(",", ".").replace("€", "").strip())
        except ValueError:
            return
        if imp <= 0:
            return
        try:
            da = int(var_da.get())
            a  = int(var_a.get())
        except ValueError:
            return
        if da >= a:
            return
        coeff  = 1.0
        labels = [str(da)]
        valori = [imp]
        for y in range(da + 1, a + 1):
            coeff *= 1 + (ISTAT_NIC.get(y, 2.0) / 100)
            labels.append(str(y))
            valori.append(round(imp * coeff, 2))
        rivalutato = imp * coeff
        perdita    = rivalutato - imp
        inf_tot    = (coeff - 1) * 100
        n_anni     = a - da
        media      = (pow(coeff, 1 / n_anni) - 1) * 100 if n_anni > 0 else 0
        lbl_riv.config(text=fmt_eur(rivalutato),
                       fg=self.COLOR_GREEN if rivalutato > imp else self.TEXT_COLOR)
        sub_riv.config(text=f"Equivale a {fmt_eur(imp)} del {da}")
        lbl_perd.config(text=fmt_eur(perdita), fg=self.COLOR_RED)
        sub_perd.config(text=f"{fmt_pct(inf_tot)} rispetto al {da}")
        lbl_tot.config(text=fmt_pct(inf_tot))
        lbl_nanni.config(text=f"{n_anni} anni")
        lbl_media.config(text=f"{media:.2f}%/a")
        if inf_tot > 20:
            lbl_badge.config(text="⚠  Inflazione elevata nel periodo", fg=self.COLOR_RED)
        else:
            lbl_badge.config(text="✔  Inflazione moderata nel periodo", fg=self.COLOR_GREEN)
        _dati_grafico[0] = (labels, valori)
        win.after(50, lambda: _disegna_grafico(labels, valori))
    var_imp.trace_add("write", _calcola)
    cb_da.bind("<<ComboboxSelected>>", _calcola)
    cb_a.bind("<<ComboboxSelected>>",  _calcola)
    cv.bind("<Configure>", lambda e: (
        _disegna_grafico(*_dati_grafico[0]) if _dati_grafico[0] else None
    ))
    ttk.Separator(win, orient="horizontal").pack(fill=tk.X, padx=15, pady=(8, 0))
    btn_frame = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    btn_frame.pack(fill=tk.X, padx=15, pady=8)
    def _reset():
        var_imp.set(imp_default)
        var_da.set(anno_da_default)
        var_a.set(str(max(ANNI)))
        _calcola()
    pulsanti = [
        ("reset",  " Reimposta", lambda e: _reset(),  "LEFT"),
        ("chiudi", " Chiudi",    lambda e: _chiudi(), "RIGHT"),
    ]
    for ico, testo, cmd, lato in pulsanti:
        img = self.icone_gui.get(ico)
        btn = ttk.Label(btn_frame, compound="left", image=img,
                        text=testo if img else testo.strip(),
                        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                        cursor="hand2", padding=(10, 5))
        btn.pack(side=tk.LEFT if lato == "LEFT" else tk.RIGHT, padx=4)
        btn.bind("<Button-1>", cmd)
    win.deiconify()
    win.lift()
    win.focus_force()
    win.after(100, _calcola)

