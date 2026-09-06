#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import datetime
import tkinter as tk
from tkinter import ttk, filedialog
from moduli.modello_spesa import campo, METODI_PAGAMENTO, METODI_PAGAMENTO_EMOJI
from moduli.mappa_conti_trasferimenti import costruisci_mappa_conti_da_trasferimenti, conto_da_mappa

def _fmt_it(v, spec=",.2f"):
    s = format(v, spec)
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")

def cerca_operazioni(self):
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    EXPORT_FILES         = _app.EXPORT_FILES
    self.mostra_treeview_statistiche()
    larghezza, altezza = 1366, 600
    x = self.winfo_screenwidth() // 2 - larghezza // 2
    y = self.winfo_screenheight() // 2 - altezza // 2
    finestra = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    finestra.withdraw()
    self._finestra_cerca = finestra
    finestra.title("Ricerca operazioni")
    finestra.geometry(f"{larghezza}x{altezza}+{x}+{y}")
    finestra.minsize(larghezza, altezza)
    finestra.transient(self)
    finestra.bind("<Escape>", lambda e: finestra.destroy())
    frame_superiore = tk.Frame(finestra, bg=self.COLOR_TOPLEVEL)
    frame_superiore.pack(fill="x", pady=10, padx=10)
    tk.Label(
        frame_superiore,
        image=self.icone_gui.get("search"),
        text=" Ricerca:",
        compound="left",
        bg=self.COLOR_TOPLEVEL,
        fg=self.TEXT_COLOR,
        font=("Arial", 9, "bold")
    ).pack(side="left")
    campo_input = ttk.Entry(frame_superiore, width=22)
    campo_input.pack(side="left", padx=8)
    campo_input.focus_set()
    mostra_futuro_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(frame_superiore, text="Includi Futuri", variable=mostra_futuro_var).pack(side="left", padx=(0, 8))
    tk.Label(frame_superiore, text="Dal:", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 9)).pack(side="left", padx=(4, 2))
    da_data_var = tk.StringVar(value="")
    da_data_entry = ttk.Entry(frame_superiore, textvariable=da_data_var, width=11)
    da_data_entry.pack(side="left")
    btn_cal_da = ttk.Label(frame_superiore, text="📅", cursor="hand2",
                           background=self.COLOR_WIDGET_BG, padding=(3, 2))
    btn_cal_da.pack(side="left", padx=(2, 8))
    btn_cal_da.bind("<Button-1>", lambda e: self.mostra_calendario_popup_semplice(da_data_entry, da_data_var))
    tk.Label(frame_superiore, text="Al:", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 9)).pack(side="left", padx=(0, 2))
    a_data_var = tk.StringVar(value="")
    a_data_entry = ttk.Entry(frame_superiore, textvariable=a_data_var, width=11)
    a_data_entry.pack(side="left")
    btn_cal_a = ttk.Label(frame_superiore, text="📅", cursor="hand2",
                          background=self.COLOR_WIDGET_BG, padding=(3, 2))
    btn_cal_a.pack(side="left", padx=(2, 8))
    btn_cal_a.bind("<Button-1>", lambda e: self.mostra_calendario_popup_semplice(a_data_entry, a_data_var))
    img_mouse = self.icone_gui.get("mouse")
    lbl_hint = ttk.Label(
        frame_superiore,
        text="Doppio clic → Vai alla spesa sulla Dashboard  |  Clic destro → popola campi inserimento ",
        image=img_mouse,
        compound="right",
        foreground="gray",
        font=("Arial", 8, "italic")
    )
    if img_mouse:
        lbl_hint.image = img_mouse
    lbl_hint.pack(side=tk.RIGHT, padx=(10, 0))
    frame_risultati = tk.Frame(finestra)
    frame_risultati.pack(fill="both", expand=True, padx=10)
    columns = ("Data", "Categoria", "Descrizione", "Tipo", "Importo", "Conto", "Ora", "Hashtag", "Metodo")
    tree = ttk.Treeview(frame_risultati, columns=columns, show="headings", selectmode='browse')
    tree.pack(side="left", fill="both", expand=True)
    def on_right_click(event):
        item_id = tree.identify_row(event.y)
        if not item_id:
            return
        values = tree.item(item_id, "values")
        if not values:
            return
        categoria   = str(values[1]).strip()
        descrizione = str(values[2]).strip()
        importo_str = str(values[4]).replace("€", "").replace(" ", "").strip()
        if "," in importo_str:
            importo_str = importo_str.replace(".", "").replace(",", ".")
        tipo = str(values[3]).strip().capitalize()
        cat_match = next(
            (c for c in self.categorie if c.strip().lower() == categoria.lower()), None
        )
        if cat_match:
            self.cat_sel.set(cat_match)
            self.cat_menu.set(cat_match)
            self.on_categoria_changed(manuale=False)
        try:
            self.imp_entry.delete(0, tk.END)
            self.imp_entry.insert(0, f"{float(importo_str):.2f}".replace(".", ","))
        except ValueError:
            pass
        self.desc_entry.delete(0, tk.END)
        if "RIC·" not in descrizione:
            self.desc_entry.insert(0, descrizione[:30])
        if self.tipo_spesa_var.get() != tipo:
            self.toggle_tipo_spesa()
        self.after(0, self.imp_entry.focus_set)
        finestra.destroy()
    tree.bind("<Double-1>", self.cerca_doppio_click)
    tree.bind("<Button-3>", on_right_click)
    def converti_importo(s):
        s = str(s).strip().replace('€', '').strip().replace(',', '')
        if s.count(',') == 1 and s.count('.') != 1:
            s = s.replace(',', '.')
        try:
            return float(s)
        except ValueError:
            return float('-inf')
    def converti_data(s):
        try:
            return datetime.datetime.strptime(str(s), '%d/%m/%Y')
        except ValueError:
            return datetime.datetime.min
    def formatta_italiano(numero):
        return "{:,.2f}".format(numero).replace('.', '#').replace(',', '.').replace('#', ',')
    def sort_by_column(tv, col, reverse):
        cols = list(tv["columns"])
        try:
            col_index = cols.index(col)
        except ValueError:
            return
        l = []
        for k in tv.get_children(''):
            item_values = tv.item(k, 'values')
            if item_values and len(item_values) > col_index:
                if col == "Importo":
                    sort_value = converti_importo(item_values[col_index])
                elif col == "Data":
                    sort_value = converti_data(item_values[col_index])
                else:
                    sort_value = item_values[col_index]
                l.append((sort_value, k))
            else:
                l.append(('', k))
        l.sort(key=lambda t: t[0], reverse=reverse)
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)
        tv.heading(col, command=lambda: sort_by_column(tv, col, not reverse))
    for col in columns:
        tree.heading(col, text=col, command=lambda c=col: sort_by_column(tree, c, False))
        tree.column(col, anchor="e" if col == "Importo" else "w")
    tree.column("Data",        width=90,  stretch=False)
    tree.column("Categoria",   width=120, stretch=False)
    tree.column("Descrizione", width=260, stretch=True)
    tree.column("Tipo",        width=80,  stretch=False)
    tree.column("Importo",     width=100, stretch=False)
    tree.column("Conto",       width=100, stretch=False)
    tree.column("Ora",         width=55,  stretch=False)
    tree.column("Hashtag",     width=130, stretch=False)
    tree.column("Metodo",      width=110, stretch=False)
    scroll = ttk.Scrollbar(frame_risultati, orient="vertical", command=tree.yview, style="Vertical.TScrollbar")
    tree.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    tree.tag_configure("entrata_tag", foreground="green")
    tree.tag_configure("uscita_tag",  foreground="red")
    tree.tag_configure("neutro_tag",  foreground="gray")
    tree.tag_configure("futuro_tag",  foreground="#E5C07B", font=("Arial", 9, "italic"))
    tree.tag_configure("sforato_tag", foreground="#C08081", font=("Arial", 9, "bold"))
    frame_totali = tk.Frame(finestra)
    frame_totali.pack(fill="x", pady=10, padx=10)
    lbl_risultati = tk.Label(frame_totali, text="", anchor="w", font=("Arial", 10))
    lbl_risultati.pack(fill="x")
    lbl_totali = tk.Label(frame_totali, text="", anchor="w", font=("Arial", 10, "bold"))
    lbl_totali.pack(fill="x")
    def esegui_ricerca(event=None):
        parola = campo_input.get().strip().lower()
        filtri = getattr(self, "filtri_avanzati", {})
        if parola:
            filtri = {}
        for item in tree.get_children():
            tree.delete(item)
        risultati = []
        oggi = datetime.date.today()
        mostra_futuro = mostra_futuro_var.get()
        da_data = None
        a_data  = None
        try:
            if da_data_var.get().strip():
                da_data = datetime.datetime.strptime(da_data_var.get().strip(), "%d-%m-%Y").date()
        except ValueError:
            pass
        try:
            if a_data_var.get().strip():
                a_data = datetime.datetime.strptime(a_data_var.get().strip(), "%d-%m-%Y").date()
        except ValueError:
            pass
        _agganci_cerca = costruisci_mappa_conti_da_trasferimenti(PORTAFOGLIO_BANCARIO)
        _uso_ordinale_cerca = {}
        _profilo_attivo_co = getattr(_app, "PROFILO_ATTIVO", "Principale")
        _gestore_nome_cerca_owner = _profilo_attivo_co if _profilo_attivo_co != "Principale" else os.path.basename(os.getcwd())
        _candidati_owner = list(self.nomi_partecipanti) if hasattr(self, "nomi_partecipanti") and self.nomi_partecipanti else []
        if self._gestore_partecipa() and not any(
                (p.get("nome", "") if isinstance(p, dict) else p) == _gestore_nome_cerca_owner
                for p in _candidati_owner):
            _candidati_owner.append({"nome": _gestore_nome_cerca_owner})
        for data_key in sorted(self.spese.keys(), reverse=True):
            try:
                d = data_key if isinstance(data_key, datetime.date) else datetime.datetime.strptime(data_key, "%d-%m-%Y").date()
            except ValueError:
                d = datetime.datetime.strptime(data_key, "%Y-%m-%d").date()
            if not mostra_futuro and d > oggi:
                continue
            if da_data and d < da_data:
                continue
            if a_data and d > a_data:
                continue
            for voce in self.spese[data_key]:
                categoria    = str(voce[0]).lower()
                descrizione  = str(voce[1]).lower()
                importo_voce = voce[2]
                tipo         = str(voce[3]).lower()
                owner = next((p["nome"] for p in _candidati_owner
                              if any(f"{ico}{p['nome']}".lower() in descrizione or f"{ico} {p['nome']}".lower() in descrizione
                                     for ico in ("PER·", "CTP·", "CNT·"))), "")
                _conto_espl_cerca = campo(voce, "conto", "")
                if _conto_espl_cerca:
                    nome_conto_cerca = _conto_espl_cerca
                else:
                    nome_conto_cerca = conto_da_mappa(_agganci_cerca, _uso_ordinale_cerca, d.strftime("%d-%m-%Y"), importo_voce, voce[3])
                metodo_cerca  = campo(voce, "metodo_pagamento", "")
                ora_cerca     = campo(voce, "ora", "")
                hashtag_cerca = campo(voce, "hashtag", [])
                hashtag_txt   = " ".join(hashtag_cerca)
                matches = True
                if parola:
                    if not any(parola in str(campo_v).lower() for campo_v in [categoria, descrizione, tipo, str(importo_voce), nome_conto_cerca.lower(), metodo_cerca.lower(), hashtag_txt.lower()]):
                        matches = False
                elif filtri:
                    if filtri.get("descrizione") and filtri["descrizione"].lower() not in descrizione:
                        matches = False
                    if filtri.get("categoria") not in ["", "—"] and categoria != filtri["categoria"].lower():
                        matches = False
                    if filtri.get("tipo") not in ["", "—"] and tipo != filtri["tipo"].lower():
                        matches = False
                    if filtri.get("icona") not in ["", "—"]:
                       simbolo = filtri["icona"].split(" ")[0]
                       if simbolo not in descrizione:
                          matches = False
                    if filtri.get("anno") not in ["", "—"] and str(d.year) != filtri["anno"]:
                        matches = False
                    if filtri.get("mese") not in ["", "—"]:
                        mesi_nomi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                                     "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
                        mesi_map = {m: i+1 for i, m in enumerate(mesi_nomi)}
                        if d.month != mesi_map.get(filtri["mese"], 0):
                            matches = False
                    if filtri.get("partecipanti") not in ["", "—"]:
                        nome_filtro = filtri["partecipanti"]
                        for prefisso in ("CTP· ", "CNT· ", "PER· "):
                            if nome_filtro.startswith(prefisso):
                                nome_filtro = nome_filtro[len(prefisso):]
                                break
                        if nome_filtro.lower() != owner.lower():
                            matches = False
                    if filtri.get("conto") not in ["", "—"] and nome_conto_cerca != filtri["conto"]:
                        matches = False
                    if filtri.get("metodo") not in ["", "—"] and metodo_cerca != filtri["metodo"]:
                        matches = False
                    if filtri.get("hashtag") and filtri["hashtag"].lower().lstrip("#") not in hashtag_txt.lower():
                        matches = False
                    try:
                        da_val = converti_importo(filtri.get("da", "0"))
                        a_val  = converti_importo(filtri.get("a", "999999999"))
                        da_f   = da_val if da_val != float('-inf') else 0.0
                        a_f    = a_val  if a_val  != float('-inf') else 999999999.0
                        if not (da_f <= float(importo_voce) <= a_f):
                            matches = False
                    except (ValueError, TypeError):
                        pass
                if matches:
                    risultati.append({
                        "data":        d.strftime('%d/%m/%Y'),
                        "categoria":   voce[0],
                        "descrizione": voce[1],
                        "importo":     importo_voce,
                        "tipo":        tipo.capitalize(),
                        "partecipante": owner,
                        "conto":       nome_conto_cerca,
                        "metodo":      metodo_cerca,
                        "ora":         ora_cerca,
                        "hashtag":     hashtag_txt
                    })
        risultati.sort(key=lambda x: datetime.datetime.strptime(x['data'], '%d/%m/%Y'), reverse=True)
        tot_entrate = sum(r['importo'] for r in risultati if r['tipo'] == "Entrata")
        tot_uscite  = sum(r['importo'] for r in risultati if r['tipo'] == "Uscita")
        netto       = tot_entrate - tot_uscite
        testo_filtri = ""
        if parola:
            testo_filtri = f"Parola chiave: '{parola}'"
        elif filtri:
            testo_filtri = ", ".join([f"{k.capitalize()}: {v}" for k, v in filtri.items() if v not in ["", "—"]])
        if da_data or a_data:
            periodo = f"Dal {da_data_var.get() or '…'} al {a_data_var.get() or '…'}"
            testo_filtri = f"{testo_filtri} | {periodo}".strip(" | ")
        if not risultati:
            lbl_risultati.config(
                text=" Nessuna corrispondenza per la ricerca attuale.",
                image=self.icone_gui.get("chiudi"),
                compound="left",
                fg="#E06C75",
                bg=self.COLOR_TOPLEVEL
            )
            lbl_totali.config(text="", image="", bg=self.COLOR_TOPLEVEL)
        else:
            colore_saldo = "#98C379" if netto >= 0 else "#E06C75"
            lbl_risultati.config(
                text=f" Trovati {len(risultati)} documenti. | Filtri: {testo_filtri or 'Nessuno'}",
                image=self.icone_gui.get("modifica"),
                compound="left",
                fg="#61AFEF",
                bg=self.COLOR_TOPLEVEL
            )
            lbl_totali.config(
                text=f" Entrate: {formatta_italiano(tot_entrate)} € | Uscite: {formatta_italiano(tot_uscite)} € | Saldo: {formatta_italiano(netto)} €",
                image=self.icone_gui.get("icc"),
                compound="left",
                fg=colore_saldo,
                bg=self.COLOR_TOPLEVEL
            )
            _budget_categorie_ref_cerca = getattr(self, 'budget_categorie', {}) or {}
            _tot_categoria_mese_cache_cerca = {}
            def _budget_categoria_cerca(cat):
                return next(
                    (v for k, v in _budget_categorie_ref_cerca.items() if k.strip().lower() == cat.strip().lower()),
                    0
                )
            def _speso_categoria_mese_cerca(cat, anno_t, mese_t):
                chiave = (anno_t, mese_t, cat.strip().lower())
                if chiave not in _tot_categoria_mese_cache_cerca:
                    tot = 0.0
                    for d2, voci2 in self.spese.items():
                        d2d = d2 if isinstance(d2, datetime.date) else datetime.datetime.strptime(d2, "%d-%m-%Y").date()
                        if d2d.year == anno_t and d2d.month == mese_t:
                            for e2 in voci2:
                                if len(e2) >= 4 and str(e2[0]).strip().lower() == cat.strip().lower() and str(e2[3]).lower() == "uscita":
                                    try:
                                        tot += float(e2[2])
                                    except (ValueError, TypeError):
                                        pass
                    _tot_categoria_mese_cache_cerca[chiave] = tot
                return _tot_categoria_mese_cache_cerca[chiave]
            for riga in risultati:
                tipo_r = riga['tipo'].lower()
                d_riga = datetime.datetime.strptime(riga['data'], '%d/%m/%Y').date()
                if d_riga > datetime.date.today():
                    tag = "futuro_tag"
                elif tipo_r == "entrata":
                    tag = "entrata_tag"
                elif tipo_r == "uscita":
                    tag = "uscita_tag"
                    _budget_val_cerca = _budget_categoria_cerca(str(riga['categoria']))
                    if _budget_val_cerca and _budget_val_cerca > 0:
                        if _speso_categoria_mese_cerca(str(riga['categoria']), d_riga.year, d_riga.month) > _budget_val_cerca:
                            tag = "sforato_tag"
                else:
                    tag = "neutro_tag"
                tree.insert("", "end", values=(
                    riga['data'],
                    riga['categoria'],
                    riga['descrizione'],
                    riga['tipo'],
                    f"{_fmt_it(riga['importo'])} €",
                    riga.get('conto', ''),
                    riga.get('ora', ''),
                    riga.get('hashtag', ''),
                    riga.get('metodo', '')
                ), tags=(tag,))
    campo_input.bind("<KeyRelease>", esegui_ricerca)
    mostra_futuro_var.trace_add("write", lambda *_: esegui_ricerca())
    da_data_var.trace_add("write", lambda *_: esegui_ricerca())
    a_data_var.trace_add("write",  lambda *_: esegui_ricerca())
    def resetta_campo():
        campo_input.delete(0, tk.END)
        da_data_var.set("")
        a_data_var.set("")
        self.filtri_avanzati = {}
        for item in tree.get_children():
            tree.delete(item)
        lbl_risultati.config(text="Nessuna corrispondenza per la ricerca attuale.", fg="gray")
        lbl_totali.config(text="")
        self.after(100, esegui_ricerca)
    img_indietro = self.icone_gui.get("reset")
    btn_reset_superiore = ttk.Label(frame_superiore, compound="left", image=img_indietro,
                                    text=" 🔙" if not img_indietro else "",
                                    background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                                    cursor="hand2", padding=(5, 5))
    btn_reset_superiore.pack(side="left", padx=5)
    btn_reset_superiore.bind("<Button-1>", lambda e: resetta_campo())
    def apri_filtri_avanzati():
        self.filtri_avanzati = getattr(self, "filtri_avanzati", {})
        parola_chiave = campo_input.get().strip()
        campo_input.delete(0, tk.END)
        if parola_chiave:
            self.filtri_avanzati = {}
        filtro_win = tk.Toplevel(finestra, bg=self.COLOR_TOPLEVEL)
        filtro_win.withdraw()
        filtro_win.title("Filtri avanzati")
        lw, lh = 400, 490
        fx = finestra.winfo_rootx() + (finestra.winfo_width()  // 2) - (lw // 2)
        fy = finestra.winfo_rooty() + (finestra.winfo_height() // 2) - (lh // 2)
        filtro_win.geometry(f"{lw}x{lh}+{fx}+{fy}")
        filtro_win.resizable(False, False)
        filtro_win.transient(finestra)
        filtro_win.update_idletasks()
        filtro_win.bind("<Escape>", lambda e: filtro_win.destroy())
        descrizione_var  = tk.StringVar(value=self.filtri_avanzati.get("descrizione",  ""))
        categoria_var    = tk.StringVar(value=self.filtri_avanzati.get("categoria",    "—"))
        tipo_var         = tk.StringVar(value=self.filtri_avanzati.get("tipo",         "—"))
        anno_var         = tk.StringVar(value=self.filtri_avanzati.get("anno",         "—"))
        mese_var         = tk.StringVar(value=self.filtri_avanzati.get("mese",         "—"))
        da_var           = tk.StringVar(value=self.filtri_avanzati.get("da",           ""))
        a_var            = tk.StringVar(value=self.filtri_avanzati.get("a",            ""))
        icona_var        = tk.StringVar(value=self.filtri_avanzati.get("icona",        "—"))
        partecipanti_var = tk.StringVar(value=self.filtri_avanzati.get("partecipanti", "—"))
        conto_var        = tk.StringVar(value=self.filtri_avanzati.get("conto",        "—"))
        metodo_var       = tk.StringVar(value=self.filtri_avanzati.get("metodo",       "—"))
        hashtag_var      = tk.StringVar(value=self.filtri_avanzati.get("hashtag",      ""))
        def crea_riga(testo, var, values=None):
            f = tk.Frame(filtro_win, bg=self.COLOR_TOPLEVEL)
            f.pack(fill="x", padx=12, pady=5)
            tk.Label(f, text=testo, fg=self.TEXT_COLOR, bg=self.COLOR_TOPLEVEL,
                     width=14, anchor="w").pack(side="left")
            if values:
                ttk.Combobox(f, textvariable=var, values=values,
                             style="Border.TCombobox", state="readonly", width=22).pack(side="left")
            else:
                ttk.Entry(f, textvariable=var, width=24).pack(side="left")
        tutte_cat = sorted(list(self.categorie_tipi.keys()))
        anni = sorted(set(
            str(d.year if isinstance(d, datetime.date)
                else datetime.datetime.strptime(d, "%d-%m-%Y").year)
            for d in self.spese if self.spese
        ), reverse=True)
        mesi_nomi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                     "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
        _profilo_attivo_co2 = getattr(_app, "PROFILO_ATTIVO", "Principale")
        _gestore_nome_cerca = _profilo_attivo_co2 if _profilo_attivo_co2 != "Principale" else os.path.basename(os.getcwd())
        _nomi_esistenti_cerca = [(p.get("nome", "") if isinstance(p, dict) else p) for p in self.nomi_partecipanti] if hasattr(self, "nomi_partecipanti") else []
        lista_partecipanti = ["—"]
        if self._gestore_partecipa() and _gestore_nome_cerca not in _nomi_esistenti_cerca:
            lista_partecipanti.append(f"PER· {_gestore_nome_cerca}")
        lista_partecipanti += [
            f"CTP· {p['nome']}" if p.get("tipo") == "personale" else
            f"CNT· {p['nome']}" if p.get("tipo") == "contenitore" else
            f"PER· {p['nome']}"
            for p in sorted(self.nomi_partecipanti, key=lambda p: p["nome"].lower())
        ] if hasattr(self, "nomi_partecipanti") and self.nomi_partecipanti else []
        try:
            with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
                _conti_filt = ["—"] + [c.get("nome","?") for c in json.load(_pf).get("conti",[])]
        except Exception:
            _conti_filt = ["—"]
        crea_riga("Descrizione:",  descrizione_var)
        crea_riga("Categoria:",    categoria_var,    ["—"] + tutte_cat)
        crea_riga("Tipo voce:",    tipo_var,         ["—", "Entrata", "Uscita"])
        crea_riga("Anno:",         anno_var,         ["—"] + anni)
        crea_riga("Mese:",         mese_var,         ["—"] + mesi_nomi)
        crea_riga("Pagamento:",    icona_var,        ["—"] + METODI_PAGAMENTO_EMOJI)
        crea_riga("Importo da:",   da_var)
        crea_riga("Importo a:",    a_var)
        crea_riga("Partecipanti:", partecipanti_var, lista_partecipanti)
        crea_riga("Conto:",        conto_var,        _conti_filt)
        crea_riga("Metodo Pag.:",  metodo_var,       ["—"] + METODI_PAGAMENTO)
        crea_riga("Hashtag:",      hashtag_var)
        def applica():
            self.filtri_avanzati = {
                "descrizione":  descrizione_var.get(),
                "categoria":    categoria_var.get(),
                "tipo":         tipo_var.get(),
                "anno":         anno_var.get(),
                "mese":         mese_var.get(),
                "da":           da_var.get(),
                "a":            a_var.get(),
                "icona":        icona_var.get(),
                "partecipanti": partecipanti_var.get(),
                "conto":        conto_var.get(),
                "metodo":       metodo_var.get(),
                "hashtag":      hashtag_var.get()
            }
            filtro_win.destroy()
            esegui_ricerca()
        def cancella():
            self.filtri_avanzati = {}
            filtro_win.destroy()
            esegui_ricerca()
        f_btn = tk.Frame(filtro_win, bg=self.COLOR_TOPLEVEL)
        f_btn.pack(pady=10)
        img_applica = self.icone_gui.get("salva")
        btn_applica = ttk.Label(f_btn, compound="left", image=img_applica,
                                text=" Applica" if img_applica else "✓ Applica",
                                background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                                cursor="hand2", padding=(10, 5))
        btn_applica.pack(side="left", padx=10)
        btn_applica.bind("<Button-1>", lambda e: applica())
        img_cancella = self.icone_gui.get("reset")
        btn_cancella = ttk.Label(f_btn, compound="left", image=img_cancella,
                                 text=" Cancella filtri" if img_cancella else "Cancella filtri",
                                 background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                                 cursor="hand2", padding=(10, 5))
        btn_cancella.pack(side="right", padx=10)
        btn_cancella.bind("<Button-1>", lambda e: cancella())
        filtro_win.deiconify()
        filtro_win.grab_set()
    def esporta_risultato():
        dati_tree   = []
        tot_entrate = 0.0
        tot_uscite  = 0.0
        for item in tree.get_children():
            values = tree.item(item, "values")
            if values:
                data, cat, desc, tipo, importo_str = values[0], values[1], values[2], values[3], values[4]
                conto    = values[5] if len(values) > 5 else ""
                ora      = values[6] if len(values) > 6 else ""
                hashtag  = values[7] if len(values) > 7 else ""
                importo_float = converti_importo(importo_str)
                dati_tree.append((data, cat, desc, tipo, importo_float, conto, ora, hashtag))
                if tipo == "Entrata":
                    tot_entrate += importo_float
                elif tipo == "Uscita":
                    tot_uscite += importo_float
        if not dati_tree:
            self.show_custom_warning("Esportazione", "⚠️ Nessun risultato trovato da salvare o stampare.")
            return
        W_DATA, W_CAT, W_DESC, W_TIPO, W_IMP, W_CNT, W_ORA, W_TAG = 10, 18, 24, 8, 13, 12, 6, 16
        header    = (f"{'Data':<{W_DATA}} │ {'Categoria':<{W_CAT}} │ {'Descrizione':<{W_DESC}} │ {'Tipo':<{W_TIPO}} │ "
                     f"{'Importo (€)':>{W_IMP}} │ {'Conto':<{W_CNT}} │ {'Ora':<{W_ORA}} │ {'Hashtag':<{W_TAG}}\n")
        separator = (f"{'─'*W_DATA}─┼─{'─'*W_CAT}─┼─{'─'*W_DESC}─┼─{'─'*W_TIPO}─┼─{'─'*W_IMP}─┼─"
                     f"{'─'*W_CNT}─┼─{'─'*W_ORA}─┼─{'─'*W_TAG}\n")
        testo_filtri_attivi = lbl_risultati.cget("text").split("| Filtri:")[1].strip() if "| Filtri:" in lbl_risultati.cget("text") else "Nessuno"
        netto = tot_entrate - tot_uscite
        contenuto_preview  = f"─── RISULTATI RICERCA ({datetime.date.today():%d/%m/%Y}) ───────────────────────────────────────────────\n"
        contenuto_preview += f" Filtri: {testo_filtri_attivi}\n"
        contenuto_preview += f" Operazioni Trovate: {len(dati_tree)}\n\n"
        contenuto_preview += f"─── RIEPILOGO FINANZIARIO ───────────────────────────────────────────────────────────────────────────\n"
        contenuto_preview += f" • Entrate Totali: {formatta_italiano(tot_entrate)} €\n"
        contenuto_preview += f" • Uscite Totali:  {formatta_italiano(tot_uscite)} €\n"
        contenuto_preview += f" • Saldo Netto:    {formatta_italiano(netto)} €\n\n"
        contenuto_preview += "─── DETTAGLIO OPERAZIONI ────────────────────────────────────────────────────────────────────────────\n"
        contenuto_preview += header + separator
        for data, cat, desc, tipo, importo_float, conto, ora, hashtag in dati_tree:
            desc_troncata = (desc[:W_DESC-3] + '...') if len(desc) > W_DESC else desc
            cat_troncata  = (cat[:W_CAT-3]  + '...') if len(cat)  > W_CAT  else cat
            cnt_troncato  = (conto[:W_CNT-3] + '...') if len(conto) > W_CNT else conto
            tag_troncato  = (hashtag[:W_TAG-3] + '...') if len(hashtag) > W_TAG else hashtag
            contenuto_preview += (f"{data:<{W_DATA}} │ {cat_troncata:<{W_CAT}} │ "
                          f"{desc_troncata:<{W_DESC}} │ {tipo:<{W_TIPO}} │ "
                          f"{formatta_italiano(importo_float):>{W_IMP}} │ {cnt_troncato:<{W_CNT}} │ "
                          f"{ora:<{W_ORA}} │ {tag_troncato:<{W_TAG}}\n")
        contenuto_preview += "\n" + separator
        def _salva_su_file(content_text, preview_popup):
            preview_popup.destroy()
            nome_file = f"Risultati_Ricerca_{datetime.date.today():%d_%m_%Y}.txt"
            file = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("File di testo", "*.txt")],
                initialdir=EXPORT_FILES,
                initialfile=nome_file,
                title="Salva risultati ricerca",
                confirmoverwrite=False,
                parent=finestra
            )
            if file:
                if os.path.exists(file):
                    if not self.show_custom_askyesno("Sovrascrivere file?",
                            f"Il file '{os.path.basename(file)}' esiste già. Vuoi sovrascriverlo?"):
                        return
                try:
                    with open(file, "w", encoding="utf-8") as f:
                        f.write(content_text)
                    self.show_custom_warning("Esportazione completata", f"✓ Risultati salvati:\n{file}")
                except Exception as e:
                    self.show_custom_warning("Errore", f"❌ Salvataggio fallito:\n{e}")
        def _salva_come_pdf(content_text, preview_popup):
            preview_popup.destroy()
            import pymupdf as fitz
            nome_file = f"Risultati_Ricerca_{datetime.date.today():%d_%m_%Y}.pdf"
            file = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("Documento PDF", "*.pdf")],
                initialdir=EXPORT_FILES,
                initialfile=nome_file,
                title="Salva risultati ricerca come PDF",
                confirmoverwrite=False,
                parent=finestra
            )
            if file:
                if os.path.exists(file):
                    if not self.show_custom_askyesno("Sovrascrivere file?",
                            f"Il file '{os.path.basename(file)}' esiste già. Vuoi sovrascriverlo?"):
                        return
                try:
                    doc = fitz.open()
                    lines = content_text.split('\n')
                    page_w, page_h = 842, 595
                    margin = 40
                    font_size = 7
                    line_height = font_size + 2
                    page = doc.new_page(width=page_w, height=page_h)
                    y = margin
                    for line in lines:
                        if y > (page_h - margin):
                            page = doc.new_page(width=page_w, height=page_h)
                            y = margin
                        page.insert_text(
                            (margin, y),
                            line,
                            fontname="cour",
                            fontsize=font_size
                        )
                        y += line_height
                    doc.save(file)
                    doc.close()
                    self.show_custom_warning("Esportazione completata", f"✓ PDF salvato:\n{file}")
                except Exception as e:
                    self.show_custom_warning("Errore", f"❌ Creazione PDF fallita:\n{e}")
        preview_popup = tk.Toplevel(finestra, bg=self.COLOR_TOPLEVEL)
        preview_popup.withdraw()
        preview_popup.title("Anteprima Risultati Ricerca")
        pw, ph = 1300, 630
        px = (preview_popup.winfo_screenwidth()  - pw) // 2
        py = (preview_popup.winfo_screenheight() - ph) // 2
        preview_popup.geometry(f"{pw}x{ph}+{px}+{py}")
        preview_popup.minsize(pw, ph)
        preview_popup.transient(finestra)
        preview_popup.update_idletasks()
        preview_popup.bind('<Escape>', lambda e: preview_popup.destroy())
        text_area = tk.Text(preview_popup, wrap='word', font=('Courier', 10), padx=10, pady=10)
        text_area.insert('1.0', contenuto_preview)
        text_area.config(state='disabled')
        text_area.pack(fill='both', expand=True, padx=10, pady=10)
        frame_btn = tk.Frame(preview_popup, bg=self.COLOR_TOPLEVEL)
        frame_btn.pack(pady=(0, 10))
        img_chiudi_ant = self.icone_gui.get("chiudi")
        btn_chiudi_ant = ttk.Label(frame_btn, compound="left", image=img_chiudi_ant,
                                   text=" Chiudi" if img_chiudi_ant else "Chiudi",
                                   background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                                   cursor="hand2", padding=(10, 5))
        btn_chiudi_ant.pack(side='right', padx=5)
        btn_chiudi_ant.bind("<Button-1>", lambda e: preview_popup.destroy())
        img_esporta = self.icone_gui.get("salva")
        btn_esporta = ttk.Label(frame_btn, compound="left", image=img_esporta,
                                text=" Esporta TXT" if img_esporta else "Esporta TXT",
                                background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                                cursor="hand2", padding=(10, 5))
        btn_esporta.pack(side='left', padx=5)
        btn_esporta.bind("<Button-1>", lambda e: _salva_su_file(contenuto_preview, preview_popup))
        img_esporta_pdf = self.icone_gui.get("salva")
        btn_esporta_pdf = ttk.Label(frame_btn, compound="left", image=img_esporta_pdf,
                                text=" Esporta PDF" if img_esporta_pdf else "Esporta PDF",
                                background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                                cursor="hand2", padding=(10, 5))
        btn_esporta_pdf.pack(side='left', padx=5)
        btn_esporta_pdf.bind("<Button-1>", lambda e: _salva_come_pdf(contenuto_preview, preview_popup))
        if hasattr(self, '_stampa_lista_diretta'):
            img_stampa_ant = self.icone_gui.get("stampa")
            btn_stampa_ant = ttk.Label(frame_btn, compound="left", image=img_stampa_ant,
                                       text=" Stampa" if img_stampa_ant else "Stampa",
                                       background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                                       cursor="hand2", padding=(10, 5))
            btn_stampa_ant.pack(side='left', padx=5)
            btn_stampa_ant.bind("<Button-1>", lambda e: self._stampa_lista_diretta(contenuto_preview, self.show_custom_warning))
        preview_popup.deiconify()
        preview_popup.grab_set()
    frame_bottoni = tk.Frame(finestra, bg=self.COLOR_TOPLEVEL)
    frame_bottoni.pack(pady=(0, 12))
    for testo, ico, cmd in [
        (" Cerca",          "search",  lambda e: esegui_ricerca()),
        (" Esporta",        "stampa",  lambda e: esporta_risultato()),
        (" Filtri avanzati","filtri",  lambda e: apri_filtri_avanzati()),
        (" Reset",          "reset",   lambda e: resetta_campo()),
        (" Chiudi",         "chiudi",  lambda e: finestra.destroy()),
    ]:
        img = self.icone_gui.get(ico)
        btn = ttk.Label(frame_bottoni, compound="left", image=img,
                        text=testo if img else testo.strip(),
                        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                        cursor="hand2", padding=(10, 5))
        btn.pack(side="left", padx=6)
        btn.bind("<Button-1>", cmd)
    self.after(100, esegui_ricerca)
    finestra.deiconify()
def cerca_doppio_click(self, event):
    tree = event.widget
    item_id = tree.focus()
    if not item_id:
        return
    vals = tree.item(item_id, "values")
    if not vals or len(vals) < 1:
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
    if giorno != datetime.date.today():
        self.blink_label_colors(self.stats_label, "purple", "yellow")
    else:
        self.stop_blink_label_colors(self.stats_label, final_color="purple")
    if hasattr(self, '_finestra_cerca') and self._finestra_cerca.winfo_exists():
        self._finestra_cerca.destroy()
        self._finestra_cerca = None

