#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import defaultdict
import datetime
import tkinter as tk
from tkinter import ttk

def _fmt_it(v, spec=",.2f"):
    s = format(v, spec)
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def crea_grafico_categorie(self, id_righe_selezionate):
    anno_filtro = None
    mese_filtro = None
    giorno_filtro = None
    entrate_count = 0
    uscite_count = 0
    tipo_transazione_ricercato = "saldo"
    colore_barra_base = None
    tooltip_window = None 
    stats_mode = getattr(self, 'stats_mode', tk.StringVar(value="totali")).get() 
    stats_refdate = getattr(self, 'stats_refdate', None) 
    categorie_da_elaborare = []
    for item_id in id_righe_selezionate:
        try:
            cat_name_raw = str(self.stats_table.item(item_id, "values")[0]).strip()
            cat_name = ' '.join(cat_name_raw.split()) 
            if cat_name not in categorie_da_elaborare:
                categorie_da_elaborare.append(cat_name)
        except:
            continue
    if not categorie_da_elaborare:
        self.show_custom_info("Errore", "Nessuna categoria valida trovata.")
        return
    if stats_mode == "giorno" and stats_refdate:
        anno_filtro = str(stats_refdate.year)
        mese_filtro = str(stats_refdate.month).zfill(2)
        giorno_filtro = str(stats_refdate.day).zfill(2)
    elif stats_mode == "mese" and stats_refdate:
        anno_filtro = str(stats_refdate.year)
        mese_filtro = str(stats_refdate.month).zfill(2)
    elif stats_mode == "anno" and stats_refdate:
        anno_filtro = str(stats_refdate.year)
    for data_oggetto, entries in self.spese.items():
        data_anno_str = str(data_oggetto.year)
        data_mese_pad = str(data_oggetto.month).zfill(2)
        if anno_filtro and data_anno_str != anno_filtro: continue
        if mese_filtro and data_mese_pad != mese_filtro: continue
        if not self.considera_ricorrenze_var.get() and data_oggetto > datetime.date.today(): continue
        for entry in entries:
            if len(entry) < 4: continue 
            cat_raw, desc, imp, tipo = entry[:4]
            cat = ' '.join(str(cat_raw).strip().split())
            tipo_lower = str(tipo).lower()
            
            if cat in categorie_da_elaborare:
                if "entrata" in tipo_lower:
                    entrate_count += 1
                elif "uscita" in tipo_lower:
                    uscite_count += 1
    if entrate_count > 0 and uscite_count > 0:
        tipo_transazione_ricercato = "misto"
    elif entrate_count > 0:
        tipo_transazione_ricercato = "entrata"
        colore_barra_base = "#28A745"
    else:
        tipo_transazione_ricercato = "uscita"
        colore_barra_base = "#DC3545"
    spese_combinate = defaultdict(lambda: {
        'Entrata': 0.0, 
        'Uscita': 0.0,
        'Dettaglio_Entrata': defaultdict(float),
        'Dettaglio_Uscita': defaultdict(float)
    })
    saldo_aggregato_totale = 0.0 
    for data_objeto, entries in self.spese.items():
        try:
            data_anno_str = str(data_objeto.year)
            data_mese_pad = str(data_objeto.month).zfill(2)
            data_giorno_pad = str(data_objeto.day).zfill(2)
        except:
            continue
        if anno_filtro and data_anno_str != anno_filtro: continue
        if mese_filtro and data_mese_pad != mese_filtro: continue
        if giorno_filtro and data_giorno_pad != giorno_filtro: continue
        if not self.considera_ricorrenze_var.get() and data_objeto > datetime.date.today(): continue
        if stats_mode == "giorno" or stats_mode == "mese":
            chiave_aggregazione = f"{data_giorno_pad} {data_mese_pad} {data_anno_str}"
        else:
            chiave_aggregazione = f"{data_anno_str}-{data_mese_pad}"
        for entry in entries:
            if len(entry) < 4: continue
            cat_raw, desc, imp, tipo = entry[:4]
            cat = ' '.join(str(cat_raw).strip().split())
            tipo_lower = str(tipo).lower()
            if cat in categorie_da_elaborare:
                try:
                    importo_numerico = float(imp)
                    
                    if tipo_transazione_ricercato == "misto":
                        if "entrata" in tipo_lower:
                            spese_combinate[chiave_aggregazione]['Entrata'] += importo_numerico
                            spese_combinate[chiave_aggregazione]['Dettaglio_Entrata'][cat] += importo_numerico
                            saldo_aggregato_totale += importo_numerico
                        elif "uscita" in tipo_lower:
                            spese_combinate[chiave_aggregazione]['Uscita'] += abs(importo_numerico)
                            spese_combinate[chiave_aggregazione]['Dettaglio_Uscita'][cat] += abs(importo_numerico)
                            saldo_aggregato_totale -= abs(importo_numerico)
                    elif tipo_transazione_ricercato == "entrata" and "entrata" in tipo_lower:
                        spese_combinate[chiave_aggregazione]['Entrata'] += importo_numerico
                        spese_combinate[chiave_aggregazione]['Dettaglio_Entrata'][cat] += importo_numerico
                        saldo_aggregato_totale += importo_numerico
                    elif tipo_transazione_ricercato == "uscita" and "uscita" in tipo_lower:
                        spese_combinate[chiave_aggregazione]['Uscita'] += abs(importo_numerico)
                        spese_combinate[chiave_aggregazione]['Dettaglio_Uscita'][cat] += abs(importo_numerico)
                        saldo_aggregato_totale -= abs(importo_numerico)
                except (ValueError, TypeError):
                    continue
    dati_filtrati_non_zero = {}
    totale_entrate_periodo = 0.0
    totale_uscite_periodo = 0.0
    for k, v in spese_combinate.items():
        if v['Entrata'] != 0.0 or v['Uscita'] != 0.0:
            totale_entrate_periodo += v['Entrata']
            totale_uscite_periodo += v['Uscita']
            if tipo_transazione_ricercato == "misto":
                dati_filtrati_non_zero[k] = v
            else:
                valore_unico = v['Entrata'] + v['Uscita']
                if tipo_transazione_ricercato == "entrata":
                    dati_filtrati_non_zero[k] = {'Totale': valore_unico, 'Dettaglio': v['Dettaglio_Entrata']}
                else:
                    dati_filtrati_non_zero[k] = {'Totale': valore_unico, 'Dettaglio': v['Dettaglio_Uscita']}
    saldo_netto_periodo = totale_entrate_periodo - totale_uscite_periodo
    if not dati_filtrati_non_zero:
        self.show_custom_info("Nessun Dato", "Nessun dato di transazione con importo non zero trovato per il filtro e il periodo selezionati.")
        return
    dati_ordinati = sorted(dati_filtrati_non_zero.items())
    dati_per_grafico = list(reversed(dati_ordinati)) 
    mesi_completi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                     "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"] 
    def _etichetta_periodo(periodo, mode):
        try:
            if mode not in ("giorno", "mese") and '-' in periodo and len(periodo.split('-')) == 2:
                a, m = periodo.split('-')
                m_num = int(m)
                if 1 <= m_num <= 12:
                    return f"{mesi_completi[m_num - 1][:3]} {a}"
            elif mode in ("giorno", "mese") and ' ' in periodo and len(periodo.split(' ')) == 3:
                g, m, a = periodo.split(' ')
                return f"{g}/{m}"
        except Exception:
            pass
        return periodo
    totale_aggregato = 0.0
    if tipo_transazione_ricercato == "misto":
        tipo_transazione_base = "Entrate vs Uscite"
        totale_copertura_desc_saldo = "Saldo Netto"
        totale_aggregato = saldo_netto_periodo
    elif tipo_transazione_ricercato == "entrata":
        tipo_transazione_base = "Entrate"
        totale_copertura_desc_saldo = "Totale Entrate"
        totale_aggregato = totale_entrate_periodo
    else:
        tipo_transazione_base = "Uscite"
        totale_copertura_desc_saldo = "Totale Uscite"
        totale_aggregato = totale_uscite_periodo
    if len(categorie_da_elaborare) > 1:
        tipo_titolo = "Combinata"
    else:
        tipo_titolo = "Categoria"
    if stats_mode == "giorno" and stats_refdate: 
        data_str = stats_refdate.strftime('%d/%m/%Y')
        etichetta_tempo = "Giornaliero"
        filtro_titolo = f" - Giorno {data_str}"
        totale_copertura_desc = f"{totale_copertura_desc_saldo} Giorno {data_str}"
    elif stats_mode == "mese" and anno_filtro and mese_filtro: 
        mese_nome = ""
        try:
            mese_num = int(mese_filtro)
            if 1 <= mese_num <= 12:
                mese_nome = mesi_completi[mese_num - 1]
            else:
                mese_nome = str(mese_filtro) 
        except ValueError:
            mese_nome = str(mese_filtro)
        etichetta_tempo = "Giornalieri" 
        filtro_titolo = f" - Mese {mese_nome} {anno_filtro}"
        totale_copertura_desc = f"{totale_copertura_desc_saldo} Mese {mese_nome} {anno_filtro}"
    elif stats_mode == "anno" and anno_filtro: 
        etichetta_tempo = "Mensili"  
        filtro_titolo = f" - Anno {anno_filtro}"
        totale_copertura_desc = f"{totale_copertura_desc_saldo} Anno {anno_filtro}"
    elif not anno_filtro:
        etichetta_tempo = "Annuale"  
        filtro_titolo = " - Totale Storico"
        totale_copertura_desc = f"{totale_copertura_desc_saldo} Totale Storico"
    else:
        etichetta_tempo = "Generale"  
        filtro_titolo = " - Periodo Non Specificato"
        totale_copertura_desc = f"{totale_copertura_desc_saldo} Generale"
    titolo_grafico = f"{tipo_transazione_base} {tipo_titolo} {etichetta_tempo}{filtro_titolo}"
    popup_width, popup_height = 1200, 600 
    self.popup_grafico = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    self.popup_grafico.withdraw()
    self.popup_grafico.title(f"📊 {titolo_grafico}")
    screen_width = self.winfo_screenwidth()
    screen_height = self.winfo_screenheight()
    center_x = int(screen_width/2 - popup_width/2)
    center_y = int(screen_height/2 - popup_height/2)
    self.popup_grafico.geometry(f'{popup_width}x{popup_height}+{center_x}+{center_y}')
    self.popup_grafico.resizable(True, True)
    self.popup_grafico.minsize(popup_width, popup_height)
    self.popup_grafico.bind('<Escape>', lambda e: self.popup_grafico.destroy())
    main_frame = tk.Frame(self.popup_grafico, bg=self.COLOR_TOPLEVEL)
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    if self.considera_ricorrenze_var.get():
        img_stato = self.icone_gui.get("check")
        testo_stato = " Movimenti futuri inclusi"
    else:
        img_stato = self.icone_gui.get("chiudi")
        testo_stato = " Movimenti futuri esclusi"
    lbl_stato = tk.Label(main_frame, image=img_stato, text=testo_stato, compound="left",
                 bg=self.COLOR_TOPLEVEL, fg="gray", font=("Arial", 9, "italic"))
    if img_stato:
        lbl_stato.image = img_stato
    lbl_stato.pack()
    img_mouse = self.icone_gui.get("mouse")
    lbl_hint = tk.Label(
        main_frame,
        text="Doppio clic → Mostra Dettaglio ",
        image=img_mouse,
        compound="right",
        background=self.COLOR_TOPLEVEL,
        foreground="gray",
        font=("Arial", 9, "italic")
    )
    if img_mouse:
        lbl_hint.image = img_mouse
    lbl_hint.pack(pady=(0, 5))
    saldo_netto_periodo = totale_entrate_periodo - totale_uscite_periodo
    colore_entrate = "green"
    colore_uscite = "red"
    colore_saldo = "green" if saldo_netto_periodo >= 0 else "red"
    colore_testo = self.TEXT_COLOR
    riepilogo_frame = tk.Frame(main_frame, bg=self.COLOR_TOPLEVEL)
    riepilogo_frame.pack(pady=(0, 15))
    font_riepilogo = ("Arial", 10, "bold")
    tk.Label(riepilogo_frame, bg=self.COLOR_TOPLEVEL , fg=colore_testo, text=" Totale Entrate: ", font=font_riepilogo).pack(side=tk.LEFT)
    tk.Label(riepilogo_frame, bg=self.COLOR_TOPLEVEL , fg=colore_entrate, text=f"{_fmt_it(totale_entrate_periodo)}", font=font_riepilogo).pack(side=tk.LEFT)
    tk.Label(riepilogo_frame, bg=self.COLOR_TOPLEVEL , fg=colore_testo, text=" € ", font=font_riepilogo).pack(side=tk.LEFT, padx=(0, 10))
    tk.Label(riepilogo_frame, bg=self.COLOR_TOPLEVEL , fg=colore_testo, text=" Totale Uscite: ", font=font_riepilogo).pack(side=tk.LEFT)
    tk.Label(riepilogo_frame, bg=self.COLOR_TOPLEVEL , fg=colore_uscite, text=f"{_fmt_it(totale_uscite_periodo)}", font=font_riepilogo).pack(side=tk.LEFT)
    tk.Label(riepilogo_frame, bg=self.COLOR_TOPLEVEL , fg=colore_testo, text=" € ", font=font_riepilogo).pack(side=tk.LEFT, padx=(0, 10))
    tk.Label(riepilogo_frame, bg=self.COLOR_TOPLEVEL , fg=colore_testo, text=" Saldo Netto: ", font=font_riepilogo).pack(side=tk.LEFT)
    tk.Label(riepilogo_frame, bg=self.COLOR_TOPLEVEL , fg=colore_saldo, text=f"{_fmt_it(saldo_netto_periodo)}", font=font_riepilogo).pack(side=tk.LEFT)
    tk.Label(riepilogo_frame, bg=self.COLOR_TOPLEVEL , fg=colore_testo, text=" €", font=font_riepilogo).pack(side=tk.LEFT)
    canvas_frame_scroll = ttk.Frame(main_frame)
    canvas_frame_scroll.pack(fill="both", expand=True)
    scrollbar_h = ttk.Scrollbar(canvas_frame_scroll, orient="horizontal", style="Horizontal.TScrollbar")
    canvas = tk.Canvas(
        canvas_frame_scroll, 
        bg=self.COLOR_TOPLEVEL,
        xscrollcommand=scrollbar_h.set 
    )
    canvas.pack(side="top", fill="both", expand=True)
    scrollbar_h.config(command=canvas.xview)
    canvas.bind("<Configure>", lambda e: disegna_barre_scroll(canvas, dati_per_grafico))
    def hide_tooltip_local(event=None):
        nonlocal tooltip_window
        if tooltip_window:
            tooltip_window.destroy()
            tooltip_window = None
    def show_tooltip_local(event, text):
        nonlocal tooltip_window
        hide_tooltip_local()
        root_x = canvas.winfo_rootx()
        root_y = canvas.winfo_rooty()
        screen_x = root_x + event.x + 15
        screen_y = root_y + event.y + 10
        tooltip_window = tk.Toplevel(canvas)
        tooltip_window.withdraw()
        tooltip_window.wm_overrideredirect(True)
        tooltip_window.wm_geometry(f"+{screen_x}+{screen_y}")
        tooltip_window.wm_attributes("-topmost", True)
        tooltip_window.config(
            highlightthickness=1,
            highlightbackground=self.COLOR_HIGHLIGHT,
            bg=self.COLOR_TOOLTIP
        )
        label = ttk.Label(tooltip_window, text=text, style="Tooltip.TLabel",
                           justify="left", font=("Courier New", 9, "bold"))
        label.pack()
        tooltip_window.deiconify()
    self.popup_grafico.bind("<Destroy>", lambda e: hide_tooltip_local(), add="+")
    def disegna_barre_scroll(c, dati_tuple):
        hide_tooltip_local()
        c.delete("all")
        ALTEZZA_MINIMA = 3
        LARGHEZZ_STANDARD = 100
        LARGHEZZ_MISTA = 140
        BAR_FACTOR = 0.7
        margine_superiore = 40
        margine_inferiore = 90
        SPAZIO_EXTRA_MINIMO = 200
        altezza = c.winfo_height()
        canvas_larghezza = c.winfo_width()
        if altezza < 50:
            altezza = c.winfo_reqheight()
            if altezza < 50: altezza = popup_height - 150 
        if canvas_larghezza < 50:
            canvas_larghezza = c.winfo_reqwidth()
            if canvas_larghezza < 50: canvas_larghezza = popup_width - 40
        if altezza <= 50 or canvas_larghezza <= 50:
            return
        y_base = altezza - margine_inferiore
        importi_entrate = []
        importi_uscite = []
        for _, val in dati_tuple:
            if isinstance(val, dict):
                if 'Totale' in val:
                    if tipo_transazione_ricercato == "entrata":
                        importi_entrate.append(val.get('Totale', 0))
                    else:
                        importi_uscite.append(abs(val.get('Totale', 0)))
                else:
                    importi_entrate.append(val.get('Entrata', 0))
                    importi_uscite.append(val.get('Uscita', 0))
            else:
                if tipo_transazione_ricercato == "entrata":
                    importi_entrate.append(val)
                else:
                    importi_uscite.append(abs(val))
        def calculate_capped_max(abs_importi):
            if not abs_importi or max(abs_importi) == 0: return 0
            abs_importi_sorted = sorted([i for i in abs_importi if i > 0], reverse=True)
            if len(abs_importi_sorted) <= 1: return abs_importi_sorted[0]
            valore_base = abs_importi_sorted[1]
            max_val_cap = valore_base * 2
            if abs_importi_sorted[0] / max_val_cap > 2.5: return max_val_cap
            else: return abs_importi_sorted[0]
        max_e = calculate_capped_max(importi_entrate)
        max_u = calculate_capped_max(importi_uscite)
        max_val = max(max_e, max_u)
        altezza_utilizzabile = altezza - (margine_superiore + margine_inferiore)
        scala = altezza_utilizzabile / max(max_val * 1.05, 0.01)
        y_zero = y_base
        x_current = margine_inferiore
        dati_posizioni = []
        for periodo, dati_valore in dati_tuple:
            is_misto = isinstance(dati_valore, dict) and 'Entrata' in dati_valore and 'Uscita' in dati_valore and 'Totale' not in dati_valore
            barra_width = LARGHEZZ_MISTA if is_misto else LARGHEZZ_STANDARD
            larghezza_gruppo = barra_width if stats_mode != "giorno" else LARGHEZZ_STANDARD 
            dati_posizioni.append({
                'periodo': periodo,
                'dati_valore': dati_valore,
                'x_start': x_current,
                'barra_width': barra_width
            })
            x_current += larghezza_gruppo
        if dati_tuple:
            larghezza_contenuto_barre = x_current + margine_inferiore
        else:
            larghezza_contenuto_barre = canvas_larghezza
        larghezza_contenuto = max(larghezza_contenuto_barre, canvas_larghezza + SPAZIO_EXTRA_MINIMO) if stats_mode != "giorno" else canvas_larghezza
        c.config(scrollregion=(0, 0, larghezza_contenuto, altezza))
        c.create_line(margine_inferiore/2, y_zero, larghezza_contenuto, y_zero, fill="gray", dash=(4, 2))
        c.bind("<Leave>", hide_tooltip_local)
        def formatta_dettaglio(dettagli_dict):
            if not dettagli_dict:
                return "Nessun dettaglio categoria."
            dati_ordinati = sorted(dettagli_dict.items(), key=lambda item: item[0], reverse=False)
            righe = [(cat, importo) for cat, importo in dati_ordinati if importo > 0]
            if not righe:
                return "Nessun dettaglio categoria."
            _larghezza_etichetta = max(len(_e) for _e, _ in righe) + 1
            dettaglio_lines = [
                f"{(_e + ':').ljust(_larghezza_etichetta + 2)}{_fmt_it(_v)} €"
                for _e, _v in righe
            ]
            return "\n".join(dettaglio_lines)
        for item in dati_posizioni:
            periodo_originale = item['periodo']
            dati_valore = item['dati_valore']
            LARGHEZZA_BARRA_DINAMICA = item['barra_width']
            x_start_base = item['x_start']
            x_start = x_start_base
            if stats_mode == "giorno":
                x_center = canvas_larghezza / 2
                bar_group_width = LARGHEZZA_BARRA_DINAMICA * BAR_FACTOR
                x_start = x_center - (bar_group_width / 2)
            is_misto = isinstance(dati_valore, dict) and 'Entrata' in dati_valore and 'Uscita' in dati_valore and 'Totale' not in dati_valore
            titolo_per_popup = _etichetta_periodo(periodo_originale, stats_mode)
            if is_misto:
                valore_e = dati_valore.get('Entrata', 0)
                valore_u = dati_valore.get('Uscita', 0)
                dettaglio_e = dati_valore.get('Dettaglio_Entrata', {})
                dettaglio_u = dati_valore.get('Dettaglio_Uscita', {})
                barra_singola_w = (LARGHEZZA_BARRA_DINAMICA * BAR_FACTOR) / 2
                if valore_e > 0:
                    valore_e_scalato = min(valore_e, max_val)
                    altezza_barra_e = max(valore_e_scalato * scala, ALTEZZA_MINIMA)
                    x0_e, x1_e = x_start, x_start + barra_singola_w
                    rect_e = c.create_rectangle(x0_e, y_zero - altezza_barra_e, x1_e, y_zero, fill="#28A745")
                    testo_etichetta = f"{_fmt_it(valore_e)}"
                    c.create_text(
                        (x0_e + x1_e) / 2, y_zero - altezza_barra_e - 6,
                        text=testo_etichetta, font=("Arial", 9), fill="#28A745"
                    )
                    dettaglio_cat_e = formatta_dettaglio(dettaglio_e)
                    tooltip_text_e = (
                        f"Totale Entrata: {_fmt_it(valore_e)} €\n"
                        f"{dettaglio_cat_e}"
                    )
                    c.tag_bind(rect_e, "<Enter>", lambda e, t=tooltip_text_e: show_tooltip_local(e, t))
                    c.tag_bind(rect_e, "<Leave>", hide_tooltip_local)                        
                    tipo_bind_e = 'Entrata'
                    titolo_e_popup = f"Entrate aggregate {titolo_per_popup}"
                    c.tag_bind(rect_e, "<Double-1>", 
                        lambda e, p=periodo_originale, t=tipo_bind_e, tit=titolo_e_popup: 
                            self.mostra_transazioni_popup(
                                self.get_filter_data(p, t, categorie_da_elaborare, stats_mode),
                                tit
                            )
                    )
                if valore_u > 0:
                    valore_u_scalato = min(valore_u, max_val)
                    altezza_barra_u = max(valore_u_scalato * scala, ALTEZZA_MINIMA)
                    x0_u, x1_u = x_start + barra_singola_w, x_start + barra_singola_w * 2
                    rect_u = c.create_rectangle(x0_u, y_zero - altezza_barra_u, x1_u, y_zero, fill="#DC3545")
                    testo_etichetta = f"{_fmt_it(valore_u)}"
                    c.create_text(
                        (x0_u + x1_u) / 2, y_zero - altezza_barra_u - 6,
                        text=testo_etichetta, font=("Arial", 9), fill="#DC3545"
                    )
                    dettaglio_cat_u = formatta_dettaglio(dettaglio_u)
                    tooltip_text_u = (
                        f"Totale Uscita: {_fmt_it(valore_u)} €\n"
                        f"{dettaglio_cat_u}"
                    )
                    c.tag_bind(rect_u, "<Enter>", lambda e, t=tooltip_text_u: show_tooltip_local(e, t))
                    c.tag_bind(rect_u, "<Leave>", hide_tooltip_local)
                    tipo_bind_u = 'Uscita'
                    titolo_u_popup = f"Uscite aggregate {titolo_per_popup}"
                    c.tag_bind(rect_u, "<Double-1>", 
                        lambda e, p=periodo_originale, t=tipo_bind_u, tit=titolo_u_popup: 
                            self.mostra_transazioni_popup(
                                self.get_filter_data(p, t, categorie_da_elaborare, stats_mode),
                                tit
                            )
                    )                        
                x_center_text = x_start + (LARGHEZZA_BARRA_DINAMICA * BAR_FACTOR) / 2
            else: 
                if isinstance(dati_valore, dict):
                    valore = dati_valore.get('Totale', 0)
                    dettaglio = dati_valore.get('Dettaglio', {})
                else:
                    valore = dati_valore
                    dettaglio = {}
                colore_barra = "#28A745" if tipo_transazione_ricercato == "entrata" else "#DC3545"
                valore_scalato = min(abs(valore), max_val)
                altezza_barra_pix = max(valore_scalato * scala, ALTEZZA_MINIMA)
                x0 = x_start
                x1 = x0 + LARGHEZZA_BARRA_DINAMICA * BAR_FACTOR
                rect = c.create_rectangle(x0, y_zero - altezza_barra_pix, x1, y_zero, fill=colore_barra)
                importo_formattato = f"{_fmt_it(valore)} €"
                c.create_text((x0 + x1) / 2, y_zero - altezza_barra_pix - 6, text=importo_formattato, font=("Arial", 9), fill=colore_barra)
                x_center_text = (x0 + x1) / 2
                tipo_testo = "Entrata" if tipo_transazione_ricercato == "entrata" else "Uscita"
                dettaglio_cat = formatta_dettaglio(dettaglio)
                tooltip_text = (
                    f"Totale {tipo_testo}: {_fmt_it(valore)} €\n"
                    f"{dettaglio_cat}"
                )
                c.tag_bind(rect, "<Enter>", lambda e, t=tooltip_text: show_tooltip_local(e, t))
                c.tag_bind(rect, "<Leave>", hide_tooltip_local)                    
                tipo_bind = tipo_transazione_ricercato.capitalize()
                titolo_s_popup = f"{tipo_bind} aggregate {titolo_per_popup}"
                c.tag_bind(rect, "<Double-1>", 
                    lambda e, p=periodo_originale, t=tipo_bind, tit=titolo_s_popup: 
                        self.mostra_transazioni_popup(
                            self.get_filter_data(p, t, categorie_da_elaborare, stats_mode),
                            tit
                        )
                )
            label_y = altezza - margine_inferiore + 40
            if stats_mode == "giorno": label_y = altezza - 20
            c.create_text(
                x_center_text,
                label_y,
                text=_etichetta_periodo(periodo_originale, stats_mode),
                font=("Arial", 8),
                fill=self.TEXT_COLOR,
                angle=45 if stats_mode != "giorno" else 0
            )
    self.get_filter_data = lambda periodo, tipo, categories, mode: self._build_filter_data(periodo, tipo, categories, mode)
    if stats_mode == "giorno":
         scrollbar_h.pack_forget()
    else:
         scrollbar_h.pack(side="bottom", fill="x")
    self.popup_grafico.update_idletasks()
    disegna_barre_scroll(canvas, dati_per_grafico)
    self.popup_grafico.after(100, lambda: disegna_barre_scroll(canvas, dati_per_grafico)) 
    self.popup_grafico.transient(self)
    if stats_mode != "giorno":
        self.popup_grafico.after(200, lambda: canvas.xview_moveto(0)) 
    def chiudi_popup():
        self.popup_grafico.destroy()
    totale_formattato = f"{_fmt_it(totale_aggregato)} €"
    colore_totale = "black"
    if tipo_transazione_ricercato == "misto":
          if totale_aggregato > 0:
              colore_totale = "#28A745"
          elif totale_aggregato < 0:
              colore_totale = "#DC3545"
          else:
              colore_totale = "gray"
    elif tipo_transazione_ricercato == "entrata":
        colore_totale = "#28A745"
    elif tipo_transazione_ricercato == "uscita":
        colore_totale = "#DC3545"
    totale_frame = tk.Frame(main_frame, bg=self.COLOR_TOPLEVEL)
    totale_frame.pack(fill='x', pady=(10, 5), padx=20) 
    tk.Label(
        totale_frame,
        bg=self.COLOR_TOPLEVEL,
        fg=self.TEXT_COLOR,
        text=f"{totale_copertura_desc}:",
        font=("Arial", 10),
        anchor="w"
    ).pack(side="left")
    tk.Label(
        totale_frame,
        bg=self.COLOR_TOPLEVEL,
        text=totale_formattato,
        font=("Arial", 10, "bold"),
        anchor="w", 
        padx=5,
        fg=colore_totale 
    ).pack(side="left") 
    img_chiudi_main = self.icone_gui.get("chiudi")
    btn_chiudi_main = tk.Label(main_frame, compound="left", image=img_chiudi_main, text="Chiudi" if img_chiudi_main else "✖ Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padx=15, pady=6, font=("Arial", 9, "bold"))
    btn_chiudi_main.pack(pady=10)
    btn_chiudi_main.bind("<Button-1>", lambda e: chiudi_popup())
    self.popup_grafico.bind("<Escape>", lambda event: chiudi_popup())
    self.popup_grafico.deiconify()
def _build_filter_data(self, periodo, tipo, categories_to_elaborate, stats_mode):
    mesi_abbr = {
        "Gen": 1, "Feb": 2, "Mar": 3, "Apr": 4, 
        "Mag": 5, "Giu": 6, "Lug": 7, "Ago": 8, 
        "Set": 9, "Ott": 10, "Nov": 11, "Dic": 12
    }
    anno_bind = None
    mese_bind = None
    giorno_bind = None
    try:
        if stats_mode == "anno" and periodo in mesi_abbr:
            mese_bind = mesi_abbr[periodo] 
            if hasattr(self, 'stats_anno') and self.stats_anno != "Tutti":
                anno_bind = self.stats_anno
            giorno_bind = None
        elif ' ' in periodo and len(periodo.split(' ')) == 3:
            g, m, a = periodo.split(' ')
            anno_bind = a
            mese_bind = int(m)
            giorno_bind = int(g)
        elif '-' in periodo and len(periodo.split('-')) == 2:
            a, m = periodo.split('-')
            anno_bind = a
            mese_bind = int(m)
            giorno_bind = None
        elif len(periodo) == 4 and periodo.isdigit():
            anno_bind = periodo
            mese_bind = None
            giorno_bind = None
    except Exception:
        pass
    return {
        "anno": anno_bind, 
        "mese": mese_bind, 
        "giorno": giorno_bind,
        "tipo": tipo,
        "categorie": categories_to_elaborate
    }

