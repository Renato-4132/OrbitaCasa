#!/usr/bin/env python3

import os
import json
import sys
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from concurrent.futures import ThreadPoolExecutor
import uuid 
import operator

try:
    from google import genai
    from google.genai.errors import APIError
except ImportError:
    messagebox.showerror("Errore Librerie", "La libreria 'google-genai' non è installata. Esegui: pip install google-genai")
    sys.exit(1)
    
DEFAULT_API_KEY = ""

VERSIONE_APP = "1.3"

BASE_DIR_APP = os.path.dirname(os.path.abspath(sys.argv[0]))
DB_DIR_NAME = "db"
DB_DIR_PATH = os.path.join(BASE_DIR_APP, DB_DIR_NAME)
ICON_PATH = os.path.join(DB_DIR_PATH, "casa-facile.png")
SUPERMERCATI_DB = os.path.join(DB_DIR_PATH, "supermercati.json")
DEFAULT_API = os.path.join(DB_DIR_PATH, "api.json")

CATEGORIE_PREDEFINITE = [
    "Acqua", "Carne", "Pollame", "Affettati", "Salumi", "Pesce", "Molluschi/Crosta", 
    "Sushi e Tartare", "Uova", "Frutta Fresca", "Verdura Fresca", "Ortaggi e Tuberi", 
    "Insalate Pronte", "Latte e Burro", "Formaggi Freschi", "Formaggi Stagion.", 
    "Latticini e Yogurt", "Pane e Panini", "Snack Panetteria", "Pasta Secca", 
    "Pasta Fresca", "Farine e Lieviti", "Riso", "Legumi Secchi/Scat", 
    "Cereali Colazione", "Salse e Condimenti", "Sottoli/Sottaceti", "Conserve Pesce", 
    "Cibi Etnici", "Caffè e Bevande", "Dolciumi e Caram", "Cioccolato", "Biscotti", 
    "Marmellate/Creme", "Merende e Snack", "Snack Salati", "Succhi/Bibite", "Birre", 
    "Vini e Spumanti", "Liquori e Distil.", "Gastronomia", "Piatti Pronti", 
    "Surgelati Verdura", "Surgelati Pesce", "Surgelati Vari", "Pizze Surgelate", 
    "Gelati", "Igiene Persona", "Cura del Corpo", "Cura dei Capelli", "Cosmetici", 
    "Assorbenza", "Integratori/Sanit", "Bucato", "Pulizia Casa", "Spugne e Guanti", 
    "Carta Casa/Igien", "Carta e Alluminio", "Casalinghi/Tessile", "Giardino e Fai da", 
    "Auto e Elettronica", "Animali Domestici", "Articoli Bimbi", "Cancelleria/Party", 
    "Varie", "Prodotti Bio", "Prodotti Veg/Vegan", "Prodotti Dietetici",
]

MAPPATURA_SUPERMERCATI = {
    "esselunga": "Esselunga", "coop": "Coop", "lidl": "Lidl", "eurospin": "Eurospin",
    "maury": "Maurys", "maurys": "Maurys", "d più": "Dpiu", "dpiu": "Dpiu" 
}

class ScontrinoParserApp:
    
    def __init__(self, master):
        self.master = master
        master.title(f"🤖 Gestore Database & Estrazione Scontrini ( Ver. {VERSIONE_APP} )")
        self.master.protocol("WM_DELETE_WINDOW", self._on_close)
        self.api_key = tk.StringVar(value=DEFAULT_API_KEY)
        self._carica_api()
        self.db_search_query = tk.StringVar() 
        self.gemini_search_query = tk.StringVar()
        
        self.lista_file = []
 
        self.dati_gemini_piatti = {}
        self.dati_db_piatti = {}
        self.db_file_path = None
        
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.gemini_client = None

        self.tree_gemini = None
        self.tree_db = None
        self.log_text = None
        self.db_path_label = None
        self.file_label = None 
        
        self._crea_interfaccia()

    def _log(self, message, is_error=False):
        tag = 'error' if is_error else 'normal'
        def _insert_log():
            self.log_text.insert(tk.END, f"{'❌ ERRORE: ' if is_error else ''}{message}\n", tag)
            self.log_text.see(tk.END)
        self.master.after_idle(_insert_log)


    def _cleanup_json(self, raw_text):
        if raw_text.startswith('```'):
            raw_text = raw_text.lstrip('`json\n').rstrip('`').strip()
        
        start_index = raw_text.find('{')
        end_index = raw_text.rfind('}')
        if start_index != -1 and end_index != -1 and end_index > start_index:
            return raw_text[start_index : end_index + 1]
            
        return raw_text

    def mappa_supermercato(self, nome_estratto):
        if not nome_estratto: return "Varie"
        nome_pulito = nome_estratto.lower().replace('.', '').replace('s.p.a', '').split('-')[0].strip()
        for chiave, valore in MAPPATURA_SUPERMERCATI.items():
            if chiave in nome_pulito: return valore
        if "d+p" in nome_pulito: return "Dpiu"
        return "Varie"

    def _appiattisci_a_piatto(self, dati_gerarchici):
        dati_piatti = {}
        for supermercato, articoli in dati_gerarchici.items():
            for art in articoli:
                item_id = str(uuid.uuid4())
                dati_piatti[item_id] = {'supermercato': supermercato, 'articolo': art}
        return dati_piatti

    def _appiattisci_a_gerarchico(self, dati_piatti):
        dati_gerarchici = {}
        for key, entry in dati_piatti.items():
            supermercato = entry['supermercato']
            articolo = entry['articolo']
            
            if supermercato not in dati_gerarchici: dati_gerarchici[supermercato] = []
 
            is_duplicate = False
            for existing_art in dati_gerarchici[supermercato]:
                if existing_art.get('nome') == articolo.get('nome') and existing_art.get('prezzo') == articolo.get('prezzo'):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                dati_gerarchici[supermercato].append(articolo)
                
        return dati_gerarchici

    def _carica_db_da_file(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                dati_gerarchici = json.load(f)
                return self._appiattisci_a_piatto(dati_gerarchici) if isinstance(dati_gerarchici, dict) else {}
        except Exception as e:
            self._log(f"Errore caricamento DB: {e}", is_error=True)
            return {}

    def _salva_db_su_file(self, filepath, dati_piatti):
        try:
            dati_gerarchici = self._appiattisci_a_gerarchico(dati_piatti)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(dati_gerarchici, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            self._log(f"ERRORE nel salvataggio del DB: {e}", is_error=True)
            return False

    def _crea_treeview(self, parent, is_db_tree=False):
        columns = ("Supermercato", "Nome Articolo", "Descrizione", "Categoria", "Quantità", "Prezzo")
        tree = ttk.Treeview(parent, columns=columns, show='headings', selectmode='extended', 
                            style='Custom.Treeview') 
        tree.sort_direction = {}
        col_widths = {"Supermercato": 120, "Nome Articolo": 120, "Descrizione": 150, "Categoria": 100, "Quantità": 80, "Prezzo": 80}
        for col in columns:
            width = col_widths.get(col, 100)
            anchor = tk.W if col not in ['Quantità', 'Prezzo'] else tk.E
            tree.column(col, width=width, anchor=anchor)
            tree.heading(col, text=col, 
                         command=lambda c=col: self._sort_column(tree, c, is_db_tree)) 
        tree.bind('<Double-1>', lambda e: self._on_cell_edit(e, tree, is_db_tree))
        
        tree.column("#0", width=0, stretch=tk.NO)
        tree.pack(fill='both', expand=True)
        return tree

    def _ricarica_treeview(self, tree, dati_piatti_source):
        for item in tree.get_children(): tree.delete(item)
        is_db_tree = (tree == self.tree_db)
        dati_da_mostrare = dati_piatti_source
        query = ""
        if is_db_tree:
            query = self.db_search_query.get().lower().strip()
        else: 
            query = self.gemini_search_query.get().lower().strip()
        if query:
            dati_filtrati = {}
            for item_id, entry in dati_piatti_source.items():
                articolo = entry['articolo']
                search_text = f"{entry['supermercato']} {articolo.get('nome', '')} {articolo.get('descrizione', '')} {articolo.get('categoria', '')}".lower()
                if query in search_text:
                    dati_filtrati[item_id] = entry
            dati_da_mostrare = dati_filtrati
        for item_id, entry in dati_da_mostrare.items():
            articolo = entry['articolo']
            supermercato = entry['supermercato']
            nome_display = articolo.get('nome', articolo.get('descrizione', 'N/D'))
            descrizione = articolo.get('descrizione', '') 
            quantita_valore = articolo.get('quantita', '1 pz')       
            categoria = articolo.get('categoria', 'Varie') 
            prezzo = articolo.get('prezzo', '0.00')
            try:
                 prezzo_float = float(str(prezzo).replace(',', '.'))
                 prezzo = f"{prezzo_float:.2f}" 
            except: pass
            tree.insert(
                '', 'end', iid=item_id,
                values=(supermercato, nome_display, descrizione, categoria, quantita_valore, prezzo) 
            )
        tree.update_idletasks() 
        if tree.sort_direction:
            col = next(iter(tree.sort_direction)) 
            current_direction = tree.sort_direction[col]
            tree.sort_direction[col] = not current_direction
            self._sort_column(tree, col, is_db_tree)


    def _crea_interfaccia(self):
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill='both', expand=True)
        input_frame = ttk.LabelFrame(main_frame, text="Configurazione & Estrazione Scontrini", padding="10")
        input_frame.pack(fill='x', pady=5)
        ttk.Label(input_frame, text="Chiave API Gemini:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        #api_entry = ttk.Entry(input_frame, textvariable=self.api_key, width=50, show='*')
        api_entry = ttk.Entry(input_frame, textvariable=self.api_key, width=50)
        api_entry.grid(row=0, column=1, sticky='ew', padx=5, pady=2)
        ttk.Button(input_frame, text="📂 Scegli File/i JPG", command=self._seleziona_file, style='Custom.TButton').grid(row=0, column=2, padx=10, pady=2)
        ttk.Button(input_frame, text="🚀 Avvia Estrazione", style='Accent.TButton', command=self._avvia_elaborazione).grid(row=1, column=2, padx=10, pady=5)
        self.file_label = ttk.Label(input_frame, text="Nessun file selezionato.", foreground='gray')
        self.file_label.grid(row=1, column=0, columnspan=2, sticky='w', padx=5, pady=2)
        panels_frame = ttk.Frame(main_frame)
        panels_frame.pack(fill='both', expand=True, pady=10)
        gemini_frame = ttk.LabelFrame(panels_frame, text="1. Risultati Estrazione Gemini (Temporaneo) - Doppio Click per Modificare", padding="5")
        gemini_frame.pack(side='left', fill='both', expand=True, padx=5)
        gemini_search_frame = ttk.Frame(gemini_frame)
        gemini_search_frame.pack(fill='x')
        ttk.Label(gemini_search_frame, text="Cerca su Gemini:").pack(side='left', padx=5, pady=2)
        gemini_search_entry = ttk.Entry(gemini_search_frame, textvariable=self.gemini_search_query)
        gemini_search_entry.pack(side='left', fill='x', expand=True, pady=2)
        gemini_search_entry.bind('<KeyRelease>', self._filter_gemini_tree) 
        self.tree_gemini = self._crea_treeview(gemini_frame, is_db_tree=False)
        gemini_controls_frame = ttk.Frame(gemini_frame)
        gemini_controls_frame.pack(fill='x', pady=5)
        ttk.Button(gemini_controls_frame, text="❌ Cancella Selezionati", command=lambda: self._cancella_selezionati(self.tree_gemini, is_db=False), style='Custom.TButton').pack(side='left', padx=5)
        ttk.Button(gemini_controls_frame, text="→ Copia Selezionati nel DB →", command=self._copia_a_db, style='Accent.TButton').pack(side='right', padx=5)
        db_frame = ttk.LabelFrame(panels_frame, text="2. Database Completo - Doppio Click per Modificare", padding="5")
        db_frame.pack(side='left', fill='both', expand=True, padx=5)
        search_frame = ttk.Frame(db_frame)
        search_frame.pack(fill='x')
        ttk.Label(search_frame, text="Cerca nel DB:").pack(side='left', padx=5, pady=2)
        search_entry = ttk.Entry(search_frame, textvariable=self.db_search_query)
        search_entry.pack(side='left', fill='x', expand=True, pady=2)
        search_entry.bind('<KeyRelease>', self._filter_db_tree) 
        self.tree_db = self._crea_treeview(db_frame, is_db_tree=True)
        db_controls_frame = ttk.Frame(db_frame)
        db_controls_frame.pack(fill='x', pady=5)
        ttk.Button(db_controls_frame, text="❌ Chiudi", command=self._on_close, style='Giallo.TButton').pack(side='right', padx=10)
        ttk.Button(db_controls_frame, text="⬆️ Carica DB Esistente", command=self._carica_db, style='Custom.TButton').pack(side='left', padx=5)
        self.db_path_label = ttk.Label(db_controls_frame, text="DB: Non Caricato", foreground='blue')
        self.db_path_label.pack(side='left', padx=10)
        ttk.Button(db_controls_frame, text="💾 Salva DB", command=self._salva_db, style='Accent.TButton').pack(side='right', padx=5)
        ttk.Button(db_controls_frame, text="❌ Cancella Selezionati", command=lambda: self._cancella_selezionati(self.tree_db, is_db=True), style='Custom.TButton').pack(side='right', padx=10)
        log_frame = ttk.LabelFrame(main_frame, text="Log Elaborazione", padding="5")
        log_frame.pack(fill='x', pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=6, font=('Courier', 9))
        self.log_text.pack(fill='both', expand=True)
        self.log_text.tag_config('error', foreground='red', background='#ffe6e6')

    def _seleziona_file(self):
        f_types = [('Immagini JPG/PNG', '*.jpg *.jpeg *.png'), ('Tutti i file', '*.*')]
        file_paths = filedialog.askopenfilenames(
            title="Seleziona Scontrini (JPG, PNG)",
            filetypes=f_types
        )
        if file_paths:
            self.lista_file = list(file_paths)
            self.file_label.config(text=f"Selezionati {len(self.lista_file)} file.")
            self._log(f"Caricati {len(self.lista_file)} file per l'elaborazione.")
            self.dati_gemini_piatti = {}
            self._ricarica_treeview(self.tree_gemini, self.dati_gemini_piatti)


    def estrai_scontrino_gemini(self, nome_file):
        if not self.gemini_client: return None
        self._log(f"1. Invio a Gemini: {os.path.basename(nome_file)}...")
        immagine = None
        try:
            immagine = self.gemini_client.files.upload(file=nome_file)
        except Exception as e:
            self._log(f"ERRORE caricamento file: {e}", is_error=True); return None
        istruzioni = f"""
        Sei un parser di scontrini altamente preciso. Analizza attentamente l'immagine del scontrino.
        Requisiti ESSENZIALI: 1. Estrai il nome completo del supermercato. 2. Estrai SOLO le righe degli articoli acquistati. 3. IGNORA CATEGORICAMENTE righe di sconto/totali. 4. "prezzo" deve riflettere il PREZZO LORDO. 5. "articolo" (nome) traccia ESATTA dallo scontrino (max 20 char). 6. "descrizione" pulita (max 20 char). 7. Estrai la "quantità" (es: "1 pz"). 8. Assegna categoria dalla lista: {", ".join(CATEGORIE_PREDEFINITE)}
        Restituisci la risposta ESCLUSIVAMENTE come un oggetto JSON Python valido.
        Formato DEVE essere: {{ "supermercato": "Nome Supermercato Estratto", "articoli": [ {{ "articolo": "...", "quantita": "...", "prezzo": 1.98, "categoria": "...", "descrizione": "..." }}, ... ] }}
        """

        risultato_completo = None
        try:
            response = self.gemini_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[istruzioni, immagine]
            )
            raw_text = response.text.strip()
            cleaned_json = self._cleanup_json(raw_text)
            self._log(f"DEBUG: Risposta RAW (primi 100 char): {raw_text[:100]}...")
            risultato_completo = json.loads(cleaned_json) 
        except json.JSONDecodeError as e:
            self._log(f"ERRORE JSON: Impossibile parsare la risposta di Gemini. Controlla il JSON RAW. Errore: {e}", is_error=True)
        except Exception as e:
            self._log(f"ERRORE Gemini/Parsing per {os.path.basename(nome_file)}: {e}", is_error=True)
        finally:
            if immagine: self.gemini_client.files.delete(name=immagine.name)
        return risultato_completo

    def _avvia_elaborazione(self):
        if not self.lista_file or not self.api_key.get():
            self.show_custom_warning("Attenzione", "Seleziona file e inserisci la Chiave API.")
            return
        try:
            self.gemini_client = genai.Client(api_key=self.api_key.get())
        except Exception as e:
            self.show_custom_warning("Errore Chiave API", f"Controlla la chiave. Errore: {e}")
            return
        self._ricarica_treeview(self.tree_gemini, {})
        self.dati_gemini_piatti = {}
        self._log(f"Avvio elaborazione per {len(self.lista_file)} file...")
        self.future = self.executor.submit(self._esegui_elaborazione_thread)
        self.master.after(100, self._check_elaborazione_thread)
        
    def _esegui_elaborazione_thread(self):
        dati_grezzi = []
        for percorso_completo_file in self.lista_file:
            risultato_completo = self.estrai_scontrino_gemini(percorso_completo_file)
            if risultato_completo and 'articoli' in risultato_completo and 'supermercato' in risultato_completo:
                nome_supermercato_mappato = self.mappa_supermercato(risultato_completo['supermercato'])
                for item in risultato_completo['articoli']:
                    item['supermercato'] = nome_supermercato_mappato 
                    item['articolo_nome'] = str(item.get('articolo', 'N/D'))[:20]
                    item['descrizione_finale'] = str(item.get('descrizione', 'N/D'))[:20]
                    dati_grezzi.append(item)
        return dati_grezzi
    
    def _check_elaborazione_thread(self):
        if self.future.running():
            self.master.after(100, self._check_elaborazione_thread)
            return
        try:
            dati_grezzi = self.future.result()
            self._consolida_e_popola_gemini(dati_grezzi)
            self._log("✅ ELABORAZIONE COMPLETA. Articoli pronti per il trasferimento.")
        except Exception as e:
            self._log(f"❌ Errore inaspettato nell'elaborazione finale: {e}", is_error=True)

    def _consolida_e_popola_gemini(self, dati_grezzi):
        unique_items = {} 
        for item_estratto in dati_grezzi:
            try:
                prezzo_normalizzato = float(str(item_estratto.get('prezzo', 0.0)).replace(',', '.'))
                unique_key = (
                    item_estratto['supermercato'],
                    item_estratto['articolo_nome'].lower(),
                    round(prezzo_normalizzato, 2),
                    item_estratto.get('categoria', 'Varie')
                )
                unique_items[unique_key] = item_estratto
            except Exception as e:
                self._log(f"⚠️ Articolo non consolidabile (Prezzo non valido?): {item_estratto.get('articolo_nome')} - Errore: {e}", is_error=False)
        self.dati_gemini_piatti = {}
        for item_estratto in unique_items.values():
            supermercato_key = item_estratto['supermercato']
            prezzo_str = str(item_estratto.get('prezzo', 0.0)).replace(',', '.')
            articolo_formattato = {
                "nome": item_estratto['articolo_nome'].title(),
                "descrizione": item_estratto['descrizione_finale'], 
                "categoria": item_estratto.get('categoria', 'Varie'),
                "prezzo": f"{float(prezzo_str):.2f}",
                "promo": False, "prezzo_promo": "",
                "supermercato": supermercato_key,
                "quantita": item_estratto.get('quantita', '1 pz') 
            }
            item_id = str(uuid.uuid4())
            self.dati_gemini_piatti[item_id] = {'supermercato': supermercato_key, 'articolo': articolo_formattato}
        self._ricarica_treeview(self.tree_gemini, self.dati_gemini_piatti)
        self._log(f"Consolidati {len(self.dati_gemini_piatti)} articoli unici dai nuovi scontrini.")

    def _on_cell_edit(self, event, tree, is_db):
        item_id = tree.identify_row(event.y)
        column_id = tree.identify_column(event.x)
        if not item_id or column_id == '#0': return 
        col_index = int(column_id.replace('#', '')) - 1
        col_name = tree['columns'][col_index]
        col_to_field = {
            1: 'supermercato', 2: 'nome', 3: 'descrizione', 
            4: 'categoria', 5: 'quantita', 6: 'prezzo'
        }
        field_name = col_to_field.get(col_index + 1)
        if not field_name: return
        x, y, width, height = tree.bbox(item_id, column_id)
        dati_ref = self.dati_db_piatti if is_db else self.dati_gemini_piatti
        if item_id not in dati_ref: return
        if field_name == 'supermercato':
            current_value = dati_ref[item_id].get(field_name)
        else:
            current_value = dati_ref[item_id]['articolo'].get(field_name)
            
        def save_edit(event_or_value):
            if not isinstance(event_or_value, str):
                 if not tree.winfo_exists(): return
                 new_value = edit_widget.get()
            else:
                 new_value = event_or_value
            if new_value is not None and str(new_value).strip() != str(current_value).strip():
                new_value = str(new_value).strip()
                if field_name == 'prezzo':
                    try:
                        float_val = float(new_value.replace(',', '.'))
                        new_value = f"{float_val:.2f}"
                    except ValueError:
                        self.show_custom_warning("Errore Input", f"Il campo '{col_name}' richiede un valore numerico valido.")
                        return
                if field_name == 'supermercato':
                    dati_ref[item_id][field_name] = new_value
                else:
                    dati_ref[item_id]['articolo'][field_name] = new_value
                tree.set(item_id, column_id, new_value)
                self._log(f"Aggiornata riga ID {item_id[:4]}...: {col_name} → '{new_value}'")
            if 'edit_widget' in locals() and edit_widget.winfo_exists():
                edit_widget.destroy()
        edit_font = ('Arial', 8, 'normal') 
        if col_name == 'Categoria':
            edit_widget = ttk.Combobox(tree, values=CATEGORIE_PREDEFINITE, font=edit_font)
            edit_widget.set(current_value)
            edit_widget.place(x=x, y=y, width=width, height=height)
            edit_widget.focus_set()
            edit_widget.bind("<<ComboboxSelected>>", lambda e: save_edit(edit_widget.get()))
            edit_widget.bind("<FocusOut>", lambda e: edit_widget.destroy())
        else:
            edit_widget = ttk.Entry(tree, font=edit_font)
            edit_widget.insert(0, current_value)
            edit_widget.place(x=x, y=y, width=width, height=height)
            edit_widget.focus_set()
            edit_widget.bind('<Return>', save_edit) 
            edit_widget.bind('<FocusOut>', save_edit) 
        return "break"

    def _sort_column(self, tree, col, is_db_tree):
        direzione = tree.sort_direction.get(col, True)
        data = [(tree.set(item, col), item) for item in tree.get_children('')]
        if col in ("Quantità", "Prezzo"):
            def sort_key(item_value):
                val = item_value[0].replace(',', '.').replace(' ', '').replace('€', '').replace('pz', '')
                try:
                    return float(val)
                except ValueError:
                    return 0.0
        else:
            def sort_key(item_value):
                return item_value[0].lower()
        data.sort(key=sort_key, reverse=not direzione) 
        for index, (value, item_id) in enumerate(data):
            tree.move(item_id, '', index) 
        tree.sort_direction[col] = not direzione
        for c in tree['columns']:
            tree.heading(c, text=tree.heading(c, 'text').split()[0]) 
        freccia = ' ▲' if direzione else ' ▼' 
        tree.heading(col, text=f"{col}{freccia}")

    def _filter_db_tree(self, event):
        self._ricarica_treeview(self.tree_db, self.dati_db_piatti)
        self._log(f"Filtro DB ricaricato per: '{self.db_search_query.get()}'")

    def _filter_gemini_tree(self, event):
        self._ricarica_treeview(self.tree_gemini, self.dati_gemini_piatti)
        self._log(f"Filtro Gemini ricaricato per: '{self.gemini_search_query.get()}'")

    def _copia_a_db(self):
        selected_items = self.tree_gemini.selection()
        if not selected_items:
            self.show_custom_warning("Selezione", "Seleziona prima gli articoli da trasferire dai risultati Gemini.")
            return

        articoli_trasferiti = 0
        
        for item_id in selected_items:
            if item_id in self.dati_gemini_piatti:
                entry = self.dati_gemini_piatti[item_id]
                new_db_id = str(uuid.uuid4())
                self.dati_db_piatti[new_db_id] = entry 
                articoli_trasferiti += 1
        self._ricarica_treeview(self.tree_db, self.dati_db_piatti)
        self._log(f"Copiati {articoli_trasferiti} articoli nel Database Completo.")
        self.show_custom_warning("Trasferimento", f"Copiati {articoli_trasferiti} articoli nel Database Completo. (Resta su Gemini)")

    def _cancella_selezionati(self, tree, is_db):
        selected_items = tree.selection()
        if not selected_items:
            self.show_custom_warning("Cancellazione", "Seleziona gli elementi da cancellare.")
            return
        dati_ref = self.dati_db_piatti if is_db else self.dati_gemini_piatti
        for item_id in selected_items:
            if item_id in dati_ref:
                del dati_ref[item_id]
        self._ricarica_treeview(tree, dati_ref)
        self._log(f"Cancellati {len(selected_items)} elementi dal pannello {'DB Completo' if is_db else 'Gemini'}.")

    def _carica_db(self):
        default_path = SUPERMERCATI_DB
        if os.path.exists(default_path):
            dati_caricati = self._carica_db_da_file(default_path)
            if dati_caricati is not None:
                self.dati_db_piatti = dati_caricati
                self.db_file_path = default_path
                self._ricarica_treeview(self.tree_db, self.dati_db_piatti) 
                self.db_path_label.config(text=f"DB: {os.path.basename(default_path)}")
                self._log(f"✅ Caricato Database di Default da {os.path.basename(default_path)} ({len(dati_caricati)} articoli).")
                return True
        self._log("⚠️ Database di Default non trovato o vuoto.")
        return False

    def _salva_db(self):
        if not self.dati_db_piatti:
            self.show_custom_warning("Salvataggio", "Nessun dato nel Database Completo da salvare.")
            return
        filepath = SUPERMERCATI_DB 
        db_directory = os.path.dirname(filepath)
        os.makedirs(db_directory, exist_ok=True)
        if self._salva_db_su_file(filepath, self.dati_db_piatti):
            self.db_file_path = filepath
            self.db_path_label.config(text=f"DB: {os.path.basename(filepath)}")
            self._salva_api()
            self._log(f"✅ Database Completo salvato con successo in {os.path.basename(filepath)}.")
            self.show_custom_warning("Salvataggio", "Database Completo salvato.")

    def _carica_api(self):
        try:
            if os.path.exists(DEFAULT_API):
                with open(DEFAULT_API, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    api_key = data.get("api_key", "")
                    if api_key:
                        self.api_key.set(api_key)
                        self._log("✅ Chiave API caricata dal file di configurazione.")
                        return True
        except Exception as e:
            self._log(f"⚠️ Errore durante il caricamento della chiave API: {e}", is_error=False)
        return False

    def _salva_api(self):
        api_key_value = self.api_key.get()
        try:
            db_directory = os.path.dirname(DEFAULT_API)
            os.makedirs(db_directory, exist_ok=True)
            data = {"api_key": api_key_value}
            with open(DEFAULT_API, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            self._log(f"✅ Chiave API salvata con successo in {os.path.basename(DEFAULT_API)}.")
            return True
        except Exception as e:
            self._log(f"❌ ERRORE nel salvataggio della chiave API: {e}", is_error=True)
            return False

    def _on_close(self):
        salva_e_chiudi = self.show_custom_askyesno(
            "Chiudere l'applicazione?", 
            "Sei sicuro di voler uscire?\n\nCliccando 'Sì' verranno salvati il DB e l'API.\n\nCliccando 'No' uscirai senza salvare."
        )
        if salva_e_chiudi:
            self._salva_db() 
            self._log("Salvataggio eseguito prima della chiusura.")
        if salva_e_chiudi is not None:
             self.master.quit()
            
    def show_custom_warning(self, title, message):
        self._show_custom_message(title, message, "yellow", "black", "warning")

    def show_custom_info(self, title, message):
        self._show_custom_message(title, message, "lightblue", "black", "info")

    def show_custom_askyesno(self, title, message):
        dialog = tk.Toplevel(self.master, bg="orange")  
        dialog.withdraw()  
        dialog.title(title)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.transient(self.master)
        dialog.update_idletasks()
        w, h = 320, 140
        x = dialog.winfo_screenwidth() // 2 - w // 2
        y = dialog.winfo_screenheight() // 2 - h // 2
        dialog.geometry(f"{w}x{h}+{x}+{y}")
        dialog.deiconify()
        dialog.lift()              
        dialog.attributes("-topmost", True) 
        label = tk.Label(dialog, text=message, font=("Arial", 10), justify="left", padx=16, pady=12, bg="orange")
        label.pack()
        btns = tk.Frame(dialog, bg="orange")
        btns.pack(pady=(0,10))
        result = {"value": False}

        def yes():
            result["value"] = True
            dialog.destroy()

        def no():
            result["value"] = False
            dialog.destroy()
            
        b1 = ttk.Button(btns, text="Sì", style="Verde.TButton", command=yes)  
        b2 = ttk.Button(btns, text="No", style="Giallo.TButton", command=no)    
        b1.grid(row=0, column=0, padx=8)
        b2.grid(row=0, column=1, padx=8)

        dialog.wait_window()
        return result["value"]

    def _show_custom_message(self, title, message, bg, fg, icon=None):
        dialog = tk.Toplevel(self.master)
        dialog.attributes("-topmost", True)
        dialog.withdraw()  
        dialog.title(title)
        dialog.transient(self.master)
        dialog.grab_set()
        dialog.resizable(False, False)
        frame = tk.Frame(dialog, bg=bg)
        frame.pack(fill="both", expand=True)
        frame.pack_propagate(False) 
        label = tk.Label(frame, text=message, font=("Arial", 10), bg=bg, fg=fg, justify="left", padx=16, pady=12)
        label.pack()
        btn = ttk.Button(frame, text="OK", style="Verde.TButton", command=dialog.destroy)
        btn.pack(pady=(0, 10))
        btn.focus_set()
        dialog.bind("<Return>", lambda e: dialog.destroy())
        dialog.bind("<KP_Enter>", lambda e: dialog.destroy())
        dialog.bind("<Escape>", lambda e: dialog.destroy())
        dialog.update_idletasks() 
        width = label.winfo_reqwidth() + 40  
        height = label.winfo_reqheight() + btn.winfo_reqheight() + 40
        x = (dialog.winfo_screenwidth() - width) // 2
        y = (dialog.winfo_screenheight() - height) // 2
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        dialog.deiconify()

if __name__ == "__main__":
    
    root = tk.Tk()
    window_width = 1400
    window_height = 750
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width/2 - window_width/2)
    center_y = int(screen_height/2 - window_height/2)
    root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
    if os.path.exists(ICON_PATH):
        try:
            icon = tk.PhotoImage(file=ICON_PATH)
            root.iconphoto(True, icon) 
            root.icon_ref = icon 
        except Exception as e:
            print(f"Errore nell'impostazione dell'icona da {ICON_PATH}. Errore: {e}")
    else:
        print(f"File icona non trovato nel percorso calcolato: {ICON_PATH}")
        
    style = ttk.Style()
    style.theme_use('clam') 

    style.configure("Custom.Treeview.Heading", font=('Arial', 8, 'normal')) 
    style.configure("Custom.Treeview", font=('Arial', 8, 'normal'), rowheight=18) 
    style.map('Custom.Treeview', 
              background=[('selected', '#5c99ff')],
              foreground=[('selected', 'white')])
    style.configure('Custom.TButton', background='#3f51b5', foreground='white', font=('Arial', 8, 'bold'), padding=[8, 2])
    style.map('Custom.TButton', background=[('active', '#303f9f')])
    style.configure('Accent.TButton', background='#4CAF50', foreground='white', font=('Arial', 8, 'bold'), padding=[8, 2])
    style.map('Accent.TButton', background=[('active', '#388E3C')])
    
    style.configure("Verde.TButton", background="#32CD32", foreground='white', font=('Arial', 8, 'bold'), padding=[8, 2])
    style.map("Verde.TButton", background=[("active", "#b2fab2")])
    style.configure("Giallo.TButton", background="#FF9800", foreground='white', font=('Arial', 8, 'bold'), padding=[8, 2])
    style.map("Giallo.TButton", background=[("active", "#F57C00")])
    style.configure("Rosso.TButton", background="red", foreground='white', font=('Arial', 8, 'bold'), padding=[8, 2])
    style.map("Rosso.TButton", background=[("active", "#ff9999")])
    style.configure("Blu.TButton", background="dodgerblue", foreground='white', font=('Arial', 8, 'bold'), padding=[8, 2])
    style.map("Blu.TButton", background=[("active", "#3399FF")])
    
    app = ScontrinoParserApp(root)
    app._carica_db()
    root.mainloop()
    
