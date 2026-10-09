#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import calendar
import datetime
from moduli.modello_spesa import campo
from moduli.mappa_conti_trasferimenti import costruisci_mappa_conti_da_trasferimenti, conto_da_mappa

# Mostra tutti i movimenti del mese selezionato, raggruppati per giorno, nella treeview di destra.
def goto_dettaglio_mese(self, salva=False):
    from __main__ import PORTAFOGLIO_BANCARIO
    self.mostra_treeview_statistiche()
    try:
        data_sel = self.cal.selection_get()
    except:
        data_sel = datetime.date.today()
    anno = getattr(self, '_view_year', data_sel.year)
    mese = getattr(self, '_view_month', data_sel.month)
    self.stats_refdate = data_sel
    self._view_year = anno
    self._view_month = mese
    if hasattr(self, 'stats_mode'):
        self.stats_mode.set("giorno")
        if salva:
            from __main__ import _salva_chiave_config
            self._stats_mode_utente = "giorno"
            self._stats_dettaglio_utente = True
            _salva_chiave_config("stats_mode_avanzato", "giorno")
            _salva_chiave_config("stats_dettaglio_mese", True)
    if hasattr(self, 'stats_hint_label'):
        self.stats_hint_label.config(text="Doppio clic → Documenti  |  Tasto destro → Promemoria")
    self.stats_table["displaycolumns"] = ("A", "B", "C", "D", "E", "F")
    cols = {
        "A": (80,  "center", "Data"),
        "B": (150, "w",      "Categoria"),
        "C": (240, "w",      "Descrizione"),
        "D": (100, "center", "Importo"),
        "E": (70,  "center", "Tipo"),
        "F": (100,  "center", "Conto/Varia"),
    }
    for col_id, (width, anchor, txt) in cols.items():
        self.stats_table.column(col_id, width=width, anchor=anchor)
        self.stats_table.heading(col_id, text=txt)
    mesi_it = ["Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno",
               "Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"]
    nome_mese = mesi_it[mese - 1] if 1 <= mese <= 12 else str(mese)
    self.stats_label.config(
        text=f"Dettaglio Giornaliero - {nome_mese} {anno}",
        foreground="purple", font=("Arial", 10, "bold"))
    if anno != datetime.date.today().year or mese != datetime.date.today().month:
        self.blink_label_colors(self.stats_label, "purple", "orange")
    else:
        self.stop_blink_label_colors(self.stats_label, final_color="purple")
    for i in self.stats_table.get_children():
        self.stats_table.delete(i)
    self.stats_table._metodo_lookup = {}
    oggi = datetime.date.today()
    _agganci_uso = {}
    _agganci = costruisci_mappa_conti_da_trasferimenti(PORTAFOGLIO_BANCARIO)
    num_giorni = calendar.monthrange(anno, mese)[1]
    righe_inserite = 0
    _mappa_indici_reali = {}
    _orig_index_method = getattr(self.stats_table, '_orig_index', self.stats_table.index)
    if not hasattr(self.stats_table, '_orig_index'):
        self.stats_table._orig_index = _orig_index_method
    for g in range(1, num_giorni + 1):
        try:
            giorno = datetime.date(anno, mese, g)
        except:
            continue
        spese_giorno = self.spese.get(giorno, [])
        if not spese_giorno:
            continue
        for idx, sp in enumerate(spese_giorno):
            try:
                cat  = campo(sp, "categoria", "")
                desc = campo(sp, "descrizione", "")
                imp  = float(campo(sp, "importo", 0.0))
                tipo = campo(sp, "tipo", "")
                _key  = (giorno.strftime("%d-%m-%Y"), round(imp, 2), tipo)
                conto = campo(sp, "conto", "")
                if not conto:
                    conto = conto_da_mappa(_agganci, _agganci_uso, giorno.strftime("%d-%m-%Y"), imp, tipo)
                imp_str = f"{imp:.2f}".replace(".", ",")
                _tag = "futuro" if giorno > oggi else tipo
                if (tipo == "Uscita" and giorno <= oggi
                        and (anno, mese) == (oggi.year, oggi.month)
                        and cat in getattr(self, "_budget_sforati", set())):
                    _tag = "sforato"
                item_id = self.stats_table.insert("", "end", values=(
                    giorno.strftime("%d-%m-%Y"),
                    cat, desc, imp_str, tipo, conto
                ), tags=(_tag,))
                _mappa_indici_reali[item_id] = idx
                metodo_val = campo(sp, "metodo_pagamento", "")
                self.stats_table._metodo_lookup[item_id] = {
                    "metodo": metodo_val,
                    "conto": conto,
                    "ora": campo(sp, "ora", ""),
                    "hashtag": campo(sp, "hashtag", []),
                    "id_ricorrenza": campo(sp, "id_ricorrenza", ""),
                    "data": giorno.strftime("%d-%m-%Y"),
                    "categoria": cat,
                    "importo": imp,
                }
                righe_inserite += 1
            except:
                continue

    if hasattr(self, "ottieni_promemoria_mese"):
        try:
            for piano in self.ottieni_promemoria_mese(anno, mese):
                quota = float(piano.get("quota_mese", piano.get("quota", 0.0)) or 0.0)
                nome_p = piano.get("nome", "") or ""
                _pid = self.stats_table.insert("", "end", values=(
                    "", piano.get("categoria", ""),
                    f"Pianificata · {nome_p}" if nome_p else "Pianificata",
                    f"{quota:.2f}".replace(".", ","), "Pianificata", ""
                ), tags=("promemoria",))
                self.stats_table._metodo_lookup[_pid] = {
                    "pianificata": True,
                    "metodo": piano.get("metodo_pagamento", ""),
                    "conto": piano.get("conto", ""),
                    "hashtag": piano.get("hashtag", []) or [],
                    "data_scadenza": piano.get("data_scadenza", ""),
                    "descrizione": piano.get("descrizione", "") or nome_p,
                    "categoria": piano.get("categoria", ""),
                    "importo": quota,
                }
                righe_inserite += 1
        except Exception:
            pass
    try:
        from __main__ import _fmt_it
        _flag_p = bool(self.considera_pianificate_var.get())
        _in_piano = set()
        if _flag_p and hasattr(self, "ids_spese_pianificate"):
            _in_piano = self.ids_spese_pianificate()
        _ricorr = self.considera_ricorrenze_var.get() if hasattr(self, "considera_ricorrenze_var") else True
        tot_e, tot_u = 0.0, 0.0
        for g in range(1, num_giorni + 1):
            _g = datetime.date(anno, mese, g)
            for sp in self.spese.get(_g, []):
                if not _ricorr and (anno, mese) == (oggi.year, oggi.month) and _g > oggi:
                    continue
                _tipo = campo(sp, "tipo", "")
                _imp = float(campo(sp, "importo", 0.0))
                if _tipo == "Entrata":
                    tot_e += _imp
                else:
                    if _in_piano and campo(sp, "id_spesa", None) in _in_piano:
                        continue
                    tot_u += _imp
        if _flag_p and hasattr(self, "ottieni_promemoria_mese"):
            for piano in self.ottieni_promemoria_mese(anno, mese):
                tot_u += float(piano.get("quota_mese", piano.get("quota", 0.0)) or 0.0)
        _diff = tot_e - tot_u
        self.totali_label.config(
            text=f"Totale Entrate: {_fmt_it(tot_e)}    Totale Uscite: {_fmt_it(tot_u)}    Differenza: {_fmt_it(_diff)}",
            foreground="dodgerblue" if _diff >= 0 else "red", font=("Arial", 10, "bold"))
    except Exception:
        pass
    def proxy_index(item_id):
        return _mappa_indici_reali.get(item_id, self.stats_table._orig_index(item_id))
    self.stats_table.index = proxy_index
    self.stats_table.tag_configure("Entrata", foreground="green")
    self.stats_table.tag_configure("Uscita",  foreground="red")
    self.stats_table.tag_configure("futuro",  foreground="#E5C07B", font=("Arial", 9, "italic"))
    self.stats_table.tag_configure("sforato", foreground='#C08081', font=("Arial", 9, "bold"))
    self.stats_table.tag_configure("promemoria", foreground='#61AFEF', font=("Arial", 9, "italic"))
    if righe_inserite == 0:
        self.stats_table.insert("", "end", values=("—", "Nessun movimento", "", "", "", ""), tags=())
    self.stats_table.yview_moveto(0)
    self.update_totalizzatore_anno_corrente(year=anno)
    self.update_totalizzatore_mese_corrente(year=anno, month=mese)
    self.update_spese_mese_corrente(year=anno, month=mese)

