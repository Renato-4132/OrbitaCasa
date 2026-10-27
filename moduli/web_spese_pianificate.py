#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import copy
import uuid
import datetime
import threading

from moduli.modello_spesa import campo
from moduli.spese_pianificate import (
    _carica_sp,
    _parse_data,
    _mesi_coperti,
    _quote_mensili,
    _sottrai_mesi,
    _aggiorna_finestra_pianifica,
    _refresh_dashboard_pianificazione,
    MESI_ESTESI,
    MESI_BREVI,
)

_LOCK = threading.RLock()
MAX_MESI = 36


def _salva(self, dati):
    self.pianificate = copy.deepcopy(dati)
    self.save_db()

    def _gui():
        try:
            _aggiorna_finestra_pianifica(self)
            _refresh_dashboard_pianificazione(self)
        except Exception:
            pass
    try:
        self.after(0, _gui)
    except Exception:
        pass


def _etichetta(a, m):
    return f"{MESI_BREVI[m - 1]} {a}"


def _indice_spese(self):
    out = {}
    for d, voci in list(getattr(self, "spese", {}).items()):
        for v in list(voci):
            ids = campo(v, "id_spesa", None)
            if ids:
                out[ids] = (d, v)
    return out


def _piano_json(self, p, oggi, indice):
    try:
        ini = _parse_data(p["inizio"])
        scad = _parse_data(p["data_scadenza"])
    except Exception:
        return None
    mesi_lista = _mesi_coperti(ini, scad)
    tot = float(p.get("importo_totale", 0) or 0)
    quote = _quote_mensili(tot, len(mesi_lista))
    corrente = (oggi.year, oggi.month)
    cal, accantonato, quota_ora = [], 0.0, None
    for (a, m), q in zip(mesi_lista, quote):
        if (a, m) < corrente:
            stato = "pagata"
            accantonato += q
        elif (a, m) == corrente:
            stato = "corrente"
            quota_ora = q
        else:
            stato = "futura"
        cal.append({"mese": f"{MESI_ESTESI[m - 1]} {a}", "quota": q, "stato": stato})
    n = len(mesi_lista)
    trascorse = sum(1 for x in cal if x["stato"] == "pagata")
    viva = indice.get(p.get("id_spesa_collegata"))
    out = {
        "id": p.get("id", ""),
        "categoria": p.get("categoria") or p.get("nome") or "",
        "descrizione": p.get("descrizione") or "",
        "conto": p.get("conto") or "",
        "metodo": p.get("metodo_pagamento") or "",
        "hashtag": list(p.get("hashtag", []) or []),
        "totale": tot,
        "quota": quote[0] if quote else 0.0,
        "quota_ultima": quote[-1] if quote else 0.0,
        "quota_mese": quota_ora,
        "mesi": n,
        "trascorse": trascorse,
        "accantonato": round(accantonato, 2),
        "residuo": round(tot - accantonato, 2),
        "pct": round(min(100.0, accantonato / tot * 100), 1) if tot > 0 else 0.0,
        "inizio": f"{MESI_ESTESI[ini.month - 1]} {ini.year}",
        "scadenza": scad.strftime("%d-%m-%Y"),
        "giorni": (scad - oggi).days,
        "orfano": viva is None,
        "calendario": cal,
    }
    if viva is not None:
        d_viva, v = viva
        imp_live = float(campo(v, "importo", 0.0) or 0.0)
        out["data_spesa"] = d_viva.strftime("%d-%m-%Y")
        out["importo_variato"] = abs(imp_live - tot) >= 0.01
        out["importo_live"] = imp_live
    return out


def _elenco(self):
    oggi = datetime.date.today()
    with _LOCK:
        dati = _carica_sp(self)
        indice = _indice_spese(self)
    piani = []
    for p in sorted(dati.get("piani", []), key=lambda x: x.get("data_scadenza", "")):
        r = _piano_json(self, p, oggi, indice)
        if r:
            piani.append(r)
    proiezione = []
    y, m = oggi.year, oggi.month
    for _ in range(12):
        tot = 0.0
        for p in dati.get("piani", []):
            try:
                lista = _mesi_coperti(_parse_data(p["inizio"]), _parse_data(p["data_scadenza"]))
            except Exception:
                continue
            if (y, m) in lista:
                tot += _quote_mensili(float(p.get("importo_totale", 0) or 0), len(lista))[lista.index((y, m))]
        proiezione.append({"mese": _etichetta(y, m), "totale": round(tot, 2)})
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return {
        "ok": True,
        "piani": piani,
        "proiezione": proiezione,
        "totali": {
            "n": len(piani),
            "importo": round(sum(x["totale"] for x in piani), 2),
            "quota_mese": round(sum(x["quota_mese"] or 0.0 for x in piani), 2),
            "accantonato": round(sum(x["accantonato"] for x in piani), 2),
            "residuo": round(sum(x["residuo"] for x in piani), 2),
        },
    }


def _candidate(self):
    oggi = datetime.date.today()
    with _LOCK:
        gia = {p.get("id_spesa_collegata") for p in _carica_sp(self).get("piani", [])}
        voci_tutte = list(getattr(self, "spese", {}).items())
    out = []
    for d, voci in voci_tutte:
        if not isinstance(d, datetime.date) or d <= oggi:
            continue
        mesi_max = (d.year - oggi.year) * 12 + (d.month - oggi.month)
        if mesi_max < 1:
            continue
        for v in list(voci):
            ids = campo(v, "id_spesa", None)
            if not ids or ids in gia or campo(v, "tipo", "") != "Uscita":
                continue
            out.append({
                "id_spesa": ids,
                "data": d.isoformat(),
                "data_it": d.strftime("%d-%m-%Y"),
                "categoria": campo(v, "categoria", ""),
                "descrizione": (campo(v, "descrizione", "") or "").strip(),
                "importo": float(campo(v, "importo", 0.0) or 0.0),
                "mesi_max": min(mesi_max, MAX_MESI),
            })
    out.sort(key=lambda x: (x["data"], x["categoria"]))
    return {"ok": True, "spese": out[:300]}


def _trova_spesa(self, id_spesa):
    for d, voci in list(getattr(self, "spese", {}).items()):
        for v in list(voci):
            if campo(v, "id_spesa", None) == id_spesa:
                return d, v
    return None, None


def _crea(self, d):
    id_spesa = str(d.get("id_spesa", "") or "")
    if not id_spesa:
        return {"ok": False, "errore": "Seleziona una spesa futura."}, 400
    try:
        n = int(d.get("mesi"))
    except (TypeError, ValueError):
        return {"ok": False, "errore": "Numero di mesi non valido."}, 400
    includi = bool(d.get("includi_corrente", True))
    oggi = datetime.date.today()
    try:
        with _LOCK:
            data_spesa, entry = _trova_spesa(self, id_spesa)
            if entry is None:
                return {"ok": False, "errore": "Spesa non trovata (forse modificata o eliminata dal desktop)."}, 404
            if data_spesa <= oggi:
                return {"ok": False, "errore": "Puoi accantonare solo spese con data futura."}, 400
            mesi_max = (data_spesa.year - oggi.year) * 12 + (data_spesa.month - oggi.month)
            if mesi_max < 1:
                return {"ok": False, "errore": "Questa spesa scade nel mese corrente: non ci sono mesi precedenti disponibili."}, 400
            mesi_max_tot = min(mesi_max, MAX_MESI)
            massimo = mesi_max_tot if includi else max(1, mesi_max_tot - 1)
            if n < 1 or n > massimo:
                return {"ok": False, "errore": f"I mesi devono essere tra 1 e {massimo}."}, 400
            dati = _carica_sp(self)
            if any(p.get("id_spesa_collegata") == id_spesa for p in dati["piani"]):
                return {"ok": False, "errore": "Questa spesa è già in un piano di accantonamento."}, 409
            importo = float(campo(entry, "importo", 0.0) or 0.0)
            descr = (campo(entry, "descrizione", "") or "").strip()
            categoria = campo(entry, "categoria", "")
            try:
                conto = self._conto_effettivo(entry)
            except Exception:
                conto = campo(entry, "conto", "")
            inizio = _sottrai_mesi(data_spesa, n)
            dati["piani"].append({
                "id": uuid.uuid4().hex[:12],
                "nome": descr or categoria or "Spesa",
                "descrizione": descr,
                "categoria": categoria,
                "conto": conto,
                "hashtag": list(campo(entry, "hashtag", []) or []),
                "metodo_pagamento": campo(entry, "metodo_pagamento", ""),
                "importo_totale": importo,
                "data_scadenza": data_spesa.isoformat(),
                "inizio": inizio.isoformat(),
                "mesi": n,
                "quota": _quote_mensili(importo, n)[0],
                "id_spesa_collegata": id_spesa,
                "creato_il": oggi.isoformat(),
            })
            _salva(self, dati)
    except Exception as e:
        return {"ok": False, "errore": f"Errore durante il salvataggio: {e}"}, 500
    return {"ok": True}, 200


def _elimina(self, d):
    pid = str(d.get("id", "") or "")
    if not pid:
        return {"ok": False, "errore": "Piano non indicato."}, 400
    try:
        with _LOCK:
            dati = _carica_sp(self)
            prima = len(dati["piani"])
            dati["piani"] = [p for p in dati["piani"] if p.get("id") != pid]
            if len(dati["piani"]) == prima:
                return {"ok": False, "errore": "Piano non trovato (forse già eliminato)."}, 404
            _salva(self, dati)
    except Exception as e:
        return {"ok": False, "errore": f"Errore durante l'eliminazione: {e}"}, 500
    return {"ok": True}, 200


def spese_pianificate_web_api(self, d):
    if not isinstance(d, dict):
        return {"ok": False, "errore": "Richiesta non valida."}, 400
    try:
        tool = d.get("tool")
        if tool == "elenco":
            return _elenco(self), 200
        if tool == "candidate":
            return _candidate(self), 200
        if tool == "crea":
            return _crea(self, d)
        if tool == "elimina":
            return _elimina(self, d)
        return {"ok": False, "errore": "Operazione sconosciuta."}, 400
    except Exception:
        return {"ok": False, "errore": "Errore imprevisto."}, 500


_PAGINA = r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>📌 Spese Pianificate</title>
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
    .campo { margin-bottom:10px; } .campo label { display:block; font-size:0.76em; color:var(--text-mid); margin-bottom:4px; }
    .chk { display:flex; align-items:center; gap:10px; color:var(--text-mid); font-size:0.88em; margin:4px 0 10px; }
    .chk input { width:20px; height:20px; flex:none; }
    .btns { display:grid; grid-template-columns:2fr 1fr; gap:8px; margin-top:6px; }
    .btn { display:block; width:100%; padding:12px; border-radius:12px; border:1px solid var(--border); background:var(--surface3); color:var(--text); font-family:inherit; font-size:0.95em; font-weight:700; cursor:pointer; }
    .btn.verde { background:var(--green); border-color:var(--green); color:#fff; }
    .btn:disabled { opacity:0.4; cursor:default; }
    details.sc { border:1px solid var(--border); border-radius:12px; margin-bottom:8px; background:var(--surface2); }
    details.sc > summary { padding:10px 12px; cursor:pointer; font-weight:700; font-size:0.9em; list-style:none; display:flex; justify-content:space-between; }
    details.sc > summary::after { content:'▸'; color:var(--text-mid); } details.sc[open] > summary::after { content:'▾'; }
    details.sc > div { padding:2px 12px 6px; }
    .scroll { overflow-x:auto; -webkit-overflow-scrolling:touch; border:1px solid var(--border); border-radius:12px; margin-top:8px; max-height:420px; overflow-y:auto; }
    table { border-collapse:collapse; width:100%; font-size:0.8em; white-space:nowrap; }
    th { position:sticky; top:0; background:var(--surface3); color:var(--text-mid); font-weight:700; text-align:right; padding:8px 10px; z-index:1; }
    td { padding:7px 10px; text-align:right; border-top:1px solid var(--border); }
    th:first-child, td:first-child { text-align:left; }
    tr.pagata td { color:var(--text-mid); } tr.corrente td { background:rgba(99,160,240,0.14); font-weight:700; }
    .kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:8px; margin:10px 0; }
    .kpi { background:var(--surface2); border:1px solid var(--border); border-radius:12px; padding:10px; }
    .kpi .e { font-size:0.7em; color:var(--text-mid); font-weight:700; text-transform:uppercase; letter-spacing:.5px; }
    .kpi .v { font-size:1.05em; font-weight:800; margin-top:3px; overflow-wrap:anywhere; }
    .pos { color:var(--green); } .neg { color:var(--red); }
    .grafico { overflow-x:auto; margin-top:8px; }
    .prog { height:8px; border-radius:6px; background:var(--surface3); overflow:hidden; margin:8px 0 4px; }
    .prog > i { display:block; height:100%; background:var(--green); }
    .badge { display:inline-block; font-size:0.68em; font-weight:800; padding:2px 8px; border-radius:20px; border:1px solid currentColor; vertical-align:middle; margin-left:6px; }
    .badge.warn { color:var(--orange); }
    .finhead { display:flex; justify-content:space-between; align-items:flex-start; gap:8px; }
    .finhead h3 { margin:0; }
    .iconbtn { background:var(--surface3); border:1px solid var(--border); color:var(--text); border-radius:8px; padding:5px 9px; cursor:pointer; font-size:0.85em; margin-left:4px; }
    .vuoto { text-align:center; color:var(--text-mid); padding:18px 10px; font-size:0.9em; }
    .verdetto { border-radius:12px; padding:12px; margin-bottom:10px; font-size:0.88em; line-height:1.5; border:1px solid currentColor; color:var(--green); }
    #msg { position:fixed; left:50%; bottom:30px; transform:translateX(-50%); background:var(--surface2); border:1px solid var(--border-active); padding:10px 16px; border-radius:12px; font-weight:700; font-size:0.9em; display:none; z-index:300; max-width:90vw; text-align:center; }
    #msg.err { border-color:var(--red); color:var(--red); }
</style>
<script>
    var $ = function(i) { return document.getElementById(i); };
    var NF = new Intl.NumberFormat('it-IT', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    var NF1 = new Intl.NumberFormat('it-IT', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
    function eur(v) { return NF.format(v == null ? 0 : v) + ' €'; }
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

    async function api(corpo) {
        try {
            var res = await fetch('/api/spese_pianificate', { method: 'POST',
                headers: {'Content-Type':'application/json'}, body: JSON.stringify(corpo) });
            if (res.status === 401 || res.redirected) { location.reload(); return null; }
            return await res.json();
        } catch (e) { return { ok: false, errore: 'Server non raggiungibile.' }; }
    }
    function vaiTab(nome) {
        document.querySelectorAll('.tab').forEach(function(t) { t.classList.toggle('on', t.dataset.t === nome); });
        document.querySelectorAll('.pannello').forEach(function(p) { p.classList.toggle('on', p.id === 'p_' + nome); });
        try { sessionStorage.setItem('sp_tab', nome); } catch (e) {}
        if (nome === 'nuovo') caricaCandidate();
    }

    function graficoProiezione(serie) {
        var n = serie.length, W = Math.max(300, n * 44 + 20), H = 170, pt = 22, pb = 24, pl = 8;
        var max = Math.max.apply(null, serie.map(function(x) { return x.totale; })) || 1;
        var cw = (W - pl * 2) / n, s = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="' + W + '" height="' + H + '" role="img" aria-label="Quote pianificate dei prossimi 12 mesi">';
        serie.forEach(function(x, i) {
            var h = (x.totale / max) * (H - pt - pb), x0 = pl + i * cw + cw * 0.15, w = cw * 0.7;
            s += '<rect x="' + x0 + '" y="' + (H - pb - h) + '" width="' + w + '" height="' + h + '" rx="2" fill="var(--blue)"><title>' + esc(x.mese) + ': ' + eur(x.totale) + '</title></rect>' +
                 '<text x="' + (x0 + w / 2) + '" y="' + (H - 8) + '" text-anchor="middle" font-size="9" fill="var(--text-mid)">' + esc(x.mese.split(' ')[0]) + '</text>';
            if (x.totale > 0) s += '<text x="' + (x0 + w / 2) + '" y="' + (H - pb - h - 4) + '" text-anchor="middle" font-size="9" fill="var(--text-mid)">' + Math.round(x.totale) + '</text>';
        });
        return s + '</svg>';
    }
    function tabCal(cal) {
        var h = '<div class="scroll"><table><thead><tr><th>Mese</th><th>Quota</th><th>Stato</th></tr></thead><tbody>';
        cal.forEach(function(c) {
            h += '<tr class="' + c.stato + '"><td>' + esc(c.mese) + '</td><td>' + eur(c.quota) + '</td><td>' +
                 (c.stato === 'pagata' ? '✔ trascorsa' : (c.stato === 'corrente' ? '● mese corrente' : 'da accantonare')) + '</td></tr>';
        });
        return h + '</tbody></table></div>';
    }
    var DATI = null;
    async function caricaPiani() {
        var r = await api({ tool: 'elenco' });
        if (!r || !r.ok) { msg((r && r.errore) || 'Errore di caricamento.', true); return; }
        DATI = r;
        var t = r.totali, h = '';
        if (r.piani.length) {
            h = '<div class="card"><h3>📌 Riepilogo</h3><div class="kpis">' +
                '<div class="kpi"><div class="e">Piani attivi</div><div class="v">' + t.n + '</div></div>' +
                '<div class="kpi"><div class="e">Importo totale</div><div class="v">' + eur(t.importo) + '</div></div>' +
                '<div class="kpi"><div class="e">Quota del mese</div><div class="v">' + eur(t.quota_mese) + '</div></div>' +
                '<div class="kpi"><div class="e">Già accantonato</div><div class="v pos">' + eur(t.accantonato) + '</div></div>' +
                '<div class="kpi"><div class="e">Ancora da accantonare</div><div class="v">' + eur(t.residuo) + '</div></div></div>' +
                '<h3 style="margin-top:12px">📈 Quote dei prossimi 12 mesi</h3><div class="grafico">' + graficoProiezione(r.proiezione) + '</div></div>';
        }
        $('spTot').innerHTML = h;
        var l = '';
        if (!r.piani.length) l = '<div class="card vuoto">Nessuna spesa pianificata. Creane una dalla scheda «Nuovo piano».</div>';
        r.piani.forEach(function(p) {
            l += '<div class="card"><div class="finhead"><h3>' + esc(p.categoria || 'Spesa') +
                 (p.orfano ? '<span class="badge warn">spesa non trovata</span>' : '') +
                 (p.importo_variato ? '<span class="badge warn">importo cambiato</span>' : '') + '</h3><div>' +
                 '<button class="iconbtn" onclick="eliminaPiano(\'' + esc(p.id) + '\')">🗑️</button></div></div>';
            if (p.descrizione) l += '<div class="nota">' + esc(p.descrizione) + '</div>';
            l += '<div class="nota">' + esc(p.inizio) + ' → scadenza ' + esc(p.scadenza) + ' · ' + p.mesi + ' mesi' +
                 (p.conto ? ' · conto ' + esc(p.conto) : '') + (p.metodo ? ' · ' + esc(p.metodo) : '') +
                 (p.hashtag.length ? ' · ' + esc(p.hashtag.join(' ')) : '') + '</div>' +
                 '<div class="prog"><i style="width:' + p.pct.toFixed(1) + '%"></i></div>' +
                 '<div class="nota">Accantonato ' + NF1.format(p.pct) + ' % · rate ' + p.trascorse + ' / ' + p.mesi + '</div>';
            if (p.importo_variato) l += '<div class="nota neg">La spesa collegata ora vale ' + eur(p.importo_live) + ': per ricalcolare il piano usa il desktop.</div>';
            l += '<div class="kpis">' +
                 '<div class="kpi"><div class="e">Importo totale</div><div class="v">' + eur(p.totale) + '</div></div>' +
                 '<div class="kpi"><div class="e">Quota mensile</div><div class="v">' + eur(p.quota) + (p.mesi > 1 && Math.abs(p.quota_ultima - p.quota) >= 0.005 ? '<br><small>ultima ' + eur(p.quota_ultima) + '</small>' : '') + '</div></div>' +
                 '<div class="kpi"><div class="e">Quota mese corrente</div><div class="v">' + (p.quota_mese == null ? '-' : eur(p.quota_mese)) + '</div></div>' +
                 '<div class="kpi"><div class="e">Già accantonato</div><div class="v pos">' + eur(p.accantonato) + '</div></div>' +
                 '<div class="kpi"><div class="e">Residuo</div><div class="v">' + eur(p.residuo) + '</div></div>' +
                 '<div class="kpi"><div class="e">Scadenza</div><div class="v">' + esc(p.scadenza) + '<br><small>' + (p.giorni >= 0 ? 'tra ' + p.giorni + ' gg' : 'scaduta') + '</small></div></div></div>' +
                 '<details class="sc"><summary>📋 Calendario delle quote</summary><div>' + tabCal(p.calendario) + '</div></details></div>';
        });
        $('spLista').innerHTML = l;
    }
    async function eliminaPiano(id) {
        if (!confirm('Eliminare questo piano di accantonamento? La spesa collegata resta nel calendario.')) return;
        var r = await api({ tool: 'elimina', id: id });
        if (!r || !r.ok) { msg((r && r.errore) || 'Errore.', true); return; }
        msg('Piano eliminato'); caricaPiani();
    }

    var CAND = [];
    async function caricaCandidate() {
        var r = await api({ tool: 'candidate' });
        var sel = $('nSpesa');
        if (!r || !r.ok) { msg((r && r.errore) || 'Errore di caricamento.', true); return; }
        CAND = r.spese;
        var o = '<option value="">— scegli una spesa futura —</option>';
        CAND.forEach(function(s, i) {
            o += '<option value="' + i + '">' + esc(s.data_it) + ' · ' + esc(s.categoria) + (s.descrizione ? ' · ' + esc(s.descrizione) : '') + ' · ' + eur(s.importo) + '</option>';
        });
        sel.innerHTML = o;
        $('nVuoto').style.display = CAND.length ? 'none' : 'block';
        aggiornaNuovo();
    }
    function aggiornaNuovo(digitando) {
        var i = $('nSpesa').value, box = $('nDettaglio'), btn = $('nBtn');
        if (i === '') { box.innerHTML = ''; btn.disabled = true; return; }
        if (digitando && $('nMesi').value === '') { box.innerHTML = ''; btn.disabled = true; return; }
        var s = CAND[+i], inc = $('nInc').checked;
        var max = inc ? s.mesi_max : Math.max(1, s.mesi_max - 1);
        var cur = parseInt($('nMesi').value, 10);
        if (isNaN(cur) || $('nMesi').dataset.spesa !== s.id_spesa) cur = max;
        cur = Math.min(Math.max(1, cur), max);
        $('nMesi').dataset.spesa = s.id_spesa; $('nMesi').min = 1; $('nMesi').max = max; $('nMesi').value = cur;
        var base = Math.round(s.importo / cur * 100) / 100, ultima = Math.round((s.importo - base * cur) * 100) / 100 + base;
        var d = s.data.split('-'), y = +d[0], m = +d[1] - cur;
        while (m <= 0) { m += 12; y -= 1; }
        var MESI = ['Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno','Luglio','Agosto','Settembre','Ottobre','Novembre','Dicembre'];
        box.innerHTML = '<div class="kpis"><div class="kpi"><div class="e">Importo</div><div class="v">' + eur(s.importo) + '</div></div>' +
            '<div class="kpi"><div class="e">Quota mensile</div><div class="v">' + eur(base) + (cur > 1 && Math.abs(ultima - base) >= 0.005 ? '<br><small>ultima ' + eur(ultima) + '</small>' : '') + '</div></div>' +
            '<div class="kpi"><div class="e">Periodo</div><div class="v" style="font-size:.9em">' + MESI[m - 1] + ' ' + y + ' → ' + MESI[+d[1] - 1] + ' ' + d[0] + ' (escluso)</div></div></div>';
        btn.disabled = false;
    }
    async function creaPiano() {
        var i = $('nSpesa').value;
        if (i === '') return;
        var s = CAND[+i];
        var r = await api({ tool: 'crea', id_spesa: s.id_spesa, mesi: $('nMesi').value, includi_corrente: $('nInc').checked });
        if (!r || !r.ok) { msg((r && r.errore) || 'Errore.', true); return; }
        msg('Piano creato'); $('nMesi').value = ''; vaiTab('piani'); caricaPiani();
    }
    window.addEventListener('DOMContentLoaded', function() {
        applyTheme(localStorage.getItem('theme') || 'dark');
        var t = 'piani'; try { t = sessionStorage.getItem('sp_tab') || 'piani'; } catch (e) {}
        vaiTab(t === 'nuovo' ? 'nuovo' : 'piani');
        caricaPiani();
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
    <div class="header-title">📌 Spese Pianificate</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="tabs">
        <button class="tab" data-t="piani" onclick="vaiTab('piani')">📌 I miei piani</button>
        <button class="tab" data-t="nuovo" onclick="vaiTab('nuovo')">➕ Nuovo piano</button>
    </div>
    <section class="pannello" id="p_piani">
        <div id="spTot"></div>
        <div id="spLista"></div>
    </section>
    <section class="pannello" id="p_nuovo">
        <div class="card">
            <h3>➕ Accantona una spesa futura</h3>
            <div class="nota">Scegli una spesa con data futura: l'importo viene diviso in quote mensili da mettere da parte nei mesi che la precedono. Si possono accantonare solo spese in uscita con scadenza dal mese prossimo in poi, per un massimo di 36 mesi.</div>
            <div class="campo"><label>Spesa futura</label><select id="nSpesa" onchange="aggiornaNuovo()"></select></div>
            <div id="nVuoto" class="nota" style="display:none">Nessuna spesa futura disponibile: inserisci prima un'uscita con data dal mese prossimo in poi, oppure tutte quelle esistenti hanno già un piano.</div>
            <div class="campo"><label>Pianifica in quanti mesi</label><input id="nMesi" type="number" inputmode="numeric" min="1" oninput="aggiornaNuovo(true)"></div>
            <label class="chk"><input type="checkbox" id="nInc" checked onchange="aggiornaNuovo()"> Includi il mese corrente come primo mese di accantonamento</label>
            <div id="nDettaglio"></div>
            <div class="btns"><button class="btn verde" id="nBtn" onclick="creaPiano()" disabled>Crea piano</button><button class="btn" onclick="vaiTab('piani')">Annulla</button></div>
        </div>
    </section>
</main>
<div id="msg"></div>
</body>
</html>
"""


def pagina_spese_pianificate_web(self):
    return _PAGINA.replace("__ANNO__", str(datetime.date.today().year))
