#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import html
import datetime
import threading
from moduli.modello_spesa import SpesaEntry, campo, METODI_PAGAMENTO
from moduli.mappa_conti_trasferimenti import costruisci_mappa_conti_da_trasferimenti, conto_da_mappa
from moduli.web_utils import _fmt_it, _saldo_effettivo_web


# Html Pagina inserimenti Web
def html_form(self):
    import __main__ as _app
    LOGIN_WEB = _app.LOGIN_WEB
    NAME = _app.NAME
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    app_config_globale = _app.app_config_globale
    SMARTCAT_ABILITATO = app_config_globale.get("smartcat_enabled", True)
    smartcat_js = "true" if SMARTCAT_ABILITATO else "false"
    smartcat_text = "SmartCat Idle..." if SMARTCAT_ABILITATO else "SmartCat Off"
    smartcat_icon = "🛠️" if SMARTCAT_ABILITATO else "❌"
    PROFILO_ATTIVO = _app.PROFILO_ATTIVO
    folder = (PROFILO_ATTIVO if PROFILO_ATTIVO != "Principale" else os.path.basename(os.getcwd())).upper()
    ultimo_log_str = "Primo accesso"
    if os.path.exists(LOGIN_WEB):
        try:
            with open(LOGIN_WEB, "r", encoding="utf-8") as f:
                logs = json.load(f)
                if len(logs) > 1:
                    prec = logs[1]
                    ultimo_log_str = prec['data_ora']
                elif len(logs) == 1:
                    ultimo_log_str = "Primo accesso!"
        except:
            pass
    oggi = datetime.date.today()
    un_anno_fa = oggi - datetime.timedelta(days=365)
    frequenze = {}
    mappa_ricorrenti = {}
    spese_valide = []
    for d_reg, lista in self.spese.items():
        if d_reg < un_anno_fa: continue
        for voce in lista:
            try:
                cat, desc, imp, tipo = voce[:4]
                if not cat or cat == "Categoria Rimossa" or cat not in self.categorie:
                    continue
                importo_f = float(imp)
                spese_valide.append({
                    "cat": cat,
                    "imp": importo_f,
                    "tipo": tipo,
                    "desc": str(desc).lower().strip(),
                    "data": d_reg.strftime("%Y-%m-%d"),
                    "mese": d_reg.month,
                    "anno": d_reg.year
                })
                if cat not in frequenze: frequenze[cat] = 0
                frequenze[cat] += 1
                chiave_esatta = f"{cat}|{round(importo_f, 2)}"
                mappa_ricorrenti[chiave_esatta] = mappa_ricorrenti.get(chiave_esatta, 0) + 1
            except: continue
    smart_data_json = json.dumps({
        "spese": spese_valide,
        "frequenze": frequenze,
        "ricorrenti_esatti": mappa_ricorrenti
    })
    tipi_default_json = json.dumps(self.categorie_tipi)
    entrate_mese = 0.0
    uscite_mese = 0.0
    movimenti_mese_corrente = []
    for d, lista in self.spese.items():
        if d.month == oggi.month and d.year == oggi.year:
            for voce in lista:
                cat, desc, importo, tipo = voce[:4]
                if not cat or cat == "Categoria Rimossa" or cat not in self.categorie:
                    continue
                if tipo == "Entrata": entrate_mese += importo
                else: uscite_mese += importo
                movimenti_mese_corrente.append({
                    "data": d,
                    "cat": cat,
                    "desc": desc,
                    "imp": importo,
                    "tipo": tipo
                })
    movimenti_mese_corrente.sort(key=lambda x: x["data"], reverse=True)
    ultimi_movimenti_html = ""
    if not movimenti_mese_corrente:
        ultimi_movimenti_html = "<div style='text-align:center; padding:12px; color:#444; font-size:0.85em; letter-spacing:1px;'>NESSUN MOVIMENTO QUESTO MESE</div>"
    else:
        for mov in movimenti_mese_corrente[:10]:
            colore = "#4caf82" if mov["tipo"] == "Entrata" else "#e05a5a"
            segno = "+" if mov["tipo"] == "Entrata" else "-"
            data_str = mov["data"].strftime("%d/%m")
            ultimi_movimenti_html += f"""
            <div class="mov-item">
                <div class="mov-left">
                    <div class="mov-date">{data_str}</div>
                    <div class="mov-cat">{mov["cat"]}</div>
                    <div class="mov-desc">{mov["desc"]}</div>
                </div>
                <div class="mov-amount" style="color:{colore}">€ {segno}{_fmt_it(mov["imp"])}</div>
            </div>"""
    today = oggi.isoformat()
    anno_corrente = oggi.year
    categorie_options = "\n".join(
        f"<option value='{c}'>{c}</option>"
        for c in self.categorie if c != "Generica"
    )
    saldo_mese = entrate_mese - uscite_mese
    icona_saldo = "☀️" if saldo_mese >= 0 else "⛈️"
    saldo_colore = "#4caf82" if saldo_mese >= 0 else "#e05a5a"
    segno_saldo_mese = "+" if saldo_mese >= 0 else ""
    check_doppi_js = "true" if self.CHECK_DOPPI_MOV else "false"
    partecipanti_fs = []
    for p in self.nomi_partecipanti:
        tipo = p.get("tipo", "persona")
        ico = "CNT·" if tipo == "contenitore" else ("CTP·" if tipo == "personale" else "PER·")
        partecipanti_fs.append({"nome": p["nome"], "tipo": tipo, "ico": ico})
    partecipanti_json = json.dumps(partecipanti_fs)
    smartcat_toll = app_config_globale.get("smartcat_toll", 15)
    try:
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
            _db_portaf = json.load(_pf)
        _conti_lista = _db_portaf.get("conti", [])
        _conto_princ = next((c.get("nome","") for c in _conti_lista if c.get("principale")), "")
        conti_options = "\n".join(
            f'<option value="{c.get("nome","")}" {"selected" if c.get("nome","") == _conto_princ else ""}>{c.get("nome","")}\u2002(\u20ac {_fmt_it(_saldo_effettivo_web(self, c, _db_portaf))})</option>'
            for c in _conti_lista
        )
        mostra_conto_stile = "block" if _conti_lista else "none"
    except Exception:
        conti_options = ""
        mostra_conto_stile = "none"
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>💰 {NAME}</title>
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
        --bg: #050505; --surface: #0f0f0f; --surface2: #161616; --surface3: #1e1e1e;
        --border: rgba(255,255,255,0.07); --border-active: rgba(99,160,240,0.5);
        --gold: #c9a84c; --blue: #63a0f0; --green: #4caf82; --red: #e05a5a;
        --text: #e8e8e8; --text-dim: #555; --text-mid: #888;
        --radius: 10px; --radius-lg: 16px;
    }}
    :root.light {{
        --bg: #f5f5f0; --surface: #ffffff; --surface2: #f0efe8; --surface3: #e8e7df;
        --border: rgba(0,0,0,0.09); --border-active: rgba(61,127,212,0.5);
        --gold: #b8902a; --blue: #3d7fd4; --green: #3a9068; --red: #cc3333;
        --text: #1a1a1a; --text-dim: #999; --text-mid: #555;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        font-family: 'DM Sans', sans-serif; background: var(--bg); color: var(--text);
        min-height: 100vh; transition: background 0.3s, color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 40% at 50% -10%, rgba(99,160,240,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 60%);
    }}
    header {{
        padding: 12px 16px 10px; display: flex; align-items: center; justify-content: center;
        border-bottom: 1px solid var(--border); background: rgba(5,5,5,0.95);
        backdrop-filter: blur(20px); position: sticky; top: 0; z-index: 100;
    }}
    :root.light header {{ background: rgba(245,245,240,0.95); }}
    .menu-btn {{
        position: absolute; left: 14px; top: 50%; transform: translateY(-50%);
        background: var(--surface3); border: 1px solid var(--border); color: var(--gold);
        width: 34px; height: 34px; border-radius: 9px; font-size: 1em;
        cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s;
    }}
    .menu-btn:hover {{ border-color: var(--gold); box-shadow: 0 0 12px rgba(201,168,76,0.2); }}
    .header-title {{
        font-family: 'DM Sans', sans-serif; font-size: 0.95em; font-weight: 700;
        letter-spacing: 0.5px; color: var(--text); text-align: center; line-height: 1.3;
    }}
    .header-sub {{
        font-size: 0.6em; color: var(--text-dim); font-weight: 400; letter-spacing: 2px;
        text-transform: uppercase; margin-top: 2px; cursor: pointer; transition: color 0.2s; text-align: center;
    }}
    .header-sub:hover {{ color: var(--blue); }}
    .theme-toggle {{
        position: absolute; right: 14px; top: 50%; transform: translateY(-50%);
        background: var(--surface3); border: 1px solid var(--border);
        border-radius: 8px; width: 34px; height: 34px;
        display: flex; align-items: center; justify-content: center;
        cursor: pointer; font-size: 1em; transition: all 0.2s;
    }}
    .theme-toggle:hover {{ border-color: var(--gold); }}
    .nav-dropdown {{
        position: absolute; top: calc(100% + 6px); left: 10px;
        background: var(--surface2); border: 1px solid var(--border);
        border-radius: var(--radius-lg); display: none; z-index: 1000;
        width: 270px; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.7);
    }}
    .nav-dropdown a {{
        display: flex; align-items: center; gap: 10px; padding: 10px 16px;
        text-decoration: none; color: var(--text-mid); border-bottom: 1px solid var(--border);
        font-size: 0.87em; transition: all 0.15s;
    }}
    .nav-dropdown a:last-child {{ border-bottom: none; }}
    .nav-dropdown a:hover {{ background: var(--surface3); color: var(--text); padding-left: 22px; }}
    .nav-group-btn {{ display:flex; justify-content:space-between; align-items:center; width:100%;
        padding:8px 16px; background:none; border:none; font-family:inherit; color:var(--gold);
        font-size:0.7em; font-weight:700; letter-spacing:1px; text-transform:uppercase; cursor:pointer; opacity:0.85; }}
    .nav-group-btn:hover {{ opacity:1; background:var(--surface3); }}
    .nav-arrow {{ font-size:0.85em; transition:transform 0.15s; }}
    .nav-group-items {{ display:none; flex-direction:column; }}
    .nav-group-items.open {{ display:flex; }}
    main {{ padding: 0 14px; max-width: 480px; margin: 0 auto; padding-bottom: 20px; animation: fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    .saldo-card {{
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius-lg); margin-top: 10px; margin-bottom: 10px; overflow: hidden;
    }}
    .saldo-header {{
        padding: 8px 16px; cursor: pointer; display: flex; justify-content: space-between;
        align-items: center; font-size: 0.85em; font-weight: 500; color: var(--text-mid);
        transition: background 0.15s; user-select: none;
    }}
    .saldo-header:hover {{ background: var(--surface2); }}
    .saldo-content {{ display: none; padding: 0 12px 12px; }}
    .saldo-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px; margin-bottom: 10px; }}
    .saldo-item {{
        background: var(--surface2); border-radius: 8px; padding: 8px 6px;
        text-align: center; border: 1px solid var(--border);
    }}
    .saldo-item small {{ display: block; font-size: 0.62em; color: var(--text-dim); letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 4px; }}
    .saldo-item b {{ font-size: 0.88em; font-weight: 600; }}
    .movimenti-section {{ border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }}
    .movimenti-header {{
        padding: 8px 12px; font-size: 0.78em; color: var(--text-dim); cursor: pointer;
        display: flex; justify-content: space-between; background: var(--surface2); user-select: none;
    }}
    .movimenti-content {{ display: none; }}
    .mov-item {{
        display: flex; justify-content: space-between; align-items: center;
        padding: 8px 12px; border-bottom: 1px solid var(--border);
    }}
    .mov-item:last-child {{ border-bottom: none; }}
    .mov-left {{ line-height: 1.25; overflow: hidden; }}
    .mov-date {{ font-size: 0.65em; color: var(--text-dim); }}
    .mov-cat {{ font-size: 0.83em; font-weight: 500; color: var(--text); }}
    .mov-desc {{ font-size: 0.7em; color: var(--text-dim); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 190px; }}
    .mov-amount {{ font-weight: 600; font-size: 0.88em; white-space: nowrap; margin-left: 8px; }}
    .form-card {{
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius-lg); padding: 16px 16px 0; position: relative; overflow: hidden;
    }}
    .form-card::before {{
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .smartcat-badge {{
        display: inline-flex; align-items: center; gap: 5px;
        background: var(--surface2); border: 1px solid var(--border);
        border-radius: 20px; padding: 4px 11px; font-size: 0.7em; color: var(--text-dim);
        letter-spacing: 0.3px; transition: all 0.3s;
    }}
    .smartcat-badge.active {{ border-color: rgba(76,175,130,0.4); color: var(--green); }}
    .badge-row {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }}
    .btn-sync-mini {{
        display: inline-flex; align-items: center; gap: 4px;
        background: var(--surface2); border: 1px solid rgba(99,160,240,0.3);
        border-radius: 20px; padding: 4px 10px; font-size: 0.7em; color: var(--blue);
        cursor: pointer; letter-spacing: 0.3px; transition: all 0.2s;
    }}
    .btn-sync-mini:hover {{ border-color: var(--blue); background: rgba(99,160,240,0.08); }}
    .btn-sync-mini:disabled {{ opacity: 0.45; cursor: default; }}
    .form-group {{ margin-bottom: 10px; }}
    label {{
        display: block; font-size: 0.68em; font-weight: 500; color: var(--text-dim);
        letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 5px;
    }}
    input, select {{
        width: 100%; padding: 10px 13px; background: var(--surface2);
        border: 1px solid var(--border); border-radius: 9px; color: var(--text);
        font-family: 'DM Sans', sans-serif; font-size: 0.93em;
        transition: all 0.2s; outline: none; -webkit-appearance: none; appearance: none;
    }}
    input:focus, select:focus {{
        border-color: var(--border-active); background: var(--surface3);
        box-shadow: 0 0 0 3px rgba(99,160,240,0.07);
    }}
    input::placeholder {{ color: var(--text-dim); }}
    select {{
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='7' viewBox='0 0 12 7'%3E%3Cpath fill='none' stroke='%23555' stroke-width='1.5' d='M1 1l5 5 5-5'/%3E%3C/svg%3E");
        background-repeat: no-repeat; background-position: right 12px center;
        padding-right: 32px; cursor: pointer;
    }}
    select option {{ background: var(--surface2); color: var(--text); }}
    .importo-wrap {{ position: relative; }}
    .importo-wrap input {{ padding-left: 30px; font-size: 1.05em; font-weight: 500; }}
    .euro-sign {{
        position: absolute; left: 12px; top: 50%; transform: translateY(-50%);
        color: var(--gold); font-weight: 700; font-size: 0.95em; pointer-events: none;
    }}
    .error-inline {{
        display: none; position: absolute; right: 10px; top: 50%; transform: translateY(-50%);
        color: var(--red); font-size: 0.68em; font-weight: 600; pointer-events: none; white-space: nowrap;
    }}
    #tipo_select.uscita {{ border-color: rgba(224,90,90,0.3); color: #e05a5a; }}
    #tipo_select.entrata {{ border-color: rgba(76,175,130,0.3); color: #4caf82; }}
    .highlight-smart {{ border-color: rgba(76,175,130,0.5) !important; background: rgba(76,175,130,0.04) !important; }}
    input::-webkit-outer-spin-button, input::-webkit-inner-spin-button {{ -webkit-appearance: none; margin: 0; }}
    input[type=number] {{ -moz-appearance: textfield; }}
    #fs_select.persona {{ border-color: rgba(99,160,240,0.3); color: var(--blue); }}
    #fs_select.contenitore {{ border-color: rgba(201,168,76,0.3); color: var(--gold); }}
    #fs_select.personale {{ border-color: rgba(76,175,130,0.3); color: var(--green); }}
    .btn-submit {{
        width: 100%; padding: 13px; margin-top: 8px;
        background: linear-gradient(135deg, #c9a84c 0%, #8a6820 100%);
        color: #000; border: none; border-radius: 9px;
        font-family: 'DM Sans', sans-serif; font-size: 0.92em; font-weight: 700;
        line-height: 1.5; letter-spacing: 0.5px; cursor: pointer; transition: all 0.2s;
    }}
    .btn-submit:hover {{ transform: translateY(-1px); box-shadow: 0 6px 20px rgba(201,168,76,0.25); }}
    .btn-submit:active {{ transform: translateY(0); }}
    .pdf-upload-card {{
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius-lg); margin-top: 10px; overflow: hidden;
    }}
    .pdf-upload-header {{
        padding: 11px 16px; cursor: pointer; display: flex; justify-content: space-between;
        align-items: center; font-size: 0.85em; font-weight: 500; color: var(--text-mid);
        transition: background 0.15s; user-select: none;
    }}
    .pdf-upload-header:hover {{ background: var(--surface2); }}
    .pdf-upload-body {{ display: none; padding: 12px 14px 14px; }}
    .drop-zone {{
        border: 2px dashed var(--border); border-radius: 10px;
        padding: 20px 12px; text-align: center; cursor: pointer;
        transition: all 0.2s; color: var(--text-dim); font-size: 0.82em;
    }}
    .drop-zone:hover, .drop-zone.dragover {{
        border-color: var(--blue); background: rgba(99,160,240,0.04); color: var(--text);
    }}
    .drop-zone .dz-icon {{ font-size: 1.8em; display: block; margin-bottom: 6px; }}
    .drop-zone .dz-filename {{ font-size: 0.88em; color: var(--blue); margin-top: 4px; font-weight: 500; }}
    .btn-analizza {{
        width: 100%; padding: 11px; margin-top: 10px;
        background: linear-gradient(135deg, #3d7fd4 0%, #1a4f8a 100%);
        color: #fff; border: none; border-radius: 9px;
        font-family: 'DM Sans', sans-serif; font-size: 0.88em; font-weight: 700;
        cursor: pointer; transition: all 0.2s;
    }}
    .btn-analizza:hover {{ transform: translateY(-1px); box-shadow: 0 6px 20px rgba(61,127,212,0.25); }}
    .btn-analizza:disabled {{ opacity: 0.5; cursor: default; transform: none; box-shadow: none; }}
    .pdf-result {{
        margin-top: 10px; padding: 10px 12px; border-radius: 8px;
        font-size: 0.82em; line-height: 1.6; display: none;
        border: 1px solid var(--border); background: var(--surface2);
    }}
    .pdf-result.ok {{ border-color: rgba(76,175,130,0.4); }}
    .pdf-result.err {{ border-color: rgba(224,90,90,0.4); color: var(--red); }}
    #customConfirm {{
        display: none; position: fixed; z-index: 9999; left: 0; top: 0;
        width: 100%; height: 100%; background: rgba(0,0,0,0.8); backdrop-filter: blur(6px);
    }}
    .modal-box {{
        background: var(--surface2); border: 1px solid var(--border);
        margin: 22% auto; padding: 24px 20px; border-radius: var(--radius-lg);
        width: 85%; max-width: 340px; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.6);
    }}
    .modal-box h3 {{ font-family: 'DM Sans', sans-serif; font-size: 1em; margin-bottom: 10px; color: var(--gold); }}
    .modal-box p {{ color: var(--text-mid); font-size: 0.85em; line-height: 1.5; }}
    .modal-actions {{ display: flex; gap: 10px; margin-top: 18px; justify-content: center; }}
    .btn-ok {{ background: var(--blue); color: #000; border: none; padding: 10px 22px; border-radius: 8px; font-weight: 700; font-family: 'DM Sans', sans-serif; cursor: pointer; font-size: 0.85em; line-height: 1.5; }}
    .btn-no {{ background: var(--surface3); color: var(--text-mid); border: 1px solid var(--border); padding: 10px 22px; border-radius: 8px; cursor: pointer; font-size: 0.85em; line-height: 1.5; }}
</style>
</head>
<body>
<div id="customConfirm">
    <div class="modal-box">
        <h3>⚠️ Movimento Duplicato</h3>
        <p id="confirmMsg"></p>
        <div class="modal-actions">
            <button class="btn-no" onclick="rispostaModal(false)">Annulla</button>
            <button class="btn-ok" onclick="rispostaModal(true)">Inserisci</button>
        </div>
    </div>
</div>
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
    <div>
        <div class="header-title">🏠 Inserisci Operazione</div>
        <div class="header-sub" id="user-badge" onclick="mostraLog()">👤 {folder}</div>
    </div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="saldo-card">
        <div class="saldo-header" onclick="toggleSection('summaryContent','summaryArrow')">
            <span>📊 Saldo Mensile {icona_saldo}</span>
            <span id="summaryArrow" style="font-size:0.75em;">▼</span>
        </div>
        <div id="summaryContent" class="saldo-content">
            <div class="saldo-grid">
                <div class="saldo-item">
                    <small>Entrate</small>
                    <b style="color:var(--green)">€ {_fmt_it(entrate_mese)}</b>
                </div>
                <div class="saldo-item">
                    <small>Uscite</small>
                    <b style="color:var(--red)">€ {_fmt_it(uscite_mese)}</b>
                </div>
                <div class="saldo-item">
                    <small>Saldo</small>
                    <b style="color:{saldo_colore}">€ {segno_saldo_mese}{_fmt_it(saldo_mese)}</b>
                </div>
            </div>
            <div class="movimenti-section">
                <div class="movimenti-header" onclick="event.stopPropagation(); toggleSection('movimentiContent','movimentiArrow')">
                    <span>🕒 Ultimi 10 Movimenti Mese</span>
                    <span id="movimentiArrow">▼</span>
                </div>
                <div id="movimentiContent" class="movimenti-content">
                    {ultimi_movimenti_html}
                </div>
            </div>
        </div>
    </div>
    <div class="form-card">
        <div class="badge-row">
            <div class="smartcat-badge" id="smartcat_badge">
                <span>{smartcat_icon}</span> {smartcat_text}
            </div>
            <button type="button" class="btn-sync-mini" id="btn_sync_web" onclick="avviaSyncWeb()">🔄 Sync Gmail</button>
        </div>
        <form method="post" action="/" onsubmit="return validaForm(event)">
            <div class="form-group">
                <label>Importo</label>
                <div class="importo-wrap">
                    <span class="euro-sign">€</span>
                    <input name="importo" id="importo_input" type="number" step="0.01"
                        placeholder="0.00" autofocus oninput="aggiornaSmartCat(this.value)">
                    <span id="local_error" class="error-inline">⚠️ Importo non valido!</span>
                </div>
            </div>
            <div class="form-group">
                <label>Categoria</label>
                <select name="categoria" id="categoria_select" onchange="applicaTipoDefault(this.value)">
                    <option value="Generica">Generica</option>
                    {categorie_options}
                </select>
            </div>
            <div style="display:flex; gap:8px; margin-bottom:10px;">
                <div style="flex:1">
                    <label>Tipo</label>
                    <select name="tipo" id="tipo_select" class="uscita" onchange="aggiornaColoreTipo()">
                        <option value="Uscita">Uscita</option>
                        <option value="Entrata">Entrata</option>
                    </select>
                </div>
                <div style="flex:1">
                    <label>Data</label>
                    <input name="data" id="data_input" type="date" value="{today}">
                </div>
            </div>
            <div class="form-group">
                <label>Descrizione</label>
                <input name="descrizione" id="desc_input"
                    placeholder="Es: Pizza, Colazione, Fattura, Regali">
            </div>
            <div class="form-group" id="fs_group" style="display:none">
                <label>Partecipante FairShare</label>
                <select id="fs_select" name="fairshare" onchange="applicaPartecipante(this.value)">
                    <option value="">— Nessuno —</option>
                </select>
            </div>
            <div class="form-group" id="conto_group" style="display:{mostra_conto_stile}">
                <label>Conto</label>
                <select name="conto" id="conto_select">
                    <option value="">(nessuno)</option>
                    {conti_options}
                </select>
            </div>
            <button type="submit" class="btn-submit" style="position:sticky; bottom:16px; box-shadow:0 4px 20px rgba(0,0,0,0.4);">➕ Aggiungi Movimento</button>
        </form>
    </div>

    <div class="pdf-upload-card">
        <div class="pdf-upload-header" onclick="toggleSection('pdfUploadBody','pdfUploadArrow')">
            <span>📎 Carica PDF → Crea Movimento</span>
            <span id="pdfUploadArrow" style="font-size:0.75em;">▼</span>
        </div>
        <div id="pdfUploadBody" class="pdf-upload-body">
            <div class="drop-zone" id="dropZone" onclick="document.getElementById('pdfFileInput').click()"
                 ondragover="event.preventDefault(); this.classList.add('dragover')"
                 ondragleave="this.classList.remove('dragover')"
                 ondrop="gestisciDrop(event)">
                <span class="dz-icon">📄</span>
                Trascina qui il PDF oppure tocca per selezionare
                <div class="dz-filename" id="dz_filename"></div>
            </div>
            <input type="file" id="pdfFileInput" accept=".pdf" style="display:none" onchange="selezionaPdf(this)">
            <button type="button" class="btn-analizza" id="btn_analizza" onclick="caricaPdfWeb()" disabled>
                🤖 Analizza con Gemini e Crea Movimento
            </button>
            <div class="pdf-result" id="pdf_result"></div>
        </div>
    </div>
</main>
<script>
    const dbSmart = {smart_data_json};
    const tipiDefault = {tipi_default_json};
    const checkDoppiAbilitato = {check_doppi_js};
    const smartCatActive = {smartcat_js};
    const smartCatToll = {smartcat_toll};
    const partecipantiFS = {partecipanti_json};

    function inizializzaFS() {{
        const sel = document.getElementById("fs_select");
        const grp = document.getElementById("fs_group");
        if (!partecipantiFS || partecipantiFS.length === 0) return;
        grp.style.display = "block";
        partecipantiFS.forEach(p => {{
            const opt = document.createElement("option");
            opt.value = p.ico + p.nome;
            opt.textContent = p.ico + " " + p.nome;
            opt.dataset.tipo = p.tipo;
            sel.appendChild(opt);
        }});
    }}

    function applicaPartecipante(prefisso) {{
        const desc = document.getElementById("desc_input");
        const sel = document.getElementById("fs_select");
        let testo = desc.value.trim();
        partecipantiFS.forEach(p => {{
            const tag = p.ico + p.nome;
            if (testo.startsWith(tag)) testo = testo.slice(tag.length).trim();
        }});
        desc.value = prefisso ? prefisso + " " + testo : testo;
        const opt = sel.options[sel.selectedIndex];
        if (opt && opt.dataset.tipo) {{
            sel.className = opt.dataset.tipo;
        }} else {{
            sel.className = "";
        }}
    }}

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
    function aggiornaColoreTipo() {{
        const st = document.getElementById("tipo_select");
        st.className = st.value === "Entrata" ? "entrata" : "uscita";
    }}
    function toggleSection(contentId, arrowId) {{
        const content = document.getElementById(contentId);
        const arrow = document.getElementById(arrowId);
        const isOpen = content.style.display === "block";
        content.style.display = isOpen ? "none" : "block";
        if (arrow) arrow.innerHTML = isOpen ? "▼" : "▲";
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
    function applicaTipoDefault(categoria) {{
        const st = document.getElementById("tipo_select");
        const tipoPredefinito = tipiDefault[categoria];
        if (tipoPredefinito) st.value = tipoPredefinito;
        aggiornaColoreTipo();
    }}
    function aggiornaSmartCat(valore) {{
        if (!smartCatActive) return;
        const sc = document.getElementById("categoria_select");
        const st = document.getElementById("tipo_select");
        const badge = document.getElementById("smartcat_badge");
        const inp = document.getElementById("importo_input");
        inp.style.borderColor = "var(--border)";
        document.getElementById("local_error").style.display = "none";
        if (!valore || valore.trim() === "") {{
            sc.value = "Generica";
            applicaTipoDefault("Generica");
            badge.className = "smartcat-badge";
            badge.innerHTML = "<span>🛠️</span> SmartCat in attesa...";
            return;
        }}
        const impCorrente = parseFloat(valore);
        if (isNaN(impCorrente)) return;
        let migliorPunteggio = Infinity;
        let categoriaMigliore = null;
        let tipoMigliore = "Uscita";
        if (dbSmart.ricorrenti_esatti) {{
            for (let chiave in dbSmart.ricorrenti_esatti) {{
                let parti = chiave.split('|');
                let cat = parti[0];
                let impStorico = parseFloat(parti[1]);
                let diff = Math.abs(impStorico - impCorrente);
                if (diff < 0.01) {{
                    let freq = dbSmart.ricorrenti_esatti[chiave];
                    let punteggio = -2000 - freq;
                    if (punteggio < migliorPunteggio) {{
                        migliorPunteggio = punteggio;
                        categoriaMigliore = cat;
                        tipoMigliore = tipiDefault[cat] || "Uscita";
                    }}
                }}
            }}
        }}
        if (migliorPunteggio > -1000) {{
            for (let chiave in dbSmart.ricorrenti_esatti) {{
                let parti = chiave.split('|');
                let cat = parti[0];
                let impStorico = parseFloat(parti[1]);
                let freq = dbSmart.ricorrenti_esatti[chiave];
                let diff = Math.abs(impStorico - impCorrente);
                let punteggio;
                if (diff <= 0.05) {{
                    punteggio = -1000 - freq + (diff * 10);
                }} else if (diff <= impCorrente * 0.02) {{
                    punteggio = diff - (freq * 2);
                }} else if (diff <= smartCatToll) {{
                    punteggio = diff - freq;
                }} else {{
                    continue;
                }}
                if (punteggio < migliorPunteggio) {{
                    migliorPunteggio = punteggio;
                    categoriaMigliore = cat;
                    tipoMigliore = tipiDefault[cat] || "Uscita";
                }}
            }}
        }}
        if (categoriaMigliore) {{
            if (sc.value !== categoriaMigliore || st.value !== tipoMigliore) {{
                sc.value = categoriaMigliore;
                st.value = tipoMigliore;
                sc.classList.add("highlight-smart");
                setTimeout(() => sc.classList.remove("highlight-smart"), 500);
            }}
            badge.className = "smartcat-badge active";
            badge.innerHTML = "<span>💡</span> SmartCat attiva";
        }}
        aggiornaColoreTipo();
    }}
    window.addEventListener('load', function() {{
        const inp = document.getElementById("importo_input");
        if (inp) inp.focus();
        applicaTipoDefault(document.getElementById("categoria_select").value);
        aggiornaColoreTipo();
        inizializzaFS();
        const p = new URLSearchParams(window.location.search);
        if (p.get('salvato') === '1' && inp) {{
            const t = document.createElement("div");
            t.innerText = "✓ Salvato";
            Object.assign(t.style, {{
                position: "absolute", right: "10px", top: "50%",
                transform: "translateY(-50%)", backgroundColor: "var(--green)",
                color: "black", padding: "3px 9px", borderRadius: "6px",
                fontSize: "11px", fontWeight: "bold", zIndex: "5",
                pointerEvents: "none", boxShadow: "0 2px 8px rgba(76,175,130,0.3)"
            }});
            inp.parentElement.appendChild(t);
            window.history.replaceState({{}}, document.title, window.location.pathname);
            setTimeout(() => {{
                t.style.transition = "opacity 0.5s";
                t.style.opacity = "0";
                setTimeout(() => t.remove(), 500);
            }}, 1500);
        }}
    }});
    window.onclick = function(event) {{
        if (!event.target.matches('.menu-btn') && !event.target.matches('.theme-toggle')) {{
            const dropdowns = document.getElementsByClassName("nav-dropdown");
            for (let i = 0; i < dropdowns.length; i++) {{
                if (dropdowns[i].style.display === "block") dropdowns[i].style.display = "none";
            }}
        }}
    }}
    function mostraLog() {{
        const badge = document.getElementById('user-badge');
        const originale = "PER· {folder}";
        const dataLog = "🕒 {ultimo_log_str}";
        if (badge.innerText.toUpperCase().includes("{folder}".toUpperCase())) {{
            badge.style.opacity = "0";
            setTimeout(() => {{
                badge.innerText = dataLog;
                badge.style.color = "var(--blue)";
                badge.style.opacity = "1";
            }}, 200);
            setTimeout(() => {{
                badge.style.opacity = "0";
                setTimeout(() => {{
                    badge.innerText = originale;
                    badge.style.color = "";
                    badge.style.opacity = "1";
                }}, 200);
            }}, 3000);
        }}
    }}
    let formInAttesa = null;
    function rispostaModal(procedi) {{
        document.getElementById("customConfirm").style.display = "none";
        if (procedi && formInAttesa) formInAttesa.submit();
    }}
    function validaForm(e) {{
        const form = e.target;
        const inp = document.getElementById("importo_input");
        const errorMsg = document.getElementById("local_error");
        const cat = document.getElementById("categoria_select").value;
        const data = document.getElementById("data_input").value;
        const valore = parseFloat(inp.value);
        if (!inp.value || isNaN(valore) || valore <= 0) {{
            e.preventDefault();
            inp.value = "";
            inp.style.borderColor = "rgba(224,90,90,0.5)";
            errorMsg.style.display = "block";
            setTimeout(() => {{
                errorMsg.style.display = "none";
                inp.style.borderColor = "var(--border)";
                inp.placeholder = "0.00";
            }}, 2000);
            return false;
        }}
        if (checkDoppiAbilitato && typeof dbSmart !== 'undefined' && dbSmart.spese) {{
            const mese = data.substring(0, 7);
            const trovato = dbSmart.spese.find(s =>
                s.imp === valore &&
                s.cat === cat &&
                s.data.substring(0, 7) === mese
            );
            if (trovato) {{
                e.preventDefault();
                formInAttesa = form;
                const d = trovato.data.split("-");
                const catSelect = document.getElementById("categoria_select");
                const catName = catSelect.options[catSelect.selectedIndex].text;
                const msg = "Hai già inserito € " + valore.toFixed(2) + " per '" + catName + "' il " + d[2]+"-"+d[1]+"-"+d[0] + ". Vuoi continuare?";
                document.getElementById("confirmMsg").innerText = msg;
                document.getElementById("customConfirm").style.display = "block";
                return false;
            }}
        }}
        return true;
    }}

    let _pdfFile = null;

    function selezionaPdf(input) {{
        if (input.files && input.files[0]) {{
            _pdfFile = input.files[0];
            document.getElementById("dz_filename").textContent = _pdfFile.name;
            document.getElementById("btn_analizza").disabled = false;
        }}
    }}

    function gestisciDrop(event) {{
        event.preventDefault();
        document.getElementById("dropZone").classList.remove("dragover");
        const file = event.dataTransfer.files[0];
        if (file && file.name.toLowerCase().endsWith(".pdf")) {{
            _pdfFile = file;
            document.getElementById("dz_filename").textContent = file.name;
            document.getElementById("btn_analizza").disabled = false;
        }}
    }}

    function caricaPdfWeb() {{
        if (!_pdfFile) return;
        const btn = document.getElementById("btn_analizza");
        const res = document.getElementById("pdf_result");
        btn.disabled = true;
        btn.textContent = "⏳ Analisi in corso...";
        res.style.display = "none";
        const fd = new FormData();
        fd.append("pdf_file", _pdfFile);
        fetch("/carica_pdf_web", {{method: "POST", body: fd}})
            .then(r => r.json())
            .then(data => {{
                btn.textContent = "🤖 Analizza con Gemini e Crea Movimento";
                btn.disabled = false;
                res.style.display = "block";
                if (data.ok) {{
                    const segno = data.direzione === "Entrata" ? "+" : "-";
                    const col   = data.direzione === "Entrata" ? "var(--green)" : "var(--red)";
                    res.className = "pdf-result ok";
                    res.innerHTML =
                        "<b style='color:var(--green)'>✅ Movimento creato!</b><br>" +
                        "<b>" + data.desc + "</b><br>" +
                        "Importo: <span style='color:" + col + ";font-weight:700'>" +
                        "€ " + segno + data.importo.toFixed(2) + "</span> · " +
                        data.categoria + " · " + data.data;
                    _pdfFile = null;
                    document.getElementById("dz_filename").textContent = "";
                    document.getElementById("pdfFileInput").value = "";
                }} else {{
                    res.className = "pdf-result err";
                    res.innerHTML = "⚠️ " + (data.errore || "Errore sconosciuto");
                }}
            }})
            .catch(() => {{
                btn.textContent = "🤖 Analizza con Gemini e Crea Movimento";
                btn.disabled = false;
                res.style.display = "block";
                res.className = "pdf-result err";
                res.innerHTML = "❌ Errore di connessione";
            }});
    }}

    function avviaSyncWeb() {{
        const btn = document.getElementById("btn_sync_web");
        if (btn.disabled) return;
        btn.disabled = true;
        btn.textContent = "⏳ Sincronizzazione in corso...";
        fetch("/avvia_sync_web", {{method: "POST"}})
            .then(r => r.json())
            .then(data => {{
                if (data.ok) {{
                    btn.textContent = "✅ Avviata sull\u2019app!";
                }} else {{
                    btn.textContent = "⚠️ " + (data.errore || "Configurazione mancante");
                }}
                setTimeout(() => {{
                    btn.disabled = false;
                    btn.textContent = "🔄 Sincronizza Email (Gmail)";
                }}, 3500);
            }})
            .catch(() => {{
                btn.textContent = "❌ Errore connessione";
                setTimeout(() => {{
                    btn.disabled = false;
                    btn.textContent = "🔄 Sincronizza Email (Gmail)";
                }}, 2500);
            }});
    }}
</script>
</body>
</html>"""
    

# Html Movimenti Mese Web
def pagina_risultati_avanzati(self, params):
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    from datetime import datetime
    from collections import defaultdict
    import html as html_escape
    categoria_filtro = params.get("categoria", [""])[0].strip().lower()
    anno = params.get("anno", [""])[0].strip()
    mese = params.get("mese", [""])[0].strip()
    tipo = params.get("tipo", [""])[0].strip().lower()
    conto_filtro = params.get("conto", [""])[0].strip()
    min_importo = float(params.get("min_importo", ["0"])[0] or 0)
    max_importo = float(params.get("max_importo", ["999999"])[0] or 999999)
    query = params.get("q", [""])[0].strip().lower()
    from urllib.parse import urlencode
    _query_originale = urlencode({
        k: v[0] for k, v in params.items() if v and v[0]
    })
    provenienza_con_filtri = "/cerca_avanzata" + (f"?{_query_originale}" if _query_originale else "")
    _agganci_r = costruisci_mappa_conti_da_trasferimenti(PORTAFOGLIO_BANCARIO)
    _uso_ordinale_r = {}
    risultati_categorizzati = defaultdict(list)
    for data in sorted(self.spese.keys(), reverse=True):
        if anno and str(data.year) != anno:
            continue
        if mese and f"{data.month:02d}" != mese:
            continue
        for idx_voce, voce in enumerate(self.spese[data]):
            if len(voce) < 4:
                continue
            cat, descrizione, importo, tipo_voce = voce[:4]
            if categoria_filtro and cat.strip().lower() != categoria_filtro:
                continue
            if tipo and tipo_voce.strip().lower() != tipo:
                continue
            if not (min_importo <= importo <= max_importo):
                continue
            if query and not (
                query in descrizione.lower()
                or query in tipo_voce.lower()
                or query in cat.lower()
                or query in str(importo)
            ):
                continue
            nome_conto_voce = campo(voce, "conto", "")
            if not nome_conto_voce:
                nome_conto_voce = conto_da_mappa(_agganci_r, _uso_ordinale_r, data.strftime("%d-%m-%Y"), importo, tipo_voce or "Uscita")
            if conto_filtro and nome_conto_voce != conto_filtro:
                continue
            risultati_categorizzati[cat].append({
                "data": data.strftime("%d-%m-%Y"),
                "desc": html_escape.escape(descrizione),
                "imp": float(importo),
                "tipo": tipo_voce.strip(),
                "idx": idx_voce,
                "cat": cat,
                "conto": nome_conto_voce
            })
    entrate_totali = sum(v["imp"] for vlist in risultati_categorizzati.values() for v in vlist if v["tipo"].lower() == "entrata")
    uscite_totali = sum(v["imp"] for vlist in risultati_categorizzati.values() for v in vlist if v["tipo"].lower() != "entrata")
    saldo = entrate_totali - uscite_totali
    colore_saldo = "#4caf82" if saldo >= 0 else "#e05a5a"
    segno_saldo = "+" if saldo >= 0 else ""
    anno_corrente = datetime.now().year
    schede_html = ""
    for cat, voci in sorted(risultati_categorizzati.items()):
        totale_cat = sum(v["imp"] if v["tipo"].lower() == "entrata" else -v["imp"] for v in voci)
        colore_tot = "#4caf82" if totale_cat >= 0 else "#e05a5a"
        simbolo_tot = "+" if totale_cat >= 0 else "−"
        voce_html = ""
        for v in voci:
            simbolo = "+" if v["tipo"].lower() == "entrata" else "−"
            colore_tipo = "#4caf82" if v["tipo"].lower() == "entrata" else "#e05a5a"
            _cat_js = v['cat'].replace("'", "\\'")
            voce_html += f"""
            <li class="voce-item">
                <div class="voce-actions">
                    <form method="get" action="/modifica" style="display:inline;">
                        <input type="hidden" name="data" value="{v['data']}">
                        <input type="hidden" name="idx" value="{v['idx']}">
                        <input type="hidden" name="from" value="{html_escape.escape(provenienza_con_filtri)}">
                        <button type="submit" class="btn-action btn-edit">✏️</button>
                    </form>
                    <button type="button" class="btn-action btn-delete"
                        onclick="apriModal('{v['data']}', '{v['idx']}', '{_cat_js}', '{_fmt_it(v['imp'])}', {'1' if 'ALL·' in v['desc'] else '0'})">❌</button>
                    <span class="voce-data">{v['data']}</span>
                </div>
                <div class="voce-body">
                    <span class="voce-imp" style="color:{colore_tipo}">€ {simbolo}{_fmt_it(v['imp'])}</span>
                    <span class="voce-tipo" style="color:{colore_tipo}">{v['tipo']}</span>
                    <div class="voce-desc">{v['desc']}</div>
                    {f'<div class="voce-desc" style="opacity:0.7;">🏦 {html_escape.escape(v["conto"])}</div>' if v.get('conto') else ''}
                </div>
            </li>"""
        schede_html += f"""
        <div class="cat-block">
            <button class="cat-toggle" onclick="toggleCategoria(this)">
                <span class="freccia">▶</span>
                <span class="cat-name">{html_escape.escape(cat)}</span>
                <span class="cat-totale" style="color:{colore_tot}">€ {simbolo_tot}{_fmt_it(abs(totale_cat))} · {len(voci)} voci</span>
            </button>
            <div class="cat-content">
                <ul class="voce-list">{voce_html}</ul>
            </div>
        </div>"""
    nessun_risultato = "" if schede_html else "<div class='empty-msg'>Nessuna voce trovata.</div>"
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🔍 Risultati Ricerca</title>
<script>
    (function() {{
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    }})();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg: #050505; --surface: #0f0f0f; --surface2: #161616; --surface3: #1e1e1e;
        --border: rgba(255,255,255,0.07); --border-active: rgba(99,160,240,0.5);
        --gold: #c9a84c; --blue: #63a0f0; --green: #4caf82; --red: #e05a5a;
        --text: #e8e8e8; --text-dim: #555; --text-mid: #888; --radius-lg: 18px;
    }}
    :root.light {{
        --bg: #f5f5f0; --surface: #ffffff; --surface2: #f0efe8; --surface3: #e8e7df;
        --border: rgba(0,0,0,0.09); --gold: #b8902a; --blue: #3d7fd4;
        --green: #3a9068; --red: #cc3333; --text: #1a1a1a; --text-dim: #999; --text-mid: #555;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        font-family: 'DM Sans', sans-serif; background: var(--bg); color: var(--text);
        min-height: 100vh; padding-bottom: 50px; transition: background 0.3s, color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 40% at 50% -10%, rgba(99,160,240,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 60%);
    }}
    header {{
        padding: 18px 20px 14px; display: flex; align-items: center; justify-content: center;
        border-bottom: 1px solid var(--border); background: rgba(5,5,5,0.95);
        backdrop-filter: blur(20px); position: sticky; top: 0; z-index: 100;
    }}
    :root.light header {{ background: rgba(245,245,240,0.95); }}
    .menu-btn {{
        position: absolute; left: 16px; top: 50%; transform: translateY(-50%);
        background: var(--surface3); border: 1px solid var(--border); color: var(--gold);
        width: 38px; height: 38px; border-radius: 10px; font-size: 1.1em;
        cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s;
    }}
    .menu-btn:hover {{ border-color: var(--gold); box-shadow: 0 0 14px rgba(201,168,76,0.2); }}
    .header-title {{ font-family: 'DM Sans', sans-serif; font-size: 1.05em; font-weight: 700; color: var(--text); }}
    .theme-toggle {{
        position: absolute; right: 16px; top: 50%; transform: translateY(-50%);
        background: var(--surface3); border: 1px solid var(--border);
        border-radius: 8px; width: 34px; height: 34px;
        display: flex; align-items: center; justify-content: center;
        cursor: pointer; font-size: 1em; transition: all 0.2s;
    }}
    .theme-toggle:hover {{ border-color: var(--gold); }}
    .nav-dropdown {{
        position: absolute; top: calc(100% + 8px); left: 10px;
        background: var(--surface2); border: 1px solid var(--border);
        border-radius: var(--radius-lg); display: none; z-index: 1000;
        width: 275px; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.7);
    }}
    .nav-dropdown a {{
        display: flex; align-items: center; gap: 10px; padding: 11px 18px;
        text-decoration: none; color: var(--text-mid); border-bottom: 1px solid var(--border);
        font-size: 0.88em; transition: all 0.15s;
    }}
    .nav-dropdown a:last-child {{ border-bottom: none; }}
    .nav-dropdown a:hover {{ background: var(--surface3); color: var(--text); padding-left: 24px; }}
    .nav-group-btn {{ display:flex; justify-content:space-between; align-items:center; width:100%;
        padding:8px 16px; background:none; border:none; font-family:inherit; color:var(--gold);
        font-size:0.7em; font-weight:700; letter-spacing:1px; text-transform:uppercase; cursor:pointer; opacity:0.85; }}
    .nav-group-btn:hover {{ opacity:1; background:var(--surface3); }}
    .nav-arrow {{ font-size:0.85em; transition:transform 0.15s; }}
    .nav-group-items {{ display:none; flex-direction:column; }}
    .nav-group-items.open {{ display:flex; }}
    main {{ padding: 16px; max-width: 640px; margin: 0 auto; animation: fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    .riepilogo {{
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius-lg); margin: 16px 0; overflow: hidden; position: relative;
    }}
    .riepilogo::before {{
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .riepilogo-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; }}
    .riepilogo-item {{ padding: 16px 12px; text-align: center; border-right: 1px solid var(--border); }}
    .riepilogo-item:last-child {{ border-right: none; }}
    .riepilogo-item small {{ display: block; font-size: 0.65em; color: var(--text-dim); letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 5px; }}
    .riepilogo-item b {{ font-size: 0.95em; font-weight: 600; }}
    .cat-block {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); margin-bottom: 10px; overflow: hidden; }}
    .cat-toggle {{ width: 100%; background: none; border: none; padding: 14px 18px; display: flex; align-items: center; gap: 10px; cursor: pointer; text-align: left; transition: background 0.15s; }}
    .cat-toggle:hover {{ background: var(--surface2); }}
    .freccia {{ font-size: 0.7em; color: var(--text-dim); transition: transform 0.2s; min-width: 12px; }}
    .cat-name {{ font-family: 'DM Sans', sans-serif; font-size: 0.9em; font-weight: 700; color: var(--text); flex: 1; }}
    .cat-totale {{ font-size: 0.82em; font-weight: 600; white-space: nowrap; }}
    .cat-content {{ display: none; border-top: 1px solid var(--border); }}
    .voce-list {{ list-style: none; padding: 0; margin: 0; }}
    .voce-item {{ padding: 12px 18px; border-bottom: 1px solid var(--border); }}
    .voce-item:last-child {{ border-bottom: none; }}
    .voce-actions {{ display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }}
    .btn-action {{ background: var(--surface2); border: 1px solid var(--border); border-radius: 6px; padding: 4px 8px; cursor: pointer; font-size: 0.8em; transition: all 0.15s; }}
    .btn-action:hover {{ background: var(--surface3); border-color: rgba(255,255,255,0.15); }}
    .voce-data {{ font-size: 0.78em; color: var(--text-mid); margin-left: 4px; font-weight: 500; }}
    .voce-body {{ padding-left: 2px; }}
    .voce-imp {{ font-size: 1.05em; font-weight: 700; margin-right: 8px; }}
    .voce-tipo {{ font-size: 0.75em; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; opacity: 0.8; }}
    .voce-desc {{ font-size: 0.82em; color: var(--text-mid); margin-top: 3px; }}
    .btn-nav {{
        display: block; text-align: center; padding: 14px; border-radius: 10px;
        text-decoration: none; font-family: 'DM Sans', sans-serif; font-weight: 700;
        font-size: 0.9em; line-height: 1.5; cursor: pointer; border: none;
        width: 100%; margin-bottom: 10px; transition: all 0.2s;
    }}
    .btn-gold {{ background: linear-gradient(135deg, var(--gold) 0%, #8a6820 100%); color: #000; }}
    .btn-outline {{ background: var(--surface); border: 1px solid var(--border); color: var(--text-mid); }}
    .btn-nav:hover {{ transform: translateY(-1px); box-shadow: 0 6px 20px rgba(0,0,0,0.3); }}
    .empty-msg {{ text-align: center; padding: 40px 20px; color: var(--text-dim); font-size: 0.9em; letter-spacing: 1px; }}
    #deleteModal {{
        display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0,0,0,0.8); backdrop-filter: blur(6px); z-index: 3000;
        align-items: center; justify-content: center;
    }}
    .modal-box {{
        background: var(--surface2); border: 1px solid var(--border); padding: 28px 24px;
        border-radius: var(--radius-lg); width: 85%; max-width: 340px;
        text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.6);
    }}
    .modal-box h3 {{ font-family: 'DM Sans', sans-serif; font-size: 1.05em; color: var(--red); margin-bottom: 12px; }}
    .modal-box p {{ color: var(--text-mid); font-size: 0.87em; line-height: 1.5; }}
    .modal-actions {{ display: flex; gap: 10px; margin-top: 22px; justify-content: center; }}
    .btn-ok {{ background: var(--red); color: white; border: none; padding: 11px 24px; border-radius: 8px; font-weight: 700; font-family: 'DM Sans', sans-serif; cursor: pointer; font-size: 0.87em; line-height: 1.5; }}
    .btn-no {{ background: var(--surface3); color: var(--text-mid); border: 1px solid var(--border); padding: 11px 24px; border-radius: 8px; cursor: pointer; font-size: 0.87em; line-height: 1.5; }}
</style>
</head>
<body>
<div id="deleteModal" style="display:none;">
    <div class="modal-box">
        <h3>🗑️ Conferma Eliminazione</h3>
        <p id="modalText"></p>
        <div class="modal-actions">
            <button class="btn-no" onclick="closeModal()">Annulla</button>
            <button class="btn-ok" id="finalDeleteBtn">Elimina</button>
        </div>
    </div>
</div>
<div id="pdfModal" style="display:none; position:fixed; z-index:9999; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.75); align-items:center; justify-content:center;">
    <div class="modal-box">
        <h3>ALL· Documento Allegato</h3>
        <p>Vuoi eliminare anche il documento PDF dal registro?</p>
        <div class="modal-actions">
            <button class="btn-no" onclick="confermaCancella(0)">Solo Movimento</button>
            <button class="btn-ok" onclick="confermaCancella(1)">Elimina Tutto</button>
        </div>
    </div>
</div>
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
    <div class="header-title">🔍 Risultati Ricerca{f' · {html_escape.escape(conto_filtro)}' if conto_filtro else ''}</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="riepilogo">
        <div class="riepilogo-grid">
            <div class="riepilogo-item">
                <small>Entrate</small>
                <b style="color:var(--green)">€ {_fmt_it(entrate_totali)}</b>
            </div>
            <div class="riepilogo-item">
                <small>Uscite</small>
                <b style="color:var(--red)">€ {_fmt_it(uscite_totali)}</b>
            </div>
            <div class="riepilogo-item">
                <small>Saldo</small>
                <b style="color:{colore_saldo}">€ {segno_saldo}{_fmt_it(saldo)}</b>
            </div>
        </div>
    </div>
    {schede_html}
    {nessun_risultato}
    <div style="margin-top: 20px;">
        <form method="get" action="/menu_esplora">
            <button type="submit" class="btn-nav btn-gold">🔙 Torna al Menu Esplora</button>
        </form>
        <form method="get" action="/">
            <button type="submit" class="btn-nav btn-outline">🏠 Torna alla Home</button>
        </form>
    </div>
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
    let dData = null, dIdx = null, dHaPdf = false;
    function apriModal(data, idx, cat, imp, ha_pdf) {{
        dData = data; dIdx = idx; dHaPdf = (ha_pdf === '1' || ha_pdf === 1);
        document.getElementById("modalText").innerHTML = "Eliminare <b>" + cat + "</b> — <b>€ " + imp + "</b>?";
        document.getElementById("deleteModal").style.display = "flex";
    }}
    function closeModal() {{ document.getElementById("deleteModal").style.display = "none"; }}
    document.getElementById("finalDeleteBtn").onclick = function() {{
        closeModal();
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
    function toggleMenu() {{
        const m = document.getElementById("extraMenu");
        m.style.display = m.style.display === "block" ? "none" : "block";
    }}
    function toggleCategoria(btn) {{
        const content = btn.nextElementSibling;
        const isVisible = content.style.display === "block";
        content.style.display = isVisible ? "none" : "block";
        btn.querySelector(".freccia").textContent = isVisible ? "▶" : "▼";
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

# Html Form Modifica Voce esistente (data/categoria/descrizione/importo/conto)
def modifica_voce_form(self, params):
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    from datetime import datetime
    data_str = params.get("data", [""])[0]
    idx = int(params.get("idx", ["0"])[0])
    provenienza = params.get("from", ["/lista"])[0]
    d_obj = datetime.strptime(data_str, "%d-%m-%Y").date()
    data_html = d_obj.strftime("%Y-%m-%d")
    if d_obj not in self.spese or idx >= len(self.spese[d_obj]):
        return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
        <meta http-equiv="refresh" content="2;url={provenienza}">
        <title>Errore</title></head><body style="background:#050505;color:#e05a5a;font-family:sans-serif;padding:2rem;">
        ⚠️ Voce non trovata (indice obsoleto). Reindirizzamento in corso...</body></html>"""
    voce = self.spese[d_obj][idx]
    categoria_corrente, descrizione, importo, tipo = voce[:4]
    categorie_options = "\n".join(
        f"<option value='{c}' {'selected' if c == categoria_corrente else ''}>{c}</option>"
        for c in sorted(self.categorie)
    )
    _conto_corrente = campo(voce, "conto", "")
    if not _conto_corrente:
        try:
            _conto_corrente = self._trova_conto_da_portafoglio(d_obj, round(float(importo), 2), tipo)
        except Exception:
            _conto_corrente = ""
    if not _conto_corrente:
        _conto_corrente = "(nessuno)"
    try:
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
            _db_portaf_m = json.load(_pf)
        _conti_lista_m = _db_portaf_m.get("conti", [])
        conti_options_mod = '<option value="">(nessuno)</option>\n' + "\n".join(
            f'<option value="{c.get("nome","")}" {"selected" if c.get("nome","") == _conto_corrente else ""}>'
            f'{c.get("nome","")}\u2002(\u20ac {_fmt_it(_saldo_effettivo_web(self, c, _db_portaf_m))})</option>'
            for c in _conti_lista_m
        )
        mostra_conto_mod = "block" if _conti_lista_m else "none"
    except Exception:
        conti_options_mod = '<option value="">(nessuno)</option>'
        mostra_conto_mod = "none"
    _metodo_corrente = campo(voce, "metodo_pagamento", "")
    metodo_options_mod = '<option value="">— (nessuno)</option>\n' + "\n".join(
        f'<option value="{m}" {"selected" if m == _metodo_corrente else ""}>{m}</option>'
        for m in METODI_PAGAMENTO
    )
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>✏️ Modifica Voce</title>
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
        min-height:100vh; display:flex; align-items:center; justify-content:center;
        padding:20px; transition:background 0.3s,color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 40% at 50% -10%, rgba(99,160,240,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 60%);
    }}
    .card {{
        width:100%; max-width:440px;
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); overflow:hidden;
        box-shadow:0 30px 80px rgba(0,0,0,0.6);
        animation:fadeIn 0.3s ease;
    }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(10px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .card::before {{
        content:''; display:block; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .card-head {{
        padding:16px 20px 14px; border-bottom:1px solid var(--border);
        font-family:'DM Sans',sans-serif; font-size:1em; font-weight:800;
        text-align:center; color:var(--text);
    }}
    .card-body {{ padding:18px 20px 20px; }}
    .form-group {{ margin-bottom:12px; }}
    label {{
        display:block; font-size:0.65em; font-weight:700; color:var(--text-dim);
        letter-spacing:1.8px; text-transform:uppercase; margin-bottom:6px;
    }}
    input, select {{
        width:100%; padding:10px 13px; background:var(--surface2);
        border:1px solid var(--border); border-radius:9px; color:var(--text);
        font-family:'DM Sans',sans-serif; font-size:0.92em;
        outline:none; transition:all 0.2s; -webkit-appearance:none; appearance:none;
    }}
    input:focus, select:focus {{
        border-color:var(--border-active); background:var(--surface3);
        box-shadow:0 0 0 3px rgba(99,160,240,0.07);
    }}
    input[type="date"]::-webkit-calendar-picker-indicator {{ filter:invert(0.5); }}
    select {{
        background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='7' viewBox='0 0 12 7'%3E%3Cpath fill='none' stroke='%23555' stroke-width='1.5' d='M1 1l5 5 5-5'/%3E%3C/svg%3E");
        background-repeat:no-repeat; background-position:right 12px center;
        padding-right:32px; cursor:pointer;
    }}
    select option {{ background:var(--surface2); color:var(--text); }}
    .form-row {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
    .btn-save {{
        width:100%; padding:13px; margin-top:6px; border:none;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; border-radius:9px;
        font-family:'DM Sans',sans-serif; font-size:0.95em; font-weight:700;
        line-height:1.5; letter-spacing:0.5px; cursor:pointer; transition:all 0.2s;
    }}
    .btn-save:hover {{ transform:translateY(-1px); box-shadow:0 6px 20px rgba(201,168,76,0.25); }}
    .btn-cancel {{
        display:block; text-align:center; padding:12px; margin-top:8px;
        background:var(--surface2); border:1px solid var(--border);
        color:var(--text-mid); border-radius:9px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.88em;
        line-height:1.5; transition:all 0.2s;
    }}
    .btn-cancel:hover {{ border-color:var(--border-active); color:var(--text); }}
</style>
<script>
    function applyTheme(t) {{
        document.documentElement.classList.toggle('light', t === 'light');
    }}
    applyTheme(localStorage.getItem('theme') || 'dark');
</script>
</head>
<body>
<div class="card">
    <div class="card-head">✏️ Modifica Voce</div>
    <div class="card-body">
        <form method="post" action="/salva_modifica">
            <input type="hidden" name="vecchia_data" value="{data_str}">
            <input type="hidden" name="vecchio_idx" value="{idx}">
            <input type="hidden" name="provenienza" value="{html.escape(provenienza)}">

            <div class="form-row">
                <div class="form-group">
                    <label>Data</label>
                    <input name="nuova_data" type="date" value="{data_html}" required>
                </div>
                <div class="form-group">
                    <label>Tipo</label>
                    <select name="tipo">
                        <option value="Entrata" {"selected" if tipo == "Entrata" else ""}>Entrata</option>
                        <option value="Uscita"  {"selected" if tipo != "Entrata" else ""}>Uscita</option>
                    </select>
                </div>
            </div>

            <div class="form-group">
                <label>Categoria</label>
                <select name="categoria" required>{categorie_options}</select>
            </div>

            <div class="form-group">
                <label>Descrizione</label>
                <input name="descrizione" type="text" value="{descrizione}">
            </div>

            <div class="form-group">
                <label>Importo (€)</label>
                <input name="importo" type="number" step="0.01" value="{importo}" required>
            </div>

            <div class="form-group" id="conto_group_mod" style="display:{mostra_conto_mod}">
                <label>Conto</label>
                <select name="conto">
                    {conti_options_mod}
                </select>
            </div>

            <div class="form-group">
                <label>Metodo Pagamento</label>
                <select name="metodo">
                    {metodo_options_mod}
                </select>
            </div>

            <button type="submit" class="btn-save">💾 Salva Modifiche</button>
        </form>
        <a href="{html.escape(provenienza)}" class="btn-cancel">🔙 Annulla</a>
    </div>
</div>
</body>
</html>"""

def cancella_voce_web(self, giorno_str, idx):
    try:
        data_obj = datetime.datetime.strptime(giorno_str, "%d-%m-%Y").date()
        if data_obj in self.spese:
            if 0 <= idx < len(self.spese[data_obj]):
                self.spese[data_obj].pop(idx)
                self.annulla_azione_gamification("movimento")
                if not self.spese[data_obj]:
                    del self.spese[data_obj]
                self.save_db()
                self._sync_fairshare_e_aggiorna()
                self.carica_db_web()
                self.refresh_gui()
                return True
    except Exception as e:
        print(f"Errore dati cancellazione: {e}")
    return False

def aggiungi_voce_web(self, voce):
    import __main__ as _app
    DB_FILE = _app.DB_FILE
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            dati = json.load(f)
    except Exception:
        dati = {"spese": []}
    try:
        d_obj = datetime.datetime.strptime(voce["date"], "%Y-%m-%d").date()
        data_str = d_obj.strftime("%d-%m-%Y")
    except Exception as e:
        print(f"Data non valida: {voce['date']} → {e}")
        return
    try:
        voce_normalizzata = SpesaEntry.da_dict({
            "categoria":   voce.get("categoria", ""),
            "descrizione": voce.get("descrizione", ""),
            "importo":     voce.get("importo", 0.0),
            "tipo":        voce.get("tipo", "Uscita"),
            "id_ricorrenza": voce.get("id_ricorrenza"),
            "id_spesa":    voce.get("id_spesa"),
            "conto":       voce.get("conto", ""),
            "ora":         voce.get("ora") or datetime.datetime.now().strftime("%H:%M"),
            "hashtag":     voce.get("hashtag", []),
            "metodo_pagamento": voce.get("metodo_pagamento", ""),
        }).a_dict()
        voce_normalizzata["date"] = data_str
        voce = voce_normalizzata
    except Exception as e:
        print(f"[aggiungi_voce_web] Normalizzazione fallita, uso voce originale: {e}")
        voce["date"] = data_str
    for giorno in dati["spese"]:
        if giorno["date"] == data_str:
            giorno["entries"].append(voce)
            break
    else:
        dati["spese"].append({
            "date": data_str,
            "entries": [voce]
        })
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(dati, f, indent=2, ensure_ascii=False)
    self.carica_db_web()
    self.registra_azione_gamification("movimento")
    self.refresh_gui()
 

def carica_db_web(self):
    import __main__ as _app
    DB_FILE = _app.DB_FILE
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            dati = json.load(f)
    except Exception as e:
        print(f"Errore lettura DB: {e}")
        return
    self.spese = {}
    for giorno in dati.get("spese", []):
        try:
            d = datetime.datetime.strptime(giorno["date"], "%d-%m-%Y").date()
            entries = [SpesaEntry.da_dict(e) for e in giorno["entries"]]
            self.spese[d] = entries
        except Exception as ex:
            print(f"Errore parsing giorno {giorno.get('date')}: {ex}")

def analizza_pdf_web(self, pdf_bytes, filename_originale="documento.pdf"):
    import __main__ as _app
    API_KEY = _app.API_KEY
    DOC_DIR = _app.DOC_DIR
    GEMINI = _app.GEMINI
    LOG_IMPORTAZIONI = _app.LOG_IMPORTAZIONI
    REGISTRY_FILE = _app.REGISTRY_FILE
    genai_client = _app.genai_client
    types = _app.types
    import re, json, shutil
    from datetime import datetime
    CATEGORIA_PDF = "Zona @Web/Bank"
    if CATEGORIA_PDF not in self.categorie:
        self.categorie.append(CATEGORIA_PDF)
        self.categorie_tipi[CATEGORIA_PDF] = "Uscita"
        self.aggiorna_combobox_categorie()
    if not os.path.exists(DOC_DIR):
        os.makedirs(DOC_DIR)
    client = genai_client.Client(api_key=API_KEY)
    lista_cat = ", ".join(f'"{c}"' for c in self.categorie)
    prompt = (
        f"Analizza questo documento PDF.\n"
        f"PRIMA DI TUTTO: se il documento è un estratto conto bancario, lista movimenti bancari, "
        f"rendiconto con più di 3 transazioni elencate in tabella, o qualsiasi documento che "
        f"riepiloga più operazioni finanziarie distinte, restituisci SOLO questo JSON:\n"
        f'{{\"tipo_documento\": \"estratto_conto\"}}\n'
        f"Altrimenti, se è una singola fattura, ricevuta, cedolino, scontrino o documento con UN SOLO importo principale, estrai:\n"
        f'{{\"tipo_documento\": \"singolo\", \"importo\": float, \"azienda\": \"nome\", '
        f'\"data\": \"YYYY-MM-DD\", '
        f'\"fattura\": \"numero o null\", \"direzione\": \"Entrata/Uscita\", '
        f'\"scadenza\": \"GG/MM/YYYY o null\", '
        f'\"categoria\": \"categoria più adatta tra [{lista_cat}]\"}}\n'
        f"REGOLE:\n"
        f"1. Se non trovi l'importo scrivi 0.01.\n"
        f"2. Determina Entrata o Uscita dal contesto. Un cedolino pensione, uno stipendio "
        f"o un accredito/bonifico ricevuto sono sempre un'ENTRATA, mai un'Uscita.\n"
        f"3. Per il campo 'azienda': se è una bolletta/fattura usa il nome del fornitore; "
        f"se è un cedolino pensione o stipendio, usa SEMPRE e SOLO la dicitura "
        f"\"prestazione rata MM/AAAA\" con il mese e l'anno di competenza della rata — NON "
        f"il nome del beneficiario, NON il numero di prestazione/pratica. Nessuna emoji o "
        f"prefisso in 'azienda'.\n"
        f"4. Per la data usa quella del fatto economico (data valuta, data pagamento, "
        f"data emissione/fattura, scadenza/competenza), MAI la data di stampa/generazione "
        f"del documento (es. \"Stampa elaborata il\", \"Generato il\"); se non leggibile "
        f"usa la data odierna.\n"
        f"5. Restituisci SOLO il JSON, senza testo aggiuntivo né backtick."
    )
    r = client.models.generate_content(
        model=GEMINI,
        contents=[
            types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
            prompt
        ]
    )
    raw = r.text.strip().replace("```json", "").replace("```", "").strip()
    dati = json.loads(raw)
    if dati.get("tipo_documento") == "estratto_conto":
        return {"ok": False, "errore": "Estratto conto non supportato — usa Importa Movimenti dal menu principale."}
    importo   = float(dati.get("importo") or 0.01)
    azienda   = str(dati.get("azienda") or "Documento").strip()
    fattura   = dati.get("fattura")
    direzione = dati.get("direzione") or "Uscita"
    scadenza  = dati.get("scadenza")
    cat_ia    = dati.get("categoria", "")
    categoria = cat_ia if cat_ia in self.categorie else CATEGORIA_PDF
    data_str_ia = dati.get("data")
    _testo_web = ""
    try:
        import pymupdf as _fitz_web
        _doc_web = _fitz_web.open(stream=pdf_bytes, filetype="pdf")
        _testo_web = "".join(p.get_text() for p in _doc_web).lower()
        _doc_web.close()
        for _pat in (
            r"data\s+valuta\s*:?\s*(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})",
            r"data\s+pagamento\s*:?\s*(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})",
            r"data\s+scadenza\s*:?\s*(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})",
            r"data\s+emissione\s*:?\s*(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})",
        ):
            _m = re.search(_pat, _testo_web)
            if _m:
                _gg, _mm, _aaaa = _m.groups()
                if len(_aaaa) == 2:
                    _aaaa = "20" + _aaaa
                data_str_ia = f"{_aaaa}-{int(_mm):02d}-{int(_gg):02d}"
                break
    except Exception:
        pass
    try:
        data_oggi = datetime.strptime(data_str_ia, "%Y-%m-%d").date()
    except Exception:
        data_oggi = datetime.now().date()
    _m_pens = re.search(r"prestazione\s+rata\s+(\d{1,2})[/\-](\d{2,4})", _testo_web) if _testo_web else None
    if _m_pens:
        _mm_p, _aaaa_p = _m_pens.groups()
        if len(_aaaa_p) == 2:
            _aaaa_p = "20" + _aaaa_p
        desc      = f"prestazione rata {int(_mm_p):02d}/{_aaaa_p}"
        direzione = "Entrata"
    else:
        desc = azienda
        if fattura: desc += f" {fattura}"
        if scadenza and scadenza != "null": desc += f" SCD:{scadenza}"
    desc_spesa = f"ALL· {desc}"
    for s in self.spese.get(data_oggi, []):
        if s[1] in (desc_spesa, desc) and abs(s[2] - importo) < 0.01:
            return {"ok": False, "errore": "Movimento già presente (duplicato)"}
    def _san(s, n=30):
        return re.sub(r'[^\w\.-]', '', s.strip().replace(' ', '_').upper())[:n]
    data_ggmmaaaa   = data_oggi.strftime("%d%m%Y")
    imp_centesimi   = int(round(importo * 100))
    nome_reg        = f"{data_ggmmaaaa}_{_san(desc)}_{direzione}_{_san(categoria)}_{imp_centesimi}.pdf"
    percorso_doc    = os.path.join(DOC_DIR, nome_reg)
    with open(percorso_doc, "wb") as f:
        f.write(pdf_bytes)
    cartella_pdf = os.path.join(os.getcwd(), "Fatture_GMail")
    if not os.path.exists(cartella_pdf):
        os.makedirs(cartella_pdf)
    azienda_safe  = re.sub(r'[\\/*?:"<>|]', "-", azienda).strip()
    fattura_safe  = re.sub(r'[\\/*?:"<>|]', "-", str(fattura or "mancante")).strip()
    nome_fattura  = f"{data_oggi.strftime('%d-%m-%Y')}_{azienda_safe}_fatt_{fattura_safe}.pdf"
    shutil.copy2(percorso_doc, os.path.join(cartella_pdf, nome_fattura))
    try:
        with open(REGISTRY_FILE, 'r', encoding='utf-8') as rf:
            registry = json.load(rf)
    except Exception:
        registry = {}
    registry[nome_reg] = {
        "data_raw":           data_ggmmaaaa,
        "categoria_esatta":   categoria,
        "descrizione_esatta": desc_spesa,
        "importo_raw":        imp_centesimi,
        "tipo_esatto":        direzione,
        "timestamp":          datetime.now().isoformat()
    }
    with open(REGISTRY_FILE, 'w', encoding='utf-8') as rf:
        json.dump(registry, rf, indent=4, ensure_ascii=False)
    self.spese.setdefault(data_oggi, []).append(SpesaEntry.nuova(categoria, desc_spesa, importo, direzione))
    self.save_db()
    self.after(0, self.refresh_gui)
    with open(LOG_IMPORTAZIONI, "a", encoding="utf-8") as log:
        log.write(
            f"{datetime.now().strftime('%d/%m/%Y %H:%M'):<17} | {'WEB-PDF':<8} | "
            f"{data_oggi.strftime('%d/%m/%Y'):<10} | {desc_spesa:<50} | "
            f"{_app._fmt_it(abs(importo)):>10} € | {direzione:<7} | {categoria}\n"
        )
    return {
        "ok":        True,
        "azienda":   azienda,
        "importo":   importo,
        "direzione": direzione,
        "categoria": categoria,
        "desc":      desc_spesa,
        "data":      data_oggi.strftime("%d/%m/%Y")
    }

def ricalcola_operazioni_web(self):
    contatore = 0
    categoria_target = "Zona @Web/Bank" 
    for entries in self.spese.values():
        for e in entries:
            if e[0] == categoria_target:
                contatore += 1
    self.operazioni_scaricate_sessione = contatore
    contatore_pdf = 0
    path_pdf = os.path.join(os.getcwd(), "Fatture_GMail")
    if os.path.exists(path_pdf):
        contatore_pdf = len([f for f in os.listdir(path_pdf) if f.lower().endswith('.pdf')])
    def applica_stato_visivo():
        if hasattr(self, 'lbl_sync_count_widget') and self.lbl_sync_count_widget.winfo_exists():
            try:
                self.lbl_sync_count_widget.config(text=f" Sync: {self.operazioni_scaricate_sessione}")
                if self.operazioni_scaricate_sessione > 0 or contatore_pdf > 0:
                    colore_stato = self.COLOR_RED
                else:
                    colore_stato = self.COLOR_GREEN
                if hasattr(self, 'btn_open_pdf_folder'):
                    self.btn_open_pdf_folder.config(foreground=colore_stato)
                self.lbl_sync_count_widget.config(foreground=colore_stato)
            except:
                pass
    if hasattr(self, 'lbl_sync_count_widget') and self.lbl_sync_count_widget.winfo_exists():
        applica_stato_visivo()
    else:
        self.after(200, applica_stato_visivo)
 

def notifica_modifica_web(self):
    import __main__ as _app
    UDP_PORT_1 = _app.UDP_PORT_1
    UDP_PORT_2 = _app.UDP_PORT_2
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        messaggio = f"REFRESH_NOW|{self.SESSION_ID}".encode('utf-8')
        for porta in [UDP_PORT_1, UDP_PORT_2]:
            sock.sendto(messaggio, ('255.255.255.255', porta))
        sock.close()
    except Exception as e:
        print(f"Errore invio: {e}")

def pianifica_sincro_web(self):
    import __main__ as _app
    SYNC_INT_MIN = _app.SYNC_INT_MIN
    from datetime import datetime
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Avvio sincronizzazione web automatica...")
        threading.Thread(target=self._esegui_sincro_thread, daemon=True).start()
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Errore durante il trigger della sincronizzazione: {e}")
    SYNC_INTERVALLO_MS = SYNC_INT_MIN * 60 * 1000
    self.after(SYNC_INTERVALLO_MS, self.pianifica_sincro_web)
