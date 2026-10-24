#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import datetime
import tkinter as tk
from tkinter import ttk
from moduli.modello_spesa import campo, METODI_PAGAMENTO_EMOJI, NOME_DA_EMOJI, metodo_pagamento_pulito
from moduli.mappa_conti_trasferimenti import costruisci_mappa_conti_da_trasferimenti, conto_da_mappa

MESI = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
TUTTI = ""

def _data_libera(s):
    s = str(s or "").strip().replace("/", "-").replace(".", "-")
    if not s:
        return None
    try:
        return datetime.datetime.strptime(s, "%d-%m-%Y").date()
    except Exception:
        return None

def apri_estratti_metodo(self, metodo=None, mese=None, anno=None, conto=None):
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO

    metodi_lista = [""] + METODI_PAGAMENTO_EMOJI
    win = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    win.title("Estratti per Metodo di Pagamento e Conti")
    win.withdraw()
    self.update_idletasks()
    w, h = 1300, 620
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")
    win.minsize(w, h)
    win.transient(self)
    win.deiconify()
    win.lift()
    win.focus_force()
    win.bind("<Escape>", lambda e: win.destroy())
    bg_f = self.COLOR_TOPLEVEL
    try:
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
            _db_p_em = json.load(_pf)
        _conti_em = [c.get("nome", "?") for c in _db_p_em.get("conti", [])]
    except Exception:
        _conti_em = []
    _agganci_em = costruisci_mappa_conti_da_trasferimenti(PORTAFOGLIO_BANCARIO)
    _anni_f = sorted({str(d.year) for d in self.spese}, reverse=True)
    _profilo_f = getattr(_app, "PROFILO_ATTIVO", "Principale")
    _gestore_f = _profilo_f if _profilo_f != "Principale" else os.path.basename(os.getcwd())
    _nomi_f = [(p.get("nome", "") if isinstance(p, dict) else p) for p in self.nomi_partecipanti] if getattr(self, "nomi_partecipanti", None) else []
    _partec_f = [TUTTI]
    if self._gestore_partecipa() and _gestore_f not in _nomi_f:
        _partec_f.append(f"PER· {_gestore_f}")
    if getattr(self, "nomi_partecipanti", None):
        _partec_f += [
            f"CTP· {p['nome']}" if p.get("tipo") == "personale" else
            f"CNT· {p['nome']}" if p.get("tipo") == "contenitore" else
            f"PER· {p['nome']}"
            for p in sorted(self.nomi_partecipanti, key=lambda p: p["nome"].lower())
        ]
    var_tipo = tk.StringVar(value=TUTTI)
    var_categoria = tk.StringVar(value=TUTTI)
    var_anno = tk.StringVar(value=TUTTI)
    var_mese = tk.StringVar(value=TUTTI)
    var_partec = tk.StringVar(value=TUTTI)
    var_conto_em = tk.StringVar(value=TUTTI)
    var_metodo = tk.StringVar(value=TUTTI)
    var_tag = tk.StringVar(value="")
    var_testo = tk.StringVar(value="")
    var_imp_da = tk.StringVar(value="")
    var_imp_a = tk.StringVar(value="")
    var_da = tk.StringVar(value="")
    var_a = tk.StringVar(value="")
    tutte_var = (var_tipo, var_categoria, var_anno, var_mese, var_partec, var_conto_em, var_metodo,
                 var_tag, var_testo, var_imp_da, var_imp_a, var_da, var_a)
    stato_f = {"aperta": False, "sosp": False}
    head = tk.Frame(win, bg=bg_f)
    head.pack(fill="x", padx=10, pady=(8, 2))
    lbl_freccia = tk.Label(head, bg=bg_f, fg="#DC3545", cursor="hand2", font=("Arial", 11, "bold"), width=2)
    lbl_freccia.pack(side="left")
    lbl_head = tk.Label(head, bg=bg_f, fg=self.TEXT_COLOR, cursor="hand2", font=("Arial", 9, "bold"), anchor="w")
    lbl_head.pack(side="left")
    body = tk.Frame(win, bg=bg_f)
    def _riga_f():
        r = tk.Frame(body, bg=bg_f)
        r.pack(fill="x", pady=2, padx=10)
        return r
    def _etichetta_f(r, testo, pad=(10, 4)):
        tk.Label(r, text=testo, bg=bg_f, fg=self.TEXT_COLOR).pack(side="left", padx=pad)
    def _combo_f(r, var, valori, w):
        c = ttk.Combobox(r, values=valori, textvariable=var, style="Border.TCombobox",
                         state="readonly", width=w)
        c.pack(side="left")
        return c
    r1, r2 = _riga_f(), _riga_f()
    _etichetta_f(r1, "Tipo:", (4, 4))
    _combo_f(r1, var_tipo, [TUTTI, "Entrata", "Uscita"], 9)
    _etichetta_f(r1, "Categoria:")
    _combo_f(r1, var_categoria, [TUTTI] + sorted(self.categorie_tipi.keys()), 18)
    _etichetta_f(r1, "Anno:")
    _combo_f(r1, var_anno, [TUTTI] + _anni_f, 7)
    _etichetta_f(r1, "Mese:")
    _combo_f(r1, var_mese, [TUTTI] + MESI, 11)
    _etichetta_f(r1, "Partecipanti:")
    _combo_f(r1, var_partec, _partec_f, 18)
    _etichetta_f(r1, "Conto:")
    self._combo_conto_em = _combo_f(r1, var_conto_em, [TUTTI] + _conti_em, 16)
    _etichetta_f(r1, "Metodo Pag.:")
    _combo_f(r1, var_metodo, [TUTTI] + METODI_PAGAMENTO_EMOJI, 20)
    _etichetta_f(r2, "Hashtag:", (4, 4))
    ttk.Entry(r2, textvariable=var_tag, width=14).pack(side="left")
    _etichetta_f(r2, "Descrizione contiene:")
    ttk.Entry(r2, textvariable=var_testo, width=20).pack(side="left")
    _etichetta_f(r2, "Importo da:")
    ttk.Entry(r2, textvariable=var_imp_da, width=9).pack(side="left")
    _etichetta_f(r2, "a:", (6, 4))
    ttk.Entry(r2, textvariable=var_imp_a, width=9).pack(side="left")
    def _cal_btn(entry, var):
        def apri(_e=None):
            self.mostra_calendario_popup(entry, var)
            try:
                pc = getattr(self, "popup_calendario", None)
                if pc is not None and pc.winfo_exists():
                    pc.attributes("-topmost", True)
                    pc.lift()
            except tk.TclError:
                pass
        img = self.icone_gui.get("calendario")
        b = tk.Label(r2, image=img, bg=bg_f, cursor="hand2", padx=2)
        if img is None:
            b.config(text="📅")
        else:
            b.image = img
        b.pack(side="left", padx=(2, 0))
        b.bind("<Button-1>", apri)
    _etichetta_f(r2, "Dal:")
    entry_da = ttk.Entry(r2, textvariable=var_da, width=11)
    entry_da.pack(side="left")
    _cal_btn(entry_da, var_da)
    _etichetta_f(r2, "Al:", (8, 4))
    entry_a = ttk.Entry(r2, textvariable=var_a, width=11)
    entry_a.pack(side="left")
    _cal_btn(entry_a, var_a)
    tk.Label(r2, text="(GG-MM-AAAA)", bg=bg_f, fg="gray", font=("Arial", 8, "italic")).pack(side="left", padx=(4, 0))
    def _num_f(x):
        x = str(x or "").strip().replace("€", "").replace(" ", "")
        if not x:
            return None
        if "," in x:
            x = x.replace(".", "").replace(",", ".")
        try:
            return float(x)
        except ValueError:
            return None
    def _descr_filtri():
        out = []
        for var, etich in ((var_tipo, ""), (var_categoria, "Categoria "), (var_anno, "Anno "), (var_mese, ""),
                           (var_partec, ""), (var_conto_em, "Conto "), (var_metodo, "Metodo ")):
            if var.get():
                out.append(f"{etich}{var.get()}")
        tags = [t for t in re.split(r"[\s,;]+", var_tag.get().strip()) if t.lstrip("#")]
        if tags:
            out.append(" ".join(f"#{t.lstrip('#')}" for t in tags))
        if var_testo.get().strip():
            out.append(f"«{var_testo.get().strip()}»")
        ida, ia = _num_f(var_imp_da.get()), _num_f(var_imp_a.get())
        if ida is not None or ia is not None:
            out.append(f"Importo {_app._fmt_it(ida) if ida is not None else '…'} → {_app._fmt_it(ia) if ia is not None else '…'}")
        da, a = _data_libera(var_da.get()), _data_libera(var_a.get())
        if da or a:
            out.append(f"{da.strftime('%d-%m-%Y') if da else '…'} → {a.strftime('%d-%m-%Y') if a else '…'}")
        return out
    def aggiorna_testata():
        d = _descr_filtri()
        stato_txt = ("filtri attivi: " + ", ".join(d)) if d else "nessun filtro attivo"
        lbl_freccia.config(text="▾" if stato_f["aperta"] else "▸")
        lbl_head.config(text=f"Filtri avanzati  ({stato_txt})",
                        fg=getattr(self, "COLOR_HIGHLIGHT", self.TEXT_COLOR) if d else self.TEXT_COLOR)
    def apri_chiudi_filtri(*_):
        stato_f["aperta"] = not stato_f["aperta"]
        if stato_f["aperta"]:
            body.pack(fill="x", before=frame_tot)
        else:
            body.pack_forget()
        aggiorna_testata()
    for _w in (lbl_freccia, lbl_head):
        _w.bind("<Button-1>", apri_chiudi_filtri)
    frame_tot = ttk.Frame(win, style="BlackFrame.TFrame")
    frame_tot.pack(fill=tk.X, padx=8, pady=2)
    lbl_entrate = ttk.Label(frame_tot, text="Entrate:", foreground="lightgreen",
                            background=self.COLOR_WIDGET_BG, font=("Arial", 9, "bold"))
    lbl_entrate.pack(side="left", padx=8)
    lbl_uscite = ttk.Label(frame_tot, text="Uscite:", foreground="lightcoral",
                           background=self.COLOR_WIDGET_BG, font=("Arial", 9, "bold"))
    lbl_uscite.pack(side="left", padx=8)
    lbl_saldo = ttk.Label(frame_tot, text="Saldo:", foreground="khaki",
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
    cols = ("data", "categoria", "descrizione", "entrata", "uscita", "conto", "metodo", "ora", "tag")
    tree = ttk.Treeview(frame_tree, columns=cols, show="headings", style="Treeview", selectmode='browse')
    tree.heading("data",        text="Data")
    tree.heading("categoria",   text="Categoria")
    tree.heading("descrizione", text="Descrizione")
    tree.heading("entrata",     text="Entrata")
    tree.heading("uscita",      text="Uscita")
    tree.heading("conto",       text="Conto")
    tree.heading("metodo",      text="Metodo")
    tree.heading("ora",         text="Ora")
    tree.heading("tag",         text="Tag")
    tree.column("data",        width=90,  anchor="center")
    tree.column("categoria",   width=120, anchor="w")
    tree.column("descrizione", width=230, anchor="w")
    tree.column("entrata",     width=100, anchor="center")
    tree.column("uscita",      width=100, anchor="center")
    tree.column("conto",       width=100, anchor="w")
    tree.column("metodo",      width=110, anchor="w")
    tree.column("ora",         width=60,  anchor="center")
    tree.column("tag",         width=100, anchor="w")
    testi_col = {"data": "Data", "categoria": "Categoria", "descrizione": "Descrizione",
                 "entrata": "Entrata", "uscita": "Uscita", "conto": "Conto", "metodo": "Metodo",
                 "ora": "Ora", "tag": "Tag"}
    for col in cols:
        tree.heading(col, text=testi_col[col],
                     command=lambda c=col: self.treeview_sort_column(tree, c, False))
    sb = ttk.Scrollbar(frame_tree, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.pack(side="left", fill=tk.BOTH, expand=True)
    sb.pack(side="right", fill=tk.Y)
    tree.tag_configure("entrata", foreground="green")
    tree.tag_configure("uscita",  foreground="red")
    tree.tag_configure("futuro",  foreground="#E5C07B", font=("Arial", 9, "italic"))
    tree.tag_configure("sforato", foreground='#C08081', font=("Arial", 9, "bold"))
    def on_doppio_clic(event):
        item_id = tree.identify_row(event.y)
        if not item_id:
            return
        vals = tree.item(item_id, "values")
        if not vals:
            return
        data_str = vals[0]
        try:
            giorno = datetime.datetime.strptime(data_str, "%d-%m-%Y").date()
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
        imp_val = abs(_app._parse_it_float(entrata if entrata else uscita))
        tipo = "Entrata" if entrata.strip() else "Uscita"
        cat_match = next((c for c in self.categorie if c.strip().lower() == categoria.lower()), None)
        if cat_match:
            self.cat_sel.set(cat_match)
            self.cat_menu.set(cat_match)
            self.on_categoria_changed(manuale=False)
        try:
            self.imp_entry.delete(0, tk.END)
            self.imp_entry.insert(0, f"{imp_val:.2f}".replace(".", ","))
        except ValueError:
            pass
        self.desc_entry.delete(0, tk.END)
        if "RIC·" not in descrizione:
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
        tree._metodo_lookup = {}
        metodo_sel = var_metodo.get()
        _nome_metodo_sel = metodo_pagamento_pulito(metodo_sel)
        _emoji_a_nome = NOME_DA_EMOJI
        anno_f = var_anno.get()
        mese_f = MESI.index(var_mese.get()) + 1 if var_mese.get() in MESI else None
        conto_f = var_conto_em.get()
        tipo_f = var_tipo.get().lower()
        cat_f = var_categoria.get().lower()
        testo_f = var_testo.get().strip().lower()
        tag_f = [t.lstrip("#").lower() for t in re.split(r"[\s,;]+", var_tag.get().strip()) if t.lstrip("#")]
        imp_da_f = _num_f(var_imp_da.get())
        imp_a_f = _num_f(var_imp_a.get())
        partec_f = var_partec.get()
        for _pref in ("CTP· ", "CNT· ", "PER· "):
            if partec_f.startswith(_pref):
                partec_f = partec_f[len(_pref):]
                break
        _candidati_owner = list(self.nomi_partecipanti) if getattr(self, "nomi_partecipanti", None) else []
        if self._gestore_partecipa() and not any(
                (p.get("nome", "") if isinstance(p, dict) else p) == _gestore_f for p in _candidati_owner):
            _candidati_owner.append({"nome": _gestore_f})
        da = _data_libera(var_da.get())
        a = _data_libera(var_a.get())
        tot_e = 0.0
        tot_u = 0.0
        righe = []
        _uso_ordinale_em = {}
        for data_obj, voci in sorted(self.spese.items()):
            if anno_f and str(data_obj.year) != anno_f:
                continue
            if mese_f and data_obj.month != mese_f:
                continue
            if da and data_obj < da:
                continue
            if a and data_obj > a:
                continue
            for voce in voci:
                cat     = campo(voce, "categoria", "").strip()
                desc    = campo(voce, "descrizione", "").strip()
                importo = float(campo(voce, "importo", 0.0))
                tipo    = campo(voce, "tipo", "").strip()
                metodo_voce = campo(voce, "metodo_pagamento", "")
                if not metodo_voce:
                    for _sim, _nome in _emoji_a_nome.items():
                        if _sim in desc:
                            metodo_voce = _nome
                            break
                if _nome_metodo_sel and metodo_voce != _nome_metodo_sel:
                    continue
                if tipo_f and tipo.lower() != tipo_f:
                    continue
                if cat_f and cat.lower() != cat_f:
                    continue
                if testo_f and testo_f not in desc.lower():
                    continue
                _tag_txt = " ".join(campo(voce, "hashtag", []) or []).lower()
                if tag_f and not all(t in _tag_txt for t in tag_f):
                    continue
                if imp_da_f is not None and importo < imp_da_f:
                    continue
                if imp_a_f is not None and importo > imp_a_f:
                    continue
                if partec_f:
                    _dl = desc.lower()
                    _owner = next((p["nome"] if isinstance(p, dict) else p for p in _candidati_owner
                                   if any(f"{ico}{(p['nome'] if isinstance(p, dict) else p)}".lower() in _dl
                                          or f"{ico} {(p['nome'] if isinstance(p, dict) else p)}".lower() in _dl
                                          for ico in ("PER·", "CTP·", "CNT·"))), "")
                    if partec_f.lower() != _owner.lower():
                        continue
                _conto_espl_em = self._conto_effettivo(voce)
                if _conto_espl_em:
                    nome_conto_em = _conto_espl_em
                else:
                    nome_conto_em = conto_da_mappa(_agganci_em, _uso_ordinale_em, data_obj.strftime("%d-%m-%Y"), importo, tipo)
                if conto_f and nome_conto_em != conto_f:
                    continue
                data_str = data_obj.strftime("%d-%m-%Y")
                ora_voce = campo(voce, "ora", "")
                tag_voce = " ".join(campo(voce, "hashtag", []) or [])
                oggi_em = datetime.date.today()
                if data_obj > oggi_em:
                    tag_colore = "futuro"
                elif tipo == "Entrata":
                    tag_colore = "entrata"
                else:
                    tag_colore = "uscita"
                    if ((data_obj.year, data_obj.month) == (oggi_em.year, oggi_em.month)
                            and cat in getattr(self, "_budget_sforati", set())):
                        tag_colore = "sforato"
                if tipo == "Entrata":
                    tot_e += importo
                    righe.append((data_obj, data_str, cat, desc, f"{_app._fmt_it(importo)} €", "", tag_colore, nome_conto_em, metodo_voce, ora_voce, tag_voce, voce))
                else:
                    tot_u += importo
                    righe.append((data_obj, data_str, cat, desc, "", f"{_app._fmt_it(importo)} €", tag_colore, nome_conto_em, metodo_voce, ora_voce, tag_voce, voce))
        righe.sort(key=lambda r: (r[0], r[9]), reverse=True)
        for r in righe:
            _iid_em = tree.insert("", "end", values=(r[1], r[2], r[3], r[4], r[5], r[7], r[8], r[9], r[10]), tags=(r[6],))
            _v_em = r[11]
            _tipo_em = campo(_v_em, "tipo", "").strip()
            tree._metodo_lookup[_iid_em] = {
                "metodo": metodo_pagamento_pulito(r[8]),
                "conto": r[7],
                "ora": r[9],
                "hashtag": list(campo(_v_em, "hashtag", []) or []),
                "id_ricorrenza": campo(_v_em, "id_ricorrenza", "") or "",
                "id_spesa": campo(_v_em, "id_spesa", "") or "",
                "data": r[1],
                "categoria": r[2],
                "importo": float(campo(_v_em, "importo", 0.0)),
                "tipo": _tipo_em,
            }
        saldo = tot_e - tot_u
        lbl_entrate.config(text=f"Entrate: {_app._fmt_it(tot_e)} €")
        lbl_uscite.config(text=f"Uscite: {_app._fmt_it(tot_u)} €")
        lbl_saldo.config(text=f"Saldo: {_app._fmt_it(saldo, spec='+,.2f')} €",
                         foreground="lightgreen" if saldo >= 0 else "lightcoral")
        lbl_count.config(text=f"Movimenti: {len(righe)}")
    def applica_filtri(*_):
        if stato_f["sosp"]:
            return
        for e, v in ((entry_da, var_da), (entry_a, var_a)):
            sbagliata = bool(v.get().strip()) and _data_libera(v.get()) is None
            try:
                e.configure(foreground="#DC3545" if sbagliata else self.TEXT_COLOR)
            except tk.TclError:
                pass
        aggiorna_testata()
        aggiorna()
    def resetta_filtri(*_):
        stato_f["sosp"] = True
        try:
            for v in tutte_var:
                v.set("")
        finally:
            stato_f["sosp"] = False
        applica_filtri()
    for _v in tutte_var:
        _v.trace_add("write", applica_filtri)
    if metodo:
        var_metodo.set(metodo)
    if anno:
        var_anno.set(str(anno))
    if mese:
        try:
            var_mese.set(MESI[int(mese) - 1])
        except (ValueError, IndexError):
            pass
    if conto:
        _conto_norm_em = conto.strip().lower()
        _match_conto_em = next((c for c in _conti_em if c.strip().lower() == _conto_norm_em), None)
        if _match_conto_em is None and conto.strip():
            _match_conto_em = conto.strip()
            _conti_em.append(_match_conto_em)
            if hasattr(self, '_combo_conto_em') and self._combo_conto_em.winfo_exists():
                self._combo_conto_em['values'] = ["Tutti"] + _conti_em
        if _match_conto_em:
            var_conto_em.set(_match_conto_em)
    bot_f = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    bot_f.pack(fill=tk.X, side=tk.BOTTOM, pady=10)
    for testo, ico, cmd, side in [
        ("  Esporta ", "salva",  lambda: self._esporta_estratti_metodo(tree, var_metodo, _descr_filtri), tk.LEFT),
        ("  Reset ",   "reset",  resetta_filtri, tk.LEFT),
        ("  Chiudi ",  "chiudi", win.destroy, tk.RIGHT),
    ]:
        b = tk.Label(bot_f, image=self.icone_gui.get(ico), text=testo,
                     compound="left", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                     cursor="hand2", font=("Arial", 10, "bold"))
        b.pack(side=side, padx=20)
        b.bind("<Button-1>", lambda e, c=cmd: c())
    aggiorna_testata()
    aggiorna()
    def _refresh_da_modifica_esterna():
        try:
            pos = tree.yview()[0]
            aggiorna()
            tree.yview_moveto(pos)
        except tk.TclError:
            pass
    if hasattr(self, "registra_refresh_finestra"):
        self.registra_refresh_finestra(win, _refresh_da_modifica_esterna)

def _esporta_estratti_metodo(self, tree, var_metodo, descr_filtri):
    import __main__ as _app
    metodo = var_metodo.get() or "Tutti i metodi"
    periodo_str = ", ".join(descr_filtri()) or "Tutto il periodo"
    C_DATA  = 12
    C_CAT   = 20
    C_DESC  = 28
    C_IMP   = 13
    C_CNT   = 12
    C_MET   = 12
    SEP     = "─" * (C_DATA + C_CAT + C_DESC + C_IMP * 2 + C_CNT + C_MET + 6)
    righe = []
    righe.append("ESTRATTI PER METODO DI PAGAMENTO E CONTI")
    righe.append(f"Metodo  : {metodo}")
    righe.append(f"Periodo : {periodo_str}")
    righe.append(SEP)
    righe.append(
        f"{'Data':<{C_DATA}} {'Categoria':<{C_CAT}} {'Descrizione':<{C_DESC}} {'Entrata':>{C_IMP}} {'Uscita':>{C_IMP}} {'Conto':<{C_CNT}} {'Metodo':<{C_MET}}"
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
        conto = str(v[5]).strip()[:C_CNT] if len(v) > 5 else ""
        met   = str(v[6]).strip()[:C_MET] if len(v) > 6 else ""
        righe.append(
            f"{data:<{C_DATA}} {cat:<{C_CAT}} {desc:<{C_DESC}} {e_str:>{C_IMP}} {u_str:>{C_IMP}} {conto:<{C_CNT}} {met:<{C_MET}}"
        )
        try:
            tot_e += abs(_app._parse_it_float(e_str)) if e_str else 0
            tot_u += abs(_app._parse_it_float(u_str)) if u_str else 0
        except Exception:
            pass
    saldo = tot_e - tot_u
    righe.append(SEP)
    righe.append(f"{'Totale Entrate:':>{C_DATA+C_CAT+C_DESC+2}} {f'{_app._fmt_it(tot_e)} €':>{C_IMP}} {'':>{C_IMP}}")
    righe.append(f"{'Totale Uscite:':>{C_DATA+C_CAT+C_DESC+2}} {'':>{C_IMP}} {f'{_app._fmt_it(tot_u)} €':>{C_IMP}}")
    _saldo_fmt = f"{_app._fmt_it(saldo, spec='+,.2f')} €"
    righe.append(f"{'Saldo:':>{C_DATA+C_CAT+C_DESC+2}} {_saldo_fmt:>{C_IMP}} {'':>{C_IMP}}")
    contenuto = "\n".join(righe)
    oggi = datetime.date.today()
    nome_file = f"Estratti_{metodo_pagamento_pulito(metodo) if metodo != 'Tutti i metodi' else 'tutti'}_{oggi.strftime('%d-%m-%Y')}.txt"
    self.show_export_preview(contenuto, nome_file)

