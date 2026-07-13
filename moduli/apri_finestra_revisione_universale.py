#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk

from moduli.modello_spesa import SpesaEntry, METODI_PAGAMENTO

def apri_finestra_revisione_universale(self, movimenti):
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    LOG_IMPORTAZIONI = _app.LOG_IMPORTAZIONI
    MEM_CAT = _app.MEM_CAT
    from datetime import datetime
    import json
    movimenti.sort(key=lambda m: m["data"])
    if not hasattr(self, "memoria_descrizioni_categoria"):
        self.memoria_descrizioni_categoria = {}
    memoria = self.memoria_descrizioni_categoria
    win = tk.Toplevel(self)
    win.resizable(True, True)
    win.title("Revisione Movimenti IA Gemini")
    win.configure(background=self.COLOR_WIDGET_BG)
    win.minsize(1366, 630)
    larghezza, altezza = 1366, 630
    x = (win.winfo_screenwidth() // 2) - (larghezza // 2)
    y = (win.winfo_screenheight() // 2) - (altezza // 2)
    win.geometry(f"{larghezza}x{altezza}+{x}+{y}")
    bar_cat = tk.Frame(win, background=self.COLOR_WIDGET_BG)
    bar_cat.pack(fill="x", padx=10, pady=(8, 2))
    ttk.Label(bar_cat, text="Nuova categoria:").pack(side="left", padx=(0, 4))
    var_nuova_cat = tk.StringVar()
    entry_nuova_cat = ttk.Entry(bar_cat, textvariable=var_nuova_cat, width=25)
    entry_nuova_cat.pack(side="left")
    righe = []
    try:
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
            _db_portafoglio = json.load(_pf)
        _conti_rev = [c.get("nome", "?") for c in _db_portafoglio.get("conti", [])]
        _conto_principale = next((c.get("nome","") for c in _db_portafoglio.get("conti",[]) if c.get("principale")), "(nessuno)")
    except Exception:
        _conti_rev = []
        _conto_principale = "(nessuno)"
    def aggiungi_categoria():
        nome = var_nuova_cat.get().strip()
        if not nome:
            return
        if nome in self.categorie:
            self.show_toast(f"Categoria «{nome}» esiste già.", parent=win)
            return
        self.categorie.append(nome)
        self.categorie_tipi[nome] = "Uscita"
        var_nuova_cat.set("")
        for _, _, _, _, _, _, combo, _, _, _ in righe:
            combo["values"] = self.categorie
        self.aggiorna_combobox_categorie()
        self.show_toast(f"Creata categoria «{nome}»", parent=win)
    img_add = self.icone_gui.get("aggiungi")
    btn_add = tk.Label(bar_cat, compound="left", image=img_add,
                       text=" Aggiungi" if img_add else "Aggiungi",
                       background=self.COLOR_WIDGET_BG, foreground=self.COLOR_RED,
                       cursor="hand2", font=("Arial", 9, "bold"))
    btn_add.pack(side="left", padx=8)
    btn_add.bind("<Button-1>", lambda e: aggiungi_categoria())
    entry_nuova_cat.bind("<Return>", lambda e: aggiungi_categoria())
    ttk.Label(bar_cat, text="Conto per tutti:").pack(side="left", padx=(20, 4))
    var_conto_bulk = tk.StringVar(value=_conto_principale)
    combo_conto_bulk = ttk.Combobox(bar_cat, textvariable=var_conto_bulk,
                                    values=["(nessuno)"] + _conti_rev,
                                    state="readonly", width=14, style="Border.TCombobox")
    combo_conto_bulk.pack(side="left")
    def applica_conto_a_tutti():
        valore = var_conto_bulk.get()
        for _, _, _, _, _, _, _, combo_conto, _, _ in righe:
            combo_conto.set(valore)
        self.show_toast(f"Conto «{valore}» applicato a tutte le righe.", parent=win)
    img_applica = self.icone_gui.get("aggiorna") or self.icone_gui.get("salva")
    btn_applica_conto = tk.Label(bar_cat, compound="left", image=img_applica,
                                 text=" Applica" if img_applica else "Applica",
                                 background=self.COLOR_WIDGET_BG, foreground=self.COLOR_RED,
                                 cursor="hand2", font=("Arial", 9, "bold"))
    btn_applica_conto.pack(side="left", padx=8)
    btn_applica_conto.bind("<Button-1>", lambda e: applica_conto_a_tutti())
    ttk.Label(bar_cat, text="Tag per tutti:").pack(side="left", padx=(20, 4))
    var_tag_bulk = tk.StringVar()
    entry_tag_bulk = ttk.Entry(bar_cat, textvariable=var_tag_bulk, width=18)
    entry_tag_bulk.pack(side="left")
    def applica_tag_a_tutti():
        valore = var_tag_bulk.get()
        for _, _, _, _, _, _, _, _, var_tag, _ in righe:
            var_tag.set(valore)
        self.show_toast("Tag applicati a tutte le righe.", parent=win)
    img_applica_tag = self.icone_gui.get("aggiorna") or self.icone_gui.get("salva")
    btn_applica_tag = tk.Label(bar_cat, compound="left", image=img_applica_tag,
                               text=" Applica" if img_applica_tag else "Applica",
                               background=self.COLOR_WIDGET_BG, foreground=self.COLOR_RED,
                               cursor="hand2", font=("Arial", 9, "bold"))
    btn_applica_tag.pack(side="left", padx=8)
    btn_applica_tag.bind("<Button-1>", lambda e: applica_tag_a_tutti())
    ttk.Label(bar_cat, text="Metodo per tutti:").pack(side="left", padx=(20, 4))
    var_metodo_bulk = tk.StringVar()
    combo_metodo_bulk = ttk.Combobox(bar_cat, textvariable=var_metodo_bulk,
                                     values=[""] + METODI_PAGAMENTO,
                                     state="readonly", width=13, style="Border.TCombobox")
    combo_metodo_bulk.pack(side="left")
    def applica_metodo_a_tutti():
        valore = var_metodo_bulk.get()
        for _, _, _, _, _, _, _, _, _, combo_metodo in righe:
            combo_metodo.set(valore)
        self.show_toast(f"Metodo «{valore}» applicato a tutte le righe.", parent=win)
    img_applica_metodo = self.icone_gui.get("aggiorna") or self.icone_gui.get("salva")
    btn_applica_metodo = tk.Label(bar_cat, compound="left", image=img_applica_metodo,
                                  text=" Applica" if img_applica_metodo else "Applica",
                                  background=self.COLOR_WIDGET_BG, foreground=self.COLOR_RED,
                                  cursor="hand2", font=("Arial", 9, "bold"))
    btn_applica_metodo.pack(side="left", padx=8)
    btn_applica_metodo.bind("<Button-1>", lambda e: applica_metodo_a_tutti())
    ttk.Separator(win, orient="horizontal").pack(fill="x", padx=10, pady=2)
    COL_MINSIZE = [30, 100, 650, 90, 150, 110, 110, 100]
    def _allinea_colonne(frame):
        for _i, _larg in enumerate(COL_MINSIZE):
            frame.grid_columnconfigure(_i, minsize=_larg, weight=(1 if _i == 2 else 0))
    header = tk.Frame(win, background=self.COLOR_WIDGET_BG)
    header.pack(fill="x", padx=10)
    _allinea_colonne(header)
    seleziona_tutti_var = tk.BooleanVar(value=True)
    def toggle_tutti():
        for _, var_check, _, _, _, _, _, _, _, _ in righe:
            var_check.set(seleziona_tutti_var.get())
    chk_header = ttk.Checkbutton(header, variable=seleziona_tutti_var, command=toggle_tutti)
    chk_header.grid(row=0, column=0, padx=4, sticky="w", ipadx=4)
    tk.Label(header, text="Data", width=8, anchor="w",
             background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
             font=("Arial", 9, "bold")).grid(row=0, column=1, padx=4, sticky="w")
    tk.Label(header, text="Descrizione", width=48, anchor="w",
             background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
             font=("Arial", 9, "bold")).grid(row=0, column=2, padx=4, sticky="w")
    tk.Label(header, text="Importo €", width=9, anchor="w",
             background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
             font=("Arial", 9, "bold")).grid(row=0, column=3, padx=4, sticky="w")
    tk.Label(header, text="Categoria", width=15, anchor="w",
             background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
             font=("Arial", 9, "bold")).grid(row=0, column=4, padx=4, sticky="w")
    tk.Label(header, text="Conto", width=11, anchor="w",
             background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
             font=("Arial", 9, "bold")).grid(row=0, column=5, padx=4, sticky="w")
    tk.Label(header, text="Tag", width=11, anchor="w",
             background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
             font=("Arial", 9, "bold")).grid(row=0, column=6, padx=4, sticky="w")
    tk.Label(header, text="Metodo", width=10, anchor="w",
             background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
             font=("Arial", 9, "bold")).grid(row=0, column=7, padx=4, sticky="w")
    ttk.Separator(win, orient="horizontal").pack(fill="x", padx=10, pady=2)
    frame_scroll = tk.Frame(win, background=self.COLOR_WIDGET_BG)
    frame_scroll.pack(fill="both", expand=True, padx=10)
    canvas = tk.Canvas(frame_scroll, highlightthickness=0,
                       background=self.COLOR_WIDGET_BG)
    sb_scroll = ttk.Scrollbar(frame_scroll, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=sb_scroll.set)
    canvas.pack(side="left", fill="both", expand=True)
    sb_scroll.pack(side="right", fill="y")
    area = tk.Frame(canvas, background=self.COLOR_WIDGET_BG)
    canvas.create_window((0, 0), window=area, anchor="nw")
    area.bind("<Configure>", lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")))
    def on_mousewheel(event):
            try:
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except:
                    pass
    canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", on_mousewheel))
    canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
    area.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    img_cal = (self.icone_gui.get("calendario")
               or self.icone_gui.get("scadenze_B")
               or self.icone_gui.get("timer_B"))
    for mov in movimenti:
        riga = tk.Frame(area, background=self.COLOR_WIDGET_BG)
        riga.pack(fill="x", pady=1)
        _allinea_colonne(riga)
        var_check = tk.BooleanVar(value=True)
        ttk.Checkbutton(riga, variable=var_check).grid(row=0, column=0, padx=4, sticky="w")
        frame_data = tk.Frame(riga, background=self.COLOR_WIDGET_BG)
        frame_data.grid(row=0, column=1, padx=4, sticky="w")
        var_data = tk.StringVar(value=mov["data"].strftime("%d-%m-%Y"))
        entry_data = ttk.Entry(frame_data, textvariable=var_data, width=8)
        entry_data.pack(side="left")
        btn_cal = tk.Label(frame_data,
                           image=img_cal if img_cal else None,
                           text="" if img_cal else "📅",
                           background=self.COLOR_WIDGET_BG, cursor="hand2")
        btn_cal.pack(side="left", padx=(2, 0))
        btn_cal.bind("<Button-1>", lambda e, w=entry_data, v=var_data:
                     self.mostra_calendario_popup(w, v))
        var_desc = tk.StringVar(value=mov["descrizione"])
        entry_desc = ttk.Entry(riga, textvariable=var_desc, width=48)
        entry_desc.grid(row=0, column=2, padx=4, sticky="ew")
        var_imp = tk.StringVar(value=f"{mov['importo']:.2f}")
        entry_imp = ttk.Entry(riga, textvariable=var_imp, width=9)
        entry_imp.grid(row=0, column=3, padx=4, sticky="w")
        combo = ttk.Combobox(riga, values=self.categorie, state="readonly",
                             width=15, style="Border.TCombobox")
        cat_ia = mov.get("categoria", "")
        cat_finale = (memoria.get(mov["descrizione"].strip().upper())
                      or (cat_ia if cat_ia in self.categorie else "")
                      or "Generica")
        combo.set(cat_finale)
        combo.grid(row=0, column=4, padx=4, sticky="w")
        combo_conto = ttk.Combobox(riga, values=["(nessuno)"] + _conti_rev,
                                   state="readonly", width=11, style="Border.TCombobox")
        combo_conto.set(_conto_principale)
        combo_conto.grid(row=0, column=5, padx=4, sticky="w")
        var_tag = tk.StringVar()
        entry_tag = ttk.Entry(riga, textvariable=var_tag, width=11)
        entry_tag.grid(row=0, column=6, padx=4, sticky="w")
        combo_metodo = ttk.Combobox(riga, values=[""] + METODI_PAGAMENTO,
                                    state="readonly", width=10, style="Border.TCombobox")
        combo_metodo.grid(row=0, column=7, padx=4, sticky="w")
        righe.append((mov, var_check, var_data, var_desc, var_imp, entry_data, combo, combo_conto, var_tag, combo_metodo))
    ttk.Separator(win, orient="horizontal").pack(fill="x", padx=10, pady=4)
    bar_btn = tk.Frame(win, background=self.COLOR_WIDGET_BG)
    bar_btn.pack(fill="x", padx=10, pady=(0, 10))
    lbl_count = tk.Label(bar_btn, text=f"{len(movimenti)} movimenti",
                         background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                         font=("Arial", 9))
    lbl_count.pack(side="left", padx=6)
    def salva():
        count, duplicati, errori = 0, 0, []
        for mov, var_check, var_data, var_desc, var_imp, entry_data, combo, combo_conto, var_tag, combo_metodo in righe:
            if not var_check.get():
                continue
            try:
                data_mov = datetime.strptime(var_data.get(), "%d-%m-%Y").date()
            except ValueError:
                errori.append(f"Data non valida: {var_data.get()}")
                continue
            try:
                importo = float(var_imp.get().replace(",", "."))
            except ValueError:
                errori.append(f"Importo non valido: {var_imp.get()}")
                continue
            desc = var_desc.get().strip()[:35]
            cat = combo.get() or "Generica"
            tipo = "Entrata" if importo >= 0 else "Uscita"
            gia_presente = any(
                abs(float(e[2])) == abs(importo) and
                str(e[3]) == tipo
                for e in self.spese.get(data_mov, [])
            )
            if gia_presente:
                duplicati += 1
                continue
            nome_conto_rev = combo_conto.get()
            conto_voce = nome_conto_rev if nome_conto_rev and nome_conto_rev != "(nessuno)" else ""
            tag_lista = self._normalizza_tags(var_tag.get())
            metodo_voce = combo_metodo.get()
            voce = SpesaEntry.nuova(cat, desc, abs(importo), tipo,
                                    conto=conto_voce, hashtag=tag_lista,
                                    metodo_pagamento=metodo_voce)
            self.spese.setdefault(data_mov, []).append(voce)
            self.memoria_descrizioni_categoria[desc.strip().upper()] = cat
            count += 1
            if nome_conto_rev and nome_conto_rev != "(nessuno)":
                try:
                    with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
                        _db_p = json.load(_pf)
                    for _c in _db_p.get("conti", []):
                        if _c.get("nome") == nome_conto_rev:
                            _segno = -1 if tipo == "Uscita" else 1
                            _c["saldo"] = round(float(_c.get("saldo", 0)) + _segno * abs(importo), 2)
                            _ids = {t.get("id", "") for t in _db_p.get("trasferimenti", [])}
                            _i = 1
                            while f"t{_i}" in _ids:
                                _i += 1
                            _db_p.setdefault("trasferimenti", []).append({
                                "id": f"t{_i}",
                                "data": data_mov.strftime("%d-%m-%Y"),
                                "da": _c["id"] if tipo == "Uscita" else "__spese__",
                                "a":  "__spese__" if tipo == "Uscita" else _c["id"],
                                "importo": round(abs(importo), 2),
                                "note": f"{cat} – {desc}".strip(" –")
                            })
                            break
                    with open(PORTAFOGLIO_BANCARIO, "w", encoding="utf-8") as _pf:
                        json.dump(_db_p, _pf, indent=2, ensure_ascii=False)
                except Exception as _ex:
                    print(f"[revisione_universale] Errore aggancio portafoglio: {_ex}")
            try:
                with open(LOG_IMPORTAZIONI, "a", encoding="utf-8") as log:
                    direzione = "Entrata" if importo >= 0 else "Uscita"
                    conto_log = nome_conto_rev if nome_conto_rev and nome_conto_rev != "(nessuno)" else "—"
                    log.write(
                        f"{datetime.now().strftime('%d/%m/%Y %H:%M'):<17} | "
                        f"{'IA':<8} | "
                        f"{data_mov.strftime('%d/%m/%Y'):<10} | "
                        f"{desc:<50} | "
                        f"{abs(importo):>10.2f} € | "
                        f"{direzione:<7} | "
                        f"{cat} | "
                        f"{conto_log}\n"
                    )
            except Exception as e:
                print(f"Errore log importazione: {e}")
        self.save_db()
        try:
            with open(MEM_CAT, "w", encoding="utf-8") as f:
                json.dump(self.memoria_descrizioni_categoria, f,
                          ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Errore scrittura memoria: {e}")
        self.refresh_gui()
        if count > 0:
            self.riproduci_beep()
        win.destroy()
        msg = f"{count} importati, {duplicati} duplicati ignorati."
        if errori:
            msg += f"\n⚠️ {len(errori)} righe saltate per errori."
        self.show_custom_info("Completato", msg)
    img_salva = self.icone_gui.get("salva")
    btn_salva = tk.Label(bar_btn, compound="left", image=img_salva,
                         text=" Salva" if img_salva else "Salva",
                         background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                         cursor="hand2", font=("Arial", 10, "bold"))
    btn_salva.pack(side="left", padx=20)
    btn_salva.bind("<Button-1>", lambda e: salva())

    img_chiudi = self.icone_gui.get("chiudi")
    btn_chiudi = tk.Label(bar_btn, compound="left", image=img_chiudi,
                          text=" Chiudi" if img_chiudi else "Chiudi",
                          background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                          cursor="hand2", font=("Arial", 10, "bold"))
    btn_chiudi.pack(side="right", padx=20)
    btn_chiudi.bind("<Button-1>", lambda e: win.destroy())        
 
