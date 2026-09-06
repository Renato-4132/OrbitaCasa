#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

MARKER_SPESE = ("__spese__", "Contabilità")

def costruisci_mappa_conti_da_trasferimenti(portafoglio_path):
    mappa = {}
    try:
        with open(portafoglio_path, "r", encoding="utf-8") as f:
            db = json.load(f)
        id_a_nome = {c.get("id"): c.get("nome", "") for c in db.get("conti", [])}
        for t in db.get("trasferimenti", []):
            da_raw = t.get("da")
            a_raw = t.get("a")
            if da_raw not in MARKER_SPESE and a_raw not in MARKER_SPESE:
                continue
            data_t = t.get("data", "")
            try:
                imp_t = round(float(t.get("importo", 0)), 2)
            except (TypeError, ValueError):
                continue
            tipo_t = "Entrata" if da_raw in MARKER_SPESE else "Uscita"
            id_conto = a_raw if tipo_t == "Entrata" else da_raw
            nome_conto = id_a_nome.get(id_conto, "")
            mappa.setdefault((data_t, imp_t, tipo_t), []).append(nome_conto)
    except Exception:
        return {}
    return mappa

def e_trasferimento_virtuale(t):
    return t.get("da", "") in MARKER_SPESE or t.get("a", "") in MARKER_SPESE

def conto_da_mappa(mappa, contatori_ordinale, data_str, importo, tipo):
    chiave = (data_str, round(float(importo), 2), str(tipo).capitalize())
    candidati = mappa.get(chiave, [])
    ordinale = contatori_ordinale.get(chiave, 0)
    contatori_ordinale[chiave] = ordinale + 1
    return candidati[ordinale] if ordinale < len(candidati) else ""
    
