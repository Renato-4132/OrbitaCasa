#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import os

def _path():
    import __main__ as _app
    return _app.LOG_IMPORTAZIONI

def _pulisci(testo):
    return str(testo or "").replace("|", "/").replace("\n", " ").strip()

def scrivi_riga(tipo_log, data_mov, desc, importo, direzione, categoria, voce=None,
                conto=None, metodo=None, tag=None, id_spesa=None):
    import __main__ as _app
    if voce is not None:
        conto = getattr(voce, "conto", "") if conto is None else conto
        metodo = getattr(voce, "metodo_pagamento", "") if metodo is None else metodo
        tag = " ".join(getattr(voce, "hashtag", []) or []) if tag is None else tag
        id_spesa = getattr(voce, "id_spesa", "") if id_spesa is None else id_spesa
    if isinstance(tag, (list, tuple)):
        tag = " ".join(tag)
    riga = (f"{datetime.datetime.now().strftime('%d/%m/%Y %H:%M'):<17} | {tipo_log:<8} | "
            f"{data_mov.strftime('%d/%m/%Y'):<10} | {_pulisci(desc):<50} | "
            f"{_app._fmt_it(abs(importo)):>10} € | {direzione:<7} | {_pulisci(categoria)} | "
            f"{_pulisci(conto) or '—'} | {id_spesa or ''} | {_pulisci(metodo) or '—'} | "
            f"{_pulisci(tag) or '—'}\n")
    try:
        with open(_path(), "a", encoding="utf-8") as f:
            f.write(riga)
    except Exception as e:
        print(f"Log importazioni non scritto: {e}")

def leggi(tipo=None):
    p = _path()
    if not os.path.exists(p):
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            righe = f.readlines()
    except Exception:
        return []
    out = []
    for n, r in enumerate(righe):
        if not r.strip():
            continue
        parti = [x.strip() for x in r.strip().split("|")]
        while len(parti) < 11:
            parti.append("")
        if tipo and parti[1].upper() != tipo.upper():
            continue
        out.append((n, parti[:11]))
    return out

def togli(numeri_riga):
    numeri = set(numeri_riga)
    if not numeri:
        return 0
    p = _path()
    with open(p, "r", encoding="utf-8") as f:
        righe = f.readlines()
    with open(p, "w", encoding="utf-8") as f:
        f.writelines(r for n, r in enumerate(righe) if n not in numeri)
    return len(numeri)
