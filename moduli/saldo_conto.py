#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import datetime
import tkinter as tk
from tkinter import ttk, filedialog
from moduli.modello_spesa import campo

def open_saldo_conto(self):
        from __main__ import PORTAFOGLIO_BANCARIO, EXPORT_FILES
        self.mostra_treeview_statistiche()
        if hasattr(self, '_saldo_popup') and self._saldo_popup and self._saldo_popup.winfo_exists():
            self._saldo_popup.lift()
            self._saldo_popup.focus_force()
            return
        W, H = 1300, 650
        bg   = self.COLOR_TOPLEVEL
        fg   = self.TEXT_COLOR
        popup = tk.Toplevel(self, bg=bg)
        self._saldo_popup = popup
        popup.title("Portafoglio Bancario")
        popup.withdraw()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        popup.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
        popup.resizable(False, False)
        popup.transient(self)
        popup.bind("<Escape>", lambda e: popup.destroy())
        def carica_db():
            if os.path.exists(PORTAFOGLIO_BANCARIO):
                try:
                    with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass
            return {
                "saldo_fisico": 0.0,
                "saldo_data":   datetime.date.today().strftime("%d-%m-%Y"),
                "storico_saldo": [],
                "conti": [],
                "trasferimenti": []
            }
        def salva_db(db):
            try:
                with open(PORTAFOGLIO_BANCARIO, "w", encoding="utf-8") as f:
                    json.dump(db, f, indent=2, ensure_ascii=False)
                if getattr(self, '_cruscotto_stato', 0) == 2:
                    self.after(100, self.aggiorna_conti_canvas)
            except Exception as e:
                self.show_toast(f"Errore salvataggio: {e}")
        def nuovo_id(prefisso, lista):
            ids = {c.get("id","") for c in lista}
            i = 1
            while f"{prefisso}{i}" in ids:
                i += 1
            return f"{prefisso}{i}"
        db = carica_db()
        def _btn(parent, ico, testo, cmd, side="left", padx=6):
            img = self.icone_gui.get(ico)
            b = tk.Label(parent, image=img, text=f" {testo}",
                         compound="left", bg=bg, fg=fg,
                         cursor="hand2", font=("Arial", 9, "bold"))
            if img:
                b.image = img
            b.pack(side=side, padx=padx, pady=4)
            b.bind("<Button-1>", lambda e: cmd())
            return b
        TIPO_COLORI = {
            "personale": "#4A90D9",
            "comune":    "#50C878",
            "figli":     "#C45E00",
            "altro":     "#A78BFA",
        }
        TIPI = ["personale", "comune", "figli", "altro"]
        nb = ttk.Notebook(popup)
        nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 0))
        tab_riepilogo     = tk.Frame(nb, bg=bg)
        tab_conti         = tk.Frame(nb, bg=bg)
        tab_trasferimenti = tk.Frame(nb, bg=bg)
        tab_movimenti     = tk.Frame(nb, bg=bg)
        tab_storico       = tk.Frame(nb, bg=bg)
        def _add_tab(frame, ico_key, testo):
            img = self.icone_gui.get(ico_key)
            if img:
                nb.add(frame, image=img, text=f"  {testo}  ", compound="left")
            else:
                nb.add(frame, text=testo)
        _add_tab(tab_riepilogo,     "report",      "Riepilogo")
        _add_tab(tab_conti,         "banca",       "Conti")
        _add_tab(tab_trasferimenti, "reset_campo", "Trasferimenti")
        _add_tab(tab_movimenti,     "descrizione", "Movimenti")
        _add_tab(tab_storico,       "grafico_linea", "Storico Saldo")
        bar_bottom = tk.Frame(popup, bg=bg)
        bar_bottom.pack(fill=tk.X, side=tk.BOTTOM, pady=(4, 6))
        def build_riepilogo():
            for w in tab_riepilogo.winfo_children():
                w.destroy()
            chk_frame = tk.Frame(tab_riepilogo, bg=bg)
            chk_frame.pack(fill=tk.X, padx=14, pady=(6, 0))
            ttk.Checkbutton(
                chk_frame,
                text="Includi movimenti futuri nel saldo",
                variable=self.considera_futuri_portafoglio_var,
                command=lambda: [build_riepilogo(), build_movimenti()]
            ).pack(side="left")
            db_now = carica_db()
            conti  = db_now.get("conti", [])

            totale_conti = sum(self._saldo_effettivo(c, db_now) for c in conti)
            conto_principale = next((c for c in conti if c.get("principale")), None)
            saldo_principale = self._saldo_effettivo(conto_principale, db_now) if conto_principale else 0.0
            oggi  = datetime.date.today()
            delta_mese = 0.0
            for d, voci in self.spese.items():
                if d.month == oggi.month and d.year == oggi.year:
                    for v in voci:
                        try:
                            imp  = float(v[2])
                            tipo = v[3]
                            delta_mese += imp if tipo == "Entrata" else -imp
                        except Exception:
                            pass
            saldo_netto = saldo_principale + delta_mese
            top_f = tk.Frame(tab_riepilogo, bg=bg)
            top_f.pack(fill=tk.X, padx=14, pady=(10, 4))
            tk.Label(top_f, text="Conti registrati", font=("Arial", 10, "bold"),
                     bg=bg, fg=fg).pack(anchor="w", pady=(0, 6))
            cards_f = tk.Frame(top_f, bg=bg)
            cards_f.pack(fill=tk.X)
            if not conti:
                tk.Label(cards_f, text="Nessun conto registrato. Vai al tab Conti.",
                         font=("Arial", 10), bg=bg, fg=fg).pack(anchor="w")
            else:
                for c in conti:
                    colore = TIPO_COLORI.get(c.get("tipo","altro"), "#A78BFA")
                    card = tk.Frame(cards_f, bg=colore, relief="flat", bd=0)
                    card.pack(side="left", padx=(0, 10), pady=2, ipadx=10, ipady=8)
                    nome = c.get("nome","?")
                    saldo_c = self._saldo_effettivo(c, db_now)
                    nome_frame = tk.Frame(card, bg=colore)
                    nome_frame.pack(anchor="w")
                    tk.Label(nome_frame, text=nome,
                             font=("Arial", 9, "bold"), bg=colore, fg="white").pack(side="left")
                    if c.get("principale"):
                        img_star = self.icone_gui.get("saldo")
                        lbl_star = tk.Label(nome_frame, image=img_star, bg=colore)
                        lbl_star.image = img_star
                        lbl_star.pack(side="left", padx=(4, 0))
                    tipo_meteo_c = "sole" if saldo_c >= 0 else "temporale"
                    lbl_meteo_c = tk.Label(card, text="", bg=colore)
                    lbl_meteo_c.pack(anchor="e", padx=(0, 4))
                    self.avvia_animazione_meteo(lbl_meteo_c, tipo_meteo_c)
                    tk.Label(card, text=f"€ {saldo_c:,.2f}",
                             font=("Arial", 13, "bold"), bg=colore, fg="white").pack(anchor="w")
                    tk.Label(card, text=c.get("tipo","").capitalize(),
                             font=("Arial", 8), bg=colore, fg="white").pack(anchor="w")
            ttk.Separator(tab_riepilogo, orient="horizontal").pack(fill=tk.X, padx=14, pady=6)
            mid_f = tk.Frame(tab_riepilogo, bg=bg)
            mid_f.pack(fill=tk.X, padx=14)
            tk.Label(mid_f, text="Distribuzione conti", font=("Arial", 10, "bold"),
                     bg=bg, fg=fg).pack(anchor="w", pady=(0, 4))
            canvas_w = 640
            canvas_h = 40
            _min_bar = 70
            if totale_conti > 0:
                _barre = []
                for c in conti:
                    saldo_c = self._saldo_effettivo(c, db_now)
                    if saldo_c <= 0:
                        continue
                    w_bar = max(_min_bar, int((saldo_c / totale_conti) * 640))
                    _barre.append((c, w_bar))
                canvas_w = sum(b[1] for b in _barre)
            else:
                canvas_w = 640
                _barre = []
            cv = tk.Canvas(mid_f, width=canvas_w, height=canvas_h,
                           bg=bg, highlightthickness=0)
            cv.pack(anchor="w")
            if _barre:
                x = 0
                for c, w_bar in _barre:
                    colore = TIPO_COLORI.get(c.get("tipo","altro"), "#A78BFA")
                    cv.create_rectangle(x, 0, x + w_bar - 2, canvas_h,
                                        fill=colore, outline="")
                    if w_bar > 15:
                        cv.create_text(x + w_bar//2, canvas_h//2,
                                       text=c.get("nome","")[:10],
                                       font=("Arial", 8, "bold"), fill="white")
                    x += w_bar
            else:
                cv.create_text(canvas_w//2, canvas_h//2,
                               text="Nessun dato", font=("Arial", 9), fill=fg)
            leg_f = tk.Frame(mid_f, bg=bg)
            leg_f.pack(anchor="w", pady=(4, 0))
            for tipo, colore in TIPO_COLORI.items():
                fr = tk.Frame(leg_f, bg=bg)
                fr.pack(side="left", padx=(0, 14))
                tk.Frame(fr, bg=colore, width=12, height=12).pack(side="left", padx=(0, 3))
                tk.Label(fr, text=tipo.capitalize(), font=("Arial", 8),
                         bg=bg, fg=fg).pack(side="left")
            ttk.Separator(tab_riepilogo, orient="horizontal").pack(fill=tk.X, padx=14, pady=8)
            bot_f = tk.Frame(tab_riepilogo, bg=bg)
            bot_f.pack(fill=tk.X, padx=14)
            def _riga(etichetta, valore, colore_val=None, bold=False):
                r = tk.Frame(bot_f, bg=bg)
                r.pack(fill=tk.X, pady=1)
                font_etich = ("Courier New", 10, "bold") if bold else ("Courier New", 10)
                font_val   = ("Courier New", 11, "bold") if bold else ("Courier New", 10)
                tk.Label(r, text=etichetta, font=font_etich,
                         bg=bg, fg=fg, anchor="w", width=34).pack(side="left")
                cv = colore_val if colore_val else fg
                tk.Label(r, text=f"€ {valore:>12,.2f}", font=font_val,
                         bg=bg, fg=cv).pack(side="left")

            _riga("Totale conti registrati:",      totale_conti)
            _riga(f"Delta spese mese ({oggi.strftime('%m/%Y')}):", delta_mese,
                  colore_val=self.COLOR_GREEN_SMOOTH if delta_mese >= 0 else self.COLOR_RED_SMOOTH)
            tk.Frame(bot_f, bg=fg, height=1).pack(fill=tk.X, pady=4)
            netto_col = self.COLOR_GREEN_SMOOTH if saldo_netto >= 0 else self.COLOR_RED_SMOOTH
            _riga("Saldo netto spendibile:", saldo_netto, colore_val=netto_col, bold=True)
            def anteprima_export_riepilogo():
                if hasattr(anteprima_export_riepilogo, '_win') and anteprima_export_riepilogo._win and anteprima_export_riepilogo._win.winfo_exists():
                    anteprima_export_riepilogo._win.lift()
                    anteprima_export_riepilogo._win.focus_force()
                    return
                db_r   = carica_db()
                conti_ = db_r.get("conti", [])
                trasf_ = db_r.get("trasferimenti", [])
                oggi_s = datetime.date.today().strftime("%d/%m/%Y")
                sep    = "═" * 80 + "\n"
                sep2   = "─" * 80 + "\n"
                contenuto  = f"RIEPILOGO PORTAFOGLIO  –  {oggi_s}\n{sep}"
                contenuto += "CONTI REGISTRATI\n" + sep2
                contenuto += f"{'Nome':<22} {'Tipo':<14} {'Saldo €':>14} {'Principale'}\n" + sep2
                for c in conti_:
                    princ = "🌟" if c.get("principale") else ""
                    contenuto += (f"{c.get('nome',''):<22} {c.get('tipo','').capitalize():<14} "
                                  f"€ {self._saldo_effettivo(c, db_now):>12,.2f}  {princ}\n")
                contenuto += sep2
                contenuto += f"{'Totale conti:':<37} € {totale_conti:>12,.2f}\n"
                contenuto += sep
                contenuto += "TRASFERIMENTI\n" + sep2
                nome_da_id = {c["id"]: c.get("nome","?") for c in conti_}
                if trasf_:
                    contenuto += f"{'Data':<12} {'Da':<18} {'A':<18} {'Importo €':>12}  Note\n" + sep2
                    for t in sorted(trasf_, key=lambda x: x.get("data",""), reverse=True):
                        da_raw = t.get("da","")
                        a_raw  = t.get("a","")
                        da_n = "Contabilità" if da_raw in ("__spese__", "Contabilità") else nome_da_id.get(da_raw, da_raw)
                        a_n  = "Contabilità" if a_raw  in ("__spese__", "Contabilità") else nome_da_id.get(a_raw,  a_raw)
                        if a_raw in ("__spese__", "Contabilità"):
                            da_n, a_n = a_n, da_n  # uscita: inverti così appare Contabilità → 111
                        contenuto += (f"{t.get('data',''):<12} {da_n:<18} {a_n:<18} "
                                      f"€ {float(t.get('importo',0)):>10,.2f}  {t.get('note','')}\n")
                else:
                    contenuto += "Nessun trasferimento registrato.\n"
                contenuto += sep
                contenuto += "RIEPILOGO SALDI\n" + sep2

                contenuto += f"{'Totale conti registrati:':<36}  € {totale_conti:>11,.2f}\n"
                d_col = "+" if delta_mese >= 0 else ""
                contenuto += f"{'Delta spese mese (' + oggi.strftime('%m/%Y') + '):':<37} {d_col}€ {delta_mese:>11,.2f}\n"
                contenuto += sep2
                s_col = "+" if saldo_netto >= 0 else ""
                contenuto += f"{'SALDO NETTO SPENDIBILE:':<37} {s_col}€ {saldo_netto:>11,.2f}\n"
                contenuto += sep
                prev_win = tk.Toplevel(popup)
                anteprima_export_riepilogo._win = prev_win
                prev_win.title("Esportazione Riepilogo Portafoglio")
                prev_win.bind("<Escape>", lambda e: prev_win.destroy())
                prev_win.bind("<Destroy>", lambda e: setattr(anteprima_export_riepilogo, '_win', None) if e.widget is prev_win else None)
                prev_win.withdraw()
                prev_win.update_idletasks()
                w, h = 900, 520
                x = self.winfo_rootx() + (self.winfo_width()  // 2) - (w // 2)
                y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
                prev_win.geometry(f"{w}x{h}+{max(0,x)}+{max(0,y)}")
                prev_win.minsize(w, h)
                prev_win.configure(background=self.COLOR_TOPLEVEL)
                prev_win.transient(popup)
                prev_win.deiconify()
                prev_win.lift()
                prev_win.focus_force()
                txt_frame = tk.Frame(prev_win, bg=self.COLOR_TOPLEVEL)
                txt_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                v_scroll = ttk.Scrollbar(txt_frame, orient="vertical")
                h_scroll = ttk.Scrollbar(txt_frame, orient="horizontal")
                v_scroll.pack(side=tk.RIGHT,  fill=tk.Y)
                h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
                txt = tk.Text(txt_frame, font=("Courier New", 10),
                              bg=self.COLOR_WHITE, fg=self.COLOR_BLACK,
                              wrap="none",
                              yscrollcommand=v_scroll.set,
                              xscrollcommand=h_scroll.set)
                txt.pack(fill=tk.BOTH, expand=True)
                v_scroll.config(command=txt.yview)
                h_scroll.config(command=txt.xview)
                txt.insert("1.0", contenuto)
                txt.config(state="disabled")
                btn_f = tk.Frame(prev_win, bg=self.COLOR_TOPLEVEL)
                btn_f.pack(fill=tk.X, pady=10)
                fn_base = f"Riepilogo_{datetime.date.today().strftime('%Y%m%d')}"
                def salva_pdf_r():
                    f = filedialog.asksaveasfilename(
                        initialdir=EXPORT_FILES, confirmoverwrite=False,
                        defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
                        initialfile=f"{fn_base}.pdf", parent=prev_win)
                    if f:
                        try:
                            import fitz
                            doc  = fitz.open()
                            page = doc.new_page(width=595, height=842)
                            page.insert_text((40, 40), contenuto, fontname="cour", fontsize=9)
                            doc.save(f)
                            doc.close()
                            self.show_toast("PDF salvato.")
                        except Exception as e:
                            self.show_custom_warning("Errore", str(e))
                def salva_txt_r():
                    f = filedialog.asksaveasfilename(
                        initialdir=EXPORT_FILES, confirmoverwrite=False,
                        defaultextension=".txt", filetypes=[("TXT", "*.txt")],
                        initialfile=f"{fn_base}.txt", parent=prev_win)
                    if f:
                        with open(f, "w", encoding="utf-8") as fh:
                            fh.write(contenuto)
                        self.show_toast("TXT salvato.")
                for testo, ico, cmd, side in [
                    (" Chiudi", "chiudi", prev_win.destroy,                                                        tk.RIGHT),
                    (" PDF",    "salva",  salva_pdf_r,                                                             tk.LEFT),
                    (" TXT",    "salva",  salva_txt_r,                                                             tk.LEFT),
                    (" Stampa", "stampa", lambda: self._stampa_lista_diretta(contenuto, self.show_custom_warning), tk.LEFT),
                ]:
                    b = ttk.Label(btn_f, compound="left", image=self.icone_gui.get(ico),
                                  text=testo, background=self.COLOR_WIDGET_BG,
                                  foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
                    b.pack(side=side, padx=5)
                    b.bind("<Button-1>", lambda e, c=cmd: c())
            bar_riep = tk.Frame(tab_riepilogo, bg=bg)
            bar_riep.pack(fill=tk.X, padx=14, pady=(8, 4))
            _btn(bar_riep, "report", "Esporta riepilogo", anteprima_export_riepilogo)
        def build_conti():
            for w in tab_conti.winfo_children():
                w.destroy()
            db_now   = carica_db()
            conti    = db_now.get("conti", [])
            sel_id   = [None]
            paned = tk.Frame(tab_conti, bg=bg)
            paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
            lf_tree = ttk.LabelFrame(paned, text="Conti", padding=6)
            lf_tree.pack(side="left", fill=tk.BOTH, expand=True, padx=(0, 6))
            cols = ("nome","tipo","saldo","principale","note")
            tree = ttk.Treeview(lf_tree, columns=cols, show="headings", height=14)
            tree.heading("nome",       text="Nome")
            tree.heading("tipo",       text="Tipo")
            tree.heading("saldo",      text="Saldo €")
            tree.heading("principale", text="Principale")
            tree.heading("note",       text="Note")
            tree.column("nome",       width=140, anchor="w")
            tree.column("tipo",       width=80,  anchor="center")
            tree.column("saldo",      width=90,  anchor="e")
            tree.column("principale", width=70,  anchor="center")
            tree.column("note",       width=140, anchor="w")
            for col in cols:
                tree.heading(col, command=lambda _col=col: self.treeview_sort_column(tree, _col, False))
            vsb = ttk.Scrollbar(lf_tree, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=vsb.set)
            vsb.pack(side="right", fill="y")
            tree.pack(fill=tk.BOTH, expand=True)
            def ricarica_tree():
                tree.delete(*tree.get_children())
                for c in db_now.get("conti", []):
                    saldo_c = self._saldo_effettivo(c, db_now)
                    princ   = "🌟" if c.get("principale") else ""
                    iid = tree.insert("", "end", iid=c["id"],
                                      values=(c.get("nome",""), c.get("tipo",""),
                                              f"{saldo_c:,.2f}", princ, c.get("note","")))
                    colore = TIPO_COLORI.get(c.get("tipo","altro"), "#A78BFA")
                    tree.tag_configure(c["id"], foreground=colore)
                    tree.item(iid, tags=(c["id"],))
            ricarica_tree()
            lf_form = ttk.LabelFrame(paned, text="Dettaglio conto", padding=10)
            lf_form.pack(side="left", fill=tk.Y, padx=(0, 0), ipadx=4)
            v_nome  = tk.StringVar()
            v_tipo  = tk.StringVar(value="personale")
            v_saldo = tk.StringVar()
            v_princ = tk.BooleanVar()
            v_iban  = tk.StringVar()
            v_note  = tk.StringVar()
            def _lbl_entry(parent, testo, var, row, entry_w=18, readonly=False, maxchar=None):
                tk.Label(parent, text=testo, font=("Arial", 9, "bold"),
                         bg=bg, fg=fg, anchor="w").grid(row=row, column=0,
                         sticky="w", padx=(0, 6), pady=3)
                st = "readonly" if readonly else "normal"
                e = ttk.Entry(parent, textvariable=var, width=entry_w)
                if maxchar:
                    vcmd = (parent.register(lambda s, n=maxchar: len(s) <= n), "%P")
                    e.config(validate="key", validatecommand=vcmd)
                e.grid(row=row, column=1, sticky="w", pady=3)
                return e
            _lbl_entry(lf_form, "Nome:",    v_nome,  0, maxchar=25)
            tk.Label(lf_form, text="Tipo:", font=("Arial", 9, "bold"),
                     bg=bg, fg=fg, anchor="w").grid(row=1, column=0, sticky="w", padx=(0,6), pady=3)
            ttk.Combobox(lf_form, textvariable=v_tipo, values=TIPI,
                         state="readonly", width=16, style="Border.TCombobox").grid(row=1, column=1, sticky="w", pady=3)
            _lbl_entry(lf_form, "Saldo €:", v_saldo, 2, maxchar=9)
            _lbl_entry(lf_form, "IBAN:",    v_iban,  3)
            _lbl_entry(lf_form, "Note:",    v_note,  4, maxchar=20)
            tk.Label(lf_form, text="Principale:", font=("Arial", 9, "bold"),
                     bg=bg, fg=fg).grid(row=5, column=0, sticky="w", padx=(0,6), pady=3)
            ttk.Checkbutton(lf_form, variable=v_princ).grid(row=5, column=1, sticky="w", pady=3)
            def reset_form():
                v_nome.set(""); v_tipo.set("personale"); v_saldo.set("")
                v_princ.set(False); v_iban.set(""); v_note.set("")
                sel_id[0] = None
            def popola_form(conto):
                v_nome.set(conto.get("nome",""))
                v_tipo.set(conto.get("tipo","personale"))
                v_saldo.set(f"{float(conto.get('saldo', 0.0)):.2f}")
                v_princ.set(bool(conto.get("principale", False)))
                v_iban.set(conto.get("iban",""))
                v_note.set(conto.get("note",""))
                sel_id[0] = conto["id"]
            def on_select(e):
                sel = tree.selection()
                if not sel:
                    return
                iid = sel[0]
                conto = next((c for c in db_now["conti"] if c["id"]==iid), None)
                if conto:
                    popola_form(conto)
            tree.bind("<<TreeviewSelect>>", on_select)
            def salva_conto():
                nome = v_nome.get().strip()
                if not nome:
                    self.show_toast("Inserisci un nome per il conto.")
                    return
                try:
                    saldo_val = float(v_saldo.get().replace(",","."))
                except ValueError:
                    self.show_toast("Saldo non valido.")
                    return
                nome_esiste = any(
                            c["nome"].lower() == nome.lower() and c["id"] != sel_id[0]
                            for c in db_now.get("conti", [])
                    )
                if nome_esiste:
                     self.show_toast("Un conto con questo nome esiste già.")
                     return
                if v_princ.get():
                    for c in db_now["conti"]:
                        c["principale"] = False
                if sel_id[0]:
                    for c in db_now["conti"]:
                        if c["id"] == sel_id[0]:
                            c["nome"]       = nome
                            c["tipo"]       = v_tipo.get()
                            c["saldo"]      = saldo_val
                            c["principale"] = v_princ.get()
                            c["iban"]       = v_iban.get().strip()
                            c["note"]       = v_note.get().strip()
                            break
                else:
                    if len(db_now.get("conti", [])) >= 7:
                           self.show_toast("Limite raggiunto: massimo 7 conti consentiti.")
                           return
                    db_now["conti"].append({
                        "id":         nuovo_id("c", db_now["conti"]),
                        "nome":       nome,
                        "tipo":       v_tipo.get(),
                        "saldo":      saldo_val,
                        "principale": v_princ.get(),
                        "iban":       v_iban.get().strip(),
                        "note":       v_note.get().strip()
                    })
                salva_db(db_now)
                ricarica_tree()
                reset_form()
                self.show_toast("Conto salvato.")
                if hasattr(self, 'cb_conto'):
                    self.cb_conto['values'] = [c.get("nome", "?") for c in db_now.get("conti", [])]
                if hasattr(self, 'cb_conto_movimento'):
                    _n = ["(nessuno)"] + [c.get("nome", "?") for c in db_now.get("conti", [])]
                    self.cb_conto_movimento['values'] = _n
                    _nuovo_princ = next((c.get("nome","") for c in db_now.get("conti",[]) if c.get("principale")), "(nessuno)")
                    self.v_conto_movimento.set(_nuovo_princ)
                build_riepilogo()
            def elimina_conto():
                if not sel_id[0]:
                    self.show_toast("Seleziona un conto da eliminare.")
                    return
                nome_c = v_nome.get()
                if not self.show_custom_askyesno("Elimina conto",
                        f"Eliminare il conto '{nome_c}'?\nVerranno eliminati anche tutti i trasferimenti collegati."):
                    return
                
                db_now["trasferimenti"] = [
                    t for t in db_now.get("trasferimenti", [])
                    if t.get("da") != sel_id[0] and t.get("a") != sel_id[0]
                ]
                db_now["conti"] = [c for c in db_now["conti"] if c["id"] != sel_id[0]]
                salva_db(db_now)
                self.refresh_gui()
                ricarica_tree()
                reset_form()
                self.show_toast("Conto eliminato.")
                if hasattr(self, 'cb_conto'):
                    self.cb_conto['values'] = [c.get("nome", "?") for c in db_now.get("conti", [])]
                    if hasattr(self, 'v_conto_agg') and self.v_conto_agg.get() == nome_c:
                        self.v_conto_agg.set(self.cb_conto['values'][0] if self.cb_conto['values'] else "")
                if hasattr(self, 'cb_conto_movimento'):
                    _n = ["(nessuno)"] + [c.get("nome", "?") for c in db_now.get("conti", [])]
                    self.cb_conto_movimento['values'] = _n
                    if self.v_conto_movimento.get() == nome_c:
                        self.v_conto_movimento.set("(nessuno)")
                build_riepilogo()
            btn_f = tk.Frame(lf_form, bg=bg)
            btn_f.grid(row=6, column=0, columnspan=2, pady=(10, 0))
            _btn(btn_f, "aggiungi", "Nuovo",    reset_form)
            _btn(btn_f, "salva",    "Salva",    salva_conto)
            _btn(btn_f, "cancella", "Elimina",  elimina_conto)
        def build_trasferimenti():
            for w in tab_trasferimenti.winfo_children():
                w.destroy()
            db_now = carica_db()
            conti  = db_now.get("conti", [])
            trasf  = db_now.get("trasferimenti", [])
            sel_id = [None]
            nomi_conti = [c["nome"] for c in conti]
            id_da_nome = {c["nome"]: c["id"] for c in conti}
            nome_da_id = {c["id"]: c["nome"] for c in conti}
            top = tk.Frame(tab_trasferimenti, bg=bg)
            top.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
            lf_tree = ttk.LabelFrame(top, text="Trasferimenti", padding=6)
            lf_tree.pack(side="left", fill=tk.BOTH, expand=True, padx=(0,6))
            cols = ("data","da","a","importo","note")
            tree = ttk.Treeview(lf_tree, columns=cols, show="headings", height=14)
            tree.heading("data",    text="Data")
            tree.heading("da",      text="Da conto")
            tree.heading("a",       text="A conto")
            tree.heading("importo", text="Importo €")
            tree.heading("note",    text="Note")
            tree.column("data",    width=90,  anchor="center")
            tree.column("da",      width=120, anchor="w")
            tree.column("a",       width=120, anchor="w")
            tree.column("importo", width=90,  anchor="e")
            tree.column("note",    width=160, anchor="w")
            for col in cols:
                tree.heading(col, command=lambda _col=col: self.treeview_sort_column(tree, _col, False))
            vsb = ttk.Scrollbar(lf_tree, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=vsb.set)
            vsb.pack(side="right", fill="y")
            tree.pack(fill=tk.BOTH, expand=True)
            def ricarica_tree_t():
                tree.delete(*tree.get_children())
                db_r = carica_db()
                for t in sorted(db_r.get("trasferimenti",[]),
                                key=lambda x: x.get("data",""), reverse=True):
                    if "__spese__" in (t.get("da",""), t.get("a","")):
                        continue
                    da_n = nome_da_id.get(t.get("da",""),"?")
                    a_n  = nome_da_id.get(t.get("a",""),"?")
                    tree.insert("", "end", iid=t["id"],
                                values=(t.get("data",""), da_n, a_n,
                                        f"{float(t.get('importo',0)):,.2f}",
                                        t.get("note","")))
            ricarica_tree_t()
            lf_form = ttk.LabelFrame(top, text="Nuovo trasferimento", padding=10)
            lf_form.pack(side="left", fill=tk.Y, ipadx=4)
            v_data   = tk.StringVar(value=datetime.date.today().strftime("%d-%m-%Y"))
            v_da     = tk.StringVar(value=nomi_conti[0] if nomi_conti else "")
            v_a      = tk.StringVar(value=nomi_conti[1] if len(nomi_conti)>1 else "")
            v_imp    = tk.StringVar()
            v_note   = tk.StringVar()
            def _row(parent, testo, widget_fn, row):
                tk.Label(parent, text=testo, font=("Arial", 9, "bold"),
                         bg=bg, fg=fg, anchor="w").grid(row=row, column=0,
                         sticky="w", padx=(0,6), pady=3)
                w = widget_fn(parent)
                w.grid(row=row, column=1, sticky="w", pady=3)
                return w
            def _valida_data_t(s):
                if s == "": return True
                parti = s.split("-")
                if len(parti) > 3: return False
                limiti = [2, 2, 4]
                for i, p in enumerate(parti):
                    if not p.isdigit() and p != "": return False
                    if len(p) > limiti[i]: return False
                return len(s) <= 10
            data_e = _row(lf_form, "Data:", lambda p: ttk.Entry(p, textvariable=v_data, width=14,
                          validate="key", validatecommand=(p.register(_valida_data_t), "%P")), 0)
            def _apri_cal_t(e=None):
                self.mostra_calendario_popup_semplice(data_e, v_data)
            img_cal = self.icone_gui.get("calendario")
            lbl_cal = tk.Label(lf_form, image=img_cal, cursor="hand2", bg=bg)
            if img_cal: lbl_cal.image = img_cal
            lbl_cal.grid(row=0, column=2, padx=2)
            lbl_cal.bind("<Button-1>", _apri_cal_t)
            _row(lf_form, "Da conto:", lambda p: ttk.Combobox(p, textvariable=v_da,
                 values=nomi_conti, state="readonly", width=16, style="Border.TCombobox"), 1)
            _row(lf_form, "A conto:",  lambda p: ttk.Combobox(p, textvariable=v_a,
                 values=nomi_conti, state="readonly", width=16, style="Border.TCombobox"), 2)
            _row(lf_form, "Importo €:", lambda p: ttk.Entry(p, textvariable=v_imp, width=14,
                 validate="key", validatecommand=(p.register(lambda s: len(s)<=9), "%P")), 3)
            _row(lf_form, "Note:",     lambda p: ttk.Entry(p, textvariable=v_note, width=18,
                 validate="key", validatecommand=(p.register(lambda s: len(s)<=20), "%P")), 4)
            def on_sel_t(e):
                sel = tree.selection()
                if not sel: return
                iid = sel[0]
                db_r = carica_db()
                t = next((x for x in db_r["trasferimenti"] if x["id"]==iid), None)
                if t:
                    v_data.set(t.get("data",""))
                    v_da.set(nome_da_id.get(t.get("da",""),""))
                    v_a.set(nome_da_id.get(t.get("a",""),""))
                    v_imp.set(f"{float(t.get('importo', 0)):.2f}")
                    v_note.set(t.get("note",""))
                    sel_id[0] = iid
            tree.bind("<<TreeviewSelect>>", on_sel_t)
            def reset_t():
                v_data.set(datetime.date.today().strftime("%d-%m-%Y"))
                v_da.set(nomi_conti[0] if nomi_conti else "")
                v_a.set(nomi_conti[1] if len(nomi_conti)>1 else "")
                v_imp.set(""); v_note.set("")
                sel_id[0] = None
            def salva_trasf():
                if not nomi_conti:
                    self.show_toast("Aggiungi prima i conti nel tab 🏦 Conti.")
                    return
                try:
                    imp = float(v_imp.get().replace(",", "."))
                    if imp <= 0: raise ValueError
                except ValueError:
                    self.show_toast("Importo non valido.")
                    return
                da_id = id_da_nome.get(v_da.get())
                a_id  = id_da_nome.get(v_a.get())
                if not da_id or not a_id:
                    self.show_toast("Seleziona conti validi.")
                    return
                if da_id == a_id:
                    self.show_toast("I conti devono essere diversi.")
                    return
                db_r = carica_db()
                if sel_id[0]:
                    vecchio = next((t for t in db_r["trasferimenti"] if t["id"] == sel_id[0]), None)
                    if vecchio:
                        vecchio["data"]    = v_data.get()
                        vecchio["da"]      = da_id
                        vecchio["a"]       = a_id
                        vecchio["importo"] = imp
                        vecchio["note"]    = v_note.get().strip()
                else:
                    db_r["trasferimenti"].append({
                        "id":      nuovo_id("t", db_r["trasferimenti"]),
                        "data":    v_data.get(),
                        "da":      da_id,
                        "a":       a_id,
                        "importo": round(float(imp), 2),
                        "note":    v_note.get().strip()
                    })
                salva_db(db_r)
                ricarica_tree_t()
                reset_t()
                build_riepilogo()
                build_conti()
                self.show_toast("Trasferimento salvato.")
            def elimina_trasf():
                if not sel_id[0]:
                    self.show_toast("Seleziona un trasferimento da eliminare.")
                    return
                if not self.show_custom_askyesno("Elimina", "Eliminare questo trasferimento e ripristinare i saldi?"):
                    return
                db_r = carica_db()
                vecchio = next((t for t in db_r["trasferimenti"] if t["id"] == sel_id[0]), None)
                if vecchio:
                    db_r["trasferimenti"] = [t for t in db_r["trasferimenti"] if t["id"] != sel_id[0]]
                salva_db(db_r)
                ricarica_tree_t()
                reset_t()
                build_riepilogo()
                build_conti()
                self.show_toast("Trasferimento eliminato.")
            btn_f = tk.Frame(lf_form, bg=bg)
            btn_f.grid(row=5, column=0, columnspan=3, pady=(10,0))
            _btn(btn_f, "aggiungi", "Nuovo",   reset_t)
            _btn(btn_f, "salva",    "Salva",   salva_trasf)
            _btn(btn_f, "cancella", "Elimina", elimina_trasf)
        def build_movimenti():
            for w in tab_movimenti.winfo_children():
                w.destroy()
            oggi  = datetime.date.today()
            MESI  = ["Tutti","Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno",
                     "Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"]
            anni  = sorted({d.year for d in self.spese.keys()}, reverse=True)
            if not anni:
                anni = [oggi.year]
            anni_str = ["Tutti"] + [str(a) for a in anni]
            v_anno = tk.StringVar(value=str(oggi.year))
            v_mese = tk.StringVar(value=MESI[oggi.month])
            v_tipo = tk.StringVar(value="Tutti")
            v_cat  = tk.StringVar(value="Tutte")
            v_conto = tk.StringVar(value="Tutti")
            tb = tk.Frame(tab_movimenti, bg=bg)
            tb.pack(fill=tk.X, padx=10, pady=(8,4))
            def _lbl_filt(testo):
                tk.Label(tb, text=testo, font=("Arial", 9, "bold"),
                         bg=bg, fg=fg).pack(side="left", padx=(6,2))
            _lbl_filt("Anno:")
            ttk.Combobox(tb, textvariable=v_anno, values=anni_str,
                         state="readonly", width=7, style="Border.TCombobox").pack(side="left", padx=(0,8))
            _lbl_filt("Mese:")
            ttk.Combobox(tb, textvariable=v_mese, values=MESI,
                         state="readonly", width=12, style="Border.TCombobox").pack(side="left", padx=(0,8))
            _lbl_filt("Tipo:")
            ttk.Combobox(tb, textvariable=v_tipo,
                         values=["Tutti","Entrata","Uscita"],
                         state="readonly", width=8, style="Border.TCombobox").pack(side="left", padx=(0,8))
            cats = sorted({v[0] for voci in self.spese.values() for v in voci if v})
            cats_str = ["Tutte"] + cats
            _lbl_filt("Categoria:")
            ttk.Combobox(tb, textvariable=v_cat, values=cats_str,
                         state="readonly", width=14, style="Border.TCombobox").pack(side="left", padx=(0,8))
            _conti_nomi_filt = [c.get("nome", "?") for c in json.load(open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8")).get("conti", [])] if os.path.exists(PORTAFOGLIO_BANCARIO) else []
            _lbl_filt("Conto:")
            ttk.Combobox(tb, textvariable=v_conto,
                         values=["Tutti", "(nessuno)"] + _conti_nomi_filt,
                         state="readonly", width=14, style="Border.TCombobox").pack(side="left")
            lf = tk.LabelFrame(tab_movimenti, text="⚙️ Storico Movimenti",
                               font=("Arial", 10, "bold"), fg="red",
                               bg=bg, padx=6, pady=6)
            img_mouse = self.icone_gui.get("mouse")
            lbl_hint_mov = ttk.Label(lf, text=" Doppio clic: Vai al movimento  |  Click dx: Copia nel form  |  Ctrl/Shift + Clic: Selezione multipla",
                                     image=img_mouse, compound="left",
                                     foreground="gray", font=("Arial", 7, "italic"),
                                     background=bg)
            if img_mouse: lbl_hint_mov.image = img_mouse
            lbl_hint_mov.pack(anchor="e", pady=(0, 2))
            lf.pack(fill=tk.BOTH, expand=True, padx=10, pady=(4,6))
            cols = ("data","categoria","descrizione","importo","tipo","conto","metodo","tag")
            tree = ttk.Treeview(lf, columns=cols, show="headings", height=14)
            for col in cols:
                        tree.heading(col, text=col, command=lambda _col=col: self.treeview_sort_column(tree, _col, False))
            tree.heading("data",        text="Data")
            tree.heading("categoria",   text="Categoria")
            tree.heading("descrizione", text="Descrizione")
            tree.heading("importo",     text="Importo €")
            tree.heading("tipo",        text="Tipo")
            tree.heading("conto",       text="Conto")
            tree.heading("metodo",      text="Metodo")
            tree.heading("tag",         text="Tag")
            tree.column("data",        width=85,  anchor="center")
            tree.column("categoria",   width=120, anchor="w")
            tree.column("descrizione", width=260, anchor="w")
            tree.column("importo",     width=90,  anchor="e")
            tree.column("tipo",        width=70,  anchor="center")
            tree.column("conto",       width=100, anchor="w")
            tree.column("metodo",      width=100, anchor="w")
            tree.column("tag",         width=140, anchor="w")
            vsb = ttk.Scrollbar(lf, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=vsb.set)
            vsb.pack(side="right", fill="y")
            tree.pack(fill=tk.BOTH, expand=True)
            lbl_riepilogo = tk.Label(tab_movimenti,
                                     text="", font=("Courier New", 9),
                                     bg=bg, fg=fg, anchor="w")
            lbl_riepilogo.pack(fill=tk.X, padx=12, pady=(0,4))
            def aggiorna_tree(*_):
                tree.delete(*tree.get_children())
                try:
                    anno_f = int(v_anno.get())
                except ValueError:
                    anno_f = None
                mese_idx = MESI.index(v_mese.get())
                tipo_f  = v_tipo.get()
                cat_f   = v_cat.get()
                conto_f = v_conto.get()
                tot_e = tot_u = 0.0
                try:
                    with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
                        _db_p = json.load(_pf)
                    _id_a_nome = {c["id"]: c.get("nome","") for c in _db_p.get("conti",[])}
                    _agganci = {}
                    for _t in _db_p.get("trasferimenti", []):
                        if _t.get("da") in ("__spese__","Contabilità") or _t.get("a") in ("__spese__","Contabilità"):
                            _data_t = _t.get("data","")
                            _imp_t  = round(float(_t.get("importo",0)), 2)
                            _tipo_t = "Entrata" if _t.get("da") in ("__spese__","Contabilità") else "Uscita"
                            _cnome  = _id_a_nome.get(_t.get("a") if _tipo_t=="Entrata" else _t.get("da"), "")
                            _agganci.setdefault((_data_t, _imp_t, _tipo_t), []).append(_cnome)
                except Exception:
                    _agganci = {}
                _uso_ordinale_sc = {}
                for d in sorted(self.spese.keys(), reverse=True):
                    if not self.considera_futuri_portafoglio_var.get() and d > datetime.date.today():
                        continue
                    if anno_f and d.year != anno_f: continue
                    if mese_idx != 0 and d.month != mese_idx: continue
                    for v in self.spese[d]:
                        try:
                            cat, desc, imp, tipo = v[0], v[1], float(v[2]), v[3]
                        except Exception:
                            continue
                        if tipo_f != "Tutti" and tipo != tipo_f: continue
                        if cat_f != "Tutte" and cat != cat_f: continue
                        _key = (d.strftime("%d-%m-%Y"), round(imp, 2), tipo)
                        _lista_c = _agganci.get(_key, [])
                        _ord_sc = _uso_ordinale_sc.get(_key, 0)
                        nome_conto_sp = campo(v, "conto", "") or (_lista_c[_ord_sc] if _ord_sc < len(_lista_c) else "")
                        _uso_ordinale_sc[_key] = _ord_sc + 1
                        if conto_f == "(nessuno)" and nome_conto_sp: continue
                        if conto_f not in ("Tutti", "(nessuno)") and nome_conto_sp != conto_f: continue
                        metodo_sp = campo(v, "metodo_pagamento", "")
                        tag_sp = " ".join(campo(v, "hashtag", []) or [])
                        oggi = datetime.date.today()
                        if d > oggi:
                            tag = "futuro"
                        elif tipo == "Entrata":
                            tag = "entrata"
                        else:
                            tag = "uscita"
                        tree.insert("", "end",
                                    values=(d.strftime("%d-%m-%Y"), cat, desc, f"{imp:,.2f}", tipo, nome_conto_sp, metodo_sp, tag_sp),
                                    tags=(tag,))
                        if tipo == "Entrata": tot_e += imp
                        else:                 tot_u += imp
                tree.tag_configure("entrata",    foreground=self.COLOR_GREEN)
                tree.tag_configure("uscita",     foreground=self.COLOR_RED)
                tree.tag_configure("futuro", foreground="#E5C07B", font=("Arial", 9, "italic"))
                saldo_m = tot_e - tot_u
                col_s = self.COLOR_GREEN_SMOOTH if saldo_m >= 0 else self.COLOR_RED_SMOOTH
                n_tot = len(tree.get_children())
                lbl_riepilogo.config(
                    text=f"  Entrate: € {tot_e:,.2f}   Uscite: € {tot_u:,.2f}   "
                         f"Saldo: € {saldo_m:+,.2f}   ({n_tot} movimenti)",
                    fg=col_s)
            bar_mov = tk.Frame(tab_movimenti, bg=bg)
            bar_mov.pack(fill=tk.X, padx=10, pady=(0,4))
            
            def on_doppio_click_mov(e):
                sel = tree.selection()
                if not sel: return
                r = tree.item(sel[0])["values"]
                try:
                    giorno = datetime.datetime.strptime(str(r[0]), "%d-%m-%Y").date()
                except Exception:
                    return
                if hasattr(self, "cal"):
                    self.cal.selection_set(giorno)
                    self.cal._sel_date = giorno
                    self.estratto_month_var.set(self.months[giorno.month - 1])
                    self.estratto_year_var.set(str(giorno.year))
                    self.on_calendar_change()
                desc_cerca = str(r[2])[:20]
                def _sel(g=giorno, d=desc_cerca):
                    for iid in self.spese_mese_tree.get_children():
                        v = self.spese_mese_tree.item(iid, "values")
                        try:
                            dv = datetime.datetime.strptime(v[0].strip(), "%d/%m/%Y").date()
                        except Exception:
                            continue
                        if dv == g and d in str(v[2]):
                            self.spese_mese_tree.selection_set(iid)
                            self.spese_mese_tree.see(iid)
                            break
                popup.destroy()
                self.after(400, _sel)
            tree.bind("<Double-1>", on_doppio_click_mov)
            
            def on_click_dx_mov(e):
                item = tree.identify_row(e.y)
                if not item: return
                r = tree.item(item)["values"]
                try:
                    imp   = float(str(r[3]).replace(",",""))
                    cat   = str(r[1])
                    desc  = str(r[2])
                    tipo  = str(r[4])
                except Exception:
                    return
                popup.destroy()
                cat_match = next((c for c in self.categorie if c.strip().lower() == cat.lower()), None)
                if cat_match:
                    self.cat_sel.set(cat_match)
                    self.cat_menu.set(cat_match)
                    self.on_categoria_changed(manuale=False)
                if self.tipo_spesa_var.get() != tipo:
                    self.toggle_tipo_spesa()
                try:
                    self.imp_entry.delete(0, tk.END)
                    self.imp_entry.insert(0, f"{imp:.2f}")
                except Exception: pass
                self.desc_entry.delete(0, tk.END)
                self.desc_entry.insert(0, desc.replace("RIC·","").replace("ALL·","").strip()[:30])
            tree.bind("<Button-3>", on_click_dx_mov)
            self._bind_tooltip_metodo(tree, col_desc=2)
            
            def anteprima_export():
                if hasattr(anteprima_export, '_win') and anteprima_export._win and anteprima_export._win.winfo_exists():
                    anteprima_export._win.lift()
                    anteprima_export._win.focus_force()
                    return
                anno_f = v_anno.get()
                mese_f = v_mese.get()
                sep    = "═" * 94 + "\n"
                sep2   = "─" * 94 + "\n"
                header = (f"{'Data':<12}  {'Categoria':<20}  "
                          f"{'Descrizione':<24}  {'Importo €':>12}  {'Tipo':<8}  Conto\n")
                contenuto = f"ESTRATTO CONTO  –  {mese_f} {anno_f}\n{sep}{header}{sep2}"
                for iid in tree.get_children():
                    r          = tree.item(iid)["values"]
                    segno      = "+" if r[4] == "Entrata" else "-"
                    imp        = f"{segno}€ {r[3]}"
                    desc_trunc = str(r[2])[:24]
                    conto_exp  = str(r[5]) if len(r) > 5 else ""
                    contenuto += (f"{str(r[0]):<12}  {str(r[1]):<20}  "
                                  f"{desc_trunc:<24}  {imp:>12}  {str(r[4]):<8}  {conto_exp}\n")
                contenuto += sep + lbl_riepilogo.cget("text").strip() + "\n"
                if not tree.get_children():
                    self.show_toast("Nessun movimento da esportare.")
                    return
                prev_win = tk.Toplevel(popup)
                anteprima_export._win = prev_win
                prev_win.title("Esportazione Estratto Conto")
                prev_win.bind("<Escape>", lambda e: prev_win.destroy())
                prev_win.bind("<Destroy>", lambda e: setattr(anteprima_export, '_win', None) if e.widget is prev_win else None)
                prev_win.withdraw()
                prev_win.update_idletasks()
                w, h = 1000, 550
                x = self.winfo_rootx() + (self.winfo_width()  // 2) - (w // 2)
                y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
                prev_win.geometry(f"{w}x{h}+{max(0,x)}+{max(0,y)}")
                prev_win.minsize(w, h)
                prev_win.configure(background=self.COLOR_TOPLEVEL)
                prev_win.transient(popup)
                prev_win.deiconify()
                prev_win.lift()
                prev_win.focus_force()
                txt_frame = tk.Frame(prev_win, bg=self.COLOR_TOPLEVEL)
                txt_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                v_scroll = ttk.Scrollbar(txt_frame, orient="vertical")
                h_scroll = ttk.Scrollbar(txt_frame, orient="horizontal")
                v_scroll.pack(side=tk.RIGHT,  fill=tk.Y)
                h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
                txt = tk.Text(txt_frame, font=("Courier New", 10),
                              bg=self.COLOR_WHITE, fg=self.COLOR_BLACK,
                              wrap="none",
                              yscrollcommand=v_scroll.set,
                              xscrollcommand=h_scroll.set)
                txt.pack(fill=tk.BOTH, expand=True)
                v_scroll.config(command=txt.yview)
                h_scroll.config(command=txt.xview)
                txt.insert("1.0", contenuto)
                txt.config(state="disabled")
                btn_f = tk.Frame(prev_win, bg=self.COLOR_TOPLEVEL)
                btn_f.pack(fill=tk.X, pady=10)
                def salva_pdf():
                    f = filedialog.asksaveasfilename(
                        initialdir=EXPORT_FILES,
                        confirmoverwrite=False,
                        defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
                        initialfile=f"Estratto_{anno_f}_{mese_f}.pdf", parent=prev_win)
                    if f:
                        try:
                            import fitz
                            doc  = fitz.open()
                            page = doc.new_page(width=842, height=595)
                            page.insert_text((40, 40), contenuto, fontname="cour", fontsize=9)
                            doc.save(f)
                            doc.close()
                            self.show_toast("PDF salvato.")
                        except Exception as e:
                            self.show_custom_warning("Errore", str(e))
                def salva_txt():
                    f = filedialog.asksaveasfilename(
                        initialdir=EXPORT_FILES,
                        confirmoverwrite=False,
                        defaultextension=".txt", filetypes=[("TXT", "*.txt")],
                        initialfile=f"Estratto_{anno_f}_{mese_f}.txt", parent=prev_win)
                    if f:
                        with open(f, "w", encoding="utf-8") as fh:
                            fh.write(contenuto)
                        self.show_toast("TXT salvato.")
                for testo, ico, cmd, side in [
                    (" Chiudi", "chiudi", prev_win.destroy,                                                        tk.RIGHT),
                    (" PDF",    "salva",  salva_pdf,                                                               tk.LEFT),
                    (" TXT",    "salva",  salva_txt,                                                               tk.LEFT),
                    (" Stampa", "stampa", lambda: self._stampa_lista_diretta(contenuto, self.show_custom_warning), tk.LEFT),
                ]:
                    b = ttk.Label(btn_f, compound="left", image=self.icone_gui.get(ico),
                                  text=testo, background=self.COLOR_WIDGET_BG,
                                  foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
                    b.pack(side=side, padx=5)
                    b.bind("<Button-1>", lambda e, c=cmd: c())
            frm_aggancia = tk.Frame(tab_movimenti, bg=bg)
            frm_aggancia.pack(fill=tk.X, padx=10, pady=(0, 4))
            tk.Label(frm_aggancia, text="Aggancia a conto:",
                     bg=bg, fg=fg, font=("Arial", 9, "bold")).pack(side="left", padx=(0, 6))
            conti_nomi = [c.get("nome", "?") for c in carica_db().get("conti", [])]
            self.v_conto_agg = tk.StringVar(value=conti_nomi[0] if conti_nomi else "")
            self.cb_conto = ttk.Combobox(frm_aggancia, textvariable=self.v_conto_agg,
                                     values=conti_nomi, state="readonly",
                                     width=18, style="Border.TCombobox")
            self.cb_conto.pack(side="left", padx=(0, 8))
            def aggancia_a_conto():
                sel = tree.selection()
                sel = [s for s in sel if not str(s).startswith("t")]
                if not sel:
                    self.show_toast("Seleziona un movimento da agganciare.")
                    return
                nome_conto = self.v_conto_agg.get()
                if not nome_conto:
                    self.show_toast("Seleziona un conto.")
                    return
                agganciati = 0
                for iid in sel:
                    vals = tree.item(iid)["values"]
                    try:
                        data_v = str(vals[0])
                        imp    = float(str(vals[3]).replace(",", ""))
                        tipo   = str(vals[4])
                        d_obj  = datetime.datetime.strptime(data_v, "%d-%m-%Y").date()
                    except Exception:
                        continue
                    for v in self.spese.get(d_obj, []):
                        try:
                            corrisponde = abs(float(v[2]) - imp) < 0.01 and str(v[3]) == tipo
                        except Exception:
                            corrisponde = False
                        if corrisponde and hasattr(v, "conto"):
                            v.conto = nome_conto
                            agganciati += 1
                            break
                if agganciati:
                    self.save_db()
                self.show_toast(f"{agganciati} movimento/i agganciato/i a '{nome_conto}'.")
                aggiorna_tree()
                build_riepilogo()
                build_trasferimenti()
                build_storico()
                self.refresh_gui()
            img_link = self.icone_gui.get("link") or self.icone_gui.get("aggiungi") or self.icone_gui.get("salva")
            btn_agg = tk.Label(frm_aggancia, image=img_link,
                               text=" Aggancia", compound="left",
                               bg=bg, fg=fg, cursor="hand2",
                               font=("Arial", 9, "bold"))
            if img_link:
                btn_agg.image = img_link
            btn_agg.pack(side="left", padx=(0, 8))
            btn_agg.bind("<Button-1>", lambda e: aggancia_a_conto())
            def rimuovi_agganciato():
                sel = tree.selection()
                if not sel:
                    self.show_toast("Seleziona un movimento agganciato.")
                    return
                sel_agg = [s for s in sel if tree.item(s)["values"][5]]
                if not sel_agg:
                    self.show_toast("Seleziona un movimento agganciato.")
                    return
                if not self.show_custom_askyesno("Rimuovi", "Rimuovere l'aggancio al conto dei movimenti selezionati e ripristinare il saldo?"):
                    return
                rimossi = 0
                for iid in sel_agg:
                    vals = tree.item(iid)["values"]
                    try:
                        data_v = str(vals[0])
                        imp    = round(float(str(vals[3]).replace(",", "")), 2)
                        tipo   = str(vals[4])
                        d_obj  = datetime.datetime.strptime(data_v, "%d-%m-%Y").date()
                    except Exception:
                        continue
                    for v in self.spese.get(d_obj, []):
                        try:
                            corrisponde = abs(float(v[2]) - imp) < 0.01 and str(v[3]) == tipo
                        except Exception:
                            corrisponde = False
                        if corrisponde and campo(v, "conto", ""):
                            v.conto = ""
                            rimossi += 1
                            break
                if rimossi:
                    self.save_db()
                self.show_toast(f"{rimossi} movimento/i rimosso/i.")
                aggiorna_tree()
                build_riepilogo()
                build_trasferimenti()
                build_storico()
                self.refresh_gui()
            img_del = self.icone_gui.get("cancella") or self.icone_gui.get("elimina")
            btn_del = tk.Label(frm_aggancia, image=img_del,
                               text=" Rimuovi agganciato", compound="left",
                               bg=bg, fg=fg, cursor="hand2",
                               font=("Arial", 9, "bold"))
            if img_del: btn_del.image = img_del
            btn_del.pack(side="left")
            btn_del.bind("<Button-1>", lambda e: rimuovi_agganciato())
            _btn(bar_mov, "report", "Esporta", anteprima_export)
            for var in (v_anno, v_mese, v_tipo, v_cat, v_conto):
                var.trace_add("write", aggiorna_tree)
            aggiorna_tree()
        def build_storico():
            for w in tab_storico.winfo_children():
                w.destroy()
            _modo = ["mesi"]
            MESI_BREVI = ["Gen","Feb","Mar","Apr","Mag","Giu",
                          "Lug","Ago","Set","Ott","Nov","Dic"]
            COL_ENT  = "#98C379"
            COL_USC  = "#E06C75"
            COL_NET  = "#61AFEF"
            GRD_COL  = "#3a3a4a"
            bar_top = tk.Frame(tab_storico, bg=bg)
            bar_top.pack(fill=tk.X, padx=12, pady=(6, 2))
            tk.Label(bar_top, text="Vista:", bg=bg, fg=fg,
                     font=("Arial", 9, "bold")).pack(side="left", padx=(0, 6))
            lbl_mesi = tk.Label(bar_top, text="Mensile", bg=self.COLOR_ACCENT if hasattr(self,"COLOR_ACCENT") else "#61AFEF",
                                fg="white", font=("Arial", 9, "bold"),
                                padx=10, pady=3, cursor="hand2")
            lbl_anni = tk.Label(bar_top, text="Annuale", bg=bg, fg=fg,
                                font=("Arial", 9, "bold"),
                                padx=10, pady=3, cursor="hand2",
                                relief="flat", bd=1)
            lbl_mesi.pack(side="left", padx=(0, 4))
            lbl_anni.pack(side="left")
            for col, testo in ((COL_ENT, "Entrate"), (COL_USC, "Uscite"), (COL_NET, "Saldo conto")):
                tk.Frame(bar_top, bg=col, width=12, height=12).pack(side="right", padx=(0,2), pady=4)
                tk.Label(bar_top, text=testo, bg=bg, fg=fg,
                         font=("Arial", 8)).pack(side="right", padx=(0,6))
            lf_g = ttk.LabelFrame(tab_storico, text="Andamento conto principale", padding=4)
            lf_g.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 6))
            c = tk.Canvas(lf_g, bg=self.COLOR_WIDGET_BG, highlightthickness=0)
            c.pack(fill=tk.BOTH, expand=True)
            def _aggrega():
                db_now = carica_db()
                conti  = db_now.get("conti", [])
                conto_princ = next((c for c in conti if c.get("principale")), None)
                saldo_attuale = self._saldo_effettivo(conto_princ, db_now) if conto_princ else 0.0
                bucket = {}
                for d, voci in self.spese.items():
                    if not self.considera_ricorrenze_var.get() and d > datetime.date.today():
                        continue
                    if _modo[0] == "mesi":
                        key = (d.year, d.month)
                    else:
                        key = (d.year, 0)
                    for v in voci:
                        try:
                            imp  = float(v[2])
                            tipo = v[3]
                        except Exception:
                            continue
                        b = bucket.setdefault(key, {"ent": 0.0, "usc": 0.0})
                        if tipo == "Entrata":
                            b["ent"] += imp
                        else:
                            b["usc"] += imp
                chiavi = sorted(bucket)
                if not chiavi:
                    return []
                netto_totale = sum(b["ent"] - b["usc"] for b in bucket.values())
                saldo_cum = saldo_attuale - netto_totale
                risultati = []
                for key in chiavi:
                    anno, mese = key
                    b = bucket[key]
                    saldo_cum += b["ent"] - b["usc"]
                    if _modo[0] == "mesi":
                        label = f"{MESI_BREVI[mese-1]}\n{anno}"
                    else:
                        label = str(anno)
                    risultati.append({
                        "label": label, "anno": anno, "mese": mese,
                        "ent": b["ent"], "usc": b["usc"],
                        "saldo": saldo_cum
                    })
                return risultati
            def disegna(event=None):
                c.delete("all")
                cw = c.winfo_width()
                ch = c.winfo_height()
                if cw < 20 or ch < 20:
                    return
                dati = _aggrega()
                if not dati:
                    c.create_text(cw//2, ch//2, text="Nessuna transazione nel database",
                                  fill=self.TEXT_COLOR, font=("Arial", 10))
                    return
                pad_t = 20
                pad_b = 38
                pad_l = 68
                pad_r = 16
                uw = cw - pad_l - pad_r
                uh = ch - pad_t - pad_b
                n  = len(dati)
                all_vals = [d["ent"] for d in dati] + [d["usc"] for d in dati] + [d["saldo"] for d in dati]
                vmin = min(all_vals + [0])
                vmax = max(all_vals + [0])
                if vmax == vmin:
                    vmin -= 1; vmax += 1
                vrange = vmax - vmin
                def cx(i):
                    return pad_l + (i / (n-1)) * uw if n > 1 else pad_l + uw/2
                def cy(v):
                    return pad_t + uh - ((v - vmin) / vrange) * uh
                for k in range(6):
                    yv = vmin + k * vrange / 5
                    yp = cy(yv)
                    c.create_line(pad_l, yp, pad_l+uw, yp, fill=GRD_COL, dash=(3,4))
                    c.create_text(pad_l-4, yp, text=f"€{yv:,.0f}",
                                  anchor="e", fill=self.TEXT_COLOR, font=("Arial", 7))
                if vmin < 0 < vmax:
                    y0 = cy(0)
                    c.create_line(pad_l, y0, pad_l+uw, y0, fill="#888", width=1)
                step_lbl = max(1, n // 14)
                for i, d in enumerate(dati):
                    if i % step_lbl == 0 or i == n-1:
                        x = cx(i)
                        for j, part in enumerate(d["label"].split("\n")):
                            c.create_text(x, ch - pad_b + 6 + j*11,
                                          text=part, fill=self.TEXT_COLOR,
                                          font=("Arial", 7), anchor="n")
                def serie(campo, colore, raggio=3):
                    pts = [(cx(i), cy(d[campo])) for i, d in enumerate(dati)]
                    for i in range(len(pts)-1):
                        c.create_line(pts[i][0], pts[i][1],
                                      pts[i+1][0], pts[i+1][1],
                                      fill=colore, width=2)
                    for i, (px, py) in enumerate(pts):
                        d = dati[i]
                        ov = c.create_oval(px-raggio, py-raggio,
                                           px+raggio, py+raggio,
                                           fill=colore, outline="")
                        if _modo[0] == "mesi":
                            titolo_tip = f"{MESI_BREVI[d['mese']-1]} {d['anno']}"
                        else:
                            titolo_tip = str(d["anno"])
                        tip = (f"{titolo_tip}\n"
                               f"Entrate:  €{d['ent']:,.2f}\n"
                               f"Uscite:   €{d['usc']:,.2f}\n"
                               f"Saldo:    €{d['saldo']:,.2f}")
                        c.tag_bind(ov, "<Enter>",
                                   lambda e, t=tip: self.esegui_disegno(
                                       t,
                                       min(e.x_root, self.winfo_rootx()+self.winfo_width()-210),
                                       min(e.y_root, self.winfo_rooty()+self.winfo_height()-80)))
                        c.tag_bind(ov, "<Leave>",
                                   lambda e: self.tooltip_win.withdraw()
                                   if self.tooltip_win and self.tooltip_win.winfo_exists() else None)
                        c.tag_bind(ov, "<Double-1>",
                                   lambda e, d=d: self.mostra_transazioni_popup(
                                       {"anno": str(d["anno"]),
                                        "mese": d["mese"] if _modo[0]=="mesi" else None},
                                       f"{d['label'].replace(chr(10),' ')}"))
                serie("ent", COL_ENT)
                serie("usc", COL_USC)
                serie("saldo", COL_NET, raggio=4)
                c.bind("<Leave>",
                       lambda e: self.tooltip_win.withdraw()
                       if self.tooltip_win and self.tooltip_win.winfo_exists() else None)
            def set_modo(m):
                _modo[0] = m
                acc = self.COLOR_ACCENT if hasattr(self, "COLOR_ACCENT") else "#61AFEF"
                if m == "mesi":
                    lbl_mesi.config(bg=acc, fg="white")
                    lbl_anni.config(bg=bg, fg=fg)
                else:
                    lbl_anni.config(bg=acc, fg="white")
                    lbl_mesi.config(bg=bg, fg=fg)
                disegna()
            lbl_mesi.bind("<Button-1>", lambda e: set_modo("mesi"))
            lbl_anni.bind("<Button-1>", lambda e: set_modo("anni"))
            c.bind("<Configure>", disegna)
        build_riepilogo()
        build_conti()
        build_trasferimenti()
        build_movimenti()
        build_storico()
        self._saldo_refresh_storico = build_storico
        self._saldo_refresh = build_riepilogo
        self._saldo_refresh_movimenti = build_movimenti
        def on_tab_change(event):
            tab = nb.index(nb.select())
            if tab == 0:
                build_riepilogo()
            elif tab == 1:
                build_conti()
            elif tab == 2:
                build_trasferimenti()
        nb.bind("<<NotebookTabChanged>>", on_tab_change)
        def chiudi_portafoglio():
            if hasattr(self, '_calendario_attivo'):
                try:
                    self._calendario_attivo.destroy()
                except Exception:
                    pass
            popup.destroy()
        _btn(bar_bottom, "chiudi", "Chiudi", chiudi_portafoglio, side="right", padx=14)
        popup.protocol("WM_DELETE_WINDOW", chiudi_portafoglio)
        popup.deiconify()
        popup.focus_force()

