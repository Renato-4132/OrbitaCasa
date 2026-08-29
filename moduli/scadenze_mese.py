#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import tkinter as tk
from tkinter import ttk
from moduli.modello_spesa import campo

# Gestione e Visualizzazione delle Scadenze/Ricorrenze Mensili
def scadenze_mese(self):
    if hasattr(self, '_scadenze_popup') and self._scadenze_popup and self._scadenze_popup.winfo_exists():
        self._scadenze_popup.lift()
        return
    def ordina_colonna(treeview, col, reverse):
        def converti(valore):
            if col in ("data", "scadenza"):
                try:
                    return datetime.datetime.strptime(valore, "%d-%m-%Y")
                except:
                    return datetime.datetime.max
            elif col == "importo":
                try:
                    return float(valore.replace("€", "").replace(".", "").replace(",", ".").strip())
                except:
                    return 0
            else:
                return valore.lower() if isinstance(valore, str) else valore
        dati = [(treeview.set(k, col), k) for k in treeview.get_children("")]
        dati.sort(key=lambda t: converti(t[0]), reverse=reverse)
        for index, (val, k) in enumerate(dati):
            treeview.move(k, "", index)
        for c in treeview["columns"]:
            base_text = c.replace("_", " ").capitalize()
            if c == col:
                freccia = " ▲" if not reverse else " ▼"
                treeview.heading(
                    c, 
                    text=base_text + freccia, 
                    command=lambda _c=c: ordina_colonna(treeview, _c, not reverse)
                )
            else:
                treeview.heading(
                    c, 
                    text=base_text, 
                    command=lambda _c=c: ordina_colonna(treeview, _c, False)
                )
    def calcola_data_fine(data_inizio, n_volte, periodo):
        if not data_inizio or not isinstance(n_volte, int) or n_volte < 1:
            return "N/D"
        periodo = periodo.lower().strip()
        if periodo == "ogni giorno":
            data_fine_obj = data_inizio + datetime.timedelta(days=n_volte - 1)
        elif periodo == "ogni mese":
            total_months = data_inizio.month + n_volte - 1
            anno_fine = data_inizio.year + (total_months - 1) // 12
            mese_fine = (total_months - 1) % 12 + 1
            giorno_inizio = data_inizio.day
            try:
                data_fine_obj = datetime.date(anno_fine, mese_fine, giorno_inizio)
            except ValueError:
                if mese_fine == 12:
                    primo_giorno_mese_successivo = datetime.date(anno_fine + 1, 1, 1)
                else:
                    primo_giorno_mese_successivo = datetime.date(anno_fine, mese_fine + 1, 1)
                ultimo_giorno_mese_fine = (primo_giorno_mese_successivo - datetime.timedelta(days=1)).day
                data_fine_obj = datetime.date(anno_fine, mese_fine, ultimo_giorno_mese_fine)
        elif periodo == "ogni anno":
            anno_fine = data_inizio.year + n_volte - 1
            try:
                data_fine_obj = data_inizio.replace(year=anno_fine)
            except ValueError:
                data_fine_obj = data_inizio.replace(year=anno_fine, day=28)
        else:
            return "N/D"
        return data_fine_obj.strftime("%d-%m-%Y")
    oggi = datetime.date.today()
    mese_corrente = oggi.month
    anno_corrente = oggi.year
    mesi_italiani = [
        "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
    ]
    mese_nome = mesi_italiani[mese_corrente - 1]
    popup_mensile = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    popup_mensile.withdraw()
    self._scadenze_popup = popup_mensile
    def on_scadenze_close():
        try:
            popup_mensile.grab_release() 
        except:
            pass
        popup_mensile.destroy()
        self._scadenze_popup = None
    popup_mensile.title(f"Scadenze di {mese_nome} {anno_corrente}")
    larghezza_finestra = 1350
    altezza_finestra = 600
    larghezza_schermo = self.winfo_screenwidth()
    altezza_schermo = self.winfo_screenheight()
    x = (larghezza_schermo // 2) - (larghezza_finestra // 2)
    y = (altezza_schermo // 2) - (altezza_finestra // 2)
    popup_mensile.geometry(f"{larghezza_finestra}x{altezza_finestra}+{x}+{y}")
    popup_mensile.minsize(larghezza_finestra, altezza_finestra)
    popup_mensile.transient(self)
    popup_mensile.resizable(True, True)
    popup_mensile.protocol("WM_DELETE_WINDOW", on_scadenze_close)
    popup_mensile.bind("<Escape>", lambda e: on_scadenze_close())
    colonne = ("data", "categoria", "descrizione", "importo", "tipo_voce", "scadenza", "pagato", "progressione", "conto", "metodo", "tag")
    tree_mensile = ttk.Treeview(popup_mensile, columns=colonne, show="headings")
    tree_mensile.pack(fill="both", expand=True, padx=10, pady=(10, 0))
    tree_mensile.bind("<Double-1>", self.on_scadenza_doppio_click)
    for col in colonne:
        tree_mensile.heading(col, text=col.replace("_", " ").capitalize(), command=(lambda c=col: lambda: ordina_colonna(tree_mensile, c, False))())
    tree_mensile.column("data", width=80, anchor="center", stretch=False)
    tree_mensile.column("categoria", width=180, anchor="center", stretch=False)
    tree_mensile.column("descrizione", width=307, anchor="w", stretch=False)
    tree_mensile.column("importo", width=100, anchor="e", stretch=False)
    tree_mensile.column("tipo_voce", width=80, anchor="center", stretch=False)
    tree_mensile.column("scadenza", width=80, anchor="center", stretch=False)
    tree_mensile.column("pagato", width=60, anchor="center", stretch=False)
    tree_mensile.column("progressione", width=100, anchor="center", stretch=False)
    tree_mensile.column("conto", width=110, anchor="center", stretch=False)
    tree_mensile.column("metodo", width=110, anchor="center", stretch=False)
    tree_mensile.column("tag", width=100, anchor="center", stretch=False)
    tree_mensile.tag_configure("verde", foreground="green")
    tree_mensile.tag_configure("rosso", foreground="red")
    tree_mensile.tag_configure("grigio", foreground="gray")
    for item_id, dati in self.ricorrenze.items():
        try:
            ric_type = dati.get("tipo", "").lower()
            n = dati.get("n", 0)
            data_inizio = datetime.datetime.strptime(dati.get("data_inizio", ""), "%d-%m-%Y").date()
            categoria = dati.get("cat", "N/D")
            descrizione_base = dati.get("desc", "—")
            tipo_voce = dati.get("tipo_voce", "N/D")
            importo_base = float(str(dati.get("imp", "0")).replace(",", "."))
            date_nel_mese = []
            for i in range(n):
                if ric_type == "ogni mese":
                    mese = (data_inizio.month - 1 + i) % 12 + 1
                    anno = data_inizio.year + (data_inizio.month - 1 + i) // 12
                    giorno = min(
                        data_inizio.day,
                        [31, 29 if anno % 4 == 0 and (anno % 100 != 0 or anno % 400 == 0) else 28,
                         31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mese - 1]
                    )
                    data_movimento = datetime.date(anno, mese, giorno)
                elif ric_type == "ogni anno":
                    try:
                        data_movimento = data_inizio.replace(year=data_inizio.year + i)
                    except ValueError:
                        data_movimento = data_inizio.replace(year=data_inizio.year + i, day=28)
                else:
                    data_movimento = data_inizio + datetime.timedelta(days=i)
                if data_movimento.month == mese_corrente and data_movimento.year == anno_corrente:
                    date_nel_mese.append((i + 1, data_movimento))
            data_fine_serie = calcola_data_fine(data_inizio, n, ric_type)
            for indice, data_movimento in date_nel_mese:
                voce_trovata = False
                importo_effettivo = importo_base
                entry_trovata = None
                if data_movimento in self.spese:
                    for voce in self.spese[data_movimento]:
                        if len(voce) >= 5 and voce[4] == item_id:
                            importo_effettivo = voce[2]
                            voce_trovata = True
                            entry_trovata = voce
                            break
                valore_importo = f"{importo_effettivo:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".") if voce_trovata else "—"
                pagato = "✔️" if data_movimento <= oggi and voce_trovata else "❌"
                progressione = f"{indice}/{n}"
                descrizione = descrizione_base
                conto_val = campo(entry_trovata, "conto", "") if entry_trovata else ""
                metodo_val = campo(entry_trovata, "metodo_pagamento", "") if entry_trovata else ""
                tag_val = " ".join(campo(entry_trovata, "hashtag", [])) if entry_trovata else ""
                tag = "rosso" if tipo_voce == "Uscita" else "verde" if voce_trovata else "grigio"
                data_scadenza = data_fine_serie
                tree_mensile.insert(
                    "",
                    "end",
                    values=(
                        data_movimento.strftime("%d-%m-%Y"),
                        categoria,
                        descrizione,
                        valore_importo,
                        tipo_voce,
                        data_scadenza,
                        pagato,
                        progressione,
                        conto_val,
                        metodo_val,
                        tag_val
                    ),
                    tags=(tag,)
                )
        except Exception as e:
            print(f"Errore nella ricorrenza con ID {item_id}: {e}")
            continue
    fine_mese = datetime.date(anno_corrente, mese_corrente, 28)
    while True:
        try:
            fine_mese = fine_mese.replace(day=fine_mese.day + 1)
        except ValueError:
            break
    for data_voce in sorted(self.spese.keys()):
        if oggi <= data_voce <= fine_mese:
            for voce in self.spese[data_voce]:
                if len(voce) < 5 or voce[4] not in self.ricorrenze:
                    try:
                        categoria, descrizione, importo, tipo_voce = voce[:4]
                        valore_importo = f"{importo:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")
                        pagato = "✔️" if data_voce <= oggi else "❌"
                        progressione = "—"
                        data_scadenza = data_voce.strftime("%d-%m-%Y")
                        conto_val = campo(voce, "conto", "")
                        metodo_val = campo(voce, "metodo_pagamento", "")
                        tag_val = " ".join(campo(voce, "hashtag", []))
                        tag = "rosso" if tipo_voce == "Uscita" else "verde"
                        tree_mensile.insert(
                            "",
                            "end",
                            values=(
                                data_voce.strftime("%d-%m-%Y"),
                                categoria,
                                descrizione,
                                valore_importo,
                                tipo_voce,
                                data_scadenza,
                                pagato,
                                progressione,
                                conto_val,
                                metodo_val,
                                tag_val
                            ),
                            tags=(tag,)
                        )
                    except Exception as e:
                        print(f"Errore nella voce normale del {data_voce}: {e}")
                        continue
    ordina_colonna(tree_mensile, "data", False)
    button_frame = tk.Frame(popup_mensile, bg=self.COLOR_TOPLEVEL)
    button_frame.pack(fill="x", pady=10)
    self.btn_calcola_mancanti = ttk.Label(
        button_frame, 
        image=self.icone_gui.get("reset"),
        text=" Calcola Mancanti", 
        compound="left",
        cursor="hand2", 
        background=self.COLOR_WIDGET_BG,
        font=("Arial", 9, "bold")
    )
    self.btn_calcola_mancanti.image = self.icone_gui.get("reset")
    self.btn_calcola_mancanti.pack(side="left", padx=20, pady=5)
    self.btn_calcola_mancanti.bind("<Button-1>", lambda e: self.calcola_mancanti())
    self.btn_chiudi_scadenze = ttk.Label(
        button_frame, 
        image=self.icone_gui.get("chiudi"), 
        text=" Chiudi", 
        compound="left",
        cursor="hand2", 
        background=self.COLOR_WIDGET_BG,
        font=("Arial", 9, "bold")
    )
    self.btn_chiudi_scadenze.image = self.icone_gui.get("chiudi")
    self.btn_chiudi_scadenze.pack(side="right", padx=20, pady=5)
    self.btn_chiudi_scadenze.bind("<Button-1>", lambda e: on_scadenze_close())
    popup_mensile.deiconify()
    popup_mensile.focus_force()

def on_scadenza_doppio_click(self, event):
    tree = event.widget
    item_id = tree.focus()
    if not item_id:
        return
    valori = tree.item(item_id, "values")
    if not valori or len(valori) < 1:
        return
    data_str = valori[0]  
    try:
        giorno = datetime.datetime.strptime(data_str, "%d-%m-%Y").date()
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
    if hasattr(self, "_scadenze_popup") and self._scadenze_popup:
       try:
          self._scadenze_popup.destroy()
          self._scadenze_popup = None
       except:
          pass
