#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import uuid
import math
import calendar
import datetime
import subprocess
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog

def apri_studio(self):
    import __main__ as _app
    DB_DIR              = _app.DB_DIR
    STUDIO_CLIENTI      = _app.STUDIO_CLIENTI
    STUDIO_APPUNTAMENTI = _app.STUDIO_APPUNTAMENTI
    STUDIO_PRESTAZIONI  = _app.STUDIO_PRESTAZIONI
    STUDIO_FATTURE      = _app.STUDIO_FATTURE
    STUDIO_CASSA        = _app.STUDIO_CASSA
    STUDIO_MAGAZZINO    = _app.STUDIO_MAGAZZINO
    STUDIO_EMITTENTE    = _app.STUDIO_EMITTENTE
    EXPORT_FATTURE_DIR  = _app.EXPORT_FATTURE_DIR
    EXPORT_DIR          = _app.EXPORT_DIR
    if hasattr(self, '_studio_popup') and self._studio_popup and \
            self._studio_popup.winfo_exists():
        self._studio_popup.lift(); self._studio_popup.focus_force(); return
    def _load(path, default=None):
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return default if default is not None else []
    def _save(path, data):
        try:
            os.makedirs(DB_DIR, exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.show_custom_warning("Errore salvataggio", str(e))
    def _new_id():
        return str(uuid.uuid4())[:8]
    def _fmt_eur(val):
        try:
            return f"€ {float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception:
            return "€ 0,00"
    clienti      = _load(STUDIO_CLIENTI)
    appuntamenti = _load(STUDIO_APPUNTAMENTI)
    prestazioni  = _load(STUDIO_PRESTAZIONI)
    fatture      = _load(STUDIO_FATTURE)
    cassa        = _load(STUDIO_CASSA)
    magazzino    = _load(STUDIO_MAGAZZINO)
    emittente    = _load(STUDIO_EMITTENTE) or {}
    if isinstance(emittente, list): emittente = {}
    win = tk.Toplevel(self)
    self._studio_popup = win
    win.withdraw()
    win.title("Studio Professionale")
    win.configure(bg=self.COLOR_BACKGROUND)
    win.protocol("WM_DELETE_WINDOW",
                 lambda: [win.destroy(), setattr(self, '_studio_popup', None)])
    win.bind("<Escape>",
             lambda e: [win.destroy(), setattr(self, '_studio_popup', None)])
    W, H = 1300, 630
    self.update_idletasks()
    px = self.winfo_rootx() + self.winfo_width()  // 2 - W // 2
    py = self.winfo_rooty() + self.winfo_height() // 2 - H // 2
    win.geometry(f"{W}x{H}+{max(0,px)}+{max(0,py)}")
    win.minsize(1300, 630)
    win.deiconify()
    win.transient(self)
    nb = ttk.Notebook(win)
    nb.pack(fill="both", expand=True, padx=6, pady=(4,6))
    tab_dash = tk.Frame(nb, bg=self.COLOR_BACKGROUND)
    tab_cli  = tk.Frame(nb, bg=self.COLOR_BACKGROUND)
    tab_app  = tk.Frame(nb, bg=self.COLOR_BACKGROUND)
    tab_pre  = tk.Frame(nb, bg=self.COLOR_BACKGROUND)
    tab_fat  = tk.Frame(nb, bg=self.COLOR_BACKGROUND)
    tab_cas  = tk.Frame(nb, bg=self.COLOR_BACKGROUND)
    tab_mag  = tk.Frame(nb, bg=self.COLOR_BACKGROUND)
    tab_emi  = tk.Frame(nb, bg=self.COLOR_BACKGROUND)
    nb.add(tab_dash, text="  Dashboard  ")
    nb.add(tab_cli,  text="  Clienti  ")
    nb.add(tab_app,  text="  Agenda  ")
    nb.add(tab_pre,  text="  Prestazioni  ")
    nb.add(tab_fat,  text="  Fatture / Preventivi  ")
    nb.add(tab_cas,  text="  Cassa  ")
    nb.add(tab_mag,  text="  Magazzino  ")
    nb.add(tab_emi,  text="  La Mia Azienda  ")
    tab_close = tk.Frame(nb, bg=self.COLOR_BACKGROUND)
    nb.add(tab_close, text="  ✖ Chiudi  ")
    def _check_close(e):
        try:
            idx = nb.index("@%d,%d" % (e.x, e.y))
            if idx == nb.index(tab_close):
                win.destroy()
        except Exception:
            pass
    nb.bind("<Button-1>", _check_close)
    def _mk_btn(parent, ico_key, testo, cmd, fg=None, side="left", padx=6):
        img = self.icone_gui.get(ico_key)
        fg  = fg or self.TEXT_COLOR
        lbl = ttk.Label(parent, text=f" {testo}", image=img, compound="left",
                        background=self.COLOR_WIDGET_BG, foreground=fg,
                        cursor="hand2", font=("Arial", 9, "bold"), padding=(6, 3))
        if img: lbl.image = img
        lbl.pack(side=side, padx=padx, pady=2)
        lbl.bind("<Button-1>", lambda e, c=cmd: c())
        return lbl
    def _mk_cal_btn(parent, entry_widget):
        img = self.icone_gui.get("calendario")
        lbl = ttk.Label(parent, image=img, cursor="hand2",
                        background=self.COLOR_WIDGET_BG, padding=(2,0))
        if img: lbl.image = img
        lbl.pack(side="left", padx=2)
        def _apri():
            _tmp = tk.StringVar()
            def _on_write(*_):
                v = _tmp.get().replace("-", "/")
                entry_widget.delete(0, "end")
                entry_widget.insert(0, v)
            _tmp.trace_add("write", _on_write)
            self.mostra_calendario_popup_semplice(entry_widget, _tmp)
        lbl.bind("<Button-1>", lambda e: _apri())
        return lbl
    def _btn_bar(parent, items):
        bar = tk.Frame(parent, bg=self.COLOR_WIDGET_BG,
                       highlightthickness=1,
                       highlightbackground=self.COLOR_HIGHLIGHT)
        bar.pack(fill="x", padx=6, pady=(0, 4))
        for ico, testo, cmd, fg in items:
            _mk_btn(bar, ico, testo, cmd, fg)
        return bar
    def _sep(parent):
        tk.Frame(parent, bg=self.COLOR_HIGHLIGHT, height=1).pack(
            fill="x", padx=6, pady=2)
    def _tree(parent, cols, widths, height=18):
        frm = tk.Frame(parent, bg=self.COLOR_BACKGROUND)
        frm.pack(fill="both", expand=True, padx=6, pady=2)
        vsb = ttk.Scrollbar(frm, orient="vertical", style="Vertical.TScrollbar")
        hsb = ttk.Scrollbar(frm, orient="horizontal", style="Horizontal.TScrollbar")
        tv  = ttk.Treeview(frm, columns=cols, show="headings",
                           yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                           selectmode="browse", height=height)
        vsb.configure(command=tv.yview)
        hsb.configure(command=tv.xview)
        for c, w in zip(cols, widths):
            tv.heading(c, text=c, anchor="w",
                       command=lambda _c=c, _tv=tv: self.treeview_sort_column(_tv, _c, False))
            tv.column(c, width=w, anchor="w", minwidth=40)
        tv.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        return tv
    def _form_win(title, w=440, h=None):
        fw = tk.Toplevel(win)
        fw.withdraw()
        fw.title(title)
        fw.transient(win)
        fw.configure(bg=self.COLOR_WIDGET_BG)
        fw.resizable(False, False)
        fw.bind("<Escape>", lambda e: fw.destroy())
        if h:
            win.update_idletasks()
            fx = win.winfo_rootx() + win.winfo_width()  // 2 - w // 2
            fy = win.winfo_rooty() + win.winfo_height() // 2 - h // 2
            fw.geometry(f"{w}x{h}+{max(0,fx)}+{max(0,fy)}")
        fw.deiconify()
        return fw
    def _row(fw, label, row, col=0):
        tk.Label(fw, text=label, bg=self.COLOR_WIDGET_BG, fg=self.COLOR_TEXT,
                 font=("Arial", 9)).grid(row=row, column=col, sticky="w",
                                          padx=10, pady=3)
    def _ent(fw, row, col=1, width=26, **kw):
        e = ttk.Entry(fw, width=width, **kw)
        e.grid(row=row, column=col, sticky="ew", padx=10, pady=3)
        return e
    def _cbo(fw, row, vals, col=1, width=22):
        c = ttk.Combobox(fw, values=vals, width=width, state="readonly",
                         style="Border.TCombobox")
        c.grid(row=row, column=col, sticky="ew", padx=10, pady=3)
        return c
    def _titolo(fw, testo, row=0):
        ttk.Label(fw, text=testo, font=("Arial", 10, "bold"),
                  background=self.COLOR_WIDGET_BG,
                  foreground=self.COLOR_HIGHLIGHT).grid(
            row=row, column=0, columnspan=6, padx=10,
            pady=(10, 6), sticky="w")
    def _salva_btn(fw, cmd, row, cols=2):
        img = self.icone_gui.get("salva")
        b   = ttk.Label(fw, text=" Salva", image=img, compound="left",
                        background=self.COLOR_WIDGET_BG,
                        foreground=self.COLOR_GREEN,
                        cursor="hand2", font=("Arial", 9, "bold"),
                        padding=(10, 4))
        if img: b.image = img
        b.grid(row=row, column=0, columnspan=cols, pady=10)
        b.bind("<Button-1>", lambda e, c=cmd: c())
    def _nomi_clienti():
        return sorted({f"{c['nome']} {c.get('cognome','')}".strip()
                       for c in clienti}) or ["—"]
    def _nomi_prestazioni():
        return sorted({p["nome"] for p in prestazioni}) or ["—"]
    def _build_dashboard():
        for w in tab_dash.winfo_children(): w.destroy()
        oggi = datetime.date.today()
        mese = oggi.month
        anno = oggi.year
        fat_mese = sum(
            sum(r.get("qty", 1) * r.get("prezzo", 0) for r in f.get("righe", []))
            for f in fatture
            if f.get("stato") in ("Emessa", "Pagata")
            and f.get("data", "")[:7] == f"{anno}-{mese:02d}"
        )
        fat_anno = sum(
            sum(r.get("qty", 1) * r.get("prezzo", 0) for r in f.get("righe", []))
            for f in fatture
            if f.get("stato") in ("Emessa", "Pagata")
            and f.get("data", "")[:4] == str(anno)
        )
        da_incassare = sum(
            sum(r.get("qty", 1) * r.get("prezzo", 0) for r in f.get("righe", []))
            for f in fatture if f.get("stato") == "Emessa"
        )
        app_oggi = [a for a in appuntamenti
                    if a.get("data", "") == oggi.strftime("%Y-%m-%d")
                    and a.get("stato") != "Annullato"]
        app_settimana = [
            a for a in appuntamenti
            if a.get("stato") != "Annullato"
            and oggi <= datetime.date.fromisoformat(a["data"]) <=
                oggi + datetime.timedelta(days=6)
            if a.get("data")
        ]
        saldo_cassa = sum(
            m.get("importo", 0) * (1 if m.get("tipo") == "Entrata" else -1)
            for m in cassa
        )
        sotto_soglia = [m for m in magazzino
                        if m.get("quantita", 0) <= m.get("soglia", 0)]
        kpi_frame = tk.Frame(tab_dash, bg=self.COLOR_BACKGROUND)
        kpi_frame.pack(fill="x", padx=10, pady=(8, 4))
        kpi_frame.columnconfigure(list(range(6)), weight=1)
        def _kpi_card(parent, col, titolo, valore, colore, sotto=""):
            card = tk.Frame(parent, bg=self.COLOR_WIDGET_BG,
                            highlightthickness=2,
                            highlightbackground=colore, padx=10, pady=8)
            card.grid(row=0, column=col, padx=5, pady=4, sticky="nsew")
            tk.Label(card, text=titolo, font=("Arial", 8, "bold"),
                     bg=self.COLOR_WIDGET_BG, fg=colore).pack(anchor="w")
            tk.Label(card, text=valore, font=("Arial", 14, "bold"),
                     bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR).pack(anchor="w")
            if sotto:
                tk.Label(card, text=sotto, font=("Arial", 7),
                         bg=self.COLOR_WIDGET_BG,
                         fg=self.COLOR_TEXT).pack(anchor="w")
        _kpi_card(kpi_frame, 0, "FATTURATO MESE",
                  _fmt_eur(fat_mese), self.COLOR_GREEN)
        _kpi_card(kpi_frame, 1, "FATTURATO ANNO",
                  _fmt_eur(fat_anno), self.COLOR_GREEN)
        _kpi_card(kpi_frame, 2, "DA INCASSARE",
                  _fmt_eur(da_incassare), self.COLOR_ORANGE,
                  f"{sum(1 for f in fatture if f.get('stato')=='Emessa')} fatture aperte")
        _kpi_card(kpi_frame, 3, "SALDO CASSA",
                  _fmt_eur(saldo_cassa),
                  self.COLOR_GREEN if saldo_cassa >= 0 else self.COLOR_RED)
        _kpi_card(kpi_frame, 4, "APPUNTAMENTI OGGI",
                  str(len(app_oggi)), self.COLOR_HIGHLIGHT,
                  f"{len(app_settimana)} questa settimana")
        _kpi_card(kpi_frame, 5, "MAGAZZINO ESAURITO",
                  str(len(sotto_soglia)),
                  self.COLOR_RED if sotto_soglia else self.COLOR_GREEN,
                  "voci sotto soglia")
        _sep(tab_dash)
        body = tk.Frame(tab_dash, bg=self.COLOR_BACKGROUND)
        body.pack(fill="both", expand=True, padx=6, pady=4)
        body.columnconfigure(0, weight=2)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        graf_frame = tk.LabelFrame(body, text=" Fatturato ultimi 6 mesi ",
                                   bg=self.COLOR_WIDGET_BG,
                                   fg=self.COLOR_HIGHLIGHT,
                                   font=("Arial", 9, "bold"))
        graf_frame.grid(row=0, column=0, sticky="nsew", padx=(0,4))
        cv = tk.Canvas(graf_frame, bg=self.COLOR_WIDGET_BG,
                       highlightthickness=0)
        cv.pack(fill="both", expand=True, padx=8, pady=8)
        def _draw_barchart(event=None):
            cv.delete("all")
            cw = cv.winfo_width()  or 500
            ch = cv.winfo_height() or 260
            margin_l, margin_b, margin_t = 60, 40, 20
            W_plot = cw - margin_l - 20
            H_plot = ch - margin_b - margin_t
            mesi = []
            for i in range(5, -1, -1):
                d = oggi.replace(day=1) - datetime.timedelta(days=1) * 0
                m_num = ((oggi.month - 1 - i) % 12) + 1
                y_num = oggi.year + ((oggi.month - 1 - i) // 12)
                mesi.append((y_num, m_num))
            valori = []
            for y, m in mesi:
                s = sum(
                    sum(r.get("qty", 1) * r.get("prezzo", 0)
                        for r in f.get("righe", []))
                    for f in fatture
                    if f.get("stato") in ("Emessa", "Pagata")
                    and f.get("data", "")[:7] == f"{y}-{m:02d}"
                )
                valori.append(s)
            max_v = max(valori) if any(v > 0 for v in valori) else 1
            n  = len(valori)
            bw = int(W_plot / n * 0.6)
            gap = W_plot / n
            for i in range(5):
                gy = margin_t + H_plot - int(H_plot * i / 4)
                cv.create_line(margin_l, gy, cw - 20, gy,
                               fill=self.COLOR_TEXT, dash=(2, 4))
                cv.create_text(margin_l - 4, gy,
                               text=_fmt_eur(max_v * i / 4).replace("€ ", ""),
                               anchor="e", font=("Arial", 7),
                               fill=self.COLOR_TEXT)
            for i, (val, (y, m)) in enumerate(zip(valori, mesi)):
                x_center = margin_l + gap * i + gap / 2
                bh = int(H_plot * val / max_v) if max_v else 0
                x0 = x_center - bw / 2
                x1 = x_center + bw / 2
                y0 = margin_t + H_plot - bh
                y1 = margin_t + H_plot
                colore = self.COLOR_HIGHLIGHT if (y, m) == (oggi.year, oggi.month) \
                         else self.COLOR_GREEN
                cv.create_rectangle(x0, y0, x1, y1,
                                    fill=colore, outline="", width=0)
                if bh > 14:
                    cv.create_text((x0+x1)//2, y0+4,
                                   text=f"{val:,.0f}",
                                   anchor="n", font=("Arial", 7, "bold"),
                                   fill="white")
                cv.create_text(x_center, margin_t + H_plot + 12,
                               text=f"{m:02d}/{str(y)[2:]}",
                               font=("Arial", 7), fill=self.COLOR_TEXT)

        cv.bind("<Configure>", _draw_barchart)
        cv.after(80, _draw_barchart)
        pros_frame = tk.LabelFrame(body, text=" Prossimi appuntamenti ",
                                   bg=self.COLOR_WIDGET_BG,
                                   fg=self.COLOR_HIGHLIGHT,
                                   font=("Arial", 9, "bold"))
        pros_frame.grid(row=0, column=1, sticky="nsew")
        tv_pros = ttk.Treeview(pros_frame,
                               columns=("data", "ora", "cliente", "prestazione"),
                               show="headings", height=14)
        for col, lbl, w in [("data", "Data", 75), ("ora", "Ora", 42),
                             ("cliente", "Cliente", 110), ("prestazione", "Prest.", 100)]:
            tv_pros.heading(col, text=lbl, anchor="w")
            tv_pros.column(col, width=w, anchor="w")
        tv_pros.pack(fill="both", expand=True, padx=4, pady=4)
        prossimi = sorted(
            [a for a in appuntamenti
             if a.get("stato") != "Annullato" and a.get("data", "") >= oggi.strftime("%Y-%m-%d")],
            key=lambda x: (x.get("data", ""), x.get("ora", ""))
        )[:20]
        for a in prossimi:
            data_fmt = a.get("data", "")
            try:
                data_fmt = datetime.date.fromisoformat(a["data"]).strftime("%d/%m/%Y")
            except Exception:
                pass
            tag = "oggi" if a.get("data","") == oggi.strftime("%Y-%m-%d") else ""
            tv_pros.insert("", "end", tags=(tag,),
                           values=(data_fmt, a.get("ora",""),
                                   a.get("cliente_nome",""), a.get("prestazione","")))
        tv_pros.tag_configure("oggi",
                              background=self.COLOR_HIGHLIGHT,
                              foreground="white")
    def _build_clienti():
        for w in tab_cli.winfo_children(): w.destroy()
        cols   = ["Nome", "Cognome", "Telefono", "Email", "CF / P.IVA", "Note"]
        widths = [120, 130, 110, 190, 130, 260]
        tv = _tree(tab_cli, cols, widths)
        for col in cols:
                tv.heading(col, anchor="w")
        def _refresh(sel_id=None):
            tv.delete(*tv.get_children())
            for c in sorted(clienti,
                            key=lambda x: x.get("cognome", "").lower()):
                tv.insert("", "end", iid=c["id"],
                          values=(c.get("nome",""), c.get("cognome",""),
                                  c.get("telefono",""), c.get("email",""),
                                  c.get("cf_piva",""), c.get("note","")))
            if sel_id:
                try: tv.selection_set(sel_id); tv.see(sel_id)
                except Exception: pass
        def _storico_cliente():
            sel = tv.selection()
            if not sel:
                self.show_toast("Seleziona un cliente."); return
            cli = next((c for c in clienti if c["id"] == sel[0]), None)
            if not cli: return
            nome_cli = f"{cli.get('nome','')} {cli.get('cognome','')}".strip()
            sw = _form_win(f"Storico — {nome_cli}", 700, 520)
            sw.resizable(True, True)
            tk.Label(sw, text=f"Storico di {nome_cli}",
                     font=("Arial", 11, "bold"),
                     bg=self.COLOR_WIDGET_BG,
                     fg=self.COLOR_HIGHLIGHT).pack(padx=12, pady=(10,4), anchor="w")
            nb_s = ttk.Notebook(sw)
            nb_s.pack(fill="both", expand=True, padx=8, pady=4)
            tf_a = tk.Frame(nb_s, bg=self.COLOR_WIDGET_BG)
            nb_s.add(tf_a, text="  Appuntamenti  ")
            tv_a = _tree(tf_a,
                         ["Data","Ora","Prestazione","Stato","Note"],
                         [90, 50, 170, 100, 220], height=10)
            for a in sorted([x for x in appuntamenti
                             if x.get("cliente_nome","").strip() == nome_cli],
                            key=lambda x: x.get("data","")):
                try: df = datetime.date.fromisoformat(a["data"]).strftime("%d/%m/%Y")
                except: df = a.get("data","")
                tv_a.insert("", "end",
                            values=(df, a.get("ora",""), a.get("prestazione",""),
                                    a.get("stato",""), a.get("note","")))
            tf_f = tk.Frame(nb_s, bg=self.COLOR_WIDGET_BG)
            nb_s.add(tf_f, text="  Fatture / Preventivi  ")
            tv_f = _tree(tf_f,
                         ["N°","Data","Tipo","Totale €","Stato"],
                         [55, 90, 90, 90, 90], height=10)
            for f in sorted([x for x in fatture
                             if x.get("cliente_nome","").strip() == nome_cli],
                            key=lambda x: x.get("data",""), reverse=True):
                tot = sum(r.get("qty",1)*r.get("prezzo",0) for r in f.get("righe",[]))
                try: df = datetime.date.fromisoformat(f["data"]).strftime("%d/%m/%Y")
                except: df = f.get("data","")
                tv_f.insert("", "end",
                            values=(f.get("numero",""), df,
                                    f.get("tipo_doc","Fattura"),
                                    _fmt_eur(tot), f.get("stato","")))
            img_c = self.icone_gui.get("chiudi")
            bc = ttk.Label(sw, text=" Chiudi", image=img_c, compound="left",
                           background=self.COLOR_WIDGET_BG,
                           foreground=self.COLOR_RED,
                           cursor="hand2", font=("Arial", 9, "bold"),
                           padding=(8, 4))
            if img_c: bc.image = img_c
            bc.pack(pady=6)
            bc.bind("<Button-1>", lambda e: sw.destroy())
        def _form(prefill=None):
            fw = _form_win("Scheda Cliente", 440)
            fw.withdraw()
            fw.columnconfigure(1, weight=1)
            _titolo(fw, "Modifica" if prefill else "➕ Nuovo cliente")
            W, H = 440, 330
            win.update_idletasks()
            fx = win.winfo_rootx() + win.winfo_width()  // 2 - W // 2
            fy = win.winfo_rooty() + win.winfo_height() // 2 - H // 2
            fw.geometry(f"{W}x{H}+{max(0,fx)}+{max(0,fy)}")
            fw.deiconify()
            _row(fw, "Nome *",      1); e_n   = _ent(fw, 1)
            _row(fw, "Cognome",     2); e_cog  = _ent(fw, 2)
            _row(fw, "Azienda",     3); e_az   = _ent(fw, 3)
            _row(fw, "Telefono",    4); e_tel  = _ent(fw, 4)
            _row(fw, "Email",       5); e_eml  = _ent(fw, 5)
            _row(fw, "CF / P.IVA", 6); e_cf   = _ent(fw, 6)
            _row(fw, "Indirizzo",  7); e_ind  = _ent(fw, 7)
            _row(fw, "Note",       8); e_note = _ent(fw, 8)
            def _limit(entry, maxlen):
                vcmd = (fw.register(
                    lambda P: len(P) <= maxlen), "%P")
                entry.config(validate="key", validatecommand=vcmd)
            _limit(e_n,    20)
            _limit(e_cog,  20)
            _limit(e_az,   20)
            _limit(e_tel,  35)
            _limit(e_eml,  35)
            _limit(e_cf,   16)
            _limit(e_ind,  50)
            _limit(e_note, 30)
            if prefill:
                for e, k in [(e_n,"nome"),(e_cog,"cognome"),(e_az,"azienda"),
                             (e_tel,"telefono"),(e_eml,"email"),(e_cf,"cf_piva"),
                             (e_ind,"indirizzo"),(e_note,"note")]:
                    e.insert(0, prefill.get(k,""))
            def _salva():
                nome = e_n.get().strip()
                if not nome:
                    self.show_toast("Nome obbligatorio."); return
                record = {
                    "id":        prefill["id"] if prefill else _new_id(),
                    "nome":      nome,
                    "cognome":   e_cog.get().strip(),
                    "azienda":   e_az.get().strip(),
                    "telefono":  e_tel.get().strip(),
                    "email":     e_eml.get().strip(),
                    "cf_piva":   e_cf.get().strip(),
                    "indirizzo": e_ind.get().strip(),
                    "note":      e_note.get().strip(),
                }
                if prefill:
                    idx = next((i for i,c in enumerate(clienti)
                                if c["id"]==prefill["id"]), None)
                    if idx is not None: clienti[idx] = record
                else:
                    clienti.append(record)
                _save(STUDIO_CLIENTI, clienti)
                _refresh(record["id"])
                fw.destroy()
                self.show_toast("Cliente salvato.")
            fw.bind("<Escape>", lambda e: fw.destroy())
            bot = tk.Frame(fw, bg=self.COLOR_BACKGROUND)
            bot.grid(row=9, column=0, columnspan=4, pady=8)
            _mk_btn(bot, "salva",  "Salva",  _salva)
            _mk_btn(bot, "chiudi", "Chiudi", fw.destroy)
        def _modifica():
            sel = tv.selection()
            if not sel: self.show_toast("Seleziona un cliente."); return
            r = next((c for c in clienti if c["id"]==sel[0]), None)
            if r: _form(prefill=r)
        def _elimina():
            sel = tv.selection()
            if not sel: self.show_toast("Seleziona un cliente."); return
            nome = tv.item(sel[0], "values")[0]
            if self.show_custom_askyesno("Elimina",
                    f"Eliminare il cliente '{nome}'?"):
                nonlocal clienti
                clienti = [c for c in clienti if c["id"]!=sel[0]]
                _save(STUDIO_CLIENTI, clienti)
                _refresh()
                self.show_toast("Cliente eliminato.")
        tv.bind("<Double-1>", lambda e: _modifica())
        _btn_bar(tab_cli, [
            ("aggiungi",   "Nuovo",       lambda: _form(),        self.COLOR_GREEN),
            ("modifica",   "Modifica",    _modifica,              self.COLOR_HIGHLIGHT),
            ("documenti",  "Storico",     _storico_cliente,       self.TEXT_COLOR),
            ("delete",     "Elimina",     _elimina,               self.COLOR_RED),
        ])
        _refresh()
    def _build_agenda():
        for w in tab_app.winfo_children(): w.destroy()
        oggi      = datetime.date.today()
        nav_date  = [oggi.replace(day=1)]
        top_row = tk.Frame(tab_app, bg=self.COLOR_BACKGROUND)
        top_row.pack(fill="x", padx=6, pady=(4, 0))
        lbl_mese = tk.Label(top_row, text="",
                            font=("Arial", 12, "bold"),
                            bg=self.COLOR_BACKGROUND,
                            fg=self.COLOR_HIGHLIGHT)
        lbl_mese.pack(side="left", padx=8)
        filtro_var = tk.StringVar(value="Tutti")
        tk.Label(top_row, text="Mostra:", bg=self.COLOR_BACKGROUND,
                 fg=self.TEXT_COLOR, font=("Arial", 9)).pack(side="right", padx=4)
        cb_filtro = ttk.Combobox(top_row, textvariable=filtro_var,
                                 values=["Tutti","Confermato","Completato","Annullato"],
                                 width=12, state="readonly",
                                 style="Border.TCombobox")
        cb_filtro.pack(side="right", padx=4)
        body = tk.Frame(tab_app, bg=self.COLOR_BACKGROUND)
        body.pack(fill="both", expand=True, padx=6, pady=4)
        det_frame = tk.LabelFrame(body, text=" Appuntamenti del giorno ",
                                  bg=self.COLOR_WIDGET_BG,
                                  fg=self.COLOR_HIGHLIGHT,
                                  font=("Arial", 9, "bold"),
                                  width=500)
        det_frame.pack(side="right", fill="y")
        det_frame.pack_propagate(False)
        cal_frame = tk.Frame(body, bg=self.COLOR_WIDGET_BG,
                             highlightthickness=1,
                             highlightbackground=self.COLOR_HIGHLIGHT)
        cal_frame.pack(side="left", fill="both", expand=True, padx=(0,4))
        cal_cv = tk.Canvas(cal_frame, bg=self.COLOR_WIDGET_BG,
                           highlightthickness=0)
        cal_cv.pack(fill="both", expand=True)
        sel_giorno = [None]
        tv_det = ttk.Treeview(det_frame,
                              columns=("ora","cliente","prestazione","stato"),
                              show="headings", height=16)
        for col, lbl, w in [("ora","Ora",50),("cliente","Cliente",120),
                             ("prestazione","Prestazione",120),("stato","Stato",90)]:
            tv_det.heading(col, text=lbl, anchor="w")
            tv_det.column(col, width=w, anchor="w")
        vsb_d = ttk.Scrollbar(det_frame, orient="vertical",
                              style="Vertical.TScrollbar",
                              command=tv_det.yview)
        tv_det.configure(yscrollcommand=vsb_d.set)
        tv_det.pack(side="left", fill="both", expand=True, padx=4, pady=4)
        vsb_d.pack(side="right", fill="y")
        def _aggiorna_dettaglio(giorno_str):
            tv_det.delete(*tv_det.get_children())
            if not giorno_str: return
            filtro = filtro_var.get()
            for a in sorted(
                [x for x in appuntamenti
                 if x.get("data","") == giorno_str
                 and (filtro == "Tutti" or x.get("stato","") == filtro)],
                key=lambda x: x.get("ora","")
            ):
                stato = a.get("stato","")
                tag = "verde" if stato=="Completato" else \
                      ("rosso" if stato=="Annullato" else "")
                tv_det.insert("", "end", iid=a["id"], tags=(tag,),
                              values=(a.get("ora",""), a.get("cliente_nome",""),
                                      a.get("prestazione",""), stato))
            tv_det.tag_configure("verde", foreground=self.COLOR_GREEN)
            tv_det.tag_configure("rosso", foreground=self.COLOR_RED)
        GIORNI_IT = ["Lun","Mar","Mer","Gio","Ven","Sab","Dom"]
        MESI_IT   = ["","Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno",
                     "Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"]
        cell_map = {}
        def _draw_cal(event=None):
            cal_cv.delete("all")
            cell_map.clear()
            cw = cal_cv.winfo_width()  or 500
            ch = cal_cv.winfo_height() or 400
            primo = nav_date[0]
            lbl_mese.config(text=f"{MESI_IT[primo.month]}  {primo.year}")
            head_h = 24
            col_w  = cw / 7
            for i, gn in enumerate(GIORNI_IT):
                cx = i * col_w + col_w / 2
                fg = self.COLOR_RED if i >= 5 else self.COLOR_TEXT
                cal_cv.create_text(cx, head_h/2, text=gn,
                                   font=("Arial", 8, "bold"), fill=fg)
            num_giorni = calendar.monthrange(primo.year, primo.month)[1]
            start_dow  = primo.weekday()
            righe      = math.ceil((start_dow + num_giorni) / 7)
            cell_h     = max(30, (ch - head_h) / righe)
            app_giorni = {a.get("data","") for a in appuntamenti
                          if a.get("data","")[:7] == primo.strftime("%Y-%m")}
            for g in range(num_giorni):
                d       = primo + datetime.timedelta(days=g)
                ds      = d.strftime("%Y-%m-%d")
                idx     = g + start_dow
                row_i   = idx // 7
                col_i   = idx % 7
                x0      = col_i * col_w + 1
                y0      = head_h + row_i * cell_h + 1
                x1      = x0 + col_w - 2
                y1      = y0 + cell_h - 2
                is_oggi = (d == oggi)
                is_sel  = (ds == sel_giorno[0])
                is_we   = col_i >= 5
                has_app = ds in app_giorni
                if is_sel:
                    fill = self.COLOR_HIGHLIGHT
                elif is_oggi:
                    fill = "#1a4a2a" if self.COLOR_BACKGROUND == "#0D0D0D" \
                           else "#d0ead0"
                elif is_we:
                    fill = "#1a1a2a" if self.COLOR_BACKGROUND == "#0D0D0D" \
                           else "#f5f0ff"
                else:
                    fill = self.COLOR_WIDGET_BG
                cal_cv.create_rectangle(x0, y0, x1, y1,
                                        fill=fill,
                                        outline=self.COLOR_HIGHLIGHT
                                        if is_sel or is_oggi else self.COLOR_TEXT)
                txt_fg = "white" if is_sel else \
                         (self.COLOR_RED if is_we else self.TEXT_COLOR)
                cal_cv.create_text(x0+8, y0+10, text=str(d.day),
                                   anchor="nw", font=("Arial", 9, "bold"),
                                   fill=txt_fg)
                if has_app:
                    n_app = sum(1 for a in appuntamenti
                                if a.get("data","") == ds)
                    cal_cv.create_oval(x1-14, y0+4, x1-4, y0+14,
                                       fill=self.COLOR_GREEN, outline="")
                    cal_cv.create_text(x1-9, y0+9, text=str(n_app),
                                       font=("Arial", 6, "bold"),
                                       fill="white")
                cell_map[ds] = (x0, y0, x1, y1)
        def _on_cal_click(event):
            x, y = event.x, event.y
            for ds, (x0,y0,x1,y1) in cell_map.items():
                if x0 <= x <= x1 and y0 <= y <= y1:
                    sel_giorno[0] = ds
                    _draw_cal()
                    _aggiorna_dettaglio(ds)
                    return
        cal_cv.bind("<Configure>", _draw_cal)
        cal_cv.bind("<Button-1>",  _on_cal_click)
        def _prev_mese():
            p = nav_date[0]
            m = p.month - 1 or 12
            y = p.year - (1 if p.month == 1 else 0)
            nav_date[0] = p.replace(year=y, month=m, day=1)
            _draw_cal()
        def _next_mese():
            p = nav_date[0]
            m = p.month % 12 + 1
            y = p.year + (1 if p.month == 12 else 0)
            nav_date[0] = p.replace(year=y, month=m, day=1)
            _draw_cal()
        def _vai_oggi():
            nav_date[0] = oggi.replace(day=1)
            sel_giorno[0] = oggi.strftime("%Y-%m-%d")
            _draw_cal()
            _aggiorna_dettaglio(sel_giorno[0])
        cb_filtro.bind("<<ComboboxSelected>>",
                       lambda e: _aggiorna_dettaglio(sel_giorno[0]))
        def _form_app(prefill=None):
            fw = _form_win("Appuntamento", 440)
            fw.withdraw()
            fw.columnconfigure(1, weight=1)
            _titolo(fw, "Modifica" if prefill else "➕ Nuovo appuntamento")
            W, H = 440, 280
            win.update_idletasks()
            fx = win.winfo_rootx() + win.winfo_width()  // 2 - W // 2
            fy = win.winfo_rooty() + win.winfo_height() // 2 - H // 2
            fw.geometry(f"{W}x{H}+{max(0,fx)}+{max(0,fy)}")
            fw.deiconify()
            _row(fw, "Data (GG/MM/AAAA) *", 1)
            frm_d = tk.Frame(fw, bg=self.COLOR_WIDGET_BG)
            frm_d.grid(row=1, column=1, sticky="w", padx=10, pady=3)
            e_data = ttk.Entry(frm_d, width=12)
            e_data.pack(side="left")
            _mk_cal_btn(frm_d, e_data)
            _row(fw, "Ora (HH:MM)",          2)
            e_ora  = _ent(fw, 2, width=8)
            _row(fw, "Cliente",              3)
            e_cli  = _cbo(fw, 3, _nomi_clienti(), width=24)
            _row(fw, "Prestazione",          4)
            e_pre  = _cbo(fw, 4, _nomi_prestazioni(), width=24)
            _row(fw, "Stato",               5)
            e_stato= _cbo(fw, 5, ["Confermato","Completato","Annullato"], width=14)
            _row(fw, "Note",                6)
            e_note = _ent(fw, 6)
            if prefill:
                d = prefill.get("data","")
                if d and len(d)==10 and "-" in d:
                    d = d[8:]+"/"+d[5:7]+"/"+d[:4]
                e_data.insert(0, d)
                e_ora.insert(0,   prefill.get("ora",""))
                e_cli.set(        prefill.get("cliente_nome",""))
                e_pre.set(        prefill.get("prestazione",""))
                e_stato.set(      prefill.get("stato","Confermato"))
                e_note.insert(0,  prefill.get("note",""))
            else:
                data_def = sel_giorno[0] or oggi.strftime("%Y-%m-%d")
                if data_def and "-" in data_def:
                    data_def = data_def[8:]+"/"+data_def[5:7]+"/"+data_def[:4]
                e_data.insert(0, data_def)
            def _salva():
                data_raw = e_data.get().strip()
                if not data_raw:
                    self.show_toast("Data obbligatoria."); return
                try:
                    data = datetime.datetime.strptime(data_raw, "%d/%m/%Y").strftime("%Y-%m-%d")
                except ValueError:
                    self.show_toast("Data non valida (GG/MM/AAAA)."); return
                record = {
                    "id":           prefill["id"] if prefill else _new_id(),
                    "data":         data,
                    "ora":          e_ora.get().strip(),
                    "cliente_nome": e_cli.get().strip(),
                    "prestazione":  e_pre.get().strip(),
                    "stato":        e_stato.get().strip() or "Confermato",
                    "note":         e_note.get().strip(),
                }
                if prefill:
                    idx = next((i for i,a in enumerate(appuntamenti)
                                if a["id"]==prefill["id"]), None)
                    if idx is not None: appuntamenti[idx] = record
                else:
                    appuntamenti.append(record)
                _save(STUDIO_APPUNTAMENTI, appuntamenti)
                _draw_cal()
                _aggiorna_dettaglio(sel_giorno[0])
                fw.destroy()
                self.show_toast("Appuntamento salvato.")
            fw.bind("<Escape>", lambda e: fw.destroy())
            bot = tk.Frame(fw, bg=self.COLOR_BACKGROUND)
            bot.grid(row=7, column=0, columnspan=4, pady=8)
            _mk_btn(bot, "salva",  "Salva",  _salva)
            _mk_btn(bot, "chiudi", "Chiudi", fw.destroy)
        def _modifica_app():
            sel = tv_det.selection()
            if not sel:
                self.show_toast("Seleziona un appuntamento."); return
            r = next((a for a in appuntamenti if a["id"]==sel[0]), None)
            if r: _form_app(prefill=r)
        def _elimina_app():
            sel = tv_det.selection()
            if not sel:
                self.show_toast("Seleziona un appuntamento."); return
            if self.show_custom_askyesno("Elimina", "Eliminare l'appuntamento?"):
                nonlocal appuntamenti
                appuntamenti = [a for a in appuntamenti if a["id"]!=sel[0]]
                _save(STUDIO_APPUNTAMENTI, appuntamenti)
                _draw_cal()
                _aggiorna_dettaglio(sel_giorno[0])
                self.show_toast("Eliminato.")
        tv_det.bind("<Double-1>", lambda e: _modifica_app())
        nav_bar = tk.Frame(tab_app, bg=self.COLOR_WIDGET_BG,
                           highlightthickness=1,
                           highlightbackground=self.COLOR_HIGHLIGHT)
        nav_bar.pack(fill="x", padx=6, pady=(0,4))
        _mk_btn(nav_bar, "reset",    "◀ Mese prec.", _prev_mese,   self.TEXT_COLOR)
        _mk_btn(nav_bar, "oggi",     "Oggi",          _vai_oggi,    self.COLOR_HIGHLIGHT)
        _mk_btn(nav_bar, "reset",    "Mese succ. ▶",  _next_mese,   self.TEXT_COLOR)
        _mk_btn(nav_bar, "aggiungi", "Nuovo",         lambda: _form_app(), self.COLOR_GREEN)
        _mk_btn(nav_bar, "modifica", "Modifica",      _modifica_app, self.COLOR_HIGHLIGHT)
        _mk_btn(nav_bar, "delete",   "Elimina",       _elimina_app,  self.COLOR_RED)
        cal_cv.after(100, _draw_cal)
    def _build_prestazioni():
        for w in tab_pre.winfo_children(): w.destroy()
        cols   = ["Nome", "Categoria", "Prezzo €", "Durata (min)", "IVA %", "Note"]
        widths = [200, 130, 80, 100, 60, 260]
        tv = _tree(tab_pre, cols, widths)
        def _refresh(sel_id=None):
            tv.delete(*tv.get_children())
            for p in sorted(prestazioni, key=lambda x: x.get("nome","").lower()):
                tv.insert("", "end", iid=p["id"],
                          values=(p.get("nome",""), p.get("categoria",""),
                                  _fmt_eur(p.get("prezzo",0)),
                                  p.get("durata",""), f"{p.get('iva',22)}%",
                                  p.get("note","")))
            if sel_id:
                try: tv.selection_set(sel_id); tv.see(sel_id)
                except Exception: pass
        def _form(prefill=None):
            fw = _form_win("Prestazione", 420)
            fw.withdraw()
            fw.columnconfigure(1, weight=1)
            _titolo(fw, "Modifica" if prefill else "➕ Nuova prestazione")
            W, H = 600, 270
            fw.minsize(W, H)
            win.update_idletasks()
            fx = win.winfo_rootx() + win.winfo_width()  // 2 - W // 2
            fy = win.winfo_rooty() + win.winfo_height() // 2 - H // 2
            fw.geometry(f"{W}x{H}+{max(0,fx)}+{max(0,fy)}")
            fw.deiconify()
            _row(fw,"Nome *",       1); e_nome = _ent(fw,1)
            _row(fw,"Categoria",   2); e_cat  = _ent(fw,2)
            _row(fw,"Prezzo €",    3); e_prez = _ent(fw,3, width=12)
            _row(fw,"Durata (min)",4); e_dur  = _ent(fw,4, width=8)
            _row(fw,"IVA %",       5)
            e_iva = _cbo(fw, 5, ["0","4","10","22"], width=6)
            _row(fw,"Note",        6); e_note = _ent(fw,6)
            def _limit(entry, maxlen):
                vcmd = (fw.register(lambda P: len(P) <= maxlen), "%P")
                entry.config(validate="key", validatecommand=vcmd)
            _limit(e_nome, 30)
            _limit(e_cat,  40)
            _limit(e_prez,  8)
            _limit(e_dur,   4)
            _limit(e_note, 80)
            if prefill:
                for e,k in [(e_nome,"nome"),(e_cat,"categoria"),
                            (e_note,"note")]:
                    e.insert(0, prefill.get(k,""))
                e_prez.insert(0, str(prefill.get("prezzo","")))
                e_dur.insert(0,  str(prefill.get("durata","")))
                e_iva.set(str(prefill.get("iva",22)))
            else:
                e_iva.set("22")
            def _salva():
                nome = e_nome.get().strip()
                if not nome:
                    self.show_toast("Nome obbligatorio."); return
                try:    prezzo = float(e_prez.get().replace(",",".") or 0)
                except: self.show_toast("Prezzo non valido."); return
                try:    durata = int(e_dur.get() or 0)
                except: durata = 0
                try:    iva = int(e_iva.get() or 22)
                except: iva = 22
                record = {
                    "id":        prefill["id"] if prefill else _new_id(),
                    "nome":      nome,
                    "categoria": e_cat.get().strip(),
                    "prezzo":    prezzo,
                    "durata":    durata,
                    "iva":       iva,
                    "note":      e_note.get().strip(),
                }
                if prefill:
                    idx = next((i for i,p in enumerate(prestazioni)
                                if p["id"]==prefill["id"]), None)
                    if idx is not None: prestazioni[idx] = record
                else:
                    prestazioni.append(record)
                _save(STUDIO_PRESTAZIONI, prestazioni)
                _refresh(record["id"])
                fw.destroy()
                self.show_toast("Prestazione salvata.")
            fw.bind("<Escape>", lambda e: fw.destroy())
            bot = tk.Frame(fw, bg=self.COLOR_BACKGROUND)
            bot.grid(row=7, column=0, columnspan=4, pady=8)
            _mk_btn(bot, "salva",  "Salva",  _salva)
            _mk_btn(bot, "chiudi", "Chiudi", fw.destroy)
        def _modifica():
            sel = tv.selection()
            if not sel: self.show_toast("Seleziona una prestazione."); return
            r = next((p for p in prestazioni if p["id"]==sel[0]), None)
            if r: _form(prefill=r)
        def _elimina():
            sel = tv.selection()
            if not sel: self.show_toast("Seleziona una prestazione."); return
            if self.show_custom_askyesno("Elimina", "Eliminare la prestazione selezionata?"):
                nonlocal prestazioni
                prestazioni = [p for p in prestazioni if p["id"]!=sel[0]]
                _save(STUDIO_PRESTAZIONI, prestazioni)
                _refresh()
                self.show_toast("Eliminata.")
        tv.bind("<Double-1>", lambda e: _modifica())
        _btn_bar(tab_pre, [
            ("aggiungi","Nuova",   lambda: _form(), self.COLOR_GREEN),
            ("modifica","Modifica",_modifica,       self.COLOR_HIGHLIGHT),
            ("delete",  "Elimina", _elimina,        self.COLOR_RED),
        ])
        _refresh()
    def _build_fatture():
        for w in tab_fat.winfo_children(): w.destroy()
        cols   = ["N°","Tipo","Data","Cliente","Imponibile €","IVA €","Totale €","Stato"]
        widths = [55, 85, 90, 170, 100, 80, 100, 90]
        tv = _tree(tab_fat, cols, widths)
        def _next_num(tipo):
            anno = datetime.date.today().year
            filtrati = [f for f in fatture if f.get("tipo_doc","Fattura") == tipo]
            if not filtrati: return f"001/{anno}"
            try:
                nums = [int(f.get("numero","0").split("/")[0]) for f in filtrati]
                return f"{max(nums)+1:03d}/{anno}"
            except Exception:
                return f"{len(filtrati)+1:03d}/{anno}"
        def _totali_doc(righe):
            imponibile = sum(r.get("qty",1)*r.get("prezzo",0) for r in righe)
            iva_tot    = sum(r.get("qty",1)*r.get("prezzo",0)*r.get("iva",22)/100
                             for r in righe)
            return imponibile, iva_tot, imponibile+iva_tot
        def _refresh(sel_id=None):
            tv.delete(*tv.get_children())
            for f in sorted(fatture, key=lambda x: x.get("data",""), reverse=True):
                imp, iva_t, tot = _totali_doc(f.get("righe",[]))
                stato = f.get("stato","Bozza")
                tag   = "verde" if stato=="Pagata" else \
                        ("rosso" if stato in ("Scaduta","Annullata") else "")
                try: df = datetime.date.fromisoformat(f["data"]).strftime("%d/%m/%Y")
                except: df = f.get("data","")
                tv.insert("", "end", iid=f["id"], tags=(tag,),
                          values=(f.get("numero",""), f.get("tipo_doc","Fattura"),
                                  df, f.get("cliente_nome",""),
                                  _fmt_eur(imp), _fmt_eur(iva_t),
                                  _fmt_eur(tot), stato))
            tv.tag_configure("verde", foreground=self.COLOR_GREEN)
            tv.tag_configure("rosso", foreground=self.COLOR_RED)
            if sel_id:
                try: tv.selection_set(sel_id); tv.see(sel_id)
                except Exception: pass
        def _form(prefill=None):
            fw = _form_win("Fattura / Preventivo", 1200, 600)
            fw.withdraw()
            fw.resizable(True, True)
            fw.minsize(1200, 600)
            w_width, w_height = 1200, 600
            s_width = fw.winfo_screenwidth()
            s_height = fw.winfo_screenheight()
            x = (s_width // 2) - (w_width // 2)
            y = (s_height // 2) - (w_height // 2)
            fw.geometry(f"{w_width}x{w_height}+{x}+{y}")
            fw.deiconify() 
            fw.columnconfigure(1, weight=1)
            fw.columnconfigure(3, weight=1)
            fw.bind("<Escape>", lambda e: fw.destroy())
            _titolo(fw, "Modifica documento" if prefill else "➕ Nuovo documento")
            _row(fw,"Tipo doc",1,0)
            tipo_var = tk.StringVar()
            e_tipo = ttk.Combobox(fw, textvariable=tipo_var,
                                                      values=["Fattura","Preventivo","Nota Credito"],
                                                      width=14, state="readonly",
                                                      style="Border.TCombobox")
            e_tipo.grid(row=1, column=1, sticky="w", padx=10, pady=3)
            _row(fw,"Numero",1,2)
            e_num = _ent(fw,1,col=3,width=12)
            _row(fw,"Data (GG/MM/AAAA)",2,0)
            frm_dat = tk.Frame(fw, bg=self.COLOR_WIDGET_BG)
            frm_dat.grid(row=2, column=1, sticky="w", padx=10, pady=3)
            e_dat = ttk.Entry(frm_dat, width=12)
            e_dat.pack(side="left")
            _mk_cal_btn(frm_dat, e_dat)
            _row(fw,"Scadenza (GG/MM/AAAA)",2,2)
            frm_sca = tk.Frame(fw, bg=self.COLOR_WIDGET_BG)
            frm_sca.grid(row=2, column=3, sticky="w", padx=10, pady=3)
            e_sca = ttk.Entry(frm_sca, width=12)
            e_sca.pack(side="left")
            _mk_cal_btn(frm_sca, e_sca)
            _row(fw,"Cliente",3,0)
            e_cli = ttk.Combobox(fw, values=_nomi_clienti(),
                                                     width=34, state="readonly",
                                                     style="Border.TCombobox")
            e_cli.grid(row=3, column=1, columnspan=3, sticky="w", padx=10, pady=3)
            _row(fw,"Stato",4,0)
            e_stato = ttk.Combobox(fw,
                    values=["Bozza","Emessa","Pagata","Scaduta","Annullata"],
                    width=12, state="readonly", style="Border.TCombobox")
            e_stato.grid(row=4, column=1, sticky="w", padx=10, pady=3)
            _row(fw,"Note",4,2)
            e_note = _ent(fw,4,col=3,width=22)
            tk.Frame(fw, bg=self.COLOR_HIGHLIGHT, height=1).grid(
                    row=5, column=0, columnspan=4, sticky="ew", padx=10, pady=6)
            tk.Label(fw, text="Righe documento",
                             bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                             font=("Arial",9,"bold")).grid(
                    row=6, column=0, columnspan=4, sticky="w", padx=10)
            rig_outer = tk.Frame(fw, bg=self.COLOR_WIDGET_BG)
            rig_outer.grid(row=7, column=0, columnspan=4, sticky="nsew", padx=10, pady=4)
            fw.rowconfigure(7, weight=1)
            rig_canvas = tk.Canvas(rig_outer, bg=self.COLOR_WIDGET_BG, highlightthickness=0, height=200)
            vsb_r = ttk.Scrollbar(rig_outer, orient="vertical", command=rig_canvas.yview)
            rig_canvas.configure(yscrollcommand=vsb_r.set)
            vsb_r.pack(side="right", fill="y")
            rig_canvas.pack(side="left", fill="both", expand=True)
            rig_frame = tk.Frame(rig_canvas, bg=self.COLOR_WIDGET_BG)
            rig_canvas.create_window((0,0), window=rig_frame, anchor="nw")
            def _upd_scroll(e=None):
                    rig_canvas.configure(scrollregion=rig_canvas.bbox("all"))
            rig_frame.bind("<Configure>", _upd_scroll)
            headers = [("Descrizione",200), ("Qtà",50), ("Prezzo €",80), ("IVA %",60), ("Subtot. €",80), ("",24)]
            for ci, (hdr, cw_h) in enumerate(headers):
                    tk.Label(rig_frame, text=hdr, bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HIGHLIGHT,
                                     font=("Arial",8,"bold"), width=cw_h//8).grid(row=0,column=ci,padx=2)
            righe_vars = []
            def _upd_subtot(dv, qv, pv, iv, sv):
                    try:
                            q = float(qv.get().replace(",",".") or 0)
                            p = float(pv.get().replace(",",".") or 0)
                            i = float(iv.get() or 0)
                            sv.set(f"{q*p*(1+i/100):.2f}")
                    except Exception:
                            sv.set("0.00")
            def _add_riga(desc="", qty=1, prezzo=0.0, iva=22):
                r = len(righe_vars) + 1
                rig_frame.columnconfigure(0, weight=1)
                dv = tk.StringVar(value=str(desc))
                qv = tk.StringVar(value=str(qty))
                pv = tk.StringVar(value=str(prezzo))
                iv = tk.StringVar(value=str(iva))
                sv = tk.StringVar(value="0.00")
                for var in (dv, qv, pv, iv):
                    var.trace_add("write", lambda *_, d=dv,q=qv,p=pv,i=iv,s=sv: _upd_subtot(d,q,p,i,s))
                e_desc = ttk.Entry(rig_frame, textvariable=dv, width=80)
                e_desc.grid(row=r, column=0, padx=2, pady=1, sticky="ew")
                ttk.Entry(rig_frame, textvariable=qv, width=6).grid(row=r, column=1, padx=2, pady=1)
                ttk.Entry(rig_frame, textvariable=pv, width=12).grid(row=r, column=2, padx=2, pady=1)
                cb_i = ttk.Combobox(rig_frame, textvariable=iv, values=["0","4","10","22"],
                                    width=5, state="readonly", style="Border.TCombobox")
                cb_i.grid(row=r, column=3, padx=2, pady=1)
                ttk.Entry(rig_frame, textvariable=sv, width=12, state="readonly").grid(row=r, column=4, padx=2, pady=1)
                img_d = self.icone_gui.get("delete")
                lbl_d = ttk.Label(rig_frame, image=img_d, cursor="hand2", background=self.COLOR_WIDGET_BG)
                lbl_d.grid(row=r, column=5, padx=2, pady=1)
                rv = (dv, qv, pv, iv)
                righe_vars.append(rv)
                _upd_subtot(dv, qv, pv, iv, sv)
                def _rimuovi():
                    if rv in righe_vars: righe_vars.remove(rv)
                    for widget in rig_frame.grid_slaves(row=r):
                        widget.destroy()
                lbl_d.bind("<Button-1>", lambda e: _rimuovi())
                _upd_subtot(dv, qv, pv, iv, sv)
                _ac_popup = [None]
                def _chiudi_ac():
                    if _ac_popup[0] and _ac_popup[0].winfo_exists():
                        _ac_popup[0].destroy()
                    _ac_popup[0] = None
                def _autocomplete(*_, entry=e_desc, dvar=dv, pvar=pv, ivar=iv):
                    _chiudi_ac()
                    testo = dvar.get().strip().lower()
                    if len(testo) < 2:
                        return
                    catalogo = []
                    for m in magazzino:
                        catalogo.append({"nome": m.get("nome",""), "prezzo": m.get("prezzo_unit",0.0), "iva": 22})
                    for p in prestazioni:
                        catalogo.append({"nome": p.get("nome",""), "prezzo": p.get("prezzo",0.0), "iva": p.get("iva",22)})
                    risultati = [c for c in catalogo if testo in c["nome"].lower()]
                    if not risultati:
                        return
                    pop_ac = tk.Toplevel(fw)
                    _ac_popup[0] = pop_ac
                    pop_ac.overrideredirect(True)
                    pop_ac.configure(bg=self.COLOR_WIDGET_BG)
                    ex = entry.winfo_rootx()
                    ey = entry.winfo_rooty() + entry.winfo_height()
                    pop_ac.geometry(f"+{ex}+{ey}")
                    lb = tk.Listbox(pop_ac, bg=self.COLOR_WIDGET_BG, fg=self.COLOR_TEXT,
                                    selectbackground=self.COLOR_HIGHLIGHT, font=("Arial",9),
                                    relief="flat", bd=1, width=50, height=min(6, len(risultati)))
                    lb.pack()
                    for c in risultati:
                        lb.insert("end", f"{c['nome']}  —  {c['prezzo']:.2f} €")
                    def _scegli(evt):
                        idx = lb.curselection()
                        if not idx:
                            return
                        sel = risultati[idx[0]]
                        dvar.set(sel["nome"])
                        pvar.set(f"{sel['prezzo']:.2f}")
                        ivar.set(str(sel["iva"]))
                        _chiudi_ac()
                        entry.focus_set()
                    def _click_fuori(e):
                        if not _ac_popup[0] or not _ac_popup[0].winfo_exists():
                            fw.unbind("<ButtonPress-1>")
                            return
                        wx, wy = lb.winfo_rootx(), lb.winfo_rooty()
                        if not (wx <= e.x_root <= wx + lb.winfo_width() and
                                wy <= e.y_root <= wy + lb.winfo_height()):
                            _chiudi_ac()
                            fw.unbind("<ButtonPress-1>")
                    lb.bind("<Motion>", lambda e: lb.selection_clear(0, "end") or lb.selection_set(lb.nearest(e.y)))
                    lb.bind("<ButtonRelease-1>", _scegli)
                    lb.bind("<Return>", _scegli)
                    lb.bind("<Escape>", lambda e: _chiudi_ac())
                    entry.bind("<Escape>", lambda e: _chiudi_ac(), add=True)
                    fw.bind("<ButtonPress-1>", _click_fuori, add=True)
                dv.trace_add("write", _autocomplete)
                def _rimuovi():
                        if rv in righe_vars: righe_vars.remove(rv)
                        for widget in rig_frame.grid_slaves(row=r):
                                widget.destroy()
                lbl_d.bind("<Button-1>", lambda e: _rimuovi())
                _upd_subtot(dv, qv, pv, iv, sv)
            def _scegli_da_magazzino():
                pop = tk.Toplevel(fw, bg=self.COLOR_TOPLEVEL)
                pop.withdraw()
                pop.title("Seleziona Prodotto o Prestazione")
                pop.transient(fw)
                pop.resizable(False, False)
                W, H = 800, 550
                pop.update_idletasks()
                fx = fw.winfo_rootx() + fw.winfo_width() // 2 - W // 2
                fy = fw.winfo_rooty() + fw.winfo_height() // 2 - H // 2
                pop.geometry(f"{W}x{H}+{max(0, fx)}+{max(0, fy)}")
                pop.deiconify()
                tk.Label(pop, text="Doppio click per inserire", bg=self.COLOR_TOPLEVEL, fg=self.COLOR_HIGHLIGHT, font=("Arial",8)).pack(pady=5)
                nb_pop = ttk.Notebook(pop)
                nb_pop.pack(fill="both", expand=True, padx=10, pady=5)
                f_prod = tk.Frame(nb_pop, bg=self.COLOR_BACKGROUND)
                nb_pop.add(f_prod, text=" Prodotti ")
                tree_p = ttk.Treeview(f_prod, columns=("Nome", "Prezzo", "Giacenza"), show="headings")
                for c in ("Nome", "Prezzo", "Giacenza"):
                    tree_p.heading(c, text=c, command=lambda _c=c: self.treeview_sort_column(tree_p, _c, False))
                    tree_p.column(c, width=100)
                tree_p.column("Nome", width=350)
                tree_p.pack(fill="both", expand=True)
                for m in sorted(magazzino, key=lambda x: x.get("nome","").lower()):
                    tree_p.insert("", "end", iid=m.get("id"), values=(
                        m.get("nome",""), 
                        f"{m.get('prezzo_unit',0):.2f} €", 
                        f"{m.get('quantita',0)} {m.get('unita','pz')}"
                    ))
                f_pre = tk.Frame(nb_pop, bg=self.COLOR_BACKGROUND)
                nb_pop.add(f_pre, text=" Prestazioni ")
                tree_s = ttk.Treeview(f_pre, columns=("Nome", "Prezzo", "IVA"), show="headings")
                for c in ("Nome", "Prezzo", "IVA"):
                    tree_s.heading(c, text=c, command=lambda _c=c: self.treeview_sort_column(tree_s, _c, False))
                    tree_s.column(c, width=100)
                tree_s.column("Nome", width=350)
                tree_s.pack(fill="both", expand=True)
                for p in sorted(prestazioni, key=lambda x: x.get("nome","").lower()):
                    tree_s.insert("", "end", iid=p.get("id"), values=(
                        p.get("nome",""), 
                        f"{p.get('prezzo',0):.2f} €", 
                        f"{p.get('iva',22)}%"
                    ))
                def _conferma(event):
                    tree = event.widget
                    sel = tree.selection()
                    if not sel: return
                    v = tree.item(sel[0], "values")
                    p_pulito = v[1].replace(" €","").replace(",","")
                    i_pulito = v[2].replace("%","") if len(v) > 2 and "%" in v[2] else "22"
                    _add_riga(desc=v[0], prezzo=float(p_pulito), iva=int(i_pulito))
                    pop.destroy()
                tree_p.bind("<Double-1>", _conferma)
                tree_s.bind("<Double-1>", _conferma)
                def _conferma_sel(event):
                    tree = event.widget
                    sel = tree.selection()
                    if not sel: return
                    item_id = sel[0]
                    prod = next((x for x in magazzino if str(x.get("id")) == str(item_id)), None)
                    if prod:
                        _add_riga(desc=prod.get("nome"), prezzo=prod.get("prezzo_unit", 0.0))
                    else:
                        presta = next((x for x in prestazioni if str(x.get("id")) == str(item_id)), None)
                        if presta:
                            _add_riga(desc=presta.get("nome"), prezzo=presta.get("prezzo", 0.0), iva=presta.get("iva", 22))
                    pop.destroy()
                tree_p.bind("<Double-1>", _conferma_sel)
                tree_s.bind("<Double-1>", _conferma_sel)
                l_close = ttk.Label(pop, text=" Chiudi ", image=self.icone_gui.get("chiudi"), compound="left", background=self.COLOR_WIDGET_BG, cursor="hand2", font=("Arial",9,"bold"), padding=(10,4))
                l_close.pack(pady=10); l_close.bind("<Button-1>", lambda e: pop.destroy())
            righe_src = (prefill or {}).get("righe", [{"desc":"","qty":1,"prezzo":0.0,"iva":22}])
            for rig in righe_src:
                _add_riga(rig.get("desc",""), rig.get("qty",1), rig.get("prezzo",0.0), rig.get("iva",22))
            tipo_doc = (prefill or {}).get("tipo_doc","Fattura")
            tipo_var.set(tipo_doc)
            e_num.insert(0, (prefill or {}).get("numero", _next_num(tipo_doc)))
            def _to_dmy(s):
                if s and len(s)==10 and "-" in s: return s[8:]+"/"+s[5:7]+"/"+s[:4]
                return s or ""
            e_dat.insert(0, _to_dmy((prefill or {}).get("data", datetime.datetime.now().strftime("%Y-%m-%d"))))
            e_sca.insert(0, _to_dmy((prefill or {}).get("scadenza","")))
            e_cli.set((prefill or {}).get("cliente_nome",""))
            e_stato.set((prefill or {}).get("stato","Bozza"))
            e_note.insert(0,(prefill or {}).get("note",""))
            e_tipo.bind("<<ComboboxSelected>>", lambda e: (e_num.delete(0,"end"), e_num.insert(0, _next_num(tipo_var.get()))) if not prefill else None)
            bot = tk.Frame(fw, bg=self.COLOR_WIDGET_BG)
            bot.grid(row=8, column=0, columnspan=4, pady=6)
            b_add = ttk.Label(bot, text=" Riga", image=self.icone_gui.get("aggiungi"), compound="left", background=self.COLOR_WIDGET_BG, cursor="hand2", font=("Arial",9,"bold"), padding=(6,3))
            b_add.pack(side="left", padx=8); b_add.bind("<Button-1>", lambda e: _add_riga())
            img_mag = self.icone_gui.get("studio") or self.icone_gui.get("box")
            b_mag = ttk.Label(bot, text=" Magazzino", image=img_mag, compound="left", background=self.COLOR_WIDGET_BG, cursor="hand2", font=("Arial", 9, "bold"), padding=(6, 3))
            b_mag.pack(side="left", padx=8); b_mag.bind("<Button-1>", lambda e: _scegli_da_magazzino())
            def _salva():
                data_str = e_dat.get().strip()
                if not data_str:
                    self.show_toast("Data obbligatoria."); return
                try:
                    datetime.datetime.strptime(data_str, "%d/%m/%Y")
                except ValueError:
                    self.show_toast("Data non valida. Usa GG/MM/AAAA."); return
                sca_str = e_sca.get().strip()
                if sca_str:
                    try:
                        datetime.datetime.strptime(sca_str, "%d/%m/%Y")
                    except ValueError:
                        self.show_toast("Scadenza non valida. Usa GG/MM/AAAA."); return
                righe = []
                for dv, qv, pv, iv in righe_vars:
                    desc = dv.get().strip()
                    if not desc: continue
                    try: q = float(qv.get().replace(",", ".") or 1)
                    except: q = 1
                    try: p = float(pv.get().replace(",", ".") or 0)
                    except: p = 0
                    try: i = int(iv.get() or 22)
                    except: i = 22
                    righe.append({"desc": desc, "qty": q, "prezzo": p, "iva": i})
                    if not prefill:
                        for prod in magazzino:
                            if prod.get("nome", "").strip().lower() == desc.lower():
                                try:
                                    attuale = float(prod.get("quantita", 0))
                                    prod["quantita"] = attuale - q
                                except: pass
                                break
                if not prefill:
                    _save(STUDIO_MAGAZZINO, magazzino)
                    if hasattr(self, '_refresh_magazzino'): self._refresh_magazzino()
                def _p(s):
                    try: return datetime.datetime.strptime(s.strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
                    except: return s.strip()
                record = {
                    "id":           prefill["id"] if prefill else _new_id(),
                    "tipo_doc":     tipo_var.get() or "Fattura",
                    "numero":       e_num.get().strip() or _next_num(tipo_var.get()),
                    "data":         _p(e_dat.get()),
                    "scadenza":     _p(e_sca.get()) if e_sca.get().strip() else "",
                    "cliente_nome": e_cli.get().strip(),
                    "righe":        righe,
                    "stato":        e_stato.get().strip() or "Bozza",
                    "note":         e_note.get().strip(),
                }
                if prefill:
                    idx = next((i for i, f in enumerate(fatture) if f["id"] == prefill["id"]), None)
                    if idx is not None: fatture[idx] = record
                else:
                    fatture.append(record)
                _save(STUDIO_FATTURE, fatture)
                _refresh(record["id"])
                fw.destroy()
                self.show_toast("Documento salvato.")
            b_salva = ttk.Label(bot, text=" Salva", image=self.icone_gui.get("salva"), compound="left", background=self.COLOR_WIDGET_BG, cursor="hand2", font=("Arial",9,"bold"), padding=(6,3))
            b_salva.pack(side="left", padx=8); b_salva.bind("<Button-1>", lambda e: _salva())
            b_close_form = ttk.Label(bot, text=" Chiudi", image=self.icone_gui.get("chiudi"), compound="left", background=self.COLOR_WIDGET_BG, cursor="hand2", font=("Arial",9,"bold"), padding=(6,3))
            b_close_form.pack(side="left", padx=8)
            b_close_form.bind("<Button-1>", lambda e: fw.destroy())
        def _genera_pdf(doc=None):
            os.makedirs(EXPORT_FATTURE_DIR, exist_ok=True)
            if doc is None:
                sel = tv.selection()
                if not sel:
                    self.show_toast("Seleziona un documento."); return
                doc = next((f for f in fatture if f["id"]==sel[0]), None)
                if not doc: return
            nome_cli = doc.get("cliente_nome","")
            cli_rec  = next((c for c in clienti
                             if f"{c.get('nome','')} {c.get('cognome','')}".strip() == nome_cli
                             or c.get("azienda","") == nome_cli), {})
            try:
                import fitz
            except ImportError:
                self.show_custom_warning("Errore",
                    "PyMuPDF (fitz) non installato.\n"
                    "Installa con: pip install pymupdf"); return
            path_out = filedialog.asksaveasfilename(
                parent=win,
                initialdir=EXPORT_FATTURE_DIR,
                defaultextension=".pdf",
                filetypes=[("PDF","*.pdf")],
                initialfile=f"{doc.get('tipo_doc','Doc')}_{doc.get('numero','').replace('/','_')}.pdf",
                confirmoverwrite=False
            )
            if not path_out: return
            if os.path.exists(path_out):
                if not self.show_custom_askyesno(
                    "Sovrascrivere file?",
                    f"Il file '{os.path.basename(path_out)}' \nesiste già. Vuoi sovrascriverlo?"
                ):
                    return
            try:
                W, H   = 595, 842
                MARG   = 45
                COL_R  = W - MARG
                BLU    = (0.10, 0.22, 0.45)
                BLU_L  = (0.18, 0.38, 0.68)
                ACCENT = (0.00, 0.55, 0.80)
                GREY_L = (0.95, 0.96, 0.97)
                GREY_M = (0.80, 0.82, 0.85)
                GREY_D = (0.45, 0.45, 0.48)
                BLACK  = (0.10, 0.10, 0.12)
                WHITE  = (1.00, 1.00, 1.00)
                RED    = (0.72, 0.10, 0.10)
                GREEN  = (0.08, 0.50, 0.22)
                ORANGE = (0.80, 0.45, 0.00)
                pdoc = fitz.open()
                def _new_page():
                    pg = pdoc.new_page(width=W, height=H)
                    pg.draw_rect(fitz.Rect(0, 0, 4, H),
                                 color=None, fill=ACCENT, width=0)
                    return pg
                page = _new_page()
                def _txt(pg, x, y, testo, size=9, color=BLACK,
                         bold=False, align="left", max_w=None):
                    fn = "Helvetica-Bold" if bold else "Helvetica"
                    tw = fitz.get_text_length(str(testo), fontname=fn, fontsize=size)
                    if align == "right":
                        x = x - tw
                    elif align == "center" and max_w:
                        x = x + (max_w - tw) / 2
                    pg.insert_text((x, y), str(testo),
                                   fontname=fn, fontsize=size, color=color)
                def _rect(pg, x0, y0, x1, y1, fill=None, stroke=None, lw=0.5):
                    pg.draw_rect(fitz.Rect(x0, y0, x1, y1),
                                 color=stroke, fill=fill, width=lw)
                def _line(pg, x0, y0, x1, y1, color=GREY_M, lw=0.5):
                    pg.draw_line((x0,y0),(x1,y1), color=color, width=lw)
                def _fmt(v):
                    return f"{v:,.2f}".replace(",","X").replace(".",",").replace("X",".")
                _rect(page, 0, 0, W, 80, fill=BLU)
                _rect(page, 0, 80, W, 84, fill=ACCENT)
                logo_path = emittente.get("logo_path","")
                logo_w = 0
                if logo_path and os.path.isfile(logo_path):
                    try:
                        lr = fitz.Rect(COL_R - 110, 8, COL_R - 4, 74)
                        page.insert_image(lr, filename=logo_path, keep_proportion=True)
                        logo_w = 120
                    except Exception:
                        pass
                tipo_doc = doc.get("tipo_doc","Fattura").upper()
                _txt(page, MARG, 35, tipo_doc, size=22, color=WHITE, bold=True)
                num = doc.get("numero","")
                _txt(page, MARG, 55, f"N°  {num}", size=12, color=ACCENT, bold=True)
                x_date = COL_R - logo_w - 170
                try:
                    df = datetime.date.fromisoformat(doc["data"]).strftime("%d/%m/%Y")
                except Exception:
                    df = doc.get("data","")
                _txt(page, x_date, 30, "Data emissione", size=7, color=GREY_M)
                _txt(page, x_date, 44, df, size=11, color=WHITE, bold=True)
                sc = doc.get("scadenza","")
                if sc:
                    try:
                        sc = datetime.date.fromisoformat(sc).strftime("%d/%m/%Y")
                    except Exception:
                        pass
                    _txt(page, x_date, 58, "Scadenza", size=7, color=GREY_M)
                    _txt(page, x_date, 70, sc, size=10, color=ORANGE, bold=True)
                y = 96
                mid = W // 2 + 6
                box_h = 76
                _rect(page, MARG, y, mid-6, y+box_h,
                      fill=GREY_L, stroke=GREY_M, lw=0.8)
                _txt(page, MARG+8, y+12, "EMITTENTE", size=7,
                     color=BLU_L, bold=True)
                _line(page, MARG+8, y+16, mid-14, y+16, color=GREY_M, lw=0.5)
                emi_lines = [
                    (emittente.get("ragione_sociale",""), True, 9, BLACK),
                    (emittente.get("indirizzo",""),       False, 8, GREY_D),
                    (f"P.IVA / CF: {emittente.get('cf_piva','')}", False, 8, GREY_D),
                    (" | ".join(filter(None,[
                        emittente.get("telefono",""),
                        emittente.get("email","")])),
                     False, 7, GREY_D),
                ]
                ye = y + 27
                for (txt, bold, sz, col) in emi_lines:
                    if txt and txt not in ("P.IVA / CF: ",""):
                        _txt(page, MARG+8, ye, txt, size=sz, color=col, bold=bold)
                        ye += sz + 3
                _rect(page, mid+6, y, COL_R, y+box_h,
                      fill=GREY_L, stroke=GREY_M, lw=0.8)
                _txt(page, mid+14, y+12, "DESTINATARIO", size=7,
                     color=BLU_L, bold=True)
                _line(page, mid+14, y+16, COL_R-8, y+16, color=GREY_M, lw=0.5)
                cli_lines = [
                    (cli_rec.get("azienda","") or nome_cli, True, 9, BLACK),
                    (cli_rec.get("indirizzo",""),           False, 8, GREY_D),
                    (f"P.IVA / CF: {cli_rec.get('cf_piva','')}" if cli_rec.get("cf_piva") else "",
                     False, 8, GREY_D),
                    (cli_rec.get("email","") or cli_rec.get("telefono",""),
                     False, 7, GREY_D),
                ]
                yc = y + 27
                for (txt, bold, sz, col) in cli_lines:
                    if txt and txt not in ("P.IVA / CF: ",""):
                        _txt(page, mid+14, yc, txt, size=sz, color=col, bold=bold)
                        yc += sz + 3
                y = y + box_h + 16
                CX = {
                    "desc_l":  MARG + 4,
                    "qty_r":   MARG + 268,
                    "prez_r":  MARG + 348,
                    "iva_r":   MARG + 400,
                    "imp_r":   COL_R - 4,
                }
                HDR_H = 18
                _rect(page, MARG, y, COL_R, y+HDR_H, fill=BLU)
                _txt(page, CX["desc_l"], y+12, "DESCRIZIONE", size=7.5, color=WHITE, bold=True)
                _txt(page, CX["qty_r"],  y+12, "QTÀ",         size=7.5, color=WHITE, bold=True, align="right")
                _txt(page, CX["prez_r"], y+12, "PREZZO",    size=7.5, color=WHITE, bold=True, align="right")
                _txt(page, CX["iva_r"],  y+12, "IVA %",       size=7.5, color=WHITE, bold=True, align="right")
                _txt(page, CX["imp_r"],  y+12, "IMPORTO",   size=7.5, color=WHITE, bold=True, align="right")
                y += HDR_H
                righe = doc.get("righe",[])
                tot_imponibile = 0.0
                tot_iva_map    = {}
                ROW_H = 15
                for i, rig in enumerate(righe):
                    desc  = rig.get("desc","")
                    qty   = rig.get("qty",1)
                    prez  = float(rig.get("prezzo",0))
                    iva_r = float(rig.get("iva",22))
                    imp   = qty * prez
                    iva_v = imp * iva_r / 100
                    sub   = imp + iva_v
                    tot_imponibile += imp
                    tot_iva_map[iva_r] = tot_iva_map.get(iva_r, 0.0) + iva_v
                    if y + ROW_H > H - 160:
                        page = _new_page()
                        y = MARG
                        _rect(page, MARG, y, COL_R, y+HDR_H, fill=BLU)
                        _txt(page, CX["desc_l"], y+12, "DESCRIZIONE", size=7.5, color=WHITE, bold=True)
                        _txt(page, CX["qty_r"],  y+12, "QTÀ",         size=7.5, color=WHITE, bold=True, align="right")
                        _txt(page, CX["prez_r"], y+12, "PREZZO",    size=7.5, color=WHITE, bold=True, align="right")
                        _txt(page, CX["iva_r"],  y+12, "IVA %",       size=7.5, color=WHITE, bold=True, align="right")
                        _txt(page, CX["imp_r"],  y+12, "IMPORTO",   size=7.5, color=WHITE, bold=True, align="right")
                        y += HDR_H
                    bg = GREY_L if i % 2 == 0 else WHITE
                    _rect(page, MARG, y, COL_R, y+ROW_H, fill=bg)
                    _line(page, MARG, y+ROW_H, COL_R, y+ROW_H, color=GREY_M, lw=0.3)
                    desc_s = (desc[:52]+"…") if len(desc)>52 else desc
                    _txt(page, CX["desc_l"], y+10, desc_s,           size=8)
                    _txt(page, CX["qty_r"],  y+10, str(qty),          size=8, align="right")
                    _txt(page, CX["prez_r"], y+10, f"{prez:.2f}",     size=8, align="right")
                    _txt(page, CX["iva_r"],  y+10, f"{iva_r:.0f}%",   size=8, align="right")
                    _txt(page, CX["imp_r"],  y+10, f"{sub:.2f}",      size=8, align="right")
                    y += ROW_H
                y += 10
                _line(page, MARG, y, COL_R, y, color=BLU_L, lw=1)
                y += 12
                tot_iva_tot = sum(tot_iva_map.values())
                tot_totale  = tot_imponibile + tot_iva_tot
                BOX_X  = COL_R - 190
                BOX_LW = 190
                def _riepilogo_row(pg, yy, label, valore, highlight=False):
                    if highlight:
                        _rect(pg, BOX_X-4, yy-2, COL_R, yy+13, fill=BLU)
                        _txt(pg, BOX_X+4,    yy+9, label,        size=9, color=WHITE, bold=True)
                        _txt(pg, COL_R-4,    yy+9, _fmt(valore), size=9, color=WHITE, bold=True, align="right")
                    else:
                        _txt(pg, BOX_X+4,    yy+9, label,        size=8, color=GREY_D)
                        _txt(pg, COL_R-4,    yy+9, _fmt(valore), size=8, color=BLACK, align="right")
                        _line(pg, BOX_X, yy+14, COL_R, yy+14, color=GREY_M, lw=0.3)

                _riepilogo_row(page, y, "Imponibile", tot_imponibile)
                y += 16
                for al, v in sorted(tot_iva_map.items()):
                    _riepilogo_row(page, y, f"IVA {al:.0f}%", v)
                    y += 16
                y += 2
                _riepilogo_row(page, y, "TOTALE DOCUMENTO", tot_totale, highlight=True)
                y += 22
                stato = doc.get("stato","")
                if stato:
                    col_s = GREEN if stato=="Pagata" else \
                            RED   if stato in ("Scaduta","Annullata") else ORANGE
                    badge_w = 90
                    _rect(page, MARG, y-1, MARG+badge_w, y+13,
                          fill=col_s)
                    _txt(page, MARG+4, y+9, f"● {stato.upper()}",
                         size=8, color=WHITE, bold=True)
                    y += 20
                note = doc.get("note","")
                if note:
                    y += 4
                    _rect(page, MARG, y, COL_R, y+10, fill=GREY_L)
                    _txt(page, MARG+4, y+8, "NOTE", size=7, color=BLU_L, bold=True)
                    y += 14
                    parole = note.split()
                    riga_n = ""
                    for p in parole:
                        if len(riga_n) + len(p) + 1 > 95:
                            _txt(page, MARG+4, y, riga_n, size=8, color=GREY_D)
                            y += 12; riga_n = p
                        else:
                            riga_n += (" "+p) if riga_n else p
                    if riga_n:
                        _txt(page, MARG+4, y, riga_n, size=8, color=GREY_D)
                        y += 12
                iban = emittente.get("iban","")
                if iban:
                    y += 8
                    _line(page, MARG, y, COL_R, y, color=GREY_M, lw=0.5)
                    y += 10
                    _txt(page, MARG, y, "COORDINATE BANCARIE", size=7,
                         color=BLU_L, bold=True)
                    y += 11
                    _txt(page, MARG, y,
                         f"IBAN: {iban}  —  Intestato a: {emittente.get('ragione_sociale','')}",
                         size=8, color=GREY_D)
                n_pages = pdoc.page_count
                for pi in range(n_pages):
                    pg = pdoc[pi]
                    _rect(pg, 0, H-32, W, H, fill=BLU)
                    _line(pg, 0, H-32, W, H-32, color=ACCENT, lw=2)
                    rs = emittente.get("ragione_sociale","")
                    cf = emittente.get("cf_piva","")
                    footer_l = " | ".join(filter(None, [rs, f"P.IVA {cf}" if cf else ""]))
                    _txt(pg, MARG, H-14, footer_l, size=7, color=GREY_M)
                    oggi_str = datetime.date.today().strftime("%d/%m/%Y")
                    pg_label = f"Pag. {pi+1}/{n_pages}  —  Stampato il {oggi_str}"
                    _txt(pg, COL_R-4, H-14, pg_label, size=7, color=GREY_M, align="right")
                pdoc.save(path_out)
                pdoc.close()
                self.show_toast("PDF salvato.")
                try:
                    if sys.platform == "win32":
                        os.startfile(path_out)
                    elif sys.platform == "darwin":
                        subprocess.Popen(["open", path_out])
                    else:
                        subprocess.Popen(["xdg-open", path_out])
                except Exception:
                    pass
            except Exception as e:
                self.show_custom_warning("Errore PDF", str(e))
        def _stampa_diretta():
            sel = tv.selection()
            if not sel:
                self.show_toast("Seleziona un documento."); return
            doc = next((f for f in fatture if f["id"]==sel[0]), None)
            if not doc: return
            import tempfile
            tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
            tmp.close()
            _genera_pdf_path(doc, tmp.name)
        def _genera_pdf_path(doc, path_out):
            try:
                import fitz
                sel_orig = tv.selection()
                _genera_pdf(doc=doc)
            except Exception:
                pass
        def _modifica():
            sel = tv.selection()
            if not sel: self.show_toast("Seleziona un documento."); return
            r = next((f for f in fatture if f["id"]==sel[0]), None)
            if r: _form(prefill=r)
        def _elimina():
            sel = tv.selection()
            if not sel: self.show_toast("Seleziona un documento."); return
            if self.show_custom_askyesno("Elimina", "Eliminare il documento selezionato?"):
                nonlocal fatture
                fatture = [f for f in fatture if f["id"]!=sel[0]]
                _save(STUDIO_FATTURE, fatture)
                _refresh()
                self.show_toast("Eliminato.")
        tv.bind("<Double-1>", lambda e: _modifica())
        _btn_bar(tab_fat, [
            ("aggiungi", "Nuovo",        lambda: _form(),  self.COLOR_GREEN),
            ("modifica", "Modifica",     _modifica,        self.COLOR_HIGHLIGHT),
            ("report",   "Salva PDF",    _genera_pdf,      self.TEXT_COLOR),
            ("stampa",   "Stampa",       lambda: _genera_pdf(), self.TEXT_COLOR),
            ("delete",   "Elimina",      _elimina,         self.COLOR_RED),
            ("link",     "Portale AE",   lambda: webbrowser.open("https://ivaservizi.agenziaentrate.gov.it/portale/"), self.COLOR_HIGHLIGHT),
        ])
        _refresh()
       
    def _build_cassa():
        for w in tab_cas.winfo_children(): w.destroy()
        top = tk.Frame(tab_cas, bg=self.COLOR_BACKGROUND)
        top.pack(fill="x", padx=8, pady=(6,2))
        lbl_saldo = tk.Label(top, text="Saldo: € 0,00",
                             font=("Arial",11,"bold"),
                             bg=self.COLOR_BACKGROUND,
                             fg=self.TEXT_COLOR)
        lbl_saldo.pack(side="left")
        lbl_in  = tk.Label(top, text="", font=("Arial",9),
                           bg=self.COLOR_BACKGROUND,
                           fg=self.COLOR_GREEN)
        lbl_in.pack(side="left", padx=14)
        lbl_out = tk.Label(top, text="", font=("Arial",9),
                           bg=self.COLOR_BACKGROUND,
                           fg=self.COLOR_RED)
        lbl_out.pack(side="left")
        cols   = ["Data","Tipo","Importo €","Categoria","Metodo Pag.","Note"]
        widths = [90, 80, 90, 140, 110, 300]
        tv = _tree(tab_cas, cols, widths)
        def _trasferisci_spesa():
            sel = tv.selection()
            if not sel:
                    self.show_toast("Seleziona un movimento."); return
            mov = next((m for m in cassa if m["id"]==sel[0]), None)
            if not mov: return
            imp  = mov.get("importo", 0.0)
            tipo = mov.get("tipo", "Entrata")
            note = mov.get("note", "") or f"Cassa Studio ({mov.get('metodo','')})"
            try:
                    data_obj = datetime.date.fromisoformat(mov["data"])
            except Exception:
                    data_obj = datetime.date.today()
            tipo_spesa = "Entrata" if tipo == "Entrata" else "Uscita"
            popup = tk.Toplevel(win, bg=self.COLOR_TOPLEVEL)
            popup.title("Aggiungi al DB principale")
            popup.resizable(False, False)
            popup.transient(win)
            popup.withdraw()
            f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL, padx=16, pady=14)
            f.pack(fill="both", expand=True)
            def _lbl(row, testo):
                    tk.Label(f, text=testo, bg=self.COLOR_TOPLEVEL,
                                     fg=self.TEXT_COLOR, anchor="e", width=14
                                     ).grid(row=row, column=0, sticky="e", pady=4, padx=(0,6))
            _lbl(0, "Data:")
            tk.Label(f, text=data_obj.strftime("%d/%m/%Y"),
                             bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR
                             ).grid(row=0, column=1, sticky="w")
            _lbl(1, "Importo:")
            tk.Label(f, text=f"{_fmt_eur(imp)}  ({tipo_spesa})",
                             bg=self.COLOR_TOPLEVEL,
                             fg=self.COLOR_GREEN if tipo_spesa=="Entrata" else self.COLOR_RED,
                             font=("Arial",9,"bold")
                             ).grid(row=1, column=1, sticky="w")
            _lbl(2, "Categoria:")
            cat_var = tk.StringVar()
            cats = sorted(self.categorie, key=lambda c: c.lower())
            cbo = ttk.Combobox(f, textvariable=cat_var, values=cats,
                                               state="readonly", width=22,
                                               style="Border.TCombobox")
            cbo.grid(row=2, column=1, sticky="w", pady=4)
            if cats: cbo.current(0)
            _lbl(3, "Descrizione:")
            desc_var = tk.StringVar(value=note[:30])
            ttk.Entry(f, textvariable=desc_var, width=28
                              ).grid(row=3, column=1, sticky="w", pady=4)
            def _conferma():
                    cat = cat_var.get().strip()
                    if not cat:
                            self.show_toast("Seleziona una categoria."); return
                    desc = desc_var.get().strip() or note
                    if data_obj not in self.spese:
                            self.spese[data_obj] = []
                    self.spese[data_obj].append([cat, desc, imp, tipo_spesa])
                    self.save_db()
                    self.refresh_gui()
                    popup.destroy()
                    self.show_toast("Movimento aggiunto al DB principale.")
            bot = tk.Frame(f, bg=self.COLOR_TOPLEVEL)
            bot.grid(row=4, column=0, columnspan=2, pady=10)
            _mk_btn(bot, "conferma", "Aggiungi", _conferma, fg=self.COLOR_GREEN)
            _mk_btn(bot, "chiudi",   "Annulla",  popup.destroy)
            popup.bind("<Escape>", lambda e: popup.destroy())
            popup.update_idletasks()
            cx = win.winfo_rootx() + (win.winfo_width()  - popup.winfo_reqwidth())  // 2
            cy = win.winfo_rooty() + (win.winfo_height() - popup.winfo_reqheight()) // 2
            popup.geometry(f"+{cx}+{cy}")
            popup.deiconify()
        def _refresh(sel_id=None):
            tv.delete(*tv.get_children())
            saldo = entrate = uscite = 0.0
            for m in sorted(cassa, key=lambda x: x.get("data","")):
                imp  = m.get("importo",0.0)
                tipo = m.get("tipo","Entrata")
                if tipo == "Entrata":
                    saldo += imp; entrate += imp
                else:
                    saldo -= imp; uscite  += imp
                tag = "verde" if tipo=="Entrata" else "rosso"
                try: df = datetime.date.fromisoformat(m["data"]).strftime("%d/%m/%Y")
                except: df = m.get("data","")
                tv.insert("", "end", iid=m["id"], tags=(tag,),
                          values=(df, tipo, _fmt_eur(imp),
                                  m.get("categoria",""),
                                  m.get("metodo",""),
                                  m.get("note","")))
            tv.tag_configure("verde", foreground=self.COLOR_GREEN)
            tv.tag_configure("rosso", foreground=self.COLOR_RED)
            col = self.COLOR_GREEN if saldo>=0 else self.COLOR_RED
            lbl_saldo.config(text=f"Saldo: {_fmt_eur(saldo)}", fg=col)
            lbl_in.config(text=f"↑ Entrate: {_fmt_eur(entrate)}")
            lbl_out.config(text=f"↓ Uscite: {_fmt_eur(uscite)}")
            if sel_id:
                try: tv.selection_set(sel_id); tv.see(sel_id)
                except Exception: pass
        def _form(prefill=None):
            fw = _form_win("Movimento Cassa", 400)
            fw.withdraw()
            fw.columnconfigure(1, weight=1)
            _titolo(fw, "Modifica" if prefill else "➕ Nuovo movimento")
            W, H = 580, 270
            fw.minsize(W, H)
            win.update_idletasks()
            fx = win.winfo_rootx() + win.winfo_width()  // 2 - W // 2
            fy = win.winfo_rooty() + win.winfo_height() // 2 - H // 2
            fw.geometry(f"{W}x{H}+{max(0,fx)}+{max(0,fy)}")
            fw.deiconify()
            _row(fw,"Data (GG/MM/AAAA) *",1)
            frm_d = tk.Frame(fw, bg=self.COLOR_WIDGET_BG)
            frm_d.grid(row=1, column=1, sticky="w", padx=10, pady=3)
            e_data = ttk.Entry(frm_d, width=12)
            e_data.pack(side="left")
            e_data.bind("<Key>", lambda e: "break")
            _mk_cal_btn(frm_d, e_data)
            _row(fw,"Tipo",               2)
            e_tipo = _cbo(fw,2,["Entrata","Uscita"],width=12)
            _row(fw,"Importo €",          3); e_imp  = _ent(fw,3,width=12)
            _row(fw,"Categoria",          4); e_cat  = _ent(fw,4)
            _row(fw,"Metodo Pagamento",   5)
            e_met = _cbo(fw,5,["Contanti","Bonifico","Carta","POS","Assegno","Altro"],width=14)
            _row(fw,"Note",               6); e_note = _ent(fw,6)
            def _limit(entry, maxlen):
                vcmd = (fw.register(lambda P: len(P) <= maxlen), "%P")
                entry.config(validate="key", validatecommand=vcmd)
            _limit(e_imp,   10)
            _limit(e_cat,   40)
            _limit(e_note,  40)
            if prefill:
                d = prefill.get("data","")
                if d and "-" in d: d = d[8:]+"/"+d[5:7]+"/"+d[:4]
                e_data.insert(0, d)
                e_tipo.set(    prefill.get("tipo","Entrata"))
                e_imp.insert(0,str(prefill.get("importo","")))
                e_cat.insert(0,prefill.get("categoria",""))
                e_met.set(    prefill.get("metodo",""))
                e_note.insert(0,prefill.get("note",""))
            else:
                e_data.insert(0, datetime.datetime.now().strftime("%d/%m/%Y"))
                e_tipo.set("Entrata")
            def _salva():
                data_raw = e_data.get().strip()
                if not data_raw: self.show_toast("Data obbligatoria."); return
                try:
                    data = datetime.datetime.strptime(data_raw, "%d/%m/%Y").strftime("%Y-%m-%d")
                except ValueError:
                    self.show_toast("Data non valida (GG/MM/AAAA)."); return
                try: imp = float(e_imp.get().replace(",",".") or 0)
                except: self.show_toast("Importo non valido."); return
                record = {
                    "id":        prefill["id"] if prefill else _new_id(),
                    "data":      data,
                    "tipo":      e_tipo.get().strip() or "Entrata",
                    "importo":   imp,
                    "categoria": e_cat.get().strip(),
                    "metodo":    e_met.get().strip(),
                    "note":      e_note.get().strip(),
                }
                if prefill:
                    idx = next((i for i,m in enumerate(cassa)
                                if m["id"]==prefill["id"]),None)
                    if idx is not None: cassa[idx] = record
                else:
                    cassa.append(record)
                _save(STUDIO_CASSA, cassa)
                _refresh(record["id"])
                fw.destroy()
                self.show_toast("Movimento salvato.")
            fw.bind("<Escape>", lambda e: fw.destroy())
            bot = tk.Frame(fw, bg=self.COLOR_BACKGROUND)
            bot.grid(row=7, column=0, columnspan=4, pady=8)
            _mk_btn(bot, "salva",  "Salva",  _salva)
            _mk_btn(bot, "chiudi", "Chiudi", fw.destroy)
        def _modifica():
            sel = tv.selection()
            if not sel: self.show_toast("Seleziona un movimento."); return
            r = next((m for m in cassa if m["id"]==sel[0]), None)
            if r: _form(prefill=r)
        def _elimina():
            sel = tv.selection()
            if not sel: self.show_toast("Seleziona un movimento."); return
            if self.show_custom_askyesno("Elimina","Eliminare il movimento selezionato?"):
                nonlocal cassa
                cassa = [m for m in cassa if m["id"]!=sel[0]]
                _save(STUDIO_CASSA, cassa)
                _refresh()
                self.show_toast("Eliminato.")
        tv.bind("<Double-1>", lambda e: _modifica())
        _btn_bar(tab_cas, [
            ("aggiungi","Nuovo",   lambda: _form(), self.COLOR_GREEN),
            ("modifica","Modifica",_modifica,       self.COLOR_HIGHLIGHT),
            ("delete",  "Elimina", _elimina,        self.COLOR_RED),
            ("sync",    "→ Esporta",    _trasferisci_spesa,     self.COLOR_ORANGE),
        ])
        _refresh()
    def _build_magazzino():
        for w in tab_mag.winfo_children(): w.destroy()
        cols   = ["Nome","Categoria","Qtà","Unità","Soglia min.","Valore €","Note"]
        widths = [180, 120, 70, 60, 90, 80, 250]
        tv = _tree(tab_mag, cols, widths)
        def _refresh(sel_id=None):
            tv.delete(*tv.get_children())
            for m in sorted(magazzino, key=lambda x: x.get("nome","").lower()):
                qty    = m.get("quantita",0)
                soglia = m.get("soglia",0)
                valore = qty * m.get("prezzo_unit",0.0)
                tag    = "rosso" if qty<=soglia else ""
                tv.insert("", "end", iid=m["id"], tags=(tag,),
                          values=(m.get("nome",""), m.get("categoria",""),
                                  qty, m.get("unita","pz"),
                                  soglia, _fmt_eur(valore) if valore else "",
                                  m.get("note","")))
            tv.tag_configure("rosso", foreground=self.COLOR_RED)
            if sel_id:
                try: tv.selection_set(sel_id); tv.see(sel_id)
                except Exception: pass
        self._refresh_magazzino = _refresh
        _refresh()
        def _form(prefill=None):
            fw = _form_win("Materiale / Prodotto", 420)
            fw.withdraw()
            fw.columnconfigure(1, weight=1)
            _titolo(fw, "Modifica" if prefill else "➕ Nuovo materiale")
            W, H = 580, 300
            fw.minsize(580, 300)
            win.update_idletasks()
            fx = win.winfo_rootx() + win.winfo_width()  // 2 - W // 2
            fy = win.winfo_rooty() + win.winfo_height() // 2 - H // 2
            fw.geometry(f"{W}x{H}+{max(0,fx)}+{max(0,fy)}")
            fw.deiconify()
            _titolo(fw,"Modifica" if prefill else "➕ Nuovo materiale")
            _row(fw,"Nome *",        1); e_nome = _ent(fw,1)
            _row(fw,"Categoria",    2); e_cat  = _ent(fw,2)
            _row(fw,"Quantità",     3); e_qty  = _ent(fw,3,width=10)
            _row(fw,"Unità",        4)
            e_unit = _cbo(fw,4,["pz","kg","lt","m","g","ml","m²","mt"],width=8)
            _row(fw,"Soglia minima",5); e_sog  = _ent(fw,5,width=10)
            _row(fw,"Prezzo unit. €",6); e_pu  = _ent(fw,6,width=12)
            _row(fw,"Note",         7); e_note = _ent(fw,7)
            def _limit(entry, maxlen):
                vcmd = (fw.register(lambda P: len(P) <= maxlen), "%P")
                entry.config(validate="key", validatecommand=vcmd)
            _limit(e_nome,  40)
            _limit(e_cat,   40)
            _limit(e_qty,   10)
            _limit(e_sog,   10)
            _limit(e_pu,    10)
            _limit(e_note,  50)
            if prefill:
                for e,k in [(e_nome,"nome"),(e_cat,"categoria"),(e_note,"note")]:
                    e.insert(0,prefill.get(k,""))
                e_qty.insert(0, str(prefill.get("quantita","")))
                e_unit.set(     prefill.get("unita","pz"))
                e_sog.insert(0, str(prefill.get("soglia","0")))
                e_pu.insert(0,  str(prefill.get("prezzo_unit","")))
            else:
                e_unit.set("pz")
            def _salva():
                nome = e_nome.get().strip()
                if not nome: self.show_toast("Nome obbligatorio."); return
                try:    qty    = float(e_qty.get().replace(",",".") or 0)
                except: self.show_toast("Quantità non valida."); return
                try:    soglia = float(e_sog.get().replace(",",".") or 0)
                except: soglia = 0
                try:    pu     = float(e_pu.get().replace(",",".") or 0)
                except: pu     = 0
                record = {
                    "id":          prefill["id"] if prefill else _new_id(),
                    "nome":        nome,
                    "categoria":   e_cat.get().strip(),
                    "quantita":    qty,
                    "unita":       e_unit.get().strip() or "pz",
                    "soglia":      soglia,
                    "prezzo_unit": pu,
                    "note":        e_note.get().strip(),
                }
                if prefill:
                    idx = next((i for i,m in enumerate(magazzino)
                                if m["id"]==prefill["id"]),None)
                    if idx is not None: magazzino[idx] = record
                else:
                    magazzino.append(record)
                _save(STUDIO_MAGAZZINO, magazzino)
                _refresh(record["id"])
                fw.destroy()
                self.show_toast("Materiale salvato.")
            fw.bind("<Escape>", lambda e: fw.destroy())
            bot = tk.Frame(fw, bg=self.COLOR_BACKGROUND)
            bot.grid(row=8, column=0, columnspan=4, pady=8)
            _mk_btn(bot, "salva",  "Salva",  _salva)
            _mk_btn(bot, "chiudi", "Chiudi", fw.destroy)
        def _modifica():
            sel = tv.selection()
            if not sel: self.show_toast("Seleziona una voce."); return
            r = next((m for m in magazzino if m["id"]==sel[0]),None)
            if r: _form(prefill=r)
        def _elimina():
            sel = tv.selection()
            if not sel: self.show_toast("Seleziona una voce."); return
            if self.show_custom_askyesno("Elimina","Eliminare la voce selezionata?"):
                nonlocal magazzino
                magazzino = [m for m in magazzino if m["id"]!=sel[0]]
                _save(STUDIO_MAGAZZINO, magazzino)
                _refresh()
                self.show_toast("Eliminata.")
        def _esporta_pdf():
            if not magazzino:
                self.show_toast("Magazzino vuoto."); return
            try:
                import fitz
            except ImportError:
                self.show_custom_warning("Errore",
                    "PyMuPDF non installato.\npip install pymupdf"); return
            path_out = filedialog.asksaveasfilename(
                parent=win,
                initialdir=EXPORT_DIR,
                defaultextension=".pdf",
                filetypes=[("PDF","*.pdf")],
                initialfile="Magazzino.pdf",
                confirmoverwrite=False
            )
            if not path_out: return
            if os.path.exists(path_out):
                if not self.show_custom_askyesno("Sovrascrivere?",
                        f"'{os.path.basename(path_out)}' esiste già. Sovrascrivere?"):
                    return
            try:
                W, H   = 595, 842
                MARG   = 40
                COL_R  = W - MARG
                BLU    = (0.10, 0.22, 0.45)
                ACCENT = (0.00, 0.55, 0.80)
                GREY_L = (0.95, 0.96, 0.97)
                GREY_M = (0.80, 0.82, 0.85)
                GREY_D = (0.45, 0.45, 0.48)
                BLACK  = (0.10, 0.10, 0.12)
                WHITE  = (1.00, 1.00, 1.00)
                RED    = (0.72, 0.10, 0.10)
                GREEN  = (0.08, 0.50, 0.22)
                pdoc = fitz.open()
                def _new_page():
                    pg = pdoc.new_page(width=W, height=H)
                    pg.draw_rect(fitz.Rect(0, 0, 4, H),
                                 color=None, fill=ACCENT, width=0)
                    return pg
                def _txt(pg, x, y, testo, size=9, color=BLACK,
                         bold=False, align="left"):
                    fn = "Helvetica-Bold" if bold else "Helvetica"
                    tw = fitz.get_text_length(str(testo), fontname=fn, fontsize=size)
                    if align == "right": x = x - tw
                    pg.insert_text((x, y), str(testo),
                                   fontname=fn, fontsize=size, color=color)
                def _rect(pg, x0, y0, x1, y1, fill=None, stroke=None, lw=0.5):
                    pg.draw_rect(fitz.Rect(x0, y0, x1, y1),
                                 color=stroke, fill=fill, width=lw)
                def _line(pg, x0, y0, x1, y1, color=GREY_M, lw=0.5):
                    pg.draw_line((x0,y0),(x1,y1), color=color, width=lw)
                page = _new_page()
                _rect(page, 0, 0, W, 60, fill=BLU)
                _rect(page, 0, 60, W, 63, fill=ACCENT)
                _txt(page, MARG, 32, "MAGAZZINO / SCORTE",
                     size=18, color=WHITE, bold=True)
                oggi = datetime.date.today().strftime("%d/%m/%Y")
                _txt(page, MARG, 50, f"Stampato il {oggi}",
                     size=8, color=GREY_M)
                rs = emittente.get("ragione_sociale","")
                if rs:
                    _txt(page, COL_R, 38, rs, size=9,
                         color=WHITE, bold=True, align="right")
                CX = {
                    "nome_l":  MARG + 4,
                    "cat_l":   MARG + 168,
                    "qty_r":   MARG + 288,
                    "unit_l":  MARG + 296,
                    "sog_r":   MARG + 366,
                    "val_r":   MARG + 446,
                    "note_l":  MARG + 454,
                }
                HDR_H = 18
                ROW_H = 14
                y = 76
                def _draw_header(pg, yy):
                    _rect(pg, MARG, yy, COL_R, yy+HDR_H, fill=BLU)
                    _txt(pg, CX["nome_l"], yy+12, "NOME",      size=7.5, color=WHITE, bold=True)
                    _txt(pg, CX["cat_l"],  yy+12, "CATEGORIA", size=7.5, color=WHITE, bold=True)
                    _txt(pg, CX["qty_r"],  yy+12, "QTÀ",       size=7.5, color=WHITE, bold=True, align="right")
                    _txt(pg, CX["unit_l"], yy+12, "UM",        size=7.5, color=WHITE, bold=True)
                    _txt(pg, CX["sog_r"],  yy+12, "SOGLIA",    size=7.5, color=WHITE, bold=True, align="right")
                    _txt(pg, CX["val_r"],  yy+12, "VALORE €",  size=7.5, color=WHITE, bold=True, align="right")
                    _txt(pg, CX["note_l"], yy+12, "NOTE",      size=7.5, color=WHITE, bold=True)
                _draw_header(page, y)
                y += HDR_H
                tot_valore = 0.0
                voci_sotto_soglia = 0
                for i, m in enumerate(sorted(magazzino,
                                              key=lambda x: x.get("nome","").lower())):
                    if y + ROW_H > H - 50:
                        _rect(page, 0, H-32, W, H, fill=BLU)
                        n_pages = pdoc.page_count
                        _txt(page, MARG, H-14,
                             f"Pag. {n_pages}/{n_pages}", size=7, color=GREY_M)
                        page = _new_page()
                        y = MARG
                        _draw_header(page, y)
                        y += HDR_H
                    qty    = m.get("quantita", 0)
                    soglia = m.get("soglia", 0)
                    pu     = m.get("prezzo_unit", 0.0)
                    valore = qty * pu
                    tot_valore += valore
                    sotto = qty <= soglia
                    if sotto: voci_sotto_soglia += 1
                    bg = GREY_L if i % 2 == 0 else WHITE
                    _rect(page, MARG, y, COL_R, y+ROW_H, fill=bg)
                    _line(page, MARG, y+ROW_H, COL_R, y+ROW_H, color=GREY_M, lw=0.3)
                    nome_s = (m.get("nome","")[:28]+"…") \
                             if len(m.get("nome",""))>28 else m.get("nome","")
                    cat_s  = (m.get("categoria","")[:18]+"…") \
                             if len(m.get("categoria",""))>18 else m.get("categoria","")
                    note_s = (m.get("note","")[:18]+"…") \
                             if len(m.get("note",""))>18 else m.get("note","")
                    col_qty = RED if sotto else BLACK
                    _txt(page, CX["nome_l"], y+10, nome_s,              size=8)
                    _txt(page, CX["cat_l"],  y+10, cat_s,               size=8, color=GREY_D)
                    _txt(page, CX["qty_r"],  y+10, str(qty),             size=8, color=col_qty, align="right", bold=sotto)
                    _txt(page, CX["unit_l"], y+10, m.get("unita","pz"), size=8, color=GREY_D)
                    _txt(page, CX["sog_r"],  y+10, str(soglia),          size=8, color=GREY_D, align="right")
                    _txt(page, CX["val_r"],  y+10, f"{valore:.2f}",      size=8, align="right")
                    _txt(page, CX["note_l"], y+10, note_s,               size=7, color=GREY_D)
                    y += ROW_H
                y += 6
                _line(page, MARG, y, COL_R, y, color=ACCENT, lw=1)
                y += 4
                _rect(page, MARG, y, COL_R, y+18, fill=BLU)
                _txt(page, CX["nome_l"], y+12,
                     f"Totale voci: {len(magazzino)}   "
                     f"Sotto soglia: {voci_sotto_soglia}",
                     size=8, color=WHITE, bold=True)
                _txt(page, CX["val_r"], y+12,
                     f"{tot_valore:.2f} €",
                     size=8, color=WHITE, bold=True, align="right")
                n_pages = pdoc.page_count
                for pi in range(n_pages):
                    pg = pdoc[pi]
                    _rect(pg, 0, H-32, W, H, fill=BLU)
                    _line(pg, 0, H-32, W, H-32, color=ACCENT, lw=2)
                    _txt(pg, MARG, H-14,
                         rs or "Magazzino", size=7, color=GREY_M)
                    _txt(pg, COL_R-4, H-14,
                         f"Pag. {pi+1}/{n_pages}  —  {oggi}",
                         size=7, color=GREY_M, align="right")
                pdoc.save(path_out)
                pdoc.close()
                self.show_toast("PDF magazzino salvato.")
                try:
                    if sys.platform == "win32":   os.startfile(path_out)
                    elif sys.platform == "darwin": subprocess.Popen(["open", path_out])
                    else:                          subprocess.Popen(["xdg-open", path_out])
                except Exception: pass
            except Exception as e:
                self.show_custom_warning("Errore PDF", str(e))
        
        tv.bind("<Double-1>", lambda e: _modifica())
        _btn_bar(tab_mag, [
            ("aggiungi","Nuovo",   lambda: _form(), self.COLOR_GREEN),
            ("modifica","Modifica",_modifica,       self.COLOR_HIGHLIGHT),
            ("delete",  "Elimina", _elimina,        self.COLOR_RED),
            ("report",  "Esporta PDF",_esporta_pdf,    self.TEXT_COLOR),
        ])
        tk.Label(tab_mag,
                 text="  🔴 Riga rossa = quantità ≤ soglia minima",
                 font=("Arial",8), bg=self.COLOR_BACKGROUND,
                 fg=self.COLOR_RED).pack(anchor="w", padx=10, pady=2)
        _refresh()
    def _build_emittente():
        f = tk.Frame(tab_emi, bg=self.COLOR_BACKGROUND)
        f.pack(fill="both", expand=True, padx=20, pady=20)
        ttk.Label(f, text="Dati emittente (stampati su ogni fattura/preventivo)",
                  font=("Arial", 10, "bold"),
                  background=self.COLOR_BACKGROUND,
                  foreground=self.COLOR_HIGHLIGHT).grid(row=0, column=0, columnspan=2,
                                                         sticky="w", pady=(0, 12))
        campi_emi = [
            ("ragione_sociale", "Ragione Sociale / Nome:"),
            ("indirizzo",       "Indirizzo:"),
            ("cf_piva",         "P.IVA / C.F.:"),
            ("telefono",        "Telefono:"),
            ("email",           "Email:"),
        ]
        _limiti_emi = {
            "ragione_sociale": 40,
            "indirizzo":       50,
            "cf_piva":         16,
            "telefono":        35,
            "email":           50,
        }
        entries_emi = {}
        for r, (key, lbl) in enumerate(campi_emi, start=1):
            ttk.Label(f, text=lbl, background=self.COLOR_BACKGROUND,
                      foreground=self.TEXT_COLOR, width=28,
                      anchor="e").grid(row=r, column=0, sticky="e", pady=4, padx=(0, 6))
            var = tk.StringVar(value=emittente.get(key, ""))
            e   = ttk.Entry(f, textvariable=var, width=46)
            maxlen = _limiti_emi.get(key, 100)
            vcmd = (f.register(lambda P, m=maxlen: len(P) <= m), "%P")
            e.config(validate="key", validatecommand=vcmd)
            e.grid(row=r, column=1, sticky="w", pady=4)
            entries_emi[key] = var
        ttk.Label(f, text="Logo aziendale (PNG/JPG):",
                  background=self.COLOR_BACKGROUND,
                  foreground=self.TEXT_COLOR, width=28,
                  anchor="e").grid(row=len(campi_emi)+1, column=0, sticky="e", pady=4, padx=(0, 6))
        frm_logo_outer = tk.LabelFrame(f, text=" Logo aziendale (PNG/JPG) ",
                                       bg=self.COLOR_BACKGROUND,
                                       fg=self.COLOR_HIGHLIGHT,
                                       font=("Arial", 9))
        frm_logo_outer.grid(row=len(campi_emi)+1, column=0, columnspan=2,
                             sticky="ew", pady=(10, 4), padx=2)
        var_logo = tk.StringVar(value=emittente.get("logo_path", ""))
        lbl_logo_path = ttk.Label(frm_logo_outer,
                                  background=self.COLOR_BACKGROUND,
                                  foreground=self.TEXT_COLOR,
                                  anchor="w", width=40)
        lbl_logo_path.pack(side="left", padx=8, pady=6)
        def _aggiorna_lbl_logo(*_):
            p = var_logo.get()
            lbl_logo_path.config(text=os.path.basename(p) if p else "(nessun logo)")
        var_logo.trace_add("write", _aggiorna_lbl_logo)
        _aggiorna_lbl_logo()
        frm_logo_btns = tk.Frame(frm_logo_outer, bg=self.COLOR_BACKGROUND)
        frm_logo_btns.pack(side="right", padx=8, pady=4)
        def _scegli_logo():
            p = filedialog.askopenfilename(
                parent=win,
                title="Scegli logo",
                filetypes=[("Immagini", "*.png *.jpg *.jpeg *.bmp *.gif")]
            )
            if p:
                var_logo.set(p)
        def _rimuovi_logo():
            var_logo.set("")
        _mk_btn(frm_logo_btns, "aggiungi", "Scegli...", _scegli_logo, padx=4)
        _mk_btn(frm_logo_btns, "elimina",  "Rimuovi",  _rimuovi_logo, fg=self.COLOR_RED, padx=4)
        def _salva_emittente():
            dati = {k: v.get().strip() for k, v in entries_emi.items()}
            dati["logo_path"] = var_logo.get().strip()
            _save(STUDIO_EMITTENTE, dati)
            emittente.update(dati)
            self.show_toast("Dati azienda salvati.")
        bar_emi = tk.Frame(f, bg=self.COLOR_BACKGROUND)
        bar_emi.grid(row=len(campi_emi)+2, column=0, columnspan=2, pady=16, sticky="w")
        _mk_btn(bar_emi, "salva", "Salva", _salva_emittente,
                fg=self.COLOR_GREEN)
    _build_emittente()
    def _on_tab_change(event):
        idx = nb.index(nb.select())
        if idx == 0: _build_dashboard()
    nb.bind("<<NotebookTabChanged>>", _on_tab_change)
    _build_dashboard()
    _build_clienti()
    _build_agenda()
    _build_prestazioni()
    _build_fatture()
    _build_cassa()
    _build_magazzino()

