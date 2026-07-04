#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import tkinter as tk
from tkinter import ttk, filedialog

def apri_portafoglio(self):
        from __main__ import EXPORT_FILES, EXP_DB, API_KEY, GEMINI
        from google import genai
        dati = self._porta_load()
        prezzi_live = {}
        stato = {"aggiornamento": False}
        win = tk.Toplevel(self)
        win.withdraw()
        win.title("Portafoglio Investimenti")
        win.configure(bg=self.COLOR_BACKGROUND)
        w_win, h_win = 1350, 630
        self.update_idletasks() 
        root_x = self.winfo_rootx()
        root_y = self.winfo_rooty()
        root_w = self.winfo_width()
        root_h = self.winfo_height()
        pos_x = root_x + (root_w // 2) - (w_win // 2)
        pos_y = root_y + (root_h // 2) - (h_win // 2)
        win.geometry(f"{w_win}x{h_win}+{max(0, pos_x)}+{max(0, pos_y)}")
        win.minsize(w_win, h_win)
        win.deiconify()
        barra_menu = tk.Menu(win, bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT,
                             activebackground=self.MENU_ACT_BG_COLOR,
                             activeforeground=self.MENU_ACT_FG_COLOR)
        win.config(menu=barra_menu)
        menu_dati = tk.Menu(barra_menu, tearoff=0,
                            bg=self.MENU_BG, fg=self.MENU_FG_LIGHT,
                            activebackground=self.MENU_ACT_BG_COLOR,
                            activeforeground=self.MENU_ACT_FG_COLOR)
        barra_menu.add_cascade(label="💾 Dati", menu=menu_dati)
        menu_dati.add_command(label="📤 Esporta JSON",      command=lambda: _esporta_json())
        menu_dati.add_command(label="📥 Importa JSON",      command=lambda: _importa_json())
        menu_dati.add_separator()
        menu_dati.add_command(label="🗑️ Reset portafoglio", command=lambda: _reset_portafoglio())
        button_frame = tk.Frame(win, bg=self.COLOR_BACKGROUND)
        button_frame.pack(side="bottom", pady=15)
        nb = ttk.Notebook(win)
        nb.pack(fill="both", expand=True, padx=8, pady=8)
        tab_dash   = tk.Frame(nb, bg=self.COLOR_BACKGROUND)
        tab_porta  = tk.Frame(nb, bg=self.COLOR_BACKGROUND)
        tab_mov    = tk.Frame(nb, bg=self.COLOR_BACKGROUND)
        tab_div    = tk.Frame(nb, bg=self.COLOR_BACKGROUND)
        tab_graf = tk.Frame(nb, bg=self.COLOR_BACKGROUND)
        tab_mercati = tk.Frame(nb, bg=self.COLOR_BACKGROUND)
        nb.add(tab_dash,  text="  Dashboard  ")
        nb.add(tab_porta, text="  Portafoglio  ")
        nb.add(tab_mov,   text="  Movimenti  ")
        nb.add(tab_div,   text="  Dividendi  ")
        nb.add(tab_graf,  text="  Grafici  ")
        nb.add(tab_mercati, text="  Mercati  ")
        def _build_dashboard():
            for w in tab_dash.winfo_children():
                w.destroy()
            titoli_calcolati = []
            tot_investito    = 0.0
            tot_attuale      = 0.0
            tot_dividendi    = 0.0
            for t in dati["titoli"]:
                c = self._porta_calcola_titolo(t, prezzi_live.get(t["ticker"]))
                titoli_calcolati.append(c)
                tot_investito  += c["investito"]
                tot_attuale    += c["valore_attuale"]
                tot_dividendi  += c["dividendi_netti"]
            pl_tot     = tot_attuale - tot_investito
            pl_pct_tot = (pl_tot / tot_investito * 100) if tot_investito > 0 else 0.0
            rend_reale = pl_tot + tot_dividendi
            frm_kpi = tk.Frame(tab_dash, bg=self.COLOR_BACKGROUND)
            frm_kpi.pack(fill="x", padx=12, pady=(12, 6))
            def kpi_box(parent, label, valore, colore=None):
                f = tk.Frame(parent, bg=self.COLOR_WIDGET_BG,
                             highlightbackground=self.COLOR_HIGHLIGHT,
                             highlightthickness=1)
                f.pack(side="left", expand=True, fill="both", padx=4)
                tk.Label(f, text=label, font=("Segoe UI", 8),
                         bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR).pack(pady=(8, 0))
                tk.Label(f, text=valore, font=("Segoe UI", 13, "bold"),
                         bg=self.COLOR_WIDGET_BG,
                         fg=colore or self.TEXT_COLOR).pack(pady=(2, 8))
            def fmt(v):
                return f"€ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            def fmt_pct(v):
                return f"{v:+.2f}%"
            pl_color = self.COLOR_GREEN if pl_tot >= 0 else self.COLOR_RED
            kpi_box(frm_kpi, "Investito",         fmt(tot_investito))
            kpi_box(frm_kpi, "Valore Attuale",    fmt(tot_attuale))
            kpi_box(frm_kpi, "P&L €",             fmt(pl_tot),         pl_color)
            kpi_box(frm_kpi, "P&L %",             fmt_pct(pl_pct_tot), pl_color)
            kpi_box(frm_kpi, "Dividendi Incassati", fmt(tot_dividendi))
            kpi_box(frm_kpi, "Rendimento Reale",  fmt(rend_reale),
                    self.COLOR_GREEN if rend_reale >= 0 else self.COLOR_RED)
            frm_low = tk.Frame(tab_dash, bg=self.COLOR_BACKGROUND)
            frm_low.pack(fill="both", expand=True, padx=12, pady=(30, 6))
            cvs = tk.Canvas(frm_low,
                bg=self.COLOR_WIDGET_BG,
                highlightbackground=self.COLOR_HIGHLIGHT,
                highlightthickness=1)
            cvs.pack(side="left", fill="both", expand=True, padx=(0, 10))
            PALETTE = ["#4E79A7","#F28E2B","#E15759","#76B7B2",
           "#59A14F","#EDC948","#B07AA1","#FF9DA7","#9C755F","#BAB0AC"]
            def _draw_torta(event=None):
                cvs.delete("all")
                W = cvs.winfo_width()
                H = cvs.winfo_height()
                if W < 10 or H < 10:
                    return
                if tot_attuale <= 0:
                    cvs.create_text(W // 2, H // 2, text="Nessun dato",
                                    font=("Segoe UI", 10), fill=self.TEXT_COLOR)
                    return
                LEG_H = 14
                n_visibili = sum(1 for c in titoli_calcolati if c["valore_attuale"] > 0)
                n_righe = (n_visibili + 2) // 3
                leg_area = n_righe * LEG_H + 8
                r = min(W // 2 - 20, (H - leg_area) // 2 - 20)
                r = max(r, 30)
                cx = W // 2
                cy = (H - leg_area) // 2
                angolo = 0.0
                for i, c in enumerate(titoli_calcolati):
                    if c["valore_attuale"] <= 0:
                        continue
                    ext = c["valore_attuale"] / tot_attuale * 360
                    col = PALETTE[i % len(PALETTE)]
                    cvs.create_arc(cx - r, cy - r, cx + r, cy + r,
                       start=angolo, extent=ext,
                       fill=col, outline=self.COLOR_BACKGROUND, width=2)
                    if ext > 18:
                        import math
                        mid_a = math.radians(angolo + ext / 2)
                        lx = cx + (r * 0.65) * math.cos(mid_a)
                        ly = cy - (r * 0.65) * math.sin(mid_a)
                        cvs.create_text(lx, ly, text=c["ticker"],
                            font=("Segoe UI", 7, "bold"), fill="white")
                    angolo += ext
                idx = 0
                for i, c in enumerate(titoli_calcolati):
                    if c["valore_attuale"] <= 0:
                        continue
                    col = PALETTE[i % len(PALETTE)]
                    col_x = 8 + (idx % 3) * (W // 3)
                    col_y = H - leg_area + 8 + (idx // 3) * LEG_H
                    cvs.create_rectangle(col_x, col_y, col_x + 10, col_y + 10,
                              fill=col, outline="")
                    pct = c["valore_attuale"] / tot_attuale * 100
                    cvs.create_text(col_x + 13, col_y + 5,
                                    text=f"{c['ticker']} {pct:.1f}%",
                                    anchor="w", font=("Segoe UI", 7),
                                    fill=self.TEXT_COLOR)
                    idx += 1
            cvs.bind("<Configure>", _draw_torta)                
            frm_rib = tk.Frame(frm_low, bg=self.COLOR_BACKGROUND)
            frm_rib.pack(side="left", fill="both", expand=True)
            tk.Label(frm_rib, text="Allocazione & Ribilanciamento",
                     font=("Segoe UI", 9, "bold"),
                     bg=self.COLOR_BACKGROUND, fg=self.COLOR_RED).pack(anchor="w", pady=(0,4))
            cols_r = ("Ticker","Attuale %","Target %","Scost.","Stato")
            tv_r   = ttk.Treeview(frm_rib, columns=cols_r, show="headings", height=10)
            vsb_r = ttk.Scrollbar(frm_rib, orient="vertical", command=tv_r.yview)
            tv_r.configure(yscrollcommand=vsb_r.set)
            vsb_r.pack(side="right", fill="y")
            soglia = float(dati["impostazioni"].get("soglia_ribilanciamento", 2.0))
            for c in cols_r:
                tv_r.heading(c, text=c)
                tv_r.column(c, width=90, anchor="center")
            tv_r.column("Ticker", width=70)
            for c in titoli_calcolati:
                att_pct = (c["valore_attuale"] / tot_attuale * 100) if tot_attuale > 0 else 0
                tgt_pct = c["target_pct"]
                sc      = att_pct - tgt_pct
                if tgt_pct == 0:
                    stato_s = "⚪"
                    tag     = ""
                elif abs(sc) <= soglia:
                    stato_s = "🟢 OK"
                    tag     = "ok"
                elif abs(sc) <= soglia * 2:
                    stato_s = "🟡 Attenzione"
                    tag     = "warn"
                else:
                    stato_s = "🔴 Ribilancia"
                    tag     = "alert"
                tv_r.insert("", "end",
                            values=(c["ticker"],
                                    f"{att_pct:.2f}%",
                                    f"{tgt_pct:.1f}%" if tgt_pct else "-",
                                    f"{sc:+.2f}%" if tgt_pct else "-",
                                    stato_s),
                            tags=(tag,))
            tv_r.tag_configure("ok",    foreground=self.COLOR_GREEN)
            tv_r.tag_configure("warn",  foreground=self.COLOR_RED)
            tv_r.tag_configure("alert", foreground=self.COLOR_YELLOW)
            tv_r.pack(fill="both", expand=True)
        def _build_mercati():
            for w in tab_mercati.winfo_children():
                w.destroy()
            sub_nb = ttk.Notebook(tab_mercati)
            sub_nb.pack(fill="both", expand=True, padx=6, pady=6)
            tab_sp500 = tk.Frame(sub_nb, bg=self.COLOR_BACKGROUND)
            tab_mib   = tk.Frame(sub_nb, bg=self.COLOR_BACKGROUND)
            sub_nb.add(tab_sp500, text="  S&P 500  ")
            sub_nb.add(tab_mib,   text="  FTSE MIB  ")
            def _build_tab(parent, url_wiki, col_ticker_idx, col_nome_idx, col_settore_idx, max_rows, label_carica, suffisso=""):
                frm_top = tk.Frame(parent, bg=self.COLOR_BACKGROUND)
                frm_top.pack(fill="x", padx=8, pady=(6, 2))
                lbl_info = tk.Label(frm_top, text="", bg=self.COLOR_BACKGROUND,
                                    fg=self.TEXT_COLOR, font=("Segoe UI", 9))
                lbl_info.pack(side="left")
                img_agg = self.icone_gui.get("reset_campo")
                btn_agg = tk.Label(frm_top, text=" Aggiorna", image=img_agg, compound="left",
                                   bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                                   cursor="hand2", padx=10, pady=4, font=("Segoe UI", 9))
                btn_agg.image = img_agg
                btn_agg.pack(side="right", padx=3)
                img_add = self.icone_gui.get("aggiungi")
                btn_add = tk.Label(frm_top, text=" Aggiungi al portafoglio", image=img_add, compound="left",
                                   bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                                   cursor="hand2", padx=10, pady=4, font=("Segoe UI", 9))
                btn_add.image = img_add
                btn_add.pack(side="right", padx=3)
                frm_main = tk.Frame(parent, bg=self.COLOR_BACKGROUND)
                frm_main.pack(fill="both", expand=True, padx=8, pady=4)
                frm_left = tk.Frame(frm_main, bg=self.COLOR_BACKGROUND)
                frm_left.pack(side="left", fill="both", expand=True)
                cols = ("Ticker", "Nome", "Settore", "Prezzo", "Var%", "Open", "High", "Low", "Volume")
                tv = ttk.Treeview(frm_left, columns=cols, show="headings")
                widths = [70, 180, 130, 80, 70, 80, 80, 80, 100]
                for c, w in zip(cols, widths):
                    tv.heading(c, text=c, command=lambda _c=c: self.treeview_sort_column(tv, _c, False))
                    tv.column(c, width=w, anchor="center")
                tv.column("Nome",    anchor="w")
                tv.column("Settore", anchor="w")
                tv.tag_configure("pos", foreground=self.COLOR_GREEN)
                tv.tag_configure("neg", foreground=self.COLOR_RED)
                sb = ttk.Scrollbar(frm_left, orient="vertical", command=tv.yview)
                tv.configure(yscrollcommand=sb.set)
                tv.pack(side="left", fill="both", expand=True)
                sb.pack(side="right", fill="y")
                frm_graf = tk.Frame(frm_main, bg=self.COLOR_WIDGET_BG,
                                    highlightbackground=self.COLOR_HIGHLIGHT,
                                    highlightthickness=1, width=300)
                frm_graf.pack(side="right", fill="y", padx=(8, 0))
                frm_graf.pack_propagate(False)
                tk.Label(frm_graf, text="Seleziona un titolo",
                         bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                         font=("Segoe UI", 9)).pack(expand=True)
                stato = {"dati": []}
                def _carica_dati():
                    lbl_info.config(text=f"⏳ {label_carica}...")
                    tv.delete(*tv.get_children())
                    btn_agg.config(state="disabled")
                    def _worker():
                        try:
                            import requests as req
                            from html.parser import HTMLParser
                            class TableParser(HTMLParser):
                                def __init__(self):
                                    super().__init__()
                                    self.rows = []
                                    self.current_row = []
                                    self.current_cell = ''
                                    self.in_td = False
                                    self.in_target_table = False
                                def handle_starttag(self, tag, attrs):
                                    attrs_d = dict(attrs)
                                    if tag == 'table' and 'wikitable' in attrs_d.get('class', ''):
                                        self.in_target_table = True
                                    if self.in_target_table and tag in ('td', 'th'):
                                        self.in_td = True
                                        self.current_cell = ''
                                    if self.in_target_table and tag == 'tr':
                                        self.current_row = []
                                def handle_endtag(self, tag):
                                    if tag == 'table':
                                        self.in_target_table = False
                                    if self.in_target_table and tag in ('td', 'th'):
                                        self.current_row.append(self.current_cell.strip())
                                        self.in_td = False
                                    if self.in_target_table and tag == 'tr':
                                        if self.current_row:
                                            self.rows.append(self.current_row)
                                def handle_data(self, data):
                                    if self.in_td:
                                        self.current_cell += data
                            headers = {'User-Agent': 'Mozilla/5.0'}
                            html = req.get(url_wiki, headers=headers, timeout=10).text
                            p = TableParser()
                            p.feed(html)
                            dati_wiki = []
                            for r in p.rows[1:max_rows+1]:
                                try:
                                    ticker  = r[col_ticker_idx].strip()
                                    nome    = r[col_nome_idx].strip()
                                    settore = r[col_settore_idx].strip() if col_settore_idx is not None else ""
                                    if ticker and not ticker.isdigit() and ticker != "Ticker":
                                        dati_wiki.append((ticker, nome, settore))
                                except Exception:
                                    continue
                            stato["dati"] = dati_wiki
                            tickers_yf = [t if "." in t else t + suffisso for t, n, s in dati_wiki]
                            parent.after(0, lambda: lbl_info.config(
                                text=f"⏳ Download prezzi {len(tickers_yf)} ticker..."))
                            import yfinance as yf
                            data = yf.download(tickers_yf, period="1d", group_by="ticker",
                                               threads=True, auto_adjust=False, progress=False)
                            def _chiama_popola():
                                try:
                                    _popola(dati_wiki, tickers_yf, data)
                                except Exception:
                                    pass
                            parent.after(0, _chiama_popola)
                        except Exception as e:
                            err = str(e)
                            parent.after(0, lambda: lbl_info.config(text=f"❌ Errore: {err}"))
                            parent.after(0, lambda: btn_agg.config(state="normal"))
                    import threading
                    threading.Thread(target=_worker, daemon=True).start()
                def _popola(dati_wiki, tickers_yf, data):
                    try:
                        tv.delete(*tv.get_children())
                    except Exception:
                        return       
                    ok = 0
                    for (ticker_orig, nome, settore), ticker_yf in zip(dati_wiki, tickers_yf):
                        try:
                            d = data[ticker_yf]
                            if d.empty:
                                continue
                            close  = float(d["Close"].iloc[-1])
                            open_  = float(d["Open"].iloc[-1])
                            high   = float(d["High"].iloc[-1])
                            low    = float(d["Low"].iloc[-1])
                            volume = int(d["Volume"].iloc[-1])
                            var    = ((close - open_) / open_ * 100) if open_ else 0
                            tag    = "pos" if var >= 0 else "neg"
                            tv.insert("", "end", iid=ticker_yf, values=(
                                ticker_orig, nome[:30], settore[:25],
                                f"{close:.2f}", f"{var:+.2f}%",
                                f"{open_:.2f}", f"{high:.2f}", f"{low:.2f}",
                                f"{volume:,}",
                            ), tags=(tag,))
                            ok += 1
                        except Exception:
                            continue
                    lbl_info.config(text=f"✅ {ok} titoli caricati.")
                    btn_agg.config(state="normal")
                def _disegna_grafico(ticker_yf, nome):
                    for w in frm_graf.winfo_children():
                        w.destroy()
                    tk.Label(frm_graf, text=nome[:28], bg=self.COLOR_WIDGET_BG,
                             fg=self.TEXT_COLOR, font=("Segoe UI", 8, "bold")).pack(pady=(6, 2))
                    lbl_g = tk.Label(frm_graf, text="⏳ Caricamento...",
                                     bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                                     font=("Segoe UI", 8))
                    lbl_g.pack()
                    def _worker_graf():
                        try:
                            import yfinance as yf
                            df = yf.download(ticker_yf, period="1mo", interval="1d",
                                             progress=False, auto_adjust=False)
                            if df.empty:
                                frm_graf.after(0, lambda: lbl_g.config(text="Nessun dato."))
                                return
                            closes = [float(df["Close"][ticker_yf].iloc[i]) for i in range(len(df))]
                            dates  = [str(df.index[i])[:10] for i in range(len(df))]
                            frm_graf.after(0, lambda: _draw_graf(closes, dates, nome))
                        except Exception as e:
                            err = str(e)
                            frm_graf.after(0, lambda: lbl_g.config(text=f"Errore: {err}"))
                    import threading
                    threading.Thread(target=_worker_graf, daemon=True).start()
                def _draw_graf(closes, dates, nome):
                    for w in frm_graf.winfo_children():
                        w.destroy()
                    tk.Label(frm_graf, text=nome[:28], bg=self.COLOR_WIDGET_BG,
                             fg=self.TEXT_COLOR, font=("Segoe UI", 8, "bold")).pack(pady=(6, 2))
                    cvs = tk.Canvas(frm_graf, bg=self.COLOR_WIDGET_BG, highlightthickness=0)
                    cvs.pack(fill="both", expand=True, padx=4, pady=4)
                    def _draw(event=None):
                        cvs.delete("all")
                        W = cvs.winfo_width()
                        H = cvs.winfo_height()
                        if W < 50 or H < 50 or not closes:
                            return
                        PAD_L, PAD_R, PAD_T, PAD_B = 50, 10, 15, 35
                        v_min = min(closes) * 0.998
                        v_max = max(closes) * 1.002
                        n = len(closes)
                        col = self.COLOR_GREEN if closes[-1] >= closes[0] else self.COLOR_RED
                        def tx(i): return PAD_L + i / max(n-1, 1) * (W - PAD_L - PAD_R)
                        def ty(v): return PAD_T + (1-(v-v_min)/(v_max-v_min)) * (H-PAD_T-PAD_B)
                        for s in range(5):
                            yv = v_min + (v_max-v_min) * s / 4
                            yp = ty(yv)
                            cvs.create_line(PAD_L, yp, W-PAD_R, yp,
                                            fill=self.COLOR_HEADER_BG, dash=(2, 4))
                            cvs.create_text(PAD_L-3, yp, text=f"{yv:.1f}",
                                            anchor="e", font=("Segoe UI", 6), fill=self.TEXT_COLOR)
                        pts = []
                        for i, v in enumerate(closes):
                            pts += [tx(i), ty(v)]
                        if len(pts) >= 4:
                            cvs.create_line(pts, fill=col, width=2, smooth=True)
                        step = max(1, n // 4)
                        for i in range(0, n, step):
                            cvs.create_text(tx(i), H-PAD_B+8, text=dates[i][5:],
                                            font=("Segoe UI", 6), fill=self.TEXT_COLOR)
                        cvs.create_text(W-PAD_R, ty(closes[-1])-8,
                                        text=f"{closes[-1]:.2f}", anchor="e",
                                        font=("Segoe UI", 7, "bold"), fill=col)
                    cvs.bind("<Configure>", _draw)
                    cvs.after(100, _draw)
                def _on_select(event):
                    sel = tv.selection()
                    if not sel:
                        return
                    ticker_yf = sel[0]
                    vals = tv.item(sel[0])["values"]
                    nome = str(vals[1])
                    _disegna_grafico(ticker_yf, nome)
                def _aggiungi_selezionato():
                    sel = tv.selection()
                    if not sel:
                        self.show_toast("Seleziona un titolo dalla lista.")
                        return
                    vals = tv.item(sel[0])["values"]
                    ticker_orig = str(vals[0])
                    _dlg_nuovo_titolo(ticker_orig)
                tv.bind("<<TreeviewSelect>>", _on_select)
                btn_agg.bind("<Button-1>", lambda e: _carica_dati())
                btn_add.bind("<Button-1>", lambda e: _aggiungi_selezionato())
                _carica_dati()
            _build_tab(tab_sp500,
                       "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
                       0, 1, 2, 50, "Download lista S&P 500")
            _build_tab(tab_mib,
                       "https://en.wikipedia.org/wiki/FTSE_MIB",
                       0, 1, 2, 40, "Download lista FTSE MIB", suffisso="")
            
        def _build_portafoglio():
            for w in tab_porta.winfo_children():
                w.destroy()
            frm_btn = tk.Frame(tab_porta, bg=self.COLOR_BACKGROUND)
            frm_btn.pack(fill="x", padx=8, pady=6)
            def _btn(parent, testo, cmd, icon_key):
                img = self.icone_gui.get(icon_key)
                lbl = tk.Label(
                    parent, 
                    image=img, 
                    text=f" {testo}" if img else testo,
                    compound="left",
                    bg=self.COLOR_WIDGET_BG,
                    fg=self.TEXT_COLOR, 
                    font=("Segoe UI", 9), 
                    cursor="hand2",
                    padx=10, 
                    pady=4
                )
                lbl.image = img 
                lbl.pack(side="left", padx=3)
                lbl.bind("<Button-1>", lambda e: cmd())
            _btn(frm_btn, "Aggiungi Titolo", _dlg_nuovo_titolo, "aggiungi")
            _btn(frm_btn, "Aggiorna Prezzi", _aggiorna_prezzi,   "reset_campo")
            _btn(frm_btn, "Rimuovi Titolo",  _rimuovi_titolo,    "delete")
            img_mouse = self.icone_gui.get("mouse")
            lbl_hint = tk.Label(frm_btn,
                                text=" doppio clic per nuovo movimento",
                                image=img_mouse, compound="left",
                                bg=self.COLOR_BACKGROUND,
                                fg=self.TEXT_COLOR,
                                font=("Segoe UI", 8, "italic"))
            lbl_hint.image = img_mouse
            lbl_hint.pack(side="left", padx=(12, 0))
            cols = ("Ticker","Descrizione","Asset Class","Quantità",
                    "P.M.C. €","Prezzo €","Valore €","Investito €","P&L €","P&L %")
            tv = ttk.Treeview(tab_porta, columns=cols, show="headings")
            widths = [70,160,100,80,90,90,100,100,90,80]
            for c, w in zip(cols, widths):
                tv.heading(c, text=c, command=lambda _c=c: _sort_porta(_c, False))
                tv.column(c, width=w, anchor="center")
            def _on_double_porta(event):
                iid = tv.identify_row(event.y)
                if not iid or iid == "TOTALE":
                    return
                _dlg_nuovo_movimento(ticker_pre=iid)
            tv.bind("<Double-1>", _on_double_porta)
            def _sort_porta(col, reverse):
                rows = [(tv.set(k, col), k) for k in tv.get_children("")
                        if tv.set(k, "Ticker") != "TOTALE"]
                totale = [k for k in tv.get_children("") if tv.set(k, "Ticker") == "TOTALE"]
                try:
                    rows.sort(key=lambda t: float(str(t[0]).replace(",",".").replace("€","").replace("%","").replace("+","").replace(" ","")), reverse=reverse)
                except Exception:
                    rows.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)
                for i, (_, k) in enumerate(rows):
                    tv.move(k, "", i)
                for k in totale:
                    tv.move(k, "", "end")
                for c2 in tv["columns"]:
                    cur = tv.heading(c2, "text")
                    clean = cur.replace(" ▲","").replace(" ▼","")
                    arrow = (" ▲" if not reverse else " ▼") if c2 == col else ""
                    tv.heading(c2, text=clean + arrow, command=lambda _c=c2: _sort_porta(_c, not reverse if _c == col else False))
            tv.column("Descrizione", anchor="w")
            tv.tag_configure("pos", foreground=self.COLOR_GREEN)
            tv.tag_configure("neg", foreground=self.COLOR_RED)
            tot_inv = tot_att = tot_pl = 0.0
            for t in dati["titoli"]:
                c = self._porta_calcola_titolo(t, prezzi_live.get(t["ticker"]))
                tag = "pos" if c["pl_eur"] >= 0 else "neg"
                tv.insert("", "end", iid=c["ticker"], values=(
                    c["ticker"],
                    c["descrizione"],
                    c["asset_class"],
                    f"{c['quantita']:.4f}",
                    f"{c['pmc']:.4f}",
                    f"{c['prezzo_attuale']:.4f}",
                    f"{c['valore_attuale']:,.2f}",
                    f"{c['investito']:,.2f}",
                    f"{c['pl_eur']:+,.2f}",
                    f"{c['pl_pct']:+.2f}%",
                ), tags=(tag,))
                tot_inv += c["investito"]
                tot_att += c["valore_attuale"]
                tot_pl  += c["pl_eur"]
            tv.insert("", "end", values=(
                "TOTALE","","","","","",
                f"{tot_att:,.2f}",
                f"{tot_inv:,.2f}",
                f"{tot_pl:+,.2f}",
                f"{(tot_pl/tot_inv*100 if tot_inv else 0):+.2f}%",
            ), tags=("pos" if tot_pl >= 0 else "neg",))
            sb = ttk.Scrollbar(tab_porta, orient="vertical", command=tv.yview)
            tv.configure(yscrollcommand=sb.set)
            tv.pack(side="left", fill="both", expand=True, padx=(8,0), pady=4)
            sb.pack(side="left", fill="y", pady=4)
            tab_porta._tv = tv
        def _build_movimenti():
            for w in tab_mov.winfo_children():
                w.destroy()
            frm_btn = tk.Frame(tab_mov, bg=self.COLOR_BACKGROUND)
            frm_btn.pack(fill="x", padx=8, pady=6)
            tk.Label(frm_btn, text="Titolo:", bg=self.COLOR_BACKGROUND,
                     fg=self.TEXT_COLOR, font=("Segoe UI", 9)).pack(side="left")
            var_filt = tk.StringVar(value="Tutti")
            tickers  = ["Tutti"] + [t["ticker"] for t in dati["titoli"]]
            cb = ttk.Combobox(frm_btn, textvariable=var_filt,
                              values=tickers, width=10, state="readonly", style="Border.TCombobox")
            cb.pack(side="left", padx=(4, 12))
            def _btn(parent, testo, cmd, icon_key):
                img = self.icone_gui.get(icon_key)
                lbl = tk.Label(
                    parent,
                    text=f" {testo}",
                    image=img,
                    compound="left",
                    bg=self.COLOR_WIDGET_BG,
                    fg=self.TEXT_COLOR,
                    font=("Segoe UI", 9, "bold"),
                    cursor="hand2",
                    padx=10,
                    pady=4
                )
                lbl.image = img
                lbl.pack(side="left", padx=3)
                lbl.bind("<Button-1>", lambda e: cmd())
            _btn(frm_btn, "Registra Movimento", _dlg_nuovo_movimento, "aggiungi")
            img_mouse = self.icone_gui.get("mouse")
            lbl_hint = tk.Label(frm_btn,
                                text=" doppio clic per modificare",
                                image=img_mouse, compound="left",
                                bg=self.COLOR_BACKGROUND,
                                fg=self.TEXT_COLOR,
                                font=("Segoe UI", 8, "italic"))
            lbl_hint.image = img_mouse
            lbl_hint.pack(side="left", padx=(12, 0))
            cols = ("Data","Ticker","Tipo","Quantità","Prezzo €","Commissioni €","Totale €","Note")
            tv = ttk.Treeview(tab_mov, columns=cols, show="headings")
            widths = [90,70,80,90,100,110,110,160]
            def _sort_mov(col, reverse):
                rows = [(tv.set(k, col), k) for k in tv.get_children("")]
                try:
                    rows.sort(key=lambda t: float(str(t[0]).replace(",",".").replace("€","").replace("%","").replace("+","").replace(" ","")), reverse=reverse)
                except Exception:
                    rows.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)
                for i, (_, k) in enumerate(rows):
                    tv.move(k, "", i)
                for c2 in tv["columns"]:
                    cur = tv.heading(c2, "text")
                    clean = cur.replace(" ▲","").replace(" ▼","")
                    arrow = (" ▲" if not reverse else " ▼") if c2 == col else ""
                    tv.heading(c2, text=clean + arrow, command=lambda _c=c2: _sort_mov(_c, not reverse if _c == col else False))
            for c, w in zip(cols, widths):
                tv.heading(c, text=c, command=lambda _c=c: _sort_mov(_c, False))
                tv.column(c, width=w, anchor="center")
            tv.column("Note", anchor="w")
            tv.tag_configure("acquisto", foreground=self.COLOR_GREEN)
            tv.tag_configure("vendita",  foreground=self.COLOR_RED)
            ref_mov = {}
            def _popola_mov(filtro="Tutti"):
                tv.delete(*tv.get_children())
                ref_mov.clear()
                for t in dati["titoli"]:
                    if filtro != "Tutti" and t["ticker"] != filtro:
                        continue
                    for m in sorted(t.get("movimenti", []),
                                    key=lambda x: x.get("data",""), reverse=True):
                        q   = float(m.get("quantita", 0))
                        p   = float(m.get("prezzo", 0))
                        com = float(m.get("commissioni", 0))
                        tot = q * p + (com if m.get("tipo") == "acquisto" else -com)
                        iid = str(id(m))
                        ref_mov[iid] = (t, m)
                        tv.insert("", "end", iid=iid, values=(
                            m.get("data",""),
                            t["ticker"],
                            m.get("tipo","").capitalize(),
                            f"{q:.4f}",
                            f"{p:.4f}",
                            f"{com:.2f}",
                            f"{tot:,.2f}",
                            m.get("note",""),
                        ), tags=(m.get("tipo",""),))
            _popola_mov()
            cb.bind("<<ComboboxSelected>>", lambda e: _popola_mov(var_filt.get()))
            def _on_double_mov(event):
                iid = tv.identify_row(event.y)
                if not iid or iid not in ref_mov:
                    return
                titolo, mov = ref_mov[iid]
                _dlg_edit_movimento(titolo, mov)
            def _dlg_edit_movimento(titolo, mov):
                import datetime
                dlg = tk.Toplevel(win)
                dlg.withdraw()
                dlg.title("Modifica Movimento")
                dlg.configure(bg=self.COLOR_BACKGROUND)
                w_dlg, h_dlg = 360, 430
                x = win.winfo_x() + (win.winfo_width()  // 2) - (w_dlg // 2)
                y = win.winfo_y() + (win.winfo_height() // 2) - (h_dlg // 2)
                dlg.geometry(f"{w_dlg}x{h_dlg}+{max(0,x)}+{max(0,y)}")
                dlg.resizable(False, False)
                dlg.transient(win)
                dlg.bind("<Escape>", lambda e: dlg.destroy())
                dlg.deiconify()
                campi_label = ["Ticker", "Tipo", "Data (GG-MM-AAAA)",
                               "Quantità", "Prezzo €", "Commissioni €", "Note"]
                campi_key   = ["ticker", "tipo", "data",
                               "quantita", "prezzo", "commissioni", "note"]
                defaults    = [
                    titolo["ticker"],
                    mov.get("tipo", "acquisto"),
                    mov.get("data", ""),
                    str(mov.get("quantita", "")),
                    str(mov.get("prezzo", "")),
                    str(mov.get("commissioni", "0")),
                    mov.get("note", ""),
                ]
                vars_ = {}
                for label, key, default in zip(campi_label, campi_key, defaults):
                    tk.Label(dlg, text=label, bg=self.COLOR_BACKGROUND,
                             fg=self.TEXT_COLOR, font=("Segoe UI", 9)).pack(anchor="w", padx=16, pady=(6,0))
                    v = tk.StringVar(value=default)
                    vars_[key] = v
                    if key == "ticker":
                        tk.Label(dlg, textvariable=v, bg=self.COLOR_BACKGROUND,
                                 fg=self.COLOR_HIGHLIGHT,
                                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16)
                    elif key == "tipo":
                        ttk.Combobox(dlg, textvariable=v, values=["acquisto", "vendita"],
                                     state="readonly", style="Border.TCombobox").pack(fill="x", padx=16)
                    elif key == "data":
                        frm_d = tk.Frame(dlg, bg=self.COLOR_BACKGROUND)
                        frm_d.pack(fill="x", padx=16)
                        ent = ttk.Entry(frm_d, textvariable=v, font=("Segoe UI", 10))
                        ent.pack(side="left", expand=True, fill="x", padx=(0, 5))
                        lbl_cal = tk.Label(frm_d, image=self.icone_gui.get("calendario"),
                                           bg=self.COLOR_BACKGROUND, cursor="hand2")
                        lbl_cal.image = self.icone_gui.get("calendario")
                        lbl_cal.pack(side="left")
                        lbl_cal.bind("<Button-1>", lambda ev, e=ent, var=v:
                                     self.mostra_calendario_popup_semplice(e, var))
                    else:
                        ttk.Entry(dlg, textvariable=v,
                                  font=("Segoe UI", 10)).pack(fill="x", padx=16)
                def _salva():
                    try:
                        datetime.datetime.strptime(vars_["data"].get(), "%d-%m-%Y")
                    except ValueError:
                        self.show_toast("Data non valida.")
                        return
                    try:
                        q = float(vars_["quantita"].get().replace(",", "."))
                        p = float(vars_["prezzo"].get().replace(",", "."))
                        c = float(vars_["commissioni"].get().replace(",", ".") or 0)
                    except ValueError:
                        self.show_toast("Valori non validi.")
                        return
                    mov["tipo"]        = vars_["tipo"].get().strip().lower()
                    mov["data"]        = vars_["data"].get()
                    mov["quantita"]    = q
                    mov["prezzo"]      = p
                    mov["commissioni"] = c
                    mov["note"]        = vars_["note"].get().strip()
                    self._porta_save(dati)
                    dlg.destroy()
                    _refresh_all()
                def _elimina():
                    if not self.show_custom_askyesno("Elimina",
                            f"Eliminare questo movimento di {titolo['ticker']}?"):
                        return
                    titolo["movimenti"] = [m for m in titolo.get("movimenti", [])
                                           if m is not mov]
                    self._porta_save(dati)
                    dlg.destroy()
                    _refresh_all()
                frm_act = tk.Frame(dlg, bg=self.COLOR_BACKGROUND)
                frm_act.pack(pady=12)
                for testo, cmd, ico in [(" Salva",   _salva,      "salva"),
                                        (" Elimina", _elimina,    "delete"),
                                        (" Chiudi",  dlg.destroy, "chiudi")]:
                    img = self.icone_gui.get(ico)
                    b = tk.Label(frm_act, text=testo, image=img, compound="left",
                                 bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                                 font=("Segoe UI", 10, "bold"), cursor="hand2",
                                 padx=15, pady=8)
                    b.image = img
                    b.pack(side="left", padx=6)
                    b.bind("<Button-1>", lambda e, c=cmd: c())
            tv.bind("<Double-1>", _on_double_mov)
            sb = ttk.Scrollbar(tab_mov, orient="vertical", command=tv.yview)
            tv.configure(yscrollcommand=sb.set)
            tv.pack(side="left", fill="both", expand=True, padx=(8,0), pady=4)
            sb.pack(side="left", fill="y", pady=4)
        def _build_dividendi():
            for w in tab_div.winfo_children():
                w.destroy()
            frm_btn = tk.Frame(tab_div, bg=self.COLOR_BACKGROUND)
            frm_btn.pack(fill="x", padx=8, pady=6)
            def _btn(parent, testo, cmd, icon_key="aggiungi"):
                img = self.icone_gui.get(icon_key)
                lbl = tk.Label(parent,
                               text=f" {testo}",
                               image=img,
                               compound="left",
                               bg=self.COLOR_WIDGET_BG,
                               fg=self.TEXT_COLOR,
                               font=("Segoe UI", 9),
                               relief="flat",
                               padx=10, pady=4,
                               cursor="hand2")
                lbl.image = img
                lbl.pack(side="left", padx=3)
                lbl.bind("<Button-1>", lambda e: cmd())
            _btn(frm_btn, "Registra Dividendo", _dlg_nuovo_dividendo, icon_key="aggiungi")
            img_mouse = self.icone_gui.get("mouse")
            lbl_hint = tk.Label(frm_btn,
                                text=" doppio clic per modificare",
                                image=img_mouse, compound="left",
                                bg=self.COLOR_BACKGROUND,
                                fg=self.TEXT_COLOR,
                                font=("Segoe UI", 8, "italic"))
            lbl_hint.image = img_mouse
            lbl_hint.pack(side="left", padx=(12, 0))
            cols = ("Data", "Ticker", "Lordo €", "Ritenuta €", "Netto €")
            tv = ttk.Treeview(tab_div, columns=cols, show="headings")
            def _sort_div(col, reverse):
                rows = [(tv.set(k, col), k) for k in tv.get_children("")
                        if tv.set(k, "Data") != "TOTALE"]
                totale = [k for k in tv.get_children("") if tv.set(k, "Data") == "TOTALE"]
                try:
                    rows.sort(key=lambda t: float(str(t[0]).replace(",",".").replace("€","").replace("%","").replace("+","").replace(" ","")), reverse=reverse)
                except Exception:
                    rows.sort(key=lambda t: str(t[0]).lower(), reverse=reverse)
                for i, (_, k) in enumerate(rows):
                    tv.move(k, "", i)
                for k in totale:
                    tv.move(k, "", "end")
                for c2 in tv["columns"]:
                    cur = tv.heading(c2, "text")
                    clean = cur.replace(" ▲","").replace(" ▼","")
                    arrow = (" ▲" if not reverse else " ▼") if c2 == col else ""
                    tv.heading(c2, text=clean + arrow, command=lambda _c=c2: _sort_div(_c, not reverse if _c == col else False))
            for c in cols:
                tv.heading(c, text=c, command=lambda _c=c: _sort_div(_c, False))
                tv.column(c, width=120, anchor="center")
            ref_div = {}
            tot_netto = 0.0
            righe = []
            for t in dati["titoli"]:
                for d in t.get("dividendi", []):
                    lordo    = float(d.get("importo_lordo", d.get("importo", 0)))
                    ritenuta = float(d.get("ritenuta", 0))
                    netto    = float(d.get("importo_netto", lordo - ritenuta))
                    righe.append((d.get("data",""), t["ticker"], lordo, ritenuta, netto, t, d))
                    tot_netto += netto
            for r in sorted(righe, key=lambda x: x[0], reverse=True):
                iid = str(id(r[6]))
                ref_div[iid] = (r[5], r[6])
                tv.insert("", "end", iid=iid, values=(
                    r[0], r[1],
                    f"{r[2]:,.2f}", f"{r[3]:,.2f}", f"{r[4]:,.2f}"))
            tv.insert("", "end", values=("TOTALE", "", "", "", f"{tot_netto:,.2f}"))
            sb = ttk.Scrollbar(tab_div, orient="vertical", command=tv.yview)
            tv.configure(yscrollcommand=sb.set)
            tv.pack(side="left", fill="both", expand=True, padx=(8,0), pady=4)
            sb.pack(side="left", fill="y", pady=4)
            def _on_double_div(event=None):
                sel = tv.selection()
                if not sel or sel[0] not in ref_div:
                    return
                titolo, div = ref_div[sel[0]]
                _dlg_edit_dividendo(titolo, div)
            def _dlg_edit_dividendo(titolo, div):
                import datetime
                dlg = tk.Toplevel(win)
                dlg.withdraw()
                dlg.title("Modifica Dividendo")
                dlg.configure(bg=self.COLOR_BACKGROUND)
                w_dlg, h_dlg = 360, 350
                x = win.winfo_x() + (win.winfo_width()  // 2) - (w_dlg // 2)
                y = win.winfo_y() + (win.winfo_height() // 2) - (h_dlg // 2)
                dlg.geometry(f"{w_dlg}x{h_dlg}+{max(0,x)}+{max(0,y)}")
                dlg.resizable(False, False)
                dlg.transient(win)
                dlg.bind("<Escape>", lambda e: dlg.destroy())
                dlg.deiconify()
                campi_label = ["Ticker", "Data (GG-MM-AAAA)",
                               "Importo Lordo €", "Ritenuta €", "Importo Netto €"]
                campi_key   = ["ticker", "data", "importo_lordo", "ritenuta", "importo_netto"]
                defaults    = [
                    titolo["ticker"],
                    div.get("data", ""),
                    str(div.get("importo_lordo", div.get("importo", ""))),
                    str(div.get("ritenuta", "0")),
                    str(div.get("importo_netto", "")),
                ]
                vars_ = {}
                for label, key, default in zip(campi_label, campi_key, defaults):
                    tk.Label(dlg, text=label, bg=self.COLOR_BACKGROUND,
                             fg=self.TEXT_COLOR, font=("Segoe UI", 9)).pack(anchor="w", padx=16, pady=(8,0))
                    v = tk.StringVar(value=default)
                    vars_[key] = v
                    if key == "ticker":
                        tk.Label(dlg, textvariable=v, bg=self.COLOR_BACKGROUND,
                                 fg=self.COLOR_HIGHLIGHT,
                                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16)
                    elif key == "data":
                        frm_d = tk.Frame(dlg, bg=self.COLOR_BACKGROUND)
                        frm_d.pack(fill="x", padx=16)
                        ent = ttk.Entry(frm_d, textvariable=v, font=("Segoe UI", 10))
                        ent.pack(side="left", expand=True, fill="x", padx=(0, 5))
                        lbl_cal = tk.Label(frm_d, image=self.icone_gui.get("calendario"),
                                           bg=self.COLOR_BACKGROUND, cursor="hand2")
                        lbl_cal.image = self.icone_gui.get("calendario")
                        lbl_cal.pack(side="left")
                        lbl_cal.bind("<Button-1>", lambda ev, e=ent, var=v:
                                     self.mostra_calendario_popup_semplice(e, var))
                    else:
                        ttk.Entry(dlg, textvariable=v,
                                  font=("Segoe UI", 10)).pack(fill="x", padx=16)
                def _calc_netto(*_):
                    try:
                        lordo    = float(vars_["importo_lordo"].get().replace(",", ".") or 0)
                        ritenuta = float(vars_["ritenuta"].get().replace(",", ".") or 0)
                        vars_["importo_netto"].set(f"{lordo - ritenuta:.2f}")
                    except Exception:
                        pass
                vars_["importo_lordo"].trace_add("write", _calc_netto)
                vars_["ritenuta"].trace_add("write", _calc_netto)
                def _salva():
                    try:
                        datetime.datetime.strptime(vars_["data"].get(), "%d-%m-%Y")
                    except ValueError:
                        self.show_toast("Data non valida.")
                        return
                    try:
                        lordo    = float(vars_["importo_lordo"].get().replace(",", "."))
                        ritenuta = float(vars_["ritenuta"].get().replace(",", ".") or 0)
                        netto    = float(vars_["importo_netto"].get().replace(",", "."))
                    except ValueError:
                        self.show_toast("Importi non validi.")
                        return
                    div["data"]          = vars_["data"].get()
                    div["importo_lordo"] = lordo
                    div["ritenuta"]      = ritenuta
                    div["importo_netto"] = netto
                    self._porta_save(dati)
                    dlg.destroy()
                    _refresh_all()
                def _elimina():
                    if not self.show_custom_askyesno("Elimina",
                            f"Eliminare questo dividendo di {titolo['ticker']}?"):
                        return
                    titolo["dividendi"] = [d for d in titolo.get("dividendi", [])
                                           if d is not div]
                    self._porta_save(dati)
                    dlg.destroy()
                    _refresh_all()
                frm_act = tk.Frame(dlg, bg=self.COLOR_BACKGROUND)
                frm_act.pack(pady=12)
                for testo, cmd, ico in [(" Salva",   _salva,          "salva"),
                         (" Elimina", _elimina,        "delete"),
                         (" Chiudi",  dlg.destroy,     "chiudi")]:
                    img = self.icone_gui.get(ico)
                    b = tk.Label(frm_act, text=testo, image=img, compound="left",
                                 bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                                 font=("Segoe UI", 10, "bold"), cursor="hand2",
                                 padx=15, pady=8)
                    b.image = img
                    b.pack(side="left", padx=6)
                    b.bind("<Button-1>", lambda e, c=cmd: c())
            tv.bind("<Double-1>", _on_double_div)
        def _dlg_nuovo_titolo(ticker_pre=""):
            dlg = tk.Toplevel(win)
            dlg.withdraw()
            dlg.title("Aggiungi Titolo")
            dlg.configure(bg=self.COLOR_BACKGROUND)
            w_dlg, h_dlg = 360, 320
            root_x = win.winfo_x()
            root_y = win.winfo_y()
            root_w = win.winfo_width()
            root_h = win.winfo_height()
            x = root_x + (root_w // 2) - (w_dlg // 2)
            y = root_y + (root_h // 2) - (h_dlg // 2)
            dlg.geometry(f"{w_dlg}x{h_dlg}+{x}+{y}")
            dlg.resizable(False, False)
            dlg.transient(win)
            dlg.bind("<Escape>", lambda e: dlg.destroy())
            dlg.deiconify()
            campi = [
                ("Ticker (es. VWCE.AS)", "ticker"),
                ("Descrizione",          "descrizione"),
                ("ISIN (opzionale)",     "isin"),
                ("Asset Class",          "asset_class"),
                ("Target % (es. 55)",    "target_pct"),
            ]
            vars_ = {}
            for label, key in campi:
                tk.Label(dlg, text=label, bg=self.COLOR_BACKGROUND,
                         fg=self.TEXT_COLOR, font=("Segoe UI", 9)).pack(anchor="w", padx=16, pady=(8,0))
                v = tk.StringVar(value=ticker_pre if key == "ticker" else "")
                vars_[key] = v
                if key == "ticker":
                    frm_ticker = tk.Frame(dlg, bg=self.COLOR_BACKGROUND)
                    frm_ticker.pack(fill="x", padx=16)
                    ttk.Entry(frm_ticker, textvariable=v, font=("Segoe UI", 10)).pack(side="left", fill="x", expand=True)
                    img_cerca = self.icone_gui.get("search") or self.icone_gui.get("lente") or self.icone_gui.get("cerca")
                    btn_cerca = tk.Label(frm_ticker, text=" 🔍", bg=self.COLOR_WIDGET_BG,
                                         fg=self.TEXT_COLOR, cursor="hand2", padx=6, pady=2,
                                         font=("Segoe UI", 10))
                    btn_cerca.pack(side="left", padx=(4, 0))
                    btn_cerca.bind("<Button-1>", lambda e: _cerca_ticker(vars_["ticker"]))
                else:
                    ttk.Entry(dlg, textvariable=v, font=("Segoe UI", 10)).pack(fill="x", padx=16)
            def _cerca_ticker(var_ticker):
                popup = tk.Toplevel(dlg)
                popup.withdraw()
                popup.title("Cerca Ticker")
                popup.configure(bg=self.COLOR_BACKGROUND)
                popup.transient(dlg)
                w, h = 1000, 400
                x = dlg.winfo_x() + (dlg.winfo_width() // 2) - (w // 2)
                y = dlg.winfo_y() + (dlg.winfo_height() // 2) - (h // 2)
                popup.geometry(f"{w}x{h}+{max(0,x)}+{max(0,y)}")
                popup.resizable(False, False)
                popup.bind("<Escape>", lambda e: popup.destroy())
                popup.deiconify()
                frm_top = tk.Frame(popup, bg=self.COLOR_BACKGROUND)
                frm_top.pack(fill="x", padx=12, pady=(12, 6))
                tk.Label(frm_top, text="Cerca:", bg=self.COLOR_BACKGROUND,
                         fg=self.TEXT_COLOR, font=("Segoe UI", 9)).pack(side="left")
                var_q = tk.StringVar()
                ent_q = ttk.Entry(frm_top, textvariable=var_q, font=("Segoe UI", 10), width=28)
                ent_q.pack(side="left", padx=(6, 4))
                img_s = self.icone_gui.get("search") or self.icone_gui.get("cerca")
                btn_s = tk.Label(frm_top, text=" Cerca", image=img_s, compound="left",
                                 bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                                 cursor="hand2", padx=8, pady=3, font=("Segoe UI", 9))
                btn_s.image = img_s
                btn_s.pack(side="left")

                lbl_stato = tk.Label(popup, text="", bg=self.COLOR_BACKGROUND,
                                     fg=self.TEXT_COLOR, font=("Segoe UI", 8))
                lbl_stato.pack(anchor="w", padx=12)

                cols = ("Ticker", "Nome", "Tipo", "Borsa")
                tv = ttk.Treeview(popup, columns=cols, show="headings", height=12)
                for c in cols:
                    tv.heading(c, text=c)
                tv.column("Ticker", width=90,  anchor="center")
                tv.column("Nome",   width=280, anchor="w")
                tv.column("Tipo",   width=70,  anchor="center")
                tv.column("Borsa",  width=100, anchor="center")
                sb = ttk.Scrollbar(popup, orient="vertical", command=tv.yview)
                tv.configure(yscrollcommand=sb.set)
                frm_bottom = tk.Frame(popup, bg=self.COLOR_BACKGROUND)
                frm_bottom.pack(side="bottom", fill="x", padx=12, pady=(0, 8))
                img_c = self.icone_gui.get("chiudi")
                btn_c = tk.Label(frm_bottom, text=" Chiudi", image=img_c, compound="left",
                                 bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                                 cursor="hand2", padx=12, pady=5, font=("Segoe UI", 9))
                btn_c.image = img_c
                btn_c.pack(anchor="center")
                btn_c.bind("<Button-1>", lambda e: popup.destroy())
                tv.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=6)
                sb.pack(side="left", fill="y", pady=6, padx=(0, 12))
                def _esegui_ricerca():
                    q = var_q.get().strip()
                    if not q:
                        return
                    lbl_stato.config(text="⏳ Ricerca in corso...")
                    btn_s.config(state="disabled")
                    tv.delete(*tv.get_children())
                    def _worker():
                        try:
                            import yfinance as yf
                            r = yf.Search(q, max_results=20)
                            risultati = r.quotes if r.quotes else []
                        except Exception as e:
                            risultati = []
                            _msg = str(e)  # cattura subito il messaggio
                            popup.after(0, lambda msg=_msg: lbl_stato.config(text=f"❌ Errore: {msg}"))
                            popup.after(0, lambda: btn_s.config(state="normal"))
                            return
                        def _popola():
                            tv.delete(*tv.get_children())
                            if not risultati:
                                lbl_stato.config(text="Nessun risultato.")
                            else:
                                lbl_stato.config(text=f"{len(risultati)} risultati.")
                                for q_ in risultati:
                                    nome = q_.get("longname") or q_.get("shortname") or ""
                                    tv.insert("", "end", values=(
                                        q_.get("symbol", ""),
                                        nome,
                                        q_.get("quoteType", ""),
                                        q_.get("exchDisp", q_.get("exchange", "")),
                                    ))
                            btn_s.config(state="normal")
                        popup.after(0, _popola)
                    import threading
                    threading.Thread(target=_worker, daemon=True).start()
                def _seleziona(event=None):
                    sel = tv.selection()
                    if not sel:
                        return
                    ticker = tv.item(sel[0])["values"][0]
                    var_ticker.set(ticker)
                    popup.destroy()

                btn_s.bind("<Button-1>", lambda e: _esegui_ricerca())
                ent_q.bind("<Return>", lambda e: _esegui_ricerca())
                tv.bind("<Double-1>", _seleziona)
                ent_q.focus_set()              
            def _salva():
                ticker = vars_["ticker"].get().strip().upper()
                if not ticker:
                    self.show_toast("Ticker obbligatorio..")
                    return
                if any(t["ticker"] == ticker for t in dati["titoli"]):
                    self.show_toast(f"Ticker {ticker} già presente..")
                    return
                try:
                    target = float(vars_["target_pct"].get().replace(",",".") or 0)
                except ValueError:
                    target = 0.0
                dati["titoli"].append({
                    "ticker":      ticker,
                    "descrizione": vars_["descrizione"].get().strip(),
                    "isin":        vars_["isin"].get().strip(),
                    "asset_class": vars_["asset_class"].get().strip() or "Altro",
                    "target_pct":  target,
                    "movimenti":   [],
                    "dividendi":   [],
                })
                self._porta_save(dati)
                dlg.destroy()
                _refresh_all()
            frm_act = tk.Frame(dlg, bg=self.COLOR_BACKGROUND)
            frm_act.pack(pady=10)
            for testo, cmd, ico in [(" Salva",  _salva,      "salva"),
                                    (" Chiudi", dlg.destroy, "chiudi")]:
                img = self.icone_gui.get(ico)
                b = tk.Label(frm_act, text=testo, image=img, compound="left",
                             bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                             font=("Segoe UI", 10, "bold"), cursor="hand2",
                             padx=15, pady=8)
                b.image = img
                b.pack(side="left", padx=6)
                b.bind("<Button-1>", lambda e, c=cmd: c())    
        def _dlg_nuovo_movimento(ticker_pre=None):
            if not dati["titoli"]:
                self.show_toast("Aggiungi prima un titolo.")
                return
            dlg = tk.Toplevel(win)
            dlg.withdraw()
            dlg.title("Registra Movimento")
            dlg.configure(bg=self.COLOR_BACKGROUND)
            w_dlg, h_dlg = 360, 400
            win.update_idletasks()
            x = win.winfo_x() + (win.winfo_width() // 2) - (w_dlg // 2)
            y = win.winfo_y() + (win.winfo_height() // 2) - (h_dlg // 2)
            dlg.geometry(f"{w_dlg}x{h_dlg}+{max(0, x)}+{max(0, y)}")
            dlg.resizable(False, False)
            dlg.transient(win)
            dlg.bind("<Escape>", lambda e: dlg.destroy())
            dlg.deiconify()
            import datetime
            campi_label = ["Ticker","Tipo (acquisto/vendita)","Data (GG-MM-AAAA)",
                           "Quantità","Prezzo €","Commissioni €","Note"]
            campi_key   = ["ticker","tipo","data","quantita","prezzo","commissioni","note"]
            defaults    = [ticker_pre if ticker_pre else dati["titoli"][0]["ticker"],"acquisto",
                           datetime.date.today().strftime("%d-%m-%Y"),
                           "","","0",""]
            vars_ = {}
            for label, key, default in zip(campi_label, campi_key, defaults):
                tk.Label(dlg, text=label, bg=self.COLOR_BACKGROUND,
                         fg=self.TEXT_COLOR, font=("Segoe UI", 9)).pack(anchor="w", padx=16, pady=(6,0))
                v = tk.StringVar(value=default)
                vars_[key] = v
                if key == "ticker":
                    ttk.Combobox(dlg, textvariable=v,
                                 values=[t["ticker"] for t in dati["titoli"]],
                                 state="readonly", style="Border.TCombobox").pack(fill="x", padx=16)
                elif key == "tipo":
                    ttk.Combobox(dlg, textvariable=v,
                                 values=["acquisto","vendita"],
                                 state="readonly", style="Border.TCombobox").pack(fill="x", padx=16)
                elif key == "data":
                    frame_data = tk.Frame(dlg, bg=self.COLOR_BACKGROUND)
                    frame_data.pack(fill="x", padx=16)
                    ent = ttk.Entry(frame_data, textvariable=v, font=("Segoe UI", 10))
                    ent.pack(side="left", expand=True, fill="x", padx=(0, 5))
                    lbl_cal = tk.Label(frame_data, image=self.icone_gui.get("calendario"), 
                                       bg=self.COLOR_BACKGROUND, cursor="hand2")
                    lbl_cal.image = self.icone_gui.get("calendario")
                    lbl_cal.pack(side="left")
                    lbl_cal.bind("<Button-1>", lambda event, e=ent, var=v: self.mostra_calendario_popup_semplice(e, var))
                    self.btn_cal_btm = lbl_cal
                else:
                    ttk.Entry(dlg, textvariable=v, font=("Segoe UI", 10)).pack(fill="x", padx=16)
            def _salva():
                import uuid, datetime
                ticker = vars_["ticker"].get().strip().upper()
                tipo   = vars_["tipo"].get().strip().lower()
                try:
                    datetime.datetime.strptime(vars_["data"].get(), "%d-%m-%Y")
                except ValueError:
                    self.show_toast("Data non valida. Formato: GG-MM-AAAA.")
                    return
                try:
                    q = float(vars_["quantita"].get().replace(",","."))
                    p = float(vars_["prezzo"].get().replace(",","."))
                    c = float(vars_["commissioni"].get().replace(",",".") or 0)
                except ValueError:
                    self.show_toast("Quantità/Prezzo non validi.")
                    return
                for t in dati["titoli"]:
                    if t["ticker"] == ticker:
                        t.setdefault("movimenti", []).append({
                            "id":           str(uuid.uuid4())[:8],
                            "data":         vars_["data"].get(),
                            "tipo":         tipo,
                            "quantita":     q,
                            "prezzo":       p,
                            "commissioni":  c,
                            "note":         vars_["note"].get().strip(),
                        })
                        break
                self._porta_save(dati)
                dlg.destroy()
                _refresh_all()
            frm_act = tk.Frame(dlg, bg=self.COLOR_BACKGROUND)
            frm_act.pack(pady=10)
            for testo, cmd, ico in [(" Salva",  _salva,      "salva"),
                                    (" Chiudi", dlg.destroy, "chiudi")]:
                img = self.icone_gui.get(ico)
                b = tk.Label(frm_act, text=testo, image=img, compound="left",
                             bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                             font=("Segoe UI", 10, "bold"), cursor="hand2",
                             padx=15, pady=8, relief="flat")
                b.image = img
                b.pack(side="left", padx=6)
                b.bind("<Button-1>", lambda e, c=cmd: c())
        def _dlg_nuovo_dividendo():
            if not dati["titoli"]:
                self.show_toast("Aggiungi prima un titolo.")
                return
            dlg = tk.Toplevel(win)
            dlg.withdraw()
            dlg.title("Registra Dividendo")
            dlg.configure(bg=self.COLOR_BACKGROUND)
            w_dlg, h_dlg = 360, 390
            win.update_idletasks()
            x = win.winfo_x() + (win.winfo_width() // 2) - (w_dlg // 2)
            y = win.winfo_y() + (win.winfo_height() // 2) - (h_dlg // 2)
            dlg.geometry(f"{w_dlg}x{h_dlg}+{max(0, x)}+{max(0, y)}")
            dlg.resizable(False, False)
            dlg.transient(win)
            dlg.bind("<Escape>", lambda e: dlg.destroy())
            dlg.deiconify()
            import datetime
            campi_label = ["Ticker","Data (GG-MM-AAAA)","Importo Lordo €",
                           "Ritenuta €","Importo Netto €"]
            campi_key   = ["ticker","data","importo_lordo","ritenuta","importo_netto"]
            defaults    = [dati["titoli"][0]["ticker"],
                           datetime.date.today().strftime("%d-%m-%Y"),
                           "","",""]
            vars_ = {}
            for i, (label, key, default) in enumerate(zip(campi_label, campi_key, defaults)):
                tk.Label(dlg, text=label, bg=self.COLOR_BACKGROUND, fg=self.COLOR_TEXT).pack(pady=(10, 0))
                v = tk.StringVar(value=default)
                vars_[key] = v
                if key == "data":
                    frame_data = tk.Frame(dlg, bg=self.COLOR_BACKGROUND)
                    frame_data.pack(pady=5)
                    ent = ttk.Entry(frame_data, textvariable=v, width=22, font=("Segoe UI", 10))
                    ent.pack(side="left", padx=(0, 2))
                    img_cal = self.icone_gui.get("calendario") 
                    lbl_cal = tk.Label(
                        frame_data, 
                        image=img_cal,
                        bg=self.COLOR_BACKGROUND, 
                        cursor="hand2"
                    )
                    lbl_cal.image = img_cal 
                    lbl_cal.pack(side="left")
                    lbl_cal.bind("<Button-1>", lambda event, e=ent, var=v: self.mostra_calendario_popup_semplice(e, var))
                elif key == "ticker":
                    ttk.Combobox(dlg, textvariable=v,
                                 values=[t["ticker"] for t in dati["titoli"]],
                                 state="readonly", width=25, style="Border.TCombobox").pack(pady=5)
                else:
                    ent = ttk.Entry(dlg, textvariable=v, width=25, font=("Segoe UI", 10))
                    ent.pack(pady=5)
                def _calc_netto(*_):
                    try:
                       lordo    = float(vars_["importo_lordo"].get().replace(",",".") or 0)
                       ritenuta = float(vars_["ritenuta"].get().replace(",",".") or 0)
                       vars_["importo_netto"].set(f"{lordo - ritenuta:.2f}")
                    except Exception:
                        pass
            vars_["importo_lordo"].trace_add("write", _calc_netto)
            vars_["ritenuta"].trace_add("write", _calc_netto)
            def _salva():
                import datetime
                ticker = vars_["ticker"].get().strip().upper()
                try:
                    datetime.datetime.strptime(vars_["data"].get(), "%d-%m-%Y")
                except ValueError:
                    self.show_toast("Data non valida. Formato: GG-MM-AAAA.")
                    return
                try:
                    lordo    = float(vars_["importo_lordo"].get().replace(",","."))
                    ritenuta = float(vars_["ritenuta"].get().replace(",",".") or 0)
                    netto    = float(vars_["importo_netto"].get().replace(",","."))
                except ValueError:
                    self.show_toast("Importi non validi.")
                    return
                for t in dati["titoli"]:
                    if t["ticker"] == ticker:
                        t.setdefault("dividendi", []).append({
                            "data":          vars_["data"].get(),
                            "importo_lordo": lordo,
                            "ritenuta":      ritenuta,
                            "importo_netto": netto,
                        })
                        break
                self._porta_save(dati)
                dlg.destroy()
                _refresh_all()
            frm_act = tk.Frame(dlg, bg=self.COLOR_BACKGROUND)
            frm_act.pack(pady=10)
            for testo, cmd, ico in [(" Salva",  _salva,      "salva"),
                                    (" Chiudi", dlg.destroy, "chiudi")]:
                img = self.icone_gui.get(ico)
                b = tk.Label(frm_act, text=testo, image=img, compound="left",
                             bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                             font=("Segoe UI", 10, "bold"), cursor="hand2",
                             padx=15, pady=8)
                b.image = img
                b.pack(side="left", padx=6)
                b.bind("<Button-1>", lambda e, c=cmd: c())
        def _rimuovi_titolo():
            if not hasattr(tab_porta, "_tv"):
                return
            sel = tab_porta._tv.selection()
            if not sel:
                self.show_toast("Seleziona un titolo dalla lista.")
                return
            ticker = tab_porta._tv.item(sel[0])["values"][0]
            if ticker == "TOTALE":
                return
            if not self.show_custom_askyesno("Conferma",
                    f"Rimuovere {ticker} con tutti i suoi movimenti e dividendi?"):
                return
            dati["titoli"] = [t for t in dati["titoli"] if t["ticker"] != ticker]
            self._porta_save(dati)
            _refresh_all()
        def _aggiorna_prezzi():
            if stato["aggiornamento"]:
                self.show_toast("Aggiornamento già in corso...")
                return
            stato["aggiornamento"] = True
            self.show_toast("Download dati di mercato...")
            def _worker():
                for t in dati["titoli"]:
                    ticker = t["ticker"]
                    p = self._porta_prezzo_live(ticker)
                    if p:
                        prezzi_live[ticker] = p
                        t["ultimo_prezzo"]  = p
                try:
                    self._porta_save(dati)
                except Exception as e:
                    print(f"[PORTAFOGLIO] Errore salvataggio prezzi: {e}")
                win.after(0, _dopo_aggiornamento)
            def _dopo_aggiornamento():
                stato["aggiornamento"] = False
                non_trovati = [t["ticker"] for t in dati["titoli"]
                               if prezzi_live.get(t["ticker"]) is None]
                if non_trovati:
                    self.show_custom_warning("Prezzi non trovati",
                        "Nessun prezzo live trovato per:\n\n" +
                        "\n".join(f"  • {tk}" for tk in non_trovati) +
                        "\n\nVerifica che il ticker sia corretto (es. VWCE.AS, AAPL).")
                else:
                    self.show_toast("Prezzi aggiornati.")
                _refresh_all()
            import threading
            threading.Thread(target=_worker, daemon=True).start()
        def _anteprima():
            titoli_calcolati = []
            tot_investito = tot_attuale = tot_dividendi = 0.0
            for t in dati["titoli"]:
                c = self._porta_calcola_titolo(t, prezzi_live.get(t["ticker"]))
                titoli_calcolati.append(c)
                tot_investito += c["investito"]
                tot_attuale   += c["valore_attuale"]
                tot_dividendi += c["dividendi_netti"]
            pl_tot     = tot_attuale - tot_investito
            pl_pct_tot = (pl_tot / tot_investito * 100) if tot_investito > 0 else 0.0
            rend_reale = pl_tot + tot_dividendi
            soglia     = float(dati["impostazioni"].get("soglia_ribilanciamento", 2.0))
            def fmt(v):
                return f"€ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")
            def fmt_pct(v):
                return f"{v:+.2f}%"
            ts = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
            def _build_testo():
                SEP  = "─" * 110
                SEP2 = "─" * 70
                lines = []
                lines.append(f"PORTAFOGLIO INVESTIMENTI — {ts}")
                lines.append("═" * 110)
                lines.append("\n── KPI " + "─" * 103)
                lines.append(f"  {'Investito':<22}: {fmt(tot_investito)}")
                lines.append(f"  {'Valore Attuale':<22}: {fmt(tot_attuale)}")
                lines.append(f"  {'P&L €':<22}: {fmt(pl_tot)}  ({fmt_pct(pl_pct_tot)})")
                lines.append(f"  {'Dividendi Incassati':<22}: {fmt(tot_dividendi)}")
                lines.append(f"  {'Rendimento Reale':<22}: {fmt(rend_reale)}")
                lines.append("\n── PORTAFOGLIO " + "─" * 95)
                hdr = (f"{'Ticker':<10}  {'Descrizione':<24}  {'Qtà':>12}  "
                       f"{'PMC':>12}  {'Prezzo':>12}  {'Valore €':>12}  "
                       f"{'Invest. €':>12}  {'P&L €':>12}  {'P&L %':>8}")
                lines.append(hdr)
                lines.append(SEP)
                for c in titoli_calcolati:
                    lines.append(
                        f"{c['ticker']:<10}  "
                        f"{c['descrizione'][:24]:<24}  "
                        f"{c['quantita']:>12.4f}  "
                        f"{c['pmc']:>12.4f}  "
                        f"{c['prezzo_attuale']:>12.4f}  "
                        f"{c['valore_attuale']:>12,.2f}  "
                        f"{c['investito']:>12,.2f}  "
                        f"{c['pl_eur']:>+12,.2f}  "
                        f"{c['pl_pct']:>+7.2f}%"
                    )
                lines.append(SEP)
                lines.append(
                    f"{'TOTALE':<10}  {'':24}  {'':>12}  {'':>12}  {'':>12}  "
                    f"{tot_attuale:>12,.2f}  "
                    f"{tot_investito:>12,.2f}  "
                    f"{pl_tot:>+12,.2f}  "
                    f"{pl_pct_tot:>+7.2f}%"
                )
                lines.append("\n── ALLOCAZIONE & RIBILANCIAMENTO " + "─" * 77)
                hdr_r = f"  {'Ticker':<10}  {'Attuale %':>10}  {'Target %':>10}  {'Scost.':>10}  Stato"
                lines.append(hdr_r)
                lines.append("  " + "─" * 60)
                for c in titoli_calcolati:
                    att = (c["valore_attuale"] / tot_attuale * 100) if tot_attuale > 0 else 0
                    tgt = c["target_pct"]
                    sc  = att - tgt
                    if tgt == 0:
                        stato_s = "⚪  —"
                    elif abs(sc) <= soglia:
                        stato_s = "🟢  OK"
                    elif abs(sc) <= soglia * 2:
                        stato_s = "🟡  Attenzione"
                    else:
                        stato_s = "🔴  Ribilancia"
                    lines.append(
                        f"  {c['ticker']:<10}  "
                        f"{att:>9.2f}%  "
                        f"{f'{tgt:.1f}%' if tgt else '-':>10}  "
                        f"{f'{sc:+.2f}%' if tgt else '-':>10}  "
                        f"{stato_s}"
                    )
                lines.append("\n── MOVIMENTI " + "─" * 97)
                hdr2 = (f"{'Data':<12}  {'Ticker':<10}  {'Tipo':<10}  "
                        f"{'Qtà':>12}  {'Prezzo':>12}  {'Comm.':>8}  {'Totale €':>12}  Note")
                lines.append(hdr2)
                lines.append(SEP)
                tutti_mov = []
                for t in dati["titoli"]:
                    for m in t.get("movimenti", []):
                        tutti_mov.append((m.get("data", ""), t["ticker"], m))
                for data, ticker, m in sorted(tutti_mov, key=lambda x: x[0], reverse=True):
                    q   = float(m.get("quantita", 0))
                    p   = float(m.get("prezzo", 0))
                    com = float(m.get("commissioni", 0))
                    tot = q * p + (com if m.get("tipo") == "acquisto" else -com)
                    lines.append(
                        f"{data:<12}  "
                        f"{ticker:<10}  "
                        f"{m.get('tipo','').capitalize():<10}  "
                        f"{q:>12.4f}  "
                        f"{p:>12.4f}  "
                        f"{com:>8.2f}  "
                        f"{tot:>12,.2f}  "
                        f"{m.get('note', '')}"
                    )
                lines.append("\n── DIVIDENDI " + "─" * 97)
                hdr3 = f"{'Data':<12}  {'Ticker':<10}  {'Lordo €':>12}  {'Ritenuta €':>12}  {'Netto €':>12}"
                lines.append(hdr3)
                lines.append(SEP2)
                tot_netto = 0.0
                righe_div = []
                for t in dati["titoli"]:
                    for d in t.get("dividendi", []):
                        lordo    = float(d.get("importo_lordo", d.get("importo", 0)))
                        ritenuta = float(d.get("ritenuta", 0))
                        netto    = float(d.get("importo_netto", lordo - ritenuta))
                        righe_div.append((d.get("data", ""), t["ticker"], lordo, ritenuta, netto))
                        tot_netto += netto
                for r in sorted(righe_div, key=lambda x: x[0], reverse=True):
                    lines.append(
                        f"{r[0]:<12}  {r[1]:<10}  "
                        f"{r[2]:>12,.2f}  {r[3]:>12,.2f}  {r[4]:>12,.2f}"
                    )
                lines.append(SEP2)
                lines.append(f"{'TOTALE':<12}  {'':10}  {'':>12}  {'':>12}  {tot_netto:>12,.2f}")
                return "\n".join(lines)
            testo = _build_testo()
            popup_width = 1300
            popup_height = 620
            screen_width = self.winfo_screenwidth()
            screen_height = self.winfo_screenheight()
            center_x = int((screen_width / 2) - (popup_width / 2))
            center_y = int((screen_height / 2) - (popup_height / 2))
            prev = tk.Toplevel(win, bg=self.COLOR_TOPLEVEL)
            prev.title("Anteprima Report")
            prev.geometry(f"{popup_width}x{popup_height}+{center_x}+{center_y}")
            prev.minsize(popup_width, popup_height)
            prev.transient(win)
            prev.bind("<Escape>", lambda e: prev.destroy())
            text_frame = tk.Frame(prev)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))
            text_frame.grid_rowconfigure(0, weight=1)
            text_frame.grid_columnconfigure(0, weight=1)
            vsb_text = ttk.Scrollbar(text_frame, orient="vertical", style="Vertical.TScrollbar")
            vsb_text.grid(row=0, column=1, sticky="ns")
            hsb_text = ttk.Scrollbar(text_frame, orient="horizontal", style="Horizontal.TScrollbar")
            hsb_text.grid(row=1, column=0, sticky="ew")
            txt = tk.Text(text_frame, font=("Courier New", 9), wrap="none",
                          yscrollcommand=vsb_text.set, xscrollcommand=hsb_text.set)
            txt.grid(row=0, column=0, sticky="nsew")
            vsb_text.config(command=txt.yview)
            hsb_text.config(command=txt.xview)
            txt.insert(tk.END, testo)
            txt.config(state="disabled")
            frm_act = tk.Frame(prev, bg=self.COLOR_TOPLEVEL)
            frm_act.pack(fill=tk.X, padx=10, pady=8)
            def _salva_txt():
                path = filedialog.asksaveasfilename(
                    parent=prev, defaultextension=".txt",
                    filetypes=[("Testo", "*.txt")],
                    confirmoverwrite=False,
                    initialfile=f"portafoglio_{datetime.date.today()}.txt")
                if not path:
                    return
                with open(path, "w", encoding="utf-8") as f:
                    f.write(testo)
                self.show_toast("TXT salvato.")
            def _salva_pdf():
                path = filedialog.asksaveasfilename(
                    parent=prev, defaultextension=".pdf",
                    filetypes=[("PDF", "*.pdf")],
                    initialdir=EXPORT_FILES,
                    confirmoverwrite=False,
                    initialfile=f"portafoglio_{datetime.date.today()}.pdf")
                if not path:
                    return
                try:
                    import fitz
                    doc = fitz.open()
                    page_w, page_h = 842, 595
                    margin = 40
                    font_size = 7
                    line_height = font_size + 2
                    page = doc.new_page(width=page_w, height=page_h)
                    y = margin
                    for line in testo.split("\n"):
                        if y > (page_h - margin):
                            page = doc.new_page(width=page_w, height=page_h)
                            y = margin
                        page.insert_text((margin, y), line, fontname="cour", fontsize=font_size)
                        y += line_height
                    doc.save(path)
                    doc.close()
                    self.show_toast("PDF salvato.")
                except Exception as e:
                    self.show_custom_warning("Errore", str(e))
            def _stampa():
                self._stampa_lista_diretta(testo, self.show_custom_warning)
            for label, ico, cmd, side in [
                (" Chiudi",      "chiudi", prev.destroy, "right"),
                (" Esporta PDF", "salva",  _salva_pdf,   "left"),
                (" Esporta TXT", "salva",  _salva_txt,   "left"),
                (" Stampa",      "stampa", _stampa,      "left"),
            ]:
                img = self.icone_gui.get(ico)
                b = tk.Label(frm_act, compound="left", image=img,
                             text=label, background=self.COLOR_WIDGET_BG,
                             foreground=self.TEXT_COLOR, cursor="hand2",
                             padx=15, pady=6, font=("Arial", 9, "bold"))
                b.image = img
                b.pack(side=side, padx=6)
                b.bind("<Button-1>", lambda e, c=cmd: c())
            prev.lift()
            prev.focus_force()
            prev.attributes('-topmost', True)
            prev.after(100, lambda: prev.attributes('-topmost', False))          
        def _esporta_json():
            path = filedialog.asksaveasfilename(
                parent=win, defaultextension=".json",
                initialdir=EXP_DB,
                filetypes=[("JSON", "*.json")],
                confirmoverwrite=False,
                initialfile=f"portafoglio_{datetime.date.today()}.json")
            if not path:
                return
            with open(path, "w", encoding="utf-8") as f:
                json.dump(dati, f, indent=2, ensure_ascii=False)
            self.show_toast("Portafoglio esportato.")
        def _importa_json():
            path = filedialog.askopenfilename(
                initialdir=EXP_DB,
                parent=win, filetypes=[("JSON", "portafoglio*.json")])
            if not path:
                return
            try:
                with open(path, "r", encoding="utf-8") as f:
                    nuovo = json.load(f)
                if "titoli" not in nuovo:
                    self.show_toast("File non valido.")
                    return
            except Exception as e:
                self.show_toast(f"Errore lettura: {e}")
                return
            if not self.show_custom_askyesno("Importa",
                    "Sovrascrivere il portafoglio attuale con il file importato?"):
                return
            dati.clear()
            dati.update(nuovo)
            self._porta_save(dati)
            _refresh_all()
            self.show_toast("Portafoglio importato.")
        def _reset_portafoglio():
            if not self.show_custom_askyesno("Reset",
                    "Azzerare completamente il portafoglio? L'operazione è irreversibile."):
                return
            dati.clear()
            dati.update({"impostazioni": {"valuta": "EUR", "soglia_ribilanciamento": 2.0}, "titoli": []})
            self._porta_save(dati)
            _refresh_all()
            self.show_toast("Portafoglio azzerato.")
        img_anteprima = self.icone_gui.get("salva")
        btn_anteprima = ttk.Label(
            button_frame,
            compound="left",
            image=img_anteprima,
            text=" Esporta",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2",
            padding=(15, 7)
        )
        btn_anteprima.image = img_anteprima
        btn_anteprima.grid(row=0, column=0, padx=5)
        btn_anteprima.bind("<Button-1>", lambda e: _anteprima())
        img_ia = self.icone_gui.get("ia") or self.icone_gui.get("api_key")
        btn_ia = ttk.Label(
            button_frame,
            compound="left",
            image=img_ia,
            text=" Analisi AI",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2",
            padding=(15, 7)
        )
        btn_ia.image = img_ia
        btn_ia.grid(row=0, column=1, padx=5)
        btn_ia.bind("<Button-1>", lambda e: _analisi_ia())
        img_help = self.icone_gui.get("help")
        btn_help = ttk.Label(
            button_frame,
            compound="left",
            image=img_help,
            text=" Guida",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2",
            padding=(15, 7)
        )
        btn_help.image = img_help
        btn_help.grid(row=0, column=2, padx=5)
        btn_help.bind("<Button-1>", lambda e: _mostra_help())
        img_chiudi_cfg = self.icone_gui.get("chiudi")
        btn_chiudi = ttk.Label(
            button_frame,
            compound="left",
            image=img_chiudi_cfg,
            text=" Chiudi" if img_chiudi_cfg else "Chiudi",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2",
            padding=(15, 7)
        )
        btn_chiudi.image = img_chiudi_cfg
        btn_chiudi.grid(row=0, column=3, padx=5)
        def _chiudi_finestra(e=None):
            win.destroy()
        btn_chiudi.bind("<Button-1>", _chiudi_finestra)
        win.bind("<Escape>", _chiudi_finestra)
        
        def _analisi_ia():
            if not API_KEY:
                self.show_custom_warning("AI", "Configura prima la chiave API Gemini nelle impostazioni.")
                return
            titoli_calcolati = []
            tot_investito = tot_attuale = tot_dividendi = 0.0
            for t in dati["titoli"]:
                c = self._porta_calcola_titolo(t, prezzi_live.get(t["ticker"]))
                titoli_calcolati.append(c)
                tot_investito += c["investito"]
                tot_attuale   += c["valore_attuale"]
                tot_dividendi += c["dividendi_netti"]
            pl_tot     = tot_attuale - tot_investito
            pl_pct_tot = (pl_tot / tot_investito * 100) if tot_investito > 0 else 0.0
            rend_reale = pl_tot + tot_dividendi
            soglia     = float(dati["impostazioni"].get("soglia_ribilanciamento", 2.0))
            riepilogo  = (
                f"PORTAFOGLIO:\n"
                f"Investito: €{tot_investito:,.2f} | Valore attuale: €{tot_attuale:,.2f}\n"
                f"P&L: €{pl_tot:+,.2f} ({pl_pct_tot:+.2f}%) | Dividendi: €{tot_dividendi:,.2f} | "
                f"Rendimento reale: €{rend_reale:+,.2f}\n"
                f"Soglia ribilanciamento: {soglia}%\n\nTITOLI:"
            )
            for c in titoli_calcolati:
                att_pct = (c["valore_attuale"] / tot_attuale * 100) if tot_attuale > 0 else 0
                riepilogo += (
                    f"\n• {c['ticker']} ({c['asset_class']}) — "
                    f"qtà {c['quantita']:.4f}, PMC €{c['pmc']:.4f}, prezzo €{c['prezzo_attuale']:.4f}, "
                    f"valore €{c['valore_attuale']:,.2f}, P&L {c['pl_pct']:+.2f}%, "
                    f"alloc {att_pct:.1f}% su target {c['target_pct']:.1f}%"
                )
            hlp_ia = tk.Toplevel(win)
            hlp_ia.title("Analisi AI Portafoglio")
            hlp_ia.configure(bg=self.COLOR_BACKGROUND)
            hlp_ia.transient(win)
            hlp_ia.minsize(1200, 620)
            hlp_ia.bind("<Escape>", lambda e: (hlp_ia.destroy(), "break") or "break")
            w, h = 1200, 620
            self.update_idletasks()
            x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
            y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
            hlp_ia.geometry(f"{w}x{h}+{x}+{y}")

            frm_top = tk.Frame(hlp_ia, bg=self.COLOR_BACKGROUND)
            frm_top.pack(fill="x", padx=10, pady=(10, 4))
            tk.Label(frm_top, text="Chiedi all'AI:", bg=self.COLOR_BACKGROUND,
                     fg=self.TEXT_COLOR, font=("Segoe UI", 9)).pack(side="left")
            domanda_var = tk.StringVar()
            entry_dom = tk.Entry(frm_top, textvariable=domanda_var,
                                 font=("Segoe UI", 10), width=50)
            entry_dom.pack(side="left", padx=(6, 4))
            img_invia = self.icone_gui.get("conferma") or self.icone_gui.get("descrizione")
            btn_invia = tk.Label(frm_top, compound="left", image=img_invia,
                                 text=" Invia", bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                                 cursor="hand2", padx=8, pady=4, font=("Segoe UI", 9))
            btn_invia.image = img_invia
            btn_invia.pack(side="left", padx=(0, 4))
            frm_txt = tk.Frame(hlp_ia, bg=self.COLOR_BACKGROUND)
            frm_txt.pack(fill="both", expand=True, padx=10, pady=4)
            vsb_txt = ttk.Scrollbar(frm_txt, orient="vertical", style="Vertical.TScrollbar")
            vsb_txt.pack(side="right", fill="y")
            txt = tk.Text(frm_txt, font=("Segoe UI", 9), wrap="word",
                          bg=self.COLOR_WHITE, fg=self.COLOR_BLACK,
                          relief="flat", padx=14, pady=10,
                          yscrollcommand=vsb_txt.set)
            txt.pack(fill="both", expand=True)
            vsb_txt.config(command=txt.yview)
            frm_btn = tk.Frame(hlp_ia, bg=self.COLOR_BACKGROUND)
            frm_btn.pack(fill="x", padx=10, pady=(0, 10))
            state = {"running": False}
            def _chiama_ia(tipo):
                if state["running"]:
                    return
                state["running"] = True
                txt.config(state="normal")
                txt.delete("1.0", "end")
                txt.insert("end", "⏳ Analisi in corso…")
                txt.config(state="disabled")
                hlp_ia.update()
                if tipo == "portafoglio":
                    prompt = (
                        f"Sei un consulente finanziario. Analizza questo portafoglio di investimenti "
                        f"e fornisci: 1) commento sulla diversificazione, 2) rischi principali, "
                        f"3) suggerimenti di ribilanciamento concreti, 4) valutazione generale. "
                        f"Rispondi in italiano, in modo chiaro e diretto.\n\n{riepilogo}"
                    )
                elif tipo == "pl":
                    prompt = (
                        f"Sei un consulente finanziario. Commenta il P&L di questo portafoglio: "
                        f"spiega se la performance è buona o no, confronta con benchmark comuni "
                        f"(es. MSCI World), e dai suggerimenti per migliorare il rendimento. "
                        f"Rispondi in italiano.\n\n{riepilogo}"
                    )
                elif tipo == "ticker":
                    desc = domanda_var.get().strip()
                    if not desc:
                        txt.config(state="normal")
                        txt.delete("1.0", "end")
                        txt.insert("end", "⚠️ Scrivi una descrizione nel campo di testo in alto.")
                        txt.config(state="disabled")
                        state["running"] = False
                        return
                    prompt = (
                        f"Sei un esperto di mercati finanziari. L'utente cerca un ETF o titolo "
                        f"con questa descrizione: '{desc}'. "
                        f"Suggerisci 3-5 ticker adatti (con borsa, es. VWCE.AS per Euronext Amsterdam), "
                        f"spiegando brevemente cosa è ciascuno e perché è adatto. "
                        f"Tieni conto che l'utente è italiano quindi preferisci titoli disponibili "
                        f"su borse europee. Rispondi in italiano."
                    )
                elif tipo == "domanda":
                    dom = domanda_var.get().strip()
                    if not dom:
                        txt.config(state="normal")
                        txt.delete("1.0", "end")
                        txt.insert("end", "⚠️ Scrivi una domanda nel campo di testo in alto.")
                        txt.config(state="disabled")
                        state["running"] = False
                        return
                    prompt = (
                        f"Sei un consulente finanziario. Rispondi a questa domanda dell'utente "
                        f"tenendo conto del suo portafoglio attuale. Rispondi in italiano.\n\n"
                        f"PORTAFOGLIO:\n{riepilogo}\n\nDOMANDA: {dom}"
                    )
                def _worker_ia():
                    try:
                        client = genai.Client(api_key=API_KEY)
                        response = client.models.generate_content(model=GEMINI, contents=prompt)
                        risposta = response.text.strip()
                    except Exception as e:
                        risposta = f"❌ Errore: {e}"
                    hlp_ia.after(0, lambda: _mostra(risposta) if hlp_ia.winfo_exists() else None)
                def _mostra(risposta):
                    state["running"] = False
                    txt.config(state="normal")
                    txt.delete("1.0", "end")
                    txt.insert("end", risposta)
                    txt.config(state="disabled")
                import threading
                threading.Thread(target=_worker_ia, daemon=True).start()
            btn_invia.bind("<Button-1>", lambda e: _chiama_ia("domanda"))
            entry_dom.bind("<Return>",   lambda e: _chiama_ia("domanda"))
            for col, (testo, tipo, icona) in enumerate([
                (" Analizza portafoglio", "portafoglio", "search"),
                (" Commenta P&L",         "pl",          "lavoro"),
                (" Suggerisci ticker",    "ticker",      "scadenze"),
                (" Fai una domanda",      "domanda",     "tools"),
            ]):
                img = self.icone_gui.get(icona)
                b = tk.Label(frm_btn, compound="left", image=img, text=testo,
                             bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                             cursor="hand2", padx=10, pady=5, font=("Segoe UI", 9))
                b.image = img
                b.grid(row=0, column=col, padx=4)
                b.bind("<Button-1>", lambda e, t=tipo: _chiama_ia(t))
            img_c = self.icone_gui.get("chiudi")
            bc = tk.Label(frm_btn, compound="left", image=img_c, text=" Chiudi",
                          bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                          cursor="hand2", padx=12, pady=5, font=("Segoe UI", 9))
            bc.image = img_c
            bc.grid(row=0, column=4, padx=(20, 4))
            bc.bind("<Button-1>", lambda e: hlp_ia.destroy())

        def _mostra_help():
            hlp = tk.Toplevel(win)
            hlp.withdraw()
            hlp.title("Guida Portafoglio")
            hlp.configure(bg=self.COLOR_BACKGROUND)
            w_hlp, h_hlp = 1100, 630
            win.update_idletasks()
            main_x = win.winfo_rootx()
            main_y = win.winfo_rooty()
            main_w = win.winfo_width()
            main_h = win.winfo_height()
            pos_x = main_x + (main_w // 2) - (w_hlp // 2)
            pos_y = main_y + (main_h // 2) - (h_hlp // 2)
            hlp.geometry(f"{w_hlp}x{h_hlp}+{max(0, pos_x)}+{max(0, pos_y)}")
            hlp.deiconify()
            hlp.transient(win)
            hlp.bind("<Escape>", lambda e: hlp.destroy())
            container = tk.Frame(hlp, bg=self.COLOR_WHITE)
            container.pack(fill="both", expand=True, padx=10, pady=(10, 10))
            sb = ttk.Scrollbar(container, orient="vertical")
            sb.pack(side="right", fill="y")
            txt = tk.Text(container, font=("Segoe UI", 10), wrap="word",
                          bg=self.COLOR_WHITE, fg=self.COLOR_BLACK,
                          relief="flat", padx=14, pady=10,
                          yscrollcommand=sb.set)
            txt.pack(side="left", fill="both", expand=True)
            sb.config(command=txt.yview)
            guida = """PORTAFOGLIO INVESTIMENTI — GUIDA RAPIDA
── DASHBOARD ──────────────────────────────────────
Mostra i KPI principali: capitale investito, valore attuale, P&L in € e %, dividendi incassati e rendimento reale (P&L + dividendi netti).
Il grafico a torta mostra la composizione del portafoglio per peso attuale.
La tabella di ribilanciamento segnala gli scostamenti rispetto ai target
impostati per ogni titolo, con tre livelli:
  🟢 OK — scostamento entro la soglia
  🟡 Attenzione — scostamento entro il doppio della soglia
  🔴 Ribilancia — scostamento superiore al doppio della soglia
La soglia di ribilanciamento (default 2%) si imposta nel file di configurazione.
── PORTAFOGLIO ────────────────────────────────────
Elenco di tutti i titoli con quantità, P.M.C., prezzo attuale, valore,
investito e P&L. Riga TOTALE in fondo con i valori aggregati.
- Aggiungi Titolo: inserisci ticker, descrizione, ISIN, asset class e target % di allocazione. Il campo ticker include un pulsante 🔍 per
  cercare il ticker corretto tramite Yahoo Finance (ricerca per nome o ISIN).
- Aggiorna Prezzi: scarica i prezzi live da Yahoo Finance per tutti i titoli.
  I prezzi vengono salvati come ultimo prezzo noto.
- Rimuovi Titolo: seleziona una riga e rimuovi il titolo con tutti i suoi movimenti e dividendi associati.
── MOVIMENTI ──────────────────────────────────────
Storico di acquisti e vendite per ogni titolo, filtrabile per ticker.
Il P.M.C. viene ricalcolato automaticamente ad ogni vendita (metodo FIFO sul costo medio). Le commissioni vengono incluse nel costo di carico
per gli acquisti. È possibile aggiungere una nota a ogni movimento.
── DIVIDENDI ──────────────────────────────────────
Registra i dividendi con importo lordo, ritenuta e netto.
L'importo netto viene calcolato automaticamente (lordo − ritenuta).
Il totale netto viene sommato nel rendimento reale del portafoglio.
── GRAFICI ────────────────────────────────────────
- 💰 Investito: evoluzione del capitale investito nel tempo.
- 📊 P&L stimato: P&L calcolato al prezzo attuale proiettato sullo storico degli acquisti (stima, non storico reale).
- 💵 Dividendi: dividendi incassati cumulativi nel tempo.
- 🏷️ Per Titolo: investito per singolo titolo nel tempo.
  Passa il mouse sul grafico per vedere i valori.
── MERCATI ────────────────────────────────────────
Visualizza i titoli dell'S&P 500 e del FTSE MIB con prezzi live, variazione giornaliera, open/high/low e volume. Selezionando un titolo 
si visualizza il grafico a 1 mese. Doppio clic o "Aggiungi al portafoglio" per inserire direttamente il titolo nel portafoglio.
── ANALISI AI ─────────────────────────────────────
Richiede una chiave API Gemini configurata nelle impostazioni.
Modalità disponibili:
- Analizza portafoglio: commento su diversificazione, rischi e ribilanciamento.
- Commenta P&L: valutazione della performance con confronto ai benchmark.
- Suggerisci ticker: suggerisce ETF o titoli in base a una descrizione libera.
- Fai una domanda: risposta libera dell'AI in base al tuo portafoglio attuale.
── ESPORTA ────────────────────────────────────────
Genera un report completo del portafoglio (KPI, titoli, movimenti, dividendi) esportabile in formato TXT o PDF, oppure stampabile direttamente.
── MENU DATI ──────────────────────────────────────
- Esporta JSON: salva il portafoglio completo su file.
- Importa JSON: ripristina un portafoglio da file (sovrascrive i dati attuali).
- Reset: azzera completamente il portafoglio."""
            txt.insert("1.0", guida)
            txt.config(state="disabled")
            img_c = self.icone_gui.get("chiudi")
            b = tk.Label(hlp, compound="left", image=img_c, text=" Chiudi",
                         bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                         cursor="hand2", padx=15, pady=6, font=("Arial", 9, "bold"))
            b.image = img_c
            b.pack(pady=8)
            b.bind("<Button-1>", lambda e: hlp.destroy())
        
        def _build_grafici():
            for w in tab_graf.winfo_children():
                w.destroy()
            import datetime as dt_mod
            eventi = []
            for t in dati["titoli"]:
                for m in t.get("movimenti", []):
                    try:
                        d = dt_mod.datetime.strptime(m["data"], "%d-%m-%Y").date()
                    except Exception:
                        continue
                    q = float(m.get("quantita", 0))
                    p = float(m.get("prezzo", 0))
                    c = float(m.get("commissioni", 0))
                    costo = q * p + c if m.get("tipo") == "acquisto" else -(q * p - c)
                    eventi.append((d, t["ticker"], m.get("tipo", ""), costo))
                for d_div in t.get("dividendi", []):
                    try:
                        d = dt_mod.datetime.strptime(d_div["data"], "%d-%m-%Y").date()
                    except Exception:
                        continue
                    netto = float(d_div.get("importo_netto", d_div.get("importo", 0)))
                    eventi.append((d, t["ticker"], "dividendo", netto))
            if not eventi:
                tk.Label(tab_graf, text="Nessun dato da visualizzare.",
                         bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
                         font=("Segoe UI", 11)).pack(expand=True)
                return
            eventi.sort(key=lambda x: x[0])
            date_uniche   = sorted(set(e[0] for e in eventi))
            inv_cum       = []
            pl_cum        = []
            div_cum       = []
            tickers_unici = list(dict.fromkeys(t["ticker"] for t in dati["titoli"]))
            serie_titoli  = {tk_: [] for tk_ in tickers_unici}
            inv_run       = 0.0
            div_run       = 0.0
            inv_x_tick    = {tk_: 0.0 for tk_ in tickers_unici}
            valore_att_attuale = sum(
                self._porta_calcola_titolo(t, prezzi_live.get(t["ticker"]))["valore_attuale"]
                for t in dati["titoli"]
            )
            for d in date_uniche:
                for (ed, etick, etipo, ecosto) in eventi:
                    if ed != d:
                        continue
                    if etipo == "dividendo":
                        div_run += ecosto
                    elif etipo == "acquisto":
                        inv_run += ecosto
                        inv_x_tick[etick] = inv_x_tick.get(etick, 0.0) + ecosto
                    elif etipo == "vendita":
                        inv_run += ecosto
                        inv_x_tick[etick] = max(0.0, inv_x_tick.get(etick, 0.0) + ecosto)
                inv_cum.append(inv_run)
                div_cum.append(div_run)
                pl_cum.append(valore_att_attuale - inv_run)
                for tk_ in tickers_unici:
                    serie_titoli[tk_].append(inv_x_tick.get(tk_, 0.0))
            sub_nb = ttk.Notebook(tab_graf)
            sub_nb.pack(fill="both", expand=True, padx=6, pady=6)
            PALETTE = ["#4E79A7", "#F28E2B", "#E15759", "#76B7B2",
                       "#59A14F", "#EDC948", "#B07AA1", "#FF9DA7"]
            def _disegna_grafico(parent, titolo, date_list, serie_list, nomi, colori, fill_sotto=False):
                frm = tk.Frame(parent, bg=self.COLOR_BACKGROUND)
                frm.pack(fill="both", expand=True, padx=8, pady=8)
                tk.Label(frm, text=titolo, bg=self.COLOR_BACKGROUND,
                         fg=self.COLOR_HIGHLIGHT, font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))
                PAD_L, PAD_R, PAD_T, PAD_B = 70, 20, 15, 50
                cvs = tk.Canvas(frm, bg=self.COLOR_WIDGET_BG,
                                highlightbackground=self.COLOR_HIGHLIGHT,
                                highlightthickness=1)
                cvs.pack(fill="both", expand=True)
                frm.update_idletasks()
                def _draw(event=None):
                    cvs.delete("all")
                    W = cvs.winfo_width()
                    H = cvs.winfo_height()
                    if W < 50 or H < 50:
                        return
                    all_vals = [v for s in serie_list for v in s]
                    if not all_vals:
                        return
                    v_min = min(0.0, min(all_vals))
                    v_max = max(all_vals) * 1.08 or 1.0
                    n = len(date_list)
                    def tx(i):
                        return PAD_L + (i / max(n - 1, 1)) * (W - PAD_L - PAD_R)
                    def ty(v):
                        return PAD_T + (1 - (v - v_min) / (v_max - v_min)) * (H - PAD_T - PAD_B)
                    for s in range(6):
                        yv = v_min + (v_max - v_min) * s / 5
                        yp = ty(yv)
                        cvs.create_line(PAD_L, yp, W - PAD_R, yp,
                                        fill=self.COLOR_HEADER_BG, dash=(2, 4))
                        lbl = f"€{yv:,.0f}" if abs(yv) < 1e6 else f"€{yv / 1000:,.0f}K"
                        cvs.create_text(PAD_L - 5, yp, text=lbl, anchor="e",
                                        font=("Segoe UI", 7), fill=self.TEXT_COLOR)
                    step_x = max(1, n // 8)
                    for i in range(0, n, step_x):
                        xp = tx(i)
                        cvs.create_line(xp, H - PAD_B, xp, H - PAD_B + 4, fill=self.TEXT_COLOR)
                        cvs.create_text(xp, H - PAD_B + 6, text=str(date_list[i]),
                                        font=("Segoe UI", 7), fill=self.TEXT_COLOR, angle=30, anchor="ne")
                    cvs.create_line(PAD_L, PAD_T, PAD_L, H - PAD_B, fill=self.TEXT_COLOR, width=1)
                    cvs.create_line(PAD_L, H - PAD_B, W - PAD_R, H - PAD_B, fill=self.TEXT_COLOR, width=1)
                    if v_min < 0:
                        cvs.create_line(PAD_L, ty(0), W - PAD_R, ty(0),
                                        fill=self.COLOR_RED, dash=(4, 3), width=1)
                    LABEL_AREA = 60
                    def tx(i):
                        return PAD_L + (i / max(n - 1, 1)) * (W - PAD_L - PAD_R - LABEL_AREA)
                    endpoints = []
                    for serie, nome, colore in zip(serie_list, nomi, colori):
                        if n < 2:
                            continue
                        pts_fill = [PAD_L, H - PAD_B]
                        pts_line = []
                        for i, v in enumerate(serie):
                            xp, yp = tx(i), ty(v)
                            pts_line += [xp, yp]
                            pts_fill += [xp, yp]
                        pts_fill += [tx(n - 1), H - PAD_B]
                        if fill_sotto and len(serie_list) == 1:
                            cvs.create_polygon(pts_fill, fill=colore, outline="", stipple="gray25")
                        cvs.create_line(pts_line, fill=colore, width=2, smooth=True)
                        xe = tx(n - 1)
                        ye = ty(serie[-1])
                        cvs.create_oval(xe - 3, ye - 3, xe + 3, ye + 3,
                                        fill=colore, outline=self.COLOR_WIDGET_BG)
                        endpoints.append([ye, serie[-1], colore])
                    STEP = 13
                    endpoints.sort(key=lambda x: x[0])
                    for i in range(1, len(endpoints)):
                        if endpoints[i][0] < endpoints[i - 1][0] + STEP:
                            endpoints[i][0] = endpoints[i - 1][0] + STEP
                    for i in range(len(endpoints) - 2, -1, -1):
                        if endpoints[i][0] > endpoints[i + 1][0] - STEP:
                            endpoints[i][0] = endpoints[i + 1][0] - STEP
                    for e in endpoints:
                        e[0] = max(PAD_T + 4, min(H - PAD_B - 4, e[0]))
                    x_fine  = tx(n - 1) 
                    x_leader = x_fine + 6 
                    x_label  = W - PAD_R - 2
                    for y_lbl, val, colore in endpoints:
                        cvs.create_line(x_fine, y_lbl, x_leader + 18, y_lbl,
                                        fill=colore, dash=(2, 3), width=1)
                        cvs.create_text(x_label, y_lbl, text=f"€{val:,.0f}",
                                        anchor="e", font=("Segoe UI", 8, "bold"), fill=colore)
                    lbl_tip  = cvs.create_text(0, 0, text="", font=("Segoe UI", 8),
                                               fill=self.TEXT_COLOR, anchor="nw", state="hidden")
                    line_tip = cvs.create_line(0, PAD_T, 0, H - PAD_B,
                                               fill=self.COLOR_HIGHLIGHT, dash=(3, 3), state="hidden")
                    def _motion(ev):
                        if n < 1:
                            return
                        i = int(round((ev.x - PAD_L) / max(W - PAD_L - PAD_R, 1) * (n - 1)))
                        i = max(0, min(i, n - 1))
                        xp = tx(i)
                        cvs.coords(line_tip, xp, PAD_T, xp, H - PAD_B)
                        cvs.itemconfig(line_tip, state="normal")
                        righe = [str(date_list[i])]
                        for s, nm in zip(serie_list, nomi):
                            righe.append(f"{nm}: €{s[i]:,.2f}")
                        testo_tip = "\n".join(righe)
                        max_chars  = max(len(r) for r in righe)
                        tip_w      = max_chars * 6 + 12
                        tip_h      = len(righe) * 14 + 6
                        tip_x = xp + 10 if xp + 10 + tip_w < W - PAD_R else xp - tip_w - 10
                        tip_y = PAD_T + 70
                        if tip_y + tip_h > H - PAD_B:
                            tip_y = H - PAD_B - tip_h - 4
                        cvs.coords(lbl_tip, tip_x, tip_y)
                        cvs.itemconfig(lbl_tip, text=testo_tip, state="normal")
                    def _leave(ev):
                        cvs.itemconfig(line_tip, state="hidden")
                        cvs.itemconfig(lbl_tip,  state="hidden")
                    cvs.bind("<Motion>", _motion)
                    cvs.bind("<Leave>",  _leave)
                cvs.bind("<Configure>", _draw)
                cvs.after(100, _draw)
            t1 = tk.Frame(sub_nb, bg=self.COLOR_BACKGROUND)
            sub_nb.add(t1, text="  Investito  ")
            _disegna_grafico(t1, "Capitale Investito nel Tempo",
                             date_uniche, [inv_cum], ["Investito"], [PALETTE[0]], fill_sotto=True)
            t2 = tk.Frame(sub_nb, bg=self.COLOR_BACKGROUND)
            sub_nb.add(t2, text="  P&L (stimato)  ")
            _disegna_grafico(t2, "P&L stimato al prezzo attuale",
                             date_uniche, [pl_cum], ["P&L (prezzo attuale)"], [PALETTE[2]], fill_sotto=True)
            t3 = tk.Frame(sub_nb, bg=self.COLOR_BACKGROUND)
            sub_nb.add(t3, text="  Dividendi  ")
            _disegna_grafico(t3, "Dividendi Incassati nel Tempo",
                             date_uniche, [div_cum], ["Dividendi"], [PALETTE[4]], fill_sotto=True)
            t4 = tk.Frame(sub_nb, bg=self.COLOR_BACKGROUND)
            sub_nb.add(t4, text="  Per Titolo  ")
            _disegna_grafico(t4, "Capitale Investito per Titolo",
                             date_uniche,
                             [serie_titoli[tk_] for tk_ in tickers_unici],
                             tickers_unici,
                             [PALETTE[i % len(PALETTE)] for i in range(len(tickers_unici))])
        def _refresh_all():
            _build_dashboard()
            _build_portafoglio()
            _build_movimenti()
            _build_dividendi()
            _build_grafici()
            _build_mercati()
        _refresh_all()

