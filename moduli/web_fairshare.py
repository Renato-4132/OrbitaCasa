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


def html_fairshare_web(self):
    anno_corrente = str(datetime.date.today().year)
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>⚖️ FairShare</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>(function() {{ if (localStorage.getItem('theme') === 'light') document.documentElement.classList.add('light'); }})();</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
    :root {{
        --bg:#050505; --surface:#0f0f0f; --surface2:#161616; --surface3:#1e1e1e;
        --border:rgba(255,255,255,0.07); --gold:#c9a84c; --blue:#63a0f0;
        --green:#4caf82; --red:#e05a5a; --text:#e8e8e8; --text-dim:#555; --text-mid:#888;
        --radius-lg:16px;
    }}
    :root.light {{
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --gold:#b8902a; --blue:#3d7fd4;
        --green:#3a9068; --red:#cc3333; --text:#1a1a1a; --text-dim:#999; --text-mid:#555;
    }}
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{
        font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text);
        min-height:100vh; padding-bottom:40px;
    }}
    header {{
        padding:12px 16px; display:flex; align-items:center; justify-content:center;
        border-bottom:1px solid var(--border); background:rgba(5,5,5,0.95);
        backdrop-filter:blur(20px); position:sticky; top:0; z-index:100;
    }}
    :root.light header {{ background:rgba(245,245,240,0.95); }}
    .menu-btn {{
        position:absolute; left:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border); color:var(--gold);
        width:34px; height:34px; border-radius:9px; font-size:1em;
        cursor:pointer; display:flex; align-items:center; justify-content:center;
    }}
    .theme-toggle {{
        position:absolute; right:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border);
        border-radius:8px; width:34px; height:34px;
        display:flex; align-items:center; justify-content:center; cursor:pointer;
    }}
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
    main {{ padding:12px 14px; max-width:680px; margin:0 auto; }}
    .filtri {{ display:flex; gap:8px; flex-wrap:wrap; margin:12px 0; }}
    .filtri select {{
        flex:1; min-width:100px; padding:9px 12px;
        background:var(--surface2); border:1px solid var(--border);
        border-radius:9px; color:var(--text); font-family:'DM Sans',sans-serif;
        font-size:0.88em; outline:none; cursor:pointer;
        -webkit-appearance:none; appearance:none;
    }}
    .btn-aggiorna {{
        padding:9px 20px; background:linear-gradient(135deg,var(--gold),#8a6820);
        color:#000; border:none; border-radius:9px; font-family:'DM Sans',sans-serif;
        font-weight:700; font-size:0.88em; cursor:pointer; white-space:nowrap;
    }}
    .section-title {{
        font-size:0.7em; font-weight:700; letter-spacing:2px; text-transform:uppercase;
        color:var(--text-dim); margin:18px 0 8px;
    }}
    .card {{
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); overflow:hidden; margin-bottom:10px;
    }}
    .totali-bar {{ display:grid; grid-template-columns:1fr 1fr; gap:6px; padding:12px; }}
    .tot-item {{
        background:var(--surface2); border-radius:8px; padding:9px 8px;
        text-align:center; border:1px solid var(--border);
    }}
    .tot-item small {{
        display:block; font-size:0.6em; color:var(--text-dim);
        letter-spacing:1.2px; text-transform:uppercase; margin-bottom:3px;
    }}
    .tot-item b {{ font-size:0.95em; font-weight:700; }}
    table {{ width:100%; border-collapse:collapse; font-size:0.82em; }}
    th {{
        padding:8px 10px; text-align:left; font-size:0.65em; font-weight:700;
        letter-spacing:1.5px; text-transform:uppercase; color:var(--text-dim);
        border-bottom:1px solid var(--border);
    }}
    td {{ padding:9px 10px; border-bottom:1px solid var(--border); vertical-align:middle; }}
    tr:last-child td {{ border-bottom:none; }}
    tr:hover td {{ background:var(--surface2); }}
    .saldo-ok  {{ color:var(--green); font-weight:700; }}
    .saldo-no  {{ color:var(--red);   font-weight:700; }}
    .saldo-zer {{ color:var(--text-mid); }}
    .chart-wrap {{ padding:14px; position:relative; height:220px; }}
    .tabs {{ display:flex; border-bottom:1px solid var(--border); }}
    .tab {{
        padding:10px 16px; font-size:0.78em; font-weight:600; cursor:pointer;
        color:var(--text-mid); border-bottom:2px solid transparent; transition:all 0.2s;
    }}
    .tab.active {{ color:var(--gold); border-bottom-color:var(--gold); }}
    .tab-content {{ display:none; }}
    .tab-content.active {{ display:block; }}
    .chi-row {{
        display:flex; justify-content:space-between; align-items:center;
        padding:10px 14px; border-bottom:1px solid var(--border); font-size:0.88em;
    }}
    .chi-row:last-of-type {{ border-bottom:none; }}
    .pers-card {{
        background:var(--surface2); border-radius:10px; padding:12px;
        margin-bottom:8px; border:1px solid var(--border);
    }}
    .pers-name {{ font-size:0.88em; font-weight:700; margin-bottom:8px; }}
    .pers-totali {{ display:flex; gap:6px; margin-bottom:10px; }}
    .pers-tot {{
        flex:1; background:var(--surface); border-radius:7px; padding:6px 8px;
        text-align:center; border:1px solid var(--border);
    }}
    .pers-tot small {{ display:block; font-size:0.58em; color:var(--text-dim); letter-spacing:1px; text-transform:uppercase; }}
    .pers-tot b {{ font-size:0.85em; font-weight:700; }}
    .pers-chart-wrap {{ position:relative; height:160px; }}
    #loading {{ text-align:center; padding:40px; color:var(--text-dim); font-size:0.85em; }}
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
                <a href="/utenze?anno={anno_corrente}">💧 Utenze</a>
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
    <div style="text-align:center">
        <div style="font-size:0.95em;font-weight:700">⚖️ FairShare</div>
        <div style="font-size:0.6em;color:var(--text-dim);letter-spacing:2px;text-transform:uppercase">Dare & Avere</div>
    </div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()">🌙</button>
</header>
<main>
    <div class="filtri">
        <select id="f_anno"><option value="0">Tutti gli anni</option></select>
        <select id="f_mese">
            <option value="0">Tutti i mesi</option>
            <option value="1">Gennaio</option><option value="2">Febbraio</option>
            <option value="3">Marzo</option><option value="4">Aprile</option>
            <option value="5">Maggio</option><option value="6">Giugno</option>
            <option value="7">Luglio</option><option value="8">Agosto</option>
            <option value="9">Settembre</option><option value="10">Ottobre</option>
            <option value="11">Novembre</option><option value="12">Dicembre</option>
        </select>
        <select id="f_utente"><option value="tutti">Tutti</option></select>
        <button class="btn-aggiorna" onclick="carica()">↻ Aggiorna</button>
    </div>
    <div id="loading">⏳ Caricamento...</div>
    <div id="contenuto" style="display:none">
        <div class="tabs">
            <div class="tab active" onclick="switchTab('tab_da')">👥 Dare & Avere</div>
            <div class="tab" onclick="switchTab('tab_pers')">⚖️ Personali</div>
        </div>
        <div id="tab_da" class="tab-content active">
            <div class="section-title">Riepilogo</div>
            <div class="card">
                <div class="totali-bar">
                    <div class="tot-item">
                        <small>Totale Dovuto</small>
                        <b id="tot_dovuto" style="color:var(--gold)">-</b>
                    </div>
                    <div class="tot-item">
                        <small>Residuo Aperto</small>
                        <b id="tot_residuo" style="color:var(--red)">-</b>
                    </div>
                </div>
                <div class="chart-wrap">
                    <canvas id="chartDA"></canvas>
                </div>
            </div>
            <div class="section-title">Per Persona</div>
            <div class="card" style="overflow-x:auto">
                <table>
                    <thead>
                        <tr>
                            <th>Persona</th>
                            <th>Dovuto</th>
                            <th>Versato</th>
                            <th>Residuo</th>
                        </tr>
                    </thead>
                    <tbody id="tbody_da"></tbody>
                </table>
            </div>
            <div class="section-title">💸 Chi Deve a Chi</div>
            <div class="card">
                <div id="chi_deve_list"></div>
            </div>
        </div>
        <div id="tab_pers" class="tab-content">
            <div class="section-title">Conti Personali ⚖️</div>
            <div id="pers_container"></div>
        </div>
    </div>
</main>
<script>
    const ANNO_CORRENTE = "{anno_corrente}";
    let chartDA = null;
    let chartsPers = {{}};
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if(btn) btn.textContent='🌙'; }}
        else {{ root.classList.remove('light'); if(btn) btn.textContent='☀️'; }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme')||'dark')==='dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next); applyTheme(next);
    }}
    applyTheme(localStorage.getItem('theme')||'dark');

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
        m.style.display = m.style.display==="block" ? "none" : "block";
    }}
    document.addEventListener("click", function(e) {{
        const m = document.getElementById("extraMenu");
        if (m && m.style.display==="block" && !m.contains(e.target) && !e.target.matches('.menu-btn'))
            m.style.display = "none";
    }});
    function switchTab(id) {{
        document.querySelectorAll('.tab').forEach((t,i) => {{
            t.classList.toggle('active', ['tab_da','tab_pers'][i] === id);
        }});
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.getElementById(id).classList.add('active');
    }}
    function fmt(v) {{
        v = Number(v || 0);
        const neg = v < 0;
        const parts = Math.abs(v).toFixed(2).split('.');
        parts[0] = parts[0].replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, '.');
        return "€ " + (neg ? '-' : '') + parts[0] + ',' + parts[1];
    }}
    async function carica() {{
        const anno   = document.getElementById("f_anno").value;
        const mese   = document.getElementById("f_mese").value;
        const utente = document.getElementById("f_utente").value;
        document.getElementById("loading").style.display = "block";
        document.getElementById("contenuto").style.display = "none";
        try {{
            const r = await fetch(`/get_fairshare_data?anno=${{anno}}&mese=${{mese}}&utente=${{encodeURIComponent(utente)}}`);
            const d = await r.json();
            renderDA(d);
            renderPersonali(d);
            aggiornaFiltriUtenti(d);
            document.getElementById("loading").style.display = "none";
            document.getElementById("contenuto").style.display = "block";
        }} catch(e) {{
            document.getElementById("loading").innerHTML = "❌ Errore caricamento dati";
        }}
    }}
    function aggiornaFiltriUtenti(d) {{
        const sel = document.getElementById("f_utente");
        const cur = sel.value;
        while (sel.options.length > 1) sel.remove(1);
        (d.utenti_personali||[]).forEach(n => {{
            const o = document.createElement("option");
            o.value = n; o.textContent = "⚖️ " + n;
            sel.appendChild(o);
        }});
        sel.value = cur || "tutti";
    }}
    function renderDA(d) {{
        document.getElementById("tot_dovuto").textContent  = fmt(d.tot_dovuto);
        document.getElementById("tot_residuo").textContent = fmt(d.tot_residuo);
        const tbody = document.getElementById("tbody_da");
        tbody.innerHTML = "";
        (d.persone||[]).forEach(p => {{
            const tr = document.createElement("tr");
            let cls = "saldo-zer";
            if (p.residuo > 0.01) cls = "saldo-no";
            else if (p.residuo < -0.01) cls = "saldo-ok";
            tr.innerHTML = `
                <td><b>PER· ${{p.nome}}</b></td>
                <td style="color:var(--gold)">${{fmt(p.dovuto)}}</td>
                <td style="color:var(--green)">${{fmt(p.versato)}}</td>
                <td class="${{cls}}">${{p.residuo < 0.01 ? '✅ Saldato' : '🔴 ' + fmt(p.residuo)}}</td>`;
            tbody.appendChild(tr);
        }});
        if (chartDA) chartDA.destroy();
        const ctx = document.getElementById("chartDA").getContext("2d");
        const labels  = (d.persone||[]).map(p => p.nome);
        const dovuti  = (d.persone||[]).map(p => p.dovuto);
        const versati = (d.persone||[]).map(p => p.versato);
        chartDA = new Chart(ctx, {{
            type: "bar",
            data: {{
                labels,
                datasets: [
                    {{ label:"Dovuto",  data:dovuti,  backgroundColor:"rgba(201,168,76,0.7)",  borderRadius:4 }},
                    {{ label:"Versato", data:versati, backgroundColor:"rgba(76,175,130,0.7)", borderRadius:4 }}
                ]
            }},
            options: {{
                responsive:true, maintainAspectRatio:false,
                plugins:{{ legend:{{ labels:{{ color:"#888", font:{{ size:10 }} }} }} }},
                scales:{{
                    x:{{ ticks:{{ color:"#888", font:{{ size:10 }} }}, grid:{{ color:"rgba(255,255,255,0.04)" }} }},
                    y:{{ ticks:{{ color:"#888", font:{{ size:10 }}, callback: v => fmt(v) }}, grid:{{ color:"rgba(255,255,255,0.04)" }} }}
                }}
            }}
        }});
        const chiList = document.getElementById("chi_deve_list");
        if (!d.chi_deve || d.chi_deve.length === 0) {{
            chiList.innerHTML = "<div style='padding:14px;color:var(--text-dim);font-size:0.85em'>Tutti in pari ✅</div>";
        }} else {{
            chiList.innerHTML = d.chi_deve.map(t => `
                <div class="chi-row">
                    <div>
                        <span style="color:var(--red);font-weight:700">${{t.da}}</span>
                        <span style="color:var(--text-dim);margin:0 8px">→</span>
                        <span style="color:var(--green);font-weight:700">${{t.a}}</span>
                    </div>
                    <div style="font-weight:700;color:var(--gold)">${{fmt(t.importo)}}</div>
                </div>`).join("");
        }}
    }}
    function renderPersonali(d) {{
        const container = document.getElementById("pers_container");
        container.innerHTML = "";
        Object.values(chartsPers).forEach(c => c.destroy());
        chartsPers = {{}};
        if (!d.personali || d.personali.length === 0) {{
            container.innerHTML = "<div style='text-align:center;padding:30px;color:var(--text-dim);font-size:0.85em'>Nessun conto personale configurato</div>";
            return;
        }}
        d.personali.forEach((p, idx) => {{
            const saldo    = p.tot_ent - p.tot_usc;
            const saldoCol = saldo >= 0 ? "var(--green)" : "var(--red)";
            const chartId  = `chartPers_${{idx}}`;
            const div      = document.createElement("div");
            div.className  = "pers-card";
            div.innerHTML  = `
                <div class="pers-name">CTP· ${{p.nome}}</div>
                <div class="pers-totali">
                    <div class="pers-tot"><small>Entrate</small><b style="color:var(--green)">${{fmt(p.tot_ent)}}</b></div>
                    <div class="pers-tot"><small>Uscite</small><b style="color:var(--red)">${{fmt(p.tot_usc)}}</b></div>
                    <div class="pers-tot"><small>Saldo</small><b style="color:${{saldoCol}}">${{fmt(saldo)}}</b></div>
                </div>
                <div class="pers-chart-wrap"><canvas id="${{chartId}}"></canvas></div>`;
            container.appendChild(div);
            if (p.categorie && p.categorie.length > 0) {{
                const top = p.categorie.slice(0,10);
                const ctx = document.getElementById(chartId).getContext("2d");
                chartsPers[chartId] = new Chart(ctx, {{
                    type:"bar",
                    data:{{
                        labels: top.map(c=>c.cat),
                        datasets:[
                            {{label:"Entrate",data:top.map(c=>c.ent),backgroundColor:"rgba(76,175,130,0.7)",borderRadius:3}},
                            {{label:"Uscite", data:top.map(c=>c.usc),backgroundColor:"rgba(224,90,90,0.7)", borderRadius:3}}
                        ]
                    }},
                    options:{{
                        responsive:true,maintainAspectRatio:false,
                        plugins:{{legend:{{labels:{{color:"#888",font:{{size:9}}}}}}}},
                        scales:{{
                            x:{{ticks:{{color:"#888",font:{{size:9}},maxRotation:30}},grid:{{color:"rgba(255,255,255,0.04)"}}}},
                            y:{{ticks:{{color:"#888",font:{{size:9}},callback:v=>fmt(v)}},grid:{{color:"rgba(255,255,255,0.04)"}}}}
                        }}
                    }}
                }});
            }} else {{
                document.getElementById(chartId).parentElement.innerHTML =
                    "<div style='text-align:center;padding:20px;color:var(--text-dim);font-size:0.8em'>Nessun movimento</div>";
            }}
        }});
    }}
    window.addEventListener('load', async function() {{
        try {{
            const r = await fetch("/get_fairshare_data?anno=0&mese=0&utente=tutti");
            const d = await r.json();
            const sel = document.getElementById("f_anno");
            (d.anni||[]).forEach(a => {{
                const o = document.createElement("option");
                o.value = a; o.textContent = a;
                if (a === ANNO_CORRENTE) o.selected = true;
                sel.appendChild(o);
            }});
            aggiornaFiltriUtenti(d);
        }} catch(e) {{}}
        carica();
    }});
</script>
</body>
</html>"""
        
