#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import datetime
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, filedialog
from moduli.modello_spesa import campo

def open_compare_window(self):
    if getattr(self, 'confronto_popup', None) is not None and self.confronto_popup.winfo_exists():
        self.confronto_popup.deiconify()
        self.confronto_popup.lift()
        self.confronto_popup.focus_force()
        return
    import __main__ as _app
    EXPORT_FILES = _app.EXPORT_FILES
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO

    self.mostra_treeview_statistiche()
    today = datetime.date.today()
    mese_oggi = f"{today.month:02d}"
    anno_oggi = str(today.year)
    compare_by_year = tk.BooleanVar(value=False)
    mostra_future_var = tk.BooleanVar(value=True)
    conto_var = tk.StringVar(value="Tutti i conti")
    def _lista_conti_presenti():
        try:
            with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _f:
                _db_c = json.load(_f)
            _nomi_conti = [c.get("nome", "?") for c in _db_c.get("conti", [])]
        except Exception:
            _nomi_conti = []
        return ["Tutti i conti"] + sorted(_nomi_conti)
    def parse_date(d):
        if isinstance(d, datetime.date):
            return d
        try:
            if len(d.split("-")[0]) == 4:
                return datetime.datetime.strptime(d, "%Y-%m-%d").date()
            else:
                return datetime.datetime.strptime(d, "%d-%m-%Y").date()
        except Exception:
            return None
    def get_rows(mese, anno, per_anno=False):
        rows = []
        oggi = datetime.date.today()
        conto_sel = conto_var.get()
        for d_raw in sorted(self.spese):
            d = parse_date(d_raw)
            if not d:
                continue
            if not mostra_future_var.get() and d > oggi:
                continue
            if (per_anno and d.year == anno) or \
               (not per_anno and d.month == mese and d.year == anno):
                for voce in self.spese[d_raw]:
                    try:
                        if len(voce) >= 4:
                            cat, desc, imp, tipo = voce[0], voce[1], voce[2], voce[3]
                            if conto_sel != "Tutti i conti":
                                conto_voce = campo(voce, "conto", "")
                                if conto_voce != conto_sel:
                                    continue
                            data_pagamento = d.strftime("%d-%m-%Y")
                            entrata = imp if tipo == "Entrata" else 0
                            uscita = imp if tipo == "Uscita" else 0
                            rows.append((cat, data_pagamento, entrata, uscita))
                    except Exception as e:
                        continue
        return rows
    def aggregate_rows_by_category(raw_rows, date_placeholder="Totale"):
        aggregated_data = defaultdict(lambda: [0.0, 0.0])
        for cat, _, ent, usc in raw_rows:
            aggregated_data[cat][0] += ent
            aggregated_data[cat][1] += usc
        result_rows = []
        for cat in sorted(aggregated_data.keys()):
             ent, usc = aggregated_data[cat]
             result_rows.append((cat, date_placeholder, ent, usc)) 
        return result_rows
    popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    popup.withdraw()
    self.confronto_popup = popup
    self.update_idletasks()
    main_x = self.winfo_rootx()
    main_y = self.winfo_rooty()
    main_width = self.winfo_width()
    main_height = self.winfo_height()
    popup_width = 1030    
    popup_height = 560
    center_x = main_x + (main_width // 2) - (popup_width // 2)
    center_y = main_y + (main_height // 2) - (popup_height // 2)
    popup.geometry(f"{popup_width}x{popup_height}+{center_x}+{center_y}")
    popup.minsize(popup_width, popup_height)
    popup.transient(self)
    popup.title("Confronta mesi/anni per categoria")
    popup.deiconify()
    popup.bind("<Escape>", lambda e: popup.destroy())
    frame = ttk.Frame(popup)
    frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)
    frame.columnconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)
    anni_presenti_nel_db = set()
    for d_raw in self.spese.keys():
        d = parse_date(d_raw)
        if d:
            anni_presenti_nel_db.add(d.year)
    anni_correnti_e_db = sorted(list(anni_presenti_nel_db.union({today.year, today.year - 1, today.year + 1})), reverse=True) 
    anni = anni_correnti_e_db 
    mesi = [f"{i:02d}" for i in range(1, 13)]

    mode_frame = tk.Frame(frame, bg=self.COLOR_TOPLEVEL)
    mode_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
    tk.Label(mode_frame, text="Modalità confronto:", bg=self.COLOR_TOPLEVEL ,fg=self.TEXT_COLOR, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))
    ttk.Radiobutton(mode_frame, text="Mese", style="Custom.TRadiobutton", variable=compare_by_year, value=False, command=lambda: update_tables()).pack(side=tk.LEFT)
    ttk.Radiobutton(mode_frame, text="Anno", style="Custom.TRadiobutton", variable=compare_by_year, value=True, command=lambda: update_tables()).pack(side=tk.LEFT)
    ttk.Checkbutton(mode_frame, text="Includi movimenti futuri nei totali", variable=mostra_future_var).pack(side=tk.LEFT, padx=(30, 0))
    ttk.Label(mode_frame, text="Conto:", background=self.COLOR_TOPLEVEL, foreground=self.TEXT_COLOR, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(20, 6))
    cb_conto = ttk.Combobox(mode_frame, textvariable=conto_var, values=_lista_conti_presenti(), width=18, style="Border.TCombobox", state="readonly", font=("Arial", 10))
    cb_conto.pack(side=tk.LEFT)
    img_mouse = self.icone_gui.get("mouse")
    lbl_hint = ttk.Label(
        mode_frame,
        text="Doppio clic → Mostra Dettaglio ",
        image=img_mouse,
        compound="right",
        foreground="gray",
        font=("Arial", 9, "italic")
    )
    if img_mouse:
        lbl_hint.image = img_mouse
    lbl_hint.pack(side=tk.RIGHT, padx=(10, 0))
    left_select_frame = ttk.Frame(frame)
    left_select_frame.grid(row=1, column=0, sticky="ew", padx=(0, 16), pady=(0, 6))
    ttk.Label(left_select_frame, text="Mese/Anno 1", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 8))
    left_mese = tk.StringVar(value=mese_oggi)
    left_anno = tk.StringVar(value=anno_oggi)
    cb_lm = ttk.Combobox(left_select_frame, textvariable=left_mese, values=mesi, width=4, style="Border.TCombobox", state="readonly", font=("Arial", 10))
    cb_la = ttk.Combobox(left_select_frame, textvariable=left_anno, values=[str(a) for a in anni], width=7, style="Border.TCombobox", state="readonly", font=("Arial", 10))
    cb_lm.pack(side="left", padx=(0, 3))
    cb_la.pack(side="left")
    def reset_left():
        left_mese.set(mese_oggi)
        left_anno.set(anno_oggi)
    img_reload_l = self.icone_gui.get("reset")
    btn_reset_l = tk.Label(left_select_frame, compound="left", image=img_reload_l, text="Reset" if img_reload_l else "🔙 Reset", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padx=15, pady=6, font=("Arial", 9, "bold"))
    btn_reset_l.pack(side="right", padx=(0, 40))
    btn_reset_l.bind("<Button-1>", lambda e: reset_left())
    left_container = ttk.Frame(frame)
    left_container.grid(row=2, column=0, sticky="nswe", padx=(0, 16))
    left_container.grid_rowconfigure(0, weight=1)
    left_container.grid_columnconfigure(0, weight=1)
    left_vsb = ttk.Scrollbar(left_container, orient="vertical", style="Vertical.TScrollbar")
    left_vsb.grid(row=0, column=1, sticky="ns")
    left_tree = ttk.Treeview(left_container, columns=("Categoria", "Data", "Entrata", "Uscita"), show="headings", height=14,
                             yscrollcommand=left_vsb.set)
    left_tree.grid(row=0, column=0, sticky="nswe")
    left_vsb.config(command=left_tree.yview)
    left_tree.tag_configure('entrata', foreground='green')
    left_tree.tag_configure('uscita', foreground='red')
    for col, w, anchor in [("Categoria", 180, "w"), ("Data", 110, "center"), ("Entrata", 100, "center"), ("Uscita", 100, "center")]:
        left_tree.heading(col, text=col, anchor=anchor, command=lambda _col=col: self.treeview_sort_column(left_tree, _col, False))
        left_tree.column(col, width=w, anchor=anchor, stretch=False)
    left_diff_frame = tk.Frame(left_container, bg=self.COLOR_TOPLEVEL)
    left_diff_frame.grid(row=1, column=0, columnspan=2, pady=(4, 0), sticky=tk.W+tk.E)
    tk.Label(left_diff_frame, bg=self.COLOR_TOPLEVEL ,fg=self.TEXT_COLOR, text="Entrate:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
    left_total_ent_lbl = tk.Label(left_diff_frame, bg=self.COLOR_TOPLEVEL ,fg=self.TEXT_COLOR, text="", font=("Arial", 10, "bold"))
    left_total_ent_lbl.pack(side=tk.LEFT, padx=(2, 10))
    tk.Label(left_diff_frame, bg=self.COLOR_TOPLEVEL ,fg=self.TEXT_COLOR, text="Uscite:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
    left_total_usc_lbl = tk.Label(left_diff_frame, bg=self.COLOR_TOPLEVEL ,fg=self.TEXT_COLOR, text="", font=("Arial", 10, "bold"))
    left_total_usc_lbl.pack(side=tk.LEFT, padx=(2, 10))
    tk.Label(left_diff_frame, bg=self.COLOR_TOPLEVEL ,fg=self.TEXT_COLOR, text="Differenza:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
    left_diff_val_lbl = tk.Label(left_diff_frame, bg=self.COLOR_TOPLEVEL ,fg=self.TEXT_COLOR, text="", font=("Arial", 10, "bold"))
    left_diff_val_lbl.pack(side=tk.LEFT, padx=(2, 0))
    right_select_frame = ttk.Frame(frame)
    right_select_frame.grid(row=1, column=1, sticky="ew", pady=(0, 6))
    ttk.Label(right_select_frame, text="Mese/Anno 2", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(0, 8))
    right_mese = tk.StringVar(value=mese_oggi)
    right_anno = tk.StringVar(value=anno_oggi)
    cb_rm = ttk.Combobox(right_select_frame, textvariable=right_mese, values=mesi, width=4, style="Border.TCombobox", state="readonly", font=("Arial", 10))
    cb_ra = ttk.Combobox(right_select_frame, textvariable=right_anno, values=[str(a) for a in anni], width=7, style="Border.TCombobox", state="readonly", font=("Arial", 10))
    cb_rm.pack(side="left", padx=(0, 3))
    cb_ra.pack(side="left")
    def reset_right():
        right_mese.set(mese_oggi)
        right_anno.set(anno_oggi)
    img_reload_r = self.icone_gui.get("reset")
    btn_reset_r = tk.Label(right_select_frame, compound="left", image=img_reload_r, text="Reset" if img_reload_r else "🔙 Reset", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padx=15, pady=6, font=("Arial", 9, "bold"))
    btn_reset_r.pack(side="right", padx=7)
    btn_reset_r.bind("<Button-1>", lambda e: reset_right())
    right_container = ttk.Frame(frame)
    right_container.grid(row=2, column=1, sticky="nswe")
    right_container.grid_rowconfigure(0, weight=1)
    right_container.grid_columnconfigure(0, weight=1)
    right_vsb = ttk.Scrollbar(right_container, orient="vertical", style="Vertical.TScrollbar")
    right_vsb.grid(row=0, column=1, sticky="ns")
    right_tree = ttk.Treeview(right_container, columns=("Categoria", "Data", "Entrata", "Uscita"), show="headings", height=14,
                              yscrollcommand=right_vsb.set)
    right_tree.grid(row=0, column=0, sticky="nswe")
    right_vsb.config(command=right_tree.yview)
    right_tree.tag_configure('entrata', foreground='green')
    right_tree.tag_configure('uscita', foreground='red')
    for col, w, anchor in [("Categoria", 180, "w"), ("Data", 110, "center"), ("Entrata", 100, "center"), ("Uscita", 100, "center")]:
        right_tree.heading(col, text=col, anchor=anchor, command=lambda _col=col: self.treeview_sort_column(right_tree, _col, False))
        right_tree.column(col, width=w, anchor=anchor, stretch=False)
    right_diff_frame = tk.Frame(right_container, bg=self.COLOR_TOPLEVEL)
    right_diff_frame.grid(row=1, column=0, columnspan=2, pady=(4, 0), sticky=tk.W+tk.E)
    tk.Label(right_diff_frame, bg=self.COLOR_TOPLEVEL ,fg=self.TEXT_COLOR, text="Entrate:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
    right_total_ent_lbl = tk.Label(right_diff_frame, bg=self.COLOR_TOPLEVEL ,fg=self.TEXT_COLOR, text="", font=("Arial", 10, "bold"))
    right_total_ent_lbl.pack(side=tk.LEFT, padx=(2, 10))
    tk.Label(right_diff_frame, bg=self.COLOR_TOPLEVEL ,fg=self.TEXT_COLOR, text="Uscite:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
    right_total_usc_lbl = tk.Label(right_diff_frame, bg=self.COLOR_TOPLEVEL ,fg=self.TEXT_COLOR, text="", font=("Arial", 10, "bold"))
    right_total_usc_lbl.pack(side=tk.LEFT, padx=(2, 10))
    tk.Label(right_diff_frame, bg=self.COLOR_TOPLEVEL ,fg=self.TEXT_COLOR, text="Differenza:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
    right_diff_val_lbl = tk.Label(right_diff_frame, bg=self.COLOR_TOPLEVEL ,fg=self.TEXT_COLOR, text="", font=("Arial", 10, "bold"))
    right_diff_val_lbl.pack(side=tk.LEFT, padx=(2, 0))
    def create_double_click_wrapper(treeview, mese_var, anno_var, per_anno_mode):
        def wrapper(event):
            item_id = treeview.identify_row(event.y)
            if not item_id:
                return
            values = treeview.item(item_id, "values")
            if not values or len(values) < 1:
                return
            original_stats_table = getattr(self, 'stats_table', None)
            original_mode = getattr(self, 'stats_mode', None)
            original_refdate = getattr(self, 'stats_refdate', None)
            try:
                self.stats_table = treeview
                mode_str = "anno" if per_anno_mode.get() else "mese"
                self.stats_mode = tk.StringVar(value=mode_str)
                mese_val = int(mese_var.get())
                anno_val = int(anno_var.get())
                self.stats_refdate = datetime.date(anno_val, mese_val, 1)
                self._caller_popup = popup
                if hasattr(self, 'on_stats_table_double_click'):
                    self.on_stats_table_double_click(event)
                else:
                    print(f"Errore: Funzione di dettaglio (on_stats_table_double_click) non trovata.")
            except Exception as e:
                print(f"Errore critico durante l'esecuzione del wrapper: {e}") 
            if original_stats_table is not None:
                self.stats_table = original_stats_table
            elif hasattr(self, 'stats_table'):
                del self.stats_table
            if original_mode is not None:
                self.stats_mode = original_mode
            elif hasattr(self, 'stats_mode'):
                del self.stats_mode
            if original_refdate is not None:
                self.stats_refdate = original_refdate
            elif hasattr(self, 'stats_refdate'):
                del self.stats_refdate
        return wrapper
    def update_month_visibility():
        is_annual = compare_by_year.get()
        if is_annual:
            cb_lm.pack_forget()
            cb_rm.pack_forget()
        else:
            cb_la.pack_forget() 
            cb_lm.pack(side="left", padx=(0, 3)) 
            cb_la.pack(side="left") 
            
            cb_ra.pack_forget()
            cb_rm.pack(side="left", padx=(0, 3))
            cb_ra.pack(side="left")
    def update_tables():
        update_month_visibility()
        per_anno = compare_by_year.get()
        a1, a2 = int(left_anno.get()), int(right_anno.get())
        m1 = int(left_mese.get()) if not per_anno else 1
        m2 = int(right_mese.get()) if not per_anno else 1
        rows1_raw, rows2_raw = get_rows(m1, a1, per_anno), get_rows(m2, a2, per_anno)
        date_placeholder = "Totale Anno" if per_anno else "Totale Mese"
        rows1 = aggregate_rows_by_category(rows1_raw, date_placeholder)
        rows2 = aggregate_rows_by_category(rows2_raw, date_placeholder)
        left_tree.delete(*left_tree.get_children())
        tot_ent1, tot_usc1 = 0, 0
        for cat, data, ent, usc in sorted(rows1, key=lambda x: x[0].lower()): 
            tag = 'entrata' if ent > 0 else ('uscita' if usc > 0 else '')
            left_tree.insert("", "end", values=(cat, data, f"{ent:.2f} €", f"{usc:.2f} €"), tags=(tag,))
            tot_ent1, tot_usc1 = tot_ent1 + ent, tot_usc1 + usc
        diff1 = tot_ent1 - tot_usc1
        left_total_ent_lbl.config(text=f"{tot_ent1:,.2f} €", fg="green")
        left_total_usc_lbl.config(text=f"{tot_usc1:,.2f} €", fg="red")
        left_diff_val_lbl.config(
            text=f"{diff1:,.2f} €",
            fg="green" if diff1 >= 0 else "red"
        )
        right_tree.delete(*right_tree.get_children())
        tot_ent2, tot_usc2 = 0, 0
        for cat, data, ent, usc in sorted(rows2, key=lambda x: x[0].lower()):
            tag = 'entrata' if ent > 0 else ('uscita' if usc > 0 else '')
            right_tree.insert("", "end", values=(cat, data, f"{ent:.2f} €", f"{usc:.2f} €"), tags=(tag,))
            tot_ent2, tot_usc2 = tot_ent2 + ent, tot_usc2 + usc
        diff2 = tot_ent2 - tot_usc2
        right_total_ent_lbl.config(text=f"{tot_ent2:,.2f} €", fg="green")
        right_total_usc_lbl.config(text=f"{tot_usc2:,.2f} €", fg="red")
        right_diff_val_lbl.config(
            text=f"{diff2:,.2f} €",
            fg="green" if diff2 >= 0 else "red"
        )
        left_tree.unbind('<Double-1>')
        right_tree.unbind('<Double-1>')
        left_tree.bind('<Double-1>', create_double_click_wrapper(left_tree, left_mese, left_anno, compare_by_year))
        right_tree.bind('<Double-1>', create_double_click_wrapper(right_tree, right_mese, right_anno, compare_by_year))
    for var in [left_mese, left_anno, right_mese, right_anno, compare_by_year, mostra_future_var, conto_var]:
        var.trace_add("write", lambda *a: update_tables())
    update_tables()
    def do_preview_export():
        per_anno = compare_by_year.get()
        a1, a2 = int(left_anno.get()), int(right_anno.get())
        m1 = int(left_mese.get()) if not per_anno else 1
        m2 = int(right_mese.get()) if not per_anno else 1
        rows1_raw, rows2_raw = get_rows(m1, a1, per_anno), get_rows(m2, a2, per_anno)
        label1 = f"{m1:02d}/{str(a1)[-2:]}" if not per_anno else str(a1)
        label2 = f"{m2:02d}/{str(a2)[-2:]}" if not per_anno else str(a2)
        lines = [f"Confronto tra {label1} e {label2}\n"]
        lines.append(f"{'Categoria':<33}{'Entrate ' + label1:>13}{'Uscite ' + label1:>13}  {'Entrate ' + label2:>13}{'Uscite ' + label2:>13}  {'Δ Entrate':>13}{'Δ Uscite':>13}")
        lines.append("─" * 130)
        data1 = defaultdict(lambda: [0.0, 0.0])
        for cat, _, ent, usc in rows1_raw:
            data1[cat][0] += ent
            data1[cat][1] += usc
        data2 = defaultdict(lambda: [0.0, 0.0])
        for cat, _, ent, usc in rows2_raw:
            data2[cat][0] += ent
            data2[cat][1] += usc
        tutte_le_categorie = sorted(set(data1.keys()) | set(data2.keys()))
        for cat in tutte_le_categorie:
            ent1, usc1 = data1[cat]
            ent2, usc2 = data2[cat]
            diff_ent, diff_usc = ent2 - ent1, usc2 - usc1
            lines.append(f"{cat:<20.20} {'':<12} {ent1:12,.2f} {usc1:12,.2f}   {ent2:12,.2f} {usc2:12,.2f}   {diff_ent:12,.2f} {diff_usc:12,.2f}")
        tot_ent1, tot_usc1 = sum(v[0] for v in data1.values()), sum(v[1] for v in data1.values())
        diff1 = tot_ent1 - tot_usc1
        tot_ent2, tot_usc2 = sum(v[0] for v in data2.values()), sum(v[1] for v in data2.values())
        diff2 = tot_ent2 - tot_usc2
        diff_ent_tot, diff_usc_tot = tot_ent2 - tot_ent1, tot_usc2 - tot_usc1
        lines.append("─" * 130)
        lines.append(f"{'TOTALI GENERALI':<33} {tot_ent1:12,.2f} {tot_usc1:12,.2f}   {tot_ent2:12,.2f} {tot_usc2:12,.2f}   {diff_ent_tot:12,.2f} {diff_usc_tot:12,.2f}")
        saldo1_str = f"{diff1:,.2f} €"
        saldo2_str = f"{diff2:,.2f} €"
        lines.append(f"{'RISPARMIO NETTO (Saldo)':<33} {saldo1_str:>25}   {saldo2_str:>25}  ")
        lines.append("─" * 130)
        text = "\n".join(lines)
        prev = tk.Toplevel(popup, bg=self.COLOR_TOPLEVEL)
        prev.title("Preview Esporta confronto")
        popup_width = 1100
        popup_height = 580
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        center_x = int((screen_width / 2) - (popup_width / 2))
        center_y = int((screen_height / 2) - (popup_height / 2))
        prev.geometry(f"{popup_width}x{popup_height}+{center_x}+{center_y}")
        prev.minsize(popup_width, popup_height)
        prev.transient(popup)
        prev.bind("<Escape>", lambda e: prev.destroy())
        text_frame = tk.Frame(prev)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 0))
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)
        vsb_text = ttk.Scrollbar(text_frame, orient="vertical", style="Vertical.TScrollbar")
        vsb_text.grid(row=0, column=1, sticky="ns")
        t = tk.Text(text_frame, font=("Courier New", 10), wrap="none", yscrollcommand=vsb_text.set)
        t.grid(row=0, column=0, sticky="nswe")
        vsb_text.config(command=t.yview)
        t.insert(tk.END, text)
        t.config(state="disabled")
        def do_save():
            now = datetime.date.today()
            default_filename = f"Confronto_Export_{now.day:02d}-{now.month:02d}-{now.year}.txt"
            file = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("File txt", "*.txt")], initialdir=EXPORT_FILES, initialfile=default_filename, title="Esporta confronto", confirmoverwrite=False, parent=prev)
            if file:
                if os.path.exists(file) and (not hasattr(self, 'show_custom_askyesno') or not self.show_custom_askyesno("Sovrascrivere file?", f"Il file '{os.path.basename(file)}' \nesiste già. Vuoi sovrascriverlo?")):
                    return
                with open(file, "w", encoding="utf-8") as f:
                    f.write(text)
                if hasattr(self, "show_custom_warning"):
                    self.show_custom_warning("Esportazione completata", f"Tabella confronti esportata in:\n{file}")
        frm = tk.Frame(prev, bg=self.COLOR_TOPLEVEL)
        frm.pack(fill=tk.X, padx=10, pady=8)
        img_esporta = self.icone_gui.get("salva")
        btn_esporta = tk.Label(frm, compound="left", image=img_esporta, text="Esporta" if img_esporta else "💾 Esporta", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padx=15, pady=6, font=("Arial", 9, "bold"))
        btn_esporta.pack(side=tk.LEFT, padx=6)
        btn_esporta.bind("<Button-1>", lambda e: do_save())
        if hasattr(self, '_stampa_lista_diretta'):
            img_stampa = self.icone_gui.get("stampa")
            btn_stampa = tk.Label(frm, compound="left", image=img_stampa, text="Stampa" if img_stampa else "📄 Stampa", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padx=15, pady=6, font=("Arial", 9, "bold"))
            btn_stampa.pack(side=tk.LEFT, padx=6)
            btn_stampa.bind("<Button-1>", lambda e: self._stampa_lista_diretta(text, self.show_custom_warning))
        img_chiudi_v = self.icone_gui.get("chiudi")
        btn_chiudi_v = tk.Label(frm, compound="left", image=img_chiudi_v, text="Chiudi" if img_chiudi_v else "❌ Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padx=15, pady=6, font=("Arial", 9, "bold"))
        btn_chiudi_v.pack(side=tk.RIGHT, padx=6)
        btn_chiudi_v.bind("<Button-1>", lambda e: prev.destroy())
        prev.lift()
        prev.focus_force()
        prev.attributes('-topmost', True)
        prev.after(100, lambda: prev.attributes('-topmost', False))
    btnframe = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    btnframe.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 7))
    img_export_c = self.icone_gui.get("salva")
    btn_export_c = tk.Label(btnframe, compound="left", image=img_export_c, text="Esporta" if img_export_c else "📄 Esporta", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padx=15, pady=6, font=("Arial", 9, "bold"))
    btn_export_c.pack(side=tk.LEFT, padx=8)
    btn_export_c.bind("<Button-1>", lambda e: do_preview_export())
    img_grafico_c = self.icone_gui.get("grafico_linea")
    btn_grafico_c = tk.Label(btnframe, compound="left", image=img_grafico_c, text="Mostra Grafico" if img_grafico_c else "Mostra Grafico", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padx=15, pady=6, font=("Arial", 9, "bold"))
    btn_grafico_c.pack(side=tk.LEFT, padx=8)
    btn_grafico_c.bind("<Button-1>", lambda e: self.crea_grafico_confronto(left_mese.get(), left_anno.get(), right_mese.get(), right_anno.get(), compare_by_year.get(), conto_sel=conto_var.get(), mostra_future=mostra_future_var.get()))
    img_chiudi_c = self.icone_gui.get("chiudi")
    btn_chiudi_c = tk.Label(btnframe, compound="left", image=img_chiudi_c, text="Chiudi" if img_chiudi_c else "❌ Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padx=15, pady=6, font=("Arial", 9, "bold"))
    btn_chiudi_c.pack(side=tk.RIGHT, padx=8)
    btn_chiudi_c.bind("<Button-1>", lambda e: popup.destroy())
    
def crea_grafico_confronto(self, m1_str, a1_str, m2_str, a2_str, per_anno, categoria_sel=None, mostra_future=True, conto_sel=None):
    if getattr(self, 'popup_grafico_confronto', None) is not None and self.popup_grafico_confronto.winfo_exists():
        self.popup_grafico_confronto.destroy()
    try:
        m1, a1, m2, a2 = int(m1_str), int(a1_str), int(m2_str), int(a2_str)
        p1_color = "#1f77b4"
        p2_color = "#ff7f0e"
        bg_color = getattr(self, "COLOR_TOPLEVEL", None)
        text_color = getattr(self, "TEXT_COLOR", "#000000")
        def parse_amount(s):
            if s is None: return 0.0
            if isinstance(s, (int, float)): return float(s)
            s = str(s).strip().replace('€', '').replace('\xa0', ' ')
            s = re.sub(r'\s+', '', s)
            if '.' in s and ',' in s: s = s.replace('.', '').replace(',', '.')
            elif ',' in s: s = s.replace(',', '.')
            elif '.' in s:
                last_dot_idx = s.rfind('.')
                if len(s) - last_dot_idx - 1 != 2: s = s.replace('.', '')
            try: return float(s)
            except Exception:
                s2 = re.sub(r'[^0-9\-\.+]', '', s)
                try: return float(s2) if s2 not in ('', '-', '+') else 0.0
                except Exception: return 0.0
        def format_euro(val, decimals=2):
            neg = val < 0
            val_abs = abs(val)
            formatted = f"{val_abs:,.{decimals}f}"
            formatted = formatted.replace(',', 'X').replace('.', ',').replace('X', '.')
            return ("-" if neg else "") + formatted + ""
        popup_width = 1100
        popup_height = 600
        popup_grafico = tk.Toplevel(self)
        self.popup_grafico_confronto = popup_grafico
        popup_grafico.title("Grafico Confronto Periodi")
        popup_grafico.transient(self)
        popup_grafico.minsize(1100, 600)
        popup_grafico.configure(bg=bg_color)
        popup_grafico.withdraw()
        self.update_idletasks()
        main_x = self.winfo_rootx()
        main_y = self.winfo_rooty()
        main_width = self.winfo_width()
        main_height = self.winfo_height()
        center_x = max(0, main_x + (main_width // 2) - (popup_width // 2))
        center_y = max(0, main_y + (main_height // 2) - (popup_height // 2))
        popup_grafico.geometry(f"{popup_width}x{popup_height}+{center_x}+{center_y}")
        main_frame = tk.Frame(popup_grafico, bg=bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True)
        controls_frame = tk.Frame(main_frame, bg=bg_color)
        controls_frame.pack(fill=tk.X, side=tk.TOP, padx=6, pady=6)
        mostra_future_var = tk.BooleanVar(value=mostra_future)
        ttk.Checkbutton(
            controls_frame,
            text="Includi movimenti futuri",
            variable=mostra_future_var
        ).pack(side=tk.LEFT, padx=(0, 16))
        categories_list_raw = getattr(self, "_saved_info", {}).get("categorie", [])
        if not categories_list_raw and getattr(self, "categorie", None):
            categories_list_raw = getattr(self, "categorie", [])
        categories_list = sorted([c for c in categories_list_raw if isinstance(c, str) and c])
        if "Tutte le Categorie" not in categories_list:
            categories_list.insert(0, "Tutte le Categorie")
        initial_categoria = categoria_sel if categoria_sel and categoria_sel in categories_list else "Tutte le Categorie"
        categoria_var = tk.StringVar(value=initial_categoria)
        combobox_cat = ttk.Combobox(controls_frame, textvariable=categoria_var, values=categories_list, state="readonly", style="Border.TCombobox", width=30)
        combobox_cat.pack(side=tk.RIGHT, padx=(0, 6))
        tk.Label(controls_frame, text="Filtra Categoria:", bg=bg_color, fg=text_color).pack(side=tk.RIGHT, padx=(4, 2))
        title_frame = tk.Frame(main_frame, bg=bg_color)
        title_frame.pack(fill=tk.X, side=tk.TOP)
        tk.Label(title_frame, text=f"Andamento Saldo Netto ({'Mensile' if per_anno else 'Giornaliero'})", bg=bg_color, fg=text_color, font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=8, pady=(0, 4))
        img_mouse = self.icone_gui.get("mouse")
        lbl_hint = tk.Label(
            title_frame,
            text="Doppio clic → Mostra Dettaglio ",
            image=img_mouse,
            compound="right",
            background=bg_color,
            foreground="gray",
            font=("Arial", 9, "italic")
        )
        if img_mouse:
            lbl_hint.image = img_mouse
        lbl_hint.pack(side=tk.LEFT, pady=(0, 4))
        subtitle_frame = tk.Frame(title_frame, bg=bg_color)
        subtitle_frame.pack(side=tk.LEFT, padx=8)
        subtitle_p1_label = tk.Label(subtitle_frame, text="", bg=bg_color, fg=p1_color, font=("Arial", 9, "bold"))
        subtitle_p1_label.pack(side=tk.LEFT, padx=(0, 4))
        subtitle_sep_label = tk.Label(subtitle_frame, text="|", bg=bg_color, fg=text_color, font=("Arial", 9))
        subtitle_sep_label.pack(side=tk.LEFT, padx=(0, 4))
        subtitle_p2_label = tk.Label(subtitle_frame, text="", bg=bg_color, fg=p2_color, font=("Arial", 9, "bold"))
        subtitle_p2_label.pack(side=tk.LEFT, padx=(0, 8))
        subtitle_cat_label = tk.Label(subtitle_frame, text="", bg=bg_color, fg=text_color, font=("Arial", 9))
        subtitle_cat_label.pack(side=tk.LEFT)
        canvas = tk.Canvas(main_frame, bg=bg_color)
        canvas.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        bottom_frame = tk.Frame(main_frame, bg=bg_color)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=6, pady=6)
        legenda_frame = tk.Frame(bottom_frame, bg=bg_color)
        legenda_frame.pack(side=tk.LEFT)
        btn_container = tk.Frame(bottom_frame, bg=bg_color)
        btn_container.pack(side=tk.LEFT, padx=(6, 8))
        img_chiudi_gr = self.icone_gui.get("chiudi")
        btn_chiudi_gr = tk.Label(btn_container, compound="left", image=img_chiudi_gr, text="Chiudi" if img_chiudi_gr else "❌ Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padx=15, pady=6, font=("Arial", 9, "bold"))
        btn_chiudi_gr.pack(side=tk.LEFT)
        btn_chiudi_gr.bind("<Button-1>", lambda e: popup_grafico.destroy())
        right_diff_frame = tk.Frame(bottom_frame, bg=bg_color)
        right_diff_frame.pack(side=tk.RIGHT, padx=(6, 8))
        p1_totals_lbl = tk.Label(right_diff_frame, bg=bg_color, fg=p1_color, text="", font=("Arial", 10, "bold"))
        p1_totals_lbl.pack(anchor="e")
        p2_totals_lbl = tk.Label(right_diff_frame, bg=bg_color, fg=p2_color, text="", font=("Arial", 10, "bold"))
        p2_totals_lbl.pack(anchor="e")
        delta_lbl = tk.Label(right_diff_frame, bg=bg_color, fg=text_color, text="", font=("Arial", 10, "bold"))
        delta_lbl.pack(anchor="e", pady=(6, 0))
        saldos1 = []
        saldos2 = []
        labels_x = []
        keys_all = []
        data1_raw_cache = {}
        data2_raw_cache = {}
        month_abbr_it = {'01': 'Gen', '02': 'Feb', '03': 'Mar', '04': 'Apr', '05': 'Mag', '06': 'Giu',
                         '07': 'Lug', '08': 'Ago', '09': 'Set', '10': 'Ott', '11': 'Nov', '12': 'Dic'}
        def get_rows_confronto(mese, anno_param, per_anno_mode, categoria_filter):
            def parse_date_obj(d):
                if isinstance(d, datetime.date): return d
                if d is None: return None
                d_str = str(d).strip()
                try:
                    if re.match(r'^\d{4}-\d{1,2}-\d{1,2}$', d_str): return datetime.datetime.strptime(d_str, "%Y-%m-%d").date()
                    if re.match(r'^\d{1,2}-\d{1,2}-\d{4}$', d_str): return datetime.datetime.strptime(d_str, "%d-%m-%Y").date()
                    for fmt in ("%d/%m/%Y", "%Y/%m/%d", "%d.%m.%Y"):
                        try: return datetime.datetime.strptime(d_str, fmt).date()
                        except Exception: pass
                except Exception: pass
                return None
            oggi = datetime.date.today()
            rows_grouped = defaultdict(lambda: [0.0, 0.0])
            categories_list_raw = getattr(self, "_saved_info", {}).get("categorie", [])
            if not categories_list_raw:
                categories_list_raw = getattr(self, "categorie", [])
            categorie_known = [c.strip().lower() for c in categories_list_raw if isinstance(c, str)]
            for d_raw, entries in getattr(self, "spese", {}).items():
                d = d_raw if isinstance(d_raw, datetime.date) else parse_date_obj(d_raw)
                if not d: continue
                if not mostra_future_var.get() and d > oggi:
                    continue
                if per_anno_mode:
                    if d.year != int(anno_param): continue
                    key = f"{d.month:02d}"
                else:
                    if d.year != int(anno_param) or d.month != int(mese): continue
                    key = f"{d.year}-{d.month:02d}-{d.day:02d}"
                for entry in entries:
                    try:
                        categoria_val = None
                        imp = None
                        tipo = None
                        try:
                            categoria_val = campo(entry, "categoria", None)
                            imp = campo(entry, "importo", None)
                            tipo = campo(entry, "tipo", None)
                        except Exception:
                            categoria_val = None
                        if categoria_val is None or imp is None or tipo is None:
                            if isinstance(entry, dict):
                                categoria_val = entry.get('categoria') or entry.get('category') or entry.get('cat')
                                imp = entry.get('importo') or entry.get('import') or entry.get('amount')
                                tipo = entry.get('tipo') or entry.get('type')
                            else:
                                try:
                                    if len(entry) >= 4:
                                        categoria_val = entry[0]; imp = entry[2]; tipo = entry[3]
                                    else:
                                        continue
                                except Exception:
                                    continue
                        if isinstance(categoria_val, str):
                            categoria_val = categoria_val.strip()
                        if categoria_filter and categoria_filter != "Tutte le Categorie":
                            if categoria_val is None or str(categoria_val).strip().lower() != str(categoria_filter).strip().lower(): continue
                        if conto_sel and conto_sel != "Tutti i conti":
                            conto_val = campo(entry, "conto", "")
                            if conto_val != conto_sel: continue
                        importo_f = parse_amount(imp)
                        if str(tipo).strip().lower() == "entrata": rows_grouped[key][0] += importo_f
                        else: rows_grouped[key][1] += importo_f
                    except Exception: continue
            return rows_grouped
        def update_totals_display(d1, d2):
            ent_p1 = sum(v[0] for v in d1.values()); usc_p1 = sum(v[1] for v in d1.values()); diff_p1 = ent_p1 - usc_p1
            ent_p2 = sum(v[0] for v in d2.values()); usc_p2 = sum(v[1] for v in d2.values()); diff_p2 = ent_p2 - usc_p2
            p1_totals_lbl.config(text=f"P1 — Entrate: {format_euro(ent_p1,2)}  Uscite: {format_euro(usc_p1,2)}  Saldo: {format_euro(diff_p1,2)}")
            p2_totals_lbl.config(text=f"P2 — Entrate: {format_euro(ent_p2,2)}  Uscite: {format_euro(usc_p2,2)}  Saldo: {format_euro(diff_p2,2)}")
            delta = diff_p2 - diff_p1
            fg = "#2ca02c" if delta > 0 else ("#d62728" if delta < 0 else text_color)
            delta_lbl.config(text=f"Variazione Saldo (P2 vs P1): {format_euro(delta,2)}", fg=fg)
        def update_data(categoria_choice):
            nonlocal saldos1, saldos2, labels_x, keys_all, data1_raw_cache, data2_raw_cache
            data1_raw_cache = get_rows_confronto(m1, a1, per_anno, categoria_choice)
            data2_raw_cache = get_rows_confronto(m2, a2, per_anno, categoria_choice)
            keys_all = sorted(set(data1_raw_cache.keys()) | set(data2_raw_cache.keys()))
            saldos1 = []; saldos2 = []; labels_x = []
            for key in keys_all:
                ent1, usc1 = data1_raw_cache.get(key, (0.0, 0.0)); ent2, usc2 = data2_raw_cache.get(key, (0.0, 0.0))
                saldos1.append(ent1 - usc1); saldos2.append(ent2 - usc2)
                if per_anno: labels_x.append(key)
                else:
                    parts = key.split('-'); labels_x.append(parts[2] if len(parts) == 3 else key)
            update_totals_display(data1_raw_cache, data2_raw_cache)
        def update_subtitle(categoria_choice):
            periodo_p1 = f"{a1}" if per_anno else f"{m1:02d}/{a1}"
            periodo_p2 = f"{a2}" if per_anno else f"{m2:02d}/{a2}"
            subtitle_p1_label.config(text=f"P1: {periodo_p1}")
            subtitle_p2_label.config(text=f"P2: {periodo_p2}")
            subtitle_cat_label.config(text=f"Categoria: {categoria_choice}")
        def refresh_all():
            update_data(categoria_var.get())
            update_subtitle(categoria_var.get())
            draw_chart()
        def draw_chart():
            try:
                MIN_BAR_HEIGHT_PX = 4
                canvas_width = max(200, canvas.winfo_width()); canvas_height = max(120, canvas.winfo_height())
                canvas.delete("all")
                side_padding_factor = 0.035
                side_padding = max(50, int(canvas_width * side_padding_factor))
                right_padding = max(20, int(canvas_width * side_padding_factor))
                top_padding_plot = max(12, int(canvas_height * 0.08))
                bottom_padding_plot = max(48, int(canvas_height * 0.15))
                plot_width = canvas_width - side_padding - right_padding
                plot_height = canvas_height - top_padding_plot - bottom_padding_plot
                if plot_width <= 0 or plot_height <= 10: return
                plot_vals1 = [abs(v) for v in saldos1]
                plot_vals2 = [abs(v) for v in saldos2]
                all_plot_vals = plot_vals1 + plot_vals2
                max_val = max(all_plot_vals) if any(all_plot_vals) else 100.0
                min_val = 0.0
                y_range = max_val - min_val
                if y_range == 0: max_val = max_val + 50; y_range = max_val - min_val
                margin = y_range * 0.15
                max_val += margin; y_range = max_val - min_val
                def scale_y_plot(val):
                    normalized = (val - min_val) / y_range
                    return top_padding_plot + plot_height * (1 - normalized)
                canvas_y_top = top_padding_plot; canvas_y_end = top_padding_plot + plot_height
                canvas.create_line(side_padding, canvas_y_top, side_padding, canvas_y_end, fill="gray", width=2)
                canvas.create_text(side_padding - 6, scale_y_plot(max_val), anchor="e", text=format_euro(max_val, 0), font=("Arial", 9), fill=text_color)
                canvas.create_text(side_padding - 6, scale_y_plot(min_val), anchor="e", text=format_euro(min_val, 0), font=("Arial", 9), fill=text_color)
                num_points = len(labels_x)
                if num_points == 0: return
                x_step = plot_width / num_points
                bar_w = max(6, int(min(40, x_step * 0.35)))
                gap = max(4, int(bar_w * 0.2))
                y_base = scale_y_plot(0)
                small_font = ("Arial", 8)
                y_base_tic = canvas_y_end + 6
                def _clamp(v, lo, hi): return max(lo, min(hi, v))
                label_offset = 10
                for i, label in enumerate(labels_x):
                    x_center = side_padding + x_step * (i + 0.5)
                    x0_p1 = x_center - (bar_w + gap // 2); x1_p1 = x_center - (gap // 2)
                    x0_p2 = x_center + (gap // 2); x1_p2 = x_center + (bar_w + gap // 2)
                    v1 = plot_vals1[i] if i < len(plot_vals1) else 0.0
                    v2 = plot_vals2[i] if i < len(plot_vals2) else 0.0
                    yv1 = scale_y_plot(v1); yv2 = scale_y_plot(v2)
                    top1 = yv1; bottom1 = y_base
                    if v1 > 0 and (bottom1 - top1) < MIN_BAR_HEIGHT_PX: top1 = bottom1 - MIN_BAR_HEIGHT_PX
                    top1 = _clamp(top1, canvas_y_top, canvas_y_end); bottom1 = _clamp(bottom1, canvas_y_top, canvas_y_end)
                    canvas.create_rectangle(x0_p1, top1, x1_p1, bottom1, fill=p1_color, outline="", tags=(f"bar_p1_{i}", "bar_p1", "bar"))
                    signed_v1 = saldos1[i] if i < len(saldos1) else 0.0
                    tx1 = (x0_p1 + x1_p1) / 2
                    ty1 = _clamp(top1 - label_offset, canvas_y_top + 4, canvas_y_end - 4)
                    color_v1 = "#d62728" if signed_v1 < 0 else ("#2ca02c" if signed_v1 > 0 else text_color)
                    canvas.create_text(tx1, ty1, text=format_euro(signed_v1, 0), fill=color_v1, font=("Arial", 8))
                    top2 = yv2; bottom2 = y_base
                    if v2 > 0 and (bottom2 - top2) < MIN_BAR_HEIGHT_PX: top2 = bottom2 - MIN_BAR_HEIGHT_PX
                    top2 = _clamp(top2, canvas_y_top, canvas_y_end); bottom2 = _clamp(bottom2, canvas_y_top, canvas_y_end)
                    canvas.create_rectangle(x0_p2, top2, x1_p2, bottom2, fill=p2_color, outline="", tags=(f"bar_p2_{i}", "bar_p2", "bar"))
                    signed_v2 = saldos2[i] if i < len(saldos2) else 0.0
                    tx2 = (x0_p2 + x1_p2) / 2
                    ty2 = _clamp(top2 - label_offset, canvas_y_top + 4, canvas_y_end - 4)
                    color_v2 = "#d62728" if signed_v2 < 0 else ("#2ca02c" if signed_v2 > 0 else text_color)
                    canvas.create_text(tx2, ty2, text=format_euro(signed_v2, 0), fill=color_v2, font=("Arial", 8))
                    if per_anno:
                        canvas.create_text(x_center, y_base_tic, anchor="n", text=month_abbr_it.get(label, label), font=small_font, fill=text_color)
                    else:
                        key_full = keys_all[i] if i < len(keys_all) else None
                        if key_full:
                            parts = key_full.split('-')
                            if len(parts) == 3:
                                canvas.create_text(x_center, y_base_tic, anchor="n", text=f"{parts[2]}/{parts[1]}", font=small_font, fill=text_color)
                            else:
                                canvas.create_text(x_center, y_base_tic, anchor="n", text=labels_x[i], font=small_font, fill=text_color)
                        else:
                            canvas.create_text(x_center, y_base_tic, anchor="n", text=labels_x[i], font=small_font, fill=text_color)
            except Exception as e:
                print(f"Errore draw_chart:", e)
        def on_bar_double_click(event):
            item_id = canvas.find_closest(event.x, event.y)[0]
            tags = canvas.gettags(item_id)
            index = -1; period = None
            for tag in tags:
                if tag.startswith("bar_p1_"): index = int(tag.split("_")[2]); period = 1; break
                elif tag.startswith("bar_p2_"): index = int(tag.split("_")[2]); period = 2; break
            if index == -1 or index >= len(keys_all): return
            key_clicked = keys_all[index]
            categoria_choice = categoria_var.get()
            mese_nome_map = {'01': 'Gennaio', '02': 'Febbraio', '03': 'Marzo', '04': 'Aprile',
                             '05': 'Maggio', '06': 'Giugno', '07': 'Luglio', '08': 'Agosto',
                             '09': 'Settembre', '10': 'Ottobre', '11': 'Novembre', '12': 'Dicembre'}
            if per_anno:
                mese_key = str(int(key_clicked)).zfill(2)
                anno_val = a1 if period == 1 else a2
                nome_mese = mese_nome_map.get(mese_key, mese_key)
                data_filter = {"anno": str(anno_val), "mese": mese_key,
                               "categoria": categoria_choice if categoria_choice != "Tutte le Categorie" else None}
                title = f"Dettaglio Mensile - {nome_mese} {anno_val}"
            else:
                try:
                    anno_str, mese_str, giorno_str = key_clicked.split('-')
                except ValueError:
                    print(f"Errore nel parsing della chiave data: {key_clicked}"); return
                nome_mese = mese_nome_map.get(mese_str, mese_str)
                data_filter = {"anno": anno_str, "mese": mese_str, "giorno": giorno_str,
                               "categoria": categoria_choice if categoria_choice != "Tutte le Categorie" else None}
                title = f"Dettaglio Giornaliero - {giorno_str} {nome_mese} {anno_str}"
            if categoria_choice != "Tutte le Categorie":
                title += f" ({categoria_choice})"
            self._caller_popup = popup_grafico
            self.mostra_transazioni_popup(data_filter, title)
        update_data(initial_categoria)
        update_subtitle(initial_categoria)
        def finalizza_apertura():
            popup_grafico.update()
            draw_chart()
            popup_grafico.deiconify()
        popup_grafico.after(100, finalizza_apertura)
        resize_after_id = None
        def on_resize(event):
            nonlocal resize_after_id
            if resize_after_id: canvas.after_cancel(resize_after_id)
            resize_after_id = canvas.after(120, draw_chart)
        popup_grafico.bind("<Configure>", on_resize)
        canvas.bind("<Configure>", on_resize)
        def on_categoria_change(event=None):
            refresh_all()
        combobox_cat.bind("<<ComboboxSelected>>", on_categoria_change)
        mostra_future_var.trace_add("write", lambda *a: refresh_all())
        popup_grafico.bind("<Escape>", lambda e: popup_grafico.destroy())
        canvas.tag_bind("bar", "<Double-Button-1>", on_bar_double_click)
        for child in legenda_frame.winfo_children(): child.destroy()
        tk.Label(legenda_frame, text=f"P1 (Blu): {a1 if per_anno else f'{m1:02d}/{a1}'}", bg=bg_color, fg=p1_color, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(2, 8))
        tk.Label(legenda_frame, text=f"P2 (Arancione): {a2 if per_anno else f'{m2:02d}/{a2}'}", bg=bg_color, fg=p2_color, font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=(2, 8))
    except Exception as e:
        if 'popup_grafico' in locals() and popup_grafico.winfo_exists():
            popup_grafico.destroy()
        self.show_custom_warning("Errore Grafico", f"Si è verificato un errore critico durante la generazione del grafico: {e}")
        
