#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import uuid
import time
import datetime
import tkinter as tk
from tkinter import ttk

from moduli.modello_spesa import (
    SpesaEntry, campo, METODI_PAGAMENTO_EMOJI, metodo_pagamento_pulito,
)

_MARCATORE = hasattr(SpesaEntry, "pool_ref")

TAG_POOL = "#communitypool"
TAG_RIENTRO  = "#rientro"
GIORNI_PICKER = 365
TUTTI = ""

STATI_LBL = {
    "proposta":  "⏳ In attesa",
    "confermata": "✔ Confermata",
    "rifiutata": "✖ Rifiutata",
    "annullata": "↩ Annullata",
}
STATI_SPESA = ["Aperta", "In attesa", "Chiusa"]

def _fmt_it(v, spec=",.2f"):
    s = format(v, spec)
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def _parse_importo(testo):
    s = str(testo or "").strip().replace("€", "").replace(" ", "")
    if not s:
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", s):
        s = s.replace(".", "")
    try:
        v = round(float(s), 2)
    except Exception:
        return None
    return v if v > 0 else None

def _num_f(s):
    s = str(s or "").strip().replace("€", "").replace(" ", "")
    if not s:
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None

def _data_libera(s):
    s = str(s or "").strip().replace("/", "-").replace(".", "-")
    if not s:
        return None
    try:
        return datetime.datetime.strptime(s, "%d-%m-%Y").date()
    except Exception:
        return None

def _data_it(iso):
    try:
        return datetime.date.fromisoformat(iso).strftime("%d/%m/%Y")
    except Exception:
        return iso or ""

def _mese_lbl(iso):
    return f"{iso[5:7]}/{iso[:4]}" if iso and len(iso) >= 7 else ""

def _safe(nome):
    return re.sub(r"[^\w\-]", "_", nome)

_RX_TAG_FS = re.compile(r"(?:PER|CNT|CTP)\u00b7")

def _e_fairshare(e):
    return bool(campo(e, "fairshare", None)) or bool(_RX_TAG_FS.search(e.descrizione or ""))

def _dir_pool():
    import __main__ as _app
    return _app.COMMUNITY_POOL_DIR


def _scrivi_json(percorso, dati):
    try:
        os.makedirs(os.path.dirname(percorso), exist_ok=True)
        with open(percorso, "w", encoding="utf-8") as f:
            json.dump(dati, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

def _leggi_config():
    percorso = os.path.join(_dir_pool(), "communitypool.json")
    try:
        with open(percorso, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def _salva_config(cfg):
    return _scrivi_json(os.path.join(_dir_pool(), "communitypool.json"), cfg)

def _carica_link():
    import __main__ as _app
    base = {"voci": {}, "fatti": {}, "riallinea": False, "pool_id": ""}
    try:
        with open(_app.COMMUNITY_POOL_LINK_FILE, "r", encoding="utf-8") as f:
            dati = json.load(f)
        base["voci"] = dati.get("voci", {})
        base["fatti"] = dati.get("fatti", {})
        base["riallinea"] = bool(dati.get("riallinea", False))
        base["pool_id"] = dati.get("pool_id", "") or ""
    except Exception:
        pass
    return base

def _salva_link(link):
    import __main__ as _app
    return _scrivi_json(_app.COMMUNITY_POOL_LINK_FILE, link)

def community_pool_segna_riallinea():
    import __main__ as _app
    try:
        if not os.path.isfile(_app.COMMUNITY_POOL_LINK_FILE):
            return
        link = _carica_link()
        link["riallinea"] = True
        _salva_link(link)
    except Exception:
        pass

def _allinea_pool_id(link):
    cfg = _leggi_config()
    if not isinstance(cfg, dict):
        return
    pid = cfg.get("pool_id")
    if not pid:
        pid = uuid.uuid4().hex
        cfg["pool_id"] = pid
        if not _salva_config(cfg):
            return
    if link.get("pool_id") != pid:
        if link.get("pool_id"):
            link["voci"] = {}
            link["fatti"] = {}
        link["pool_id"] = pid

def _scrivi_evento(profilo, tipo, **dati):
    ev = {
        "id": uuid.uuid4().hex[:12],
        "ts": datetime.datetime.now().isoformat(timespec="seconds"),
        "seq": time.time_ns(),
        "tipo": tipo,
        "profilo": profilo,
    }
    ev.update(dati)
    cartella = _dir_pool()
    os.makedirs(cartella, exist_ok=True)
    percorso = os.path.join(cartella, f"eventi_{_safe(profilo)}.jsonl")
    with open(percorso, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False) + "\n")
        f.flush()
    return ev

SUFFISSO_ELIMINATO = " (eliminato)"

def _base_nome(nome):
    if isinstance(nome, str) and nome.endswith(SUFFISSO_ELIMINATO):
        return nome[:-len(SUFFISSO_ELIMINATO)]
    return nome

def _file_eventi(profilo):
    return os.path.join(_dir_pool(), f"eventi_{_safe(profilo)}.jsonl")

def community_pool_elimina_profilo(nome):
    try:
        if not os.path.isfile(_file_eventi(nome)):
            return True
        _scrivi_evento(nome, "profilo_eliminato")
        return True
    except Exception:
        return False

def community_pool_rinomina_profilo(vecchio, nuovo):
    from moduli.profili import _percorso_db_profilo
    ok = True
    try:
        src = _file_eventi(vecchio)
        dst = _file_eventi(nuovo)
        if os.path.isfile(src):
            stesso = os.path.abspath(src) == os.path.abspath(dst)
            prima = []
            if not stesso and os.path.isfile(dst):
                with open(dst, "r", encoding="utf-8") as f:
                    prima = [r.strip() for r in f if r.strip()]
            righe = []
            with open(src, "r", encoding="utf-8") as f:
                for riga in f:
                    riga = riga.strip()
                    if not riga:
                        continue
                    try:
                        ev = json.loads(riga)
                        if isinstance(ev, dict) and ev.get("profilo") == vecchio:
                            ev["profilo"] = nuovo
                            riga = json.dumps(ev, ensure_ascii=False)
                    except Exception:
                        pass
                    righe.append(riga)
            tmp = dst + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                f.write("\n".join(prima + righe) + "\n")
            os.replace(tmp, dst)
            if not stesso:
                os.remove(src)
    except Exception:
        ok = False
    try:
        pv = os.path.join(_percorso_db_profilo(nuovo), "communitypool_visto.json")
        if os.path.isfile(pv):
            with open(pv, "r", encoding="utf-8") as f:
                dati = json.load(f)
            if vecchio in dati:
                dati[nuovo] = dati.pop(vecchio)
                if not _scrivi_json(pv, dati):
                    ok = False
    except Exception:
        ok = False
    return ok

def _evento_valido(ev):
    """Scarta gli eventi malformati (campi mancanti o importo non numerico)."""
    try:
        if not (isinstance(ev, dict) and ev.get("id") and ev.get("tipo") and ev.get("profilo")):
            return False
        t = ev["tipo"]
        if t in ("spesa_pubblicata", "spesa_aggiornata", "spesa_ritirata", "spesa_chiusa", "spesa_riaperta") and not ev.get("id_fam"):
            return False
        if t in ("quota_proposta", "quota_confermata", "quota_rifiutata", "quota_annullata") and not ev.get("id_contrib") and not ev.get("id_fam"):
            return False
        if t == "quota_proposta" and not (ev.get("id_contrib") and ev.get("id_fam")):
            return False
        if "importo" in ev:
            v = float(ev["importo"])
            if v != v or v in (float("inf"), float("-inf")):
                return False
        if "hashtag" in ev and not isinstance(ev["hashtag"], (list, tuple, type(None))):
            return False
        return True
    except Exception:
        return False

def _chiave_evento(e):
    try:
        seq = int(e.get("seq", 0))
    except Exception:
        seq = 0
    return (e.get("ts", ""), seq, e["id"])

def _leggi_eventi():
    cartella = _dir_pool()
    visti = {}
    if os.path.isdir(cartella):
        for nome in os.listdir(cartella):
            if not (nome.startswith("eventi_") and nome.endswith(".jsonl")):
                continue
            try:
                with open(os.path.join(cartella, nome), "r", encoding="utf-8") as f:
                    for riga in f:
                        riga = riga.strip()
                        if not riga:
                            continue
                        try:
                            ev = json.loads(riga)
                        except Exception:
                            continue
                        if _evento_valido(ev):
                            visti[ev["id"]] = ev
            except Exception:
                continue
    return sorted(visti.values(), key=_chiave_evento)

def _costruisci_stato(eventi):
    spese = {}
    contributi = {}
    for ev in eventi:
        t = ev["tipo"]
        if t == "spesa_pubblicata":
            spese[ev["id_fam"]] = {
                "id_fam": ev["id_fam"], "id_spesa": ev.get("id_spesa", ""),
                "data": ev.get("data", ""), "categoria": ev.get("categoria", ""),
                "descrizione": ev.get("descrizione", ""),
                "importo": round(float(ev.get("importo", 0.0)), 2),
                "ora": ev.get("ora", ""), "metodo": ev.get("metodo", ""),
                "hashtag": list(ev.get("hashtag", []) or []),
                "pagante": ev["profilo"], "ritirata": False, "chiusa": False, "contributi": [],
                "ts": ev.get("ts", ""),
            }
        elif t == "quota_proposta":
            imp = round(float(ev.get("importo", 0.0)), 2)
            contributi[ev["id_contrib"]] = {
                "id_contrib": ev["id_contrib"], "id_fam": ev.get("id_fam", ""),
                "profilo": ev["profilo"], "proposta": imp, "importo": imp,
                "stato": "proposta", "nota": ev.get("nota", ""),
                "categoria_membro": ev.get("categoria_membro", ""),
                "data_conferma": "", "nota_risposta": "", "ts": ev.get("ts", ""),
            }
    for ev in eventi:
        t = ev["tipo"]
        if t == "profilo_eliminato":
            p = ev["profilo"]
            lim = ev.get("ts", "")
            etichetta = p + SUFFISSO_ELIMINATO
            for c in contributi.values():
                s = spese.get(c["id_fam"])
                mia = c["profilo"] == p and c["ts"] <= lim
                su_mia = bool(s) and s["pagante"] == p and s["ts"] <= lim
                if c["stato"] == "proposta" and (mia or su_mia):
                    c["stato"] = "annullata"
                if mia:
                    c["profilo"] = etichetta
            for s in spese.values():
                if s["pagante"] == p and s["ts"] <= lim:
                    s["chiusa"] = True
                    s["pagante"] = etichetta
            continue
        if t == "spesa_ritirata":
            s = spese.get(ev.get("id_fam"))
            if s and s["pagante"] == ev["profilo"]:
                s["ritirata"] = True
            continue
        if t in ("spesa_chiusa", "spesa_riaperta"):
            s = spese.get(ev.get("id_fam"))
            if s and s["pagante"] == ev["profilo"]:
                s["chiusa"] = (t == "spesa_chiusa")
            continue
        if t == "spesa_aggiornata":
            s = spese.get(ev.get("id_fam"))
            if s and s["pagante"] == ev["profilo"]:
                if "importo" in ev:
                    s["importo"] = round(float(ev["importo"]), 2)
                for k in ("data", "categoria", "descrizione"):
                    if k in ev:
                        s[k] = ev[k]
            continue
        if t not in ("quota_confermata", "quota_rifiutata", "quota_annullata"):
            continue
        c = contributi.get(ev.get("id_contrib"))
        if not c or c["stato"] != "proposta":
            continue
        s = spese.get(c["id_fam"])
        if t == "quota_annullata" and ev["profilo"] == c["profilo"]:
            c["stato"] = "annullata"
        elif t == "quota_confermata" and s and ev["profilo"] == s["pagante"]:
            c["stato"] = "confermata"
            c["importo"] = round(float(ev.get("importo", c["proposta"])), 2)
            c["data_conferma"] = ev.get("ts", "")[:10]
        elif t == "quota_rifiutata" and s and ev["profilo"] == s["pagante"]:
            c["stato"] = "rifiutata"
            c["nota_risposta"] = ev.get("nota", "")
    for c in contributi.values():
        s = spese.get(c["id_fam"])
        if s:
            s["contributi"].append(c)
    return spese, contributi

def _coperto(s):
    return round(sum(c["importo"] for c in s["contributi"] if c["stato"] == "confermata"), 2)

def _stato_spesa(s):
    if s["chiusa"] or round(s["importo"] - _coperto(s), 2) <= 0:
        return "Chiusa"
    if any(c["stato"] == "proposta" for c in s["contributi"]):
        return "In attesa"
    return "Aperta"

def _trova_voce(self, id_spesa):
    if not id_spesa:
        return None, None
    for d, lista in self.spese.items():
        for e in lista:
            if campo(e, "id_spesa", None) == id_spesa:
                return d, e
    return None, None

def _invalida_cache_tag(self):
    if hasattr(self, '_cache_tutti_tag'):
        del self._cache_tutti_tag

def _materializza_quota(self, s, c, link, per_ref):
    chiave = f"{c['id_contrib']}:quota"
    if chiave in link["fatti"]:
        return False
    vid = per_ref.get(chiave)
    if vid:
        link["fatti"][chiave] = vid
        link["voci"][vid] = {"ruolo": "quota", "id_fam": c["id_fam"],
                             "id_contrib": c["id_contrib"], "origine": s["id_spesa"]}
        return False
    cat = c.get("categoria_membro") or s["categoria"]
    if cat not in self.categorie:
        cat = s["categoria"] if s["categoria"] in self.categorie else "Generica"
    try:
        data = datetime.date.fromisoformat(s["data"])
    except Exception:
        data = datetime.date.today()
    voce = SpesaEntry.nuova(cat, f"Quota: {s['descrizione']}", c["importo"], "Uscita",
                            hashtag=[TAG_POOL])
    if _MARCATORE:
        voce.pool_ref = chiave
        per_ref[chiave] = voce.id_spesa
    self.spese.setdefault(data, []).append(voce)
    link["fatti"][chiave] = voce.id_spesa
    link["voci"][voce.id_spesa] = {"ruolo": "quota", "id_fam": c["id_fam"],
                                   "id_contrib": c["id_contrib"], "origine": s["id_spesa"]}
    _invalida_cache_tag(self)
    return True

def _materializza_rientro(self, s, c, link, etichetta, per_ref):
    chiave = f"{c['id_contrib']}:rientro"
    if chiave in link["fatti"]:
        return False
    vid = per_ref.get(chiave)
    if vid:
        link["fatti"][chiave] = vid
        link["voci"][vid] = {"ruolo": "rientro", "id_fam": c["id_fam"],
                             "id_contrib": c["id_contrib"], "origine": s["id_spesa"]}
        return False
    _d0, e0 = _trova_voce(self, s["id_spesa"])
    cat = campo(e0, "categoria", "") if e0 is not None else s["categoria"]
    conto = campo(e0, "conto", "") if e0 is not None else ""
    try:
        data = datetime.date.fromisoformat(s["data"])
    except Exception:
        data = datetime.date.today()
    voce = SpesaEntry.nuova(cat or s["categoria"], f"Rientro: {s['descrizione']} ({etichetta})",
                            c["importo"], "Entrata", conto=conto,
                            hashtag=[TAG_POOL, TAG_RIENTRO])
    if _MARCATORE:
        voce.pool_ref = chiave
        per_ref[chiave] = voce.id_spesa
    self.spese.setdefault(data, []).append(voce)
    link["fatti"][chiave] = voce.id_spesa
    link["voci"][voce.id_spesa] = {"ruolo": "rientro", "id_fam": c["id_fam"],
                                   "id_contrib": c["id_contrib"], "origine": s["id_spesa"]}
    _invalida_cache_tag(self)
    return True

def _riallinea_pubblicate(me, spese, link, voci_loc, data_loc):
    ritirate = chiuse = aggiornate = 0
    for vid, info in list(link["voci"].items()):
        if info.get("ruolo") != "origine":
            continue
        s = spese.get(info.get("id_fam"))
        if not s or s["pagante"] != me or s["ritirata"]:
            continue
        try:
            e = voci_loc.get(vid)
            if e is None:
                if _coperto(s) > 0:
                    if not s["chiusa"]:
                        for c in s["contributi"]:
                            if c["stato"] == "proposta":
                                _scrivi_evento(me, "quota_rifiutata", id_contrib=c["id_contrib"],
                                               nota="Spesa cancellata dal pagante")
                        _scrivi_evento(me, "spesa_chiusa", id_fam=s["id_fam"])
                        chiuse += 1
                else:
                    _scrivi_evento(me, "spesa_ritirata", id_fam=s["id_fam"])
                    ritirate += 1
                link["voci"].pop(vid, None)
                continue
            d = data_loc.get(vid)
            nuovi = {"importo": round(float(e.importo), 2),
                     "data": d.isoformat() if d else s["data"],
                     "categoria": e.categoria, "descrizione": e.descrizione}
            if any(nuovi[k] != s[k] for k in nuovi):
                _scrivi_evento(me, "spesa_aggiornata", id_fam=s["id_fam"], **nuovi)
                aggiornate += 1
        except Exception:
            continue
    return ritirate, chiuse, aggiornate

def community_pool_sync(self, silenzioso=True):
    import __main__ as _app
    from moduli.profili import _etichetta_profilo
    if not os.path.isdir(_dir_pool()):
        return 0
    me = _app.PROFILO_ATTIVO
    spese, contributi = _costruisci_stato(_leggi_eventi())
    link = _carica_link()
    snap = json.dumps(link, sort_keys=True)
    voci_loc = {e.id_spesa: e for lista in self.spese.values() for e in lista if isinstance(e, SpesaEntry)}
    data_loc = {e.id_spesa: d for d, lista in self.spese.items() for e in lista if isinstance(e, SpesaEntry)}
    db_mod = False
    if _MARCATORE:
        for vid, info in link["voci"].items():
            e = voci_loc.get(vid)
            if e is not None and info.get("ruolo") in ("quota", "rientro") and not e.pool_ref:
                e.pool_ref = f"{info.get('id_contrib', '')}:{info['ruolo']}"
                db_mod = True
    _allinea_pool_id(link)
    n_rit = n_chi = n_agg = 0
    if voci_loc:
        n_rit, n_chi, n_agg = _riallinea_pubblicate(me, spese, link, voci_loc, data_loc)
        if n_rit or n_chi or n_agg:
            spese, contributi = _costruisci_stato(_leggi_eventi())
    if link.get("riallinea"):
        for k, vid in list(link["fatti"].items()):
            if vid not in voci_loc:
                del link["fatti"][k]
        for vid in list(link["voci"]):
            if vid not in voci_loc:
                del link["voci"][vid]
        link["riallinea"] = False
    per_ref = {e.pool_ref: vid for vid, e in voci_loc.items() if _MARCATORE and e.pool_ref}
    nuove_quote = 0
    nuovi_rientri = 0
    for c in contributi.values():
        if c["stato"] != "confermata":
            continue
        s = spese.get(c["id_fam"])
        if not s:
            continue
        if c["profilo"] == me and _materializza_quota(self, s, c, link, per_ref):
            nuove_quote += 1
        if s["pagante"] == me and _materializza_rientro(self, s, c, link, _etichetta_profilo(self, c["profilo"]), per_ref):
            nuovi_rientri += 1
    totale = nuove_quote + nuovi_rientri
    if totale or db_mod:
        self.save_db()
    if totale or db_mod or json.dumps(link, sort_keys=True) != snap:
        _salva_link(link)
    if totale:
        self.refresh_gui()
        if not silenzioso or nuove_quote:
            self.show_toast(f"CommunityPool: {nuove_quote} quote e {nuovi_rientri} rientri registrati")
    if n_rit or n_chi:
        self.show_toast(f"CommunityPool: {n_rit} spese ritirate e {n_chi} chiuse perché cancellate dal database")
    return totale

def _passa_filtri(spec, rec):
    if not spec:
        return True
    for k in ("pagante", "stato", "categoria", "mese", "conto", "metodo"):
        v = spec.get(k, "")
        if v and rec.get(k, "") != v:
            return False
    tag = spec.get("tag")
    if tag and not all(t in rec.get("hashtag", "").lower() for t in tag):
        return False
    testo = spec.get("testo")
    if testo and testo not in rec.get("descrizione", "").lower():
        return False
    imp = rec.get("importo")
    if imp is not None:
        if spec.get("imp_da") is not None and imp < spec["imp_da"]:
            return False
        if spec.get("imp_a") is not None and imp > spec["imp_a"]:
            return False
    d = rec.get("data")
    if d is not None:
        if spec.get("da") and d < spec["da"]:
            return False
        if spec.get("a") and d > spec["a"]:
            return False
    return True

def _pannello_filtri(self, finestra, bg, righe, su_cambio, prima_di):
    campi = [c for r in righe for c in r]
    f = {c[0]: tk.StringVar(value="") for c in campi}
    etichette = {c[0]: c[2].rstrip(":") for c in campi}
    st = {"aperta": False, "sosp": False, "job": None}
    combo = {}
    date_entry = {}

    head = tk.Frame(finestra, bg=bg)
    head.pack(fill="x", padx=10, pady=(0, 2))
    lbl_freccia = tk.Label(head, bg=bg, fg="#DC3545", cursor="hand2", font=("Arial", 11, "bold"), width=2)
    lbl_freccia.pack(side="left")
    lbl_head = tk.Label(head, bg=bg, fg=self.TEXT_COLOR, cursor="hand2", font=("Arial", 9, "bold"), anchor="w")
    lbl_head.pack(side="left")
    body = tk.Frame(finestra, bg=bg)

    def _cal_btn(riga, entry, var):
        def apri(_e=None):
            self.mostra_calendario_popup(entry, var)
            try:
                pc = getattr(self, "popup_calendario", None)
                if pc is not None and pc.winfo_exists():
                    pc.attributes("-topmost", True)
                    pc.lift()
            except tk.TclError:
                pass
        img = self.icone_gui.get("calendario")
        b = tk.Label(riga, image=img, bg=bg, cursor="hand2", padx=2)
        if img is None:
            b.config(text="📅")
        else:
            b.image = img
        b.pack(side="left", padx=(2, 0))
        b.bind("<Button-1>", apri)

    for r in righe:
        riga = tk.Frame(body, bg=bg)
        riga.pack(fill="x", pady=2, padx=10)
        for i, (chiave, tipo, etich, valori, w) in enumerate(r):
            tk.Label(riga, text=etich, bg=bg, fg=self.TEXT_COLOR).pack(side="left", padx=(4 if i == 0 else 10, 4))
            if tipo == "combo":
                cb = ttk.Combobox(riga, values=valori or [], textvariable=f[chiave],
                                  style="Border.TCombobox", state="readonly", width=w)
                cb.pack(side="left")
                combo[chiave] = cb
            else:
                e = ttk.Entry(riga, textvariable=f[chiave], width=w)
                e.pack(side="left")
                if tipo == "data":
                    date_entry[chiave] = e
                    _cal_btn(riga, e, f[chiave])
        if any(c[1] == "data" for c in r):
            tk.Label(riga, text="(GG-MM-AAAA)", bg=bg, fg="gray", font=("Arial", 8, "italic")).pack(side="left", padx=(4, 0))

    def spec():
        out = {k: v.get().strip() for k, v in f.items()}
        if "tag" in out:
            out["tag"] = [t.lstrip("#").lower() for t in re.split(r"[\s,;]+", out["tag"]) if t.lstrip("#")]
        if "testo" in out:
            out["testo"] = out["testo"].lower()
        for k in ("imp_da", "imp_a"):
            if k in out:
                out[k] = _num_f(out[k])
        for k in ("da", "a"):
            if k in out:
                out[k] = _data_libera(out[k])
        attivo = any((v is not None and v != "" and v != []) for v in out.values())
        return out if attivo else None

    def descr(sp):
        out = []
        for k, v in sp.items():
            if v is None or v == "" or v == []:
                continue
            if k == "tag":
                out.append(" ".join(f"#{t}" for t in v))
            elif isinstance(v, datetime.date):
                out.append(f"{etichette[k]} {v.strftime('%d-%m-%Y')}")
            elif isinstance(v, float):
                out.append(f"{etichette[k]} {_fmt_it(v)}")
            else:
                out.append(f"{etichette[k]} {v}")
        return out

    def aggiorna_testata():
        sp = spec()
        txt = ("filtri attivi: " + ", ".join(descr(sp))) if sp else "nessun filtro attivo"
        lbl_freccia.config(text="▾" if st["aperta"] else "▸")
        lbl_head.config(text=f"Filtri avanzati  ({txt})",
                        fg=getattr(self, "COLOR_HIGHLIGHT", self.TEXT_COLOR) if sp else self.TEXT_COLOR)

    def applica(*_):
        if st["sosp"]:
            return
        st["job"] = None
        try:
            if not finestra.winfo_exists():
                return
        except tk.TclError:
            return
        for k, e in date_entry.items():
            sbagliata = bool(f[k].get().strip()) and _data_libera(f[k].get()) is None
            try:
                e.configure(foreground="#DC3545" if sbagliata else self.TEXT_COLOR)
            except tk.TclError:
                pass
        aggiorna_testata()
        su_cambio()

    def rinvia(*_):
        if st["job"]:
            finestra.after_cancel(st["job"])
        st["job"] = finestra.after(400, applica)

    def reset():
        st["sosp"] = True
        try:
            for v in f.values():
                v.set("")
        finally:
            st["sosp"] = False
        applica()

    def apri_chiudi(*_):
        st["aperta"] = not st["aperta"]
        if st["aperta"]:
            body.pack(fill="x", before=prima_di())
        else:
            body.pack_forget()
        aggiorna_testata()

    for chiave, tipo, *_resto in campi:
        f[chiave].trace_add("write", applica if tipo == "combo" else rinvia)
    for w in (lbl_freccia, lbl_head):
        w.bind("<Button-1>", apri_chiudi)
    aggiorna_testata()
    return {"spec": spec, "reset": reset, "combo": combo, "f": f, "rinvia": rinvia}


def _file_visto():
    import __main__ as _app
    return os.path.join(os.path.dirname(_app.COMMUNITY_POOL_LINK_FILE), "communitypool_visto.json")

def _leggi_visto(me):
    try:
        with open(_file_visto(), "r", encoding="utf-8") as f:
            return json.load(f).get(me, "")
    except Exception:
        return ""

def _segna_visto(me):
    try:
        with open(_file_visto(), "r", encoding="utf-8") as f:
            dati = json.load(f)
    except Exception:
        dati = {}
    dati[me] = datetime.datetime.now().isoformat(timespec="seconds")
    _scrivi_json(_file_visto(), dati)

def _conta_novita(me):
    visto = _leggi_visto(me)
    eventi = _leggi_eventi()
    spese, contributi = _costruisci_stato(eventi)
    n_sp = n_q = n_es = 0
    for ev in eventi:
        if ev.get("ts", "") <= visto or ev["profilo"] == me:
            continue
        t = ev["tipo"]
        if t == "spesa_pubblicata":
            s = spese.get(ev.get("id_fam"))
            if s and not s["ritirata"] and not s["chiusa"]:
                n_sp += 1
        elif t == "quota_proposta":
            c = contributi.get(ev.get("id_contrib"))
            s = spese.get(c["id_fam"]) if c else None
            if c and s and s["pagante"] == me and c["stato"] == "proposta" and not s["ritirata"]:
                n_q += 1
        elif t in ("quota_confermata", "quota_rifiutata"):
            c = contributi.get(ev.get("id_contrib"))
            if c and c["profilo"] == me:
                n_es += 1
    return n_sp, n_q, n_es

def _form_in_uso(self):
    try:
        if getattr(self, "modifica_idx", None):
            return True
        for nome in ("desc_entry", "imp_entry"):
            w = getattr(self, nome, None)
            if w is not None and w.get().strip():
                return True
    except Exception:
        pass
    return False

def _aggiorna_badge_pool(self, n):
    try:
        self._pool_novita_pendenti = n
        from moduli.messaggi_servizio import _aggiorna_badge_messaggi_servizio
        _aggiorna_badge_messaggi_servizio(self)
    except Exception:
        pass

def community_pool_controlla_novita(self):
    import __main__ as _app
    try:
        self.after(5 * 60 * 1000, lambda: community_pool_controlla_novita(self))
    except Exception:
        return
    try:
        if not os.path.isdir(_dir_pool()):
            return
        win = getattr(self, "_win_community_pool", None)
        if win is not None and win.winfo_exists():
            return
        if not _form_in_uso(self):
            community_pool_sync(self, silenzioso=True)
        n_sp, n_q, n_es = _conta_novita(_app.PROFILO_ATTIVO)
        tot = n_sp + n_q + n_es
        _aggiorna_badge_pool(self, tot)
        if tot > getattr(self, "_pool_novita_notificate", 0):
            parti = []
            if n_sp:
                parti.append(f"{n_sp} nuova spesa" if n_sp == 1 else f"{n_sp} nuove spese")
            if n_q:
                parti.append(f"{n_q} quota da confermare" if n_q == 1 else f"{n_q} quote da confermare")
            if n_es:
                parti.append(f"{n_es} esito su tue proposte" if n_es == 1 else f"{n_es} esiti su tue proposte")
            from moduli.messaggi_servizio import mostra_toast_cliccabile
            mostra_toast_cliccabile(self, "CommunityPool: " + ", ".join(parti) + "\n\nClicca qui (o sull'icona lampeggiante in alto a sinistra) per aprire", self.apri_community_pool, 8000)
        self._pool_novita_notificate = tot
    except Exception:
        pass

def apri_community_pool(self):
    import __main__ as _app
    from moduli.profili import elenco_profili, _etichetta_profilo

    if hasattr(self, '_win_community_pool') and self._win_community_pool and \
            self._win_community_pool.winfo_exists():
        self._win_community_pool.lift()
        self._win_community_pool.focus_force()
        return

    me = _app.PROFILO_ATTIVO

    if len(elenco_profili(self)) < 2:
        self.show_custom_warning(
            "CommunityPool",
            "Per attivare il CommunityPool servono almeno due profili.\n"
            "Crea un altro profilo e riprova.")
        return

    if _leggi_config() is None:
        if not self.show_custom_askyesno("CommunityPool",
                                         "Nessun CommunityPool trovato.\nCrearlo con questo profilo?"):
            return
        cfg = {"creato_da": me, "creato": datetime.date.today().isoformat(), "pool_id": uuid.uuid4().hex}
        if not _salva_config(cfg):
            self.show_toast("Errore: impossibile creare il CommunityPool")
            return
    community_pool_sync(self, silenzioso=True)
    _aggiorna_badge_pool(self, 0)

    def et(nome):
        return _etichetta_profilo(self, nome)

    stato = {"spese": {}, "contributi": {}, "eventi": [], "voci_loc": {}}

    nov_sp, nov_q, nov_es = _conta_novita(me)

    win = tk.Toplevel(self)
    self._win_community_pool = win
    win.transient(self)
    win.withdraw()
    win.title(f"CommunityPool — {et(me)}")
    win.configure(bg=self.COLOR_BACKGROUND)
    w_win, h_win = 1300, 620
    self.update_idletasks()
    pos_x = self.winfo_rootx() + (self.winfo_width() // 2) - (w_win // 2)
    pos_y = self.winfo_rooty() + (self.winfo_height() // 2) - (h_win // 2)
    win.geometry(f"{w_win}x{h_win}+{max(0, pos_x)}+{max(0, pos_y)}")
    win.minsize(w_win, h_win)
    win.bind("<Escape>", lambda e: win.destroy())
    win.deiconify()

    bg = self.COLOR_BACKGROUND
    fg = self.TEXT_COLOR

    def _btn(parent, ico, testo, cmd, side="left", padx=6):
        img = self.icone_gui.get(ico)
        b = tk.Label(parent, image=img, text=f" {testo}", compound="left",
                     bg=bg, fg=fg, cursor="hand2", font=("Arial", 9, "bold"))
        if img:
            b.image = img
        b.pack(side=side, padx=padx, pady=4)
        b.bind("<Button-1>", lambda e: cmd())
        return b

    bar_bottom = tk.Frame(win, bg=bg)
    bar_bottom.pack(fill="x", side="bottom", pady=(4, 8))
    bar_bottom_in = tk.Frame(bar_bottom, bg=bg)
    bar_bottom_in.pack()
    _btn(bar_bottom_in, "salva", "Esporta", lambda: esporta(), padx=15)
    _btn(bar_bottom_in, "chiudi", "Chiudi", win.destroy, padx=15)

    top = tk.Frame(win, bg=bg)
    top.pack(fill="x", padx=10, pady=(8, 4))
    tk.Label(top, image=self.icone_gui.get("search"), text=" Ricerca:", compound="left",
             bg=bg, fg=fg, font=("Arial", 9, "bold")).pack(side="left")
    var_cerca = tk.StringVar()
    campo_input = ttk.Entry(top, textvariable=var_cerca, width=22)
    campo_input.pack(side="left", padx=8)
    var_nascondi = tk.BooleanVar(value=True)
    ttk.Checkbutton(top, text="Nascondi chiuse", variable=var_nascondi,
                    command=lambda: ricarica()).pack(side="left", padx=(0, 8))
    lbl_info = tk.Label(top, bg=bg, fg=fg, font=("Arial", 9, "bold"), anchor="e")
    lbl_info.pack(side="right")

    pann = _pannello_filtri(
        self, win, bg,
        [[("pagante", "combo", "Pagante:", [TUTTI], 18),
          ("stato", "combo", "Stato:", [TUTTI] + STATI_SPESA, 11),
          ("categoria", "combo", "Categoria:", [TUTTI], 18),
          ("mese", "combo", "Mese:", [TUTTI], 9)],
         [("tag", "entry", "Hashtag:", None, 14),
          ("testo", "entry", "Descrizione contiene:", None, 20),
          ("imp_da", "entry", "Importo da:", None, 9),
          ("imp_a", "entry", "a:", None, 9),
          ("da", "data", "Dal:", None, 11),
          ("a", "data", "Al:", None, 11)]],
        su_cambio=lambda: ricarica(), prima_di=lambda: nb)
    job_cerca = {"id": None}

    def _rinvia_cerca(*_):
        if job_cerca["id"]:
            win.after_cancel(job_cerca["id"])
        job_cerca["id"] = win.after(400, lambda: ricarica())
    var_cerca.trace_add("write", _rinvia_cerca)

    nb = ttk.Notebook(win)
    nb.pack(fill="both", expand=True, padx=10, pady=6)

    def _tree(parent, colonne, larghezze, altezza=14, tooltip_desc=None):
        fr = tk.Frame(parent, bg=bg)
        fr.pack(fill="both", expand=True)
        tv = ttk.Treeview(fr, columns=[c for c, _ in colonne], show="headings",
                          selectmode="browse", height=altezza)
        for (cid, testo), w in zip(colonne, larghezze):
            anchor = "e" if cid in ("tot", "cop", "res", "mia", "imp", "prop", "ant", "ric", "ver") else "w"
            tv.heading(cid, text=testo,
                       command=lambda _c=cid, _tv=tv: self.treeview_sort_column(_tv, _c, False))
            tv.column(cid, width=w, anchor=anchor,
                      stretch=(cid in ("desc", "evento", "nota")))
        sb = ttk.Scrollbar(fr, orient="vertical", command=tv.yview, style="Vertical.TScrollbar")
        tv.configure(yscrollcommand=sb.set)
        tv.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        tv._metodo_lookup = {}
        if tooltip_desc is not None:
            self._bind_tooltip_metodo(tv, col_desc=tooltip_desc)
        return tv

    def _barra(parent):
        fr = tk.Frame(parent, bg=bg)
        fr.pack(fill="x", pady=(6, 0))
        return fr

    tab_pan = tk.Frame(nb, bg=bg)
    tab_conf = tk.Frame(nb, bg=bg)
    tab_mie = tk.Frame(nb, bg=bg)
    tab_saldi = tk.Frame(nb, bg=bg)
    tab_storico = tk.Frame(nb, bg=bg)

    def _add_tab(frame, ico_key, testo):
        img = self.icone_gui.get(ico_key)
        if img:
            nb.add(frame, image=img, text=f"  {testo}  ", compound="left")
        else:
            nb.add(frame, text=testo)
    _add_tab(tab_pan, "report", "Panoramica")
    _add_tab(tab_conf, "utenti", "Da confermare")
    _add_tab(tab_mie, "saldo", "Le mie quote")
    _add_tab(tab_saldi, "grafico_linea", "Saldi")
    _add_tab(tab_storico, "calendario", "Storico")

    tv_pan = _tree(tab_pan,
                   [("data", "Data"), ("cat", "Categoria"), ("desc", "Descrizione"), ("pag", "Pagante"),
                    ("tot", "Totale €"), ("cop", "Coperto €"), ("res", "Residuo €"), ("mia", "Mia quota €"),
                    ("stato", "Stato"), ("conto", "Conto"), ("ora", "Ora"), ("tag", "Hashtag"),
                    ("met", "Metodo")],
                   [80, 100, 190, 90, 80, 80, 80, 95, 85, 90, 50, 110, 90], tooltip_desc=2)
    tv_pan.tag_configure("chiusa", foreground="#888888")
    tv_pan.tag_configure("attesa", foreground="#E5C07B")
    bar_pan = _barra(tab_pan)
    tv_conf = _tree(tab_conf,
                    [("data", "Data spesa"), ("mem", "Membro"), ("desc", "Spesa"), ("tot", "Totale €"),
                     ("prop", "Proposta €"), ("nota", "Nota")],
                    [90, 140, 280, 90, 100, 300])
    bar_conf = _barra(tab_conf)
    tv_mie = _tree(tab_mie,
                   [("data", "Data spesa"), ("desc", "Spesa"), ("pag", "Pagante"), ("prop", "Proposta €"),
                    ("imp", "Confermata €"), ("stato", "Stato"), ("nota", "Nota")],
                   [90, 260, 130, 100, 100, 120, 260])
    bar_mie = _barra(tab_mie)
    lbl_tot_saldi = tk.Label(tab_saldi, text="", bg=bg, fg=fg, anchor="w",
                             font=("Arial", 10, "bold"))
    lbl_tot_saldi.pack(side="bottom", fill="x", padx=10, pady=(6, 6))
    tk.Label(tab_saldi, text="I saldi usano solo i filtri Mese, Dal, Al e l'opzione \"Nascondi chiuse\"",
             bg=bg, fg="gray", font=("Arial", 8, "italic"), anchor="w").pack(side="top", fill="x", padx=10, pady=(4, 0))
    tv_saldi = _tree(tab_saldi,
                     [("mem", "Membro"), ("ant", "Spese anticipate €"), ("ric", "Quote ricevute €"),
                      ("res", "Residuo a suo carico €"), ("ver", "Quote versate ad altri €")],
                     [220, 170, 170, 190, 190])
    tv_storico = _tree(tab_storico, [("quando", "Quando"), ("evento", "Evento")], [150, 800])

    def _selezione(tv):
        sel = tv.selection()
        return sel[0] if sel else None

    def _info(s):
        e = stato["voci_loc"].get(s["id_spesa"])
        conto = ""
        if e is not None:
            try:
                conto = self._conto_effettivo(e) or ""
            except Exception:
                conto = campo(e, "conto", "") or ""
        ora = s["ora"] or (campo(e, "ora", "") if e is not None else "")
        metodo = s["metodo"] or (campo(e, "metodo_pagamento", "") if e is not None else "")
        tags = list(s["hashtag"])
        if not tags and e is not None:
            tags = [t for t in (campo(e, "hashtag", []) or []) if t not in (TAG_POOL, TAG_RIENTRO)]
        return {"conto": conto, "ora": ora, "metodo": metodo, "hashtag": " ".join(tags or [])}

    def _record(s):
        info = _info(s)
        try:
            d = datetime.date.fromisoformat(s["data"])
        except Exception:
            d = None
        return {"pagante": et(s["pagante"]), "stato": _stato_spesa(s), "categoria": s["categoria"],
                "mese": _mese_lbl(s["data"]), "conto": info["conto"], "metodo": info["metodo"],
                "hashtag": info["hashtag"], "descrizione": s["descrizione"],
                "importo": s["importo"], "data": d}, info

    def _spese_periodo(spec):
        sp = {k: spec[k] for k in ("mese", "da", "a") if spec and k in spec} if spec else None
        lista = []
        for s in stato["spese"].values():
            if s["ritirata"]:
                continue
            rec, _ = _record(s)
            if _passa_filtri(sp, rec):
                lista.append(s)
        return sorted(lista, key=lambda s: s["data"], reverse=True)

    def ricarica(*_):
        eventi = _leggi_eventi()
        stato["eventi"] = eventi
        stato["spese"], stato["contributi"] = _costruisci_stato(eventi)
        ids = {s["id_spesa"] for s in stato["spese"].values() if s["id_spesa"]}
        voci_loc = {}
        if ids:
            for lista_v in self.spese.values():
                for e in lista_v:
                    sid = campo(e, "id_spesa", None)
                    if sid in ids:
                        voci_loc[sid] = e
        stato["voci_loc"] = voci_loc
        lbl_info.config(text=f"Profilo attivo: {et(me)}")

        attive = [s for s in stato["spese"].values() if not s["ritirata"]]
        mesi = sorted({_mese_lbl(s["data"]) for s in attive}, key=lambda m: (m[3:], m[:2]), reverse=True)
        pann["combo"]["mese"]["values"] = [TUTTI] + mesi
        pann["combo"]["pagante"]["values"] = [TUTTI] + sorted({et(s["pagante"]) for s in attive}, key=str.lower)
        pann["combo"]["categoria"]["values"] = [TUTTI] + sorted({s["categoria"] for s in attive}, key=str.lower)

        for tv in (tv_pan, tv_conf, tv_mie, tv_saldi, tv_storico):
            tv.delete(*tv.get_children())
        tv_pan._metodo_lookup.clear()

        spec = pann["spec"]()
        parola = var_cerca.get().strip().lower()
        lista = _spese_periodo(spec)
        for s in sorted(attive, key=lambda x: x["data"], reverse=True):
            rec, info = _record(s)
            if not _passa_filtri(spec, rec):
                continue
            if var_nascondi.get() and rec["stato"] == "Chiusa" and not (spec and spec.get("stato") == "Chiusa"):
                continue
            cop = _coperto(s)
            if parola and not any(parola in str(x).lower() for x in (
                    rec["categoria"], rec["descrizione"], rec["pagante"], rec["stato"],
                    _fmt_it(s["importo"]), rec["conto"], rec["metodo"], rec["hashtag"])):
                continue
            mie = [c for c in s["contributi"] if c["profilo"] == me]
            conf_mia = round(sum(c["importo"] for c in mie if c["stato"] == "confermata"), 2)
            testo_mia = _fmt_it(conf_mia) if conf_mia else ""
            if any(c["stato"] == "proposta" for c in mie):
                testo_mia = (testo_mia + " ⏳").strip()
            tag_r = "chiusa" if rec["stato"] == "Chiusa" else ("attesa" if rec["stato"] == "In attesa" else "")
            tv_pan.insert("", "end", iid=s["id_fam"], tags=(tag_r,) if tag_r else (), values=(
                _data_it(s["data"]), s["categoria"], s["descrizione"], et(s["pagante"]),
                _fmt_it(s["importo"]), _fmt_it(cop), _fmt_it(round(s["importo"] - cop, 2)), testo_mia,
                ("⏳ " if rec["stato"] == "In attesa" else "") + rec["stato"],
                info["conto"], info["ora"], info["hashtag"], info["metodo"]))
            try:
                _d_tip = datetime.date.fromisoformat(s["data"]).strftime("%d-%m-%Y")
            except Exception:
                _d_tip = ""
            tv_pan._metodo_lookup[s["id_fam"]] = {
                "metodo": metodo_pagamento_pulito(info["metodo"]),
                "conto": info["conto"],
                "ora": info["ora"],
                "hashtag": info["hashtag"].split(),
                "id_ricorrenza": "",
                "id_spesa": s["id_spesa"] if s["id_spesa"] in stato["voci_loc"] else "",
                "data": _d_tip,
                "categoria": s["categoria"],
                "importo": s["importo"],
                "tipo": "Uscita",
                "_righe_extra": [("Pagante", et(s["pagante"])), ("Stato", rec["stato"])],
            }

        n_conf = 0
        for c in sorted(stato["contributi"].values(), key=lambda x: x["id_contrib"]):
            s = stato["spese"].get(c["id_fam"])
            if not s or s["ritirata"]:
                continue
            if c["stato"] == "proposta" and s["pagante"] == me:
                n_conf += 1
                tv_conf.insert("", "end", iid=c["id_contrib"], values=(
                    _data_it(s["data"]), et(c["profilo"]), s["descrizione"],
                    _fmt_it(s["importo"]), _fmt_it(c["proposta"]), c["nota"]))
            if c["profilo"] == me:
                nota = c["nota_risposta"] if c["stato"] == "rifiutata" and c["nota_risposta"] else c["nota"]
                tv_mie.insert("", "end", iid=c["id_contrib"], values=(
                    _data_it(s["data"]), s["descrizione"], et(s["pagante"]), _fmt_it(c["proposta"]),
                    _fmt_it(c["importo"]) if c["stato"] == "confermata" else "",
                    STATI_LBL.get(c["stato"], c["stato"]), nota))
        nb.tab(tab_conf, text=f"  Da confermare ({n_conf})  " if n_conf else "  Da confermare  ")

        ant, ric, ver = {}, {}, {}
        for s in lista:
            if var_nascondi.get() and _stato_spesa(s) == "Chiusa":
                continue
            ant[s["pagante"]] = ant.get(s["pagante"], 0.0) + s["importo"]
            for c in s["contributi"]:
                if c["stato"] == "confermata":
                    ric[s["pagante"]] = ric.get(s["pagante"], 0.0) + c["importo"]
                    ver[c["profilo"]] = ver.get(c["profilo"], 0.0) + c["importo"]
        membri = list(dict.fromkeys(list(elenco_profili(self)) + list(ant) + list(ver)))
        tot = [0.0, 0.0, 0.0, 0.0]
        for m in membri:
            a, r, v = ant.get(m, 0.0), ric.get(m, 0.0), ver.get(m, 0.0)
            if not (a or r or v):
                continue
            tot = [tot[0] + a, tot[1] + r, tot[2] + (a - r), tot[3] + v]
            tv_saldi.insert("", "end", values=(et(m), _fmt_it(round(a, 2) or 0.0), _fmt_it(round(r, 2) or 0.0),
                                               _fmt_it(round(a - r, 2) or 0.0), _fmt_it(round(v, 2) or 0.0)))
        lbl_tot_saldi.config(text=(
            f"TOTALE    Spese anticipate: {_fmt_it(round(tot[0], 2) or 0.0)} €    Quote ricevute: {_fmt_it(round(tot[1], 2) or 0.0)} €    "
            f"Residuo: {_fmt_it(round(tot[2], 2) or 0.0)} €    Quote versate: {_fmt_it(round(tot[3], 2) or 0.0)} €"))

        for ev in sorted(eventi, key=_chiave_evento, reverse=True):
            testo = _descrivi_evento(ev, stato, et)
            if testo:
                tv_storico.insert("", "end", values=(
                    f"{_data_it(ev.get('ts', '')[:10])} {ev.get('ts', '')[11:16]}", testo))

    def _centra(dlg, w, h):
        win.update_idletasks()
        x = win.winfo_rootx() + (win.winfo_width() // 2) - (w // 2)
        y = win.winfo_rooty() + (win.winfo_height() // 2) - (h // 2)
        dlg.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")

    def _dialogo(titolo, w, h, ico="utenti", ridimensiona=False):
        dlg = tk.Toplevel(win)
        dlg.withdraw()
        dlg.title(titolo)
        dlg.configure(bg=bg)
        dlg.transient(win)
        dlg.resizable(ridimensiona, ridimensiona)
        if ridimensiona:
            dlg.minsize(w, h)
        _centra(dlg, w, h)
        dlg.bind("<Escape>", lambda e: dlg.destroy())
        img = self.icone_gui.get(ico)
        lt = tk.Label(dlg, text=" " + titolo, image=img, compound="left",
                      font=("Arial", 11, "bold"), bg=bg, fg=self.COLOR_HEADER, anchor="w")
        if img:
            lt.image = img
        lt.pack(fill="x", padx=18, pady=(14, 6))
        return dlg

    def _barra_pop(dlg, cmd_ok, testo_ok="Conferma"):
        fr = tk.Frame(dlg, bg=bg)
        fr.pack(side="bottom", fill="x", padx=18, pady=(10, 14))
        _btn(fr, "check", testo_ok, cmd_ok, side="left", padx=0)
        _btn(fr, "chiudi", "Annulla", dlg.destroy, side="right", padx=0)
        return fr

    def _apri(dlg):
        dlg.deiconify()
        try:
            dlg.wait_visibility()
            dlg.grab_set()
        except tk.TclError:
            pass

    def _riga(parent, r, testo, widget_fn):
        tk.Label(parent, text=testo, bg=bg, fg=fg, font=("Arial", 9, "bold")).grid(
            row=r, column=0, sticky="w", padx=(0, 10), pady=5)
        w = widget_fn(parent)
        w.grid(row=r, column=1, sticky="ew", pady=5)
        return w

    def _pubblica_voce(d, e):
        id_spesa = campo(e, "id_spesa", "")
        id_fam = uuid.uuid4().hex[:12]
        tags = list(campo(e, "hashtag", []) or [])
        _scrivi_evento(me, "spesa_pubblicata", id_fam=id_fam, id_spesa=id_spesa, data=d.isoformat(),
                       categoria=e.categoria, descrizione=e.descrizione,
                       importo=round(float(e.importo), 2),
                       ora=campo(e, "ora", ""), metodo=campo(e, "metodo_pagamento", ""),
                       hashtag=[t for t in tags if t not in (TAG_POOL, TAG_RIENTRO)])
        link = _carica_link()
        link["voci"][id_spesa] = {"ruolo": "origine", "id_fam": id_fam}
        _salva_link(link)
        if TAG_POOL not in tags:
            tags.append(TAG_POOL)
            e.hashtag = tags
        _invalida_cache_tag(self)
        self.save_db()
        self.refresh_gui()

    def pubblica():
        link = _carica_link()
        limite = datetime.date.today() - datetime.timedelta(days=GIORNI_PICKER)
        dlg = _dialogo("Pubblica spesa", 1150, 600, ico="aggiungi", ridimensiona=True)
        _barra_pop(dlg, lambda: condividi(), "Condividi")

        candidate = []
        for d in sorted(self.spese, reverse=True):
            if d < limite:
                break
            for e in self.spese[d]:
                if not isinstance(e, SpesaEntry) or e.tipo != "Uscita":
                    continue
                if e.id_spesa in link["voci"]:
                    continue
                if _e_fairshare(e):
                    continue
                try:
                    conto = self._conto_effettivo(e) or ""
                except Exception:
                    conto = campo(e, "conto", "") or ""
                candidate.append((d, e, conto))

        riga_cerca = tk.Frame(dlg, bg=bg)
        riga_cerca.pack(fill="x", padx=10, pady=(0, 4))
        tk.Label(riga_cerca, image=self.icone_gui.get("search"), text=" Ricerca:", compound="left",
                 bg=bg, fg=fg, font=("Arial", 9, "bold")).pack(side="left")
        v_cerca = tk.StringVar()
        e_cerca = ttk.Entry(riga_cerca, textvariable=v_cerca, width=22)
        e_cerca.pack(side="left", padx=8)
        tk.Label(riga_cerca, text=f"Uscite degli ultimi {GIORNI_PICKER} giorni non ancora condivise (escluse quelle FairShare)",
                 bg=bg, fg="gray", font=("Arial", 8, "italic")).pack(side="right")

        pp = _pannello_filtri(
            self, dlg, bg,
            [[("categoria", "combo", "Categoria:",
               [TUTTI] + sorted({e.categoria for _d, e, _c in candidate}, key=str.lower), 18),
              ("mese", "combo", "Mese:",
               [TUTTI] + sorted({_mese_lbl(d.isoformat()) for d, _e, _c in candidate},
                                key=lambda m: (m[3:], m[:2]), reverse=True), 9),
              ("conto", "combo", "Conto:",
               [TUTTI] + sorted({c for _d, _e, c in candidate if c}, key=str.lower), 16),
              ("metodo", "combo", "Metodo Pag.:", [TUTTI] + METODI_PAGAMENTO_EMOJI, 20)],
             [("tag", "entry", "Hashtag:", None, 14),
              ("testo", "entry", "Descrizione contiene:", None, 20),
              ("imp_da", "entry", "Importo da:", None, 9),
              ("imp_a", "entry", "a:", None, 9),
              ("da", "data", "Dal:", None, 11),
              ("a", "data", "Al:", None, 11)]],
            su_cambio=lambda: riempi(), prima_di=lambda: fr)

        fr = tk.Frame(dlg, bg=bg)
        fr.pack(fill="both", expand=True, padx=10, pady=(0, 4))
        colonne = ("Data", "Categoria", "Descrizione", "Importo", "Conto", "Ora", "Hashtag", "Metodo")
        tvp = ttk.Treeview(fr, columns=colonne, show="headings", selectmode="browse")
        larg = {"Data": 90, "Categoria": 130, "Descrizione": 300, "Importo": 100, "Conto": 110,
                "Ora": 55, "Hashtag": 140, "Metodo": 110}
        for col in colonne:
            tvp.heading(col, text=col, command=lambda _c=col: self.treeview_sort_column(tvp, _c, False))
            tvp.column(col, width=larg[col], anchor="e" if col == "Importo" else "w",
                       stretch=(col == "Descrizione"))
        sbp = ttk.Scrollbar(fr, orient="vertical", command=tvp.yview, style="Vertical.TScrollbar")
        tvp.configure(yscrollcommand=sbp.set)
        tvp.pack(side="left", fill="both", expand=True)
        sbp.pack(side="right", fill="y")
        riferimenti = {}
        tvp._metodo_lookup = {}
        self._bind_tooltip_metodo(tvp, col_desc=2)

        def riempi(*_):
            tvp.delete(*tvp.get_children())
            riferimenti.clear()
            tvp._metodo_lookup.clear()
            spec = pp["spec"]()
            if spec and spec.get("metodo"):
                spec["metodo"] = metodo_pagamento_pulito(spec["metodo"])
            parola = v_cerca.get().strip().lower()
            for d, e, conto in candidate:
                tags_txt = " ".join(campo(e, "hashtag", []) or [])
                metodo = campo(e, "metodo_pagamento", "")
                rec = {"categoria": e.categoria, "mese": _mese_lbl(d.isoformat()), "conto": conto,
                       "metodo": metodo, "hashtag": tags_txt, "descrizione": e.descrizione,
                       "importo": float(e.importo), "data": d}
                if not _passa_filtri(spec, rec):
                    continue
                if parola and not any(parola in str(x).lower() for x in (
                        e.categoria, e.descrizione, _fmt_it(e.importo), conto, metodo, tags_txt)):
                    continue
                iid = tvp.insert("", "end", values=(
                    d.strftime("%d/%m/%Y"), e.categoria, e.descrizione, f"{_fmt_it(e.importo)} €",
                    conto, campo(e, "ora", ""), tags_txt, metodo), tags=("uscita_tag",))
                riferimenti[iid] = (d, e)
                tvp._metodo_lookup[iid] = {
                    "metodo": metodo_pagamento_pulito(metodo),
                    "conto": conto,
                    "ora": campo(e, "ora", ""),
                    "hashtag": list(campo(e, "hashtag", []) or []),
                    "id_ricorrenza": campo(e, "id_ricorrenza", "") or "",
                    "id_spesa": campo(e, "id_spesa", "") or "",
                    "data": d.strftime("%d-%m-%Y"),
                    "categoria": e.categoria,
                    "importo": e.importo,
                    "tipo": "Uscita",
                }
            self.treeview_sort_column(tvp, "Data", True)
        tvp.tag_configure("uscita_tag", foreground="red")

        job = {"id": None}

        def _rinvia(*_):
            if job["id"]:
                dlg.after_cancel(job["id"])
            job["id"] = dlg.after(400, riempi)
        v_cerca.trace_add("write", _rinvia)

        def condividi(*_):
            iid = _selezione(tvp)
            if not iid:
                self.show_toast("Seleziona una spesa", parent=dlg)
                return
            d, e = riferimenti[iid]
            _pubblica_voce(d, e)
            dlg.destroy()
            ricarica()
            self.show_toast("Spesa condivisa nel CommunityPool", parent=win)
        tvp.bind("<Double-1>", condividi)
        riempi()
        _apri(dlg)
        e_cerca.focus_set()

    def ritira():
        iid = _selezione(tv_pan)
        s = stato["spese"].get(iid)
        if not s:
            self.show_toast("Seleziona una spesa", parent=win)
            return
        if s["pagante"] != me:
            self.show_toast("Puoi ritirare solo le spese che hai pubblicato", parent=win)
            return
        if _coperto(s) > 0:
            self.show_toast("Ci sono quote già confermate: non si può ritirare", parent=win)
            return
        if not self.show_custom_askyesno("Ritira spesa", f"Ritirare '{s['descrizione']}' dal CommunityPool?"):
            return
        _scrivi_evento(me, "spesa_ritirata", id_fam=s["id_fam"])
        link = _carica_link()
        link["voci"].pop(s["id_spesa"], None)
        _salva_link(link)
        _d, e = _trova_voce(self, s["id_spesa"])
        if e is not None:
            tags = [t for t in (campo(e, "hashtag", []) or []) if t != TAG_POOL]
            e.hashtag = tags
            _invalida_cache_tag(self)
            self.save_db()
            self.refresh_gui()
        ricarica()

    def chiudi_riapri():
        iid = _selezione(tv_pan)
        s = stato["spese"].get(iid)
        if not s:
            self.show_toast("Seleziona una spesa", parent=win)
            return
        if s["pagante"] != me:
            self.show_toast("Solo chi ha pubblicato la spesa può chiuderla", parent=win)
            return
        if s["chiusa"]:
            _scrivi_evento(me, "spesa_riaperta", id_fam=s["id_fam"])
        else:
            if any(c["stato"] == "proposta" for c in s["contributi"]):
                self.show_toast("Ci sono proposte in attesa: confermale o rifiutale prima", parent=win)
                return
            if round(s["importo"] - _coperto(s), 2) <= 0:
                self.show_toast("La spesa è già chiusa (residuo 0)", parent=win)
                return
            if not self.show_custom_askyesno(
                    "Chiudi spesa",
                    f"Chiudere '{s['descrizione']}'?\nNessuno potrà più proporre quote."):
                return
            _scrivi_evento(me, "spesa_chiusa", id_fam=s["id_fam"])
        ricarica()

    def proponi():
        iid = _selezione(tv_pan)
        s = stato["spese"].get(iid)
        if not s:
            self.show_toast("Seleziona una spesa", parent=win)
            return
        if s["pagante"] == me:
            self.show_toast("Hai pagato tu questa spesa", parent=win)
            return
        if any(c["profilo"] == me and c["stato"] == "proposta" for c in s["contributi"]):
            self.show_toast("Hai già una proposta in attesa su questa spesa", parent=win)
            return
        if s["chiusa"]:
            self.show_toast("La spesa è chiusa dal pagante", parent=win)
            return
        residuo = round(s["importo"] - _coperto(s), 2)
        if residuo <= 0:
            self.show_toast("La spesa è già coperta", parent=win)
            return
        dlg = _dialogo("Proponi la tua quota", 460, 330, ico="saldo")
        _barra_pop(dlg, lambda: invia(), "Invia proposta")
        corpo = tk.Frame(dlg, bg=bg)
        corpo.pack(fill="both", expand=True, padx=18)
        corpo.columnconfigure(1, weight=1)
        cats_loc = sorted((c for c in self.categorie if c != self.CATEGORIA_RIMOSSA), key=str.lower)
        v_imp = tk.StringVar()
        v_nota = tk.StringVar()
        v_cat = tk.StringVar(value=s["categoria"] if s["categoria"] in cats_loc else "Generica")
        tk.Label(corpo, text=f"{s['descrizione']}\nTotale {_fmt_it(s['importo'])} €  ·  residuo {_fmt_it(residuo)} €",
                 bg=bg, fg=fg, font=("Arial", 9, "bold"), justify="left", anchor="w").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
        e_imp = _riga(corpo, 1, "La tua quota €", lambda p: ttk.Entry(p, textvariable=v_imp))
        _riga(corpo, 2, "Nota (facoltativa)", lambda p: ttk.Entry(p, textvariable=v_nota))
        _riga(corpo, 3, "Categoria nel tuo profilo",
              lambda p: ttk.Combobox(p, textvariable=v_cat, values=cats_loc,
                                     state="readonly", style="Border.TCombobox"))

        def invia(*_):
            imp = _parse_importo(v_imp.get())
            if imp is None:
                self.show_toast("Importo non valido", parent=dlg)
                return
            if imp > residuo + 0.005:
                self.show_toast(f"Supera il residuo ({_fmt_it(residuo)} €)", parent=dlg)
                return
            _scrivi_evento(me, "quota_proposta", id_contrib=uuid.uuid4().hex[:12], id_fam=s["id_fam"],
                           importo=imp, nota=v_nota.get().strip(), categoria_membro=v_cat.get())
            dlg.destroy()
            ricarica()
            self.show_toast("Quota inviata, in attesa di conferma", parent=win)
        dlg.bind("<Return>", invia)
        _apri(dlg)
        e_imp.focus_set()

    def _controlla_conferma(s, imp, parent):
        if s["chiusa"]:
            self.show_toast("Spesa chiusa: riaprila per confermare quote", parent=parent)
            return False
        if _coperto(s) + imp > s["importo"] + 0.005:
            self.show_toast("Con questa quota si supera il totale della spesa", parent=parent)
            return False
        return True

    def _esegui_conferma(c, imp):
        _scrivi_evento(me, "quota_confermata", id_contrib=c["id_contrib"], importo=imp)
        community_pool_sync(self, silenzioso=True)
        ricarica()
        self.show_toast("Quota confermata, rientro registrato", parent=win)

    def conferma(modifica=False):
        iid = _selezione(tv_conf)
        c = stato["contributi"].get(iid)
        if not c:
            self.show_toast("Seleziona una proposta", parent=win)
            return
        s = stato["spese"].get(c["id_fam"])
        if not modifica:
            if _controlla_conferma(s, c["proposta"], win):
                _esegui_conferma(c, c["proposta"])
            return
        if s["chiusa"]:
            self.show_toast("Spesa chiusa: riaprila per confermare quote", parent=win)
            return
        dlg = _dialogo("Importo confermato", 420, 220, ico="salva")
        _barra_pop(dlg, lambda: ok(), "Conferma")
        corpo = tk.Frame(dlg, bg=bg)
        corpo.pack(fill="both", expand=True, padx=18)
        corpo.columnconfigure(1, weight=1)
        v_imp = tk.StringVar(value=_fmt_it(c["proposta"]))
        tk.Label(corpo, text=f"{et(c['profilo'])} propone {_fmt_it(c['proposta'])} € su '{s['descrizione']}'",
                 bg=bg, fg=fg, font=("Arial", 9, "bold"), wraplength=380, justify="left",
                 anchor="w").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
        e_imp = _riga(corpo, 1, "Importo da confermare €", lambda p: ttk.Entry(p, textvariable=v_imp))

        def ok(*_):
            imp = _parse_importo(v_imp.get())
            if imp is None:
                self.show_toast("Importo non valido", parent=dlg)
                return
            if not _controlla_conferma(s, imp, dlg):
                return
            dlg.destroy()
            _esegui_conferma(c, imp)
        dlg.bind("<Return>", ok)
        _apri(dlg)
        e_imp.focus_set()
        e_imp.select_range(0, "end")

    def rifiuta():
        iid = _selezione(tv_conf)
        c = stato["contributi"].get(iid)
        if not c:
            self.show_toast("Seleziona una proposta", parent=win)
            return
        s = stato["spese"].get(c["id_fam"])
        dlg = _dialogo("Rifiuta quota", 420, 220, ico="cancella")
        _barra_pop(dlg, lambda: ok(), "Rifiuta")
        corpo = tk.Frame(dlg, bg=bg)
        corpo.pack(fill="both", expand=True, padx=18)
        corpo.columnconfigure(1, weight=1)
        v_nota = tk.StringVar()
        tk.Label(corpo, text=f"Rifiutare la quota di {et(c['profilo'])} ({_fmt_it(c['proposta'])} €) "
                             f"su '{s['descrizione'] if s else '?'}'?",
                 bg=bg, fg=fg, font=("Arial", 9, "bold"), wraplength=380, justify="left",
                 anchor="w").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
        e_nota = _riga(corpo, 1, "Motivo (facoltativo)", lambda p: ttk.Entry(p, textvariable=v_nota))

        def ok(*_):
            _scrivi_evento(me, "quota_rifiutata", id_contrib=c["id_contrib"], nota=v_nota.get().strip())
            dlg.destroy()
            ricarica()
        dlg.bind("<Return>", ok)
        _apri(dlg)
        e_nota.focus_set()

    def annulla():
        iid = _selezione(tv_mie)
        c = stato["contributi"].get(iid)
        if not c or c["stato"] != "proposta":
            self.show_toast("Seleziona una proposta in attesa", parent=win)
            return
        _scrivi_evento(me, "quota_annullata", id_contrib=c["id_contrib"])
        ricarica()

    _btn(bar_pan, "aggiungi", "Pubblica spesa", pubblica)
    _btn(bar_pan, "saldo", "Proponi quota", proponi)
    _btn(bar_pan, "cancella", "Ritira spesa", ritira)
    _btn(bar_pan, "check", "Chiudi / Riapri spesa", chiudi_riapri)
    _btn(bar_pan, "reset_campo", "Aggiorna", ricarica, side="right")
    _btn(bar_conf, "salva", "Conferma", lambda: conferma(False))
    _btn(bar_conf, "salva", "Modifica importo e conferma", lambda: conferma(True))
    _btn(bar_conf, "cancella", "Rifiuta", rifiuta)
    _btn(bar_mie, "reset_campo", "Annulla proposta", annulla)

    def esporta():
        indice = nb.index(nb.select())
        nomi = ["Panoramica", "Da confermare", "Le mie quote", "Saldi", "Storico"]
        alberi = [tv_pan, tv_conf, tv_mie, tv_saldi, tv_storico]
        tv = alberi[indice]
        righe = [tv.item(i, "values") for i in tv.get_children()]
        if not righe:
            self.show_toast("Nulla da esportare.", parent=win)
            return
        intest = [re.sub(r" [▲▼]$", "", tv.heading(c)["text"]) for c in tv["columns"]]
        periodo = pann["f"]["mese"].get() or "tutti"
        titolo = f"COMMUNITYPOOL — {nomi[indice].upper()} ({et(me)}, periodo: {periodo if indice in (0, 3) else 'tutti'})"
        oggi = datetime.date.today()
        self.show_export_preview(
            _testo_tabella(titolo, intest, righe),
            default_filename=f"CommunityPool_{nomi[indice].replace(' ', '_')}_{oggi.strftime('%d-%m-%Y')}.txt")

    ricarica()
    if nov_sp:
        nb.tab(tab_pan, text=f"  Panoramica ({nov_sp} nuove)  ")
    if nov_es:
        nb.tab(tab_mie, text=f"  Le mie quote ({nov_es} esiti)  ")

    def _alla_chiusura(e):
        if e.widget is win:
            _segna_visto(me)
            self._pool_novita_notificate = 0
            _aggiorna_badge_pool(self, 0)
    win.bind("<Destroy>", _alla_chiusura, add="+")
    campo_input.focus_set()

_RE_NUM = re.compile(r"^-?[\d.]+,\d{2}( ⏳)?$")

def _testo_tabella(titolo, intestazioni, righe):
    righe = [[str(v) for v in r] for r in righe]
    n = len(intestazioni)
    larg = [max([len(intestazioni[i])] + [len(r[i]) for r in righe if i < len(r)]) for i in range(n)]
    num = [all((_RE_NUM.match(r[i]) or r[i] == "") for r in righe) for i in range(n)]

    def fmt(vals):
        parti = []
        for i in range(n):
            v = vals[i] if i < len(vals) else ""
            parti.append(f"{v:>{larg[i]}}" if num[i] else f"{v:<{larg[i]}}")
        return " │ ".join(parti)
    header = fmt(intestazioni)
    sep = "─" * len(header)
    larghezza = max(len(header), len(titolo))
    linee = ["═" * larghezza, titolo.center(larghezza), "═" * larghezza, "", header, sep]
    linee += [fmt(r) for r in righe]
    linee += [sep, f"Righe: {len(righe)}", "═" * larghezza]
    return "\n".join(linee)

def _descrivi_evento(ev, stato, et):
    t = ev["tipo"]
    chi = et(ev["profilo"])
    if t == "profilo_eliminato":
        return f"{chi} è stato eliminato"
    if t == "spesa_pubblicata":
        return f"{chi} ha condiviso '{ev.get('descrizione', '')}' ({_fmt_it(float(ev.get('importo', 0)))} €)"
    if t == "spesa_aggiornata":
        return f"{chi} ha aggiornato '{ev.get('descrizione', '')}' ({_fmt_it(float(ev.get('importo', 0)))} €)"
    if t == "spesa_ritirata":
        s = stato["spese"].get(ev.get("id_fam"))
        return f"{chi} ha ritirato '{s['descrizione'] if s else ev.get('id_fam', '')}'"
    if t in ("spesa_chiusa", "spesa_riaperta"):
        s = stato["spese"].get(ev.get("id_fam"))
        azione = "chiuso" if t == "spesa_chiusa" else "riaperto"
        return f"{chi} ha {azione} '{s['descrizione'] if s else ev.get('id_fam', '')}'"
    c = stato["contributi"].get(ev.get("id_contrib"))
    s = stato["spese"].get(c["id_fam"]) if c else stato["spese"].get(ev.get("id_fam"))
    desc = s["descrizione"] if s else "?"
    if t == "quota_proposta":
        return f"{chi} propone {_fmt_it(float(ev.get('importo', 0)))} € su '{desc}'"
    if t in ("quota_confermata", "quota_rifiutata") and s and ev["profilo"] != _base_nome(s["pagante"]):
        return ""
    if t == "quota_annullata" and c and ev["profilo"] != _base_nome(c["profilo"]):
        return ""
    if t == "quota_confermata":
        membro = et(c["profilo"]) if c else "?"
        return f"{chi} ha confermato {_fmt_it(float(ev.get('importo', 0)))} € di {membro} su '{desc}'"
    if t == "quota_rifiutata":
        membro = et(c["profilo"]) if c else "?"
        nota = f" ({ev['nota']})" if ev.get("nota") else ""
        return f"{chi} ha rifiutato la quota di {membro} su '{desc}'{nota}"
    if t == "quota_annullata":
        return f"{chi} ha annullato la sua proposta su '{desc}'"
    return ""
    
def _voce_bloccata(e):
    if campo(e, "pool_ref", ""):
        return True
    try:
        return _carica_link()["voci"].get(campo(e, "id_spesa", ""), {}).get("ruolo") == "origine"
    except Exception:
        return False
        
def installa_blocco_modifica(GestioneSpese):
    def _sblocca(self):
        try:
            self.imp_entry.config(state="normal")
        except Exception:
            pass

    def _voce_pool(self):
        try:
            d, i = self.modifica_idx
            return _voce_bloccata(self.spese[d][i])
        except Exception:
            return False

    def _avvolgi_carica(nome):
        orig = getattr(GestioneSpese, nome)
        def f(self, *a, **k):
            _sblocca(self)
            r = orig(self, *a, **k)
            if _voce_pool(self):
                self.imp_entry.config(state="readonly")
                self.set_tipo_spesa_editable(False)
            return r
        f.__name__ = nome
        setattr(GestioneSpese, nome, f)

    _avvolgi_carica("avvia_modifica_da_selezione")
    _avvolgi_carica("on_table_click")

    _orig_reset = GestioneSpese.reset_modifica_form
    def reset_modifica_form(self, *a, **k):
        _sblocca(self)
        return _orig_reset(self, *a, **k)
    GestioneSpese.reset_modifica_form = reset_modifica_form

    _orig_web = GestioneSpese.salva_modifica_voce
    def salva_modifica_voce(self, params):
        msg = None
        try:
            d = datetime.datetime.strptime(params.get("vecchia_data", [""])[0], "%d-%m-%Y").date()
            i = self._idx_da_id(d, int(params.get("vecchio_idx", ["0"])[0]), params.get("vecchio_sid", [""])[0])
            v = self.spese[d][i] if i is not None else None
            if v is not None and _voce_bloccata(v):
                imp = float(params.get("importo", ["0"])[0])
                tipo = params.get("tipo", ["Uscita"])[0]
                if abs(imp - float(campo(v, "importo", 0))) > 0.004 or tipo != campo(v, "tipo", ""):
                    msg = "Importo e tipo di una quota o di un rientro del Pool non si modificano: seguono il contributo registrato nel Pool."
        except Exception:
            pass
        if msg:
            raise ValueError(msg)
        return _orig_web(self, params)
    GestioneSpese.salva_modifica_voce = salva_modifica_voce
