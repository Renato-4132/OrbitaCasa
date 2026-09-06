#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import calendar
import math
import json
import datetime
import tkinter as tk
from moduli.modello_spesa import campo, SIMBOLI_METODO, NOME_DA_EMOJI

def _fmt_it(v, spec=",.2f"):
    s = format(v, spec)
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def _mostra_tip_safe(self, event, testo):
    if hasattr(self, '_tip_after_id') and self._tip_after_id:
        self.after_cancel(self._tip_after_id)
        self._tip_after_id = None
    def _mostra():
        if not self.tooltip_win or not self.tooltip_win.winfo_exists():
            self.tooltip_win = tk.Toplevel(self)
            self.tooltip_win.overrideredirect(True)
            self.tooltip_win.withdraw()
        self.tooltip_win.withdraw()
        self.tooltip_win.config(
                highlightthickness=1,
                highlightbackground=self.COLOR_HIGHLIGHT)
        for ch in self.tooltip_win.winfo_children():
            ch.destroy()
        main_frame = tk.Frame(self.tooltip_win, bg=self.COLOR_TOOLTIP,
                              relief="solid", borderwidth=1)
        main_frame.pack(fill="both", expand=True)
        for riga in testo.split('\n'):
            if not riga.strip():
                continue
            if "-" in riga:
                fg = self.COLOR_RED_SMOOTH
            elif "+" in riga:
                fg = self.COLOR_GREEN_SMOOTH
            else:
                fg = self.COLOR_TEXT_TOOLTIP
            tk.Label(main_frame, text=riga, fg=fg, bg=self.COLOR_TOOLTIP,
                     font=("Courier New", 9, "bold"), justify="left",
                     padx=10, pady=2).pack(anchor="w")
        self.tooltip_win.update_idletasks()
        tw = self.tooltip_win.winfo_reqwidth()
        th = self.tooltip_win.winfo_reqheight()
        sx, sy = self.winfo_rootx(), self.winfo_rooty()
        sw, sh = self.winfo_width(), self.winfo_height()
        x = event.x_root + 15
        y = event.y_root + 10
        if x + tw > sx + sw:
            x = event.x_root - tw - 5
        if y + th > sy + sh:
            y = event.y_root - th - 5
        if x < sx:
            x = sx + 5
        if y < sy:
            y = sy + 5
        self.tooltip_win.geometry(f"+{int(x)}+{int(y)}")
        self.tooltip_win.deiconify()
        self.tooltip_win.attributes("-topmost", True)
    self._tip_after_id = self.after(200, _mostra)

def _nascondi_tip_safe(self):
    if hasattr(self, '_tip_after_id') and self._tip_after_id:
        self.after_cancel(self._tip_after_id)
        self._tip_after_id = None
    if self.tooltip_win and self.tooltip_win.winfo_exists():
        self.tooltip_win.withdraw()

def draw_estratto_metodo(self):
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    if not hasattr(self, 'canvas_estratto_metodo') or not self.canvas_estratto_metodo.winfo_exists():
        return
    c = self.canvas_estratto_metodo
    c.delete("all")
    w = c.winfo_width()
    h = c.winfo_height()
    if w < 10 or h < 10:
        return
    _simboli_metodo = NOME_DA_EMOJI
    now = datetime.date.today()
    view_year  = getattr(self, '_view_year',  now.year)
    view_month = getattr(self, '_view_month', now.month)
    _agganci_conto = {}
    try:
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
            _db_p = json.load(_pf)
        _id_a_nome = {conto["id"]: conto.get("nome", "") for conto in _db_p.get("conti", [])}
        for _t in _db_p.get("trasferimenti", []):
            if _t.get("da") in ("__spese__", "Contabilità") or _t.get("a") in ("__spese__", "Contabilità"):
                _data_t = _t.get("data", "")
                _imp_t  = round(float(_t.get("importo", 0)), 2)
                _tipo_t = "Entrata" if _t.get("da") in ("__spese__", "Contabilità") else "Uscita"
                _cnome  = _id_a_nome.get(_t.get("a") if _tipo_t == "Entrata" else _t.get("da"), "")
                _agganci_conto.setdefault((_data_t, _imp_t, _tipo_t), []).append(_cnome)
    except Exception:
        _agganci_conto = {}
    _uso_ordinale_conto = {}
    totali = {}
    dettagli = {}
    _nome_a_simbolo = SIMBOLI_METODO
    for d, entries in self.spese.items():
        if not self.considera_ricorrenze_var.get() and d > now:
            continue
        if d.year == view_year and d.month == view_month:
            for entry in entries:
                cat, desc, imp, tipo = entry[:4]
                metodo_campo = campo(entry, "metodo_pagamento", "")
                if metodo_campo:
                    simbolo_trovato = _nome_a_simbolo.get(metodo_campo, "")
                    nome_metodo_pulito = metodo_campo
                else:
                    simbolo_trovato = None
                    for simbolo in _simboli_metodo:
                        if simbolo in str(desc):
                            simbolo_trovato = simbolo
                            break
                    if not simbolo_trovato:
                        continue
                    nome_metodo_pulito = _simboli_metodo[simbolo_trovato]
                nome_base = f"{simbolo_trovato} {nome_metodo_pulito}" if simbolo_trovato else nome_metodo_pulito
                _key_conto = (d.strftime("%d-%m-%Y"), round(float(imp), 2), str(tipo).capitalize())
                _conto_espl = campo(entry, "conto", "")
                if _conto_espl:
                    sotto_nome = _conto_espl
                else:
                    _lista_c = _agganci_conto.get(_key_conto, [])
                    _ord_c = _uso_ordinale_conto.get(_key_conto, 0)
                    sotto_nome = _lista_c[_ord_c] if _ord_c < len(_lista_c) else ""
                    _uso_ordinale_conto[_key_conto] = _ord_c + 1
                nome_metodo = f"{nome_base} {sotto_nome}" if sotto_nome else nome_base
                segno = 1 if tipo == "Entrata" else -1
                totali[nome_metodo] = totali.get(nome_metodo, 0) + imp * segno
                dettagli.setdefault(nome_metodo, []).append((d, imp, tipo))
    if not totali:
        c.create_text(w // 2, h // 2, text="Nessun movimento con metodo di pagamento questo mese",
                      fill=self.TEXT_COLOR, font=("Arial", 10))
        c.configure(scrollregion=(0, 0, w, h))
        return
    righe_ordinate = sorted(totali.items(), key=lambda x: abs(x[1]), reverse=True)
    max_val = max(abs(v) for _, v in righe_ordinate) or 1
    pad_l, pad_r, pad_t, pad_b = 10, 10, 10, 10
    row_h = 36
    bar_max_w = w - pad_l - pad_r - 150
    colors = ["#E06C75", "#C678DD", "#61AFEF", "#98C379", "#56B6C2"]
    total_h = pad_t + len(righe_ordinate) * row_h + pad_b
    c.configure(scrollregion=(0, 0, w, total_h))
    for i, (metodo, val) in enumerate(righe_ordinate):
        y = pad_t + i * row_h + row_h // 2
        bar_w = int(bar_max_w * abs(val) / max_val) if max_val else 0
        bx = pad_l + 150
        fill = "#E5A550" if val >= 0 else colors[i % len(colors)]
        tag_riga = f"riga_metodo_{i}"
        _simb = metodo.split(" ")[0]
        _nome_met = _simboli_metodo.get(_simb, "")
        nome_base = f"{_simb} {_nome_met}" if _nome_met else metodo
        sotto_nome = metodo[len(nome_base):].strip()
        c.create_text(pad_l, y, text=metodo[:24], anchor="w",
                          fill=self.TEXT_COLOR, font=("Arial", 9), tags=tag_riga)
        rect_id = c.create_rectangle(
                bx, y - 10, bx + max(bar_w, 4), y + 10,
                fill=fill, outline="", tags=tag_riga
        )
        x_fine_barra = bx + max(bar_w, 4)
        if x_fine_barra > (w - 60):
                    c.create_text(x_fine_barra - 5, y, text=f"{_fmt_it(val)}€", anchor="e",
                                  fill="white", font=("Arial", 8, "bold"), tags=tag_riga)
        else:
                    c.create_text(x_fine_barra + 5, y, text=f"{_fmt_it(val)}€", anchor="w",
                                  fill=self.TEXT_COLOR, font=("Arial", 8, "bold"), tags=tag_riga)
        voci = sorted(dettagli.get(metodo, []), key=lambda x: x[0], reverse=True)
        tot_usc = sum(iv for _, iv, tv in voci if tv == "Uscita")
        tot_ent = sum(iv for _, iv, tv in voci if tv == "Entrata")
        w_l = 13
        w_v = 12
        righe_dati = [
                    f"{'[-] USCITE:':<{w_l}} {'-' + f'{_fmt_it(tot_usc)}':>{w_v}}€",
                    f"{'[+] ENTRATE:':<{w_l}} {'+' + f'{_fmt_it(tot_ent)}':>{w_v}}€",
                    f"{'[=] NETTO:':<{w_l}} {('+' if tot_ent-tot_usc >= 0 else '') + f'{_fmt_it(tot_ent-tot_usc)}':>{w_v}}€",
        ]
        voci_righe = []
        for d_v, imp_v, tipo_v in voci[:15]:
                    p = "-" if tipo_v == "Uscita" else "+"
                    s = "»" if tipo_v == "Uscita" else "«"
                    dt = d_v.strftime('%d/%m')
                    sinistra = f"{s} {dt}"
                    destra = f"{p + f'{_fmt_it(imp_v)}':>{w_v}}€"
                    gap = w_l + w_v + 2 - len(sinistra) - len(destra)
                    voci_righe.append(sinistra + " " * max(gap, 1) + destra)
        col_w = max(len(r) for r in righe_dati + voci_righe) if (righe_dati + voci_righe) else 28
        sep = "─" * col_w
        righe = [
                f" {metodo.upper()} ".center(col_w, "═"),
                righe_dati[0],
                righe_dati[1],
                sep,
                righe_dati[2],
                sep,
                *voci_righe,
        ]
        if len(voci) > 15:
                righe.append(f"... +altri {len(voci)-15}")
        tip_txt = "\n".join(righe)
        c.tag_bind(tag_riga, "<Enter>",
                   lambda e, t=tip_txt: self._mostra_tip_safe(e, t))
        c.tag_bind(tag_riga, "<Leave>",
                   lambda e: self._nascondi_tip_safe())
        simb_metodo = metodo.split(" ")[0]
        c.tag_bind(tag_riga, "<Double-1>",
                   lambda e, filtri=simb_metodo, metodo_pulito=_nome_met, lbl=metodo, m=view_month, a=view_year:
                       self.mostra_transazioni_popup(
                           {"anno": str(a), "mese": m},
                           f"Dettaglio {lbl} {['Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno','Luglio','Agosto','Settembre','Ottobre','Novembre','Dicembre'][m-1]} {a}",
                           filtro_desc=filtri,
                           filtro_metodo=metodo_pulito
                       ))
        c.tag_bind(tag_riga, "<Button-3>",
                   lambda e, nm=nome_base, cnt=sotto_nome, m=view_month, a=view_year:
                       self.apri_estratti_metodo(metodo=nm, mese=m, anno=a,
                                                 conto=cnt if cnt else None))
    def _on_mousewheel(event):
        if not c.winfo_exists():
            return
        if event.num == 4:
            c.yview_scroll(-1, "units")
        elif event.num == 5:
            c.yview_scroll(1, "units")
        else:
            c.yview_scroll(int(-1 * (event.delta / 120)), "units")
    c.bind("<Enter>",      lambda e: c.focus_set())
    c.bind("<MouseWheel>", _on_mousewheel)
    c.bind("<Button-4>",   _on_mousewheel)
    c.bind("<Button-5>",   _on_mousewheel)

def draw_estratto_conto(self):
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    if not hasattr(self, 'canvas_estratto_conto') or not self.canvas_estratto_conto.winfo_exists():
        return
    c = self.canvas_estratto_conto
    c.delete("all")
    w = c.winfo_width()
    h = c.winfo_height()
    if w < 10 or h < 10:
        return
    now = datetime.date.today()
    view_year  = getattr(self, '_view_year',  now.year)
    view_month = getattr(self, '_view_month', now.month)
    _agganci_conto = {}
    _db_p = {"conti": [], "trasferimenti": []}
    _id_a_nome = {}
    try:
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
            _db_p = json.load(_pf)
        _id_a_nome = {conto["id"]: conto.get("nome", "") for conto in _db_p.get("conti", [])}
        for _t in _db_p.get("trasferimenti", []):
            if _t.get("da") in ("__spese__", "Contabilità") or _t.get("a") in ("__spese__", "Contabilità"):
                _data_t = _t.get("data", "")
                _imp_t  = round(float(_t.get("importo", 0)), 2)
                _tipo_t = "Entrata" if _t.get("da") in ("__spese__", "Contabilità") else "Uscita"
                _cnome  = _id_a_nome.get(_t.get("a") if _tipo_t == "Entrata" else _t.get("da"), "")
                _agganci_conto.setdefault((_data_t, _imp_t, _tipo_t), []).append(_cnome)
    except Exception:
        _agganci_conto = {}
        _db_p = {"conti": [], "trasferimenti": []}
        _id_a_nome = {}
    _uso_ordinale_conto2 = {}
    totali = {}
    dettagli = {}
    chiavi_per_conto = {}
    for d, entries in self.spese.items():
        if not self.considera_ricorrenze_var.get() and d > now:
            continue
        if d.year == view_year and d.month == view_month:
            for entry in entries:
                cat, desc, imp, tipo = entry[:4]
                _key_conto = (d.strftime("%d-%m-%Y"), round(float(imp), 2), str(tipo).capitalize())
                _conto_espl2 = campo(entry, "conto", "")
                if _conto_espl2:
                    nome_conto = _conto_espl2
                else:
                    _lista_c2 = _agganci_conto.get(_key_conto, [])
                    _ord_c2 = _uso_ordinale_conto2.get(_key_conto, 0)
                    nome_conto = _lista_c2[_ord_c2] if _ord_c2 < len(_lista_c2) else ""
                    _uso_ordinale_conto2[_key_conto] = _ord_c2 + 1
                if not nome_conto:
                    continue
                segno = 1 if tipo == "Entrata" else -1
                totali[nome_conto] = totali.get(nome_conto, 0) + imp * segno
                dettagli.setdefault(nome_conto, []).append((d, imp, tipo))
                chiavi_per_conto.setdefault(nome_conto, set()).add(_key_conto)
    for _t in _db_p.get("trasferimenti", []):
        if _t.get("da") in ("__spese__", "Contabilità") or _t.get("a") in ("__spese__", "Contabilità"):
            continue
        try:
            _data_tr = datetime.datetime.strptime(_t["data"], "%d-%m-%Y").date()
        except Exception:
            continue
        if _data_tr.year != view_year or _data_tr.month != view_month:
            continue
        if not self.considera_ricorrenze_var.get() and _data_tr > now:
            continue
        try:
            _imp_tr = round(float(_t.get("importo", 0)), 2)
        except Exception:
            continue
        _nome_da_tr = _id_a_nome.get(_t.get("da"), "")
        _nome_a_tr  = _id_a_nome.get(_t.get("a"), "")
        if _nome_da_tr:
            totali[_nome_da_tr] = totali.get(_nome_da_tr, 0) - _imp_tr
            dettagli.setdefault(_nome_da_tr, []).append((_data_tr, _imp_tr, "Uscita"))
        if _nome_a_tr:
            totali[_nome_a_tr] = totali.get(_nome_a_tr, 0) + _imp_tr
            dettagli.setdefault(_nome_a_tr, []).append((_data_tr, _imp_tr, "Entrata"))
    if not totali:
        c.create_text(w // 2, h // 2, text="Nessun movimento agganciato a un conto questo mese",
                      fill=self.TEXT_COLOR, font=("Arial", 10))
        c.configure(scrollregion=(0, 0, w, h))
        return
    righe_ordinate = sorted(totali.items(), key=lambda x: abs(x[1]), reverse=True)
    max_val = max(abs(v) for _, v in righe_ordinate) or 1
    pad_l, pad_r, pad_t, pad_b = 10, 10, 10, 10
    row_h = 36
    bar_max_w = w - pad_l - pad_r - 150
    colors = ["#E06C75", "#C678DD", "#61AFEF", "#98C379", "#56B6C2"]
    total_h = pad_t + len(righe_ordinate) * row_h + pad_b
    c.configure(scrollregion=(0, 0, w, total_h))
    for i, (conto, val) in enumerate(righe_ordinate):
        y = pad_t + i * row_h + row_h // 2
        bar_w = int(bar_max_w * abs(val) / max_val) if max_val else 0
        bx = pad_l + 150
        fill = "#E5A550" if val >= 0 else colors[i % len(colors)]
        tag_riga = f"riga_conto_{i}"
        c.create_text(pad_l, y, text=conto[:24], anchor="w",
                          fill=self.TEXT_COLOR, font=("Arial", 9), tags=tag_riga)
        rect_id = c.create_rectangle(
                bx, y - 10, bx + max(bar_w, 4), y + 10,
                fill=fill, outline="", tags=tag_riga
        )
        x_fine_barra = bx + max(bar_w, 4)
        if x_fine_barra > (w - 60):
                    c.create_text(x_fine_barra - 5, y, text=f"{_fmt_it(val)}€", anchor="e",
                                  fill="white", font=("Arial", 8, "bold"), tags=tag_riga)
        else:
                    c.create_text(x_fine_barra + 5, y, text=f"{_fmt_it(val)}€", anchor="w",
                                  fill=self.TEXT_COLOR, font=("Arial", 8, "bold"), tags=tag_riga)
        voci = sorted(dettagli.get(conto, []), key=lambda x: x[0], reverse=True)
        tot_usc = sum(iv for _, iv, tv in voci if tv == "Uscita")
        tot_ent = sum(iv for _, iv, tv in voci if tv == "Entrata")
        w_l = 13
        w_v = 12
        righe_dati = [
                    f"{'[-] USCITE:':<{w_l}} {'-' + f'{_fmt_it(tot_usc)}':>{w_v}}€",
                    f"{'[+] ENTRATE:':<{w_l}} {'+' + f'{_fmt_it(tot_ent)}':>{w_v}}€",
                    f"{'[=] NETTO:':<{w_l}} {('+' if tot_ent-tot_usc >= 0 else '') + f'{_fmt_it(tot_ent-tot_usc)}':>{w_v}}€",
        ]
        voci_righe = []
        for d_v, imp_v, tipo_v in voci[:15]:
                    p = "-" if tipo_v == "Uscita" else "+"
                    s = "»" if tipo_v == "Uscita" else "«"
                    dt = d_v.strftime('%d/%m')
                    sinistra = f"{s} {dt}"
                    destra = f"{p + f'{_fmt_it(imp_v)}':>{w_v}}€"
                    gap = w_l + w_v + 2 - len(sinistra) - len(destra)
                    voci_righe.append(sinistra + " " * max(gap, 1) + destra)
        col_w = max(len(r) for r in righe_dati + voci_righe) if (righe_dati + voci_righe) else 28
        sep = "─" * col_w
        righe = [
                f" {conto.upper()} ".center(col_w, "═"),
                righe_dati[0],
                righe_dati[1],
                sep,
                righe_dati[2],
                sep,
                *voci_righe,
        ]
        if len(voci) > 15:
                righe.append(f"... +altri {len(voci)-15}")
        tip_txt = "\n".join(righe)
        c.tag_bind(tag_riga, "<Enter>",
                   lambda e, t=tip_txt: self._mostra_tip_safe(e, t))
        c.tag_bind(tag_riga, "<Leave>",
                   lambda e: self._nascondi_tip_safe())
        _chiavi_dc = chiavi_per_conto.get(conto, set())
        c.tag_bind(tag_riga, "<Double-1>",
                   lambda e, chiavi=_chiavi_dc, lbl=conto, m=view_month, a=view_year:
                       self.mostra_transazioni_popup(
                           {"anno": str(a), "mese": m},
                           f"Dettaglio {lbl} {['Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno','Luglio','Agosto','Settembre','Ottobre','Novembre','Dicembre'][m-1]} {a}",
                           chiavi_filtro=chiavi,
                           trasferimenti_conto=lbl
                       ))
        c.tag_bind(tag_riga, "<Button-3>",
                   lambda e: self.open_saldo_conto())
    def _on_mousewheel(event):
        if not c.winfo_exists():
            return
        if event.num == 4:
            c.yview_scroll(-1, "units")
        elif event.num == 5:
            c.yview_scroll(1, "units")
        else:
            c.yview_scroll(int(-1 * (event.delta / 120)), "units")
    c.bind("<Enter>",      lambda e: c.focus_set())
    c.bind("<MouseWheel>", _on_mousewheel)
    c.bind("<Button-4>",   _on_mousewheel)
    c.bind("<Button-5>",   _on_mousewheel)

def draw_heatmap_mese(self):
    if not hasattr(self, 'canvas_heatmap') or not self.canvas_heatmap.winfo_exists():
        return
    c = self.canvas_heatmap
    c.delete("all")
    w, h = c.winfo_width(), c.winfo_height()
    if w < 10 or h < 10: return
    now = datetime.date.today()
    view_year  = getattr(self, '_view_year',  now.year)
    view_month = getattr(self, '_view_month', now.month)
    giorni = calendar.monthrange(view_year, view_month)[1]
    usc_g, ent_g = {}, {}
    for d, entries in self.spese.items():
        if not self.considera_ricorrenze_var.get() and d > now:
            continue
        if d.year == view_year and d.month == view_month:
            for entry in entries:
                imp, tipo = entry[2], entry[3]
                if tipo == "Uscita":
                    usc_g[d.day] = usc_g.get(d.day, 0.0) + imp
                else:
                    ent_g[d.day] = ent_g.get(d.day, 0.0) + imp
    def get_intensity(val, max_val):
        if val <= 0 or max_val <= 0: return 0
        return (math.log1p(val) / math.log1p(max_val)) * 0.85
    max_usc = max(usc_g.values(), default=1) or 1
    max_ent = max(ent_g.values(), default=1) or 1
    primo = datetime.date(view_year, view_month, 1)
    offset, cols = primo.weekday(), 7
    pad_l, pad_t = 8, 28
    cell_w = (w - pad_l * 2) / cols
    rows_needed = (offset + giorni + 6) // 7
    cell_h = max(20, (h - pad_t - 10) / rows_needed)
    def hex_to_rgb(hx):
        try:
            r, g, b = c.winfo_rgb(str(hx))
            return r >> 8, g >> 8, b >> 8
        except Exception:
            return (42, 39, 63)
    def blend(c1, c2, r):
        r = max(0.0, min(1.0, r))
        return f"#{int(c1[0]+(c2[0]-c1[0])*r):02x}{int(c1[1]+(c2[1]-c1[1])*r):02x}{int(c1[2]+(c2[2]-c1[2])*r):02x}"
    bg_rgb  = hex_to_rgb(getattr(self, 'COLOR_WIDGET_BG', '#2a273f'))
    red_rgb = hex_to_rgb(getattr(self, 'COLOR_RED_SMOOTH', '#e06c75'))
    grn_rgb = hex_to_rgb(getattr(self, 'COLOR_GREEN_SMOOTH', '#98c379'))
    for i, dn in enumerate(["Lun", "Mar", "Mer", "Gio", "Ven", "Sab", "Dom"]):
        c.create_text(pad_l + i*cell_w + cell_w/2, pad_t-12, text=dn, fill=self.TEXT_COLOR, font=("Arial", 8, "bold"))
    tips = {}
    for g_day in range(1, giorni + 1):
        idx = offset + g_day - 1
        x1, y1 = pad_l + (idx % 7) * cell_w + 2, pad_t + (idx // 7) * cell_h + 2
        x2, y2 = x1 + cell_w - 4, y1 + cell_h - 4
        u, e = usc_g.get(g_day, 0.0), ent_g.get(g_day, 0.0)
        netto = e - u
        if u == 0 and e == 0:
            fill = getattr(self, 'COLOR_WIDGET_BG', '#2a273f')
        elif netto < 0:
            fill = blend(bg_rgb, red_rgb, get_intensity(abs(netto), max_usc))
        else:
            fill = blend(bg_rgb, grn_rgb, get_intensity(netto, max_ent))
        c.create_rectangle(x1, y1, x2, y2, fill=fill, outline=self.TEXT_COLOR, width=1)
        rgb_f = hex_to_rgb(fill)
        lum = 0.299*rgb_f[0] + 0.587*rgb_f[1] + 0.114*rgb_f[2]
        t_col = "#FFFFFF" if (u > 0 or e > 0) and lum < 140 else self.TEXT_COLOR
        c.create_text((x1+x2)/2, y1+8, text=str(g_day), fill=t_col, font=("Arial", 8, "bold"))
        if u > 0: c.create_text((x1+x2)/2, (y1+y2)/2 + 2, text=f"-{_fmt_it(u, ',.0f')}", fill=t_col, font=("Arial", 7))
        if e > 0: c.create_text((x1+x2)/2, y2-7, text=f"+{_fmt_it(e, ',.0f')}", fill=t_col, font=("Arial", 7))
        if g_day == now.day:
            c.create_rectangle(x1, y1, x2, y2, outline="#E5C07B", width=2)
        tips[g_day] = (
            f"{g_day:02d}/{view_month:02d}/{view_year}\n"
            f"{'Uscite:':<9}{('-'+f'{_fmt_it(u)}'):>13} €\n"
            f"{'Entrate:':<9}{('+'+f'{_fmt_it(e)}'):>13} €\n"
            f"{'Netto:':<9}{(('+' if netto>=0 else '')+f'{_fmt_it(netto)}'):>13} €"
        )
    def _on_motion(e):
        col, row = int((e.x - pad_l) / cell_w), int((e.y - pad_t) / cell_h)
        g = row * 7 + col - offset + 1
        if 1 <= g <= giorni and g in tips:
            u_g = usc_g.get(g, 0.0)
            e_g = ent_g.get(g, 0.0)
            if u_g > 0 or e_g > 0:
                if getattr(c, '_last_tip_day', None) != g:
                    c._last_tip_day = g
                    self._mostra_tip_safe(e, tips[g])
            else:
                c._last_tip_day = None
                self._nascondi_tip_safe()
    def _on_double_click(e):
        col, row = int((e.x - pad_l) / cell_w), int((e.y - pad_t) / cell_h)
        g = row * 7 + col - offset + 1
        if 1 <= g <= giorni:
            u_g = usc_g.get(g, 0.0)
            e_g = ent_g.get(g, 0.0)
            if u_g > 0 or e_g > 0:
                self.mostra_transazioni_popup(
                    {"anno": str(view_year), "mese": view_month, "giorno": g},
                    f"Dettaglio {g:02d} {['Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno','Luglio','Agosto','Settembre','Ottobre','Novembre','Dicembre'][view_month-1]} {view_year}"
                )
    c.bind("<Double-1>", _on_double_click)
    def _on_right_click(e):
        col, row = int((e.x - pad_l) / cell_w), int((e.y - pad_t) / cell_h)
        g = row * 7 + col - offset + 1
        if 1 <= g <= giorni:
            data = datetime.date(view_year, view_month, g)
            self.cal.selection_set(data)
            self.after(50, lambda: self.apri_inserimento_rapido(
                type('E', (), {'widget': type('W', (), {'cget': lambda s, x: '1'})()})()
            ))
    c.bind("<Button-3>", _on_right_click)
    c.bind("<Motion>", _on_motion)
    c.bind("<Leave>", lambda e: [setattr(c, '_last_tip_day', None), self._nascondi_tip_safe()])

def draw_spark_mese(self):
    if not hasattr(self, 'canvas_spark') or not self.canvas_spark.winfo_exists():
        return
    c = self.canvas_spark
    c.delete("all")
    w = c.winfo_width()
    h = c.winfo_height()
    if w < 10 or h < 10:
        return
    now = datetime.date.today()
    view_year  = getattr(self, '_view_year',  now.year)
    view_month = getattr(self, '_view_month', now.month)
    giorni = calendar.monthrange(view_year, view_month)[1]
    uscite = [0.0] * (giorni + 1)
    entrate = [0.0] * (giorni + 1)
    det_u = {}
    det_e = {}
    for d, entries in self.spese.items():
        if not self.considera_ricorrenze_var.get() and d > now:
            continue
        if d.year == view_year and d.month == view_month:
            for entry in entries:
                _, desc, imp, tipo = entry[:4]
                if tipo == "Uscita":
                    uscite[d.day] += imp
                    det_u.setdefault(d.day, []).append((desc, imp))
                else:
                    entrate[d.day] += imp
                    det_e.setdefault(d.day, []).append((desc, imp))
    pad_t, pad_b, pad_l, pad_r = 22, 18, 10, 10
    usable_w = w - pad_l - pad_r
    usable_h = h - pad_t - pad_b
    max_val = max(max(uscite[1:], default=0), max(entrate[1:], default=0)) or 1
    step = usable_w / giorni
    def disegna_serie(valori, colore, tipo_label):
        pts = []
        for g in range(1, giorni + 1):
            x = pad_l + (g - 1) * step + step / 2
            frac = valori[g] / max_val
            y = pad_t + usable_h - frac * usable_h
            pts.append((g, x, y))
        for i in range(len(pts) - 1):
            c.create_line(pts[i][1], pts[i][2], pts[i+1][1], pts[i+1][2],
                          fill=colore, width=2)
        for g, x, y in pts:
            r = 4 if valori[g] > 0 else 2
            ov = c.create_oval(x - r, y - r, x + r, y + r, fill=colore, outline="")
            data_str = datetime.date(view_year, view_month, g).strftime("%d/%m/%Y")
            if valori[g] > 0:
                c.tag_bind(ov, "<Double-1>",
                           lambda e, g=g, m=view_month, a=view_year:
                               self.mostra_transazioni_popup(
                                   {"anno": str(a), "mese": m, "giorno": g},
                                   f"Dettaglio {g:02d} {['Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno','Luglio','Agosto','Settembre','Ottobre','Novembre','Dicembre'][m-1]} {a}"
                               ))
                tip = f"{data_str}  —  {tipo_label}: €{_fmt_it(valori[g])}"
            else:
                tip = f"{data_str}\n{tipo_label}: nessuna"
            c.tag_bind(ov, "<Enter>", lambda e, t=tip: self.esegui_disegno(t,
                min(e.x_root, self.winfo_rootx() + self.winfo_width() - 200),
                min(e.y_root, self.winfo_rooty() + self.winfo_height() - 100)))
            c.tag_bind(ov, "<Leave>", lambda e: self.tooltip_win.withdraw()
                       if self.tooltip_win and self.tooltip_win.winfo_exists() else None)
    disegna_serie(uscite,  "#E06C75", "Uscite")
    disegna_serie(entrate, "#98C379", "Entrate")
    c.bind("<Motion>", lambda e: self.tooltip_win.withdraw()
           if not c.find_withtag("current") and self.tooltip_win and self.tooltip_win.winfo_exists() else None)
    c.bind("<Leave>", lambda e: self.tooltip_win.withdraw()
           if self.tooltip_win and self.tooltip_win.winfo_exists() else None)
    c.create_rectangle(pad_l, 4, pad_l + 10, 14, fill="#E06C75", outline="")
    c.create_text(pad_l + 14, 9, text="Uscite", anchor="w",
                  fill=self.TEXT_COLOR, font=("Arial", 8))
    c.create_rectangle(pad_l + 60, 4, pad_l + 70, 14, fill="#98C379", outline="")
    c.create_text(pad_l + 74, 9, text="Entrate", anchor="w",
                  fill=self.TEXT_COLOR, font=("Arial", 8))
    c.create_text(pad_l + 130, 9, text=f"(max €{_fmt_it(max_val, ',.0f')})", anchor="w",
                  fill=self.TEXT_COLOR, font=("Arial", 7))
    for g in range(1, giorni + 1, 5):
        x = pad_l + (g - 1) * step + step / 2
        c.create_text(x, h - 4, text=str(g), fill=self.TEXT_COLOR, font=("Arial", 7))
