#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import datetime
import tkinter as tk
from tkinter import ttk
from moduli.modello_spesa import campo, METODI_PAGAMENTO
from moduli.mappa_conti_trasferimenti import costruisci_mappa_conti_da_trasferimenti, conto_da_mappa

def _data_giorno(giorno):
    if isinstance(giorno, datetime.date):
        return giorno
    try:
        return datetime.datetime.strptime(str(giorno), "%Y-%m-%d").date()
    except Exception:
        return None


def _elimina_documenti_allegati(voci, registry_file, doc_dir):
    if not voci or not os.path.exists(registry_file):
        return 0
    with open(registry_file, "r", encoding="utf-8") as f:
        reg = json.load(f)
    eliminati = 0
    for giorno, voce in voci:
        d = _data_giorno(giorno)
        if d is None:
            continue
        o_s = d.strftime("%d%m%Y")
        o_i = str(int(round(float(campo(voce, "importo", 0.0)) * 100)))
        o_t = campo(voce, "tipo", "")
        desc = str(campo(voce, "descrizione", "")).strip()
        candidati = [k for k in reg if k.startswith(o_s) and o_i in k and o_t in k]
        if not candidati:
            continue
        # preferisce il documento con la stessa descrizione; altrimenti il primo che combacia
        scelto = next((k for k in candidati
                       if isinstance(reg[k], dict) and str(reg[k].get("descrizione_esatta", "")).strip() == desc),
                      candidati[0])
        percorso = os.path.join(doc_dir, scelto)
        try:
            if os.path.exists(percorso):
                os.remove(percorso)
        except OSError as e:
            print(f"Documento non eliminato ({scelto}): {e}")
            continue
        reg.pop(scelto, None)
        eliminati += 1
    if eliminati:
        with open(registry_file, "w", encoding="utf-8") as f:
            json.dump(reg, f, indent=4, ensure_ascii=False)
    return eliminati


def apri_cancella_spese_treeview_unica(self):
    if hasattr(self, '_cancella_spese_popup') and self._cancella_spese_popup and self._cancella_spese_popup.winfo_exists():
        self._cancella_spese_popup.lift()
        return
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    REGISTRY_FILE = _app.REGISTRY_FILE
    DOC_DIR = _app.DOC_DIR
    NOMI_MESI_ITALIANO = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", 
                          "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    if not hasattr(self, 'spese') or not isinstance(self.spese, dict):
        self.spese = {} 
    self.filtri_cancellazione = {
        "partecipante": "",
        "descrizione": "",
        "categoria": "",
        "tipo": "",
        "anno": "",
        "mese": "",
        "da": "",
        "a": "",
        "conto": "",
        "metodo": "",
        "hashtag": "",
        "mostra_futuro": True,
        "data_da": "",
        "data_a": "",
        "ricerca_rapida": ""
    }
    stato_f = {"aperta": False, "sosp": False}
    iid_bloccati = set()
    def _ruoli_pool():
        try:
            from moduli.community_pool import _carica_link
            return {str(k): (v.get("ruolo", "") if isinstance(v, dict) else "")
                    for k, v in _carica_link().get("voci", {}).items()}
        except Exception:
            return {}
    if not hasattr(self, 'selezionate_iid'):
        self.selezionate_iid = set()
    self.selezionate_iid.clear() 
    def sort_treeview_column(tree, col, reverse, data_type='string', initial=False):
            items_to_sort = []
            children = tree.get_children('')
            if not children: return
            for k in children:
                if k in ("EMPTY_MSG", "FILTER_MSG", "NO_DATA"): continue
                value = tree.set(k, col)
                items_to_sort.append((value, k))
            def get_sort_key(item):
                value = item[0]
                if value in ("—", ""):
                    return (0 if data_type in ('float', 'date') else "")
                try:
                    if data_type == 'float':
                        return float(value.replace(' €', '').replace('.', '').replace(',', '.'))
                    elif data_type == 'date':
                        return datetime.datetime.strptime(value, '%d/%m/%Y')
                    return value.lower()
                except Exception: return value
            items_to_sort.sort(key=get_sort_key, reverse=reverse)
            for index, (val, k) in enumerate(items_to_sort):
                tree.move(k, '', index)
            col_names = {"Giorno": "Giorno", "Categoria": "Categoria", "Descrizione": "Descrizione", "Tipo": "Tipo", "Importo": "Importo"}
            for c in tree["columns"]:
                base = col_names.get(c, c)
                if c == col:
                    sym = " ▲" if not reverse else " ▼"
                    tree.heading(c, text=base + sym, command=lambda _c=c: sort_treeview_column(tree, _c, not reverse, data_type))
                else:
                    tree.heading(c, text=base)
    def toggle_selection_treeview(event):
        row_id = self.spese_treeview.identify_row(event.y)
        if not row_id or row_id in ("EMPTY_MSG", "FILTER_MSG"): return
        if row_id in iid_bloccati: return
        is_selected = row_id in self.selezionate_iid
        current_tags = list(self.spese_treeview.item(row_id, 'tags'))
        type_tag = [t for t in current_tags if t in ('entrata', 'uscita', 'futuro', 'sforato')] 
        if is_selected:
            self.selezionate_iid.remove(row_id)
            self.spese_treeview.item(row_id, tags=type_tag, text="[ ]") 
        else:
            self.selezionate_iid.add(row_id)
            new_tags = type_tag + ['selezionata']
            self.spese_treeview.item(row_id, tags=new_tags, text="[X]") 
    def esegui_cancellazione_azione(): 
        if not self.selezionate_iid:
            self.show_custom_warning("Attenzione", "Seleziona almeno una spesa da cancellare.")
            return
        num_selezionate = len(self.selezionate_iid)
        _lk0 = getattr(self.spese_treeview, "_metodo_lookup", {}) or {}
        _ruoli0 = _ruoli_pool()
        n_orig_pool = sum(1 for _i in self.selezionate_iid
                          if _ruoli0.get(str((_lk0.get(_i) or {}).get("id_spesa", ""))) == "origine")
        _avviso_pool = (
            f"Tra queste {n_orig_pool} " + ("è una spesa pubblicata" if n_orig_pool == 1 else "sono spese pubblicate") +
            " nel CommunityPool: al prossimo sync " + ("verrà ritirata o chiusa" if n_orig_pool == 1 else "verranno ritirate o chiuse") +
            " e le quote in attesa saranno rifiutate.\n\n"
        ) if n_orig_pool else ""
        testo_messaggio = (
            f"⚠️ CONFERMA CANCELLAZIONE DEFINITIVA\n\n"
            f"Stai per cancellare {num_selezionate} elementi selezionati.\n\n"
            f"{_avviso_pool}"
            f"ATTENZIONE: Questa azione è IRREVERSIBILE e i dati non potranno più essere recuperati.\n"
            f"Sei assolutamente sicuro di voler procedere con l'eliminazione?"
        )
        response = self.show_custom_askyesno("Conferma Cancellazione", testo_messaggio)
        if not response: return
        _lookup = getattr(self.spese_treeview, "_metodo_lookup", {}) or {}
        ids_sel = set()
        for _iid in self.selezionate_iid:
            _idsp = (_lookup.get(_iid) or {}).get("id_spesa", "")
            if _idsp:
                ids_sel.add(str(_idsp))
        if not ids_sel:
            self.show_custom_warning("Attenzione", "Le spese selezionate non sono piu' disponibili. Riapri l'elenco e riprova.")
            return
        spese_da_mantenere = {}
        self.spese_cancellate_tmp = {}
        for giorno_obj in list(self.spese.keys()):
            spese_mantenute_giorno = []
            for voce in self.spese.get(giorno_obj, []):
                if str(campo(voce, "id_spesa", "")) in ids_sel:
                    self.spese_cancellate_tmp.setdefault(giorno_obj, []).append(voce)
                    if hasattr(self, "elimina_piano_per_spesa"):
                        self.elimina_piano_per_spesa(campo(voce, "id_spesa", None))
                else:
                    spese_mantenute_giorno.append(voce)
            if spese_mantenute_giorno:
                spese_da_mantenere[giorno_obj] = spese_mantenute_giorno
        num_selezionate = sum(len(v) for v in self.spese_cancellate_tmp.values())
        if num_selezionate == 0:
            self.selezionate_iid.clear()
            popola_treeview_spese()
            self.show_custom_warning("Attenzione", "Le spese selezionate erano gia' state modificate o eliminate dal web. Nessuna cancellazione eseguita.")
            return
        voci_con_doc = [(g, v) for g, lista in self.spese_cancellate_tmp.items() for v in lista
                        if "ALL·" in str(campo(v, "descrizione", ""))]
        elimina_doc = False
        if voci_con_doc:
            n_doc = len(voci_con_doc)
            elimina_doc = self.show_custom_askyesno(
                "Elimina Allegati",
                f"{n_doc} dei movimenti selezionati " + ("ha" if n_doc == 1 else "hanno") +
                " un documento allegato.\n\n"
                f"Vuoi eliminare anche {'il file PDF' if n_doc == 1 else f'i {n_doc} file PDF'}?"
            )
        self.spese = spese_da_mantenere
        doc_eliminati = 0
        if elimina_doc:
            try:
                doc_eliminati = _elimina_documenti_allegati(voci_con_doc, REGISTRY_FILE, DOC_DIR)
            except Exception as e_doc:
                self.show_custom_warning("Errore", f"Registro: {e_doc}")
        self.selezionate_iid.clear()
        popola_treeview_spese()
        if hasattr(self, 'refresh_gui'): self.refresh_gui()
        if hasattr(self, 'save_db'): self.save_db()
        if hasattr(self, 'annulla_azione_gamification'):
            for lista_voci_canc in self.spese_cancellate_tmp.values():
                for _voce in lista_voci_canc:
                    self.annulla_azione_gamification("movimento")
        self._sync_fairshare_e_aggiorna()
        _msg_ok = f"✓ {num_selezionate} spese sono state cancellate."
        if elimina_doc:
            _msg_ok += f"\n✓ {doc_eliminati} documenti eliminati."
        self.show_custom_warning("Successo", _msg_ok)
    def popola_treeview_spese():
        self.spese_treeview.delete(*self.spese_treeview.get_children())
        self.spese_treeview._metodo_lookup = {}
        iid_bloccati.clear()
        _ruoli_p = _ruoli_pool()
        if not self.spese:
            self.spese_treeview.insert("", "end", iid="FILTER_MSG",
                                       text="",
                                       values=("", "Nessuna spesa presente.", "", "", "", "", "", "", ""),
                                       tags=('empty',))
            return
        filtri = self.filtri_cancellazione
        items_inserted = 0
        ricerca_rapida = filtri.get("ricerca_rapida", "").strip().lower()
        filtro_testo_globale = filtri.get("descrizione", "").lower()
        filtro_categoria_esatta = filtri.get("categoria")
        filtro_tipo = filtri.get("tipo")
        filtro_anno = filtri.get("anno")
        filtro_mese_nome = filtri.get("mese")
        filtro_partecipante = filtri.get("partecipante")
        mostra_futuro = filtri.get("mostra_futuro", True)
        data_da_f = None
        data_a_f = None
        try:
            if filtri.get("data_da", "").strip():
                data_da_f = datetime.datetime.strptime(filtri["data_da"].strip(), "%d-%m-%Y").date()
        except ValueError:
            pass
        try:
            if filtri.get("data_a", "").strip():
                data_a_f = datetime.datetime.strptime(filtri["data_a"].strip(), "%d-%m-%Y").date()
        except ValueError:
            pass
        filtro_mese_numero = ""
        if filtro_mese_nome and filtro_mese_nome != "—":
            try:
                mese_index = NOMI_MESI_ITALIANO.index(filtro_mese_nome) + 1
                filtro_mese_numero = f"{mese_index:02d}"
            except ValueError:
                pass 
        try:
            giorni_ordinati = sorted(self.spese.keys(), 
                                     key=lambda d: d if isinstance(d, datetime.date) else datetime.datetime.strptime(str(d), '%Y-%m-%d').date(), 
                                     reverse=True) 
        except Exception:
             giorni_ordinati = sorted(self.spese.keys(), reverse=True)
        _agganci_cs = costruisci_mappa_conti_da_trasferimenti(PORTAFOGLIO_BANCARIO)
        _uso_ordinale_cs = {}
        for giorno_obj in giorni_ordinati:
            d = None
            giorno_interno = str(giorno_obj)
            giorno_visualizzato = str(giorno_obj)
            try:
                if isinstance(giorno_obj, datetime.date):
                    d = giorno_obj
                else:
                    d = datetime.datetime.strptime(str(giorno_obj), '%Y-%m-%d').date()
                giorno_interno = d.strftime('%Y-%m-%d')
                giorno_visualizzato = d.strftime('%d/%m/%Y')
            except Exception:
                pass 
            if d:
                oggi_cf = datetime.date.today()
                if not mostra_futuro and d > oggi_cf:
                    continue
                if data_da_f and d < data_da_f:
                    continue
                if data_a_f and d > data_a_f:
                    continue
            lista_voci = self.spese.get(giorno_obj, [])
            for indice, voce in enumerate(lista_voci): 
                try:
                    try:
                        categoria   = voce[0]
                        descrizione = voce[1]
                    except (KeyError, TypeError):
                        categoria   = campo(voce, "categoria", "")
                        descrizione = campo(voce, "descrizione", "")
                    importo     = campo(voce, "importo", 0.0)
                    tipo        = campo(voce, "tipo", "").capitalize() 
                    metodo_sp   = campo(voce, "metodo_pagamento", "")
                    ora_sp      = campo(voce, "ora", "")
                    hashtag_sp  = campo(voce, "hashtag", [])
                    hashtag_txt_sp = " ".join(hashtag_sp)
                    nome_conto_sp = self._conto_effettivo(voce) or (
                        conto_da_mappa(_agganci_cs, _uso_ordinale_cs, d.strftime("%d-%m-%Y"), float(importo), tipo)
                        if d else ""
                    )
                    if ricerca_rapida:
                        campi_ricerca_rapida = [
                            categoria, descrizione, tipo, str(importo),
                            nome_conto_sp, metodo_sp, hashtag_txt_sp
                        ]
                        matches = any(ricerca_rapida in str(cr).lower() for cr in campi_ricerca_rapida)
                    else:
                        matches = True
                        if filtro_partecipante and filtro_partecipante not in ["", "—"]:
                           _fp_low = filtro_partecipante.lower()
                           if not any(f"{_ico}{_fp_low}" in descrizione.lower() for _ico in ("per·", "ctp·", "cnt·")):
                                matches = False
                        if filtro_testo_globale:
                            testo_da_cercare = f"{descrizione} {categoria} {metodo_sp} {hashtag_txt_sp}".lower()
                            if filtro_testo_globale not in testo_da_cercare: 
                                matches = False
                        if matches and filtro_categoria_esatta not in ["", "—"] and categoria != filtro_categoria_esatta: matches = False
                        if matches and filtro_tipo not in ["", "—"] and tipo != filtro_tipo: matches = False
                        if matches and filtro_anno not in ["", "—"] and d and str(d.year) != filtro_anno: matches = False
                        if matches and filtro_mese_numero and d:
                            if d.strftime('%m') != filtro_mese_numero:
                                matches = False
                        try:
                            da = float(filtri.get("da", "") or "0")
                            a = float(filtri.get("a", "") or "999999999")
                            if matches and not (da <= float(importo) <= a): matches = False 
                        except (ValueError, TypeError): pass
                        if matches and filtri.get("conto", "—") not in ("", "—") and nome_conto_sp != filtri.get("conto"):
                            matches = False
                        if matches and filtri.get("metodo", "—") not in ("", "—") and metodo_sp != filtri.get("metodo"):
                            matches = False
                        if matches and filtri.get("hashtag") and filtri["hashtag"].lower().lstrip("#") not in hashtag_txt_sp.lower():
                            matches = False
                    if matches:
                        importo_formattato = f"{_app._fmt_it(float(importo))} €"
                        iid = f"{giorno_interno}_{indice}" 
                        pool_bloccata = (
                            _ruoli_p.get(str(campo(voce, "id_spesa", ""))) in ("quota", "rientro")
                            or bool(campo(voce, "pool_ref", ""))
                        )
                        if pool_bloccata:
                            iid_bloccati.add(iid)
                            self.selezionate_iid.discard(iid)
                        is_selected = iid in self.selezionate_iid
                        if d and d > datetime.date.today():
                            color_tag = 'futuro'
                        else:
                            color_tag = 'entrata' if tipo == 'Entrata' else 'uscita'
                            oggi_sf = datetime.date.today()
                            if (tipo == 'Uscita' and d
                                    and (d.year, d.month) == (oggi_sf.year, oggi_sf.month)
                                    and categoria in getattr(self, "_budget_sforati", set())):
                                color_tag = 'sforato'
                        tags = ['bloccato'] if pool_bloccata else [color_tag]
                        if is_selected:
                            tags.append('selezionata')
                        checkbox_text = "[–]" if pool_bloccata else ("[X]" if is_selected else "[ ]")
                        self.spese_treeview.insert(
                            "", "end", iid=iid,
                            text=checkbox_text,
                            values=(giorno_visualizzato, categoria, descrizione, tipo, importo_formattato, nome_conto_sp, metodo_sp, ora_sp, hashtag_txt_sp),
                            tags=tags
                        )
                        self.spese_treeview._metodo_lookup[iid] = {
                            "metodo": metodo_sp,
                            "conto": nome_conto_sp,
                            "ora": ora_sp,
                            "hashtag": list(hashtag_sp),
                            "id_ricorrenza": campo(voce, "id_ricorrenza", ""),
                            "data": d.strftime("%d-%m-%Y") if d else "",
                            "categoria": categoria,
                            "importo": float(importo),
                            "tipo": tipo,
                            "id_spesa": campo(voce, "id_spesa", ""),
                        }
                        items_inserted += 1
                except Exception:
                    continue
        if items_inserted == 0 and self.spese:
            self.spese_treeview.insert("", "end", iid="FILTER_MSG", 
                                       text="", 
                                       values=("", "Nessun risultato.", "", "", "", "", "", "", ""),
                                       tags=('empty',))
    def aggiorna_stato_filtri():
        f = self.filtri_cancellazione
        parti = []
        if f.get("ricerca_rapida", "").strip():
            parti.append(f"Ricerca '{f['ricerca_rapida'].strip()}'")
        for k, etich in (("partecipante", "Partecipante "), ("categoria", "Categoria "), ("tipo", ""),
                         ("anno", "Anno "), ("mese", ""), ("conto", "Conto "), ("metodo", "Metodo ")):
            v = f.get(k)
            if v and v != "—":
                parti.append(f"{etich}{v}")
        if f.get("hashtag"):
            parti.append("#" + f["hashtag"].lstrip("#"))
        if f.get("descrizione"):
            parti.append(f"«{f['descrizione']}»")
        if f.get("da") or f.get("a"):
            parti.append(f"Importo {f.get('da') or '…'} → {f.get('a') or '…'}")
        if f.get("data_da") or f.get("data_a"):
            parti.append(f"{f.get('data_da') or '…'} → {f.get('data_a') or '…'}")
        lbl_freccia.config(text="▾" if stato_f["aperta"] else "▸")
        lbl_filtri_attivi.config(
            text="Filtri avanzati  (" + (("filtri attivi: " + ", ".join(parti)) if parti else "nessun filtro attivo") + ")",
            fg="dodgerblue" if parti else self.TEXT_COLOR)
    def seleziona_tutto_azione():
        all_children = self.spese_treeview.get_children()
        self.selezionate_iid.clear()
        items_to_select = []
        for iid in all_children:
            if iid in ("EMPTY_MSG", "FILTER_MSG", "NO_DATA") or iid in iid_bloccati:
                continue
            self.selezionate_iid.add(iid)
            items_to_select.append(iid)
        popola_treeview_spese()
    popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    self._cancella_spese_popup = popup
    popup.transient(self)
    popup.title("Cancella Movimenti Multipli")
    larg, alt = 1366, 660
    x = self.winfo_x() + (self.winfo_width() // 2) - (larg // 2)
    y = self.winfo_y() + (self.winfo_height() // 2) - (alt // 2)
    popup.geometry(f"{larg}x{alt}+{x}+{y}")
    popup.minsize(larg, alt)
    def chiudi_popup_cf():
        popup.destroy()
        self._cancella_spese_popup = None
    popup.bind("<Escape>", lambda e: chiudi_popup_cf())
    tk.Label(popup, text="Seleziona Movimenti da cancellare:", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR, font=("Arial", 12, "bold")).pack(pady=(10, 5))
    top_controls_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    top_controls_frame.pack(fill='x', padx=10, pady=(0, 5))
    tk.Label(
        top_controls_frame,
        image=self.icone_gui.get("search"),
        text=" Ricerca:",
        compound="left",
        bg=self.COLOR_TOPLEVEL,
        fg=self.TEXT_COLOR,
        font=("Arial", 9, "bold")
    ).pack(side="left")
    ricerca_var = tk.StringVar(value=self.filtri_cancellazione.get("ricerca_rapida", ""))
    ricerca_entry = ttk.Entry(top_controls_frame, textvariable=ricerca_var, width=22)
    ricerca_entry.pack(side="left", padx=(4, 14))
    ricerca_entry.focus_set()
    def _aggiorna_ricerca_rapida(*_a):
        self.filtri_cancellazione["ricerca_rapida"] = ricerca_var.get()
        self.selezionate_iid.clear()
        aggiorna_stato_filtri()
        popola_treeview_spese()
    ricerca_var.trace_add("write", _aggiorna_ricerca_rapida)
    mostra_futuro_var = tk.BooleanVar(value=self.filtri_cancellazione.get("mostra_futuro", True))
    ttk.Checkbutton(top_controls_frame, text="Includi Futuri", variable=mostra_futuro_var).pack(side="left", padx=(0, 8))
    def _aggiorna_futuro(*_a):
        self.filtri_cancellazione["mostra_futuro"] = mostra_futuro_var.get()
        popola_treeview_spese()
    mostra_futuro_var.trace_add("write", _aggiorna_futuro)
    filter_control_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    filter_control_frame.pack(fill='x', padx=10, pady=5)
    lbl_freccia = tk.Label(filter_control_frame, bg=self.COLOR_TOPLEVEL, fg="#DC3545", cursor="hand2",
                           font=("Arial", 11, "bold"), width=2)
    lbl_freccia.pack(side="left")
    lbl_filtri_attivi = tk.Label(filter_control_frame, bg=self.COLOR_TOPLEVEL, text="", fg=self.TEXT_COLOR,
                                 cursor="hand2", font=("Arial", 9, "bold"), anchor="w")
    lbl_filtri_attivi.pack(side="left", fill='x', expand=True)
    img_reset_veloce = self.icone_gui.get("reset")
    btn_reset_veloce = ttk.Label(
            filter_control_frame, 
            compound="left", 
            image=img_reset_veloce, 
            text=" Reset Filtri" if img_reset_veloce else "Reset Filtri", 
            background=self.COLOR_WIDGET_BG, 
            foreground=self.TEXT_COLOR, 
            cursor="hand2", 
            padding=(10, 5)
    )
    btn_reset_veloce.pack(side="right", padx=(10, 0))
    def esegui_reset_totale(e):
            self.filtri_cancellazione = {
                    "partecipante": "",
                    "descrizione": "",
                    "categoria": "",
                    "tipo": "",
                    "anno": "",
                    "mese": "",
                    "da": "",
                    "a": "",
                    "conto": "",
                    "metodo": "",
                    "hashtag": "",
                    "mostra_futuro": True,
                    "data_da": "",
                    "data_a": "",
                    "ricerca_rapida": ""
            }
            _reset_pannello()
            mostra_futuro_var.set(True)
            data_da_var.set("")
            data_a_var.set("")
            ricerca_var.set("")
            self.selezionate_iid.clear()
            aggiorna_stato_filtri()
            popola_treeview_spese()
    btn_reset_veloce.bind("<Button-1>", esegui_reset_totale)
    bg_f = self.COLOR_TOPLEVEL
    _profilo_ac = getattr(_app, "PROFILO_ATTIVO", "Principale")
    _gestore_ac = _profilo_ac if _profilo_ac != "Principale" else os.path.basename(os.getcwd())
    _nomi_reg_ac = [(p.get("nome", "") if isinstance(p, dict) else p) for p in self.nomi_partecipanti]
    _partec_f = [""]
    if self._gestore_partecipa() and _gestore_ac not in _nomi_reg_ac:
        _partec_f.append(f"PER· {_gestore_ac}")
    _partec_f += [
        f"CNT· {p['nome']}" if p.get("tipo") == "contenitore" else
        f"CTP· {p['nome']}" if p.get("tipo") == "personale" else
        f"PER· {p['nome']}"
        for p in sorted(self.nomi_partecipanti, key=lambda p: (p.get("nome", "") if isinstance(p, dict) else p).lower())
    ]
    try:
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _fp:
            _conti_f = [""] + [c.get("nome", "") for c in json.load(_fp).get("conti", [])]
    except Exception:
        _conti_f = [""]
    _anni_f = set()
    for _g in self.spese.keys():
        try:
            _dd = _g if isinstance(_g, datetime.date) else datetime.datetime.strptime(str(_g), "%Y-%m-%d").date()
            _anni_f.add(str(_dd.year))
        except Exception:
            continue
    _anni_f = [""] + sorted(_anni_f, reverse=True)
    var_f_desc = tk.StringVar(value="")
    var_f_partec = tk.StringVar(value="")
    var_f_cat = tk.StringVar(value="")
    var_f_tipo = tk.StringVar(value="")
    var_f_anno = tk.StringVar(value="")
    var_f_mese = tk.StringVar(value="")
    var_f_da = tk.StringVar(value="")
    var_f_a = tk.StringVar(value="")
    var_f_conto = tk.StringVar(value="")
    var_f_metodo = tk.StringVar(value="")
    var_f_hashtag = tk.StringVar(value="")
    data_da_var = tk.StringVar(value="")
    data_a_var = tk.StringVar(value="")
    _vars_pannello = (var_f_desc, var_f_partec, var_f_cat, var_f_tipo, var_f_anno, var_f_mese,
                      var_f_da, var_f_a, var_f_conto, var_f_metodo, var_f_hashtag,
                      data_da_var, data_a_var)
    body_f = tk.Frame(popup, bg=bg_f)
    def _riga_f():
        r = tk.Frame(body_f, bg=bg_f)
        r.pack(fill="x", pady=2, padx=10)
        return r
    def _etichetta_f(r, testo, pad=(10, 4)):
        tk.Label(r, text=testo, bg=bg_f, fg=self.TEXT_COLOR).pack(side="left", padx=pad)
    def _combo_f(r, var, valori, w):
        ttk.Combobox(r, values=valori, textvariable=var, style="Border.TCombobox",
                     state="readonly", width=w).pack(side="left")
    def _entry_f(r, var, w):
        ttk.Entry(r, textvariable=var, width=w).pack(side="left")
    r1_f, r2_f = _riga_f(), _riga_f()
    _etichetta_f(r1_f, "Tipo:", (4, 4))
    _combo_f(r1_f, var_f_tipo, ["", "Entrata", "Uscita"], 9)
    _etichetta_f(r1_f, "Categoria:")
    _combo_f(r1_f, var_f_cat, [""] + sorted(self.categorie_tipi.keys()), 18)
    _etichetta_f(r1_f, "Anno:")
    _combo_f(r1_f, var_f_anno, _anni_f, 7)
    _etichetta_f(r1_f, "Mese:")
    _combo_f(r1_f, var_f_mese, [""] + NOMI_MESI_ITALIANO, 11)
    _etichetta_f(r1_f, "Partecipanti:")
    _combo_f(r1_f, var_f_partec, _partec_f, 18)
    _etichetta_f(r1_f, "Conto:")
    _combo_f(r1_f, var_f_conto, _conti_f, 14)
    _etichetta_f(r1_f, "Metodo Pag.:")
    _combo_f(r1_f, var_f_metodo, [""] + METODI_PAGAMENTO, 18)
    _etichetta_f(r2_f, "Testo Globale:", (4, 4))
    _entry_f(r2_f, var_f_desc, 24)
    _etichetta_f(r2_f, "Hashtag:")
    _entry_f(r2_f, var_f_hashtag, 14)
    _etichetta_f(r2_f, "Importo da (€):")
    _entry_f(r2_f, var_f_da, 9)
    _etichetta_f(r2_f, "a:", (6, 4))
    _entry_f(r2_f, var_f_a, 9)
    img_cal_f = self.icone_gui.get("calendario")
    def _cal_btn_f(entry, var):
        b = tk.Label(r2_f, image=img_cal_f, bg=bg_f, cursor="hand2", padx=2,
                     text="" if img_cal_f else "📅", fg=self.TEXT_COLOR)
        b.image = img_cal_f
        b.pack(side="left", padx=(2, 0))
        b.bind("<Button-1>", lambda e: self.mostra_calendario_popup_semplice(entry, var))
    _etichetta_f(r2_f, "Dal:")
    data_da_entry = ttk.Entry(r2_f, textvariable=data_da_var, width=11)
    data_da_entry.pack(side="left")
    _cal_btn_f(data_da_entry, data_da_var)
    _etichetta_f(r2_f, "Al:", (8, 4))
    data_a_entry = ttk.Entry(r2_f, textvariable=data_a_var, width=11)
    data_a_entry.pack(side="left")
    _cal_btn_f(data_a_entry, data_a_var)
    tk.Label(r2_f, text="(GG-MM-AAAA)", bg=bg_f, fg="gray", font=("Arial", 8, "italic")).pack(side="left", padx=(4, 0))
    def _partec_pulito(v):
        v = (v or "").strip()
        for _ico in ("CNT· ", "PER· ", "CTP· ", "CNT·", "PER·", "CTP·"):
            if v.startswith(_ico):
                return v[len(_ico):].strip()
        return v
    def _applica_pannello(*_):
        if stato_f["sosp"]:
            return
        self.filtri_cancellazione.update({
            "descrizione": var_f_desc.get(),
            "partecipante": _partec_pulito(var_f_partec.get()),
            "categoria": var_f_cat.get(),
            "tipo": var_f_tipo.get(),
            "anno": var_f_anno.get(),
            "mese": var_f_mese.get(),
            "da": var_f_da.get(),
            "a": var_f_a.get(),
            "conto": var_f_conto.get(),
            "metodo": var_f_metodo.get(),
            "hashtag": var_f_hashtag.get(),
            "data_da": data_da_var.get(),
            "data_a": data_a_var.get(),
        })
        for _e, _v in ((data_da_entry, data_da_var), (data_a_entry, data_a_var)):
            _txt = _v.get().strip()
            _ko = False
            if _txt:
                try:
                    datetime.datetime.strptime(_txt, "%d-%m-%Y")
                except ValueError:
                    _ko = True
            try:
                _e.configure(foreground="#DC3545" if _ko else self.TEXT_COLOR)
            except tk.TclError:
                pass
        self.selezionate_iid.clear()
        aggiorna_stato_filtri()
        popola_treeview_spese()
    def _reset_pannello():
        stato_f["sosp"] = True
        try:
            for v in _vars_pannello:
                v.set("")
        finally:
            stato_f["sosp"] = False
    for _v in _vars_pannello:
        _v.trace_add("write", _applica_pannello)
    def _apri_chiudi_f(*_):
        stato_f["aperta"] = not stato_f["aperta"]
        if stato_f["aperta"]:
            body_f.pack(fill="x", before=tree_frame)
        else:
            body_f.pack_forget()
        aggiorna_stato_filtri()
    for _w in (lbl_freccia, lbl_filtri_attivi):
        _w.bind("<Button-1>", _apri_chiudi_f)
    tree_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    tree_frame.pack(fill='both', expand=True, padx=10, pady=5) 
    scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", style="Vertical.TScrollbar")
    scrollbar.pack(side="right", fill="y")
    self.spese_treeview = ttk.Treeview(
        tree_frame,
        columns=("Giorno", "Categoria", "Descrizione", "Tipo", "Importo", "Conto", "Metodo", "Ora", "Hashtag"),
        show=("tree", "headings"), 
        yscrollcommand=scrollbar.set,
        height=15
    )
    self.spese_treeview.pack(side="left", fill="both", expand=True) 
    scrollbar.config(command=self.spese_treeview.yview)
    self.spese_treeview.heading("#0", text="Sel.", anchor="center") 
    self.spese_treeview.heading("Giorno", text="Giorno", anchor="center", 
                                command=lambda: sort_treeview_column(self.spese_treeview, "Giorno", True, data_type='date')) 
    self.spese_treeview.heading("Categoria", text="Categoria", anchor="center", 
                                command=lambda: sort_treeview_column(self.spese_treeview, "Categoria", False, data_type='string'))
    self.spese_treeview.heading("Descrizione", text="Descrizione", anchor="center", 
                                command=lambda: sort_treeview_column(self.spese_treeview, "Descrizione", False, data_type='string'))
    self.spese_treeview.heading("Tipo", text="Tipo", anchor="center", 
                                command=lambda: sort_treeview_column(self.spese_treeview, "Tipo", False, data_type='string'))
    self.spese_treeview.heading("Importo", text="Importo", anchor="center", 
                                command=lambda: sort_treeview_column(self.spese_treeview, "Importo", False, data_type='float'))
    self.spese_treeview.heading("Conto", text="Conto", anchor="center",
                                command=lambda: sort_treeview_column(self.spese_treeview, "Conto", False, data_type='string'))
    self.spese_treeview.heading("Metodo", text="Metodo", anchor="center",
                                command=lambda: sort_treeview_column(self.spese_treeview, "Metodo", False, data_type='string'))
    self.spese_treeview.heading("Ora", text="Ora", anchor="center",
                                command=lambda: sort_treeview_column(self.spese_treeview, "Ora", False, data_type='string'))
    self.spese_treeview.heading("Hashtag", text="Hashtag", anchor="center",
                                command=lambda: sort_treeview_column(self.spese_treeview, "Hashtag", False, data_type='string'))
    self.spese_treeview.column("#0", width=40, anchor="center", stretch=False) 
    self.spese_treeview.column("Giorno", width=90, anchor="w", stretch=False)
    self.spese_treeview.column("Categoria", width=150, anchor="w", stretch=False)
    self.spese_treeview.column("Descrizione", width=200, anchor="w", stretch=True)
    self.spese_treeview.column("Tipo", width=60, anchor="center", stretch=False) 
    self.spese_treeview.column("Importo", width=100, anchor="e", stretch=False)
    self.spese_treeview.column("Conto", width=100, anchor="center", stretch=False)
    self.spese_treeview.column("Metodo", width=100, anchor="center", stretch=False)
    self.spese_treeview.column("Ora", width=50, anchor="center", stretch=False)
    self.spese_treeview.column("Hashtag", width=120, anchor="center", stretch=False)
    self.spese_treeview.tag_configure('selezionata') 
    self.spese_treeview.tag_configure('entrata', foreground='green')
    self.spese_treeview.tag_configure('uscita', foreground='red') 
    self.spese_treeview.tag_configure('futuro', foreground='#E5C07B', font=('Arial', 9, 'italic'))
    self.spese_treeview.tag_configure('sforato', foreground='#C08081', font=('Arial', 9, 'bold'))
    self.spese_treeview.tag_configure('empty', foreground='gray', font=('Arial', 10, 'italic'))
    self.spese_treeview.tag_configure('bloccato', foreground='gray', font=('Arial', 9, 'italic'))
    def vai_a_spesa_doppio_clic(event):
        iid = self.spese_treeview.identify_row(event.y)
        if not iid or iid in ("EMPTY_MSG", "FILTER_MSG"): return
        toggle_selection_treeview(event)
        vals = self.spese_treeview.item(iid, "values")
        try:
            d = datetime.datetime.strptime(str(vals[0]).strip(), "%d/%m/%Y").date()
        except (ValueError, IndexError):
            return
        desc_sel = str(vals[2])[:20]
        _id_sp = (getattr(self.spese_treeview, "_metodo_lookup", {}).get(iid) or {}).get("id_spesa", "")
        chiudi_popup_cf()
        if self.stats_view_mode.get() != "tabella":
            self.mostra_treeview_statistiche()
        self.stats_view_mode.set("giorno")
        if hasattr(self, "cal"):
            self.cal.selection_set(d)
            self.cal._sel_date = d
            self.cal.event_generate("<<CalendarSelected>>")
        self.update_stats()
        self.stats_label.config(
            text=f"Riepilogo Giornaliero - {d.strftime('%d-%m-%Y')}",
            foreground="purple", font=("Arial", 10, "bold"))
        self.after(400, lambda: self.seleziona_spesa_in_lista(d, desc_sel, _id_sp))
    self.spese_treeview.bind('<Button-1>', toggle_selection_treeview)
    self.spese_treeview.bind('<Double-1>', vai_a_spesa_doppio_clic)
    btn_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    btn_frame.pack(pady=10) 
    img_canc_sel = self.icone_gui.get("delete")
    btn_canc_sel = ttk.Label(btn_frame, compound="left", image=img_canc_sel, text=" Cancella Selezionate" if img_canc_sel else "Cancella Selezionate", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
    btn_canc_sel.pack(side="left", padx=5)
    btn_canc_sel.bind("<Button-1>", lambda e: esegui_cancellazione_azione())
    img_sel_tutto = self.icone_gui.get("salva")
    btn_sel_tutto = ttk.Label(btn_frame, compound="left", image=img_sel_tutto, text=" Seleziona Tutto" if img_sel_tutto else "Seleziona Tutto", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
    btn_sel_tutto.pack(side="left", padx=5)
    btn_sel_tutto.bind("<Button-1>", lambda e: seleziona_tutto_azione())
    img_desel = self.icone_gui.get("reset")
    btn_desel = ttk.Label(btn_frame, compound="left", image=img_desel, text=" Deseleziona Tutto" if img_desel else "Deseleziona Tutto", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
    btn_desel.pack(side="left", padx=5)
    btn_desel.bind("<Button-1>", lambda e: [self.selezionate_iid.clear(), popola_treeview_spese()])
    img_chiudi_pop = self.icone_gui.get("chiudi")
    btn_chiudi_pop = ttk.Label(btn_frame, compound="left", image=img_chiudi_pop, text=" Chiudi" if img_chiudi_pop else "Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
    btn_chiudi_pop.pack(side="left", padx=5)
    btn_chiudi_pop.bind("<Button-1>", lambda e: chiudi_popup_cf())
    aggiorna_stato_filtri() 
    popola_treeview_spese()
    sort_treeview_column(self.spese_treeview, "Giorno", True, data_type='date') 
    def _refresh_da_modifica_esterna():
        # Il web (o altro) ha cambiato le spese: rilegge l'elenco mantenendo la selezione per id_spesa
        try:
            lk = getattr(self.spese_treeview, "_metodo_lookup", {}) or {}
            ids_sel = {str((lk.get(i) or {}).get("id_spesa", "")) for i in self.selezionate_iid}
            ids_sel.discard("")
            popola_treeview_spese()
            lk = self.spese_treeview._metodo_lookup
            self.selezionate_iid.clear()
            for iid, info in lk.items():
                if str(info.get("id_spesa", "")) in ids_sel:
                    self.selezionate_iid.add(iid)
            popola_treeview_spese()
        except tk.TclError:
            pass
    if hasattr(self, "registra_refresh_finestra"):
        self.registra_refresh_finestra(popup, _refresh_da_modifica_esterna)
    self._bind_tooltip_metodo(self.spese_treeview, col_desc=2)
    popup.wait_visibility()
    popup.grab_set()
