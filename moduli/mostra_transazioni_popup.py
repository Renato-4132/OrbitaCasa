#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import tkinter as tk
from tkinter import ttk
from moduli.modello_spesa import campo

# Popup dettaglio transazioni: mostra lista filtrata per anno/mese/giorno/tipo/categoria con totali, ordinamento colonne e azioni rapide
def mostra_transazioni_popup(self, data_filter, title, filtro_desc=None, chiavi_filtro=None, filtro_metodo=None):
    MESI_NOME_COMPLETO = {
        1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile", 
        5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto", 
        9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
    }
    anno = data_filter.get("anno")
    mese_filtro_raw = data_filter.get("mese") 
    giorno = data_filter.get("giorno")
    tipo_filtro = data_filter.get("tipo")
    categorie_filtro_list = data_filter.get("categorie", []) 
    categoria_singola_raw = data_filter.get("categoria")
    if categoria_singola_raw and categoria_singola_raw != "Tutti":
        if categoria_singola_raw not in categorie_filtro_list:
            categorie_filtro_list.append(categoria_singola_raw)
    categorie_filtro_normalizzate_aggressive = [str(cat).replace(' ', '').lower() for cat in categorie_filtro_list]
    devo_filtrare_categorie = bool(categorie_filtro_normalizzate_aggressive)
    mese_filtro_num = None
    if mese_filtro_raw and mese_filtro_raw != "Tutti":
        try:
            mese_filtro_num = int(mese_filtro_raw)
        except (ValueError, TypeError):
            pass 
    new_title = title
    if mese_filtro_num is not None and anno and anno != "Tutti":
        nome_mese = MESI_NOME_COMPLETO.get(mese_filtro_num, f"{mese_filtro_num:02d}")
        mese_str = str(mese_filtro_num).zfill(2)
        identificatore1 = f"{anno}-{mese_str}"
        identificatore2 = mese_str
        if identificatore1 in title:
            new_title = title.replace(identificatore1, f"{nome_mese} {anno}")
        elif identificatore2 in title and nome_mese not in title:
            new_title = title.replace(identificatore2, nome_mese)
    title = new_title
    spese_filtrate = []
    for data, voci in self.spese.items():
        if anno and anno != "Tutti" and str(data.year) != anno: continue
        if mese_filtro_num is not None and data.month != mese_filtro_num: continue
        if giorno and giorno != "Tutti":
            try:
                if data.day != int(giorno): continue
            except: continue
        for entry in voci:
            try:
                cat_originale, desc, imp_str, entry_tipo = entry[:4]
                cat_normalized_aggressive = str(cat_originale).replace(' ', '').lower()
                cat_normalized_display = ' '.join(str(cat_originale).strip().split()).title() 
                entry_imp = float(imp_str)
                entry_tipo = entry_tipo.strip().capitalize()
            except (ValueError, TypeError, IndexError): 
                continue 
            if devo_filtrare_categorie and cat_normalized_aggressive not in categorie_filtro_normalizzate_aggressive:
                continue
            if tipo_filtro and entry_tipo != tipo_filtro.capitalize():
                continue
            if filtro_metodo:
                entry_metodo = campo(entry, "metodo_pagamento", "")
                if entry_metodo:
                    if entry_metodo != filtro_metodo:
                        continue
                elif filtro_desc:
                    _filtri_desc = [filtro_desc] if isinstance(filtro_desc, str) else list(filtro_desc)
                    if not all(f in str(desc) for f in _filtri_desc):
                        continue
                else:
                    continue
            elif filtro_desc:
                _filtri_desc = [filtro_desc] if isinstance(filtro_desc, str) else list(filtro_desc)
                if not all(f in str(desc) for f in _filtri_desc):
                    continue
            if chiavi_filtro is not None:
                _chiave_voce = (data.strftime("%d-%m-%Y"), round(float(entry_imp), 2), entry_tipo)
                if _chiave_voce not in chiavi_filtro:
                    continue
            entry_conto_diretto = campo(entry, "conto", "")
            entry_metodo_diretto = campo(entry, "metodo_pagamento", "")
            entry_tag_diretto = " ".join(campo(entry, "hashtag", []) or [])
            spese_filtrate.append((data, cat_normalized_display, desc, entry_imp, entry_tipo, entry_conto_diretto, entry_metodo_diretto, entry_tag_diretto))
    if not spese_filtrate:
        self.show_custom_info("Nessuna transazione", f"Nessuna transazione trovata per {title}.")
        return
    popup_width, popup_height = 1150, 450
    popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    popup.title(f"Dettaglio Transazioni - {title}")
    popup.attributes("-topmost", True)
    popup.resizable(True, True)
    popup.withdraw()
    self.update_idletasks()
    main_x = self.winfo_rootx()
    main_y = self.winfo_rooty()
    main_width = self.winfo_width()
    main_height = self.winfo_height()
    center_x = main_x + (main_width // 2) - (popup_width // 2)
    center_y = main_y + (main_height // 2) - (popup_height // 2)
    popup.geometry(f"{popup_width}x{popup_height}+{center_x}+{center_y}")
    popup.minsize(popup_width, popup_height)
    popup.transient(self)
    popup.deiconify() 
    popup.lift()
    popup.focus_force()
    tk.Label(popup, bg=self.COLOR_TOPLEVEL , fg=self.TEXT_COLOR, text=title, font=("Arial", 12, "bold")).pack(pady=10)
    ttk.Label(popup, text="Doppio clic → mostra nella lista principale  |  Clic destro → popola campi inserimento",
              font=("Arial", 9, "italic"), foreground="gray").pack(anchor="center", padx=4)
    tree_frame = ttk.Frame(popup)
    tree_frame.pack(fill="both", expand=True, padx=10, pady=6)
    vsb = ttk.Scrollbar(tree_frame, orient="vertical", style="Vertical.TScrollbar")
    vsb.pack(side="right", fill="y")
    columns = ("Data", "Categoria", "Descrizione", "Importo", "Tipo", "Conto", "Metodo", "Tag")
    tree = ttk.Treeview(
        tree_frame, 
        columns=columns, 
        show="headings", 
        height=10,
        yscrollcommand=vsb.set,
        selectmode='browse'
    )
    tree.pack(fill="both", expand=True, side="left") 
    vsb.config(command=tree.yview)
    widths = (90, 150, 250, 100, 80, 120, 100, 140)
    anchors = ("center", "w", "center", "e", "center", "center", "center", "w")
    def popola_form_da_transazione(event):
        item = tree.identify_row(event.y)
        if not item:
            return
        valori = tree.item(item, "values")
        categoria  = str(valori[1]).strip()
        descrizione = str(valori[2]).strip()
        importo_str = str(valori[3]).replace("€", "").replace(".", "").replace(",", ".").strip()
        tipo        = str(valori[4]).strip()
        cat_match = next(
            (c for c in self.categorie if c.strip().lower() == categoria.lower()),
            None
        )
        if cat_match:
            self.cat_sel.set(cat_match)
            self.cat_menu.set(cat_match)
            self.on_categoria_changed(manuale=False)
        try:
            self.imp_entry.delete(0, tk.END)
            self.imp_entry.insert(0, f"{float(importo_str):.2f}")
        except ValueError:
            pass
        self.desc_entry.delete(0, tk.END)
        if "RIC·" not in descrizione:
            self.desc_entry.insert(0, descrizione[:30])
        tipo_corrente = self.tipo_spesa_var.get()
        if tipo_corrente != tipo:
            self.toggle_tipo_spesa()
        try:
            data_mov = datetime.datetime.strptime(str(valori[0]).strip(), "%d-%m-%Y").date()
            conto_da_tabella = str(valori[5]).strip() if len(valori) > 5 else ""
            if conto_da_tabella and conto_da_tabella != "(nessuno)":
                nome_conto = conto_da_tabella
            else:
                nome_conto = self._trova_conto_da_portafoglio(data_mov, float(importo_str), tipo)
            if nome_conto and hasattr(self, "cb_conto_movimento"):
                self.cb_conto_movimento.set(nome_conto)
        except Exception:
            pass
        metodo_da_tabella = str(valori[6]).strip() if len(valori) > 6 else ""
        if hasattr(self, 'metodo_pagamento_var'):
            self.metodo_pagamento_var.set(self._metodo_pagamento_a_combo(metodo_da_tabella))
        tag_da_tabella = str(valori[7]).strip() if len(valori) > 7 else ""
        if hasattr(self, 'tag_entry'):
            self.tag_entry.delete(0, tk.END)
            self.tag_entry.insert(0, tag_da_tabella)
        caller = getattr(self, '_caller_popup', None)
        self._caller_popup = None
        _chiudi_popup()
        if caller and caller.winfo_exists():
            try:
                caller.destroy()
            except:
                pass
        for w in self.winfo_children():
            if isinstance(w, tk.Toplevel) and w.winfo_exists():
                try:
                    w.destroy()
                except:
                    pass
    def treeview_sort_column(tv, col, reverse):
        try:
            data = [(tv.set(k, col), k) for k in tv.get_children('')]
            if col == "Data" or col == "Giorno":
                data.sort(key=lambda t: datetime.datetime.strptime(t[0], "%d-%m-%Y"), reverse=reverse)
            elif col == "Importo":
                data.sort(key=lambda t: float(t[0].replace(' €', '').replace('.', '').replace(',', '.')), reverse=reverse)
            else:
                data.sort(key=lambda t: t[0].lower(), reverse=reverse)
            for index, (_, k) in enumerate(data):
                tv.move(k, '', index)
            for c in tv["columns"]:
                if c == col:
                    simbolo = " ▲" if not reverse else " ▼"
                    tv.heading(c, text=c + simbolo, 
                               command=lambda _c=c: treeview_sort_column(tv, _c, not reverse))
                else:
                    tv.heading(c, text=c, 
                               command=lambda _c=c: treeview_sort_column(tv, _c, False))
        except Exception as e:
            print(f"Errore ordinamento: {e}")
    for col, w, a in zip(columns, widths, anchors):
        tree.heading(
            col,
            text=col,
            command=lambda c=col: treeview_sort_column(tree, c, False)
        )
        tree.column(col, width=w, anchor=a)
        self._bind_tooltip_metodo(tree, col_desc=2)
    import datetime as _dt
    oggi_d = _dt.date.today()
    tot_entrate = tot_uscite = 0.0
    fut_entrate = fut_uscite = 0.0
    _uso_ordinale_tr = {}
    for d, cat, desc, imp, tipo, conto_diretto, metodo_diretto, tag_diretto in sorted(spese_filtrate, key=lambda x: x[0], reverse=True):
        imp_formattato = f"{imp:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        if d > oggi_d:
            tag_name = "yellow_row"
            if tipo == "Entrata": fut_entrate += imp
            else: fut_uscite += imp
        else:
            tag_name = "green_row" if tipo == "Entrata" else "red_row"
            if tipo == "Entrata": tot_entrate += imp
            else: tot_uscite += imp
        if conto_diretto:
            nome_conto_tr = conto_diretto
        elif d:
            _key_tr = (d.strftime("%d-%m-%Y"), round(imp, 2), tipo)
            _ord_tr = _uso_ordinale_tr.get(_key_tr, 0)
            nome_conto_tr = self._trova_conto_da_portafoglio(d, imp, tipo, ordinale=_ord_tr)
            _uso_ordinale_tr[_key_tr] = _ord_tr + 1
        else:
            nome_conto_tr = ""
        tree.insert("", "end", values=(d.strftime("%d-%m-%Y"), cat, desc, f"{imp_formattato} €", tipo, nome_conto_tr, metodo_diretto, tag_diretto), tags=(tag_name,))
    tree.tag_configure("green_row",  foreground="green")
    tree.tag_configure("red_row",    foreground="red")
    tree.tag_configure("yellow_row", foreground="#E5C07B")
    saldo = tot_entrate - tot_uscite
    includi_futuri_var = tk.BooleanVar(value=True)
    lbl_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    lbl_frame.pack(fill=tk.X, pady=(7, 0))
    lbl = tk.Text(
        lbl_frame,
        bg=self.COLOR_TOPLEVEL,
        fg=self.TEXT_COLOR,
        height=1,
        borderwidth=0,
        font=("Arial", 10, "bold"),
        wrap="none",
        background=popup.cget("background"),
        highlightthickness=0,
        relief="flat"
    )
    lbl.pack(expand=True)
    lbl.tag_config("entrate_color",   foreground="green")
    lbl.tag_config("uscite_color",    foreground="red")
    lbl.tag_config("saldo_pos_color", foreground="green")
    lbl.tag_config("saldo_neg_color", foreground="red")
    lbl.tag_config("center",          justify="center")
    chk_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    chk_frame.pack(pady=(2, 4))
    ttk.Checkbutton(
        chk_frame,
        text="Includi movimenti futuri nei totali",
        variable=includi_futuri_var,
        command=lambda: aggiorna_totali()
    ).pack()
    def formatta_italiano(valore):
        return f"{valore:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    def aggiorna_totali():
        if includi_futuri_var.get():
            e = tot_entrate + fut_entrate
            u = tot_uscite  + fut_uscite
        else:
            e = tot_entrate
            u = tot_uscite
        s = e - u
        e_str = formatta_italiano(e)
        u_str = formatta_italiano(u)
        s_str = formatta_italiano(s)
        text = f"Totale Entrate: {e_str} €  Totale Uscite: {u_str} €  Saldo: {s_str} €"
        lbl.config(state="normal")
        lbl.delete("1.0", "end")
        lbl.insert("end", text)
        lbl.tag_add("center", "1.0", "end")
        es = text.find(e_str)
        lbl.tag_add("entrate_color", f"1.{es}", f"1.{es+len(e_str)}")
        us = text.find(u_str, es)
        lbl.tag_add("uscite_color",  f"1.{us}", f"1.{us+len(u_str)}")
        ss = text.find(s_str, us)
        tag = "saldo_pos_color" if s >= 0 else "saldo_neg_color"
        lbl.tag_add(tag, f"1.{ss}", f"1.{ss+len(s_str)}")
        lbl.config(state="disabled")
    def _chiudi_popup():
        if getattr(self, '_popup_da_doppio_click', False):
            self._popup_da_doppio_click = False
            popup.withdraw()
            self.after(50, popup.destroy)
            return
        popup.withdraw()
        if hasattr(self, 'stats_canvas') and self.stats_canvas.winfo_exists():
            self.stats_canvas.focus_set()
        self.after(50, popup.destroy)

    tree.bind("<Double-1>", lambda evt: (
        setattr(self, '_popup_da_doppio_click', True),
        self.goto_day_from_popup(tree, popup)
    ))
    popup.bind("<Escape>", lambda event: _chiudi_popup())
    popup.protocol("WM_DELETE_WINDOW", lambda: _chiudi_popup())
    aggiorna_totali()
    tree.bind("<Button-3>", popola_form_da_transazione)
    img_chiudi_pop = self.icone_gui.get("chiudi")
    btn_chiudi_pop = ttk.Label(popup, compound="left", image=img_chiudi_pop, text=" Chiudi" if img_chiudi_pop else "Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
    btn_chiudi_pop.pack(pady=10)
    btn_chiudi_pop.bind("<Button-1>", lambda e: _chiudi_popup())

