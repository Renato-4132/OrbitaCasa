#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import uuid
import datetime

from moduli.modello_spesa import campo
from moduli.finanziamenti import (
    _num,
    _rata_francese,
    _medie_storico,
    _file_fin,
    _carica_fin,
    _salva_fin,
    _aggiungi_mesi,
    _mesi_residui,
    _eventi_validi,
    _piano_fin,
    _residuo_dopo,
    _serie,
    _data_it,
    _cronostoria,
    _status_fin,
    _fin_elenco,
    _fin_salva,
    _fin_elimina,
    _fin_var_aggiungi,
    _fin_var_elimina,
    MAX_FIN,
    MAX_VAR,
    TIPI_VAR,
)

MESI_ITA = ["", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
            "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
STRATEGIE = ("Mantieni Rata", "Ricalcola Rata")

def _vuoto(v):
    return v is None or str(v).strip() == ""


def _data_rata(oggi, n):
    m = (oggi.month + n - 1) % 12 + 1
    a = oggi.year + (oggi.month + n - 1) // 12
    return f"{min(oggi.day, 28):02d}-{m:02d}-{a}"

def _piano(capitale, mesi, tasso_mensile, spese, extra=0.0):
    oggi = datetime.date.today()
    righe = []
    debito = capitale
    if extra > 0:
        debito -= extra
        righe.append({"tipo": "extra", "label": "Ammortamento Extra", "rata": extra,
                      "cap": extra, "int": 0.0, "residuo": debito})
    rata_base = _rata_francese(debito, tasso_mensile, mesi)
    tot_cap, tot_int = extra, 0.0
    for n in range(1, mesi + 1):
        interessi = debito * tasso_mensile
        quota_cap = rata_base - interessi
        debito -= quota_cap
        tot_cap += quota_cap
        tot_int += interessi
        righe.append({"tipo": "rata", "label": f"Rata {n} ({_data_rata(oggi, n)})",
                      "rata": rata_base + spese, "cap": quota_cap, "int": interessi,
                      "residuo": debito if debito > 0.005 else 0.0})
    tot_pagato = tot_cap + tot_int + spese * mesi
    return {"righe": righe, "tot_cap": tot_cap, "tot_int": tot_int, "tot_pagato": tot_pagato,
            "rata_base": rata_base}

def _scenario(capitale, anni, tasso_annuo, spese, extra):
    tm = tasso_annuo / 100 / 12
    mesi = anni * 12
    debito = capitale - extra
    rata_base = _rata_francese(debito, tm, mesi)
    interessi = rata_base * mesi - debito
    return {"capitale": capitale, "anni": anni, "mesi": mesi, "tasso": tasso_annuo, "tm": tm,
            "spese": spese, "extra": extra, "rata_base": rata_base,
            "rata_totale": rata_base + spese, "interessi": interessi,
            "importo_totale": debito + interessi + spese * mesi + extra}

def _calcola_simulazioni(d):
    lista = d.get("scenari") or []
    out, base = [], None
    for i in range(6):
        s = lista[i] if i < len(lista) and isinstance(lista[i], dict) else {}
        if _vuoto(s.get("capitale")) or _vuoto(s.get("anni")) or _vuoto(s.get("tasso")):
            out.append({"ok": False, "vuoto": True})
            continue
        cap = _num(s.get("capitale"), -1)
        anni_f = _num(s.get("anni"), -1)
        tasso = _num(s.get("tasso"), -1)
        spese = _num(s.get("spese"), 0.0)
        extra = _num(s.get("extra"), 0.0)
        if (cap <= 0 or anni_f < 1 or tasso < 0 or cap > 500000 or anni_f > 35 or tasso > 35
                or spese < 0 or extra < 0):
            out.append({"ok": False, "errore": "Valori non validi: capitale 1–500.000 €, durata 1–35 anni, "
                                               "tasso 0–35 %, spese ed extra non negativi."})
            continue
        if extra > cap:
            out.append({"ok": False, "errore": "L'ammortamento extra non può essere maggiore del capitale."})
            continue
        anni = int(anni_f)
        sc = _scenario(cap, anni, tasso, spese, extra)
        if extra >= cap:
            out.append({"ok": False, "errore": "Con questo extra il debito è già estinto."})
            continue
        p = _piano(cap, sc["mesi"], sc["tm"], spese, extra)
        sc["piano"] = p
        sc["ok"] = True
        out.append(sc)
        if i == 0:
            base = sc
    for sc in out:
        if sc.get("ok"):
            sc["costo_cap_int"] = sc["capitale"] + sc["interessi"]
            sc["risparmio"] = (base["interessi"] - sc["interessi"]) if base else None
            sc["tm_pct"] = sc.pop("tm") * 100
    return {"ok": True, "scenari": out}

def _calcola_rata_sostenibile(d):
    rata_disp = _num(d.get("rata"), 0.0)
    anni_f = _num(d.get("anni"), 0.0)
    tasso = _num(d.get("tasso"), 0.0)
    spese = _num(d.get("spese"), 0.0)
    if rata_disp <= 0 or anni_f < 1 or tasso < 0:
        return {"ok": False, "errore": "Rata, durata e tasso devono essere valori positivi."}, 400
    if anni_f > 50 or tasso > 35:
        return {"ok": False, "errore": "Durata massima 50 anni, tasso massimo 35 %."}, 400
    rata_cap = rata_disp - spese
    if rata_cap <= 0:
        return {"ok": False, "errore": "La rata sostenibile deve essere maggiore delle spese mensili."}, 400
    anni = int(anni_f)
    mesi = anni * 12
    tm = tasso / 100 / 12
    if tm > 0:
        cap_max = rata_cap * (1 - (1 + tm) ** -mesi) / tm
    else:
        cap_max = rata_cap * mesi
    p = _piano(cap_max, mesi, tm, spese)
    return {"ok": True, "capitale_max": cap_max, "rata": rata_disp, "anni": anni, "mesi": mesi,
            "tasso": tasso, "spese": spese, "piano": p}, 200

def _calcola_killer(d):
    oggi = datetime.date.today()
    if _vuoto(d.get("residuo")) or _vuoto(d.get("mesi")) or _vuoto(d.get("tasso")):
        return {"ok": False, "errore": "Compila almeno Debito, Mesi e Tasso."}, 400
    residuo = _num(d.get("residuo"), 0.0)
    mesi_rim = int(_num(d.get("mesi"), 0.0))
    tasso = _num(d.get("tasso"), -1.0)
    rata_orig = _num(d.get("rata"), 0.0)
    extra_annuo = _num(d.get("extra_annuo"), 0.0)
    extra_subito = _num(d.get("extra_subito"), 0.0)
    try:
        mese_vers = int(_num(d.get("mese"), 12))
    except (TypeError, ValueError):
        mese_vers = 12
    strategia = d.get("strategia") if d.get("strategia") in STRATEGIE else "Ricalcola Rata"
    if (residuo <= 0 or mesi_rim <= 0 or tasso < 0 or residuo > 1000000 or mesi_rim > 600
            or tasso > 25 or extra_annuo < 0 or extra_subito < 0 or not 1 <= mese_vers <= 12):
        return {"ok": False, "errore": "Controlla i dati: debito 1–1.000.000 €, mesi 1–600, tasso 0–25 %, "
                                       "mese di versamento 1–12, importi non negativi."}, 400
    if extra_subito > residuo:
        return {"ok": False, "errore": "L'abbattimento iniziale non può superare il debito residuo."}, 400
    tm = tasso / 100 / 12
    if rata_orig <= residuo * tm + 0.01:
        return {"ok": False, "errore": "La rata è troppo bassa per coprire gli interessi mensili."}, 400

    interessi_standard = rata_orig * mesi_rim - residuo
    debito = residuo
    tot_vers = tot_int = risp_anno = 0.0
    rata_corr = rata_orig
    anticipo_fatto = extra_subito <= 0
    righe, annuali = [], []
    n = 0
    while debito > 0.01 and n < 600:
        n += 1
        m_rata = (oggi.month + n - 1) % 12 + 1
        data_str = _data_rata(oggi, n)
        if not anticipo_fatto and m_rata == mese_vers:
            abb = min(extra_subito, debito)
            debito -= abb
            tot_vers += abb
            righe.append({"tipo": "extra", "label": f"Anticipo ({data_str})", "rata": abb,
                          "cap": abb, "int": 0.0, "residuo": debito})
            anticipo_fatto = True
            if strategia == "Ricalcola Rata":
                m_res = mesi_rim - (n - 1)
                if m_res > 0:
                    rata_corr = _rata_francese(debito, tm, m_res)
        interessi = debito * tm
        tot_int += interessi
        risp_anno += rata_orig - rata_corr
        vers_extra = extra_annuo if m_rata == mese_vers else 0.0
        rata_mese = rata_corr
        if vers_extra > 0 and strategia == "Ricalcola Rata":
            m_res = mesi_rim - n
            if m_res > 0:
                dp = debito - (rata_corr - interessi)
                dn = max(0.0, dp - vers_extra)
                rata_corr = _rata_francese(dn, tm, m_res) if dn > 0 else 0.0
        abb_pot = (rata_mese - interessi) + vers_extra
        if abb_pot >= debito:
            vers_reale = debito + interessi
            abb_eff = debito
            debito = 0.0
        else:
            vers_reale = rata_mese + vers_extra
            abb_eff = abb_pot
            debito -= abb_eff
        tot_vers += vers_reale
        righe.append({"tipo": "extra" if vers_extra > 0 else "rata", "label": f"Rata {n} ({data_str})",
                      "rata": vers_reale, "cap": abb_eff, "int": interessi, "residuo": max(debito, 0.0)})
        if n % 12 == 0 or debito <= 0:
            annuali.append({"anno": (n + 11) // 12, "risparmio_rate": risp_anno,
                            "sforzo_netto": (extra_annuo - risp_anno) if extra_annuo > 0 else 0.0,
                            "anno_solare": oggi.year + (oggi.month + n - 1) // 12})
            risp_anno = 0.0
            if debito <= 0:
                break

    anno_f = oggi.year + (oggi.month + n - 1) // 12
    mese_f = (oggi.month + n - 1) % 12 + 1
    ultima = righe[-1] if righe else None
    return {"ok": True, "strategia": strategia, "mesi_estinzione": n,
            "mesi_risparmiati": mesi_rim - n, "termine": f"{MESI_ITA[mese_f]} {anno_f}",
            "anno_estinzione": anno_f, "tot_versato": tot_vers, "tot_interessi": tot_int,
            "interessi_senza": interessi_standard, "risparmio": max(0.0, interessi_standard - tot_int),
            "extra_subito": extra_subito, "extra_annuo": extra_annuo,
            "ultimo_versamento": ultima["rata"] if ultima else 0.0,
            "piano": {"righe": righe}, "annuali": annuali}, 200

def _sost_rata(capitale, tasso_pct, anni):
    n = round(anni * 12)
    r = tasso_pct / 100 / 12
    if n <= 0:
        return 0.0
    if r == 0:
        return capitale / n
    try:
        return capitale * r * (1 + r) ** n / ((1 + r) ** n - 1)
    except (ZeroDivisionError, OverflowError):
        return 0.0


def _sost_piano(capitale, tasso_pct, anni, stress_on, stress_delta, stress_anno):
    n = anni * 12
    piano, debito, tasso = [], capitale, tasso_pct
    rata = _sost_rata(debito, tasso, n / 12)
    for m in range(1, n + 1):
        if stress_on and m == stress_anno * 12 + 1:
            tasso = tasso_pct + stress_delta
            rata = _sost_rata(debito, tasso, (n - m + 1) / 12)
        interessi = debito * tasso / 100 / 12
        quota = min(rata - interessi, debito)
        debito = max(0.0, debito - quota)
        piano.append(rata)
    return piano

def _sost_righe(entrate0, spese0, capitale, tasso, anni, orizzonte, inflazione, crescita,
                stress_on, stress_delta, stress_anno):
    piano = _sost_piano(capitale, tasso, anni, stress_on, stress_delta, stress_anno)
    righe = []
    for y in range(orizzonte + 1):
        entrate = entrate0 * (1 + crescita / 100) ** y
        spese = spese0 * (1 + inflazione / 100) ** y
        if y == 0:
            rata_anno = piano[0] if piano else 0.0
        else:
            tratto = piano[(y - 1) * 12:min(y * 12, len(piano))]
            rata_anno = sum(tratto) / len(tratto) if tratto else 0.0
        residuo = entrate - spese - rata_anno
        pct = (rata_anno / entrate * 100) if entrate > 0 else 0.0
        stato = "r" if (residuo < 0 or pct >= 40) else ("y" if pct >= 30 else "g")
        righe.append({"anno": y, "entrate": entrate, "spese": spese, "rata": rata_anno,
                      "disponibile": entrate - spese, "residuo": residuo, "pct": pct, "stato": stato})
    return righe

def _calcola_sostenibilita(d):
    entrate0 = _num(d.get("entrate"), 0.0)
    spese0 = _num(d.get("spese"), 0.0)
    capitale = _num(d.get("capitale"), 0.0)
    tasso = _num(d.get("tasso"), 0.0)
    anni = int(max(1, min(50, _num(d.get("durata"), 1))))
    orizzonte = int(max(1, min(50, _num(d.get("orizzonte"), 1))))
    infl = _num(d.get("inflazione"), 0.0)
    crescita = _num(d.get("crescita"), 0.0)
    stress_on = bool(d.get("stress"))
    stress_delta = _num(d.get("stress_delta"), 0.0)
    stress_anno = int(max(1, _num(d.get("stress_anno"), 1)))
    err = []
    if not 0 < entrate0 <= 50000:
        err.append("le entrate nette mensili devono essere tra 1 e 50.000 €")
    if not 0 <= spese0 <= 50000:
        err.append("le spese fisse mensili devono essere tra 0 e 50.000 €")
    if not 0 < capitale <= 2000000:
        err.append("l'importo del finanziamento deve essere tra 1 e 2.000.000 €")
    if not 0 <= tasso <= 30:
        err.append("il tasso d'interesse annuo deve essere tra 0% e 30%")
    if not 0 <= infl <= 30:
        err.append("la crescita annua del costo della vita deve essere tra 0% e 30%")
    if not 0 <= crescita <= 30:
        err.append("la crescita annua del reddito deve essere tra 0% e 30%")
    if not 1 <= anni <= 35:
        err.append("la durata del finanziamento deve essere tra 1 e 35 anni")
    if not 1 <= orizzonte <= anni:
        err.append("l'orizzonte osservato deve essere tra 1 anno e la durata del piano")
    if stress_on:
        if not 0 <= stress_delta <= 20:
            err.append("il rialzo tassi stimato deve essere tra 0 e 20 punti percentuali")
        if not 1 <= stress_anno < anni:
            err.append("l'anno di partenza del rialzo tassi deve cadere prima della fine del piano")
    if err:
        return {"ok": False, "errore": "Correggi i seguenti campi: " + "; ".join(err) + "."}, 400
    righe = _sost_righe(entrate0, spese0, capitale, tasso, anni, orizzonte, infl, crescita,
                        stress_on, stress_delta, stress_anno)
    rank = {"g": 0, "y": 1, "r": 2}
    peggiore = max((r["stato"] for r in righe), key=lambda s: rank[s])
    return {"ok": True, "righe": righe, "peggiore": peggiore, "orizzonte": orizzonte,
            "rata_oggi": righe[0]["rata"], "pct_oggi": righe[0]["pct"], "pct_fine": righe[-1]["pct"],
            "residuo_oggi": righe[0]["residuo"], "residuo_fine": righe[-1]["residuo"]}, 200

def finanziamenti_web_calcola(self, d):
    if not isinstance(d, dict):
        return {"ok": False, "errore": "Richiesta non valida."}, 400
    try:
        tool = d.get("tool")
        if tool == "fin_elenco":
            return _fin_elenco(self), 200
        if tool == "fin_salva":
            return _fin_salva(d)
        if tool == "fin_elimina":
            return _fin_elimina(d)
        if tool == "fin_var_aggiungi":
            return _fin_var_aggiungi(d)
        if tool == "fin_var_elimina":
            return _fin_var_elimina(d)
        if tool == "simulazioni":
            return _calcola_simulazioni(d), 200
        if tool == "rata":
            return _calcola_rata_sostenibile(d)
        if tool == "killer":
            return _calcola_killer(d)
        if tool == "sostenibilita":
            return _calcola_sostenibilita(d)
        return {"ok": False, "errore": "Strumento sconosciuto."}, 400
    except (ValueError, OverflowError, ZeroDivisionError):
        return {"ok": False, "errore": "Controlla i dati inseriti."}, 400
    except Exception:
        return {"ok": False, "errore": "Errore di calcolo."}, 500

_PAGINA = r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>🧮 Mutui e Prestiti</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
    (function() {
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    })();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>

    :root {
        --bg:#050505; --surface:#0f0f0f; --surface2:#161616; --surface3:#1e1e1e;
        --border:rgba(255,255,255,0.07); --border-active:rgba(99,160,240,0.5);
        --gold:#c9a84c; --blue:#63a0f0; --green:#4caf82; --red:#e05a5a; --orange:#e8a23c;
        --text:#e8e8e8; --text-dim:#555; --text-mid:#888; --radius-lg:18px;
    }
    :root.light {
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --border-active:rgba(61,127,212,0.5);
        --gold:#b8902a; --blue:#3d7fd4; --green:#3a9068; --red:#cc3333; --orange:#c98314;
        --text:#1a1a1a; --text-dim:#999; --text-mid:#555;
    }
    * { box-sizing:border-box; margin:0; padding:0; }
    body { font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text); min-height:100vh; padding-bottom:100px; transition:background 0.3s,color 0.3s; }
    header { padding:14px 16px 12px; display:flex; align-items:center; justify-content:center; border-bottom:1px solid var(--border); background:rgba(5,5,5,0.95); backdrop-filter:blur(20px); position:sticky; top:0; z-index:100; }
    :root.light header { background:rgba(245,245,240,0.95); }
    .menu-btn { position:absolute; left:14px; top:50%; transform:translateY(-50%); background:var(--surface3); border:1px solid var(--border); color:var(--gold); width:36px; height:36px; border-radius:10px; font-size:1em; cursor:pointer; display:flex; align-items:center; justify-content:center; }
    .theme-toggle { position:absolute; right:14px; top:50%; transform:translateY(-50%); background:var(--surface3); border:1px solid var(--border); border-radius:8px; width:34px; height:34px; display:flex; align-items:center; justify-content:center; cursor:pointer; font-size:1em; }
    .nav-dropdown { position:absolute; top:calc(100% + 6px); left:10px; background:var(--surface2); border:1px solid var(--border); border-radius:var(--radius-lg); display:none; z-index:1000; width:270px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.7); }
    .nav-dropdown a { display:flex; align-items:center; gap:10px; padding:10px 16px; text-decoration:none; color:var(--text-mid); border-bottom:1px solid var(--border); font-size:0.87em; }
    .nav-dropdown a:last-child { border-bottom:none; }
    .nav-dropdown a:hover { background:var(--surface3); color:var(--text); }
    .nav-group-btn { display:flex; justify-content:space-between; align-items:center; width:100%; padding:8px 16px; background:none; border:none; font-family:inherit; color:var(--gold); font-size:0.7em; font-weight:700; letter-spacing:1px; text-transform:uppercase; cursor:pointer; opacity:0.85; }
    .nav-group-btn:hover { opacity:1; background:var(--surface3); }
    .nav-group-items { display:none; flex-direction:column; }
    .nav-group-items.open { display:flex; }
    .header-title { font-size:1em; font-weight:700; }
    main { padding:14px; max-width:760px; margin:0 auto; }
    .tabs { display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-bottom:14px; }
    .tab { background:var(--surface2); border:1px solid var(--border); color:var(--text-mid); border-radius:14px; padding:10px 8px; font-family:inherit; font-size:0.82em; font-weight:700; cursor:pointer; text-align:center; line-height:1.25; }
    .tab.on { background:var(--gold); border-color:var(--gold); color:#000; }
    .pannello { display:none; } .pannello.on { display:block; }
    .card { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-lg); padding:14px; margin-bottom:12px; }
    .card h3 { font-size:0.9em; color:var(--gold); margin-bottom:10px; }
    .nota { font-size:0.8em; color:var(--text-mid); line-height:1.45; margin-bottom:10px; }
    input, select { background:var(--surface3); border:1px solid var(--border); color:var(--text); border-radius:10px; padding:10px; font-family:inherit; font-size:1em; width:100%; }
    input:focus, select:focus { outline:none; border-color:var(--border-active); }
    input:disabled { opacity:0.4; }
    .campo { margin-bottom:10px; } .campo label { display:block; font-size:0.76em; color:var(--text-mid); margin-bottom:4px; }
    .griglia { display:grid; grid-template-columns:repeat(auto-fit,minmax(135px,1fr)); gap:0 10px; }
    .chk { display:flex; align-items:center; gap:10px; color:var(--text-mid); font-size:0.88em; margin:4px 0 10px; }
    .chk input { width:20px; height:20px; flex:none; }
    .btns { display:grid; grid-template-columns:2fr 1fr; gap:8px; margin-top:6px; }
    .btn { display:block; width:100%; padding:12px; border-radius:12px; border:1px solid var(--border); background:var(--surface3); color:var(--text); font-family:inherit; font-size:0.95em; font-weight:700; cursor:pointer; }
    .btn.verde { background:var(--green); border-color:var(--green); color:#fff; }
    .btn.mini { width:auto; display:inline-block; padding:7px 12px; font-size:0.8em; margin:8px 6px 0 0; }
    details.sc { border:1px solid var(--border); border-radius:12px; margin-bottom:8px; background:var(--surface2); }
    details.sc > summary { padding:10px 12px; cursor:pointer; font-weight:700; font-size:0.9em; list-style:none; display:flex; justify-content:space-between; }
    details.sc > summary::after { content:'▸'; color:var(--text-mid); } details.sc[open] > summary::after { content:'▾'; }
    details.sc > div { padding:2px 12px 6px; }
    .scroll { overflow-x:auto; -webkit-overflow-scrolling:touch; border:1px solid var(--border); border-radius:12px; margin-top:8px; max-height:520px; overflow-y:auto; }
    table { border-collapse:collapse; width:100%; font-size:0.8em; white-space:nowrap; }
    th { position:sticky; top:0; background:var(--surface3); color:var(--text-mid); font-weight:700; text-align:right; padding:8px 10px; z-index:1; }
    td { padding:7px 10px; text-align:right; border-top:1px solid var(--border); }
    th:first-child, td:first-child { text-align:left; }
    tr.extra td { background:rgba(99,160,240,0.14); } tr.tot td { font-weight:800; border-top:2px solid var(--border-active); }
    tr.g td:last-child { color:var(--green); } tr.y td:last-child { color:var(--orange); } tr.r td:last-child { color:var(--red); }
    .kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:8px; margin:10px 0; }
    .kpi { background:var(--surface2); border:1px solid var(--border); border-radius:12px; padding:10px; }
    .kpi .e { font-size:0.7em; color:var(--text-mid); font-weight:700; text-transform:uppercase; letter-spacing:.5px; }
    .kpi .v { font-size:1.05em; font-weight:800; margin-top:3px; overflow-wrap:anywhere; }
    .verdetto { border-radius:12px; padding:12px; margin-bottom:10px; font-size:0.88em; line-height:1.5; border:1px solid currentColor; }
    .verdetto b { display:block; font-size:1.1em; margin-bottom:4px; }
    .verdetto.g { color:var(--green); } .verdetto.y { color:var(--orange); } .verdetto.r { color:var(--red); }
    .pos { color:var(--green); } .neg { color:var(--red); }
    .riepilogo { font-size:0.84em; line-height:1.6; color:var(--text-mid); white-space:pre-line; margin-top:10px; }
    .grafico { overflow-x:auto; margin-top:8px; }
    #msg { position:fixed; left:50%; bottom:30px; transform:translateX(-50%); background:var(--surface2); border:1px solid var(--border-active); padding:10px 16px; border-radius:12px; font-weight:700; font-size:0.9em; display:none; z-index:300; max-width:90vw; text-align:center; }
    #msg.err { border-color:var(--red); color:var(--red); }

    .prog { height:8px; border-radius:6px; background:var(--surface3); overflow:hidden; margin:8px 0 4px; }
    .prog > i { display:block; height:100%; background:var(--green); }
    .badge { display:inline-block; font-size:0.68em; font-weight:800; padding:2px 8px; border-radius:20px; border:1px solid currentColor; vertical-align:middle; margin-left:6px; }
    .badge.in_corso { color:var(--blue); } .badge.estinto { color:var(--green); } .badge.non_iniziato { color:var(--orange); }
    .finhead { display:flex; justify-content:space-between; align-items:flex-start; gap:8px; }
    .finhead h3 { margin:0; }
    .iconbtn { background:var(--surface3); border:1px solid var(--border); color:var(--text); border-radius:8px; padding:5px 9px; cursor:pointer; font-size:0.85em; margin-left:4px; }
    .griglia.larga { grid-template-columns:repeat(auto-fit,minmax(260px,1fr)); }
    select { text-overflow:clip; }
    .vuoto { text-align:center; color:var(--text-mid); padding:18px 10px; font-size:0.9em; }
</style>
<script>
    var $ = function(i) { return document.getElementById(i); };
    var ULTIMO = { sim: null, sost: null, killer: null, rata: null };
    var NF = new Intl.NumberFormat('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    var NF1 = new Intl.NumberFormat('it-IT', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
    function eur(v) { return NF.format(v == null ? 0 : v) + ' €'; }
    function pct(v, d) { return (d === 0 ? Math.round(v).toLocaleString('it-IT') : NF.format(v)) + ' %'; }
    function pct1(v) { return NF1.format(v) + ' %'; }
    function esc(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function(c) {
            return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; });
    }
    function msg(t, err) {
        var m = $('msg'); m.textContent = t; m.className = err ? 'err' : ''; m.style.display = 'block';
        clearTimeout(msg._t); msg._t = setTimeout(function() { m.style.display = 'none'; }, err ? 5000 : 2200);
    }
    function applyTheme(t) {
        const root = document.documentElement, btn = $('themeBtn');
        if (t === 'light') { root.classList.add('light'); if (btn) btn.textContent = '🌙'; }
        else               { root.classList.remove('light'); if (btn) btn.textContent = '☀️'; }
    }
    function toggleTheme() {
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next); applyTheme(next);
    }
    function toggleNavGroup(btn, ev) {
        if (ev) ev.stopPropagation();
        const items = btn.nextElementSibling, giaAperto = items.classList.contains('open');
        btn.closest('.nav-dropdown').querySelectorAll('.nav-group-items.open').forEach(function(el) {
            el.classList.remove('open'); el.previousElementSibling.querySelector('.nav-arrow').textContent = '▶';
        });
        if (!giaAperto) { items.classList.add('open'); btn.querySelector('.nav-arrow').textContent = '▼'; }
    }
    function toggleMenu() { const m = $('extraMenu'); m.style.display = m.style.display === 'block' ? 'none' : 'block'; }
    document.addEventListener('click', function(e) {
        const menu = $('extraMenu'), btn = document.querySelector('.menu-btn');
        if (menu && menu.style.display === 'block' && !menu.contains(e.target) && e.target !== btn) menu.style.display = 'none';
    });

    async function calcola(corpo) {
        try {
            var res = await fetch('/api/finanziamenti/calcola', { method: 'POST',
                headers: {'Content-Type':'application/json'}, body: JSON.stringify(corpo) });
            if (res.status === 401 || res.redirected) { location.reload(); return null; }
            return await res.json();
        } catch (e) { return { ok: false, errore: 'Server non raggiungibile.' }; }
    }
    function val(id) { return $(id).value; }

    function vaiTab(nome) {
        document.querySelectorAll('.tab').forEach(function(t) { t.classList.toggle('on', t.dataset.t === nome); });
        document.querySelectorAll('.pannello').forEach(function(p) { p.classList.toggle('on', p.id === 'p_' + nome); });
        try { sessionStorage.setItem('fin_tab', nome); } catch (e) {}
    }


    var FIN = null;
    var STATI = { in_corso: 'In corso', estinto: 'Estinto', non_iniziato: 'Da iniziare' };
    function graficoFin(serie) {
        var n = serie.length, W = Math.max(300, n * 34 + 20), H = 170, pt = 18, pb = 24, pl = 8;
        var max = Math.max.apply(null, serie.map(function(x) { return x.residuo; })) || 1;
        var cw = (W - pl * 2) / n, s = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="' + W + '" height="' + H + '" role="img" aria-label="Debito residuo anno per anno">';
        serie.forEach(function(x, i) {
            var h = (x.residuo / max) * (H - pt - pb), x0 = pl + i * cw + cw * 0.15, w = cw * 0.7;
            s += '<rect x="' + x0 + '" y="' + (H - pb - h) + '" width="' + w + '" height="' + h + '" rx="2" fill="var(--blue)"><title>' + (i === 0 ? 'Oggi' : x.anno_solare) + ': ' + eur(x.residuo) + '</title></rect>' +
                 '<text x="' + (x0 + w / 2) + '" y="' + (H - 8) + '" text-anchor="middle" font-size="9" fill="var(--text-mid)">' + (i === 0 ? 'oggi' : (n > 14 && i % 2 ? '' : "'" + String(x.anno_solare).slice(2))) + '</text>';
        });
        return s + '</svg>';
    }
    function tabProiezione(serie) {
        var h = '<div class="scroll"><table><thead><tr><th>Periodo</th><th>Debito residuo</th><th>Rate versate</th><th>di cui capitale</th><th>di cui interessi</th></tr></thead><tbody>';
        serie.forEach(function(x, i) {
            h += '<tr><td>' + (i === 0 ? 'Oggi' : 'Fine ' + x.anno_solare + ' (+' + i + ')') + '</td><td>' + eur(x.residuo) + '</td><td>' + (i ? eur(x.rata) : '-') + '</td><td>' + (i ? eur(x.cap) : '-') + '</td><td>' + (i ? eur(x.int) : '-') + '</td></tr>';
        });
        return h + '</tbody></table></div>';
    }

    var TIPI_VAR = { extra: 'Estinzione parziale', durata: 'Nuova durata residua', tasso: 'Nuovo tasso', rata: 'Nuova rata' };
    function descVar(v) {
        var d = v.data.split('-').reverse().join('-');
        if (v.tipo === 'extra') return d + ' · Estinzione parziale ' + eur(v.valore) + ' (' + (v.strategia === 'accorcia' ? 'mantieni rata, accorcia' : 'ricalcola rata') + ')';
        if (v.tipo === 'durata') return d + ' · Durata residua ' + Math.round(v.valore * 12) + ' mesi';
        if (v.tipo === 'prolunga') return d + ' · ' + (v.valore > 0 ? 'Prolungato di ' : 'Accorciato di ') + Math.round(Math.abs(v.valore) * 12) + ' mesi';
        if (v.tipo === 'tasso') return d + ' · Tasso ' + pct(v.valore);
        return d + ' · Rata ' + eur(v.valore);
    }

    function tabCrono(c) {
        var h = '<div class="scroll"><table><thead><tr><th>Data</th><th>Evento</th><th>Rata prima</th><th>Rata dopo</th><th>Debito dopo</th><th>Fine prevista</th><th>Interessi totali</th></tr></thead><tbody>';
        c.forEach(function(x) {
            var ev = x.tipo ? esc(descVar({ data: x.data.split('-').reverse().join('-'), tipo: x.tipo, valore: x.valore, strategia: x.strategia }).split(' · ').slice(1).join(' · ')) : '<b>' + esc(x.titolo) + '</b> · ' + esc(x.dettaglio);
            h += '<tr><td>' + esc(x.data) + '</td><td style="white-space:normal;min-width:170px">' + ev + '</td><td>' + (x.rata_prima == null ? '-' : eur(x.rata_prima)) + '</td><td>' + eur(x.rata_dopo) + '</td><td>' + eur(x.debito) + '</td><td>' + esc(x.fine) + '</td><td>' + eur(x.int_totali) + '</td></tr>';
        });
        return h + '</tbody></table></div>';
    }
    function boxVar(f) {
        var h = '<details class="sc"><summary>🔧 Variazioni (' + (f.variazioni || []).length + ')</summary><div>' +
            '<div class="nota">Registra estinzioni parziali, cambi di durata, tasso o rata: status e proiezioni vengono ricalcolati. Per ripartire da un estratto della banca crea un nuovo finanziamento con debito residuo, prossima rata e mesi rimasti.</div>';
        (f.variazioni || []).forEach(function(v, i) {
            h += '<div class="nota" style="display:flex;justify-content:space-between;gap:8px"><span>' + esc(descVar(v)) + '</span><button class="iconbtn" onclick="eliminaVar(\'' + esc(f.id) + '\',' + i + ')">🗑️</button></div>';
        });
        h += '<div class="griglia larga"><div class="campo"><label>Data</label><input type="date" id="vD_' + esc(f.id) + '"></div>' +
            '<div class="campo"><label>Tipo</label><select id="vT_' + esc(f.id) + '" onchange="aggiornaVar(\'' + esc(f.id) + '\')"><option value="extra">Estinzione parziale</option><option value="durata">Nuova durata residua (mesi)</option><option value="prolunga">Prolunga la durata</option><option value="accorcia">Accorcia la durata</option><option value="tasso">Cambio tasso</option><option value="rata">Cambio rata</option></select></div>' +
            '<div class="campo"><label id="vL_' + esc(f.id) + '">Importo versato (€)</label><input id="vV_' + esc(f.id) + '" inputmode="decimal" autocomplete="off"></div>' +
            '<div class="campo" id="vSW_' + esc(f.id) + '"><label>Dopo il versamento</label><select id="vS_' + esc(f.id) + '"><option value="ricalcola">Ricalcola la rata (durata uguale)</option><option value="accorcia">Mantieni la rata (finisce prima)</option></select></div></div>' +
            '<button class="btn verde mini" onclick="aggiungiVar(\'' + esc(f.id) + '\')">Aggiungi variazione</button></div></details>';
        return h;
    }
    function aggiornaVar(id) {
        var t = $('vT_' + id).value;
        $('vL_' + id).textContent = { extra: 'Importo versato (€)', durata: 'Durata residua (mesi)', prolunga: 'Mesi da aggiungere', accorcia: 'Mesi da togliere', tasso: 'Nuovo tasso annuo (%)', rata: 'Nuova rata (€)' }[t];
        $('vSW_' + id).style.display = t === 'extra' ? '' : 'none';
    }
    async function aggiungiVar(id) {
        var tipo = val('vT_' + id), v = val('vV_' + id);
        if (tipo === 'accorcia') { tipo = 'prolunga'; v = '-' + String(v).replace('-', '').trim(); }
        var r = await calcola({ tool: 'fin_var_aggiungi', id: id, data: val('vD_' + id), tipo: tipo, valore: v, strategia: val('vS_' + id) });
        if (!r || !r.ok) { msg((r && r.errore) || 'Errore.', true); return; }
        msg('Variazione aggiunta'); caricaFin();
    }
    async function eliminaVar(id, i) {
        if (!confirm('Eliminare questa variazione?')) return;
        var r = await calcola({ tool: 'fin_var_elimina', id: id, indice: i });
        if (!r || !r.ok) { msg((r && r.errore) || 'Errore.', true); return; }
        msg('Variazione eliminata'); caricaFin();
    }
    async function caricaFin() {
        var r = await calcola({ tool: 'fin_elenco' });
        if (!r || !r.ok) { msg((r && r.errore) || 'Errore di caricamento.', true); return; }
        FIN = r;
        var t = r.totali, h = '';
        if (r.finanziamenti.length) {
            var rosso = t.pct_entrate != null && t.pct_entrate >= 40, giallo = t.pct_entrate != null && t.pct_entrate >= 30;
            h = '<div class="card"><h3>📌 Status complessivo</h3><div class="kpis">' +
                '<div class="kpi"><div class="e">Finanziamenti attivi</div><div class="v">' + t.n_attivi + (t.n_estinti ? ' (+' + t.n_estinti + ' estinti)' : '') + '</div></div>' +
                '<div class="kpi"><div class="e">Debito residuo</div><div class="v">' + eur(t.residuo) + '</div></div>' +
                '<div class="kpi"><div class="e">Rate mensili</div><div class="v">' + eur(t.rata_mensile) + '</div></div>' +
                '<div class="kpi"><div class="e">Interessi ancora da pagare</div><div class="v">' + eur(t.int_restanti) + '</div></div>' +
                '<div class="kpi"><div class="e">Libero da debiti</div><div class="v">' + (t.fine_ultimo || '-') + '</div></div>' +
                '<div class="kpi"><div class="e">Rate / entrate medie</div><div class="v ' + (rosso ? 'neg' : (giallo ? '' : 'pos')) + '">' + (t.pct_entrate == null ? 'n.d.' : pct1(t.pct_entrate)) + '</div></div></div>';
            if (r.serie.length > 1) {
                h += '<h3 style="margin-top:12px">📈 Proiezione del debito totale</h3><div class="grafico">' + graficoFin(r.serie) + '</div>' + tabProiezione(r.serie);
            }
            h += '</div>';
        }
        $('finTot').innerHTML = h;
        var l = '';
        if (!r.finanziamenti.length) l = '<div class="card vuoto">Nessun finanziamento salvato. Aggiungine uno qui sotto.</div>';
        r.finanziamenti.forEach(function(f) {
            var st = f.status;
            l += '<div class="card"><div class="finhead"><h3>' + esc(f.nome) + (st ? '<span class="badge ' + st.stato + '">' + STATI[st.stato] + '</span>' : '') + '</h3><div>' +
                 '<button class="iconbtn" onclick="modificaFin(\'' + esc(f.id) + '\')">✏️</button><button class="iconbtn" onclick="eliminaFin(\'' + esc(f.id) + '\')">🗑️</button></div></div>';
            if (!st) { l += '<div class="nota neg">' + esc(f.errore) + '</div></div>'; return; }
            l += '<div class="nota">' + eur(f.capitale) + ' al ' + pct(f.tasso) + ' · ' + f.mesi + ' mesi' + (f.periodo === 3 ? ' · rate trimestrali' : '') + ' · dal ' + esc(f.data_inizio.split('-').reverse().join('-')) + '</div>' +
                 '<div class="prog"><i style="width:' + Math.min(100, st.pct).toFixed(1) + '%"></i></div>' +
                 '<div class="nota">Rimborsato ' + pct1(st.pct) + ' · rate ' + st.rate_pagate + ' / ' + st.rate_tot + '</div><div class="kpis">' +
                 '<div class="kpi"><div class="e">Debito residuo</div><div class="v">' + eur(st.residuo) + '</div></div>' +
                 '<div class="kpi"><div class="e">Rata mensile</div><div class="v">' + eur(st.rata_mensile) + (st.periodo === 3 ? '<br><small>' + eur(st.rata_periodo) + ' a trimestre</small>' : '') + '</div></div>' +
                 '<div class="kpi"><div class="e">Prossima scadenza</div><div class="v">' + (st.prossima_data ? esc(st.prossima_data) + '<br><small>' + eur(st.prossima_importo) + (st.giorni_prossima != null ? ' · tra ' + st.giorni_prossima + ' gg' : '') + '</small>' : '-') + '</div></div>' +
                 '<div class="kpi"><div class="e">Fine prevista</div><div class="v">' + esc(st.fine) + '<br><small>' + st.rate_rimaste + ' rate rimaste</small></div></div>' +
                 '<div class="kpi"><div class="e">Interessi pagati</div><div class="v">' + eur(st.int_pagati) + '</div></div>' +
                 '<div class="kpi"><div class="e">Interessi restanti</div><div class="v">' + eur(st.int_restanti) + '</div></div></div>';
            if (st.risparmio_int != null) {
                var dm = st.mesi_diff;
                l += '<div class="verdetto g"><b>Effetto delle variazioni</b>Fine prevista ' + esc(st.fine) + ' invece di ' + esc(st.base_fine) +
                     (dm ? ' (' + Math.abs(dm) + (dm > 0 ? ' mesi in meno' : ' mesi in più') + ')' : '') + ' · interessi ' + (st.risparmio_int >= 0 ? 'risparmiati ' : 'in più ') + eur(Math.abs(st.risparmio_int)) + '</div>';
            }
            if (f.crono && f.crono.length > 1) l += '<details class="sc" open><summary>🕓 Cronostoria</summary><div>' + tabCrono(f.crono) + '</div></details>';
            l += boxVar(f);
            if (st.stato !== 'estinto') l += '<details class="sc"><summary>📈 Proiezione anno per anno</summary><div>' + tabProiezione(f.proiezione) + '</div></details>';
            l += '<details class="sc"><summary>📋 Piano di ammortamento</summary><div><div class="scroll"><table><thead><tr><th>Rata</th><th>Importo</th><th>Capitale</th><th>Interessi</th><th>Residuo</th></tr></thead><tbody>';
            f.piano.forEach(function(p) {
                l += '<tr class="' + (p.pagata ? 'extra' : '') + '"><td>' + p.n + ' (' + esc(p.data) + ')' + (p.pagata ? ' ✔' : '') + (p.extra > 0 ? ' · incl. extra ' + eur(p.extra) : '') + (p.cambio ? ' 🔄' : '') + '</td><td>' + eur(p.rata) + '</td><td>' + eur(p.cap) + '</td><td>' + eur(p.int) + '</td><td>' + eur(p.residuo) + '</td></tr>';
            });
            l += '</tbody></table></div></div></details></div>';
        });
        $('finLista').innerHTML = l;
    }
    function resetFin() {
        ['fId','fN','fC','fT','fA','fD','fR','fS'].forEach(function(i) { $(i).value = ''; });
        $('fP').value = 'Mensile';
        $('finFormTit').textContent = '➕ Aggiungi un finanziamento';
    }
    function modificaFin(id) {
        var f = (FIN && FIN.finanziamenti || []).filter(function(x) { return x.id === id; })[0];
        if (!f) return;
        $('fId').value = f.id; $('fN').value = f.nome; $('fC').value = String(f.capitale).replace('.', ',');
        $('fT').value = String(f.tasso).replace('.', ','); $('fA').value = String(f.mesi);
        $('fP').value = f.periodo === 3 ? 'Trimestrale' : 'Mensile';
        $('fD').value = f.data_inizio; $('fR').value = f.rata_fissa ? String(f.rata_fissa).replace('.', ',') : '';
        $('fS').value = f.spese ? String(f.spese).replace('.', ',') : '';
        $('finFormTit').textContent = '✏️ Modifica finanziamento';
        $('fN').scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    async function salvaFin() {
        var r = await calcola({ tool: 'fin_salva', id: val('fId'), nome: val('fN'), capitale: val('fC'), tasso: val('fT'), mesi: val('fA'), periodo: val('fP'), data_inizio: val('fD'), rata: val('fR'), spese: val('fS') });
        if (!r || !r.ok) { msg((r && r.errore) || 'Errore di salvataggio.', true); return; }
        msg('Finanziamento salvato'); resetFin(); caricaFin();
    }
    async function eliminaFin(id) {
        if (!confirm('Eliminare questo finanziamento?')) return;
        var r = await calcola({ tool: 'fin_elimina', id: id });
        if (!r || !r.ok) { msg((r && r.errore) || 'Errore.', true); return; }
        msg('Eliminato'); caricaFin();
    }

    var INT_PIANO = ['Rata', 'Rata mensile', 'Quota capitale', 'Quota interessi', 'Debito residuo'];
    function tabellaPiano(p) {
        var h = '<div class="scroll"><table><thead><tr>' + INT_PIANO.map(function(x) { return '<th>' + x + '</th>'; }).join('') + '</tr></thead><tbody>';
        p.righe.forEach(function(r) {
            h += '<tr class="' + (r.tipo === 'extra' ? 'extra' : '') + '"><td>' + esc(r.label) + '</td><td>' + eur(r.rata) + '</td><td>' + eur(r.cap) +
                 '</td><td>' + eur(r.int) + '</td><td>' + eur(r.residuo) + '</td></tr>';
        });
        if (p.tot_pagato != null) {
            h += '<tr class="tot"><td>TOTALE</td><td>' + eur(p.tot_pagato) + '</td><td>' + eur(p.tot_cap) + '</td><td>' + eur(p.tot_int) + '</td><td>-</td></tr>';
        }
        return h + '</tbody></table></div>';
    }

    var N_SIM = 6;
    function costruisciSim() {
        var h = '';
        for (var i = 0; i < N_SIM; i++) {
            h += '<details class="sc"' + (i < 2 ? ' open' : '') + '><summary>Simulazione ' + (i + 1) + (i === 0 ? ' (riferimento)' : '') + '</summary><div class="griglia">' +
                '<div class="campo"><label>Capitale (€)</label><input id="s' + i + 'c" inputmode="decimal" autocomplete="off"></div>' +
                '<div class="campo"><label>Durata (anni)</label><input id="s' + i + 'a" inputmode="numeric" autocomplete="off"></div>' +
                '<div class="campo"><label>Tasso annuo (%)</label><input id="s' + i + 't" inputmode="decimal" autocomplete="off"></div>' +
                '<div class="campo"><label>Spese mensili (€)</label><input id="s' + i + 's" inputmode="decimal" autocomplete="off"></div>' +
                '<div class="campo"><label>Ammortamento extra (€)</label><input id="s' + i + 'e" inputmode="decimal" autocomplete="off"></div>' +
                '</div></details>';
        }
        $('simCampi').innerHTML = h;
    }
    async function calcolaSim() {
        var sc = [];
        for (var i = 0; i < N_SIM; i++) sc.push({ capitale: val('s' + i + 'c'), anni: val('s' + i + 'a'), tasso: val('s' + i + 't'), spese: val('s' + i + 's'), extra: val('s' + i + 'e') });
        var r = await calcola({ tool: 'simulazioni', scenari: sc });
        if (!r || !r.ok) { msg((r && r.errore) || 'Errore di calcolo.', true); return; }
        ULTIMO.sim = r;
        var errori = r.scenari.map(function(s, i) { return s.errore ? 'Sim. ' + (i + 1) + ': ' + s.errore : ''; }).filter(Boolean);
        var buoni = r.scenari.filter(function(s) { return s.ok; });
        if (!buoni.length) { $('simRis').innerHTML = '<div class="vuoto">' + (errori.length ? esc(errori.join(' ')) : 'Compila almeno capitale, durata e tasso di una simulazione.') + '</div>'; return; }
        var h = '<div class="card"><h3>Analisi comparativa</h3>';
        if (errori.length) h += '<div class="nota neg">' + esc(errori.join(' · ')) + '</div>';
        h += '<div class="scroll"><table><thead><tr><th>Sim.</th><th>Capitale</th><th>Durata</th><th>Tasso</th><th>Extra</th><th>Rata mensile</th><th>Importo totale</th><th>Interessi</th><th>Risparmio</th></tr></thead><tbody>';
        r.scenari.forEach(function(s, i) {
            if (!s.ok) return;
            var rs = s.risparmio == null ? 0 : s.risparmio;
            h += '<tr><td>Sim. ' + (i + 1) + '</td><td>' + eur(s.capitale) + '</td><td>' + s.anni + ' anni (' + s.mesi + ' rate)</td><td>' + pct(s.tasso) + '</td><td>' + eur(s.extra) +
                 '</td><td>' + eur(s.rata_totale) + '</td><td>' + eur(s.importo_totale) + '</td><td>' + eur(s.interessi) + '</td><td class="' + (rs > 0 ? 'pos' : (rs < 0 ? 'neg' : '')) + '">' + eur(rs) + '</td></tr>';
        });
        h += '</tbody></table></div></div>';
        h += '<div class="card"><h3>Piano di ammortamento</h3><div class="campo"><select id="simSel" onchange="mostraPianoSim()">';
        r.scenari.forEach(function(s, i) { if (s.ok) h += '<option value="' + i + '">Simulazione ' + (i + 1) + '</option>'; });
        h += '</select></div><div id="simPiano"></div></div>';
        $('simRis').innerHTML = h;
        mostraPianoSim();
    }
    function mostraPianoSim() {
        var s = ULTIMO.sim.scenari[parseInt(val('simSel'), 10)];
        var h = '<div class="riepilogo">Capitale: ' + eur(s.capitale) + '\nDurata: ' + s.anni + ' anni (' + s.mesi + ' mesi)\nTasso: ' + pct(s.tasso) + ' (mensile ' + s.tm_pct.toLocaleString('it-IT', { minimumFractionDigits: 4, maximumFractionDigits: 4 }) + ' %)\nMetodo: Ammortamento Francese (Rata Costante)\nAmmortamento Extra: ' + eur(s.extra) + '\nImporto Totale Restituito: ' + eur(s.piano.tot_pagato) + '\nInteressi Totali: ' + eur(s.piano.tot_int) + '</div>';
        h += tabellaPiano(s.piano) + '';
        $('simPiano').innerHTML = h;
    }
    function azzeraSim() { for (var i = 0; i < N_SIM; i++) ['c','a','t','s','e'].forEach(function(k) { $('s' + i + k).value = ''; }); $('simRis').innerHTML = ''; ULTIMO.sim = null; }

    function toggleStress() { var on = $('xStress').checked; $('xSD').disabled = !on; $('xSA').disabled = !on; }
    function impostaSost() {
        $('xE').value = '__DEF_ENTRATE__'; $('xS').value = '__DEF_SPESE__'; $('xC').value = '180000'; $('xT').value = '3,2';
        $('xD').value = '25'; $('xO').value = '10'; $('xI').value = '2,0'; $('xG').value = '1,0';
        $('xStress').checked = false; $('xSD').value = '2,0'; $('xSA').value = '3'; toggleStress();
    }
    function resetSost() { impostaSost(); $('sostRis').innerHTML = ''; ULTIMO.sost = null; }
    function graficoSost(righe) {
        var SOGLIA = 100, RANGE = 25;
        function sc(p) { if (p <= SOGLIA) return p; var e = p - SOGLIA; return SOGLIA + RANGE * (e / (e + RANGE)); }
        var n = righe.length, colW = 34, W = Math.max(300, n * colW + 40), H = 190, pl = 20, pr = 36, pt = 14, pb = 24;
        var maxP = Math.max(50, sc(Math.max.apply(null, righe.map(function(r) { return r.pct; })))) * 1.15;
        var col = { g: 'var(--green)', y: 'var(--orange)', r: 'var(--red)' };
        var cw = (W - pl - pr) / n;
        function Y(p) { return pt + (1 - p / maxP) * (H - pt - pb); }
        var s = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="' + W + '" height="' + H + '" role="img" aria-label="Rata in percentuale delle entrate, anno per anno">';
        [30, 40].forEach(function(l) {
            s += '<line x1="' + pl + '" x2="' + (W - pr) + '" y1="' + Y(l) + '" y2="' + Y(l) + '" stroke="var(--text-dim)" stroke-dasharray="3 3"/>' +
                 '<text x="' + (W - 2) + '" y="' + (Y(l) + 3) + '" text-anchor="end" font-size="9" fill="var(--text-mid)">' + l + '%</text>';
        });
        righe.forEach(function(r, i) {
            var x0 = pl + i * cw + cw * 0.2, x1 = pl + i * cw + cw * 0.8, y0 = Y(sc(r.pct));
            s += '<rect x="' + x0 + '" y="' + y0 + '" width="' + (x1 - x0) + '" height="' + (H - pb - y0) + '" rx="2" fill="' + col[r.stato] + '"><title>' + (r.anno === 0 ? 'Oggi' : 'Anno ' + r.anno) + ': ' + pct1(r.pct) + '</title></rect>';
            if (r.pct > SOGLIA) s += '<text x="' + ((x0 + x1) / 2) + '" y="' + (y0 - 3) + '" text-anchor="middle" font-size="9" font-weight="700" fill="' + col[r.stato] + '">' + Math.round(r.pct) + '%</text>';
            s += '<text x="' + ((x0 + x1) / 2) + '" y="' + (H - 8) + '" text-anchor="middle" font-size="9" fill="var(--text-mid)">' + (r.anno === 0 ? 'oggi' : '+' + r.anno) + '</text>';
        });
        return s + '</svg>';
    }
    async function calcolaSost() {
        var r = await calcola({ tool: 'sostenibilita', entrate: val('xE'), spese: val('xS'), capitale: val('xC'), tasso: val('xT'), durata: val('xD'),
            orizzonte: val('xO'), inflazione: val('xI'), crescita: val('xG'), stress: $('xStress').checked, stress_delta: val('xSD'), stress_anno: val('xSA') });
        if (!r || !r.ok) { msg((r && r.errore) || 'Errore di calcolo.', true); return; }
        ULTIMO.sost = r;
        var T = {
            g: ['✔ Sostenibile', 'Nell’arco di ' + r.orizzonte + ' anni la rata resta sotto il 30% delle entrate stimate. Oggi assorbe ' + pct1(r.pct_oggi) + ' delle entrate; tra ' + r.orizzonte + ' anni la stima è ' + pct1(r.pct_fine) + '.'],
            y: ['⚠ Da monitorare', 'In almeno un anno dell’orizzonte la rata sale tra il 30% e il 40% delle entrate. Non è allarmante, ma conviene costruire un fondo di emergenza più solido.'],
            r: ['✖ A rischio', 'In almeno un anno dell’orizzonte il residuo dopo la rata scende sotto zero, oppure la rata supera il 40% delle entrate. Conviene rivedere importo, durata o margine di reddito prima di procedere.']
        }[r.peggiore];
        var h = '<div class="card"><div class="verdetto ' + r.peggiore + '"><b>' + T[0] + '</b>' + esc(T[1]) + '</div><div class="kpis">' +
            '<div class="kpi"><div class="e">Rata oggi</div><div class="v">' + eur(r.rata_oggi) + '</div></div>' +
            '<div class="kpi"><div class="e">% entrate oggi</div><div class="v">' + pct1(r.pct_oggi) + '</div></div>' +
            '<div class="kpi"><div class="e">% entrate a ' + r.orizzonte + ' anni</div><div class="v">' + pct1(r.pct_fine) + '</div></div>' +
            '<div class="kpi"><div class="e">Residuo oggi</div><div class="v">' + eur(r.residuo_oggi) + '</div></div>' +
            '<div class="kpi"><div class="e">Residuo a ' + r.orizzonte + ' anni</div><div class="v">' + eur(r.residuo_fine) + '</div></div></div>' +
            '<div class="nota">Rata in % delle entrate, anno per anno (verde &lt; 30%, giallo 30–40%, rosso ≥ 40% o residuo negativo).</div><div class="grafico">' + graficoSost(r.righe) + '</div>';
        h += '<div class="scroll"><table><thead><tr><th>Anno</th><th>Entrate</th><th>Spese</th><th>Rata</th><th>Residuo</th><th>% entrate</th><th>Stato</th></tr></thead><tbody>';
        var nomi = { g: 'Margine sano', y: 'Da monitorare', r: 'A rischio' };
        r.righe.forEach(function(x) {
            h += '<tr class="' + x.stato + '"><td>' + (x.anno === 0 ? 'Oggi' : 'Anno ' + x.anno) + '</td><td>' + eur(x.entrate) + '</td><td>' + eur(x.spese) + '</td><td>' + eur(x.rata) + '</td><td>' + eur(x.residuo) + '</td><td>' + pct1(x.pct) + '</td><td>' + nomi[x.stato] + '</td></tr>';
        });
        $('sostRis').innerHTML = h + '</tbody></table></div></div>';
    }
    
    function resetKiller() { ['kR','kM','kT','kRata','kEA','kES'].forEach(function(i) { $(i).value = ''; }); $('kMese').value = '12'; $('kStr').value = 'Ricalcola Rata'; $('killerRis').innerHTML = ''; ULTIMO.killer = null; }
    async function calcolaKiller() {
        var r = await calcola({ tool: 'killer', residuo: val('kR'), mesi: val('kM'), tasso: val('kT'), rata: val('kRata'), extra_annuo: val('kEA'), extra_subito: val('kES'), mese: val('kMese'), strategia: val('kStr') });
        if (!r || !r.ok) { msg((r && r.errore) || 'Errore di calcolo.', true); return; }
        ULTIMO.killer = r;
        var h = '<div class="card"><h3>Risultato · ' + esc(r.strategia) + '</h3><div class="kpis">' +
            '<div class="kpi"><div class="e">📅 Termine</div><div class="v">' + esc(r.termine) + '</div></div>' +
            '<div class="kpi"><div class="e">🎯 Estinzione</div><div class="v">' + r.mesi_estinzione + ' mesi</div></div>' +
            '<div class="kpi"><div class="e">Mesi risparmiati</div><div class="v">' + r.mesi_risparmiati + '</div></div>' +
            '<div class="kpi"><div class="e">💰 Totale versato</div><div class="v">' + eur(r.tot_versato) + '</div></div>' +
            '<div class="kpi"><div class="e">📉 Interessi</div><div class="v">' + eur(r.tot_interessi) + '</div></div>' +
            '<div class="kpi"><div class="e">🚀 Risparmio interessi</div><div class="v pos">' + eur(r.risparmio) + '</div></div></div>' +
            '<div class="nota">Senza versamenti extra gli interessi sarebbero stati ' + eur(r.interessi_senza) + '.</div>';
        h += '<button class="btn mini" onclick="$(\'killerImp\').style.display = ($(\'killerImp\').style.display === \'block\' ? \'none\' : \'block\')">📊 Impatto e cash-flow</button>' +
             '';
        h += '<div id="killerImp" style="display:none"><div class="scroll"><table><thead><tr><th>Anno</th><th>Solare</th><th>Extra</th><th>Risparmio rate</th><th>Impatto reale</th></tr></thead><tbody>';
        if (r.extra_subito > 0) h += '<tr class="extra"><td>ANTICIPO</td><td>' + new Date().getFullYear() + '</td><td>' + eur(r.extra_subito) + '</td><td>' + eur(0) + '</td><td>' + eur(r.extra_subito) + '</td></tr>';
        r.annuali.forEach(function(a) { h += '<tr><td>Anno ' + a.anno + '</td><td>' + a.anno_solare + '</td><td>' + eur(r.extra_annuo) + '</td><td>' + eur(a.risparmio_rate) + '</td><td>' + eur(a.sforzo_netto) + '</td></tr>'; });
        h += '<tr class="tot"><td>ESTINZIONE</td><td>' + r.anno_estinzione + '</td><td>' + eur(r.ultimo_versamento) + '</td><td>---</td><td>' + eur(r.ultimo_versamento) + '</td></tr></tbody></table></div></div>';
        h += tabellaPiano(r.piano) + '</div>';
        $('killerRis').innerHTML = h;
    }

    function resetRata() { ['rR','rA','rT','rS'].forEach(function(i) { $(i).value = ''; }); $('rataRis').innerHTML = ''; ULTIMO.rata = null; }
    async function calcolaRata() {
        var r = await calcola({ tool: 'rata', rata: val('rR'), anni: val('rA'), tasso: val('rT'), spese: val('rS') });
        if (!r || !r.ok) { msg((r && r.errore) || 'Errore di calcolo.', true); return; }
        ULTIMO.rata = r;
        var h = '<div class="card"><div class="verdetto g"><b>💰 Capitale massimo finanziabile: ' + eur(r.capitale_max) + '</b>rata ' + eur(r.rata) + ' su ' + r.anni + ' anni al ' + pct(r.tasso) + '</div>' +
            '<div class="riepilogo">Capitale: ' + eur(r.capitale_max) + '\nDurata: ' + r.anni + ' anni (' + r.mesi + ' mesi)\nTasso: ' + pct(r.tasso) + '\nImporto Totale Restituito: ' + eur(r.piano.tot_pagato) + '\nInteressi Totali: ' + eur(r.piano.tot_int) + '</div>' +
            tabellaPiano(r.piano) + '</div>';
        $('rataRis').innerHTML = h;
    }

    document.addEventListener('DOMContentLoaded', function() {
        applyTheme(localStorage.getItem('theme') || 'dark');
        costruisciSim(); impostaSost(); caricaFin();
        document.querySelectorAll('input').forEach(function(i) {
            i.addEventListener('keydown', function(e) {
                if (e.key !== 'Enter') return;
                var p = i.closest('.pannello'); if (!p) return;
                var b = p.querySelector('.btn.verde'); if (b) b.click();
            });
        });
        var t = 'fin'; try { t = sessionStorage.getItem('fin_tab') || 'fin'; } catch (e) {}
        if (!$('p_' + t)) t = 'fin';
        vaiTab(t);
    });
</script>
</head>
<body>
<header>
    <button class="menu-btn" onclick="toggleMenu()">⚙️</button>
    <div id="extraMenu" class="nav-dropdown">
        <a href="/">🏠 Home</a>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>🗓️ Movimenti</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/calendario_web">🗓️ Calendario</a>
                <a href="/inserisci">➕ Aggiungi Operazione</a>
                <a href="/lista">📈 Gestione Movimenti Mese</a>
                <a href="/menu_esplora">🔍 Esplora e Cerca</a>
                <a href="/ricorrenze_web">🔁 Ricorrenze</a>
                <a href="/scadenze_web">📅 Scadenze del Mese</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>📊 Statistiche</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/stats">📊 Bilancio Mese</a>
                <a href="/grafici_web">📉 Grafici e Statistiche</a>
                <a href="/fairshare_web">⚖️ FairShare</a>
                <a href="/community_pool_web">🤝 CommunityPool</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>🏦 Portafoglio</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/portafoglio_web">🏦 Portafoglio Bancario</a>
                <a href="/finanziamenti_web">🧮 Mutui e Prestiti</a>
                <a href="/spese_pianificate_web">📌 Spese Pianificate</a>
                <a href="/fondo_risparmio_web">💰 Fondo Risparmio</a>
                <a href="/gestione_categorie">⚙️ Gestione Categorie</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>🏠 Casa</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/utenze?anno=__ANNO__">💧 Utenze</a>
                <a href="/consultazione_supermercati">🛒 Supermercati</a>
                <a href="/magazzino_web">📦 StockBox (Magazzino)</a>
                <a href="/immobili_web">🏢 ImmoBil (Immobili)</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>🌿 Vita</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/promemoria_web">🔔 Promemoria</a>
                <a href="/autopark_web">🚗 AutoPark (Veicoli)</a>
                <a href="/petcare_web">🐾 PetCare (Animali)</a>
                <a href="/dieta_web">🥗 Dieta</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>🗄️ Documenti</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/documenti_pdf_web">🗄️ Documenti Contabili</a>
                <a href="/documenti_personali_web">🗂️ Documenti Personali</a>
                <a href="/chiedi_ia_web">🤖 Chiedi al Database</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>🛠️ Strumenti</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/info_sys_web">📡 Monitor Server</a>
                <a href="/cambia_pw_web">🔑 Cambia Password</a>
                <a href="/webauthn_web">👆 Biometrico</a>
                <a href="/cambia_profilo_web">👤 Cambia Profilo</a>
                <a href="/logoff">🔓 Logout</a>
            </div>
        </div>
    </div>
    <div class="header-title">🧮 Mutui e Prestiti</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="tabs">
        <button class="tab" data-t="fin" onclick="vaiTab('fin')">💼 I miei finanziamenti</button>
        <button class="tab" data-t="sim" onclick="vaiTab('sim')">📊 Simulazioni</button>
        <button class="tab" data-t="sost" onclick="vaiTab('sost')">🏠 Sostenibilità nel tempo</button>
        <button class="tab" data-t="killer" onclick="vaiTab('killer')">🎯 Estinzione anticipata</button>
        <button class="tab" data-t="rata" onclick="vaiTab('rata')">💰 Rata sostenibile</button>
    </div>

    <section class="pannello" id="p_fin">
        <div id="finTot"></div>
        <div id="finLista"></div>
        <div class="card">
            <h3 id="finFormTit">➕ Aggiungi un finanziamento</h3>
            <div class="nota">Salva i tuoi mutui e prestiti reali: lo status (rate pagate, debito residuo, prossima scadenza) si aggiorna da solo in base alla data di oggi. Se non conosci la rata esatta lasciala vuota: viene calcolata (ammortamento alla francese).</div>
            <input type="hidden" id="fId">
            <div class="griglia">
                <div class="campo"><label>Nome (es. Mutuo casa)</label><input id="fN" autocomplete="off" maxlength="60"></div>
                <div class="campo"><label>Capitale erogato (€)</label><input id="fC" inputmode="decimal" autocomplete="off"></div>
                <div class="campo"><label>Tasso annuo (%)</label><input id="fT" inputmode="decimal" autocomplete="off"></div>
                <div class="campo"><label>Durata (mesi)</label><input id="fA" inputmode="numeric" autocomplete="off"></div>
                <div class="campo"><label>Periodicità rate</label><select id="fP"><option value="Mensile">Mensile</option><option value="Trimestrale">Trimestrale</option></select></div>
                <div class="campo"><label>Data prima rata</label><input id="fD" type="date"></div>
                <div class="campo"><label>Rata reale (€, opzionale)</label><input id="fR" inputmode="decimal" autocomplete="off"></div>
                <div class="campo"><label>Spese mensili (€)</label><input id="fS" inputmode="decimal" autocomplete="off"></div>
            </div>
            <div class="btns"><button class="btn verde" onclick="salvaFin()">Salva</button><button class="btn" onclick="resetFin()">Annulla</button></div>
        </div>
    </section>

    <section class="pannello" id="p_sim">
        <div class="card">
            <h3>Simulazioni di mutuo / prestito</h3>
            <div class="nota">Confronta fino a 6 scenari (ammortamento alla francese, rata costante). Il risparmio è calcolato rispetto alla Simulazione 1. Limiti: capitale fino a 500.000 €, durata fino a 35 anni, tasso fino al 35 %.</div>
            <div id="simCampi"></div>
            <div class="btns"><button class="btn verde" onclick="calcolaSim()">Calcola</button><button class="btn" onclick="azzeraSim()">Azzera</button></div>
        </div>
        <div id="simRis"></div>
    </section>

    <section class="pannello" id="p_sost">
        <div class="card">
            <h3>Il finanziamento resta sostenibile nel tempo?</h3>
            <div class="nota">Proietta entrate, spese e rata anno per anno. I valori di entrate e spese sono precompilati con la media mensile del tuo storico.</div>
            <div class="griglia">
                <div class="campo"><label>Entrate nette mensili (€)</label><input id="xE" inputmode="decimal" autocomplete="off"></div>
                <div class="campo"><label>Spese fisse mensili (€)</label><input id="xS" inputmode="decimal" autocomplete="off"></div>
                <div class="campo"><label>Importo finanziamento (€)</label><input id="xC" inputmode="decimal" autocomplete="off"></div>
                <div class="campo"><label>Tasso annuo (%)</label><input id="xT" inputmode="decimal" autocomplete="off"></div>
                <div class="campo"><label>Durata (anni)</label><input id="xD" inputmode="decimal" autocomplete="off"></div>
                <div class="campo"><label>Orizzonte osservato (anni)</label><input id="xO" inputmode="decimal" autocomplete="off"></div>
                <div class="campo"><label>Crescita costo della vita (% annua)</label><input id="xI" inputmode="decimal" autocomplete="off"></div>
                <div class="campo"><label>Crescita reddito (% annua)</label><input id="xG" inputmode="decimal" autocomplete="off"></div>
            </div>
            <label class="chk"><input type="checkbox" id="xStress" onchange="toggleStress()"> Simula un rialzo dei tassi (stress test)</label>
            <div class="griglia">
                <div class="campo"><label>Rialzo stimato (punti %)</label><input id="xSD" inputmode="decimal" autocomplete="off"></div>
                <div class="campo"><label>Dall’anno</label><input id="xSA" inputmode="decimal" autocomplete="off"></div>
            </div>
            <div class="btns"><button class="btn verde" onclick="calcolaSost()">Calcola</button><button class="btn" onclick="resetSost()">Ripristina</button></div>
        </div>
        <div id="sostRis"></div>
    </section>

    <section class="pannello" id="p_killer">
        <div class="card">
            <h3>Piano di estinzione strategica (Killer)</h3>
            <div class="nota">Simula versamenti extra su un debito in corso. «Mantieni rata» accorcia la durata; «Ricalcola rata» tiene la durata e abbassa la rata.</div>
            <div class="griglia">
                <div class="campo"><label>Debito residuo (€)</label><input id="kR" inputmode="decimal" autocomplete="off"></div>
                <div class="campo"><label>Mesi rimanenti</label><input id="kM" inputmode="decimal" autocomplete="off"></div>
                <div class="campo"><label>Tasso annuo (%)</label><input id="kT" inputmode="decimal" autocomplete="off"></div>
                <div class="campo"><label>Rata attuale (€)</label><input id="kRata" inputmode="decimal" autocomplete="off"></div>
                <div class="campo"><label>Extra annuo (€)</label><input id="kEA" inputmode="decimal" autocomplete="off"></div>
                <div class="campo"><label>Abbattimento iniziale (€)</label><input id="kES" inputmode="decimal" autocomplete="off"></div>
                <div class="campo"><label>Mese del versamento</label><select id="kMese"><option value="1">1</option><option value="2">2</option><option value="3">3</option><option value="4">4</option><option value="5">5</option><option value="6">6</option><option value="7">7</option><option value="8">8</option><option value="9">9</option><option value="10">10</option><option value="11">11</option><option value="12" selected>12</option></select></div>
                <div class="campo"><label>Strategia</label><select id="kStr"><option>Ricalcola Rata</option><option>Mantieni Rata</option></select></div>
            </div>
            <div class="btns"><button class="btn verde" onclick="calcolaKiller()">Calcola</button><button class="btn" onclick="resetKiller()">Azzera</button></div>
        </div>
        <div id="killerRis"></div>
    </section>

    <section class="pannello" id="p_rata">
        <div class="card">
            <h3>Quanto posso finanziare?</h3>
            <div class="nota">Dalla rata mensile che puoi permetterti ricava il capitale massimo finanziabile.</div>
            <div class="griglia">
                <div class="campo"><label>Rata mensile sostenibile (€)</label><input id="rR" inputmode="decimal" autocomplete="off"></div>
                <div class="campo"><label>Durata (anni)</label><input id="rA" inputmode="decimal" autocomplete="off"></div>
                <div class="campo"><label>Tasso annuo (%)</label><input id="rT" inputmode="decimal" autocomplete="off"></div>
                <div class="campo"><label>Spese mensili incluse nella rata (€)</label><input id="rS" inputmode="decimal" autocomplete="off"></div>
            </div>
            <div class="btns"><button class="btn verde" onclick="calcolaRata()">Calcola</button><button class="btn" onclick="resetRata()">Azzera</button></div>
        </div>
        <div id="rataRis"></div>
    </section>
</main>
<div id="msg"></div>
</body>
</html>
"""

def pagina_finanziamenti_web(self):
    e, s = _medie_storico(self)
    return (_PAGINA
            .replace("__DEF_ENTRATE__", str(int(round(e))) if e > 0 else "2400")
            .replace("__DEF_SPESE__", str(int(round(s))) if s > 0 else "1100")
            .replace("__ANNO__", str(datetime.date.today().year)))
