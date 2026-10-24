#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import uuid
import shutil
import re
import time
import threading
import calendar
import datetime
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, filedialog

import __main__ as _app

try:
    from moduli import ics_agenda as _ics
except ImportError:
    import ics_agenda as _ics

MESI = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
GIORNI = ["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]
GIORNI_ESTESI = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
TIPI = ["Appuntamento", "Scadenza"]
RIPETIZIONI = ["Nessuna", "Giornaliera", "Settimanale", "Mensile", "Annuale", "Personalizzata"]
UNITA_RIP = ["giorni", "settimane", "mesi", "anni"]
UNITA_SING = {"giorni": "giorno", "settimane": "settimana", "mesi": "mese", "anni": "anno"}
UNITA_ICS = {"giorni": "DAILY", "settimane": "WEEKLY", "mesi": "MONTHLY", "anni": "YEARLY"}
MAX_TITOLO = 35
MAX_IMPORTO = 8
MAX_NOTE = 150
COL_APPUNTAMENTO = "#3b82f6"
COL_SCADENZA = "#e5484d"
COL_FATTO = "#8a8a8a"
COL_ANTICIPO = "#d9822b"
ORIGINI = ["Veicoli", "PetCare", "Documenti personali", "Archivi PDF", "Immobili", "CasaCare", "Spese pianificate", "MyBusiness"]
PREAVVISI = [("Il giorno stesso", 0), ("1 giorno prima", 1), ("3 giorni prima", 3), ("7 giorni prima", 7),
             ("14 giorni prima", 14), ("30 giorni prima", 30)]
ANTICIPI_ORA = [("5 minuti prima", 5), ("15 minuti prima", 15), ("30 minuti prima", 30),
                ("1 ora prima", 60), ("2 ore prima", 120)]
PREAVVISO_ESTERNE = 7
ANTICIPO_ORA_MIN = 15
EMAIL_RETRY_SEC = 30 * 60
EMAIL_REG_GIORNI = 150
_EMAIL_LOCK = threading.Lock()
LIMITE_SCADUTI_GG = 60
LIMITE_RIPETUTE_APPUNTAMENTI_GG = 14
LIMITE_RIPETUTE_SCADENZE_GG = 366

def _carica():
    dati = {"agenda": [], "note": "", "fonti": {}, "digest": {"attivo": False, "ora": "08:00"}}
    errore = None
    path = getattr(_app, "PROMEMORIA_FILE", None)
    if not path or not os.path.exists(path):
        return dati, errore
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            raise ValueError("formato non valido")
    except Exception as e:
        try:
            shutil.copy2(path, path + ".corrotto")
        except Exception:
            pass
        return dati, f"{e} (copia salvata in promemoria.json.corrotto)"
    if isinstance(raw.get("agenda"), list):
        for v in raw["agenda"]:
            if isinstance(v, dict) and v.get("data"):
                try:
                    datetime.date.fromisoformat(v["data"])
                except Exception:
                    continue
                v.setdefault("id", uuid.uuid4().hex[:8])
                v.setdefault("titolo", "")
                v.setdefault("tipo", "Appuntamento")
                v.setdefault("ora", "")
                v.setdefault("importo", None)
                v.setdefault("ripetizione", "Nessuna")
                v.setdefault("note", "")
                v.setdefault("fatti", [])
                for _k in ("ora_fine", "data_fine", "luogo", "rip_fine", "rrule"):
                    if not isinstance(v.get(_k), str):
                        v[_k] = ""
                if not isinstance(v.get("escluse"), list):
                    v["escluse"] = []
                try:
                    v["preavviso"] = max(0, int(v.get("preavviso", 0) or 0))
                except (TypeError, ValueError):
                    v["preavviso"] = 0
                v.setdefault("seq", 0)
                v["email"] = bool(v.get("email", False))
                v["anticipo_min"] = _anticipo_min(v)
                if v.get("ripetizione") == "Personalizzata":
                    n_, u_ = _rip_params(v)
                    v["rip_n"], v["rip_unita"] = n_ or 1, u_ or "mesi"
                dati["agenda"].append(v)
        dati["note"] = raw.get("note", "") or ""
        if isinstance(raw.get("digest"), dict):
            try:
                _ora_dg = _normalizza_ora(raw["digest"].get("ora", "08:00")) or "08:00"
            except ValueError:
                _ora_dg = "08:00"
            dati["digest"] = {"attivo": bool(raw["digest"].get("attivo", False)), "ora": _ora_dg}
        if isinstance(raw.get("fonti"), dict):
            dati["fonti"] = {k: bool(x) for k, x in raw["fonti"].items()}
            if "Documenti" in dati["fonti"]:
                dati["fonti"].setdefault("Documenti personali", dati["fonti"].pop("Documenti"))
    else:
        dati["note"] = raw.get("promemoria", "") or ""
    return dati, errore

def _salva(dati):
    path = getattr(_app, "PROMEMORIA_FILE", None)
    if not path:
        raise RuntimeError("PROMEMORIA_FILE non definito")
    out = {
        "promemoria": _testo_riepilogo(dati),
        "note": dati["note"],
        "agenda": dati["agenda"],
        "fonti": dati.get("fonti", {}),
        "digest": dati.get("digest", {"attivo": False, "ora": "08:00"}),
    }
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=4, ensure_ascii=False)
    os.replace(tmp, path)

def _data(v):
    return datetime.date.fromisoformat(v["data"])

def _rip_params(v):
    try:
        n = int(v.get("rip_n", 1) or 1)
    except (TypeError, ValueError):
        return None, None
    u = v.get("rip_unita", "")
    if n < 1 or n > 99 or u not in UNITA_RIP:
        return None, None
    return n, u

def _rip_testo(v):
    r = v.get("ripetizione", "Nessuna")
    if r == "Avanzata":
        t = _ics.testo_rrule(v.get("rrule", ""))
    elif r == "Personalizzata":
        n, u = _rip_params(v)
        if not n:
            t = "personalizzata"
        else:
            t = f"ogni {UNITA_SING[u]}" if n == 1 else f"ogni {n} {u}"
    else:
        t = r.lower()
    gg = _ics.giorni_da_rrule(v.get("rrule"))
    if gg and r != "Avanzata":
        t += " (" + ", ".join(GIORNI[i].lower() for i in gg) + ")"
    if v.get("rip_fine"):
        try:
            t += " fino al " + _fmt_data(datetime.date.fromisoformat(v["rip_fine"]))
        except ValueError:
            pass
    return t

def _anticipo_min(v):
    try:
        n = int(v.get("anticipo_min", ANTICIPO_ORA_MIN) or ANTICIPO_ORA_MIN)
    except (TypeError, ValueError):
        n = ANTICIPO_ORA_MIN
    return max(1, min(n, 1440))

def _durata_gg(v):
    try:
        if v.get("data_fine"):
            return max(0, min(366, (datetime.date.fromisoformat(v["data_fine"]) - _data(v)).days))
    except Exception:
        pass
    return 0

def _occorre(v, d):
    for k in range(_durata_gg(v) + 1):
        if _occorre_inizio(v, d - datetime.timedelta(days=k)):
            return True
    return False

def _occorre_inizio(v, d):
    try:
        d0 = _data(v)
    except Exception:
        return False
    if d < d0:
        return False
    iso = d.isoformat()
    if (v.get("rip_fine") and iso > v["rip_fine"]) or iso in (v.get("escluse") or ()):
        return False
    if v.get("rrule"):
        return _ics.occorre(v["rrule"], d0, d)
    r = v.get("ripetizione", "Nessuna")
    if r == "Nessuna":
        return d == d0
    if r == "Giornaliera":
        return True
    if r == "Settimanale":
        return (d - d0).days % 7 == 0
    ultimo = calendar.monthrange(d.year, d.month)[1]
    if r == "Personalizzata":
        n, u = _rip_params(v)
        if not n:
            return d == d0
        if u == "giorni":
            return (d - d0).days % n == 0
        if u == "settimane":
            return (d - d0).days % (7 * n) == 0
        if u == "mesi":
            return ((d.year - d0.year) * 12 + d.month - d0.month) % n == 0 and d.day == min(d0.day, ultimo)
        return (d.year - d0.year) % n == 0 and d.month == d0.month and d.day == min(d0.day, ultimo)
    if r == "Mensile":
        return d.day == min(d0.day, ultimo)
    if r == "Annuale":
        return d.month == d0.month and d.day == min(d0.day, ultimo)
    return False

def _chiave_ordine(v):
    return (v.get("ora") or "", (v.get("titolo") or "").lower())

def _occorrenze(agenda, d1, d2):
    res = {}
    giorno = d1
    while giorno <= d2:
        voci = [v for v in agenda if _occorre(v, giorno)]
        if voci:
            res[giorno] = sorted(voci, key=_chiave_ordine)
        giorno += datetime.timedelta(days=1)
    return res

def _fatta(v, d):
    return d.isoformat() in v.get("fatti", [])

def _scaduti(agenda, oggi):
    ieri = oggi - datetime.timedelta(days=1)
    res = []
    for v in agenda:
        try:
            d0 = _data(v)
        except Exception:
            continue
        if v.get("ripetizione", "Nessuna") == "Nessuna":
            df = d0 + datetime.timedelta(days=_durata_gg(v))
            if oggi - datetime.timedelta(days=LIMITE_SCADUTI_GG) <= df <= ieri and not _fatta(v, d0):
                res.append((d0, v))
            continue
        limite = LIMITE_RIPETUTE_SCADENZE_GG if v.get("tipo") == "Scadenza" else LIMITE_RIPETUTE_APPUNTAMENTI_GG
        for k in range(limite + 1):
            d = ieri - datetime.timedelta(days=k)
            if d < d0:
                break
            if _occorre_inizio(v, d):
                if not _fatta(v, d):
                    res.append((d, v))
                break
    return sorted(res, key=lambda t: (t[0], _chiave_ordine(t[1])))

def _anticipi(agenda, oggi):
    res = []
    for v in agenda:
        try:
            pre = int(v.get("preavviso", 0) or 0)
        except (TypeError, ValueError):
            pre = 0
        for k in range(1, pre + 1):
            d = oggi + datetime.timedelta(days=k)
            if _occorre_inizio(v, d) and not _fatta(v, d):
                res.append((d, v))
                break
    return sorted(res, key=lambda t: (t[0], _chiave_ordine(t[1])))

def _tutte(dati):
    return list(dati.get("agenda", [])) + list(dati.get("_ext", []))

def _tocca(v):
    v["seq"] = int(v.get("seq", 0) or 0) + 1
    v["modificata"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def _normalizza_ora(s):
    s = (s or "").strip().replace(".", ":").replace(",", ":").replace(" ", "")
    if not s:
        return ""
    if ":" in s:
        h, _, m = s.partition(":")
        m = m or "00"
    elif s.isdigit():
        if len(s) <= 2:
            h, m = s, "00"
        elif len(s) == 3:
            h, m = s[0], s[1:]
        elif len(s) == 4:
            h, m = s[:2], s[2:]
        else:
            raise ValueError(s)
    else:
        raise ValueError(s)
    if not (h.isdigit() and m.isdigit()):
        raise ValueError(s)
    hh, mm = int(h), int(m)
    if not (0 <= hh <= 23 and 0 <= mm <= 59):
        raise ValueError(s)
    return f"{hh:02d}:{mm:02d}"

def _scadenze_esterne(app=None, fonti=None):
    res = []

    def data_it(s):
        try:
            return datetime.datetime.strptime((s or "").strip(), "%d-%m-%Y").date()
        except ValueError:
            return None

    def aggiungi(origine, apri, chiave, titolo, d, importo=None, ora="", tipo="Scadenza", preavviso=PREAVVISO_ESTERNE):
        res.append({"id": "ext-" + re.sub(r"[^A-Za-z0-9_.-]", "_", str(chiave)), "esterna": True,
                    "origine": origine, "apri": apri, "titolo": titolo, "tipo": tipo,
                    "data": d.isoformat(), "ora": ora, "importo": importo, "ripetizione": "Nessuna",
                    "note": "", "fatti": [], "preavviso": preavviso})

    def leggi(path):
        if not path or not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            return None

    db = leggi(getattr(_app, "VEICOLI_FILE", None))
    for v in (db or {}).get("veicoli", []) if isinstance(db, dict) else []:
        nome = v.get("nome") or v.get("targa") or "Veicolo"
        for etic, k in (("Bollo", "scad_bollo"), ("Assicurazione", "scad_assicurazione"), ("Revisione", "scad_revisione")):
            d = data_it(v.get(k))
            if d:
                aggiungi("Veicoli", "veicoli", f"veic-{v.get('id')}-{k}", f"{nome}: {etic}", d)

    db = leggi(getattr(_app, "ANIMALI_FILE", None))
    for a in (db or {}).get("animali", []) if isinstance(db, dict) else []:
        nome = a.get("nome") or "Animale"
        for etic, k in (("Vaccinazioni", "scad_vaccino"), ("Antiparassitario", "scad_antiparassitario"),
                        ("Assicurazione", "scad_assicurazione"), ("Controllo veterinario", "prossimo_controllo")):
            d = data_it(a.get(k))
            if d:
                aggiungi("PetCare", "animali", f"anim-{a.get('id')}-{k}", f"{nome}: {etic}", d)

    db = leggi(getattr(_app, "IMMOBIL_FILE", None))
    for i in (db or {}).get("immobili", []) if isinstance(db, dict) else []:
        d = data_it(i.get("scadenza_contratto"))
        if d:
            aggiungi("Immobili", "immobil", f"imm-{i.get('id')}", f"{i.get('nome') or 'Immobile'}: scadenza contratto", d)

    db = leggi(getattr(_app, "MANUTENZIONE_CASA_FILE", None))
    for m in (db or {}).get("voci", []) if isinstance(db, dict) else []:
        ult = data_it(m.get("ultima"))
        try:
            freq = int(m.get("freq_giorni") or 0)
        except (TypeError, ValueError):
            freq = 0
        if ult and freq > 0:
            aggiungi("CasaCare", "manutenzione_casa", f"casa-{m.get('id')}", m.get("nome") or "Manutenzione",
                     ult + datetime.timedelta(days=freq))

    base = getattr(_app, "DOC_PERS_DIR", None)
    profili = leggi(os.path.join(base, "profili.json")) if base else None
    for prof in profili if isinstance(profili, list) else []:
        reg = leggi(os.path.join(base, str(prof), "registry.json"))
        if not isinstance(reg, dict):
            continue
        for fname, rec in reg.items():
            if not isinstance(rec, dict):
                continue
            d = data_it(rec.get("data_scadenza"))
            if d:
                desc = rec.get("descrizione") or rec.get("categoria") or fname
                aggiungi("Documenti personali", "gestisci_documenti_personali", f"doc-{prof}-{fname}", f"{prof}: {desc}", d)

    reg = leggi(getattr(_app, "REGISTRY_FILE", None))
    oggi_ = datetime.date.today()
    for fname, rec in (reg.items() if isinstance(reg, dict) else []):
        if not isinstance(rec, dict) or rec.get("tipo_esatto") == "Entrata":
            continue
        desc = rec.get("descrizione_esatta") or ""
        m = re.search(r"SCD:\s*(\d{2})[/-](\d{2})[/-](\d{4})", desc, re.I)
        m2 = None if m else re.search(r"SCD:\s*(\d{4})[/-](\d{2})[/-](\d{2})", desc, re.I)
        try:
            if m:
                d = datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            elif m2:
                d = datetime.date(int(m2.group(1)), int(m2.group(2)), int(m2.group(3)))
            else:
                continue
        except ValueError:
            continue
        if d < oggi_:
            continue
        titolo = re.sub(r"\s*SCD:\s*\S+", "", desc).strip() or fname
        try:
            imp = int(rec.get("importo_raw")) / 100.0
        except (TypeError, ValueError):
            imp = None
        aggiungi("Archivi PDF", "gestisci_archivi_pdf", f"pdf-{fname}", titolo, d, imp)

    lista = leggi(getattr(_app, "STUDIO_APPUNTAMENTI", None))
    for a in lista if isinstance(lista, list) else []:
        if not isinstance(a, dict) or a.get("stato") == "Annullato":
            continue
        try:
            d = datetime.date.fromisoformat(str(a.get("data") or ""))
        except ValueError:
            continue
        if d < oggi_:
            continue
        try:
            ora = _normalizza_ora(a.get("ora"))
        except ValueError:
            ora = ""
        cli, pre = (a.get("cliente_nome") or "").strip(), (a.get("prestazione") or "").strip()
        fiscale = cli == "Scadenza Fiscale"
        titolo = pre if fiscale else ": ".join(x for x in (cli, pre) if x) or "Appuntamento"
        aggiungi("MyBusiness", "apri_studio", f"studio-{a.get('id')}", titolo, d, ora=ora,
                 tipo="Scadenza" if fiscale else "Appuntamento",
                 preavviso=PREAVVISO_ESTERNE if fiscale else 0)

    for p in ((getattr(app, "pianificate", None) or {}).get("piani", []) if app is not None else []):
        try:
            d = datetime.date.fromisoformat(p["data_scadenza"])
        except Exception:
            continue
        aggiungi("Spese pianificate", "apri_gestione_spese_pianificate", f"sp-{p.get('id')}",
                 f"{p.get('nome') or 'Spesa'} (pianificata)", d, p.get("importo_totale"))
    fonti = fonti or {}
    return [r for r in res if fonti.get(r["origine"], False)]

def _fmt_data(d):
    return d.strftime("%d-%m-%Y")

def _testo_fine(v):
    df, of = v.get("data_fine"), v.get("ora_fine")
    try:
        if df:
            return f"fino al {_fmt_data(datetime.date.fromisoformat(df))}" + (f" {of}" if of else "")
    except ValueError:
        pass
    return f"fino alle {of}" if of else ""

def _fmt_eur(x):
    try:
        return f"{float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " €"
    except (TypeError, ValueError):
        return ""

def _parse_importo(s):
    s = (s or "").replace("€", "").strip()
    if not s:
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    return float(s)

def _riga_voce(d, v, con_ora=True):
    parti = [_fmt_data(d)]
    if con_ora and v.get("ora"):
        parti.append(v["ora"])
    parti.append(f"[{v.get('tipo', '')}]")
    parti.append(v.get("titolo", ""))
    riga = " ".join(parti)
    if v.get("importo") not in (None, ""):
        riga += f" ({_fmt_eur(v['importo'])})"
    if v.get("ripetizione", "Nessuna") != "Nessuna":
        riga += f" - ripete: {_rip_testo(v)}"
    if _testo_fine(v):
        riga += f" ({_testo_fine(v)})"
    if v.get("luogo"):
        riga += f" @ {v['luogo']}"
    if v.get("esterna"):
        riga += f" - da {v.get('origine', '')}"
    if v.get("note"):
        riga += f" - {v['note'].strip().splitlines()[0]}"
    return riga

def _testo_agenda(dati, giorni, oggi=None, con_esterne=False):
    oggi = oggi or datetime.date.today()
    agenda = _tutte(dati) if con_esterne else dati["agenda"]
    righe = []
    ritardo = _scaduti(agenda, oggi)
    if ritardo:
        righe.append("SCADUTI / NON COMPLETATI:")
        righe += ["  " + _riga_voce(d, v) for d, v in ritardo]
        righe.append("")
    prossimi = _occorrenze(agenda, oggi, oggi + datetime.timedelta(days=giorni))
    righe.append(f"PROSSIMI {giorni} GIORNI:")
    n = 0
    for d in sorted(prossimi):
        for v in prossimi[d]:
            if _fatta(v, d):
                continue
            righe.append("  " + _riga_voce(d, v))
            n += 1
    if n == 0:
        righe.append("  (nessuna voce)")
    return "\n".join(righe)

def _testo_riepilogo(dati):
    blocchi = []
    if (dati.get("note") or "").strip():
        blocchi.append(dati["note"].strip())
    if dati.get("agenda"):
        blocchi.append("AGENDA (appuntamenti e scadenze):\n" + _testo_agenda(dati, 30))
    return "\n\n".join(blocchi)

INTERVALLO_AVVISI_MS = 30 * 60 * 1000
INTERVALLO_ORARI_MS = 60 * 1000

def conteggio_avvisi(app=None):
    dati, _ = _carica()
    try:
        dati["_ext"] = _scadenze_esterne(app, dati.get("fonti"))
    except Exception:
        dati["_ext"] = []
    agenda = _tutte(dati)
    oggi = datetime.date.today()
    n_oggi = sum(1 for v in agenda if _occorre(v, oggi) and not _fatta(v, oggi))
    return n_oggi, len(_scaduti(agenda, oggi)), len(_anticipi(agenda, oggi))

def _aggiorna_badge_agenda(self, n):
    try:
        self._agenda_novita_pendenti = n
        from moduli.messaggi_servizio import _aggiorna_badge_messaggi_servizio
        _aggiorna_badge_messaggi_servizio(self)
    except Exception:
        pass

def _segna_agenda_vista(self):
    try:
        self._agenda_ack = (datetime.date.today(), sum(conteggio_avvisi(self)))
    except Exception:
        pass
    _aggiorna_badge_agenda(self, 0)

def _email_configurata():
    return bool(getattr(_app, "EMAIL_USER", "") and getattr(_app, "APP_PASSWORD", ""))

def _email_reg_path():
    path = getattr(_app, "PROMEMORIA_FILE", None)
    return (os.path.splitext(path)[0] + "_email.json") if path else None

def _carica_email_reg():
    path = _email_reg_path()
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return raw if isinstance(raw, dict) else {}
    except Exception:
        return {}

def _salva_email_reg(reg):
    path = _email_reg_path()
    if not path:
        return
    limite = (datetime.date.today() - datetime.timedelta(days=EMAIL_REG_GIORNI)).isoformat()
    reg = {k: x for k, x in reg.items() if len(k.split("|")) < 2 or k.split("|")[1] >= limite}
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(reg, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception:
        pass

def _corpo_email_voce(v, d, quando):
    righe = [f"PROMEMORIA {_app.NAME.upper()}", "─" * 31, f"📌 {v.get('titolo', '')}",
             f"Quando: {_fmt_data(d)}" + (f" {v['ora']}" if v.get("ora") else "") + f" ({quando})",
             f"Tipo: {v.get('tipo', '')}"]
    if _testo_fine(v):
        righe.append("Durata: " + _testo_fine(v))
    if v.get("luogo"):
        righe.append(f"Luogo: {v['luogo']}")
    if v.get("importo") not in (None, ""):
        righe.append(f"Importo: {_fmt_eur(v['importo'])}")
    if v.get("ripetizione", "Nessuna") != "Nessuna":
        righe.append(f"Ripete: {_rip_testo(v)}")
    if v.get("note"):
        righe += ["", v["note"].strip()]
    return "\n".join(righe)

def _invia_email_thread(self, chiave, nome, corpo):
    inflight = getattr(self, "_agenda_email_inflight", None)
    if inflight is None:
        inflight = self._agenda_email_inflight = set()
    if getattr(self, "_agenda_email_esiti", None) is None:
        self._agenda_email_esiti = []
    if getattr(self, "_agenda_email_falliti", None) is None:
        self._agenda_email_falliti = {}
    inflight.add(chiave)
    dest = _app.EMAIL_USER

    def lavoro():
        try:
            ok, errore = self._invia_email_scheduler(nome, corpo, dest)
        except Exception as e:
            ok, errore = False, str(e)
        with _EMAIL_LOCK:
            if ok:
                reg = _carica_email_reg()
                reg[chiave] = datetime.datetime.now().isoformat(timespec="seconds")
                _salva_email_reg(reg)
            else:
                self._agenda_email_falliti[chiave] = time.time()
        inflight.discard(chiave)
        self._agenda_email_esiti.append((ok, nome))
    threading.Thread(target=lavoro, daemon=True).start()

def _controlla_email(self, dati, adesso):
    esiti = getattr(self, "_agenda_email_esiti", None)
    while esiti:
        ok, nome = esiti.pop(0)
        try:
            self.show_toast(f"✉ Promemoria inviato: {nome}" if ok else f"✉ Invio email fallito: {nome}", duration=3500)
        except Exception:
            pass
    if not _email_configurata():
        return
    oggi = adesso.date()
    reg = _carica_email_reg()
    inflight = getattr(self, "_agenda_email_inflight", None) or set()
    falliti = getattr(self, "_agenda_email_falliti", None) or {}
    coda = []
    for v in dati["agenda"]:
        if not v.get("email"):
            continue
        ora = (v.get("ora") or "").strip()
        h = None
        if ora:
            try:
                h = datetime.datetime.strptime(ora, "%H:%M").time()
            except ValueError:
                h = None
        if _occorre_inizio(v, oggi) and not _fatta(v, oggi):
            if h:
                minuti = (datetime.datetime.combine(oggi, h) - adesso).total_seconds() / 60.0
                if -5 <= minuti <= _anticipo_min(v):
                    quando = f"tra {max(1, int(minuti + 0.999))} minuti" if minuti >= 1 else "adesso"
                    coda.append((f"{v['id']}|{oggi.isoformat()}|ora@{ora}", f"Promemoria: {v.get('titolo', '')}",
                                 _corpo_email_voce(v, oggi, quando)))
            else:
                coda.append((f"{v['id']}|{oggi.isoformat()}|oggi", f"Promemoria oggi: {v.get('titolo', '')}",
                             _corpo_email_voce(v, oggi, "oggi")))
        try:
            pre = int(v.get("preavviso", 0) or 0)
        except (TypeError, ValueError):
            pre = 0
        for k in range(1, pre + 1):
            d = oggi + datetime.timedelta(days=k)
            if _occorre_inizio(v, d) and not _fatta(v, d):
                coda.append((f"{v['id']}|{d.isoformat()}|pre", f"In arrivo: {v.get('titolo', '')}",
                             _corpo_email_voce(v, d, f"tra {k} giorn{'o' if k == 1 else 'i'}")))
                break
    dg = dati.get("digest", {})
    if dg.get("attivo"):
        try:
            h_dg = datetime.datetime.strptime(dg.get("ora", "08:00"), "%H:%M").time()
        except ValueError:
            h_dg = datetime.time(8, 0)
        k_dg = f"digest|{oggi.isoformat()}|d"
        if adesso.time() >= h_dg and k_dg not in reg:
            try:
                ext = _scadenze_esterne(self, dati.get("fonti"))
            except Exception:
                ext = []
            testo = _testo_agenda({"agenda": dati["agenda"], "_ext": ext}, 7, oggi, con_esterne=True)
            if "(nessuna voce)" in testo and "SCADUTI" not in testo:
                with _EMAIL_LOCK:
                    reg = _carica_email_reg()
                    reg[k_dg] = adesso.isoformat(timespec="seconds")
                    _salva_email_reg(reg)
            else:
                coda.append((k_dg, f"Agenda del {_fmt_data(oggi)}",
                             f"AGENDA {_app.NAME.upper()} - {_fmt_data(oggi)}\n{'─' * 31}\n{testo}"))
    for chiave, nome, corpo in coda:
        if chiave in reg or chiave in inflight:
            continue
        if time.time() - falliti.get(chiave, 0) < EMAIL_RETRY_SEC:
            continue
        _invia_email_thread(self, chiave, nome, corpo)

def _controlla_orari(self):
    adesso = datetime.datetime.now()
    oggi = adesso.date()
    ultimo = getattr(self, "_agenda_giorno", None)
    self._agenda_giorno = oggi
    if ultimo is not None and ultimo != oggi:
        avvisi_agenda(self)
    dati, _ = _carica()
    try:
        _controlla_email(self, dati, adesso)
    except Exception:
        pass
    voci = list(dati["agenda"])
    if dati.get("fonti", {}).get("MyBusiness"):
        try:
            voci += [e for e in _scadenze_esterne(self, {"MyBusiness": True}) if e.get("ora")]
        except Exception:
            pass
    avvisati = getattr(self, "_agenda_orari_avvisati", None)
    if avvisati is None:
        avvisati = self._agenda_orari_avvisati = set()
    avvisati.intersection_update({k for k in avvisati if k[1] == oggi.isoformat()})
    for v in voci:
        ora = (v.get("ora") or "").strip()
        if not ora or not _occorre_inizio(v, oggi) or _fatta(v, oggi):
            continue
        try:
            h = datetime.datetime.strptime(ora, "%H:%M").time()
        except ValueError:
            continue
        minuti = (datetime.datetime.combine(oggi, h) - adesso).total_seconds() / 60.0
        if minuti > _anticipo_min(v) or minuti < -5:
            continue
        chiave = (v["id"], oggi.isoformat())
        if chiave in avvisati:
            continue
        avvisati.add(chiave)
        quando = f"tra {max(1, int(minuti + 0.999))} minuti" if minuti >= 1 else "adesso"
        testo = f"🔔 {ora}  {v.get('titolo', '')}\n{quando}\n\nClicca qui per aprire l'agenda"
        try:
            from moduli.messaggi_servizio import mostra_toast_cliccabile
            mostra_toast_cliccabile(self, testo, self.gestisci_promemoria, 12000)
        except Exception:
            self.show_toast(testo, duration=8000)

def _ciclo_orari(self):
    try:
        self._agenda_orari_job = self.after(INTERVALLO_ORARI_MS, lambda: _ciclo_orari(self))
    except Exception:
        return
    try:
        _controlla_orari(self)
    except Exception:
        pass

def avvisi_agenda(self):
    try:
        job = getattr(self, "_agenda_avvisi_job", None)
        if job:
            self.after_cancel(job)
        self._agenda_avvisi_job = self.after(INTERVALLO_AVVISI_MS, lambda: avvisi_agenda(self))
        if not getattr(self, "_agenda_orari_job", None):
            _ciclo_orari(self)
    except Exception:
        return
    popup = getattr(self, "_promemoria_popup", None)
    try:
        if popup is not None and popup.winfo_exists():
            return
    except Exception:
        pass
    oggi = datetime.date.today()
    self._agenda_giorno = oggi
    n_oggi, n_scad, n_ant = conteggio_avvisi(self)
    tot = n_oggi + n_scad + n_ant
    ack = getattr(self, "_agenda_ack", None)
    if ack and ack[0] == oggi and tot <= ack[1]:
        tot = 0
    _aggiorna_badge_agenda(self, tot)
    if not tot:
        return
    notif = getattr(self, "_agenda_notificate", None)
    if notif and notif[0] == oggi and tot <= notif[1]:
        return
    self._agenda_notificate = (oggi, tot)
    parti = []
    if n_oggi:
        parti.append(f"{n_oggi} in agenda oggi")
    if n_scad:
        parti.append(f"{n_scad} scadut{'a' if n_scad == 1 else 'e'}")
    if n_ant:
        parti.append(f"{n_ant} in arrivo (preavviso)")
    testo = "Promemoria: " + ", ".join(parti) + "\n\nClicca qui (o sull'icona lampeggiante in alto a sinistra) per aprire"
    try:
        from moduli.messaggi_servizio import mostra_toast_cliccabile
        mostra_toast_cliccabile(self, testo, self.gestisci_promemoria, 8000)
    except Exception:
        self.show_toast(testo, duration=6000)

def _ics_testo(t):
    return (str(t).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
            .replace("\r\n", "\n").replace("\n", "\\n"))

def _ics_riga(riga):
    out, cur, n = [], "", 0
    for ch in riga:
        b = len(ch.encode("utf-8"))
        if n + b > 75:
            out.append(cur)
            cur, n = " " + ch, 1 + b
        else:
            cur += ch
            n += b
    out.append(cur)
    return "\r\n".join(out)

def _genera_ics(dati, includi_fatte=False, esterne=None):
    adesso = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    righe = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:-//{_app.NAME}//Agenda//IT",
             "CALSCALE:GREGORIAN", "METHOD:PUBLISH"]
    n = 0
    for v in list(dati["agenda"]) + list(esterne or []):
        try:
            d0 = _data(v)
        except Exception:
            continue
        rip = v.get("ripetizione", "Nessuna")
        fatti = [x for x in v.get("fatti", []) if x]
        if rip == "Nessuna" and fatti and not includi_fatte:
            continue
        uid = re.sub(r"[^A-Za-z0-9_.-]", "_", str(v["id"]))
        ev = ["BEGIN:VEVENT", f"UID:{uid}@orbitacasa", f"DTSTAMP:{adesso}",
              f"SEQUENCE:{int(v.get('seq', 0) or 0)}", f"LAST-MODIFIED:{v.get('modificata') or adesso}"]
        ora = (v.get("ora") or "").strip()
        h = None
        if ora:
            try:
                h = datetime.datetime.strptime(ora, "%H:%M").time()
            except ValueError:
                ora = ""
        d_fine = d0 + datetime.timedelta(days=_durata_gg(v))
        un_giorno = datetime.timedelta(days=1)
        if h:
            ini = datetime.datetime.combine(d0, h)
            fine = None
            of = (v.get("ora_fine") or "").strip()
            if of:
                try:
                    fine = datetime.datetime.combine(d_fine, datetime.datetime.strptime(of, "%H:%M").time())
                except ValueError:
                    fine = None
            if fine is None:
                fine = (datetime.datetime.combine(d_fine + un_giorno, datetime.time())
                        if d_fine > d0 else ini + datetime.timedelta(hours=1))
            if fine <= ini:
                fine = ini + datetime.timedelta(hours=1)
            ev.append("DTSTART:" + ini.strftime("%Y%m%dT%H%M%S"))
            ev.append("DTEND:" + fine.strftime("%Y%m%dT%H%M%S"))
        else:
            ev.append("DTSTART;VALUE=DATE:" + d0.strftime("%Y%m%d"))
            ev.append("DTEND;VALUE=DATE:" + (d_fine + un_giorno).strftime("%Y%m%d"))
        prefisso = "Scadenza: " if v.get("tipo") == "Scadenza" else ""
        ev.append("SUMMARY:" + _ics_testo(prefisso + v.get("titolo", "")))
        if v.get("luogo"):
            ev.append("LOCATION:" + _ics_testo(v["luogo"]))
        desc = []
        if v.get("esterna"):
            desc.append("Da " + v.get("origine", _app.NAME))
        if v.get("importo") not in (None, ""):
            desc.append("Importo: " + _fmt_eur(v["importo"]))
        if v.get("note"):
            desc.append(v["note"].strip())
        if desc:
            ev.append("DESCRIPTION:" + _ics_testo("\n".join(desc)))
        regola = v.get("rrule") or ""
        if not regola:
            if rip == "Personalizzata":
                n_, u_ = _rip_params(v)
                freq = UNITA_ICS.get(u_) if n_ else None
                intervallo = n_ if n_ and n_ > 1 else None
            else:
                freq = {"Giornaliera": "DAILY", "Settimanale": "WEEKLY", "Mensile": "MONTHLY", "Annuale": "YEARLY"}.get(rip)
                intervallo = None
            if freq:
                regola = f"FREQ={freq}" + (f";INTERVAL={intervallo}" if intervallo else "")
        if regola:
            if v.get("rip_fine"):
                try:
                    u = datetime.date.fromisoformat(v["rip_fine"])
                    regola += ";UNTIL=" + u.strftime("%Y%m%d") + ("T235959" if h else "")
                except ValueError:
                    pass
            ev.append("RRULE:" + regola)
            esclusi = set(v.get("escluse") or [])
            if fatti and not includi_fatte:
                esclusi.update(fatti)
            for x in sorted(esclusi):
                try:
                    dx = datetime.date.fromisoformat(x)
                except ValueError:
                    continue
                if h:
                    ev.append("EXDATE:" + datetime.datetime.combine(dx, h).strftime("%Y%m%dT%H%M%S"))
                else:
                    ev.append("EXDATE;VALUE=DATE:" + dx.strftime("%Y%m%d"))
        try:
            pre = int(v.get("preavviso", 0) or 0)
        except (TypeError, ValueError):
            pre = 0
        trigger = ([f"-P{pre}D"] if pre > 0 else []) + ([f"-PT{_anticipo_min(v)}M"] if ora else [])
        for trig in trigger:
            ev += ["BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:" + _ics_testo(v.get("titolo", "") or "Promemoria"),
                   f"TRIGGER:{trig}", "END:VALARM"]
        ev.append("END:VEVENT")
        righe += ev
        n += 1
    righe.append("END:VCALENDAR")
    return "\r\n".join(_ics_riga(r) for r in righe) + "\r\n", n

def _segna_passata(v, oggi):
    try:
        d0 = _data(v)
    except Exception:
        return
    if v.get("ripetizione", "Nessuna") == "Nessuna":
        if (v.get("data_fine") or v["data"]) < oggi.isoformat():
            v["fatti"] = [v["data"]]
        return
    if d0 >= oggi:
        return
    lim = LIMITE_RIPETUTE_SCADENZE_GG if v.get("tipo") == "Scadenza" else LIMITE_RIPETUTE_APPUNTAMENTI_GG
    for k in range(1, lim + 1):
        d = oggi - datetime.timedelta(days=k)
        if d < d0:
            break
        if _occorre_inizio(v, d):
            v["fatti"] = [d.isoformat()]
            break

def _prepara_import(voci, oggi):
    nuove, passate = [], []
    for v in voci:
        n = v.pop("_count", None)
        try:
            d0 = _data(v)
        except Exception:
            continue
        ripete = v.get("ripetizione", "Nessuna") != "Nessuna"
        if n and ripete:
            prova = dict(v, rip_fine="", escluse=[])
            g, trovate = d0, 0
            for _ in range(366 * 60):
                if _occorre_inizio(prova, g):
                    trovate += 1
                    if trovate >= n:
                        v["rip_fine"] = g.isoformat()
                        break
                g += datetime.timedelta(days=1)
        fine = v.get("rip_fine") if ripete else (v.get("data_fine") or v["data"])
        conclusa = bool(fine) and fine < oggi.isoformat()
        _segna_passata(v, oggi)
        _tocca(v)
        (passate if conclusa else nuove).append(v)
    return nuove, passate

def gestisci_promemoria(self):
    if hasattr(self, '_promemoria_popup') and self._promemoria_popup and self._promemoria_popup.winfo_exists():
        self._promemoria_popup.lift()
        return
    if hasattr(self, 'popup_calendario') and self.popup_calendario and self.popup_calendario.winfo_exists():
        self.popup_calendario.destroy()
        self.popup_calendario = None

    BG = getattr(self, "COLOR_WIDGET_BG", "white")
    FG = getattr(self, "TEXT_COLOR", "black")
    HL = getattr(self, "COLOR_HIGHLIGHT", "#007ACC")
    BG_MAIN = getattr(self, "COLOR_BACKGROUND", BG)
    ROSSO = getattr(self, "COLOR_RED", COL_SCADENZA)
    GRIGLIA = "#CCCCCC" if str(BG_MAIN).upper() == "#FFFFFF" else "#444444"

    def _lbl(parent, testo, comando, icona=None):
        lb = ttk.Label(parent, text=testo, compound="left", cursor="hand2", background=BG,
                       foreground=FG, font=("Arial", 9, "bold"), padding=(8, 4), anchor="center")
        img = self.icone_gui.get(icona) if (icona and hasattr(self, "icone_gui")) else None
        if img and not isinstance(img, str):
            lb.config(image=img, text=(" " + testo) if testo else "")
            lb.image = img
        lb.bind("<Button-1>", lambda e: comando())
        return lb

    dati, errore = _carica()
    if errore:
        if not self.show_custom_askyesno(
                "Agenda illeggibile",
                f"Il file promemoria.json non si legge: {errore}\n\n"
                "Vuoi ripartire da un'agenda vuota? Il file attuale verrà sostituito al prossimo salvataggio "
                "(la copia .corrotto resta).\n\nSe rispondi No il file non viene toccato e l'agenda non si apre."):
            return

    def ricarica_esterne():
        try:
            dati["_ext"] = _scadenze_esterne(self, dati.get("fonti"))
        except Exception:
            dati["_ext"] = []
    ricarica_esterne()
    oggi = datetime.date.today()
    stato = {"anno": oggi.year, "mese": oggi.month, "sel": oggi, "after_note": None}

    popup = tk.Toplevel(self)
    self._promemoria_popup = popup
    popup.title("Promemoria · Agenda")
    popup.configure(bg=getattr(self, "COLOR_TOPLEVEL", BG_MAIN))
    popup.withdraw()
    popup.transient(self)
    popup.resizable(True, True)

    def salva():
        try:
            _salva(dati)
        except Exception as e:
            self.show_custom_warning("Errore", f"Impossibile salvare il file: {e}")

    def chiudi():
        tip_nascondi()
        if stato["after_note"]:
            try:
                popup.after_cancel(stato["after_note"])
            except Exception:
                pass
            stato["after_note"] = None
        try:
            dati["note"] = txt_note.get("1.0", "end-1c").strip()
        except Exception:
            pass
        salva()
        popup.destroy()
        self._promemoria_popup = None
        _segna_agenda_vista(self)

    popup.protocol("WM_DELETE_WINDOW", chiudi)

    def voce_per_id(vid):
        return next((v for v in dati["agenda"] if v["id"] == vid), None)

    nb = ttk.Notebook(popup)
    nb.pack(fill="both", expand=True, padx=8, pady=(8, 0))
    tab_agenda = ttk.Frame(nb, padding=6)
    tab_note = ttk.Frame(nb, padding=6)
    nb.add(tab_agenda, text=" Agenda ")
    nb.add(tab_note, text=" Note ")

    tab_agenda.columnconfigure(0, weight=3, uniform="col")
    tab_agenda.columnconfigure(1, weight=2, uniform="col")
    tab_agenda.rowconfigure(0, weight=1)

    sx = ttk.Frame(tab_agenda)
    sx.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
    sx.rowconfigure(1, weight=1)
    sx.columnconfigure(0, weight=1)

    barra = ttk.Frame(sx)
    barra.grid(row=0, column=0, sticky="ew", pady=(0, 4))
    lbl_mese = ttk.Label(barra, font=("Arial", 13, "bold"), anchor="center")

    def cambia_mese(delta):
        m = stato["mese"] - 1 + delta
        stato["anno"] += m // 12
        stato["mese"] = m % 12 + 1
        ridisegna()

    def vai_oggi():
        t = datetime.date.today()
        stato["anno"], stato["mese"], stato["sel"] = t.year, t.month, t
        ricarica_esterne()
        ridisegna()
        aggiorna_pannelli()

    _lbl(barra, "◀", lambda: cambia_mese(-1)).pack(side="left")
    lbl_mese.pack(side="left", fill="x", expand=True)
    _lbl(barra, "▶", lambda: cambia_mese(1)).pack(side="left")
    _lbl(barra, "Oggi", vai_oggi).pack(side="left", padx=(6, 0))

    COL_CORNICE = "#8a8a8a"
    cornice = tk.Frame(sx, bg=COL_CORNICE, padx=2, pady=2)
    cornice.grid(row=1, column=0, sticky="nsew")
    cv = tk.Canvas(cornice, bg=BG, highlightthickness=0, bd=0, cursor="hand2")
    cv.pack(fill="both", expand=True)

    leg = ttk.Frame(sx)
    leg.grid(row=2, column=0, sticky="w", pady=(4, 0))
    for testo, col in (("● Appuntamento", COL_APPUNTAMENTO), ("● Scadenza", COL_SCADENZA), ("● Fatto", COL_FATTO)):
        ttk.Label(leg, text=testo, foreground=col, font=("Arial", 9, "bold")).pack(side="left", padx=(0, 12))

    geom = {"x0": 0, "y0": 0, "cw": 1, "ch": 1, "settimane": []}

    def colore_voce(v, d):
        if _fatta(v, d):
            return COL_FATTO
        return COL_SCADENZA if v.get("tipo") == "Scadenza" else COL_APPUNTAMENTO

    def ridisegna(_e=None):
        cv.delete("all")
        w, h = max(cv.winfo_width(), 200), max(cv.winfo_height(), 150)
        anno, mese = stato["anno"], stato["mese"]
        lbl_mese.config(text=f"{MESI[mese - 1]} {anno}")
        settimane = calendar.Calendar(0).monthdatescalendar(anno, mese)
        geom["settimane"] = settimane
        testa = 22
        cw = w / 7.0
        ch = (h - testa) / len(settimane)
        geom.update(cw=cw, ch=ch, y0=testa)
        for i, g in enumerate(GIORNI):
            cv.create_text(cw * i + cw / 2, testa / 2, text=g, fill=FG, font=("Arial", 9, "bold"))
        eventi = _occorrenze(_tutte(dati), settimane[0][0], settimane[-1][-1])
        oggi_ = datetime.date.today()
        righe_max = max(0, int((ch - 28) // 13))
        car_max = max(4, int(cw // 6.2))
        for r, sett in enumerate(settimane):
            for c, d in enumerate(sett):
                x1, y1 = cw * c, testa + ch * r
                x2, y2 = x1 + cw, y1 + ch
                cv.create_rectangle(x1, y1, x2, y2, outline=GRIGLIA, fill=BG)
                altro_mese = d.month != mese
                col_num = "gray50" if altro_mese else (ROSSO if d.weekday() == 6 else FG)
                if d == oggi_:
                    cv.create_oval(x1 + 3, y1 + 3, x1 + 21, y1 + 21, fill=HL, outline=HL)
                    cv.create_text(x1 + 12, y1 + 12, text=str(d.day), fill="white", font=("Arial", 9, "bold"))
                else:
                    cv.create_text(x1 + 12, y1 + 12, text=str(d.day), fill=col_num, font=("Arial", 9, "bold"))
                if altro_mese:
                    continue
                voci = eventi.get(d, [])
                mostra = voci if len(voci) <= righe_max else voci[:max(0, righe_max - 1)]
                for k, v in enumerate(mostra):
                    t = ("✓ " if _fatta(v, d) else "") + ("↗ " if v.get("esterna") else "") + v.get("titolo", "")
                    if len(t) > car_max:
                        t = t[:car_max - 1] + "…"
                    cv.create_text(x1 + 4, y1 + 32 + 13 * k, text=t, anchor="w",
                                   fill=colore_voce(v, d), font=("Arial", 8))
                resto = len(voci) - len(mostra)
                if resto > 0:
                    cv.create_text(x1 + 4, y1 + 32 + 13 * len(mostra), text=f"+{resto} altre", anchor="w",
                                   fill=FG, font=("Arial", 8, "italic"))
                if d == stato["sel"]:
                    cv.create_rectangle(x1 + 1, y1 + 1, x2 - 1, y2 - 1, outline=HL, width=2)

    def data_da_click(x, y):
        if y < geom["y0"] or not geom["settimane"]:
            return None
        c = int(x // geom["cw"])
        r = int((y - geom["y0"]) // geom["ch"])
        if 0 <= r < len(geom["settimane"]) and 0 <= c < 7:
            return geom["settimane"][r][c]
        return None

    def click_giorno(e):
        cv.focus_set()
        d = data_da_click(e.x, e.y)
        if d:
            stato["sel"] = d
            if (d.year, d.month) != (stato["anno"], stato["mese"]):
                stato["anno"], stato["mese"] = d.year, d.month
            ridisegna()
            aggiorna_pannelli()

    def doppio_click_giorno(e):
        d = data_da_click(e.x, e.y)
        if d:
            stato["sel"] = d
            ridisegna()
            aggiorna_pannelli()
            apri_form(None, d)

    tip = {"win": None, "timer": None, "data": None}

    def tip_nascondi(_e=None):
        if tip["timer"]:
            try:
                popup.after_cancel(tip["timer"])
            except Exception:
                pass
            tip["timer"] = None
        if tip["win"] is not None:
            try:
                tip["win"].destroy()
            except Exception:
                pass
            tip["win"] = None

    def tip_testo(d):
        righe = []
        if d == datetime.date.today():
            righe.append(("Oggi", None, True))
        voci = _occorrenze(_tutte(dati), d, d).get(d, [])
        for n, v in enumerate(voci):
            fatta = _fatta(v, d)
            col = None
            if not fatta and v.get("tipo") == "Scadenza":
                col = getattr(self, "COLOR_RED_SMOOTH", COL_SCADENZA)
            elif fatta:
                col = COL_FATTO
            if n or righe:
                righe.append(("", None, False))
            righe.append((("✓ " if fatta else "") + (v["ora"] + "  " if v.get("ora") else "") + ("↗ " if v.get("esterna") else "") + v.get("titolo", ""), col, True))
            dett = v.get("tipo", "") + (f" · da {v['origine']}" if v.get("esterna") else "")
            if v.get("importo") not in (None, ""):
                dett += f"  ·  {_fmt_eur(v['importo'])}"
            righe.append((dett, col, False))
            if _testo_fine(v) or v.get("luogo"):
                righe.append(("  ·  ".join(x for x in (_testo_fine(v), ("@ " + v["luogo"]) if v.get("luogo") else "") if x), col, False))
            if v.get("ripetizione", "Nessuna") != "Nessuna":
                righe.append((f"↻ ripete: {_rip_testo(v)}", None, False))
            if v.get("note"):
                righe.append((v["note"].strip(), None, False))
        return righe

    def tip_mostra(d, x, y):
        tip["timer"] = None
        righe = tip_testo(d)
        if not righe:
            return
        w = tk.Toplevel(popup)
        tip["win"] = w
        w.withdraw()
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        bg_t = getattr(self, "COLOR_TOOLTIP", "#F9F9F9")
        fg_t = getattr(self, "COLOR_TEXT_TOOLTIP", "black")
        w.config(highlightthickness=1, highlightbackground=HL, bg=bg_t)
        fr_t = tk.Frame(w, bg=bg_t, relief="solid", borderwidth=1)
        fr_t.pack(fill="both", expand=True)
        for testo, col, bold in righe:
            if not testo:
                tk.Frame(fr_t, bg=bg_t, height=4).pack(fill="x")
                continue
            tk.Label(fr_t, text=testo, bg=bg_t, fg=col or fg_t, font=("Arial", 9, "bold" if bold else "normal"),
                     anchor="w", justify="left", wraplength=320).pack(fill="x", padx=8, pady=1)
        w.update_idletasks()
        px = min(x + 14, popup.winfo_screenwidth() - w.winfo_reqwidth() - 4)
        py = min(y + 14, popup.winfo_screenheight() - w.winfo_reqheight() - 4)
        w.geometry(f"+{max(px, 0)}+{max(py, 0)}")
        w.deiconify()

    def tip_muovi(e):
        d = data_da_click(e.x, e.y)
        if d == tip["data"]:
            return
        tip_nascondi()
        tip["data"] = d
        if d and getattr(_app, "CAL_TOOLTIPS", True) and d.month == stato["mese"] and tip_testo(d):
            tip["timer"] = popup.after(700, lambda: tip_mostra(d, e.x_root, e.y_root))

    def tip_esci(e=None):
        tip["data"] = None
        tip_nascondi()

    cv.bind("<Motion>", tip_muovi, add="+")
    cv.bind("<Leave>", tip_esci, add="+")
    cv.bind("<Button-1>", tip_esci, add="+")
    cv.bind("<Configure>", ridisegna)
    cv.bind("<Button-1>", click_giorno, add="+")
    cv.bind("<Double-1>", doppio_click_giorno)

    dx = ttk.Frame(tab_agenda)
    dx.grid(row=0, column=1, sticky="nsew")
    dx.columnconfigure(0, weight=1)
    dx.rowconfigure(2, weight=3)
    dx.rowconfigure(5, weight=2)

    lbl_giorno = ttk.Label(dx, font=("Arial", 11, "bold"))
    lbl_giorno.grid(row=0, column=0, sticky="w", pady=(0, 4))

    bt = ttk.Frame(dx)
    bt.grid(row=1, column=0, sticky="ew", pady=(0, 4))

    cols_g = ("ora", "titolo", "tipo", "importo")
    fr_g = ttk.Frame(dx)
    fr_g.grid(row=2, column=0, sticky="nsew")
    try:
        _f = tkfont.Font(font=ttk.Style().lookup("Treeview", "font") or "TkDefaultFont")
        W_IMPORTO = max(_f.measure("99.999,99 €"), tkfont.Font(font=ttk.Style().lookup("Treeview.Heading", "font") or "TkHeadingFont").measure("Importo")) + 24
    except Exception:
        W_IMPORTO = 130
    tree_g = ttk.Treeview(fr_g, columns=cols_g, show="headings", selectmode="browse", height=8)
    for c, t, w_, a in (("ora", "Ora", 50, "center"), ("titolo", "Titolo", 140, "w"),
                        ("tipo", "Tipo", 120, "w"), ("importo", "Importo", W_IMPORTO, "e")):
        tree_g.heading(c, text=t)
        tree_g.column(c, width=w_, minwidth=w_, anchor=a, stretch=(c == "titolo"))
    sb_g = ttk.Scrollbar(fr_g, orient="vertical", command=tree_g.yview, style="Vertical.TScrollbar")
    tree_g.configure(yscrollcommand=sb_g.set)
    tree_g.pack(side="left", fill="both", expand=True)
    sb_g.pack(side="right", fill="y")
    tree_g.tag_configure("fatta", foreground=COL_FATTO)

    lbl_dettaglio = ttk.Label(dx, wraplength=360, justify="left", foreground="gray")
    lbl_dettaglio.grid(row=3, column=0, sticky="ew", pady=(4, 6))

    fr_cerca = ttk.Frame(dx)
    fr_cerca.grid(row=4, column=0, sticky="ew", pady=(0, 2))
    lbl_prossimi = ttk.Label(fr_cerca, font=("Arial", 10, "bold"))
    lbl_prossimi.pack(side="left")
    v_cerca = tk.StringVar(popup)
    e_cerca = ttk.Entry(fr_cerca, textvariable=v_cerca, width=12)
    e_cerca.pack(side="right")
    ttk.Label(fr_cerca, text="Cerca:").pack(side="right", padx=(0, 4))
    v_range = tk.StringVar(popup, value="30 giorni")
    cb_range = ttk.Combobox(fr_cerca, textvariable=v_range, values=("7 giorni", "30 giorni", "Mese", "Anno", "Tutte"),
                            state="readonly", width=10, style="Border.TCombobox")
    cb_range.pack(side="right", padx=(0, 8))
    cb_range.bind("<<ComboboxSelected>>", lambda e: aggiorna_pannelli())
    cols_p = ("data", "titolo", "quando")
    fr_p = ttk.Frame(dx)
    fr_p.grid(row=5, column=0, sticky="nsew")
    tree_p = ttk.Treeview(fr_p, columns=cols_p, show="headings", selectmode="browse", height=6)
    for c, t, w_, a in (("data", "Data", 100, "center"), ("titolo", "Titolo", 140, "w"), ("quando", "Quando", 115, "w")):
        tree_p.heading(c, text=t)
        tree_p.column(c, width=w_, anchor=a, stretch=(c == "titolo"))
    sb_p = ttk.Scrollbar(fr_p, orient="vertical", command=tree_p.yview, style="Vertical.TScrollbar")
    tree_p.configure(yscrollcommand=sb_p.set)
    tree_p.pack(side="left", fill="both", expand=True)
    sb_p.pack(side="right", fill="y")
    tree_p.tag_configure("scaduta", foreground=ROSSO)
    tree_p.tag_configure("oggi", foreground=HL)
    tree_p.tag_configure("anticipo", foreground=COL_ANTICIPO)

    ordine = {}

    def ordina_colonna(treeview, col, reverse):
        def converti(valore):
            if col == "data":
                try:
                    return datetime.datetime.strptime(valore, "%d-%m-%Y")
                except Exception:
                    return datetime.datetime.max
            if col == "importo":
                try:
                    return float(valore.replace("€", "").replace(".", "").replace(",", ".").strip())
                except Exception:
                    return -1.0
            if col == "ora":
                return "99:99" if valore in ("—", "") else valore
            if col == "quando":
                v = valore.lower()
                if v.startswith("scaduta"):
                    return -int(v.split()[1]) if v.split()[1].isdigit() else -1
                if v == "oggi":
                    return 0
                if v == "domani":
                    return 1
                return int(v.split()[1]) if v.startswith("tra") and v.split()[1].isdigit() else 999
            return valore.lower().lstrip("✓↗ ") if isinstance(valore, str) else valore
        dati_r = [(treeview.set(k, col), k) for k in treeview.get_children("")]
        dati_r.sort(key=lambda t: converti(t[0]), reverse=reverse)
        for index, (val, k) in enumerate(dati_r):
            treeview.move(k, "", index)
        ordine[treeview] = (col, reverse)
        for c in treeview["columns"]:
            base_text = titoli[treeview][c]
            if c == col:
                freccia = " ▲" if not reverse else " ▼"
                treeview.heading(c, text=base_text + freccia,
                                 command=lambda _c=c: ordina_colonna(treeview, _c, not reverse))
            else:
                treeview.heading(c, text=base_text,
                                 command=lambda _c=c: ordina_colonna(treeview, _c, False))

    titoli = {}

    def abilita_ordinamento(treeview):
        titoli[treeview] = {c: treeview.heading(c, "text") for c in treeview["columns"]}
        for c in treeview["columns"]:
            treeview.heading(c, command=lambda _c=c: ordina_colonna(treeview, _c, False))

    def riapplica_ordine(treeview):
        if treeview in ordine:
            col, rev = ordine[treeview]
            ordina_colonna(treeview, col, rev)

    abilita_ordinamento(tree_g)
    abilita_ordinamento(tree_p)

    map_g, map_p = {}, {}

    def selezione_corrente():
        s = tree_g.selection()
        if s and s[0] in map_g:
            return map_g[s[0]]
        s = tree_p.selection()
        if s and s[0] in map_p:
            return map_p[s[0]]
        return None, None

    def etichetta_titolo(v, d):
        return ("✓ " if _fatta(v, d) else "") + ("↗ " if v.get("esterna") else "") + v.get("titolo", "")

    def aggiorna_pannelli():
        d = stato["sel"]
        lbl_giorno.config(text=f"{GIORNI_ESTESI[d.weekday()]} {d.day} {MESI[d.month - 1].lower()} {d.year}")
        agenda = _tutte(dati)
        tree_g.delete(*tree_g.get_children())
        map_g.clear()
        for v in _occorrenze(agenda, d, d).get(d, []):
            tipo = f"{v.get('tipo', 'Scadenza')} · {v.get('origine', '')}" if v.get("esterna") else (
                v.get("tipo", "") + (" ↻" if v.get("ripetizione", "Nessuna") != "Nessuna" else ""))
            iid = tree_g.insert("", "end", values=(
                v.get("ora") or "—", etichetta_titolo(v, d), tipo,
                _fmt_eur(v["importo"]) if v.get("importo") not in (None, "") else ""),
                tags=("fatta",) if _fatta(v, d) else ())
            map_g[iid] = (v, d)
        tree_p.delete(*tree_p.get_children())
        map_p.clear()
        t = datetime.date.today()
        q = v_cerca.get().strip().lower()

        def passa(v):
            return not q or q in " ".join((v.get("titolo", ""), v.get("note", ""), v.get("origine", ""))).lower()

        ritardo = [(dd, v) for dd, v in _scaduti(agenda, t) if passa(v)]
        scelta = v_range.get()
        if q:
            fine = t + datetime.timedelta(days=365)
        elif scelta == "7 giorni":
            fine = t + datetime.timedelta(days=7)
        elif scelta == "Mese":
            fine = (t.replace(day=28) + datetime.timedelta(days=4)).replace(day=1) - datetime.timedelta(days=1)
        elif scelta == "Anno":
            fine = datetime.date(t.year, 12, 31)
        elif scelta == "Tutte":
            lontane = []
            for v_ in agenda:
                if v_.get("ripetizione", "Nessuna") == "Nessuna":
                    try:
                        lontane.append(_data(v_))
                    except Exception:
                        pass
            fine = min(max(lontane + [t + datetime.timedelta(days=365)]), t + datetime.timedelta(days=1825))
        else:
            fine = t + datetime.timedelta(days=30)
        prossimi = _occorrenze(agenda, t, fine)
        n_pross = 0
        for dd, v in ritardo:
            iid = tree_p.insert("", "end", values=(_fmt_data(dd), etichetta_titolo(v, dd) if v.get("esterna") else v.get("titolo", ""),
                                                   f"scaduta {(t - dd).days} g fa"), tags=("scaduta",))
            map_p[iid] = (v, dd)
        for dd in sorted(prossimi):
            for v in prossimi[dd]:
                if _fatta(v, dd) or not passa(v):
                    continue
                dif = (dd - t).days
                try:
                    pre = int(v.get("preavviso", 0) or 0)
                except (TypeError, ValueError):
                    pre = 0
                quando = "oggi" if dif == 0 else ("domani" if dif == 1 else f"tra {dif} giorni")
                if v.get("ora"):
                    quando += f" · {v['ora']}"
                tag = ("oggi",) if dif == 0 else (("anticipo",) if 0 < dif <= pre else ())
                iid = tree_p.insert("", "end", values=(_fmt_data(dd), etichetta_titolo(v, dd) if v.get("esterna") else v.get("titolo", ""), quando),
                                    tags=tag)
                map_p[iid] = (v, dd)
                n_pross += 1
        riapplica_ordine(tree_g)
        riapplica_ordine(tree_p)
        if q:
            lbl_prossimi.config(text=f"Ricerca: {n_pross + len(ritardo)} risultati")
        else:
            lbl_prossimi.config(text=f"In arrivo: {n_pross}   ·   Scadute: {len(ritardo)}")
        lbl_dettaglio.config(text="")
        aggiorna_stato()

    v_cerca.trace_add("write", lambda *_a: aggiorna_pannelli())

    def mostra_dettaglio(_e=None):
        v, d = selezione_corrente()
        if not v:
            lbl_dettaglio.config(text="")
            return
        righe = []
        if v.get("esterna"):
            righe.append(f"Da {v.get('origine', '')} (sola lettura): doppio clic o Modifica per aprire il modulo.")
        if _testo_fine(v):
            righe.append("Durata: " + _testo_fine(v))
        if v.get("luogo"):
            righe.append(f"Luogo: {v['luogo']}")
        if v.get("ripetizione", "Nessuna") != "Nessuna":
            righe.append(f"Ripetizione: {_rip_testo(v)}")
        if int(v.get("preavviso", 0) or 0) > 0 and not v.get("esterna"):
            righe.append(f"Avviso: {v['preavviso']} giorn{'o' if v['preavviso'] == 1 else 'i'} prima")
        if v.get("ora") and not v.get("esterna"):
            righe.append(f"Avviso orario: {_anticipo_min(v)} min prima")
        if v.get("email") and not v.get("esterna"):
            righe.append("Email: attiva")
        if v.get("note"):
            righe.append(v["note"].strip())
        lbl_dettaglio.config(text="\n".join(righe))

    def sel_giorno(_e=None):
        if tree_g.selection():
            tree_p.selection_remove(tree_p.selection())
        mostra_dettaglio()

    def sel_prossimi(_e=None):
        if tree_p.selection():
            tree_g.selection_remove(tree_g.selection())
        mostra_dettaglio()

    def vai_a_data(_e=None):
        s = tree_p.selection()
        if s and s[0] in map_p:
            d = map_p[s[0]][1]
            stato["sel"] = d
            stato["anno"], stato["mese"] = d.year, d.month
            vid = map_p[s[0]][0]["id"]
            ridisegna()
            aggiorna_pannelli()
            for iid, (v, _d) in map_g.items():
                if v["id"] == vid:
                    tree_g.selection_set(iid)
                    break

    tree_g.bind("<<TreeviewSelect>>", sel_giorno)
    tree_p.bind("<<TreeviewSelect>>", sel_prossimi)
    tree_g.bind("<Double-1>", lambda e: modifica())
    tree_p.bind("<Double-1>", vai_a_data)

    def apri_origine(v):
        fn = getattr(self, v.get("apri", ""), None)
        if not fn:
            self.show_toast("Modulo non disponibile.")
            return
        try:
            fn()
        except Exception as e:
            self.show_custom_warning("Errore", f"Impossibile aprire {v.get('origine', 'il modulo')}: {e}")

    def modifica():
        v, d = selezione_corrente()
        if not v:
            return
        if v.get("esterna"):
            apri_origine(v)
            return
        apri_form(v, d)

    def solo_lettura(v):
        if v.get("esterna"):
            self.show_toast(f"Voce di {v.get('origine', 'un altro modulo')}: si gestisce da lì.")
            return True
        return False

    def alterna_fatto():
        v, d = selezione_corrente()
        if not v or solo_lettura(v):
            return
        k = d.isoformat()
        if k in v["fatti"]:
            v["fatti"].remove(k)
        else:
            v["fatti"].append(k)
        _tocca(v)
        salva()
        ridisegna()
        aggiorna_pannelli()

    def elimina():
        v, d = selezione_corrente()
        if not v or solo_lettura(v):
            return
        rip = v.get("ripetizione", "Nessuna") != "Nessuna"
        msg = f"Eliminare '{v.get('titolo', '')}'?"
        if rip:
            msg += "\nLa voce si ripete: verranno eliminate tutte le occorrenze."
        if not self.show_custom_askyesno("Elimina voce", msg):
            return
        dati["agenda"] = [x for x in dati["agenda"] if x["id"] != v["id"]]
        salva()
        ridisegna()
        aggiorna_pannelli()

    def posticipa(modo):
        v, d = selezione_corrente()
        if not v or solo_lettura(v):
            return
        adesso = datetime.datetime.now()
        ora = (v.get("ora") or "").strip()
        try:
            h = datetime.datetime.strptime(ora, "%H:%M").time() if ora else None
        except ValueError:
            h = None
        base_d = max(d, adesso.date())
        if modo == "ora":
            if h is None:
                self.show_toast("Questa voce non ha un'ora.")
                return
            nuovo = max(datetime.datetime.combine(d, h), adesso) + datetime.timedelta(hours=1)
            nd, nh = nuovo.date(), nuovo.strftime("%H:%M")
        elif modo == "giorno":
            nd, nh = base_d + datetime.timedelta(days=1), ora
        else:
            nd, nh = base_d + datetime.timedelta(days=7), ora
        if v.get("ripetizione", "Nessuna") == "Nessuna":
            _gg = _durata_gg(v)
            v["data"] = nd.isoformat()
            v["ora"] = nh
            v["data_fine"] = (nd + datetime.timedelta(days=_gg)).isoformat() if _gg else ""
            if nh != ora:
                v["ora_fine"] = ""
            v["fatti"] = []
            _tocca(v)
            av = getattr(self, "_agenda_orari_avvisati", None)
            if av:
                av.difference_update({k for k in av if k[0] == v["id"]})
        else:
            nuova = {k: v[k] for k in ("titolo", "tipo", "importo", "note", "preavviso", "email", "anticipo_min", "luogo") if k in v}
            nuova.update(id=uuid.uuid4().hex[:8], data=nd.isoformat(), ora=nh, ripetizione="Nessuna", fatti=[])
            _tocca(nuova)
            dati["agenda"].append(nuova)
            if d.isoformat() not in v["fatti"]:
                v["fatti"].append(d.isoformat())
            _tocca(v)
        stato["sel"] = nd
        stato["anno"], stato["mese"] = nd.year, nd.month
        salva()
        ridisegna()
        aggiorna_pannelli()
        self.show_toast(f"Posticipata a {_fmt_data(nd)}" + (f" {nh}" if nh else ""))

    def menu_posticipa(ancora):
        v, d = selezione_corrente()
        if not v:
            self.show_toast("Seleziona una voce.")
            return
        m = tk.Menu(popup, tearoff=0, bg=BG, fg=FG, activebackground=HL, activeforeground="white")
        libero = not v.get("esterna")
        m.add_command(label="+1 ora", command=lambda: posticipa("ora"),
                      state="normal" if (libero and v.get("ora")) else "disabled")
        m.add_command(label="+1 giorno", command=lambda: posticipa("giorno"), state="normal" if libero else "disabled")
        m.add_command(label="+1 settimana", command=lambda: posticipa("settimana"), state="normal" if libero else "disabled")
        try:
            m.tk_popup(ancora.winfo_rootx(), ancora.winfo_rooty() + ancora.winfo_height())
        finally:
            m.grab_release()

    def google_calendar():
        v, d = selezione_corrente()
        if not v:
            return
        if not hasattr(self, "launch_qr_svg_generator"):
            self.show_custom_warning("Calendar", "Generatore Google Calendar non disponibile.")
            return
        desc = v.get("titolo", "")
        if v.get("ora"):
            desc += f" (ore {v['ora']})"
        if v.get("note"):
            desc += " - " + v["note"].strip().splitlines()[0]
        imp = ""
        if v.get("importo") not in (None, ""):
            imp = f"{float(v['importo']):.2f}".replace(".", ",")
        self.launch_qr_svg_generator(initial_category="Promemoria", initial_amount=imp,
                                     initial_date=_fmt_data(d), initial_description=desc,
                                     initial_type="Promemoria")

    bt_r1 = ttk.Frame(bt)
    bt_r1.pack(fill="x")
    bt_r2 = ttk.Frame(bt)
    bt_r2.pack(fill="x", pady=(2, 0))
    _lbl(bt_r1, "Nuovo", lambda: apri_form(None, stato["sel"]), "aggiungi").pack(side="left", padx=(0, 4))
    _lbl(bt_r1, "Modifica", modifica, "modifica").pack(side="left", padx=4)
    _lbl(bt_r1, "Fatto / Riapri", alterna_fatto, "check").pack(side="left", padx=4)
    _lbl(bt_r1, "Elimina", elimina, "delete").pack(side="left", padx=4)
    lb_post = _lbl(bt_r2, "Posticipa", lambda: menu_posticipa(lb_post), "timer")
    lb_post.pack(side="left", padx=(0, 4))
    _lbl(bt_r2, "Google Calendar", google_calendar, "calendario").pack(side="left", padx=4)

    def scegli_ora(f, v_ora, ancora):
        vecchio = getattr(f, "_orologio", None)
        try:
            if vecchio is not None and vecchio.winfo_exists():
                vecchio.destroy()
                f._orologio = None
                return
        except Exception:
            pass
        try:
            corrente = _normalizza_ora(v_ora.get())
        except ValueError:
            corrente = ""
        adesso_ = datetime.datetime.now()
        st = {"h": int(corrente[:2]) if corrente else adesso_.hour, "m": int(corrente[3:]) if corrente else 0}
        w = tk.Toplevel(f)
        f._orologio = w
        w.title("Scegli l'ora")
        w.configure(bg=BG_MAIN)
        w.transient(f)
        w.resizable(False, False)
        cont = tk.Frame(w, bg=BG_MAIN, padx=14, pady=10)
        cont.pack()

        def aggiorna(scrivi=True):
            lbl_h.config(text=f"{st['h']:02d}")
            lbl_m.config(text=f"{st['m']:02d}")
            if scrivi:
                v_ora.set(f"{st['h']:02d}:{st['m']:02d}")

        def passo(chiave, delta, blocchi=False):
            if chiave == "h":
                st["h"] = (st["h"] + delta) % 24
            else:
                m = st["m"]
                if blocchi:
                    m = (m // 5) * 5 + 5 if delta > 0 else ((m - 1) // 5) * 5 if m % 5 else m - 5
                else:
                    m += delta
                st["m"] = m % 60
            aggiorna()

        def colonna(c, chiave):
            su = tk.Label(cont, text="▲", bg=BG_MAIN, fg=HL, font=("Arial", 16, "bold"), cursor="hand2")
            su.grid(row=0, column=c)
            val = tk.Label(cont, bg=BG, fg=FG, font=("Arial", 30, "bold"), width=3, relief="groove", borderwidth=1)
            val.grid(row=1, column=c, padx=2)
            giu = tk.Label(cont, text="▼", bg=BG_MAIN, fg=HL, font=("Arial", 16, "bold"), cursor="hand2")
            giu.grid(row=2, column=c)
            su.bind("<Button-1>", lambda e: passo(chiave, 1, True))
            giu.bind("<Button-1>", lambda e: passo(chiave, -1, True))
            for wd in (val, su, giu):
                wd.bind("<MouseWheel>", lambda e: passo(chiave, 1 if e.delta > 0 else -1))
                wd.bind("<Button-4>", lambda e: passo(chiave, 1))
                wd.bind("<Button-5>", lambda e: passo(chiave, -1))
            return val
        lbl_h = colonna(0, "h")
        tk.Label(cont, text=":", bg=BG_MAIN, fg=FG, font=("Arial", 30, "bold")).grid(row=1, column=1)
        lbl_m = colonna(2, "m")

        def imposta_e_chiudi(testo):
            v_ora.set(testo)
            w.destroy()

        rapidi = tk.Frame(cont, bg=BG_MAIN)
        rapidi.grid(row=3, column=0, columnspan=3, pady=(10, 0))
        for i, t in enumerate(("08:00", "09:00", "12:00", "15:00", "18:00", "20:00")):
            b_ = tk.Label(rapidi, text=t, bg=BG, fg=FG, font=("Arial", 10, "bold"), relief="groove",
                          borderwidth=1, cursor="hand2", padx=6, pady=3)
            b_.grid(row=i // 3, column=i % 3, padx=2, pady=2)
            b_.bind("<Button-1>", lambda e, x=t: imposta_e_chiudi(x))

        bt_o = tk.Frame(cont, bg=BG_MAIN)
        bt_o.grid(row=4, column=0, columnspan=3, pady=(8, 0), sticky="ew")
        _lbl(bt_o, "Adesso", lambda: imposta_e_chiudi(f"{datetime.datetime.now():%H:%M}"), "oggi").pack(side="left")
        _lbl(bt_o, "Nessuna ora", lambda: imposta_e_chiudi(""), "cancella").pack(side="left", padx=4)
        _lbl(bt_o, "OK", w.destroy, "check").pack(side="right")
        w.bind("<Escape>", lambda e: w.destroy())
        w.bind("<Return>", lambda e: w.destroy())
        aggiorna(scrivi=False)
        w.update_idletasks()

        ww, hh = w.winfo_reqwidth(), w.winfo_reqheight()
        x = f.winfo_rootx() + (f.winfo_width() - ww) // 2
        y = f.winfo_rooty() + (f.winfo_height() - hh) // 2
        x = max(0, min(x, w.winfo_screenwidth() - ww - 8))
        y = max(0, min(y, w.winfo_screenheight() - hh - 48))
        w.geometry(f"+{x}+{y}")
        
        w.focus_set()

    def apri_form(voce, data_iniziale):
        if getattr(popup, "_form", None) is not None and popup._form.winfo_exists():
            popup._form.lift()
            return
        nuovo = voce is None
        f = tk.Toplevel(popup)
        popup._form = f
        f.title("Nuova voce" if nuovo else "Modifica voce")
        f.configure(bg=popup.cget("bg"))
        f.transient(popup)
        f.resizable(False, False)
        fr = ttk.Frame(f, padding=12)
        fr.pack(fill="both", expand=True)
        fr.columnconfigure(1, weight=1)

        v_tit = tk.StringVar(f, value="" if nuovo else voce.get("titolo", ""))
        v_tipo = tk.StringVar(f, value="Appuntamento" if nuovo else voce.get("tipo", "Appuntamento"))
        d0 = data_iniziale if nuovo else _data(voce)
        v_data = tk.StringVar(f, value=_fmt_data(d0))
        v_ora = tk.StringVar(f, value="" if nuovo else voce.get("ora", ""))
        v_imp = tk.StringVar(f, value="" if nuovo or voce.get("importo") in (None, "")
                             else f"{float(voce['importo']):.2f}".replace(".", ","))
        v_rip = tk.StringVar(f, value="Nessuna" if nuovo else voce.get("ripetizione", "Nessuna"))
        _n0, _u0 = (None, None) if nuovo else _rip_params(voce)
        v_rip_n = tk.StringVar(f, value=str(_n0 or 1))
        v_rip_u = tk.StringVar(f, value=_u0 or "mesi")
        v_email = tk.BooleanVar(f, value=False if nuovo else bool(voce.get("email", False)))
        _ant_lbl = lambda n: next((e for e, x in ANTICIPI_ORA if x == n), ANTICIPI_ORA[1][0])
        v_ant = tk.StringVar(f, value=_ant_lbl(ANTICIPO_ORA_MIN if nuovo else _anticipo_min(voce)))

        def riga(r, testo):
            ttk.Label(fr, text=testo).grid(row=r, column=0, sticky="w", pady=4, padx=(0, 10))

        riga(0, "Titolo")
        def _v_tit(P): return len(P) <= MAX_TITOLO
        def _v_imp(P): return len(P) <= MAX_IMPORTO and re.match(r"^\d*[.,]?\d{0,2}$", P) is not None
        def _v_ora(P): return len(P) <= 5 and re.match(r"^[\d:.,]*$", P) is not None
        def _v_data(P): return len(P) <= 10 and re.match(r"^[\d\-]*$", P) is not None
        e_tit = ttk.Entry(fr, textvariable=v_tit, width=38, validate="key",
                          validatecommand=(f.register(_v_tit), "%P"))
        e_tit.grid(row=0, column=1, columnspan=2, sticky="ew")
        riga(1, "Tipo")
        cb_tipo = ttk.Combobox(fr, textvariable=v_tipo, values=TIPI, state="readonly", width=16, style="Border.TCombobox")
        cb_tipo.grid(row=1, column=1, sticky="w")
        riga(2, "Data")
        fr_data = ttk.Frame(fr)
        fr_data.grid(row=2, column=1, sticky="w")
        e_data = ttk.Entry(fr_data, textvariable=v_data, width=14, validate="key",
                           validatecommand=(f.register(_v_data), "%P"))
        e_data.pack(side="left")

        btn_cal = _lbl(fr_data, "", lambda: self.mostra_calendario_popup_semplice(e_data, v_data), "calendario")
        if not btn_cal.cget("image"):
            btn_cal.config(text="📅")
        btn_cal.pack(side="left", padx=2)
        riga(3, "Ora (HH:MM)")
        fr_ora = ttk.Frame(fr)
        fr_ora.grid(row=3, column=1, sticky="w")
        e_ora = ttk.Entry(fr_ora, textvariable=v_ora, width=8, validate="key",
                          validatecommand=(f.register(_v_ora), "%P"))
        e_ora.pack(side="left")

        def norm_ora(_e=None):
            try:
                v_ora.set(_normalizza_ora(v_ora.get()))
            except ValueError:
                pass
        e_ora.bind("<FocusOut>", norm_ora)
        btn_ora = _lbl(fr_ora, "", lambda: scegli_ora(f, v_ora, btn_ora), "timer")
        if not btn_ora.cget("image"):
            btn_ora.config(text="🕐")
        btn_ora.pack(side="left", padx=2)
        riga(4, "Importo (€)")
        ttk.Entry(fr, textvariable=v_imp, width=14, validate="key",
                  validatecommand=(f.register(_v_imp), "%P")).grid(row=4, column=1, sticky="w")
        riga(5, "Ripetizione")
        fr_rip = ttk.Frame(fr)
        fr_rip.grid(row=5, column=1, columnspan=2, sticky="w")
        cb_rip = ttk.Combobox(fr_rip, textvariable=v_rip, values=RIPETIZIONI, state="readonly", width=16, style="Border.TCombobox")
        cb_rip.pack(side="left")
        fr_rip_c = ttk.Frame(fr_rip)
        ttk.Label(fr_rip_c, text="ogni").pack(side="left", padx=(8, 4))

        def _v_rip_n(P): return len(P) <= 2 and (P == "" or P.isdigit())
        ttk.Entry(fr_rip_c, textvariable=v_rip_n, width=3, validate="key",
                  validatecommand=(f.register(_v_rip_n), "%P")).pack(side="left")
        ttk.Combobox(fr_rip_c, textvariable=v_rip_u, values=UNITA_RIP, state="readonly", width=9,
                     style="Border.TCombobox").pack(side="left", padx=(4, 0))

        def mostra_rip_c(_e=None):
            if v_rip.get() == "Personalizzata":
                fr_rip_c.pack(side="left")
            else:
                fr_rip_c.pack_forget()
        cb_rip.bind("<<ComboboxSelected>>", mostra_rip_c)
        mostra_rip_c()
        etichette_pre = [e for e, _n in PREAVVISI]

        def pre_label(n):
            return next((e for e, x in PREAVVISI if x == n), PREAVVISI[0][0])
        v_pre = tk.StringVar(f, value=pre_label(0 if nuovo else int(voce.get("preavviso", 0) or 0)))
        pre_toccato = {"v": not nuovo}
        riga(6, "Avvisami")
        cb_pre = ttk.Combobox(fr, textvariable=v_pre, values=etichette_pre, state="readonly", width=16, style="Border.TCombobox")
        cb_pre.grid(row=6, column=1, sticky="w")
        cb_pre.bind("<<ComboboxSelected>>", lambda e: pre_toccato.update(v=True))
        cb_tipo.bind("<<ComboboxSelected>>", lambda e: None if pre_toccato["v"] else
                     v_pre.set(pre_label(3 if v_tipo.get() == "Scadenza" else 0)))
        riga(7, "Avviso orario")
        cb_ant = ttk.Combobox(fr, textvariable=v_ant, values=[e for e, _n in ANTICIPI_ORA], state="readonly", width=16, style="Border.TCombobox")
        cb_ant.grid(row=7, column=1, sticky="w")

        def agg_ant(*_a):
            cb_ant.config(state="readonly" if v_ora.get().strip() else "disabled")
        v_ora.trace_add("write", agg_ant)
        agg_ant()
        _em_ok = _email_configurata()
        chk_email = ttk.Checkbutton(fr, text="Invia anche via email" + ("" if _em_ok else " (email non configurata)"),
                                    variable=v_email, state="normal" if _em_ok else "disabled")
        chk_email.grid(row=8, column=1, columnspan=2, sticky="w", pady=2)
        t_note = tk.Text(fr, width=38, height=4, wrap="word", bg=BG, fg=FG, insertbackground=FG,
                         relief="flat", borderwidth=1, highlightthickness=1, highlightbackground=GRIGLIA, highlightcolor=HL)
        t_note.grid(row=9, column=1, columnspan=2, sticky="ew")
        if not nuovo:
            t_note.insert("1.0", voce.get("note", "")[:MAX_NOTE])
        lbl_cnt = ttk.Label(fr, text="Note")
        lbl_cnt.grid(row=9, column=0, sticky="nw", pady=4, padx=(0, 10))

        def limita_note(_e=None):
            if not t_note.edit_modified():
                return
            t_note.edit_modified(False)
            testo = t_note.get("1.0", "end-1c")
            if len(testo) > MAX_NOTE:
                t_note.delete(f"1.0+{MAX_NOTE}c", "end")
            lbl_cnt.config(text=f"Note ({len(t_note.get('1.0', 'end-1c'))}/{MAX_NOTE})")
        t_note.bind("<<Modified>>", limita_note)
        t_note.edit_modified(True)
        limita_note()

        fr_ext = ttk.Frame(fr)
        fr_ext.grid(row=10, column=0, columnspan=3, sticky="ew")
        fr_ext.columnconfigure(1, weight=1)

        def riga_e(r, testo):
            lb = ttk.Label(fr_ext, text=testo)
            lb.grid(row=r, column=0, sticky="w", pady=4, padx=(0, 10))
            return lb

        def _data_it(s):
            try:
                return _fmt_data(datetime.date.fromisoformat(s)) if s else ""
            except ValueError:
                return ""
        _g = (lambda k: "" if nuovo else (voce.get(k) or ""))
        v_dfine = tk.StringVar(f, value=_data_it(_g("data_fine")))
        v_ofine = tk.StringVar(f, value=_g("ora_fine"))
        v_luogo = tk.StringVar(f, value=_g("luogo"))
        v_rfine = tk.StringVar(f, value=_data_it(_g("rip_fine")))
        v_gs = [tk.BooleanVar(f, value=(i in (_ics.giorni_da_rrule(_g("rrule")) or [d0.weekday()]))) for i in range(7)]
        gs_toccati = {"v": False}

        riga_e(0, "Fine")
        fr_fine = ttk.Frame(fr_ext)
        fr_fine.grid(row=0, column=1, sticky="w")
        e_dfine = ttk.Entry(fr_fine, textvariable=v_dfine, width=14, validate="key",
                            validatecommand=(f.register(_v_data), "%P"))
        e_dfine.pack(side="left")
        btn_cfine = _lbl(fr_fine, "", lambda: self.mostra_calendario_popup_semplice(e_dfine, v_dfine), "calendario")
        if not btn_cfine.cget("image"):
            btn_cfine.config(text="📅")
        btn_cfine.pack(side="left", padx=2)
        ttk.Label(fr_fine, text="Ora (HH:MM)").pack(side="left", padx=(8, 4))
        e_ofine = ttk.Entry(fr_fine, textvariable=v_ofine, width=8, validate="key",
                            validatecommand=(f.register(_v_ora), "%P"))
        e_ofine.pack(side="left")

        def norm_ofine(_e=None):
            try:
                v_ofine.set(_normalizza_ora(v_ofine.get()))
            except ValueError:
                pass
        e_ofine.bind("<FocusOut>", norm_ofine)
        btn_ofine = _lbl(fr_fine, "", lambda: scegli_ora(f, v_ofine, btn_ofine), "timer")
        if not btn_ofine.cget("image"):
            btn_ofine.config(text="🕐")
        btn_ofine.pack(side="left", padx=2)

        riga_e(1, "Luogo")
        ttk.Entry(fr_ext, textvariable=v_luogo, width=38, validate="key",
                  validatecommand=(f.register(lambda P: len(P) <= _ics.MAX_LUOGO), "%P")).grid(row=1, column=1, sticky="ew")

        lb_rf = riga_e(2, "Ripeti fino al")
        fr_rf = ttk.Frame(fr_ext)
        fr_rf.grid(row=2, column=1, sticky="w")
        e_rfine = ttk.Entry(fr_rf, textvariable=v_rfine, width=14, validate="key",
                            validatecommand=(f.register(_v_data), "%P"))
        e_rfine.pack(side="left")
        btn_crf = _lbl(fr_rf, "", lambda: self.mostra_calendario_popup_semplice(e_rfine, v_rfine), "calendario")
        if not btn_crf.cget("image"):
            btn_crf.config(text="📅")
        btn_crf.pack(side="left", padx=2)
        ttk.Label(fr_rf, text="(vuoto = senza fine)").pack(side="left", padx=6)

        lb_gs = riga_e(3, "Giorni")
        fr_gs = ttk.Frame(fr_ext)
        fr_gs.grid(row=3, column=1, sticky="w")
        for i_, nome_ in enumerate(GIORNI):
            ttk.Checkbutton(fr_gs, text=nome_, variable=v_gs[i_],
                            command=lambda: gs_toccati.update(v=True)).pack(side="left", padx=(0, 4))

        lb_av = riga_e(4, "Regola")
        t_av = ttk.Label(fr_ext, text=(_rip_testo(voce) if (not nuovo and voce.get("ripetizione") == "Avanzata") else "")
                         + "  (importata: per cambiarla scegli un'altra ripetizione)", wraplength=300, justify="left")
        t_av.grid(row=4, column=1, sticky="w")

        def agg_ext(*_a):
            r_ = v_rip.get()
            sett = r_ == "Settimanale" or (r_ == "Personalizzata" and v_rip_u.get() == "settimane")
            for ok, wgs in ((r_ != "Nessuna", (lb_rf, fr_rf)), (sett, (lb_gs, fr_gs)), (r_ == "Avanzata", (lb_av, t_av))):
                for w_ in wgs:
                    (w_.grid if ok else w_.grid_remove)()
        v_rip.trace_add("write", agg_ext)
        v_rip_u.trace_add("write", agg_ext)
        agg_ext()

        def conferma(_e=None):
            titolo = v_tit.get().strip()
            if not titolo:
                self.show_custom_warning("Dati mancanti", "Inserisci un titolo.")
                return
            try:
                d = datetime.datetime.strptime(v_data.get().strip(), "%d-%m-%Y").date()
            except ValueError:
                self.show_custom_warning("Data non valida", "Usa il formato GG-MM-AAAA.")
                return
            try:
                ora = _normalizza_ora(v_ora.get())
            except ValueError:
                self.show_custom_warning("Ora non valida", "Scrivi ad esempio 18, 18:30 o 1830, oppure lascia vuoto.")
                return
            try:
                imp = _parse_importo(v_imp.get())
            except ValueError:
                self.show_custom_warning("Importo non valido", "Inserisci un numero, ad esempio 85,50.")
                return

            def _data_opz(s):
                s = s.strip()
                return datetime.datetime.strptime(s, "%d-%m-%Y").date() if s else None
            try:
                d_fine = _data_opz(v_dfine.get())
            except ValueError:
                self.show_custom_warning("Data di fine non valida", "Usa il formato GG-MM-AAAA.")
                return
            if d_fine and d_fine < d:
                self.show_custom_warning("Data di fine non valida", "La fine è prima dell'inizio.")
                return
            if d_fine == d:
                d_fine = None
            try:
                ora_fine = _normalizza_ora(v_ofine.get())
            except ValueError:
                self.show_custom_warning("Ora di fine non valida", "Scrivi ad esempio 18, 18:30 o 1830, oppure lascia vuoto.")
                return
            if ora_fine and not ora:
                self.show_custom_warning("Ora di fine", "Per indicare l'ora di fine serve anche l'ora di inizio.")
                return
            if ora_fine and not d_fine and ora_fine <= ora:
                self.show_custom_warning("Ora di fine", "L'ora di fine deve essere dopo quella di inizio.")
                return
            try:
                rip_fine = _data_opz(v_rfine.get()) if v_rip.get() != "Nessuna" else None
            except ValueError:
                self.show_custom_warning("Fine ripetizione non valida", "Usa il formato GG-MM-AAAA.")
                return
            if rip_fine and rip_fine < d:
                self.show_custom_warning("Fine ripetizione non valida", "La ripetizione finisce prima dell'inizio.")
                return
            pre = next((n for e, n in PREAVVISI if e == v_pre.get()), 0)
            ant = next((n for e, n in ANTICIPI_ORA if e == v_ant.get()), ANTICIPO_ORA_MIN)
            rip_n, rip_u = 1, "mesi"
            if v_rip.get() == "Personalizzata":
                try:
                    rip_n = int(v_rip_n.get())
                    if not 1 <= rip_n <= 99:
                        raise ValueError
                except ValueError:
                    self.show_custom_warning("Ripetizione non valida", "Scrivi un numero da 1 a 99 per la ripetizione personalizzata.")
                    return
                rip_u = v_rip_u.get() if v_rip_u.get() in UNITA_RIP else "mesi"
            rr = ""
            if v_rip.get() == "Avanzata" and not nuovo:
                rr = voce.get("rrule", "")
            elif v_rip.get() == "Settimanale" or (v_rip.get() == "Personalizzata" and rip_u == "settimane"):
                sel = ([i for i, x in enumerate(v_gs) if x.get()] if gs_toccati["v"]
                       else (None if nuovo else _ics.giorni_da_rrule(voce.get("rrule"))))
                if sel and sel != [d.weekday()]:
                    rr = _ics.rrule_settimanale(rip_n if v_rip.get() == "Personalizzata" else 1, sel)
            campi = {"titolo": titolo, "tipo": v_tipo.get(), "data": d.isoformat(), "ora": ora,
                     "importo": imp, "ripetizione": v_rip.get(), "note": t_note.get("1.0", "end-1c").strip(),
                     "preavviso": pre, "anticipo_min": ant, "email": bool(v_email.get()),
                     "data_fine": d_fine.isoformat() if d_fine else "", "ora_fine": ora_fine,
                     "luogo": v_luogo.get().strip(), "rip_fine": rip_fine.isoformat() if rip_fine else "", "rrule": rr}
            if v_rip.get() == "Personalizzata":
                campi.update(rip_n=rip_n, rip_unita=rip_u)
            if nuovo:
                campi.update(id=uuid.uuid4().hex[:8], fatti=[], escluse=[])
                _tocca(campi)
                dati["agenda"].append(campi)
            else:
                if (campi["data"] != voce["data"] or campi["ripetizione"] != voce.get("ripetizione")
                        or campi["rrule"] != (voce.get("rrule") or "")
                        or (campi["ripetizione"] == "Personalizzata"
                            and (campi["rip_n"], campi["rip_unita"]) != (voce.get("rip_n"), voce.get("rip_unita")))):
                    campi["fatti"] = []
                    campi["escluse"] = []
                voce.update(campi)
                _tocca(voce)
            stato["sel"] = d
            stato["anno"], stato["mese"] = d.year, d.month
            salva()
            f.destroy()
            ridisegna()
            aggiorna_pannelli()

        bt_f = ttk.Frame(fr)
        bt_f.grid(row=11, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        _lbl(bt_f, "Salva", conferma, "check").pack(side="left", padx=(0, 4))
        _lbl(bt_f, "Annulla", f.destroy, "chiudi").pack(side="right", padx=(4, 0))
        def esc_form(_e=None):
            pc = getattr(self, "popup_calendario", None)
            if pc is not None and pc.winfo_exists():
                return
            f.destroy()
        f.bind("<Escape>", esc_form)
        f.update_idletasks()
        w, h = f.winfo_reqwidth(), f.winfo_reqheight()
        x = popup.winfo_rootx() + (popup.winfo_width() - w) // 2
        y = popup.winfo_rooty() + (popup.winfo_height() - h) // 2
        f.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        e_tit.focus_set()

    tab_note.rowconfigure(1, weight=1)
    tab_note.columnconfigure(0, weight=1)
    ttk.Label(tab_note, foreground="gray",
              text="Nota libera. Viene salvata da sola e fa parte del contesto dell'assistente IA insieme all'agenda."
              ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
    txt_note = tk.Text(tab_note, wrap="word", bg=BG, fg=FG, insertbackground=FG, relief="flat",
                       borderwidth=1, highlightthickness=1, highlightbackground=GRIGLIA, highlightcolor=HL, undo=True,
                       selectbackground=HL, selectforeground="white")
    txt_note.grid(row=1, column=0, sticky="nsew")
    sb_n = ttk.Scrollbar(tab_note, command=txt_note.yview, style="Vertical.TScrollbar")
    sb_n.grid(row=1, column=1, sticky="ns")
    txt_note.configure(yscrollcommand=sb_n.set)
    txt_note.insert("1.0", dati["note"])
    txt_note.edit_reset()

    def nota_salva():
        stato["after_note"] = None
        dati["note"] = txt_note.get("1.0", "end-1c").strip()
        salva()
        lbl_stato.config(text=f"Salvato alle {datetime.datetime.now():%H:%M:%S}   ·   " + _sintesi())

    def nota_modificata(_e=None):
        txt_note.edit_modified(False)
        if stato["after_note"]:
            popup.after_cancel(stato["after_note"])
        stato["after_note"] = popup.after(700, nota_salva)

    txt_note.bind("<<Modified>>", lambda e: nota_modificata() if txt_note.edit_modified() else None)

    piede = ttk.Frame(popup, padding=(10, 6))
    piede.pack(fill="x")
    lbl_stato = ttk.Label(piede, foreground="gray")
    lbl_stato.pack(side="left")

    def _sintesi():
        t = datetime.date.today()
        agenda = _tutte(dati)
        n_oggi = sum(1 for v in agenda if _occorre(v, t) and not _fatta(v, t))
        n_ext = len(dati.get("_ext", []))
        return (f"{len(dati['agenda'])} voci in agenda" + (f" + {n_ext} da altri moduli" if n_ext else "")
                + f", {n_oggi} per oggi, {len(_scaduti(agenda, t))} scadute")

    def aggiorna_stato():
        lbl_stato.config(text=_sintesi())

    def testo_export():
        parti = [f"AGENDA E PROMEMORIA - {_fmt_data(datetime.date.today())}", "", _testo_agenda(dati, 90, con_esterne=True)]
        nota = txt_note.get("1.0", "end-1c").strip()
        if nota:
            parti += ["", "NOTE:", nota]
        return "\n".join(parti)

    def esporta():
        now = datetime.date.today()
        self.show_export_preview(testo_export(),
                                 default_filename=f"Promemoria_Export_{now.day:02d}-{now.month:02d}-{now.year}.txt")

    def esporta_ics():
        testo, n_ev = _genera_ics(dati, esterne=dati.get("_ext"))
        if n_ev == 0:
            self.show_custom_warning("Esporta .ics", "Non ci sono voci da esportare.")
            return
        now = datetime.date.today()
        file = filedialog.asksaveasfilename(
            defaultextension=".ics", filetypes=[("Calendario iCalendar", "*.ics"), ("Tutti i file", "*.*")],
            initialdir=getattr(_app, "EXPORT_FILES", None),
            initialfile=f"Agenda_{now.day:02d}-{now.month:02d}-{now.year}.ics",
            title="Esporta agenda per Google Calendar", parent=popup)
        if not file:
            return
        try:
            with open(file, "w", encoding="utf-8", newline="") as fh:
                fh.write(testo)
            self.show_toast(f"Esportate {n_ev} voci.")
        except Exception as e:
            self.show_custom_warning("Errore", f"Impossibile salvare il file: {e}")

    def importa_ics():
        file = filedialog.askopenfilename(
            filetypes=[("Calendario iCalendar", "*.ics"), ("Tutti i file", "*.*")],
            initialdir=getattr(_app, "EXPORT_FILES", None), title="Importa calendario .ics", parent=popup)
        if not file:
            return
        try:
            with open(file, "rb") as fh:
                raw = fh.read()
            try:
                testo = raw.decode("utf-8-sig")
            except UnicodeDecodeError:
                testo = raw.decode("latin-1")
            voci, info = _ics.leggi_ics(testo, dati["agenda"], MAX_TITOLO, MAX_NOTE, ORIGINI,
                                        [n for _e, n in PREAVVISI], [n for _e, n in ANTICIPI_ORA], ANTICIPO_ORA_MIN)
            nuove, passate = _prepara_import(voci, datetime.date.today())
        except Exception as e:
            self.show_custom_warning("Errore", f"Impossibile leggere il file: {e}")
            return
        det = []
        for chiave, frase in (("doppi", "già presenti in agenda, saltati"),
                              ("annullati", "annullati nel calendario, saltati"),
                              ("da_moduli", "provenienti dagli altri moduli, saltati"),
                              ("invalidi", "senza data valida, saltati"),
                              ("eccezioni", "istanze modificate di una serie (importate come voci singole)"),
                              ("troncati", "titoli lunghi accorciati (il testo intero è nelle note)"),
                              ("note_troncate", f"note accorciate a {MAX_NOTE} caratteri"),
                              ("semplificati", "ripetizioni con parti non supportate, semplificate")):
            if info.get(chiave):
                det.append(f"• {info[chiave]} {frase}")
        riepilogo = ("\n".join(det) + "\n\n") if det else ""
        da_aggiungere = []
        if nuove:
            if not self.show_custom_askyesno("Importa .ics", f"Trovate {len(nuove)} voci da importare.\n\n{riepilogo}Procedo?"):
                return
            da_aggiungere += nuove
            riepilogo = ""
        if not nuove and not passate:
            self.show_custom_warning("Importa .ics", "Nessuna voce da importare.\n\n" + riepilogo)
            return
        if passate and self.show_custom_askyesno(
                "Importa .ics", f"{riepilogo}Ci sono {len(passate)} eventi già conclusi.\nLi importo segnati come completati?"):
            da_aggiungere += passate
        if not da_aggiungere:
            return
        dati["agenda"].extend(da_aggiungere)
        salva()
        ridisegna()
        aggiorna_pannelli()
        aggiorna_stato()
        self.show_toast(f"Importate {len(da_aggiungere)} voci.")

    def apri_fonti():
        if getattr(popup, "_fonti", None) is not None and popup._fonti.winfo_exists():
            popup._fonti.lift()
            return
        w = tk.Toplevel(popup)
        popup._fonti = w
        w.title("Fonti scadenze")
        w.configure(bg=popup.cget("bg"))
        w.transient(popup)
        w.resizable(False, False)
        fr = ttk.Frame(w, padding=12)
        fr.pack(fill="both", expand=True)
        ttk.Label(fr, text="Da quali moduli l'agenda prende le scadenze?\n(valgono anche per avvisi e badge)",
                  justify="left").pack(anchor="w", pady=(0, 8))
        var = {}
        for o in ORIGINI:
            var[o] = tk.BooleanVar(w, value=dati.get("fonti", {}).get(o, False))
            ttk.Checkbutton(fr, text=o, variable=var[o]).pack(anchor="w", pady=1)

        def conferma_fonti(_e=None):
            dati["fonti"] = {o: bool(var[o].get()) for o in ORIGINI}
            salva()
            w.destroy()
            ricarica_esterne()
            ridisegna()
            aggiorna_pannelli()

        bt_w = ttk.Frame(fr)
        bt_w.pack(fill="x", pady=(12, 0))
        _lbl(bt_w, "Salva", conferma_fonti, "check").pack(side="left", padx=(0, 4))
        _lbl(bt_w, "Annulla", w.destroy, "chiudi").pack(side="right", padx=(4, 0))
        w.bind("<Escape>", lambda e: w.destroy())
        w.update_idletasks()
        ww, hh = w.winfo_reqwidth(), w.winfo_reqheight()
        x = popup.winfo_rootx() + (popup.winfo_width() - ww) // 2
        y = popup.winfo_rooty() + (popup.winfo_height() - hh) // 2
        w.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    def apri_email_cfg():
        if getattr(popup, "_emailcfg", None) is not None and popup._emailcfg.winfo_exists():
            popup._emailcfg.lift()
            return
        w = tk.Toplevel(popup)
        popup._emailcfg = w
        w.title("Email promemoria")
        w.configure(bg=popup.cget("bg"))
        w.transient(popup)
        w.resizable(False, False)
        fr = ttk.Frame(w, padding=12)
        fr.pack(fill="both", expand=True)
        ok_cfg = _email_configurata()
        ttk.Label(fr, justify="left",
                  text="Gli avvisi email delle singole voci si attivano dal form (\"Invia anche via email\").\n"
                       "Qui puoi anche ricevere ogni giorno il riepilogo dell'agenda (scadute + prossimi 7 giorni).\n"
                       f"Le email partono solo con {_app.NAME} aperto."
                  ).pack(anchor="w", pady=(0, 8))
        ttk.Label(fr, foreground="gray" if ok_cfg else ROSSO,
                  text=f"Destinatario: {_app.EMAIL_USER}" if ok_cfg else "Email non configurata (Impostazioni)."
                  ).pack(anchor="w", pady=(0, 8))
        dg = dati.get("digest", {"attivo": False, "ora": "08:00"})
        v_dg = tk.BooleanVar(w, value=bool(dg.get("attivo")))
        v_dg_ora = tk.StringVar(w, value=dg.get("ora", "08:00"))
        ttk.Checkbutton(fr, text="Invia il riepilogo giornaliero", variable=v_dg,
                        state="normal" if ok_cfg else "disabled").pack(anchor="w")
        fr_o = ttk.Frame(fr)
        fr_o.pack(anchor="w", pady=(6, 0))
        ttk.Label(fr_o, text="Dalle ore (HH:MM)").pack(side="left", padx=(0, 8))
        ttk.Entry(fr_o, textvariable=v_dg_ora, width=8).pack(side="left")

        def conferma_email(_e=None):
            try:
                ora = _normalizza_ora(v_dg_ora.get()) or "08:00"
            except ValueError:
                self.show_custom_warning("Ora non valida", "Scrivi ad esempio 8, 08:30 o 0830.")
                return
            dati["digest"] = {"attivo": bool(v_dg.get()), "ora": ora}
            salva()
            w.destroy()
        bt_w = ttk.Frame(fr)
        bt_w.pack(fill="x", pady=(12, 0))
        _lbl(bt_w, "Salva", conferma_email, "check").pack(side="left", padx=(0, 4))
        _lbl(bt_w, "Annulla", w.destroy, "chiudi").pack(side="right", padx=(4, 0))
        w.bind("<Escape>", lambda e: w.destroy())
        w.update_idletasks()
        ww, hh = w.winfo_reqwidth(), w.winfo_reqheight()
        x = popup.winfo_rootx() + (popup.winfo_width() - ww) // 2
        y = popup.winfo_rooty() + (popup.winfo_height() - hh) // 2
        w.geometry(f"+{max(x, 0)}+{max(y, 0)}")

    _lbl(piede, "Chiudi", chiudi, "chiudi").pack(side="right", padx=(6, 0))
    _lbl(piede, "Email", apri_email_cfg, "sync").pack(side="right", padx=6)
    _lbl(piede, "Fonti", apri_fonti, "filtri").pack(side="right", padx=6)
    _lbl(piede, "Esporta / Stampa", esporta, "carica").pack(side="right", padx=6)
    _lbl(piede, "Esporta .ics", esporta_ics, "carica").pack(side="right", padx=6)
    _lbl(piede, "Importa .ics", importa_ics, "archivia").pack(side="right", padx=6)

    def esc(_e=None):
        chiudi()
        return "break"

    popup.bind("<Escape>", esc)
    popup.bind("<Prior>", lambda e: cambia_mese(-1))
    popup.bind("<Next>", lambda e: cambia_mese(1))
    tree_g.bind("<Delete>", lambda e: elimina())
    tree_p.bind("<Delete>", lambda e: elimina())
    tree_g.bind("<Return>", lambda e: (modifica(), "break")[1])
    tree_p.bind("<Return>", lambda e: (modifica(), "break")[1])

    def muovi_sel(giorni):
        d = stato["sel"] + datetime.timedelta(days=giorni)
        stato["sel"] = d
        stato["anno"], stato["mese"] = d.year, d.month
        ridisegna()
        aggiorna_pannelli()
        return "break"

    def invio_calendario(_e=None):
        figli = tree_g.get_children()
        if figli:
            if not tree_g.selection():
                tree_g.selection_set(figli[0])
            modifica()
        else:
            apri_form(None, stato["sel"])
        return "break"

    cv.bind("<Left>", lambda e: muovi_sel(-1))
    cv.bind("<Right>", lambda e: muovi_sel(1))
    cv.bind("<Up>", lambda e: muovi_sel(-7))
    cv.bind("<Down>", lambda e: muovi_sel(7))
    cv.bind("<Return>", invio_calendario)
    cv.bind("<Home>", lambda e: (vai_oggi(), "break")[1])

    def esc_cerca(_e=None):
        if v_cerca.get():
            v_cerca.set("")
            return "break"
    e_cerca.bind("<Escape>", esc_cerca)

    self.update_idletasks()
    W, H = 1366, 630
    cx = self.winfo_rootx() + self.winfo_width() // 2 - W // 2
    cy = self.winfo_rooty() + self.winfo_height() // 2 - H // 2
    popup.geometry(f"{W}x{H}+{max(cx, 0)}+{max(cy, 0)}")
    popup.minsize(W, H)
    popup.deiconify()
    popup.update_idletasks()
    ridisegna()
    aggiorna_pannelli()
    cv.focus_set()
