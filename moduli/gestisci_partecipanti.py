#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import tkinter as tk
from tkinter import ttk

def _fmt_pct(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return s if s else "0"

def gestisci_partecipanti(self, target_popup=None):
    import __main__ as _app
    PARTECIPANTI = _app.PARTECIPANTI
    _leggi_gestore_partecipa = _app._leggi_gestore_partecipa
    _scrivi_gestore_partecipa = _app._scrivi_gestore_partecipa

    if hasattr(self, '_gestione_popup') and self._gestione_popup and self._gestione_popup.winfo_exists():
        self._gestione_popup.lift()
        self._gestione_popup.focus_force()
        return

    def _salva_partecipanti_json():
        _gp_val = _leggi_gestore_partecipa()
        payload = {"gestore_partecipa": _gp_val, "partecipanti": self.nomi_partecipanti}
        tmp_path = PARTECIPANTI + ".tmp"
        try:
            with open(tmp_path, 'w', encoding='utf-8') as fp:
                json.dump(payload, fp, indent=2)
            os.replace(tmp_path, PARTECIPANTI)
            return True
        except Exception as e:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
            self.show_toast(f"Errore salvataggio partecipanti: {e}")
            return False

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
                    target_popup.lift()
                    target_popup.focus_force()
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
            icona = "CNT·" if tipo == "contenitore" else ("CTP·" if tipo == "personale" else "PER·")
            info = f" ({len(_soci_effettivi(p))} soci)" if tipo == "contenitore" else ""
            return f"{icona} {nome}{info}"
        return f"PER· {p}"
    def _get_nome(p):
        return p.get("nome", p) if isinstance(p, dict) else p
    def _soci_effettivi(p):
        _pa = getattr(_app, "PROFILO_ATTIVO", "Principale")
        _gest = _pa if _pa != "Principale" else os.path.basename(os.getcwd())
        validi = {_get_nome(x) for x in self.nomi_partecipanti
                  if isinstance(x, dict) and x.get("tipo", "persona") == "persona"}
        if _leggi_gestore_partecipa():
            validi.add(_gest)
        return [n for n in p.get("soci", []) if n in validi]
    def aggiorna_lista():
        _profilo_attivo_gp = getattr(_app, "PROFILO_ATTIVO", "Principale")
        NOME_GESTORE = _profilo_attivo_gp if _profilo_attivo_gp != "Principale" else os.path.basename(os.getcwd())
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
            nomi_per_combo.append(f"PER· {NOME_GESTORE}")
        for p in self.nomi_partecipanti:
            nome = p.get("nome", p) if isinstance(p, dict) else p
            tipo = p.get("tipo", "persona") if isinstance(p, dict) else "persona"
            ico = "CNT·" if tipo == "contenitore" else ("CTP·" if tipo == "personale" else "PER·")
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
    ttk.Radiobutton(radio_f, text="PER· Persona", variable=tipo_var,
                    value="persona", style="Custom.TRadiobutton").pack(side=tk.LEFT, padx=(0, 4))
    ttk.Radiobutton(radio_f, text="CNT· Contenitore", variable=tipo_var,
                    value="contenitore", style="Custom.TRadiobutton").pack(side=tk.LEFT, padx=(0, 6))
    ttk.Radiobutton(radio_f, text="CTP· Personale", variable=tipo_var,
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
        _profilo_attivo_gp = getattr(_app, "PROFILO_ATTIVO", "Principale")
        NOME_GESTORE = _profilo_attivo_gp if _profilo_attivo_gp != "Principale" else os.path.basename(os.getcwd())
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
        _salva_partecipanti_json()
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
        p_selezionato = self.nomi_partecipanti[sel[0]]
        nome_pulito = _get_nome(p_selezionato)
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
        _salva_partecipanti_json()
        nuovo_var.set("")
        nascondi_soci()
        aggiorna_lista()
    def rimuovi():
        sel = listbox.curselection()
        if not sel:
            self.show_toast("Attenzione: Seleziona un partecipante da rimuovere.")
            return
        nome_da_rimuovere = _get_nome(self.nomi_partecipanti[sel[0]])
        self.nomi_partecipanti.pop(sel[0])
        gruppi_vuoti = []
        for p in self.nomi_partecipanti:
            if isinstance(p, dict) and p.get("tipo") == "contenitore" and nome_da_rimuovere in p.get("soci", []):
                p["soci"] = [s for s in p["soci"] if s != nome_da_rimuovere]
                if not p["soci"]:
                    gruppi_vuoti.append(p.get("nome", ""))
        _salva_partecipanti_json()
        if gruppi_vuoti:
            self.show_toast(f"Gruppo senza soci: {', '.join(gruppi_vuoti)}. Aggiungi almeno un socio.")
        valore_corrente = self.partecipante_var.get()
        nome_corrente = valore_corrente.split(" ", 1)[1].strip() if " " in valore_corrente else valore_corrente
        if nome_corrente == nome_da_rimuovere:
            self.partecipante_var.set("")
        nuovo_var.set("")
        nascondi_soci()
        aggiorna_lista()
        listbox.focus_set()
    listbox.bind("<Delete>", lambda e: rimuovi())
    def apri_percentuali():
        _profilo_attivo_gp = getattr(_app, "PROFILO_ATTIVO", "Principale")
        NOME_GESTORE = _profilo_attivo_gp if _profilo_attivo_gp != "Principale" else os.path.basename(os.getcwd())
        gestore_partecipa = self._gestore_partecipa()
        persone = [p for p in self.nomi_partecipanti
                   if isinstance(p, dict) and p.get("tipo", "persona") == "persona"]
        nomi_esistenti = [p.get("nome") for p in persone]
        gest_dict = None
        if gestore_partecipa and NOME_GESTORE not in nomi_esistenti:
            gest_dict = {"nome": NOME_GESTORE, "tipo": "persona"}
            persone = persone + [gest_dict]
        if len(persone) < 2:
            self.show_toast("Servono almeno due persone per impostare le percentuali.")
            return
        persone = sorted(persone, key=lambda p: p.get("nome", "").lower())
        pop = tk.Toplevel(dialogo)
        pop.title("FairShare - Percentuali di Ripartizione")
        pop.resizable(False, False)
        pop.withdraw()
        pop.configure(bg=self.COLOR_TOPLEVEL)
        pop.transient(dialogo)
        RIGHE_VISIBILI = min(len(persone), 8)
        w2 = 406
        h2 = 140 + 34 * RIGHE_VISIBILI
        x2 = dialogo.winfo_rootx() + (dialogo.winfo_width() // 2) - (w2 // 2)
        y2 = dialogo.winfo_rooty() + (dialogo.winfo_height() // 2) - (h2 // 2)
        pop.geometry(f"{w2}x{h2}+{x2}+{y2}")
        pop.deiconify()
        pop.lift()
        pop.focus_force()
        pop.grab_set()
        fp2 = ttk.Frame(pop, padding=11)
        fp2.pack(fill=tk.BOTH, expand=True)
        ttk.Label(fp2, text="Percentuale fissa per persona:",
                  font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 2))
        ttk.Label(fp2, text="Lascia vuoto per dividere in parti uguali il resto.",
                  font=("Arial", 8)).pack(anchor="w", pady=(0, 8))
        area = ttk.Frame(fp2)
        area.pack(fill=tk.BOTH, expand=False)
        border_frame = tk.Frame(area, bg="#5a5a5a", bd=1)
        border_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas_pct = tk.Canvas(border_frame, height=34 * RIGHE_VISIBILI,
                               bg=self.COLOR_WIDGET_BG, highlightthickness=0, bd=0)
        scroll_pct = ttk.Scrollbar(area, orient="vertical", command=canvas_pct.yview,
                                   style="Vertical.TScrollbar")
        righe_pct = ttk.Frame(canvas_pct)
        window_id = canvas_pct.create_window((0, 0), window=righe_pct, anchor="nw")
        def _on_canvas_configure(event):
            canvas_pct.itemconfig(window_id, width=event.width)
            canvas_pct.configure(scrollregion=canvas_pct.bbox("all"))
        canvas_pct.bind("<Configure>", _on_canvas_configure)
        righe_pct.bind("<Configure>", lambda e: canvas_pct.configure(scrollregion=canvas_pct.bbox("all")))
        def _scroll_pct(event):
            canvas_pct.yview_scroll(-1 * (event.delta // 120) if event.delta else 0, "units")
            return "break"
        def _bind_recursive(widget):
            widget.bind("<MouseWheel>", _scroll_pct)
            widget.bind("<Button-4>", lambda e: (canvas_pct.yview_scroll(-1, "units"), "break")[1])
            widget.bind("<Button-5>", lambda e: (canvas_pct.yview_scroll(1, "units"), "break")[1])
            for child in widget.winfo_children():
                _bind_recursive(child)
        for _w in (border_frame, canvas_pct, righe_pct):
            _w.bind("<MouseWheel>", _scroll_pct)
            _w.bind("<Button-4>", lambda e: (canvas_pct.yview_scroll(-1, "units"), "break")[1])
            _w.bind("<Button-5>", lambda e: (canvas_pct.yview_scroll(1, "units"), "break")[1])
            
        canvas_pct.configure(yscrollcommand=scroll_pct.set)
        canvas_pct.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_pct.pack(side=tk.RIGHT, fill=tk.Y)
        vcmd_pct = (self.register(lambda s: s == "" or (s.replace(",", ".").replace(".", "", 1).isdigit()
                    and 0 <= float(s.replace(",", ".") or 0) <= 100)), '%P')
        vars_pct = {}
        for p in persone:
            nome = p.get("nome")
            riga = ttk.Frame(righe_pct)
            riga.pack(fill=tk.X, pady=3)
            ttk.Label(riga, text=nome, width=18).pack(side=tk.LEFT)
            v = tk.StringVar()
            pct_esistente = p.get("percentuale")
            if pct_esistente is not None:
                v.set(_fmt_pct(pct_esistente))
            e = ttk.Entry(riga, textvariable=v, width=6, justify="right",
                          validate="key", validatecommand=vcmd_pct)
            e.pack(side=tk.LEFT)
            ttk.Label(riga, text="%").pack(side=tk.LEFT, padx=(3, 0))
            vars_pct[nome] = v
        _bind_recursive(righe_pct)
        lbl_tot = tk.Label(fp2, text="", bg=self.COLOR_TOPLEVEL,
                           font=("Arial", 9, "bold"))
        lbl_tot.pack(anchor="w", pady=(8, 4))
        def aggiorna_totale(*args):
            tot = 0.0
            tutti_compilati = True
            for v in vars_pct.values():
                s = v.get().strip().replace(",", ".")
                if s == "":
                    tutti_compilati = False
                else:
                    try:
                        tot += float(s)
                    except ValueError:
                        pass
            if tot > 100.0:
                lbl_tot.config(text=f"Totale impostato: {_fmt_pct(tot)}% (Attenzione: supera il 100%!)",
                               fg="#ff4444")
            elif tutti_compilati and abs(tot - 100.0) > 0.01:
                lbl_tot.config(text=f"Totale impostato: {_fmt_pct(tot)}% (Deve essere esattamente 100%)",
                               fg="#ff4444")
            else:
                lbl_tot.config(text=f"Totale impostato: {_fmt_pct(tot)}% (il resto si divide in parti uguali)",
                               fg=self.TEXT_COLOR)
        for v in vars_pct.values():
            v.trace_add("write", aggiorna_totale)
        aggiorna_totale()
        def salva_percentuali():
            valori = {}
            totale_corrente = 0.0
            for nome, v in vars_pct.items():
                s = v.get().strip().replace(",", ".")
                if s:
                    try:
                        val = float(s)
                        if val < 0 or val > 100:
                            self.show_toast(f"Valore non valido per {nome}.")
                            return
                        valori[nome] = val
                        totale_corrente += val
                    except ValueError:
                        self.show_toast(f"Percentuale non valida per {nome}.")
                        return
            if valori:
                if abs(totale_corrente - 100.0) > 0.01:
                    self.show_toast(f"Il totale delle percentuali è {totale_corrente:.1f}%: deve essere esattamente 100%.")
                    return
            if gest_dict is not None and gest_dict not in self.nomi_partecipanti and _leggi_gestore_partecipa():
                self.nomi_partecipanti.append(gest_dict)
            for p in self.nomi_partecipanti:
                if isinstance(p, dict) and p.get("nome") in vars_pct:
                    nome = p.get("nome")
                    if nome in valori:
                        p["percentuale"] = valori[nome]
                    else:
                        p.pop("percentuale", None)
            _salva_partecipanti_json()
            self.show_toast("Percentuali salvate.")
            pop.destroy()
        def azzera_percentuali():
            for v in vars_pct.values():
                v.set("")
        btn_row = ttk.Frame(fp2)
        btn_row.pack(fill=tk.X, pady=(6, 0))
        img_salva2 = self.icone_gui.get("salva")
        b_salva = ttk.Label(btn_row, compound="left", image=img_salva2,
                            text=" Salva" if img_salva2 else "Salva",
                            background=self.COLOR_WIDGET_BG, foreground="#98C379",
                            cursor="hand2", padding=(8, 4), font=("Arial", 9, "bold"))
        b_salva.pack(side=tk.LEFT, padx=2)
        b_salva.bind("<Button-1>", lambda e: salva_percentuali())
        img_azzera = self.icone_gui.get("reset")
        b_azzera = ttk.Label(btn_row, compound="left" if img_azzera else "none", image=img_azzera,
                             text=" Reset a parti uguali" if img_azzera else "Reset a parti uguali",
                             background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                             cursor="hand2", padding=(8, 4), anchor="center")
        b_azzera.pack(side=tk.LEFT, padx=2, expand=True)
        b_azzera.bind("<Button-1>", lambda e: azzera_percentuali())
        img_ann2 = self.icone_gui.get("chiudi")
        b_ann = ttk.Label(btn_row, compound="left", image=img_ann2,
                          text=" Chiudi" if img_ann2 else "Chiudi",
                          background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                          cursor="hand2", padding=(8, 4))
        b_ann.pack(side=tk.RIGHT, padx=2)
        b_ann.bind("<Button-1>", lambda e: pop.destroy())
        pop.bind("<Escape>", lambda e: pop.destroy())
        def _on_pop_destroy(e):
            if e.widget is not pop:
                return
            try:
                if dialogo.winfo_exists():
                    dialogo.grab_set()
            except Exception:
                pass
        pop.bind("<Destroy>", _on_pop_destroy)
    aggiorna_lista()
    btn_frame = ttk.Frame(f)
    btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(4, 0))
    _profilo_attivo_gp = getattr(_app, "PROFILO_ATTIVO", "Principale")
    _nome_gest = _profilo_attivo_gp if _profilo_attivo_gp != "Principale" else os.path.basename(os.getcwd())
    var_gest_part = tk.BooleanVar(value=_leggi_gestore_partecipa())
    def _salva_gestore_e_chiudi():
        _scrivi_gestore_partecipa(var_gest_part.get())
        dialogo.destroy()
    dialogo.protocol("WM_DELETE_WINDOW", _salva_gestore_e_chiudi)
    def _on_gestore_toggle():
        _scrivi_gestore_partecipa(var_gest_part.get())
        aggiorna_lista()
        if soci_wrapper.winfo_ismapped():
            attuali = [n for n, v in check_vars.items() if v.get()]
            aggiorna_soci_ui(attuali or None, readonly=False)
    gest_cb = ttk.Checkbutton(btn_frame,
                              text=f"'{_nome_gest}' partecipa alle spese condivise",
                              variable=var_gest_part,
                              command=_on_gestore_toggle)
    gest_cb.pack(side=tk.LEFT, padx=(0, 10))
    img_del = self.icone_gui.get("cancella")
    btn_del = ttk.Label(btn_frame, compound="left", image=img_del,
                        text=" Rimuovi" if img_del else "Rimuovi",
                        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                        cursor="hand2", padding=(8, 4))
    btn_del.pack(side=tk.LEFT)
    btn_del.bind("<Button-1>", lambda e: rimuovi())
    btn_pct = ttk.Label(btn_frame, text=" % Percentuali",
                        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                        cursor="hand2", padding=(8, 4))
    btn_pct.pack(side=tk.LEFT, padx=4)
    btn_pct.bind("<Button-1>", lambda e: apri_percentuali())
    img_fs = self.icone_gui.get("saldo")
    btn_fs = ttk.Label(btn_frame, compound="left", image=img_fs,
                       text=" FairShare" if img_fs else "FairShare",
                       background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                       cursor="hand2", padding=(8, 4))
    btn_fs.pack(side=tk.LEFT, padx=4)
    btn_fs.bind("<Button-1>", lambda e: (_salva_gestore_e_chiudi(), self.mostra_dare_avere()))
    img_chiudi = self.icone_gui.get("chiudi")
    btn_chiudi = ttk.Label(btn_frame, compound="left", image=img_chiudi,
                           text=" Chiudi" if img_chiudi else "Chiudi",
                           background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                           cursor="hand2", padding=(8, 4))
    btn_chiudi.pack(side=tk.RIGHT)
    btn_chiudi.bind("<Button-1>", lambda e: _salva_gestore_e_chiudi())
    dialogo.bind("<Escape>", lambda e: _salva_gestore_e_chiudi())
    
