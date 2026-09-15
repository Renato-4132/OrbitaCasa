#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import uuid
import datetime
import tkinter as tk
from tkinter import ttk
from tkcalendar import Calendar


CATEGORIE_MANUTENZIONE_CASA = [
    "Impianto Idrico",
    "Rubinetti e Docce",
    "Buone Abitudini",
    "Lavatrice",
    "Lavastoviglie",
    "Ferro da Stiro",
    "Frigorifero e Congelatore",
    "Scaldabagno / Caldaia",
    "Riscaldamento e Camino",
    "Climatizzazione",
    "Ventilazione (VMC) e Cappa",
    "Esterni e Tetto",
    "Automazioni",
    "Sicurezza",
    "Monitoraggio Consumi",
    "Dispensa e Alimenti",
    "Varie",
]

FREQ_PRESET_MANUTENZIONE = [
    ("Ogni settimana", 7),
    ("Ogni 2 settimane", 14),
    ("Ogni mese", 30),
    ("Ogni 2 mesi", 60),
    ("Ogni 3 mesi", 90),
    ("Ogni 6 mesi", 182),
    ("Ogni anno", 365),
    ("Ogni 2 anni", 730),
    ("Ogni 5 anni", 1825),
    ("Personalizzata (gg)", None),
]

_COL_VERDE = "#98C379"
_COL_ROSSO = "#E06C75"
_COL_AMBRA = "#E5C07B"
_COL_GRIGIO = "#9AA0A6"

_SOGLIA_ROSSA = 15   # giorni: sotto questa soglia -> rosso (urgente)
_SOGLIA_AMBRA = 45   # giorni: sotto questa soglia -> ambra (in avvicinamento)


def _mc_uid():
    return uuid.uuid4().hex[:12]

def _manutenzione_default_voci():
    grezzo = [
        ("Impianto Idrico", "Pulizia filtro raccoglitore centralizzato", 90, "Ogni 3 mesi", False),
        ("Impianto Idrico", "Controllo livello sale addolcitore", 30, "Ogni mese", False),
        ("Impianto Idrico", "Pulizia filtro aspirazione autoclave (case con pozzo)", 90, "Ogni 3 mesi", False),
        ("Impianto Idrico", "Controllo tubature esposte al gelo (inizio inverno)", 365, "Ogni anno", False),
        ("Impianto Idrico", "Svuotamento fanghi fossa biologica/depuratore", 730, "Ogni 2 anni", False),

        ("Rubinetti e Docce", "Pulizia frangigetto (aeratori) rubinetti", 60, "Ogni 2 mesi", False),
        ("Rubinetti e Docce", "Pulizia soffione doccia", 30, "Ogni mese", False),

        ("Buone Abitudini", "Versare acqua negli scarichi poco usati (sifone)", 14, "Ogni 2 settimane", False),
        ("Buone Abitudini", "Pulizia preventiva scarichi (bicarbonato/aceto)", 30, "Ogni mese", False),
        ("Buone Abitudini", "Spolvero pareti (angoli e zone dietro i mobili)", 30, "Ogni mese", False),

        ("Lavatrice", "Pulizia filtro di scarico (pompa)", 60, "Ogni 2 mesi", False),
        ("Lavatrice", "Pulizia filtro ingresso acqua + rubinetto", 182, "Ogni 6 mesi", False),
        ("Lavatrice", "Lavaggio a vuoto ad alta temperatura (90°, anticalcare)", 60, "Ogni 2 mesi", False),
        ("Lavatrice", "Pulizia guarnizione oblò", 7, "Ogni settimana", False),
        ("Lavatrice", "Pulizia vaschetta detersivo/ammorbidente", 30, "Ogni mese", False),

        ("Lavastoviglie", "Pulizia filtro fondo vasca", 14, "Ogni 2 settimane", False),
        ("Lavastoviglie", "Controllo sale rigenerante", 30, "Ogni mese", False),
        ("Lavastoviglie", "Ciclo a vuoto ad alta temperatura (anticalcare)", 30, "Ogni mese", False),
        ("Lavastoviglie", "Pulizia braccetti irroratori", 30, "Ogni mese", False),
        ("Lavastoviglie", "Pulizia guarnizione sportello", 14, "Ogni 2 settimane", False),

        ("Ferro da Stiro", "Pulizia piastra", 30, "Ogni mese", False),
        ("Ferro da Stiro", "Decalcificazione serbatoio/caldaia interna", 30, "Ogni mese", False),

        ("Frigorifero e Congelatore", "Pulizia serpentina/griglia posteriore (condensatore)", 182, "Ogni 6 mesi", False),
        ("Frigorifero e Congelatore", "Pulizia vaschetta raccolta condensa", 60, "Ogni 2 mesi", False),
        ("Frigorifero e Congelatore", "Pulizia canalina/foro scarico condensa interno", 90, "Ogni 3 mesi", False),
        ("Frigorifero e Congelatore", "Pulizia interna (ripiani, cassetti, guarnizioni)", 30, "Ogni mese", False),
        ("Frigorifero e Congelatore", "Controllo tenuta guarnizione sportello", 182, "Ogni 6 mesi", False),

        ("Scaldabagno / Caldaia", "Pulizia filtro defangatore circuito riscaldamento", 365, "Ogni anno", False),
        ("Scaldabagno / Caldaia", "Pulizia filtro impurità ingresso caldaia (lato sanitario)", 182, "Ogni 6 mesi", False),
        ("Scaldabagno / Caldaia", "Controllo/sostituzione anodo di magnesio", 730, "Ogni 2 anni", False),
        ("Scaldabagno / Caldaia", "Azionamento manuale valvola di sicurezza/sfiato", 90, "Ogni 3 mesi", False),
        ("Scaldabagno / Caldaia", "Manutenzione completa caldaia a gas (tecnico abilitato)", 365, "Ogni anno", True),

        ("Riscaldamento e Camino", "Pulizia cenere/condotto stufa a pellet (uso stagionale)", 60, "Ogni 2 mesi", False),
        ("Riscaldamento e Camino", "Pulizia canna fumaria (spazzacamino abilitato)", 365, "Ogni anno", True),
        ("Riscaldamento e Camino", "Sfiato aria dai radiatori (inizio stagione)", 365, "Ogni anno", False),

        ("Climatizzazione", "Pulizia filtri aria climatizzatore (stagione d'uso)", 30, "Ogni mese", False),
        ("Climatizzazione", "Controllo/pulizia unità esterna (foglie, detriti)", 182, "Ogni 6 mesi", False),
        ("Climatizzazione", "Manutenzione con carica gas (tecnico frigorista)", 365, "Ogni anno", False),

        ("Ventilazione (VMC) e Cappa", "Pulizia filtri VMC", 90, "Ogni 3 mesi", False),
        ("Ventilazione (VMC) e Cappa", "Sostituzione filtri VMC", 365, "Ogni anno", False),
        ("Ventilazione (VMC) e Cappa", "Pulizia filtro antigrasso cappa cucina", 30, "Ogni mese", False),
        ("Ventilazione (VMC) e Cappa", "Sostituzione filtro carboni attivi cappa", 182, "Ogni 6 mesi", False),

        ("Esterni e Tetto", "Pulizia gronde e pluviali", 365, "Ogni anno", False),
        ("Esterni e Tetto", "Controllo guaina impermeabilizzante terrazzi/balconi", 365, "Ogni anno", False),
        ("Esterni e Tetto", "Pulizia pozzetti e caditoie esterne", 182, "Ogni 6 mesi", False),
        ("Esterni e Tetto", "Pulizia pannelli fotovoltaici", 182, "Ogni 6 mesi", False),

        ("Automazioni", "Lubrificazione guide/cinghie tapparelle e cancelli", 365, "Ogni anno", False),
        ("Automazioni", "Verifica batteria di backup automazioni", 182, "Ogni 6 mesi", False),

        ("Sicurezza", "Test pulsante rilevatore fughe gas", 30, "Ogni mese", False),
        ("Sicurezza", "Verifica batteria backup rilevatore gas", 182, "Ogni 6 mesi", False),
        ("Sicurezza", "Sostituzione sensore rilevatore gas", 1825, "Ogni 5 anni", False),
        ("Sicurezza", "Test pulsante differenziale (salvavita)", 182, "Ogni 6 mesi", False),
        ("Sicurezza", "Verifica dispositivo riarmo automatico frigo/congelatore", 182, "Ogni 6 mesi", False),
        ("Sicurezza", "Test pulsante rilevatore di fumo", 30, "Ogni mese", False),
        ("Sicurezza", "Pulizia sensore rilevatore di fumo", 182, "Ogni 6 mesi", False),
        ("Sicurezza", "Sostituzione batteria rilevatore di fumo", 365, "Ogni anno", False),
        ("Sicurezza", "Controllo visivo estintore (pressione, sicura)", 182, "Ogni 6 mesi", False),
        ("Sicurezza", "Revisione estintore (tecnico abilitato)", 365, "Ogni anno", True),
        ("Sicurezza", "Test pulsante rilevatore monossido di carbonio (CO)", 30, "Ogni mese", False),
        ("Sicurezza", "Sostituzione sensore rilevatore CO", 1825, "Ogni 5 anni", False),

        ("Monitoraggio Consumi", "Lettura contatori acqua/luce/gas", 30, "Ogni mese", False),
        ("Monitoraggio Consumi", "Controllo ripartizione consumi (STAND BY/HIGH/OTHER)", 60, "Ogni 2 mesi", False),
        ("Monitoraggio Consumi", "Test perdite d'acqua (contatore a tutto chiuso)", 90, "Ogni 3 mesi", False),
        ("Monitoraggio Consumi", "Test cassetta WC con colorante alimentare", 182, "Ogni 6 mesi", False),

        ("Dispensa e Alimenti", "Controllo dispensa per tarme/infestanti", 90, "Ogni 3 mesi", False),
    ]
    voci = []
    for categoria, nome, giorni, etichetta, legge in grezzo:
        voci.append({
            "id": _mc_uid(),
            "categoria": categoria,
            "nome": nome,
            "freq_giorni": giorni,
            "freq_label": etichetta,
            "ultima": "",
            "note": "",
            "legge": legge,
        })
    return voci

def _manutenzione_carica(self):
    import __main__ as _app
    MANUTENZIONE_CASA_FILE = _app.MANUTENZIONE_CASA_FILE
    if os.path.exists(MANUTENZIONE_CASA_FILE):
        try:
            with open(MANUTENZIONE_CASA_FILE, "r", encoding="utf-8") as f:
                db = json.load(f)
            if "voci" not in db:
                db["voci"] = []
            return db
        except Exception:
            pass
    return {"voci": _manutenzione_default_voci()}


def _manutenzione_salva(self, db):
    import __main__ as _app
    MANUTENZIONE_CASA_FILE = _app.MANUTENZIONE_CASA_FILE
    DB_DIR = _app.DB_DIR
    try:
        os.makedirs(DB_DIR, exist_ok=True)
        with open(MANUTENZIONE_CASA_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=2, ensure_ascii=False)
    except Exception as e:
        self.show_toast(f"Errore salvataggio CasaCare: {e}")

def _manutenzione_calcola_prossima(self, ultima_str, freq_giorni):
    if not ultima_str:
        return None
    try:
        d = datetime.datetime.strptime(ultima_str, "%d-%m-%Y").date()
    except ValueError:
        return None
    try:
        giorni = int(freq_giorni or 0)
    except (TypeError, ValueError):
        giorni = 0
    return d + datetime.timedelta(days=giorni)

def _manutenzione_giorni_a_scadenza(self, voce):
    prossima = self._manutenzione_calcola_prossima(voce.get("ultima", ""), voce.get("freq_giorni", 0))
    if prossima is None:
        return None
    return (prossima - datetime.date.today()).days

def _manutenzione_stato(self, voce):
    prossima = self._manutenzione_calcola_prossima(voce.get("ultima", ""), voce.get("freq_giorni", 0))
    if prossima is None:
        return "Mai eseguita — da pianificare", "grigio", None
    giorni = (prossima - datetime.date.today()).days
    prossima_str = prossima.strftime("%d-%m-%Y")
    if giorni < 0:
        return f"SCADUTA da {abs(giorni)} gg  ({prossima_str})", "rosso", prossima
    if giorni == 0:
        return f"Scade OGGI  ({prossima_str})", "rosso", prossima
    if giorni <= _SOGLIA_ROSSA:
        return f"tra {giorni} gg  ({prossima_str})", "rosso", prossima
    if giorni <= _SOGLIA_AMBRA:
        return f"tra {giorni} gg  ({prossima_str})", "ambra", prossima
    return f"tra {giorni} gg  ({prossima_str})", "verde", prossima

def manutenzione_casa(self):
    if hasattr(self, "_manutenzione_win") and self._manutenzione_win and self._manutenzione_win.winfo_exists():
        self._manutenzione_win.lift()
        self._manutenzione_win.focus_force()
        return

    db = self._manutenzione_carica()

    win = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    win.title("CasaCare — Manutenzione e Risparmio Casa")
    self._manutenzione_win = win
    win.bind("<Destroy>", lambda e: setattr(self, "_manutenzione_win", None) if e.widget is win else None)
    win.bind("<Escape>", lambda e: win.destroy())
    win.withdraw()
    win.update_idletasks()
    W, H = 1360, 660
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (W // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (H // 2)
    win.geometry(f"{W}x{H}+{max(0, x)}+{max(0, y)}")
    win.minsize(1100, 560)
    win.transient(self)

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

    def _selezionata():
        sel = tree.selection()
        if not sel:
            self.show_toast("Seleziona prima un'attività.")
            return None
        return sel[0]

    def _voce_da_iid(iid):
        return next((v for v in db["voci"] if v["id"] == iid), None)

    _btn(toolbar, " Nuova Attività", lambda: self._manutenzione_popup_editor(db, win, tree, _ripopola), "aggiungi")
    _btn(toolbar, " Modifica", lambda: (
        self._manutenzione_popup_editor(db, win, tree, _ripopola, _voce_da_iid(_selezionata()))
        if _selezionata() else None
    ), "modifica")
    _btn(toolbar, " Segna Eseguita Oggi", lambda: _segna_eseguita(), "check")
    _btn(toolbar, " Azzera", lambda: _azzera(), "reset")
    _btn(toolbar, " Elimina", lambda: _elimina(), "delete")
    _btn(toolbar, " Calendario Scadenze", lambda: self._manutenzione_calendario(db), "calendario")
    _btn(toolbar, " Esporta Scadenze", lambda: self._manutenzione_estratto(db), "descrizione")
    _btn(toolbar, " Manuale Risparmio Casa", lambda: self.scarica_manuale_risparmio(), "search")
    _btn(toolbar, " Salva", lambda: (self._manutenzione_salva(db), self.show_toast("CasaCare salvato.")), "salva")
    _btn(toolbar, " Chiudi", lambda: win.destroy(), "chiudi")

    filtri = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    filtri.pack(fill=tk.X, padx=8, pady=(6, 0))

    tk.Label(filtri, text="Categoria:", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
             font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
    v_cat = tk.StringVar(value="Tutte")
    cats_presenti = sorted({v.get("categoria", "Varie") for v in db["voci"]}) or CATEGORIE_MANUTENZIONE_CASA
    cb_cat = ttk.Combobox(filtri, textvariable=v_cat, values=["Tutte"] + cats_presenti,
                          state="readonly", style="Border.TCombobox", width=28)
    cb_cat.pack(side=tk.LEFT, padx=(0, 12))

    tk.Label(filtri, text="Stato:", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
             font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
    v_stato = tk.StringVar(value="Tutti")
    cb_stato = ttk.Combobox(filtri, textvariable=v_stato,
                            values=["Tutti", "Scadute/Urgenti", "In avvicinamento", "OK", "Da pianificare"],
                            state="readonly", style="Border.TCombobox", width=18)
    cb_stato.pack(side=tk.LEFT, padx=(0, 12))

    lbl_riepilogo = tk.Frame(filtri, bg=self.COLOR_TOPLEVEL)
    lbl_riepilogo.pack(side=tk.RIGHT, padx=(0, 4))

    def _crea_indicatore(parent, colore, etichetta_base):
        blocco = tk.Frame(parent, bg=self.COLOR_TOPLEVEL)
        blocco.pack(side=tk.LEFT, padx=(10, 0))
        swatch = tk.Frame(blocco, bg=colore, width=10, height=10, highlightthickness=1,
                          highlightbackground=self.COLOR_TOPLEVEL)
        swatch.pack(side=tk.LEFT, padx=(0, 4))
        swatch.pack_propagate(False)
        lbl = tk.Label(blocco, text=f"{etichetta_base}: 0", bg=self.COLOR_TOPLEVEL,
                       fg=self.TEXT_COLOR, font=("Arial", 9, "bold"))
        lbl.pack(side=tk.LEFT)
        return lbl

    lbl_cnt_rosso = _crea_indicatore(lbl_riepilogo, _COL_ROSSO, "Scadute/Urgenti")
    lbl_cnt_ambra = _crea_indicatore(lbl_riepilogo, _COL_AMBRA, "In avvicinamento")
    lbl_cnt_verde = _crea_indicatore(lbl_riepilogo, _COL_VERDE, "OK")
    lbl_cnt_grigio = _crea_indicatore(lbl_riepilogo, _COL_GRIGIO, "Da pianificare")

    tree_frame = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

    colonne = ("categoria", "nome", "frequenza", "ultima", "stato", "note")
    tree = ttk.Treeview(tree_frame, columns=colonne, show="headings", selectmode="browse")
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scroll = ttk.Scrollbar(tree_frame, command=tree.yview, style="Vertical.TScrollbar")
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    tree.configure(yscrollcommand=scroll.set)

    intestazioni = {
        "categoria": ("Categoria", 220, "w"),
        "nome": ("Attività", 400, "w"),
        "frequenza": ("Frequenza", 120, "center"),
        "ultima": ("Ultima Esecuzione", 120, "center"),
        "stato": ("Stato / Prossima Scadenza", 230, "w"),
        "note": ("Note", 180, "w"),
    }

    for c in colonne:
        testo, larghezza, ancora = intestazioni[c]
        tree.heading(c, text=testo, command=lambda _c=c: self.treeview_sort_column(tree, _c, False))
        tree.column(c, width=larghezza, anchor=ancora, stretch=(c in ("nome", "stato", "note")))

    tree.tag_configure("rosso", foreground=_COL_ROSSO)
    tree.tag_configure("ambra", foreground=_COL_AMBRA)
    tree.tag_configure("verde", foreground=_COL_VERDE)
    tree.tag_configure("grigio", foreground=_COL_GRIGIO)

    def _ripopola():
        tree.delete(*tree.get_children())
        n_rosso = n_ambra = n_verde = n_grigio = 0
        for v in db["voci"]:
            if v_cat.get() != "Tutte" and v.get("categoria") != v_cat.get():
                continue
            testo_stato, tag, _ = self._manutenzione_stato(v)
            if v_stato.get() == "Scadute/Urgenti" and tag != "rosso":
                continue
            if v_stato.get() == "In avvicinamento" and tag != "ambra":
                continue
            if v_stato.get() == "OK" and tag != "verde":
                continue
            if v_stato.get() == "Da pianificare" and tag != "grigio":
                continue
            if tag == "rosso":
                n_rosso += 1
            elif tag == "ambra":
                n_ambra += 1
            elif tag == "verde":
                n_verde += 1
            else:
                n_grigio += 1
            nome_vis = ("⚖ " if v.get("legge") else "") + v.get("nome", "")
            tree.insert("", tk.END, iid=v["id"], tags=(tag,), values=(
                v.get("categoria", ""), nome_vis, v.get("freq_label", ""),
                v.get("ultima", "") or "—", testo_stato, v.get("note", ""),
            ))
        lbl_cnt_rosso.config(text=f"Scadute/Urgenti: {n_rosso}")
        lbl_cnt_ambra.config(text=f"In avvicinamento: {n_ambra}")
        lbl_cnt_verde.config(text=f"OK: {n_verde}")
        lbl_cnt_grigio.config(text=f"Da pianificare: {n_grigio}")

    def _segna_eseguita():
        iid = _selezionata()
        if not iid:
            return
        v = _voce_da_iid(iid)
        if not v:
            return
        v["ultima"] = datetime.date.today().strftime("%d-%m-%Y")
        self._manutenzione_salva(db)
        _ripopola()
        self.show_toast(f"'{v.get('nome','')}' segnata come eseguita oggi.")
    def _azzera():
        iid = _selezionata()
        if not iid:
            return
        v = _voce_da_iid(iid)
        if not v:
            return
        conferma = self.show_custom_askyesno(
            "Azzera attività",
            f"Riportare '{v.get('nome','')}' allo stato 'mai eseguita'?"
        )
        if not conferma:
            return
        v["ultima"] = ""
        self._manutenzione_salva(db)
        _ripopola()
        self.show_toast(f"'{v.get('nome','')}' azzerata.")
    
    def _elimina():
        iid = _selezionata()
        if not iid:
            return
        v = _voce_da_iid(iid)
        if not v:
            return
        conferma = self.show_custom_askyesno(
            "Elimina attività",
            f"Eliminare definitivamente '{v.get('nome','')}'?"
        )
        if not conferma:
            return
        db["voci"] = [x for x in db["voci"] if x["id"] != iid]
        self._manutenzione_salva(db)
        _ripopola()
        self.show_toast("Attività eliminata.")

    def _doppio_click(event):
        iid = _selezionata()
        if iid:
            self._manutenzione_popup_editor(db, win, tree, _ripopola, _voce_da_iid(iid))

    tree.bind("<Double-1>", _doppio_click)
    cb_cat.bind("<<ComboboxSelected>>", lambda e: _ripopola())
    cb_stato.bind("<<ComboboxSelected>>", lambda e: _ripopola())

    _ripopola()
    win.deiconify()
    win.lift()
    win.focus_force()

def _manutenzione_popup_editor(self, db, parent_win, tree, callback_refresh, voce=None):
    nuovo = voce is None
    if nuovo:
        voce = {"id": _mc_uid(), "categoria": CATEGORIE_MANUTENZIONE_CASA[0], "nome": "",
                "freq_giorni": 30, "freq_label": "Ogni mese", "ultima": "", "note": "", "legge": False}

    popup = tk.Toplevel(parent_win, bg=self.COLOR_TOPLEVEL)
    popup.title("Nuova Attività" if nuovo else "Modifica Attività")
    popup.transient(parent_win)
    popup.withdraw()
    popup.bind("<Escape>", lambda e: popup.destroy())
    popup.resizable(False, False)

    frm = tk.Frame(popup, bg=self.COLOR_TOPLEVEL, padx=14, pady=12)
    frm.pack(fill=tk.BOTH, expand=True)

    def _riga(r, etichetta):
        tk.Label(frm, text=etichetta, bg=self.COLOR_TOPLEVEL, fg=self.COLOR_HEADER,
                 font=("Arial", 9, "bold")).grid(row=r, column=0, sticky="w", padx=(0, 8), pady=4)

    _riga(0, "Categoria:")
    v_categoria = tk.StringVar(value=voce.get("categoria", CATEGORIE_MANUTENZIONE_CASA[0]))
    cb_categoria = ttk.Combobox(frm, textvariable=v_categoria, values=CATEGORIE_MANUTENZIONE_CASA,
                                style="Border.TCombobox", width=34)
    cb_categoria.grid(row=0, column=1, columnspan=2, sticky="ew", pady=4)

    _riga(1, "Attività:")
    v_nome = tk.StringVar(value=voce.get("nome", ""))
    ttk.Entry(frm, textvariable=v_nome, width=45, style="TEntry").grid(
        row=1, column=1, columnspan=2, sticky="ew", pady=4)

    _riga(2, "Frequenza:")
    label_correnti = [lbl for lbl, _ in FREQ_PRESET_MANUTENZIONE]
    freq_label_iniziale = voce.get("freq_label", "Ogni mese")
    if freq_label_iniziale not in label_correnti:
        freq_label_iniziale = "Personalizzata (gg)"
    v_freq_label = tk.StringVar(value=freq_label_iniziale)
    cb_freq = ttk.Combobox(frm, textvariable=v_freq_label, values=label_correnti,
                           state="readonly", style="Border.TCombobox", width=20)
    cb_freq.grid(row=2, column=1, sticky="ew", pady=4)

    v_freq_custom = tk.StringVar(value=str(voce.get("freq_giorni", 30)))

    frame_giorni = tk.Frame(frm, bg=self.COLOR_TOPLEVEL)
    frame_giorni.grid(row=2, column=2, columnspan=2, sticky="w", padx=(6, 0), pady=4)

    entry_freq_custom = ttk.Entry(frame_giorni, textvariable=v_freq_custom, width=8, style="TEntry")
    entry_freq_custom.pack(side=tk.LEFT)

    tk.Label(frame_giorni, text=" Giorni", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
         font=("Arial", 8)).pack(side=tk.LEFT, padx=(2, 0))

    def _sync_freq_custom(*_a):
        if v_freq_label.get() == "Personalizzata (gg)":
            entry_freq_custom.configure(state="normal")
        else:
            giorni = dict(FREQ_PRESET_MANUTENZIONE).get(v_freq_label.get())
            v_freq_custom.set(str(giorni))
            entry_freq_custom.configure(state="disabled")
    cb_freq.bind("<<ComboboxSelected>>", _sync_freq_custom)
    _sync_freq_custom()

    _riga(3, "Ultima esecuzione:")
    v_ultima = tk.StringVar(value=voce.get("ultima", ""))

    frame_ultima = tk.Frame(frm, bg=self.COLOR_TOPLEVEL)
    frame_ultima.grid(row=3, column=1, columnspan=3, sticky="w", pady=4)

    entry_ultima = ttk.Entry(frame_ultima, textvariable=v_ultima, width=14, style="TEntry")
    entry_ultima.pack(side=tk.LEFT)

    img_cal = self.icone_gui.get("calendario")
    btn_cal = ttk.Label(frame_ultima, image=img_cal, text=" 📅" if not img_cal else "",
                     compound="left", cursor="hand2",
                     background=self.COLOR_TOPLEVEL, foreground=self.TEXT_COLOR)
    btn_cal.pack(side=tk.LEFT, padx=(6, 10))
    btn_cal.bind("<Button-1>", lambda e: self.mostra_calendario_popup_semplice(entry_ultima, v_ultima))

    ttk.Label(frame_ultima, text="(vuoto = mai eseguita)", background=self.COLOR_TOPLEVEL,
          foreground=_COL_GRIGIO, font=("Arial", 8)).pack(side=tk.LEFT)
    _riga(4, "Note:")
    v_note = tk.StringVar(value=voce.get("note", ""))
    ttk.Entry(frm, textvariable=v_note, width=45, style="TEntry").grid(
        row=4, column=1, columnspan=2, sticky="ew", pady=4)

    v_legge = tk.BooleanVar(value=bool(voce.get("legge", False)))
    chk_legge = tk.Checkbutton(
        frm, text="Manutenzione obbligatoria per legge (es. caldaia, canna fumaria, estintore)",
        variable=v_legge, bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
        selectcolor=self.COLOR_WIDGET_BG, activebackground=self.COLOR_TOPLEVEL,
        activeforeground=self.TEXT_COLOR, font=("Arial", 8, "italic")
    )
    chk_legge.grid(row=5, column=0, columnspan=4, sticky="w", pady=(4, 8))

    btn_frame = tk.Frame(frm, bg=self.COLOR_TOPLEVEL)
    btn_frame.grid(row=6, column=0, columnspan=4, sticky="ew", pady=(6, 0))

    def _salva():
        nome_pulito = v_nome.get().strip()
        if not nome_pulito:
            self.show_custom_warning("Attenzione", "Il nome dell'attività non può essere vuoto.")
            return
        categoria_pulita = v_categoria.get().strip() or "Varie"
        try:
            giorni = int(v_freq_custom.get())
            if giorni <= 0:
                raise ValueError
        except ValueError:
            self.show_custom_warning("Attenzione", "La frequenza deve essere un numero di giorni positivo.")
            return
        ultima_pulita = v_ultima.get().strip()
        if ultima_pulita:
            try:
                datetime.datetime.strptime(ultima_pulita, "%d-%m-%Y")
            except ValueError:
                self.show_custom_warning("Attenzione", "Data non valida. Formato richiesto: gg-mm-aaaa.")
                return
        voce["categoria"] = categoria_pulita
        voce["nome"] = nome_pulito
        voce["freq_giorni"] = giorni
        voce["freq_label"] = v_freq_label.get()
        voce["ultima"] = ultima_pulita
        voce["note"] = v_note.get().strip()
        voce["legge"] = bool(v_legge.get())
        if nuovo:
            db["voci"].append(voce)
        self._manutenzione_salva(db)
        callback_refresh()
        self.show_toast("Attività salvata.")
        popup.destroy()

    img_ok = self.icone_gui.get("check")
    b_ok = ttk.Label(btn_frame, image=img_ok, text=" Salva", compound="left", cursor="hand2",
                  background=self.COLOR_TOPLEVEL, foreground=self.TEXT_COLOR, font=("Arial", 9, "bold"))
    b_ok.pack(side=tk.LEFT, padx=(15, 0))
    b_ok.bind("<Button-1>", lambda e: _salva())

    img_no = self.icone_gui.get("chiudi")
    b_no = ttk.Label(btn_frame, image=img_no, text=" Annulla", compound="left", cursor="hand2",
                  background=self.COLOR_TOPLEVEL, foreground=self.TEXT_COLOR, font=("Arial", 9, "bold"))
    b_no.pack(side=tk.RIGHT, padx=(0, 15))
    b_no.bind("<Button-1>", lambda e: popup.destroy())

    popup.update_idletasks()
    w_popup, h_popup = 520, 250
    x = parent_win.winfo_rootx() + (parent_win.winfo_width() // 2) - (w_popup // 2)
    y = parent_win.winfo_rooty() + (parent_win.winfo_height() // 2) - (h_popup // 2)
    popup.geometry(f"{w_popup}x{h_popup}+{x}+{y}")
    popup.resizable(False, False)
    popup.deiconify()
    popup.lift()
    popup.focus_force()
    
def _manutenzione_calendario(self, db):
    if hasattr(self, "_manutenzione_cal_win") and self._manutenzione_cal_win and self._manutenzione_cal_win.winfo_exists():
        self._manutenzione_cal_win.lift()
        self._manutenzione_cal_win.focus_force()
        return

    win = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    win.title("Calendario Scadenze — CasaCare")
    self._manutenzione_cal_win = win
    win.bind("<Destroy>", lambda e: setattr(self, "_manutenzione_cal_win", None) if e.widget is win else None)
    win.bind("<Escape>", lambda e: win.destroy())
    win.withdraw()
    win.transient(self)
    win.resizable(False, False)

    corpo = tk.Frame(win, bg=self.COLOR_TOPLEVEL, padx=10, pady=10)
    corpo.pack(fill=tk.BOTH, expand=True)

    sinistra = tk.Frame(corpo, bg=self.COLOR_TOPLEVEL)
    sinistra.pack(side=tk.LEFT, fill=tk.Y)

    cal = Calendar(
        sinistra,
        selectmode='day',
        locale="it_IT",
        date_pattern="dd-mm-yyyy",
        font=("Arial", 10),
        cursor="hand2",
        background=self.cal_header_bg,
        foreground=self.cal_header_fg,
        headersbackground=self.cal_header_bg,
        headersforeground=self.cal_header_fg,
        normalbackground=self.cal_bg,
        normalforeground=self.cal_fg,
        weekendbackground=self.cal_weekend_bg,
        weekendforeground=self.cal_weekend_fg,
        selectbackground=self.cal_select_bg,
        selectforeground=self.cal_select_fg,
        showweeknumbers=False,
        bordercolor=self.cal_bg,
        showothermonthdays=False,
    )
    cal.pack(padx=1, pady=1)
    cal.tag_config("rosso", background=_COL_ROSSO, foreground="#1e1e1e")
    cal.tag_config("ambra", background=_COL_AMBRA, foreground="#1e1e1e")
    cal.tag_config("verde", background=_COL_VERDE, foreground="#1e1e1e")
    cal.tag_config("today", background=self.cal_select_bg, foreground=self.cal_select_fg)

    dati_giorno = {}
    for v in db["voci"]:
        _, tag, prossima = self._manutenzione_stato(v)
        if prossima is None:
            continue
        dati_giorno.setdefault(prossima, []).append((v, tag))
    for data_obj, righe in dati_giorno.items():
        tag_peggiore = "verde"
        if any(t == "rosso" for _, t in righe):
            tag_peggiore = "rosso"
        elif any(t == "ambra" for _, t in righe):
            tag_peggiore = "ambra"
        cal.calevent_create(data_obj, "scadenza", tag_peggiore)
    oggi = datetime.date.today()
    cal.calevent_create(oggi, "Oggi", "today")

    legenda = tk.Frame(sinistra, bg=self.COLOR_TOPLEVEL)
    legenda.pack(fill=tk.X, pady=(8, 0))
    for testo, colore in (("Urgente/Scaduta", _COL_ROSSO), ("In avvicinamento", _COL_AMBRA), ("OK", _COL_VERDE)):
        blocco = tk.Frame(legenda, bg=self.COLOR_TOPLEVEL)
        blocco.pack(side=tk.LEFT, padx=6)
        tk.Frame(blocco, bg=colore, width=12, height=12).pack(side=tk.LEFT, padx=(0, 4))
        tk.Label(blocco, text=testo, bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR, font=("Arial", 8)).pack(side=tk.LEFT)

    destra = tk.Frame(corpo, bg=self.COLOR_TOPLEVEL)
    destra.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(14, 0))
    lbl_giorno = tk.Label(destra, text="Seleziona un giorno per vedere le attività in scadenza",
                      bg=self.COLOR_TOPLEVEL, fg=self.COLOR_HEADER, font=("Arial", 10, "bold"),
                      wraplength=260, justify="left")
    lbl_giorno.pack(anchor="w", pady=(0, 6))

    lista_frame = tk.Frame(destra, bg=self.COLOR_TOPLEVEL)
    lista_frame.pack(fill=tk.BOTH, expand=True)

    lista = tk.Listbox(lista_frame, width=42, height=16, bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                   highlightthickness=1, highlightbackground=self.COLOR_HIGHLIGHT, relief=tk.FLAT,
                   font=("Arial", 9))
    lista.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scroll_lista = ttk.Scrollbar(lista_frame, orient="vertical", command=lista.yview, style="Vertical.TScrollbar")
    scroll_lista.pack(side=tk.RIGHT, fill=tk.Y)
    lista.configure(yscrollcommand=scroll_lista.set)

    def _mostra_giorno(data_obj):
        lista.delete(0, tk.END)
        righe = dati_giorno.get(data_obj, [])
        lbl_giorno.config(text=f"Attività in scadenza il {data_obj.strftime('%d-%m-%Y')}:"
                                if righe else f"Nessuna attività in scadenza il {data_obj.strftime('%d-%m-%Y')}.")
        for v, tag in righe:
            prefisso = "⚖ " if v.get("legge") else "• "
            lista.insert(tk.END, f"{prefisso}{v.get('categoria','')} — {v.get('nome','')}")

    def _on_select(event):
        try:
            data_sel = cal.selection_get()
        except Exception:
            return
        _mostra_giorno(data_sel)
    cal.bind("<<CalendarSelected>>", _on_select)

    btn_chiudi = ttk.Label(destra, text=" Chiudi", image=self.icone_gui.get("chiudi"), compound="left",
                           cursor="hand2", background=self.COLOR_TOPLEVEL, foreground=self.TEXT_COLOR,
                           font=("Arial", 9, "bold"))
    btn_chiudi.pack(anchor="e", pady=(8, 0))
    btn_chiudi.bind("<Button-1>", lambda e: win.destroy())

    win.update_idletasks()
    W, H = 900, 500
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (W // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (H // 2)
    win.geometry(f"{W}x{H}+{max(0, x)}+{max(0, y)}")
    win.resizable(False, False)
    win.deiconify()
    win.lift()
    win.focus_force()

def _manutenzione_estratto(self, db):
    if not db.get("voci"):
        self.show_toast("Nessuna attività di manutenzione presente.")
        return

    righe_calc = []
    for v in db["voci"]:
        giorni = self._manutenzione_giorni_a_scadenza(v)
        testo_stato, tag, _ = self._manutenzione_stato(v)
        chiave_ordine = giorni if giorni is not None else 999999
        righe_calc.append((chiave_ordine, v, testo_stato, tag))
    righe_calc.sort(key=lambda t: t[0])

    W_CAT = max([len("CATEGORIA")] + [len(v.get("categoria", "")) for v in db["voci"]]) + 2
    W_NOME = max([len("ATTIVITÀ")] + [len(v.get("nome", "")) for v in db["voci"]]) + 2
    W_FREQ = max([len("FREQUENZA")] + [len(v.get("freq_label", "")) for v in db["voci"]]) + 2
    W_STATO = max([len("STATO / PROSSIMA SCADENZA")] + [len(t) for _, _, t, _ in righe_calc]) + 2

    LARGHEZZA_DOC = 2 + W_CAT + 1 + W_NOME + 1 + W_FREQ + 1 + W_STATO
    linea_doppia = "═" * LARGHEZZA_DOC
    linea_singola = "─" * LARGHEZZA_DOC
    lines = [
        linea_doppia,
        "CasaCare".center(LARGHEZZA_DOC),
        "Scadenze di Manutenzione e Risparmio Casa".center(LARGHEZZA_DOC),
        linea_doppia,
        "",
        f"  {'CATEGORIA':<{W_CAT}} {'ATTIVITÀ':<{W_NOME}} {'FREQUENZA':<{W_FREQ}} {'STATO / PROSSIMA SCADENZA':<{W_STATO}}",
        linea_singola,
    ]
    n_rosso = n_ambra = n_verde = n_grigio = 0
    for _, v, testo_stato, tag in righe_calc:
        if tag == "rosso":
            n_rosso += 1
        elif tag == "ambra":
            n_ambra += 1
        elif tag == "verde":
            n_verde += 1
        else:
            n_grigio += 1
        prefisso = "⚖ " if v.get("legge") else "  "
        lines.append(
            f"{prefisso}{v.get('categoria',''):<{W_CAT}} {v.get('nome',''):<{W_NOME}} "
            f"{v.get('freq_label',''):<{W_FREQ}} {testo_stato:<{W_STATO}}"
        )

    lines += [
        linea_singola,
        "",
        "Riepilogo".center(LARGHEZZA_DOC),
        "─────────".center(LARGHEZZA_DOC),
        f"Scadute/Urgenti: {n_rosso}    In avvicinamento: {n_ambra}    OK: {n_verde}    Da pianificare: {n_grigio}".center(LARGHEZZA_DOC),
        "",
        linea_doppia,
        f"Documento generato il {datetime.date.today().strftime('%d-%m-%Y')}".center(LARGHEZZA_DOC),
        "⚖ = manutenzione obbligatoria per legge".center(LARGHEZZA_DOC),
        linea_doppia,
    ]
    contenuto = "\n".join(lines)
    now = datetime.date.today()
    fname = f"CasaCare_Scadenze_{now.strftime('%d-%m-%Y')}"
    self.show_export_preview(contenuto, default_filename=fname)
