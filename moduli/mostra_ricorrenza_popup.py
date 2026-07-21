#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import datetime
import tkinter as tk
from tkinter import ttk
from moduli.modello_spesa import (
    METODI_PAGAMENTO_FILTRO, VOCE_FILTRO_MOVIMENTI, SEPARATORE_FILTRO_MOVIMENTI, campo,
)

def mostra_ricorrenza_popup(self):
    import __main__ as _app
    TOLL = _app.TOLL
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    oggi = datetime.date.today().strftime("%d-%m-%Y")
    if hasattr(self, 'ricorrenza_popup') and self.ricorrenza_popup.winfo_exists():
        self.reset_ricorrenza_popup()
        self.ricorrenza_popup.deiconify()
        self.ricorrenza_popup.lift()
        self.ric_cat_menu.configure(style="Border.TCombobox")
        self.ric_combo.configure(style="Border.TCombobox")
        if hasattr(self, 'ric_imp_entry'):
            self.ricorrenza_popup.after(100, self.ric_imp_entry.focus_set) 
        return
    self.ricorrenza_popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    self.ricorrenza_popup.transient(self)
    self.ricorrenza_popup.title("Gestione Ricorrenze")
    self.ricorrenza_popup.resizable(False, False)
    self.ricorrenza_popup.protocol(
        "WM_DELETE_WINDOW", 
        lambda: (
            self.ricorrenza_popup.withdraw(), 
            (self.popup_calendario.destroy(), setattr(self, 'popup_calendario', None))
            if hasattr(self, 'popup_calendario') and self.popup_calendario and self.popup_calendario.winfo_exists()
            else None,
            setattr(self, 'ricorrenza_bloccata', False) 
        )
    )
    self.ricorrenza_bloccata = False
    self.ricorrenza_popup.bind(
        "<Escape>", 
        lambda event: (
            self.ricorrenza_popup.withdraw(),
            (self.popup_calendario.destroy(), setattr(self, 'popup_calendario', None))
            if hasattr(self, 'popup_calendario') and self.popup_calendario and self.popup_calendario.winfo_exists()
            else None,
            setattr(self, 'ricorrenza_bloccata', False) 
        )
    )
    window_width = 720
    window_height = 250
    screen_width = self.winfo_screenwidth()
    screen_height = self.winfo_screenheight()
    center_x = int(screen_width/2 - window_width/2)
    center_y = int(screen_height/2 - window_height/2)
    self.ricorrenza_popup.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    if not hasattr(self, 'importo_ricorrenza'):
        self.importo_ricorrenza = tk.StringVar()
        self.ricorrenza_tipo = tk.StringVar(value="Nessuna")
        self.ricorrenza_n = tk.IntVar(value=1)
        self.ricorrenza_data_inizio = tk.StringVar(value=oggi)
        self.ricorrenza_cat_sel = tk.StringVar(value=self.categorie[0])
        self.ricorrenza_desc = tk.StringVar()
        self.ricorrenza_imp = tk.StringVar()
        self.ricorrenza_tipo_voce = tk.StringVar(value="Uscita")
        self.ricorrenza_bloccata = False
        self.ricorrenza_metodo = tk.StringVar(value="")
        self.ricorrenza_tag = tk.StringVar(value="")
    def on_ric_cat_selected(event=None, manuale=True):
        if manuale:
            self.ric_cat_menu.selection_clear()
            self.ric_imp_entry.focus_set()
            self.ricorrenza_bloccata = True
            self.label_smartcat_ric.config(text="💡 SmartCat Off", foreground="green")
            self.ric_percentuali_label.config(text="0% Entrate / 0% Uscite")
        categoria = self.ricorrenza_cat_sel.get()
        tipo = self.categorie_tipi.get(categoria, "Uscita")
        self.ricorrenza_tipo_voce.set(tipo)
        self.aggiorna_stile_tipo_voce_popup()
        if self.ricorrenza_bloccata:
            self.ric_cat_menu.configure(style="Border.TCombobox")
    def aggiorna_categoria_automatica_ricorrenza(*args):
        valore_imp = self.ricorrenza_imp.get().replace(",", ".").strip()
        if not valore_imp:
            self.ric_percentuali_label.config(text="0% Entrate / 0% Uscite")
            self.ricorrenza_bloccata = False
            self.ricorrenza_cat_sel.set("Generica")
            self.ricorrenza_tipo_voce.set("Uscita")
            self.aggiorna_stile_tipo_voce_popup()
            self.label_smartcat_ric.config(text="💡 SmartCat Idle...", foreground="gray")
            self.ric_cat_menu.configure(style="Border.TCombobox")
            return
        if self.ricorrenza_bloccata:
            return
        try:
            imp_corrente = float(valore_imp)
        except ValueError:
            self.ric_percentuali_label.config(text="0% Entrate / 0% Uscite")
            return
        oggi_ric = datetime.date.today()
        un_anno_fa = oggi_ric - datetime.timedelta(days=365)
        frequenze_per_categoria_tipo = {}
        for d, lista in self.spese.items():
            if d < un_anno_fa:
                continue
            for voce in lista:
                try:
                    categoria = campo(voce, "categoria", "")
                    importo = campo(voce, "importo", 0.0)
                    tipo = campo(voce, "tipo", "")
                    if categoria not in frequenze_per_categoria_tipo:
                        frequenze_per_categoria_tipo[categoria] = {"Entrata": 0, "Uscita": 0, "importi": []}
                    frequenze_per_categoria_tipo[categoria][tipo] += 1
                    frequenze_per_categoria_tipo[categoria]["importi"].append(importo)
                except (ValueError, IndexError):
                    continue
        if not self.suggerimenti_attivi:
            self.ricorrenza_bloccata = False
            self.label_smartcat_ric.config(text="💡 SmartCat Off", foreground="green")
            self.ric_cat_menu.configure(style="Border.TCombobox")
            categoria_selezionata = self.ricorrenza_cat_sel.get()
            percentuale_entrate, percentuale_uscite = 0.0, 0.0
            if categoria_selezionata in frequenze_per_categoria_tipo:
                conteggi = frequenze_per_categoria_tipo[categoria_selezionata]
                totale = conteggi["Entrata"] + conteggi["Uscita"]
                if totale > 0:
                    percentuale_entrate = (conteggi["Entrata"] / totale) * 100
                    percentuale_uscite = (conteggi["Uscita"] / totale) * 100
            self.ric_percentuali_label.config(text=f'{percentuale_entrate:.0f}% Entrate / {percentuale_uscite:.0f}% Uscite')
            return
        miglior_punteggio = float("inf")
        categoria_migliore = None
        mappa_ricorrenti = {}
        for d, lista in self.spese.items():
                if d < un_anno_fa:
                        continue
                for voce in lista:
                        try:
                                cat = campo(voce, "categoria", "")
                                imp = campo(voce, "importo", 0.0)
                                if cat not in self.categorie: continue
                            
                                chiave = (cat, round(float(imp), 2))
                                mappa_ricorrenti[chiave] = mappa_ricorrenti.get(chiave, 0) + 1
                        except:
                                continue
        for (categoria, importo_storico), freq in mappa_ricorrenti.items():
            diff = abs(importo_storico - imp_corrente)
            if diff < 0.01:
                punteggio = -2000 - freq
            elif diff <= 0.05:
                punteggio = -1000 - freq + (diff * 10)
            elif diff <= (imp_corrente * 0.02):
                punteggio = diff - (freq * 2)
            elif diff <= TOLL:
                punteggio = diff - freq
            else:
                continue
            if punteggio < miglior_punteggio:
                miglior_punteggio = punteggio
                categoria_migliore = categoria
        if categoria_migliore and not self.ricorrenza_bloccata:
            self.ricorrenza_cat_sel.set(categoria_migliore)
            conteggi = frequenze_per_categoria_tipo.get(categoria_migliore, {"Entrata": 0, "Uscita": 0})
            totale = conteggi["Entrata"] + conteggi["Uscita"]
            if totale > 0:
                percentuale_entrate = (conteggi["Entrata"] / totale) * 100
                percentuale_uscite = (conteggi["Uscita"] / totale) * 100
            else:
                percentuale_entrate, percentuale_uscite = 0.0, 0.0
            colore_percentuale = "black"
            if percentuale_entrate > percentuale_uscite:
                colore_percentuale = "forestgreen"
            elif percentuale_uscite > percentuale_entrate:
                colore_percentuale = "firebrick"
            self.ric_percentuali_label.config(
                text=f'{percentuale_entrate:.0f}% Entrate / {percentuale_uscite:.0f}% Uscite',
                foreground=colore_percentuale
            )
            on_ric_cat_selected(manuale=False)
            self.label_smartcat_ric.config(text="💡 SmartCat On", foreground="red")
            self.ric_cat_menu.configure(style="Highlight.TCombobox")
            self.ric_cat_menu.after(500, lambda: self.ric_cat_menu.configure(style="Border.TCombobox"))
    self.ricorrenza_imp.trace_add("write", aggiorna_categoria_automatica_ricorrenza)
    ric_frame = ttk.LabelFrame(self.ricorrenza_popup, text="🔄 Pianificazione Ricorrenze", style="RedBold.TLabelframe")
    ric_frame.pack(padx=10, pady=10, fill="both", expand=True)
    row = 0
    self.lbl_categoria = ttk.Label(
        ric_frame, 
        image=self.icone_gui.get("search"),
        text=" Categoria:", 
        compound="left",
        background=self.COLOR_WIDGET_BG,
        font=("Arial", 9, "bold")
    )
    self.lbl_categoria.image = self.icone_gui.get("search")
    self.lbl_categoria.grid(row=row, column=0, sticky="e", padx=2, pady=2)
    self.ric_cat_menu = ttk.Combobox(ric_frame, textvariable=self.ricorrenza_cat_sel, values=sorted(self.categorie, key=lambda c: c.lower()), state="readonly", style="Border.TCombobox", width=22, font=("Arial", 10, "bold"))
    self.ric_cat_menu.grid(row=row, column=1, sticky="w", padx=2, pady=2)
    self.ric_cat_menu.bind("<<ComboboxSelected>>", on_ric_cat_selected)
    info_frame = ttk.Frame(ric_frame)
    info_frame.grid(row=row, column=2, columnspan=5, sticky="w", padx=2, pady=2)
    self.label_smartcat_ric = ttk.Label(info_frame, text="💡 SmartCat Idle...", foreground="gray")
    self.label_smartcat_ric.pack(side="left", padx=2, pady=2)
    row += 1
    self.lbl_importo = ttk.Label(
        ric_frame, 
        image=self.icone_gui.get("saldo"),
        text=" Importo (€):", 
        compound="left",
        background=self.COLOR_WIDGET_BG,
        font=("Arial", 9, "bold")
    )
    self.lbl_importo.image = self.icone_gui.get("saldo")
    self.lbl_importo.grid(row=row, column=0, sticky="e", padx=2, pady=2)

    def convalida_importo(valore):
        if valore == "":
          return True  
        import re
        return len(valore) <= 7 and re.fullmatch(r"^\d*[.,]?\d{0,2}$", valore) is not None
    vcmd_importo = ric_frame.register(convalida_importo)  
    imp_frame = ttk.Frame(ric_frame)
    imp_frame.grid(row=row, column=1, sticky="w", padx=2, pady=2)

    self.ric_imp_entry = ttk.Entry(imp_frame, width=20, textvariable=self.ricorrenza_imp,
            validate="key", validatecommand=(vcmd_importo, "%P"))
    self.ric_imp_entry.pack(side="left")
    self.ric_imp_entry.focus_set()
    self.btn_calc_spesa = ttk.Label(imp_frame, image=self.icone_gui.get("calcolatrice"),
            cursor="hand2", background=self.COLOR_WIDGET_BG)
    self.btn_calc_spesa.image = self.icone_gui.get("calcolatrice")
    self.btn_calc_spesa.pack(side="left", padx=(4, 0))
    self.btn_calc_spesa.bind("<Button-1>", lambda e: self.apri_calcolatrice())
    self.v_conto_ricorrenza = tk.StringVar(value="(nessuno)")
    try:
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _f:
            _db_c = json.load(_f)
        _nomi_ric = ["(nessuno)", "📂 Portafoglio", "───────────"] + [c.get("nome","?") for c in _db_c.get("conti",[])]
        _princ_ric = next((c.get("nome","") for c in _db_c.get("conti",[]) if c.get("principale")), "(nessuno)")
        self.v_conto_ricorrenza.set(_princ_ric)
    except Exception:
        _nomi_ric = ["(nessuno)"]
    _conto_ric_frame = ttk.Frame(ric_frame)
    _conto_ric_frame.grid(row=row, column=2, sticky="w", padx=(10,2), pady=2)
    ttk.Label(_conto_ric_frame, text="Conto:", font=("Arial", 9, "bold")).pack(side="left", padx=(0,4))
    self.cb_conto_ricorrenza = ttk.Combobox(
        _conto_ric_frame, textvariable=self.v_conto_ricorrenza,
        values=_nomi_ric, state="readonly",
        style="Border.TCombobox", width=14
    )
    self.cb_conto_ricorrenza.pack(side="left")
    def gestisci_selezione_conto_ric(event):
            scelta = self.v_conto_ricorrenza.get()
            if scelta == "📂 Portafoglio":
                    self.apri_portafoglio()
                    self.v_conto_ricorrenza.set("(nessuno)")
    self.cb_conto_ricorrenza.bind("<<ComboboxSelected>>", gestisci_selezione_conto_ric)
    def start_blinking_callback_ric(event):
        if hasattr(self, 'lbl_ric_inizio'):
            self.start_blinking(self.lbl_ric_inizio)
        if self.STATO_CORRENTE != 0:
            self.mostra_treeview_statistiche()
    def stop_blinking_callback_ric(event):
        if hasattr(self, 'lbl_ric_inizio'):
            self.stop_blinking(self.lbl_ric_inizio)
    self.ric_imp_entry.bind('<FocusIn>', start_blinking_callback_ric)
    self.ric_imp_entry.bind('<FocusOut>', stop_blinking_callback_ric)
    self.ric_percentuali_label = ttk.Label(info_frame, text="0% Entrate / 0% Uscite")
    self.ric_percentuali_label.pack(side="left", padx=2, pady=2)
    row += 1
    self.lbl_info_desc = ttk.Label(
        ric_frame, 
        image=self.icone_gui.get("descrizione"),
        text=" Descrizione:", 
        compound="left",
        background=self.COLOR_WIDGET_BG,
        font=("Arial", 9, "bold")
    )
    self.lbl_info_desc.image = self.icone_gui.get("descrizione")
    self.lbl_info_desc.grid(row=row, column=0, sticky="e", padx=2, pady=2)
    def convalida_descrizione(valore):
        return len(valore) <= 35
    vdesc = ric_frame.register(convalida_descrizione)
    self.ric_desc_entry = ttk.Entry(ric_frame, width=25, textvariable=self.ricorrenza_desc, validate="key", validatecommand=(vdesc, "%P"))
    self.ric_desc_entry.grid(row=row, column=1, sticky="w", padx=2, pady=2)       
    metodi_ric = METODI_PAGAMENTO_FILTRO
    pag_frame = ttk.Frame(ric_frame)
    pag_frame.grid(row=row, column=2, sticky="w", padx=(19,2), pady=2)
    ttk.Label(pag_frame, text="Pagamento:").pack(side="left", padx=(0,4))
    self.ric_metodo_combo = ttk.Combobox(
            pag_frame, textvariable=self.ricorrenza_metodo,
            values=metodi_ric, state="readonly",
            style="Border.TCombobox", width=16
    )
    self.ric_metodo_combo.pack(side="left")
    def aggiorna_simbolo_metodo_ric(event=None):
            metodo = self.ricorrenza_metodo.get()
            if metodo == SEPARATORE_FILTRO_MOVIMENTI:
                    self.ricorrenza_metodo.set("")
                    return
            if metodo == VOCE_FILTRO_MOVIMENTI:
                    self.apri_estratti_metodo()
                    self.ricorrenza_metodo.set("")
                    return
            self.ric_metodo_combo.selection_clear()
            self.ric_imp_entry.focus_set()
    self.ric_metodo_combo.bind("<<ComboboxSelected>>", aggiorna_simbolo_metodo_ric)
    lbl_hash_ric = ttk.Label(pag_frame, text="#", compound="left", cursor="hand2",
                 background=self.COLOR_WIDGET_BG, font=("Arial", 12, "bold"))
    lbl_hash_ric.pack(side="left", padx=(8, 2))
    lbl_hash_ric.bind("<Button-1>", lambda e: self.apri_gestione_tag())
    _vcmd_tag_ric = (self.register(lambda P: len(P) <= 15), "%P")
    self.ric_tag_entry = ttk.Entry(pag_frame, width=13, style="Border.TEntry",
                               validate="key", validatecommand=_vcmd_tag_ric,
                               textvariable=self.ricorrenza_tag)
    self.ric_tag_entry.pack(side="left")
    self._ac_lb_ric = None
    def _get_tutti_tag_ric():
        if not hasattr(self, '_cache_tutti_tag'):
            tutti = set()
            for lista in self.spese.values():
                for voce in lista:
                    for t in campo(voce, "hashtag", []):
                        tutti.add(t.lstrip("#"))
            self._cache_tutti_tag = sorted(tutti)
        return self._cache_tutti_tag
    def _chiudi_ac_ric():
        if self._ac_lb_ric and self._ac_lb_ric.winfo_exists():
            self._ac_lb_ric.destroy()
        self._ac_lb_ric = None
    def _on_tag_ric_keyrelease(event):
        if event.keysym in ("Return", "Escape", "Tab"):
            _chiudi_ac_ric()
            return
        testo = self.ric_tag_entry.get()
        parole = testo.replace(",", " ").split()
        ultima = parole[-1].lstrip("#") if parole else ""
        if len(ultima) < 1:
            _chiudi_ac_ric()
            return
        suggerimenti = [t for t in _get_tutti_tag_ric() if t.lower().startswith(ultima.lower()) and t.lower() != ultima.lower()]
        if not suggerimenti:
            _chiudi_ac_ric()
            return
        if not self._ac_lb_ric or not self._ac_lb_ric.winfo_exists():
            self._ac_lb_ric = tk.Listbox(
                self.ricorrenza_popup,
                height=min(5, len(suggerimenti)),
                font=("Arial", 9),
                relief="solid", bd=1,
                bg=self.COLOR_WIDGET_BG,
                fg=self.TEXT_COLOR,
                selectbackground="#4a90d9"
            )
            x = self.ric_tag_entry.winfo_rootx() - self.ricorrenza_popup.winfo_rootx()
            y = self.ric_tag_entry.winfo_rooty() - self.ricorrenza_popup.winfo_rooty() + self.ric_tag_entry.winfo_height()
            self._ac_lb_ric.place(x=x, y=y, width=self.ric_tag_entry.winfo_width())
            def _seleziona_ric(e):
                if not self._ac_lb_ric:
                    return
                sel = self._ac_lb_ric.curselection()
                if not sel:
                    return
                scelto = self._ac_lb_ric.get(sel[0])
                parole_attuali = self.ric_tag_entry.get().replace(",", " ").split()
                if parole_attuali:
                    parole_attuali[-1] = scelto
                self.ric_tag_entry.delete(0, tk.END)
                self.ric_tag_entry.insert(0, " ".join(parole_attuali))
                _chiudi_ac_ric()
            self._ac_lb_ric.bind("<ButtonRelease-1>", _seleziona_ric)
        self._ac_lb_ric.delete(0, tk.END)
        self._ac_lb_ric.config(height=min(5, len(suggerimenti)))
        for s in suggerimenti:
            self._ac_lb_ric.insert(tk.END, s)
    self.ric_tag_entry.bind("<KeyRelease>", _on_tag_ric_keyrelease)
    self.ric_tag_entry.bind("<FocusOut>", lambda e: self.after(300, _chiudi_ac_ric))
    row += 1
    desc_frame = tk.Frame(ric_frame, bg=self.COLOR_WIDGET_BG)
    desc_frame.grid(row=row, column=2, sticky="w", padx=5, pady=2)
    self.nomi_con_icone = []
    self.nomi_partecipanti.sort(key=lambda x: (
            0 if x.get("tipo") == "contenitore" else
            (2 if x.get("tipo") == "personale" else 1),
            x.get("nome", "").lower()
    ))
    _gestore_init = os.path.basename(os.getcwd())
    _nomi_init    = [p.get("nome", "") for p in self.nomi_partecipanti]
    if self._gestore_partecipa() and _gestore_init not in _nomi_init:
        self.nomi_con_icone.append(f"✽ {_gestore_init}")
    for p in self.nomi_partecipanti:
            n = p.get("nome", "")
            t = p.get("tipo", "persona")
            ico = "❍" if t == "contenitore" else ("⚖️" if t == "personale" else "✽")
            self.nomi_con_icone.append(f"{ico} {n}")
    img_partecipante = self.icone_gui.get("utenti")
    lbl_part = ttk.Label(desc_frame, image=img_partecipante,
                         text=" 👥" if not img_partecipante else "",
                         compound="left", cursor="hand2",
                         background=self.COLOR_WIDGET_BG)
    lbl_part.pack(side=tk.LEFT, padx=(4, 0))
    lbl_part.bind("<Button-1>", lambda e: self.mostra_dare_avere())
    self.ric_partecipante_var = tk.StringVar(value="")
    self.ric_partecipante_combobox = ttk.Combobox(
            desc_frame,
            textvariable=self.ric_partecipante_var,
            values=[""] + self.nomi_con_icone + ["⚙️ Gestisci Partecipanti"],
            state="readonly",
            style="Border.TCombobox",
            width=25
    )
    self.ric_partecipante_combobox.pack(side=tk.LEFT, padx=(0, 4))
    self.ric_partecipante_combobox.bind("<<ComboboxSelected>>", lambda e: (
            self._on_ric_partecipante_selected(),
            self.ric_partecipante_combobox.selection_clear(),
            self.ric_partecipante_var.set(""),
            self.imp_entry.focus_set()
    ))
    ttk.Label(ric_frame, text="Tipo:").grid(row=row, column=0, sticky="e", padx=2, pady=2)
    self.ricorrenza_tipo_voce.set("Uscita")
    def aggiorna_stile_tipo_voce_popup():
            tipo = self.ricorrenza_tipo_voce.get()
            stile_da_applicare = "GreenOutline.TButton" if tipo == "Entrata" else "RedOutline.TButton"
            self.btn_tipo_voce.config(text=tipo, style=stile_da_applicare)
    def toggle_tipo_voce():
            tipo_corrente = self.ricorrenza_tipo_voce.get()
            self.ricorrenza_tipo_voce.set("Entrata" if tipo_corrente == "Uscita" else "Uscita")
            aggiorna_stile_tipo_voce_popup()
    self.btn_tipo_voce = ttk.Button(
            ric_frame,
            text=self.ricorrenza_tipo_voce.get(),
            width=7,
            command=toggle_tipo_voce,
            style=("GreenOutline.TButton" if self.ricorrenza_tipo_voce.get() == "Entrata" else "RedOutline.TButton")
    )
    self.btn_tipo_voce.grid(row=row, column=1, sticky="w", padx=2, pady=2)
    self.btn_tipo_voce.config(cursor="hand2")
    self.aggiorna_stile_tipo_voce_popup = aggiorna_stile_tipo_voce_popup
    self.aggiorna_stile_tipo_voce_popup()
    row += 1
    ripeti_frame = ttk.Frame(ric_frame)
    ripeti_frame.grid(row=row, column=0, columnspan=6, sticky="w", padx=2, pady=2)
    self.lbl_ripeti = ttk.Label(
        ripeti_frame, 
        image=self.icone_gui.get("calendario"),
        text=" Ripeti:", 
        compound="left",
        background=self.COLOR_WIDGET_BG,
        font=("Arial", 9, "bold")
    )
    self.lbl_ripeti.image = self.icone_gui.get("calendario")
    self.lbl_ripeti.pack(side="left", padx=2, pady=2)
    self.ric_combo = ttk.Combobox(
            ripeti_frame, 
            values=["Nessuna", "Ogni giorno", "Ogni mese", "Ogni anno"], 
            width=10, 
            state="readonly", 
            style="Border.TCombobox", 
            textvariable=self.ricorrenza_tipo
    )
    self.ric_combo.pack(side="left", padx=5)
    ttk.Label(ripeti_frame, text="Ripeti volte:").pack(side="left", padx=5, pady=2)
    self.ric_combo.bind("<<ComboboxSelected>>", lambda e: (
            self.ric_combo.selection_clear(),
            self.ric_n_entry.focus_set(),
            self.ric_n_entry.icursor(tk.END)
    ))
    def convalida_ric_n(valore):
        if valore == "":
            self.ricorrenza_n.set(1) 
            return True
        try:
            n = int(valore)
            return True
        except ValueError:
            self.ricorrenza_n.set(1)
            return False
    self.ric_n_entry = ttk.Entry(
        ripeti_frame,
        width=4,
        textvariable=self.ricorrenza_n,
    )
    self.ric_n_entry.pack(side="left", padx=2, pady=2)
    self.ric_n_entry.bind("<FocusOut>", lambda event: convalida_ric_n(self.ricorrenza_n.get()))
    self.ric_n_entry.bind("<Return>", lambda event: convalida_ric_n(self.ricorrenza_n.get()))
    self.ric_n_entry.bind("<KP_Enter>", lambda event: convalida_ric_n(self.ricorrenza_n.get()))
    self.lbl_ric_inizio = ttk.Label(ripeti_frame, text="Data Inizio:", style="BlinkAllarme.TLabel")
    self.lbl_ric_inizio.pack(side="left", padx=10, pady=2) 
    ric_data_frame = ttk.Frame(ripeti_frame)
    ric_data_frame.pack(side="left")
    self.ric_data_entry = ttk.Entry(ric_data_frame, textvariable=self.ricorrenza_data_inizio, width=15, font=("Arial", 10, "bold"))
    self.ric_data_entry.pack(side="left") 
    self.btn_cal_popup = ttk.Label(
        ric_data_frame,
        image=self.icone_gui.get("calendario"),
        cursor="hand2",
        background=self.COLOR_WIDGET_BG
    )
    self.btn_cal_popup.image = self.icone_gui.get("calendario")
    self.btn_cal_popup.pack(side="left", padx=4)
    self.btn_cal_popup.bind("<Button-1>", lambda e: self.mostra_calendario_popup(self.ric_data_entry, self.ricorrenza_data_inizio))
    self.btn_reset_ric_data = ttk.Label(
        ric_data_frame,
        image=self.icone_gui.get("reset"),
        cursor="hand2",
        background=self.COLOR_WIDGET_BG
    )
    self.btn_reset_ric_data.image = self.icone_gui.get("reset")
    self.btn_reset_ric_data.pack(side="left", padx=4)
    self.btn_reset_ric_data.bind("<Button-1>", lambda e: self.reset_ric_data_inizio())
    row += 1 
    btn_frame = tk.Frame(self.ricorrenza_popup, bg=self.COLOR_TOPLEVEL)
    btn_frame.pack(pady=10)
    self.btn_add_ricorrenza = ttk.Label(
        btn_frame, image=self.icone_gui.get("salva"),
        text=" Salva", compound="left", cursor="hand2", background=self.COLOR_WIDGET_BG, font=("Arial", 9, "bold")
    )
    self.btn_add_ricorrenza.image = self.icone_gui.get("salva")
    self.btn_add_ricorrenza.pack(side="left", padx=4)
    self.btn_add_ricorrenza.bind("<Button-1>", lambda e: (
        self.add_ricorrenza(),
        self.reset_ricorrenza_popup(),
        self.ric_imp_entry.focus_set()
    ))
    self.btn_reset_ricorrenza = ttk.Label(
        btn_frame, image=self.icone_gui.get("reset"),
        cursor="hand2", background=self.COLOR_WIDGET_BG
    )
    self.btn_reset_ricorrenza.image = self.icone_gui.get("reset")
    self.btn_reset_ricorrenza.pack(side="left", padx=4)
    self.btn_reset_ricorrenza.bind("<Button-1>", lambda e: self.reset_ricorrenza_popup())
    self.btn_modifica_ricorrenza = ttk.Label(
        btn_frame, image=self.icone_gui.get("report"),
        text=" Lista", compound="left", cursor="hand2", background=self.COLOR_WIDGET_BG, font=("Arial", 9, "bold")
    )
    self.btn_modifica_ricorrenza.image = self.icone_gui.get("report")
    self.btn_modifica_ricorrenza.pack(side="left", padx=4)
    self.btn_modifica_ricorrenza.bind("<Button-1>", lambda e: self.mostra_lista_ricorrenze())
    self.btn_chiudi_ricorrenza = ttk.Label(
        btn_frame, image=self.icone_gui.get("chiudi"),
        text=" Chiudi", compound="left", cursor="hand2", background=self.COLOR_WIDGET_BG, font=("Arial", 9, "bold")
    )
    self.btn_chiudi_ricorrenza.image = self.icone_gui.get("chiudi")
    self.btn_chiudi_ricorrenza.pack(side="left", padx=4)
    self.btn_chiudi_ricorrenza.bind("<Button-1>", lambda e: self.ricorrenza_popup.withdraw())

def reset_ricorrenza_popup(self):
    oggi = datetime.date.today().strftime("%d-%m-%Y")
    self.importo_ricorrenza.set("")
    self.ricorrenza_tipo.set("Nessuna")
    self.ricorrenza_n.set(1)
    self.ricorrenza_data_inizio.set(oggi)
    self.ricorrenza_cat_sel.set(self.categorie[0])
    self.ricorrenza_desc.set("")
    self.ricorrenza_imp.set("")
    self.ricorrenza_bloccata = False
    self.ricorrenza_tipo_voce.set("Uscita")
    self.aggiorna_stile_tipo_voce_popup()
    self.ric_percentuali_label.config(text="0% Entrate / 0% Uscite")
    self.label_smartcat_ric.config(text="💡 SmartCat Idle...", foreground="gray")
    self.ric_cat_menu.configure(style="Border.TCombobox")
    if hasattr(self, 'ricorrenza_metodo'):
        self.ricorrenza_metodo.set("")
    if hasattr(self, 'ricorrenza_tag'):
        self.ricorrenza_tag.set("")

