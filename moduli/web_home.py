#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import calendar
import datetime
import html
import json
import os

from moduli.modello_spesa import campo
from moduli.web_utils import _fmt_it

MESI = ("Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre")


def _utente_e_ultimo_accesso():
    try:
        import __main__ as _app
        profilo = getattr(_app, "PROFILO_ATTIVO", "Principale")
        nome = (profilo if profilo != "Principale" else os.path.basename(os.getcwd())).upper()
        ultimo = "Primo accesso"
        login_web = getattr(_app, "LOGIN_WEB", None)
        if login_web and os.path.exists(login_web):
            with open(login_web, "r", encoding="utf-8") as f:
                logs = json.load(f)
            if len(logs) > 1:
                ultimo = str(logs[1].get("data_ora", "N/D"))
            elif len(logs) == 1:
                ultimo = "Primo accesso!"
        return nome, ultimo
    except Exception:
        return "", ""


def _riepilogo_mese(self, anno, mese):
    entrate = uscite = 0.0
    try:
        from moduli import web_pianificate as _wp
        _pian_on = _wp.attivo("mese")
        _pian_ids = _wp.ids_in_piano(self) if _pian_on else set()
    except Exception:
        _wp, _pian_on, _pian_ids = None, False, set()
    for d, voci in list(self.spese.items()):
        if d.year != anno or d.month != mese:
            continue
        for v in voci:
            try:
                imp = float(v[2])
            except Exception:
                continue
            if str(v[3]) == "Entrata":
                entrate += imp
            else:
                if _pian_ids and campo(v, "id_spesa", None) in _pian_ids:
                    continue
                uscite += imp
    if _pian_on and _wp is not None:
        try:
            uscite += _wp.totale_quote(self, anno, mese)
        except Exception:
            pass
    return entrate, uscite


def _promemoria_badge(self):
    try:
        from moduli.web_promemoria import promemoria_web_elenco
        r = promemoria_web_elenco(self, 1)
        if not r.get("ok"):
            return 0, 0
        scaduti = len(r.get("scaduti", []))
        oggi = sum(len(g.get("voci", [])) for g in r.get("gruppi", []) if g.get("delta") == 0)
        return scaduti, oggi
    except Exception:
        return 0, 0


def pagina_home_web(self):
    oggi = datetime.date.today()
    entrate, uscite = _riepilogo_mese(self, oggi.year, oggi.month)
    saldo = entrate - uscite
    n_oggi = len(self.spese.get(oggi, []))
    scaduti, prom_oggi = _promemoria_badge(self)

    def badge(testo, tono=""):
        return f'<span class="badge {tono}">{testo}</span>' if testo else ""

    b_cal = badge(f"oggi: {n_oggi} mov." if n_oggi else "")
    if scaduti:
        b_prom = badge(f"{scaduti} scadut{'o' if scaduti == 1 else 'i'}", "rosso")
    elif prom_oggi:
        b_prom = badge(f"{prom_oggi} oggi", "arancio")
    else:
        b_prom = ""

    gruppi = [
        ("Movimenti", [
            ("/calendario_web", "🗓️", "Calendario", b_cal),
            ("/lista", "📈", "Movimenti del mese", ""),
            ("/menu_esplora", "🔍", "Esplora e cerca", ""),
            ("/ricorrenze_web", "🔁", "Ricorrenze", ""),
            ("/scadenze_web", "📅", "Scadenze del mese", ""),
        ]),
        ("Statistiche", [
            ("/stats", "📊", "Bilancio mese", ""),
            ("/grafici_web", "📉", "Grafici e statistiche", ""),
            ("/fairshare_web", "⚖️", "FairShare", ""),
            ("/community_pool_web", "🤝", "CommunityPool", ""),
        ]),
        ("Portafoglio", [
            ("/portafoglio_web", "🏦", "Portafoglio bancario", ""),
            ("/finanziamenti_web", "🧮", "Mutui e prestiti", ""),
            ("/spese_pianificate_web", "📌", "Spese pianificate", ""),
            ("/fondo_risparmio_web", "💰", "Fondo risparmio", ""),
            ("/gestione_categorie", "⚙️", "Categorie", ""),
        ]),
        ("Casa", [
            ("/utenze?anno=%d" % oggi.year, "💧", "Utenze", ""),
            ("/consultazione_supermercati", "🛒", "Supermercati", ""),
            ("/magazzino_web", "📦", "StockBox", ""),
            ("/immobili_web", "🏢", "ImmoBil", ""),
        ]),
        ("Vita", [
            ("/promemoria_web", "🔔", "Promemoria", b_prom),
            ("/autopark_web", "🚗", "AutoPark", ""),
            ("/petcare_web", "🐾", "PetCare", ""),
            ("/dieta_web", "🥗", "Dieta", ""),
        ]),
        ("Documenti", [
            ("/documenti_pdf_web", "🗄️", "Documenti contabili", ""),
            ("/documenti_personali_web", "🗂️", "Documenti personali", ""),
            ("/chiedi_ia_web", "🤖", "Chiedi al Database", ""),
        ]),
        ("Strumenti", [
            ("/info_sys_web", "📡", "Monitor server", ""),
            ("/cambia_pw_web", "🔑", "Cambia password", ""),
            ("/webauthn_web", "👆", "Biometrico", ""),
            ("/cambia_profilo_web", "👤", "Cambia profilo", ""),
            ("/logoff", "🔓", "Logout", ""),
        ]),
    ]
    ico_gruppi = {
        "Movimenti": "🗓️", "Statistiche": "📊", "Portafoglio": "🏦",
        "Casa": "🏠", "Vita": "🌿", "Documenti": "🗄️", "Strumenti": "🛠️",
    }

    html_gruppi = ""
    for titolo, tessere in gruppi:
        html_gruppi += (f'<div class="grp"><button class="gtitolo" data-g="{titolo}" onclick="apriGruppo(this)">'
                        f'<span class="gl"><span class="gi">{ico_gruppi.get(titolo, "")}</span>{titolo}</span>'
                        f'<span class="fr">▶</span></button><div class="grid">')
        for href, ico, label, b in tessere:
            html_gruppi += (f'<a class="tile" href="{href}"><span class="ico">{ico}</span>'
                            f'<span class="lbl">{label}</span>{b}</a>')
        html_gruppi += "</div></div>"

    cls = "pos" if saldo >= 0 else "neg"
    segno = "+" if saldo >= 0 else "−"
    riepilogo = (
        f'<div class="riep"><div class="rmese">{MESI[oggi.month - 1]} {oggi.year}</div>'
        f'<div class="rcol"><div><small>Entrate</small><b class="pos">€ {_fmt_it(entrate)}</b></div>'
        f'<div><small>Uscite</small><b class="neg">€ {_fmt_it(uscite)}</b></div>'
        f'<div><small>Saldo</small><b class="{cls}">€ {segno}{_fmt_it(abs(saldo))}</b></div></div></div>'
    )
    nome_u, ultimo_u = _utente_e_ultimo_accesso()
    return (_HOME.replace("__MENU__", _menu(oggi.year))
            .replace("__UTENTE__", html.escape(nome_u, quote=True))
            .replace("__ULTIMO__", html.escape(ultimo_u, quote=True))
            .replace("__RIEPILOGO__", riepilogo)
            .replace("__GRUPPI__", html_gruppi))


def calendario_web_mese(self, anno, mese):
    try:
        anno = int(anno)
        mese = int(mese)
        datetime.date(anno, mese, 1)
    except (TypeError, ValueError):
        oggi = datetime.date.today()
        anno, mese = oggi.year, oggi.month
    ultimo = calendar.monthrange(anno, mese)[1]
    giorni = {}
    ent_t = usc_t = 0.0
    usc_escluse = 0.0
    try:
        from moduli import web_pianificate as _wp
        _pian_on = _wp.attivo("mese")
        _pian_ids = _wp.ids_in_piano(self) if _pian_on else set()
    except Exception:
        _wp, _pian_on, _pian_ids = None, False, set()
    for d, voci in list(self.spese.items()):
        if d.year != anno or d.month != mese:
            continue
        e = u = 0.0
        righe = []
        for idx, v in enumerate(voci):
            try:
                imp = float(v[2])
            except Exception:
                continue
            tipo = str(v[3])
            if tipo == "Entrata":
                e += imp
            else:
                u += imp
                if _pian_ids and campo(v, "id_spesa", None) in _pian_ids:
                    usc_escluse += imp
            tags = campo(v, "hashtag", []) or []
            if isinstance(tags, str):
                tags = [tags]
            desc = str(v[1] or "")
            righe.append({
                "idx": idx,
                "sid": campo(v, "id_spesa", "") or "",
                "cat": str(v[0] or ""),
                "desc": desc,
                "imp": imp,
                "imp_str": _fmt_it(imp),
                "tipo": tipo,
                "conto": campo(v, "conto", "") or "",
                "metodo": campo(v, "metodo_pagamento", "") or "",
                "ora": campo(v, "ora", "") or "",
                "tag": " ".join("#" + str(t).lstrip("#") for t in tags if t),
                "pdf": "ALL·" in desc,
                "ric": bool(campo(v, "id_ricorrenza", None)),
            })
        if not righe:
            continue
        righe.sort(key=lambda r: (r["ora"] or "99:99", r["idx"]))
        ent_t += e
        usc_t += u
        giorni[d.isoformat()] = {"e": round(e, 2), "u": round(u, 2), "voci": righe, "ev": []}
    try:
        from moduli import gestisci_promemoria as gp
        from moduli.web_promemoria import _voce_json
        oggi = datetime.date.today()
        dati, errore = gp._carica()
        if not errore:
            try:
                ext = gp._scadenze_esterne(self, dati.get("fonti"))
            except Exception:
                ext = []
            agenda = list(dati["agenda"]) + ext
            occ = gp._occorrenze(agenda, datetime.date(anno, mese, 1), datetime.date(anno, mese, ultimo))
            for d, vv in occ.items():
                g = giorni.setdefault(d.isoformat(), {"e": 0.0, "u": 0.0, "voci": [], "ev": []})
                g["ev"] = [_voce_json(d, v, oggi) for v in vv]
    except Exception:
        pass
    pian = {"presenti": False, "on": _pian_on, "righe": [], "tot_str": _fmt_it(0)}
    if _wp is not None:
        try:
            qs = _wp.quote(self, anno, mese)
            pian = {
                "presenti": bool(_wp.piani(self)),
                "on": _pian_on,
                "righe": [{"cat": (x["piano"].get("categoria") or x["piano"].get("nome") or "Pianificata"),
                           "desc": x["piano"].get("descrizione") or "",
                           "quota_str": _fmt_it(x["quota"])} for x in qs],
                "tot_str": _fmt_it(sum(x["quota"] for x in qs)),
            }
            if _pian_on:
                usc_t = usc_t - usc_escluse + sum(x["quota"] for x in qs)
        except Exception:
            pass
    return {"ok": True, "anno": anno, "mese": mese, "oggi": datetime.date.today().isoformat(),
            "pian": pian,
            "giorni": giorni, "ent": round(ent_t, 2), "usc": round(usc_t, 2),
            "ent_str": _fmt_it(ent_t), "usc_str": _fmt_it(usc_t),
            "saldo_str": _fmt_it(abs(ent_t - usc_t)), "saldo_pos": ent_t - usc_t >= 0}


def pagina_calendario_web(self):
    return _CAL.replace("__MENU__", _menu(datetime.date.today().year))


def _menu(anno):
    return _MENU.replace("__ANNO__", str(anno))


_CSS = r"""
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
    body { font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text); min-height:100vh; padding-bottom:60px; transition:background 0.3s,color 0.3s; }
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
    main { padding:14px; max-width:520px; margin:0 auto; }
    .pos { color:var(--green); } .neg { color:var(--red); }
"""

_JS_COMUNE = r"""
    var $ = function(i) { return document.getElementById(i); };
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
    window.addEventListener('load', function() { applyTheme(localStorage.getItem('theme') || 'dark'); });
"""

_JS_HOME = r"""
    function mostraLog() {
        var b = $('user-badge');
        if (!b || b.getAttribute('data-busy')) return;
        var nome = b.getAttribute('data-nome'), ultimo = b.getAttribute('data-ultimo');
        if (!nome || !ultimo) return;
        b.setAttribute('data-busy', '1');
        b.style.opacity = '0';
        setTimeout(function() { b.textContent = '🕒 Ultimo accesso: ' + ultimo; b.style.color = 'var(--blue)'; b.style.opacity = '1'; }, 200);
        setTimeout(function() {
            b.style.opacity = '0';
            setTimeout(function() { b.textContent = '👤 ' + nome; b.style.color = ''; b.style.opacity = '1'; b.removeAttribute('data-busy'); }, 200);
        }, 3000);
    }
    function apriGruppo(btn) {
        var g = btn.parentNode, era = g.classList.contains('open');
        document.querySelectorAll('.grp.open').forEach(function(x) { x.classList.remove('open'); });
        if (!era) g.classList.add('open');
        try { sessionStorage.setItem('home_grp', era ? '' : btn.getAttribute('data-g')); } catch (e) {}
    }
    window.addEventListener('load', function() {
        try {
            var nav = performance.getEntriesByType('navigation')[0];
            if (!nav || nav.type !== 'reload') sessionStorage.removeItem('home_grp');
            var n = sessionStorage.getItem('home_grp');
            if (n) document.querySelectorAll('.gtitolo').forEach(function(b) {
                if (b.getAttribute('data-g') === n) b.parentNode.classList.add('open');
            });
        } catch (e) {}
    });
"""

_MENU = r"""<button class="menu-btn" onclick="toggleMenu()">⚙️</button>
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
    </div>"""

_HEAD = r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>__TITOLO__</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
    (function() {
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    })();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>"""

_HOME = (_HEAD.replace("__TITOLO__", "🏠 Home") + _CSS + r"""
    .riep { background:var(--surface); border:1px solid var(--border); border-radius:16px; padding:8px 10px; margin-bottom:4px; }
    .rmese { font-size:0.62em; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:var(--gold); margin-bottom:4px; }
    .rcol { display:grid; grid-template-columns:repeat(3,1fr); gap:6px; text-align:center; }
    .rcol small { display:block; font-size:0.62em; font-weight:700; letter-spacing:1px; text-transform:uppercase; color:var(--text-dim); margin-bottom:3px; }
    .rcol b { font-size:0.85em; font-weight:800; }
    .gtitolo { display:flex; justify-content:space-between; align-items:center; width:100%; font-family:inherit; font-size:0.78em; font-weight:700; letter-spacing:1.5px; text-transform:uppercase; color:var(--gold); background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:9px 12px; margin-top:6px; cursor:pointer; }
    .grp .grid { display:none; margin-top:6px; gap:6px; }
    .grp.open .grid { display:grid; }
    .grp.open .gtitolo { border-color:var(--border-active); }
    .grp.open .fr { transform:rotate(90deg); }
    .fr { font-size:0.8em; transition:transform 0.2s; }
    .gl { display:flex; align-items:center; gap:8px; }
    .gi { font-size:1.25em; line-height:1; }
    .grid { display:grid; grid-template-columns:repeat(2,1fr); gap:10px; }
    .tile { position:relative; display:flex; flex-direction:column; align-items:flex-start; justify-content:center; gap:3px; min-height:52px; padding:8px 10px; background:var(--surface); border:1px solid var(--border); border-radius:12px; text-decoration:none; color:var(--text); transition:border-color 0.15s, transform 0.1s; }
    .tile:active { transform:scale(0.97); border-color:var(--border-active); }
    .tile .ico { font-size:1.15em; line-height:1; }
    .tile .lbl { font-weight:700; font-size:0.78em; line-height:1.25; }
    .tile.hero { grid-column:1 / -1; flex-direction:row; align-items:center; gap:10px; min-height:44px; padding:8px 12px; background:linear-gradient(135deg,var(--gold),#8a6820); color:#000; border:none; }
    .tile.hero .ico { font-size:1.4em; }
    .tile.hero .lbl { font-size:0.95em; font-weight:800; }
    .titolo-box { position:relative; text-align:center; padding-bottom:15px; }
    .header-sub { position:absolute; left:50%; bottom:0; transform:translateX(-50%); white-space:nowrap; font-size:0.62em; font-weight:700; letter-spacing:1px; color:var(--text-mid); cursor:pointer; transition:opacity 0.2s, color 0.2s; }
    .header-sub:hover { color:var(--blue); }
    .badge { position:absolute; top:6px; right:6px; font-size:0.56em; font-weight:800; padding:2px 6px; border-radius:20px; background:var(--surface3); color:var(--text-mid); }
    .badge.rosso { background:rgba(224,90,90,0.18); color:var(--red); }
    .badge.arancio { background:rgba(232,162,60,0.18); color:var(--orange); }
</style>
<script>""" + _JS_COMUNE + _JS_HOME + r"""</script>
</head>
<body>
<header>
    __MENU__
    <div class="titolo-box">
        <div class="header-title">🏠 Home</div>
        <div class="header-sub" id="user-badge" data-nome="__UTENTE__" data-ultimo="__ULTIMO__" onclick="mostraLog()">👤 __UTENTE__</div>
    </div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    __RIEPILOGO__
    <div class="grid" style="margin-top:8px;">
        <a class="tile hero" href="/inserisci"><span class="ico">➕</span><span class="lbl">Aggiungi Operazione</span></a>
    </div>
    __GRUPPI__
</main>
</body>
</html>""")

_CAL = (_HEAD.replace("__TITOLO__", "🗓️ Calendario") + _CSS + r"""
    .nav-mese { display:flex; align-items:center; justify-content:space-between; gap:8px; margin-bottom:10px; }
    .nav-mese button { background:var(--surface3); border:1px solid var(--border); color:var(--text); border-radius:10px; width:40px; height:40px; font-size:1.1em; cursor:pointer; font-family:inherit; }
    .nav-mese .oggi { width:auto; padding:0 12px; font-size:0.8em; font-weight:700; color:var(--gold); }
    .nav-mese .titolo { flex:1; text-align:center; font-weight:800; font-size:1.05em; }
    .riep { display:grid; grid-template-columns:repeat(3,1fr); gap:6px; text-align:center; background:var(--surface); border:1px solid var(--border); border-radius:14px; padding:10px; margin-bottom:10px; }
    .riep small { display:block; font-size:0.6em; font-weight:700; letter-spacing:1px; text-transform:uppercase; color:var(--text-dim); margin-bottom:2px; }
    .riep b { font-size:0.9em; font-weight:800; }
    .sett, .griglia { display:grid; grid-template-columns:repeat(7,1fr); gap:4px; }
    .sett div { text-align:center; font-size:0.62em; font-weight:700; letter-spacing:1px; color:var(--text-dim); text-transform:uppercase; padding:4px 0; }
    .cella { position:relative; min-height:58px; background:var(--surface); border:1px solid var(--border); border-radius:10px; padding:4px 3px; display:flex; flex-direction:column; align-items:center; gap:2px; cursor:pointer; font-family:inherit; color:var(--text); }
    .cella.vuota { visibility:hidden; }
    .cella.oggi { border-color:var(--gold); }
    .cella.sel { border-color:var(--blue); background:var(--surface3); }
    .cella .n { font-size:0.8em; font-weight:700; }
    .cella .dots { display:flex; gap:3px; min-height:7px; }
    .cella .dots i { width:6px; height:6px; border-radius:50%; display:block; }
    .cella .tot { font-size:0.58em; font-weight:700; white-space:nowrap; }
    .d-e { background:var(--green); } .d-u { background:var(--red); } .d-v { background:var(--blue); }
    #velo { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.6); z-index:1000; }
    #sheet { position:absolute; left:0; right:0; bottom:0; max-height:82vh; overflow-y:auto; background:var(--surface); border-top:1px solid var(--border); border-radius:20px 20px 0 0; padding:16px 14px 90px; max-width:520px; margin:0 auto; }
    .xch { float:right; width:34px; height:34px; border-radius:50%; border:1px solid var(--border); background:var(--surface3); color:var(--text); font-size:1em; cursor:pointer; margin:-4px 0 6px 8px; }
    #sheet h3 { font-size:1em; margin-bottom:10px; text-transform:capitalize; }
    .tabs { display:flex; gap:6px; margin-bottom:10px; }
    .tabs button { flex:1; padding:9px; border-radius:10px; border:1px solid var(--border); background:var(--surface3); color:var(--text-mid); font-family:inherit; font-weight:700; font-size:0.82em; cursor:pointer; }
    .tabs button.on { color:var(--gold); border-color:var(--gold); }
    .btn-add { display:block; text-align:center; text-decoration:none; padding:12px; border-radius:10px; font-weight:800; font-size:0.9em; background:linear-gradient(135deg,var(--gold),#8a6820); color:#000; margin-bottom:12px; }
    .mov { display:flex; justify-content:space-between; gap:10px; align-items:flex-start; background:var(--surface2); border:1px solid var(--border); border-left:4px solid var(--red); border-radius:12px; padding:10px; margin-bottom:8px; }
    .mov.entrata { border-left-color:var(--green); }
    .mov .cat { font-weight:700; font-size:0.9em; }
    .mov .meta { color:var(--text-mid); font-size:0.75em; margin-top:3px; line-height:1.5; word-break:break-word; }
    .mov .imp { font-weight:800; white-space:nowrap; font-size:0.92em; }
    .mov .az { display:flex; gap:6px; margin-top:8px; }
    .mov .az a, .mov .az button { background:var(--surface3); border:1px solid var(--border); border-radius:8px; padding:6px 10px; font-size:0.85em; cursor:pointer; text-decoration:none; color:var(--text); font-family:inherit; }
    .ev { background:var(--surface2); border:1px solid var(--border); border-left:4px solid var(--blue); border-radius:12px; padding:10px; margin-bottom:8px; }
    .ev.fatta { opacity:0.55; }
    .ev .t { font-weight:700; font-size:0.9em; }
    .ev .meta { color:var(--text-mid); font-size:0.75em; margin-top:3px; line-height:1.5; }
    .vuoto { text-align:center; color:var(--text-dim); font-style:italic; padding:22px 10px; font-size:0.88em; }
    .modal-overlay { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.75); backdrop-filter:blur(6px); z-index:3000; align-items:center; justify-content:center; }
    .modal-box { background:var(--surface2); border:1px solid var(--border); border-radius:var(--radius-lg); padding:24px 20px; width:88%; max-width:320px; text-align:center; }
    .modal-title { font-size:1em; font-weight:800; color:var(--gold); margin-bottom:10px; }
    .modal-text { font-size:0.88em; color:var(--text-mid); margin-bottom:14px; line-height:1.5; white-space:pre-line; }
    .modal-chk { display:none; align-items:center; justify-content:center; gap:8px; font-size:0.82em; color:var(--text-mid); margin-bottom:14px; }
    .modal-btns { display:flex; gap:10px; }
    .m-btn { flex:1; padding:12px; border-radius:9px; border:none; font-family:inherit; font-weight:700; font-size:0.88em; cursor:pointer; }
    .m-cancel { background:var(--surface3); color:var(--text-mid); }
    .m-confirm { background:linear-gradient(135deg,var(--red),#a33); color:#fff; }
    #msg { position:fixed; left:50%; bottom:92px; transform:translateX(-50%); background:var(--surface2); border:1px solid var(--border-active); padding:10px 16px; border-radius:12px; font-weight:700; font-size:0.9em; display:none; z-index:4000; max-width:90%; text-align:center; }
    #msg.err { border-color:var(--red); color:var(--red); }
</style>
<script>""" + _JS_COMUNE + r"""
    var GIORNI_N = ['Domenica','Lunedì','Martedì','Mercoledì','Giovedì','Venerdì','Sabato'];
    var MESI_N = ['Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno','Luglio','Agosto','Settembre','Ottobre','Novembre','Dicembre'];
    var Y = 0, M = 0, DATI = null, SEL = '', TAB = 'mov', DEL = null;

    function esc(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function(c) {
            return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; });
    }
    function msg(t, err) {
        var m = $('msg'); m.textContent = t; m.className = err ? 'err' : ''; m.style.display = 'block';
        clearTimeout(msg._t); msg._t = setTimeout(function() { m.style.display = 'none'; }, err ? 4500 : 2200);
    }
    function fmt(n, dec) {
        return Number(n).toLocaleString('it-IT', {minimumFractionDigits: dec, maximumFractionDigits: dec});
    }
    function corto(n) {
        var a = Math.abs(n), s = n < 0 ? '−' : '+';
        if (a >= 1000) return s + fmt(a / 1000, 1) + 'k';
        return s + fmt(a, 0);
    }
    function pad(n) { return (n < 10 ? '0' : '') + n; }
    function iso(y, m, d) { return y + '-' + pad(m) + '-' + pad(d); }
    function itData(i) { var p = i.split('-'); return p[2] + '-' + p[1] + '-' + p[0]; }

    function salvaStato() {
        var q = '?m=' + Y + '-' + pad(M) + (SEL ? '&d=' + SEL : '');
        history.replaceState(null, '', location.pathname + q);
    }
    async function carica() {
        try {
            var r = await fetch('/api/calendario/mese?anno=' + Y + '&mese=' + M + (PIAN ? '&pian=1' : ''), {cache: 'no-store'});
            if (r.status === 401) { location.href = '/login'; return; }
            DATI = await r.json();
        } catch (e) { msg('Connessione non riuscita', true); return; }
        disegna();
        if ($('velo').style.display === 'block') apriGiorno(SEL, true);
    }
    function vaiMese(delta) {
        M += delta;
        if (M < 1) { M = 12; Y--; } else if (M > 12) { M = 1; Y++; }
        SEL = ''; nascondi(); salvaStato(); carica();
    }
    function vaiOggi() {
        var t = new Date(); Y = t.getFullYear(); M = t.getMonth() + 1;
        SEL = ''; nascondi(); salvaStato(); carica();
    }
    var PIAN = false;
    function togglePianificate(attivo) { PIAN = attivo; carica(); }
    function disegnaPian() {
        var b = $('pianBox'), p = DATI.pian;
        if (!p || !p.presenti) { b.innerHTML = ''; return; }
        var h = '<div class="riep" style="display:block;margin-top:12px;text-align:left;">' +
            '<div style="font-weight:800;font-size:0.9em;margin-bottom:4px;">📌 Spese pianificate del mese <span style="font-weight:600;opacity:0.7;">· ' +
            (p.on ? 'incluse nei totali' : 'non incluse nei totali') + '</span></div>';
        if (!p.righe.length) h += '<div style="font-size:0.82em;opacity:0.7;padding:6px 0;">Nessuna quota da accantonare in questo mese.</div>';
        p.righe.forEach(function(x) {
            h += '<div style="display:flex;justify-content:space-between;gap:10px;padding:7px 0;border-top:1px solid var(--border);font-size:0.85em;">' +
                '<span>' + esc(x.cat) + (x.desc ? ' <small style="opacity:0.7">· ' + esc(x.desc) + '</small>' : '') + '</span>' +
                '<b class="neg" style="white-space:nowrap;">€ −' + x.quota_str + '</b></div>';
        });
        if (p.righe.length > 1) h += '<div style="display:flex;justify-content:space-between;padding-top:8px;border-top:2px solid var(--border);font-size:0.88em;"><b>Totale quote</b><b>€ −' + p.tot_str + '</b></div>';
        h += '<button onclick="togglePianificate(' + (p.on ? 'false' : 'true') + ')" style="margin-top:10px;width:100%;padding:10px;border-radius:10px;border:1px solid var(--border);background:var(--surface3);color:var(--text);font-family:inherit;font-weight:700;cursor:pointer;">' +
            '📌 ' + (p.on ? 'Escludi dai totali' : 'Includi nei totali') + '</button></div>';
        b.innerHTML = h;
    }
    function disegna() {
        disegnaPian();
        $('titolo').textContent = MESI_N[M - 1] + ' ' + Y;
        $('r_e').textContent = '€ ' + DATI.ent_str;
        $('r_u').textContent = '€ ' + DATI.usc_str;
        var s = $('r_s'); s.textContent = '€ ' + (DATI.saldo_pos ? '+' : '−') + DATI.saldo_str;
        s.className = DATI.saldo_pos ? 'pos' : 'neg';
        var primo = new Date(Y, M - 1, 1).getDay();
        var off = (primo + 6) % 7;
        var n = new Date(Y, M, 0).getDate();
        var h = '';
        for (var i = 0; i < off; i++) h += '<div class="cella vuota"></div>';
        for (var d = 1; d <= n; d++) {
            var k = iso(Y, M, d), g = DATI.giorni[k];
            var cls = 'cella' + (k === DATI.oggi ? ' oggi' : '') + (k === SEL ? ' sel' : '');
            var dots = '', tot = '';
            if (g) {
                if (g.e > 0) dots += '<i class="d-e"></i>';
                if (g.u > 0) dots += '<i class="d-u"></i>';
                if (g.ev && g.ev.length) dots += '<i class="d-v"></i>';
                if (g.voci.length) {
                    var net = g.e - g.u;
                    tot = '<span class="tot ' + (net >= 0 ? 'pos' : 'neg') + '">' + corto(net) + '</span>';
                }
            }
            h += '<button class="' + cls + '" onclick="apriGiorno(\'' + k + '\')"><span class="n">' + d +
                 '</span><span class="dots">' + dots + '</span>' + tot + '</button>';
        }
        $('griglia').innerHTML = h;
    }
    function apriGiorno(k, mantieniTab) {
        SEL = k; if (!mantieniTab) TAB = 'mov';
        salvaStato(); disegna();
        var g = DATI.giorni[k] || {voci: [], ev: []};
        var p = k.split('-'), dt = new Date(+p[0], +p[1] - 1, +p[2]);
        var from = encodeURIComponent('/calendario_web?m=' + Y + '-' + pad(M) + '&d=' + k);
        var h = '<button class="xch" onclick="chiudi()" title="Chiudi">✕</button><h3>' + GIORNI_N[dt.getDay()] + ' ' + (+p[2]) + ' ' + MESI_N[+p[1] - 1] + ' ' + p[0] + '</h3>';
        h += '<a class="btn-add" href="/inserisci?data=' + k + '">➕ Aggiungi qui</a>';
        h += '<div class="tabs"><button class="' + (TAB === 'mov' ? 'on' : '') + '" onclick="TAB=\'mov\';apriGiorno(SEL,true)">Movimenti (' + g.voci.length +
             ')</button><button class="' + (TAB === 'ev' ? 'on' : '') + '" onclick="TAB=\'ev\';apriGiorno(SEL,true)">Promemoria (' + g.ev.length + ')</button></div>';
        if (TAB === 'mov') {
            if (!g.voci.length) h += '<div class="vuoto">Nessun movimento in questo giorno.</div>';
            g.voci.forEach(function(v) {
                var ent = v.tipo === 'Entrata';
                var meta = [];
                if (v.desc) meta.push(esc(v.desc));
                if (v.conto) meta.push('🏦 ' + esc(v.conto));
                if (v.metodo) meta.push('💳 ' + esc(v.metodo));
                if (v.ora) meta.push('🕒 ' + esc(v.ora));
                if (v.tag) meta.push('🏷️ ' + esc(v.tag));
                if (v.ric) meta.push('🔁 ricorrenza');
                var mod = '/modifica?data=' + itData(k) + '&idx=' + v.idx + '&sid=' + encodeURIComponent(v.sid) + '&from=' + from;
                h += '<div class="mov ' + (ent ? 'entrata' : '') + '"><div style="min-width:0;flex:1"><div class="cat">' + esc(v.cat) +
                     '</div><div class="meta">' + meta.join('<br>') + '</div><div class="az"><a href="' + mod + '">✏️ Modifica</a>' +
                     '<button onclick="chiediElimina(' + v.idx + ')">❌ Elimina</button></div></div><div class="imp ' + (ent ? 'pos' : 'neg') + '">€ ' +
                     (ent ? '+' : '−') + v.imp_str + '</div></div>';
            });
        } else {
            if (!g.ev.length) h += '<div class="vuoto">Nessun promemoria in questo giorno.</div>';
            g.ev.forEach(function(e) {
                var meta = [];
                if (e.ora) meta.push('🕒 ' + esc(e.ora));
                if (e.importo) meta.push('€ ' + esc(e.importo));
                if (e.luogo) meta.push('📍 ' + esc(e.luogo));
                if (e.rip) meta.push('🔁 ' + esc(e.rip));
                if (e.fatta) meta.push('✅ fatto');
                h += '<div class="ev ' + (e.fatta ? 'fatta' : '') + '"><div class="t">' + esc(e.titolo) + '</div><div class="meta">' + esc(e.tipo) +
                     (meta.length ? '<br>' + meta.join(' · ') : '') + '</div></div>';
            });
            h += '<div style="text-align:center;margin-top:8px"><a href="/promemoria_web" style="color:var(--blue);font-size:0.82em">Apri Promemoria</a></div>';
        }
        $('sheet').innerHTML = h;
        if ($('velo').style.display !== 'block') history.pushState({sheet: 1}, '', location.href);
        $('velo').style.display = 'block';
    }
    function nascondi() { $('velo').style.display = 'none'; if (SEL) { SEL = ''; salvaStato(); if (DATI) disegna(); } }
    function chiudi() {
        if ($('velo').style.display !== 'block') return;
        if (history.state && history.state.sheet) history.back(); else nascondi();
    }
    window.addEventListener('popstate', function() { nascondi(); });
    function chiediElimina(idx) {
        var g = DATI.giorni[SEL], v = g.voci.filter(function(x) { return x.idx === idx; })[0];
        if (!v) return;
        DEL = v;
        $('confTesto').textContent = v.cat + ' · € ' + v.imp_str + '\n' + itData(SEL);
        $('confChk').style.display = v.pdf ? 'flex' : 'none';
        $('confPdf').checked = false;
        $('confModal').style.display = 'flex';
    }
    function annullaElimina() { $('confModal').style.display = 'none'; DEL = null; }
    async function confermaElimina() {
        if (!DEL) return;
        var v = DEL, body = new URLSearchParams();
        body.set('data', itData(SEL)); body.set('idx', v.idx); body.set('sid', v.sid);
        body.set('elimina_pdf', $('confPdf').checked ? '1' : '0'); body.set('ajax', '1');
        annullaElimina();
        try {
            var r = await fetch('/cancella', {method: 'POST', body: body});
            var j = await r.json();
            if (!r.ok || j.ok === false) { msg('Eliminazione non riuscita', true); return; }
            msg('Movimento eliminato');
        } catch (e) { msg('Connessione non riuscita', true); return; }
        carica();
    }
    window.addEventListener('load', function() {
        var p = new URLSearchParams(location.search), t = new Date();
        var m = (p.get('m') || '').match(/^(\d{4})-(\d{1,2})$/);
        Y = m ? +m[1] : t.getFullYear(); M = m ? +m[2] : t.getMonth() + 1;
        if (M < 1 || M > 12) { Y = t.getFullYear(); M = t.getMonth() + 1; }
        var d = p.get('d');
        if (d && /^\d{4}-\d{2}-\d{2}$/.test(d) && d.slice(0, 7) === Y + '-' + pad(M)) SEL = d;
        carica().then(function() { if (SEL) apriGiorno(SEL); });
    });
</script>
</head>
<body>
<header>
    __MENU__
    <div class="header-title">🗓️ Calendario</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="nav-mese">
        <button onclick="vaiMese(-1)">‹</button>
        <div class="titolo" id="titolo">–</div>
        <button class="oggi" onclick="vaiOggi()">Oggi</button>
        <button onclick="vaiMese(1)">›</button>
    </div>
    <div class="riep">
        <div><small>Entrate</small><b class="pos" id="r_e">–</b></div>
        <div><small>Uscite</small><b class="neg" id="r_u">–</b></div>
        <div><small>Saldo</small><b id="r_s">–</b></div>
    </div>
    <div class="sett"><div>Lun</div><div>Mar</div><div>Mer</div><div>Gio</div><div>Ven</div><div>Sab</div><div>Dom</div></div>
    <div class="griglia" id="griglia"></div>
    <div id="pianBox"></div>
</main>
<div id="velo" onclick="if (event.target === this) chiudi()"><div id="sheet"></div></div>
<div id="confModal" class="modal-overlay">
    <div class="modal-box">
        <div class="modal-title">⚠️ Elimina movimento</div>
        <div class="modal-text" id="confTesto"></div>
        <label class="modal-chk" id="confChk"><input type="checkbox" id="confPdf"> Elimina anche il PDF allegato</label>
        <div class="modal-btns">
            <button class="m-btn m-cancel" onclick="annullaElimina()">Annulla</button>
            <button class="m-btn m-confirm" onclick="confermaElimina()">Elimina</button>
        </div>
    </div>
</div>
<div id="msg"></div>
</body>
</html>""")
