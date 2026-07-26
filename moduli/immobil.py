#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import uuid
import datetime
from collections import defaultdict
import tkinter as tk
from tkinter import ttk
from tkinter import ttk
from moduli.modello_spesa import (
    SpesaEntry, METODI_PAGAMENTO_EMOJI, SIMBOLI_METODO, metodo_pagamento_pulito,
)

def _immobil_carica(self):
    import __main__ as _app
    IMMOBIL_FILE = _app.IMMOBIL_FILE
    if os.path.exists(IMMOBIL_FILE):
        try:
            with open(IMMOBIL_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"immobili": []}
def _immobil_salva(self, db):
    import __main__ as _app
    IMMOBIL_FILE = _app.IMMOBIL_FILE
    DB_DIR = _app.DB_DIR
    try:
        os.makedirs(DB_DIR, exist_ok=True)
        with open(IMMOBIL_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
    except Exception as e:
        self.show_toast(f"Errore salvataggio ImmoBil: {e}")
def immobil(self):
    if hasattr(self, "_immobil_win") and self._immobil_win and self._immobil_win.winfo_exists():
        self._immobil_win.lift()
        self._immobil_win.focus_force()
        return
    db = self._immobil_carica()
    win = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    win.title("ImmoBil — Gestione Immobili")
    self._immobil_win = win
    win.bind("<Destroy>", lambda e: setattr(self, "_immobil_win", None) if e.widget is win else None)
    win.bind("<Escape>", lambda e: win.destroy())
    win.withdraw()
    win.update_idletasks()
    W, H = 1350, 630
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (W // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (H // 2)
    win.geometry(f"{W}x{H}+{max(0,x)}+{max(0,y)}")
    win.minsize(W, H)
    win.transient(self)
    win.deiconify()
    win.lift()
    win.focus_force()
    toolbar = tk.Frame(win, bg=self.COLOR_WIDGET_BG, pady=4)
    toolbar.pack(fill=tk.X, padx=8, pady=(6, 0))
    def _btn(parent, testo, cmd, icona=None):
        img = self.icone_gui.get(icona) if icona else None
        b = ttk.Label(parent, text=testo, image=img,
              compound="left" if img else None,
              cursor="hand2", font=("Arial", 9, "bold"),
              foreground=self.TEXT_COLOR,
              background=self.COLOR_WIDGET_BG)
        b.pack(side=tk.LEFT, padx=6)
        b.bind("<Button-1>", lambda e: cmd())
        return b
    _btn(toolbar, " Nuovo Immobile",   lambda: self._immobil_nuovo(db, nb, win),  "home")
    _btn(toolbar, " Elimina Immobile", lambda: self._immobil_elimina(db, nb, win),"delete")
    _btn(toolbar, " Grafici",          lambda: self._immobil_grafici(db),          "report")
    def _get_vars():
        try:
            idx = nb.index(nb.select())
            return getattr(self, '_immobil_vars', {}).get(idx, (None, None))
        except Exception:
            return (None, None)
    _btn(toolbar, " Estratto",
         lambda: self._immobil_estratto(db, nb, *_get_vars()),
         "descrizione")
    _btn(toolbar, " Estratto Totale",
         lambda: self._immobil_estratto_totale(db, *_get_vars()),
         "report")
    _btn(toolbar, " Salva",            lambda: (self._immobil_salva(db), self.show_toast("ImmoBil salvato.")), "salva")
    _btn(toolbar, " Chiudi",           lambda: win.destroy(),                      "chiudi")
    nb = ttk.Notebook(win)
    nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
    if not db["immobili"]:
        ph = ttk.Frame(nb)
        nb.add(ph, text="  (nessun immobile)  ")
        tk.Label(
            ph, text="Clicca '🏠 Nuovo Immobile' per iniziare",
            font=("Arial", 12), bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER
        ).pack(expand=True)
    else:
        for imm in db["immobili"]:
            self._immobil_crea_tab(nb, imm, db, win)
def _immobil_crea_tab(self, nb, imm, db, win):
    from __main__ import PORTAFOGLIO_BANCARIO
    tab = ttk.Frame(nb)
    img_tab_immobile = self.icone_gui.get("home")
    if img_tab_immobile:
        nb.add(tab, image=img_tab_immobile, text=f"  {imm.get('nome','Immobile')}  ", compound="left")
    else:
        nb.add(tab, text=f"  🏠 {imm.get('nome','Immobile')}  ")
    ana_lf = ttk.LabelFrame(tab, text="📋 Anagrafica", style="RedBold.TLabelframe")
    ana_lf.pack(fill=tk.X, padx=8, pady=(6, 4))
    campi_r0 = [
        ("Nome",            "nome",               20),
        ("Indirizzo",       "indirizzo",          30),
        ("Inquilino",       "inquilino",          30),
    ]
    campi_r1 = [
        ("Canone €/mese",   "canone",             10),
        ("Scad. contratto", "scadenza_contratto", 12),
        ("Note",            "note",               50),
    ]
    vars_ana = {}
    for col, (etichetta, chiave, w) in enumerate(campi_r0):
        tk.Label(ana_lf, text=etichetta + ":", bg=self.COLOR_WIDGET_BG,
                 fg=self.COLOR_HEADER, font=("Arial", 9, "bold")).grid(
            row=0, column=col*2, sticky="w", padx=(8,2), pady=2)
        v = tk.StringVar(value=str(imm.get(chiave, "")))
        vars_ana[chiave] = v
        ttk.Entry(ana_lf, textvariable=v, width=w, style="TEntry").grid(
            row=0, column=col*2+1, sticky="ew", padx=(0,8), pady=2)
    for col, (etichetta, chiave, w) in enumerate(campi_r1):
        tk.Label(ana_lf, text=etichetta + ":", bg=self.COLOR_WIDGET_BG,
                 fg=self.COLOR_HEADER, font=("Arial", 9, "bold")).grid(
            row=1, column=col*2, sticky="w", padx=(8,2), pady=2)
        v = tk.StringVar(value=str(imm.get(chiave, "")))
        vars_ana[chiave] = v
        ttk.Entry(ana_lf, textvariable=v, width=w, style="TEntry").grid(
            row=1, column=col*2+1, sticky="ew", padx=(0,8), pady=2)
    try:
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf_imm:
            _db_p_imm = json.load(_pf_imm)
        _conti_imm = [c.get("nome", "") for c in _db_p_imm.get("conti", []) if c.get("nome")]
    except Exception:
        _conti_imm = []
    tk.Label(ana_lf, text="Conto:", bg=self.COLOR_WIDGET_BG,
             fg=self.COLOR_HEADER, font=("Arial", 9, "bold")).grid(
        row=2, column=0, sticky="w", padx=(8,2), pady=2)
    v_conto_imm = tk.StringVar(value=imm.get("conto", "(nessuno)"))
    vars_ana["conto"] = v_conto_imm
    cb_conto_imm = ttk.Combobox(ana_lf, textvariable=v_conto_imm,
                                values=["(nessuno)"] + _conti_imm,
                                state="readonly", style="Border.TCombobox", width=20)
    cb_conto_imm.grid(row=2, column=1, sticky="ew", padx=(0,8), pady=2)
    def _salva_ana():
        for chiave, var in vars_ana.items():
            val = var.get().strip()
            if chiave == "canone":
                try:
                    imm[chiave] = float(val.replace(",", "."))
                except ValueError:
                    imm[chiave] = 0.0
            else:
                imm[chiave] = val
        idx = nb.index(nb.select())
        nb.tab(idx, text=f"  {imm.get('nome','Immobile')}  ")
        self._immobil_salva(db)
        self.show_toast("Anagrafica salvata.")
    img_save_ana = self.icone_gui.get("check")
    btn_salva = ttk.Label(
            ana_lf,
            compound="left",
            image=img_save_ana,
            text=" Salva Anagrafica" if img_save_ana else "Salva Anagrafica",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_salva.image = img_save_ana
    btn_salva.grid(row=1, column=len(campi_r1)*2, padx=8, pady=2)
    btn_salva.bind("<Button-1>", lambda e: _salva_ana())
    tot_frame = tk.Frame(tab, bg=self.COLOR_WIDGET_BG)
    tot_frame.pack(fill=tk.X, padx=8, pady=(0, 4))
    def _mk_tot(parent, testo, colore):
        tk.Label(parent, text=testo, bg=self.COLOR_WIDGET_BG,
                 fg=colore, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=4)
        lbl = tk.Label(parent, text="0.00 €", bg=self.COLOR_WIDGET_BG,
                       fg=colore, font=("Arial", 10, "bold"))
        lbl.pack(side=tk.LEFT, padx=(0, 12))
        return lbl
    lbl_ent  = _mk_tot(tot_frame, "Entrate:", self.COLOR_GREEN)
    lbl_usc  = _mk_tot(tot_frame, "Uscite:",  self.COLOR_RED)
    lbl_sald = _mk_tot(tot_frame, "Saldo:",   "dodgerblue")
    _ic_sole = self.icone_gui.get("meteo_sole")
    lbl_sole_imm = tk.Label(tot_frame, image=_ic_sole, bg=self.COLOR_WIDGET_BG)
    lbl_sole_imm.image = _ic_sole
    lbl_sole_imm.pack(side=tk.LEFT, padx=(0, 4))
    main_container = tk.Frame(tab, bg=self.COLOR_WIDGET_BG)
    main_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 6))
    form_lf = ttk.LabelFrame(main_container, text="Registra Movimento", style="RedBold.TLabelframe", width=280)
    form_lf.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
    form_lf.columnconfigure(1, weight=1)
    cat_imm = imm.setdefault("categorie", [
            "Acconto Spese Condominiali",
            "Assicurazione Immobile",
            "Canone Locazione",
            "Cedolare Secca / IRPEF",
            "Conguaglio Spese",
            "Deposito Cauzionale",
            "Elettrodomestici e Arredi",
            "Imposta IMU",
            "Interessi Mutuo Casa",
            "Manutenzione Caldaia/Clima",
            "Provvigioni Agenzia",
            "Quota Registrazione Contratto",
            "Riparazioni Elettriche",
            "Riparazioni Idrauliche",
            "Ristrutturazioni (Detraibili)",
            "Spese Condominiali Inquilino",
            "Spese Condominiali Proprietario",
            "Spese Legali e Contratti",
            "Tassa TARI (Rifiuti)",
            "Utenze (Luce/Gas/Acqua)",
            "Varie"
    ])
    r = 0
    tk.Label(form_lf, text="Data:", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
             font=("Arial", 9, "bold")).grid(row=r, column=0, sticky="w", padx=6, pady=3)
    v_data = tk.StringVar(value=datetime.date.today().strftime("%d-%m-%Y"))
    frm_data_box = tk.Frame(form_lf, bg=self.COLOR_WIDGET_BG)
    frm_data_box.grid(row=r, column=1, sticky="ew", padx=6, pady=3)
    frm_data_box.columnconfigure(0, weight=1)
    ent_data = ttk.Entry(frm_data_box, textvariable=v_data, width=14)
    ent_data.grid(row=0, column=0, sticky="ew")
    btn_cal = ttk.Label(frm_data_box, image=self.icone_gui.get("calendario"),
                        text="", background=self.COLOR_WIDGET_BG, cursor="hand2")
    btn_cal.image = self.icone_gui.get("calendario")
    btn_cal.grid(row=0, column=1, padx=(4, 0))
    btn_cal.bind("<Button-1>", lambda e: self.mostra_calendario_popup_semplice(ent_data, v_data))
    r += 1
    tk.Label(form_lf, text="Categoria:", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
             font=("Arial", 9, "bold")).grid(row=r, column=0, sticky="w", padx=6, pady=3)
    v_cat = tk.StringVar(value=cat_imm[0])
    cb_cat = ttk.Combobox(form_lf, textvariable=v_cat, values=cat_imm,
                          width=25, style="Border.TCombobox")
    cb_cat.grid(row=r, column=1, sticky="ew", padx=6, pady=3)
    r += 1
    tk.Label(form_lf, text="Descrizione:", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
             font=("Arial", 9, "bold")).grid(row=r, column=0, sticky="w", padx=6, pady=3)
    v_desc = tk.StringVar()
    def limita_descrizione(*args):
        if len(v_desc.get()) > 22:
            v_desc.set(v_desc.get()[:22])
    v_desc.trace_add("write", limita_descrizione)
    ent_desc = ttk.Entry(form_lf, textvariable=v_desc, width=22)
    ent_desc.grid(row=r, column=1, sticky="ew", padx=6, pady=3)
    r += 1
    tk.Label(form_lf, text="Importo €:", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
             font=("Arial", 9, "bold")).grid(row=r, column=0, sticky="w", padx=6, pady=3)
    v_imp = tk.StringVar()
    def limita_importo(*args):
        testo_originale = v_imp.get()
        testo_filtrato = "".join(c for c in testo_originale if c.isdigit() or c == ".")
        punti = [i for i, c in enumerate(testo_filtrato) if c == "."]
        if len(punti) > 1:
            idx_valido = punti[0]
            testo_filtrato = "".join(
                c for i, c in enumerate(testo_filtrato) 
                if c.isdigit() or i == idx_valido
            )
        if testo_filtrato and testo_filtrato != ".":
            try:
                valore_float = float(testo_filtrato)
                if valore_float > 99999:
                    testo_filtrato = "99999"
            except ValueError:
                pass
        if testo_originale != testo_filtrato:
            v_imp.set(testo_filtrato)
    v_imp.trace_add("write", limita_importo)
    ent_imp = ttk.Entry(form_lf, textvariable=v_imp, width=12)
    ent_imp.grid(row=r, column=1, sticky="ew", padx=6, pady=3)
    ent_imp.bind("<Return>", lambda e: _aggiungi())
    ent_imp.bind("<KP_Enter>", lambda e: _aggiungi())
    r += 1
    tk.Label(form_lf, text="Tipo:", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
             font=("Arial", 9, "bold")).grid(row=r, column=0, sticky="w", padx=6, pady=3)
    v_tipo = tk.StringVar(value="Uscita")
    ttk.Combobox(form_lf, textvariable=v_tipo, values=["Uscita", "Entrata"],
                 width=10, state="readonly", style="Border.TCombobox").grid(
        row=r, column=1, sticky="ew", padx=6, pady=3)
    r += 1
    tk.Label(form_lf, text="Categorie:", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
             font=("Arial", 9, "bold")).grid(row=r, column=0, sticky="w", padx=6, pady=(8,2))
    r += 1
    cat_frame = tk.Frame(form_lf, bg=self.COLOR_WIDGET_BG)
    cat_frame.grid(row=r, column=0, columnspan=2, sticky="ew", padx=6, pady=2)
    r += 1
    v_nuova_cat = tk.StringVar()
    def _limita_cat(*a):
        if len(v_nuova_cat.get()) > 22: v_nuova_cat.set(v_nuova_cat.get()[:22])
    v_nuova_cat.trace_add("write", _limita_cat)
    ttk.Entry(cat_frame, textvariable=v_nuova_cat, width=25).pack(side=tk.LEFT, padx=(0,4))
    def _aggiungi_cat():
        nc = v_nuova_cat.get().strip()
        if nc and nc not in cat_imm:
            cat_imm.append(nc)
            cat_imm.sort(key=str.lower)
            cb_cat["values"] = cat_imm
            v_cat.set(nc)
            self._immobil_salva(db)
            v_nuova_cat.set("")
            self.show_toast(f"Categoria '{nc}' aggiunta.")
    def _rimuovi_cat():
        sel = v_cat.get()
        if sel in cat_imm and sel != "Generale":
            cat_imm.remove(sel)
            cb_cat["values"] = cat_imm
            if cat_imm:
                v_cat.set(cat_imm[0])
            else:
                cat_imm.append("Generale")
                cb_cat["values"] = cat_imm
                v_cat.set("Generale")
            self._immobil_salva(db)
    img_add_cat = self.icone_gui.get("aggiungi")
    btn_add_cat = ttk.Label(
            cat_frame,
            compound="left",
            image=img_add_cat,
            text="" if img_add_cat else "➕",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_add_cat.image = img_add_cat
    btn_add_cat.pack(side=tk.LEFT, padx=2)
    btn_add_cat.bind("<Button-1>", lambda e: _aggiungi_cat())
    img_remove_cat = self.icone_gui.get("delete")
    btn_remove_cat = ttk.Label(
            cat_frame,
            compound="left",
            image=img_remove_cat,
            text="" if img_remove_cat else "➖",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_remove_cat.image = img_remove_cat
    btn_remove_cat.pack(side=tk.LEFT, padx=2)
    btn_remove_cat.bind("<Button-1>", lambda e: _rimuovi_cat())
    btn_frame = tk.Frame(form_lf, bg=self.COLOR_WIDGET_BG)
    btn_frame.grid(row=r, column=0, columnspan=2, pady=8)
    tree_lf = ttk.LabelFrame(main_container, text="Movimenti", style="RedBold.TLabelframe")
    tree_lf.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 0), pady=3)
    filtri_tree_f = tk.Frame(tree_lf, bg=self.COLOR_WIDGET_BG)
    filtri_tree_f.pack(fill=tk.X, padx=4, pady=(4, 0))
    tk.Label(filtri_tree_f, text="Categoria:", bg=self.COLOR_WIDGET_BG,
             fg=self.COLOR_HEADER, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
    v_fcat = tk.StringVar(value="Tutte")
    cat_vals = ["Tutte"] + sorted(cat_imm)
    cb_fcat = ttk.Combobox(filtri_tree_f, textvariable=v_fcat, values=cat_vals,
                           state="readonly", style="Border.TCombobox", width=25)
    cb_fcat.pack(side=tk.LEFT, padx=(0, 8))
    cb_fcat.bind("<<ComboboxSelected>>", lambda e: _popola_tree())
    tk.Label(filtri_tree_f, text="Mese:", bg=self.COLOR_WIDGET_BG,
             fg=self.COLOR_HEADER, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
    v_fmese = tk.StringVar(value=datetime.date.today().strftime("%m"))
    mesi_f = ["Tutti","01","02","03","04","05","06","07","08","09","10","11","12"]
    cb_fmese = ttk.Combobox(filtri_tree_f, textvariable=v_fmese, values=mesi_f,
                            state="readonly", style="Border.TCombobox", width=5)
    cb_fmese.pack(side=tk.LEFT, padx=(0, 8))
    tk.Label(filtri_tree_f, text="Anno:", bg=self.COLOR_WIDGET_BG,
             fg=self.COLOR_HEADER, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
    anni_f = sorted({
        m.get("data", "")[-4:]
        for m in imm.get("spese", [])
        if len(m.get("data", "")) == 10
    }, reverse=True)
    v_fanno = tk.StringVar(value=str(datetime.date.today().year))
    cb_fanno = ttk.Combobox(filtri_tree_f, textvariable=v_fanno,
                            values=["Tutti"] + anni_f,
                            state="readonly", style="Border.TCombobox", width=7)
    cb_fanno.pack(side=tk.LEFT, padx=(0, 8))
    cb_fmese.bind("<<ComboboxSelected>>", lambda e: _popola_tree())
    cb_fanno.bind("<<ComboboxSelected>>", lambda e: _popola_tree())
    def _reset_filtri():
        v_fmese.set(datetime.date.today().strftime("%m"))
        v_fanno.set(str(datetime.date.today().year))
        v_fcat.set("Tutte")
        _popola_tree()
    btn_reset = tk.Label(filtri_tree_f, text="↺ Reset", bg=self.COLOR_WIDGET_BG,
                         fg=self.COLOR_HIGHLIGHT, font=("Arial", 8, "bold"),
                         cursor="hand2")
    btn_reset.pack(side=tk.LEFT, padx=(4, 0))
    btn_reset.bind("<Button-1>", lambda e: _reset_filtri())
    if not hasattr(self, '_immobil_vars'):
        self._immobil_vars = {}
    tab_idx = nb.index("end") - 1 if nb.index("end") > 0 else 0
    self._immobil_vars[tab_idx] = (v_fmese, v_fanno)
    cols = ("Data", "Categoria", "Descrizione", "Tipo", "Importo")
    tree_frame_inner = ttk.Frame(tree_lf)
    tree_frame_inner.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
    tree = ttk.Treeview(tree_frame_inner, columns=cols, show="headings", selectmode="browse")
    vsb  = ttk.Scrollbar(tree_frame_inner, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(fill=tk.BOTH, expand=True)
    wcfg = {"Data": (90,"w"), "Categoria": (110,"w"),
            "Descrizione": (220,"w"), "Tipo": (70,"center"), "Importo": (90,"e")}
    for c in cols:
        w, anc = wcfg[c]
        tree.heading(c, text=c, command=lambda _c=c: self.treeview_sort_column(tree, _c, False))
        tree.column(c, width=w, anchor=anc)
    tree.tag_configure("entrata", foreground=self.COLOR_GREEN)
    tree.tag_configure("uscita",  foreground=self.COLOR_RED)
    def _match_f(data_str):
        if len(data_str) != 10:
            return True
        ms = v_fmese.get()
        an = v_fanno.get()
        if an != "Tutti" and data_str[-4:] != an:
            return False
        if ms != "Tutti" and data_str[3:5] != ms:
            return False
        return True
    def _aggiorna_totali():
        fc = v_fcat.get()
        spese_vis = [
            m for m in imm.get("spese", [])
            if _match_f(m.get("data", ""))
            and (fc == "Tutte" or m.get("categoria", "") == fc)
        ]
        ent = sum(float(m["importo"]) for m in spese_vis if m.get("tipo","").lower()=="entrata")
        usc = sum(float(m["importo"]) for m in spese_vis if m.get("tipo","").lower()=="uscita")
        sal = ent - usc
        self._anima_label_valore(lbl_ent,  ent)
        self._anima_label_valore(lbl_usc,  usc)
        self._anima_label_valore(lbl_sald, sal)
        lbl_sald.config(foreground=self.COLOR_GREEN if sal >= 0 else self.COLOR_RED)
        self.avvia_animazione_meteo(lbl_sole_imm, "sole" if sal >= 0 else "temporale")
    def _popola_tree():
        anni_aggiornati = sorted({
            m.get("data", "")[-4:]
            for m in imm.get("spese", [])
            if len(m.get("data", "")) == 10
        }, reverse=True)
        cb_fanno["values"] = ["Tutti"] + anni_aggiornati
        cb_fcat["values"] = ["Tutte"] + sorted(cat_imm)
        migrato = False
        for m in imm.get("spese", []):
            if not m.get("id"):
                m["id"] = str(uuid.uuid4())
                migrato = True
        if migrato:
            self._immobil_salva(db)
        tree.delete(*tree.get_children())
        for m in sorted(imm.get("spese", []), key=lambda x: x.get("data","")):
            if not _match_f(m.get("data", "")):
                continue
            fc = v_fcat.get()
            if fc != "Tutte" and m.get("categoria", "") != fc:
                continue
            tag = "entrata" if m.get("tipo","").lower()=="entrata" else "uscita"
            try:
                val_float = float(m.get('importo', 0))
            except ValueError:
                val_float = 0.0
            tree.insert("", "end", iid=m["id"], tags=(tag,), values=(
                m.get("data",""),
                m.get("categoria",""),
                m.get("descrizione",""),
                m.get("tipo",""),
                f"{val_float:.2f} €"
            ))
        _aggiorna_totali()
        
    riga_in_modifica = None

    def _carica_in_form():
        nonlocal riga_in_modifica
        sel = tree.selection()
        if not sel:
            self.show_toast("Seleziona un movimento da modificare.")
            return
        item_id = sel[0]
        movimento = next((m for m in imm.get("spese", []) if m.get("id") == item_id), None)
        if not movimento:
            self.show_toast("Movimento non trovato.")
            return
        riga_in_modifica = movimento
        v_data.set(movimento.get("data", ""))
        v_cat.set(movimento.get("categoria", ""))
        v_desc.set(movimento.get("descrizione", ""))
        v_tipo.set(movimento.get("tipo", "Uscita"))
        try:
            val_float = float(movimento.get("importo", 0))
            v_imp.set(f"{val_float:.2f}")
        except ValueError:
            v_imp.set(str(movimento.get("importo", "")))
        btn_add.config(text=" Conferma" if img_add else "✓ Salva Modifica")
    def _aggiungi():
        nonlocal riga_in_modifica
        data  = v_data.get().strip()
        cat   = v_cat.get().strip()
        desc  = v_desc.get().strip()
        tipo  = v_tipo.get()
        testo_importo = v_imp.get().strip()
        if testo_importo.count(".") > 1:
            parti = testo_importo.split(".")
            testo_importo = "".join(parti[:-1]) + "." + parti[-1]
        try:
            imp = float(testo_importo)
        except ValueError:
            self.show_toast("Importo non valido.")
            return
        try:
            datetime.datetime.strptime(data, "%d-%m-%Y")
        except ValueError:
            self.show_toast("Data non valida (gg-mm-aaaa).")
            return
        if riga_in_modifica is not None:
            riga_in_modifica["data"] = data
            riga_in_modifica["categoria"] = cat
            riga_in_modifica["descrizione"] = desc
            riga_in_modifica["importo"] = imp
            riga_in_modifica["tipo"] = tipo
            riga_in_modifica = None
            btn_add.config(text=" Aggiungi" if img_add else "➕ Aggiungi")
            self.show_toast("Movimento modificato.")
        else:
            imm.setdefault("spese", []).append({
                "id": str(uuid.uuid4()),
                "data": data, "categoria": cat,
                "descrizione": desc, "importo": imp, "tipo": tipo
            })
            self.show_toast("Movimento aggiunto.")
        self._immobil_salva(db)
        v_desc.set("")
        v_imp.set("")
        v_desc.set("")
        v_imp.set("")
        _popola_tree()
    def _elimina_mov():
        sel = tree.selection()
        if not sel:
            return
        item_id = sel[0]
        da_rimuovere = next((m for m in imm.get("spese", []) if m.get("id") == item_id), None)
        if da_rimuovere:
            imm.get("spese", []).remove(da_rimuovere)
            self._immobil_salva(db)
            _popola_tree()
    def _esporta_in_spesedb():
        fc = v_fcat.get()
        spese_filtrate = [
            m for m in imm.get("spese", [])
            if _match_f(m.get("data", ""))
            and (fc == "Tutte" or m.get("categoria", "") == fc)
        ]
        ent = sum(float(m["importo"]) for m in spese_filtrate if m.get("tipo","").lower()=="entrata")
        usc = sum(float(m["importo"]) for m in spese_filtrate if m.get("tipo","").lower()=="uscita")
        saldo = ent - usc
        if saldo == 0:
            self.show_toast("Saldo zero, nessun movimento esportato.")
            return
        nome = imm.get("nome", "Immobile")
        tipo_mov = "Entrata" if saldo >= 0 else "Uscita"
        imp_mov  = abs(saldo)
        oggi = datetime.date.today()
        if oggi not in self.spese:
            self.spese[oggi] = []
        cat_export = "ImmoBil"
        if cat_export not in self.categorie:
            self.categorie.append(cat_export)
            self.aggiorna_combobox_categorie()
        nome_conto = vars_ana["conto"].get().strip() if "conto" in vars_ana else imm.get("conto", "")
        self.spese[oggi].append(SpesaEntry.nuova(
            cat_export, f"ImmoBil: {nome}", imp_mov, tipo_mov,
            conto=(nome_conto if nome_conto and nome_conto != "(nessuno)" else ""),
            hashtag=["#immobili"]
        ))
        self.save_db()
        self.refresh_gui()
        self.show_toast(f"Saldo {nome} ({tipo_mov} {imp_mov:.2f}€) esportato in SpesaDB.")
    img_add = self.icone_gui.get("aggiungi")
    btn_add = ttk.Label(
            btn_frame,
            compound="left",
            image=img_add,
            text=" Aggiungi" if img_add else "➕ Aggiungi",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_add.image = img_add
    btn_add.pack(side=tk.LEFT, padx=4)
    btn_add.bind("<Button-1>", lambda e: _aggiungi())
    img_edit = self.icone_gui.get("modifica") or self.icone_gui.get("edit")
    btn_edit = ttk.Label(
            btn_frame,
            compound="left",
            image=img_edit,
            text=" Modifica" if img_edit else "📝 Modifica",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_edit.image = img_edit
    btn_edit.pack(side=tk.LEFT, padx=4)
    btn_edit.bind("<Button-1>", lambda e: _carica_in_form())
    img_delete = self.icone_gui.get("delete")
    btn_delete = ttk.Label(
            btn_frame,
            compound="left",
            image=img_delete,
            text=" Elimina" if img_delete else "🗑 Elimina",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_delete.image = img_delete
    btn_delete.pack(side=tk.LEFT, padx=4)
    btn_delete.bind("<Button-1>", lambda e: _elimina_mov())
    btn_frame2 = tk.Frame(form_lf, bg=self.COLOR_WIDGET_BG)
    btn_frame2.grid(row=r+1, column=0, columnspan=2, pady=(0, 8))
    img_export = self.icone_gui.get("archivia")
    btn_export = ttk.Label(
            btn_frame2,
            compound="left",
            image=img_export,
            text=" → SpesaDB" if img_export else "📤 → SpesaDB",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_export.image = img_export
    btn_export.pack(side=tk.LEFT, padx=4)
    btn_export.bind("<Button-1>", lambda e: _esporta_in_spesedb())
    tk.Label(btn_frame2, text="(esporta saldo periodo visualizzato)",
             bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
             font=("Arial", 8, "italic")).pack(side=tk.LEFT, padx=(4, 0))
    _popola_tree()
def _immobil_nuovo(self, db, nb, win):
    popup = tk.Toplevel(win, bg=self.COLOR_TOPLEVEL)
    popup.title("Nuovo Immobile")
    popup.transient(win)
    popup.resizable(False, False)
    popup.withdraw()
    win.update_idletasks()
    w, h = 380, 150
    x = win.winfo_rootx() + (win.winfo_width()  // 2) - (w // 2)
    y = win.winfo_rooty() + (win.winfo_height() // 2) - (h // 2)
    popup.geometry(f"{w}x{h}+{max(0,x)}+{max(0,y)}")
    popup.deiconify()
    popup.lift()
    popup.focus_force()
    popup.bind("<Escape>", lambda e: popup.destroy())
    tk.Label(popup, text="Nome immobile:", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 12, "bold")).pack(pady=(20,4))
    v = tk.StringVar()
    def limita_caratteri(*args):
        if len(v.get()) > 22:
            v.set(v.get()[:22])
    v.trace_add("write", limita_caratteri)
    e = ttk.Entry(popup, textvariable=v, width=21)
    e.pack(pady=4)
    e.focus_set()
    def _ok(event=None):
        nome = v.get().strip()
        if not nome:
            self.show_toast("Inserisci un nome.")
            return
        LIMITE_MAX_TAB = 7
        if len(db.get("immobili", [])) >= LIMITE_MAX_TAB:
            self.show_toast(f"Limite raggiunto! Massimo {LIMITE_MAX_TAB} immobili consentiti.")
            popup.destroy()
            return
        for i in range(nb.index("end")):
            if "(nessun immobile)" in nb.tab(i, "text"):
                nb.forget(i)
                break
        nuovo = {
            "id": str(uuid.uuid4()),
            "nome": nome,
            "indirizzo": "",
            "inquilino": "",
            "canone": 0.0,
            "scadenza_contratto": "",
            "note": "",
            "categorie": 
            ["Acconto Spese Condominiali",
            "Assicurazione Immobile",
            "Canone Locazione",
            "Cedolare Secca / IRPEF",
            "Conguaglio Spese",
            "Deposito Cauzionale",
            "Elettrodomestici e Arredi",
            "Imposta IMU",
            "Interessi Mutuo Casa",
            "Manutenzione Caldaia/Clima",
            "Provvigioni Agenzia",
            "Quota Registrazione Contratto",
            "Riparazioni Elettriche",
            "Riparazioni Idrauliche",
            "Ristrutturazioni (Detraibili)",
            "Spese Condominiali Inquilino",
            "Spese Condominiali Proprietario",
            "Spese Legali e Contratti",
            "Tassa TARI (Rifiuti)",
            "Utenze (Luce/Gas/Acqua)",
            "Varie"],
            "spese": []
        }
        db["immobili"].append(nuovo)
        self._immobil_salva(db)
        self._immobil_crea_tab(nb, nuovo, db, win)
        nb.select(nb.index("end") - 1)
        popup.destroy()
    popup.bind("<Return>", _ok)
    btn_box = tk.Frame(popup, bg=self.COLOR_WIDGET_BG)
    btn_box.pack(fill=tk.X, pady=12, padx=15)
    center_f = tk.Frame(btn_box, bg=self.COLOR_WIDGET_BG)
    center_f.pack(anchor=tk.CENTER)
    lbl_crea = ttk.Label(center_f, image=self.icone_gui.get("check"),
                         text="Crea", compound=tk.LEFT, cursor="hand2",
                         background=self.COLOR_TOPLEVEL, foreground=self.TEXT_COLOR,
                         font=("Arial", 10, "bold"))
    lbl_crea.image = self.icone_gui.get("check")
    lbl_crea.pack(side=tk.LEFT, padx=15)
    lbl_crea.bind("<Button-1>", lambda e: _ok())
    lbl_chiudi = ttk.Label(center_f, image=self.icone_gui.get("chiudi"),
                           text="Chiudi", compound=tk.LEFT, cursor="hand2",
                           background=self.COLOR_TOPLEVEL, foreground=self.TEXT_COLOR,
                           font=("Arial", 10, "bold"))
    lbl_chiudi.image = self.icone_gui.get("chiudi")
    lbl_chiudi.pack(side=tk.LEFT, padx=15)
    lbl_chiudi.bind("<Button-1>", lambda e: popup.destroy())
def _immobil_elimina(self, db, nb, win):
    idx = nb.index(nb.select())
    if idx < 0 or idx >= len(db["immobili"]):
        self.show_toast("Nessun immobile selezionato.")
        return
    imm = db["immobili"][idx]
    risposta = self.show_custom_askyesno(
        "Elimina Immobile",
        f"Eliminare '{imm.get('nome','')}' e tutti i suoi movimenti?"
    )
    if not risposta:
        return
    db["immobili"].pop(idx)
    self._immobil_salva(db)
    nb.forget(idx)
    if not db["immobili"]:
        ph = ttk.Frame(nb)
        nb.add(ph, text="  (nessun immobile)  ")
        tk.Label(
            ph, text="Clicca '🏠 Nuovo Immobile' per iniziare",
            font=("Arial", 12), bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER
        ).pack(expand=True)
    self.show_toast(f"Immobile eliminato.")

def _immobil_grafici(self, db):
    if not db["immobili"]:
        self.show_toast("Nessun immobile presente.")
        return
    if hasattr(self, '_immobil_grafici_win') and self._immobil_grafici_win and self._immobil_grafici_win.winfo_exists():
        self._immobil_grafici_win.lift()
        self._immobil_grafici_win.focus_force()
        return
    popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    self._immobil_grafici_win = popup
    popup.title("ImmoBil — Grafici")
    popup.transient(self)
    popup.bind("<Escape>", lambda e: popup.destroy())
    popup.withdraw()
    W, H = 1300, 630
    x = self.winfo_rootx() + (self.winfo_width()  // 2) - (W // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (H // 2)
    popup.geometry(f"{W}x{H}+{max(0,x)}+{max(0,y)}")
    popup.minsize(W, H)
    popup.deiconify()
    popup.lift()
    popup.focus_force()
    nomi_case = [imm.get("nome", "?") for imm in db["immobili"]]
    tutte_categorie = sorted({
        m.get("categoria", "Altro")
        for imm in db["immobili"]
        for m in imm.get("spese", [])
    })
    anni_disponibili = sorted({
        m.get("data", "")[-4:]
        for imm in db["immobili"]
        for m in imm.get("spese", [])
        if len(m.get("data", "")) == 10
    }, reverse=True)
    filtri_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL, pady=6)
    filtri_f.pack(fill=tk.X, padx=14, pady=(8, 0))
    tk.Label(filtri_f, text="Immobile:", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
    v_casa = tk.StringVar(value="Tutte")
    cb_casa = ttk.Combobox(filtri_f, textvariable=v_casa,
                           values=["Tutte"] + nomi_case,
                           state="readonly", style="Border.TCombobox", width=24)
    cb_casa.pack(side=tk.LEFT, padx=(0, 10))
    tk.Label(filtri_f, text="Categoria:", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
    v_cat = tk.StringVar(value="Tutte")
    cb_cat = ttk.Combobox(filtri_f, textvariable=v_cat,
                          values=["Tutte"] + tutte_categorie,
                          state="readonly", style="Border.TCombobox", width=24)
    cb_cat.pack(side=tk.LEFT, padx=(0, 10))
    tk.Label(filtri_f, text="Tipo:", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))
    v_tipo = tk.StringVar(value="uscita")
    ttk.Radiobutton(filtri_f, text="Uscite", variable=v_tipo, value="uscita",
                    style="Custom.TRadiobutton",
                    command=lambda: _disegna()).pack(side=tk.LEFT, padx=4)
    ttk.Radiobutton(filtri_f, text="Entrate", variable=v_tipo, value="entrata",
                    style="Custom.TRadiobutton",
                    command=lambda: _disegna()).pack(side=tk.LEFT, padx=4)
    _oggi = datetime.date.today()
    _mese_corrente = f"{_oggi.month:02d}"
    _anno_corrente = str(_oggi.year)

    v_anno = tk.StringVar(value=_anno_corrente)
    cb_anno = ttk.Combobox(filtri_f, textvariable=v_anno,
                           values=["Tutti"] + anni_disponibili,
                           state="readonly", style="Border.TCombobox", width=7)
    cb_anno.pack(side=tk.RIGHT, padx=(0, 6))
    tk.Label(filtri_f, text="Anno:", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 9, "bold")).pack(side=tk.RIGHT, padx=(0, 4))
    v_mese = tk.StringVar(value=_mese_corrente)
    mesi = ["Tutti","01","02","03","04","05","06","07","08","09","10","11","12"]
    cb_mese = ttk.Combobox(filtri_f, textvariable=v_mese, values=mesi,
                           state="readonly", style="Border.TCombobox", width=5)
    cb_mese.pack(side=tk.RIGHT, padx=(0, 6))
    tk.Label(filtri_f, text="Mese:", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 9, "bold")).pack(side=tk.RIGHT, padx=(4, 4))
    def _reset_oggi():
        v_mese.set(f"{datetime.date.today().month:02d}")
        v_anno.set(str(datetime.date.today().year))
        _disegna()
    tk.Label(filtri_f, text="↺ Reset", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HIGHLIGHT, font=("Arial", 8, "bold"),cursor="hand2").pack(side=tk.RIGHT, padx=(0, 8))
    filtri_f.winfo_children()[-1].bind("<Button-1>", lambda e: _reset_oggi())
    cb_casa.bind("<<ComboboxSelected>>",  lambda e: _disegna())
    cb_cat.bind("<<ComboboxSelected>>",   lambda e: _disegna())
    cb_mese.bind("<<ComboboxSelected>>",  lambda e: _disegna())
    cb_anno.bind("<<ComboboxSelected>>",  lambda e: _disegna())
    canvas = tk.Canvas(popup, bg=self.COLOR_WIDGET_BG, highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True, padx=12, pady=(8, 4))
    footer_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL, pady=5)
    footer_f.pack(fill=tk.X, padx=14, pady=(0, 4))
    lbl_ent = tk.Label(footer_f, text="Entrate: —",
                       bg=self.COLOR_TOPLEVEL, fg="#98C379",
                       font=("Arial", 9, "bold"))
    lbl_ent.pack(side=tk.LEFT, padx=(0, 24))
    lbl_usc = tk.Label(footer_f, text="Uscite: —",
                       bg=self.COLOR_TOPLEVEL, fg=self.COLOR_RED,
                       font=("Arial", 9, "bold"))
    lbl_usc.pack(side=tk.LEFT, padx=(0, 24))
    lbl_saldo = tk.Label(footer_f, text="Saldo: —",
                         bg=self.COLOR_TOPLEVEL, fg=self.COLOR_HEADER,
                         font=("Arial", 9, "bold"))
    lbl_saldo.pack(side=tk.LEFT)
    btn_chiudi_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    btn_chiudi_f.pack(pady=(0, 8))
    img_chiudi = self.icone_gui.get("chiudi")
    btn_chiudi = tk.Label(btn_chiudi_f, image=img_chiudi, text=" Chiudi", compound="left",
                          bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                          font=("Arial", 10, "bold"), padx=20, pady=5, cursor="hand2")
    btn_chiudi.pack()
    btn_chiudi.bind("<Button-1>", lambda e: popup.destroy())
    popup.img_chiudi = img_chiudi
    def _disegna(event=None):
        canvas.delete("all")
        cw = canvas.winfo_width()  or W - 24
        ch = canvas.winfo_height() or H - 160
        if cw < 10 or ch < 10:
            return
        casa_sel = v_casa.get()
        cat_sel  = v_cat.get()
        tipo_sel = v_tipo.get()
        mese_sel = v_mese.get()
        anno_sel = v_anno.get()
        if casa_sel == "Tutte":
            case_attive = db["immobili"]
        else:
            case_attive = [imm for imm in db["immobili"]
                           if imm.get("nome") == casa_sel]
        def _match_periodo(data_str):
            if len(data_str) != 10:
                return True
            if anno_sel != "Tutti" and data_str[-4:] != anno_sel:
                return False
            if mese_sel != "Tutti" and data_str[3:5] != mese_sel:
                return False
            return True
        tot_ent = sum(
            float(m.get("importo", 0))
            for imm in case_attive
            for m in imm.get("spese", [])
            if m.get("tipo", "").lower() == "entrata"
            and _match_periodo(m.get("data", ""))
        )
        tot_usc = sum(
            float(m.get("importo", 0))
            for imm in case_attive
            for m in imm.get("spese", [])
            if m.get("tipo", "").lower() == "uscita"
            and _match_periodo(m.get("data", ""))
        )
        saldo = tot_ent - tot_usc
        lbl_ent.config(text=f"Totale Entrate: € {tot_ent:,.2f}")
        lbl_usc.config(text=f"Totale Uscite: € {tot_usc:,.2f}")
        lbl_saldo.config(
            text=f"Saldo: € {saldo:,.2f}",
            fg="#98C379" if saldo >= 0 else self.COLOR_RED
        )
        cat_totali = defaultdict(float)
        for imm in case_attive:
            for m in imm.get("spese", []):
                if m.get("tipo", "").lower() != tipo_sel:
                    continue
                if not _match_periodo(m.get("data", "")):
                    continue
                cat = m.get("categoria", "Altro")
                if cat_sel != "Tutte" and cat != cat_sel:
                    continue
                cat_totali[cat] += float(m.get("importo", 0))
        bars_data = sorted(cat_totali.items(), key=lambda x: x[1], reverse=True)
        if not bars_data:
            canvas.create_text(cw // 2, ch // 2,
                               text="Nessun dato per i filtri selezionati",
                               fill=self.TEXT_COLOR, font=("Arial", 11))
            return
        tipo_lbl = "Uscite" if tipo_sel == "uscita" else "Entrate"
        casa_lbl = casa_sel if casa_sel != "Tutte" else "Tutte le Case"
        cat_lbl  = f"  —  {cat_sel}" if cat_sel != "Tutte" else ""
        per_lbl  = ""
        if mese_sel != "Tutti" or anno_sel != "Tutti":
            per_lbl = f"  —  {mese_sel if mese_sel != 'Tutti' else ''}" \
                      f"{'/' if mese_sel != 'Tutti' and anno_sel != 'Tutti' else ''}" \
                      f"{anno_sel if anno_sel != 'Tutti' else ''}"
        titolo = f"{tipo_lbl} per Categoria  |  {casa_lbl}{cat_lbl}{per_lbl}"
        palette  = ["#61AFEF","#98C379","#E06C75","#E5C07B","#C678DD","#56B6C2","#D19A66"]
        col_mono = self.COLOR_RED if tipo_sel == "uscita" else "#98C379"
        mx       = max(v for _, v in bars_data) or 1
        margin_t = 34
        margin_b = 18
        margin_l = 170
        margin_r = 110
        n        = len(bars_data)
        plot_h   = ch - margin_t - margin_b
        plot_w   = cw - margin_l - margin_r
        bar_step = plot_h / n
        bar_h    = max(6, int(bar_step * 0.60))
        canvas.create_text(cw // 2, margin_t // 2, text=titolo,
                           fill=self.COLOR_HEADER, font=("Arial", 10, "bold"))
        canvas.create_line(margin_l, margin_t, margin_l, margin_t + plot_h,
                           fill=self.TEXT_COLOR, width=1)
        for i in range(1, 5):
            x_g = margin_l + int(plot_w * i / 4)
            v_g = mx * i / 4
            canvas.create_line(x_g, margin_t, x_g, margin_t + plot_h,
                               fill=self.COLOR_HEADER, dash=(2, 4))
            canvas.create_text(x_g, margin_t + plot_h + 4,
                               text=f"{v_g:,.0f}", anchor="n",
                               fill=self.TEXT_COLOR, font=("Arial", 7))
        for i, (etichetta, valore) in enumerate(bars_data):
            cy  = margin_t + i * bar_step + bar_step / 2
            y0  = int(cy - bar_h / 2)
            y1  = int(cy + bar_h / 2)
            x0  = margin_l
            x1  = margin_l + max(2, int(plot_w * valore / mx))
            col = palette[i % len(palette)] if cat_sel == "Tutte" else col_mono
            canvas.create_rectangle(x0, y0, x1, y1, fill=col, outline="")
            lbl = etichetta if len(etichetta) <= 25 else etichetta[:24] + "…"
            canvas.create_text(margin_l - 6, int(cy), text=lbl,
                               anchor="e", fill=self.TEXT_COLOR, font=("Arial", 8))
            canvas.create_text(x1 + 5, int(cy),
                               text=f"€ {valore:,.2f}", anchor="w",
                               fill=self.TEXT_COLOR, font=("Arial", 8, "bold"))
    canvas.bind("<Configure>", _disegna)
    popup.after(100, _disegna)

def _immobil_estratto(self, db, nb, v_fmese=None, v_fanno=None):
    idx = nb.index(nb.select())
    if idx < 0 or idx >= len(db["immobili"]):
        self.show_toast("Nessun immobile selezionato.")
        return
    imm   = db["immobili"][idx]
    nome  = imm.get("nome", "Immobile")
    mese_sel = v_fmese.get() if v_fmese else "Tutti"
    anno_sel = v_fanno.get() if v_fanno else "Tutti"

    def _match(data_str):
        if len(data_str) != 10:
            return True
        if anno_sel != "Tutti" and data_str[-4:] != anno_sel:
            return False
        if mese_sel != "Tutti" and data_str[3:5] != mese_sel:
            return False
        return True

    spese = sorted(
        [m for m in imm.get("spese", []) if _match(m.get("data", ""))],
        key=lambda x: x.get("data", "")
    )
    periodo_str = ""
    if mese_sel != "Tutti" or anno_sel != "Tutti":
        periodo_str = f"  Periodo: {mese_sel if mese_sel != 'Tutti' else '--'}/{anno_sel if anno_sel != 'Tutti' else '----'}"

    LARGHEZZA_DOC = 85
    linea_doppia  = "═" * LARGHEZZA_DOC
    linea_singola = "─" * LARGHEZZA_DOC
    lines = [
        linea_doppia,
        f"Gestione Immobili".center(LARGHEZZA_DOC),
        f"Estratto Conto: {nome.upper()}".center(LARGHEZZA_DOC),
    ]
    if periodo_str:
        lines.append(periodo_str.center(LARGHEZZA_DOC))
    lines += [
        linea_doppia,
        "",
        f"  Informazione Immobile",
        f"  ─────────────────────",
        f"  Indirizzo : {imm.get('indirizzo', '─'):<26} Inquilino : {imm.get('inquilino', '─'):<26}",
        f"  Canone    : € {imm.get('canone', 0):.2f}/mese{'' :<13} Scadenza  : {imm.get('scadenza_contratto', '─'):<26}",
        f"  Note      : {imm.get('note', '-'):<66}",
        "",
        linea_doppia,
        f"  {'DATA':<12} {'CATEGORIA':<22} {'TIPO':<10} {'IMPORTO':>12}   {'DESCRIZIONE'}",
        linea_singola,
    ]
    tot_ent = 0.0
    tot_usc = 0.0
    for m in spese:
        tipo = m.get("tipo", "")
        try:
            imp = float(m.get("importo", 0))
        except ValueError:
            imp = 0.0
        if tipo.lower() == "entrata":
            tot_ent += imp
            segno = "+"
        else:
            tot_usc += imp
            segno = "-"
        str_importo = f"{segno}{imp:.2f}"
        cat_pulita = m.get('categoria', '')
        if len(cat_pulita) > 22:
            cat_pulita = cat_pulita[:19] + "..."
        tipo_pulito = tipo[:8] if len(tipo) > 8 else tipo
        lines.append(
            f"  {m.get('data', ''):<12} "
            f"{cat_pulita:<22} "
            f"{tipo_pulito:<10} "
            f"{str_importo:>12}   "
            f"{m.get('descrizione', '')}"
        )
    saldo = tot_ent - tot_usc
    lines += [
        linea_singola,
        "",
        f"Riepilogo Finanziario".rjust(70),
        f"─────────────────────".rjust(70),
        f"Totale Entrate: {tot_ent:>15.2f} €".rjust(70),
        f"Totale Uscite:  {tot_usc:>15.2f} €".rjust(70),
        f"Saldo Netto:    {saldo:>15.2f} €".rjust(70),
        "",
        linea_doppia,
        f"Documento generato il {datetime.date.today().strftime('%d-%m-%Y')}".center(LARGHEZZA_DOC),
        linea_doppia,
    ]
    contenuto = "\n".join(lines)
    now = datetime.date.today()
    fname = f"Estratto_{nome}_{now.strftime('%d-%m-%Y')}"
    self.show_export_preview(contenuto, default_filename=fname)
    
def _immobil_estratto_totale(self, db, v_fmese=None, v_fanno=None):
    if "immobili" not in db or not db["immobili"]:
        self.show_toast("Nessun immobile presente nel database.")
        return
    mese_sel = v_fmese.get() if v_fmese else "Tutti"
    anno_sel = v_fanno.get() if v_fanno else "Tutti"

    def _match(data_str):
        if len(data_str) != 10:
            return True
        if anno_sel != "Tutti" and data_str[-4:] != anno_sel:
            return False
        if mese_sel != "Tutti" and data_str[3:5] != mese_sel:
            return False
        return True

    tutti_i_movimenti = []
    for imm in db["immobili"]:
        nome_imm = imm.get("nome", "Immobile")
        for m in imm.get("spese", []):
            if _match(m.get("data", "")):
                mov_copia = m.copy()
                mov_copia["_nome_immobile"] = nome_imm
                tutti_i_movimenti.append(mov_copia)
    tutti_i_movimenti.sort(key=lambda x: x.get("data", ""))

    periodo_str = ""
    if mese_sel != "Tutti" or anno_sel != "Tutti":
        periodo_str = f"  Periodo: {mese_sel if mese_sel != 'Tutti' else '--'}/{anno_sel if anno_sel != 'Tutti' else '----'}"

    linea_doppia  = "═" * 110
    linea_singola = "─" * 110
    lines = [
        linea_doppia,
        f"  Gestione Immobili  ".center(110),
        f"  Estratto conto generale e cumulativo".center(110),
    ]
    if periodo_str:
        lines.append(periodo_str.center(110))
    lines += [
        linea_doppia,
        "",
        f"  Riepilogo patrimonio attivo:",
        f"  ────────────────────────────",
    ]
    for imm in db["immobili"]:
        lines.append(f"  • {imm.get('nome', 'Immobile'):<25} (Inquilino: {imm.get('inquilino', '─'):<20})")
    lines += [
        "",
        linea_doppia,
        f"  {'DATA':<12} {'IMMOBILE':<18} {'CATEGORIA':<30} {'TIPO':<10} {'IMPORTO':>12}   {'DESCRIZIONE'}",
        linea_singola,
    ]
    tot_ent = 0.0
    tot_usc = 0.0
    for m in tutti_i_movimenti:
        tipo = m.get("tipo", "")
        try:
            imp = float(m.get("importo", 0))
        except ValueError:
            imp = 0.0
        if tipo.lower() == "entrata":
            tot_ent += imp
            segno = "+"
        else:
            tot_usc += imp
            segno = "-"
        str_importo = f"{segno}{imp:.2f}"
        cat_pula = m.get('categoria', '')
        if len(cat_pula) > 28:
            cat_pula = cat_pula[:25] + "..."
        nome_imm_pulito = m.get('_nome_immobile', '')
        if len(nome_imm_pulito) > 16:
            nome_imm_pulito = nome_imm_pulito[:13] + "..."
        lines.append(
            f"  {m.get('data', ''):<12} {nome_imm_pulito:<18} {cat_pula:<30} "
            f"{tipo:<10} {str_importo:>12}   {m.get('descrizione', '')}"
        )
    saldo = tot_ent - tot_usc
    lines += [
        linea_singola,
        "",
        f"  Bilancio Globale Complessivo".rjust(100),
        f"  ────────────────────────────".rjust(100),
        f"  Totale Entrate Generali: {tot_ent:>15.2f} €".rjust(100),
        f"  Totale Uscite Generali:  {tot_usc:>15.2f} €".rjust(100),
        f"  Saldo Netto Totale:      {saldo:>15.2f} €".rjust(100),
        "",
        linea_doppia,
        f"  Documento complessivo generato il {datetime.date.today().strftime('%d-%m-%Y')}".center(110),
        linea_doppia,
    ]
    contenuto = "\n".join(lines)
    now = datetime.date.today()
    fname = f"Estratto_Generale_{now.strftime('%d-%m-%Y')}"
    self.show_export_preview(contenuto, default_filename=fname)
