#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import ast
import datetime
import threading

from moduli import web_ricorrenze as _wr

_LOCK = threading.RLock()
PASTI = ("colazione", "pranzo", "cena", "spuntino")
_GIORNI = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
_ALI_CACHE = {"t": 0.0, "righe": None}


def _percorsi():
    import __main__ as _app
    db_dir = _app.DB_DIR
    utente = "Generico"
    try:
        ua = os.path.join(db_dir, "utente_attivo.json")
        if os.path.exists(ua):
            with open(ua, encoding="utf-8") as f:
                utente = json.load(f).get("utente", "Generico")
    except Exception:
        pass
    if utente != "Generico":
        d = os.path.join(db_dir, "utenti", utente)
        return {"dieta": os.path.join(d, "dieta.json"), "peso": os.path.join(d, "peso.json"),
                "fabb": os.path.join(d, "fabbisogno.json"), "ped": os.path.join(d, "pedometro.json"),
                "custom": os.path.join(d, "alimenti_custom.json")}
    return {"dieta": os.path.join(db_dir, "dieta_piano.json"), "peso": os.path.join(db_dir, "peso_storico.json"),
            "fabb": os.path.join(db_dir, "fabbisogno_dati.json"), "ped": os.path.join(db_dir, "pedometro.json"),
            "custom": os.path.join(db_dir, "alimenti_custom.json")}


def _leggi(f, default):
    if os.path.exists(f) and os.path.getsize(f) > 0:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            raise ValueError(f"il file {os.path.basename(f)} risulta illeggibile o corrotto: nessuna modifica effettuata")
    return default


def _sicuro(con_codice):
    def deco(fn):
        def w(*a, **k):
            try:
                return fn(*a, **k)
            except Exception as e:
                r = {"ok": False, "errore": f"Errore: {e}"}
                return (r, 500) if con_codice else r
        w.__name__ = fn.__name__
        return w
    return deco


def _scrivi(f, dati):
    os.makedirs(os.path.dirname(f), exist_ok=True)
    tmp = f + ".web.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(dati, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, f)


def _dieta_desktop_aperto(self):
    try:
        p = getattr(self, "_dieta_popup", None)
        return bool(p and p.winfo_exists())
    except Exception:
        return False


_BLOCCO_DIETA = ({"ok": False, "errore": "Chiudi la finestra Dieta sul desktop prima di modificare dal web."}, 409)


def _piano_vuoto():
    return [{"titolo": "Settimana 1", "giorni": [[g, "", "", "", "", 0, 0, 0, 0, 0, 0] for g in _GIORNI]}], {}


def _carica_piano(p):
    d = _leggi(p["dieta"], None)
    if isinstance(d, dict) and isinstance(d.get("piano"), list) and d["piano"]:
        return d["piano"], d.get("composizioni", {}) or {}
    return _piano_vuoto()


def _num(v):
    try:
        return float(str(v).strip().replace(",", "."))
    except (ValueError, TypeError):
        return None


def _data_ok(s):
    try:
        datetime.datetime.strptime(s, "%d-%m-%Y")
        return True
    except (ValueError, TypeError):
        return False


def _ordina_data(s):
    try:
        return datetime.datetime.strptime(s, "%d-%m-%Y")
    except (ValueError, TypeError):
        return datetime.datetime.min


def _alimenti(p):
    import __main__ as _app
    ora = time.time()
    if _ALI_CACHE["righe"] is None or ora - _ALI_CACHE["t"] > 3600:
        righe = []
        try:
            import requests
            r = requests.get(getattr(_app, "ALIMENTI", ""), timeout=6)
            r.raise_for_status()
            t = r.text
            if "ALIMENTI_DB =" in t:
                righe = ast.literal_eval(t[t.find("["):t.rfind("]") + 1])
            else:
                righe = r.json()
        except Exception:
            righe = _ALI_CACHE["righe"] or []
        _ALI_CACHE.update({"t": ora, "righe": righe})
    custom = _leggi(p["custom"], [])
    nomi_c = {r[0] for r in custom if isinstance(r, list) and r}
    tutte = [list(r) for r in _ALI_CACHE["righe"] if r and r[0] not in nomi_c] + \
            [list(r) for r in custom if isinstance(r, list) and len(r) >= 8]
    return tutte


def _giorno_json(riga, comp, s, g):
    pasti = {}
    for i, pk in enumerate(PASTI):
        items = comp.get(f"{s}_{g}_{pk}", []) or []
        pasti[pk] = {"testo": riga[1 + i] if len(riga) > 1 + i else "", "items": items}
    macro = [riga[5 + i] if len(riga) > 5 + i else 0 for i in range(6)]
    return {"nome": riga[0], "pasti": pasti, "macro": macro}


@_sicuro(False)
def dieta_web_dati(self):
    p = _percorsi()
    with _LOCK:
        piano, comp = _carica_piano(p)
        out = []
        for s, sett in enumerate(piano):
            out.append({"titolo": sett.get("titolo", f"Settimana {s + 1}"),
                        "giorni": [_giorno_json(r, comp, s, g) for g, r in enumerate(sett.get("giorni", []))]})
        peso = _leggi(p["peso"], {})
        if isinstance(peso, list):
            peso = {"pesate": peso}
        ped = _leggi(p["ped"], {})
        fabb = _leggi(p["fabb"], {})
    return {
        "ok": True, "piano": out,
        "peso": {"pesate": sorted(peso.get("pesate", []), key=lambda r: _ordina_data(r.get("data", ""))),
                 "altezza": peso.get("altezza", ""), "obiettivo": peso.get("obiettivo", "")},
        "passi": {"db": ped.get("passi", {}), "obiettivo": int(ped.get("obiettivo_default", 10000) or 10000)},
        "fabb": fabb, "oggi": datetime.date.today().strftime("%d-%m-%Y"),
        "oggi_iso": datetime.date.today().isoformat(),
    }


@_sicuro(False)
def dieta_web_alimenti(self, q):
    p = _percorsi()
    q = (q or "").strip().lower()
    righe = _alimenti(p)
    if q:
        righe = [r for r in righe if q in str(r[0]).lower() or q in str(r[1]).lower()]
    righe.sort(key=lambda r: str(r[0]).lower())
    return {"ok": True, "alimenti": [r[:8] for r in righe[:40]], "totale": len(righe)}


@_sicuro(True)
def dieta_web_alimento_custom(self, d):
    if _dieta_desktop_aperto(self):
        return _BLOCCO_DIETA
    nome = str(d.get("nome", "")).strip()
    cat = str(d.get("categoria", "") or "Personalizzati").strip()
    vals = [_num(d.get(k)) for k in ("kcal", "prot", "grassi", "carb", "zucc", "fibre")]
    if not nome or any(v is None or v < 0 for v in vals):
        return {"ok": False, "errore": "Nome e valori nutrizionali (per 100 g) validi richiesti."}, 400
    p = _percorsi()
    with _LOCK:
        custom = [r for r in _leggi(p["custom"], []) if isinstance(r, list) and r and r[0] != nome]
        custom.append([nome, cat] + vals)
        _scrivi(p["custom"], custom)
    return {"ok": True}, 200


@_sicuro(True)
def dieta_web_giorno(self, d):
    if _dieta_desktop_aperto(self):
        return _BLOCCO_DIETA
    try:
        s, g = int(d.get("s")), int(d.get("g"))
    except (TypeError, ValueError):
        return {"ok": False, "errore": "Giorno non valido."}, 400
    p = _percorsi()
    with _LOCK:
        piano, comp = _carica_piano(p)
        if not (0 <= s < len(piano)) or not (0 <= g < len(piano[s].get("giorni", []))):
            return {"ok": False, "errore": "Giorno non trovato."}, 404
        riga = piano[s]["giorni"][g]
        while len(riga) < 11:
            riga.append(0)
        pasti_in = d.get("pasti") or {}
        tot = [0.0] * 6
        ci_sono_items = False
        for i, pk in enumerate(PASTI):
            pin = pasti_in.get(pk) or {}
            items = []
            for it in pin.get("items") or []:
                try:
                    nome = str(it[0]).strip()
                    vals = [float(x) for x in it[1:8]]
                    if not nome or len(vals) != 7 or vals[0] <= 0 or any(v < 0 for v in vals):
                        raise ValueError
                except (ValueError, TypeError, IndexError):
                    return {"ok": False, "errore": "Composizione pasto non valida."}, 400
                items.append([nome] + vals)
            chiave = f"{s}_{g}_{pk}"
            if items:
                comp[chiave] = items
                riga[1 + i] = ", ".join(x[0] for x in items)
                ci_sono_items = True
                for x in items:
                    for ti in range(6):
                        tot[ti] += x[2 + ti]
            else:
                comp.pop(chiave, None)
                riga[1 + i] = str(pin.get("testo", "")).strip()
        if ci_sono_items:
            for ti in range(6):
                riga[5 + ti] = round(tot[ti])
        else:
            macro = d.get("macro") or []
            for ti in range(6):
                v = _num(macro[ti]) if ti < len(macro) else None
                riga[5 + ti] = round(v) if v is not None and v >= 0 else 0
        _scrivi(p["dieta"], {"piano": piano, "composizioni": comp})
    return {"ok": True}, 200


@_sicuro(True)
def dieta_web_peso(self, d):
    if _dieta_desktop_aperto(self):
        return _BLOCCO_DIETA
    p = _percorsi()
    with _LOCK:
        peso = _leggi(p["peso"], {})
        if isinstance(peso, list):
            peso = {"pesate": peso}
        pesate = peso.get("pesate", [])
        az = d.get("azione")
        if az == "salva":
            data = str(d.get("data", "")).strip()
            v = _num(d.get("peso"))
            if not _data_ok(data) or v is None or v <= 0 or v > 500:
                return {"ok": False, "errore": "Data (gg-mm-aaaa) e peso validi richiesti."}, 400
            pesate = [r for r in pesate if r.get("data") != data] + [{"data": data, "peso": round(v, 1)}]
        elif az == "elimina":
            pesate = [r for r in pesate if r.get("data") != str(d.get("data", ""))]
        elif az == "azzera":
            pesate = []
        elif az == "meta":
            peso["altezza"] = str(d.get("altezza", "")).strip()
            peso["obiettivo"] = str(d.get("obiettivo", "")).strip()
        else:
            return {"ok": False, "errore": "Azione non valida."}, 400
        pesate.sort(key=lambda r: _ordina_data(r.get("data", "")))
        peso["pesate"] = pesate
        _scrivi(p["peso"], {"pesate": pesate, "altezza": peso.get("altezza", ""),
                            "obiettivo": peso.get("obiettivo", "")})
    return {"ok": True}, 200


@_sicuro(True)
def dieta_web_passi(self, d):
    if _dieta_desktop_aperto(self):
        return _BLOCCO_DIETA
    p = _percorsi()
    with _LOCK:
        ped = _leggi(p["ped"], {})
        passi = ped.get("passi", {})
        ob_def = int(ped.get("obiettivo_default", 10000) or 10000)
        az = d.get("azione")
        if az == "salva":
            data = str(d.get("data", "")).strip()
            try:
                n = int(str(d.get("passi", "")).strip().replace(".", "").replace(",", ""))
                if n < 0 or n > 200000:
                    raise ValueError
            except ValueError:
                return {"ok": False, "errore": "Numero di passi non valido."}, 400
            if not _data_ok(data):
                return {"ok": False, "errore": "Data non valida (gg-mm-aaaa)."}, 400
            try:
                ob = int(str(d.get("obiettivo", "")).strip().replace(".", "").replace(",", ""))
                if ob <= 0:
                    ob = ob_def
            except ValueError:
                ob = ob_def
            passi[data] = {"passi": n, "obiettivo": ob, "note": str(d.get("note", "")).strip()}
        elif az == "elimina":
            passi.pop(str(d.get("data", "")), None)
        elif az == "obiettivo":
            try:
                ob_def = int(str(d.get("obiettivo", "")).strip().replace(".", ""))
                if ob_def <= 0:
                    raise ValueError
            except ValueError:
                return {"ok": False, "errore": "Obiettivo non valido."}, 400
        else:
            return {"ok": False, "errore": "Azione non valida."}, 400
        _scrivi(p["ped"], {"passi": passi, "obiettivo_default": ob_def})
    return {"ok": True}, 200


@_sicuro(True)
def dieta_web_fabb(self, d):
    if _dieta_desktop_aperto(self):
        return _BLOCCO_DIETA
    sesso = "Uomo" if d.get("sesso") == "Uomo" else "Donna"
    vals = [_num(d.get(k)) for k in ("peso", "altezza", "eta")]
    if any(v is None or v <= 0 for v in vals):
        return {"ok": False, "errore": "Peso, altezza ed età devono essere valori positivi."}, 400
    p = _percorsi()
    with _LOCK:
        _scrivi(p["fabb"], {"sesso": sesso, "peso": str(d.get("peso")).strip(), "altezza": str(d.get("altezza")).strip(),
                            "eta": str(d.get("eta")).strip()})
    return {"ok": True}, 200


_JS = r"""
    var D = null, tabD = 'piano', sett = 0, ed = null, picker = null;
    var NOMI_PASTI = {colazione: 'Colazione', pranzo: 'Pranzo', cena: 'Cena', spuntino: 'Spuntino'};
    var PASTI = ['colazione', 'pranzo', 'cena', 'spuntino'];
    function f1(v) { return (Math.round(v * 10) / 10).toLocaleString('it-IT'); }
    function iso2dmy(s) { var p = s.split('-'); return p.length === 3 ? p[2] + '-' + p[1] + '-' + p[0] : s; }
    function sortKey(s) { var p = s.split('-'); return p[2] + p[1] + p[0]; }
    async function carica() { var j = await chiama('/api/dieta/dati'); if (!j) return; D = j; if (sett >= D.piano.length) sett = 0; disegna(); }
    function setTabD(t) { tabD = t; disegna(); }
    function disegna() {
        var t = ['piano', 'peso', 'passi', 'fabb'], n = {piano: '🍽️ Piano', peso: '⚖️ Peso', passi: '👟 Passi', fabb: '🔥 Fabbisogno'};
        var h = '<div class="tabs">';
        t.forEach(function(k) { h += '<button class="' + (k === tabD ? 'on' : '') + '" onclick="setTabD(\'' + k + '\')">' + n[k] + '</button>'; });
        h += '</div>';
        h += tabD === 'piano' ? htmlPiano() : tabD === 'peso' ? htmlPeso() : tabD === 'passi' ? htmlPassi() : htmlFabb();
        $('contenuto').innerHTML = h;
        if (tabD === 'fabb') calcFabb();
        if (tabD === 'peso') calcBmi();
    }
    function htmlPiano() {
        var s = D.piano[sett], h = '<div class="campo"><label>Settimana</label><select onchange="sett=+this.value;disegna()">';
        D.piano.forEach(function(x, i) { h += '<option value="' + i + '"' + (i === sett ? ' selected' : '') + '>' + esc(x.titolo) + '</option>'; });
        h += '</select></div>';
        var tot = [0, 0, 0, 0, 0, 0], nz = 0;
        s.giorni.forEach(function(g) { if (g.macro[0] > 0) { nz++; g.macro.forEach(function(v, i) { tot[i] += v; }); } });
        if (nz) h += '<div class="riepilogo"><span>Media/giorno</span><b>' + Math.round(tot[0] / nz) + ' kcal</b></div><div class="meta" style="margin:-4px 2px 10px">Prot ' + Math.round(tot[1] / nz) + 'g · Grassi ' + Math.round(tot[2] / nz) + 'g · Carb ' + Math.round(tot[3] / nz) + 'g · Zucch ' + Math.round(tot[4] / nz) + 'g · Fibre ' + Math.round(tot[5] / nz) + 'g</div>';
        s.giorni.forEach(function(g, gi) {
            h += '<div class="ric" onclick="apriGiorno(' + gi + ')"><div class="riga1"><span class="cat">' + esc(g.nome) + '</span><span class="imp">' + g.macro[0] + ' kcal</span></div>';
            PASTI.forEach(function(pk) { var tx = g.pasti[pk].testo; h += '<div class="meta"><b>' + NOMI_PASTI[pk] + ':</b> ' + (tx ? esc(tx) : '—') + '</div>'; });
            h += '<div class="meta">P ' + g.macro[1] + ' · G ' + g.macro[2] + ' · C ' + g.macro[3] + ' · Z ' + g.macro[4] + ' · F ' + g.macro[5] + '</div></div>';
        });
        return h;
    }
    function copiaGiorno(gi) {
        var g = D.piano[sett].giorni[gi], pasti = {};
        PASTI.forEach(function(pk) { pasti[pk] = {testo: g.pasti[pk].testo, items: JSON.parse(JSON.stringify(g.pasti[pk].items))}; });
        return {s: sett, g: gi, nome: g.nome, pasti: pasti, macro: g.macro.slice()};
    }
    function apriGiorno(gi) { ed = copiaGiorno(gi); disegnaGiorno(); $('velo').style.display = 'block'; document.body.style.overflow = 'hidden'; }
    function chiudi() { $('velo').style.display = 'none'; document.body.style.overflow = ''; ed = null; }
    function chiudi2() { $('velo2').style.display = 'none'; picker = null; }
    function totaliEd() {
        var t = [0, 0, 0, 0, 0, 0], ci = false;
        PASTI.forEach(function(pk) { ed.pasti[pk].items.forEach(function(it) { ci = true; for (var i = 0; i < 6; i++) t[i] += it[2 + i]; }); });
        return ci ? t : null;
    }
    function disegnaGiorno() {
        var h = '<div class="sh"><h3>' + esc(ed.nome) + ' · ' + esc(D.piano[sett].titolo) + '</h3><button class="x" onclick="chiudi()">✕</button></div>';
        PASTI.forEach(function(pk) {
            var p = ed.pasti[pk];
            h += '<div class="pasto"><div class="riga1"><b>' + NOMI_PASTI[pk] + '</b><button class="btn no mini" onclick="apriPicker(\'' + pk + '\')">＋ Alimento</button></div>';
            if (p.items.length) {
                p.items.forEach(function(it, i) {
                    h += '<div class="dt"><span>' + esc(it[0]) + ' · ' + f1(it[1]) + ' g</span><span>' + f1(it[2]) + ' kcal <a class="rm" onclick="rimuovi(\'' + pk + '\',' + i + ')">✕</a></span></div>';
                });
            } else h += '<input type="text" value="' + esc(p.testo) + '" placeholder="Descrizione libera" oninput="ed.pasti[\'' + pk + '\'].testo=this.value" autocomplete="off">';
            h += '</div>';
        });
        var t = totaliEd();
        if (t) h += '<div class="riepilogo" id="totEd"><span>Totale giornata</span><b>' + Math.round(t[0]) + ' kcal</b></div><div class="meta">P ' + f1(t[1]) + ' · G ' + f1(t[2]) + ' · C ' + f1(t[3]) + ' · Z ' + f1(t[4]) + ' · F ' + f1(t[5]) + '</div>';
        else {
            h += '<div class="meta" style="margin-top:8px">Valori manuali (senza composizione)</div><div class="tre">';
            ['Kcal', 'Prot', 'Grassi', 'Carb', 'Zucc', 'Fibre'].forEach(function(l, i) { h += '<div class="campo"><label>' + l + '</label><input type="text" inputmode="decimal" id="mc' + i + '" value="' + ed.macro[i] + '"></div>'; });
            h += '</div>';
        }
        h += '<div class="btns"><button class="btn no" onclick="chiudi()">Annulla</button><button class="btn ok" id="btnSalvaGiorno" onclick="salvaGiorno()">Salva</button></div>';
        $('scheda').innerHTML = h;
    }
    function rimuovi(pk, i) { ed.pasti[pk].items.splice(i, 1); disegnaGiorno(); }
    async function salvaGiorno() {
        var macro = ed.macro;
        if (!totaliEd()) macro = [0, 1, 2, 3, 4, 5].map(function(i) { return $('mc' + i).value; });
        var j = await chiama('/api/dieta/giorno', {s: ed.s, g: ed.g, pasti: ed.pasti, macro: macro});
        if (!j) return;
        chiudi(); msg('Giorno salvato'); carica();
    }
    function apriPicker(pk) {
        picker = {pk: pk, sel: null};
        $('scheda2').innerHTML = '<div class="sh"><h3>Aggiungi a ' + NOMI_PASTI[pk] + '</h3><button class="x" onclick="chiudi2()">✕</button></div><div class="campo"><input type="text" id="qAli" placeholder="Cerca alimento…" oninput="cercaAli()" autocomplete="off"></div><div id="risAli"></div><div id="selAli"></div><div class="meta" style="margin-top:8px">Non lo trovi? <a class="rm" style="color:var(--blue)" onclick="formCustom()">Crea alimento personalizzato</a></div>';
        $('velo2').style.display = 'block'; cercaAli();
    }
    var tAli = null;
    function cercaAli() {
        clearTimeout(tAli);
        tAli = setTimeout(async function() {
            var j = await chiama('/api/dieta/alimenti?q=' + encodeURIComponent($('qAli').value));
            if (!j) return;
            var h = '';
            if (!j.alimenti.length) h = '<div class="vuoto">Nessun alimento trovato.</div>';
            picker.lista = j.alimenti;
            j.alimenti.forEach(function(a, i) { h += '<div class="dt ali" onclick="scegliAli(' + i + ')"><span>' + esc(a[0]) + '</span><span>' + f1(a[2]) + ' kcal/100g</span></div>'; });
            $('risAli').innerHTML = h;
        }, 250);
    }
    function scegliAli(i) {
        var a = picker.lista[i]; picker.sel = a;
        $('selAli').innerHTML = '<div class="riepilogo" style="margin-top:10px"><span>' + esc(a[0]) + '</span><input type="text" inputmode="decimal" id="gAli" placeholder="grammi" style="width:90px"></div><button class="btn ok" id="btnAggAli" style="width:100%" onclick="aggiungiAli()">Aggiungi</button>';
    }
    function aggiungiAli() {
        var g = parseFloat($('gAli').value.replace(',', '.'));
        if (!(g > 0)) { msg('Inserisci i grammi', true); return; }
        var a = picker.sel, f = g / 100, row = [a[0], g];
        for (var i = 2; i < 8; i++) row.push(Math.round(a[i] * f * 10) / 10);
        ed.pasti[picker.pk].items.push(row);
        chiudi2(); disegnaGiorno();
    }
    function formCustom() {
        var h = '<div class="sh"><h3>Nuovo alimento (per 100 g)</h3><button class="x" onclick="apriPicker(picker.pk)">←</button></div><div class="campo"><label>Nome</label><input type="text" id="cNome"></div><div class="tre">';
        ['Kcal', 'Prot', 'Grassi', 'Carb', 'Zucc', 'Fibre'].forEach(function(l, i) { h += '<div class="campo"><label>' + l + '</label><input type="text" inputmode="decimal" id="cv' + i + '" value="0"></div>'; });
        h += '</div><button class="btn ok" id="btnSalvaCustom" style="width:100%" onclick="salvaCustom()">Salva alimento</button>';
        $('scheda2').innerHTML = h;
    }
    async function salvaCustom() {
        var k = ['kcal', 'prot', 'grassi', 'carb', 'zucc', 'fibre'], c = {nome: $('cNome').value};
        k.forEach(function(x, i) { c[x] = $('cv' + i).value; });
        var j = await chiama('/api/dieta/alimento_custom', c);
        if (!j) return;
        msg('Alimento salvato'); apriPicker(picker.pk);
    }
    function bmiCat(b) { return b < 18.5 ? 'Sottopeso' : b < 25 ? 'Normopeso' : b < 30 ? 'Sovrappeso' : b < 35 ? 'Obesità I' : b < 40 ? 'Obesità II' : 'Obesità III'; }
    function htmlPeso() {
        var P = D.peso, ps = P.pesate, h = '<div class="scad"><div class="due"><div class="campo"><label>Data</label><input type="date" id="pData" value="' + D.oggi_iso + '"></div><div class="campo"><label>Peso (kg)</label><input type="text" inputmode="decimal" id="pPeso" oninput="calcBmi()" placeholder="0,0"></div></div>';
        h += '<div class="due"><div class="campo"><label>Altezza (cm)</label><input type="text" inputmode="decimal" id="pAlt" value="' + esc(P.altezza) + '" oninput="calcBmi()"></div><div class="campo"><label>Obiettivo (kg)</label><input type="text" inputmode="decimal" id="pOb" value="' + esc(P.obiettivo) + '"></div></div>';
        h += '<div class="meta" id="bmiTxt" style="margin-bottom:8px">BMI: —</div><div class="btns" style="margin-top:0"><button class="btn no" onclick="salvaMeta()">Salva altezza/obiettivo</button><button class="btn ok" id="btnAggPeso" onclick="aggiungiPeso()">Aggiungi pesata</button></div></div>';
        if (ps.length) {
            var pesi = ps.map(function(r) { return r.peso; }), min = Math.min.apply(null, pesi), max = Math.max.apply(null, pesi);
            h += '<div class="riepilogo"><span>Min ' + f1(min) + ' · Max ' + f1(max) + ' · Media ' + f1(pesi.reduce(function(a, b) { return a + b; }, 0) / pesi.length) + '</span><b>' + ps.length + ' pesate</b></div>';
            h += graficoPeso(ps);
            ps.slice().reverse().forEach(function(r, i, arr) {
                var prev = arr[i + 1], dv = prev ? Math.round((r.peso - prev.peso) * 10) / 10 : null;
                h += '<div class="dt"><span>' + esc(r.data) + '</span><span><b>' + f1(r.peso) + ' kg</b>' + (dv === null ? '' : ' <span class="' + (dv > 0 ? 'neg' : dv < 0 ? 'pos' : '') + '">' + (dv > 0 ? '+' : '') + dv + '</span>') + ' <a class="rm" onclick="eliminaPeso(\'' + esc(r.data) + '\')">✕</a></span></div>';
            });
            h += '<div class="btns"><button class="btn del" onclick="azzeraPeso()">🗑 Azzera storico</button></div>';
        } else h += '<div class="vuoto">Nessuna pesata registrata.</div>';
        return h;
    }
    function graficoPeso(ps) {
        if (ps.length < 2) return '';
        var W = 320, H = 120, pad = 22, pesi = ps.map(function(r) { return r.peso; });
        var mn = Math.min.apply(null, pesi), mx = Math.max.apply(null, pesi); if (mx === mn) { mx += 1; mn -= 1; }
        var pts = ps.map(function(r, i) { return [pad + i * (W - 2 * pad) / (ps.length - 1), H - pad - (r.peso - mn) * (H - 2 * pad) / (mx - mn)]; });
        var s = '<svg viewBox="0 0 ' + W + ' ' + H + '" style="width:100%;background:var(--surface);border:1px solid var(--border);border-radius:12px;margin-bottom:8px"><polyline fill="none" stroke="var(--blue)" stroke-width="2" points="' + pts.map(function(p) { return p[0] + ',' + p[1]; }).join(' ') + '"/>';
        pts.forEach(function(p) { s += '<circle cx="' + p[0] + '" cy="' + p[1] + '" r="3" fill="var(--gold)"/>'; });
        s += '<text x="4" y="14" font-size="10" fill="var(--text-mid)">' + f1(mx) + '</text><text x="4" y="' + (H - 6) + '" font-size="10" fill="var(--text-mid)">' + f1(mn) + '</text></svg>';
        return s;
    }
    function calcBmi() {
        var el = $('bmiTxt'); if (!el) return;
        var p = parseFloat(($('pPeso').value || '').replace(',', '.')), h = parseFloat(($('pAlt').value || '').replace(',', '.')) / 100;
        if (!p && D.peso.pesate.length) p = D.peso.pesate[D.peso.pesate.length - 1].peso;
        if (p > 0 && h > 0) { var b = Math.round(p / (h * h) * 10) / 10; el.textContent = 'BMI: ' + b + ' — ' + bmiCat(b); } else el.textContent = 'BMI: —';
    }
    async function aggiungiPeso() {
        var m = await chiama('/api/dieta/peso', {azione: 'meta', altezza: $('pAlt').value, obiettivo: $('pOb').value});
        if (!m) return;
        var j = await chiama('/api/dieta/peso', {azione: 'salva', data: iso2dmy($('pData').value), peso: $('pPeso').value});
        if (!j) return; msg('Pesata salvata'); carica();
    }
    async function salvaMeta() { var j = await chiama('/api/dieta/peso', {azione: 'meta', altezza: $('pAlt').value, obiettivo: $('pOb').value}); if (!j) return; msg('Salvato'); carica(); }
    async function eliminaPeso(d) { var j = await chiama('/api/dieta/peso', {azione: 'elimina', data: d}); if (!j) return; msg('Pesata eliminata'); carica(); }
    function azzeraPeso() { apriModalConferma('Eliminare TUTTE le pesate?\nL\'operazione non è reversibile.', async function() { var j = await chiama('/api/dieta/peso', {azione: 'azzera'}); if (!j) return; msg('Storico azzerato'); carica(); }); }
    function htmlPassi() {
        var P = D.passi, chiavi = Object.keys(P.db).sort(function(a, b) { return sortKey(b).localeCompare(sortKey(a)); });
        var h = '<div class="scad"><div class="due"><div class="campo"><label>Data</label><input type="date" id="sData" value="' + D.oggi_iso + '"></div><div class="campo"><label>Passi</label><input type="text" inputmode="numeric" id="sPassi" placeholder="0"></div></div>';
        h += '<div class="due"><div class="campo"><label>Obiettivo</label><input type="text" inputmode="numeric" id="sOb" value="' + P.obiettivo + '"></div><div class="campo"><label>Note</label><input type="text" id="sNote" autocomplete="off"></div></div>';
        h += '<div class="btns" style="margin-top:0"><button class="btn no" onclick="salvaObDef()">Imposta come default</button><button class="btn ok" id="btnSalvaPassi" onclick="salvaPassi()">Registra</button></div></div>';
        if (chiavi.length) {
            var ult = chiavi.slice(0, 30), vals = ult.map(function(k) { return P.db[k].passi; });
            h += '<div class="riepilogo"><span>Media ultimi ' + ult.length + ' giorni</span><b>' + Math.round(vals.reduce(function(a, b) { return a + b; }, 0) / vals.length).toLocaleString('it-IT') + '</b></div>';
            chiavi.slice(0, 60).forEach(function(k) {
                var r = P.db[k], pct = Math.min(100, Math.round(r.passi * 100 / (r.obiettivo || 10000)));
                h += '<div class="dt" style="flex-direction:column;gap:4px"><div style="display:flex;justify-content:space-between"><span>' + esc(k) + (r.note ? ' · ' + esc(r.note) : '') + '</span><span><b>' + r.passi.toLocaleString('it-IT') + '</b> / ' + (r.obiettivo || 10000).toLocaleString('it-IT') + ' <a class="rm" onclick="eliminaPassi(\'' + esc(k) + '\')">✕</a></span></div><div class="barra"><i style="width:' + pct + '%;background:' + (pct >= 100 ? 'var(--green)' : 'var(--blue)') + '"></i></div></div>';
            });
        } else h += '<div class="vuoto">Nessun dato sui passi.</div>';
        return h;
    }
    async function salvaPassi() { var j = await chiama('/api/dieta/passi', {azione: 'salva', data: iso2dmy($('sData').value), passi: $('sPassi').value, obiettivo: $('sOb').value, note: $('sNote').value}); if (!j) return; msg('Passi registrati'); carica(); }
    async function salvaObDef() { var j = await chiama('/api/dieta/passi', {azione: 'obiettivo', obiettivo: $('sOb').value}); if (!j) return; msg('Obiettivo predefinito salvato'); carica(); }
    async function eliminaPassi(d) { var j = await chiama('/api/dieta/passi', {azione: 'elimina', data: d}); if (!j) return; msg('Voce eliminata'); carica(); }
    function htmlFabb() {
        var F = D.fabb || {};
        return '<div class="scad"><div class="due"><div class="campo"><label>Sesso</label><select id="fSesso" onchange="calcFabb()"><option' + (F.sesso === 'Uomo' ? '' : ' selected') + '>Donna</option><option' + (F.sesso === 'Uomo' ? ' selected' : '') + '>Uomo</option></select></div><div class="campo"><label>Età</label><input type="text" inputmode="numeric" id="fEta" value="' + esc(F.eta || '') + '" oninput="calcFabb()"></div></div><div class="due"><div class="campo"><label>Peso (kg)</label><input type="text" inputmode="decimal" id="fPeso" value="' + esc(F.peso || '') + '" oninput="calcFabb()"></div><div class="campo"><label>Altezza (cm)</label><input type="text" inputmode="decimal" id="fAlt" value="' + esc(F.altezza || '') + '" oninput="calcFabb()"></div></div><button class="btn ok" id="btnSalvaFabb" style="width:100%" onclick="salvaFabb()">Salva dati</button></div><div id="fabbRis"></div>';
    }
    function calcFabb() {
        var el = $('fabbRis'); if (!el) return;
        var p = parseFloat($('fPeso').value.replace(',', '.')), a = parseFloat($('fAlt').value.replace(',', '.')), e = parseInt($('fEta').value, 10);
        if (!(p > 0 && a > 0 && e > 0)) { el.innerHTML = '<div class="vuoto">Inserisci peso, altezza ed età.</div>'; return; }
        var bmr = 10 * p + 6.25 * a - 5 * e + ($('fSesso').value === 'Uomo' ? 5 : -161);
        var L = [['Sedentario (ufficio)', 1.2], ['Leggero (attività 1-2 volte)', 1.375], ['Moderato (sport 3-5 volte)', 1.55], ['Attivo (lavoro fisico)', 1.725]];
        var h = '<div class="riepilogo"><span>Metabolismo basale (BMR)</span><b>' + Math.round(bmr) + ' kcal</b></div>';
        L.forEach(function(l) { h += '<div class="dt"><span>' + l[0] + '</span><b>' + Math.round(bmr * l[1]) + ' kcal</b></div>'; });
        var base = Math.round(bmr * 1.55);
        h += '<div class="meta" style="margin:12px 0 4px"><b>Obiettivi consigliati (base Moderato)</b></div><div class="dt"><span>Perdere peso (−15%)</span><b class="neg">' + Math.round(base * 0.85) + ' kcal</b></div><div class="dt"><span>Mantenere il peso</span><b style="color:var(--blue)">' + base + ' kcal</b></div><div class="dt"><span>Aumentare massa (+10%)</span><b class="pos">' + Math.round(base * 1.1) + ' kcal</b></div>';
        el.innerHTML = h;
    }
    async function salvaFabb() { var j = await chiama('/api/dieta/fabb', {sesso: $('fSesso').value, peso: $('fPeso').value, altezza: $('fAlt').value, eta: $('fEta').value}); if (!j) return; msg('Dati salvati'); carica(); }
    var inAttesaConferma = null;
    function apriModalConferma(testo, fn) { inAttesaConferma = fn; $('modalConfermaText').textContent = testo; $('confermaModal').style.display = 'flex'; }
    function chiudiModalConferma() { $('confermaModal').style.display = 'none'; inAttesaConferma = null; }
    function eseguiConferma() { var fn = inAttesaConferma; chiudiModalConferma(); if (fn) fn(); }
    document.addEventListener('keydown', function(e) {
        if (e.key !== 'Escape') return;
        if ($('confermaModal').style.display === 'flex') chiudiModalConferma();
        else if ($('velo2').style.display === 'block') chiudi2();
        else chiudi();
    });
    window.addEventListener('load', function() { applyTheme(localStorage.getItem('theme') || 'dark'); carica(); });
"""

_CSS = """
    .tabs { display:flex; gap:6px; margin-bottom:12px; }
    .tabs button { flex:1; padding:10px 4px; border-radius:10px; border:1px solid var(--border); background:var(--surface3); color:var(--text-mid); font-family:inherit; font-weight:700; font-size:0.8em; cursor:pointer; }
    .tabs button.on { border-color:var(--gold); color:var(--gold); }
    .sh { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }
    .sh h3 { margin:0; }
    .x { background:var(--surface3); border:1px solid var(--border); color:var(--text-mid); width:34px; height:34px; border-radius:10px; cursor:pointer; }
    .scad { background:var(--surface); border:1px solid var(--border); border-radius:14px; padding:12px; margin-bottom:12px; }
    .pasto { background:var(--surface2); border:1px solid var(--border); border-radius:12px; padding:10px; margin-bottom:8px; }
    .mini { flex:none; padding:6px 10px; font-size:0.78em; }
    .rm { color:var(--red); cursor:pointer; margin-left:6px; }
    .ali { cursor:pointer; }
    .tre { display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; }
    #velo2 { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.6); z-index:600; overflow-y:auto; }
    .riepilogo { gap:8px; }
"""


def _costruisci():
    base = _wr._PAGINA
    css = base[base.index("<style>") + 7:base.index("</style>")]
    js_comune = base[base.index("    var $ = function"):base.index("    function disegna()")]
    js_comune = js_comune.replace("var DATI = null, tipoVoce = 'Uscita', aperta = null;", "")
    menu = base[base.index('<div id="extraMenu"'):base.index('<div class="header-title">')]
    return (
        '<!DOCTYPE html>\n<html lang="it">\n<head>\n<meta charset="utf-8">\n<title>🥗 Dieta</title>\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<script>(function(){ if (localStorage.getItem('theme') === 'light') document.documentElement.classList.add('light'); })();</script>\n"
        '<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">\n'
        f"<style>{css}{_CSS}\n    #fab {{ display:none; }}</style>\n<script>\n{js_comune}\n{_JS}\n</script>\n</head>\n<body>\n<header>\n"
        '    <button class="menu-btn" onclick="toggleMenu()">⚙️</button>\n    '
        f'{menu}<div class="header-title">🥗 Dieta</div>\n'
        '    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>\n</header>\n'
        '<main>\n    <div id="contenuto"></div>\n</main>\n'
        '<div id="velo" onclick="if (event.target === this) chiudi()"><div class="scheda" id="scheda"></div></div>\n'
        '<div id="velo2" onclick="if (event.target === this) chiudi2()"><div class="scheda" id="scheda2"></div></div>\n'
        '<div id="confermaModal" class="modal-overlay"><div class="modal-box"><div class="modal-title">⚠️ Conferma</div>'
        '<div class="modal-text" id="modalConfermaText"></div><div class="modal-btns">'
        '<button class="m-btn m-cancel" onclick="chiudiModalConferma()">Annulla</button>'
        '<button class="m-btn m-confirm" onclick="eseguiConferma()">Conferma</button></div></div></div>\n'
        '<div id="msg"></div>\n</body>\n</html>\n'
    )


_PAGINA_CACHE = {}


def pagina_dieta_web(self):
    if "h" not in _PAGINA_CACHE:
        _PAGINA_CACHE["h"] = _costruisci()
    return _PAGINA_CACHE["h"].replace("__ANNO__", str(datetime.date.today().year))
