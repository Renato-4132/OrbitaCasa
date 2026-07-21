#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import datetime
import tkinter as tk
from tkinter import ttk

def mostra_grafici_fairshare(self, anno_sel="Tutti", mese_sel="Tutti"):
    if hasattr(self, '_grafici_fairshare_win') and self._grafici_fairshare_win.winfo_exists():
        self._grafici_fairshare_win.lift()
        self._grafici_fairshare_win.focus_force()
        return
    debiti = self.carica_fairshare_state()
    parent = self._dare_avere_popup if hasattr(self, '_dare_avere_popup') and self._dare_avere_popup and self._dare_avere_popup.winfo_exists() else self
    popup = tk.Toplevel(parent, bg=self.COLOR_TOPLEVEL)
    self._grafici_fairshare_win = popup
    popup.title("FairShare — Grafici Dare & Avere")
    popup.withdraw()
    self.update_idletasks()
    w, h = 980, 620
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    popup.geometry(f"{w}x{h}+{x}+{y}")
    popup.minsize(w, h)
    popup.transient(parent)
    popup.deiconify()
    popup.lift()
    popup.focus_force()
    popup.bind("<Escape>", lambda e: popup.destroy())
    ROSSO   = "#E06C75"
    VERDE   = "#98C379"
    GIALLO  = "#E5C07B"
    txt = self.TEXT_COLOR
    bg  = self.COLOR_TOPLEVEL
    mesi_nomi = ["Tutti", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                 "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    anni_db = sorted({d.year for d in self.spese if isinstance(d, datetime.date)}, reverse=True)
    nomi_p_raw = {p["nome"]: p.get("tipo","persona") for p in self.nomi_partecipanti
                  if p.get("tipo") in ("persona","contenitore")}
    _gestore = os.path.basename(os.getcwd())
    if self._gestore_partecipa() and _gestore not in nomi_p_raw:
        nomi_p_raw[_gestore] = "persona"
    def _ico_g(nome):
        return "❍" if nomi_p_raw.get(nome) == "contenitore" else "✽"
    nomi_p = sorted([f"{_ico_g(n)} {n}" for n in nomi_p_raw], key=lambda x: x[2:].lower())
    toolbar = tk.Frame(popup, bg=bg)
    toolbar.pack(fill=tk.X, padx=10, pady=(8, 0))
    def _lbl(t):
        tk.Label(toolbar, text=t, bg=bg, fg=txt, font=("Arial", 9)).pack(side=tk.LEFT, padx=(8, 2))
    anno_var  = tk.StringVar(value=anno_sel)
    mese_var  = tk.StringVar(value=mese_sel)
    parte_var = tk.StringVar(value="Tutti")
    cat_var_g = tk.StringVar(value="Tutte")
    cat_list_g = ["Tutte"] + sorted(self.categorie, key=str.lower)
    _lbl("Anno:")
    ttk.Combobox(toolbar, textvariable=anno_var,
                 values=["Tutti"] + [str(a) for a in anni_db],
                 state="readonly", style="Border.TCombobox", width=6).pack(side=tk.LEFT)
    _lbl("Mese:")
    ttk.Combobox(toolbar, textvariable=mese_var, values=mesi_nomi,
                 state="readonly", style="Border.TCombobox", width=11).pack(side=tk.LEFT)
    _lbl("Persona:")
    ttk.Combobox(toolbar, textvariable=parte_var,
                 values=["Tutti"] + nomi_p,
                 state="readonly", style="Border.TCombobox", width=16).pack(side=tk.LEFT)
    _lbl("Categoria:")
    ttk.Combobox(toolbar, textvariable=cat_var_g, values=cat_list_g,
                 state="readonly", style="Border.TCombobox", width=16).pack(side=tk.LEFT)
    nb = ttk.Notebook(popup)
    nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
    tab1 = tk.Frame(nb, bg=bg); nb.add(tab1, text="👤 Dovuto / Versato per Persona")
    tab2 = tk.Frame(nb, bg=bg); nb.add(tab2, text="📂 Aperto / Chiuso per Categoria")
    tab3 = tk.Frame(nb, bg=bg); nb.add(tab3, text="📅 Andamento Mensile")
    def _crea_canvas_scroll(tab):
        hsb = ttk.Scrollbar(tab, orient="horizontal")
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        cv = tk.Canvas(tab, bg=bg, highlightthickness=0, xscrollcommand=hsb.set)
        cv.pack(fill=tk.BOTH, expand=True)
        hsb.config(command=cv.xview)
        return cv
    cv1 = _crea_canvas_scroll(tab1)
    cv2 = _crea_canvas_scroll(tab2)
    cv3 = _crea_canvas_scroll(tab3)
    def _dati_filtrati():
        a_sel = anno_var.get()
        m_num = mesi_nomi.index(mese_var.get())
        p_sel = parte_var.get()
        c_sel = cat_var_g.get()
        if p_sel not in ("", "Tutti") and " " in p_sel:
            p_sel = p_sel.split(" ", 1)[1].strip()
        filtrati = []
        for deb in debiti:
            ds = deb.get("data", "")
            try:
                d_obj = datetime.datetime.strptime(ds, "%d/%m/%Y").date()
            except Exception:
                continue
            if a_sel != "Tutti" and str(d_obj.year) != a_sel: continue
            if m_num > 0 and d_obj.month != m_num: continue
            if c_sel != "Tutte" and deb.get("categoria") != c_sel: continue
            filtrati.append((d_obj, deb))
        return filtrati, p_sel
    _tooltip_data1 = {}
    _tooltip_data2 = {}
    _tooltip_data3 = {}
    _tip_win = [None]
    def _show_tip(event, canvas, data_dict):
        _hide_tip()
        items = canvas.find_overlapping(event.x-2, event.y-2, event.x+2, event.y+2)
        for it in items:
            for t in canvas.gettags(it):
                if t in data_dict:
                    win = tk.Toplevel(canvas)
                    win.overrideredirect(True)
                    win.attributes("-topmost", True)
                    tk.Label(win, text=data_dict[t], bg="#2a2a2a", fg="#eeeeee",
                             font=("Arial", 9), padx=6, pady=3,
                             relief="solid", borderwidth=1).pack()
                    win.geometry(f"+{event.x_root+14}+{event.y_root+14}")
                    _tip_win[0] = win
                    return
    def _hide_tip(*_):
        if _tip_win[0]:
            try: _tip_win[0].destroy()
            except: pass
            _tip_win[0] = None
    def disegna_tab1(event=None):
        cv1.delete("all"); _tooltip_data1.clear()
        W = cv1.winfo_width(); H = cv1.winfo_height()
        if W < 80 or H < 80: return
        filtrati, p_sel = _dati_filtrati()
        dovuto = {}; versato = {}; cat_per_persona = {}
        for d_obj, deb in filtrati:
            quota = deb.get("quota", 0.0)
            cat   = deb.get("categoria", "")
            pag   = deb.get("pagamenti", {})
            for nome in deb.get("partecipanti", []):
                if p_sel != "Tutti" and nome != p_sel: continue
                dovuto.setdefault(nome, 0.0);  dovuto[nome] += quota
                versato.setdefault(nome, 0.0)
                if pag.get(nome, {}).get("pagato", False):
                    versato[nome] += quota
                cat_per_persona.setdefault(nome, {})
                cat_per_persona[nome].setdefault(cat, 0.0)
                cat_per_persona[nome][cat] += quota
        nomi_g = sorted(dovuto.keys())
        if not nomi_g:
            cv1.create_text(W//2, H//2, text="Nessun dato", fill="#777", font=("Arial", 11))
            cv1.configure(scrollregion=cv1.bbox("all")); return
        slot_w = max(80, W // len(nomi_g))
        pad_l, pad_r, pad_t, pad_b = 80, 30, 50, 90
        canvas_w = max(W, pad_l + slot_w * len(nomi_g) + pad_r)
        area_h = H - pad_t - pad_b
        base_y = pad_t + area_h
        max_v  = max(max(dovuto.values()), 1)
        scala  = area_h / max_v
        cv1.create_text(canvas_w//2, 22,
            text=f"Dovuto vs Versato  —  {mese_var.get()} {anno_var.get()}",
            fill=txt, font=("Arial", 11, "bold"))
        for i in range(6):
            val = max_v * i / 5; gy = base_y - val * scala
            cv1.create_line(pad_l, gy, pad_l + canvas_w - pad_l - pad_r, gy, fill="#333")
            cv1.create_text(pad_l - 6, gy, text=f"{val:,.0f}€", fill="#888", font=("Arial", 7), anchor="e")
        cv1.create_line(pad_l, pad_t, pad_l, base_y, fill="#555")
        cv1.create_line(pad_l, base_y, canvas_w - pad_r, base_y, fill="#555")
        bar_w = max(14, min(50, slot_w // 3))
        for i, nome in enumerate(nomi_g):
            cx  = pad_l + i * slot_w + slot_w // 2
            dov = dovuto[nome]; ver = versato[nome]; res = dov - ver
            dy1 = base_y - dov * scala
            tag_d = f"d_{i}"; tag_v = f"v_{i}"; tag_r = f"r_{i}"
            cats_txt = "\n".join(f"  {c}: {v:,.2f} €"
                for c, v in sorted(cat_per_persona.get(nome, {}).items(),
                                   key=lambda x: x[1], reverse=True))
            cv1.create_rectangle(cx-bar_w-4, dy1, cx-4, base_y, fill=GIALLO, outline="", tags=(tag_d,))
            _tooltip_data1[tag_d] = f"{nome}\nDovuto: {dov:,.2f} €\nResiduo: {res:,.2f} €\n{cats_txt}"
            if dov > 0:
                cv1.create_text(cx-bar_w//2-4, dy1-9, text=f"{dov:,.0f}€", fill=GIALLO, font=("Arial", 8, "bold"))
            vy1 = base_y - ver * scala
            cv1.create_rectangle(cx+4, vy1, cx+bar_w+4, base_y, fill=VERDE, outline="", tags=(tag_v,))
            _tooltip_data1[tag_v] = f"{nome}\nVersato: {ver:,.2f} €\n{cats_txt}"
            if ver > 0:
                cv1.create_text(cx+bar_w//2+4, vy1-9, text=f"{ver:,.0f}€", fill=VERDE, font=("Arial", 8, "bold"))
            if res > 0.01:
                ry1 = base_y - ver * scala
                cv1.create_rectangle(cx-bar_w-4, ry1, cx-4, dy1, fill=ROSSO, outline="", stipple="gray50", tags=(tag_r,))
                _tooltip_data1[tag_r] = f"{nome}\nResiduo da saldare: {res:,.2f} €\n{cats_txt}"
            cv1.create_text(cx, base_y+16, text=nome, fill=txt, font=("Arial", 9, "bold"))
        leg1 = [("Dovuto totale", GIALLO), ("Versato", VERDE), ("Residuo da saldare", ROSSO)]
        lx = pad_l
        for lab, col in leg1:
            cv1.create_rectangle(lx, H-28, lx+14, H-14, fill=col, outline="")
            cv1.create_text(lx+18, H-21, text=lab, fill=txt, font=("Arial", 8), anchor="w")
            lx += len(lab)*7 + 30
        cv1.create_text(canvas_w//2, H-6,
            text="Barra sx = dovuto  |  Barra dx = versato  |  Rosso tratteggiato = ancora da pagare",
            fill="#666", font=("Arial", 7))
        cv1.configure(scrollregion=(0, 0, canvas_w, H))
    def disegna_tab2(event=None):
        cv2.delete("all"); _tooltip_data2.clear()
        W = cv2.winfo_width(); H = cv2.winfo_height()
        if W < 80 or H < 80: return
        filtrati, p_sel = _dati_filtrati()
        cat_aperto = {}; cat_chiuso = {}; cat_tot_imp = {}
        cat_debitori = {}
        cat_creditori = {}
        for d_obj, deb in filtrati:
            cat   = deb.get("categoria", "—")
            imp   = deb.get("importo_totale", 0.0)
            quota = deb.get("quota", 0.0)
            stato = deb.get("stato", "aperto")
            pag   = deb.get("pagamenti", {})
            if p_sel != "Tutti" and p_sel not in deb.get("partecipanti", []): continue
            cat_tot_imp.setdefault(cat, 0.0); cat_tot_imp[cat] += imp
            if stato == "chiuso":
                cat_chiuso.setdefault(cat, 0.0); cat_chiuso[cat] += imp
                cat_creditori.setdefault(cat, {})
                for nome in deb.get("partecipanti", []):
                    cat_creditori[cat].setdefault(nome, 0.0)
                    cat_creditori[cat][nome] += quota
            else:
                cat_aperto.setdefault(cat, 0.0); cat_aperto[cat] += imp
                cat_debitori.setdefault(cat, {})
                for nome in deb.get("partecipanti", []):
                    if not pag.get(nome, {}).get("pagato", False):
                        cat_debitori[cat].setdefault(nome, 0.0)
                        cat_debitori[cat][nome] += quota
        cats = sorted(cat_tot_imp.keys())
        if not cats:
            cv2.create_text(W//2, H//2, text="Nessun dato", fill="#777", font=("Arial", 11))
            cv2.configure(scrollregion=cv2.bbox("all")); return
        pad_l, pad_r, pad_t, pad_b = 80, 30, 50, 90
        slot_w = max(80, W // len(cats))
        canvas_w = max(W, pad_l + slot_w * len(cats) + pad_r)
        area_h = H - pad_t - pad_b
        base_y = pad_t + area_h
        max_v  = max(cat_tot_imp.values()) if cat_tot_imp else 1
        scala  = area_h / max_v
        cv2.create_text(canvas_w//2, 22,
            text=f"Aperto / Chiuso per Categoria  —  {mese_var.get()} {anno_var.get()}",
            fill=txt, font=("Arial", 11, "bold"))
        for i in range(6):
            val = max_v * i / 5; gy = base_y - val * scala
            cv2.create_line(pad_l, gy, canvas_w - pad_r, gy, fill="#333")
            cv2.create_text(pad_l - 6, gy, text=f"{val:,.0f}€", fill="#888", font=("Arial", 7), anchor="e")
        cv2.create_line(pad_l, pad_t, pad_l, base_y, fill="#555")
        cv2.create_line(pad_l, base_y, canvas_w - pad_r, base_y, fill="#555")
        bar_w = max(12, min(45, slot_w // 3))
        for i, cat in enumerate(cats):
            cx  = pad_l + i * slot_w + slot_w // 2
            ap  = cat_aperto.get(cat, 0.0); cl = cat_chiuso.get(cat, 0.0)
            tag_a = f"a_{i}"; tag_c = f"c_{i}"
            deb_txt = "\n".join(f"  {n}: {v:,.2f} €"
                for n, v in sorted(cat_debitori.get(cat, {}).items(),
                                   key=lambda x: x[1], reverse=True))
            tip_a = f"{cat}\nAperto (da saldare): {ap:,.2f} €"
            if deb_txt:
                tip_a += f"\nIn attesa da:\n{deb_txt}"
            cred_txt = "\n".join(f"  {n}: {v:,.2f} €"
                for n, v in sorted(cat_creditori.get(cat, {}).items(),
                                   key=lambda x: x[1], reverse=True))
            tip_c = f"{cat}\nChiuso (saldato): {cl:,.2f} €"
            if cred_txt:
                tip_c += f"\nSaldato da:\n{cred_txt}"
            ay1 = base_y - ap * scala
            cv2.create_rectangle(cx-bar_w-4, ay1, cx-4, base_y, fill=ROSSO, outline="", tags=(tag_a,))
            _tooltip_data2[tag_a] = tip_a
            if ap > 0:
                cv2.create_text(cx-bar_w//2-4, ay1-9, text=f"{ap:,.0f}€", fill=ROSSO, font=("Arial", 7, "bold"))
            cy1 = base_y - cl * scala
            cv2.create_rectangle(cx+4, cy1, cx+bar_w+4, base_y, fill=VERDE, outline="", tags=(tag_c,))
            _tooltip_data2[tag_c] = tip_c
            if cl > 0:
                cv2.create_text(cx+bar_w//2+4, cy1-9, text=f"{cl:,.0f}€", fill=VERDE, font=("Arial", 7, "bold"))
            label = cat if len(cat) <= 10 else cat[:9] + "…"
            cv2.create_text(cx, base_y+16, text=label, fill=txt, font=("Arial", 8, "bold"))
        leg2 = [("Aperto — da saldare", ROSSO), ("Chiuso — saldato", VERDE)]
        lx = pad_l
        for lab, col in leg2:
            cv2.create_rectangle(lx, H-28, lx+14, H-14, fill=col, outline="")
            cv2.create_text(lx+18, H-21, text=lab, fill=txt, font=("Arial", 8), anchor="w")
            lx += len(lab)*7 + 30
        cv2.create_text(canvas_w//2, H-6,
            text="Barra sx = importo ancora aperto  |  Barra dx = importo già chiuso",
            fill="#666", font=("Arial", 7))
        cv2.configure(scrollregion=(0, 0, canvas_w, H))
    def disegna_tab3(event=None):
        cv3.delete("all"); _tooltip_data3.clear()
        W = cv3.winfo_width(); H = cv3.winfo_height()
        if W < 80 or H < 80: return
        filtrati, p_sel = _dati_filtrati()
        mensile_dov = {}; mensile_ver = {}
        mensile_cat_dov = {}
        mensile_cat_ver = {}
        for d_obj, deb in filtrati:
            mkey  = (d_obj.year, d_obj.month)
            quota = deb.get("quota", 0.0)
            cat   = deb.get("categoria", "—")
            pag   = deb.get("pagamenti", {})
            for nome in deb.get("partecipanti", []):
                if p_sel != "Tutti" and nome != p_sel: continue
                mensile_dov.setdefault(mkey, 0.0); mensile_dov[mkey] += quota
                mensile_ver.setdefault(mkey, 0.0)
                mensile_cat_dov.setdefault(mkey, {})
                mensile_cat_dov[mkey].setdefault(cat, 0.0)
                mensile_cat_dov[mkey][cat] += quota
                if pag.get(nome, {}).get("pagato", False):
                    mensile_ver[mkey] += quota
                    mensile_cat_ver.setdefault(mkey, {})
                    mensile_cat_ver[mkey].setdefault(cat, 0.0)
                    mensile_cat_ver[mkey][cat] += quota
        mesi_keys = sorted(set(list(mensile_dov.keys()) + list(mensile_ver.keys())))
        if not mesi_keys:
            cv3.create_text(W//2, H//2, text="Nessun dato", fill="#777", font=("Arial", 11))
            cv3.configure(scrollregion=cv3.bbox("all")); return
        pad_l, pad_r, pad_t, pad_b = 80, 30, 50, 90
        slot_w = max(80, W // len(mesi_keys))
        canvas_w = max(W, pad_l + slot_w * len(mesi_keys) + pad_r)
        area_h = H - pad_t - pad_b
        base_y = pad_t + area_h
        max_v  = max(max(mensile_dov.values() or [1]), max(mensile_ver.values() or [1]), 1)
        scala  = area_h / max_v
        p_label = p_sel if p_sel == "Tutti" else p_sel
        cv3.create_text(canvas_w//2, 22,
            text=f"Andamento Mensile  —  {anno_var.get()}  {p_label}",
            fill=txt, font=("Arial", 11, "bold"))
        for i in range(6):
            val = max_v * i / 5; gy = base_y - val * scala
            cv3.create_line(pad_l, gy, canvas_w - pad_r, gy, fill="#333")
            cv3.create_text(pad_l - 6, gy, text=f"{val:,.0f}€", fill="#888", font=("Arial", 7), anchor="e")
        cv3.create_line(pad_l, pad_t, pad_l, base_y, fill="#555")
        cv3.create_line(pad_l, base_y, canvas_w - pad_r, base_y, fill="#555")
        bar_w = max(10, min(40, slot_w // 3))
        pts_dov = []; pts_ver = []
        for i, mkey in enumerate(mesi_keys):
            cx  = pad_l + i * slot_w + slot_w // 2
            dov = mensile_dov.get(mkey, 0.0); ver = mensile_ver.get(mkey, 0.0)
            etichetta = f"{mesi_nomi[mkey[1]][:3]} {str(mkey[0])[2:]}"
            tag_d = f"md_{i}"; tag_v = f"mv_{i}"
            cat_dov_txt = "\n".join(f"  {c}: {v:,.2f} €"
                for c, v in sorted(mensile_cat_dov.get(mkey, {}).items(),
                                   key=lambda x: x[1], reverse=True))
            tip_d = f"{etichetta}\nDovuto: {dov:,.2f} €\nDa versare: {dov-ver:,.2f} €"
            if cat_dov_txt:
                tip_d += f"\nPer categoria:\n{cat_dov_txt}"
            cat_ver_txt = "\n".join(f"  {c}: {v:,.2f} €"
                for c, v in sorted(mensile_cat_ver.get(mkey, {}).items(),
                                   key=lambda x: x[1], reverse=True))
            tip_v = f"{etichetta}\nVersato: {ver:,.2f} €"
            if cat_ver_txt:
                tip_v += f"\nPer categoria:\n{cat_ver_txt}"
            dy1 = base_y - dov * scala
            cv3.create_rectangle(cx-bar_w-3, dy1, cx-3, base_y, fill=GIALLO, outline="", tags=(tag_d,))
            _tooltip_data3[tag_d] = tip_d
            vy1 = base_y - ver * scala
            cv3.create_rectangle(cx+3, vy1, cx+3+bar_w, base_y, fill=VERDE, outline="", tags=(tag_v,))
            _tooltip_data3[tag_v] = tip_v
            pts_dov.append((cx, dy1)); pts_ver.append((cx, vy1))
            cv3.create_text(cx, base_y+16, text=etichetta, fill=txt, font=("Arial", 7, "bold"), angle=30)
        if len(pts_dov) > 1:
            cv3.create_line(*[c for p in pts_dov for c in p], fill=GIALLO, width=2, smooth=True, dash=(5,3))
        if len(pts_ver) > 1:
            cv3.create_line(*[c for p in pts_ver for c in p], fill=VERDE, width=2, smooth=True, dash=(5,3))
        leg3 = [("Dovuto mensile", GIALLO), ("Versato mensile", VERDE)]
        lx = pad_l
        for lab, col in leg3:
            cv3.create_rectangle(lx, H-28, lx+14, H-14, fill=col, outline="")
            cv3.create_text(lx+18, H-21, text=lab, fill=txt, font=("Arial", 8), anchor="w")
            lx += len(lab)*7 + 30
        cv3.create_text(canvas_w//2, H-6,
            text="Barra sx = dovuto  |  Barra dx = versato  |  Linea tratteggiata = tendenza",
            fill="#666", font=("Arial", 7))
        cv3.configure(scrollregion=(0, 0, canvas_w, H))
    cv1.bind("<Motion>",  lambda e: _show_tip(e, cv1, _tooltip_data1))
    cv1.bind("<Leave>",   _hide_tip)
    cv2.bind("<Motion>",  lambda e: _show_tip(e, cv2, _tooltip_data2))
    cv2.bind("<Leave>",   _hide_tip)
    cv3.bind("<Motion>",  lambda e: _show_tip(e, cv3, _tooltip_data3))
    cv3.bind("<Leave>",   _hide_tip)
    def aggiorna_grafici(*_args):
        disegna_tab1(); disegna_tab2(); disegna_tab3()
    cv1.bind("<Configure>", lambda e: disegna_tab1())
    cv2.bind("<Configure>", lambda e: disegna_tab2())
    cv3.bind("<Configure>", lambda e: disegna_tab3())
    nb.bind("<<NotebookTabChanged>>", lambda e: aggiorna_grafici())
    for cb_w in toolbar.winfo_children():
        if isinstance(cb_w, ttk.Combobox):
            cb_w.bind("<<ComboboxSelected>>", aggiorna_grafici)
    btn_frame_g = ttk.Frame(popup, padding=(10, 4, 10, 8))
    btn_frame_g.pack(fill=tk.X)
    img_chiudi_gb = self.icone_gui.get("chiudi")
    btn_chiudi_gb = ttk.Label(btn_frame_g, compound="left", image=img_chiudi_gb,
                              text=" Chiudi" if img_chiudi_gb else "Chiudi",
                              background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                              cursor="hand2", padding=(12, 5))
    btn_chiudi_gb.pack(side=tk.RIGHT)
    btn_chiudi_gb.bind("<Button-1>", lambda e: popup.destroy())
    popup.after(150, aggiorna_grafici)
