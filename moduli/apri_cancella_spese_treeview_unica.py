#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import datetime
import tkinter as tk
from tkinter import ttk
from moduli.modello_spesa import campo, METODI_PAGAMENTO

def apri_cancella_spese_treeview_unica(self):
    if hasattr(self, '_cancella_spese_popup') and self._cancella_spese_popup and self._cancella_spese_popup.winfo_exists():
        self._cancella_spese_popup.lift()
        return
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    NOMI_MESI_ITALIANO = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", 
                          "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    if not hasattr(self, 'spese') or not isinstance(self.spese, dict):
        self.spese = {} 
    self.filtri_cancellazione = {
        "partecipante": "—",
        "descrizione": "",
        "categoria": "—",
        "tipo": "—",
        "anno": "—",
        "mese": "—",
        "da": "",
        "a": "",
        "conto": "—",
        "metodo": "—",
        "hashtag": "",
        "mostra_futuro": True,
        "data_da": "",
        "data_a": "",
        "ricerca_rapida": ""
    }
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
                except: return value
            items_to_sort.sort(key=get_sort_key, reverse=reverse)
            if initial: tree.withdraw() 
            for index, (val, k) in enumerate(items_to_sort):
                tree.move(k, '', index)
            if initial: tree.deiconify()
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
        is_selected = row_id in self.selezionate_iid
        current_tags = list(self.spese_treeview.item(row_id, 'tags'))
        type_tag = [t for t in current_tags if t in ('entrata', 'uscita', 'futuro')] 
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
        testo_messaggio = (
            f"⚠️ CONFERMA CANCELLAZIONE DEFINITIVA\n\n"
            f"Stai per cancellare {num_selezionate} elementi selezionati.\n\n"
            f"ATTENZIONE: Questa azione è IRREVERSIBILE e i dati non potranno più essere recuperati.\n"
            f"Sei assolutamente sicuro di voler procedere con l'eliminazione?"
        )
        response = self.show_custom_askyesno("Conferma Cancellazione", testo_messaggio)
        if not response: return
        spese_da_mantenere = {}
        self.spese_cancellate_tmp = {}
        for giorno_obj in self.spese.keys():
            giorno_interno = str(giorno_obj)
            for indice, voce in enumerate(self.spese.get(giorno_obj, [])):
                iid = f"{giorno_interno}_{indice}"
                if iid in self.selezionate_iid:
                    if giorno_obj not in self.spese_cancellate_tmp:
                        self.spese_cancellate_tmp[giorno_obj] = []
                    self.spese_cancellate_tmp[giorno_obj].append(voce)
        for giorno_obj in self.spese.keys():
            giorno_interno = str(giorno_obj)
            spese_mantenute_giorno = []
            for indice, voce in enumerate(self.spese.get(giorno_obj, [])):
                iid = f"{giorno_interno}_{indice}"
                if iid not in self.selezionate_iid:
                    spese_mantenute_giorno.append(voce)
            if spese_mantenute_giorno:
                spese_da_mantenere[giorno_obj] = spese_mantenute_giorno
        self.spese = spese_da_mantenere
        self.selezionate_iid.clear()
        popola_treeview_spese()
        if hasattr(self, 'refresh_gui'): self.refresh_gui()
        if hasattr(self, 'save_db'): self.save_db()
        if hasattr(self, 'annulla_azione_gamification'):
            for lista_voci_canc in self.spese_cancellate_tmp.values():
                for _voce in lista_voci_canc:
                    self.annulla_azione_gamification("movimento")
        self._sync_fairshare_e_aggiorna()
        self.show_custom_warning("Successo", f"✓ {num_selezionate} spese sono state cancellate.")
    def popola_treeview_spese():
        self.spese_treeview.delete(*self.spese_treeview.get_children())
        if not self.spese:
            self.spese_treeview.insert("", "end", iid="FILTER_MSG",
                                       text="",
                                       values=("—", "Nessuna spesa presente.", "", "", "", "", "", "", ""),
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
                    nome_conto_sp = campo(voce, "conto", "") or (self._trova_conto_da_portafoglio(d, float(importo), tipo) if d else "")
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
                        importo_formattato = f"{float(importo):.2f} €"
                        iid = f"{giorno_interno}_{indice}" 
                        is_selected = iid in self.selezionate_iid
                        if d and d > datetime.date.today():
                            color_tag = 'futuro'
                        else:
                            color_tag = 'entrata' if tipo == 'Entrata' else 'uscita'
                        tags = [color_tag]
                        if is_selected:
                            tags.append('selezionata')
                        checkbox_text = "[X]" if is_selected else "[ ]" 
                        self.spese_treeview.insert(
                            "", "end", iid=iid,
                            text=checkbox_text,
                            values=(giorno_visualizzato, categoria, descrizione, tipo, importo_formattato, nome_conto_sp, metodo_sp, ora_sp, hashtag_txt_sp),
                            tags=tags
                        )
                        items_inserted += 1
                except Exception:
                    continue
        if items_inserted == 0 and self.spese:
            self.spese_treeview.insert("", "end", iid="FILTER_MSG", 
                                       text="", 
                                       values=("—", "Nessun risultato.", "", "", "", "", "", "", ""),
                                       tags=('empty',))
    def aggiorna_stato_filtri():
        chiavi_escluse = ("mostra_futuro", "data_da", "data_a", "ricerca_rapida")
        attivi = {k: v for k, v in self.filtri_cancellazione.items()
                  if k not in chiavi_escluse and v and v != "—"}
        ricerca_attiva = self.filtri_cancellazione.get("ricerca_rapida", "").strip()
        if not attivi and not ricerca_attiva:
            lbl_filtri_attivi.config(text="Nessun filtro attivo. Attiva un Filtro Avanzato.", fg="gray")
        else:
            testo_formattato = []
            if ricerca_attiva:
                testo_formattato.append(f"Ricerca rapida: '{ricerca_attiva}'")
            for k, v in attivi.items():
                if k == 'descrizione':
                    testo_formattato.append(f"Testo Globale: {v}")
                elif k == 'partecipante':
                    testo_formattato.append(f"Partecipante: {v}")
                else:
                    testo_formattato.append(f"{k.capitalize()}: {v}")
            testo = ", ".join(testo_formattato)
            lbl_filtri_attivi.config(text=f"Filtri attivi: {testo}", fg="dodgerblue")
    def apri_filtri_avanzati():
        filtro_win = tk.Toplevel(popup, bg=self.COLOR_TOPLEVEL)
        filtro_win.title("⚙️ Filtri Avanzati di Cancellazione")
        larghezza_finestra = 400
        altezza_finestra = 460
        x = popup.winfo_rootx() + (popup.winfo_width() // 2) - (larghezza_finestra // 2)
        y = popup.winfo_rooty() + (popup.winfo_height() // 2) - (altezza_finestra // 2)
        filtro_win.geometry(f"{larghezza_finestra}x{altezza_finestra}+{x}+{y}")
        filtro_win.resizable(False, False)
        filtro_win.transient(popup)
        filtro_win.update_idletasks()
        filtro_win.grab_set()
        filtro_win.bind("<Escape>", lambda e: filtro_win.destroy())
        _profilo_attivo_ac = getattr(_app, "PROFILO_ATTIVO", "Principale")
        _gestore_nome_canc = _profilo_attivo_ac if _profilo_attivo_ac != "Principale" else os.path.basename(os.getcwd())
        _nomi_reg_canc = [(p.get("nome", "") if isinstance(p, dict) else p) for p in self.nomi_partecipanti]
        nomi_p = ["—"]
        if self._gestore_partecipa() and _gestore_nome_canc not in _nomi_reg_canc:
            nomi_p.append(f"PER· {_gestore_nome_canc}")
        nomi_p += [
                   f"CNT· {p['nome']}" if p.get("tipo") == "contenitore" else
                   f"CTP· {p['nome']}" if p.get("tipo") == "personale" else
                   f"PER· {p['nome']}"
                   for p in sorted(self.nomi_partecipanti, key=lambda p: (p.get("nome", "") if isinstance(p, dict) else p).lower())
        ]
        p_salvato = self.filtri_cancellazione.get("partecipante", "—")
        p_con_icona = "—"
        if p_salvato != "—":
            for voce in nomi_p:
                if voce.endswith(p_salvato):
                    p_con_icona = voce
                    break
        descrizione_var = tk.StringVar(value=self.filtri_cancellazione.get("descrizione", ""))
        partecipante_var = tk.StringVar(value=p_con_icona)
        categoria_var = tk.StringVar(value=self.filtri_cancellazione.get("categoria", "—"))
        tipo_var = tk.StringVar(value=self.filtri_cancellazione.get("tipo", "—"))
        anno_var = tk.StringVar(value=self.filtri_cancellazione.get("anno", "—"))
        mese_var = tk.StringVar(value=self.filtri_cancellazione.get("mese", "—"))
        da_var = tk.StringVar(value=self.filtri_cancellazione.get("da", ""))
        a_var = tk.StringVar(value=self.filtri_cancellazione.get("a", ""))
        conto_var = tk.StringVar(value=self.filtri_cancellazione.get("conto", "—"))
        metodo_var = tk.StringVar(value=self.filtri_cancellazione.get("metodo", "—"))
        hashtag_var = tk.StringVar(value=self.filtri_cancellazione.get("hashtag", ""))
        try:
            with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _f:
                conti_nomi = ["—"] + [c.get("nome","") for c in json.load(_f).get("conti",[])]
        except Exception:
            conti_nomi = ["—"]
        def crea_riga(testo, var, values=None):
            f = tk.Frame(filtro_win, bg=self.COLOR_TOPLEVEL)
            f.pack(fill="x", padx=12, pady=5)
            tk.Label(f, text=testo, fg=self.TEXT_COLOR, bg=self.COLOR_TOPLEVEL, width=16, anchor="w").pack(side="left")
            if values:
                ttk.Combobox(f, textvariable=var, values=values, style="Border.TCombobox", state="readonly", width=20).pack(side="left")
            else:
                ttk.Entry(f, textvariable=var, width=22).pack(side="left")
        nomi_p = ["—"]
        if self._gestore_partecipa() and _gestore_nome_canc not in _nomi_reg_canc:
            nomi_p.append(f"PER· {_gestore_nome_canc}")
        nomi_p += [
           f"CNT· {p['nome']}" if p.get("tipo") == "contenitore" else
           f"CTP· {p['nome']}" if p.get("tipo") == "personale" else
           f"PER· {p['nome']}"
           for p in sorted(self.nomi_partecipanti, key=lambda p: (p.get("nome", "") if isinstance(p, dict) else p).lower())
        ]
        tutte_cat = ["—"] + sorted(list(self.categorie_tipi.keys()))
        anni = ["—"]
        for giorno_obj in self.spese.keys():
            try:
                d = giorno_obj if isinstance(giorno_obj, datetime.date) else datetime.datetime.strptime(str(giorno_obj), "%Y-%m-%d").date()
                anni.append(str(d.year))
            except Exception:
                continue
        anni = sorted(list(set(anni)), reverse=True)
        nomi_mesi_dropdown = ["—"] + NOMI_MESI_ITALIANO
        crea_riga("Testo Globale:", descrizione_var)
        crea_riga("Partecipante:", partecipante_var, nomi_p)
        crea_riga("Categoria:", categoria_var, tutte_cat)
        crea_riga("Tipo voce:", tipo_var, ["—", "Entrata", "Uscita"])
        crea_riga("Anno:", anno_var, anni)
        crea_riga("Mese:", mese_var, nomi_mesi_dropdown)
        crea_riga("Importo da (€):", da_var)
        crea_riga("Importo a (€):", a_var)
        crea_riga("Conto:", conto_var, conti_nomi)
        crea_riga("Metodo Pag.:", metodo_var, ["—"] + METODI_PAGAMENTO)
        crea_riga("Hashtag:", hashtag_var)
        def applica():
            p_selezionato = partecipante_var.get()
            if p_selezionato and p_selezionato != "—":
                p_pulito = p_selezionato.strip()
                for _ico in ("CNT· ", "PER· ", "CTP· ", "CNT·", "PER·", "CTP·"):
                    if p_pulito.startswith(_ico):
                        p_pulito = p_pulito[len(_ico):].strip()
                        break
            else:
                p_pulito = p_selezionato
            self.filtri_cancellazione = {
                "descrizione": descrizione_var.get(),
                "partecipante": p_pulito,
                "categoria": categoria_var.get(),
                "tipo": tipo_var.get(),
                "anno": anno_var.get(),
                "mese": mese_var.get(),
                "da": da_var.get(),
                "a": a_var.get(),
                "conto": conto_var.get(),
                "metodo": metodo_var.get(),
                "hashtag": hashtag_var.get()
            }
            self.selezionate_iid.clear()
            aggiorna_stato_filtri()
            popola_treeview_spese()
            filtro_win.destroy()
        def cancella_filtri():
            descrizione_var.set("")
            partecipante_var.set("—")
            categoria_var.set("—")
            tipo_var.set("—")
            anno_var.set("—")
            mese_var.set("—")
            da_var.set("")
            a_var.set("")
            conto_var.set("—")
            metodo_var.set("—")
            hashtag_var.set("")
            self.filtri_cancellazione = {
                "partecipante": "—",
                "descrizione": "",
                "categoria": "—",
                "tipo": "—",
                "anno": "—",
                "mese": "—",
                "da": "",
                "a": "",
                "conto": "—",
                "metodo": "—",
                "hashtag": ""
            }
            self.selezionate_iid.clear()
            aggiorna_stato_filtri()
            popola_treeview_spese()
            filtro_win.destroy()
        f_btn = tk.Frame(filtro_win, bg=self.COLOR_TOPLEVEL)
        f_btn.pack(pady=10)
        img_applica_f = self.icone_gui.get("salva")
        btn_applica_f = ttk.Label(f_btn, compound="left", image=img_applica_f, text=" Applica Filtri" if img_applica_f else "Applica Filtri", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_applica_f.pack(side="left", padx=10)
        btn_applica_f.bind("<Button-1>", lambda e: applica())
        img_cancella_f = self.icone_gui.get("reset")
        btn_cancella_f = ttk.Label(f_btn, compound="left", image=img_cancella_f, text=" Cancella Filtri" if img_cancella_f else "Cancella Filtri", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_cancella_f.pack(side="right", padx=10)
        btn_cancella_f.bind("<Button-1>", lambda e: cancella_filtri())
    def seleziona_tutto_azione():
        all_children = self.spese_treeview.get_children()
        self.selezionate_iid.clear()
        items_to_select = []
        for iid in all_children:
            if iid in ("EMPTY_MSG", "FILTER_MSG", "NO_DATA"):
                continue
            self.selezionate_iid.add(iid)
            items_to_select.append(iid)
        popola_treeview_spese()
    popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    self._cancella_spese_popup = popup
    popup.transient(self)
    popup.title("Cancella Movimenti Multipli")
    larg, alt = 1300, 600
    x = self.winfo_x() + (self.winfo_width() // 2) - (larg // 2)
    y = self.winfo_y() + (self.winfo_height() // 2) - (alt // 2)
    popup.geometry(f"{larg}x{alt}+{x}+{y}")
    popup.minsize(larg, alt)
    def chiudi_popup_cf():
        popup.destroy()
        self._cancella_spese_popup = None
    popup.bind("<Escape>", lambda e: chiudi_popup_cf())
    popup.wait_visibility()
    popup.grab_set()
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
    tk.Label(top_controls_frame, text="Dal:", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 9)).pack(side="left", padx=(4, 2))
    data_da_var = tk.StringVar(value=self.filtri_cancellazione.get("data_da", ""))
    data_da_entry = ttk.Entry(top_controls_frame, textvariable=data_da_var, width=11)
    data_da_entry.pack(side="left")
    btn_cal_da_cf = ttk.Label(top_controls_frame, text="📅", cursor="hand2",
                              background=self.COLOR_WIDGET_BG, padding=(3, 2))
    btn_cal_da_cf.pack(side="left", padx=(2, 8))
    btn_cal_da_cf.bind("<Button-1>", lambda e: self.mostra_calendario_popup_semplice(data_da_entry, data_da_var))
    tk.Label(top_controls_frame, text="Al:", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 9)).pack(side="left", padx=(0, 2))
    data_a_var = tk.StringVar(value=self.filtri_cancellazione.get("data_a", ""))
    data_a_entry = ttk.Entry(top_controls_frame, textvariable=data_a_var, width=11)
    data_a_entry.pack(side="left")
    btn_cal_a_cf = ttk.Label(top_controls_frame, text="📅", cursor="hand2",
                             background=self.COLOR_WIDGET_BG, padding=(3, 2))
    btn_cal_a_cf.pack(side="left", padx=(2, 8))
    btn_cal_a_cf.bind("<Button-1>", lambda e: self.mostra_calendario_popup_semplice(data_a_entry, data_a_var))
    def _aggiorna_filtro_date(*_a):
        self.filtri_cancellazione["mostra_futuro"] = mostra_futuro_var.get()
        self.filtri_cancellazione["data_da"] = data_da_var.get()
        self.filtri_cancellazione["data_a"] = data_a_var.get()
        popola_treeview_spese()
    mostra_futuro_var.trace_add("write", _aggiorna_filtro_date)
    data_da_var.trace_add("write", _aggiorna_filtro_date)
    data_a_var.trace_add("write", _aggiorna_filtro_date)
    filter_control_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    filter_control_frame.pack(fill='x', padx=10, pady=5)
    lbl_filtri_attivi = tk.Label(filter_control_frame, bg=self.COLOR_TOPLEVEL, text="", fg="gray")
    lbl_filtri_attivi.pack(side="left", fill='x', expand=True)
    img_filtri_av = self.icone_gui.get("filtri")
    btn_filtri_av = ttk.Label(filter_control_frame, compound="left", image=img_filtri_av, text=" Filtri Avanzati" if img_filtri_av else "Filtri Avanzati", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
    btn_filtri_av.pack(side="right")
    btn_filtri_av.bind("<Button-1>", lambda e: apri_filtri_avanzati())
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
                    "partecipante": "—",
                    "descrizione": "",
                    "categoria": "—",
                    "tipo": "—",
                    "anno": "—",
                    "mese": "—",
                    "da": "",
                    "a": "",
                    "conto": "—",
                    "metodo": "—",
                    "hashtag": "",
                    "mostra_futuro": True,
                    "data_da": "",
                    "data_a": "",
                    "ricerca_rapida": ""
            }
            mostra_futuro_var.set(True)
            data_da_var.set("")
            data_a_var.set("")
            ricerca_var.set("")
            self.selezionate_iid.clear()
            aggiorna_stato_filtri()
            popola_treeview_spese()
    btn_reset_veloce.bind("<Button-1>", esegui_reset_totale)
    tree_frame = tk.Frame(popup)
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
    self.spese_treeview.column("Conto", width=100, anchor="w", stretch=False)
    self.spese_treeview.column("Metodo", width=100, anchor="w", stretch=False)
    self.spese_treeview.column("Ora", width=50, anchor="center", stretch=False)
    self.spese_treeview.column("Hashtag", width=120, anchor="w", stretch=False)
    self.spese_treeview.tag_configure('selezionata', background='#FFEBCC') 
    self.spese_treeview.tag_configure('entrata', foreground='green')
    self.spese_treeview.tag_configure('uscita', foreground='red') 
    self.spese_treeview.tag_configure('futuro', foreground='#E5C07B', font=('Arial', 9, 'italic'))
    self.spese_treeview.tag_configure('empty', foreground='gray', font=('Arial', 10, 'italic'))
    self.spese_treeview.bind('<Button-1>', toggle_selection_treeview)
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
    self._bind_tooltip_metodo(self.spese_treeview, col_desc=2)

