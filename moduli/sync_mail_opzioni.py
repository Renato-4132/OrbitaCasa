#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import tkinter as tk
from tkinter import ttk, Toplevel

CAT_BOLLETTE_DEFAULT = "Zona @Web/Bank"

OPZIONI_DEFAULT = {
    "data_movimento": "mail",
    "cat_bollette": CAT_BOLLETTE_DEFAULT,
    "segna_letta": True,
    "solo_non_lette": True,
    "giorni_indietro": 30,
    "controllo_doppioni": True,
    "importo_mancante": "ripiego",
    "cat_estratti": "Generica",
    "conto_estratti": "",
    "metodo_estratti": "",
    "tag_estratti": "",
    "pausa_sec": 5,
    "copia_fatture_gmail": True,
}

REGOLA_VUOTA = {"mittente": "", "categoria": "", "conto": "", "metodo": "", "tag": "", "tipo": ""}

_ETICHETTE_DATA = {
    "mail": "Data della mail",
    "oggi": "Data di oggi",
    "scadenza": "Scadenza (se presente)",
}
_ETICHETTE_RICERCA = {True: "Solo mail non lette", False: "Tutte (salta quelle già importate)"}
_ETICHETTE_IMPORTO = {"ripiego": "Registra con 0,01 €", "salta": "Salta la mail"}
_ETICHETTE_TIPO = {"": "Automatico (Gemini)", "Entrata": "Entrata", "Uscita": "Uscita"}

def normalizza_mittenti(raw):
    if raw is None:
        return []
    if isinstance(raw, str):
        pezzi = [raw]
    else:
        pezzi = [str(x) for x in raw]
    risultato = []
    for p in pezzi:
        for k in p.replace(",", " ").replace(";", " ").split():
            k = k.strip().lower()
            if k and k not in risultato:
                risultato.append(k)
    return risultato

def leggi_opzioni(cfg):
    grezzo = (cfg or {}).get("sync_opzioni", {})
    if not isinstance(grezzo, dict):
        grezzo = {}
    opz = dict(OPZIONI_DEFAULT)
    for k, default in OPZIONI_DEFAULT.items():
        if k not in grezzo:
            continue
        v = grezzo[k]
        if isinstance(default, bool):
            opz[k] = bool(v)
        elif isinstance(default, int):
            try:
                opz[k] = int(v)
            except (TypeError, ValueError):
                pass
        else:
            opz[k] = str(v) if v is not None else default
    opz["giorni_indietro"] = max(1, min(365, opz["giorni_indietro"]))
    opz["pausa_sec"] = max(0, min(10, opz["pausa_sec"]))
    if opz["data_movimento"] not in _ETICHETTE_DATA:
        opz["data_movimento"] = "mail"
    if opz["importo_mancante"] not in _ETICHETTE_IMPORTO:
        opz["importo_mancante"] = "ripiego"
    return opz

def leggi_regole(cfg):
    grezzo = (cfg or {}).get("regole_mail", [])
    if not isinstance(grezzo, list):
        return []
    regole = []
    visti = set()
    for r in grezzo:
        if not isinstance(r, dict):
            continue
        mitt = str(r.get("mittente", "")).strip().lower()
        if not mitt or mitt in visti:
            continue
        visti.add(mitt)
        regola = dict(REGOLA_VUOTA)
        for k in REGOLA_VUOTA:
            regola[k] = str(r.get(k, "") or "").strip()
        regola["mittente"] = mitt
        if regola["tipo"] not in ("Entrata", "Uscita"):
            regola["tipo"] = ""
        regole.append(regola)
    return regole

def _nomi_conti(app_main):
    try:
        with open(app_main.PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as f:
            db = json.load(f)
        return [c.get("nome", "") for c in db.get("conti", []) if c.get("nome")]
    except Exception:
        return []


def _metodi_pagamento():
    try:
        from moduli.modello_spesa import METODI_PAGAMENTO
        return list(METODI_PAGAMENTO)
    except Exception:
        return []


def _riempi_tooltip(corpo, testo, larghezza=340):
    """Una riga per ogni «\n» e per ogni frase (a capo dopo il punto). Le righe che iniziano con «• » hanno il pallino in una colonna
    a parte, così le righe a capo restano allineate al testo e non al pallino."""
    import re
    righe = []
    for r in testo.split("\n"):
        if r.startswith("• "):
            righe.append(r)
        else:
            # a capo dopo ogni frase (punto seguito da una maiuscola; «es. #tag» non si spezza)
            righe.extend(re.split(r'(?<=[.!?])\s+(?=[A-ZÀ-Ý«"])', r))
    for i, riga in enumerate(righe):
        pad_alto = 8 if i == 0 else 2
        pad_basso = 8 if i == len(righe) - 1 else 2
        if riga.startswith("• "):
            f = tk.Frame(corpo, bg=corpo.cget("bg"))
            f.pack(fill="x", padx=10, pady=(pad_alto, pad_basso))
            ttk.Label(f, text="•", style="Tooltip.TLabel").pack(side="left", anchor="n", padx=(4, 6))
            ttk.Label(f, text=riga[2:], style="Tooltip.TLabel", justify="left",
                      wraplength=larghezza - 30).pack(side="left", anchor="n")
        else:
            ttk.Label(corpo, text=riga, style="Tooltip.TLabel", justify="left",
                      wraplength=larghezza).pack(anchor="w", padx=10, pady=(pad_alto, pad_basso))


def _tooltip(app, widget, testo, ritardo_ms=1000):
    if not testo:
        return
    stato = {"win": None, "job": None}

    def mostra_ora():
        stato["job"] = None
        try:
            win = Toplevel(widget)
            win.withdraw()
            win.wm_overrideredirect(True)
            try:
                win.wm_attributes("-topmost", True)
            except tk.TclError:
                pass
            # Bordo blu 1 px: sfondo in COLOR_HIGHLIGHT + frame interno; testo con padding
            win.config(bg=app.COLOR_HIGHLIGHT)
            corpo = tk.Frame(win, bg=app.COLOR_TOOLTIP)
            corpo.pack(fill="both", expand=True, padx=1, pady=1)
            _riempi_tooltip(corpo, testo)
            win.update_idletasks()
            tw, th = win.winfo_reqwidth(), win.winfo_reqheight()
            wx, wy = widget.winfo_rootx(), widget.winfo_rooty()
            ww, wh = widget.winfo_width(), widget.winfo_height()
            top = widget.winfo_toplevel()
            swx, swy = top.winfo_rootx(), top.winfo_rooty()
            sww, swh = top.winfo_width(), top.winfo_height()
            x = wx + (ww // 2) - (tw // 2)
            y = wy - th - 15
            if x < swx:
                x = swx + 5
            elif x + tw > swx + sww:
                x = swx + sww - tw - 5
            if y < swy:
                y = wy + wh + 5
            elif y + th > swy + swh:
                y = swy + swh - th - 5
            win.wm_geometry(f"+{int(x)}+{int(y)}")
            win.deiconify()
            stato["win"] = win
        except tk.TclError:
            stato["win"] = None

    def mostra(event=None):
        if stato["win"] is not None or stato["job"] is not None:
            return
        stato["job"] = widget.after(ritardo_ms, mostra_ora)

    def nascondi(event=None):
        if stato["job"] is not None:
            try:
                widget.after_cancel(stato["job"])
            except tk.TclError:
                pass
            stato["job"] = None
        if stato["win"] is not None:
            try:
                stato["win"].destroy()
            except tk.TclError:
                pass
            stato["win"] = None

    widget.bind("<Enter>", mostra, add="+")
    widget.bind("<Leave>", nascondi, add="+")
    widget.bind("<ButtonPress>", nascondi, add="+")
    widget.bind("<Destroy>", nascondi, add="+")


TIP_OPZIONI = {
    "Data del movimento (bollette):":
        "Che data dare al movimento creato da una bolletta o fattura.\n"
        "• Data della mail: il giorno in cui è arrivata\n"
        "• Data di oggi: il giorno della sincronizzazione\n"
        "• Scadenza: quella letta da Gemini; se manca usa la data della mail\n"
        "Negli estratti conto non vale: ogni movimento ha la sua data.",
    "Categoria predefinita bollette:":
        "Categoria usata quando la regola del mittente non ne ha una. "
        "Se non esiste ancora, viene creata.",
    "Cerca:":
        "Solo mail non lette: legge solo quelle non lette in Gmail.\n"
        "Tutte: legge anche quelle già lette, saltando quelle già importate.\n"
        "Una mail già importata non viene riscaricata nemmeno se la rimetti da leggere "
        "(si sblocca con il reset di «Mail Elaborate»).",
    "Giorni da controllare (1-365):":
        "Quanti giorni indietro cerca le mail. Lo stesso valore decide per quanto tempo "
        "ricorda quelle già elaborate: il doppio dei giorni, minimo 90.",
    "Se l'importo non si trova:":
        "Registra con 0,01 € (la spesa compare e la correggi a mano) oppure salta la mail: "
        "in quel caso scrive SALTATA nel log e la mail non viene più ripresa.",
    "Pausa tra una mail e l'altra (s):":
        "Attesa dopo ogni mail analizzata, per non superare i limiti di richieste di Gemini. "
        "0 = nessuna pausa, massimo 10 secondi.",
    "Estratti conto: categoria di ripiego:":
        "Negli estratti conto Gemini sceglie la categoria di ogni movimento. Se ne propone una "
        "che non è nella tua lista, si usa questa. Se la regola del mittente ha una categoria, "
        "vince quella.",
    "Estratti conto: conto:":
        "Conto assegnato ai movimenti importati dagli estratti conto. "
        "Se la regola del mittente ha un conto, vince quello.",
    "Estratti conto: metodo:":
        "Metodo di pagamento assegnato ai movimenti importati dagli estratti conto. "
        "Se la regola del mittente ha un metodo, vince quello.",
    "Estratti conto: tag:":
        "Tag aggiunti ai movimenti importati dagli estratti conto, separati da uno spazio. "
        "Se la regola del mittente ha dei tag, vincono quelli.",
    "Segna la mail come letta dopo l'importazione":
        "Dopo l'importazione marca la mail come letta in Gmail, così con «Solo mail non lette» "
        "non viene riletta.",
    "Controllo doppioni (stesso importo e descrizione)":
        "Non registra un movimento con stessa descrizione e stesso importo di uno già presente. "
        "Per le bollette controlla su tutte le date, per gli estratti conto nello stesso giorno.",
    "Conserva una copia dei PDF in Fatture_GMail":
        "Salva una copia dei PDF allegati nella cartella Fatture_GMail. "
        "Il PDF finisce comunque nell'archivio documenti dell'app.",
    "btn_ripristina":
        "Riporta le opzioni ai valori predefiniti. Non tocca le regole per mittente. "
        "Per salvare usa Salva della Configurazione.",
    "btn_per_tutti":
        "Aggiunge una regola vuota per ogni indirizzo dei Filtri Email che non ne ha già una.",
}

TIP_REGOLA = {
    "Mittente (indirizzo):":
        "Deve essere uguale a uno dei Filtri Email, altrimenti la regola non viene applicata. "
        "Dopo la creazione non si può modificare.",
    "Categoria:":
        "Categoria dei movimenti di questo mittente. Vuoto = categoria predefinita bollette.",
    "Conto:":
        "Conto bancario a cui assegnare i movimenti. Vuoto = nessun conto "
        "(per gli estratti conto si usa il conto delle opzioni).",
    "Metodo di pagamento:":
        "Metodo di pagamento dei movimenti. Vuoto = nessuno.",
    "Tag (es. #utenze #casa):":
        "Tag aggiunti ai movimenti, separati da uno spazio.",
    "Tipo movimento:":
        "Automatico: lo decide Gemini leggendo la mail.\n"
        "Entrata/Uscita: forza il verso.\n"
        "Negli estratti conto decide comunque il segno dell'importo.",
}


def _pulsante(app, parent, icona, testo, comando, tip=None):
    img = None
    try:
        img = app.icone_gui.get(icona)
    except Exception:
        pass
    b = ttk.Label(parent, compound="left", image=img if img else "",
                  text=f" {testo}" if img else testo,
                  background=app.COLOR_WIDGET_BG, foreground=app.TEXT_COLOR,
                  cursor="hand2", padding=(10, 5))
    b.image = img
    b.bind("<Button-1>", lambda e: comando())
    _tooltip(app, b, tip)
    return b

def _dimensiona(win, parent, min_w=0, min_h=0):
    win.update_idletasks()
    w = max(min_w, win.winfo_reqwidth() + 16)
    h = max(min_h, win.winfo_reqheight() + 16)
    w = min(w, win.winfo_screenwidth() - 40)
    h = min(h, win.winfo_screenheight() - 100)
    _centra(win, parent, w, h)
    win.minsize(min(w, win.winfo_screenwidth() - 40), min(h, win.winfo_screenheight() - 100))

def _centra(win, parent, w, h):
    try:
        parent.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (w // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2)
        x = max(0, min(x, win.winfo_screenwidth() - w))
        y = max(0, min(y, win.winfo_screenheight() - h - 40))
        win.geometry(f"{w}x{h}+{x}+{y}")
    except Exception:
        win.geometry(f"{w}x{h}")

def _editor_regola(app, parent, regola, mittenti_disponibili, gia_usati, categorie, conti, metodi, on_ok):
    win = Toplevel(parent)
    win.withdraw()
    win.title("Regola mittente")
    win.transient(parent)
    win.resizable(False, False)
    try:
        win.configure(bg=app.COLOR_WIDGET_BG)
    except Exception:
        pass

    frm = ttk.Frame(win, padding=14)
    frm.pack(fill="both", expand=True)
    frm.columnconfigure(1, weight=1)

    v_mitt = tk.StringVar(value=regola.get("mittente", ""))
    v_cat = tk.StringVar(value=regola.get("categoria", ""))
    v_conto = tk.StringVar(value=regola.get("conto", ""))
    v_metodo = tk.StringVar(value=regola.get("metodo", ""))
    v_tag = tk.StringVar(value=regola.get("tag", ""))
    v_tipo = tk.StringVar(value=_ETICHETTE_TIPO.get(regola.get("tipo", ""), _ETICHETTE_TIPO[""]))

    modifica = bool(regola.get("mittente"))

    def riga(r, testo, widget):
        lbl = ttk.Label(frm, text=testo, anchor="w")
        lbl.grid(row=r, column=0, sticky="w", pady=4)
        widget.grid(row=r, column=1, sticky="we", pady=4, padx=(10, 0))
        _tooltip(app, lbl, TIP_REGOLA.get(testo))
        _tooltip(app, widget, TIP_REGOLA.get(testo))

    liberi = [m for m in mittenti_disponibili if m not in gia_usati or m == regola.get("mittente")]
    cb_mitt = ttk.Combobox(frm, style="Border.TCombobox", textvariable=v_mitt, values=liberi, width=44)
    if modifica:
        cb_mitt.state(["disabled"])
    riga(0, "Mittente (indirizzo):", cb_mitt)
    riga(1, "Categoria:", ttk.Combobox(frm, style="Border.TCombobox", textvariable=v_cat,
                                       values=[""] + list(categorie), width=44))
    riga(2, "Conto:", ttk.Combobox(frm, style="Border.TCombobox", textvariable=v_conto,
                                   values=[""] + list(conti), width=44, state="readonly"))
    riga(3, "Metodo di pagamento:", ttk.Combobox(frm, style="Border.TCombobox", textvariable=v_metodo,
                                                 values=[""] + list(metodi), width=44, state="readonly"))
    riga(4, "Tag (es. #utenze #casa):", ttk.Entry(frm, textvariable=v_tag, width=46))
    riga(5, "Tipo movimento:", ttk.Combobox(frm, style="Border.TCombobox", textvariable=v_tipo,
                                            values=list(_ETICHETTE_TIPO.values()), width=44, state="readonly"))

    ttk.Label(
        frm, foreground="gray", wraplength=520, justify="left",
        text="Lascia vuoto un campo per usare il comportamento predefinito "
             "(categoria predefinita bollette, nessun conto, nessun metodo, nessun tag, tipo deciso da Gemini)."
    ).grid(row=6, column=0, columnspan=2, sticky="w", pady=(8, 2))

    def conferma():
        mitt = v_mitt.get().strip().lower()
        if not mitt or ("@" not in mitt and "." not in mitt):
            app.show_custom_info("Regola", "Inserisci l'indirizzo del mittente (o una parte di esso).")
            return
        if not modifica and mitt in gia_usati:
            app.show_custom_info("Regola", "Esiste già una regola per questo mittente.")
            return
        tipo_sel = next((k for k, v in _ETICHETTE_TIPO.items() if v == v_tipo.get()), "")
        try:
            tag_norm = " ".join(app._normalizza_tags(v_tag.get()))
        except Exception:
            tag_norm = v_tag.get().strip()
        on_ok({
            "mittente": mitt,
            "categoria": v_cat.get().strip(),
            "conto": v_conto.get().strip(),
            "metodo": v_metodo.get().strip(),
            "tag": tag_norm,
            "tipo": tipo_sel,
        })
        win.destroy()

    bt = ttk.Frame(frm)
    bt.grid(row=7, column=0, columnspan=2, pady=(12, 0), sticky="e")
    _pulsante(app, bt, "chiudi", "Annulla", win.destroy).pack(side="right", padx=(6, 0))
    _pulsante(app, bt, "salva", "OK", conferma).pack(side="right")

    _dimensiona(win, parent)
    win.deiconify()
    win.grab_set()
    cb_mitt.focus_set()

class TabImportazione:

    def __init__(self, app, tab, finestra, stato, get_mittenti):
        import __main__ as _app
        self.app = app
        self.finestra = finestra
        self.stato = stato
        self.get_mittenti = get_mittenti
        self.categorie = sorted(set(getattr(app, "categorie", []) or []), key=str.lower)
        self.conti = _nomi_conti(_app)
        self.metodi = _metodi_pagamento()
        self.regole = [dict(r) for r in leggi_regole({"regole_mail": stato.get("regole", [])})]
        opz = leggi_opzioni({"sync_opzioni": stato.get("opzioni", {})})
        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=0)
        tab.rowconfigure(0, weight=1)
        self._costruisci_regole(tab)
        self._costruisci_opzioni(tab, opz)

    def _costruisci_regole(self, tab):
        app = self.app
        lf = ttk.LabelFrame(tab, text=" Regole per mittente ", padding=8)
        lf.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ttk.Label(
            lf, foreground="gray", wraplength=640, justify="left",
            text="Ogni riga assegna categoria, conto, metodo, tag e tipo ai movimenti importati da quel mittente. "
                 "I mittenti da leggere si impostano nel campo «Filtri Email» del tab Sync Email & AI."
        ).pack(anchor="w", pady=(0, 6))

        colonne = ("mittente", "categoria", "conto", "metodo", "tag", "tipo")
        intest = {"mittente": "Mittente", "categoria": "Categoria", "conto": "Conto",
                  "metodo": "Metodo", "tag": "Tag", "tipo": "Tipo"}
        largh = {"mittente": 210, "categoria": 110, "conto": 100, "metodo": 90, "tag": 100, "tipo": 80}

        f_tree = ttk.Frame(lf)
        f_tree.pack(fill="both", expand=True)
        f_tree.rowconfigure(0, weight=1)
        f_tree.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(f_tree, columns=colonne, show="headings", height=14, selectmode="browse")
        for c in colonne:
            self.tree.heading(c, text=intest[c])
            self.tree.column(c, width=largh[c], anchor="w")
        sb = ttk.Scrollbar(f_tree, orient="vertical", command=self.tree.yview)
        sbo = ttk.Scrollbar(f_tree, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=sb.set, xscrollcommand=sbo.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        sbo.grid(row=1, column=0, sticky="we")
        self.tree.bind("<Double-1>", lambda e: self.modifica())

        f_bt = ttk.Frame(lf)
        f_bt.pack(fill="x", pady=(8, 0))
        _pulsante(app, f_bt, "aggiungi", "Aggiungi", self.aggiungi).pack(side="left")
        _pulsante(app, f_bt, "modifica", "Modifica", self.modifica).pack(side="left", padx=4)
        _pulsante(app, f_bt, "delete", "Elimina", self.elimina).pack(side="left")
        _pulsante(app, f_bt, "email", "Una regola per ogni filtro", self.crea_per_tutti,
                  tip=TIP_OPZIONI["btn_per_tutti"]).pack(side="right")
        self.ricarica()

    def ricarica(self):
        self.tree.delete(*self.tree.get_children())
        righe = []
        for i, r in enumerate(self.regole):
            valori = (
                r["mittente"], r["categoria"] or "(predefinita)", r["conto"], r["metodo"], r["tag"],
                _ETICHETTE_TIPO.get(r["tipo"], "Automatico").replace(" (Gemini)", ""),
            )
            righe.append(valori)
            self.tree.insert("", "end", iid=str(i), values=valori)
        self._adatta_colonne(righe)

    def _adatta_colonne(self, righe):
        import tkinter.font as tkfont
        try:
            nome_font = ttk.Style().lookup("Treeview", "font") or "TkDefaultFont"
            fnt = tkfont.nametofont(nome_font)
        except Exception:
            fnt = tkfont.nametofont("TkDefaultFont")
        try:
            fnt_h = tkfont.nametofont(ttk.Style().lookup("Treeview.Heading", "font") or "TkHeadingFont")
        except Exception:
            fnt_h = fnt
        colonne = self.tree["columns"]
        for n, c in enumerate(colonne):
            w = fnt_h.measure(self.tree.heading(c, "text")) + 18
            for riga in righe:
                w = max(w, fnt.measure(str(riga[n])) + 18)
            w = min(w, 460)
            self.tree.column(c, width=w, minwidth=w, stretch=True)

    def _mittenti(self):
        return normalizza_mittenti(self.get_mittenti())

    def _usati(self):
        return {r["mittente"] for r in self.regole}

    def _indice(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def aggiungi(self):
        _editor_regola(self.app, self.finestra, dict(REGOLA_VUOTA), self._mittenti(), self._usati(),
                       self.categorie, self.conti, self.metodi,
                       lambda r: (self.regole.append(r), self.ricarica()))

    def modifica(self):
        i = self._indice()
        if i is None:
            self.app.show_toast("Seleziona prima una regola.", duration=1800, parent=self.finestra)
            return

        def _salva(r, i=i):
            self.regole[i] = r
            self.ricarica()
        _editor_regola(self.app, self.finestra, dict(self.regole[i]), self._mittenti(), self._usati(),
                       self.categorie, self.conti, self.metodi, _salva)

    def elimina(self):
        i = self._indice()
        if i is None:
            self.app.show_toast("Seleziona prima una regola.", duration=1800, parent=self.finestra)
            return
        del self.regole[i]
        self.ricarica()

    def crea_per_tutti(self):
        presenti = self._usati()
        nuovi = [m for m in self._mittenti() if m not in presenti]
        for m in nuovi:
            r = dict(REGOLA_VUOTA)
            r["mittente"] = m
            self.regole.append(r)
        self.ricarica()
        self.app.show_toast(f"Aggiunte {len(nuovi)} regole.", duration=1800, parent=self.finestra)

    def _costruisci_opzioni(self, tab, opz):
        app = self.app
        lf = ttk.LabelFrame(tab, text=" Opzioni di importazione ", padding=8)
        lf.grid(row=0, column=1, sticky="nsew")
        lf.columnconfigure(1, weight=1)

        self.v_data = tk.StringVar(value=_ETICHETTE_DATA[opz["data_movimento"]])
        self.v_catb = tk.StringVar(value=opz["cat_bollette"])
        self.v_letta = tk.BooleanVar(value=opz["segna_letta"])
        self.v_ricerca = tk.StringVar(value=_ETICHETTE_RICERCA[opz["solo_non_lette"]])
        self.v_giorni = tk.IntVar(value=opz["giorni_indietro"])
        self.v_dopp = tk.BooleanVar(value=opz["controllo_doppioni"])
        self.v_importo = tk.StringVar(value=_ETICHETTE_IMPORTO[opz["importo_mancante"]])
        self.v_cate = tk.StringVar(value=opz["cat_estratti"])
        self.v_conte = tk.StringVar(value=opz["conto_estratti"])
        self.v_metodoe = tk.StringVar(value=opz["metodo_estratti"])
        self.v_tage = tk.StringVar(value=opz["tag_estratti"])
        self.v_pausa = tk.IntVar(value=opz["pausa_sec"])
        self.v_copia = tk.BooleanVar(value=opz["copia_fatture_gmail"])

        def combo(r, testo, var, valori, readonly=True, width=22):
            lbl = ttk.Label(lf, text=testo, anchor="w")
            lbl.grid(row=r, column=0, sticky="w", padx=(0, 8), pady=3)
            cb = ttk.Combobox(lf, style="Border.TCombobox", textvariable=var, values=valori, width=width,
                              state="readonly" if readonly else "normal")
            cb.grid(row=r, column=1, sticky="w", pady=3)
            _tooltip(app, lbl, TIP_OPZIONI.get(testo))
            _tooltip(app, cb, TIP_OPZIONI.get(testo))

        def spin(r, testo, var, a, b):
            lbl = ttk.Label(lf, text=testo, anchor="w")
            lbl.grid(row=r, column=0, sticky="w", padx=(0, 8), pady=3)
            sp = ttk.Spinbox(lf, style="Custom.TSpinbox", from_=a, to=b, textvariable=var, width=6,
                             justify="center")
            sp.grid(row=r, column=1, sticky="w", pady=3)
            _tooltip(app, lbl, TIP_OPZIONI.get(testo))
            _tooltip(app, sp, TIP_OPZIONI.get(testo))

        def campo_testo(r, testo, var):
            lbl = ttk.Label(lf, text=testo, anchor="w")
            lbl.grid(row=r, column=0, sticky="w", padx=(0, 8), pady=3)
            en = ttk.Entry(lf, textvariable=var, width=24)
            en.grid(row=r, column=1, sticky="w", pady=3)
            _tooltip(app, lbl, TIP_OPZIONI.get(testo))
            _tooltip(app, en, TIP_OPZIONI.get(testo))

        def check(r, testo, var):
            cb = ttk.Checkbutton(lf, text=testo, variable=var)
            cb.grid(row=r, column=0, columnspan=2, sticky="w", pady=2)
            _tooltip(app, cb, TIP_OPZIONI.get(testo))

        combo(0, "Data del movimento (bollette):", self.v_data, list(_ETICHETTE_DATA.values()))
        combo(1, "Categoria predefinita bollette:", self.v_catb, self.categorie, readonly=False)
        combo(2, "Cerca:", self.v_ricerca, list(_ETICHETTE_RICERCA.values()))
        spin(3, "Giorni da controllare (1-365):", self.v_giorni, 1, 365)
        combo(4, "Se l'importo non si trova:", self.v_importo, list(_ETICHETTE_IMPORTO.values()))
        spin(5, "Pausa tra una mail e l'altra (s):", self.v_pausa, 0, 10)
        combo(6, "Estratti conto: categoria di ripiego:", self.v_cate, self.categorie, readonly=False)
        combo(7, "Estratti conto: conto:", self.v_conte, [""] + self.conti)
        combo(8, "Estratti conto: metodo:", self.v_metodoe, [""] + self.metodi)
        campo_testo(9, "Estratti conto: tag:", self.v_tage)

        check(10, "Segna la mail come letta dopo l'importazione", self.v_letta)
        check(11, "Controllo doppioni (stesso importo e descrizione)", self.v_dopp)
        check(12, "Conserva una copia dei PDF in Fatture_GMail", self.v_copia)
        _pulsante(app, lf, "reset", "Ripristina opzioni predefinite", self.ripristina_opzioni,
                  tip=TIP_OPZIONI["btn_ripristina"]).grid(
            row=13, column=0, columnspan=2, sticky="w", pady=(6, 0))

    def _imposta_opzioni(self, d):
        self.v_data.set(_ETICHETTE_DATA[d["data_movimento"]])
        self.v_catb.set(d["cat_bollette"])
        self.v_letta.set(d["segna_letta"])
        self.v_ricerca.set(_ETICHETTE_RICERCA[d["solo_non_lette"]])
        self.v_giorni.set(d["giorni_indietro"])
        self.v_dopp.set(d["controllo_doppioni"])
        self.v_importo.set(_ETICHETTE_IMPORTO[d["importo_mancante"]])
        self.v_cate.set(d["cat_estratti"])
        self.v_conte.set(d["conto_estratti"])
        self.v_metodoe.set(d["metodo_estratti"])
        self.v_tage.set(d["tag_estratti"])
        self.v_pausa.set(d["pausa_sec"])
        self.v_copia.set(d["copia_fatture_gmail"])

    def ripristina_opzioni(self):
        self._imposta_opzioni(OPZIONI_DEFAULT)

    def ripristina_tutto(self, opzioni, regole):
        self._imposta_opzioni(leggi_opzioni({"sync_opzioni": opzioni}))
        self.regole = [dict(r) for r in leggi_regole({"regole_mail": regole})]
        self.ricarica()

    def raccogli(self):
        try:
            giorni = int(self.v_giorni.get())
            pausa = int(self.v_pausa.get())
        except (tk.TclError, ValueError):
            self.app.show_custom_info("Opzioni importazione", "Giorni e pausa devono essere numeri interi.")
            return False
        if not 1 <= giorni <= 365:
            self.app.show_custom_info("Opzioni importazione", "I giorni da controllare devono essere tra 1 e 365.")
            return False
        if not 0 <= pausa <= 10:
            self.app.show_custom_info("Opzioni importazione", "La pausa deve essere tra 0 e 10 secondi.")
            return False

        def inverso(mappa, valore, default):
            return next((k for k, v in mappa.items() if v == valore), default)

        try:
            tag_estratti = " ".join(self.app._normalizza_tags(self.v_tage.get()))
        except Exception:
            tag_estratti = self.v_tage.get().strip()

        self.stato["opzioni"] = {
            "data_movimento": inverso(_ETICHETTE_DATA, self.v_data.get(), "mail"),
            "cat_bollette": self.v_catb.get().strip() or CAT_BOLLETTE_DEFAULT,
            "segna_letta": bool(self.v_letta.get()),
            "solo_non_lette": inverso(_ETICHETTE_RICERCA, self.v_ricerca.get(), True),
            "giorni_indietro": giorni,
            "controllo_doppioni": bool(self.v_dopp.get()),
            "importo_mancante": inverso(_ETICHETTE_IMPORTO, self.v_importo.get(), "ripiego"),
            "cat_estratti": self.v_cate.get().strip() or "Generica",
            "conto_estratti": self.v_conte.get().strip(),
            "metodo_estratti": self.v_metodoe.get().strip(),
            "tag_estratti": tag_estratti,
            "pausa_sec": pausa,
            "copia_fatture_gmail": bool(self.v_copia.get()),
        }
        self.stato["regole"] = [dict(r) for r in self.regole]
        return True
