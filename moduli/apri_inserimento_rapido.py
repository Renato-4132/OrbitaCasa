#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import tkinter as tk
from tkinter import ttk

# Inserimento rapido
def apri_inserimento_rapido(self, event):
    import __main__ as _app
    TOLL = _app.TOLL
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    try:
        testo = event.widget.cget("text")
        if not str(testo).strip().isdigit():
            return
    except:
        pass
    hud = getattr(self, '_quick_add_hud', None)
    if hud:
        try:
            if hud.winfo_exists():
                hud.destroy()
        except Exception:
            pass
        self._quick_add_hud = None
    if hasattr(self, 'popup_rapido_attivo') and self.popup_rapido_attivo:
        try:
            if self.popup_rapido_attivo.winfo_exists():
                return
        except: pass
    if self.tooltip_timer:
        self.after_cancel(self.tooltip_timer)
        self.tooltip_timer = None
    if hasattr(self, 'popup_rapido_attivo') and self.popup_rapido_attivo and self.popup_rapido_attivo.winfo_exists():
        self.popup_rapido_attivo.lift()
        self.popup_rapido_attivo.focus_force()
        return
    if self.stats_view_mode.get() != "tabella":
        self.mostra_treeview_statistiche()
    data_sel = self.cal.selection_get()
    if not data_sel:
        return
    popup = tk.Toplevel(self, bg=self.COLOR_WIDGET_BG)
    self.popup_rapido_attivo = popup
    popup.withdraw()
    popup.title(f"Inserimento Rapido")
    popup.transient(self)
    popup.resizable(False, False)
    w, h = 400, 380
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    popup.geometry(f"{w}x{h}+{x}+{y}")
    popup.update_idletasks()
    popup.deiconify()
    lbl_data_popup = tk.Label(popup, text=f"  {data_sel.strftime('%d/%m/%Y')}",
                              image=self.icone_gui.get("calendario"),
                              compound="left",
                              bg=self.COLOR_WIDGET_BG, fg="purple",
                              font=("Arial", 11, "bold"))
    lbl_data_popup.image = self.icone_gui.get("calendario")
    lbl_data_popup.pack(fill="x", padx=15, pady=(8, 0))
    self.blink_label_colors(lbl_data_popup, "purple", "orange")
    var_imp = tk.StringVar()
    var_cat = tk.StringVar(value=self.categorie[0])
    var_tipo = tk.StringVar(value="Uscita")
    var_desc = tk.StringVar()
    def _limita_desc(*args):
        v = var_desc.get()
        if len(v) > 35:
            var_desc.set(v[:35])
    var_desc.trace_add("write", _limita_desc)
    var_part = tk.StringVar()
    var_metodo = tk.StringVar()
    try:
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
            _db_p_rap = json.load(_pf)
        _conti_rap = [c.get("nome","?") for c in _db_p_rap.get("conti",[])]
        _princ_rap = next((c.get("nome","") for c in _db_p_rap.get("conti",[]) if c.get("principale")), "(nessuno)")
    except Exception:
        _conti_rap = []
        _princ_rap = "(nessuno)"
    var_conto_rap = tk.StringVar(value=_princ_rap)
    frame = ttk.Frame(popup, padding=15)
    frame.pack(fill="both", expand=False)
    lbl_smartcat = ttk.Label(frame, text="💡 SmartCat Idle...", foreground="gray", font=("Arial", 9, "bold"))
    lbl_smartcat.grid(row=0, column=0, columnspan=3, pady=(0, 10), sticky="w")
    def trigger_smartcat(e=None):
        if not self.suggerimenti_attivi: return
        val = var_imp.get().replace(",", ".").strip()
        if not val:
            var_cat.set("Generica")
            var_tipo.set("Uscita")
            lbl_smartcat.config(text="💡 SmartCat Idle...", foreground="gray")
            return
        try: imp_corrente = float(val)
        except ValueError: return
        import datetime
        oggi = datetime.date.today()
        un_anno_fa = oggi - datetime.timedelta(days=365)
        mappa_ricorrenti = {}
        for d, lista in self.spese.items():
            if d < un_anno_fa: continue
            for voce in lista:
                try:
                    cat, _, imp, _ = voce[:4]
                    if cat in ["", "Categoria Rimossa", None] or cat not in self.categorie: continue
                    chiave = (cat, round(float(imp), 2))
                    mappa_ricorrenti[chiave] = mappa_ricorrenti.get(chiave, 0) + 1
                except: continue
        miglior_punteggio = float("inf")
        categoria_migliore = None
        for (categoria, importo_storico), freq in mappa_ricorrenti.items():
            diff = abs(importo_storico - imp_corrente)
            if diff < 0.01: punteggio = -2000 - freq
            elif diff <= 0.05: punteggio = -1000 - freq + (diff * 10)
            elif diff <= (imp_corrente * 0.02): punteggio = diff - (freq * 2)
            elif diff <= TOLL: punteggio = diff - freq
            else: continue
            if punteggio < miglior_punteggio:
                miglior_punteggio = punteggio
                categoria_migliore = categoria
        if categoria_migliore:
            var_cat.set(categoria_migliore)
            var_tipo.set(self.categorie_tipi.get(categoria_migliore, "Uscita"))
            lbl_smartcat.config(text=f"💡 SmartCat: On", foreground="red")
    ttk.Label(frame, text="Importo (€):", font=("Arial", 9, "bold")).grid(row=1, column=0, sticky="w", pady=5)
    def _val_imp(p):
        if p == "":
            return True
        import re
        return len(p) <= 8 and re.match(r"^\d*[.,]?\d{0,2}$", p) is not None
    _vi = frame.register(_val_imp)
    entry_imp_rapido = ttk.Entry(frame, textvariable=var_imp, width=15, validate="key", validatecommand=(_vi, "%P"))
    entry_imp_rapido.grid(row=1, column=1, sticky="w", pady=5)
    entry_imp_rapido.bind("<KeyRelease>", trigger_smartcat)
    entry_imp_rapido.focus_set()
    entry_originale = getattr(self, 'imp_entry', None)
    self.imp_entry = entry_imp_rapido
    btn_calc = ttk.Label(frame, image=self.icone_gui.get("calcolatrice"), cursor="hand2", background=self.COLOR_WIDGET_BG)
    btn_calc.image = self.icone_gui.get("calcolatrice")
    btn_calc.grid(row=1, column=2, sticky="w", padx=5)
    btn_calc.bind("<Button-1>", lambda e: self.apri_calcolatrice())
    ttk.Label(frame, text="Tipo:", font=("Arial", 9, "bold")).grid(row=2, column=0, sticky="w", pady=5)
    ttk.Combobox(frame, textvariable=var_tipo, values=["Uscita", "Entrata"], state="readonly", style="Border.TCombobox", width=15).grid(row=2, column=1, sticky="w", pady=5)
    ttk.Label(frame, text="Categoria:", font=("Arial", 9, "bold")).grid(row=3, column=0, sticky="w", pady=5)
    combo_cat = ttk.Combobox(frame, textvariable=var_cat, values=sorted(self.categorie, key=str.lower), state="readonly", style="Border.TCombobox", width=25)
    combo_cat.grid(row=3, column=1, columnspan=2, sticky="w", pady=5)
    combo_cat.bind("<<ComboboxSelected>>", lambda e: var_tipo.set(self.categorie_tipi.get(var_cat.get(), "Uscita")))
    ttk.Label(frame, text="Pagamento:", font=("Arial", 9, "bold")).grid(row=4, column=0, sticky="w", pady=5)
    metodi_lista = ["", "📂 Movimenti", "──────────", "💰 Contanti", "🔄 RID/SDD", "🏦 Bonifico", "💎 C.Credito", "💜 C.Credito", "💳 C.Debito", "📶 Contactless", "📯 PayPal", "📮 Bollettino", "🏪 Prepagata", "🪙 Assegno", "🔘 Revolut", "🍎 Apple Pay", "🎯 Google Pay", "🏣 Postepay", "📲 Satispay", "🔀 Scalapay", "🛒 Amazon Pay"]
    combo_metodo = ttk.Combobox(frame, textvariable=var_metodo, values=metodi_lista,
                                state="readonly", style="Border.TCombobox", width=15)
    combo_metodo.grid(row=4, column=1, sticky="w", pady=5)
    ttk.Label(frame, text="Partecipante:", font=("Arial", 9, "bold")).grid(row=5, column=0, sticky="w", pady=5)
    def aggiorna_nomi_combo():
        vals = [""]
        for p in self.nomi_partecipanti:
            n = p.get("nome", "")
            t = p.get("tipo", "persona")
            ico = "🏠" if t == "contenitore" else ("⚖️" if t == "personale" else "👤")
            vals.append(f"{ico} {n}")
        vals.append("⚙️ Gestisci Partecipanti")
        return vals
    nomi_combo = aggiorna_nomi_combo()
    combo_part = ttk.Combobox(frame, textvariable=var_part, values=nomi_combo,
                              state="readonly", style="Border.TCombobox", width=25)
    combo_part.grid(row=5, column=1, columnspan=2, sticky="w", pady=5)
    ttk.Label(frame, text="Descrizione:", font=("Arial", 9, "bold")).grid(row=6, column=0, sticky="w", pady=5)
    entry_desc_rapida = ttk.Entry(frame, textvariable=var_desc, width=27)
    entry_desc_rapida.grid(row=6, column=1, columnspan=2, sticky="w", pady=5)
    if _conti_rap:
        ttk.Label(frame, text="Conto:", font=("Arial", 9, "bold")).grid(row=7, column=0, sticky="w", pady=5)
        ttk.Combobox(frame, textvariable=var_conto_rap,
                     values=["(nessuno)"] + _conti_rap,
                     state="readonly", style="Border.TCombobox", width=25).grid(row=7, column=1, columnspan=2, sticky="w", pady=5)
    def aggiorna_tutto_desc(event=None):
        testo_puro = entry_desc_rapida.get().strip()
        simbolo_attuale = ""
        metodi_simboli = [m.split(" ")[0] for m in metodi_lista if m]
        for sim in metodi_simboli:
            if testo_puro.startswith(sim):
                simbolo_attuale = sim
                testo_puro = testo_puro[len(sim):].strip()
                break
        partecipante_attuale = ""
        for p_nome in sorted(nomi_combo, key=len, reverse=True):
            if p_nome and testo_puro.endswith(p_nome):
                partecipante_attuale = p_nome
                testo_puro = testo_puro[:-len(p_nome)].strip()
                break
        if event and event.widget == combo_metodo:
            scelta_m = var_metodo.get()
            simbolo_finale = scelta_m.split(" ")[0] if scelta_m else ""
            partecipante_finale = partecipante_attuale
        elif event and event.widget == combo_part:
            simbolo_finale = simbolo_attuale
            partecipante_finale = var_part.get()
        else:
            simbolo_finale = simbolo_attuale
            partecipante_finale = partecipante_attuale
        risultato = f"{simbolo_finale} {testo_puro} {partecipante_finale}".strip()
        entry_desc_rapida.delete(0, tk.END)
        entry_desc_rapida.insert(0, risultato)
        var_part.set("")
        var_metodo.set("")
        entry_imp_rapido.focus_set()
    def gestisci_metodo_inserimento(event):
        scelta = var_metodo.get()
        if scelta == "──────────":
            var_metodo.set("")
            return
        if scelta == "📂 Movimenti":
            self.apri_estratti_metodo()
            var_metodo.set("")
            return
        aggiorna_tutto_desc(event)
    combo_metodo.bind("<<ComboboxSelected>>", gestisci_metodo_inserimento)
    def on_part_selected(event=None):
        if "Gestisci Partecipanti" in var_part.get():
            var_part.set("")
            self.gestisci_partecipanti(target_popup=popup)
            combo_part["values"] = aggiorna_nomi_combo()
            nomi_combo[:] = combo_part["values"]
            return
        aggiorna_tutto_desc(event)
    combo_part.bind("<<ComboboxSelected>>", on_part_selected)
    def salva_rapido(e=None):
        try:
            imp = float(var_imp.get().replace(",", "."))
        except ValueError:
            self.show_toast("Errore: Importo mancante o non valido.", parent=popup)
            return
        cat = var_cat.get()
        if not cat or cat == "Categoria Rimossa" or cat not in self.categorie:
            self.show_toast("Errore: Seleziona una categoria valida.", parent=popup)
            return
        parti_desc = []
        if var_metodo.get():
            simbolo_pagamento = var_metodo.get().split(" ")[0]
            parti_desc.append(simbolo_pagamento)
        if var_part.get():
            parti_desc.append(var_part.get().strip())
        if var_desc.get().strip():
            parti_desc.append(var_desc.get().strip())
        desc_finale = " ".join(parti_desc)
        if data_sel not in self.spese:
            self.spese[data_sel] = []
        self.spese[data_sel].append((cat, desc_finale, imp, var_tipo.get()))
        self.save_db()
        _nome_c_rap = var_conto_rap.get()
        if _nome_c_rap and _nome_c_rap != "(nessuno)":
            self._aggiorna_conto_portafoglio(
                _nome_c_rap, None, None,
                imp, var_tipo.get(), data_sel, cat, desc_finale
            )
        self.refresh_gui()
        chiudi_rapido()
        self.show_toast(f"Spesa salvata in data {data_sel.strftime('%d/%m/%Y')}!")
    def chiudi_rapido(e=None):
        if entry_originale is not None:
            self.imp_entry = entry_originale
        popup.destroy()
    btn_box = tk.Frame(popup, bg=self.COLOR_WIDGET_BG)
    btn_box.pack(pady=15)
    lbl_salva = ttk.Label(btn_box, text=" Aggiungi", image=self.icone_gui.get("carica"), compound="left", cursor="hand2", font=("Arial", 10, "bold"), background=self.COLOR_WIDGET_BG, foreground=self.COLOR_GREEN)
    lbl_salva.image = self.icone_gui.get("carica")
    lbl_salva.pack(side="left", padx=10)
    lbl_salva.bind("<Button-1>", salva_rapido)
    lbl_annulla = ttk.Label(btn_box, text=" Annulla", image=self.icone_gui.get("chiudi"), compound="left", cursor="hand2", font=("Arial", 10, "bold"), background=self.COLOR_WIDGET_BG, foreground=self.COLOR_RED)
    lbl_annulla.image = self.icone_gui.get("chiudi")
    lbl_annulla.pack(side="right", padx=10)
    lbl_annulla.bind("<Button-1>", chiudi_rapido)
    popup.bind("<Return>", salva_rapido)
    popup.bind("<Escape>", chiudi_rapido)
    popup.protocol("WM_DELETE_WINDOW", chiudi_rapido)
    
