#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import random
import calendar
import tkinter as tk
from tkinter import ttk, filedialog
import datetime

import __main__ as _app
from moduli.modello_spesa import SpesaEntry, campo

def mostra_categorie_popup(self):
    import datetime
    if hasattr(self, 'categorie_popup') and self.categorie_popup.winfo_exists():
        self.categorie_popup.deiconify()
        self.categorie_popup.lift()
        self.categorie_popup.focus_force()
        self.cat_mod_menu.configure(style="Border.TCombobox")
        self.reset_campi_categoria()
        self.categorie_popup.after(100, self.entry_nuova_cat.focus_set) 
        return
    self.categorie_popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    self.categorie_popup.transient(self)
    self.categorie_popup.title("Gestione Categorie")
    self.categorie_popup.resizable(False, False)
    window_width = 650
    window_height = 200
    screen_width = self.winfo_screenwidth()
    screen_height = self.winfo_screenheight()
    center_x = int(screen_width / 2 - window_width / 2)
    center_y = int(screen_height / 2 - window_height / 2)
    self.categorie_popup.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    self.categorie_popup.bind("<Escape>", lambda event: self.categorie_popup.withdraw())
    main_frame = ttk.Frame(self.categorie_popup)
    main_frame.pack(padx=10, pady=10, fill="both", expand=True)
    aggiungi_cat_frame = ttk.LabelFrame(main_frame, text="✓ Configurazione Categorie", style="RedBold.TLabelframe")
    aggiungi_cat_frame.pack(padx=5, pady=5, fill="both", expand=True)
    aggiungi_cat_frame.columnconfigure(1, weight=1)
    if not hasattr(self, 'nuova_cat'):
        self.nuova_cat = tk.StringVar()
        self.cat_mod_sel = tk.StringVar(value=self.categorie[0] if self.categorie else "")
        self.tipo_categoria = tk.StringVar(value="Uscita")
    def convalida_categoria(valore):
        return len(valore) <= 20
    vcmd_cat = aggiungi_cat_frame.register(convalida_categoria)
    self.lbl_nome_cat = ttk.Label(
        aggiungi_cat_frame, 
        image=self.icone_gui.get("search"),
        text=" Nome:", 
        compound="left",
        background=self.COLOR_WIDGET_BG,
        font=("Arial", 9, "bold")
    )
    self.lbl_nome_cat.image = self.icone_gui.get("search")
    self.lbl_nome_cat.grid(row=0, column=0, sticky="e", padx=4, pady=2)
    self.entry_nuova_cat = ttk.Entry(
        aggiungi_cat_frame,
        textvariable=self.nuova_cat,
        width=22,
        validate="key",
        validatecommand=(vcmd_cat, "%P")
    )
    self.entry_nuova_cat.grid(row=0, column=1, sticky="w", padx=2, pady=2)
    self.entry_nuova_cat.bind("<Return>", lambda e: self.add_categoria())
    self.entry_nuova_cat.bind("<KP_Enter>", lambda e: self.add_categoria())
    self.lbl_tipo_cat = ttk.Label(
        aggiungi_cat_frame, 
        image=self.icone_gui.get("documenti"),
        text=" Tipo:", 
        compound="left",
        background=self.COLOR_WIDGET_BG,
        font=("Arial", 9, "bold")
    )
    self.lbl_tipo_cat.image = self.icone_gui.get("documenti")
    self.lbl_tipo_cat.grid(row=0, column=2, sticky="e", padx=4, pady=2)
    def toggle_tipo_spesa_popup_cat():
        tipo_corrente = self.tipo_categoria.get()
        nuovo_tipo = "Entrata" if tipo_corrente == "Uscita" else "Uscita"
        self.tipo_categoria.set(nuovo_tipo)
        self._aggiorna_stile_pulsante_tipo_popup()
    self.btn_gestisci_tipo = ttk.Button(
        aggiungi_cat_frame,
        text=self.tipo_categoria.get(),
        width=10,
        command=toggle_tipo_spesa_popup_cat,
        style='RedOutline.TButton',
        takefocus=0
    )
    self.btn_gestisci_tipo.grid(row=0, column=3, sticky="w", padx=2, pady=2)
    self.btn_gestisci_tipo.config(cursor="hand2")
    self._aggiorna_stile_pulsante_tipo_popup()
    ttk.Label(aggiungi_cat_frame,
     image=self.icone_gui.get("filtri"),
     text=" Modifica:",
     compound="left").grid(row=1, column=0, sticky="e", padx=4, pady=2)
    self.cat_mod_menu = ttk.Combobox(
        aggiungi_cat_frame,
        textvariable=self.cat_mod_sel,
        values=sorted(self.categorie),
        style="Border.TCombobox",
        state="readonly",
        width=22
    )
    self.cat_mod_menu.grid(row=1, column=1, sticky="w", padx=2, pady=2)
    self.cat_mod_menu.bind("<<ComboboxSelected>>", lambda e: (
            self.on_categoria_modifica_changed_popup(),
            self.cat_mod_menu.selection_clear(),
            aggiungi_cat_frame.focus_set()
    ))
    ttk.Label(aggiungi_cat_frame,
              text=" Budget €/mese:",
              font=("Arial", 9, "bold")).grid(row=1, column=2, sticky="e", padx=4, pady=2)
    def convalida_budget(valore):
        if valore == "" or valore == ".":
            return True
        try:
            float(valore.replace(",", "."))
            return len(valore) <= 8
        except ValueError:
            return False
    vcmd_budget = aggiungi_cat_frame.register(convalida_budget)
    def _formatta_budget(self):
        val = self.var_budget_cat.get().strip().replace(",", ".")
        try:
            self.var_budget_cat.set(f"{float(val):.2f}")
        except ValueError:
            pass
    self.entry_budget_cat = ttk.Entry(
        aggiungi_cat_frame,
        textvariable=self.var_budget_cat,
        width=10,
        validate="key",
        validatecommand=(vcmd_budget, "%P")
    )
    self.entry_budget_cat.bind("<FocusOut>", lambda e: [
        self.var_budget_cat.set(f"{float(self.var_budget_cat.get().strip().replace(',', '.')):.2f}")
        if self.var_budget_cat.get().strip() else None
    ])
    self.entry_budget_cat.grid(row=1, column=3, sticky="w", padx=2, pady=2)
    btn_frame_cat = ttk.Frame(aggiungi_cat_frame)
    btn_frame_cat.grid(row=2, column=0, columnspan=2, pady=10)
    self.btn_add_cat = ttk.Label(
        btn_frame_cat, image=self.icone_gui.get("check"),
        text=" Aggiungi", compound="left", cursor="hand2", background=self.COLOR_WIDGET_BG, font=("Arial", 9, "bold")
    )
    self.btn_add_cat.image = self.icone_gui.get("check")
    self.btn_add_cat.pack(side="left", padx=2)
    self.btn_add_cat.bind("<Button-1>", lambda e: self.add_categoria())
    self.btn_modifica_cat = ttk.Label(
        btn_frame_cat, image=self.icone_gui.get("descrizione"),
        text=" Modifica", compound="left", cursor="hand2", background=self.COLOR_WIDGET_BG, font=("Arial", 9, "bold")
    )
    self.btn_modifica_cat.image = self.icone_gui.get("descrizione")
    self.btn_modifica_cat.pack(side="left", padx=2)
    self.btn_modifica_cat.bind("<Button-1>", lambda e: self.modifica_categoria())
    self.btn_cancella_cat = ttk.Label(
        btn_frame_cat, image=self.icone_gui.get("delete"),
        text=" Cancella", compound="left", cursor="hand2", background=self.COLOR_WIDGET_BG, font=("Arial", 9, "bold")
    )
    self.btn_cancella_cat.image = self.icone_gui.get("delete")
    self.btn_cancella_cat.pack(side="left", padx=2)
    self.btn_cancella_cat.bind("<Button-1>", lambda e: self.cancella_categoria())
    self.btn_suggerite = ttk.Label(
        btn_frame_cat, image=self.icone_gui.get("help"), 
        cursor="hand2", background=self.COLOR_WIDGET_BG
    )
    self.btn_suggerite.image = self.icone_gui.get("help")
    self.btn_suggerite.pack(side="left", padx=2)
    self.btn_suggerite.bind("<Button-1>", lambda e: self.apri_categorie_suggerite())
    self.btn_multi_del = ttk.Label(
        btn_frame_cat, image=self.icone_gui.get("documenti"),
        cursor="hand2", background=self.COLOR_WIDGET_BG
    )
    self.btn_multi_del.image = self.icone_gui.get("documenti")
    self.btn_multi_del.pack(side="left", padx=2)
    self.btn_multi_del.bind("<Button-1>", lambda e: self.apri_cancella_multiplo())
    self.btn_elenco_cat = ttk.Label(
        btn_frame_cat, image=self.icone_gui.get("report"),
        text=" Elenco", compound="left", cursor="hand2", background=self.COLOR_WIDGET_BG, font=("Arial", 9, "bold")
    )
    self.btn_elenco_cat.image = self.icone_gui.get("report")
    self.btn_elenco_cat.pack(side="left", padx=2)
    self.btn_elenco_cat.bind("<Button-1>", lambda e: self.mostra_tutte_le_categorie())
    self.btn_reset_cat = ttk.Label(
        btn_frame_cat, image=self.icone_gui.get("reset"),
        cursor="hand2", background=self.COLOR_WIDGET_BG
    )
    self.btn_reset_cat.image = self.icone_gui.get("reset")
    self.btn_reset_cat.pack(side="left", padx=2)
    self.btn_reset_cat.bind("<Button-1>", lambda e: self.reset_campi_categoria())
    self.btn_chiudi_popup_cat = ttk.Label(
        main_frame, image=self.icone_gui.get("chiudi"),
        text=" Chiudi", compound="left", cursor="hand2", background=self.COLOR_WIDGET_BG, font=("Arial", 9, "bold")
    )
    self.btn_chiudi_popup_cat.image = self.icone_gui.get("chiudi")
    self.btn_chiudi_popup_cat.pack(side="bottom", pady=(0, 10))
    self.btn_chiudi_popup_cat.bind("<Button-1>", lambda e: self.categorie_popup.withdraw())
    self.aggiorna_combobox_categorie()
    self.reset_campi_categoria()
    if not self.categorie:
        self.cat_mod_menu['state'] = 'disabled'

def _aggiorna_stile_pulsante_tipo_popup(self):
    tipo = self.tipo_categoria.get()
    btn_style = 'GreenOutline.TButton' if tipo == "Entrata" else 'RedOutline.TButton'
    self.btn_gestisci_tipo.config(
        text=tipo,
        style=btn_style
    )

def on_categoria_modifica_changed_popup(self):
    nome = self.cat_mod_sel.get()
    tipo = self.categorie_tipi.get(nome, "Uscita")
    self.nuova_cat.set(nome)
    self.tipo_categoria.set(tipo)
    self._aggiorna_stile_pulsante_tipo_popup()
    budget = self.budget_categorie.get(self.cat_mod_sel.get(), 0)
    self.var_budget_cat.set(f"{budget:.2f}" if budget > 0 else "")

def on_categoria_modifica_changed(self):
    nome = self.cat_mod_sel.get()
    tipo = self.categorie_tipi.get(nome, "Uscita")
    self.nuova_cat.set(nome)  
    self.tipo_categoria.set(tipo)

def reset_campi_categoria(self):
    self.nuova_cat.set("")                          
    self.cat_mod_sel.set("")                        
    self.tipo_categoria.set("Uscita")    
    self._aggiorna_stile_pulsante_tipo_popup()
    self.var_budget_cat.set("")
    if hasattr(self, 'entry_nuova_cat') and self.entry_nuova_cat.winfo_exists():
        self.entry_nuova_cat.focus_set()           

def aggiorna_categoria_automatica(self, event=None):
    if event is not None and getattr(event, "keysym", "") == "Tab":
        return
    if self.categoria_bloccata:
        if getattr(event, "keysym", "") in ("BackSpace", "Delete") and not self.imp_entry.get():
            self.categoria_bloccata = False
        else:
            return
    if hasattr(self, "cat_filter_entry"):
        self.cat_filter_entry.delete(0, "end")
        self.cat_filter_entry.config(foreground=self.TEXT_COLOR)
        self.cat_menu.config(values=sorted(self.categorie, key=lambda c: c.lower()))
    if not self.suggerimenti_attivi:
        self.label_smartcat.config(text="💡 SmartCat Off", foreground="green")
        self.aggiorna_bottone_spese_simili(visibile=False)
        return
    valore = self.imp_entry.get().replace(",", ".").strip()
    if not valore:
        self.aggiorna_bottone_spese_simili(visibile=False)
        if not self.categoria_bloccata:
            self.cat_sel.set("Generica")
        self.categoria_bloccata = False
        self.label_smartcat.config(text="💡 SmartCat Idle...", foreground="gray")
        self.tipo_spesa_var.set("Uscita")
        self.aggiorna_stile_tipo_spesa()
        self.lbl_tipo_percentuale.config(text="0% Entrate / 0% Uscite ")
        return
    try:
        imp_corrente = float(valore)
    except ValueError:
        return
    oggi = datetime.date.today()
    un_anno_fa = oggi - datetime.timedelta(days=365)
    mappa_ricorrenti = {}
    for d, lista in self.spese.items():
        if d < un_anno_fa:
            continue
        for voce in lista:
            try:
                cat = campo(voce, "categoria", "")
                imp = campo(voce, "importo", 0.0)
                if cat in ["", "Categoria Rimossa", None] or cat not in self.categorie:
                    continue
                chiave = (cat, round(float(imp), 2))
                mappa_ricorrenti[chiave] = mappa_ricorrenti.get(chiave, 0) + 1
            except:
                continue
    if not mappa_ricorrenti:
        return
    miglior_punteggio = float("inf")
    categoria_migliore = None
    for (categoria, importo_storico), freq in mappa_ricorrenti.items():
        diff = abs(importo_storico - imp_corrente)
        if diff < 0.01:
            punteggio = -2000 - freq
        elif diff <= 0.05:
            punteggio = -1000 - freq + (diff * 10)
        elif diff <= (imp_corrente * 0.02):
            punteggio = diff - (freq * 2)
        elif diff <= _app.TOLL:
            punteggio = diff - freq
        else:
            continue
        if punteggio < miglior_punteggio:
            miglior_punteggio = punteggio
            categoria_migliore = categoria
    if categoria_migliore and not self.categoria_bloccata:
        self.cat_sel.set(categoria_migliore)
        self.on_categoria_changed(manuale=False)
        self.label_smartcat.config(text="💡 SmartCat On", foreground="red")
        self.aggiorna_bottone_spese_simili(visibile=True)
        self.cat_menu.configure(style="Highlight.TCombobox")
        self.cat_menu.after(500, lambda: self.cat_menu.configure(style="Border.TCombobox"))
    else:
        self.aggiorna_bottone_spese_simili(visibile=False)
        self.label_smartcat.config(text="💡 SmartCat Idle...", foreground="gray")  

def aggiorna_combobox_categorie(self):
    altre = sorted([c for c in self.categorie if c != "Generica"], key=str.lower)
    ordinata = ["Generica"] + altre if "Generica" in self.categorie else altre
    self.categorie = ordinata
    if hasattr(self, 'cat_menu') and self.cat_menu.winfo_exists():
        self.cat_menu["values"] = self.categorie
        try:
            if "Generica" in self.categorie:
                self.cat_menu.current(self.categorie.index("Generica"))
            elif self.categorie:
                self.cat_menu.current(0)
        except: pass
    if hasattr(self, 'cat_mod_menu') and self.cat_mod_menu.winfo_exists():
        self.cat_mod_menu["values"] = self.categorie
        try:
            if "Generica" in self.categorie:
                idx = self.categorie.index("Generica")
                self.cat_mod_menu.current(idx)
            elif self.categorie:
                self.cat_mod_menu.current(0)
        except: pass

# Sincronizzazione Tipo Voce (Entrata/Uscita) e Aggiornamento Stile UI
def on_categoria_changed(self, event=None, manuale=True):
    if manuale:
        self.categoria_bloccata = True
    cat = self.cat_sel.get()
    tipo_cat = self.categorie_tipi.get(cat, "Uscita")
    self.tipo_spesa_var.set(tipo_cat)
    self.btn_tipo_spesa.config(text=tipo_cat)
    new_style = 'GreenOutline.TButton' if tipo_cat == "Entrata" else 'RedOutline.TButton'
    self.btn_tipo_spesa.config(style=new_style)
    tipo_cat_suggerito, perc_entrate, perc_uscite = self.suggerisci_tipo_categoria(cat)
    colore_percentuale = "gray"
    if perc_entrate > perc_uscite:
        colore_percentuale = "forestgreen"
    elif perc_uscite > perc_entrate:
        colore_percentuale = "firebrick"
    self.lbl_tipo_percentuale.config(
        text=f"{perc_entrate}% Entrate / {perc_uscite}% Uscite",
        foreground=colore_percentuale
    )
    self.label_smartcat.config(text="💡 SmartCat Off", foreground="green")
    self.aggiorna_bottone_spese_simili(visibile=False)

# Popup Mostra Categorie Attive
def mostra_tutte_le_categorie(self):
    popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    popup.title("📋 Elenco Categorie")
    popup.resizable(False, False)
    popup_width = 320
    popup_height = 420
    screen_width = self.winfo_screenwidth()
    screen_height = self.winfo_screenheight()
    center_x = int((screen_width / 2) - (popup_width / 2))
    center_y = int((screen_height / 2) - (popup_height / 2))
    popup.geometry(f"{popup_width}x{popup_height}+{center_x}+{center_y}")
    popup.resizable(True, True)
    popup.minsize(popup_width, popup_height)
    popup.transient(self)
    popup.lift()
    popup.focus_force()
    popup.bind("<Escape>", lambda e: popup.destroy())
    frame = ttk.Frame(popup, padding=10)
    frame.pack(fill="both", expand=True)
    label = ttk.Label(frame, text="Categorie disponibili:", font=("Arial", 11, "bold"))
    label.pack(pady=(0, 10))
    text_frame = ttk.Frame(frame)
    text_frame.pack(fill="both", expand=True)
    vsb = ttk.Scrollbar(text_frame, orient="vertical", style="Vertical.TScrollbar")
    vsb.pack(side="right", fill="y")
    text = tk.Text( 
        text_frame, 
        font=("Arial", 10), 
        height=18, 
        wrap="none", 
        state="normal",
        bg=self.COLOR_TOPLEVEL,
        fg=self.TEXT_COLOR,
        insertbackground=self.TEXT_COLOR,
        highlightthickness=0,
        yscrollcommand=vsb.set
    )
    text.pack(side="left", fill="both", expand=True)
    vsb.config(command=text.yview)
    text.tag_configure("entrata", foreground="green")
    text.tag_configure("uscita", foreground="red")
    for nome in sorted(self.categorie, key=lambda x: x.lower()):
        tipo = self.categorie_tipi.get(nome, "Uscita")
        riga = f"• {nome}  ("
        text.insert("end", riga)
        if tipo == "Entrata":
            text.insert("end", tipo, "entrata")
        else:
            text.insert("end", tipo, "uscita")
        text.insert("end", ")\n")
    text.config(state="disabled") 
    btn_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    btn_frame.pack(pady=10)
    img_chiudi_pop = self.icone_gui.get("chiudi")
    btn_chiudi_pop = tk.Label(btn_frame, compound="left", image=img_chiudi_pop, text=" Chiudi" if img_chiudi_pop else "❌ Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padx=15, pady=8, font=("Arial", 9, "bold"))
    btn_chiudi_pop.pack(pady=10)
    btn_chiudi_pop.bind("<Button-1>", lambda e: popup.destroy())

# Gestione Completa delle Categorie (Aggiunta, Modifica, Eliminazione e Controllo Spese)
def add_categoria(self):
    nome = self.nuova_cat.get().strip()
    tipo = self.tipo_categoria.get()
    if not nome or nome in self.categorie or nome == self.CATEGORIA_RIMOSSA:
        self.reset_campi_categoria()
        self.show_toast("Attenzione: Nome categoria vuoto, già esistente o riservato.")
        return
    self.categorie.append(nome)
    self.categorie_tipi[nome] = tipo
    self.aggiorna_combobox_categorie()
    budget_val = self.var_budget_cat.get().strip().replace(",", ".")
    try:
        budget_val = float(budget_val)
    except ValueError:
        budget_val = 0.0
    if budget_val > 0:
        self.budget_categorie[nome] = budget_val
    elif nome in self.budget_categorie:
        del self.budget_categorie[nome]
    self.save_db()
    self.refresh_gui()
    self.reset_campi_categoria()  
    if hasattr(self, 'ricorrenza_popup') and self.ricorrenza_popup.winfo_exists():
        if hasattr(self, 'ric_cat_menu'):
            self.ric_cat_menu['values'] = sorted(self.categorie)
    self.show_toast(f"Categoria '{nome}' ({tipo}) aggiunta. Budget: €{budget_val:.2f}" if budget_val > 0 else f"Categoria '{nome}' ({tipo}) aggiunta.")

def modifica_categoria(self):
    old_nome = self.cat_mod_sel.get()
    if not old_nome:
        self.show_toast("Seleziona una categoria da modificare.")
        return
    if old_nome == "Generica":
     self.show_toast("La categoria 'Generica' non può essere rinominata.")
     self.reset_campi_categoria()  
     return
    new_nome = self.nuova_cat.get().strip()
    if not new_nome:
        self.show_toast("Inserisci il nuovo nome della categoria.")
        return
    if new_nome == old_nome:
        tipo = self.tipo_categoria.get()
        self.categorie_tipi[new_nome] = tipo
        budget_val = self.var_budget_cat.get().strip().replace(",", ".")
        try:
            budget_val = float(budget_val)
        except ValueError:
            budget_val = 0.0
        if budget_val > 0:
            self.budget_categorie[new_nome] = budget_val
        elif new_nome in self.budget_categorie:
            del self.budget_categorie[new_nome]
        self.save_db()
        self.refresh_gui()
        self.show_toast(f"Tipo '{new_nome}' aggiornato a '{tipo}'. Budget: €{budget_val:.2f}" if budget_val > 0 else f"Tipo '{new_nome}' aggiornato a '{tipo}'.")
        self.reset_campi_categoria()
        return
    if new_nome in self.categorie:
        self.show_toast("Esiste già una categoria con questo nome.")
        return
    idx = self.categorie.index(old_nome)
    self.categorie[idx] = new_nome
    nuovo_tipo = self.tipo_categoria.get()
    self.categorie_tipi[new_nome] = nuovo_tipo
    if new_nome != old_nome:
        self.categorie_tipi.pop(old_nome, None)
    for d in self.spese:
        new_entries = []
        for entry in self.spese[d]:
            if campo(entry, "categoria", "") == old_nome:
                entry = entry.sostituisci(categoria=new_nome)
            new_entries.append(entry)
        self.spese[d] = new_entries
    self.cat_menu["values"] = self.categorie
    self.cat_mod_menu["values"] = self.categorie
    budget_val = self.var_budget_cat.get().strip().replace(",", ".")
    try:
        budget_val = float(budget_val)
    except ValueError:
        budget_val = 0.0
    if budget_val > 0:
        self.budget_categorie[new_nome] = budget_val
    elif new_nome in self.budget_categorie:
        del self.budget_categorie[new_nome]
    if old_nome in self.budget_categorie:
        del self.budget_categorie[old_nome]
    self.save_db()
    self.refresh_gui()
    self.show_toast(f"Categoria '{old_nome}' rinominata in '{new_nome}' ({nuovo_tipo}). Budget: €{budget_val:.2f}" if budget_val > 0 else f"Categoria '{old_nome}' rinominata in '{new_nome}' ({nuovo_tipo}).")
    self.aggiorna_combobox_categorie()
    self.reset_campi_categoria() 
    if hasattr(self, 'ricorrenza_popup') and self.ricorrenza_popup.winfo_exists():
        if hasattr(self, 'ric_cat_menu'):
            self.ric_cat_menu['values'] = sorted(self.categorie)

def conferma_cancella_categoria(self, cat):
    popup = tk.Toplevel(self)
    popup.title("Conferma eliminazione")
    popup.resizable(False, False)
    width, height = 350, 180 
    popup.withdraw()
    popup.update_idletasks()
    parent_x = self.winfo_rootx()
    parent_y = self.winfo_rooty()
    parent_w = self.winfo_width()
    parent_h = self.winfo_height()
    x = parent_x + (parent_w // 2) - (width // 2)
    y = parent_y + (parent_h // 2) - (height // 2)
    popup.geometry(f"{width}x{height}+{x}+{y}")
    popup.configure(bg="#FFFACD")
    messaggio_var = tk.StringVar()
    messaggio_var.set(
        f"Eliminare la categoria '{cat}'?\nI Movimenti saranno Mantenuti ma etichettati\n'{self.CATEGORIA_RIMOSSA}'."
    )
    label = tk.Label(
        popup,
        textvariable=messaggio_var,
        font=("Arial", 10),
        justify="center",
        wraplength=320,
        bg="#FFFACD",
        fg="black"
    )
    label.pack(pady=8, padx=10)
    elimina_importi_var = tk.BooleanVar()
    def aggiorna_messaggio(*_):
        if elimina_importi_var.get():
            messaggio_var.set(
                f"Eliminare la categoria '{cat}'?\nI Movimenti e gli importi saranno eliminati."
            )
        else:
            messaggio_var.set(
                f"Eliminare la categoria '{cat}'?\nI Movimenti saranno etichettati '{self.CATEGORIA_RIMOSSA}'."
            )
    elimina_importi_var.trace_add("write", aggiorna_messaggio)
    tk.Checkbutton(
        popup,
        text="Elimina TUTTO anche gli importi associati",
        variable=elimina_importi_var,
        bg="#FFFACD",
        fg="black",
        selectcolor="#FFFACD",
        activebackground="#FFFACD",
        highlightthickness=0,
        relief="flat",
        borderwidth=0
    ).pack(pady=(0, 6), padx=20, anchor="w")
    btns_frame = tk.Frame(popup, bg="#FFFACD")
    btns_frame.pack(pady=10, fill="x", padx=20)
    btns_frame.columnconfigure(0, weight=1)
    btns_frame.columnconfigure(1, weight=1)
    result = {"ok": False, "elimina_importi": False}
    def do_ok():
        result["ok"] = True
        result["elimina_importi"] = elimina_importi_var.get()
        popup.destroy()
    def do_cancel():
        popup.destroy()
    b1 = ttk.Label(
        btns_frame, 
        image=self.icone_gui.get("delete"), 
        text=" Elimina", 
        compound="left", 
        cursor="hand2", 
        background="#FFFACD",
        foreground="black",
        font=("Arial", 10, "bold"),
        anchor="center"
    )
    b1.image = self.icone_gui.get("delete")
    b1.grid(row=0, column=0, padx=5, sticky="nsew")
    b1.bind("<Button-1>", lambda e: do_ok())
    b2 = ttk.Label(
        btns_frame, 
        image=self.icone_gui.get("chiudi"), 
        text=" Annulla", 
        compound="left", 
        cursor="hand2", 
        background="#FFFACD",
        foreground="black",
        font=("Arial", 10, "bold"),
        anchor="center"
    )
    b2.image = self.icone_gui.get("chiudi")
    b2.grid(row=0, column=1, padx=5, sticky="nsew")
    b2.bind("<Button-1>", lambda e: do_cancel())
    popup.bind("<Return>", lambda e: do_ok())
    popup.bind("<Escape>", lambda e: do_cancel())
    popup.deiconify()
    popup.wait_visibility()
    popup.grab_set()
    popup.wait_window()
    return result

def cancella_categoria(self):
    cat = self.cat_mod_sel.get()
    if not cat:
        self.show_toast("Attenzione: Seleziona una categoria da modificare.")
        return
    if cat in ("Generica", self.CATEGORIA_RIMOSSA):
        self.show_custom_warning("Attenzione", f"Non puoi cancellare la categoria '{cat}'.")
        self.reset_campi_categoria()
        return
    conferma = self.conferma_cancella_categoria(cat)
    if not conferma["ok"]:
        return
    elimina_importi = conferma["elimina_importi"]
    if cat in self.categorie:
        self.categorie.remove(cat)
    if cat in self.categorie_tipi:
        del self.categorie_tipi[cat]
    if cat in self.budget_categorie:
        del self.budget_categorie[cat]
    for giorno in list(self.spese):
        nuove_spese = []
        for voce in self.spese[giorno]:
            voce_cat = campo(voce, "categoria", "")
            if voce_cat == cat:
                if not elimina_importi:
                    nuove_spese.append(
                        voce.sostituisci(categoria=self.CATEGORIA_RIMOSSA)
                    )
            else:
                nuove_spese.append(voce)
        if nuove_spese:
            self.spese[giorno] = nuove_spese
        else:
            del self.spese[giorno]
    self.save_db()
    self.refresh_gui()
    self.on_categoria_changed()
    self.aggiorna_combobox_categorie()
    self.reset_campi_categoria()
    self.show_toast(f"Categoria '{cat}' cancellata.")
    if hasattr(self, 'ricorrenza_popup') and self.ricorrenza_popup.winfo_exists():
        if hasattr(self, 'ric_cat_menu'):
            self.ric_cat_menu['values'] = sorted(self.categorie)

def draw_top_categorie(self):
    if not hasattr(self, 'canvas_top_cat') or not self.canvas_top_cat.winfo_exists():
        return
    c = self.canvas_top_cat
    c.delete("all")
    w = c.winfo_width()
    h = c.winfo_height()
    if w < 10 or h < 10:
        return

    now = datetime.date.today()
    view_year  = getattr(self, '_view_year',  now.year)
    view_month = getattr(self, '_view_month', now.month)
    totali = {}
    dettagli = {}
    for d, entries in self.spese.items():
        if not self.considera_ricorrenze_var.get() and d > now:
            continue
        if d.year == view_year and d.month == view_month:
            for entry in entries:
                cat = campo(entry, "categoria", "")
                imp = campo(entry, "importo", 0.0)
                tipo = campo(entry, "tipo", "")
                segno = 1 if tipo == "Entrata" else -1
                totali[cat] = totali.get(cat, 0) + imp * segno
                dettagli.setdefault(cat, []).append((d, imp, tipo))

    if not totali:
        c.create_text(w // 2, h // 2, text="Nessuna uscita questo mese",
                      fill=self.TEXT_COLOR, font=("Arial", 10))
        c.configure(scrollregion=(0, 0, w, h))
        return

    # top10 = sorted(totali.items(), key=lambda x: x[1], reverse=True)[:10]
    top10 = sorted(totali.items(), key=lambda x: abs(x[1]), reverse=True)
    max_val = max(abs(v) for _, v in top10) or 1

    pad_l, pad_r, pad_t, pad_b = 10, 10, 10, 10
    row_h = 36
    bar_max_w = w - pad_l - pad_r - 110
    colors = ["#E06C75", "#C678DD", "#61AFEF", "#98C379", "#56B6C2"]
    total_h = pad_t + len(top10) * row_h + pad_b
    c.configure(scrollregion=(0, 0, w, total_h))
    for i, (cat, val) in enumerate(top10):
        y = pad_t + i * row_h + row_h // 2
        bar_w = int(bar_max_w * abs(val) / max_val) if max_val else 0
        bx = pad_l + 110
        fill = "#E5A550" if val >= 0 else colors[i % len(colors)]
        budget = self.budget_categorie.get(cat, 0.0) if val < 0 else 0.0
        tag_riga = f"riga_{i}"
        c.create_text(pad_l, y, text=cat[:16], anchor="w",
                          fill=self.TEXT_COLOR, font=("Arial", 9), tags=tag_riga)
        if budget > 0 and abs(val) > budget:
            bar_w_ok  = int(bar_max_w * budget / max_val)
            bar_w_ovr = max(bar_w - bar_w_ok, 2)
            rect_id = c.create_rectangle(
                    bx, y - 10, bx + max(bar_w_ok, 4), y + 10,
                    fill=fill, outline="", tags=tag_riga
            )
            c.create_rectangle(
                    bx + max(bar_w_ok, 4), y - 10,
                    bx + max(bar_w_ok, 4) + bar_w_ovr, y + 10,
                    fill="#E5A550", outline="", tags=tag_riga
            )
        else:
            rect_id = c.create_rectangle(
                    bx, y - 10, bx + max(bar_w, 4), y + 10,
                    fill=fill, outline="", tags=tag_riga
            )
        x_fine_barra = bx + max(bar_w, 4)
        if x_fine_barra > (w - 60): 
                    c.create_text(x_fine_barra - 5, y, text=f"{val:,.2f}€", anchor="e",
                                  fill="white", font=("Arial", 8, "bold"), tags=tag_riga)
        else:
                    c.create_text(x_fine_barra + 5, y, text=f"{val:,.2f}€", anchor="w",
                                  fill=self.TEXT_COLOR, font=("Arial", 8, "bold"), tags=tag_riga)
        voci = sorted(dettagli.get(cat, []), key=lambda x: x[0], reverse=True)
        tot_usc = sum(iv for _, iv, tv in voci if tv == "Uscita")
        tot_ent = sum(iv for _, iv, tv in voci if tv == "Entrata")
        w_l = 13
        w_v = 12
        righe_dati = [
                    f"{'[-] USCITE:':<{w_l}} {'-' + f'{tot_usc:,.2f}':>{w_v}}€",
                    f"{'[+] ENTRATE:':<{w_l}} {'+' + f'{tot_ent:,.2f}':>{w_v}}€",
                    f"{'[=] NETTO:':<{w_l}} {('+' if tot_ent-tot_usc >= 0 else '') + f'{tot_ent-tot_usc:,.2f}':>{w_v}}€",
        ]
        voci_righe = []
        for d_v, imp_v, tipo_v in voci[:15]:
                    p = "-" if tipo_v == "Uscita" else "+"
                    s = "»" if tipo_v == "Uscita" else "«"
                    dt = d_v.strftime('%d/%m')
                    sinistra = f"{s} {dt}"
                    destra = f"{p + f'{imp_v:,.2f}':>{w_v}}€"
                    gap = w_l + w_v + 2 - len(sinistra) - len(destra)
                    voci_righe.append(sinistra + " " * max(gap, 1) + destra)
        col_w = max(len(r) for r in righe_dati + voci_righe) if (righe_dati + voci_righe) else 28
        sep = "─" * col_w
        righe = [
                f" {cat.upper()} ".center(col_w, "═"),
                righe_dati[0],
                righe_dati[1],
                sep,
                righe_dati[2],
                sep,
                *voci_righe,
        ]
        if len(voci) > 15:
                righe.append(f"... +altri {len(voci)-15}")
        tip_txt = "\n".join(righe)
        c.tag_bind(tag_riga, "<Enter>",
                   lambda e, t=tip_txt: self._mostra_tip_safe(e, t))
        c.tag_bind(tag_riga, "<Leave>",
                   lambda e: self._nascondi_tip_safe())
        c.tag_bind(tag_riga, "<Double-1>",
                   lambda e, cat=cat, m=view_month, a=view_year:
                       self.mostra_transazioni_popup(
                           {"anno": str(a), "mese": m, "categoria": cat},
                           f"Dettaglio {cat} — {['Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno','Luglio','Agosto','Settembre','Ottobre','Novembre','Dicembre'][m-1]} {a}"
                       ))
        c.tag_bind(tag_riga, "<Button-3>",
                   lambda e, cat=cat: self.mostra_storico_categoria(cat))
    def _on_mousewheel(event):
        if not c.winfo_exists():
            return
        if event.num == 4:
            c.yview_scroll(-1, "units")
        elif event.num == 5:
            c.yview_scroll(1, "units")
        else:
            c.yview_scroll(int(-1 * (event.delta / 120)), "units")
    c.bind("<Enter>",      lambda e: c.focus_set())
    c.bind("<MouseWheel>", _on_mousewheel)
    c.bind("<Button-4>",   _on_mousewheel)
    c.bind("<Button-5>",   _on_mousewheel)

def mostra_storico_categoria(self, categoria):
    popup = tk.Toplevel(self)
    self.storico_cat_popup = popup
    popup.title(f"Storico — {categoria}")
    popup.withdraw()
    w, h = 520, 400
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    popup.geometry(f"{w}x{h}+{max(0,x)}+{max(0,y)}")
    popup.configure(bg=self.COLOR_TOPLEVEL)
    popup.resizable(False, False)
    popup.attributes("-topmost", True)
    popup.bind("<Escape>", lambda e: popup.destroy())
    now = datetime.date.today()
    MESI = ["Gen","Feb","Mar","Apr","Mag","Giu","Lug","Ago","Set","Ott","Nov","Dic"]
    totali = [0.0] * 12
    totali_ent = [0.0] * 12
    totali_usc = [0.0] * 12
    for d, entries in self.spese.items():
        if d.year == now.year:
            for entry in entries:
                if campo(entry, "categoria", "") == categoria:
                    imp = campo(entry, "importo", 0.0)
                    if campo(entry, "tipo", "") == "Entrata":
                        totali_ent[d.month - 1] += imp
                    else:
                        totali_usc[d.month - 1] += imp
                    totali[d.month - 1] = totali_ent[d.month - 1] - totali_usc[d.month - 1]
    totale_ent = sum(totali_ent)
    totale_usc = sum(totali_usc)
    saldo = totale_ent - totale_usc
    segno_saldo = "+" if saldo >= 0 else ""
    tk.Label(popup, text=f"{categoria} — {now.year}",
             bg=self.COLOR_TOPLEVEL, fg=self.COLOR_HIGHLIGHT,
             font=("Arial", 11, "bold")).pack(pady=(10, 4))
    c = tk.Canvas(popup, bg=self.COLOR_WIDGET_BG, highlightthickness=0)
    c.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 4))
    tk.Label(popup,
             text=f"  Entrate: +{totale_ent:,.2f}€   Uscite: -{totale_usc:,.2f}€   Saldo: {segno_saldo}{saldo:,.2f}€",
             bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
             font=("Arial", 8)).pack(pady=(0, 2))
    tk.Label(popup,
             text="  Doppio clic → Dettaglio mese",
             bg=self.COLOR_TOPLEVEL, fg="gray",
             font=("Arial", 7, "italic")).pack()         
    bot_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    bot_f.pack(fill=tk.X, side=tk.BOTTOM, pady=8)
    b = tk.Label(bot_f, image=self.icone_gui.get("chiudi"), text="  Chiudi ",
                 compound="left", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                 cursor="hand2", font=("Arial", 10, "bold"))
    b.pack(anchor="center")
    b.bind("<Button-1>", lambda e: popup.destroy())
    popup.update_idletasks()
    popup.deiconify()
    def disegna():
        cw, ch = c.winfo_width(), c.winfo_height()
        c.delete("all")
        pad_l, pad_r, pad_t, pad_b = 30, 10, 30, 30
        max_val = max(abs(v) for v in totali) or 1
        bar_w = (cw - pad_l - pad_r) / 12
        for i, val in enumerate(totali):
            bh = int((abs(val) / max_val) * (ch - pad_t - pad_b))
            x1 = pad_l + i * bar_w + bar_w * 0.1
            x2 = pad_l + (i + 1) * bar_w - bar_w * 0.1
            y1 = ch - pad_b - bh
            y2 = ch - pad_b
            fill = "#98C379" if val > 0 else "#E06C75" if val < 0 else self.COLOR_WIDGET_BG
            rect_id = c.create_rectangle(x1, y1, x2, y2, fill=fill, outline="")
            if val != 0:
                c.create_text((x1+x2)/2, y1 - 10, text=f"{val:.0f}",
                              fill=self.TEXT_COLOR, font=("Arial", 7))
                c.tag_bind(rect_id, "<Double-1>",
                           lambda e, m=i+1, a=now.year:
                               self.mostra_transazioni_popup(
                                   {"anno": str(a), "mese": m, "categoria": categoria},
                                   f"Dettaglio {categoria} — {MESI[m-1]} {a}"
                               ))
            c.create_text((x1+x2)/2, ch - pad_b + 10, text=MESI[i],
                          fill=self.TEXT_COLOR, font=("Arial", 8))
    c.bind("<Configure>", lambda e: disegna())

def suggerisci_tipo_categoria(self, categoria):
    n_entrate = 0
    n_uscite = 0
    for voci in self.spese.values():
        for voce in voci:
            if campo(voce, "categoria", "") == categoria:
                tipo = campo(voce, "tipo", "")
                if tipo == "Entrata":
                    n_entrate += 1
                elif tipo == "Uscita":
                    n_uscite += 1
    totale = n_entrate + n_uscite
    if totale == 0:
        return ("Uscita", 0, 0)
    perc_entrate = int(n_entrate / totale * 100)
    perc_uscite = int(n_uscite / totale * 100)
    tipo_prevalente = "Entrata" if n_entrate >= n_uscite else "Uscita"
    return (tipo_prevalente, perc_entrate, perc_uscite)

# Finestra Interattiva per l'Analisi Dettagliata per Categoria e Periodo
def open_analisi_categoria(self):
    popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    popup.title("Analisi Categoria")
    popup.transient(self)
    popup.bind("<Escape>", lambda e: popup.destroy())
    self.update_idletasks()
    w, h = 1200, 620
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    popup.geometry(f"{w}x{h}+{x}+{y}")
    popup.resizable(True, True)
    popup.minsize(w, h)
    frame_top = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    frame_top.pack(padx=18, pady=10, fill=tk.X)
    img_search = self.icone_gui.get("search")

    lbl_modalita = tk.Label(
            frame_top, 
            text=" Seleziona modalità:", 
            image=img_search,
            compound="left",
            bg=self.COLOR_TOPLEVEL, 
            fg=self.TEXT_COLOR,
            font=("Arial", 10, "bold")
    )
    lbl_modalita.image = img_search
    lbl_modalita.pack(side=tk.LEFT, padx=(10, 5))
    mode_var = tk.StringVar(value="Giorno")
    mode_combo = ttk.Combobox(frame_top, values=["Giorno", "Mese", "Anno", "Totale"], style="Border.TCombobox", textvariable=mode_var, state="readonly", width=10)
    mode_combo.pack(side=tk.LEFT, padx=10)
    frame_period = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    frame_period.pack(padx=18, pady=2, fill=tk.X)
    months = [
        "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
    ]
    today = datetime.date.today()
    anni_presenti = sorted({d.year for d in self.spese.keys()}, reverse=True)
    if not anni_presenti:
        anni_presenti = [today.year]
    year_var_initial = str(anni_presenti[0]) if anni_presenti else str(today.year)
    year_var = tk.StringVar(value=today.year)
    day_var = tk.StringVar(value=str(today.day))
    month_var = tk.StringVar(value=months[today.month - 1]) 
    def get_years_presenti():
        return [str(y) for y in anni_presenti]
    year_combo = ttk.Combobox(frame_period, values=get_years_presenti(), textvariable=year_var, style="Border.TCombobox", state="readonly", width=8)
    month_combo = ttk.Combobox(frame_period, values=months, textvariable=month_var, style="Border.TCombobox", state="readonly", width=16)
    day_combo = ttk.Combobox(frame_period, values=[str(d) for d in range(1, 32)], textvariable=day_var, style="Border.TCombobox", state="readonly", width=4)
    year_combo_only = ttk.Combobox(frame_period, values=get_years_presenti(), textvariable=year_var, style="Border.TCombobox", state="readonly", width=8)
    def update_days(*_):
        try:
            m = months.index(month_var.get()) + 1
            y = int(year_var.get())
        except Exception:
            m = today.month
            y = today.year
        n_days = calendar.monthrange(y, m)[1]
        days = [str(d) for d in range(1, n_days+1)]
        day_combo['values'] = days
        if day_var.get() not in days:
            day_var.set(days[-1])
    month_var.trace_add("write", update_days)
    year_var.trace_add("write", update_days)
    def reset_period():
        oggi = datetime.date.today()
        day_var.set(str(oggi.day))
        month_var.set(months[oggi.month - 1])
        year_var.set(str(oggi.year))
    def update_period_inputs(*_):
        for widget in frame_period.winfo_children():
            widget.pack_forget()
        mode = mode_var.get()
        img_reset = self.icone_gui.get("reset_campo")
        reset_btn = ttk.Label(
            frame_period,
            compound="left",
            image=img_reset,
            text="🔙" if not img_reset else "",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2",
            padding=(5, 5)
        )
        reset_btn.image = img_reset
        reset_btn.bind("<Button-1>", lambda e: reset_period())
        if mode == "Giorno":
            day_combo.pack(side=tk.LEFT)
            month_combo.pack(side=tk.LEFT, padx=(4,8))
            year_combo.pack(side=tk.LEFT)
            reset_btn.pack(side=tk.LEFT, padx=(10, 0))
            update_days()
        elif mode == "Mese":
            month_combo.pack(side=tk.LEFT, padx=(0,8))
            year_combo.pack(side=tk.LEFT)
            reset_btn.pack(side=tk.LEFT, padx=(10, 0))
        elif mode == "Anno":
            year_combo_only.pack(side=tk.LEFT)
            reset_btn.pack(side=tk.LEFT, padx=(10, 0))
    mode_combo.bind("<<ComboboxSelected>>", update_period_inputs)
    update_period_inputs()
    frame_cat = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    frame_cat.pack(padx=18, pady=12, fill=tk.X)
    tk.Label(frame_cat, bg=self.COLOR_TOPLEVEL ,fg=self.TEXT_COLOR, text="Categoria:").pack(side=tk.LEFT)
    def get_catlist():
        return ["Tutte le categorie"] + sorted(self.categorie, key=lambda c: c.lower())
    cat_var = tk.StringVar(value="Tutte le categorie")
    cat_combo = ttk.Combobox(frame_cat, values=get_catlist(), textvariable=cat_var, style="Border.TCombobox", state="readonly", width=25)
    cat_combo.pack(side=tk.LEFT, padx=10)
    main_result_frame = ttk.Frame(popup)
    main_result_frame.pack(padx=18, fill=tk.BOTH, expand=True) 
    main_result_frame.grid_rowconfigure(0, weight=1)
    main_result_frame.grid_columnconfigure(0, weight=1)
    scroll_y = ttk.Scrollbar(main_result_frame, orient=tk.VERTICAL, style="Vertical.TScrollbar")
    scroll_y.grid(row=0, column=1, sticky="ns")
    scroll_x = ttk.Scrollbar(main_result_frame, orient=tk.HORIZONTAL, style="Horizontal.TScrollbar")
    scroll_x.grid(row=1, column=0, sticky="ew")
    text_result = tk.Text(
        main_result_frame, 
        height=22, 
        width=90, 
        font=("Courier New", 10), 
        wrap='none',
        yscrollcommand=scroll_y.set, 
        xscrollcommand=scroll_x.set,
        bg=self.COLOR_TOPLEVEL, 
        fg=self.TEXT_COLOR 
    )
    text_result.grid(row=0, column=0, sticky="nsew") 
    scroll_y.config(command=text_result.yview)
    scroll_x.config(command=text_result.xview)
    text_result.config(state="disabled")
    frame_buttons = ttk.Frame(popup)
    frame_buttons.pack(fill=tk.X, padx=18, pady=8) 
    img_chiudi_pop = self.icone_gui.get("chiudi")
    close_btn = ttk.Label(
            frame_buttons,
            compound="left",
            image=img_chiudi_pop,
            text=" Chiudi" if img_chiudi_pop else "Chiudi",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2",
            padding=(10, 5)
    )
    close_btn.image = img_chiudi_pop
    close_btn.pack(side=tk.RIGHT, padx=4)
    close_btn.bind("<Button-1>", lambda e: popup.destroy())
    img_esporta = self.icone_gui.get("salva")
    export_btn = ttk.Label(
            frame_buttons,
            compound="left",
            image=img_esporta,
            text=" Esporta" if img_esporta else "Esporta",
            background=self.COLOR_WIDGET_BG,
            foreground=self.TEXT_COLOR,
            cursor="hand2",
            padding=(10, 5)
    )
    export_btn.image = img_esporta
    export_btn.pack(side=tk.LEFT, padx=4)
    def aggiorna_cat_combo():
        cat_combo['values'] = get_catlist()
        if cat_var.get() not in cat_combo['values']:
            cat_var.set("Tutte le categorie")
    aggiorna_cat_combo()
    def mostra_dettagli(*_):
        cat = cat_var.get()
        mode = mode_var.get()
        result_lines = []
        today = datetime.date.today()
        def calcola_totali():
            entrate = sum(e[2] for _, e in filtered if "entrata" in e[3].lower())
            uscite = sum(e[2] for _, e in filtered if "entrata" not in e[3].lower())
            return entrate, uscite, entrate - uscite
        filtered = []
        label_intestazione = ""
        if mode == "Giorno":
            try:
                m = months.index(month_var.get()) + 1
                d = int(day_var.get())
                y = int(year_var.get())
                giorno = datetime.date(y, m, d)
            except Exception:
                giorno = today
            spese = self.spese.get(giorno, [])
            filtered = [(giorno, e) for e in spese if cat == "Tutte le categorie" or e[0] == cat]
            label_intestazione = f"{'Entrate/Uscite' if cat == 'Tutte le categorie' else 'Spese ' + cat} per il giorno {giorno.strftime('%d-%m-%Y')}"
        elif mode == "Mese":
            try:
                m = months.index(month_var.get()) + 1
                y = int(year_var.get())
            except Exception:
                m = today.month
                y = today.year
            for d, sp in self.spese.items():
                if d.year == y and d.month == m:
                    for e in sp:
                        if cat == "Tutte le categorie" or e[0] == cat:
                            filtered.append((d, e))
            label_intestazione = f"{'Entrate/Uscite' if cat == 'Tutte le categorie' else 'Spese ' + cat} per {self.get_month_name(m)} {y}"
        elif mode == "Anno":
            try:
                y = int(year_var.get())
            except Exception:
                y = today.year
            for d, sp in self.spese.items():
                if d.year == y:
                    for e in sp:
                        if cat == "Tutte le categorie" or e[0] == cat:
                            filtered.append((d, e))
            label_intestazione = f"{'Entrate/Uscite' if cat == 'Tutte le categorie' else 'Spese ' + cat} per l'anno {y}"
        elif mode == "Totale":
            for d, sp in self.spese.items():
                for e in sp:
                    if cat == "Tutte le categorie" or e[0] == cat:
                        filtered.append((d, e))
            label_intestazione = f"{'Entrate/Uscite' if cat == 'Tutte le categorie' else 'Spese ' + cat} totali"
        text_result.configure(font=("Courier New", 10))
        result_lines.clear()
        if not filtered:
            result_lines.append(f"Nessuna spesa per '{cat}'.")
        else:
            W_DATA, W_CAT, W_DESC, W_TIPO, W_IMP, W_CNT, W_MET, W_ORA, W_TAG = 10, 16, 20, 8, 12, 14, 12, 6, 16
            larghezza_riga = W_DATA + W_CAT + W_DESC + W_TIPO + W_IMP + W_CNT + W_MET + W_ORA + W_TAG + 24
            result_lines.append("═" * larghezza_riga)
            result_lines.append(label_intestazione)
            result_lines.append("─" * larghezza_riga)
            result_lines.append(
                f"{'Data':<{W_DATA}} │ {'Categoria':<{W_CAT}} │ {'Descrizione':<{W_DESC}} │ "
                f"{'Tipo':<{W_TIPO}} │ {'Importo':>{W_IMP}} │ {'Conto':<{W_CNT}} │ "
                f"{'Metodo':<{W_MET}} │ {'Ora':<{W_ORA}} │ {'Hashtag':<{W_TAG}}"
            )
            result_lines.append("─" * larghezza_riga)
            for d, e in sorted(filtered, key=lambda x: x[0], reverse=True):
                valore = abs(e[2])
                categoria = e[0][:W_CAT-3] + '...' if len(e[0]) > W_CAT else e[0]
                descrizione = e[1][:W_DESC-3] + '...' if len(e[1]) > W_DESC else e[1]
                tipo_riga = str(e[3]).capitalize()
                conto = campo(e, "conto", "")
                if not conto:
                    try:
                        conto = self._trova_conto_da_portafoglio(d, float(e[2]), tipo_riga) or ""
                    except Exception:
                        conto = ""
                metodo = campo(e, "metodo_pagamento", "")
                ora = campo(e, "ora", "")
                hashtag_txt = " ".join(campo(e, "hashtag", []))
                conto_tr    = (conto[:W_CNT-3] + '...') if len(conto) > W_CNT else conto
                metodo_tr   = (metodo[:W_MET-3] + '...') if len(metodo) > W_MET else metodo
                hashtag_tr  = (hashtag_txt[:W_TAG-3] + '...') if len(hashtag_txt) > W_TAG else hashtag_txt
                result_lines.append(
                    f"{d.strftime('%d-%m-%Y'):<{W_DATA}} │ {categoria:<{W_CAT}} │ {descrizione:<{W_DESC}} │ "
                    f"{tipo_riga:<{W_TIPO}} │ {valore:>{W_IMP-2}.2f} € │ {conto_tr:<{W_CNT}} │ "
                    f"{metodo_tr:<{W_MET}} │ {ora:<{W_ORA}} │ {hashtag_tr:<{W_TAG}}"
                )
            result_lines.append("─" * larghezza_riga)
            entrate, uscite, saldo = calcola_totali()
            result_lines.append(f"{'Totale entrate':<54}  {entrate:>9.2f} €")
            result_lines.append(f"{'Totale uscite':<54}  {uscite:>9.2f} €")
            result_lines.append(f"{'Saldo finale':<54}  {saldo:+9.2f} €")
            result_lines.append("═" * larghezza_riga)
        text_result.config(state="normal")
        text_result.delete("1.0", tk.END)
        text_result.insert("end", "\n".join(result_lines))
        text_result.config(state="disabled")
    def esporta_analisi():
        text_result.config(state="normal")
        contenuto = text_result.get("1.0", tk.END).strip()
        text_result.config(state="disabled")
        if not contenuto:
            self.show_toast("Nulla da esportare.")
            return
        preview = tk.Toplevel(popup, bg=self.COLOR_TOPLEVEL)
        preview.title("Preview esportazione")
        preview.withdraw()
        larghezza_finestra = 1200
        altezza_finestra = 620
        x = popup.winfo_rootx() + (popup.winfo_width() // 2) - (larghezza_finestra // 2)
        y = popup.winfo_rooty() + (popup.winfo_height() // 2) - (altezza_finestra // 2)
        preview.geometry(f"{larghezza_finestra}x{altezza_finestra}+{x}+{y}")
        preview.minsize(larghezza_finestra, altezza_finestra)
        preview.transient(popup)
        preview.resizable(True, True)
        preview.update_idletasks()
        preview.deiconify()
        preview.focus_set()
        preview.grab_set()
        preview.bind('<Escape>', lambda e: preview.destroy())
        tx = tk.Text(preview, font=("Courier new", 10), wrap="none")
        tx.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        contenuto_preview = "\n".join(" " + l for l in contenuto.splitlines())
        tx.insert(tk.END, contenuto_preview)
        tx.config(state="disabled")
        frm = tk.Frame(preview, bg=self.COLOR_TOPLEVEL)
        frm.pack(fill=tk.X, padx=10, pady=8)
        def do_save():
            now = datetime.date.today()
            default_filename = f"Analisi_Export_{now.day:02d}-{now.month:02d}-{now.year}.txt"
            file = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("File txt", "*.txt")], initialdir=_app.EXPORT_FILES, title="Esporta Analisi Categoria", initialfile=default_filename, confirmoverwrite=False, parent=preview)
            if file:
                if os.path.exists(file):
                    conferma = self.show_custom_askyesno("Sovrascrivere file?", f"Il file '{os.path.basename(file)}' \nesiste già. Vuoi sovrascriverlo?")
                    if not conferma: return  
                try:
                    with open(file, "w", encoding="utf-8") as f:
                        f.write(contenuto_preview)
                    self.show_custom_warning("Esporta", f"✓ Analisi esportata in:\n{file}")
                    preview.destroy()
                except Exception as e:
                    self.show_custom_warning("Errore", f"❌ Salvataggio fallito:\n{e}")
        def do_save_pdf():
            import pymupdf as fitz
            now = datetime.date.today()
            default_filename = f"Analisi_Export_{now.day:02d}-{now.month:02d}-{now.year}.pdf"
            file = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("Documento PDF", "*.pdf")],
                initialdir=_app.EXPORT_FILES,
                title="Esporta Analisi Categoria come PDF",
                initialfile=default_filename,
                confirmoverwrite=False,
                parent=preview
            )
            if file:
                if os.path.exists(file):
                    conferma = self.show_custom_askyesno("Sovrascrivere file?", f"Il file '{os.path.basename(file)}' \nesiste già. Vuoi sovrascriverlo?")
                    if not conferma: return
                try:
                    doc = fitz.open()
                    lines = contenuto_preview.split('\n')
                    page_w, page_h = 1000, 595
                    margin = 30
                    font_size = 6.5
                    line_height = font_size + 2
                    page = doc.new_page(width=page_w, height=page_h)
                    y = margin
                    for line in lines:
                        if y > (page_h - margin):
                            page = doc.new_page(width=page_w, height=page_h)
                            y = margin
                        page.insert_text((margin, y), line, fontname="cour", fontsize=font_size)
                        y += line_height
                    doc.save(file)
                    doc.close()
                    self.show_custom_warning("Esportazione completata", f"✓ PDF salvato:\n{file}")
                    preview.destroy()
                except Exception as e:
                    self.show_custom_warning("Errore", f"❌ Creazione PDF fallita:\n{e}")
        img_salva = self.icone_gui.get("salva")
        btn_salva = ttk.Label(frm, compound="left", image=img_salva, text=" Esporta TXT" if img_salva else "💾 Esporta TXT", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_salva.pack(side=tk.LEFT, padx=6)
        btn_salva.bind("<Button-1>", lambda e: do_save())
        img_esporta_pdf = self.icone_gui.get("salva")
        btn_esporta_pdf = ttk.Label(frm, compound="left", image=img_esporta_pdf, text=" Esporta PDF" if img_esporta_pdf else "📕 Esporta PDF", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_esporta_pdf.pack(side=tk.LEFT, padx=6)
        btn_esporta_pdf.bind("<Button-1>", lambda e: do_save_pdf())
        img_stampa = self.icone_gui.get("stampa")
        btn_stampa = ttk.Label(frm, compound="left", image=img_stampa, text=" Stampa" if img_stampa else "📄 Stampa", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_stampa.pack(side=tk.LEFT, padx=6)
        btn_stampa.bind("<Button-1>", lambda e: self._stampa_lista_diretta(contenuto_preview.rstrip('\n'), self.show_custom_warning))
        img_chiudi = self.icone_gui.get("chiudi")
        btn_chiudi = ttk.Label(frm, compound="left", image=img_chiudi, text=" Chiudi" if img_chiudi else "❌ Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_chiudi.pack(side=tk.RIGHT, padx=6)
        btn_chiudi.bind("<Button-1>", lambda e: preview.destroy())
        preview.lift()
        preview.attributes('-topmost', True)
        preview.after(100, lambda: preview.attributes('-topmost', False))
        preview.bind("<Escape>", lambda e: preview.destroy())
    export_btn.bind("<Button-1>", lambda e: esporta_analisi())
    mode_var.trace_add("write", mostra_dettagli)
    month_var.trace_add("write", mostra_dettagli)
    year_var.trace_add("write", mostra_dettagli)
    day_var.trace_add("write", mostra_dettagli)
    cat_var.trace_add("write", mostra_dettagli)
    mostra_dettagli()

def _ottieni_categorie_ricorrenti_mancanti(self):
    from datetime import datetime
    oggi = datetime.today().date()
    def converti_data(d):
        if isinstance(d, str):
            try: return datetime.strptime(d, "%d-%m-%Y").date()
            except: return None
        elif isinstance(d, datetime): return d.date()
        return d
    categorie_base = {cat.title() for cat in self.categorie if cat}
    if not categorie_base:
        return []
    presenti_questo_mese = set()
    conteggio_storico = {}
    mesi_gia_contati = set()
    MESI_INDIETRO = 12
    for d, sp in self.spese.items():
        dd = converti_data(d)
        if not dd: continue
        diff_mesi = (oggi.year - dd.year) * 12 + (oggi.month - dd.month)
        if diff_mesi == 0:
            for voce in sp:
                cat_raw = campo(voce, "categoria", "")
                if cat_raw.strip():
                    presenti_questo_mese.add(cat_raw.strip().title())
        elif 1 <= diff_mesi <= MESI_INDIETRO:
            for voce in sp:
                cat_raw = campo(voce, "categoria", "")
                if cat_raw.strip():
                    cat = cat_raw.strip().title()
                    chiave_mese = (cat, dd.year, dd.month)
                    if cat in categorie_base and chiave_mese not in mesi_gia_contati:
                        conteggio_storico[cat] = conteggio_storico.get(cat, 0) + 1
                        mesi_gia_contati.add(chiave_mese)
    categorie_mancanti = []
    for cat in categorie_base:
        presenze_passate = conteggio_storico.get(cat, 0)
        if presenze_passate >= 4 and cat not in presenti_questo_mese:
            categorie_mancanti.append(cat)
    return sorted(categorie_mancanti)

def gruppo_categorie(self):
    popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL )
    popup.title("Analisi per categorie selezionate")
    popup.geometry("1200x650") 
    popup.withdraw() 
    self.update_idletasks()
    main_x = self.winfo_x()
    main_y = self.winfo_y()
    main_width = self.winfo_width()
    main_height = self.winfo_height()
    popup_width = 1200
    popup_height = 650
    center_x = main_x + (main_width // 2) - (popup_width // 2)
    center_y = main_y + (main_height // 2) - (popup_height // 2)
    popup.geometry(f"{popup_width}x{popup_height}+{center_x}+{center_y}")
    popup.minsize(popup_width, popup_height)
    popup.transient(self)
    popup.update_idletasks()
    popup.deiconify()
    popup.update()  
    main_frame = ttk.Frame(popup, padding=10)
    main_frame.pack(fill="both", expand=True)
    today = datetime.date.today()
    mesi = ["Tutti"] + ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                    "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    mese_var = tk.StringVar(value="Tutti")
    anno_var = tk.StringVar(value=str(today.year))
    mostra_future_var = tk.BooleanVar(value=True)
    top_bar = ttk.Frame(main_frame)
    top_bar.pack(fill="x", pady=(0, 10))
    ttk.Label(top_bar, text="Mese:").pack(side="left", padx=(0, 5))
    ttk.Combobox(top_bar, values=mesi, textvariable=mese_var, style="Border.TCombobox", state="readonly", width=12).pack(side="left")
    anni = sorted({
        d.year if not isinstance(d, str) else datetime.datetime.strptime(d, "%d-%m-%Y").year
        for d in self.spese
    }, reverse=True)
    ttk.Label(top_bar, text="Anno:").pack(side="left", padx=(10, 5))
    ttk.Combobox(top_bar, values=["Tutti"] + [str(a) for a in anni], textvariable=anno_var, style="Border.TCombobox", state="readonly", width=8).pack(side="left")
    img_reset_filtri = self.icone_gui.get("reset")
    btn_reset_filtri = tk.Label(top_bar, compound="left", image=img_reset_filtri, text=" Filtri correnti" if img_reset_filtri else " 🔙 Filtri correnti", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padx=10, pady=5, font=("Arial", 9, "bold"))
    btn_reset_filtri.pack(side="left", padx=(10, 0))
    btn_reset_filtri.bind("<Button-1>", lambda e: [mese_var.set("Tutti"), anno_var.set(str(today.year))])
    ttk.Checkbutton(
        top_bar,
        text="Includi movimenti futuri nei totali",
        variable=mostra_future_var
    ).pack(side="left", padx=(20,0))
    valori_combo = ["— Nessuna —"] + sorted(list(self.categorie_tipi.keys()))
    selettori_box = ttk.LabelFrame(main_frame, text="Seleziona fino a 10 categorie da analizzare")
    selettori_box.pack(fill="x", pady=(5, 15))
    sx = ttk.Frame(selettori_box)
    dx = ttk.Frame(selettori_box)
    sx.pack(side="left", fill="both", expand=True, padx=(0, 10))
    dx.pack(side="right", fill="both", expand=True)
    combo_vars = []
    for i in range(10):
        var = tk.StringVar(value="— Nessuna —")
        cb = ttk.Combobox(sx if i < 5 else dx, values=valori_combo, textvariable=var, style="Border.TCombobox", state="readonly", width=35, height=15)
        cb.pack(anchor="w", pady=2)
        combo_vars.append(var)
    ttk.Label(main_frame, text="📊 Risultato:", font=("Arial", 10, "bold")).pack(anchor="w")

    text_output = tk.Text(main_frame, height=15, wrap="word", 
                         font=("Courier New", 10),
                         bg=self.COLOR_WIDGET_BG,
                         fg=self.TEXT_COLOR,
                         insertbackground=self.TEXT_COLOR,
                         padx=10, pady=10,
                         borderwidth=1,
                         relief="flat",
                         highlightthickness=1,
                         highlightbackground=self.COLOR_BUTTON_BG)
    scroll = ttk.Scrollbar(main_frame, command=text_output.yview, style="Vertical.TScrollbar")
    text_output.config(yscrollcommand=scroll.set)
    text_output.pack(side="left", fill="both", expand=True, pady=(5, 10))
    scroll.pack(side="right", fill="y")
    text_output.config(state="disabled")
    def analizza():
        text_output.config(state="normal")
        text_output.delete("1.0", "end")
        anno_sel = anno_var.get()
        if anno_sel != "Tutti":
            try:
                anno = int(anno_sel)
            except:
                text_output.config(state="disabled")
                self.show_custom_warning("Errore", "Anno non valido.")
                return
        else:
            anno = None
        selezionato = mese_var.get()
        if selezionato not in mesi:
            text_output.config(state="disabled")
            self.show_custom_warning("Errore", "Mese non valido.")
            return
        scelte = {v.get().strip().title() for v in combo_vars if v.get() != "— Nessuna —"}
        risultato = {}
        oggi = datetime.date.today()
        for d, sp in self.spese.items():
            if isinstance(d, str):
                d = datetime.datetime.strptime(d, "%d-%m-%Y").date()
            if not mostra_future_var.get() and d > oggi:
                continue
            if (anno is None or d.year == anno) and (selezionato == "Tutti" or d.month == mesi.index(selezionato)):
                for voce in sp:
                    cat = campo(voce, "categoria", "").strip().title()
                    imp = campo(voce, "importo", 0.0)
                    tipo = campo(voce, "tipo", "")
                    if cat in scelte:
                            if cat not in risultato:
                                risultato[cat] = {"num": 0, "uscite": 0.0, "entrate": 0.0}
                            risultato[cat]["num"] += 1
                            if tipo == "Uscita":
                                risultato[cat]["uscite"] += imp
                            elif tipo == "Entrata":
                                risultato[cat]["entrate"] += imp
        anno_label = "Tutti gli anni" if anno is None else str(anno)
        righe = [f"Analisi categorie – {mese_var.get()} {anno_label}\n"]
        righe.append(f"{'Categoria':<30} {'Num':>4}   {'Uscite (€)':>12}   {'Entrate (€)':>12}   {'Saldo (€)':>12}")
        righe.append("─" * 80)
        totale = 0.0
        tot_entrate = 0.0
        tot_uscite = 0.0
        for cat, dati in sorted(risultato.items(), key=lambda x: -(x[1]["entrate"] - x[1]["uscite"])):
            saldo = dati["entrate"] - dati["uscite"]
            righe.append(f"{cat:<30} {dati['num']:>4}   {dati['uscite']:>12.2f}   {dati['entrate']:>12.2f}   {saldo:>12.2f}")
            totale += saldo
            tot_entrate += dati["entrate"]
            tot_uscite += dati["uscite"]
        righe.append("─" * 80)
        _label_entrate = "Totale Entrate:"
        _label_uscite = "Totale Uscite:"
        _label_saldo = "Saldo Netto (Entrate - Uscite):"
        _larg_label = max(len(_label_entrate), len(_label_uscite), len(_label_saldo)) + 1
        righe.append(f"{_label_entrate:<{_larg_label}} {tot_entrate:>12.2f} €")
        righe.append(f"{_label_uscite:<{_larg_label}} {tot_uscite:>12.2f} €")
        righe.append(f"{_label_saldo:<{_larg_label}} {totale:>12.2f} €")
        text_output.insert("1.0", "\n".join(righe))
        text_output.config(state="disabled")
    def reset_campi():
        mese_var.set("Tutti")
        anno_var.set(str(today.year))
        mostra_future_var.set(True)
        for var in combo_vars:
            var.set("— Nessuna —")
        text_output.config(state="normal")
        text_output.delete("1.0", "end")
        text_output.config(state="disabled")
    def esporta_analisi():
        contenuto = text_output.get("1.0", "end").strip()
        if not contenuto:
            self.show_toast("Nessun risultato da esportare.")
            return
        preview = tk.Toplevel(popup, bg=self.COLOR_TOPLEVEL)
        preview.title("Preview esportazione")
        preview.withdraw()
        larghezza_finestra = 1200
        altezza_finestra = 620
        x = popup.winfo_rootx() + (popup.winfo_width() // 2) - (larghezza_finestra // 2)
        y = popup.winfo_rooty() + (popup.winfo_height() // 2) - (altezza_finestra // 2)
        preview.geometry(f"{larghezza_finestra}x{altezza_finestra}+{x}+{y}")
        preview.minsize(larghezza_finestra, altezza_finestra)
        preview.transient(popup)
        preview.resizable(True, True)
        preview.update_idletasks()
        preview.deiconify()
        preview.focus_set()
        preview.grab_set()
        preview.bind('<Escape>', lambda e: preview.destroy())
        tx = tk.Text(preview, font=("Courier new", 10), wrap="none")
        tx.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        contenuto_preview = "\n".join(" " + l for l in contenuto.splitlines())
        tx.insert(tk.END, contenuto_preview)
        tx.config(state="disabled")
        frm = tk.Frame(preview, bg=self.COLOR_TOPLEVEL)
        frm.pack(fill=tk.X, padx=10, pady=8)
        def do_save():
            now = datetime.date.today()
            default_filename = f"Analisi_Categorie_{now:%d_%m_%Y}.txt"
            file = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("File txt", "*.txt")], initialdir=_app.EXPORT_FILES, title="Esporta Analisi Categorie", initialfile=default_filename, confirmoverwrite=False, parent=preview)
            if file:
                if os.path.exists(file):
                    conferma = self.show_custom_askyesno("Sovrascrivere file?", f"Il file '{os.path.basename(file)}' \nesiste già. Vuoi sovrascriverlo?")
                    if not conferma: return
                try:
                    with open(file, "w", encoding="utf-8") as f:
                        f.write(contenuto_preview)
                    self.show_custom_warning("Esporta", f"✓ Analisi esportata in:\n{file}")
                    preview.destroy()
                except Exception as e:
                    self.show_custom_warning("Errore", f"❌ Salvataggio fallito:\n{e}")
        def do_save_pdf():
            import pymupdf as fitz
            now = datetime.date.today()
            default_filename = f"Analisi_Categorie_{now:%d_%m_%Y}.pdf"
            file = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("Documento PDF", "*.pdf")],
                initialdir=_app.EXPORT_FILES,
                title="Esporta Analisi Categorie come PDF",
                initialfile=default_filename,
                confirmoverwrite=False,
                parent=preview
            )
            if file:
                if os.path.exists(file):
                    conferma = self.show_custom_askyesno("Sovrascrivere file?", f"Il file '{os.path.basename(file)}' \nesiste già. Vuoi sovrascriverlo?")
                    if not conferma: return
                try:
                    doc = fitz.open()
                    lines = contenuto_preview.split('\n')
                    page_w, page_h = 1000, 595
                    margin = 30
                    font_size = 6.5
                    line_height = font_size + 2
                    page = doc.new_page(width=page_w, height=page_h)
                    y = margin
                    for line in lines:
                        if y > (page_h - margin):
                            page = doc.new_page(width=page_w, height=page_h)
                            y = margin
                        page.insert_text((margin, y), line, fontname="cour", fontsize=font_size)
                        y += line_height
                    doc.save(file)
                    doc.close()
                    self.show_custom_warning("Esportazione completata", f"✓ PDF salvato:\n{file}")
                    preview.destroy()
                except Exception as e:
                    self.show_custom_warning("Errore", f"❌ Creazione PDF fallita:\n{e}")
        img_salva = self.icone_gui.get("salva")
        btn_salva = ttk.Label(frm, compound="left", image=img_salva, text=" Esporta TXT" if img_salva else "💾 Esporta TXT", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_salva.pack(side=tk.LEFT, padx=6)
        btn_salva.bind("<Button-1>", lambda e: do_save())
        img_esporta_pdf = self.icone_gui.get("salva")
        btn_esporta_pdf = ttk.Label(frm, compound="left", image=img_esporta_pdf, text=" Esporta PDF" if img_esporta_pdf else "📕 Esporta PDF", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_esporta_pdf.pack(side=tk.LEFT, padx=6)
        btn_esporta_pdf.bind("<Button-1>", lambda e: do_save_pdf())
        img_stampa = self.icone_gui.get("stampa")
        btn_stampa = ttk.Label(frm, compound="left", image=img_stampa, text=" Stampa" if img_stampa else "📄 Stampa", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_stampa.pack(side=tk.LEFT, padx=6)
        btn_stampa.bind("<Button-1>", lambda e: self._stampa_lista_diretta(contenuto_preview.rstrip('\n'), self.show_custom_warning))
        img_chiudi = self.icone_gui.get("chiudi")
        btn_chiudi = ttk.Label(frm, compound="left", image=img_chiudi, text=" Chiudi" if img_chiudi else "❌ Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_chiudi.pack(side=tk.RIGHT, padx=6)
        btn_chiudi.bind("<Button-1>", lambda e: preview.destroy())
        preview.lift()
        preview.attributes('-topmost', True)
        preview.after(100, lambda: preview.attributes('-topmost', False))
    mostra_future_var.trace_add("write", lambda *a: analizza())
    bottom_buttons = tk.Frame(popup, bg=self.COLOR_TOPLEVEL ) 
    bottom_buttons.pack(fill="x", pady=10)
    img_analizza = self.icone_gui.get("report")
    btn_analizza = tk.Label(bottom_buttons, compound="left", image=img_analizza, text="Analizza" if img_analizza else "📥 Analizza", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padx=12, pady=6, font=("Arial", 9, "bold"))
    btn_analizza.pack(side="left", padx=10)
    btn_analizza.bind("<Button-1>", lambda e: analizza())
    img_salva_an = self.icone_gui.get("salva")
    btn_salva_an = tk.Label(bottom_buttons, compound="left", image=img_salva_an, text="Esporta" if img_salva_an else "💾 Esporta", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padx=12, pady=6, font=("Arial", 9, "bold"))
    btn_salva_an.pack(side="left", padx=10)
    btn_salva_an.bind("<Button-1>", lambda e: esporta_analisi())
    img_reset_an = self.icone_gui.get("reset")
    btn_reset_an = tk.Label(bottom_buttons, compound="left", image=img_reset_an, text="Reset campi" if img_reset_an else "🟨 Reset campi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padx=12, pady=6, font=("Arial", 9, "bold"))
    btn_reset_an.pack(side="left", padx=10)
    btn_reset_an.bind("<Button-1>", lambda e: reset_campi())
    img_chiudi_an = self.icone_gui.get("chiudi")
    btn_chiudi_an = tk.Label(bottom_buttons, compound="left", image=img_chiudi_an, text="Chiudi" if img_chiudi_an else "❌ Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padx=12, pady=6, font=("Arial", 9, "bold"))
    btn_chiudi_an.pack(side="right", padx=10)
    btn_chiudi_an.bind("<Button-1>", lambda e: popup.destroy())
    popup.bind("<Escape>", lambda e: popup.destroy())

def cancella_categorie_checkbox(self, popup):
    selezionate = [cat for cat, var in self.checkbox_vars.items() if var.get()]
    if not selezionate:
        self.show_custom_warning("Attenzione", "Seleziona almeno una categoria da cancellare.")
        return
    MAX_MOSTRATE = 6
    if len(selezionate) > MAX_MOSTRATE:
        elenco = "\n".join(f"• {c}" for c in selezionate[:MAX_MOSTRATE])
        elenco += f"\n… e altre {len(selezionate) - MAX_MOSTRATE} categorie"
    else:
        elenco = "\n".join(f"• {c}" for c in selezionate)
    testo_conferma = "Sei sicuro di voler cancellare le seguenti categorie?\n\n" + elenco
    conferma = self.show_custom_askyesno("Elimina", testo_conferma)
    if not conferma:
        return
    for cat in selezionate:
        if cat in self.categorie:
            self.categorie.remove(cat)
        if cat in self.categorie_tipi:
            del self.categorie_tipi[cat]
        if cat in self.budget_categorie:
            del self.budget_categorie[cat]
        for giorno in list(self.spese.keys()):
            nuove_spese = []
            for voce in self.spese[giorno]:
                voce_cat = campo(voce, "categoria", "")
                if voce_cat == cat:
                     if not self.elimina_spese_var.get():
                         nuove_spese.append(
                             voce.sostituisci(categoria=self.CATEGORIA_RIMOSSA)
                         )
                else:
                    nuove_spese.append(voce)
            self.spese[giorno] = nuove_spese
    self.show_custom_warning("Rimosse", f"✓ {len(selezionate)} categorie sono state cancellate.")
    popup.destroy()
    self.save_db()
    self.refresh_gui()
    self.aggiorna_combobox_categorie()

# Finestra Aggiunta Categorie Suggerite
def apri_categorie_suggerite(self, parent=None):
    CATEGORIE_SUGGERITE = [
            "Abbigliamento", "Abbonamenti digitali", "Affitto Immobile", 
            "Alimentari & Consumi", "Animali Domestici", "Arredamento", 
            "Asporto / Fast food", "Assicurazione Immobile", "Assicurazione Veicoli", 
            "Bollette & Abbonamenti", "Bollo Auto", "Caldaia", "Carburante", "Casa", 
            "Cinema / Eventi", "Colazioni / Caffè fuori", "Commercialista", 
            "Computer", "Conto Corrente", "Corsi / Formazione", "Dentista", 
            "Emergenze", "Entrate Extra", "Farmaci", "Finanza & Risparmio", 
            "Istruzione & Lavoro", "Libri / Materiali", "Manutenzione Auto", 
            "Manutenzione casa", "Mutuo Immobile", "Palestra / Fitness", 
            "Parrucchiere / Estetica", "Pellet", "Pensione", "Pranzi / Ristoranti", 
            "Pulizie Domestiche", "Rate / Finanziamenti", "Regali", 
            "Riparazioni Impreviste", "Salute & Benessere", "Servizi Cloud / Backup", 
            "Software", "Spesa Discount", "Spesa supermercato", "Spese non Ricorrenti", 
            "Stipendio", "Streaming (Netflix, Prime...)", "Tabacchi", 
            "Tassa Rifiuti", "Taxi / Car sharing", "Telefonia / Cellulari", 
            "Telefonia / Internet", "Tempo libero & Spese personali", 
            "Trasporti pubblici", "Uscite Straordinarie", "Utenze (Acqua)", 
            "Utenze (Gas)", "Utenze (Luce)", "Utenze professionali / Partita IVA", 
            "Veicoli & Trasporti", "Videogiochi", "Visite Mediche", "Wellness / Spa"
    ]
    TIPO_SUGGERITI = {cat: ("Entrata" if any(x in cat for x in ["Stipendio", "Pensione", "Extra"]) else "Uscita") for cat in CATEGORIE_SUGGERITE}
    def esegui_import_interna(event=None):
        aggiunte = 0
        gia_presenti = 0
        for nome_p, var in selezioni.items():
            if var.get():
                if nome_p not in self.categorie:
                    tipo = TIPO_SUGGERITI.get(nome_p, "Uscita")
                    self.categorie.append(nome_p)
                    self.categorie_tipi[nome_p] = tipo
                    aggiunte += 1
                else:
                    gia_presenti += 1
        if aggiunte == 0:
            if gia_presenti > 0:
                self.show_custom_warning("Attenzione", "Le categorie selezionate sono già presenti nel tuo database.")
            else:
                self.show_custom_warning("Nessuna Selezione", "Seleziona almeno una categoria da importare per procedere.")
            return
        self.categorie.sort()
        if hasattr(self, 'aggiorna_combobox_categorie'): self.aggiorna_combobox_categorie()
        self.save_db()
        self.show_toast(f"Successo! Aggiunte {aggiunte} categorie.")
        self.update_idletasks()
        finestra.destroy()
    finestra = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    finestra.transient(parent or self)
    finestra.title("Importa Categorie")
    larghezza, altezza = 580, 620
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (larghezza // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (altezza // 2)
    finestra.geometry(f"{larghezza}x{altezza}+{x}+{y}") 
    finestra.minsize(larghezza, altezza)       
    finestra.update_idletasks()
    finestra.wait_visibility()
    try:
        finestra.grab_set()
        finestra.focus_force()
    except: pass
    container = tk.Frame(finestra, bg=self.COLOR_TOPLEVEL)
    container.pack(padx=20, pady=5, fill="both", expand=True)
    canvas = tk.Canvas(container, bg=self.COLOR_TOPLEVEL, highlightthickness=0)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    scroll_frame = tk.Frame(canvas, bg=self.COLOR_TOPLEVEL)
    canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    def _on_mousewheel(event):
        try:
            if canvas and canvas.winfo_exists():
                delta = getattr(event, 'delta', 0)
                num = getattr(event, 'num', 0)          
                if num == 4 or delta > 0:
                     canvas.yview_scroll(-1, "units")
                elif num == 5 or delta < 0:
                     canvas.yview_scroll(1, "units")
        except (tk.TclError, NameError, AttributeError):
                    pass
    finestra.bind("<MouseWheel>", _on_mousewheel)
    finestra.bind("<Button-4>", _on_mousewheel)
    finestra.bind("<Button-5>", _on_mousewheel)
    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
    selezioni = {}
    toggle_var = tk.BooleanVar()
    def toggle_all():
        for v in selezioni.values(): v.set(toggle_var.get())
    f_toggle = tk.Frame(scroll_frame, bg=self.COLOR_TOPLEVEL)
    f_toggle.pack(anchor="w", padx=10, pady=10)
    tk.Checkbutton(f_toggle, variable=toggle_var, command=toggle_all,
                   bg=self.COLOR_TOPLEVEL,
                   fg=self.COLOR_BLACK,
                   selectcolor=self.COLOR_WHITE,
                   activebackground=self.COLOR_TOPLEVEL,
                   highlightthickness=0,
                   bd=0).pack(side="left")
    tk.Label(f_toggle, text=" Seleziona Tutto/Nessuno",
             bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR,
             font=("Arial", 10, "bold italic")).pack(side="left")
    lista_home = ["Casa", "Affitto", "Mutuo", "Immobile", "Arredamento", "Pulizie", "Tassa", "Pellet", "Caldaia", "Utenze", "Bollette", "Consumi"]
    lista_lavoro1 = ["Ristoranti", "Pranzi", "Asporto", "Colazioni"]
    lista_icc = ["Stipendio", "Pensione", "Extra", "Corrente", "Finanza", "Commercialista"]
    lista_salute = ["Salute", "Farmaci", "Mediche", "Dentista"]
    lista_fitness = ["Palestra", "Wellness"]
    lista_mobile = ["Telefonia", "Internet", "Cellulari"]
    lista_bus = ["Trasporti", "Taxi", "Bollo", "Auto", "Veicoli", "Carburante"]
    lista_cinema = ["Cinema", "Videogiochi", "Eventi"]
    lista_beauty = ["Parrucchiere", "Estetica"]
    lista_cloud = ["Cloud", "Streaming", "Abbonamenti"]
    lista_studio = ["Libri", "Corsi"]
    lista_lavoro2 = ["Software", "Lavoro", "IVA"]
    lista_alert = ["Emergenze", "Straordinarie", "Impreviste"]
    for nome_p in CATEGORIE_SUGGERITE:
        var = tk.BooleanVar()
        tipo = TIPO_SUGGERITI[nome_p]
        icona_key = "home" if any(x in nome_p for x in lista_home) else \
                    "spesa" if "Spesa" in nome_p else \
                    "lavoro" if any(x in nome_p for x in lista_lavoro1) else \
                    "icc" if any(x in nome_p for x in lista_icc) else \
                    "salute" if any(x in nome_p for x in lista_salute) else \
                    "fitness" if any(x in nome_p for x in lista_fitness) else \
                    "mobile" if any(x in nome_p for x in lista_mobile) else \
                    "bus" if any(x in nome_p for x in lista_bus) else \
                    "regalo" if "Regali" in nome_p else \
                    "cinema" if any(x in nome_p for x in lista_cinema) else \
                    "vestiti" if "Abbigliamento" in nome_p else \
                    "beauty" if any(x in nome_p for x in lista_beauty) else \
                    "aereo" if "Viaggi" in nome_p else \
                    "cloud" if any(x in nome_p for x in lista_cloud) else \
                    "studio" if any(x in nome_p for x in lista_studio) else \
                    "lavoro" if any(x in nome_p for x in lista_lavoro2) else \
                    "alert" if any(x in nome_p for x in lista_alert) else "tools"
        img_png = self.icone_gui.get(icona_key)
        f_riga = tk.Frame(scroll_frame, bg=self.COLOR_TOPLEVEL)
        f_riga.pack(fill="x", pady=1)
        chk = tk.Checkbutton(f_riga, variable=var, bg=self.COLOR_TOPLEVEL, 
                             selectcolor=self.COLOR_WHITE, activebackground=self.COLOR_TOPLEVEL, 
                             highlightthickness=0, bd=0)
        chk.pack(side="left", padx=(5, 0))
        if img_png:
            lbl_i = tk.Label(f_riga, image=img_png, bg=self.COLOR_TOPLEVEL)
            lbl_i.image = img_png
            lbl_i.pack(side="left", padx=5)
        tk.Label(f_riga, text=nome_p, bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR, font=("Arial", 10)).pack(side="left", padx=5)            
        color_t = "#98C379" if tipo == "Entrata" else "#E06C75"
        tk.Label(f_riga, text=f"({tipo})", bg=self.COLOR_TOPLEVEL, fg=color_t, font=("Arial", 8, "italic")).pack(side="right", padx=15)            
        selezioni[nome_p] = var
    btn_f = tk.Frame(finestra, bg=self.COLOR_TOPLEVEL)
    btn_f.pack(pady=20)
    b_add = tk.Label(btn_f, text=" Aggiungi", image=self.icone_gui.get("aggiungi"), compound="left",
                     bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR, font=("Arial", 9, "bold"),
                     cursor="hand2", padx=20, pady=8)
    b_add.pack(side="left", padx=10)
    b_add.bind("<Button-1>", esegui_import_interna)        
    b_cls = tk.Label(btn_f, text=" Chiudi", image=self.icone_gui.get("chiudi"), compound="left",
                     bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR, font=("Arial", 9, "bold"),
                     cursor="hand2", padx=20, pady=8)
    b_cls.pack(side="left", padx=10)
    b_cls.bind("<Button-1>", lambda e: finestra.destroy())

def get_dati_categorie_storiche_json(self):
    spese_per_categoria = {}
    for giorno, voci in self.spese.items():
            for voce in voci:
                    if campo(voce, "tipo", "") == "Uscita":
                            categoria = campo(voce, "categoria", "")
                            importo = campo(voce, "importo", 0.0)
                            spese_per_categoria[categoria] = spese_per_categoria.get(categoria, 0.0) + importo
    if not spese_per_categoria:
            return '{"labels": ["N/D"], "datasets": [{"data": [1], "backgroundColor": ["#ccc"], "label": "Dati non disponibili"}]}'
    sorted_categorie = sorted(spese_per_categoria.keys())
    labels = sorted_categorie
    data = [spese_per_categoria[cat] for cat in sorted_categorie]
    colori_predefiniti = [
            "#3e95cd", "#8e5ea2", "#3cba9f", "#e8c3b9", "#c45850",
            "#ff6384", "#36a2eb", "#ffce56", "#4bc0c0", "#9966ff",
            "#ff9f40", "#ff6384", "#63b5ff", "#c9cbcf", "#e7e9ed"
    ]
    background_colors = [colori_predefiniti[i % len(colori_predefiniti)] for i in range(len(labels))]
    chart_data = {
            "labels": labels,
            "datasets": [{
                    "data": data,
                    "backgroundColor": background_colors,
                    "label": "Spese Storiche"
            }]
    }
    return json.dumps(chart_data)

def get_dati_categorie_json(self):
    oggi = datetime.date.today()
    anno_corrente = oggi.year
    spese_per_categoria = {}
    for data, entries in self.spese.items():
        if data.year == anno_corrente:
            for entry in entries:
                if campo(entry, "tipo", "") == "Uscita":
                    categoria = campo(entry, "categoria", "")
                    importo = campo(entry, "importo", 0.0)
                    spese_per_categoria[categoria] = spese_per_categoria.get(categoria, 0.0) + importo
    labels = list(spese_per_categoria.keys())
    spese = [round(v, 2) for v in spese_per_categoria.values()]
    colori = ['#' + ''.join([random.choice('0123456789ABCDEF') for j in range(6)]) for i in range(len(labels))]
    dati = {
        'labels': labels,
        'datasets': [{
            'data': spese,
            'backgroundColor': colori,
            'hoverOffset': 4
        }]
    }
    return json.dumps(dati)

def mostra_editor_memoria_categorie(self, event=None):
    import json, os
    def carica():
        if os.path.exists(_app.MEM_CAT):
            with open(_app.MEM_CAT, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    def salva(dati):
        with open(_app.MEM_CAT, "w", encoding="utf-8") as f:
            json.dump(dati, f, indent=2, ensure_ascii=False)
    popup = tk.Toplevel(bg=self.COLOR_TOPLEVEL)
    popup.withdraw()
    popup.title("Editor Memoria Categorie")
    popup.resizable(True, True)
    def centra_finestra():
        w, h = 1300, 600
        sw = popup.winfo_screenwidth()
        sh = popup.winfo_screenheight()
        popup.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        popup.minsize(w, h)
        popup.deiconify()
        popup.lift()
        popup.focus_force()
    popup.after(0, centra_finestra)
    popup.bind("<Escape>", lambda e: popup.destroy())
    frame_top = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    frame_top.pack(fill="x", padx=10, pady=(8, 2))
    tk.Label(frame_top, text="Descrizione", font=("Arial", 9, "bold"),
             bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR, width=70, anchor="w").pack(side="left", padx=(4, 0))
    tk.Label(frame_top, text="Categoria", font=("Arial", 9, "bold"),
             bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR, width=20, anchor="w").pack(side="left")
    ttk.Separator(popup, orient="horizontal").pack(fill="x", padx=10, pady=2)
    frame_tree = ttk.Frame(popup)
    frame_tree.pack(fill="both", expand=True, padx=10, pady=4)
    frame_tree.columnconfigure(0, weight=1)
    frame_tree.rowconfigure(0, weight=1)
    colonne = ("descrizione", "categoria")
    tree = ttk.Treeview(frame_tree, columns=colonne, show="headings", selectmode="browse")
    tree.heading("descrizione", text="Descrizione", anchor="w",
         command=lambda: self.treeview_sort_column(tree, "descrizione", False))
    tree.heading("categoria",   text="Categoria",   anchor="w",
         command=lambda: self.treeview_sort_column(tree, "categoria", False))
    tree.column("descrizione", width=700, minwidth=300, stretch=True,  anchor="w")
    tree.column("categoria",   width=180, minwidth=100, stretch=False, anchor="w")
    sb = ttk.Scrollbar(frame_tree, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.grid(row=0, column=0, sticky="nsew")
    sb.grid(row=0, column=1, sticky="ns")
    frame_cerca = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    frame_cerca.pack(fill="x", padx=10, pady=(0, 2))
    tk.Label(frame_cerca, text="🔍", bg=self.COLOR_TOPLEVEL).pack(side="left")
    cerca_var = tk.StringVar()
    entry_cerca = ttk.Entry(frame_cerca, textvariable=cerca_var, width=50)
    entry_cerca.pack(side="left", padx=4)
    dati = carica()
    def popola(filtro=""):
        tree.delete(*tree.get_children())
        for desc, cat in dati.items():
            if filtro.lower() in desc.lower() or filtro.lower() in cat.lower():
                tree.insert("", "end", values=(desc, cat))
        lbl_count.config(text=f"{len(tree.get_children())} voci")
    cerca_var.trace_add("write", lambda *_: popola(cerca_var.get()))
    def apri_editor(desc_esistente="", cat_esistente=""):
        dlg = tk.Toplevel(popup, bg=self.COLOR_TOPLEVEL)
        dlg.withdraw()
        dlg.title("Modifica voce" if desc_esistente else "Nuova voce")
        dlg.resizable(False, False)
        def centra_dlg():
            dlg.geometry(f"700x160+{popup.winfo_x()+150}+{popup.winfo_y()+200}")
            dlg.deiconify()
            dlg.focus_force()
        dlg.after(0, centra_dlg)
        dlg.bind("<Escape>", lambda e: dlg.destroy())
        tk.Label(dlg, text="Descrizione:", bg=self.COLOR_TOPLEVEL,
                 fg=self.TEXT_COLOR, font=("Arial", 9)).grid(row=0, column=0, padx=10, pady=8, sticky="w")
        var_desc = tk.StringVar(value=desc_esistente)
        entry_desc = ttk.Entry(dlg, textvariable=var_desc, width=70)
        entry_desc.grid(row=0, column=1, padx=10, pady=8, sticky="ew")
        tk.Label(dlg, text="Categoria:", bg=self.COLOR_TOPLEVEL,
                 fg=self.TEXT_COLOR, font=("Arial", 9)).grid(row=1, column=0, padx=10, pady=4, sticky="w")
        categorie_usate = sorted(set(dati.values()) | set(getattr(self, "categorie", [])))
        var_cat = tk.StringVar(value=cat_esistente)
        combo_cat = ttk.Combobox(dlg, textvariable=var_cat, values=categorie_usate, width=25, style="Border.TCombobox")
        combo_cat.grid(row=1, column=1, padx=10, pady=4, sticky="w")
        dlg.columnconfigure(1, weight=1)
        def conferma():
            nuova_desc = var_desc.get().strip()
            nuova_cat  = var_cat.get().strip()
            if not nuova_desc or not nuova_cat:
                self.show_toast("Descrizione e categoria non possono essere vuote.", parent=dlg)
                return
            if desc_esistente and desc_esistente != nuova_desc:
                del dati[desc_esistente]
            dati[nuova_desc] = nuova_cat
            salva(dati)
            self.memoria_descrizioni_categoria = dati
            popola(cerca_var.get())
            dlg.destroy()
            self.show_toast("Voce salvata.")
        frame_btn = tk.Frame(dlg, bg=self.COLOR_TOPLEVEL)
        frame_btn.grid(row=2, column=0, columnspan=2, pady=10)
        img_salva = self.icone_gui.get("salva")
        btn_salva = ttk.Label(frame_btn, compound="left", image=img_salva,
                  text=" Salva" if img_salva else "Salva",
                  background=self.COLOR_TOPLEVEL, foreground=self.TEXT_COLOR,
                  cursor="hand2", padding=(8, 4))
        btn_salva.pack(side=tk.LEFT, padx=8)
        btn_salva.bind("<Button-1>", lambda e: conferma())
        img_annulla = self.icone_gui.get("chiudi")
        btn_annulla = ttk.Label(frame_btn, compound="left", image=img_annulla,
                    text=" Annulla" if img_annulla else "Annulla",
                    background=self.COLOR_TOPLEVEL, foreground=self.TEXT_COLOR,
                    cursor="hand2", padding=(8, 4))
        btn_annulla.pack(side=tk.LEFT, padx=8)
        btn_annulla.bind("<Button-1>", lambda e: dlg.destroy())
        entry_desc.bind("<Return>", lambda e: combo_cat.focus())
        combo_cat.bind("<Return>",  lambda e: conferma())
    def modifica_voce():
        sel = tree.selection()
        if not sel:
            self.show_toast("Seleziona una voce da modificare.", parent=popup)
            return
        desc, cat = tree.item(sel[0], "values")
        apri_editor(desc, cat)
    def elimina_voce():
        sel = tree.selection()
        if not sel:
            self.show_toast("Seleziona una voce da eliminare.", parent=popup)
            return
        desc, _ = tree.item(sel[0], "values")
        desc_breve = desc[:60] + "…" if len(desc) > 60 else desc
        if self.show_custom_askyesno("Conferma eliminazione",
                                     f"Eliminare questa voce?\n\n«{desc_breve}»"):
           del dati[desc]
           salva(dati)
           self.memoria_descrizioni_categoria = dati
           popola(cerca_var.get())
           self.show_toast("Voce eliminata.")
    def elimina_tutte():
        if not dati:
            self.show_toast("La memoria è già vuota.", parent=popup)
            return
        if self.show_custom_askyesno("Conferma pulizia totale",
                                     f"Vuoi eliminare TUTTE le {len(dati)} voci dalla memoria?\n\nQuesta operazione non è reversibile."):
            dati.clear()
            salva(dati)
            self.memoria_descrizioni_categoria = dati
            popola()
            self.show_toast("Memoria categorie svuotata.")
    def nuova_voce():
        apri_editor()
    tree.bind("<Double-1>", lambda e: modifica_voce())
    ttk.Separator(popup, orient="horizontal").pack(fill="x", padx=10, pady=2)
    frame_bottoni = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    frame_bottoni.pack(pady=8, fill="x", padx=10)
    lbl_count = tk.Label(frame_bottoni, text="", bg=self.COLOR_TOPLEVEL,
                         fg=self.TEXT_COLOR, font=("Arial", 9))
    lbl_count.pack(side="left", padx=6)
    popola()
    def _btn(text, icon_key, cmd, fg=None):
        img = self.icone_gui.get(icon_key)
        b = ttk.Label(frame_bottoni, text=f" {text}", image=img, compound="left",
                      cursor="hand2", font=("Arial", 9),
                      background=self.COLOR_WIDGET_BG,
                      foreground=fg or self.TEXT_COLOR)
        b.pack(side="left", padx=8)
        b.bind("<Button-1>", lambda e: cmd())
        return b
    _btn("Nuova",        "nuovo",    nuova_voce)
    _btn("Modifica",     "modifica", modifica_voce)
    _btn("Elimina voce", "delete",   elimina_voce,  fg=self.COLOR_RED)
    _btn("Svuota tutto", "delete",   elimina_tutte, fg=self.COLOR_RED)
    btn_chiudi = ttk.Label(frame_bottoni, text=" Chiudi",
                           image=self.icone_gui.get("chiudi"), compound="left",
                           cursor="hand2", font=("Arial", 9, "bold"),
                           background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR)
    btn_chiudi.pack(side="right", padx=10)
    btn_chiudi.bind("<Button-1>", lambda e: popup.destroy())

def pop_categorie(self): 
    m = tk.Menu(self, tearoff=0, bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT,  
                activebackground=self.MENU_ACT_BG_COLOR, font=("Arial", 9)) 
    self._add_m_item(m, "Analisi Categorie", "timer", self.open_analisi_categoria, "Ctrl+K") 
    self._add_m_item(m, "Suggerisci Categorie", "descrizione", self.apri_categorie_suggerite, "Ctrl+Shift+K") 
    self._add_m_item(m, "Gestione Categorie", "filtri", self.mostra_categorie_popup, "Ctrl+Shift+T") 
    self._add_m_item(m, "Gestione Categorie Bulk", "delete", self.apri_cancella_multiplo, "Ctrl+Shift+S") 
    self._add_m_item(m, "Editor Categorie Estratti", "filtri", self.mostra_editor_memoria_categorie)
    self._mostra_popup(m, 220) 

