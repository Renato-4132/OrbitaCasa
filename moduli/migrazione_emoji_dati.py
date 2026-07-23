#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time

MAPPA_EMOJI_DATI = {
    "♻️": "RIC·",
    "♻":  "RIC·",
    "📎": "ALL·",
    "👤": "PER·",
    "🏠": "CNT·",
    "⚖️": "CTP·",
    "⚖":  "CTP·",
    "⏰": "SCD:",
    "⏰\ufe0f": "SCD:",
}

def _migra_valore(obj, mappa):
    if isinstance(obj, dict):
        nuovo = {}
        conteggio = 0
        for k, v in obj.items():
            nuova_chiave = k
            if isinstance(k, str):
                for emoji, testo in mappa.items():
                    if emoji in nuova_chiave:
                        nuova_chiave = nuova_chiave.replace(emoji, testo)
                        conteggio += 1
            nuovo_valore, c = _migra_valore(v, mappa)
            conteggio += c
            nuovo[nuova_chiave] = nuovo_valore
        return nuovo, conteggio
    if isinstance(obj, list):
        conteggio = 0
        nuova_lista = []
        for v in obj:
            nuovo_valore, c = _migra_valore(v, mappa)
            conteggio += c
            nuova_lista.append(nuovo_valore)
        return nuova_lista, conteggio
    if isinstance(obj, str):
        nuovo_testo = obj
        conteggio = 0
        for emoji, testo in mappa.items():
            if emoji in nuovo_testo:
                nuovo_testo = nuovo_testo.replace(emoji, testo)
                conteggio += 1
        return nuovo_testo, conteggio
    return obj, 0


def _migra_file_json(percorso, mappa, indent=2):
    if not percorso or not os.path.exists(percorso):
        return 0
    try:
        with open(percorso, "r", encoding="utf-8") as f:
            dati = json.load(f)
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Migrazione emoji: impossibile leggere {os.path.basename(percorso)}: {e}")
        return 0
    nuovo, conteggio = _migra_valore(dati, mappa)
    if not conteggio:
        return 0
    try:
        temp_file = percorso + ".tmp_emoji"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(nuovo, f, indent=indent, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_file, percorso)
        print(f"[{time.strftime('%H:%M:%S')}] Migrazione emoji: {conteggio} sostituzioni in {os.path.basename(percorso)}")
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Migrazione emoji: scrittura fallita per {os.path.basename(percorso)}: {e}")
        return 0
    return conteggio

def migra_emoji_nei_dati(file_e_indent, mappa=None):
    mappa = mappa or MAPPA_EMOJI_DATI
    totale = 0
    for percorso, indent in file_e_indent:
        totale += _migra_file_json(percorso, mappa, indent)
    return totale
