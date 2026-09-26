#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import html
import datetime


# Html Ricerca Globale Web
def pagina_menu_esplora(self):
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    HOUSEHOLD_LABEL = "Patrimonio Complessivo"
    try:
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
            _db_portaf_e = json.load(_pf)
        _conti_lista_e = _db_portaf_e.get("conti", [])
    except Exception:
        _conti_lista_e = []
    conto_options_e = f'<option value="">-- {HOUSEHOLD_LABEL} --</option>\n' + "\n".join(
        f"<option value='{html.escape(c.get('nome',''))}'>{html.escape(c.get('nome',''))}</option>"
        for c in _conti_lista_e
    )
    mesi_it_map = {
        "01": "Gennaio", "02": "Febbraio", "03": "Marzo",
        "04": "Aprile", "05": "Maggio", "06": "Giugno",
        "07": "Luglio", "08": "Agosto", "09": "Settembre",
        "10": "Ottobre", "11": "Novembre", "12": "Dicembre"
    }
    mesi = [f"{m:02d} - {mesi_it_map[f'{m:02d}']}" for m in range(1, 13)]
    categorie = sorted(set(self.categorie))
    anno_corrente = datetime.date.today().year
    anni = [str(anno) for anno in range(anno_corrente, anno_corrente - 6, -1)]
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>🔎 Esplorazione Avanzata</title>
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
    main {{ padding:14px; max-width:560px; margin:0 auto; animation:fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .form-card {{
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); padding:20px 18px 18px;
        position:relative; overflow:hidden; margin-top:14px;
    }}
    .form-card::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .form-group {{ margin-bottom:12px; }}
    label {{
        display:block; font-size:0.68em; font-weight:600; color:var(--text-dim);
        letter-spacing:1.8px; text-transform:uppercase; margin-bottom:6px;
    }}
    input, select {{
        width:100%; padding:10px 13px; background:var(--surface2);
        border:1px solid var(--border); border-radius:9px; color:var(--text);
        font-family:'DM Sans',sans-serif; font-size:0.92em;
        transition:all 0.2s; outline:none; -webkit-appearance:none; appearance:none;
    }}
    input:focus, select:focus {{
        border-color:var(--border-active); background:var(--surface3);
        box-shadow:0 0 0 3px rgba(99,160,240,0.07);
    }}
    input::placeholder {{ color:var(--text-dim); }}
    select {{
        background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='7' viewBox='0 0 12 7'%3E%3Cpath fill='none' stroke='%23555' stroke-width='1.5' d='M1 1l5 5 5-5'/%3E%3C/svg%3E");
        background-repeat:no-repeat; background-position:right 12px center;
        padding-right:32px; cursor:pointer;
    }}
    select option {{ background:var(--surface2); color:var(--text); }}
    .form-row {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
    .collapsible-wrap {{ margin-top:14px; padding-top:14px; border-top:1px solid var(--border); }}
    .collapsible-toggle {{
        background:none; border:none; width:100%;
        display:flex; align-items:center; gap:8px;
        color:var(--text-mid); font-family:'DM Sans',sans-serif;
        font-size:0.82em; font-weight:700; letter-spacing:0.5px;
        cursor:pointer; padding:0 0 10px 0; text-align:left;
        line-height:1.5; transition:color 0.15s;
    }}
    .collapsible-toggle:hover {{ color:var(--blue); }}
    .arrow {{ font-size:0.7em; transition:transform 0.25s; }}
    .collapsible-open .arrow {{ transform:rotate(90deg); }}
    .collapsible-content {{ display:none; }}
    .collapsible-open .collapsible-content {{ display:block; }}
    .btn-submit {{
        width:100%; padding:13px; margin-top:16px;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; border:none; border-radius:9px;
        font-family:'DM Sans',sans-serif; font-size:0.95em; font-weight:700;
        line-height:1.5; letter-spacing:0.5px; cursor:pointer; transition:all 0.2s;
    }}
    .btn-submit:hover {{ transform:translateY(-1px); box-shadow:0 6px 20px rgba(201,168,76,0.25); }}
    .btn-submit:active {{ transform:translateY(0); }}
    .btn-home {{
        display:block; text-align:center; padding:13px; margin-top:10px;
        background:var(--surface); border:1px solid var(--border);
        color:var(--text-mid); border-radius:9px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.88em;
        line-height:1.5; transition:all 0.2s;
    }}
    .btn-home:hover {{ border-color:var(--border-active); color:var(--text); }}
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
    <div class="header-title">🔎 Esplorazione Avanzata</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="form-card">
        <form method="get" action="/cerca_avanzata">
            <div class="form-row">
                <div class="form-group">
                    <label>Categoria</label>
                    <select name="categoria">
                        <option value="">-- Qualsiasi --</option>
                        {''.join(f"<option value='{html.escape(str(cat))}'>{html.escape(str(cat))}</option>" for cat in categorie)}
                    </select>
                </div>
                <div class="form-group">
                    <label>Tipo</label>
                    <select name="tipo">
                        <option value="">-- Qualsiasi --</option>
                        <option value="Entrata">Entrata</option>
                        <option value="Uscita">Uscita</option>
                    </select>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Anno</label>
                    <select name="anno">
                        <option value="">-- Tutti --</option>
                        {''.join(f"<option value='{html.escape(a)}'>{html.escape(a)}</option>" for a in anni)}
                    </select>
                </div>
                <div class="form-group">
                    <label>Mese</label>
                    <select name="mese">
                        <option value="">-- Tutti --</option>
                        {''.join(f"<option value='{m.split(' - ')[0]}'>{m}</option>" for m in mesi)}
                    </select>
                </div>
            </div>
            <div class="form-group">
                <label>Conto</label>
                <select name="conto">
                    {conto_options_e}
                </select>
            </div>
            <div class="collapsible-wrap">
                <button type="button" class="collapsible-toggle" onclick="toggleCollapsible(this)">
                    <span class="arrow">▶</span> Filtri aggiuntivi
                </button>
                <div class="collapsible-content">
                    <div class="form-row">
                        <div class="form-group">
                            <label>Importo minimo (€)</label>
                            <input type="number" name="min_importo" step="0.01" placeholder="es: 10.50">
                        </div>
                        <div class="form-group">
                            <label>Importo massimo (€)</label>
                            <input type="number" name="max_importo" step="0.01" placeholder="es: 100.00">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Testo libero</label>
                        <input type="text" name="q" placeholder="es: pane, bolletta, abbonamento">
                    </div>
                </div>
            </div>
            <button type="submit" class="btn-submit">🔍 Avvia Esplorazione</button>
        </form>
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
    function toggleCollapsible(btn) {{
        btn.parentNode.classList.toggle('collapsible-open');
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

# Cambia Profilo (Web) - Logica di switch, richiamata dalla rotta POST
def esegui_switch_profilo_web(self, nome_profilo, crea_nuovo=False):
    import __main__ as _app
    import threading
    from moduli.costanti import salva_profilo_attivo
    from moduli.profili import elenco_profili, _nome_profilo_valido, _restart_application

    nome_profilo = (nome_profilo or "").strip()
    if not nome_profilo:
        return {"ok": False, "errore": "Nome profilo mancante"}

    profili_esistenti = elenco_profili(self)

    if crea_nuovo:
        nome_valido = _nome_profilo_valido(nome_profilo)
        if not nome_valido:
            return {"ok": False, "errore": "Nome profilo non valido"}
        if nome_valido in profili_esistenti:
            return {"ok": False, "errore": "Esiste già un profilo con questo nome"}
        nome_profilo = nome_valido
    else:
        if nome_profilo not in profili_esistenti:
            return {"ok": False, "errore": "Profilo non trovato"}

    if nome_profilo == _app.PROFILO_ATTIVO:
        return {"ok": False, "errore": "Questo profilo è già attivo"}

    if nome_profilo != "Principale":
        cartella_nuovo_profilo = os.path.join(_app.PROFILI_DIR, nome_profilo)
        db_nuovo_profilo = os.path.join(cartella_nuovo_profilo, "db")
        os.makedirs(db_nuovo_profilo, exist_ok=True)
        if crea_nuovo:
            from moduli.profili import _copia_certificati_e_licenza, _propaga_config_webserver
            _copia_certificati_e_licenza(_app.DB_DIR, db_nuovo_profilo)
            _propaga_config_webserver(_app.DB_DIR, db_nuovo_profilo)
    else:
        db_nuovo_profilo = os.path.join(_app.PATH_LOCALE, "db")
    _salvataggio_fatto = threading.Event()
    _errore_salvataggio = []
    def _salva_su_thread_principale():
        try:
            self.save_db()
        except Exception as e:
            _errore_salvataggio.append(str(e))
        finally:
            _salvataggio_fatto.set()
    self.after(0, _salva_su_thread_principale)
    if not _salvataggio_fatto.wait(timeout=30):
        return {"ok": False, "errore": "Timeout durante il salvataggio dei dati"}
    if _errore_salvataggio:
        return {"ok": False, "errore": f"Impossibile salvare i dati correnti: {_errore_salvataggio[0]}"}
    try:
        os.makedirs(db_nuovo_profilo, exist_ok=True)
        with open(os.path.join(db_nuovo_profilo, ".web_switch_pending"), "w") as _f:
            _f.write(datetime.datetime.now().isoformat())
    except Exception:
        pass
    salva_profilo_attivo(_app.PATH_LOCALE, nome_profilo)
    try:
        self._on_close_lock()
    except Exception:
        pass
    self.after(900, _restart_application)
    return {"ok": True, "profilo": nome_profilo, "nuovo": crea_nuovo}

# Html Cambia Profilo (Web)
def pagina_cambia_profilo_web(self):
    import __main__ as _app
    from moduli.profili import elenco_profili, _etichetta_profilo

    profili = elenco_profili(self)
    attivo  = _app.PROFILO_ATTIVO

    righe_altri = []
    for nome in profili:
        if nome == attivo:
            continue
        etichetta = html.escape(_etichetta_profilo(self, nome))
        nome_esc  = html.escape(nome, quote=True)
        righe_altri.append(f"""
        <div class="profile-item">
            <span class="profile-name">👤 {etichetta}</span>
            <form method="post" action="/switch_profilo_web" data-etichetta="{etichetta}" onsubmit="return confermaSwitchProfilo(this)">
                <input type="hidden" name="azione" value="switch">
                <input type="hidden" name="profilo" value="{nome_esc}">
                <button type="submit" class="btn-switch">🔄 Attiva</button>
            </form>
        </div>""")
    lista_altri_html = "".join(righe_altri) if righe_altri else \
        '<div class="empty-hint">Nessun altro profilo disponibile. Creane uno qui sotto.</div>'

    etichetta_attivo = html.escape(_etichetta_profilo(self, attivo))

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>👤 Cambia Profilo</title>
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
    main {{ padding:14px; max-width:480px; margin:0 auto; animation:fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .sec-card {{
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); margin-bottom:12px; position:relative; overflow:hidden;
    }}
    .sec-card::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .sec-title {{
        font-size:0.68em; font-weight:700; color:var(--text-dim); letter-spacing:1.8px;
        text-transform:uppercase; padding:14px 16px 8px;
    }}
    .active-box {{
        display:flex; align-items:center; justify-content:space-between;
        padding:10px 16px 16px;
    }}
    .active-name {{ font-size:1.05em; font-weight:800; color:var(--gold); }}
    .active-badge {{
        font-size:0.62em; font-weight:700; letter-spacing:1px; text-transform:uppercase;
        color:var(--green); background:rgba(76,175,130,0.12);
        padding:4px 9px; border-radius:6px;
    }}
    .profile-item {{
        display:flex; align-items:center; justify-content:space-between;
        padding:12px 16px; border-top:1px solid var(--border);
    }}
    .profile-item form {{ margin:0; }}
    .profile-name {{ font-size:0.9em; font-weight:600; color:var(--text); }}
    .btn-switch {{
        padding:8px 14px; border:none; border-radius:8px; cursor:pointer;
        background:linear-gradient(135deg, var(--blue), #2f5faa); color:#fff;
        font-family:'DM Sans',sans-serif; font-size:0.78em; font-weight:700;
        transition:all 0.2s;
    }}
    .btn-switch:hover {{ transform:translateY(-1px); box-shadow:0 6px 16px rgba(99,160,240,0.3); }}
    .empty-hint {{ padding:8px 16px 16px; font-size:0.82em; color:var(--text-dim); }}
    .new-form {{ padding:4px 16px 16px; display:flex; flex-wrap:wrap; gap:8px; }}
    .new-form input[type="text"] {{
        flex:1 1 120px; min-width:0; padding:10px 13px; background:var(--surface2);
        border:1px solid var(--border); border-radius:9px; color:var(--text);
        font-family:'DM Sans',sans-serif; font-size:0.88em; outline:none; transition:all 0.2s;
    }}
    .new-form input[type="text"]:focus {{
        border-color:var(--border-active); background:var(--surface3);
        box-shadow:0 0 0 3px rgba(99,160,240,0.07);
    }}
    .btn-nuovo {{
        padding:10px 14px; border:none; border-radius:9px; cursor:pointer; white-space:nowrap;
        background:linear-gradient(135deg, var(--green), #2d7a56); color:#000;
        font-family:'DM Sans',sans-serif; font-size:0.82em; font-weight:700; transition:all 0.2s;
    }}
    .btn-nuovo:hover {{ transform:translateY(-1px); box-shadow:0 6px 16px rgba(76,175,130,0.25); }}
    .warn-box {{
        background:rgba(224,90,90,0.08); border:1px solid rgba(224,90,90,0.25);
        color:var(--red); font-size:0.78em; padding:10px 13px; border-radius:10px;
        margin-bottom:14px; line-height:1.5;
    }}
    .err-box {{
        background:rgba(224,90,90,0.1); border:1px solid rgba(224,90,90,0.25);
        color:var(--red); font-size:0.82em; padding:10px 13px; border-radius:10px;
        margin-bottom:14px; display:none;
    }}
    .btn-home {{ display:block; text-align:center; padding:13px; margin-top:12px;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; border-radius:10px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.9em;
        line-height:1.5; transition:all 0.2s; }}
    .btn-home:hover {{ transform:translateY(-1px); box-shadow:0 6px 20px rgba(201,168,76,0.25); }}
    .modal-overlay {{ display:none; position:fixed; inset:0;
        background:rgba(0,0,0,0.75); backdrop-filter:blur(6px);
        z-index:3000; align-items:center; justify-content:center; }}
    .modal-box {{ background:var(--surface2); border:1px solid var(--border);
        border-radius:var(--radius-lg); padding:24px 20px; width:88%; max-width:320px; text-align:center; }}
    .modal-title {{ font-family:'DM Sans',sans-serif; font-size:1em; font-weight:800; color:var(--gold); margin-bottom:10px; }}
    .modal-text {{ font-size:0.88em; color:var(--text-mid); margin-bottom:18px; line-height:1.5; }}
    .modal-btns {{ display:flex; gap:10px; }}
    .m-btn {{ flex:1; padding:12px; border-radius:9px; border:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.88em; cursor:pointer; transition:all 0.15s; }}
    .m-cancel {{ background:var(--surface3); color:var(--text-mid); }}
    .m-confirm {{ background:linear-gradient(135deg, var(--blue), #2f5faa); color:#fff; }}
    .m-confirm:hover {{ box-shadow:0 6px 16px rgba(99,160,240,0.3); }}
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
                <a href="/utenze">💧 Utenze</a>
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
    <div class="header-title">👤 Cambia Profilo</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="err-box" id="errBox"></div>
    <div class="warn-box">⚠️ Il cambio profilo riavvia l'intera applicazione: tutte le sessioni web attive (anche su altri dispositivi) verranno temporaneamente disconnesse.</div>
    <div class="sec-card">
        <div class="sec-title">Profilo attivo</div>
        <div class="active-box">
            <span class="active-name">{etichetta_attivo}</span>
            <span class="active-badge">● Attivo</span>
        </div>
    </div>
    <div class="sec-card">
        <div class="sec-title">Passa ad un altro profilo</div>
        {lista_altri_html}
    </div>
    <div class="sec-card">
        <div class="sec-title">Crea nuovo profilo</div>
        <form class="new-form" method="post" action="/switch_profilo_web"
              onsubmit="return confermaCreaProfilo(this)">
            <input type="hidden" name="azione" value="nuovo">
            <input type="text" name="profilo" placeholder="Nome nuovo profilo" maxlength="40" required>
            <button type="submit" class="btn-nuovo">➕ Crea e Passa</button>
        </form>
    </div>
    <a href="/" class="btn-home">🏠 Torna alla Home</a>
</main>
<div id="switchModal" class="modal-overlay">
    <div class="modal-box">
        <div class="modal-title">🔄 Cambio Profilo</div>
        <div class="modal-text" id="modalText"></div>
        <div class="modal-btns">
            <button class="m-btn m-cancel" onclick="chiudiModalConferma()">Annulla</button>
            <button id="confermaSwitchBtn" class="m-btn m-confirm">Conferma</button>
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
        const btn = document.querySelector(".menu-btn");
        if (menu && menu.style.display === "block" && !menu.contains(e.target) && e.target !== btn)
            menu.style.display = "none";
    }});
    function confermaSwitchProfilo(form) {{
        const nome = form.dataset.etichetta || "";
        return apriModalConferma(form, "Passare al profilo '" + nome + "'?\\n\\nL'app verrà riavviata per tutti gli utenti connessi.");
    }}
    function confermaCreaProfilo(form) {{
        return apriModalConferma(form, "Creare il nuovo profilo e passare subito ad esso?\\n\\nL'app verrà riavviata.");
    }}
    let formInAttesa = null;
    function apriModalConferma(form, messaggio) {{
        formInAttesa = form;
        document.getElementById("modalText").textContent = messaggio;
        document.getElementById("switchModal").style.display = "flex";
        return false;
    }}
    function chiudiModalConferma() {{
        document.getElementById("switchModal").style.display = "none";
        formInAttesa = null;
    }}
    document.getElementById("confermaSwitchBtn").onclick = function() {{
        document.getElementById("switchModal").style.display = "none";
        if (formInAttesa) formInAttesa.submit();
    }};
    const p = new URLSearchParams(window.location.search);
    if (p.get('errore')) {{
        const el = document.getElementById('errBox');
        el.textContent = '❌ ' + p.get('errore');
        el.style.display = 'block';
    }}
</script>
</body>
</html>"""

# Html Switch Profilo In Corso (Web) - Interstiziale di riavvio
def pagina_switch_in_corso_web(self, nome_profilo, nuovo=False):
    from moduli.profili import _etichetta_profilo
    etichetta = html.escape(_etichetta_profilo(self, nome_profilo))
    delay_link_ms = 25000 if nuovo else 8000
    max_tentativi = 120 if nuovo else 60
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>🔄 Cambio Profilo in corso</title>
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
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
        --text:#e8e8e8; --text-dim:#666; --text-mid:#888; --radius-lg:18px;
    }}
    :root.light {{
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --border-active:rgba(61,127,212,0.5);
        --gold:#b8902a; --blue:#3d7fd4; --green:#3a9068; --red:#cc3333;
        --text:#1a1a1a; --text-dim:#888; --text-mid:#555;
    }}
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{
        font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text);
        min-height:100vh; min-height:100dvh; transition:background 0.3s,color 0.3s;
        display:flex; align-items:center; justify-content:center; padding:16px;
    }}
    .theme-toggle {{
        position:fixed; right:14px; top:14px;
        background:var(--surface3); border:1px solid var(--border);
        border-radius:8px; width:34px; height:34px;
        display:flex; align-items:center; justify-content:center;
        cursor:pointer; font-size:1em; transition:all 0.2s;
    }}
    .theme-toggle:hover {{ border-color:var(--gold); }}
    .box {{
        width:100%; max-width:380px; text-align:center;
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); padding:34px 24px; position:relative; overflow:hidden;
        box-shadow:0 20px 60px rgba(0,0,0,0.6);
    }}
    .box::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .spinner {{
        width:44px; height:44px; margin:0 auto 18px;
        border:3px solid var(--border); border-top-color:var(--gold);
        border-radius:50%; animation:spin 0.9s linear infinite;
    }}
    @keyframes spin {{ to {{ transform:rotate(360deg); }} }}
    .titolo {{ font-size:1.05em; font-weight:800; margin-bottom:8px; }}
    .sub {{ font-size:0.82em; color:var(--text-dim); line-height:1.5; }}
    .manual-link {{ display:inline-block; margin-top:18px; padding:10px 20px; font-size:0.82em; font-weight:700;
        color:#fff; text-decoration:none; border-radius:9px;
        background:linear-gradient(135deg, var(--blue), #2f5faa);
        opacity:0; transition:opacity 0.4s; }}
    .manual-link.visible {{ opacity:1; }}
</style>
</head>
<body>
<button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
<div class="box">
    <div class="spinner"></div>
    <div class="titolo">Passaggio al profilo "{etichetta}"</div>
    <div class="sub">L'applicazione si sta riavviando per caricare i dati del nuovo profilo.<br>Verrai reindirizzato automaticamente.</div>
    <a href="/login" class="manual-link" id="manualLink">🔄 Ricarica pagina</a>
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
    setTimeout(function() {{
        document.getElementById('manualLink').classList.add('visible');
    }}, {delay_link_ms});
    let tentativi = 0;
    function provaPing() {{
        tentativi++;
        fetch('/ping', {{cache:'no-store'}})
            .then(r => {{
                if (r.ok) {{ setTimeout(() => {{ window.location.href = '/'; }}, 700); }}
                else {{ ritenta(); }}
            }})
            .catch(() => ritenta());
    }}
    function ritenta() {{
        if (tentativi < {max_tentativi}) setTimeout(provaPing, 1500);
        else window.location.href = '/login';
    }}
    setTimeout(provaPing, 2500);
</script>
</body>
</html>"""
