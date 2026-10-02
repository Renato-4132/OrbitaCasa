#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import datetime
import threading

from moduli.magazzino import (
    CATEGORIE_DEFAULT, UNITA, calcola_stato, stato_scadenza, normalizza_articolo,
    articolo_corrisponde, _num, _fmt_q, _fmt_eur, _oggi, _parse_data,
)

_LOCK = threading.RLock()
LIMITE_QTA = 900.0
LIMITE_PREZZO = 9000.0


def _mw_chiave(codice):
    k = "".join(str(codice or "").split()).replace("-", "").lower()
    return k.lstrip("0") if k.isdigit() else k


def _mw_scad(v):
    v = str(v or "").strip()
    if not v:
        return ""
    try:
        return datetime.datetime.strptime(v, "%Y-%m-%d").strftime("%d-%m-%Y")
    except ValueError:
        pass
    d = _parse_data(v)
    return d.strftime("%d-%m-%Y") if d else None


def _mw_leggi():
    import __main__ as _app
    f = _app.MAGAZZINO_FILE
    categorie, articoli = list(CATEGORIE_DEFAULT), []
    if os.path.exists(f):
        with open(f, "r", encoding="utf-8") as fh:
            d = json.load(fh)
        lista = d.get("articoli", []) if isinstance(d, dict) else d
        if not isinstance(lista, list):
            raise ValueError("Formato non valido")
        if isinstance(d, dict) and "categorie" in d:
            categorie = []
            for c in d.get("categorie", []):
                if c not in categorie:
                    categorie.append(c)
        articoli = [normalizza_articolo(x) for x in lista if isinstance(x, dict) and str(x.get("nome", "")).strip()]
    return f, categorie, articoli


def _mw_salva(f, categorie, articoli):
    os.makedirs(os.path.dirname(f), exist_ok=True)
    tmp = f + ".web.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({"versione": 1, "categorie": categorie, "articoli": articoli}, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, f)


def _mw_json(a):
    stato, tag, ordina = calcola_stato(a)
    sc_stato, _, sc_txt = stato_scadenza(a)
    return {"id": a["id"], "nome": a["nome"], "codice": a.get("codice", ""), "categoria": a.get("categoria", ""),
            "unita": a.get("unita", "pz"), "q": _fmt_q(a["quantita"]), "min": _fmt_q(a.get("qta_min", 0)),
            "max": _fmt_q(a["qta_max"]) if a.get("qta_max") else "",
            "stato": stato, "tag": tag, "scad_stato": sc_stato, "scadenza": sc_txt,
            "scad_data": a.get("scadenza", ""), "scad_iso": (_parse_data(a.get("scadenza")).isoformat() if _parse_data(a.get("scadenza")) else ""),
            "da_ordinare": _fmt_q(ordina) if ordina else ""}


def _mw_notifica_desktop(self):
    fn = getattr(self, "_magazzino_ricarica", None)
    if fn:
        try:
            self.after(0, fn)
        except Exception:
            pass


def magazzino_web_cerca(self, q):
    q = str(q or "").strip()
    if not q:
        return {"ok": True, "trovati": [], "esatto": False}
    try:
        with _LOCK:
            _, _, art = _mw_leggi()
    except Exception as e:
        return {"ok": False, "errore": f"Magazzino non leggibile: {e}"}
    k = _mw_chiave(q)
    esatti = [a for a in art if a.get("codice") and _mw_chiave(a["codice"]) == k]
    if esatti:
        return {"ok": True, "trovati": [_mw_json(a) for a in esatti], "esatto": True}
    if q.isdigit() and len(q) >= 6:
        return {"ok": True, "trovati": [], "esatto": False}
    per_nome = [a for a in art if articolo_corrisponde(a, q)][:12]
    return {"ok": True, "trovati": [_mw_json(a) for a in per_nome], "esatto": False}


def magazzino_web_movimento(self, d):
    tipo = str(d.get("tipo", "")).lower()
    if tipo not in ("carico", "scarico"):
        return {"ok": False, "errore": "Tipo di movimento non valido."}, 400
    try:
        q = _num(d.get("qta", 1))
    except ValueError as ex:
        return {"ok": False, "errore": str(ex)}, 400
    if q <= 0 or q > LIMITE_QTA:
        return {"ok": False, "errore": "Quantità non valida (maggiore di 0, massimo 900)."}, 400
    nota = str(d.get("nota", "")).strip()[:60]
    try:
        with _LOCK:
            f, cat, art = _mw_leggi()
            a = next((x for x in art if x["id"] == str(d.get("id", ""))), None)
            if a is None:
                return {"ok": False, "errore": "Articolo non trovato."}, 404
            delta = q if tipo == "carico" else -q
            if tipo == "scarico" and q > a["quantita"] + 1e-9:
                return {"ok": False, "errore": f"Giacenza insufficiente: disponibili {_fmt_q(a['quantita'])} {a['unita']}."}, 409
            if a["quantita"] + delta > LIMITE_QTA:
                return {"ok": False, "errore": f"La giacenza non può superare 900 («{a['nome']}»)."}, 409
            a["quantita"] = round(a["quantita"] + delta, 3)
            a["data"] = _oggi()
            a["movimenti"].append({"data": _oggi(), "delta": round(delta, 3), "qta": a["quantita"],
                                   "nota": nota or ("Carico (web)" if delta > 0 else "Scarico (web)")})
            a["movimenti"] = a["movimenti"][-100:]
            _mw_salva(f, cat, art)
            risposta = _mw_json(a)
    except Exception as e:
        return {"ok": False, "errore": f"Errore durante il salvataggio: {e}"}, 500
    _mw_notifica_desktop(self)
    avviso = ""
    if risposta["tag"] in ("sotto", "esaurito"):
        avviso = risposta["stato"].lower() + (f" (min {risposta['min']})" if risposta["tag"] == "sotto" else "")
    return {"ok": True, "articolo": risposta, "qta_mov": _fmt_q(q), "avviso": avviso}, 200


def magazzino_web_nuovo(self, d):
    nome = str(d.get("nome", "")).strip()
    if not nome:
        return {"ok": False, "errore": "Il nome dell'articolo è obbligatorio."}, 400
    try:
        q, mn, pr = _num(d.get("quantita", 0)), _num(d.get("min", 0)), _num(d.get("prezzo", 0))
        mx = _num(d.get("max", 0))
    except ValueError as ex:
        return {"ok": False, "errore": str(ex)}, 400
    if min(q, mn, mx, pr) < 0:
        return {"ok": False, "errore": "Quantità, scorte e prezzo non possono essere negativi."}, 400
    if pr > LIMITE_PREZZO:
        return {"ok": False, "errore": "Il prezzo unitario non può superare 9.000 €."}, 400
    if max(q, mn, mx) > LIMITE_QTA:
        return {"ok": False, "errore": "Le quantità non possono superare 900."}, 400
    if mx and mx < mn:
        return {"ok": False, "errore": "La scorta massima non può essere inferiore alla minima (lascia vuoto per nessun massimo)."}, 400
    scad = _mw_scad(d.get("scadenza"))
    if scad is None:
        return {"ok": False, "errore": "Scadenza non valida: usa gg-mm-aaaa oppure lascia vuoto."}, 400
    codice = str(d.get("codice", "")).strip()
    categoria = str(d.get("categoria", "")).strip()
    unita = str(d.get("unita", "pz")).strip() or "pz"
    try:
        with _LOCK:
            f, cat, art = _mw_leggi()
            if codice and any(_mw_chiave(x.get("codice")) == _mw_chiave(codice) for x in art):
                return {"ok": False, "errore": "Esiste già un articolo con questo codice."}, 409
            if not d.get("forza") and any(x["nome"].lower() == nome.lower() and x["categoria"].lower() == categoria.lower() for x in art):
                return {"ok": False, "errore": f"Esiste già «{nome}» in questa categoria.", "conferma": True}, 409
            nuovo = normalizza_articolo(dict(nome=nome, codice=codice, categoria=categoria, unita=unita,
                                             quantita=q, qta_min=mn, qta_max=mx, prezzo=pr, scadenza=scad))
            if q > 0:
                nuovo["movimenti"].append({"data": _oggi(), "delta": q, "qta": q, "nota": "Carico iniziale (web)"})
            art.append(nuovo)
            _mw_salva(f, cat, art)
            risposta = _mw_json(nuovo)
    except Exception as e:
        return {"ok": False, "errore": f"Errore durante il salvataggio: {e}"}, 500
    _mw_notifica_desktop(self)
    return {"ok": True, "articolo": risposta}, 200


def magazzino_web_scorte(self, d):
    try:
        mn, mx = _num(d.get("min", 0)), _num(d.get("max", 0))
    except ValueError as ex:
        return {"ok": False, "errore": str(ex)}, 400
    if min(mn, mx) < 0:
        return {"ok": False, "errore": "Le scorte non possono essere negative."}, 400
    if max(mn, mx) > LIMITE_QTA:
        return {"ok": False, "errore": "Le quantità non possono superare 900."}, 400
    if mx and mx < mn:
        return {"ok": False, "errore": "La scorta massima non può essere inferiore alla minima (lascia vuoto per nessun massimo)."}, 400
    scad = _mw_scad(d.get("scadenza")) if "scadenza" in d else None
    if "scadenza" in d and scad is None:
        return {"ok": False, "errore": "Scadenza non valida: usa gg-mm-aaaa oppure lascia vuoto."}, 400
    try:
        with _LOCK:
            f, cat, art = _mw_leggi()
            a = next((x for x in art if x["id"] == str(d.get("id", ""))), None)
            if a is None:
                return {"ok": False, "errore": "Articolo non trovato."}, 404
            cambia_sc = "scadenza" in d and scad != a.get("scadenza", "")
            if abs(a["qta_min"] - mn) > 1e-9 or abs(a["qta_max"] - mx) > 1e-9 or cambia_sc:
                a["qta_min"], a["qta_max"] = mn, mx
                if cambia_sc:
                    a["scadenza"] = scad
                a["data"] = _oggi()
                _mw_salva(f, cat, art)
            risposta = _mw_json(a)
    except Exception as e:
        return {"ok": False, "errore": f"Errore durante il salvataggio: {e}"}, 500
    _mw_notifica_desktop(self)
    return {"ok": True, "articolo": risposta}, 200


def magazzino_web_riordino(self):
    try:
        with _LOCK:
            _, _, art = _mw_leggi()
    except Exception as e:
        return {"ok": False, "errore": f"Magazzino non leggibile: {e}"}
    righe, tot = [], 0.0
    for a in sorted(art, key=lambda x: (x["categoria"].lower(), x["nome"].lower())):
        stato, tag, ordina = calcola_stato(a)
        if ordina <= 0:
            continue
        costo = ordina * a["prezzo"]
        tot += costo
        righe.append({"id": a["id"], "nome": a["nome"], "categoria": a["categoria"] or "Senza categoria",
                      "unita": a["unita"], "q": _fmt_q(a["quantita"]), "stato": stato, "tag": tag,
                      "ordina": _fmt_q(ordina), "costo": _fmt_eur(costo) if a["prezzo"] else ""})
    return {"ok": True, "righe": righe, "totale": _fmt_eur(tot) if tot else "",
            "data": _oggi(), "con_scorte": sum(1 for a in art if a["qta_min"] > 0 or a["qta_max"] > 0),
            "totale_articoli": len(art)}


_PAGINA = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>📦 StockBox</title>
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
        --gold:#c9a84c; --blue:#63a0f0; --green:#4caf82; --red:#e05a5a; --orange:#e8a23c; --viola:#b86fe0;
        --text:#e8e8e8; --text-dim:#555; --text-mid:#888; --radius-lg:18px;
    }
    :root.light {
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --border-active:rgba(61,127,212,0.5);
        --gold:#b8902a; --blue:#3d7fd4; --green:#3a9068; --red:#cc3333; --orange:#c98314; --viola:#9448c0;
        --text:#1a1a1a; --text-dim:#999; --text-mid:#555;
    }
    * { box-sizing:border-box; margin:0; padding:0; }
    body { font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text); min-height:100vh; padding-bottom:90px; transition:background 0.3s,color 0.3s; }
    header { padding:14px 16px 12px; display:flex; align-items:center; justify-content:center; border-bottom:1px solid var(--border); background:rgba(5,5,5,0.95); backdrop-filter:blur(20px); position:sticky; top:0; z-index:100; }
    :root.light header { background:rgba(245,245,240,0.95); }
    .menu-btn { position:absolute; left:14px; top:50%; transform:translateY(-50%); background:var(--surface3); border:1px solid var(--border); color:var(--gold); width:36px; height:36px; border-radius:10px; font-size:1em; cursor:pointer; display:flex; align-items:center; justify-content:center; }
    .header-title { font-size:1em; font-weight:700; }
    .theme-toggle { position:absolute; right:14px; top:50%; transform:translateY(-50%); background:var(--surface3); border:1px solid var(--border); border-radius:8px; width:34px; height:34px; display:flex; align-items:center; justify-content:center; cursor:pointer; font-size:1em; }
    .nav-dropdown { position:absolute; top:calc(100% + 6px); left:10px; background:var(--surface2); border:1px solid var(--border); border-radius:var(--radius-lg); display:none; z-index:1000; width:270px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.7); }
    .nav-dropdown a { display:flex; align-items:center; gap:10px; padding:10px 16px; text-decoration:none; color:var(--text-mid); border-bottom:1px solid var(--border); font-size:0.87em; }
    .nav-dropdown a:last-child { border-bottom:none; }
    .nav-dropdown a:hover { background:var(--surface3); color:var(--text); }
    .nav-group-btn { display:flex; justify-content:space-between; align-items:center; width:100%; padding:8px 16px; background:none; border:none; font-family:inherit; color:var(--gold); font-size:0.7em; font-weight:700; letter-spacing:1px; text-transform:uppercase; cursor:pointer; opacity:0.85; }
    .nav-group-btn:hover { opacity:1; background:var(--surface3); }
    .nav-group-items { display:none; flex-direction:column; }
    .nav-group-items.open { display:flex; }
    main { padding:14px; max-width:480px; margin:0 auto; }
    .seg { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:12px; }
    .seg button { padding:16px 8px; border-radius:14px; border:2px solid var(--border); background:var(--surface); color:var(--text-mid); font-family:inherit; font-size:1.05em; font-weight:700; cursor:pointer; }
    .seg button.on.c { border-color:var(--green); color:var(--green); background:rgba(76,175,130,0.12); }
    .seg button.on.s { border-color:var(--red); color:var(--red); background:rgba(224,90,90,0.12); }
    .card { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-lg); padding:14px; margin-bottom:12px; }
    .qrow { display:flex; align-items:center; gap:8px; }
    .qrow label { color:var(--text-mid); font-size:0.85em; margin-right:auto; }
    .qrow input { width:90px; text-align:center; font-size:1.3em; font-weight:700; }
    input, select { background:var(--surface3); border:1px solid var(--border); color:var(--text); border-radius:10px; padding:12px; font-family:inherit; font-size:1em; width:100%; }
    input:focus, select:focus { outline:none; border-color:var(--border-active); }
    .step { width:46px; height:46px; border-radius:12px; border:1px solid var(--border); background:var(--surface3); color:var(--text); font-size:1.4em; cursor:pointer; flex:none; }
    .chk { display:flex; align-items:center; gap:10px; margin-top:12px; color:var(--text-mid); font-size:0.9em; }
    .chk input { width:20px; height:20px; flex:none; }
    .btn { display:block; width:100%; padding:14px; border-radius:12px; border:1px solid var(--border); background:var(--surface3); color:var(--text); font-family:inherit; font-size:1em; font-weight:700; cursor:pointer; }
    .btn.verde { background:var(--green); border-color:var(--green); color:#fff; }
    .btn.rosso { background:var(--red); border-color:var(--red); color:#fff; }
    .btn.blu { background:var(--blue); border-color:var(--blue); color:#fff; }
    .btns { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:12px; }
    .cerca { display:flex; gap:8px; margin-bottom:12px; }
    .cerca .btn { width:auto; padding:0 18px; }
    #camWrap { display:none; position:relative; margin-bottom:12px; border-radius:var(--radius-lg); overflow:hidden; background:#000; }
    #video { width:100%; display:block; max-height:300px; object-fit:cover; }
    #mirino { position:absolute; left:12%; right:12%; top:50%; height:2px; background:rgba(224,90,90,0.85); box-shadow:0 0 10px rgba(224,90,90,0.8); }
    .hint { font-size:0.8em; color:var(--text-mid); margin:-4px 0 12px; line-height:1.4; }
    .art-nome { font-size:1.15em; font-weight:800; }
    .art-sub { color:var(--text-mid); font-size:0.85em; margin:2px 0 10px; }
    .art-q { margin-bottom:10px; }
    .art-q .n { font-size:2.2em; font-weight:800; }
    .art-q .u { color:var(--text-mid); font-size:1em; }
    .badge { display:inline-block; padding:3px 10px; border-radius:20px; font-size:0.75em; font-weight:700; margin:0 6px 10px 0; border:1px solid currentColor; }
    .badge.ok { color:var(--green); } .badge.sotto { color:var(--orange); } .badge.esaurito { color:var(--red); }
    .badge.eccesso { color:var(--blue); } .badge.scadenza { color:var(--viola); }
    .esito { padding:10px 12px; border-radius:10px; font-weight:700; font-size:0.92em; }
    .esito.ok { background:rgba(76,175,130,0.15); color:var(--green); }
    .esito.warn { background:rgba(232,162,60,0.15); color:var(--orange); }
    .riga { display:flex; justify-content:space-between; gap:10px; width:100%; padding:13px 14px; margin-bottom:6px; border-radius:12px; border:1px solid var(--border); background:var(--surface); color:var(--text); font-family:inherit; font-size:0.95em; cursor:pointer; text-align:left; }
    .riga .r-q { color:var(--text-mid); flex:none; }
    .campo { margin-bottom:10px; }
    .campo label { display:block; font-size:0.78em; color:var(--text-mid); margin-bottom:4px; }
    .due { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
    .logriga { display:flex; align-items:center; gap:10px; padding:8px 0; border-bottom:1px solid var(--border); font-size:0.9em; }
    .logriga:last-child { border-bottom:none; }
    .l-t { font-weight:800; min-width:44px; } .l-t.carico { color:var(--green); } .l-t.scarico { color:var(--red); }
    .l-n { flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .mini { background:var(--surface3); border:1px solid var(--border); color:var(--text); border-radius:8px; width:34px; height:34px; cursor:pointer; }
    h3 { font-size:0.85em; color:var(--gold); margin-bottom:6px; }
    #suggNuovo { position:absolute; left:0; right:0; top:100%; z-index:50; margin-top:4px; background:var(--surface2); border:1px solid var(--border-active); border-radius:12px; box-shadow:0 12px 30px rgba(0,0,0,0.5); max-height:260px; overflow-y:auto; }
    #suggNuovo:empty { display:none; }
    #catBox { position:absolute; left:0; top:100%; z-index:60; margin-top:4px; width:max-content; min-width:100%; max-width:90vw; background:var(--surface2); border:1px solid var(--border-active); border-radius:12px; box-shadow:0 12px 30px rgba(0,0,0,0.5); max-height:240px; overflow-y:auto; }
    #catBox:empty { display:none; }
    #catBox .riga { margin:0; border:none; border-bottom:1px solid var(--border); border-radius:0; background:transparent; }
    #catBox .riga:last-child { border-bottom:none; }
    #suggNuovo .hint { margin:0; padding:8px 14px; border-bottom:1px solid var(--border); }
    #suggNuovo .riga { margin:0; border:none; border-bottom:1px solid var(--border); border-radius:0; background:transparent; }
    #suggNuovo .riga:last-child { border-bottom:none; }
    .tabs { display:grid; grid-template-columns:1fr 1fr; gap:0; margin-bottom:14px; border-bottom:1px solid var(--border); }
    .tabs button { padding:12px 8px; background:none; border:none; border-bottom:3px solid transparent; color:var(--text-mid); font-family:inherit; font-size:0.95em; font-weight:700; cursor:pointer; }
    .tabs button.on { color:var(--gold); border-bottom-color:var(--gold); }
    .scorte { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:10px; padding-top:10px; border-top:1px solid var(--border); }
    .scorte .campo { margin:0; }
    .scorte .tutta { grid-column:1 / -1; }
    .linkbtn { background:none; border:none; color:var(--blue); font-family:inherit; font-size:0.85em; font-weight:700; cursor:pointer; padding:8px 0 0; }
    .sp-top { display:flex; justify-content:space-between; align-items:baseline; margin-bottom:10px; }
    .sp-top .tot { font-size:1.4em; font-weight:800; }
    .sp-top .sub { color:var(--text-mid); font-size:0.8em; }
    .cat { font-size:0.75em; font-weight:700; color:var(--gold); margin:14px 0 6px; letter-spacing:0.5px; }
    .spesa { display:flex; align-items:center; gap:12px; width:100%; padding:12px 14px; margin-bottom:6px; border-radius:12px; border:1px solid var(--border); background:var(--surface); color:var(--text); font-family:inherit; font-size:0.97em; cursor:pointer; text-align:left; }
    .spesa .box { width:24px; height:24px; border-radius:7px; border:2px solid var(--text-dim); flex:none; display:flex; align-items:center; justify-content:center; font-size:0.9em; color:transparent; }
    .spesa .nm { flex:1; } .spesa .qq { font-weight:800; flex:none; }
    .spesa.fatto { opacity:0.45; } .spesa.fatto .nm { text-decoration:line-through; }
    .spesa.fatto .box { background:var(--green); border-color:var(--green); color:#fff; }
    .vuoto { text-align:center; color:var(--text-mid); font-size:0.92em; line-height:1.5; padding:26px 10px; }
    #msg { display:none; position:fixed; left:12px; right:12px; bottom:14px; max-width:456px; margin:0 auto; padding:13px 16px; border-radius:12px; font-weight:700; font-size:0.92em; z-index:2000; box-shadow:0 10px 30px rgba(0,0,0,0.5); }
    #msg.ok { background:var(--green); color:#fff; } #msg.err { background:var(--red); color:#fff; } #msg.warn { background:var(--orange); color:#fff; }
</style>
<script>
    const CATEGORIE = __CATJSON__;
    const UNITA = __UNITAJSON__;
    const $ = id => document.getElementById(id);
    let modo = 'carico', stream = null, reader = null, ciclo = null, cand = {}, recente = {c:'', t:0}, tMostra = 0, gen = 0, occupato = false, log = [];

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

    function el(t, c, x) { const e = document.createElement(t); if (c) e.className = c; if (x !== undefined) e.textContent = x; return e; }
    function msg(t, k) {
        const m = $('msg'); m.textContent = t; m.className = k || 'ok'; m.style.display = 'block';
        clearTimeout(msg.t); msg.t = setTimeout(() => { m.style.display = 'none'; }, k === 'err' ? 6000 : 3500);
    }
    async function api(url, body) {
        const opt = body ? {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)} : {};
        if (window.AbortSignal && AbortSignal.timeout) opt.signal = AbortSignal.timeout(10000);
        const res = await fetch(url, opt);
        if (res.redirected || !(res.headers.get('content-type') || '').includes('json')) { location.href = '/login?expired=1'; throw new Error('sessione'); }
        return res.json();
    }
    function errRete(e) { if (e.message !== 'sessione') msg('Connessione al server non riuscita.', 'err'); }

    function setModo(m) {
        modo = m; localStorage.setItem('mag_modo', m);
        $('bCarico').classList.toggle('on', m === 'carico');
        $('bScarico').classList.toggle('on', m === 'scarico');
        $('bCerca').className = 'btn ' + (m === 'carico' ? 'verde' : 'rosso');
        $('bCerca').textContent = m === 'carico' ? '➕ Carica' : '➖ Scarica';
        const r = document.querySelector('#risultato .btn');
        if (r) { r.className = 'btn ' + (m === 'carico' ? 'verde' : 'rosso'); r.textContent = m === 'carico' ? '➕ Registra carico' : '➖ Registra scarico'; }
    }
    function step(d) {
        let n = parseFloat(($('qta').value || '1').replace(',', '.'));
        if (isNaN(n)) n = 1;
        $('qta').value = String(Math.max(0, Math.round((n + d) * 1000) / 1000)).replace('.', ',');
    }
    function setVista(v) {
        $('vistaScan').style.display = v === 'scan' ? 'block' : 'none';
        $('vistaSpesa').style.display = v === 'spesa' ? 'block' : 'none';
        $('tScan').classList.toggle('on', v === 'scan'); $('tSpesa').classList.toggle('on', v === 'spesa');
        if (v === 'spesa') { fermaCamera(); caricaSpesa(); }
    }
    let spesa = null;
    function leggiSpunte() { try { return JSON.parse(localStorage.getItem('mag_spunte') || '[]'); } catch (e) { return []; } }
    function salvaSpunte(l) { try { localStorage.setItem('mag_spunte', JSON.stringify(l)); } catch (e) {} }
    async function caricaSpesa() {
        try {
            const r = await api('/api/magazzino/riordino');
            if (!r.ok) { msg(r.errore, 'err'); return; }
            spesa = r;
            const ids = r.righe.map(x => x.id); salvaSpunte(leggiSpunte().filter(i => ids.includes(i)));
            disegnaSpesa();
        } catch (e) { errRete(e); }
    }
    function disegnaSpesa() {
        const r = spesa, box = $('listaSpesa'); box.innerHTML = '';
        const sp = leggiSpunte(), da = r.righe.filter(x => !sp.includes(x.id)).length;
        $('spTot').textContent = r.totale || '—';
        $('spSub').textContent = r.righe.length ? (da + ' da riordinare su ' + r.righe.length + ' articoli') : 'Nessun articolo da riordinare';
        $('spAzioni').style.display = r.righe.length ? 'grid' : 'none';
        if (!r.righe.length) {
            const v = el('div', 'vuoto');
            v.textContent = r.con_scorte === 0
                ? 'Nessun articolo ha una scorta minima, quindi la lista resta vuota. Imposta Min (e Max) dalla scheda articolo in Scansiona con ⚙️ Scorte e scadenza.'
                : 'Tutto a posto: nessun articolo è sotto scorta.';
            box.appendChild(v); return;
        }
        let cat = null;
        r.righe.forEach(x => {
            if (x.categoria !== cat) { cat = x.categoria; box.appendChild(el('div', 'cat', cat)); }
            const b = el('button', 'spesa' + (sp.includes(x.id) ? ' fatto' : ''));
            b.appendChild(el('span', 'box', '✓')); b.appendChild(el('span', 'nm', x.nome));
            b.appendChild(el('span', 'qq', x.ordina + ' ' + x.unita));
            b.onclick = () => { const l = leggiSpunte(), i = l.indexOf(x.id); if (i >= 0) l.splice(i, 1); else l.push(x.id); salvaSpunte(l); disegnaSpesa(); };
            box.appendChild(b);
        });
    }
    function testoSpesa() {
        const sp = leggiSpunte(), righe = spesa.righe.filter(x => !sp.includes(x.id));
        if (!righe.length) return '';
        let t = '📋 Riordino — ' + spesa.data + '\\n', cat = null;
        righe.forEach(x => { if (x.categoria !== cat) { cat = x.categoria; t += '\\n' + cat + '\\n'; } t += '• ' + x.nome + ': ' + x.ordina + ' ' + x.unita + '\\n'; });
        return t.trim();
    }
    async function condividiSpesa() {
        const t = testoSpesa();
        if (!t) { msg('Niente da condividere: tutto spuntato.', 'warn'); return; }
        try {
            if (navigator.share) { await navigator.share({text:t}); return; }
            await navigator.clipboard.writeText(t); msg('Lista copiata negli appunti.', 'ok');
        } catch (e) { if (e && e.name === 'AbortError') return; msg('Condivisione non disponibile su questo browser.', 'err'); }
    }
    function azzeraSpunte() { salvaSpunte([]); disegnaSpesa(); }

    function apriScorte(a, card, btn) {
        if (card.querySelector('.scorte')) return;
        btn.style.display = 'none';
        const f = el('div', 'scorte');
        const mk = (lbl, val, tipo, tutta) => { const c = el('div', 'campo' + (tutta ? ' tutta' : '')); c.appendChild(el('label', '', lbl)); const i = document.createElement('input'); i.type = tipo || 'text'; if (!tipo) i.inputMode = 'decimal'; i.value = val; c.appendChild(i); f.appendChild(c); return i; };
        const iMin = mk('Scorta min', a.min === '0' ? '' : a.min), iMax = mk('Scorta max', a.max);
        const iScad = mk('Scadenza (vuoto = nessuna)', a.scad_iso, 'date', true);
        const ok = el('button', 'btn verde tutta', '💾 Salva');
        ok.onclick = async () => {
            try {
                const r = await api('/api/magazzino/scorte', {id:a.id, min:iMin.value, max:iMax.value, scadenza:iScad.value});
                if (!r.ok) { msg(r.errore, 'err'); return; }
                pulisci(); mostra(r.articolo, {k:'ok', t:'Articolo aggiornato.'});
            } catch (e) { errRete(e); }
        };
        f.appendChild(ok); card.appendChild(f); iMin.focus();
    }
    function pulisci() { $('risultato').innerHTML = ''; $('elenco').innerHTML = ''; $('suggNuovo').innerHTML = ''; $('catBox').innerHTML = ''; $('nuovo').style.display = 'none'; }

    async function cerca(q, auto, live) {
        q = (q || '').trim();
        if (!q || occupato) return;
        occupato = true;
        try {
            const r = await api('/api/magazzino/cerca?q=' + encodeURIComponent(q));
            if (!r.ok) { msg(r.errore, 'err'); return; }
            if (r.trovati.length === 0 && live) { nonTrovato(q); return; }
            pulisci();
            if (r.trovati.length === 0) { apriNuovo(q); return; }
            if (r.trovati.length === 1) {
                if (r.esatto && auto && $('auto').checked) await registra(r.trovati[0]); else mostra(r.trovati[0]);
                return;
            }
            mostraElenco(r.trovati);
        } catch (e) { errRete(e); }
        finally { occupato = false; if (auto) $('codice').value = ''; }
    }

    function nonTrovato(q) {
        if (navigator.vibrate) navigator.vibrate([80, 60, 80]);
        if (modo === 'scarico') { msg('Codice ' + q + ' non presente in magazzino: impossibile scaricare.', 'err'); return; }
        // risultato appena registrato, oppure modulo gia' aperto: non toccare nulla
        if ($('risultato').firstChild && Date.now() - tMostra < 10000) { msg('Codice ' + q + ' non presente.', 'warn'); return; }
        if ($('nuovo').style.display === 'block') return;
        fermaCamera(); pulisci(); apriNuovo(q);
    }
    function mostra(a, esito) {
        tMostra = Date.now();
        const box = $('risultato'); box.innerHTML = '';
        const c = el('div', 'card');
        c.appendChild(el('div', 'art-nome', a.nome));
        c.appendChild(el('div', 'art-sub', [a.categoria, a.codice, a.scad_data ? 'Scad. ' + a.scad_data : ''].filter(Boolean).join(' • ') || 'Senza categoria'));
        const q = el('div', 'art-q'); q.appendChild(el('span', 'n', a.q)); q.appendChild(el('span', 'u', ' ' + a.unita)); c.appendChild(q);
        c.appendChild(el('span', 'badge ' + (a.tag || 'ok'), a.stato));
        if (a.scad_stato) c.appendChild(el('span', 'badge ' + (a.scad_stato === 'Scaduto' ? 'esaurito' : 'scadenza'), a.scadenza));
        if (esito) c.appendChild(el('div', 'esito ' + esito.k, esito.t));
        else {
            const b = el('button', 'btn ' + (modo === 'carico' ? 'verde' : 'rosso'), modo === 'carico' ? '➕ Registra carico' : '➖ Registra scarico');
            b.onclick = () => registra(a); c.appendChild(b);
        }
        const sb = el('button', 'linkbtn', '⚙️ Scorte e scadenza (min ' + a.min + (a.max ? ', max ' + a.max : '') + ')');
        sb.onclick = () => apriScorte(a, c, sb); c.appendChild(sb);
        box.appendChild(c);
    }
    function mostraElenco(lista) {
        const box = $('elenco'); box.innerHTML = '';
        lista.forEach(a => {
            const b = el('button', 'riga'); b.appendChild(el('span', 'r-n', a.nome + (a.codice ? '  (' + a.codice + ')' : '')));
            b.appendChild(el('span', 'r-q', a.q + ' ' + a.unita)); b.onclick = () => { pulisci(); mostra(a); }; box.appendChild(b);
        });
    }

    async function registra(a) {
        const tipo = modo, raw = $('qta').value;
        try {
            const r = await api('/api/magazzino/movimento', {id:a.id, tipo:tipo, qta:raw});
            if (!r.ok) { mostra(a); msg(r.errore, 'err'); if (navigator.vibrate) navigator.vibrate([80, 60, 80]); return; }
            if (navigator.vibrate) navigator.vibrate(40);
            pulisci();
            mostra(r.articolo, {k:r.avviso ? 'warn' : 'ok', t:(tipo === 'carico' ? 'Caricati ' : 'Scaricati ') + r.qta_mov + ' ' + r.articolo.unita + (r.avviso ? ' — ' + r.avviso : '')});
            log.unshift({id:a.id, nome:a.nome, tipo:tipo, q:r.qta_mov, raw:raw}); log.length = Math.min(log.length, 10); ridisegnaLog();
            $('qta').value = '1';
        } catch (e) { errRete(e); }
    }
    async function annulla(i) {
        const m = log[i], inv = m.tipo === 'carico' ? 'scarico' : 'carico';
        try {
            const r = await api('/api/magazzino/movimento', {id:m.id, tipo:inv, qta:m.raw, nota:'Annullamento (web)'});
            if (!r.ok) { msg(r.errore, 'err'); return; }
            log.splice(i, 1); ridisegnaLog(); pulisci(); msg('Movimento annullato.', 'ok');
        } catch (e) { errRete(e); }
    }
    function ridisegnaLog() {
        const box = $('log'); box.innerHTML = ''; $('logWrap').style.display = log.length ? 'block' : 'none';
        log.forEach((m, i) => {
            const r = el('div', 'logriga'); r.appendChild(el('span', 'l-t ' + m.tipo, (m.tipo === 'carico' ? '+' : '−') + m.q));
            r.appendChild(el('span', 'l-n', m.nome));
            const b = el('button', 'mini', '↩'); b.title = 'Annulla'; b.onclick = () => annulla(i); r.appendChild(b); box.appendChild(r);
        });
    }

    function apriNuovo(q) {
        const eCodice = /\\d/.test(q) && !/\\s/.test(q);
        $('nCodice').value = eCodice ? q : ''; $('nNome').value = eCodice ? '' : q;
        $('nQta').value = modo === 'carico' ? $('qta').value : '0';
        $('nuovo').style.display = 'block'; $('nNome').focus();
        if (q) msg(eCodice ? 'Codice non presente: crea l\\'articolo.' : 'Nessun articolo trovato: puoi crearlo.', 'warn');
    }
    let tSugg = null, nSugg = 0;
    document.addEventListener('click', e => { if (!e.target.closest('#suggNuovo') && e.target.id !== 'nNome' && e.target.id !== 'nCodice') $('suggNuovo').innerHTML = ''; });
    document.addEventListener('click', e => { if (e.target.id !== 'nCat' && !e.target.closest('#catBox')) $('catBox').innerHTML = ''; });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') { $('suggNuovo').innerHTML = ''; $('catBox').innerHTML = ''; } });
    function mostraCategorie() {
        const box = $('catBox'), t = $('nCat').value.trim().toLowerCase();
        box.innerHTML = '';
        CATEGORIE.filter(c => !t || c.toLowerCase().includes(t)).forEach(c => {
            const b = el('button', 'riga', c); b.type = 'button';
            b.onclick = () => { $('nCat').value = c; box.innerHTML = ''; };
            box.appendChild(b);
        });
    }
    function suggerisciEsistenti() {
        clearTimeout(tSugg);
        tSugg = setTimeout(async () => {
            const mio = ++nSugg, box = $('suggNuovo');
            const qs = [$('nNome').value.trim(), $('nCodice').value.trim()].filter(s => s.length >= 2);
            box.innerHTML = '';
            if (!qs.length) return;
            try {
                const ris = await Promise.all(qs.map(q => api('/api/magazzino/cerca?q=' + encodeURIComponent(q))));
                if (mio !== nSugg) return;
                const viste = {}, lista = [];
                ris.forEach(r => (r.ok ? r.trovati : []).forEach(a => { if (!viste[a.id]) { viste[a.id] = 1; lista.push(a); } }));
                const err = ris.find(r => !r.ok);
                if (!lista.length) { box.appendChild(el('div', 'hint', err ? 'Ricerca non riuscita: ' + err.errore : 'Nessun articolo simile in magazzino: puoi crearlo.')); return; }
                box.appendChild(el('div', 'hint', 'Già presenti in magazzino: tocca per usarlo invece di crearne uno nuovo.'));
                lista.slice(0, 6).forEach(a => {
                    const b = el('button', 'riga');
                    b.appendChild(el('span', 'r-n', a.nome + (a.codice ? '  (' + a.codice + ')' : '')));
                    b.appendChild(el('span', 'r-q', a.q + ' ' + a.unita));
                    b.onclick = () => { pulisci(); mostra(a); };
                    box.appendChild(b);
                });
            } catch (e) { if (mio === nSugg && e.message !== 'sessione') box.appendChild(el('div', 'hint', 'Ricerca non riuscita: ' + e.message)); }
        }, 300);
    }
    async function salvaNuovo(forza) {
        const corpo = {nome:$('nNome').value, codice:$('nCodice').value, categoria:$('nCat').value, unita:$('nUnita').value,
                       quantita:$('nQta').value, min:$('nMin').value, max:$('nMax').value, prezzo:$('nPrezzo').value, scadenza:$('nScad').value, forza:!!forza};
        try {
            const r = await api('/api/magazzino/nuovo', corpo);
            if (!r.ok) {
                if (r.conferma && confirm(r.errore + '\\nAggiungerlo comunque?')) return salvaNuovo(true);
                msg(r.errore, 'err'); return;
            }
            const nc = corpo.categoria.trim(); if (nc && !CATEGORIE.some(x => x.toLowerCase() === nc.toLowerCase())) CATEGORIE.push(nc);
            pulisci(); mostra(r.articolo, {k:'ok', t:'Articolo creato.'});
            ['nNome', 'nCodice', 'nMin', 'nMax', 'nPrezzo', 'nScad'].forEach(i => { $(i).value = ''; });
        } catch (e) { errRete(e); }
    }

    function trovato(c) {
        c = String(c || '').trim();
        if (!c || occupato) return;
        const t = Date.now();
        if (t - tMostra < 3500) return;  // appena mostrato un risultato: ignora altre letture
        // stesso codice ancora davanti alla camera: ignora finche' non sparisce per 4 s
        if (c === recente.c && t - recente.t < 4000) { recente.t = t; return; }
        // conferma: serve leggerlo 2 volte entro 2 s (scarta le letture sbagliate)
        Object.keys(cand).forEach(k => { if (t - cand[k].t > 2000) delete cand[k]; });
        const e = cand[c] || (cand[c] = {n:0, t:t});
        e.n++; e.t = t;
        if (e.n < 2) return;
        cand = {}; recente = {c:c, t:t};
        fermaCamera();  // camera spenta appena letto il codice
        $('codice').value = c; cerca(c, true, true);
    }
    function caricaZXing() {
        if (window.ZXing) return Promise.resolve();
        return new Promise((ok, ko) => {
            const s = document.createElement('script');
            s.src = 'https://cdn.jsdelivr.net/npm/@zxing/library@0.21.3/umd/index.min.js';
            s.onload = ok; s.onerror = () => { msg('Lettore non caricabile (serve internet). Digita il codice.', 'err'); ko(new Error('zxing')); };
            document.head.appendChild(s);
        });
    }
    async function avviaCamera() {
        if (stream || reader) { fermaCamera(); return; }
        if (!window.isSecureContext || !navigator.mediaDevices) {
            msg('La fotocamera live richiede HTTPS. Usa 🖼️ Foto o digita il codice.', 'err'); return;
        }
        $('camWrap').style.display = 'block'; $('bCam').textContent = '⏹ Ferma';
        try {
            if ('BarcodeDetector' in window) {
                stream = await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:'environment'}}, audio:false});
                const v = $('video'); v.srcObject = stream; await v.play();
                const sup = await BarcodeDetector.getSupportedFormats();
                const det = new BarcodeDetector({formats:['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128', 'code_39', 'itf', 'qr_code', 'data_matrix'].filter(f => sup.includes(f))});
                const mio = ++gen;
                const giro = async () => {
                    if (!stream || mio !== gen) return;
                    try { const r = await det.detect(v); if (r.length) trovato(r[0].rawValue); } catch (e) {}
                    if (stream && mio === gen) ciclo = setTimeout(giro, 250);
                };
                giro();
            } else {
                await caricaZXing();
                reader = new ZXing.BrowserMultiFormatReader();
                reader.decodeFromConstraints({video:{facingMode:'environment'}}, $('video'), res => { if (res) trovato(res.getText()); });
            }
        } catch (e) { fermaCamera(); msg('Fotocamera non accessibile: controlla i permessi del browser.', 'err'); }
    }
    function fermaCamera() {
        gen++; clearTimeout(ciclo);
        if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
        if (reader) { try { reader.reset(); } catch (e) {} reader = null; }
        $('video').srcObject = null; $('camWrap').style.display = 'none'; $('bCam').textContent = '📷 Scansiona';
    }
    async function daFoto(file) {
        if (!file) return;
        let codice = null;
        try {
            if ('BarcodeDetector' in window) {
                const r = await new BarcodeDetector().detect(await createImageBitmap(file));
                if (r.length) codice = r[0].rawValue;
            } else {
                await caricaZXing();
                const url = URL.createObjectURL(file);
                try { codice = (await new ZXing.BrowserMultiFormatReader().decodeFromImageUrl(url)).getText(); }
                finally { URL.revokeObjectURL(url); }
            }
        } catch (e) {}
        $('foto').value = '';
        if (codice) { $('codice').value = codice; cerca(codice, true); } else msg('Nessun codice riconosciuto nella foto.', 'err');
    }

    document.addEventListener('DOMContentLoaded', function() {
        applyTheme(localStorage.getItem('theme') || 'dark');
        $('auto').checked = localStorage.getItem('mag_auto') !== '0';
        $('auto').onchange = () => localStorage.setItem('mag_auto', $('auto').checked ? '1' : '0');
        setModo(localStorage.getItem('mag_modo') === 'scarico' ? 'scarico' : 'carico');
        UNITA.forEach(u => { const o = el('option', '', u); o.value = u; $('nUnita').appendChild(o); });
        if (!window.isSecureContext) $('hintHttps').style.display = 'block';
        $('formCerca').addEventListener('submit', function(ev) {
            ev.preventDefault(); const v = $('codice').value; cerca(v, true);
            $('codice').value = ''; if (!('ontouchstart' in window)) $('codice').focus();
        });
        $('foto').addEventListener('change', e => daFoto(e.target.files[0]));
        window.addEventListener('pagehide', fermaCamera);
    });
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
                <a href="/utenze?anno=__ANNO__">💧 Utenze</a>
                <a href="/consultazione_supermercati">🛒 Gestione Supermercati</a>
                <a href="/magazzino_web">📦 StockBox (Magazzino)</a>
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
    <div class="header-title">📦 StockBox</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="tabs">
        <button id="tScan" class="on" onclick="setVista('scan')">📷 Scansiona</button>
        <button id="tSpesa" onclick="setVista('spesa')">📋 Riordino</button>
    </div>
    <div id="vistaScan">
    <div class="seg">
        <button id="bCarico" class="c" onclick="setModo('carico')">➕ Carico</button>
        <button id="bScarico" class="s" onclick="setModo('scarico')">➖ Scarico</button>
    </div>
    <div class="card">
        <div class="qrow">
            <label for="qta">Quantità</label>
            <button class="step" onclick="step(-1)">−</button>
            <input id="qta" type="text" inputmode="decimal" value="1">
            <button class="step" onclick="step(1)">+</button>
        </div>
        <label class="chk"><input type="checkbox" id="auto"> Registra subito alla scansione</label>
    </div>
    <div class="btns">
        <button class="btn blu" id="bCam" onclick="avviaCamera()">📷 Scansiona</button>
        <button class="btn" onclick="document.getElementById('foto').click()">🖼️ Foto</button>
    </div>
    <input type="file" id="foto" accept="image/*" capture="environment" style="display:none">
    <div id="hintHttps" class="hint" style="display:none">Su questo indirizzo (HTTP) la fotocamera live è bloccata dal browser: usa 🖼️ Foto, un lettore barcode o digita il codice. Con HTTPS la scansione live funziona.</div>
    <div id="camWrap"><video id="video" playsinline muted></video><div id="mirino"></div></div>
    <form id="formCerca" class="cerca">
        <input id="codice" type="text" autocomplete="off" autocapitalize="off" placeholder="Codice a barre o articolo">
        <button class="btn verde" id="bCerca" type="submit">➕ Carica</button>
    </form>
    <button class="btn" style="margin-bottom:12px" onclick="pulisci(); apriNuovo('')">➕ Nuovo articolo</button>
    <div id="risultato"></div>
    <div id="elenco"></div>
    <div id="nuovo" class="card" style="display:none">
        <h3>Nuovo articolo</h3>
        <div class="campo" style="position:relative"><label>Articolo</label><input id="nNome" type="text" autocomplete="off" oninput="suggerisciEsistenti()"><div id="suggNuovo"></div></div>
        <div class="campo"><label>Codice a barre</label><input id="nCodice" type="text" autocomplete="off" oninput="suggerisciEsistenti()"></div>
        <div class="due">
            <div class="campo" style="position:relative"><label>Categoria</label><input id="nCat" type="text" autocomplete="off" onfocus="mostraCategorie()" onclick="mostraCategorie()" oninput="mostraCategorie()"><div id="catBox"></div></div>
            <div class="campo"><label>Unità</label><select id="nUnita"></select></div>
        </div>
        <div class="due">
            <div class="campo"><label>Quantità iniziale</label><input id="nQta" type="text" inputmode="decimal" value="0"></div>
            <div class="campo"><label>Scorta minima</label><input id="nMin" type="text" inputmode="decimal" placeholder="0"></div>
        </div>
        <div class="due">
            <div class="campo"><label>Scorta massima</label><input id="nMax" type="text" inputmode="decimal" placeholder="nessuna"></div>
            <div class="campo"><label>Prezzo unitario (€)</label><input id="nPrezzo" type="text" inputmode="decimal" placeholder="0,00"></div>
        </div>
        <div class="campo"><label>Scadenza (facoltativa)</label><input id="nScad" type="date"></div>
        <button class="btn verde" onclick="salvaNuovo(false)">💾 Crea articolo</button>
    </div>
    <div id="logWrap" class="card" style="display:none"><h3>Ultimi movimenti</h3><div id="log"></div></div>
    </div>
    <div id="vistaSpesa" style="display:none">
        <div class="sp-top"><div><div class="tot" id="spTot">—</div><div class="sub" id="spSub"></div></div>
            <button class="mini" style="width:auto;padding:0 12px" onclick="caricaSpesa()" title="Aggiorna">↻ Aggiorna</button></div>
        <div id="spAzioni" class="btns" style="display:none">
            <button class="btn blu" onclick="condividiSpesa()">📤 Condividi</button>
            <button class="btn" onclick="azzeraSpunte()">Azzera spunte</button>
        </div>
        <div id="listaSpesa"></div>
    </div>
</main>
<div id="msg"></div>
</body>
</html>
"""


def pagina_magazzino_web(self):
    try:
        with _LOCK:
            _, categorie, art = _mw_leggi()
        tutte = sorted(set(categorie) | {a["categoria"] for a in art if a["categoria"]}, key=str.lower)
    except Exception:
        tutte = sorted(CATEGORIE_DEFAULT, key=str.lower)
    cat_json = json.dumps(tutte, ensure_ascii=False).replace("</", "<\\/")
    unita_json = json.dumps(UNITA, ensure_ascii=False)
    return (_PAGINA.replace("__CATJSON__", cat_json)
                   .replace("__UNITAJSON__", unita_json)
                   .replace("__ANNO__", str(datetime.date.today().year)))
