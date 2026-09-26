#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import html
import datetime
from moduli.modello_spesa import campo
from moduli.mappa_conti_trasferimenti import e_trasferimento_virtuale
from moduli.web_utils import _fmt_it, _saldo_effettivo_web


# Html Grafici Web
def get_dati_entrate_uscite_tutti_gli_anni_json(self, conto_filtro=None):
    totali_annuali = {}
    for giorno, voci in self.spese.items():
        try:
            anno = giorno.year
        except AttributeError:
            continue 
        if anno not in totali_annuali:
            totali_annuali[anno] = {'Entrate': 0.0, 'Uscite': 0.0}
        for voce in voci:
            if len(voce) < 4: continue
            if conto_filtro and campo(voce, "conto", "") != conto_filtro:
                continue
            raw_importo = voce[2]
            tipo = voce[3] 
            try:
                importo_str = str(raw_importo).strip().replace(',', '.')
                importo = float(importo_str)
            except (TypeError, ValueError):
                continue 
            if tipo == "Entrata":
                totali_annuali[anno]['Entrate'] += importo
            elif tipo == "Uscita":
                totali_annuali[anno]['Uscite'] += importo
    anni_ordinati = sorted(totali_annuali.keys()) 
    data_entrate = [totali_annuali[anno]['Entrate'] for anno in anni_ordinati]
    data_uscite = [totali_annuali[anno]['Uscite'] for anno in anni_ordinati]
    dati_json = {
        "labels": [str(anno) for anno in anni_ordinati],
        "datasets": [
            {
                "label": "Entrate",
                "data": data_entrate,
                "backgroundColor": "rgba(40, 167, 69, 0.7)"
            },
            {
                "label": "Uscite",
                "data": data_uscite,
                "backgroundColor": "rgba(220, 53, 69, 0.7)"
            }
        ]
    }
    return json.dumps(dati_json)

def get_dati_saldo_annuale_json(self, conto_filtro=None):
    saldo_per_anno = {} 
    for d, voci in self.spese.items():
        anno = d.year
        if anno not in saldo_per_anno:
            saldo_per_anno[anno] = 0.0
        for voce in voci:
            if conto_filtro and campo(voce, "conto", "") != conto_filtro:
                continue
            importo = float(voce[2]) 
            tipo = voce[3].strip().lower()
            if tipo == "entrata":
                saldo_per_anno[anno] += importo
            elif tipo == "uscita":
                saldo_per_anno[anno] -= importo
    if conto_filtro:
        import __main__ as _app
        PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
        try:
            with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
                _db_p = json.load(_pf)
        except Exception:
            _db_p = {"conti": [], "trasferimenti": []}
        conto_sel = next((c for c in _db_p.get("conti", []) if c.get("nome", "") == conto_filtro), None)
        if conto_sel is not None:
            for t in _db_p.get("trasferimenti", []):
                if e_trasferimento_virtuale(t):
                    continue
                try:
                    data_t = datetime.datetime.strptime(t["data"], "%d-%m-%Y").date()
                    imp = round(float(t.get("importo", 0)), 2)
                except Exception:
                    continue
                anno_t = data_t.year
                saldo_per_anno.setdefault(anno_t, 0.0)
                if t.get("da") == conto_sel.get("id"):
                    saldo_per_anno[anno_t] -= imp
                elif t.get("a") == conto_sel.get("id"):
                    saldo_per_anno[anno_t] += imp
    anni_ordinati = sorted(saldo_per_anno.keys())
    dati_json = {
        "labels": [str(anno) for anno in anni_ordinati],
        "datasets": [{
            "label": "Saldo Netto Annuale",
            "data": [saldo_per_anno[anno] for anno in anni_ordinati],
            "backgroundColor": ["#228B22" if saldo_per_anno[anno] >= 0 else "#c43b2e" for anno in anni_ordinati]
        }]
    }
    return json.dumps(dati_json)

def get_dati_entrate_uscite_json(self, conto_filtro=None):
    oggi = datetime.date.today()
    anno_corrente = oggi.year
    entrate_mensili = [0.0] * 12
    uscite_mensili = [0.0] * 12
    for data, entries in self.spese.items():
        if data.year == anno_corrente:
            mese_indice = data.month - 1  
            for entry in entries:
                if conto_filtro and campo(entry, "conto", "") != conto_filtro:
                    continue
                importo = entry[2]
                tipo = entry[3].strip() if len(entry) > 3 else 'Uscita'
                if tipo == 'Entrata':
                    entrate_mensili[mese_indice] += importo
                else: 
                    uscite_mensili[mese_indice] += importo
    mesi = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic']
    dati = {
        'labels': mesi,
        'datasets': [
            {'label': 'Entrate (€)', 'data': entrate_mensili, 'borderColor': 'rgba(75, 192, 192, 1)', 'backgroundColor': 'rgba(75, 192, 192, 0.5)'},
            {'label': 'Uscite (€)', 'data': uscite_mensili, 'borderColor': 'rgba(255, 99, 132, 1)', 'backgroundColor': 'rgba(255, 99, 132, 0.5)'}
        ]
    }
    return json.dumps(dati)

def get_dati_saldo_json(self, conto_filtro=None):
    oggi = datetime.date.today()
    anno_corrente = oggi.year
    saldo_mensile_netto = [0.0] * 12
    for data, entries in self.spese.items():
        if data.year == anno_corrente:
            mese_indice = data.month - 1
            for entry in entries:
                if conto_filtro and campo(entry, "conto", "") != conto_filtro:
                    continue
                importo = entry[2]
                tipo = entry[3].strip() if len(entry) > 3 else 'Uscita'

                if tipo == 'Entrata':
                    saldo_mensile_netto[mese_indice] += importo
                else:
                    saldo_mensile_netto[mese_indice] -= importo
    if conto_filtro:
        import __main__ as _app
        PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
        try:
            with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
                _db_p = json.load(_pf)
        except Exception:
            _db_p = {"conti": [], "trasferimenti": []}
        conto_sel = next((c for c in _db_p.get("conti", []) if c.get("nome", "") == conto_filtro), None)
        if conto_sel is not None:
            for t in _db_p.get("trasferimenti", []):
                if e_trasferimento_virtuale(t):
                    continue
                try:
                    data_t = datetime.datetime.strptime(t["data"], "%d-%m-%Y").date()
                    imp = round(float(t.get("importo", 0)), 2)
                except Exception:
                    continue
                if data_t.year != anno_corrente:
                    continue
                mese_indice_t = data_t.month - 1
                if t.get("da") == conto_sel.get("id"):
                    saldo_mensile_netto[mese_indice_t] -= imp
                elif t.get("a") == conto_sel.get("id"):
                    saldo_mensile_netto[mese_indice_t] += imp
    saldo_progressivo = []
    saldo_accumulato = 0.0
    for saldo_netto in saldo_mensile_netto:
        saldo_accumulato += saldo_netto
        saldo_progressivo.append(round(saldo_accumulato, 2))
    mesi = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic']
    dati = {
        'labels': mesi,
        'datasets': [{
            'label': 'Saldo Progressivo (€)',
            'data': saldo_progressivo,
            'fill': False,
            'borderColor': 'rgb(75, 192, 192)',
            'tension': 0.1
        }]
    }
    return json.dumps(dati)

# Portafoglio Bancario Web

_PORTAFOGLIO_TIPI = ["personale", "comune", "figli", "altro"]
_PORTAFOGLIO_MAX_CONTI = 10
_PORTAFOGLIO_TIPO_COLORI = {
    "personale": "#4A90D9",
    "comune":    "#50C878",
    "figli":     "#C45E00",
    "altro":     "#A78BFA",
}

def _carica_portafoglio_db_web(path):
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {
        "saldo_fisico": 0.0,
        "saldo_data":   datetime.date.today().strftime("%d-%m-%Y"),
        "storico_saldo": [],
        "conti": [],
        "trasferimenti": []
    }

def _salva_portafoglio_db_web(path, db):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)

def _nuovo_id_portafoglio_web(prefisso, lista):
    ids = {c.get("id", "") for c in lista}
    i = 1
    while f"{prefisso}{i}" in ids:
        i += 1
    return f"{prefisso}{i}"

def refresh_portafoglio_web(self):
    if hasattr(self, "_esegui_aggiornamento_gui"):
        self.after(100, self._esegui_aggiornamento_gui)
    try:
        if getattr(self, "_cruscotto_stato", 0) == 2 and hasattr(self, "aggiorna_conti_canvas"):
            self.after(100, self.aggiorna_conti_canvas)
    except Exception:
        pass
    try:
        if hasattr(self, "_saldo_refresh"):
            self.after(100, self._saldo_refresh)
        if hasattr(self, "_saldo_refresh_movimenti"):
            self.after(100, self._saldo_refresh_movimenti)
        if hasattr(self, "_saldo_refresh_conti"):
            self.after(100, self._saldo_refresh_conti)
        if hasattr(self, "_saldo_refresh_trasferimenti"):
            self.after(100, self._saldo_refresh_trasferimenti)
        if hasattr(self, "_saldo_refresh_storico"):
            self.after(100, self._saldo_refresh_storico)
    except Exception:
        pass

def salva_conto_web(self, params):
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    db = _carica_portafoglio_db_web(PORTAFOGLIO_BANCARIO)
    db.setdefault("conti", [])
    conto_id = params.get("conto_id", [""])[0].strip()
    nome = params.get("nome", [""])[0].strip()
    if not nome:
        return
    tipo = params.get("tipo", ["personale"])[0]
    if tipo not in _PORTAFOGLIO_TIPI:
        tipo = "altro"
    try:
        saldo_val = float(params.get("saldo", ["0"])[0].strip().replace(",", "."))
    except ValueError:
        saldo_val = 0.0
    principale = params.get("principale", [""])[0] == "1"
    iban = params.get("iban", [""])[0].strip()
    note = params.get("note", [""])[0].strip()[:20]
    nome_esiste = any(
        c.get("nome", "").lower() == nome.lower() and c.get("id") != conto_id
        for c in db["conti"]
    )
    if nome_esiste:
        return
    if principale:
        for c in db["conti"]:
            c["principale"] = False
    if conto_id:
        for c in db["conti"]:
            if c.get("id") == conto_id:
                c["nome"]       = nome
                c["tipo"]       = tipo
                c["saldo"]      = saldo_val
                c["principale"] = principale
                c["iban"]       = iban
                c["note"]       = note
                break
    else:
        if len(db["conti"]) >= _PORTAFOGLIO_MAX_CONTI:
            return f"Impossibile aggiungere oltre {_PORTAFOGLIO_MAX_CONTI} conti."
        db["conti"].append({
            "id":         _nuovo_id_portafoglio_web("c", db["conti"]),
            "nome":       nome,
            "tipo":       tipo,
            "saldo":      saldo_val,
            "principale": principale,
            "iban":       iban,
            "note":       note
        })
    _salva_portafoglio_db_web(PORTAFOGLIO_BANCARIO, db)
    self.refresh_portafoglio_web()

def elimina_conto_web(self, params):
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    db = _carica_portafoglio_db_web(PORTAFOGLIO_BANCARIO)
    conto_id = params.get("conto_id", [""])[0].strip()
    if not conto_id:
        return
    db["trasferimenti"] = [
        t for t in db.get("trasferimenti", [])
        if t.get("da") != conto_id and t.get("a") != conto_id
    ]
    db["conti"] = [c for c in db.get("conti", []) if c.get("id") != conto_id]
    _salva_portafoglio_db_web(PORTAFOGLIO_BANCARIO, db)
    self.refresh_portafoglio_web()

def salva_trasferimento_web(self, params):
    import __main__ as _app
    import uuid as _uuid
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    db = _carica_portafoglio_db_web(PORTAFOGLIO_BANCARIO)
    db.setdefault("trasferimenti", [])
    conti = db.get("conti", [])
    id_da_nome = {c.get("nome"): c.get("id") for c in conti}
    trasf_id = params.get("trasferimento_id", [""])[0].strip()
    data_str = params.get("data", [""])[0].strip()
    da_nome  = params.get("da", [""])[0]
    a_nome   = params.get("a", [""])[0]
    note     = params.get("note", [""])[0].strip()[:20]
    try:
        _d_check = datetime.datetime.strptime(data_str, "%d-%m-%Y").date()
    except Exception:
        return
    try:
        imp = float(params.get("importo", ["0"])[0].strip().replace(",", "."))
        if imp <= 0:
            return
    except ValueError:
        return
    da_id = id_da_nome.get(da_nome)
    a_id  = id_da_nome.get(a_nome)
    if not da_id or not a_id or da_id == a_id:
        return
    if trasf_id:
        vecchio = next((t for t in db["trasferimenti"] if t.get("id") == trasf_id), None)
        if vecchio:
            vecchio["data"]    = data_str
            vecchio["da"]      = da_id
            vecchio["a"]       = a_id
            vecchio["importo"] = round(imp, 2)
            vecchio["note"]    = note
        _salva_portafoglio_db_web(PORTAFOGLIO_BANCARIO, db)
        self.refresh_portafoglio_web()
        return
    ric_tipo = params.get("ricorrenza_tipo", ["Nessuna"])[0]
    if ric_tipo == "Nessuna":
        db["trasferimenti"].append({
            "id":      _nuovo_id_portafoglio_web("t", db["trasferimenti"]),
            "data":    data_str,
            "da":      da_id,
            "a":       a_id,
            "importo": round(imp, 2),
            "note":    note
        })
        _salva_portafoglio_db_web(PORTAFOGLIO_BANCARIO, db)
        self.refresh_portafoglio_web()
        return
    try:
        n = int(params.get("ricorrenza_n", ["1"])[0])
        if n <= 0 or n > 360:
            return
    except Exception:
        return
    try:
        from moduli.saldo_conto import _genera_date_ricorrenza_trasf
    except Exception:
        return
    date_list = _genera_date_ricorrenza_trasf(_d_check, ric_tipo, n)
    if not date_list:
        return
    ric_id = str(_uuid.uuid4())
    for i, d in enumerate(date_list, start=1):
        db["trasferimenti"].append({
            "id":                _nuovo_id_portafoglio_web("t", db["trasferimenti"]),
            "data":              d.strftime("%d-%m-%Y"),
            "da":                da_id,
            "a":                 a_id,
            "importo":           round(imp, 2),
            "note":              note,
            "id_ricorrenza":     ric_id,
            "ricorrenza_tipo":   ric_tipo,
            "ricorrenza_seq":    i,
            "ricorrenza_totale": n,
        })
    _salva_portafoglio_db_web(PORTAFOGLIO_BANCARIO, db)
    self.refresh_portafoglio_web()

def elimina_trasferimento_web(self, params):
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    db = _carica_portafoglio_db_web(PORTAFOGLIO_BANCARIO)
    trasf_id = params.get("trasferimento_id", [""])[0].strip()
    ambito   = params.get("ambito", ["singola"])[0]
    if not trasf_id:
        return
    vecchio = next((t for t in db.get("trasferimenti", []) if t.get("id") == trasf_id), None)
    if not vecchio:
        return
    ric_id = vecchio.get("id_ricorrenza")
    if ric_id and ambito == "serie":
        db["trasferimenti"] = [
            t for t in db.get("trasferimenti", []) if t.get("id_ricorrenza") != ric_id
        ]
    else:
        db["trasferimenti"] = [
            t for t in db.get("trasferimenti", []) if t.get("id") != trasf_id
        ]
    _salva_portafoglio_db_web(PORTAFOGLIO_BANCARIO, db)
    self.refresh_portafoglio_web()

def pagina_portafoglio_web(self):
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    db = _carica_portafoglio_db_web(PORTAFOGLIO_BANCARIO)
    conti = db.get("conti", [])
    trasf_tutti = db.get("trasferimenti", [])
    trasf = [t for t in trasf_tutti if not e_trasferimento_virtuale(t)]
    nome_da_id = {c.get("id"): c.get("nome", "?") for c in conti}
    TIPO_COLORI = _PORTAFOGLIO_TIPO_COLORI
    TIPI = _PORTAFOGLIO_TIPI

    totale_conti = sum(_saldo_effettivo_web(self, c, db) for c in conti)
    totale_abs = sum(abs(_saldo_effettivo_web(self, c, db)) for c in conti) or 1
    cards_html = ""
    barre_html = ""
    for c in conti:
        saldo_c = _saldo_effettivo_web(self, c, db)
        colore = "#E06C75" if saldo_c < 0 else TIPO_COLORI.get(c.get("tipo", "altro"), "#A78BFA")
        pct = max(4, round(abs(saldo_c) / totale_abs * 100, 1))
        star = " ⭐" if c.get("principale") else ""
        cards_html += f"""
        <div class="conto-card" style="background:{colore};">
            <div class="conto-card-nome">{html.escape(c.get('nome',''))}{star}</div>
            <div class="conto-card-saldo">€ {_fmt_it(saldo_c)}</div>
            <div class="conto-card-tipo">{html.escape(c.get('tipo','').capitalize())}</div>
        </div>"""
        barre_html += (f'<div style="background:{colore}; width:{pct}%;" '
                        f'title="{html.escape(c.get("nome",""))}: € {_fmt_it(saldo_c)}"></div>')
    if not conti:
        cards_html = ('<div style="color:var(--text-dim); padding:10px; font-size:0.85em;">'
                      'Nessun conto registrato. Vai al tab Conti per aggiungerne uno.</div>')
        barre_html = ""
    legenda_html = "".join(
        f'<div class="legenda-item"><span class="legenda-dot" style="background:{col};"></span>{tipo.capitalize()}</div>'
        for tipo, col in TIPO_COLORI.items()
    )

    conti_rows = ""
    for c in conti:
        saldo_c = _saldo_effettivo_web(self, c, db)
        colore = TIPO_COLORI.get(c.get("tipo", "altro"), "#A78BFA")
        star = "⭐" if c.get("principale") else ""
        conti_rows += f"""
        <tr>
            <td style="color:{colore}; font-weight:700;">{html.escape(c.get('nome',''))}</td>
            <td>{html.escape(c.get('tipo','').capitalize())}</td>
            <td style="text-align:right;">€ {_fmt_it(saldo_c)}</td>
            <td style="text-align:center;">{star}</td>
            <td>{html.escape(c.get('note','') or '')}</td>
        </tr>"""
    if not conti:
        conti_rows = ('<tr><td colspan="5" style="text-align:center; color:var(--text-dim); '
                      'padding:12px;">Nessun conto registrato</td></tr>')
    conti_options_modifica = "".join(
        f'<option value="{c.get("id")}" '
        f'data-nome="{html.escape(c.get("nome",""))}" '
        f'data-tipo="{c.get("tipo","personale")}" '
        f'data-saldo="{float(c.get("saldo",0) or 0):.2f}" '
        f'data-principale="{"1" if c.get("principale") else "0"}" '
        f'data-iban="{html.escape(c.get("iban","") or "")}" '
        f'data-note="{html.escape(c.get("note","") or "")}">'
        f'{html.escape(c.get("nome",""))}</option>'
        for c in conti
    )
    tipo_options = "".join(f'<option value="{t}">{t.capitalize()}</option>' for t in TIPI)
    nomi_conti_options = "".join(
        f'<option value="{html.escape(c.get("nome",""))}">{html.escape(c.get("nome",""))}</option>'
        for c in conti
    )

    def _key_data_t(t):
        try:
            return datetime.datetime.strptime(t.get("data", ""), "%d-%m-%Y").date()
        except Exception:
            return datetime.date.min
    trasf_ord = sorted(trasf, key=_key_data_t, reverse=True)
    trasf_rows = ""
    for t in trasf_ord:
        ric_badge = (f' 🔁 {t.get("ricorrenza_seq","?")}/{t.get("ricorrenza_totale","?")}'
                     if t.get("id_ricorrenza") else "")
        trasf_rows += f"""
        <tr>
            <td>{html.escape(t.get('data',''))}</td>
            <td>{html.escape(nome_da_id.get(t.get('da',''), '?'))}</td>
            <td>{html.escape(nome_da_id.get(t.get('a',''), '?'))}</td>
            <td style="text-align:right;">€ {_fmt_it(float(t.get('importo',0) or 0))}</td>
            <td>{html.escape(t.get('note','') or '')}{ric_badge}</td>
        </tr>"""
    if not trasf_ord:
        trasf_rows = ('<tr><td colspan="5" style="text-align:center; color:var(--text-dim); '
                      'padding:12px;">Nessun trasferimento registrato</td></tr>')
    trasf_options_modifica = "".join(
        f'<option value="{t.get("id")}" '
        f'data-data="{html.escape(t.get("data",""))}" '
        f'data-da="{html.escape(nome_da_id.get(t.get("da",""),""))}" '
        f'data-a="{html.escape(nome_da_id.get(t.get("a",""),""))}" '
        f'data-importo="{float(t.get("importo",0) or 0):.2f}" '
        f'data-note="{html.escape(t.get("note","") or "")}" '
        f'data-ricorrente="{"1" if t.get("id_ricorrenza") else "0"}">'
        f'{html.escape(t.get("data",""))} · {html.escape(nome_da_id.get(t.get("da",""),"?"))} → '
        f'{html.escape(nome_da_id.get(t.get("a",""),"?"))} · € {_fmt_it(float(t.get("importo",0) or 0))}</option>'
        for t in trasf_ord
    )

    oggi = datetime.date.today()
    anno_corrente_format = str(oggi.year)
    netto_col = "var(--green)" if totale_conti >= 0 else "var(--red)"

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>🏦 Portafoglio Bancario</title>
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
    .main-container {{ max-width:720px; margin:0 auto; padding:14px; animation:fadeIn 0.3s ease; }}
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
    .tab-frame {{
        background:var(--surface); border:1px solid var(--border);
        border-radius:0 var(--radius-lg) var(--radius-lg) var(--radius-lg);
        padding:16px; position:relative; overflow:hidden;
    }}
    .tab-frame::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .tab-pane {{ display:none; }}
    .conto-cards {{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:10px; }}
    .conto-card {{
        border-radius:12px; padding:10px 14px; min-width:120px; color:#fff;
    }}
    .conto-card-nome {{ font-size:0.82em; font-weight:700; }}
    .conto-card-saldo {{ font-size:1.05em; font-weight:800; margin-top:2px; }}
    .conto-card-tipo {{ font-size:0.68em; opacity:0.85; margin-top:1px; }}
    .barra-distrib {{
        display:flex; width:100%; height:34px; border-radius:8px; overflow:hidden; margin-top:6px;
    }}
    .barra-distrib div {{ height:100%; }}
    .legenda-riep {{ display:flex; flex-wrap:wrap; gap:12px; margin-top:8px; }}
    .legenda-item {{ display:flex; align-items:center; gap:5px; font-size:0.78em; color:var(--text-mid); }}
    .legenda-dot {{ width:10px; height:10px; border-radius:50%; flex-shrink:0; }}
    .riep-riga {{
        display:flex; justify-content:space-between; align-items:center;
        padding:8px 0; border-top:1px solid var(--border); font-size:0.9em;
    }}
    .riep-riga.tot {{ font-weight:800; font-size:1.02em; }}
    table.tbl-portafoglio {{
        width:100%; border-collapse:collapse; font-size:0.82em; margin-top:6px;
    }}
    table.tbl-portafoglio th {{
        text-align:left; color:var(--text-dim); font-size:0.75em; text-transform:uppercase;
        letter-spacing:0.5px; padding:6px 6px; border-bottom:1px solid var(--border);
    }}
    table.tbl-portafoglio td {{
        padding:7px 6px; border-bottom:1px solid var(--border); vertical-align:top;
    }}
    .tbl-scroll {{ max-height:340px; overflow-y:auto; }}
    .sec-card {{
        background:var(--surface2); border:1px solid var(--border);
        border-radius:var(--radius-lg); margin-top:12px; position:relative;
    }}
    .sec-card::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        border-radius:var(--radius-lg) var(--radius-lg) 0 0; z-index:1;
    }}
    .sec-card.add::before {{ background:linear-gradient(90deg, transparent, var(--green), transparent); }}
    .sec-card.edit::before {{ background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent); }}
    details summary {{
        list-style:none; cursor:pointer; padding:13px 16px;
        display:flex; align-items:center; gap:10px;
        font-family:'DM Sans',sans-serif; font-size:0.86em; font-weight:700;
        border-radius:var(--radius-lg); transition:background 0.15s; user-select:none;
    }}
    details[open] summary {{ border-radius:var(--radius-lg) var(--radius-lg) 0 0; }}
    details summary::-webkit-details-marker {{ display:none; }}
    details summary:hover {{ background:var(--surface3); }}
    .sum-arrow {{ font-size:0.7em; color:var(--text-dim); margin-left:auto; transition:transform 0.22s; }}
    details[open] .sum-arrow {{ transform:rotate(90deg); }}
    .sum-add {{ color:var(--green); }}
    .sum-edit {{ color:var(--gold); }}
    .form-body {{ padding:4px 16px 18px; border-top:1px solid var(--border); }}
    .form-row {{ display:flex; gap:10px; flex-wrap:wrap; }}
    .form-group {{ margin-top:12px; flex:1; min-width:130px; }}
    label {{
        display:block; font-size:0.62em; font-weight:700; color:var(--text-dim);
        letter-spacing:1.6px; text-transform:uppercase; margin-bottom:5px;
    }}
    input[type="text"], input[type="number"], select {{
        width:100%; padding:9px 12px; background:var(--surface); font-size: 0.62em;
        border:1px solid var(--border); border-radius:9px; color:var(--text);
        font-family:'DM Sans',sans-serif; font-size:0.88em;
        transition:all 0.2s; outline:none; -webkit-appearance:none; appearance:none;
    }}
    input[type="text"]:focus, input[type="number"]:focus, select:focus {{
        border-color:var(--border-active); background:var(--surface3);
        box-shadow:0 0 0 3px rgba(99,160,240,0.07);
    }}
    select {{
        background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='7' viewBox='0 0 12 7'%3E%3Cpath fill='none' stroke='%23555' stroke-width='1.5' d='M1 1l5 5 5-5'/%3E%3C/svg%3E");
        background-repeat:no-repeat; background-position:right 12px center;
        padding-right:30px; cursor:pointer;
    }}
    .chk-row {{ display:flex; align-items:center; gap:8px; margin-top:14px; }}
    .chk-row label {{ margin:0; text-transform:none; letter-spacing:0; font-size:0.85em; color:var(--text); }}
    .btn-submit {{
        padding:10px 16px; margin-top:14px; margin-right:8px; border:none; border-radius:9px;
        font-family:'DM Sans',sans-serif; font-size:0.85em; font-weight:700;
        line-height:1.5; cursor:pointer; transition:all 0.2s;
    }}
    .btn-submit:hover {{ transform:translateY(-1px); }}
    .btn-add {{ background:linear-gradient(135deg, var(--green), #2d7a56); color:#000; }}
    .btn-edit {{ background:linear-gradient(135deg, var(--gold), #8a6820); color:#000; }}
    .btn-del {{ background:linear-gradient(135deg, var(--red), #9c2d2d); color:#fff; }}
    .ric-extra {{ display:none; }}
    .ambito-extra {{ display:none; }}
    .btn-home {{
        display:block; text-align:center; padding:13px; margin-top:12px;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; border-radius:10px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.9em;
        line-height:1.5; transition:all 0.2s;
    }}
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
    function openTab(id, btn) {{
        document.querySelectorAll('.tab-pane').forEach(function(el) {{ el.style.display = 'none'; }});
        document.querySelectorAll('.tab-btn').forEach(function(el) {{ el.classList.remove('active'); }});
        document.getElementById(id).style.display = 'block';
        btn.classList.add('active');
        localStorage.setItem('portafoglio_tab', id);
    }}
    function aggiornaFormConto() {{
        const sel = document.getElementById("conto_modifica_sel");
        const opt = sel.options[sel.selectedIndex];
        if (!opt || !opt.value) return;
        document.getElementById("c_id").value = opt.value;
        document.getElementById("c_nome").value = opt.getAttribute("data-nome") || "";
        document.getElementById("c_tipo").value = opt.getAttribute("data-tipo") || "personale";
        document.getElementById("c_saldo").value = opt.getAttribute("data-saldo") || "0";
        document.getElementById("c_iban").value = opt.getAttribute("data-iban") || "";
        document.getElementById("c_note").value = opt.getAttribute("data-note") || "";
        document.getElementById("c_princ").checked = opt.getAttribute("data-principale") === "1";
    }}
    function aggiornaFormTrasferimento() {{
        const sel = document.getElementById("trasf_modifica_sel");
        const opt = sel.options[sel.selectedIndex];
        if (!opt || !opt.value) return;
        document.getElementById("t_id").value = opt.value;
        document.getElementById("t_data").value = opt.getAttribute("data-data") || "";
        document.getElementById("t_da").value = opt.getAttribute("data-da") || "";
        document.getElementById("t_a").value = opt.getAttribute("data-a") || "";
        document.getElementById("t_importo").value = opt.getAttribute("data-importo") || "";
        document.getElementById("t_note").value = opt.getAttribute("data-note") || "";
        const ambitoBox = document.getElementById("ambito_box");
        ambitoBox.style.display = (opt.getAttribute("data-ricorrente") === "1") ? "block" : "none";
        document.getElementById("del_trasf_id").value = opt.value;
    }}
    function toggleRicorrenza() {{
        const v = document.getElementById("ric_tipo_sel").value;
        document.getElementById("ric_extra_box").style.display = (v === "Nessuna") ? "none" : "block";
    }}
    document.addEventListener("DOMContentLoaded", function() {{
        applyTheme(localStorage.getItem('theme') || 'dark');
        const savedTab = localStorage.getItem('portafoglio_tab') || 'tabRiepilogo';
        const btn = document.querySelector('.tab-btn[data-tab="' + savedTab + '"]') || document.querySelector('.tab-btn');
        if (btn) openTab(btn.getAttribute('data-tab'), btn);
        const hash = window.location.hash.replace('#', '');
        if (hash === 'conti' || hash === 'trasferimenti') {{
            const b2 = document.querySelector('.tab-btn[data-tab="tab' + (hash === 'conti' ? 'Conti' : 'Trasferimenti') + '"]');
            if (b2) openTab(b2.getAttribute('data-tab'), b2);
        }}
    }});
    document.addEventListener("click", function(e) {{
        const menu = document.getElementById("extraMenu");
        const btn = document.querySelector(".menu-btn");
        if (menu && menu.style.display === "block" && !menu.contains(e.target) && e.target !== btn)
            menu.style.display = "none";
    }});
    let formInAttesaConferma = null;
    function apriModalConferma(form, messaggio) {{
        formInAttesaConferma = form;
        document.getElementById("modalConfermaText").textContent = messaggio;
        document.getElementById("confermaModal").style.display = "flex";
        return false;
    }}
    function chiudiModalConferma() {{
        document.getElementById("confermaModal").style.display = "none";
        formInAttesaConferma = null;
    }}
    function apriAlertModal(messaggio) {{
        document.getElementById("alertModalText").textContent = messaggio;
        document.getElementById("alertModal").style.display = "flex";
    }}
    function chiudiAlertModal() {{
        document.getElementById("alertModal").style.display = "none";
    }}
    function confermaEliminaConto(form) {{
        const id = document.getElementById("c_id_del").value;
        if (!id) {{
            apriAlertModal("Seleziona prima un conto da eliminare.");
            return false;
        }}
        return apriModalConferma(form, "Eliminare questo conto? Verranno eliminati anche i trasferimenti collegati.");
    }}
    function confermaEliminaTrasferimento(form) {{
        const id = document.getElementById("del_trasf_id").value;
        if (!id) {{
            apriAlertModal("Seleziona prima un trasferimento da eliminare.");
            return false;
        }}
        return apriModalConferma(form, "Eliminare questo trasferimento?");
    }}
    document.addEventListener("DOMContentLoaded", function() {{
        document.getElementById("modalConfermaBtn").onclick = function() {{
            document.getElementById("confermaModal").style.display = "none";
            if (formInAttesaConferma) formInAttesaConferma.submit();
        }};
        const paramsErrore = new URLSearchParams(window.location.search);
        if (paramsErrore.get('errore')) {{
            apriAlertModal(paramsErrore.get('errore'));
        }}
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
    <div class="header-title">🏦 Portafoglio Bancario</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main class="main-container">
    <div class="tab-bar">
        <button class="tab-btn" data-tab="tabRiepilogo" onclick="openTab('tabRiepilogo', this)">📋 Riepilogo</button>
        <button class="tab-btn" data-tab="tabConti" onclick="openTab('tabConti', this)">🏦 Conti</button>
        <button class="tab-btn" data-tab="tabTrasferimenti" onclick="openTab('tabTrasferimenti', this)">🔁 Trasferimenti</button>
    </div>
    <div class="tab-frame">

        <div id="tabRiepilogo" class="tab-pane">
            <div class="conto-cards">{cards_html}</div>
            <div class="barra-distrib">{barre_html}</div>
            <div class="legenda-riep">{legenda_html}</div>
            <div class="riep-riga tot">
                <span>Totale conti registrati</span>
                <span style="color:{netto_col};">€ {_fmt_it(totale_conti)}</span>
            </div>
        </div>

        <div id="tabConti" class="tab-pane">
            <div class="tbl-scroll">
                <table class="tbl-portafoglio">
                    <thead><tr><th>Nome</th><th>Tipo</th><th style="text-align:right;">Saldo</th><th>★</th><th>Note</th></tr></thead>
                    <tbody>{conti_rows}</tbody>
                </table>
            </div>
            <div class="sec-card add">
                <details>
                    <summary><span class="sum-add">➕</span><span class="sum-add">Aggiungi Conto</span><span class="sum-arrow">▶</span></summary>
                    <div class="form-body">
                        <form action="/portafoglio_web/salva_conto" method="POST">
                            <input type="hidden" name="conto_id" value="">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Nome</label>
                                    <input type="text" name="nome" maxlength="25" required placeholder="es: Conto Corrente">
                                </div>
                                <div class="form-group">
                                    <label>Tipo</label>
                                    <select name="tipo">{tipo_options}</select>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Saldo iniziale €</label>
                                    <input type="text" name="saldo" inputmode="decimal" placeholder="0,00">
                                </div>
                                <div class="form-group">
                                    <label>IBAN (opzionale)</label>
                                    <input type="text" name="iban" placeholder="IT00...">
                                </div>
                            </div>
                            <div class="form-group">
                                <label>Note (opzionale)</label>
                                <input type="text" name="note" maxlength="20" placeholder="es: risparmio">
                            </div>
                            <div class="chk-row">
                                <input type="checkbox" name="principale" value="1" id="c_princ_new">
                                <label for="c_princ_new">Conto principale</label>
                            </div>
                            <button type="submit" class="btn-submit btn-add">➕ Aggiungi</button>
                        </form>
                    </div>
                </details>
            </div>
            <div class="sec-card edit">
                <details>
                    <summary><span class="sum-edit">✏️</span><span class="sum-edit">Modifica / Elimina Conto</span><span class="sum-arrow">▶</span></summary>
                    <div class="form-body">
                        <div class="form-group">
                            <label>Seleziona conto</label>
                            <select id="conto_modifica_sel" onchange="aggiornaFormConto()">
                                <option value="">— seleziona —</option>
                                {conti_options_modifica}
                            </select>
                        </div>
                        <form action="/portafoglio_web/salva_conto" method="POST">
                            <input type="hidden" name="conto_id" id="c_id" value="">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Nome</label>
                                    <input type="text" name="nome" id="c_nome" maxlength="25" required>
                                </div>
                                <div class="form-group">
                                    <label>Tipo</label>
                                    <select name="tipo" id="c_tipo">{tipo_options}</select>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Saldo €</label>
                                    <input type="text" name="saldo" id="c_saldo" inputmode="decimal">
                                </div>
                                <div class="form-group">
                                    <label>IBAN</label>
                                    <input type="text" name="iban" id="c_iban">
                                </div>
                            </div>
                            <div class="form-group">
                                <label>Note</label>
                                <input type="text" name="note" id="c_note" maxlength="20">
                            </div>
                            <div class="chk-row">
                                <input type="checkbox" name="principale" value="1" id="c_princ">
                                <label for="c_princ">Conto principale</label>
                            </div>
                            <button type="submit" class="btn-submit btn-edit">✏️ Salva Modifiche</button>
                        </form>
                        <form action="/portafoglio_web/elimina_conto" method="POST"
                              onsubmit="return confermaEliminaConto(this);">
                            <input type="hidden" name="conto_id" id="c_id_del" value="">
                            <button type="submit" class="btn-submit btn-del"
                                    onclick="document.getElementById('c_id_del').value = document.getElementById('c_id').value;">
                                🗑️ Elimina Conto
                            </button>
                        </form>
                    </div>
                </details>
            </div>
        </div>

        <div id="tabTrasferimenti" class="tab-pane">
            <div class="tbl-scroll">
                <table class="tbl-portafoglio">
                    <thead><tr><th>Data</th><th>Da</th><th>A</th><th style="text-align:right;">Importo</th><th>Note</th></tr></thead>
                    <tbody>{trasf_rows}</tbody>
                </table>
            </div>
            <div class="sec-card add">
                <details>
                    <summary><span class="sum-add">➕</span><span class="sum-add">Nuovo Trasferimento</span><span class="sum-arrow">▶</span></summary>
                    <div class="form-body">
                        <form action="/portafoglio_web/salva_trasferimento" method="POST">
                            <input type="hidden" name="trasferimento_id" value="">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Data</label>
                                    <input type="text" name="data" required placeholder="GG-MM-AAAA" value="{oggi.strftime('%d-%m-%Y')}">
                                </div>
                                <div class="form-group">
                                    <label>Importo €</label>
                                    <input type="text" name="importo" inputmode="decimal" required placeholder="0,00">
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Da conto</label>
                                    <select name="da">{nomi_conti_options}</select>
                                </div>
                                <div class="form-group">
                                    <label>A conto</label>
                                    <select name="a">{nomi_conti_options}</select>
                                </div>
                            </div>
                            <div class="form-group">
                                <label>Note (opzionale)</label>
                                <input type="text" name="note" maxlength="20" placeholder="es: risparmio mensile">
                            </div>
                            <div class="form-group">
                                <label>Ripeti</label>
                                <select name="ricorrenza_tipo" id="ric_tipo_sel" onchange="toggleRicorrenza()">
                                    <option value="Nessuna">Nessuna</option>
                                    <option value="Ogni giorno">Ogni giorno</option>
                                    <option value="Ogni settimana">Ogni settimana</option>
                                    <option value="Ogni mese">Ogni mese</option>
                                    <option value="Ogni anno">Ogni anno</option>
                                </select>
                            </div>
                            <div class="form-group ric-extra" id="ric_extra_box">
                                <label>Numero ripetizioni (la Data è l'inizio serie)</label>
                                <input type="text" name="ricorrenza_n" value="1" inputmode="numeric">
                            </div>
                            <button type="submit" class="btn-submit btn-add">➕ Salva Trasferimento</button>
                        </form>
                    </div>
                </details>
            </div>
            <div class="sec-card edit">
                <details>
                    <summary><span class="sum-edit">✏️</span><span class="sum-edit">Modifica / Elimina Trasferimento</span><span class="sum-arrow">▶</span></summary>
                    <div class="form-body">
                        <div class="form-group">
                            <label>Seleziona trasferimento</label>
                            <select id="trasf_modifica_sel" onchange="aggiornaFormTrasferimento()">
                                <option value="">— seleziona —</option>
                                {trasf_options_modifica}
                            </select>
                        </div>
                        <form action="/portafoglio_web/salva_trasferimento" method="POST">
                            <input type="hidden" name="trasferimento_id" id="t_id" value="">
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Data</label>
                                    <input type="text" name="data" id="t_data" required placeholder="GG-MM-AAAA">
                                </div>
                                <div class="form-group">
                                    <label>Importo €</label>
                                    <input type="text" name="importo" id="t_importo" inputmode="decimal" required>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Da conto</label>
                                    <select name="da" id="t_da">{nomi_conti_options}</select>
                                </div>
                                <div class="form-group">
                                    <label>A conto</label>
                                    <select name="a" id="t_a">{nomi_conti_options}</select>
                                </div>
                            </div>
                            <div class="form-group">
                                <label>Note</label>
                                <input type="text" name="note" id="t_note" maxlength="20">
                            </div>
                            <p style="font-size:0.72em; color:var(--text-dim); margin-top:10px;">
                                Nota: modificando un trasferimento ricorrente viene aggiornata solo questa occorrenza.
                            </p>
                            <button type="submit" class="btn-submit btn-edit">✏️ Salva Modifiche</button>
                        </form>
                        <form action="/portafoglio_web/elimina_trasferimento" method="POST"
                              onsubmit="return confermaEliminaTrasferimento(this);">
                            <input type="hidden" name="trasferimento_id" id="del_trasf_id" value="">
                            <div class="form-group ambito-extra" id="ambito_box">
                                <label>Ambito eliminazione</label>
                                <select name="ambito">
                                    <option value="singola">Solo questa occorrenza</option>
                                    <option value="serie">Tutta la serie ricorrente</option>
                                </select>
                            </div>
                            <button type="submit" class="btn-submit btn-del">🗑️ Elimina Trasferimento</button>
                        </form>
                    </div>
                </details>
            </div>
        </div>

    </div>
    <a href="/" class="btn-home">🏠 Torna alla Home</a>
</main>
<div id="confermaModal" class="modal-overlay">
    <div class="modal-box">
        <div class="modal-title">⚠️ Conferma</div>
        <div class="modal-text" id="modalConfermaText"></div>
        <div class="modal-btns">
            <button class="m-btn m-cancel" onclick="chiudiModalConferma()">Annulla</button>
            <button id="modalConfermaBtn" class="m-btn m-confirm">Conferma</button>
        </div>
    </div>
</div>
<div id="alertModal" class="modal-overlay">
    <div class="modal-box">
        <div class="modal-title">⚠️ Attenzione</div>
        <div class="modal-text" id="alertModalText"></div>
        <div class="modal-btns">
            <button class="m-btn m-confirm" onclick="chiudiAlertModal()">OK</button>
        </div>
    </div>
</div>
</body>
</html>"""
