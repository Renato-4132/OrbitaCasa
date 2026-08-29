#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import datetime
import tkinter as tk
from tkinter import ttk

from moduli.modello_spesa import campo

def _fmt_it(v, spec=",.2f"):
    s = format(v, spec)
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


# Visualizzazione e Gestione di Tutte le Ricorrenze Programmate (Dashboard)
def mostra_lista_ricorrenze(self):
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    import datetime
    if hasattr(self, 'lista_window_ref') and self.lista_window_ref.winfo_exists():
        self.lista_window_ref.lift()
        self.lista_window_ref.focus_force()
        return
    def parse_data(data_str):
        if isinstance(data_str, datetime.date):
            return data_str
        try:
            return datetime.datetime.strptime(data_str, "%d-%m-%Y").date()
        except (ValueError, TypeError):
            return None
    def calcola_data_fine(data_inizio, n_volte, periodo):
        if not data_inizio or not isinstance(n_volte, int) or n_volte < 1:
            return "N/D"
        periodo = periodo.lower().strip()
        if periodo == "ogni giorno":
            data_fine_obj = data_inizio + datetime.timedelta(days=n_volte - 1)
        elif periodo == "ogni mese":
            total_months = data_inizio.month + n_volte - 1
            anno_fine = data_inizio.year + (total_months - 1) // 12
            mese_fine = (total_months - 1) % 12 + 1
            giorno_inizio = data_inizio.day
            try:
                data_fine_obj = datetime.date(anno_fine, mese_fine, giorno_inizio)
            except ValueError:
                if mese_fine == 12:
                    primo_giorno_mese_successivo = datetime.date(anno_fine + 1, 1, 1)
                else:
                    primo_giorno_mese_successivo = datetime.date(anno_fine, mese_fine + 1, 1)
                ultimo_giorno_mese_fine = (primo_giorno_mese_successivo - datetime.timedelta(days=1)).day
                data_fine_obj = datetime.date(anno_fine, mese_fine, ultimo_giorno_mese_fine)
        elif periodo == "ogni anno":
            anno_fine = data_inizio.year + n_volte - 1
            try:
                data_fine_obj = data_inizio.replace(year=anno_fine)
            except ValueError:
                data_fine_obj = data_inizio.replace(year=anno_fine, day=28)
        else:
            return "N/D"
        return data_fine_obj.strftime("%d-%m-%Y")
    def destroy_window_and_cleanup():
        if hasattr(self, 'lista_window_ref') and self.lista_window_ref.winfo_exists():
            self.lista_window_ref.destroy() 
            delattr(self, 'lista_window_ref')
    def _delete_selected_ricorrenze():
        selected_ids = tree.selection()
        if not selected_ids:
            self.show_toast("Seleziona almeno una ricorrenza da cancellare.")
            return
        response = self.show_custom_askyesno(
            "Conferma Cancellazione", 
            f"Sei sicuro di voler cancellare {len(selected_ids)} ricorrenza/e selezionata/e?"
        )
        if not response:
            return
        ids_to_delete = list(selected_ids)
        deleted_count = 0
        voci_cancellate = []
        for ric_id in ids_to_delete:
            if ric_id not in self.ricorrenze:
                continue
            keys_to_delete = []
            for data_key, voci in list(self.spese.items()):
                nuove_voci = [
                    voce for voce in voci 
                    if campo(voce, "id_ricorrenza", None) != ric_id
                ]
                rimosse = [v for v in voci if campo(v, "id_ricorrenza", None) == ric_id]
                for v in rimosse:
                    voci_cancellate.append((data_key.strftime("%d-%m-%Y"), round(float(campo(v, "importo", 0.0)),2), campo(v, "tipo", "")))
                if nuove_voci:
                    self.spese[data_key] = nuove_voci
                else:
                    keys_to_delete.append(data_key)
            for data_key in keys_to_delete:
                del self.spese[data_key]
            del self.ricorrenze[ric_id]
            try:
                tree.delete(ric_id) 
                deleted_count += 1
            except tk.TclError:
                pass
        if deleted_count > 0:
            if hasattr(self, "db"):
                self.db["spese"] = self.spese
                self.db["ricorrenze"] = self.ricorrenze
            self.save_db()
            self.show_custom_info("Cancellazione Eseguita", f"Sono state rimosse con successo {deleted_count} transazione/i dal registro.")
        self.refresh_gui() 
        self.ricorrenza_cat_sel.set(self.categorie[0]) 
        self.ricorrenza_tipo_voce.set("Uscita")
        self.btn_tipo_voce.configure(text="Uscita", style="RedOutline.TButton")
    def treeview_sort_column(tv, col, reverse):
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        try:
            l.sort(key=lambda t: float(t[0].replace(' €', '').replace('.', '').replace(',', '.').strip()), reverse=reverse)
        except (ValueError, IndexError):
            l.sort(key=lambda t: t[0], reverse=reverse)
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)
        tv.heading(col, command=lambda: treeview_sort_column(tv, col, not reverse))
    lista_window = tk.Toplevel(self)
    self.lista_window_ref = lista_window
    lista_window.withdraw()
    self.update_idletasks()
    main_x = self.winfo_rootx()
    main_y = self.winfo_rooty()
    main_width = self.winfo_width()
    main_height = self.winfo_height()
    lista_window_width = 1300
    lista_window_height = 600
    center_x = main_x + (main_width // 2) - (lista_window_width // 2)
    center_y = main_y + (main_height // 2) - (lista_window_height // 2)
    lista_window.geometry(f"{lista_window_width}x{lista_window_height}+{center_x}+{center_y}")
    lista_window.minsize(lista_window_width, lista_window_height)
    lista_window.transient(self)
    lista_window.title("Lista delle Ricorrenze Programmate")
    lista_window.deiconify()
    lista_window.lift()
    lista_window.bind("<Escape>", lambda e: lista_window.after(50, destroy_window_and_cleanup))
    lista_window.protocol("WM_DELETE_WINDOW", lambda: lista_window.after(50, destroy_window_and_cleanup))
    main_frame = ttk.Frame(lista_window, padding=10)
    main_frame.pack(fill="both", expand=True)
    columns = ("Categoria", "Conto", "Metodo", "Tag", "Tipo", "Importo", "Durata", "Saldate", "Data Inizio", "Data Fine", "Importo Totale", "Contabilizzato", "Residuo", "ID")
    tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=12)
    tree.tag_configure("uscita", foreground="red")
    tree.tag_configure("entrata", foreground="green")
    larghezze = {"Categoria": 130, "Conto": 100, "Metodo": 100, "Tag": 100, "Tipo": 60, "Importo": 75, "Durata": 55, "Saldate": 55, "Data Inizio": 85, "Data Fine": 85, "Importo Totale": 100, "Contabilizzato": 100, "Residuo": 85, "ID": 90}
    for col in columns:
        tree.heading(col, text=col, command=lambda _col=col: self.treeview_sort_column(tree, _col, False))
        tree.column(col, width=larghezze[col], anchor="center")
    tree.pack(fill="both", expand=True)
    oggi = datetime.date.today()
    bilancio_mensile = 0.0
    conteggio_reale = {}
    for data_key, voci in self.spese.items():
        for voce in voci:
            rid = campo(voce, "id_ricorrenza", None)
            if rid and rid in self.ricorrenze:
                entry = conteggio_reale.setdefault(rid, {"volte": 0, "importo": 0.0})
                entry["volte"] += 1
                entry["importo"] += float(campo(voce, "importo", 0.0))
    for i, (id_ricorrenza, dati) in enumerate(self.ricorrenze.items()):
        cat = dati.get("cat", "Sconosciuta")
        conto = dati.get("conto") or ""
        metodo = dati.get("metodo_pagamento") or ""
        tag_str = " ".join(dati.get("hashtag", []) or [])
        tipo_voce = dati.get("tipo_voce", dati.get("tipo", "N/D"))
        imp = dati.get("imp", 0.0)
        n_volte = dati.get("n", 0)
        ric_periodo = dati.get("tipo", "N/D")
        data_inizio_str = dati.get("data_inizio", "N/D")
        data_inizio_obj = parse_data(data_inizio_str)
        data_fine = calcola_data_fine(data_inizio_obj, n_volte, ric_periodo)
        importo_totale = imp * n_volte if isinstance(n_volte, int) else 0.0
        reale = conteggio_reale.get(id_ricorrenza, {"volte": 0, "importo": 0.0})
        volte_passate = min(reale["volte"], n_volte) if isinstance(n_volte, int) and n_volte > 0 else reale["volte"]
        importo_gia_pagato = reale["importo"]
        importo_rimasto = importo_totale - importo_gia_pagato
        tag = "uscita" if tipo_voce == "Uscita" else "entrata"
        values = (cat, conto, metodo, tag_str, tipo_voce, f"{_fmt_it(imp)} €", n_volte, volte_passate, data_inizio_str, data_fine, f"{_fmt_it(importo_totale)} €", f"{_fmt_it(importo_gia_pagato)} €", f"{_fmt_it(importo_rimasto)} €", id_ricorrenza)
        tree.insert("", "end", iid=id_ricorrenza, values=values, tags=(tag,))
        if ric_periodo.lower() == "ogni mese":
            bilancio_mensile += imp if tipo_voce == "Entrata" else -imp
    tree.bind("<Double-1>", self.on_ricorrenza_double_click)
    summary_frame = ttk.Frame(main_frame, padding=(0, 10))
    summary_frame.pack(fill="x", expand=False)
    img_mouse = self.icone_gui.get("mouse")
    self.lbl_hint_ricorrenze = ttk.Label(
            summary_frame,
            text="Doppio clic su una riga per vedere il dettaglio dei pagamenti previsti",
            image=img_mouse,
            compound="right",
            foreground="gray",
            font=("Arial", 8, "italic")
    )
    if img_mouse:
            self.lbl_hint_ricorrenze.image = img_mouse
    self.lbl_hint_ricorrenze.pack(side="right", padx=5)
    bilancio_colore = "green" if bilancio_mensile >= 0 else "red"
    ttk.Label(summary_frame, text="Impatto Mensile Stimato (su base 'Mese'):", font=("Arial", 10)).pack(side="left")
    ttk.Label(summary_frame, text=f"{_fmt_it(bilancio_mensile)} €", font=("Arial", 11, "bold"), foreground=bilancio_colore).pack(side="left", padx=5)
    button_frame = ttk.Frame(main_frame, padding=(0, 10))
    button_frame.pack(fill="x", expand=False)
    self.btn_cancella_ric = ttk.Label(
        button_frame, 
        image=self.icone_gui.get("delete"),
        text=" Cancella Selezionate", 
        compound="left",
        cursor="hand2", 
        background=self.COLOR_WIDGET_BG,
        font=("Arial", 9, "bold")
    )
    self.btn_cancella_ric.image = self.icone_gui.get("delete")
    self.btn_cancella_ric.pack(side="left", padx=5)
    self.btn_cancella_ric.bind("<Button-1>", lambda e: _delete_selected_ricorrenze())
    self.btn_chiudi_ric = ttk.Label(
        button_frame, 
        image=self.icone_gui.get("chiudi"),
        text=" Chiudi", 
        compound="left",
        cursor="hand2", 
        background=self.COLOR_WIDGET_BG,
        font=("Arial", 9, "bold")
    )
    self.btn_chiudi_ric.image = self.icone_gui.get("chiudi")
    self.btn_chiudi_ric.pack(side="right", padx=5)
    self.btn_chiudi_ric.bind("<Button-1>", lambda e: lista_window.after(50, destroy_window_and_cleanup))

# Visualizzazione Dettagliata (Popup) delle Scadenze di una Ricorrenza
def on_ricorrenza_double_click(self, event):
    tree = event.widget
    parent_window = tree.winfo_toplevel()
    item_id = tree.focus()
    if not item_id or item_id not in self.ricorrenze:
        return
    if hasattr(self, '_popup_movimenti_ref') and self._popup_movimenti_ref and self._popup_movimenti_ref.winfo_exists():
        self._popup_movimenti_ref.lift()
        self._popup_movimenti_ref.focus_force()
        return
    ricorrenza_dati = self.ricorrenze.get(item_id, {})
    descrizione_ricorrenza = ricorrenza_dati.get("cat", "N/D")
    conto_ricorrenza = ricorrenza_dati.get("conto") or ""
    metodo_ricorrenza = ricorrenza_dati.get("metodo_pagamento") or ""
    importo_ricorrenza = ricorrenza_dati.get("imp", 0.0)
    tipo_std = ricorrenza_dati.get('tipo_voce', 'Uscita')
    n_volte = ricorrenza_dati.get("n", 0)
    tag_ricorrenza_str = " ".join(ricorrenza_dati.get("hashtag", []) or [])
    popup_movimenti = tk.Toplevel(parent_window)
    self._popup_movimenti_ref = popup_movimenti
    popup_movimenti.bind("<Destroy>", lambda e: setattr(self, '_popup_movimenti_ref', None) if e.widget is popup_movimenti else None)
    popup_movimenti.configure(bg=self.COLOR_WIDGET_BG)
    popup_movimenti.title(f"Movimenti di '{descrizione_ricorrenza}'")
    width, height = 1000, 550
    screen_width = popup_movimenti.winfo_screenwidth()
    screen_height = popup_movimenti.winfo_screenheight()
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    popup_movimenti.geometry(f"{width}x{height}+{x}+{y}")
    popup_movimenti.resizable(True, True)
    popup_movimenti.minsize(width, height)
    popup_movimenti.transient(parent_window)
    popup_movimenti.focus_set()
    tree_movimenti = ttk.Treeview(
        popup_movimenti,
        columns=("data", "categoria", "conto", "metodo", "tag", "importo", "saldato", "da_saldare"),
        show="headings"
    )
    tree_movimenti.pack(fill="both", expand=True, padx=10, pady=10)
    for col in ("data", "categoria", "conto", "metodo", "tag", "importo", "saldato", "da_saldare"):
        tree_movimenti.heading(
            col, 
            text="Tag" if col == "tag" else col.capitalize(), 
            command=lambda _col=col: self.treeview_sort_column(tree_movimenti, _col, False)
        )
        if col == "categoria":
                w = 250
        elif col == "conto":
                w = 120
        elif col == "metodo":
                w = 110
        elif col == "tag":
                w = 100
        else:
                w = 100
        tree_movimenti.column(col, width=w, anchor="center")
    tree_movimenti.tag_configure("verde", foreground="green")
    tree_movimenti.tag_configure("rosso", foreground="red")
    tree_movimenti.tag_configure("grigio", foreground="gray")
    oggi = datetime.date.today()
    date_list_str = ricorrenza_dati.get("date_list", [])
    for data_str in date_list_str:
        try:
            data_movimento = datetime.datetime.strptime(data_str, "%d-%m-%Y").date()
        except: continue
        voce_trovata = False
        importo_effettivo = importo_ricorrenza
        if data_movimento in self.spese:
            for voce in self.spese[data_movimento]:
                if str(campo(voce, "id_ricorrenza", None)) == str(item_id):
                    importo_effettivo = campo(voce, "importo", importo_ricorrenza)
                    voce_trovata = True
                    break
        if data_movimento <= oggi:
            if voce_trovata:
                icona_p, icona_dp = "✔️", ""
                tag = "verde" if tipo_std == "Entrata" else "rosso"
            else:
                icona_p, icona_dp = "", "❌"
                tag = "grigio"
        else:
            icona_p, icona_dp = "", "❌"
            tag = "verde" if tipo_std == "Entrata" else "rosso"

        tree_movimenti.insert("", "end", values=(
            data_str, descrizione_ricorrenza, conto_ricorrenza, metodo_ricorrenza, tag_ricorrenza_str, f"{_fmt_it(importo_effettivo)} €", icona_p, icona_dp
        ), tags=(tag,))
    info_frame = ttk.Frame(popup_movimenti, padding=(10, 5))
    info_frame.pack(fill="x", expand=False)
    
    info_text = (
            f"Dettagli ricorrenza: {descrizione_ricorrenza} - "
            f"Importo: {_fmt_it(importo_ricorrenza)} € - "
            f"Periodo: {ricorrenza_dati.get('tipo', 'N/D')} - "
            f"Durata: {n_volte} volte"
            + (f" - Metodo: {metodo_ricorrenza}" if metodo_ricorrenza else "")
            + (f" - Tag: {tag_ricorrenza_str}" if tag_ricorrenza_str else "")
    )
    ttk.Label(info_frame, text=info_text, font=("Arial", 10, "bold")).pack(side="left")
    self.btn_chiudi_mov = ttk.Label(
            info_frame, 
            text=" Chiudi",
            compound="left",
            image=self.icone_gui.get("chiudi"),
            cursor="hand2", 
            background=self.COLOR_WIDGET_BG
    )
    if self.icone_gui.get("chiudi"):
            self.btn_chiudi_mov.image = self.icone_gui.get("chiudi")
    self.btn_chiudi_mov.pack(side="right", padx=10)
    img_mouse = self.icone_gui.get("mouse")
    hint_label = ttk.Label(
            info_frame,
            text="Doppio clic → Vai alla spesa sulla Dashboard",
            image=img_mouse,
            compound="right",
            foreground="gray",
            font=("Arial", 8, "italic")
    )
    if img_mouse:
            hint_label.image = img_mouse
    hint_label.pack(side="right", padx=10)
    self.btn_chiudi_mov.bind("<Button-1>", lambda e: (
            self.reset_ricorrenza_popup(), 
            popup_movimenti.destroy()
    ))
    popup_movimenti.bind("<Escape>", lambda e: (
            self.reset_ricorrenza_popup(),
            popup_movimenti.destroy()
    ))
    tree_movimenti.bind("<Double-1>", lambda e: (
            self.on_scadenza_doppio_click(e),
            self.reset_ricorrenza_popup(),
            popup_movimenti.destroy(),
            self.lista_window_ref.destroy() if hasattr(self, 'lista_window_ref') and self.lista_window_ref.winfo_exists() else None,
            self.ricorrenza_popup.destroy() if hasattr(self, 'ricorrenza_popup') and self.ricorrenza_popup.winfo_exists() else None
    ))
