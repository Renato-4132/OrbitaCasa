#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import calendar
import datetime
import json
import os
import re
import uuid

from moduli.modello_spesa import campo

_RE_MIGLIAIA = re.compile(r"^\d{1,3}(\.\d{3})+$")

def _num(v, default=0.0):
    if v is None:
        return default
    if isinstance(v, bool):
        return default
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace("€", "").replace("%", "").replace(" ", "").strip()
    if not s:
        return default
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif _RE_MIGLIAIA.match(s):
        s = s.replace(".", "")
    try:
        x = float(s)
    except ValueError:
        return default
    if x != x or x in (float("inf"), float("-inf")):
        return default
    return x


def _rata_francese(capitale, tasso_mensile, mesi):
    if mesi <= 0:
        return 0.0
    try:
        if tasso_mensile > 0:
            f = (1 + tasso_mensile) ** mesi
            return capitale * (tasso_mensile * f) / (f - 1)
        return capitale / mesi
    except (ZeroDivisionError, OverflowError):
        return 0.0

def _medie_storico(self):
    entrate, uscite = {}, {}
    try:
        for dt, voci in list(self.spese.items()):
            k = (dt.year, dt.month)
            for v in list(voci):
                tipo = campo(v, "tipo", "")
                imp = float(campo(v, "importo", 0.0))
                if tipo == "Entrata":
                    entrate[k] = entrate.get(k, 0.0) + imp
                elif tipo == "Uscita":
                    uscite[k] = uscite.get(k, 0.0) + imp
    except Exception:
        pass
    e = sum(entrate.values()) / len(entrate) if entrate else 0.0
    s = sum(uscite.values()) / len(uscite) if uscite else 0.0
    return e, s

MAX_FIN = 30
CAT_EXPORT_FIN = "FinPlan"
MAX_VAR = 200

def _file_fin():
    import __main__ as _app
    return _app.FIN_FILE

def _carica_fin():
    try:
        with open(_file_fin(), "r", encoding="utf-8") as fh:
            dati = json.load(fh)
        lista = dati.get("finanziamenti", []) if isinstance(dati, dict) else []
        return [x for x in lista if isinstance(x, dict)]
    except FileNotFoundError:
        return []
    except Exception:
        try:
            import shutil
            shutil.copy2(_file_fin(), _file_fin() + ".corrotto")
        except Exception:
            pass
        return []

def _salva_fin(lista):
    path = _file_fin()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump({"finanziamenti": lista}, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, path)

def _aggiungi_mesi(d, n):
    m0 = d.month - 1 + n
    a, m = d.year + m0 // 12, m0 % 12 + 1
    return datetime.date(a, m, min(d.day, calendar.monthrange(a, m)[1]))

TIPI_VAR = ("extra", "durata", "prolunga", "tasso", "rata")

def _periodo(f):
    try:
        return 3 if int(f.get("periodo") or 1) == 3 else 1
    except (TypeError, ValueError):
        return 1

def _mesi_residui(debito, tm, rata):
    if debito <= 0.005:
        return 0
    if tm <= 0:
        return int(-(-debito // rata))
    x = 1 - debito * tm / rata
    if x <= 0:
        return 600
    import math
    return max(1, int(math.ceil(-math.log(x) / math.log(1 + tm) - 1e-9)))

def _eventi_validi(f):
    out = []
    for e in f.get("variazioni") or []:
        try:
            out.append({"data": datetime.date.fromisoformat(e["data"]), "tipo": e["tipo"],
                        "valore": float(e["valore"]), "strategia": e.get("strategia") or "ricalcola"})
        except Exception:
            continue
    out.sort(key=lambda x: x["data"])
    return out

def _piano_fin(f, log=None):
    cap = float(f["capitale"])
    p = _periodo(f)
    tm = float(f["tasso"]) / 1200 * p
    mesi = -(-int(f["mesi"]) // p)
    spese = float(f.get("spese") or 0.0) * p
    inizio = datetime.date.fromisoformat(f["data_inizio"])
    rata_fissa = float(f.get("rata") or 0.0)
    custom = rata_fissa > 0
    rata = rata_fissa if custom else _rata_francese(cap, tm, mesi)
    if custom and tm > 0 and rata <= cap * tm + 0.005:
        return [], "La rata è troppo bassa per coprire gli interessi."
    eventi = _eventi_validi(f)
    ei = 0
    vincolo = not custom
    mesi_rim = mesi
    righe, debito, n = [], cap, 0
    while debito > 0.005 and n < 600:
        n += 1
        data = _aggiungi_mesi(inizio, (n - 1) * p)
        extra_n = 0.0
        while ei < len(eventi) and eventi[ei]["data"] <= data:
            e = eventi[ei]
            ei += 1
            t, v = e["tipo"], e["valore"]
            rata_prima, debito_prima = rata, debito
            if not vincolo:
                mesi_rim = _mesi_residui(debito, tm, rata)
            if t == "tasso":
                tm = v / 1200 * p
                if vincolo:
                    rata = _rata_francese(debito, tm, max(mesi_rim, 1))
            elif t == "rata":
                rata, vincolo = v, False
            elif t == "durata":
                mesi_rim = max(1, int(round(v * 12 / p)))
                vincolo = True
                rata = _rata_francese(debito, tm, mesi_rim)
            elif t == "prolunga":
                mesi_rim = max(1, mesi_rim + int(round(v * 12 / p)))
                vincolo = True
                rata = _rata_francese(debito, tm, mesi_rim)
            elif t == "extra":
                ex = min(v, debito)
                debito -= ex
                extra_n += ex
                if e["strategia"] == "ricalcola" and debito > 0.005:
                    vincolo = True
                    rata = _rata_francese(debito, tm, max(mesi_rim, 1))
                else:
                    vincolo = False
            if log is not None:
                log.append({"n": n, "data": e["data"], "tipo": t, "valore": v, "strategia": e["strategia"],
                            "rata_prima": rata_prima, "rata_dopo": rata, "debito_prima": debito_prima,
                            "debito_dopo": debito})
        if debito <= 0.005:
            righe.append({"n": n, "data": data, "rata": extra_n, "rata_base": 0.0, "cap": extra_n,
                          "int": 0.0, "residuo": 0.0, "extra": extra_n, "per": p})
            break
        interessi = debito * tm
        quota = rata - interessi
        if tm > 0 and quota <= 0:
            return righe, "Con queste variazioni la rata non copre gli interessi."
        if quota >= debito or (vincolo and mesi_rim <= 1):
            quota = debito
        debito -= quota
        base = quota + interessi + spese
        righe.append({"n": n, "data": data, "rata": base + extra_n, "rata_base": base, "cap": quota + extra_n,
                      "int": interessi, "residuo": max(debito, 0.0), "extra": extra_n, "per": p})
        mesi_rim -= 1
    if debito > 0.005:
        return righe, "Il finanziamento non si estingue entro 50 anni."
    return righe, None

def _residuo_dopo(righe, cap, idx):
    if idx <= 0:
        return cap
    if idx >= len(righe):
        return 0.0
    return righe[idx - 1]["residuo"]

def _serie(piani, oggi, max_anni=40):
    n_anni = 0
    for righe, k, _ in piani:
        rpa = 12 // (righe[0].get("per", 1) if righe else 1)
        n_anni = max(n_anni, -(-max(len(righe) - k, 0) // rpa))
    n_anni = min(n_anni, max_anni)
    out = []
    for y in range(n_anni + 1):
        residuo = rata = inter = quota = 0.0
        for righe, k, cap in piani:
            rpa = 12 // (righe[0].get("per", 1) if righe else 1)
            residuo += _residuo_dopo(righe, cap, k + rpa * y)
            if y > 0:
                tratto = righe[k + rpa * (y - 1):k + rpa * y]
                rata += sum(r["rata"] for r in tratto)
                inter += sum(r["int"] for r in tratto)
                quota += sum(r["cap"] for r in tratto)
        out.append({"anno": y, "anno_solare": oggi.year + y, "residuo": residuo,
                    "rata": rata, "int": inter, "cap": quota})
    return out

def _data_it(d):
    return d.strftime("%d-%m-%Y")

def _cronostoria(f):
    righe, err = _piano_fin(dict(f, variazioni=[]))
    if err or not righe:
        return []
    out = [{"data": _data_it(datetime.date.fromisoformat(f["data_inizio"])), "titolo": "Inizio",
            "dettaglio": f"{f['capitale']:,.2f} € al {f['tasso']:.2f} % per {int(f['mesi'])} mesi".replace(",", "X").replace(".", ",").replace("X", "."),
            "rata_prima": None, "rata_dopo": righe[0]["rata_base"] / _periodo(f), "debito": float(f["capitale"]),
            "fine": _data_it(righe[-1]["data"]), "int_totali": sum(r["int"] for r in righe)}]
    log = []
    _piano_fin(f, log)
    eventi = _eventi_validi(f)
    for i, e in enumerate(log):
        pre = dict(f, variazioni=[{"data": x["data"].isoformat(), "tipo": x["tipo"], "valore": x["valore"],
                                   "strategia": x["strategia"]} for x in eventi[:i + 1]])
        r_i, e_i = _piano_fin(pre)
        if e_i or not r_i:
            continue
        out.append({"data": _data_it(e["data"]), "tipo": e["tipo"], "valore": e["valore"],
                    "strategia": e["strategia"], "rata_prima": e["rata_prima"] / _periodo(f) + float(f.get("spese") or 0),
                    "rata_dopo": e["rata_dopo"] / _periodo(f) + float(f.get("spese") or 0), "debito": e["debito_dopo"],
                    "debito_prima": e["debito_prima"], "fine": _data_it(r_i[-1]["data"]),
                    "int_totali": sum(r["int"] for r in r_i)})
    return out

def _status_fin(f, oggi):
    righe, err = _piano_fin(f)
    if err:
        return None, err
    cap = float(f["capitale"])
    tot = len(righe)
    k = sum(1 for r in righe if r["data"] <= oggi)
    residuo = _residuo_dopo(righe, cap, k)
    int_pagati = sum(r["int"] for r in righe[:k])
    int_resto = sum(r["int"] for r in righe[k:])
    prossima = righe[k] if k < tot else None
    if k >= tot:
        stato = "estinto"
    elif k == 0:
        stato = "non_iniziato"
    else:
        stato = "in_corso"
    st = {
        "stato": stato, "rate_tot": tot, "rate_pagate": k, "rate_rimaste": tot - k,
        "residuo": residuo, "rimborsato": cap - residuo,
        "pct": (100.0 * (cap - residuo) / cap) if cap > 0 else 0.0,
        "int_pagati": int_pagati, "int_restanti": int_resto, "int_totali": int_pagati + int_resto,
        "rata_mensile": righe[min(k, tot - 1)]["rata_base"] / _periodo(f) if tot else 0.0,
        "rata_periodo": righe[min(k, tot - 1)]["rata_base"] if tot else 0.0,
        "periodo": _periodo(f),
        "prossima_data": _data_it(prossima["data"]) if prossima else "",
        "prossima_importo": prossima["rata"] if prossima else 0.0,
        "giorni_prossima": (prossima["data"] - oggi).days if prossima else None,
        "fine": _data_it(righe[-1]["data"]) if righe else "",
        "costo_totale": sum(r["rata"] for r in righe),
    }
    if f.get("variazioni"):
        base, e2 = _piano_fin(dict(f, variazioni=[]))
        if not e2 and base:
            st["base_fine"] = _data_it(base[-1]["data"])
            st["base_int"] = sum(r["int"] for r in base)
            st["risparmio_int"] = st["base_int"] - st["int_totali"]
            st["mesi_diff"] = (len(base) - tot) * _periodo(f)
    return (st, righe, k), None

def _fin_elenco(self):
    oggi = datetime.date.today()
    out, piani = [], []
    lista_fin = _carica_fin()
    mappa_esp = _fin_mappa_esportate(self)
    tags_esp = set(mappa_esp)
    modificato = False
    for f in lista_fin:
        esp = f.get("esportate")
        if isinstance(esp, dict):
            for n_, id_ in [(a, b) for a, b in esp.items() if b not in tags_esp]:
                del esp[n_]
                modificato = True
        try:
            res, err = _status_fin(f, oggi)
        except Exception:
            res, err = None, "Dati non validi."
        voce = {"id": f.get("id"), "nome": f.get("nome", ""), "capitale": f.get("capitale"),
                "tasso": f.get("tasso"), "mesi": f.get("mesi"), "data_inizio": f.get("data_inizio"),
                "rata_fissa": f.get("rata") or 0, "spese": f.get("spese") or 0, "periodo": _periodo(f),
                "variazioni": f.get("variazioni") or [], "conto": f.get("conto") or ""}
        if err or not res:
            voce["errore"] = err or "Dati non validi."
            out.append(voce)
            continue
        st, righe, k = res
        voce["status"] = st
        voce["proiezione"] = _serie([(righe, k, float(f["capitale"]))], oggi)
        try:
            voce["crono"] = _cronostoria(f)
        except Exception:
            voce["crono"] = []
        esp_n = f.get("esportate") if isinstance(f.get("esportate"), dict) else {}
        da_riall, orfane = _fin_da_riallineare(f, righe, esp_n, mappa_esp)
        voce["orfane"] = orfane
        voce["piano"] = [{"n": r["n"], "data": _data_it(r["data"]), "rata": r["rata"], "cap": r["cap"],
                          "int": r["int"], "residuo": r["residuo"], "extra": r["extra"], "pagata": r["n"] <= k,
                          "esportata": str(r["n"]) in esp_n, "riallinea": r["n"] in da_riall,
                          "cambio": i > 0 and abs(r["rata_base"] - righe[i - 1]["rata_base"]) > 0.005 and i < len(righe) - 1}
                         for i, r in enumerate(righe)]
        out.append(voce)
        if st["stato"] != "estinto":
            piani.append((righe, k, float(f["capitale"])))
    if modificato:
        try:
            _salva_fin(lista_fin)
        except Exception:
            pass
    attivi = [v for v in out if v.get("status") and v["status"]["stato"] != "estinto"]
    serie = _serie(piani, oggi)
    entrate, _ = _medie_storico(self)
    rata_mese = sum(v["status"]["rata_mensile"] for v in attivi)
    tot = {"n_attivi": len(attivi), "n_estinti": sum(1 for v in out if v.get("status") and v["status"]["stato"] == "estinto"),
           "residuo": sum(v["status"]["residuo"] for v in attivi), "rata_mensile": rata_mese,
           "int_restanti": sum(v["status"]["int_restanti"] for v in attivi),
           "entrate_medie": entrate, "pct_entrate": (100.0 * rata_mese / entrate) if entrate > 0 else None,
           "fine_ultimo": max((v["status"]["fine"][-4:] for v in attivi), default="")}
    return {"ok": True, "finanziamenti": out, "totali": tot, "serie": serie}

def _fin_conti():
    try:
        import __main__ as _app
        with open(_app.PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as fh:
            db = json.load(fh)
        return [c.get("nome", "") for c in db.get("conti", []) if c.get("nome")]
    except Exception:
        return []

def _fin_mappa_esportate(self):
    mappa = {}
    try:
        for k, voci in self.spese.items():
            for e in voci:
                for h in (getattr(e, "hashtag", None) or []):
                    if isinstance(h, str) and h.startswith("#finexp:"):
                        mappa[h[8:]] = (k, e)
    except Exception:
        pass
    return mappa

def _fin_tag_esportate(self):
    return set(_fin_mappa_esportate(self))

def _fin_voce_rata(f, r, tot):
    desc = f"{f.get('nome', 'Finanziamento')} - rata {r['n']}/{tot}"
    if r.get("extra", 0) > 0.005:
        desc += " (con estinzione parziale)"
    return desc, round(float(r["rata"]), 2)

def _fin_da_riallineare(f, righe, esp, mappa):
    tot = len(righe)
    per_n = {r["n"]: r for r in righe}
    conto = f.get("conto") or ""
    da, orfane = [], []
    for n_, eid in esp.items():
        if eid not in mappa:
            continue
        try:
            n = int(n_)
        except (TypeError, ValueError):
            continue
        r = per_n.get(n)
        if r is None or r["rata"] <= 0.005:
            orfane.append(n)
            continue
        k, e = mappa[eid]
        desc, imp = _fin_voce_rata(f, r, tot)
        if k != r["data"] or abs(float(e.importo) - imp) > 0.005 or e.descrizione != desc \
                or (e.conto or "") != conto:
            da.append(n)
    return da, orfane

def _fin_esporta(self, d):
    fid = str(d.get("id") or "")
    lista = _carica_fin()
    f = next((x for x in lista if x.get("id") == fid), None)
    if f is None:
        return {"ok": False, "errore": "Finanziamento non trovato."}, 404
    righe, err = _piano_fin(f)
    if err:
        return {"ok": False, "errore": err}, 400
    esp = f.get("esportate")
    if not isinstance(esp, dict):
        esp = f["esportate"] = {}
    tags = _fin_tag_esportate(self)
    for n_ in [a for a, b in esp.items() if b not in tags]:
        del esp[n_]
    voluti = None if d.get("tutte") else set()
    if voluti is not None:
        for x in d.get("numeri") or []:
            try:
                voluti.add(int(x))
            except (TypeError, ValueError):
                continue
    oggi = datetime.date.today()
    da = [r for r in righe
          if (voluti is not None or r["data"] <= oggi) and str(r["n"]) not in esp and r["rata"] > 0.005
          and (voluti is None or r["n"] in voluti)]
    if not da:
        return {"ok": False, "errore": "Nessuna rata da esportare tra quelle scelte "
                                       "(quelle già esportate vengono saltate)."}, 400
    from moduli.modello_spesa import SpesaEntry
    cat = CAT_EXPORT_FIN
    if cat not in self.categorie:
        self.categorie.append(cat)
        self.aggiorna_combobox_categorie()
    tot = len(righe)
    somma = 0.0
    for r in da:
        eid = uuid.uuid4().hex[:7]
        while eid in tags:
            eid = uuid.uuid4().hex[:7]
        tags.add(eid)
        desc, imp = _fin_voce_rata(f, r, tot)
        if r["data"] not in self.spese:
            self.spese[r["data"]] = []
        self.spese[r["data"]].append(SpesaEntry.nuova(
            cat, desc, imp, "Uscita", conto=(f.get("conto") or ""), hashtag=[f"#finexp:{eid}"]))
        esp[str(r["n"])] = eid
        somma += imp
    _salva_fin(lista)
    self.save_db()
    if hasattr(self, "registra_azione_gamification"):
        self.registra_azione_gamification("movimento")
    self.refresh_gui()
    return {"ok": True, "n": len(da), "totale": somma}, 200

def _fin_riallinea(self, d):
    fid = str(d.get("id") or "")
    lista = _carica_fin()
    f = next((x for x in lista if x.get("id") == fid), None)
    if f is None:
        return {"ok": False, "errore": "Finanziamento non trovato."}, 404
    righe, err = _piano_fin(f)
    if err:
        return {"ok": False, "errore": err}, 400
    esp = f.get("esportate") if isinstance(f.get("esportate"), dict) else {}
    mappa = _fin_mappa_esportate(self)
    tot = len(righe)
    per_n = {r["n"]: r for r in righe}
    conto = f.get("conto") or ""
    agg = orfane = 0
    for n_, eid in esp.items():
        if eid not in mappa:
            continue
        try:
            n = int(n_)
        except (TypeError, ValueError):
            continue
        r = per_n.get(n)
        if r is None or r["rata"] <= 0.005:
            orfane += 1
            continue
        k, e = mappa[eid]
        desc, imp = _fin_voce_rata(f, r, tot)
        if k == r["data"] and abs(float(e.importo) - imp) <= 0.005 and e.descrizione == desc \
                and (e.conto or "") == conto:
            continue
        if k != r["data"]:
            voci = self.spese.get(k, [])
            for idx, x in enumerate(voci):
                if x is e:
                    del voci[idx]
                    break
            if r["data"] not in self.spese:
                self.spese[r["data"]] = []
            self.spese[r["data"]].append(e)
        e.importo = imp
        e.descrizione = desc
        e.conto = conto
        agg += 1
    if agg == 0 and orfane == 0:
        return {"ok": False, "errore": "Le rate esportate sono già allineate al piano."}, 400
    if agg:
        self.save_db()
        self.refresh_gui()
    return {"ok": True, "n": agg, "orfane": orfane}, 200

def _fin_elimina_esportate(self, d):
    fid = str(d.get("id") or "")
    lista = _carica_fin()
    f = next((x for x in lista if x.get("id") == fid), None)
    if f is None:
        return {"ok": False, "errore": "Finanziamento non trovato."}, 404
    esp = f.get("esportate") if isinstance(f.get("esportate"), dict) else {}
    numeri = d.get("numeri")
    chiavi = [str(x) for x in numeri if str(x) in esp] if numeri else list(esp.keys())
    if not chiavi:
        return {"ok": False, "errore": "Nessuna rata esportata tra quelle scelte."}, 400
    mappa = _fin_mappa_esportate(self)
    n_spese = 0
    for k_ in chiavi:
        voce = mappa.get(esp[k_])
        if voce:
            data_k, e = voce
            lst = self.spese.get(data_k, [])
            for idx, x in enumerate(lst):
                if x is e:
                    del lst[idx]
                    n_spese += 1
                    break
        del esp[k_]
    f["esportate"] = esp
    _salva_fin(lista)
    self.save_db()
    self.refresh_gui()
    return {"ok": True, "n": len(chiavi), "spese": n_spese}, 200

def _fin_smarca(self, d):
    fid = str(d.get("id") or "")
    lista = _carica_fin()
    f = next((x for x in lista if x.get("id") == fid), None)
    if f is None:
        return {"ok": False, "errore": "Finanziamento non trovato."}, 404
    esp = f.get("esportate") if isinstance(f.get("esportate"), dict) else {}
    numeri = d.get("numeri")
    if numeri:
        chiavi = [str(x) for x in numeri if str(x) in esp]
    else:
        chiavi = list(esp.keys())
    for k in chiavi:
        del esp[k]
    if not chiavi:
        return {"ok": False, "errore": "Nessuna rata esportata tra quelle scelte."}, 400
    f["esportate"] = esp
    _salva_fin(lista)
    return {"ok": True, "n": len(chiavi)}, 200

def _fin_salva(d):
    nome = str(d.get("nome") or "").strip()[:60]
    cap = _num(d.get("capitale"), -1)
    tasso = _num(d.get("tasso"), -1)
    mesi_in = _num(d.get("mesi"), None)
    if mesi_in is None:
        a_in = _num(d.get("anni"), None)
        mesi_in = a_in * 12 if a_in is not None else -1
    rata = _num(d.get("rata"), 0.0)
    spese = _num(d.get("spese"), 0.0)
    data_in = str(d.get("data_inizio") or "").strip()
    try:
        datetime.date.fromisoformat(data_in)
    except ValueError:
        return {"ok": False, "errore": "Data della prima rata non valida."}, 400
    if not nome:
        return {"ok": False, "errore": "Inserisci un nome per il finanziamento."}, 400
    if not 0 < cap <= 2000000 or not 0 <= tasso <= 35 or not 1 <= mesi_in <= 600 or rata < 0 or spese < 0:
        return {"ok": False, "errore": "Controlla i dati: capitale 1–2.000.000 €, tasso 0–35 %, "
                                       "durata da 1 a 600 mesi, rata e spese non negative."}, 400
    conto = str(d.get("conto") or "").strip()
    if "periodo" in d:
        per = 3 if str(d.get("periodo") or "").strip().lower().startswith(("tri", "3")) else 1
    else:
        fid0 = str(d.get("id") or "")
        per = next((_periodo(x) for x in _carica_fin() if fid0 and x.get("id") == fid0), 1)
    f = {"nome": nome, "capitale": cap, "tasso": tasso, "mesi": max(1, int(round(mesi_in))),
         "data_inizio": data_in, "rata": rata, "spese": spese}
    if per == 3:
        f["periodo"] = 3
    if conto and conto != "(nessuno)":
        f["conto"] = conto
    _, err = _piano_fin(f)
    if err:
        return {"ok": False, "errore": err}, 400
    lista = _carica_fin()
    fid = str(d.get("id") or "")
    for i, x in enumerate(lista):
        if fid and x.get("id") == fid:
            f["id"] = fid
            f["variazioni"] = x.get("variazioni") or []
            if x.get("esportate"):
                f["esportate"] = x["esportate"]
            if "conto" not in d and x.get("conto"):
                f["conto"] = x["conto"]
            _, err = _piano_fin(f)
            if err:
                return {"ok": False, "errore": err + " Controlla le variazioni di questo finanziamento."}, 400
            lista[i] = f
            break
    else:
        if len(lista) >= MAX_FIN:
            return {"ok": False, "errore": f"Massimo {MAX_FIN} finanziamenti."}, 400
        f["id"] = uuid.uuid4().hex[:8]
        lista.append(f)
    _salva_fin(lista)
    return {"ok": True, "id": f["id"]}, 200

def _fin_elimina(d):
    fid = str(d.get("id") or "")
    lista = _carica_fin()
    nuova = [x for x in lista if x.get("id") != fid]
    if len(nuova) == len(lista):
        return {"ok": False, "errore": "Finanziamento non trovato."}, 404
    _salva_fin(nuova)
    return {"ok": True}, 200

def _fin_var_aggiungi(d):
    fid = str(d.get("id") or "")
    tipo = d.get("tipo")
    valore = _num(d.get("valore"), None)
    strategia = d.get("strategia") if d.get("strategia") in ("ricalcola", "accorcia") else "ricalcola"
    try:
        data_var = datetime.date.fromisoformat(str(d.get("data") or "")).isoformat()
    except ValueError:
        return {"ok": False, "errore": "Data della variazione non valida."}, 400
    if tipo not in TIPI_VAR:
        return {"ok": False, "errore": "Tipo di variazione sconosciuto."}, 400
    limiti = {"extra": (0.01, 2000000), "durata": (1, 600), "prolunga": (-480, 480), "tasso": (0, 35),
              "rata": (0.01, 100000)}
    lo, hi = limiti[tipo]
    if valore is not None and tipo in ("durata", "prolunga"):
        valore = float(round(valore))
    if valore is None or not lo <= valore <= hi or (tipo == "prolunga" and valore == 0):
        return {"ok": False, "errore": "Valore non valido per questa variazione."}, 400
    if tipo in ("durata", "prolunga"):
        valore = valore / 12

    lista = _carica_fin()
    for x in lista:
        if x.get("id") == fid:
            var = x.setdefault("variazioni", [])
            if len(var) >= MAX_VAR:
                return {"ok": False, "errore": f"Massimo {MAX_VAR} variazioni per finanziamento."}, 400
            var.append({"data": data_var, "tipo": tipo, "valore": valore, "strategia": strategia})
            var.sort(key=lambda z: z["data"])
            _, err = _piano_fin(x)
            if err:
                return {"ok": False, "errore": err}, 400
            _salva_fin(lista)
            return {"ok": True}, 200
    return {"ok": False, "errore": "Finanziamento non trovato."}, 404

def _fin_var_elimina(d):
    fid = str(d.get("id") or "")
    try:
        i = int(d.get("indice"))
    except (TypeError, ValueError):
        return {"ok": False, "errore": "Variazione non valida."}, 400
    lista = _carica_fin()
    for x in lista:
        if x.get("id") == fid:
            var = x.get("variazioni") or []
            if not 0 <= i < len(var):
                return {"ok": False, "errore": "Variazione non trovata."}, 404
            del var[i]
            _, err = _piano_fin(x)
            if err:
                return {"ok": False, "errore": err}, 400
            _salva_fin(lista)
            return {"ok": True}, 200
    return {"ok": False, "errore": "Finanziamento non trovato."}, 404
