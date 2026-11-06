#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import threading

_LOCK = threading.Lock()
MAX_PROPOSTE = 500

_NUM = r"(\d{1,3}(?:[.,\u00a0\u202f]\d{3})+(?:[.,]\d{1,2})?|\d+(?:[.,]\d{1,2})?)"
RE_IMPORTO = [
    re.compile(r"(?:€|eur(?:o)?\b)\s*" + _NUM, re.I),
    re.compile(_NUM + r"\s*(?:€|eur(?:o)?\b)", re.I),
]
RE_SALDO = re.compile(r"saldo|disponibil|residuo|plafond|limite", re.I)
RE_SOLDI = re.compile(r"€|\beur(?:o)?\b", re.I)

USCITA = ("pagament", "pagat", "addebit", "acquist", "prelievo", "hai pagato", "hai speso",
          "speso", "bonifico inviato", "bonifico disposto", "ricarica", "paypal",
          "transazione", "carta", "pos ",
          "payment", "paid", "purchase", "spent", "debited")
ENTRATA = ("accredit", "hai ricevuto", "ricevuto", "bonifico ricevuto", "bonifico in entrata",
           "stipendio", "rimborso", "incasso", "versamento",
           "received", "refund", "credited")

RE_ESERCENTE = [
    re.compile(r"(?:presso|a favore di|beneficiario|merchant|esercente)[:\s]+(.{2,40}?)(?:[.,;\n]|\s+(?:il|del|con|per|di|in)\s|$)", re.I),
    re.compile(r"\bda\s+([A-Z][\w&' .-]{1,30}?)(?:[.,;\n]|\s+(?:il|del|con|per)\s|$)"),
    re.compile(r"\ba\s+([A-Z][\w&' .-]{1,30}?)(?:[.,;\n]|\s+(?:il|del|con|per)\s|$)"),
    re.compile(r"@\s*([\w&' .-]{2,30})"),
]

def _p_coda():
    import __main__ as _app
    return os.path.join(_app.DB_DIR, "notifiche_proposte.json")

def _num_a_float(s):
    s = s.strip()
    m = re.search(r"[.,](\d{1,2})$", s)
    if m:
        intero = re.sub(r"[.,\u00a0\u202f]", "", s[:m.start()])
        dec = m.group(1)
    else:
        intero = re.sub(r"[.,\u00a0\u202f]", "", s)
        dec = "0"
    return float(f"{intero}.{dec}")

def _importo(testo):
    trovati = []
    for rx in RE_IMPORTO:
        for m in rx.finditer(testo):
            if RE_SALDO.search(testo[max(0, m.start() - 25):m.start()]):
                continue
            try:
                v = _num_a_float(m.group(1))
            except ValueError:
                continue
            if v > 0:
                trovati.append((m.start(), round(v, 2)))
    return min(trovati)[1] if trovati else None

def _tipo(testo):
    t = testo.lower()
    e = any(k in t for k in ENTRATA)
    u = any(k in t for k in USCITA)
    if e and not u:
        return "Entrata"
    return "Uscita"

def _descrizione(titolo, testo):
    for rx in RE_ESERCENTE:
        m = rx.search(testo)
        if m:
            return m.group(1).strip(" .-")[:50]
    breve = testo.strip().replace("\n", " ")
    if 0 < len(breve) <= 60:
        for rx in RE_IMPORTO:
            breve = rx.sub(" ", breve)
        breve = re.sub(r"\s+", " ", breve).strip(" .,;:-")
        if len(breve) >= 4:
            return breve[:50]
    return (titolo or testo).strip().replace("\n", " ")[:50]

def _estrai_gemini(titolo, testo):
    try:
        import __main__ as _app
        if not getattr(_app, "API_KEY", None):
            return None
        client = _app.genai_client.Client(api_key=_app.API_KEY)
        prompt = (
            "Questa è la notifica di uno smartphone. Dì se descrive un pagamento o un incasso "
            "di denaro. Rispondi SOLO con JSON: "
            '{"movimento": true/false, "importo": float, "direzione": "Entrata/Uscita", "descrizione": "esercente o motivo, max 40 caratteri"}. '
            "Se non è un movimento di denaro, movimento=false.\n\n"
            f"Titolo: {titolo}\nTesto: {testo}")
        r = client.models.generate_content(model=_app.GEMINI, contents=[prompt])
        raw = r.text.strip().replace("```json", "").replace("```", "").strip()
        d = json.loads(raw)
        if not d.get("movimento"):
            return None
        imp = float(d.get("importo") or 0)
        if imp <= 0:
            return None
        tipo = "Entrata" if str(d.get("direzione", "")).lower().startswith("entr") else "Uscita"
        return {"importo": round(imp, 2), "tipo": tipo,
                "desc": str(d.get("descrizione") or titolo or testo)[:50], "fonte": "gemini"}
    except Exception as e:
        print(f"Notifiche→spese: Gemini non riuscito: {e}")
        return None

def estrai(n, usa_gemini=True):
    titolo, testo = n.get("title", ""), n.get("text", "")
    tutto = f"{titolo}\n{testo}"
    imp = _importo(tutto)
    t = tutto.lower()
    if imp is not None and any(k in t for k in USCITA + ENTRATA):
        return {"importo": imp, "tipo": _tipo(tutto), "desc": _descrizione(titolo, testo), "fonte": "regole"}
    if usa_gemini and RE_SOLDI.search(tutto):
        return _estrai_gemini(titolo, testo)
    return None

def _leggi():
    try:
        with open(_p_coda(), "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, list) else []
    except Exception:
        return []

def _scrivi(lista):
    p = _p_coda()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(lista[-MAX_PROPOSTE:], f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)

def aggiungi_proposte(notifiche):
    nuove = []
    for n in notifiche:
        if n.get("prova") or n.get("riepilogo"):
            continue
        dati = estrai(n)
        if not dati:
            continue
        nuove.append({
            "id": n["id"], "quando": n.get("quando", ""), "app": n.get("app", ""),
            "title": n.get("title", ""), "text": n.get("text", ""),
            "importo": dati["importo"], "tipo": dati["tipo"], "desc": dati["desc"],
            "fonte": dati["fonte"], "stato": "attesa",
            "conto": n.get("conto", ""), "metodo": n.get("metodo", ""), "auto": n.get("auto", ""),
            "tags": n.get("tags", []),
        })
    if not nuove:
        return 0
    with _LOCK:
        lista = _leggi()
        visti = {x.get("id") for x in lista}
        unici = []
        for x in nuove:
            if x["id"] not in visti:
                visti.add(x["id"])
                unici.append(x)
        nuove = unici
        if nuove:
            _scrivi(lista + nuove)
    return len(nuove)

def elenco(stato="attesa"):
    with _LOCK:
        return [x for x in reversed(_leggi()) if x.get("stato") == stato]

def aggiorna_indicatore(app):
    try:
        n = len(elenco())
    except Exception:
        return
    def _ap():
        w = getattr(app, "lbl_notifiche_attesa", None)
        if w is None or not w.winfo_exists():
            return
        w.config(text=f"Da confermare: {n}" if n else " ")
    try:
        app.after(0, _ap)
    except Exception:
        pass

def trova(id_):
    with _LOCK:
        return next((x for x in _leggi() if x.get("id") == id_ and x.get("stato") == "attesa"), None)

def _imposta_stato(id_, stato):
    with _LOCK:
        lista = _leggi()
        for x in lista:
            if x.get("id") == id_:
                x["stato"] = stato
        _scrivi(lista)

def scarta(id_):
    _imposta_stato(id_, "scartata")

def segna_confermata(id_):
    _imposta_stato(id_, "confermata")

def _p_regole():
    import __main__ as _app
    return os.path.join(_app.DB_DIR, "regole_notifiche.json")

def _chiave_app(app):
    return (app or "").strip().lower()

def _leggi_regole():
    try:
        with open(_p_regole(), "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}

def regola_app(app):
    r = _leggi_regole().get(_chiave_app(app), {})
    return {k: r.get(k, "") for k in ("categoria", "conto", "metodo", "tag")}


def ricorda_app(app, categoria, conto, metodo, tag):
    chiave = _chiave_app(app)
    if not chiave:
        return
    with _LOCK:
        d = _leggi_regole()
        d[chiave] = {"categoria": categoria or "", "conto": conto or "",
                     "metodo": metodo or "", "tag": tag or ""}
        tmp = _p_regole() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        os.replace(tmp, _p_regole())


def _auto_consentita(p):
    modo = p.get("auto", "")
    return modo == "tutto" or (modo == "regole" and p.get("fonte") == "regole")

def categoria_da_testo(app, p):
    testo = f"{p.get('desc', '')} {p.get('title', '')} {p.get('text', '')}".lower()
    trovate = []
    for c in getattr(app, "categorie", []) or []:
        nome = str(c).strip()
        if len(nome) < 3 or nome.lower() == "generica":
            continue
        if re.search(r"(?<!\w)" + re.escape(nome.lower()) + r"(?!\w)", testo):
            trovate.append(nome)
    return max(trovate, key=len) if trovate else ""

def registra_auto(app, p):
    import datetime
    import __main__ as _app
    from moduli import log_importazioni as li
    from moduli.modello_spesa import METODI_PAGAMENTO, campo
    r = regola_app(p.get("app", ""))
    memoria = getattr(app, "memoria_descrizioni_categoria", {}) or {}
    cat = memoria.get(p["desc"].strip().upper()) or categoria_da_testo(app, p) or r["categoria"]
    if not cat or cat == "Generica" or cat not in app.categorie:
        return False
    try:
        with open(_app.PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as f:
            conti = [c.get("nome", "") for c in json.load(f).get("conti", []) if c.get("nome")]
    except Exception:
        conti = []
    conto_p = (p.get("conto") or "").strip().lower()
    conto = next((c for c in conti if conto_p and c.lower() == conto_p), "")
    if not conto and r["conto"] in conti:
        conto = r["conto"]
    metodo_p = (p.get("metodo") or "").strip().lower()
    metodo = next((m for m in METODI_PAGAMENTO if metodo_p and m.lower() == metodo_p), "")
    if not metodo and r["metodo"] in METODI_PAGAMENTO:
        metodo = r["metodo"]
    testo_tag = " ".join("#" + t.lstrip("#") for t in (p.get("tags") or [])) or r["tag"]
    try:
        tags = app._normalizza_tags(testo_tag)
    except Exception:
        tags = []
    try:
        d = datetime.datetime.fromisoformat(p["quando"]).date()
    except Exception:
        d = datetime.date.today()
    desc = p["desc"].strip()[:60]
    imp, tipo = float(p["importo"]), p["tipo"]
    from moduli.sync_mail_opzioni import leggi_opzioni
    if leggi_opzioni(_app.app_config_globale)["controllo_doppioni"] and any(
            campo(e, "descrizione", "") == desc and abs(float(campo(e, "importo", 0.0)) - imp) < 0.01
            for e in app.spese.get(d, [])):
        li.scrivi_riga("DOPPIA", d, desc, imp, tipo, cat)
        scarta(p["id"])
        return False
    voce = _app.SpesaEntry.nuova(cat, desc, imp, tipo, conto=conto, hashtag=tags, metodo_pagamento=metodo)
    app.spese.setdefault(d, []).append(voce)
    ricorda_app(p.get("app", ""), cat, conto, metodo, " ".join(tags))
    li.scrivi_riga("AUTO", d, desc, imp, tipo, cat, voce)
    app.save_db()
    segna_confermata(p["id"])
    try:
        app.registra_azione_gamification("movimento")
    except Exception:
        pass
    app.refresh_gui()
    return True

def processa_automatiche(app):
    fatte = 0
    for p in list(elenco()):
        if not _auto_consentita(p):
            continue
        try:
            if registra_auto(app, p):
                fatte += 1
        except Exception as e:
            print(f"Notifiche: registrazione automatica non riuscita: {e}")
    return fatte
