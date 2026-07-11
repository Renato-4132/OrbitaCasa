#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import datetime
import tkinter as tk
from tkinter import ttk

def apri_estratti_metodo(self, metodo=None, mese=None, anno=None, conto=None):
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO

    simboli_metodo = {
        "💰 Contanti": "💰",
        "🔄 RID/SDD": "🔄",
        "🏦 Bonifico": "🏦",
        "💎 C.Credito": "💎",
        "💜 C.Credito": "💜",
        "💳 C.Debito": "💳",
        "📶 Contactless": "📶",
        "📯 PayPal": "📯",
        "📮 Bollettino": "📮",
        "🏪 Prepagata": "🏪",
        "🪙 Assegno": "🪙",
        "🔘 Revolut": "🔘",
        "🍎 Apple Pay": "🍎",
        "🎯 Google Pay": "🎯",
        "🏣 Postepay": "🏣",
        "📲 Satispay": "📲",
        "🔀 Scalapay": "🔀",
        "🛒 Amazon Pay": "🛒",
        }
    metodi_lista = [""] + list(simboli_metodo.keys())
    win = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    win.title("Estratti per Metodo di Pagamento e Conti")
    win.withdraw()
    self.update_idletasks()
    w, h = 1100, 620
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")
    win.minsize(w, h)
    win.transient(self)
    win.deiconify()
    win.lift()
    win.focus_force()
    win.bind("<Escape>", lambda e: win.destroy())
    toolbar = ttk.Frame(win, style="BlackFrame.TFrame")
    toolbar.pack(fill=tk.X, padx=8, pady=(8, 4))
    ttk.Label(toolbar, text="Metodo:", background=self.COLOR_WIDGET_BG,
              foreground=self.TEXT_COLOR, font=("Arial", 9)).pack(side="left", padx=(0, 4))
    var_metodo = tk.StringVar(value="")
    combo = ttk.Combobox(toolbar, textvariable=var_metodo, values=metodi_lista,
                         state="readonly", style="Border.TCombobox", width=18)
    combo.pack(side="left", padx=4)
    try:
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
            _db_p_em = json.load(_pf)
        _conti_em = [c.get("nome","?") for c in _db_p_em.get("conti",[])]
        _id_a_nome_em = {c["id"]: c.get("nome","") for c in _db_p_em.get("conti",[])}
        _agganci_em = {}
        for _t in _db_p_em.get("trasferimenti", []):
            if _t.get("da") in ("__spese__","Contabilità") or _t.get("a") in ("__spese__","Contabilità"):
                _data_t = _t.get("data","")
                _imp_t  = round(float(_t.get("importo",0)), 2)
                _tipo_t = "Entrata" if _t.get("da") in ("__spese__","Contabilità") else "Uscita"
                _cnome  = _id_a_nome_em.get(_t.get("a") if _tipo_t=="Entrata" else _t.get("da"), "")
                _agganci_em.setdefault((_data_t, _imp_t, _tipo_t), []).append(_cnome)
    except Exception:
        _conti_em = []
        _agganci_em = {}
    var_conto_em = tk.StringVar(value="Tutti")
    if _conti_em:
        ttk.Label(toolbar, text="Conto:", background=self.COLOR_WIDGET_BG,
                  foreground=self.TEXT_COLOR, font=("Arial", 9)).pack(side="left", padx=(12, 4))
        ttk.Combobox(toolbar, textvariable=var_conto_em,
                     values=["Tutti"] + _conti_em,
                     state="readonly", style="Border.TCombobox", width=14).pack(side="left", padx=4)
    ttk.Label(toolbar, text="Periodo:", background=self.COLOR_WIDGET_BG,
              foreground=self.TEXT_COLOR, font=("Arial", 9)).pack(side="left", padx=(12, 4))
    var_periodo = tk.StringVar(value="tutto")
    for val, lbl in [("tutto", "Tutto"), ("anno", "Anno"), ("mese", "Mese"), ("giorno", "Giorno")]:
        ttk.Radiobutton(toolbar, text=lbl, variable=var_periodo, value=val,
                        style="Custom.TRadiobutton").pack(side="left", padx=3)
    oggi = datetime.date.today()
    frame_anno = ttk.Frame(toolbar, style="BlackFrame.TFrame")
    frame_anno.pack(side="left", padx=4)
    var_anno = tk.StringVar(value=str(oggi.year))
    combo_anno = ttk.Combobox(frame_anno, textvariable=var_anno,
                              values=[str(y) for y in range(oggi.year - 15, oggi.year + 2)],
                              state="readonly", style="Border.TCombobox", width=6)
    combo_anno.pack(side="left")
    mesi = ["01","02","03","04","05","06","07","08","09","10","11","12"]
    var_mese = tk.StringVar(value=f"{oggi.month:02d}")
    combo_mese = ttk.Combobox(frame_anno, textvariable=var_mese, values=mesi,
                              state="readonly", style="Border.TCombobox", width=4)
    combo_mese.pack(side="left", padx=2)
    var_giorno = tk.StringVar(value=f"{oggi.day:02d}")
    combo_giorno = ttk.Combobox(frame_anno, textvariable=var_giorno,
                                values=[f"{d:02d}" for d in range(1, 32)],
                                state="readonly", style="Border.TCombobox", width=4)
    combo_giorno.pack(side="left", padx=2)
    frame_date = ttk.Frame(toolbar, style="BlackFrame.TFrame")
    frame_date.pack(side="right", padx=(8, 0))
    ttk.Label(frame_date, text="Da:", background=self.COLOR_WIDGET_BG,
              foreground=self.TEXT_COLOR, font=("Arial", 9)).pack(side="left", padx=(0, 2))
    var_da = tk.StringVar(value="")
    entry_da = ttk.Entry(frame_date, textvariable=var_da, width=10, font=("Arial", 9))
    entry_da.pack(side="left")
    btn_cal_da = ttk.Label(frame_date, image=self.icone_gui.get("calendario"),
                           cursor="hand2", background=self.COLOR_WIDGET_BG)
    btn_cal_da.pack(side="left", padx=(2, 8))
    btn_cal_da.bind("<Button-1>", lambda e: self.mostra_calendario_popup(entry_da, var_da))
    ttk.Label(frame_date, text="A:", background=self.COLOR_WIDGET_BG,
              foreground=self.TEXT_COLOR, font=("Arial", 9)).pack(side="left", padx=(0, 2))
    var_a = tk.StringVar(value="")
    entry_a = ttk.Entry(frame_date, textvariable=var_a, width=10, font=("Arial", 9))
    entry_a.pack(side="left")
    btn_cal_a = ttk.Label(frame_date, image=self.icone_gui.get("calendario"),
                          cursor="hand2", background=self.COLOR_WIDGET_BG)
    btn_cal_a.pack(side="left", padx=(2, 0))
    btn_cal_a.bind("<Button-1>", lambda e: self.mostra_calendario_popup(entry_a, var_a))
    btn_reset_date = ttk.Label(frame_date, image=self.icone_gui.get("reset"),
                               cursor="hand2", background=self.COLOR_WIDGET_BG)
    btn_reset_date.pack(side="left", padx=(6, 0))
    btn_reset_date.bind("<Button-1>", lambda e: [var_da.set(""), var_a.set("")])
    frame_tot = ttk.Frame(win, style="BlackFrame.TFrame")
    frame_tot.pack(fill=tk.X, padx=8, pady=2)
    lbl_entrate = ttk.Label(frame_tot, text="Entrate: —", foreground="lightgreen",
                            background=self.COLOR_WIDGET_BG, font=("Arial", 9, "bold"))
    lbl_entrate.pack(side="left", padx=8)
    lbl_uscite = ttk.Label(frame_tot, text="Uscite: —", foreground="lightcoral",
                           background=self.COLOR_WIDGET_BG, font=("Arial", 9, "bold"))
    lbl_uscite.pack(side="left", padx=8)
    lbl_saldo = ttk.Label(frame_tot, text="Saldo: —", foreground="khaki",
                          background=self.COLOR_WIDGET_BG, font=("Arial", 9, "bold"))
    lbl_saldo.pack(side="left", padx=8)
    lbl_count = ttk.Label(frame_tot, text="Movimenti: 0", foreground=self.TEXT_COLOR,
                          background=self.COLOR_WIDGET_BG, font=("Arial", 9))
    lbl_count.pack(side="left", padx=8)
    img_mouse = self.icone_gui.get("mouse")
    lbl_hint = ttk.Label(
        frame_tot,
        text="  2×→ Vai al giorno  |  Dx→ Popola campi inserimento",
        image=img_mouse,
        compound="right",
        foreground="gray",
        background=self.COLOR_WIDGET_BG,
        font=("Arial", 8, "italic")
    )
    if img_mouse:
        lbl_hint.image = img_mouse
    lbl_hint.pack(side="right", padx=10)
    frame_tree = ttk.Frame(win, style="BlackFrame.TFrame")
    frame_tree.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 8))
    cols = ("data", "categoria", "descrizione", "entrata", "uscita", "conto")
    tree = ttk.Treeview(frame_tree, columns=cols, show="headings", style="Treeview")
    tree.heading("data",        text="Data")
    tree.heading("categoria",   text="Categoria")
    tree.heading("descrizione", text="Descrizione")
    tree.heading("entrata",     text="Entrata")
    tree.heading("uscita",      text="Uscita")
    tree.heading("conto",       text="Conto")
    tree.column("data",        width=90,  anchor="center")
    tree.column("categoria",   width=120, anchor="w")
    tree.column("descrizione", width=260, anchor="w")
    tree.column("entrata",     width=100, anchor="center")
    tree.column("uscita",      width=100, anchor="center")
    tree.column("conto",       width=100, anchor="w")
    testi_col = {"data": "Data", "categoria": "Categoria", "descrizione": "Descrizione",
                 "entrata": "Entrata", "uscita": "Uscita", "conto": "Conto"}
    for col in cols:
        tree.heading(col, text=testi_col[col],
                     command=lambda c=col: self.treeview_sort_column(tree, c, False))
    sb = ttk.Scrollbar(frame_tree, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill=tk.BOTH, expand=True)
    sb.pack(side="right", fill=tk.Y)
    tree.tag_configure("entrata", foreground="green")
    tree.tag_configure("uscita",  foreground="red")
    def on_doppio_clic(event):
        item_id = tree.identify_row(event.y)
        if not item_id:
            return
        vals = tree.item(item_id, "values")
        if not vals:
            return
        data_str = vals[0]
        try:
            giorno = datetime.datetime.strptime(data_str, "%d/%m/%Y").date()
        except Exception:
            return
        self.set_stats_mode("giorno")
        if hasattr(self, "cal"):
            self.cal.selection_set(giorno)
            self.cal._sel_date = giorno
            self.stats_refdate = giorno
        self.update_stats()
        self.estratto_month_var.set(f"{giorno.month:02d}")
        self.estratto_year_var.set(str(giorno.year))
        self.stats_label.config(
            text=f"Riepilogo Giornaliero - {giorno.strftime('%d-%m-%Y')}",
            foreground="purple", font=("Arial", 10, "bold"))
        win.destroy()
    def on_clic_destro(event):
        item_id = tree.identify_row(event.y)
        if not item_id:
            return
        vals = tree.item(item_id, "values")
        if not vals:
            return
        categoria   = str(vals[1]).strip()
        descrizione = str(vals[2]).strip()
        entrata     = str(vals[3]).strip()
        uscita      = str(vals[4]).strip()
        importo_str = entrata.replace("+","").replace("€","").strip() if entrata else uscita.replace("-","").replace("€","").strip()
        tipo = "Entrata" if entrata.strip() else "Uscita"
        cat_match = next((c for c in self.categorie if c.strip().lower() == categoria.lower()), None)
        if cat_match:
            self.cat_sel.set(cat_match)
            self.cat_menu.set(cat_match)
            self.on_categoria_changed(manuale=False)
        try:
            self.imp_entry.delete(0, tk.END)
            self.imp_entry.insert(0, f"{float(importo_str):.2f}")
        except ValueError:
            pass
        self.desc_entry.delete(0, tk.END)
        if "♻️" not in descrizione:
            self.desc_entry.insert(0, descrizione[:30])
        if self.tipo_spesa_var.get() != tipo:
            self.toggle_tipo_spesa()
        self.after(0, self.imp_entry.focus_set)
        win.destroy()
    tree.bind("<Double-1>", on_doppio_clic)
    tree.bind("<Button-3>", on_clic_destro)
    self._bind_tooltip_metodo(tree, col_desc=2)
    def aggiorna(*_):
        tree.delete(*tree.get_children())
        metodo_sel = var_metodo.get()
        simbolo = simboli_metodo.get(metodo_sel, "") if metodo_sel else ""
        periodo = var_periodo.get()
        conto_f = var_conto_em.get()
        tot_e = 0.0
        tot_u = 0.0
        righe = []
        _uso_ordinale_em = {}
        for data_obj, voci in sorted(self.spese.items()):
            if periodo == "anno":
                if str(data_obj.year) != var_anno.get():
                    continue
            elif periodo == "mese":
                if str(data_obj.year) != var_anno.get() or f"{data_obj.month:02d}" != var_mese.get():
                    continue
            elif periodo == "giorno":
                if (str(data_obj.year) != var_anno.get() or
                    f"{data_obj.month:02d}" != var_mese.get() or
                    f"{data_obj.day:02d}" != var_giorno.get()):
                    continue
            try:
                da = datetime.datetime.strptime(var_da.get(), "%d-%m-%Y").date() if var_da.get() else None
            except:
                da = None
            try:
                a = datetime.datetime.strptime(var_a.get(), "%d-%m-%Y").date() if var_a.get() else None
            except:
                a = None
            if da and data_obj < da:
                continue
            if a and data_obj > a:
                continue
            for voce in voci:
                if len(voce) < 3:
                    continue
                cat     = str(voce[0]).strip()
                desc    = str(voce[1]).strip()
                importo = float(voce[2])
                tipo    = str(voce[3]).strip() if len(voce) > 3 else ""
                if simbolo and simbolo not in desc:
                    continue
                _key_em = (data_obj.strftime("%d-%m-%Y"), round(importo, 2), tipo)
                _lista_c_em = _agganci_em.get(_key_em, [])
                _ord_em = _uso_ordinale_em.get(_key_em, 0)
                nome_conto_em = _lista_c_em[_ord_em] if _ord_em < len(_lista_c_em) else ""
                _uso_ordinale_em[_key_em] = _ord_em + 1
                if conto_f != "Tutti" and nome_conto_em != conto_f:
                    continue
                data_str = data_obj.strftime("%d/%m/%Y")
                if tipo == "Entrata":
                    tot_e += importo
                    righe.append((data_obj, data_str, cat, desc, f"+{importo:.2f} €", "", "entrata", nome_conto_em))
                else:
                    tot_u += importo
                    righe.append((data_obj, data_str, cat, desc, "", f"-{importo:.2f} €", "uscita", nome_conto_em))
        for r in righe:
            tree.insert("", "end", values=(r[1], r[2], r[3], r[4], r[5], r[7]), tags=(r[6],))
        saldo = tot_e - tot_u
        lbl_entrate.config(text=f"Entrate: +{tot_e:.2f} €")
        lbl_uscite.config(text=f"Uscite: -{tot_u:.2f} €")
        lbl_saldo.config(text=f"Saldo: {saldo:+.2f} €",
                         foreground="lightgreen" if saldo >= 0 else "lightcoral")
        lbl_count.config(text=f"Movimenti: {len(righe)}")
    def on_periodo(*_):
        p = var_periodo.get()
        combo_anno.config(state="readonly" if p in ("anno","mese","giorno") else "disabled")
        combo_mese.config(state="readonly" if p in ("mese","giorno") else "disabled")
        combo_giorno.config(state="readonly" if p == "giorno" else "disabled")
        if p == "tutto":
            frame_anno.pack_forget()
        elif p == "anno":
            frame_anno.pack(side="left", padx=4)
            combo_anno.pack(side="left")
            combo_mese.pack_forget()
            combo_giorno.pack_forget()
        elif p == "mese":
            frame_anno.pack(side="left", padx=4)
            combo_anno.pack(side="left")
            combo_mese.pack(side="left", padx=2)
            combo_giorno.pack_forget()
        elif p == "giorno":
            frame_anno.pack(side="left", padx=4)
            combo_anno.pack(side="left")
            combo_mese.pack(side="left", padx=2)
            combo_giorno.pack(side="left", padx=2)
        aggiorna()
    var_periodo.trace_add("write", on_periodo)
    var_metodo.trace_add("write", aggiorna)
    var_conto_em.trace_add("write", aggiorna)
    var_anno.trace_add("write", aggiorna)
    var_mese.trace_add("write", aggiorna)
    var_giorno.trace_add("write", aggiorna)
    var_da.trace_add("write", aggiorna)
    var_a.trace_add("write", aggiorna)
    if metodo:
        var_metodo.set(metodo)
    if anno:
        var_anno.set(str(anno))
    if mese:
        var_mese.set(f"{int(mese):02d}")
        var_periodo.set("mese")
    if conto and conto in _conti_em:
        var_conto_em.set(conto)
    bot_f = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    bot_f.pack(fill=tk.X, side=tk.BOTTOM, pady=10)
    for testo, ico, cmd, side in [
        ("  Esporta ", "salva",  lambda: self._esporta_estratti_metodo(tree, var_metodo, var_periodo, var_anno, var_mese, var_giorno), tk.LEFT),
        ("  Chiudi ",  "chiudi", win.destroy, tk.RIGHT),
    ]:
        b = tk.Label(bot_f, image=self.icone_gui.get(ico), text=testo,
                     compound="left", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                     cursor="hand2", font=("Arial", 10, "bold"))
        b.pack(side=side, padx=20)
        b.bind("<Button-1>", lambda e, c=cmd: c())
    on_periodo()

def _esporta_estratti_metodo(self, tree, var_metodo, var_periodo, var_anno, var_mese, var_giorno):
    metodo = var_metodo.get() or "Tutti i metodi"
    periodo = var_periodo.get()
    if periodo == "tutto":
        periodo_str = "Tutto il periodo"
    elif periodo == "anno":
        periodo_str = f"Anno {var_anno.get()}"
    elif periodo == "mese":
        periodo_str = f"{var_mese.get()}/{var_anno.get()}"
    else:
        periodo_str = f"{var_giorno.get()}/{var_mese.get()}/{var_anno.get()}"
    C_DATA  = 12
    C_CAT   = 22
    C_DESC  = 34
    C_IMP   = 14
    C_CNT   = 14
    SEP     = "─" * (C_DATA + C_CAT + C_DESC + C_IMP * 2 + C_CNT + 5)
    righe = []
    righe.append("ESTRATTI PER METODO DI PAGAMENTO E CONTI")
    righe.append(f"Metodo  : {metodo}")
    righe.append(f"Periodo : {periodo_str}")
    righe.append(SEP)
    righe.append(
        f"{'Data':<{C_DATA}} {'Categoria':<{C_CAT}} {'Descrizione':<{C_DESC}} {'Entrata':>{C_IMP}} {'Uscita':>{C_IMP}} {'Conto':<{C_CNT}}"
    )
    righe.append(SEP)
    tot_e = 0.0
    tot_u = 0.0
    for iid in tree.get_children():
        v    = tree.item(iid, "values")
        data = str(v[0])
        cat  = str(v[1])[:C_CAT]
        desc = str(v[2])[:C_DESC]
        e_str = str(v[3]).strip()
        u_str = str(v[4]).strip()
        conto = str(v[5]).strip() if len(v) > 5 else ""
        righe.append(
            f"{data:<{C_DATA}} {cat:<{C_CAT}} {desc:<{C_DESC}} {e_str:>{C_IMP}} {u_str:>{C_IMP}} {conto:<{C_CNT}}"
        )
        try:
            tot_e += float(e_str.replace("+","").replace("€","").strip()) if e_str else 0
            tot_u += float(u_str.replace("-","").replace("€","").strip()) if u_str else 0
        except:
            pass
    saldo = tot_e - tot_u
    righe.append(SEP)
    righe.append(f"{'Totale Entrate:':>{C_DATA+C_CAT+C_DESC+2}} {f'+{tot_e:.2f} €':>{C_IMP}} {'':>{C_IMP}}")
    righe.append(f"{'Totale Uscite:':{C_DATA+C_CAT+C_DESC+2}} {'':>{C_IMP}} {f'-{tot_u:.2f} €':>{C_IMP}}")
    righe.append(f"{'Saldo:':{C_DATA+C_CAT+C_DESC+2}} {f'{saldo:+.2f} €':>{C_IMP}} {'':>{C_IMP}}")
    contenuto = "\n".join(righe)
    oggi = datetime.date.today()
    nome_file = f"Estratti_{metodo.split()[0] if metodo else 'tutti'}_{oggi.strftime('%d-%m-%Y')}.txt"
    self.show_export_preview(contenuto, nome_file)
