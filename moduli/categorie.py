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
from moduli.modello_spesa import campo
from moduli.mappa_conti_trasferimenti import costruisci_mappa_conti_da_trasferimenti, conto_da_mappa

def _fmt_it(v, spec=",.2f"):
    s = format(v, spec)
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def _aggiorna_cat_ricorrenze(self, vecchio, nuovo):
    for r in getattr(self, "ricorrenze", {}).values():
        if isinstance(r, dict) and r.get("cat") == vecchio:
            r["cat"] = nuovo

def _salva_budget_annuo_categoria(self, nome):
    val = self.var_budget_annuo_cat.get().strip().replace(",", ".")
    try:
        val = float(val)
    except ValueError:
        val = 0.0
    if val > 0:
        self.budget_annuale_categorie[nome] = val
    elif nome in self.budget_annuale_categorie:
        del self.budget_annuale_categorie[nome]
    return val


def mostra_categorie_popup(self):
    if hasattr(self, 'categorie_popup') and self.categorie_popup.winfo_exists():
        self.categorie_popup.deiconify()
        self.categorie_popup.lift()
        self.categorie_popup.focus_force()
        self.cat_mod_menu.configure(style="Border.TCombobox")
        self.reset_campi_categoria()
        self.categorie_popup.after(100, self.entry_nuova_cat.focus_set) 
        return
    self.categorie_popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    self.categorie_popup.withdraw()
    self.categorie_popup.transient(self)
    self.categorie_popup.title("Gestione Categorie")
    self.categorie_popup.resizable(False, False)
    window_width = 600
    window_height = 300
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
    aggiungi_cat_frame.columnconfigure(1, weight=0)
    if not hasattr(self, 'classe_categoria'):
        self.classe_categoria = tk.StringVar(value="Nessuna")
    if not hasattr(self, 'conto_risp_cat'):
        self.conto_risp_cat = tk.StringVar(value="(nessuno)")
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
    self.lbl_tipo_cat.grid(row=0, column=2, sticky="e", padx=(28, 4), pady=2)
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
              text=" Classe 50/30/20:",
              background=self.COLOR_WIDGET_BG,
              font=("Arial", 9, "bold")).grid(row=1, column=2, sticky="e", padx=(28, 4), pady=2)
    self.cb_classe_cat = ttk.Combobox(
        aggiungi_cat_frame,
        textvariable=self.classe_categoria,
        values=["Nessuna", "Bisogni", "Desideri", "Risparmio"],
        style="Border.TCombobox",
        state="readonly",
        width=16
    )
    self.cb_classe_cat.grid(row=1, column=3, sticky="w", padx=2, pady=2)
    ttk.Label(aggiungi_cat_frame,
              text=" Conto:",
              font=("Arial", 9, "bold")).grid(row=2, column=2, sticky="e", padx=(28, 4), pady=2)
    _stl = ttk.Style()
    try:
        _base_cb = _stl.lookup("Border.TCombobox", "fieldbackground", ["readonly"]) or self.COLOR_WIDGET_BG
        _fg_cb = _stl.lookup("Border.TCombobox", "foreground", ["readonly"]) or self.TEXT_COLOR
        _btn_cb = _stl.lookup("Border.TCombobox", "background") or self.COLOR_WIDGET_BG
        _arr_cb = _stl.lookup("Border.TCombobox", "arrowcolor", ["!disabled"]) or self.TEXT_COLOR
    except tk.TclError:
        _base_cb, _fg_cb = self.COLOR_WIDGET_BG, self.TEXT_COLOR
        _btn_cb, _arr_cb = self.COLOR_WIDGET_BG, self.TEXT_COLOR
    _stl.configure("ContoRisp.Border.TCombobox")
    _stl.map("ContoRisp.Border.TCombobox",
             fieldbackground=[("disabled", _base_cb), ("readonly", _base_cb), ("!disabled", _base_cb)],
             foreground=[("disabled", _fg_cb), ("readonly", _fg_cb), ("!disabled", _fg_cb)],
             background=[("disabled", _btn_cb), ("!disabled", _btn_cb)],
             arrowcolor=[("disabled", _btn_cb), ("!disabled", _arr_cb)])
    self.cb_conto_risp_cat = ttk.Combobox(
        aggiungi_cat_frame,
        textvariable=self.conto_risp_cat,
        values=["(nessuno)"] + self._nomi_conti_portafoglio(
            solo_risparmio=True, includi=self.conto_risp_cat.get()),
        style="ContoRisp.Border.TCombobox",
        state="readonly",
        width=16
    )
    self.cb_conto_risp_cat.grid(row=2, column=3, sticky="w", padx=2, pady=2)
    def _aggiorna_stato_conto_risp(*_):
        try:
            if self.classe_categoria.get() == "Risparmio":
                self.cb_conto_risp_cat.config(state="readonly")
            else:
                self.conto_risp_cat.set("(nessuno)")
                self.cb_conto_risp_cat.config(state="disabled")
        except tk.TclError:
            pass
    self.classe_categoria.trace_add("write", _aggiorna_stato_conto_risp)
    _aggiorna_stato_conto_risp()
    def _tt_cat(widget, testo):
        import textwrap
        testo_w = textwrap.fill(testo, width=48)
        stato = {"job": None}
        def _chiudi(e=None):
            if stato["job"]:
                try:
                    widget.after_cancel(stato["job"])
                except tk.TclError:
                    pass
                stato["job"] = None
            self.hide_tooltip()
        def _entra(e):
            _chiudi()
            stato["job"] = widget.after(500, lambda ev=e: (stato.update(job=None), self.show_tooltip(ev, testo_w)))
        widget.bind("<Enter>", _entra, add="+")
        widget.bind("<Leave>", _chiudi, add="+")
        widget.bind("<Button-1>", _chiudi, add="+")
        widget.bind("<Destroy>", _chiudi, add="+")
    _tt_cat(self.cb_classe_cat,
            "Classe 50/30/20 della categoria: Bisogni (max 50%), Desideri (max 30%), "
            "Risparmio (min 20%). Decide in quale gruppo contano le uscite di questa categoria nel Metodo 50/30/20.")
    _tt_cat(self.cb_conto_risp_cat,
            "Attivo solo con classe Risparmio. Ogni uscita in questa categoria, registrata con un conto "
            "(es. Luca), diventa un trasferimento da quel conto al conto risparmio scelto qui. "
            "Premi Aggiungi o Modifica per salvare.")
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
              font=("Arial", 9, "bold")).grid(row=2, column=0, sticky="e", padx=4, pady=2)
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
            self.var_budget_cat.set(f"{float(val):.2f}".replace(".", ","))
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
        self.var_budget_cat.set(f"{float(self.var_budget_cat.get().strip().replace(',', '.')):.2f}".replace(".", ","))
        if self.var_budget_cat.get().strip() else None
    ])
    self.entry_budget_cat.grid(row=2, column=1, sticky="w", padx=2, pady=2)

    ttk.Label(aggiungi_cat_frame,
              text=" Budget €/anno:",
              font=("Arial", 9, "bold")).grid(row=3, column=0, sticky="e", padx=4, pady=2)
    self.entry_budget_annuo_cat = ttk.Entry(
        aggiungi_cat_frame,
        textvariable=self.var_budget_annuo_cat,
        width=10,
        validate="key",
        validatecommand=(vcmd_budget, "%P")
    )
    self.entry_budget_annuo_cat.bind("<FocusOut>", lambda e: [
        self.var_budget_annuo_cat.set(f"{float(self.var_budget_annuo_cat.get().strip().replace(',', '.')):.2f}".replace(".", ","))
        if self.var_budget_annuo_cat.get().strip() else None
    ])
    self.entry_budget_annuo_cat.grid(row=3, column=1, sticky="w", padx=2, pady=2)

    def _crea_btn_cat(parent, attr, icona, testo, comando):
        btn = ttk.Label(
            parent, image=self.icone_gui.get(icona),
            text=testo, compound="left", cursor="hand2",
            background=self.COLOR_WIDGET_BG, font=("Arial", 9, "bold")
        )
        btn.image = self.icone_gui.get(icona)
        btn.pack(side="left", padx=6)
        btn.bind("<Button-1>", lambda e: comando())
        setattr(self, attr, btn)
        return btn
    btn_frame_cat = ttk.Frame(aggiungi_cat_frame)
    btn_frame_cat.grid(row=4, column=0, columnspan=4, pady=(18, 4), sticky="")
    _crea_btn_cat(btn_frame_cat, "btn_add_cat", "check", " Aggiungi", lambda: self.add_categoria())
    _crea_btn_cat(btn_frame_cat, "btn_modifica_cat", "descrizione", " Salva", lambda: self.modifica_categoria())
    _crea_btn_cat(btn_frame_cat, "btn_cancella_cat", "delete", " Cancella", lambda: self.cancella_categoria())
    _crea_btn_cat(btn_frame_cat, "btn_reset_cat", "reset", " Reset", lambda: self.reset_campi_categoria())
    fr_strumenti = ttk.Frame(aggiungi_cat_frame)
    fr_strumenti.grid(row=6, column=0, columnspan=4, pady=(4, 8), sticky="")
    _crea_btn_cat(fr_strumenti, "btn_cat_avanzate", "documenti", " Editor", lambda: apri_gestione_categorie(self))
    _crea_btn_cat(fr_strumenti, "btn_analisi_cat", "timer", " Analisi",
                  lambda: self.analisi_categorie(self.cat_mod_sel.get() or None))
    fr_strumenti.grid_remove()
    fr_toggle = ttk.Frame(aggiungi_cat_frame)
    fr_toggle.grid(row=5, column=0, columnspan=4, pady=(2, 0), sticky="")
    stato_strumenti = {"aperto": False}
    def _ridimensiona_popup():
        self.categorie_popup.update_idletasks()
        w = max(self.categorie_popup.winfo_width(), self.categorie_popup.winfo_reqwidth())
        h = self.categorie_popup.winfo_reqheight()
        self.categorie_popup.geometry(f"{w}x{h}")
    def _toggle_strumenti(event=None):
        stato_strumenti["aperto"] = not stato_strumenti["aperto"]
        if stato_strumenti["aperto"]:
            fr_strumenti.grid()
        else:
            fr_strumenti.grid_remove()
        lbl_freccia_str.config(text="▼" if stato_strumenti["aperto"] else "▶")
        _ridimensiona_popup()
    lbl_freccia_str = tk.Label(
        fr_toggle, text="▶", font=("Arial", 9, "bold"),
        bg=self.COLOR_WIDGET_BG, fg="red", cursor="hand2"
    )
    lbl_freccia_str.pack(side="left")
    lbl_testo_str = ttk.Label(
        fr_toggle, text=" Strumenti", cursor="hand2",
        background=self.COLOR_WIDGET_BG, font=("Arial", 9, "bold")
    )
    lbl_testo_str.pack(side="left")
    for _w_str in (lbl_freccia_str, lbl_testo_str):
        _w_str.bind("<Button-1>", _toggle_strumenti)
        _tt_cat(_w_str, "Clic: mostra o nascondi gli strumenti delle categorie "
                        "(editor categorie: elenco, dettagli, cancellazione multipla, suggerite; analisi).")
    self.btn_chiudi_popup_cat = ttk.Label(
        main_frame, image=self.icone_gui.get("chiudi"),
        text=" Chiudi", compound="left", cursor="hand2", background=self.COLOR_WIDGET_BG, font=("Arial", 9, "bold")
    )
    self.btn_chiudi_popup_cat.image = self.icone_gui.get("chiudi")
    self.btn_chiudi_popup_cat.pack(side="bottom", pady=(0, 10))
    self.btn_chiudi_popup_cat.bind("<Button-1>", lambda e: self.categorie_popup.withdraw())
    for _w in aggiungi_cat_frame.winfo_children():
        if _w.grid_info().get("row") in (0, 1, 2, 3):
            _w.grid_configure(pady=5)
    self.aggiorna_combobox_categorie()
    self.reset_campi_categoria()
    if not self.categorie:
        self.cat_mod_menu['state'] = 'disabled'
    self.categorie_popup.update_idletasks()
    window_width = max(560, self.categorie_popup.winfo_reqwidth())
    window_height = self.categorie_popup.winfo_reqheight()
    center_x = int(screen_width / 2 - window_width / 2)
    center_y = int(screen_height / 2 - window_height / 2)
    self.categorie_popup.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    self.categorie_popup.deiconify()

def _aggiorna_stile_pulsante_tipo_popup(self):
    tipo = self.tipo_categoria.get()
    btn_style = 'GreenOutline.TButton' if tipo == "Entrata" else 'RedOutline.TButton'
    for nome_b in ("btn_gestisci_tipo", "ed_btn_tipo"):
        b = getattr(self, nome_b, None)
        if b is not None:
            try:
                b.config(text=tipo, style=btn_style)
            except tk.TclError:
                pass

def _classi_categorie(self):
    if not hasattr(self, "categorie_classi"):
        self.categorie_classi = dict(getattr(self, "db", {}).get("categorie_classi", {}))
    return self.categorie_classi

def _etichetta_classe_conto(self, entry):
    classe = self._classi_categorie().get(campo(entry, "categoria", ""), "")
    conto = self._conto_effettivo(entry)
    return " · ".join(p for p in (classe, conto) if p)

def _suffisso_conto_risp(self, nome):
    if self._classi_categorie().get(nome) != "Risparmio":
        return ""
    n = self._nome_conto_risparmio_cat(nome)
    return f" Conto risparmio: {n}." if n and n != "(nessuno)" else ""

def _salva_classe_categoria(self, nome):
    classi = self._classi_categorie()
    classe = self.classe_categoria.get()
    if classe in ("Bisogni", "Desideri", "Risparmio"):
        classi[nome] = classe
    else:
        classi.pop(nome, None)
    self._salva_conto_risparmio_categoria(nome)

def on_categoria_modifica_changed_popup(self):
    nome = self.cat_mod_sel.get()
    tipo = self.categorie_tipi.get(nome, "Uscita")
    self.nuova_cat.set(nome)
    self.tipo_categoria.set(tipo)
    self._aggiorna_stile_pulsante_tipo_popup()
    self.classe_categoria.set(self._classi_categorie().get(nome, "Nessuna"))
    _cb_conto = getattr(self, 'cb_conto_risp_cat', None)
    try:
        if _cb_conto is not None and _cb_conto.winfo_exists():
            _cb_conto['values'] = ["(nessuno)"] + self._nomi_conti_portafoglio(
                solo_risparmio=True, includi=self._nome_conto_risparmio_cat(nome))
    except tk.TclError:
        pass
    self.conto_risp_cat.set(self._nome_conto_risparmio_cat(nome))
    budget = self.budget_categorie.get(self.cat_mod_sel.get(), 0)
    self.var_budget_cat.set(f"{budget:.2f}".replace(".", ",") if budget > 0 else "")
    budget_annuo = self.budget_annuale_categorie.get(self.cat_mod_sel.get(), 0)
    self.var_budget_annuo_cat.set(f"{budget_annuo:.2f}".replace(".", ",") if budget_annuo > 0 else "")

def on_categoria_modifica_changed(self):
    nome = self.cat_mod_sel.get()
    tipo = self.categorie_tipi.get(nome, "Uscita")
    self.nuova_cat.set(nome)  
    self.tipo_categoria.set(tipo)

def reset_campi_categoria(self):
    try:
        f_prima = self.focus_get()
    except Exception:
        f_prima = None
    self.nuova_cat.set("")                          
    self.cat_mod_sel.set("")                        
    self.tipo_categoria.set("Uscita")    
    self._aggiorna_stile_pulsante_tipo_popup()
    if hasattr(self, 'classe_categoria'):
        self.classe_categoria.set("Nessuna")
    if hasattr(self, 'conto_risp_cat'):
        self.conto_risp_cat.set("(nessuno)")
    self.var_budget_cat.set("")
    self.var_budget_annuo_cat.set("")
    _aggiorna_albero_cat_avanz(self)
    if hasattr(self, 'entry_nuova_cat') and self.entry_nuova_cat.winfo_exists():
        self.entry_nuova_cat.focus_set()           
    ed = getattr(self, 'ed_entry_nome', None)
    if ed is not None and ed.winfo_exists() and f_prima is not None and str(f_prima).startswith(str(self.cat_av_popup)):
        ed.focus_set()

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
            except Exception:
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
        except Exception: pass
    if hasattr(self, 'cat_mod_menu') and self.cat_mod_menu.winfo_exists():
        self.cat_mod_menu["values"] = self.categorie
        try:
            if "Generica" in self.categorie:
                idx = self.categorie.index("Generica")
                self.cat_mod_menu.current(idx)
            elif self.categorie:
                self.cat_mod_menu.current(0)
        except Exception: pass
    _aggiorna_albero_cat_avanz(self)

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

def mostra_tutte_le_categorie(self):
    apri_gestione_categorie(self, tab="elenco")

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
    self._salva_classe_categoria(nome)
    self.aggiorna_combobox_categorie()
    try:
        budget_val = float(self.var_budget_cat.get().strip().replace(",", "."))
    except ValueError:
        budget_val = 0.0

    if budget_val > 0:
        self.budget_categorie[nome] = budget_val
    elif nome in self.budget_categorie:
        del self.budget_categorie[nome]
    try:
        budget_anno_val = float(self.var_budget_annuo_cat.get().strip().replace(",", "."))
    except ValueError:
        budget_anno_val = 0.0
    self._salva_budget_annuo_categoria(nome)
    self.save_db()
    self.refresh_gui()
    self.reset_campi_categoria()
    if hasattr(self, 'ricorrenza_popup') and self.ricorrenza_popup.winfo_exists():
        if hasattr(self, 'ric_cat_menu'):
                self.ric_cat_menu['values'] = sorted(self.categorie)

    self.show_toast((
        f"Categoria '{nome}' ({tipo}) aggiunta. Budget Mese: € {_fmt_it(budget_val)} — Anno: € {_fmt_it(budget_anno_val)}"
        if (budget_val > 0 or budget_anno_val > 0)
        else f"Categoria '{nome}' ({tipo}) aggiunta."
    ) + _suffisso_conto_risp(self, nome))

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
    if old_nome == self.CATEGORIA_RIMOSSA and new_nome != old_nome:
        self.show_toast(f"La categoria '{self.CATEGORIA_RIMOSSA}' non può essere rinominata.")
        self.reset_campi_categoria()
        return
    if new_nome == old_nome:
        tipo = self.tipo_categoria.get()
        self.categorie_tipi[new_nome] = tipo
        self._salva_classe_categoria(new_nome)
        budget_val = self.var_budget_cat.get().strip().replace(",", ".")
        try:
            budget_val = float(budget_val)
        except ValueError:
            budget_val = 0.0
        if budget_val > 0:
            self.budget_categorie[new_nome] = budget_val
        elif new_nome in self.budget_categorie:
            del self.budget_categorie[new_nome]
        self._salva_budget_annuo_categoria(new_nome)
        budget_anno_val = self.budget_annuale_categorie.get(new_nome, 0.0)
        self.save_db()
        self.refresh_gui()
        self.show_toast((
                f"Tipo '{new_nome}' aggiornato a '{tipo}'. Budget Mese: € {_fmt_it(budget_val)} — Anno: € {_fmt_it(budget_anno_val)}"
                if (budget_val > 0 or budget_anno_val > 0)
               else f"Tipo '{new_nome}' aggiornato a '{tipo}'."
        ) + _suffisso_conto_risp(self, new_nome))
        self.reset_campi_categoria()
        return
    if new_nome in self.categorie:
        self.show_toast("Esiste già una categoria con questo nome.")
        return
    idx = self.categorie.index(old_nome)
    self.categorie[idx] = new_nome
    nuovo_tipo = self.tipo_categoria.get()
    self.categorie_tipi[new_nome] = nuovo_tipo
    self._salva_classe_categoria(new_nome)
    if new_nome != old_nome:
        self.categorie_tipi.pop(old_nome, None)
        self._classi_categorie().pop(old_nome, None)
        self._conti_risparmio_cat().pop(old_nome, None)
        _aggiorna_cat_ricorrenze(self, old_nome, new_nome)
    for d in self.spese:
        new_entries = []
        for entry in self.spese[d]:
            if campo(entry, "categoria", "") == old_nome:
                entry = entry.sostituisci(categoria=new_nome)
            new_entries.append(entry)
        self.spese[d] = new_entries
    for _cb in (getattr(self, 'cat_menu', None), getattr(self, 'cat_mod_menu', None)):
        try:
            if _cb is not None and _cb.winfo_exists():
                _cb["values"] = self.categorie
        except tk.TclError:
            pass
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
    self._salva_budget_annuo_categoria(new_nome)
    if old_nome != new_nome and old_nome in self.budget_annuale_categorie:
        del self.budget_annuale_categorie[old_nome]
    self.save_db()
    self.refresh_gui()
    self.show_toast((f"Categoria '{old_nome}' rinominata in '{new_nome}' ({nuovo_tipo}). Budget: € {_fmt_it(budget_val)}" if budget_val > 0 else f"Categoria '{old_nome}' rinominata in '{new_nome}' ({nuovo_tipo}).") + _suffisso_conto_risp(self, new_nome))
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
    if cat in self.budget_annuale_categorie:
        del self.budget_annuale_categorie[cat]
    self._classi_categorie().pop(cat, None)
    self._conti_risparmio_cat().pop(cat, None)
    _aggiorna_cat_ricorrenze(self, cat, self.CATEGORIA_RIMOSSA)
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
            c.create_rectangle(
                    bx, y - 10, bx + max(bar_w_ok, 4), y + 10,
                    fill=fill, outline="", tags=tag_riga
            )
            c.create_rectangle(
                    bx + max(bar_w_ok, 4), y - 10,
                    bx + max(bar_w_ok, 4) + bar_w_ovr, y + 10,
                    fill="#E5A550", outline="", tags=tag_riga
            )
        else:
            c.create_rectangle(
                    bx, y - 10, bx + max(bar_w, 4), y + 10,
                    fill=fill, outline="", tags=tag_riga
            )
        x_fine_barra = bx + max(bar_w, 4)
        segno_val = "+" if val >= 0 else ""
        if x_fine_barra > (w - 60): 
                    c.create_text(x_fine_barra - 5, y, text=f"{segno_val}{_fmt_it(val)} €", anchor="e",
                                  fill="white", font=("Arial", 8, "bold"), tags=tag_riga)
        else:
                    c.create_text(x_fine_barra + 5, y, text=f"{segno_val}{_fmt_it(val)} €", anchor="w",
                                  fill=self.TEXT_COLOR, font=("Arial", 8, "bold"), tags=tag_riga)
        voci = sorted(dettagli.get(cat, []), key=lambda x: x[0], reverse=True)
        tot_usc = sum(iv for _, iv, tv in voci if tv == "Uscita")
        tot_ent = sum(iv for _, iv, tv in voci if tv == "Entrata")
        w_l = 13
        w_v = 12
        righe_dati = [
                    f"{'[-] USCITE:':<{w_l}} {'-' + f'{_fmt_it(tot_usc)}':>{w_v}} €",
                    f"{'[+] ENTRATE:':<{w_l}} {'+' + f'{_fmt_it(tot_ent)}':>{w_v}} €",
                    f"{'[=] NETTO:':<{w_l}} {('+' if tot_ent-tot_usc >= 0 else '') + f'{_fmt_it(tot_ent-tot_usc)}':>{w_v}} €",
        ]
        voci_righe = []
        for d_v, imp_v, tipo_v in voci[:15]:
                    p = "-" if tipo_v == "Uscita" else "+"
                    s = "»" if tipo_v == "Uscita" else "«"
                    dt = d_v.strftime('%d/%m')
                    sinistra = f"{s} {dt}"
                    destra = f"{p + f'{_fmt_it(imp_v)}':>{w_v}} €"
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
    colore_saldo = self.COLOR_GREEN_SMOOTH if saldo >= 0 else self.COLOR_RED_SMOOTH
    frm_riepilogo = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    frm_riepilogo.pack(pady=(0, 2))
    tk.Label(frm_riepilogo, text="  Entrate: ", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 8)).pack(side="left")
    tk.Label(frm_riepilogo, text=f"+{_fmt_it(totale_ent)} €", bg=self.COLOR_TOPLEVEL,
             fg=self.COLOR_GREEN_SMOOTH, font=("Arial", 8, "bold")).pack(side="left")
    tk.Label(frm_riepilogo, text="   Uscite: ", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 8)).pack(side="left")
    tk.Label(frm_riepilogo, text=f"-{_fmt_it(totale_usc)} €", bg=self.COLOR_TOPLEVEL,
             fg=self.COLOR_RED_SMOOTH, font=("Arial", 8, "bold")).pack(side="left")
    tk.Label(frm_riepilogo, text="   Saldo: ", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 8)).pack(side="left")
    tk.Label(frm_riepilogo, text=f"{segno_saldo}{_fmt_it(saldo)} €", bg=self.COLOR_TOPLEVEL,
             fg=colore_saldo, font=("Arial", 8, "bold")).pack(side="left")
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
                segno_mese = "+" if val >= 0 else ""
                c.create_text((x1+x2)/2, y1 - 10, text=f"{segno_mese}{_fmt_it(val, ',.0f')}",
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
def _ottieni_categorie_ricorrenti_mancanti(self):
    from datetime import datetime
    oggi = datetime.today().date()
    def converti_data(d):
        if isinstance(d, str):
            try: return datetime.strptime(d, "%d-%m-%Y").date()
            except Exception: return None
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

def cancella_categorie_checkbox(self, popup=None):
    cancella_categorie_selezionate(self)

def apri_categorie_suggerite(self, parent=None):
    apri_gestione_categorie(self, tab="suggerite")

def apri_gestione_categorie(self, event=None, tab=None):
    if hasattr(self, 'cat_av_popup') and self.cat_av_popup.winfo_exists():
        self.cat_av_popup.deiconify()
        self.cat_av_popup.lift()
        self.cat_av_popup.focus_force()
        self.cat_av_elimina_var.set(False)
        for v in self.cat_av_vars.values():
            v.set(False)
        self.reset_campi_categoria()
        self.nb_cat_av.select(self.tab_cat_av_sugg if tab == "suggerite" else self.tab_cat_av_elenco)
        return
    popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    self.cat_av_popup = popup
    popup.withdraw()
    popup.transient(self)
    popup.title("Editor Categorie")
    popup.resizable(True, True)
    larghezza, altezza = 1180, 600
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (larghezza // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (altezza // 2)
    popup.geometry(f"{larghezza}x{altezza}+{max(0, x)}+{max(0, y)}")
    popup.minsize(larghezza, altezza)
    popup.bind("<Escape>", lambda e: popup.destroy())
    if not hasattr(self, 'classe_categoria'):
        self.classe_categoria = tk.StringVar(value="Nessuna")
    if not hasattr(self, 'conto_risp_cat'):
        self.conto_risp_cat = tk.StringVar(value="(nessuno)")
    if not hasattr(self, 'nuova_cat'):
        self.nuova_cat = tk.StringVar()
        self.cat_mod_sel = tk.StringVar(value=self.categorie[0] if self.categorie else "")
        self.tipo_categoria = tk.StringVar(value="Uscita")
    self.cat_av_elimina_var = tk.BooleanVar(value=False)
    self.cat_av_vars = {}
    self.cat_av_rows = {}
    self.var_filtro_cat_av = tk.StringVar()
    btn_chiudi = ttk.Label(popup, image=self.icone_gui.get("chiudi"), text=" Chiudi", compound="left",
                           cursor="hand2", background=self.COLOR_WIDGET_BG, font=("Arial", 9, "bold"))
    btn_chiudi.image = self.icone_gui.get("chiudi")
    btn_chiudi.pack(side="bottom", pady=(4, 10))
    btn_chiudi.bind("<Button-1>", lambda e: popup.destroy())
    self.nb_cat_av = ttk.Notebook(popup)
    self.nb_cat_av.pack(fill="both", expand=True, padx=10, pady=10)
    self.tab_cat_av_elenco = ttk.Frame(self.nb_cat_av)
    self.tab_cat_av_sugg = ttk.Frame(self.nb_cat_av)
    self.nb_cat_av.add(self.tab_cat_av_elenco, text="  Categorie  ")
    self.nb_cat_av.add(self.tab_cat_av_sugg, text="  Suggerite  ")
    tab_e = self.tab_cat_av_elenco
    tab_e.columnconfigure(0, weight=1)
    tab_e.rowconfigure(0, weight=1)

    def _btn(parent, icona, testo, comando):
        b = ttk.Label(parent, image=self.icone_gui.get(icona), text=testo, compound="left", cursor="hand2",
                      background=self.COLOR_WIDGET_BG, font=("Arial", 9, "bold"))
        b.image = self.icone_gui.get(icona)
        b.pack(side="left", padx=6)
        b.bind("<Button-1>", lambda e: comando())
        return b

    def _tt_cat(widget, testo):
        import textwrap
        testo_w = textwrap.fill(testo, width=48)
        stato = {"job": None}
        def _chiudi(e=None):
            if stato["job"]:
                try:
                    widget.after_cancel(stato["job"])
                except tk.TclError:
                    pass
                stato["job"] = None
            self.hide_tooltip()
        def _entra(e):
            _chiudi()
            stato["job"] = widget.after(500, lambda ev=e: (stato.update(job=None), self.show_tooltip(ev, testo_w)))
        widget.bind("<Enter>", _entra, add="+")
        widget.bind("<Leave>", _chiudi, add="+")
        widget.bind("<Button-1>", _chiudi, add="+")
        widget.bind("<Destroy>", _chiudi, add="+")

    fr_lista = ttk.Frame(tab_e)
    fr_lista.grid(row=0, column=0, sticky="nsew", padx=(8, 4), pady=8)
    fr_lista.columnconfigure(0, weight=1)
    fr_lista.rowconfigure(1, weight=1)
    fr_filtro = ttk.Frame(fr_lista)
    fr_filtro.grid(row=0, column=0, sticky="ew", pady=(0, 4))
    lbl_cerca = ttk.Label(fr_filtro, image=self.icone_gui.get("search"), text=" Cerca:", compound="left",
                          background=self.COLOR_WIDGET_BG, font=("Arial", 9, "bold"))
    lbl_cerca.image = self.icone_gui.get("search")
    lbl_cerca.pack(side="left")
    entry_filtro_cat = ttk.Entry(fr_filtro, textvariable=self.var_filtro_cat_av, width=24)
    entry_filtro_cat.pack(side="left", padx=6)
    def _reset_filtro_cat():
        self.var_filtro_cat_av.set("")
        entry_filtro_cat.focus_set()
    _btn(fr_filtro, "reset", " Reset", _reset_filtro_cat)
    self.var_filtro_cat_av.trace_add("write", lambda *_: _aggiorna_albero_cat_avanz(self))
    cont = tk.Frame(fr_lista, bg=self.COLOR_TOPLEVEL)
    cont.grid(row=1, column=0, sticky="nsew")
    canvas = tk.Canvas(cont, bg=self.COLOR_TOPLEVEL, highlightthickness=0)
    scrollbar = ttk.Scrollbar(cont, orient="vertical", command=canvas.yview, style="Vertical.TScrollbar")
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    scroll_frame = tk.Frame(canvas, bg=self.COLOR_TOPLEVEL)
    canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
    def _on_wheel_elenco(event):
        try:
            if self.nb_cat_av.select() != str(tab_e):
                return
            delta = getattr(event, 'delta', 0)
            num = getattr(event, 'num', 0)
            if num == 4 or delta > 0:
                canvas.yview_scroll(-1, "units")
            elif num == 5 or delta < 0:
                canvas.yview_scroll(1, "units")
        except (tk.TclError, AttributeError):
            pass
    popup.bind("<MouseWheel>", _on_wheel_elenco, add="+")
    popup.bind("<Button-4>", _on_wheel_elenco, add="+")
    popup.bind("<Button-5>", _on_wheel_elenco, add="+")
    self.cat_av_toggle_var = tk.BooleanVar()
    f_toggle = tk.Frame(scroll_frame, bg=self.COLOR_TOPLEVEL)
    f_toggle.pack(anchor="w", padx=10, pady=(6, 6))
    tk.Checkbutton(f_toggle, variable=self.cat_av_toggle_var, command=lambda: _toggle_tutte_cat_av(self),
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
    f_head = tk.Frame(scroll_frame, bg=self.COLOR_TOPLEVEL)
    f_head.pack(fill="x", pady=(0, 2))
    for titolo, w, anc in reversed(_COLONNE_CAT_AV):
        tk.Label(f_head, text=titolo, width=w, anchor=anc, bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                 font=("Arial", 9, "bold")).pack(side="right", padx=(0, 6))
    tk.Label(f_head, text="Categoria", anchor="w", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
             font=("Arial", 9, "bold")).pack(side="left", padx=(44, 0))
    self.cat_av_righe = tk.Frame(scroll_frame, bg=self.COLOR_TOPLEVEL)
    self.cat_av_righe.pack(fill="x")
    fr_del = ttk.Frame(fr_lista)
    fr_del.grid(row=2, column=0, sticky="ew", pady=(8, 0))
    tk.Checkbutton(
        fr_del,
        text="Elimina anche Movimenti associati",
        variable=self.cat_av_elimina_var,
        anchor="w",
        bg="yellow",
        activebackground="gold"
    ).pack(side="left", padx=(0, 6))
    _btn(fr_del, "delete", " Cancella spuntate", lambda: cancella_categorie_selezionate(self))
    self.lbl_cont_cat_av = ttk.Label(fr_del, text="", font=("Arial", 8))
    self.lbl_cont_cat_av.pack(side="right")

    form = ttk.LabelFrame(tab_e, text="✓ Dettagli Categoria", style="RedBold.TLabelframe")
    form.grid(row=0, column=1, sticky="ns", padx=(4, 8), pady=8)
    def convalida_categoria(valore):
        return len(valore) <= 20
    vcmd_cat = form.register(convalida_categoria)
    lbl_n = ttk.Label(form, image=self.icone_gui.get("search"), text=" Nome:", compound="left",
                      background=self.COLOR_WIDGET_BG, font=("Arial", 9, "bold"))
    lbl_n.image = self.icone_gui.get("search")
    lbl_n.grid(row=0, column=0, sticky="e", padx=4, pady=5)
    self.ed_entry_nome = ttk.Entry(form, textvariable=self.nuova_cat, width=22, validate="key",
                                   validatecommand=(vcmd_cat, "%P"))
    self.ed_entry_nome.grid(row=0, column=1, sticky="w", padx=2, pady=5)
    self.ed_entry_nome.bind("<Return>", lambda e: self.add_categoria())
    self.ed_entry_nome.bind("<KP_Enter>", lambda e: self.add_categoria())
    lbl_t = ttk.Label(form, image=self.icone_gui.get("documenti"), text=" Tipo:", compound="left",
                      background=self.COLOR_WIDGET_BG, font=("Arial", 9, "bold"))
    lbl_t.image = self.icone_gui.get("documenti")
    lbl_t.grid(row=1, column=0, sticky="e", padx=4, pady=5)
    def toggle_tipo():
        self.tipo_categoria.set("Entrata" if self.tipo_categoria.get() == "Uscita" else "Uscita")
        self._aggiorna_stile_pulsante_tipo_popup()
    self.ed_btn_tipo = ttk.Button(form, text=self.tipo_categoria.get(), width=10, command=toggle_tipo,
                                  style='RedOutline.TButton', takefocus=0)
    self.ed_btn_tipo.grid(row=1, column=1, sticky="w", padx=2, pady=5)
    self.ed_btn_tipo.config(cursor="hand2")
    self._aggiorna_stile_pulsante_tipo_popup()
    ttk.Label(form, text=" Classe 50/30/20:", background=self.COLOR_WIDGET_BG,
              font=("Arial", 9, "bold")).grid(row=2, column=0, sticky="e", padx=4, pady=5)
    self.ed_cb_classe = ttk.Combobox(form, textvariable=self.classe_categoria,
                                     values=["Nessuna", "Bisogni", "Desideri", "Risparmio"],
                                     style="Border.TCombobox", state="readonly", width=16)
    self.ed_cb_classe.grid(row=2, column=1, sticky="w", padx=2, pady=5)
    ttk.Label(form, text=" Conto:", font=("Arial", 9, "bold")).grid(row=3, column=0, sticky="e", padx=4, pady=5)
    self.ed_cb_conto = ttk.Combobox(form, textvariable=self.conto_risp_cat,
                                    values=["(nessuno)"] + self._nomi_conti_portafoglio(
                                        solo_risparmio=True, includi=self.conto_risp_cat.get()),
                                    style="ContoRisp.Border.TCombobox", state="readonly", width=16)
    self.ed_cb_conto.grid(row=3, column=1, sticky="w", padx=2, pady=5)
    def _stato_conto(*_):
        try:
            if not self.ed_cb_conto.winfo_exists():
                return
            if self.classe_categoria.get() == "Risparmio":
                self.ed_cb_conto.config(state="readonly")
            else:
                self.conto_risp_cat.set("(nessuno)")
                self.ed_cb_conto.config(state="disabled")
        except tk.TclError:
            pass
    self.classe_categoria.trace_add("write", _stato_conto)
    _stato_conto()
    _tt_cat(self.ed_cb_classe,
            "Classe 50/30/20 della categoria: Bisogni (max 50%), Desideri (max 30%), "
            "Risparmio (min 20%). Decide in quale gruppo contano le uscite di questa categoria nel Metodo 50/30/20.")
    _tt_cat(self.ed_cb_conto,
            "Attivo solo con classe Risparmio. Ogni uscita in questa categoria, registrata con un conto "
            "(es. Luca), diventa un trasferimento da quel conto al conto risparmio scelto qui. "
            "Premi Aggiungi o Modifica per salvare.")
    def convalida_budget(valore):
        if valore == "" or valore == ".":
            return True
        try:
            float(valore.replace(",", "."))
            return len(valore) <= 8
        except ValueError:
            return False
    vcmd_budget = form.register(convalida_budget)
    for riga, testo, var in ((4, " Budget €/mese:", self.var_budget_cat), (5, " Budget €/anno:", self.var_budget_annuo_cat)):
        ttk.Label(form, text=testo, font=("Arial", 9, "bold")).grid(row=riga, column=0, sticky="e", padx=4, pady=5)
        e = ttk.Entry(form, textvariable=var, width=10, validate="key", validatecommand=(vcmd_budget, "%P"))
        e.bind("<FocusOut>", lambda ev, v=var: [
            v.set(f"{float(v.get().strip().replace(',', '.')):.2f}".replace(".", ","))
            if v.get().strip() else None
        ])
        e.grid(row=riga, column=1, sticky="w", padx=2, pady=5)
    fr_b1 = ttk.Frame(form)
    fr_b1.grid(row=6, column=0, columnspan=2, pady=(14, 2))
    _btn(fr_b1, "check", " Aggiungi", lambda: self.add_categoria())
    _btn(fr_b1, "salva", " Salva", lambda: self.modifica_categoria())
    fr_b2 = ttk.Frame(form)
    fr_b2.grid(row=7, column=0, columnspan=2, pady=(4, 8))
    btn_annulla_cat = _btn(fr_b2, "chiudi", " Annulla", lambda: self.reset_campi_categoria())
    _btn(fr_b2, "timer", " Analisi", lambda: self.analisi_categorie(self.cat_mod_sel.get() or None))
    _tt_cat(btn_annulla_cat,
            "Annulla la modifica: svuota i campi e toglie la selezione dalla categoria scelta, senza salvare nulla.")

    _costruisci_tab_suggerite(self, self.tab_cat_av_sugg)
    self.nb_cat_av.bind("<<NotebookTabChanged>>",
        lambda e: self._ricostruisci_sugg_av() if self.nb_cat_av.select() == str(self.tab_cat_av_sugg) else None)
    self.reset_campi_categoria()
    popup.deiconify()
    self.nb_cat_av.select(self.tab_cat_av_sugg if tab == "suggerite" else self.tab_cat_av_elenco)

_ICONE_CAT_REGOLE = (
    ("home", ["Casa", "Affitto", "Mutuo", "Immobile", "Arredamento", "Pulizie", "Tassa", "Pellet", "Caldaia", "Utenze", "Bollette", "Consumi"]),
    ("spesa", ["Spesa"]),
    ("lavoro", ["Ristoranti", "Pranzi", "Asporto", "Colazioni"]),
    ("icc", ["Stipendio", "Pensione", "Extra", "Corrente", "Finanza", "Commercialista"]),
    ("salute", ["Salute", "Farmaci", "Mediche", "Dentista"]),
    ("fitness", ["Palestra", "Wellness"]),
    ("mobile", ["Telefonia", "Internet", "Cellulari"]),
    ("bus", ["Trasporti", "Taxi", "Bollo", "Auto", "Veicoli", "Carburante"]),
    ("regalo", ["Regali"]),
    ("cinema", ["Cinema", "Videogiochi", "Eventi"]),
    ("vestiti", ["Abbigliamento"]),
    ("beauty", ["Parrucchiere", "Estetica"]),
    ("aereo", ["Viaggi"]),
    ("cloud", ["Cloud", "Streaming", "Abbonamenti"]),
    ("studio", ["Libri", "Corsi"]),
    ("lavoro", ["Software", "Lavoro", "IVA"]),
    ("alert", ["Emergenze", "Straordinarie", "Impreviste"]),
)

def _icona_categoria_key(nome):
    for chiave, parole in _ICONE_CAT_REGOLE:
        if any(p in nome for p in parole):
            return chiave
    return "tools"

_COLONNE_CAT_AV = (("Classe", 9, "w"), ("Conto", 13, "w"), ("Mese", 9, "e"), ("Anno", 10, "e"), ("Tipo", 9, "w"))

def _fmt_budget_cat(v):
    return _fmt_it(v) if v and v > 0 else "–"

def _cat_av_protetta(self, nome):
    return nome in ("Generica", self.CATEGORIA_RIMOSSA)

def _seleziona_cat_av(self, nome):
    self.cat_mod_sel.set(nome)
    self.on_categoria_modifica_changed_popup()
    self.ed_cb_conto["values"] = ["(nessuno)"] + self._nomi_conti_portafoglio(
        solo_risparmio=True, includi=self._nome_conto_risparmio_cat(nome))
    for n, ws in self.cat_av_rows.items():
        bg = self.COLOR_WIDGET_BG if n == nome else self.COLOR_TOPLEVEL
        for w in ws:
            w.config(bg=bg)
        ws[1].config(activebackground=bg)

def _toggle_tutte_cat_av(self):
    val = self.cat_av_toggle_var.get()
    for n in self.cat_av_rows:
        if not _cat_av_protetta(self, n):
            self.cat_av_vars[n].set(val)
    _conta_cat_av(self)

def _conta_cat_av(self):
    vis = [n for n in self.cat_av_rows if not _cat_av_protetta(self, n)]
    self.cat_av_toggle_var.set(bool(vis) and all(self.cat_av_vars[n].get() for n in vis))
    k = sum(1 for n, v in self.cat_av_vars.items() if v.get() and n in self.categorie)
    self.lbl_cont_cat_av.config(text=f"{len(self.cat_av_rows)} categorie" + (f" · {k} spuntate" if k else ""))

def _aggiorna_albero_cat_avanz(self):
    righe = getattr(self, 'cat_av_righe', None)
    if righe is None:
        return
    try:
        if not righe.winfo_exists():
            return
    except tk.TclError:
        return
    filtro = self.var_filtro_cat_av.get().strip().lower()
    for n in list(self.cat_av_vars):
        if n not in self.categorie:
            del self.cat_av_vars[n]
    for w in righe.winfo_children():
        w.destroy()
    self.cat_av_rows = {}
    sel = self.cat_mod_sel.get()
    for nome in sorted(set(self.categorie), key=lambda c: c.lower()):
        if filtro and filtro not in nome.lower():
            continue
        var = self.cat_av_vars.setdefault(nome, tk.BooleanVar())
        prot = _cat_av_protetta(self, nome)
        if prot:
            var.set(False)
        bg = self.COLOR_WIDGET_BG if nome == sel else self.COLOR_TOPLEVEL
        f = tk.Frame(righe, bg=bg)
        f.pack(fill="x", pady=1)
        chk = tk.Checkbutton(f, variable=var, command=lambda: _conta_cat_av(self), bg=bg,
                             selectcolor=self.COLOR_WHITE, activebackground=bg,
                             highlightthickness=0, bd=0, state="disabled" if prot else "normal")
        chk.pack(side="left", padx=(5, 0))
        img_cat = self.icone_gui.get(_icona_categoria_key(nome))
        li = None
        if img_cat:
            li = tk.Label(f, image=img_cat, bg=bg, cursor="hand2")
            li.image = img_cat
            li.pack(side="left", padx=5)
        tipo = self.categorie_tipi.get(nome, "Uscita")
        classe = self._classi_categorie().get(nome, "")
        conto = self._nome_conto_risparmio_cat(nome) if classe == "Risparmio" else ""
        if conto == "(nessuno)":
            conto = ""
        valori = (classe or "–", conto or "–",
                  _fmt_budget_cat(self.budget_categorie.get(nome, 0)),
                  _fmt_budget_cat(self.budget_annuale_categorie.get(nome, 0)),
                  f"({tipo})")
        col_cols = []
        for (titolo, w, anc), testo in reversed(list(zip(_COLONNE_CAT_AV, valori))):
            if titolo == "Tipo":
                fg, fnt = ("#98C379" if tipo == "Entrata" else "#E06C75"), ("Arial", 8, "italic")
            else:
                fg, fnt = ("gray" if (prot or testo == "–") else self.TEXT_COLOR), ("Arial", 9)
            c = tk.Label(f, text=testo, width=w, anchor=anc, bg=bg, fg=fg, font=fnt, cursor="hand2")
            c.pack(side="right", padx=(0, 6))
            col_cols.append(c)
        lbl = tk.Label(f, text=nome, bg=bg, fg="gray" if prot else self.TEXT_COLOR,
                       font=("Arial", 10), cursor="hand2", anchor="w")
        lbl.pack(side="left", padx=5, fill="x", expand=True)
        for w in (f, li, lbl, *col_cols):
            if w is not None:
                w.bind("<Button-1>", lambda e, n=nome: _seleziona_cat_av(self, n))
        self.cat_av_rows[nome] = (f, chk, lbl) + tuple(col_cols) + ((li,) if li is not None else ())
    _conta_cat_av(self)

def cancella_categorie_selezionate(self):
    selezionate = sorted((c for c, v in getattr(self, 'cat_av_vars', {}).items()
                          if v.get() and c in self.categorie and not _cat_av_protetta(self, c)), key=str.lower)
    if not selezionate:
        self.show_custom_warning("Attenzione", "Spunta almeno una categoria da cancellare.")
        return
    var_elimina = getattr(self, 'cat_av_elimina_var', None)
    elimina_movimenti = bool(var_elimina.get()) if var_elimina is not None else False
    MAX_MOSTRATE = 6
    if len(selezionate) > MAX_MOSTRATE:
        elenco = "\n".join(f"• {c}" for c in selezionate[:MAX_MOSTRATE])
        elenco += f"\n… e altre {len(selezionate) - MAX_MOSTRATE} categorie"
    else:
        elenco = "\n".join(f"• {c}" for c in selezionate)
    testo_conferma = "Sei sicuro di voler cancellare le seguenti categorie?\n\n" + elenco
    if elimina_movimenti:
        testo_conferma += "\n\nI Movimenti associati saranno ELIMINATI."
    else:
        testo_conferma += f"\n\nI Movimenti saranno mantenuti ed etichettati '{self.CATEGORIA_RIMOSSA}'."
    if not self.show_custom_askyesno("Elimina", testo_conferma):
        return
    sel_set = set(selezionate)
    for cat in selezionate:
        if cat in self.categorie:
            self.categorie.remove(cat)
        self.categorie_tipi.pop(cat, None)
        self.budget_categorie.pop(cat, None)
        self.budget_annuale_categorie.pop(cat, None)
        self._classi_categorie().pop(cat, None)
        self._conti_risparmio_cat().pop(cat, None)
        _aggiorna_cat_ricorrenze(self, cat, self.CATEGORIA_RIMOSSA)
    for giorno in list(self.spese):
        nuove_spese = []
        for voce in self.spese[giorno]:
            if campo(voce, "categoria", "") in sel_set:
                if not elimina_movimenti:
                    nuove_spese.append(
                        voce.sostituisci(categoria=self.CATEGORIA_RIMOSSA)
                    )
            else:
                nuove_spese.append(voce)
        if nuove_spese:
            self.spese[giorno] = nuove_spese
        else:
            del self.spese[giorno]
    if var_elimina is not None:
        var_elimina.set(False)
    self.save_db()
    self.refresh_gui()
    self.aggiorna_combobox_categorie()
    self.on_categoria_changed()
    self.reset_campi_categoria()
    if len(selezionate) == 1:
        self.show_toast(f"Categoria '{selezionate[0]}' cancellata.")
    else:
        self.show_toast(f"{len(selezionate)} categorie cancellate.")
    if hasattr(self, 'ricorrenza_popup') and self.ricorrenza_popup.winfo_exists():
        if hasattr(self, 'ric_cat_menu'):
            self.ric_cat_menu['values'] = sorted(self.categorie)

# Tab Categorie Suggerite
def _costruisci_tab_suggerite(self, parent):
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
    selezioni = {nome_p: tk.BooleanVar() for nome_p in CATEGORIE_SUGGERITE}
    toggle_var = tk.BooleanVar()
    parent.columnconfigure(0, weight=1)
    parent.rowconfigure(0, weight=1)
    container = tk.Frame(parent, bg=self.COLOR_TOPLEVEL)
    container.grid(row=0, column=0, sticky="nsew", padx=8, pady=(8, 0))
    canvas = tk.Canvas(container, bg=self.COLOR_TOPLEVEL, highlightthickness=0)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview, style="Vertical.TScrollbar")
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    scroll_frame = tk.Frame(canvas, bg=self.COLOR_TOPLEVEL)
    canvas_window = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    def _on_mousewheel(event):
        try:
            if self.nb_cat_av.select() != str(parent):
                return
            if canvas and canvas.winfo_exists():
                delta = getattr(event, 'delta', 0)
                num = getattr(event, 'num', 0)          
                if num == 4 or delta > 0:
                     canvas.yview_scroll(-1, "units")
                elif num == 5 or delta < 0:
                     canvas.yview_scroll(1, "units")
        except (tk.TclError, NameError, AttributeError):
                    pass
    self.cat_av_popup.bind("<MouseWheel>", _on_mousewheel, add="+")
    self.cat_av_popup.bind("<Button-4>", _on_mousewheel, add="+")
    self.cat_av_popup.bind("<Button-5>", _on_mousewheel, add="+")
    scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
    def toggle_all():
        presenti = set(self.categorie)
        for n, v in selezioni.items():
            v.set(toggle_var.get() and n not in presenti)
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
    righe_frame = tk.Frame(scroll_frame, bg=self.COLOR_TOPLEVEL)
    righe_frame.pack(fill="x")
    def costruisci():
        for w in righe_frame.winfo_children():
            w.destroy()
        presenti = set(self.categorie)
        for nome_p in CATEGORIE_SUGGERITE:
            var = selezioni[nome_p]
            gia = nome_p in presenti
            if gia:
                var.set(False)
            tipo = TIPO_SUGGERITI[nome_p]
            icona_key = _icona_categoria_key(nome_p)
            img_png = self.icone_gui.get(icona_key)
            f_riga = tk.Frame(righe_frame, bg=self.COLOR_TOPLEVEL)
            f_riga.pack(fill="x", pady=1)
            chk = tk.Checkbutton(f_riga, variable=var, bg=self.COLOR_TOPLEVEL, 
                                 selectcolor=self.COLOR_WHITE, activebackground=self.COLOR_TOPLEVEL, 
                                 highlightthickness=0, bd=0, state="disabled" if gia else "normal")
            chk.pack(side="left", padx=(5, 0))
            if img_png:
                lbl_i = tk.Label(f_riga, image=img_png, bg=self.COLOR_TOPLEVEL)
                lbl_i.image = img_png
                lbl_i.pack(side="left", padx=5)
            tk.Label(f_riga, text=nome_p, bg=self.COLOR_TOPLEVEL, fg="gray" if gia else self.TEXT_COLOR, font=("Arial", 10)).pack(side="left", padx=5)            
            if gia:
                tk.Label(f_riga, text="già presente", bg=self.COLOR_TOPLEVEL, fg="gray", font=("Arial", 8, "italic")).pack(side="right", padx=15)
            else:
                color_t = "#98C379" if tipo == "Entrata" else "#E06C75"
                tk.Label(f_riga, text=f"({tipo})", bg=self.COLOR_TOPLEVEL, fg=color_t, font=("Arial", 8, "italic")).pack(side="right", padx=15)            
    self._ricostruisci_sugg_av = costruisci
    costruisci()
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
        self.aggiorna_combobox_categorie()
        self.save_db()
        for v in selezioni.values():
            v.set(False)
        toggle_var.set(False)
        costruisci()
        self.show_toast(f"Successo! Aggiunte {aggiunte} categorie.")
    btn_f = tk.Frame(parent, bg=self.COLOR_TOPLEVEL)
    btn_f.grid(row=1, column=0, pady=10)
    b_add = tk.Label(btn_f, text=" Aggiungi selezionate", image=self.icone_gui.get("aggiungi"), compound="left",
                     bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR, font=("Arial", 9, "bold"),
                     cursor="hand2", padx=20, pady=8)
    b_add.pack()
    b_add.bind("<Button-1>", esegui_import_interna)        

def get_dati_categorie_storiche_json(self, conto_filtro=None):
    spese_per_categoria = {}
    for giorno, voci in self.spese.items():
            for voce in voci:
                    if conto_filtro and self._conto_effettivo(voce) != conto_filtro:
                            continue
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

def get_dati_categorie_json(self, conto_filtro=None):
    oggi = datetime.date.today()
    anno_corrente = oggi.year
    spese_per_categoria = {}
    try:
        from moduli import web_pianificate as _wp
        _pian_on = _wp.attivo("anno")
        _pian_ids = _wp.ids_in_piano(self) if _pian_on else set()
    except Exception:
        _wp, _pian_on, _pian_ids = None, False, set()
    for data, entries in self.spese.items():
        if data.year == anno_corrente:
            for entry in entries:
                if conto_filtro and self._conto_effettivo(entry) != conto_filtro:
                    continue
                if campo(entry, "tipo", "") == "Uscita":
                    if _pian_ids and campo(entry, "id_spesa", None) in _pian_ids:
                        continue
                    categoria = campo(entry, "categoria", "")
                    importo = campo(entry, "importo", 0.0)
                    spese_per_categoria[categoria] = spese_per_categoria.get(categoria, 0.0) + importo
    if _pian_on and _wp is not None:
        for _cat, _q in _wp.quote_per_categoria(self, anno_corrente, None, conto_filtro).items():
            spese_per_categoria[_cat] = spese_per_categoria.get(_cat, 0.0) + _q
    labels = list(spese_per_categoria.keys())
    spese = [round(v, 2) for v in spese_per_categoria.values()]
    colori = ['#' + ''.join([random.choice('0123456789ABCDEF') for j in range(6)]) for i in range(len(labels))]
    budget_annuale_cat = getattr(self, 'budget_annuale_categorie', {})
    budget = [round(budget_annuale_cat.get(lbl, 0) or 0, 2) for lbl in labels]
    dati = {
        'labels': labels,
        'datasets': [{
            'data': spese,
            'backgroundColor': colori,
            'budget': budget,
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
    _btn("Nuova",        "aggiungi", nuova_voce)
    _btn("Modifica",     "modifica", modifica_voce)
    _btn("Elimina voce", "delete",   elimina_voce,  fg=self.COLOR_RED)
    _btn("Svuota tutto", "delete",   elimina_tutte, fg=self.COLOR_RED)
    btn_chiudi = ttk.Label(frame_bottoni, text=" Chiudi",
                           image=self.icone_gui.get("chiudi"), compound="left",
                           cursor="hand2", font=("Arial", 9, "bold"),
                           background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR)
    btn_chiudi.pack(side="right", padx=10)
    btn_chiudi.bind("<Button-1>", lambda e: popup.destroy())
