#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import shutil
import tempfile
import zipfile
import platform
import subprocess
import threading
import datetime
from decimal import Decimal
import tkinter as tk
from tkinter import ttk, filedialog

def gestisci_archivi_pdf(self, categoria_iniziale=None, data_iniziale=None, importo_iniziale=None, tipo_iniziale="Uscita", descrizione_iniziale="", pdf_path_iniziale=None):
    import __main__ as _app
    DB_DIR               = _app.DB_DIR
    DOC_DIR              = _app.DOC_DIR
    REGISTRY_FILE        = _app.REGISTRY_FILE
    DB_CONDIVISO         = _app.DB_CONDIVISO
    EXPORT_FILES         = _app.EXPORT_FILES
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    _HAS_DND             = _app._HAS_DND
    _DND_FILES           = _app._DND_FILES
    API_KEY              = _app.API_KEY
    genai_client         = _app.genai_client
    GEMINI               = _app.GEMINI
    types                = _app.types
    Image                = _app.Image
    ImageTk              = _app.ImageTk
    fitz                 = _app.fitz
    if importo_iniziale and isinstance(importo_iniziale, str):
        if "," in importo_iniziale:
           importo_iniziale = importo_iniziale.replace(".", "").replace(",", ".")
    from datetime import datetime
    categorie_vuote = [] 
    if not hasattr(self, 'filtri_avanzati'):
         self.filtri_avanzati = {} 
    if categoria_iniziale and categoria_iniziale.strip() not in ("", "Generica", "—"):
         self.filtri_avanzati['categoria'] = categoria_iniziale
    elif 'categoria' in self.filtri_avanzati and not categoria_iniziale:
         del self.filtri_avanzati['categoria']
    if data_iniziale:
         self.filtri_avanzati['data_da'] = data_iniziale
         self.filtri_avanzati['data_a'] = data_iniziale
    else:
         self.filtri_avanzati.pop('data_da', None)
         self.filtri_avanzati.pop('data_a', None)
    if not hasattr(self, '_ignore_trace'):
         self._ignore_trace = False
    def crea_directory_documenti():
         if not os.path.exists(DB_DIR): os.makedirs(DB_DIR)
         if not os.path.exists(DOC_DIR): os.makedirs(DOC_DIR)
    def load_document_registry():
         crea_directory_documenti()
         if os.path.exists(REGISTRY_FILE):
             with open(REGISTRY_FILE, 'r', encoding='utf-8') as f:
                 try:
                     content = f.read()
                     if not content: return {}
                     f.seek(0)
                     return json.load(f)
                 except json.JSONDecodeError:
                     self.show_custom_warning("Attenzione", "Il file di registro è corrotto. Creazione di un nuovo registro.")
                     return {}
         return {}
    def save_document_registry(registry):
         crea_directory_documenti()
         with open(REGISTRY_FILE, 'w', encoding='utf-8') as f:
             json.dump(registry, f, indent=4, ensure_ascii=False)
         # DataBase Condiviso
         if DB_CONDIVISO:
             self.notifica_modifica_web()
             print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 📡 Notifica di aggiornamento inviata .")
    def sanitizza_stringa(s, max_len=None):
         s_sanitizzata = s.strip().replace(' ', '_')
         s_sanitizzata = re.sub(r'[^\w\.-]', '', s_sanitizzata) 
         if max_len and len(s_sanitizzata) > max_len: return s_sanitizzata[:max_len]
         return s_sanitizzata.upper()
    def validate_importo(P):
         if P == "": return True
         if not re.match(r'^[\d,\.]*$', P): return False
         cifre = re.sub(r'[^\d]', '', P)
         if len(cifre) > 7: return False
         return True
    vcmd_importo = self.register(validate_importo) 

    def formatta_importo_pulito(importo_raw):
        try:
            importo_str = str(importo_raw).replace(',', '.').strip()
            if not importo_str or importo_str == "N/D":
                return "0,00"
            valore_float = float(importo_str)
            if isinstance(importo_raw, str) and importo_raw.isdigit() and len(importo_raw) > 0:
                padded_str = importo_raw.zfill(2)
                interi = padded_str[:-2] if len(padded_str) > 2 else "0"
                decimali = padded_str[-2:]
            else:
                interi = str(int(valore_float))
                decimali = f"{int(round((valore_float - int(valore_float)) * 100)):02d}"
            if not interi: interi = "0"
            interi_formattati = f"{int(interi):,}".replace(",", ".")
            return f"{interi_formattati},{decimali}"
        except Exception as e:
            print(f"Errore formattazione importo ({importo_raw}): {e}")
            return "0,00"
    def parse_importo_pulito(importo_str_visibile):
         if not importo_str_visibile: return None
         s = importo_str_visibile.replace(' €', '').replace('.', '').replace(',', '.')
         try: return float(s.strip())
         except ValueError: return None
    def open_pdf(event, treeview):
            selected = treeview.selection()
            if not selected:
                    return
            try:
                    selected_item = treeview.selection()[0]
                    values = treeview.item(selected_item, 'values')
                    file_name = values[5] 
                    if not file_name or file_name == "N/D":
                            return self.show_custom_warning("Attenzione", "File non disponibile.")
                    file_path = os.path.join(DOC_DIR, file_name)
                    if not os.path.exists(file_path):
                            cartella_alt = os.path.join(os.getcwd(), "Fatture_GMail")
                            file_path = os.path.join(cartella_alt, file_name)
                    
                    if not os.path.exists(file_path):
                            return self.show_custom_warning("Errore", f"File non trovato: {file_name}")
                    preview_win = tk.Toplevel(self)
                    preview_win.title(f"Visualizzatore Documento - {file_name}")
                    preview_win.transient(self)
                    preview_win.withdraw()
                    W, H = 950, 630
                    preview_win.geometry(f'{W}x{H}')
                    preview_win.bind("<Escape>", lambda e: preview_win.destroy())
                    preview_win.update_idletasks()
                    sw, sh = preview_win.winfo_screenwidth(), preview_win.winfo_screenheight()
                    x, y = (sw // 2) - (W // 2), (sh // 2) - (H // 2)
                    preview_win.geometry(f'{W}x{H}+{x}+{y}')
                    preview_win.minsize(W, H)
                    preview_win.configure(bg=self.COLOR_WIDGET_BG)
                    main_container = tk.Frame(preview_win, bg=self.COLOR_WIDGET_BG)
                    main_container.pack(fill=tk.BOTH, expand=True)
                    canvas = tk.Canvas(main_container, bg=self.COLOR_WIDGET_BG, highlightthickness=0)
                    v_scroll = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview, style="Vertical.TScrollbar")
                    h_scroll = ttk.Scrollbar(main_container, orient="horizontal", command=canvas.xview, style="Horizontal.TScrollbar")
                    canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
                    v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
                    h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
                    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                    fitz.TOOLS.mupdf_display_errors(False)
                    doc = fitz.open(file_path)
                    self.pdf_images = [] 
                    y_offset, max_w, zoom = 20, 0, 1.4
                    mat = fitz.Matrix(zoom, zoom)
                    for page_num in range(len(doc)):
                            page = doc.load_page(page_num)
                            pix = page.get_pixmap(matrix=mat, annots=False)
                            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                            photo = ImageTk.PhotoImage(img)
                            self.pdf_images.append(photo)                                
                            pos_x = max(20, (W - pix.width) // 2)
                            canvas.create_image(pos_x, y_offset, anchor="nw", image=photo)
                            y_offset += pix.height + 25
                            if pix.width > max_w: max_w = pix.width
                    canvas.config(scrollregion=(0, 0, max(W, max_w + 40), y_offset + 50))
                    doc.close()
                    def _on_mousewheel(event):
                        try:
                            if canvas.winfo_exists():
                                if event.num == 4 or event.delta > 0: canvas.yview_scroll(-1, "units")
                                elif event.num == 5 or event.delta < 0: canvas.yview_scroll(1, "units")
                        except (tk.TclError, NameError, AttributeError):
                            pass
                    canvas.bind_all("<MouseWheel>", _on_mousewheel)
                    canvas.bind_all("<Button-4>", _on_mousewheel)
                    canvas.bind_all("<Button-5>", _on_mousewheel)
                    frame_btns = tk.Frame(preview_win, bg=self.COLOR_WIDGET_BG)
                    frame_btns.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=10)
                    img_stampa = self.icone_gui.get("stampa")
                    img_salva = self.icone_gui.get("salva")
                    img_chiudi = self.icone_gui.get("chiudi")
                    btn_stampa = ttk.Label(
                            frame_btns, compound="left", image=img_stampa,
                            text=" Stampa" if img_stampa else "Stampa",
                            background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                            cursor="hand2"
                    )
                    btn_stampa.image = img_stampa
                    btn_stampa.pack(side='left', padx=10)
                    btn_stampa.bind("<Button-1>", lambda e: self.stampa_pdf(file_path, self.show_custom_warning))
                    def salva_documento():
                            dest = filedialog.asksaveasfilename(
                                   defaultextension=".pdf",
                                   filetypes=[("File di testo", "*.pdf"), ("Tutti i file", "*.*")],
                                   initialdir=EXPORT_FILES,
                                   initialfile=file_name,
                                   title="Esporta PDF",
                                   confirmoverwrite=False)
                            if dest:
                                    shutil.copy2(file_path, dest)
                                    self.show_toast("Documento salvato!")
                    btn_salva = ttk.Label(
                            frame_btns, compound="left", image=img_salva,
                            text=" Salva" if img_salva else "Salva",
                            background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                            cursor="hand2"
                    )
                    btn_salva.image = img_salva
                    btn_salva.pack(side='left', padx=10)
                    btn_salva.bind("<Button-1>", lambda e: salva_documento())
                    btn_chiudi = ttk.Label(
                            frame_btns, compound="left", image=img_chiudi,
                            text=" Chiudi" if img_chiudi else "Chiudi",
                            background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                            cursor="hand2"
                    )
                    btn_chiudi.image = img_chiudi
                    btn_chiudi.pack(side='right', padx=10)
                    btn_chiudi.bind("<Button-1>", lambda e: preview_win.destroy())
                    preview_win.deiconify()
                    preview_win.wait_window()
            except Exception as e:
                    self.show_custom_warning("Errore", f"Errore: {e}")
    def get_document_components(filename, registry):
        DEFAULT_CATEGORY = "Generica"
        if filename in registry:
            doc_data = registry[filename]
            categoria = doc_data.get('categoria_esatta', DEFAULT_CATEGORY)
            descrizione = doc_data.get('descrizione_esatta', 'N/D')
            tipo = doc_data.get('tipo_esatto', 'N/D')
            data_ggmmaaaa = doc_data.get('data_raw', '00000000')
            try: 
                data_formattata = datetime.strptime(data_ggmmaaaa, "%d%m%Y").strftime("%d-%m-%Y")
            except ValueError: 
                data_formattata = "N/D"
            importo_raw = str(doc_data.get('importo_raw', 0))
            importo_formattato = formatta_importo_pulito(importo_raw)
            return (data_formattata, categoria, descrizione, importo_formattato, tipo, data_ggmmaaaa, importo_raw, True)
        return "N/D", "N/D", filename, "N/D", "N/D", "00000000", "0", False
    def treeview_sort_column(treeview, col, reverse):
         l = [(treeview.set(k, col), k) for k in treeview.get_children('')]
         if col == 'importo':
             def sort_key_importo(item):
                 s = item[0].replace(' €', '').replace('.', '').replace(',', '.')
                 try: return float(s.strip())
                 except ValueError: return -999999999
             l.sort(key=sort_key_importo, reverse=reverse)
         elif col == 'data':
             def sort_key_date(item):
                 date_str = item[0]
                 try: return datetime.strptime(date_str, "%d-%m-%Y")
                 except ValueError: return datetime.min
             l.sort(key=sort_key_date, reverse=reverse)
         else:
             l.sort(reverse=reverse)
         for index, (val, k) in enumerate(l):
             treeview.move(k, '', index)
         treeview.heading(col, command=lambda c=col: treeview_sort_column(treeview, col, not reverse))
    def load_documents(treeview, filtri_attuali=None):
            self.funzione_carica_documenti = load_documents
            crea_directory_documenti()
            registry = load_document_registry()
            if not registry and os.path.exists(REGISTRY_FILE) and os.path.getsize(REGISTRY_FILE) > 2:
                    self.after(200, lambda: load_documents(treeview, filtri_attuali))
                    return
            for item in treeview.get_children(): treeview.delete(item)
            documenti_validi = [f for f in registry.keys() if f.endswith('.pdf')]
            items_caricati = []
            totale_filtrato = 0.0
            filtri_attuali = filtri_attuali or {}
            parola_chiave_lower = filtri_attuali.get('parola_chiave', '').lower().strip()
            data_da_obj = None; data_a_obj = None
            if filtri_attuali:
                    try: 
                            if filtri_attuali.get('data_da'): data_da_obj = datetime.strptime(filtri_attuali['data_da'], "%d-%m-%Y").date()
                            if filtri_attuali.get('data_a'): data_a_obj = datetime.strptime(filtri_attuali['data_a'], "%d-%m-%Y").date()
                    except ValueError: pass
            importo_da_float = parse_importo_pulito(filtri_attuali.get('importo_da', ''))
            importo_a_float = parse_importo_pulito(filtri_attuali.get('importo_a', ''))
            def sort_key(doc_file):
                    data_raw = registry.get(doc_file, {}).get('data_raw')
                    if data_raw and len(data_raw) == 8 and data_raw.isdigit():
                            giorno = data_raw[0:2]
                            mese = data_raw[2:4]
                            anno = data_raw[4:8]
                            return anno + mese + giorno
                    return '00000000'
            for doc_file in sorted(documenti_validi, key=sort_key, reverse=True):
                    data, categoria, descrizione, importo_formattato, tipo, data_raw, importo_raw, is_new_logic = get_document_components(doc_file, registry)
                    if not is_new_logic: continue
                    importo_visualizzato = f"{importo_formattato} €" if importo_formattato != "N/D" else "N/D"
                    search_string = f"{data} {categoria} {descrizione} {tipo} {importo_formattato} {doc_file}".lower()
                    match = True
                    if parola_chiave_lower and parola_chiave_lower not in search_string: match = False
                    if filtri_attuali and match:
                            filtro_categoria_attuale = filtri_attuali.get("categoria")
                            if filtro_categoria_attuale and filtro_categoria_attuale != "—":
                                    if filtro_categoria_attuale != categoria: 
                                            match = False
                            if filtri_attuali.get("descrizione") and filtri_attuali["descrizione"].lower() not in descrizione.lower(): match = False
                            if filtri_attuali.get("tipo") and filtri_attuali["tipo"] != "—" and filtri_attuali["tipo"] != tipo: match = False
                            if data_raw != "00000000":
                                    try:
                                            doc_date_obj = datetime.strptime(data_raw, "%d%m%Y").date()
                                            if data_da_obj and doc_date_obj < data_da_obj: match = False
                                            if data_a_obj and doc_date_obj > data_a_obj: match = False
                                    except ValueError: pass 
                            if importo_raw.isdigit():
                                    doc_importo_float = float(importo_raw) / 100 
                                    if importo_da_float is not None and doc_importo_float < importo_da_float: match = False
                                    if importo_a_float is not None and doc_importo_float > importo_a_float: match = False
                    if match:
                            if tipo == "Uscita":
                                    tag_colore = 'uscita_tag'
                            elif tipo == "Entrata":
                                    tag_colore = 'entrata_tag'
                            else:
                                    tag_colore = ''
                            treeview.insert(
                                    "", 
                                    "end", 
                                    values=(data, categoria, descrizione, importo_visualizzato, tipo, doc_file),
                                    tags=(tag_colore,)
                            )
                            items_caricati.append(doc_file)
                            if importo_formattato != "N/D":
                                    importo_float_str = importo_formattato.replace('.', '').replace(',', '.')
                                    try: totale_filtrato += float(importo_float_str)
                                    except ValueError: pass
            num_risultati = len(items_caricati)
            lbl_conteggio_doc.config(text=f"Documenti visualizzati: {num_risultati}")             
            if num_risultati == 0:
                if parola_chiave_lower or filtri_attuali:
                    lbl_risultati.config(text=" Nessuna corrispondenza.", foreground="#E06C75", image=self.icone_gui.get("chiudi"), compound="left")
                else:
                    lbl_risultati.config(text=" L'archivio è vuoto.", foreground="#abb2bf", image=self.icone_gui.get("chiudi"), compound="left")
            elif parola_chiave_lower or filtri_attuali:
                lbl_risultati.config(text=f" Trovati {num_risultati} documenti.", foreground="#61AFEF", image=self.icone_gui.get("modifica"), compound="left")
            else:
                lbl_risultati.config(text=f" Totale documenti: {num_risultati}.", foreground="#abb2bf", image=self.icone_gui.get("aggiungi"), compound="left")

            if num_risultati > 0:
                totale_in_centesimi = int(round(totale_filtrato * 100))
                totale_formattato = formatta_importo_pulito(str(totale_in_centesimi))
            else:
                totale_formattato = "0,00"

            lbl_totali.config(text=f" Totale Filtrato: {totale_formattato} €", foreground="#98C379", image=self.icone_gui.get("icc"), compound="left")

    def inserisci_documento_e_copia():
        data_str = data_var.get()
        categoria_esatta = combo_categoria.get()
        descrizione_esatta = entry_descrizione.get().strip()
        tipo_esatto = combo_tipo.get()
        importo_vis = importo_var.get()
        try:
          data_obj = datetime.strptime(data_str, "%d-%m-%Y").date()
          data_ggmmaaaa = data_obj.strftime("%d%m%Y")
          imp_dec = Decimal(importo_vis.replace(",", "."))
          imp_float, imp_raw = float(imp_dec), str(int(imp_dec * 100))
        except Exception:
          return self.show_toast("Dati non validi.")
        desc_pulita = descrizione_esatta.strip()
        while desc_pulita.startswith('📎'):
            desc_pulita = desc_pulita[len('📎'):].strip()
        desc_icona = f"📎 {desc_pulita}"
        f_name = f"{data_ggmmaaaa}_{sanitizza_stringa(descrizione_esatta, 30)}_{tipo_esatto}_{sanitizza_stringa(categoria_esatta, 20)}_{imp_raw}.pdf"
        path = _drop_path_ref[0] or filedialog.askopenfilename(parent=pdf_window, filetypes=[("PDF", "*.pdf")])
        if not path: return
        try:
          shutil.copy2(path, os.path.join(DOC_DIR, f_name))
          spesa_trovata = False
          if data_obj in self.spese:
              for s in self.spese[data_obj]:
                  if abs(float(s[2]) - imp_float) < 0.01 and s[3] == tipo_esatto:
                      spesa_trovata = True
                      break
          if spesa_trovata:
              aggiorna_spesa = self.show_custom_askyesno("Aggiorna Spese",
                  "Ho trovato una spesa simile.\n\nSì → aggancia il documento alla spesa esistente\nNo → salva solo il documento")
          else:
              aggiorna_spesa = self.show_custom_askyesno("Nuova Spesa",
                  "Nessuna spesa trovata per questa data/importo.\n\nSì → aggiungi anche la spesa al database\nNo → salva solo il documento")
          if aggiorna_spesa:
            if data_obj not in self.spese:
              self.spese[data_obj] = [[categoria_esatta, desc_icona, imp_float, tipo_esatto]]
            else:
              nuova_lista, trovato = [], False
              for s in self.spese[data_obj]:
                sp = list(s)
                if abs(float(sp[2]) - imp_float) < 0.01 and sp[3] == tipo_esatto:
                    sp[0] = categoria_esatta 
                    sp[1] = desc_icona
                    trovato = True
                nuova_lista.append(sp)
              if not trovato: 
                  nuova_lista.append([categoria_esatta, desc_icona, imp_float, tipo_esatto])
              self.spese[data_obj] = nuova_lista
            self.save_db()
          registry = load_document_registry()
          registry[f_name] = {
            "data_raw": data_ggmmaaaa, "categoria_esatta": categoria_esatta,
            "descrizione_esatta": desc_icona, "importo_raw": int(imp_raw),
            "tipo_esatto": tipo_esatto, "timestamp": datetime.now().isoformat()
          }
          save_document_registry(registry)
          self.refresh_gui() 
          _nome_c_doc = conto_doc_var.get()
          if _nome_c_doc and _nome_c_doc != "(nessuno)":
              self._aggiorna_conto_portafoglio(
                  _nome_c_doc, None, None,
                  imp_float, tipo_esatto, data_obj, categoria_esatta, desc_pulita
              )
          if hasattr(self, 'filtri_avanzati'):
              self.filtri_avanzati['categoria'] = categoria_esatta
          _drop_path_ref[0] = None
          data_var.set(datetime.now().strftime("%d-%m-%Y"))
          importo_var.set("")
          desc_var.set("")
          combo_categoria.set("Generica")
          combo_tipo.set("Uscita")
          self.show_toast("Documento salvato correttamente.")
          pdf_window.after(100, filtra_documenti)
        except Exception as e:
          self.show_custom_warning("Errore", f"Errore: {e}")

    def cancella_documento():
        items = tree.selection()
        if not items: return self.show_toast("Seleziona un documento da cancellare.")
        try:
            reg, mod = load_document_registry(), False
            spese_trovate = False
            for item in items:
                val = tree.item(item, 'values')
                d_s, c_v, d_v, i_v, t_v, f_n = val
                try:
                    d_o = datetime.strptime(d_s, "%d-%m-%Y").date()
                    i_f = float(i_v.replace("€","").replace(".","").replace(",",".").strip())
                    if d_o in self.spese:
                        for s in self.spese[d_o]:
                            desc_db = str(s[1]).replace("📎 ", "").strip()
                            desc_tabella = str(d_v).replace("📎 ", "").strip()
                            if (s[0] == c_v and s[3] == t_v and abs(float(s[2]) - i_f) < 0.01 and desc_db == desc_tabella):
                                spese_trovate = True
                                break
                except: continue
                if spese_trovate: break
            msg_doc = "Eliminare il documento selezionato?" if len(items) == 1 else f"Eliminare i {len(items)} documenti selezionati?"
            if not self.show_custom_askyesno("Conferma", msg_doc): return
            cancella_anche_spesa = False
            if spese_trovate:
                cancella_anche_spesa = self.show_custom_askyesno("Database Spese", "Trovati Movimenti collegati. Vuoi rimuovere anche quelli?")
            for item in items:
                val = tree.item(item, 'values')
                d_s, c_v, d_v, i_v, t_v, f_n = val
                p = os.path.join(DOC_DIR, f_n)
                if os.path.exists(p): os.remove(p)
                try:
                    d_o = datetime.strptime(d_s, "%d-%m-%Y").date()
                    i_f = float(i_v.replace("€","").replace(".","").replace(",",".").strip())
                    if d_o in self.spese:
                        nuova_lista = []
                        for s in self.spese[d_o]:
                            desc_db = str(s[1]).replace("📎 ", "").strip()
                            desc_tabella = str(d_v).replace("📎 ", "").strip()
                            if (s[0] == c_v and s[3] == t_v and abs(float(s[2]) - i_f) < 0.01 and desc_db == desc_tabella):
                                mod = True
                                if not cancella_anche_spesa:
                                    nuova_lista.append([s[0], desc_db, s[2], s[3]])
                                else:
                                    continue 
                            else:
                                nuova_lista.append(s)
                        self.spese[d_o] = nuova_lista
                except: pass
                if f_n in reg: del reg[f_n]
                tree.delete(item)
            if mod: self.save_db(); self.refresh_gui()
            save_document_registry(reg); load_documents(tree, self.filtri_avanzati)
            self.show_toast("Operazione completata.")
        except Exception as e: self.show_custom_warning("Errore", f"Errore: {e}")
            
    def esporta_documenti_selezionati():
        selected_items = tree.selection()
        if not selected_items:
            self.show_toast("Seleziona documenti da esportare.")
            return
        target_dir = filedialog.askdirectory(
            initialdir=EXPORT_FILES,
            title="Seleziona la cartella di destinazione",
        )
        if not target_dir:
            return
        esportati_count = 0
        errori_count = 0
        for item_id in selected_items:
            try:
                values = tree.item(item_id, 'values')
                data = values[0]       
                categoria = values[1]  
                descrizione = values[2] 
                original_file_name = values[5]
                if not original_file_name or original_file_name == "N/D":
                    errori_count += 1
                    continue
                original_path = os.path.join(DOC_DIR, original_file_name)
                if not os.path.exists(original_path):
                    self.show_custom_warning("File Mancante", f"Il file sorgente '{original_file_name}' non è stato trovato.")
                    errori_count += 1
                    continue
                categoria_safe = categoria.replace(" ", "_").replace("/", "_")
                descrizione_safe = descrizione.replace(" ", "_").replace("/", "_").replace(".", "")
                data_safe = data.replace("-", "_")
                if descrizione_safe and descrizione_safe != "N/D":
                     new_file_name = f"{categoria_safe}_{descrizione_safe}_{data_safe}.pdf"
                else:
                     new_file_name = f"{categoria_safe}_{data_safe}.pdf"
                target_path = os.path.join(target_dir, new_file_name)
                shutil.copy2(original_path, target_path)
                esportati_count += 1
            except Exception as e:
                print(f"Errore durante l'esportazione del file '{item_id}': {e}") 
                errori_count += 1
                continue
        if esportati_count > 0:
            messaggio = f"Esportazione completata! Sono stati copiati {esportati_count} documenti nella cartella:\n{target_dir}"
            if errori_count > 0:
                messaggio += f"\nAttenzione: {errori_count} documenti non sono stati esportati a causa di errori."
            self.show_custom_info("Esportazione Multipla Riuscita", messaggio)
            try:
                os.startfile(target_dir)
            except Exception:
                pass
        elif errori_count > 0:
             self.show_custom_warning("Esportazione Fallita", f"Nessun documento è stato esportato. {errori_count} errori riscontrati.")
    def apri_filtri_avanzati():
        root = pdf_window
        filtro_win = tk.Toplevel(root, bg=self.COLOR_TOPLEVEL)
        filtro_win.title("⚙️ Filtri Avanzati")
        larghezza_finestra = 500
        altezza_finestra = 380
        x = root.winfo_rootx() + (root.winfo_width() // 2) - (larghezza_finestra // 2)
        y = root.winfo_rooty() + (root.winfo_height() // 2) - (altezza_finestra // 2)
        filtro_win.geometry(f"{larghezza_finestra}x{altezza_finestra}+{x}+{y}")
        filtro_win.resizable(False, False)
        filtro_win.protocol("WM_DELETE_WINDOW", lambda: (
            (self.popup_calendario.destroy(), setattr(self, 'popup_calendario', None)) 
            if hasattr(self, 'popup_calendario') and self.popup_calendario and self.popup_calendario.winfo_exists() 
            else None,
            filtro_win.destroy()
        ))
        filtro_win.bind("<Escape>", lambda e: filtro_win.destroy())
        filtro_win.transient(root)
        descrizione_initial = self.filtri_avanzati.get("descrizione", campo_input.get().strip() if 'campo_input' in locals() else '')
        descrizione_var = tk.StringVar(value=descrizione_initial)
        categoria_var = tk.StringVar(value=self.filtri_avanzati.get("categoria", "—"))
        tipo_var = tk.StringVar(value=self.filtri_avanzati.get("tipo", "—"))
        data_da_var = tk.StringVar(value=self.filtri_avanzati.get("data_da", ""))
        data_a_var = tk.StringVar(value=self.filtri_avanzati.get("data_a", ""))
        importo_da_var = tk.StringVar(value=self.filtri_avanzati.get("importo_da", ""))
        importo_a_var = tk.StringVar(value=self.filtri_avanzati.get("importo_a", ""))
        valori_categoria = ["—"] + (getattr(self, 'categorie', []))
        valori_tipo = ["—", "Entrata", "Uscita"]
        def applica_filtri():
            nuovi_filtri = {}; 
            if descrizione_var.get().strip():
                nuovi_filtri["descrizione"] = descrizione_var.get().strip()
                if 'campo_input' in locals(): campo_input.delete(0, tk.END) 
            if categoria_var.get() and categoria_var.get() != "—": nuovi_filtri["categoria"] = categoria_var.get()
            if tipo_var.get() and tipo_var.get() != "—": nuovi_filtri["tipo"] = tipo_var.get()
            try:
                data_da_str = data_da_var.get().strip()
                data_a_str = data_a_var.get().strip()
                if data_da_str: 
                    datetime.strptime(data_da_str, "%d-%m-%Y")
                    nuovi_filtri["data_da"] = data_da_str
                if data_a_str: 
                    datetime.strptime(data_a_str, "%d-%m-%Y")
                    nuovi_filtri["data_a"] = data_a_str
            except ValueError: 
                self.show_custom_warning("Errore", "Formato Data non valido (DD-MM-YYYY).")
                return 
            if parse_importo_pulito(importo_da_var.get()) is not None: nuovi_filtri["importo_da"] = importo_da_var.get()
            if parse_importo_pulito(importo_a_var.get()) is not None: nuovi_filtri["importo_a"] = importo_a_var.get()
            self.filtri_avanzati = nuovi_filtri
            filtro_win.destroy()
            load_documents(tree, self.filtri_avanzati) 
            self.show_custom_info("Filtri Applicati", "Filtri avanzati applicati con successo.")
        def chiudi_filtri(): filtro_win.destroy()
        frame_filtri = ttk.Frame(filtro_win, padding="10"); frame_filtri.pack(fill='both', expand=True)
        ttk.Label(frame_filtri, text="Descrizione (nel nome file):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        entry_desc_filtro = ttk.Entry(frame_filtri, textvariable=descrizione_var, width=30)
        entry_desc_filtro.grid(row=0, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        ttk.Label(frame_filtri, text="Categoria Esatta:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        combo_cat_filtro = ttk.Combobox(frame_filtri, textvariable=categoria_var, values=valori_categoria, style="Border.TCombobox", state='readonly', width=27)
        combo_cat_filtro.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        ttk.Label(frame_filtri, text="Tipo (Entrata/Uscita):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        combo_tipo_filtro = ttk.Combobox(frame_filtri, textvariable=tipo_var, values=valori_tipo, style="Border.TCombobox", state='readonly', width=27)
        combo_tipo_filtro.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        entry_desc_filtro.bind("<Return>", lambda e: combo_cat_filtro.focus_set())
        combo_cat_filtro.bind("<<ComboboxSelected>>", lambda e: (
            combo_cat_filtro.selection_clear(),
            combo_tipo_filtro.focus_set()
        ))
        combo_tipo_filtro.bind("<<ComboboxSelected>>", lambda e: (
            combo_tipo_filtro.selection_clear(),
            frame_filtri.focus_set()
        ))
        ttk.Separator(frame_filtri, orient='horizontal').grid(row=3, column=0, columnspan=3, sticky='ew', pady=10)
        ttk.Label(frame_filtri, text="Intervallo Data DA:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        entry_data_da = ttk.Entry(frame_filtri, textvariable=data_da_var, width=12)
        entry_data_da.grid(row=4, column=1, padx=(0, 2), pady=5, sticky="ew")
        img_cal = self.icone_gui.get("oggi")
        btn_cal_da = ttk.Label(
            frame_filtri,
            image=img_cal,
            text="🗓️" if not img_cal else "",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
        )
        btn_cal_da.image = img_cal
        btn_cal_da.grid(row=4, column=2, padx=(2, 5), pady=5, sticky="w")
        btn_cal_da.bind("<Button-1>", lambda e: self.mostra_calendario_popup_semplice(entry_data_da, data_da_var))
        ttk.Label(frame_filtri, text="Intervallo Data A:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        entry_data_a = ttk.Entry(frame_filtri, textvariable=data_a_var, width=12)
        entry_data_a.grid(row=5, column=1, padx=(0, 2), pady=5, sticky="ew")
        btn_cal_a = ttk.Label(
            frame_filtri,
            image=img_cal,
            text="🗓️" if not img_cal else "",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
        )
        btn_cal_a.image = img_cal
        btn_cal_a.grid(row=5, column=2, padx=(2, 5), pady=5, sticky="w")
        btn_cal_a.bind("<Button-1>", lambda e: self.mostra_calendario_popup_semplice(entry_data_a, data_a_var))
        ttk.Label(frame_filtri, text="Importo DA (€):").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        entry_importo_da = ttk.Entry(frame_filtri, textvariable=importo_da_var, width=15); entry_importo_da.grid(row=6, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(frame_filtri, text="Importo A (€):").grid(row=7, column=0, padx=5, pady=5, sticky="w")
        entry_importo_a = ttk.Entry(frame_filtri, textvariable=importo_a_var, width=15); entry_importo_a.grid(row=7, column=1, padx=5, pady=5, sticky="ew")
        frame_btns = tk.Frame(filtro_win, bg=self.COLOR_TOPLEVEL); frame_btns.pack(pady=10)
        img_check = self.icone_gui.get("check")
        btn_applica = ttk.Label(
            frame_btns,
            compound="left",
            image=img_check,
            text=" Applica Filtri" if img_check else "Applica Filtri",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
        )
        btn_applica.image = img_check
        btn_applica.pack(side='left', padx=10)
        btn_applica.bind("<Button-1>", lambda e: applica_filtri())
        img_chiudi = self.icone_gui.get("chiudi")
        btn_annulla = ttk.Label(
            frame_btns,
            compound="left",
            image=img_chiudi,
            text=" Annulla" if img_chiudi else "Annulla",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
        )
        btn_annulla.image = img_chiudi
        btn_annulla.pack(side='left', padx=10)
        btn_annulla.bind("<Button-1>", lambda e: chiudi_filtri())
        filtro_win.wait_window()
    def stampa_documenti_selezionati():
        selected_items = tree.selection()
        if not selected_items:
            self.show_custom_warning("Attenzione", "Seleziona almeno un documento da stampare.")
            return
        stampati_count = 0
        errori_count = 0
        current_os = platform.system()
        for item_id in selected_items:
            try:
                values = tree.item(item_id, 'values')
                original_file_name = values[5] 
                if not original_file_name or original_file_name == "N/D":
                    errori_count += 1
                    continue
                original_path = os.path.join(DOC_DIR, original_file_name) 
                if not os.path.exists(original_path):
                    self.show_custom_warning("File Mancante", f"Il file sorgente '{original_file_name}' non è stato trovato.")
                    errori_count += 1
                    continue
                if current_os == "Windows":
                    os.startfile(original_path, 'print')
                elif current_os in ["Linux", "Darwin"]:
                    subprocess.Popen(['lp', original_path])
                else:
                    self.show_custom_warning("OS Non Supportato", f"La stampa diretta di documenti non è supportata su {current_os}.")
                    errori_count += 1
                    continue
                stampati_count += 1
            except Exception as e:
                print(f"Errore durante la preparazione alla stampa del file '{original_file_name}': {e}")
                self.show_custom_warning("Errore Stampa", f"Impossibile avviare la stampa per '{original_file_name}'. Dettagli: {e}")
                errori_count += 1
                continue
        if stampati_count > 0:
            messaggio = f"Comando di stampa inviato per {stampati_count} documento/i."
            if errori_count > 0:
                messaggio += f"\nAttenzione: {errori_count} documenti non sono stati elaborati per la stampa."
            self.show_custom_info("Stampa Avviata", messaggio)
        elif errori_count > 0:
            self.show_custom_warning("Stampa Fallita", f"Nessun documento è stato stampato. {errori_count} errori riscontrati.")
    def chiudi_finestra():
         if hasattr(self, 'popup_calendario') and self.popup_calendario and self.popup_calendario.winfo_exists():
             self.popup_calendario.destroy()
         threading.Thread(target=self.backup_documenti, daemon=False).start()   
         self.filtri_avanzati = {}
         self.pdf_window.destroy()
    def filtra_documenti(event=None):
         filtri = self.filtri_avanzati.copy(); filtri['parola_chiave'] = campo_input.get().strip()
         load_documents(tree, filtri)
    def resetta_campo():
         campo_input.delete(0, tk.END); self.filtri_avanzati = {}
         load_documents(tree, {})
    crea_directory_documenti()
    if hasattr(self, 'pdf_window') and self.pdf_window.winfo_exists(): self.pdf_window.lift(); return
    pdf_window = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    barra_menu_popup = tk.Menu(pdf_window, bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT, activebackground=self.MENU_ACT_BG_COLOR, activeforeground=self.MENU_ACT_FG_COLOR) 
    barra_menu_popup.config(bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT)
    pdf_window.config(menu=barra_menu_popup)
    menu_archivio = tk.Menu(barra_menu_popup, tearoff=0,bg=self.MENU_BG, fg=self.MENU_FG_LIGHT, activebackground=self.MENU_ACT_BG_COLOR, activeforeground=self.MENU_ACT_FG_COLOR)
    barra_menu_popup.add_cascade(label="📂 Archivio", menu=menu_archivio)
    menu_archivio.add_command(label="💾 Esporta documenti Zip", command=self.esegui_export_documenti_pdf)
    menu_archivio.add_command(label="📥 Importa documenti Zip", command=self.esegui_import_documenti_pdf)
    menu_archivio.add_separator()
    menu_archivio.add_command(label="❌ Chiudi (ESC)", command=chiudi_finestra)
    self.pdf_window = pdf_window
    pdf_window.title("Archivio Documenti Contabili")
    pdf_window.withdraw()
    larghezza_finestra = 1250
    altezza_finestra = 600
    larghezza_schermo = self.winfo_screenwidth()
    altezza_schermo = self.winfo_screenheight()
    x = (larghezza_schermo // 2) - (larghezza_finestra // 2)
    y = (altezza_schermo // 2) - (altezza_finestra // 2)
    pdf_window.geometry(f"{larghezza_finestra}x{altezza_finestra}+{x}+{y}")
    pdf_window.minsize(width=1250, height=600)
    pdf_window.transient(self)
    pdf_window.deiconify()
    pdf_window.protocol("WM_DELETE_WINDOW", chiudi_finestra)
    pdf_window.bind('<Escape>', lambda e: chiudi_finestra())
    frame_input = ttk.Frame(pdf_window, padding="10") 
    frame_input.pack(fill='x', padx=10, pady=(10, 5))
    data_default = data_iniziale if data_iniziale else datetime.now().strftime("%d-%m-%Y")
    data_var = tk.StringVar(value=data_default)
    importo_var = tk.StringVar(value=importo_iniziale if importo_iniziale else "")
    desc_var = tk.StringVar(value=descrizione_iniziale if descrizione_iniziale else "")
    def _limita_desc(*_):
        v = desc_var.get()
        if len(v) > 35:
            desc_var.set(v[:35])
    desc_var.trace_add("write", _limita_desc)
    ttk.Label(frame_input, text="Data:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    sub_frame_data = ttk.Frame(frame_input)
    sub_frame_data.grid(row=0, column=1, padx=0, pady=5, sticky="w")
    entry_data = ttk.Entry(sub_frame_data, textvariable=data_var, width=12)
    entry_data.pack(side="left", padx=(0, 5))
    btn_cal = ttk.Label(
            sub_frame_data, 
            image=self.icone_gui.get("calendario"), 
            text="🗓️" if not self.icone_gui.get("calendario") else "", 
            foreground="black",
            cursor="hand2"
    )
    btn_cal.image = self.icone_gui.get("calendario")
    btn_cal.pack(side="left", padx=2)
    btn_cal.bind("<Button-1>", lambda e: self.mostra_calendario_popup(entry_data, data_var))
    def imposta_data_oggi():
        oggi = datetime.now().strftime("%d-%m-%Y")
        data_var.set(oggi)
        tabella = getattr(self, 'tabella_documenti', None)
        funzione_load = getattr(self, 'funzione_carica_documenti', None)
        if tabella and funzione_load:
            funzione_load(tabella, {'data_da': oggi, 'data_a': oggi, 'categoria': combo_categoria.get()})
    btn_oggi = ttk.Label(
            sub_frame_data, 
            image=self.icone_gui.get("oggi"), 
            text="🔙" if not self.icone_gui.get("oggi") else "", 
            foreground="black",
            cursor="hand2"
    )
    btn_oggi.image = self.icone_gui.get("oggi")
    btn_oggi.pack(side="left", padx=2)
    btn_oggi.bind("<Button-1>", lambda e: imposta_data_oggi())
    def reset_data_totale():
        data_var.set("")
        tabella = getattr(self, 'tabella_documenti', None)
        funzione_load = getattr(self, 'funzione_carica_documenti', None)
        if tabella and funzione_load:
            funzione_load(tabella, {'categoria': combo_categoria.get(), 'data_da': None, 'data_a': None})
    btn_reset = ttk.Label(
            sub_frame_data, 
            image=self.icone_gui.get("reset"), 
            text="🔍" if not self.icone_gui.get("reset") else "", 
            foreground="black",
            cursor="hand2"
    )
    btn_reset.image = self.icone_gui.get("reset")
    btn_reset.pack(side="left", padx=2)
    btn_reset.bind("<Button-1>", lambda e: reset_data_totale())
    ttk.Label(frame_input, text="Categoria:").grid(row=0, column=3, padx=5, pady=5, sticky="w")
    combo_categoria = ttk.Combobox(frame_input, values=(getattr(self, 'categorie', categorie_vuote)), width=35, style="Border.TCombobox", state='readonly') 
    combo_categoria.set(categoria_iniziale if categoria_iniziale and categoria_iniziale.strip() not in ("", "Generica", "—") else "Generica") 
    combo_categoria.grid(row=0, column=4, padx=5, pady=5, sticky="w")
    ttk.Label(frame_input, text="Descrizione:").grid(row=0, column=5, padx=5, pady=5, sticky="w")
    entry_descrizione = ttk.Entry(frame_input, width=35, textvariable=desc_var)
    entry_descrizione.grid(row=0, column=6, padx=5, pady=5, sticky="w")
    ttk.Label(frame_input, text="Importo:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
    entry_importo = ttk.Entry(frame_input, width=15, textvariable=importo_var, validate='key', validatecommand=(vcmd_importo, '%P')) 
    entry_importo.grid(row=1, column=1, padx=5, pady=5, sticky="w")
    tipi_movimento = ["Entrata", "Uscita"] 
    ttk.Label(frame_input, text="Tipo:").grid(row=1, column=3, padx=5, pady=5, sticky="w")
    combo_tipo = ttk.Combobox(frame_input, values=tipi_movimento, width=15, style="Border.TCombobox", state='readonly')
    combo_tipo.set(tipo_iniziale if tipo_iniziale else "Uscita")  
    combo_tipo.grid(row=1, column=4, padx=5, pady=5, sticky="w")
    try:
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
            _db_p_doc = json.load(_pf)
        _conti_doc = [c.get("nome","?") for c in _db_p_doc.get("conti",[])]
        _princ_doc = next((c.get("nome","") for c in _db_p_doc.get("conti",[]) if c.get("principale")), "(nessuno)")
    except Exception:
        _conti_doc = []
        _princ_doc = "(nessuno)"
    conto_doc_var = tk.StringVar(value=_princ_doc)
    if _conti_doc:
        ttk.Label(frame_input, text="Conto:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        ttk.Combobox(frame_input, textvariable=conto_doc_var,
                     values=["(nessuno)"] + _conti_doc,
                     state="readonly", width=16, style="Border.TCombobox").grid(row=2, column=1, padx=5, pady=5, sticky="w")
    img_mouse = self.icone_gui.get("mouse")
    lbl_hint = ttk.Label(
        frame_input,
        text="Doppio clic → Apri Documento PDF  |  Clic destro → Salva i documenti PDF selezionati.",
        image=img_mouse,
        compound="right",
        foreground="gray",
        font=("Arial", 8, "italic")
    )
    if img_mouse:
        lbl_hint.image = img_mouse
    lbl_hint.grid(row=1, column=5, columnspan=2, padx=(10, 0), sticky="w")
    _dnd_txt = "Trascina un PDF sulla finestra, poi clicca Archivia PDF per salvare." if _HAS_DND else "Compila i campi, clicca Archivia PDF per selezionare e salvare il documento."
    lbl_hint2 = ttk.Label(
        frame_input,
        text=_dnd_txt,
        foreground="gray",
        font=("Arial", 8, "italic")
    )
    lbl_hint2.grid(row=2, column=5, columnspan=2, padx=(10, 0), pady=(0, 2), sticky="w")
    frame_progress_ai = ttk.Frame(frame_input)
    frame_progress_ai.grid(row=2, column=3, columnspan=2, padx=5, pady=(0, 2), sticky="w")
    lbl_progress_ai = ttk.Label(frame_progress_ai, text="", foreground="#61AFEF", font=("Arial", 8, "italic"))
    lbl_progress_ai.pack(side="left", padx=(0, 8))
    progress_ai = ttk.Progressbar(frame_progress_ai, mode="indeterminate", length=160, style="Horizontal.TProgressbar")
    progress_ai.pack(side="left")
    frame_progress_ai.grid_remove()
    def _mostra_progress_ai(testo="Analisi AI in corso…"):
        lbl_progress_ai.config(text=testo)
        frame_progress_ai.grid()
        progress_ai.start(12)
    def _nascondi_progress_ai():
        progress_ai.stop()
        frame_progress_ai.grid_remove()
    def esegui_auto_tipo(event=None, forza_tipo=None):
            if forza_tipo:
                    combo_tipo.set(forza_tipo)
            else:
                    scelta = combo_categoria.get()
                    tipo_db = self.categorie_tipi.get(scelta, "Uscita")
                    combo_tipo.set(tipo_db)
            if event:
                    combo_categoria.selection_clear()
                    entry_importo.after(10, entry_importo.focus_set)
    def esegui_salto_da_tipo(event):
            combo_tipo.selection_clear()
            entry_importo.after(10, entry_importo.focus_set)
            
    def modifica_documento():
        items = tree.selection()
        if not items:
            self.show_toast("Seleziona un documento da modificare.")
            return
        if len(items) > 1:
            self.show_toast("Seleziona un solo documento alla volta.")
            return
        val = tree.item(items[0], 'values')
        d_s, c_v, d_v, i_v, t_v, f_n = val
        registry = load_document_registry()
        if f_n not in registry:
            self.show_toast("Documento non trovato nel Registro.")
            return
        doc_data = registry[f_n]
        edit_win = tk.Toplevel(pdf_window, bg=self.COLOR_TOPLEVEL)
        edit_win.title("Modifica Documento")
        edit_win.transient(pdf_window)
        w, h = 500, 300
        x = pdf_window.winfo_rootx() + (pdf_window.winfo_width() // 2) - (w // 2)
        y = pdf_window.winfo_rooty() + (pdf_window.winfo_height() // 2) - (h // 2)
        edit_win.geometry(f"{w}x{h}+{x}+{y}")
        edit_win.resizable(False, False)
        frame = ttk.Frame(edit_win, padding="15")
        frame.pack(fill='both', expand=True)
        data_e_var = tk.StringVar(value=d_s)
        cat_e_var = tk.StringVar(value=c_v)
        desc_pulita = d_v.strip()
        while desc_pulita.startswith('📎'):
            desc_pulita = desc_pulita[len('📎'):].strip()
        desc_e_var = tk.StringVar(value=desc_pulita)
        def _limita_desc_e(*_):
            v = desc_e_var.get()
            if len(v) > 35:
                desc_e_var.set(v[:35])
        desc_e_var.trace_add("write", _limita_desc_e)
        imp_e_var = tk.StringVar(value=i_v.replace(' €', '').strip())
        tipo_e_var = tk.StringVar(value=t_v)
        ttk.Label(frame, text="Data:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        entry_data_e = ttk.Entry(frame, textvariable=data_e_var, width=15)
        entry_data_e.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        f_data = tk.Frame(frame, bg=self.COLOR_WIDGET_BG)
        f_data.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        entry_data_e = ttk.Entry(f_data, textvariable=data_e_var, width=12)
        entry_data_e.pack(side="left")
        self.btn_cal_data_spesa = tk.Label(
            f_data,
            image=self.icone_gui.get("calendario"),
            cursor="hand2",
            bg=self.COLOR_WIDGET_BG
        )
        self.btn_cal_data_spesa.pack(side="left", padx=5)
        self.btn_cal_data_spesa.bind(
            "<Button-1>", 
            lambda e: self.mostra_calendario_popup(entry_data_e, data_e_var)
        )
        ttk.Label(frame, text="Categoria:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        combo_cat_e = ttk.Combobox(frame, textvariable=cat_e_var, values=getattr(self, 'categorie', []), style="Border.TCombobox", state='readonly', width=30)
        combo_cat_e.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(frame, text="Descrizione:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        entry_desc_e = ttk.Entry(frame, textvariable=desc_e_var, width=32)
        entry_desc_e.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(frame, text="Importo:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        entry_imp_e = ttk.Entry(frame, textvariable=imp_e_var, width=15, validate='key', validatecommand=(vcmd_importo, '%P'))
        entry_imp_e.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        ttk.Label(frame, text="Tipo:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        combo_tipo_e = ttk.Combobox(frame, textvariable=tipo_e_var, values=["Entrata", "Uscita"], style="Border.TCombobox", state='readonly', width=15)
        combo_tipo_e.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        conto_e_var = tk.StringVar(value="(nessuno)")
        if _conti_doc:
            try:
                conto_e_var.set(_princ_doc)
            except Exception:
                pass
            ttk.Label(frame, text="Conto:").grid(row=5, column=0, padx=5, pady=5, sticky="w")
            ttk.Combobox(frame, textvariable=conto_e_var,
                         values=["(nessuno)"] + _conti_doc,
                         state="readonly", width=20, style="Border.TCombobox").grid(row=5, column=1, padx=5, pady=5, sticky="w")
        def salva_modifica():
            try:
                data_obj = datetime.strptime(data_e_var.get(), "%d-%m-%Y").date()
                data_ggmmaaaa = data_obj.strftime("%d%m%Y")
                imp_pulito = imp_e_var.get().replace(".", "").replace(",", ".")
                imp_dec = Decimal(imp_pulito)
                imp_float = float(imp_dec)
                imp_raw = str(int(imp_dec * 100))
            except Exception:
                self.show_toast("Dati non validi.")
            desc_pulita = desc_e_var.get().strip()
            while desc_pulita.startswith('📎'):
                desc_pulita = desc_pulita[len('📎'):].strip()
            desc_icona = f"📎 {desc_pulita}"
            categoria = cat_e_var.get()
            tipo = tipo_e_var.get()
            data_obj_old = datetime.strptime(d_s, "%d-%m-%Y").date()
            imp_float_old = float(doc_data.get('importo_raw', 0)) / 100
            tipo_old = doc_data.get('tipo_esatto', '')
            desc_old = doc_data.get('descrizione_esatta', '')
            aggiorna_spesa = False
            idx_spesa = -1
            if data_obj_old in self.spese:
                for i, s in enumerate(self.spese[data_obj_old]):
                    corrispondenza_importo = abs(float(s[2]) - imp_float_old) < 0.01
                    corrispondenza_tipo    = s[3] == tipo_old
                    corrispondenza_desc    = s[1] == desc_old or s[1] == desc_old.lstrip('📎').strip()
                    if corrispondenza_importo and corrispondenza_tipo and corrispondenza_desc:
                        idx_spesa = i
                        break
                if idx_spesa == -1:
                    for i, s in enumerate(self.spese[data_obj_old]):
                        if abs(float(s[2]) - imp_float_old) < 0.01 and s[3] == tipo_old:
                            idx_spesa = i
                            break
            spesa_trovata = idx_spesa != -1
            if spesa_trovata:
                aggiorna_spesa = self.show_custom_askyesno("Aggiorna Spesa",
                    "Ho trovato una spesa collegata.\nVuoi aggiornare anche quella?")
            nuovo_f_name = f"{data_ggmmaaaa}_{sanitizza_stringa(desc_pulita, 30)}_{tipo}_{sanitizza_stringa(categoria, 20)}_{imp_raw}.pdf"
            old_path = os.path.join(DOC_DIR, f_n)
            new_path = os.path.join(DOC_DIR, nuovo_f_name)
            if f_n != nuovo_f_name and os.path.exists(old_path):
                os.rename(old_path, new_path)
            registry = load_document_registry()
            if f_n in registry:
                del registry[f_n]
            registry[nuovo_f_name] = {
                "data_raw": data_ggmmaaaa,
                "categoria_esatta": categoria,
                "descrizione_esatta": desc_icona,
                "importo_raw": int(imp_raw),
                "tipo_esatto": tipo,
                "timestamp": doc_data.get("timestamp", datetime.now().isoformat())
            }
            save_document_registry(registry)
            if aggiorna_spesa and idx_spesa != -1:
                voce_aggiornata = [categoria, desc_icona, imp_float, tipo]
                if data_obj == data_obj_old:
                    self.spese[data_obj_old][idx_spesa] = voce_aggiornata
                else:
                    self.spese[data_obj_old].pop(idx_spesa)
                    if not self.spese[data_obj_old]:
                        del self.spese[data_obj_old]
                    if data_obj not in self.spese:
                        self.spese[data_obj] = []
                    self.spese[data_obj].append(voce_aggiornata)
                self.save_db()
            nuova_cat = cat_e_var.get()
            combo_categoria.set(nuova_cat) 
            self.refresh_gui()
            _nome_c_e = conto_e_var.get()
            if _nome_c_e and _nome_c_e != "(nessuno)":
                self._aggiorna_conto_portafoglio(
                    _nome_c_e, None, None,
                    imp_float, tipo, data_obj, categoria, desc_pulita
                )
            edit_win.destroy()
            filtra_documenti()
            tabella = getattr(self, 'tabella_documenti', None)
            funzione_load = getattr(self, 'funzione_carica_documenti', None)
            if tabella and funzione_load:
                    funzione_load(tabella, {
                            'categoria': nuova_cat, 
                            'data_da': None, 
                            'data_a': None
                    })
            self.show_toast("Documento aggiornato correttamente.")
        frame_btns = tk.Frame(edit_win, bg=self.COLOR_TOPLEVEL)
        frame_btns.pack(pady=10)
        img_check = self.icone_gui.get("check")
        btn_salva_e = ttk.Label(frame_btns, compound="left", image=img_check,
                                 text=" Salva" if img_check else "Salva",
                                 background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2")
        btn_salva_e.image = img_check
        btn_salva_e.pack(side='left', padx=10)
        btn_salva_e.bind("<Button-1>", lambda e: salva_modifica())
        img_chiudi = self.icone_gui.get("chiudi")
        btn_ann_e = ttk.Label(frame_btns, compound="left", image=img_chiudi,
                               text=" Annulla" if img_chiudi else "Annulla",
                               background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2")
        btn_ann_e.image = img_chiudi
        btn_ann_e.pack(side='left', padx=10)
        btn_ann_e.bind("<Button-1>", lambda e: edit_win.destroy())
        edit_win.bind("<Escape>", lambda e: edit_win.destroy())
        edit_win.wait_window()        
    combo_categoria.bind("<<ComboboxSelected>>", esegui_auto_tipo)
    combo_tipo.bind("<<ComboboxSelected>>", esegui_salto_da_tipo)
    entry_importo.bind("<Return>", lambda e: combo_tipo.focus_set())
    if _HAS_DND:
        _drop_path_ref = [pdf_path_iniziale]
        def on_drop(event):
            raw = event.data.strip()
            if raw.startswith("{") and raw.endswith("}"):
                raw = raw[1:-1]
            paths = [p.strip() for p in raw.split("} {") if p.strip()]
            pdf_path = paths[0] if paths else raw
            if not pdf_path.lower().endswith(".pdf"):
                self.show_toast("Trascina solo file PDF.")
                return
            _drop_path_ref[0] = pdf_path
            if not API_KEY:
                self.show_toast(f"📎 {os.path.basename(pdf_path)} — imposta API Key Gemini per l'analisi automatica")
                return
            nome_file_drop = os.path.basename(pdf_path)
            self.show_toast(f"Analisi AI: {nome_file_drop}…")
            _mostra_progress_ai(f"Analisi AI in corso…")
            def _analizza():
                try:
                    import json as _json
                    with open(pdf_path, "rb") as _pf:
                        pdf_bytes = _pf.read()
                    client_drop = genai_client.Client(api_key=API_KEY)
                    lista_cat = ", ".join(f'"{c}"' for c in self.categorie)
                    prompt_drop = (
                        f"Analizza questo documento PDF (fattura, ricevuta, cedolino, scontrino o simile).\n"
                        f"Estrai i seguenti campi e restituisci SOLO un JSON (senza backtick):\n"
                        f'{{\"importo\": float, \"azienda\": \"nome breve\", '
                        f'\"data\": \"YYYY-MM-DD\", '
                        f'\"fattura\": \"numero fattura o null\", '
                        f'\"scadenza\": \"GG-MM-AAAA o null\", '
                        f'\"direzione\": \"Entrata o Uscita\", '
                        f'\"categoria\": \"la più adatta tra [{lista_cat}]\"}}\n'
                        f"REGOLE: importo 0.01 se non trovato. "
                        f"Per la data usa quella del fatto economico (data valuta, data "
                        f"pagamento, data emissione/fattura, scadenza/competenza), MAI la "
                        f"data di stampa/generazione del documento (es. \"Stampa elaborata "
                        f"il\", \"Generato il\"); se non leggibile usa la data odierna. "
                        f"Se nel documento compaiono più date etichettate 'scadenza' (es. scadenza "
                        f"del pagamento dovuto E scadenza di un'offerta/contratto/promozione), usa "
                        f"per il campo 'scadenza' SOLO quella dell'importo da pagare indicato in "
                        f"bolletta, ignorando le altre. "
                        f"azienda solo nome senza emoji; SOLO JSON."
                    )
                    r_drop = client_drop.models.generate_content(
                        model=GEMINI,
                        contents=[
                            types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                            prompt_drop
                        ]
                    )
                    raw_json = r_drop.text.strip().replace("```json", "").replace("```", "").strip()
                    dati_drop = _json.loads(raw_json)
                    importo_ia   = float(dati_drop.get("importo") or 0.01)
                    azienda_ia   = str(dati_drop.get("azienda") or "Documento").strip()
                    fattura_ia   = dati_drop.get("fattura")
                    scadenza_ia  = dati_drop.get("scadenza")
                    data_str_ia  = dati_drop.get("data")
                    direzione_ia = dati_drop.get("direzione", "Uscita")
                    _testo_dp = ""
                    try:
                        import fitz as _fitz_dp
                        _doc_dp = _fitz_dp.open(pdf_path)
                        _testo_dp = "".join(p.get_text() for p in _doc_dp).lower()
                        _doc_dp.close()
                    except Exception:
                        pass
                    try:
                        data_ia = datetime.strptime(data_str_ia, "%Y-%m-%d").strftime("%d-%m-%Y")
                    except Exception:
                        data_ia = datetime.now().strftime("%d-%m-%Y")
                    _m_pens = None
                    if _testo_dp:
                        _m_pens = re.search(
                            r"prestazione\s+rata\s+(\d{1,2})[/\-](\d{2,4})", _testo_dp
                        )
                    if _m_pens:
                        _mm_p, _aaaa_p = _m_pens.groups()
                        if len(_aaaa_p) == 2:
                            _aaaa_p = "20" + _aaaa_p
                        desc_ia      = f"prestazione rata {int(_mm_p):02d}/{_aaaa_p}"
                        direzione_ia = "Entrata"
                    else:
                        desc_ia = azienda_ia
                        if fattura_ia and str(fattura_ia).lower() != "null":
                            desc_ia += f" {fattura_ia}"
                        if scadenza_ia and str(scadenza_ia).lower() != "null":
                            desc_ia += f" ⏰{scadenza_ia}"
                            try:
                                data_ia = datetime.strptime(str(scadenza_ia), "%d-%m-%Y").strftime("%d-%m-%Y")
                            except Exception:
                                pass
                    cat_ia       = dati_drop.get("categoria", "")
                    categoria_ia = cat_ia if cat_ia in self.categorie else (self.categorie[0] if self.categorie else "")
                    def _aggiorna_gui():
                        _nascondi_progress_ai()
                        data_var.set(data_ia)
                        importo_var.set(f"{importo_ia:.2f}".replace(".", ","))
                        entry_descrizione.delete(0, "end")
                        entry_descrizione.insert(0, desc_ia)
                        if direzione_ia in ("Entrata", "Uscita"):
                            combo_tipo.set(direzione_ia)
                        if categoria_ia:
                            combo_categoria.set(categoria_ia)
                        self.show_toast(f"📎 {os.path.basename(pdf_path)} — campi compilati, verifica e archivia", duration=2000)
                    pdf_window.after(0, _aggiorna_gui)
                except Exception as e_ia:
                    err_ia = str(e_ia)
                    if "429" in err_ia or "RESOURCE_EXHAUSTED" in err_ia:
                        msg_ia = "Quota API Gemini esaurita. Riprova domani."
                    elif "503" in err_ia or "UNAVAILABLE" in err_ia:
                        msg_ia = "Gemini non disponibile. Riprova tra poco."
                    else:
                        msg_ia = f"Analisi AI fallita: {err_ia[:80]}"
                    def _on_errore_ia(m=msg_ia):
                        _nascondi_progress_ai()
                        self.show_toast(m)
                    pdf_window.after(0, _on_errore_ia)
            threading.Thread(target=_analizza, daemon=True).start()
        try:
            pdf_window.drop_target_register(_DND_FILES)
            pdf_window.dnd_bind('<<Drop>>', on_drop)
        except Exception:
            pass
    else:
        _drop_path_ref = [None]
    frame_ricerca = ttk.Frame(pdf_window, padding="10 0 10 5") 
    frame_ricerca.pack(fill='x', padx=10)
    lbl_cerca = ttk.Label(frame_ricerca, text="Ricerca Documenti:", font=('Arial', 10, 'bold'))
    lbl_cerca.pack(side="left", padx=(0, 5))
    campo_input = ttk.Entry(frame_ricerca, width=30)
    campo_input.pack(side="left", padx=(0, 5), fill='x', expand=True)
    campo_input.bind('<KeyRelease>', filtra_documenti)
    lbl_conteggio_doc = ttk.Label(frame_ricerca, text="Documenti visualizzati: 0", foreground="#0066cc", font=('Arial', 10, 'bold'))
    lbl_conteggio_doc.pack(side="left", padx=(10, 5))
    lbl_risultati = ttk.Label(frame_ricerca, text="", foreground="gray")
    lbl_risultati.pack(side="left")
    lbl_totali = ttk.Label(frame_ricerca, text="")
    lbl_totali.pack(side="left", padx=10)
    btn_help = ttk.Label(
            frame_ricerca,
            compound="left",
            image=self.icone_gui.get("help"),
            text="" if self.icone_gui.get("help") else "?",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_help.image = self.icone_gui.get("help")
    btn_help.pack(side="right", padx=(1, 5))
    btn_help.bind("<Button-1>", lambda e: self.mostra_help_pdf())
    btn_filtri = ttk.Label(
            frame_ricerca,
            compound="left",
            image=self.icone_gui.get("filtri"),
            text=" Filtri Avanzati" if self.icone_gui.get("filtri") else "Filtri Avanzati",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_filtri.image = self.icone_gui.get("filtri")
    btn_filtri.pack(side="right", padx=5)
    btn_filtri.bind("<Button-1>", lambda e: apri_filtri_avanzati())
    btn_reset_campo = ttk.Label(
            frame_ricerca,
            compound="left",
            image=self.icone_gui.get("reset_campo"),
            text=" Reset" if self.icone_gui.get("reset_campo") else "Reset",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_reset_campo.image = self.icone_gui.get("reset_campo")
    btn_reset_campo.pack(side="right", padx=5)
    btn_reset_campo.bind("<Button-1>", lambda e: resetta_campo())
    frame_treeview_container = ttk.Frame(pdf_window)
    frame_treeview_container.pack(fill='both', expand=True, padx=10, pady=5)
    cols = ("data", "categoria", "descrizione", "importo", "tipo", "nome_completo")
    vsb = ttk.Scrollbar(frame_treeview_container, orient="vertical", style="Vertical.TScrollbar")
    tree = ttk.Treeview(frame_treeview_container, columns=cols, show='headings', selectmode='extended', yscrollcommand=vsb.set)
    self.tabella_documenti = tree
    vsb.config(command=tree.yview)
    vsb.pack(side='right', fill='y') 
    tree.pack(side='left', fill='both', expand=True) 
    col_widths = {'data': 100, 'categoria': 150, 'descrizione': 300, 'importo': 100, 'tipo': 70, 'nome_completo': 0}
    col_anchors = {'data': 'center', 'categoria': 'w', 'descrizione': 'w', 'importo': 'e', 'tipo': 'center', 'nome_completo': 'w'}
    for col in cols:
        tree.heading(col, text=col.capitalize(), command=lambda c=col: self.treeview_sort_column(tree, c, False))
        tree.column(col, width=col_widths.get(col, 100), anchor=col_anchors.get(col, 'w'))
    tree.column("nome_completo", width=0, stretch=tk.NO) 
    tree.tag_configure('uscita_tag', foreground='red')
    tree.tag_configure('entrata_tag', foreground='green') 
    tree.bind('<Double-1>', lambda e: open_pdf(e, tree))
    tree.bind('<Delete>', lambda e: cancella_documento())
    tree.bind('<Button-3>', lambda event: esporta_documenti_selezionati())
    self._bind_tooltip_metodo(tree, col_desc=2)
    frame_bottom_buttons = ttk.Frame(pdf_window, padding="10") 
    frame_bottom_buttons.pack(fill='x', padx=10, pady=(5, 10))
    btn_archivia = ttk.Label(
            frame_bottom_buttons, 
            image=self.icone_gui.get("archivia"), 
            text=" Archivia PDF" if self.icone_gui.get("archivia") else "Archivia PDF", 
            compound="left",
            cursor="hand2",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR
    )
    btn_archivia.image = self.icone_gui.get("archivia")
    btn_archivia.pack(side='left', padx=10)
    btn_archivia.bind("<Button-1>", lambda e: inserisci_documento_e_copia())
    btn_modifica = ttk.Label(
        frame_bottom_buttons,
        image=self.icone_gui.get("modifica"),
        text=" Modifica" if self.icone_gui.get("modifica") else "Modifica",
        compound="left", cursor="hand2",
        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR
    )
    btn_modifica.image = self.icone_gui.get("modifica")
    btn_modifica.pack(side='left', padx=10)
    btn_modifica.bind("<Button-1>", lambda e: modifica_documento())
    btn_cancella = ttk.Label(
            frame_bottom_buttons, 
            image=self.icone_gui.get("cancella"), 
            text=" Cancella Documenti" if self.icone_gui.get("cancella") else "Cancella Documenti", 
            compound="left",
            cursor="hand2",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR
    )
    btn_cancella.image = self.icone_gui.get("cancella")
    btn_cancella.pack(side='left', padx=10)
    btn_cancella.bind("<Button-1>", lambda e: cancella_documento())
    btn_stampa = ttk.Label(
            frame_bottom_buttons, 
            image=self.icone_gui.get("stampa"), 
            text=" Stampa Selezionati" if self.icone_gui.get("stampa") else "Stampa Selezionati", 
            compound="left",
            cursor="hand2",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR
    )
    btn_stampa.image = self.icone_gui.get("stampa")
    btn_stampa.pack(side='left', padx=10)
    btn_stampa.bind("<Button-1>", lambda e: stampa_documenti_selezionati())
    btn_chiudi = ttk.Label(
            frame_bottom_buttons, 
            image=self.icone_gui.get("chiudi"), 
            text=" Chiudi" if self.icone_gui.get("chiudi") else "Chiudi", 
            compound="left",
            cursor="hand2",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR
    )
    btn_esporta = ttk.Label(
        frame_bottom_buttons, 
        image=self.icone_gui.get("salva"), 
        text=" Esporta" if self.icone_gui.get("backup") else "Esporta", 
        compound="left",
        cursor="hand2",
        background=self.COLOR_WIDGET_BG,
        foreground=self.TEXT_COLOR)
    btn_esporta.image = self.icone_gui.get("backup")
    btn_esporta.pack(side='left', padx=10)
    btn_esporta.bind("<Button-1>", lambda e: esporta_documenti_selezionati())
    btn_chiudi.image = self.icone_gui.get("chiudi")
    btn_chiudi.pack(side='right', padx=10)
    btn_chiudi.bind("<Button-1>", lambda e: chiudi_finestra())
    filtra_documenti() 
    self.wait_window(pdf_window)
def mostra_help_pdf(self):
    if hasattr(self, '_filter_help_popup') and self._filter_help_popup.winfo_exists():
        self._filter_help_popup.destroy()
    popup_aiuto = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    popup_aiuto.title("Guida: Archivio Documenti Contabili")
    popup_width = 950
    popup_height = 500
    screen_width = self.winfo_screenwidth()
    screen_height = self.winfo_screenheight()
    center_x = int((screen_width / 2) - (popup_width / 2))
    center_y = int((screen_height / 2) - (popup_height / 2))
    popup_aiuto.geometry(f"{popup_width}x{popup_height}+{center_x}+{center_y}")
    popup_aiuto.resizable(False, False)
    popup_aiuto.transient(self)
    popup_aiuto.update_idletasks()
    popup_aiuto.grab_set() 
    popup_aiuto.focus_set()
    self._filter_help_popup = popup_aiuto
    main_frame = ttk.Frame(popup_aiuto, padding="15")
    main_frame.pack(fill="both", expand=True)
    content_frame = tk.Frame(main_frame)
    content_frame.pack(fill="both", expand=True)
    def ottieni_contenuto_testo():
        testo = ""

        testo += "=================================================\n"
        testo += "          HELP: ARCHIVIO DOCUMENTI CONTABILI PDF\n"
        testo += "=================================================\n"

        testo += "\nArchiviazione Nuovi Documenti:\n"
        testo += "---------------------------------------\n"
        testo += "• Campi di Archiviazione: I campi nel pannello superiore sono obbligatori e vengono usati per creare il nome univoco del file e per registrare i metadati nel registro locale.\n\n"
        testo += "• Archivia PDF (Bottone Verde): Apre il selettore file. Il PDF selezionato viene copiato nella directory locale (db/doc). Attenzione: se il nome file generato esiste già, il file viene sovrascritto.\n"

        testo += "\nNavigazione e Interazione (Treeview Documenti):\n"
        testo += "---------------------------------------------------------\n"
        testo += "• Apertura Documento (Doppio Clic): Doppio clic su una riga per aprire il file PDF associato.\n"
        testo += "• Ordinamento: Clicca sull'intestazione di qualsiasi colonna (Data, Importo, Categoria, ecc.) per ordinare i dati.\n"
        testo += "• Esportazione Selezionata (Tasto Destro): Seleziona righe, clicca Tasto Destro per esportare i file in una cartella esterna.\n"
        testo += "  > Utilizza CTRL + Click per selezionare righe sparse, o SHIFT + Click per selezionare un intervallo continuo.\n"
        testo += "• Scroll e Navigazione: Utilizza la Rotella del Mouse per scorrere verticalmente in qualsiasi Treeview o area.\n"
        testo += "• Cancellazione (Canc/Bottone): Seleziona una riga e premi CANC (o usa il bottone 'Cancella Documento') per eliminare file e registro.\n"

        testo += "\nRicerca e Filtraggio:\n"
        testo += "----------------------------\n"

        testo += "• Ricerca Veloce: Digita una parola chiave; la ricerca è effettuata su nome file, data, categoria, descrizione e tipo.\n"
        testo += "• Filtri Avanzati (Bottone Filtro): Filtra documenti per Intervallo di Data, Intervallo di Importo, Categoria Esatta e Tipo (Entrata/Uscita).\n"
 
        testo += "\nOperazioni di Sistema (Menu Archivio):\n"
        testo += "--------------------------------------------------\n"

        testo += "• Esporta documenti: Crea un archivio ZIP contenente tutti i PDF e il file di registro (.json) per il backup.\n"
        testo += "• Importa documenti: Carica un archivio ZIP esportato. Attenzione: questa operazione è distruttiva e sovrascrive tutti i documenti e il registro esistenti.\n"
        
        return testo.strip()
    tk.Label(
        content_frame, 
        text="Archiviazione Nuovi Documenti:", 
        font=("Arial", 11, "bold"), 
        anchor='w'
    ).pack(pady=(5, 5), fill='x')
    tk.Label(
        content_frame,
        text="• Campi di Archiviazione: I campi nel pannello superiore sono obbligatori e vengono usati per creare il nome univoco del file\n      e per registrare i metadati nel registro locale.\n\n"
             "• Archivia PDF (Bottone Verde): Apre il selettore file. Il PDF selezionato viene copiato nella directory locale (`db/doc`).\n      Attenzione: se il nome file generato esiste già, il file viene sovrascritto.",
        font=("Arial", 9),
        justify=tk.LEFT,
        anchor='w',
        wraplength=900 
    ).pack(fill='x', padx=5, pady=(0, 5))
    tk.Label(
        content_frame, 
        text="Navigazione e Interazione (Treeview Documenti):", 
        font=("Arial", 11, "bold"), 
        anchor='w'
    ).pack(pady=(10, 5), fill='x')
    tk.Label(
        content_frame,
        text="• Apertura Documento (Doppio Clic): Doppio clic su una riga per aprire il file PDF associato.\n"
             "• Ordinamento: Clicca sull'intestazione di qualsiasi colonna (Data, Importo, Categoria, ecc.) per ordinare i dati.\n"
             "• Esportazione Selezionata (Tasto Destro): Seleziona righe, clicca Tasto Destro per esportare i file in una cartella esterna.\n"
             "  > Utilizza CTRL + Click per selezionare righe sparse (selezione mista), o SHIFT + Click per selezionare un intervallo continuo di righe.\n" 
             "• Scroll e Navigazione: Utilizza la Rotella del Mouse per scorrere verticalmente in qualsiasi Treeview o area.\n"
             "• Cancellazione (Canc/Bottone): Seleziona una riga e premi CANC (o usa il bottone '📄 Cancella Documento') per eliminare file e registro.",
        font=("Arial", 9),
        justify=tk.LEFT,
        anchor='w',
        wraplength=900
    ).pack(fill='x', padx=5, pady=(0, 5))
    tk.Label(
        content_frame, 
        text="Ricerca e Filtraggio:", 
        font=("Arial", 11, "bold"), 
        anchor='w'
    ).pack(pady=(10, 5), fill='x')
    tk.Label(
        content_frame,
        text="• Ricerca Veloce: Digita una parola chiave; la ricerca è effettuata su nome file, data, categoria, descrizione e tipo.\n"
             "• Filtri Avanzati (Bottone ⚙️): Filtra documenti per Intervallo di Data, Intervallo di Importo, Categoria Esatta e Tipo (Entrata/Uscita).",
        font=("Arial", 9),
        justify=tk.LEFT,
        anchor='w',
        wraplength=900
    ).pack(fill='x', padx=5, pady=(0, 5))
    tk.Label(
        content_frame, 
        text="Operazioni di Sistema (Menu 📂 Archivio):", 
        font=("Arial", 11, "bold"), 
        anchor='w'
    ).pack(pady=(10, 5), fill='x')
    tk.Label(
        content_frame,
        text="• Esporta documenti: Crea un archivio ZIP contenente tutti i PDF e il file di registro (`.json`) per il backup.\n"
             "• Importa documenti: Carica un archivio ZIP esportato. Attenzione: questa operazione è distruttiva e sovrascrive tutti i documenti e il registro esistenti.",
        font=("Arial", 9),
        justify=tk.LEFT,
        anchor='w',
        wraplength=900
    ).pack(fill='x', padx=5, pady=(0, 5))
    bottom_frame = tk.Frame(main_frame, bg=self.COLOR_TOPLEVEL)
    bottom_frame.pack(side=tk.BOTTOM, fill='x', pady=5)
    img_stampa = self.icone_gui.get("stampa")
    btn_stampa_guida = ttk.Label(
            bottom_frame,
            compound="left",
            image=img_stampa,
            text=" Stampa Guida" if img_stampa else "Stampa Guida",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_stampa_guida.image = img_stampa
    btn_stampa_guida.pack(side=tk.LEFT, pady=5, padx=10)
    btn_stampa_guida.bind("<Button-1>", lambda e: self._stampa_lista_diretta(
            ottieni_contenuto_testo(), 
            self.show_custom_warning
    ))
    img_check = self.icone_gui.get("check")
    btn_ok = ttk.Label(
            bottom_frame,
            compound="left",
            image=img_check,
            text=" Ho Capito (OK)" if img_check else "Ho Capito (OK)",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2"
    )
    btn_ok.image = img_check
    btn_ok.pack(side=tk.RIGHT, pady=5, padx=10)
    btn_ok.bind("<Button-1>", lambda e: popup_aiuto.destroy())
    popup_aiuto.bind("<Escape>", lambda e: popup_aiuto.destroy())
    popup_aiuto.wait_visibility()
    popup_aiuto.grab_set()
    popup_aiuto.focus_set()
    
def esegui_export_documenti_pdf(self):
    import __main__ as _app
    DOC_DIR       = _app.DOC_DIR
    REGISTRY_FILE = _app.REGISTRY_FILE
    EXP_DB        = _app.EXP_DB
    from datetime import datetime
    backup_formato = "zip"
    current_folder = os.path.basename(DOC_DIR)
    percorso_archivio = ""
    cartella_temp_path = None
    if not os.path.exists(DOC_DIR):
        self.show_custom_warning("Attenzione", f"La cartella sorgente '{DOC_DIR}' non esiste. Backup annullato.")
        return ""
    try:
        timestamp = datetime.now().strftime("%Y%m%d")
        default_name = f"Archivio_Doc-{timestamp}"
        percorso_completo_output = filedialog.asksaveasfilename(
            title="Path Archivio ZIP",
            initialdir=EXP_DB,
            initialfile=default_name,
            confirmoverwrite=False,
            defaultextension=f".{backup_formato}",
            filetypes=[(f"Archivi {backup_formato.upper()}", f"*.{backup_formato}"), ("Tutti i file", "*.*")]
        )
        if not percorso_completo_output:
            return ""
        self.update_idletasks()
        self.update() 
        percorso_output_senza_ext, _ = os.path.splitext(percorso_completo_output)
        cartella_temp_path = tempfile.mkdtemp()
        cartella_dati_nel_temp_path = os.path.join(cartella_temp_path, current_folder)
        shutil.copytree(
            DOC_DIR,
            cartella_dati_nel_temp_path,
            dirs_exist_ok=True
        )
        if os.path.exists(REGISTRY_FILE):
            destinazione_registro = os.path.join(cartella_temp_path, os.path.basename(REGISTRY_FILE))
            shutil.copy2(REGISTRY_FILE, destinazione_registro)
        percorso_archivio = shutil.make_archive(
            base_name=percorso_output_senza_ext,
            format=backup_formato,
            root_dir=cartella_temp_path,
            base_dir=''
        )
        self.show_custom_warning("Salvataggio", f"Estrazione Archivio PDF completato.\n\nFile salvato in: {percorso_archivio}")
    except Exception as e:
        self.show_custom_warning("Errore Backup", f"Errore durante la creazione del backup dei PDF: {e}")
    finally:
        if cartella_temp_path and os.path.exists(cartella_temp_path):
            shutil.rmtree(cartella_temp_path, ignore_errors=True)
    return percorso_archivio
def esegui_import_documenti_pdf(self):
    import __main__ as _app
    DB_DIR        = _app.DB_DIR
    DOC_DIR       = _app.DOC_DIR
    REGISTRY_FILE = _app.REGISTRY_FILE
    DB_CONDIVISO  = _app.DB_CONDIVISO
    EXP_DB        = _app.EXP_DB
    current_folder_name = os.path.basename(DOC_DIR)
    registry_file_name = os.path.basename(REGISTRY_FILE)
    backup_file_path = filedialog.askopenfilename(
        title="Seleziona ZIP",
        defaultextension=".zip",
        initialdir=EXP_DB,
        filetypes=[("Archivi ZIP", "Archivio_Doc-*.zip"), ("Tutti i file", "*.*")]
    )
    if not backup_file_path:
        return
    cartella_temp_path = None
    try:
        cartella_temp_path = tempfile.mkdtemp()
        try:
            with zipfile.ZipFile(backup_file_path, 'r') as zip_ref:
                zip_ref.extractall(cartella_temp_path)
        except zipfile.BadZipFile:
            self.show_custom_warning("Errore Importazione", "Il file selezionato non è un archivio ZIP valido.")
            return
        temp_pdf_dir = os.path.join(cartella_temp_path, current_folder_name)
        temp_registry_file = os.path.join(cartella_temp_path, registry_file_name)
        if not os.path.isdir(temp_pdf_dir):
             self.show_custom_warning("Errore Importazione", f"Archivio non valido. Manca la cartella '{current_folder_name}' al suo interno.")
             return
        registry_present = os.path.exists(temp_registry_file)
        messaggio_conferma = (
            "ATTENZIONE: Stai per importare un backup.\n\n"
            "Sei sicuro di voler procedere con la\nSOVRASCRITTURA?"
        )
        response = self.show_custom_askyesno("Conferma Importazione e Sovrascrittura", messaggio_conferma)
        if not response:
            return   
        if os.path.exists(DOC_DIR):
            shutil.rmtree(DOC_DIR)
        shutil.copytree(temp_pdf_dir, DOC_DIR)
        if registry_present:
            if not os.path.exists(DB_DIR): os.makedirs(DB_DIR) 
            shutil.copy2(temp_registry_file, REGISTRY_FILE)
        if hasattr(self, 'pdf_window') and self.pdf_window.winfo_exists():
            self.filtri_avanzati = {}
            tabella = getattr(self, 'tabella_documenti', None)
            funzione_load = getattr(self, 'funzione_carica_documenti', None)
            if tabella and funzione_load:
                for i in tabella.get_children():
                    tabella.delete(i)
                funzione_load(tabella, {}) 
                self.show_custom_info("Importazione Riuscita", "Lista aggiornata correttamente.")
            # DataBase Condiviso
            if DB_CONDIVISO:
                self.notifica_modifica_web()
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 📡 Notifica di aggiornamento inviata .")    
    except Exception as e:
        self.show_custom_warning("Errore Importazione", f"Si è verificato un errore critico durante l'importazione: {e}")
    finally:
        if cartella_temp_path and os.path.exists(cartella_temp_path):
            shutil.rmtree(cartella_temp_path, ignore_errors=True)
def backup_documenti(self):
    import __main__ as _app
    DOC_DIR       = _app.DOC_DIR
    REGISTRY_FILE = _app.REGISTRY_FILE
    BASE_DIR      = _app.BASE_DIR
    from datetime import datetime
    current_folder = os.path.basename(DOC_DIR)
    if not os.path.exists(DOC_DIR):
       os.makedirs(DOC_DIR)
    try:
        cartella_dest_backup = os.path.join(BASE_DIR, "backup")
        os.makedirs(cartella_dest_backup, exist_ok=True)
        files_esistenti = [os.path.join(cartella_dest_backup, f) for f in os.listdir(cartella_dest_backup)
                            if f.startswith("Archivio_Doc_Contabili") and f.endswith(".zip")]
        if files_esistenti:
            ultimo_backup_mtime = max(os.path.getmtime(f) for f in files_esistenti)
            ultima_modifica = 0.0
            for root, _, fnames in os.walk(DOC_DIR):
                for fn in fnames:
                    m = os.path.getmtime(os.path.join(root, fn))
                    if m > ultima_modifica:
                        ultima_modifica = m
            if os.path.exists(REGISTRY_FILE):
                ultima_modifica = max(ultima_modifica, os.path.getmtime(REGISTRY_FILE))
            if ultima_modifica <= ultimo_backup_mtime:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Backup Documenti Contabili: nessuna modifica, salto.")
                return
        timestamp = datetime.now().strftime("%d%m%Y_%H%M")
        nome_file_nuovo = f"Archivio_Doc_Contabili-{timestamp}.zip"
        percorso_archivio = os.path.join(cartella_dest_backup, nome_file_nuovo)
        with zipfile.ZipFile(percorso_archivio, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for root, _, fnames in os.walk(DOC_DIR):
                for fn in fnames:
                    percorso_completo = os.path.join(root, fn)
                    percorso_nello_zip = os.path.join(current_folder, os.path.relpath(percorso_completo, DOC_DIR))
                    zf.write(percorso_completo, percorso_nello_zip)
            if os.path.exists(REGISTRY_FILE):
                zf.write(REGISTRY_FILE, os.path.basename(REGISTRY_FILE))
        files = [os.path.join(cartella_dest_backup, f) for f in os.listdir(cartella_dest_backup) if f.startswith("Archivio_Doc_Contabili") and f.endswith(".zip")]
        files.sort(key=os.path.getmtime)
        while len(files) > 3:
            file_da_eliminare = files.pop(0)
            os.remove(file_da_eliminare)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Backup Documenti Contabili (ZIP) completato.")    
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Errore durante il backup con data: {e}")
            
