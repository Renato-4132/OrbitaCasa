#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymupdf as fitz
import tkinter as tk
from tkinter import ttk
from moduli.modello_spesa import campo

def _fmt_it(v, spec=",.2f"):
    s = format(v, spec)
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def _genera_report_pdf_core(self, anno_da=None, anno_a=None, mese_filtro=0, sezioni=None):
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    import os
    _profilo_attivo_rep = getattr(_app, "PROFILO_ATTIVO", "Principale")
    current_folder = _profilo_attivo_rep if _profilo_attivo_rep != "Principale" else os.path.basename(os.getcwd())
    import datetime, tempfile, os, json
    from collections import defaultdict
    if sezioni is None:
        sezioni = {"mesi": True, "categorie": True, "storico": True, "portafoglio": True}
    oggi      = datetime.date.today()
    anno_curr = anno_a if anno_a is not None else oggi.year
    if anno_da is None:
        anno_da = anno_curr
    mesi_nomi   = ["","Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno",
                    "Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"]
    _db_p = {"conti": [], "trasferimenti": [], "saldo_fisico": 0.0}
    try:
        if os.path.exists(PORTAFOGLIO_BANCARIO):
            with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
                _db_p = json.load(_pf)
    except Exception:
        pass
    _id_a_nome  = {c["id"]: c.get("nome", "?") for c in _db_p.get("conti", [])}
    _agganci    = defaultdict(list)
    _agganci_uso = defaultdict(int)
    for _t in _db_p.get("trasferimenti", []):
        _data_t = _t.get("data", "")
        _imp_t  = round(float(_t.get("importo", 0)), 2)
        if _t.get("a") in ("__spese__", "Contabilità"):
            _tipo_t = "uscita"
            _cnome  = _id_a_nome.get(_t.get("da"), "")
        elif _t.get("da") in ("__spese__", "Contabilità"):
            _tipo_t = "entrata"
            _cnome  = _id_a_nome.get(_t.get("a"), "")
        else:
            continue
        if _cnome:
            _agganci[(_data_t, _imp_t, _tipo_t)].append(_cnome)
    def _nome_conto(data_obj, val, t_tipo):
        key   = (data_obj.strftime("%d-%m-%Y"), round(val, 2), t_tipo)
        lista = _agganci.get(key, [])
        uso   = _agganci_uso.get(key, 0)
        nome  = lista[uso] if uso < len(lista) else ""
        _agganci_uso[key] = uso + 1
        return nome
    data_punti          = defaultdict(float)
    movimenti_per_id    = defaultdict(list)
    tot_anno            = {"in": 0.0, "out": 0.0}
    tot_st              = {"in": 0.0, "out": 0.0}
    cat_anno_val        = defaultdict(float)
    cat_anno_count      = defaultdict(int)
    cat_st_val          = defaultdict(float)
    cat_st_count        = defaultdict(int)
    conto_anno_in       = defaultdict(float)
    conto_anno_out      = defaultdict(float)
    conto_st_in         = defaultdict(float)
    conto_st_out        = defaultdict(float)
    movimenti_per_conto_periodo = defaultdict(list)
    giorni_ordinati = sorted(self.spese.keys(), reverse=True)
    for giorno in giorni_ordinati:
        entries = self.spese[giorno]
        anno, mese = giorno.year, giorno.month
        for entry in entries:
            cat  = campo(entry, "categoria", "Varie")
            desc = campo(entry, "descrizione", "")
            imp  = campo(entry, "importo", 0)
            tipo = campo(entry, "tipo", "Uscita")
            try:
                val = float(str(imp).replace(",", ".").replace("€", "").strip())
            except Exception:
                val = 0
            t_tipo   = str(tipo).lower()
            suffix   = "in" if t_tipo == "entrata" else "out"
            data_str = giorno.strftime('%d/%m/%Y')
            conto    = campo(entry, "conto", "") or _nome_conto(giorno, val, t_tipo)
            metodo   = campo(entry, "metodo_pagamento", "")
            ora_val  = campo(entry, "ora", "")
            tag_val  = " ".join(campo(entry, "hashtag", []))
            riga     = (data_str, cat, desc, val, t_tipo, conto, metodo, ora_val, tag_val, giorno)
            tot_st[suffix] += val
            data_punti[f"st_a_{anno}_{suffix}"] += val
            if t_tipo == "uscita":
                cat_st_val[cat]   += val
                cat_st_count[cat] += 1
            if conto:
                if t_tipo == "entrata":
                    conto_st_in[conto] += val
                else:
                    conto_st_out[conto] += val
            if anno_da <= anno <= anno_curr and (mese_filtro == 0 or mese == mese_filtro):
                tot_anno[suffix] += val
                data_punti[f"curr_m_{mese}_{suffix}"] += val
                if t_tipo == "uscita":
                    cat_anno_val[cat]   += val
                    cat_anno_count[cat] += 1
                    movimenti_per_id[f"curr_cat_{cat}"].append(riga)
                movimenti_per_id[f"curr_m_{mese}_{suffix}"].append(riga)
                if conto:
                    if t_tipo == "entrata":
                        conto_anno_in[conto] += val
                    else:
                        conto_anno_out[conto] += val
                    movimenti_per_conto_periodo[conto].append(riga)
    anni_lista   = sorted(set(int(k.split('_')[2]) for k in data_punti if k.startswith('st_a_')))
    mesi_attivi  = sorted(m for m in range(1, 13)
                          if data_punti[f"curr_m_{m}_in"] > 0 or data_punti[f"curr_m_{m}_out"] > 0)
    cat_a_sorted = sorted(cat_anno_val, key=lambda x: cat_anno_val[x], reverse=True)
    cat_s_sorted = sorted(cat_st_val,   key=lambda x: cat_st_val[x],   reverse=True)
    import locale
    _locale_originale = locale.setlocale(locale.LC_ALL, None)
    try:
        locale.setlocale(locale.LC_ALL, 'it_IT.UTF-8')
        cat_a_alfa = sorted(cat_anno_val, key=lambda x: locale.strxfrm(x.lower()))
        cat_s_alfa = sorted(cat_st_val,   key=lambda x: locale.strxfrm(x.lower()))
    except locale.Error:
        cat_a_alfa = sorted(cat_anno_val, key=lambda x: x.lower())
        cat_s_alfa = sorted(cat_st_val,   key=lambda x: x.lower())
    finally:
        try:
            locale.setlocale(locale.LC_ALL, _locale_originale)
        except locale.Error:
            pass
    range_anni = f"{anni_lista[0]}-{anni_lista[-1]}" if anni_lista else str(anno_curr)
    W, H        = 595, 842
    MARG        = 40
    C_BG        = (0.95, 0.97, 0.96)
    C_HEADER    = (0.17, 0.24, 0.31)
    C_WHITE     = (1, 1, 1)
    C_GREEN     = (0.18, 0.80, 0.44)
    C_RED       = (0.91, 0.30, 0.24)
    C_ORANGE    = (0.95, 0.61, 0.07)
    C_DARKRED   = (0.75, 0.22, 0.17)
    C_BLUE      = (0.20, 0.60, 0.86)
    C_PURPLE    = (0.55, 0.27, 0.68)
    C_TEAL      = (0.13, 0.70, 0.67)
    C_TEXT      = (0.17, 0.24, 0.31)
    C_SUBTEXT   = (0.50, 0.55, 0.60)
    C_LINE      = (0.88, 0.90, 0.92)
    PALETTE_CONTI = [
        (0.20, 0.60, 0.86),
        (0.18, 0.80, 0.44),
        (0.95, 0.61, 0.07),
        (0.55, 0.27, 0.68),
        (0.13, 0.70, 0.67),
        (0.91, 0.30, 0.24),
        (0.96, 0.49, 0.00),
        (0.25, 0.47, 0.82),
    ]
    tutti_conti_nomi = sorted(set(list(conto_st_in.keys()) + list(conto_st_out.keys())))
    colore_conto = {
        nome: PALETTE_CONTI[i % len(PALETTE_CONTI)]
        for i, nome in enumerate(tutti_conti_nomi)
    }
    doc = fitz.open()
    def nuova_pagina():
        page = doc.new_page(width=W, height=H)
        page.draw_rect(fitz.Rect(0, 0, W, H), color=None, fill=C_BG)
        return page
    def header_pagina(page, titolo, sottotitolo=""):
        page.draw_rect(fitz.Rect(0, 0, W, 52), color=None, fill=C_HEADER)
        page.insert_text((MARG, 32), titolo,
                         fontsize=13, color=C_WHITE, fontname="Helvetica")
        if sottotitolo:
            page.insert_text((W - MARG - len(sottotitolo) * 5.5, 32), sottotitolo,
                             fontsize=9, color=(0.7, 0.75, 0.8), fontname="Helvetica")
        page.insert_text((MARG, 46), f"Generato il {oggi.strftime('%d/%m/%Y')}",
                         fontsize=7, color=(0.6, 0.65, 0.7), fontname="Helvetica")
    def card(page, y, h, titolo):
        r = fitz.Rect(MARG, y, W - MARG, y + h)
        page.draw_rect(r, color=None, fill=C_WHITE)
        page.draw_rect(fitz.Rect(MARG, y, MARG + 4, y + h),
                       color=None, fill=C_BLUE)
        page.insert_text((MARG + 12, y + 16), titolo,
                         fontsize=9, color=C_TEXT, fontname="Helvetica-Bold")
        page.draw_line((MARG + 12, y + 20), (W - MARG - 8, y + 20),
                       color=C_LINE, width=0.5)
        return y + 26
    def card_colored(page, y, h, titolo, colore_accent):
        r = fitz.Rect(MARG, y, W - MARG, y + h)
        page.draw_rect(r, color=None, fill=C_WHITE)
        page.draw_rect(fitz.Rect(MARG, y, MARG + 4, y + h),
                       color=None, fill=colore_accent)
        page.insert_text((MARG + 12, y + 16), titolo,
                         fontsize=9, color=C_TEXT, fontname="Helvetica-Bold")
        page.draw_line((MARG + 12, y + 20), (W - MARG - 8, y + 20),
                       color=C_LINE, width=0.5)
        return y + 26
    def totali_row(page, y, items):
        box_w = (W - MARG * 2 - 8) / len(items)
        for i, (label, valore, colore) in enumerate(items):
            bx = MARG + 12 + i * box_w
            page.draw_rect(fitz.Rect(bx, y, bx + box_w - 6, y + 28),
                           color=C_LINE, fill=(0.97, 0.98, 0.99))
            page.insert_text((bx + 6, y + 11), label,
                             fontsize=7, color=C_SUBTEXT, fontname="Helvetica")
            page.insert_text((bx + 6, y + 23), valore,
                             fontsize=9, color=colore, fontname="Helvetica-Bold")
        return y + 34
    def grafico_barre(page, y, labels, datasets, altezza_barra=14, gap=6):
        if not labels:
            return y
        max_val = max((max(d["valori"]) for d in datasets if d["valori"]), default=1)
        if max_val == 0:
            max_val = 1
        bar_area_w = W - MARG * 2 - 160
        lbl_w      = 150
        VAL_W      = 55
        bar_max_w  = bar_area_w - VAL_W
        n_ds       = len(datasets)
        step       = altezza_barra * n_ds + gap
        lx = MARG + 12 + lbl_w + 10
        for i, ds in enumerate(datasets):
            page.draw_rect(fitz.Rect(lx + i * 70, y, lx + i * 70 + 10, y + 8),
                   color=None, fill=ds["colore"])
            page.insert_text((lx + i * 70 + 13, y + 8), ds["label"],
                     fontsize=7, color=C_SUBTEXT, fontname="Helvetica")
        y += 14
        for idx, lbl in enumerate(labels):
            by = y + idx * step
            lbl_corta = lbl[:28] + "…" if len(lbl) > 28 else lbl
            page.insert_text((MARG + 12, by + altezza_barra - 2), lbl_corta,
                     fontsize=7, color=C_TEXT, fontname="Helvetica")
            for di, ds in enumerate(datasets):
                val = ds["valori"][idx] if idx < len(ds["valori"]) else 0
                bw  = min((val / max_val) * bar_area_w, bar_max_w)
                bx  = MARG + 12 + lbl_w
                by2 = by + di * altezza_barra
                if bw > 0:
                    page.draw_rect(
                        fitz.Rect(bx, by2 + 1, bx + bw, by2 + altezza_barra - 1),
                        color=None, fill=ds["colore"]
                    )
                val_str = f"€ {_fmt_it(val, ',.0f')}"
                page.insert_text((bx + bw + 4, by2 + altezza_barra - 2), val_str,
                         fontsize=6.5, color=ds["colore"], fontname="Helvetica-Bold")
        return y + len(labels) * step + 8
    def pagina_movimenti(titolo, sottotitolo, righe):
        if not righe:
            return
        from datetime import datetime as _dt
        righe_ord = sorted(
            righe,
            key=lambda r: r[9] if len(r) > 9 else _dt.strptime(r[0], '%d/%m/%Y')
        )
        page      = nuova_pagina()
        header_pagina(page, titolo, sottotitolo)
        cy = 68
        def intestazione_tab(p, y):
            p.draw_rect(fitz.Rect(MARG, y, W - MARG, y + 16),
                        color=None, fill=C_HEADER)
            p.insert_text((MARG + 4,   y + 11), "Data",        fontsize=7, color=C_WHITE, fontname="Helvetica-Bold")
            p.insert_text((MARG + 55,  y + 11), "Categoria",   fontsize=7, color=C_WHITE, fontname="Helvetica-Bold")
            p.insert_text((MARG + 108, y + 11), "Descrizione", fontsize=7, color=C_WHITE, fontname="Helvetica-Bold")
            p.insert_text((MARG + 240, y + 11), "Conto",       fontsize=7, color=C_WHITE, fontname="Helvetica-Bold")
            p.insert_text((MARG + 310, y + 11), "Metodo",      fontsize=7, color=C_WHITE, fontname="Helvetica-Bold")
            p.insert_text((MARG + 360, y + 11), "Ora",         fontsize=7, color=C_WHITE, fontname="Helvetica-Bold")
            p.insert_text((MARG + 392, y + 11), "Tag",         fontsize=7, color=C_WHITE, fontname="Helvetica-Bold")
            p.insert_text((W-MARG-60,  y + 11), "Importo",     fontsize=7, color=C_WHITE, fontname="Helvetica-Bold")
            p.insert_text((W-MARG-18,  y + 11), "T",           fontsize=7, color=C_WHITE, fontname="Helvetica-Bold")
            return y + 18
        cy = intestazione_tab(page, cy)
        for i, riga in enumerate(righe_ord):
            data_s, cat, desc, val, tipo = riga[0], riga[1], riga[2], riga[3], riga[4]
            conto_r  = riga[5] if len(riga) > 5 else ""
            metodo_r = riga[6] if len(riga) > 6 else ""
            ora_r    = riga[7] if len(riga) > 7 else ""
            tag_r    = riga[8] if len(riga) > 8 else ""
            if cy > H - 50:
                page = nuova_pagina()
                header_pagina(page, titolo, sottotitolo)
                cy = 68
                cy = intestazione_tab(page, cy)
            bg = C_WHITE if i % 2 == 0 else (0.96, 0.97, 0.98)
            page.draw_rect(fitz.Rect(MARG, cy, W - MARG, cy + 13),
                           color=None, fill=bg)
            colore_val  = C_GREEN if tipo == "entrata" else C_RED
            desc_corta  = desc[:28]  + "…" if len(desc)  > 28  else desc
            conto_corto = conto_r[:12] + "…" if len(conto_r) > 12 else conto_r
            metodo_corto = metodo_r[:10] + "…" if len(metodo_r) > 10 else metodo_r
            tag_corto   = tag_r[:20] + "…" if len(tag_r) > 20 else tag_r
            c_conto     = colore_conto.get(conto_r, C_SUBTEXT) if conto_r else C_SUBTEXT
            page.insert_text((MARG + 4,   cy + 10), data_s,         fontsize=7,   color=C_TEXT,     fontname="Helvetica")
            page.insert_text((MARG + 55,  cy + 10), cat[:12],       fontsize=7,   color=C_TEXT,     fontname="Helvetica")
            page.insert_text((MARG + 108, cy + 10), desc_corta,     fontsize=6.5, color=C_SUBTEXT,  fontname="Helvetica")
            page.insert_text((MARG + 240, cy + 10), conto_corto,    fontsize=6.5, color=c_conto,    fontname="Helvetica-Bold")
            page.insert_text((MARG + 310, cy + 10), metodo_corto,   fontsize=6.5, color=C_SUBTEXT,  fontname="Helvetica")
            page.insert_text((MARG + 360, cy + 10), ora_r,          fontsize=6.5, color=C_SUBTEXT,  fontname="Helvetica")
            page.insert_text((MARG + 392, cy + 10), tag_corto,      fontsize=6.5, color=C_SUBTEXT,  fontname="Helvetica")
            page.insert_text((W-MARG-60,  cy + 10), f"€{_fmt_it(val)}", fontsize=7,   color=colore_val, fontname="Helvetica-Bold")
            page.insert_text((W-MARG-18,  cy + 10), tipo[0].upper(),fontsize=6,   color=C_SUBTEXT,  fontname="Helvetica")
            cy += 13
    page = nuova_pagina()
    _titolo_periodo = str(anno_curr) if anno_da == anno_curr else f"{anno_da}–{anno_curr}"
    if mese_filtro > 0:
        _titolo_periodo += f"  ·  {mesi_nomi[mese_filtro]}"
    header_pagina(page, f"Report Finanziario — {_titolo_periodo}", current_folder)
    cy = 68
    h_card1 = 46 + len(mesi_attivi) * 34 + 30
    cy = card(page, cy, h_card1, f"Riepilogo {_titolo_periodo}")
    saldo_a   = tot_anno['in'] - tot_anno['out']
    c_saldo_a = C_GREEN if saldo_a >= 0 else C_RED
    cy = totali_row(page, cy, [
        ("ENTRATE", f"€ {_fmt_it(tot_anno['in'])}",  C_GREEN),
        ("USCITE",  f"€ {_fmt_it(tot_anno['out'])}", C_RED),
        ("SALDO",   f"€ {_fmt_it(saldo_a)}",          c_saldo_a),
    ])
    labels_mesi = [
        f"{mesi_nomi[m]} ({'+' if (data_punti[f'curr_m_{m}_in']-data_punti[f'curr_m_{m}_out'])>=0 else ''}€{_fmt_it(data_punti[f'curr_m_{m}_in']-data_punti[f'curr_m_{m}_out'], ',.0f')})"
        for m in mesi_attivi
    ]
    cy = grafico_barre(page, cy, labels_mesi, [
        {"valori": [data_punti[f"curr_m_{m}_in"]  for m in mesi_attivi], "colore": C_GREEN, "label": "Entrate"},
        {"valori": [data_punti[f"curr_m_{m}_out"] for m in mesi_attivi], "colore": C_RED,   "label": "Uscite"},
    ])
    cy += 10
    if sezioni.get("categorie", True) and cat_a_sorted:
        h_card2 = 46 + len(cat_a_sorted) * 20 + 20
        if cy + h_card2 > H - MARG:
            page = nuova_pagina()
            header_pagina(page, f"Report — Categorie {_titolo_periodo}")
            cy = 68
        cy = card(page, cy, h_card2, f"Categorie Uscite {_titolo_periodo}")
        cy = grafico_barre(page, cy,
            [f"{c} ({cat_anno_count[c]})" for c in cat_a_sorted],
            [{"valori": [cat_anno_val[c] for c in cat_a_sorted], "colore": C_ORANGE, "label": "Uscite"}],
            altezza_barra=16, gap=4
        )
    conti_db = _db_p.get("conti", [])
    if sezioni.get("portafoglio", True) and conti_db:
        page = nuova_pagina()
        header_pagina(page, "Portafoglio Bancario", current_folder)
        cy = 68
        totale_portafoglio = sum(float(c.get("saldo", 0)) for c in conti_db)
        h_card_p = 46 + len(conti_db) * 42 + 20
        cy = card(page, cy, h_card_p, "Saldi Conti")
        for c in conti_db:
            nome_c   = c.get("nome", "?")
            saldo_c  = float(c.get("saldo", 0))
            tipo_c   = c.get("tipo", "altro")
            princ_c  = c.get("principale", False)
            colore_c = colore_conto.get(nome_c, C_BLUE)
            bar_w_max = W - MARG * 2 - 30
            bar_fill  = int((abs(saldo_c) / max(abs(totale_portafoglio), 1)) * bar_w_max)
            bar_fill  = max(bar_fill, 4)
            page.draw_rect(fitz.Rect(MARG + 8, cy, W - MARG - 8, cy + 36),
                           color=C_LINE, fill=(0.97, 0.98, 0.99))
            page.draw_rect(fitz.Rect(MARG + 8, cy, MARG + 12, cy + 36),
                           color=None, fill=colore_c)
            label_c = f"{'★ ' if princ_c else ''}{nome_c}  [{tipo_c}]"
            page.insert_text((MARG + 18, cy + 13), label_c,
                             fontsize=8, color=C_TEXT, fontname="Helvetica-Bold")
            col_s = C_GREEN if saldo_c >= 0 else C_RED
            page.insert_text((W - MARG - 80, cy + 13), f"€ {_fmt_it(saldo_c)}",
                             fontsize=9, color=col_s, fontname="Helvetica-Bold")
            page.draw_rect(fitz.Rect(MARG + 18, cy + 20, MARG + 18 + bar_fill, cy + 26),
                           color=None, fill=colore_c)
            e_a = conto_anno_in.get(nome_c, 0)
            u_a = conto_anno_out.get(nome_c, 0)
            page.insert_text((MARG + 18, cy + 33),
                             f"{_titolo_periodo}: +€{_fmt_it(e_a, ',.0f')}  -€{_fmt_it(u_a, ',.0f')}",
                             fontsize=6.5, color=C_SUBTEXT, fontname="Helvetica")
            cy += 42
        cy += 6
        page.draw_rect(fitz.Rect(MARG + 8, cy, W - MARG - 8, cy + 24),
                       color=None, fill=C_HEADER)
        page.insert_text((MARG + 18, cy + 16), "TOTALE PORTAFOGLIO",
                         fontsize=8, color=C_WHITE, fontname="Helvetica-Bold")
        page.insert_text((W - MARG - 85, cy + 16), f"€ {_fmt_it(totale_portafoglio)}",
                         fontsize=10, color=C_GREEN if totale_portafoglio >= 0 else C_RED,
                         fontname="Helvetica-Bold")
        cy += 34
        conti_con_mov_a = [n for n in tutti_conti_nomi
                           if conto_anno_in.get(n, 0) > 0 or conto_anno_out.get(n, 0) > 0]
        if conti_con_mov_a:
            h_card_ca = 46 + len(conti_con_mov_a) * 34 + 20
            if cy + h_card_ca > H - MARG:
                page = nuova_pagina()
                header_pagina(page, f"Portafoglio — Movimenti {_titolo_periodo}")
                cy = 68
            cy = card(page, cy, h_card_ca, f"Movimenti per Conto — {_titolo_periodo}")
            cy = grafico_barre(page, cy, conti_con_mov_a, [
                {"valori": [conto_anno_in.get(n, 0)  for n in conti_con_mov_a], "colore": C_GREEN, "label": "Entrate"},
                {"valori": [conto_anno_out.get(n, 0) for n in conti_con_mov_a], "colore": C_RED,   "label": "Uscite"},
            ])
            cy += 10
        conti_con_mov_s = [n for n in tutti_conti_nomi
                           if conto_st_in.get(n, 0) > 0 or conto_st_out.get(n, 0) > 0]
        if conti_con_mov_s:
            h_card_cs = 46 + len(conti_con_mov_s) * 34 + 20
            if cy + h_card_cs > H - MARG:
                page = nuova_pagina()
                header_pagina(page, "Portafoglio — Storico Conti")
                cy = 68
            cy = card(page, cy, h_card_cs, f"Movimenti Storici per Conto ({range_anni})")
            cy = grafico_barre(page, cy, conti_con_mov_s, [
                {"valori": [conto_st_in.get(n, 0)  for n in conti_con_mov_s], "colore": C_GREEN, "label": "Entrate"},
                {"valori": [conto_st_out.get(n, 0) for n in conti_con_mov_s], "colore": C_RED,   "label": "Uscite"},
            ])
    if sezioni.get("storico", True) and anni_lista:
        page = nuova_pagina()
        header_pagina(page, f"Bilancio Storico ({range_anni})", current_folder)
        cy = 68
        h_card3 = 46 + len(anni_lista) * 34 + 30
        cy = card(page, cy, h_card3, f"Bilancio Storico {range_anni}")
        saldo_s   = tot_st['in'] - tot_st['out']
        c_saldo_s = C_GREEN if saldo_s >= 0 else C_RED
        cy = totali_row(page, cy, [
            ("Tot. Entrate", f"€ {_fmt_it(tot_st['in'])}",  C_GREEN),
            ("Tot. Uscite",  f"€ {_fmt_it(tot_st['out'])}", C_RED),
            ("Saldo Totale", f"€ {_fmt_it(saldo_s)}",        c_saldo_s),
        ])
        labels_anni = [
            f"Anno {a} ({'+' if (data_punti[f'st_a_{a}_in']-data_punti[f'st_a_{a}_out'])>=0 else ''}€{_fmt_it(data_punti[f'st_a_{a}_in']-data_punti[f'st_a_{a}_out'], ',.0f')})"
            for a in anni_lista
        ]
        cy = grafico_barre(page, cy, labels_anni, [
            {"valori": [data_punti[f"st_a_{a}_in"]  for a in anni_lista], "colore": C_GREEN, "label": "Entrate"},
            {"valori": [data_punti[f"st_a_{a}_out"] for a in anni_lista], "colore": C_RED,   "label": "Uscite"},
        ])
        cy += 10
        if cat_s_sorted:
            h_card4 = 46 + len(cat_s_sorted) * 20 + 20
            if cy + h_card4 > H - MARG:
                page = nuova_pagina()
                header_pagina(page, "Categorie Storiche")
                cy = 68
            cy = card(page, cy, h_card4, "Categorie Uscite Storiche")
            cy = grafico_barre(page, cy,
                [f"{c} ({cat_st_count[c]})" for c in cat_s_sorted],
                [{"valori": [cat_st_val[c] for c in cat_s_sorted], "colore": C_DARKRED, "label": "Uscite"}],
                altezza_barra=16, gap=4
            )
    if sezioni.get("mesi", True):
        for m in mesi_attivi:
            righe_in  = movimenti_per_id.get(f"curr_m_{m}_in",  [])
            righe_out = movimenti_per_id.get(f"curr_m_{m}_out", [])
            tutte = righe_in + righe_out
            if tutte:
                tot_m_in  = sum(r[3] for r in righe_in)
                tot_m_out = sum(r[3] for r in righe_out)
                saldo_m   = tot_m_in - tot_m_out
                s_segno   = "+" if saldo_m >= 0 else ""
                _titolo_mese = f"{mesi_nomi[m]}" if anno_da != anno_curr else f"{mesi_nomi[m]} {anno_curr}"
                pagina_movimenti(
                    _titolo_mese,
                    f"Entrate € {_fmt_it(tot_m_in)}  |  Uscite € {_fmt_it(tot_m_out)}  |  Saldo {s_segno}€ {_fmt_it(saldo_m)}",
                    tutte
                )
    if sezioni.get("categorie", True):
        for cat in cat_a_alfa:
            righe = movimenti_per_id.get(f"curr_cat_{cat}", [])
            if righe:
                tot_cat = sum(r[3] for r in righe)
                pagina_movimenti(
                    f"Categoria: {cat} — {_titolo_periodo}",
                    f"{cat_anno_count[cat]} movimenti  |  Totale € {_fmt_it(tot_cat)}",
                    righe
                )
    if sezioni.get("portafoglio", True):
        for nome_c in sorted(movimenti_per_conto_periodo.keys()):
            righe = movimenti_per_conto_periodo[nome_c]
            if righe:
                tot_c_in  = sum(r[3] for r in righe if r[4] == "entrata")
                tot_c_out = sum(r[3] for r in righe if r[4] == "uscita")
                saldo_c_r = tot_c_in - tot_c_out
                s_segno   = "+" if saldo_c_r >= 0 else ""
                pagina_movimenti(
                    f"Conto: {nome_c}",
                    f"Entrate € {_fmt_it(tot_c_in)}  |  Uscite € {_fmt_it(tot_c_out)}  |  Saldo {s_segno}€ {_fmt_it(saldo_c_r)}",
                    righe
                )
    n_tot = doc.page_count
    for i, page in enumerate(doc):
        page.insert_text(
            (W - MARG - 40, H - 12),
            f"Pagina {i+1} / {n_tot}",
            fontsize=7, color=C_SUBTEXT, fontname="Helvetica"
        )
    temp_path = os.path.join(tempfile.gettempdir(), "report_OrbitaCasa.pdf")
    doc.save(temp_path)
    doc.close()
    self.after(0, lambda: self._apri_viewer_report(temp_path))
    
def _apri_viewer_report(self, pdf_path):
    import __main__ as _app
    EXPORT_FILES = _app.EXPORT_FILES
    import os
    _profilo_attivo_rep2 = getattr(_app, "PROFILO_ATTIVO", "Principale")
    current_folder = _profilo_attivo_rep2 if _profilo_attivo_rep2 != "Principale" else os.path.basename(os.getcwd())

    import os, datetime
    oggi = datetime.date.today()
    doc = fitz.open(pdf_path)
    pagina_corrente = [0]
    zoom_level = [1.5]
    win = tk.Toplevel(self, bg=self.COLOR_BACKGROUND)
    win.withdraw()
    win.title(f"Bilancio — {current_folder}")
    win.configure(bd=0)
    win.bind('<Escape>', lambda e: win.destroy())
    header = tk.Frame(win, bg=self.COLOR_HEADER_BG, height=42)
    header.pack(fill="x")
    header.pack_propagate(False)
    dot_canvas = tk.Canvas(header, width=10, height=10,
                           bg=self.COLOR_HEADER_BG, highlightthickness=0)
    dot_canvas.create_oval(0, 0, 10, 10, fill=self.COLOR_HIGHLIGHT, outline="")
    dot_canvas.pack(side="left", padx=(16, 8), pady=16)
    tk.Label(header, text="Report Finanziario",
             bg=self.COLOR_HEADER_BG, fg=self.COLOR_HEADER,
             font=("Segoe UI", 8, "bold")).pack(side="left")
    tk.Frame(win, bg=self.COLOR_BACKGROUND, height=1).pack(fill="x")
    frame_pdf = tk.Frame(win, bg=self.COLOR_WIDGET_BG,
                         highlightbackground=self.COLOR_HEADER_BG,
                         highlightthickness=1)
    frame_pdf.pack(padx=16, pady=(12, 0), fill='both', expand=True)
    scrollbar_y = ttk.Scrollbar(frame_pdf, style="Vertical.TScrollbar")
    scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
    scrollbar_x = ttk.Scrollbar(frame_pdf, orient="horizontal")
    scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
    canvas_pdf = tk.Canvas(frame_pdf,
                           bg=self.COLOR_WIDGET_BG,
                           yscrollcommand=scrollbar_y.set,
                           xscrollcommand=scrollbar_x.set,
                           highlightthickness=0)
    canvas_pdf.pack(side=tk.LEFT, fill='both', expand=True)
    scrollbar_y.config(command=canvas_pdf.yview)
    scrollbar_x.config(command=canvas_pdf.xview)
    tk.Frame(win, bg=self.COLOR_BACKGROUND, height=1).pack(fill="x", pady=(10, 0))
    frame_ctrl = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    frame_ctrl.pack(pady=10)
    img_prev = self.icone_gui.get("indietro")
    btn_prev = ttk.Label(frame_ctrl, compound="left", image=img_prev,
                         text=" Indietro" if img_prev else "◀ Indietro",
                         background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                         cursor="hand2", padding=(10, 5))
    btn_prev.image = img_prev
    btn_prev.pack(side="left", padx=5)
    lbl_pagina = tk.Label(frame_ctrl, text=f"Pagina 1 / {len(doc)}",
                          bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
                          font=("Segoe UI", 9))
    lbl_pagina.pack(side="left", padx=12)
    img_next = self.icone_gui.get("avanti")
    btn_next = ttk.Label(frame_ctrl, compound="left", image=img_next,
                         text=" Avanti" if img_next else "Avanti ▶",
                         background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                         cursor="hand2", padding=(10, 5))
    btn_next.image = img_next
    btn_next.pack(side="left", padx=5)
    tk.Frame(frame_ctrl, bg=self.COLOR_BACKGROUND, width=20).pack(side="left")
    btn_zoom_out = ttk.Label(frame_ctrl, text="  −  ",
                             background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                             cursor="hand2", padding=(8, 5), font=("Segoe UI", 11, "bold"))
    btn_zoom_out.pack(side="left", padx=2)
    lbl_zoom = tk.Label(frame_ctrl, text="150%",
                        bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
                        font=("Segoe UI", 9), width=5)
    lbl_zoom.pack(side="left")
    btn_zoom_in = ttk.Label(frame_ctrl, text="  +  ",
                            background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                            cursor="hand2", padding=(8, 5), font=("Segoe UI", 11, "bold"))
    btn_zoom_in.pack(side="left", padx=2)
    tk.Frame(frame_ctrl, bg=self.COLOR_BACKGROUND, width=20).pack(side="left")
    img_stampa = self.icone_gui.get("stampa")
    btn_stampa = ttk.Label(frame_ctrl, compound="left", image=img_stampa,
                           text=" Stampa" if img_stampa else "Stampa",
                           background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                           cursor="hand2", padding=(10, 5))
    btn_stampa.image = img_stampa
    btn_stampa.pack(side="left", padx=5)
    img_salva = self.icone_gui.get("salva")
    btn_salva = ttk.Label(frame_ctrl, compound="left", image=img_salva,
                          text=" Salva" if img_salva else "Salva",
                          background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                          cursor="hand2", padding=(10, 5))
    btn_salva.image = img_salva
    btn_salva.pack(side="left", padx=5)
    tk.Frame(frame_ctrl, bg=self.COLOR_BACKGROUND, width=20).pack(side="left")
    img_chiudi = self.icone_gui.get("chiudi")
    btn_chiudi = ttk.Label(frame_ctrl, compound="left", image=img_chiudi,
                           text=" Chiudi" if img_chiudi else "Chiudi",
                           background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                           cursor="hand2", padding=(10, 5))
    btn_chiudi.image = img_chiudi
    btn_chiudi.pack(side="left", padx=5)
    img_ref = [None]
    def render_pagina():
        page = doc[pagina_corrente[0]]
        mat = fitz.Matrix(zoom_level[0], zoom_level[0])
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("ppm")
        img = tk.PhotoImage(data=img_data)
        img_ref[0] = img
        canvas_pdf.delete("all")
        canvas_pdf.create_image(0, 0, anchor="nw", image=img)
        canvas_pdf.config(scrollregion=(0, 0, pix.width, pix.height))
        canvas_pdf.yview_moveto(0)
        lbl_pagina.config(text=f"Pagina {pagina_corrente[0] + 1} / {len(doc)}")
        lbl_zoom.config(text=f"{int(zoom_level[0] * 100)}%")
    def vai_prev():
        if pagina_corrente[0] > 0:
            pagina_corrente[0] -= 1
            render_pagina()
    def vai_next():
        if pagina_corrente[0] < len(doc) - 1:
            pagina_corrente[0] += 1
            render_pagina()
    def zoom_in():
        if zoom_level[0] < 3.0:
            zoom_level[0] = round(zoom_level[0] + 0.25, 2)
            render_pagina()
    def zoom_out():
        if zoom_level[0] > 0.5:
            zoom_level[0] = round(zoom_level[0] - 0.25, 2)
            render_pagina()
    def stampa():
        if os.name == 'nt':
            os.startfile(pdf_path, "print")
        else:
            import subprocess
            subprocess.run(["lp", pdf_path])
    def salva():
        from tkinter import filedialog
        import shutil
        dest = filedialog.asksaveasfilename(
            parent=win,
            title="Salva Bilancio",
            confirmoverwrite=False,
            initialdir=EXPORT_FILES,
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile=f"Bilancio_{current_folder}_{oggi.strftime('%d-%m-%Y')}.pdf"
        )
        if dest:
            try:
                shutil.copy2(pdf_path, dest)
                self.show_custom_info("Salvataggio", f"Report salvato in:\n{dest}")
            except Exception as e:
                self.show_custom_warning("Errore", f"Salvataggio fallito:\n{e}")

    btn_prev.bind("<Button-1>",    lambda e: vai_prev())
    btn_next.bind("<Button-1>",    lambda e: vai_next())
    btn_zoom_in.bind("<Button-1>", lambda e: zoom_in())
    btn_zoom_out.bind("<Button-1>",lambda e: zoom_out())
    btn_stampa.bind("<Button-1>",  lambda e: stampa())
    btn_salva.bind("<Button-1>",   lambda e: salva())
    btn_chiudi.bind("<Button-1>",  lambda e: win.destroy())
    win.bind("<Left>",  lambda e: vai_prev())
    win.bind("<Right>", lambda e: vai_next())
    canvas_pdf.bind("<MouseWheel>", lambda e: canvas_pdf.yview_scroll(int(-1*(e.delta/120)), "units"))
    canvas_pdf.bind("<Button-4>",   lambda e: canvas_pdf.yview_scroll(-1, "units"))
    canvas_pdf.bind("<Button-5>",   lambda e: canvas_pdf.yview_scroll(1,  "units"))
    win.update_idletasks()
    min_w, min_h = 950, 630
    w = max(win.winfo_width(), min_w)
    h = max(win.winfo_height(), min_h)
    x = self.winfo_rootx() + (self.winfo_width()  // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    if self.state() == 'iconic':
        self.deiconify()
        self.lift()
        self.focus_force()
    win.geometry(f"{w}x{h}+{x}+{y}")
    win.minsize(min_w, min_h)
    win.deiconify()
    win.transient(self)
    win.focus_set()
    render_pagina()
    win.wait_window()
    doc.close()
    try:
        os.remove(pdf_path)
    except Exception:
        pass
        
