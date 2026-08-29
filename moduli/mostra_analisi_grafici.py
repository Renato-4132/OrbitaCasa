#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import datetime
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, TclError
from moduli.modello_spesa import campo

def _fmt_it(v, spec=",.2f"):
    s = format(v, spec)
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def mostra_analisi_grafici(self):
    def bind_popup(canvas, item, filter_data, title):
        canvas.tag_bind(item, "<Double-1>", 
                        lambda e: self.mostra_transazioni_popup(filter_data, title))
    def disegna_barre(canvas, dati, colori, mostra_anno=False, mostra_tipo=False, centro=False):
        canvas.delete("all")
        canvas.update_idletasks()
        larghezza = canvas.winfo_width()
        altezza = canvas.winfo_height()
        margine_h = 20   # margine laterale (sinistra/destra) - piccolo per usare lo spazio ai lati
        margine_v = 55   # margine verticale (sopra/sotto) - spazio per le etichette sotto le barre
        if isinstance(dati, dict):
            elementi = list(dati.items())
        else:
            elementi = dati
        max_val = max(abs(val) for _, val in elementi) if elementi else 1
        scala = (altezza - margine_v * 2) / (max_val * 1.5) if max_val > 0 else 0
        n = max(len(elementi), 1)
        PAIR_GAP = 5    # spazio (px) tra le due barre della stessa coppia Entrata/Uscita
        GROUP_GAP = 10  # spazio (px) tra una coppia e la successiva (anno diverso)
        numero_gruppi = max((n + 1) // 2, 1)
        numero_pair_gap = n // 2          # una per ogni coppia completa
        numero_group_gap = max(numero_gruppi - 1, 0)
        spazio_extra = numero_pair_gap * PAIR_GAP + numero_group_gap * GROUP_GAP
        larghezza_barra = (larghezza - margine_h * 2 - spazio_extra) / n
        y_base = altezza // 2 if centro else altezza - margine_v
        anno_selezionato = canvas.selettore_rif.get()
        mesi_abbr = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
        nomi_completi_mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", 
                              "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
        x_corrente = margine_h
        for i, (etichetta, valore) in enumerate(elementi):
            x0 = x_corrente
            x1 = x0 + larghezza_barra
            x_corrente = x1 + (PAIR_GAP if i % 2 == 0 else GROUP_GAP)
            colore = colori.get(etichetta, "gray")
            parts = etichetta.split(" ")
            tipo = parts[-1] if mostra_tipo else None
            if anno_selezionato == "Tutti":
                anno_filter = parts[0]
                mese_filter = None
                periodo_title = f"l'anno {anno_filter}"
            else:
                anno_filter = anno_selezionato
                nome_mese_abbr = parts[0]
                try:
                    mese_index = mesi_abbr.index(nome_mese_abbr)
                    mese_filter = mese_index + 1
                    nome_mese_completo = nomi_completi_mesi[mese_index]
                except ValueError:
                    mese_filter = None
                    nome_mese_completo = nome_mese_abbr
                periodo_title = f"{nome_mese_completo} {anno_filter}"
            filter_data = {"anno": anno_filter, "mese": mese_filter, "tipo": tipo}
            title_text = f"Transazioni {tipo} per {periodo_title}"
            if valore >= 0:
                y1 = y_base - valore * scala
                rect = canvas.create_rectangle(x0, y_base, x1, y1, fill=colore)
                canvas.create_text((x0 + x1) / 2, y1 - 10, text=f"{_fmt_it(valore)}", font=("Arial", 8), fill=self.TEXT_COLOR)
            else:
                y1 = y_base + abs(valore) * scala
                rect = canvas.create_rectangle(x0, y_base, x1, y1, fill=colore)
                canvas.create_text((x0 + x1) / 2, y1 + 10, text=f"{_fmt_it(valore)}", font=("Arial", 8), fill=self.TEXT_COLOR)
            bind_popup(canvas, rect, filter_data, title_text)
            if mostra_tipo and " " in etichetta:
                tipo_label = etichetta.split(" ")[1]
                canvas.create_text((x0 + x1) / 2, y_base + 15, text=tipo_label, font=("Arial", 8), fill=self.TEXT_COLOR)
            if not mostra_anno and " " in etichetta:
                mese_label = etichetta.split(" ")[0]
                canvas.create_text((x0 + x1) / 2, y_base + 30, text=mese_label, font=("Arial", 8), fill=self.TEXT_COLOR)
            elif mostra_anno:
                anno_label = etichetta.split(" ")[0] if " " in etichetta else etichetta
                canvas.create_text((x0 + x1) / 2, y_base + 30, text=anno_label, font=("Arial", 8), fill=self.TEXT_COLOR)
    def disegna_barre_categorie(canvas, dati, colori):
        if hasattr(canvas, "tooltip") and canvas.tooltip:
            canvas.tooltip.destroy()
            canvas.tooltip = None
        canvas.delete("all")
        canvas.update_idletasks()
        LARGHEZZA_BARRA_FISSA = 80
        margine_laterale = 50
        margine_inferiore = 130  
        margine_superiore = 60
        larghezza_visualizzata = canvas.winfo_width()
        altezza = canvas.winfo_height()
        if larghezza_visualizzata < 10:
            canvas.after(100, lambda: disegna_barre_categorie(canvas, dati, colori))
            return
        y_base = altezza - margine_inferiore
        totale = sum(val for _, val in dati) if dati else 1
        max_val = max(val for _, val in dati) if dati else 1
        spazio_utile = altezza - margine_inferiore - margine_superiore
        scala = spazio_utile / (max_val * 1.2) if max_val > 0 else 0
        numero_barre = max(len(dati), 1)
        larghezza_contenuto = margine_laterale * 2 + numero_barre * LARGHEZZA_BARRA_FISSA
        x_offset = max(0, (larghezza_visualizzata - larghezza_contenuto) // 2)
        anno_selezionato = canvas.anno_corrente
        for i, (categoria, valore) in enumerate(dati):
            x0 = x_offset + margine_laterale + i * LARGHEZZA_BARRA_FISSA
            x1 = x0 + LARGHEZZA_BARRA_FISSA * 0.6
            altezza_pixel = valore * scala
            if valore > 0 and altezza_pixel < 4:
                altezza_pixel = 4
            y1 = y_base - altezza_pixel
            colore = colori.get(categoria, "#888888")
            rect = canvas.create_rectangle(x0, y_base, x1, y1, fill=colore)
            filter_data = {"anno": anno_selezionato, "categoria": categoria, "tipo": "Uscita"}
            title_text = f"Movimenti Categoria '{categoria}' ({anno_selezionato})"
            bind_popup(canvas, rect, filter_data, title_text)
            percentuale = (valore / totale) * 100
            canvas.create_text((x0 + x1) / 2, y1 - 12, text=f"{_fmt_it(valore)}", font=("Arial", 9), fill=self.TEXT_COLOR)
            canvas.create_text((x0 + x1) / 2, y1 - 26, text=f"{percentuale:.1f}%", font=("Arial", 8), fill="gray")
            canvas.create_text(
                (x0 + x1) / 2, 
                y_base + 10, 
                text=categoria, 
                font=("Arial", 9),
                angle=45,
                anchor="ne",
                fill=colore
            )
            def show_tooltip(event, text=categoria):
                if hasattr(canvas, "tooltip") and canvas.tooltip:
                    canvas.tooltip.destroy()
                    canvas.tooltip = None
                canvas.tooltip = tk.Toplevel(canvas)
                canvas.tooltip.wm_overrideredirect(True)
                canvas.tooltip.config(
                    highlightthickness=1,
                    highlightbackground=self.COLOR_HIGHLIGHT,
                    bg=self.COLOR_TOOLTIP
                )
                try:
                    canvas.tooltip.wm_geometry(f"+{event.x_root + 10}+{event.y_root + 10}")
                except: pass
                label = ttk.Label(canvas.tooltip, text=text, style="Tooltip.TLabel")
                label.pack(ipadx=4)
            def hide_tooltip(event):
                if hasattr(canvas, "tooltip") and canvas.tooltip:
                    canvas.tooltip.destroy()
                    canvas.tooltip = None
            canvas.tag_bind(rect, "<Enter>", show_tooltip)
            canvas.tag_bind(rect, "<Leave>", hide_tooltip)
        lbl_totale = tk.Label(canvas, text=f"Totale uscite: € {_fmt_it(totale)}", font=("Arial", 10, "bold"), bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR, padx=5)
        win_totale = canvas.create_window(10, altezza - 25, window=lbl_totale, anchor="w", tags="fissato")
        def fissa_elementi(event=None):
            x_visibile = canvas.canvasx(10)
            canvas.coords("fissato", x_visibile, altezza - 25)
            canvas.tag_raise("fissato")
        canvas.bind("<Configure>", fissa_elementi)
        scrollbar_h.config(command=lambda *args: [canvas.xview(*args), fissa_elementi()])
        canvas.config(scrollregion=(0, 0, larghezza_contenuto, altezza))
        fissa_elementi()
        
    def aggiorna_legenda_treeview(tree, dati, colori):
            for item in tree.get_children():
                    tree.delete(item)
            dati_ordinati = sorted(dati, key=lambda x: x[1], reverse=True)
            for cat, val in dati_ordinati:
                    colore = colori.get(cat, "#888888")
                    r = int(colore[1:3], 16)
                    g = int(colore[3:5], 16)
                    b = int(colore[5:7], 16)
                    luminosita = (0.2126 * r + 0.7152 * g + 0.0722 * b)
                    colore_testo = "black" if luminosita > 150 else "white"
                    tag_name = cat.replace(" ", "_").replace("(", "").replace(")", "")
                    tree.insert("", "end", values=(cat, f"€ {_fmt_it(val)}"), tags=(tag_name,))
                    try:
                            tree.tag_configure(tag_name, background=colore, foreground=colore_testo)
                    except TclError:
                            pass
    def disegna_barre_saldo(canvas, dati):
        nomi_completi_mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", 
                              "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
        canvas.delete("all")
        canvas.update_idletasks()
        larghezza = canvas.winfo_width()
        altezza = canvas.winfo_height()
        margine = 50
        mesi_ordinati_abbr = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
        chiavi = mesi_ordinati_abbr if set(mesi_ordinati_abbr).issubset(dati.keys()) else list(dati.keys())
        max_val = max(abs(dati[k]) for k in chiavi) if dati else 1
        scala = (altezza - margine * 2) / (max_val * 1.5) if max_val > 0 else 0
        larghezza_barra = (larghezza - margine * 2) // max(len(chiavi), 1)
        y_base = altezza - margine
        anno_selezionato_selettore = canvas.selettore_rif.get()
        for i, etichetta in enumerate(chiavi):
                valore = dati.get(etichetta, 0)
                x0 = margine + i * larghezza_barra
                x1 = x0 + larghezza_barra * 0.6
                if abs(valore) < 0.01:
                        y1 = y_base
                else:
                        y1 = y_base - abs(valore) * scala
                colore = "green" if valore >= 0 else "red"
                segno = "+" if valore >= 0 else "−"
                rect = canvas.create_rectangle(x0, y_base, x1, y1, fill=colore)
                mese_num = None
                anno_filtro = anno_selezionato_selettore
                title_text_base = "Tutte le transazioni"
                nome_mese_per_titolo = etichetta
                if anno_selezionato_selettore == "Tutti":
                        anno_filtro = etichetta
                        title_text = f"{title_text_base} per l'anno {anno_filtro}"
                else:
                        if etichetta in mesi_ordinati_abbr:
                                try:
                                    mese_index = mesi_ordinati_abbr.index(etichetta)
                                    mese_num = mese_index + 1
                                    nome_mese_per_titolo = nomi_completi_mesi[mese_index]
                                except ValueError:
                                    pass
                        title_text = f"{title_text_base} per {nome_mese_per_titolo} {anno_filtro}" 
                filter_data = {"anno": anno_filtro, "mese": mese_num}
                bind_popup(canvas, rect, filter_data, title_text)
                testo_y = y1 - 10
                valore_formattato = f"{_fmt_it(abs(valore))}"
                canvas.create_text(
                        (x0 + x1) / 2,
                        testo_y,
                        text=f"{segno}{valore_formattato}",
                        font=("Arial", 9),
                        fill=self.TEXT_COLOR
                )
                canvas.create_text((x0 + x1) / 2, y_base + 20, text=etichetta, font=("Arial", 9), fill=self.TEXT_COLOR)

    def on_legenda_double_click(event):
        item_id = self.tree_legenda.selection()
        if not item_id:
            return
        valori = self.tree_legenda.item(item_id[0], "values")
        categoria = valori[0]
        anno = selettore_anno2.get()
        filter_data = {"anno": anno, "categoria": categoria, "tipo": "Uscita"}
        title_text = f"Movimenti Categoria '{categoria}' ({anno})"
        self.mostra_transazioni_popup(filter_data, title_text)
                
    def aggiorna_tab3(event=None):
        selezione = selettore_anno3.get()
        entrate = defaultdict(float)
        uscite = defaultdict(float)
        for data, voci in self.spese.items():
            anno = data.year
            mese = data.month
            if selezione != "Tutti" and str(anno) != selezione:
                continue
            for voce in voci:
                if not includi_futuri_graf_var.get() and data > datetime.date.today():
                    continue
                tipo = campo(voce, "tipo", "").strip().lower()
                importo = campo(voce, "importo", 0.0)
                chiave = str(anno) if selezione == "Tutti" else mese
                if tipo == "entrata":
                    entrate[chiave] += importo
                elif tipo == "uscita":
                    uscite[chiave] += importo
        total_entrate = sum(entrate.values())
        total_uscite = sum(uscite.values())
        saldo_totale = total_entrate - total_uscite
        self.lbl_entrate_tab3.config(text=f"Entrate: € {_fmt_it(total_entrate)}")
        self.lbl_uscite_tab3.config(text=f"Uscite: € {_fmt_it(total_uscite)}")
        if saldo_totale >= 0:
            self.lbl_saldo_tab3.config(text=f"Saldo: € {_fmt_it(saldo_totale)}", style="GSaldoPositivo.TLabel")
        else:
            self.lbl_saldo_tab3.config(text=f"Saldo: € {_fmt_it(saldo_totale)}", style="GSaldoNegativo.TLabel")
        saldo_per_grafico = defaultdict(float)
        for chiave, importo in entrate.items():
            saldo_per_grafico[chiave] += importo
        for chiave, importo in uscite.items():
            saldo_per_grafico[chiave] -= importo
        if selezione == "Tutti":
            grafico = {str(a): saldo_per_grafico.get(a, 0) for a in sorted(saldo_per_grafico)}
        else:
            mesi = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
            grafico = {mesi[m - 1]: saldo_per_grafico.get(m, 0) for m in range(1, 13)}
        canvas3.dati_cache = grafico
        ridisegna_tab3()
    def ridisegna_tab3(event=None):
        if hasattr(canvas3, "dati_cache"):
            disegna_barre_saldo(canvas3, canvas3.dati_cache)
    def aggiorna_tab2(event=None):
        anno = selettore_anno2.get()
        canvas2.anno_corrente = anno
        categories = defaultdict(float)
        for data, voci in self.spese.items():
            if anno == "Tutti" or str(data.year) == anno:
                for voce in voci:
                    if not includi_futuri_graf_var.get() and data > datetime.date.today():
                        continue
                    if campo(voce, "tipo", "").strip().lower() == "uscita":
                        categories[campo(voce, "categoria", "")] += float(campo(voce, "importo", 0.0))
        tutte_categorie = sorted(categories.items(), key=lambda x: x[1], reverse=True)
        colore = {}
        if not hasattr(self, '_colori_categorie'):
            self._colori_categorie = {}
        for cat, _ in tutte_categorie:
            if cat not in self._colori_categorie:
                self._colori_categorie[cat] = f'#{random.randint(50,200):02x}{random.randint(50,200):02x}{random.randint(50,200):02x}'
        colore = self._colori_categorie
        canvas2.tutte_categorie = tutte_categorie
        canvas2.colori = colore
        canvas2.dati_cache = tutte_categorie
        canvas2.colori_cache = colore
        ridisegna_tab2()
        aggiorna_legenda_treeview(self.tree_legenda, tutte_categorie, colore)
    def ridisegna_tab2(event=None):
        if hasattr(canvas2, "dati_cache"):
            canvas2.delete("all")
            canvas2.update_idletasks()
            disegna_barre_categorie(canvas2, canvas2.dati_cache, canvas2.colori_cache)
    def aggiorna_tab1(event=None):
        anno_selezionato = selettore_anno1.get()
        entrate = defaultdict(float)
        uscite = defaultdict(float)
        for data, voci in self.spese.items():
            anno = data.year
            mese = data.month
            if anno_selezionato != "Tutti" and str(anno) != anno_selezionato:
                continue
            for voce in voci:
                if not includi_futuri_graf_var.get() and data > datetime.date.today():
                    continue
                tipo = campo(voce, "tipo", "").strip().lower()
                importo = campo(voce, "importo", 0.0)
                chiave = str(anno) if anno_selezionato == "Tutti" else mese
                if tipo == "entrata":
                    entrate[chiave] += importo
                elif tipo == "uscita":
                    uscite[chiave] += importo
        total_entrate = sum(entrate.values())
        total_uscite = sum(uscite.values())
        saldo = total_entrate - total_uscite
        lbl_entrate.config(text=f"Entrate: € {_fmt_it(total_entrate)}")
        lbl_uscite.config(text=f"Uscite: € {_fmt_it(total_uscite)}")
        if saldo >= 0:
            lbl_saldo_tab1.config(text=f"Saldo: € {_fmt_it(saldo)}", style="GSaldoPositivo.TLabel")
        else:
            lbl_saldo_tab1.config(text=f"Saldo: € {_fmt_it(saldo)}", style="GSaldoNegativo.TLabel")
        grafico = {}
        colore = {}
        if anno_selezionato == "Tutti":
            for anno in sorted(set(entrate.keys()) | set(uscite.keys())):
                grafico[f"{anno} Entrata"] = entrate[anno]
                grafico[f"{anno} Uscita"] = uscite[anno]
                colore[f"{anno} Entrata"] = "green"
                colore[f"{anno} Uscita"] = "red"
        else:
            mesi = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
            for m in range(1, 13):
                nome_mese = mesi[m - 1]
                grafico[f"{nome_mese} Entrata"] = entrate.get(m, 0)
                grafico[f"{nome_mese} Uscita"] = uscite.get(m, 0)
                colore[f"{nome_mese} Entrata"] = "green"
                colore[f"{nome_mese} Uscita"] = "red"
        canvas1.dati_cache = grafico
        canvas1.colori_cache = colore
        canvas1.mostra_anno_cache = (anno_selezionato == "Tutti")
        ridisegna_tab1()
    def ridisegna_tab1(event=None):
        if hasattr(canvas1, "dati_cache"):
            disegna_barre(canvas1, canvas1.dati_cache, canvas1.colori_cache, 
                          mostra_anno=canvas1.mostra_anno_cache, mostra_tipo=True, centro=False)
    larghezza_finestra = 1230
    altezza_finestra = 600
    larghezza_schermo = self.winfo_screenwidth()
    altezza_schermo = self.winfo_screenheight()
    x = (larghezza_schermo // 2) - (larghezza_finestra // 2)
    y = (altezza_schermo // 2) - (altezza_finestra // 2)
    self.grafico_analisi_popup = tk.Toplevel(self)
    self.grafico_analisi_popup.withdraw()
    self.grafico_analisi_popup.transient(self)
    self.grafico_analisi_popup.configure(bg=self.COLOR_TOPLEVEL)
    self.grafico_analisi_popup.title("Grafico Analisi Movimenti")
    self.grafico_analisi_popup.geometry(f"{larghezza_finestra}x{altezza_finestra}+{x}+{y}")
    self.grafico_analisi_popup.minsize(larghezza_finestra, altezza_finestra)
    self.grafico_analisi_popup.bind("<Escape>", lambda e: self.grafico_analisi_popup.destroy())
    notebook = ttk.Notebook(self.grafico_analisi_popup)
    notebook.pack(fill="both", expand=True, padx=10, pady=(10, 5))
    def _add_tab(frame, ico_key, testo):
        img = self.icone_gui.get(ico_key)
        if img:
            notebook.add(frame, image=img, text=f" {testo} ", compound="left")
        else:
            notebook.add(frame, text=f" {testo} ")
    anni = sorted({d.year for d in self.spese.keys()}, reverse=True)
    anno_corrente = str(datetime.date.today().year)
    tab1 = ttk.Frame(notebook)
    _add_tab(tab1, "grafico_linea", "Entrate/Uscite")
    frame_totali = ttk.Frame(tab1)
    frame_totali.pack(side="bottom", pady=10)
    lbl_entrate = ttk.Label(frame_totali, text="Entrate: € 0.00", style="GSaldoPositivo.TLabel")
    lbl_entrate.pack(side="left", padx=10)
    lbl_uscite = ttk.Label(frame_totali, text="Uscite: € 0.00", style="GSaldoNegativo.TLabel")
    lbl_uscite.pack(side="left", padx=10)
    lbl_saldo_tab1 = ttk.Label(frame_totali, text="Saldo: € 0.00", style="GSaldo.TLabel")
    lbl_saldo_tab1.pack(side="left", padx=10)
    img_mouse = self.icone_gui.get("mouse")
    lbl_periodo = tk.Label(
            tab1, 
            text="Doppio clic → Mostra Dettaglio ", 
            image=img_mouse,
            compound="right",
            background=self.COLOR_WIDGET_BG, 
            foreground="gray", 
            font=("Arial", 9, "italic"),
    )
    lbl_periodo.image = img_mouse
    lbl_periodo.pack(side="top", padx=10)
    selettore_anno1 = ttk.Combobox(tab1, values=["Tutti"] + [str(a) for a in anni], style="Border.TCombobox", state='readonly')
    selettore_anno1.set("Tutti")
    selettore_anno1.pack(pady=10)
    selettore_anno1.bind("<<ComboboxSelected>>", aggiorna_tab1)
    canvas1 = tk.Canvas(tab1, bg=self.COLOR_WIDGET_BG)
    canvas1.pack(fill="both", expand=True, padx=10, pady=10)
    canvas1.selettore_rif = selettore_anno1
    canvas1.bind("<Configure>", ridisegna_tab1)
    tab2 = ttk.Frame(notebook)
    tab2.grid_columnconfigure(0, weight=3)
    tab2.grid_columnconfigure(1, weight=1)
    tab2.grid_rowconfigure(1, weight=1)
    _add_tab(tab2, "grafico_torta", "Categorie")
    img_mouse = self.icone_gui.get("mouse")
    lbl_periodo_tab2 = tk.Label(
            tab2, 
            text="Doppio clic → Mostra Dettaglio ", 
            image=img_mouse,
            compound="right",
            background=self.COLOR_WIDGET_BG, 
            foreground="gray", 
            font=("Arial", 9, "italic"),
    )
    lbl_periodo_tab2.image = img_mouse 
    lbl_periodo_tab2.grid(row=0, column=0, sticky="w", padx=10, pady=5)
    selettore_anno2 = ttk.Combobox(tab2, values=["Tutti"] + [str(a) for a in anni], style="Border.TCombobox", state='readonly')
    selettore_anno2.set("Tutti")
    selettore_anno2.grid(row=0, column=0, sticky="n", pady=10)
    selettore_anno2.bind("<<ComboboxSelected>>", aggiorna_tab2)
    canvas_frame_scroll = ttk.Frame(tab2)
    canvas_frame_scroll.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 10))
    scrollbar_h = ttk.Scrollbar(canvas_frame_scroll, orient="horizontal", style="Horizontal.TScrollbar")
    scrollbar_h.pack(side="bottom", fill="x")
    canvas2 = tk.Canvas(canvas_frame_scroll, bg=self.COLOR_WIDGET_BG, xscrollcommand=scrollbar_h.set)
    canvas2.pack(side="top", fill="both", expand=True)
    scrollbar_h.config(command=canvas2.xview)
    canvas2.tooltip = None
    canvas2.anno_corrente = selettore_anno2.get()
    canvas2.bind("<Configure>", ridisegna_tab2)
    frame_legenda = ttk.Frame(tab2)
    frame_legenda.grid(row=1, column=1, sticky="nsew", padx=5, pady=(0, 10))
    lbl_leg = tk.Label(frame_legenda, text="Legenda Categorie", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR, font=("Arial", 10, "bold"))
    lbl_leg.pack(pady=5)
    columns = ("Categoria", "Importo")
    self.tree_legenda = ttk.Treeview(frame_legenda, columns=columns, show="headings", selectmode="browse")
    self.tree_legenda.heading("Categoria", text="Categoria", 
        command=lambda: self.treeview_sort_column(self.tree_legenda, "Categoria", False))
    self.tree_legenda.heading("Importo", text="Importo", 
        command=lambda: self.treeview_sort_column(self.tree_legenda, "Importo", False))
    self.tree_legenda.column("Categoria", width=120, anchor="w")
    self.tree_legenda.column("Importo", width=80, anchor="e")
    sb_legenda = ttk.Scrollbar(frame_legenda, orient="vertical", command=self.tree_legenda.yview, style="Vertical.TScrollbar")
    self.tree_legenda.configure(yscrollcommand=sb_legenda.set)
    sb_legenda.pack(side="right", fill="y")
    self.tree_legenda.pack(side="left", fill="both", expand=True)
    self.tree_legenda.bind("<Double-1>", on_legenda_double_click)
    tab3 = ttk.Frame(notebook)
    _add_tab(tab3, "saldo", "Saldo Mensile/Annuale")
    frame_totali_tab3 = ttk.Frame(tab3)
    frame_totali_tab3.pack(side="bottom", pady=10)
    self.lbl_entrate_tab3 = ttk.Label(frame_totali_tab3, text="Entrate: € 0.00", style="GSaldoPositivo.TLabel")
    self.lbl_entrate_tab3.pack(side="left", padx=10)
    self.lbl_uscite_tab3 = ttk.Label(frame_totali_tab3, text="Uscite: € 0.00", style="GSaldoNegativo.TLabel")
    self.lbl_uscite_tab3.pack(side="left", padx=10)
    self.lbl_saldo_tab3 = ttk.Label(frame_totali_tab3, text="Saldo: € 0.00", style="GSaldo.TLabel")
    self.lbl_saldo_tab3.pack(side="left", padx=10)
    img_mouse_tab3 = self.icone_gui.get("mouse")
    lbl_periodo_tab3 = tk.Label(
            tab3, 
            text="Doppio clic → Mostra Dettaglio ", 
            image=img_mouse,
            compound="right",
            background=self.COLOR_WIDGET_BG, 
            foreground="gray", 
            font=("Arial", 9, "italic"),
    )
    lbl_periodo_tab3.image = img_mouse_tab3
    lbl_periodo_tab3.pack(side="top", padx=10, pady=5)
    selettore_anno3 = ttk.Combobox(tab3, values=["Tutti"] + [str(a) for a in anni], style="Border.TCombobox", state='readonly')
    selettore_anno3.set("Tutti")
    selettore_anno3.pack(pady=10)
    selettore_anno3.bind("<<ComboboxSelected>>", aggiorna_tab3)
    canvas3 = tk.Canvas(tab3, bg=self.COLOR_WIDGET_BG)
    canvas3.pack(fill="both", expand=True, padx=10, pady=10)
    canvas3.selettore_rif = selettore_anno3
    canvas3.bind("<Configure>", ridisegna_tab3)
    frame_footer = ttk.Frame(self.grafico_analisi_popup)
    frame_footer.pack(side="bottom", fill="x", pady=(0, 15), padx=20)
    includi_futuri_graf_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(
        frame_footer,
        text="Includi movimenti futuri",
        variable=includi_futuri_graf_var,
        command=lambda: (aggiorna_tab1(), aggiorna_tab2(), aggiorna_tab3())
    ).pack(side="left", padx=10)
    img_chiudi_graf = self.icone_gui.get("chiudi")
    btn_chiudi_graf = tk.Label(frame_footer, compound="left", image=img_chiudi_graf, text="Chiudi" if img_chiudi_graf else "✖ Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padx=15, pady=6, font=("Arial", 9, "bold"))
    btn_chiudi_graf.pack(side="right")
    btn_chiudi_graf.bind("<Button-1>", lambda e: self.grafico_analisi_popup.destroy())
    aggiorna_tab3()
    aggiorna_tab2()
    aggiorna_tab1()
    self.grafico_analisi_popup.deiconify()

