#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import uuid
import datetime
from collections import defaultdict
import tkinter as tk
from tkinter import ttk
from moduli.modello_spesa import SpesaEntry

CATEGORIE_VEICOLO_DEFAULT = [
    "Assicurazione",
    "Bollo",
    "Carburante",
    "Gomme",
    "Lavaggio",
    "Manutenzione Ordinaria",
    "Manutenzione Straordinaria",
    "Multe",
    "Parcheggio/Pedaggi",
    "Revisione",
    "Tagliando",
    "Varie",
]

LIMITE_MAX_VEICOLI = 7

_PALETTE_GRAFICO = ["#61AFEF", "#98C379", "#E06C75", "#E5C07B", "#C678DD", "#56B6C2", "#D19A66"]
_COL_VERDE  = "#98C379"
_COL_ROSSO  = "#E06C75"
_COL_AMBRA  = "#E5C07B"

def _veicoli_carica(self):
    import __main__ as _app
    VEICOLI_FILE = _app.VEICOLI_FILE
    if os.path.exists(VEICOLI_FILE):
        try:
            with open(VEICOLI_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"veicoli": []}

def _veicoli_salva(self, db):
    import __main__ as _app
    VEICOLI_FILE = _app.VEICOLI_FILE
    DB_DIR = _app.DB_DIR
    try:
        os.makedirs(DB_DIR, exist_ok=True)
        with open(VEICOLI_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
    except Exception as e:
        self.show_toast(f"Errore salvataggio Veicoli: {e}")

def _veicoli_giorni_a_scadenza(self, data_str):
    if not data_str:
        return None
    try:
        d = datetime.datetime.strptime(data_str, "%d-%m-%Y").date()
    except ValueError:
        return None
    return (d - datetime.date.today()).days

def _veicoli_colore_giorni(self, giorni, soglia_rossa=15, soglia_ambra=45):
    if giorni is None:
        return None
    if giorni <= soglia_rossa:
        return _COL_ROSSO
    if giorni <= soglia_ambra:
        return _COL_AMBRA
    return _COL_VERDE

def _veicoli_testo_scadenza(self, data_str):
    giorni = self._veicoli_giorni_a_scadenza(data_str)
    if giorni is None:
        return "Non impostata", None
    if giorni < 0:
        return f"SCADUTA da {abs(giorni)} gg  ({data_str})", _COL_ROSSO
    if giorni == 0:
        return f"Scade OGGI  ({data_str})", _COL_ROSSO
    return f"tra {giorni} gg  ({data_str})", self._veicoli_colore_giorni(giorni)

def _veicoli_costo_al_km(self, v):
    try:
        km_i = float(v.get("km_iniziale", 0) or 0)
        km_a = float(v.get("km_attuali", 0) or 0)
    except ValueError:
        return None
    percorsi = km_a - km_i
    if percorsi <= 0:
        return None
    totale = sum(float(m.get("importo", 0) or 0) for m in v.get("movimenti", []))
    return totale / percorsi

def _veicoli_consumo_medio(self, v):

    rifornimenti = [
        m for m in v.get("movimenti", [])
        if m.get("categoria") == "Carburante"
        and str(m.get("km", "")).strip() not in ("", "0")
        and str(m.get("litri", "")).strip() not in ("", "0")
    ]
    if len(rifornimenti) < 2:
        return None
    try:
        rifornimenti = sorted(rifornimenti, key=lambda m: float(m["km"]))
    except (ValueError, TypeError):
        return None
    valori = []
    for prec, succ in zip(rifornimenti, rifornimenti[1:]):
        try:
            delta_km = float(succ["km"]) - float(prec["km"])
            litri = float(succ["litri"])
        except (ValueError, TypeError):
            continue
        if delta_km > 0 and litri > 0:
            valori.append(litri / delta_km * 100)
    if not valori:
        return None
    return sum(valori) / len(valori)

def veicoli(self):
    if hasattr(self, "_veicoli_win") and self._veicoli_win and self._veicoli_win.winfo_exists():
        self._veicoli_win.lift()
        self._veicoli_win.focus_force()
        return
    db = self._veicoli_carica()
    win = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    win.title("Veicoli — Gestione Parco Auto")
    self._veicoli_win = win
    win.bind("<Destroy>", lambda e: setattr(self, "_veicoli_win", None) if e.widget is win else None)
    win.bind("<Escape>", lambda e: win.destroy())
    win.withdraw()
    win.update_idletasks()
    W, H = 1300, 660
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
        b.image = img
        b.pack(side=tk.LEFT, padx=6)
        b.bind("<Button-1>", lambda e: cmd())
        return b

    _btn(toolbar, " Nuovo Veicolo",   lambda: self._veicoli_nuovo(db, nb, win),   "auto_manutenzione")
    _btn(toolbar, " Elimina Veicolo", lambda: self._veicoli_elimina(db, nb, win), "delete")
    _btn(toolbar, " Grafici",         lambda: self._veicoli_grafici(db),          "report")

    def _get_vars():
        try:
            idx = nb.index(nb.select())
            return getattr(self, "_veicoli_vars", {}).get(idx, (None, None))
        except Exception:
            return (None, None)

    _btn(toolbar, " Estratto",        lambda: self._veicoli_estratto(db, nb, *_get_vars()),        "descrizione")
    _btn(toolbar, " Estratto Totale", lambda: self._veicoli_estratto_totale(db, *_get_vars()),      "report")
    _btn(toolbar, " Salva",           lambda: (self._veicoli_salva(db), self.show_toast("Veicoli salvati.")), "salva")
    _btn(toolbar, " Chiudi",          lambda: win.destroy(),                       "chiudi")

    nb = ttk.Notebook(win)
    nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    if not db["veicoli"]:
        ph = ttk.Frame(nb)
        nb.add(ph, text="  (nessun veicolo)  ")
        tk.Label(
            ph, text="Clicca '🚗 Nuovo Veicolo' per iniziare",
            font=("Arial", 12), bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER
        ).pack(expand=True)
    else:
        for v in db["veicoli"]:
            self._veicoli_crea_tab(nb, v, db, win)

def _veicoli_crea_tab(self, nb, v, db, win):
    tab = ttk.Frame(nb)
    nb.add(tab, text=f"  🚗 {v.get('nome','Veicolo')}  ")

    ana_lf = ttk.LabelFrame(tab, text="📋 Anagrafica", style="RedBold.TLabelframe")
    ana_lf.pack(fill=tk.X, padx=8, pady=(6, 4))

    righe_campi = [
        [("Nome/Targa", "nome", 16), ("Modello", "modello", 22), ("Targa", "targa", 12)],
        [("Km Iniziale", "km_iniziale", 10), ("Km Attuali", "km_attuali", 10), ("Data Immatricolazione", "data_immatricolazione", 12)],
        [("Prossimo Tagliando (km)", "prossimo_tagliando_km", 10), ("Note", "note", 40), ("Conto Bancario", "conto_bancario", 20)],
    ]
    vars_ana = {}
    widgets_combo_ana = {}
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    conti_disponibili = ["(nessuno)"]
    try:
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as f:
            _db_p = json.load(f)
        conti_disponibili += [c.get("nome", "") for c in _db_p.get("conti", []) if c.get("nome")]
    except Exception:
        pass
    for r_idx, riga in enumerate(righe_campi):
        for col, (etichetta, chiave, w) in enumerate(riga):
            tk.Label(ana_lf, text=etichetta + ":", bg=self.COLOR_WIDGET_BG,
                     fg=self.COLOR_HEADER, font=("Arial", 9, "bold")).grid(
                row=r_idx, column=col * 2, sticky="w", padx=(8, 2), pady=2)
            val = v.get(chiave, "")
            vv = tk.StringVar(value=str(val))
            vars_ana[chiave] = vv
            if chiave == "data_immatricolazione":
                frm_data_imm = tk.Frame(ana_lf, bg=self.COLOR_WIDGET_BG)
                frm_data_imm.grid(row=r_idx, column=col * 2 + 1, sticky="ew", padx=(0, 8), pady=2)
                ent_imm = ttk.Entry(frm_data_imm, textvariable=vv, width=w, style="TEntry")
                ent_imm.pack(side=tk.LEFT)
                btn_cal_imm = ttk.Label(frm_data_imm, image=self.icone_gui.get("calendario"),
                                        background=self.COLOR_WIDGET_BG, cursor="hand2")
                btn_cal_imm.image = self.icone_gui.get("calendario")
                btn_cal_imm.pack(side=tk.LEFT, padx=(4, 0))
                btn_cal_imm.bind("<Button-1>", lambda e, ent=ent_imm, vv=vv: self.mostra_calendario_popup_semplice(ent, vv))
            elif chiave == "conto_bancario":
                if vv.get() not in conti_disponibili:
                    vv.set("(nessuno)")
                cb_conto = ttk.Combobox(ana_lf, textvariable=vv, values=conti_disponibili, width=w,
                                         state="readonly", style="Border.TCombobox")
                cb_conto.grid(row=r_idx, column=col * 2 + 1, sticky="ew", padx=(0, 8), pady=2)
                widgets_combo_ana[chiave] = cb_conto
            else:
                ttk.Entry(ana_lf, textvariable=vv, width=w, style="TEntry").grid(
                    row=r_idx, column=col * 2 + 1, sticky="ew", padx=(0, 8), pady=2)

    def _salva_ana():
        for chiave, var in vars_ana.items():
            if chiave in widgets_combo_ana:
                val = widgets_combo_ana[chiave].get().strip()
            else:
                val = var.get().strip()
            if chiave in ("km_iniziale", "km_attuali", "prossimo_tagliando_km"):
                try:
                    v[chiave] = float(val.replace(",", "."))
                except ValueError:
                    v[chiave] = 0.0
            else:
                v[chiave] = val
        idx = nb.index(nb.select())
        nb.tab(idx, text=f"  🚗 {v.get('nome','Veicolo')}  ")
        self._veicoli_salva(db)
        self.show_toast("Anagrafica salvata.")
        _aggiorna_pannello_stato()

    img_save_ana = self.icone_gui.get("check")
    btn_salva = ttk.Label(
        ana_lf, compound="left", image=img_save_ana,
        text=" Salva Anagrafica" if img_save_ana else "Salva Anagrafica",
        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2"
    )
    btn_salva.image = img_save_ana
    btn_salva.grid(row=0, column=6, rowspan=1, padx=8, pady=2, sticky="e")
    btn_salva.bind("<Button-1>", lambda e: _salva_ana())

    stato_lf = ttk.LabelFrame(tab, text="⏱ Scadenze e Indicatori", style="RedBold.TLabelframe")
    stato_lf.pack(fill=tk.X, padx=8, pady=(0, 4))
    stato_lf.columnconfigure(2, weight=1)
    campi_scad = [("Bollo", "scad_bollo"), ("Assicurazione", "scad_assicurazione"), ("Revisione", "scad_revisione")]
    lbl_scad = {}
    vars_scad = {}
    for riga_idx, (etichetta, chiave) in enumerate(campi_scad):
        tk.Label(stato_lf, text=etichetta + ":", bg=self.COLOR_WIDGET_BG,
                 fg=self.COLOR_HEADER, font=("Arial", 9, "bold"), width=13, anchor="w").grid(
            row=riga_idx, column=0, sticky="w", padx=(8, 2), pady=4)
        vv = tk.StringVar(value=str(v.get(chiave, "")))
        vars_scad[chiave] = vv
        frm_data_box = tk.Frame(stato_lf, bg=self.COLOR_WIDGET_BG)
        frm_data_box.grid(row=riga_idx, column=1, sticky="w", padx=(0, 2), pady=4)
        ent = ttk.Entry(frm_data_box, textvariable=vv, width=11)
        ent.pack(side=tk.LEFT)
        btn_cal = ttk.Label(frm_data_box, image=self.icone_gui.get("calendario"),
                             background=self.COLOR_WIDGET_BG, cursor="hand2")
        btn_cal.image = self.icone_gui.get("calendario")
        btn_cal.pack(side=tk.LEFT, padx=(4, 0))
        btn_cal.bind("<Button-1>", lambda e, ent=ent, vv=vv: self.mostra_calendario_popup_semplice(ent, vv))
        lbl = tk.Label(stato_lf, text="—", bg=self.COLOR_WIDGET_BG,
                        fg=self.TEXT_COLOR, font=("Arial", 9, "bold"), anchor="w")
        lbl.grid(row=riga_idx, column=2, sticky="w", padx=(6, 14), pady=4)
        lbl_scad[chiave] = lbl

    def _salva_scadenze():
        for chiave, var in vars_scad.items():
            val = var.get().strip()
            if val:
                try:
                    datetime.datetime.strptime(val, "%d-%m-%Y")
                except ValueError:
                    self.show_toast(f"Data non valida per {chiave} (gg-mm-aaaa).")
                    continue
            v[chiave] = val
        self._veicoli_salva(db)
        self.show_toast("Scadenze salvate.")
        _aggiorna_pannello_stato()

    img_save_scad = self.icone_gui.get("check")
    btn_salva_scad = ttk.Label(
        stato_lf, compound="left", image=img_save_scad,
        text=" Salva Scadenze" if img_save_scad else "Salva Scadenze",
        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2"
    )
    btn_salva_scad.image = img_save_scad
    btn_salva_scad.grid(row=0, column=3, rowspan=3, padx=8, pady=4, sticky="ne")
    btn_salva_scad.bind("<Button-1>", lambda e: _salva_scadenze())

    riga2_lf = tk.Frame(stato_lf, bg=self.COLOR_WIDGET_BG)
    riga2_lf.grid(row=3, column=0, columnspan=4, sticky="ew", padx=8, pady=(0, 6))
    lbl_tagliando = tk.Label(riga2_lf, text="—", bg=self.COLOR_WIDGET_BG,
                              fg=self.TEXT_COLOR, font=("Arial", 9, "bold"))
    lbl_tagliando.pack(side=tk.LEFT, padx=(0, 20))
    lbl_costo_km = tk.Label(riga2_lf, text="—", bg=self.COLOR_WIDGET_BG,
                             fg=self.COLOR_HEADER, font=("Arial", 9, "bold"))
    lbl_costo_km.pack(side=tk.LEFT, padx=(0, 20))
    lbl_consumo = tk.Label(riga2_lf, text="—", bg=self.COLOR_WIDGET_BG,
                            fg=self.COLOR_HEADER, font=("Arial", 9, "bold"))
    lbl_consumo.pack(side=tk.LEFT)

    def _aggiorna_pannello_stato():
        for _et, chiave in campi_scad:
            testo, colore = self._veicoli_testo_scadenza(v.get(chiave, ""))
            lbl_scad[chiave].config(text=testo, fg=colore or self.TEXT_COLOR)
        try:
            km_a = float(v.get("km_attuali", 0) or 0)
            km_t = float(v.get("prossimo_tagliando_km", 0) or 0)
        except ValueError:
            km_a, km_t = 0, 0
        if km_t > 0:
            residuo = km_t - km_a
            colore_t = _COL_ROSSO if residuo <= 500 else (_COL_AMBRA if residuo <= 2000 else _COL_VERDE)
            lbl_tagliando.config(text=f"🔧 Tagliando: {residuo:,.0f} km rimanenti", fg=colore_t)
        else:
            lbl_tagliando.config(text="🔧 Tagliando: non impostato", fg=self.TEXT_COLOR)
        costo_km = self._veicoli_costo_al_km(v)
        lbl_costo_km.config(text=f"💰 Costo medio: € {costo_km:.3f}/km" if costo_km else "💰 Costo medio: —")
        consumo = self._veicoli_consumo_medio(v)
        lbl_consumo.config(text=f"⛽ Consumo medio: {consumo:.1f} L/100km" if consumo else "⛽ Consumo medio: —")

    main_container = tk.Frame(tab, bg=self.COLOR_WIDGET_BG)
    main_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 6))

    form_lf = ttk.LabelFrame(main_container, text="⚙️ Registra Movimento", style="RedBold.TLabelframe", width=280)
    form_lf.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
    form_lf.columnconfigure(1, weight=1)

    cat_v = v.setdefault("categorie", list(CATEGORIE_VEICOLO_DEFAULT))

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
                         background=self.COLOR_WIDGET_BG, cursor="hand2")
    btn_cal.image = self.icone_gui.get("calendario")
    btn_cal.grid(row=0, column=1, padx=(4, 0))
    btn_cal.bind("<Button-1>", lambda e: self.mostra_calendario_popup_semplice(ent_data, v_data))
    r += 1

    tk.Label(form_lf, text="Categoria:", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
             font=("Arial", 9, "bold")).grid(row=r, column=0, sticky="w", padx=6, pady=3)
    v_cat = tk.StringVar(value=cat_v[0] if cat_v else "Varie")
    cb_cat = ttk.Combobox(form_lf, textvariable=v_cat, values=cat_v, width=25, style="Border.TCombobox")
    cb_cat.grid(row=r, column=1, sticky="ew", padx=6, pady=3)
    r += 1

    tk.Label(form_lf, text="Km Odometro:", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
             font=("Arial", 9, "bold")).grid(row=r, column=0, sticky="w", padx=6, pady=3)
    v_km = tk.StringVar()
    ttk.Entry(form_lf, textvariable=v_km, width=12).grid(row=r, column=1, sticky="ew", padx=6, pady=3)
    r += 1

    tk.Label(form_lf, text="Litri (solo Carburante):", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
             font=("Arial", 9, "bold")).grid(row=r, column=0, sticky="w", padx=6, pady=3)
    v_litri = tk.StringVar()
    ttk.Entry(form_lf, textvariable=v_litri, width=10).grid(row=r, column=1, sticky="ew", padx=6, pady=3)
    r += 1

    tk.Label(form_lf, text="Descrizione:", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
             font=("Arial", 9, "bold")).grid(row=r, column=0, sticky="w", padx=6, pady=3)
    v_desc = tk.StringVar()
    ent_desc = ttk.Entry(form_lf, textvariable=v_desc, width=22)
    ent_desc.grid(row=r, column=1, sticky="ew", padx=6, pady=3)
    r += 1

    tk.Label(form_lf, text="Importo €:", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
             font=("Arial", 9, "bold")).grid(row=r, column=0, sticky="w", padx=6, pady=3)
    v_imp = tk.StringVar()

    def limita_importo(*a):
        testo = "".join(c for c in v_imp.get() if c.isdigit() or c == ".")
        punti = [i for i, c in enumerate(testo) if c == "."]
        if len(punti) > 1:
            idx_valido = punti[0]
            testo = "".join(c for i, c in enumerate(testo) if c.isdigit() or i == idx_valido)
        if v_imp.get() != testo:
            v_imp.set(testo)
    v_imp.trace_add("write", limita_importo)
    ent_imp = ttk.Entry(form_lf, textvariable=v_imp, width=12)
    ent_imp.grid(row=r, column=1, sticky="ew", padx=6, pady=3)
    ent_imp.bind("<Return>", lambda e: _aggiungi())
    r += 1

    tk.Label(form_lf, text="Categorie:", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
             font=("Arial", 9, "bold")).grid(row=r, column=0, sticky="w", padx=6, pady=(8, 2))
    r += 1
    cat_frame = tk.Frame(form_lf, bg=self.COLOR_WIDGET_BG)
    cat_frame.grid(row=r, column=0, columnspan=2, sticky="ew", padx=6, pady=2)
    r += 1
    v_nuova_cat = tk.StringVar()
    ttk.Entry(cat_frame, textvariable=v_nuova_cat, width=25).pack(side=tk.LEFT, padx=(0, 4))

    def _aggiungi_cat():
        nc = v_nuova_cat.get().strip()
        if nc and nc not in cat_v:
            cat_v.append(nc)
            cat_v.sort(key=str.lower)
            cb_cat["values"] = cat_v
            v_cat.set(nc)
            self._veicoli_salva(db)
            v_nuova_cat.set("")
            self.show_toast(f"Categoria '{nc}' aggiunta.")

    def _rimuovi_cat():
        sel = v_cat.get()
        if sel in cat_v and len(cat_v) > 1:
            cat_v.remove(sel)
            cb_cat["values"] = cat_v
            v_cat.set(cat_v[0])
            self._veicoli_salva(db)

    img_add_cat = self.icone_gui.get("aggiungi")
    btn_add_cat = ttk.Label(cat_frame, compound="left", image=img_add_cat,
                             text="" if img_add_cat else "➕",
                             background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2")
    btn_add_cat.image = img_add_cat
    btn_add_cat.pack(side=tk.LEFT, padx=2)
    btn_add_cat.bind("<Button-1>", lambda e: _aggiungi_cat())

    img_remove_cat = self.icone_gui.get("delete")
    btn_remove_cat = ttk.Label(cat_frame, compound="left", image=img_remove_cat,
                                text="" if img_remove_cat else "➖",
                                background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2")
    btn_remove_cat.image = img_remove_cat
    btn_remove_cat.pack(side=tk.LEFT, padx=2)
    btn_remove_cat.bind("<Button-1>", lambda e: _rimuovi_cat())

    btn_frame = tk.Frame(form_lf, bg=self.COLOR_WIDGET_BG)
    btn_frame.grid(row=r, column=0, columnspan=2, pady=8)

    tree_lf = ttk.LabelFrame(main_container, text="📒 Movimenti", style="RedBold.TLabelframe")
    tree_lf.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 0), pady=3)

    filtri_tree_f = tk.Frame(tree_lf, bg=self.COLOR_WIDGET_BG)
    filtri_tree_f.pack(fill=tk.X, padx=4, pady=(4, 0))
    tk.Label(filtri_tree_f, text="Categoria:", bg=self.COLOR_WIDGET_BG,
             fg=self.COLOR_HEADER, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
    v_fcat = tk.StringVar(value="Tutte")
    cb_fcat = ttk.Combobox(filtri_tree_f, textvariable=v_fcat, values=["Tutte"] + sorted(cat_v),
                            state="readonly", style="Border.TCombobox", width=22)
    cb_fcat.pack(side=tk.LEFT, padx=(0, 8))
    cb_fcat.bind("<<ComboboxSelected>>", lambda e: _popola_tree())

    tk.Label(filtri_tree_f, text="Mese:", bg=self.COLOR_WIDGET_BG,
             fg=self.COLOR_HEADER, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
    v_fmese = tk.StringVar(value=datetime.date.today().strftime("%m"))
    mesi_f = ["Tutti", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
    cb_fmese = ttk.Combobox(filtri_tree_f, textvariable=v_fmese, values=mesi_f,
                             state="readonly", style="Border.TCombobox", width=5)
    cb_fmese.pack(side=tk.LEFT, padx=(0, 8))
    cb_fmese.bind("<<ComboboxSelected>>", lambda e: _popola_tree())

    tk.Label(filtri_tree_f, text="Anno:", bg=self.COLOR_WIDGET_BG,
             fg=self.COLOR_HEADER, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
    anni_f = sorted({m.get("data", "")[-4:] for m in v.get("movimenti", []) if len(m.get("data", "")) == 10}, reverse=True)
    v_fanno = tk.StringVar(value=str(datetime.date.today().year))
    cb_fanno = ttk.Combobox(filtri_tree_f, textvariable=v_fanno, values=["Tutti"] + anni_f,
                             state="readonly", style="Border.TCombobox", width=7)
    cb_fanno.pack(side=tk.LEFT, padx=(0, 8))
    cb_fanno.bind("<<ComboboxSelected>>", lambda e: _popola_tree())

    def _reset_filtri():
        v_fmese.set(datetime.date.today().strftime("%m"))
        v_fanno.set(str(datetime.date.today().year))
        v_fcat.set("Tutte")
        _popola_tree()

    btn_reset = tk.Label(filtri_tree_f, text="↺ Reset", bg=self.COLOR_WIDGET_BG,
                          fg=self.COLOR_HIGHLIGHT, font=("Arial", 8, "bold"), cursor="hand2")
    btn_reset.pack(side=tk.LEFT, padx=(4, 0))
    btn_reset.bind("<Button-1>", lambda e: _reset_filtri())

    if not hasattr(self, "_veicoli_vars"):
        self._veicoli_vars = {}
    tab_idx = nb.index("end") - 1 if nb.index("end") > 0 else 0
    self._veicoli_vars[tab_idx] = (v_fmese, v_fanno)

    tot_frame = tk.Frame(tree_lf, bg=self.COLOR_WIDGET_BG)
    tot_frame.pack(fill=tk.X, padx=4, pady=(4, 0))
    lbl_tot_periodo = tk.Label(tot_frame, text="Spesa periodo: € 0.00", bg=self.COLOR_WIDGET_BG,
                                fg=self.COLOR_RED, font=("Arial", 10, "bold"))
    lbl_tot_periodo.pack(side=tk.LEFT, padx=4)

    cols = ("Data", "Categoria", "Km", "Descrizione", "Importo")
    tree_frame_inner = ttk.Frame(tree_lf)
    tree_frame_inner.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
    tree = ttk.Treeview(tree_frame_inner, columns=cols, show="headings", selectmode="browse")
    vsb = ttk.Scrollbar(tree_frame_inner, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(fill=tk.BOTH, expand=True)
    wcfg = {"Data": (90, "w"), "Categoria": (140, "w"), "Km": (80, "e"),
            "Descrizione": (200, "w"), "Importo": (90, "e")}
    for c in cols:
        w, anc = wcfg[c]
        tree.heading(c, text=c, command=lambda _c=c: self.treeview_sort_column(tree, _c, False))
        tree.column(c, width=w, anchor=anc)
    tree.tag_configure("spesa", foreground=self.COLOR_RED)

    def _match_f(data_str):
        if len(data_str) != 10:
            return True
        ms, an = v_fmese.get(), v_fanno.get()
        if an != "Tutti" and data_str[-4:] != an:
            return False
        if ms != "Tutti" and data_str[3:5] != ms:
            return False
        return True

    def _movimenti_visibili():
        fc = v_fcat.get()
        return [m for m in v.get("movimenti", [])
                if _match_f(m.get("data", "")) and (fc == "Tutte" or m.get("categoria", "") == fc)]

    def _popola_tree():
        anni_agg = sorted({m.get("data", "")[-4:] for m in v.get("movimenti", []) if len(m.get("data", "")) == 10}, reverse=True)
        cb_fanno["values"] = ["Tutti"] + anni_agg
        cb_fcat["values"] = ["Tutte"] + sorted(cat_v)
        migrato = False
        for m in v.get("movimenti", []):
            if not m.get("id"):
                m["id"] = str(uuid.uuid4())
                migrato = True
        if migrato:
            self._veicoli_salva(db)
        tree.delete(*tree.get_children())
        vis = sorted(_movimenti_visibili(), key=lambda x: x.get("data", ""))
        for m in vis:
            try:
                val_float = float(m.get("importo", 0))
            except (ValueError, TypeError):
                val_float = 0.0
            km_txt = f"{float(m['km']):,.0f}" if str(m.get("km", "")).strip() not in ("", "0") else "—"
            tree.insert("", "end", iid=m["id"], tags=("spesa",), values=(
                m.get("data", ""), m.get("categoria", ""), km_txt,
                m.get("descrizione", ""), f"{val_float:.2f} €"
            ))
        tot = sum(float(m.get("importo", 0) or 0) for m in vis)
        lbl_tot_periodo.config(text=f"Spesa periodo: € {tot:,.2f}")
        _aggiorna_pannello_stato()

    riga_in_modifica = None

    def _carica_in_form():
        nonlocal riga_in_modifica
        sel = tree.selection()
        if not sel:
            self.show_toast("Seleziona un movimento da modificare.")
            return
        mid = sel[0]
        movimento = next((m for m in v.get("movimenti", []) if m.get("id") == mid), None)
        if not movimento:
            self.show_toast("Movimento non trovato.")
            return
        riga_in_modifica = movimento
        v_data.set(movimento.get("data", ""))
        v_cat.set(movimento.get("categoria", ""))
        v_km.set(str(movimento.get("km", "")))
        v_litri.set(str(movimento.get("litri", "")))
        v_desc.set(movimento.get("descrizione", ""))
        try:
            v_imp.set(f"{float(movimento.get('importo', 0)):.2f}")
        except (ValueError, TypeError):
            v_imp.set("")
        btn_add.config(text=" Conferma" if img_add else "✓ Conferma")

    def _aggiungi():
        nonlocal riga_in_modifica
        data = v_data.get().strip()
        cat = v_cat.get().strip()
        desc = v_desc.get().strip()
        try:
            imp = float(v_imp.get().strip())
        except ValueError:
            self.show_toast("Importo non valido.")
            return
        try:
            datetime.datetime.strptime(data, "%d-%m-%Y")
        except ValueError:
            self.show_toast("Data non valida (gg-mm-aaaa).")
            return
        km_val = v_km.get().strip().replace(",", ".")
        litri_val = v_litri.get().strip().replace(",", ".")
        try:
            km_num = float(km_val) if km_val else ""
        except ValueError:
            km_num = ""
        try:
            litri_num = float(litri_val) if litri_val else ""
        except ValueError:
            litri_num = ""
        if riga_in_modifica is not None:
            riga_in_modifica.update({
                "data": data, "categoria": cat, "km": km_num,
                "litri": litri_num, "importo": imp, "descrizione": desc
            })
            riga_in_modifica = None
            btn_add.config(text=" Aggiungi" if img_add else "➕ Aggiungi")
            self.show_toast("Movimento modificato.")
        else:
            v.setdefault("movimenti", []).append({
                "id": str(uuid.uuid4()), "data": data, "categoria": cat,
                "km": km_num, "litri": litri_num, "importo": imp, "descrizione": desc
            })
            self.show_toast("Movimento aggiunto.")
        if km_num:
            try:
                if float(km_num) > float(v.get("km_attuali", 0) or 0):
                    v["km_attuali"] = float(km_num)
                    vars_ana["km_attuali"].set(str(km_num))
            except ValueError:
                pass
        self._veicoli_salva(db)
        v_desc.set("")
        v_imp.set("")
        v_km.set("")
        v_litri.set("")
        _popola_tree()

    def _elimina_mov():
        sel = tree.selection()
        if not sel:
            return
        mid = sel[0]
        v["movimenti"] = [m for m in v.get("movimenti", []) if m.get("id") != mid]
        self._veicoli_salva(db)
        _popola_tree()

    def _esporta_in_spesedb():
        fc = v_fcat.get()
        movimenti_filtrati = [
            m for m in v.get("movimenti", [])
            if _match_f(m.get("data", ""))
            and (fc == "Tutte" or m.get("categoria", "") == fc)
        ]
        tot = sum(float(m.get("importo", 0) or 0) for m in movimenti_filtrati)
        if tot == 0:
            self.show_toast("Nessuna spesa da esportare per il periodo selezionato.")
            return
        nome = v.get("nome", "Veicolo")
        cat_export = "AutoPark"
        if cat_export not in self.categorie:
            self.categorie.append(cat_export)
            self.aggiorna_combobox_categorie()
        oggi = datetime.date.today()
        if oggi not in self.spese:
            self.spese[oggi] = []
        nome_conto = widgets_combo_ana["conto_bancario"].get().strip() if "conto_bancario" in widgets_combo_ana else v.get("conto_bancario", "")
        self.spese[oggi].append(SpesaEntry.nuova(
            cat_export, f"Veicoli: {nome}", tot, "Uscita",
            conto=(nome_conto if nome_conto and nome_conto != "(nessuno)" else ""),
            hashtag=["#veicoli"]
        ))
        self.save_db()
        self.refresh_gui()
        self.show_toast(f"Spesa {nome} ({tot:.2f}€) esportata in SpesaDB.")

    img_add = self.icone_gui.get("aggiungi")
    btn_add = ttk.Label(btn_frame, compound="left", image=img_add,
                         text=" Aggiungi" if img_add else "➕ Aggiungi",
                         background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2")
    btn_add.image = img_add
    btn_add.pack(side=tk.LEFT, padx=4)
    btn_add.bind("<Button-1>", lambda e: _aggiungi())

    img_edit = self.icone_gui.get("modifica")
    btn_edit = ttk.Label(btn_frame, compound="left", image=img_edit,
                          text=" Modifica" if img_edit else "📝 Modifica",
                          background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2")
    btn_edit.image = img_edit
    btn_edit.pack(side=tk.LEFT, padx=4)
    btn_edit.bind("<Button-1>", lambda e: _carica_in_form())

    img_delete = self.icone_gui.get("delete")
    btn_delete = ttk.Label(btn_frame, compound="left", image=img_delete,
                            text=" Elimina" if img_delete else "🗑 Elimina",
                            background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2")
    btn_delete.image = img_delete
    btn_delete.pack(side=tk.LEFT, padx=4)
    btn_delete.bind("<Button-1>", lambda e: _elimina_mov())

    btn_frame2 = tk.Frame(form_lf, bg=self.COLOR_WIDGET_BG)
    btn_frame2.grid(row=r + 1, column=0, columnspan=2, pady=(0, 8))
    img_export = self.icone_gui.get("archivia")
    btn_export = ttk.Label(
        btn_frame2, compound="left", image=img_export,
        text=" → SpesaDB" if img_export else "📤 → SpesaDB",
        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2"
    )
    btn_export.image = img_export
    btn_export.pack(side=tk.LEFT, padx=4)
    btn_export.bind("<Button-1>", lambda e: _esporta_in_spesedb())
    tk.Label(btn_frame2, text="(esporta spesa periodo visualizzato)",
             bg=self.COLOR_WIDGET_BG, fg=self.COLOR_TEXT,
             font=("Arial", 8, "italic")).pack(side=tk.LEFT, padx=(4, 0))

    _popola_tree()

def _veicoli_nuovo(self, db, nb, win):
    popup = tk.Toplevel(win, bg=self.COLOR_TOPLEVEL)
    popup.title("Nuovo Veicolo")
    popup.transient(win)
    popup.resizable(False, False)
    popup.withdraw()
    win.update_idletasks()
    w, h = 380, 150
    x = win.winfo_rootx() + (win.winfo_width() // 2) - (w // 2)
    y = win.winfo_rooty() + (win.winfo_height() // 2) - (h // 2)
    popup.geometry(f"{w}x{h}+{max(0,x)}+{max(0,y)}")
    popup.deiconify()
    popup.lift()
    popup.focus_force()
    popup.bind("<Escape>", lambda e: popup.destroy())

    tk.Label(popup, text="Nome / Targa veicolo:", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 12, "bold")).pack(pady=(20, 4))
    v = tk.StringVar()

    def limita_caratteri(*a):
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
        if len(db.get("veicoli", [])) >= LIMITE_MAX_VEICOLI:
            self.show_toast(f"Limite raggiunto! Massimo {LIMITE_MAX_VEICOLI} veicoli consentiti.")
            popup.destroy()
            return
        for i in range(nb.index("end")):
            if "(nessun veicolo)" in nb.tab(i, "text"):
                nb.forget(i)
                break
        nuovo = {
            "id": str(uuid.uuid4()),
            "nome": nome,
            "modello": "",
            "targa": "",
            "km_iniziale": 0.0,
            "km_attuali": 0.0,
            "data_immatricolazione": "",
            "scad_bollo": "",
            "scad_assicurazione": "",
            "scad_revisione": "",
            "prossimo_tagliando_km": 0.0,
            "note": "",
            "categorie": list(CATEGORIE_VEICOLO_DEFAULT),
            "movimenti": [],
        }
        db["veicoli"].append(nuovo)
        self._veicoli_salva(db)
        self._veicoli_crea_tab(nb, nuovo, db, win)
        nb.select(nb.index("end") - 1)
        popup.destroy()

    popup.bind("<Return>", _ok)
    btn_box = tk.Frame(popup, bg=self.COLOR_WIDGET_BG)
    btn_box.pack(fill=tk.X, pady=12, padx=15)
    center_f = tk.Frame(btn_box, bg=self.COLOR_WIDGET_BG)
    center_f.pack(anchor=tk.CENTER)

    lbl_crea = ttk.Label(center_f, image=self.icone_gui.get("check"), text="Crea", compound=tk.LEFT,
                          cursor="hand2", background=self.COLOR_TOPLEVEL, foreground=self.TEXT_COLOR,
                          font=("Arial", 10, "bold"))
    lbl_crea.image = self.icone_gui.get("check")
    lbl_crea.pack(side=tk.LEFT, padx=15)
    lbl_crea.bind("<Button-1>", lambda e: _ok())

    lbl_chiudi = ttk.Label(center_f, image=self.icone_gui.get("chiudi"), text="Chiudi", compound=tk.LEFT,
                            cursor="hand2", background=self.COLOR_TOPLEVEL, foreground=self.TEXT_COLOR,
                            font=("Arial", 10, "bold"))
    lbl_chiudi.image = self.icone_gui.get("chiudi")
    lbl_chiudi.pack(side=tk.LEFT, padx=15)
    lbl_chiudi.bind("<Button-1>", lambda e: popup.destroy())

def _veicoli_elimina(self, db, nb, win):
    idx = nb.index(nb.select())
    if idx < 0 or idx >= len(db["veicoli"]):
        self.show_toast("Nessun veicolo selezionato.")
        return
    v = db["veicoli"][idx]
    if not self.show_custom_askyesno("Elimina Veicolo", f"Eliminare '{v.get('nome','')}' e tutti i suoi movimenti?"):
        return
    db["veicoli"].pop(idx)
    self._veicoli_salva(db)
    nb.forget(idx)
    if not db["veicoli"]:
        ph = ttk.Frame(nb)
        nb.add(ph, text="  (nessun veicolo)  ")
        tk.Label(ph, text="Clicca '🚗 Nuovo Veicolo' per iniziare",
                 font=("Arial", 12), bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER).pack(expand=True)
    self.show_toast("Veicolo eliminato.")

def _veicoli_grafici(self, db):
    if not db["veicoli"]:
        self.show_toast("Nessun veicolo presente.")
        return
    if hasattr(self, "_veicoli_grafici_win") and self._veicoli_grafici_win and self._veicoli_grafici_win.winfo_exists():
        self._veicoli_grafici_win.lift()
        self._veicoli_grafici_win.focus_force()
        return

    popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    self._veicoli_grafici_win = popup
    popup.title("Veicoli — Grafici")
    popup.transient(self)
    popup.bind("<Escape>", lambda e: popup.destroy())
    popup.withdraw()
    W, H = 1350, 630
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (W // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (H // 2)
    popup.geometry(f"{W}x{H}+{max(0,x)}+{max(0,y)}")
    popup.minsize(W, H)
    popup.deiconify()
    popup.lift()
    popup.focus_force()

    nomi_veicoli = [v.get("nome", "?") for v in db["veicoli"]]
    tutte_categorie = sorted({m.get("categoria", "Altro") for v in db["veicoli"] for m in v.get("movimenti", [])})
    anni_disponibili = sorted({
        m.get("data", "")[-4:] for v in db["veicoli"] for m in v.get("movimenti", [])
        if len(m.get("data", "")) == 10
    }, reverse=True)

    filtri_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL, pady=6)
    filtri_f.pack(fill=tk.X, padx=14, pady=(8, 0))

    tk.Label(filtri_f, text="Veicolo:", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
             font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
    v_veic = tk.StringVar(value="Tutti")
    cb_veic = ttk.Combobox(filtri_f, textvariable=v_veic, values=["Tutti"] + nomi_veicoli,
                            state="readonly", style="Border.TCombobox", width=22)
    cb_veic.pack(side=tk.LEFT, padx=(0, 10))

    tk.Label(filtri_f, text="Vista:", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
             font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
    v_vista = tk.StringVar(value="categoria")
    ttk.Radiobutton(filtri_f, text="Per Categoria", variable=v_vista, value="categoria",
                     style="Custom.TRadiobutton", command=lambda: _disegna()).pack(side=tk.LEFT, padx=4)
    ttk.Radiobutton(filtri_f, text="Confronto Veicoli", variable=v_vista, value="confronto",
                     style="Custom.TRadiobutton", command=lambda: _disegna()).pack(side=tk.LEFT, padx=4)

    tk.Label(filtri_f, text="Categoria:", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
             font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(10, 4))
    v_cat = tk.StringVar(value="Tutte")
    cb_cat = ttk.Combobox(filtri_f, textvariable=v_cat, values=["Tutte"] + tutte_categorie,
                           state="readonly", style="Border.TCombobox", width=20)
    cb_cat.pack(side=tk.LEFT, padx=(0, 10))

    _oggi = datetime.date.today()
    v_anno = tk.StringVar(value=str(_oggi.year))
    cb_anno = ttk.Combobox(filtri_f, textvariable=v_anno, values=["Tutti"] + anni_disponibili,
                            state="readonly", style="Border.TCombobox", width=7)
    cb_anno.pack(side=tk.RIGHT, padx=(0, 6))
    tk.Label(filtri_f, text="Anno:", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
             font=("Arial", 9, "bold")).pack(side=tk.RIGHT, padx=(0, 4))
    mesi = ["Tutti", "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]
    v_mese = tk.StringVar(value=f"{_oggi.month:02d}")
    cb_mese = ttk.Combobox(filtri_f, textvariable=v_mese, values=mesi,
                            state="readonly", style="Border.TCombobox", width=5)
    cb_mese.pack(side=tk.RIGHT, padx=(0, 6))
    tk.Label(filtri_f, text="Mese:", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
             font=("Arial", 9, "bold")).pack(side=tk.RIGHT, padx=(4, 4))

    cb_veic.bind("<<ComboboxSelected>>", lambda e: _disegna())
    cb_cat.bind("<<ComboboxSelected>>", lambda e: _disegna())
    cb_mese.bind("<<ComboboxSelected>>", lambda e: _disegna())
    cb_anno.bind("<<ComboboxSelected>>", lambda e: _disegna())

    canvas = tk.Canvas(popup, bg=self.COLOR_WIDGET_BG, highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True, padx=12, pady=(8, 4))

    footer_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL, pady=5)
    footer_f.pack(fill=tk.X, padx=14, pady=(0, 4))
    lbl_tot = tk.Label(footer_f, text="Totale: —", bg=self.COLOR_TOPLEVEL, fg=self.COLOR_RED,
                        font=("Arial", 9, "bold"))
    lbl_tot.pack(side=tk.LEFT)

    btn_chiudi_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    btn_chiudi_f.pack(pady=(0, 8))
    img_chiudi = self.icone_gui.get("chiudi")
    btn_chiudi = tk.Label(btn_chiudi_f, image=img_chiudi, text=" Chiudi", compound="left",
                           bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR, font=("Arial", 10, "bold"),
                           padx=20, pady=5, cursor="hand2")
    btn_chiudi.pack()
    btn_chiudi.bind("<Button-1>", lambda e: popup.destroy())
    popup.img_chiudi = img_chiudi

    def _match_periodo(data_str):
        if len(data_str) != 10:
            return True
        if v_anno.get() != "Tutti" and data_str[-4:] != v_anno.get():
            return False
        if v_mese.get() != "Tutti" and data_str[3:5] != v_mese.get():
            return False
        return True

    def _disegna(event=None):
        canvas.delete("all")
        cw = canvas.winfo_width() or W - 24
        ch = canvas.winfo_height() or H - 160
        if cw < 10 or ch < 10:
            return

        veicoli_attivi = db["veicoli"] if v_veic.get() == "Tutti" else \
            [v for v in db["veicoli"] if v.get("nome") == v_veic.get()]

        tot_generale = sum(
            float(m.get("importo", 0) or 0)
            for v in veicoli_attivi for m in v.get("movimenti", [])
            if _match_periodo(m.get("data", ""))
            and (v_cat.get() == "Tutte" or m.get("categoria", "") == v_cat.get())
        )
        lbl_tot.config(text=f"Totale: € {tot_generale:,.2f}")

        vista = v_vista.get()
        if vista == "confronto" and v_veic.get() == "Tutti":
            bars_data = []
            for v in db["veicoli"]:
                tot_v = sum(
                    float(m.get("importo", 0) or 0) for m in v.get("movimenti", [])
                    if _match_periodo(m.get("data", ""))
                    and (v_cat.get() == "Tutte" or m.get("categoria", "") == v_cat.get())
                )
                bars_data.append((v.get("nome", "?"), tot_v))
            titolo_base = "Confronto Spesa tra Veicoli"
        else:
            cat_totali = defaultdict(float)
            for v in veicoli_attivi:
                for m in v.get("movimenti", []):
                    if not _match_periodo(m.get("data", "")):
                        continue
                    cat = m.get("categoria", "Altro")
                    if v_cat.get() != "Tutte" and cat != v_cat.get():
                        continue
                    cat_totali[cat] += float(m.get("importo", 0) or 0)
            bars_data = list(cat_totali.items())
            titolo_base = f"Spesa per Categoria  |  {v_veic.get()}"

        bars_data = sorted(bars_data, key=lambda x: x[1], reverse=True)
        bars_data = [b for b in bars_data if b[1] > 0]
        if not bars_data:
            canvas.create_text(cw // 2, ch // 2, text="Nessun dato per i filtri selezionati",
                                fill=self.TEXT_COLOR, font=("Arial", 11))
            return

        per_lbl = ""
        if v_mese.get() != "Tutti" or v_anno.get() != "Tutti":
            per_lbl = f"  —  {v_mese.get() if v_mese.get() != 'Tutti' else ''}" \
                      f"{'/' if v_mese.get() != 'Tutti' and v_anno.get() != 'Tutti' else ''}" \
                      f"{v_anno.get() if v_anno.get() != 'Tutti' else ''}"
        titolo = f"{titolo_base}{per_lbl}"

        mx = max(v for _, v in bars_data) or 1
        margin_t, margin_b, margin_l, margin_r = 34, 18, 170, 110
        n = len(bars_data)
        plot_h = ch - margin_t - margin_b
        plot_w = cw - margin_l - margin_r
        bar_step = plot_h / n
        bar_h = max(6, int(bar_step * 0.60))

        canvas.create_text(cw // 2, margin_t // 2, text=titolo, fill=self.COLOR_HEADER, font=("Arial", 10, "bold"))
        canvas.create_line(margin_l, margin_t, margin_l, margin_t + plot_h, fill=self.TEXT_COLOR, width=1)
        for i in range(1, 5):
            x_g = margin_l + int(plot_w * i / 4)
            v_g = mx * i / 4
            canvas.create_line(x_g, margin_t, x_g, margin_t + plot_h, fill=self.COLOR_HEADER, dash=(2, 4))
            canvas.create_text(x_g, margin_t + plot_h + 4, text=f"{v_g:,.0f}", anchor="n",
                                fill=self.TEXT_COLOR, font=("Arial", 7))

        for i, (etichetta, valore) in enumerate(bars_data):
            cy = margin_t + i * bar_step + bar_step / 2
            y0, y1 = int(cy - bar_h / 2), int(cy + bar_h / 2)
            x0 = margin_l
            x1 = margin_l + max(2, int(plot_w * valore / mx))
            col = _PALETTE_GRAFICO[i % len(_PALETTE_GRAFICO)]
            canvas.create_rectangle(x0, y0, x1, y1, fill=col, outline="")
            lbl = etichetta if len(etichetta) <= 25 else etichetta[:24] + "…"
            canvas.create_text(margin_l - 6, int(cy), text=lbl, anchor="e", fill=self.TEXT_COLOR, font=("Arial", 8))
            canvas.create_text(x1 + 5, int(cy), text=f"€ {valore:,.2f}", anchor="w",
                                fill=self.TEXT_COLOR, font=("Arial", 8, "bold"))

    canvas.bind("<Configure>", _disegna)
    popup.after(100, _disegna)

def _veicoli_estratto(self, db, nb, v_fmese=None, v_fanno=None):
    idx = nb.index(nb.select())
    if idx < 0 or idx >= len(db["veicoli"]):
        self.show_toast("Nessun veicolo selezionato.")
        return
    v = db["veicoli"][idx]
    nome = v.get("nome", "Veicolo")
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

    movimenti = sorted([m for m in v.get("movimenti", []) if _match(m.get("data", ""))], key=lambda x: x.get("data", ""))
    periodo_str = ""
    if mese_sel != "Tutti" or anno_sel != "Tutti":
        periodo_str = f"  Periodo: {mese_sel if mese_sel != 'Tutti' else '--'}/{anno_sel if anno_sel != 'Tutti' else '----'}"

    LARGHEZZA_DOC = 90
    linea_doppia = "═" * LARGHEZZA_DOC
    linea_singola = "─" * LARGHEZZA_DOC
    lines = [
        linea_doppia,
        "Gestione Veicoli".center(LARGHEZZA_DOC),
        f"Estratto Conto: {nome.upper()}".center(LARGHEZZA_DOC),
    ]
    if periodo_str:
        lines.append(periodo_str.center(LARGHEZZA_DOC))

    testo_bollo, _c1 = self._veicoli_testo_scadenza(v.get("scad_bollo", ""))
    testo_ass, _c2 = self._veicoli_testo_scadenza(v.get("scad_assicurazione", ""))
    testo_rev, _c3 = self._veicoli_testo_scadenza(v.get("scad_revisione", ""))
    costo_km = self._veicoli_costo_al_km(v)
    consumo = self._veicoli_consumo_medio(v)

    lines += [
        linea_doppia, "",
        "  Informazione Veicolo",
        "  ─────────────────────",
        f"  Modello   : {v.get('modello', '─'):<26} Targa      : {v.get('targa', '─'):<26}",
        f"  Km Attuali: {v.get('km_attuali', 0):,.0f}{'':<15} Km Iniziali: {v.get('km_iniziale', 0):,.0f}",
        f"  Bollo     : {testo_bollo:<40} Assicurazione: {testo_ass}",
        f"  Revisione : {testo_rev}",
        f"  Costo medio al km : {'€ ' + format(costo_km, ',.3f') if costo_km else '—'}",
        f"  Consumo medio     : {'%.1f L/100km' % consumo if consumo else '—'}",
        f"  Note      : {v.get('note', '-'):<66}",
        "",
        linea_doppia,
        f"  {'DATA':<12} {'CATEGORIA':<22} {'KM':>10} {'IMPORTO':>12}   {'DESCRIZIONE'}",
        linea_singola,
    ]
    tot = 0.0
    for m in movimenti:
        try:
            imp = float(m.get("importo", 0))
        except (ValueError, TypeError):
            imp = 0.0
        tot += imp
        cat_pulita = m.get("categoria", "")
        if len(cat_pulita) > 22:
            cat_pulita = cat_pulita[:19] + "..."
        km_txt = f"{float(m['km']):,.0f}" if str(m.get("km", "")).strip() not in ("", "0") else "—"
        lines.append(f"  {m.get('data', ''):<12} {cat_pulita:<22} {km_txt:>10} {imp:>11.2f}€   {m.get('descrizione', '')}")

    lines += [
        linea_singola, "",
        "Riepilogo Finanziario".rjust(70),
        "─────────────────────".rjust(70),
        f"Totale Spesa: {tot:>15.2f} €".rjust(70),
        "",
        linea_doppia,
        f"Documento generato il {datetime.date.today().strftime('%d-%m-%Y')}".center(LARGHEZZA_DOC),
        linea_doppia,
    ]
    contenuto = "\n".join(lines)
    now = datetime.date.today()
    fname = f"Estratto_{nome}_{now.strftime('%d-%m-%Y')}"
    self.show_export_preview(contenuto, default_filename=fname)


def _veicoli_estratto_totale(self, db, v_fmese=None, v_fanno=None):
    if "veicoli" not in db or not db["veicoli"]:
        self.show_toast("Nessun veicolo presente nel database.")
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
    for v in db["veicoli"]:
        nome_v = v.get("nome", "Veicolo")
        for m in v.get("movimenti", []):
            if _match(m.get("data", "")):
                mc = m.copy()
                mc["_nome_veicolo"] = nome_v
                tutti_i_movimenti.append(mc)
    tutti_i_movimenti.sort(key=lambda x: x.get("data", ""))

    periodo_str = ""
    if mese_sel != "Tutti" or anno_sel != "Tutti":
        periodo_str = f"  Periodo: {mese_sel if mese_sel != 'Tutti' else '--'}/{anno_sel if anno_sel != 'Tutti' else '----'}"

    linea_doppia = "═" * 110
    linea_singola = "─" * 110
    lines = [
        linea_doppia,
        "  Gestione Veicoli  ".center(110),
        "  Estratto conto generale e cumulativo".center(110),
    ]
    if periodo_str:
        lines.append(periodo_str.center(110))
    lines += [linea_doppia, "", "  Riepilogo parco veicoli:", "  ────────────────────────"]
    for v in db["veicoli"]:
        costo_km = self._veicoli_costo_al_km(v)
        lines.append(
            f"  • {v.get('nome', 'Veicolo'):<25} (Targa: {v.get('targa', '─'):<12}) "
            f"Costo/km: {'€ ' + format(costo_km, ',.3f') if costo_km else '—'}"
        )
    lines += [
        "", linea_doppia,
        f"  {'DATA':<12} {'VEICOLO':<16} {'CATEGORIA':<24} {'IMPORTO':>12}   {'DESCRIZIONE'}",
        linea_singola,
    ]
    tot = 0.0
    for m in tutti_i_movimenti:
        try:
            imp = float(m.get("importo", 0))
        except (ValueError, TypeError):
            imp = 0.0
        tot += imp
        cat_pula = m.get("categoria", "")
        if len(cat_pula) > 22:
            cat_pula = cat_pula[:19] + "..."
        nome_v_pulito = m.get("_nome_veicolo", "")
        if len(nome_v_pulito) > 14:
            nome_v_pulito = nome_v_pulito[:11] + "..."
        lines.append(f"  {m.get('data', ''):<12} {nome_v_pulito:<16} {cat_pula:<24} {imp:>11.2f}€   {m.get('descrizione', '')}")

    lines += [
        linea_singola, "",
        "  Bilancio Globale Complessivo".rjust(100),
        "  ────────────────────────────".rjust(100),
        f"  Spesa Totale Generale: {tot:>15.2f} €".rjust(100),
        "", linea_doppia,
        f"  Documento complessivo generato il {datetime.date.today().strftime('%d-%m-%Y')}".center(110),
        linea_doppia,
    ]
    contenuto = "\n".join(lines)
    now = datetime.date.today()
    fname = f"Estratto_Generale_Veicoli_{now.strftime('%d-%m-%Y')}"
    self.show_export_preview(contenuto, default_filename=fname)
