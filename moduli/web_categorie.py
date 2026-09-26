#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
from moduli.modello_spesa import SpesaEntry


# Html Gestione Categorie Web
def add_categoria_web(self, params):
    nome = params.get("nome_categoria", [""])[0].strip()
    tipo = params.get("tipo_categoria", ["Uscita"])[0]
    if not nome or nome in self.categorie or nome == self.CATEGORIA_RIMOSSA:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore: Categoria '{nome}' già esistente o non valida.")
        return self.html_gestione_categorie()
    self.categorie.append(nome)
    self.categorie_tipi[nome] = tipo
    self.categorie.sort()
    budget_val = params.get("budget_categoria", ["0"])[0].strip().replace(",", ".")
    try:
        budget_val = float(budget_val)
    except ValueError:
        budget_val = 0.0
    if budget_val > 0:
        self.budget_categorie[nome] = budget_val
    elif nome in self.budget_categorie:
        del self.budget_categorie[nome]
    budget_anno_val = params.get("budget_annuale_categoria", ["0"])[0].strip().replace(",", ".")
    try:
        budget_anno_val = float(budget_anno_val)
    except ValueError:
        budget_anno_val = 0.0
    if budget_anno_val > 0:
        self.budget_annuale_categorie[nome] = budget_anno_val
    elif nome in self.budget_annuale_categorie:
        del self.budget_annuale_categorie[nome]
    self.save_db()
    self.refresh_categorie_web()
    

def modifica_categoria_web(self, params):
    old_nome = params.get("categoria_selezionata", [""])[0]
    new_nome = params.get("nuovo_nome", [""])[0].strip()
    nuovo_tipo = params.get("nuovo_tipo", ["Uscita"])[0]
    if not old_nome or old_nome == "Generica":
        return
    if not new_nome:
        new_nome = old_nome
    if new_nome == old_nome:
        self.categorie_tipi[new_nome] = nuovo_tipo
    else:
        if new_nome in self.categorie:
            return
        idx = self.categorie.index(old_nome)
        self.categorie[idx] = new_nome
        self.categorie_tipi[new_nome] = nuovo_tipo
        self.categorie_tipi.pop(old_nome, None)
        for d in self.spese:
            new_entries = []
            for entry in self.spese[d]:
                if entry[0] == old_nome:
                    entry = entry.sostituisci(categoria=new_nome) if isinstance(entry, SpesaEntry) else (new_nome,) + entry[1:]
                new_entries.append(entry)
            self.spese[d] = new_entries
        self.categorie.sort()
    budget_val = params.get("budget_categoria", ["0"])[0].strip().replace(",", ".")
    try:
        budget_val = float(budget_val)
    except ValueError:
        budget_val = 0.0
    nome_finale = new_nome
    if budget_val > 0:
        self.budget_categorie[nome_finale] = budget_val
    elif nome_finale in self.budget_categorie:
        del self.budget_categorie[nome_finale]
    if new_nome != old_nome and old_nome in self.budget_categorie:
        del self.budget_categorie[old_nome]
    budget_anno_val = params.get("budget_annuale_categoria", ["0"])[0].strip().replace(",", ".")
    try:
        budget_anno_val = float(budget_anno_val)
    except ValueError:
        budget_anno_val = 0.0
    if budget_anno_val > 0:
        self.budget_annuale_categorie[nome_finale] = budget_anno_val
    elif nome_finale in self.budget_annuale_categorie:
        del self.budget_annuale_categorie[nome_finale]
    if new_nome != old_nome and old_nome in self.budget_annuale_categorie:
        del self.budget_annuale_categorie[old_nome]
    self.save_db()
    self.refresh_categorie_web()

def cancella_categoria_web(self, params):
    cat_da_cancellare = params.get("categoria_selezionata", [""])[0]
    if not cat_da_cancellare or cat_da_cancellare not in self.categorie or cat_da_cancellare == "Generica":
        return
    self.categorie.remove(cat_da_cancellare)
    self.categorie_tipi.pop(cat_da_cancellare, None)
    self.budget_categorie.pop(cat_da_cancellare, None)
    self.budget_annuale_categorie.pop(cat_da_cancellare, None)
    for d in self.spese:
        new_entries = []
        for entry in self.spese[d]:
            if entry[0] == cat_da_cancellare:
                entry = entry.sostituisci(categoria=self.CATEGORIA_RIMOSSA) if isinstance(entry, SpesaEntry) else (self.CATEGORIA_RIMOSSA,) + entry[1:]
            new_entries.append(entry)
        self.spese[d] = new_entries
    self.save_db()
    self.refresh_categorie_web()

def refresh_categorie_web(self):
    self.after(100, self._esegui_aggiornamento_gui)
                    

# Html Gestione Categorie Web             
def html_gestione_categorie(self):
    import datetime
    categorie_tipi_js = str(self.categorie_tipi).replace("'", '"')
    categorie_options = "".join(
        f"<option value='{cat}' data-budget='{self.budget_categorie.get(cat, 0):.2f}' data-budget-annuo='{self.budget_annuale_categorie.get(cat, 0):.2f}'>{cat}</option>"
        for cat in sorted(self.categorie, key=lambda x: x.strip().lower())
    )
    anno_corrente = datetime.datetime.now().year
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>⚙️ Gestione Categorie</title>
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
        border-radius:var(--radius-lg); margin-bottom:8px; position:relative;
    }}
    .sec-card::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        border-radius:var(--radius-lg) var(--radius-lg) 0 0; z-index:1;
    }}
    .sec-card.add::before {{ background:linear-gradient(90deg, transparent, var(--green), transparent); }}
    .sec-card.edit::before {{ background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent); }}
    .sec-card.del::before {{ background:linear-gradient(90deg, transparent, var(--red), transparent); }}
    details summary {{
        list-style:none; cursor:pointer; padding:15px 18px;
        display:flex; align-items:center; gap:10px;
        font-family:'DM Sans',sans-serif; font-size:0.92em; font-weight:700;
        border-radius:var(--radius-lg); transition:background 0.15s; user-select:none;
    }}
    details[open] summary {{ border-radius:var(--radius-lg) var(--radius-lg) 0 0; }}
    details summary::-webkit-details-marker {{ display:none; }}
    details summary:hover {{ background:var(--surface2); }}
    .sum-arrow {{ font-size:0.7em; color:var(--text-dim); margin-left:auto; transition:transform 0.22s; }}
    details[open] .sum-arrow {{ transform:rotate(90deg); }}
    .sum-add {{ color:var(--green); }}
    .sum-edit {{ color:var(--gold); }}
    .sum-del {{ color:var(--red); }}
    .form-body {{ padding:4px 18px 20px; border-top:1px solid var(--border); }}
    .form-group {{ margin-top:13px; }}
    label {{
        display:block; font-size:0.65em; font-weight:700; color:var(--text-dim);
        letter-spacing:1.8px; text-transform:uppercase; margin-bottom:6px;
    }}
    input[type="text"], select {{
        width:100%; padding:10px 13px; background:var(--surface2);
        border:1px solid var(--border); border-radius:9px; color:var(--text);
        font-family:'DM Sans',sans-serif; font-size:0.92em;
        transition:all 0.2s; outline:none; -webkit-appearance:none; appearance:none;
    }}
    input[type="text"]:focus, select:focus {{
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
    .btn-submit {{
        width:100%; padding:12px 13px; margin-top:16px; border:none; border-radius:9px;
        font-family:'DM Sans',sans-serif; font-size:0.92em; font-weight:700;
        line-height:1.5; cursor:pointer; transition:all 0.2s;
    }}
    .btn-submit:hover {{ transform:translateY(-1px); }}
    .btn-add {{ background:linear-gradient(135deg, var(--green), #2d7a56); color:#000; }}
    .btn-add:hover {{ box-shadow:0 6px 20px rgba(76,175,130,0.25); }}
    .btn-edit {{ background:linear-gradient(135deg, var(--gold), #8a6820); color:#000; }}
    .btn-edit:hover {{ box-shadow:0 6px 20px rgba(201,168,76,0.25); }}
    .btn-del {{ background:linear-gradient(135deg, var(--red), #9c2d2d); color:#fff; }}
    .btn-del:hover {{ box-shadow:0 6px 20px rgba(224,90,90,0.25); }}
    .btn-home {{
        display:block; text-align:center; padding:12px 13px; margin-top:10px;
        background:var(--surface); border:1px solid var(--border);
        color:var(--text-mid); border-radius:9px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.88em;
        line-height:1.5; transition:all 0.2s;
    }}
    .btn-home:hover {{ border-color:var(--border-active); color:var(--text); }}
</style>
<script>
    const CategorieTipi = {categorie_tipi_js};
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
    function aggiornaTipoCategoria() {{
        const sel = document.getElementById("categoria_modifica");
        const tipo = document.getElementById("nuovo_tipo");
        tipo.value = (sel.value && CategorieTipi[sel.value]) ? CategorieTipi[sel.value] : "Uscita";
        const opt = sel.options[sel.selectedIndex];
        const budgetField = document.getElementById("budget_modifica");
        if (budgetField && opt) {{
            const b = parseFloat(opt.getAttribute("data-budget")) || 0;
            budgetField.value = b > 0 ? b.toFixed(2) : "";
        }}
        const budgetAnnoField = document.getElementById("budget_annuo_modifica");
        if (budgetAnnoField && opt) {{
            const ba = parseFloat(opt.getAttribute("data-budget-annuo")) || 0;
            budgetAnnoField.value = ba > 0 ? ba.toFixed(2) : "";
        }}
    }}
    document.addEventListener("DOMContentLoaded", function() {{
        applyTheme(localStorage.getItem('theme') || 'dark');
        const cm = document.getElementById("categoria_modifica");
        if (cm) {{
            cm.addEventListener("change", aggiornaTipoCategoria);
            if (cm.value) aggiornaTipoCategoria();
        }}
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
    <div class="header-title">⚙️ Gestione Categorie</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="sec-card add">
        <details>
            <summary>
                <span class="sum-add">➕</span>
                <span class="sum-add">Aggiungi Categoria</span>
                <span class="sum-arrow">▶</span>
            </summary>
            <div class="form-body">
                <form action="/salva_categoria" method="POST">
                    <input type="hidden" name="operazione" value="aggiungi">
                    <div class="form-group">
                        <label>Nome Categoria</label>
                        <input type="text" name="nome_categoria" required placeholder="es: Abbonamenti">
                    </div>
                    <div class="form-group">
                        <label>Tipo</label>
                        <select name="tipo_categoria">
                            <option value="Uscita">Uscita</option>
                            <option value="Entrata">Entrata</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Budget €/mese (opzionale)</label>
                        <input type="text" name="budget_categoria" placeholder="es: 500.00" inputmode="decimal">
                    </div>
                    <div class="form-group">
                        <label>Budget €/anno (opzionale)</label>
                        <input type="text" name="budget_annuale_categoria" placeholder="es: 6000.00" inputmode="decimal">
                    </div>
                    <button type="submit" class="btn-submit btn-add">➕ Aggiungi</button>
                </form>
            </div>
        </details>
    </div>
    <div class="sec-card edit">
        <details>
            <summary>
                <span class="sum-edit">✏️</span>
                <span class="sum-edit">Modifica Categoria</span>
                <span class="sum-arrow">▶</span>
            </summary>
            <div class="form-body">
                <form action="/salva_categoria" method="POST">
                    <input type="hidden" name="operazione" value="modifica">
                    <div class="form-group">
                        <label>Seleziona Categoria</label>
                        <select name="categoria_selezionata" id="categoria_modifica" required>
                            {categorie_options}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Nuovo Nome (opzionale)</label>
                        <input type="text" name="nuovo_nome" placeholder="Lascia vuoto per non modificare">
                    </div>
                    <div class="form-group">
                        <label>Nuovo Tipo</label>
                        <select name="nuovo_tipo" id="nuovo_tipo">
                            <option value="Uscita">Uscita</option>
                            <option value="Entrata">Entrata</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Budget €/mese (0 per rimuovere)</label>
                        <input type="text" name="budget_categoria" id="budget_modifica" placeholder="es: 500.00" inputmode="decimal">
                    </div>
                    <div class="form-group">
                        <label>Budget €/anno (0 per rimuovere)</label>
                        <input type="text" name="budget_annuale_categoria" id="budget_annuo_modifica" placeholder="es: 6000.00" inputmode="decimal">
                    </div>
                    <button type="submit" class="btn-submit btn-edit">✏️ Modifica</button>
                </form>
            </div>
        </details>
    </div>
    <div class="sec-card del">
        <details>
            <summary>
                <span class="sum-del">❌</span>
                <span class="sum-del">Cancella Categoria</span>
                <span class="sum-arrow">▶</span>
            </summary>
            <div class="form-body">
                <form action="/cancella_categoria" method="POST">
                    <div class="form-group">
                        <label>Seleziona Categoria da eliminare</label>
                        <select name="categoria_selezionata" required>
                            {categorie_options}
                        </select>
                    </div>
                    <button type="submit" class="btn-submit btn-del">❌ Cancella</button>
                </form>
            </div>
        </details>
    </div>
    <a href="/" class="btn-home">🏠 Torna alla Home</a>
</main>
</body>
</html>"""
