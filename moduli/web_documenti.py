#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from moduli.web_utils import _fmt_it


# Html Gestione Documenti Contabili Web
def documenti_pdf_web(self):
    import datetime
    from datetime import datetime as dt
    import os
    import __main__ as _app
    DB_DIR = _app.DB_DIR
    DOC_DIR = _app.DOC_DIR
    REGISTRY_FILE = _app.REGISTRY_FILE
    oggi = datetime.date.today()
    def bytes_to_human(byte_count):
        if byte_count is None: return "0 B"
        byte_count = int(byte_count)
        if byte_count < 1024: return f"{byte_count} B"
        elif byte_count < 1024 ** 2: return f"{byte_count / 1024:.2f} KB"
        else: return f"{byte_count / (1024 ** 2):.2f} MB"
    registry_file_path = REGISTRY_FILE
    doc_dir = DOC_DIR
    dati_json = getattr(self, 'archivi_pdf', {})
    if not dati_json and os.path.exists(registry_file_path):
        try:
            with open(registry_file_path, "r", encoding="utf-8") as f:
                dati_json = json.load(f)
        except:
            dati_json = {}
    archivi_dati_strutturati = []
    categorie_set = set()
    for nome_file, dettagli in dati_json.items():
        percorso_fisico_check = os.path.join(doc_dir, nome_file)
        if not os.path.exists(percorso_fisico_check):
            continue
        try:
            data_raw = dettagli.get("data_raw")
            data_obj = dt.strptime(data_raw, "%d%m%Y").date() if data_raw else datetime.date.today()
        except:
            data_obj = datetime.date.today()
        cat = dettagli.get('categoria_esatta', 'Generico')
        categorie_set.add(cat)
        importo_raw = dettagli.get('importo_raw', 0)
        tipo_doc = dettagli.get('tipo_esatto', 'Uscita')
        segno_doc = "+" if tipo_doc == "Entrata" else "-"
        try:
            importo_val = float(importo_raw) / 100 if isinstance(importo_raw, (int, float)) else 0.0
        except:
            importo_val = 0.0
        archivi_dati_strutturati.append({
            "nome_file": nome_file,
            "data_caricamento": data_obj,
            "data_str": data_obj.strftime("%d/%m/%Y"),
            "data_iso": data_obj.isoformat(),
            "descrizione": dettagli.get('descrizione_esatta', 'N/D'),
            "categoria": cat,
            "importo_val": importo_val,
            "importo_str": f"€ {segno_doc}{_fmt_it(importo_val)}",
            "dimensione": bytes_to_human(os.path.getsize(percorso_fisico_check))
        })
    archivi_ordinati = sorted(archivi_dati_strutturati, key=lambda x: x["data_caricamento"], reverse=True)
    categorie_options = "".join(
        f"<option value='{c}'>{c}</option>"
        for c in sorted(categorie_set)
    )
    docs_js = json.dumps([{
        "nome": a["nome_file"],
        "data": a["data_str"],
        "data_iso": a["data_iso"],
        "desc": a["descrizione"],
        "cat": a["categoria"],
        "imp": a["importo_val"],
        "imp_str": a["importo_str"],
        "dim": a["dimensione"]
    } for a in archivi_ordinati])
    anno_corrente = oggi.year
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>🗄️ Documenti Contabili</title>
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
        --border:rgba(255,255,255,0.07); --border-active:rgba(99,160,240,0.5);
        --gold:#c9a84c; --blue:#63a0f0; --green:#4caf82; --red:#e05a5a;
        --text:#e8e8e8; --text-dim:#555; --text-mid:#888; --radius-lg:18px;
    }}
    :root.light {{
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --border-active:rgba(61,127,212,0.5);
        --gold:#b8902a; --blue:#3d7fd4; --green:#3a9068; --red:#cc3333;
        --text:#1a1a1a; --text-dim:#999; --text-mid:#555;
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
    main {{ padding:14px; max-width:680px; margin:0 auto; animation:fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .filter-card {{
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); padding:14px 16px 16px;
        margin-bottom:10px; position:relative; overflow:hidden; margin-top:14px;
    }}
    .filter-card::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .filter-row {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:8px; }}
    .filter-group label {{
        display:block; font-size:0.6em; font-weight:700; color:var(--text-dim);
        letter-spacing:1.5px; text-transform:uppercase; margin-bottom:5px;
    }}
    input[type="text"], input[type="number"], input[type="date"], select {{
        width:100%; padding:9px 12px;
        background:var(--surface2); border:1px solid var(--border);
        border-radius:8px; color:var(--text);
        font-family:'DM Sans',sans-serif; font-size:0.88em;
        outline:none; transition:all 0.2s;
        -webkit-appearance:none; appearance:none;
    }}
    input:focus, select:focus {{ border-color:var(--border-active); background:var(--surface3); }}
    input::placeholder {{ color:var(--text-dim); }}
    select {{
        background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='7' viewBox='0 0 12 7'%3E%3Cpath fill='none' stroke='%23555' stroke-width='1.5' d='M1 1l5 5 5-5'/%3E%3C/svg%3E");
        background-repeat:no-repeat; background-position:right 10px center;
        padding-right:28px; cursor:pointer;
    }}
    select option {{ background:var(--surface2); color:var(--text); }}
    .filter-actions {{ display:flex; gap:8px; margin-top:6px; }}
    .btn-filter {{
        flex:1; padding:10px; border:none; border-radius:8px;
        font-family:'DM Sans',sans-serif; font-size:0.88em; font-weight:700;
        line-height:1.5; cursor:pointer; transition:all 0.2s;
    }}
    .btn-filter.apply {{ background:linear-gradient(135deg, var(--gold), #8a6820); color:#000; }}
    .btn-filter.apply:hover {{ transform:translateY(-1px); box-shadow:0 4px 16px rgba(201,168,76,0.25); }}
    .btn-filter.reset {{ background:var(--surface2); border:1px solid var(--border); color:var(--text-mid); }}
    .btn-filter.reset:hover {{ border-color:var(--border-active); color:var(--text); }}
    .results-bar {{
        display:flex; justify-content:space-between; align-items:center;
        margin-bottom:8px; font-size:0.75em; color:var(--text-dim);
    }}
    .results-count {{ color:var(--blue); font-weight:700; font-size:1.1em; }}
    .doc-list {{
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); overflow:hidden;
        position:relative; margin-bottom:10px; min-height:60px;
    }}
    .doc-list::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .doc-item {{
        display:flex; align-items:center; justify-content:space-between;
        padding:11px 16px; border-bottom:1px solid var(--border); gap:10px; transition:background 0.15s;
    }}
    .doc-item:last-child {{ border-bottom:none; }}
    .doc-item:hover {{ background:var(--surface2); }}
    .doc-main {{ flex:1; overflow:hidden; }}
    .doc-date {{ font-size:0.65em; color:var(--text-dim); margin-bottom:2px; }}
    .doc-cat {{
        font-size:0.88em; font-weight:700; color:var(--blue);
        text-decoration:none; display:block; margin-bottom:2px; transition:color 0.15s;
    }}
    .doc-cat:hover {{ color:var(--gold); }}
    .doc-desc {{ font-size:0.77em; color:var(--text-mid); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; margin-bottom:3px; }}
    .doc-meta {{ display:flex; gap:10px; align-items:center; }}
    .doc-importo {{ font-size:0.75em; font-weight:700; color:var(--gold); }}
    .doc-dim {{ font-size:0.7em; color:var(--text-dim); }}
    .doc-dl {{ font-size:1.2em; text-decoration:none; opacity:0.5; transition:opacity 0.15s; flex-shrink:0; }}
    .doc-dl:hover {{ opacity:1; }}
    .empty-msg {{ text-align:center; padding:30px; color:var(--text-dim); font-size:0.85em; font-style:italic; }}
    .pagination {{ display:flex; justify-content:center; gap:6px; margin-bottom:10px; flex-wrap:wrap; }}
    .pg-btn {{
        padding:7px 13px; border:1px solid var(--border); border-radius:8px;
        background:var(--surface); color:var(--text-mid);
        font-family:'DM Sans',sans-serif; font-size:0.8em; font-weight:700;
        cursor:pointer; transition:all 0.15s; line-height:1.5;
    }}
    .pg-btn:hover {{ border-color:var(--border-active); color:var(--text); }}
    .pg-btn.active {{ background:var(--gold); color:#000; border-color:var(--gold); }}
    .pg-btn[disabled] {{ opacity:0.3; cursor:default; pointer-events:none; }}
    .pg-ellipsis {{ padding:7px 4px; color:var(--text-dim); font-size:0.8em; }}
    .btn-home {{
        display:block; text-align:center; padding:13px;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; border-radius:10px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.9em;
        line-height:1.5; transition:all 0.2s;
    }}
    .btn-home:hover {{ transform:translateY(-1px); box-shadow:0 6px 20px rgba(201,168,76,0.25); }}
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
    <div class="header-title">🗄️ Documenti Contabili</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="filter-card">
        <div class="filter-row">
            <div class="filter-group">
                <label>Descrizione</label>
                <input type="text" id="f_desc" placeholder="es: bolletta, fattura...">
            </div>
            <div class="filter-group">
                <label>Categoria</label>
                <select id="f_cat">
                    <option value="">-- Tutte --</option>
                    {categorie_options}
                </select>
            </div>
        </div>
        <div class="filter-row">
            <div class="filter-group">
                <label>Data da</label>
                <input type="date" id="f_data_da">
            </div>
            <div class="filter-group">
                <label>Data a</label>
                <input type="date" id="f_data_a">
            </div>
        </div>
        <div class="filter-row">
            <div class="filter-group">
                <label>Importo da (€)</label>
                <input type="number" id="f_imp_da" step="0.01" min="0" placeholder="es: 10.00">
            </div>
            <div class="filter-group">
                <label>Importo a (€)</label>
                <input type="number" id="f_imp_a" step="0.01" min="0" placeholder="es: 500.00">
            </div>
        </div>
        <div class="filter-actions">
            <button class="btn-filter apply" onclick="applicaFiltri()">🔍 Filtra</button>
            <button class="btn-filter reset" onclick="resetFiltri()">✕ Reset</button>
        </div>
    </div>
    <div class="results-bar">
        <span id="results_label">Tutti i documenti</span>
        <span class="results-count" id="results_count">0 risultati</span>
    </div>
    <div class="doc-list" id="docList"></div>
    <div class="pagination" id="pagination"></div>
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
    const DOCS = {docs_js};
    const PER_PAGE = 15;
    let filtered = [...DOCS];
    let currentPage = 1;
    function applicaFiltri() {{
        const desc  = document.getElementById('f_desc').value.toLowerCase().trim();
        const cat   = document.getElementById('f_cat').value;
        const daDt  = document.getElementById('f_data_da').value || null;
        const aDt   = document.getElementById('f_data_a').value  || null;
        const impDa = document.getElementById('f_imp_da').value !== '' ? parseFloat(document.getElementById('f_imp_da').value) : null;
        const impA  = document.getElementById('f_imp_a').value  !== '' ? parseFloat(document.getElementById('f_imp_a').value)  : null;
        filtered = DOCS.filter(d => {{
            if (desc && !d.desc.toLowerCase().includes(desc) && !d.cat.toLowerCase().includes(desc) && !d.data.includes(desc)) return false;
            if (cat  && d.cat !== cat) return false;
            if (daDt && d.data_iso < daDt) return false;
            if (aDt  && d.data_iso > aDt)  return false;
            if (impDa !== null && d.imp < impDa) return false;
            if (impA  !== null && d.imp > impA)  return false;
            return true;
        }});
        currentPage = 1;
        renderPage();
    }}
    function resetFiltri() {{
        ['f_desc','f_cat','f_data_da','f_data_a','f_imp_da','f_imp_a'].forEach(id => {{
            document.getElementById(id).value = '';
        }});
        filtered = [...DOCS];
        currentPage = 1;
        renderPage();
    }}
    function esc(s) {{
        return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }}
    function renderPage() {{
        const list  = document.getElementById('docList');
        const count = document.getElementById('results_count');
        const label = document.getElementById('results_label');
        const total = filtered.length;
        count.textContent = total + ' risultat' + (total === 1 ? 'o' : 'i');
        label.textContent = total === DOCS.length ? 'Tutti i documenti' : 'Risultati filtrati';
        list.innerHTML = '';
        const start = (currentPage - 1) * PER_PAGE;
        const page  = filtered.slice(start, start + PER_PAGE);
        if (page.length === 0) {{
            list.innerHTML = "<div class='empty-msg'>Nessun documento trovato con i filtri selezionati.</div>";
        }} else {{
            page.forEach(d => {{
                const link = '/get_pdf?file=' + encodeURIComponent(d.nome);
                const el = document.createElement('div');
                el.className = 'doc-item';
                el.innerHTML =
                    '<div class="doc-main">' +
                        '<div class="doc-date">' + esc(d.data) + '</div>' +
                        '<a href="' + link + '" target="_blank" class="doc-cat">' + esc(d.cat) + '</a>' +
                        '<div class="doc-desc">' + esc(d.desc) + '</div>' +
                        '<div class="doc-meta">' +
                            '<span class="doc-importo">' + esc(d.imp_str) + '</span>' +
                            '<span class="doc-dim">' + esc(d.dim) + '</span>' +
                        '</div>' +
                    '</div>' +
                    '<a href="' + link + '" download="' + esc(d.nome) + '" class="doc-dl" title="Scarica">⬇️</a>';
                list.appendChild(el);
            }});
        }}
        renderPagination(total);
    }}
    function renderPagination(total) {{
        const pg = document.getElementById('pagination');
        pg.innerHTML = '';
        const pages = Math.ceil(total / PER_PAGE);
        if (pages <= 1) return;
        const btn = (label, page, active, disabled) => {{
            const b = document.createElement('button');
            b.className = 'pg-btn' + (active ? ' active' : '');
            b.textContent = label;
            if (disabled) b.setAttribute('disabled', '');
            else b.onclick = () => {{ currentPage = page; renderPage(); window.scrollTo(0,0); }};
            pg.appendChild(b);
        }};
        const ellipsis = () => {{
            const s = document.createElement('span');
            s.className = 'pg-ellipsis'; s.textContent = '…'; pg.appendChild(s);
        }};
        btn('◀', currentPage-1, false, currentPage===1);
        for (let i=1; i<=pages; i++) {{
            if (pages > 7 && i>2 && i<pages-1 && Math.abs(i-currentPage)>1) {{
                if (i===3 || i===pages-2) ellipsis();
                continue;
            }}
            btn(i, i, i===currentPage, false);
        }}
        btn('▶', currentPage+1, false, currentPage===pages);
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
    document.addEventListener("click", function(e) {{
        const menu = document.getElementById("extraMenu");
        const btn  = document.querySelector(".menu-btn");
        if (menu && menu.style.display === "block" && !menu.contains(e.target) && e.target !== btn)
            menu.style.display = "none";
    }});
    renderPage();
</script>
</body>
</html>"""

# Html Documenti Personali Web 
def documenti_personali_web(self):
    import __main__ as _app
    DOC_PERS_DIR = _app.DOC_PERS_DIR
    import datetime
    from datetime import datetime as dt
    import os
    oggi = datetime.date.today()
    anno_corrente = oggi.year
    def bytes_to_human(n):
        n = int(n) if n else 0
        if n < 1024: return f"{n} B"
        elif n < 1024**2: return f"{n/1024:.1f} KB"
        else: return f"{n/1024**2:.1f} MB"
    PROFILI_FILE = os.path.join(DOC_PERS_DIR, "profili.json")
    profili = []
    if os.path.exists(PROFILI_FILE):
        try:
            with open(PROFILI_FILE, "r", encoding="utf-8") as f:
                profili = json.load(f)
        except Exception:
            profili = []
    profili = sorted(profili)
    tutti = []
    categorie_set = set()
    for nome_profilo in profili:
        reg_path = os.path.join(DOC_PERS_DIR, nome_profilo, "registry.json")
        docs_dir = os.path.join(DOC_PERS_DIR, nome_profilo, "documenti")
        dati = {}
        if os.path.exists(reg_path):
            try:
                with open(reg_path, "r", encoding="utf-8") as f:
                    dati = json.load(f)
            except Exception:
                dati = {}
        for fname, d in dati.items():
            fpath = os.path.join(docs_dir, fname)
            if not os.path.exists(fpath):
                continue
            try:
                data_obj = dt.strptime(d.get("data_raw", ""), "%d%m%Y").date()
            except Exception:
                data_obj = oggi
            cat = d.get("categoria", "Altro")
            categorie_set.add(cat)
            tutti.append({
                "nome_file":   fname,
                "data_obj":    data_obj,
                "data_str":    data_obj.strftime("%d/%m/%Y"),
                "data_iso":    data_obj.isoformat(),
                "descrizione": d.get("descrizione", ""),
                "note":        d.get("note", ""),
                "categoria":   cat,
                "dimensione":  bytes_to_human(os.path.getsize(fpath)),
                "profilo":     nome_profilo,
            })
    tutti.sort(key=lambda x: x["data_obj"], reverse=True)
    docs_js = json.dumps([{
        "nome":     a["nome_file"],
        "data":     a["data_str"],
        "data_iso": a["data_iso"],
        "desc":     a["descrizione"],
        "note":     a["note"],
        "cat":      a["categoria"],
        "dim":      a["dimensione"],
        "profilo":  a["profilo"],
    } for a in tutti])
    categorie_options = "".join(
        f"<option value='{c}'>{c}</option>"
        for c in sorted(categorie_set)
    )
    profili_options = "".join(
        f"<option value='{p}'>{p}</option>"
        for p in profili
    )
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>📄 Documenti Personali</title>
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
        --border:rgba(255,255,255,0.07); --border-active:rgba(99,160,240,0.5);
        --gold:#c9a84c; --blue:#63a0f0; --green:#4caf82; --red:#e05a5a;
        --text:#e8e8e8; --text-dim:#555; --text-mid:#888; --radius-lg:18px;
    }}
    :root.light {{
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --border-active:rgba(61,127,212,0.5);
        --gold:#b8902a; --blue:#3d7fd4; --green:#3a9068; --red:#cc3333;
        --text:#1a1a1a; --text-dim:#999; --text-mid:#555;
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
    main {{ padding:14px; max-width:680px; margin:0 auto; animation:fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .filter-card {{
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); padding:14px 16px 16px;
        margin-bottom:10px; position:relative; overflow:hidden; margin-top:14px;
    }}
    .filter-card::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .filter-row {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:8px; }}
    .filter-row-3 {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-bottom:8px; }}
    @media (max-width:520px) {{
        .filter-row, .filter-row-3 {{ grid-template-columns:1fr; }}
    }}
    .filter-group label {{
        display:block; font-size:0.6em; font-weight:700; color:var(--text-dim);
        letter-spacing:1.5px; text-transform:uppercase; margin-bottom:5px;
    }}
    input[type="text"], input[type="date"], select {{
        width:100%; padding:9px 12px;
        background:var(--surface2); border:1px solid var(--border);
        border-radius:8px; color:var(--text);
        font-family:'DM Sans',sans-serif; font-size:0.88em;
        outline:none; transition:all 0.2s;
        -webkit-appearance:none; appearance:none;
    }}
    input:focus, select:focus {{ border-color:var(--border-active); background:var(--surface3); }}
    input::placeholder {{ color:var(--text-dim); }}
    select {{
        background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='7' viewBox='0 0 12 7'%3E%3Cpath fill='none' stroke='%23555' stroke-width='1.5' d='M1 1l5 5 5-5'/%3E%3C/svg%3E");
        background-repeat:no-repeat; background-position:right 10px center;
        padding-right:28px; cursor:pointer;
    }}
    select option {{ background:var(--surface2); color:var(--text); }}
    .filter-actions {{ display:flex; gap:8px; margin-top:6px; }}
    .btn-filter {{
        flex:1; padding:10px; border:none; border-radius:8px;
        font-family:'DM Sans',sans-serif; font-size:0.88em; font-weight:700;
        line-height:1.5; cursor:pointer; transition:all 0.2s;
    }}
    .btn-filter.apply {{ background:linear-gradient(135deg, var(--gold), #8a6820); color:#000; }}
    .btn-filter.apply:hover {{ transform:translateY(-1px); box-shadow:0 4px 16px rgba(201,168,76,0.25); }}
    .btn-filter.reset {{ background:var(--surface2); border:1px solid var(--border); color:var(--text-mid); }}
    .btn-filter.reset:hover {{ border-color:var(--border-active); color:var(--text); }}
    .results-bar {{
        display:flex; justify-content:space-between; align-items:center;
        margin-bottom:8px; font-size:0.75em; color:var(--text-dim);
    }}
    .results-count {{ color:var(--blue); font-weight:700; font-size:1.1em; }}
    .doc-list {{
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); overflow:hidden;
        position:relative; margin-bottom:10px; min-height:60px;
    }}
    .doc-list::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .doc-item {{
        display:flex; align-items:flex-start; justify-content:space-between;
        padding:14px 16px; border-bottom:1px solid var(--border); gap:12px; transition:background 0.15s;
    }}
    .doc-item:last-child {{ border-bottom:none; }}
    .doc-item:hover {{ background:var(--surface2); }}
    .doc-main {{ flex:1; min-width:0; }}
    .doc-header {{
        display:flex; align-items:center; gap:10px; margin-bottom:6px;
        flex-wrap:wrap; row-gap:4px;
    }}
    .doc-date {{ font-size:0.82em; color:var(--text-mid); white-space:nowrap; }}
    .doc-profilo {{
        font-size:0.75em; font-weight:700; color:var(--gold);
        text-transform:uppercase; letter-spacing:0.8px; white-space:nowrap;
    }}
    .doc-dim {{ font-size:0.75em; color:var(--text-dim); white-space:nowrap; }}
    .doc-cat {{
        font-size:1em; font-weight:700; color:var(--blue);
        text-decoration:none; display:block; margin-bottom:6px; transition:color 0.15s;
    }}
    .doc-cat:hover {{ color:var(--gold); }}
    .doc-desc {{ font-size:0.88em; color:var(--text-mid); margin-bottom:4px; word-break:break-word; line-height:1.4; }}
    .doc-note {{ font-size:0.82em; color:var(--text-dim); font-style:italic; word-break:break-word; line-height:1.4; margin-bottom:2px; }}
    .doc-dl {{ font-size:1.5em; text-decoration:none; opacity:0.6; transition:opacity 0.15s; flex-shrink:0; padding-top:2px; }}
    .doc-dl:hover {{ opacity:1; }}
    .doc-dl {{ font-size:1.2em; text-decoration:none; opacity:0.5; transition:opacity 0.15s; flex-shrink:0; }}
    .doc-dl:hover {{ opacity:1; }}
    .empty-msg {{ text-align:center; padding:30px; color:var(--text-dim); font-size:0.85em; font-style:italic; }}
    .pagination {{ display:flex; justify-content:center; gap:6px; margin-bottom:10px; flex-wrap:wrap; }}
    .pg-btn {{
        padding:7px 13px; border:1px solid var(--border); border-radius:8px;
        background:var(--surface); color:var(--text-mid);
        font-family:'DM Sans',sans-serif; font-size:0.8em; font-weight:700;
        cursor:pointer; transition:all 0.15s; line-height:1.5;
    }}
    .pg-btn:hover {{ border-color:var(--border-active); color:var(--text); }}
    .pg-btn.active {{ background:var(--gold); color:#000; border-color:var(--gold); }}
    .pg-btn[disabled] {{ opacity:0.3; cursor:default; pointer-events:none; }}
    .pg-ellipsis {{ padding:7px 4px; color:var(--text-dim); font-size:0.8em; }}
    .btn-home {{
        display:block; text-align:center; padding:13px;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; border-radius:10px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.9em;
        line-height:1.5; transition:all 0.2s;
    }}
    .btn-home:hover {{ transform:translateY(-1px); box-shadow:0 6px 20px rgba(201,168,76,0.25); }}
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
                <a href="/consultazione_supermercati">🛒 Gestione Supermercati</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Documenti</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/documenti_pdf_web">🗄️ Documenti Contabili</a>
                <a href="/documenti_personali_web">📄 Documenti Personali</a>
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
    <div class="header-title">📄 Documenti Personali</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="filter-card">
        <div class="filter-row">
            <div class="filter-group">
                <label>Descrizione / Note</label>
                <input type="text" id="f_desc" placeholder="cerca...">
            </div>
            <div class="filter-group">
                <label>Profilo</label>
                <select id="f_profilo">
                    <option value="">-- Tutti --</option>
                    {profili_options}
                </select>
            </div>
        </div>
        <div class="filter-row-3">
            <div class="filter-group">
                <label>Categoria</label>
                <select id="f_cat">
                    <option value="">-- Tutte --</option>
                    {categorie_options}
                </select>
            </div>
            <div class="filter-group">
                <label>Data da</label>
                <input type="date" id="f_data_da">
            </div>
            <div class="filter-group">
                <label>Data a</label>
                <input type="date" id="f_data_a">
            </div>
        </div>
        <div class="filter-actions">
            <button class="btn-filter apply" onclick="applicaFiltri()">🔍 Filtra</button>
            <button class="btn-filter reset"  onclick="resetFiltri()">✕ Reset</button>
        </div>
    </div>
    <div class="results-bar">
        <span id="results_label">Tutti i documenti</span>
        <span class="results-count" id="results_count">0 risultati</span>
    </div>
    <div class="doc-list" id="docList"></div>
    <div class="pagination" id="pagination"></div>
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
    document.addEventListener("DOMContentLoaded", function() {{
        applyTheme(localStorage.getItem('theme') || 'dark');
    }});
    const DOCS = {docs_js};
    const PER_PAGE = 15;
    let filtered = [...DOCS];
    let currentPage = 1;
    function applicaFiltri() {{
        const desc    = document.getElementById('f_desc').value.toLowerCase().trim();
        const cat     = document.getElementById('f_cat').value;
        const profilo = document.getElementById('f_profilo').value;
        const daDt    = document.getElementById('f_data_da').value || null;
        const aDt     = document.getElementById('f_data_a').value  || null;
        filtered = DOCS.filter(d => {{
            if (desc    && !d.desc.toLowerCase().includes(desc) &&
                           !d.note.toLowerCase().includes(desc) &&
                           !d.cat.toLowerCase().includes(desc))  return false;
            if (cat     && d.cat     !== cat)     return false;
            if (profilo && d.profilo !== profilo) return false;
            if (daDt    && d.data_iso < daDt)     return false;
            if (aDt     && d.data_iso > aDt)      return false;
            return true;
        }});
        currentPage = 1;
        renderPage();
    }}
    function resetFiltri() {{
        ['f_desc','f_cat','f_profilo','f_data_da','f_data_a'].forEach(id => {{
            document.getElementById(id).value = '';
        }});
        filtered = [...DOCS];
        currentPage = 1;
        renderPage();
    }}
    function esc(s) {{
        return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }}
    function renderPage() {{
        const list  = document.getElementById('docList');
        const count = document.getElementById('results_count');
        const label = document.getElementById('results_label');
        const total = filtered.length;
        count.textContent = total + ' risultat' + (total === 1 ? 'o' : 'i');
        label.textContent = total === DOCS.length ? 'Tutti i documenti' : 'Risultati filtrati';
        list.innerHTML = '';
        const start = (currentPage - 1) * PER_PAGE;
        const page  = filtered.slice(start, start + PER_PAGE);
        if (page.length === 0) {{
            list.innerHTML = "<div class='empty-msg'>Nessun documento trovato.</div>";
        }} else {{
            page.forEach(d => {{
                const link = '/get_pdf_pers?profilo=' + encodeURIComponent(d.profilo) + '&file=' + encodeURIComponent(d.nome);
                const el = document.createElement('div');
                el.className = 'doc-item';
                el.innerHTML =
                    '<div class="doc-main">' +
                        '<div class="doc-header">' +
                            '<span class="doc-date">📅 ' + esc(d.data) + '</span>' +
                            '<span class="doc-profilo">👤 ' + esc(d.profilo) + '</span>' +
                            '<span class="doc-dim">' + esc(d.dim) + '</span>' +
                        '</div>' +
                        '<a href="' + link + '" target="_blank" class="doc-cat">' + esc(d.cat) + '</a>' +
                        (d.desc ? '<div class="doc-desc">' + esc(d.desc) + '</div>' : '') +
                        (d.note ? '<div class="doc-note">📝 ' + esc(d.note) + '</div>' : '') +
                    '</div>' +
                    '<a href="' + link + '" download="' + esc(d.nome) + '" class="doc-dl" title="Scarica">⬇️</a>';
                list.appendChild(el);
            }});
        }}
        renderPagination(total);
    }}
    function renderPagination(total) {{
        const pg = document.getElementById('pagination');
        pg.innerHTML = '';
        const pages = Math.ceil(total / PER_PAGE);
        if (pages <= 1) return;
        const btn = (label, page, active, disabled) => {{
            const b = document.createElement('button');
            b.className = 'pg-btn' + (active ? ' active' : '');
            b.textContent = label;
            if (disabled) b.setAttribute('disabled', '');
            else b.onclick = () => {{ currentPage = page; renderPage(); window.scrollTo(0,0); }};
            pg.appendChild(b);
        }};
        const ellipsis = () => {{
            const s = document.createElement('span');
            s.className = 'pg-ellipsis'; s.textContent = '…'; pg.appendChild(s);
        }};
        btn('◀', currentPage-1, false, currentPage===1);
        for (let i=1; i<=pages; i++) {{
            if (pages > 7 && i>2 && i<pages-1 && Math.abs(i-currentPage)>1) {{
                if (i===3 || i===pages-2) ellipsis();
                continue;
            }}
            btn(i, i, i===currentPage, false);
        }}
        btn('▶', currentPage+1, false, currentPage===pages);
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
    document.addEventListener("click", function(e) {{
        const menu = document.getElementById("extraMenu");
        const btn  = document.querySelector(".menu-btn");
        if (menu && menu.style.display === "block" && !menu.contains(e.target) && e.target !== btn)
            menu.style.display = "none";
    }});
    renderPage();
</script>
</body>
</html>"""

# Html Visualizza Utenze Web
def genera_html_utenze(self, percorso_db, anno):
    import __main__ as _app
    UTENZE_DB = _app.UTENZE_DB
    from datetime import datetime
    utenze = ["Acqua", "Luce", "Gas"]
    if not os.path.exists(percorso_db):
        return """<!DOCTYPE html>
<html><head><title>Errore DB</title><meta charset="utf-8">
<style>body{{font-family:'DM Sans',sans-serif;background:#050505;color:#e8e8e8;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px;}}.box{{background:#0f0f0f;border:1px solid rgba(255,255,255,0.07);border-radius:18px;padding:30px;max-width:400px;text-align:center;}}.t{{color:#e05a5a;font-size:1.2em;font-weight:800;margin-bottom:10px;}}.s{{color:#555;font-size:0.9em;margin-bottom:20px;}}.btn{{display:inline-block;padding:12px 24px;background:linear-gradient(135deg,#c9a84c,#8a6820);color:#000;border-radius:10px;text-decoration:none;font-weight:700;}}</style>
</head><body><div class="box"><div class="t">❌ Errore Database</div><div class="s">Il file UTENZE_DB non esiste o è vuoto.</div><a href="/" class="btn">🏠 Torna alla Home</a></div></body></html>"""
    try:
        with open(percorso_db, "r", encoding="utf-8") as f:
            contenuto = f.read().strip()
            if not contenuto:
                return "<p style='color:#e05a5a;padding:20px;'>⚠️ Il file database è vuoto.</p>"
            data = json.loads(contenuto)
    except Exception as e:
        return f"<p style='color:#e05a5a;padding:20px;'>❌ Errore nel file JSON: {e}</p>"
    letture = data.get("letture_salvate", {})
    anno_corrente = datetime.now().year
    anni_disponibili = [str(anno_corrente - i) for i in range(6)]
    select_html = "<div class='anno-select'><label>🗓️ Anno</label><select onchange=\"location.href='/utenze?anno=' + this.value\">"
    for a in anni_disponibili:
        selected = " selected" if a == str(anno) else ""
        select_html += f"<option value='{a}'{selected}>{a}</option>"
    select_html += "</select></div>"
    MESI_NOMI = ["Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno",
                  "Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"]
    utenze_html = ""
    for utenza in utenze:
        righe_db = letture.get(utenza, {}).get(str(anno), [])
        mese_map = {}
        for r in righe_db:
            try:
                mese_num = int(r[0].split("/")[0])
                mese_map[mese_num] = [float(r[1]), float(r[2]), float(r[3])]
            except Exception:
                pass
        uid = f"utenza_{utenza.lower()}"
        icone = {"Acqua": "💧", "Luce": "⚡", "Gas": "🔥"}
        ico = icone.get(utenza, "📊")
        rows_html = ""
        total = 0.0
        consumi = []
        for i, mese in enumerate(MESI_NOMI):
            vals = mese_map.get(i + 1, [0.0, 0.0, 0.0])
            prec, att, cons = vals[0], vals[1], vals[2]
            total += cons
            consumi.append(cons)
            _onchg = "calcCons(this.closest('tr'))"
            rows_html += (
                "<tr>"
                f"<td class='td-mese'>{mese}</td>"
                f"<td><input class='u-inp' type='number' step='0.1' min='0' name='prec_{i}' value='{prec:.1f}' onchange='{_onchg}'></td>"
                f"<td><input class='u-inp' type='number' step='0.1' min='0' name='att_{i}' value='{att:.1f}' onchange='{_onchg}'></td>"
                f"<td class='cons' id='cons_{utenza.lower()}_{i}'>{cons:.1f}</td>"
                "</tr>"
            )
        teardown_html = ""
        if any(c > 0 for c in consumi):
            media = total / len([c for c in consumi if c > 0]) if consumi else 0
            variazioni = [consumi[i] - consumi[i-1] for i in range(1, len(consumi)) if consumi[i-1] > 0 or consumi[i] > 0]
            ultima = variazioni[-1] if variazioni else 0
            ultima_color = "var(--green)" if ultima <= 0 else "var(--red)"
            teardown_html = f"""
            <div class='teardown'>
                <div class='td-item'><span>Totale</span><b>{total:.1f}</b></div>
                <div class='td-item'><span>Media mensile</span><b>{media:.1f}</b></div>
                <div class='td-item'><span>Ultima variazione</span><b style='color:{ultima_color}'>{ultima:+.1f}</b></div>
                <div class='td-item'><span>Mesi con dati</span><b>{len([c for c in consumi if c > 0])}</b></div>
            </div>"""
        utenze_html += f"""
        <div class='u-block'>
            <button class='u-toggle' onclick="toggleU('{uid}', this)" type='button'>
                <span>{ico} {utenza}</span>
                <span class='u-arrow'>▶</span>
            </button>
            <div class='u-content' id='{uid}' style='display:none;'>
                <form method='post' action='/salva_utenza_web'>
                    <input type='hidden' name='utenza' value='{utenza}'>
                    <input type='hidden' name='anno' value='{anno}'>
                    <table>
                        <thead><tr><th>Mese</th><th>Prec.</th><th>Att.</th><th>Consumo</th></tr></thead>
                        <tbody>{rows_html}</tbody>
                    </table>
                    {teardown_html}
                    <div class='form-save-row'>
                        <button type='submit' class='btn-salva-utenza'>💾 Salva {utenza}</button>
                    </div>
                </form>
            </div>
        </div>"""
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>💧 Utenze — {anno}</title>
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
    main {{ padding:14px; max-width:580px; margin:0 auto; animation:fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .anno-select {{
        background:var(--surface); border:1px solid var(--border); border-radius:12px;
        padding:10px 14px; margin-bottom:12px; display:flex; align-items:center; gap:10px;
    }}
    .anno-select label {{ font-size:0.78em; color:var(--text-mid); }}
    .anno-select select {{
        background:var(--surface2); border:1px solid var(--border); border-radius:8px;
        color:var(--text); padding:6px 10px; font-family:'DM Sans',sans-serif;
        font-size:0.88em; outline:none; cursor:pointer;
    }}
    .u-block {{
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); margin-bottom:8px; overflow:hidden; position:relative;
    }}
    .u-block::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .u-toggle {{
        width:100%; background:none; border:none; padding:14px 18px;
        display:flex; justify-content:space-between; align-items:center;
        cursor:pointer; color:var(--text); font-family:'DM Sans',sans-serif;
        font-size:0.95em; font-weight:700; line-height:1.5; transition:background 0.15s;
    }}
    .u-toggle:hover {{ background:var(--surface2); }}
    .u-arrow {{ font-size:0.75em; color:var(--text-dim); transition:transform 0.2s; }}
    .u-content {{ border-top:1px solid var(--border); }}
    table {{ width:100%; border-collapse:collapse; }}
    thead tr {{ background:var(--surface2); }}
    th {{ padding:9px 12px; font-size:0.7em; font-weight:700; color:var(--text-dim); letter-spacing:1.5px; text-transform:uppercase; text-align:left; border-bottom:1px solid var(--border); }}
    td {{ padding:9px 12px; font-size:0.88em; border-bottom:1px solid var(--border); color:var(--text-mid); }}
    td.cons {{ font-weight:600; color:var(--text); }}
    tr:last-child td {{ border-bottom:none; }}
    .empty-row {{ text-align:center; color:var(--text-dim); font-style:italic; }}
    .teardown {{ display:grid; grid-template-columns:1fr 1fr; gap:6px; padding:12px; background:var(--surface2); border-top:1px solid var(--border); }}
    .td-item {{ background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:8px 10px; }}
    .td-item span {{ display:block; font-size:0.62em; color:var(--text-dim); letter-spacing:1.2px; text-transform:uppercase; margin-bottom:3px; }}
    .td-item b {{ font-size:0.9em; font-weight:700; color:var(--text); }}
    .btn-home {{
        display:block; text-align:center; padding:13px;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; border-radius:10px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.9em;
        line-height:1.5; margin-top:14px; transition:all 0.2s;
    }}
    .btn-home:hover {{ transform:translateY(-1px); box-shadow:0 6px 20px rgba(201,168,76,0.25); }}
    .u-inp {{
        background:var(--surface3); border:1px solid var(--border); color:var(--text);
        padding:5px 7px; border-radius:7px; font-family:'DM Sans',sans-serif;
        font-size:0.85em; width:90px; text-align:right;
    }}
    .u-inp:focus {{ outline:none; border-color:var(--gold); }}
    .u-inp::-webkit-outer-spin-button,
    .u-inp::-webkit-inner-spin-button {{ -webkit-appearance:none; margin:0; }}
    .u-inp[type=number] {{ -moz-appearance:textfield; }}
    .td-mese {{ font-weight:600; color:var(--text); min-width:80px; }}
    .form-save-row {{ padding:10px 12px; background:var(--surface2); border-top:1px solid var(--border); }}
    .btn-salva-utenza {{
        padding:9px 22px; border-radius:9px; border:none; cursor:pointer;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.88em;
        transition:all 0.2s;
    }}
    .btn-salva-utenza:hover {{ transform:translateY(-1px); box-shadow:0 4px 14px rgba(201,168,76,0.3); }}
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
    <div class="header-title">💧 Utenze — {anno}</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    {select_html}
    {utenze_html}
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
    function toggleMenu() {{
        const m = document.getElementById("extraMenu");
        m.style.display = m.style.display === "block" ? "none" : "block";
    }}
    function toggleU(id, btn) {{
        const el = document.getElementById(id);
        const arrow = btn.querySelector(".u-arrow");
        const open = el.style.display === "block";
        el.style.display = open ? "none" : "block";
        arrow.textContent = open ? "▶" : "▼";
    }}
    function calcCons(row) {{
        const inputs = row.querySelectorAll("input[type='number']");
        if (inputs.length < 2) return;
        const prec = parseFloat(inputs[0].value) || 0;
        const att  = parseFloat(inputs[1].value) || 0;
        const cons = Math.max(0, att - prec).toFixed(1);
        const td = row.querySelector("td.cons");
        if (td) td.textContent = cons;
    }}
    document.addEventListener("click", function(e) {{
        const menu = document.getElementById("extraMenu");
        const btn = document.querySelector(".menu-btn");
        if (menu && menu.style.display === "block" && !menu.contains(e.target) && e.target !== btn)
            menu.style.display = "none";
    }});
</script>
</body>
</html>"""

# Lista Spesa Supermarket e Prezzi Promo
def genera_html_consultazione(self, file_selezionato=None):
    import __main__ as _app
    EXPORT_FILES = _app.EXPORT_FILES
    SUPERMERCATI_DB = _app.SUPERMERCATI_DB
    import datetime
    anno_corrente = datetime.datetime.now().year
    def inizializza_db_file(percorso_db, contenuto_iniziale="{}"):
        dir_path = os.path.dirname(percorso_db)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        if not os.path.exists(percorso_db):
            try:
                with open(percorso_db, "w", encoding="utf-8") as f:
                    f.write(contenuto_iniziale)
                return True
            except Exception as e:
                print(f"Errore nella creazione automatica di {percorso_db}: {e}")
                return False
        return True
    def get_file_list_internal():
        directory_esportazione = EXPORT_FILES
        if not os.path.isdir(directory_esportazione):
            try: os.makedirs(directory_esportazione)
            except: pass
            return []
        list_files = os.listdir(directory_esportazione)
        lista_spesa_files = [f for f in list_files if f.startswith("Lista_Spesa_") and f.endswith(".txt")]
        try:
            lista_spesa_files.sort(key=lambda f: os.path.getmtime(os.path.join(directory_esportazione, f)), reverse=True)
        except: pass
        return lista_spesa_files
    def leggi_lista_spesa_internal(nome_file):
        file_path = os.path.join(EXPORT_FILES, nome_file)
        if not os.path.exists(file_path): return []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Errore lettura file {nome_file}: {e}")
            return []
        return [{"raw_content": content}]
    lista_file_disponibili = get_file_list_internal()
    file_visualizzato = lista_file_disponibili[0] if lista_file_disponibili else "Nessuna Lista Trovata"
    ultima_spesa_data = []
    if file_visualizzato != "Nessuna Lista Trovata":
        ultima_spesa_data = leggi_lista_spesa_internal(file_visualizzato)
    is_raw_content = ultima_spesa_data and 'raw_content' in ultima_spesa_data[0]
    percorso_db = SUPERMERCATI_DB
    dati_supermercati = {}
    if not inizializza_db_file(percorso_db):
        return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Errore</title><style>body{{font-family:'DM Sans',sans-serif;background:#050505;color:#e8e8e8;padding:30px;}}.e{{color:#e05a5a;}}</style></head><body><p class="e">❌ Impossibile creare il file {percorso_db}.</p><a href="/" style="color:#c9a84c;">🏠 Home</a></body></html>"""
    try:
        with open(percorso_db, "r", encoding="utf-8") as f:
            contenuto = f.read().strip()
            dati_supermercati = json.loads(contenuto) if contenuto else {}
    except Exception as e:
        return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Errore JSON</title><style>body{{font-family:'DM Sans',sans-serif;background:#050505;color:#e8e8e8;padding:30px;}}</style></head><body><p style="color:#e05a5a;">❌ Errore lettura database: {e}</p><a href="/" style="color:#c9a84c;">🏠 Home</a></body></html>"""
    supermercati = sorted(dati_supermercati.keys())
    if is_raw_content:
        raw_text = ultima_spesa_data[0]['raw_content']
        raw_safe = raw_text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        lista_inner = f"<pre class='lista-pre'>{raw_safe}</pre>"
    else:
        lista_inner = "<p class='empty-msg'>❌ Nessun file lista spesa trovato nella cartella export.</p>"
    cataloghi_html = ""
    if supermercati:
        for superm in supermercati:
            articoli = dati_supermercati.get(superm, [])
            sid = f"cat_{superm.lower().replace(' ','_')}"
            rows = ""
            if articoli:
                for art in sorted(articoli, key=lambda x: x.get('nome','')):
                    nome = art.get("nome","N/D")
                    desc = art.get("descrizione","N/D")
                    cat  = art.get("categoria","Varie")
                    try: pn = f"{_fmt_it(float(art.get('prezzo','0')))}"
                    except: pn = art.get("prezzo","N/D")
                    promo_attiva = art.get("promo", False)
                    try: pp = float(art.get("prezzo_promo","0"))
                    except: pp = 0
                    promo_cell = f"<span class='promo'>€ {_fmt_it(pp)}</span>" if promo_attiva and pp > 0 else "—"
                    rows += f"<tr><td>{nome}</td><td class='td-desc'>{desc}</td><td>{cat}</td><td class='td-price'>€ {pn}</td><td class='td-price'>{promo_cell}</td></tr>"
                table = f"<table><thead><tr><th>Articolo</th><th>Descrizione</th><th>Categoria</th><th>Prezzo</th><th>Promo</th></tr></thead><tbody>{rows}</tbody></table>"
            else:
                table = "<p class='empty-msg'>Nessun articolo registrato.</p>"
            cataloghi_html += f"""
            <div class='u-block' style='margin-bottom:6px;'>
                <button class='u-toggle' onclick="toggleU('{sid}', this)">
                    <span>🛒 {superm} <small>({len(articoli)} articoli)</small></span>
                    <span class='u-arrow'>▶</span>
                </button>
                <div class='u-content' id='{sid}' style='display:none;overflow-x:auto;'>{table}</div>
            </div>"""
    else:
        cataloghi_html = "<p class='empty-msg'>⚠️ Nessun supermercato nel database.</p>"
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>🛒 Gestione Supermercati</title>
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
    .menu-btn:hover {{ border-color:var(--gold); }}
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
    main {{ padding:14px; max-width:680px; margin:0 auto; animation:fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .section-card {{
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); margin-bottom:10px; overflow:hidden; position:relative;
    }}
    .section-card::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .section-toggle {{
        width:100%; background:none; border:none; padding:14px 18px;
        display:flex; justify-content:space-between; align-items:center;
        cursor:pointer; color:var(--text); font-family:'DM Sans',sans-serif;
        font-size:0.92em; font-weight:700; line-height:1.5; transition:background 0.15s;
    }}
    .section-toggle:hover {{ background:var(--surface2); }}
    .u-block {{
        background:var(--surface2); border:1px solid var(--border);
        border-radius:12px; overflow:hidden; position:relative;
    }}
    .u-toggle {{
        width:100%; background:none; border:none; padding:12px 16px;
        display:flex; justify-content:space-between; align-items:center;
        cursor:pointer; color:var(--text); font-family:'DM Sans',sans-serif;
        font-size:0.88em; font-weight:700; line-height:1.5; transition:background 0.15s;
    }}
    .u-toggle:hover {{ background:var(--surface3); }}
    .u-toggle small {{ font-size:0.75em; color:var(--text-dim); font-weight:400; margin-left:6px; }}
    .u-arrow {{ font-size:0.72em; color:var(--text-dim); }}
    .u-content {{ border-top:1px solid var(--border); }}
    .section-inner {{ padding:12px; border-top:1px solid var(--border); display:none; }}
    table {{ width:100%; border-collapse:collapse; font-size:0.8em; }}
    thead tr {{ background:var(--surface3); }}
    th {{ padding:8px 10px; font-size:0.68em; font-weight:700; color:var(--text-dim); letter-spacing:1.2px; text-transform:uppercase; text-align:left; border-bottom:1px solid var(--border); }}
    td {{ padding:8px 10px; border-bottom:1px solid var(--border); color:var(--text-mid); vertical-align:top; }}
    td.td-price {{ text-align:right; font-weight:600; color:var(--text); }}
    td.td-desc {{ font-size:0.9em; color:var(--text-dim); }}
    tr:last-child td {{ border-bottom:none; }}
    .promo {{ color:var(--red); font-weight:700; }}
    .lista-pre {{
        white-space:pre-wrap; word-wrap:break-word; background:var(--surface2);
        border:1px solid var(--border); border-left:3px solid var(--gold);
        border-radius:8px; padding:12px; font-size:0.82em; color:var(--text-mid); line-height:1.5;
    }}
    .empty-msg {{ text-align:center; padding:16px; color:var(--text-dim); font-size:0.85em; font-style:italic; }}
    .btn-home {{
        display:block; text-align:center; padding:13px;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; border-radius:10px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.9em;
        line-height:1.5; margin-top:14px; transition:all 0.2s;
    }}
    .btn-home:hover {{ transform:translateY(-1px); box-shadow:0 6px 20px rgba(201,168,76,0.25); }}
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
    <div class="header-title">🛒 Gestione Supermercati</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="section-card">
        <button class="section-toggle" onclick="toggleS('lista_spesa', this)">
            <span>📋 Ultima Lista: {file_visualizzato}</span>
            <span class="u-arrow">▶</span>
        </button>
        <div id="lista_spesa" class="section-inner">
            {lista_inner}
        </div>
    </div>
    <div class="section-card">
        <button class="section-toggle" onclick="toggleS('cataloghi', this)">
            <span>🛒 Cataloghi ({len(supermercati)} supermercati)</span>
            <span class="u-arrow">▶</span>
        </button>
        <div id="cataloghi" class="section-inner" style="display:flex; flex-direction:column; gap:6px;">
            {cataloghi_html}
        </div>
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
    function toggleMenu() {{
        const m = document.getElementById("extraMenu");
        m.style.display = m.style.display === "block" ? "none" : "block";
    }}
    function toggleS(id, btn) {{
        const el = document.getElementById(id);
        const arrow = btn.querySelector(".u-arrow");
        const open = el.style.display !== "none" && el.style.display !== "";
        el.style.display = open ? "none" : "flex";
        if (id === "lista_spesa") el.style.display = open ? "none" : "block";
        arrow.textContent = open ? "▶" : "▼";
    }}
    function toggleU(id, btn) {{
        const el = document.getElementById(id);
        const arrow = btn.querySelector(".u-arrow");
        const open = el.style.display === "block";
        el.style.display = open ? "none" : "block";
        arrow.textContent = open ? "▶" : "▼";
    }}
    document.addEventListener("click", function(e) {{
        const menu = document.getElementById("extraMenu");
        const btn = document.querySelector(".menu-btn");
        if (menu && menu.style.display === "block" && !menu.contains(e.target) && e.target !== btn)
            menu.style.display = "none";
    }});
</script>
</body>
</html>"""
