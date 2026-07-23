#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import datetime
import tkinter as tk
from tkinter import ttk

from moduli.modello_spesa import campo

def apri_fondo_risparmio(self):
    import __main__ as _app
    FR_FILE = _app.FR_FILE
    DB_DIR  = _app.DB_DIR
    if hasattr(self, '_win_fondo_risparmio') and self._win_fondo_risparmio and self._win_fondo_risparmio.winfo_exists():
        self._win_fondo_risparmio.lift()
        self._win_fondo_risparmio.focus_force()
        return
    def _carica_fr():
        try:
            if os.path.exists(FR_FILE):
                with open(FR_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {"obiettivo_annuale": 0.0, "fondo_attuale": 0.0, "obiettivi": []}
    def _salva_fr(dati):
        try:
            os.makedirs(DB_DIR, exist_ok=True)
            with open(FR_FILE, "w", encoding="utf-8") as f:
                json.dump(dati, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.show_toast(f"Errore salvataggio: {e}")
    fr_dati = _carica_fr()
    win = tk.Toplevel(self)
    self._win_fondo_risparmio = win
    win.transient(self)
    win.withdraw()
    win.title("Proiezione - Fondo Risparmio")
    win.configure(bg=self.COLOR_BACKGROUND)
    w_win, h_win = 1100, 630
    self.update_idletasks()
    root_x = self.winfo_rootx()
    root_y = self.winfo_rooty()
    root_w = self.winfo_width()
    root_h = self.winfo_height()
    pos_x  = root_x + (root_w // 2) - (w_win // 2)
    pos_y  = root_y + (root_h // 2) - (h_win // 2)
    win.geometry(f"{w_win}x{h_win}+{max(0, pos_x)}+{max(0, pos_y)}")
    win.minsize(w_win, h_win)
    win.bind("<Escape>", lambda e: win.destroy())
    win.deiconify()
    MESI_BREVI  = ["Gen","Feb","Mar","Apr","Mag","Giu",
                   "Lug","Ago","Set","Ott","Nov","Dic"]
    MESI_ESTESI = ["Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno",
                   "Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"]
    def fmt(v):
        return f"€ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    def fmts(v):
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    def _calcola_dati_365():
        today  = datetime.date.today()
        inizio = today - datetime.timedelta(days=364)
        entrate_tot = 0.0
        uscite_tot  = 0.0
        mesi_dati   = {}
        for d, sp in self.spese.items():
            if inizio <= d <= today:
                for entry in sp:
                    imp = campo(entry, "importo", 0.0)
                    tipo = campo(entry, "tipo", "")
                    key = (d.year, d.month)
                    if key not in mesi_dati:
                        mesi_dati[key] = {"e": 0.0, "u": 0.0}
                    if tipo == "Entrata":
                        entrate_tot          += imp
                        mesi_dati[key]["e"]  += imp
                    else:
                        uscite_tot           += imp
                        mesi_dati[key]["u"]  += imp
        n_mesi  = len(mesi_dati) if mesi_dati else 1
        media_e = entrate_tot / n_mesi
        media_u = uscite_tot  / n_mesi
        media_r = (entrate_tot - uscite_tot) / n_mesi
        return {
            "entrate_tot": entrate_tot,
            "uscite_tot":  uscite_tot,
            "risparmio":   entrate_tot - uscite_tot,
            "media_e":     media_e,
            "media_u":     media_u,
            "media_r":     media_r,
            "n_mesi":      n_mesi,
            "mesi_dati":   mesi_dati,
        }
    def _calcola_proiezione_anno(stats):
        today      = datetime.date.today()
        anno       = today.year
        anno_prec  = anno - 1
        mesi_reali = {}
        for (y, m), v in stats["mesi_dati"].items():
            if y == anno:
                mesi_reali[m] = v
        mesi_anno_prec = {}
        for d, sp in self.spese.items():
            if d.year == anno_prec:
                key = d.month
                if key not in mesi_anno_prec:
                    mesi_anno_prec[key] = {"e": 0.0, "u": 0.0}
                for entry in sp:
                    imp = campo(entry, "importo", 0.0)
                    tipo = campo(entry, "tipo", "")
                    if tipo == "Entrata":
                        mesi_anno_prec[key]["e"] += imp
                    else:
                        mesi_anno_prec[key]["u"] += imp
        proiezione  = []
        entrate_tot = 0.0
        uscite_tot  = 0.0
        for m in range(1, 13):
            if m in mesi_reali:
                e, u, futuro = mesi_reali[m]["e"], mesi_reali[m]["u"], False
            else:
                if m in mesi_anno_prec:
                    e = mesi_anno_prec[m]["e"]
                    u = mesi_anno_prec[m]["u"]
                else:
                    e, u = stats["media_e"], stats["media_u"]
                futuro = True
            proiezione.append({"m": m, "e": e, "u": u, "r": e - u, "futuro": futuro})
            entrate_tot += e
            uscite_tot  += u
        return proiezione, entrate_tot, uscite_tot, entrate_tot - uscite_tot
    def _calcola_12_mesi():
        today  = datetime.date.today()
        result = []
        for i in range(11, -1, -1):
            total = today.year * 12 + today.month - 1 - i
            y = total // 12
            m = total % 12 + 1
            e, u = 0.0, 0.0
            for d, sp in self.spese.items():
                if d.year == y and d.month == m:
                    for entry in sp:
                        imp = campo(entry, "importo", 0.0)
                        tipo = campo(entry, "tipo", "")
                        if tipo == "Entrata":
                            e += imp
                        else:
                            u += imp
            result.append({"y": y, "m": m, "e": e, "u": u, "r": e - u})
        return result
    def kpi_box(parent, label, valore, colore=None):
        f = tk.Frame(parent, bg=self.COLOR_WIDGET_BG,
                     highlightbackground=self.COLOR_HIGHLIGHT,
                     highlightthickness=1)
        f.pack(side="left", expand=True, fill="both", padx=3)
        tk.Label(f, text=label, font=("Arial", 8),
                 bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR).pack(pady=(7, 0))
        tk.Label(f, text=valore, font=("Arial", 11, "bold"),
                 bg=self.COLOR_WIDGET_BG,
                 fg=colore or self.TEXT_COLOR).pack(pady=(2, 7))
    button_frame = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    button_frame.pack(side="bottom", pady=12)
    nb = ttk.Notebook(win)
    nb.pack(fill="both", expand=True, padx=8, pady=8)
    tab_proiezione = tk.Frame(nb, bg=self.COLOR_BACKGROUND)
    tab_mensile    = tk.Frame(nb, bg=self.COLOR_BACKGROUND)
    tab_obiettivi  = tk.Frame(nb, bg=self.COLOR_BACKGROUND)
    tab_trend      = tk.Frame(nb, bg=self.COLOR_BACKGROUND)
    tab_emergenza  = tk.Frame(nb, bg=self.COLOR_BACKGROUND)
    nb.add(tab_proiezione, text="Proiezione Annuale  ")
    nb.add(tab_mensile,    text="Fondo Mensile  ")
    nb.add(tab_obiettivi,  text="Obiettivi  ")
    nb.add(tab_trend,      text="Trend 12 Mesi  ")
    nb.add(tab_emergenza,  text="Fondo Emergenza  ")
    def _build_proiezione():
        for w in tab_proiezione.winfo_children():
            w.destroy()
        stats = _calcola_dati_365()
        proj, e_proj, u_proj, r_proj = _calcola_proiezione_anno(stats)
        today = datetime.date.today()
        frm_kpi = tk.Frame(tab_proiezione, bg=self.COLOR_BACKGROUND)
        frm_kpi.pack(fill="x", padx=12, pady=(10, 4))
        col_r = self.COLOR_GREEN if stats["risparmio"] >= 0 else self.COLOR_RED
        kpi_box(frm_kpi, "Entrate 365gg",        fmt(stats["entrate_tot"]))
        kpi_box(frm_kpi, "Uscite 365gg",         fmt(stats["uscite_tot"]))
        kpi_box(frm_kpi, "Risparmio 365gg",      fmt(stats["risparmio"]),  col_r)
        kpi_box(frm_kpi, "Media Entrate/mese",   fmt(stats["media_e"]))
        kpi_box(frm_kpi, "Media Uscite/mese",    fmt(stats["media_u"]))
        kpi_box(frm_kpi, "Media Risparmio/mese", fmt(stats["media_r"]),    col_r)
        frm_proj = tk.Frame(tab_proiezione, bg=self.COLOR_BACKGROUND)
        frm_proj.pack(fill="x", padx=12, pady=(0, 2))
        lbl_band = tk.Label(frm_proj,
            text=f"  Proiezione {today.year}  ",
            font=("Arial", 9, "bold"),
            bg=self.COLOR_HIGHLIGHT, fg="white")
        lbl_band.pack(side="left", ipady=2, ipadx=4, padx=(0, 8))
        frm_proj2 = tk.Frame(frm_proj, bg=self.COLOR_BACKGROUND)
        frm_proj2.pack(side="left", fill="x", expand=True)
        col_rp = self.COLOR_GREEN if r_proj >= 0 else self.COLOR_RED
        kpi_box(frm_proj2, f"Entrate stimate",  fmt(e_proj))
        kpi_box(frm_proj2, f"Uscite stimate",   fmt(u_proj))
        kpi_box(frm_proj2, f"Risparmio atteso", fmt(r_proj), col_rp)
        mesi_passati  = today.month
        mesi_mancanti = 12 - mesi_passati
        img_info = self.icone_gui.get("info")
        frm_info = tk.Frame(tab_proiezione, bg=self.COLOR_BACKGROUND)
        frm_info.pack(fill="x", padx=14)
        lbl_info = tk.Label(frm_info,
                 image=img_info, compound="left",
                 text=f"  {mesi_passati} mesi con dati reali · {mesi_mancanti} mesi proiettati dalla media",
                 font=("Arial", 9, "bold"), bg=self.COLOR_BACKGROUND, fg="gray")
        if img_info:
            lbl_info.image = img_info
        lbl_info.pack(side="left")
        tipo_meteo = "sole" if r_proj >= 0 else "temporale"
        img_meteo = self.icone_gui.get(f"meteo_{tipo_meteo}")
        lbl_meteo = tk.Label(frm_info, image=img_meteo or "",
                             bg=self.COLOR_BACKGROUND)
        if img_meteo:
            lbl_meteo.image = img_meteo
        lbl_meteo.pack(side="left", padx=8)
        win.after(200, lambda: self.avvia_animazione_meteo(lbl_meteo, tipo_meteo))
        cvs = tk.Canvas(tab_proiezione, bg=self.COLOR_WIDGET_BG,
                        highlightbackground=self.COLOR_HIGHLIGHT,
                        highlightthickness=1)
        tk.Label(frm_info,
                 image=self.icone_gui.get("mouse"), compound="left",
                 text="  Doppio clic sulle barre per vedere i movimenti",
                 bg=self.COLOR_BACKGROUND, fg="gray",
                 font=("Arial", 8, "italic")).pack(side="left", padx=12)
        cvs.pack(fill="both", expand=True, padx=12, pady=(4, 4))
        def _scelta_mese_futuro(anno, mese, nome_mese, tipo):
            dlg = tk.Toplevel(win)
            dlg.withdraw()
            dlg.title(f"{nome_mese} — Scegli anno")
            dlg.configure(bg=self.COLOR_BACKGROUND)
            dlg.transient(win)
            dlg.resizable(False, False)
            dlg.bind("<Escape>", lambda e: dlg.destroy())
            tipo_label = f" — Solo {tipo}" if tipo else ""
            tk.Label(dlg,
                     image=self.icone_gui.get("calendario"), compound="left",
                     text=f"  {nome_mese} è in proiezione.\n  Vuoi vedere i movimenti di:",
                     bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
                     font=("Arial", 10), justify="left").pack(padx=24, pady=(18, 12))
            def _apri(a):
                dlg.destroy()
                self.mostra_transazioni_popup(
                    {"anno": str(a), "mese": mese, "categoria": None, "tipo": tipo},
                    f"Transazioni {nome_mese} {a}{tipo_label}")
            frm_btn = tk.Frame(dlg, bg=self.COLOR_BACKGROUND)
            frm_btn.pack(pady=(0, 18))
            for testo, ico, cmd in [
                (f"  {anno} (anno corrente)",   "oggi",       lambda: _apri(anno)),
                (f"  {anno - 1} (anno scorso)", "calendario", lambda: _apri(anno - 1)),
            ]:
                b = tk.Label(frm_btn, image=self.icone_gui.get(ico), text=testo,
                             compound="left", bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                             cursor="hand2", font=("Arial", 10, "bold"))
                b.pack(side="left", padx=8)
                b.bind("<Button-1>", lambda e, c=cmd: c())
            btn_chiudi = tk.Label(dlg,
                     image=self.icone_gui.get("chiudi"), compound="left",
                     text="  Chiudi",
                     bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                     cursor="hand2", font=("Arial", 9, "bold"))
            btn_chiudi.pack(pady=(0, 12))
            btn_chiudi.bind("<Button-1>", lambda e: dlg.destroy())
            dlg.update_idletasks()
            w = dlg.winfo_reqwidth()
            h = dlg.winfo_reqheight()
            x = win.winfo_rootx() + (win.winfo_width() // 2) - (w // 2)
            y = win.winfo_rooty() + (win.winfo_height() // 2) - (h // 2)
            dlg.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")
            dlg.deiconify()
            dlg.lift()
            dlg.focus_force()
        def _draw_barre(event=None):
            cvs.delete("all")
            W = cvs.winfo_width()
            H = cvs.winfo_height()
            if W < 20 or H < 20:
                return
            PL, PR, PT, PB = 44, 12, 30, 30
            aw = W - PL - PR
            ah = H - PT - PB
            max_val = max((max(p["e"], p["u"], abs(p["r"])) for p in proj), default=1.0) or 1.0
            max_val *= 1.1
            cvs.create_line(PL, PT, PL, PT + ah, fill="#DDDDDD")
            cvs.create_line(PL, PT + ah, PL + aw, PT + ah, fill="#DDDDDD")
            for tick in range(0, 6):
                v = max_val * tick / 5
                y = PT + ah - ah * tick / 5
                label_y = (f"{v/1000:.1f}k" if v >= 1000 else f"{v:.0f}")
                cvs.create_text(PL - 5, y, anchor="e", text=label_y,
                                font=("Arial", 8), fill="gray")
            bar_gw = aw / 12
            bar_w  = min(bar_gw * 0.35, 24)
            anno_c = datetime.date.today().year
            for i, p in enumerate(proj):
                xc    = PL + i * bar_gw + bar_gw / 2 - bar_w / 2
                nm    = MESI_ESTESI[p["m"] - 1]
                he    = min(ah * (p["e"] / max_val), ah)
                col_e = "#A5D6A7" if p["futuro"] else "#4CAF50"
                tag_e = f"bar_e_{i}"
                cvs.create_rectangle(xc - bar_w - 1, PT + ah - he,
                                     xc - 1,          PT + ah,
                                     fill=col_e, outline="", tags=tag_e)
                val_e   = (f"{p['e']/1000:.1f}k" if p["e"] >= 1000 else f"{p['e']:.0f}")
                y_lbl_e = PT + ah - he - 8
                if y_lbl_e < PT + 2: y_lbl_e = PT + 8
                cvs.create_text(xc - bar_w/2 - 1, y_lbl_e, anchor="center",
                                text=val_e, font=("Arial", 7, "bold"),
                                fill=col_e, tags=tag_e)
                hu    = min(ah * (p["u"] / max_val), ah)
                col_u = "#FFCDD2" if p["futuro"] else "#EF5350"
                tag_u = f"bar_u_{i}"
                cvs.create_rectangle(xc + 1,         PT + ah - hu,
                                     xc + bar_w + 1, PT + ah,
                                     fill=col_u, outline="", tags=tag_u)
                val_u   = (f"{p['u']/1000:.1f}k" if p["u"] >= 1000 else f"{p['u']:.0f}")
                y_lbl_u = PT + ah - hu - 8
                if y_lbl_u < PT + 2: y_lbl_u = PT + 8
                cvs.create_text(xc + bar_w/2 + 1, y_lbl_u, anchor="center",
                                text=val_u, font=("Arial", 7, "bold"),
                                fill=col_u, tags=tag_u)
                hr        = min(ah * (abs(p["r"]) / max_val), ah)
                yr        = PT + ah - hr if p["r"] >= 0 else PT + ah
                col_bar_r = "#90CAF9" if p["futuro"] else "#1976D2"
                tag_r     = f"bar_r_{i}"
                cvs.create_rectangle(xc + bar_w + 3,     yr,
                                     xc + bar_w * 2 + 3, PT + ah,
                                     fill=col_bar_r, outline="", tags=tag_r)
                segno   = "+" if p["r"] >= 0 else ""
                val_r   = (f"{p['r']/1000:.1f}k" if abs(p["r"]) >= 1000 else f"{p['r']:.0f}")
                y_lbl_r = yr - 8
                if y_lbl_r < PT + 2: y_lbl_r = PT + 8
                cvs.create_text(xc + bar_w + bar_w/2 + 3, y_lbl_r, anchor="center",
                                text=f"{segno}{val_r}",
                                font=("Arial", 7, "bold"),
                                fill=col_bar_r, tags=tag_r)
                fill_lbl = "gray" if p["futuro"] else self.TEXT_COLOR
                cvs.create_text(xc + bar_w/2 + 1, PT + ah + 14, anchor="center",
                                text=MESI_BREVI[p["m"] - 1],
                                font=("Arial", 8, "bold"), fill=fill_lbl)
                if p["futuro"]:
                    cvs.tag_bind(tag_e, "<Double-1>", lambda e, a=anno_c, m=p["m"], n=nm:
                        _scelta_mese_futuro(a, m, n, "Entrata"))
                    cvs.tag_bind(tag_u, "<Double-1>", lambda e, a=anno_c, m=p["m"], n=nm:
                        _scelta_mese_futuro(a, m, n, "Uscita"))
                    cvs.tag_bind(tag_r, "<Double-1>", lambda e, a=anno_c, m=p["m"], n=nm:
                        _scelta_mese_futuro(a, m, n, None))
                else:
                    cvs.tag_bind(tag_e, "<Double-1>", lambda e, a=anno_c, m=p["m"], n=nm:
                        self.mostra_transazioni_popup(
                            {"anno": str(a), "mese": m, "categoria": None, "tipo": "Entrata"},
                            f"Entrate {n} {a}"))
                    cvs.tag_bind(tag_u, "<Double-1>", lambda e, a=anno_c, m=p["m"], n=nm:
                        self.mostra_transazioni_popup(
                            {"anno": str(a), "mese": m, "categoria": None, "tipo": "Uscita"},
                            f"Uscite {n} {a}"))
                    cvs.tag_bind(tag_r, "<Double-1>", lambda e, a=anno_c, m=p["m"], n=nm:
                        self.mostra_transazioni_popup(
                            {"anno": str(a), "mese": m, "categoria": None, "tipo": None},
                            f"Transazioni {n} {a}"))
            lx, ly = PL + 10, PT + 10
            for colore, testo in [("#4CAF50","Entrate"), ("#EF5350","Uscite"), ("#1976D2","Risparmio")]:
                cvs.create_rectangle(lx, ly - 5, lx + 10, ly + 5, fill=colore, outline="")
                cvs.create_text(lx + 13, ly, anchor="w", text=testo,
                                font=("Arial", 8), fill=self.TEXT_COLOR)
                lx += 70
            cvs.create_text(lx + 4, ly, anchor="w", text="(sbiadito = proiezione)",
                            font=("Arial", 8), fill="gray")
        cvs.bind("<Configure>", _draw_barre)
        win.after(120, _draw_barre)
    def _build_mensile():
        for w in tab_mensile.winfo_children():
            w.destroy()
        stats = _calcola_dati_365()
        frm_kpi = tk.Frame(tab_mensile, bg=self.COLOR_BACKGROUND)
        frm_kpi.pack(fill="x", padx=12, pady=(10, 6))
        col_r = self.COLOR_GREEN if stats["media_r"] >= 0 else self.COLOR_RED
        kpi_box(frm_kpi, "Media Entrate/mese",   fmt(stats["media_e"]))
        kpi_box(frm_kpi, "Media Uscite/mese",    fmt(stats["media_u"]))
        kpi_box(frm_kpi, "Risparmio Medio/mese", fmt(stats["media_r"]), col_r)
        kpi_box(frm_kpi, "Mesi analizzati",      str(stats["n_mesi"]))
        frm_obj = tk.LabelFrame(tab_mensile, text="Obiettivo Risparmio Annuale ",
                                bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                                font=("Arial", 9, "bold"))
        frm_obj.pack(fill="x", padx=12, pady=(0, 4))
        frm_row = tk.Frame(frm_obj, bg=self.COLOR_WIDGET_BG)
        frm_row.pack(fill="x", padx=8, pady=8)
        tk.Label(frm_row, text="Obiettivo annuale (€):",
                 bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                 font=("Arial", 9)).pack(side="left", padx=(0, 4))
        obj_var = tk.StringVar(value=str(int(fr_dati.get("obiettivo_annuale", 0))))
        ttk.Entry(frm_row, textvariable=obj_var, width=10).pack(side="left", padx=(0, 16))
        lbl_rata     = tk.Label(frm_row, text="", bg=self.COLOR_WIDGET_BG,
                                fg=self.TEXT_COLOR, font=("Arial", 9, "bold"))
        lbl_rata.pack(side="left", padx=8)
        lbl_confronto = tk.Label(frm_row, text="", bg=self.COLOR_WIDGET_BG,
                                 fg=self.TEXT_COLOR, font=("Arial", 9, "bold"))
        lbl_confronto.pack(side="left", padx=8)
        tk.Label(frm_row,
                 image=self.icone_gui.get("mouse"), compound="left",
                 text="  Doppio clic sulla tabella per vedere i movimenti",
                 bg=self.COLOR_WIDGET_BG, fg="gray",
                 font=("Arial", 8, "italic")).pack(side="right", padx=8)
        tipo_meteo_m = "sole" if stats["media_r"] >= 0 else "temporale"
        img_meteo_m = self.icone_gui.get(f"meteo_{tipo_meteo_m}")
        lbl_meteo_m = tk.Label(frm_row, image=img_meteo_m or "",
                               bg=self.COLOR_WIDGET_BG)
        if img_meteo_m:
            lbl_meteo_m.image = img_meteo_m
        lbl_meteo_m.pack(side="right", padx=8)
        win.after(200, lambda: self.avvia_animazione_meteo(lbl_meteo_m, tipo_meteo_m))
        cvs_bar = tk.Canvas(tab_mensile, height=28, bg=self.COLOR_WIDGET_BG,
                            highlightbackground=self.COLOR_HIGHLIGHT,
                            highlightthickness=1)
        cvs_bar.pack(fill="x", padx=12, pady=(0, 4))
        def _draw_bar_obj(event=None):
            cvs_bar.delete("all")
            W = cvs_bar.winfo_width()
            if W < 10:
                return
            try:
                obj = float(obj_var.get().replace(",", "."))
            except ValueError:
                obj = 0.0
            base = max(stats["risparmio"], obj, 1.0)
            pct  = max(0.0, min(stats["risparmio"] / base, 1.0))
            fw   = int(W * pct)
            col  = (self.COLOR_GREEN if pct >= 1.0
                    else self.COLOR_ORANGE if pct >= 0.5
                    else self.COLOR_RED)
            cvs_bar.create_rectangle(0, 0, W, 28, fill="#EEEEEE", outline="")
            if fw > 0:
                cvs_bar.create_rectangle(0, 0, fw, 28, fill=col, outline="")
            txt = (f"Risparmio 365gg: {fmt(stats['risparmio'])}   /   "
                   f"Obiettivo: {fmt(obj) if obj > 0 else '—'}   "
                   f"({pct*100:.1f}%)")
            cvs_bar.create_text(W // 2, 14, text=txt, font=("Arial", 8, "bold"),
                                fill="#111111")
        def _calcola_rata(*args):
            try:
                obj = float(obj_var.get().replace(",", "."))
            except ValueError:
                obj = 0.0
            rata = obj / 12 if obj > 0 else 0.0
            lbl_rata.config(text=f"→  Rata mensile necessaria: {fmt(rata)}")
            diff = stats["media_r"] - rata
            if diff >= 0:
                lbl_confronto.config(
                    text=f"Sei in linea  (+{fmt(diff)}/mese)",
                    fg=self.COLOR_GREEN)
            else:
                lbl_confronto.config(
                    text=f"Mancano {fmt(abs(diff))}/mese",
                    fg=self.COLOR_RED)
            fr_dati["obiettivo_annuale"] = obj
            _salva_fr(fr_dati)
            win.after(50, _draw_bar_obj)

        obj_var.trace_add("write", _calcola_rata)
        cvs_bar.bind("<Configure>", _draw_bar_obj)
        frm_tree = tk.LabelFrame(tab_mensile,
                                 text="Andamento Mensile — ultimi 12 mesi ",
                                 bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                                 font=("Arial", 9, "bold"))
        frm_tree.pack(fill="both", expand=True, padx=12, pady=(0, 4))
        cols = ("Mese", "Entrate", "Uscite", "Risparmio", "vs Media mensile")
        tree12 = ttk.Treeview(frm_tree, columns=cols, show="headings", height=7)
        for c in cols:
            tree12.heading(c, text=c)
        tree12.column("Mese",             width=140, anchor="w")
        tree12.column("Entrate",          width=120, anchor="e")
        tree12.column("Uscite",           width=120, anchor="e")
        tree12.column("Risparmio",        width=120, anchor="e")
        tree12.column("vs Media mensile", width=140, anchor="e")
        tree12.tag_configure("positivo", foreground=self.COLOR_GREEN)
        tree12.tag_configure("negativo", foreground=self.COLOR_RED)
        sb = ttk.Scrollbar(frm_tree, orient="vertical", command=tree12.yview)
        tree12.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        tree12.pack(fill="both", expand=True)
        def _on_tree12_double(event):
            sel = tree12.selection()
            if not sel:
                return
            row_vals = tree12.item(sel[0], "values")
            if not row_vals:
                return
            parti = row_vals[0].split(" — ")
            if len(parti) != 2:
                return
            try:
                anno_r = int(parti[0].strip())
            except ValueError:
                return
            nome_r = parti[1].strip()
            mese_r = MESI_ESTESI.index(nome_r) + 1 if nome_r in MESI_ESTESI else None
            if mese_r is None:
                return
            self.mostra_transazioni_popup(
                {"anno": str(anno_r), "mese": mese_r, "categoria": None, "tipo": None},
                f"Transazioni {nome_r} {anno_r}")
        tree12.bind("<Double-1>", _on_tree12_double)
        dati_12 = _calcola_12_mesi()
        for row in dati_12:
            vs    = row["r"] - stats["media_r"]
            vs_s  = f"▲ +{fmts(vs)}" if vs >= 0 else f"▼ {fmts(vs)}"
            tag   = "positivo" if row["r"] >= 0 else "negativo"
            tree12.insert("", "end", values=(
                f"{row['y']} — {MESI_ESTESI[row['m']-1]}",
                fmts(row["e"]), fmts(row["u"]), fmts(row["r"]), vs_s,
            ), tags=(tag,))
        _calcola_rata()
    def _build_obiettivi():
        for w in tab_obiettivi.winfo_children():
            w.destroy()
        stats = _calcola_dati_365()
        frm_form = tk.LabelFrame(tab_obiettivi, text=" ➕ Nuovo Obiettivo ",
                                 bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                                 font=("Arial", 9, "bold"))
        frm_form.pack(fill="x", padx=12, pady=(10, 6))
        frm_row = tk.Frame(frm_form, bg=self.COLOR_WIDGET_BG)
        frm_row.pack(fill="x", padx=8, pady=8)
        tk.Label(frm_row, text="Nome:",
                 bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                 font=("Arial", 9)).grid(row=0, column=0, sticky="w", padx=(0, 4))
        nome_var = tk.StringVar()
        vcmd_nome = frm_row.register(lambda v: len(v) <= 20)
        ttk.Entry(frm_row, textvariable=nome_var, width=20,
                  validate="key", validatecommand=(vcmd_nome, "%P")).grid(
            row=0, column=1, padx=(0, 14))
        tk.Label(frm_row, text="Importo (€):",
                 bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                 font=("Arial", 9)).grid(row=0, column=2, sticky="w", padx=(0, 4))
        imp_var = tk.StringVar()
        def _val_imp_ob(v):
            if v == "": return True
            return len(v) <= 8 and re.match(r"^\d*[.,]?\d{0,2}$", v) is not None
        vcmd_imp = frm_row.register(_val_imp_ob)
        ttk.Entry(frm_row, textvariable=imp_var, width=10,
                  validate="key", validatecommand=(vcmd_imp, "%P")).grid(
            row=0, column=3, padx=(0, 14))
        tk.Label(frm_row, text="Entro (MM/AAAA):",
                 bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                 font=("Arial", 9)).grid(row=0, column=4, sticky="w", padx=(0, 4))
        data_var = tk.StringVar()
        ttk.Entry(frm_row, textvariable=data_var, width=10).grid(
            row=0, column=5, padx=(0, 14))
        def _aggiungi():
            nome = nome_var.get().strip()
            if not nome:
                self.show_toast("Inserisci un nome per l'obiettivo")
                return
            try:
                importo = float(imp_var.get().replace(",", "."))
            except ValueError:
                self.show_toast("Importo non valido")
                return
            try:
                parts = data_var.get().strip().split("/")
                dt = datetime.date(int(parts[1]), int(parts[0]), 1)
            except Exception:
                self.show_toast("Data non valida — usa MM/AAAA")
                return
            today = datetime.date.today()
            mesi_disp = (dt.year - today.year) * 12 + (dt.month - today.month)
            if mesi_disp <= 0:
                self.show_toast("La data deve essere futura")
                return
            fr_dati.setdefault("obiettivi", []).append({
                "nome": nome, "importo": importo,
                "data": data_var.get().strip(), "mesi": mesi_disp,
            })
            _salva_fr(fr_dati)
            nome_var.set(""); imp_var.set(""); data_var.set("")
            _build_obiettivi()
        ttk.Button(frm_row, text="Aggiungi", style="Blu.TButton",
                   command=_aggiungi).grid(row=0, column=6, padx=8)
        frm_lista = tk.LabelFrame(tab_obiettivi, text="I Tuoi Obiettivi ",
                                  bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                                  font=("Arial", 9, "bold"))
        frm_lista.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        cols_o = ("Nome", "Importo", "Entro", "Mesi", "Rata/mese",
                  "Fattibile", "Mesi realistici")
        tree_o = ttk.Treeview(frm_lista, columns=cols_o, show="headings", height=8)
        for c in cols_o:
            tree_o.heading(c, text=c)
        tree_o.column("Nome",            width=160, anchor="center")
        tree_o.column("Importo",         width=100, anchor="center")
        tree_o.column("Entro",           width=85,  anchor="center")
        tree_o.column("Mesi",            width=50,  anchor="center")
        tree_o.column("Rata/mese",       width=110, anchor="center")
        tree_o.column("Fattibile",       width=80,  anchor="center")
        tree_o.column("Mesi realistici", width=110, anchor="center")
        tree_o.tag_configure("si", foreground=self.COLOR_GREEN)
        tree_o.tag_configure("no", foreground=self.COLOR_RED)
        sb_o = ttk.Scrollbar(frm_lista, orient="vertical", command=tree_o.yview)
        tree_o.configure(yscrollcommand=sb_o.set)
        sb_o.pack(side="right", fill="y")
        tree_o.pack(fill="both", expand=True)
        media_r = stats["media_r"]
        for ob in fr_dati.get("obiettivi", []):
            rata  = ob["importo"] / ob["mesi"] if ob["mesi"] > 0 else ob["importo"]
            ok    = media_r >= rata
            mesi_r = int(ob["importo"] / media_r) if media_r > 0 else 9999
            tree_o.insert("", "end", values=(
                ob["nome"], fmts(ob["importo"]), ob["data"], ob["mesi"],
                fmts(rata),
                "Sì" if ok else "No",
                f"{mesi_r} mesi" if media_r > 0 else "N/D",
            ), tags=("si" if ok else "no",))
        def _elimina():
            sel = tree_o.selection()
            if not sel:
                self.show_toast("Seleziona un obiettivo da eliminare")
                return
            idx = tree_o.index(sel[0])
            if 0 <= idx < len(fr_dati.get("obiettivi", [])):
                del fr_dati["obiettivi"][idx]
                _salva_fr(fr_dati)
                _build_obiettivi()
        frm_btn_o = tk.Frame(frm_lista, bg=self.COLOR_WIDGET_BG)
        frm_btn_o.pack(fill="x", pady=(4, 2))
        img_elimina = self.icone_gui.get("cancella")
        lbl_elimina = tk.Label(frm_btn_o, text="  Elimina selezionato",
                   image=img_elimina, compound="left",
                   bg=self.COLOR_WIDGET_BG, fg=self.COLOR_RED,
                   font=("Arial", 10, "bold"), cursor="hand2")
        lbl_elimina.image = img_elimina
        lbl_elimina.pack(side="left", padx=8)
        lbl_elimina.bind("<Button-1>", lambda e: _elimina())
        tk.Label(frm_lista,
                 text=f"  ℹ  Risparmio medio mensile attuale: {fmt(media_r)}",
                 bg=self.COLOR_WIDGET_BG, fg="gray",
                 font=("Arial", 8)).pack(anchor="w", padx=8, pady=(0, 4))
    def _build_trend():
        for w in tab_trend.winfo_children():
            w.destroy()
        dati_12 = _calcola_12_mesi()
        stats   = _calcola_dati_365()
        best  = max(dati_12, key=lambda x: x["r"], default={"m":1,"y":2024,"r":0})
        worst = min(dati_12, key=lambda x: x["r"], default={"m":1,"y":2024,"r":0})
        frm_badge = tk.Frame(tab_trend, bg=self.COLOR_BACKGROUND)
        frm_badge.pack(fill="x", padx=12, pady=(10, 4))
        saldo_trend = sum(r["r"] for r in dati_12)
        tk.Label(frm_badge,
                 image=self.icone_gui.get("mouse"), compound="left",
                 text="  Doppio clic sulla tabella o sui punti del grafico per vedere i movimenti",
                 bg=self.COLOR_BACKGROUND, fg="gray",
                 font=("Arial", 8, "italic")).pack(side="right", padx=8)
        tipo_meteo_t = "sole" if saldo_trend >= 0 else "temporale"
        img_meteo_t = self.icone_gui.get(f"meteo_{tipo_meteo_t}")
        lbl_meteo_t = tk.Label(frm_badge, image=img_meteo_t or "",
                               bg=self.COLOR_BACKGROUND)
        if img_meteo_t:
            lbl_meteo_t.image = img_meteo_t
        lbl_meteo_t.pack(side="right", padx=8)
        win.after(200, lambda: self.avvia_animazione_meteo(lbl_meteo_t, tipo_meteo_t))
        tk.Label(frm_badge,
                 text=(f"Mese migliore: "
                       f"{MESI_ESTESI[best['m']-1]} {best['y']}  "
                       f"(+{fmt(best['r'])})"),
                 bg=self.COLOR_BACKGROUND, fg=self.COLOR_GREEN,
                 font=("Arial", 9, "bold")).pack(side="left", padx=12)
        tk.Label(frm_badge,
                 text=(f"Mese peggiore: "
                       f"{MESI_ESTESI[worst['m']-1]} {worst['y']}  "
                       f"({fmt(worst['r'])})"),
                 bg=self.COLOR_BACKGROUND, fg=self.COLOR_RED,
                 font=("Arial", 9, "bold")).pack(side="left", padx=12)
        frm_t = tk.Frame(tab_trend, bg=self.COLOR_BACKGROUND)
        frm_t.pack(fill="x", padx=12, pady=(0, 4))
        cols_t = ("Mese", "Entrate", "Uscite", "Saldo", "Delta vs precedente")
        tree_t = ttk.Treeview(frm_t, columns=cols_t, show="headings", height=12)
        for c in cols_t:
            tree_t.heading(c, text=c)
        tree_t.column("Mese",               width=150, anchor="w")
        tree_t.column("Entrate",            width=120, anchor="e")
        tree_t.column("Uscite",             width=120, anchor="e")
        tree_t.column("Saldo",              width=120, anchor="e")
        tree_t.column("Delta vs precedente",width=140, anchor="e")
        tree_t.tag_configure("positivo", foreground=self.COLOR_GREEN)
        tree_t.tag_configure("negativo", foreground=self.COLOR_RED)
        sb_t = ttk.Scrollbar(frm_t, orient="vertical", command=tree_t.yview)
        tree_t.configure(yscrollcommand=sb_t.set)
        sb_t.pack(side="right", fill="y")
        tree_t.pack(fill="both", expand=True)
        def _on_tree_t_double(event):
            sel = tree_t.selection()
            if not sel:
                return
            row_vals = tree_t.item(sel[0], "values")
            if not row_vals:
                return
            parti = row_vals[0].split(" — ")
            if len(parti) != 2:
                return
            try:
                anno_r = int(parti[0].strip())
            except ValueError:
                return
            nome_r = parti[1].strip()
            mese_r = MESI_ESTESI.index(nome_r) + 1 if nome_r in MESI_ESTESI else None
            if mese_r is None:
                return
            self.mostra_transazioni_popup(
                {"anno": str(anno_r), "mese": mese_r, "categoria": None, "tipo": None},
                f"Transazioni {nome_r} {anno_r}")
        tree_t.bind("<Double-1>", _on_tree_t_double)
        prev_r = None
        for row in dati_12:
            delta_s = ("—" if prev_r is None
                       else (f"▲ +{fmts(row['r'] - prev_r)}"
                             if row["r"] >= prev_r
                             else f"▼ {fmts(row['r'] - prev_r)}"))
            tree_t.insert("", "end", values=(
                f"{row['y']} — {MESI_ESTESI[row['m']-1]}",
                fmts(row["e"]), fmts(row["u"]), fmts(row["r"]), delta_s,
            ), tags=("positivo" if row["r"] >= 0 else "negativo",))
            prev_r = row["r"]
        cvs_sp = tk.Canvas(tab_trend, bg=self.COLOR_WIDGET_BG,
                           highlightbackground=self.COLOR_HIGHLIGHT,
                           highlightthickness=1, height=180)
        cvs_sp.pack(fill="x", padx=12, pady=(2, 4))
        def _draw_spark(event=None):
            cvs_sp.delete("all")
            W = cvs_sp.winfo_width()
            H = cvs_sp.winfo_height()
            if W < 20 or not dati_12:
                return
            valori = [r["r"] for r in dati_12]
            max_v  = max(abs(v) for v in valori) or 1.0
            pad    = 24
            step   = (W - 2 * pad) / max(len(valori) - 1, 1)
            y_zero = H // 2
            cvs_sp.create_line(pad, y_zero, W - pad, y_zero,
                               fill="#CCCCCC", dash=(4, 2))
            pts = []
            for i, v in enumerate(valori):
                x = pad + i * step
                y = y_zero - (v / max_v) * (y_zero - 10)
                pts.append((x, y))
            for i in range(len(pts) - 1):
                col = (self.COLOR_GREEN if valori[i] >= 0 else self.COLOR_RED)
                cvs_sp.create_line(pts[i][0], pts[i][1],
                                   pts[i+1][0], pts[i+1][1],
                                   fill=col, width=2)
            for i, (x, y) in enumerate(pts):
                col    = (self.COLOR_GREEN if valori[i] >= 0 else self.COLOR_RED)
                tag_pt = f"pt_{i}"
                cvs_sp.create_oval(x - 3, y - 3, x + 3, y + 3,
                                   fill=col, outline="", tags=tag_pt)
                cvs_sp.create_text(x, H - 8, anchor="center",
                                   text=MESI_BREVI[dati_12[i]["m"] - 1],
                                   font=("Arial", 9, "bold"), fill=self.TEXT_COLOR, tags=tag_pt)
                cvs_sp.tag_bind(tag_pt, "<Double-1>", lambda e, r=dati_12[i]:
                    self.mostra_transazioni_popup(
                        {"anno": str(r["y"]), "mese": r["m"], "categoria": None, "tipo": None},
                        f"Transazioni {MESI_ESTESI[r['m']-1]} {r['y']}"))
        cvs_sp.bind("<Configure>", _draw_spark)
        win.after(120, _draw_spark)
    def _build_emergenza():
        for w in tab_emergenza.winfo_children():
            w.destroy()
        stats = _calcola_dati_365()
        spesa_mm = stats["media_u"]
        frm_kpi = tk.Frame(tab_emergenza, bg=self.COLOR_BACKGROUND)
        frm_kpi.pack(fill="x", padx=12, pady=(10, 6))
        kpi_box(frm_kpi, "Spesa media/mese",  fmt(spesa_mm))
        kpi_box(frm_kpi, "Fondo consigliato 3 mesi",  fmt(spesa_mm * 3))
        kpi_box(frm_kpi, "Fondo consigliato 6 mesi",  fmt(spesa_mm * 6))
        kpi_box(frm_kpi, "Fondo consigliato 12 mesi", fmt(spesa_mm * 12))
        frm_att = tk.LabelFrame(tab_emergenza, text="Il Tuo Fondo Attuale ",
                                bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                                font=("Arial", 9, "bold"))
        frm_att.pack(fill="x", padx=12, pady=(0, 6))
        frm_att_row = tk.Frame(frm_att, bg=self.COLOR_WIDGET_BG)
        frm_att_row.pack(fill="x", padx=8, pady=8)
        tk.Label(frm_att_row, text="Fondo emergenza attuale (€):",
                 bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                 font=("Arial", 9)).pack(side="left", padx=(0, 4))
        fondo_var = tk.StringVar(value=str(int(fr_dati.get("fondo_attuale", 0))))
        ttk.Entry(frm_att_row, textvariable=fondo_var, width=12).pack(
            side="left", padx=(0, 16))
        lbl_stato = tk.Label(frm_att_row, text="",
                             bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                             font=("Arial", 9, "bold"))
        lbl_stato.pack(side="left", padx=8)
        lbl_meteo_em = tk.Label(frm_att_row, image="",
                                bg=self.COLOR_WIDGET_BG)
        lbl_meteo_em.pack(side="right", padx=8)
        frm_barre = tk.Frame(tab_emergenza, bg=self.COLOR_BACKGROUND)
        frm_barre.pack(fill="x", padx=12, pady=4)
        cvs_3  = tk.Canvas(frm_barre, height=26, bg=self.COLOR_WIDGET_BG,
                           highlightbackground=self.COLOR_HIGHLIGHT, highlightthickness=1)
        cvs_6  = tk.Canvas(frm_barre, height=26, bg=self.COLOR_WIDGET_BG,
                           highlightbackground=self.COLOR_HIGHLIGHT, highlightthickness=1)
        cvs_12 = tk.Canvas(frm_barre, height=26, bg=self.COLOR_WIDGET_BG,
                           highlightbackground=self.COLOR_HIGHLIGHT, highlightthickness=1)
        cvs_3.pack(fill="x", pady=2)
        cvs_6.pack(fill="x", pady=2)
        cvs_12.pack(fill="x", pady=2)
        def _draw_barra(cvs, target, etichetta, event=None):
            cvs.delete("all")
            W = cvs.winfo_width()
            if W < 10:
                return
            try:
                fondo = float(fondo_var.get().replace(",", "."))
            except ValueError:
                fondo = 0.0
            pct = max(0.0, min(fondo / target, 1.0)) if target > 0 else 0.0
            fw  = int(W * pct)
            col = (self.COLOR_GREEN if pct >= 1.0
                   else self.COLOR_ORANGE if pct >= 0.5
                   else self.COLOR_RED)
            cvs.create_rectangle(0, 0, W, 26, fill="#EEEEEE", outline="")
            if fw > 0:
                cvs.create_rectangle(0, 0, fw, 26, fill=col, outline="")
            txt = (f"{etichetta}  "
                   f"{fmt(fondo)} / {fmt(target)}  "
                   f"({pct*100:.1f}%)")
            cvs.create_text(W // 2, 13, text=txt,
                            font=("Arial", 8, "bold"),
                            fill="#111111")
        def _aggiorna(*args):
            try:
                fondo = float(fondo_var.get().replace(",", "."))
            except ValueError:
                fondo = 0.0
            fr_dati["fondo_attuale"] = fondo
            _salva_fr(fr_dati)
            win.after(50, lambda: _draw_barra(cvs_3,  spesa_mm * 3,  "Obiettivo 3 mesi  "))
            win.after(50, lambda: _draw_barra(cvs_6,  spesa_mm * 6,  "Obiettivo 6 mesi  "))
            win.after(50, lambda: _draw_barra(cvs_12, spesa_mm * 12, "Obiettivo 12 mesi "))
            media_r = stats["media_r"]
            if fondo >= spesa_mm * 12:
                testo, col = "Fondo 12 mesi raggiunto!", self.COLOR_GREEN
                tipo_m = "sole"
            elif fondo >= spesa_mm * 6:
                testo, col = "Fondo 6 mesi raggiunto — punta a 12 mesi", self.COLOR_ORANGE
                tipo_m = "sole"
            elif fondo >= spesa_mm * 3:
                testo, col = "Fondo 3 mesi raggiunto — punta a 6 mesi", self.COLOR_ORANGE
                tipo_m = "sole"
            else:
                mancanti = (((spesa_mm * 3) - fondo) / media_r
                            if media_r > 0 else 0)
                testo = (f"Con il risparmio attuale raggiungi "
                         f"3 mesi in {mancanti:.0f} mesi")
                col = self.COLOR_RED
                tipo_m = "temporale"
            lbl_stato.config(text=testo, fg=col)
            self.avvia_animazione_meteo(lbl_meteo_em, tipo_m)
        fondo_var.trace_add("write", _aggiorna)
        cvs_3.bind("<Configure>",
            lambda e: _draw_barra(cvs_3,  spesa_mm * 3,  "Obiettivo 3 mesi  "))
        cvs_6.bind("<Configure>",
            lambda e: _draw_barra(cvs_6,  spesa_mm * 6,  "Obiettivo 6 mesi  "))
        cvs_12.bind("<Configure>",
            lambda e: _draw_barra(cvs_12, spesa_mm * 12, "Obiettivo 12 mesi "))
        img_info = self.icone_gui.get("info")
        lbl_info_em = tk.Label(tab_emergenza,
                 image=img_info, compound="left",
                 text="  Un fondo emergenza ideale copre almeno 3-6 mesi di spese. "
                      "12 mesi garantisce la massima sicurezza.",
                 bg=self.COLOR_BACKGROUND, fg="gray",
                 font=("Arial", 9, "bold"))
        if img_info:
            lbl_info_em.image = img_info
        lbl_info_em.pack(anchor="w", padx=12, pady=(6, 2))
        win.after(200, _aggiorna)
    _build_proiezione()
    _build_mensile()
    _build_obiettivi()
    _build_trend()
    _build_emergenza()
    img_chiudi = self.icone_gui.get("chiudi")
    btn_chiudi = tk.Label(button_frame, compound="left",
                          image=img_chiudi,
                          text=" Chiudi" if img_chiudi else "❌ Chiudi",
                          background=self.COLOR_WIDGET_BG,
                          foreground=self.TEXT_COLOR,
                          cursor="hand2", padx=15, pady=8,
                          font=("Arial", 9, "bold"))
    btn_chiudi.pack()
    if img_chiudi:
        btn_chiudi.image = img_chiudi
    btn_chiudi.bind("<Button-1>", lambda e: win.destroy())
