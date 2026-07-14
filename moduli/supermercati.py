#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import datetime
import threading
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, filedialog

def spesa_supermercato(self):
    import __main__ as _app
    DB_DIR                 = _app.DB_DIR
    EXPORT_FILES           = _app.EXPORT_FILES
    EXP_DB                 = _app.EXP_DB
    SUPERMERCATI_DB        = _app.SUPERMERCATI_DB
    CATEGORIE_PREDEFINITE  = _app.CATEGORIE_PREDEFINITE
    self.risultati_finali = []
    try:
        from tkcalendar import DateEntry
    except ImportError:
        DateEntry = None
        if not hasattr(self, '_tkcalendar_warned'):
            print(f"AVVISO: Libreria 'tkcalendar' non trovata. La data dovrà essere inserita manualmente (gg-mm-aaaa).")
            self._tkcalendar_warned = True
    DEFAULT_SUPERMERCATI = ["Coop", "Dpiu", "Esselunga", "Eurospin", "Lidl", "Maurys"]
    SUPERMERCATI = []
    lista_spesa_data = defaultdict(lambda: {})
    campi_input_refs = {}
    dati_supermercati = {}
    ricerca_vars_crud = {}
    ricerca_var_confronto = tk.StringVar()
    supermercato_selezionato_var = tk.StringVar()
    filtro_supermercato_confronto_var = tk.StringVar(value="Tutti i supermercati")
    if not hasattr(self, 'risultati_tv_ref'):
        self.risultati_tv_ref = None
    if hasattr(self, '_popup_spesa_active') and self._popup_spesa_active.winfo_exists():
        self._popup_spesa_active.lift()
        return
    def _carica_dati_interno():
        nonlocal SUPERMERCATI, dati_supermercati
        if not os.path.exists(DB_DIR):
            os.makedirs(DB_DIR, exist_ok=True)
        try:
            if not os.path.exists(SUPERMERCATI_DB) or os.stat(SUPERMERCATI_DB).st_size == 0:
                dati = {s: [] for s in DEFAULT_SUPERMERCATI}
                SUPERMERCATI = DEFAULT_SUPERMERCATI
                dati_supermercati = dati
                _salva_dati_interno(dati)
                return
            else:
                with open(SUPERMERCATI_DB, 'r', encoding='utf-8') as f:
                    dati = json.load(f)
                    loaded_supermercati = [k for k, v in dati.items() if isinstance(v, list)]
                    loaded_supermercati.sort()
                    SUPERMERCATI = loaded_supermercati if loaded_supermercati else DEFAULT_SUPERMERCATI
                    dati_supermercati = {s: dati.get(s, []) for s in SUPERMERCATI}
        except (FileNotFoundError, json.JSONDecodeError):
            SUPERMERCATI = DEFAULT_SUPERMERCATI
            dati_supermercati = {s: [] for s in DEFAULT_SUPERMERCATI}
    def _salva_dati_interno(dati_da_salvare):
        try:
            with open(SUPERMERCATI_DB, 'w', encoding='utf-8') as f:
                dati_filtrati = {}
                for s in SUPERMERCATI:
                    if s in dati_da_salvare and dati_da_salvare[s]:
                        lista_articoli = dati_da_salvare[s].copy()
                        lista_articoli.sort(key=lambda x: x.get('nome', '').strip().lower()) 
                        dati_filtrati[s] = lista_articoli
                    elif s in dati_da_salvare:
                        dati_filtrati[s] = []
                json.dump(dati_filtrati, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Errore durante il salvataggio: {e}")
    def _svuota_campi(refs):
        prima_categoria_default = "Affettati"
        if CATEGORIE_PREDEFINITE and isinstance(CATEGORIE_PREDEFINITE, list):
            prima_categoria_default = CATEGORIE_PREDEFINITE[0]
        refs['nome'].set("")
        refs['descrizione'].set("")
        refs['categoria'].set(prima_categoria_default)
        refs['prezzo'].set("")
        refs['promo_attiva'].set(False)
        refs['prezzo_promo'].set("")
        refs['quantita'].set("")
        refs['data_scadenza'].set("")
        refs['data_inserimento_prezzo'].set("")
        refs['data_inizio_promo'].set("")
    def _controlla_scadenza_promo():
        def _parse_data_per_confronto(data_str):
            if not data_str:
                return None
            for fmt in ['%d-%m-%Y']:
                try:
                    return datetime.datetime.strptime(data_str, fmt).date() 
                except ValueError:
                    continue
            return None
        nonlocal dati_supermercati
        oggi = datetime.datetime.now().date()
        articoli_modificati = False
        for supermercato, articoli in dati_supermercati.items():
            for articolo in articoli:
                if articolo.get("promo", False) and articolo.get("data_scadenza"):
                    data_scad_str = articolo["data_scadenza"].strip()
                    data_scadenza = _parse_data_per_confronto(data_scad_str)
                    if data_scadenza is None:
                        continue 
                    if data_scadenza <= oggi:
                        articolo["promo"] = False
                        articolo["prezzo_promo"] = ""
                        articolo["data_scadenza"] = ""
                        articolo["data_inizio_promo"] = ""
                        articoli_modificati = True
        if articoli_modificati:
            _salva_dati_interno(dati_supermercati)
            if hasattr(self, 'risultati_tv_ref') and self.risultati_tv_ref:
                _aggiorna_lista_spesa_intelligente(self.risultati_tv_ref)
            if hasattr(self, 'show_custom_warning'):
                self.show_custom_warning("Aggiornamento Automatico", "Sono state disattivate alcune promozioni scadute.")
    def _sort_treeview(treeview, col, reverse):
        def convert_value(val):
            if isinstance(val, str):
                val_clean = val.replace('€', '').replace(',', '.').strip()
                try:
                    return float(val_clean)
                except (ValueError, TypeError):
                    return str(val).lower()
            try:
                return float(val)
            except:
                return str(val).lower()
        is_hierarchical = treeview.cget('show') == 'tree headings' and col != '#0' and treeview.master.winfo_name() == 'frame_tv_lista'
        if is_hierarchical:
            for parent in treeview.get_children(''):
                if treeview.tag_has('grand_total', parent): continue
                children = treeview.get_children(parent)
                data = [(treeview.set(child, col), child) for child in children if treeview.item(child, 'tags') != ('supermarket',)]
                data.sort(key=lambda item: convert_value(item[0]), reverse=reverse)
                for index, (val, child) in enumerate(data):
                    treeview.move(child, parent, index)
        else:
            data = [(treeview.set(child, col), child) for child in treeview.get_children('')]
            data.sort(key=lambda item: convert_value(item[0]), reverse=reverse)
            for index, (val, child) in enumerate(data):
                treeview.move(child, '', index)
        treeview.heading(col, command=lambda _col=col, t=treeview: _sort_treeview(t, _col, not reverse))
    def _carica_treeview(treeview, supermercato, articoli_filtrati=None):
        from datetime import datetime
        def determina_tag_promo(data_inizio_str, data_scadenza_str, is_promo_flag):
            if not is_promo_flag:
                return ()
            FORMATO_DATA = '%d-%m-%Y' 
            oggi = datetime.now().date()
            data_inizio = None
            data_scadenza = None
            try:
                if data_inizio_str:
                    data_inizio = datetime.strptime(data_inizio_str, FORMATO_DATA).date()
                if data_scadenza_str:
                    data_scadenza = datetime.strptime(data_scadenza_str, FORMATO_DATA).date()
            except (ValueError, TypeError):
                pass 
            if not data_inizio or not data_scadenza:
                return ('promo_in_arrivo',) 
            if data_inizio <= oggi <= data_scadenza:
                return ('promo_attiva',)
            elif oggi < data_inizio:
                return ('promo_in_arrivo',)
            else:
                return () 
        treeview.delete(*treeview.get_children())
        articoli_da_mostrare = articoli_filtrati if articoli_filtrati is not None else dati_supermercati.get(supermercato, [])
        articoli_da_mostrare.sort(key=lambda x: x.get('nome', '').lower())
        for i, articolo in enumerate(articoli_da_mostrare):
            promo_attiva_str = "Si" if articolo.get('promo', False) else "No"
            prezzo_promo_raw = articolo.get('prezzo_promo')
            prezzo_promo_val = f"{float(prezzo_promo_raw):.2f}" if prezzo_promo_raw and str(prezzo_promo_raw).replace('.', '', 1).isdigit() else ""
            prezzo_normale_raw = articolo.get('prezzo')
            prezzo_normale_val = f"{float(prezzo_normale_raw):.2f}" if prezzo_normale_raw and str(prezzo_normale_raw).replace('.', '', 1).isdigit() else ""
            data_inizio = articolo.get('data_inizio_promo', '')
            data_scadenza = articolo.get('data_scadenza', '')
            is_promo = articolo.get('promo', False)
            tags_da_applicare = determina_tag_promo(data_inizio, data_scadenza, is_promo) 
            valori_tupla = (
                articolo.get('nome', ''),
                articolo.get('descrizione', ''),
                articolo.get('categoria', ''),
                prezzo_normale_val,
                articolo.get('data_inserimento_prezzo', ''),
                promo_attiva_str,
                prezzo_promo_val,
                articolo.get('quantita', ''),
                articolo.get('data_inizio_promo', ''),
                articolo.get('data_scadenza', '')
            )
            treeview.insert('', 'end', 
                                    iid=f"item_{supermercato}_{i}", 
                                    values=valori_tupla,
                                    tags=tags_da_applicare 
                                   )
    def calcola_prezzo_minimo_globale(nome_articolo_cercato):
        minimo = float('inf')
        supermercato_migliore = None
        for nome_superm, articoli in dati_supermercati.items():
            for articolo in articoli:
                if articolo.get('nome', '').lower() == nome_articolo_cercato.lower():
                    try:
                        prezzo_str = articolo.get('prezzo', '9999.0')
                        prezzo = float(prezzo_str.replace(',', '.'))
                    except (ValueError, TypeError):
                        continue
                    if prezzo < minimo:
                        minimo = prezzo
                        supermercato_migliore = nome_superm
        return minimo, supermercato_migliore
    def trova_dettagli_affare_migliore(nome_articolo, superm_migliore, prezzo_minimo):
        articoli_superm = dati_supermercati.get(superm_migliore, [])
        for articolo in articoli_superm:
            nome = articolo.get('nome', '').lower()
            qta_catalogo = articolo.get('qta_catalogo', '1PZ')
            prezzo_str = articolo.get('prezzo', '9999.0')
            try:
                prezzo = float(prezzo_str.replace(',', '.'))
            except (ValueError, TypeError):
                continue
            if nome == nome_articolo.lower() and prezzo == prezzo_minimo:
                return {
                    'supermercato': superm_migliore,
                    'prezzo_un': prezzo,
                    'qta_catalogo': qta_catalogo 
                }
        raise ValueError(f"Dettagli completi dell'affare non trovati per {nome_articolo}.")
    def _cerca_articoli_crud(supermercato, treeview, ricerca_var):
        testo_ricerca = ricerca_var.get().lower().strip()
        if not treeview: return
        
        if not testo_ricerca:
            self.risultati_finali = dati_supermercati.get(supermercato, []).copy()
            _carica_treeview(treeview, supermercato, articoli_filtrati=None)
            return
        articoli_filtrati = []
        for articolo in dati_supermercati.get(supermercato, []):
            nome = articolo.get("nome", "").lower()
            categoria = articolo.get("categoria", "").lower()
            descrizione = articolo.get("descrizione", "").lower()
            
            if testo_ricerca in nome or testo_ricerca in categoria or testo_ricerca in descrizione:
                articoli_filtrati.append(articolo)
        self.risultati_finali = articoli_filtrati 
        _carica_treeview(treeview, supermercato, articoli_filtrati=articoli_filtrati)
    def _funzione_crud(azione, supermercato, treeview, frame_input):
        if supermercato not in campi_input_refs:
            self.show_toast("Seleziona un supermercato prima di procedere."); return
        if not treeview: return
        refs = campi_input_refs.get(supermercato)
        if not refs:
            refs = campi_input_refs.get('combo_gestione_super')
        if not refs: return
        data_ins_prezzo_ref = refs.get('data_inserimento_prezzo', tk.StringVar())
        data_inizio_promo_ref = refs.get('data_inizio_promo', tk.StringVar())
        LIMITI_CARATTERI = {
            'nome': 27,
            'descrizione': 35,
            'categoria': 24,
            'quantita': 18,
            'prezzo': 7,
            'prezzo_promo': 7
        }
        def _valida_lunghezza_campi_locale(refs):
            errori = []
            prezzo = refs['prezzo'].get().strip().replace(',', '.')
            prezzo_promo = refs['prezzo_promo'].get().strip().replace(',', '.')
            data_scadenza = refs['data_scadenza'].get().strip()
            data_ins_prezzo = data_ins_prezzo_ref.get().strip()
            data_inizio_promo = data_inizio_promo_ref.get().strip()
            promo_attiva = refs['promo_attiva'].get()
            if promo_attiva:
                if not prezzo_promo:
                    errori.append("- Hai attivato la promozione: il 'PREZZO PROMO' è obbligatorio.")
                if not data_inizio_promo:
                    errori.append("- Hai attivato la promozione: la 'DATA INIZIO PROMO' è obbligatoria.")
                if not data_scadenza:
                    errori.append("- Hai attivato la promozione: la 'DATA SCADENZA PROMO' è obbligatoria.")
            for key, max_len in LIMITI_CARATTERI.items():
                if key in refs:
                    current_value = refs[key].get().strip()
                    if len(current_value) > max_len:
                        errori.append(
                            f"- Il campo '{key.upper()}' ha {len(current_value)} caratteri, "
                            f"ma il limite massimo è {max_len}. Per favore accorcia."
                        )
            campi_prezzo = {
                'prezzo': prezzo,
                'prezzo_promo': prezzo_promo
            }
            for key, value in campi_prezzo.items():
                if value:
                    try:
                        float(value)
                    except ValueError:
                        errore_visuale = value.replace('.', ',')
                        errori.append(f"- Il campo '{key.upper()}' ('{errore_visuale}') deve essere un valore numerico valido (es. 10.50 o 10,50).")
            campi_data_check = {
                'DATA SCADENZA': data_scadenza,
                'DATA INSERIMENTO PREZZO': data_ins_prezzo,
                'DATA INIZIO PROMO': data_inizio_promo
            }
            formati_validi = ['%d-%m-%Y']
            date_oggetti = {}
            for key_name, date_value in campi_data_check.items():
                if date_value:
                    data_valida = False
                    data_obj = None
                    for formato in formati_validi:
                        try:
                            data_obj = datetime.datetime.strptime(date_value, formato)
                            data_valida = True; break
                        except ValueError: continue
                        
                    if data_valida:
                        date_oggetti[key_name] = data_obj
                    else:
                        errori.append(f"- Il campo '{key_name}' ('{date_value}') non è nel formato richiesto (GG-MM-AAAA).")
            if (promo_attiva and 'DATA INIZIO PROMO' in date_oggetti and 'DATA SCADENZA' in date_oggetti):
                data_inizio = date_oggetti['DATA INIZIO PROMO']
                data_fine = date_oggetti['DATA SCADENZA']
                if data_inizio >= data_fine:
                    errori.append("- Errore Logico: La 'DATA INIZIO PROMO' deve essere precedente (minore) alla 'DATA SCADENZA PROMO'.")
            nome = refs['nome'].get().strip()
            descrizione = refs['descrizione'].get().strip()
            categoria = refs['categoria'].get().strip()
            quantita = refs['quantita'].get().strip()
            return errori, nome, descrizione, categoria, quantita, prezzo, prezzo_promo, data_ins_prezzo, data_inizio_promo
        selezione = treeview.selection()
        azione_eseguita = False
        ricerca_var_locale = ricerca_vars_crud.get(supermercato, tk.StringVar())
        if azione == 'inserisci':
            errori, nome, descrizione, categoria, quantita, prezzo, prezzo_promo, data_ins_prezzo, data_inizio_promo = _valida_lunghezza_campi_locale(refs)
            data_ins_prezzo = data_ins_prezzo.strip()
            if errori:
                errore_messaggio = "Impossibile inserire. Si sono verificati i seguenti errori:\n" + "\n".join(errori)
                self.show_custom_warning("Errore di Validazione", errore_messaggio); return
            promo_attiva = refs['promo_attiva'].get()
            data_scadenza = refs['data_scadenza'].get().strip()
            data_corrente = datetime.datetime.now().strftime("%d-%m-%Y")
            if not data_ins_prezzo:
                data_ins_prezzo = data_corrente
                refs['data_inserimento_prezzo'].set(data_corrente)
            if not nome or not prezzo: self.show_custom_warning("Errore di Input", "Nome e Prezzo sono obbligatori."); return
            nuovo_articolo = {
                "nome": nome, "descrizione": descrizione, "categoria": categoria,
                "prezzo": prezzo,
                "promo": promo_attiva,
                "prezzo_promo": prezzo_promo,
                "supermercato": supermercato,
                "quantita": quantita,
                "data_scadenza": data_scadenza,
                "data_inserimento_prezzo": data_ins_prezzo,
                "data_inizio_promo": data_inizio_promo
            }
            dati_supermercati[supermercato].append(nuovo_articolo)
            dati_supermercati[supermercato].sort(key=lambda x: x.get('nome', '').lower())
            _svuota_campi(refs); _salva_dati_interno(dati_supermercati)
            _cerca_articoli_crud(supermercato, treeview, ricerca_var_locale)
            azione_eseguita = True
        elif azione == 'cancella':
            if not selezione: self.show_custom_warning("Selezione", "Selezionare un articolo da cancellare."); return
            if self.show_custom_askyesno("Cancellazione", "Sei sicuro di voler cancellare l'articolo selezionato?"):
                iid_da_cancellare = selezione[0]
                try: idx_cancellare = int(iid_da_cancellare.split('_')[-1])
                except ValueError: self.show_custom_warning("Errore", "Impossibile identificare l'articolo da cancellare."); return
                if 0 <= idx_cancellare < len(dati_supermercati[supermercato]):
                    dati_supermercati[supermercato].pop(idx_cancellare)
                    dati_supermercati[supermercato].sort(key=lambda x: x.get('nome', '').lower())
                    _svuota_campi(refs);
                    _salva_dati_interno(dati_supermercati)
                    _cerca_articoli_crud(supermercato, treeview, ricerca_var_locale)
                    azione_eseguita = True
        elif azione == 'modifica':
            if not selezione:
                self.show_toast("Per modificare, seleziona un articolo dalla lista."); return
            iid_selezionato = selezione[0]; valori_selezionati = treeview.item(iid_selezionato, 'values')
            if len(valori_selezionati) < 10:
                self.show_custom_warning("Errore Dati", f"Articolo incompleto. Trovati {len(valori_selezionati)} campi, attesi 10."); return
            refs['nome'].set(valori_selezionati[0])
            refs['descrizione'].set(valori_selezionati[1])
            refs['categoria'].set(valori_selezionati[2])
            prezzo_normale_pulito = valori_selezionati[3].replace('€', '').strip()
            refs['prezzo'].set(prezzo_normale_pulito)
            data_ins_prezzo_ref.set(valori_selezionati[4])
            promo_attiva = (valori_selezionati[5] == "Si" or valori_selezionati[5] == "Sì")
            refs['promo_attiva'].set(promo_attiva)
            prezzo_promo_pulito = valori_selezionati[6].replace('€', '').strip()
            refs['prezzo_promo'].set(prezzo_promo_pulito)
            refs['quantita'].set(valori_selezionati[7])
            refs['data_scadenza'].set(valori_selezionati[9])
            data_inizio_promo_ref.set(valori_selezionati[8])
            setattr(self, 'modifica_iid', iid_selezionato)
        elif azione == 'salva':
            modifica_iid_ref = getattr(self, 'modifica_iid', None) 
            if not selezione or not modifica_iid_ref or modifica_iid_ref not in selezione:
                self.show_custom_warning("Selezione/Stato", "Nessun articolo selezionato o lo stato di modifica non è attivo.\nSeleziona un articolo e premi 'Modifica', poi 'Salva'."); return
            errori, nome, descrizione, categoria, quantita, prezzo, prezzo_promo, data_ins_prezzo, data_inizio_promo = _valida_lunghezza_campi_locale(refs)
            if errori:
                errore_messaggio = "Impossibile salvare. Si sono verificati i seguenti errori:\n" + "\n".join(errori)
                self.show_custom_warning("Errore di Validazione", errore_messaggio); return
            promo_attiva = refs['promo_attiva'].get()
            data_corrente = datetime.datetime.now().strftime("%d-%m-%Y")
            if not data_ins_prezzo:
                data_ins_prezzo = data_corrente
                refs['data_inserimento_prezzo'].set(data_corrente)
            if not promo_attiva:
                data_inizio_promo = ""
                refs['data_inizio_promo'].set("")
                data_scadenza = ""
                refs['data_scadenza'].set("")
                prezzo_promo = ""
                refs['prezzo_promo'].set("")
            data_scadenza = refs['data_scadenza'].get().strip()
            if not nome or not prezzo: self.show_custom_warning("Errore di Input", "Nome e Prezzo sono obbligatori per il salvataggio."); return
            iid_da_salvare = selezione[0]
            try: idx_da_salvare = int(iid_da_salvare.split('_')[-1])
            except ValueError: self.show_custom_warning("Errore", "Impossibile identificare l'articolo da salvare."); return
            if 0 <= idx_da_salvare < len(dati_supermercati[supermercato]):
                dati_supermercati[supermercato][idx_da_salvare] = {
                    "nome": nome, "descrizione": descrizione, "categoria": categoria,
                    "prezzo": prezzo,
                    "promo": promo_attiva,
                    "prezzo_promo": prezzo_promo,
                    "supermercato": supermercato,
                    "quantita": quantita,
                    "data_scadenza": data_scadenza,
                    "data_inserimento_prezzo": data_ins_prezzo,
                    "data_inizio_promo": data_inizio_promo
                }
                dati_supermercati[supermercato].sort(key=lambda x: x.get('nome', '').lower())
                _salva_dati_interno(dati_supermercati); _svuota_campi(refs);
                delattr(self, 'modifica_iid')
                _cerca_articoli_crud(supermercato, treeview, ricerca_var_locale)
                azione_eseguita = True
        if azione_eseguita and self.risultati_tv_ref:
            _aggiorna_lista_spesa_intelligente(self.risultati_tv_ref)
    def _svuota_supermercato(supermercato, treeview):
        if not supermercato or supermercato == "Seleziona Supermercato":
            self.show_custom_warning("Selezione", "Seleziona un supermercato prima di svuotare."); return
        if self.show_custom_askyesno("Azzeramento Dati", f"Sei sicuro di voler cancellare TUTTI gli articoli\n dal supermercato '{supermercato}'?"):
            dati_supermercati[supermercato] = []
            _salva_dati_interno(dati_supermercati)
            _carica_treeview(treeview, supermercato)
            if self.risultati_tv_ref:
                _aggiorna_lista_spesa_intelligente(self.risultati_tv_ref)
            self.show_custom_warning("Successo", f"Database del supermercato '{supermercato}' azzerato.")
    def _cerca_articoli(testo_ricerca, tv_risultati):
        def _parse_data_per_confronto(data_str):
            if not data_str:
                return None
            for fmt in ['%d-%m-%Y']:
                try:
                    return datetime.datetime.strptime(data_str, fmt).date()
                except ValueError:
                    continue
            return None
        if not tv_risultati: return
        tv_risultati.delete(*tv_risultati.get_children())
        testo_ricerca = testo_ricerca.lower().strip()
        articoli_da_mostrare = []
        filtro_superm_selezionato = filtro_supermercato_confronto_var.get()
        if filtro_superm_selezionato == "Tutti i supermercati" or filtro_superm_selezionato == "Seleziona Supermercato":
            supermercati_da_cercare = dati_supermercati.keys()
            cerca_il_piu_conveniente = True
        else:
            supermercati_da_cercare = [filtro_superm_selezionato]
            cerca_il_piu_conveniente = False
        oggi = datetime.date.today()
        for supermercato in supermercati_da_cercare:
            if supermercato not in dati_supermercati: continue
            articoli = dati_supermercati[supermercato]
            for articolo in articoli:
                nome = articolo.get("nome", "").strip()
                categoria = articolo.get("categoria", "").strip()
                descrizione = articolo.get("descrizione", "").strip()
                if testo_ricerca and not (testo_ricerca in nome.lower() or testo_ricerca in categoria.lower() or testo_ricerca in descrizione.lower()):
                    continue
                prezzo_base_str = articolo.get("prezzo", "")
                prezzo_promo_str = articolo.get("prezzo_promo", "")
                prezzo_effettivo = prezzo_base_str
                promozione_valida = False
                promozione_futura = False
                status_promo = ""
                if articolo.get("promo", False) and prezzo_promo_str:
                    data_inizio = _parse_data_per_confronto(articolo.get("data_inizio_promo"))
                    data_fine = _parse_data_per_confronto(articolo.get("data_scadenza"))
                    if data_inizio:
                        if oggi < data_inizio:
                            status_promo = "Promo dal " + articolo.get('data_inizio_promo')
                            promozione_futura = True
                        elif oggi >= data_inizio:
                            if not data_fine or oggi <= data_fine:
                                promozione_valida = True
                                status_promo = "Promo Attiva"
                                prezzo_effettivo = prezzo_promo_str
                            else:
                                status_promo = "Promo scaduta"
                if not prezzo_effettivo: continue
                try:
                    prezzo_float = float(str(prezzo_effettivo).replace(',', '.'))
                    prezzo_base_float = float(str(prezzo_base_str).replace(',', '.')) if prezzo_base_str else None
                    prezzo_base_finale = f"{prezzo_base_float:.2f}" if prezzo_base_float else ""
                    prezzo_finale_formattato = f"{prezzo_float:.2f}"
                    articoli_da_mostrare.append({
                        "nome": nome,
                        "quantita": articolo.get("quantita", ""),
                        "supermercato": supermercato,
                        "descrizione": descrizione,
                        "categoria": categoria,
                        "prezzo_float": prezzo_float,
                        "prezzo_formattato": prezzo_finale_formattato,
                        "dettagli": status_promo,
                        "is_promo_valida": promozione_valida,
                        "is_promo_futura": promozione_futura,
                        "prezzo_base_str": prezzo_base_finale,
                        "data_inizio_promo_str": articolo.get("data_inizio_promo", ""),
                        "data_scadenza_str": articolo.get("data_scadenza", ""),
                    })
                except (ValueError, TypeError):
                    continue
        articoli_raggruppati_per_nome = defaultdict(list)
        for offerta in articoli_da_mostrare:
            chiave = (offerta['nome'].lower(), offerta['quantita'].lower())
            articoli_raggruppati_per_nome[chiave].append(offerta)
        tutti_gli_articoli_ordinati = sorted(articoli_da_mostrare, key=lambda x: x['nome'].strip().lower())
        articoli_inseriti_set = set()
        for offerta in tutti_gli_articoli_ordinati:
            chiave_comparazione = (offerta['nome'].lower(), offerta['quantita'].lower())
            iid_val = f"{offerta['nome']}|{offerta['quantita']}|{offerta['supermercato']}|{offerta['prezzo_float']}"
            if iid_val in articoli_inseriti_set: continue
            articoli_inseriti_set.add(iid_val)
            indicatore = ""
            is_strictly_cheaper = False
            if cerca_il_piu_conveniente:
                prezzi_simili = [o['prezzo_float'] for o in articoli_raggruppati_per_nome.get(chiave_comparazione, [])]
                min_price = min(prezzi_simili) if prezzi_simili else float('inf')
                is_min_price = (offerta['prezzo_float'] == min_price)
                count_min_price = sum(1 for p in prezzi_simili if p == min_price)
                is_strictly_cheaper = (is_min_price and count_min_price < len(prezzi_simili))
            promo_icona = ""
            if offerta.get("is_promo_valida", False):
                promo_icona = "Promo🔥" 
            elif offerta.get("is_promo_futura", False):
                promo_icona = "Promo🔥"
            elif offerta['dettagli'] and 'scaduta' in offerta['dettagli'].lower():
                promo_icona = "Promo⏳"
            miglior_prezzo_icona = ""
            if cerca_il_piu_conveniente and is_strictly_cheaper:
                miglior_prezzo_icona = "Top⭐"
            indicatore_testo = []
            if promo_icona:
                indicatore_testo.append(promo_icona)
            if miglior_prezzo_icona:
                indicatore_testo.append(miglior_prezzo_icona)
            if offerta['dettagli'] and 'attiva' not in offerta['dettagli'].lower():
                indicatore_testo.append(offerta['dettagli'])
            indicatore = " ".join(indicatore_testo).strip()
            tags_list = []
            if offerta.get("is_promo_valida", False):
                tags_list.append('promo_rossa')
            elif offerta.get("is_promo_futura", False):
                tags_list.append('promo_gialla')
            if cerca_il_piu_conveniente and is_strictly_cheaper and not tags_list:
                tags_list.append('piu_conveniente')
            tags_da_applicare = tuple(tags_list)
            values_to_insert = (
                offerta["nome"],
                offerta["quantita"],
                offerta["supermercato"],
                offerta["descrizione"],
                offerta["categoria"],
                f'{offerta["prezzo_formattato"]}',
                indicatore,
                offerta["data_inizio_promo_str"],
                offerta["data_scadenza_str"],
                f'{offerta["prezzo_base_str"]}'
            )
            tv_risultati.insert(
                parent='', index='end', iid=iid_val,
                values=values_to_insert, 
                tags=tags_da_applicare
            )
        self.risultati_finali = tutti_gli_articoli_ordinati
    def _ricarica_lista_spesa(tv_lista):
        tv_lista.delete(*tv_lista.get_children())
        totale_generale = 0.0
        gruppi_supermercati = defaultdict(lambda: [])
        for chiave, dati in lista_spesa_data.items():
            gruppi_supermercati[dati['supermercato']].append(dati)
        for superm in sorted(gruppi_supermercati.keys()):
            articoli = gruppi_supermercati[superm]
            articoli.sort(key=lambda x: x['nome'])
            totale_super = 0.0
            iid_super = f"group_{superm}"
            tv_lista.insert('', 'end', iid=iid_super, text=f"🛒 {superm}", tags=('supermarket',))
            for dati in articoli:
                totale_articolo = dati['qta_int'] * dati['prezzo_un']
                totale_super += totale_articolo
                chiave_lista = f"{dati['nome']}|{superm}"
                iid_articolo = f"item_{chiave_lista}"
                tv_lista.insert(
                    iid_super, 'end', iid=iid_articolo, text=dati['nome'],
                    values=(dati['qta_catalogo'], dati['qta_int'], f"{dati['prezzo_un']:.2f}",
                            f"{totale_articolo:.2f}", dati['supermercato'])
                )
            tv_lista.item(iid_super, values=("", "", "TOTALE PARZIALE:", f"{totale_super:.2f}", ""), tags=('supermarket',))
            totale_generale += totale_super
        tv_lista.insert('', 'end', text="TOTALE GENERALE SPESA:", values=("", "", "", f"{totale_generale:.2f}", ""), tags=('grand_total',))
        tv_lista.tag_configure('grand_total', font=('Arial', 10, 'bold'), background='#E0F7FA')
        tv_lista.tag_configure('supermarket', font=('Arial', 10, 'bold'), foreground='dodgerblue')
    def _aggiungi_a_lista_spesa(event, tv_lista, tv_risultati_ref):
        selezione = tv_risultati_ref.selection()
        if not selezione: return
        iid_selezionato = selezione[0]
        try:
            nome, qta_catalogo_base, superm_base, prezzo_str_base = iid_selezionato.split('|')
            prezzo_float_base = float(prezzo_str_base)
            nome = nome.strip()
        except ValueError:
            return
        prezzo_minimo, superm_migliore = calcola_prezzo_minimo_globale(nome)
        azione_richiesta = 'SELEZIONATO'
        if prezzo_minimo < prezzo_float_base and superm_migliore != superm_base:
            titolo_custom = "CONVIENE ALTROVE !"
            messaggio_custom = (
                f"L'articolo '{nome.upper()}' costa {prezzo_float_base:.2f} da {superm_base}.\n\n"
                f"Trovato a {prezzo_minimo:.2f} presso {superm_migliore}."
                f"\n\nVuoi aggiungere l'articolo con il PREZZO MIGLIORE?"
            )
            scelta = self.show_custom_askyesno(titolo_custom, messaggio_custom)
            if scelta:
                azione_richiesta = 'MIGLIORE'
            else:
                azione_richiesta = 'BASE' 
        superm_finale = superm_base
        prezzo_float_finale = prezzo_float_base
        qta_catalogo_finale = qta_catalogo_base
        if azione_richiesta == 'MIGLIORE':
            try:
                dettagli_migliore = trova_dettagli_affare_migliore(nome, superm_migliore, prezzo_minimo)
                superm_finale = dettagli_migliore['supermercato']
                prezzo_float_finale = dettagli_migliore['prezzo_un']
                qta_catalogo_finale = dettagli_migliore['qta_catalogo']
            except Exception as e:
                self.show_custom_warning("Errore Dati Critico", f"Errore nel recupero dettagli:\n{e}")
                return False
        chiave_lista = f"{nome}|{superm_finale}"
        quantita_precedente = lista_spesa_data.get(chiave_lista, {}).get('qta_int', 0)
        nuova_quantita_int = quantita_precedente + 1
        if quantita_precedente > 0:
            azione_testo = "Aggiornato"
        else:
            azione_testo = "Aggiunto"
        lista_spesa_data[chiave_lista] = {
            'nome': nome,
            'qta_catalogo': qta_catalogo_finale,
            'qta_int': nuova_quantita_int,
            'prezzo_un': prezzo_float_finale,
            'supermercato': superm_finale
        }
        messaggio_notifica = (
            f"✓ Articolo {azione_testo} in lista!\n"
            f"'{nome}' ({superm_finale})\n"
            f"Quantità Totale: {nuova_quantita_int} pezzi"
        )
        show_temporary_notification(tv_risultati_ref.winfo_toplevel(),
            "Conferma Lista",
            messaggio_notifica)
        _ricarica_lista_spesa(tv_lista)
    def show_temporary_notification(parent, title, message, duration_ms=3000):
        popup_note = tk.Toplevel(parent)
        popup_note.title(title)
        popup_note.overrideredirect(True) 
        popup_note.attributes("-topmost", True)
        popup_note.config(bg="orange")
        popup_note.withdraw() 
        parent.update_idletasks()
        width = 300
        height = 80
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)
        popup_note.geometry(f"{width}x{height}+{x}+{y}")
        label = tk.Label(popup_note, text=message, font=("Arial", 10, "bold"), 
                        justify="center", padx=10, pady=10, bg="orange", fg="black")
        label.pack(expand=True, fill='both')
        popup_note.deiconify() 
        popup_note.after(duration_ms, popup_note.destroy)
    def _rimuovi_articolo_da_lista(tv_lista):
        selezione = tv_lista.selection()
        if not selezione: 
            show_temporary_notification(
                tv_lista.winfo_toplevel(), 
                "Attenzione", 
                "Seleziona articolo o gruppo da rimuovere.",
                duration_ms=1500
            )
            return
        iid_selezionato = selezione[0]
        if iid_selezionato.startswith('item_'):
            try: 
                chiave_lista = iid_selezionato.split('item_')[1]
            except IndexError: 
                return
            if chiave_lista in lista_spesa_data:
                dettagli_articolo = lista_spesa_data[chiave_lista]
                nome_articolo = dettagli_articolo['nome']
                superm_articolo = dettagli_articolo['supermercato']
                qta_articolo = dettagli_articolo['qta_int']
                del lista_spesa_data[chiave_lista]
                _ricarica_lista_spesa(tv_lista)
                messaggio_notifica = (
                    f"Articolo Rimosso dalla lista.\n"
                    f"'{nome_articolo}' ({superm_articolo})\n"
                    f"Quantità: {qta_articolo} pezzi"
                )
                show_temporary_notification(tv_lista.winfo_toplevel(), 
                                            "Conferma Rimozione", 
                                            messaggio_notifica,
                                            duration_ms=2500)
        elif iid_selezionato.startswith('group_'):
            if self.show_custom_askyesno("Conferma", "Sei sicuro di voler rimuovere tutti gli articoli\n di questo supermercato dalla lista?"):
                superm = iid_selezionato.split('group_')[1]
                chiavi_da_rimuovere = [k for k, v in lista_spesa_data.items() if v['supermercato'] == superm]
                if chiavi_da_rimuovere:
                    for chiave in chiavi_da_rimuovere: 
                        del lista_spesa_data[chiave]
                    _ricarica_lista_spesa(tv_lista)
                    messaggio_notifica = f"Gruppo Rimosso dalla lista.\nSupermercato: {superm}"
                    show_temporary_notification(tv_lista.winfo_toplevel(), 
                                                "Conferma Rimozione", 
                                                messaggio_notifica,
                                                duration_ms=2500)
    def _svuota_lista_spesa(tv_lista):
        if not lista_spesa_data:
            show_temporary_notification(
                tv_lista.winfo_toplevel(), 
                "Attenzione", 
                "La lista della spesa è già vuota.",
                duration_ms=2000
            )
            return
        if self.show_custom_askyesno("Conferma", "Sei sicuro di voler rimuovere TUTTI gli articoli\n dalla lista spesa?"):
            tv_lista.delete(*tv_lista.get_children())
            lista_spesa_data.clear()
            _ricarica_lista_spesa(tv_lista)
            show_temporary_notification(
            tv_lista.winfo_toplevel(), 
            "Lista Svuotata", 
            "La lista della spesa è stata svuotata.",
            duration_ms=2000,
        )
    def _on_edit_quantity(event, tv_lista):
        region = tv_lista.identify("region", event.x, event.y)
        col = tv_lista.identify_column(event.x)
        
        if region == "cell" and col == "#2":
            row_id = tv_lista.identify_row(event.y)
            if not row_id.startswith('item_'): return
            try: chiave_lista = row_id.split('item_')[1]
            except: return
            if chiave_lista not in lista_spesa_data: return
            current_value = tv_lista.item(row_id)['values'][1]
            entry_editor = ttk.Entry(tv_lista, width=10)
            entry_editor.insert(0, str(current_value))
            x, y, width, height = tv_lista.bbox(row_id, col)
            entry_editor.place(x=x, y=y, width=width, height=height)
            entry_editor.focus_set()
            def on_entry_confirm(e):
                try:
                    new_qta = int(entry_editor.get().strip())
                    if new_qta > 0:
                        lista_spesa_data[chiave_lista]['qta_int'] = new_qta
                        _ricarica_lista_spesa(tv_lista)
                    elif new_qta == 0:
                        del lista_spesa_data[chiave_lista]
                        _ricarica_lista_spesa(tv_lista)
                except ValueError:
                    self.show_custom_warning("Errore", "La quantità deve essere un numero intero valido.")
                finally:
                    entry_editor.destroy()
            entry_editor.bind('<Return>', on_entry_confirm)
            entry_editor.bind('<FocusOut>', on_entry_confirm)
    def _genera_testo_esportazione():
        import datetime
        data_esportazione = datetime.datetime.now().strftime("%d/%m/%Y")
        WIDTH_NOME = 45
        WIDTH_QTA = 4
        WIDTH_PREZZO_BLOCCO = 30
        testo = f"CHECK-OUT: Spesa Ottimizzata ({data_esportazione})\n\n"
        totale_generale = 0.0
        gruppi_supermercati = defaultdict(lambda: [])
        for chiave, dati in lista_spesa_data.items(): gruppi_supermercati[dati['supermercato']].append(dati)
        for superm in sorted(gruppi_supermercati.keys()):
            articoli = gruppi_supermercati[superm]
            articoli.sort(key=lambda x: x['nome'])
            testo += f"[{superm.upper()}]\n"
            totale_super = 0.0
            for dati in articoli:
                totale_articolo = dati['qta_int'] * dati['prezzo_un']
                totale_super += totale_articolo
                linea = "[ ] "
                nome_completo = f"{dati['nome']} ({dati['qta_catalogo']})"
                linea += f"{nome_completo:<{WIDTH_NOME}}"
                qta_comprare = f"x {dati['qta_int']} pz"
                linea += f"{qta_comprare:<{WIDTH_QTA + 4}}"
                prezzo_blocco = f"({dati['prezzo_un']:.2f}) - Tot: {totale_articolo:.2f}"
                linea += f"{prezzo_blocco:>{WIDTH_PREZZO_BLOCCO}}\n"
                testo += linea
            testo += f"  TOTALE PARZIALE {superm}: {totale_super:.2f}\n\n"
            totale_generale += totale_super
        testo += f"\n"
        testo += f"TOTALE GENERALE STIMATO: {totale_generale:.2f}\n"
        return testo
    def _mostra_anteprima_esportazione():
        anteprima_text = _genera_testo_esportazione()
        preview_popup = tk.Toplevel(popup, bg=self.COLOR_TOPLEVEL)
        preview_popup.title("Anteprima Esportazione Lista Spesa")
        screen_width = preview_popup.winfo_screenwidth()
        screen_height = preview_popup.winfo_screenheight()
        x = (screen_width - 1050) // 2
        y = (screen_height - 600) // 2
        preview_popup.geometry(f"1050x600+{x}+{y}")
        preview_popup.minsize(1050, 600)
        preview_popup.after(10, lambda: preview_popup.focus_force())
        preview_popup.bind('<Escape>', lambda e: preview_popup.destroy())
        text_area = tk.Text(preview_popup, wrap='word', font=('Courier', 10), padx=10, pady=10)
        text_area.insert('1.0', anteprima_text)
        text_area.config(state='disabled')
        text_area.pack(fill='both', expand=True, padx=10, pady=10)
        frame_btn = tk.Frame(preview_popup, bg=self.COLOR_TOPLEVEL); frame_btn.pack(pady=(0, 10))
        img_chiudi = self.icone_gui.get("chiudi")
        btn_chiudi_preview = ttk.Label(
            frame_btn,
            compound="left",
            image=img_chiudi,
            text=" Chiudi" if img_chiudi else "Chiudi",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
        )
        btn_chiudi_preview.image = img_chiudi
        btn_chiudi_preview.pack(side='right', padx=5)
        btn_chiudi_preview.bind("<Button-1>", lambda e: preview_popup.destroy())
        img_esporta = self.icone_gui.get("salva")
        btn_esporta = ttk.Label(
            frame_btn,
            compound="left",
            image=img_esporta,
            text=" Esporta" if img_esporta else "Esporta",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
        )
        btn_esporta.image = img_esporta
        btn_esporta.pack(side='left', padx=5)
        btn_esporta.bind("<Button-1>", lambda e: _esporta_su_file(anteprima_text, preview_popup))
        img_stampa = self.icone_gui.get("stampa")
        btn_stampa_preview = ttk.Label(
            frame_btn,
            compound="left",
            image=img_stampa,
            text=" Stampa" if img_stampa else "Stampa",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
        )
        btn_stampa_preview.image = img_stampa
        btn_stampa_preview.pack(side='left', padx=5)
        btn_stampa_preview.bind("<Button-1>", lambda e: self._stampa_lista_diretta(anteprima_text, self.show_custom_warning))
    def _esporta_su_file(content_text, preview_popup):
        preview_popup.destroy()
        now = datetime.date.today()
        default_filename = f"Lista_Spesa_{now.day:02d}_{now.month:02d}_{now.year}.txt"
        f = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("File txt", "*.txt")], title="Salva la Lista Spesa su File",
            initialdir=EXPORT_FILES, confirmoverwrite=False, initialfile=default_filename, parent=popup
        )
        if f:
            try:
                with open(f, 'w', encoding='utf-8') as file_handle: file_handle.write(content_text)
                self.show_custom_warning("Successo", f"Lista spesa salvata con successo in:\n{f}")
            except Exception as e:
                self.show_custom_warning("Errore", f"Impossibile salvare il file:\n{e}")
        
    def _aggiorna_lista_spesa_intelligente(tv_risultati):
        if tv_risultati:
            _cerca_articoli(ricerca_var_confronto.get(), tv_risultati)
            if hasattr(self, 'risultati_finali') and self.risultati_finali:
                self.risultati_finali.sort(key=lambda x: x.get('nome', '').strip().lower())
    def _on_supermercato_change(event, combo, treeview_crud, frame_input, ricerca_var):
        selected_superm = combo.get()
        refs_combo = campi_input_refs.get('combo_gestione_super')
        if selected_superm == "Seleziona Supermercato":
            treeview_crud.delete(*treeview_crud.get_children())
            _svuota_campi(refs_combo) 
            return
        if selected_superm not in campi_input_refs:
            refs = {
                'nome': tk.StringVar(), 'descrizione': tk.StringVar(), 'categoria': tk.StringVar(),
                'prezzo': tk.StringVar(), 'promo_attiva': tk.BooleanVar(), 'prezzo_promo': tk.StringVar(),
                'quantita': tk.StringVar(), 'data_scadenza': tk.StringVar(),
                'data_inserimento_prezzo': tk.StringVar(),
                'data_inizio_promo': tk.StringVar()
            }
            campi_input_refs[selected_superm] = refs
        refs_superm = campi_input_refs[selected_superm]
        for key in refs_superm:
            refs_combo[key].set(refs_superm[key].get())
            refs_superm[key] = refs_combo[key] 
        if CATEGORIE_PREDEFINITE:
            if not refs_combo['categoria'].get().strip():
                 refs_combo['categoria'].set(CATEGORIE_PREDEFINITE[0])
        if selected_superm not in ricerca_vars_crud:
            ricerca_vars_crud[selected_superm] = tk.StringVar()
        ricerca_var.set(ricerca_vars_crud[selected_superm].get())
        _cerca_articoli_crud(selected_superm, treeview_crud, ricerca_vars_crud[selected_superm])
    def _esegui_rinomina_supermercato(combo, treeview_crud, ricerca_var):
        nonlocal SUPERMERCATI, dati_supermercati, campi_input_refs
        old_superm = combo.get()
        if old_superm == "Seleziona Supermercato" or not old_superm:
            self.show_custom_warning("Modifica Supermercato", "Seleziona prima un supermercato da rinominare.")
            return
        rinomina_popup = tk.Toplevel(popup, bg=self.COLOR_TOPLEVEL)
        rinomina_popup.title(f"Rinomina {old_superm}")
        rinomina_popup.transient(popup)
        rinomina_popup.resizable(False, False)
        rinomina_popup.update_idletasks()
        rinomina_popup.deiconify()
        rinomina_popup.grab_set()
        rinomina_popup.focus_set()
        ttk.Label(rinomina_popup, text="Nuovo nome:", style="Popup.TLabel").pack(padx=10, pady=(10, 0))
        new_name_var = tk.StringVar(value=old_superm)
        entry = ttk.Entry(rinomina_popup, textvariable=new_name_var, width=30)
        entry.pack(padx=10, pady=5)
        entry.focus_set()
        def on_confirm(e=None):
            nonlocal SUPERMERCATI
            new_superm = new_name_var.get().strip()
            if not new_superm or new_superm == old_superm:
                rinomina_popup.destroy(); return                
            if new_superm in dati_supermercati:
                self.show_custom_warning("Errore", f"Il supermercato '{new_superm}' esiste già."); return
            if old_superm in dati_supermercati:
                articoli = dati_supermercati.pop(old_superm)
                dati_supermercati[new_superm] = articoli
                for articolo in dati_supermercati[new_superm]: 
                    articolo['supermercato'] = new_superm                    
                try: 
                    index = SUPERMERCATI.index(old_superm)
                    SUPERMERCATI[index] = new_superm
                except ValueError: pass
                if old_superm in campi_input_refs: campi_input_refs[new_superm] = campi_input_refs.pop(old_superm)
                if old_superm in ricerca_vars_crud: ricerca_vars_crud[new_superm] = ricerca_vars_crud.pop(old_superm)
                combo['values'] = tuple(["Seleziona Supermercato"] + sorted(SUPERMERCATI))
                combo.set(new_superm)
                rinomina_popup.destroy()
                _carica_treeview(treeview_crud, new_superm)
                _salva_dati_interno(dati_supermercati)
                if self.risultati_tv_ref: _aggiorna_lista_spesa_intelligente(self.risultati_tv_ref)
                self.show_custom_warning("Successo", f"Supermercato rinominato in '{new_superm}'.")
        btn_frame = ttk.Frame(rinomina_popup, style="Popup.TFrame")
        btn_frame.pack(pady=(10, 10))
        img_annulla = self.icone_gui.get("chiudi")
        btn_annulla = tk.Label(
            btn_frame, 
            compound="left", 
            image=img_annulla, 
            text=" Annulla" if img_annulla else "Annulla", 
            background=self.COLOR_WIDGET_BG, 
            foreground=self.TEXT_COLOR, 
            cursor="hand2", 
            padx=15, 
            pady=6, 
            font=("Arial", 9, "bold")
        )
        btn_annulla.pack(side="left", padx=5)
        btn_annulla.bind("<Button-1>", lambda e: rinomina_popup.destroy())

        img_salva = self.icone_gui.get("salva")
        btn_salva = tk.Label(
            btn_frame, 
            compound="left", 
            image=img_salva, 
            text=" Salva" if img_salva else "Salva", 
            background=self.COLOR_WIDGET_BG, 
            foreground=self.TEXT_COLOR, 
            cursor="hand2", 
            padx=15, 
            pady=6, 
            font=("Arial", 9, "bold")
        )
        btn_salva.pack(side="left", padx=5)
        btn_salva.bind("<Button-1>", lambda e: on_confirm())
        entry.bind("<Return>", on_confirm)
        rinomina_popup.update_idletasks()
        w, h = rinomina_popup.winfo_reqwidth(), rinomina_popup.winfo_reqheight()
        x = popup.winfo_rootx() + (popup.winfo_width() // 2) - (w // 2)
        y = popup.winfo_rooty() + (popup.winfo_height() // 2) - (h // 2)
        rinomina_popup.geometry(f'+{x}+{y}')

    def import_supermercati_db():
        popup.lift() 
        popup.focus_force() 
        file = filedialog.askopenfilename(
            parent=popup,
            title="Importa Database Supermercati",
            defaultextension=".json",
            initialdir=EXP_DB,
            filetypes=[("File JSON", "*supermercati.json"), ("Tutti i file", "*.*")]
        )
        if file:
            if not self.show_custom_askyesno("Conferma Ripristino", "\nSovrascrivere il database attuale dei supermercati?\n"):
                return
            try:
                with open(file, "r", encoding="utf-8") as fsrc:
                    dati_importati = json.load(fsrc) 
                with open(SUPERMERCATI_DB, "w", encoding="utf-8") as fdst:
                    json.dump(dati_importati, fdst, indent=4, ensure_ascii=False) 
                _carica_dati_interno()
                self.after(200, _controlla_scadenza_promo)
                if popup.winfo_exists():
                    popup.destroy()
                    self.deiconify()
                    self.after(0, self.imp_entry.focus_set)
                    self.spesa_supermercato()
                self.show_custom_warning("Importazione completata", f"\nDatabase Supermercati ripristinato da:\n\n {file}\n")
            except json.JSONDecodeError:
                self.show_custom_warning("Errore", f"Errore di lettura JSON. Il file selezionato non è un file di database valido.")
            except Exception as e:
                self.show_custom_warning("Errore", f"Errore durante il ripristino: {e}")
    def export_supermercati_db():
        popup.lift() 
        popup.focus_force() 
        now = datetime.date.today()
        default_dir = EXP_DB
        default_filename = f"{now.day:02d}-{now.month:02d}-{now.year}-supermercati.json"
        file = filedialog.asksaveasfilename(
            parent=popup,
            title="Esporta Database Supermercati",
            defaultextension=".json",
            initialdir=default_dir,
            initialfile=default_filename,
            confirmoverwrite=False,
            filetypes=[("File JSON", "*supermercati.json"), ("Tutti i file", "*.*")]
        )
        if file:
            try:
                with open(SUPERMERCATI_DB, "r", encoding="utf-8") as fsrc:
                    dbdata = fsrc.read()
                with open(file, "w", encoding="utf-8") as fdst:
                    fdst.write(dbdata)
                self.show_custom_warning("Esportazione completata", f"Database Supermercati esportato in {file}")
            except FileNotFoundError:
                self.show_custom_warning("Errore", "Impossibile trovare il database sorgente dei supermercati.")
            except Exception as e:
                self.show_custom_warning("Errore", f"Errore durante l'esportazione: {e}")

    def info_popup():
        popup = tk.Toplevel(frame_gestione, width=550) 
        popup.title("Informazioni sull'Importazione")
        popup.withdraw() 
        popup.transient(frame_gestione)
        messaggio = (
            "Questo programma gestisce i prezzi dei supermercati. 📊\n\n"
            
            "Non è indispensabile inserire tutti i prezzi a mano. \nIl database "
            "prevede l'importazione tramite scontrini digitali.\n\n"
        )
        frame_contenuto = ttk.Frame(popup, padding="2")
        frame_contenuto.pack(expand=True, fill='both')
        ttk.Label(
            frame_contenuto, 
            text=messaggio, 
            wraplength=400,
            justify='left'
        ).pack(pady=10)
        img_check = self.icone_gui.get("check")
        btn_ok_popup = ttk.Label(
            frame_contenuto,
            compound="left",
            image=img_check,
            text=" OK" if img_check else "OK",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2",
            padding=(20, 5)
        )
        btn_ok_popup.image = img_check
        btn_ok_popup.pack(pady=10)
        btn_ok_popup.bind("<Button-1>", lambda e: popup.destroy())
        frame_gestione.update_idletasks()
        popup.update_idletasks() 
        width = popup.winfo_width()
        height = popup.winfo_height()
        MIN_W = 450 
        MIN_H = 200
        if width < MIN_W or height < MIN_H:
             width = max(width, MIN_W)
             height = max(height, MIN_H)
        parent_x = frame_gestione.winfo_rootx() 
        parent_y = frame_gestione.winfo_rooty()
        parent_width = frame_gestione.winfo_width()
        parent_height = frame_gestione.winfo_height()
        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)
        popup.geometry(f'{width}x{height}+{x}+{y}') 
        popup.deiconify() 
        popup.grab_set() 
        popup.bind("<Escape>", lambda e: popup.destroy())
        
    _carica_dati_interno()
    self.after(200, _controlla_scadenza_promo)
    popup = tk.Toplevel(self.master, bg=self.COLOR_TOPLEVEL)
    barra_menu_popup = tk.Menu(popup, bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT, activebackground=self.MENU_ACT_BG_COLOR, activeforeground=self.MENU_ACT_FG_COLOR)
    barra_menu_popup.config(bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT)
    popup.config(menu=barra_menu_popup) 
    menu_db = tk.Menu(barra_menu_popup, tearoff=0,bg=self.MENU_BG, fg=self.MENU_FG_LIGHT, activebackground=self.MENU_ACT_BG_COLOR, activeforeground=self.MENU_ACT_FG_COLOR)
    barra_menu_popup.add_cascade(label="💾 Database", menu=menu_db)       
    menu_db.add_command(label="📤 Esporta Supermercati", command=export_supermercati_db)
    menu_db.add_command(label="📥 Importa Supermercati", command=import_supermercati_db)
    menu_db.add_separator()
    menu_db.add_command(label="⬇️ Controlla Aggiornamento Editor Scontrini", command=self.check_supermarket_update_manuale)
    menu_db.add_command(label="⬇️ Forza Aggiornamento Editor Scontrini", command=self._scarica_editor_esterno)
    menu_db.add_command(label="⬇️ Rimuovi Completamente Editor Scontrini", command=self._rimuovi_editor_esterno)
    menu_db.add_separator()
    menu_db.add_command(label="❌ Chiudi (ESC)", command=lambda: (self.deiconify(), self.after(0, self.imp_entry.focus_set), popup.destroy()))
    self._popup_spesa_active = popup
    popup.title("Gestione e Confronto Spesa")
    popup.geometry("1300x630")
    popup.minsize(1300, 630)
    screen_width = popup.winfo_screenwidth()
    screen_height = popup.winfo_screenheight()
    x = (screen_width - 1300) // 2
    y = (screen_height - 630) // 2
    popup.geometry(f"1200x630+{x}+{y}")
    popup.after(10, lambda: popup.focus_force())
    popup.bind("<Escape>", lambda e: (self.deiconify(), self.after(0, self.imp_entry.focus_set), popup.destroy()))
    self.withdraw()
    threading.Thread(target=self.check_supermarket_update, daemon=True).start()
    def on_popup_close():
        _salva_dati_interno(dati_supermercati)
        try:
            self.popup_calendario.destroy() 
        except:
            pass
        self.popup_calendario = None
        popup.destroy()
        self.deiconify()
        self.after(0, self.imp_entry.focus_set)
    popup.protocol("WM_DELETE_WINDOW", on_popup_close)
    notebook = ttk.Notebook(popup)
    notebook.pack(expand=True, fill='both', padx=10, pady=10)
    frame_lista = ttk.Frame(notebook, padding="10", name='frame_lista')
    notebook.add(frame_lista, text="Lista Spesa Intelligente")
    frame_lista.grid_rowconfigure(1, weight=1)
    frame_lista.grid_rowconfigure(3, weight=2)
    frame_lista.grid_columnconfigure(0, weight=1)
    frame_ricerca_input = ttk.Frame(frame_lista)
    frame_ricerca_input.grid(row=0, column=0, sticky='ew', pady=5)
    frame_ricerca_input.grid_columnconfigure(3, weight=1) 
    ttk.Label(frame_ricerca_input, text="Filtra Supermercato:").grid(row=0, column=0, padx=(5,0), sticky='w')
    combo_filtro_confronto = ttk.Combobox(
        frame_ricerca_input,
        textvariable=filtro_supermercato_confronto_var,
        values=tuple(["Tutti i supermercati"] + sorted(SUPERMERCATI)),
        style="Border.TCombobox",
        state='readonly',
        width=30
    )
    combo_filtro_confronto.grid(row=0, column=1, padx=5, sticky='w')
    ttk.Label(frame_ricerca_input, text="Cerca Articolo (Testo):").grid(row=0, column=2, padx=(15, 0), sticky='w')
    entry_ricerca = ttk.Entry(frame_ricerca_input, textvariable=ricerca_var_confronto)
    entry_ricerca.grid(row=0, column=3, padx=5, sticky='ew')
    img_reset_conf = self.icone_gui.get("reset_campo")
    btn_reset_confronto = ttk.Label(
            frame_ricerca_input,
            image=img_reset_conf,
            text="🔙" if not img_reset_conf else "",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_reset_confronto.image = img_reset_conf
    btn_reset_confronto.grid(row=0, column=4, padx=(5, 5), sticky='w')
    btn_reset_confronto.bind("<Button-1>", lambda e: (
            ricerca_var_confronto.set(""), 
            _aggiorna_lista_spesa_intelligente(risultati_tv)
    ))
    img_cerca_conf = self.icone_gui.get("reset")
    btn_cerca_confronto = ttk.Label(
            frame_ricerca_input,
            compound="left",
            image=img_cerca_conf,
            text=" Cerca/Aggiorna Confronto" if img_cerca_conf else "Cerca/Aggiorna Confronto",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_cerca_confronto.image = img_cerca_conf
    btn_cerca_confronto.grid(row=0, column=5, padx=(10, 5), sticky='e')
    btn_cerca_confronto.bind("<Button-1>", lambda e: _aggiorna_lista_spesa_intelligente(risultati_tv))
    img_help_conf = self.icone_gui.get("help")
    btn_help_confronto = ttk.Label(
            frame_ricerca_input,
            image=img_help_conf,
            text="?" if not img_help_conf else "",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_help_confronto.image = img_help_conf
    btn_help_confronto.grid(row=0, column=6, padx=(5, 5), sticky='w')
    btn_help_confronto.bind("<Button-1>", lambda e: self.mostra_help_supermercati())
    combo_filtro_confronto.bind('<<ComboboxSelected>>', lambda e: _aggiorna_lista_spesa_intelligente(risultati_tv))
    cols_risultati = ("Nome Articolo", "Qtà Catalogo", "Supermercato", "Descrizione", "Categoria", "Prezzo", "Confronto",
"Data Inizio Promo", "Data Scadenza Promo", "Prezzo Intero")
    frame_tv_risultati = ttk.Frame(frame_lista)
    frame_tv_risultati.grid(row=1, column=0, sticky='nsew', pady=5)
    risultati_tv = ttk.Treeview(frame_tv_risultati, columns=cols_risultati, show='headings')
    self.risultati_tv_ref = risultati_tv
    risultati_tv.tag_configure('promo_rossa', foreground='red')
    risultati_tv.tag_configure('piu_conveniente', foreground='green')
    risultati_tv.tag_configure('promo_gialla', foreground='darkorange')
    vbar_res = ttk.Scrollbar(frame_tv_risultati, orient="vertical", command=risultati_tv.yview, style="Vertical.TScrollbar")
    hbar_res = ttk.Scrollbar(frame_tv_risultati, orient="horizontal", command=risultati_tv.xview, style="Horizontal.TScrollbar")
    risultati_tv.configure(yscrollcommand=vbar_res.set, xscrollcommand=hbar_res.set)
    vbar_res.pack(side="right", fill="y")
    hbar_res.pack(side="bottom", fill="x")
    risultati_tv.pack(side="left", fill='both', expand=True)
    risultati_tv.heading("Nome Articolo", text="Articolo"); 
    risultati_tv.heading("Qtà Catalogo", text="Qtà Cat."); 
    risultati_tv.heading("Supermercato", text="Supermercato"); 
    risultati_tv.heading("Prezzo", text="Prezzo")
    risultati_tv.heading("Confronto", text="Confronto")
    risultati_tv.heading("Descrizione", text="Descrizione")
    risultati_tv.heading("Categoria", text="Categoria")
    risultati_tv.column("Descrizione", width=150, stretch=True)
    risultati_tv.column("Categoria", width=130, stretch=False)
    risultati_tv.column("Qtà Catalogo", width=60, anchor='center', stretch=True)
    risultati_tv.column("Prezzo", width=70, anchor='e', stretch=False)
    risultati_tv.column("Confronto", width=80, anchor='center')
    risultati_tv.column("Nome Articolo", width=140, anchor='w', stretch=True)
    risultati_tv.column("Supermercato", width=100, anchor='w', stretch=False)
    risultati_tv.column("Prezzo Intero", width=70, anchor='e', stretch=False)
    risultati_tv.column("Data Inizio Promo", width=80, anchor='center', stretch=False)
    risultati_tv.column("Data Scadenza Promo", width=80, anchor='center', stretch=False)
    for col in cols_risultati:
        text_to_show = {
            "Nome Articolo": "Articolo", 
            "Qtà Catalogo": "Qtà Cat.", 
            "Supermercato": "Supermercato",
            "Descrizione": "Descrizione",
            "Categoria": "Categoria",
            "Prezzo": "Prezzo",
            "Confronto": "Confronto",
            "Prezzo Intero": "Prezzo 🔥", 
            "Data Inizio Promo": "Inizio", 
            "Data Scadenza Promo": "Scadenza"
        }.get(col, col)
        risultati_tv.heading(col, text=text_to_show, command=lambda _col=col, t=risultati_tv: _sort_treeview(t, _col, False))
    frame_legenda = ttk.Frame(frame_lista)
    frame_legenda.grid(row=2, column=0, pady=5, sticky='ew')
    frame_legenda.columnconfigure(0, weight=1)
    frame_riga_unica = ttk.Frame(frame_legenda)
    frame_riga_unica.grid(row=0, column=0)
    ttk.Label(
            frame_riga_unica, 
            text="Doppio Click su Qtà per Modificare | Promo🔥: ", 
            font=('Arial', 8, 'bold')
    ).grid(row=0, column=0)
    ttk.Label(
            frame_riga_unica, 
            text="■ Attiva", 
            foreground="red", 
            font=('Arial', 8, 'bold')
    ).grid(row=0, column=1)
    ttk.Label(frame_riga_unica, text=" | ", font=('Arial', 10, 'bold')).grid(row=0, column=2)
    ttk.Label(
            frame_riga_unica, 
            text="■ Futura", 
            foreground="darkorange", 
            font=('Arial', 8, 'bold')
    ).grid(row=0, column=3)
    ttk.Label(frame_riga_unica, text=" | Miglior Prezzo⭐: ", font=('Arial', 10, 'bold')).grid(row=0, column=4)
    ttk.Label(
            frame_riga_unica, 
            text="■ Assoluto", 
            foreground="green", 
            font=('Arial', 8, 'bold')
    ).grid(row=0, column=5)
    cols_lista_spesa = ("Qtà Catalogo", "Qtà da Comprare", "Prezzo Un. (€)", "Totale (€)", "Supermercato")
    frame_tv_lista = ttk.Frame(frame_lista, name='frame_tv_lista')
    frame_tv_lista.grid(row=3, column=0, sticky='nsew')
    tv_lista_spesa = ttk.Treeview(frame_tv_lista, columns=cols_lista_spesa, show='tree headings')
    vbar_list = ttk.Scrollbar(frame_tv_lista, orient="vertical", command=tv_lista_spesa.yview, style="Vertical.TScrollbar")
    hbar_list = ttk.Scrollbar(frame_tv_lista, orient="horizontal", command=tv_lista_spesa.xview, style="Horizontal.TScrollbar")
    tv_lista_spesa.configure(yscrollcommand=vbar_list.set, xscrollcommand=hbar_list.set)
    vbar_list.pack(side="right", fill="y")
    hbar_list.pack(side="bottom", fill="x")
    tv_lista_spesa.pack(side="left", fill='both', expand=True)
    tv_lista_spesa.heading("#0", text="Articolo/Gruppo")
    heading_map = {
        "Qtà Catalogo": "Qtà Cat.",
        "Qtà da Comprare": "Qtà Ordine",
        "Prezzo Un. (€)": "Prezzo Un. (€)",
        "Totale (€)": "Totale (€)",      
        "Supermercato": "Supermercato"
    }
    for col in cols_lista_spesa: 
        tv_lista_spesa.heading(col, text=heading_map.get(col, col))
    tv_lista_spesa.column("#0", width=180, anchor='w', stretch=True)
    tv_lista_spesa.column("Qtà Catalogo", width=80, anchor='center', stretch=False)
    tv_lista_spesa.column("Qtà da Comprare", width=120, anchor='center', stretch=False)
    tv_lista_spesa.column("Prezzo Un. (€)", width=140, anchor='e', stretch=False)
    tv_lista_spesa.column("Totale (€)", width=100, anchor='e', stretch=False)
    tv_lista_spesa.column("Supermercato", width=120, anchor='center')
    for col in cols_lista_spesa:
        tv_lista_spesa.heading(col, command=lambda _col=col: self.treeview_sort_column(tv_lista_spesa, _col, False))
    risultati_tv.bind('<Double-1>', lambda e, tv_list=tv_lista_spesa, tv_res=risultati_tv: _aggiungi_a_lista_spesa(e, tv_list, tv_res))
    entry_ricerca.bind('<KeyRelease>', lambda e, tv=risultati_tv: _cerca_articoli(ricerca_var_confronto.get(), tv))
    tv_lista_spesa.bind('<Button-1>', lambda e, tv=tv_lista_spesa: _on_edit_quantity(e, tv))
    frame_pulsanti_lista = ttk.Frame(frame_lista)
    frame_pulsanti_lista.grid(row=4, column=0, sticky='ew', pady=5)
    img_cancella = self.icone_gui.get("cancella")
    btn_rimuovi = ttk.Label(
            frame_pulsanti_lista,
            compound="left",
            image=img_cancella,
            text=" Rimuovi Selezionato" if img_cancella else "Rimuovi Selezionato",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_rimuovi.image = img_cancella
    btn_rimuovi.pack(side='left', padx=5)
    btn_rimuovi.bind("<Button-1>", lambda e: _rimuovi_articolo_da_lista(tv_lista_spesa))
    img_svuota = self.icone_gui.get("chiudi")
    btn_svuota = ttk.Label(
            frame_pulsanti_lista,
            compound="left",
            image=img_svuota,
            text=" Svuota Lista" if img_svuota else "Svuota Lista",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_svuota.image = img_svuota
    btn_svuota.pack(side='left', padx=5)
    btn_svuota.bind("<Button-1>", lambda e: _svuota_lista_spesa(tv_lista_spesa))
    img_esci = self.icone_gui.get("chiudi")
    btn_esci_lista = ttk.Label(
            frame_pulsanti_lista,
            compound="left",
            image=img_esci,
            text=" Chiudi" if img_esci else "Chiudi",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_esci_lista.image = img_esci
    btn_esci_lista.pack(side='right', padx=5)
    btn_esci_lista.bind("<Button-1>", lambda e: on_popup_close())
    img_esporta = self.icone_gui.get("salva")
    btn_esporta_lista = ttk.Label(
            frame_pulsanti_lista,
            compound="left",
            image=img_esporta,
            text=" Esporta Lista" if img_esporta else "Esporta Lista",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_esporta_lista.image = img_esporta
    btn_esporta_lista.pack(side='right', padx=5)
    btn_esporta_lista.bind("<Button-1>", lambda e: _mostra_anteprima_esportazione())
    frame_gestione = ttk.Frame(notebook, padding="10")
    notebook.add(frame_gestione, text="Gestione Supermercati")
    frame_gestione.grid_columnconfigure(0, weight=1)
    frame_gestione.grid_rowconfigure(3, weight=1)
    img_carrello = self.icone_gui.get("spesa")
    self.label_conteggio_db = ttk.Label(
            frame_gestione,
            image=img_carrello,
            text="🛒" if not img_carrello else "",
            font=('Arial', 12, 'bold'),
            foreground=self.TEXT_COLOR,
            background=self.COLOR_WIDGET_BG,
            cursor="hand2"
    )
    self.label_conteggio_db.image = img_carrello
    self.label_conteggio_db.bind("<Button-1>", lambda event: info_popup())
    
    self.label_conteggio_db.grid(row=0, column=1, sticky='e', padx=5, pady=5)
    frame_selezione = ttk.Frame(frame_gestione)
    frame_selezione.grid(row=0, column=0, sticky='ew', pady=(0, 10))
    ttk.Label(frame_selezione, text="Seleziona Supermercato da Gestire:").pack(side='left', padx=5)
    combo_supermercato = ttk.Combobox(frame_selezione, textvariable=supermercato_selezionato_var,
                                      values=tuple(["Seleziona Supermercato"] + sorted(SUPERMERCATI)),
                                      style="Border.TCombobox",
                                      state='readonly', width=30, name='combo_gestione_super')
    combo_supermercato.pack(side='left', padx=5)
    supermercato_selezionato_var.set("Seleziona Supermercato")
    img_rinomina = self.icone_gui.get("filtri")
    btn_rinomina_super = ttk.Label(
            frame_selezione,
            compound="left",
            image=img_rinomina,
            text=" Rinomina Selezionato" if img_rinomina else "Rinomina Selezionato",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_rinomina_super.image = img_rinomina
    btn_rinomina_super.pack(side='left', padx=15)
    btn_rinomina_super.bind("<Button-1>", lambda e: _esegui_rinomina_supermercato(
            combo_supermercato, 
            tree_super_crud, 
            ricerca_vars_crud.get(supermercato_selezionato_var.get(), tk.StringVar())
    ))
    if 'combo_gestione_super' not in campi_input_refs:
        campi_input_refs['combo_gestione_super'] = {
            'nome': tk.StringVar(), 'descrizione': tk.StringVar(), 'categoria': tk.StringVar(),
            'prezzo': tk.StringVar(), 'promo_attiva': tk.BooleanVar(), 'prezzo_promo': tk.StringVar(),
            'quantita': tk.StringVar(), 'data_scadenza': tk.StringVar(),
            'data_inserimento_prezzo': tk.StringVar(),
            'data_inizio_promo': tk.StringVar()
        }
    refs_crud = campi_input_refs['combo_gestione_super']
    frame_input = ttk.Frame(frame_gestione)
    frame_input.grid(row=1, column=0, sticky='nw', pady=5)
    ttk.Label(frame_input, text="Nome Articolo:").grid(row=0, column=0, padx=5, pady=2, sticky='w')
    ttk.Entry(frame_input, textvariable=refs_crud['nome'], width=30).grid(row=0, column=1, padx=5, pady=2, sticky='w')
    ttk.Label(frame_input, text="Categoria:").grid(row=0, column=2, padx=5, pady=2, sticky='w')
    combo_categoria = ttk.Combobox(
        frame_input, 
        textvariable=refs_crud['categoria'],
        values=CATEGORIE_PREDEFINITE,
        state='readonly',
        style="Border.TCombobox",
        width=15
    )
    combo_categoria.grid(row=0, column=3, padx=5, pady=2, sticky='w') 
    if CATEGORIE_PREDEFINITE:
        combo_categoria.set(CATEGORIE_PREDEFINITE[0])
    ttk.Label(frame_input, text="Descrizione:").grid(row=1, column=0, padx=5, pady=2, sticky='w')
    ttk.Entry(frame_input, textvariable=refs_crud['descrizione'], width=30).grid(row=1, column=1, padx=5, pady=2, sticky='w')
    ttk.Label(frame_input, text="Quantità (es: 500g):").grid(row=1, column=2, padx=5, pady=2, sticky='w')
    ttk.Entry(frame_input, textvariable=refs_crud['quantita'], width=15).grid(row=1, column=3, padx=5, pady=2, sticky='w')
    ttk.Label(frame_input, text="Prezzo Normale (€):").grid(row=2, column=0, padx=5, pady=2, sticky='w')
    ttk.Entry(frame_input, textvariable=refs_crud['prezzo'], width=15).grid(row=2, column=1, padx=5, pady=2, sticky='w')
    ttk.Label(frame_input, text="Prezzo Promo (€):").grid(row=2, column=2, padx=5, pady=2, sticky='w')
    ttk.Entry(frame_input, textvariable=refs_crud['prezzo_promo'], width=15).grid(row=2, column=3, padx=5, pady=2, sticky='w')
    ttk.Checkbutton(frame_input, text="Articolo in Promozione", variable=refs_crud['promo_attiva']).grid(row=3, column=0, padx=5, pady=5, sticky='w')
    ttk.Label(frame_input, text="Data Inizio Promo:").grid(row=3, column=2, padx=5, pady=2, sticky='w')
    frame_data_inizio_promo = ttk.Frame(frame_input)
    frame_data_inizio_promo.grid(row=3, column=3, padx=5, pady=2, sticky='w')
    entry_data_inizio_promo = ttk.Entry(frame_data_inizio_promo, textvariable=refs_crud['data_inizio_promo'], width=15)
    entry_data_inizio_promo.grid(row=0, column=0, sticky='w')
    img_cal_inizio = self.icone_gui.get("oggi")
    btn_cal_inizio_promo = ttk.Label(
            frame_data_inizio_promo,
            image=img_cal_inizio,
            text="🗓️" if not img_cal_inizio else "",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_cal_inizio_promo.image = img_cal_inizio
    btn_cal_inizio_promo.grid(row=0, column=1, sticky='w', padx=(5, 0))
    btn_cal_inizio_promo.bind(
            "<Button-1>", 
            lambda e: self.mostra_calendario_popup_semplice(
                    entry_data_inizio_promo, 
                    refs_crud['data_inizio_promo']
            )
    )
    ttk.Label(frame_input, text="Data Inserimento Prezzo:").grid(row=4, column=0, padx=5, pady=2, sticky='w')
    frame_data_ins = ttk.Frame(frame_input)
    frame_data_ins.grid(row=4, column=1, padx=5, pady=2, sticky='w')
    entry_data_ins = ttk.Entry(frame_data_ins, textvariable=refs_crud['data_inserimento_prezzo'], width=15)
    entry_data_ins.grid(row=0, column=0, sticky='w')
    img_cal_ins = self.icone_gui.get("oggi")
    btn_cal_inserimento = ttk.Label(
            frame_data_ins,
            image=img_cal_ins,
            text="🗓️" if not img_cal_ins else "",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_cal_inserimento.image = img_cal_ins
    btn_cal_inserimento.grid(row=0, column=1, sticky='w', padx=(5, 0))
    btn_cal_inserimento.bind(
            "<Button-1>", 
            lambda e: self.mostra_calendario_popup_semplice(
                    entry_data_ins, 
                    refs_crud['data_inserimento_prezzo']
            )
    )
    ttk.Label(frame_input, text="Data Scadenza:").grid(row=4, column=2, padx=5, pady=2, sticky='w')
    frame_data_input = ttk.Frame(frame_input)
    frame_data_input.grid(row=4, column=3, padx=5, pady=2, sticky='w')
    entry_data_scadenza = ttk.Entry(frame_data_input, textvariable=refs_crud['data_scadenza'], width=15)
    entry_data_scadenza.grid(row=0, column=0, sticky='w')
    img_cal_scad = self.icone_gui.get("oggi")
    btn_cal_scadenza = ttk.Label(
            frame_data_input,
            image=img_cal_scad,
            text="🗓️" if not img_cal_scad else "",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_cal_scadenza.image = img_cal_scad
    btn_cal_scadenza.grid(row=0, column=1, sticky='w', padx=(5, 0))
    btn_cal_scadenza.bind(
            "<Button-1>", 
            lambda e: self.mostra_calendario_popup_semplice(
                    entry_data_scadenza, 
                    refs_crud['data_scadenza']
            )
    )
    frame_ricerca_crud = ttk.Frame(frame_gestione)
    frame_ricerca_crud.grid(row=2, column=0, sticky='ew', pady=(0, 5))        
    ttk.Label(frame_ricerca_crud, text="Cerca Articolo (Testo):").pack(side='left', padx=5)
    ricerca_var_crud_attuale = tk.StringVar()
    entry_ricerca_crud = ttk.Entry(frame_ricerca_crud, textvariable=ricerca_var_crud_attuale, width=40)
    entry_ricerca_crud.pack(side='left', padx=5, fill='x', expand=True)
    def update_crud_search_var(e=None):
        current_superm = supermercato_selezionato_var.get()
        if current_superm != "Seleziona Supermercato":
            _cerca_articoli_crud(current_superm, tree_super_crud, ricerca_var_crud_attuale)
    def reset_ricerca_crud():
        ricerca_var_crud_attuale.set("") 
        update_crud_search_var()
    img_reset = self.icone_gui.get("reset_campo")
    btn_reset_crud = ttk.Label(
            frame_ricerca_crud,
            image=img_reset,
            text="🔙" if not img_reset else "",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_reset_crud.image = img_reset
    btn_reset_crud.pack(side='left', padx=5)
    btn_reset_crud.bind("<Button-1>", lambda e: reset_ricerca_crud())
    entry_ricerca_crud.bind('<KeyRelease>', update_crud_search_var)
    cols_super = ("Nome", "Descrizione", "Categoria", "Prezzo", "Data Ins.", "Promo", "P. Promo", "Quantità", "Inizio Promo", "Scadenza")
    frame_tv_crud = ttk.Frame(frame_gestione)
    frame_tv_crud.grid(row=3, column=0, sticky='nsew', pady=(5, 0))
    tree_super_crud = ttk.Treeview(frame_tv_crud, columns=cols_super, show='headings')
    tree_super_crud.tag_configure('promo_attiva', foreground='red')
    tree_super_crud.tag_configure('promo_in_arrivo', foreground='orange')
    vbar_tv = ttk.Scrollbar(frame_tv_crud, orient="vertical", command=tree_super_crud.yview, style="Vertical.TScrollbar")
    hbar_tv = ttk.Scrollbar(frame_tv_crud, orient="horizontal", command=tree_super_crud.xview, style="Horizontal.TScrollbar")
    tree_super_crud.configure(yscrollcommand=vbar_tv.set, xscrollcommand=hbar_tv.set)
    vbar_tv.pack(side="right", fill="y")
    hbar_tv.pack(side="bottom", fill="x")
    tree_super_crud.pack(side="left", fill='both', expand=True)
    for col in cols_super:
        text_to_show = col.replace("P. Promo", "Promo €").replace("Data Ins.", "Data Inserita").replace("Inizio Promo", "Inizio Promo").replace("Scadenza", "Scadenza")
        tree_super_crud.heading(col, text=text_to_show, command=lambda _col=col: self.treeview_sort_column(tree_super_crud, _col, False))
    tree_super_crud.column("Promo", width=50, anchor='center', stretch=False)
    tree_super_crud.column("P. Promo", width=70, anchor='e', stretch=False)
    tree_super_crud.column("Quantità", width=80, anchor='center', stretch=False)
    tree_super_crud.column("Prezzo", width=70, anchor='e', stretch=False)
    tree_super_crud.column("Inizio Promo", width=90, anchor='center', stretch=False)
    tree_super_crud.column("Scadenza", width=90, anchor='center', stretch=False)
    tree_super_crud.column("Nome", width=120, anchor='w')
    tree_super_crud.column("Descrizione", width=120, anchor='w')
    tree_super_crud.column("Categoria", width=90, anchor='w')
    tree_super_crud.column("Data Ins.", width=90, anchor='center', stretch=False)
    frame_pulsanti_crud = ttk.Frame(frame_gestione)
    frame_pulsanti_crud.grid(row=4, column=0, sticky='ew', pady=5)
    supermercato_destinazione_var = tk.StringVar() 
    ttk.Label(frame_pulsanti_crud, text="Sposta Articolo").pack(side='left', padx=(20, 5))
    combo_super_sposta = ttk.Combobox(
        frame_pulsanti_crud,
        textvariable=supermercato_destinazione_var,
        values=tuple(sorted(SUPERMERCATI)),
        style="Border.TCombobox",
        state='readonly',
        width=20
    )
    combo_super_sposta.pack(side='left', padx=5)
    img_sposta = self.icone_gui.get("reset_campo")
    btn_sposta_crud = ttk.Label(
            frame_pulsanti_crud,
            compound="left",
            image=img_sposta,
            text=" Sposta" if img_sposta else "Sposta",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_sposta_crud.image = img_sposta
    btn_sposta_crud.pack(side='left', padx=10)
    btn_sposta_crud.bind(
            "<Button-1>", 
            lambda e: _sposta_articolo_tra_super(tree_super_crud, combo_super_sposta)
    )
    def _sposta_articolo_tra_super(treeview_crud, combo_superm_dest):
        selected_item_iid = treeview_crud.focus()
        if not selected_item_iid:
            self.show_custom_warning("Articolo Mancante", "Seleziona un articolo nella tabella da spostare.")
            return
        super_destinazione = combo_superm_dest.get()
        super_corrente = supermercato_selezionato_var.get()
        if not super_destinazione: 
            self.show_custom_warning("Destinazione Mancante", "Seleziona un supermercato di destinazione valido.")
            return
        if super_destinazione == super_corrente:
            self.show_custom_warning("Spostamento Inutile", "L'articolo è già nel supermercato selezionato come destinazione.")
            return
        if not dati_supermercati.get(super_corrente):
            self.show_custom_warning("Errore Dati", "Supermercato di origine non trovato.")
            return
        try:
            iid_parts = selected_item_iid.split('_')
            if len(iid_parts) == 3 and iid_parts[0] == 'item':
                idx_da_rimuovere = int(iid_parts[2])
            else:
                item_values = treeview_crud.item(selected_item_iid, 'values')
                if not item_values:
                    self.show_custom_warning("Errore Dati", "Articolo non trovato nei dati del supermercato corrente.")
                    return
                nome_articolo = item_values[0]
                articoli_correnti = dati_supermercati[super_corrente]
                idx_da_rimuovere = next(i for i, a in enumerate(articoli_correnti) if a.get('nome') == nome_articolo)
            articolo_spostato = dati_supermercati[super_corrente].pop(idx_da_rimuovere)
        except StopIteration:
            self.show_custom_warning("Errore Dati", "Articolo non trovato nei dati del supermercato corrente.")
            return
        except Exception as e:
            self.show_custom_warning("Errore Estrazione", f"Errore durante l'estrazione o rimozione dell'articolo: {e}")
            return
        if super_destinazione not in dati_supermercati:
             dati_supermercati[super_destinazione] = []
        dati_supermercati[super_destinazione].append(articolo_spostato)
        supermercato_destinazione_var.set("")
        self.show_custom_warning("Spostamento Riuscito", f"L'articolo è stato spostato con successo da '{super_corrente}' a '{super_destinazione}'.")
        ricerca_var_attuale = ricerca_vars_crud.get(super_corrente, tk.StringVar())
        _cerca_articoli_crud(super_corrente, treeview_crud, ricerca_var_attuale)
        if hasattr(self, 'risultati_tv_ref') and self.risultati_tv_ref:
            _aggiorna_lista_spesa_intelligente(self.risultati_tv_ref)
        _salva_dati_interno(dati_supermercati)
    def _genera_testo_esportazione_supermercato(supermercato):
        import datetime
        WIDTH_NOME = 29          
        WIDTH_DESC = 20          
        WIDTH_CAT = 20
        WIDTH_QTA = 10           
        WIDTH_PREZZO_N = 8
        WIDTH_PREZZO_P = 8
        WIDTH_PROMO = 5          
        WIDTH_INIZIO_PROMO = 10  
        WIDTH_SCAD = 10          
        WIDTH_DATA_INS = 10      
        EXTRA_SPACE = "  "
        data_esportazione = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        testo = f"═══ CATALOGO SUPERMERCATO: {supermercato.upper()} ({data_esportazione}) ═══\n"
        articoli = dati_supermercati.get(supermercato, [])
        if not articoli:
            testo += "\nNessun articolo registrato per questo supermercato."
            return testo
        articoli.sort(key=lambda x: x.get('nome', ''))
        intestazione = (
            f"{'Nome':<{WIDTH_NOME}} {'Descrizione':<{WIDTH_DESC}} {'Cat.':<{WIDTH_CAT}} " 
            f"{'Qtà':<{WIDTH_QTA}} {'P.N.':>{WIDTH_PREZZO_N}} {'P.P.':>{WIDTH_PREZZO_P}} " 
            f"{'Pr.':<{WIDTH_PROMO}} "                               
            f"{'Iniz.Pr.':<{WIDTH_INIZIO_PROMO}}{EXTRA_SPACE}"  
            f"{'Scad.':<{WIDTH_SCAD}}{EXTRA_SPACE}"             
            f"{'Ins.':<{WIDTH_DATA_INS}}"                            
        )
        separatore = "─" * len(intestazione)
        testo += "\n" + separatore + "\n"
        testo += intestazione + "\n"
        testo += separatore + "\n"
        articoli_incompleti_count = 0
        articoli_esportati_count = 0
        for articolo in articoli:
            nome = articolo.get("nome", "")
            categoria = articolo.get("categoria", "")
            prezzo = str(articolo.get("prezzo", ""))
            mancanze = []
            if not nome: mancanze.append("Nome")
            if not categoria: mancanze.append("Cat")
            if not (prezzo and prezzo.replace('.', '', 1).isdigit()): mancanze.append("Prezzo")
            if mancanze:
                articoli_incompleti_count += 1
                continue 
            articoli_esportati_count += 1
            descrizione = articolo.get("descrizione", "")
            quantita = articolo.get("quantita", "")
            promo = "SI" if articolo.get("promo") else "NO"
            prezzo_promo = str(articolo.get("prezzo_promo", ""))
            data_scadenza = articolo.get("data_scadenza", "")
            data_inizio_promo = articolo.get("data_inizio_promo", "")
            data_inserimento = articolo.get("data_inserimento_prezzo", "") 
            prezzo_fmt = f"{float(prezzo):.2f}"
            promo_fmt = f"{float(prezzo_promo):.2f}" if prezzo_promo and prezzo_promo.replace('.', '', 1).isdigit() else ""
            linea = (
                f"{nome[:WIDTH_NOME-1]:<{WIDTH_NOME}} "
                f"{descrizione[:WIDTH_DESC-1]:<{WIDTH_DESC}} "
                f"{categoria[:WIDTH_CAT-1]:<{WIDTH_CAT}} "
                f"{quantita[:WIDTH_QTA-1]:<{WIDTH_QTA}} "
                f"{prezzo_fmt:>{WIDTH_PREZZO_N}} " 
                f"{promo_fmt:>{WIDTH_PREZZO_P}} " 
                f"{promo:<{WIDTH_PROMO}} "                             
                f"{data_inizio_promo:<{WIDTH_INIZIO_PROMO}}{EXTRA_SPACE}" 
                f"{data_scadenza:<{WIDTH_SCAD}}{EXTRA_SPACE}"             
                f"{data_inserimento:<{WIDTH_DATA_INS}}\n"              
            )
            testo += linea
        testo += separatore + "\n"
        total_articoli = len(articoli)
        testo += f"\n═══ RIEPILOGO DATI ═══\n"
        testo += f"Totale Articoli: {total_articoli}\n"
        testo += f"Articoli Esportati: {articoli_esportati_count}\n"
        testo += f"Articoli Ignorati: {articoli_incompleti_count}\n"
        testo += "═" * len(intestazione) + "\n"
        return testo
    def _mostra_anteprima_esportazione_supermercato(supermercato):
        if supermercato == "Seleziona Supermercato" or not supermercato:
            self.show_toast("Seleziona un supermercato da esportare."); return
        anteprima_text = _genera_testo_esportazione_supermercato(supermercato)
        def _esporta_su_file_super(content_text, default_name, preview_popup):
            preview_popup.destroy()
            f = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("File txt", "*.txt")],
                title=f"Salva Catalogo {supermercato} su File",
                initialdir=EXPORT_FILES,
                confirmoverwrite=False,
                initialfile=default_name,
                parent=popup
            )
            if f:
                try:
                    with open(f, 'w', encoding='utf-8') as file_handle: file_handle.write(content_text)
                    self.show_toast("Catalogo salvato con successo.")
                except Exception as e:
                    self.show_custom_warning("Errore", f"❌ Impossibile salvare il file:\n{e}")
        preview_popup = tk.Toplevel(popup, bg=self.COLOR_TOPLEVEL)
        preview_popup.title(f"Anteprima Esportazione Catalogo: {supermercato}")
        WIDTH = 1200
        HEIGHT = 600
        screen_width = preview_popup.winfo_screenwidth()
        screen_height = preview_popup.winfo_screenheight()
        x = (screen_width - WIDTH) // 2
        y = (screen_height - HEIGHT) // 2
        preview_popup.geometry(f"{WIDTH}x{HEIGHT}+{x}+{y}")
        preview_popup.minsize(WIDTH, HEIGHT)
        preview_popup.after(10, lambda: preview_popup.focus_force())
        preview_popup.bind('<Escape>', lambda e: preview_popup.destroy())
        text_area = tk.Text(preview_popup, wrap='word', font=('Courier', 10), padx=10, pady=10)
        text_area.insert('1.0', anteprima_text)
        text_area.config(state='disabled')
        text_area.pack(fill='both', expand=True, padx=10, pady=10)
        frame_btn = tk.Frame(preview_popup, bg=self.COLOR_TOPLEVEL); frame_btn.pack(pady=(0, 10))
        img_chiudi_popup = self.icone_gui.get("chiudi")
        btn_chiudi_final = ttk.Label(
            frame_btn,
            compound="left",
            image=img_chiudi_popup,
            text=" Chiudi" if img_chiudi_popup else "Chiudi",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
        )
        btn_chiudi_final.image = img_chiudi_popup
        btn_chiudi_final.pack(side='right', padx=5)
        btn_chiudi_final.bind("<Button-1>", lambda e: preview_popup.destroy())
        now = datetime.date.today()
        default_filename = f"Catalogo_{supermercato}_{now.day:02d}_{now.month:02d}_{now.year}.txt"
        img_esporta = self.icone_gui.get("salva")
        btn_esporta = tk.Label(
            frame_btn, 
            compound="left", 
            image=img_esporta, 
            text=" Esporta" if img_esporta else "Esporta", 
            background=self.COLOR_WIDGET_BG, 
            foreground=self.TEXT_COLOR, 
            cursor="hand2", 
            padx=15, 
            pady=6, 
            font=("Arial", 9, "bold")
        )
        btn_esporta.pack(side='left', padx=5)
        btn_esporta.bind(
                    "<Button-1>", 
                    lambda e: _esporta_su_file_super(anteprima_text, default_filename, preview_popup)
        )
        img_stampa_ant = self.icone_gui.get("stampa")
        btn_stampa_anteprima = ttk.Label(
            frame_btn,
            compound="left",
            image=img_stampa_ant,
            text=" Stampa" if img_stampa_ant else "Stampa",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
        )
        btn_stampa_anteprima.image = img_stampa_ant
        btn_stampa_anteprima.pack(side='left', padx=5)
        btn_stampa_anteprima.bind(
            "<Button-1>", 
            lambda e: self._stampa_lista_diretta(
                    anteprima_text, 
                    self.show_custom_warning
            )
    )
    def crud_wrapper(azione, tree, frame_input):
        superm = supermercato_selezionato_var.get()
        if superm == "Seleziona Supermercato":
            self.show_toast("Seleziona un supermercato prima di eseguire l'azione."); return
        _funzione_crud(azione, superm, tree, frame_input)
    img_inserisci = self.icone_gui.get("archivia")
    btn_inserisci = ttk.Label(
            frame_pulsanti_crud,
            compound="left",
            image=img_inserisci,
            text=" Inserisci" if img_inserisci else "Inserisci",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_inserisci.image = img_inserisci
    btn_inserisci.pack(side='left', padx=5)
    btn_inserisci.bind("<Button-1>", lambda e: crud_wrapper('inserisci', tree_super_crud, frame_input))
    img_modifica = self.icone_gui.get("filtri")
    btn_modifica = ttk.Label(
            frame_pulsanti_crud,
            compound="left",
            image=img_modifica,
            text=" Modifica" if img_modifica else "Modifica",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_modifica.image = img_modifica
    btn_modifica.pack(side='left', padx=5)
    btn_modifica.bind("<Button-1>", lambda e: crud_wrapper('modifica', tree_super_crud, frame_input))
    img_salva = self.icone_gui.get("salva")
    btn_salva_mod = ttk.Label(
            frame_pulsanti_crud,
            compound="left",
            image=img_salva,
            text=" Salva Modifiche" if img_salva else "Salva Modifiche",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_salva_mod.image = img_salva
    btn_salva_mod.pack(side='left', padx=5)
    btn_salva_mod.bind("<Button-1>", lambda e: crud_wrapper('salva', tree_super_crud, frame_input))
    img_cancella = self.icone_gui.get("cancella")
    btn_cancella_crud = ttk.Label(
            frame_pulsanti_crud,
            compound="left",
            image=img_cancella,
            text=" Cancella" if img_cancella else "Cancella",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_cancella_crud.image = img_cancella
    btn_cancella_crud.pack(side='left', padx=5)
    btn_cancella_crud.bind("<Button-1>", lambda e: crud_wrapper('cancella', tree_super_crud, frame_input))
    img_scontrini = self.icone_gui.get("oggi")
    btn_importa_scontrini = ttk.Label(
            frame_pulsanti_crud,
            compound="left",
            image=img_scontrini,
            text="Scontrini" if img_scontrini else "Scontrini",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_importa_scontrini.image = img_scontrini
    btn_importa_scontrini.pack(side='left', padx=5)
    btn_importa_scontrini.bind("<Button-1>", lambda e: self._avvia_editor_esterno())
    btn_azzera = ttk.Label(
            frame_pulsanti_crud,
            compound="left",
            image=img_cancella,
            text=" AZZERA Dati" if img_cancella else "AZZERA Dati",
            background=self.COLOR_WIDGET_BG,
            foreground="red",
            cursor="hand2"
    )
    btn_azzera.image = img_cancella
    btn_azzera.pack(side='right', padx=15)
    btn_azzera.bind("<Button-1>", lambda e: _svuota_supermercato(supermercato_selezionato_var.get(), tree_super_crud))
    img_esporta = self.icone_gui.get("stampa")
    btn_esporta_cat = ttk.Label(
            frame_pulsanti_crud,
            compound="left",
            image=img_esporta,
            text="Esporta" if img_esporta else "Esporta",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_esporta_cat.image = img_esporta
    btn_esporta_cat.pack(side='right', padx=5)
    btn_esporta_cat.bind("<Button-1>", lambda e: _mostra_anteprima_esportazione_supermercato(supermercato_selezionato_var.get()))
    combo_supermercato.bind('<<ComboboxSelected>>', 
            lambda e: _on_supermercato_change(e, combo_supermercato, tree_super_crud, frame_input, ricerca_var_crud_attuale))
    _cerca_articoli("", risultati_tv)
    _ricarica_lista_spesa(tv_lista_spesa)
    popup.wait_visibility()
def mostra_help_supermercati(self):
    if not hasattr(self, '_popup_spesa_active') or not self._popup_spesa_active.winfo_exists():
        return 
    parent_window = self._popup_spesa_active
    help_text_lista = """
Obiettivo: Creare una lista spesa ottimizzata, trovando il prezzo migliore per ogni articolo tra tutti i cataloghi registrati.

# A. Sezione Confronto (Tabella Superiore)
1.  Filtro e Ricerca: Utilizza la casella di ricerca e il filtro supermercato per visualizzare solo gli articoli desiderati nel catalogo complessivo.
2.  La Colonna 'Confronto' (Il Cuore Smart):
* Questa colonna esegue il confronto prezzi in tempo reale.
* Se l'articolo costa meno altrove, la colonna ti mostra il costo minimo più basso trovato e in quale supermercato, evidenziando l'opportunità di risparmio.
* La tua scelta finale è sempre basata sulla riga che selezioni.

3.  Aggiunta Articoli e Accumulo Quantità (Doppio Click):
* Doppio click su una riga nella tabella superiore per aggiungere l'articolo alla lista spesa ottimizzata (tabella inferiore).
* Cruciale: Se l'articolo è già presente nella lista inferiore, un ulteriore doppio click su di esso non aggiunge una nuova riga,\n      ma incrementa automaticamente la quantità da comprare di 1 unità.

# B. Sezione Lista Spesa Ottimizzata (Tabella Inferiore)
1.  Ottimizzazione Prezzo/Supermercato: La lista spesa finale suggerisce gli acquisti. La colonna 'Supermercato' indica dove\n
  è consigliato comprare l'articolo per ottenere il prezzo finale più basso.
2.  Modifica Quantità: Fai doppio click sulla cella della colonna 'Qtà da Comprare' per modificare manualmente il numero esatto di unità.
3.  Gestione: Usa i pulsanti Rimuovi Selezionato, Svuota Lista e Esporta Lista per finalizzare e salvare la tua lista spesa ottimizzata.
"""
    help_text_gestione = """
Obiettivo: Mantenere aggiornati i cataloghi (prezzi, promozioni, descrizioni) di ciascun supermercato per garantire un confronto accurato.

# A. Operazioni Base (CRUD)
1.  Selezione Catalogo: Seleziona un supermercato dal ComboBox 'Seleziona Supermercato da Gestire'. La tabella sottostante si popolerà con i suoi articoli.
2.  ➕ Inserisci: Compila tutti i campi di input (Nome Articolo, Categoria, Prezzo, ecc.) e aggiungi un nuovo articolo al catalogo selezionato.
3.   Modifica (Carica): Seleziona un articolo nella tabella e premi 'Modifica' per caricare i suoi dati nei campi di input per l'editing.
4.   Salva Modifiche (Aggiorna): Dopo aver modificato i dati negli input, premi 'Salva Modifiche' per aggiornare l'articolo precedentemente selezionato.
5.  ❌ Cancella: Seleziona un articolo e premi 'Cancella' per rimuoverlo dal catalogo.

# B. Funzionalità Aggiuntive
*  Sposta Articolo: Sposta l'articolo selezionato dal catalogo corrente a un altro supermercato, specificato nel ComboBox di destinazione.
*  Rinomina Selezionato: Permette di cambiare il nome del supermercato selezionato.
*  AZZERA Dati: Attenzione! Cancella TUTTI gli articoli del supermercato selezionato.
*  Esporta Catalogo: Salva l'intero catalogo del supermercato selezionato in un file di testo per backup o consultazione esterna.
*  Importa Scontrini: Strumento per l'importazione e modifica rapida di dati dagli scontrini per popolare il catalogo.

# C. Funzionalità Menu'
*  Importa Supermercati: Carica un archivio contenente l'intero database. ATTENZIONE: Sovrascrive TUTTI i dati esistenti.
*  Esporta Supermercati: Crea un archivio con l'intero database dei cataloghi per un backup completo .
"""
    testo_stampa_completo = (
        "========================================================\n"
        "         GUIDA COMPLETA: LISTA SPESA E CATALOGO\n"
        "========================================================\n\n"
        
        "--- SEZIONE 1: LISTA SPESA INTELLIGENTE ---\n"
        "Obiettivo: Creare una lista spesa ottimizzata, trovando il prezzo migliore per ogni articolo tra tutti i cataloghi registrati.\n\n"
        
        "A. Sezione Confronto (Tabella Superiore)\n"
        "1. Filtro e Ricerca: Utilizza la casella di ricerca e il filtro supermercato per visualizzare solo gli articoli desiderati.\n"
        "2. La Colonna 'Confronto' (Il Cuore Smart): Mostra il costo minimo più basso trovato e il supermercato più conveniente.\n"
        "3. Aggiunta Articoli e Accumulo Quantità (Doppio Click): Doppio click aggiunge l'articolo; se è già presente, incrementa la quantità di 1 unità.\n\n"
        
        "B. Sezione Lista Spesa Ottimizzata (Tabella Inferiore)\n"
        "1. Ottimizzazione Prezzo/Supermercato: La lista suggerisce dove comprare l'articolo per il prezzo più basso.\n"
        "2. Modifica Quantità: Doppio click sulla cella 'Qtà da Comprare' per modificare manualmente.\n"
        "3. Gestione: Usa i pulsanti Rimuovi Selezionato, Svuota Lista e Esporta Lista.\n\n"
        
        "--- SEZIONE 2: GESTIONE SUPERMERCATI ---\n"
        "Obiettivo: Mantenere aggiornati i cataloghi per garantire un confronto accurato.\n\n"
        
        "A. Operazioni Base (CRUD)\n"
        "1. Selezione Catalogo: Scegli il supermercato dal ComboBox per popolare la tabella.\n"
        "2. Inserisci: Compila i campi e aggiungi un nuovo articolo.\n"
        "3. Modifica (Carica): Seleziona un articolo e premi 'Modifica' per caricare i dati.\n"
        "4. Salva Modifiche (Aggiorna): Aggiorna l'articolo con i nuovi dati negli input.\n"
        "5. Cancella: Rimuove l'articolo dal catalogo.\n\n"
        
        "B. Funzionalità Aggiuntive\n"
        "* Sposta Articolo: Sposta l'articolo selezionato a un altro supermercato.\n"
        "* Rinomina Selezionato: Cambia il nome del supermercato.\n"
        "* AZZERA Dati: ATTENZIONE! Cancella TUTTI gli articoli del supermercato selezionato.\n"
        "* Esporta Catalogo: Salva l'intero catalogo in un file di testo.\n"
        "* Importa Scontrini: Strumento per l'importazione e modifica rapida di dati dagli scontrini.\n\n"
        
        "C. Funzionalità Menu\n"
        "* Importa Supermercati: Carica un archivio contenente l'intero database. ATTENZIONE: Sovrascrive TUTTI i dati esistenti.\n"
        "* Esporta Supermercati: Crea un archivio con l'intero database dei cataloghi per un backup completo."
    )
    def _crea_text_area(parent_frame, content):
        text_container = ttk.Frame(parent_frame)
        text_container.pack(fill='both', expand=True)
        text_area = tk.Text(text_container, wrap='word', font=('Arial', 10), 
                            padx=10, pady=10, background='#f0f0f0', borderwidth=0)
        text_area.insert('1.0', content)
        text_area.config(state='disabled') 
        scrollbar = ttk.Scrollbar(text_container, command=text_area.yview, style="Vertical.TScrollbar")
        text_area.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        text_area.pack(side='left', fill='both', expand=True)
    help_popup = tk.Toplevel(parent_window, bg=self.COLOR_TOPLEVEL) 
    help_popup.title("Guida Completa: Catalogo e Lista Spesa Intelligente")
    WIDTH = 1200
    HEIGHT = 630
    help_popup.resizable(False, False)
    screen_width = help_popup.winfo_screenwidth()
    screen_height = help_popup.winfo_screenheight()
    x = (screen_width - WIDTH) // 2
    y = (screen_height - HEIGHT) // 2
    help_popup.geometry(f"{WIDTH}x{HEIGHT}+{x}+{y}")
    help_popup.transient(parent_window)
    help_popup.bind("<Escape>", lambda e: help_popup.destroy())
    help_popup.protocol("WM_DELETE_WINDOW", help_popup.destroy)
    help_popup.update_idletasks() 
    help_popup.wait_visibility()
    help_popup.grab_set()
    help_popup.focus_force()
    main_frame = ttk.Frame(help_popup, padding="15")
    main_frame.pack(fill='both', expand=True)
    ttk.Label(main_frame, text="Guida all'Utilizzo delle Schede", 
              font=('Arial', 14, 'bold')).pack(pady=(0, 15))
    notebook_help = ttk.Notebook(main_frame)
    notebook_help.pack(expand=True, fill='both')
    frame_help_lista = ttk.Frame(notebook_help, padding="10")
    notebook_help.add(frame_help_lista, text="Lista Spesa Intelligente")
    _crea_text_area(frame_help_lista, help_text_lista)
    frame_help_gestione = ttk.Frame(notebook_help, padding="10")
    notebook_help.add(frame_help_gestione, text="Gestione Supermercati (CRUD)")
    _crea_text_area(frame_help_gestione, help_text_gestione)
    btn_frame = ttk.Frame(help_popup, padding=(15, 0))
    btn_frame.pack(fill='x', padx=15, pady=(5, 15))
    img_stampa_help = self.icone_gui.get("stampa")
    btn_stampa_guida_help = ttk.Label(
            btn_frame,
            compound="left",
            image=img_stampa_help,
            text=" Stampa Guida" if img_stampa_help else "Stampa Guida",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_stampa_guida_help.image = img_stampa_help
    btn_stampa_guida_help.pack(side=tk.LEFT, padx=10, pady=5)
    btn_stampa_guida_help.bind(
            "<Button-1>", 
            lambda e: self._stampa_lista_diretta(
                    testo_stampa_completo, 
                    self.show_custom_warning
            )
    )
    img_check_help = self.icone_gui.get("check")
    btn_ok_help = ttk.Label(
            btn_frame,
            compound="left",
            image=img_check_help,
            text=" Ho Capito (OK)" if img_check_help else "Ho Capito (OK)",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_ok_help.image = img_check_help
    btn_ok_help.pack(side=tk.RIGHT, padx=10, pady=5)
    btn_ok_help.bind("<Button-1>", lambda e: help_popup.destroy())
    help_popup.wait_window(help_popup)

