#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import html as _html

from moduli.spese_pianificate import _carica_sp, _parse_data, _mesi_coperti, _quote_mensili

def attivo(ambito=None):
    try:
        from flask import request, has_request_context
        return bool(has_request_context() and request.args.get("pian") == "1")
    except Exception:
        return False

def campo_nascosto():
    return '<input type="hidden" name="pian" value="1">' if attivo() else ""

def _fmt(v):
    s = format(float(v), ",.2f")
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")

def piani(self):
    try:
        return list(_carica_sp(self).get("piani", []))
    except Exception:
        return []

def ids_in_piano(self):
    return {p.get("id_spesa_collegata") for p in piani(self) if p.get("id_spesa_collegata")}

def quote(self, anno, mese=None, conto=None):
    out = []
    for p in piani(self):
        if conto and (p.get("conto") or "") != conto:
            continue
        try:
            lista = _mesi_coperti(_parse_data(p["inizio"]), _parse_data(p["data_scadenza"]))
            qs = _quote_mensili(float(p.get("importo_totale", 0) or 0), len(lista))
        except Exception:
            continue
        for (a, m), q in zip(lista, qs):
            if a == anno and (mese is None or m == mese) and q > 0:
                out.append({"piano": p, "anno": a, "mese": m, "quota": q})
    return out

def tutte_le_quote(self):
    out = []
    for p in piani(self):
        try:
            lista = _mesi_coperti(_parse_data(p["inizio"]), _parse_data(p["data_scadenza"]))
            qs = _quote_mensili(float(p.get("importo_totale", 0) or 0), len(lista))
        except Exception:
            continue
        for (a, m), q in zip(lista, qs):
            if q > 0:
                out.append({"piano": p, "anno": a, "mese": m, "quota": q})
    return out

def totale_quote(self, anno, mese=None, conto=None):
    return sum(x["quota"] for x in quote(self, anno, mese, conto))

def quote_per_categoria(self, anno, mese=None, conto=None):
    r = {}
    for x in quote(self, anno, mese, conto):
        p = x["piano"]
        cat = p.get("categoria") or p.get("nome") or "Pianificata"
        r[cat] = r.get(cat, 0.0) + x["quota"]
    return r

def quote_per_anno(self, conto=None):
    r = {}
    for p in piani(self):
        if conto and (p.get("conto") or "") != conto:
            continue
        try:
            lista = _mesi_coperti(_parse_data(p["inizio"]), _parse_data(p["data_scadenza"]))
            qs = _quote_mensili(float(p.get("importo_totale", 0) or 0), len(lista))
        except Exception:
            continue
        for (a, _m), q in zip(lista, qs):
            r[a] = r.get(a, 0.0) + q
    return r

def html_blocco(self, ambito, anno, mese, conto=None):
    tutte = quote(self, anno, mese, conto)
    if not tutte and not piani(self):
        return ""
    on = attivo(ambito)
    righe = ""
    tot = 0.0
    for x in tutte:
        p = x["piano"]
        nome = (p.get("categoria") or p.get("nome") or "Pianificata")
        desc = p.get("descrizione") or ""
        tot += x["quota"]
        righe += (
            '<div style="display:flex;justify-content:space-between;gap:10px;padding:7px 0;'
            'border-top:1px solid var(--border);font-size:0.86em;">'
            f'<span>{_html.escape(str(nome))}'
            + (f' <small style="opacity:0.7">· {_html.escape(str(desc))}</small>' if desc else '')
            + f'</span><b style="color:var(--red);white-space:nowrap;">€ -{_fmt(x["quota"])}</b></div>'
        )
    if not righe:
        righe = ('<div style="padding:8px 0;font-size:0.84em;opacity:0.7;">'
                 'Nessuna quota pianificata in questo periodo.</div>')
    stato = "incluse nei totali" if on else "non incluse nei totali"
    nota = ("Le spese originali collegate ai piani sono escluse dai totali, al loro posto contano le quote."
            if on else "Le quote sono solo indicative: i totali contano le spese reali.")
    return (
        '<div style="margin:12px 0;padding:12px 14px;border:1px solid var(--border);'
        'border-radius:12px;background:var(--surface2);">'
        f'<div style="font-weight:800;font-size:0.9em;margin-bottom:4px;">📌 Quote pianificate '
        f'<span style="font-weight:600;opacity:0.7;">· {stato}</span></div>'
        f'<div style="font-size:0.76em;opacity:0.7;margin-bottom:6px;">{nota}</div>'
        f'{righe}'
        + (f'<div style="display:flex;justify-content:space-between;padding-top:8px;border-top:2px solid var(--border);'
           f'font-size:0.88em;"><b>Totale quote</b><b>€ -{_fmt(tot)}</b></div>' if len(tutte) > 1 else '')
        + f'<button type="button" onclick="togglePianificate(\'{ambito}\', {"false" if on else "true"})" '
        'style="margin-top:10px;width:100%;padding:10px;border-radius:10px;border:1px solid var(--border);'
        'background:var(--surface3);color:var(--text);font-family:inherit;font-weight:700;cursor:pointer;">'
        f'📌 {"Escludi dai totali" if on else "Includi nei totali"}</button></div>'
        + _SCRIPT
    )


def html_toggle(self, ambito):
    if not piani(self):
        return ""
    on = attivo(ambito)
    return (
        f'<button type="button" onclick="togglePianificate(\'{ambito}\', {"false" if on else "true"})" '
        'style="display:block;width:100%;margin:10px 0;padding:10px;border-radius:10px;border:1px solid var(--border);'
        'background:var(--surface3);color:var(--text);font-family:inherit;font-weight:700;cursor:pointer;">'
        f'📌 Quote pianificate: {"incluse" if on else "escluse"} · tocca per {"escluderle" if on else "includerle"}</button>'
        + _SCRIPT
    )


_SCRIPT = """<script>
if (typeof togglePianificate === 'undefined') {
    window.togglePianificate = function(ambito, attivo) {
        var u = new URL(location.href);
        if (attivo) u.searchParams.set('pian', '1'); else u.searchParams.delete('pian');
        location.href = u.toString();
    };
}
</script>"""
