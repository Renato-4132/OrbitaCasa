#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import calendar
import datetime
from collections import defaultdict

_MESI = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
         "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]

MAX_RIGHE_CATEGORIE = 20
MAX_MOVIMENTI_OGGI = 8
GIORNI_PROSSIMI = 7
GRAZIA_CHIUSURA_MS = 400
SUGGERIMENTO_ANALISI = "Tasto destro su una categoria: Analisi Categorie"
_GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
PALETTE = ["#61AFEF", "#E5C07B", "#C678DD", "#56B6C2", "#E06C75", "#98C379", "#D19A66", "#7F8DE0",
           "#E58BB4", "#8FD694"]
COLORE_ALTRE = "#7A7F8C"
LARGHEZZA_MAX_ETICHETTA = 26

def _eur(v):
    s = f"{abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{'-' if v < 0 else ''}{s} €"

def _pref(v):
    return "▲" if v > 0 else ("▼" if v < 0 else " ")

def _movimenti_mese(self):
    oggi = datetime.date.today()
    try:
        mese, anno = self.cal.get_displayed_month()
    except Exception:
        mese, anno = oggi.month, oggi.year
    escludi_futuri = hasattr(self, "considera_ricorrenze_var") and not self.considera_ricorrenze_var.get()
    giorni = {}
    for d, sp in self.spese.items():
        if d.year != anno or d.month != mese:
            continue
        if escludi_futuri and d > oggi:
            continue
        giorni[d] = [(e[0], float(e[2]), e[3] == "Entrata") for e in sp]
    return anno, mese, giorni

def _somme(voci):
    ent = sum(i for _c, i, e in voci if e)
    usc = sum(i for _c, i, e in voci if not e)
    return ent, usc, ent - usc

def _per_categoria(voci, entrata):
    tot = defaultdict(float)
    for cat, imp, is_in in voci:
        if is_in == entrata:
            tot[cat or "Senza categoria"] += imp
    return sorted(tot.items(), key=lambda x: -x[1])

def _variazione(corrente, precedente):
    if precedente <= 0:
        return "nuovo" if corrente > 0 else ""
    p = (corrente - precedente) / precedente * 100
    return "0%" if abs(p) < 0.5 else f"{p:+.0f}%"

def _mese_precedente(self, anno, mese):
    m, a = (12, anno - 1) if mese == 1 else (mese - 1, anno)
    voci = []
    for d, sp in self.spese.items():
        if d.year == a and d.month == m:
            voci += [(e[0], float(e[2]), e[3] == "Entrata") for e in sp]
    return m, voci

def _intervallo(a, b):
    return f"{a.strftime('%d/%m')}-{b.strftime('%d/%m')}"

def _formatta(elementi):
    righe_dati = [e for e in elementi if e[0] == "r"]
    larg_et = min(max([len(e[2]) for e in righe_dati] or [0]), LARGHEZZA_MAX_ETICHETTA)
    n_col = max([len(e[3]) for e in righe_dati] or [0])
    def _t(v):
        return v[0] if isinstance(v, tuple) else v
    larg_val = [max([len(_t(e[3][c])) for e in righe_dati if len(e[3]) > c] or [0]) for c in range(n_col)]
    righe = []
    for e in elementi:
        if e[0] == "t":
            righe.append(e[1])
        elif e[0] == "s":
            righe.append(None)
        else:
            _k, simbolo, etichetta, valori = e
            if len(etichetta) > larg_et:
                etichetta = etichetta[:larg_et - 1] + "…"
            riga = f"{simbolo} {etichetta.ljust(larg_et)}"
            riga += "".join("  " + (v[0].ljust(larg_val[c]) if isinstance(v, tuple) else v.rjust(larg_val[c]))
                            for c, v in enumerate(valori))
            righe.append(riga)
    larghezza = max([len(r) for r in righe if r is not None] or [0])
    return "\n".join("─" * larghezza if r is None else r for r in righe)

def _righe_categorie(elenco, simbolo):
    el = [("r", simbolo, c, [_eur(v)]) for c, v in elenco[:MAX_RIGHE_CATEGORIE]]
    resto = elenco[MAX_RIGHE_CATEGORIE:]
    if resto:
        el.append(("r", simbolo, f"Altre {len(resto)} categorie", [_eur(sum(v for _c, v in resto))]))
    return el or [("r", " ", "(nessuna)", ["-"])]

def _blocco_entrate_uscite(voci):
    ent, usc, saldo = _somme(voci)
    el = [("t", "Entrate per categoria")]
    el += _righe_categorie(_per_categoria(voci, True), "▲")
    el += [("s",), ("r", " ", "Totale entrate", [_eur(ent)]),
           ("t", "Uscite per categoria")]
    el += _righe_categorie(_per_categoria(voci, False), "▼")
    el += [("s",), ("r", " ", "Totale uscite", [_eur(usc)]),
           ("r", _pref(saldo), "Saldo", [_eur(saldo)])]
    return el

def _tabella_barre(titolo, intestazione, righe, totale):
    massimo = max([r[3] for r in righe] or [0.0]) or 1.0
    el = [("titolo", titolo), ("sep",),
          ("riga", " ", intestazione, ["Entrate", "Uscite", "Saldo"], None, None), ("sep",)]
    comp = []
    for i, (simbolo, et, ent, usc, saldo) in enumerate(righe):
        colore = PALETTE[i % len(PALETTE)]
        comp.append((usc, colore))
        el.append(("riga", simbolo, et, [_eur(ent), _eur(usc), _eur(saldo)], (usc / massimo, None),
                   [None, None, "ok" if saldo > 0 else ("ko" if saldo < 0 else None)], colore))
    if sum(v for v, _c in comp) > 0:
        el.insert(2, ("composizione", comp))
    simbolo, et, ent, usc, saldo = totale
    el += [("sep",), ("riga", simbolo, et, [_eur(ent), _eur(usc), _eur(saldo)], None, None)]
    return el

def _tooltip_oggi(self):
    oggi = datetime.date.today()
    escludi_futuri = hasattr(self, "considera_ricorrenze_var") and not self.considera_ricorrenze_var.get()
    def _voci(d):
        return [(e[0], e[1], float(e[2]), e[3] == "Entrata") for e in self.spese.get(d, [])]
    voci_oggi = _voci(oggi)
    titolo = f"Oggi - {_GIORNI[oggi.weekday()]} {oggi.day} {_MESI[oggi.month - 1].lower()} {oggi.year}"
    el = [("titolo", titolo), ("sep",)]
    ent_o = usc_o = 0.0
    if voci_oggi:
        ordinate = sorted(voci_oggi, key=lambda v: -v[2])
        massimo = ordinate[0][2] or 1.0
        for i, (cat, desc, imp, is_in) in enumerate(ordinate[:MAX_MOVIMENTI_OGGI]):
            if cat and desc and desc != cat:
                etichetta = f"{cat} - {desc}"
            else:
                etichetta = cat or desc or "Senza categoria"
            el.append(("riga", "▲" if is_in else "▼", etichetta, [_eur(imp)], (imp / massimo, None), None,
                       PALETTE[i % len(PALETTE)], cat or None))
        resto = ordinate[MAX_MOVIMENTI_OGGI:]
        if resto:
            el.append(("riga", " ", f"Altri {len(resto)} movimenti", [_eur(sum(v[2] for v in resto))], None, None))
        ent_o, usc_o, saldo_o = _somme([(c, i, e) for c, _d, i, e in voci_oggi])
        el += [("sep",),
               ("riga", "▲", "Entrate di oggi", [_eur(ent_o)], None, None),
               ("riga", "▼", "Uscite di oggi", [_eur(usc_o)], None, None),
               ("riga", _pref(saldo_o), "Saldo di oggi", [_eur(saldo_o)], None, None)]
    else:
        el.append(("nota", "Nessun movimento registrato oggi"))
    voci_mese = [(c, i, e) for d, sp in self.spese.items()
                 if d.year == oggi.year and d.month == oggi.month and d <= oggi
                 for c, _d, i, e in _voci(d)]
    ent_m, usc_m, saldo_m = _somme(voci_mese)
    media = usc_m / oggi.day
    el += [("sep",), ("nota", f"{_MESI[oggi.month - 1]} fino a oggi"),
           ("riga", "▲", "Entrate", [_eur(ent_m)], None, None),
           ("riga", "▼", "Uscite", [_eur(usc_m)], None, None),
           ("riga", _pref(saldo_m), "Saldo del mese", [_eur(saldo_m)], None, None),
           ("riga", " ", "Media uscite al giorno", [_eur(media)], None, None)]
    if oggi.day > 1 and usc_o > 0:
        media_prec = (usc_m - usc_o) / (oggi.day - 1)
        if media_prec > 0:
            dp = (usc_o - media_prec) / media_prec * 100
            el.append(("nota", f"Oggi spendi il {abs(dp):.0f}% {'in più' if dp > 0 else 'in meno'} "
                               f"della media dei giorni scorsi"))
    if not escludi_futuri:
        prossimi = [v for g in range(1, GIORNI_PROSSIMI + 1)
                    for v in _voci(oggi + datetime.timedelta(days=g))]
        if prossimi:
            n_in = sum(1 for v in prossimi if v[3])
            n_out = len(prossimi) - n_in
            ent_p = sum(v[2] for v in prossimi if v[3])
            usc_p = sum(v[2] for v in prossimi if not v[3])
            el += [("sep",), ("nota", f"Prossimi {GIORNI_PROSSIMI} giorni")]
            if n_in:
                el.append(("riga", "▲", f"Entrate ({n_in})", [_eur(ent_p)], None, None))
            if n_out:
                el.append(("riga", "▼", f"Uscite ({n_out})", [_eur(usc_p)], None, None))
    el += [("sep",)]
    if any(r[0] == "riga" and len(r) > 7 and r[7] for r in el):
        el.append(("nota", SUGGERIMENTO_ANALISI))
    el.append(("nota", "Clic: torna al giorno di oggi"))
    return {"elementi": el, "barra": "ko", "periodo": (oggi.year, oggi.month)}

def testo_tooltip_legenda(self, tipo):
    if tipo == "oggi":
        return _tooltip_oggi(self)
    anno, mese, giorni = _movimenti_mese(self)
    nome = f"{_MESI[mese - 1]} {anno}"
    tutte = [v for voci in giorni.values() for v in voci]
    if tipo in ("entrate", "uscite"):
        entrata = tipo == "entrate"
        elenco = _per_categoria(tutte, entrata)
        if not elenco:
            return f"Nessuna {'entrata' if entrata else 'uscita'} a {nome}"
        ent, usc, saldo = _somme(tutte)
        totale = (ent if entrata else usc) or 1.0
        m_prec, voci_prec = _mese_precedente(self, anno, mese)
        prec_cat = dict(_per_categoria(voci_prec, entrata))
        sigla = _MESI[m_prec - 1]
        massimo = max([v for _c, v in elenco[:MAX_RIGHE_CATEGORIE]] +
                      [prec_cat.get(c, 0.0) for c, _v in elenco[:MAX_RIGHE_CATEGORIE]] or [1.0]) or 1.0
        simbolo = "▲" if entrata else "▼"
        el = [("titolo", f"{'Entrate' if entrata else 'Uscite'} di {nome}"), ("sep",),
              ("riga", " ", "Categoria", ["Importo", "Quota", sigla, "Differenza"], None, None), ("sep",)]
        def _diff(corr, prec):
            d = corr - prec
            if abs(d) < 0.005:
                return "0,00 €", None
            buono = (d > 0) == entrata
            return f"{'+' if d > 0 else ''}{_eur(d)}", ("ok" if buono else "ko")
        comp = []
        for i, (c, v) in enumerate(elenco[:MAX_RIGHE_CATEGORIE]):
            p_v = prec_cat.get(c, 0.0)
            dtxt, dcol = _diff(v, p_v)
            colore = PALETTE[i % len(PALETTE)]
            comp.append((v, colore))
            el.append(("riga", simbolo, c, [_eur(v), f"{v / totale * 100:.0f}%", _eur(p_v), dtxt],
                       (v / massimo, p_v / massimo), [None, None, None, dcol], colore,
                       c if c != "Senza categoria" else None))
        resto = elenco[MAX_RIGHE_CATEGORIE:]
        if resto:
            v = sum(x for _c, x in resto)
            p_v = sum(prec_cat.get(c, 0.0) for c, _x in resto)
            dtxt, dcol = _diff(v, p_v)
            el.append(("riga", simbolo, f"Altre {len(resto)} categorie",
                       [_eur(v), f"{v / totale * 100:.0f}%", _eur(p_v), dtxt],
                       (min(v / massimo, 1.0), min(p_v / massimo, 1.0)), [None, None, None, dcol], COLORE_ALTRE))
            comp.append((v, COLORE_ALTRE))
        tot_prec = sum(prec_cat.values())
        dtxt, dcol = _diff(totale, tot_prec)
        el += [("sep",), ("riga", " ", f"Totale {'entrate' if entrata else 'uscite'}",
                         [_eur(totale), "100%", _eur(tot_prec), dtxt], None, [None, None, None, dcol]),
               ("riga", _pref(saldo), "Saldo del mese", [_eur(saldo), "", "", ""], None, None)]
        if any(r[0] == "riga" and len(r) > 7 and r[7] for r in el):
            el += [("sep",), ("nota", SUGGERIMENTO_ANALISI)]
        el.insert(2, ("composizione", comp))
        return {"elementi": el, "barra": "ok" if entrata else "ko", "periodo": (anno, mese)}

    if tipo == "righe":
        el = [("titolo", "Colori righe movimenti"), ("sep",),
              ("testo", "Verde: Entrata", "green", "bold"),
              ("testo", "Rosso: Uscita", "red", "bold"),
              ("testo", "Giallo corsivo: futuro", "#E5C07B", "bold italic"),
              ("testo", "Rosso spento grassetto: oltre budget", "#C08081", "bold"),
              ("testo", "Azzurro corsivo: pianificata", "#61AFEF", "bold italic")]
        return {"elementi": el, "barra": None}

    if tipo == "misto":
        misti = {d: vs for d, vs in giorni.items()
                 if any(e for _c, _i, e in vs) and any(not e for _c, _i, e in vs)}
        if not misti:
            return f"Nessun giorno con entrate e uscite a {nome}"
        righe = []
        for d in sorted(misti):
            ent, usc, saldo = _somme(misti[d])
            righe.append((_pref(saldo), d.strftime("%d/%m"), ent, usc, saldo))
        ent, usc, saldo = _somme([v for vs in misti.values() for v in vs])
        el = _tabella_barre(f"Giorni con entrate e uscite - {nome}", "Giorno", righe,
                            (_pref(saldo), f"Totale ({len(misti)} giorni)", ent, usc, saldo))
        return {"elementi": el, "barra": "ko"}

    if tipo == "weekend":
        fine_settimana = defaultdict(list)
        for d, vs in giorni.items():
            if d.weekday() >= 5:
                sabato = d - datetime.timedelta(days=d.weekday() - 5)
                fine_settimana[sabato].extend(vs)
        if not fine_settimana:
            return f"Nessun movimento nei weekend di {nome}"
        righe = []
        for sabato in sorted(fine_settimana):
            ent, usc, saldo = _somme(fine_settimana[sabato])
            righe.append((_pref(saldo), _intervallo(sabato, sabato + datetime.timedelta(days=1)), ent, usc, saldo))
        ent, usc, saldo = _somme([v for vs in fine_settimana.values() for v in vs])
        el = _tabella_barre(f"Weekend di {nome}", "Weekend", righe, (_pref(saldo), "Totale", ent, usc, saldo))
        oggi = datetime.date.today()
        gm = calendar.monthrange(anno, mese)[1]
        fino_a = oggi.day if (anno, mese) == (oggi.year, oggi.month) else (gm if (anno, mese) < (oggi.year, oggi.month) else 0)
        n_we = sum(1 for g in range(1, fino_a + 1) if datetime.date(anno, mese, g).weekday() >= 5)
        n_fe = fino_a - n_we
        usc_we = sum(_somme(vs)[1] for d, vs in giorni.items() if d.weekday() >= 5 and d.day <= fino_a)
        usc_fe = sum(_somme(vs)[1] for d, vs in giorni.items() if d.weekday() < 5 and d.day <= fino_a)
        if n_we and n_fe:
            m_we, m_fe = usc_we / n_we, usc_fe / n_fe
            el += [("sep",), ("nota", "Spesa media al giorno"),
                   ("riga", " ", f"Weekend ({n_we} giorni)", [_eur(m_we), "", ""], None, None),
                   ("riga", " ", f"Feriali ({n_fe} giorni)", [_eur(m_fe), "", ""], None, None)]
            if m_fe > 0:
                dp = (m_we - m_fe) / m_fe * 100
                el += [("nota", f"Nel weekend spendi il {abs(dp):.0f}% {'in più' if dp > 0 else 'in meno'} al giorno")]
        return {"elementi": el, "barra": "ko"}

    ent, usc, saldo = _somme(tutte)
    oggi = datetime.date.today()
    giorni_mese = calendar.monthrange(anno, mese)[1]
    mese_corrente = (anno, mese) == (oggi.year, oggi.month)
    fino_a = oggi.day if mese_corrente else (giorni_mese if (anno, mese) < (oggi.year, oggi.month) else 0)
    el = [("titolo", f"Saldi di {nome}"), ("sep",),
          ("riga", "▲", "Entrate", ["", "", _eur(ent)], None, None),
          ("riga", "▼", "Uscite", ["", "", _eur(usc)], None, None),
          ("riga", _pref(saldo), "Saldo del mese", ["", "", _eur(saldo)], None, None)]
    if fino_a:
        corrente, serie = 0.0, []
        for g in range(1, fino_a + 1):
            vs = giorni.get(datetime.date(anno, mese, g), [])
            corrente += _somme(vs)[2]
            serie.append(corrente)
        usc_trascorse = sum(_somme(vs)[1] for d, vs in giorni.items() if d.day <= fino_a)
        media = usc_trascorse / fino_a
        previsto = None
        if mese_corrente and fino_a < giorni_mese:
            previste = usc_trascorse + media * (giorni_mese - fino_a)
            previsto = ent - previste
        el += [("sep",), ("nota", "Andamento del saldo"),
               ("grafico", {"serie": serie, "giorni": giorni_mese, "previsto": previsto}),
               ("riga", " ", "Media uscite al giorno", ["", "", _eur(media)], None, None)]
        if previsto is not None:
            el += [("riga", " ", "Uscite a fine mese", ["", "", _eur(previste)], None, None),
                   ("riga", _pref(previsto), "Saldo a fine mese", ["", "", _eur(previsto)], None, None),
                   ("nota", "(proiezione al ritmo attuale)")]
    settimane = defaultdict(list)
    for d, vs in giorni.items():
        settimane[d - datetime.timedelta(days=d.weekday())].extend(vs)
    if settimane:
        righe = []
        for lunedi in sorted(settimane):
            e_, u_, sv = _somme(settimane[lunedi])
            righe.append((_pref(sv), _intervallo(lunedi, lunedi + datetime.timedelta(days=6)), e_, u_, sv))
        massimo = max([r[3] for r in righe] or [0.0]) or 1.0
        el += [("sep",), ("riga", " ", "Settimana", ["Entrate", "Uscite", "Saldo"], None, None), ("sep",)]
        comp = []
        for i, (simbolo, et, e_, u_, sv) in enumerate(righe):
            colore = PALETTE[i % len(PALETTE)]
            comp.append((u_, colore))
            el.append(("riga", simbolo, et, [_eur(e_), _eur(u_), _eur(sv)], (u_ / massimo, None),
                       [None, None, "ok" if sv > 0 else ("ko" if sv < 0 else None)], colore))
        if sum(v for v, _c in comp) > 0:
            el.insert(len(el) - len(righe) - 2, ("composizione", comp))
    return {"elementi": el, "barra": "ko"}

_FONT = ("Courier New", 8, "bold")
_FONT_PICC = ("Courier New", 7, "bold")
LARG_BARRA = 110
ALT_BARRA = 12
LARG_GRAFICO = 300
ALT_GRAFICO = 84

def _mix(w, c1, c2, t):
    try:
        a, b = w.winfo_rgb(c1), w.winfo_rgb(c2)
        return "#%02x%02x%02x" % tuple(int((a[i] + (b[i] - a[i]) * t) / 257) for i in range(3))
    except Exception:
        return c1

def _grafico_saldo(self, cv, dati, colori):
    import tkinter as tk
    serie, giorni, previsto = dati["serie"], dati["giorni"], dati["previsto"]
    W, H = LARG_GRAFICO, ALT_GRAFICO
    sx, dx, alto, basso = 6, 6, 8, 14
    n = len(serie)
    x_max = giorni if previsto is not None else max(n, 2)
    valori = list(serie) + ([previsto] if previsto is not None else []) + [0.0]
    lo, hi = min(valori), max(valori)
    if hi - lo < 1e-9:
        hi, lo = hi + 1, lo - 1
    def X(g):
        return sx + (g - 1) / (x_max - 1) * (W - sx - dx) if x_max > 1 else sx
    def Y(v):
        return alto + (hi - v) / (hi - lo) * (H - alto - basso)
    y0 = Y(0.0)
    colore = colori["ok"] if serie[-1] >= 0 else colori["ko"]
    riempi = _mix(cv, colore, colori["bg"], 0.72)
    punti = [(X(i + 1), Y(v)) for i, v in enumerate(serie)]
    if n == 1:
        punti.append((X(1) + 1, punti[0][1]))
    poly = [(punti[0][0], y0)] + punti + [(punti[-1][0], y0)]
    cv.create_polygon([c for p in poly for c in p], fill=riempi, outline="")
    cv.create_line(sx, y0, W - dx, y0, fill=colori["dim"], dash=(2, 3))
    if n > 1:
        cv.create_line([c for p in punti for c in p], fill=colore, width=2, joinstyle="round")
    ux, uy = punti[-1]
    if previsto is not None:
        px, py = X(giorni), Y(previsto)
        cv.create_line(ux, uy, px, py, fill=colori["ok"] if previsto >= 0 else colori["ko"], width=2, dash=(4, 3))
        cv.create_oval(px - 2, py - 2, px + 2, py + 2, outline="", fill=colori["ok"] if previsto >= 0 else colori["ko"])
        cv.create_line(ux, alto - 2, ux, H - basso + 2, fill=colori["dim"], dash=(1, 3))
    cv.create_oval(ux - 3, uy - 3, ux + 3, uy + 3, outline=colori["bg"], fill=colore)
    cv.create_text(sx, H - 4, text="1", anchor="w", fill=colori["dim"], font=_FONT_PICC)
    cv.create_text(W - dx, H - 4, text=str(giorni if previsto is not None else n), anchor="e",
                   fill=colori["dim"], font=_FONT_PICC)
    if previsto is not None:
        cv.create_text(ux, H - 4, text=str(n), anchor="center", fill=colori["dim"], font=_FONT_PICC)

def _apri_analisi_categoria(self, categoria, periodo=None):
    self._tooltip_interattivo = False
    try:
        if self.tooltip_win and self.tooltip_win.winfo_exists():
            self.tooltip_win.withdraw()
    except Exception:
        pass
    apri = getattr(self, "analisi_categorie", None)
    if not callable(apri):
        return
    def _vai():
        if periodo:
            try:
                apri(categoria, None, "Mese", periodo[0], periodo[1])
                return
            except TypeError:
                pass
        apri(categoria)
    self.after(10, _vai)

def _lega_riga(self, widgets, categoria, bg, fg, periodo=None):
    evid = _mix(widgets[0], fg, bg, 0.88)
    def _acceso(_e=None):
        for w in widgets:
            w.configure(bg=evid)
    def _spento(_e=None):
        for w in widgets:
            w.configure(bg=bg)
    def _destro(_e=None):
        _apri_analisi_categoria(self, categoria, periodo)
        return "break"
    for w in widgets:
        w.bind("<Enter>", _acceso)
        w.bind("<Leave>", _spento)
        w.bind("<Button-3>", _destro)

def esegui_disegno_ricco(self, contenuto, x, y):
    import tkinter as tk
    if not self.tooltip_win or not self.tooltip_win.winfo_exists():
        self.tooltip_win = tk.Toplevel(self)
        self.tooltip_win.overrideredirect(True)
        self.tooltip_win.withdraw()
    self.tooltip_win.withdraw()
    for c in self.tooltip_win.winfo_children():
        c.destroy()
    bg, fg = self.COLOR_TOOLTIP, self.COLOR_TEXT_TOOLTIP
    colori = {"bg": bg, "fg": fg, "ok": self.COLOR_GREEN_SMOOTH, "ko": self.COLOR_RED_SMOOTH,
              "dim": _mix(self, fg, bg, 0.55)}
    main = tk.Frame(self.tooltip_win, bg=bg, relief="solid", borderwidth=1)
    main.pack(fill="both", expand=True)
    tab = tk.Frame(main, bg=bg)
    tab.pack(fill="both", expand=True, padx=2, pady=3)
    elementi = contenuto["elementi"]
    barra = contenuto.get("barra")
    periodo = contenuto.get("periodo")
    n_val = max([len(e[3]) for e in elementi if e[0] == "riga"] or [1])
    col_barra = 1 if barra else None
    primo_val = 2 if barra else 1
    n_col = primo_val + n_val
    larg_et = min(max([len(e[2]) for e in elementi if e[0] == "riga"] or [0]) + 2, LARGHEZZA_MAX_ETICHETTA + 2)
    r = 0
    da_disegnare = []
    for e in elementi:
        k = e[0]
        if k == "titolo" or k == "nota":
            tk.Label(tab, text=e[1], fg=fg, bg=bg, font=_FONT, justify="left", padx=10, pady=2
                     ).grid(row=r, column=0, columnspan=n_col, sticky="w")
        elif k == "sep":
            tk.Frame(tab, height=1, bg=colori["dim"]).grid(row=r, column=0, columnspan=n_col,
                                                          sticky="ew", padx=10, pady=3)
        elif k == "testo":
            tk.Label(tab, text=e[1], fg=e[2], bg=bg, font=("Courier New", 8, e[3]), anchor="w", padx=10, pady=1
                     ).grid(row=r, column=0, columnspan=n_col, sticky="w")
        elif k == "composizione":
            cc = tk.Canvas(tab, width=10, height=14, bg=bg, highlightthickness=0, bd=0)
            cc.grid(row=r, column=0, columnspan=n_col, sticky="w", padx=10, pady=(2, 4))
            da_disegnare.append((cc, e[1]))
        elif k == "grafico":
            cv = tk.Canvas(tab, width=LARG_GRAFICO, height=ALT_GRAFICO, bg=bg, highlightthickness=0, bd=0)
            cv.grid(row=r, column=0, columnspan=n_col, sticky="w", padx=10, pady=2)
            _grafico_saldo(self, cv, e[1], colori)
        else:
            _k, simbolo, etichetta, valori, frac, cvals = e[:6]
            colore_barra = e[6] if len(e) > 6 else None
            col = colori["ko"] if simbolo == "▼" else (colori["ok"] if simbolo == "▲" else fg)
            if len(etichetta) > LARGHEZZA_MAX_ETICHETTA:
                etichetta = etichetta[:LARGHEZZA_MAX_ETICHETTA - 1] + "…"
            categoria = e[7] if len(e) > 7 else None
            w_riga = []
            lbl_et = tk.Label(tab, text=f"{simbolo} {etichetta}", fg=col, bg=bg, font=_FONT, anchor="w",
                              padx=10, pady=2, width=larg_et)
            lbl_et.grid(row=r, column=0, sticky="w")
            w_riga.append(lbl_et)
            if col_barra is not None:
                if frac is not None:
                    f_cur, f_prec = frac if isinstance(frac, tuple) else (frac, None)
                    c_b = colore_barra or colori[barra]
                    cb = tk.Canvas(tab, width=LARG_BARRA, height=ALT_BARRA, bg=bg, highlightthickness=0, bd=0)
                    cb.create_rectangle(0, 0, LARG_BARRA, ALT_BARRA, fill=_mix(cb, fg, bg, 0.86), outline="")
                    cb.create_rectangle(0, 0, max(3, round(LARG_BARRA * f_cur)), ALT_BARRA, fill=c_b, outline="")
                    if f_prec:
                        xp = min(LARG_BARRA - 1, max(1, round(LARG_BARRA * f_prec)))
                        cb.create_line(xp, 0, xp, ALT_BARRA, fill=fg, width=2)
                    cb.grid(row=r, column=col_barra, padx=(2, 6))
                    w_riga.append(cb)
            for i, v in enumerate(valori):
                c_v = col
                if cvals and cvals[i]:
                    c_v = colori[cvals[i]]
                lbl_v = tk.Label(tab, text=v, fg=c_v, bg=bg, font=_FONT, anchor="e", padx=6, pady=2)
                lbl_v.grid(row=r, column=primo_val + i, sticky="e")
                w_riga.append(lbl_v)
            if categoria:
                _lega_riga(self, w_riga, categoria, bg, fg, periodo)
        r += 1
    if da_disegnare:
        tab.update_idletasks()
        larg = max(100, tab.winfo_reqwidth() - 20)
        for cc, voci in da_disegnare:
            cc.configure(width=larg)
            tot = sum(v for v, _c in voci) or 1.0
            xx = 0.0
            for v, colore in voci:
                w = v / tot * larg
                cc.create_rectangle(round(xx), 0, max(round(xx) + 1, round(xx + w) - 1), 14, fill=colore, outline="")
                xx += w
    interattivo = any(e[0] == "riga" and len(e) > 7 and e[7] for e in elementi)
    self._tooltip_interattivo = interattivo
    self._tooltip_token = getattr(self, "_tooltip_token", 0) + 1
    token = self._tooltip_token
    prec = getattr(self, "_tooltip_chiudi_timer", None)
    if prec:
        try:
            self.after_cancel(prec)
        except Exception:
            pass
        self._tooltip_chiudi_timer = None
    def _chiudi_se_fuori():
        self._tooltip_chiudi_timer = None
        if getattr(self, "_tooltip_token", None) != token or not getattr(self, "_tooltip_interattivo", False):
            return
        try:
            tw = self.tooltip_win
            if not tw or not tw.winfo_exists():
                return
            px, py = self.winfo_pointerxy()
            x0, y0 = tw.winfo_rootx(), tw.winfo_rooty()
            if x0 - 2 <= px <= x0 + tw.winfo_width() + 2 and y0 - 2 <= py <= y0 + tw.winfo_height() + 2:
                return
            tw.withdraw()
        except tk.TclError:
            pass
    def _chiudi_ritardato(_e=None):
        t = getattr(self, "_tooltip_chiudi_timer", None)
        if t:
            try:
                self.after_cancel(t)
            except Exception:
                pass
        self._tooltip_chiudi_timer = self.after(GRAZIA_CHIUSURA_MS, _chiudi_se_fuori)
    self._tooltip_chiudi_ritardato = _chiudi_ritardato
    if interattivo:
        self.tooltip_win.bind("<Leave>", _chiudi_ritardato)
    else:
        self.tooltip_win.unbind("<Leave>")
    dx, dy = (8, 6) if interattivo else (15, 10)
    self.tooltip_win.geometry(f"+{x+dx}+{y+dy}")
    self.tooltip_win.update_idletasks()
    self.tooltip_win.deiconify()
    self.tooltip_win.attributes("-topmost", True)

