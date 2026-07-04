#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk

# Visualizzazione Dettagliata per Categoria (Doppio Click sul Riepilogo)
def on_stats_table_double_click(self, event):
    MESI_NOME_COMPLETO = {
        1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile", 
        5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto", 
        9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
    }
    mode = self.stats_mode.get()
    item_id = self.stats_table.identify_row(event.y)
    if not item_id:
        return
    values = self.stats_table.item(item_id, "values")
    if not values or len(values) < 1:
        return
    categoria = str(values[0]).strip()
    categoria_selezionata = str(values[1]).strip()
    spese_categoria = []
    if mode == "giorno":
        try:
            from datetime import datetime
            stringa_giorno = str(values[0]).strip()
            solo_numero_giorno = "".join(filter(str.isdigit, stringa_giorno))[:2].zfill(2)
            ref = self.stats_refdate
            mese_corretto = f"{ref.month:02d}"
            anno_corretto = f"{ref.year}"
            data_estratta = f"{solo_numero_giorno}-{mese_corretto}-{anno_corretto}"
            def pulisci_importo(testo):
                if not testo: return 0.0
                t = str(testo).replace('€', '').replace(' ', '').strip()
                if '.' in t and ',' in t:
                    t = t.replace('.', '').replace(',', '.')
                elif ',' in t:
                    t = t.replace(',', '.')
                try:
                    return float(t)
                except:
                    return 0.0
            categoria_da_tabella = str(values[1]).strip() if len(values) > 1 else "Generica"
            descrizione_reale = str(values[2]).strip() if len(values) > 2 else ""
            val_imp = pulisci_importo(values[3]) if len(values) > 3 else 0.0
            importo_finale = f"{abs(val_imp):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            tipo_movimento = str(values[4]).strip() if len(values) > 4 else "Uscita"
            self.after(500, lambda: self.gestisci_archivi_pdf(
                categoria_iniziale=categoria_da_tabella, 
                data_iniziale=data_estratta,
                importo_iniziale=importo_finale,
                tipo_iniziale=tipo_movimento,
                descrizione_iniziale=descrizione_reale
            ))
            return
        except Exception as e:
            print(f"Errore estrazione dati: {e}")
    if mode == "mese":
        ref = self.stats_refdate
        mese, anno = ref.month, ref.year
        nome_mese = MESI_NOME_COMPLETO.get(mese, f"{mese:02d}")
        for d, sp in self.spese.items():
            if d.month == mese and d.year == anno:
                for entry in sp:
                    cat, desc, imp, tipo = entry[:4]
                    if cat.strip() == categoria: 
                        spese_categoria.append((d, desc, imp, tipo))
        titolo_periodo = f"{nome_mese} {anno}"
        testo_periodo = f"il mese di {nome_mese} {anno}"
    elif mode == "anno":
        ref = self.stats_refdate
        anno = ref.year
        for d, sp in self.spese.items():
            if d.year == anno:
                for entry in sp:
                    cat, desc, imp, tipo = entry[:4]
                    if cat.strip() == categoria:
                        spese_categoria.append((d, desc, imp, tipo))
        titolo_periodo = f"{anno}"
        testo_periodo = f"l'anno {anno}"
    elif mode == "totali":
        for d, sp in self.spese.items():
            for entry in sp:
                cat, desc, imp, tipo = entry[:4]
                if cat.strip() == categoria:
                    spese_categoria.append((d, desc, imp, tipo))
        titolo_periodo = "Tutte le annualità"
        testo_periodo = "tutti gli anni"
    if not spese_categoria:
        self.show_custom_info("Nessuna spesa", f"Nessuna spesa per la categoria '{categoria}' nel periodo selezionato.")
        return
    popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    popup.title(f"Dettaglio Movimenti - {categoria} ({titolo_periodo})")
    popup.geometry("900x450")
    popup.withdraw()
    self.update_idletasks()
    main_x = self.winfo_x()
    main_y = self.winfo_y()
    main_width = self.winfo_width()
    main_height = self.winfo_height()
    popup_width = 900
    popup_height = 450
    center_x = main_x + (main_width // 2) - (popup_width // 2)
    center_y = main_y + (main_height // 2) - (popup_height // 2)
    popup.geometry(f"{popup_width}x{popup_height}+{center_x}+{center_y}")
    popup.resizable(True, True)
    popup.minsize(popup_width, popup_height)
    popup.transient(self)
    popup.update_idletasks()
    popup.deiconify()
    popup.update()
    label = tk.Label(
        popup,
        text=f"Movimenti Categoria '{categoria}' per {testo_periodo}",
        font=("Arial", 11),
        bg=self.COLOR_TOPLEVEL,
        fg=self.TEXT_COLOR
    )
    label.pack(pady=8)
    tree_frame = ttk.Frame(popup)
    tree_frame.pack(fill="both", expand=True, padx=10, pady=6)
    ttk.Label(tree_frame, text="Doppio clic → mostra nella lista principale  |  Clic destro → popola campi inserimento",
              font=("Arial", 9, "italic"), foreground="gray").pack(anchor="center", padx=4)
    vsb = ttk.Scrollbar(tree_frame, orient="vertical", style="Vertical.TScrollbar")
    vsb.pack(side="right", fill="y")
    columns = ("Data", "Descrizione", "Importo", "Tipo", "Conto")
    tree = ttk.Treeview(
        tree_frame, 
        columns=columns, 
        show="headings", 
        height=10,
        yscrollcommand=vsb.set
    )
    tree.pack(fill="both", expand=True, side="left")
    vsb.config(command=tree.yview)
    def ordina_colonna(treeview, colonna, inverti):
        dati = [(treeview.set(k, colonna), k) for k in treeview.get_children("")]
        try:
            if colonna == "Data":
                dati.sort(
                    key=lambda t: datetime.datetime.strptime(t[0], "%d-%m-%Y"),
                    reverse=inverti
                )
            elif colonna == "Importo":
                dati.sort(
                    key=lambda t: float(t[0].replace(" €", "").replace(".", "").replace(",", ".")),
                    reverse=inverti
                )
            else:
                dati.sort(key=lambda t: t[0].lower(), reverse=inverti)
        except Exception as e:
            print(f"Errore ordinamento:", e)
        for index, (_, k) in enumerate(dati):
            treeview.move(k, "", index)
        treeview.heading(colonna, command=lambda: ordina_colonna(treeview, colonna, not inverti))
    for col, w in zip(columns, (90, 210, 90, 80, 120)):
        anchor = "w" if col == "Descrizione" else "center"
        tree.heading(col, text=col, command=lambda c=col: self.treeview_sort_column(tree, c, False))
        tree.column(col, width=w, anchor=anchor)
        self._bind_tooltip_metodo(tree, col_desc=1)
    tot_entrate = tot_uscite = 0.0
    import datetime as _dt
    oggi_d = _dt.date.today()
    fut_entrate = fut_uscite = 0.0
    for d, desc, imp, tipo in sorted(spese_categoria, key=lambda x: x[0], reverse=True):
        imp_formattato_it = f"{imp:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        tag_name = f"row_{d.strftime('%Y%m%d%H%M%S')}_{len(tree.get_children(''))}"
        nome_conto_tr = self._trova_conto_da_portafoglio(d, imp, tipo) if d else ""
        tree.insert("", "end", values=(d.strftime("%d-%m-%Y"), desc, f"{imp_formattato_it} €", tipo, nome_conto_tr), tags=(tag_name,))
        if d > oggi_d:
            tree.tag_configure(tag_name, foreground="#E5C07B")
            if tipo == "Entrata": fut_entrate += imp
            else: fut_uscite += imp
        elif tipo == "Entrata":
            tree.tag_configure(tag_name, foreground="green")
            tot_entrate += imp
        else:
            tree.tag_configure(tag_name, foreground="red")
            tot_uscite += imp
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
        text = f"Totale entrate: {e_str} €  Totale uscite: {u_str} €  Saldo: {s_str} €"
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
    aggiorna_totali()
    tree.bind("<Double-1>", lambda evt: self.goto_day_from_popup(tree, popup))
    
    def on_right_click(event):
        item_id = tree.identify_row(event.y)
        if not item_id:
            return
        values = tree.item(item_id, "values")
        if not values:
            return
        descrizione = str(values[1]).strip()
        importo_str = str(values[2]).replace("€", "").replace(".", "").replace(",", ".").strip()
        tipo        = str(values[3]).strip()
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
        if "♻️" not in descrizione:
            self.desc_entry.insert(0, descrizione[:30])
        if self.tipo_spesa_var.get() != tipo:
            self.toggle_tipo_spesa()
        nome_conto = str(values[4]).strip() if len(values) > 4 else ""
        if nome_conto and nome_conto != "(nessuno)" and hasattr(self, "cb_conto_movimento"):
            self.cb_conto_movimento.set(nome_conto)
        self.after(0, self.imp_entry.focus_set)
        popup.destroy()
        for attr in ['_caller_popup']:
            w = getattr(self, attr, None)
            if w and w.winfo_exists():
                try:
                    w.destroy()
                except:
                    pass
            setattr(self, attr, None)
    tree.bind("<Button-3>", on_right_click)
    img_chiudi_pop = self.icone_gui.get("chiudi")
    btn_chiudi_pop = tk.Label(popup, compound="left", image=img_chiudi_pop, text="Chiudi" if img_chiudi_pop else "Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padx=15, pady=6, font=("Arial", 9, "bold"))
    btn_chiudi_pop.pack(pady=4)
    btn_chiudi_pop.bind("<Button-1>", lambda e: popup.destroy())
