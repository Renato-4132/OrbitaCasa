#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import tkinter as tk
from tkinter import ttk

def gestisci_partecipanti(self, target_popup=None):
    import __main__ as _app
    PARTECIPANTI = _app.PARTECIPANTI
    _leggi_gestore_partecipa = _app._leggi_gestore_partecipa
    _scrivi_gestore_partecipa = _app._scrivi_gestore_partecipa

    if hasattr(self, '_gestione_popup') and self._gestione_popup and self._gestione_popup.winfo_exists():
        self._gestione_popup.lift()
        self._gestione_popup.focus_force()
        return
    dialogo = tk.Toplevel(self)
    self._gestione_popup = dialogo
    dialogo.title("Fair Share - Gestisci Partecipanti")
    dialogo.resizable(False, False)
    dialogo.withdraw()
    self.update_idletasks()
    w, h = 750, 620
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    dialogo.geometry(f"{w}x{h}+{x}+{y}")
    dialogo.configure(bg=self.COLOR_TOPLEVEL)
    dialogo.transient(self)
    dialogo.deiconify()
    dialogo.lift()
    dialogo.focus_force()
    dialogo.grab_set()
    def _on_dialogo_destroy(e):
        if e.widget is not dialogo:
            return
        setattr(self, '_gestione_popup', None)
        if target_popup:
            try:
                if target_popup.winfo_exists():
                    target_popup.grab_set()
            except Exception:
                pass
    dialogo.bind("<Destroy>", _on_dialogo_destroy)
    f = ttk.Frame(dialogo, padding=14)
    f.pack(fill=tk.BOTH, expand=True)
    ttk.Label(f, text="Partecipanti Fair Share:", font=("Arial", 10, "bold")).pack(anchor="w")
    list_frame = ttk.Frame(f)
    list_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 8))
    vsb = ttk.Scrollbar(list_frame, orient="vertical", style="Vertical.TScrollbar")
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    listbox = tk.Listbox(list_frame, yscrollcommand=vsb.set,
                         bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                         selectbackground="#61AFEF", font=("Arial", 10),
                         height=6, borderwidth=0, highlightthickness=0)
    listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
    vsb.config(command=listbox.yview)
    _contenitore_in_modifica = [None]
    def _nomi_display(p):
        if isinstance(p, dict):
            nome = p.get("nome", "")
            tipo = p.get("tipo", "persona")
            icona = "🏠" if tipo == "contenitore" else ("⚖️" if tipo == "personale" else "👤")
            info = f" ({len(p.get('soci', []))} soci)" if tipo == "contenitore" else ""
            return f"{icona} {nome}{info}"
        return f"👤 {p}"
    def _get_nome(p):
        return p.get("nome", p) if isinstance(p, dict) else p
    def aggiorna_lista():
        NOME_GESTORE = os.path.basename(os.getcwd())
        self.nomi_partecipanti.sort(key=lambda x: (
            0 if (isinstance(x, dict) and x.get("tipo") == "contenitore") else
            (2 if (isinstance(x, dict) and x.get("tipo") == "personale") else 1),
            (x.get("nome", "") if isinstance(x, dict) else x).lower()
        ))
        listbox.delete(0, tk.END)
        nomi_per_combo = []
        gestore_partecipa = self._gestore_partecipa()
        nomi_esistenti = [_get_nome(p) for p in self.nomi_partecipanti]
        if gestore_partecipa and NOME_GESTORE not in nomi_esistenti:
            nomi_per_combo.append(f"👤 {NOME_GESTORE}")
        for p in self.nomi_partecipanti:
            nome = p.get("nome", p) if isinstance(p, dict) else p
            tipo = p.get("tipo", "persona") if isinstance(p, dict) else "persona"
            ico = "🏠" if tipo == "contenitore" else ("⚖️" if tipo == "personale" else "👤")
            nomi_per_combo.append(f"{ico} {nome}")
            listbox.insert(tk.END, _nomi_display(p))
        nuovi_valori = [""] + nomi_per_combo + ["⚙️ Gestisci Partecipanti"]
        if hasattr(self, 'partecipante_combobox'):
            self.partecipante_combobox["values"] = nuovi_valori
        if hasattr(self, 'ric_partecipante_combobox'):
            self.ric_partecipante_combobox["values"] = nuovi_valori
        if target_popup and hasattr(target_popup, 'calcola'):
            target_popup.calcola()
    add_frame = ttk.Frame(f)
    add_frame.pack(fill=tk.X, pady=(0, 4))
    riga_entry = ttk.Frame(add_frame)
    riga_entry.pack(fill=tk.X, pady=(0, 4))
    nuovo_var = tk.StringVar()
    vcmd = (self.register(lambda s: len(s) <= 25), '%P')
    entry_nuovo = ttk.Entry(riga_entry, textvariable=nuovo_var, width=25,
                            validate="key", validatecommand=vcmd)
    entry_nuovo.pack(side=tk.LEFT, padx=(0, 6))
    entry_nuovo.focus_set()
    img_add = self.icone_gui.get("aggiungi")
    btn_add = ttk.Label(riga_entry, compound="left", image=img_add,
        text=" Aggiungi" if img_add else "Aggiungi",
        background=self.COLOR_WIDGET_BG, foreground=self.COLOR_RED,
        cursor="hand2", padding=(8, 4))
    btn_add.pack(side=tk.LEFT)
    btn_add.bind("<Button-1>", lambda e: aggiungi())
    entry_nuovo.bind("<Return>", lambda e: aggiungi())
    radio_f = ttk.Frame(add_frame)
    radio_f.pack(fill=tk.X, pady=(0, 2))
    tipo_var = tk.StringVar(value="persona")
    ttk.Radiobutton(radio_f, text="👤 Persona", variable=tipo_var,
                    value="persona", style="Custom.TRadiobutton").pack(side=tk.LEFT, padx=(0, 4))
    ttk.Radiobutton(radio_f, text="🏠 Contenitore", variable=tipo_var,
                    value="contenitore", style="Custom.TRadiobutton").pack(side=tk.LEFT, padx=(0, 6))
    ttk.Radiobutton(radio_f, text="⚖️ Personale", variable=tipo_var,
                    value="personale", style="Custom.TRadiobutton").pack(side=tk.LEFT, padx=(0, 6))
    soci_wrapper = ttk.Frame(f)
    lbl_titolo_soci = tk.Label(soci_wrapper, text="",
                               bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                               font=("Arial", 9, "bold"))
    lbl_titolo_soci.pack(anchor="w", padx=2)
    canvas_soci = tk.Canvas(soci_wrapper, bg=self.COLOR_TOPLEVEL,
                            highlightthickness=0, height=100, width=350)
    scrollbar_soci = ttk.Scrollbar(soci_wrapper, orient="vertical",
                                   command=canvas_soci.yview)
    canvas_soci.configure(yscrollcommand=scrollbar_soci.set)
    soci_container = tk.Frame(canvas_soci, bg=self.COLOR_TOPLEVEL)
    finestra_id = canvas_soci.create_window((0, 0), window=soci_container, anchor="nw")
    def reset_scroll(e):
        canvas_soci.configure(scrollregion=canvas_soci.bbox("all"))
        if canvas_soci.winfo_width() > 1:
            canvas_soci.itemconfig(finestra_id, width=canvas_soci.winfo_width())
    soci_container.bind("<Configure>", reset_scroll)
    scrollbar_soci.pack(side=tk.RIGHT, fill=tk.Y)
    canvas_soci.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    salva_soci_frame = ttk.Frame(f)
    img_salva = self.icone_gui.get("salva")
    img_ann   = self.icone_gui.get("reset")
    btn_salva_soci = ttk.Label(salva_soci_frame, compound="left", image=img_salva,
                               text=" Salva Soci" if img_salva else "Salva Soci",
                               background=self.COLOR_WIDGET_BG, foreground="#98C379",
                               cursor="hand2", padding=(8, 4),
                               font=("Arial", 9, "bold"))
    btn_salva_soci.pack(side=tk.LEFT, padx=2)
    btn_annulla_soci = ttk.Label(salva_soci_frame, compound="left", image=img_ann,
                                 text=" Annulla" if img_ann else "Annulla",
                                 background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                                 cursor="hand2", padding=(8, 4))
    btn_annulla_soci.pack(side=tk.LEFT, padx=2)
    check_vars = {}
    def aggiorna_soci_ui(soci_correnti=None, readonly=False):
        for w in soci_container.winfo_children():
            w.destroy()
        check_vars.clear()
        NOME_GESTORE = os.path.basename(os.getcwd())
        persone = [p for p in self.nomi_partecipanti
                   if (isinstance(p, dict) and p.get("tipo") == "persona") or isinstance(p, str)]
        gestore_partecipa = self._gestore_partecipa()
        nomi_esistenti = [_get_nome(p) for p in persone]
        if gestore_partecipa and NOME_GESTORE not in nomi_esistenti:
            persone = [{"nome": NOME_GESTORE, "tipo": "persona"}] + persone
        r, c = 0, 0
        for p in persone:
            nome = _get_nome(p)
            v = tk.BooleanVar(value=(nome in soci_correnti) if soci_correnti else True)
            check_vars[nome] = v
            state = "disabled" if readonly else "normal"
            cb = tk.Checkbutton(soci_container, text=nome, variable=v,
                                bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                                selectcolor=self.COLOR_WIDGET_BG,
                                activebackground=self.COLOR_TOPLEVEL,
                                activeforeground=self.TEXT_COLOR,
                                font=("Arial", 9), state=state,
                                borderwidth=0, highlightthickness=0,
                                disabledforeground="#888888")
            cb.grid(row=r, column=c, sticky="w", padx=4, pady=2)
            c += 1
            if c > 2:
                c = 0; r += 1
        soci_container.update_idletasks()
    def mostra_soci(nome_contenitore, soci_correnti):
        _contenitore_in_modifica[0] = nome_contenitore
        lbl_titolo_soci.config(
            text=f"Soci di '{nome_contenitore}' — modifica e clicca Salva Soci:")
        aggiorna_soci_ui(soci_correnti, readonly=False)
        soci_wrapper.pack(fill=tk.X, pady=5)
        salva_soci_frame.pack(fill=tk.X, pady=(0, 4))
        soci_wrapper.update_idletasks()
        canvas_soci.configure(scrollregion=canvas_soci.bbox("all"))
    def nascondi_soci():
        _contenitore_in_modifica[0] = None
        soci_wrapper.pack_forget()
        salva_soci_frame.pack_forget()
    def salva_soci():
        nome_cont = _contenitore_in_modifica[0]
        if not nome_cont:
            return
        scelti = [n for n, v in check_vars.items() if v.get()]
        if not scelti:
            self.show_toast("Seleziona almeno una persona.")
            return
        for p in self.nomi_partecipanti:
            if isinstance(p, dict) and p.get("nome") == nome_cont:
                p["soci"] = scelti
                break
        with open(PARTECIPANTI, 'w', encoding='utf-8') as fp:
            json.dump({"gestore_partecipa": self._gestore_partecipa(),
                       "partecipanti": self.nomi_partecipanti}, fp, indent=2)
        self.show_toast(f"Soci di '{nome_cont}' aggiornati.")
        nascondi_soci()
        aggiorna_lista()
    btn_salva_soci.bind("<Button-1>", lambda e: salva_soci())
    btn_annulla_soci.bind("<Button-1>", lambda e: nascondi_soci())
    def toggle_soci(*args):
        if tipo_var.get() == "contenitore":
            lbl_titolo_soci.config(
                text="Seleziona chi partecipa a questo contenitore:")
            aggiorna_soci_ui(readonly=False)
            soci_wrapper.pack(fill=tk.X, pady=5)
            salva_soci_frame.pack_forget()
            soci_wrapper.update_idletasks()
            canvas_soci.configure(scrollregion=canvas_soci.bbox("all"))
        else:
            nascondi_soci()
    tipo_var.trace_add("write", toggle_soci)
    def on_select(event):
        sel = listbox.curselection()
        if not sel:
            return
        testo_riga = listbox.get(sel[0])
        nome_pulito = testo_riga
        for ico in ["🏠 ", "👤 ", "⚖️ "]:
            nome_pulito = nome_pulito.replace(ico, "")
        nome_pulito = nome_pulito.split(" (")[0].strip()
        p_selezionato = next(
            (p for p in self.nomi_partecipanti if _get_nome(p) == nome_pulito), None)
        if p_selezionato and isinstance(p_selezionato, dict):
            tipo = p_selezionato.get("tipo", "persona")
            tipo_var.set(tipo)
            if tipo == "contenitore":
                soci_salvati = p_selezionato.get("soci", [])
                mostra_soci(nome_pulito, soci_salvati)
            else:
                nascondi_soci()
        nuovo_var.set("")
    listbox.bind("<<ListboxSelect>>", on_select)
    def aggiungi():
        nome = nuovo_var.get().strip()
        if not nome:
            self.show_toast("Il campo Nome è obbligatorio.")
            return
        nomi_esistenti = [_get_nome(p) for p in self.nomi_partecipanti]
        if nome in nomi_esistenti:
            self.show_toast(f"'{nome}' è già presente.")
            return
        dati_p = {"nome": nome, "tipo": tipo_var.get()}
        if tipo_var.get() == "contenitore":
            scelti = [n for n, v in check_vars.items() if v.get()]
            if not scelti:
                self.show_toast("Seleziona almeno una persona.")
                return
            dati_p["soci"] = scelti
        self.nomi_partecipanti.append(dati_p)
        with open(PARTECIPANTI, 'w', encoding='utf-8') as fp:
            json.dump({"gestore_partecipa": self._gestore_partecipa(),
                       "partecipanti": self.nomi_partecipanti}, fp, indent=2)
        nuovo_var.set("")
        nascondi_soci()
        aggiorna_lista()
    def rimuovi():
        sel = listbox.curselection()
        if not sel:
            self.show_toast("Attenzione: Seleziona un partecipante da rimuovere.")
            return
        testo_riga = listbox.get(sel[0])
        nome_da_rimuovere = testo_riga[2:].split(" (")[0].strip()
        for i, p in enumerate(self.nomi_partecipanti):
            nome_p = p.get("nome", p) if isinstance(p, dict) else p
            if nome_p == nome_da_rimuovere:
                self.nomi_partecipanti.pop(i)
                break
        with open(PARTECIPANTI, 'w', encoding='utf-8') as fp:
            json.dump({"gestore_partecipa": self._gestore_partecipa(),
                       "partecipanti": self.nomi_partecipanti}, fp, indent=2)
        if nome_da_rimuovere in self.partecipante_var.get():
            self.partecipante_var.set("")
        nuovo_var.set("")
        nascondi_soci()
        aggiorna_lista()
        listbox.focus_set()
    listbox.bind("<Delete>", lambda e: rimuovi())
    aggiorna_lista()
    btn_frame = ttk.Frame(f)
    btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(4, 0))
    _nome_gest = os.path.basename(os.getcwd())
    var_gest_part = tk.BooleanVar(value=_leggi_gestore_partecipa())
    def _salva_gestore_e_chiudi():
        _scrivi_gestore_partecipa(var_gest_part.get())
        dialogo.destroy()

    gest_cb = ttk.Checkbutton(btn_frame,
                              text=f"'{_nome_gest}' partecipa alle spese condivise",
                              variable=var_gest_part)
    gest_cb.pack(side=tk.LEFT, padx=(0, 10))
    img_del = self.icone_gui.get("cancella")
    btn_del = ttk.Label(btn_frame, compound="left", image=img_del,
                        text=" Rimuovi" if img_del else "Rimuovi",
                        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                        cursor="hand2", padding=(8, 4))
    btn_del.pack(side=tk.LEFT)
    btn_del.bind("<Button-1>", lambda e: rimuovi())
    img_fs = self.icone_gui.get("saldo")
    btn_fs = ttk.Label(btn_frame, compound="left", image=img_fs,
                       text=" FairShare" if img_fs else "FairShare",
                       background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                       cursor="hand2", padding=(8, 4))
    btn_fs.pack(side=tk.LEFT, padx=4)
    btn_fs.bind("<Button-1>", lambda e: self.mostra_dare_avere())
    img_chiudi = self.icone_gui.get("chiudi")
    btn_chiudi = ttk.Label(btn_frame, compound="left", image=img_chiudi,
                           text=" Chiudi" if img_chiudi else "Chiudi",
                           background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                           cursor="hand2", padding=(8, 4))
    btn_chiudi.pack(side=tk.RIGHT)
    btn_chiudi.bind("<Button-1>", lambda e: _salva_gestore_e_chiudi())
    dialogo.bind("<Escape>", lambda e: _salva_gestore_e_chiudi())
