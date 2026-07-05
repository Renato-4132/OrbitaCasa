#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import datetime
import tkinter as tk
from tkinter import ttk, filedialog

def rubrica_app(self):
    import __main__ as _app
    DATI_FILE    = _app.DATI_FILE
    EXP_DB       = _app.EXP_DB
    EXPORT_FILES = _app.EXPORT_FILES
    if hasattr(self, '_rubrica_window') and self._rubrica_window and self._rubrica_window.winfo_exists():
        self._rubrica_window.lift()
        return
    root = tk.Toplevel(self) 
    root.transient(self)
    self._rubrica_window = root     
    def on_rubrica_close():
        root.destroy()
        self._rubrica_window = None
    root.protocol("WM_DELETE_WINDOW", on_rubrica_close)
    root.bind("<Escape>", lambda e: on_rubrica_close())
    root.title("Rubrica Contatti")
    window_width, window_height = 1100, 600
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    pos_x = (screen_width - window_width) // 2
    pos_y = (screen_height - window_height) // 2
    root.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
    root.minsize(window_width, window_height)
    root.resizable(True, True)
    root.configure(bg=self.COLOR_TOPLEVEL)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(2, weight=1)
    barra_menu_popup = tk.Menu(root, bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT, activebackground=self.MENU_ACT_BG_COLOR, activeforeground=self.MENU_ACT_FG_COLOR)
    barra_menu_popup.config(bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT)
    root.config(menu=barra_menu_popup)
    menu_db = tk.Menu(barra_menu_popup, tearoff=0, bg=self.MENU_BG, fg=self.MENU_FG_LIGHT, activebackground=self.MENU_ACT_BG_COLOR, activeforeground=self.MENU_ACT_FG_COLOR)
    barra_menu_popup.add_cascade(label="💾 Database", menu=menu_db)
    menu_db.add_command(label="📤 Esporta DataBase", command=lambda: esporta_rubrica())
    menu_db.add_command(label="📥 Importa Database", command=lambda: importa_rubrica())
    menu_db.add_separator()
    menu_db.add_command(label="📥 Importa Rubrica vCard", command=lambda: importa_vcf_rubrica())
    menu_db.add_separator()
    menu_db.add_command(label="📥 Reset DataBase", command=lambda: reset_rubrica())
    menu_db.add_separator()
    menu_db.add_command(label="❌ Chiudi", command=lambda: on_rubrica_close())
    contatti = []
    def ordina_contatti():
        contatti.sort(key=lambda c: c["nome"].lower())
    def salva_su_json():
        with open(DATI_FILE, "w", encoding="utf-8") as f:
            json.dump(contatti, f, indent=2, ensure_ascii=False)
    def pulisci_campi():
        entry_nome.delete(0, tk.END)
        entry_telefono.delete(0, tk.END)
        entry_email.delete(0, tk.END)
        entry_note.delete("1.0", tk.END)
        tree_contatti.selection_remove(tree_contatti.selection()) 
    def aggiorna_lista():
        for i in tree_contatti.get_children():
            tree_contatti.delete(i)
        if not contatti:
            tree_contatti.insert("", tk.END, text="0", 
                                 values=("Aggiungi il tuo primo contatto!", "", "", ""), 
                                 tags=('empty',))
        else:
            for i, c in enumerate(contatti):
                tree_contatti.insert("", tk.END, iid=i, 
                                    values=(c["nome"], c["telefono"], c["email"], c["note"]))
    def carica_da_json():
        if os.path.exists(DATI_FILE):
            with open(DATI_FILE, "r", encoding="utf-8") as f:
                try:
                    dati = json.load(f)
                    contatti.clear()
                    contatti.extend(dati)
                    ordina_contatti()
                    aggiorna_lista()
                except:
                    self.show_custom_warning("Attenzione", "File rubrica non valido !")
    def seleziona_contatto(event):
        selected_items = tree_contatti.selection()
        if not selected_items:
            return
        iid = selected_items[0]
        if tree_contatti.tag_has('empty', iid):
            pulisci_campi()
            return
        try:
            indice = int(iid)
            c = contatti[indice] 
        except (ValueError, IndexError):
            pulisci_campi()
            return
        entry_nome.delete(0, tk.END)
        entry_nome.insert(0, c["nome"])
        entry_telefono.delete(0, tk.END)
        entry_telefono.insert(0, c["telefono"])
        entry_email.delete(0, tk.END)
        entry_email.insert(0, c["email"])
        entry_note.delete("1.0", tk.END)
        entry_note.insert("1.0", c["note"])
    def aggiungi_contatto():
        nome = entry_nome.get().strip()
        telefono = entry_telefono.get().strip()
        email = entry_email.get().strip()
        note = entry_note.get("1.0", tk.END).strip()
        if len(nome) > 43 or len(telefono) > 43 or len(email) > 43 or len(note) > 100:
            self.show_custom_warning("Limite superato", 
                     "Hai superato il limite massimo di caratteri:\n\n"
                     "- Nome: 43\n- Telefono: 43\n- Email: 43\n- Note: 100")
            return
        if nome:
            contatti.append({"nome": nome, "telefono": telefono, "email": email, "note": note})
            ordina_contatti()
            salva_su_json()
            aggiorna_lista()
            pulisci_campi()
            self.show_toast("Contatto aggiunto correttamente !")
        else:
            self.show_toast("Il campo Nome è obbligatorio.")
    def modifica_contatto():
        selected_items = tree_contatti.selection()
        if not selected_items: 
            self.show_toast("Seleziona un contatto valido da modificare.")
            return
        iid = selected_items[0]
        if tree_contatti.tag_has('empty', iid):
             self.show_toast("Seleziona un contatto valido da modificare.")
             return
        try:
            i = int(iid)
        except ValueError:
            self.show_toast("Selezione non valida per la modifica.")
            return
        contatti[i] = {
            "nome": entry_nome.get().strip(),
            "telefono": entry_telefono.get().strip(),
            "email": entry_email.get().strip(),
            "note": entry_note.get("1.0", tk.END).strip()
        }
        ordina_contatti()
        salva_su_json()
        pulisci_campi() 
        aggiorna_lista()
        self.show_toast("Contatto modificato correttamente!")
    def cancella_contatto():
        selected_items = tree_contatti.selection()
        if not selected_items: return self.show_toast("Nessun contatto selezionato.")
        iid = selected_items[0]
        if tree_contatti.tag_has('empty', iid):
            self.show_toast("Nessun contatto valido selezionato per la cancellazione.")
            return
        try:
            i = int(iid)
        except ValueError:
            return
        contatti.pop(i) 
        salva_su_json()
        pulisci_campi() 
        aggiorna_lista()
        self.show_toast("Contatto cancellato con successo !")
    def cerca_contatto(event=None):
        query = entry_cerca.get().lower()
        for i in tree_contatti.get_children():
            tree_contatti.delete(i)
        risultati_trovati = False
        if not query:
            aggiorna_lista()
            return
        for i, c in enumerate(contatti):
            if query in c["nome"].lower() or query in c["telefono"].lower() or query in c["email"].lower():
                tree_contatti.insert("", tk.END, iid=i, 
                                    values=(c["nome"], c["telefono"], c["email"], c["note"]))
                risultati_trovati = True
        if not risultati_trovati:
            tree_contatti.insert("", tk.END, tags=('empty',), 
                                 values=("Nessun contatto trovato.", "", "", ""))
        pulisci_campi()
    def reset_rubrica():
        conferma = self.show_custom_askyesno("Reset Rubrica", "Sei sicuro di voler cancellare tutti i contatti?")
        if conferma:
            try:
                if os.path.exists(DATI_FILE):
                    os.remove(DATI_FILE)
                contatti.clear()
                aggiorna_lista()
                self.show_custom_warning("Reset", "Rubrica resettata con successo. Contatti e file dati eliminati.")
            except Exception as e:
                self.show_custom_warning("Errore", f"Si è verificato un errore durante il reset del file:\n{e}")
    def _parse_vcard_content_inner(vcard_content):
        contatti_importati = []
        vcard_blocks = re.findall(r"BEGIN:VCARD.*?END:VCARD", vcard_content, re.DOTALL)
        for block in vcard_blocks:
            nome = ""
            all_telefoni = []
            email_principale = ""
            note = [] 
            for line in block.split('\n'):
                line = line.strip()
                if not line:
                    continue
                if line.startswith(' '):
                    if note:
                        note[-1] += line.strip()
                    continue
                match_prop = re.match(r"([^:]+):(.*)", line, re.IGNORECASE)
                if not match_prop:
                    continue
                prop_data = match_prop.group(1).split(';')
                prop_name = prop_data[0].upper()
                prop_value = match_prop.group(2).strip()
                if prop_name == "FN":
                    nome = prop_value                        
                elif prop_name == "TEL":
                    number = prop_value.replace('-', ' ').strip()
                    if number:
                         all_telefoni.append(number)
                elif prop_name == "EMAIL":
                    if not email_principale:
                        email_principale = prop_value.strip()
                    else:
                        note.append(prop_value.strip()) 
                elif prop_name == "ADR":
                    addr_parts = prop_value.split(';')
                    street = addr_parts[2].strip() if len(addr_parts) > 2 and addr_parts[2] else ""
                    city = addr_parts[3].strip() if len(addr_parts) > 3 and addr_parts[3] else ""
                    region = addr_parts[4].strip() if len(addr_parts) > 4 and addr_parts[4] else ""
                    clean_addr = []
                    if street: clean_addr.append(street)
                    if city: clean_addr.append(city)
                    if region and region != city: clean_addr.append(region)
                    if clean_addr: note.append(', '.join(clean_addr))
                elif prop_name == "ORG":
                    note.append(prop_value.strip())
                elif prop_name == "NOTE":
                    note.append(prop_value.strip())
                elif prop_name in ["URL"]:
                    note.append(f"{prop_name}: {prop_value.strip()}")
            telefono_finale = ', '.join(all_telefoni)
            note_finale = "\n".join(note)
            if nome:
                contatti_importati.append({
                    "nome": nome,
                    "telefono": telefono_finale, 
                    "email": email_principale,
                    "note": note_finale
                })
        return contatti_importati
    def importa_vcf_rubrica():
        initial_dir = EXP_DB if 'EXP_DB' in globals() else os.getcwd()
        path = filedialog.askopenfilename(
            defaultextension=".vcf",
            filetypes=[("File VCF", "*.vcf")],
            initialdir=initial_dir,
            title="Importa Rubrica da File .vCard",
            parent=root
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    vcf_content = f.read()
                dati_importati = _parse_vcard_content_inner(vcf_content)
                if dati_importati:
                    conferma = self.show_custom_askyesno(
                        "Importazione vCard",
                        f"Trovati {len(dati_importati)} contatti.\nVuoi SOSTITUIRE la rubrica esistente con i nuovi contatti (Sì) o UNIRLI (No)?"
                    )
                    if conferma:
                        contatti.clear()
                        contatti.extend(dati_importati)
                        self.show_custom_warning("Importazione vCard", f"Rubrica SOSTITUITA con {len(dati_importati)} contatti.")
                    else:
                        contatti.extend(dati_importati)
                        self.show_custom_warning("Importazione vCard", f"Aggiunti {len(dati_importati)} contatti alla rubrica esistente.")
                    ordina_contatti()
                    salva_su_json()
                    aggiorna_lista()
                else:
                    self.show_custom_warning("Attenzione", "Il file vCard non contiene contatti validi.")
            except Exception as e:
                self.show_custom_warning("Errore di Importazione", f"Impossibile leggere o analizzare il file vCard:\n{e}")
    def esporta_rubrica():
        now = datetime.date.today()
        default_dir = EXP_DB 
        default_filename = f"{now.day:02d}-{now.month:02d}-{now.year}-rubrica.json"
        if not contatti:
            self.show_toast("Nessun contatto, la rubrica e' vuota !")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("File JSON", "*rubrica.json"), ("Tutti i file", "*.*")],
            initialdir=default_dir,
            initialfile=default_filename,
            title="Salva Rubrica .json",
            confirmoverwrite=False,
            parent=root
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(contatti, f, indent=2, ensure_ascii=False)
                self.show_custom_warning("Attenzione", f"Rubrica salvata con successo in {path}")
            except Exception as e:
                self.show_custom_warning("Attenzione", f"Impossibile salvare la rubrica:\n{e}")
    def importa_rubrica():
        path = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("File JSON", "*rubrica.json"), ("Tutti i file", "*.*")],
            initialdir=EXP_DB,
            parent=root
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    dati_importati = json.load(f)
                    if isinstance(dati_importati, list):
                        contatti.clear()
                        contatti.extend(dati_importati)
                        ordina_contatti()
                        aggiorna_lista()
                        self.show_custom_warning("Importazione riuscita", "Rubrica importata correttamente!")
                    else:
                        self.show_custom_warning("Errore", "Il file selezionato non contiene una rubrica valida (non è un elenco).")
            except json.JSONDecodeError:
                self.show_custom_warning("Errore", "Il file non è un JSON valido.")
            except Exception as e:
                self.show_custom_warning("Errore", f"Impossibile importare la rubrica:\n{e}")
    def esporta_txt():
        if not contatti:
            self.show_toast("Nessun Contatto. Rubrica vuota. L'anteprima non può essere aperta.")
            return
        contenuto_txt = []
        for c in contatti:
            linea1 = f"Nome: {c['nome']}  Telefono: {c['telefono']}"
            linea2 = f"Email: {c['email']}"
            linea3 = f"Note: {c['note']}"
            contenuto_txt.append(linea1)
            if c['email']: contenuto_txt.append(linea2)
            if c['note']: contenuto_txt.append(linea3)
            contenuto_txt.append("─" * 70)
        contenuto = "\n".join(contenuto_txt).strip()
        if not contenuto:
            self.show_custom_warning("Esporta", "Contenuto rubrica generato vuoto. Nulla da esportare.")
            return
        try:
            preview = tk.Toplevel(root, bg=self.COLOR_TOPLEVEL) 
            preview.title("Preview Esportazione Rubrica")
            larghezza_finestra = 800
            altezza_finestra = 600
            x = root.winfo_rootx() + (root.winfo_width() // 2) - (larghezza_finestra // 2)
            y = root.winfo_rooty() + (root.winfo_height() // 2) - (altezza_finestra // 2)
            preview.geometry(f"{larghezza_finestra}x{altezza_finestra}+{x}+{y}")
            preview.minsize(larghezza_finestra, altezza_finestra)
            preview.transient(root)
            preview.update_idletasks()
            preview.grab_set()
            preview.focus_set()
            preview.bind("<Escape>", lambda e: preview.destroy())
            text_frame = tk.Frame(preview)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(10, 5))
            vsb = ttk.Scrollbar(text_frame, orient="vertical", style="Vertical.TScrollbar")
            vsb.pack(side=tk.RIGHT, fill=tk.Y)
            tx = tk.Text(text_frame, font=("Courier new", 10), wrap="none", yscrollcommand=vsb.set)
            tx.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            vsb.config(command=tx.yview)
            tx.insert(tk.END, contenuto)
            tx.config(state="disabled")
            frm = tk.Frame(preview, bg=self.COLOR_TOPLEVEL)
            frm.pack(fill=tk.X, padx=10, pady=8)
            def do_save():
                now = datetime.date.today()
                default_filename = f"Rubrica_Export_{now.day:02d}-{now.month:02d}-{now.year}.txt"
                file = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[("File txt", "*.txt")],
                    initialdir=EXPORT_FILES,
                    title="Esporta Rubrica",
                    initialfile=default_filename,
                    confirmoverwrite=False,
                    parent=preview)
                if file:
                    if os.path.exists(file):
                        conferma = self.show_custom_askyesno("Sovrascrivere file?",
                            f"Il file '{os.path.basename(file)}' \nesiste già. Vuoi sovrascriverlo?")
                        if not conferma:
                            return  
                    with open(file, "w", encoding="utf-8") as f:
                        f.write(contenuto) 
                        self.show_custom_warning("Esporta", f"Rubrica esportata in {file}")
                    preview.destroy() 
            img_salva_p = self.icone_gui.get("salva")
            btn_salva_p = ttk.Label(frm, compound="left", image=img_salva_p, text=" Salva" if img_salva_p else "Salva", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
            btn_salva_p.pack(side=tk.LEFT, padx=6)
            btn_salva_p.bind("<Button-1>", lambda e: do_save())
            img_stampa_p = self.icone_gui.get("stampa")
            btn_stampa_p = ttk.Label(frm, compound="left", image=img_stampa_p, text=" Stampa" if img_stampa_p else "Stampa", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
            btn_stampa_p.pack(side=tk.LEFT, padx=6)
            btn_stampa_p.bind("<Button-1>", lambda e: self._stampa_lista_diretta(contenuto, self.show_custom_warning))
            img_chiudi_p = self.icone_gui.get("chiudi")
            btn_chiudi_p = ttk.Label(frm, compound="left", image=img_chiudi_p, text=" Chiudi" if img_chiudi_p else "Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
            btn_chiudi_p.pack(side=tk.RIGHT, padx=6)
            btn_chiudi_p.bind("<Button-1>", lambda e: preview.destroy())
            preview.lift()
            preview.attributes('-topmost', True)
            preview.after(100, lambda: preview.attributes('-topmost', False))
        except Exception as e:
            self.show_custom_warning("Errore Apertura", f"Errore nell'apertura dell'anteprima: {e}")
    frame_input = ttk.Frame(root)
    frame_input.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
    frame_input.columnconfigure(1, weight=1)
    ttk.Label(frame_input, text="Nome:").grid(row=0, column=0, sticky="e")
    entry_nome = ttk.Entry(frame_input)
    entry_nome.grid(row=0, column=1, padx=5, pady=2, sticky="ew")
    ttk.Label(frame_input, text="Telefono:").grid(row=1, column=0, sticky="e")
    entry_telefono = ttk.Entry(frame_input)
    entry_telefono.grid(row=1, column=1, padx=5, pady=2, sticky="ew")
    ttk.Label(frame_input, text="Email:").grid(row=2, column=0, sticky="e")
    entry_email = ttk.Entry(frame_input)
    entry_email.grid(row=2, column=1, padx=5, pady=2, sticky="ew")
    ttk.Label(frame_input, text="Note:").grid(row=3, column=0, sticky="ne")
    entry_note_frame = ttk.Frame(frame_input, padding=1)
    entry_note_frame.grid(row=3, column=1, padx=5, pady=2, sticky="ew")
    entry_note_frame.columnconfigure(0, weight=1)
    entry_note = tk.Text(
        entry_note_frame, 
        height=5, 
        relief=tk.FLAT,
        borderwidth=0,
        bg=self.COLOR_WIDGET_BG,
        fg=self.TEXT_COLOR, 
        insertbackground=self.TEXT_COLOR,
        padx=5, pady=5
    )
    entry_note.pack(fill=tk.BOTH, expand=True)
    frame_cerca = ttk.Frame(root)
    frame_cerca.grid(row=1, column=0, padx=10, pady=(5, 10), sticky="ew")
    frame_cerca.columnconfigure(1, weight=1)
    ttk.Label(frame_cerca, text="Cerca:").grid(row=0, column=0, sticky="e", padx=(0, 5))
    entry_cerca = ttk.Entry(frame_cerca)
    entry_cerca.grid(row=0, column=1, sticky="ew", padx=5)
    entry_cerca.bind("<Return>", cerca_contatto)
    entry_cerca.bind("<KP_Enter>", cerca_contatto)
    tree_frame = ttk.Frame(root)
    tree_frame.grid(row=2, column=0, padx=10, pady=10, sticky="nsew")
    tree_frame.columnconfigure(0, weight=1)
    tree_frame.rowconfigure(0, weight=1)
    vsb = ttk.Scrollbar(tree_frame, orient="vertical", style="Vertical.TScrollbar")
    vsb.grid(row=0, column=1, sticky="ns")
    tree_contatti = ttk.Treeview(
        tree_frame, 
        columns=("Nome", "Telefono", "Email", "Note"), 
        show="headings", 
        yscrollcommand=vsb.set
    )
    tree_contatti.grid(row=0, column=0, sticky="nsew")
    vsb.config(command=tree_contatti.yview)
    tree_contatti.heading("Nome", text="Nome")
    tree_contatti.heading("Telefono", text="Telefono")
    tree_contatti.heading("Email", text="Email")
    tree_contatti.heading("Note", text="Note")
    tree_contatti.column("Nome", width=180, anchor=tk.W)
    tree_contatti.column("Telefono", width=150, anchor=tk.W)
    tree_contatti.column("Email", width=220, anchor=tk.W)
    tree_contatti.column("Note", width=250, anchor=tk.W)
    tree_contatti.bind("<<TreeviewSelect>>", seleziona_contatto)
    frame_btn = ttk.Frame(root)
    frame_btn.grid(row=3, column=0, pady=10)
    img_agg_cont = self.icone_gui.get("aggiungi")
    btn_agg_cont = ttk.Label(frame_btn, compound="left", image=img_agg_cont, text=" Aggiungi" if img_agg_cont else "Aggiungi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
    btn_agg_cont.pack(side=tk.LEFT, padx=4)
    btn_agg_cont.bind("<Button-1>", lambda e: aggiungi_contatto())
    img_mod_cont = self.icone_gui.get("modifica")
    btn_mod_cont = ttk.Label(frame_btn, compound="left", image=img_mod_cont, text=" Modifica" if img_mod_cont else "Modifica", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
    btn_mod_cont.pack(side=tk.LEFT, padx=4)
    btn_mod_cont.bind("<Button-1>", lambda e: modifica_contatto())
    img_can_cont = self.icone_gui.get("delete")
    btn_can_cont = ttk.Label(frame_btn, compound="left", image=img_can_cont, text=" Cancella" if img_can_cont else "Cancella", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
    btn_can_cont.pack(side=tk.LEFT, padx=4)
    btn_can_cont.bind("<Button-1>", lambda e: cancella_contatto())
    img_esp_cont = self.icone_gui.get("stampa")
    btn_esp_cont = ttk.Label(frame_btn, compound="left", image=img_esp_cont, text=" Esporta/Stampa" if img_esp_cont else "Esporta/Stampa", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
    btn_esp_cont.pack(side=tk.LEFT, padx=4)
    btn_esp_cont.bind("<Button-1>", lambda e: esporta_txt())
    img_chiu_cont = self.icone_gui.get("chiudi")
    btn_chiu_cont = ttk.Label(frame_btn, compound="left", image=img_chiu_cont, text=" Chiudi" if img_chiu_cont else "Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
    btn_chiu_cont.pack(side=tk.LEFT, padx=4)
    btn_chiu_cont.bind("<Button-1>", lambda e: on_rubrica_close())
    root.update_idletasks()
    carica_da_json()
