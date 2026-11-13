#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import json
import math
import re
from collections import Counter

PREFISSI = {"versamenti": "V", "valorizzazioni": "Z", "riscatti": "R"}
SEZIONI = {"versamenti": "Versamento", "valorizzazioni": "Valorizzazione", "riscatti": "Riscatto"}

PROMPT = (
    "Leggi questo documento di un fondo pensione italiano (estratto conto, comunicazione periodica, "
    "posizione individuale, riepilogo contributi oppure un elenco esportato da OrbitaCasa). "
    "Rispondi SOLO con un oggetto JSON in questa forma:\n"
    '{"valorizzazioni": [{"data": "gg-mm-aaaa", "controvalore": numero}],\n'
    ' "versamenti": [{"data": "gg-mm-aaaa", "tipo": "TFR|Lavoratore|Datore di Lavoro|Volontario", "importo": numero}],\n'
    ' "riscatti": [{"data": "gg-mm-aaaa", "tipo": "Anticipazione|Riscatto Parziale|Riscatto Totale|'
    'Trasferimento ad altro fondo", "importo": numero, "motivo": "testo breve"}]}\n'
    'Regole: "valorizzazioni" contiene il valore (controvalore) della posizione alla data di riferimento '
    "del documento: in un estratto è una sola riga, in un elenco una per ogni data presente. "
    "Le date sono nel formato gg-mm-aaaa. Gli importi sono numeri positivi con il punto come separatore "
    "decimale, senza simbolo di valuta. Includi in \"versamenti\" e \"riscatti\" solo i movimenti realmente "
    "presenti nel documento, uno per ogni riga con la sua data e il suo tipo di contributo; "
    "se non ce ne sono usa una lista vuota. Non usare la data di stampa del documento. "
    "Non inventare nulla, non sommare movimenti diversi e ignora le righe di totale."
)


def estrai_json(testo):
    if not testo:
        raise ValueError("Risposta vuota dall'IA")
    t = re.sub(r"```(?:json)?", "", str(testo), flags=re.I).strip()
    i, j = t.find("{"), t.rfind("}")
    if i < 0 or j <= i:
        raise ValueError("Risposta IA non leggibile")
    r = json.loads(t[i:j + 1])
    if not isinstance(r, dict):
        raise ValueError("Risposta IA non leggibile")
    return r

def _num(v):
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        x = float(v)
    else:
        s = str(v).replace("€", "").replace(" ", "").replace("\u00a0", "").strip()
        if not s or s.lower() == "null":
            return None
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        try:
            x = float(s)
        except ValueError:
            return None
    return x if math.isfinite(x) else None

def _data(v):
    s = str(v or "").strip().replace("/", "-").replace(".", "-")
    if not s or s.lower() == "null":
        return None
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d-%m-%y"):
        try:
            return datetime.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None

def _tipo_vers(t):
    s = str(t or "").lower()
    if "tfr" in s or "liquidazione" in s:
        return "TFR"
    if "datore" in s or "azienda" in s:
        return "Datore di Lavoro"
    if "lavorator" in s or "aderente" in s or "dipendente" in s:
        return "Lavoratore"
    return "Volontario"

def _tipo_risc(t):
    s = str(t or "").lower()
    if "trasfer" in s:
        return "Trasferimento ad altro fondo"
    if "total" in s:
        return "Riscatto Totale"
    if "parzial" in s:
        return "Riscatto Parziale"
    return "Anticipazione"

def _prop(chiave, d, tipo, importo, motivo):
    return {"chiave": chiave, "_d": d, "data": d.strftime("%d-%m-%Y"),
            "tipo": tipo, "importo": round(importo, 2), "motivo": motivo or ""}

def _lista(j, chiave):
    v = j.get(chiave)
    return [r for r in v if isinstance(r, dict)] if isinstance(v, list) else []

def _chiave_importo(x):
    try:
        return int(round(float(x or 0) * 100))
    except (TypeError, ValueError):
        return None

def leggi(j, db):
    nuove, gia = [], 0
    righe = _lista(j, "valorizzazioni")
    if isinstance(j.get("valorizzazione"), dict):
        righe.append(j["valorizzazione"])
    esistenti = {d for d in (_data(m.get("data")) for m in db.get("valorizzazioni", [])) if d}
    viste = set()
    for r in righe:
        d = _data(r.get("data"))
        imp = _num(r.get("controvalore", r.get("importo")))
        if d is None or imp is None or imp <= 0:
            continue
        if d in esistenti:
            gia += 1
        elif d not in viste:
            viste.add(d)
            nuove.append(_prop("valorizzazioni", d, "", imp, ""))

    for chiave, mappa in (("versamenti", _tipo_vers), ("riscatti", _tipo_risc)):
        conta = Counter()
        for m in db.get(chiave, []):
            d, c = _data(m.get("data")), _chiave_importo(m.get("importo"))
            if d is not None and c is not None:
                conta[(d, m.get("tipo"), c)] += 1
        for r in _lista(j, chiave):
            d = _data(r.get("data"))
            imp = _num(r.get("importo"))
            if d is None or imp is None or imp <= 0:
                continue
            tipo = mappa(r.get("tipo"))
            k = (d, tipo, _chiave_importo(imp))
            if conta[k] > 0:
                conta[k] -= 1
                gia += 1
            else:
                motivo = str(r.get("motivo") or "").strip() if chiave == "riscatti" else ""
                nuove.append(_prop(chiave, d, tipo, imp, motivo))

    ordine = {"versamenti": 0, "valorizzazioni": 1, "riscatti": 2}
    nuove.sort(key=lambda p: (p["_d"], ordine[p["chiave"]]))
    return nuove, gia

def _nuovo_id(prefisso, lista):
    ids = {x.get("id", "") for x in lista}
    i = 1
    while f"{prefisso}{i}" in ids:
        i += 1
    return f"{prefisso}{i}"

def applica(db, props):
    n = 0
    for p in props:
        lista = db.setdefault(p["chiave"], [])
        riga = {"id": _nuovo_id(PREFISSI[p["chiave"]], lista), "data": p["data"]}
        if p["chiave"] == "valorizzazioni":
            riga["controvalore"] = p["importo"]
        else:
            riga["tipo"] = p["tipo"]
            riga["importo"] = p["importo"]
        if p["chiave"] == "riscatti":
            riga["motivo"] = p["motivo"][:30]
        riga["note"] = "da PDF"
        lista.append(riga)
        n += 1
    return n
