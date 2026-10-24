#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import uuid
import threading

from moduli import community_pool as _cp

_LOCK = threading.RLock()
_NOTA_MAX = 200

_ERR = ({"ok": False, "errore": "Richiesta non valida"}, 400)


def _app():
    import __main__ as a
    return a


def _fmt(v):
    return _cp._fmt_it(round(float(v), 2) or 0.0)


def _leggi_stato():
    eventi = _cp._leggi_eventi()
    spese, contributi = _cp._costruisci_stato(eventi)
    return spese, contributi


def _pianifica_sync(self):
    def _vai():
        try:
            if not _cp._form_in_uso(self):
                _cp.community_pool_sync(self, silenzioso=True)
        except Exception:
            pass
    try:
        self.after(0, _vai)
    except Exception:
        pass


def _saldi(lista, membri, et, nascondi):
    ant, ric, ver = {}, {}, {}
    for s in lista:
        if nascondi and _cp._stato_spesa(s) == "Chiusa":
            continue
        ant[s["pagante"]] = ant.get(s["pagante"], 0.0) + s["importo"]
        for c in s["contributi"]:
            if c["stato"] == "confermata":
                ric[s["pagante"]] = ric.get(s["pagante"], 0.0) + c["importo"]
                ver[c["profilo"]] = ver.get(c["profilo"], 0.0) + c["importo"]
    elenco = list(dict.fromkeys(list(membri) + list(ant) + list(ver)))
    righe = []
    tot = [0.0, 0.0, 0.0, 0.0]
    for m in elenco:
        a, r, v = ant.get(m, 0.0), ric.get(m, 0.0), ver.get(m, 0.0)
        if not (a or r or v):
            continue
        tot = [tot[0] + a, tot[1] + r, tot[2] + (a - r), tot[3] + v]
        righe.append({"nome": et(m), "anticipate": _fmt(a), "ricevute": _fmt(r),
                      "residuo": _fmt(a - r), "residuo_n": round(a - r, 2), "versate": _fmt(v)})
    return {"righe": righe, "tot": {"anticipate": _fmt(tot[0]), "ricevute": _fmt(tot[1]),
                                     "residuo": _fmt(tot[2]), "versate": _fmt(tot[3])}}


def community_pool_web_dati(self, primo=False):
    from moduli.profili import elenco_profili, _etichetta_profilo
    me = _app().PROFILO_ATTIVO

    def et(nome):
        return _etichetta_profilo(self, nome)

    try:
        profili = elenco_profili(self)
        if len(profili) < 2:
            return {"ok": True, "attivo": False,
                    "messaggio": "Per usare il CommunityPool servono almeno due profili."}
        if _cp._leggi_config() is None:
            return {"ok": True, "attivo": False,
                    "messaggio": "Nessun CommunityPool creato: crealo dal desktop (menu Finanze)."}
        with _LOCK:
            spese, contributi = _leggi_stato()
            n_sp, n_q, n_es = _cp._conta_novita(me)
            if primo:
                _cp._segna_visto(me)
    except Exception as e:
        return {"ok": False, "errore": f"CommunityPool non leggibile: {e}"}

    attive = [s for s in spese.values() if not s["ritirata"]]
    attive.sort(key=lambda x: x["data"], reverse=True)

    righe = []
    for s in attive:
        cop = _cp._coperto(s)
        res = round(s["importo"] - cop, 2)
        mie = [c for c in s["contributi"] if c["profilo"] == me]
        conf_mia = round(sum(c["importo"] for c in mie if c["stato"] == "confermata"), 2)
        attesa_mia = any(c["stato"] == "proposta" for c in mie)
        mia_spesa = s["pagante"] == me
        stato_s = _cp._stato_spesa(s)
        righe.append({
            "id_fam": s["id_fam"], "data_it": _cp._data_it(s["data"]), "categoria": s["categoria"],
            "descrizione": s["descrizione"], "pagante": et(s["pagante"]), "mia_spesa": mia_spesa,
            "importo_t": _fmt(s["importo"]), "coperto_t": _fmt(cop), "residuo_t": _fmt(res),
            "stato": stato_s, "hashtag": " ".join(s["hashtag"] or []), "metodo": s["metodo"],
            "mia_quota_t": _fmt(conf_mia) if conf_mia else "", "mia_attesa": attesa_mia,
            "puo_proporre": (not mia_spesa) and (not s["chiusa"]) and res > 0 and not attesa_mia,
        })

    da_conf, mie_q = [], []
    for c in sorted(contributi.values(), key=lambda x: x["id_contrib"]):
        s = spese.get(c["id_fam"])
        if not s or s["ritirata"]:
            continue
        if c["stato"] == "proposta" and s["pagante"] == me:
            da_conf.append({
                "id_contrib": c["id_contrib"], "data_it": _cp._data_it(s["data"]), "da": et(c["profilo"]),
                "descrizione": s["descrizione"], "importo_t": _fmt(s["importo"]),
                "residuo_t": _fmt(s["importo"] - _cp._coperto(s)), "proposta_t": _fmt(c["proposta"]),
                "nota": c["nota"], "chiusa": bool(s["chiusa"]),
            })
        if c["profilo"] == me:
            mie_q.append({
                "id_contrib": c["id_contrib"], "data_it": _cp._data_it(s["data"]),
                "descrizione": s["descrizione"], "pagante": et(s["pagante"]), "stato": c["stato"],
                "stato_lbl": _cp.STATI_LBL.get(c["stato"], c["stato"]), "proposta_t": _fmt(c["proposta"]),
                "importo_t": _fmt(c["importo"]) if c["stato"] == "confermata" else "",
                "nota": (c["nota_risposta"] if c["stato"] == "rifiutata" and c["nota_risposta"] else c["nota"]),
            })

    try:
        cats = sorted((c for c in self.categorie if c != self.CATEGORIA_RIMOSSA), key=str.lower)
    except Exception:
        cats = ["Generica"]
    if "Generica" not in cats:
        cats.append("Generica")

    return {
        "ok": True, "attivo": True, "me": et(me),
        "novita": {"spese": n_sp, "quote": n_q, "esiti": n_es},
        "spese": righe, "da_confermare": da_conf, "mie": mie_q, "categorie": cats,
        "saldi": _saldi(attive, profili, et, True),
        "saldi_tutti": _saldi(attive, profili, et, False),
    }


def community_pool_web_azione(self, d):
    d = d or {}
    azione = str(d.get("azione", "")).strip()
    if azione not in ("proponi", "conferma", "rifiuta", "annulla"):
        return _ERR
    me = _app().PROFILO_ATTIVO
    nota = str(d.get("nota", "") or "").strip()[:_NOTA_MAX]
    try:
        with _LOCK:
            if _cp._leggi_config() is None:
                return {"ok": False, "errore": "CommunityPool non attivo"}, 400
            spese, contributi = _leggi_stato()

            if azione == "proponi":
                s = spese.get(str(d.get("id_fam", "")))
                if not s or s["ritirata"]:
                    return {"ok": False, "errore": "Spesa non trovata"}, 404
                if s["pagante"] == me:
                    return {"ok": False, "errore": "Hai pagato tu questa spesa"}, 400
                if any(c["profilo"] == me and c["stato"] == "proposta" for c in s["contributi"]):
                    return {"ok": False, "errore": "Hai già una proposta in attesa su questa spesa"}, 400
                if s["chiusa"]:
                    return {"ok": False, "errore": "La spesa è chiusa dal pagante"}, 400
                residuo = round(s["importo"] - _cp._coperto(s), 2)
                if residuo <= 0:
                    return {"ok": False, "errore": "La spesa è già coperta"}, 400
                imp = _cp._parse_importo(d.get("importo"))
                if imp is None:
                    return {"ok": False, "errore": "Importo non valido"}, 400
                if imp > residuo + 0.005:
                    return {"ok": False, "errore": f"Supera il residuo ({_fmt(residuo)} €)"}, 400
                try:
                    cats = [c for c in self.categorie if c != self.CATEGORIA_RIMOSSA]
                except Exception:
                    cats = []
                cat = str(d.get("categoria", "") or "")
                if cat not in cats:
                    cat = s["categoria"] if s["categoria"] in cats else "Generica"
                _cp._scrivi_evento(me, "quota_proposta", id_contrib=uuid.uuid4().hex[:12],
                                   id_fam=s["id_fam"], importo=imp, nota=nota, categoria_membro=cat)
                return {"ok": True}, 200

            c = contributi.get(str(d.get("id_contrib", "")))
            s = spese.get(c["id_fam"]) if c else None
            if not c or not s:
                return {"ok": False, "errore": "Proposta non trovata"}, 404

            if azione == "annulla":
                if c["profilo"] != me or c["stato"] != "proposta":
                    return {"ok": False, "errore": "Puoi annullare solo una tua proposta in attesa"}, 400
                _cp._scrivi_evento(me, "quota_annullata", id_contrib=c["id_contrib"])
                return {"ok": True}, 200

            if s["pagante"] != me or c["stato"] != "proposta" or s["ritirata"]:
                return {"ok": False, "errore": "Questa proposta non è più da confermare"}, 400

            if azione == "conferma":
                imp = c["proposta"] if d.get("importo") in (None, "") else _cp._parse_importo(d.get("importo"))
                if imp is None:
                    return {"ok": False, "errore": "Importo non valido"}, 400
                if s["chiusa"]:
                    return {"ok": False, "errore": "Spesa chiusa: riaprila dal desktop per confermare quote"}, 400
                if _cp._coperto(s) + imp > s["importo"] + 0.005:
                    return {"ok": False, "errore": "Con questa quota si supera il totale della spesa"}, 400
                _cp._scrivi_evento(me, "quota_confermata", id_contrib=c["id_contrib"], importo=imp)
                _pianifica_sync(self)
                return {"ok": True}, 200

            if azione == "rifiuta":
                _cp._scrivi_evento(me, "quota_rifiutata", id_contrib=c["id_contrib"], nota=nota)
                return {"ok": True}, 200
    except Exception as e:
        return {"ok": False, "errore": f"Errore: {e}"}, 500
    return _ERR


_PAGINA = r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>🤝 CommunityPool</title>
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
    main { padding:14px; max-width:720px; margin:0 auto; }
    input, select { background:var(--surface3); border:1px solid var(--border); color:var(--text); border-radius:10px; padding:11px; font-family:inherit; font-size:1em; width:100%; min-width:0; }
    input:focus, select:focus { outline:none; border-color:var(--border-active); }
    .vuoto { text-align:center; color:var(--text-mid); padding:30px 10px; font-size:0.95em; line-height:1.5; }
    .nov { background:rgba(99,160,240,0.12); border:1px solid rgba(99,160,240,0.35); color:var(--blue); border-radius:12px; padding:10px 12px; font-size:0.85em; font-weight:700; margin-bottom:12px; }
    .tabs { display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:6px; margin-bottom:12px; }
    .tab { min-width:0; background:var(--surface3); border:1px solid var(--border); color:var(--text-mid); border-radius:10px; padding:9px 12px; font-family:inherit; font-size:0.85em; font-weight:700; cursor:pointer; white-space:nowrap; }
    .tab.on { background:var(--blue); border-color:var(--blue); color:#fff; }
    .bdg { display:inline-block; min-width:18px; margin-left:6px; padding:0 5px; border-radius:9px; background:var(--red); color:#fff; font-size:0.8em; line-height:18px; }
    .bdg:empty { display:none; }
    .barra { display:flex; gap:10px; align-items:center; margin-bottom:12px; }
    .chk { display:flex; align-items:center; gap:8px; color:var(--text-mid); font-size:0.85em; white-space:nowrap; }
    .chk input { width:20px; height:20px; flex:none; }
    .voce { background:var(--surface); border:1px solid var(--border); border-left:4px solid var(--blue); border-radius:14px; padding:11px 12px; margin-bottom:8px; }
    .voce.chiusa { opacity:0.55; border-left-color:var(--text-dim); }
    .voce.attesa { border-left-color:var(--orange); }
    .voce.mia { border-left-color:var(--green); }
    .tit { font-weight:700; font-size:0.98em; overflow-wrap:anywhere; }
    .meta { color:var(--text-mid); font-size:0.8em; margin-top:2px; line-height:1.4; }
    .cifre { display:flex; gap:14px; flex-wrap:wrap; margin-top:6px; font-size:0.85em; }
    .cifre b { color:var(--text); }
    .chip { display:inline-block; font-size:0.72em; font-weight:700; padding:1px 8px; border-radius:20px; border:1px solid currentColor; margin-left:6px; vertical-align:middle; }
    .chip.Aperta { color:var(--blue); } .chip.Attesa { color:var(--orange); } .chip.Chiusa { color:var(--text-mid); }
    .chip.ok { color:var(--green); } .chip.no { color:var(--red); }
    .azioni { display:flex; gap:8px; flex-wrap:wrap; margin-top:10px; }
    .mini { background:var(--surface3); border:1px solid var(--border); color:var(--text); border-radius:10px; padding:8px 12px; font-family:inherit; font-size:0.82em; font-weight:700; cursor:pointer; }
    .mini.verde { background:var(--green); border-color:var(--green); color:#fff; }
    .mini.rosso { color:var(--red); }
    table { width:100%; border-collapse:collapse; font-size:0.85em; }
    th, td { padding:9px 6px; border-bottom:1px solid var(--border); text-align:right; }
    th:first-child, td:first-child { text-align:left; }
    .tw { overflow-x:auto; -webkit-overflow-scrolling:touch; }
    @media (max-width:480px) { table { font-size:0.74em; } th, td { padding:8px 3px; } th { font-size:0.72em; } }
    th { color:var(--text-mid); font-size:0.78em; font-weight:700; }
    tr.tot td { font-weight:800; border-top:2px solid var(--border); border-bottom:none; }
    .neg { color:var(--red); } .pos { color:var(--green); }
    #velo { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.65); z-index:200; overflow-y:auto; padding:14px; }
    #form { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-lg); padding:16px; max-width:520px; margin:40px auto; }
    #form h3 { font-size:1em; color:var(--gold); margin-bottom:10px; }
    .info { color:var(--text-mid); font-size:0.88em; line-height:1.45; margin-bottom:12px; overflow-wrap:anywhere; }
    .campo { margin-bottom:10px; }
    .campo label { display:block; font-size:0.78em; color:var(--text-mid); margin-bottom:4px; }
    .btn { display:block; width:100%; padding:13px; border-radius:12px; border:1px solid var(--border); background:var(--surface3); color:var(--text); font-family:inherit; font-size:1em; font-weight:700; cursor:pointer; }
    .btn.verde { background:var(--green); border-color:var(--green); color:#fff; }
    .btn.rosso { background:var(--red); border-color:var(--red); color:#fff; }
    .btns { display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:12px; }
    #msg { position:fixed; left:50%; bottom:92px; transform:translateX(-50%); background:var(--surface2); border:1px solid var(--border-active); padding:10px 16px; border-radius:12px; font-weight:700; font-size:0.9em; display:none; z-index:300; max-width:90vw; text-align:center; }
    #msg.err { border-color:var(--red); color:var(--red); }
</style>
<script>
    var $ = function(i) { return document.getElementById(i); };
    var D = null, tab = 'spese', modale = null, inInvio = false;

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

    function carica(primo) {
        fetch('/api/community_pool/dati' + (primo ? '?primo=1' : ''), {cache: 'no-store'})
            .then(function(r) { return r.json(); })
            .then(function(r) {
                if (!r.ok) { msg(r.errore || 'Errore di lettura', true); return; }
                D = r;
                if (!r.attivo) {
                    $('app').style.display = 'none';
                    $('vuoto').style.display = 'block'; $('vuoto').textContent = r.messaggio; return;
                }
                $('vuoto').style.display = 'none'; $('app').style.display = 'block';
                if (primo) mostraNovita();
                disegna();
            })
            .catch(function() { msg('Connessione assente', true); });
    }
    function mostraNovita() {
        var n = D.novita, p = [];
        if (n.spese) p.push(n.spese + (n.spese === 1 ? ' nuova spesa' : ' nuove spese'));
        if (n.quote) p.push(n.quote + (n.quote === 1 ? ' quota da confermare' : ' quote da confermare'));
        if (n.esiti) p.push(n.esiti + (n.esiti === 1 ? ' esito sulle tue proposte' : ' esiti sulle tue proposte'));
        var b = $('nov');
        if (p.length) { b.textContent = '🔔 Novità: ' + p.join(', '); b.style.display = 'block'; }
        else b.style.display = 'none';
    }
    function setTab(t) {
        tab = t;
        document.querySelectorAll('.tab').forEach(function(b) { b.classList.toggle('on', b.dataset.t === t); });
        disegna();
    }
    function disegna() {
        if (!D || !D.attivo) return;
        var nc = D.da_confermare.length;
        $('bConf').textContent = nc ? nc : '';
        $('barraFiltri').style.display = (tab === 'spese' || tab === 'saldi') ? 'flex' : 'none';
        $('cerca').style.display = tab === 'spese' ? '' : 'none';
        var h = '';
        if (tab === 'spese') h = htmlSpese();
        else if (tab === 'conf') h = htmlConf();
        else if (tab === 'mie') h = htmlMie();
        else h = htmlSaldi();
        $('elenco').innerHTML = h;
    }
    function htmlSpese() {
        var nasc = $('chkChiuse').checked, q = $('cerca').value.trim().toLowerCase(), h = '', n = 0;
        D.spese.forEach(function(s) {
            if (nasc && s.stato === 'Chiusa') return;
            if (q && (s.categoria + ' ' + s.descrizione + ' ' + s.pagante + ' ' + s.stato + ' ' + s.importo_t + ' ' + s.hashtag + ' ' + s.metodo).toLowerCase().indexOf(q) < 0) return;
            n++;
            var cls = 'voce' + (s.stato === 'Chiusa' ? ' chiusa' : (s.stato === 'In attesa' ? ' attesa' : '')) + (s.mia_spesa ? ' mia' : '');
            h += '<div class="' + cls + '"><div class="tit">' + esc(s.descrizione || s.categoria) +
                '<span class="chip ' + (s.stato === 'In attesa' ? 'Attesa' : s.stato) + '">' + esc(s.stato) + '</span></div>' +
                '<div class="meta">' + esc(s.data_it) + ' · ' + esc(s.categoria) + ' · pagata da ' + esc(s.pagante) +
                (s.mia_spesa ? ' (tu)' : '') + (s.hashtag ? ' · ' + esc(s.hashtag) : '') + '</div>' +
                '<div class="cifre"><span>Totale <b>' + s.importo_t + ' €</b></span><span>Coperto <b>' + s.coperto_t +
                ' €</b></span><span>Residuo <b>' + s.residuo_t + ' €</b></span></div>';
            if (s.mia_quota_t || s.mia_attesa)
                h += '<div class="meta">La tua quota: ' + (s.mia_quota_t ? s.mia_quota_t + ' €' : '') + (s.mia_attesa ? ' ⏳ in attesa' : '') + '</div>';
            if (s.puo_proporre) h += '<div class="azioni"><button class="mini verde" onclick="apriForm(\'proponi\',\'' + esc(s.id_fam) + '\')">Proponi la tua quota</button></div>';
            h += '</div>';
        });
        return n ? h : '<div class="vuoto">Nessuna spesa da mostrare</div>';
    }
    function htmlConf() {
        if (!D.da_confermare.length) return '<div class="vuoto">Nessuna proposta da confermare</div>';
        var h = '';
        D.da_confermare.forEach(function(c) {
            h += '<div class="voce attesa"><div class="tit">' + esc(c.da) + ' propone ' + c.proposta_t + ' €</div>' +
                '<div class="meta">' + esc(c.data_it) + ' · ' + esc(c.descrizione) + '</div>' +
                '<div class="cifre"><span>Totale <b>' + c.importo_t + ' €</b></span><span>Residuo <b>' + c.residuo_t + ' €</b></span></div>' +
                (c.nota ? '<div class="meta">“' + esc(c.nota) + '”</div>' : '') +
                (c.chiusa ? '<div class="meta neg">Spesa chiusa: riaprila dal desktop per confermare</div>' : '') +
                '<div class="azioni">' +
                (c.chiusa ? '' : '<button class="mini verde" onclick="conferma(\'' + esc(c.id_contrib) + '\')">✔ Conferma</button>' +
                '<button class="mini" onclick="apriForm(\'conferma\',\'' + esc(c.id_contrib) + '\')">✏️ Cambia importo</button>') +
                '<button class="mini rosso" onclick="apriForm(\'rifiuta\',\'' + esc(c.id_contrib) + '\')">✖ Rifiuta</button></div></div>';
        });
        return h;
    }
    function htmlMie() {
        if (!D.mie.length) return '<div class="vuoto">Non hai ancora proposto quote</div>';
        var h = '';
        D.mie.forEach(function(c) {
            var k = c.stato === 'confermata' ? 'ok' : (c.stato === 'rifiutata' ? 'no' : 'Attesa');
            h += '<div class="voce"><div class="tit">' + esc(c.descrizione) + '<span class="chip ' + k + '">' + esc(c.stato_lbl) + '</span></div>' +
                '<div class="meta">' + esc(c.data_it) + ' · pagata da ' + esc(c.pagante) + '</div>' +
                '<div class="cifre"><span>Proposta <b>' + c.proposta_t + ' €</b></span>' +
                (c.importo_t ? '<span>Confermata <b>' + c.importo_t + ' €</b></span>' : '') + '</div>' +
                (c.nota ? '<div class="meta">“' + esc(c.nota) + '”</div>' : '');
            if (c.stato === 'proposta') h += '<div class="azioni"><button class="mini rosso" onclick="annulla(\'' + esc(c.id_contrib) + '\')">↩ Annulla proposta</button></div>';
            h += '</div>';
        });
        return h;
    }
    function htmlSaldi() {
        var S = $('chkChiuse').checked ? D.saldi : D.saldi_tutti;
        if (!S.righe.length) return '<div class="vuoto">Nessun movimento nel pool</div>';
        var h = '<div class="tw"><table><tr><th>Membro</th><th>Anticipate</th><th>Ricevute</th><th>Residuo</th><th>Versate</th></tr>';
        S.righe.forEach(function(r) {
            h += '<tr><td>' + esc(r.nome) + '</td><td>' + r.anticipate + '</td><td>' + r.ricevute + '</td><td class="' + (r.residuo_n > 0 ? 'pos' : '') + '">' + r.residuo + '</td><td>' + r.versate + '</td></tr>';
        });
        h += '<tr class="tot"><td>Totale</td><td>' + S.tot.anticipate + '</td><td>' + S.tot.ricevute + '</td><td>' + S.tot.residuo + '</td><td>' + S.tot.versate + '</td></tr></table></div>';
        return h;
    }

    function trovaSpesa(id) { return D.spese.filter(function(s) { return s.id_fam === id; })[0]; }
    function trovaConf(id) { return D.da_confermare.filter(function(c) { return c.id_contrib === id; })[0]; }
    function apriForm(tipo, id) {
        modale = { tipo: tipo, id: id };
        $('cImp').style.display = 'none'; $('cCat').style.display = 'none'; $('cNota').style.display = 'none';
        $('bOk').className = 'btn verde'; $('fImp').value = ''; $('fNota').value = '';
        if (tipo === 'proponi') {
            var s = trovaSpesa(id); if (!s) return;
            $('fTitolo').textContent = 'Proponi la tua quota';
            $('fInfo').textContent = (s.descrizione || s.categoria) + ' — totale ' + s.importo_t + ' €, residuo ' + s.residuo_t + ' €';
            $('lImp').textContent = 'La tua quota €'; $('lNota').textContent = 'Nota (facoltativa)';
            var sel = $('fCat'); sel.innerHTML = '';
            D.categorie.forEach(function(c) { var o = document.createElement('option'); o.textContent = c; o.value = c; sel.appendChild(o); });
            sel.value = D.categorie.indexOf(s.categoria) >= 0 ? s.categoria : 'Generica';
            $('cImp').style.display = ''; $('cCat').style.display = ''; $('cNota').style.display = '';
            $('bOk').textContent = 'Invia proposta';
        } else if (tipo === 'conferma') {
            var c = trovaConf(id); if (!c) return;
            $('fTitolo').textContent = 'Importo confermato';
            $('fInfo').textContent = c.da + ' propone ' + c.proposta_t + ' € su “' + c.descrizione + '”';
            $('lImp').textContent = 'Importo da confermare €'; $('fImp').value = c.proposta_t;
            $('cImp').style.display = ''; $('bOk').textContent = 'Conferma';
        } else if (tipo === 'rifiuta') {
            var r = trovaConf(id); if (!r) return;
            $('fTitolo').textContent = 'Rifiuta quota';
            $('fInfo').textContent = 'Rifiutare la quota di ' + r.da + ' (' + r.proposta_t + ' €) su “' + r.descrizione + '”?';
            $('lNota').textContent = 'Motivo (facoltativo)'; $('cNota').style.display = '';
            $('bOk').className = 'btn rosso'; $('bOk').textContent = 'Rifiuta';
        }
        $('velo').style.display = 'block';
        if (tipo !== 'rifiuta') setTimeout(function() { $('fImp').focus(); }, 50);
    }
    function chiudiForm() { $('velo').style.display = 'none'; modale = null; }
    function conferma(id) { post({ azione: 'conferma', id_contrib: id }, 'Quota confermata, rientro registrato'); }
    function annulla(id) { post({ azione: 'annulla', id_contrib: id }, 'Proposta annullata'); }
    function invia() {
        if (!modale) return;
        var p = { azione: modale.tipo };
        if (modale.tipo === 'proponi') { p.id_fam = modale.id; p.importo = $('fImp').value; p.nota = $('fNota').value; p.categoria = $('fCat').value; }
        else if (modale.tipo === 'conferma') { p.id_contrib = modale.id; p.importo = $('fImp').value; }
        else { p.id_contrib = modale.id; p.nota = $('fNota').value; }
        var ok = modale.tipo === 'proponi' ? 'Quota inviata, in attesa di conferma' : (modale.tipo === 'conferma' ? 'Quota confermata, rientro registrato' : 'Quota rifiutata');
        post(p, ok, chiudiForm);
    }
    function post(corpo, testoOk, dopo) {
        if (inInvio) return;
        inInvio = true;
        fetch('/api/community_pool/azione', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(corpo) })
            .then(function(r) { return r.json(); })
            .then(function(r) {
                inInvio = false;
                if (!r.ok) { msg(r.errore || 'Operazione non riuscita', true); return; }
                if (dopo) dopo();
                msg(testoOk); carica(false);
            })
            .catch(function() { inInvio = false; msg('Connessione assente', true); });
    }

    document.addEventListener('DOMContentLoaded', function() {
        applyTheme((function() { try { return localStorage.getItem('theme') || 'dark'; } catch (e) { return 'dark'; } })());
        document.querySelectorAll('.tab').forEach(function(b) { b.onclick = function() { setTab(b.dataset.t); }; });
        $('cerca').oninput = disegna;
        $('chkChiuse').onchange = disegna;
        $('fImp').addEventListener('keydown', function(e) { if (e.key === 'Enter') invia(); });
        carica(true);
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
    <div class="header-title">🤝 CommunityPool</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div id="vuoto" class="vuoto" style="display:none"></div>
    <div id="app" style="display:none">
        <div class="nov" id="nov" style="display:none"></div>
        <div class="tabs" id="tabs">
            <button class="tab on" data-t="spese">Spese</button>
            <button class="tab" data-t="conf">Da confermare<span class="bdg" id="bConf"></span></button>
            <button class="tab" data-t="mie">Le mie quote</button>
            <button class="tab" data-t="saldi">Saldi</button>
        </div>
        <div class="barra" id="barraFiltri">
            <input id="cerca" type="search" placeholder="Cerca..." autocomplete="off">
            <label class="chk"><input type="checkbox" id="chkChiuse" checked><span>Nascondi chiuse</span></label>
        </div>
        <div id="elenco"></div>
    </div>
</main>
<div id="velo">
  <div id="form">
    <h3 id="fTitolo"></h3>
    <div id="fInfo" class="info"></div>
    <div class="campo" id="cImp"><label id="lImp">La tua quota €</label><input id="fImp" type="text" inputmode="decimal" maxlength="12" placeholder="0,00" autocomplete="off"></div>
    <div class="campo" id="cCat"><label>Categoria nel tuo profilo</label><select id="fCat"></select></div>
    <div class="campo" id="cNota"><label id="lNota">Nota (facoltativa)</label><input id="fNota" type="text" maxlength="200" autocomplete="off"></div>
    <div class="btns">
        <button class="btn" onclick="chiudiForm()">Annulla</button>
        <button class="btn verde" id="bOk" onclick="invia()">Conferma</button>
    </div>
  </div>
</div>
<div id="msg"></div>
</body>
</html>
"""


def pagina_community_pool_web(self):
    import datetime
    return _PAGINA.replace("__ANNO__", str(datetime.date.today().year))
