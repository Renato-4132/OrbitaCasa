#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import tkinter as tk

import __main__ as _app

QUOTE = (("Bisogni", 50), ("Desideri", 30), ("Risparmio", 20))
MESI = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

def _fmt_it(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def _calcola_503020(self, anno, mese, includi_futuri=True, conto=None):
    oggi = datetime.date.today()
    classi_cat = self._classi_categorie()
    netto = {}
    for d, sp in self.spese.items():
        if (anno is not None and d.year != anno) or (mese is not None and d.month != mese):
            continue
        if not includi_futuri and d > oggi:
            continue
        for entry in sp:
            if conto and self._conto_effettivo(entry) != conto:
                continue
            imp = float(entry[2])
            cat = entry[0]
            if str(entry[3]).strip().capitalize() == "Entrata":
                imp = -imp
            netto[cat] = netto.get(cat, 0.0) + imp
    entrate = 0.0
    classi = {"Bisogni": 0.0, "Desideri": 0.0, "Risparmio": 0.0, "": 0.0}
    non_assegnate = {}
    for cat, n in netto.items():
        n = round(n, 2)
        classe = classi_cat.get(cat, "")
        if classe not in ("Bisogni", "Desideri", "Risparmio"):
            classe = ""
        if classe:
            classi[classe] += n
        elif n < 0:
            entrate += -n
        elif n > 0:
            classi[""] += n
            non_assegnate[cat] = n
    return entrate, classi, non_assegnate

def mostra_metodo_503020(self):
    self.analisi_categorie(None, "503020")

ALTEZZA_BARRA = 6
COLORI_CLASSI = {"Bisogni": "#4c8bf5", "Desideri": "#f5a623", "Risparmio": "#2ecc71"}

def crea_barra_503020(self, parent, chiave):
    if not hasattr(self, "_b503020"):
        self._b503020 = {}
    st = {"after": None, "tip": None, "segs": [], "info": None, "corrente": None, "periodo": None}
    self._b503020[chiave] = st
    cv = tk.Canvas(parent, width=1, height=ALTEZZA_BARRA + 2, bg=self.COLOR_WIDGET_BG,
                   highlightthickness=0, cursor="hand2")
    st["cv"] = cv
    cv.bind("<Configure>", lambda e: _ridisegna_debounce(self, chiave))
    cv.bind("<Double-1>", lambda e: self.mostra_metodo_503020())
    cv.bind("<Motion>", lambda e: _hover_barra(self, chiave, e))
    cv.bind("<Leave>", lambda e: _tip_barra_off(self, chiave))
    cv.bind("<Destroy>", lambda e: _chiudi_barra(self, chiave), add="+")
    return cv

def aggiorna_barre_503020(self, chiave=None, anno=None, mese=None):
    barre = getattr(self, "_b503020", {})
    if chiave is not None and chiave in barre and anno is not None:
        barre[chiave]["periodo"] = (anno, mese)
    for k in ([chiave] if chiave in barre else list(barre)):
        _disegna_barra(self, k)

def _chiudi_barra(self, chiave):
    st = getattr(self, "_b503020", {}).get(chiave)
    if not st:
        return
    if st.get("after"):
        try:
            self.after_cancel(st["after"])
        except Exception:
            pass
        st["after"] = None
    _tip_barra_off(self, chiave)

def _ridisegna_debounce(self, chiave):
    st = self._b503020[chiave]
    if st.get("after"):
        self.after_cancel(st["after"])
    st["after"] = self.after(80, lambda: _disegna_barra(self, chiave))

def _disegna_barra(self, chiave):
    st = self._b503020.get(chiave)
    if not st:
        return
    st["after"] = None
    cv = st["cv"]
    if not cv.winfo_exists():
        return
    oggi = datetime.date.today()
    anno, mese = st["periodo"] or ((oggi.year, oggi.month) if chiave == "mese" else (oggi.year, None))
    futuri = bool(getattr(_app, "app_config_globale", {}).get("includi_futuri_analisi", True))
    try:
        entrate, classi, _na = _calcola_503020(self, anno, mese, futuri)
    except Exception:
        return
    if entrate <= 0 or (classi["Bisogni"] + classi["Desideri"] + classi["Risparmio"]) <= 0:
        _tip_barra_off(self, chiave)
        cv.delete("all")
        cv.grid_remove()
        st["info"] = None
        st["segs"] = []
        return
    cv.grid()
    if cv.winfo_width() <= 1:
        return
    cv.delete("all")
    w = max(cv.winfo_width(), 50) - 2
    st["info"] = (entrate, classi, f"{MESI[mese - 1]} {anno}" if mese else str(anno))
    st["segs"] = []
    cv.create_rectangle(1, 1, w, ALTEZZA_BARRA + 1, fill=self.COLOR_WIDGET_BG, outline=self.TEXT_COLOR, width=1)
    x = 1.0
    for nome, quota in QUOTE:
        pct = max(0.0, classi[nome]) / entrate * 100
        wseg = (w - 1) * min(pct, 100 - (x - 1) / (w - 1) * 100) / 100
        if wseg > 0:
            ok = pct >= quota if nome == "Risparmio" else pct <= quota
            cv.create_rectangle(x, 1, x + wseg, ALTEZZA_BARRA + 1, fill=COLORI_CLASSI[nome],
                                outline="" if ok else self.COLOR_RED, width=1)
            st["segs"].append((x, x + wseg, nome))
        x += wseg
    for t in (50, 80):
        xt = 1 + (w - 1) * t / 100
        cv.create_line(xt, 0, xt, ALTEZZA_BARRA + 2, fill=self.TEXT_COLOR, width=1)

def _testo_segmento(nome, entrate, classi, periodo):
    quota = dict(QUOTE)[nome]
    segno = "\u2265" if nome == "Risparmio" else "\u2264"
    valore = classi[nome]
    pct = max(0.0, valore) / entrate * 100 if entrate > 0 else 0.0
    ok = pct >= quota if nome == "Risparmio" else pct <= quota
    righe = [
        ("Periodo", periodo),
        ("Classe", nome),
        ("Target", f"{segno} {quota}%"),
        ("Attuale", f"{pct:.0f}%  ({'ok' if ok else 'fuori target'})"),
        ("Importo", f"\u20ac {_fmt_it(valore)}"),
        ("Entrate", f"\u20ac {_fmt_it(entrate)}"),
    ]
    w = max(len(k) for k, _ in righe)
    testo = "\n".join(f"{k.ljust(w)}  {v}" for k, v in righe)
    titolo = "Metodo 50/30/20: come ripartisci le entrate\n(Bisogni 50% \u00b7 Desideri 30% \u00b7 Risparmio 20%)"
    return titolo + "\n\n" + testo + "\nDoppio click per aprire il dettaglio"

def _hover_barra(self, chiave, event):
    st = self._b503020[chiave]
    info = st.get("info")
    if not info or info[0] <= 0:
        return
    nome = next((n for a, b, n in st["segs"] if a <= event.x < b), None)
    if nome is None:
        _tip_barra_off(self, chiave)
        return
    entrate, classi, periodo = info
    if st["tip"] is None:
        t = tk.Toplevel(self)
        t.wm_overrideredirect(True)
        t.attributes("-topmost", True)
        lbl = tk.Label(t, justify="left", bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                       font=("Courier New", 9), highlightthickness=1,
                       highlightbackground="#378ADD", highlightcolor="#378ADD", padx=6, pady=4)
        lbl.pack()
        st["tip"] = (t, lbl)
    t, lbl = st["tip"]
    if st["corrente"] != nome:
        lbl.config(text=_testo_segmento(nome, entrate, classi, periodo))
        st["corrente"] = nome
    t.wm_geometry(f"+{event.x_root + 12}+{event.y_root + 16}")

def _tip_barra_off(self, chiave):
    st = getattr(self, "_b503020", {}).get(chiave)
    if not st:
        return
    if st.get("tip"):
        try:
            st["tip"][0].destroy()
        except Exception:
            pass
        st["tip"] = None
    st["corrente"] = None

