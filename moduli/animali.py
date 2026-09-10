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

def _fmt_it(v, spec=",.2f"):
    s = format(v, spec)
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


CATEGORIE_ANIMALE_DEFAULT = [
    "Alimentazione",
    "Veterinario",
    "Vaccinazioni",
    "Antiparassitari",
    "Toelettatura",
    "Farmaci",
    "Accessori",
    "Pensione/Dog-sitter",
    "Assicurazione",
    "Varie",
]

LIMITE_MAX_ANIMALI = 7

_PALETTE_GRAFICO = ["#61AFEF", "#98C379", "#E06C75", "#E5C07B", "#C678DD", "#56B6C2", "#D19A66"]
_COL_VERDE  = "#98C379"
_COL_ROSSO  = "#E06C75"
_COL_AMBRA  = "#E5C07B"

def _animali_carica(self):
    import __main__ as _app
    ANIMALI_FILE = _app.ANIMALI_FILE
    if os.path.exists(ANIMALI_FILE):
        try:
            with open(ANIMALI_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"animali": []}

def _animali_salva(self, db):
    import __main__ as _app
    ANIMALI_FILE = _app.ANIMALI_FILE
    DB_DIR = _app.DB_DIR
    try:
        os.makedirs(DB_DIR, exist_ok=True)
        with open(ANIMALI_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
    except Exception as e:
        self.show_toast(f"Errore salvataggio Animali: {e}")

def _animali_giorni_a_scadenza(self, data_str):
    if not data_str:
        return None
    try:
        d = datetime.datetime.strptime(data_str, "%d-%m-%Y").date()
    except ValueError:
        return None
    return (d - datetime.date.today()).days

def _animali_colore_giorni(self, giorni, soglia_rossa=15, soglia_ambra=45):
    if giorni is None:
        return None
    if giorni <= soglia_rossa:
        return _COL_ROSSO
    if giorni <= soglia_ambra:
        return _COL_AMBRA
    return _COL_VERDE

def _animali_testo_scadenza(self, data_str):
    giorni = self._animali_giorni_a_scadenza(data_str)
    if giorni is None:
        return "Non impostata", None
    if giorni < 0:
        return f"SCADUTA da {abs(giorni)} gg  ({data_str})", _COL_ROSSO
    if giorni == 0:
        return f"Scade OGGI  ({data_str})", _COL_ROSSO
    return f"tra {giorni} gg  ({data_str})", self._animali_colore_giorni(giorni)

def _animali_costo_medio_mensile(self, a):
    data_str = a.get("data_nascita", "")
    try:
        d = datetime.datetime.strptime(data_str, "%d-%m-%Y").date()
    except (ValueError, TypeError):
        return None
    giorni = (datetime.date.today() - d).days
    if giorni <= 0:
        return None
    mesi = giorni / 30.44
    if mesi <= 0:
        return None
    totale = sum(float(m.get("importo", 0) or 0) for m in a.get("movimenti", []))
    return totale / mesi

def _animali_consumo_medio_cibo(self, a):

    rifornimenti = [
        m for m in a.get("movimenti", [])
        if m.get("categoria") == "Alimentazione"
        and len(m.get("data", "")) == 10
        and str(m.get("quantita_cibo", "")).strip() not in ("", "0")
    ]
    if len(rifornimenti) < 2:
        return None
    try:
        rifornimenti = sorted(
            rifornimenti,
            key=lambda m: datetime.datetime.strptime(m["data"], "%d-%m-%Y")
        )
    except (ValueError, TypeError):
        return None
    valori = []
    for prec, succ in zip(rifornimenti, rifornimenti[1:]):
        try:
            d_prec = datetime.datetime.strptime(prec["data"], "%d-%m-%Y").date()
            d_succ = datetime.datetime.strptime(succ["data"], "%d-%m-%Y").date()
            delta_giorni = (d_succ - d_prec).days
            quantita = float(succ["quantita_cibo"])
        except (ValueError, TypeError):
            continue
        if delta_giorni > 0 and quantita > 0:
            valori.append(quantita / delta_giorni * 30.44)
    if not valori:
        return None
    return sum(valori) / len(valori)

def _animali_importa_da_spese(self, db, win, nb):
    if not db.get("animali"):
        self.show_toast("Crea prima almeno un animale.")
        return

    candidate = []
    for data_key, lista in self.spese.items():
        for entry in lista:
            if getattr(entry, "tipo", "") != "Uscita":
                continue
            gia_importata = "#animali" in getattr(entry, "hashtag", [])
            candidate.append((data_key, entry, gia_importata))
    candidate.sort(key=lambda t: t[0], reverse=True)

    popup = tk.Toplevel(win, bg=self.COLOR_TOPLEVEL)
    popup.title("Importa spese in Animali")
    popup.transient(win)
    popup.withdraw()
    win.update_idletasks()
    W, H = 1000, 560
    x = win.winfo_rootx() + (win.winfo_width() // 2) - (W // 2)
    y = win.winfo_rooty() + (win.winfo_height() // 2) - (H // 2)
    popup.geometry(f"{W}x{H}+{max(0,x)}+{max(0,y)}")
    popup.deiconify()
    popup.lift()
    popup.focus_force()
    popup.bind("<Escape>", lambda e: popup.destroy())

    top_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    top_f.pack(fill=tk.X, padx=10, pady=(10, 4))
    tk.Label(top_f, text="Animale destinazione:", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 6))
    nomi_a = [x.get("nome", "Animale") for x in db["animali"]]
    a_dest = tk.StringVar(value=nomi_a[0])
    cb_dest = ttk.Combobox(top_f, textvariable=a_dest, values=nomi_a,
                           state="readonly", style="Border.TCombobox", width=20)
    cb_dest.pack(side=tk.LEFT, padx=(0, 12))

    tk.Label(top_f, text="Categoria animale:", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 6))
    a_catdest = tk.StringVar()
    cb_catdest = ttk.Combobox(top_f, textvariable=a_catdest, state="readonly",
                              style="Border.TCombobox", width=18)
    cb_catdest.pack(side=tk.LEFT)

    def _aggiorna_catdest(*_a):
        animale_sel = next((x for x in db["animali"] if x.get("nome") == a_dest.get()), None)
        cat_a_dest = (animale_sel or {}).get("categorie") or list(CATEGORIE_ANIMALE_DEFAULT)
        cb_catdest["values"] = cat_a_dest
        if cat_a_dest:
            a_catdest.set(cat_a_dest[0])
    cb_dest.bind("<<ComboboxSelected>>", _aggiorna_catdest)
    _aggiorna_catdest()

    filtro_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    filtro_f.pack(fill=tk.X, padx=10, pady=(4, 0))
    tk.Label(filtro_f, text="Filtra per categoria spesa originale:", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 6))
    cats_presenti = sorted({e.categoria for _, e, _ in candidate}, key=str.lower)
    v_catf = tk.StringVar(value="Tutte")
    cb_catf = ttk.Combobox(filtro_f, textvariable=v_catf, values=["Tutte"] + cats_presenti,
                           state="readonly", style="Border.TCombobox", width=18)
    cb_catf.pack(side=tk.LEFT, padx=(0, 12))

    tk.Label(filtro_f, text="Mese:", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 6))
    mesi_presenti = sorted({data_key.strftime("%m") for data_key, _, _ in candidate})
    v_mesef = tk.StringVar(value="Tutti")
    cb_mesef = ttk.Combobox(filtro_f, textvariable=v_mesef, values=["Tutti"] + mesi_presenti,
                            state="readonly", style="Border.TCombobox", width=6)
    cb_mesef.pack(side=tk.LEFT, padx=(0, 12))

    tk.Label(filtro_f, text="Anno:", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 6))
    anni_presenti = sorted({data_key.strftime("%Y") for data_key, _, _ in candidate})
    v_annof = tk.StringVar(value="Tutti")
    cb_annof = ttk.Combobox(filtro_f, textvariable=v_annof, values=["Tutti"] + anni_presenti,
                            state="readonly", style="Border.TCombobox", width=8)
    cb_annof.pack(side=tk.LEFT, padx=(0, 12))

    v_nascondi = tk.BooleanVar(value=False)
    chk_nascondi = ttk.Checkbutton(filtro_f, text="Nascondi già importate", variable=v_nascondi)
    chk_nascondi.pack(side=tk.LEFT)

    cols = ("Data", "Categoria originale", "Descrizione", "Importo", "Stato")
    tree_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    tree_f.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)
    tree = ttk.Treeview(tree_f, columns=cols, show="headings", selectmode="extended")
    vsb = ttk.Scrollbar(tree_f, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(fill=tk.BOTH, expand=True)
    wcfg = {"Data": (90, "w"), "Categoria originale": (150, "w"),
            "Descrizione": (240, "w"), "Importo": (90, "e"), "Stato": (110, "center")}
    for c in cols:
        w, anc = wcfg[c]
        tree.heading(c, text=c, command=lambda _c=c: self.treeview_sort_column(tree, _c, False))
        tree.column(c, width=w, anchor=anc)
    tree.tag_configure("gia_importata", foreground="#888888")

    riga_map = {}

    def _popola():
        tree.delete(*tree.get_children())
        riga_map.clear()
        fc = v_catf.get()
        fm = v_mesef.get()
        fa = v_annof.get()
        nascondi = v_nascondi.get()
        for i, (data_key, entry, gia_importata) in enumerate(candidate):
            if fc != "Tutte" and entry.categoria != fc:
                continue
            if fm != "Tutti" and data_key.strftime("%m") != fm:
                continue
            if fa != "Tutti" and data_key.strftime("%Y") != fa:
                continue
            if nascondi and gia_importata:
                continue
            iid = str(i)
            riga_map[iid] = (data_key, entry, gia_importata)
            stato_txt = "✔ Importata" if gia_importata else "Da importare"
            tags = ("gia_importata",) if gia_importata else ()
            tree.insert("", "end", iid=iid, tags=tags, values=(
                data_key.strftime("%d-%m-%Y"), entry.categoria,
                entry.descrizione, f"{_fmt_it(entry.importo)} €", stato_txt
            ))
    cb_catf.bind("<<ComboboxSelected>>", lambda e: _popola())
    cb_mesef.bind("<<ComboboxSelected>>", lambda e: _popola())
    cb_annof.bind("<<ComboboxSelected>>", lambda e: _popola())
    chk_nascondi.configure(command=_popola)
    _popola()

    def _importa():
        sel = tree.selection()
        if not sel:
            self.show_toast("Seleziona almeno una spesa da importare.")
            return
        gia_sel = [riga_map[iid] for iid in sel if riga_map.get(iid, (None, None, False))[2]]
        sel_valide = [iid for iid in sel if not riga_map.get(iid, (None, None, False))[2]]
        if not sel_valide:
            self.show_toast("Le spese selezionate risultano già importate.")
            return
        animale = next((x for x in db["animali"] if x.get("nome") == a_dest.get()), None)
        if animale is None:
            self.show_toast("Animale non trovato.")
            return
        cat_dest = a_catdest.get().strip()
        if not cat_dest:
            self.show_toast("Seleziona una categoria di destinazione.")
            return
        n = 0
        for iid in sel_valide:
            data_key, entry, _ = riga_map.get(iid, (None, None, False))
            if entry is None:
                continue
            nuovo_mov = {
                "id": str(uuid.uuid4()),
                "data": data_key.strftime("%d-%m-%Y"),
                "categoria": cat_dest,
                "peso": "", "quantita_cibo": "",
                "importo": entry.importo,
                "descrizione": entry.descrizione,
            }
            animale.setdefault("movimenti", []).append(nuovo_mov)
            entry.hashtag = list(getattr(entry, "hashtag", [])) + ["#animali"]
            n += 1
        self._animali_salva(db)
        self.save_db()
        self.refresh_gui()

        nome_dest = animale.get("nome")
        for tab_id in list(nb.tabs()):
            nb.forget(tab_id)
        for aa in db["animali"]:
            self._animali_crea_tab(nb, aa, db, win)
        for i, aa in enumerate(db["animali"]):
            if aa.get("nome") == nome_dest:
                nb.select(i)
                break

        msg = f"Importate {n} spese in {animale.get('nome')} (categoria: {cat_dest})."
        if gia_sel:
            msg += f" {len(gia_sel)} già importate saltate."
        self.show_toast(msg)
        popup.destroy()

    btn_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    btn_f.pack(fill=tk.X, padx=10, pady=(0, 10))
    img_imp = self.icone_gui.get("aggiungi")
    b_imp = ttk.Label(btn_f, compound="left", image=img_imp,
                      text=" Importa selezionate" if img_imp else "📥 Importa selezionate",
                      background=self.COLOR_TOPLEVEL, foreground=self.TEXT_COLOR, cursor="hand2")
    b_imp.image = img_imp
    b_imp.pack(side=tk.LEFT, padx=4)
    b_imp.bind("<Button-1>", lambda e: _importa())
    img_ch = self.icone_gui.get("chiudi")
    b_ch = ttk.Label(btn_f, compound="left", image=img_ch,
                     text=" Chiudi" if img_ch else "Chiudi",
                     background=self.COLOR_TOPLEVEL, foreground=self.TEXT_COLOR, cursor="hand2")
    b_ch.image = img_ch
    b_ch.pack(side=tk.LEFT, padx=4)
    b_ch.bind("<Button-1>", lambda e: popup.destroy())

    if not candidate:
        tk.Label(popup, text="Nessuna spesa da importare: tutte le spese sono già collegate,\n"
                             "oppure non ci sono ancora spese registrate.",
                bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR, font=("Arial", 10)).pack(pady=20)

def animali(self):
    if hasattr(self, "_animali_win") and self._animali_win and self._animali_win.winfo_exists():
        self._animali_win.lift()
        self._animali_win.focus_force()
        return
    db = self._animali_carica()
    win = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    win.title("Animali — Gestione Anagrafica e Spese")
    self._animali_win = win
    win.bind("<Destroy>", lambda e: setattr(self, "_animali_win", None) if e.widget is win else None)
    win.bind("<Escape>", lambda e: win.destroy())
    win.withdraw()
    win.update_idletasks()
    W, H = 1300, 630
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (W // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (H // 2)
    win.geometry(f"{W}x{H}+{max(0,x)}+{max(0,y)}")
    win.minsize(W, H)
    win.transient(self)
    win.deiconify()
    win.lift()
    win.focus_force()

    toolbar = tk.Frame(win, bg=self.COLOR_WIDGET_BG, pady=4)
    toolbar.pack(fill=tk.X, padx=8, pady=(4, 0))

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

    _btn(toolbar, " Nuovo Animale",   lambda: self._animali_nuovo(db, nb, win),   "animali")
    _btn(toolbar, " Elimina Animale", lambda: self._animali_elimina(db, nb, win), "delete")
    _btn(toolbar, " Grafici",         lambda: self._animali_grafici(db),          "report")
    _btn(toolbar, " Importa da Spese", lambda: self._animali_importa_da_spese(db, win, nb), "aggiungi")

    def _get_vars():
        try:
            idx = nb.index(nb.select())
            return getattr(self, "_animali_vars", {}).get(idx, (None, None))
        except Exception:
            return (None, None)

    _btn(toolbar, " Estratto Animale",        lambda: self._animali_estratto(db, nb, *_get_vars()),        "descrizione")
    _btn(toolbar, " Estratto Tutti gli Animali", lambda: self._animali_estratto_totale(db, *_get_vars()),  "report")
    _btn(toolbar, " Salva",           lambda: (self._animali_salva(db), self.show_toast("Animali salvati.")), "salva")
    _btn(toolbar, " Chiudi",          lambda: win.destroy(),                       "chiudi")

    nb = ttk.Notebook(win)
    nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

    if not db["animali"]:
        ph = ttk.Frame(nb)
        img_ph = self.icone_gui.get("animali")
        if img_ph:
            nb.add(ph, image=img_ph, text="  (nessun animale)  ", compound="left")
        else:
            nb.add(ph, text="  (nessun animale)  ")
        tk.Label(
            ph, text="Clicca '🐾 Nuovo Animale' per iniziare",
            font=("Arial", 12), bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER
        ).pack(expand=True)
    else:
        for a in db["animali"]:
            self._animali_crea_tab(nb, a, db, win)

def _animali_crea_tab(self, nb, a, db, win):
    tab = ttk.Frame(nb)
    img_tab_animale = self.icone_gui.get("animali")
    if img_tab_animale:
        nb.add(tab, image=img_tab_animale, text=f"  {a.get('nome','Animale')}  ", compound="left")
    else:
        nb.add(tab, text=f"  🐾 {a.get('nome','Animale')}  ")

    ana_lf = ttk.LabelFrame(tab, text="Anagrafica", style="RedBold.TLabelframe")
    ana_lf.pack(fill=tk.X, padx=8, pady=(4, 2))

    righe_campi = [
        [("Nome", "nome", 16), ("Razza/Specie", "razza", 22), ("Microchip", "microchip", 16)],
        [("Peso Iniziale (kg)", "peso_iniziale", 10), ("Peso Attuale (kg)", "peso_attuale", 10), ("Data di Nascita", "data_nascita", 12)],
        [("Prossimo Controllo", "prossimo_controllo", 12), ("Note", "note", 40), ("Conto Bancario", "conto_bancario", 20)],
    ]
    vars_ana = {}
    widgets_combo_ana = {}
    campi_data = ("data_nascita", "prossimo_controllo")
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
            val = a.get(chiave, "")
            vv = tk.StringVar(value=str(val))
            vars_ana[chiave] = vv
            if chiave in campi_data:
                frm_data_camp = tk.Frame(ana_lf, bg=self.COLOR_WIDGET_BG)
                frm_data_camp.grid(row=r_idx, column=col * 2 + 1, sticky="ew", padx=(0, 8), pady=2)
                ent_data_camp = ttk.Entry(frm_data_camp, textvariable=vv, width=w, style="TEntry")
                ent_data_camp.pack(side=tk.LEFT)
                btn_cal_camp = ttk.Label(frm_data_camp, image=self.icone_gui.get("calendario"),
                                        background=self.COLOR_WIDGET_BG, cursor="hand2")
                btn_cal_camp.image = self.icone_gui.get("calendario")
                btn_cal_camp.pack(side=tk.LEFT, padx=(4, 0))
                btn_cal_camp.bind("<Button-1>", lambda e, ent=ent_data_camp, vv=vv: self.mostra_calendario_popup_semplice(ent, vv))
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
            if chiave in ("peso_iniziale", "peso_attuale"):
                try:
                    a[chiave] = float(val.replace(",", "."))
                except ValueError:
                    a[chiave] = 0.0
            else:
                a[chiave] = val
        idx = nb.index(nb.select())
        nb.tab(idx, text=f"  {a.get('nome','Animale')}  ")
        self._animali_salva(db)
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

    stato_lf = ttk.LabelFrame(tab, text="Scadenze e Indicatori", style="RedBold.TLabelframe")
    stato_lf.pack(fill=tk.X, padx=8, pady=(0, 2))
    stato_lf.columnconfigure(2, weight=1)
    campi_scad = [("Vaccinazioni", "scad_vaccino"), ("Antiparassitario", "scad_antiparassitario"), ("Assicurazione", "scad_assicurazione")]
    lbl_scad = {}
    vars_scad = {}
    for riga_idx, (etichetta, chiave) in enumerate(campi_scad):
        tk.Label(stato_lf, text=etichetta + ":", bg=self.COLOR_WIDGET_BG,
                 fg=self.COLOR_HEADER, font=("Arial", 9, "bold"), width=13, anchor="w").grid(
            row=riga_idx, column=0, sticky="w", padx=(8, 2), pady=2)
        vv = tk.StringVar(value=str(a.get(chiave, "")))
        vars_scad[chiave] = vv
        frm_data_box = tk.Frame(stato_lf, bg=self.COLOR_WIDGET_BG)
        frm_data_box.grid(row=riga_idx, column=1, sticky="w", padx=(0, 2), pady=2)
        ent = ttk.Entry(frm_data_box, textvariable=vv, width=11)
        ent.pack(side=tk.LEFT)
        btn_cal = ttk.Label(frm_data_box, image=self.icone_gui.get("calendario"),
                             background=self.COLOR_WIDGET_BG, cursor="hand2")
        btn_cal.image = self.icone_gui.get("calendario")
        btn_cal.pack(side=tk.LEFT, padx=(4, 0))
        btn_cal.bind("<Button-1>", lambda e, ent=ent, vv=vv: self.mostra_calendario_popup_semplice(ent, vv))
        lbl = tk.Label(stato_lf, text="—", bg=self.COLOR_WIDGET_BG,
                        fg=self.TEXT_COLOR, font=("Arial", 9, "bold"), anchor="w")
        lbl.grid(row=riga_idx, column=2, sticky="w", padx=(6, 14), pady=2)
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
            a[chiave] = val
        self._animali_salva(db)
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
    riga2_lf.grid(row=3, column=0, columnspan=4, sticky="ew", padx=8, pady=(0, 2))
    lbl_controllo = tk.Label(riga2_lf, text="—", bg=self.COLOR_WIDGET_BG,
                              fg=self.TEXT_COLOR, font=("Arial", 9, "bold"))
    lbl_controllo.pack(side=tk.LEFT, padx=(0, 20))
    lbl_costo_mese = tk.Label(riga2_lf, text="—", bg=self.COLOR_WIDGET_BG,
                             fg=self.COLOR_HEADER, font=("Arial", 9, "bold"))
    lbl_costo_mese.pack(side=tk.LEFT, padx=(0, 20))
    lbl_consumo_cibo = tk.Label(riga2_lf, text="—", bg=self.COLOR_WIDGET_BG,
                            fg=self.COLOR_HEADER, font=("Arial", 9, "bold"))
    lbl_consumo_cibo.pack(side=tk.LEFT)

    def _aggiorna_pannello_stato():
        for _et, chiave in campi_scad:
            testo, colore = self._animali_testo_scadenza(a.get(chiave, ""))
            lbl_scad[chiave].config(text=testo, fg=colore or self.TEXT_COLOR)
        testo_c, colore_c = self._animali_testo_scadenza(a.get("prossimo_controllo", ""))
        lbl_controllo.config(text=f"Prossimo controllo: {testo_c}", fg=colore_c or self.TEXT_COLOR)
        costo_mese = self._animali_costo_medio_mensile(a)
        lbl_costo_mese.config(text=f"Costo medio: € {_fmt_it(costo_mese)}/mese" if costo_mese else "Costo medio: —")
        consumo = self._animali_consumo_medio_cibo(a)
        lbl_consumo_cibo.config(text=f"Consumo cibo: {consumo:.2f} kg/mese" if consumo else "Consumo cibo: —")

    main_container = tk.Frame(tab, bg=self.COLOR_WIDGET_BG)
    main_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 2))

    form_lf = ttk.LabelFrame(main_container, text="Registra Movimento", style="RedBold.TLabelframe", width=280)
    form_lf.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
    form_lf.columnconfigure(1, weight=1)

    cat_a = a.setdefault("categorie", list(CATEGORIE_ANIMALE_DEFAULT))

    r = 0
    tk.Label(form_lf, text="Data:", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
             font=("Arial", 9, "bold")).grid(row=r, column=0, sticky="w", padx=6, pady=2)
    v_data = tk.StringVar(value=datetime.date.today().strftime("%d-%m-%Y"))
    frm_data_box = tk.Frame(form_lf, bg=self.COLOR_WIDGET_BG)
    frm_data_box.grid(row=r, column=1, sticky="ew", padx=6, pady=2)
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
             font=("Arial", 9, "bold")).grid(row=r, column=0, sticky="w", padx=6, pady=2)
    v_cat = tk.StringVar(value=cat_a[0] if cat_a else "Varie")
    cb_cat = ttk.Combobox(form_lf, textvariable=v_cat, values=cat_a, width=25, style="Border.TCombobox", state="readonly")
    cb_cat.grid(row=r, column=1, sticky="ew", padx=6, pady=2)
    r += 1

    tk.Label(form_lf, text="Peso (kg):", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
             font=("Arial", 9, "bold")).grid(row=r, column=0, sticky="w", padx=6, pady=2)
    v_peso = tk.StringVar()
    ttk.Entry(form_lf, textvariable=v_peso, width=12).grid(row=r, column=1, sticky="ew", padx=6, pady=2)
    r += 1

    tk.Label(form_lf, text="Quantità Cibo kg (solo Alimentazione):", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
             font=("Arial", 9, "bold")).grid(row=r, column=0, sticky="w", padx=6, pady=2)
    v_quantita = tk.StringVar()
    ttk.Entry(form_lf, textvariable=v_quantita, width=10).grid(row=r, column=1, sticky="ew", padx=6, pady=2)
    r += 1

    tk.Label(form_lf, text="Descrizione:", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
             font=("Arial", 9, "bold")).grid(row=r, column=0, sticky="w", padx=6, pady=2)
    v_desc = tk.StringVar()
    ent_desc = ttk.Entry(form_lf, textvariable=v_desc, width=22)
    ent_desc.grid(row=r, column=1, sticky="ew", padx=6, pady=2)
    r += 1

    tk.Label(form_lf, text="Importo €:", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
             font=("Arial", 9, "bold")).grid(row=r, column=0, sticky="w", padx=6, pady=2)
    v_imp = tk.StringVar()

    def limita_importo(*a_):
        testo = "".join(c for c in v_imp.get() if c.isdigit() or c == ".")
        punti = [i for i, c in enumerate(testo) if c == "."]
        if len(punti) > 1:
            idx_valido = punti[0]
            testo = "".join(c for i, c in enumerate(testo) if c.isdigit() or i == idx_valido)
        if v_imp.get() != testo:
            v_imp.set(testo)
    v_imp.trace_add("write", limita_importo)
    ent_imp = ttk.Entry(form_lf, textvariable=v_imp, width=12)
    ent_imp.grid(row=r, column=1, sticky="ew", padx=6, pady=2)
    ent_imp.bind("<Return>", lambda e: _aggiungi())
    r += 1

    cat_frame = tk.Frame(form_lf, bg=self.COLOR_WIDGET_BG)
    cat_frame.grid(row=r, column=0, columnspan=2, sticky="ew", padx=6, pady=(4, 2))
    r += 1
    tk.Label(cat_frame, text="Categorie:", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
             font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
    v_nuova_cat = tk.StringVar()
    def _limita_cat(*a_):
        if len(v_nuova_cat.get()) > 22:
            v_nuova_cat.set(v_nuova_cat.get()[:22])
    v_nuova_cat.trace_add("write", _limita_cat)
    ttk.Entry(cat_frame, textvariable=v_nuova_cat, width=22).pack(side=tk.LEFT, padx=(0, 4))

    def _aggiungi_cat():
        nc = v_nuova_cat.get().strip()
        if nc and nc not in cat_a:
            cat_a.append(nc)
            cat_a.sort(key=str.lower)
            cb_cat["values"] = cat_a
            cb_fcat["values"] = ["Tutte"] + sorted(cat_a, key=str.lower)
            v_cat.set(nc)
            self._animali_salva(db)
            v_nuova_cat.set("")
            self.show_toast(f"Categoria '{nc}' aggiunta.")

    def _rimuovi_cat():
        sel = v_cat.get()
        if sel in cat_a and len(cat_a) > 1:
            cat_a.remove(sel)
            cb_cat["values"] = cat_a
            cb_fcat["values"] = ["Tutte"] + sorted(cat_a, key=str.lower)
            v_cat.set(cat_a[0])
            self._animali_salva(db)

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
    btn_frame.grid(row=r, column=0, columnspan=2, pady=4)

    tree_lf = ttk.LabelFrame(main_container, text="Movimenti", style="RedBold.TLabelframe")
    tree_lf.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(6, 0), pady=2)

    filtri_tree_f = tk.Frame(tree_lf, bg=self.COLOR_WIDGET_BG)
    filtri_tree_f.pack(fill=tk.X, padx=4, pady=(4, 0))
    tk.Label(filtri_tree_f, text="Categoria:", bg=self.COLOR_WIDGET_BG,
             fg=self.COLOR_HEADER, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
    v_fcat = tk.StringVar(value="Tutte")
    cb_fcat = ttk.Combobox(filtri_tree_f, textvariable=v_fcat, values=["Tutte"] + sorted(cat_a, key=str.lower),
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
    anni_f = sorted({m.get("data", "")[-4:] for m in a.get("movimenti", []) if len(m.get("data", "")) == 10}, reverse=True)
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

    def _tutti_filtri():
        v_fmese.set("Tutti")
        v_fanno.set("Tutti")
        _popola_tree()
        tutte = tree.get_children()
        if tutte:
            tree.selection_set(tutte)
            tree.see(tutte[0])

    btn_reset = tk.Label(filtri_tree_f, text="↺ Reset", bg=self.COLOR_WIDGET_BG,
                          fg=self.COLOR_HIGHLIGHT, font=("Arial", 8, "bold"), cursor="hand2")
    btn_reset.pack(side=tk.LEFT, padx=(4, 0))
    btn_reset.bind("<Button-1>", lambda e: _reset_filtri())

    btn_tutti = tk.Label(filtri_tree_f, text="∞ Tutti", bg=self.COLOR_WIDGET_BG,
                          fg=self.COLOR_HIGHLIGHT, font=("Arial", 8, "bold"), cursor="hand2")
    btn_tutti.pack(side=tk.LEFT, padx=(4, 0))
    btn_tutti.bind("<Button-1>", lambda e: _tutti_filtri())

    def _seleziona_da_esportare():
        da_esportare = [
            m["id"] for m in a.get("movimenti", [])
            if m["id"] in tree.get_children() and not m.get("esportato")
        ]
        if not da_esportare:
            self.show_toast("Nessuna voce da esportare tra quelle visualizzate.")
            return
        tree.selection_set(da_esportare)
        tree.see(da_esportare[0])

    btn_da_esportare = tk.Label(filtri_tree_f, text="📤 Da esportare", bg=self.COLOR_WIDGET_BG,
                                 fg=self.COLOR_HIGHLIGHT, font=("Arial", 8, "bold"), cursor="hand2")
    btn_da_esportare.pack(side=tk.LEFT, padx=(4, 0))
    btn_da_esportare.bind("<Button-1>", lambda e: _seleziona_da_esportare())

    def _smarca_esportato():
        sel = tree.selection()
        if not sel:
            sel = [
                m["id"] for m in a.get("movimenti", [])
                if m["id"] in tree.get_children() and m.get("esportato")
            ]
            if not sel:
                self.show_toast("Nessuna voce esportata tra quelle visualizzate.")
                return
            tree.selection_set(sel)
        n = 0
        for m in a.get("movimenti", []):
            if m.get("id") in sel and m.get("esportato"):
                m["esportato"] = None
                n += 1
        if n:
            self._animali_salva(db)
            _popola_tree()
            self.show_toast(f"{n} voce/i smarcata/e come non esportata.")
        else:
            self.show_toast("Le voci selezionate non risultano esportate.")

    btn_smarca = tk.Label(filtri_tree_f, text="↩ Smarca esportato", bg=self.COLOR_WIDGET_BG,
                           fg=self.COLOR_HIGHLIGHT, font=("Arial", 8, "bold"), cursor="hand2")
    btn_smarca.pack(side=tk.LEFT, padx=(4, 0))
    btn_smarca.bind("<Button-1>", lambda e: _smarca_esportato())

    if not hasattr(self, "_animali_vars"):
        self._animali_vars = {}
    tab_idx = nb.index("end") - 1 if nb.index("end") > 0 else 0
    self._animali_vars[tab_idx] = (v_fmese, v_fanno)

    tot_frame = tk.Frame(tree_lf, bg=self.COLOR_WIDGET_BG)
    tot_frame.pack(fill=tk.X, padx=4, pady=(4, 0))
    lbl_tot_periodo = tk.Label(tot_frame, text="Spesa periodo: € 0.00", bg=self.COLOR_WIDGET_BG,
                                fg=self.COLOR_RED, font=("Arial", 10, "bold"))
    lbl_tot_periodo.pack(side=tk.LEFT, padx=4)

    cols = ("Data", "Categoria", "Peso", "Descrizione", "Importo", "Esportato")
    tree_frame_inner = ttk.Frame(tree_lf)
    tree_frame_inner.pack(fill=tk.BOTH, expand=True, padx=4, pady=2)
    tree = ttk.Treeview(tree_frame_inner, columns=cols, show="headings", selectmode="extended")
    vsb = ttk.Scrollbar(tree_frame_inner, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(fill=tk.BOTH, expand=True)
    def _seleziona_tutte_righe(event=None):
        tree.selection_set(tree.get_children())
        return "break"
    tree.bind("<Control-a>", _seleziona_tutte_righe)
    wcfg = {"Data": (90, "w"), "Categoria": (140, "w"), "Peso": (80, "e"),
            "Descrizione": (200, "w"), "Importo": (90, "e"), "Esportato": (70, "center")}
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
        return [m for m in a.get("movimenti", [])
                if _match_f(m.get("data", "")) and (fc == "Tutte" or m.get("categoria", "") == fc)]

    def _popola_tree():
        anni_agg = sorted({m.get("data", "")[-4:] for m in a.get("movimenti", []) if len(m.get("data", "")) == 10}, reverse=True)
        cb_fanno["values"] = ["Tutti"] + anni_agg
        cb_fcat["values"] = ["Tutte"] + sorted(cat_a, key=str.lower)
        migrato = False
        for m in a.get("movimenti", []):
            if not m.get("id"):
                m["id"] = str(uuid.uuid4())
                migrato = True
            exp_id = m.get("esportato")
            if exp_id and exp_id is not True:
                tag = f"#aexp:{exp_id}"
                esiste = any(
                    tag in getattr(entry, "hashtag", [])
                    for lista in self.spese.values() for entry in lista
                )
                if not esiste:
                    m["esportato"] = None
                    migrato = True
        if migrato:
            self._animali_salva(db)
        tree.delete(*tree.get_children())
        vis = sorted(_movimenti_visibili(), key=lambda x: x.get("data", ""))
        for m in vis:
            try:
                val_float = float(m.get("importo", 0))
            except (ValueError, TypeError):
                val_float = 0.0
            peso_txt = f"{float(m['peso']):.1f}" if str(m.get("peso", "")).strip() not in ("", "0") else "—"
            tree.insert("", "end", iid=m["id"], tags=("spesa",), values=(
                m.get("data", ""), m.get("categoria", ""), peso_txt,
                m.get("descrizione", ""), f"{val_float:.2f} €",
                "Sì" if m.get("esportato") else "No"
            ))
        tot = sum(float(m.get("importo", 0) or 0) for m in vis)
        lbl_tot_periodo.config(text=f"Spesa periodo: € {_fmt_it(tot)}")
        _aggiorna_pannello_stato()

    riga_in_modifica = None

    def _carica_in_form():
        nonlocal riga_in_modifica
        sel = tree.selection()
        if not sel:
            self.show_toast("Seleziona un movimento da modificare.")
            return
        mid = sel[0]
        movimento = next((m for m in a.get("movimenti", []) if m.get("id") == mid), None)
        if not movimento:
            self.show_toast("Movimento non trovato.")
            return
        riga_in_modifica = movimento
        v_data.set(movimento.get("data", ""))
        v_cat.set(movimento.get("categoria", ""))
        v_peso.set(str(movimento.get("peso", "")))
        v_quantita.set(str(movimento.get("quantita_cibo", "")))
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
        peso_val = v_peso.get().strip().replace(",", ".")
        quantita_val = v_quantita.get().strip().replace(",", ".")
        try:
            peso_num = float(peso_val) if peso_val else ""
        except ValueError:
            peso_num = ""
        try:
            quantita_num = float(quantita_val) if quantita_val else ""
        except ValueError:
            quantita_num = ""
        if riga_in_modifica is not None:
            riga_in_modifica.update({
                "data": data, "categoria": cat, "peso": peso_num,
                "quantita_cibo": quantita_num, "importo": imp, "descrizione": desc
            })
            riga_in_modifica = None
            btn_add.config(text=" Aggiungi" if img_add else "➕ Aggiungi")
            self.show_toast("Movimento modificato.")
        else:
            a.setdefault("movimenti", []).append({
                "id": str(uuid.uuid4()), "data": data, "categoria": cat,
                "peso": peso_num, "quantita_cibo": quantita_num, "importo": imp, "descrizione": desc
            })
            self.show_toast("Movimento aggiunto.")
        if peso_num:
            a["peso_attuale"] = float(peso_num)
            vars_ana["peso_attuale"].set(str(peso_num))
        self._animali_salva(db)
        v_desc.set("")
        v_imp.set("")
        v_peso.set("")
        v_quantita.set("")
        _popola_tree()

    def _elimina_mov():
        sel = tree.selection()
        if not sel:
            return
        mid = sel[0]
        a["movimenti"] = [m for m in a.get("movimenti", []) if m.get("id") != mid]
        self._animali_salva(db)
        _popola_tree()

    def _esporta_in_spesedb():
        sel = tree.selection()
        if not sel:
            self.show_toast("Seleziona almeno una riga da esportare.")
            return
        movimenti_filtrati = [
            m for m in a.get("movimenti", [])
            if m.get("id") in sel and not m.get("esportato")
        ]
        if not movimenti_filtrati:
            self.show_toast("Le voci selezionate risultano già tutte esportate.")
            return
        tot = sum(float(m.get("importo", 0) or 0) for m in movimenti_filtrati)
        if tot == 0:
            self.show_toast("Saldo zero, nessun movimento esportato.")
            return
        nome = a.get("nome", "Animale")
        desc_export = f"Saldo {nome}" if len(movimenti_filtrati) <= 1 else f"Saldo {nome} ({len(movimenti_filtrati)} mov.)"
        cat_export = "PetCare"
        if cat_export not in self.categorie:
            self.categorie.append(cat_export)
            self.aggiorna_combobox_categorie()
        oggi = datetime.date.today()
        if oggi not in self.spese:
            self.spese[oggi] = []
        nome_conto = widgets_combo_ana["conto_bancario"].get().strip() if "conto_bancario" in widgets_combo_ana else a.get("conto_bancario", "")
        export_id = str(uuid.uuid4())
        self.spese[oggi].append(SpesaEntry.nuova(
            cat_export, desc_export, tot, "Uscita",
            conto=(nome_conto if nome_conto and nome_conto != "(nessuno)" else ""),
            hashtag=["#animali", f"#aexp:{export_id}"]
        ))
        for m in movimenti_filtrati:
            m["esportato"] = export_id
        self._animali_salva(db)
        self.save_db()
        if hasattr(self, 'registra_azione_gamification'):
            self.registra_azione_gamification("movimento")
        _popola_tree()
        self.refresh_gui()
        self.show_toast(f"Spesa {nome} ({_fmt_it(tot)}€, {len(movimenti_filtrati)} movimenti) esportata.")

    def _esporta_singole_in_spesedb():
        sel = tree.selection()
        if not sel:
            self.show_toast("Seleziona almeno una riga da esportare.")
            return
        movimenti_filtrati = [
            m for m in a.get("movimenti", [])
            if m.get("id") in sel and not m.get("esportato")
        ]
        if not movimenti_filtrati:
            self.show_toast("Le voci selezionate risultano già tutte esportate.")
            return
        nome = a.get("nome", "Animale")
        cat_export = "PetCare"
        if cat_export not in self.categorie:
            self.categorie.append(cat_export)
            self.aggiorna_combobox_categorie()
        nome_conto = widgets_combo_ana["conto_bancario"].get().strip() if "conto_bancario" in widgets_combo_ana else a.get("conto_bancario", "")
        oggi = datetime.date.today()
        if oggi not in self.spese:
            self.spese[oggi] = []
        n = 0
        for m in movimenti_filtrati:
            try:
                imp = float(m.get("importo", 0))
            except (ValueError, TypeError):
                imp = 0.0
            if imp == 0:
                continue
            cat_orig = m.get("categoria", "")
            desc_orig = m.get("descrizione", "")
            desc_export = f"{nome}: {cat_orig}" if cat_orig else nome
            if desc_orig:
                desc_export += f" - {desc_orig}"
            export_id = str(uuid.uuid4())
            self.spese[oggi].append(SpesaEntry.nuova(
                cat_export, desc_export, imp, "Uscita",
                conto=(nome_conto if nome_conto and nome_conto != "(nessuno)" else ""),
                hashtag=["#animali", f"#aexp:{export_id}"]
            ))
            m["esportato"] = export_id
            n += 1
        if n == 0:
            self.show_toast("Nessuna voce valida da esportare.")
            return
        self._animali_salva(db)
        self.save_db()
        if hasattr(self, 'registra_azione_gamification'):
            self.registra_azione_gamification("movimento")
        _popola_tree()
        self.refresh_gui()
        self.show_toast(f"{n} voce/i di {nome} esportate singolarmente.")

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
    btn_frame2.grid(row=r + 1, column=0, columnspan=2, pady=(0, 2))

    riga_export1 = tk.Frame(btn_frame2, bg=self.COLOR_WIDGET_BG)
    riga_export1.pack(fill=tk.X, anchor="w")
    img_export = self.icone_gui.get("archivia")
    btn_export = ttk.Label(
        riga_export1, compound="left", image=img_export,
        text=" → Saldo" if img_export else "📤 → Saldo",
        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2"
    )
    btn_export.image = img_export
    btn_export.pack(side=tk.LEFT, padx=4)
    btn_export.bind("<Button-1>", lambda e: _esporta_in_spesedb())
    tk.Label(riga_export1, text="(totale unico delle righe selezionate)",
             bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
             font=("Arial", 8, "italic")).pack(side=tk.LEFT, padx=(4, 0))

    riga_export2 = tk.Frame(btn_frame2, bg=self.COLOR_WIDGET_BG)
    riga_export2.pack(fill=tk.X, anchor="w", pady=(4, 0))
    img_export_righe = self.icone_gui.get("archivia")
    btn_export_righe = ttk.Label(
        riga_export2, compound="left", image=img_export_righe,
        text=" Esporta righe" if img_export_righe else "📤 Esporta righe",
        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2"
    )
    btn_export_righe.image = img_export_righe
    btn_export_righe.pack(side=tk.LEFT, padx=4)
    btn_export_righe.bind("<Button-1>", lambda e: _esporta_singole_in_spesedb())
    tk.Label(riga_export2, text="(una voce per riga, con categoria originale in descrizione)",
             bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
             font=("Arial", 8, "italic")).pack(side=tk.LEFT, padx=(4, 0))

    _popola_tree()

def _animali_nuovo(self, db, nb, win):
    popup = tk.Toplevel(win, bg=self.COLOR_TOPLEVEL)
    popup.title("Nuovo Animale")
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

    tk.Label(popup, text="Nome animale:", bg=self.COLOR_TOPLEVEL,
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
        if len(db.get("animali", [])) >= LIMITE_MAX_ANIMALI:
            self.show_toast(f"Limite raggiunto! Massimo {LIMITE_MAX_ANIMALI} animali consentiti.")
            popup.destroy()
            return
        for i in range(nb.index("end")):
            if "(nessun animale)" in nb.tab(i, "text"):
                nb.forget(i)
                break
        nuovo = {
            "id": str(uuid.uuid4()),
            "nome": nome,
            "razza": "",
            "microchip": "",
            "peso_iniziale": 0.0,
            "peso_attuale": 0.0,
            "data_nascita": "",
            "scad_vaccino": "",
            "scad_antiparassitario": "",
            "scad_assicurazione": "",
            "prossimo_controllo": "",
            "note": "",
            "categorie": list(CATEGORIE_ANIMALE_DEFAULT),
            "movimenti": [],
        }
        db["animali"].append(nuovo)
        self._animali_salva(db)
        self._animali_crea_tab(nb, nuovo, db, win)
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

def _animali_elimina(self, db, nb, win):
    idx = nb.index(nb.select())
    if idx < 0 or idx >= len(db["animali"]):
        self.show_toast("Nessun animale selezionato.")
        return
    a = db["animali"][idx]
    if not self.show_custom_askyesno("Elimina Animale", f"Eliminare '{a.get('nome','')}' e tutti i suoi movimenti?"):
        return
    db["animali"].pop(idx)
    self._animali_salva(db)

    for tab_id in list(nb.tabs()):
        nb.forget(tab_id)
    self._animali_vars = {}
    if not db["animali"]:
        ph = ttk.Frame(nb)
        img_ph = self.icone_gui.get("animali")
        if img_ph:
            nb.add(ph, image=img_ph, text="  (nessun animale)  ", compound="left")
        else:
            nb.add(ph, text="  (nessun animale)  ")
        tk.Label(ph, text="Clicca '🐾 Nuovo Animale' per iniziare",
                 font=("Arial", 12), bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER).pack(expand=True)
    else:
        for aa in db["animali"]:
            self._animali_crea_tab(nb, aa, db, win)
    self.show_toast("Animale eliminato.")

def _animali_grafici(self, db):
    if not db["animali"]:
        self.show_toast("Nessun animale presente.")
        return
    if hasattr(self, "_animali_grafici_win") and self._animali_grafici_win and self._animali_grafici_win.winfo_exists():
        self._animali_grafici_win.lift()
        self._animali_grafici_win.focus_force()
        return

    popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    self._animali_grafici_win = popup
    popup.title("Animali — Grafici")
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

    nomi_animali = [a.get("nome", "?") for a in db["animali"]]
    tutte_categorie = sorted({m.get("categoria", "Altro") for a in db["animali"] for m in a.get("movimenti", [])}, key=str.lower)
    anni_disponibili = sorted({
        m.get("data", "")[-4:] for a in db["animali"] for m in a.get("movimenti", [])
        if len(m.get("data", "")) == 10
    }, reverse=True)

    filtri_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL, pady=6)
    filtri_f.pack(fill=tk.X, padx=14, pady=(8, 0))

    tk.Label(filtri_f, text="Animale:", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
             font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
    v_anim = tk.StringVar(value="Tutti")
    cb_anim = ttk.Combobox(filtri_f, textvariable=v_anim, values=["Tutti"] + nomi_animali,
                            state="readonly", style="Border.TCombobox", width=22)
    cb_anim.pack(side=tk.LEFT, padx=(0, 10))

    tk.Label(filtri_f, text="Vista:", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
             font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
    v_vista = tk.StringVar(value="categoria")
    ttk.Radiobutton(filtri_f, text="Per Categoria", variable=v_vista, value="categoria",
                     style="Custom.TRadiobutton", command=lambda: _disegna()).pack(side=tk.LEFT, padx=4)
    ttk.Radiobutton(filtri_f, text="Confronto Animali", variable=v_vista, value="confronto",
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

    cb_anim.bind("<<ComboboxSelected>>", lambda e: _disegna())
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

        animali_attivi = db["animali"] if v_anim.get() == "Tutti" else \
            [a for a in db["animali"] if a.get("nome") == v_anim.get()]

        tot_generale = sum(
            float(m.get("importo", 0) or 0)
            for a in animali_attivi for m in a.get("movimenti", [])
            if _match_periodo(m.get("data", ""))
            and (v_cat.get() == "Tutte" or m.get("categoria", "") == v_cat.get())
        )
        lbl_tot.config(text=f"Totale: € {_fmt_it(tot_generale)}")

        vista = v_vista.get()
        if vista == "confronto" and v_anim.get() == "Tutti":
            bars_data = []
            for a in db["animali"]:
                tot_a = sum(
                    float(m.get("importo", 0) or 0) for m in a.get("movimenti", [])
                    if _match_periodo(m.get("data", ""))
                    and (v_cat.get() == "Tutte" or m.get("categoria", "") == v_cat.get())
                )
                bars_data.append((a.get("nome", "?"), tot_a))
            titolo_base = "Confronto Spesa tra Animali"
        else:
            cat_totali = defaultdict(float)
            for a in animali_attivi:
                for m in a.get("movimenti", []):
                    if not _match_periodo(m.get("data", "")):
                        continue
                    cat = m.get("categoria", "Altro")
                    if v_cat.get() != "Tutte" and cat != v_cat.get():
                        continue
                    cat_totali[cat] += float(m.get("importo", 0) or 0)
            bars_data = list(cat_totali.items())
            titolo_base = f"Spesa per Categoria  |  {v_anim.get()}"

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
            canvas.create_text(x_g, margin_t + plot_h + 4, text=_fmt_it(v_g, ',.0f'), anchor="n",
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
            canvas.create_text(x1 + 5, int(cy), text=f"€ {_fmt_it(valore)}", anchor="w",
                                fill=self.TEXT_COLOR, font=("Arial", 8, "bold"))

    canvas.bind("<Configure>", _disegna)
    popup.after(100, _disegna)

def _animali_estratto(self, db, nb, v_fmese=None, v_fanno=None):
    idx = nb.index(nb.select())
    if idx < 0 or idx >= len(db["animali"]):
        self.show_toast("Nessun animale selezionato.")
        return
    a = db["animali"][idx]
    nome = a.get("nome", "Animale")
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

    movimenti = sorted([m for m in a.get("movimenti", []) if _match(m.get("data", ""))], key=lambda x: x.get("data", ""))
    periodo_str = ""
    if mese_sel != "Tutti" or anno_sel != "Tutti":
        periodo_str = f"  Periodo: {mese_sel if mese_sel != 'Tutti' else '--'}/{anno_sel if anno_sel != 'Tutti' else '----'}"

    LARGHEZZA_DOC = 90
    linea_doppia = "═" * LARGHEZZA_DOC
    linea_singola = "─" * LARGHEZZA_DOC
    lines = [
        linea_doppia,
        "Gestione Animali".center(LARGHEZZA_DOC),
        f"Estratto Conto: {nome.upper()}".center(LARGHEZZA_DOC),
    ]
    if periodo_str:
        lines.append(periodo_str.center(LARGHEZZA_DOC))

    testo_vac, _c1 = self._animali_testo_scadenza(a.get("scad_vaccino", ""))
    testo_anti, _c2 = self._animali_testo_scadenza(a.get("scad_antiparassitario", ""))
    testo_ass, _c3 = self._animali_testo_scadenza(a.get("scad_assicurazione", ""))
    testo_ctrl, _c4 = self._animali_testo_scadenza(a.get("prossimo_controllo", ""))
    costo_mese = self._animali_costo_medio_mensile(a)
    consumo = self._animali_consumo_medio_cibo(a)

    lines += [
        linea_doppia, "",
        "  Informazioni Animale",
        "  ─────────────────────",
        f"  Razza/Specie       : {a.get('razza', '─')}",
        f"  Microchip          : {a.get('microchip', '─')}",
        f"  Peso Attuale       : {a.get('peso_attuale', 0):,.1f} kg",
        f"  Peso Iniziale      : {a.get('peso_iniziale', 0):,.1f} kg",
        f"  Data di Nascita    : {a.get('data_nascita', '─')}",
        f"  Prossimo Controllo : {testo_ctrl}",
        f"  Vaccinazioni       : {testo_vac}",
        f"  Antiparassitario   : {testo_anti}",
        f"  Assicurazione      : {testo_ass}",
        f"  Costo medio mensile: {'€ ' + _fmt_it(costo_mese) if costo_mese else '—'}",
        f"  Consumo medio cibo : {'%.2f kg/mese' % consumo if consumo else '—'}",
        f"  Note               : {a.get('note', '-'):<66}",
        "",
        linea_doppia,
        f"  {'DATA':<12} {'CATEGORIA':<22} {'PESO':>10} {'IMPORTO':>12}   {'DESCRIZIONE'}",
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
        peso_txt = f"{float(m['peso']):,.1f}" if str(m.get("peso", "")).strip() not in ("", "0") else "—"
        lines.append(f"  {m.get('data', ''):<12} {cat_pulita:<22} {peso_txt:>10} {_fmt_it(imp, '>11,.2f')}€   {m.get('descrizione', '')}")

    lines += [
        linea_singola, "",
        "Riepilogo Finanziario".rjust(70),
        "─────────────────────".rjust(70),
        f"Totale Spesa: {_fmt_it(tot, '>15,.2f')} €".rjust(70),
        "",
        linea_doppia,
        f"Documento generato il {datetime.date.today().strftime('%d-%m-%Y')}".center(LARGHEZZA_DOC),
        linea_doppia,
    ]
    contenuto = "\n".join(lines)
    now = datetime.date.today()
    fname = f"Estratto_{nome}_{now.strftime('%d-%m-%Y')}"
    self.show_export_preview(contenuto, default_filename=fname)


def _animali_estratto_totale(self, db, v_fmese=None, v_fanno=None):
    if "animali" not in db or not db["animali"]:
        self.show_toast("Nessun animale presente nel database.")
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
    for a in db["animali"]:
        nome_a = a.get("nome", "Animale")
        for m in a.get("movimenti", []):
            if _match(m.get("data", "")):
                mc = m.copy()
                mc["_nome_animale"] = nome_a
                tutti_i_movimenti.append(mc)
    tutti_i_movimenti.sort(key=lambda x: x.get("data", ""))

    periodo_str = ""
    if mese_sel != "Tutti" or anno_sel != "Tutti":
        periodo_str = f"  Periodo: {mese_sel if mese_sel != 'Tutti' else '--'}/{anno_sel if anno_sel != 'Tutti' else '----'}"

    linea_doppia = "═" * 110
    linea_singola = "─" * 110
    lines = [
        linea_doppia,
        "  Gestione Animali  ".center(110),
        "  Estratto conto generale e cumulativo".center(110),
    ]
    if periodo_str:
        lines.append(periodo_str.center(110))
    lines += [linea_doppia, "", "  Riepilogo animali:", "  ────────────────────────"]
    for a in db["animali"]:
        costo_mese = self._animali_costo_medio_mensile(a)
        lines.append(
            f"  • {a.get('nome', 'Animale'):<25} (Razza: {a.get('razza', '─'):<12}) "
            f"Costo/mese: {'€ ' + _fmt_it(costo_mese) if costo_mese else '—'}"
        )
    lines += [
        "", linea_doppia,
        f"  {'DATA':<12} {'ANIMALE':<16} {'CATEGORIA':<24} {'IMPORTO':>12}   {'DESCRIZIONE'}",
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
        nome_a_pulito = m.get("_nome_animale", "")
        if len(nome_a_pulito) > 14:
            nome_a_pulito = nome_a_pulito[:11] + "..."
        lines.append(f"  {m.get('data', ''):<12} {nome_a_pulito:<16} {cat_pula:<24} {_fmt_it(imp, '>11,.2f')}€   {m.get('descrizione', '')}")

    lines += [
        linea_singola, "",
        "  Bilancio Globale Complessivo".rjust(100),
        "  ────────────────────────────".rjust(100),
        f"  Spesa Totale Generale: {_fmt_it(tot, '>15,.2f')} €".rjust(100),
        "", linea_doppia,
        f"  Documento complessivo generato il {datetime.date.today().strftime('%d-%m-%Y')}".center(110),
        linea_doppia,
    ]
    contenuto = "\n".join(lines)
    now = datetime.date.today()
    fname = f"Estratto_Generale_Animali_{now.strftime('%d-%m-%Y')}"
    self.show_export_preview(contenuto, default_filename=fname)
