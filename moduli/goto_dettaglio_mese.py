#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import calendar
import datetime
from moduli.modello_spesa import campo

# Mostra tutti i movimenti del mese selezionato, raggruppati per giorno, nella treeview di destra.
def goto_dettaglio_mese(self):
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
    _agganci = {}
    _agganci_uso = {}
    try:
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
            _db_p = json.load(_pf)
        _id_a_nome = {c["id"]: c.get("nome", "") for c in _db_p.get("conti", [])}
        for _t in _db_p.get("trasferimenti", []):
            if _t.get("da") in ("__spese__", "Contabilità") or _t.get("a") in ("__spese__", "Contabilità"):
                _data_t = _t.get("data", "")
                _imp_t  = round(float(_t.get("importo", 0)), 2)
                _tipo_t = "Entrata" if _t.get("da") in ("__spese__", "Contabilità") else "Uscita"
                _cnome  = _id_a_nome.get(_t.get("a") if _tipo_t == "Entrata" else _t.get("da"), "")
                _agganci.setdefault((_data_t, _imp_t, _tipo_t), []).append(_cnome)
    except Exception:
        pass
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
                    _uso  = _agganci_uso.get(_key, 0)
                    _lista = _agganci.get(_key, [])
                    conto = _lista[_uso] if _uso < len(_lista) else ""
                    _agganci_uso[_key] = _uso + 1
                imp_str = f"{imp:.2f}"
                _tag = "futuro" if giorno > oggi else tipo
                item_id = self.stats_table.insert("", "end", values=(
                    giorno.strftime("%d-%m-%Y"),
                    cat, desc, imp_str, tipo, conto
                ), tags=(_tag,))
                _mappa_indici_reali[item_id] = idx
                metodo_val = campo(sp, "metodo_pagamento", "")
                self.stats_table._metodo_lookup[item_id] = metodo_val
                righe_inserite += 1
            except:
                continue
    def proxy_index(item_id):
        return _mappa_indici_reali.get(item_id, self.stats_table._orig_index(item_id))
    self.stats_table.index = proxy_index
    self.stats_table.tag_configure("Entrata", foreground="green")
    self.stats_table.tag_configure("Uscita",  foreground="red")
    self.stats_table.tag_configure("futuro",  foreground="#E5C07B", font=("Arial", 9, "italic"))
    if righe_inserite == 0:
        self.stats_table.insert("", "end", values=("—", "Nessun movimento", "", "", "", ""), tags=())
    self.stats_table.yview_moveto(0)
    self.update_totalizzatore_anno_corrente(year=anno)
    self.update_totalizzatore_mese_corrente(year=anno, month=mese)
    self.update_spese_mese_corrente(year=anno, month=mese)
