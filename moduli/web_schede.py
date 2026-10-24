#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import uuid
import datetime
import threading

from moduli.modello_spesa import SpesaEntry
from moduli.web_utils import _fmt_it
from moduli import web_ricorrenze as _wr

_LOCK = threading.RLock()

_CAT_IMM = [
    "Acconto Spese Condominiali", "Assicurazione Immobile", "Canone Locazione",
    "Cedolare Secca / IRPEF", "Conguaglio Spese", "Deposito Cauzionale",
    "Elettrodomestici e Arredi", "Imposta IMU", "Interessi Mutuo Casa",
    "Manutenzione Caldaia/Clima", "Provvigioni Agenzia", "Quota Registrazione Contratto",
    "Riparazioni Elettriche", "Riparazioni Idrauliche", "Ristrutturazioni (Detraibili)",
    "Spese Condominiali Inquilino", "Spese Condominiali Proprietario",
    "Spese Legali e Contratti", "Tassa TARI (Rifiuti)", "Utenze (Luce/Gas/Acqua)", "Varie",
]
_CAT_VEI = [
    "Assicurazione", "Bollo", "Carburante", "Gomme", "Lavaggio", "Manutenzione Ordinaria",
    "Manutenzione Straordinaria", "Multe", "Parcheggio/Pedaggi", "Revisione", "Tagliando", "Varie",
]
_CAT_ANI = [
    "Alimentazione", "Veterinario", "Vaccinazioni", "Antiparassitari", "Toelettatura",
    "Farmaci", "Accessori", "Pensione/Dog-sitter", "Assicurazione", "Varie",
]

CFG = {
    "immobili": {
        "titolo": "ImmoBil", "emoji": "🏢", "icona": "🏠", "sing": "immobile", "plur": "Immobili",
        "file": "IMMOBIL_FILE", "radice": "immobili", "mov": "spese", "max": 7,
        "pref": "_immobil", "cat_export": "ImmoBil", "tag": "#immobili", "tag_exp": "#immexp:",
        "conto": "conto", "tipo_mov": True, "cat": _CAT_IMM, "url": "/immobili_web",
        "campi": [
            ("nome", "Nome", "text"), ("indirizzo", "Indirizzo", "text"),
            ("inquilino", "Inquilino", "text"), ("canone", "Canone €/mese", "num"),
            ("scadenza_contratto", "Scadenza contratto", "date"),
            ("note", "Note", "text"), ("conto", "Conto", "conto"),
        ],
        "scadenze": [("scadenza_contratto", "Contratto")],
        "extra": [],
        "nuovo": {"indirizzo": "", "inquilino": "", "canone": 0.0, "scadenza_contratto": "", "note": ""},
    },
    "autopark": {
        "titolo": "AutoPark", "emoji": "🚗", "icona": "🚗", "sing": "veicolo", "plur": "Veicoli",
        "file": "VEICOLI_FILE", "radice": "veicoli", "mov": "movimenti", "max": 7,
        "pref": "_veicoli", "cat_export": "AutoPark", "tag": "#veicoli", "tag_exp": "#vexp:",
        "conto": "conto_bancario", "tipo_mov": False, "cat": _CAT_VEI, "url": "/autopark_web",
        "campi": [
            ("nome", "Nome / Targa", "text"), ("modello", "Modello", "text"), ("targa", "Targa", "text"),
            ("km_iniziale", "Km iniziali", "num"), ("km_attuali", "Km attuali", "num"),
            ("data_immatricolazione", "Immatricolazione", "date"),
            ("scad_bollo", "Scadenza bollo", "date"),
            ("scad_assicurazione", "Scadenza assicurazione", "date"),
            ("scad_revisione", "Scadenza revisione", "date"),
            ("prossimo_tagliando_km", "Prossimo tagliando (km)", "num"),
            ("note", "Note", "text"), ("conto_bancario", "Conto bancario", "conto"),
        ],
        "scadenze": [("scad_bollo", "Bollo"), ("scad_assicurazione", "Assicurazione"),
                     ("scad_revisione", "Revisione")],
        "extra": [("km", "Km", "num"), ("litri", "Litri", "num")],
        "nuovo": {"modello": "", "targa": "", "km_iniziale": 0.0, "km_attuali": 0.0,
                  "data_immatricolazione": "", "scad_bollo": "", "scad_assicurazione": "",
                  "scad_revisione": "", "prossimo_tagliando_km": 0.0, "note": ""},
    },
    "petcare": {
        "titolo": "PetCare", "emoji": "🐾", "icona": "🐾", "sing": "animale", "plur": "Animali",
        "file": "ANIMALI_FILE", "radice": "animali", "mov": "movimenti", "max": 7,
        "pref": "_animali", "cat_export": "PetCare", "tag": "#animali", "tag_exp": "#aexp:",
        "conto": "conto_bancario", "tipo_mov": False, "cat": _CAT_ANI, "url": "/petcare_web",
        "campi": [
            ("nome", "Nome", "text"), ("razza", "Razza / Specie", "text"),
            ("microchip", "Microchip", "text"), ("peso_iniziale", "Peso iniziale (kg)", "num"),
            ("peso_attuale", "Peso attuale (kg)", "num"), ("data_nascita", "Data di nascita", "date"),
            ("scad_vaccino", "Scadenza vaccino", "date"),
            ("scad_antiparassitario", "Scadenza antiparassitario", "date"),
            ("scad_assicurazione", "Scadenza assicurazione", "date"),
            ("prossimo_controllo", "Prossimo controllo", "date"),
            ("note", "Note", "text"), ("conto_bancario", "Conto bancario", "conto"),
        ],
        "scadenze": [("scad_vaccino", "Vaccinazioni"), ("scad_antiparassitario", "Antiparassitario"),
                     ("scad_assicurazione", "Assicurazione"), ("prossimo_controllo", "Controllo")],
        "extra": [("peso", "Peso (kg)", "num"), ("quantita_cibo", "Cibo (kg)", "num")],
        "nuovo": {"razza": "", "microchip": "", "peso_iniziale": 0.0, "peso_attuale": 0.0,
                  "data_nascita": "", "scad_vaccino": "", "scad_antiparassitario": "",
                  "scad_assicurazione": "", "prossimo_controllo": "", "note": ""},
    },
}


def _parse(s):
    try:
        return datetime.datetime.strptime(s, "%d-%m-%Y").date()
    except (ValueError, TypeError):
        return None


def _iso(s):
    d = _parse(s)
    return d.isoformat() if d else ""


def _dmy(iso):
    try:
        return datetime.date.fromisoformat(str(iso)).strftime("%d-%m-%Y")
    except ValueError:
        return None


def _num(v):
    try:
        return float(str(v).strip().replace(",", "."))
    except (ValueError, TypeError):
        return None


def _fmt_n(v):
    if v in ("", None):
        return ""
    try:
        f = float(v)
    except (ValueError, TypeError):
        return str(v)
    return str(int(f)) if f == int(f) else str(round(f, 2))


def _leggi(c):
    import __main__ as _app
    f = getattr(_app, c["file"])
    db = {c["radice"]: []}
    if os.path.exists(f) and os.path.getsize(f) > 0:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                d = json.load(fh)
        except Exception:
            raise ValueError(f"il file {os.path.basename(f)} risulta illeggibile o corrotto: nessuna modifica effettuata")
        if not (isinstance(d, dict) and isinstance(d.get(c["radice"]), list)):
            raise ValueError(f"formato di {os.path.basename(f)} non riconosciuto: nessuna modifica effettuata")
        db = d
    return f, db


def _salva(f, db):
    os.makedirs(os.path.dirname(f), exist_ok=True)
    tmp = f + ".web.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(db, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, f)


def _stato_scadenza(data_str):
    d = _parse(data_str)
    if not d:
        return "nd", "Non impostata", None
    g = (d - datetime.date.today()).days
    if g < 0:
        return "rosso", f"SCADUTA da {abs(g)} gg ({data_str})", g
    if g == 0:
        return "rosso", f"Scade OGGI ({data_str})", g
    stato = "rosso" if g <= 15 else ("ambra" if g <= 45 else "verde")
    return stato, f"tra {g} gg ({data_str})", g


def _info(k, it, movs):
    righe = []
    tot = sum((_num(m.get("importo", 0)) or 0.0) for m in movs)
    if k == "autopark":
        ki, ka = _num(it.get("km_iniziale")) or 0.0, _num(it.get("km_attuali")) or 0.0
        if ka - ki > 0 and tot:
            righe.append(f"Costo al km: € {_fmt_it(tot / (ka - ki), ',.3f')}")
        rif = []
        for m in movs:
            if m.get("categoria") == "Carburante" and _num(m.get("km")) and _num(m.get("litri")):
                rif.append((_num(m["km"]), _num(m["litri"])))
        rif.sort()
        val = [l2 / (k2 - k1) * 100 for (k1, _), (k2, l2) in zip(rif, rif[1:]) if k2 > k1 and l2 > 0]
        if val:
            righe.append(f"Consumo medio: {_fmt_it(sum(val) / len(val), ',.1f')} l/100 km")
        tg = _num(it.get("prossimo_tagliando_km"))
        if tg and ka:
            righe.append(f"Prossimo tagliando: {_fmt_n(tg)} km (mancano {_fmt_n(max(tg - ka, 0))} km)")
    elif k == "petcare":
        d = _parse(it.get("data_nascita"))
        if d and (datetime.date.today() - d).days > 0 and tot:
            mesi = (datetime.date.today() - d).days / 30.44
            righe.append(f"Costo medio mensile: € {_fmt_it(tot / mesi)}")
        rif = []
        for m in movs:
            dd = _parse(m.get("data", ""))
            if m.get("categoria") == "Alimentazione" and dd and _num(m.get("quantita_cibo")):
                rif.append((dd, _num(m["quantita_cibo"])))
        rif.sort()
        val = [q2 / (d2 - d1).days * 30.44 for (d1, _), (d2, q2) in zip(rif, rif[1:])
               if (d2 - d1).days > 0 and q2 > 0]
        if val:
            righe.append(f"Consumo medio cibo: {_fmt_it(sum(val) / len(val), ',.1f')} kg/mese")
    else:
        can = _num(it.get("canone")) or 0.0
        if can:
            righe.append(f"Canone annuo: € {_fmt_it(can * 12)}")
    return righe


def _json_item(c, k, it):
    movs = it.get(c["mov"], []) or []
    campi = {}
    for key, _et, tipo in c["campi"]:
        v = it.get(key, "")
        if tipo == "date":
            v = _iso(v)
        elif tipo == "num":
            v = _fmt_n(v)
        elif tipo == "conto":
            v = "" if v in (None, "(nessuno)") else str(v)
        else:
            v = "" if v is None else str(v)
        campi[key] = v
    scad = []
    peggiore = None
    for key, et in c["scadenze"]:
        stato, testo, g = _stato_scadenza(it.get(key, ""))
        scad.append({"label": et, "stato": stato, "testo": testo})
        if g is not None and (peggiore is None or g < peggiore[0]):
            peggiore = (g, et, stato, testo)
    mov_out = []
    ent = usc = 0.0
    da_esp = 0
    for m in sorted(movs, key=lambda x: _iso(x.get("data", "")), reverse=True):
        try:
            imp = float(m.get("importo", 0) or 0)
        except (ValueError, TypeError):
            imp = 0.0
        tipo = "Uscita"
        if c["tipo_mov"] and str(m.get("tipo", "")).lower() == "entrata":
            tipo = "Entrata"
        if tipo == "Entrata":
            ent += imp
        else:
            usc += imp
        if not m.get("esportato"):
            da_esp += 1
        mov_out.append({
            "id": m.get("id", ""), "data": m.get("data", ""), "iso": _iso(m.get("data", "")),
            "cat": m.get("categoria", ""), "desc": m.get("descrizione", ""),
            "imp": imp, "imp_str": _fmt_it(imp), "tipo": tipo, "esp": bool(m.get("esportato")),
            "extra": {e[0]: _fmt_n(m.get(e[0], "")) for e in c["extra"]},
        })
    nome = str(it.get("nome", ""))
    if k == "immobili":
        sub = " · ".join(x for x in (it.get("indirizzo", ""), it.get("inquilino", "")) if x)
    elif k == "autopark":
        sub = " · ".join(x for x in (it.get("modello", ""), it.get("targa", "")) if x)
        if _num(it.get("km_attuali")):
            sub += (" · " if sub else "") + _fmt_n(it.get("km_attuali")) + " km"
    else:
        sub = " · ".join(x for x in (it.get("razza", ""),
                                     (_fmt_n(it.get("peso_attuale")) + " kg") if _num(it.get("peso_attuale")) else "") if x)
    return {
        "id": it.get("id", ""), "nome": nome, "sub": sub, "campi": campi, "scadenze": scad,
        "prossima": ({"label": peggiore[1], "stato": peggiore[2], "testo": peggiore[3]} if peggiore else None),
        "categorie": list(it.get("categorie") or c["cat"]),
        "movimenti": mov_out, "n_mov": len(mov_out), "da_esportare": da_esp,
        "ent_str": _fmt_it(ent), "usc_str": _fmt_it(usc), "saldo": ent - usc,
        "saldo_str": _fmt_it(abs(ent - usc)), "info": _info(k, it, movs),
    }


def _aggiorna_gui(self, nuova_cat=False):
    try:
        self.after(0, self.refresh_gui)
        if nuova_cat and hasattr(self, "aggiorna_combobox_categorie"):
            self.after(0, self.aggiorna_combobox_categorie)
    except Exception:
        pass


def _assegna_id_mov(c, db):
    cambiato = False
    for it in db[c["radice"]]:
        if not isinstance(it, dict):
            continue
        for m in it.get(c["mov"], []) or []:
            if isinstance(m, dict) and not m.get("id"):
                m["id"] = str(uuid.uuid4())
                cambiato = True
    return cambiato


def _desktop_aperto(self, c):
    return bool(getattr(self, c["pref"] + "_win", None))


def _blocco_desktop(self, c, azione):
    if _desktop_aperto(self, c):
        return {"ok": False, "errore": f"Chiudi la finestra {c['titolo']} sul desktop prima di {azione} dal web."}, 409
    return None


def _in_place(cur, nuovo):
    cambiate = set()
    for key in list(cur.keys()):
        if key not in nuovo:
            del cur[key]
            cambiate.add(key)
    for key, val in nuovo.items():
        if cur.get(key) != val or key not in cur:
            cambiate.add(key)
        if isinstance(cur.get(key), list) and isinstance(val, list):
            cur[key][:] = val
        else:
            cur[key] = val
    return cambiate


def _applica_desktop(self, c, fresco):
    try:
        dbd = getattr(self, c["pref"] + "_db", None)
        if not getattr(self, c["pref"] + "_win", None) or dbd is None:
            return
        per_id = {x.get("id"): x for x in dbd[c["radice"]] if isinstance(x, dict) and x.get("id")}
        refresh = getattr(self, c["pref"] + "_refresh", None) or {}
        for nuovo in fresco[c["radice"]]:
            cur = per_id.get(nuovo.get("id"))
            if cur is None:
                continue
            cambiate = _in_place(cur, nuovo)
            fn = refresh.get(id(cur))
            if fn:
                try:
                    fn(cambiate)
                except Exception:
                    pass
    except Exception:
        pass


def _sync_desktop(self, c):
    if not _desktop_aperto(self, c):
        return
    try:
        with _LOCK:
            _f, fresco = _leggi(c)
        self.after(0, lambda: _applica_desktop(self, c, fresco))
    except Exception:
        pass


def _elenco(self, k, c):
    with _LOCK:
        f, db = _leggi(c)
        if _assegna_id_mov(c, db):
            _salva(f, db)
            _sync_desktop(self, c)
        items = [_json_item(c, k, it) for it in db[c["radice"]] if isinstance(it, dict)]
    conti, princ = _wr._conti_portafoglio()
    return {
        "ok": True, "items": items, "conti": conti, "conto_principale": princ,
        "campi": [{"k": a, "l": b, "t": t} for a, b, t in c["campi"]],
        "extra": [{"k": a, "l": b} for a, b, _t in c["extra"]],
        "tipo_mov": c["tipo_mov"], "max": c["max"], "sing": c["sing"],
        "oggi": datetime.date.today().isoformat(),
    }


def _trova(db, c, iid):
    return next((x for x in db[c["radice"]] if x.get("id") == iid), None)


def _nuovo(self, k, c, d):
    b = _blocco_desktop(self, c, "creare una scheda")
    if b:
        return b
    nome = str(d.get("nome", "")).strip()[:22]
    if not nome:
        return {"ok": False, "errore": "Inserisci un nome."}, 400
    with _LOCK:
        f, db = _leggi(c)
        if len(db[c["radice"]]) >= c["max"]:
            return {"ok": False, "errore": f"Limite raggiunto: massimo {c['max']} {c['plur'].lower()}."}, 400
        nuovo = {"id": str(uuid.uuid4()), "nome": nome}
        nuovo.update(c["nuovo"])
        nuovo["categorie"] = list(c["cat"])
        nuovo[c["mov"]] = []
        db[c["radice"]].append(nuovo)
        _salva(f, db)
    return {"ok": True, "id": nuovo["id"]}, 200


def _salva_ana(self, k, c, d):
    campi = d.get("campi") or {}
    conti, _ = _wr._conti_portafoglio()
    with _LOCK:
        f, db = _leggi(c)
        it = _trova(db, c, str(d.get("id", "")))
        if it is None:
            return {"ok": False, "errore": "Scheda non trovata."}, 404
        nuovi = {}
        for key, et, tipo in c["campi"]:
            if key not in campi:
                continue
            v = str(campi[key] if campi[key] is not None else "").strip()
            if tipo == "date":
                if v:
                    v = _dmy(v)
                    if v is None:
                        return {"ok": False, "errore": f"Data non valida: {et}."}, 400
            elif tipo == "num":
                if v:
                    n = _num(v)
                    if n is None or n < 0:
                        return {"ok": False, "errore": f"Valore non valido: {et}."}, 400
                    v = n
                else:
                    v = 0.0
            elif tipo == "conto":
                if v and v != "(nessuno)" and v not in conti:
                    return {"ok": False, "errore": "Conto non valido."}, 400
                v = v if v else "(nessuno)"
            elif key == "nome":
                v = v[:22]
                if not v:
                    return {"ok": False, "errore": "Il nome è obbligatorio."}, 400
            nuovi[key] = v
        it.update(nuovi)
        _salva(f, db)
    return {"ok": True}, 200


def _elimina(self, k, c, d):
    b = _blocco_desktop(self, c, "eliminare una scheda")
    if b:
        return b
    with _LOCK:
        f, db = _leggi(c)
        n0 = len(db[c["radice"]])
        db[c["radice"]] = [x for x in db[c["radice"]] if x.get("id") != str(d.get("id", ""))]
        if len(db[c["radice"]]) == n0:
            return {"ok": False, "errore": "Scheda non trovata."}, 404
        _salva(f, db)
    return {"ok": True}, 200


def _mov_salva(self, k, c, d):
    data = _dmy(d.get("data", ""))
    if not data:
        return {"ok": False, "errore": "Data non valida."}, 400
    imp = _num(d.get("imp"))
    if imp is None or imp <= 0:
        return {"ok": False, "errore": "Importo mancante o non valido."}, 400
    cat = str(d.get("cat", "")).strip()
    if not cat:
        return {"ok": False, "errore": "Categoria obbligatoria."}, 400
    desc = str(d.get("desc", "")).strip()
    extra = {}
    for key, et, _t in c["extra"]:
        raw = str((d.get("extra") or {}).get(key, "")).strip()
        if raw:
            n = _num(raw)
            if n is None or n < 0:
                return {"ok": False, "errore": f"Valore non valido: {et}."}, 400
            extra[key] = n
        else:
            extra[key] = ""
    tipo = "Uscita"
    if c["tipo_mov"]:
        tipo = "Entrata" if str(d.get("tipo", "")) == "Entrata" else "Uscita"
    with _LOCK:
        f, db = _leggi(c)
        it = _trova(db, c, str(d.get("id", "")))
        if it is None:
            return {"ok": False, "errore": "Scheda non trovata."}, 404
        cats = it.setdefault("categorie", list(c["cat"]))
        if cat not in cats:
            cats.append(cat)
        lista = it.setdefault(c["mov"], [])
        mid = str(d.get("mov_id", "") or "")
        riga = next((m for m in lista if m.get("id") == mid), None) if mid else None
        if mid and riga is None:
            return {"ok": False, "errore": "Movimento non trovato."}, 404
        if riga is None:
            riga = {"id": str(uuid.uuid4())}
            lista.append(riga)
        riga.update({"data": data, "categoria": cat, "descrizione": desc, "importo": imp})
        riga.update(extra)
        if c["tipo_mov"]:
            riga["tipo"] = tipo
        if k == "autopark" and extra.get("km"):
            if extra["km"] > (_num(it.get("km_attuali")) or 0.0):
                it["km_attuali"] = float(extra["km"])
        if k == "petcare" and extra.get("peso"):
            it["peso_attuale"] = float(extra["peso"])
        _salva(f, db)
    return {"ok": True}, 200


def _mov_elimina(self, k, c, d):
    ids = {str(x) for x in (d.get("ids") or [])}
    if not ids:
        return {"ok": False, "errore": "Nessun movimento selezionato."}, 400
    with _LOCK:
        f, db = _leggi(c)
        it = _trova(db, c, str(d.get("id", "")))
        if it is None:
            return {"ok": False, "errore": "Scheda non trovata."}, 404
        prima = len(it.get(c["mov"], []))
        it[c["mov"]] = [m for m in it.get(c["mov"], []) if m.get("id") not in ids]
        n = prima - len(it[c["mov"]])
        _salva(f, db)
    return {"ok": True, "eliminati": n}, 200


def _smarca(self, k, c, d):
    ids = {str(x) for x in (d.get("ids") or [])}
    with _LOCK:
        f, db = _leggi(c)
        it = _trova(db, c, str(d.get("id", "")))
        if it is None:
            return {"ok": False, "errore": "Scheda non trovata."}, 404
        n = 0
        for m in it.get(c["mov"], []):
            if m.get("id") in ids and m.get("esportato"):
                m["esportato"] = None
                n += 1
        if n:
            _salva(f, db)
    if not n:
        return {"ok": False, "errore": "Le voci selezionate non risultano esportate."}, 400
    return {"ok": True, "smarcate": n}, 200


def _esporta(self, k, c, d):
    ids = {str(x) for x in (d.get("ids") or [])}
    modo = "righe" if d.get("modo") == "righe" else "saldo"
    with _LOCK:
        f, db = _leggi(c)
        it = _trova(db, c, str(d.get("id", "")))
        if it is None:
            return {"ok": False, "errore": "Scheda non trovata."}, 404
        sel = [m for m in it.get(c["mov"], []) if m.get("id") in ids and not m.get("esportato")]
        if not sel:
            return {"ok": False, "errore": "Nessuna voce da esportare tra quelle selezionate."}, 400
        nome = it.get("nome", c["sing"].capitalize())
        conto = str(it.get(c["conto"], "") or "")
        conto = "" if conto == "(nessuno)" else conto
        oggi = datetime.date.today()
        nuova_cat = False
        if c["cat_export"] not in self.categorie:
            self.categorie.append(c["cat_export"])
            nuova_cat = True

        def _tipo(m):
            return "Entrata" if c["tipo_mov"] and str(m.get("tipo", "")).lower() == "entrata" else "Uscita"

        def _imp(m):
            try:
                return float(m.get("importo", 0) or 0)
            except (ValueError, TypeError):
                return 0.0
        creati = 0
        if modo == "saldo":
            saldo = sum(_imp(m) if _tipo(m) == "Entrata" else -_imp(m) for m in sel)
            if saldo == 0:
                return {"ok": False, "errore": "Saldo zero, nessun movimento esportato."}, 400
            eid = str(uuid.uuid4())
            desc = f"Saldo {nome}" if len(sel) <= 1 else f"Saldo {nome} ({len(sel)} mov.)"
            self.spese.setdefault(oggi, []).append(SpesaEntry.nuova(
                c["cat_export"], desc, abs(saldo), "Entrata" if saldo >= 0 else "Uscita",
                conto=conto, hashtag=[c["tag"], f"{c['tag_exp']}{eid}"]))
            for m in sel:
                m["esportato"] = eid
            creati = 1
            msg = f"Saldo {nome} ({'Entrata' if saldo >= 0 else 'Uscita'} € {_fmt_it(abs(saldo))}) esportato"
        else:
            for m in sel:
                imp = _imp(m)
                if imp == 0:
                    continue
                eid = str(uuid.uuid4())
                cat_o, desc_o = m.get("categoria", ""), m.get("descrizione", "")
                desc = f"{nome}: {cat_o}" if cat_o else nome
                if desc_o:
                    desc += f" - {desc_o}"
                self.spese.setdefault(oggi, []).append(SpesaEntry.nuova(
                    c["cat_export"], desc, imp, _tipo(m), conto=conto,
                    hashtag=[c["tag"], f"{c['tag_exp']}{eid}"]))
                m["esportato"] = eid
                creati += 1
            if not creati:
                return {"ok": False, "errore": "Nessuna voce valida da esportare."}, 400
            msg = f"{creati} voce/i di {nome} esportate singolarmente"
        _salva(f, db)
        self.save_db()
    try:
        self.registra_azione_gamification("movimento")
    except Exception:
        pass
    _aggiorna_gui(self, nuova_cat)
    return {"ok": True, "creati": creati, "msg": msg}, 200


_AZIONI = {
    "nuovo": _nuovo, "salva_ana": _salva_ana, "elimina": _elimina, "mov_salva": _mov_salva,
    "mov_elimina": _mov_elimina, "esporta": _esporta, "smarca": _smarca,
}


def schede_web_api(self, chiave, azione, dati=None):
    c = CFG.get(chiave)
    if c is None:
        return {"ok": False, "errore": "Modulo sconosciuto."}, 404
    try:
        if azione == "elenco":
            return _elenco(self, chiave, c), 200
        fn = _AZIONI.get(azione)
        if fn is None:
            return {"ok": False, "errore": "Azione sconosciuta."}, 404
        esito = fn(self, chiave, c, dati or {})
        if esito[1] == 200:
            _sync_desktop(self, c)
        return esito
    except Exception as e:
        return {"ok": False, "errore": f"Errore: {e}"}, 500


_JS_SPEC = r"""
    var CHIAVE = '__CHIAVE__', API = '/api/schede/__CHIAVE__/', EMOJI = '__EMOJI__';
    var DATI = null, curId = null, tab = 'mov', fAnno = '', fCat = '', sel = {}, movAperto = null;
    function modOpen() { return curId ? DATI.items.find(function(x) { return x.id === curId; }) : null; }
    function statoCol(s) { return s === 'rosso' ? 'var(--red)' : s === 'ambra' ? 'var(--orange)' : s === 'verde' ? 'var(--green)' : 'var(--text-dim)'; }
    function disegna() {
        var el = $('elenco'); el.innerHTML = '';
        if (!DATI.items.length) { el.innerHTML = '<div class="vuoto">Nessun elemento. Tocca + per crearne uno.</div>'; return; }
        DATI.items.forEach(function(x) {
            var d = document.createElement('div'); d.className = 'ric';
            var h = '<div class="riga1"><span class="cat">' + EMOJI + ' ' + esc(x.nome) + '</span><span class="imp">€ ' + esc(x.usc_str) + '</span></div>';
            if (x.sub) h += '<div class="meta">' + esc(x.sub) + '</div>';
            if (x.prossima) h += '<div class="meta" style="color:' + statoCol(x.prossima.stato) + '">⏰ ' + esc(x.prossima.label) + ': ' + esc(x.prossima.testo) + '</div>';
            h += '<div class="meta">' + x.n_mov + ' movimenti' + (x.da_esportare ? ' · ' + x.da_esportare + ' da esportare' : '') + '</div>';
            d.innerHTML = h; d.onclick = function() { apri(x.id); };
            el.appendChild(d);
        });
    }
    async function carica(riapri) {
        var j = await chiama(API + 'elenco');
        if (!j) return;
        DATI = j; disegna();
        if (riapri && curId) { if (modOpen()) disegnaScheda(); else chiudi(); }
    }
    function chiudi() { $('velo').style.display = 'none'; document.body.style.overflow = ''; curId = null; sel = {}; }
    function chiudi2() { $('velo2').style.display = 'none'; movAperto = null; }
    function apri(id) { curId = id; tab = 'mov'; fAnno = ''; fCat = ''; sel = {}; $('velo').style.display = 'block'; document.body.style.overflow = 'hidden'; disegnaScheda(); }
    function setTab(t) { tab = t; disegnaScheda(); }
    function movFiltrati(x) {
        return x.movimenti.filter(function(m) {
            return (!fAnno || m.iso.slice(0, 4) === fAnno) && (!fCat || m.cat === fCat);
        });
    }
    function disegnaScheda() {
        var x = modOpen(); if (!x) return;
        var h = '<div class="sh"><h3>' + EMOJI + ' ' + esc(x.nome) + '</h3><button class="x" onclick="chiudi()">✕</button></div>';
        h += '<div class="tabs"><button class="' + (tab === 'mov' ? 'on' : '') + '" onclick="setTab(\'mov\')">Movimenti</button><button class="' + (tab === 'ana' ? 'on' : '') + '" onclick="setTab(\'ana\')">Anagrafica</button></div>';
        h += tab === 'mov' ? htmlMov(x) : htmlAna(x);
        $('scheda').innerHTML = h;
    }
    function htmlMov(x) {
        var anni = {}; x.movimenti.forEach(function(m) { if (m.iso) anni[m.iso.slice(0, 4)] = 1; });
        if (fAnno && !anni[fAnno]) fAnno = '';
        var h = '<div class="due"><div class="campo"><label>Anno</label><select onchange="fAnno=this.value;disegnaScheda()"><option value="">Tutti</option>';
        Object.keys(anni).sort().reverse().forEach(function(a) { h += '<option' + (a === fAnno ? ' selected' : '') + '>' + a + '</option>'; });
        h += '</select></div><div class="campo"><label>Categoria</label><select onchange="fCat=this.value;disegnaScheda()"><option value="">Tutte</option>';
        x.categorie.forEach(function(c) { h += '<option' + (c === fCat ? ' selected' : '') + '>' + esc(c) + '</option>'; });
        h += '</select></div></div>';
        var lista = movFiltrati(x), ent = 0, usc = 0;
        lista.forEach(function(m) { if (m.tipo === 'Entrata') ent += m.imp; else usc += m.imp; });
        function f(v) { return v.toLocaleString('it-IT', {minimumFractionDigits: 2, maximumFractionDigits: 2}); }
        if (DATI.tipo_mov) h += '<div class="riepilogo"><span>Entrate <b class="pos">€ ' + f(ent) + '</b></span><span>Uscite <b class="neg">€ ' + f(usc) + '</b></span><span>Saldo <b class="' + (ent - usc >= 0 ? 'pos' : 'neg') + '">€ ' + f(ent - usc) + '</b></span></div>';
        else h += '<div class="riepilogo"><span>Totale spese</span><b class="neg">€ ' + f(usc) + '</b></div>';
        h += '<button class="btn ok" style="width:100%;margin-bottom:8px" onclick="apriMov(null)">＋ Nuovo movimento</button>';
        if (!lista.length) h += '<div class="vuoto">Nessun movimento.</div>';
        lista.forEach(function(m) {
            var ex = []; DATI.extra.forEach(function(e) { if (m.extra[e.k]) ex.push(esc(e.l) + ' ' + esc(m.extra[e.k])); });
            h += '<div class="mv' + (m.esp ? ' esp' : '') + '"><input type="checkbox" class="ck" ' + (sel[m.id] ? 'checked' : '') + ' onchange="togSel(\'' + m.id + '\',this.checked)">';
            h += '<div class="mb" onclick="apriMov(\'' + m.id + '\')"><div class="riga1"><span class="cat">' + esc(m.cat) + '</span><span class="imp ' + (m.tipo === 'Entrata' ? 'pos' : 'neg') + '">€ ' + (m.tipo === 'Entrata' ? '+' : '-') + esc(m.imp_str) + '</span></div>';
            h += '<div class="meta">' + esc(m.data) + (m.desc ? ' · ' + esc(m.desc) : '') + (ex.length ? ' · ' + ex.join(' · ') : '') + (m.esp ? ' · ✔ esportato' : '') + '</div></div></div>';
        });
        h += '<div class="azioni"><button class="btn no" onclick="selDaEsp()">☑ Da esportare</button><button class="btn no" onclick="esporta(\'saldo\')">📤 Saldo unico</button><button class="btn no" onclick="esporta(\'righe\')">📤 Righe</button><button class="btn no" onclick="smarca()">↩ Smarca</button><button class="btn del" onclick="eliminaSel()">🗑 Elimina</button></div>';
        return h;
    }
    function togSel(id, on) { if (on) sel[id] = 1; else delete sel[id]; }
    function selDaEsp() {
        var x = modOpen(); sel = {};
        movFiltrati(x).forEach(function(m) { if (!m.esp) sel[m.id] = 1; });
        if (!Object.keys(sel).length) msg('Nessuna voce da esportare', true);
        disegnaScheda();
    }
    function idsSel() {
        var vis = {}; movFiltrati(modOpen()).forEach(function(m) { vis[m.id] = 1; });
        return Object.keys(sel).filter(function(i) { return vis[i]; });
    }
    async function esporta(modo) {
        if (!idsSel().length) { msg('Seleziona almeno una riga', true); return; }
        var j = await chiama(API + 'esporta', {id: curId, ids: idsSel(), modo: modo});
        if (!j) return;
        sel = {}; msg(j.msg); carica(true);
    }
    async function smarca() {
        if (!idsSel().length) { msg('Seleziona almeno una riga', true); return; }
        var j = await chiama(API + 'smarca', {id: curId, ids: idsSel()});
        if (!j) return;
        sel = {}; msg(j.smarcate + ' voce/i smarcata/e'); carica(true);
    }
    function eliminaSel() {
        if (!idsSel().length) { msg('Seleziona almeno una riga', true); return; }
        var n = idsSel().length;
        apriModalConferma('Eliminare ' + n + ' movimento/i?', async function() {
            var j = await chiama(API + 'mov_elimina', {id: curId, ids: idsSel()});
            if (!j) return;
            sel = {}; msg('Movimenti eliminati'); carica(true);
        });
    }
    function htmlAna(x) {
        var h = '';
        if (x.scadenze.length) {
            h += '<div class="scad">';
            x.scadenze.forEach(function(s) { h += '<div class="dt"><span>' + esc(s.label) + '</span><span style="color:' + statoCol(s.stato) + '">' + esc(s.testo) + '</span></div>'; });
            h += '</div>';
        }
        x.info.forEach(function(r) { h += '<div class="meta" style="margin-bottom:4px">📊 ' + esc(r) + '</div>'; });
        h += '<div style="margin-top:10px">';
        DATI.campi.forEach(function(c) {
            var v = x.campi[c.k];
            h += '<div class="campo"><label>' + esc(c.l) + '</label>';
            if (c.t === 'date') h += '<input type="date" id="a_' + c.k + '" value="' + esc(v) + '">';
            else if (c.t === 'num') h += '<input type="text" inputmode="decimal" id="a_' + c.k + '" value="' + esc(v) + '">';
            else if (c.t === 'conto') {
                h += '<select id="a_' + c.k + '"><option value="">(nessuno)</option>';
                DATI.conti.forEach(function(n) { h += '<option' + (n === v ? ' selected' : '') + '>' + esc(n) + '</option>'; });
                h += '</select>';
            } else h += '<input type="text" id="a_' + c.k + '" value="' + esc(v) + '" autocomplete="off">';
            h += '</div>';
        });
        h += '</div><div class="btns"><button class="btn del" onclick="eliminaScheda()">🗑 Elimina</button><button class="btn ok" onclick="salvaAna()">Salva</button></div>';
        return h;
    }
    async function salvaAna() {
        var campi = {};
        DATI.campi.forEach(function(c) { campi[c.k] = $('a_' + c.k).value; });
        var j = await chiama(API + 'salva_ana', {id: curId, campi: campi});
        if (!j) return;
        msg('Anagrafica salvata'); carica(true);
    }
    function eliminaScheda() {
        var x = modOpen();
        apriModalConferma('Eliminare "' + x.nome + '" e tutti i suoi movimenti?', async function() {
            var j = await chiama(API + 'elimina', {id: curId});
            if (!j) return;
            chiudi(); msg('Eliminato'); carica();
        });
    }
    function apriMov(mid) {
        var x = modOpen(); movAperto = mid;
        var m = mid ? x.movimenti.find(function(r) { return r.id === mid; }) : null;
        var h = '<h3>' + (m ? 'Modifica movimento' : 'Nuovo movimento') + '</h3>';
        if (DATI.tipo_mov) h += '<div class="campo"><label>Tipo</label><select id="m_tipo"><option' + (m && m.tipo === 'Uscita' ? ' selected' : '') + '>Uscita</option><option' + (m && m.tipo === 'Entrata' ? ' selected' : '') + '>Entrata</option></select></div>';
        h += '<div class="due"><div class="campo"><label>Data</label><input type="date" id="m_data" value="' + esc(m ? m.iso : DATI.oggi) + '"></div>';
        h += '<div class="campo"><label>Importo (€)</label><input type="text" inputmode="decimal" id="m_imp" placeholder="0,00" value="' + (m ? esc(String(m.imp).replace('.', ',')) : '') + '"></div></div>';
        h += '<div class="campo"><label>Categoria</label><select id="m_cat" onchange="$(\'m_nc\').style.display = this.value === \'__nuova__\' ? \'block\' : \'none\'">';
        x.categorie.forEach(function(c) { h += '<option' + (m && m.cat === c ? ' selected' : '') + '>' + esc(c) + '</option>'; });
        h += '<option value="__nuova__">➕ Nuova categoria…</option></select><input type="text" id="m_nc" placeholder="Nome nuova categoria" style="display:none;margin-top:6px"></div>';
        h += '<div class="campo"><label>Descrizione</label><input type="text" id="m_desc" autocomplete="off" value="' + esc(m ? m.desc : '') + '"></div>';
        if (DATI.extra.length) {
            h += '<div class="due">';
            DATI.extra.forEach(function(e) { h += '<div class="campo"><label>' + esc(e.l) + '</label><input type="text" inputmode="decimal" id="e_' + e.k + '" value="' + esc(m ? m.extra[e.k] : '') + '"></div>'; });
            h += '</div>';
        }
        h += '<div class="btns"><button class="btn no" onclick="chiudi2()">Annulla</button><button class="btn ok" id="btnSalvaMov" onclick="salvaMov()">Salva</button></div>';
        $('scheda2').innerHTML = h; $('velo2').style.display = 'block';
    }
    async function salvaMov() {
        var cat = $('m_cat').value;
        if (cat === '__nuova__') cat = $('m_nc').value.trim();
        var extra = {}; DATI.extra.forEach(function(e) { extra[e.k] = $('e_' + e.k).value; });
        var corpo = {id: curId, mov_id: movAperto || '', data: $('m_data').value, imp: $('m_imp').value, cat: cat, desc: $('m_desc').value, extra: extra};
        if (DATI.tipo_mov) corpo.tipo = $('m_tipo').value;
        var j = await chiama(API + 'mov_salva', corpo);
        if (!j) return;
        chiudi2(); msg('Movimento salvato'); carica(true);
    }
    var inAttesaConferma = null;
    function apriModalConferma(testo, fn) { inAttesaConferma = fn; $('modalConfermaText').textContent = testo; $('confermaModal').style.display = 'flex'; }
    function chiudiModalConferma() { $('confermaModal').style.display = 'none'; inAttesaConferma = null; }
    function eseguiConferma() { var fn = inAttesaConferma; chiudiModalConferma(); if (fn) fn(); }
    function apriNuovo() {
        if (!DATI) return;
        var h = '<h3>Nuovo ' + esc(DATI.sing) + '</h3><div class="campo"><label>Nome</label><input type="text" id="n_nome" maxlength="22" autocomplete="off"></div>';
        h += '<div class="btns"><button class="btn no" onclick="chiudi2()">Annulla</button><button class="btn ok" id="btnCrea" onclick="creaNuovo()">Crea</button></div>';
        $('scheda2').innerHTML = h; $('velo2').style.display = 'block';
    }
    async function creaNuovo() {
        var j = await chiama(API + 'nuovo', {nome: $('n_nome').value});
        if (!j) return;
        chiudi2(); msg('Creato'); await carica(); apri(j.id); setTab('ana');
    }
    document.addEventListener('keydown', function(e) {
        if (e.key !== 'Escape') return;
        if ($('confermaModal').style.display === 'flex') chiudiModalConferma();
        else if ($('velo2').style.display === 'block') chiudi2();
        else chiudi();
    });
    window.addEventListener('load', function() { applyTheme(localStorage.getItem('theme') || 'dark'); carica(); });
"""

_CSS_EXTRA = """
    .tabs { display:flex; gap:6px; margin-bottom:12px; }
    .tabs button { flex:1; padding:10px; border-radius:10px; border:1px solid var(--border); background:var(--surface3); color:var(--text-mid); font-family:inherit; font-weight:700; cursor:pointer; }
    .tabs button.on { border-color:var(--gold); color:var(--gold); }
    .sh { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }
    .sh h3 { margin:0; }
    .x { background:var(--surface3); border:1px solid var(--border); color:var(--text-mid); width:34px; height:34px; border-radius:10px; cursor:pointer; font-size:1em; }
    .mv { display:flex; gap:8px; align-items:flex-start; padding:8px 4px; border-bottom:1px solid var(--border); }
    .mv.esp { opacity:0.6; }
    .mv .mb { flex:1; cursor:pointer; min-width:0; }
    .ck { width:20px; height:20px; margin-top:3px; flex:none; accent-color:var(--gold); }
    .azioni { display:flex; flex-wrap:wrap; gap:6px; margin-top:12px; }
    .azioni .btn { flex:1 1 45%; padding:10px 6px; font-size:0.8em; }
    .scad { margin-bottom:8px; }
    #velo2 { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.6); z-index:600; overflow-y:auto; }
    .riepilogo span b { margin-left:4px; }
    input[type=checkbox] { width:20px; }
"""


def _costruisci(chiave):
    c = CFG[chiave]
    base = _wr._PAGINA
    css = base[base.index("<style>") + 7:base.index("</style>")]
    js_comune = base[base.index("    var $ = function"):base.index("    function disegna()")]
    js_comune = js_comune.replace("var DATI = null, tipoVoce = 'Uscita', aperta = null;", "")
    menu = base[base.index('<div id="extraMenu"'):base.index('<div class="header-title">')]
    js_spec = _JS_SPEC.replace("__CHIAVE__", chiave).replace("__EMOJI__", c["icona"])
    # dalla pagina Ricorrenze erediamo anche le funzioni di conferma: qui sono ridefinite
    html = (
        '<!DOCTYPE html>\n<html lang="it">\n<head>\n<meta charset="utf-8">\n'
        f'<title>{c["emoji"]} {c["titolo"]}</title>\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<script>(function(){ if (localStorage.getItem('theme') === 'light') document.documentElement.classList.add('light'); })();</script>\n"
        '<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">\n'
        f"<style>{css}{_CSS_EXTRA}</style>\n<script>\n{js_comune}\n{js_spec}\n</script>\n</head>\n<body>\n<header>\n"
        '    <button class="menu-btn" onclick="toggleMenu()">⚙️</button>\n    '
        f'{menu}<div class="header-title">{c["emoji"]} {c["titolo"]}</div>\n'
        '    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>\n</header>\n'
        '<main>\n    <div id="elenco"></div>\n</main>\n'
        f'<button id="fab" onclick="apriNuovo()" title="Nuovo {c["sing"]}">＋</button>\n'
        '<div id="velo" onclick="if (event.target === this) chiudi()"><div class="scheda" id="scheda"></div></div>\n'
        '<div id="velo2" onclick="if (event.target === this) chiudi2()"><div class="scheda" id="scheda2"></div></div>\n'
        '<div id="confermaModal" class="modal-overlay"><div class="modal-box"><div class="modal-title">⚠️ Conferma</div>'
        '<div class="modal-text" id="modalConfermaText"></div><div class="modal-btns">'
        '<button class="m-btn m-cancel" onclick="chiudiModalConferma()">Annulla</button>'
        '<button class="m-btn m-confirm" onclick="eseguiConferma()">Conferma</button></div></div></div>\n'
        '<div id="msg"></div>\n</body>\n</html>\n'
    )
    return html


_CACHE = {}


def pagina_schede_web(self, chiave):
    if chiave not in CFG:
        return "Modulo sconosciuto"
    if chiave not in _CACHE:
        _CACHE[chiave] = _costruisci(chiave)
    return _CACHE[chiave].replace("__ANNO__", str(datetime.date.today().year))
