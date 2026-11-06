#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import hmac
import html
import secrets
import hashlib
import threading
import datetime
from collections import OrderedDict

_LOCK = threading.Lock()
_FALLITI = {}
_CHIAVI = OrderedDict()
_STATO = {"righe": None, "dir": None}

MAX_BYTES = 256 * 1024
MAX_ITEMS = 200
MAX_RIGHE = 5000
TENTATIVI_MAX = 10
FINESTRA_SEC = 600

def _db_dir():
    import __main__ as _app
    return _app.DB_DIR

def _p_cfg():
    return os.path.join(_db_dir(), "webhook_notifiche.json")

def _p_inbox():
    return os.path.join(_db_dir(), "notifiche_ricevute.jsonl")

def _scrivi_atomico(percorso, testo):
    tmp = percorso + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(testo)
    os.replace(tmp, percorso)

def _token():
    p = _p_cfg()
    with _LOCK:
        try:
            with open(p, "r", encoding="utf-8") as f:
                t = str(json.load(f).get("token", "")).strip()
            if t:
                return t, False
        except Exception:
            pass
        t = secrets.token_urlsafe(32)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        _scrivi_atomico(p, json.dumps({"token": t}, indent=2))
        return t, True

def rigenera_token():
    p = _p_cfg()
    t = secrets.token_urlsafe(32)
    with _LOCK:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        _scrivi_atomico(p, json.dumps({"token": t}, indent=2))
    return t

def _autorizzato(request):
    intest = request.headers.get("Authorization", "")
    if not intest.lower().startswith("bearer "):
        return False
    inviato = intest[7:].strip().encode("utf-8")
    atteso = _token()[0].encode("utf-8")
    return hmac.compare_digest(inviato, atteso)

def _bloccato(ip):
    with _LOCK:
        voce = _FALLITI.get(ip)
        if not voce:
            return False
        if time.time() - voce[1] > FINESTRA_SEC:
            del _FALLITI[ip]
            return False
        return voce[0] >= TENTATIVI_MAX

def _registra_fallimento(ip):
    with _LOCK:
        ora = time.time()
        voce = _FALLITI.get(ip)
        if not voce or ora - voce[1] > FINESTRA_SEC:
            _FALLITI[ip] = [1, ora]
        else:
            voce[0] += 1
        if len(_FALLITI) > 1000:
            _FALLITI.clear()

def _carica_stato_se_serve():
    d = _db_dir()
    if _STATO["dir"] == d and _STATO["righe"] is not None:
        return
    _CHIAVI.clear()
    righe = 0
    try:
        with open(_p_inbox(), "r", encoding="utf-8") as f:
            for r in f:
                righe += 1
                try:
                    _CHIAVI[json.loads(r).get("id", "")] = 1
                except Exception:
                    pass
    except FileNotFoundError:
        pass
    while len(_CHIAVI) > 3000:
        _CHIAVI.popitem(last=False)
    _STATO["righe"] = righe
    _STATO["dir"] = d

def _taglia_se_serve():
    if _STATO["righe"] is None or _STATO["righe"] <= MAX_RIGHE + MAX_RIGHE // 5:
        return
    p = _p_inbox()
    with open(p, "r", encoding="utf-8") as f:
        ultime = f.readlines()[-MAX_RIGHE:]
    _scrivi_atomico(p, "".join(ultime))
    _STATO["righe"] = len(ultime)

def svuota():
    with _LOCK:
        _scrivi_atomico(_p_inbox(), "")
        _STATO["righe"] = 0
        _CHIAVI.clear()

def _leggi_ultime(limite):
    p = _p_inbox()
    try:
        with _LOCK, open(p, "r", encoding="utf-8") as f:
            righe = f.readlines()[-limite:]
    except FileNotFoundError:
        return []
    out = []
    for r in reversed(righe):
        try:
            out.append(json.loads(r))
        except Exception:
            continue
    return out

def _txt(v, massimo):
    return ("" if v is None else str(v)).strip()[:massimo]

def _ts_ms(v):
    try:
        t = float(v)
        if t < 1e11:
            t *= 1000
        datetime.datetime.fromtimestamp(t / 1000)
        return int(t)
    except Exception:
        return int(time.time() * 1000)

def _normalizza(payload):
    if not isinstance(payload, dict):
        return None
    grezzi = payload.get("items")
    if grezzi is None and ("title" in payload or "text" in payload):
        grezzi = [payload]
    if not isinstance(grezzi, list) or len(grezzi) > MAX_ITEMS:
        return None
    notifiche = []
    for it in grezzi:
        if not isinstance(it, dict):
            continue
        titolo = _txt(it.get("title"), 2000)
        testo = _txt(it.get("text"), 6000)
        if not titolo and not testo:
            continue
        notifiche.append({
            "ts": _ts_ms(it.get("ts")),
            "app": _txt(it.get("app"), 100),
            "pkg": _txt(it.get("pkg"), 200),
            "title": titolo,
            "text": testo,
        })
    tags_raw = payload.get("tags")
    if isinstance(tags_raw, str):
        tags_raw = tags_raw.replace(",", " ").split()
    tags = []
    if isinstance(tags_raw, list):
        for t in tags_raw[:1]:
            t = _txt(t, 40).lstrip("#").replace(" ", "")
            if t and t not in tags:
                tags.append(t)
    metodo = _txt(payload.get("metodo"), 40)
    try:
        from moduli.modello_spesa import METODI_PAGAMENTO
        metodo = next((m for m in METODI_PAGAMENTO if m.lower() == metodo.lower()), "")
    except Exception:
        pass
    auto = _txt(payload.get("auto"), 10).lower()
    if auto not in ("regole", "tutto"):
        auto = ""
    return (_txt(payload.get("rule"), 100), bool(payload.get("digest")), notifiche,
            _txt(payload.get("conto"), 100), tags, metodo, auto)


def registra(flask_app, tk_app, richiede_login):
    from flask import request, Response

    def _json(obj, codice=200):
        r = Response(json.dumps(obj, ensure_ascii=False), status=codice, mimetype="application/json")
        r.headers["Cache-Control"] = "no-store"
        return r

    def _nega():
        ip = request.remote_addr or "?"
        if _bloccato(ip):
            return _json({"ok": False, "errore": "troppi tentativi"}, 429)
        if not _autorizzato(request):
            _registra_fallimento(ip)
            return _json({"ok": False, "errore": "non autorizzato"}, 401)
        return None

    @flask_app.route("/api/notifiche", methods=["POST"])
    def api_notifiche_ricevi():
        rifiuto = _nega()
        if rifiuto is not None:
            return rifiuto
        if request.content_length and request.content_length > MAX_BYTES:
            return _json({"ok": False, "errore": "richiesta troppo grande"}, 413)
        corpo = request.get_data(cache=False)
        if len(corpo) > MAX_BYTES:
            return _json({"ok": False, "errore": "richiesta troppo grande"}, 413)
        try:
            payload = json.loads(corpo.decode("utf-8"))
        except Exception:
            return _json({"ok": False, "errore": "JSON non valido"}, 400)
        norm = _normalizza(payload)
        if norm is None:
            return _json({"ok": False, "errore": "formato non riconosciuto"}, 400)
        regola, riepilogo, notifiche, conto, tags, metodo, auto = norm

        nuove = []
        ora = datetime.datetime.now().isoformat(timespec="seconds")
        with _LOCK:
            _carica_stato_se_serve()
            righe_nuove = []
            for n in notifiche:
                chiave = hashlib.sha1(
                    f"{n['pkg']}|{n['ts']}|{n['title']}|{n['text']}".encode("utf-8")).hexdigest()[:16]
                if chiave in _CHIAVI:
                    continue
                _CHIAVI[chiave] = 1
                while len(_CHIAVI) > 3000:
                    _CHIAVI.popitem(last=False)
                rec = dict(n)
                rec.update({
                    "id": chiave,
                    "quando": datetime.datetime.fromtimestamp(n["ts"] / 1000).isoformat(timespec="seconds"),
                    "ricevuta": ora,
                    "regola": regola,
                    "riepilogo": riepilogo,
                    "prova": n["pkg"] == "it.notif2mail",
                    "conto": conto,
                    "metodo": metodo,
                    "auto": auto,
                    "tags": tags,
                })
                righe_nuove.append(json.dumps(rec, ensure_ascii=False))
                nuove.append(rec)
            if righe_nuove:
                os.makedirs(_db_dir(), exist_ok=True)
                with open(_p_inbox(), "a", encoding="utf-8") as f:
                    f.write("\n".join(righe_nuove) + "\n")
                _STATO["righe"] += len(righe_nuove)
                _taglia_se_serve()

        if nuove:
            def _proponi(recs=list(nuove)):
                try:
                    from moduli.notifiche_spese import aggiungi_proposte
                    n = aggiungi_proposte(recs)
                    if n:
                        from moduli.notifiche_spese import aggiorna_indicatore, processa_automatiche
                        def _segnala():
                            try:
                                auto = processa_automatiche(tk_app)
                            except Exception as e:
                                print(f"Notifiche→spese: registrazione automatica: {e}")
                                auto = 0
                            aggiorna_indicatore(tk_app)
                            resto = max(0, n - auto)
                            if auto:
                                tk_app.show_toast(f"✅ {auto} spesa/e registrata/e in automatico", duration=4000)
                            if resto:
                                tk_app.show_toast(f"💸 {resto} nuova/e spesa/e da webhook in attesa!", duration=4000)
                                try:
                                    tk_app.riproduci_beep()
                                except Exception:
                                    pass
                        tk_app.after(0, _segnala)
                except Exception as e:
                    print(f"Notifiche→spese: {e}")
            threading.Thread(target=_proponi, daemon=True).start()
            try:
                prima = nuove[0]
                testo = f"📩 {prima['app'] or 'Notifica'}: {prima['title'] or prima['text']}"[:120]
                if len(nuove) > 1:
                    testo += f" (+{len(nuove) - 1})"
                tk_app.after(0, lambda t=testo: tk_app.show_toast(t, duration=3000))
            except Exception:
                pass
        return _json({"ok": True, "ricevute": len(notifiche), "nuove": len(nuove)})

    @flask_app.route("/api/notifiche/opzioni", methods=["GET"])
    def api_notifiche_opzioni():
        rifiuto = _nega()
        if rifiuto is not None:
            return rifiuto
        import __main__ as _app
        conti = []
        try:
            with open(_app.PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as f:
                conti = [c.get("nome", "") for c in json.load(f).get("conti", []) if c.get("nome")]
        except Exception:
            pass
        tutti = set()
        try:
            for lista in list(tk_app.spese.values()):
                for voce in list(lista):
                    h = voce.get("hashtag", []) if isinstance(voce, dict) else getattr(voce, "hashtag", [])
                    for t in h or []:
                        tutti.add(str(t).lstrip("#"))
        except Exception:
            pass
        try:
            from moduli.modello_spesa import METODI_PAGAMENTO
            metodi = list(METODI_PAGAMENTO)
        except Exception:
            metodi = []
        return _json({"ok": True, "conti": conti, "tag": sorted(tutti), "metodi": metodi})

    @flask_app.route("/api/notifiche", methods=["GET"])
    def api_notifiche_elenco():
        rifiuto = _nega()
        if rifiuto is not None:
            return rifiuto
        try:
            limite = max(1, min(500, int(request.args.get("limit", "50"))))
        except ValueError:
            limite = 50
        return _json({"ok": True, "items": _leggi_ultime(limite)})

