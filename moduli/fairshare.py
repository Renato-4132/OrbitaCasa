#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import tkinter as tk
from tkinter import ttk, filedialog
import datetime
from collections import defaultdict

import __main__ as _app
from moduli.modello_spesa import SIMBOLI_METODO, SpesaEntry, campo

ICONE_TAG = ("CNT·", "PER·", "CTP·")
FMT_DATA = "%d/%m/%Y"


def _fmt_it(v, spec=",.2f"):
    s = format(v, spec)
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def _quota_persona(deb, nome):
    return deb.get("quote", {}).get(nome, deb.get("quota", 0.0))


def _compensa_debiti(chi_deve):
    netto = {}
    for (debitore, creditore), imp in chi_deve.items():
        diff = round(imp - chi_deve.get((creditore, debitore), 0.0), 2)
        if diff > 0.005:
            netto[(debitore, creditore)] = diff
    return netto


def _nome_gestore():
    profilo = getattr(_app, "PROFILO_ATTIVO", "Principale")
    return profilo if profilo != "Principale" else os.path.basename(os.getcwd())


def _gn(p):
    return p.get("nome", "") if isinstance(p, dict) else p


def _percentuale_di(self, nome):
    for p in self.nomi_partecipanti:
        if isinstance(p, dict) and p.get("nome") == nome:
            pct = p.get("percentuale")
            if pct is None:
                return None
            try:
                return float(pct)
            except (TypeError, ValueError):
                return None
    return None


def calcola_quote_spesa(self, imp, partecipanti):
    partecipanti = list(dict.fromkeys(partecipanti))
    n = len(partecipanti)
    if n == 0:
        return {}
    percentuali = {}
    for nm in partecipanti:
        pct = _percentuale_di(self, nm)
        percentuali[nm] = pct if (pct is not None and pct >= 0) else None
    fissi  = {nm: pct for nm, pct in percentuali.items() if pct is not None}
    liberi = [nm for nm in partecipanti if percentuali[nm] is None]
    somma_fissi = sum(fissi.values())
    if somma_fissi > 100.0 + 1e-9:
        fattore = 100.0 / somma_fissi
        fissi = {nm: pct * fattore for nm, pct in fissi.items()}
        somma_fissi = 100.0
    pct_finali = dict(fissi)
    if liberi:
        pct_libero = max(0.0, 100.0 - somma_fissi) / len(liberi)
        for nm in liberi:
            pct_finali[nm] = pct_libero
    elif somma_fissi <= 0:
        pct_finali = {nm: 100.0 / n for nm in partecipanti}
    elif abs(somma_fissi - 100.0) > 0.01:
        fattore = 100.0 / somma_fissi
        pct_finali = {nm: pct * fattore for nm, pct in fissi.items()}
    segno = -1 if imp < 0 else 1
    cent_tot = int(round(abs(imp) * 100))
    quote = {}
    residuo = cent_tot
    for i, nm in enumerate(partecipanti):
        if i == n - 1:
            c = residuo
        else:
            c = min(residuo, int(cent_tot * pct_finali.get(nm, 0.0) / 100.0 + 0.5 + 1e-9))
            residuo -= c
        quote[nm] = segno * c / 100.0
    return quote


# Descrizione: inserimento/sostituzione del tag partecipante (PER· / CNT· / CTP·)
def _riscrivi_descrizione(self, scelta_combo, desc):
    if scelta_combo and "Gestisci Partecipanti" in scelta_combo:
        return None
    nome_nuovo = ""
    nuova_ico = ""
    if scelta_combo:
        nome_nuovo = scelta_combo.strip()
        for ico in ICONE_TAG:
            if nome_nuovo.startswith(ico):
                nome_nuovo = nome_nuovo[len(ico):].strip()
                break
        nuova_ico = "PER·"
        for p in self.nomi_partecipanti:
            if isinstance(p, dict) and p.get("nome") == nome_nuovo:
                nuova_ico = {"personale": "CTP·", "contenitore": "CNT·"}.get(p.get("tipo"), "PER·")
                break
    desc = desc.strip()
    prefisso_pag = ""
    for s in set(SIMBOLI_METODO.values()):
        if desc.startswith(s):
            prefisso_pag = s
            desc = desc[len(s):].strip()
            break
    nomi_noti = sorted([_gn(p) for p in self.nomi_partecipanti] + [_nome_gestore()],
                       key=len, reverse=True)
    tolto = False
    for ico in ICONE_TAG:
        for nome in nomi_noti:
            pref = f"{ico}{nome}"
            if nome and desc.startswith(pref):
                desc = desc[len(pref):].strip()
                tolto = True
                break
        if tolto:
            break
    if not tolto:
        for ico in ICONE_TAG:
            if desc.startswith(ico):
                desc = desc[len(ico):].strip()
                break
    parti = [x for x in (prefisso_pag, f"{nuova_ico}{nome_nuovo}" if nome_nuovo else "", desc) if x]
    return " ".join(parti)


def _on_partecipante_selected(self, event=None):
    scelta = self.partecipante_var.get()
    if "Gestisci Partecipanti" in scelta:
        self.partecipante_var.set("")
        self.gestisci_partecipanti()
        return
    self._aggiorna_descrizione_con_partecipante(scelta)


def _aggiorna_descrizione_con_partecipante(self, scelta_combo, target_var=None):
    desc = target_var.get() if target_var else self.desc_entry.get()
    nuova = _riscrivi_descrizione(self, scelta_combo, desc)
    if nuova is None:
        return
    self.desc_entry.delete(0, "end")
    self.desc_entry.insert(0, nuova)
    self.desc_entry.icursor("end")


def _on_ric_partecipante_selected(self, event=None):
    scelta = self.ric_partecipante_var.get()
    if "Gestisci Partecipanti" in scelta:
        self.ric_partecipante_var.set("")
        self.gestisci_partecipanti()
        return
    self._aggiorna_descrizione_con_ric_partecipante(scelta)


def _aggiorna_descrizione_con_ric_partecipante(self, scelta_combo, target_var=None):
    desc = target_var.get() if target_var else self.ricorrenza_desc.get()
    nuova = _riscrivi_descrizione(self, scelta_combo, desc)
    if nuova is None:
        return
    self.ricorrenza_desc.set(nuova)


def _gestore_partecipa(self):
    return bool(getattr(self, "fairshare_gestore_partecipa", True))


def carica_partecipanti_da_db(self):
    blocco = (getattr(self, "db", None) or {}).get("fairshare")
    if isinstance(blocco, dict):
        lista = blocco.get("partecipanti", []) or []
        gestore = blocco.get("gestore_partecipa", True)
    elif hasattr(self, "nomi_partecipanti"):
        # db senza blocco fairshare (es. import di un export vecchio): tengo i partecipanti attuali
        return
    else:
        lista, gestore = [], True
    self.nomi_partecipanti = [
        p if isinstance(p, dict) else {"nome": p, "tipo": "persona"}
        for p in lista if p
    ]
    self.fairshare_gestore_partecipa = bool(gestore)


def rinomina_partecipante_fairshare(self, vecchio, nuovo):
    nuovo = (nuovo or "").strip()
    if not nuovo:
        return False, "Il nuovo nome è vuoto."
    if nuovo == vecchio:
        return False, "Il nome è uguale a quello attuale."
    if nuovo in {_gn(p) for p in self.nomi_partecipanti} | {_nome_gestore()}:
        return False, f"'{nuovo}' è già presente."
    anagrafica = next((p for p in self.nomi_partecipanti
                       if isinstance(p, dict) and p.get("nome") == vecchio), None)
    if anagrafica is None:
        return False, f"'{vecchio}' non trovato."
    nomi_alt = sorted({_gn(p) for p in self.nomi_partecipanti} | {_nome_gestore(), vecchio},
                      key=len, reverse=True)
    rx = re.compile(r"(PER|CNT|CTP)·(" + "|".join(re.escape(n) for n in nomi_alt if n) + r")(?!\w)")
    def sost(testo):
        if not isinstance(testo, str):
            return testo
        return rx.sub(lambda m: f"{m.group(1)}·{nuovo}" if m.group(2) == vecchio else m.group(0), testo)
    n_voci = 0
    for voci in self.spese.values():
        for v in voci:
            if not isinstance(v, SpesaEntry):
                continue
            mod = False
            d2 = sost(v.descrizione)
            if d2 != v.descrizione:
                v.descrizione = d2
                mod = True
            pag = (v.fairshare or {}).get("pagamenti", {})
            if vecchio in pag:
                pag[nuovo] = pag.pop(vecchio)
                mod = True
            if mod:
                n_voci += 1
    for r in (getattr(self, "ricorrenze", None) or {}).values():
        if isinstance(r, dict) and "desc" in r:
            r["desc"] = sost(r["desc"])
    anagrafica["nome"] = nuovo
    for p in self.nomi_partecipanti:
        if isinstance(p, dict) and vecchio in p.get("soci", []):
            p["soci"] = [nuovo if s == vecchio else s for s in p["soci"]]
    self.save_db()
    try:
        from moduli.spese_pianificate import _carica_sp, _salva_sp
        dati = _carica_sp(self)
        cambiato = False
        for piano in dati.get("piani", []):
            for k in ("descrizione", "nome"):
                nv = sost(piano.get(k))
                if nv != piano.get(k):
                    piano[k] = nv
                    cambiato = True
        if cambiato:
            _salva_sp(self, dati)
    except Exception:
        pass
    if hasattr(self, "refresh_gui"):
        self.refresh_gui()
    return True, f"'{vecchio}' rinominato in '{nuovo}' ({n_voci} movimenti aggiornati)."


# Motore FairShare 
def _rx_tag(sigla, nomi):
    nomi = sorted({n for n in nomi if n}, key=len, reverse=True)
    if not nomi:
        return None
    return re.compile(sigla + "·(" + "|".join(re.escape(n) for n in nomi) + r")(?!\w)")


def _contesto_fairshare(self):
    gestore = _nome_gestore()
    parts = [p for p in self.nomi_partecipanti if isinstance(p, dict) and p.get("nome")]
    persone = {p["nome"] for p in parts if p.get("tipo", "persona") == "persona"}
    if _gestore_partecipa(self):
        persone.add(gestore)
    persone = sorted(persone, key=lambda n: (-len(n), n))
    contenitori = {
        p["nome"]: [s for s in p.get("soci", []) if s in persone]
        for p in parts if p.get("tipo") == "contenitore"
    }
    tutti_nomi = [p["nome"] for p in parts] + [gestore]
    nomi_alt = sorted(set(tutti_nomi), key=len, reverse=True)
    rx_pulisci = re.compile(
        "(?:PER|CNT|CTP)·(?:" + "|".join(re.escape(n) for n in nomi_alt) + r")(?!\w)"
    )
    return {
        "gestore":     gestore,
        "persone":     persone,
        "contenitori": contenitori,
        "rx_per":      _rx_tag("PER", persone),
        "rx_cnt":      _rx_tag("CNT", contenitori.keys()),
        "rx_pulisci":  rx_pulisci,
    }


def _analizza_descrizione(desc, ctx):
    parti = []
    if ctx["rx_cnt"]:
        for m in ctx["rx_cnt"].finditer(desc):
            soci = ctx["contenitori"].get(m.group(1), [])
            if soci:
                parti = list(soci)
                break
    creditore = None
    if ctx["rx_per"]:
        m = ctx["rx_per"].search(desc)
        if m:
            creditore = m.group(1)
    if not parti and creditore:
        parti = list(ctx["persone"]) or [creditore]
    if not parti:
        return None
    return creditore or ctx["gestore"], sorted(set(parti))


def _stato_debito(deb):
    parti = deb.get("partecipanti", [])
    tutti_ok = bool(parti) and all(
        deb["pagamenti"].get(nm, {}).get("pagato", False) for nm in parti
    )
    deb["stato"] = "chiuso" if tutti_ok else "aperto"


def _debito_da_voce(self, data_obj, voce, ctx):
    if not isinstance(voce, SpesaEntry):
        return None
    if str(campo(voce, "tipo", "")).strip() != "Uscita":
        return None
    try:
        imp = round(float(campo(voce, "importo", 0.0)), 2)
    except (TypeError, ValueError):
        return None
    if imp <= 0:
        return None
    desc_str = str(campo(voce, "descrizione", "")).strip()
    esito = _analizza_descrizione(desc_str, ctx)
    if not esito:
        return None
    creditore, parti = esito
    n = len(parti)
    data_str = data_obj.strftime(FMT_DATA)
    id_spesa = campo(voce, "id_spesa", "")
    salvati = (campo(voce, "fairshare", None) or {}).get("pagamenti", {})
    pagamenti = {}
    for nm in parti:
        info = salvati.get(nm)
        if isinstance(info, dict) and info.get("sorgente") in ("manuale", "auto"):
            pagamenti[nm] = {"pagato": bool(info.get("pagato")),
                             "data": info.get("data"),
                             "sorgente": info["sorgente"]}
        elif nm == creditore:
            pagamenti[nm] = {"pagato": True, "data": data_str, "sorgente": "creditore"}
        else:
            pagamenti[nm] = {"pagato": False, "data": None}
    desc_pulita = " ".join(ctx["rx_pulisci"].sub("", desc_str).split())
    deb = {
        "_key":           f"{data_str}#{id_spesa}",
        "_id_spesa":      id_spesa,
        "data":           data_str,
        "categoria":      str(campo(voce, "categoria", "")).strip(),
        "descrizione":    desc_pulita,
        "importo_totale": imp,
        "quota":          round(imp / n, 2),
        "quote":          calcola_quote_spesa(self, imp, parti),
        "n_partecipanti": n,
        "creditore":      creditore,
        "partecipanti":   parti,
        "pagamenti":      pagamenti,
        "ora":            campo(voce, "ora", ""),
        "hashtag":        list(campo(voce, "hashtag", []) or []),
    }
    _stato_debito(deb)
    return voce, deb


def _coppie_debiti(self, ctx):
    coppie = []
    for data_obj in sorted(k for k in self.spese if isinstance(k, datetime.date)):
        for voce in self.spese[data_obj]:
            r = _debito_da_voce(self, data_obj, voce, ctx)
            if r:
                coppie.append(r)
    return coppie


def _entrate_pagate(self, ctx):
    out = defaultdict(list)
    if not ctx["rx_per"]:
        return out
    for data_obj in sorted(k for k in self.spese if isinstance(k, datetime.date)):
        for voce in self.spese[data_obj]:
            if str(campo(voce, "tipo", "")).strip() != "Entrata":
                continue
            m = ctx["rx_per"].search(str(campo(voce, "descrizione", "")))
            if not m:
                continue
            try:
                imp = round(float(campo(voce, "importo", 0.0)), 2)
            except (TypeError, ValueError):
                continue
            out[(m.group(1), str(campo(voce, "categoria", "")).strip(), imp)].append(data_obj)
    return out


def _applica_pagamenti_auto(coppie, entrate):
    for _voce, deb in coppie:
        cat = deb["categoria"]
        for nm, info in list(deb["pagamenti"].items()):
            sorgente = info.get("sorgente", "")
            if sorgente in ("manuale", "creditore"):
                continue
            lista = entrate.get((nm, cat, round(_quota_persona(deb, nm), 2)))
            if lista:
                d_ent = lista.pop(0)
                if not info.get("pagato"):
                    deb["pagamenti"][nm] = {"pagato": True,
                                            "data": d_ent.strftime(FMT_DATA),
                                            "sorgente": "auto"}
            elif info.get("pagato") and sorgente == "auto":
                deb["pagamenti"][nm] = {"pagato": False, "data": None}
        _stato_debito(deb)


def _payload_fs(deb):
    pag = {
        nm: {"pagato": bool(i.get("pagato")), "data": i.get("data"), "sorgente": i["sorgente"]}
        for nm, i in deb.get("pagamenti", {}).items()
        if i.get("sorgente") in ("manuale", "auto")
    }
    return {"pagamenti": pag} if pag else None


def _persisti_pagamenti(coppie):
    modificato = False
    for voce, deb in coppie:
        nuovo = _payload_fs(deb)
        if (voce.fairshare or None) != nuovo:
            voce.fairshare = nuovo
            modificato = True
    return modificato


def carica_fairshare_state(self):
    ctx = _contesto_fairshare(self)
    coppie = _coppie_debiti(self, ctx)
    _applica_pagamenti_auto(coppie, _entrate_pagate(self, ctx))
    return [deb for _v, deb in coppie]


def salva_fairshare_state(self, debiti):
    idx = {}
    for voci in self.spese.values():
        for v in voci:
            if isinstance(v, SpesaEntry):
                idx[v.id_spesa] = v
    modificato = False
    for deb in debiti:
        voce = idx.get(deb.get("_id_spesa"))
        if voce is None:
            continue
        nuovo = _payload_fs(deb)
        if (voce.fairshare or None) != nuovo:
            voce.fairshare = nuovo
            modificato = True
    if modificato:
        self.save_db()


def sincronizza_fairshare_state(self):
    ctx = _contesto_fairshare(self)
    coppie = _coppie_debiti(self, ctx)
    _applica_pagamenti_auto(coppie, _entrate_pagate(self, ctx))
    if _persisti_pagamenti(coppie):
        self.save_db()
    return [deb for _v, deb in coppie]


def _sync_fairshare_e_aggiorna(self):
    sincronizza_fairshare_state(self)
    def _aggiorna_se_aperta():
        try:
            if (getattr(self, '_dare_avere_aggiorna', None) and
                    getattr(self, '_dare_avere_popup', None) and
                    self._dare_avere_popup.winfo_exists()):
                self._dare_avere_aggiorna()
        except Exception:
            pass
    self.after(50, _aggiorna_se_aperta)


def mostra_riepilogo_fairshare_periodo(self):
    if hasattr(self, '_analitico_popup') and self._analitico_popup and self._analitico_popup.winfo_exists():
        self._analitico_popup.lift(); self._analitico_popup.focus_force(); return
    debiti = self.sincronizza_fairshare_state()
    parent = self._dare_avere_popup if hasattr(self, '_dare_avere_popup') and self._dare_avere_popup and self._dare_avere_popup.winfo_exists() else self
    popup = tk.Toplevel(parent, bg=self.COLOR_TOPLEVEL)
    popup.title("FairShare — Estratto Analitico per Spesa")
    self._analitico_popup = popup
    popup.bind("<Escape>", lambda e: popup.destroy())
    popup.bind("<Destroy>", lambda e: setattr(self, '_analitico_popup', None) if e.widget is popup else None)
    popup.withdraw()
    self.update_idletasks()
    w, h = 1250, 650
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    popup.geometry(f"{w}x{h}+{x}+{y}")
    popup.minsize(w, h)
    popup.transient(parent)
    popup.deiconify()
    popup.lift()
    popup.focus_force()
    oggi = datetime.date.today()
    mesi_nomi = ["Tutti", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                 "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    anni_db = sorted({d.year for d in self.spese if isinstance(d, datetime.date)}, reverse=True)
    if oggi.year not in anni_db:
        anni_db.insert(0, oggi.year)
    nomi_p_raw = {p["nome"]: p.get("tipo","persona") for p in self.nomi_partecipanti
                  if p.get("tipo") in ("persona","contenitore")}
    _gestore = _nome_gestore()
    if self._gestore_partecipa() and _gestore not in nomi_p_raw:
        nomi_p_raw[_gestore] = "persona"
    def _ico_p(nome):
        return "CNT·" if nomi_p_raw.get(nome) == "contenitore" else "PER·"
    nomi_p = ["Tutti"] + sorted([f"{_ico_p(n)} {n}" for n in nomi_p_raw], key=lambda x: x.split(" ", 1)[1].lower())
    cat_lst = ["Tutte"] + sorted(self.categorie, key=str.lower)
    filter_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL, pady=8)
    filter_f.pack(fill=tk.X, padx=15)
    def _lbl2(t):
        tk.Label(filter_f, text=t, bg=self.COLOR_TOPLEVEL,
                 fg=self.TEXT_COLOR, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(6, 2))
    _lbl2("Partecipante:")
    cb_part = ttk.Combobox(filter_f, values=nomi_p, width=18,
                           state="readonly", style="Border.TCombobox")
    cb_part.set("Tutti"); cb_part.pack(side=tk.LEFT, padx=3)
    _lbl2("Anno:")
    cb_anno = ttk.Combobox(filter_f, values=["Tutti"] + [str(a) for a in anni_db],
                           width=7, state="readonly", style="Border.TCombobox")
    cb_anno.set("Tutti"); cb_anno.pack(side=tk.LEFT, padx=3)
    _lbl2("Mese:")
    cb_mese = ttk.Combobox(filter_f, values=mesi_nomi, width=11,
                           state="readonly", style="Border.TCombobox")
    cb_mese.set("Tutti"); cb_mese.pack(side=tk.LEFT, padx=3)
    _lbl2("Categoria:")
    cb_cat = ttk.Combobox(filter_f, values=cat_lst, width=20,
                          state="readonly", style="Border.TCombobox")
    cb_cat.set("Tutte"); cb_cat.pack(side=tk.LEFT, padx=3)
    _lbl2("Stato:")
    cb_stato = ttk.Combobox(filter_f, values=["Tutti", "Aperto", "Chiuso"],
                            width=8, state="readonly", style="Border.TCombobox")
    cb_stato.set("Aperto"); cb_stato.pack(side=tk.LEFT, padx=3)

    tree_frame = ttk.Frame(popup)
    tree_frame.pack(fill=tk.X, padx=15, pady=5)
    cols_a = ("Data", "Categoria", "Descrizione", "Totale €", "Quota €",
              "N.Part.", "Paganti ✅", "In Attesa 🔴", "Stato")
    tree_a = ttk.Treeview(tree_frame, columns=cols_a, show="headings", height=15)
    vsb_a  = ttk.Scrollbar(tree_frame, orient="vertical", command=tree_a.yview)
    tree_a.configure(yscrollcommand=vsb_a.set)
    tree_a.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    vsb_a.pack(side=tk.RIGHT, fill=tk.Y)
    w_map = {"Data": 90, "Categoria": 110, "Descrizione": 260,
             "Totale €": 90, "Quota €": 80, "N.Part.": 55,
             "Paganti ✅": 110, "In Attesa 🔴": 120, "Stato": 90}
    _col_num = ("Totale €", "Quota €", "N.Part.", "Paganti ✅", "In Attesa 🔴")
    def _val_sort(col, v):
        s = str(v).replace("€", "").strip()
        if col == "Data":
            try:
                return datetime.datetime.strptime(s, "%d/%m/%Y")
            except Exception:
                return None
        if col in _col_num:
            try:
                return float(s.replace(".", "").replace(",", "."))
            except Exception:
                return None
        return s.lower()
    _sort_stato = {"col": None, "rev": False}
    def _sort_analitico(col, reverse=False):
        _sort_stato["col"], _sort_stato["rev"] = col, reverse
        righe = [(_val_sort(col, tree_a.set(k, col)), k) for k in tree_a.get_children("")]
        con    = [(v, k) for v, k in righe if v is not None]
        senza  = [k for v, k in righe if v is None]
        con.sort(key=lambda t: t[0], reverse=reverse)
        for i, k in enumerate([k for _, k in con] + senza):
            tree_a.move(k, "", i)
        for c in cols_a:
            freccia = (" ▼" if reverse else " ▲") if c == col else ""
            tree_a.heading(c, text=c + freccia,
                           command=lambda _c=c: _sort_analitico(_c, not reverse if _c == col else False))
    for col in cols_a:
        tree_a.heading(col, text=col, command=lambda c=col: _sort_analitico(c, False))
        tree_a.column(col, width=w_map.get(col, 100),
                      anchor="w" if col == "Descrizione" else "center")
    tree_a.tag_configure("aperto",  foreground="#E06C75")
    tree_a.tag_configure("chiuso",  foreground="#61AFEF")
    self._bind_tooltip_metodo(tree_a, col_desc=2)
    _riga_deb_a = {}
    def _vai_a_spesa_a(event):
        deb = _riga_deb_a.get(tree_a.identify_row(event.y))
        if not deb:
            return
        try:
            d = datetime.datetime.strptime(deb.get("data", ""), "%d/%m/%Y").date()
        except ValueError:
            return
        self.vai_a_spesa(d, popup, str(deb.get("descrizione", ""))[:20], deb.get("_id_spesa", ""))
    tree_a.bind("<Double-1>", _vai_a_spesa_a)
    det_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    det_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 4))
    vsb_det = ttk.Scrollbar(det_frame, orient="vertical", style="Vertical.TScrollbar")
    vsb_det.pack(side=tk.RIGHT, fill=tk.Y)
    lbl_det = tk.Text(det_frame, bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                      height=8, borderwidth=0, font=("Courier New", 9),
                      wrap="none", highlightthickness=0, relief="flat",
                      yscrollcommand=vsb_det.set)
    lbl_det.pack(fill=tk.BOTH, expand=True)
    vsb_det.config(command=lbl_det.yview)
    lbl_det.tag_config("verde",  foreground="#98C379")
    lbl_det.tag_config("rosso",  foreground="#E06C75")
    lbl_det.tag_config("giallo", foreground="#E5C07B")
    lbl_det.tag_config("neutro", foreground=self.TEXT_COLOR)
    lbl_det.tag_config("bold",   font=("Courier New", 9, "bold"))
    def aggiorna_tabella(*_args):
        tree_a.delete(*tree_a.get_children())
        tree_a._metodo_lookup = {}
        _riga_deb_a.clear()
        p_sel  = cb_part.get()
        if p_sel not in ("", "Tutti") and " " in p_sel:
            p_sel = p_sel.split(" ", 1)[1].strip()
        a_sel  = cb_anno.get()
        m_idx  = mesi_nomi.index(cb_mese.get())
        c_sel  = cb_cat.get()
        st_sel = cb_stato.get()
        tot_dovuto = {}; tot_versato = {}; tot_debito = {}; chi_deve_a_chi_a = {}
        def _chiave_data(d):
            try:
                return datetime.datetime.strptime(d.get("data", ""), "%d/%m/%Y")
            except Exception:
                return datetime.datetime.max
        for deb in sorted(debiti, key=_chiave_data):
            data_str = deb.get("data", "")
            try:
                d_obj = datetime.datetime.strptime(data_str, "%d/%m/%Y").date()
            except Exception:
                continue
            if a_sel != "Tutti" and str(d_obj.year) != a_sel: continue
            if m_idx > 0 and d_obj.month != m_idx: continue
            if c_sel != "Tutte" and deb.get("categoria") != c_sel: continue
            stato = deb.get("stato", "aperto")
            if st_sel != "Tutti" and stato != st_sel.lower(): continue
            pag   = deb.get("pagamenti", {})
            parti = deb.get("partecipanti", [])
            if p_sel != "Tutti" and p_sel not in parti:
                continue
            imp     = deb.get("importo_totale", 0.0)
            if p_sel != "Tutti":
                quota_txt = f"{_fmt_it(_quota_persona(deb, p_sel))} €"
            else:
                _qv = [_quota_persona(deb, n) for n in parti]
                quota_txt = "—" if _qv and max(_qv) - min(_qv) > 0.01 else f"{_fmt_it(deb.get('quota', 0.0))} €"
            paganti = [n for n in parti if pag.get(n, {}).get("pagato", False)]
            attesa  = [n for n in parti if not pag.get(n, {}).get("pagato", False)]
            st_ic   = "Chiuso" if stato == "chiuso" else "Aperto"
            tag_row = "chiuso" if stato == "chiuso" else "aperto"
            _iid_a = tree_a.insert("", "end", tags=(tag_row,), values=(
                data_str,
                deb.get("categoria", ""),
                deb.get("descrizione", ""),
                f"{_fmt_it(imp)} €",
                quota_txt,
                len(parti),
                len(paganti),
                len(attesa),
                st_ic,
            ))
            _riga_deb_a[_iid_a] = deb
            _extra_a = []
            if deb.get("creditore"):
                _extra_a.append(("Creditore", deb.get("creditore")))
            _extra_a.append(("Paganti", ", ".join(paganti) if paganti else "—"))
            _extra_a.append(("In attesa", ", ".join(attesa) if attesa else "—"))
            tree_a._metodo_lookup[_iid_a] = {
                "data": d_obj.strftime("%d-%m-%Y"),
                "categoria": deb.get("categoria", ""),
                "importo": imp,
                "ora": deb.get("ora", ""),
                "hashtag": deb.get("hashtag", []),
                "_righe_extra": _extra_a,
            }
            for nome in parti:
                if p_sel != "Tutti" and nome != p_sel: continue
                quota = _quota_persona(deb, nome)
                tot_dovuto.setdefault(nome, 0.0);  tot_dovuto[nome] += quota
                tot_versato.setdefault(nome, 0.0); tot_debito.setdefault(nome, 0.0)
                if pag.get(nome, {}).get("pagato", False):
                    tot_versato[nome] += quota
                else:
                    tot_debito[nome] += quota
                    creditore = deb.get("creditore", "")
                    if creditore and creditore != nome:
                        chi_deve_a_chi_a.setdefault((nome, creditore), 0.0)
                        chi_deve_a_chi_a[(nome, creditore)] += quota
        chi_deve_a_chi_a = _compensa_debiti(chi_deve_a_chi_a)
        lbl_det.config(state="normal")
        lbl_det.delete("1.0", "end")
        lbl_det.insert("end",
            f"{'PERSONA':<20} {'DOVUTO':>12} {'VERSATO':>12} {'RESIDUO':>12}   SALDO\n",
            "bold")
        lbl_det.insert("end", "─" * 75 + "\n", "neutro")
        for nome in sorted(tot_dovuto.keys()):
            dov = tot_dovuto[nome]
            ver = tot_versato.get(nome, 0.0)
            res = tot_debito.get(nome, 0.0)
            sal_tag = "verde" if res < 0.01 else "rosso"
            lbl_det.insert("end", f"  {nome:<18} ", "neutro")
            lbl_det.insert("end", f"{_fmt_it(dov, '>11,.2f')} €  ", "giallo")
            lbl_det.insert("end", f"{_fmt_it(ver, '>11,.2f')} €  ", "verde")
            lbl_det.insert("end", f"{_fmt_it(res, '>11,.2f')} €  ", sal_tag)
            lbl_det.insert("end",
                ("Saldato\n" if res < 0.01 else f"Deve {_fmt_it(res)} EUR\n"),
                sal_tag)
        if tot_dovuto:
            lbl_det.insert("end", "─" * 75 + "\n", "neutro")
            td = sum(tot_dovuto.values()); tv = sum(tot_versato.values())
            tr = sum(tot_debito.values())
            lbl_det.insert("end", f"  {'TOTALE':<18} ", "bold")
            lbl_det.insert("end", f"{_fmt_it(td, '>11,.2f')} €  ", "giallo")
            lbl_det.insert("end", f"{_fmt_it(tv, '>11,.2f')} €  ", "verde")
            lbl_det.insert("end", f"{_fmt_it(tr, '>11,.2f')} €\n",
                           "verde" if tr < 0.01 else "rosso")
            if chi_deve_a_chi_a:
                lbl_det.insert("end", "\n", "neutro")
                lbl_det.insert("end", "  CHI DEVE A CHI:\n", "bold")
                for (debitore, creditore), importo in sorted(
                        chi_deve_a_chi_a.items(), key=lambda x: (x[0][1], x[0][0])):
                    lbl_det.insert("end", f"  {debitore} → {creditore}: ", "neutro")
                    lbl_det.insert("end", f"{_fmt_it(importo)} EUR\n", "rosso")
        else:
            lbl_det.insert("end", "  Nessun risultato per i filtri selezionati.\n", "neutro")
        lbl_det.config(state="disabled")
        if _sort_stato["col"]:
            _sort_analitico(_sort_stato["col"], _sort_stato["rev"])

    def apri_anteprima_export():
        p_sel = cb_part.get(); a_sel = cb_anno.get()
        m_sel = cb_mese.get(); c_sel = cb_cat.get(); st_sel = cb_stato.get()
        sep = "═" * 105
        header  = "FAIRSHARE — ESTRATTO ANALITICO\n"
        header += f"Partecipante: {p_sel}  Anno: {a_sel}  Mese: {m_sel}  "
        header += f"Categoria: {c_sel}  Stato: {st_sel}\n{sep}\n"
        header += (f"{'DATA':<10} {'CATEGORIA':<15} {'DESCRIZIONE':<25} "
                   f"{'TOTALE':>9} {'QUOTA':>9} {'N':>3} "
                   f"{'PAGATO':>7} {'ATTESA':>7}  STATO\n{'─'*105}\n")
        body = ""
        for iid in tree_a.get_children():
            v = tree_a.item(iid, "values")
            body += (f"{str(v[0]):<10} {str(v[1]):<15} {str(v[2])[:25]:<25} "
                     f"{str(v[3]):>9} {str(v[4]):>9} {str(v[5]):>3} "
                     f"{str(v[6]):>7} {str(v[7]):>7}  {str(v[8])}\n")
        footer  = f"\n{sep}\nRIEPILOGO PER PERSONA\n{sep}\n"
        footer += f"{'PERSONA':<20} {'DOVUTO':>15} {'VERSATO':>18} {'RESIDUO':>18}   SALDO\n"
        footer += "─" * 105 + "\n"
        m_idx2 = mesi_nomi.index(m_sel)
        st_sel2 = st_sel
        tot_d3 = {}; tot_v3 = {}; tot_r3 = {}
        for deb in debiti:
            ds = deb.get("data", "")
            try:
                d_obj = datetime.datetime.strptime(ds, "%d/%m/%Y").date()
            except Exception:
                continue
            if a_sel != "Tutti" and str(d_obj.year) != a_sel: continue
            if m_idx2 > 0 and d_obj.month != m_idx2: continue
            if c_sel != "Tutte" and deb.get("categoria") != c_sel: continue
            st2 = deb.get("stato", "aperto")
            if st_sel2 != "Tutti" and st2 != st_sel2.lower(): continue
            for nome in deb.get("partecipanti", []):
                if p_sel != "Tutti" and nome != p_sel: continue
                q = _quota_persona(deb, nome)
                pag2 = deb.get("pagamenti", {}).get(nome, {}).get("pagato", False)
                tot_d3.setdefault(nome, 0.0); tot_d3[nome] += q
                tot_v3.setdefault(nome, 0.0); tot_r3.setdefault(nome, 0.0)
                if pag2: tot_v3[nome] += q
                else:    tot_r3[nome] += q
        for nome in sorted(tot_d3.keys()):
            dov = tot_d3[nome]; ver = tot_v3.get(nome, 0); res = tot_r3.get(nome, 0)
            sal_s = "SALDATO" if res < 0.01 else f"DEVE {_fmt_it(res)} EUR"
            footer += (f"  {nome:<18} {_fmt_it(dov, '>12,.2f')} EUR  "
                       f"{_fmt_it(ver, '>12,.2f')} EUR  {_fmt_it(res, '>12,.2f')} EUR   {sal_s}\n")
        footer += "─" * 105 + "\n"
        td2 = sum(tot_d3.values()); tv2 = sum(tot_v3.values()); tr2 = sum(tot_r3.values())
        footer += (f"  {'TOTALE':<18} {_fmt_it(td2, '>12,.2f')} EUR  "
                   f"{_fmt_it(tv2, '>12,.2f')} EUR  {_fmt_it(tr2, '>12,.2f')} EUR\n")
        chi3 = {}
        for deb in debiti:
            ds = deb.get("data", "")
            try:
                d_obj = datetime.datetime.strptime(ds, "%d/%m/%Y").date()
            except Exception:
                continue
            if a_sel != "Tutti" and str(d_obj.year) != a_sel: continue
            if m_idx2 > 0 and d_obj.month != m_idx2: continue
            if c_sel != "Tutte" and deb.get("categoria") != c_sel: continue
            st2 = deb.get("stato", "aperto")
            if st_sel2 != "Tutti" and st2 != st_sel2.lower(): continue
            creditore = deb.get("creditore", "")
            for nome in deb.get("partecipanti", []):
                if p_sel != "Tutti" and nome != p_sel: continue
                if not deb.get("pagamenti", {}).get(nome, {}).get("pagato", False):
                    if creditore and creditore != nome:
                        chi3.setdefault((nome, creditore), 0.0)
                        chi3[(nome, creditore)] += _quota_persona(deb, nome)
        chi3 = _compensa_debiti(chi3)
        if chi3:
            footer += "\nCHI DEVE A CHI:\n"
            for (debitore, creditore), importo in sorted(
                    chi3.items(), key=lambda x: (x[0][1], x[0][0])):
                footer += f"  {debitore} -> {creditore}: {_fmt_it(importo)} EUR\n"
        self.show_export_preview(header + body + footer,
                                 f"FairShare_Analitico_{p_sel}_{a_sel}.txt")
    btn_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=10, padx=15)
    for ico, lbl_t, cmd in [
        ("salva",  " Esporta", lambda e: apri_anteprima_export()),
        ("chiudi", " Chiudi",  lambda e: popup.destroy())
    ]:
        img = self.icone_gui.get(ico)
        side = tk.RIGHT if ico == "chiudi" else tk.LEFT
        b = ttk.Label(btn_frame, compound="left", image=img,
                      text=lbl_t if img else lbl_t.strip(),
                      background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                      cursor="hand2", padding=(12, 6))
        b.pack(side=side, padx=5)
        b.bind("<Button-1>", cmd)
    for cb_w in [cb_part, cb_anno, cb_mese, cb_cat, cb_stato]:
        cb_w.bind("<<ComboboxSelected>>", aggiorna_tabella)
    aggiorna_tabella()

def popup_personali(self):
    if hasattr(self, '_popup_personali_win') and self._popup_personali_win.winfo_exists():
        self._popup_personali_win.lift()
        self._popup_personali_win.focus_force()
        return
    parent = self._dare_avere_popup if hasattr(self, '_dare_avere_popup') and self._dare_avere_popup and self._dare_avere_popup.winfo_exists() else self
    popup = tk.Toplevel(parent, bg=self.COLOR_TOPLEVEL)
    self._popup_personali_win = popup
    popup.title("Dettaglio Movimenti Personali CTP·")
    popup.withdraw()
    self.update_idletasks()
    w, h = 1100, 650
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    popup.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")
    popup.minsize(w, h)
    popup.configure(background=self.COLOR_TOPLEVEL)
    popup.transient(parent)
    popup.deiconify()
    popup.lift()
    popup.focus_force()
    popup.bind("<Escape>", lambda e: popup.destroy())
    top_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    top_f.pack(fill=tk.X, padx=15, pady=15)
    style_cb = "Border.TCombobox"
    mese_nomi = ["Tutti", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio",
                 "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    indips_names = [p["nome"] for p in self.nomi_partecipanti if p.get("tipo") == "personale"]
    indips_display = [f"CTP· {n}" for n in indips_names]
    indips_names_match = sorted(indips_names, key=len, reverse=True)
    anni_disponibili = sorted(set(str(d.year) for d in self.spese.keys()), reverse=True)
    anno_v  = tk.StringVar(value="Tutti")
    mese_v  = tk.StringVar(value="Tutti")
    indip_v = tk.StringVar(value="Tutti")
    cat_v   = tk.StringVar(value="Tutti")
    filtri = [
        ("Anno:",      anno_v,  ["Tutti"] + anni_disponibili,    7),
        ("Mese:",      mese_v,  mese_nomi,                       10),
        ("Utente:",    indip_v, ["Tutti"] + indips_display,      25),
        ("Categoria:", cat_v,   ["Tutti"] + self.categorie,      25),
    ]
    combobox_lista = []
    for lbl_txt, var, vals, cw in filtri:
        tk.Label(top_f, text=lbl_txt, bg=self.COLOR_TOPLEVEL,
                 fg=self.TEXT_COLOR).pack(side=tk.LEFT, padx=(0, 5))
        cb = ttk.Combobox(top_f, textvariable=var, values=vals,
                          width=cw, state="readonly", style=style_cb)
        cb.pack(side=tk.LEFT, padx=(0, 15))
        combobox_lista.append(cb)
    tree_frame = ttk.Frame(popup)
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
    cols = ("Data", "Partecipante", "Categoria", "Descrizione", "Tipo", "Importo")
    tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
    vsb  = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    col_cfg = {
        "Data":          (100, "center"),
        "Partecipante":  (130, "center"),
        "Categoria":     (130, "center"),
        "Descrizione":   (280, "w"),
        "Tipo":          (80,  "center"),
        "Importo":       (110, "center"),
    }
    for c in cols:
        w_col, anchor = col_cfg[c]
        tree.heading(c, text=c, command=lambda _c=c: self.treeview_sort_column(tree, _c, False))
        tree.column(c, width=w_col, anchor=anchor)
    tree.tag_configure("pos", foreground="#98C379")
    tree.tag_configure("neg", foreground="#E06C75")
    self._bind_tooltip_metodo(tree, col_desc=3)
    def _vai_a_spesa_ctp(event):
        iid = tree.identify_row(event.y)
        info = getattr(tree, "_metodo_lookup", {}).get(iid)
        if not info:
            return
        try:
            d = datetime.datetime.strptime(info.get("data", ""), "%d-%m-%Y").date()
        except ValueError:
            return
        self.vai_a_spesa(d, popup, str(tree.item(iid, "values")[3])[:20], info.get("id_spesa", ""))
    tree.bind("<Double-1>", _vai_a_spesa_ctp)
    summary_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL,
                         highlightbackground=self.COLOR_WIDGET_BG, highlightthickness=1)
    summary_f.pack(fill=tk.X, padx=15, pady=5)
    lbl_ent_val = tk.Label(summary_f, text="0,00 €", font=("Arial", 11, "bold"),
                           bg=self.COLOR_TOPLEVEL, fg="#98C379")
    lbl_usc_val = tk.Label(summary_f, text="0,00 €", font=("Arial", 11, "bold"),
                           bg=self.COLOR_TOPLEVEL, fg="#E06C75")
    lbl_sal_val = tk.Label(summary_f, text="0,00 €", font=("Arial", 11, "bold"),
                           bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR)
    for etichetta, widget in [("Entrate:", lbl_ent_val),
                               ("Uscite:",  lbl_usc_val),
                               ("Saldo:",   lbl_sal_val)]:
        tk.Label(summary_f, text=etichetta, bg=self.COLOR_TOPLEVEL,
                 fg=self.TEXT_COLOR, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(10, 2))
        widget.pack(side=tk.LEFT, padx=(0, 20))
    def ricarica(*_):
        tree.delete(*tree.get_children())
        tree._metodo_lookup = {}
        idx_m = mese_nomi.index(mese_v.get())
        t_ent = t_usc = 0.0
        for data, voci in self.spese.items():
            if anno_v.get() != "Tutti" and str(data.year) != anno_v.get():
                continue
            if idx_m > 0 and data.month != idx_m:
                continue
            for v in voci:
                categoria   = campo(v, "categoria", "") or "Varie"
                descrizione = campo(v, "descrizione", "")
                imp = campo(v, "importo", None)
                if imp is None:
                    continue
                imp = float(imp)
                tipo = campo(v, "tipo", "")
                nome_ind = next((n for n in indips_names_match if f"CTP·{n}" in descrizione), None)
                if not nome_ind:
                    continue
                sel_ind = indip_v.get()
                if sel_ind != "Tutti":
                    sel_ind_puro = sel_ind.replace("CTP· ", "").strip()
                    if sel_ind_puro != nome_ind:
                        continue
                if cat_v.get() != "Tutti" and cat_v.get() != categoria:
                    continue
                tag = "pos" if tipo == "Entrata" else "neg"
                _iid_c = tree.insert("", "end",
                            values=(data.strftime("%d/%m/%Y"),
                                    f"CTP· {nome_ind}",
                                    categoria,
                                    descrizione,
                                    tipo,
                                    f"{_fmt_it(imp)} €"),
                            tags=(tag,))
                tree._metodo_lookup[_iid_c] = {
                    "metodo": campo(v, "metodo_pagamento", ""),
                    "conto": campo(v, "conto", ""),
                    "ora": campo(v, "ora", ""),
                    "hashtag": campo(v, "hashtag", []),
                    "id_ricorrenza": campo(v, "id_ricorrenza", ""),
                    "data": data.strftime("%d-%m-%Y"),
                    "categoria": categoria,
                    "importo": imp,
                    "tipo": tipo,
                    "id_spesa": campo(v, "id_spesa", ""),
                }
                if tipo == "Entrata":
                    t_ent += imp
                else:
                    t_usc += imp
        saldo = t_ent - t_usc
        lbl_ent_val.config(text=f"{_fmt_it(t_ent)} €")
        lbl_usc_val.config(text=f"{_fmt_it(t_usc)} €")
        lbl_sal_val.config(text=f"{_fmt_it(saldo)} €",
                           fg="#98C379" if saldo >= 0 else "#E06C75")
    for cb in combobox_lista:
        cb.bind("<<ComboboxSelected>>", ricarica)
    def anteprima_export():
        if hasattr(anteprima_export, '_win') and anteprima_export._win and anteprima_export._win.winfo_exists():
            anteprima_export._win.lift()
            anteprima_export._win.focus_force()
            return
        anno_sel = anno_v.get()
        mese_sel = mese_v.get()
        sep      = "─" * 110 + "\n"
        header   = (f"{'Data':<12} | {'Utente':<15} | {'Categoria':<18} | "
                    f"{'Descrizione':<25} | {'Tipo':<8} | {'Importo':>12}\n")
        contenuto = f"ESTRATTO MOVIMENTI PERSONALI - {mese_sel} {anno_sel}\n{sep}{header}{sep}"
        for item in tree.get_children():
            v = tree.item(item, "values")
            utente = v[1].replace("CTP· ", "")[:15]
            contenuto += (f"{v[0]:<12} | {utente:<15} | {v[2]:<18} | "
                          f"{v[3][:24]:<25} | {v[4]:<8} | {v[5]:>12}\n")
        contenuto += (f"{sep}"
                      f"Entrate: {lbl_ent_val.cget('text'):>12} | "
                      f"Uscite: {lbl_usc_val.cget('text'):>12} | "
                      f"Saldo: {lbl_sal_val.cget('text'):>12}\n")
        prev_win = tk.Toplevel(popup)
        anteprima_export._win = prev_win
        prev_win.title("Esportazione Personali")
        prev_win.bind("<Escape>", lambda e: prev_win.destroy())
        prev_win.bind("<Destroy>", lambda e: setattr(anteprima_export, '_win', None) if e.widget is prev_win else None)
        prev_win.withdraw()
        prev_win.update_idletasks()
        w, h = 1000, 550
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
        prev_win.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")
        prev_win.minsize(w, h)
        prev_win.configure(background=self.COLOR_TOPLEVEL)
        prev_win.transient(popup)
        prev_win.deiconify()
        prev_win.lift()
        prev_win.focus_force()
        txt_frame = tk.Frame(prev_win, bg=self.COLOR_TOPLEVEL)
        txt_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        v_scroll = ttk.Scrollbar(txt_frame, orient="vertical")
        h_scroll = ttk.Scrollbar(txt_frame, orient="horizontal")
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        txt = tk.Text(txt_frame, font=("Courier New", 10),
                      bg=self.COLOR_WHITE, fg=self.COLOR_BLACK,
                      wrap="none",
                      yscrollcommand=v_scroll.set,
                      xscrollcommand=h_scroll.set)
        txt.pack(fill=tk.BOTH, expand=True)
        v_scroll.config(command=txt.yview)
        h_scroll.config(command=txt.xview)
        txt.insert("1.0", contenuto)
        txt.config(state="disabled")
        btn_f = tk.Frame(prev_win, bg=self.COLOR_TOPLEVEL)
        btn_f.pack(fill=tk.X, pady=10)
        def salva_pdf():
            f = filedialog.asksaveasfilename(
                initialdir=_app.EXPORT_FILES,
                confirmoverwrite=False,
                defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
                initialfile=f"Personali_{mese_sel}_{anno_sel}.pdf", parent=prev_win)
            if f:
                try:
                    import pymupdf as fitz
                    doc  = fitz.open()
                    page = doc.new_page(width=842, height=595)
                    page.insert_text((40, 40), contenuto, fontname="cour", fontsize=10)
                    doc.save(f); doc.close()
                    self.show_toast("PDF salvato.")
                except Exception as e:
                    self.show_custom_warning("Errore", str(e))
        def salva_txt():
            f = filedialog.asksaveasfilename(
                initialdir=_app.EXPORT_FILES,
                confirmoverwrite=False,
                defaultextension=".txt", filetypes=[("TXT", "*.txt")],
                initialfile=f"Personali_{mese_sel}_{anno_sel}.txt", parent=prev_win)
            if f:
                with open(f, "w", encoding="utf-8") as fh:
                    fh.write(contenuto)
                self.show_toast("TXT salvato.")
        for testo, ico, cmd, side in [
            (" Chiudi", "chiudi", prev_win.destroy, tk.RIGHT),
            (" PDF",    "salva",  salva_pdf,        tk.LEFT),
            (" TXT",    "salva",  salva_txt,        tk.LEFT),
            (" Stampa", "stampa", lambda: self._stampa_lista_diretta(contenuto, self.show_custom_warning), tk.LEFT),
        ]:
            b = ttk.Label(btn_f, compound="left", image=self.icone_gui.get(ico),
                          text=testo, background=self.COLOR_WIDGET_BG,
                          foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
            b.pack(side=side, padx=5)
            b.bind("<Button-1>", lambda e, c=cmd: c())
    bot_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    bot_f.pack(fill=tk.X, side=tk.BOTTOM, pady=15)
    for testo, ico, cmd, side in [
        ("  Esporta ", "salva",  anteprima_export, tk.LEFT),
        ("  Grafico ", "salva",  self.popup_grafico_categorie_personali, tk.LEFT),
        ("  Chiudi ",  "chiudi", popup.destroy,    tk.RIGHT),
    ]:
        b = tk.Label(bot_f, image=self.icone_gui.get(ico), text=testo,
                     compound="left", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                     cursor="hand2", font=("Arial", 10, "bold"))
        b.pack(side=side, padx=20)
        b.bind("<Button-1>", lambda e, c=cmd: c())
    ricarica()
def popup_grafico_categorie_personali(self):
    if hasattr(self, '_grafico_cat_personali_win') and self._grafico_cat_personali_win.winfo_exists():
        self._grafico_cat_personali_win.lift()
        self._grafico_cat_personali_win.focus_force()
        return
    popup = tk.Toplevel(self)
    self._grafico_cat_personali_win = popup 
    popup.title("Grafico Movimenti Personali per Categoria")
    popup.withdraw()
    self.update_idletasks()
    w, h = 1200, 650
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    popup.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")
    popup.minsize(w, h)
    popup.configure(bg=self.COLOR_TOPLEVEL)
    popup.attributes("-topmost", True)
    popup.resizable(True, True)
    popup.deiconify()
    popup.update_idletasks()
    popup.attributes("-topmost", False)
    popup.bind("<Escape>", lambda e: popup.destroy())
    MESI_NOMI = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                 "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    PALETTE = [
        "#61AFEF", "#E06C75", "#98C379", "#E5C07B", "#C678DD",
        "#56B6C2", "#FF9F43", "#A29BFE", "#FD79A8", "#6BCB77",
        "#F8961E", "#4D908E", "#F3722C", "#90BE6D", "#277DA1",
        "#D4AC0D", "#EB5757", "#48CAE4", "#B5838D", "#52B788",
    ]
    indips_names = [p["nome"] for p in self.nomi_partecipanti if p.get("tipo") == "personale"]
    indips_names_match = sorted(indips_names, key=len, reverse=True)
    top_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    top_f.pack(fill=tk.X, padx=15, pady=8)
    anni_disponibili = sorted(set(str(d.year) for d in self.spese.keys()), reverse=True)
    nomi_lista = ["Tutti"] + sorted(indips_names, key=lambda n: n.lower())
    anno_v = tk.StringVar(value="Tutti")
    mese_v = tk.StringVar(value="Tutti")
    tipo_v = tk.StringVar(value="Entrambi")
    nome_v = tk.StringVar(value="Tutti")
    def _lbl(t):
        return tk.Label(top_f, text=t, bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR)
    def _cb(var, vals, cw):
        return ttk.Combobox(top_f, textvariable=var, values=vals,
                            width=cw, state="readonly", style="Border.TCombobox")
    _lbl("Anno:").pack(side=tk.LEFT, padx=(0, 4))
    cb_anno = _cb(anno_v, ["Tutti"] + anni_disponibili, 7)
    cb_anno.pack(side=tk.LEFT, padx=(0, 15))
    _lbl("Mese:").pack(side=tk.LEFT, padx=(0, 4))
    cb_mese = _cb(mese_v, ["Tutti"] + MESI_NOMI, 10)
    cb_mese.pack(side=tk.LEFT, padx=(0, 15))
    _lbl("Tipo:").pack(side=tk.LEFT, padx=(0, 4))
    cb_tipo = _cb(tipo_v, ["Entrambi", "Uscita", "Entrata"], 9)
    cb_tipo.pack(side=tk.LEFT, padx=(0, 15))
    _lbl("Utente:").pack(side=tk.LEFT, padx=(0, 4))
    cb_nome = _cb(nome_v, nomi_lista, 25)
    cb_nome.pack(side=tk.LEFT, padx=(0, 15))
    main_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    main_f.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
    LEG_W = 200
    leg_outer = tk.Frame(main_f, bg=self.COLOR_TOPLEVEL, width=LEG_W)
    leg_outer.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))
    leg_outer.pack_propagate(False)
    leg_head = tk.Frame(leg_outer, bg=self.COLOR_TOPLEVEL)
    leg_head.pack(fill=tk.X, pady=(0, 4))
    tk.Label(leg_head, text="Categoria", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 8, "bold"), width=25, anchor="w").pack(side=tk.LEFT)
    tk.Label(leg_head, text="Saldo", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 8, "bold"), width=10, anchor="e").pack(side=tk.RIGHT)
    tk.Frame(leg_outer, bg=self.TEXT_COLOR, height=1).pack(fill=tk.X, pady=(0, 4))
    leg_cv = tk.Canvas(leg_outer, bg=self.COLOR_TOPLEVEL, highlightthickness=0)
    leg_sb = ttk.Scrollbar(leg_outer, orient="vertical", command=leg_cv.yview)
    leg_cv.configure(yscrollcommand=leg_sb.set)
    leg_sb.pack(side=tk.RIGHT, fill=tk.Y)
    leg_cv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    leg_inner = tk.Frame(leg_cv, bg=self.COLOR_TOPLEVEL)
    leg_cv.create_window((0, 0), window=leg_inner, anchor="nw")
    leg_inner.bind("<Configure>", lambda e: leg_cv.configure(scrollregion=leg_cv.bbox("all")))
    chart_f = tk.Frame(main_f, bg=self.COLOR_TOPLEVEL)
    chart_f.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    h_scroll = ttk.Scrollbar(chart_f, orient="horizontal")
    h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
    canvas = tk.Canvas(chart_f, bg=self.COLOR_WIDGET_BG,
                       highlightthickness=0, xscrollcommand=h_scroll.set)
    canvas.pack(fill=tk.BOTH, expand=True)
    h_scroll.config(command=canvas.xview)
    canvas.bind("<MouseWheel>", lambda e: canvas.xview_scroll(int(-1*(e.delta/120)), "units"))
    tot_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL,
                     highlightbackground=self.COLOR_WIDGET_BG, highlightthickness=1)
    tot_f.pack(fill=tk.X, padx=15, pady=(0, 4))
    riga_tot = tk.Frame(tot_f, bg=self.COLOR_TOPLEVEL)
    riga_tot.pack(fill=tk.X)

    lbl_ent_val = tk.Label(riga_tot, text="0,00 €", font=("Arial", 11, "bold"),
                           bg=self.COLOR_TOPLEVEL, fg="#98C379")
    lbl_usc_val = tk.Label(riga_tot, text="0,00 €", font=("Arial", 11, "bold"),
                           bg=self.COLOR_TOPLEVEL, fg="#E06C75")
    lbl_sal_val = tk.Label(riga_tot, text="0,00 €", font=("Arial", 11, "bold"),
                           bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR)
    for etichetta, widget in [("Entrate:", lbl_ent_val),
                               ("Uscite:",  lbl_usc_val),
                               ("Saldo:",   lbl_sal_val)]:
        tk.Label(riga_tot, text=etichetta, bg=self.COLOR_TOPLEVEL,
                 fg=self.TEXT_COLOR, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(10, 2))
        widget.pack(side=tk.LEFT, padx=(0, 20))
    lbl_dettaglio_utenti = tk.Label(tot_f, text="", font=("Arial", 8),
                                    bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                                    wraplength=900, justify="left")
    lbl_dettaglio_utenti.pack(fill=tk.X, padx=10, pady=(0, 3))
    bot_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    bot_f.pack(fill=tk.X, side=tk.BOTTOM, pady=8)
    b = tk.Label(bot_f, image=self.icone_gui.get("chiudi"), text="  Chiudi ",
                 compound="left", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                 cursor="hand2", font=("Arial", 10, "bold"))
    b.pack(side=tk.RIGHT, padx=20)
    b.bind("<Button-1>", lambda e: popup.destroy())
    tooltip_lbl = tk.Label(popup, text="", bg=self.COLOR_TOOLTIP, fg=self.COLOR_TEXT_TOOLTIP,
                           font=("Arial", 9), padx=6, pady=3,
                           highlightthickness=1, highlightbackground=self.COLOR_HIGHLIGHT)
    def show_tip(event, testo):
        tooltip_lbl.config(text=testo)
        tooltip_lbl.update_idletasks()
        tw = tooltip_lbl.winfo_reqwidth()
        th = tooltip_lbl.winfo_reqheight()
        pw, ph = popup.winfo_width(), popup.winfo_height()
        x = event.x_root - popup.winfo_rootx() + 14
        y = event.y_root - popup.winfo_rooty() - 34
        if x + tw > pw:
            x = pw - tw
        if x < 0:
            x = 0
        if y + th > ph:
            y = ph - th
        if y < 0:
            y = 0
        tooltip_lbl.place(x=x, y=y)
    def hide_tip(_):
        tooltip_lbl.place_forget()
    _pronto = [False]
    _disegnando = [False]
    def _disegna_impl():
        canvas.delete("all")
        for widget in leg_inner.winfo_children():
            widget.destroy()
        anno_sel = anno_v.get()
        mese_sel = mese_v.get()
        tipo_sel = tipo_v.get()
        nome_sel = nome_v.get()
        idx_mese = MESI_NOMI.index(mese_sel) + 1 if mese_sel != "Tutti" else 0
        dati_graf = {}
        saldi_cat = {}
        totali_utenti = {n: {"ent": 0.0, "usc": 0.0} for n in indips_names}
        t_ent = t_usc = 0.0
        for data, voci in self.spese.items():
            if anno_sel != "Tutti" and str(data.year) != anno_sel:
                continue
            if idx_mese > 0 and data.month != idx_mese:
                continue
            chiave = (data.year, data.month)
            for v in voci:
                cat  = campo(v, "categoria", "") or "Varie"
                desc = campo(v, "descrizione", "")
                imp = campo(v, "importo", None)
                if imp is None:
                    continue
                imp = float(imp)
                tipo = campo(v, "tipo", "")
                nome_trovato = next((n for n in indips_names_match
                                     if f"CTP·{n}" in desc), None)
                if not nome_trovato:
                    continue
                if nome_sel != "Tutti" and nome_sel != nome_trovato:
                    continue
                if tipo_sel != "Entrambi" and tipo != tipo_sel:
                    continue
                if cat not in saldi_cat:
                    saldi_cat[cat] = {"ent": 0.0, "usc": 0.0}
                if tipo == "Entrata":
                    saldi_cat[cat]["ent"] += imp
                    t_ent += imp
                    totali_utenti[nome_trovato]["ent"] += imp
                else:
                    saldi_cat[cat]["usc"] += imp
                    t_usc += imp
                    totali_utenti[nome_trovato]["usc"] += imp
                if chiave not in dati_graf:
                    dati_graf[chiave] = {}
                if nome_trovato not in dati_graf[chiave]:
                    dati_graf[chiave][nome_trovato] = {}
                if cat not in dati_graf[chiave][nome_trovato]:
                    dati_graf[chiave][nome_trovato][cat] = {"ent": 0.0, "usc": 0.0}
                if tipo == "Entrata":
                    dati_graf[chiave][nome_trovato][cat]["ent"] += imp
                else:
                    dati_graf[chiave][nome_trovato][cat]["usc"] += imp
        saldo_tot = t_ent - t_usc
        lbl_ent_val.config(text=f"{_fmt_it(t_ent)} €")
        lbl_usc_val.config(text=f"{_fmt_it(t_usc)} €")
        lbl_sal_val.config(text=f"{_fmt_it(saldo_tot)} €",
                           fg="#98C379" if saldo_tot >= 0 else "#E06C75")
        if nome_sel == "Tutti" and len(indips_names) > 1:
            parti = []
            for n in sorted(indips_names):
                e = totali_utenti[n]["ent"]
                u = totali_utenti[n]["usc"]
                s = e - u
                segno = "+" if s >= 0 else ""
                parti.append(f"{n}: {segno}{_fmt_it(s)}€")
            lbl_dettaglio_utenti.config(text="  |  ".join(parti))
        else:
            lbl_dettaglio_utenti.config(text="")
        if not dati_graf or not any(dati_graf.values()):
            canvas.create_text(300, 150, text="Nessun dato disponibile",
                               fill=self.TEXT_COLOR, font=("Arial", 14))
            return
        mesi_ordinati   = sorted(dati_graf.keys())
        categorie_usate = set(cat for m in dati_graf.values()
                                  for utente in m.values()
                                  for cat in utente)
        categorie_lista = sorted(categorie_usate, key=lambda c: c.lower())
        n_cat  = len(categorie_lista)
        n_mesi = len(mesi_ordinati)
        utenti_lista = sorted({nu for m in dati_graf.values() for nu in m}, key=lambda n: n.lower())
        pos_ut = {nu: i for i, nu in enumerate(utenti_lista)}
        n_ut   = max(len(utenti_lista), 1)
        colori = {cat: PALETTE[i % len(PALETTE)] for i, cat in enumerate(
            sorted(saldi_cat.keys(), key=lambda c: c.lower())
        )}
        popup.update_idletasks()
        CW      = max(canvas.winfo_width(), 500)
        CH      = max(canvas.winfo_height(), 300)
        PAD_L   = 75
        PAD_R   = 15
        PAD_T   = 20
        PAD_B   = 52
        CHART_H = CH - PAD_T - PAD_B
        base_y  = PAD_T + CHART_H
        bar_w   = 14
        bar_gap = 3
        group_w = max(n_cat * n_ut * (bar_w + bar_gap) + 20, 80)
        total_w = PAD_L + n_mesi * group_w + PAD_R
        canvas.config(scrollregion=(0, 0, max(total_w, CW), CH))
        max_val = max(
            (d["ent"] + d["usc"] for mese in dati_graf.values()
                  for utente in mese.values()
                  for d in utente.values()), default=1
        ) or 1
        def val_to_y(v):
            return PAD_T + CHART_H - int((v / max_val) * CHART_H)
        for i in range(6):
            val = max_val * i / 5
            y   = val_to_y(val)
            canvas.create_line(PAD_L, y, total_w - PAD_R, y,
                               fill="#3a3a3a", dash=(3, 4))
            canvas.create_text(PAD_L - 5, y, text=f"{_fmt_it(val, ',.0f')}€",
                               anchor="e", fill=self.TEXT_COLOR, font=("Arial", 8))
        canvas.create_line(PAD_L, base_y, total_w - PAD_R, base_y,
                           fill=self.TEXT_COLOR, width=1)
        for mi, mese_key in enumerate(mesi_ordinati):
            anno_m, mese_m = mese_key
            x_group  = PAD_L + mi * group_w
            centro_x = x_group + (n_cat * n_ut * (bar_w + bar_gap)) // 2
            label_m  = f"{MESI_NOMI[mese_m-1]}\n{anno_m}" if anno_sel == "Tutti" else MESI_NOMI[mese_m-1]
            canvas.create_text(centro_x, base_y + 6, text=label_m,
                               anchor="n", fill=self.TEXT_COLOR, font=("Arial", 8))
            for ci, cat in enumerate(categorie_lista):
                for nome_u, cat_dict in dati_graf[mese_key].items():
                    d = cat_dict.get(cat, None)
                    if not d:
                        continue
                    val = d["ent"] + d["usc"]
                    if val == 0:
                        continue
                    x0    = x_group + (ci * n_ut + pos_ut[nome_u]) * (bar_w + bar_gap)
                    x1    = x0 + bar_w
                    y0    = val_to_y(val)
                    barra = canvas.create_rectangle(x0, y0, x1, base_y,
                                                    fill=colori[cat], outline="",
                                                    tags="barra")
                    tip = (f"CTP· {nome_u}  |  {cat}  ({MESI_NOMI[mese_m-1]} {anno_m})\n"
                           f"Entrate: {_fmt_it(d['ent'])}€   Uscite: {_fmt_it(d['usc'])}€")
                    canvas.tag_bind(barra, "<Enter>", lambda e, t=tip: show_tip(e, t))
                    canvas.tag_bind(barra, "<Leave>", hide_tip)
        for cat in sorted(saldi_cat.keys(), key=lambda c: c.lower()):
            ent    = saldi_cat[cat]["ent"]
            usc    = saldi_cat[cat]["usc"]
            sal    = ent - usc
            fg_sal = "#98C379" if sal >= 0 else "#E06C75"
            f_row  = tk.Frame(leg_inner, bg=self.COLOR_TOPLEVEL)
            f_row.pack(fill=tk.X, pady=1)
            tk.Canvas(f_row, width=11, height=11,
                      bg=colori.get(cat, "#888"),
                      highlightthickness=0).pack(side=tk.LEFT, padx=(0, 4))
            tk.Label(f_row, text=cat, bg=self.COLOR_TOPLEVEL,
                     fg=self.TEXT_COLOR, font=("Arial", 8),
                     anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)
            tk.Label(f_row, text=f"{_fmt_it(sal, ',.0f')}€", bg=self.COLOR_TOPLEVEL,
                     fg=fg_sal, font=("Arial", 8, "bold"),
                     anchor="e").pack(side=tk.RIGHT, padx=(0, 4))
    def disegna(*_):
        if not _pronto[0] or _disegnando[0]:
            return
        _disegnando[0] = True
        try:
            if popup.winfo_exists():
                _disegna_impl()
        except tk.TclError:
            pass
        finally:
            _disegnando[0] = False
    canvas.bind("<Configure>", disegna)
    for cb in [cb_anno, cb_mese, cb_tipo, cb_nome]:
        cb.bind("<<ComboboxSelected>>", disegna)
    def _avvia():
        _pronto[0] = True
        disegna()
    _avvia_id = popup.after(150, _avvia)
    def _annulla_avvia(e):
        if e.widget is popup:
            try:
                popup.after_cancel(_avvia_id)
            except Exception:
                pass
    popup.bind("<Destroy>", _annulla_avvia)

def mostra_guida_dare_avere(self, popup=None):
    if hasattr(self, '_guida_popup') and self._guida_popup and self._guida_popup.winfo_exists():
        self._guida_popup.lift(); self._guida_popup.focus_force(); return
    guida_win = tk.Toplevel(popup, bg=self.COLOR_TOPLEVEL)
    self._guida_popup = guida_win
    guida_win.withdraw()
    guida_win.title("Guida FairShare — Dare & Avere per Spesa")
    guida_win.resizable(True, True)
    guida_win.bind("<Escape>", lambda e: guida_win.destroy())
    guida_win.bind("<Destroy>", lambda e: setattr(self, '_guida_popup', None) if e.widget is guida_win else None)
    guida_win.transient(popup)
    NOME_GESTORE = _nome_gestore()
    testo_guida = (
        "1. LOGICA DI BASE\n"
        "   La quota di ogni Persona = totale uscite (incluse quelle dei Gruppi) / numero Persone.\n"
        "   Il Gestore (" + NOME_GESTORE + ") partecipa come qualsiasi altra Persona\n"
        "   se abilitato in 'Gestisci Partecipanti'.\n\n"
        "2. TIPI DI PARTECIPANTE\n"
        "   PER· Persona    → Partecipa alla divisione delle spese comuni.\n"
        "   CNT· Gruppo     → Fondo comune (es. Casa). Le spese vengono divise tra i soci.\n"
        "                   Non paga quota propria.\n"
        "   CTP· Personale  → Spese e entrate solo sue (stipendio, spese private).\n"
        "                   Non partecipa alla divisione.\n\n"
        "3. COME REGISTRARE UNA SPESA\n"
        "   - Seleziona il partecipante dalla combobox PER·/CNT·:\n"
        "     il prefisso icona+Nome viene aggiunto in automatico alla descrizione.\n"
        "   - USCITA  → spesa pagata da quel partecipante (chi ha anticipato i soldi).\n"
        "   - ENTRATA → rimborso ricevuto (chi restituisce la quota).\n"
        "     L'entrata deve avere la STESSA CATEGORIA della spesa originale.\n"
        "4. SEGNARE UN PAGAMENTO\n"
        "   AUTOMATICO: se registri un'entrata con tag PER·Nome e stessa categoria\n"
        "   della spesa originale, il sistema segna il pagamento automaticamente.\n\n"
        "   MANUALE: doppio click sulla riga nella vista Dare & Avere.\n"
        "   - Primo doppio click  → segna PAGATO (con data odierna)\n"
        "   - Secondo doppio click → ANNULLA il pagamento\n"
        "   Sia il pagamento sia il suo annullamento manuale restano fissi:\n"
        "   il sync automatico non li modifica piu'.\n\n"
        "   Quando TUTTI i partecipanti hanno pagato, lo stato diventa Chiuso.\n\n"
        "5. CALCOLO DEL SALDO FAIRSHARE\n"
        "   Saldo = (Uscite pagate + Entrate ricevute) − Quota pro capite\n"
        "   La quota include anche la divisione delle spese dei Gruppi di cui si è soci.\n"
        "   Positivo → deve RICEVERE dagli altri.\n"
        "   Negativo → deve VERSARE agli altri.\n"
        "   Zero     → pari.\n\n"
        "6. GRUPPI CNT·\n"
        "   Crea un Gruppo in 'Gestisci Partecipanti' e seleziona i soci.\n"
        "   Le spese taggate CNT·NomeGruppo vengono divise automaticamente tra i soci.\n"
        "   Il Gestore può essere incluso tra i soci di un Gruppo.\n\n"
        "7. MOVIMENTI PERSONALI CTP·\n"
        "   Accessibili da 'Personali' nel pannello FairShare.\n"
        "   Filtrabili per anno, mese, utente e categoria.\n\n"
        "8. RICORRENZE\n"
        "   Le spese ricorrenti vengono generate automaticamente alla data prevista.\n"
        "   Ogni ricorrenza può avere partecipante, categoria e metodo di pagamento.\n"
        "   Gestibili dal pannello Ricorrenze nel form principale.\n\n"
        "9. GRAFICI\n"
        "   Tab 1 → Dovuto vs Versato per persona.\n"
        "   Tab 2 → Quote ancora da versare (Aperto) vs già versate (Chiuso) per categoria.\n"
        "   Tab 3 → Andamento mensile dovuto/versato.\n"
        "   Filtrabili per anno, mese, persona e categoria.\n"
        "   Hover sul grafico → tooltip con i valori.\n\n"
        "10. ESPORTAZIONE\n"
        "    Esporta → anteprima con salvataggio PDF o TXT.\n"
        "    Analitico → estratto completo per partecipante e periodo.\n"
        "    Entrambi includono il riepilogo 'Chi deve a chi', compensato\n"
        "    (se A deve a B e B deve ad A, resta solo la differenza).\n"
        "    Con 'Tutti' e percentuali fisse la colonna Quota mostra '—':\n"
        "    la quota dipende dalla persona, filtra per partecipante per vederla.\n"
    )
    def centra_guida():
        if not guida_win.winfo_exists():
            return
        w_g, h_g = 960, 700
        if popup:
            x = popup.winfo_rootx() + (popup.winfo_width() // 2) - (w_g // 2)
            y = popup.winfo_rooty() + (popup.winfo_height() // 2) - (h_g // 2)
        else:
            x = (guida_win.winfo_screenwidth() // 2) - (w_g // 2)
            y = (guida_win.winfo_screenheight() // 2) - (h_g // 2)
        guida_win.geometry(f"{w_g}x{h_g}+{max(0, x)}+{max(0, y)}")
        guida_win.deiconify()
        guida_win.focus_force()
    guida_win.after(0, centra_guida)
    txt_frame = tk.Frame(guida_win, bg=self.COLOR_HIGHLIGHT, padx=2, pady=2)
    txt_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    vsb = ttk.Scrollbar(txt_frame, orient="vertical", style="Vertical.TScrollbar")
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    st_guida = tk.Text(txt_frame, font=("Courier New", 10),
                       bg=self.COLOR_WHITE, fg=self.COLOR_BLACK,
                       padx=15, pady=15, relief="flat", borderwidth=0,
                       wrap="word", yscrollcommand=vsb.set)
    st_guida.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    vsb.config(command=st_guida.yview)
    st_guida.insert("1.0", testo_guida)
    st_guida.config(state="disabled")
    btn_frame_g = tk.Frame(guida_win, bg=self.COLOR_TOPLEVEL)
    btn_frame_g.pack(fill=tk.X, pady=(0, 10))
    img_p = self.icone_gui.get("stampa")
    btn_p = ttk.Label(btn_frame_g, compound="left", image=img_p,
                      text=" Stampa" if img_p else "Stampa",
                      background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                      cursor="hand2", padding=(10, 5))
    btn_p.pack(side=tk.LEFT, padx=15)
    btn_p.bind("<Button-1>", lambda e: self._stampa_lista_diretta(testo_guida, self.show_custom_warning))
    img_ok = self.icone_gui.get("chiudi")
    btn_ok = ttk.Label(btn_frame_g, compound="left", image=img_ok,
                       text=" Ho Capito" if img_ok else "Ho Capito",
                       background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                       cursor="hand2", padding=(10, 5))
    btn_ok.pack(side=tk.RIGHT, padx=15)
    btn_ok.bind("<Button-1>", lambda e: guida_win.destroy())

def get_fairshare_data_json(self, anno_sel, mese_sel, utente_sel):
    mese_num = int(mese_sel) if mese_sel and mese_sel != "0" else 0
    debiti   = self.carica_fairshare_state()
    personali = [p for p in self.nomi_partecipanti if p.get("tipo") == "personale"]
    debiti_filtrati = []
    for deb in debiti:
        ds = deb.get("data", "")
        try:
            d_obj = datetime.datetime.strptime(ds, "%d/%m/%Y").date()
        except Exception:
            continue
        if anno_sel and anno_sel != "0" and str(d_obj.year) != anno_sel:
            continue
        if mese_num > 0 and d_obj.month != mese_num:
            continue
        debiti_filtrati.append(deb)
    tot_dovuto  = {}
    tot_versato = {}
    chi_deve    = {}
    for deb in debiti_filtrati:
        creditore = deb.get("creditore", "")
        pag       = deb.get("pagamenti", {})
        for nome in deb.get("partecipanti", []):
            quota = _quota_persona(deb, nome)
            tot_dovuto.setdefault(nome, 0.0)
            tot_versato.setdefault(nome, 0.0)
            tot_dovuto[nome] += quota
            if pag.get(nome, {}).get("pagato", False):
                tot_versato[nome] += quota
            else:
                if creditore and creditore != nome:
                    chiave = (nome, creditore)
                    chi_deve.setdefault(chiave, 0.0)
                    chi_deve[chiave] += quota
    persone_list = []
    for nome in sorted(tot_dovuto.keys()):
        dov = tot_dovuto[nome]
        ver = tot_versato.get(nome, 0.0)
        res = round(dov - ver, 2)
        persone_list.append({
            "nome":    nome,
            "dovuto":  round(dov, 2),
            "versato": round(ver, 2),
            "residuo": res,
        })
    chi_deve = _compensa_debiti(chi_deve)
    chi_deve_list = [
        {"da": d, "a": c, "importo": round(v, 2)}
        for (d, c), v in sorted(chi_deve.items(), key=lambda x: (x[0][1], x[0][0]))
    ]
    indips      = [p["nome"] for p in personali]
    indips_match = sorted(indips, key=len, reverse=True)
    saldi_cat_p = {n: {} for n in indips}
    totali_p    = {n: {"ent": 0.0, "usc": 0.0} for n in indips}
    for data, voci in self.spese.items():
        if anno_sel and anno_sel != "0" and str(data.year) != anno_sel:
            continue
        if mese_num > 0 and data.month != mese_num:
            continue
        for voce in voci:
            try:
                cat  = campo(voce, "categoria", "")
                imp  = float(campo(voce, "importo", 0.0))
                tipo = campo(voce, "tipo", "")
                desc_str = campo(voce, "descrizione", "")
            except Exception:
                continue
            nome_trovato = next(
                (n for n in indips_match if f"CTP·{n}" in desc_str), None
            )
            if not nome_trovato:
                continue
            if utente_sel and utente_sel != "tutti" and utente_sel != nome_trovato:
                continue
            saldi_cat_p[nome_trovato].setdefault(cat, {"ent": 0.0, "usc": 0.0})
            if tipo == "Entrata":
                saldi_cat_p[nome_trovato][cat]["ent"] += imp
                totali_p[nome_trovato]["ent"]          += imp
            else:
                saldi_cat_p[nome_trovato][cat]["usc"] += imp
                totali_p[nome_trovato]["usc"]          += imp
    personali_data = []
    for nome in indips:
        cats = [
            {"cat": cat, "ent": round(v["ent"], 2), "usc": round(v["usc"], 2)}
            for cat, v in saldi_cat_p[nome].items()
        ]
        cats.sort(key=lambda x: x["usc"] + x["ent"], reverse=True)
        personali_data.append({
            "nome":      nome,
            "tot_ent":   round(totali_p[nome]["ent"], 2),
            "tot_usc":   round(totali_p[nome]["usc"], 2),
            "categorie": cats
        })
    anni_disponibili = sorted(set(str(d.year) for d in self.spese.keys()), reverse=True)
    tot_dovuto_all  = round(sum(tot_dovuto.values()), 2)
    tot_residuo_all = round(sum(tot_dovuto.values()) - sum(tot_versato.values()), 2)
    return json.dumps({
        "persone":          persone_list,
        "chi_deve":         chi_deve_list,
        "personali":        personali_data,
        "anni":             anni_disponibili,
        "utenti_personali": indips,
        "tot_dovuto":       tot_dovuto_all,
        "tot_residuo":      tot_residuo_all,
    })

