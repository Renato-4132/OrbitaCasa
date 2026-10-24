#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import html
import threading

_LOCK = threading.Lock()
MAX_DOMANDA = 2000
MAX_STORICO = 8
MAX_TESTO_STORICO = 3000
MAX_FILE = 5
MAX_BYTES_TOT = 15 * 1024 * 1024
MAX_CHARS_TESTO = 200000
_EXT_MIME = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
             ".webp": "image/webp", ".heic": "image/heic", ".heif": "image/heif"}
_EXT_TESTO = {".txt", ".csv", ".tsv", ".md", ".json", ".log", ".xml"}

_REGOLE = """REGOLE DI RISPOSTA:
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


def _pulisci_storico(raw):
    righe = []
    if not isinstance(raw, list):
        return righe
    for m in raw[-MAX_STORICO:]:
        if not isinstance(m, dict):
            continue
        testo = str(m.get("testo", "")).strip()[:MAX_TESTO_STORICO]
        if not testo:
            continue
        righe.append(("TU: " if m.get("ruolo") == "tu" else "GEMINI: ") + testo)
    return righe


def _testo_docx(data):
    import io
    import zipfile
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if z.getinfo("word/document.xml").file_size > 30 * 1024 * 1024:
            raise ValueError("documento troppo grande")
        xml = z.read("word/document.xml").decode("utf-8", "replace")
    xml = re.sub(r"</w:p>", "\n", xml)
    xml = re.sub(r"<[^>]+>", "", xml)
    return html.unescape(xml)


def _prepara_allegati(files):
    binari, testi = [], []
    if not files:
        return binari, testi, None
    if len(files) > MAX_FILE:
        return [], [], f"massimo {MAX_FILE} file per domanda."
    if sum(len(f[2]) for f in files) > MAX_BYTES_TOT:
        return [], [], "gli allegati superano i 15 MB in totale."
    for nome, _mime, data in files:
        nome = os.path.basename(str(nome or "file")).strip()[:80] or "file"
        ext = os.path.splitext(nome)[1].lower()
        if not data:
            continue
        if ext in _EXT_MIME:
            binari.append((nome, _EXT_MIME[ext], data))
        elif ext in _EXT_TESTO:
            testi.append((nome, data.decode("utf-8", "replace")[:MAX_CHARS_TESTO]))
        elif ext == ".docx":
            try:
                testi.append((nome, _testo_docx(data)[:MAX_CHARS_TESTO]))
            except Exception:
                return [], [], f"impossibile leggere {nome}."
        else:
            return [], [], f"formato non supportato: {nome} (accettati pdf, png, jpg, webp, heic, txt, csv, md, json, docx)."
    return binari, testi, None


def chiedi_ia_web_risposta(self, dati, files=None):
    import __main__ as _app
    from moduli.chiedi_ia import _costruisci_contesto_database
    API_KEY = _app.API_KEY
    GEMINI = _app.GEMINI
    genai_client = _app.genai_client
    types = _app.types
    _fmt_it = _app._fmt_it
    nome_app = os.path.basename(_app.PATH_LOCALE)

    binari, testi, err_all = _prepara_allegati(files)
    if err_all:
        return {"errore": err_all}, 400
    domanda = str((dati or {}).get("domanda", "")).strip()[:MAX_DOMANDA]
    if not domanda and (binari or testi):
        domanda = "Analizza i file allegati e riassumi il contenuto."
    if not domanda:
        return {"errore": "scrivi prima una domanda."}, 400
    if not API_KEY:
        return {"errore": "chiave api gemini non configurata. impostala dalla sezione impostazioni dell'app."}, 400
    if not _LOCK.acquire(blocking=False):
        return {"errore": "attendi la risposta precedente..."}, 429
    try:
        try:
            contesto = _costruisci_contesto_database(self, _app, _fmt_it)
        except Exception as err:
            return {"errore": f"errore nella lettura dei dati del database: {err}"}, 500
        cronologia = _pulisci_storico((dati or {}).get("storico"))
        cronologia_txt = ""
        if cronologia:
            cronologia_txt = "CONVERSAZIONE PRECEDENTE (per mantenere il contesto):\n" + "\n".join(cronologia) + "\n\n"
        if binari or testi:
            intro = ("Rispondi sulla base dei dati del database forniti sotto e dei file allegati dall'utente. "
                     "Se un dato richiesto non è disponibile né nel contesto né negli allegati, dillo chiaramente "
                     "invece di inventare numeri.\n\n")
            blocco_all = "FILE ALLEGATI DALL'UTENTE: " + ", ".join([b[0] for b in binari] + [t[0] for t in testi]) + "\n"
            for nome_t, testo_t in testi:
                blocco_all += f"\n--- {nome_t} ---\n{testo_t}\n--- fine {nome_t} ---\n"
            blocco_all += "\n"
        else:
            intro = ("Rispondi ESCLUSIVAMENTE sulla base dei dati del database forniti sotto. Se un dato\n"
                     "richiesto non è disponibile nel contesto, dillo chiaramente invece di inventare numeri.\n\n")
            blocco_all = ""
        prompt = (
            f"Sei un assistente esperto di finanza personale integrato nell'app {nome_app}.\n"
            + intro +
            "DATI DEL DATABASE (spese, conti, trasferimenti tra conti, e tutti i moduli collegati: veicoli,\n"
            "immobili, fondo pensione, fondo risparmio, spese pianificate, fairshare, utenze, studio,\n"
            "promemoria, rubrica, automazioni — se una sezione non compare qui sotto significa che quel\n"
            "modulo non ha ancora dati registrati):\n"
            f"{contesto}\n\n{blocco_all}{cronologia_txt}DOMANDA DELL'UTENTE:\n{domanda}\n\n{_REGOLE}"
        )
        try:
            client = genai_client.Client(api_key=API_KEY)
            parti = [types.Part.from_bytes(data=d, mime_type=m) for _n, m, d in binari]
            response = client.models.generate_content(model=GEMINI, contents=(parti + [prompt]) if parti else prompt)
            risposta = response.text if response.text else "Nessuna risposta generata."
        except Exception as err:
            testo_err = str(err)
            if "RESOURCE_EXHAUSTED" in testo_err or "429" in testo_err:
                if "PerDay" in testo_err:
                    m_quota = re.search(r"quotaValue\W+(\d+)", testo_err)
                    dettaglio = f" ({m_quota.group(1)} richieste/giorno)" if m_quota else ""
                    risposta = (f"quota giornaliera gratuita di gemini esaurita{dettaglio} per il modello {GEMINI}. "
                                "riprova domani, oppure attiva la fatturazione sulla tua chiave API su ai.google.dev "
                                "per aumentare il limite.")
                else:
                    risposta = ("hai fatto troppe richieste in poco tempo (limite di gemini per minuto raggiunto). "
                                "attendi qualche secondo e riprova.")
            else:
                risposta = f"ERRORE API GEMINI:\n{testo_err}"
        return {"risposta": risposta}, 200
    finally:
        _LOCK.release()


def pagina_chiedi_ia_web(self):
    import datetime
    return _PAGINA.replace("__ANNO__", str(datetime.date.today().year))


_PAGINA = r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>🤖 Chiedi al Database</title>
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
        --border:rgba(255,255,255,0.07); --gold:#c9a84c; --blue:#63a0f0; --red:#e05a5a;
        --text:#e8e8e8; --text-dim:#555; --text-mid:#888; --radius-lg:18px;
    }
    :root.light {
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --gold:#b8902a; --blue:#3d7fd4; --red:#cc3333;
        --text:#1a1a1a; --text-dim:#999; --text-mid:#555;
    }
    * { box-sizing:border-box; margin:0; padding:0; }
    body { font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text); min-height:100vh; transition:background 0.3s,color 0.3s; }
    header { padding:14px 16px 12px; display:flex; align-items:center; justify-content:center; border-bottom:1px solid var(--border); background:rgba(5,5,5,0.95); backdrop-filter:blur(20px); position:sticky; top:0; z-index:100; }
    :root.light header { background:rgba(245,245,240,0.95); }
    .hbtn { position:absolute; top:50%; transform:translateY(-50%); background:var(--surface3); border:1px solid var(--border); color:var(--gold); min-width:36px; height:36px; padding:0 10px; border-radius:10px; font-size:1em; cursor:pointer; display:flex; align-items:center; justify-content:center; text-decoration:none; font-family:inherit; }
    .hbtn.l { left:14px; }
    .hbtn.r { right:14px; }
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
    main { padding:14px 14px 175px; max-width:720px; margin:0 auto; }
    .vuoto { text-align:center; color:var(--text-mid); padding:30px 10px 10px; font-size:0.92em; line-height:1.5; }
    .chips { display:flex; flex-direction:column; gap:8px; margin-top:14px; }
    .chip { background:var(--surface); border:1px solid rgba(255,255,255,0.2); color:var(--text-mid); border-radius:14px; padding:12px 14px; font-family:inherit; font-size:0.9em; text-align:left; cursor:pointer; }    .chip { background:var(--surface); border:1px solid rgba(255,255,255,0.2); color:var(--text-mid); border-radius:14px; padding:12px 14px; font-family:inherit; font-size:0.9em; text-align:left; cursor:pointer; }
    :root.light .chip { border-color:var(--border); }
    .chip:hover { color:var(--text); background:var(--surface2); }
    .msg { margin:10px 0; padding:11px 14px; border-radius:16px; font-size:0.95em; line-height:1.5; white-space:pre-wrap; word-wrap:break-word; max-width:92%; }
    .msg.tu { margin-left:auto; background:rgba(99,160,240,0.14); border:1px solid rgba(99,160,240,0.35); }
    .msg.ia { margin-right:auto; background:var(--surface2); border:1px solid var(--border); }
    .msg.err { margin-right:auto; background:rgba(224,90,90,0.1); border:1px solid rgba(224,90,90,0.4); color:var(--red); }
    .msg.att { margin-right:auto; color:var(--text-mid); font-style:italic; background:transparent; border:none; padding-left:4px; }
    .barra { position:fixed; left:0; right:0; bottom:0; background:var(--bg); border-top:1px solid var(--border); padding:10px 12px calc(10px + env(safe-area-inset-bottom, 0px)); }
    .barra-in { max-width:720px; margin:0 auto; display:flex; flex-wrap:wrap; gap:8px; align-items:center; }
    textarea { order:-1; flex:1 1 100%; min-width:0; resize:none; max-height:140px; background:var(--surface); color:var(--text); border:1px solid var(--border); border-radius:14px; padding:11px 14px; font-family:inherit; font-size:1em; line-height:1.4; outline:none; }
    textarea:focus { border-color:var(--blue); }
    #clip { margin-left:auto; }
    .invia { flex-shrink:0; background:var(--blue); color:#fff; border:none; border-radius:14px; height:44px; padding:0 18px; font-family:inherit; font-weight:700; font-size:1em; cursor:pointer; }
    .invia:disabled { opacity:0.5; cursor:default; }
    .clip { background:var(--surface3); border:1px solid var(--border); color:var(--text-mid); border-radius:14px; height:44px; width:44px; font-size:1.1em; cursor:pointer; flex-shrink:0; }
    .alleg { max-width:720px; margin:0 auto 8px; display:none; flex-wrap:wrap; gap:6px; }
    .alleg span { background:var(--surface2); border:1px solid var(--border); border-radius:10px; padding:4px 8px; font-size:0.8em; color:var(--text-mid); }
    .alleg b { cursor:pointer; margin-left:6px; color:var(--red); }
    .nuova { display:block; margin:0 auto 8px; max-width:720px; background:none; border:none; color:var(--text-dim); font-family:inherit; font-size:0.8em; cursor:pointer; text-decoration:underline; }
</style>
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
    <div class="header-title">🤖 Chiedi al Database</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main id="chat">
    <div class="vuoto" id="vuoto">
        Fai una domanda sui tuoi dati: spese, conti, scadenze, utenze, veicoli e altro.
        <div class="chips">
            <button class="chip">Quanto ho speso questo mese?</button>
            <button class="chip">Confronta le uscite di questo mese con quelle del mese scorso</button>
            <button class="chip">Quali sono le categorie dove spendo di più quest'anno?</button>
        </div>
    </div>
</main>
<div class="barra">
    <button class="nuova" id="nuova" style="display:none">Nuova conversazione</button>
    <div class="alleg" id="alleg"></div>
    <div class="barra-in">
        <button class="clip" id="clip" title="Allega documento">📎</button>
        <button class="clip" id="foto" title="Allega foto">🖼️</button>
        <input type="file" id="file" multiple hidden accept=".pdf,.txt,.csv,.tsv,.md,.json,.log,.xml,.docx">
        <input type="file" id="fileFoto" multiple hidden accept="image/*">
        <textarea id="domanda" rows="1" maxlength="2000" placeholder="Scrivi una domanda..."></textarea>
        <button class="invia" id="invia">Invia</button>
    </div>
</div>
<script>
    var storico = [];
    var allegati = [];
    var MAX_FILE = 5, MAX_BYTES = 15 * 1024 * 1024;
    var inCorso = false;
    var chat = document.getElementById('chat');
    var campo = document.getElementById('domanda');
    var btn = document.getElementById('invia');

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
    document.addEventListener('DOMContentLoaded', function() { applyTheme(localStorage.getItem('theme') || 'dark'); });
    function giu() { window.scrollTo(0, document.body.scrollHeight); }
    function bolla(classe, testo) {
        var d = document.createElement('div');
        d.className = 'msg ' + classe;
        d.textContent = testo;
        chat.appendChild(d);
        giu();
        return d;
    }
    function adatta() {
        campo.style.height = 'auto';
        campo.style.height = Math.min(campo.scrollHeight, 140) + 'px';
    }
    campo.addEventListener('input', adatta);
    campo.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); invia(); }
    });
    btn.onclick = invia;
    var fileIn = document.getElementById('file');
    var fotoIn = document.getElementById('fileFoto');
    document.getElementById('clip').onclick = function() { fileIn.click(); };
    document.getElementById('foto').onclick = function() { fotoIn.click(); };
    function aggiungiFile(inp) {
        for (var i = 0; i < inp.files.length; i++) allegati.push(inp.files[i]);
        inp.value = '';
        var tot = allegati.reduce(function(a, f) { return a + f.size; }, 0);
        if (allegati.length > MAX_FILE || tot > MAX_BYTES) {
            allegati = [];
            alert('Massimo ' + MAX_FILE + ' file e 15 MB in totale per domanda.');
        }
        mostraAllegati();
    }
    fileIn.onchange = function() { aggiungiFile(fileIn); };
    fotoIn.onchange = function() { aggiungiFile(fotoIn); };
    function mostraAllegati() {
        var box = document.getElementById('alleg');
        box.innerHTML = '';
        allegati.forEach(function(f, i) {
            var s = document.createElement('span');
            s.textContent = f.name;
            var x = document.createElement('b');
            x.textContent = '✕';
            x.onclick = function() { allegati.splice(i, 1); mostraAllegati(); };
            s.appendChild(x);
            box.appendChild(s);
        });
        box.style.display = allegati.length ? 'flex' : 'none';
    }
    document.querySelectorAll('.chip').forEach(function(c) {
        c.onclick = function() { campo.value = c.textContent; invia(); };
    });
    document.getElementById('nuova').onclick = function() {
        if (inCorso) return;
        storico = [];
        chat.querySelectorAll('.msg').forEach(function(m) { m.remove(); });
        document.getElementById('vuoto').style.display = '';
        this.style.display = 'none';
    };

    async function invia() {
        var testo = campo.value.trim();
        if ((!testo && !allegati.length) || inCorso) return;
        var nomi = allegati.map(function(f) { return '📎 ' + f.name; }).join('\n');
        var fd = new FormData();
        fd.append('domanda', testo);
        fd.append('storico', JSON.stringify(storico));
        allegati.forEach(function(f) { fd.append('files', f, f.name); });
        allegati = [];
        mostraAllegati();
        inCorso = true;
        btn.disabled = true;
        document.getElementById('vuoto').style.display = 'none';
        document.getElementById('nuova').style.display = 'block';
        campo.value = '';
        adatta();
        bolla('tu', (testo ? testo + (nomi ? '\n' : '') : '') + nomi);
        var attesa = bolla('att', 'Gemini sta pensando...');
        try {
            var r = await fetch('/api/chiedi_ia', {
                method: 'POST',
                body: fd
            });
            var tipo = r.headers.get('content-type') || '';
            if (r.redirected || tipo.indexOf('application/json') < 0) {
                window.location.href = '/login';
                return;
            }
            var j = await r.json();
            attesa.remove();
            if (j.risposta) {
                bolla('ia', j.risposta);
                storico.push({ruolo: 'tu', testo: testo || nomi});
                storico.push({ruolo: 'gemini', testo: j.risposta});
                if (storico.length > 8) storico = storico.slice(-8);
            } else {
                bolla('err', j.errore || 'Errore sconosciuto.');
            }
        } catch (e) {
            attesa.remove();
            bolla('err', 'Connessione non riuscita: ' + e);
        } finally {
            inCorso = false;
            btn.disabled = false;
            campo.focus();
        }
    }
</script>
</body>
</html>
"""
