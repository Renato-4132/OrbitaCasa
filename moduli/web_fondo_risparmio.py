#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import html
import datetime


# Html Genera la pagina web del Fondo Risparmio (proiezione, obiettivi, emergenza, trend)
def pagina_fondo_risparmio_web(self):
    import __main__ as _app
    FR_FILE = _app.FR_FILE
    oggi = datetime.date.today()
    anno_corrente = oggi.year
    oggi_formattata = oggi.strftime('%d/%m/%Y')
    MESI_BREVI  = ["Gen","Feb","Mar","Apr","Mag","Giu",
                   "Lug","Ago","Set","Ott","Nov","Dic"]
    MESI_ESTESI = ["Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno",
                   "Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"]
    try:
        if os.path.exists(FR_FILE):
            with open(FR_FILE, "r", encoding="utf-8") as _f:
                fr_dati = json.load(_f)
        else:
            fr_dati = {"obiettivo_annuale": 0.0, "fondo_attuale": 0.0, "obiettivi": []}
    except Exception:
        fr_dati = {"obiettivo_annuale": 0.0, "fondo_attuale": 0.0, "obiettivi": []}
    obiettivo_annuale = fr_dati.get("obiettivo_annuale", 0.0)
    fondo_attuale     = fr_dati.get("fondo_attuale", 0.0)
    obiettivi         = fr_dati.get("obiettivi", [])
    def fmt(v):
        return f"€ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")
    def fmts(v):
        return f"{v:,.2f}".replace(",","X").replace(".",",").replace("X",".")
    inizio_365 = oggi - datetime.timedelta(days=364)
    entrate_tot = 0.0
    uscite_tot  = 0.0
    mesi_dati   = {}
    for d, sp in self.spese.items():
        if inizio_365 <= d <= oggi:
            for entry in sp:
                cat, desc, imp, tipo = entry[:4]
                key = (d.year, d.month)
                if key not in mesi_dati:
                    mesi_dati[key] = {"e": 0.0, "u": 0.0}
                if tipo == "Entrata":
                    entrate_tot        += imp
                    mesi_dati[key]["e"] += imp
                else:
                    uscite_tot         += imp
                    mesi_dati[key]["u"] += imp
    n_mesi  = len(mesi_dati) if mesi_dati else 1
    media_e = entrate_tot / n_mesi
    media_u = uscite_tot  / n_mesi
    media_r = (entrate_tot - uscite_tot) / n_mesi
    risparmio_365 = entrate_tot - uscite_tot
    anno_prec = anno_corrente - 1
    mesi_reali = {}
    for (y, m), v in mesi_dati.items():
        if y == anno_corrente:
            mesi_reali[m] = v
    mesi_anno_prec = {}
    for d, sp in self.spese.items():
        if d.year == anno_prec:
            key = d.month
            if key not in mesi_anno_prec:
                mesi_anno_prec[key] = {"e": 0.0, "u": 0.0}
            for entry in sp:
                imp, tipo = entry[2], entry[3]
                if tipo == "Entrata":
                    mesi_anno_prec[key]["e"] += imp
                else:
                    mesi_anno_prec[key]["u"] += imp
    proj = []
    e_proj = 0.0; u_proj = 0.0
    for m in range(1, 13):
        if m in mesi_reali:
            e, u, futuro = mesi_reali[m]["e"], mesi_reali[m]["u"], False
        else:
            if m in mesi_anno_prec:
                e = mesi_anno_prec[m]["e"]
                u = mesi_anno_prec[m]["u"]
            else:
                e, u = media_e, media_u
            futuro = True
        proj.append({"m": m, "e": e, "u": u, "r": e - u, "futuro": futuro})
        e_proj += e; u_proj += u
    r_proj = e_proj - u_proj
    dati_12 = []
    for i in range(11, -1, -1):
        total = oggi.year * 12 + oggi.month - 1 - i
        y = total // 12; m = total % 12 + 1
        e12 = 0.0; u12 = 0.0
        for d, sp in self.spese.items():
            if d.year == y and d.month == m:
                for entry in sp:
                    imp, tipo = entry[2], entry[3]
                    if tipo == "Entrata": e12 += imp
                    else: u12 += imp
        dati_12.append({"y": y, "m": m, "e": e12, "u": u12, "r": e12 - u12})
    best  = max(dati_12, key=lambda x: x["r"], default={"m":1,"y":oggi.year,"r":0})
    worst = min(dati_12, key=lambda x: x["r"], default={"m":1,"y":oggi.year,"r":0})
    spesa_mm = media_u
    fe3  = spesa_mm * 3
    fe6  = spesa_mm * 6
    fe12 = spesa_mm * 12
    pct3  = max(0.0, min(fondo_attuale / fe3,  1.0)) if fe3  > 0 else 0.0
    pct6  = max(0.0, min(fondo_attuale / fe6,  1.0)) if fe6  > 0 else 0.0
    pct12 = max(0.0, min(fondo_attuale / fe12, 1.0)) if fe12 > 0 else 0.0
    def bar_col(pct):
        if pct >= 1.0:  return "var(--green)"
        if pct >= 0.5:  return "var(--orange)"
        return "var(--red)"
    rata_mensile = obiettivo_annuale / 12 if obiettivo_annuale > 0 else 0.0
    diff_obj = media_r - rata_mensile
    pct_obj  = max(0.0, min(risparmio_365 / obiettivo_annuale, 1.0)) if obiettivo_annuale > 0 else 0.0
    proj_rows = ""
    for p in proj:
        futuro_cls = " futuro" if p["futuro"] else ""
        segno = "+" if p["r"] >= 0 else ""
        col_r = "var(--green)" if p["r"] >= 0 else "var(--red)"
        proj_rows += (
            f"<tr class='pr-row{futuro_cls}'>"
            f"<td>{MESI_BREVI[p['m']-1]}</td>"
            f"<td class='num'>{fmts(p['e'])}</td>"
            f"<td class='num'>{fmts(p['u'])}</td>"
            f"<td class='num' style='color:{col_r}'>{segno}{fmts(p['r'])}</td>"
            f"<td class='futuro-badge'>{'📊 stimato' if p['futuro'] else '✓ reale'}</td>"
            f"</tr>"
        )
    trend_rows = ""
    prev_r = None
    for row in dati_12:
        if prev_r is None:
            delta_s = "—"
        elif row["r"] >= prev_r:
            delta_s = f"▲ +{fmts(row['r'] - prev_r)}"
        else:
            delta_s = f"▼ {fmts(row['r'] - prev_r)}"
        col_r = "var(--green)" if row["r"] >= 0 else "var(--red)"
        trend_rows += (
            f"<tr>"
            f"<td>{MESI_ESTESI[row['m']-1]} {row['y']}</td>"
            f"<td class='num'>{fmts(row['e'])}</td>"
            f"<td class='num'>{fmts(row['u'])}</td>"
            f"<td class='num' style='color:{col_r}'>{fmts(row['r'])}</td>"
            f"<td class='num'>{delta_s}</td>"
            f"</tr>"
        )
        prev_r = row["r"]
    obj_rows = ""
    for i, ob in enumerate(obiettivi):
        rata  = ob["importo"] / ob["mesi"] if ob.get("mesi", 0) > 0 else ob["importo"]
        ok    = media_r >= rata
        mesi_r = int(ob["importo"] / media_r) if media_r > 0 else 9999
        col_ok = "var(--green)" if ok else "var(--red)"
        obj_rows += (
            f"<tr>"
            f"<td>{html.escape(ob['nome'])}</td>"
            f"<td class='num'>{fmts(ob['importo'])}</td>"
            f"<td>{ob.get('data','—')}</td>"
            f"<td class='num'>{ob.get('mesi','—')}</td>"
            f"<td class='num'>{fmts(rata)}</td>"
            f"<td style='color:{col_ok}'>{'Sì' if ok else 'No'}</td>"
            f"<td class='num'>{'N/D' if media_r <= 0 else f'{mesi_r} mesi'}</td>"
            f"<td><form method='post' action='/fondo_risparmio_web' style='margin:0'>"
            f"<input type='hidden' name='action' value='elimina_obiettivo'>"
            f"<input type='hidden' name='idx' value='{i}'>"
            f"<button class='btn-del' type='submit' title='Elimina'>✕</button>"
            f"</form></td>"
            f"</tr>"
        )
    if not obj_rows:
        obj_rows = "<tr><td colspan='8' style='text-align:center;color:var(--text-dim);padding:18px'>Nessun obiettivo impostato</td></tr>"
    valori_12 = [r["r"] for r in dati_12]
    max_v12   = max(abs(v) for v in valori_12) or 1.0
    sw, sh    = 560, 90
    pad_s     = 24
    step_s    = (sw - 2 * pad_s) / max(len(valori_12) - 1, 1)
    y_zero_s  = sh // 2
    spark_lines = ""
    spark_pts   = ""
    spark_lbls  = ""
    pts_s = []
    for i, v in enumerate(valori_12):
        x = pad_s + i * step_s
        y = y_zero_s - (v / max_v12) * (y_zero_s - 10)
        pts_s.append((x, y))
    for i in range(len(pts_s) - 1):
        col = "#4caf82" if valori_12[i] >= 0 else "#e05a5a"
        spark_lines += f"<line x1='{pts_s[i][0]:.1f}' y1='{pts_s[i][1]:.1f}' x2='{pts_s[i+1][0]:.1f}' y2='{pts_s[i+1][1]:.1f}' stroke='{col}' stroke-width='2'/>"
    for i, (x, y) in enumerate(pts_s):
        col = "#4caf82" if valori_12[i] >= 0 else "#e05a5a"
        spark_pts  += f"<circle cx='{x:.1f}' cy='{y:.1f}' r='4' fill='{col}'/>"
        spark_lbls += f"<text x='{x:.1f}' y='{sh - 4}' text-anchor='middle' font-size='9' fill='#888'>{MESI_BREVI[dati_12[i]['m']-1]}</text>"
    col_r_proj = "var(--green)" if r_proj >= 0 else "var(--red)"
    col_r_365  = "var(--green)" if risparmio_365 >= 0 else "var(--red)"
    col_media  = "var(--green)" if media_r >= 0 else "var(--red)"
    col_diff   = "var(--green)" if diff_obj >= 0 else "var(--red)"
    diff_testo = (f"Sei in linea (+{fmt(diff_obj)}/mese)" if diff_obj >= 0
                  else f"Mancano {fmt(abs(diff_obj))}/mese")
    nav_anno = anno_corrente
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>💰 Fondo Risparmio {oggi_formattata}</title>
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
        --green:#4caf82; --red:#e05a5a; --orange:#e09a3a;
        --text:#e8e8e8; --text-dim:#555; --text-mid:#888; --radius-lg:18px;
    }}
    :root.light {{
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --gold:#b8902a; --blue:#3d7fd4;
        --green:#3a9068; --red:#cc3333; --orange:#c07820;
        --text:#1a1a1a; --text-dim:#999; --text-mid:#555;
    }}
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{
        font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text);
        min-height:100vh; padding-bottom:60px; transition:background 0.3s,color 0.3s;
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
    .header-title {{ font-size:1em; font-weight:700; color:var(--text); }}
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
    main {{ padding:14px; max-width:860px; margin:0 auto; animation:fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .tabs {{ display:flex; gap:6px; margin-bottom:14px; flex-wrap:wrap; }}
    .tab-btn {{
        padding:8px 18px; border-radius:10px; border:1px solid var(--border);
        background:var(--surface3); color:var(--text-mid); cursor:pointer;
        font-family:'DM Sans',sans-serif; font-size:0.85em; font-weight:600;
        transition:all 0.18s;
    }}
    .tab-btn.active, .tab-btn:hover {{
        background:var(--gold); color:#000; border-color:var(--gold);
    }}
    .tab-panel {{ display:none; }}
    .tab-panel.active {{ display:block; }}
    .card {{
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); padding:18px 16px; margin-bottom:14px;
        position:relative; overflow:hidden;
    }}
    .card::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .card-title {{
        font-size:0.8em; font-weight:700; color:var(--text-mid);
        text-transform:uppercase; letter-spacing:0.05em; margin-bottom:12px;
    }}
    .kpi-grid {{ display:grid; grid-template-columns:repeat(3, 1fr); gap:10px; }}
    .kpi {{
        background:var(--surface2); border:1px solid var(--border);
        border-radius:12px; padding:12px 10px; text-align:center;
    }}
    .kpi-label {{ font-size:0.72em; color:var(--text-dim); margin-bottom:4px; }}
    .kpi-value {{ font-size:1.05em; font-weight:700; }}
    .tbl-wrap {{ overflow-x:auto; }}
    table {{ width:100%; border-collapse:collapse; font-size:0.83em; }}
    th {{
        padding:8px 10px; text-align:left; border-bottom:1px solid var(--border);
        color:var(--text-dim); font-weight:600; font-size:0.78em; text-transform:uppercase;
    }}
    td {{ padding:7px 10px; border-bottom:1px solid var(--border); color:var(--text-mid); }}
    tr:last-child td {{ border-bottom:none; }}
    tr:hover td {{ background:var(--surface2); color:var(--text); }}
    td.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
    tr.futuro td {{ opacity:0.6; }}
    .futuro-badge {{ font-size:0.75em; color:var(--text-dim); }}
    .prog-wrap {{ background:var(--surface3); border-radius:8px; height:14px; overflow:hidden; margin-bottom:4px; }}
    .prog-fill {{ height:100%; border-radius:8px; transition:width 0.6s ease; }}
    .prog-label {{ font-size:0.75em; color:var(--text-mid); margin-bottom:10px; }}
    .form-row {{ display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-top:10px; }}
    .form-row input[type=text], .form-row input[type=number] {{
        background:var(--surface3); border:1px solid var(--border); color:var(--text);
        padding:7px 10px; border-radius:8px; font-family:'DM Sans',sans-serif; font-size:0.85em;
        width:120px;
    }}
    .form-row input:focus {{ outline:none; border-color:var(--gold); }}
    .btn-save {{
        padding:7px 18px; border-radius:8px; border:none; cursor:pointer;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.85em;
        transition:all 0.2s;
    }}
    .btn-save:hover {{ transform:translateY(-1px); box-shadow:0 4px 14px rgba(201,168,76,0.3); }}
    .btn-del {{
        background:none; border:1px solid var(--red); color:var(--red);
        border-radius:6px; padding:3px 8px; cursor:pointer; font-size:0.8em; transition:all 0.15s;
    }}
    .btn-del:hover {{ background:var(--red); color:#fff; }}
    .hint {{ font-size:0.78em; color:var(--text-dim); margin-top:6px; }}
    .badge-best {{ color:var(--green); font-weight:700; }}
    .badge-worst {{ color:var(--red); font-weight:700; }}
    svg.spark {{ width:100%; height:90px; }}
</style>
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
    function showTab(id) {{
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.getElementById(id).classList.add('active');
        document.querySelector('[data-tab="' + id + '"]').classList.add('active');
        localStorage.setItem('fr_tab', id);
    }}
    document.addEventListener("DOMContentLoaded", function() {{
        applyTheme(localStorage.getItem('theme') || 'dark');
        const saved = localStorage.getItem('fr_tab') || 'tab-proiezione';
        showTab(saved);
    }});
    document.addEventListener("click", function(e) {{
        const menu = document.getElementById("extraMenu");
        const btn = document.querySelector(".menu-btn");
        if (menu && menu.style.display === "block" && !menu.contains(e.target) && e.target !== btn)
            menu.style.display = "none";
    }});
</script>
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
            <a href="/utenze?anno={nav_anno}">💧 Utenze</a>
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
<div class="header-title">💰 Fondo Risparmio {oggi_formattata}</div>
<button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
<div class="tabs">
    <button class="tab-btn" data-tab="tab-proiezione" onclick="showTab('tab-proiezione')">📊 Proiezione {anno_corrente}</button>
    <button class="tab-btn" data-tab="tab-mensile"   onclick="showTab('tab-mensile')">📅 Fondo Mensile</button>
    <button class="tab-btn" data-tab="tab-obiettivi" onclick="showTab('tab-obiettivi')">🎯 Obiettivi</button>
    <button class="tab-btn" data-tab="tab-trend"     onclick="showTab('tab-trend')">📈 Trend 12 Mesi</button>
    <button class="tab-btn" data-tab="tab-emergenza" onclick="showTab('tab-emergenza')">🛡 Fondo Emergenza</button>
</div>
<!-- TAB PROIEZIONE -->
<div id="tab-proiezione" class="tab-panel">
    <div class="card">
        <div class="card-title">Ultimi 365 giorni</div>
        <div class="kpi-grid">
            <div class="kpi"><div class="kpi-label">Entrate</div><div class="kpi-value">{fmt(entrate_tot)}</div></div>
            <div class="kpi"><div class="kpi-label">Uscite</div><div class="kpi-value">{fmt(uscite_tot)}</div></div>
            <div class="kpi"><div class="kpi-label">Risparmio</div><div class="kpi-value" style="color:{col_r_365}">{fmt(risparmio_365)}</div></div>
            <div class="kpi"><div class="kpi-label">Media Entrate/mese</div><div class="kpi-value">{fmt(media_e)}</div></div>
            <div class="kpi"><div class="kpi-label">Media Uscite/mese</div><div class="kpi-value">{fmt(media_u)}</div></div>
            <div class="kpi"><div class="kpi-label">Media Risparmio/mese</div><div class="kpi-value" style="color:{col_media}">{fmt(media_r)}</div></div>
        </div>
    </div>
    <div class="card">
        <div class="card-title">Proiezione {anno_corrente} — Entrate stimate {fmt(e_proj)} · Uscite stimate {fmt(u_proj)} · Risparmio atteso <span style="color:{col_r_proj}">{fmt(r_proj)}</span></div>
        <p class="hint">I mesi con sfondo attenuato (📊 stimato) usano dati dell'anno precedente o la media degli ultimi 365 giorni.</p>
        <div class="tbl-wrap" style="margin-top:12px">
            <table>
                <thead><tr><th>Mese</th><th>Entrate</th><th>Uscite</th><th>Risparmio</th><th>Fonte</th></tr></thead>
                <tbody>{proj_rows}</tbody>
            </table>
        </div>
    </div>
</div>
<!-- TAB FONDO MENSILE -->
<div id="tab-mensile" class="tab-panel">
    <div class="card">
        <div class="card-title">Medie mensili ({n_mesi} mesi analizzati)</div>
        <div class="kpi-grid">
            <div class="kpi"><div class="kpi-label">Media Entrate/mese</div><div class="kpi-value">{fmt(media_e)}</div></div>
            <div class="kpi"><div class="kpi-label">Media Uscite/mese</div><div class="kpi-value">{fmt(media_u)}</div></div>
            <div class="kpi"><div class="kpi-label">Risparmio Medio/mese</div><div class="kpi-value" style="color:{col_media}">{fmt(media_r)}</div></div>
        </div>
    </div>
    <div class="card">
        <div class="card-title">Obiettivo Risparmio Annuale</div>
        <form method="post" action="/fondo_risparmio_web">
            <input type="hidden" name="action" value="salva_obiettivo">
            <div class="form-row">
                <span style="font-size:0.85em">Obiettivo annuale (€):</span>
                <input type="number" name="obiettivo_annuale" value="{int(obiettivo_annuale)}" min="0" step="100">
                <button class="btn-save" type="submit">Salva</button>
            </div>
        </form>
        <div style="margin-top:14px">
            <div class="prog-wrap">
                <div class="prog-fill" style="width:{pct_obj*100:.1f}%;background:{bar_col(pct_obj)}"></div>
            </div>
            <div class="prog-label">Risparmio 365gg: {fmt(risparmio_365)} / Obiettivo: {fmt(obiettivo_annuale) if obiettivo_annuale > 0 else '—'} ({pct_obj*100:.1f}%)</div>
            <p style="font-size:0.83em;margin-top:6px">
                Rata mensile necessaria: <strong>{fmt(rata_mensile)}</strong> &nbsp;·&nbsp;
                <span style="color:{col_diff}">{diff_testo}</span>
            </p>
        </div>
    </div>
</div>
<!-- TAB OBIETTIVI -->
<div id="tab-obiettivi" class="tab-panel">
    <div class="card">
        <div class="card-title">➕ Nuovo Obiettivo</div>
        <form method="post" action="/fondo_risparmio_web">
            <input type="hidden" name="action" value="aggiungi_obiettivo">
            <div class="form-row">
                <input type="text"   name="nome"           placeholder="Nome"       style="width:160px">
                <input type="number" name="importo"        placeholder="Importo €"  min="0" step="0.01">
                <input type="text"   name="data_scadenza"  placeholder="MM/AAAA"    style="width:90px">
                <button class="btn-save" type="submit">Aggiungi</button>
            </div>
        </form>
        <p class="hint">Data nel formato MM/AAAA — deve essere futura</p>
    </div>
    <div class="card">
        <div class="card-title">I Tuoi Obiettivi</div>
        <p class="hint" style="margin-bottom:10px">Risparmio medio mensile attuale: <strong>{fmt(media_r)}</strong></p>
        <div class="tbl-wrap">
            <table>
                <thead><tr><th>Nome</th><th>Importo</th><th>Entro</th><th>Mesi</th><th>Rata/mese</th><th>Fattibile</th><th>Mesi realistici</th><th></th></tr></thead>
                <tbody>{obj_rows}</tbody>
            </table>
        </div>
    </div>
</div>
<!-- TAB TREND -->
<div id="tab-trend" class="tab-panel">
    <div class="card">
        <div class="card-title">Trend Risparmio — ultimi 12 mesi</div>
        <p>
            <span class="badge-best">Mese migliore: {MESI_ESTESI[best['m']-1]} {best['y']} (+{fmt(best['r'])})</span>
            &nbsp;·&nbsp;
            <span class="badge-worst">Mese peggiore: {MESI_ESTESI[worst['m']-1]} {worst['y']} ({fmt(worst['r'])})</span>
        </p>
        <svg class="spark" viewBox="0 0 {sw} {sh}" xmlns="http://www.w3.org/2000/svg" style="margin-top:10px">
            <line x1="{pad_s}" y1="{y_zero_s}" x2="{sw-pad_s}" y2="{y_zero_s}" stroke="#444" stroke-dasharray="4 2"/>
            {spark_lines}
            {spark_pts}
            {spark_lbls}
        </svg>
    </div>
    <div class="card">
        <div class="card-title">Andamento Mensile — ultimi 12 mesi</div>
        <div class="tbl-wrap">
            <table>
                <thead><tr><th>Mese</th><th>Entrate</th><th>Uscite</th><th>Saldo</th><th>Delta vs precedente</th></tr></thead>
                <tbody>{trend_rows}</tbody>
            </table>
        </div>
    </div>
</div>
<!-- TAB EMERGENZA -->
<div id="tab-emergenza" class="tab-panel">
    <div class="card">
        <div class="card-title">Calcolo Fondo Emergenza</div>
        <div class="kpi-grid">
            <div class="kpi"><div class="kpi-label">Spesa media/mese</div><div class="kpi-value">{fmt(spesa_mm)}</div></div>
            <div class="kpi"><div class="kpi-label">Consigliato 3 mesi</div><div class="kpi-value">{fmt(fe3)}</div></div>
            <div class="kpi"><div class="kpi-label">Consigliato 6 mesi</div><div class="kpi-value">{fmt(fe6)}</div></div>
            <div class="kpi"><div class="kpi-label">Consigliato 12 mesi</div><div class="kpi-value">{fmt(fe12)}</div></div>
        </div>
    </div>
    <div class="card">
        <div class="card-title">Il Tuo Fondo Attuale</div>
        <form method="post" action="/fondo_risparmio_web">
            <input type="hidden" name="action" value="salva_fondo">
            <div class="form-row">
                <span style="font-size:0.85em">Fondo emergenza attuale (€):</span>
                <input type="number" name="fondo_attuale" value="{int(fondo_attuale)}" min="0" step="100">
                <button class="btn-save" type="submit">Salva</button>
            </div>
        </form>
        <div style="margin-top:16px;display:flex;flex-direction:column;gap:10px">
            <div>
                <div class="prog-wrap">
                    <div class="prog-fill" style="width:{pct3*100:.1f}%;background:{bar_col(pct3)}"></div>
                </div>
                <div class="prog-label">Obiettivo 3 mesi: {fmt(fondo_attuale)} / {fmt(fe3)} ({pct3*100:.1f}%)</div>
            </div>
            <div>
                <div class="prog-wrap">
                    <div class="prog-fill" style="width:{pct6*100:.1f}%;background:{bar_col(pct6)}"></div>
                </div>
                <div class="prog-label">Obiettivo 6 mesi: {fmt(fondo_attuale)} / {fmt(fe6)} ({pct6*100:.1f}%)</div>
            </div>
            <div>
                <div class="prog-wrap">
                    <div class="prog-fill" style="width:{pct12*100:.1f}%;background:{bar_col(pct12)}"></div>
                </div>
                <div class="prog-label">Obiettivo 12 mesi: {fmt(fondo_attuale)} / {fmt(fe12)} ({pct12*100:.1f}%)</div>
            </div>
        </div>
        <p class="hint" style="margin-top:10px">Un fondo emergenza ideale copre almeno 3–6 mesi di spese. 12 mesi garantisce la massima sicurezza.</p>
    </div>
</div>
</main>
</body>
</html>"""
