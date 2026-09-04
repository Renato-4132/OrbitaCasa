#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk

from moduli.modello_spesa import campo

def calcola_mancanti(self):
    import __main__ as _app
    ANNI_STORICO = 4
    MAX_VOLTE_ANNO = 2
    from datetime import datetime, timedelta
    if hasattr(self, '_mancanti_popup') and self._mancanti_popup and self._mancanti_popup.winfo_exists():
        self._mancanti_popup.lift()
        return
    def on_mancanti_close():
        popup.destroy()
        self._mancanti_popup = None
    popup = tk.Toplevel(bg=self.COLOR_TOPLEVEL)
    popup.transient(self)
    self._mancanti_popup = popup
    popup.protocol("WM_DELETE_WINDOW", on_mancanti_close)
    popup.bind("<Escape>", lambda e: on_mancanti_close())
    popup.withdraw()
    popup.title("Controllo Categorie Ricorrenti")
    w, h = 950, 620
    x = (popup.winfo_screenwidth() // 2) - (w // 2)
    y = (popup.winfo_screenheight() // 2) - (h // 2)
    popup.geometry(f"{w}x{h}+{x}+{y}")
    popup.minsize(w, h)
    popup.resizable(True, True)
    mesi = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu",
            "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
    oggi = datetime.today().date()
    def converti_data(d):
        if isinstance(d, str):
            try:
                return datetime.strptime(d, "%d-%m-%Y").date()
            except:
                return None
        elif isinstance(d, datetime):
            return d.date()
        return d
    anni_disponibili = sorted({
        converti_data(d).year for d in self.spese
        if converti_data(d)
    }, reverse=True)
    notebook = ttk.Notebook(popup)
    notebook.pack(fill="both", expand=True, padx=10, pady=(8, 0))
    def _add_tab(frame, ico_key, testo):
        img = self.icone_gui.get(ico_key)
        if img:
            notebook.add(frame, image=img, text=f" {testo} ", compound="left")
        else:
            notebook.add(frame, text=f" {testo} ")
    tab_mensili = ttk.Frame(notebook)
    tab_annuali = ttk.Frame(notebook)
    _add_tab(tab_mensili, "scadenze", "Mensili / Periodiche")
    _add_tab(tab_annuali, "calendario", "Annuali")
    anno_var = tk.StringVar(value=str(oggi.year))
    top_bar = ttk.Frame(tab_mensili, padding=10)
    top_bar.pack(fill="x")
    ttk.Label(top_bar, text="Anno di Analisi:").pack(side="left", padx=6)
    anno_combo = ttk.Combobox(top_bar, textvariable=anno_var,
                              values=[str(a) for a in anni_disponibili],
                              style="Border.TCombobox", state="readonly", width=6)
    anno_combo.pack(side="left", padx=6)
    anno_combo.bind("<<ComboboxSelected>>", lambda event: analizza())
    img_indietro_barra = self.icone_gui.get("reset")
    btn_indietro_barra = ttk.Label(top_bar, compound="left",
                                   image=img_indietro_barra,
                                   text=" 🔙" if not img_indietro_barra else "",
                                   background=self.COLOR_WIDGET_BG,
                                   foreground=self.TEXT_COLOR,
                                   cursor="hand2", padding=(5, 5))
    btn_indietro_barra.pack(side="left", padx=2)
    btn_indietro_barra.bind("<Button-1>", lambda e: [anno_var.set(str(oggi.year)), analizza()])
    ttk.Label(top_bar,
              text="Doppio clic → dettaglio movimenti  Clic destro → popola campi inserimento  "
                   "Clicca sull'intestazione per ordinare.  ✔/✖ = Mese con/senza Movimenti.",
              font=("Arial", 8, "italic"), foreground="gray").pack(side="right", padx=6)
    tree_container = tk.Frame(tab_mensili, bg=self.COLOR_TOPLEVEL)
    tree_container.pack(fill="both", expand=True, padx=0, pady=(0, 4))
    cols = ["Categoria", "Totale (€)", "Media (€)", "Cadenza"] + mesi
    self.tree = ttk.Treeview(tree_container, columns=cols, show='headings', selectmode='browse')
    scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
    self.tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    self.tree.pack(side="left", fill="both", expand=True)
    for col in cols:
        self.tree.heading(col,
                          text=col.replace(" (€)", ""),
                          anchor="center",
                          command=lambda c=col: self.treeview_sort_column(self.tree, c, False))
        if col == "Categoria":
            width_val = 150
        elif col in ("Totale (€)", "Media (€)"):
            width_val = 75
        elif col == "Cadenza":
            width_val = 100
        else:
            width_val = 35
        self.tree.column(col, width=width_val,
                         anchor="w" if col == "Categoria" else ("e" if col in ("Totale (€)", "Media (€)") else "center"))
    self.tree.tag_configure("mese_presente",      foreground="green",   font=("Arial", 8, "bold"))
    self.tree.tag_configure("mese_assente",        foreground="red")
    self.tree.tag_configure("cadenza_mensile",     background="#E6FFE6", foreground="#004C00")
    self.tree.tag_configure("cadenza_regolare",    background="#F0FFF0", foreground="#333333")
    self.tree.tag_configure("cadenza_bimestrale",  background="#FFFFE0", foreground="#CC9900")
    self.tree.tag_configure("cadenza_trimestrale", background="#FFF0E0", foreground="#FF6600")
    self.tree.tag_configure("cadenza_irregolare",  background="#FFEEEE", foreground="#CC0000")
    self.tree.tag_configure("intestazione",        background="#CCCCCC", foreground="black", font=("Arial", 10, "bold"))
    def analizza():
        dati_mensili = {}
        for i in self.tree.get_children():
            self.tree.delete(i)
        try:
            anno = int(anno_var.get())
        except ValueError:
            self.show_custom_warning("Errore", "Anno non valido.")
            return
        risultati = {}
        importi_categoria = {}
        conteggio_categoria = {}
        for d, sp in self.spese.items():
            dd = converti_data(d)
            if not dd or dd.year != anno:
                continue
            mese = dd.month
            for voce in sp:
                cat_raw = campo(voce, "categoria", "")
                if not cat_raw.strip():
                    continue
                cat = cat_raw.strip().title()
                importo = campo(voce, "importo", 0)
                tipo = campo(voce, "tipo", "Uscita").strip().title() or "Uscita"
                importo_netto = importo if tipo == "Entrata" else -importo
                importi_categoria[cat] = importi_categoria.get(cat, 0) + importo_netto
                conteggio_categoria[cat] = conteggio_categoria.get(cat, 0) + 1
                risultati.setdefault(cat, set()).add(mese)
                dati_mensili.setdefault(cat, {}).setdefault(mese, {"Entrata": 0, "Uscita": 0})
                if tipo == "Entrata":
                    dati_mensili[cat][mese]["Entrata"] += importo
                else:
                    dati_mensili[cat][mese]["Uscita"] += importo
        count = 0
        soglia_presenza = 1 if anno == oggi.year else 2
        for cat, mesi_presenti in sorted(risultati.items()):
            if len(mesi_presenti) < soglia_presenza:
                continue
            spesa_totale = importi_categoria.get(cat, 0)
            n_elementi = conteggio_categoria.get(cat, 1)
            media_spesa = spesa_totale / n_elementi
            segno = "+" if spesa_totale >= 0 else "-"
            spesa_totale_abs = abs(spesa_totale)
            media_spesa_abs = abs(media_spesa)
            sorted_months = sorted(list(mesi_presenti))
            avg_interval = 0
            if len(sorted_months) > 1:
                intervals = [(sorted_months[i] - sorted_months[i-1]) for i in range(1, len(sorted_months))]
                avg_interval = sum(intervals) / len(intervals)
            if len(mesi_presenti) == 12:
                cadenza = "Mensile";       tag_riga = "cadenza_mensile"
            elif 0.8 <= avg_interval <= 1.2:
                cadenza = "Mensile Reg.";  tag_riga = "cadenza_regolare"
            elif 1.5 <= avg_interval <= 2.5:
                cadenza = "Bimestrale";    tag_riga = "cadenza_bimestrale"
            elif 2.5 < avg_interval <= 3.5:
                cadenza = "Trimestrale";   tag_riga = "cadenza_trimestrale"
            else:
                cadenza = "Irregolare";    tag_riga = "cadenza_irregolare"
            valori_riga = [cat, f"€ {segno}{_app._fmt_it(spesa_totale_abs)}", f"€ {segno}{_app._fmt_it(media_spesa_abs)}", cadenza]
            for mese_idx in range(1, 13):
                simbolo = "✔" if mese_idx in mesi_presenti else "✖"
                if mese_idx == oggi.month and anno == oggi.year:
                    simbolo = f"[{simbolo}]"
                valori_riga.append(simbolo)
            self.tree.insert("", "end", iid=cat, values=valori_riga, tags=(tag_riga,))
            count += 1
        if count == 0:
            self.tree.insert("", "end",
                             values=("Nessuna categoria ricorrente trovata.", "", "", ""),
                             tags=("intestazione",))
    def on_tree_select(event):
        selected_item = self.tree.focus()
        if not selected_item:
            return
        valori = self.tree.item(selected_item, 'values')
        categoria_selezionata = valori[0]
        if categoria_selezionata.startswith("Nessuna"):
            return
        anno_selezionato = anno_var.get()
        data_filter = {"anno": anno_selezionato, "mese": None,
                       "categoria": categoria_selezionata, "tipo": None}
        title = f"Movimenti Ricorrenti: {categoria_selezionata} ({anno_selezionato})"
        self.mostra_transazioni_popup(data_filter, title)
    def popola_form(event):
        item = self.tree.identify_row(event.y)
        if not item:
            return
        valori = self.tree.item(item, "values")
        categoria = str(valori[0]).strip()
        if categoria.startswith("Nessuna"):
            return
        cat_match = next(
            (c for c in self.categorie if c.strip().lower() == categoria.lower()), None)
        if cat_match:
            self.cat_sel.set(cat_match)
            self.cat_menu.set(cat_match)
            self.on_categoria_changed(manuale=False)
        try:
            media_str = str(valori[2]).replace("€", "").replace("+", "").replace("-", "").strip()
            media_val = _app._parse_it_float(media_str)
            self.imp_entry.delete(0, tk.END)
            self.imp_entry.insert(0, f"{media_val:.2f}".replace(".", ","))
        except (ValueError, IndexError):
            pass
        tipo = self.categorie_tipi.get(cat_match or categoria, "Uscita")
        if self.tipo_spesa_var.get() != tipo:
            self.toggle_tipo_spesa()
        self.desc_entry.delete(0, tk.END)
        on_mancanti_close()
    self.tree.bind("<Double-1>", on_tree_select)
    self.tree.bind("<Button-3>", popola_form)
    legenda_frame = ttk.Frame(tab_mensili, padding=(6, 4, 6, 4))
    legenda_frame.pack(fill="x")
    ttk.Label(legenda_frame, text="Legenda Cadenza: ", font=("Arial", 8, "bold")).pack(side="left", padx=(0, 10))
    for testo, alias in [("Mensile", "mensile"), ("Regolare", "regolare"),
                          ("Bimestrale", "bimestrale"), ("Trimestrale", "trimestrale"),
                          ("Irregolare", "irregolare")]:
        ttk.Label(legenda_frame, text=testo,
                  style=f"Legenda.{alias}.TLabel").pack(side="left", padx=5)
    ttk.Label(legenda_frame, text=" | Simboli Mese: ", font=("Arial", 8, "bold")).pack(side="left", padx=(10, 10))
    ttk.Label(legenda_frame, text="✔ Presente", foreground="green", font=("Arial", 8, "bold")).pack(side="left", padx=5)
    ttk.Label(legenda_frame, text="✖ Assente",  foreground="red").pack(side="left", padx=5)
    ttk.Label(legenda_frame, text="[ ] Mese Corrente", foreground="#555555").pack(side="left", padx=5)
    top_bar2 = ttk.Frame(tab_annuali, padding=10)
    top_bar2.pack(fill="x")
    ttk.Label(top_bar2,
              text=f"Voci che compaiono ogni anno (≥ 2 anni su {ANNI_STORICO}) — "
                   f"confronto con {oggi.year}   |   "
                   "Doppio clic → storico movimenti   Clic destro → popola campi inserimento",
              font=("Arial", 8, "italic"), foreground="gray").pack(side="left", padx=6)
    tree_ann_container = tk.Frame(tab_annuali, bg=self.COLOR_TOPLEVEL)
    tree_ann_container.pack(fill="both", expand=True, padx=0, pady=(0, 4))
    cols_ann = ["Categoria", "Mese Atteso", "Media (€)", "Anni Rilevati", str(oggi.year)]
    tree_annuali = ttk.Treeview(tree_ann_container, columns=cols_ann, show='headings', selectmode='browse')
    sb_ann = ttk.Scrollbar(tree_ann_container, orient="vertical", command=tree_annuali.yview)
    tree_annuali.configure(yscrollcommand=sb_ann.set)
    sb_ann.pack(side="right", fill="y")
    tree_annuali.pack(side="left", fill="both", expand=True)
    for col in cols_ann:
        tree_annuali.heading(col, text=str(col), anchor="center",
                             command=lambda c=col: self.treeview_sort_column(tree_annuali, c, False))
    tree_annuali.column("Categoria",     width=220, anchor="w")
    tree_annuali.column("Mese Atteso",   width=90,  anchor="center")
    tree_annuali.column("Media (€)",     width=90,  anchor="e")
    tree_annuali.column("Anni Rilevati", width=90,  anchor="center")
    tree_annuali.column(str(oggi.year),  width=80,  anchor="center")
    tree_annuali.tag_configure("ann_presente", foreground=self.COLOR_GREEN_SMOOTH)
    tree_annuali.tag_configure("ann_mancante", foreground=self.COLOR_RED_SMOOTH, font=("Arial", 9, "bold"))
    tree_annuali.tag_configure("ann_futuro",   foreground="#FFAA00")
    def analizza_annuali():
        for i in tree_annuali.get_children():
            tree_annuali.delete(i)
        anno_corrente = oggi.year
        storico = {}
        importi_storico = {}
        presenti_corrente = {}
        occorrenze_per_anno = {}
        for d, sp in self.spese.items():
            dd = converti_data(d)
            if not dd:
                continue
            anni_fa = anno_corrente - dd.year
            if anni_fa == 0:
                for voce in sp:
                    cat_raw = campo(voce, "categoria", "")
                    if not cat_raw.strip():
                        continue
                    cat = cat_raw.strip().title()
                    presenti_corrente.setdefault(cat, set()).add(dd.month)
            elif 1 <= anni_fa <= ANNI_STORICO:
                for voce in sp:
                    cat_raw = campo(voce, "categoria", "")
                    if not cat_raw.strip():
                        continue
                    cat = cat_raw.strip().title()
                    importo = campo(voce, "importo", 0)
                    tipo_voce = campo(voce, "tipo", "Uscita").strip().title() or "Uscita"
                    importo_netto = importo if tipo_voce == "Entrata" else -importo
                    chiave = (cat, dd.month)
                    storico.setdefault(chiave, set()).add(dd.year)
                    importi_storico.setdefault(chiave, []).append(importo_netto)
                    occorrenze_per_anno.setdefault(cat, {}).setdefault(dd.year, 0)
                    occorrenze_per_anno[cat][dd.year] += 1
        anni_per_cat = {}
        for (cat_k, mese_k), anni_set_k in storico.items():
            anni_per_cat.setdefault(cat_k, set()).update(anni_set_k)
        righe = []
        già_inserite = set()
        for (cat, mese), anni_set in storico.items():
            if len(anni_set) < 2:
                continue
            max_occ = max(occorrenze_per_anno.get(cat, {0: 1}).values())
            if max_occ > MAX_VOLTE_ANNO:
                continue
            if (cat, mese) in già_inserite:
                continue
            già_inserite.add((cat, mese))
            importi = importi_storico.get((cat, mese), [0])
            media = sum(importi) / len(importi) if importi else 0
            presente = mese in presenti_corrente.get(cat, set())
            righe.append((cat, mese, media, len(anni_per_cat.get(cat, set())), presente))
        righe.sort(key=lambda x: (x[1], x[0]))
        mesi_nomi = ["Gen","Feb","Mar","Apr","Mag","Giu","Lug","Ago","Set","Ott","Nov","Dic"]
        for cat, mese, media, n_anni, presente in righe:
            if presente:
                tag = "ann_presente"; simbolo = "✔"
            elif mese > oggi.month:
                tag = "ann_futuro";   simbolo = "—"
            else:
                tag = "ann_mancante"; simbolo = "✖"
            segno = "+" if media >= 0 else "-"
            tree_annuali.insert("", "end",
                                values=(cat, mesi_nomi[mese - 1], f"€ {segno}{_app._fmt_it(abs(media))}", n_anni, simbolo),
                                tags=(tag,))
        if not tree_annuali.get_children():
            tree_annuali.insert("", "end",
                                values=("Nessuna ricorrenza annuale rilevata.", "", "", "", ""),
                                tags=())
    def on_ann_select(event):
        item = tree_annuali.focus()
        if not item:
            return
        valori = tree_annuali.item(item, "values")
        cat = str(valori[0]).strip()
        if cat.startswith("Nessuna"):
            return
        data_filter = {"anno": None, "mese": None, "categoria": cat, "tipo": None}
        self.mostra_transazioni_popup(data_filter, f"Storico Annuale: {cat}")
    def popola_form_ann(event):
        item = tree_annuali.identify_row(event.y)
        if not item:
            return
        valori = tree_annuali.item(item, "values")
        cat = str(valori[0]).strip()
        if cat.startswith("Nessuna"):
            return
        cat_match = next(
            (c for c in self.categorie if c.strip().lower() == cat.lower()), None)
        if cat_match:
            self.cat_sel.set(cat_match)
            self.cat_menu.set(cat_match)
            self.on_categoria_changed(manuale=False)
        try:
            media_str = str(valori[2]).replace("€", "").replace("+", "").replace("-", "").strip()
            media_val = _app._parse_it_float(media_str)
            self.imp_entry.delete(0, tk.END)
            self.imp_entry.insert(0, f"{media_val:.2f}".replace(".", ","))
        except (ValueError, IndexError):
            pass
        tipo = self.categorie_tipi.get(cat_match or cat, "Uscita")
        if self.tipo_spesa_var.get() != tipo:
            self.toggle_tipo_spesa()
        self.desc_entry.delete(0, tk.END)
        on_mancanti_close()
    tree_annuali.bind("<Double-1>", on_ann_select)
    tree_annuali.bind("<Button-3>", popola_form_ann)
    legenda_ann = ttk.Frame(tab_annuali, padding=(6, 4, 6, 4))
    legenda_ann.pack(fill="x")
    ttk.Label(legenda_ann, text="✔ Già registrata quest'anno",
              foreground=self.COLOR_GREEN_SMOOTH, font=("Arial", 8, "bold")).pack(side="left", padx=8)
    ttk.Label(legenda_ann, text="✖ Mancante (mese già passato)",
              foreground=self.COLOR_RED_SMOOTH, font=("Arial", 8, "bold")).pack(side="left", padx=8)
    ttk.Label(legenda_ann, text="— Non ancora registrata (mese futuro)",
              foreground="#FFAA00", font=("Arial", 8)).pack(side="left", padx=8)
    bottom_buttons = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    bottom_buttons.pack(pady=8)
    self.btn_chiudi_popup_generico = ttk.Label(
        bottom_buttons,
        image=self.icone_gui.get("chiudi"),
        text=" Chiudi",
        compound="left",
        cursor="hand2",
        background=self.COLOR_WIDGET_BG,
        font=("Arial", 9, "bold")
    )
    self.btn_chiudi_popup_generico.image = self.icone_gui.get("chiudi")
    self.btn_chiudi_popup_generico.pack(side="right", padx=10)
    self.btn_chiudi_popup_generico.bind("<Button-1>", lambda e: popup.destroy())
    analizza()
    analizza_annuali()
    notebook.bind("<<NotebookTabChanged>>",
                  lambda e: analizza_annuali() if notebook.index("current") == 1 else None)
    popup.deiconify()

def get_lista_categorie_mancanti(self):
    import __main__ as _app
    SOGLIA_CHECKOUT = _app.SOGLIA_CHECKOUT

    from datetime import datetime
    oggi = datetime.today().date()
    def converti_data(d):
        if isinstance(d, str):
            try:
                return datetime.strptime(d, "%d-%m-%Y").date()
            except:
                return None
        elif isinstance(d, datetime):
            return d.date()
        return d
    categorie_base = {cat.title() for cat in self.categorie if cat}
    presenti_questo_mese = set()
    conteggio_storico = {}
    MESI_INDIETRO = 12 
    for d, sp in self.spese.items():
        dd = converti_data(d)
        if not dd: 
            continue
        diff_mesi = (oggi.year - dd.year) * 12 + (oggi.month - dd.month)
        if diff_mesi == 0:
            for voce in sp:
                cat_raw = campo(voce, "categoria", "")
                if cat_raw.strip():
                    presenti_questo_mese.add(cat_raw.strip().title())
        elif 1 <= diff_mesi <= MESI_INDIETRO:
            viste_in_data = set()
            for voce in sp:
                cat_raw = campo(voce, "categoria", "")
                if cat_raw.strip():
                    cat = cat_raw.strip().title()
                    if cat in categorie_base and cat not in viste_in_data:
                        conteggio_storico[cat] = conteggio_storico.get(cat, 0) + 1
                        viste_in_data.add(cat)
    mancanti = [cat for cat in categorie_base 
                if conteggio_storico.get(cat, 0) >= SOGLIA_CHECKOUT and cat not in presenti_questo_mese]
    return sorted(mancanti)
