#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import datetime
import tkinter as tk
from tkinter import ttk, filedialog
from moduli.modello_spesa import campo, METODI_PAGAMENTO_EMOJI, metodo_pagamento_pulito
from moduli.mappa_conti_trasferimenti import costruisci_mappa_conti_da_trasferimenti, conto_da_mappa

MESI = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
TUTTI = ""

def _data_libera(s):
    s = str(s or "").strip().replace("/", "-").replace(".", "-")
    if not s:
        return None
    try:
        return datetime.datetime.strptime(s, "%d-%m-%Y").date()
    except Exception:
        return None

def _fmt_it(v, spec=",.2f"):
    s = format(v, spec)
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")

def cerca_operazioni(self):
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    EXPORT_FILES         = _app.EXPORT_FILES
    self.mostra_treeview_statistiche()
    larghezza, altezza = 1366, 600
    x = self.winfo_screenwidth() // 2 - larghezza // 2
    y = self.winfo_screenheight() // 2 - altezza // 2
    finestra = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    finestra.withdraw()
    self._finestra_cerca = finestra
    finestra.title("Ricerca operazioni")
    finestra.geometry(f"{larghezza}x{altezza}+{x}+{y}")
    finestra.minsize(larghezza, altezza)
    finestra.transient(self)
    finestra.bind("<Escape>", lambda e: finestra.destroy())
    frame_superiore = tk.Frame(finestra, bg=self.COLOR_TOPLEVEL)
    frame_superiore.pack(fill="x", pady=10, padx=10)
    tk.Label(
        frame_superiore,
        image=self.icone_gui.get("search"),
        text=" Ricerca:",
        compound="left",
        bg=self.COLOR_TOPLEVEL,
        fg=self.TEXT_COLOR,
        font=("Arial", 9, "bold")
    ).pack(side="left")
    campo_input = ttk.Entry(frame_superiore, width=22)
    campo_input.pack(side="left", padx=8)
    campo_input.focus_set()
    mostra_futuro_var = tk.BooleanVar(value=True)
    ttk.Checkbutton(frame_superiore, text="Includi Futuri", variable=mostra_futuro_var).pack(side="left", padx=(0, 8))
    img_mouse = self.icone_gui.get("mouse")
    lbl_hint = ttk.Label(
        frame_superiore,
        text="Doppio clic → Vai alla spesa sulla Dashboard  |  Clic destro → popola campi inserimento ",
        image=img_mouse,
        compound="right",
        foreground="gray",
        font=("Arial", 8, "italic")
    )
    if img_mouse:
        lbl_hint.image = img_mouse
    lbl_hint.pack(side=tk.RIGHT, padx=(10, 0))
    # --- Pannello filtri richiudibile (stessa logica di Analisi Categorie) ---
    bg_f = self.COLOR_TOPLEVEL
    _conti_f = [TUTTI]
    try:
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
            _conti_f += [c.get("nome", "?") for c in json.load(_pf).get("conti", [])]
    except Exception:
        pass
    _profilo_f = getattr(_app, "PROFILO_ATTIVO", "Principale")
    _gestore_f = _profilo_f if _profilo_f != "Principale" else os.path.basename(os.getcwd())
    _nomi_f = [(p.get("nome", "") if isinstance(p, dict) else p) for p in self.nomi_partecipanti] if getattr(self, "nomi_partecipanti", None) else []
    _partec_f = [TUTTI]
    if self._gestore_partecipa() and _gestore_f not in _nomi_f:
        _partec_f.append(f"PER· {_gestore_f}")
    if getattr(self, "nomi_partecipanti", None):
        _partec_f += [
            f"CTP· {p['nome']}" if p.get("tipo") == "personale" else
            f"CNT· {p['nome']}" if p.get("tipo") == "contenitore" else
            f"PER· {p['nome']}"
            for p in sorted(self.nomi_partecipanti, key=lambda p: p["nome"].lower())
        ]
    _anni_f = sorted({str(d.year if isinstance(d, datetime.date) else datetime.datetime.strptime(d, "%d-%m-%Y").year)
                      for d in self.spese}, reverse=True)
    f = {"tipo": tk.StringVar(value=TUTTI), "categoria": tk.StringVar(value=TUTTI),
         "anno": tk.StringVar(value=TUTTI), "mese": tk.StringVar(value=TUTTI),
         "partecipanti": tk.StringVar(value=TUTTI), "conto": tk.StringVar(value=TUTTI),
         "metodo": tk.StringVar(value=TUTTI), "tag": tk.StringVar(value=""),
         "testo": tk.StringVar(value=""), "imp_da": tk.StringVar(value=""), "imp_a": tk.StringVar(value=""),
         "da": tk.StringVar(value=""), "a": tk.StringVar(value="")}
    stato_f = {"aperta": False, "sosp": False, "job": None}
    head = tk.Frame(finestra, bg=bg_f)
    head.pack(fill="x", padx=10, pady=(0, 2))
    lbl_freccia = tk.Label(head, bg=bg_f, fg="#DC3545", cursor="hand2", font=("Arial", 11, "bold"), width=2)
    lbl_freccia.pack(side="left")
    lbl_head = tk.Label(head, bg=bg_f, fg=self.TEXT_COLOR, cursor="hand2", font=("Arial", 9, "bold"), anchor="w")
    lbl_head.pack(side="left")
    body = tk.Frame(finestra, bg=bg_f)
    def _riga_f():
        r = tk.Frame(body, bg=bg_f)
        r.pack(fill="x", pady=2, padx=10)
        return r
    def _etichetta_f(r, testo, pad=(10, 4)):
        tk.Label(r, text=testo, bg=bg_f, fg=self.TEXT_COLOR).pack(side="left", padx=pad)
    def _combo_f(r, chiave, valori, w):
        ttk.Combobox(r, values=valori, textvariable=f[chiave], style="Border.TCombobox",
                     state="readonly", width=w).pack(side="left")
    r1, r2 = _riga_f(), _riga_f()
    _etichetta_f(r1, "Tipo:", (4, 4))
    _combo_f(r1, "tipo", [TUTTI, "Entrata", "Uscita"], 9)
    _etichetta_f(r1, "Categoria:")
    _combo_f(r1, "categoria", [TUTTI] + sorted(self.categorie_tipi.keys()), 18)
    _etichetta_f(r1, "Anno:")
    _combo_f(r1, "anno", [TUTTI] + _anni_f, 7)
    _etichetta_f(r1, "Mese:")
    _combo_f(r1, "mese", [TUTTI] + MESI, 11)
    _etichetta_f(r1, "Partecipanti:")
    _combo_f(r1, "partecipanti", _partec_f, 18)
    _etichetta_f(r1, "Conto:")
    _combo_f(r1, "conto", _conti_f, 16)
    _etichetta_f(r1, "Metodo Pag.:")
    _combo_f(r1, "metodo", [TUTTI] + METODI_PAGAMENTO_EMOJI, 20)
    _etichetta_f(r2, "Hashtag:", (4, 4))
    ttk.Entry(r2, textvariable=f["tag"], width=14).pack(side="left")
    _etichetta_f(r2, "Descrizione contiene:")
    ttk.Entry(r2, textvariable=f["testo"], width=20).pack(side="left")
    _etichetta_f(r2, "Importo da:")
    ttk.Entry(r2, textvariable=f["imp_da"], width=9).pack(side="left")
    _etichetta_f(r2, "a:", (6, 4))
    ttk.Entry(r2, textvariable=f["imp_a"], width=9).pack(side="left")
    def _cal_btn(entry, var):
        def apri(_e=None):
            self.mostra_calendario_popup(entry, var)
            try:
                pc = getattr(self, "popup_calendario", None)
                if pc is not None and pc.winfo_exists():
                    pc.attributes("-topmost", True)
                    pc.lift()
            except tk.TclError:
                pass
        img = self.icone_gui.get("calendario")
        b = tk.Label(r2, image=img, bg=bg_f, cursor="hand2", padx=2)
        if img is None:
            b.config(text="📅")
        else:
            b.image = img
        b.pack(side="left", padx=(2, 0))
        b.bind("<Button-1>", apri)
    _etichetta_f(r2, "Dal:")
    e_da = ttk.Entry(r2, textvariable=f["da"], width=11)
    e_da.pack(side="left")
    _cal_btn(e_da, f["da"])
    _etichetta_f(r2, "Al:", (8, 4))
    e_a = ttk.Entry(r2, textvariable=f["a"], width=11)
    e_a.pack(side="left")
    _cal_btn(e_a, f["a"])
    tk.Label(r2, text="(GG-MM-AAAA)", bg=bg_f, fg="gray", font=("Arial", 8, "italic")).pack(side="left", padx=(4, 0))
    def _num_f(s):
        s = str(s or "").strip().replace("€", "").replace(" ", "")
        if not s:
            return None
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None
    def _spec_filtri():
        try:
            spec = {k: v.get() for k, v in f.items()}
        except Exception:
            return None
        spec["metodo"] = metodo_pagamento_pulito(spec["metodo"]) if spec["metodo"] != TUTTI else TUTTI
        spec["tag"] = [t.lstrip("#").lower() for t in re.split(r"[\s,;]+", spec["tag"].strip()) if t.lstrip("#")]
        spec["testo"] = spec["testo"].strip().lower()
        spec["imp_da"] = _num_f(spec["imp_da"])
        spec["imp_a"] = _num_f(spec["imp_a"])
        spec["da"] = _data_libera(spec["da"])
        spec["a"] = _data_libera(spec["a"])
        attivo = (any(spec[k] != TUTTI for k in ("tipo", "categoria", "anno", "mese", "partecipanti", "conto", "metodo"))
                  or spec["tag"] or spec["testo"] or spec["imp_da"] is not None or spec["imp_a"] is not None
                  or spec["da"] or spec["a"])
        return spec if attivo else None
    def _descr_filtri(spec):
        out = []
        for k, etich in (("tipo", ""), ("categoria", "Categoria "), ("anno", "Anno "), ("mese", ""),
                         ("partecipanti", ""), ("conto", "Conto "), ("metodo", "Metodo ")):
            if spec[k] != TUTTI:
                out.append(f"{etich}{spec[k]}")
        if spec["tag"]:
            out.append(" ".join(f"#{t}" for t in spec["tag"]))
        if spec["testo"]:
            out.append(f"«{spec['testo']}»")
        if spec["imp_da"] is not None or spec["imp_a"] is not None:
            ida = _fmt_it(spec["imp_da"]) if spec["imp_da"] is not None else "…"
            ia = _fmt_it(spec["imp_a"]) if spec["imp_a"] is not None else "…"
            out.append(f"Importo {ida} → {ia}")
        if spec["da"] or spec["a"]:
            da = spec["da"].strftime("%d-%m-%Y") if spec["da"] else "…"
            a = spec["a"].strftime("%d-%m-%Y") if spec["a"] else "…"
            out.append(f"{da} → {a}")
        return out
    def aggiorna_testata():
        spec = _spec_filtri()
        stato_txt = ("filtri attivi: " + ", ".join(_descr_filtri(spec))) if spec else "nessun filtro attivo"
        lbl_freccia.config(text="▾" if stato_f["aperta"] else "▸")
        lbl_head.config(text=f"Filtri avanzati  ({stato_txt})",
                        fg=getattr(self, "COLOR_HIGHLIGHT", self.TEXT_COLOR) if spec else self.TEXT_COLOR)
    def applica_filtri(*_):
        if stato_f["sosp"]:
            return
        stato_f["job"] = None
        try:
            if not finestra.winfo_exists():
                return
        except tk.TclError:
            return
        for e, k in ((e_da, "da"), (e_a, "a")):
            sbagliata = bool(f[k].get().strip()) and _data_libera(f[k].get()) is None
            try:
                e.configure(foreground="#DC3545" if sbagliata else self.TEXT_COLOR)
            except tk.TclError:
                pass
        aggiorna_testata()
        esegui_ricerca()
    def rinvia_filtri(*_):
        if stato_f["job"]:
            finestra.after_cancel(stato_f["job"])
        stato_f["job"] = finestra.after(400, applica_filtri)
    def azzera_filtri(*_):
        stato_f["sosp"] = True
        try:
            for k, v in f.items():
                v.set("" if k in ("tag", "testo", "imp_da", "imp_a", "da", "a") else TUTTI)
        finally:
            stato_f["sosp"] = False
        applica_filtri()
    def apri_chiudi_filtri(*_):
        stato_f["aperta"] = not stato_f["aperta"]
        if stato_f["aperta"]:
            body.pack(fill="x", before=frame_risultati)
        else:
            body.pack_forget()
        aggiorna_testata()
    for k in ("tipo", "categoria", "anno", "mese", "partecipanti", "conto", "metodo"):
        f[k].trace_add("write", applica_filtri)
    for k in ("tag", "testo", "imp_da", "imp_a", "da", "a"):
        f[k].trace_add("write", rinvia_filtri)
    for _w in (lbl_freccia, lbl_head):
        _w.bind("<Button-1>", apri_chiudi_filtri)
    aggiorna_testata()
    frame_risultati = tk.Frame(finestra, bg=self.COLOR_TOPLEVEL)
    frame_risultati.pack(fill="both", expand=True, padx=10)
    columns = ("Data", "Categoria", "Descrizione", "Tipo", "Importo", "Conto", "Ora", "Hashtag", "Metodo")
    tree = ttk.Treeview(frame_risultati, columns=columns, show="headings", selectmode='browse')
    tree.pack(side="left", fill="both", expand=True)
    def on_right_click(event):
        item_id = tree.identify_row(event.y)
        if not item_id:
            return
        values = tree.item(item_id, "values")
        if not values:
            return
        categoria   = str(values[1]).strip()
        descrizione = str(values[2]).strip()
        importo_str = str(values[4]).replace("€", "").replace(" ", "").strip()
        if "," in importo_str:
            importo_str = importo_str.replace(".", "").replace(",", ".")
        tipo = str(values[3]).strip().capitalize()
        cat_match = next(
            (c for c in self.categorie if c.strip().lower() == categoria.lower()), None
        )
        if cat_match:
            self.cat_sel.set(cat_match)
            self.cat_menu.set(cat_match)
            self.on_categoria_changed(manuale=False)
        try:
            self.imp_entry.delete(0, tk.END)
            self.imp_entry.insert(0, f"{float(importo_str):.2f}".replace(".", ","))
        except ValueError:
            pass
        self.desc_entry.delete(0, tk.END)
        if "RIC·" not in descrizione:
            self.desc_entry.insert(0, descrizione[:30])
        if self.tipo_spesa_var.get() != tipo:
            self.toggle_tipo_spesa()
        self.after(0, self.imp_entry.focus_set)
        finestra.destroy()
    tree.bind("<Double-1>", self.cerca_doppio_click)
    tree.bind("<Button-3>", on_right_click)
    self._bind_tooltip_metodo(tree, col_desc=2)
    def converti_importo(s):
        s = str(s).strip().replace('€', '').strip().replace(',', '')
        if s.count(',') == 1 and s.count('.') != 1:
            s = s.replace(',', '.')
        try:
            return float(s)
        except ValueError:
            return float('-inf')
    def converti_data(s):
        try:
            return datetime.datetime.strptime(str(s), '%d/%m/%Y')
        except ValueError:
            return datetime.datetime.min
    def formatta_italiano(numero):
        return "{:,.2f}".format(numero).replace('.', '#').replace(',', '.').replace('#', ',')
    def sort_by_column(tv, col, reverse):
        cols = list(tv["columns"])
        try:
            col_index = cols.index(col)
        except ValueError:
            return
        l = []
        for k in tv.get_children(''):
            item_values = tv.item(k, 'values')
            if item_values and len(item_values) > col_index:
                if col == "Importo":
                    sort_value = converti_importo(item_values[col_index])
                elif col == "Data":
                    sort_value = converti_data(item_values[col_index])
                else:
                    sort_value = item_values[col_index]
                l.append((sort_value, k))
            else:
                l.append(('', k))
        l.sort(key=lambda t: t[0], reverse=reverse)
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)
        tv.heading(col, command=lambda: sort_by_column(tv, col, not reverse))
    for col in columns:
        tree.heading(col, text=col, command=lambda c=col: sort_by_column(tree, c, False))
        tree.column(col, anchor="e" if col == "Importo" else "w")
    tree.column("Data",        width=90,  stretch=False)
    tree.column("Categoria",   width=120, stretch=False)
    tree.column("Descrizione", width=260, stretch=True)
    tree.column("Tipo",        width=80,  stretch=False)
    tree.column("Importo",     width=100, stretch=False)
    tree.column("Conto",       width=100, stretch=False)
    tree.column("Ora",         width=55,  stretch=False)
    tree.column("Hashtag",     width=130, stretch=False)
    tree.column("Metodo",      width=110, stretch=False)
    scroll = ttk.Scrollbar(frame_risultati, orient="vertical", command=tree.yview, style="Vertical.TScrollbar")
    tree.configure(yscrollcommand=scroll.set)
    scroll.pack(side="right", fill="y")
    tree.tag_configure("entrata_tag", foreground="green")
    tree.tag_configure("uscita_tag",  foreground="red")
    tree.tag_configure("neutro_tag",  foreground="gray")
    tree.tag_configure("futuro_tag",  foreground="#E5C07B", font=("Arial", 9, "italic"))
    tree.tag_configure("sforato_tag", foreground="#C08081", font=("Arial", 9, "bold"))
    frame_totali = tk.Frame(finestra, bg=self.COLOR_TOPLEVEL)
    frame_totali.pack(fill="x", pady=10, padx=10)
    lbl_risultati = tk.Label(frame_totali, text="", anchor="w", font=("Arial", 10))
    lbl_risultati.pack(fill="x")
    lbl_totali = tk.Label(frame_totali, text="", anchor="w", font=("Arial", 10, "bold"))
    lbl_totali.pack(fill="x")
    def esegui_ricerca(event=None):
        parola = campo_input.get().strip().lower()
        spec = _spec_filtri()
        for item in tree.get_children():
            tree.delete(item)
        tree._metodo_lookup = {}
        risultati = []
        oggi = datetime.date.today()
        mostra_futuro = mostra_futuro_var.get()
        da_data = _data_libera(f["da"].get())
        a_data  = _data_libera(f["a"].get())
        _agganci_cerca = costruisci_mappa_conti_da_trasferimenti(PORTAFOGLIO_BANCARIO)
        _uso_ordinale_cerca = {}
        _profilo_attivo_co = getattr(_app, "PROFILO_ATTIVO", "Principale")
        _gestore_nome_cerca_owner = _profilo_attivo_co if _profilo_attivo_co != "Principale" else os.path.basename(os.getcwd())
        _candidati_owner = list(self.nomi_partecipanti) if hasattr(self, "nomi_partecipanti") and self.nomi_partecipanti else []
        if self._gestore_partecipa() and not any(
                (p.get("nome", "") if isinstance(p, dict) else p) == _gestore_nome_cerca_owner
                for p in _candidati_owner):
            _candidati_owner.append({"nome": _gestore_nome_cerca_owner})
        for data_key in sorted(self.spese.keys(), reverse=True):
            try:
                d = data_key if isinstance(data_key, datetime.date) else datetime.datetime.strptime(data_key, "%d-%m-%Y").date()
            except ValueError:
                d = datetime.datetime.strptime(data_key, "%Y-%m-%d").date()
            if not mostra_futuro and d > oggi:
                continue
            if da_data and d < da_data:
                continue
            if a_data and d > a_data:
                continue
            for voce in self.spese[data_key]:
                categoria    = str(voce[0]).lower()
                descrizione  = str(voce[1]).lower()
                importo_voce = voce[2]
                tipo         = str(voce[3]).lower()
                owner = next((p["nome"] for p in _candidati_owner
                              if any(f"{ico}{p['nome']}".lower() in descrizione or f"{ico} {p['nome']}".lower() in descrizione
                                     for ico in ("PER·", "CTP·", "CNT·"))), "")
                _conto_espl_cerca = self._conto_effettivo(voce)
                if _conto_espl_cerca:
                    nome_conto_cerca = _conto_espl_cerca
                else:
                    nome_conto_cerca = conto_da_mappa(_agganci_cerca, _uso_ordinale_cerca, d.strftime("%d-%m-%Y"), importo_voce, voce[3])
                metodo_cerca  = campo(voce, "metodo_pagamento", "")
                ora_cerca     = campo(voce, "ora", "")
                hashtag_cerca = campo(voce, "hashtag", [])
                hashtag_txt   = " ".join(hashtag_cerca)
                matches = True
                if parola:
                    if not any(parola in str(campo_v).lower() for campo_v in [categoria, descrizione, tipo, str(importo_voce), nome_conto_cerca.lower(), metodo_cerca.lower(), hashtag_txt.lower()]):
                        matches = False
                if spec:
                    if spec["testo"] and spec["testo"] not in descrizione:
                        matches = False
                    if spec["categoria"] != TUTTI and categoria != spec["categoria"].lower():
                        matches = False
                    if spec["tipo"] != TUTTI and tipo != spec["tipo"].lower():
                        matches = False
                    if spec["anno"] != TUTTI and str(d.year) != spec["anno"]:
                        matches = False
                    if spec["mese"] != TUTTI and d.month != MESI.index(spec["mese"]) + 1:
                        matches = False
                    if spec["partecipanti"] != TUTTI:
                        nome_filtro = spec["partecipanti"]
                        for prefisso in ("CTP· ", "CNT· ", "PER· "):
                            if nome_filtro.startswith(prefisso):
                                nome_filtro = nome_filtro[len(prefisso):]
                                break
                        if nome_filtro.lower() != owner.lower():
                            matches = False
                    if spec["conto"] != TUTTI and nome_conto_cerca != spec["conto"]:
                        matches = False
                    if spec["metodo"] != TUTTI and metodo_cerca != spec["metodo"]:
                        matches = False
                    if spec["tag"] and not all(t in hashtag_txt.lower() for t in spec["tag"]):
                        matches = False
                    try:
                        if spec["imp_da"] is not None and float(importo_voce) < spec["imp_da"]:
                            matches = False
                        if spec["imp_a"] is not None and float(importo_voce) > spec["imp_a"]:
                            matches = False
                    except (ValueError, TypeError):
                        pass
                if matches:
                    risultati.append({
                        "data":        d.strftime('%d/%m/%Y'),
                        "categoria":   voce[0],
                        "descrizione": voce[1],
                        "importo":     importo_voce,
                        "tipo":        tipo.capitalize(),
                        "partecipante": owner,
                        "conto":       nome_conto_cerca,
                        "metodo":      metodo_cerca,
                        "ora":         ora_cerca,
                        "hashtag":     hashtag_txt,
                        "id_ricorrenza": campo(voce, "id_ricorrenza", ""),
                        "id_spesa":    campo(voce, "id_spesa", "")
                    })
        risultati.sort(key=lambda x: datetime.datetime.strptime(x['data'], '%d/%m/%Y'), reverse=True)
        tot_entrate = sum(r['importo'] for r in risultati if r['tipo'] == "Entrata")
        tot_uscite  = sum(r['importo'] for r in risultati if r['tipo'] == "Uscita")
        netto       = tot_entrate - tot_uscite
        _desc = _descr_filtri(spec) if spec else []
        if parola:
            _desc.insert(0, f"Parola chiave: '{parola}'")
        testo_filtri = ", ".join(_desc)
        if not risultati:
            lbl_risultati.config(
                text=" Nessuna corrispondenza per la ricerca attuale.",
                image=self.icone_gui.get("chiudi"),
                compound="left",
                fg="#E06C75",
                bg=self.COLOR_TOPLEVEL
            )
            lbl_totali.config(text="", image="", bg=self.COLOR_TOPLEVEL)
        else:
            colore_saldo = "#98C379" if netto >= 0 else "#E06C75"
            lbl_risultati.config(
                text=f" Trovati {len(risultati)} documenti. | Filtri: {testo_filtri or 'Nessuno'}",
                image=self.icone_gui.get("modifica"),
                compound="left",
                fg="#61AFEF",
                bg=self.COLOR_TOPLEVEL
            )
            lbl_totali.config(
                text=f" Entrate: {formatta_italiano(tot_entrate)} € | Uscite: {formatta_italiano(tot_uscite)} € | Saldo: {formatta_italiano(netto)} €",
                image=self.icone_gui.get("icc"),
                compound="left",
                fg=colore_saldo,
                bg=self.COLOR_TOPLEVEL
            )
            _budget_categorie_ref_cerca = getattr(self, 'budget_categorie', {}) or {}
            _tot_categoria_mese_cache_cerca = {}
            def _budget_categoria_cerca(cat):
                return next(
                    (v for k, v in _budget_categorie_ref_cerca.items() if k.strip().lower() == cat.strip().lower()),
                    0
                )
            def _speso_categoria_mese_cerca(cat, anno_t, mese_t):
                chiave = (anno_t, mese_t, cat.strip().lower())
                if chiave not in _tot_categoria_mese_cache_cerca:
                    tot = 0.0
                    for d2, voci2 in self.spese.items():
                        d2d = d2 if isinstance(d2, datetime.date) else datetime.datetime.strptime(d2, "%d-%m-%Y").date()
                        if d2d.year == anno_t and d2d.month == mese_t:
                            for e2 in voci2:
                                if len(e2) >= 4 and str(e2[0]).strip().lower() == cat.strip().lower() and str(e2[3]).lower() == "uscita":
                                    try:
                                        tot += float(e2[2])
                                    except (ValueError, TypeError):
                                        pass
                    _tot_categoria_mese_cache_cerca[chiave] = tot
                return _tot_categoria_mese_cache_cerca[chiave]
            for riga in risultati:
                tipo_r = riga['tipo'].lower()
                d_riga = datetime.datetime.strptime(riga['data'], '%d/%m/%Y').date()
                if d_riga > datetime.date.today():
                    tag = "futuro_tag"
                elif tipo_r == "entrata":
                    tag = "entrata_tag"
                elif tipo_r == "uscita":
                    tag = "uscita_tag"
                    _budget_val_cerca = _budget_categoria_cerca(str(riga['categoria']))
                    if _budget_val_cerca and _budget_val_cerca > 0:
                        if _speso_categoria_mese_cerca(str(riga['categoria']), d_riga.year, d_riga.month) > _budget_val_cerca:
                            tag = "sforato_tag"
                else:
                    tag = "neutro_tag"
                _item_c = tree.insert("", "end", values=(
                    riga['data'],
                    riga['categoria'],
                    riga['descrizione'],
                    riga['tipo'],
                    f"{_fmt_it(riga['importo'])} €",
                    riga.get('conto', ''),
                    riga.get('ora', ''),
                    riga.get('hashtag', ''),
                    riga.get('metodo', '')
                ), tags=(tag,))
                tree._metodo_lookup[_item_c] = {
                    "metodo": riga.get('metodo', ''),
                    "conto": riga.get('conto', ''),
                    "ora": riga.get('ora', ''),
                    "hashtag": riga.get('hashtag', ''),
                    "id_ricorrenza": riga.get('id_ricorrenza', ''),
                    "partecipante": riga.get('partecipante', ''),
                    "data": d_riga.strftime('%d-%m-%Y'),
                    "categoria": riga['categoria'],
                    "importo": riga['importo'],
                    "tipo": riga['tipo'],
                    "id_spesa": riga.get('id_spesa', ''),
                }
    campo_input.bind("<KeyRelease>", esegui_ricerca)
    mostra_futuro_var.trace_add("write", lambda *_: esegui_ricerca())
    def resetta_campo():
        campo_input.delete(0, tk.END)
        azzera_filtri()
    img_indietro = self.icone_gui.get("reset")
    btn_reset_superiore = ttk.Label(frame_superiore, compound="left", image=img_indietro,
                                    text=" 🔙" if not img_indietro else "",
                                    background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                                    cursor="hand2", padding=(5, 5))
    btn_reset_superiore.pack(side="left", padx=5)
    btn_reset_superiore.bind("<Button-1>", lambda e: resetta_campo())
    def esporta_risultato():
        dati_tree   = []
        tot_entrate = 0.0
        tot_uscite  = 0.0
        for item in tree.get_children():
            values = tree.item(item, "values")
            if values:
                data, cat, desc, tipo, importo_str = values[0], values[1], values[2], values[3], values[4]
                conto    = values[5] if len(values) > 5 else ""
                ora      = values[6] if len(values) > 6 else ""
                hashtag  = values[7] if len(values) > 7 else ""
                importo_float = converti_importo(importo_str)
                dati_tree.append((data, cat, desc, tipo, importo_float, conto, ora, hashtag))
                if tipo == "Entrata":
                    tot_entrate += importo_float
                elif tipo == "Uscita":
                    tot_uscite += importo_float
        if not dati_tree:
            self.show_custom_warning("Esportazione", "⚠️ Nessun risultato trovato da salvare o stampare.")
            return
        W_DATA, W_CAT, W_DESC, W_TIPO, W_IMP, W_CNT, W_ORA, W_TAG = 10, 18, 24, 8, 13, 12, 6, 16
        header    = (f"{'Data':<{W_DATA}} │ {'Categoria':<{W_CAT}} │ {'Descrizione':<{W_DESC}} │ {'Tipo':<{W_TIPO}} │ "
                     f"{'Importo (€)':>{W_IMP}} │ {'Conto':<{W_CNT}} │ {'Ora':<{W_ORA}} │ {'Hashtag':<{W_TAG}}\n")
        separator = (f"{'─'*W_DATA}─┼─{'─'*W_CAT}─┼─{'─'*W_DESC}─┼─{'─'*W_TIPO}─┼─{'─'*W_IMP}─┼─"
                     f"{'─'*W_CNT}─┼─{'─'*W_ORA}─┼─{'─'*W_TAG}\n")
        testo_filtri_attivi = lbl_risultati.cget("text").split("| Filtri:")[1].strip() if "| Filtri:" in lbl_risultati.cget("text") else "Nessuno"
        netto = tot_entrate - tot_uscite
        contenuto_preview  = f"─── RISULTATI RICERCA ({datetime.date.today():%d/%m/%Y}) ───────────────────────────────────────────────\n"
        contenuto_preview += f" Filtri: {testo_filtri_attivi}\n"
        contenuto_preview += f" Operazioni Trovate: {len(dati_tree)}\n\n"
        contenuto_preview += "─── RIEPILOGO FINANZIARIO ───────────────────────────────────────────────────────────────────────────\n"
        contenuto_preview += f" • Entrate Totali: {formatta_italiano(tot_entrate)} €\n"
        contenuto_preview += f" • Uscite Totali:  {formatta_italiano(tot_uscite)} €\n"
        contenuto_preview += f" • Saldo Netto:    {formatta_italiano(netto)} €\n\n"
        contenuto_preview += "─── DETTAGLIO OPERAZIONI ────────────────────────────────────────────────────────────────────────────\n"
        contenuto_preview += header + separator
        for data, cat, desc, tipo, importo_float, conto, ora, hashtag in dati_tree:
            desc_troncata = (desc[:W_DESC-3] + '...') if len(desc) > W_DESC else desc
            cat_troncata  = (cat[:W_CAT-3]  + '...') if len(cat)  > W_CAT  else cat
            cnt_troncato  = (conto[:W_CNT-3] + '...') if len(conto) > W_CNT else conto
            tag_troncato  = (hashtag[:W_TAG-3] + '...') if len(hashtag) > W_TAG else hashtag
            contenuto_preview += (f"{data:<{W_DATA}} │ {cat_troncata:<{W_CAT}} │ "
                          f"{desc_troncata:<{W_DESC}} │ {tipo:<{W_TIPO}} │ "
                          f"{formatta_italiano(importo_float):>{W_IMP}} │ {cnt_troncato:<{W_CNT}} │ "
                          f"{ora:<{W_ORA}} │ {tag_troncato:<{W_TAG}}\n")
        contenuto_preview += "\n" + separator
        def _salva_su_file(content_text, preview_popup):
            preview_popup.destroy()
            nome_file = f"Risultati_Ricerca_{datetime.date.today():%d_%m_%Y}.txt"
            file = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("File di testo", "*.txt")],
                initialdir=EXPORT_FILES,
                initialfile=nome_file,
                title="Salva risultati ricerca",
                confirmoverwrite=False,
                parent=finestra
            )
            if file:
                if os.path.exists(file):
                    if not self.show_custom_askyesno("Sovrascrivere file?",
                            f"Il file '{os.path.basename(file)}' esiste già. Vuoi sovrascriverlo?"):
                        return
                try:
                    with open(file, "w", encoding="utf-8") as f:
                        f.write(content_text)
                    self.show_custom_warning("Esportazione completata", f"✓ Risultati salvati:\n{file}")
                except Exception as e:
                    self.show_custom_warning("Errore", f"❌ Salvataggio fallito:\n{e}")
        def _salva_come_pdf(content_text, preview_popup):
            preview_popup.destroy()
            import pymupdf as fitz
            nome_file = f"Risultati_Ricerca_{datetime.date.today():%d_%m_%Y}.pdf"
            file = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("Documento PDF", "*.pdf")],
                initialdir=EXPORT_FILES,
                initialfile=nome_file,
                title="Salva risultati ricerca come PDF",
                confirmoverwrite=False,
                parent=finestra
            )
            if file:
                if os.path.exists(file):
                    if not self.show_custom_askyesno("Sovrascrivere file?",
                            f"Il file '{os.path.basename(file)}' esiste già. Vuoi sovrascriverlo?"):
                        return
                try:
                    doc = fitz.open()
                    lines = content_text.split('\n')
                    page_w, page_h = 842, 595
                    margin = 40
                    font_size = 7
                    line_height = font_size + 2
                    page = doc.new_page(width=page_w, height=page_h)
                    y = margin
                    for line in lines:
                        if y > (page_h - margin):
                            page = doc.new_page(width=page_w, height=page_h)
                            y = margin
                        page.insert_text(
                            (margin, y),
                            line,
                            fontname="cour",
                            fontsize=font_size
                        )
                        y += line_height
                    doc.save(file)
                    doc.close()
                    self.show_custom_warning("Esportazione completata", f"✓ PDF salvato:\n{file}")
                except Exception as e:
                    self.show_custom_warning("Errore", f"❌ Creazione PDF fallita:\n{e}")
        preview_popup = tk.Toplevel(finestra, bg=self.COLOR_TOPLEVEL)
        preview_popup.withdraw()
        preview_popup.title("Anteprima Risultati Ricerca")
        pw, ph = 1300, 630
        px = (preview_popup.winfo_screenwidth()  - pw) // 2
        py = (preview_popup.winfo_screenheight() - ph) // 2
        preview_popup.geometry(f"{pw}x{ph}+{px}+{py}")
        preview_popup.minsize(pw, ph)
        preview_popup.transient(finestra)
        preview_popup.update_idletasks()
        preview_popup.bind('<Escape>', lambda e: preview_popup.destroy())
        text_area = tk.Text(preview_popup, wrap='word', font=('Courier', 10), padx=10, pady=10)
        text_area.insert('1.0', contenuto_preview)
        text_area.config(state='disabled')
        text_area.pack(fill='both', expand=True, padx=10, pady=10)
        frame_btn = tk.Frame(preview_popup, bg=self.COLOR_TOPLEVEL)
        frame_btn.pack(pady=(0, 10))
        img_chiudi_ant = self.icone_gui.get("chiudi")
        btn_chiudi_ant = ttk.Label(frame_btn, compound="left", image=img_chiudi_ant,
                                   text=" Chiudi" if img_chiudi_ant else "Chiudi",
                                   background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                                   cursor="hand2", padding=(10, 5))
        btn_chiudi_ant.pack(side='right', padx=5)
        btn_chiudi_ant.bind("<Button-1>", lambda e: preview_popup.destroy())
        img_esporta = self.icone_gui.get("salva")
        btn_esporta = ttk.Label(frame_btn, compound="left", image=img_esporta,
                                text=" Esporta TXT" if img_esporta else "Esporta TXT",
                                background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                                cursor="hand2", padding=(10, 5))
        btn_esporta.pack(side='left', padx=5)
        btn_esporta.bind("<Button-1>", lambda e: _salva_su_file(contenuto_preview, preview_popup))
        img_esporta_pdf = self.icone_gui.get("salva")
        btn_esporta_pdf = ttk.Label(frame_btn, compound="left", image=img_esporta_pdf,
                                text=" Esporta PDF" if img_esporta_pdf else "Esporta PDF",
                                background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                                cursor="hand2", padding=(10, 5))
        btn_esporta_pdf.pack(side='left', padx=5)
        btn_esporta_pdf.bind("<Button-1>", lambda e: _salva_come_pdf(contenuto_preview, preview_popup))
        if hasattr(self, '_stampa_lista_diretta'):
            img_stampa_ant = self.icone_gui.get("stampa")
            btn_stampa_ant = ttk.Label(frame_btn, compound="left", image=img_stampa_ant,
                                       text=" Stampa" if img_stampa_ant else "Stampa",
                                       background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                                       cursor="hand2", padding=(10, 5))
            btn_stampa_ant.pack(side='left', padx=5)
            btn_stampa_ant.bind("<Button-1>", lambda e: self._stampa_lista_diretta(contenuto_preview, self.show_custom_warning))
        preview_popup.deiconify()
        preview_popup.grab_set()
    frame_bottoni = tk.Frame(finestra, bg=self.COLOR_TOPLEVEL)
    frame_bottoni.pack(pady=(0, 12))
    for testo, ico, cmd in [
        (" Cerca",          "search",  lambda e: esegui_ricerca()),
        (" Esporta",        "stampa",  lambda e: esporta_risultato()),
        (" Reset",          "reset",   lambda e: resetta_campo()),
        (" Chiudi",         "chiudi",  lambda e: finestra.destroy()),
    ]:
        img = self.icone_gui.get(ico)
        btn = ttk.Label(frame_bottoni, compound="left", image=img,
                        text=testo if img else testo.strip(),
                        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                        cursor="hand2", padding=(10, 5))
        btn.pack(side="left", padx=6)
        btn.bind("<Button-1>", cmd)
    self.after(100, esegui_ricerca)
    def _refresh_da_modifica_esterna():
        try:
            pos = tree.yview()[0]
            esegui_ricerca()
            tree.yview_moveto(pos)
        except tk.TclError:
            pass
    if hasattr(self, "registra_refresh_finestra"):
        self.registra_refresh_finestra(finestra, _refresh_da_modifica_esterna)
    finestra.deiconify()
def cerca_doppio_click(self, event):
    tree = event.widget
    item_id = tree.focus()
    if not item_id:
        return
    vals = tree.item(item_id, "values")
    if not vals or len(vals) < 1:
        return
    data_str = vals[0]
    try:
        giorno = datetime.datetime.strptime(data_str, "%d/%m/%Y").date()
    except Exception:
        return
    self.set_stats_mode("giorno")
    if hasattr(self, "cal"):
        self.cal.selection_set(giorno)
        self.cal._sel_date = giorno
        self.stats_refdate = giorno
    self.update_stats()
    self.estratto_month_var.set(f"{giorno.month:02d}")
    self.estratto_year_var.set(str(giorno.year))
    self.stats_label.config(
        text=f"Riepilogo Giornaliero - {giorno.strftime('%d-%m-%Y')}",
        foreground="purple", font=("Arial", 10, "bold"))
    if giorno != datetime.date.today():
        self.blink_label_colors(self.stats_label, "purple", "yellow")
    else:
        self.stop_blink_label_colors(self.stats_label, final_color="purple")
    if hasattr(self, '_finestra_cerca') and self._finestra_cerca.winfo_exists():
        self._finestra_cerca.destroy()
        self._finestra_cerca = None
    desc_cerca = str(vals[2])[:20] if len(vals) > 2 else ""
    _id_sp = (getattr(tree, "_metodo_lookup", {}).get(item_id) or {}).get("id_spesa", "")
    self.after(400, lambda: self.seleziona_spesa_in_lista(giorno, desc_cerca, _id_sp))

