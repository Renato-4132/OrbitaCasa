#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import uuid
import datetime
import threading

from moduli.modello_spesa import SpesaEntry, campo, METODI_PAGAMENTO, metodo_pagamento_pulito
from moduli.web_utils import _fmt_it

_LOCK = threading.RLock()
PERIODI = ("Ogni giorno", "Ogni mese", "Ogni anno")
N_MAX = 365


def _parse_data(s):
    try:
        return datetime.datetime.strptime(s, "%d-%m-%Y").date()
    except (ValueError, TypeError):
        return None


def _giorni_nel_mese(year, month):
    bisestile = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    return [31, 29 if bisestile else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]


def _date_ricorrenza(periodo, data_inizio, n):
    date_list = []
    for i in range(n):
        if periodo == "Ogni giorno":
            d = data_inizio + datetime.timedelta(days=i)
        elif periodo == "Ogni mese":
            month = (data_inizio.month - 1 + i) % 12 + 1
            year = data_inizio.year + (data_inizio.month - 1 + i) // 12
            day = min(data_inizio.day, _giorni_nel_mese(year, month))
            try:
                d = datetime.date(year, month, day)
            except Exception:
                d = datetime.date(year, month, 1)
        elif periodo == "Ogni anno":
            year = data_inizio.year + i
            try:
                d = datetime.date(year, data_inizio.month, data_inizio.day)
            except Exception:
                d = datetime.date(year, data_inizio.month, 1)
        else:
            break
        date_list.append(d)
    return date_list


def _data_fine(dati):
    dl = [x for x in (_parse_data(s) for s in dati.get("date_list", []) or []) if x]
    if dl:
        return max(dl)
    di = _parse_data(dati.get("data_inizio"))
    n = dati.get("n", 0)
    if di and isinstance(n, int) and n > 0:
        dd = _date_ricorrenza(dati.get("tipo", ""), di, n)
        return dd[-1] if dd else None
    return None


def _conti_portafoglio():
    import __main__ as _app
    try:
        with open(_app.PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as f:
            db = json.load(f)
        conti = db.get("conti", [])
        nomi = [c.get("nome", "") for c in conti if c.get("nome")]
        princ = next((c.get("nome", "") for c in conti if c.get("principale")), "")
        return nomi, princ
    except Exception:
        return [], ""


def _aggiorna_gui(self):
    try:
        self.after(0, self.refresh_gui)
    except Exception:
        pass


def ricorrenze_web_elenco(self):
    oggi = datetime.date.today()
    with _LOCK:
        reale = {}
        for voci in self.spese.values():
            for voce in voci:
                rid = campo(voce, "id_ricorrenza", None)
                if rid and rid in self.ricorrenze:
                    e = reale.setdefault(rid, {"volte": 0, "importo": 0.0, "conto": ""})
                    e["volte"] += 1
                    e["importo"] += float(campo(voce, "importo", 0.0))
                    if not e["conto"]:
                        try:
                            e["conto"] = self._conto_effettivo(voce) or ""
                        except Exception:
                            e["conto"] = campo(voce, "conto", "") or ""
        righe = []
        impatto = 0.0
        for rid, dati in self.ricorrenze.items():
            tipo_voce = dati.get("tipo_voce", "Uscita")
            imp = float(dati.get("imp", 0.0) or 0.0)
            n = dati.get("n", 0) if isinstance(dati.get("n", 0), int) else 0
            periodo = dati.get("tipo", "")
            r = reale.get(rid, {"volte": 0, "importo": 0.0, "conto": ""})
            tot = imp * n
            saldate = min(r["volte"], n) if n > 0 else r["volte"]
            df = _data_fine(dati)
            prossima = ""
            for s in dati.get("date_list", []) or []:
                d = _parse_data(s)
                if d and d >= oggi:
                    prossima = s
                    break
            hashtag = list(dati.get("hashtag", []) or [])
            righe.append({
                "id": rid,
                "cat": dati.get("cat", "Sconosciuta"),
                "desc": dati.get("desc", ""),
                "conto": dati.get("conto") or r["conto"] or "",
                "metodo": dati.get("metodo_pagamento") or "",
                "tag": " ".join(hashtag),
                "tipo_voce": tipo_voce,
                "imp": imp,
                "imp_str": _fmt_it(imp),
                "n": n,
                "periodo": periodo,
                "saldate": saldate,
                "inizio": dati.get("data_inizio", ""),
                "fine": df.strftime("%d-%m-%Y") if df else "N/D",
                "prossima": prossima,
                "totale_str": _fmt_it(tot),
                "contab_str": _fmt_it(r["importo"]),
                "residuo_str": _fmt_it(tot - r["importo"]),
                "voci_registrate": r["volte"],
            })
            if periodo.lower() == "ogni mese":
                impatto += imp if tipo_voce == "Entrata" else -imp
        righe.sort(key=lambda x: (
            0 if x["prossima"] else 1,
            _parse_data(x["prossima"]) or datetime.date.max,
            x["cat"].lower(),
        ))
        nomi_conti, princ = _conti_portafoglio()
        categorie = [{"nome": c, "tipo": (getattr(self, "categorie_tipi", {}) or {}).get(c, "Uscita")}
                     for c in self.categorie if c and c != "Categoria Rimossa"]
        return {
            "ok": True,
            "ricorrenze": righe,
            "impatto_str": _fmt_it(abs(impatto)),
            "impatto_segno": "+" if impatto >= 0 else "-",
            "impatto_pos": impatto >= 0,
            "categorie": categorie,
            "conti": nomi_conti,
            "conto_principale": princ,
            "metodi": list(METODI_PAGAMENTO),
            "oggi": oggi.isoformat(),
        }


def ricorrenze_web_dettaglio(self, ric_id):
    oggi = datetime.date.today()
    with _LOCK:
        dati = self.ricorrenze.get(ric_id)
        if dati is None:
            return {"ok": False, "errore": "Ricorrenza non trovata."}, 404
        tipo_voce = dati.get("tipo_voce", "Uscita")
        imp_rif = float(dati.get("imp", 0.0) or 0.0)
        conto_rif = dati.get("conto") or ""
        righe = []
        for s in dati.get("date_list", []) or []:
            d = _parse_data(s)
            if d is None:
                continue
            trovata = None
            for voce in self.spese.get(d, []):
                if str(campo(voce, "id_ricorrenza", None)) == str(ric_id):
                    trovata = voce
                    break
            imp = float(campo(trovata, "importo", imp_rif)) if trovata is not None else imp_rif
            conto = ""
            if trovata is not None:
                try:
                    conto = self._conto_effettivo(trovata) or ""
                except Exception:
                    conto = campo(trovata, "conto", "") or ""
            if trovata is not None:
                stato = "registrata"
            elif d <= oggi:
                stato = "non_registrata"
            else:
                stato = "prevista"
            righe.append({
                "data": s,
                "stato": stato,
                "imp_str": _fmt_it(imp),
                "conto": conto or conto_rif,
            })
        return {"ok": True, "tipo_voce": tipo_voce, "date": righe}, 200


def ricorrenze_web_crea(self, d):
    periodo = str(d.get("periodo", ""))
    if periodo not in PERIODI:
        return {"ok": False, "errore": "Seleziona un tipo di ricorrenza valido."}, 400
    try:
        n = int(d.get("n"))
        if n <= 0 or n > N_MAX:
            raise ValueError
    except Exception:
        return {"ok": False, "errore": f"Numero ripetizioni non valido (1-{N_MAX})."}, 400
    try:
        data_inizio = datetime.date.fromisoformat(str(d.get("data_inizio", "")))
    except ValueError:
        return {"ok": False, "errore": "Data inizio ricorrenza non valida."}, 400
    cat = str(d.get("cat", "")).strip()
    if not cat or cat == "Categoria Rimossa" or cat not in self.categorie:
        return {"ok": False, "errore": "Categoria non valida."}, 400
    try:
        imp = float(str(d.get("imp", "")).replace(",", "."))
        if imp <= 0:
            raise ValueError
    except Exception:
        return {"ok": False, "errore": "Importo mancante o non valido."}, 400
    tipo = str(d.get("tipo_voce", "Uscita"))
    if tipo not in ("Entrata", "Uscita"):
        return {"ok": False, "errore": "Tipo voce non valido."}, 400
    nomi_conti, _ = _conti_portafoglio()
    conto = str(d.get("conto", "") or "").strip()
    if conto == "(nessuno)":
        conto = ""
    if conto and conto not in nomi_conti:
        return {"ok": False, "errore": "Conto non valido."}, 400
    metodo = metodo_pagamento_pulito(str(d.get("metodo", "") or ""))
    if metodo and metodo not in METODI_PAGAMENTO:
        return {"ok": False, "errore": "Metodo di pagamento non valido."}, 400
    tags = self._normalizza_tags(str(d.get("tag", "") or ""))
    desc_in = str(d.get("desc", "") or "").strip()
    try:
        with _LOCK:
            ric_id = str(uuid.uuid4())
            id_visibile = ric_id[:8]
            desc = f"RIC· {desc_in} ID:{id_visibile}" if desc_in else f"RIC· ID:{id_visibile}"
            date_list = _date_ricorrenza(periodo, data_inizio, n)
            for dd in date_list:
                self.spese.setdefault(dd, []).append(SpesaEntry.nuova(
                    cat, desc, imp, tipo, hashtag=list(tags), conto=conto,
                    id_ricorrenza=ric_id, metodo_pagamento=metodo))
            self.ricorrenze[ric_id] = {
                "tipo": periodo,
                "n": n,
                "data_inizio": data_inizio.strftime("%d-%m-%Y"),
                "cat": cat,
                "desc": desc,
                "imp": imp,
                "tipo_voce": tipo,
                "conto": conto,
                "metodo_pagamento": metodo,
                "hashtag": list(tags),
                "date_list": [x.strftime("%d-%m-%Y") for x in date_list],
            }
            self.save_db()
    except Exception as e:
        return {"ok": False, "errore": f"Errore durante il salvataggio: {e}"}, 500
    _aggiorna_gui(self)
    return {"ok": True, "generate": n}, 200


def ricorrenze_web_elimina(self, d):
    ids = d.get("ids") or []
    if isinstance(ids, str):
        ids = [ids]
    ids = [str(x) for x in ids]
    if not ids:
        return {"ok": False, "errore": "Nessuna ricorrenza selezionata."}, 400
    eliminate = 0
    voci_cancellate = 0
    try:
        with _LOCK:
            for ric_id in ids:
                if ric_id not in self.ricorrenze:
                    continue
                for data_key, voci in list(self.spese.items()):
                    rimosse = [v for v in voci if campo(v, "id_ricorrenza", None) == ric_id]
                    if not rimosse:
                        continue
                    nuove = [v for v in voci if campo(v, "id_ricorrenza", None) != ric_id]
                    for v in rimosse:
                        if hasattr(self, "elimina_piano_per_spesa"):
                            self.elimina_piano_per_spesa(campo(v, "id_spesa", None))
                        self.annulla_azione_gamification("movimento")
                        voci_cancellate += 1
                    if nuove:
                        self.spese[data_key] = nuove
                    else:
                        del self.spese[data_key]
                del self.ricorrenze[ric_id]
                eliminate += 1
            if eliminate:
                if hasattr(self, "db"):
                    self.db["spese"] = self.spese
                    self.db["ricorrenze"] = self.ricorrenze
                self.save_db()
    except Exception as e:
        return {"ok": False, "errore": f"Errore durante la cancellazione: {e}"}, 500
    if not eliminate:
        return {"ok": False, "errore": "Ricorrenza non trovata."}, 404
    _aggiorna_gui(self)
    return {"ok": True, "eliminate": eliminate, "voci": voci_cancellate}, 200


_PAGINA = r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>🔁 Ricorrenze</title>
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
    body { font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text); min-height:100vh; padding-bottom:100px; transition:background 0.3s,color 0.3s; }
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
    .riepilogo { background:var(--surface); border:1px solid var(--border); border-radius:14px; padding:12px 14px; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; font-size:0.85em; color:var(--text-mid); }
    .riepilogo b { font-size:1.15em; }
    .pos { color:var(--green); } .neg { color:var(--red); }
    .ric { background:var(--surface); border:1px solid var(--border); border-left:4px solid var(--red); border-radius:14px; padding:11px 12px; margin-bottom:8px; cursor:pointer; }
    .ric.entrata { border-left-color:var(--green); }
    .ric.conclusa { opacity:0.55; }
    .ric .riga1 { display:flex; justify-content:space-between; gap:10px; align-items:baseline; }
    .ric .cat { font-weight:700; font-size:0.95em; }
    .ric .imp { font-weight:800; white-space:nowrap; }
    .ric .meta { color:var(--text-mid); font-size:0.78em; margin-top:4px; line-height:1.5; word-break:break-word; }
    .barra { height:5px; background:var(--surface3); border-radius:3px; margin-top:8px; overflow:hidden; }
    .barra i { display:block; height:100%; background:var(--blue); }
    .vuoto { text-align:center; color:var(--text-dim); font-style:italic; padding:30px 10px; font-size:0.9em; }
    input, select { background:var(--surface3); border:1px solid var(--border); color:var(--text); border-radius:10px; padding:11px; font-family:inherit; font-size:1em; width:100%; }
    input:focus, select:focus { outline:none; border-color:var(--border-active); }
    .campo { margin-bottom:10px; }
    .campo label { display:block; font-size:0.62em; font-weight:700; color:var(--text-dim); letter-spacing:1.5px; text-transform:uppercase; margin-bottom:5px; }
    .due { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
    #fab { position:fixed; right:18px; bottom:22px; width:56px; height:56px; border-radius:50%; border:none; background:linear-gradient(135deg,var(--gold),#8a6820); color:#000; font-size:1.8em; cursor:pointer; box-shadow:0 6px 20px rgba(0,0,0,0.5); z-index:50; }
    #velo { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.6); z-index:500; overflow-y:auto; }
    .scheda { background:var(--surface); border:1px solid var(--border); border-radius:18px; max-width:480px; margin:30px auto; padding:18px; }
    .scheda h3 { margin-bottom:14px; font-size:1.05em; }
    .btns { display:flex; gap:8px; margin-top:14px; }
    .btn { flex:1; padding:12px; border:none; border-radius:10px; font-family:inherit; font-weight:700; font-size:0.92em; cursor:pointer; }
    .btn.ok { background:linear-gradient(135deg,var(--gold),#8a6820); color:#000; }
    .btn.no { background:var(--surface3); color:var(--text-mid); border:1px solid var(--border); }
    .btn.del { background:rgba(224,90,90,0.15); color:var(--red); border:1px solid var(--red); }
    .toggle-t { display:flex; gap:6px; }
    .toggle-t button { flex:1; padding:10px; border-radius:10px; border:1px solid var(--border); background:var(--surface3); color:var(--text-mid); font-family:inherit; font-weight:700; cursor:pointer; }
    .toggle-t button.on.u { background:rgba(224,90,90,0.18); color:var(--red); border-color:var(--red); }
    .toggle-t button.on.e { background:rgba(76,175,130,0.18); color:var(--green); border-color:var(--green); }
    .collapsible-wrap { margin-top:6px; padding-top:12px; border-top:1px solid var(--border); }
    .collapsible-toggle { background:none; border:none; width:100%; display:flex; align-items:center; gap:8px; color:var(--text-mid); font-family:inherit; font-size:0.82em; font-weight:700; letter-spacing:0.5px; cursor:pointer; padding:0 0 10px 0; text-align:left; transition:color 0.15s; }
    .collapsible-toggle:hover { color:var(--blue); }
    .arrow { font-size:0.7em; transition:transform 0.25s; }
    .collapsible-open .arrow { transform:rotate(90deg); }
    .collapsible-content { display:none; }
    .collapsible-open .collapsible-content { display:block; }
    .dt { display:flex; justify-content:space-between; gap:8px; padding:8px 4px; border-bottom:1px solid var(--border); font-size:0.88em; }
    .dt:last-child { border-bottom:none; }
    .st-registrata { color:var(--green); } .st-non_registrata { color:var(--orange); } .st-prevista { color:var(--text-mid); }
    .modal-overlay { display:none; position:fixed; inset:0;
        background:rgba(0,0,0,0.75); backdrop-filter:blur(6px);
        z-index:3000; align-items:center; justify-content:center; }
    .modal-box { background:var(--surface2); border:1px solid var(--border);
        border-radius:var(--radius-lg); padding:24px 20px; width:88%; max-width:320px; text-align:center; }
    .modal-title { font-family:'DM Sans',sans-serif; font-size:1em; font-weight:800; color:var(--gold); margin-bottom:10px; }
    .modal-text { font-size:0.88em; color:var(--text-mid); margin-bottom:18px; line-height:1.5; white-space:pre-line; }
    .modal-btns { display:flex; gap:10px; }
    .m-btn { flex:1; padding:12px; border-radius:9px; border:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.88em; cursor:pointer; transition:all 0.15s; }
    .m-cancel { background:var(--surface3); color:var(--text-mid); }
    .m-confirm { background:linear-gradient(135deg, var(--blue), #2f5faa); color:#fff; }
    .m-confirm:hover { box-shadow:0 6px 16px rgba(99,160,240,0.3); }
    #msg { position:fixed; left:50%; bottom:92px; transform:translateX(-50%); background:var(--surface2); border:1px solid var(--border-active); padding:10px 16px; border-radius:12px; font-weight:700; font-size:0.9em; display:none; z-index:900; max-width:90%; text-align:center; }
    #msg.err { border-color:var(--red); color:var(--red); }
</style>
<script>
    var $ = function(i) { return document.getElementById(i); };
    var DATI = null, tipoVoce = 'Uscita', aperta = null;

    function esc(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function(c) {
            return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; });
    }
    function msg(t, err) {
        var m = $('msg'); m.textContent = t; m.className = err ? 'err' : ''; m.style.display = 'block';
        clearTimeout(msg._t); msg._t = setTimeout(function() { m.style.display = 'none'; }, err ? 4500 : 2200);
    }
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
    function toggleCollapsible(btn) { btn.parentNode.classList.toggle('collapsible-open'); }
    document.addEventListener('click', function(e) {
        const menu = $('extraMenu'), btn = document.querySelector('.menu-btn');
        if (menu && menu.style.display === 'block' && !menu.contains(e.target) && e.target !== btn) menu.style.display = 'none';
    });

    async function chiama(url, corpo) {
        try {
            var opt = corpo === undefined ? {} : { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(corpo) };
            var res = await fetch(url, opt);
            var j = await res.json();
            if (!res.ok || j.ok === false) { msg(j.errore || 'Errore', true); return null; }
            return j;
        } catch (e) { msg('Connessione non riuscita', true); return null; }
    }

    function disegna() {
        var r = DATI;
        var imp = $('impatto');
        imp.className = r.impatto_pos ? 'pos' : 'neg';
        imp.textContent = r.impatto_segno + ' € ' + r.impatto_str;
        var el = $('elenco'); el.innerHTML = '';
        if (!r.ricorrenze.length) { el.innerHTML = '<div class="vuoto">Nessuna ricorrenza. Tocca + per crearne una.</div>'; return; }
        r.ricorrenze.forEach(function(x) {
            var d = document.createElement('div');
            var conclusa = x.n > 0 && x.saldate >= x.n && !x.prossima;
            d.className = 'ric' + (x.tipo_voce === 'Entrata' ? ' entrata' : '') + (conclusa ? ' conclusa' : '');
            var segno = x.tipo_voce === 'Entrata' ? '+' : '-';
            var pct = x.n > 0 ? Math.min(100, Math.round(x.saldate * 100 / x.n)) : 0;
            var h = '<div class="riga1"><span class="cat">' + esc(x.cat) + '</span>';
            h += '<span class="imp ' + (x.tipo_voce === 'Entrata' ? 'pos' : 'neg') + '">€ ' + segno + esc(x.imp_str) + '</span></div>';
            h += '<div class="meta">' + esc(x.periodo) + ' × ' + x.n + ' · saldate ' + x.saldate + '/' + x.n;
            if (x.prossima) h += ' · prossima ' + esc(x.prossima);
            h += '</div>';
            var extra = [];
            if (x.conto) extra.push('🏦 ' + esc(x.conto));
            if (x.metodo) extra.push('💳 ' + esc(x.metodo));
            if (x.tag) extra.push('🏷️ ' + esc(x.tag));
            if (extra.length) h += '<div class="meta">' + extra.join(' · ') + '</div>';
            h += '<div class="barra"><i style="width:' + pct + '%"></i></div>';
            d.innerHTML = h;
            d.onclick = function() { apriDettaglio(x); };
            el.appendChild(d);
        });
    }
    async function carica() {
        var j = await chiama('/api/ricorrenze/elenco');
        if (!j) return;
        DATI = j; disegna();
    }

    function chiudi() { $('velo').style.display = 'none'; document.body.style.overflow = ''; aperta = null; }
    function mostra(html) { $('scheda').innerHTML = html; $('velo').style.display = 'block'; document.body.style.overflow = 'hidden'; }

    async function apriDettaglio(x) {
        aperta = x;
        var j = await chiama('/api/ricorrenze/dettaglio?id=' + encodeURIComponent(x.id));
        if (!j) return;
        var h = '<h3>' + esc(x.cat) + '</h3>';
        h += '<div class="meta" style="color:var(--text-mid);font-size:0.85em;line-height:1.6;margin-bottom:10px">';
        h += esc(x.periodo) + ' × ' + x.n + ' · € ' + esc(x.imp_str) + ' · ' + esc(x.tipo_voce) + '<br>';
        h += 'Dal ' + esc(x.inizio) + ' al ' + esc(x.fine) + '<br>';
        h += 'Totale € ' + esc(x.totale_str) + ' · contabilizzato € ' + esc(x.contab_str) + ' · residuo € ' + esc(x.residuo_str);
        var extra = [];
        if (x.conto) extra.push('🏦 ' + esc(x.conto));
        if (x.metodo) extra.push('💳 ' + esc(x.metodo));
        if (x.tag) extra.push('🏷️ ' + esc(x.tag));
        if (extra.length) h += '<br>' + extra.join(' · ');
        h += '</div>';
        var etichette = { registrata: '✔️ Registrata', non_registrata: '❌ Non registrata', prevista: 'Prevista' };
        j.date.forEach(function(r) {
            h += '<div class="dt"><span>' + esc(r.data) + '</span><span class="st-' + r.stato + '">' + etichette[r.stato] + '</span><span>€ ' + esc(r.imp_str) + '</span></div>';
        });
        h += '<div class="btns"><button class="btn no" onclick="chiudi()">Chiudi</button><button class="btn del" onclick="elimina()">🗑️ Cancella</button></div>';
        mostra(h);
    }
    var inAttesaConferma = null;
    function apriModalConferma(testo, fn) {
        inAttesaConferma = fn;
        $('modalConfermaText').textContent = testo;
        $('confermaModal').style.display = 'flex';
    }
    function chiudiModalConferma() {
        $('confermaModal').style.display = 'none';
        inAttesaConferma = null;
    }
    function eseguiConferma() {
        var fn = inAttesaConferma;
        chiudiModalConferma();
        if (fn) fn();
    }
    function elimina() {
        if (!aperta) return;
        var r = aperta;
        var testo = 'Cancellare la ricorrenza "' + r.cat + '"?';
        if (r.voci_registrate) testo += '\n\nVerranno eliminate anche ' + r.voci_registrate + ' spese già registrate.';
        apriModalConferma(testo, async function() {
            var j = await chiama('/api/ricorrenze/elimina', { ids: [r.id] });
            if (!j) return;
            chiudi(); msg('Ricorrenza cancellata (' + j.voci + ' spese rimosse)'); carica();
        });
    }

    function impostaTipo(t) {
        tipoVoce = t;
        $('tU').className = 'u' + (t === 'Uscita' ? ' on' : '');
        $('tE').className = 'e' + (t === 'Entrata' ? ' on' : '');
    }
    function apriNuova() {
        if (!DATI) return;
        var h = '<h3>Nuova ricorrenza</h3>';
        h += '<div class="campo"><div class="toggle-t"><button type="button" id="tU" onclick="impostaTipo(\'Uscita\')">Uscita</button><button type="button" id="tE" onclick="impostaTipo(\'Entrata\')">Entrata</button></div></div>';
        h += '<div class="campo"><label>Categoria</label><select id="fCat" onchange="catCambiata()">';
        DATI.categorie.forEach(function(c) { h += '<option value="' + esc(c.nome) + '">' + esc(c.nome) + '</option>'; });
        h += '</select></div>';
        h += '<div class="campo"><label>Descrizione</label><input id="fDesc" type="text" autocomplete="off"></div>';
        h += '<div class="due"><div class="campo"><label>Importo (€)</label><input id="fImp" type="text" inputmode="decimal" placeholder="0,00"></div>';
        h += '<div class="campo"><label>Data inizio</label><input id="fData" type="date" value="' + esc(DATI.oggi) + '"></div></div>';
        h += '<div class="due"><div class="campo"><label>Periodo</label><select id="fPer"><option>Ogni giorno</option><option selected>Ogni mese</option><option>Ogni anno</option></select></div>';
        h += '<div class="campo"><label>Ripetizioni</label><input id="fN" type="number" min="1" max="365" value="12"></div></div>';
        h += '<div class="collapsible-wrap"><button type="button" class="collapsible-toggle" onclick="toggleCollapsible(this)"><span class="arrow">▶</span> Dettagli aggiuntivi</button><div class="collapsible-content">';
        h += '<div class="campo"><label>Conto</label><select id="fConto"><option value="">(nessuno)</option>';
        DATI.conti.forEach(function(c) { h += '<option value="' + esc(c) + '"' + (c === DATI.conto_principale ? ' selected' : '') + '>' + esc(c) + '</option>'; });
        h += '</select></div>';
        h += '<div class="due"><div class="campo"><label>Metodo di pagamento</label><select id="fMet"><option value="">-- Nessuno --</option>';
        DATI.metodi.forEach(function(m) { h += '<option value="' + esc(m) + '">' + esc(m) + '</option>'; });
        h += '</select></div><div class="campo"><label>Tag</label><input id="fTag" type="text" placeholder="es: #casa, vacanza" autocomplete="off"></div></div>';
        h += '</div></div>';
        h += '<div class="btns"><button class="btn no" onclick="chiudi()">Annulla</button><button class="btn ok" onclick="salva()">Salva</button></div>';
        mostra(h);
        impostaTipo('Uscita');
        catCambiata();
    }
    function catCambiata() {
        var nome = $('fCat').value;
        var c = DATI.categorie.find(function(x) { return x.nome === nome; });
        if (c) impostaTipo(c.tipo === 'Entrata' ? 'Entrata' : 'Uscita');
    }
    async function salva() {
        var corpo = {
            tipo_voce: tipoVoce, cat: $('fCat').value, desc: $('fDesc').value,
            imp: $('fImp').value, data_inizio: $('fData').value,
            periodo: $('fPer').value, n: $('fN').value,
            conto: $('fConto').value, metodo: $('fMet').value, tag: $('fTag').value
        };
        var j = await chiama('/api/ricorrenze/crea', corpo);
        if (!j) return;
        chiudi(); msg('Ricorrenza creata: ' + j.generate + ' movimenti generati'); carica();
    }
    document.addEventListener('keydown', function(e) { if (e.key === 'Escape') { if ($('confermaModal').style.display === 'flex') chiudiModalConferma(); else chiudi(); } });
    window.addEventListener('load', function() { applyTheme(localStorage.getItem('theme') || 'dark'); carica(); });
</script>
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
    </div>
    <div class="header-title">🔁 Ricorrenze</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="riepilogo"><span>Impatto mensile stimato (ricorrenze mensili)</span><b id="impatto">–</b></div>
    <div id="elenco"></div>
</main>
<button id="fab" onclick="apriNuova()" title="Nuova ricorrenza">＋</button>
<div id="velo" onclick="if (event.target === this) chiudi()"><div class="scheda" id="scheda"></div></div>
<div id="confermaModal" class="modal-overlay">
    <div class="modal-box">
        <div class="modal-title">⚠️ Conferma</div>
        <div class="modal-text" id="modalConfermaText"></div>
        <div class="modal-btns">
            <button class="m-btn m-cancel" onclick="chiudiModalConferma()">Annulla</button>
            <button class="m-btn m-confirm" onclick="eseguiConferma()">Conferma</button>
        </div>
    </div>
</div>
<div id="msg"></div>
</body>
</html>
"""


def pagina_ricorrenze_web(self):
    return _PAGINA.replace("__ANNO__", str(datetime.date.today().year))
