#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import tkinter as tk
from tkinter import ttk
from moduli.modello_spesa import campo

# Popup Movimenti Simili     
def mostra_spese_simili(self):
    import __main__ as _app
    TOLL = _app.TOLL
    if hasattr(self, "popup_simili") and self.popup_simili.winfo_exists():
        self.popup_simili.lift()
        self.popup_simili.focus_force()
        return
    valore = self.imp_entry.get().replace(",", ".").strip()
    try:
        target = float(valore)
    except ValueError:
        self.show_toast("Errore: Importo mancante o non valido.")
        return
    tolleranza = int(self.spin_tolleranza.get()) if hasattr(self, "spin_tolleranza") else TOLL
    limite_basso = target - tolleranza
    limite_alto = target + tolleranza
    
    voci_simili = [
        (d, voce)
        for d, lista in self.spese.items()
        for voce in lista
        if len(voce) >= 4 
        and isinstance(voce[2], (int, float)) 
        and limite_basso <= voce[2] <= limite_alto
        and voce[0] not in ["", "Categoria Rimossa", None]
        and voce[0] in self.categorie
    ]
    if not voci_simili:
        self.show_toast("Nessuna corrispondenza: Nessuna spesa trovata con questo importo.")
        return
    popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    popup.title(f"Movimenti simili a €{target:.2f}")
    popup.resizable(False, False)
    popup.bind("<Escape>", lambda e: popup.destroy())
    larghezza, altezza = 900, 460
    x = (popup.winfo_screenwidth() // 2) - (larghezza // 2)
    y = (popup.winfo_screenheight() // 2) - (altezza // 2)
    popup.geometry(f"{larghezza}x{altezza}+{x}+{y}")
    label_range = ttk.Label(
        popup,
        text=f"Movimenti compresi tra €{limite_basso:.2f} e €{limite_alto:.2f}",
        style="White.TLabel"
    )
    label_range.pack(pady=(10, 4))
    ttk.Label(
        popup,
        text="Margine di tolleranza (€):",
        style="WhiteSmall.TLabel"
    ).pack(pady=(4, 2))
    tolleranza_var = tk.StringVar(value=str(tolleranza))
    def aggiorna_auto(*args):
        try:
            nuovo_tolleranza = int(tolleranza_var.get())
        except ValueError:
            return
        limite_basso = target - nuovo_tolleranza
        limite_alto = target + nuovo_tolleranza
        label_range.config(text=f"Movimenti compresi tra €{limite_basso:.2f} e €{limite_alto:.2f}")
        nuove_voci = [
            (d, voce)
            for d, lista in self.spese.items()
            for voce in lista
            if len(voce) >= 4 and isinstance(voce[2], (int, float)) and limite_basso <= voce[2] <= limite_alto
        ]
        for item in tree.get_children():
            tree.delete(item)
        nuove_voci.sort(key=lambda x: x[0], reverse=True)
        for d, voce in nuove_voci:
            try:
                categoria, descrizione, importo, tipo = voce[0], voce[1], voce[2], voce[3]
                conto_v = campo(voce, "conto", "")
                metodo_v = campo(voce, "metodo_pagamento", "")
                tag_v = " ".join(campo(voce, "hashtag", []))
                tag = "entrata" if str(tipo).lower() == "entrata" else "uscita"
                tree.insert("", tk.END, values=(
                    d.strftime("%d-%m-%Y"),
                    tipo,
                    categoria,
                    descrizione,
                    f"€{importo:.2f}",
                    conto_v,
                    metodo_v,
                    tag_v
                ), tags=(tag,))
            except Exception:
                continue
    spin_tolleranza_popup = ttk.Spinbox(
        popup,
        from_=0,
        to=100,
        increment=1,
        width=6,
        font=("Arial", 10),
        justify="center",
        style="Custom.TSpinbox",
        textvariable=tolleranza_var
    )
    spin_tolleranza_popup.pack(pady=(0, 10))
    tolleranza_var.trace_add("write", aggiorna_auto)
    columns = ("data", "tipo", "categoria", "descrizione", "importo", "conto", "metodo", "tag")
    headers = {
        "data": "Data",
        "tipo": "Tipo",
        "categoria": "Categoria",
        "descrizione": "Descrizione",
        "importo": "Importo",
        "conto": "Conto",
        "metodo": "Metodo",
        "tag": "Tag"
    }
    tree_frame = ttk.Frame(popup)
    tree_frame.pack(padx=12, pady=(0, 6), fill="both", expand=True)
    vsb = ttk.Scrollbar(tree_frame, orient="vertical", style="Vertical.TScrollbar")
    vsb.pack(side="right", fill="y")
    tree = ttk.Treeview(
        tree_frame, 
        columns=columns, 
        show="headings", 
        height=10,
        yscrollcommand=vsb.set,
    )
    tree.pack(fill="both", expand=True)
    tree.bind("<Double-1>", lambda e: usa_categoria())
    vsb.config(command=tree.yview)
    for col in columns:
        tree.heading(col, text=headers[col], command=lambda c=col: self.treeview_sort_column(tree, c, False))
    tree.column("data", width=90, anchor="center")
    tree.column("tipo", width=70, anchor="center")
    tree.column("categoria", width=110, anchor="w")
    tree.column("descrizione", width=170, anchor="w")
    tree.column("importo", width=75, anchor="e")
    tree.column("conto", width=90, anchor="center")
    tree.column("metodo", width=90, anchor="center")
    tree.column("tag", width=90, anchor="center")
    voci_simili.sort(key=lambda x: x[0], reverse=True)
    for d, voce in voci_simili:
        try:
            categoria, descrizione, importo, tipo = voce[0], voce[1], voce[2], voce[3]
            conto_v = campo(voce, "conto", "")
            metodo_v = campo(voce, "metodo_pagamento", "")
            tag_v = " ".join(campo(voce, "hashtag", []))
            tag = "entrata" if str(tipo).lower() == "entrata" else "uscita"
            tree.insert("", tk.END, values=(
                d.strftime("%d-%m-%Y"),
                tipo,
                categoria,
                descrizione,
                f"€{importo:.2f}",
                conto_v,
                metodo_v,
                tag_v
            ), tags=(tag,))
        except Exception as e:
            print(f"[Voce malformata]: {voce} → {e}")
            continue
    tree.tag_configure("entrata", foreground="green")
    tree.tag_configure("uscita", foreground="red")
    def usa_categoria():
        selezione = tree.selection()
        if not selezione:
            self.show_toast("Seleziona una spesa per copiarne la categoria.")
            return
        valori = tree.item(selezione[0], "values")
        self.cat_sel.set(valori[2])
        self.on_categoria_changed(manuale=True)
        popup.destroy()
    btn_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    btn_frame.pack(pady=(4, 12))
    img_usa = self.icone_gui.get("aggiungi")
    btn_usa = tk.Label(
            btn_frame,
            compound="left",
            image=img_usa,
            text=" Usa questa categoria" if img_usa else "Usa questa categoria",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2",
            padx=15,
            pady=6,
            font=("Arial", 9, "bold")
    )
    btn_usa.pack(side="left", padx=8)
    btn_usa.bind("<Button-1>", lambda e: usa_categoria())
    img_chiudi = self.icone_gui.get("chiudi")
    btn_chiudi_pop = tk.Label(
            btn_frame,
            compound="left",
            image=img_chiudi,
            text=" Chiudi" if img_chiudi else "Chiudi",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2",
            padx=15,
            pady=6,
            font=("Arial", 9, "bold")
    )
    btn_chiudi_pop.pack(side="left", padx=8)
    btn_chiudi_pop.bind("<Button-1>", lambda e: popup.destroy())
    def sort_column(tv, col, reverse):
        def extract(val):
            try:
                if col == "importo":
                    return float(val.replace("€", "").replace(",", "").strip())
                elif col == "data":
                    return datetime.datetime.strptime(val, "%d-%m-%Y")
                return str(val).lower()
            except:
                return val
        idx = columns.index(col)
        dati = [(tv.item(k)["values"], k) for k in tv.get_children()]
        try:
            dati.sort(key=lambda x: extract(x[0][idx]), reverse=reverse)
        except Exception as e:
            print(f"[Errore ordinamento '{col}']: {e}")
            return
        for i, (valori, k) in enumerate(dati):
            tv.move(k, "", i)
        tv.heading(col, command=lambda: sort_column(tv, col, not reverse))

