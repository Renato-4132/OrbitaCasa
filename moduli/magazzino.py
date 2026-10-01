#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import uuid
import datetime
import tkinter as tk
from tkinter import ttk, filedialog

CATEGORIE_DEFAULT = [
    "Alimentari", "Bevande", "Pulizia casa", "Igiene personale", "Medicinali",
    "Ferramenta", "Elettronica", "Cancelleria", "Abbigliamento", "Giardino",
    "Auto / Moto", "Animali", "Varie",
]
# Categorie suggerite in base all'uso che si fa del magazzino (modificabili a piacere dopo l'aggiunta)
PROFILI_CATEGORIE = {
    "Officina / Garage": ["Viteria e Bulloneria", "Utensili a mano", "Elettroutensili", "Materiale elettrico",
                             "Idraulica", "Vernici e Colle", "Lubrificanti", "Ricambi auto", "Abrasivi",
                             "Protezioni (DPI)"],
    "Ufficio / Studio": ["Carta e Stampa", "Cancelleria", "Toner e Cartucce", "Cavi e Accessori",
                            "Hardware", "Archiviazione", "Pulizia ufficio", "Materiale da riunione"],
    "Negozio / Bottega": ["Merce in vendita", "Imballaggi", "Etichette", "Espositori", "Materiale promozionale",
                             "Resi e Difettosi", "Campionario"],
    "Bar / Ristorante": ["Materie prime", "Carne e Pesce", "Ortofrutta", "Panetteria", "Vini e Bevande",
                            "Caffè e Tè", "Monouso e Tovagliato", "Pulizia e Sanificazione"],
    "Farmacia / Salute": ["Farmaci da banco", "Integratori", "Medicazione", "Igiene", "Dispositivi medici",
                             "Cosmetici"],
    "Hobby / Bricolage": ["Colori e Pennelli", "Carta e Cartoncini", "Tessuti e Filati", "Perline e Minuteria",
                             "Legno e Modellismo", "Colle e Adesivi", "Attrezzi hobby"],
    "Giardino / Orto": ["Semi e Bulbi", "Terricci e Concimi", "Fitofarmaci", "Vasi e Contenitori",
                           "Attrezzi da giardino", "Irrigazione", "Mangimi"],
}

UNITA = ["pz", "kg", "g", "lt", "ml", "m", "m²", "conf", "scatola", "set"]
TUTTE_CAT = "Tutte le categorie"
STATI_FILTRO = ["Tutti gli stati", "Da riordinare", "Sotto scorta", "Esauriti", "In eccesso", "Disponibile",
               "In scadenza", "Scaduti"]
GIORNI_SCADENZA = 30
COLONNE = ("Articolo", "Categoria", "Descrizione", "Qtà", "U.M.", "Min", "Max",
           "Prezzo", "Valore", "Riordino", "Stato", "Scadenza", "Data")
LARGHEZZE = (170, 110, 200, 65, 50, 60, 60, 85, 95, 70, 100, 140, 85)
ANCORE = ("w", "w", "w", "e", "center", "e", "e", "e", "e", "e", "center", "center", "center")

def _fmt_it(v, spec=",.2f"):
    s = format(v, spec)
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")

def _fmt_eur(v):
    return _fmt_it(v) + " €"

def _fmt_q(v, mil=False):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return "0"
    if abs(v - round(v)) < 1e-9:
        return _fmt_it(int(round(v)), ",d" if mil else "d")
    return _fmt_it(v, ",.3f" if mil else ".3f").rstrip("0").rstrip(",")

def _num(v, default=0.0):
    if isinstance(v, (int, float)):
        r = float(v)
    else:
        s = str(v or "").replace("€", "").replace(" ", "").strip()
        if not s:
            return default
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        elif s.count(".") > 1:
            s = s.replace(".", "")
        try:
            r = float(s)
        except ValueError:
            raise ValueError(f"Numero non valido: {v!r}")
    if r != r or r in (float("inf"), float("-inf")):
        raise ValueError(f"Numero non valido: {v!r}")
    return r
    
def _oggi():
    return datetime.date.today().strftime("%d-%m-%Y")

def _parse_data(s):
    s = str(s or "").strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None

def calcola_stato(a):
    q = float(a.get("quantita", 0) or 0)
    mn = float(a.get("qta_min", 0) or 0)
    mx = float(a.get("qta_max", 0) or 0)
    esaurito = q <= 0
    sotto = mn > 0 and q <= mn
    if esaurito:
        stato, tag = "Esaurito", "esaurito"
    elif sotto:
        stato, tag = "Sotto scorta", "sotto"
    elif mx > 0 and q > mx:
        stato, tag = "In eccesso", "eccesso"
    else:
        stato, tag = "Disponibile", ""
    da_ordinare = 0.0
    if sotto or (esaurito and (mn > 0 or mx > 0)):
        target = mx if mx > 0 else mn * 2
        da_ordinare = round(max(target - q, 0.0), 3)
    return stato, tag, da_ordinare

def stato_scadenza(a, oggi=None, giorni=GIORNI_SCADENZA):
    d = _parse_data(a.get("scadenza"))
    if d is None:
        return "", "", ""
    testo = d.strftime("%d-%m-%Y")
    if float(a.get("quantita", 0) or 0) <= 0:
        return "", "", testo
    delta = (d - (oggi or datetime.date.today())).days
    if delta < 0:
        return "Scaduto", "scaduto", f"{testo} (scaduto)"
    if delta <= giorni:
        return "In scadenza", "scadenza", f"{testo} ({'oggi' if delta == 0 else str(delta) + ' gg'})"
    return "", "", testo

def scorta_min_suggerita(a, oggi=None, finestra=90, copertura=14):
    oggi = oggi or datetime.date.today()
    mov = [(_parse_data(m.get("data")), m) for m in a.get("movimenti", [])]
    mov = [(d, m) for d, m in mov if d]
    if not mov:
        return None
    inizio = max(oggi - datetime.timedelta(days=finestra), min(d for d, _ in mov))
    scarichi = [-m["delta"] for d, m in mov
                if m.get("delta", 0) < 0 and m.get("nota") != "Rettifica da modifica" and d >= inizio]
    if len(scarichi) < 2:
        return None
    al_giorno = sum(scarichi) / max((oggi - inizio).days, copertura)
    v = al_giorno * copertura
    if a.get("unita", "pz") in ("pz", "conf", "scatola", "set"):
        n = int(v)
        v = float(n + (1 if v > n else 0))
    else:
        v = round(v, 2)
    v = min(v, 900.0)
    return (al_giorno, v) if v > 0 else None

def valori_riga(a):
    stato, tag, ordina = calcola_stato(a)
    _, tag_sc, txt_sc = stato_scadenza(a)
    if tag_sc:
        tag = tag_sc
    q = float(a.get("quantita", 0) or 0)
    pr = float(a.get("prezzo", 0) or 0)
    mx = float(a.get("qta_max", 0) or 0)
    return (
        a.get("nome", ""), a.get("categoria", ""), a.get("descrizione", "").replace("\n", " "),
        _fmt_q(q, True), a.get("unita", "pz"), _fmt_q(a.get("qta_min", 0), True),
        _fmt_q(mx, True) if mx else "",
        _fmt_eur(pr), _fmt_eur(q * pr),
        _fmt_q(ordina, True) if ordina else "",
        stato, txt_sc, a.get("data", ""),
    ), tag

def normalizza_articolo(a):
    _sc = _parse_data(a.get("scadenza"))
    return {
        "id": str(a.get("id") or uuid.uuid4().hex[:12]),
        "codice": str(a.get("codice", "")),
        "nome": str(a.get("nome", "")).strip(),
        "categoria": str(a.get("categoria", "")).strip(),
        "descrizione": str(a.get("descrizione", "")),
        "unita": str(a.get("unita", "pz") or "pz"),
        "quantita": _num(a.get("quantita", 0)),
        "qta_min": _num(a.get("qta_min", 0)),
        "qta_max": _num(a.get("qta_max", 0)),
        "prezzo": _num(a.get("prezzo", 0)),
        "scadenza": _sc.strftime("%d-%m-%Y") if _sc else "",
        "data": a.get("data") or _oggi(),
        "movimenti": list(a.get("movimenti", []))[-100:],
    }

def articolo_corrisponde(a, testo):
    parole = testo.lower().split()
    if not parole:
        return True
    vals, _ = valori_riga(a)
    pagliaio = " ".join([a.get("codice", ""), a.get("descrizione", "")] + [str(v) for v in vals]).lower()
    return all(p in pagliaio for p in parole)

def _tabella_txt(titolo, cols, righe, tot_label, tot_val, col_tot):
    celle = []
    for r in righe:
        celle.append([str(v)[:c[2]] if c[2] else str(v) for v, c in zip(r, cols)])
    larg = [max([len(c[0])] + [len(r[i]) for r in celle]) for i, c in enumerate(cols)]
    def riga(vals):
        return "  ".join(f"{v:{c[1]}{w}}" for v, c, w in zip(vals, cols, larg)).rstrip()
    tot_w = sum(larg) + 2 * (len(cols) - 1)
    fine = sum(larg[:col_tot + 1]) + 2 * col_tot
    L = [titolo, "=" * tot_w, riga([c[0] for c in cols]), "-" * tot_w]
    L += [riga(r) for r in celle]
    L += ["-" * tot_w, (tot_label + "  ").rjust(fine - len(tot_val)) + tot_val]
    return "\n".join(L)

def testo_inventario(elenco, filtro_attivo=False):
    LARG = 153
    L = [f"INVENTARIO MAGAZZINO — {_oggi()}" + (" (filtrato)" if filtro_attivo else ""), "=" * LARG,
         f"{'Articolo':<28}{'Categoria':<16}{'Qtà':>8} {'UM':<5}{'Min':>7}{'Max':>7}{'Prezzo':>14}{'Valore':>18}"
         f"  {'Stato':<13}  {'Scadenza':<20}  {'Data':<10}",
         "-" * LARG]
    for a in sorted(elenco, key=lambda x: (x["categoria"].lower(), x["nome"].lower())):
        L.append(f"{a['nome'][:27]:<28}{a['categoria'][:15]:<16}{_fmt_q(a['quantita']):>8} {a['unita'][:4]:<5}"
                 f"{_fmt_q(a['qta_min']):>7}{(_fmt_q(a['qta_max']) if a['qta_max'] else '-'):>7}"
                 f"{_fmt_eur(a['prezzo']):>14}{_fmt_eur(a['quantita'] * a['prezzo']):>18}"
                 f"  {calcola_stato(a)[0]:<13}  {(stato_scadenza(a)[2] or '-'):<20}  {a.get('data', ''):<10}")
    L += ["-" * LARG, f"{'VALORE TOTALE  ':>86}{_fmt_eur(sum(a['quantita'] * a['prezzo'] for a in elenco)):>18}"]
    return "\n".join(L)

def _mostra(win, parent, w, h):
    try:
        parent.update_idletasks()
        win.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (w // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2)
        win.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")
        win.deiconify()
        win.lift()
        win.focus_force()
    except tk.TclError:
        pass

def magazzino_app(self):
    import __main__ as _app
    DB_DIR       = _app.DB_DIR
    MAG_FILE     = _app.MAGAZZINO_FILE
    EXP_DB       = _app.EXP_DB
    EXPORT_FILES = _app.EXPORT_FILES

    if getattr(self, "_magazzino_window", None) and self._magazzino_window.winfo_exists():
        self._magazzino_window.lift()
        self._magazzino_window.focus_force()
        return

    root = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    root.title("StockBox — Magazzino e Scorte")
    self._magazzino_window = root
    def _alla_chiusura(e):
        if e.widget is root:
            self._magazzino_window = None
            self._magazzino_ricarica = None
    root.bind("<Destroy>", _alla_chiusura)
    root.withdraw()
    W, H = 1366, 660
    root.minsize(W, H)
    root.transient(self)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(2, weight=1)

    col_red = getattr(self, "COLOR_RED", "#FF5555")
    col_org = getattr(self, "COLOR_ORANGE", "#FFA500")
    col_scad = "#E066FF"
    col_insc = "#F4D03F"
    stato_dati = {"articoli": [], "categorie": []}
    art = stato_dati["articoli"]

    def salva():
        try:
            os.makedirs(os.path.dirname(MAG_FILE), exist_ok=True)
            tmp = MAG_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"versione": 1, "categorie": stato_dati["categorie"], "articoli": art},
                          f, indent=2, ensure_ascii=False)
            os.replace(tmp, MAG_FILE)
        except Exception as e:
            self.show_custom_warning("Errore", f"Impossibile salvare il magazzino:\n{e}")

    def carica():
        art.clear()
        stato_dati["categorie"] = list(CATEGORIE_DEFAULT)
        if not os.path.exists(MAG_FILE):
            return
        try:
            with open(MAG_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d, dict) and "categorie" in d:
                stato_dati["categorie"] = []
            _leggi_struttura(d)
        except Exception:
            art.clear()
            try:
                os.replace(MAG_FILE, MAG_FILE + ".corrotto")
            except OSError:
                pass
            self.show_custom_warning("Attenzione", "File magazzino non valido!\nRinominato in .corrotto per non perdere i dati.")

    def _leggi_struttura(d, unisci=False):
        lista = d.get("articoli", []) if isinstance(d, dict) else d
        if not isinstance(lista, list):
            raise ValueError("Formato non valido")
        nuovi = [normalizza_articolo(x) for x in lista if isinstance(x, dict) and str(x.get("nome", "")).strip()]
        if not unisci:
            art.clear()
        ids = {a["id"] for a in art}
        for n in nuovi:
            if n["id"] in ids:
                n["id"] = uuid.uuid4().hex[:12]
            art.append(n)
        if isinstance(d, dict):
            for c in d.get("categorie", []):
                if c not in stato_dati["categorie"]:
                    stato_dati["categorie"].append(c)
        return len(nuovi)

    def tutte_categorie():
        s = set(stato_dati["categorie"]) | {a["categoria"] for a in art if a["categoria"]}
        return sorted(s, key=str.lower)

    ctx = None
    menu_popup = tk.Menu(root, tearoff=0, bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT,
                         activebackground=self.MENU_ACT_BG_COLOR, activeforeground=self.MENU_ACT_FG_COLOR)
    menu_db = tk.Menu(menu_popup, tearoff=0, bg=self.MENU_BG, fg=self.MENU_FG_LIGHT,
                      activebackground=self.MENU_ACT_BG_COLOR, activeforeground=self.MENU_ACT_FG_COLOR)
    menu_popup.add_cascade(label="💾 Database", menu=menu_db)
    menu_db.add_command(label="📤 Esporta DataBase (.json)", command=lambda: esporta_json())
    menu_db.add_command(label="📥 Importa Database (.json)", command=lambda: importa_json())
    menu_db.add_separator()
    menu_db.add_command(label="🖨️ Esporta inventario (anteprima PDF / TXT / Stampa)", command=lambda: stampa_inventario())
    menu_db.add_separator()
    menu_db.add_command(label="🔙 Reset DataBase", command=lambda: reset_db())
    menu_db.add_separator()
    menu_db.add_command(label="❌ Chiudi", command=lambda: chiudi())

    _timer_menu = {"id": None}

    def chiudi_menu_sicuro(event=None):
        _timer_menu["id"] = None
        for m in (menu_popup, menu_db, ctx):
            if m is None:
                continue
            try:
                m.unpost()
                m.grab_release()
            except tk.TclError:
                pass

    def avvia_timer_menu(event=None):
        if _timer_menu["id"] is None:
            _timer_menu["id"] = root.after(400, chiudi_menu_sicuro)

    def annulla_timer_menu(event=None):
        if _timer_menu["id"] is not None:
            root.after_cancel(_timer_menu["id"])
            _timer_menu["id"] = None

    def rendi_chiudibile(m):
        m.bind("<Leave>", avvia_timer_menu)
        m.bind("<Enter>", annulla_timer_menu)

    def apri_menu(widget):
        try:
            menu_popup.tk_popup(widget.winfo_rootx(), widget.winfo_rooty() + widget.winfo_height())
        finally:
            menu_popup.grab_release()

    def chiudi():
        root.destroy()
    root.protocol("WM_DELETE_WINDOW", chiudi)
    root.bind("<Escape>", lambda e: chiudi())

    def crea_btn(parent, icona, testo, cmd, fallback=""):
        img = self.icone_gui.get(icona) if hasattr(self, "icone_gui") else None
        b = ttk.Label(parent, compound="left", image=img,
                      text=f" {testo}" if img else f"{fallback} {testo}".strip(),
                      background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                      cursor="hand2", padding=(10, 5))
        b.bind("<Button-1>", lambda e: cmd())
        return b

    def crea_icona_cal(parent):
        img = self.icone_gui.get("calendario") if hasattr(self, "icone_gui") else None
        lb = ttk.Label(parent, image=img, cursor="hand2", background=self.COLOR_WIDGET_BG, padding=(3, 2)) if img \
            else ttk.Label(parent, text="📅", cursor="hand2", background=self.COLOR_WIDGET_BG, padding=(3, 2))
        if img:
            lb.image = img
        return lb

    header = tk.Frame(root, bg=self.COLOR_TOPLEVEL)
    header.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 0))
    b_menu = crea_btn(header, "tools", "Menu", lambda: apri_menu(b_menu), "☰")
    b_menu.pack(side="left")
    tk.Label(header, text="  Ricerca globale:", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
             font=("Arial", 9, "bold")).pack(side="left", padx=(10, 4))
    var_cerca = tk.StringVar()
    entry_cerca = ttk.Entry(header, textvariable=var_cerca, width=30)
    entry_cerca.pack(side="left")
    _img_x = self.icone_gui.get("chiudi") if hasattr(self, "icone_gui") else None
    if _img_x:
        lbl_x = ttk.Label(header, image=_img_x, cursor="hand2", background=self.COLOR_WIDGET_BG, padding=(5, 2))
        lbl_x.image = _img_x
    else:
        lbl_x = ttk.Label(header, text="✖", cursor="hand2", background=self.COLOR_WIDGET_BG, padding=(5, 2))
    lbl_x.pack(side="left", padx=(3, 12))
    lbl_x.bind("<Button-1>", lambda e: (var_cerca.set(""), entry_cerca.focus_set()))

    tk.Label(header, text="Categoria:", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
             font=("Arial", 9)).pack(side="left", padx=(0, 4))
    var_cat = tk.StringVar(value=TUTTE_CAT)
    cmb_cat = ttk.Combobox(header, textvariable=var_cat, state="readonly", width=30, style="Border.TCombobox")
    cmb_cat.pack(side="left", padx=(0, 10))
    tk.Label(header, text="Stato:", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
             font=("Arial", 9)).pack(side="left", padx=(0, 4))
    var_stato = tk.StringVar(value=STATI_FILTRO[0])
    cmb_stato = ttk.Combobox(header, textvariable=var_stato, state="readonly", width=14, values=STATI_FILTRO, style="Border.TCombobox")
    cmb_stato.pack(side="left")

    riga_data = tk.Frame(root, bg=self.COLOR_TOPLEVEL)
    riga_data.grid(row=1, column=0, sticky="ew", padx=10, pady=(6, 6))
    tk.Label(riga_data, text="Data aggiornamento — Dal:", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
             font=("Arial", 9)).pack(side="left", padx=(0, 2))
    var_dal, var_al = tk.StringVar(), tk.StringVar()
    ent_dal = ttk.Entry(riga_data, textvariable=var_dal, width=11)
    ent_dal.pack(side="left")
    cal_dal = crea_icona_cal(riga_data)
    cal_dal.pack(side="left", padx=(2, 8))
    cal_dal.bind("<Button-1>", lambda e: self.mostra_calendario_popup_semplice(ent_dal, var_dal))
    tk.Label(riga_data, text="Al:", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
             font=("Arial", 9)).pack(side="left", padx=(0, 2))
    ent_al = ttk.Entry(riga_data, textvariable=var_al, width=11)
    ent_al.pack(side="left")
    cal_al = crea_icona_cal(riga_data)
    cal_al.pack(side="left", padx=(2, 12))
    cal_al.bind("<Button-1>", lambda e: self.mostra_calendario_popup_semplice(ent_al, var_al))
    crea_btn(riga_data, "reset", "Azzera filtri", lambda: azzera_filtri(), "↺").pack(side="left")
    tk.Label(riga_data,
             text="Doppio clic → modifica   |   Clic destro → carico / scarico / storico   |   Clic sull'intestazione → ordina",
             bg=self.COLOR_TOPLEVEL, fg="gray", font=("Arial", 8, "italic")).pack(side="right")

    frame_tree = ttk.Frame(root)
    frame_tree.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 4))
    frame_tree.columnconfigure(0, weight=1)
    frame_tree.rowconfigure(0, weight=1)
    vsb = ttk.Scrollbar(frame_tree, orient="vertical", style="Vertical.TScrollbar")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb = ttk.Scrollbar(frame_tree, orient="horizontal")
    hsb.grid(row=1, column=0, sticky="ew")
    tree = ttk.Treeview(frame_tree, columns=COLONNE, show="headings", selectmode="extended",
                        yscrollcommand=vsb.set, xscrollcommand=hsb.set)
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)
    for c, w, an in zip(COLONNE, LARGHEZZE, ANCORE):
        tree.heading(c, text=c, command=lambda _c=c: self.treeview_sort_column(tree, _c, False))
        tree.column(c, width=w, anchor=an, minwidth=40)
    tree.tag_configure("esaurito", foreground=col_red)
    tree.tag_configure("sotto", foreground=col_org)
    tree.tag_configure("eccesso", foreground="#4DA3FF")
    tree.tag_configure("scaduto", foreground=col_scad)
    tree.tag_configure("scadenza", foreground=col_insc)
    tree.tag_configure("vuoto", foreground="gray")

    lbl_tot = tk.Label(root, text="", anchor="w", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                       font=("Arial", 9, "bold"))
    lbl_tot.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 2))
    leg = tk.Frame(root, bg=self.COLOR_TOPLEVEL)
    leg.grid(row=4, column=0, sticky="w", padx=12)
    tk.Label(leg, text="Legenda:", bg=self.COLOR_TOPLEVEL, fg="gray", font=("Arial", 8)).pack(side="left")
    for colore, testo in ((col_red, "esaurito"), (col_org, "sotto scorta minima (da riordinare)"),
                          ("#4DA3FF", "oltre la scorta massima"), (col_scad, "scaduto"),
                          (col_insc, f"in scadenza (entro {GIORNI_SCADENZA} giorni)")):
        tk.Label(leg, text="  ●", bg=self.COLOR_TOPLEVEL, fg=colore, font=("Arial", 10)).pack(side="left")
        tk.Label(leg, text=testo, bg=self.COLOR_TOPLEVEL, fg="gray", font=("Arial", 8)).pack(side="left")

    barra = tk.Frame(root, bg=self.COLOR_TOPLEVEL)
    barra.grid(row=5, column=0, pady=8)
    for icona, testo, cmd, fb in [
        ("aggiungi", "Inserisci", lambda: apri_form(), "➕"),
        ("modifica", "Modifica", lambda: modifica_sel(), "✏️"),
        ("delete", "Cancella", lambda: cancella_sel(), "🗑️"),
        ("sync", "Carico / Scarico", lambda: movimento_sel(), "🔄"),
        ("tag", "Categorie", lambda: gestisci_categorie(), "🏷️"),
        ("spesa", "Lista riordino", lambda: apri_riordino(), "🛒"),
        ("report", "Scorte suggerite", lambda: suggerisci_scorta(), "📈"),
        ("stampa", "Esporta / Stampa", lambda: stampa_inventario(), "🖨️"),
        ("chiudi", "Chiudi", lambda: chiudi(), "❌"),
    ]:
        crea_btn(barra, icona, testo, cmd, fb).pack(side="left", padx=4)

    def aggiorna_categorie():
        cmb_cat["values"] = [TUTTE_CAT] + tutte_categorie()
        if var_cat.get() not in cmb_cat["values"]:
            var_cat.set(TUTTE_CAT)

    def filtrati():
        testo = var_cerca.get().strip()
        cat = var_cat.get()
        stt = var_stato.get()
        dal, al = _parse_data(var_dal.get()), _parse_data(var_al.get())
        out = []
        for a in art:
            if cat != TUTTE_CAT and a["categoria"] != cat:
                continue
            stato, _, ordina = calcola_stato(a)
            if stt == "Da riordinare" and not ordina:
                continue
            if stt == "Sotto scorta" and stato != "Sotto scorta":
                continue
            if stt == "Esauriti" and stato != "Esaurito":
                continue
            if stt == "In eccesso" and stato != "In eccesso":
                continue
            if stt == "Disponibile" and stato != "Disponibile":
                continue
            if stt == "In scadenza" and stato_scadenza(a)[0] != "In scadenza":
                continue
            if stt == "Scaduti" and stato_scadenza(a)[0] != "Scaduto":
                continue
            if dal or al:
                d = _parse_data(a.get("data"))
                if d is None or (dal and d < dal) or (al and d > al):
                    continue
            if testo and not articolo_corrisponde(a, testo):
                continue
            out.append(a)
        return out

    def riapplica_ordinamento():
        for c in COLONNE:
            t = tree.heading(c, "text")
            if t.endswith(" ▲") or t.endswith(" ▼"):
                self.treeview_sort_column(tree, c, t.endswith(" ▼"))
                return
        self.treeview_sort_column(tree, "Articolo", False)

    def ridisegna(seleziona=None):
        sel_prec = set(tree.selection()) if seleziona is None else set(seleziona)
        tree.delete(*tree.get_children())
        elenco = filtrati()
        for a in elenco:
            vals, tag = valori_riga(a)
            tree.insert("", "end", iid=a["id"], values=vals, tags=(tag,) if tag else ())
        if not elenco:
            if art:
                tree.insert("", "end", iid="__vuoto__", values=("Nessun articolo trovato.",) + ("",) * (len(COLONNE) - 1), tags=("vuoto",))
        else:
            riapplica_ordinamento()
            presenti = [i for i in sel_prec if tree.exists(i)]
            if presenti:
                tree.selection_set(presenti)
                tree.see(presenti[0])
        valore = sum(a["quantita"] * a["prezzo"] for a in elenco)
        n_sotto = sum(1 for a in elenco if calcola_stato(a)[1] == "sotto")
        n_esa = sum(1 for a in elenco if calcola_stato(a)[1] == "esaurito")
        n_ord = sum(1 for a in elenco if calcola_stato(a)[2] > 0)
        n_scad = sum(1 for a in elenco if stato_scadenza(a)[0] == "Scaduto")
        n_insc = sum(1 for a in elenco if stato_scadenza(a)[0] == "In scadenza")
        lbl_tot.config(text=f"Articoli: {len(elenco)} su {len(art)}    |    Valore in magazzino: {_fmt_eur(valore)}"
                            f"    |    Sotto scorta: {n_sotto}    |    Esauriti: {n_esa}    |    Da riordinare: {n_ord}"
                            f"    |    Scaduti: {n_scad}    |    In scadenza: {n_insc}")

    def azzera_filtri():
        var_cerca.set("")
        var_cat.set(TUTTE_CAT)
        var_stato.set(STATI_FILTRO[0])
        var_dal.set("")
        var_al.set("")

    var_cerca.trace_add("write", lambda *a: ridisegna())
    var_dal.trace_add("write", lambda *a: ridisegna())
    var_al.trace_add("write", lambda *a: ridisegna())
    cmb_cat.bind("<<ComboboxSelected>>", lambda e: ridisegna())
    cmb_stato.bind("<<ComboboxSelected>>", lambda e: ridisegna())

    def sel_articoli():
        return [a for a in art if a["id"] in tree.selection()]

    def trova(id_):
        return next((a for a in art if a["id"] == id_), None)

    def finestra_aperta(chiave):
        if not hasattr(root, chiave):
            return False
        w = getattr(root, chiave)
        try:
            if w.winfo_exists():
                w.deiconify()
                w.lift()
                w.focus_force()
                return True
        except tk.TclError:
            pass
        return False

    def apri_form(articolo=None):
        if finestra_aperta("_edit_win"):
            return
        f = tk.Toplevel(root, bg=self.COLOR_TOPLEVEL)
        root._edit_win = f
        f.withdraw()
        f.transient(root)
        f.title("Modifica articolo" if articolo else "Inserisci articolo")
        fw, fh = 600, 500
        f.minsize(fw, fh)
        f.columnconfigure(1, weight=1)
        f.bind("<Escape>", lambda e: f.destroy())
        v = {k: tk.StringVar() for k in ("nome", "codice", "categoria", "unita", "quantita", "min", "max", "prezzo", "scadenza", "data")}
        tk.Label(f, text="Modifica articolo" if articolo else "Inserisci articolo", bg=self.COLOR_TOPLEVEL,
                 fg=self.TEXT_COLOR, font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=3, pady=(12, 10))

        def riga(r, testo, widget):
            tk.Label(f, text=testo, bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR).grid(row=r, column=0, sticky="ne" if r == 4 else "e", padx=(14, 6), pady=4)
            widget.grid(row=r, column=1, sticky="ew", padx=(0, 14), pady=4, columnspan=2 if r != 9 else 1)
            return widget
        e_nome = riga(1, "Articolo *", ttk.Entry(f, textvariable=v["nome"]))
        e_cod = riga(2, "Codice / SKU", ttk.Entry(f, textvariable=v["codice"]))
        c_cat = riga(3, "Categoria", ttk.Combobox(f, textvariable=v["categoria"], values=[""] + tutte_categorie(), state="readonly", style="Border.TCombobox"))

        txt_desc = tk.Text(f, height=2, wrap="word", relief="flat", borderwidth=0, bg=self.COLOR_WIDGET_BG,
                   fg=self.TEXT_COLOR, insertbackground=self.TEXT_COLOR, padx=5, pady=5,
                   highlightthickness=1, highlightbackground="gray",
                   highlightcolor=getattr(self, "COLOR_ACCENT", "#61AFEF"))
        riga(4, "Descrizione", txt_desc)
        limite_desc = 45
        def controlla_limite_testo(event):
            if event.keysym in ("BackSpace", "Delete", "Left", "Right", "Up", "Down", "Home", "End"):
                return
            if len(txt_desc.get("1.0", "end-1c")) >= limite_desc:
                return "break"
        txt_desc.bind("<KeyPress>", controlla_limite_testo)
        c_um = riga(5, "Unità di misura", ttk.Combobox(f, textvariable=v["unita"], values=UNITA, width=12, style="Border.TCombobox"))
        c_um.grid_configure(columnspan=1, sticky="w")
        e_q = riga(6, "Quantità in magazzino", ttk.Entry(f, textvariable=v["quantita"], width=14))
        e_q.grid_configure(columnspan=1, sticky="w")
        e_min = riga(7, "Quantità minima (scorta)", ttk.Entry(f, textvariable=v["min"], width=14))
        e_min.grid_configure(columnspan=1, sticky="w")
        e_max = riga(8, "Quantità massima (scorta)", ttk.Entry(f, textvariable=v["max"], width=14))
        e_max.grid_configure(columnspan=1, sticky="w")
        e_pr = riga(9, "Prezzo unitario €", ttk.Entry(f, textvariable=v["prezzo"], width=14))
        e_pr.grid_configure(columnspan=1, sticky="w")
        tk.Label(f, text="Scadenza", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR).grid(row=10, column=0, sticky="e", padx=(14, 6), pady=4)
        fr_s = tk.Frame(f, bg=self.COLOR_TOPLEVEL)
        fr_s.grid(row=10, column=1, sticky="w", pady=4)
        e_scad = ttk.Entry(fr_s, textvariable=v["scadenza"], width=12)
        e_scad.pack(side="left")
        b_cal_s = crea_icona_cal(fr_s)
        b_cal_s.pack(side="left", padx=4)
        b_cal_s.bind("<Button-1>", lambda e: self.mostra_calendario_popup_semplice(e_scad, v["scadenza"]))
        tk.Label(fr_s, text="facoltativa (gg-mm-aaaa)", bg=self.COLOR_TOPLEVEL, fg="gray",
                 font=("Arial", 8)).pack(side="left", padx=4)
        tk.Label(f, text="Data", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR).grid(row=11, column=0, sticky="e", padx=(14, 6), pady=4)
        fr_d = tk.Frame(f, bg=self.COLOR_TOPLEVEL)
        fr_d.grid(row=11, column=1, sticky="w", pady=4)
        e_data = ttk.Entry(fr_d, textvariable=v["data"], width=12)
        e_data.pack(side="left")
        b_cal = crea_icona_cal(fr_d)
        b_cal.pack(side="left", padx=4)
        b_cal.bind("<Button-1>", lambda e: self.mostra_calendario_popup_semplice(e_data, v["data"]))
        tk.Label(f, text="Se lasci il campo vuoto o invariato, la data sarà aggiornata a oggi.",
         bg=self.COLOR_TOPLEVEL, fg="gray", font=("Arial", 8)).grid(row=12, column=1, columnspan=2, sticky="w")

        for w, n in ((e_nome, 24), (e_cod, 30), (c_cat, 30)):
            w.config(validate="key", validatecommand=(f.register(lambda P, n=n: len(P) <= n), "%P"))

        if articolo:
            v["nome"].set(articolo["nome"]); v["codice"].set(articolo.get("codice", ""))
            v["categoria"].set(articolo["categoria"]); v["unita"].set(articolo["unita"])
            v["quantita"].set(_fmt_q(articolo["quantita"])); v["min"].set(_fmt_q(articolo["qta_min"]))
            v["max"].set(_fmt_q(articolo["qta_max"]) if articolo["qta_max"] else "")
            v["prezzo"].set(_fmt_it(articolo["prezzo"])); v["data"].set(articolo["data"])
            v["scadenza"].set(articolo.get("scadenza", ""))
            txt_desc.insert("1.0", articolo.get("descrizione", ""))
        else:
            v["unita"].set("pz"); v["quantita"].set("0"); v["min"].set("0"); v["prezzo"].set("0,00")
            v["data"].set(_oggi())
        data_originale = v["data"].get()
        e_nome.focus_set()

        def leggi():
            nome = v["nome"].get().strip()
            if not nome:
                self.show_toast("Il campo Articolo è obbligatorio.")
                return None
            try:
                q, mn = _num(v["quantita"].get()), _num(v["min"].get())
                mx, pr = _num(v["max"].get()), _num(v["prezzo"].get())
            except ValueError as ex:
                self.show_custom_warning("Valore non valido", str(ex))
                return None
            if min(q, mn, mx, pr) < 0:
                self.show_custom_warning("Valore non valido", "Quantità, scorte e prezzo non possono essere negativi.")
                return None
            if pr > 9_000:
                self.show_custom_warning("Valore non valido", "Il prezzo unitario non può superare 9.000 €.")
                return None
            if max(q, mn, mx) > 9_00:
                self.show_custom_warning("Valore non valido", "Le quantità non possono superare 900.")
                return None
            if mx and mx < mn:
                self.show_custom_warning("Scorte incoerenti", "La quantità massima non può essere inferiore alla minima\n(lascia 0 se non vuoi un massimo).")
                return None
            if _parse_data(v["data"].get()) is None:
                self.show_custom_warning("Data non valida", "Usa il formato gg-mm-aaaa (es. 30-09-2026).")
                return None
            scad = v["scadenza"].get().strip()
            if scad and _parse_data(scad) is None:
                self.show_custom_warning("Scadenza non valida", "Usa il formato gg-mm-aaaa (es. 30-10-2026) oppure lascia vuoto.")
                return None
            desc = txt_desc.get("1.0", "end").strip()
            if len(desc) > 45:
                self.show_custom_warning("Limite superato", "La descrizione può avere al massimo 45 caratteri.")
                return None
            return dict(nome=nome, codice=v["codice"].get().strip(), categoria=v["categoria"].get().strip(),
                        descrizione=desc, unita=v["unita"].get().strip() or "pz",
                        quantita=q, qta_min=mn, qta_max=mx, prezzo=pr,
                        scadenza=_parse_data(scad).strftime("%d-%m-%Y") if scad else "", data=v["data"].get().strip())

        def registra(chiudi_dopo):
            d = leggi()
            if d is None:
                return
            if articolo:
                mod = any(articolo.get(k) != d[k] for k in d if k != "data")
                if d["data"] == data_originale and mod:
                    d["data"] = _oggi()
                if abs(articolo["quantita"] - d["quantita"]) > 1e-9:
                    articolo["movimenti"].append({"data": _oggi(), "delta": round(d["quantita"] - articolo["quantita"], 3),
                                                  "qta": d["quantita"], "nota": "Rettifica da modifica"})
                    articolo["movimenti"] = articolo["movimenti"][-100:]
                articolo.update(d)
                id_ = articolo["id"]
                self.show_toast("Articolo modificato correttamente!")
            else:
                if any(a["nome"].lower() == d["nome"].lower() and a["categoria"].lower() == d["categoria"].lower() for a in art):
                    if not self.show_custom_askyesno("Articolo già presente",
                                                     f"Esiste già «{d['nome']}» in questa categoria.\nAggiungerlo comunque?"):
                        return
                nuovo = normalizza_articolo(d)
                if d["quantita"] > 0:
                    nuovo["movimenti"].append({"data": d["data"], "delta": d["quantita"], "qta": d["quantita"], "nota": "Carico iniziale"})
                art.append(nuovo)
                id_ = nuovo["id"]
                self.show_toast("Articolo aggiunto correttamente!")
            if d["categoria"] and d["categoria"] not in tutte_categorie():
                stato_dati["categorie"].append(d["categoria"])
            salva()
            aggiorna_categorie()
            ridisegna([id_])
            f.destroy()
            if not chiudi_dopo:
                apri_form()

        bt = tk.Frame(f, bg=self.COLOR_TOPLEVEL)
        bt.grid(row=13, column=0, columnspan=3, pady=14)
        crea_btn(bt, "salva", "Salva", lambda: registra(True), "💾").pack(side="left", padx=4)
        if not articolo:
            crea_btn(bt, "aggiungi", "Salva e inserisci altro", lambda: registra(False), "➕").pack(side="left", padx=4)
        crea_btn(bt, "chiudi", "Chiudi", f.destroy, "❌").pack(side="left", padx=4)
        _mostra(f, root, fw, fh)

        def _focus_articolo():
            try:
                if f.winfo_exists():
                    e_nome.focus_force()
                    e_nome.icursor("end")
            except tk.TclError:
                pass
        f.after(50, _focus_articolo)
        f.after(250, _focus_articolo)

    def modifica_sel(event=None):
        s = sel_articoli()
        if not s:
            self.show_toast("Seleziona un articolo da modificare.")
            return
        if len(s) > 1:
            modifica_multipla(s)
        else:
            apri_form(s[0])

    def modifica_multipla(s):
        if finestra_aperta("_edit_win"):
            return
        f = tk.Toplevel(root, bg=self.COLOR_TOPLEVEL)
        root._edit_win = f
        f.withdraw()
        f.transient(root)
        f.title(f"Modifica {len(s)} articoli")
        f.resizable(False, False)
        f.columnconfigure(1, weight=1)
        f.bind("<Escape>", lambda e: f.destroy())
        v = {k: tk.StringVar() for k in ("categoria", "unita", "min", "max", "prezzo", "data")}
        tk.Label(f, text=f"Modifica di {len(s)} articoli selezionati", bg=self.COLOR_TOPLEVEL,
                 fg=self.TEXT_COLOR, font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(12, 2))
        tk.Label(f, text="Compila solo i campi da cambiare: quelli lasciati vuoti restano invariati.",
                 bg=self.COLOR_TOPLEVEL, fg="gray", font=("Arial", 8)).grid(row=1, column=0, columnspan=2, pady=(0, 8))

        def riga(r, testo, widget):
            tk.Label(f, text=testo, bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR).grid(row=r, column=0, sticky="e", padx=(14, 6), pady=4)
            widget.grid(row=r, column=1, sticky="w", padx=(0, 14), pady=4)
            return widget
        c_cat = riga(2, "Categoria", ttk.Combobox(f, textvariable=v["categoria"], values=[""] + tutte_categorie(), width=30, state="readonly",                      style="Border.TCombobox"))
        c_cat.config(validate="key", validatecommand=(f.register(lambda P: len(P) <= 30), "%P"))
        riga(3, "Unità di misura", ttk.Combobox(f, textvariable=v["unita"], values=UNITA, width=12, style="Border.TCombobox"))
        riga(4, "Quantità minima (scorta)", ttk.Entry(f, textvariable=v["min"], width=14))
        riga(5, "Quantità massima (scorta)", ttk.Entry(f, textvariable=v["max"], width=14))
        riga(6, "Prezzo unitario €", ttk.Entry(f, textvariable=v["prezzo"], width=14))
        tk.Label(f, text="Data", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR).grid(row=7, column=0, sticky="e", padx=(14, 6), pady=4)
        fr_d = tk.Frame(f, bg=self.COLOR_TOPLEVEL)
        fr_d.grid(row=7, column=1, sticky="w", pady=4)
        e_data = ttk.Entry(fr_d, textvariable=v["data"], width=12)
        e_data.pack(side="left")
        b_cal = crea_icona_cal(fr_d)
        b_cal.pack(side="left", padx=4)
        b_cal.bind("<Button-1>", lambda e: self.mostra_calendario_popup_semplice(e_data, v["data"]))
        tk.Label(f, text="Quantità, nome, codice e descrizione restano quelli di ogni articolo.\n"
                         "Massimo: scrivi 0 per toglierlo. Data vuota = oggi.",
                 bg=self.COLOR_TOPLEVEL, fg="gray", font=("Arial", 8), justify="left").grid(row=8, column=0, columnspan=2, padx=14, sticky="w")

        def registra():
            cat, um = v["categoria"].get().strip(), v["unita"].get().strip()
            try:
                mn, mx, pr = (_num(v[k].get(), None) for k in ("min", "max", "prezzo"))
            except ValueError as ex:
                self.show_custom_warning("Valore non valido", str(ex))
                return
            nuovi = [x for x in (mn, mx, pr) if x is not None]
            if nuovi and min(nuovi) < 0:
                self.show_custom_warning("Valore non valido", "Scorte e prezzo non possono essere negativi.")
                return
            if pr is not None and pr > 9_000:
                self.show_custom_warning("Valore non valido", "Il prezzo unitario non può superare 9.000 €.")
                return
            if any(x is not None and x > 900 for x in (mn, mx)):
                self.show_custom_warning("Valore non valido", "Le quantità non possono superare 900.")
                return
            data = v["data"].get().strip()
            if data and _parse_data(data) is None:
                self.show_custom_warning("Data non valida", "Usa il formato gg-mm-aaaa (es. 30-09-2026).")
                return
            if not (cat or um or nuovi or data):
                self.show_toast("Nessun campo da modificare.")
                return
            for a in s:
                n_mn = mn if mn is not None else a["qta_min"]
                n_mx = mx if mx is not None else a["qta_max"]
                if n_mx and n_mx < n_mn:
                    self.show_custom_warning("Scorte incoerenti",
                                             f"Per «{a['nome']}» la quantità massima risulterebbe inferiore alla minima.")
                    return
            if cat and cat not in tutte_categorie():
                stato_dati["categorie"].append(cat)
            for a in s:
                if cat:
                    a["categoria"] = cat
                if um:
                    a["unita"] = um
                if mn is not None:
                    a["qta_min"] = mn
                if mx is not None:
                    a["qta_max"] = mx
                if pr is not None:
                    a["prezzo"] = pr
                a["data"] = data or _oggi()
            salva()
            aggiorna_categorie()
            ridisegna([a["id"] for a in s])
            f.destroy()
            self.show_toast(f"{len(s)} articoli modificati correttamente!")

        bt = tk.Frame(f, bg=self.COLOR_TOPLEVEL)
        bt.grid(row=9, column=0, columnspan=2, pady=14)
        crea_btn(bt, "salva", "Salva", registra, "💾").pack(side="left", padx=4)
        crea_btn(bt, "chiudi", "Chiudi", f.destroy, "❌").pack(side="left", padx=4)
        f.bind("<Return>", lambda e: registra())
        _mostra(f, root, 520, 400)
        c_cat.focus_set()

    def cancella_sel(event=None):
        s = sel_articoli()
        if not s:
            self.show_toast("Nessun articolo selezionato.")
            return
        testo = f"Eliminare l'articolo '{s[0]['nome']}'?" if len(s) == 1 else f"Eliminare i {len(s)} articoli selezionati?"
        if not self.show_custom_askyesno("Elimina articolo", testo):
            return
        ids = {a["id"] for a in s}
        art[:] = [a for a in art if a["id"] not in ids]
        salva()
        aggiorna_categorie()
        ridisegna([])
        self.show_toast("Articolo cancellato con successo !" if len(s) == 1 else f"{len(s)} articoli cancellati.")

    def duplica_sel():
        s = sel_articoli()
        if not s:
            self.show_toast("Seleziona un articolo.")
            return
        nuovi = []
        for a in s:
            n = normalizza_articolo({**a, "id": None, "nome": a["nome"] + " (copia)", "movimenti": [], "data": _oggi()})
            art.append(n)
            nuovi.append(n["id"])
        salva()
        ridisegna(nuovi)
        self.show_toast("Articolo duplicato." if len(s) == 1 else f"{len(s)} articoli duplicati.")

    def gestisci_categorie():
        if getattr(root, "_cat_win", None) and root._cat_win.winfo_exists():
            root._cat_win.lift()
            return
        d = tk.Toplevel(root, bg=self.COLOR_TOPLEVEL)
        root._cat_win = d
        d.withdraw()
        d.transient(root)
        d.title("Gestisci categorie")
        d.minsize(600, 400)
        d.bind("<Escape>", lambda e: d.destroy())
        d.columnconfigure(0, weight=1)
        d.rowconfigure(1, weight=1)
        tk.Label(d, text="Categorie del magazzino", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                 font=("Arial", 11, "bold")).grid(row=0, column=0, pady=(12, 6))
        fr = ttk.Frame(d)
        fr.grid(row=1, column=0, sticky="nsew", padx=12)
        fr.columnconfigure(0, weight=1)
        fr.rowconfigure(0, weight=1)
        tv = ttk.Treeview(fr, columns=("Categoria", "Articoli"), show="headings", selectmode="browse")
        tv.heading("Categoria", text="Categoria", command=lambda: self.treeview_sort_column(tv, "Categoria", False))
        tv.heading("Articoli", text="Articoli", command=lambda: self.treeview_sort_column(tv, "Articoli", False))
        tv.column("Categoria", width=300, anchor="w")
        tv.column("Articoli", width=80, anchor="e")
        sb = ttk.Scrollbar(fr, orient="vertical", command=tv.yview, style="Vertical.TScrollbar")
        tv.configure(yscrollcommand=sb.set)
        tv.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        tk.Label(d, text="Nuova categoria / nuovo nome:", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR).grid(row=2, column=0, sticky="w", padx=12, pady=(10, 2))
        v_nome = tk.StringVar()
        e_nome = ttk.Entry(d, textvariable=v_nome)
        e_nome.grid(row=3, column=0, sticky="ew", padx=12)
        e_nome.config(validate="key", validatecommand=(d.register(lambda P: len(P) <= 40), "%P"))

        def riempi():
            tv.delete(*tv.get_children())
            for c in tutte_categorie():
                tv.insert("", "end", iid=c, values=(c, sum(1 for a in art if a["categoria"] == c)))
            self.treeview_sort_column(tv, "Categoria", False)

        def dopo_modifica():
            salva()
            aggiorna_categorie()
            ridisegna()
            riempi()

        def esiste(nome):
            return any(c.lower() == nome.lower() for c in tutte_categorie())

        def aggiungi():
            nome = v_nome.get().strip()
            if not nome:
                self.show_toast("Scrivi il nome della categoria.")
                return
            if esiste(nome):
                self.show_toast("Categoria già presente.")
                return
            stato_dati["categorie"].append(nome)
            v_nome.set("")
            dopo_modifica()
            self.show_toast("Categoria aggiunta.")

        def rinomina():
            sel = tv.selection()
            nome = v_nome.get().strip()
            if not sel:
                self.show_toast("Seleziona la categoria da rinominare.")
                return
            if not nome:
                self.show_toast("Scrivi il nuovo nome.")
                return
            vecchio = sel[0]
            if nome == vecchio:
                return
            if esiste(nome) and nome.lower() != vecchio.lower():
                if not self.show_custom_askyesno("Unisci categorie",
                                                 f"«{nome}» esiste già.\nUnire gli articoli di «{vecchio}» in «{nome}»?"):
                    return
            stato_dati["categorie"] = [c for c in stato_dati["categorie"] if c != vecchio]
            if not esiste(nome):
                stato_dati["categorie"].append(nome)
            for a in art:
                if a["categoria"] == vecchio:
                    a["categoria"] = nome
            if var_cat.get() == vecchio:
                var_cat.set(nome)
            v_nome.set("")
            dopo_modifica()
            self.show_toast("Categoria rinominata.")

        def elimina():
            sel = tv.selection()
            if not sel:
                self.show_toast("Seleziona la categoria da eliminare.")
                return
            c = sel[0]
            n = sum(1 for a in art if a["categoria"] == c)
            msg = f"Eliminare la categoria «{c}»?"
            if n:
                msg += f"\n{n} articoli resteranno senza categoria."
            if not self.show_custom_askyesno("Elimina categoria", msg):
                return
            stato_dati["categorie"] = [x for x in stato_dati["categorie"] if x != c]
            for a in art:
                if a["categoria"] == c:
                    a["categoria"] = ""
            if var_cat.get() == c:
                var_cat.set(TUTTE_CAT)
            dopo_modifica()
            self.show_toast("Categoria eliminata.")

        def suggerite():
            if getattr(d, "_sugg_win", None) and d._sugg_win.winfo_exists():
                d._sugg_win.lift()
                return
            w = tk.Toplevel(d, bg=self.COLOR_TOPLEVEL)
            d._sugg_win = w
            w.withdraw()
            w.transient(d)
            w.title("Categorie suggerite")
            w.bind("<Escape>", lambda e: w.destroy())
            tk.Label(w, text="Categorie suggerite", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                     font=("Arial", 11, "bold")).pack(pady=(12, 2))
            tk.Label(w, text="Per che uso ti serve il magazzino?", bg=self.COLOR_TOPLEVEL,
                     fg="gray", font=("Arial", 9)).pack()
            profili = {"Casa / Dispensa": list(_app.CATEGORIE_PREDEFINITE)}
            profili.update(PROFILI_CATEGORIE)
            v_prof = tk.StringVar(value=list(profili)[0])
            cb = ttk.Combobox(w, textvariable=v_prof, values=list(profili), state="readonly", width=32, style="Border.TCombobox")
            cb.pack(pady=8)
            v_tutte = tk.BooleanVar(value=True)
            chk_tutte = ttk.Checkbutton(w, text="Tutte / Nessuna", variable=v_tutte,
                                        command=lambda: seleziona_tutte(v_tutte.get()))
            chk_tutte.pack(anchor="w", padx=20, pady=(0, 4))
            fr_l = tk.Frame(w, bg=self.COLOR_TOPLEVEL)
            fr_l.pack(fill="both", expand=True, padx=14)
            cv = tk.Canvas(fr_l, bg=self.COLOR_TOPLEVEL, highlightthickness=0)
            sb_l = ttk.Scrollbar(fr_l, orient="vertical", command=cv.yview, style="Vertical.TScrollbar")
            cv.configure(yscrollcommand=sb_l.set)
            sb_l.pack(side="right", fill="y")
            cv.pack(side="left", fill="both", expand=True)
            box = tk.Frame(cv, bg=self.COLOR_TOPLEVEL)
            cv.create_window((0, 0), window=box, anchor="nw")
            box.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
            cv.bind("<MouseWheel>", lambda e: cv.yview_scroll(-1 if e.delta > 0 else 1, "units"))
            cv.bind("<Button-4>", lambda e: cv.yview_scroll(-1, "units"))
            cv.bind("<Button-5>", lambda e: cv.yview_scroll(1, "units"))
            scelte = {}

            def mostra(event=None):
                for wd in box.winfo_children():
                    wd.destroy()
                scelte.clear()
                for nome in profili[v_prof.get()]:
                    gia = esiste(nome)
                    var = tk.BooleanVar(value=not gia)
                    scelte[nome] = var
                    chk = ttk.Checkbutton(box, text=nome + ("   (già presente)" if gia else ""),
                                          variable=var, state="disabled" if gia else "normal",
                                          command=aggiorna_selettore)
                    chk.pack(anchor="w", pady=1)
                    chk.bind("<MouseWheel>", lambda e: cv.yview_scroll(-1 if e.delta > 0 else 1, "units"))
                    chk.bind("<Button-4>", lambda e: cv.yview_scroll(-1, "units"))
                    chk.bind("<Button-5>", lambda e: cv.yview_scroll(1, "units"))
                cv.yview_moveto(0)
                aggiorna_selettore()

            def seleziona_tutte(val):
                for n, v in scelte.items():
                    if not esiste(n):
                        v.set(val)

            def aggiorna_selettore():
                libere = [v for n, v in scelte.items() if not esiste(n)]
                v_tutte.set(bool(libere) and all(v.get() for v in libere))

            def aggiungi_scelte():
                nuove = [n for n, v in scelte.items() if v.get() and not esiste(n)]
                if not nuove:
                    self.show_toast("Nessuna nuova categoria selezionata.")
                    return
                stato_dati["categorie"].extend(nuove)
                dopo_modifica()
                self.show_toast(f"{len(nuove)} categorie aggiunte.")
                w.destroy()

            cb.bind("<<ComboboxSelected>>", mostra)
            mostra()
            bs = tk.Frame(w, bg=self.COLOR_TOPLEVEL)
            bs.pack(pady=10)
            crea_btn(bs, "aggiungi", "Aggiungi selezionate", aggiungi_scelte, "➕").pack(side="left", padx=3)
            crea_btn(bs, "chiudi", "Chiudi", w.destroy, "❌").pack(side="left", padx=3)
            w.minsize(440, 560)
            _mostra(w, d, 440, 560)

        tv.bind("<<TreeviewSelect>>", lambda e: v_nome.set(tv.selection()[0]) if tv.selection() else None)
        e_nome.bind("<Return>", lambda e: aggiungi())
        tv.bind("<Delete>", lambda e: elimina())
        bt = tk.Frame(d, bg=self.COLOR_TOPLEVEL)
        bt.grid(row=4, column=0, pady=10)
        crea_btn(bt, "aggiungi", "Aggiungi", aggiungi, "➕").pack(side="left", padx=3)
        crea_btn(bt, "modifica", "Rinomina", rinomina, "✏️").pack(side="left", padx=3)
        crea_btn(bt, "delete", "Elimina", elimina, "🗑️").pack(side="left", padx=3)
        crea_btn(bt, "sparkles", "Suggerite", suggerite, "💡").pack(side="left", padx=3)
        crea_btn(bt, "chiudi", "Chiudi", d.destroy, "❌").pack(side="left", padx=3)
        riempi()
        _mostra(d, root, 600, 400)

    def applica_movimento(a, delta, nota):
        a["quantita"] = round(a["quantita"] + delta, 3)
        a["data"] = _oggi()
        a["movimenti"].append({"data": _oggi(), "delta": round(delta, 3), "qta": a["quantita"], "nota": nota})
        a["movimenti"] = a["movimenti"][-100:]

    def movimento_sel(event=None):
        if finestra_aperta("_edit_win"):
            return
        s = sel_articoli()
        if not s:
            self.show_toast("Seleziona un articolo.")
            return
        multi = len(s) > 1
        a = s[0]
        d = tk.Toplevel(root, bg=self.COLOR_TOPLEVEL)
        root._edit_win = d
        d.withdraw()
        d.transient(root)
        d.title("Carico / Scarico" + (f" — {len(s)} articoli" if multi else ""))
        d.resizable(False, False)
        d.bind("<Escape>", lambda e: d.destroy())
        if multi:
            tk.Label(d, text=f"{len(s)} articoli selezionati", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                     font=("Arial", 11, "bold")).pack(pady=(12, 0))
            tk.Label(d, text="La stessa quantità viene applicata a ciascun articolo.", bg=self.COLOR_TOPLEVEL,
                     fg="gray").pack(pady=(0, 8))
        else:
            tk.Label(d, text=a["nome"], bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR, font=("Arial", 11, "bold")).pack(pady=(12, 0))
            tk.Label(d, text=f"Giacenza attuale: {_fmt_q(a['quantita'])} {a['unita']}", bg=self.COLOR_TOPLEVEL,
                     fg="gray").pack(pady=(0, 8))
        tipo = tk.StringVar(value="carico")
        v_riord = tk.BooleanVar(value=False)
        fr = tk.Frame(d, bg=self.COLOR_TOPLEVEL)
        fr.pack()
        for _t, _v in (("➕ Carico (entrata)", "carico"), ("➖ Scarico (uscita)", "scarico")):
            tk.Radiobutton(fr, text=_t, variable=tipo, value=_v, bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                           selectcolor=self.COLOR_WIDGET_BG, activebackground=self.COLOR_TOPLEVEL,
                           activeforeground=self.TEXT_COLOR, highlightthickness=0, bd=0,
                           command=lambda: aggiorna_campi()).pack(side="left", padx=8)
        fq = tk.Frame(d, bg=self.COLOR_TOPLEVEL)
        fq.pack(pady=8)
        tk.Label(fq, text="Quantità:", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR).grid(row=0, column=0, padx=4, pady=3)
        vq = tk.StringVar(value="1" if multi else (_fmt_q(calcola_stato(a)[2]) if calcola_stato(a)[2] else "1"))
        eq = ttk.Entry(fq, textvariable=vq, width=10)
        eq.grid(row=0, column=1, pady=3, sticky="w")
        tk.Label(fq, text="Nota:", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR).grid(row=1, column=0, padx=4, pady=3)
        vn = tk.StringVar()
        ttk.Entry(fq, textvariable=vn, width=28).grid(row=1, column=1, pady=3)
        chk_riord = None
        if multi:
            chk_riord = ttk.Checkbutton(d, text="Carico = quantità di riordino di ciascun articolo\n(solo quelli sotto scorta)",
                                        variable=v_riord, command=lambda: aggiorna_campi())
            chk_riord.pack(pady=(0, 4))

        def aggiorna_campi():
            carico = tipo.get() == "carico"
            if chk_riord is not None:
                chk_riord.config(state="normal" if carico else "disabled")
            eq.config(state="disabled" if (multi and carico and v_riord.get()) else "normal")

        def ok():
            nota = vn.get().strip()
            movimenti = []
            if multi and tipo.get() == "carico" and v_riord.get():
                movimenti = [(x, calcola_stato(x)[2]) for x in s if calcola_stato(x)[2] > 0]
                if not movimenti:
                    self.show_toast("Nessuno degli articoli selezionati è da riordinare.")
                    return
            else:
                try:
                    q = _num(vq.get())
                except ValueError:
                    self.show_toast("Quantità non valida.")
                    return
                if q <= 0:
                    self.show_toast("Inserisci una quantità maggiore di zero.")
                    return
                if tipo.get() == "scarico":
                    scarsi = [x for x in s if q > x["quantita"] + 1e-9]
                    if scarsi and len(scarsi) == len(s):
                        if multi:
                            self.show_custom_warning("Giacenza insufficiente",
                                                     "Nessun articolo selezionato ha una giacenza sufficiente.")
                        else:
                            self.show_custom_warning("Giacenza insufficiente",
                                                     f"Disponibili solo {_fmt_q(a['quantita'])} {a['unita']}.")
                        return
                    if scarsi:
                        elenco = ", ".join(x["nome"] for x in scarsi[:5]) + ("…" if len(scarsi) > 5 else "")
                        if not self.show_custom_askyesno("Giacenza insufficiente",
                                                         f"{len(scarsi)} articoli non hanno giacenza sufficiente:\n{elenco}\n\n"
                                                         "Scaricare solo gli altri?"):
                            return
                    movimenti = [(x, -q) for x in s if x not in scarsi]
                else:
                    movimenti = [(x, q) for x in s]
            sforati = [x for x, delta in movimenti if x["quantita"] + delta > 900]
            if sforati:
                self.show_custom_warning("Quantità non valida", f"La giacenza non può superare 900 («{sforati[0]['nome']}»).")
                return
            for x, delta in movimenti:
                applica_movimento(x, delta, nota or ("Carico" if delta > 0 else "Scarico"))
            salva()
            ridisegna([x["id"] for x in s])
            d.destroy()
            critici = sum(1 for x, _ in movimenti if calcola_stato(x)[1] in ("sotto", "esaurito"))
            if multi:
                msg = f"Movimento registrato su {len(movimenti)} articoli."
                if critici:
                    msg += f" Attenzione: {critici} sotto scorta o esauriti!"
            else:
                st = calcola_stato(a)
                msg = "Movimento registrato." + (f" Attenzione: {st[0].lower()}!" if st[1] in ("sotto", "esaurito") else "")
            self.show_toast(msg)
        bt = tk.Frame(d, bg=self.COLOR_TOPLEVEL)
        bt.pack(pady=6)
        crea_btn(bt, "salva", "Registra", ok, "💾").pack(side="left", padx=4)
        crea_btn(bt, "chiudi", "Chiudi", d.destroy, "❌").pack(side="left", padx=4)
        d.bind("<Return>", lambda e: ok())
        aggiorna_campi()
        _mostra(d, root, 420 if multi else 400, 320 if multi else 250)
        eq.focus_set()
        eq.select_range(0, "end")

    def storico_sel():
        if finestra_aperta("_storico_win"):
            return
        s = sel_articoli()
        if not s:
            self.show_toast("Seleziona un articolo.")
            return
        multi = len(s) > 1
        d = tk.Toplevel(root, bg=self.COLOR_TOPLEVEL)
        root._storico_win = d
        d.withdraw()
        d.transient(root)
        d.title(f"Storico movimenti — {len(s)} articoli" if multi else f"Storico movimenti — {s[0]['nome']}")
        W, H = (820, 420) if multi else (560, 380)
        d.minsize(W, H)
        d.bind("<Escape>", lambda e: d.destroy())
        fr = ttk.Frame(d)
        fr.pack(fill="both", expand=True, padx=10, pady=10)
        cols = (("Articolo", 200),) if multi else ()
        cols += (("Data", 90), ("Movimento", 90), ("Giacenza", 90), ("Nota", 270))
        tv = ttk.Treeview(fr, columns=[c for c, _ in cols], show="headings")
        for c, w in cols:
            tv.heading(c, text=c, command=lambda _c=c: self.treeview_sort_column(tv, _c, False))
            tv.column(c, width=w, anchor="w")
        sb = ttk.Scrollbar(fr, orient="vertical", command=tv.yview, style="Vertical.TScrollbar")
        tv.configure(yscrollcommand=sb.set)
        tv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        righe = [(x, m) for x in s for m in reversed(x["movimenti"])]
        righe.sort(key=lambda r: _parse_data(r[1].get("data")) or datetime.date.min, reverse=True)
        for x, m in righe:
            vals = (m.get("data", ""), ("+" if m["delta"] > 0 else "") + _fmt_q(m["delta"]),
                    _fmt_q(m.get("qta", "")), m.get("nota", ""))
            tv.insert("", "end", values=((x["nome"],) if multi else ()) + vals)
        if not righe:
            tv.insert("", "end", values=("",) * (len(cols) - 1) + ("Nessun movimento registrato.",))
        crea_btn(d, "chiudi", "Chiudi", d.destroy, "❌").pack(pady=(0, 10))
        _mostra(d, root, W, H)

    def suggerisci_scorta():
        if finestra_aperta("_scorta_win"):
            return
        base = sel_articoli() or filtrati()
        righe = []
        for a in base:
            r = scorta_min_suggerita(a)
            if r and abs(r[1] - a["qta_min"]) > 1e-9:
                righe.append((a, r[0] * 7, r[1]))
        if not righe:
            self.show_toast("Nessuna scorta da aggiornare (servono almeno 2 scarichi negli ultimi 90 giorni).")
            return
        d = tk.Toplevel(root, bg=self.COLOR_TOPLEVEL)
        root._scorta_win = d
        d.withdraw()
        d.transient(root)
        d.title("Scorta minima suggerita")
        d.minsize(800, 400)
        d.bind("<Escape>", lambda e: d.destroy())
        d.columnconfigure(0, weight=1)
        d.rowconfigure(1, weight=1)
        tk.Label(d, text="Scorta minima suggerita = consumo medio degli ultimi 90 giorni × 14 giorni di copertura",
                 bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR, font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=8)
        fr = ttk.Frame(d)
        fr.grid(row=1, column=0, sticky="nsew", padx=10)
        fr.columnconfigure(0, weight=1)
        fr.rowconfigure(0, weight=1)
        cols = ("Articolo", "U.M.", "Consumo/sett.", "Min attuale", "Min suggerita", "Max", "Nota")
        tv = ttk.Treeview(fr, columns=cols, show="headings", selectmode="extended")
        for c, w, an in zip(cols, (220, 55, 105, 95, 105, 70, 120), ("w", "center", "e", "e", "e", "e", "w")):
            tv.heading(c, text=c, command=lambda _c=c: self.treeview_sort_column(tv, _c, False))
            tv.column(c, width=w, anchor=an)
        sb = ttk.Scrollbar(fr, orient="vertical", command=tv.yview, style="Vertical.TScrollbar")
        tv.configure(yscrollcommand=sb.set)
        tv.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")

        def sfora(a, sug):
            return bool(a["qta_max"]) and sug > a["qta_max"]

        for a, sett, sug in righe:
            tv.insert("", "end", iid=a["id"],
                      values=(a["nome"], a["unita"], _fmt_q(round(sett, 2)), _fmt_q(a["qta_min"]), _fmt_q(sug),
                              _fmt_q(a["qta_max"]) if a["qta_max"] else "", "supera il max" if sfora(a, sug) else ""))
        tv.selection_set([a["id"] for a, _, sug in righe if not sfora(a, sug)])

        def applica():
            ids = set(tv.selection())
            n = 0
            for a, _, sug in righe:
                if a["id"] in ids and not sfora(a, sug):
                    a["qta_min"] = sug
                    a["data"] = _oggi()
                    n += 1
            if not n:
                self.show_toast("Nessuna riga da applicare.")
                return
            salva()
            ridisegna([a["id"] for a, _, _ in righe])
            d.destroy()
            self.show_toast(f"Scorta minima aggiornata su {n} articoli.")

        bt = tk.Frame(d, bg=self.COLOR_TOPLEVEL)
        bt.grid(row=2, column=0, pady=10)
        crea_btn(bt, "salva", "Applica ai selezionati", applica, "💾").pack(side="left", padx=4)
        crea_btn(bt, "chiudi", "Chiudi", d.destroy, "❌").pack(side="left", padx=4)
        _mostra(d, root, 800, 440)

    def righe_riordino():
        out = []
        for a in sorted(art, key=lambda x: (x["categoria"].lower(), x["nome"].lower())):
            st, tag, ordina = calcola_stato(a)
            if ordina > 0:
                out.append((a, ordina))
        return out

    def testo_riordino():
        righe = righe_riordino()
        if not righe:
            return ""
        
        cols = [
            ("Articolo", "<", 27),
            ("Categoria", "<", 15),
            ("Qtà", ">", None),
            ("Min", ">", None),
            ("Max", ">", None),
            ("Ordina", "<", None),
            ("Prezzo", ">", None),
            ("Costo", ">", None),
            ("Scadenza", "<", None),
            ("Data", "<", None)
        ]
        
        tab_righe = []
        tot = 0.0
        for a, o in righe:
            costo = o * a["prezzo"]
            tot += costo
            tab_righe.append([
                a["nome"],
                a["categoria"],
                _fmt_q(a["quantita"]),
                _fmt_q(a["qta_min"]),
                _fmt_q(a["qta_max"]) if a["qta_max"] else "-",
                _fmt_q(o) + " " + a["unita"],
                _fmt_eur(a["prezzo"]),
                _fmt_eur(costo),
                stato_scadenza(a)[2] or "-",
                a.get("data", "")
            ])
            
        titolo = f"LISTA RIORDINO MAGAZZINO — {_oggi()}"
        return _tabella_txt(titolo, cols, tab_righe, "TOTALE STIMATO", _fmt_eur(tot), col_tot=7)

    def apri_riordino():
        if getattr(root, "_riordino_win", None) and root._riordino_win.winfo_exists():
            root._riordino_win.lift()
            return
        if not righe_riordino():
            self.show_toast("Nessun articolo da riordinare: tutte le scorte sono sopra il minimo.")
            return
        d = tk.Toplevel(root, bg=self.COLOR_TOPLEVEL)
        root._riordino_win = d
        d.withdraw()
        d.transient(root)
        d.title("Lista riordino scorte")
        d.minsize(1100, 400)
        d.bind("<Escape>", lambda e: d.destroy())
        d.columnconfigure(0, weight=1)
        d.rowconfigure(1, weight=1)
        tk.Label(d, text="Articoli da riordinare (quantità = massimo − giacenza; se manca il massimo si riporta al doppio del minimo)",
                 bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR, font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=8)
        fr = ttk.Frame(d)
        fr.grid(row=1, column=0, sticky="nsew", padx=10)
        fr.columnconfigure(0, weight=1)
        fr.rowconfigure(0, weight=1)
        cols = ("Articolo", "Categoria", "Qtà", "Min", "Max", "Da ordinare", "U.M.", "Prezzo", "Costo stimato", "Scadenza", "Data")
        tv = ttk.Treeview(fr, columns=cols, show="headings", selectmode="extended")
        for c, w, an in zip(cols, (200, 110, 65, 65, 65, 95, 55, 90, 110, 150, 85), ("w", "w", "e", "e", "e", "e", "center", "e", "e", "center", "center")):
            tv.heading(c, text=c, command=lambda _c=c: self.treeview_sort_column(tv, _c, False))
            tv.column(c, width=w, anchor=an)
        sb = ttk.Scrollbar(fr, orient="vertical", command=tv.yview, style="Vertical.TScrollbar")
        tv.configure(yscrollcommand=sb.set)
        tv.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")
        tv.tag_configure("esaurito", foreground=col_red)
        tv.tag_configure("sotto", foreground=col_org)
        lbl = tk.Label(d, text="", anchor="e", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR, font=("Arial", 10, "bold"))
        lbl.grid(row=2, column=0, sticky="ew", padx=12, pady=4)

        def riempi():
            tv.delete(*tv.get_children())
            tot = 0.0
            for a, o in righe_riordino():
                costo = o * a["prezzo"]
                tot += costo
                tv.insert("", "end", iid=a["id"], tags=(calcola_stato(a)[1],),
                          values=(a["nome"], a["categoria"], _fmt_q(a["quantita"]), _fmt_q(a["qta_min"]),
                                  _fmt_q(a["qta_max"]) if a["qta_max"] else "", _fmt_q(o), a["unita"],
                                  _fmt_eur(a["prezzo"]), _fmt_eur(costo), stato_scadenza(a)[2], a.get("data", "")))
            lbl.config(text=f"Costo totale stimato del riordino: {_fmt_eur(tot)}")
            if not tv.get_children():
                d.destroy()

        def carica_ricevuti():
            ids = list(tv.selection()) or list(tv.get_children())
            if not ids:
                return
            if not self.show_custom_askyesno("Merce ricevuta",
                                             f"Registrare il carico di {len(ids)} articoli fino alla scorta prevista?\n"
                                             "(Se non selezioni righe vengono caricati tutti.)"):
                return
            for id_ in ids:
                a = trova(id_)
                if a:
                    o = calcola_stato(a)[2]
                    if o > 0:
                        applica_movimento(a, o, "Riordino ricevuto")
            salva()
            ridisegna()
            riempi()
            self.show_toast("Carichi registrati.")

        def esporta_ordine():
            t = testo_riordino()
            if t:
                anteprima_testo(d, "Esporta lista riordino — StockBox", t, "Riordino")

        riempi()
        bt = tk.Frame(d, bg=self.COLOR_TOPLEVEL)
        bt.grid(row=3, column=0, pady=8)
        crea_btn(bt, "archivia", "Merce arrivata", carica_ricevuti, "📥").pack(side="left", padx=4)
        crea_btn(bt, "stampa", "Esporta / Stampa", esporta_ordine, "🖨️").pack(side="left", padx=4)
        crea_btn(bt, "chiudi", "Chiudi", d.destroy, "❌").pack(side="left", padx=4)
        if d.winfo_exists():
            _mostra(d, root, 1200, 520)

    def anteprima_testo(parent, titolo, testo, nome_base):
        chiave = "_anteprima_" + nome_base
        if getattr(root, chiave, None) and getattr(root, chiave).winfo_exists():
            getattr(root, chiave).lift()
            return
        pv = tk.Toplevel(parent, bg=self.COLOR_TOPLEVEL)
        setattr(root, chiave, pv)
        pv.withdraw()
        pv.title(titolo)
        pv.transient(parent)
        pv.bind("<Escape>", lambda e: pv.destroy())
        wa, ha = 1200, 600
        pv.minsize(800, 400)

        def do_pdf():
            f_path = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
                                                  initialdir=EXPORT_FILES, initialfile=f"{nome_base}_{_oggi()}.pdf",
                                                  confirmoverwrite=False, parent=pv)
            if not f_path:
                return
            try:
                import pymupdf as fitz
                doc = fitz.open()
                pw, ph, mg, fs = 842, 595, 30, 7
                page = doc.new_page(width=pw, height=ph)
                y = mg
                for riga in testo.split("\n"):
                    if y > ph - mg:
                        page = doc.new_page(width=pw, height=ph)
                        y = mg
                    page.insert_text((mg, y), riga, fontname="cour", fontsize=fs)
                    y += fs + 2
                doc.save(f_path)
                doc.close()
                self.show_toast("PDF salvato.")
            except Exception as ex:
                self.show_custom_warning("Errore PDF", str(ex))

        def do_txt():
            f_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("TXT", "*.txt")],
                                                  initialdir=EXPORT_FILES, initialfile=f"{nome_base}_{_oggi()}.txt",
                                                  confirmoverwrite=False, parent=pv)
            if f_path:
                try:
                    with open(f_path, "w", encoding="utf-8") as fh:
                        fh.write(testo)
                    self.show_toast("File TXT salvato.")
                except Exception as ex:
                    self.show_custom_warning("Errore", f"Impossibile salvare il file:\n{ex}")

        fr_t = tk.Frame(pv, bg=self.COLOR_TOPLEVEL)
        fr_t.pack(fill="both", expand=True, padx=10, pady=10)
        vs = ttk.Scrollbar(fr_t, orient="vertical", style="Vertical.TScrollbar")
        vs.pack(side="right", fill="y")
        hs = ttk.Scrollbar(fr_t, orient="horizontal")
        hs.pack(side="bottom", fill="x")
        area = tk.Text(fr_t, font=("Courier New", 9), bg=getattr(self, "COLOR_WHITE", "white"),
                       fg=getattr(self, "COLOR_BLACK", "black"), wrap="none",
                       yscrollcommand=vs.set, xscrollcommand=hs.set)
        area.pack(fill="both", expand=True)
        vs.config(command=area.yview)
        hs.config(command=area.xview)
        area.insert("1.0", testo)
        area.config(state="disabled")
        bf = tk.Frame(pv, bg=self.COLOR_TOPLEVEL)
        bf.pack(fill="x", pady=8)
        crea_btn(bf, "salva", "PDF", do_pdf, "💾").pack(side="left", padx=5)
        crea_btn(bf, "salva", "TXT", do_txt, "💾").pack(side="left", padx=5)
        if hasattr(self, "_stampa_lista_diretta"):
            crea_btn(bf, "stampa", "Stampa", lambda: self._stampa_lista_diretta(testo, self.show_custom_warning),
                     "🖨️").pack(side="left", padx=5)
        crea_btn(bf, "chiudi", "Chiudi", pv.destroy, "❌").pack(side="right", padx=10)
        _mostra(pv, parent, wa, ha)

    def stampa_inventario():
        elenco = filtrati()
        if not elenco:
            self.show_toast("Nessun articolo da esportare.")
            return
        filtro_attivo = any([var_cerca.get().strip(), var_cat.get() != TUTTE_CAT,
                             var_stato.get() != STATI_FILTRO[0], var_dal.get(), var_al.get()])
        anteprima_testo(root, "Esporta inventario — StockBox", testo_inventario(elenco, filtro_attivo), "Inventario")

    def esporta_json():
        if not art:
            self.show_toast("Magazzino vuoto, niente da esportare!")
            return
        now = datetime.date.today()
        path = filedialog.asksaveasfilename(
            defaultextension=".json", filetypes=[("File JSON", "*magazzino.json"), ("Tutti i file", "*.*")],
            initialdir=EXP_DB, initialfile=f"{now.day:02d}-{now.month:02d}-{now.year}-magazzino.json",
            title="Salva Magazzino .json", confirmoverwrite=False, parent=root)
        if path:
            try:
                with open(path, "w", encoding="utf-8") as fh:
                    json.dump({"versione": 1, "categorie": stato_dati["categorie"], "articoli": art}, fh, indent=2, ensure_ascii=False)
                self.show_custom_warning("Attenzione", f"Magazzino salvato con successo in {path}")
            except Exception as e:
                self.show_custom_warning("Attenzione", f"Impossibile salvare il magazzino:\n{e}")

    def importa_json():
        path = filedialog.askopenfilename(defaultextension=".json", filetypes=[("File JSON", "*.json"), ("Tutti i file", "*.*")],
                                          initialdir=EXP_DB, parent=root)
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as fh:
                dati = json.load(fh)
            sostituisci = True
            if art:
                sostituisci = self.show_custom_askyesno(
                    "Importazione", "Vuoi SOSTITUIRE il magazzino esistente (Sì) o UNIRE i nuovi articoli (No)?")
            n = _leggi_struttura(dati, unisci=not sostituisci)
            salva()
            aggiorna_categorie()
            ridisegna([])
            self.show_custom_warning("Importazione riuscita", f"{n} articoli importati correttamente!")
        except json.JSONDecodeError:
            self.show_custom_warning("Errore", "Il file non è un JSON valido.")
        except Exception as e:
            self.show_custom_warning("Errore", f"Impossibile importare il magazzino:\n{e}")

    def reset_db():
        if self.show_custom_askyesno("Reset Magazzino", "Sei sicuro di voler cancellare TUTTI gli articoli del magazzino?"):
            try:
                if os.path.exists(MAG_FILE):
                    os.remove(MAG_FILE)
                art.clear()
                stato_dati["categorie"] = list(CATEGORIE_DEFAULT)
                aggiorna_categorie()
                ridisegna([])
                self.show_custom_warning("Reset", "Magazzino resettato con successo.")
            except Exception as e:
                self.show_custom_warning("Errore", f"Errore durante il reset:\n{e}")

    ctx = tk.Menu(root, tearoff=0, bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT,
                  activebackground=self.MENU_ACT_BG_COLOR, activeforeground=self.MENU_ACT_FG_COLOR)
    ctx.add_command(label="✏️ Modifica", command=modifica_sel)
    ctx.add_command(label="🔄 Carico / Scarico", command=movimento_sel)
    ctx.add_command(label="📜 Storico movimenti", command=storico_sel)
    ctx.add_command(label="📈 Suggerisci scorta minima", command=suggerisci_scorta)
    ctx.add_command(label="📄 Duplica", command=duplica_sel)
    ctx.add_separator()
    ctx.add_command(label="🗑️ Cancella", command=cancella_sel)

    def click_destro(event):
        r = tree.identify_row(event.y)
        if r and r != "__vuoto__":
            if r not in tree.selection():
                tree.selection_set(r)
            chiudi_menu_sicuro()
            try:
                ctx.tk_popup(event.x_root, event.y_root)
            finally:
                ctx.grab_release()

    def doppio_click(event):
        r = tree.identify_row(event.y)
        if r and r != "__vuoto__":
            modifica_sel()

    for _m in (menu_popup, menu_db, ctx):
        rendi_chiudibile(_m)
    root.bind("<Button-1>", lambda e: None if e.widget is b_menu else chiudi_menu_sicuro(), add="+")
    
    def _controlla_focus():
        try:
            perso = root.focus_displayof() is None
        except (KeyError, tk.TclError):
 
            perso = False
        if perso:
            chiudi_menu_sicuro()

    def _focus_out(e):
        root.after(200, _controlla_focus)
    root.bind("<FocusOut>", _focus_out, add="+")
    root.bind("<Configure>", lambda e: chiudi_menu_sicuro() if e.widget is root else None, add="+")
    tree.bind("<Double-1>", doppio_click)
    tree.bind("<Control-a>", lambda e: (tree.selection_set([i for i in tree.get_children() if i != "__vuoto__"]), "break")[1])
    tree.bind("<Button-3>", click_destro)
    tree.bind("<Return>", lambda e: modifica_sel())
    tree.bind("<Delete>", cancella_sel)
    root.bind("<Control-n>", lambda e: apri_form())
    root.bind("<Control-f>", lambda e: (entry_cerca.focus_set(), entry_cerca.select_range(0, "end")))

    def _ricarica_da_web():
        try:
            if root.winfo_exists():
                carica()
                aggiorna_categorie()
                ridisegna()
        except tk.TclError:
            pass
    self._magazzino_ricarica = _ricarica_da_web

    carica()
    aggiorna_categorie()
    ridisegna([])
    _mostra(root, self, W, H)
    entry_cerca.focus_set()
