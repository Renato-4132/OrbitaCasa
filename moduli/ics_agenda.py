#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import uuid
import math
import calendar
import datetime
import functools

WD = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
GIORNI_BREVI = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"]
FREQ_RIP = {"DAILY": ("Giornaliera", "giorni"), "WEEKLY": ("Settimanale", "settimane"),
            "MONTHLY": ("Mensile", "mesi"), "YEARLY": ("Annuale", "anni")}
CHIAVI_SUPPORTATE = {"FREQ", "INTERVAL", "COUNT", "UNTIL", "BYDAY", "BYMONTHDAY", "BYMONTH", "BYSETPOS", "WKST"}
MAX_LUOGO = 80
_ONE_DAY = datetime.timedelta(days=1)

@functools.lru_cache(maxsize=256)
def parse_rrule(s):
    r = {}
    for parte in (s or "").split(";"):
        if "=" in parte:
            k, val = parte.split("=", 1)
            r[k.strip().upper()] = val.strip().upper()
    out = {"freq": r.get("FREQ", ""), "n": 1, "byday": [], "bymd": [], "bymo": [], "setpos": [], "wkst": 0}
    try:
        out["n"] = max(1, int(r.get("INTERVAL", 1)))
    except ValueError:
        pass
    for x in r.get("BYDAY", "").split(","):
        m = re.fullmatch(r"([+-]?\d{1,2})?(MO|TU|WE|TH|FR|SA|SU)", x.strip())
        if m:
            out["byday"].append((int(m.group(1)) if m.group(1) else 0, WD.index(m.group(2))))
    for chiave, campo in (("BYMONTHDAY", "bymd"), ("BYMONTH", "bymo"), ("BYSETPOS", "setpos")):
        out[campo] = [int(x) for x in r.get(chiave, "").split(",") if re.fullmatch(r"[+-]?\d+", x.strip())]
    if r.get("WKST") in WD:
        out["wkst"] = WD.index(r["WKST"])
    return out

def costruisci_rrule(R):
    p = ["FREQ=" + R["freq"]]
    if R["n"] > 1:
        p.append(f"INTERVAL={R['n']}")
    if R["byday"]:
        p.append("BYDAY=" + ",".join((str(o) if o else "") + WD[wd] for o, wd in R["byday"]))
    if R["bymd"]:
        p.append("BYMONTHDAY=" + ",".join(str(x) for x in R["bymd"]))
    if R["bymo"]:
        p.append("BYMONTH=" + ",".join(str(x) for x in R["bymo"]))
    if R["setpos"]:
        p.append("BYSETPOS=" + ",".join(str(x) for x in R["setpos"]))
    if R["wkst"]:
        p.append("WKST=" + WD[R["wkst"]])
    return ";".join(p)

def rrule_settimanale(n, giorni):
    p = ["FREQ=WEEKLY"]
    if n and n > 1:
        p.append(f"INTERVAL={n}")
    p.append("BYDAY=" + ",".join(WD[i] for i in sorted(set(giorni))))
    return ";".join(p)

def giorni_da_rrule(s):
    if not s:
        return None
    R = parse_rrule(s)
    if R["freq"] != "WEEKLY" or not R["byday"] or any(o for o, _ in R["byday"]) or R["bymd"] or R["bymo"] or R["setpos"]:
        return None
    return sorted({wd for _, wd in R["byday"]})

def _giorni_mese(R, y, m, d0):
    ultimo = calendar.monthrange(y, m)[1]
    giorni = set()
    if R["bymd"]:
        for x in R["bymd"]:
            g = x if x > 0 else ultimo + 1 + x
            if 1 <= g <= ultimo:
                giorni.add(g)
        if R["byday"]:
            wds = {wd for _, wd in R["byday"]}
            giorni = {g for g in giorni if datetime.date(y, m, g).weekday() in wds}
    elif R["byday"]:
        for o, wd in R["byday"]:
            dd = [g for g in range(1, ultimo + 1) if datetime.date(y, m, g).weekday() == wd]
            if o == 0:
                giorni.update(dd)
            elif 0 < o <= len(dd):
                giorni.add(dd[o - 1])
            elif o < 0 and -o <= len(dd):
                giorni.add(dd[o])
    elif d0.day <= ultimo:
        giorni.add(d0.day)
    lista = sorted(giorni)
    if R["setpos"] and lista:
        lista = sorted({lista[p - 1] if p > 0 else lista[p] for p in R["setpos"] if p != 0 and abs(p) <= len(lista)})
    return lista

def _md_ok(R, d):
    if not R["bymd"]:
        return True
    ultimo = calendar.monthrange(d.year, d.month)[1]
    return d.day in {x if x > 0 else ultimo + 1 + x for x in R["bymd"]}

def occorre(rrule, d0, d):
    if d < d0:
        return False
    if d == d0:
        return True
    R = parse_rrule(rrule)
    f, n = R["freq"], R["n"]
    if R["bymo"] and d.month not in R["bymo"] and f != "YEARLY":
        return False
    if f == "DAILY":
        if (d - d0).days % n:
            return False
        if R["byday"] and d.weekday() not in {wd for _, wd in R["byday"]}:
            return False
        return _md_ok(R, d)
    if f == "WEEKLY":
        def inizio(x):
            return x - datetime.timedelta(days=(x.weekday() - R["wkst"]) % 7)
        if ((inizio(d) - inizio(d0)).days // 7) % n:
            return False
        return d.weekday() in ({wd for _, wd in R["byday"]} or {d0.weekday()})
    if f == "MONTHLY":
        if ((d.year - d0.year) * 12 + d.month - d0.month) % n:
            return False
        return d.day in _giorni_mese(R, d.year, d.month, d0)
    if f == "YEARLY":
        if (d.year - d0.year) % n or d.month not in (R["bymo"] or [d0.month]):
            return False
        return d.day in _giorni_mese(R, d.year, d.month, d0)
    return False


def testo_rrule(s):
    R = parse_rrule(s)
    unita = {"DAILY": ("giorno", "giorni"), "WEEKLY": ("settimana", "settimane"),
             "MONTHLY": ("mese", "mesi"), "YEARLY": ("anno", "anni")}.get(R["freq"])
    if not unita:
        return "personalizzata"
    t = f"ogni {unita[0]}" if R["n"] == 1 else f"ogni {R['n']} {unita[1]}"
    det = []
    if R["byday"]:
        parti = []
        for o, wd in R["byday"]:
            nome = GIORNI_BREVI[wd]
            if o == 0:
                parti.append(nome)
            elif o == -1:
                parti.append(f"ultimo {nome}")
            elif o < 0:
                parti.append(f"{-o}° {nome} dalla fine")
            else:
                parti.append(f"{o}° {nome}")
        det.append(", ".join(parti))
    if R["bymd"]:
        det.append("giorno " + ", ".join("ultimo" if x == -1 else str(x) for x in R["bymd"]))
    if R["bymo"]:
        det.append("mesi " + ", ".join(str(x) for x in R["bymo"]))
    return t + (" (" + "; ".join(det) + ")" if det else "")

def _unescape(t):
    out, i = [], 0
    while i < len(t):
        c = t[i]
        if c == "\\" and i + 1 < len(t):
            out.append("\n" if t[i + 1] in "nN" else t[i + 1])
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _dt(valore, params=""):
    valore = valore.strip()
    if "T" not in valore.upper():
        return datetime.datetime.strptime(valore[:8], "%Y%m%d").date()
    dt = datetime.datetime.strptime(valore.rstrip("Zz")[:15], "%Y%m%dT%H%M%S")
    if valore.upper().endswith("Z"):
        dt = dt.replace(tzinfo=datetime.timezone.utc).astimezone().replace(tzinfo=None)
    else:
        m = re.search(r'TZID="?([^;:"]+)', params, re.I)
        if m:
            try:
                from zoneinfo import ZoneInfo
                dt = dt.replace(tzinfo=ZoneInfo(m.group(1))).astimezone().replace(tzinfo=None)
            except Exception:
                pass
    return dt

def _solo_data(x):
    return x.date() if isinstance(x, datetime.datetime) else x

def _durata(s):
    m = re.fullmatch(r"([+-])?P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", s.strip().upper())
    if not m:
        return None
    w, d, h, mi, sec = (int(x or 0) for x in m.groups()[1:])
    td = datetime.timedelta(weeks=w, days=d, hours=h, minutes=mi, seconds=sec)
    return -td if m.group(1) == "-" else td

def _eventi_grezzi(testo):
    righe = []
    for r in testo.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if r[:1] in (" ", "\t") and righe:
            righe[-1] += r[1:]
        else:
            righe.append(r)
    eventi, cur, alarm = [], None, False
    for r in righe:
        u = r.strip().upper()
        if u == "BEGIN:VEVENT":
            cur, alarm = [], False
        elif u == "END:VEVENT":
            if cur is not None:
                eventi.append(cur)
            cur = None
        elif cur is not None:
            if u == "BEGIN:VALARM":
                alarm = True
            elif u == "END:VALARM":
                alarm = False
            elif ":" in r:
                np_, _, val = r.partition(":")
                nome, _, par = np_.partition(";")
                cur.append((nome.strip().upper(), par, val, alarm))
    return eventi

def _parse_importo(s):
    s = (s or "").replace("€", "").strip()
    if not s:
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    return float(s)

def _leggi_evento(ev, max_titolo, max_note, origini):
    p, exd, rdt, trig = {}, [], [], []
    for nome, par, val, alarm in ev:
        if alarm:
            if nome == "TRIGGER":
                trig.append(val.strip().upper())
        elif nome == "EXDATE":
            exd.append((val, par))
        elif nome == "RDATE":
            rdt.append((val, par))
        else:
            p.setdefault(nome, (val, par))
    try:
        ini = _dt(*p["DTSTART"])
    except (KeyError, ValueError):
        return None, "invalidi"
    tutto = not isinstance(ini, datetime.datetime)
    d0 = _solo_data(ini)
    ora = "" if tutto else ini.strftime("%H:%M")

    fine = None
    try:
        if "DTEND" in p:
            fine = _dt(*p["DTEND"])
        elif "DURATION" in p:
            dur = _durata(p["DURATION"][0])
            fine = ini + dur if dur is not None else None
    except ValueError:
        fine = None
    data_fine, ora_fine = "", ""
    if fine is not None:
        if tutto:
            ultimo = _solo_data(fine) - _ONE_DAY
            if ultimo > d0:
                data_fine = ultimo.isoformat()
        else:
            if not isinstance(fine, datetime.datetime):
                fine = datetime.datetime.combine(fine, datetime.time())
            if fine.date() > d0:
                if fine.time() == datetime.time(0, 0):
                    ultimo = fine.date() - _ONE_DAY
                    if ultimo > d0:
                        data_fine = ultimo.isoformat()
                else:
                    data_fine, ora_fine = fine.date().isoformat(), fine.strftime("%H:%M")
            elif fine > ini:
                ora_fine = fine.strftime("%H:%M")

    titolo = _unescape(p.get("SUMMARY", ("", ""))[0]).strip()
    tipo = "Appuntamento"
    if titolo.lower().startswith("scadenza:"):
        tipo, titolo = "Scadenza", titolo[9:].strip()
    titolo = titolo or "(senza titolo)"
    note = _unescape(p.get("DESCRIPTION", ("", ""))[0]).strip()
    if origini and re.match(r"Da (" + "|".join(re.escape(o) for o in origini) + r")(\n|$)", note):
        return None, "da_moduli"
    importo = None
    m = re.search(r"^Importo:\s*([\d.,]+)", note, re.M)
    if m:
        try:
            importo = _parse_importo(m.group(1))
            note = re.sub(r"^Importo:.*\n?", "", note, flags=re.M).strip()
        except ValueError:
            pass
    luogo = re.sub(r"\s*\n\s*", ", ", _unescape(p.get("LOCATION", ("", ""))[0]).strip())[:MAX_LUOGO]
    troncato_t = len(titolo) > max_titolo
    if troncato_t:
        note = titolo + ("\n" + note if note else "")
        titolo = titolo[:max_titolo - 1].rstrip() + "…"
    troncata_n = len(note) > max_note
    note = note[:max_note]

    rip, rn, ru, rr, semplificata, count, until = "Nessuna", None, None, "", False, None, None
    if "RRULE" in p:
        pezzi = dict(x.split("=", 1) for x in p["RRULE"][0].split(";") if "=" in x)
        chiavi = {k.strip().upper() for k in pezzi}
        R = parse_rrule(p["RRULE"][0])
        base = FREQ_RIP.get(R["freq"])
        if not base:
            semplificata = True
        else:
            if chiavi - CHIAVI_SUPPORTATE:
                semplificata = True
            nucleo = chiavi - {"COUNT", "UNTIL", "WKST"}
            semplice = nucleo <= {"FREQ", "INTERVAL"}
            sett = (R["freq"] == "WEEKLY" and nucleo <= {"FREQ", "INTERVAL", "BYDAY"}
                    and all(o == 0 for o, _ in R["byday"]))
            if (semplice or sett) and R["n"] <= 99:
                rip, rn, ru = (base[0], None, None) if R["n"] == 1 else ("Personalizzata", R["n"], base[1])
                if sett and R["byday"] and {wd for _, wd in R["byday"]} != {d0.weekday()}:
                    rr = costruisci_rrule(R)
            else:
                rip, rr = "Avanzata", costruisci_rrule(R)
            try:
                count = int(pezzi["COUNT"]) if "COUNT" in pezzi else None
            except ValueError:
                count = None
            if "UNTIL" in pezzi:
                try:
                    until = _solo_data(_dt(pezzi["UNTIL"]))
                except ValueError:
                    until = None

    def _date_lista(lista):
        res = set()
        for val, par in lista:
            for x in val.split(","):
                try:
                    res.add(_solo_data(_dt(x.split("/")[0], par)))
                except ValueError:
                    pass
        return res

    pre, ant = 0, None
    for t in trig:
        mt = re.fullmatch(r"-P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?)?", t)
        if not mt:
            continue
        w, dd, h, mi = (int(x or 0) for x in mt.groups())
        tot = w * 10080 + dd * 1440 + h * 60 + mi
        if tot == 0:
            continue
        if ora and tot < 1440:
            ant = ant if ant is not None else tot
        else:
            pre = max(pre, math.ceil(tot / 1440))

    rid = None
    if "RECURRENCE-ID" in p:
        try:
            rid = _solo_data(_dt(*p["RECURRENCE-ID"]))
        except ValueError:
            rid = None
    return {
        "uid": p.get("UID", ("", ""))[0].strip(), "rid": rid,
        "stato": p.get("STATUS", ("", ""))[0].strip().upper(),
        "titolo": titolo, "tipo": tipo, "d0": d0, "ora": ora, "data_fine": data_fine, "ora_fine": ora_fine,
        "note": note, "importo": importo, "luogo": luogo,
        "rip": rip, "rip_n": rn, "rip_unita": ru, "rrule": rr, "count": count, "until": until,
        "exd": {d.isoformat() for d in _date_lista(exd)}, "rdate": sorted(_date_lista(rdt)),
        "pre": pre, "ant": ant, "tr_titolo": troncato_t, "tr_note": troncata_n, "semplificata": semplificata,
    }, None

def _vicino(valore, lista):
    return min(lista, key=lambda n: abs(n - valore))

def leggi_ics(testo, agenda=(), max_titolo=35, max_note=150, origini=(),
              preavvisi=(0, 1, 3, 7, 14, 30), anticipi=(5, 15, 30, 60, 120), anticipo_def=15):
    info = {"letti": 0, "invalidi": 0, "annullati": 0, "da_moduli": 0, "doppi": 0, "eccezioni": 0,
            "troncati": 0, "note_troncate": 0, "semplificati": 0}
    letti = []
    for ev in _eventi_grezzi(testo):
        info["letti"] += 1
        e, errore = _leggi_evento(ev, max_titolo, max_note, origini)
        if errore:
            info[errore] += 1
        else:
            letti.append(e)

    master = {e["uid"]: e for e in letti if e["uid"] and e["rid"] is None and e["stato"] != "CANCELLED"}
    validi = []
    for e in letti:
        if e["stato"] == "CANCELLED":
            if e["rid"] and e["uid"] in master:
                master[e["uid"]]["exd"].add(e["rid"].isoformat())
            info["annullati"] += 1
            continue
        if e["rid"] and e["uid"] in master:
            master[e["uid"]]["exd"].add(e["rid"].isoformat())
            info["eccezioni"] += 1
        validi.append(e)
        for rd in e["rdate"]:
            c = dict(e, d0=rd, rrule="", rip="Nessuna", rip_n=None, rip_unita=None, until=None, count=None,
                     exd=set(), rdate=[], uid="", rid=None)
            if e["data_fine"]:
                c["data_fine"] = (rd + (datetime.date.fromisoformat(e["data_fine"]) - e["d0"])).isoformat()
            validi.append(c)

    ids = {v.get("id") for v in agenda}
    chiavi = {((v.get("titolo") or "").lower(), v.get("data"), v.get("ora") or "", v.get("ripetizione", "Nessuna"))
              for v in agenda}
    voci = []
    for e in validi:
        if e["uid"].endswith("@orbitacasa") and e["uid"][:-11] in ids:
            info["doppi"] += 1
            continue
        chiave = (e["titolo"].lower(), e["d0"].isoformat(), e["ora"], e["rip"])
        if chiave in chiavi:
            info["doppi"] += 1
            continue
        chiavi.add(chiave)
        info["troncati"] += e["tr_titolo"]
        info["note_troncate"] += e["tr_note"]
        info["semplificati"] += e["semplificata"]
        v = {"id": uuid.uuid4().hex[:8], "titolo": e["titolo"], "tipo": e["tipo"], "data": e["d0"].isoformat(),
             "ora": e["ora"], "data_fine": e["data_fine"], "ora_fine": e["ora_fine"], "luogo": e["luogo"],
             "importo": e["importo"], "ripetizione": e["rip"], "rrule": e["rrule"],
             "rip_fine": e["until"].isoformat() if e["until"] else "", "escluse": sorted(e["exd"]),
             "note": e["note"], "fatti": [], "preavviso": _vicino(e["pre"], preavvisi),
             "anticipo_min": _vicino(e["ant"] if e["ant"] is not None else anticipo_def, anticipi),
             "email": False, "_count": e["count"]}
        if e["rip"] == "Personalizzata":
            v.update(rip_n=e["rip_n"], rip_unita=e["rip_unita"])
        voci.append(v)
    return voci, info
