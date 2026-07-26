#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import datetime
import tkinter as tk
from tkinter import ttk, filedialog

def calcolo_mutuo_prestito(self):
    import __main__ as _app
    EXPORT_FILES = _app.EXPORT_FILES
    def popola_piano(tree_widget, capitale_iniziale, anni, mesi, rata_base, spese_mensili, tasso_mensile, title_label, ammortamento_extra=0):
        import datetime
        oggi = datetime.date.today()
        if capitale_iniziale is None or anni is None or mesi is None:
            for row in tree_widget.get_children():
                tree_widget.delete(row)
            title_label.config(text="Nessun dato disponibile")
            return
        for row in tree_widget.get_children():
            tree_widget.delete(row)
        debito_res = capitale_iniziale
        if ammortamento_extra > 0:
            debito_res -= ammortamento_extra
        capitale_res_dopo_extra = debito_res
        try:
            if tasso_mensile > 0:
                rata_base_nuova = capitale_res_dopo_extra * (tasso_mensile * (1 + tasso_mensile) ** mesi) / ((1 + tasso_mensile) ** mesi - 1)
            else:
                rata_base_nuova = capitale_res_dopo_extra / mesi
        except (ZeroDivisionError, OverflowError):
            rata_base_nuova = 0
        totale_capitale = ammortamento_extra
        totale_interessi = 0
        for mese in range(1, mesi + 1):
            m_rata = (oggi.month + mese - 1) % 12 + 1
            a_rata = oggi.year + (oggi.month + mese - 1) // 12
            data_str = f"{oggi.day:02d}-{m_rata:02d}-{a_rata}"
            label_periodo = f"Rata {mese} ({data_str})"
            interessi_rata = debito_res * tasso_mensile
            capitale_rata = rata_base_nuova - interessi_rata
            debito_res -= capitale_rata
            totale_capitale += capitale_rata
            totale_interessi += interessi_rata
            tree_widget.insert("", "end", values=(
               label_periodo,
               f"{rata_base_nuova + spese_mensili:.2f} €",
               f"{capitale_rata:.2f} €",
               f"{interessi_rata:.2f} €",
               f"{debito_res if debito_res > 0.005 else 0.0:.2f} €"
            ))
        totale_rata_pagata = totale_capitale + totale_interessi + (spese_mensili * mesi)
        riepilogo_text = (
            f"Capitale: {capitale_iniziale:.2f} €\n"
            f"Durata: {anni} anni ({mesi} mesi)\n"
            f"Tasso: {tasso_mensile * 100 * 12:.2f} %\n"
            f"Metodo: Ammortamento Francese (Rata Costante)\n"
            f"Ammortamento Extra: {ammortamento_extra:.2f} €\n"
            f"Importo Totale Restituito: {totale_rata_pagata:.2f} €\n"
            f"Interessi Totali: {totale_interessi:.2f} €"
        )
        title_label.config(text=riepilogo_text, wraplength=1000)
        tree_widget.insert("", "end", values=("TOTALE", f"{totale_rata_pagata:,.2f} €", f"{totale_capitale:,.2f} €", f"{totale_interessi:,.2f} €", "-"), tags=('total_row',))
        tree_widget.tag_configure('total_row', font=('Arial', 10, 'bold'))
    def crea_tab_piano_ammortamento(notebook_widget, title):
        frame = ttk.Frame(notebook_widget, padding=10)
        img_tab_piano = self.icone_gui.get("grafico_linea")
        if img_tab_piano:
            notebook_widget.add(frame, image=img_tab_piano, text=f"  {title}  ", compound="left")
        else:
            notebook_widget.add(frame, text=title)
        title_label = ttk.Label(frame, text="Nessun dato disponibile", font=("Arial", 9, "bold"))
        title_label.pack(pady=10, fill=tk.X)
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        tree = ttk.Treeview(tree_frame, columns=("Rata", "Rata Mensile", "Quota Capitale", "Quota Interessi", "Debito Residuo"), show="headings")
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview, style="Vertical.TScrollbar")
        scrollbar.pack(side='right', fill='y')
        tree.configure(yscrollcommand=scrollbar.set)
        tree.heading("Rata", text="Rata")
        tree.heading("Rata Mensile", text="Rata Mensile")
        tree.heading("Quota Capitale", text="Quota Capitale")
        tree.heading("Quota Interessi", text="Quota Interessi")
        tree.heading("Debito Residuo", text="Debito Residuo")            
        tree.column("Rata", width=50, anchor="center")
        tree.column("Rata Mensile", width=120, anchor="center")
        tree.column("Quota Capitale", width=120, anchor="center")
        tree.column("Quota Interessi", width=120, anchor="center")
        tree.column("Debito Residuo", width=120, anchor="center")            
        return tree, title_label
    def calcola_scenario_singolo(capitale_iniziale, anni_simulazione, tasso_annuo, spese_mensili, ammortamento_extra=0):
        try:
            if ammortamento_extra > capitale_iniziale:
                raise ValueError("L'ammortamento extra non può essere maggiore del capitale.")
            tasso_mensile = tasso_annuo / 100 / 12
            mesi_simulazione = anni_simulazione * 12
            if mesi_simulazione <= 0:
                return {
                    "rata_mensile_totale": 0,
                    "interessi_totali": 0,
                    "importo_totale": ammortamento_extra,
                    "capitale": capitale_iniziale,
                    "anni": 0,
                    "mesi": 0,
                    "rata_base": 0,
                    "spese_mensili": spese_mensili,
                    "tasso_mensile": tasso_mensile,
                    "tasso_annuo": tasso_annuo,
                    "ammortamento_extra": ammortamento_extra
                }
            debito_res = capitale_iniziale - ammortamento_extra
            if debito_res <= 0:
                return {
                    "rata_mensile_totale": 0,
                    "interessi_totali": 0,
                    "importo_totale": ammortamento_extra,
                    "capitale": capitale_iniziale,
                    "anni": 0,
                    "mesi": 0,
                    "rata_base": 0,
                    "spese_mensili": spese_mensili,
                    "tasso_mensile": tasso_mensile,
                    "tasso_annuo": tasso_annuo,
                    "ammortamento_extra": ammortamento_extra
                }
            if tasso_mensile > 0:
                rata_base = debito_res * (tasso_mensile * (1 + tasso_mensile) ** mesi_simulazione) / ((1 + tasso_mensile) ** mesi_simulazione - 1)
            else:
                rata_base = debito_res / mesi_simulazione
            interessi_totali_nuovi = (rata_base * mesi_simulazione) - debito_res
            importo_totale_nuovo = debito_res + interessi_totali_nuovi + (spese_mensili * mesi_simulazione) + ammortamento_extra
            return {
                "rata_mensile_totale": rata_base + spese_mensili,
                "interessi_totali": interessi_totali_nuovi,
                "importo_totale": importo_totale_nuovo,
                "capitale": capitale_iniziale,
                "anni": anni_simulazione,
                "mesi": mesi_simulazione,
                "rata_base": rata_base,
                "spese_mensili": spese_mensili,
                "tasso_mensile": tasso_mensile,
                "tasso_annuo": tasso_annuo,
                "ammortamento_extra": ammortamento_extra
            }
        except (ValueError, OverflowError):
            return None
    def aggiorna_simulazione_singola(i):
        campi_input = [entry.get().replace(",", ".").strip() for entry in entry_scenari[i]]
        if not campi_input[0] or not campi_input[1] or not campi_input[2]:
            for lbl in lbl_scenari_risultati[i]: lbl.config(text="N/A", foreground=self.TEXT_COLOR )
            popola_piano(trees_piani[i], None, None, None, None, None, None, labels_piani[i])
            self.tutti_i_risultati[i] = None
            return
        try:
            capitale_simulazione = float(campi_input[0])
            anni_simulazione = int(campi_input[1])
            tasso_annuo = float(campi_input[2])
            spese = float(campi_input[3] or 0)
            ammortamento_extra = float(campi_input[4] or 0)
            if (capitale_simulazione <= 0 or anni_simulazione <= 0 or tasso_annuo < 0 or
                capitale_simulazione > 500000 or anni_simulazione > 35 or tasso_annuo > 35):
                self.show_custom_warning("Attenzione", "Assicurati che siano positivi e rientrino in un intervallo ragionevole.\ncapitale_simulazione > 500000 or anni_simulazione > 35 or tasso_annuo > 35")
                raise ValueError("Uno o più valori non sono validi. Assicurati che siano positivi e rientrino in un intervallo ragionevole.")
            if ammortamento_extra > capitale_simulazione:
                self.show_custom_warning("Attenzione", "L'ammortamento extra non può essere maggiore del capitale.")
                raise ValueError("L'ammortamento extra non può essere maggiore del capitale.")
            risultati_scenario = calcola_scenario_singolo(capitale_simulazione, anni_simulazione, tasso_annuo, spese, ammortamento_extra)
            if risultati_scenario is not None:
                self.tutti_i_risultati[i] = risultati_scenario
                risultati_principali = self.tutti_i_risultati[0]
                lbl_scenari_risultati[i][0].config(text=f"{risultati_scenario['mesi']}")
                lbl_scenari_risultati[i][1].config(text=f"{risultati_scenario['tasso_mensile'] * 100:.4f} %")
                lbl_scenari_risultati[i][2].config(text=f"{risultati_scenario['rata_mensile_totale']:.2f} €")
                lbl_scenari_risultati[i][3].config(text=f"{risultati_scenario['interessi_totali']:.2f} €")
                costo_totale_cap_int = risultati_scenario['capitale'] + risultati_scenario['interessi_totali']
                lbl_scenari_risultati[i][4].config(text=f"{costo_totale_cap_int:.2f} €")
                if risultati_principali:
                    risparmio = risultati_principali["interessi_totali"] - risultati_scenario["interessi_totali"]
                    lbl_scenari_risultati[i][5].config(
                        text=f"{risparmio:.2f} €", 
                        foreground='green' if risparmio > 0 else ('#E53935' if risparmio < 0 else self.TEXT_COLOR)
                    )
                else:
                    lbl_scenari_risultati[i][5].config(text="N/A", foreground=self.TEXT_COLOR)
                popola_piano(
                    trees_piani[i], risultati_scenario["capitale"], risultati_scenario["anni"],
                    risultati_scenario["mesi"], risultati_scenario["rata_base"],
                    risultati_scenario["spese_mensili"], risultati_scenario["tasso_mensile"],
                    labels_piani[i], risultati_scenario["ammortamento_extra"]
                )
            else:
                for lbl in lbl_scenari_risultati[i]: lbl.config(text="N/A", foreground=self.TEXT_COLOR)
                popola_piano(trees_piani[i], None, None, None, None, None, None, labels_piani[i])
                self.tutti_i_risultati[i] = None
        except ValueError as ve:
            for lbl in lbl_scenari_risultati[i]: lbl.config(text="N/A", foreground=self.TEXT_COLOR)
            popola_piano(trees_piani[i], None, None, None, None, None, None, labels_piani[i])
            self.tutti_i_risultati[i] = None
    def calcola_tutte_simulazioni():
        self.tutti_i_risultati = [None] * 6
        for i in range(6):
            aggiorna_simulazione_singola(i)
        aggiorna_tab_analisi(self.tutti_i_risultati)
    def aggiorna_tab_analisi(risultati):
        for row in tree_analisi.get_children():
            tree_analisi.delete(row)
        risultati_principali = risultati[0] if risultati and risultati[0] else None
        for i, res in enumerate(risultati):
            if res:
                risparmio = 0.0
                if risultati_principali:
                    risparmio = risultati_principali["interessi_totali"] - res["interessi_totali"]
                tree_analisi.insert("", "end", values=(
                    f"Simulazione {i+1}", 
                    f"{res['capitale']:,.2f} €",
                    f"{res['anni']} anni ({res['mesi']} rate)", 
                    f"{res['tasso_annuo']:,.2f} %",
                    f"{res['ammortamento_extra']:,.2f} €",
                    f"{res['rata_mensile_totale']:,.2f} €", 
                    f"{res['importo_totale']:,.2f} €",
                    f"{res['interessi_totali']:,.2f} €",
                    f"{risparmio:,.2f} €"
                ), tags=('all_rows',))
        tree_analisi.tag_configure('all_rows', font=('Arial', 10, 'bold'))
    def resetta_tutti_i_campi_simulazione():
        for i in range(6):
            for entry_widget in entry_scenari[i]:
                entry_widget.delete(0, tk.END)
            for lbl in lbl_scenari_risultati[i]:
                lbl.config(text="N/A", foreground=self.TEXT_COLOR)
            popola_piano(trees_piani[i], None, None, None, None, None, None, labels_piani[i])
            self.tutti_i_risultati[i] = None
        aggiorna_tab_analisi(self.tutti_i_risultati)
    def esporta_dati_con_preview():
        import datetime
        oggi = datetime.date.today()
        try:
            idx_notebook = notebook.index(notebook.select())
        except:
            try:
                idx_notebook = self.notebook.index(self.notebook.select())
            except:
                return
        has_sim = hasattr(self, 'tutti_i_risultati') and any(self.tutti_i_risultati)
        has_killer = hasattr(self, 'killer_stats') and self.killer_stats
        if not has_sim and not has_killer:
            self.show_custom_warning("Dati mancanti", "Esegui una simulazione o un Piano Killer per esportare i dati.")
            return
        preview_window = tk.Toplevel(root, bg=self.COLOR_TOPLEVEL)
        preview_window.title("Report di Analisi e Proiezione Finanziaria")
        window_width, window_height = 1100, 630
        preview_window.geometry(f"{window_width}x{window_height}+{int(preview_window.winfo_screenwidth()/2 - window_width/2)}+{int(preview_window.winfo_screenheight()/2 - window_height/2)}")
        preview_window.minsize(window_width, window_height)
        preview_window.bind("<Escape>", lambda e: preview_window.destroy())
        preview_window.transient(root)
        preview_window.focus_set()
        contenuto_testo = (
            "═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════\n"
            "            REPORT FINANZIARIO COMPLETO - RIEPILOGO STATISTICHE E PIANO KILLER (AMMORTAMENTO FRANCESE)\n"
            "═════════════════════════════════════════════════════════════════════════════════════════════════════════════════════\n"
        )

        if has_sim:
            contenuto_testo += "Categoria            | Simulazione 1 | Simulazione 2 | Simulazione 3 | Simulazione 4 | Simulazione 5 | Simulazione 6\n"
            contenuto_testo += "─────────────────────┼───────────────┼───────────────┼───────────────┼───────────────┼───────────────┼───────────────\n"
            
            sim_data = {
                "Capitale (€)": [], "Durata (anni)": [], "N° Rate": [], "Scadenza Prevista": [],
                "Tasso (%)": [], "Spese Incasso (€)": [], "Ammort. Extra (€)": [], 
                "Rata Mensile (€)": [], "Interessi Totali (€)": [], "Costo Totale (€)": [], 
                "Risparmio Int. (€)": []
            }
            
            risultati_principali = self.tutti_i_risultati[0] if self.tutti_i_risultati[0] else None
            for i, res in enumerate(self.tutti_i_risultati):
                if res:
                    mesi_res = int(res['mesi'])
                    target_date = oggi + datetime.timedelta(days=int(mesi_res * 30.44))
                    data_stringa = target_date.strftime('%m/%Y')
                    sim_data["Capitale (€)"].append(f"{res['capitale']:.2f}")
                    sim_data["Durata (anni)"].append(f"{res['anni']}")
                    sim_data["N° Rate"].append(f"{res['mesi']}")
                    sim_data["Scadenza Prevista"].append(data_stringa)
                    sim_data["Tasso (%)"].append(f"{res['tasso_annuo']:.2f}")
                    sim_data["Spese Incasso (€)"].append(f"{res['spese_mensili']:.2f}")
                    sim_data["Ammort. Extra (€)"].append(f"{res['ammortamento_extra']:.2f}")
                    sim_data["Rata Mensile (€)"].append(f"{res['rata_mensile_totale']:.2f}")
                    sim_data["Interessi Totali (€)"].append(f"{res['interessi_totali']:.2f}")
                    sim_data["Costo Totale (€)"].append(f"{res['capitale'] + res['interessi_totali']:.2f}")
                    risparmio = risultati_principali["interessi_totali"] - res["interessi_totali"] if risultati_principali and i > 0 else 0.0
                    sim_data["Risparmio Int. (€)"].append(f"{risparmio:.2f}")
                else:
                    for key in sim_data: sim_data[key].append("")
            max_len_cat = max(len(cat) for cat in sim_data.keys())
            for cat, values in sim_data.items():
                formatted_cat = f"{cat}{' ' * (max_len_cat - len(cat))}"
                formatted_values = " | ".join(f"{val:<13}" for val in values)
                contenuto_testo += f"{formatted_cat} | {formatted_values}\n"
                if cat in ["Ammort. Extra (€)", "Costo Totale (€)", "Risparmio Int. (€)"]:
                    contenuto_testo += "─────────────────────┴───────────────┴───────────────┴───────────────┴───────────────┴───────────────┴───────────────\n"

        if 2 <= idx_notebook <= 5:
            idx_sim = idx_notebook - 2
            res_sel = self.tutti_i_risultati[idx_sim]
            if res_sel:
                contenuto_testo += f"\n📋 PIANO AMMORTAMENTO DETTAGLIATO: SIMULAZIONE {idx_sim + 1}\n"
                linea = "─" * 117
                contenuto_testo += linea + "\n"
                contenuto_testo += f"{'Periodo':<30} | {'Rata (€)':>12} | {'Cap. (€)':>12} | {'Int. (€)':>12} | {'Residuo (€)':>15}\n"
                contenuto_testo += linea + "\n"
                res_p = res_sel['capitale'] - res_sel.get('ammortamento_extra', 0)
                tasso_m = res_sel['tasso_mensile']
                rata_tot = res_sel['rata_mensile_totale']
                data_inizio = datetime.date.today()
                for m in range(1, res_sel['mesi'] + 1):
                    mese_rata = (data_inizio.month + m - 1) % 12 + 1
                    anno_rata = data_inizio.year + (data_inizio.month + m - 1) // 12
                    giorno_rata = min(data_inizio.day, 28)
                    data_corrente = f"{giorno_rata:02d}-{mese_rata:02d}-{anno_rata}"
                    q_i = res_p * tasso_m
                    q_c = res_sel['rata_base'] - q_i
                    res_p -= q_c
                    etichetta = f"Rata {m:>3} ({data_corrente})"
                    contenuto_testo += (
                        f"{etichetta:<30} | "
                        f"{rata_tot:>12.2f} | "
                        f"{q_c:>12.2f} | "
                        f"{q_i:>12.2f} | "
                        f"{max(0, res_p):>15.2f}\n"
                    )
                contenuto_testo += linea + "\n"
                
        elif idx_notebook >= 6:
            if has_killer:
                import datetime
                try:
                    def get_val_local(entry):
                        val = entry.get().strip().replace(",", ".")
                        return float(val) if val else 0.0
                    capitale_input = get_val_local(ent_k_residuo)
                    mesi_input     = int(get_val_local(ent_k_mesi))
                    rata_input     = get_val_local(ent_k_rata)
                    tasso_input    = get_val_local(ent_k_tasso)
                    extra_s_input  = get_val_local(ent_k_extra_subito)
                except:
                    capitale_input = rata_input = tasso_input = extra_s_input = 0.0
                    mesi_input = 0
                k_tot = getattr(self, 'killer_totali', {})
                int_senza_k = k_tot.get('interessi_senza_killer', 0.0)
                totale_senza_k = capitale_input + int_senza_k
                risparmio_k = k_tot.get('risparmio', 0.0)
                mesi_risp = int(k_tot.get('mesi_risparmiati', 0))
                strat = k_tot.get('strategia', 'N/D')
                total_int_k = sum(item['quota_int'] for item in self.killer_stats)
                total_vers_k = sum(item['versato'] for item in self.killer_stats)
                durata_effettiva = max(0, mesi_input - mesi_risp)
                oggi = datetime.date.today()
                def get_date_str(m):
                    if m <= 0: return "IMMEDIATA"
                    target = oggi + datetime.timedelta(days=int(m * 30.44))
                    return target.strftime('%m/%Y')
                d_fine_std = get_date_str(mesi_input)
                d_fine_k   = get_date_str(durata_effettiva)
                contenuto_testo += "\n\n🎯 " + "═"*45 + " PIANO KILLER " + "═"*55 + "\n"
                contenuto_testo += f"Sintesi: {getattr(self, 'killer_summary', 'Analisi Estinzione Strategica')}\n"
                contenuto_testo += f"{'─'*117}\n"
                contenuto_testo += " SITUAZIONE ATTUALE (DATI INSERITI)\n"
                contenuto_testo += f"{'─'*117}\n"
                contenuto_testo += f"{' > Debito Residuo Iniziale:':<45} {capitale_input:>20.2f} €\n"
                if extra_s_input > 0:
                    contenuto_testo += f"{' > Abbattimento Immediato:':<45} {extra_s_input:>20.2f} €\n"
                contenuto_testo += f"{' > Rata Mensile Attuale:':<45} {rata_input:>20.2f} €\n"
                contenuto_testo += f"{' > Durata Residua Dichiarata:':<45} {mesi_input:>20} rate\n"
                contenuto_testo += f"{' > Tasso Applicato:':<45} {tasso_input:>20.2f} %\n"
                contenuto_testo += f"{'─'*117}\n"
                contenuto_testo += " PROIEZIONE SENZA INTERVENTO (PIANO ORIGINARIO)\n"
                contenuto_testo += f"{'─'*117}\n"
                contenuto_testo += f"{' > Scadenza Prevista:':<45} {d_fine_std:>20}\n"
                contenuto_testo += f"{' > Interessi Totali Previsti:':<45} {int_senza_k:>20.2f} €\n"
                contenuto_testo += f"{' > Totale Montante (Cap+Int):':<45} {totale_senza_k:>20.2f} €\n"
                contenuto_testo += f"{'─'*117}\n"
                contenuto_testo += " RISULTATI DOPO IL PIANO KILLER\n"
                contenuto_testo += f"{'─'*117}\n"
                contenuto_testo += f" Metodo: Ricalcolo interessi su debito residuo (Ammortamento Francese)\n"
                contenuto_testo += f"{' > Strategia Selezionata:':<45} {strat.upper():>20}\n"
                contenuto_testo += f"{'─'*117}\n"
                contenuto_testo += f"{' > Risparmio Interessi Netto:':<45} {risparmio_k:>20.2f} €\n"
                contenuto_testo += f"{' > Totale Interessi da Pagare:':<45} {total_int_k:>20.2f} €\n"
                contenuto_testo += f"{'─'*117}\n"
                contenuto_testo += f"{' > Nuova Scadenza (Killer):':<45} {d_fine_k:>20}\n"
                contenuto_testo += f"{' > Numero Rate Residue:':<45} {durata_effettiva:>20} rate\n"
                contenuto_testo += f"{' > Anticipo su Estinzione:':<45} {mesi_risp:>20} mesi\n"
                contenuto_testo += f"{'─'*117}\n"
                contenuto_testo += f"{' > TOTALE VERSATO FINALE:':<45} {total_vers_k:>20.2f} €\n"
                contenuto_testo += f"{'═'*117}\n"
                if hasattr(self, 'killer_annuali') and self.killer_annuali:
                    import datetime
                    oggi = datetime.date.today()
                    
                    contenuto_testo += "\n─── Piano di Recupero Cash-Flow Annuale (Auto-Finanziamento) ───\n"
                    contenuto_testo += "─"*117 + "\n"
                    contenuto_testo += f"{'ANNO':<10} | {'ANNO SOLARE':<12} | {'Extra Previsto':>18} | {'Risparmio Rate':>18} | {'Impatto Reale':>20}\n"
                    contenuto_testo += "─"*117 + "\n"
                    anticipo_val = 0.0
                    if self.killer_stats and "Anticipo" in str(self.killer_stats[0]['mese']):
                        anticipo_val = self.killer_stats[0]['versato']
                        contenuto_testo += (
                            f"{'ANTICIPO':<10} | "
                            f"{oggi.year:<12} | "
                            f"{anticipo_val:>18.2f} | "
                            f"{0.0:>18.2f} | "
                            f"{anticipo_val:>20.2f}\n"
                        )
                    try:
                        val_extra_ricorrente = float(ent_k_extra_annuo.get().replace(",", "."))
                    except:
                        val_extra_ricorrente = 0.0
                    for ann in self.killer_annuali:
                        anno_solare = oggi.year + ann['anno']
                        extra_anno = val_extra_ricorrente
                        risparmio = ann.get('risparmio_rate', 0.0)
                        impatto_reale = extra_anno - risparmio
                        
                        contenuto_testo += (
                            f"Anno {ann['anno']:<5} | "
                            f"{anno_solare:<12} | "
                            f"{extra_anno:>18.2f} | "
                            f"{risparmio:>18.2f} | "
                            f"{impatto_reale:>20.2f}\n"
                        )
                    if self.killer_stats:
                        ultima_r = self.killer_stats[-1]
                        mesi_totali = len(self.killer_stats)
                        data_fine = oggi + datetime.timedelta(days=int(mesi_totali * 30.44))
                        contenuto_testo += (
                            f"{'CHIUSURA':<10} | "
                            f"{data_fine.year:<12} | "
                            f"{ultima_r['versato']:>18.2f} | "
                            f"{'---':>18} | "
                            f"{ultima_r['versato']:>20.2f} (Saldo Finale)\n"
                        )
                    contenuto_testo += "─"*117 + "\n"
                    contenuto_testo += "* ANTICIPO: Versamento una tantum effettuato oggi per abbattere il capitale.\n"
                    contenuto_testo += "* Extra Previsto: Somma degli extra versati nell'anno solare (esclusa la quota capitale della rata).\n"
                    contenuto_testo += "* Impatto Reale: Sforzo finanziario netto (Extra versato - Risparmio generato dalla riduzione della rata).\n"
                contenuto_testo += "\nDettaglio Piano Di Ammortamento Killer:\n"
                contenuto_testo += "─"*117 + "\n"
                contenuto_testo += f"{'Periodo':<30} | {'Versato (€)':>15} | {'Quota Cap. (€)':>15} | {'Quota Int. (€)':>15} | {'Residuo (€)':>15}\n"
                contenuto_testo += "─"*117 + "\n"
                for row in self.killer_stats:
                    contenuto_testo += (
                        f"{str(row['mese']):<30} | "
                        f"{row['versato']:>15.2f} | "
                        f"{row['quota_cap']:>15.2f} | "
                        f"{row['quota_int']:>15.2f} | "
                        f"{row['residuo']:>15.2f}\n"
                    )
                contenuto_testo += "═"*117 + "\n"
        contenuto_testo += f"\nReport generato il: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        text_frame = ttk.Frame(preview_window, padding=10)
        text_frame.pack(fill=tk.BOTH, expand=True)
        txt_preview = tk.Text(text_frame, wrap=tk.NONE, height=30, width=140, font=('Courier New', 9))
        txt_preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll = ttk.Scrollbar(text_frame, orient="vertical", command=txt_preview.yview, style="Vertical.TScrollbar")
        v_scroll.pack(side=tk.RIGHT, fill='y')
        txt_preview.config(yscrollcommand=v_scroll.set)
        txt_preview.insert(tk.END, contenuto_testo)
        txt_preview.config(state="disabled")
        def salva_effettivamente():
            now = datetime.date.today()
            default_filename = f"Analisi_Mutuo_Killer_{now.strftime('%d-%m-%Y')}.txt"
            file = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("File di testo", "*.txt")],
                initialdir=EXPORT_FILES,
                initialfile=default_filename,
                title="Salva Report Finanziario",
                confirmoverwrite=False,
                parent=preview_window
            )
            if file:
                if os.path.exists(file):
                    conferma = self.show_custom_askyesno(
                        "Sovrascrivere file?",
                        f"Il file '{os.path.basename(file)}' \nesiste già. Vuoi sovrascriverlo?"
                    )
                    if not conferma:
                        return
                try:
                    with open(file, "w", encoding="utf-8") as f:
                        f.write(contenuto_testo)
                    self.show_toast("Report salvato correttamente!")
                except Exception as e:
                    self.show_custom_warning("Errore", f"Impossibile salvare il file: {e}")
        button_frame = tk.Frame(preview_window, bg=self.COLOR_TOPLEVEL, pady=10)
        button_frame.pack()
        img_salva_rep = self.icone_gui.get("salva")
        btn_salva_rep = ttk.Label(button_frame, compound="left", image=img_salva_rep, text=" Salva Report" if img_salva_rep else "Salva Report", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_salva_rep.pack(side=tk.LEFT, padx=5)
        btn_salva_rep.bind("<Button-1>", lambda e: salva_effettivamente())
        img_stampa_rep = self.icone_gui.get("stampa")
        btn_stampa_rep = ttk.Label(button_frame, compound="left", image=img_stampa_rep, text=" Stampa" if img_stampa_rep else "Stampa", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_stampa_rep.pack(side=tk.LEFT, padx=5)
        btn_stampa_rep.bind("<Button-1>", lambda e: self._stampa_lista_diretta(contenuto_testo, self.show_custom_warning))
        img_chiudi_rep = self.icone_gui.get("chiudi")
        btn_chiudi_rep = ttk.Label(button_frame, compound="left", image=img_chiudi_rep, text=" Chiudi" if img_chiudi_rep else "Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_chiudi_rep.pack(side=tk.LEFT, padx=5)
        btn_chiudi_rep.bind("<Button-1>", lambda e: preview_window.destroy())

    def calcola_ammortamento_killer():
        try:
            import datetime
            oggi = datetime.date.today()
            self.killer_stats = []
            self.killer_annuali = []
            for row in tree_k_piano.get_children():
                tree_k_piano.delete(row)
            def get_val(entry):
                val = entry.get().strip().replace(",", ".")
                return float(val) if val else 0.0
            if not ent_k_residuo.get().strip() or not ent_k_mesi.get().strip() or not ent_k_tasso.get().strip():
                self.show_toast("Compila almeno Debito, Mesi e Tasso!")
                return
            residuo_iniziale = get_val(ent_k_residuo)
            mesi_rimanenti = int(get_val(ent_k_mesi))
            tasso_annuo = get_val(ent_k_tasso)
            rata_originale = get_val(ent_k_rata)
            extra_annuo = get_val(ent_k_extra_annuo)
            extra_subito = get_val(ent_k_extra_subito)
            if (residuo_iniziale <= 0 or mesi_rimanenti <= 0 or tasso_annuo < 0 or
                residuo_iniziale > 1000000 or mesi_rimanenti > 600 or tasso_annuo > 25):
                msg = ("Controlla i dati inseriti:\n"
                       "- Il debito deve essere tra 1 e 1.000.000 €\n"
                       "- I mesi devono essere tra 1 e 600\n"
                       "- Il tasso deve essere tra 0% e 25%")
                self.show_custom_warning("Dati non validi", msg)
                return
            if extra_subito > residuo_iniziale:
                self.show_custom_warning("Attenzione", "L'Abbattimento Iniziale non può superare il debito residuo.")
                return
            if rata_originale <= (residuo_iniziale * (tasso_annuo/100/12)) + 0.01:
                self.show_custom_warning("Errore Calcolo", "La rata è troppo bassa per coprire gli interessi mensili!")
                return
            mese_versamento = int(combo_k_mese.get())
            strategia = combo_k_strategia.get()
            self.killer_strategia_usata = strategia
            tasso_mensile = tasso_annuo / 100 / 12
            interessi_teorici_standard = (rata_originale * mesi_rimanenti) - residuo_iniziale
            debito = residuo_iniziale
            tot_versato_killer = 0
            tot_interessi_killer = 0
            risparmio_rate_anno_corrente = 0
            if extra_subito > 0:
                data_subito = oggi.strftime("%d-%m-%Y")
                abbattimento = min(extra_subito, debito)
                debito -= abbattimento
                tot_versato_killer += abbattimento
                tree_k_piano.insert("", "end", values=(
                    f"Anticipo ({data_subito})",
                    f"{abbattimento:.2f} €", 
                    f"{abbattimento:.2f} €", 
                    "0.00 €", 
                    f"{debito:.2f} €"
                ), tags=('extra_row',))
                self.killer_stats.append({
                'mese': f"Anticipo ({data_subito})", 
                'versato': abbattimento, 
                'quota_cap': abbattimento, 
                'quota_int': 0, 
                'residuo': debito
                })
            mese_corrente = 0
            rata_corrente = rata_originale
            if strategia == "Ricalcola Rata" and extra_subito > 0:
                if tasso_mensile > 0:
                    rata_corrente = debito * (tasso_mensile * (1 + tasso_mensile) ** mesi_rimanenti) / ((1 + tasso_mensile) ** mesi_rimanenti - 1)
                else:
                    rata_corrente = debito / mesi_rimanenti
            oggi = datetime.date.today()
            mese_corrente = 0
            while debito > 0.01 and mese_corrente < 600:
                mese_corrente += 1
                m_rata = (oggi.month + mese_corrente - 1) % 12 + 1
                a_rata = oggi.year + (oggi.month + mese_corrente - 1) // 12
                data_str = f"{oggi.day:02d}-{m_rata:02d}-{a_rata}"
                interessi_mese = debito * tasso_mensile
                tot_interessi_killer += interessi_mese
                risparmio_rate_anno_corrente += (rata_originale - rata_corrente)
                versamento_extra = extra_annuo if (m_rata == mese_versamento) else 0
                if versamento_extra > 0 and strategia == "Ricalcola Rata":
                    m_res = mesi_rimanenti - mese_corrente
                    if m_res > 0:
                        dp = debito - (rata_corrente - interessi_mese)
                        dn = max(0, dp - versamento_extra)
                        if dn > 0 and tasso_mensile > 0:
                            rata_corrente = dn * (tasso_mensile * (1 + tasso_mensile) ** m_res) / ((1 + tasso_mensile) ** m_res - 1)
                        elif dn > 0:
                            rata_corrente = dn / m_res
                        else:
                            rata_corrente = 0
                abb_pot = (rata_corrente - interessi_mese) + versamento_extra
                if abb_pot >= debito:
                    versato_reale = debito + interessi_mese
                    abb_eff = debito
                    debito = 0
                else:
                    versato_reale = rata_corrente + versamento_extra
                    abb_eff = abb_pot
                    debito -= abb_eff
                    
                tot_versato_killer += versato_reale
                label_periodo = f"Rata {mese_corrente:>3} ({data_str})"
                tree_k_piano.insert("", "end", values=(
                    label_periodo,
                    f"{versato_reale:.2f} €", 
                    f"{abb_eff:.2f} €", 
                    f"{interessi_mese:.2f} €", 
                    f"{max(debito,0):.2f} €"
                ), tags=('extra_row' if versamento_extra > 0 else ''))
                self.killer_stats.append({
                    'mese': label_periodo,
                    'versato': versato_reale, 
                    'quota_cap': abb_eff, 
                    'quota_int': interessi_mese, 
                    'residuo': max(debito, 0)
                })
                if mese_corrente % 12 == 0 or debito <= 0:
                    self.killer_annuali.append({
                        'anno': (mese_corrente + 11) // 12,
                        'risparmio_rate': risparmio_rate_anno_corrente,
                        'sforzo_netto': extra_annuo - risparmio_rate_anno_corrente if extra_annuo > 0 else 0
                    })
                    risparmio_rate_anno_corrente = 0
                    if debito <= 0: break
            oggi = datetime.date.today()
            anno_f = oggi.year + (oggi.month + mese_corrente - 1) // 12
            mese_f = (oggi.month + mese_corrente - 1) % 12 + 1
            mesi_ita = ["", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", 
                        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
            freedom_date = f"{mesi_ita[mese_f]} {anno_f}"
            risparmio_interessi = interessi_teorici_standard - tot_interessi_killer
            tree_k_piano.tag_configure('extra_row', background='#e1f5fe')
            self.killer_totali = {
                'tot_versato': tot_versato_killer,
                'tot_interessi': tot_interessi_killer,
                'interessi_senza_killer': interessi_teorici_standard,
                'risparmio': risparmio_interessi,
                'mesi_risparmiati': mesi_rimanenti - mese_corrente,
                'freedom_date': freedom_date,
                'strategia': strategia
            }
            testo_risultato = (
                f"Strategia: {strategia}  📅 Termine: {freedom_date.upper()}\n"
                f"🎯 Estinzione in {mese_corrente} Mesi (Risparmiati {self.killer_totali['mesi_risparmiati']} mesi)\n"
                f"💰 Tot. Versato: {tot_versato_killer:.2f} €  📉 Interessi: {tot_interessi_killer:.2f} €  🚀 Risparmio: {max(0, risparmio_interessi):.2f} €"
            )
            lbl_k_risultato.config(text=testo_risultato, foreground="#2e7d32")
            dati_per_pop = self.killer_annuali.copy()
            ex_val = extra_annuo
            f_date_pop = freedom_date

            def comando_popup(e, d_pop, ex_s, lista_dati):
                    pop = tk.Toplevel(root)
                    pop.title(f"Analisi Impatto - Termine previsto: {d_pop}")
                    pop.transient(root)
                    pop.focus_set()
                    w_pop, h_pop = 650, 520 
                    sw = pop.winfo_screenwidth(); sh = pop.winfo_screenheight()
                    x_c = int((sw/2) - (w_pop/2)); y_c = int((sh/2) - (h_pop/2))
                    pop.geometry(f"{w_pop}x{h_pop}+{x_c}+{y_c}")
                    pop.bind("<Escape>", lambda event: pop.destroy())
                    main_container = ttk.Frame(pop, padding="15")
                    main_container.pack(fill=tk.BOTH, expand=True)
                    ttk.Label(main_container, text="Riepilogo Impatto e Cash-Flow Reale", font=("Arial", 11, "bold")).pack(pady=(0,10))
                    table_frame = ttk.Frame(main_container)
                    table_frame.pack(fill=tk.BOTH, expand=True)
                    tree = ttk.Treeview(table_frame, columns=("a","as","e","r","s"), show="headings", height=12)
                    tree.heading("a", text="Anno"); tree.heading("as", text="Solare")
                    tree.heading("e", text="Extra"); tree.heading("r", text="Risparmio Rate")
                    tree.heading("s", text="Impatto Reale")
                    tree.column("a", width=70, anchor="center"); tree.column("as", width=80, anchor="center")
                    tree.column("e", width=100, anchor="e"); tree.column("r", width=120, anchor="e")
                    tree.column("s", width=140, anchor="e")
                    oggi = datetime.date.today()
                    if ex_s > 0:
                            tree.insert("", "end", values=("ANTICIPO", f"{oggi.year}", f"{ex_s:.2f} €", "0.00 €", f"{ex_s:.2f} €"), tags=("evidenza",))
                    for r in lista_dati:
                            data_target = oggi + datetime.timedelta(days=int(r['anno'] * 12 * 30.44))
                            tree.insert("", "end", values=(f"Anno {r['anno']}", f"{data_target.year}", f"{ex_val:.2f} €", f"{r['risparmio_rate']:.2f} €", f"{r['sforzo_netto']:.2f} €"))
                    if self.killer_stats:
                            ultima_riga = self.killer_stats[-1]
                            data_fine = oggi + datetime.timedelta(days=int(len(self.killer_stats) * 30.44))
                            tree.tag_configure("saldo", background="#D4EDDA", foreground="#155724")
                            tree.tag_configure("evidenza", background="#FFF9C4", foreground="#856404")
                            tree.insert("", "end", values=("ESTINZIONE", f"{data_fine.year}", f"{ultima_riga['versato']:.2f} €", "---", f"{ultima_riga['versato']:.2f} €"), tags=("saldo",))
                    sb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
                    tree.configure(yscrollcommand=sb.set)
                    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                    sb.pack(side=tk.RIGHT, fill=tk.Y)
                    img_chiudi_p = self.icone_gui.get("chiudi")
                    btn_chiudi_p = ttk.Label(main_container, compound="left", image=img_chiudi_p, text=" Chiudi" if img_chiudi_p else "❌ Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
                    btn_chiudi_p.pack(pady=10)
                    btn_chiudi_p.bind("<Button-1>", lambda event: pop.destroy())
            btn_vidi_sforzo.config(foreground=self.TEXT_COLOR, cursor="hand2")
            btn_vidi_sforzo.bind("<Button-1>", lambda e: comando_popup(e, f_date_pop, extra_subito, dati_per_pop))
        except Exception as e:
            self.show_custom_warning("Errore", f"Controlla i dati: {str(e)}")
            
    def reset_killer():
        ent_k_residuo.delete(0, tk.END)
        ent_k_mesi.delete(0, tk.END)
        ent_k_tasso.delete(0, tk.END)
        ent_k_rata.delete(0, tk.END)
        ent_k_extra_annuo.delete(0, tk.END)
        ent_k_extra_subito.delete(0, tk.END)
        combo_k_mese.set("1")
        combo_k_strategia.set("Ricalcola Rata")
        for row in tree_k_piano.get_children():
            tree_k_piano.delete(row)
        lbl_k_risultato.config(text="Pronto per il calcolo")
        self.killer_stats = []
        self.killer_annuali = []
        btn_vidi_sforzo.config(state="disabled", command=None)            
    self.killer_stats = []
    root = tk.Toplevel(bg=self.COLOR_TOPLEVEL)
    root.title("Gestore Finanziario - Calcolo Finanziamento e Simulazioni - Ammortamento Francese")
    root.geometry("1250x650")
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    window_width = 1250
    window_height = 650
    position_top = int(screen_height / 2 - window_height / 2)
    position_right = int(screen_width / 2 - window_width / 2)
    root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')
    root.minsize(window_width, window_height)
    root.protocol("WM_DELETE_WINDOW", lambda: (self.deiconify(), self.after(0, self.imp_entry.focus_set), root.destroy()))
    root.bind("<Escape>", lambda e: (self.deiconify(), self.after(0, self.imp_entry.focus_set), root.destroy()))
    self.withdraw()
    self.tutti_i_risultati = [None] * 6
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    simulazioni_frame = ttk.Frame(notebook, padding=10)
    img_tab_simulazioni = self.icone_gui.get("calcolatrice")
    if img_tab_simulazioni:
        notebook.add(simulazioni_frame, image=img_tab_simulazioni, text="  Simulazioni  ", compound="left")
    else:
        notebook.add(simulazioni_frame, text="Simulazioni")
    titoli_simulazioni = ["Scenario", "Capitale (€)", "Durata (anni)", "Tasso (%)", "Spese Incasso (€)", "Ammort. Extra (€)", "N° Rate", "Tasso Mensile", "Rata Mensile", "Interessi Totali", "Costo Totale", "Risparmio Interessi"]
    for i, titolo in enumerate(titoli_simulazioni):
        ttk.Label(simulazioni_frame, text=titolo, font=("Arial", 9, "bold")).grid(row=0, column=i, padx=5, pady=5, sticky="w")
    entry_scenari, lbl_scenari_risultati = [], []
    for i in range(6):
        entry_row, lbl_row = [], []
        ttk.Label(simulazioni_frame, text=f"Simulazione {i+1}").grid(row=i+1, column=0, pady=5, sticky="w")
        entry_capitale_scen = ttk.Entry(simulazioni_frame, width=9); entry_capitale_scen.grid(row=i+1, column=1, padx=5); entry_row.append(entry_capitale_scen)
        entry_durata_scen = ttk.Entry(simulazioni_frame, width=9); entry_durata_scen.grid(row=i+1, column=2, padx=5); entry_row.append(entry_durata_scen)
        entry_tasso_scen = ttk.Entry(simulazioni_frame, width=5); entry_tasso_scen.grid(row=i+1, column=3, padx=5); entry_row.append(entry_tasso_scen)
        entry_spese_scen = ttk.Entry(simulazioni_frame, width=9); entry_spese_scen.grid(row=i+1, column=4, padx=5); entry_row.append(entry_spese_scen)
        entry_ammortamento_extra_scen = ttk.Entry(simulazioni_frame, width=9); entry_ammortamento_extra_scen.grid(row=i+1, column=5, padx=5); entry_row.append(entry_ammortamento_extra_scen)
        lbl_rate_scen = ttk.Label(simulazioni_frame, text="N/A", width=5, anchor="w"); lbl_rate_scen.grid(row=i+1, column=6, padx=5); lbl_row.append(lbl_rate_scen)
        lbl_tasso_mensile_scen = ttk.Label(simulazioni_frame, text="N/A", width=9, anchor="w"); lbl_tasso_mensile_scen.grid(row=i+1, column=7, padx=5); lbl_row.append(lbl_tasso_mensile_scen)
        lbl_rata_scen = ttk.Label(simulazioni_frame, text="N/A", width=12, anchor="w"); lbl_rata_scen.grid(row=i+1, column=8, padx=5); lbl_row.append(lbl_rata_scen)
        lbl_interessi_scen = ttk.Label(simulazioni_frame, text="N/A", width=12, anchor="w"); lbl_interessi_scen.grid(row=i+1, column=9, padx=5); lbl_row.append(lbl_interessi_scen)
        lbl_costo_totale = ttk.Label(simulazioni_frame, text="N/A", width=12, anchor="w"); lbl_costo_totale.grid(row=i+1, column=10, padx=5); lbl_row.append(lbl_costo_totale)
        lbl_risparmiati_scen = ttk.Label(simulazioni_frame, text="N/A", width=15, anchor="w", font=("Arial", 9, "bold")); lbl_risparmiati_scen.grid(row=i+1, column=11, padx=5); lbl_row.append(lbl_risparmiati_scen)
        entry_scenari.append(entry_row)
        lbl_scenari_risultati.append(lbl_row)
    img_simula = self.icone_gui.get("stampa")
    btn_calcola_simulazioni = ttk.Label(simulazioni_frame, compound="left", image=img_simula, text=" Calcola Tutte le Simulazioni" if img_simula else "📄 Calcola Tutte le Simulazioni", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
    btn_calcola_simulazioni.grid(row=7, column=0, columnspan=11, pady=10)
    btn_calcola_simulazioni.bind("<Button-1>", lambda e: calcola_tutte_simulazioni())
    img_reset = self.icone_gui.get("reset")
    btn_reset_simulazioni = ttk.Label(simulazioni_frame, compound="left", image=img_reset, text=" Reset" if not img_reset else "", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(5, 5))
    btn_reset_simulazioni.grid(row=7, column=7, pady=10, padx=5)
    btn_reset_simulazioni.bind("<Button-1>", lambda e: resetta_tutti_i_campi_simulazione())
    analisi_frame = ttk.Frame(notebook, padding=10)
    img_tab_analisi = self.icone_gui.get("report")
    if img_tab_analisi:
        notebook.add(analisi_frame, image=img_tab_analisi, text="  Riepilogo Analisi  ", compound="left")
    else:
        notebook.add(analisi_frame, text="Riepilogo Analisi")
    tree_analisi = ttk.Treeview(analisi_frame, columns=("Scenario", "Capitale", "Durata", "Tasso", "Ammortamento Extra", "Rata Mensile", "Importo Totale", "Interessi Totali", "Risparmio Interessi"), show="headings")
    tree_analisi.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    headings = {"Scenario": 120, "Capitale": 120, "Durata": 150, "Tasso": 80, "Ammortamento Extra": 140, "Rata Mensile": 120, "Importo Totale": 150, "Interessi Totali": 120, "Risparmio Interessi": 140}
    for col, width in headings.items():
        tree_analisi.heading(col, text=col)
        tree_analisi.column(col, width=width, anchor="center")
    trees_piani, labels_piani = [], []
    for i in range(6):
        tree, label = crea_tab_piano_ammortamento(notebook, f"Simulazione {i+1}")
        trees_piani.append(tree); labels_piani.append(label)
    killer_frame = ttk.Frame(notebook, padding=10)
    img_tab_killer = self.icone_gui.get("tools")
    if img_tab_killer:
        notebook.add(killer_frame, image=img_tab_killer, text="  Piano KILLER  ", compound="left")
    else:
        notebook.add(killer_frame, text="🎯 Piano KILLER")
    k_input_frame = ttk.LabelFrame(killer_frame, text=" Parametri Estinzione Anticipata Strategica ", padding=10)
    k_input_frame.pack(fill=tk.X, pady=5)
    ttk.Label(k_input_frame, text="Debito Residuo (€):").grid(row=0, column=0, padx=5, sticky="w")
    ent_k_residuo = ttk.Entry(k_input_frame, width=12); ent_k_residuo.grid(row=0, column=1, padx=5, pady=2)
    ttk.Label(k_input_frame, text="Mesi Rimanenti:").grid(row=0, column=2, padx=5, sticky="w")
    ent_k_mesi = ttk.Entry(k_input_frame, width=8); ent_k_mesi.grid(row=0, column=3, padx=5, pady=2)
    ttk.Label(k_input_frame, text="Tasso Annuo (%):").grid(row=0, column=4, padx=5, sticky="w")
    ent_k_tasso = ttk.Entry(k_input_frame, width=8); ent_k_tasso.grid(row=0, column=5, padx=5, pady=2)
    ttk.Label(k_input_frame, text="Rata Mensile Attuale (€):").grid(row=0, column=6, padx=5, sticky="w")
    ent_k_rata = ttk.Entry(k_input_frame, width=12); ent_k_rata.grid(row=0, column=7, padx=5, pady=2)
    ttk.Label(k_input_frame, text="Extra Annuale (€):").grid(row=1, column=0, padx=5, sticky="w")
    ent_k_extra_annuo = ttk.Entry(k_input_frame, width=12); ent_k_extra_annuo.grid(row=1, column=1, padx=5, pady=2)
    ttk.Label(k_input_frame, text="Extra Anticipo (€):").grid(row=1, column=2, padx=5, sticky="w")
    ent_k_extra_subito = ttk.Entry(k_input_frame, width=8); ent_k_extra_subito.grid(row=1, column=3, padx=5, pady=2)
    ttk.Label(k_input_frame, text="Mese Versamento:").grid(row=1, column=4, padx=5, sticky="w")
    combo_k_mese = ttk.Combobox(k_input_frame, values=[str(i) for i in range(1, 13)], width=5, style="Border.TCombobox"); combo_k_mese.set("12"); combo_k_mese.grid(row=1, column=5, padx=5, pady=2)
    ttk.Label(k_input_frame, text="Strategia:").grid(row=1, column=6, padx=5, sticky="w")
    combo_k_strategia = ttk.Combobox(k_input_frame, values=["Mantieni Rata", "Ricalcola Rata"], width=15, style="Border.TCombobox"); combo_k_strategia.set("Ricalcola Rata"); combo_k_strategia.grid(row=1, column=7, padx=5, pady=2)
    img_killer = self.icone_gui.get("aggiungi")
    btn_killer = ttk.Label(k_input_frame, compound="left", image=img_killer, text=" Calcola Piano Killer" if img_killer else "🚀 Calcola Piano Killer", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
    btn_killer.grid(row=2, column=0, columnspan=4, pady=10)
    btn_killer.bind("<Button-1>", lambda e: calcola_ammortamento_killer())
    img_sforzo = self.icone_gui.get("help")
    btn_vidi_sforzo = ttk.Label(k_input_frame, compound="left", image=img_sforzo, text=" Analisi Esborso" if img_sforzo else "💡 Analisi Esborso", background=self.COLOR_WIDGET_BG, foreground="gray", cursor="arrow", padding=(10, 5))
    btn_vidi_sforzo.grid(row=2, column=4, columnspan=4, pady=10)
    img_reset_k = self.icone_gui.get("cancella")
    btn_reset_k = ttk.Label(k_input_frame, compound="left", image=img_reset_k, text=" Reset" if img_reset_k else "🔄 Reset", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
    btn_reset_k.grid(row=2, column=6, columnspan=2, pady=10, padx=2)
    btn_reset_k.bind("<Button-1>", lambda e: reset_killer())
       
    lbl_k_risultato = ttk.Label(killer_frame, text="Pronto per il calcolo", style="Verde.TLabel")
    lbl_k_risultato.pack(pady=5)
    tree_k_frame = ttk.Frame(killer_frame)
    tree_k_frame.pack(fill=tk.BOTH, expand=True)
    tree_k_piano = ttk.Treeview(tree_k_frame, columns=("Mese", "Versato", "Quota Capitale", "Quota Interessi", "Debito Residuo"), show="headings")
    tree_k_piano.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    for col in tree_k_piano["columns"]:
        tree_k_piano.heading(col, text=col)
        tree_k_piano.column(col, width=120, anchor="center")
    sb_k = ttk.Scrollbar(tree_k_frame, orient="vertical", command=tree_k_piano.yview, style="Vertical.TScrollbar")
    sb_k.pack(side=tk.RIGHT, fill=tk.Y)
    tree_k_piano.configure(yscrollcommand=sb_k.set)

    common_button_frame = tk.Frame(root,bg=self.COLOR_TOPLEVEL, padx=10, pady=10)
    common_button_frame.pack()  
    img_esp_riep = self.icone_gui.get("stampa")
    btn_esp_riep = ttk.Label(common_button_frame, compound="left", image=img_esp_riep, text=" Esporta Riepilogo" if img_esp_riep else "Esporta Riepilogo", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
    btn_esp_riep.pack(side=tk.LEFT, padx=5)
    btn_esp_riep.bind("<Button-1>", lambda e: esporta_dati_con_preview())
    img_chiudi_riep = self.icone_gui.get("chiudi")
    btn_chiudi_riep = ttk.Label(common_button_frame, compound="left", image=img_chiudi_riep, text=" Chiudi" if img_chiudi_riep else "Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
    btn_chiudi_riep.pack(side=tk.LEFT, padx=5)
    btn_chiudi_riep.bind("<Button-1>", lambda e: (self.deiconify(), self.after(0, self.imp_entry.focus_set), common_button_frame.winfo_toplevel().destroy()))

