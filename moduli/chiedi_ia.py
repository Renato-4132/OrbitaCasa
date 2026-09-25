#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import threading
import datetime
import tkinter as tk
from tkinter import ttk, filedialog

from moduli.modello_spesa import campo
from moduli.spinner_animato import crea_spinner_animato
from moduli.mappa_conti_trasferimenti import e_trasferimento_virtuale

def _crea_periodi(oggi):
    lun_corrente = oggi - datetime.timedelta(days=oggi.weekday())
    lun_scorsa = lun_corrente - datetime.timedelta(days=7)
    dom_scorsa = lun_corrente - datetime.timedelta(days=1)
    primo_mese_corrente = oggi.replace(day=1)
    ultimo_mese_scorso = primo_mese_corrente - datetime.timedelta(days=1)
    primo_mese_scorso = ultimo_mese_scorso.replace(day=1)
    primo_anno_corrente = oggi.replace(month=1, day=1)
    primo_anno_scorso = primo_anno_corrente.replace(year=primo_anno_corrente.year - 1)
    ultimo_anno_scorso = primo_anno_corrente - datetime.timedelta(days=1)
    return {
        "OGGI":               (oggi, oggi),
        "IERI":                (oggi - datetime.timedelta(days=1), oggi - datetime.timedelta(days=1)),
        "ULTIMI 7 GIORNI":     (oggi - datetime.timedelta(days=6), oggi),
        "ULTIMI 30 GIORNI":    (oggi - datetime.timedelta(days=29), oggi),
        "ULTIMI 90 GIORNI":    (oggi - datetime.timedelta(days=89), oggi),
        "QUESTA SETTIMANA (lun-oggi)":  (lun_corrente, oggi),
        "SETTIMANA SCORSA (lun-dom)":   (lun_scorsa, dom_scorsa),
        "QUESTO MESE":         (primo_mese_corrente, oggi),
        "MESE SCORSO":         (primo_mese_scorso, ultimo_mese_scorso),
        "QUEST'ANNO":          (primo_anno_corrente, oggi),
        "ANNO SCORSO":         (primo_anno_scorso, ultimo_anno_scorso),
    }


def _leggi_json(path):
    try:
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None

def _blocco_spese_pianificate(data, _fmt_it):
    piani = (data or {}).get("piani") if isinstance(data, dict) else None
    if not piani:
        return []
    oggi = datetime.datetime.now().date()
    righe = ["", "SPESE PIANIFICATE / DILAZIONATE (rate mensili programmate):"]
    for p in piani:
        nome = p.get("nome", "?")
        cat = p.get("categoria", "")
        conto = p.get("conto", "")
        tot = float(p.get("importo_totale", 0) or 0)
        quota = float(p.get("quota", 0) or 0)
        mesi = p.get("mesi", "?")
        scadenza = p.get("data_scadenza", "")
        inizio = p.get("inizio", "")
        riga = (f"   - {nome} [{cat}]" + (f" su conto '{conto}'" if conto else "") +
                     f": totale {_fmt_it(tot)}€, rata {_fmt_it(quota)}€/mese per {mesi} mesi"
                     f" (dal {inizio} al {scadenza})")
        try:
            d_inizio = datetime.datetime.strptime(inizio, "%Y-%m-%d").date()
            mesi_trascorsi = max(0, min(int(mesi) if str(mesi).isdigit() else 0,
                                         (oggi.year - d_inizio.year) * 12 + (oggi.month - d_inizio.month)))
            mesi_rimanenti = max(0, (int(mesi) if str(mesi).isdigit() else 0) - mesi_trascorsi)
            gia_accantonato = quota * mesi_trascorsi
            residuo = tot - gia_accantonato
            riga += (f" - progresso: {mesi_trascorsi}/{mesi} rate trascorse, "
                     f"{_fmt_it(gia_accantonato)}€ già accantonati indicativamente, "
                     f"{_fmt_it(residuo)}€ residui in {mesi_rimanenti} rate")
        except Exception:
            pass
        righe.append(riga)
    return righe

def _blocco_scadenze_ricorrenti_mese(self, oggi, _fmt_it):
    ricorrenze = getattr(self, "ricorrenze", {}) or {}
    if not ricorrenze:
        return []
    mese_corrente = oggi.month
    anno_corrente = oggi.year
    dimenticate = []
    prossime = []
    for item_id, dati in ricorrenze.items():
        try:
            ric_type = dati.get("tipo", "").lower()
            n = dati.get("n", 0)
            data_inizio = datetime.datetime.strptime(dati.get("data_inizio", ""), "%d-%m-%Y").date()
            categoria = dati.get("cat", "N/D")
            descrizione_base = dati.get("desc", "—")
            tipo_voce = dati.get("tipo_voce", "N/D")
            importo_base = float(str(dati.get("imp", "0")).replace(",", "."))
            for i in range(n):
                if ric_type == "ogni mese":
                    mese = (data_inizio.month - 1 + i) % 12 + 1
                    anno = data_inizio.year + (data_inizio.month - 1 + i) // 12
                    giorno = min(data_inizio.day,
                        [31, 29 if anno % 4 == 0 and (anno % 100 != 0 or anno % 400 == 0) else 28,
                         31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mese - 1])
                    data_movimento = datetime.date(anno, mese, giorno)
                elif ric_type == "ogni anno":
                    try:
                        data_movimento = data_inizio.replace(year=data_inizio.year + i)
                    except ValueError:
                        data_movimento = data_inizio.replace(year=data_inizio.year + i, day=28)
                else:
                    data_movimento = data_inizio + datetime.timedelta(days=i)
                if data_movimento.month != mese_corrente or data_movimento.year != anno_corrente:
                    continue
                voce_trovata = False
                if data_movimento in self.spese:
                    for voce in self.spese[data_movimento]:
                        if len(voce) >= 5 and voce[4] == item_id:
                            voce_trovata = True
                            break
                riga = (f"{descrizione_base} [{categoria}] {tipo_voce} {_fmt_it(importo_base)}€ "
                        f"prevista il {data_movimento.strftime('%d-%m-%Y')}")
                if data_movimento <= oggi and not voce_trovata:
                    dimenticate.append(riga)
                elif data_movimento > oggi and not voce_trovata:
                    prossime.append(riga)
        except Exception:
            continue
    righe = []
    if dimenticate:
        righe.append("")
        righe.append("SPESE RICORRENTI DI QUESTO MESE NON ANCORA REGISTRATE (possibili dimenticanze, "
                     "data di scadenza già passata senza movimento corrispondente registrato):")
        for r in dimenticate:
            righe.append(f"   - {r}")
    if prossime:
        righe.append("")
        righe.append("SPESE RICORRENTI DI QUESTO MESE ANCORA DA VENIRE (non ancora scadute):")
        for r in prossime:
            righe.append(f"   - {r}")
    return righe

def _blocco_fondo_pensione(data, _fmt_it):
    if not data:
        return []
    anag = data.get("anagrafica", {}) or {}
    versamenti = data.get("versamenti", []) or []
    riscatti = data.get("riscatti", []) or []
    valorizzazioni = data.get("valorizzazioni", []) or []
    tot_vers = sum(float(v.get("importo", 0) or 0) for v in versamenti)
    tot_risc = sum(float(r.get("importo", 0) or 0) for r in riscatti)
    righe = ["", "FONDO PENSIONE:"]
    if anag:
        righe.append(f"   Fondo: {anag.get('nome_fondo', '?')} - Gestore: {anag.get('gestore', '?')} - "
                     f"Comparto: {anag.get('comparto', '?')} - Tipo: {anag.get('tipo', '?')} - "
                     f"Adesione: {anag.get('data_adesione', '?')}")
    righe.append(f"   Totale versamenti: {_fmt_it(tot_vers)}€ ({len(versamenti)} versamenti)")

    per_tipo = {}
    per_anno = {}
    for v in versamenti:
        tipo_v = v.get("tipo", "?") or "?"
        per_tipo[tipo_v] = per_tipo.get(tipo_v, 0.0) + float(v.get("importo", 0) or 0)
        d = v.get("data", "")
        anno = d[-4:] if len(d) == 10 else "Anno n/d"
        per_anno[anno] = per_anno.get(anno, 0.0) + float(v.get("importo", 0) or 0)
    if per_tipo:
        righe.append("      Versamenti per tipo: " + ", ".join(
            f"{t} {_fmt_it(imp)}€" for t, imp in sorted(per_tipo.items(), key=lambda kv: kv[1], reverse=True)))
    if per_anno:
        righe.append("      Versamenti per anno: " + ", ".join(
            f"{a} {_fmt_it(imp)}€" for a, imp in sorted(per_anno.items(), reverse=True)))

    righe.append(f"   Totale riscatti/anticipazioni: {_fmt_it(tot_risc)}€ ({len(riscatti)} riscatti)")

    if valorizzazioni:
        valor_ordinate = sorted(valorizzazioni, key=lambda x: x.get("data", ""))
        ultima = valor_ordinate[-1]
        controvalore = float(ultima.get("controvalore", 0) or 0)
        versato_netto = tot_vers - tot_risc
        rendimento = controvalore - versato_netto
        righe.append(f"   Ultimo controvalore comunicato: {_fmt_it(controvalore)}€ "
                     f"(al {ultima.get('data', '?')})")
        righe.append(f"   Versato netto (versamenti - riscatti) fino ad oggi: {_fmt_it(versato_netto)}€ - "
                     f"differenza rispetto al controvalore (rendimento/perdita stimati): {_fmt_it(rendimento)}€")
    return righe

def _blocco_fondo_risparmio(data, _fmt_it):
    if not data:
        return []
    obiettivo = float(data.get("obiettivo_annuale", 0) or 0)
    attuale = float(data.get("fondo_attuale", 0) or 0)
    perc = (attuale / obiettivo * 100) if obiettivo else 0
    righe = ["", "FONDO RISPARMIO:"]
    righe.append(f"   Fondo attuale accantonato: {_fmt_it(attuale)}€ - "
                 f"Obiettivo annuale: {_fmt_it(obiettivo)}€ ({perc:.0f}% raggiunto)")
    obiettivi = data.get("obiettivi") or []
    if obiettivi:
        righe.append("   Obiettivi specifici di risparmio:")
        for o in obiettivi:
            nome_o = o.get("nome", "?")
            imp_o = float(o.get("importo", 0) or 0)
            entro = o.get("data", "?")
            mesi = o.get("mesi", 0) or 0
            rata = imp_o / mesi if mesi else imp_o
            righe.append(f"      - {nome_o}: obiettivo {_fmt_it(imp_o)}€ entro {entro} "
                         f"({mesi} mesi rimanenti al momento della creazione), "
                         f"rata mensile necessaria {_fmt_it(rata)}€")
    return righe

def _blocco_immobili(data, _fmt_it):
    immobili = (data or {}).get("immobili") if isinstance(data, dict) else None
    if not immobili:
        return []
    righe = ["", "IMMOBILI:"]
    for imm in immobili:
        nome = imm.get("nome", "?")
        canone = float(imm.get("canone", 0) or 0)
        conto = imm.get("conto", "")
        spese = imm.get("spese", []) or []
        tot_e = sum(float(s.get("importo", 0) or 0) for s in spese if s.get("tipo") == "Entrata")
        tot_u = sum(float(s.get("importo", 0) or 0) for s in spese if s.get("tipo") == "Uscita")
        righe.append(f"   - {nome}" + (f" (canone {_fmt_it(canone)}€/mese)" if canone else "") +
                     (f" - conto: {conto}" if conto else "") +
                     f": entrate {_fmt_it(tot_e)}€, uscite {_fmt_it(tot_u)}€, "
                     f"saldo {_fmt_it(tot_e - tot_u)}€ ({len(spese)} movimenti registrati)")
        per_anno_cat = {}
        ultima_data = None
        for s in spese:
            if s.get("tipo") != "Uscita":
                continue
            d = s.get("data", "")
            anno = d[-4:] if len(d) == 10 else "Anno n/d"
            cat = s.get("categoria", "") or "Senza categoria"
            per_anno_cat.setdefault(anno, {})
            per_anno_cat[anno][cat] = per_anno_cat[anno].get(cat, 0.0) + float(s.get("importo", 0) or 0)
            if len(d) == 10 and (ultima_data is None or
               d[-4:]+d[3:5]+d[0:2] > ultima_data[-4:]+ultima_data[3:5]+ultima_data[0:2]):
                ultima_data = d
        if per_anno_cat:
            righe.append("      Uscite per anno e categoria:")
            for anno in sorted(per_anno_cat.keys(), reverse=True):
                dettaglio = ", ".join(f"{c} {_fmt_it(imp)}€" for c, imp in
                                       sorted(per_anno_cat[anno].items(), key=lambda kv: kv[1], reverse=True))
                righe.append(f"         {anno}: {dettaglio}")
        if ultima_data:
            righe.append(f"      Ultima spesa registrata: {ultima_data}")
    return righe

def _blocco_fairshare(data, _fmt_it):
    if not data:
        return []
    righe = ["", "FAIRSHARE - SPESE CONDIVISE TRA PIÙ PERSONE (DARE/AVERE):"]
    per_categoria_fs = {}
    chi_deve_a_chi = {}
    for voce in data:
        cat = voce.get("categoria", "?")
        tot = float(voce.get("importo_totale", 0) or 0)
        creditore = voce.get("creditore", "?")
        stato = voce.get("stato", "?")
        partecipanti = voce.get("partecipanti", []) or []
        pagamenti = voce.get("pagamenti", {}) or {}
        non_pagati = [p for p, info in pagamenti.items() if not info.get("pagato")]
        n_parti = len(partecipanti) or 1
        quota_indicativa = tot / n_parti
        riga = (f"   - {cat} del {voce.get('data', '?')}: totale {_fmt_it(tot)}€, "
               f"creditore {creditore}, partecipanti: {', '.join(partecipanti) or '?'} "
               f"(quota indicativa a parti uguali: {_fmt_it(quota_indicativa)}€ ciascuno), stato: {stato}")
        if non_pagati:
            riga += f", ancora da pagare: {', '.join(non_pagati)}"
        else:
            riga += ", tutti i partecipanti hanno pagato"
        righe.append(riga)

        per_categoria_fs[cat] = per_categoria_fs.get(cat, 0.0) + tot

        if stato != "chiuso":
            for debitore in non_pagati:
                if debitore == creditore:
                    continue
                chiave = (debitore, creditore)
                chi_deve_a_chi[chiave] = chi_deve_a_chi.get(chiave, 0.0) + quota_indicativa

    if per_categoria_fs:
        righe.append("")
        righe.append("   TOTALE FAIRSHARE PER CATEGORIA (storico completo):")
        for c, v in sorted(per_categoria_fs.items(), key=lambda kv: kv[1], reverse=True):
            righe.append(f"      - {c}: {_fmt_it(v)}€")

    if chi_deve_a_chi:
        righe.append("")
        righe.append("   CHI DEVE A CHI (saldo aperto complessivo, quote indicative a parti uguali):")
        for (debitore, creditore), importo in sorted(chi_deve_a_chi.items(), key=lambda x: (x[0][1], x[0][0])):
            righe.append(f"      - {debitore} -> {creditore}: {_fmt_it(importo)}€")
        righe.append("      (nota: se sono impostate percentuali di ripartizione personalizzate per "
                     "qualche persona, gli importi reali possono differire leggermente da questa stima "
                     "a parti uguali; vedi il modulo Dare & Avere per i valori esatti)")
    return righe

def _blocco_utenze(data, _fmt_it):
    letture = (data or {}).get("letture_salvate") if isinstance(data, dict) else None
    if not letture:
        return []
    righe = ["", "UTENZE (LETTURE CONTATORI ACQUA/LUCE/GAS):"]
    for utenza, anni in letture.items():
        for anno, righe_lettura in (anni or {}).items():
            try:
                consumo_tot = sum(float(r[3]) for r in righe_lettura if len(r) > 3 and r[3] not in (None, ""))
            except Exception:
                consumo_tot = 0.0
            righe.append(f"   - {utenza} anno {anno}: consumo totale registrato {consumo_tot:.1f} unità")
    return righe

def _blocco_promemoria(data):
    testo = (data or {}).get("promemoria", "") if isinstance(data, dict) else ""
    testo = (testo or "").strip()
    if not testo:
        return []
    return ["", "PROMEMORIA / SCADENZIARIO (testo libero inserito dall'utente):", testo]

def _blocco_schedule(data):
    if not data:
        return []
    righe = ["", "AUTOMAZIONI / NOTIFICHE PROGRAMMATE:"]
    for s in data:
        nome = s.get("nome", "?")
        tipo = s.get("tipo", "?")
        freq = s.get("frequenza", "?")
        attivo = "attiva" if s.get("attivo") else "disattivata"
        ultima = s.get("ultima_esecuzione", "n/d")
        righe.append(f"   - {nome} ({tipo}, {freq}, {attivo}) - ultima esecuzione: {ultima}")
    return righe

def _blocco_veicoli(data, _fmt_it):
    veicoli = (data or {}).get("veicoli") if isinstance(data, dict) else None
    if not veicoli:
        return []
    righe = ["", "VEICOLI:"]
    for v in veicoli:
        nome = v.get("nome", "?")
        modello = v.get("modello", "")
        targa = v.get("targa", "")
        km = v.get("km_attuali", "")
        movimenti = v.get("movimenti", []) or []
        tot_spese = sum(float(m.get("importo", 0) or 0) for m in movimenti)
        scadenze = []
        for campo_s, etichetta in [("scad_bollo", "bollo"), ("scad_assicurazione", "assicurazione"),
                                    ("scad_revisione", "revisione")]:
            val = v.get(campo_s)
            if val:
                scadenze.append(f"{etichetta} {val}")
        riga = f"   - {nome}" + (f" {modello}" if modello else "") + (f" (targa {targa})" if targa else "")
        riga += f": km attuali {km}, spesa totale {_fmt_it(tot_spese)}€ ({len(movimenti)} movimenti)"
        if scadenze:
            riga += " - scadenze: " + ", ".join(scadenze)
        righe.append(riga)

        def _chiave_data(d):
            return d[-4:] + d[3:5] + d[0:2] if len(d) == 10 else ""

        per_anno_cat = {}
        per_cat_ultima = {}
        ultima_data = None
        for m in movimenti:
            d = m.get("data", "")
            anno = d[-4:] if len(d) == 10 else "Anno n/d"
            cat = m.get("categoria", "") or "Senza categoria"
            per_anno_cat.setdefault(anno, {})
            per_anno_cat[anno][cat] = per_anno_cat[anno].get(cat, 0.0) + float(m.get("importo", 0) or 0)
            if len(d) == 10:
                if cat not in per_cat_ultima or _chiave_data(d) > _chiave_data(per_cat_ultima[cat]):
                    per_cat_ultima[cat] = d
                if ultima_data is None or _chiave_data(d) > _chiave_data(ultima_data):
                    ultima_data = d
        if per_anno_cat:
            for anno in sorted(per_anno_cat.keys(), reverse=True):
                dettaglio = ", ".join(f"{c} {_fmt_it(imp)}€" for c, imp in
                                       sorted(per_anno_cat[anno].items(), key=lambda kv: kv[1], reverse=True))
                righe.append(f"      {anno}: {dettaglio}")
        if per_cat_ultima:
            dettaglio_date = ", ".join(f"{c}: {d}" for c, d in
                                        sorted(per_cat_ultima.items(), key=lambda kv: kv[1], reverse=True))
            righe.append(f"      Ultima spesa per categoria: {dettaglio_date}")
        if ultima_data:
            righe.append(f"      Ultimo movimento registrato: {ultima_data}")
    return righe

def _blocco_rubrica(data):
    if not data:
        return []
    nomi = [c.get("nome", "?") for c in data if c.get("nome")]
    dettaglio = f" ({', '.join(nomi[:20])}{'...' if len(nomi) > 20 else ''})" if nomi else ""
    return ["", f"RUBRICA CONTATTI: {len(data)} contatti registrati{dettaglio}"]

def _blocco_supermercati(data):
    if not data:
        return []
    try:
        n = len(data)
    except Exception:
        n = 0
    return ["", f"DATABASE PREZZI SUPERMERCATI: {n} voci registrate per il confronto prodotti/prezzi."]

def _blocco_trasferimenti(trasferimenti_raw, id_a_nome, _fmt_it):
    if not trasferimenti_raw:
        return []
    NOMI_MESI_IT = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
                    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]
    reali = []
    for t in trasferimenti_raw:
        if e_trasferimento_virtuale(t):
            continue
        try:
            d_obj = datetime.datetime.strptime(t.get("data", ""), "%d-%m-%Y").date()
        except Exception:
            continue
        try:
            importo = round(float(t.get("importo", 0) or 0), 2)
        except (TypeError, ValueError):
            continue
        reali.append({
            "data": d_obj,
            "da": id_a_nome.get(t.get("da"), "?"),
            "a": id_a_nome.get(t.get("a"), "?"),
            "importo": importo,
            "note": t.get("note", ""),
        })
    if not reali:
        return []
    reali.sort(key=lambda r: r["data"], reverse=True)
    tot = sum(r["importo"] for r in reali)

    per_coppia = {}
    per_mese_t = {}
    for r in reali:
        coppia = f"{r['da']} \u2192 {r['a']}"
        c = per_coppia.setdefault(coppia, {"totale": 0.0, "conteggio": 0})
        c["totale"] += r["importo"]
        c["conteggio"] += 1
        mese_key = (r["data"].year, r["data"].month)
        m = per_mese_t.setdefault(mese_key, {"totale": 0.0, "conteggio": 0})
        m["totale"] += r["importo"]
        m["conteggio"] += 1

    righe = ["", "TRASFERIMENTI TRA CONTI (movimenti interni tra i conti registrati: NON sono entrate "
                 "né uscite reali, spostano solo denaro da un conto all'altro e NON sono già inclusi "
                 "nei totali di entrate/uscite calcolati sopra):"]
    righe.append(f"   Totale trasferimenti registrati: {len(reali)} - "
                 f"importo complessivo trasferito: {_fmt_it(tot)}€")
    righe.append("   Riepilogo per coppia di conti (da \u2192 a):")
    for coppia, v in sorted(per_coppia.items(), key=lambda kv: kv[1]["totale"], reverse=True):
        righe.append(f"      - {coppia}: {_fmt_it(v['totale'])}€ ({v['conteggio']} trasferimenti)")
    righe.append("   Riepilogo mese per mese:")
    for (anno_m, mese_m), v in sorted(per_mese_t.items(), reverse=True):
        righe.append(f"      - {NOMI_MESI_IT[mese_m - 1]} {anno_m}: {_fmt_it(v['totale'])}€ "
                     f"({v['conteggio']} trasferimenti)")
    righe.append(f"   Elenco dettagliato (dal più recente, max 60 mostrati - per i totali oltre questo "
                 f"limite usa i riepiloghi sopra):")
    for r in reali[:60]:
        nota = f" - nota: {r['note']}" if r.get("note") else ""
        righe.append(f"      - {r['data'].strftime('%d/%m/%Y')}: {r['da']} \u2192 {r['a']}, "
                     f"{_fmt_it(r['importo'])}€{nota}")
    if len(reali) > 60:
        righe.append(f"      ... e altri {len(reali) - 60} trasferimenti più vecchi non elencati singolarmente.")
    return righe

def _blocco_studio(clienti, appuntamenti, fatture, cassa, magazzino, _fmt_it):
    if not any([clienti, appuntamenti, fatture, cassa, magazzino]):
        return []
    oggi_iso = datetime.datetime.now().strftime("%Y-%m-%d")
    righe = ["", "MODULO STUDIO / ATTIVITÀ PROFESSIONALE (MyBusiness):"]
    if clienti:
        nomi = [f"{c.get('nome','')} {c.get('cognome','')}".strip() +
                (f" ({c.get('azienda')})" if c.get("azienda") else "")
                for c in clienti]
        righe.append(f"   Clienti registrati: {len(clienti)} ({', '.join(nomi[:30])}{'...' if len(nomi) > 30 else ''})")
    if appuntamenti:
        stati = {}
        for a in appuntamenti:
            st = a.get("stato", "?")
            stati[st] = stati.get(st, 0) + 1
        dettaglio_stati = ", ".join(f"{k}: {v}" for k, v in stati.items())
        righe.append(f"   Appuntamenti totali: {len(appuntamenti)} ({dettaglio_stati})")
        prossimi = sorted(
            [a for a in appuntamenti if a.get("stato") != "Annullato" and a.get("data", "") >= oggi_iso],
            key=lambda a: a.get("data", ""))[:15]
        if prossimi:
            righe.append("   Prossimi appuntamenti:")
            for a in prossimi:
                try:
                    df = datetime.date.fromisoformat(a["data"]).strftime("%d/%m/%Y")
                except Exception:
                    df = a.get("data", "")
                righe.append(f"      - {df} {a.get('ora','')} {a.get('cliente_nome','')} "
                             f"({a.get('prestazione','')}) - {a.get('stato','')}")
    if fatture:
        tot_fatt = 0.0
        stati_f = {}
        for f in fatture:
            st = f.get("stato", "?")
            stati_f[st] = stati_f.get(st, 0) + 1
            for r in (f.get("righe") or []):
                tot_fatt += float(r.get("qty", 0) or 0) * float(r.get("prezzo", 0) or 0)
        dettaglio_stati_f = ", ".join(f"{k}: {v}" for k, v in stati_f.items())
        righe.append(f"   Fatture: {len(fatture)} ({dettaglio_stati_f}) - "
                     f"imponibile totale stimato {_fmt_it(tot_fatt)}€")
        aperte = [f for f in fatture if f.get("stato") in ("Emessa", "Scaduta")]
        if aperte:
            righe.append("   Fatture ancora da incassare (Emesse/Scadute):")
            for f in sorted(aperte, key=lambda x: x.get("data", "")):
                tot_f = sum(float(r.get("qty", 0) or 0) * float(r.get("prezzo", 0) or 0)
                            for r in (f.get("righe") or []))
                try:
                    df = datetime.date.fromisoformat(f["data"]).strftime("%d/%m/%Y")
                except Exception:
                    df = f.get("data", "")
                righe.append(f"      - {df} {f.get('cliente_nome','')}: {_fmt_it(tot_f)}€ ({f.get('stato','')})")
    if cassa:
        tot_e = sum(float(c.get("importo", 0) or 0) for c in cassa if c.get("tipo") == "Entrata")
        tot_u = sum(float(c.get("importo", 0) or 0) for c in cassa if c.get("tipo") == "Uscita")
        righe.append(f"   Cassa studio: entrate {_fmt_it(tot_e)}€, uscite {_fmt_it(tot_u)}€ "
                     f"({len(cassa)} movimenti)")
        per_cat_e, per_cat_u = {}, {}
        for c in cassa:
            cat = c.get("categoria", "") or "Senza categoria"
            imp = float(c.get("importo", 0) or 0)
            if c.get("tipo") == "Entrata":
                per_cat_e[cat] = per_cat_e.get(cat, 0.0) + imp
            else:
                per_cat_u[cat] = per_cat_u.get(cat, 0.0) + imp
        if per_cat_e:
            righe.append("      Entrate per categoria: " + ", ".join(
                f"{c} {_fmt_it(v)}€" for c, v in sorted(per_cat_e.items(), key=lambda kv: kv[1], reverse=True)))
        if per_cat_u:
            righe.append("      Uscite per categoria: " + ", ".join(
                f"{c} {_fmt_it(v)}€" for c, v in sorted(per_cat_u.items(), key=lambda kv: kv[1], reverse=True)))
    if magazzino:
        sotto_soglia = [m for m in magazzino if float(m.get("quantita", 0) or 0) <= float(m.get("soglia", 0) or 0)]
        righe.append(f"   Magazzino: {len(magazzino)} articoli, {len(sotto_soglia)} sotto soglia scorta")
        if sotto_soglia:
            nomi = ", ".join(m.get("nome", "?") for m in sotto_soglia[:10])
            righe.append(f"      Articoli sotto soglia: {nomi}")
    return righe

def _costruisci_contesto_database(self, _app, _fmt_it):
    PORTAFOGLIO_BANCARIO = getattr(_app, 'PORTAFOGLIO_BANCARIO', None)
    oggi = datetime.datetime.now().date()
    limite_365 = oggi - datetime.timedelta(days=365)
    periodi = _crea_periodi(oggi)


    e_tot_all, u_tot_all = 0.0, 0.0
    e_tot_365, u_tot_365 = 0.0, 0.0
    per_categoria = {}
    per_metodo = {}
    per_conto = {}
    n_movimenti = 0
    data_min, data_max = None, None

    per_periodo = {nome: {"entrate": 0.0, "uscite": 0.0, "categorie": {}, "conti": {},
                          "categorie_per_conto": {}} for nome in periodi}
    per_mese = {}
    NOMI_MESI_IT = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
                    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"]

    for data_op, lista_movimenti in self.spese.items():
        if isinstance(data_op, str):
            try:
                d_obj = datetime.datetime.strptime(data_op, "%d-%m-%Y").date()
            except Exception:
                continue
        elif isinstance(data_op, datetime.datetime):
            d_obj = data_op.date()
        elif isinstance(data_op, datetime.date):
            d_obj = data_op
        else:
            continue

        if data_min is None or d_obj < data_min:
            data_min = d_obj
        if data_max is None or d_obj > data_max:
            data_max = d_obj
        in_365 = d_obj >= limite_365

        periodi_coinvolti = [nome for nome, (ini, fine) in periodi.items() if ini <= d_obj <= fine]
        mese_key = (d_obj.year, d_obj.month)
        per_mese.setdefault(mese_key, {"entrate": 0.0, "uscite": 0.0, "categorie": {}, "conti": {},
                                       "categorie_per_conto": {}})

        for mov in lista_movimenti:
            try:
                cat = campo(mov, "categoria", "") or "Senza categoria"
                importo = float(campo(mov, "importo", 0.0))
                tipo = campo(mov, "tipo", "")
                metodo = campo(mov, "metodo_pagamento", "") or "Non specificato"
                conto = campo(mov, "conto", "") or "Non assegnato"
                n_movimenti += 1
                per_conto.setdefault(conto, {"entrate": 0.0, "uscite": 0.0})
                if tipo == "Entrata":
                    e_tot_all += importo
                    per_conto[conto]["entrate"] += importo
                    if in_365:
                        e_tot_365 += importo
                    for nome_p in periodi_coinvolti:
                        per_periodo[nome_p]["entrate"] += importo
                        pc = per_periodo[nome_p]["conti"].setdefault(conto, {"entrate": 0.0, "uscite": 0.0})
                        pc["entrate"] += importo
                    per_mese[mese_key]["entrate"] += importo
                    pcm = per_mese[mese_key]["conti"].setdefault(conto, {"entrate": 0.0, "uscite": 0.0})
                    pcm["entrate"] += importo
                else:
                    u_tot_all += importo
                    per_conto[conto]["uscite"] += importo
                    per_categoria[cat] = per_categoria.get(cat, 0.0) + importo
                    per_metodo[metodo] = per_metodo.get(metodo, 0.0) + importo
                    if in_365:
                        u_tot_365 += importo
                    for nome_p in periodi_coinvolti:
                        per_periodo[nome_p]["uscite"] += importo
                        per_periodo[nome_p]["categorie"][cat] = per_periodo[nome_p]["categorie"].get(cat, 0.0) + importo
                        pc = per_periodo[nome_p]["conti"].setdefault(conto, {"entrate": 0.0, "uscite": 0.0})
                        pc["uscite"] += importo
                        cpc_p = per_periodo[nome_p]["categorie_per_conto"].setdefault(conto, {})
                        cpc_p[cat] = cpc_p.get(cat, 0.0) + importo
                    per_mese[mese_key]["uscite"] += importo
                    per_mese[mese_key]["categorie"][cat] = per_mese[mese_key]["categorie"].get(cat, 0.0) + importo
                    pcm = per_mese[mese_key]["conti"].setdefault(conto, {"entrate": 0.0, "uscite": 0.0})
                    pcm["uscite"] += importo
                    cpc_m = per_mese[mese_key]["categorie_per_conto"].setdefault(conto, {})
                    cpc_m[cat] = cpc_m.get(cat, 0.0) + importo
            except Exception:
                continue

    cat_ordinate = dict(sorted(per_categoria.items(), key=lambda kv: kv[1], reverse=True))
    metodo_ordinati = dict(sorted(per_metodo.items(), key=lambda kv: kv[1], reverse=True))

    righe = []
    righe.append(f"OGGI È: {oggi.strftime('%d/%m/%Y')} ({['lunedì','martedì','mercoledì','giovedì','venerdì','sabato','domenica'][oggi.weekday()]})")
    righe.append(f"PERIODO DATI DISPONIBILI NEL DATABASE: dal {data_min.strftime('%d/%m/%Y') if data_min else 'n/d'} "
                 f"al {data_max.strftime('%d/%m/%Y') if data_max else 'n/d'}")
    righe.append(f"NUMERO TOTALE MOVIMENTI REGISTRATI: {n_movimenti}")
    righe.append("")
    righe.append("RIEPILOGO PER PERIODI TEMPORALI (usa questi dati per domande su oggi, ieri, "
                 "questa settimana, settimana scorsa, questo mese, mese scorso, quest'anno, anno scorso):")
    for nome_p, (ini, fine) in periodi.items():
        dati = per_periodo[nome_p]
        intervallo = ini.strftime('%d/%m/%Y') if ini == fine else f"{ini.strftime('%d/%m/%Y')} - {fine.strftime('%d/%m/%Y')}"
        righe.append(f"")
        righe.append(f"{nome_p} ({intervallo}):")
        righe.append(f"   Entrate: {_fmt_it(dati['entrate'])}€   Uscite: {_fmt_it(dati['uscite'])}€")
        cat_top = dict(sorted(dati["categorie"].items(), key=lambda kv: kv[1], reverse=True)[:5])
        if cat_top:
            dettaglio_cat = ", ".join(f"{c} {_fmt_it(v)}€" for c, v in cat_top.items())
            righe.append(f"   Categorie principali: {dettaglio_cat}")
        if dati["conti"]:
            dettaglio_conti = ", ".join(
                f"{c} (entrate {_fmt_it(v['entrate'])}€, uscite {_fmt_it(v['uscite'])}€)"
                for c, v in dati["conti"].items())
            righe.append(f"   Per conto/persona: {dettaglio_conti}")
        if dati["categorie_per_conto"]:
            righe.append("   Per conto/persona, dettaglio categorie di uscita:")
            for conto_p, cats_p in dati["categorie_per_conto"].items():
                cats_p_ord = dict(sorted(cats_p.items(), key=lambda kv: kv[1], reverse=True))
                dettaglio_cats_p = ", ".join(f"{c} {_fmt_it(v)}€" for c, v in cats_p_ord.items())
                righe.append(f"      - {conto_p}: {dettaglio_cats_p}")
    righe.append("")
    righe.append("RIEPILOGO MESE PER MESE, CON CATEGORIE (usa questi dati per domande su un mese specifico "
                 "nominato per nome, es. \"a giugno\", \"a gennaio e febbraio\", indipendentemente dall'anno corrente):")
    for (anno_m, mese_m), dati_m in sorted(per_mese.items(), reverse=True):
        righe.append("")
        righe.append(f"{NOMI_MESI_IT[mese_m - 1].upper()} {anno_m}:")
        righe.append(f"   Entrate: {_fmt_it(dati_m['entrate'])}€   Uscite: {_fmt_it(dati_m['uscite'])}€")
        cat_top_m = dict(sorted(dati_m["categorie"].items(), key=lambda kv: kv[1], reverse=True))
        if cat_top_m:
            dettaglio_cat_m = ", ".join(f"{c} {_fmt_it(v)}€" for c, v in cat_top_m.items())
            righe.append(f"   Categorie: {dettaglio_cat_m}")
        if dati_m["conti"]:
            dettaglio_conti_m = ", ".join(
                f"{c} (entrate {_fmt_it(v['entrate'])}€, uscite {_fmt_it(v['uscite'])}€)"
                for c, v in dati_m["conti"].items())
            righe.append(f"   Per conto/persona: {dettaglio_conti_m}")
        if dati_m["categorie_per_conto"]:
            righe.append("   Per conto/persona, dettaglio categorie di uscita:")
            for conto_pm, cats_pm in dati_m["categorie_per_conto"].items():
                cats_pm_ord = dict(sorted(cats_pm.items(), key=lambda kv: kv[1], reverse=True))
                dettaglio_cats_pm = ", ".join(f"{c} {_fmt_it(v)}€" for c, v in cats_pm_ord.items())
                righe.append(f"      - {conto_pm}: {dettaglio_cats_pm}")
    righe.append("")
    righe.append("TOTALI STORICO COMPLETO:")
    righe.append(f"   Entrate totali: {_fmt_it(e_tot_all)}€")
    righe.append(f"   Uscite totali:  {_fmt_it(u_tot_all)}€")
    righe.append(f"   Saldo movimenti (entrate - uscite): {_fmt_it(e_tot_all - u_tot_all)}€")
    righe.append("")
    righe.append("TOTALI ULTIMI 365 GIORNI:")
    righe.append(f"   Entrate: {_fmt_it(e_tot_365)}€")
    righe.append(f"   Uscite:  {_fmt_it(u_tot_365)}€")
    righe.append("")
    righe.append("USCITE PER CATEGORIA (storico completo):")
    if cat_ordinate:
        for c, v in cat_ordinate.items():
            righe.append(f"   - {c:.<28} {_fmt_it(v):>12}€")
    else:
        righe.append("   Nessuna uscita registrata.")
    righe.append("")
    righe.append("USCITE PER METODO DI PAGAMENTO (storico completo):")
    if metodo_ordinati:
        for m, v in metodo_ordinati.items():
            righe.append(f"   - {m:.<28} {_fmt_it(v):>12}€")
    else:
        righe.append("   Nessun dato disponibile.")
    righe.append("")
    righe.append("MOVIMENTI PER CONTO (storico completo):")
    if per_conto:
        for c, vals in per_conto.items():
            righe.append(f"   - {c}: entrate {_fmt_it(vals['entrate'])}€ / uscite {_fmt_it(vals['uscite'])}€")
    else:
        righe.append("   Nessun movimento associato a un conto.")

    try:
        if os.path.exists(PORTAFOGLIO_BANCARIO):
            with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as f:
                db = json.load(f)
        else:
            db = {}
    except Exception:
        db = {}

    conti = db.get("conti", []) if isinstance(db, dict) else []
    righe.append("")
    righe.append("CONTI REGISTRATI NEL PORTAFOGLIO BANCARIO:")
    if conti:
        for c in conti:
            try:
                saldo_eff = self._saldo_effettivo(c, db)
            except Exception:
                saldo_eff = c.get("saldo", 0.0)
            principale = " (conto principale)" if c.get("principale") else ""
            righe.append(f"   - {c.get('nome', '?')} [{c.get('tipo', 'n/d')}]{principale}: "
                         f"saldo attuale {_fmt_it(float(saldo_eff))}€")
    else:
        righe.append("   Nessun conto registrato.")
    righe.append(f"   Saldo fisico (contante) dichiarato: {_fmt_it(float(db.get('saldo_fisico', 0.0)))}€")

    id_a_nome_conti = {c.get("id"): c.get("nome", "?") for c in conti}
    righe += _blocco_trasferimenti(
        db.get("trasferimenti", []) if isinstance(db, dict) else [],
        id_a_nome_conti, _fmt_it)

    righe += _blocco_spese_pianificate(
        self.piani_puliti() if hasattr(self, "piani_puliti") else _leggi_json(getattr(_app, 'PIANIFICA_FILE', None)),
        _fmt_it
    )
    righe += _blocco_scadenze_ricorrenti_mese(self, oggi, _fmt_it)
    righe += _blocco_fondo_pensione(_leggi_json(getattr(_app, 'PENSIONE_FILE', None)), _fmt_it)
    righe += _blocco_fondo_risparmio(_leggi_json(getattr(_app, 'FR_FILE', None)), _fmt_it)
    righe += _blocco_immobili(_leggi_json(getattr(_app, 'IMMOBIL_FILE', None)), _fmt_it)
    righe += _blocco_fairshare(_leggi_json(getattr(_app, 'FAIRSHARE_STATE', None)), _fmt_it)
    righe += _blocco_veicoli(_leggi_json(getattr(_app, 'VEICOLI_FILE', None)), _fmt_it)
    righe += _blocco_utenze(_leggi_json(getattr(_app, 'UTENZE_DB', None)), _fmt_it)
    righe += _blocco_studio(
        _leggi_json(getattr(_app, 'STUDIO_CLIENTI', None)),
        _leggi_json(getattr(_app, 'STUDIO_APPUNTAMENTI', None)),
        _leggi_json(getattr(_app, 'STUDIO_FATTURE', None)),
        _leggi_json(getattr(_app, 'STUDIO_CASSA', None)),
        _leggi_json(getattr(_app, 'STUDIO_MAGAZZINO', None)),
        _fmt_it)
    righe += _blocco_promemoria(_leggi_json(getattr(_app, 'PROMEMORIA_FILE', None)))
    righe += _blocco_schedule(_leggi_json(getattr(_app, 'SCHEDULE_FILE', None)))
    righe += _blocco_rubrica(_leggi_json(getattr(_app, 'DATI_FILE', None)))
    righe += _blocco_supermercati(_leggi_json(getattr(_app, 'SUPERMERCATI_DB', None)))

    return "\n".join(righe)

def chiedi_ia_database(self):
    import __main__ as _app
    API_KEY = _app.API_KEY
    GEMINI = _app.GEMINI
    genai_client = _app.genai_client
    PATH_LOCALE = _app.PATH_LOCALE
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    EXPORT_FILES = getattr(_app, 'EXPORT_FILES', None)
    _fmt_it = _app._fmt_it
    nome_app = os.path.basename(PATH_LOCALE)

    if not API_KEY:
        self.show_custom_warning("Configurazione AI Necessaria",
            "Questa funzione richiede una chiave API Gemini (gratuita).\n\n"
            "Vai nella sezione Impostazioni e clicca sul pulsante 'Ottieni'.\n")
        return

    if hasattr(self, '_chiedi_ia_win') and self._chiedi_ia_win.winfo_exists():
        self._chiedi_ia_win.lift()
        self._chiedi_ia_win.focus_force()
        return

    if not hasattr(self, '_chiedi_ia_storico'):
        self._chiedi_ia_storico = [] 

    popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    self._chiedi_ia_win = popup
    popup.withdraw()
    popup.title(f"Chiedi al Database — Gemini AI — {nome_app}")
    w, h = 1300, 660
    x = self.winfo_rootx() + (self.winfo_width()  // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    popup.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")
    popup.minsize(1300, 660)
    popup.resizable(True, True)
    popup.bind("<Escape>", lambda e: popup.destroy())

    hdr = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    hdr.pack(fill="x", padx=18, pady=(14, 4))
    img_ia = self.icone_gui.get("ia") or self.icone_gui.get("report")
    ttk.Label(hdr, image=img_ia, text="  Chiedi al Database — Assistente Gemini",
              compound="left", style="Header.TLabel",
              font=("Segoe UI", 12, "bold")).pack(side="left")

    tk.Label(popup, text="Fai qualsiasi domanda statistica o di ricerca su spese, entrate, categorie, conti, veicoli,\n"
                         "immobili, fondo pensione, fondo risparmio, spese pianificate e altri dati dell'app:",
             bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
             font=("Segoe UI", 9, "bold"), justify="left").pack(anchor="w", padx=18, pady=(6, 2))

    ttk.Separator(popup, orient="horizontal").pack(fill="x", padx=18, pady=(0, 6))

    res_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    res_frame.pack(fill="both", expand=True, padx=18, pady=(0, 6))
    res_scroll = ttk.Scrollbar(res_frame, orient="vertical", style="Vertical.TScrollbar")
    res_scroll.pack(side="right", fill="y")
    text_area = tk.Text(res_frame, bg=self.COLOR_WHITE, fg=self.COLOR_BLACK,
                font=("Consolas", 10), wrap="word", height=21,
                yscrollcommand=res_scroll.set,
                borderwidth=0, highlightthickness=1,
                highlightbackground=self.COLOR_HIGHLIGHT,
                padx=14, pady=12, state="disabled")
    text_area.pack(side="left", fill="both", expand=True)
    res_scroll.config(command=text_area.yview)
    text_area.tag_configure("domanda", font=("Segoe UI", 10, "bold"), foreground=self.COLOR_HIGHLIGHT)
    text_area.tag_configure("risposta", font=("Consolas", 10), foreground=self.COLOR_BLACK)

    def _stampa_in_area(tag, testo):
        text_area.config(state="normal")
        text_area.insert("end", testo + "\n", tag)
        text_area.config(state="disabled")
        text_area.see("end")

    if self._chiedi_ia_storico:
        for tag, testo in self._chiedi_ia_storico:
            _stampa_in_area(tag, testo)
    else:
        _stampa_in_area("risposta",
            "Scrivi una domanda qui sotto, ad esempio:\n"
            "  - Quanto ho speso in totale il mese scorso?\n"
            "  - Qual è la categoria dove spendo di più?\n"
            "  - Che conti ho e qual è il saldo di ciascuno?\n"
            "  - Ci sono spese pianificate in corso?\n"
            "  - Quanto ho versato nel fondo pensione?\n"
            "  - A che punto è il fondo risparmio rispetto all'obiettivo?\n"
            "  - Quanto ho speso per i veicoli quest'anno?\n"
            "  - Quali immobili ho e quanto rendono?\n")

    input_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    input_frame.pack(fill="x", padx=18, pady=(0, 4))
    in_scroll = ttk.Scrollbar(input_frame, orient="vertical")
    in_scroll.pack(side="right", fill="y")
    entry_domanda = tk.Text(input_frame, height=3,
                       bg=self.COLOR_WHITE, fg=self.COLOR_BLACK,
                       font=("Segoe UI", 10), wrap="word",
                       yscrollcommand=in_scroll.set,
                       borderwidth=0, highlightthickness=1,
                       highlightbackground=self.COLOR_HIGHLIGHT,
                       padx=8, pady=6)
    entry_domanda.pack(side="left", fill="x", expand=True)
    in_scroll.config(command=entry_domanda.yview)

    _placeholder = "Scrivi qui la tua domanda sul database (statistiche, conti, categorie, ricerche...)  —  Invio per inviare, Shift+Invio per andare a capo"
    entry_domanda.insert("1.0", _placeholder)

    def _clear_placeholder(event=None):
        if entry_domanda.get("1.0", "end").strip() == _placeholder:
            entry_domanda.delete("1.0", "end")
    entry_domanda.bind("<FocusIn>", _clear_placeholder)
    entry_domanda.focus_set()

    run_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    run_frame.pack(fill="x", padx=18, pady=(0, 6))
    img_run = self.icone_gui.get("cerca") or self.icone_gui.get("sync")
    btn_chiedi = ttk.Label(run_frame, text=" Chiedi a Gemini", image=img_run, compound="left",
                          cursor="hand2", background=self.COLOR_WIDGET_BG,
                          foreground=self.COLOR_HIGHLIGHT,
                          font=("Segoe UI", 10, "bold"), padding=(12, 5))
    btn_chiedi.pack(side="left")
    lbl_stato = tk.Label(run_frame, text="", bg=self.COLOR_TOPLEVEL,
                          fg=self.COLOR_HIGHLIGHT, font=("Segoe UI", 9))
    lbl_stato.pack(side="left", padx=10)

    ttk.Separator(popup, orient="horizontal").pack(fill="x", padx=18, pady=(0, 6))
    bot_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    bot_frame.pack(side="bottom", fill="x", padx=18, pady=(0, 14))

    def _get_testo_area():
        return text_area.get("1.0", "end").strip()

    def anteprima_esporta():
        testo = _get_testo_area()
        if not testo:
            self.show_toast("Nessun testo da esportare.")
            return
        if hasattr(anteprima_esporta, '_win') and anteprima_esporta._win.winfo_exists():
            anteprima_esporta._win.lift()
            anteprima_esporta._win.focus_force()
            return
        prev_win = tk.Toplevel(popup, bg=self.COLOR_TOPLEVEL)
        anteprima_esporta._win = prev_win
        prev_win.withdraw()
        prev_win.title("Esportazione — Chiedi al Database")
        prev_win.bind("<Escape>", lambda e: prev_win.destroy())
        prev_win.transient(popup)
        def centra():
            w_a, h_a = 1300, 660
            x = popup.winfo_rootx() + (popup.winfo_width() // 2) - (w_a // 2)
            y = popup.winfo_rooty() + (popup.winfo_height() // 2) - (h_a // 2)
            prev_win.geometry(f"{w_a}x{h_a}+{x}+{y}")
            prev_win.minsize(w_a, h_a)
            prev_win.deiconify()
        prev_win.after(0, centra)
        def do_pdf():
            f_path = filedialog.asksaveasfilename(
                defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
                initialdir=EXPORT_FILES, initialfile="Chiedi_IA_Database.pdf",
                confirmoverwrite=False, parent=prev_win)
            if f_path:
                try:
                    import pymupdf as fitz
                    doc = fitz.open()
                    page_w, page_h = 842, 595
                    margin = 30
                    font_size = 7
                    line_height = font_size + 2
                    page = doc.new_page(width=page_w, height=page_h)
                    y = margin
                    for line in testo.split("\n"):
                        if y > (page_h - margin):
                            page = doc.new_page(width=page_w, height=page_h)
                            y = margin
                        page.insert_text((margin, y), line, fontname="cour", fontsize=font_size)
                        y += line_height
                    doc.save(f_path); doc.close()
                    self.show_toast("PDF salvato.")
                except Exception as ex:
                    self.show_custom_warning("Errore PDF", str(ex))
        def do_txt():
            f_path = filedialog.asksaveasfilename(
                defaultextension=".txt", filetypes=[("TXT", "*.txt")],
                initialdir=EXPORT_FILES, initialfile="Chiedi_IA_Database.txt",
                confirmoverwrite=False, parent=prev_win)
            if f_path:
                with open(f_path, "w", encoding="utf-8") as fh:
                    fh.write(testo)
                self.show_toast("File TXT salvato.")
        txt_area_frame = tk.Frame(prev_win, bg=self.COLOR_TOPLEVEL)
        txt_area_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        v_scroll = ttk.Scrollbar(txt_area_frame, orient="vertical")
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        txt_area = tk.Text(txt_area_frame, font=("Courier New", 9),
                           bg=self.COLOR_WHITE, fg=self.COLOR_BLACK,
                           wrap="none",
                           yscrollcommand=v_scroll.set)
        txt_area.pack(fill=tk.BOTH, expand=True)
        v_scroll.config(command=txt_area.yview)
        txt_area.insert("1.0", testo)
        txt_area.config(state="disabled")
        bf = tk.Frame(prev_win, bg=self.COLOR_TOPLEVEL)
        bf.pack(fill=tk.X, pady=8)
        for lbl_txt, ico, cmd in [(" PDF", "salva", do_pdf), (" TXT", "salva", do_txt),
                              (" Stampa", "stampa", lambda: self._stampa_lista_diretta(
                                  testo, self.show_custom_warning))]:
            img = self.icone_gui.get(ico)
            b = ttk.Label(bf, compound="left", image=img, text=lbl_txt,
                          background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                          cursor="hand2", padding=(10, 5))
            b.pack(side=tk.LEFT, padx=5)
            b.bind("<Button-1>", lambda e, c=cmd: c())
        img_c = self.icone_gui.get("chiudi")
        bc = ttk.Label(bf, compound="left", image=img_c, text=" Chiudi",
                       background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                       cursor="hand2", padding=(10, 5))
        bc.pack(side=tk.RIGHT, padx=10)
        bc.bind("<Button-1>", lambda e: prev_win.destroy())

    def nuova_conversazione():
        self._chiedi_ia_storico = []
        text_area.config(state="normal")
        text_area.delete("1.0", "end")
        text_area.config(state="disabled")
        _stampa_in_area("risposta", "Nuova conversazione iniziata. Scrivi una domanda qui sotto.")

    for txt, ico_k, cmd, side in [
        (" Esporta", "salva",  anteprima_esporta,   "left"),
        (" Nuova",  "reset",  nuova_conversazione, "left"),
        (" Chiudi", "chiudi", popup.destroy,      "right"),
    ]:
        img = self.icone_gui.get(ico_k)
        b = ttk.Label(bot_frame, text=txt, image=img, compound="left",
                      cursor="hand2", background=self.COLOR_WIDGET_BG,
                      foreground=self.TEXT_COLOR, padding=(10, 4))
        b.pack(side=side, padx=4)
        b.bind("<Button-1>", lambda e, c=cmd: c())

    _stato_richiesta = {"in_corso": False}

    def invia_domanda(event=None):
        if _stato_richiesta["in_corso"]:
            self.show_toast("Attendi la risposta precedente...", duration=1500)
            return "break"
        domanda = entry_domanda.get("1.0", "end").strip()
        if not domanda or domanda == _placeholder:
            self.show_toast("Scrivi prima una domanda.")
            return "break"

        _stato_richiesta["in_corso"] = True
        entry_domanda.delete("1.0", "end")
        entry_domanda.config(state="disabled")

        cvs, spinner_stop = crea_spinner_animato(run_frame, self.COLOR_TOPLEVEL, size=18, tick_ms=30)
        cvs.pack(side="left", padx=(10, 0))
        lbl_stato.config(text="Gemini sta pensando...")

        riga_domanda = f"\nTU: {domanda}"
        _stampa_in_area("domanda", riga_domanda)
        self._chiedi_ia_storico.append(("domanda", riga_domanda))

        cronologia_precedente = [t for _, t in self._chiedi_ia_storico[-9:-1]]
        cronologia_txt = ""
        if cronologia_precedente:
            cronologia_txt = "CONVERSAZIONE PRECEDENTE (per mantenere il contesto):\n" + \
                              "\n".join(cronologia_precedente) + "\n\n"

        def _componi_prompt(contesto):
            return f"""
        Sei un assistente esperto di finanza personale integrato nell'app {nome_app}.
        Rispondi ESCLUSIVAMENTE sulla base dei dati del database forniti sotto. Se un dato
        richiesto non è disponibile nel contesto, dillo chiaramente invece di inventare numeri.

        DATI DEL DATABASE (spese, conti, trasferimenti tra conti, e tutti i moduli collegati: veicoli,
        immobili, fondo pensione, fondo risparmio, spese pianificate, fairshare, utenze, studio,
        promemoria, rubrica, automazioni — se una sezione non compare qui sotto significa che quel
        modulo non ha ancora dati registrati):
        {contesto}

        {cronologia_txt}DOMANDA DELL'UTENTE:
        {domanda}

        REGOLE DI RISPOSTA:
        1. NON usare simboli Markdown (*, #, -, `, []).
        2. Usa il minuscolo per il corpo del testo. Usa le MAIUSCOLE esclusivamente per i titoli di sezione, se servono.
        3. Scrivi tutti gli importi in formato italiano (virgola come separatore decimale, punto per le migliaia), es. 1.234,56€.
        4. Sii diretto, concreto e sintetico. Se utile, aggiungi numeri e percentuali a supporto.
        5. Se la domanda contiene riferimenti temporali relativi (oggi, ieri, questa settimana, settimana
           scorsa, questo mese, mese scorso, quest'anno, anno scorso), usa SEMPRE i dati della sezione
           "RIEPILOGO PER PERIODI TEMPORALI" già calcolata sopra: non dire mai che il dato non è disponibile
           se il periodo richiesto corrisponde a uno di quelli elencati.
        6. Usa la data odierna indicata in "OGGI È" come riferimento per capire cosa intende l'utente
           quando parla di periodi relativi non elencati esplicitamente (es. "negli ultimi 3 giorni").
        6b. Se la domanda nomina uno o più mesi specifici per nome, con o senza anno (es. "a giugno",
            "a gennaio e febbraio", "settembre 2025 vs settembre 2026"), usa SEMPRE i dati della
            sezione "RIEPILOGO MESE PER MESE, CON CATEGORIE": non dire mai che il dato non è disponibile
            se il mese/anno richiesto compare in quella sezione. Se non viene indicato l'anno, usa il
            mese più recente disponibile nel database con quel nome, a meno che il contesto della
            domanda suggerisca diversamente. Se la domanda chiede di CONFRONTARE o PARAGONARE più mesi
            (es. "confronta", "rispetto a", "vs", "differenza tra"), riporta i valori di ciascun mese
            separatamente e calcola la differenza; NON sommarli insieme. Solo se la domanda chiede
            esplicitamente un TOTALE COMPLESSIVO su più mesi (es. "somma", "totale di gennaio e
            febbraio insieme"), somma i valori dei mesi indicati.
        6c. Se la domanda chiede quanto ha speso/incassato una persona o un conto specifico (i conti
            possono essere intestati a nomi di persone) in un periodo relativo o in un mese/anno
            nominato, cerca il nome nella riga "Per conto/persona:" della sezione periodo o mese
            corrispondente: quel valore è già filtrato per quel conto/persona in quel periodo, non
            confonderlo con il totale storico dello stesso conto riportato altrove.
        7. Prima di dire che un dato non è disponibile, controlla TUTTE le sezioni del contesto (spese,
           conti, trasferimenti tra conti, veicoli, immobili, fondo pensione, fondo risparmio, spese
           pianificate, fairshare, utenze, studio, promemoria, rubrica, automazioni): l'informazione
           richiesta potrebbe trovarsi in una sezione diversa da quella più ovvia. Dichiara l'assenza del
           dato solo se davvero non compare in nessuna sezione.
        6d. Se la domanda chiede le spese/uscite di una persona o conto specifico SUDDIVISE PER CATEGORIA
            (es. "spese di federico per categoria", "dove ha speso federico"), cerca la riga "Per
            conto/persona, dettaglio categorie di uscita:" nella sezione periodo o mese corrispondente:
            lì trovi l'elenco delle categorie con importo, già filtrato per quel conto/persona. Usa
            SEMPRE questo dato quando disponibile, prima di dire che il dettaglio non è disponibile.
        8. I trasferimenti tra conti (sezione "TRASFERIMENTI TRA CONTI") NON sono entrate né uscite: sono
           spostamenti di denaro tra i conti dell'utente e non vanno mai sommati o confusi con i totali di
           entrate/uscite delle altre sezioni.
        """

        def _chiedi_a_gemini(prompt):
            try:
                client = genai_client.Client(api_key=API_KEY)
                response = client.models.generate_content(model=GEMINI, contents=prompt)
                risposta = response.text if response.text else "Nessuna risposta generata."
            except Exception as err:
                testo_err = str(err)
                if "RESOURCE_EXHAUSTED" in testo_err or "429" in testo_err:
                    if "PerDay" in testo_err:
                        m_quota = re.search(r"quotaValue\W+(\d+)", testo_err)
                        dettaglio_quota = f" ({m_quota.group(1)} richieste/giorno)" if m_quota else ""
                        risposta = (f"quota giornaliera gratuita di gemini esaurita{dettaglio_quota} "
                                    f"per il modello {GEMINI}. riprova domani, oppure attiva la fatturazione "
                                    "sulla tua chiave API su ai.google.dev per aumentare il limite.")
                    else:
                        risposta = ("hai fatto troppe richieste in poco tempo (limite di gemini per minuto "
                                    "raggiunto). attendi qualche secondo e riprova.")
                else:
                    risposta = f"ERRORE API GEMINI:\n{testo_err}"
            return risposta

        def _run():
            try:
                contesto = _costruisci_contesto_database(self, _app, _fmt_it)
                prompt = _componi_prompt(contesto)
            except Exception as err:
                risposta = f"ERRORE nella lettura dei dati del database:\n{err}"
            else:
                risposta = _chiedi_a_gemini(prompt)

            def _fine():
                _stato_richiesta["in_corso"] = False
                riga_risposta = f"GEMINI: {risposta}\n"
                self._chiedi_ia_storico.append(("risposta", riga_risposta))
                try:
                    spinner_stop()
                    cvs.destroy()
                except Exception:
                    pass
                if not popup.winfo_exists():
                    return
                lbl_stato.config(text="")
                if entry_domanda.winfo_exists():
                    entry_domanda.config(state="normal")
                    entry_domanda.focus_set()
                _stampa_in_area("risposta", riga_risposta)
            self.after(0, _fine)

        threading.Thread(target=_run, daemon=True).start()
        return "break"

    btn_chiedi.bind("<Button-1>", invia_domanda)
    entry_domanda.bind("<Return>", invia_domanda)
    entry_domanda.bind("<Shift-Return>", lambda e: None)

    popup.deiconify()
    popup.focus_set()

