#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import uuid
import json
import datetime
import threading

from moduli import gestisci_promemoria as gp
from moduli import ics_agenda as _ics

_LOCK = threading.RLock()
GIORNI_MAX = 90

def _oggi():
    return datetime.date.today()

def _desktop_aperto(self):
    p = getattr(self, "_promemoria_popup", None)
    return p is not None

_MSG_DESKTOP = ("La finestra Promemoria è aperta sul desktop: chiudila prima di modificare dal web, "
                "altrimenti le modifiche verrebbero sovrascritte.")

def _voce_json(d, v, oggi):
    try:
        d0 = datetime.date.fromisoformat(v["data"])
    except Exception:
        d0 = d
    dur = gp._durata_gg(v)
    rip = v.get("ripetizione", "Nessuna")
    rip_txt = gp._rip_testo(v) if rip != "Nessuna" else ""
    imp = v.get("importo")
    delta = (d - oggi).days
    return {
        "id": v.get("id", ""),
        "titolo": v.get("titolo", ""),
        "tipo": v.get("tipo", "Appuntamento"),
        "d": d.isoformat(),
        "d_it": gp._fmt_data(d),
        "giorno": gp.GIORNI_ESTESI[d.weekday()],
        "delta": delta,
        "ora": v.get("ora", "") or "",
        "fine": gp._testo_fine(v),
        "importo": gp._fmt_eur(imp) if imp not in (None, "") else "",
        "rip": rip_txt,
        "luogo": v.get("luogo", "") or "",
        "note": v.get("note", "") or "",
        "esterna": bool(v.get("esterna")),
        "origine": v.get("origine", "") if v.get("esterna") else "",
        "fatta": (not v.get("esterna")) and gp._fatta(v, d),
        "ripete": rip != "Nessuna",
        "multi": dur > 0,
        "d0": d0.isoformat(),
    }

def _voce_form(v):
    imp = v.get("importo")
    rip = v.get("ripetizione", "Nessuna")
    return {
        "id": v["id"], "titolo": v.get("titolo", ""), "tipo": v.get("tipo", "Appuntamento"),
        "data": v["data"], "ora": v.get("ora", ""), "ora_fine": v.get("ora_fine", ""),
        "data_fine": v.get("data_fine", ""),
        "importo": ("%.2f" % float(imp)).replace(".", ",") if imp not in (None, "") else "",
        "ripetizione": rip,
        "rip_n": int(v.get("rip_n", 1) or 1) if rip == "Personalizzata" else 1,
        "rip_unita": v.get("rip_unita", "mesi") if rip == "Personalizzata" else "mesi",
        "rip_fine": v.get("rip_fine", ""), "preavviso": int(v.get("preavviso", 0) or 0),
        "anticipo_min": gp._anticipo_min(v), "luogo": v.get("luogo", ""), "note": v.get("note", ""),
        "email": bool(v.get("email", False)),
        "rip_testo": gp._rip_testo(v) if rip in ("Avanzata",) or v.get("rrule") else "",
    }

def promemoria_web_elenco(self, giorni=14):
    try:
        giorni = max(1, min(GIORNI_MAX, int(giorni)))
    except (TypeError, ValueError):
        giorni = 14
    oggi = _oggi()
    try:
        with _LOCK:
            dati, errore = gp._carica()
            if errore:
                return {"ok": False, "errore": f"Il file promemoria non si legge: {errore}"}
            try:
                ext = gp._scadenze_esterne(self, dati.get("fonti"))
            except Exception:
                ext = []
            agenda = list(dati["agenda"]) + ext
            scaduti = [_voce_json(d, v, oggi) for d, v in gp._scaduti(agenda, oggi)]
            occ = gp._occorrenze(agenda, oggi, oggi + datetime.timedelta(days=giorni))
            gruppi = []
            for d in sorted(occ):
                gruppi.append({"d": d.isoformat(), "d_it": gp._fmt_data(d), "giorno": gp.GIORNI_ESTESI[d.weekday()],
                               "delta": (d - oggi).days,
                               "voci": [_voce_json(d, v, oggi) for v in occ[d]]})
            fine = oggi + datetime.timedelta(days=giorni)
            preavvisi = [_voce_json(d, v, oggi) for d, v in gp._anticipi(agenda, oggi) if d > fine]
            modificabili = {v["id"]: _voce_form(v) for v in dati["agenda"]}
    except Exception as e:
        return {"ok": False, "errore": f"Errore nella lettura dell'agenda: {e}"}
    return {"ok": True, "oggi": oggi.isoformat(), "giorni": giorni, "scaduti": scaduti, "gruppi": gruppi,
            "preavvisi": preavvisi, "voci": modificabili, "n_ext": len(ext),
            "desktop_aperto": _desktop_aperto(self)}

def _parse_data_iso(s):
    s = str(s or "").strip()
    if not s:
        return None
    return datetime.date.fromisoformat(s)

def _valida(d):
    titolo = str(d.get("titolo", "")).strip()
    if not titolo:
        return None, "Inserisci un titolo."
    if len(titolo) > gp.MAX_TITOLO:
        return None, f"Titolo troppo lungo (massimo {gp.MAX_TITOLO} caratteri)."
    tipo = d.get("tipo")
    if tipo not in gp.TIPI:
        return None, "Tipo non valido."
    try:
        data = _parse_data_iso(d.get("data"))
    except ValueError:
        return None, "Data non valida."
    if data is None:
        return None, "Inserisci la data."
    try:
        ora = gp._normalizza_ora(d.get("ora"))
    except ValueError:
        return None, "Ora non valida: scrivi ad esempio 18, 18:30 o 1830."
    try:
        ora_fine = gp._normalizza_ora(d.get("ora_fine"))
    except ValueError:
        return None, "Ora di fine non valida."
    try:
        d_fine = _parse_data_iso(d.get("data_fine"))
        rip_fine = _parse_data_iso(d.get("rip_fine"))
    except ValueError:
        return None, "Data di fine non valida."
    imp_s = str(d.get("importo", "") or "").strip()
    if len(imp_s) > gp.MAX_IMPORTO or (imp_s and not re.match(r"^\d*[.,]?\d{0,2}$", imp_s.replace("€", "").strip())):
        return None, "Importo non valido: inserisci un numero, ad esempio 85,50."
    try:
        imp = gp._parse_importo(imp_s)
    except ValueError:
        return None, "Importo non valido: inserisci un numero, ad esempio 85,50."
    if d_fine and d_fine < data:
        return None, "La data di fine è prima dell'inizio."
    if d_fine == data:
        d_fine = None
    if ora_fine and not ora:
        return None, "Per indicare l'ora di fine serve anche l'ora di inizio."
    if ora_fine and not d_fine and ora_fine <= ora:
        return None, "L'ora di fine deve essere dopo quella di inizio."
    rip = str(d.get("ripetizione", "Nessuna"))
    if rip not in gp.RIPETIZIONI and rip != "Avanzata":
        return None, "Ripetizione non valida."
    if rip == "Nessuna":
        rip_fine = None
    if rip_fine and rip_fine < data:
        return None, "La ripetizione finisce prima dell'inizio."
    rip_n, rip_u = 1, "mesi"
    if rip == "Personalizzata":
        try:
            rip_n = int(d.get("rip_n"))
            if not 1 <= rip_n <= 99:
                raise ValueError
        except (TypeError, ValueError):
            return None, "Scrivi un numero da 1 a 99 per la ripetizione personalizzata."
        rip_u = d.get("rip_unita") if d.get("rip_unita") in gp.UNITA_RIP else "mesi"
    try:
        pre = int(d.get("preavviso", 0) or 0)
    except (TypeError, ValueError):
        pre = 0
    pre = max(0, min(pre, 365))
    try:
        ant = gp._anticipo_min(d)
    except Exception:
        ant = gp.ANTICIPO_ORA_MIN
    luogo = str(d.get("luogo", "") or "").strip()[:_ics.MAX_LUOGO]
    note = str(d.get("note", "") or "").strip()[:gp.MAX_NOTE]
    campi = {"titolo": titolo, "tipo": tipo, "data": data.isoformat(), "ora": ora, "importo": imp,
             "ripetizione": rip, "note": note, "preavviso": pre, "anticipo_min": ant,
             "email": bool(d.get("email")), "data_fine": d_fine.isoformat() if d_fine else "",
             "ora_fine": ora_fine, "luogo": luogo, "rip_fine": rip_fine.isoformat() if rip_fine else ""}
    if rip == "Personalizzata":
        campi.update(rip_n=rip_n, rip_unita=rip_u)
    return campi, None

def promemoria_web_salva(self, d):
    campi, err = _valida(d)
    if err:
        return {"ok": False, "errore": err}, 400
    vid = str(d.get("id", "") or "")
    if _desktop_aperto(self):
        return {"ok": False, "errore": _MSG_DESKTOP}, 409
    try:
        with _LOCK:
            dati, errore = gp._carica()
            if errore:
                return {"ok": False, "errore": f"Il file promemoria non si legge: {errore}"}, 500
            if vid:
                voce = next((v for v in dati["agenda"] if v["id"] == vid), None)
                if voce is None:
                    return {"ok": False, "errore": "Voce non trovata (forse eliminata dal desktop)."}, 404
                rr = voce.get("rrule", "") if campi["ripetizione"] == voce.get("ripetizione") else ""
                if campi["ripetizione"] == "Personalizzata" and (
                        campi["rip_n"], campi["rip_unita"]) != (voce.get("rip_n"), voce.get("rip_unita")):
                    rr = ""
                campi["rrule"] = rr
                if (campi["data"] != voce["data"] or campi["ripetizione"] != voce.get("ripetizione")
                        or rr != (voce.get("rrule") or "")
                        or (campi["ripetizione"] == "Personalizzata"
                            and (campi["rip_n"], campi["rip_unita"]) != (voce.get("rip_n"), voce.get("rip_unita")))):
                    campi["fatti"] = []
                    campi["escluse"] = []
                voce.update(campi)
                gp._tocca(voce)
            else:
                campi.update(id=uuid.uuid4().hex[:8], fatti=[], escluse=[], rrule="")
                gp._tocca(campi)
                dati["agenda"].append(campi)
            gp._salva(dati)
    except Exception as e:
        return {"ok": False, "errore": f"Errore durante il salvataggio: {e}"}, 500
    return {"ok": True}, 200

def promemoria_web_fatto(self, d):
    vid = str(d.get("id", "") or "")
    try:
        giorno = datetime.date.fromisoformat(str(d.get("data", "")))
    except ValueError:
        return {"ok": False, "errore": "Data non valida."}, 400
    if _desktop_aperto(self):
        return {"ok": False, "errore": _MSG_DESKTOP}, 409
    try:
        with _LOCK:
            dati, errore = gp._carica()
            if errore:
                return {"ok": False, "errore": f"Il file promemoria non si legge: {errore}"}, 500
            v = next((x for x in dati["agenda"] if x["id"] == vid), None)
            if v is None:
                return {"ok": False, "errore": "Voce non trovata (le scadenze degli altri moduli si gestiscono da lì)."}, 404
            k = giorno.isoformat()
            if k in v["fatti"]:
                v["fatti"].remove(k)
                fatta = False
            else:
                v["fatti"].append(k)
                fatta = True
            gp._tocca(v)
            gp._salva(dati)
    except Exception as e:
        return {"ok": False, "errore": f"Errore durante il salvataggio: {e}"}, 500
    return {"ok": True, "fatta": fatta}, 200

def promemoria_web_elimina(self, d):
    vid = str(d.get("id", "") or "")
    if _desktop_aperto(self):
        return {"ok": False, "errore": _MSG_DESKTOP}, 409
    try:
        with _LOCK:
            dati, errore = gp._carica()
            if errore:
                return {"ok": False, "errore": f"Il file promemoria non si legge: {errore}"}, 500
            n = len(dati["agenda"])
            dati["agenda"] = [x for x in dati["agenda"] if x["id"] != vid]
            if len(dati["agenda"]) == n:
                return {"ok": False, "errore": "Voce non trovata."}, 404
            gp._salva(dati)
    except Exception as e:
        return {"ok": False, "errore": f"Errore durante il salvataggio: {e}"}, 500
    return {"ok": True}, 200

def promemoria_web_posticipa(self, d):
    vid = str(d.get("id", "") or "")
    modo = d.get("modo")
    if modo not in ("giorno", "settimana"):
        return {"ok": False, "errore": "Modo non valido."}, 400
    try:
        giorno = datetime.date.fromisoformat(str(d.get("data", "")))
    except ValueError:
        return {"ok": False, "errore": "Data non valida."}, 400
    if _desktop_aperto(self):
        return {"ok": False, "errore": _MSG_DESKTOP}, 409
    try:
        with _LOCK:
            dati, errore = gp._carica()
            if errore:
                return {"ok": False, "errore": f"Il file promemoria non si legge: {errore}"}, 500
            v = next((x for x in dati["agenda"] if x["id"] == vid), None)
            if v is None:
                return {"ok": False, "errore": "Voce non trovata."}, 404
            base = max(giorno, _oggi())
            nd = base + datetime.timedelta(days=1 if modo == "giorno" else 7)
            if v.get("ripetizione", "Nessuna") == "Nessuna":
                gg = gp._durata_gg(v)
                v["data"] = nd.isoformat()
                v["data_fine"] = (nd + datetime.timedelta(days=gg)).isoformat() if gg else ""
                v["fatti"] = []
                gp._tocca(v)
            else:
                nuova = {k: v[k] for k in ("titolo", "tipo", "importo", "note", "preavviso", "email",
                                          "anticipo_min", "luogo", "ora") if k in v}
                nuova.update(id=uuid.uuid4().hex[:8], data=nd.isoformat(), ripetizione="Nessuna",
                             fatti=[], escluse=[], rrule="", rip_fine="", data_fine="", ora_fine="")
                gp._tocca(nuova)
                dati["agenda"].append(nuova)
                if giorno.isoformat() not in v["fatti"]:
                    v["fatti"].append(giorno.isoformat())
                gp._tocca(v)
            gp._salva(dati)
    except Exception as e:
        return {"ok": False, "errore": f"Errore durante il salvataggio: {e}"}, 500
    return {"ok": True, "nuova_data": gp._fmt_data(nd)}, 200


_PAGINA = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>🗓️ Promemoria</title>
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
    .barra { display:flex; gap:8px; align-items:center; margin-bottom:12px; }
    .barra select { flex:1; }
    input, select, textarea { background:var(--surface3); border:1px solid var(--border); color:var(--text); border-radius:10px; padding:11px; font-family:inherit; font-size:1em; width:100%; }
    input:focus, select:focus, textarea:focus { outline:none; border-color:var(--border-active); }
    textarea { resize:vertical; min-height:70px; }
    .chk { display:flex; align-items:center; gap:10px; color:var(--text-mid); font-size:0.88em; margin:4px 0 10px; }
    .chk input { width:20px; height:20px; flex:none; }
    .sez { font-size:0.78em; font-weight:800; letter-spacing:1px; text-transform:uppercase; margin:16px 2px 6px; color:var(--gold); display:flex; justify-content:space-between; }
    .sez.rosso { color:var(--red); }
    .sez .sub { color:var(--text-mid); font-weight:500; letter-spacing:0; text-transform:none; }
    .voce { display:flex; gap:10px; align-items:flex-start; background:var(--surface); border:1px solid var(--border); border-left:4px solid var(--blue); border-radius:14px; padding:11px 12px; margin-bottom:6px; cursor:pointer; }
    .voce.scad { border-left-color:var(--red); }
    .voce.ext { border-left-style:dashed; cursor:default; opacity:0.9; }
    .voce.fatta { opacity:0.5; }
    .voce.fatta .tit { text-decoration:line-through; }
    .spunta { flex:none; width:30px; height:30px; border-radius:50%; border:2px solid var(--text-dim); background:none; color:#fff; font-size:1em; cursor:pointer; display:flex; align-items:center; justify-content:center; margin-top:1px; }
    .voce.fatta .spunta { background:var(--green); border-color:var(--green); }
    .spunta:disabled { opacity:0.25; cursor:default; }
    .corpo { flex:1; min-width:0; }
    .tit { font-weight:700; font-size:0.98em; overflow-wrap:anywhere; }
    .meta { color:var(--text-mid); font-size:0.8em; margin-top:2px; line-height:1.4; }
    .chip { display:inline-block; font-size:0.72em; font-weight:700; padding:1px 8px; border-radius:20px; border:1px solid currentColor; margin-right:4px; }
    .chip.s { color:var(--red); } .chip.a { color:var(--blue); } .chip.e { color:var(--orange); }
    .ora { font-weight:800; color:var(--text); }
    .vuoto { text-align:center; color:var(--text-mid); padding:30px 10px; font-size:0.95em; }
    .azioni { display:flex; flex-direction:column; gap:4px; flex:none; }
    .mini { background:var(--surface3); border:1px solid var(--border); color:var(--text-mid); border-radius:8px; height:28px; padding:0 8px; font-size:0.72em; font-family:inherit; font-weight:700; cursor:pointer; }
    #fab { position:fixed; right:18px; bottom:22px; width:58px; height:58px; border-radius:50%; background:var(--gold); color:#000; border:none; font-size:2em; font-weight:300; cursor:pointer; box-shadow:0 8px 24px rgba(0,0,0,0.5); z-index:90; }
    #velo { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.65); z-index:200; overflow-y:auto; padding:14px; }
    #form { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-lg); padding:16px; max-width:520px; margin:0 auto 40px; }
    #form h3 { font-size:1em; color:var(--gold); margin-bottom:12px; }
    .campo { margin-bottom:10px; }
    .campo label { display:block; font-size:0.78em; color:var(--text-mid); margin-bottom:4px; }
    .due { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
    .btn { display:block; width:100%; padding:13px; border-radius:12px; border:1px solid var(--border); background:var(--surface3); color:var(--text); font-family:inherit; font-size:1em; font-weight:700; cursor:pointer; }
    .btn.verde { background:var(--green); border-color:var(--green); color:#fff; }
    .btn.rosso { background:var(--red); border-color:var(--red); color:#fff; }
    .btns { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:12px; }
    .nota-av { font-size:0.8em; color:var(--text-mid); margin:-4px 0 10px; line-height:1.4; }
    #msg { position:fixed; left:50%; bottom:92px; transform:translateX(-50%); background:var(--surface2); border:1px solid var(--border-active); padding:10px 16px; border-radius:12px; font-weight:700; font-size:0.9em; display:none; z-index:300; max-width:90vw; text-align:center; }
    #msg.err { border-color:var(--red); color:var(--red); }
    #avvDesk { display:none; background:rgba(232,162,60,0.15); color:var(--orange); border-radius:10px; padding:10px 12px; font-size:0.85em; font-weight:700; margin-bottom:12px; }
</style>
<script>
    var PREAVVISI = __PREAVVISI__;
    var ANTICIPI = __ANTICIPI__;
    var UNITA = __UNITA__;
    var RIPET = __RIPET__;
    var stato = { giorni: 14, voci: {}, ext: true };
    var $ = function(i) { return document.getElementById(i); };

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
    document.addEventListener('click', function(e) {
        const menu = $('extraMenu'), btn = document.querySelector('.menu-btn');
        if (menu && menu.style.display === 'block' && !menu.contains(e.target) && e.target !== btn) menu.style.display = 'none';
    });

    function quando(delta, giorno, d_it) {
        if (delta === 0) return 'Oggi';
        if (delta === 1) return 'Domani';
        if (delta === -1) return 'Ieri';
        return giorno + ' ' + d_it;
    }

    function rigaVoce(v, scaduta) {
        var d = document.createElement('div');
        d.className = 'voce' + (v.tipo === 'Scadenza' ? ' scad' : '') + (v.esterna ? ' ext' : '') + (v.fatta ? ' fatta' : '');
        var h = '<button class="spunta" ' + (v.esterna ? 'disabled' : '') + ' title="Fatta / da fare">' + (v.fatta ? '✓' : '') + '</button>';
        h += '<div class="corpo"><div class="tit">' + esc(v.titolo) + '</div><div class="meta">';
        h += '<span class="chip ' + (v.tipo === 'Scadenza' ? 's' : 'a') + '">' + esc(v.tipo) + '</span>';
        if (v.esterna) h += '<span class="chip e">' + esc(v.origine) + '</span>';
        if (scaduta) h += '<span class="ora">' + esc(quando(v.delta, v.giorno, v.d_it)) + '</span> ';
        if (v.ora) h += '<span class="ora">' + esc(v.ora) + '</span> ';
        if (v.fine) h += esc(v.fine) + ' ';
        if (v.importo) h += '· ' + esc(v.importo) + ' ';
        if (v.rip) h += '· 🔁 ' + esc(v.rip) + ' ';
        if (v.luogo) h += '· 📍 ' + esc(v.luogo);
        h += '</div>';
        if (v.note) h += '<div class="meta">' + esc(v.note.split('\\n')[0]) + '</div>';
        h += '</div>';
        if (!v.esterna && (scaduta || v.delta >= 0)) {
            h += '<div class="azioni"><button class="mini" data-p="giorno">+1g</button><button class="mini" data-p="settimana">+7g</button></div>';
        }
        d.innerHTML = h;
        d.querySelector('.spunta').onclick = function(e) { e.stopPropagation(); if (!v.esterna) fatto(v); };
        d.querySelectorAll('[data-p]').forEach(function(b) {
            b.onclick = function(e) { e.stopPropagation(); posticipa(v, b.getAttribute('data-p')); };
        });
        if (!v.esterna) d.onclick = function() { apriForm(v.id); };
        return d;
    }

    function sezione(titolo, sub, cls) {
        var s = document.createElement('div'); s.className = 'sez ' + (cls || '');
        s.innerHTML = '<span>' + esc(titolo) + '</span><span class="sub">' + esc(sub || '') + '</span>';
        return s;
    }

    function disegna(r) {
        var el = $('elenco'); el.innerHTML = '';
        stato.voci = r.voci || {};
        $('avvDesk').style.display = r.desktop_aperto ? 'block' : 'none';
        var tot = 0;
        var filtra = function(l) { return stato.ext ? l : l.filter(function(v) { return !v.esterna; }); };
        var sc = filtra(r.scaduti || []);
        if (sc.length) {
            el.appendChild(sezione('Scaduti / non completati', sc.length + '', 'rosso'));
            sc.forEach(function(v) { el.appendChild(rigaVoce(v, true)); }); tot += sc.length;
        }
        (r.gruppi || []).forEach(function(g) {
            var vv = filtra(g.voci); if (!vv.length) return;
            el.appendChild(sezione(quando(g.delta, g.giorno, g.d_it), g.delta === 0 || g.delta === 1 ? g.giorno + ' ' + g.d_it : ''));
            vv.forEach(function(v) { el.appendChild(rigaVoce(v, false)); }); tot += vv.length;
        });
        var pv = filtra(r.preavvisi || []);
        if (pv.length) {
            el.appendChild(sezione('In arrivo oltre il periodo', 'preavviso attivo'));
            pv.forEach(function(v) {
                var x = rigaVoce(v, true); x.querySelector('.meta').insertAdjacentHTML('beforeend', ' · tra ' + v.delta + ' giorni'); el.appendChild(x);
            });
            tot += pv.length;
        }
        if (!tot) el.innerHTML = '<div class="vuoto">Nessun promemoria nei prossimi ' + r.giorni + ' giorni.<br>Premi ＋ per aggiungerne uno.</div>';
        $('extRiga').style.display = r.n_ext ? 'flex' : 'none';
        $('extLbl').textContent = 'Mostra scadenze da altri moduli (' + (r.n_ext || 0) + ')';
    }

    async function chiama(url, corpo) {
        try {
            var opt = corpo === undefined ? {} : { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(corpo) };
            var res = await fetch(url, opt);
            if (res.status === 401 || res.redirected) { location.reload(); return null; }
            var j = await res.json(); j._status = res.status; return j;
        } catch (e) { return { ok: false, errore: 'Server non raggiungibile.' }; }
    }

    var ultimo = null;
    async function carica() {
        var r = await chiama('/api/promemoria/elenco?giorni=' + stato.giorni);
        if (!r) return;
        if (!r.ok) { msg(r.errore || 'Errore.', true); return; }
        ultimo = r; disegna(r);
    }
    async function fatto(v) {
        var r = await chiama('/api/promemoria/fatto', { id: v.id, data: v.d });
        if (!r) return;
        if (!r.ok) { msg(r.errore, true); return; }
        carica();
    }
    async function posticipa(v, modo) {
        var r = await chiama('/api/promemoria/posticipa', { id: v.id, data: v.d, modo: modo });
        if (!r) return;
        if (!r.ok) { msg(r.errore, true); return; }
        msg('Posticipata a ' + r.nuova_data); carica();
    }

    function riempiSelect(id, coppie) {
        var s = $(id); s.innerHTML = '';
        coppie.forEach(function(c) { var o = document.createElement('option'); o.value = c[1]; o.textContent = c[0]; s.appendChild(o); });
    }
    function aggiornaRip() {
        var r = $('fRip').value;
        $('rigaPers').style.display = r === 'Personalizzata' ? 'grid' : 'none';
        $('rigaRipFine').style.display = (r === 'Nessuna') ? 'none' : 'block';
        $('notaAv').style.display = r === 'Avanzata' ? 'block' : 'none';
    }
    var editId = '';
    function apriForm(id) {
        editId = id || '';
        var v = id ? stato.voci[id] : null;
        var oggi = (ultimo && ultimo.oggi) || new Date().toISOString().slice(0, 10);
        $('fTitoloH').textContent = v ? 'Modifica promemoria' : 'Nuovo promemoria';
        $('fTit').value = v ? v.titolo : '';
        $('fTipo').value = v ? v.tipo : 'Appuntamento';
        $('fData').value = v ? v.data : oggi;
        $('fOra').value = v ? v.ora : '';
        $('fOraFine').value = v ? v.ora_fine : '';
        $('fDataFine').value = v ? v.data_fine : '';
        $('fImp').value = v ? v.importo : '';
        var opt = $('fRip').querySelector('option[value="Avanzata"]');
        if (opt) opt.remove();
        if (v && v.ripetizione === 'Avanzata') {
            var o = document.createElement('option'); o.value = 'Avanzata'; o.textContent = 'Avanzata (da desktop/import)'; $('fRip').appendChild(o);
            $('notaAv').textContent = 'Regola: ' + (v.rip_testo || '') + '. Si modifica solo dal desktop; cambiando la ripetizione qui viene sostituita.';
        }
        $('fRip').value = v ? v.ripetizione : 'Nessuna';
        $('fRipN').value = v ? v.rip_n : 1;
        $('fRipU').value = v ? v.rip_unita : 'mesi';
        $('fRipFine').value = v ? v.rip_fine : '';
        $('fPre').value = v ? v.preavviso : 0;
        $('fAnt').value = v ? v.anticipo_min : 15;
        $('fLuogo').value = v ? v.luogo : '';
        $('fNote').value = v ? v.note : '';
        $('fEmail').checked = v ? v.email : false;
        $('bElimina').style.display = v ? 'block' : 'none';
        aggiornaRip();
        $('velo').style.display = 'block';
        document.body.style.overflow = 'hidden';
        if (!v) setTimeout(function() { $('fTit').focus(); }, 50);
    }
    function chiudiForm() { $('velo').style.display = 'none'; document.body.style.overflow = ''; }
    async function salva() {
        var corpo = {
            id: editId, titolo: $('fTit').value, tipo: $('fTipo').value, data: $('fData').value,
            ora: $('fOra').value, ora_fine: $('fOraFine').value, data_fine: $('fDataFine').value,
            importo: $('fImp').value, ripetizione: $('fRip').value, rip_n: $('fRipN').value,
            rip_unita: $('fRipU').value, rip_fine: $('fRipFine').value, preavviso: $('fPre').value,
            anticipo_min: $('fAnt').value, luogo: $('fLuogo').value, note: $('fNote').value, email: $('fEmail').checked
        };
        var r = await chiama('/api/promemoria/salva', corpo);
        if (!r) return;
        if (!r.ok) { msg(r.errore, true); return; }
        chiudiForm(); msg('Salvato'); carica();
    }
    async function elimina() {
        var v = stato.voci[editId]; if (!v) return;
        var t = "Eliminare '" + v.titolo + "'?" + (v.ripetizione !== 'Nessuna' ? '\\nLa voce si ripete: verranno eliminate tutte le occorrenze.' : '');
        if (!confirm(t)) return;
        var r = await chiama('/api/promemoria/elimina', { id: editId });
        if (!r) return;
        if (!r.ok) { msg(r.errore, true); return; }
        chiudiForm(); msg('Eliminato'); carica();
    }

    document.addEventListener('DOMContentLoaded', function() {
        applyTheme((function() { try { return localStorage.getItem('theme') || 'dark'; } catch (e) { return 'dark'; } })());
        try { stato.giorni = parseInt(localStorage.getItem('pm_giorni')) || 14; stato.ext = localStorage.getItem('pm_ext') !== '0'; } catch (e) {}
        riempiSelect('fPre', PREAVVISI); riempiSelect('fAnt', ANTICIPI);
        RIPET.forEach(function(x) { var o = document.createElement('option'); o.value = x; o.textContent = x; $('fRip').appendChild(o); });
        UNITA.forEach(function(x) { var o = document.createElement('option'); o.value = x; o.textContent = x; $('fRipU').appendChild(o); });
        $('selGiorni').value = String(stato.giorni);
        $('selGiorni').onchange = function() { stato.giorni = parseInt(this.value); try { localStorage.setItem('pm_giorni', this.value); } catch (e) {} carica(); };
        $('chkExt').checked = stato.ext;
        $('chkExt').onchange = function() { stato.ext = this.checked; try { localStorage.setItem('pm_ext', this.checked ? '1' : '0'); } catch (e) {} if (ultimo) disegna(ultimo); };
        $('fRip').onchange = aggiornaRip;
        $('velo').addEventListener('mousedown', function(e) { if (e.target === $('velo')) chiudiForm(); });
        carica();
        document.addEventListener('visibilitychange', function() { if (!document.hidden && $('velo').style.display !== 'block') carica(); });
    });
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
    <div class="header-title">🗓️ Promemoria</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div id="avvDesk">⚠️ La finestra Promemoria è aperta sul desktop: per modificare dal web va chiusa.</div>
    <div class="barra">
        <select id="selGiorni">
            <option value="7">Prossimi 7 giorni</option>
            <option value="14">Prossimi 14 giorni</option>
            <option value="30">Prossimi 30 giorni</option>
            <option value="60">Prossimi 60 giorni</option>
            <option value="90">Prossimi 90 giorni</option>
        </select>
    </div>
    <label class="chk" id="extRiga" style="display:none"><input type="checkbox" id="chkExt"><span id="extLbl"></span></label>
    <div id="elenco"></div>
</main>
<button id="fab" onclick="apriForm('')" title="Nuovo promemoria">＋</button>
<div id="velo">
  <div id="form">
    <h3 id="fTitoloH">Nuovo promemoria</h3>
    <div class="campo"><label>Titolo</label><input id="fTit" type="text" maxlength="35" autocomplete="off"></div>
    <div class="campo"><label>Tipo (prova)</label><select id="fTipo"><option>Appuntamento</option><option>Scadenza</option></select></div>
    <div class="campo"><label>Data</label><input id="fData" type="date"></div>
    <div class="due">
        <div class="campo"><label>Ora inizio</label><input id="fOra" type="time"></div>
        <div class="campo"><label>Ora fine</label><input id="fOraFine" type="time"></div>
    </div>
    <div class="due">
        <div class="campo"><label>Data fine (più giorni)</label><input id="fDataFine" type="date"></div>
        <div class="campo"><label>Importo (€)</label><input id="fImp" type="text" inputmode="decimal" maxlength="8" placeholder="0,00"></div>
    </div>
    <div class="campo"><label>Ripetizione</label><select id="fRip"></select></div>
    <div id="notaAv" class="nota-av" style="display:none"></div>
    <div id="rigaPers" class="due" style="display:none">
        <div class="campo"><label>Ogni</label><input id="fRipN" type="number" min="1" max="99" value="1"></div>
        <div class="campo"><label>Unità</label><select id="fRipU"></select></div>
    </div>
    <div id="rigaRipFine" class="campo" style="display:none"><label>Ripeti fino al (facoltativo)</label><input id="fRipFine" type="date"></div>
    <div class="due">
        <div class="campo"><label>Preavviso (giorni)</label><select id="fPre"></select></div>
        <div class="campo"><label>Avviso orario (desktop)</label><select id="fAnt"></select></div>
    </div>
    <div class="campo"><label>Luogo</label><input id="fLuogo" type="text" maxlength="__MAXLUOGO__" autocomplete="off"></div>
    <div class="campo"><label>Note (max 150)</label><textarea id="fNote" maxlength="150"></textarea></div>
    <label class="chk"><input type="checkbox" id="fEmail"> Invia anche per email (dal programma desktop)</label>
    <div class="btns">
        <button class="btn" onclick="chiudiForm()">Annulla</button>
        <button class="btn verde" onclick="salva()">💾 Salva</button>
    </div>
    <button class="btn rosso" id="bElimina" style="margin-top:8px;display:none" onclick="elimina()">🗑️ Elimina</button>
  </div>
</div>
<div id="msg"></div>
</body>
</html>
"""

def pagina_promemoria_web(self):
    return (_PAGINA
            .replace("__PREAVVISI__", json.dumps([[e, n] for e, n in gp.PREAVVISI], ensure_ascii=False))
            .replace("__ANTICIPI__", json.dumps([[e, n] for e, n in gp.ANTICIPI_ORA], ensure_ascii=False))
            .replace("__UNITA__", json.dumps(gp.UNITA_RIP, ensure_ascii=False))
            .replace("__RIPET__", json.dumps([r for r in gp.RIPETIZIONI], ensure_ascii=False))
            .replace("__MAXLUOGO__", str(_ics.MAX_LUOGO))
            .replace("__ANNO__", str(datetime.date.today().year)))
