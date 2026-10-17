#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import calendar
import json
import re
import statistics
import textwrap
import tkinter as tk
from tkinter import ttk

import __main__ as _app
from moduli.modello_spesa import campo, METODI_PAGAMENTO_EMOJI, SIMBOLI_METODO, metodo_pagamento_pulito
from moduli.mappa_conti_trasferimenti import costruisci_mappa_conti_da_trasferimenti, conto_da_mappa

MESI = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
NESSUNA = "— Nessuna —"
TUTTE = "Tutte le categorie"
HOUSEHOLD_LABEL = "Patrimonio Complessivo"
TAB_NOMI = ("dettaglio", "aggrega", "timemachine", "trend", "distribuzione", "budgetsuperato", "target", "503020")

def _fmt_it(v, spec=",.2f"):
    s = format(v, spec)
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")

def _to_date(d):
    if isinstance(d, datetime.datetime):
        return d.date()
    if isinstance(d, datetime.date):
        return d
    if isinstance(d, str):
        try:
            return datetime.datetime.strptime(d, "%d-%m-%Y").date()
        except Exception:
            return None
    return None

def _movimenti(self, conto=None, filtrati=True):
    out = []
    for d, sp in self.spese.items():
        dd = _to_date(d)
        if dd is None:
            continue
        for v in sp:
            out.append((dd, v))
    if filtrati:
        spec = _spec_filtri(self)
        if spec:
            out = [(d, v) for d, v in out if _passa_filtri(spec, d, v)]
    if not conto or conto == HOUSEHOLD_LABEL:
        return out
    try:
        agganci = costruisci_mappa_conti_da_trasferimenti(_app.PORTAFOGLIO_BANCARIO)
    except Exception:
        agganci = {}
    uso = {}
    filtrati = []
    for d, v in sorted(out, key=lambda x: x[0]):
        c = self._conto_effettivo(v)
        if not c:
            try:
                c = conto_da_mappa(agganci, uso, d.strftime("%d-%m-%Y"),
                                   float(abs(campo(v, "importo", 0.0))),
                                   str(campo(v, "tipo", "")).capitalize()) or ""
            except Exception:
                c = ""
        if c == conto:
            filtrati.append((d, v))
    return filtrati

def _nomi_conti():
    try:
        with open(_app.PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as f:
            conti = json.load(f).get("conti", [])
    except Exception:
        conti = []
    return [HOUSEHOLD_LABEL] + [c.get("nome", "") for c in conti if c.get("nome")]

_FILTRI_TXT = [""]

def _suff_conto(conto):
    return (f" – Conto: {conto}" if conto and conto != HOUSEHOLD_LABEL else "") + _FILTRI_TXT[0]

TUTTI = "Tutti"
NESSUN_METODO = "(nessuno)"
TIPI_FILTRO = [TUTTI, "Entrata", "Uscita"]
ORIG_FILTRO = [TUTTI, "Ricorrenti", "Non ricorrenti"]

def _data_libera(s):
    s = str(s or "").strip().replace("/", "-").replace(".", "-")
    if not s:
        return None
    try:
        return datetime.datetime.strptime(s, "%d-%m-%Y").date()
    except Exception:
        return None

def _spec_filtri(self):
    f = getattr(self, "_analisi_filtri", None)
    if not f:
        return None
    try:
        spec = {
            "tipo": f["tipo"].get(), "metodo": metodo_pagamento_pulito(f["metodo"].get()), "orig": f["orig"].get(),
            "tag": [t.lstrip("#").lower() for t in re.split(r"[\s,;]+", f["tag"].get().strip()) if t.lstrip("#")],
            "testo": f["testo"].get().strip().lower(), "all": bool(f["allegato"].get()),
            "da": _data_libera(f["da"].get()), "a": _data_libera(f["a"].get()),
        }
    except Exception:
        return None
    attivo = (spec["tipo"] != TUTTI or spec["metodo"] != TUTTI or spec["orig"] != TUTTI or spec["tag"]
              or spec["testo"] or spec["all"] or spec["da"] or spec["a"])
    return spec if attivo else None

def _passa_filtri(spec, d, v):
    if spec["da"] and d < spec["da"]:
        return False
    if spec["a"] and d > spec["a"]:
        return False
    if spec["tipo"] != TUTTI and str(campo(v, "tipo", "")).strip().lower() != spec["tipo"].lower():
        return False
    desc = str(campo(v, "descrizione", "") or "")
    if spec["metodo"] != TUTTI:
        m = str(campo(v, "metodo_pagamento", "") or "").strip()
        if spec["metodo"] == NESSUN_METODO:
            if m or any(sim in desc for sim in SIMBOLI_METODO.values()):
                return False
        elif m:
            if spec["metodo"] != m:
                return False
        else:
            sim = SIMBOLI_METODO.get(spec["metodo"], "")
            if not sim or sim not in desc:
                return False
    if spec["testo"] and spec["testo"] not in desc.lower():
        return False
    if spec["tag"]:
        tags = {str(t).lstrip("#").lower() for t in (campo(v, "hashtag", []) or [])}
        if not all(t in tags for t in spec["tag"]):
            return False
    if spec["orig"] != TUTTI:
        ric = bool(campo(v, "id_ricorrenza", "")) or "RIC·" in desc
        if (spec["orig"] == "Ricorrenti") != ric:
            return False
    if spec["all"] and "ALL·" not in desc:
        return False
    return True

def _descr_filtri(spec):
    out = []
    if spec["tipo"] != TUTTI:
        out.append(spec["tipo"])
    if spec["metodo"] != TUTTI:
        out.append(f"Metodo {SIMBOLI_METODO.get(spec['metodo'], '')} {spec['metodo']}".replace("  ", " "))
    if spec["orig"] != TUTTI:
        out.append(spec["orig"])
    if spec["tag"]:
        out.append(" ".join(f"#{t}" for t in spec["tag"]))
    if spec["testo"]:
        out.append(f"«{spec['testo']}»")
    if spec["all"]:
        out.append("con allegato")
    if spec["da"] or spec["a"]:
        da = spec["da"].strftime("%d-%m-%Y") if spec["da"] else "…"
        a = spec["a"].strftime("%d-%m-%Y") if spec["a"] else "…"
        out.append(f"{da} → {a}")
    return out

def _anni_disponibili(self):
    anni = {d.year for d, _ in _movimenti(self, filtrati=False)}
    anni.add(datetime.date.today().year)
    return sorted(anni, reverse=True)

def _futuri_condiviso(self, tab):
    top = tab.winfo_toplevel()
    v = getattr(top, "_futuri_var", None)
    if v is None:
        cfg = getattr(_app, "app_config_globale", {}) or {}
        v = tk.BooleanVar(value=bool(cfg.get("includi_futuri_analisi", True)))

        def salva(*_):
            try:
                _app._salva_chiave_config("includi_futuri_analisi", bool(v.get()))
            except Exception:
                pass
            try:
                self.aggiorna_barre_503020()
            except Exception:
                pass

        v.trace_add("write", salva)
        top._futuri_var = v
    return v

class _BarraTotali:
    def __init__(self, app, parent):
        self.app = app
        self.valori = {}
        self.resets = {}
        self.attivo = 0
        bg = app.COLOR_TOPLEVEL
        self.frame = tk.Frame(parent, bg=bg)
        mk = lambda: tk.Label(self.frame, bg=bg, font=("Arial", 10, "bold"), padx=8)
        self.l_ent, self.l_usc, self.l_sal = mk(), mk(), mk()
        for l in (self.l_ent, self.l_usc, self.l_sal):
            l.pack(side=tk.LEFT)
        self.mostra()

    def registra_reset(self, idx, fn):
        self.resets[idx] = fn

    def imposta(self, idx, entrate, uscite):
        self.valori[idx] = None if entrate is None else (entrate, uscite)
        if idx == self.attivo:
            self.mostra()

    def attiva(self, idx):
        self.attivo = idx
        self.mostra()

    def reset(self):
        fn = self.resets.get(self.attivo)
        if fn:
            fn()

    def mostra(self):
        a = self.app
        verde = getattr(a, "COLOR_GREEN_SMOOTH", "#28A745")
        rosso = getattr(a, "COLOR_RED_SMOOTH", "#DC3545")
        neutro = getattr(a, "TEXT_COLOR", "#dddddd")
        v = self.valori.get(self.attivo)
        if not v:
            for l, t in ((self.l_ent, "Entrate: —"), (self.l_usc, "Uscite: —"), (self.l_sal, "Saldo: —")):
                l.config(text=t, fg=neutro)
            return
        e, u = v
        saldo = e - u
        self.l_ent.config(text=f"Entrate: {_fmt_it(e)} €", fg=verde if e > 0 else neutro)
        self.l_usc.config(text=f"Uscite: {_fmt_it(u)} €", fg=rosso if u > 0 else neutro)
        self.l_sal.config(text=f"Saldo: {_fmt_it(saldo, '+,.2f')} €",
                          fg=verde if saldo > 0.004 else (rosso if saldo < -0.004 else neutro))


def _btn(self, parent, ico, testo, cmd, side="left"):
    img = self.icone_gui.get(ico)
    b = tk.Label(parent, compound="left", image=img, text=f" {testo}",
                 background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                 cursor="hand2", padx=12, pady=6, font=("Arial", 9, "bold"))
    b.image = img
    b.pack(side=side, padx=6)
    b.bind("<Button-1>", lambda e: cmd())
    return b


COLORE_FUTURO = "#E5C07B"
TIPO_COLORE = {"entrata": "green", "uscita": "red"}
COLORE_BUDGET_SUPERATO = "#FF8C00"

def _configura_tag(tv):
    tv.tag_configure("entrata", foreground="green")
    tv.tag_configure("uscita", foreground="red")
    tv.tag_configure("futuro", foreground=COLORE_FUTURO, font=("Arial", 9, "italic"))
    tv.tag_configure("budget_superato", foreground=COLORE_BUDGET_SUPERATO, font=("Arial", 9, "bold"))

def _parse_data(s):
    try:
        return datetime.datetime.strptime(str(s).strip(), "%d-%m-%Y").date()
    except Exception:
        return None

def _casella_tree(self, parent, colonne):
    fr = ttk.Frame(parent)
    fr.grid_rowconfigure(0, weight=1)
    fr.grid_columnconfigure(0, weight=1)
    sy = ttk.Scrollbar(fr, orient=tk.VERTICAL, style="Vertical.TScrollbar")
    sy.grid(row=0, column=1, sticky="ns")
    sx = ttk.Scrollbar(fr, orient=tk.HORIZONTAL, style="Horizontal.TScrollbar")
    sx.grid(row=1, column=0, sticky="ew")
    tv = ttk.Treeview(fr, columns=[c[0] for c in colonne], show="headings", selectmode="browse",
                      height=8, yscrollcommand=sy.set, xscrollcommand=sx.set)
    tv.grid(row=0, column=0, sticky="nsew")
    sy.config(command=tv.yview)
    sx.config(command=tv.xview)
    titoli = {c[0]: c[1] for c in colonne}

    def ripristina_intestazioni():
        for cid, tit in titoli.items():
            tv.heading(cid, text=tit, command=lambda _c=cid: self.treeview_sort_column(tv, _c, False))

    for cid, _tit, w, anc, stretch in colonne:
        tv.column(cid, width=w, minwidth=40, anchor=anc, stretch=stretch)
    ripristina_intestazioni()
    _configura_tag(tv)
    tv._ripristina_intestazioni = ripristina_intestazioni
    tv._exp = {}
    tv._entry_lookup = {}
    tv._metodo_lookup = {}
    tv._extra = {}
    self._bind_tooltip_metodo(tv, col_desc=2)
    return fr, tv

def _svuota(tv):
    tv.delete(*tv.get_children())
    tv._exp.clear()
    tv._entry_lookup.clear()
    tv._metodo_lookup.clear()
    tv._extra.clear()
    tv._ripristina_intestazioni()

def _inserisci(tv, valori, tag=None, entry=None, info=None, extra=None):
    iid = tv.insert("", "end", values=valori, tags=(tag,) if tag else ())
    tv._exp[iid] = [str(x) for x in valori]
    if entry is not None:
        tv._entry_lookup[iid] = entry
    if info is not None:
        tv._metodo_lookup[iid] = info
    if extra is not None:
        tv._extra[iid] = extra
    return iid

def _riga_info(self, parent, hint=""):
    fr = ttk.Frame(parent)
    lbl_i = ttk.Label(fr, text="", font=("Arial", 9, "bold"))
    lbl_i.pack(side=tk.LEFT)
    lbl_h = ttk.Label(fr, text=hint, foreground="gray", font=("Arial", 8, "italic"))
    lbl_h.pack(side=tk.RIGHT)
    return fr, lbl_i, lbl_h

def _tronca(s, w):
    s = str(s)
    return s if len(s) <= w else s[:max(w - 1, 1)] + "…"

def _componi_testo(titolo, colonne, righe, footer=(), extra=()):
    MAX_LARGH = 110
    n = len(colonne)
    tutte = [list(r) for r in righe] + [list(r) for r in footer]
    larg = []
    for i, (h, _al, mx) in enumerate(colonne):
        w = max([len(h)] + [len(str(r[i])) for r in tutte if i < len(r)])
        larg.append(max(len(h), min(w, mx)))

    def cella(i, s):
        s = _tronca(s, larg[i])
        al = colonne[i][1]
        return s.rjust(larg[i]) if al == "r" else (s.center(larg[i]) if al == "c" else s.ljust(larg[i]))

    def riga(r):
        return " │ ".join(cella(i, r[i] if i < len(r) else "") for i in range(n)).rstrip()

    def righe_testo(lista):
        out_t = []
        for t in lista:
            t = str(t)
            out_t += (textwrap.wrap(t, MAX_LARGH) or [""]) if len(t) > MAX_LARGH else [t.rstrip()]
        return out_t

    oggi = datetime.date.today()
    testa = righe_testo(titolo)
    coda = righe_testo(extra)
    gen = f"Generato il {oggi.day:02d}-{oggi.month:02d}-{oggi.year}"
    tab_w = sum(larg) + 3 * (n - 1)
    totw = max([tab_w, len(gen)] + [len(x) for x in testa + coda])
    dbl, sing = "═" * totw, "─" * totw
    ultima = larg[-1] + (totw - tab_w)
    reg = "─┼─".join(["─" * w for w in larg[:-1]] + ["─" * ultima])
    out = [dbl] + testa + [gen, sing,
                           " │ ".join(cella(i, colonne[i][0]) for i in range(n)).rstrip(), reg]
    out += [riga(r) for r in righe]
    if footer:
        out.append(reg)
        out += [riga(r) for r in footer]
    out.append(dbl)
    out += coda
    return "\n".join(out)

def _esporta(self, tree, nome, colonne, stato):
    ids = tree.get_children()
    if not ids:
        self.show_toast("Nulla da esportare.")
        return
    righe, fut = [], False
    for iid in ids:
        c = list(tree._exp.get(iid) or [str(x) for x in tree.item(iid, "values")])
        if "futuro" in tree.item(iid, "tags"):
            fut = True
            c[0] = f"{c[0]}*"
        righe.append(c)
    extra = list(stato.get("extra", []))
    if fut:
        extra.append("* = futuro (data successiva a oggi)")
    contenuto = _componi_testo(stato.get("intest", []), colonne, righe, stato.get("footer", []), extra)
    oggi = datetime.date.today()
    self.show_export_preview(contenuto, f"{nome}_{oggi.day:02d}-{oggi.month:02d}-{oggi.year}.txt")

def _copia_nel_form(self, entry, conto=None):
    categoria = campo(entry, "categoria", "").strip()
    descrizione = campo(entry, "descrizione", "").strip()
    importo = campo(entry, "importo", 0.0)
    tipo = campo(entry, "tipo", "").strip()
    metodo = campo(entry, "metodo_pagamento", "")
    conto = conto or self._conto_effettivo(entry)
    hashtag = campo(entry, "hashtag", [])
    cat_match = next((c for c in self.categorie if c.strip().lower() == categoria.lower()), None)
    if cat_match:
        self.cat_sel.set(cat_match)
        self.cat_menu.set(cat_match)
        self.on_categoria_changed(manuale=False)
    try:
        self.imp_entry.delete(0, tk.END)
        self.imp_entry.insert(0, _app._fmt_it_safe(float(importo)))
    except (ValueError, TypeError):
        pass
    self.desc_entry.delete(0, tk.END)
    if "RIC·" not in descrizione:
        self.desc_entry.insert(0, descrizione.replace("ALL·", "").strip()[:30])
    if self.tipo_spesa_var.get() != tipo:
        self.toggle_tipo_spesa()
    if hasattr(self, "metodo_pagamento_var"):
        self.metodo_pagamento_var.set(self._metodo_pagamento_a_combo(metodo))
    if hasattr(self, "v_conto_movimento"):
        self.v_conto_movimento.set(conto or "(nessuno)")
    if hasattr(self, "tag_entry"):
        self.tag_entry.delete(0, tk.END)
        self.tag_entry.insert(0, " ".join(hashtag))
    self.after(0, self.imp_entry.focus_set)
    self.show_toast("Movimento copiato nel form")

def _stessa_cat(a, b):
    return str(a).replace(" ", "").lower() == str(b).replace(" ", "").lower()

def _apri_transazioni(self, popup, categorie, anno, mese, conto, titolo, sel, forza_chiavi=False):
    chiavi = None
    if forza_chiavi or (conto and conto != HOUSEHOLD_LABEL) or _spec_filtri(self):
        chiavi = set()
        for d, v in _movimenti(self, conto):
            if sel(d, v):
                try:
                    chiavi.add((d.strftime("%d-%m-%Y"), round(float(campo(v, "importo", 0.0)), 2),
                                str(campo(v, "tipo", "")).strip().capitalize()))
                except Exception:
                    pass
    data_filter = {"anno": str(anno) if anno else "Tutti",
                   "mese": str(mese) if mese else "Tutti",
                   "categorie": list(categorie)}
    prima = {str(w) for w in self.winfo_children() if isinstance(w, tk.Toplevel)}
    self.mostra_transazioni_popup(data_filter, titolo, chiavi_filtro=chiavi)

    def alla_chiusura(e, w):
        if e.widget is not w or not getattr(self, "_popup_da_doppio_click", False):
            return
        self._popup_da_doppio_click = False
        try:
            if popup.winfo_exists():
                self.after(60, popup.destroy)
        except tk.TclError:
            pass

    try:
        for w in self.winfo_children():
            if isinstance(w, tk.Toplevel) and str(w) not in prima:
                w.bind("<Destroy>", lambda e, w=w: alla_chiusura(e, w), add="+")
    except tk.TclError:
        pass

class _Grafico:
    RIGA_MIN = 26
    ALTEZZA_MIN_COLONNE = 340

    def __init__(self, app, parent, orizzontale=True):
        self.app = app
        self.orizzontale = orizzontale
        bg = getattr(app, "COLOR_BACKGROUND", "#1e1e1e")
        self.box = tk.Frame(parent, bg=bg)
        self.box.grid_rowconfigure(1, weight=1)
        self.box.grid_columnconfigure(1, weight=1)
        self.hdr = tk.Canvas(self.box, bg=bg, highlightthickness=0, height=28)
        self.hdr.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.sb = ttk.Scrollbar(self.box, orient=tk.VERTICAL, style="Vertical.TScrollbar")
        self.cv = tk.Canvas(self.box, bg=bg, highlightthickness=0, width=300, height=120,
                            yscrollcommand=self.sb.set, yscrollincrement=self.RIGA_MIN)
        self.sb.config(command=self.cv.yview)
        self.cv.grid(row=1, column=1, sticky="nsew")
        self.sb.grid(row=1, column=0, sticky="ns")
        self.titolo = ""
        self.righe = []
        self.serie = []
        self._job = None
        self._reset_scroll = False
        self.chiavi = []
        self.dettagli = []
        self.azione = None
        self.suggerimento = ""
        self.evidenza = {}
        self._geo = None
        self._hover = None
        self._tip = None
        self.cv.bind("<Configure>", lambda e: self._pianifica())
        for ev in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
            self.cv.bind(ev, self._rotella)
        self.cv.bind("<Motion>", self._muovi)
        self.cv.bind("<Leave>", self._esci)
        self.cv.bind("<Double-Button-1>", self._doppio)
        self.cv.bind("<Destroy>", lambda e: self._nascondi_tip())

    def _rotella(self, e):
        su = getattr(e, "num", 0) == 4 or getattr(e, "delta", 0) > 0
        self.cv.yview_scroll(-1 if su else 1, "units")
        self._nascondi_tip()
        self._hover = None
        self.cv.delete("hl")

    def imposta(self, titolo, righe, serie, chiavi=None, azione=None, dettagli=None, suggerimento="", evidenza=None):
        self.titolo, self.righe, self.serie = titolo, righe, serie
        self.evidenza = dict(evidenza or {})
        self.chiavi = list(chiavi) if chiavi else []
        self.azione = azione
        self.dettagli = list(dettagli) if dettagli else []
        self.suggerimento = suggerimento
        self._reset_scroll = True
        self._pianifica()

    def _attivo(self, i):
        return self.azione is not None and i < len(self.chiavi) and self.chiavi[i] is not None

    def _riga_da_evento(self, e):
        g = self._geo
        if not g or not self.righe:
            return None
        x, y = self.cv.canvasx(e.x), self.cv.canvasy(e.y)
        if g["tipo"] == "h":
            if y < g["top"]:
                return None
            i = int((y - g["top"]) / g["rh"])
        else:
            if x < g["x0"]:
                return None
            i = int((x - g["x0"]) / g["cw"])
        return i if 0 <= i < len(self.righe) else None

    def _testo_tip(self, i):
        et, vals = self.righe[i]
        linee = [str(et)]
        con_quota = len(self.righe) > 1 and all(v >= 0 for _, vv in self.righe for v in vv)
        for j, v in enumerate(vals):
            nome = self.serie[j][0] if j < len(self.serie) else ""
            r = (f"{nome}: " if nome else "") + f"{_fmt_it(v)} €"
            if con_quota:
                tot = sum(rr[1][j] for rr in self.righe)
                if tot > 0:
                    r += f"  ({_fmt_it(v / tot * 100, '.1f')}%)"
            linee.append(r)
        if i < len(self.dettagli) and self.dettagli[i]:
            linee.append(self.dettagli[i])
        if self._attivo(i) and self.suggerimento:
            linee.append("")
            linee.append(self.suggerimento)
        return "\n".join(linee)

    def _evidenzia(self, i):
        self.cv.delete("hl")
        g = self._geo
        if i is None or not g:
            return
        if g["tipo"] == "h":
            box = (2, g["top"] + g["rh"] * i, g["W"] - 2, g["top"] + g["rh"] * (i + 1))
        else:
            box = (g["x0"] + g["cw"] * i, 2, g["x0"] + g["cw"] * (i + 1), g["H"] - 2)
        self.cv.create_rectangle(*box, outline=self._colori()["accent"], width=1, dash=(3, 2), tags="hl")

    def _muovi(self, e):
        i = self._riga_da_evento(e)
        if i != self._hover:
            self._hover = i
            self._evidenzia(i)
            self.cv.configure(cursor="hand2" if i is not None and self._attivo(i) else "")
        if i is None:
            self._nascondi_tip()
        else:
            self._mostra_tip(i, e.x_root, e.y_root)

    def _esci(self, e=None):
        self._hover = None
        self.cv.delete("hl")
        self.cv.configure(cursor="")
        self._nascondi_tip()

    def _mostra_tip(self, i, xr, yr):
        a = self.app
        testo = self._testo_tip(i)
        nuovo = self._tip is None
        if nuovo:
            bgt = getattr(a, "COLOR_TOOLTIP", "#333333")
            w = tk.Toplevel(self.cv)
            w.withdraw()
            w.overrideredirect(True)
            try:
                w.attributes("-topmost", True)
            except tk.TclError:
                pass
            w.config(highlightthickness=1, highlightbackground=getattr(a, "COLOR_HIGHLIGHT", "#3B82F6"), bg=bgt)
            lb = tk.Label(w, text=testo, justify="left", bg=bgt, fg=getattr(a, "TEXT_COLOR", "#dddddd"),
                          font=("Arial", 8), padx=6, pady=4)
            lb.pack()
            self._tip = (w, lb)
        else:
            w, lb = self._tip
            if lb.cget("text") != testo:
                lb.config(text=testo)
        w.update_idletasks()
        x, y = xr + 14, yr + 16
        if x + w.winfo_reqwidth() > w.winfo_screenwidth():
            x = xr - w.winfo_reqwidth() - 14
        if y + w.winfo_reqheight() > w.winfo_screenheight():
            y = yr - w.winfo_reqheight() - 10
        w.wm_geometry(f"+{max(x, 0)}+{max(y, 0)}")
        if nuovo:
            w.deiconify()

    def _nascondi_tip(self):
        if self._tip is not None:
            try:
                self._tip[0].destroy()
            except tk.TclError:
                pass
            self._tip = None

    def _doppio(self, e):
        i = self._riga_da_evento(e)
        if i is None or not self._attivo(i):
            return
        self._nascondi_tip()
        self.azione(self.chiavi[i], str(self.righe[i][0]))

    def _pianifica(self):
        if self._job is not None:
            try:
                self.cv.after_cancel(self._job)
            except Exception:
                pass
        self._job = self.cv.after(40, self.disegna)

    def _colori(self):
        a = self.app
        return {
            "bg": getattr(a, "COLOR_BACKGROUND", "#1e1e1e"),
            "fg": getattr(a, "TEXT_COLOR", "#dddddd"),
            "green": getattr(a, "COLOR_GREEN_SMOOTH", "#28A745"),
            "red": getattr(a, "COLOR_RED_SMOOTH", "#DC3545"),
            "accent": getattr(a, "COLOR_HIGHLIGHT", "#3B82F6"),
            "orange": COLORE_BUDGET_SUPERATO,
        }

    def _intestazione(self, col):
        hd = self.hdr
        hd.configure(bg=col["bg"])
        hd.delete("all")
        W = hd.winfo_width()
        hd.create_text(8, 8, anchor="nw", text=self.titolo, fill=col["fg"], font=("Arial", 9, "bold"))
        if len(self.serie) > 1 or (self.serie and self.serie[0][0]):
            x = W - 8
            for nome, ck in reversed(self.serie):
                hd.create_text(x, 9, anchor="ne", text=nome, fill=col["fg"], font=("Arial", 8))
                x -= len(nome) * 6 + 14
                hd.create_rectangle(x, 11, x + 8, 19, fill=col[ck], outline="")
                x -= 12

    def disegna(self):
        self._job = None
        cv = self.cv
        try:
            if not cv.winfo_exists():
                return
        except tk.TclError:
            return
        col = self._colori()
        cv.configure(bg=col["bg"])
        cv.delete("all")
        self._geo = None
        self._hover = None
        self._nascondi_tip()
        self._intestazione(col)
        W, H = cv.winfo_width(), cv.winfo_height()
        if W < 40 or H < 40:
            return
        tutti = [v for _, vals in self.righe for v in vals]
        if not tutti:
            cv.configure(scrollregion=(0, 0, W, H))
            cv.create_text(W / 2, H / 2, text="Nessun dato da mostrare", fill=col["fg"], font=("Arial", 10))
            return
        vmax, vmin = max(0.0, max(tutti)), min(0.0, min(tutti))
        span = (vmax - vmin) or 1.0
        if self.orizzontale:
            self._orizz(cv, col, W, H, vmin, span)
        else:
            Hc = max(H, self.ALTEZZA_MIN_COLONNE)
            cv.configure(scrollregion=(0, 0, W, Hc))
            self._vert(cv, col, W, Hc, vmin, span)
        if self._reset_scroll:
            cv.yview_moveto(0)
            self._reset_scroll = False

    def _orizz(self, cv, col, W, H, vmin, span):
        n, ns = len(self.righe), len(self.serie)
        top, bot = 6, 6
        scorre = top + n * self.RIGA_MIN + bot > H
        if scorre:
            rh = float(self.RIGA_MIN)
            cv.configure(scrollregion=(0, 0, W, top + n * rh + bot))
        else:
            rh = min(40.0, (H - top - bot) / n)
            cv.configure(scrollregion=(0, 0, W, H))
        self._geo = {"tipo": "h", "top": top, "rh": rh, "W": W}
        lmax = max(len(str(e)) for e, _ in self.righe)
        x0 = min(170, max(60, lmax * 7 + 10))
        if vmin < 0:
            x0 += 70
        x1 = W - 80
        if x1 - x0 < 40:
            return
        sp = (x1 - x0) / span
        xz = x0 + (-vmin) * sp
        bh = max(3.0, min(14.0, rh * 0.8 / ns))
        cv.create_line(xz, top, xz, top + n * rh, fill=col["fg"], dash=(2, 3))
        for i, (et, vals) in enumerate(self.righe):
            yc = top + rh * i + rh / 2
            et_txt = str(et) if len(str(et)) <= 24 else str(et)[:22] + "…"
            cv.create_text(x0 - (76 if vmin < 0 else 6), yc, anchor="e", text=et_txt,
                           fill=col["fg"], font=("Arial", 8))
            for j, v in enumerate(vals):
                y0 = yc - bh * ns / 2 + bh * j
                xv = xz + v * sp
                cv.create_rectangle(min(xz, xv), y0, max(xz, xv), y0 + bh - 1,
                                    fill=col[self.evidenza.get((i, j), self.serie[j][1])], outline="")
                if v == 0:
                    continue
                if v > 0:
                    cv.create_text(max(xz, xv) + 4, y0 + bh / 2, anchor="w",
                                   text=_fmt_it(v), fill=col["fg"], font=("Arial", 7))
                else:
                    cv.create_text(min(xz, xv) - 4, y0 + bh / 2, anchor="e",
                                   text=_fmt_it(v), fill=col["fg"], font=("Arial", 7))

    def _vert(self, cv, col, W, H, vmin, span):
        n, ns = len(self.righe), len(self.serie)
        x0, x1 = 12, W - 10
        top, bot = 28, 22
        cw = (x1 - x0) / n
        self._geo = {"tipo": "v", "x0": x0, "cw": cw, "H": H}
        sp = (H - top - bot) / span
        yz = H - bot - (-vmin) * sp
        bw = max(3.0, min(50.0, cw * 1 / ns))
        cv.create_line(x0, yz, x1, yz, fill=col["fg"])
        for i, (et, vals) in enumerate(self.righe):
            xc = x0 + cw * i + cw / 2
            cv.create_text(xc, H - bot + 4, anchor="n", text=str(et), fill=col["fg"], font=("Arial", 8))
            for j, v in enumerate(vals):
                xb = xc - bw * ns / 2 + bw * j
                yv = yz - v * sp
                cv.create_rectangle(xb, min(yz, yv), xb + bw - 1, max(yz, yv),
                                    fill=col[self.evidenza.get((i, j), self.serie[j][1])], outline="")
                if cw >= 26 and v:
                    sfalsa = 11 * (j % 2) if (ns > 1 and bw < 38) else 0
                    cv.create_text(xb + bw / 2, min(yz, yv) - 2 - sfalsa, anchor="s",
                                   text=_fmt_it(v, ",.0f"), fill=col["fg"], font=("Arial", 7))


def _combo_conto(self, parent, var, bg=None):
    if bg:
        tk.Label(parent, text="Conto:", bg=bg, fg=self.TEXT_COLOR).pack(side=tk.LEFT, padx=(18, 4))
    else:
        ttk.Label(parent, text="Conto:").pack(side=tk.LEFT, padx=(14, 5))
    cb = ttk.Combobox(parent, values=_nomi_conti(), textvariable=var, style="Border.TCombobox",
                      state="readonly", width=22, height=15)
    cb.pack(side=tk.LEFT)
    return cb

def _combo_cat(self, parent, var, valori, width=22):
    return ttk.Combobox(parent, values=valori, textvariable=var, style="Border.TCombobox",
                        state="readonly", width=width, height=15)

def _pannello_corpo(self, tab, colonne, affiancato=True, orizzontale=True, peso_testo=58):
    fr = ttk.Frame(tab)
    fr_t, tree = _casella_tree(self, fr, colonne)
    graf = _Grafico(self, fr, orizzontale=orizzontale)
    if affiancato:
        fr.grid_rowconfigure(0, weight=1)
        fr.grid_columnconfigure(0, weight=peso_testo, uniform="corpo")
        fr.grid_columnconfigure(1, weight=100 - peso_testo, uniform="corpo")
        fr_t.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        graf.box.grid(row=0, column=1, sticky="nsew", padx=(4, 0))
    else:
        fr.grid_columnconfigure(0, weight=1)
        fr.grid_rowconfigure(0, weight=60, uniform="corpo")
        fr.grid_rowconfigure(1, weight=40, uniform="corpo")
        fr_t.grid(row=0, column=0, sticky="nsew", pady=(0, 4))
        graf.box.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
    return fr, tree, graf

def _aggrega_dati(self, categorie, filtro, conto=None, movs=None):
    ris = {}
    for d, v in (movs if movs is not None else _movimenti(self, conto)):
        if not filtro(d):
            continue
        cat = campo(v, "categoria", "").strip().title()
        if cat not in categorie:
            continue
        r = ris.setdefault(cat, {"num": 0, "uscite": 0.0, "entrate": 0.0, "max": 0.0})
        r["num"] += 1
        tipo = campo(v, "tipo", "")
        imp = campo(v, "importo", 0.0)
        r["max"] = max(r["max"], abs(imp))
        if tipo == "Uscita":
            r["uscite"] += imp
        elif tipo == "Entrata":
            r["entrate"] += imp
    return ris

COLS_DETT = [("Data", "Data", 95, "center", False), ("Categoria", "Categoria", 150, "w", False),
             ("Descrizione", "Descrizione", 260, "w", True), ("Tipo", "Tipo", 70, "center", False),
             ("Importo", "Importo", 100, "e", False), ("Conto", "Conto", 120, "center", False),
             ("Metodo", "Metodo", 115, "center", False), ("Ora", "Ora", 60, "center", False),
             ("Hashtag", "Hashtag", 150, "w", True)]
EXP_DETT = [("Data", "l", 11), ("Categoria", "l", 16), ("Descrizione", "l", 26), ("Tipo", "l", 7),
            ("Importo (€)", "r", 12), ("Conto", "l", 14), ("Metodo", "l", 12), ("Ora", "c", 5),
            ("Hashtag", "l", 16)]

def _tab_dettaglio(self, tab, categoria, conto_var, bt):
    today = datetime.date.today()
    mode_var = tk.StringVar(value="Giorno")
    day_var = tk.StringVar(value=str(today.day))
    month_var = tk.StringVar(value=MESI[today.month - 1])
    year_var = tk.StringVar(value=str(today.year))
    cat_var = tk.StringVar(value=categoria if isinstance(categoria, str) and categoria in self.categorie else TUTTE)
    futuri = _futuri_condiviso(self, tab)
    top = tk.Frame(tab, bg=self.COLOR_TOPLEVEL)
    top.pack(fill=tk.X, padx=6, pady=(8, 4))
    img_search = self.icone_gui.get("search")
    lbl = tk.Label(top, text=" Modalità:", image=img_search, compound="left", bg=self.COLOR_TOPLEVEL,
                   fg=self.TEXT_COLOR, font=("Arial", 10, "bold"))
    lbl.image = img_search
    lbl.pack(side=tk.LEFT, padx=(4, 4))
    mode_combo = ttk.Combobox(top, values=["Giorno", "Mese", "Anno", "Totale"], textvariable=mode_var,
                              style="Border.TCombobox", state="readonly", width=9)
    mode_combo.pack(side=tk.LEFT, padx=(0, 10))
    fr_per = tk.Frame(top, bg=self.COLOR_TOPLEVEL)
    fr_per.pack(side=tk.LEFT)
    anni = [str(a) for a in _anni_disponibili(self)]
    day_combo = ttk.Combobox(fr_per, values=[str(d) for d in range(1, 32)], textvariable=day_var,
                             style="Border.TCombobox", state="readonly", width=4)
    month_combo = ttk.Combobox(fr_per, values=MESI, textvariable=month_var,
                               style="Border.TCombobox", state="readonly", width=12)
    year_combo = ttk.Combobox(fr_per, values=anni, textvariable=year_var,
                              style="Border.TCombobox", state="readonly", width=6)

    def update_days(*_):
        try:
            n = calendar.monthrange(int(year_var.get()), MESI.index(month_var.get()) + 1)[1]
        except Exception:
            n = 31
        giorni = [str(d) for d in range(1, n + 1)]
        day_combo["values"] = giorni
        if day_var.get() not in giorni:
            day_var.set(giorni[-1])

    def update_period_inputs(*_):
        for w in fr_per.winfo_children():
            w.pack_forget()
        m = mode_var.get()
        if m == "Giorno":
            day_combo.pack(side=tk.LEFT)
            month_combo.pack(side=tk.LEFT, padx=(4, 4))
            year_combo.pack(side=tk.LEFT)
            update_days()
        elif m == "Mese":
            month_combo.pack(side=tk.LEFT, padx=(0, 4))
            year_combo.pack(side=tk.LEFT)
        elif m == "Anno":
            year_combo.pack(side=tk.LEFT)

    tk.Label(top, bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR, text="Categoria:").pack(side=tk.LEFT, padx=(18, 4))
    cat_combo = _combo_cat(self, top, cat_var, [TUTTE] + sorted(self.categorie, key=lambda c: c.lower()), 25)
    cat_combo.pack(side=tk.LEFT)
    ttk.Checkbutton(top, text="Includi movimenti futuri", variable=futuri).pack(side=tk.LEFT, padx=(15, 0))
    
    _combo_conto(self, top, conto_var, bg=self.COLOR_TOPLEVEL)

    pw, tree, graf = _pannello_corpo(self, tab, COLS_DETT, affiancato=False)
    barra = tk.Frame(tab, bg=self.COLOR_TOPLEVEL)
    barra.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=8)
    inf, lbl_info, lbl_hint = _riga_info(self, tab)
    inf.pack(fill=tk.X, padx=8, pady=(2, 0))
    pw.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
    stato = {"sosp": False, "voci": {}, "intest": [], "footer": [], "extra": [], "periodo": None}

    def periodo():
        mode = mode_var.get()
        try:
            y = int(year_var.get())
        except Exception:
            y = today.year
        try:
            m = MESI.index(month_var.get()) + 1
        except Exception:
            m = today.month
        if mode == "Giorno":
            try:
                g = datetime.date(y, m, int(day_var.get()))
            except Exception:
                g = today
            return mode, g.year, g.month, (lambda d: d == g), f"per il giorno {g.strftime('%d-%m-%Y')}"
        if mode == "Mese":
            return mode, y, m, (lambda d: d.year == y and d.month == m), f"per {MESI[m - 1]} {y}"
        if mode == "Anno":
            return mode, y, None, (lambda d: d.year == y), f"per l'anno {y}"
        return mode, None, None, (lambda d: True), "totali"

    def mostra(*_):
        if stato["sosp"]:
            return
        cat = cat_var.get()
        mode, anno_p, mese_p, sel, quando = periodo()
        movs = _movimenti(self, conto_var.get())
        oggi = datetime.date.today()
        filtered = [(d, e) for d, e in movs
                    if sel(d) and (futuri.get() or d <= oggi) and (cat == TUTTE or campo(e, "categoria", "") == cat)]
        intest = f"{'Entrate/Uscite' if cat == TUTTE else 'Spese ' + cat} {quando}{_suff_conto(conto_var.get())}"
        _svuota(tree)
        stato["voci"] = {}
        lbl_hint.config(text=("Doppio clic → Vai alla spesa nella lista principale  |  Clic destro → Copia nel form"
                              if mode == "Giorno" else
                              "Doppio clic → Movimenti della categoria nel periodo  |  Clic destro → Copia nel form"))
        if not filtered:
            lbl_info.config(text=f"Nessuna spesa per '{cat}'.")
            graf.imposta(intest, [], [])
            bt.imposta(0, 0.0, 0.0)
            return
        try:
            agganci = costruisci_mappa_conti_da_trasferimenti(_app.PORTAFOGLIO_BANCARIO)
        except Exception:
            agganci = {}
        uso = {}
        oggi = datetime.date.today()
        ent = usc = 0.0
        for d, e in sorted(filtered, key=lambda x: x[0], reverse=True):
            imp = abs(campo(e, "importo", 0.0))
            tipo = str(campo(e, "tipo", "")).capitalize()
            conto = self._conto_effettivo(e)
            if not conto:
                try:
                    conto = conto_da_mappa(agganci, uso, d.strftime("%d-%m-%Y"), float(imp), tipo) or ""
                except Exception:
                    conto = ""
            entrata = "entrata" in tipo.lower()
            if entrata:
                ent += imp
            else:
                usc += imp
            tag = "futuro" if d > oggi else ("entrata" if entrata else "uscita")
            hashtag = " ".join(campo(e, "hashtag", []) or [])
            iid = _inserisci(tree, (d.strftime("%d-%m-%Y"), campo(e, "categoria", ""), campo(e, "descrizione", ""),
                                    tipo, _fmt_it(imp), conto, campo(e, "metodo_pagamento", ""),
                                    campo(e, "ora", ""), hashtag), tag, entry=e,
                             info={"metodo": campo(e, "metodo_pagamento", ""), "conto": conto,
                                   "ora": campo(e, "ora", ""), "hashtag": campo(e, "hashtag", []),
                                   "id_ricorrenza": campo(e, "id_ricorrenza", ""),
                                   "id_spesa": campo(e, "id_spesa", ""),
                                   "data": d.strftime("%d-%m-%Y"), "categoria": campo(e, "categoria", ""),
                                   "importo": imp, "tipo": tipo})
            kv = (campo(e, "descrizione", "") or "(senza nome)").strip().title()
            stato["voci"].setdefault(kv, []).append(iid)
        n = len(filtered)
        lbl_info.config(text=f"{intest}  ·  {n} moviment{'o' if n == 1 else 'i'}")
        stato["intest"] = [intest, f"Movimenti: {n}"]
        stato["footer"] = [["", "Totale entrate", "", "", _fmt_it(ent)],
                           ["", "Totale uscite", "", "", _fmt_it(usc)],
                           ["", "Saldo finale", "", "", _fmt_it(ent - usc, "+,.2f")]]
        bt.imposta(0, ent, usc)
        chiave = "descrizione" if cat != TUTTE else "categoria"
        gruppi = {}
        for d, e in filtered:
            k = (campo(e, chiave, "") or "(senza nome)").strip().title()
            g = gruppi.setdefault(k, [0.0, 0.0, 0])
            g[2] += 1
            if "entrata" in str(campo(e, "tipo", "")).lower():
                g[0] += abs(campo(e, "importo", 0.0))
            else:
                g[1] += abs(campo(e, "importo", 0.0))
        ordinati = sorted(gruppi.items(), key=lambda x: -(x[1][0] + x[1][1]))
        graf.imposta(intest + (" – per categoria" if chiave == "categoria" else " – per voce"),
                     [(k, v[:2]) for k, v in ordinati], [("Entrate", "green"), ("Uscite", "red")],
                     chiavi=[k for k, _ in ordinati], azione=apri_voce,
                     dettagli=[f"Movimenti: {v[2]}" for _, v in ordinati],
                     suggerimento=("Doppio click: dettaglio categoria" if chiave == "categoria"
                                   else "Doppio click: evidenzia nella tabella"))

    def evidenzia(voce):
        ids = stato["voci"].get(voce)
        if not ids:
            return
        tree.selection_set(ids)
        tree.see(ids[0])
        tree.focus(ids[0])

    def apri_voce(chiave, _etichetta):
        if cat_var.get() == TUTTE:
            imposta(chiave)
        else:
            evidenzia(chiave)

    def doppio_click(event):
        iid = tree.identify_row(event.y)
        if not iid or iid not in tree._exp:
            return
        celle = tree._exp[iid]
        entry = tree._entry_lookup.get(iid)
        popup = tab.winfo_toplevel()
        mode, anno_p, mese_p, sel, quando = periodo()
        if mode == "Giorno":
            giorno = _parse_data(celle[0])
            if giorno is None:
                return
            id_sp = campo(entry, "id_spesa", "") if entry is not None else ""
            self.vai_a_spesa(giorno, popup, celle[2][:20], id_sp)
            return
        categoria_riga = celle[1].strip()
        if not categoria_riga:
            return
        _apri_transazioni(self, popup, [categoria_riga], anno_p, mese_p, conto_var.get(),
                          f"{categoria_riga} {quando}{_suff_conto(conto_var.get())}",
                          lambda d, v: sel(d) and _stessa_cat(campo(v, "categoria", ""), categoria_riga))

    def click_destro(event):
        iid = tree.identify_row(event.y)
        if not iid:
            return
        tree.selection_set(iid)
        entry = tree._entry_lookup.get(iid)
        if entry is None:
            return
        _copia_nel_form(self, entry, conto=tree._exp[iid][5].strip() or None)
        try:
            tab.winfo_toplevel().destroy()
        except tk.TclError:
            pass

    tree.bind("<Double-1>", doppio_click)
    tree.bind("<Button-3>", click_destro)

    def reset():
        mode_var.set("Giorno")
        day_var.set(str(today.day))
        month_var.set(MESI[today.month - 1])
        year_var.set(str(today.year))
        cat_var.set(TUTTE)
        conto_var.set(HOUSEHOLD_LABEL)
        update_period_inputs()

    _btn(self, barra, "salva", "Esporta", lambda: _esporta(self, tree, "Analisi_Categoria_Dettaglio", EXP_DETT, stato))
    _btn(self, barra, "reset", "Reset campi", reset)
    bt.registra_reset(0, reset)

    month_var.trace_add("write", update_days)
    year_var.trace_add("write", update_days)
    mode_combo.bind("<<ComboboxSelected>>", update_period_inputs)
    for v in (mode_var, month_var, year_var, day_var, cat_var, conto_var, futuri):
        v.trace_add("write", mostra)
    update_period_inputs()
    mostra()

    def imposta(c=None, modo=None, anno=None, mese=None):
        stato["sosp"] = True
        try:
            if isinstance(c, str):
                if c == TUTTE:
                    cat_var.set(TUTTE)
                else:
                    k = {x.lower(): x for x in self.categorie}.get(c.strip().lower())
                    if k:
                        cat_var.set(k)
                    else:
                        self.show_toast(f"Categoria '{c}' non trovata.")
            if modo in ("Giorno", "Mese", "Anno", "Totale"):
                mode_var.set(modo)
                if anno:
                    year_var.set(str(anno))
                if mese:
                    month_var.set(MESI[int(mese) - 1])
                update_period_inputs()
        finally:
            stato["sosp"] = False
        mostra()
    return imposta

COLS_RIEP = [("Categoria", "Categoria", 190, "w", True), ("Num", "Num", 55, "e", False),
             ("Uscite", "Uscite (€)", 105, "e", False), ("Entrate", "Entrate (€)", 105, "e", False),
             ("Saldo", "Saldo (€)", 105, "e", False)]
EXP_RIEP = [("Categoria", "l", 28), ("Num", "r", 5), ("Uscite (€)", "r", 14), ("Entrate (€)", "r", 14),
            ("Saldo (€)", "r", 14)]

COLS_AGG = [("Categoria", "Categoria", 155, "w", True), ("Num", "Num", 50, "e", False),
            ("Uscite", "Uscite (€)", 95, "e", False), ("Entrate", "Entrate (€)", 95, "e", False),
            ("Saldo", "Saldo (€)", 95, "e", False), ("Medio", "Importo medio", 100, "e", False),
            ("Max", "Importo max", 95, "e", False), ("Perc", "% uscite", 70, "e", False),
            ("MediaMese", "Media/mese (€)", 105, "e", False), ("DPrec", "Δ vs prec.", 90, "e", False),
            ("DAnno", "Δ anno prec.", 95, "e", False), ("Budget", "Budget (€)", 90, "e", False),
            ("PercBud", "% budget", 80, "e", False), ("Prev", "Prev. fine mese", 110, "e", False)]
EXP_AGG = [("Categoria", "l", 22), ("Num", "r", 4), ("Uscite (€)", "r", 12), ("Entrate (€)", "r", 12),
           ("Saldo (€)", "r", 12), ("Medio (€)", "r", 10), ("Max (€)", "r", 10), ("% usc.", "r", 7),
           ("Media/mese", "r", 11), ("Δ prec.", "r", 9), ("Δ anno", "r", 9), ("Budget (€)", "r", 10),
           ("% bud.", "r", 8), ("Prev. fine mese", "r", 14)]

def _vol(r):
    return r["uscite"] if r["uscite"] > 0 else r["entrate"]

def _fmt_pct(v, segno=False):
    return _fmt_it(v, "+,.1f" if segno else ",.1f") + "%"

def _fmt_delta(cur, prev):
    if prev is None:
        return "—"
    if prev <= 0.004:
        return "nuovo" if cur > 0.004 else "—"
    return _fmt_pct((cur - prev) / prev * 100, True)

def _mesi_in_periodo(date_list, anno, mese_n, oggi):
    if mese_n:
        return 1
    if anno is not None:
        if anno < oggi.year:
            return 12
        mesi = [d.month for d in date_list if d.year == anno]
        ultimo = max([oggi.month if anno == oggi.year else 1] + mesi)
        return max(1, min(12, ultimo))
    if not date_list:
        return 1
    primo, ultimo = min(date_list), max(max(date_list), oggi)
    return max(1, (ultimo.year - primo.year) * 12 + ultimo.month - primo.month + 1)

def _budget_dict(raw):
    out = {}
    for k, v in (raw or {}).items():
        try:
            if float(v) > 0:
                out[str(k).strip().title()] = float(v)
        except (TypeError, ValueError):
            pass
    return out

# Suggerimenti automatici di budget / target (basati sullo storico)
SUGG_MESI = 12      # finestra massima: ultimi 12 mesi chiusi (il mese in corso è escluso)
SUGG_MIN_MESI = 3   # sotto questa soglia lo storico è considerato troppo corto

def _fmt_campo(v):
    return f"{v:.2f}".replace(".", ",")

def _finestra_mesi(n, oggi=None):
    oggi = oggi or datetime.date.today()
    y, m = oggi.year, oggi.month
    out = []
    for _ in range(n):
        m -= 1
        if m == 0:
            y, m = y - 1, 12
        out.append((y, m))
    return out

def _mesi_storico(movs, mesi=SUGG_MESI, oggi=None):
    oggi = oggi or datetime.date.today()
    date = [d for d, _ in movs if d <= oggi]
    if not date:
        return 0
    primo = min(date)
    chiusi = (oggi.year - primo.year) * 12 + oggi.month - primo.month
    return max(0, min(mesi, chiusi))

def _totali_mensili(movs, tipo="Uscita", cat=None, n=SUGG_MESI, oggi=None):
    fin = _finestra_mesi(n, oggi)
    tot = dict.fromkeys(fin, 0.0)
    cat_k = cat.strip().title() if cat else None
    for d, v in movs:
        k = (d.year, d.month)
        if k not in tot or campo(v, "tipo", "") != tipo:
            continue
        if cat_k and campo(v, "categoria", "").strip().title() != cat_k:
            continue
        tot[k] += float(campo(v, "importo", 0.0))
    return [tot[k] for k in fin]

def _stima(valori):
    attivi = [x for x in valori if x > 0.004]
    if len(attivi) < SUGG_MIN_MESI:
        return None
    return (round(statistics.median(attivi), 2),
            round(sum(valori) / len(valori) * 12, 2),
            len(attivi))

def suggerisci_budget(movs, cat, n, oggi=None):
    if n < SUGG_MIN_MESI:
        return None
    return _stima(_totali_mensili(movs, "Uscita", cat, n, oggi))

def suggerimenti_target(self, movs, n, oggi=None):
    out = []
    if n >= SUGG_MIN_MESI:
        s = _stima(_totali_mensili(movs, "Uscita", None, n, oggi))
        if s:
            out.append(("Storico spese",
                        f"Mediana delle uscite totali mensili degli ultimi {n} mesi chiusi",
                        s[0], s[1]))
        e = _stima(_totali_mensili(movs, "Entrata", None, n, oggi))
        if e:
            m = round(e[0] * 0.8, 2)
            out.append(("Da entrate (50/30/20)",
                        f"80% della mediana delle entrate mensili ({_fmt_it(e[0])} €): il restante 20% resta al risparmio",
                        m, round(m * 12, 2)))
    bm = _budget_dict(getattr(self, "budget_categorie", {}))
    ba = _budget_dict(getattr(self, "budget_annuale_categorie", {}))
    if bm or ba:
        sm = round(sum(bm.values()), 2)
        cats = set(bm) | set(ba)
        sa = round(sum(ba.get(c) or bm.get(c, 0.0) * 12 for c in cats), 2)
        out.append(("Somma dei budget",
                    f"Somma dei budget delle categorie ({len(cats)} con budget); annuale = budget annuale, "
                    "oppure mensile × 12 se manca",
                    sm if sm > 0 else round(sa / 12, 2), sa))
    return out

def _centra(w, parent, wd, ht):
    top = parent.winfo_toplevel()
    top.update_idletasks()
    x = top.winfo_rootx() + (top.winfo_width() - wd) // 2
    y = top.winfo_rooty() + (top.winfo_height() - ht) // 2
    w.geometry(f"{wd}x{ht}+{max(x, 0)}+{max(y, 0)}")

def _popup_sugg_aperto(self):
    w = getattr(self, "_popup_sugg", None)
    if w is not None:
        try:
            if w.winfo_exists():
                w.deiconify()
                w.lift()
                w.focus_force()
                return True
        except tk.TclError:
            pass
        self._popup_sugg = None
    return False

def _fissa_popup(self, w, parent, wd, ht):
    self._popup_sugg = w
    w.bind("<Destroy>", lambda e: setattr(self, "_popup_sugg", None) if e.widget is w else None, add="+")
    w.transient(parent.winfo_toplevel())
    _centra(w, parent, wd, ht)
    w.resizable(False, False)
    try:
        w.attributes("-topmost", True)
    except tk.TclError:
        pass
    try:
        w.wait_visibility()
        w.grab_set()
    except tk.TclError:
        pass
    w.focus_set()

def _popup_suggerisci_target(self, parent, opzioni, tm_var, ta_var):
    if _popup_sugg_aperto(self):
        return
    top = parent.winfo_toplevel()
    bg = self.COLOR_TOPLEVEL
    w = tk.Toplevel(top, bg=bg)
    w.title("Suggerisci target")
    w.bind("<Escape>", lambda e: w.destroy())
    tk.Label(w, bg=bg, fg=self.TEXT_COLOR, font=("Arial", 9, "bold"), anchor="w",
             text="Scegli un criterio: i valori vengono inseriti nei campi, poi confermi con «Salva target».").pack(
        fill=tk.X, padx=12, pady=(12, 6))
    scelta = tk.IntVar(value=0)
    for i, (titolo, descr, m, a) in enumerate(opzioni):
        riga = tk.Frame(w, bg=bg)
        riga.pack(fill=tk.X, padx=12, pady=3)
        tk.Radiobutton(riga, variable=scelta, value=i, bg=bg, fg=self.TEXT_COLOR, selectcolor=bg,
                       activebackground=bg, activeforeground=self.TEXT_COLOR, highlightthickness=0, bd=0,
                       font=("Arial", 9, "bold"), anchor="w",
                       text=f"{titolo}  –  Mese € {_fmt_it(m)}  ·  Anno € {_fmt_it(a)}").pack(fill=tk.X)
        tk.Label(riga, bg=bg, fg="gray", font=("Arial", 8, "italic"), anchor="w", justify="left",
                 wraplength=590, text=descr).pack(fill=tk.X, padx=(24, 0))

    def applica():
        _t, _d, m, a = opzioni[scelta.get()]
        tm_var.set(_fmt_campo(m))
        ta_var.set(_fmt_campo(a))
        w.destroy()
        self.show_toast("Target suggerito inserito nei campi: premi «Salva target» per confermare")

    barra = tk.Frame(w, bg=bg)
    barra.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=10)
    _btn(self, barra, "salva", "Applica ai campi", applica)
    _btn(self, barra, "chiudi", "Annulla", w.destroy, side="right")
    _fissa_popup(self, w, parent, 640, 120 + 70 * len(opzioni))

def _popup_suggerisci_tutti(self, parent, righe, n, applica):
    if _popup_sugg_aperto(self):
        return
    top = parent.winfo_toplevel()
    bg = self.COLOR_TOPLEVEL
    w = tk.Toplevel(top, bg=bg)
    w.title("Suggerisci budget per tutte le categorie")
    w.bind("<Escape>", lambda e: w.destroy())
    tk.Label(w, bg=bg, fg=self.TEXT_COLOR, font=("Arial", 9), anchor="w", justify="left",
             text=(f"Proposta dalla mediana delle uscite mensili degli ultimi {n} mesi chiusi (mesi senza spesa esclusi).\n"
                   "Clicca sulla casella per includere/escludere una categoria. "
                   "Quelle che hanno già un budget partono deselezionate.")).pack(fill=tk.X, padx=12, pady=(12, 4))

    fr = ttk.Frame(w)
    fr.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)
    cols = (("Usa", "Usa", 50, "center"), ("Categoria", "Categoria", 220, "w"),
            ("BudAtt", "Mensile attuale (€)", 135, "e"), ("BudSug", "Mensile suggerito (€)", 150, "e"),
            ("AnnAtt", "Annuale attuale (€)", 130, "e"), ("AnnSug", "Annuale suggerito (€)", 150, "e"))
    tv = ttk.Treeview(fr, columns=[c[0] for c in cols], show="headings", selectmode="browse", height=12)
    for cid, tit, wd, anc in cols:
        tv.heading(cid, text=tit)
        tv.column(cid, width=wd, minwidth=40, anchor=anc, stretch=(cid == "Categoria"))
    sy = ttk.Scrollbar(fr, orient=tk.VERTICAL, style="Vertical.TScrollbar", command=tv.yview)
    tv.configure(yscrollcommand=sy.set)
    tv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    sy.pack(side=tk.RIGHT, fill=tk.Y)

    dati = {}
    for cat, bm_a, bm_s, ba_a, ba_s in righe:
        iid = tv.insert("", "end", values=("☐" if bm_a > 0 else "☑", cat,
                                           _fmt_it(bm_a) if bm_a > 0 else "—", _fmt_it(bm_s),
                                           _fmt_it(ba_a) if ba_a > 0 else "—", _fmt_it(ba_s)))
        dati[iid] = (cat, bm_s, ba_s, bm_a > 0)

    def toggle(e):
        iid = tv.identify_row(e.y)
        if iid and tv.identify_column(e.x) == "#1":
            tv.set(iid, "Usa", "☐" if tv.set(iid, "Usa") == "☑" else "☑")

    tv.bind("<Button-1>", toggle, add="+")

    def segna(fn):
        for iid in tv.get_children():
            tv.set(iid, "Usa", "☑" if fn(dati[iid]) else "☐")

    con_annuale = tk.BooleanVar(value=True)
    opz = tk.Frame(w, bg=bg)
    opz.pack(fill=tk.X, padx=12, pady=(2, 0))
    ttk.Checkbutton(opz, text="Applica anche il budget annuale", variable=con_annuale).pack(side=tk.LEFT)

    def conferma():
        scelte = [(dati[i][0], dati[i][1], dati[i][2]) for i in tv.get_children() if tv.set(i, "Usa") == "☑"]
        if not scelte:
            self.show_toast("Nessuna categoria selezionata.")
            return
        w.destroy()
        applica(scelte, bool(con_annuale.get()))

    barra = tk.Frame(w, bg=bg)
    barra.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=10)
    _btn(self, barra, "salva", "Applica selezionati", conferma)
    _btn(self, barra, "filtri", "Seleziona tutte", lambda: segna(lambda d: True))
    _btn(self, barra, "reset", "Deseleziona tutte", lambda: segna(lambda d: False))
    _btn(self, barra, "reset", "Solo senza budget", lambda: segna(lambda d: not d[3]))
    _btn(self, barra, "chiudi", "Annulla", w.destroy, side="right")
    _fissa_popup(self, w, parent, 900, 500)

def _tag_saldo(entrate, uscite):
    if entrate - uscite > 0.004:
        return "entrata"
    if uscite - entrate > 0.004:
        return "uscita"
    return None

def _tab_aggrega(self, tab, vai, conto_var, bt):
    today = datetime.date.today()
    mese_var = tk.StringVar(value="Tutti")
    anno_var = tk.StringVar(value=str(today.year))
    futuri = _futuri_condiviso(self, tab)

    top = ttk.Frame(tab)
    top.pack(fill=tk.X, padx=6, pady=(8, 4))
    ttk.Label(top, text="Mese:").pack(side=tk.LEFT, padx=(0, 5))
    ttk.Combobox(top, values=["Tutti"] + MESI, textvariable=mese_var, style="Border.TCombobox",
                 state="readonly", width=12).pack(side=tk.LEFT)
    ttk.Label(top, text="Anno:").pack(side=tk.LEFT, padx=(10, 5))
    ttk.Combobox(top, values=["Tutti"] + [str(a) for a in _anni_disponibili(self)], textvariable=anno_var,
                 style="Border.TCombobox", state="readonly", width=8).pack(side=tk.LEFT)
    ttk.Checkbutton(top, text="Includi movimenti futuri nei totali", variable=futuri).pack(side=tk.LEFT, padx=(20, 0))
    _combo_conto(self, top, conto_var)

    box = ttk.LabelFrame(tab, text="Seleziona fino a 10 categorie da analizzare")
    box.pack(fill=tk.X, padx=6, pady=(4, 6))
    griglia = ttk.Frame(box)
    griglia.pack(fill=tk.X, padx=6, pady=4)
    valori = [NESSUNA] + sorted(self.categorie_tipi.keys())
    combo_vars = []
    for i in range(10):
        griglia.grid_columnconfigure(i % 5, weight=1, uniform="agg")
        v = tk.StringVar(value=NESSUNA)
        _combo_cat(self, griglia, v, valori, 26).grid(row=i // 5, column=i % 5, sticky="ew", padx=4, pady=2)
        combo_vars.append(v)

    barra = tk.Frame(tab, bg=self.COLOR_TOPLEVEL)
    barra.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=8)
    pw, tree, graf = _pannello_corpo(self, tab, COLS_AGG, affiancato=False)
    inf, lbl_info, _lbl_hint = _riga_info(
        self, tab, "Doppio clic → Movimenti della categoria  |  Doppio clic sulle barre → Dettaglio")
    inf.pack(fill=tk.X, padx=8, pady=(2, 0))
    pw.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
    stato = {"intest": [], "footer": [], "extra": [], "anno": None, "mese": None, "etich": ""}

    def analizza(*_):
        scelte = {v.get().strip().title() for v in combo_vars if v.get() != NESSUNA}
        anno = None
        if anno_var.get() != "Tutti":
            try:
                anno = int(anno_var.get())
            except Exception:
                self.show_custom_warning("Errore", "Anno non valido.")
                return
        mese = mese_var.get()
        oggi = datetime.date.today()

        def filtro(d):
            if not futuri.get() and d > oggi:
                return False
            return (anno is None or d.year == anno) and (mese == "Tutti" or d.month == MESI.index(mese) + 1)

        _svuota(tree)
        stato["anno"] = anno
        stato["mese"] = None if mese == "Tutti" else MESI.index(mese) + 1
        conto = conto_var.get()
        movs = _movimenti(self, conto)
        mese_n = None if mese == "Tutti" else MESI.index(mese) + 1
        ris = _aggrega_dati(self, scelte, filtro, movs=movs)
        etich = "Tutti gli anni" if anno is None else str(anno)
        stato["etich"] = f"{mese} {etich}"
        titolo = f"Analisi categorie – {mese} {etich}{_suff_conto(conto)}"
        tutte = {k.strip().title() for k in self.categorie_tipi.keys()}
        tot_usc_periodo = sum(r["uscite"] for r in _aggrega_dati(self, tutte, filtro, movs=movs).values())
        date_sel = [d for d, v in movs if filtro(d) and campo(v, "categoria", "").strip().title() in scelte]
        n_mesi = _mesi_in_periodo(date_sel, anno, mese_n, oggi)
        parziale_m = anno == oggi.year and mese_n == oggi.month
        parziale_a = anno == oggi.year and mese_n is None
        parziale = parziale_m or parziale_a

        def mk_filtro(y, m):
            def f(d):
                if d.year != y or (m is not None and d.month != m):
                    return False
                if parziale_m:
                    return d.day <= oggi.day
                if parziale_a:
                    return (d.month, d.day) <= (oggi.month, oggi.day)
                return True
            return f

        ris_prec = ris_anno = None
        txt_prec = txt_anno = ""
        if anno is not None and mese_n:
            py, pm = (anno, mese_n - 1) if mese_n > 1 else (anno - 1, 12)
            ris_prec = _aggrega_dati(self, scelte, mk_filtro(py, pm), movs=movs)
            ris_anno = _aggrega_dati(self, scelte, mk_filtro(anno - 1, mese_n), movs=movs)
            txt_prec = f"Δ vs prec.: rispetto a {MESI[pm - 1]} {py}"
            txt_anno = f"Δ anno prec.: rispetto a {MESI[mese_n - 1]} {anno - 1}"
        elif anno is not None:
            ris_prec = _aggrega_dati(self, scelte, mk_filtro(anno - 1, None), movs=movs)
            txt_prec = f"Δ vs prec.: rispetto al {anno - 1}"
        if parziale and txt_prec:
            txt_prec += " (stesso intervallo di giorni)"
            txt_anno += " (stesso intervallo di giorni)" if txt_anno else ""
        ris_oggi = _aggrega_dati(self, scelte, lambda d: filtro(d) and d <= oggi, movs=movs)
        ris_cfr = ris_oggi if parziale else ris

        bud_m = _budget_dict(getattr(self, "budget_categorie", {}))
        bud_a = _budget_dict(getattr(self, "budget_annuale_categorie", {}))

        def budget_periodo(cat):
            if mese_n:
                return bud_m.get(cat, 0.0)
            if anno is not None and bud_a.get(cat):
                return bud_a[cat]
            return bud_m.get(cat, 0.0) * n_mesi
        prev_fine = {}
        if parziale_m:
            gg_mese = calendar.monthrange(oggi.year, oggi.month)[1]
            for cat, r in ris.items():
                spesa_oggi = ris_oggi.get(cat, {}).get("uscite", 0.0)
                if r["uscite"] > 0 or spesa_oggi > 0:
                    prev_fine[cat] = max(r["uscite"], spesa_oggi / oggi.day * gg_mese)

        te = tu = 0.0
        tn = 0
        tmax = 0.0
        t_vol = t_cfr = t_prec = t_anno = 0.0
        t_bud = t_usc_bud = t_prev = 0.0
        ordinati = sorted(ris.items(), key=lambda x: -(x[1]["entrate"] - x[1]["uscite"]))
        for cat, r in ordinati:
            vol = _vol(r)
            cfr = _vol(ris_cfr.get(cat, {"uscite": 0.0, "entrate": 0.0}))
            p_prec = None if ris_prec is None else _vol(ris_prec.get(cat, {"uscite": 0.0, "entrate": 0.0}))
            p_anno = None if ris_anno is None else _vol(ris_anno.get(cat, {"uscite": 0.0, "entrate": 0.0}))
            bud = budget_periodo(cat)
            superato = bud > 0 and r["uscite"] > bud
            perc_usc = (r["uscite"] / tot_usc_periodo * 100) if (tot_usc_periodo > 0 and r["uscite"] > 0) else None
            if bud > 0 and r["uscite"] > 0:
                pb = r["uscite"] / bud * 100
                txt_pb = _fmt_pct(pb) + (" ▲" if pb > 100 else "")
                t_usc_bud += r["uscite"]
            else:
                txt_pb = "—"
            if bud > 0:
                t_bud += bud
            _inserisci(tree, (cat, r["num"], _fmt_it(r["uscite"]), _fmt_it(r["entrate"]),
                              _fmt_it(r["entrate"] - r["uscite"], "+,.2f"),
                              _fmt_it((r["uscite"] + r["entrate"]) / r["num"]), _fmt_it(r["max"]),
                              "—" if perc_usc is None else _fmt_pct(perc_usc),
                              _fmt_it(vol / n_mesi) if not mese_n else "—",
                              _fmt_delta(cfr, p_prec), _fmt_delta(cfr, p_anno),
                              _fmt_it(bud) if bud > 0 else "—", txt_pb,
                              _fmt_it(prev_fine[cat]) if cat in prev_fine else "—"),
                       "budget_superato" if superato else _tag_saldo(r["entrate"], r["uscite"]))
            te += r["entrate"]
            tu += r["uscite"]
            tn += r["num"]
            tmax = max(tmax, r["max"])
            t_vol += vol
            t_cfr += cfr
            t_prec += p_prec or 0.0
            t_anno += p_anno or 0.0
            t_prev += prev_fine.get(cat, 0.0)
        stato["intest"] = [titolo]
        extra = [t for t in (txt_prec, txt_anno) if t]
        if mese_n is None and ordinati:
            extra.append(f"Media/mese calcolata su {n_mesi} mes{'e' if n_mesi == 1 else 'i'}")
        if bud_m or bud_a:
            extra.append("Budget: mensile" + (" · annuale se impostato (vista Anno)" if anno is not None and not mese_n else "")
                         + (f" × {n_mesi} mesi" if not mese_n and not (anno is not None and bud_a) else "")
                         + " · ▲ = oltre budget")
        if prev_fine:
            extra.append(f"Prev. fine mese: stima lineare (speso fino a oggi ÷ giorno {oggi.day} × {gg_mese} giorni)")
        stato["extra"] = extra
        if ordinati:
            stato["footer"] = [["Totale", tn, _fmt_it(tu), _fmt_it(te), _fmt_it(te - tu, "+,.2f"),
                                _fmt_it((tu + te) / tn), _fmt_it(tmax),
                                _fmt_pct(tu / tot_usc_periodo * 100) if tot_usc_periodo > 0 and tu > 0 else "—",
                                _fmt_it(t_vol / n_mesi) if not mese_n else "—",
                                _fmt_delta(t_cfr, t_prec if ris_prec is not None else None),
                                _fmt_delta(t_cfr, t_anno if ris_anno is not None else None),
                                _fmt_it(t_bud) if t_bud > 0 else "—",
                                _fmt_pct(t_usc_bud / t_bud * 100) if t_bud > 0 and t_usc_bud > 0 else "—",
                                _fmt_it(t_prev) if prev_fine else "—"]]
        else:
            stato["footer"] = []
        testo_info = titolo
        if prev_fine:
            testo_info += f"  ·  Previsione uscite a fine mese: {_fmt_it(t_prev)} €"
        lbl_info.config(text=testo_info if scelte else "Seleziona almeno una categoria da analizzare")
        if scelte:
            bt.imposta(1, te, tu)
        else:
            bt.imposta(1, None, None)
        if anno is None:
            modo, a_n, m_n = "Totale", None, None
        elif mese != "Tutti":
            modo, a_n, m_n = "Mese", anno, MESI.index(mese) + 1
        else:
            modo, a_n, m_n = "Anno", anno, None
        graf.imposta(f"Categorie a confronto – {mese} {etich}{_suff_conto(conto_var.get())}",
                     [(c, [r["entrate"], r["uscite"]]) for c, r in ordinati],
                     [("Entrate", "green"), ("Uscite", "red")],
                     chiavi=[c for c, _ in ordinati],
                     azione=lambda k, _e, mo=modo, a=a_n, m=m_n: vai(k, mo, a, m),
                     dettagli=[f"Movimenti: {r['num']}\nSaldo: {_fmt_it(r['entrate'] - r['uscite'], '+,.2f')} €\n"
                               f"Medio: {_fmt_it((r['uscite'] + r['entrate']) / r['num'])} €  ·  Max: {_fmt_it(r['max'])} €"
                               for _, r in ordinati],
                     suggerimento="Doppio click: apri nel Dettaglio",
                     evidenza={(i, 1): "orange" for i, (c, r) in enumerate(ordinati)
                               if budget_periodo(c) > 0 and r["uscite"] > budget_periodo(c)})

    def doppio_click(event):
        iid = tree.identify_row(event.y)
        if not iid or iid not in tree._exp:
            return
        cat = tree._exp[iid][0]
        anno, mese = stato["anno"], stato["mese"]
        oggi = datetime.date.today()
        sel = lambda d, v: ((anno is None or d.year == anno) and (mese is None or d.month == mese)
                            and (futuri.get() or d <= oggi) and _stessa_cat(campo(v, "categoria", ""), cat))
        _apri_transazioni(self, tab.winfo_toplevel(), [cat], anno, mese, conto_var.get(),
                          f"{cat} – {stato['etich']}{_suff_conto(conto_var.get())}", sel)

    tree.bind("<Double-1>", doppio_click)

    def reset():
        mese_var.set("Tutti")
        anno_var.set(str(today.year))
        conto_var.set(HOUSEHOLD_LABEL)
        for v in combo_vars:
            v.set(NESSUNA)
        _svuota(tree)
        lbl_info.config(text="Seleziona almeno una categoria da analizzare")
        graf.imposta("", [], [])

    _btn(self, barra, "salva", "Esporta", lambda: _esporta(self, tree, "Analisi_Categorie_Aggrega", EXP_AGG, stato))
    _btn(self, barra, "reset", "Reset campi", reset)
    bt.registra_reset(1, reset)
    for v in [mese_var, anno_var, futuri, conto_var] + combo_vars:
        v.trace_add("write", analizza)
    lbl_info.config(text="Seleziona almeno una categoria da analizzare")
    graf.imposta("Seleziona almeno una categoria", [], [])

def _tab_time_machine(self, tab, vai, conto_var, bt):
    anno_var = tk.StringVar(value=str(datetime.date.today().year))
    futuri = _futuri_condiviso(self, tab)
    selezioni = {}
    combo_vars, combo_w = [], []

    top = ttk.Frame(tab)
    top.pack(fill=tk.X, padx=6, pady=(8, 4))
    ttk.Label(top, text="Anno:").pack(side=tk.LEFT, padx=(0, 5))
    anno_combo = ttk.Combobox(top, textvariable=anno_var, style="Border.TCombobox", state="readonly", width=8,
                              values=["Tutti"] + [str(a) for a in _anni_disponibili(self)])
    anno_combo.pack(side=tk.LEFT)
    _btn(self, top, "reset", "Anno corrente",
         lambda: [anno_var.set(str(datetime.date.today().year)), aggiorna_interfaccia()])
    ttk.Checkbutton(top, text="Includi movimenti futuri nei totali", variable=futuri).pack(side=tk.LEFT, padx=(20, 0))
    _combo_conto(self, top, conto_var)

    band = ttk.Frame(tab)
    band.pack(fill=tk.X, padx=6, pady=(4, 4))
    man = ttk.LabelFrame(band, text="Selezione manuale")
    man.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 6))
    mgr = ttk.Frame(man)
    mgr.pack(padx=6, pady=4)
    for i in range(10):
        v = tk.StringVar(value=NESSUNA)
        cb = _combo_cat(self, mgr, v, [NESSUNA], 21)
        cb.grid(row=i // 3, column=i % 3, padx=2, pady=2)
        combo_vars.append(v)
        combo_w.append(cb)
    topf = tk.LabelFrame(band, text=" Top 10 categorie per risparmio ", bg=self.COLOR_TOPLEVEL,
                         fg=self.TEXT_COLOR, bd=1)
    topf.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    barra = tk.Frame(tab, bg=self.COLOR_TOPLEVEL)
    barra.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=8)
    pw, tree, graf = _pannello_corpo(self, tab, COLS_RIEP[:4] + [("Saldo", "Risparmio (€)", 110, "e", False)],
                                     affiancato=True)
    inf, lbl_info, _lbl_hint = _riga_info(
        self, tab, "Doppio clic → Movimenti della categoria  |  Doppio clic sulle barre → Dettaglio")
    inf.pack(fill=tk.X, padx=8, pady=(2, 0))
    pw.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
    stato = {"intest": [], "footer": [], "extra": [], "anno": None, "periodo": ""}
    exp_tm = EXP_RIEP[:4] + [("Risparmio (€)", "r", 14)]

    def contatori():
        anno = anno_var.get()
        oggi = datetime.date.today()
        c = {}
        for d, v in _movimenti(self, conto_var.get()):
            if not futuri.get() and d > oggi:
                continue
            if anno != "Tutti" and d.year != int(anno):
                continue
            cat = campo(v, "categoria", "").strip().lower()
            if not cat:
                continue
            r = c.setdefault(cat, {"count": 0, "uscite": 0.0, "entrate": 0.0})
            r["count"] += 1
            tipo, imp = campo(v, "tipo", ""), campo(v, "importo", 0.0)
            if tipo == "Uscita":
                r["uscite"] += imp
            elif tipo == "Entrata":
                r["entrate"] += imp
        for r in c.values():
            r["risparmio"] = r["uscite"] - r["entrate"]
        return c

    sosp = {"v": False}

    def aggiorna_interfaccia(*_):
        sosp["v"] = True
        try:
            _ricostruisci()
        finally:
            sosp["v"] = False
        simula()

    def _ricostruisci():
        c = contatori()
        tutte = sorted({k.lower() for k in c} | {k.lower() for k in self.categorie_tipi})
        for v, cb in zip(combo_vars, combo_w):
            cb["values"] = [NESSUNA] + tutte
            if v.get().strip().lower() not in tutte:
                v.set(NESSUNA)
        prec = {k for k, (v, _) in selezioni.items() if v.get()}
        for w in topf.winfo_children():
            w.destroy()
        selezioni.clear()
        top10 = sorted(c.items(), key=lambda x: -x[1]["risparmio"])[:10]
        for i, (cat, dati) in enumerate(top10):
            v = tk.BooleanVar(value=(cat in prec))
            v.trace_add("write", simula)
            selezioni[cat] = (v, dati)
            nome = cat.title() if len(cat) <= 14 else cat.title()[:13] + "…"
            tk.Checkbutton(topf, text=f"{nome} – {dati['count']}× · {_fmt_it(dati['risparmio'])} €", variable=v,
                           bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR, selectcolor=self.COLOR_TOPLEVEL,
                           activebackground=self.COLOR_TOPLEVEL, activeforeground=self.TEXT_COLOR,
                           highlightthickness=0, bd=0).grid(row=i % 4, column=i // 4, sticky="w", padx=4, pady=2)

    def simula(*_):
        if sosp["v"]:
            return
        c = contatori()
        anno = anno_var.get()
        scelte = {k for k, (v, _) in selezioni.items() if v.get()}
        for v in combo_vars:
            val = v.get().strip().lower()
            if val and val != NESSUNA.lower() and val in c:
                scelte.add(val)
        ris = sorted(((k, c[k]) for k in scelte if k in c), key=lambda x: -x[1]["risparmio"])
        periodo = ("Tutti gli anni" if anno == "Tutti" else f"Anno {anno}") + _suff_conto(conto_var.get())
        proiez = "su tutti gli anni disponibili" if anno == "Tutti" else f"nel {anno}"
        stato["anno"] = None if anno == "Tutti" else int(anno)
        stato["periodo"] = periodo
        _svuota(tree)
        if not ris:
            lbl_info.config(text="Seleziona almeno una categoria")
            graf.imposta("Seleziona almeno una categoria", [], [])
            bt.imposta(2, None, None)
            stato["intest"], stato["footer"], stato["extra"] = [], [], []
            return
        tot = tn = tu = te = 0.0
        for k, r in ris:
            _inserisci(tree, (k.title(), r["count"], _fmt_it(r["uscite"]), _fmt_it(r["entrate"]),
                              _fmt_it(r["risparmio"])),
                       _tag_saldo(r["entrate"], r["uscite"]))
            tot += r["risparmio"]
            tn += r["count"]
            tu += r["uscite"]
            te += r["entrate"]
        lbl_info.config(text=f"Time Machine – {periodo}  ·  Risparmio totale teorico: {_fmt_it(tot)} €")
        stato["intest"] = [f"Time Machine – {periodo}",
                           f"Proiezione del risparmio ottenibile {proiez}, escludendo le categorie selezionate."]
        stato["footer"] = [["Totale", int(tn), _fmt_it(tu), _fmt_it(te), _fmt_it(tot)]]
        stato["extra"] = [f"Risparmio totale teorico: {_fmt_it(tot)} € (Uscite - Entrate delle categorie selezionate)"]
        bt.imposta(2, sum(r["entrate"] for _, r in ris), sum(r["uscite"] for _, r in ris))
        if anno == "Tutti":
            modo, a_n = "Totale", None
        else:
            modo, a_n = "Anno", anno
        graf.imposta(f"Risparmio teorico per categoria – {periodo}",
                     [(k.title(), [r["risparmio"]]) for k, r in ris], [("Risparmio", "accent")],
                     chiavi=[k for k, _ in ris],
                     azione=lambda k, _e, mo=modo, a=a_n: vai(k, mo, a, None),
                     dettagli=[f"Movimenti: {r['count']}\nUscite: {_fmt_it(r['uscite'])} €\n"
                               f"Entrate: {_fmt_it(r['entrate'])} €" for _, r in ris],
                     suggerimento="Doppio click: apri nel Dettaglio")

    def doppio_click(event):
        iid = tree.identify_row(event.y)
        if not iid or iid not in tree._exp:
            return
        cat = tree._exp[iid][0]
        anno = stato["anno"]
        oggi = datetime.date.today()
        sel = lambda d, v: ((anno is None or d.year == anno) and (futuri.get() or d <= oggi)
                            and _stessa_cat(campo(v, "categoria", ""), cat))
        _apri_transazioni(self, tab.winfo_toplevel(), [cat], anno, None, conto_var.get(),
                          f"{cat} – {stato['periodo']}", sel)

    tree.bind("<Double-1>", doppio_click)

    def reset():
        sosp["v"] = True
        anno_var.set(str(datetime.date.today().year))
        conto_var.set(HOUSEHOLD_LABEL)
        for v in combo_vars:
            v.set(NESSUNA)
        for v, _ in selezioni.values():
            v.set(False)
        sosp["v"] = False
        aggiorna_interfaccia()

    _btn(self, barra, "salva", "Esporta", lambda: _esporta(self, tree, "Time_Machine", exp_tm, stato))
    _btn(self, barra, "reset", "Reset campi", reset)
    bt.registra_reset(2, reset)
    anno_combo.bind("<<ComboboxSelected>>", aggiorna_interfaccia)
    futuri.trace_add("write", aggiorna_interfaccia)
    conto_var.trace_add("write", aggiorna_interfaccia)
    for v in combo_vars:
        v.trace_add("write", simula)
    aggiorna_interfaccia()

COLS_TREND = [("Mese", "Mese", 100, "w", True), ("Num", "Num", 50, "e", False),
              ("Uscite", "Uscite (€)", 100, "e", False), ("Entrate", "Entrate (€)", 100, "e", False),
              ("Saldo", "Saldo (€)", 100, "e", False), ("Var", "Var. uscite %", 120, "e", False)]
EXP_TREND = [("Mese", "l", 12), ("Num", "r", 5), ("Uscite (€)", "r", 14), ("Entrate (€)", "r", 14),
             ("Saldo (€)", "r", 14), ("Var. uscite %", "r", 13)]

def _tab_trend(self, tab, categoria, vai, conto_var, bt):
    today = datetime.date.today()
    anno_var = tk.StringVar(value=str(today.year))
    cat_var = tk.StringVar(value=categoria if isinstance(categoria, str) and categoria in self.categorie else TUTTE)
    futuri = _futuri_condiviso(self, tab)

    top = ttk.Frame(tab)
    top.pack(fill=tk.X, padx=6, pady=(8, 4))
    ttk.Label(top, text="Anno:").pack(side=tk.LEFT, padx=(0, 5))
    ttk.Combobox(top, values=[str(a) for a in _anni_disponibili(self)], textvariable=anno_var,
                 style="Border.TCombobox", state="readonly", width=8).pack(side=tk.LEFT)
    ttk.Label(top, text="Categoria:").pack(side=tk.LEFT, padx=(14, 5))
    cat_combo = _combo_cat(self, top, cat_var, [TUTTE] + sorted(self.categorie, key=lambda c: c.lower()), 25)
    cat_combo.pack(side=tk.LEFT)
    ttk.Checkbutton(top, text="Includi movimenti futuri", variable=futuri).pack(side=tk.LEFT, padx=(20, 0))
    _combo_conto(self, top, conto_var)

    barra = tk.Frame(tab, bg=self.COLOR_TOPLEVEL)
    barra.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=8)
    pw, tree, graf = _pannello_corpo(self, tab, COLS_TREND, affiancato=True, orizzontale=False, peso_testo=50)
    inf, lbl_info, _lbl_hint = _riga_info(
        self, tab, "Doppio clic → Movimenti del mese  |  Doppio clic sulle barre → Dettaglio del mese")
    inf.pack(fill=tk.X, padx=8, pady=(2, 0))
    pw.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
    stato = {"intest": [], "footer": [], "extra": []}

    def aggiorna(*_):
        try:
            anno = int(anno_var.get())
        except Exception:
            return
        cat = cat_var.get()
        oggi = datetime.date.today()
        mesi = {m: {"n": 0, "u": 0.0, "e": 0.0} for m in range(1, 13)}
        for d, v in _movimenti(self, conto_var.get()):
            if d.year != anno or (not futuri.get() and d > oggi):
                continue
            if cat != TUTTE and campo(v, "categoria", "") != cat:
                continue
            r = mesi[d.month]
            r["n"] += 1
            tipo, imp = campo(v, "tipo", ""), campo(v, "importo", 0.0)
            if tipo == "Uscita":
                r["u"] += imp
            elif tipo == "Entrata":
                r["e"] += imp
        sc = _suff_conto(conto_var.get())
        nome_cat = "tutte le categorie" if cat == TUTTE else cat
        _svuota(tree)
        tn = tu = te = 0.0
        prec = None
        attivi = []
        for m in range(1, 13):
            r = mesi[m]
            if r["n"] and prec:
                var = f"{(r['u'] - prec) / prec * 100:+.1f}".replace(".", ",")
            else:
                var = ""
            if datetime.date(anno, m, 1) > oggi:
                tag = "futuro"
            else:
                tag = _tag_saldo(r["e"], r["u"]) if r["n"] else None
            _inserisci(tree, (MESI[m - 1], r["n"], _fmt_it(r["u"]), _fmt_it(r["e"]),
                              _fmt_it(r["e"] - r["u"], "+,.2f"), var), tag, extra=m if r["n"] else None)
            tn += r["n"]
            tu += r["u"]
            te += r["e"]
            if r["n"]:
                attivi.append((m, r["u"]))
                prec = r["u"] if r["u"] else prec
        stato["intest"] = [f"Andamento mensile – {nome_cat} – {anno}{sc}"]
        stato["footer"] = [["Totale", int(tn), _fmt_it(tu), _fmt_it(te), _fmt_it(te - tu, "+,.2f"), ""]]
        stato["extra"] = []
        info = f"Andamento mensile – {nome_cat} – {anno}{sc}"
        if attivi:
            mx = max(attivi, key=lambda x: x[1])
            r1 = f"Media uscite sui {len(attivi)} mesi con movimenti: {_fmt_it(tu / len(attivi))} €"
            r2 = f"Mese con più uscite: {MESI[mx[0] - 1]} ({_fmt_it(mx[1])} €)"
            stato["extra"] = ["", r1, r2]
            info += f"  ·  {r1}  ·  {r2}"
        lbl_info.config(text=info)
        bt.imposta(3, te, tu)
        graf.imposta(f"Entrate e uscite per mese – {nome_cat} – {anno}{sc}",
                     [(MESI[m - 1][:3], [mesi[m]["e"], mesi[m]["u"]]) for m in range(1, 13)],
                     [("Entrate", "green"), ("Uscite", "red")],
                     chiavi=[m if mesi[m]["n"] else None for m in range(1, 13)],
                     azione=lambda m, _e, c=cat, a=anno: vai(c, "Mese", a, m),
                     dettagli=[(f"{MESI[m - 1]}\nMovimenti: {mesi[m]['n']}\n"
                                f"Saldo: {_fmt_it(mesi[m]['e'] - mesi[m]['u'], '+,.2f')} €")
                               if mesi[m]["n"] else f"{MESI[m - 1]}\nNessun movimento" for m in range(1, 13)],
                     suggerimento="Doppio click: movimenti del mese nel Dettaglio")

    def doppio_click(event):
        iid = tree.identify_row(event.y)
        if not iid or iid not in tree._exp:
            return
        m = tree._extra.get(iid)
        if not m:
            return
        try:
            anno = int(anno_var.get())
        except Exception:
            return
        cat = cat_var.get()
        oggi = datetime.date.today()
        sel = lambda d, v: (d.year == anno and d.month == m and (futuri.get() or d <= oggi)
                            and (cat == TUTTE or campo(v, "categoria", "") == cat))
        _apri_transazioni(self, tab.winfo_toplevel(), [] if cat == TUTTE else [cat], anno, m, conto_var.get(),
                          f"{'Tutte le categorie' if cat == TUTTE else cat} – {MESI[m - 1]} {anno}"
                          f"{_suff_conto(conto_var.get())}", sel)

    tree.bind("<Double-1>", doppio_click)

    def reset():
        anno_var.set(str(today.year))
        cat_var.set(TUTTE)
        conto_var.set(HOUSEHOLD_LABEL)

    _btn(self, barra, "salva", "Esporta", lambda: _esporta(self, tree, "Analisi_Categorie_Trend", EXP_TREND, stato))
    _btn(self, barra, "reset", "Reset campi", reset)
    bt.registra_reset(3, reset)
    for v in (anno_var, cat_var, futuri, conto_var):
        v.trace_add("write", aggiorna)
    aggiorna()

    def imposta_categoria(c):
        if isinstance(c, str) and c in self.categorie:
            cat_var.set(c)
    return imposta_categoria

GIORNI = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
FASCE = [("Notte (00–06)", 0, 6), ("Mattina (06–12)", 6, 12), ("Pomeriggio (12–18)", 12, 18), ("Sera (18–24)", 18, 24)]
SENZA_ORA = "Senza orario"
MODI_DIST = ["Giorno della settimana", "Fascia oraria", "Ora"]
COLS_DIST = [("Gruppo", "Gruppo", 90, "w", True), ("Num", "Num", 50, "e", False),
             ("Uscite", "Uscite (€)", 90, "e", False), ("Entrate", "Entrate (€)", 90, "e", False),
             ("Saldo", "Saldo (€)", 90, "e", False), ("Medio", "Importo medio", 95, "e", False),
             ("Perc", "% uscite", 70, "e", False)]
EXP_DIST = [("Gruppo", "l", 22), ("Num", "r", 5), ("Uscite (€)", "r", 14), ("Entrate (€)", "r", 14),
            ("Saldo (€)", "r", 14), ("Medio (€)", "r", 12), ("% usc.", "r", 8)]

def _ora_di(v):
    s = str(campo(v, "ora", "") or "").strip()
    try:
        h = int(s.split(":")[0])
    except Exception:
        return None
    return h if 0 <= h <= 23 else None

def _chiave_dist(modo, d, v):
    if modo == MODI_DIST[0]:
        return d.weekday(), GIORNI[d.weekday()]
    h = _ora_di(v)
    if h is None:
        return 99, SENZA_ORA
    if modo == MODI_DIST[1]:
        for i, (nome, a, b) in enumerate(FASCE):
            if a <= h < b:
                return i, nome
    return h, f"{h:02d}:00–{h:02d}:59"

def _raggruppa_dist(movs, modo):
    gruppi = {}
    if modo == MODI_DIST[0]:
        gruppi = {(i, g): {"n": 0, "u": 0.0, "e": 0.0} for i, g in enumerate(GIORNI)}
    elif modo == MODI_DIST[1]:
        gruppi = {(i, f[0]): {"n": 0, "u": 0.0, "e": 0.0} for i, f in enumerate(FASCE)}
    for d, v in movs:
        r = gruppi.setdefault(_chiave_dist(modo, d, v), {"n": 0, "u": 0.0, "e": 0.0})
        r["n"] += 1
        tipo, imp = str(campo(v, "tipo", "")).strip().lower(), abs(campo(v, "importo", 0.0))
        if tipo == "uscita":
            r["u"] += imp
        elif tipo == "entrata":
            r["e"] += imp
    return gruppi

def _tab_distribuzione(self, tab, categoria, vai, conto_var, bt):
    today = datetime.date.today()
    modo_var = tk.StringVar(value=MODI_DIST[0])
    mese_var = tk.StringVar(value="Tutti")
    anno_var = tk.StringVar(value=str(today.year))
    cat_var = tk.StringVar(value=categoria if isinstance(categoria, str) and categoria in self.categorie else TUTTE)
    futuri = _futuri_condiviso(self, tab)

    top = ttk.Frame(tab)
    top.pack(fill=tk.X, padx=6, pady=(8, 4))
    ttk.Label(top, text="Raggruppa per:").pack(side=tk.LEFT, padx=(0, 5))
    ttk.Combobox(top, values=MODI_DIST, textvariable=modo_var, style="Border.TCombobox",
                 state="readonly", width=21).pack(side=tk.LEFT)
    ttk.Label(top, text="Mese:").pack(side=tk.LEFT, padx=(14, 5))
    ttk.Combobox(top, values=["Tutti"] + MESI, textvariable=mese_var, style="Border.TCombobox",
                 state="readonly", width=12).pack(side=tk.LEFT)
    ttk.Label(top, text="Anno:").pack(side=tk.LEFT, padx=(10, 5))
    ttk.Combobox(top, values=["Tutti"] + [str(a) for a in _anni_disponibili(self)], textvariable=anno_var,
                 style="Border.TCombobox", state="readonly", width=8).pack(side=tk.LEFT)
    ttk.Label(top, text="Categoria:").pack(side=tk.LEFT, padx=(14, 5))
    _combo_cat(self, top, cat_var, [TUTTE] + sorted(self.categorie, key=lambda c: c.lower()), 25).pack(side=tk.LEFT)
    ttk.Checkbutton(top, text="Includi movimenti futuri", variable=futuri).pack(side=tk.LEFT, padx=(20, 0))
    _combo_conto(self, top, conto_var)

    barra = tk.Frame(tab, bg=self.COLOR_TOPLEVEL)
    barra.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=8)
    pw, tree, graf = _pannello_corpo(self, tab, COLS_DIST, affiancato=True, orizzontale=False, peso_testo=50)
    inf, lbl_info, _lbl_hint = _riga_info(
        self, tab, "Doppio clic → Movimenti del gruppo  |  Doppio clic sulle barre → Dettaglio della categoria")
    inf.pack(fill=tk.X, padx=8, pady=(2, 0))
    pw.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
    stato = {"intest": [], "footer": [], "extra": []}

    def aggiorna(*_):
        modo, cat, mese, oggi = modo_var.get(), cat_var.get(), mese_var.get(), datetime.date.today()
        try:
            anno = None if anno_var.get() == "Tutti" else int(anno_var.get())
        except Exception:
            return
        mese_n = None if mese == "Tutti" else MESI.index(mese) + 1
        movs = [(d, v) for d, v in _movimenti(self, conto_var.get())
                if (anno is None or d.year == anno) and (mese_n is None or d.month == mese_n)
                and (futuri.get() or d <= oggi)
                and (cat == TUTTE or campo(v, "categoria", "") == cat)]
        gruppi = _raggruppa_dist(movs, modo)
        if modo == MODI_DIST[2]:
            gruppi = {k: r for k, r in gruppi.items() if r["n"]}
        chiavi = sorted(gruppi)
        tot_u = sum(r["u"] for r in gruppi.values())
        tot_e = sum(r["e"] for r in gruppi.values())
        tot_n = sum(r["n"] for r in gruppi.values())
        quando = f"{mese} {'tutti gli anni' if anno is None else anno}"
        nome_cat = "tutte le categorie" if cat == TUTTE else cat
        titolo = f"Distribuzione per {modo.lower()} – {nome_cat} – {quando}{_suff_conto(conto_var.get())}"
        _svuota(tree)
        for k in chiavi:
            r = gruppi[k]
            _inserisci(tree, (k[1], r["n"], _fmt_it(r["u"]), _fmt_it(r["e"]),
                              _fmt_it(r["e"] - r["u"], "+,.2f") if r["n"] else "—",
                              _fmt_it((r["u"] + r["e"]) / r["n"]) if r["n"] else "—",
                              _fmt_pct(r["u"] / tot_u * 100) if tot_u > 0 and r["u"] > 0 else "—"),
                       _tag_saldo(r["e"], r["u"]) if r["n"] else None, extra=k if r["n"] else None)
        stato["intest"] = [titolo, f"Movimenti: {tot_n}"]
        stato["footer"] = [["Totale", tot_n, _fmt_it(tot_u), _fmt_it(tot_e), _fmt_it(tot_e - tot_u, "+,.2f"),
                            _fmt_it((tot_u + tot_e) / tot_n) if tot_n else "—", "100,0%" if tot_u > 0 else "—"]] if tot_n else []
        stato["extra"] = []
        info = titolo
        if tot_u > 0:
            candidati = [k for k in chiavi if k[1] != SENZA_ORA] or chiavi
            top_k = max(candidati, key=lambda k: gruppi[k]["u"])
            r1 = f"Più uscite: {top_k[1]} ({_fmt_it(gruppi[top_k]['u'])} €, {_fmt_pct(gruppi[top_k]['u'] / tot_u * 100)})"
            stato["extra"] = ["", r1]
            info += f"  ·  {r1}"
        n_senza = gruppi.get((99, SENZA_ORA), {}).get("n", 0)
        if modo != MODI_DIST[0] and n_senza:
            r2 = f"{n_senza} moviment{'o' if n_senza == 1 else 'i'} senza orario"
            stato["extra"].append(r2)
            info += f"  ·  {r2}"
        lbl_info.config(text=info if tot_n else f"{titolo}  ·  Nessun movimento")
        bt.imposta(4, tot_e, tot_u) if tot_n else bt.imposta(4, None, None)
        modo_g = "Totale" if anno is None else ("Mese" if mese_n else "Anno")
        graf.imposta(titolo, [(k[1], [gruppi[k]["e"], gruppi[k]["u"]]) for k in chiavi],
                     [("Entrate", "green"), ("Uscite", "red")],
                     chiavi=[k if gruppi[k]["n"] else None for k in chiavi],
                     azione=lambda k, _e, c=cat, mo=modo_g, a=anno, m=mese_n: vai(c, mo, a, m),
                     dettagli=[f"Movimenti: {gruppi[k]['n']}\nSaldo: {_fmt_it(gruppi[k]['e'] - gruppi[k]['u'], '+,.2f')} €"
                               for k in chiavi],
                     suggerimento="Doppio click: apri nel Dettaglio")

    def apri_gruppo(k):
        modo, cat, mese, oggi = modo_var.get(), cat_var.get(), mese_var.get(), datetime.date.today()
        try:
            anno = None if anno_var.get() == "Tutti" else int(anno_var.get())
        except Exception:
            return
        mese_n = None if mese == "Tutti" else MESI.index(mese) + 1
        sel = lambda d, v: ((anno is None or d.year == anno) and (mese_n is None or d.month == mese_n)
                            and (futuri.get() or d <= oggi) and (cat == TUTTE or campo(v, "categoria", "") == cat)
                            and _chiave_dist(modo, d, v) == k)
        _apri_transazioni(self, tab.winfo_toplevel(), [] if cat == TUTTE else [cat], anno, mese_n, conto_var.get(),
                          f"{k[1]} – {'Tutte le categorie' if cat == TUTTE else cat} – {mese} "
                          f"{'tutti gli anni' if anno is None else anno}{_suff_conto(conto_var.get())}",
                          sel, forza_chiavi=True)

    def doppio_click(event):
        iid = tree.identify_row(event.y)
        if iid and iid in tree._exp and tree._extra.get(iid):
            apri_gruppo(tree._extra[iid])

    tree.bind("<Double-1>", doppio_click)

    def reset():
        modo_var.set(MODI_DIST[0])
        mese_var.set("Tutti")
        anno_var.set(str(today.year))
        cat_var.set(TUTTE)
        conto_var.set(HOUSEHOLD_LABEL)

    _btn(self, barra, "salva", "Esporta", lambda: _esporta(self, tree, "Analisi_Categorie_Distribuzione", EXP_DIST, stato))
    _btn(self, barra, "reset", "Reset campi", reset)
    bt.registra_reset(4, reset)
    for v in (modo_var, mese_var, anno_var, cat_var, futuri, conto_var):
        v.trace_add("write", aggiorna)
    aggiorna()

    def imposta_categoria(c):
        if isinstance(c, str) and c in self.categorie:
            cat_var.set(c)
    return imposta_categoria

COLS_BUDGET = [("Categoria", "Categoria", 160, "w", True), ("Periodo", "Periodo", 130, "w", False),
             ("Budget", "Budget (€)", 95, "e", False), ("Speso", "Speso (€)", 95, "e", False),
             ("Eccesso", "Superamento (€)", 105, "e", False), ("PercBud", "% budget", 80, "e", False),
             ("Num", "Num", 50, "e", False), ("Data", "Superato il", 95, "center", False)]
EXP_BUDGET = [("Categoria", "l", 22), ("Periodo", "l", 15), ("Budget (€)", "r", 11), ("Speso (€)", "r", 11),
            ("Superamento (€)", "r", 14), ("% bud.", "r", 8), ("Num", "r", 4), ("Superato il", "c", 11)]

def _calcola_budget_superato(movs, bud_m, bud_a, anno, mese_n, oggi, futuri=True):
    def filtro(d):
        if not futuri and d > oggi:
            return False
        return (anno is None or d.year == anno) and (mese_n is None or d.month == mese_n)

    mesi, anni = {}, {}
    for d, v in movs:
        if not filtro(d) or campo(v, "tipo", "") != "Uscita":
            continue
        cat = campo(v, "categoria", "").strip().title()
        if cat in bud_m:
            mesi.setdefault((cat, d.year, d.month), []).append((d, v))
        if cat in bud_a and mese_n is None:
            anni.setdefault((cat, d.year), []).append((d, v))

    def riga(cat, y, m, lista, bud):
        speso = sum(float(campo(v, "importo", 0.0)) for _, v in lista)
        if speso <= bud:
            return None
        cum, quando = 0.0, None
        for d, v in sorted(lista, key=lambda x: (x[0], str(campo(x[1], "ora", "") or ""))):
            cum += float(campo(v, "importo", 0.0))
            if cum > bud:
                quando = d
                break
        return {"cat": cat, "anno": y, "mese": m, "bud": bud, "speso": speso, "eccesso": speso - bud,
                "perc": speso / bud * 100, "num": len(lista), "quando": quando}

    righe = []
    for (cat, y, m), lista in mesi.items():
        r = riga(cat, y, m, lista, bud_m[cat])
        if r:
            righe.append(r)
    for (cat, y), lista in anni.items():
        r = riga(cat, y, None, lista, bud_a[cat])
        if r:
            righe.append(r)
    righe.sort(key=lambda r: (-r["eccesso"], r["cat"]))
    return righe, len(set(bud_m) | set(bud_a))

def _tab_budget_superato(self, tab, vai, conto_var, bt):
    today = datetime.date.today()
    mese_var = tk.StringVar(value="Tutti")
    anno_var = tk.StringVar(value=str(today.year))
    futuri = _futuri_condiviso(self, tab)

    top = ttk.Frame(tab)
    top.pack(fill=tk.X, padx=6, pady=(8, 4))
    ttk.Label(top, text="Mese:").pack(side=tk.LEFT, padx=(0, 5))
    ttk.Combobox(top, values=["Tutti"] + MESI, textvariable=mese_var, style="Border.TCombobox",
                 state="readonly", width=12).pack(side=tk.LEFT)
    ttk.Label(top, text="Anno:").pack(side=tk.LEFT, padx=(10, 5))
    ttk.Combobox(top, values=["Tutti"] + [str(a) for a in _anni_disponibili(self)], textvariable=anno_var,
                 style="Border.TCombobox", state="readonly", width=8).pack(side=tk.LEFT)
    ttk.Checkbutton(top, text="Includi movimenti futuri nei totali", variable=futuri).pack(side=tk.LEFT, padx=(20, 0))
    _combo_conto(self, top, conto_var)

    barra = tk.Frame(tab, bg=self.COLOR_TOPLEVEL)
    barra.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=8)

    mod = ttk.Frame(tab)
    mod.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=(4, 0))
    cat_var, bm_var, ba_var = tk.StringVar(), tk.StringVar(), tk.StringVar()
    ttk.Label(mod, text="Modifica budget  ·  Categoria:").pack(side=tk.LEFT, padx=(0, 5))
    cb_cat = ttk.Combobox(mod, textvariable=cat_var, style="Border.TCombobox", state="readonly", width=22,
                          values=sorted(self.categorie),
                          postcommand=lambda: cb_cat.configure(values=sorted(self.categorie)))
    cb_cat.pack(side=tk.LEFT)
    ttk.Label(mod, text="Budget mensile (€):").pack(side=tk.LEFT, padx=(12, 5))
    ttk.Entry(mod, textvariable=bm_var, width=10, justify="right").pack(side=tk.LEFT)
    ttk.Label(mod, text="Budget annuale (€):").pack(side=tk.LEFT, padx=(12, 5))
    ttk.Entry(mod, textvariable=ba_var, width=10, justify="right").pack(side=tk.LEFT)
    _btn(self, mod, "salva", "Salva budget", lambda: salva_budget())
    _btn(self, mod, "report", "Suggerisci", lambda: suggerisci())
    _btn(self, mod, "filtri", "Suggerisci tutti", lambda: suggerisci_tutti())

    pw, tree, graf = _pannello_corpo(self, tab, COLS_BUDGET, affiancato=False)
    inf, lbl_info, _lbl_hint = _riga_info(
        self, tab, "Doppio clic → Movimenti del periodo  |  Doppio clic sulle barre → Dettaglio della categoria")
    inf.pack(fill=tk.X, padx=8, pady=(2, 0))
    pw.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
    stato = {"intest": [], "footer": [], "extra": [], "anno": None, "mese": None, "etich": ""}

    def aggiorna(*_):
        anno = None
        if anno_var.get() != "Tutti":
            try:
                anno = int(anno_var.get())
            except Exception:
                return
        mese = mese_var.get()
        mese_n = None if mese == "Tutti" else MESI.index(mese) + 1
        conto = conto_var.get()
        bud_m = _budget_dict(getattr(self, "budget_categorie", {}))
        bud_a = _budget_dict(getattr(self, "budget_annuale_categorie", {}))
        righe, n_bud = _calcola_budget_superato(_movimenti(self, conto), bud_m, bud_a, anno, mese_n,
                                        datetime.date.today(), futuri.get())
        etich = "Tutti gli anni" if anno is None else str(anno)
        titolo = f"Budget superato – {mese} {etich}{_suff_conto(conto)}"
        stato.update(anno=anno, mese=mese_n, etich=f"{mese} {etich}", intest=[titolo])
        stato["extra"] = ["Una riga per ogni mese oltre il budget mensile (e per ogni anno oltre il budget annuale)",
                          "Superato il: giorno in cui la spesa cumulata ha oltrepassato il budget del periodo"]
        _svuota(tree)
        tb = ts = 0.0
        tn = 0
        per_cat = {}
        for r in righe:
            periodo = f"{MESI[r['mese'] - 1]} {r['anno']}" if r["mese"] else f"Anno {r['anno']}"
            _inserisci(tree, (r["cat"], periodo, _fmt_it(r["bud"]), _fmt_it(r["speso"]),
                              _fmt_it(r["eccesso"], "+,.2f"), _fmt_pct(r["perc"]), r["num"],
                              r["quando"].strftime("%d-%m-%Y") if r["quando"] else "—"),
                       "budget_superato", extra=(r["cat"], r["anno"], r["mese"]))
            tb += r["bud"]
            ts += r["speso"]
            tn += r["num"]
            a = per_cat.setdefault(r["cat"], {"eccesso": 0.0, "n": 0})
            a["eccesso"] += r["eccesso"]
            a["n"] += 1
        stato["footer"] = ([["Totale", f"{len(righe)} superamenti", _fmt_it(tb), _fmt_it(ts),
                             _fmt_it(ts - tb, "+,.2f"), _fmt_pct(ts / tb * 100), tn, ""]] if righe else [])
        if not (bud_m or bud_a):
            lbl_info.config(text="Nessun budget impostato: imposta i budget delle categorie per vedere i budget superati")
        elif righe:
            lbl_info.config(text=f"{titolo}  ·  {len(righe)} superament{'o' if len(righe) == 1 else 'i'} in "
                                 f"{len(per_cat)} categori{'a' if len(per_cat) == 1 else 'e'}"
                                 f"  ·  Superamento totale: {_fmt_it(ts - tb)} €")
        else:
            lbl_info.config(text=f"{titolo}  ·  Nessun budget superato ({n_bud} categorie con budget)")
        bt.imposta(5, None, None)
        if anno is None:
            modo, a_n, m_n = "Totale", None, None
        elif mese_n:
            modo, a_n, m_n = "Mese", anno, mese_n
        else:
            modo, a_n, m_n = "Anno", anno, None
        ordine = sorted(per_cat.items(), key=lambda x: -x[1]["eccesso"])
        graf.imposta(f"Superamento totale per categoria – {mese} {etich}{_suff_conto(conto)}",
                     [(c, [a["eccesso"]]) for c, a in ordine],
                     [("Superamento (€)", "orange")],
                     chiavi=[c for c, _ in ordine],
                     azione=lambda k, _e, mo=modo, a=a_n, m=m_n: vai(k, mo, a, m),
                     dettagli=[f"Superamenti: {a['n']}\nSuperamento totale: {_fmt_it(a['eccesso'])} €" for _, a in ordine],
                     suggerimento="Doppio click: apri nel Dettaglio")

    def doppio_click(event):
        iid = tree.identify_row(event.y)
        if not iid or iid not in tree._exp or not tree._extra.get(iid):
            return
        cat, anno, mese = tree._extra[iid]
        oggi = datetime.date.today()
        sel = lambda d, v: (d.year == anno and (mese is None or d.month == mese)
                            and (futuri.get() or d <= oggi) and _stessa_cat(campo(v, "categoria", ""), cat)
                            and campo(v, "tipo", "") == "Uscita")
        periodo = f"{MESI[mese - 1]} {anno}" if mese else str(anno)
        _apri_transazioni(self, tab.winfo_toplevel(), [cat], anno, mese, conto_var.get(),
                          f"{cat} – {periodo}{_suff_conto(conto_var.get())}", sel)

    tree.bind("<Double-1>", doppio_click)

    def carica_budget(*_):
        cat = cat_var.get()
        bm = _budget_dict(getattr(self, "budget_categorie", {})).get(cat, 0.0)
        ba = _budget_dict(getattr(self, "budget_annuale_categorie", {})).get(cat, 0.0)
        bm_var.set(f"{bm:.2f}".replace(".", ",") if bm else "")
        ba_var.set(f"{ba:.2f}".replace(".", ",") if ba else "")

    def da_selezione(_e=None):
        sel = tree.selection()
        if sel and sel[0] in tree._exp:
            cat_var.set(tree._exp[sel[0]][0])

    def salva_budget():
        cat = cat_var.get().strip()
        if not cat:
            return
        try:
            m = float(bm_var.get().strip().replace(",", ".") or 0)
            a = float(ba_var.get().strip().replace(",", ".") or 0)
        except ValueError:
            if hasattr(self, "show_toast"):
                self.show_toast("Budget non valido: usa solo numeri (es. 450,00).")
            return
        if m > 0:
            self.budget_categorie[cat] = m
        else:
            self.budget_categorie.pop(cat, None)
        if a > 0:
            self.budget_annuale_categorie[cat] = a
        else:
            self.budget_annuale_categorie.pop(cat, None)
        self.save_db()
        try:
            self.refresh_gui()
        except Exception:
            pass
        if hasattr(self, "show_toast"):
            self.show_toast(f"Budget di '{cat}' aggiornato – Mese: € {_fmt_it(m)} · Anno: € {_fmt_it(a)}")
        conto_var.set(conto_var.get())
        carica_budget()

    def suggerisci():
        cat = cat_var.get().strip()
        if not cat:
            self.show_toast("Seleziona prima una categoria.")
            return
        movs = _movimenti(self, filtrati=False)
        n = _mesi_storico(movs)
        s = suggerisci_budget(movs, cat, n)
        if not s:
            self.show_toast(f"Storico insufficiente per '{cat}': servono almeno {SUGG_MIN_MESI} mesi con spese.")
            return
        bm_var.set(_fmt_campo(s[0]))
        ba_var.set(_fmt_campo(s[1]))
        self.show_toast(f"Suggerito per '{cat}': mediana su {s[2]} mesi con spese (ultimi {n} mesi chiusi). "
                        "Premi «Salva budget» per confermare.")

    def applica_suggeriti(scelte, con_annuale):
        for cat, m, a in scelte:
            self.budget_categorie[cat] = m
            if con_annuale:
                self.budget_annuale_categorie[cat] = a
        self.save_db()
        try:
            self.refresh_gui()
        except Exception:
            pass
        self.show_toast(f"Budget aggiornati per {len(scelte)} categori{'a' if len(scelte) == 1 else 'e'}.")
        conto_var.set(conto_var.get())
        carica_budget()

    def suggerisci_tutti():
        movs = _movimenti(self, filtrati=False)
        n = _mesi_storico(movs)
        bm = _budget_dict(getattr(self, "budget_categorie", {}))
        ba = _budget_dict(getattr(self, "budget_annuale_categorie", {}))
        righe = []
        for cat in sorted(self.categorie, key=str.lower):
            s = suggerisci_budget(movs, cat, n)
            if s:
                k = cat.strip().title()
                righe.append((cat, bm.get(k, 0.0), s[0], ba.get(k, 0.0), s[1]))
        if not righe:
            self.show_toast(f"Storico insufficiente: servono almeno {SUGG_MIN_MESI} mesi chiusi con spese.")
            return
        _popup_suggerisci_tutti(self, tab, righe, n, applica_suggeriti)

    cat_var.trace_add("write", carica_budget)
    tree.bind("<<TreeviewSelect>>", da_selezione)

    def reset():
        mese_var.set("Tutti")
        anno_var.set(str(today.year))
        conto_var.set(HOUSEHOLD_LABEL)

    _btn(self, barra, "salva", "Esporta", lambda: _esporta(self, tree, "Analisi_Budget_Superato", EXP_BUDGET, stato))
    _btn(self, barra, "reset", "Reset campi", reset)
    bt.registra_reset(5, reset)
    for v in (mese_var, anno_var, futuri, conto_var):
        v.trace_add("write", aggiorna)
    aggiorna()

COLS_TARGET = [("Mese", "Mese", 110, "w", True), ("Num", "Num", 50, "e", False),
               ("Uscite", "Uscite (€)", 105, "e", False), ("Target", "Target (€)", 105, "e", False),
               ("Perc", "% target", 80, "e", False), ("Residuo", "Residuo (€)", 105, "e", False)]
EXP_TARGET = [("Mese", "l", 22), ("Num", "r", 5), ("Uscite (€)", "r", 14), ("Target (€)", "r", 14),
              ("% target", "r", 9), ("Residuo (€)", "r", 14)]

def _target_correnti():
    cfg = getattr(_app, "app_config_globale", None) or {}
    out = []
    for k in ("target_mese", "target_anno"):
        try:
            out.append(max(float(cfg.get(k, 0) or 0), 0.0))
        except (TypeError, ValueError):
            out.append(0.0)
    return out[0], out[1]

def _tag_target(perc):
    if perc is None:
        return None
    if perc < 80:
        return "entrata"
    if perc <= 100:
        return "budget_superato"
    return "uscita"

def _colore_target(perc):
    return "green" if perc < 80 else ("orange" if perc <= 100 else "red")

def _tab_target(self, tab, vai, conto_var, bt):
    today = datetime.date.today()
    anno_var = tk.StringVar(value=str(today.year))
    futuri = _futuri_condiviso(self, tab)
    tm_var, ta_var = tk.StringVar(), tk.StringVar()

    top = ttk.Frame(tab)
    top.pack(fill=tk.X, padx=6, pady=(8, 4))
    ttk.Label(top, text="Anno:").pack(side=tk.LEFT, padx=(0, 5))
    ttk.Combobox(top, values=[str(a) for a in _anni_disponibili(self)], textvariable=anno_var,
                 style="Border.TCombobox", state="readonly", width=8).pack(side=tk.LEFT)
    ttk.Checkbutton(top, text="Includi movimenti futuri nei totali", variable=futuri).pack(side=tk.LEFT, padx=(20, 0))
    _combo_conto(self, top, conto_var)

    barra = tk.Frame(tab, bg=self.COLOR_TOPLEVEL)
    barra.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=8)

    mod = ttk.Frame(tab)
    mod.pack(side=tk.BOTTOM, fill=tk.X, padx=8, pady=(4, 0))
    ttk.Label(mod, text="Modifica target  ·  Target mese (€):").pack(side=tk.LEFT, padx=(0, 5))
    ttk.Entry(mod, textvariable=tm_var, width=10, justify="right").pack(side=tk.LEFT)
    ttk.Label(mod, text="Target anno (€):").pack(side=tk.LEFT, padx=(12, 5))
    ttk.Entry(mod, textvariable=ta_var, width=10, justify="right").pack(side=tk.LEFT)
    _btn(self, mod, "salva", "Salva target", lambda: salva_target())
    _btn(self, mod, "report", "Suggerisci target", lambda: suggerisci_target())

    pw, tree, graf = _pannello_corpo(self, tab, COLS_TARGET, affiancato=True, orizzontale=False, peso_testo=50)
    inf, lbl_info, _lbl_hint = _riga_info(
        self, tab, "Doppio clic → Movimenti del mese  |  Doppio clic sulle barre → Dettaglio del mese")
    inf.pack(fill=tk.X, padx=8, pady=(2, 0))
    fr_coer = ttk.Frame(tab)
    fr_coer.pack(fill=tk.X, padx=8, pady=(0, 0))
    pw.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
    stato = {"intest": [], "footer": [], "extra": []}

    def carica_target():
        tm, ta = _target_correnti()
        tm_var.set(f"{tm:.2f}".replace(".", ",") if tm else "")
        ta_var.set(f"{ta:.2f}".replace(".", ",") if ta else "")

    def aggiorna(*_):
        try:
            anno = int(anno_var.get())
        except Exception:
            return
        oggi = datetime.date.today()
        conto = conto_var.get()
        tm, ta = _target_correnti()
        mesi = {m: {"n": 0, "u": 0.0, "e": 0.0} for m in range(1, 13)}
        for d, v in _movimenti(self, conto):
            if d.year != anno or (not futuri.get() and d > oggi):
                continue
            r = mesi[d.month]
            r["n"] += 1
            tipo, imp = campo(v, "tipo", ""), float(campo(v, "importo", 0.0))
            if tipo == "Uscita":
                r["u"] += imp
            elif tipo == "Entrata":
                r["e"] += imp
        sc = _suff_conto(conto)
        _svuota(tree)
        tn = tu = te = 0.0
        percs = {}
        for m in range(1, 13):
            r = mesi[m]
            perc = (r["u"] / tm * 100) if tm > 0 else None
            percs[m] = perc
            if datetime.date(anno, m, 1) > oggi:
                tag = "futuro"
            else:
                tag = _tag_target(perc) if r["n"] else None
            _inserisci(tree, (MESI[m - 1], r["n"], _fmt_it(r["u"]), _fmt_it(tm) if tm > 0 else "N/D",
                              _fmt_pct(perc) if perc is not None else "",
                              _fmt_it(tm - r["u"], "+,.2f") if tm > 0 else ""),
                       tag, extra=m if r["n"] else None)
            tn += r["n"]
            tu += r["u"]
            te += r["e"]

        if anno == oggi.year:
            chiusi = [mesi[m]["u"] for m in range(1, oggi.month)]
            media = (sum(chiusi) / len(chiusi)) if chiusi else None
            if media is None:
                proiez = None
            else:
                proiez = sum(chiusi) + sum(max(mesi[m]["u"], media) for m in range(oggi.month, 13))
        else:
            media, proiez = None, tu
        perc_a = (tu / ta * 100) if ta > 0 else None
        mesi_sopra = [m for m in range(1, 13) if tm > 0 and mesi[m]["u"] > tm]

        righe_footer = [[f"Totale {anno}", int(tn), _fmt_it(tu), _fmt_it(ta) if ta > 0 else "N/D",
                         _fmt_pct(perc_a) if perc_a is not None else "",
                         _fmt_it(ta - tu, "+,.2f") if ta > 0 else ""]]
        extra = []
        if proiez is not None and anno == oggi.year:
            righe_footer.append(["Proiezione fine anno", "", _fmt_it(proiez), _fmt_it(ta) if ta > 0 else "N/D",
                                 _fmt_pct(proiez / ta * 100) if ta > 0 else "",
                                 _fmt_it(ta - proiez, "+,.2f") if ta > 0 else ""])
            extra += ["Proiezione:",
                      "mesi chiusi + per ogni mese restante il maggiore tra il registrato e la",
                      f"media dei mesi chiusi ({_fmt_it(media)} €)"]
        if tm <= 0 and ta <= 0:
            extra.append("Target non impostati")
        stato["intest"] = [f"Target di spesa – {anno}{sc}"]
        stato["footer"] = righe_footer
        stato["extra"] = extra

        info = f"Target di spesa – {anno}{sc}"
        if tm > 0:
            info += f"  ·  Mesi oltre target: {len(mesi_sopra)}"
        if ta > 0:
            info += f"  ·  Anno: {_fmt_it(tu)} / {_fmt_it(ta)} € ({_fmt_pct(perc_a)})"
        if proiez is not None and anno == oggi.year:
            info += f"  ·  Proiezione fine anno: {_fmt_it(proiez)} €"
            if ta > 0:
                info += " (oltre il target)" if proiez > ta else " (nel target)"
        if tm <= 0 and ta <= 0:
            info += "  ·  Imposta Target mese / Target anno qui sotto"
        lbl_info.config(text=info)

        bud_m = _budget_dict(getattr(self, "budget_categorie", {}))
        bud_a = _budget_dict(getattr(self, "budget_annuale_categorie", {}))
        sm, sa = sum(bud_m.values()), sum(bud_a.values())
        msg = []
        if tm > 0 and bud_m:
            msg.append((f"Budget mensili categorie: {_fmt_it(sm)} € {'>' if sm > tm else '≤'} Target mese {_fmt_it(tm)} €"
                        + ("  (incoerente)" if sm > tm else ""), sm <= tm))
        if ta > 0 and bud_a:
            msg.append((f"Budget annuali categorie: {_fmt_it(sa)} € {'>' if sa > ta else '≤'} Target anno {_fmt_it(ta)} €"
                        + ("  (incoerente)" if sa > ta else ""), sa <= ta))
        if tm > 0 and ta > 0:
            msg.append((f"Target mese × 12 = {_fmt_it(tm * 12)} € {'>' if tm * 12 > ta else '≤'} Target anno {_fmt_it(ta)} €"
                        + ("  (incoerente)" if tm * 12 > ta else ""), tm * 12 <= ta))
        for w in fr_coer.winfo_children():
            w.destroy()
        for k, (testo, ok) in enumerate(msg):
            ttk.Label(fr_coer, text=testo, font=("Arial", 9, "bold"),
                      foreground=getattr(self, "COLOR_GREEN_SMOOTH", "#28A745") if ok
                      else getattr(self, "COLOR_RED_SMOOTH", "#DC3545")).pack(side=tk.LEFT, padx=(0 if k == 0 else 24, 0))

        bt.imposta(6, te, tu)
        evid = {}
        if tm > 0:
            for i, m in enumerate(range(1, 13)):
                if mesi[m]["n"] and percs[m] is not None:
                    evid[(i, 0)] = _colore_target(percs[m])
        serie = [("Uscite", "accent")] + ([("Target", "orange")] if tm > 0 else [])
        graf.imposta(f"Uscite contro Target mese – {anno}{sc}",
                     [(MESI[m - 1][:3], [mesi[m]["u"]] + ([tm] if tm > 0 else [])) for m in range(1, 13)],
                     serie,
                     chiavi=[m if mesi[m]["n"] else None for m in range(1, 13)],
                     azione=lambda m, _e, a=anno: vai(TUTTE, "Mese", a, m),
                     dettagli=[(f"{MESI[m - 1]}\nUscite: {_fmt_it(mesi[m]['u'])} €"
                                + (f"\nTarget: {_fmt_it(tm)} € ({_fmt_pct(percs[m])})" if tm > 0 else ""))
                               if mesi[m]["n"] else f"{MESI[m - 1]}\nNessun movimento" for m in range(1, 13)],
                     evidenza=evid,
                     suggerimento="Doppio click: movimenti del mese nel Dettaglio")

    def doppio_click(event):
        iid = tree.identify_row(event.y)
        if not iid or iid not in tree._exp:
            return
        m = tree._extra.get(iid)
        if not m:
            return
        try:
            anno = int(anno_var.get())
        except Exception:
            return
        oggi = datetime.date.today()
        sel = lambda d, v: d.year == anno and d.month == m and (futuri.get() or d <= oggi)
        _apri_transazioni(self, tab.winfo_toplevel(), [], anno, m, conto_var.get(),
                          f"Tutte le categorie – {MESI[m - 1]} {anno}{_suff_conto(conto_var.get())}", sel)

    tree.bind("<Double-1>", doppio_click)

    def suggerisci_target():
        movs = _movimenti(self, filtrati=False)
        n = _mesi_storico(movs)
        opzioni = suggerimenti_target(self, movs, n)
        if not opzioni:
            self.show_toast(f"Storico insufficiente: servono almeno {SUGG_MIN_MESI} mesi chiusi con spese "
                            "(oppure imposta prima dei budget per categoria).")
            return
        _popup_suggerisci_target(self, tab, opzioni, tm_var, ta_var)

    def salva_target():
        try:
            m = float(tm_var.get().strip().replace(",", ".") or 0)
            a = float(ta_var.get().strip().replace(",", ".") or 0)
        except ValueError:
            if hasattr(self, "show_toast"):
                self.show_toast("Target non valido: usa solo numeri (es. 1800,00).")
            return
        if m < 0 or a < 0:
            if hasattr(self, "show_toast"):
                self.show_toast("I Target di spesa non possono essere negativi.")
            return
        _app._salva_chiave_config("target_mese", m)
        _app._salva_chiave_config("target_anno", a)
        _app.TARGET_MESE, _app.TARGET_ANNO = m, a
        self.budget_mensile, self.budget_annuale = m, a
        try:
            self.lbl_budget_mese_widget.config(text=f"Target Mese: € {_fmt_it(m)}" if m > 0 else "Target Mese: N/D")
            self.lbl_budget_anno_widget.config(text=f"Target Anno: € {_fmt_it(a)}" if a > 0 else "Target Anno: N/D")
        except Exception:
            pass
        try:
            self.aggiorna_monitoraggio_budget()
        except Exception:
            pass
        try:
            self.refresh_gui()
        except Exception:
            pass
        if hasattr(self, "show_toast"):
            self.show_toast(f"Target aggiornati – Mese: € {_fmt_it(m)} · Anno: € {_fmt_it(a)}")
        conto_var.set(conto_var.get())
        carica_target()

    def reset():
        anno_var.set(str(today.year))
        conto_var.set(HOUSEHOLD_LABEL)
        carica_target()

    _btn(self, barra, "salva", "Esporta", lambda: _esporta(self, tree, "Analisi_Target", EXP_TARGET, stato))
    _btn(self, barra, "reset", "Reset campi", reset)
    bt.registra_reset(6, reset)
    for v in (anno_var, futuri, conto_var):
        v.trace_add("write", aggiorna)
    carica_target()
    aggiorna()

QUOTE_503020 = (("Bisogni", 50), ("Desideri", 30), ("Risparmio", 20))
CLASSI_503020 = ("Bisogni", "Desideri", "Risparmio")
SERIE_503020 = (("Bisogni", "accent"), ("Desideri", "orange"), ("Risparmio", "green"))
COLS_503020 = [("Mese", "Periodo", 100, "w", True), ("Entrate", "Entrate (€)", 90, "e", False),
               ("Bis", "Bisogni (€)", 90, "e", False), ("BisP", "% Bis.", 55, "e", False),
               ("Des", "Desideri (€)", 90, "e", False), ("DesP", "% Des.", 55, "e", False),
               ("Ris", "Risparmio (€)", 95, "e", False), ("RisP", "% Ris.", 55, "e", False),
               ("NA", "Senza classe (€)", 105, "e", False)]
EXP_503020 = [("Periodo", "l", 22), ("Entrate (€)", "r", 13), ("Bisogni (€)", "r", 13), ("% Bis.", "r", 7),
              ("Desideri (€)", "r", 13), ("% Des.", "r", 7), ("Risparmio (€)", "r", 13), ("% Ris.", "r", 7),
              ("Senza classe (€)", "r", 15)]

def _calcola_503020_periodi(self, movs, classi_cat, anno, futuri, oggi, unico=False):
    netti = {}
    for d, v in movs:
        if (anno is not None and d.year != anno) or (not futuri and d > oggi):
            continue
        k = 0 if unico else (d.month if anno is not None else d.year)
        imp = float(campo(v, "importo", 0.0))
        if str(campo(v, "tipo", "")).strip().capitalize() == "Entrata":
            imp = -imp
        r = netti.setdefault(k, {"n": 0, "cat": {}})
        r["n"] += 1
        cat = campo(v, "categoria", "")
        r["cat"][cat] = r["cat"].get(cat, 0.0) + imp
    out = {}
    for k, r in netti.items():
        entrate, classi, na = 0.0, {c: 0.0 for c in CLASSI_503020}, {}
        for cat, n in r["cat"].items():
            n = round(n, 2)
            classe = classi_cat.get(cat, "")
            if classe in classi:
                classi[classe] += n
            elif n < 0:
                entrate += -n
            elif n > 0:
                na[cat] = n
        out[k] = {"n": r["n"], "entrate": entrate, "classi": classi, "na": na}
    return out

def _esito_503020(r):
    if not r or r["entrate"] <= 0:
        return None, None
    perc, ok = {}, {}
    for nome, quota in QUOTE_503020:
        p = r["classi"][nome] / r["entrate"] * 100
        perc[nome] = p
        ok[nome] = p >= quota if nome == "Risparmio" else p <= quota
    return perc, ok

def _tab_503020(self, tab, vai, conto_var, bt):
    today = datetime.date.today()
    anno_var = tk.StringVar(value=str(today.year))
    classe_var = tk.StringVar(value="Tutte")
    cfg = getattr(_app, "app_config_globale", {}) or {}
    futuri = _futuri_condiviso(self, tab)

    top = ttk.Frame(tab)
    top.pack(fill=tk.X, padx=6, pady=(8, 4))
    ttk.Label(top, text="Anno:").pack(side=tk.LEFT, padx=(0, 5))
    ttk.Combobox(top, values=["Tutti"] + [str(a) for a in _anni_disponibili(self)], textvariable=anno_var,
                 style="Border.TCombobox", state="readonly", width=8).pack(side=tk.LEFT)
    ttk.Label(top, text="Classe:").pack(side=tk.LEFT, padx=(14, 5))
    ttk.Combobox(top, values=["Tutte"] + list(CLASSI_503020), textvariable=classe_var, style="Border.TCombobox",
                 state="readonly", width=11).pack(side=tk.LEFT)
    ttk.Checkbutton(top, text="Includi movimenti futuri nei totali", variable=futuri).pack(side=tk.LEFT, padx=(20, 0))
    _combo_conto(self, top, conto_var)

    barra = tk.Frame(tab, bg=self.COLOR_TOPLEVEL)
    barra.pack(side=tk.BOTTOM, fill=tk.X, padx=6, pady=8)
    pw, tree, graf = _pannello_corpo(self, tab, COLS_503020, affiancato=True, orizzontale=False, peso_testo=58)
    inf, lbl_info, _lbl_hint = _riga_info(
        self, tab, "Doppio clic → Movimenti del periodo  |  Doppio clic sulle barre → Dettaglio del periodo")
    inf.pack(fill=tk.X, padx=8, pady=(2, 0))
    lbl_na = ttk.Label(tab, text="", font=("Arial", 9, "bold"), foreground=getattr(self, "COLOR_RED", "red"))
    lbl_na.pack(fill=tk.X, padx=8)
    pw.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)
    stato = {"intest": [], "footer": [], "extra": []}

    def anno_sel():
        return None if anno_var.get() == "Tutti" else int(anno_var.get())

    def aggiorna(*_):
        try:
            anno = anno_sel()
        except Exception:
            return
        oggi = datetime.date.today()
        conto = conto_var.get()
        classe_f = classe_var.get()
        filtra_c = classe_f in CLASSI_503020
        sigle_c = {"Bisogni": ("Bis", "BisP"), "Desideri": ("Des", "DesP"), "Risparmio": ("Ris", "RisP")}
        tree["displaycolumns"] = (["Mese", "Entrate", *sigle_c[classe_f]] if filtra_c else "#all")
        classi_cat = self._classi_categorie()
        movs = _movimenti(self, conto)
        gruppi = _calcola_503020_periodi(self, movs, classi_cat, anno, futuri.get(), oggi)
        tot = _calcola_503020_periodi(self, movs, classi_cat, anno, futuri.get(), oggi, unico=True).get(0)
        chiavi = list(range(1, 13)) if anno is not None else sorted(gruppi)
        sc = _suff_conto(conto)
        etich = "tutti gli anni" if anno is None else str(anno)
        suff_c = f" – {classe_f}" if filtra_c else ""
        _svuota(tree)

        def celle(nome_periodo, r):
            if not r:
                return (nome_periodo, "0,00", "0,00", "—", "0,00", "—", "0,00", "—", "0,00")
            perc, _ok = _esito_503020(r)
            p = lambda n: _fmt_pct(perc[n]) if perc else "—"
            return (nome_periodo, _fmt_it(r["entrate"]),
                    _fmt_it(r["classi"]["Bisogni"]), p("Bisogni"),
                    _fmt_it(r["classi"]["Desideri"]), p("Desideri"),
                    _fmt_it(r["classi"]["Risparmio"]), p("Risparmio"),
                    _fmt_it(sum(r["na"].values())))

        in_regola = con_entrate = 0
        for k in chiavi:
            r = gruppi.get(k)
            nome_p = MESI[k - 1] if anno is not None else str(k)
            perc, ok = _esito_503020(r)
            if anno is not None and datetime.date(anno, k, 1) > oggi:
                tag = "futuro"
            elif ok is None:
                tag = None
            else:
                rel = [n for n in ok if not filtra_c or n == classe_f]
                fuori = sum(1 for n in rel if not ok[n])
                if len(rel) == 1:
                    tag = "entrata" if fuori == 0 else "uscita"
                else:
                    tag = "entrata" if fuori == 0 else ("budget_superato" if fuori == 1 else "uscita")
            if ok is not None:
                con_entrate += 1
                in_regola += 1 if all(ok[n] for n in ok if not filtra_c or n == classe_f) else 0
            _inserisci(tree, celle(nome_p, r), tag, extra=k if r else None)

        na_tot = tot["na"] if tot else {}
        stato["intest"] = [f"Metodo 50/30/20 – {etich}{sc}{suff_c}"]
        stato["footer"] = [list(celle(f"Totale {etich}" if anno is not None else "Totale", tot))] if tot else []
        stato["extra"] = ["Target: Bisogni ≤ 50% · Desideri ≤ 30% · Risparmio ≥ 20% delle entrate nette",
                          "Importi netti per categoria (uscite − entrate); Risparmio = categorie con classe Risparmio"]
        info = f"Metodo 50/30/20 – {etich}{sc}{suff_c}"
        if tot and tot["entrate"] > 0:
            info += f"  ·  Entrate nette: {_fmt_it(tot['entrate'])} €"
            if con_entrate:
                info += f"  ·  Periodi in regola: {in_regola} su {con_entrate}"
        else:
            info += "  ·  Nessuna entrata nel periodo"
        lbl_info.config(text=info)
        if na_tot:
            top3 = sorted(na_tot.items(), key=lambda x: -x[1])[:3]
            testo = (f"Uscite senza classe: {_fmt_it(sum(na_tot.values()))} €  (" +
                     ", ".join(f"{c} {_fmt_it(v)} €" for c, v in top3) +
                     ")  ·  assegna la classe da Gestione Categorie")
            lbl_na.config(text=testo)
            stato["extra"].append(testo)
        else:
            lbl_na.config(text="")
        bt.imposta(7, None, None)

        righe, dett, evid = [], [], {}
        serie_f = [(n, c) for n, c in SERIE_503020 if not filtra_c or n == classe_f]
        nomi_f = [n for n, _ in serie_f]
        for i, k in enumerate(chiavi):
            r = gruppi.get(k)
            perc, ok = _esito_503020(r)
            righe.append((MESI[k - 1] if anno is not None else str(k),
                          [max(0.0, perc[n]) if perc else 0.0 for n in nomi_f]))
            if perc:
                for j, n in enumerate(nomi_f):
                    if not ok[n]:
                        evid[(i, j)] = "red"
                fuori = [n for n in nomi_f if not ok[n]]
                txt_dett = f"{MESI[k - 1] if anno is not None else k}\nEntrate nette: {_fmt_it(r['entrate'])} €"
                if fuori:
                    txt_dett += "\nFuori target: " + ", ".join(fuori)
                dett.append(txt_dett)
            else:
                dett.append(f"{MESI[k - 1] if anno is not None else k}\nNessuna entrata nel periodo")
        graf.imposta(f"% sulle entrate nette – {etich}{sc}{suff_c}", righe, serie_f,
                     chiavi=[k if gruppi.get(k) else None for k in chiavi],
                     azione=lambda k, _e, a=anno: vai(TUTTE, "Mese", a, k) if a is not None else vai(TUTTE, "Anno", k, None),
                     dettagli=dett, evidenza=evid,
                     suggerimento="Rosso = fuori target  ·  Doppio click: apri nel Dettaglio")

    def doppio_click(event):
        iid = tree.identify_row(event.y)
        if not iid or iid not in tree._exp:
            return
        k = tree._extra.get(iid)
        if not k:
            return
        try:
            anno = anno_sel()
        except Exception:
            return
        a, m = (anno, k) if anno is not None else (k, None)
        classe = classe_var.get()
        cats = [] if classe == "Tutte" else [c for c, v in self._classi_categorie().items() if v == classe]
        if classe != "Tutte" and not cats:
            self.show_toast(f"Nessuna categoria con classe {classe}.")
            return
        oggi = datetime.date.today()
        sel = lambda d, v: (d.year == a and (m is None or d.month == m) and (futuri.get() or d <= oggi)
                            and (not cats or any(_stessa_cat(campo(v, "categoria", ""), c) for c in cats)))
        periodo = f"{MESI[m - 1]} {a}" if m else str(a)
        _apri_transazioni(self, tab.winfo_toplevel(), cats, a, m, conto_var.get(),
                          f"50/30/20 – {'Tutte le categorie' if classe == 'Tutte' else classe} – {periodo}"
                          f"{_suff_conto(conto_var.get())}", sel, forza_chiavi=True)

    tree.bind("<Double-1>", doppio_click)

    def cambia_futuri(*_):
        try:
            _app._salva_chiave_config("includi_futuri_analisi", bool(futuri.get()))
        except Exception as e:
            self.show_toast(f"Errore salvataggio: {e}")
        aggiorna()
        try:
            self.aggiorna_barre_503020()
        except Exception:
            pass

    def reset():
        anno_var.set(str(today.year))
        classe_var.set("Tutte")
        conto_var.set(HOUSEHOLD_LABEL)

    _btn(self, barra, "salva", "Esporta", lambda: _esporta(self, tree, "Analisi_503020", EXP_503020, stato))
    _btn(self, barra, "reset", "Reset campi", reset)
    bt.registra_reset(7, reset)
    for v in (anno_var, conto_var, futuri, classe_var):
        v.trace_add("write", aggiorna)
    futuri.trace_add("write", cambia_futuri)
    aggiorna()

def _barra_filtri(self, popup, main, nb, conto_var):
    noti = {metodo_pagamento_pulito(m) for m in METODI_PAGAMENTO_EMOJI}
    extra = sorted({str(campo(v, "metodo_pagamento", "") or "").strip()
                    for _, v in _movimenti(self, filtrati=False)} - {""} - noti, key=str.lower)
    metodi = list(METODI_PAGAMENTO_EMOJI) + extra
    f = {"tipo": tk.StringVar(value=TUTTI), "metodo": tk.StringVar(value=TUTTI), "orig": tk.StringVar(value=TUTTI),
         "tag": tk.StringVar(value=""), "testo": tk.StringVar(value=""), "da": tk.StringVar(value=""),
         "a": tk.StringVar(value=""), "allegato": tk.BooleanVar(value=False)}
    self._analisi_filtri = f
    bg = self.COLOR_TOPLEVEL
    stato = {"aperta": False, "sosp": False, "job": None}

    head = tk.Frame(main, bg=bg)
    head.pack(fill=tk.X, pady=(0, 2), before=nb)
    lbl_freccia = tk.Label(head, bg=bg, fg="#DC3545", cursor="hand2", font=("Arial", 11, "bold"), width=2)
    lbl_freccia.pack(side=tk.LEFT)
    lbl_head = tk.Label(head, bg=bg, fg=self.TEXT_COLOR, cursor="hand2", font=("Arial", 9, "bold"), anchor="w")
    lbl_head.pack(side=tk.LEFT)
    body = tk.Frame(main, bg=bg)

    def riga():
        r = tk.Frame(body, bg=bg)
        r.pack(fill=tk.X, pady=2)
        return r

    def etichetta(r, testo, pad=(10, 4)):
        tk.Label(r, text=testo, bg=bg, fg=self.TEXT_COLOR).pack(side=tk.LEFT, padx=pad)

    r1, r2 = riga(), riga()
    etichetta(r1, "Tipo:", (4, 4))
    ttk.Combobox(r1, values=TIPI_FILTRO, textvariable=f["tipo"], style="Border.TCombobox",
                 state="readonly", width=9).pack(side=tk.LEFT)
    etichetta(r1, "Metodo di pagamento:")
    ttk.Combobox(r1, values=[TUTTI, NESSUN_METODO] + metodi, textvariable=f["metodo"], style="Border.TCombobox",
                 state="readonly", width=22).pack(side=tk.LEFT)
    etichetta(r1, "Origine:")
    ttk.Combobox(r1, values=ORIG_FILTRO, textvariable=f["orig"], style="Border.TCombobox",
                 state="readonly", width=11).pack(side=tk.LEFT)
    ttk.Checkbutton(r1, text="Solo con allegato (ALL·)", variable=f["allegato"]).pack(side=tk.LEFT, padx=(14, 0))

    etichetta(r2, "Hashtag:", (4, 4))
    ttk.Entry(r2, textvariable=f["tag"], width=22).pack(side=tk.LEFT)
    etichetta(r2, "Descrizione contiene:")
    ttk.Entry(r2, textvariable=f["testo"], width=24).pack(side=tk.LEFT)
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
        b = tk.Label(r2, image=img, bg=bg, cursor="hand2", padx=2)
        if img is None:
            b.config(text="📅")
        else:
            b.image = img
        b.pack(side=tk.LEFT, padx=(2, 0))
        b.bind("<Button-1>", apri)

    etichetta(r2, "Dal:")
    e_da = ttk.Entry(r2, textvariable=f["da"], width=11)
    e_da.pack(side=tk.LEFT)
    _cal_btn(e_da, f["da"])
    etichetta(r2, "Al:", (8, 4))
    e_a = ttk.Entry(r2, textvariable=f["a"], width=11)
    e_a.pack(side=tk.LEFT)
    _cal_btn(e_a, f["a"])
    tk.Label(r2, text="(GG-MM-AAAA)", bg=bg, fg="gray", font=("Arial", 8, "italic")).pack(side=tk.LEFT, padx=(4, 0))
    btn_reset = tk.Label(r2, text=" Azzera filtri ", bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR, cursor="hand2",
                         padx=8, pady=3, font=("Arial", 9, "bold"))
    btn_reset.pack(side=tk.RIGHT, padx=6)

    def aggiorna_testata():
        spec = _spec_filtri(self)
        freccia = "▾" if stato["aperta"] else "▸"
        stato_txt = ("filtri attivi: " + ", ".join(_descr_filtri(spec))) if spec else "nessun filtro attivo"
        lbl_freccia.config(text=freccia)
        lbl_head.config(text=f"Filtri avanzati  ({stato_txt})",
                        fg=getattr(self, "COLOR_HIGHLIGHT", self.TEXT_COLOR) if spec else self.TEXT_COLOR)

    def applica(*_):
        if stato["sosp"]:
            return
        stato["job"] = None
        try:
            if not popup.winfo_exists():
                return
        except tk.TclError:
            return
        spec = _spec_filtri(self)
        _FILTRI_TXT[0] = (" – Filtri: " + ", ".join(_descr_filtri(spec))) if spec else ""
        for e, k in ((e_da, "da"), (e_a, "a")):
            sbagliata = bool(f[k].get().strip()) and _data_libera(f[k].get()) is None
            try:
                e.configure(foreground="#DC3545" if sbagliata else self.TEXT_COLOR)
            except tk.TclError:
                pass
        aggiorna_testata()
        conto_var.set(conto_var.get())

    def rinvia(*_):
        if stato["job"]:
            popup.after_cancel(stato["job"])
        stato["job"] = popup.after(400, applica)

    def azzera(*_):
        stato["sosp"] = True
        try:
            for k, v in f.items():
                v.set(False if k == "allegato" else (TUTTI if k in ("tipo", "metodo", "orig") else ""))
        finally:
            stato["sosp"] = False
        applica()

    def apri_chiudi(*_):
        stato["aperta"] = not stato["aperta"]
        if stato["aperta"]:
            body.pack(fill=tk.X, before=nb)
        else:
            body.pack_forget()
        aggiorna_testata()

    for k in ("tipo", "metodo", "orig", "allegato"):
        f[k].trace_add("write", applica)
    for k in ("tag", "testo", "da", "a"):
        f[k].trace_add("write", rinvia)
    for _w in (lbl_freccia, lbl_head):
        _w.bind("<Button-1>", apri_chiudi)
    btn_reset.bind("<Button-1>", azzera)
    aggiorna_testata()

def analisi_categorie(self, categoria=None, tab=None):
    esistente = getattr(self, "_analisi_cat_popup", None)
    if esistente is not None:
        try:
            if esistente.winfo_exists():
                esistente.deiconify()
                esistente.lift()
                esistente.focus_force()
                esistente._seleziona(categoria, tab)
                return
        except tk.TclError:
            pass

    popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    self._analisi_cat_popup = popup
    def _alla_chiusura_popup(e):
        if e.widget is popup:
            self._analisi_cat_popup = None
            self._analisi_filtri = None
            _FILTRI_TXT[0] = ""
    popup.bind("<Destroy>", _alla_chiusura_popup)
    popup.withdraw()
    popup.title("Analisi Categorie")
    self.update_idletasks()
    w, h = 1366, 633
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    popup.geometry(f"{w}x{h}+{max(x, 0)}+{max(y, 0)}")
    popup.minsize(1366, 633)
    popup.resizable(True, True)
    popup.transient(self)
    popup.bind("<Escape>", lambda e: popup.destroy())

    main = ttk.Frame(popup, padding=10)
    main.pack(fill=tk.BOTH, expand=True)
    nb = ttk.Notebook(main)
    nb.pack(fill=tk.BOTH, expand=True)

    def nuova_tab(ico, testo):
        fr = ttk.Frame(nb)
        img = self.icone_gui.get(ico)
        if img:
            nb.add(fr, image=img, text=f" {testo} ", compound="left")
        else:
            nb.add(fr, text=testo)
        return fr

    t1, t2, t3, t4, t5, t6, t7, t8 = (nuova_tab("search", "Dettaglio"), nuova_tab("filtri", "Aggrega"),
                                  nuova_tab("timer_sync", "Time Machine"), nuova_tab("report", "Trend mensile"),
                                  nuova_tab("report", "Distribuzione"), nuova_tab("alert", "Budget superato"),
                                  nuova_tab("report", "Target"), nuova_tab("grafico_linea", "50/30/20"))
    rif = {}

    def vai(cat=None, modo=None, anno=None, mese=None):
        rif["dett"](cat, modo, anno, mese)
        nb.select(0)

    chiudi = tk.Frame(main, bg=self.COLOR_TOPLEVEL)
    chiudi.pack(side=tk.BOTTOM, fill=tk.X, pady=(6, 0), before=nb)
    bt = _BarraTotali(self, chiudi)
    bt.frame.pack(side=tk.LEFT)
    _btn(self, chiudi, "chiudi", "Chiudi", popup.destroy, side="right")
    _btn(self, chiudi, "reset", "Reset", bt.reset, side="right")
    nb.bind("<<NotebookTabChanged>>", lambda e: bt.attiva(nb.index(nb.select())))

    conto_var = tk.StringVar(value=HOUSEHOLD_LABEL)
    _barra_filtri(self, popup, main, nb, conto_var)
    set_cat_dett = _tab_dettaglio(self, t1, categoria, conto_var, bt)
    rif["dett"] = set_cat_dett
    _tab_aggrega(self, t2, vai, conto_var, bt)
    _tab_time_machine(self, t3, vai, conto_var, bt)
    set_cat_trend = _tab_trend(self, t4, categoria, vai, conto_var, bt)
    set_cat_dist = _tab_distribuzione(self, t5, categoria, vai, conto_var, bt)
    _tab_budget_superato(self, t6, vai, conto_var, bt)
    _tab_target(self, t7, vai, conto_var, bt)
    _tab_503020(self, t8, vai, conto_var, bt)

    def seleziona(cat=None, tab_sel=None):
        if cat:
            set_cat_dett(cat)
            set_cat_trend(cat)
            set_cat_dist(cat)
        if tab_sel is None and cat:
            tab_sel = 0
        if isinstance(tab_sel, str) and tab_sel.lower() in TAB_NOMI:
            tab_sel = TAB_NOMI.index(tab_sel.lower())
        if isinstance(tab_sel, int) and 0 <= tab_sel < 8:
            nb.select(tab_sel)

    popup._seleziona = seleziona
    seleziona(categoria, tab)
    popup.update_idletasks()
    popup.deiconify()
    popup.focus_set()

