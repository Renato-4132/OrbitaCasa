#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import tkinter as tk
from tkinter import ttk

# Andamento Risparmio
def apri_andamento_risparmio(self):
    if hasattr(self, "win_risparmio") and self.win_risparmio and self.win_risparmio.winfo_exists():
            self.win_risparmio.lift()
            self.win_risparmio.focus_force()
            return
    MESI_ABBR = ["Gen","Feb","Mar","Apr","Mag","Giu","Lug","Ago","Set","Ott","Nov","Dic"]
    _tip_win = [None, None]
    def _calcola_anno(anno):
            oggi = datetime.date.today()
            entrate_m  = [0.0] * 12
            uscite_m   = [0.0] * 12
            for d, voci in self.spese.items():
                    if d.year != anno:
                            continue
                    if not includi_futuri_var.get() and d > oggi:
                            continue
                    m = d.month - 1
                    for voce in voci:
                            try:
                                    cat, desc, imp, tipo = voce[0], voce[1], float(voce[2]), voce[3]
                            except Exception:
                                    continue
                            if tipo == "Entrata":
                                    entrate_m[m] += imp
                            else:
                                    uscite_m[m]  += imp
            saldi_m = [entrate_m[i] - uscite_m[i] for i in range(12)]
            return entrate_m, uscite_m, saldi_m
    def _disegna(anno):
            if _tip_win[0]:
                    try:
                            _tip_win[0].destroy()
                    except:
                            pass
                    _tip_win[0] = None
            entrate_m, uscite_m, saldi_m = _calcola_anno(anno)
            canvas.delete("all")
            canvas.update_idletasks()
            W = canvas.winfo_width()
            H = canvas.winfo_height()
            if W < 10:
                    canvas.after(80, lambda: _disegna(anno))
                    return
            MARG_L = 60
            MARG_R = 20
            MARG_T = 30
            MARG_B = 55
            n      = 12
            slot_w = (W - MARG_L - MARG_R) / n
            bar_w  = slot_w * 0.30
            tutti_val = entrate_m + uscite_m + [abs(s) for s in saldi_m]
            max_val   = max(tutti_val) if max(tutti_val) > 0 else 1
            y_base    = H - MARG_B
            area_h    = H - MARG_T - MARG_B
            canvas.create_line(MARG_L, y_base, W - MARG_R, y_base,
                               fill=self.TEXT_COLOR, width=1)
            for pct in (0.25, 0.5, 0.75, 1.0):
                    gy = y_base - area_h * pct
                    canvas.create_line(MARG_L, gy, W - MARG_R, gy,
                                       fill="#444444", dash=(3, 6))
                    canvas.create_text(MARG_L - 6, gy,
                                       text=f"{max_val * pct:,.0f}",
                                       font=("Arial", 7, "bold"), fill=self.TEXT_COLOR,
                                       anchor="e")
            tooltip_items = {}
            tooltip_mese  = {}
            tooltip_tipo  = {}
            for i in range(n):
                    cx    = MARG_L + slot_w * i + slot_w / 2
                    e_val = entrate_m[i]
                    u_val = uscite_m[i]
                    s_val = saldi_m[i]
                    gap   = 2
                    e_h = (e_val / max_val) * area_h if e_val > 0 else 0
                    x0e = cx - bar_w * 1.5 - gap
                    x1e = cx - bar_w * 0.5 - gap
                    if e_val > 0:
                            rid = canvas.create_rectangle(
                                    x0e, y_base - e_h, x1e, y_base,
                                    fill=self.COLOR_GREEN_SMOOTH, outline="")
                            tooltip_items[rid] = (
                                    f"{MESI_ABBR[i]} {anno}\n"
                                    f"Entrate:  {e_val:,.2f} €\n"
                                    f"Uscite:   {u_val:,.2f} €\n"
                                    f"Saldo:    {s_val:+,.2f} €"
                            )
                            tooltip_mese[rid] = i
                            tooltip_tipo[rid] = "Entrata"
                            canvas.create_text((x0e+x1e)/2, y_base - e_h - 8,
                                               text=f"{e_val:,.0f}",
                                               font=("Arial", 7, "bold"), fill=self.COLOR_GREEN_SMOOTH)
                    u_h = (u_val / max_val) * area_h if u_val > 0 else 0
                    x0u = cx - bar_w * 0.5
                    x1u = cx + bar_w * 0.5
                    if u_val > 0:
                            rid = canvas.create_rectangle(
                                    x0u, y_base - u_h, x1u, y_base,
                                    fill=self.COLOR_RED_SMOOTH, outline="")
                            tooltip_items[rid] = (
                                    f"{MESI_ABBR[i]} {anno}\n"
                                    f"Entrate:  {e_val:,.2f} €\n"
                                    f"Uscite:   {u_val:,.2f} €\n"
                                    f"Saldo:    {s_val:+,.2f} €"
                            )
                            tooltip_mese[rid] = i
                            tooltip_tipo[rid] = "Uscita"
                            canvas.create_text((x0u+x1u)/2, y_base - u_h - 8,
                                               text=f"{u_val:,.0f}",
                                               font=("Arial", 7, "bold"), fill=self.COLOR_RED_SMOOTH)
                    s_col = self.COLOR_HIGHLIGHT if s_val >= 0 else self.COLOR_RED
                    s_h   = (abs(s_val) / max_val) * area_h if s_val != 0 else 0
                    x0s   = cx + bar_w * 0.5 + gap
                    x1s   = cx + bar_w * 1.5 + gap
                    if abs(s_val) > 0:
                            rid = canvas.create_rectangle(
                                    x0s, y_base - s_h, x1s, y_base,
                                    fill=s_col, outline="")
                            tooltip_items[rid] = (
                                    f"{MESI_ABBR[i]} {anno}\n"
                                    f"Entrate:  {e_val:,.2f} €\n"
                                    f"Uscite:   {u_val:,.2f} €\n"
                                    f"Saldo:    {s_val:+,.2f} €"
                            )
                            tooltip_mese[rid] = i
                            tooltip_tipo[rid] = None
                            canvas.create_text((x0s+x1s)/2, y_base - s_h - 8,
                                               text=f"{s_val:+,.0f}",
                                               font=("Arial", 7, "bold"), fill=s_col)
                    canvas.create_text(cx, y_base + 14,
                                       text=MESI_ABBR[i],
                                       font=("Arial", 8), fill=self.TEXT_COLOR)
            def _show_tip(event, txt):
                    if _tip_win[0]:
                            try: _tip_win[0].destroy()
                            except: pass
                            _tip_win[0] = None
                    if _tip_win[1]:
                            canvas.after_cancel(_tip_win[1])
                            _tip_win[1] = None
                    x, y = event.x_root, event.y_root
                    def _mostra():
                            tw = tk.Toplevel(canvas)
                            tw.wm_overrideredirect(True)
                            tw.wm_geometry(f"+{x+12}+{y+10}")
                            ttk.Label(tw, text=txt, style="Tooltip.TLabel").pack()
                            _tip_win[0] = tw
                    _tip_win[1] = canvas.after(600, _mostra)
            def _hide_tip(event):
                    if _tip_win[1]:
                            canvas.after_cancel(_tip_win[1])
                            _tip_win[1] = None
                    if _tip_win[0]:
                            try: _tip_win[0].destroy()
                            except: pass
                            _tip_win[0] = None
            def _apri_dettaglio(mi, a, tp):
                    etichetta = "Entrate" if tp == "Entrata" else ("Uscite" if tp == "Uscita" else "Saldo")
                    data_filter = {"anno": str(a), "mese": mi + 1, "tipo": tp}
                    title = f"Dettaglio {etichetta} - {MESI_ABBR[mi]} {a}"
                    self.mostra_transazioni_popup(data_filter, title)
            for item_id, txt in tooltip_items.items():
                    canvas.tag_bind(item_id, "<Enter>",           lambda e, t=txt: _show_tip(e, t))
                    canvas.tag_bind(item_id, "<Leave>",           _hide_tip)
                    canvas.tag_bind(item_id, "<Double-Button-1>", lambda e,
                                    mi=tooltip_mese[item_id],
                                    a=anno,
                                    tp=tooltip_tipo[item_id]: _apri_dettaglio(mi, a, tp))
            tot_e = sum(entrate_m)
            tot_u = sum(uscite_m)
            tot_s = tot_e - tot_u
            col_s = self.COLOR_GREEN if tot_s >= 0 else self.COLOR_RED
            lbl_tot_e.config(text=f"Entrate Totali:  {tot_e:,.2f} €")
            lbl_tot_u.config(text=f"Uscite Totali:   {tot_u:,.2f} €")
            lbl_tot_s.config(text=f"Saldo Anno:      {tot_s:+,.2f} €", fg=col_s)
    def _aggiorna_anno(event=None):
            try:
                    anno = int(combo_anno.get())
            except ValueError:
                    return
            _disegna(anno)
    win = tk.Toplevel(self)
    self.win_risparmio = win
    win.withdraw()
    win.title("Andamento Risparmio per Anno")
    win.configure(bg=self.COLOR_TOPLEVEL)
    W_WIN, H_WIN = 1350, 630
    self.update_idletasks()
    px = self.winfo_rootx() + (self.winfo_width()  - W_WIN) // 2
    py = self.winfo_rooty() + (self.winfo_height() - H_WIN) // 2
    win.geometry(f"{W_WIN}x{H_WIN}+{max(0,px)}+{max(0,py)}")
    win.minsize(W_WIN, H_WIN)
    win.transient(self)
    win.bind("<Escape>", lambda e: win.destroy())
    top_bar = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    top_bar.pack(fill="x", padx=14, pady=(10, 4))
    tk.Label(top_bar, text="Anno:", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 10, "bold")).pack(side="left")
    anni_db = sorted({d.year for d in self.spese}, reverse=True)
    if not anni_db:
            anni_db = [datetime.date.today().year]
    combo_anno = ttk.Combobox(top_bar, values=anni_db, width=8,
                              state="readonly", font=("Arial", 10), style="Border.TCombobox")
    combo_anno.set(str(anni_db[0]))
    combo_anno.pack(side="left", padx=8)
    combo_anno.bind("<<ComboboxSelected>>", _aggiorna_anno)
    leg = tk.Frame(top_bar, bg=self.COLOR_TOPLEVEL)
    leg.pack(side="right", padx=10)
    includi_futuri_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(top_bar, text="Includi movimenti futuri",
                    variable=includi_futuri_var,
                    command=lambda: _disegna(int(combo_anno.get()))).pack(side="left", padx=16)
    img_mouse = self.icone_gui.get("mouse")
    tk.Label(top_bar, text="Doppio clic su una barra → dettaglio transazioni del mese",
             image=img_mouse, compound="right",
             bg=self.COLOR_TOPLEVEL, fg="gray", font=("Arial", 8, "italic")).pack(side="left", padx=20)
    tk.Label(leg, text="■ Entrate", bg=self.COLOR_TOPLEVEL,
             fg=self.COLOR_GREEN_SMOOTH, font=("Arial", 9)).pack(side="left", padx=6)
    tk.Label(leg, text="■ Uscite", bg=self.COLOR_TOPLEVEL,
             fg=self.COLOR_RED_SMOOTH, font=("Arial", 9)).pack(side="left", padx=6)
    tk.Label(leg, text="● Saldo", bg=self.COLOR_TOPLEVEL,
             fg=self.COLOR_HIGHLIGHT, font=("Arial", 9)).pack(side="left", padx=6)
    canvas = tk.Canvas(win, bg=self.COLOR_BACKGROUND,
                       highlightthickness=0)
    canvas.pack(fill="both", expand=True, padx=14, pady=(4, 4))
    canvas.bind("<Configure>", lambda e: _disegna(int(combo_anno.get())))
    footer = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    footer.pack(fill="x", padx=14, pady=(4, 12))
    lbl_tot_e = tk.Label(footer, text="", bg=self.COLOR_TOPLEVEL,
                         fg=self.COLOR_GREEN, font=("Arial", 9, "bold"))
    lbl_tot_e.pack(side="left", padx=16)
    lbl_tot_u = tk.Label(footer, text="", bg=self.COLOR_TOPLEVEL,
                         fg=self.COLOR_RED, font=("Arial", 9, "bold"))
    lbl_tot_u.pack(side="left", padx=16)
    lbl_tot_s = tk.Label(footer, text="", bg=self.COLOR_TOPLEVEL,
                         font=("Arial", 9, "bold"))
    lbl_tot_s.pack(side="left", padx=16)
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
    win.after(80, lambda: _disegna(int(combo_anno.get())))
