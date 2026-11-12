#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import hashlib
import datetime
import threading

from moduli.webhook_notifiche import _autorizzato, _bloccato, _registra_fallimento

PROTO = 1
MAX_BYTES = 4 * 1024 * 1024
MAX_ID_RICHIESTI = 5000
TIMEOUT_TK = 40
FMT = "%d-%m-%Y"
MAX_FILE = 8 * 1024 * 1024
MAX_DOC = 40 * 1024 * 1024

FILE_SYNC = (
    "veicoli", "animali", "immobil", "finanziamenti", "fondo_risparmio", "rubrica",
    "utenze_db", "documenti_archiviati", "supermercati", "promemoria", "portafoglio",
    "fondo_pensione", "dieta_piano", "alimenti_custom", "peso_storico", "fabbisogno_dati",
    "pedometro", "manutenzione_casa", "magazzino", "studio_clienti", "studio_appuntamenti",
    "studio_prestazioni", "studio_fatture", "studio_emittente", "studio_cassa",
    "studio_magazzino", "portafoglio_db",
)
BLOCCHI = (
    "categorie", "categorie_tipi", "categorie_classi", "categorie_conti_risparmio",
    "ricorrenze", "budget_categorie", "budget_annuale_categorie", "pianificate",
    "fairshare", "memoria_categorie",
)


def _su_tk(tk_app, fn):
    ev = threading.Event()
    out = {}

    def _run():
        try:
            out["r"] = fn()
        except Exception as e:
            out["e"] = e
        finally:
            ev.set()

    tk_app.after(0, _run)
    if not ev.wait(TIMEOUT_TK):
        raise TimeoutError("il programma sul PC non ha risposto in tempo")
    if "e" in out:
        raise out["e"]
    return out["r"]


def _dict_voce(tk_app, v):
    if hasattr(v, "a_dict"):
        return v.a_dict()
    return tk_app._entry_a_dict(v)


def _impronta(data_str, d):
    base = dict(d)
    base["date"] = data_str
    if "importo" in base:
        try:
            base["importo"] = round(float(base["importo"]), 2)
        except Exception:
            pass
    testo = json.dumps(base, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(testo.encode("utf-8")).hexdigest()[:12]


def _mappa_id(tk_app):
    m = {}
    for d, lista in tk_app.spese.items():
        for i, v in enumerate(lista):
            sid = getattr(v, "id_spesa", None)
            if sid:
                m[sid] = (d, i)
    return m


def _indice(tk_app):
    voci = []
    for d, lista in sorted(tk_app.spese.items()):
        ds = d.strftime(FMT)
        for v in lista:
            sid = getattr(v, "id_spesa", None)
            if not sid:
                continue
            dv = _dict_voce(tk_app, v)
            voci.append([sid, ds, _impronta(ds, dv), 1 if dv.get("pool_ref") else 0])
    tipi = dict(getattr(tk_app, "categorie_tipi", {}) or {})
    cats = list(getattr(tk_app, "categorie", []) or [])
    return {"voci": voci, "categorie": cats, "categorie_tipi": tipi}


def _scarica(tk_app, ids):
    voglio = set(ids)
    out = []
    for d, lista in tk_app.spese.items():
        ds = d.strftime(FMT)
        for v in lista:
            sid = getattr(v, "id_spesa", None)
            if sid in voglio:
                dv = _dict_voce(tk_app, v)
                out.append({"date": ds, "entry": dv, "h": _impronta(ds, dv)})
    return out


def _valida(e):
    if not isinstance(e, dict):
        return "voce non valida"
    for k in ("id_spesa", "categoria", "tipo"):
        if not str(e.get(k, "")).strip():
            return f"campo mancante: {k}"
    try:
        float(e.get("importo"))
    except Exception:
        return "importo non valido"
    if not isinstance(e.get("descrizione", ""), str):
        return "descrizione non valida"
    return None


def _applica(tk_app, upsert, elimina, categorie_nuove):
    from moduli.modello_spesa import SpesaEntry
    esito = {"applicati": [], "eliminati": [], "rifiutati": []}
    mappa = _mappa_id(tk_app)
    toccato = False

    def _corrente(sid):
        pos = mappa.get(sid)
        if not pos:
            return None, None, None
        d, i = pos
        v = tk_app.spese[d][i]
        dv = _dict_voce(tk_app, v)
        return d, dv, _impronta(d.strftime(FMT), dv)

    for nome, tipo in (categorie_nuove or {}).items():
        nome = str(nome).strip()
        if not nome or nome in tk_app.categorie:
            continue
        tk_app.categorie.append(nome)
        tk_app.categorie_tipi[nome] = str(tipo or "Uscita")
        toccato = True

    for it in upsert or []:
        try:
            e = it.get("entry")
            err = _valida(e)
            sid = str((e or {}).get("id_spesa", ""))
            if err:
                esito["rifiutati"].append({"id": sid, "motivo": err})
                continue
            d_nuova = datetime.datetime.strptime(str(it.get("date", "")), FMT).date()
            base = it.get("base")
            d_att, dv_att, h_att = _corrente(sid)
            if dv_att is not None:
                if dv_att.get("pool_ref"):
                    esito["rifiutati"].append({"id": sid, "motivo": "bloccata", "bloccata": True})
                    continue
                nuova_h = _impronta(d_nuova.strftime(FMT), SpesaEntry.da_dict(e).a_dict())
                if nuova_h == h_att:
                    esito["applicati"].append({"id": sid, "h": h_att})
                    continue
                if base != h_att:
                    esito["rifiutati"].append({"id": sid, "motivo": "conflitto", "h": h_att})
                    continue
            elif base:
                esito["rifiutati"].append({"id": sid, "motivo": "eliminata", "h": None})
                continue
            if str(e.get("categoria")) not in tk_app.categorie:
                tk_app.categorie.append(str(e["categoria"]))
                tk_app.categorie_tipi.setdefault(str(e["categoria"]), str(e.get("tipo") or "Uscita"))
            nuovo = SpesaEntry.da_dict(e)
            if dv_att is not None:
                pos = mappa[sid]
                lista = tk_app.spese[pos[0]]
                lista.pop(pos[1])
                if not lista:
                    del tk_app.spese[pos[0]]
            tk_app.spese.setdefault(d_nuova, []).append(nuovo)
            mappa = _mappa_id(tk_app)
            toccato = True
            esito["applicati"].append({
                "id": sid, "h": _impronta(d_nuova.strftime(FMT), nuovo.a_dict())})
        except Exception as ex:
            esito["rifiutati"].append({"id": str((it or {}).get("entry", {}).get("id_spesa", "")),
                                       "motivo": f"errore: {ex}"})

    for it in elimina or []:
        sid = str((it or {}).get("id", ""))
        try:
            d_att, dv_att, h_att = _corrente(sid)
            if dv_att is None:
                esito["eliminati"].append(sid)
                continue
            if dv_att.get("pool_ref"):
                esito["rifiutati"].append({"id": sid, "motivo": "bloccata", "bloccata": True})
                continue
            if it.get("base") != h_att:
                esito["rifiutati"].append({"id": sid, "motivo": "conflitto", "h": h_att})
                continue
            pos = mappa[sid]
            lista = tk_app.spese[pos[0]]
            lista.pop(pos[1])
            if not lista:
                del tk_app.spese[pos[0]]
            mappa = _mappa_id(tk_app)
            toccato = True
            esito["eliminati"].append(sid)
        except Exception as ex:
            esito["rifiutati"].append({"id": sid, "motivo": f"errore: {ex}"})

    if toccato:
        tk_app.save_db()
        try:
            tk_app._sync_fairshare_e_aggiorna()
        except Exception as ex:
            print(f"Sync: fairshare: {ex}")
        try:
            tk_app.refresh_gui()
        except Exception as ex:
            print(f"Sync: refresh: {ex}")
        try:
            n = len(esito["applicati"]) + len(esito["eliminati"])
            tk_app.show_toast(f"📲 Sync dal telefono: {n} movimento/i", duration=3000)
        except Exception:
            pass
    return esito


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

    def _corpo():
        if request.content_length and request.content_length > MAX_BYTES:
            return None, _json({"ok": False, "errore": "richiesta troppo grande"}, 413)
        raw = request.get_data(cache=False)
        if len(raw) > MAX_BYTES:
            return None, _json({"ok": False, "errore": "richiesta troppo grande"}, 413)
        try:
            p = json.loads(raw.decode("utf-8"))
        except Exception:
            return None, _json({"ok": False, "errore": "JSON non valido"}, 400)
        if not isinstance(p, dict):
            return None, _json({"ok": False, "errore": "formato non riconosciuto"}, 400)
        return p, None

    @flask_app.route("/api/sync/stato", methods=["GET"])
    def sd_api_sync_stato():
        rifiuto = _nega()
        if rifiuto is not None:
            return rifiuto
        try:
            n = _su_tk(tk_app, lambda: sum(len(l) for l in tk_app.spese.values()))
        except Exception as e:
            return _json({"ok": False, "errore": str(e)}, 503)
        return _json({"ok": True, "proto": PROTO, "movimenti": n,
                      "ora": datetime.datetime.now().isoformat(timespec="seconds")})

    @flask_app.route("/api/sync/indice", methods=["GET"])
    def sd_api_sync_indice():
        rifiuto = _nega()
        if rifiuto is not None:
            return rifiuto
        try:
            ind = _su_tk(tk_app, lambda: _indice(tk_app))
        except Exception as e:
            return _json({"ok": False, "errore": str(e)}, 503)
        ind.update({"ok": True, "proto": PROTO})
        return _json(ind)

    @flask_app.route("/api/sync/scarica", methods=["POST"])
    def sd_api_sync_scarica():
        rifiuto = _nega()
        if rifiuto is not None:
            return rifiuto
        p, err = _corpo()
        if err is not None:
            return err
        ids = p.get("ids")
        if not isinstance(ids, list) or len(ids) > MAX_ID_RICHIESTI:
            return _json({"ok": False, "errore": "elenco id non valido"}, 400)
        ids = [str(i) for i in ids]
        try:
            voci = _su_tk(tk_app, lambda: _scarica(tk_app, ids))
        except Exception as e:
            return _json({"ok": False, "errore": str(e)}, 503)
        return _json({"ok": True, "voci": voci})

    @flask_app.route("/api/sync/applica", methods=["POST"])
    def sd_api_sync_applica():
        rifiuto = _nega()
        if rifiuto is not None:
            return rifiuto
        p, err = _corpo()
        if err is not None:
            return err
        upsert = p.get("upsert") or []
        elimina = p.get("elimina") or []
        nuove = p.get("categorie_nuove") or {}
        if not isinstance(upsert, list) or not isinstance(elimina, list) or not isinstance(nuove, dict):
            return _json({"ok": False, "errore": "formato non riconosciuto"}, 400)
        try:
            esito = _su_tk(tk_app, lambda: _applica(tk_app, upsert, elimina, nuove))
        except Exception as e:
            return _json({"ok": False, "errore": str(e)}, 503)
        esito["ok"] = True
        return _json(esito)

    _registra_extra(flask_app, tk_app, _json, _nega, _corpo)


def _h_json(v):
    t = json.dumps(v, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(t.encode("utf-8")).hexdigest()[:12]


def _blocco_leggi(tk_app, nome):
    if nome == "categorie":
        return list(tk_app.categorie)
    if nome == "categorie_tipi":
        return dict(tk_app.categorie_tipi)
    if nome == "categorie_classi":
        return dict(getattr(tk_app, "categorie_classi", None)
                    or (getattr(tk_app, "db", None) or {}).get("categorie_classi", {}) or {})
    if nome == "categorie_conti_risparmio":
        return dict(tk_app._conti_risparmio_cat())
    if nome == "ricorrenze":
        return tk_app.ricorrenze
    if nome == "budget_categorie":
        return tk_app.budget_categorie
    if nome == "budget_annuale_categorie":
        return tk_app.budget_annuale_categorie
    if nome == "pianificate":
        return getattr(tk_app, "pianificate", None) or {"piani": []}
    if nome == "fairshare":
        return {"gestore_partecipa": bool(getattr(tk_app, "fairshare_gestore_partecipa", True)),
                "partecipanti": list(getattr(tk_app, "nomi_partecipanti", []) or [])}
    if nome == "memoria_categorie":
        return tk_app.memoria_descrizioni_categoria
    raise KeyError(nome)


def _blocco_scrivi(tk_app, nome, v):
    def _sost(dest, nuovo):
        if isinstance(dest, list):
            dest[:] = nuovo
        else:
            dest.clear()
            dest.update(nuovo)
    db = getattr(tk_app, "db", None)
    if nome in ("categorie", "categorie_tipi", "ricorrenze", "budget_categorie",
                "budget_annuale_categorie", "memoria_categorie"):
        attr = {"categorie": "categorie", "categorie_tipi": "categorie_tipi",
                "ricorrenze": "ricorrenze", "budget_categorie": "budget_categorie",
                "budget_annuale_categorie": "budget_annuale_categorie",
                "memoria_categorie": "memoria_descrizioni_categoria"}[nome]
        _sost(getattr(tk_app, attr), v)
    elif nome == "categorie_classi":
        tk_app.categorie_classi = dict(v)
        if isinstance(db, dict):
            db["categorie_classi"] = dict(v)
    elif nome == "categorie_conti_risparmio":
        tk_app.categorie_conti_risparmio = dict(v)
        if isinstance(db, dict):
            db["categorie_conti_risparmio"] = dict(v)
    elif nome == "pianificate":
        tk_app.pianificate = {"piani": list(v.get("piani", []))}
        if isinstance(db, dict):
            db["pianificate"] = tk_app.pianificate
    elif nome == "fairshare":
        if isinstance(db, dict):
            db["fairshare"] = v
        tk_app.carica_partecipanti_da_db()
    else:
        raise KeyError(nome)


def _blocchi_tutti(tk_app):
    out = {}
    for n in BLOCCHI:
        v = _blocco_leggi(tk_app, n)
        out[n] = {"h": _h_json(v), "valore": v}
    return out


def _blocchi_applica(tk_app, blocchi):
    esito = {"applicati": [], "rifiutati": []}
    toccato = False
    for nome, it in blocchi.items():
        if nome not in BLOCCHI or not isinstance(it, dict):
            esito["rifiutati"].append({"nome": nome, "motivo": "blocco sconosciuto"})
            continue
        try:
            att = _blocco_leggi(tk_app, nome)
            h_att = _h_json(att)
            v = it.get("valore")
            if not isinstance(v, (dict, list)) or isinstance(v, list) != isinstance(att, list):
                esito["rifiutati"].append({"nome": nome, "motivo": "formato non valido"})
                continue
            if _h_json(v) == h_att:
                esito["applicati"].append({"nome": nome, "h": h_att})
                continue
            if it.get("base") != h_att:
                esito["rifiutati"].append({"nome": nome, "motivo": "conflitto", "h": h_att})
                continue
            _blocco_scrivi(tk_app, nome, v)
            toccato = True
            esito["applicati"].append({"nome": nome, "h": _h_json(_blocco_leggi(tk_app, nome))})
        except Exception as ex:
            esito["rifiutati"].append({"nome": nome, "motivo": f"errore: {ex}"})
    if toccato:
        tk_app.save_db()
        try:
            tk_app.refresh_gui()
        except Exception as ex:
            print(f"Sync: refresh: {ex}")
    return esito


def _percorso_file(nome):
    import __main__ as _app
    if nome not in FILE_SYNC:
        return None
    return os.path.join(_app.DB_DIR, nome + ".json")


def _leggi_file(p):
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def _scrivi_file(p, valore):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(valore, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    if os.path.exists(p):
        try:
            import shutil
            shutil.copy2(p, p + ".bak")
        except Exception:
            pass
    os.replace(tmp, p)


def _nome_doc_ok(nome):
    return (bool(nome) and nome == os.path.basename(nome) and not nome.startswith(".")
            and "\\" not in nome and "/" not in nome and len(nome) < 200)


EST_DOC = ("pdf", "jpg", "jpeg", "png", "webp", "gif", "heic")


def _percorso_doc(nome):
    import __main__ as _app
    nome = str(nome or "")
    if _nome_doc_ok(nome):
        return os.path.join(_app.DOC_DIR, nome)
    p = nome.split("/")
    if len(p) < 2 or p[0] != "documenti_personali":
        return None
    for seg in p:
        if (not seg or seg in (".", "..") or seg.startswith(".") or "\\" in seg
                or len(seg) > 200 or "\x00" in seg):
            return None
    r = p[1:]
    ok = ((len(r) == 1 and r[0] == "profili.json")
          or (len(r) == 2 and r[1] in ("registry.json", "categorie.json"))
          or (len(r) == 3 and r[1] == "documenti" and "." in r[2]
              and r[2].rsplit(".", 1)[-1].lower() in EST_DOC))
    if not ok:
        return None
    base = _app.DOC_PERS_DIR
    full = os.path.join(base, *r)
    if os.path.commonpath([os.path.realpath(base), os.path.realpath(full)]) != os.path.realpath(base):
        return None
    return full


def _elenco_personali():
    import __main__ as _app
    out = []
    base = _app.DOC_PERS_DIR
    if not os.path.isdir(base):
        return out

    def _agg(rel, p):
        try:
            st = os.stat(p)
            out.append({"nome": "documenti_personali/" + rel, "size": st.st_size,
                        "mt": int(st.st_mtime)})
        except OSError:
            pass

    pf = os.path.join(base, "profili.json")
    if os.path.isfile(pf):
        _agg("profili.json", pf)
    with os.scandir(base) as it:
        for e in sorted(it, key=lambda x: x.name):
            if not e.is_dir() or e.name.startswith("."):
                continue
            for meta in ("registry.json", "categorie.json"):
                mp = os.path.join(e.path, meta)
                if os.path.isfile(mp):
                    _agg(e.name + "/" + meta, mp)
            dd = os.path.join(e.path, "documenti")
            if os.path.isdir(dd):
                with os.scandir(dd) as it2:
                    for f in sorted(it2, key=lambda x: x.name):
                        if (f.is_file() and not f.name.startswith(".") and "." in f.name
                                and f.name.rsplit(".", 1)[-1].lower() in EST_DOC):
                            _agg(e.name + "/documenti/" + f.name, f.path)
    return out


def _registra_extra(flask_app, tk_app, _json, _nega, _corpo):
    from flask import request, Response, send_file

    @flask_app.route("/api/sync/blocchi", methods=["GET"])
    def sd_api_sync_blocchi_leggi():
        rifiuto = _nega()
        if rifiuto is not None:
            return rifiuto
        try:
            out = _su_tk(tk_app, lambda: _blocchi_tutti(tk_app))
        except Exception as e:
            return _json({"ok": False, "errore": str(e)}, 503)
        return _json({"ok": True, "blocchi": out})

    @flask_app.route("/api/sync/blocchi", methods=["POST"])
    def sd_api_sync_blocchi_scrivi():
        rifiuto = _nega()
        if rifiuto is not None:
            return rifiuto
        p, err = _corpo()
        if err is not None:
            return err
        blocchi = p.get("blocchi")
        if not isinstance(blocchi, dict):
            return _json({"ok": False, "errore": "formato non riconosciuto"}, 400)
        try:
            esito = _su_tk(tk_app, lambda: _blocchi_applica(tk_app, blocchi))
        except Exception as e:
            return _json({"ok": False, "errore": str(e)}, 503)
        esito["ok"] = True
        return _json(esito)

    @flask_app.route("/api/sync/files", methods=["GET"])
    def sd_api_sync_files():
        rifiuto = _nega()
        if rifiuto is not None:
            return rifiuto
        out = {}
        for n in FILE_SYNC:
            try:
                v = _leggi_file(_percorso_file(n))
                out[n] = _h_json(v) if v is not None else None
            except Exception:
                out[n] = None
        return _json({"ok": True, "files": out})

    @flask_app.route("/api/sync/file", methods=["GET"])
    def sd_api_sync_file_leggi():
        rifiuto = _nega()
        if rifiuto is not None:
            return rifiuto
        p = _percorso_file(request.args.get("nome", ""))
        if p is None:
            return _json({"ok": False, "errore": "file non sincronizzabile"}, 400)
        try:
            v = _leggi_file(p)
        except Exception as e:
            return _json({"ok": False, "errore": f"file illeggibile: {e}"}, 500)
        return _json({"ok": True, "h": _h_json(v) if v is not None else None, "contenuto": v})

    @flask_app.route("/api/sync/file", methods=["POST"])
    def sd_api_sync_file_scrivi():
        rifiuto = _nega()
        if rifiuto is not None:
            return rifiuto
        if request.content_length and request.content_length > MAX_FILE:
            return _json({"ok": False, "errore": "richiesta troppo grande"}, 413)
        raw = request.get_data(cache=False)
        if len(raw) > MAX_FILE:
            return _json({"ok": False, "errore": "richiesta troppo grande"}, 413)
        try:
            pl = json.loads(raw.decode("utf-8"))
        except Exception:
            return _json({"ok": False, "errore": "JSON non valido"}, 400)
        nome = str(pl.get("nome", "")) if isinstance(pl, dict) else ""
        p = _percorso_file(nome)
        if p is None:
            return _json({"ok": False, "errore": "file non sincronizzabile"}, 400)
        nuovo = pl.get("contenuto")
        if not isinstance(nuovo, (dict, list)):
            return _json({"ok": False, "errore": "contenuto non valido"}, 400)
        try:
            att = _leggi_file(p)
        except Exception:
            att = None
        h_att = _h_json(att) if att is not None else None
        if _h_json(nuovo) == h_att:
            return _json({"ok": True, "h": h_att})
        if pl.get("base") != h_att:
            return _json({"ok": False, "errore": "conflitto", "h": h_att}, 409)
        try:
            _scrivi_file(p, nuovo)
        except Exception as e:
            return _json({"ok": False, "errore": f"scrittura fallita: {e}"}, 500)
        try:
            tk_app.after(0, tk_app.refresh_gui)
        except Exception:
            pass
        return _json({"ok": True, "h": _h_json(nuovo)})

    @flask_app.route("/api/sync/docs", methods=["GET"])
    def sd_api_sync_docs():
        rifiuto = _nega()
        if rifiuto is not None:
            return rifiuto
        import __main__ as _app
        out = []
        try:
            with os.scandir(_app.DOC_DIR) as it:
                for e in it:
                    if e.is_file() and not e.name.startswith("."):
                        st = e.stat()
                        out.append({"nome": e.name, "size": st.st_size, "mt": int(st.st_mtime)})
        except FileNotFoundError:
            pass
        try:
            out.extend(_elenco_personali())
        except Exception as e:
            print(f"Sync: documenti personali: {e}")
        return _json({"ok": True, "docs": out})

    @flask_app.route("/api/sync/doc", methods=["GET"])
    def sd_api_sync_doc_leggi():
        rifiuto = _nega()
        if rifiuto is not None:
            return rifiuto
        nome = request.args.get("nome", "")
        p = _percorso_doc(nome)
        if p is None:
            return _json({"ok": False, "errore": "nome non valido"}, 400)
        if not os.path.isfile(p):
            return _json({"ok": False, "errore": "non trovato"}, 404)
        return send_file(p, as_attachment=True, download_name=os.path.basename(p))

    @flask_app.route("/api/sync/doc", methods=["POST"])
    def sd_api_sync_doc_scrivi():
        rifiuto = _nega()
        if rifiuto is not None:
            return rifiuto
        import __main__ as _app
        nome = request.args.get("nome", "")
        personale = nome.startswith("documenti_personali/")
        meta = personale and nome.endswith(".json")
        if personale:
            p = _percorso_doc(nome)
            if p is None:
                return _json({"ok": False, "errore": "nome non valido"}, 400)
        elif _nome_doc_ok(nome):
            p = os.path.join(_app.DOC_DIR, nome)
        else:
            return _json({"ok": False, "errore": "nome non valido"}, 400)
        limite = MAX_FILE if meta else MAX_DOC
        if request.content_length and request.content_length > limite:
            return _json({"ok": False, "errore": "file troppo grande"}, 413)
        raw = request.get_data(cache=False)
        if len(raw) > limite:
            return _json({"ok": False, "errore": "file troppo grande"}, 413)
        if meta:
            try:
                nuovo = json.loads(raw.decode("utf-8"))
            except Exception:
                return _json({"ok": False, "errore": "JSON non valido"}, 400)
            if os.path.basename(p) == "registry.json":
                valido = isinstance(nuovo, dict)
            else:
                valido = isinstance(nuovo, list)
            if not valido:
                return _json({"ok": False, "errore": "contenuto non valido"}, 400)
            if os.path.exists(p):
                try:
                    att = int(os.stat(p).st_mtime)
                except OSError:
                    att = 0
                try:
                    bm = int(request.args.get("base_mt", ""))
                except ValueError:
                    bm = -1
                if bm != att:
                    return _json({"ok": False, "errore": "conflitto"}, 409)
            try:
                _scrivi_file(p, nuovo)
                mt = int(os.stat(p).st_mtime)
            except Exception as e:
                return _json({"ok": False, "errore": f"scrittura fallita: {e}"}, 500)
            try:
                tk_app.after(0, tk_app.refresh_gui)
            except Exception:
                pass
            return _json({"ok": True, "mt": mt})
        if os.path.exists(p):
            return _json({"ok": True, "esistente": True})
        try:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            tmp = p + ".tmp"
            with open(tmp, "wb") as f:
                f.write(raw)
            os.replace(tmp, p)
            mt = int(os.stat(p).st_mtime)
        except Exception as e:
            return _json({"ok": False, "errore": f"scrittura fallita: {e}"}, 500)
        return _json({"ok": True, "esistente": False, "mt": mt})
