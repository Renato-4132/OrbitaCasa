#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import time
import socket
import hashlib
import logging
import platform
import ctypes
import shutil
import html
import datetime
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk
from moduli.modello_spesa import SpesaEntry, campo, METODI_PAGAMENTO
from moduli.mappa_conti_trasferimenti import costruisci_mappa_conti_da_trasferimenti, conto_da_mappa, e_trasferimento_virtuale
from moduli.web_utils import _fmt_it


def pagina_grafici_web(self, conto_filtro=""):
    import __main__ as _app
    HOUSEHOLD_LABEL = "Patrimonio Complessivo"
    conto_filtro = (conto_filtro or "").strip()
    try:
        PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
            _conti_lista_g = json.load(_pf).get("conti", [])
    except Exception:
        _conti_lista_g = []
    conto_options_g = f'<option value="" {"selected" if not conto_filtro else ""}>{HOUSEHOLD_LABEL}</option>\n' + "\n".join(
        f'<option value="{html.escape(c.get("nome",""))}" {"selected" if c.get("nome","") == conto_filtro else ""}>{html.escape(c.get("nome",""))}</option>'
        for c in _conti_lista_g
    )
    oggi = datetime.date.today()
    anno_corrente = oggi.year
    oggi_formattata = oggi.strftime('%d/%m/%Y')
    anno_corrente_format = str(anno_corrente)
    fallback_storico     = '{"labels": ["N/D"], "datasets": [{"label": "Dati non caricati", "data": [0], "backgroundColor": ["#333"]}]}'
    fallback_mensile     = '{"labels": ["N/D"], "datasets": [{"label": "Dati non caricati", "data": [0], "backgroundColor": ["#333"]}]}'
    fallback_cat         = '{"labels": ["N/D"], "datasets": [{"data": [1], "backgroundColor": ["#333"], "label": "Dati non caricati"}]}'
    fallback_saldo       = '{"labels": ["N/D"], "datasets": [{"label": "Dati non caricati", "data": [0], "borderColor": "#333"}]}'
    fallback_cat_storico = '{"labels": ["N/D"], "datasets": [{"data": [1], "backgroundColor": ["#333"], "label": "Dati non caricati"}]}'
    fallback_saldo_annuale = '{"labels": ["N/D"], "datasets": [{"label": "Dati non caricati", "data": [0], "borderColor": "#333", "backgroundColor": ["#333"]}]}'
    try:
        dati_entrate_uscite_storici = self.get_dati_entrate_uscite_tutti_gli_anni_json(conto_filtro or None)
    except Exception:
        dati_entrate_uscite_storici = fallback_storico
    try:
        dati_entrate_uscite_mensili = self.get_dati_entrate_uscite_json(conto_filtro or None)
    except Exception:
        dati_entrate_uscite_mensili = fallback_mensile
    try:
        dati_categorie = self.get_dati_categorie_json(conto_filtro or None)
    except Exception:
        dati_categorie = fallback_cat
    try:
        dati_saldo = self.get_dati_saldo_json(conto_filtro or None)
    except Exception:
        dati_saldo = fallback_saldo
    try:
        dati_categorie_storiche = self.get_dati_categorie_storiche_json(conto_filtro or None)
    except Exception:
        dati_categorie_storiche = fallback_cat_storico
    try:
        dati_saldo_annuale = self.get_dati_saldo_annuale_json(conto_filtro or None)
    except Exception:
        dati_saldo_annuale = fallback_saldo_annuale

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>📊 Grafici e Statistiche</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
    (function() {{
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    }})();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
    :root {{
        --bg:#050505; --surface:#0f0f0f; --surface2:#161616; --surface3:#1e1e1e;
        --border:rgba(255,255,255,0.07); --gold:#c9a84c; --blue:#63a0f0;
        --green:#4caf82; --red:#e05a5a; --text:#e8e8e8;
        --text-dim:#555; --text-mid:#888; --radius-lg:18px;
    }}
    :root.light {{
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --gold:#b8902a; --blue:#3d7fd4;
        --green:#3a9068; --red:#cc3333; --text:#1a1a1a;
        --text-dim:#999; --text-mid:#555;
    }}
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{
        font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text);
        min-height:100vh; padding-bottom:50px; transition:background 0.3s,color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 40% at 50% -10%, rgba(99,160,240,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 60%);
    }}
    header {{
        padding:14px 16px 12px; display:flex; align-items:center; justify-content:center;
        border-bottom:1px solid var(--border); background:rgba(5,5,5,0.95);
        backdrop-filter:blur(20px); position:sticky; top:0; z-index:100;
    }}
    :root.light header {{ background:rgba(245,245,240,0.95); }}
    .menu-btn {{
        position:absolute; left:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border); color:var(--gold);
        width:36px; height:36px; border-radius:10px; font-size:1em;
        cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.2s;
    }}
    .menu-btn:hover {{ border-color:var(--gold); box-shadow:0 0 12px rgba(201,168,76,0.2); }}
    .header-title {{ font-family:'DM Sans',sans-serif; font-size:1em; font-weight:700; color:var(--text); }}
    .theme-toggle {{
        position:absolute; right:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border);
        border-radius:8px; width:34px; height:34px;
        display:flex; align-items:center; justify-content:center;
        cursor:pointer; font-size:1em; transition:all 0.2s;
    }}
    .theme-toggle:hover {{ border-color:var(--gold); }}
    .nav-dropdown {{
        position:absolute; top:calc(100% + 6px); left:10px;
        background:var(--surface2); border:1px solid var(--border);
        border-radius:var(--radius-lg); display:none; z-index:1000;
        width:270px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.7);
    }}
    .nav-dropdown a {{
        display:flex; align-items:center; gap:10px; padding:10px 16px;
        text-decoration:none; color:var(--text-mid); border-bottom:1px solid var(--border);
        font-size:0.87em; transition:all 0.15s;
    }}
    .nav-dropdown a:last-child {{ border-bottom:none; }}
    .nav-dropdown a:hover {{ background:var(--surface3); color:var(--text); padding-left:22px; }}
    .nav-group-btn {{ display:flex; justify-content:space-between; align-items:center; width:100%;
        padding:8px 16px; background:none; border:none; font-family:inherit; color:var(--gold);
        font-size:0.7em; font-weight:700; letter-spacing:1px; text-transform:uppercase; cursor:pointer; opacity:0.85; }}
    .nav-group-btn:hover {{ opacity:1; background:var(--surface3); }}
    .nav-arrow {{ font-size:0.85em; transition:transform 0.15s; }}
    .nav-group-items {{ display:none; flex-direction:column; }}
    .nav-group-items.open {{ display:flex; }}
    .main-container {{ max-width:960px; margin:0 auto; padding:14px; animation:fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .tab-bar {{ display:flex; flex-wrap:wrap; gap:4px; margin-bottom:0; padding:0; }}
    .tab-btn {{
        padding:8px 14px; cursor:pointer;
        font-family:'DM Sans',sans-serif; font-size:0.75em; font-weight:700;
        color:var(--text-dim); border:1px solid var(--border);
        background:var(--surface2); border-radius:9px 9px 0 0;
        transition:all 0.15s; white-space:nowrap; line-height:1.5;
    }}
    .tab-btn:hover {{ color:var(--text-mid); background:var(--surface3); }}
    .tab-btn.active {{
        color:var(--gold); background:var(--surface);
        border-color:var(--border); border-bottom-color:var(--surface);
    }}
    .chart-frame {{
        background:var(--surface); border:1px solid var(--border);
        border-radius:0 var(--radius-lg) var(--radius-lg) var(--radius-lg);
        padding:16px; position:relative; overflow:hidden;
    }}
    .chart-frame::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .chart-container {{
        position:relative; width:100%;
        height:58vh; min-height:320px; max-height:520px;
    }}
    .chart-container.donut {{
        height:auto; min-height:unset; max-height:unset;
        display:flex; flex-direction:column; align-items:center; gap:14px;
        padding:8px 0 4px;
    }}
    .donut-canvas-wrap {{
        position:relative;
        width:min(320px, 78vw);
        height:min(320px, 78vw);
        flex-shrink:0;
    }}
    .donut-legend {{
        width:100%; display:flex; flex-direction:column; gap:3px;
        max-height:220px; overflow-y:auto; padding:0 2px;
    }}
    .donut-legend::-webkit-scrollbar {{ width:4px; }}
    .donut-legend::-webkit-scrollbar-track {{ background:transparent; }}
    .donut-legend::-webkit-scrollbar-thumb {{ background:var(--border); border-radius:4px; }}
    .legend-item {{
        display:flex; align-items:center; gap:8px;
        font-size:0.78em; color:var(--text-mid); padding:4px 8px;
        border-radius:7px; transition:background 0.15s;
    }}
    .legend-item:hover {{ background:var(--surface2); color:var(--text); }}
    .legend-dot {{ width:9px; height:9px; border-radius:50%; flex-shrink:0; }}
    .legend-name {{ flex:1; display:flex; flex-direction:column; gap:1px; }}
    .legend-budget {{ font-size:0.78em; color:var(--text-dim); }}
    .legend-budget.over {{ color:var(--red); font-weight:700; }}
    .legend-item.over-budget {{ background:rgba(224,90,90,0.09); }}
    .legend-val {{ font-weight:700; color:var(--text); }}
    .legend-pct {{ color:var(--text-dim); font-size:0.88em; margin-left:3px; }}
    .tab-pane {{ display:none; }}
    .btn-home {{
        display:block; text-align:center; padding:13px; margin-top:12px;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; border-radius:10px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.9em;
        line-height:1.5; transition:all 0.2s;
    }}
    .btn-home:hover {{ transform:translateY(-1px); box-shadow:0 6px 20px rgba(201,168,76,0.25); }}
    @media (max-width:500px) {{
        .tab-btn {{ padding:7px 10px; font-size:0.7em; }}
        .chart-container {{ height:52vw; min-height:260px; }}
        .donut-canvas-wrap {{ width:min(260px, 82vw); height:min(260px, 82vw); }}
    }}
</style>
</head>
<body>
<header>
    <button class="menu-btn" onclick="toggleMenu()">⚙️</button>
    <div id="extraMenu" class="nav-dropdown">
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Finanze</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/">🏠 Aggiungi Operazione</a>
                <a href="/lista">📈 Gestione Movimenti Mese</a>
                <a href="/stats">📊 Bilancio Mese</a>
                <a href="/fondo_risparmio_web">💰 Fondo Risparmio</a>
                <a href="/scadenze_web">📅 Scadenze del Mese</a>
                <a href="/fairshare_web">⚖️ FairShare</a>
                <a href="/menu_esplora">🔍 Esplora</a>
                <a href="/grafici_web">📅 Grafici e Statistiche</a>
                <a href="/portafoglio_web">🏦 Portafoglio Bancario</a>
                <a href="/gestione_categorie">⚙️ Gestione Categorie</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Casa</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/utenze?anno={anno_corrente_format}">💧 Utenze</a>
                <a href="/consultazione_supermercati">🛒 Gestione Supermercati</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Documenti</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/documenti_pdf_web">🗄️ Documenti Contabili</a>
                <a href="/documenti_personali_web">🗄️ Documenti Personali</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Sistema</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/info_sys_web">📡 Monitor Server</a>
                <a href="/cambia_pw_web">🔑 Cambia Password</a>
                <a href="/webauthn_web">👆 Biometrico</a>
                <a href="/cambia_profilo_web">👤 Cambia Profilo</a>
                <a href="/logoff">🔓 Logout</a>
            </div>
        </div>
    </div>
    <div class="header-title">📊 Grafici e Statistiche</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main class="main-container">
    <form method="get" action="/grafici_web" style="margin-bottom:12px;">
        <select name="conto" onchange="this.form.submit()"
            style="width:100%; padding:11px 14px; border-radius:12px; border:1px solid var(--border);
                   background:var(--surface); color:var(--text); font-family:'DM Sans',sans-serif;
                   font-size:0.88em; font-weight:700;">
            {conto_options_g}
        </select>
    </form>
    <div class="tab-bar">
        <button class="tab-btn" onclick="openTab('tabStoricoEU', this)">📅 Storico</button>
        <button class="tab-btn" onclick="openTab('tabMensileEU', this)">🗓️ Mensile</button>
        <button class="tab-btn" onclick="openTab('tabSaldo', this)">📈 Saldo Mese</button>
        <button class="tab-btn" onclick="openTab('tabSaldoAnnuale', this)">⚖️ Saldo Annuale</button>
        <button class="tab-btn" onclick="openTab('tabCategorie', this)">🍩 Uscite</button>
        <button class="tab-btn" onclick="openTab('tabStoricoCat', this)">📊 Uscite Storiche</button>
    </div>
    <div class="chart-frame">
        <div id="tabStoricoEU"    class="tab-pane"><div class="chart-container"><canvas></canvas></div></div>
        <div id="tabMensileEU"    class="tab-pane"><div class="chart-container"><canvas></canvas></div></div>
        <div id="tabSaldo"        class="tab-pane"><div class="chart-container"><canvas></canvas></div></div>
        <div id="tabSaldoAnnuale" class="tab-pane"><div class="chart-container"><canvas></canvas></div></div>
        <div id="tabCategorie" class="tab-pane">
            <div class="chart-container donut">
                <div class="donut-canvas-wrap"><canvas></canvas></div>
                <div class="donut-legend" id="legendTabCategorie"></div>
            </div>
        </div>
        <div id="tabStoricoCat" class="tab-pane">
            <div class="chart-container donut">
                <div class="donut-canvas-wrap"><canvas></canvas></div>
                <div class="donut-legend" id="legendTabStoricoCat"></div>
            </div>
        </div>
    </div>

    <a href="/" class="btn-home">🏠 Torna alla Home</a>
</main>
<script>
    const chartInstances = {{}};
    const chartData = {{
        tabStoricoEU:    {dati_entrate_uscite_storici},
        tabMensileEU:    {dati_entrate_uscite_mensili},
        tabSaldo:        {dati_saldo},
        tabSaldoAnnuale: {dati_saldo_annuale},
        tabCategorie:    {dati_categorie},
        tabStoricoCat:   {dati_categorie_storiche}
    }};
    function fmtIt(v) {{
        v = Number(v || 0);
        const neg = v < 0;
        const parts = Math.abs(v).toFixed(2).split('.');
        parts[0] = parts[0].replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, '.');
        return (neg ? '-' : '') + parts[0] + ',' + parts[1];
    }}
    function getChartColors() {{
        const light = document.documentElement.classList.contains('light');
        return {{
            tick:   light ? '#777' : '#555',
            grid:   light ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.04)',
            legend: light ? '#555' : '#888'
        }};
    }}
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if (btn) btn.textContent = '🌙'; }}
        else               {{ root.classList.remove('light'); if (btn) btn.textContent = '☀️'; }}
        const activeTab = document.querySelector('.tab-btn.active');
        if (activeTab) {{
            const tabName = activeTab.getAttribute('onclick').match(/'([^']+)'/)[1];
            renderChart(tabName);
        }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        applyTheme(next);
    }}
    applyTheme(localStorage.getItem('theme') || 'dark');
    function sortData(data) {{
        if (!data.labels) return data;
        const budgets = data.datasets[0].budget || [];
        let combined = data.labels.map((l, i) => ({{
            label: l,
            val: data.datasets[0].data[i],
            color: data.datasets[0].backgroundColor[i],
            budget: budgets[i] || 0
        }}));
        combined.sort((a, b) => b.val - a.val);
        data.labels = combined.map(x => x.label);
        data.datasets[0].data = combined.map(x => x.val);
        data.datasets[0].backgroundColor = combined.map(x => x.color);
        data.datasets[0].budget = combined.map(x => x.budget);
        return data;
    }}
    function buildDonutLegend(legendId, data) {{
        const legendEl = document.getElementById(legendId);
        if (!legendEl) return;
        const labels = data.labels || [];
        const vals = data.datasets[0].data || [];
        const colors = data.datasets[0].backgroundColor || [];
        const budgets = data.datasets[0].budget || [];
        const total = vals.reduce((a, b) => a + b, 0);
        legendEl.innerHTML = labels.map((lbl, i) => {{
            const pct = total > 0 ? ((vals[i] / total) * 100).toFixed(1) : '0.0';
            const budget = budgets[i] || 0;
            const sfora = budget > 0 && vals[i] > budget;
            const budgetInfo = budget > 0
                ? `<span class="legend-budget${{sfora ? ' over' : ''}}">${{sfora ? '⚠️ ' : ''}}budget € ${{fmtIt(budget)}}</span>`
                : '';
            return `<div class="legend-item${{sfora ? ' over-budget' : ''}}">
                <span class="legend-dot" style="background:${{colors[i] || '#888'}}"></span>
                <span class="legend-name">${{lbl}}${{budgetInfo}}</span>
                <span class="legend-val">€ ${{fmtIt(vals[i])}}</span>
                <span class="legend-pct">${{pct}}%</span>
            </div>`;
        }}).join('');
    }}
    function toggleNavGroup(btn, ev) {{
        if (ev) ev.stopPropagation();
        const items = btn.nextElementSibling;
        const giaAperto = items.classList.contains('open');
        btn.closest('.nav-dropdown').querySelectorAll('.nav-group-items.open').forEach(function(el) {{
            el.classList.remove('open');
            el.previousElementSibling.querySelector('.nav-arrow').textContent = '▶';
        }});
        if (!giaAperto) {{
            items.classList.add('open');
            btn.querySelector('.nav-arrow').textContent = '▼';
        }}
    }}
    function toggleMenu() {{
        const m = document.getElementById("extraMenu");
        m.style.display = m.style.display === "block" ? "none" : "block";
    }}
    function openTab(tabName, btn) {{
        document.querySelectorAll(".tab-pane").forEach(p => p.style.display = "none");
        document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
        document.getElementById(tabName).style.display = "block";
        btn.classList.add("active");
        renderChart(tabName);
    }}
    function renderChart(tabName) {{
        if (chartInstances[tabName]) chartInstances[tabName].destroy();
        const isDonut = tabName === 'tabCategorie' || tabName === 'tabStoricoCat';
        const ctx = document.querySelector(`#${{tabName}} canvas`).getContext('2d');
        const cc = getChartColors();
        let type = 'bar';
        let opts = {{
            responsive: true,
            maintainAspectRatio: isDonut,
            plugins: {{ legend: {{ display: false }} }},
            scales: {{}}
        }};
        if (tabName === 'tabSaldo' || tabName === 'tabSaldoAnnuale') {{
            type = 'line';
        }}
        if (isDonut) {{
            type = 'doughnut';
            opts.cutout = '58%';
            opts.plugins.tooltip = {{
                callbacks: {{
                    label: function(ctx) {{
                        const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                        const pct = total > 0 ? ((ctx.parsed / total) * 100).toFixed(1) : 0;
                        return ` ${{ctx.label}}: € ${{fmtIt(ctx.parsed)}} (${{pct}}%)`;
                    }}
                }}
            }};
        }} else {{
            opts.plugins.legend = {{ labels: {{ color: cc.legend, font: {{ family: 'DM Sans' }} }} }};
            opts.plugins.tooltip = {{
                callbacks: {{
                    label: function(ctx) {{
                        const dsLabel = ctx.dataset.label ? ctx.dataset.label + ': ' : '';
                        return ` ${{dsLabel}}€ ${{fmtIt(ctx.parsed.y)}}`;
                    }}
                }}
            }};
            opts.scales = {{
                x: {{ ticks: {{ color: cc.tick, font: {{ family: 'DM Sans' }} }}, grid: {{ color: cc.grid }} }},
                y: {{ ticks: {{ color: cc.tick, font: {{ family: 'DM Sans' }}, callback: v => '€ ' + fmtIt(v) }}, grid: {{ color: cc.grid }} }}
            }};
        }}
        let data = JSON.parse(JSON.stringify(chartData[tabName]));
        if (isDonut) {{
            data = sortData(data);
            if (tabName === 'tabCategorie') {{
                const budgets = data.datasets[0].budget || [];
                const vals = data.datasets[0].data || [];
                const normalBorder = getComputedStyle(document.documentElement).getPropertyValue('--surface').trim() || '#0f0f0f';
                data.datasets[0].borderColor = vals.map((v, i) => (budgets[i] > 0 && v > budgets[i]) ? '#dc3545' : normalBorder);
                data.datasets[0].borderWidth = vals.map((v, i) => (budgets[i] > 0 && v > budgets[i]) ? 3 : 2);
            }}
            const legendId = 'legend' + tabName.charAt(0).toUpperCase() + tabName.slice(1);
            buildDonutLegend(legendId, data);
        }}
        chartInstances[tabName] = new Chart(ctx, {{ type, data, options: opts }});
    }}
    document.addEventListener("click", function(e) {{
        const menu = document.getElementById("extraMenu");
        const btn = document.querySelector(".menu-btn");
        if (menu && menu.style.display === "block" && !menu.contains(e.target) && e.target !== btn)
            menu.style.display = "none";
    }});
    document.querySelector('.tab-btn').click();
</script>
</body>
</html>"""

# Html Genera la pagina web delle scadenze/ricorrenze del mese corrente (equivalente web del popup scadenze_mese)
def html_scadenze_mese(self):
    import datetime
    from moduli.modello_spesa import campo
    def calcola_data_fine(data_inizio, n_volte, periodo):
        if not data_inizio or not isinstance(n_volte, int) or n_volte < 1:
            return "N/D"
        periodo = periodo.lower().strip()
        if periodo == "ogni giorno":
            data_fine_obj = data_inizio + datetime.timedelta(days=n_volte - 1)
        elif periodo == "ogni mese":
            total_months = data_inizio.month + n_volte - 1
            anno_fine = data_inizio.year + (total_months - 1) // 12
            mese_fine = (total_months - 1) % 12 + 1
            giorno_inizio = data_inizio.day
            try:
                data_fine_obj = datetime.date(anno_fine, mese_fine, giorno_inizio)
            except ValueError:
                if mese_fine == 12:
                    primo_giorno_mese_successivo = datetime.date(anno_fine + 1, 1, 1)
                else:
                    primo_giorno_mese_successivo = datetime.date(anno_fine, mese_fine + 1, 1)
                ultimo_giorno_mese_fine = (primo_giorno_mese_successivo - datetime.timedelta(days=1)).day
                data_fine_obj = datetime.date(anno_fine, mese_fine, ultimo_giorno_mese_fine)
        elif periodo == "ogni anno":
            anno_fine = data_inizio.year + n_volte - 1
            try:
                data_fine_obj = data_inizio.replace(year=anno_fine)
            except ValueError:
                data_fine_obj = data_inizio.replace(year=anno_fine, day=28)
        else:
            return "N/D"
        return data_fine_obj.strftime("%d-%m-%Y")
    oggi = datetime.date.today()
    mese_corrente = oggi.month
    anno_corrente = oggi.year
    mesi_italiani = [
        "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
    ]
    mese_nome = mesi_italiani[mese_corrente - 1]
    righe = []
    for item_id, dati in self.ricorrenze.items():
        try:
            ric_type = dati.get("tipo", "").lower()
            n = dati.get("n", 0)
            data_inizio = datetime.datetime.strptime(dati.get("data_inizio", ""), "%d-%m-%Y").date()
            categoria = dati.get("cat", "N/D")
            descrizione_base = dati.get("desc", "—")
            tipo_voce = dati.get("tipo_voce", "N/D")
            importo_base = float(str(dati.get("imp", "0")).replace(",", "."))
            date_nel_mese = []
            for i in range(n):
                if ric_type == "ogni mese":
                    mese = (data_inizio.month - 1 + i) % 12 + 1
                    anno = data_inizio.year + (data_inizio.month - 1 + i) // 12
                    giorno = min(
                        data_inizio.day,
                        [31, 29 if anno % 4 == 0 and (anno % 100 != 0 or anno % 400 == 0) else 28,
                         31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mese - 1]
                    )
                    data_movimento = datetime.date(anno, mese, giorno)
                elif ric_type == "ogni anno":
                    try:
                        data_movimento = data_inizio.replace(year=data_inizio.year + i)
                    except ValueError:
                        data_movimento = data_inizio.replace(year=data_inizio.year + i, day=28)
                else:
                    data_movimento = data_inizio + datetime.timedelta(days=i)
                if data_movimento.month == mese_corrente and data_movimento.year == anno_corrente:
                    date_nel_mese.append((i + 1, data_movimento))
            data_fine_serie = calcola_data_fine(data_inizio, n, ric_type)
            for indice, data_movimento in date_nel_mese:
                voce_trovata = False
                importo_effettivo = importo_base
                if data_movimento in self.spese:
                    for voce in self.spese[data_movimento]:
                        if len(voce) >= 5 and voce[4] == item_id:
                            importo_effettivo = voce[2]
                            voce_trovata = True
                            break
                pagato = data_movimento <= oggi and voce_trovata
                righe.append({
                    "data": data_movimento, "categoria": categoria, "descrizione": descrizione_base,
                    "importo": importo_effettivo, "tipo": tipo_voce, "scadenza_serie": data_fine_serie,
                    "pagato": pagato, "trovata": voce_trovata, "progressione": f"{indice}/{n}",
                })
        except Exception as e:
            print(f"Errore nella ricorrenza con ID {item_id}: {e}")
            continue
    fine_mese = datetime.date(anno_corrente, mese_corrente, 28)
    while True:
        try:
            fine_mese = fine_mese.replace(day=fine_mese.day + 1)
        except ValueError:
            break
    for data_voce in sorted(self.spese.keys()):
        if oggi <= data_voce <= fine_mese:
            for voce in self.spese[data_voce]:
                if len(voce) < 5 or voce[4] not in self.ricorrenze:
                    try:
                        categoria, descrizione, importo, tipo_voce = voce[:4]
                        righe.append({
                            "data": data_voce, "categoria": categoria, "descrizione": descrizione,
                            "importo": importo, "tipo": tipo_voce, "scadenza_serie": data_voce.strftime("%d-%m-%Y"),
                            "pagato": data_voce <= oggi, "trovata": True, "progressione": "—",
                        })
                    except Exception as e:
                        print(f"Errore nella voce normale del {data_voce}: {e}")
                        continue
    righe.sort(key=lambda r: r["data"])
    righe_html = ""
    if not righe:
        righe_html = "<p style='text-align:center; color:#555; padding:20px; font-style:italic;'>Nessuna scadenza per questo mese.</p>"
    else:
        for r in righe:
            colore = "#4caf82" if r["tipo"].strip().lower() != "uscita" and r["trovata"] else ("#e05a5a" if r["tipo"].strip().lower() == "uscita" else "#888")
            segno = "-" if r["tipo"].strip().lower() == "uscita" else "+"
            stato_icona = "✔️" if r["pagato"] else "❌"
            stato_testo = "Pagato" if r["pagato"] else "Da pagare"
            valore_importo = f"{segno}€{_fmt_it(r['importo'])}" if r["trovata"] else "—"
            righe_html += f"""
            <div class="scad-item">
                <div class="scad-date">{r['data'].strftime('%d-%m-%Y')}</div>
                <div class="scad-body">
                    <div class="scad-top">
                        <span class="scad-cat">{r['categoria']}</span>
                        <span class="scad-amt" style="color:{colore};">{valore_importo}</span>
                    </div>
                    <div class="scad-desc">{r['descrizione']}</div>
                    <div class="scad-meta">
                        <span class="scad-badge">{stato_icona} {stato_testo}</span>
                        <span class="scad-badge">{r['progressione']}</span>
                        <span class="scad-badge">{r['tipo']}</span>
                    </div>
                </div>
            </div>"""
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>📅 Scadenze del Mese</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
    (function() {{
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    }})();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg:#050505; --surface:#0f0f0f; --surface2:#161616; --surface3:#1e1e1e;
        --border:rgba(255,255,255,0.07); --gold:#c9a84c; --blue:#63a0f0;
        --green:#4caf82; --red:#e05a5a; --text:#e8e8e8; --text-dim:#555; --text-mid:#888;
        --radius-lg:18px;
    }}
    :root.light {{
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --gold:#b8902a; --blue:#3d7fd4;
        --green:#3a9068; --red:#cc3333; --text:#1a1a1a; --text-dim:#999; --text-mid:#555;
    }}
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{ font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text);
        min-height:100vh; padding-bottom:50px; transition:background 0.3s,color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 40% at 50% -10%, rgba(99,160,240,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 60%); }}
    header {{ padding:14px 16px 12px; display:flex; align-items:center; justify-content:center;
        border-bottom:1px solid var(--border); background:rgba(5,5,5,0.95);
        backdrop-filter:blur(20px); position:sticky; top:0; z-index:100; }}
    :root.light header {{ background:rgba(245,245,240,0.95); }}
    .menu-btn {{ position:absolute; left:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border); color:var(--gold);
        width:36px; height:36px; border-radius:10px; font-size:1em;
        cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.2s; }}
    .menu-btn:hover {{ border-color:var(--gold); }}
    .header-title {{ font-family:'DM Sans',sans-serif; font-size:1em; font-weight:700; color:var(--text); }}
    .theme-toggle {{
        position:absolute; right:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border);
        border-radius:8px; width:34px; height:34px;
        display:flex; align-items:center; justify-content:center;
        cursor:pointer; font-size:1em; transition:all 0.2s; }}
    .theme-toggle:hover {{ border-color:var(--gold); }}
    .nav-dropdown {{ position:absolute; top:calc(100% + 6px); left:10px;
        background:var(--surface2); border:1px solid var(--border); border-radius:var(--radius-lg);
        display:none; z-index:1000; width:270px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.7); }}
    .nav-dropdown a {{ display:flex; align-items:center; gap:10px; padding:10px 16px;
        text-decoration:none; color:var(--text-mid); border-bottom:1px solid var(--border);
        font-size:0.87em; transition:all 0.15s; }}
    .nav-dropdown a:last-child {{ border-bottom:none; }}
    .nav-dropdown a:hover {{ background:var(--surface3); color:var(--text); padding-left:22px; }}
    .nav-group-btn {{ display:flex; justify-content:space-between; align-items:center; width:100%;
        padding:8px 16px; background:none; border:none; font-family:inherit; color:var(--gold);
        font-size:0.7em; font-weight:700; letter-spacing:1px; text-transform:uppercase; cursor:pointer; opacity:0.85; }}
    .nav-group-btn:hover {{ opacity:1; background:var(--surface3); }}
    .nav-arrow {{ font-size:0.85em; transition:transform 0.15s; }}
    .nav-group-items {{ display:none; flex-direction:column; }}
    .nav-group-items.open {{ display:flex; }}
    main {{ padding:14px; max-width:580px; margin:0 auto; animation:fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .summary-card {{ background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-lg);
        padding:16px 18px; margin-bottom:12px; text-align:center; position:relative; overflow:hidden; }}
    .summary-card::before {{ content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent); }}
    .summary-title {{ font-family:'DM Sans',sans-serif; font-size:1.05em; font-weight:800; }}
    .scad-item {{ background:var(--surface); border:1px solid var(--border); border-radius:12px;
        margin-bottom:8px; display:flex; overflow:hidden; }}
    .scad-date {{ background:var(--surface3); color:var(--text-dim); font-size:0.72em; font-weight:700;
        writing-mode:vertical-rl; text-orientation:mixed; padding:10px 6px; flex-shrink:0;
        display:flex; align-items:center; justify-content:center; letter-spacing:1px; }}
    .scad-body {{ padding:10px 14px; flex:1; min-width:0; }}
    .scad-top {{ display:flex; justify-content:space-between; align-items:baseline; gap:8px; }}
    .scad-cat {{ font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.9em; }}
    .scad-amt {{ font-weight:700; font-size:0.9em; flex-shrink:0; }}
    .scad-desc {{ font-size:0.78em; color:var(--text-mid); margin-top:2px; }}
    .scad-meta {{ display:flex; gap:6px; margin-top:8px; flex-wrap:wrap; }}
    .scad-badge {{ background:var(--surface2); border:1px solid var(--border); border-radius:6px;
        padding:2px 8px; font-size:0.68em; color:var(--text-dim); }}
    .btn-home {{ display:block; text-align:center; padding:13px; margin-top:12px;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; border-radius:10px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.9em;
        line-height:1.5; transition:all 0.2s; }}
    .btn-home:hover {{ transform:translateY(-1px); box-shadow:0 6px 20px rgba(201,168,76,0.25); }}
</style>
</head>
<body>
<header>
    <button class="menu-btn" onclick="toggleMenu(event)">⚙️</button>
    <div id="extraMenu" class="nav-dropdown">
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Finanze</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/">🏠 Aggiungi Operazione</a>
                <a href="/lista">📈 Gestione Movimenti Mese</a>
                <a href="/stats">📊 Bilancio Mese</a>
                <a href="/fondo_risparmio_web">💰 Fondo Risparmio</a>
                <a href="/scadenze_web">📅 Scadenze del Mese</a>
                <a href="/fairshare_web">⚖️ FairShare</a>
                <a href="/menu_esplora">🔍 Esplora</a>
                <a href="/grafici_web">📅 Grafici e Statistiche</a>
                <a href="/portafoglio_web">🏦 Portafoglio Bancario</a>
                <a href="/gestione_categorie">⚙️ Gestione Categorie</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Casa</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/utenze?anno={oggi.year}">💧 Utenze</a>
                <a href="/consultazione_supermercati">🛒 Supermercati</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Documenti</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/documenti_pdf_web">🗄️ Documenti Contabili</a>
                <a href="/documenti_personali_web">🗄️ Documenti Personali</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Sistema</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/info_sys_web">📡 Monitor Server</a>
                <a href="/cambia_pw_web">🔑 Cambia Password</a>
                <a href="/webauthn_web">👆 Biometrico</a>
                <a href="/cambia_profilo_web">👤 Cambia Profilo</a>
                <a href="/logoff">🔓 Logout</a>
            </div>
        </div>
    </div>
    <div class="header-title">📅 Scadenze del Mese</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="summary-card">
        <div class="summary-title">Scadenze di {mese_nome} {anno_corrente}</div>
    </div>
    {righe_html}
    <a href="/" class="btn-home">🏠 Torna alla Home</a>
</main>
<script>
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if (btn) btn.textContent = '🌙'; }}
        else               {{ root.classList.remove('light'); if (btn) btn.textContent = '☀️'; }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        applyTheme(next);
    }}
    applyTheme(localStorage.getItem('theme') || 'dark');
    function toggleNavGroup(btn, ev) {{
        if (ev) ev.stopPropagation();
        const items = btn.nextElementSibling;
        const giaAperto = items.classList.contains('open');
        btn.closest('.nav-dropdown').querySelectorAll('.nav-group-items.open').forEach(function(el) {{
            el.classList.remove('open');
            el.previousElementSibling.querySelector('.nav-arrow').textContent = '▶';
        }});
        if (!giaAperto) {{
            items.classList.add('open');
            btn.querySelector('.nav-arrow').textContent = '▼';
        }}
    }}
    function toggleMenu(e) {{
        e.stopPropagation();
        const m = document.getElementById("extraMenu");
        m.style.display = (m.style.display === "block") ? "none" : "block";
    }}
    document.addEventListener("click", function(e) {{
        const m = document.getElementById("extraMenu");
        if (m && m.style.display === "block" && !m.contains(e.target)) m.style.display = "none";
    }});
</script>
</body>
</html>"""

# Html Genera la pagina web dei movimenti del mese corrente con riepilogo entrate/uscite/saldo e azioni di modifica e cancellazione
def html_lista_spese_mensili(self, conto_filtro=""):
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    import datetime
    HOUSEHOLD_LABEL = "Patrimonio Complessivo"
    conto_filtro = (conto_filtro or "").strip()
    try:
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
            _db_portaf_l = json.load(_pf)
        _conti_lista_l = _db_portaf_l.get("conti", [])
    except Exception:
        _conti_lista_l = []
    _agganci_l = costruisci_mappa_conti_da_trasferimenti(PORTAFOGLIO_BANCARIO)
    _uso_ordinale_l = {}
    conto_options_l = f'<option value="" {"selected" if not conto_filtro else ""}>{HOUSEHOLD_LABEL}</option>\n' + "\n".join(
        f'<option value="{c.get("nome","")}" {"selected" if c.get("nome","") == conto_filtro else ""}>{c.get("nome","")}</option>'
        for c in _conti_lista_l
    )
    mesi_it = {
        "January": "gennaio", "February": "febbraio", "March": "marzo",
        "April": "aprile", "May": "maggio", "June": "giugno",
        "July": "luglio", "August": "agosto", "September": "settembre",
        "October": "ottobre", "November": "novembre", "December": "dicembre"
    }
    oggi = datetime.date.today()
    mese_en = oggi.strftime('%B')
    mese_it_corrente = mesi_it.get(mese_en, mese_en)
    titolo_mese = f"{mese_it_corrente.capitalize()} {oggi.year}"
    if conto_filtro:
        titolo_mese += f" · {conto_filtro}"
    current_month_expenses = []
    tot_entrate = 0.0
    tot_uscite = 0.0
    for d, voci in self.spese.items():
        if d.month == oggi.month and d.year == oggi.year:
            for idx, voce in enumerate(voci):
                if isinstance(voce, dict):
                    categoria = voce.get("categoria", "")
                    descrizione = voce.get("descrizione", "")
                    importo = float(voce.get("importo", 0))
                    tipo = voce.get("tipo", "")
                else:
                    categoria = voce[0] if len(voce) >= 1 else ""
                    descrizione = voce[1] if len(voce) >= 2 else ""
                    importo = float(voce[2]) if len(voce) >= 3 else 0.0
                    tipo = voce[3] if len(voce) >= 4 else ""
                tipo = tipo or ""
                nome_conto_voce = campo(voce, "conto", "")
                if not nome_conto_voce:
                    nome_conto_voce = conto_da_mappa(_agganci_l, _uso_ordinale_l, d.strftime("%d-%m-%Y"), importo, tipo or "Uscita")
                if conto_filtro and nome_conto_voce != conto_filtro:
                    continue
                current_month_expenses.append((d, idx, categoria, descrizione, importo, tipo, nome_conto_voce))
                if tipo.strip().lower() == "entrata":
                    tot_entrate += importo
                else:
                    tot_uscite += importo
    saldo_mese = tot_entrate - tot_uscite
    icona_meteo = "☀️" if saldo_mese >= 0 else "⛈️"
    colore_saldo = "#4caf82" if saldo_mese >= 0 else "#e05a5a"
    segno_saldo_mese = "+" if saldo_mese >= 0 else ""
    current_month_expenses.sort(key=lambda x: x[0], reverse=True)
    schede_html = ""
    if not current_month_expenses:
        schede_html = "<p style='text-align:center; color:#555; padding:20px; font-style:italic;'>Nessun movimento registrato.</p>"
    else:
        for d, idx, cat, desc, imp, tipo, nome_conto_voce in current_month_expenses:
            data_str = d.strftime('%d-%m-%Y')
            details_id = f"details_{d.strftime('%Y%m%d')}_{idx}"
            colore_imp = "#4caf82" if tipo.strip().lower() == "entrata" else "#e05a5a"
            segno = "+" if tipo.strip().lower() == "entrata" else "-"
            riga_conto = (
                f'<div class="op-row"><span class="op-lbl">Conto</span><span>{nome_conto_voce}</span></div>'
                if nome_conto_voce else ""
            )
            schede_html += f"""
            <div class="op-item">
                <div class="op-summary" onclick="toggleVisibility('{details_id}', this)">
                    <span class="op-arrow">▶</span>
                    <span class="op-date">{data_str}</span>
                    <span class="op-cat">{cat}</span>
                    <span class="op-amt" style="color:{colore_imp};">€ {segno}{_fmt_it(imp)}</span>
                </div>
                <div id="{details_id}" class="op-details">
                    <div class="op-row"><span class="op-lbl">Tipo</span><span>{tipo}</span></div>
                    <div class="op-row"><span class="op-lbl">Dettaglio</span><span>{desc}</span></div>
                    {riga_conto}
                    <div class="op-row op-actions">
                        <form method="get" action="/modifica" style="flex:1;">
                            <input type="hidden" name="data" value="{data_str}">
                            <input type="hidden" name="idx" value="{idx}">
                            <button type="submit" class="op-btn">✏️ Modifica</button>
                        </form>
                        <button type="button" class="op-btn danger"
                            onclick="event.stopPropagation(); apriModal('{data_str}', '{idx}', '{cat}', '{_fmt_it(imp)}', {'1' if 'ALL·' in desc else '0'})">
                            ❌ Cancella
                        </button>
                    </div>
                </div>
            </div>"""
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>📈 Movimenti Mese</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
    (function() {{
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    }})();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg:#050505; --surface:#0f0f0f; --surface2:#161616; --surface3:#1e1e1e;
        --border:rgba(255,255,255,0.07); --gold:#c9a84c; --blue:#63a0f0;
        --green:#4caf82; --red:#e05a5a; --text:#e8e8e8; --text-dim:#555; --text-mid:#888;
        --radius-lg:18px;
    }}
    :root.light {{
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --gold:#b8902a; --blue:#3d7fd4;
        --green:#3a9068; --red:#cc3333; --text:#1a1a1a; --text-dim:#999; --text-mid:#555;
    }}
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{ font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text);
        min-height:100vh; padding-bottom:50px; transition:background 0.3s,color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 40% at 50% -10%, rgba(99,160,240,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 60%); }}
    header {{ padding:14px 16px 12px; display:flex; align-items:center; justify-content:center;
        border-bottom:1px solid var(--border); background:rgba(5,5,5,0.95);
        backdrop-filter:blur(20px); position:sticky; top:0; z-index:100; }}
    :root.light header {{ background:rgba(245,245,240,0.95); }}
    .menu-btn {{ position:absolute; left:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border); color:var(--gold);
        width:36px; height:36px; border-radius:10px; font-size:1em;
        cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.2s; }}
    .menu-btn:hover {{ border-color:var(--gold); }}
    .header-title {{ font-family:'DM Sans',sans-serif; font-size:1em; font-weight:700; color:var(--text); }}
    .theme-toggle {{
        position:absolute; right:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border);
        border-radius:8px; width:34px; height:34px;
        display:flex; align-items:center; justify-content:center;
        cursor:pointer; font-size:1em; transition:all 0.2s; }}
    .theme-toggle:hover {{ border-color:var(--gold); }}
    .nav-dropdown {{ position:absolute; top:calc(100% + 6px); left:10px;
        background:var(--surface2); border:1px solid var(--border); border-radius:var(--radius-lg);
        display:none; z-index:1000; width:270px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.7); }}
    .nav-dropdown a {{ display:flex; align-items:center; gap:10px; padding:10px 16px;
        text-decoration:none; color:var(--text-mid); border-bottom:1px solid var(--border);
        font-size:0.87em; transition:all 0.15s; }}
    .nav-dropdown a:last-child {{ border-bottom:none; }}
    .nav-dropdown a:hover {{ background:var(--surface3); color:var(--text); padding-left:22px; }}
    .nav-group-btn {{ display:flex; justify-content:space-between; align-items:center; width:100%;
        padding:8px 16px; background:none; border:none; font-family:inherit; color:var(--gold);
        font-size:0.7em; font-weight:700; letter-spacing:1px; text-transform:uppercase; cursor:pointer; opacity:0.85; }}
    .nav-group-btn:hover {{ opacity:1; background:var(--surface3); }}
    .nav-arrow {{ font-size:0.85em; transition:transform 0.15s; }}
    .nav-group-items {{ display:none; flex-direction:column; }}
    .nav-group-items.open {{ display:flex; }}
    main {{ padding:14px; max-width:580px; margin:0 auto; animation:fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .summary-card {{ background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-lg);
        padding:16px 18px; margin-bottom:12px; text-align:center; position:relative; overflow:hidden; }}
    .summary-card::before {{ content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent); }}
    .summary-title {{ font-family:'DM Sans',sans-serif; font-size:1.05em; font-weight:800; margin-bottom:10px; }}
    .summary-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:10px; }}
    .sg-box {{ background:var(--surface2); border:1px solid var(--border); border-radius:10px; padding:9px 12px; }}
    .sg-label {{ display:block; font-size:0.6em; color:var(--text-dim); letter-spacing:1.5px; text-transform:uppercase; margin-bottom:3px; }}
    .sg-val {{ font-family:'DM Sans',sans-serif; font-size:1.05em; font-weight:800; }}
    .saldo-row {{ padding-top:10px; border-top:1px solid var(--border); }}
    .saldo-lbl {{ font-size:0.6em; color:var(--text-dim); letter-spacing:1.5px; text-transform:uppercase; }}
    .saldo-num {{ font-family:'DM Sans',sans-serif; font-size:1.5em; font-weight:800; }}
    .op-item {{ background:var(--surface); border:1px solid var(--border); border-radius:12px; margin-bottom:6px; overflow:hidden; }}
    .op-summary {{ display:flex; align-items:center; padding:11px 14px; cursor:pointer; gap:8px; transition:background 0.15s; }}
    .op-summary:hover {{ background:var(--surface2); }}
    .op-arrow {{ font-size:0.65em; color:var(--text-dim); transition:transform 0.2s; flex-shrink:0; }}
    .op-date {{ color:var(--text-dim); font-size:0.75em; width:72px; flex-shrink:0; }}
    .op-cat {{ font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.85em; flex:1; }}
    .op-amt {{ font-weight:700; font-size:0.9em; flex-shrink:0; }}
    .op-details {{ display:none; border-top:1px solid var(--border); padding:10px 14px; background:var(--surface2); }}
    .op-details.active {{ display:block; }}
    .op-row {{ display:flex; gap:8px; font-size:0.83em; margin-bottom:6px; }}
    .op-lbl {{ color:var(--blue); font-weight:700; width:72px; flex-shrink:0; font-size:0.9em; }}
    .op-actions {{ margin-top:8px; gap:8px; }}
    .op-btn {{ flex:1; padding:9px; border-radius:8px; border:1px solid var(--border);
        background:var(--surface); color:var(--text-mid); font-size:0.82em; cursor:pointer; transition:all 0.15s;
        font-family:'DM Sans',sans-serif; line-height:1.5; }}
    .op-btn:hover {{ border-color:var(--blue); color:var(--text); }}
    .op-btn.danger {{ border-color:var(--red); color:var(--red); }}
    .op-btn.danger:hover {{ background:rgba(224,90,90,0.1); }}
    .modal-overlay {{ display:none; position:fixed; inset:0;
        background:rgba(0,0,0,0.75); backdrop-filter:blur(6px);
        z-index:3000; align-items:center; justify-content:center; }}
    .modal-box {{ background:var(--surface2); border:1px solid var(--border);
        border-radius:var(--radius-lg); padding:24px 20px; width:88%; max-width:320px; text-align:center; }}
    .modal-title {{ font-family:'DM Sans',sans-serif; font-size:1em; font-weight:800; color:var(--red); margin-bottom:10px; }}
    .modal-text {{ font-size:0.88em; color:var(--text-mid); margin-bottom:18px; }}
    .modal-btns {{ display:flex; gap:10px; }}
    .m-btn {{ flex:1; padding:12px; border-radius:9px; border:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.88em; cursor:pointer; transition:all 0.15s; }}
    .m-cancel {{ background:var(--surface3); color:var(--text-mid); }}
    .m-confirm {{ background:var(--red); color:white; }}
    .m-confirm:hover {{ box-shadow:0 4px 14px rgba(224,90,90,0.3); }}
    .btn-home {{ display:block; text-align:center; padding:13px; margin-top:12px;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; border-radius:10px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.9em;
        line-height:1.5; transition:all 0.2s; }}
    .btn-home:hover {{ transform:translateY(-1px); box-shadow:0 6px 20px rgba(201,168,76,0.25); }}
</style>
</head>
<body>
<header>
    <button class="menu-btn" onclick="toggleMenu(event)">⚙️</button>
    <div id="extraMenu" class="nav-dropdown">
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Finanze</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/">🏠 Aggiungi Operazione</a>
                <a href="/lista">📈 Gestione Movimenti Mese</a>
                <a href="/stats">📊 Bilancio Mese</a>
                <a href="/fondo_risparmio_web">💰 Fondo Risparmio</a>
                <a href="/scadenze_web">📅 Scadenze del Mese</a>
                <a href="/fairshare_web">⚖️ FairShare</a>
                <a href="/menu_esplora">🔍 Esplora</a>
                <a href="/grafici_web">📅 Grafici e Statistiche</a>
                <a href="/portafoglio_web">🏦 Portafoglio Bancario</a>
                <a href="/gestione_categorie">⚙️ Gestione Categorie</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Casa</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/utenze?anno={oggi.year}">💧 Utenze</a>
                <a href="/consultazione_supermercati">🛒 Supermercati</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Documenti</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/documenti_pdf_web">🗄️ Documenti Contabili</a>
                <a href="/documenti_personali_web">🗄️ Documenti Personali</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Sistema</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/info_sys_web">📡 Monitor Server</a>
                <a href="/cambia_pw_web">🔑 Cambia Password</a>
                <a href="/webauthn_web">👆 Biometrico</a>
                <a href="/cambia_profilo_web">👤 Cambia Profilo</a>
                <a href="/logoff">🔓 Logout</a>
            </div>
        </div>
    </div>
    <div class="header-title">📈 Gestione Movimenti Mese</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <form method="get" action="/lista" style="margin-bottom:12px;">
        <select name="conto" onchange="this.form.submit()"
            style="width:100%; padding:11px 14px; border-radius:12px; border:1px solid var(--border);
                   background:var(--surface); color:var(--text); font-family:'DM Sans',sans-serif;
                   font-size:0.88em; font-weight:700;">
            {conto_options_l}
        </select>
    </form>
    <div class="summary-card">
        <div class="summary-title">{titolo_mese} {icona_meteo}</div>
        <div class="summary-grid">
            <div class="sg-box">
                <span class="sg-label">Entrate</span>
                <span class="sg-val" style="color:var(--green);">€ +{_fmt_it(tot_entrate)}</span>
            </div>
            <div class="sg-box">
                <span class="sg-label">Uscite</span>
                <span class="sg-val" style="color:var(--red);">€ -{_fmt_it(tot_uscite)}</span>
            </div>
        </div>
        <div class="saldo-row">
            <div class="saldo-lbl">Saldo attuale</div>
            <div class="saldo-num" style="color:{colore_saldo};">€ {segno_saldo_mese}{_fmt_it(saldo_mese)}</div>
        </div>
    </div>
    {schede_html}
    <a href="/" class="btn-home">🏠 Torna alla Home</a>
</main>
<div id="deleteModal" class="modal-overlay">
    <div class="modal-box">
        <div class="modal-title">❌ Conferma Eliminazione</div>
        <div class="modal-text" id="modalText"></div>
        <div class="modal-btns">
            <button class="m-btn m-cancel" onclick="closeDeleteModal()">Annulla</button>
            <button id="finalDeleteBtn" class="m-btn m-confirm">Elimina</button>
        </div>
    </div>
</div>
<div id="pdfModal" class="modal-overlay" style="display:none;">
    <div class="modal-box">
        <div class="modal-title">📎 Documento Allegato</div>
        <div class="modal-text">Vuoi eliminare anche il documento PDF dal registro?</div>
        <div class="modal-btns">
            <button class="m-btn m-cancel" onclick="confermaCancella(0)">Solo Movimento</button>
            <button class="m-btn m-confirm" onclick="confermaCancella(1)">Elimina Tutto</button>
        </div>
    </div>
</div>
<script>
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if (btn) btn.textContent = '🌙'; }}
        else               {{ root.classList.remove('light'); if (btn) btn.textContent = '☀️'; }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        applyTheme(next);
    }}
    applyTheme(localStorage.getItem('theme') || 'dark');
    let dData = null, dIdx = null, dHaPdf = false;
    function apriModal(data, idx, cat, imp, ha_pdf) {{
        dData = data; dIdx = idx; dHaPdf = (ha_pdf === '1' || ha_pdf === 1);
        document.getElementById("modalText").innerHTML = "Vuoi eliminare <b>" + cat + "</b> da <b>€ " + imp + "</b>?";
        document.getElementById("deleteModal").style.display = "flex";
    }}
    function closeDeleteModal() {{ document.getElementById("deleteModal").style.display = "none"; }}
    document.getElementById("finalDeleteBtn").onclick = function() {{
        closeDeleteModal();
        if (dHaPdf) {{
            document.getElementById("pdfModal").style.display = "flex";
        }} else {{
            confermaCancella(0);
        }}
    }};
    function confermaCancella(elimina_pdf) {{
        document.getElementById("pdfModal").style.display = "none";
        fetch('/cancella', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
            body: 'data=' + encodeURIComponent(dData) + '&idx=' + encodeURIComponent(dIdx) + '&elimina_pdf=' + elimina_pdf
        }}).then(() => window.location.reload());
    }}
    function toggleNavGroup(btn, ev) {{
        if (ev) ev.stopPropagation();
        const items = btn.nextElementSibling;
        const giaAperto = items.classList.contains('open');
        btn.closest('.nav-dropdown').querySelectorAll('.nav-group-items.open').forEach(function(el) {{
            el.classList.remove('open');
            el.previousElementSibling.querySelector('.nav-arrow').textContent = '▶';
        }});
        if (!giaAperto) {{
            items.classList.add('open');
            btn.querySelector('.nav-arrow').textContent = '▼';
        }}
    }}
    function toggleMenu(e) {{
        e.stopPropagation();
        const m = document.getElementById("extraMenu");
        m.style.display = (m.style.display === "block") ? "none" : "block";
    }}
    document.addEventListener("click", function(e) {{
        const m = document.getElementById("extraMenu");
        if (m && m.style.display === "block" && !m.contains(e.target)) m.style.display = "none";
    }});
    function toggleVisibility(id, el) {{
        const c = document.getElementById(id);
        const a = el.querySelector(".op-arrow");
        if (c) c.classList.toggle("active");
        if (a) a.style.transform = c.classList.contains("active") ? "rotate(90deg)" : "rotate(0deg)";
    }}
</script>
</body>
</html>"""

# Html Bilancio Mese corrente con riepilogo entrate/uscite/saldo per categoria
def stats_mensili_html(self, conto_filtro=""):
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    HOUSEHOLD_LABEL = "Patrimonio Complessivo"
    conto_filtro = (conto_filtro or "").strip()
    try:
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
            _db_portaf_s = json.load(_pf)
        _conti_lista_s = _db_portaf_s.get("conti", [])
    except Exception:
        _conti_lista_s = []
    _agganci_s = costruisci_mappa_conti_da_trasferimenti(PORTAFOGLIO_BANCARIO)
    _uso_ordinale_s = {}
    conto_options_s = f'<option value="" {"selected" if not conto_filtro else ""}>{HOUSEHOLD_LABEL}</option>\n' + "\n".join(
        f'<option value="{c.get("nome","")}" {"selected" if c.get("nome","") == conto_filtro else ""}>{c.get("nome","")}</option>'
        for c in _conti_lista_s
    )
    mesi_it = {
        "January": "gennaio", "February": "febbraio", "March": "marzo",
        "April": "aprile", "May": "maggio", "June": "giugno",
        "July": "luglio", "August": "agosto", "September": "settembre",
        "October": "ottobre", "November": "novembre", "December": "dicembre"
    }
    oggi = datetime.date.today()
    mese_en = oggi.strftime('%B')
    mese_it_corrente = mesi_it.get(mese_en, mese_en)
    titolo_mese = f"{mese_it_corrente.capitalize()} {oggi.year}"
    if conto_filtro:
        titolo_mese += f" · {conto_filtro}"
    entrate = 0.0
    uscite = 0.0
    entrate_categorie = {}
    uscite_categorie = {}
    raw_entrate_dettaglio = {}
    raw_uscite_dettaglio = {}
    entrate_count = {}
    uscite_count = {}
    for d, voci in self.spese.items():
        if d.month == oggi.month and d.year == oggi.year:
            for voce in voci:
                categoria, descrizione, importo, tipo = voce[:4]
                if conto_filtro:
                    nome_conto_voce = campo(voce, "conto", "")
                    if not nome_conto_voce:
                        nome_conto_voce = conto_da_mappa(_agganci_s, _uso_ordinale_s, d.strftime("%d-%m-%Y"), importo, tipo or "Uscita")
                    if nome_conto_voce != conto_filtro:
                        continue
                if tipo == "Entrata":
                    entrate += importo
                    entrate_categorie[categoria] = entrate_categorie.get(categoria, 0.0) + importo
                    raw_entrate_dettaglio.setdefault(categoria, []).append((d, descrizione, importo))
                    entrate_count[categoria] = entrate_count.get(categoria, 0) + 1
                else:
                    uscite += importo
                    uscite_categorie[categoria] = uscite_categorie.get(categoria, 0.0) + importo
                    raw_uscite_dettaglio.setdefault(categoria, []).append((d, descrizione, importo))
                    uscite_count[categoria] = uscite_count.get(categoria, 0) + 1
    saldo = entrate - uscite
    saldo_colore = "#4caf82" if saldo >= 0 else "#e05a5a"
    meteo_saldo = "☀️" if saldo >= 0 else "🌧️"
    segno_saldo = "+" if saldo >= 0 else ""

    def genera_html_categorie(categorie_totals, raw_dettaglio, prefix, counts_dict):
        html_content = ""
        if not categorie_totals:
            return f"<p class='no-data-msg'>Nessuna {prefix} per categoria da mostrare.</p>"
        html_content += "<ul class='category-list'>"
        for cat, totale in sorted(categorie_totals.items()):
            voci_dettaglio = raw_dettaglio.get(cat, [])
            dettagli_id = f"{prefix}_{''.join(filter(str.isalnum, cat))}"
            arrow_button_html = ''
            if voci_dettaglio:
                arrow_button_html = f"""<button type="button" class="cat-arrow-btn" onclick="toggleCat('{dettagli_id}', this)" aria-expanded="false"><span class="cat-arrow">▶</span></button>"""
            color_class = "amt-income" if prefix == "entrate" else "amt-expense"
            segno_cat = "+" if prefix == "entrate" else "-"
            dettaglio_items_html = ''.join(
                f'<li class="det-item"><span class="det-text">{data.strftime("%d-%m-%Y")}{" — " + desc if desc else ""}</span><span class="det-amt {color_class}">€ {segno_cat}{_fmt_it(imp)}</span></li>'
                for data, desc, imp, *_ in voci_dettaglio
            )
            if not dettaglio_items_html:
                dettaglio_items_html = '<li class="det-item" style="color:var(--text-dim)">Nessun dettaglio.</li>'
            num_ops = counts_dict.get(cat, 0)
            budget_cat = self.budget_categorie.get(cat, 0) if prefix == "uscite" else 0
            sfora_budget = budget_cat > 0 and totale > budget_cat
            budget_info_html = ''
            if budget_cat > 0:
                budget_info_html = f'<span class="cat-budget{" over" if sfora_budget else ""}">{"⚠️ " if sfora_budget else ""}budget € {_fmt_it(budget_cat)}</span>'
            item_class = "cat-item over-budget" if sfora_budget else "cat-item"
            html_content += f"""
            <li class="{item_class}">
                <div class="cat-summary">
                    {arrow_button_html}
                    <span class="cat-name"><span class="cat-name-row">{cat} <small>({num_ops})</small></span>{budget_info_html}</span>
                    <span class="cat-total {color_class}">€ {segno_cat}{_fmt_it(totale)}</span>
                </div>
                <ul id="{dettagli_id}" class="cat-details hidden">{dettaglio_items_html}</ul>
            </li>"""
        html_content += "</ul>"
        return html_content
    categorie_uscite_html  = genera_html_categorie(uscite_categorie,  raw_uscite_dettaglio,  "uscite",  uscite_count)
    categorie_entrate_html = genera_html_categorie(entrate_categorie, raw_entrate_dettaglio, "entrate", entrate_count)
    COMMON_HEAD = """
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
        --border:rgba(255,255,255,0.07); --gold:#c9a84c; --blue:#63a0f0;
        --green:#4caf82; --red:#e05a5a; --text:#e8e8e8;
        --text-dim:#555; --text-mid:#888; --radius-lg:18px;
    }
    :root.light {
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --gold:#b8902a; --blue:#3d7fd4;
        --green:#3a9068; --red:#cc3333; --text:#1a1a1a;
        --text-dim:#999; --text-mid:#555;
    }
    * { box-sizing:border-box; margin:0; padding:0; }
    body { font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text);
        min-height:100vh; padding-bottom:50px; transition:background 0.3s,color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 40% at 50% -10%, rgba(99,160,240,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 60%); }
    header { padding:14px 16px 12px; display:flex; align-items:center; justify-content:center;
        border-bottom:1px solid var(--border); background:rgba(5,5,5,0.95);
        backdrop-filter:blur(20px); position:sticky; top:0; z-index:100; }
    :root.light header { background:rgba(245,245,240,0.95); }
    .menu-btn { position:absolute; left:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border); color:var(--gold);
        width:36px; height:36px; border-radius:10px; font-size:1em;
        cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.2s; }
    .menu-btn:hover { border-color:var(--gold); box-shadow:0 0 12px rgba(201,168,76,0.2); }
    .header-title { font-family:'DM Sans',sans-serif; font-size:1em; font-weight:700; color:var(--text); }
    .theme-toggle {
        position:absolute; right:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border);
        border-radius:8px; width:34px; height:34px;
        display:flex; align-items:center; justify-content:center;
        cursor:pointer; font-size:1em; transition:all 0.2s; }
    .theme-toggle:hover { border-color:var(--gold); }
    .nav-dropdown { position:absolute; top:calc(100% + 6px); left:10px;
        background:var(--surface2); border:1px solid var(--border); border-radius:var(--radius-lg);
        display:none; z-index:1000; width:270px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.7); }
    .nav-dropdown a { display:flex; align-items:center; gap:10px; padding:10px 16px;
        text-decoration:none; color:var(--text-mid); border-bottom:1px solid var(--border);
        font-size:0.87em; transition:all 0.15s; }
    .nav-dropdown a:last-child { border-bottom:none; }
    .nav-dropdown a:hover { background:var(--surface3); color:var(--text); padding-left:22px; }
    .nav-group-btn { display:flex; justify-content:space-between; align-items:center; width:100%;
        padding:8px 16px; background:none; border:none; font-family:inherit; color:var(--gold);
        font-size:0.7em; font-weight:700; letter-spacing:1px; text-transform:uppercase; cursor:pointer; opacity:0.85; }
    .nav-group-btn:hover { opacity:1; background:var(--surface3); }
    .nav-arrow { font-size:0.85em; transition:transform 0.15s; }
    .nav-group-items { display:none; flex-direction:column; }
    .nav-group-items.open { display:flex; }
    main { padding:14px; max-width:580px; margin:0 auto; animation:fadeIn 0.3s ease; }
    @keyframes fadeIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
    .btn-home { display:block; text-align:center; padding:13px; margin-top:12px;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; border-radius:10px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.9em;
        line-height:1.5; transition:all 0.2s; }
    .btn-home:hover { transform:translateY(-1px); box-shadow:0 6px 20px rgba(201,168,76,0.25); }
    .amt-income { color:var(--green); }
    .amt-expense { color:var(--red); }
</style>"""
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>📊 Bilancio Mese</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
{COMMON_HEAD}
<style>
    .stats-card {{ background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-lg);
        padding:18px; margin-bottom:12px; position:relative; overflow:hidden; text-align:center; }}
    .stats-card::before {{ content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent); }}
    .stats-title {{ font-family:'DM Sans',sans-serif; font-size:1.05em; font-weight:800; margin-bottom:12px; }}
    .stats-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:12px; }}
    .stat-box {{ background:var(--surface2); border:1px solid var(--border); border-radius:10px; padding:10px; }}
    .stat-label {{ display:block; font-size:0.6em; color:var(--text-dim); letter-spacing:1.5px; text-transform:uppercase; margin-bottom:3px; }}
    .stat-val {{ font-family:'DM Sans',sans-serif; font-size:1.1em; font-weight:800; }}
    .saldo-row {{ padding-top:10px; border-top:1px solid var(--border); }}
    .saldo-label {{ font-size:0.62em; color:var(--text-dim); letter-spacing:1.5px; text-transform:uppercase; }}
    .saldo-val {{ font-family:'DM Sans',sans-serif; font-size:1.5em; font-weight:800; }}
    .sec-toggle {{ width:100%; padding:13px 16px; margin-bottom:6px;
        background:var(--surface); border:1px solid var(--border); border-radius:12px;
        color:var(--text); font-family:'DM Sans',sans-serif; font-size:0.88em; font-weight:700;
        line-height:1.5; display:flex; justify-content:space-between; align-items:center;
        cursor:pointer; transition:background 0.15s; }}
    .sec-toggle:hover {{ background:var(--surface2); }}
    .sec-arrow {{ font-size:0.7em; color:var(--text-dim); transition:transform 0.22s; }}
    .collapsible-content {{ display:none; }}
    .collapsible-content.active {{ display:block; }}
    .no-data-msg {{ text-align:center; color:var(--text-dim); font-size:0.85em; padding:16px; font-style:italic; }}
    .category-list {{ list-style:none; padding:0; margin:0 0 10px 0; display:flex; flex-direction:column; gap:5px; }}
    .cat-item {{ background:var(--surface2); border:1px solid var(--border); border-radius:10px; overflow:hidden; }}
    .cat-summary {{ display:flex; align-items:center; gap:8px; padding:10px 14px; }}
    .cat-arrow-btn {{ background:none; border:none; cursor:pointer; padding:0; display:flex; align-items:center; color:var(--text-dim); }}
    .cat-arrow {{ font-size:0.7em; transition:transform 0.22s; }}
    .cat-arrow.open {{ transform:rotate(90deg); }}
    .cat-name {{ flex:1; font-size:0.88em; color:var(--text); display:flex; flex-direction:column; gap:1px; }}
    .cat-name small {{ color:var(--text-dim); font-size:0.8em; }}
    .cat-budget {{ font-size:0.78em; color:var(--text-dim); }}
    .cat-budget.over {{ color:var(--red); font-weight:700; }}
    .cat-item.over-budget {{ background:rgba(224,90,90,0.09); }}
    .cat-total {{ font-weight:700; font-size:0.9em; }}
    .cat-details {{ list-style:none; padding:8px 14px 10px; border-top:1px solid var(--border); display:flex; flex-direction:column; gap:5px; }}
    .cat-details.hidden {{ display:none; }}
    .det-item {{ display:flex; justify-content:space-between; align-items:baseline; font-size:0.82em; color:var(--text-mid); padding:2px 0; }}
    .det-text {{ flex:1; padding-right:10px; }}
    .det-amt {{ font-weight:600; flex-shrink:0; }}
</style>
</head>
<body>
<header>
    <button class="menu-btn" onclick="toggleMenu(event)">⚙️</button>
    <div id="extraMenu" class="nav-dropdown">
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Finanze</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/">🏠 Aggiungi Operazione</a>
                <a href="/lista">📈 Gestione Movimenti Mese</a>
                <a href="/stats">📊 Bilancio Mese</a>
                <a href="/fondo_risparmio_web">💰 Fondo Risparmio</a>
                <a href="/scadenze_web">📅 Scadenze del Mese</a>
                <a href="/fairshare_web">⚖️ FairShare</a>
                <a href="/menu_esplora">🔍 Esplora</a>
                <a href="/grafici_web">📅 Grafici e Statistiche</a>
                <a href="/portafoglio_web">🏦 Portafoglio Bancario</a>
                <a href="/gestione_categorie">⚙️ Gestione Categorie</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Casa</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/utenze?anno={datetime.date.today().year}">💧 Utenze</a>
                <a href="/consultazione_supermercati">🛒 Gestione Supermercati</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Documenti</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/documenti_pdf_web">🗄️ Documenti Contabili</a>
                <a href="/documenti_personali_web">🗄️ Documenti Personali</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Sistema</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/info_sys_web">📡 Monitor Server</a>
                <a href="/cambia_pw_web">🔑 Cambia Password</a>
                <a href="/webauthn_web">👆 Biometrico</a>
                <a href="/cambia_profilo_web">👤 Cambia Profilo</a>
                <a href="/logoff">🔓 Logout</a>
            </div>
        </div>
    </div>
    <div class="header-title">⚖️ Andamento Mensile</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <form method="get" action="/stats" style="margin-bottom:12px;">
        <select name="conto" onchange="this.form.submit()"
            style="width:100%; padding:11px 14px; border-radius:12px; border:1px solid var(--border);
                   background:var(--surface); color:var(--text); font-family:'DM Sans',sans-serif;
                   font-size:0.88em; font-weight:700;">
            {conto_options_s}
        </select>
    </form>
    <div class="stats-card">
        <div class="stats-title">📊 {titolo_mese} {meteo_saldo}</div>
        <div class="stats-grid">
            <div class="stat-box">
                <span class="stat-label">Entrate</span>
                <span class="stat-val amt-income">€ +{_fmt_it(entrate)}</span>
            </div>
            <div class="stat-box">
                <span class="stat-label">Uscite</span>
                <span class="stat-val amt-expense">€ -{_fmt_it(uscite)}</span>
            </div>
        </div>
        <div class="saldo-row">
            <div class="saldo-label">Saldo attuale</div>
            <div class="saldo-val" style="color:{saldo_colore};">€ {segno_saldo}{_fmt_it(saldo)}</div>
        </div>
    </div>
    <button type="button" class="sec-toggle" onclick="toggleSec('usciteCatContent', this)">
        <span>🧮 Uscite per Categoria</span>
        <span class="sec-arrow">▶</span>
    </button>
    <div id="usciteCatContent" class="collapsible-content">
        {categorie_uscite_html}
    </div>
    <button type="button" class="sec-toggle" onclick="toggleSec('entrateCatContent', this)">
        <span>📥 Entrate per Categoria</span>
        <span class="sec-arrow">▶</span>
    </button>
    <div id="entrateCatContent" class="collapsible-content">
        {categorie_entrate_html}
    </div>
    <a href="/" class="btn-home">🏠 Torna alla Home</a>
</main>
<script>
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if (btn) btn.textContent = '🌙'; }}
        else               {{ root.classList.remove('light'); if (btn) btn.textContent = '☀️'; }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        applyTheme(next);
    }}
    applyTheme(localStorage.getItem('theme') || 'dark');
    function toggleNavGroup(btn, ev) {{
        if (ev) ev.stopPropagation();
        const items = btn.nextElementSibling;
        const giaAperto = items.classList.contains('open');
        btn.closest('.nav-dropdown').querySelectorAll('.nav-group-items.open').forEach(function(el) {{
            el.classList.remove('open');
            el.previousElementSibling.querySelector('.nav-arrow').textContent = '▶';
        }});
        if (!giaAperto) {{
            items.classList.add('open');
            btn.querySelector('.nav-arrow').textContent = '▼';
        }}
    }}
    function toggleMenu(e) {{
        e.stopPropagation();
        const m = document.getElementById("extraMenu");
        m.style.display = m.style.display === "block" ? "none" : "block";
    }}
    document.addEventListener("click", function(e) {{
        const m = document.getElementById("extraMenu");
        const btn = document.querySelector(".menu-btn");
        if (m && m.style.display === "block" && !m.contains(e.target) && e.target !== btn)
            m.style.display = "none";
    }});
    function toggleSec(id, btn) {{
        const c = document.getElementById(id);
        const a = btn.querySelector(".sec-arrow");
        const open = c.classList.toggle("active");
        if (a) a.style.transform = open ? "rotate(90deg)" : "rotate(0deg)";
    }}
    function toggleCat(id, btn) {{
        const c = document.getElementById(id);
        const a = btn.querySelector(".cat-arrow");
        c.classList.toggle("hidden");
        if (a) a.classList.toggle("open");
    }}
</script>
</body>
</html>"""
