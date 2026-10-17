#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#Versamenti automatici sul conto risparmio.

import datetime
import json
import os

import __main__ as _app

from moduli.modello_spesa import SpesaEntry, campo

NESSUNO = "(nessuno)"

def _carica_portafoglio():
    with open(_app.PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as f:
        return json.load(f)

def _conti_risparmio_cat(self):
    if not hasattr(self, "categorie_conti_risparmio"):
        self.categorie_conti_risparmio = dict(getattr(self, "db", {}).get("categorie_conti_risparmio", {}))
    return self.categorie_conti_risparmio

def _mappa_conti_risparmio_auto(self):
    try:
        st = os.stat(_app.PORTAFOGLIO_BANCARIO)
        firma = (st.st_mtime, st.st_size)
    except OSError:
        return {}
    cache = getattr(self, "_cache_conti_risp_auto", None)
    if cache and cache[0] == firma:
        return cache[1]
    mappa = {}
    try:
        db = _carica_portafoglio()
        id_a_nome = {c.get("id"): c.get("nome", "") for c in db.get("conti", [])}
        for t in db.get("trasferimenti", []):
            if t.get("auto_risparmio") and t.get("id_spesa"):
                mappa[t["id_spesa"]] = id_a_nome.get(t.get("da"), "")
    except Exception:
        return {}
    self._cache_conti_risp_auto = (firma, mappa)
    return mappa


def _conto_effettivo(self, entry):
    conto = campo(entry, "conto", "")
    if conto:
        return conto
    idsp = campo(entry, "id_spesa", "")
    return self._mappa_conti_risparmio_auto().get(idsp, "") if idsp else ""


def _nomi_conti_portafoglio(self, solo_risparmio=False, includi=None):
    try:
        conti = _carica_portafoglio().get("conti", [])
        nomi = [c.get("nome", "?") for c in conti]
        if solo_risparmio:
            ris = [c.get("nome", "?") for c in conti if c.get("tipo") == "risparmio"]
            if ris:
                nomi = ris
                if includi and includi in [c.get("nome", "?") for c in conti] and includi not in nomi:
                    nomi.append(includi)
        return nomi
    except Exception:
        return []

def _nome_conto_risparmio_cat(self, categoria):
    cid = self._conti_risparmio_cat().get(categoria)
    if not cid:
        return NESSUNO
    try:
        for c in _carica_portafoglio().get("conti", []):
            if c.get("id") == cid:
                return c.get("nome", NESSUNO)
    except Exception:
        pass
    return NESSUNO

def _salva_conto_risparmio_categoria(self, nome):
    mappa = self._conti_risparmio_cat()
    scelto = self.conto_risp_cat.get() if hasattr(self, "conto_risp_cat") else NESSUNO
    classe = self._classi_categorie().get(nome)
    cid = None
    if classe == "Risparmio" and scelto and scelto != NESSUNO:
        try:
            cid = next((c.get("id") for c in _carica_portafoglio().get("conti", []) if c.get("nome") == scelto), None)
        except Exception:
            cid = None
    if cid:
        mappa[nome] = cid
    else:
        mappa.pop(nome, None)
        if classe == "Risparmio":
            try:
                self.after(2000, lambda: self.show_toast(
                    f"'{nome}' ha classe Risparmio ma nessun Conto risparmio: nessun trasferimento verrà creato.", duration=6000))
            except Exception:
                pass

def _nuovo_id_t(trasferimenti):
    ids = {t.get("id", "") for t in trasferimenti}
    i = 1
    while f"t{i}" in ids:
        i += 1
    return f"t{i}"

def _ripara_id_duplicati(trasf):
    visti = set()
    cambiato = False
    for t in trasf:
        if t.get("id", "") in visti:
            t["id"] = _nuovo_id_t(trasf)
            cambiato = True
        visti.add(t["id"])
    return cambiato

def _sincronizza_risparmio(self):
    try:
        db = _carica_portafoglio()
    except Exception:
        return
    conti = db.get("conti", [])
    id_a_nome = {c.get("id"): c.get("nome", "") for c in conti}
    nome_a_id = {v: k for k, v in id_a_nome.items()}
    classi = self._classi_categorie()
    dest = self._conti_risparmio_cat()
    trasf = db.get("trasferimenti", [])
    cambiato = _ripara_id_duplicati(trasf)
    auto = {t["id_spesa"]: t for t in trasf if t.get("auto_risparmio") and t.get("id_spesa")}
    visti = set()

    for d, voci in self.spese.items():
        for e in voci:
            if not isinstance(e, SpesaEntry):
                continue
            idsp = e.id_spesa
            cat = e.categoria
            dest_id = dest.get(cat)
            eleggibile = (str(e.tipo).strip().capitalize() == "Uscita"
                          and classi.get(cat) == "Risparmio"
                          and dest_id in id_a_nome)
            t = auto.get(idsp)
            if not eleggibile:
                if t is not None:
                    if not e.conto and t.get("da") in id_a_nome:
                        e.conto = id_a_nome[t["da"]]
                    trasf.remove(t)
                    cambiato = True
                continue
            src_id = nome_a_id.get(e.conto) if e.conto else (t.get("da") if t else None)
            if not src_id or src_id == dest_id or src_id not in id_a_nome:
                continue
            data_s = d.strftime("%d-%m-%Y")
            imp = round(float(e.importo), 2)
            nota = f"Risparmio: {e.descrizione}".strip()[:60] if e.descrizione else "Risparmio"
            if t is None:
                t = {"id": _nuovo_id_t(trasf), "data": data_s, "da": src_id, "a": dest_id,
                     "importo": imp, "note": nota, "auto_risparmio": True, "id_spesa": idsp}
                trasf.append(t)
                cambiato = True
            else:
                nuovo = {"data": data_s, "da": src_id, "a": dest_id, "importo": imp, "note": nota}
                if any(t.get(k) != v for k, v in nuovo.items()):
                    t.update(nuovo)
                    cambiato = True
            visti.add(idsp)
            if e.conto:
                e.conto = ""

    try:
        limite = datetime.date.today() - datetime.timedelta(days=365 * _app.ANNI_DA_MANTENERE)
    except Exception:
        limite = None
    def _storico(t):
        # trasferimento il cui movimento e' stato rimosso dalla pulizia dei dati vecchi: va conservato
        try:
            return limite is not None and datetime.datetime.strptime(t.get("data", ""), "%d-%m-%Y").date() < limite
        except ValueError:
            return False

    for idsp, t in list(auto.items()):
        if idsp not in visti and t in trasf and not _storico(t):
            esiste = any(isinstance(e, SpesaEntry) and e.id_spesa == idsp
                         for voci in self.spese.values() for e in voci)
            if not esiste:
                trasf.remove(t)
                cambiato = True
    if cambiato:
        db["trasferimenti"] = trasf
        try:
            with open(_app.PORTAFOGLIO_BANCARIO, "w", encoding="utf-8") as f:
                json.dump(db, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
