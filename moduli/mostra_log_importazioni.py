#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import tkinter as tk
from tkinter import ttk, filedialog

# Log Importazioni
def mostra_log_importazioni(self):
    import __main__ as _app
    LOG_IMPORTAZIONI = _app.LOG_IMPORTAZIONI
    EXPORT_FILES = _app.EXPORT_FILES
    import pymupdf as fitz
    from datetime import datetime
    if hasattr(self, '_log_importazioni_popup') and self._log_importazioni_popup and self._log_importazioni_popup.winfo_exists():
        self._log_importazioni_popup.lift()
        self._log_importazioni_popup.focus_force()
        return
    popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    self._log_importazioni_popup = popup
    popup.bind("<Destroy>", lambda e: setattr(self, '_log_importazioni_popup', None) if e.widget is popup else None)
    popup.transient(self)
    popup.withdraw()
    popup.title(" Log Importazioni")
    popup.resizable(True, True)
    width, height = 1366, 630
    popup.minsize(width, height)
    popup.columnconfigure(0, weight=1)
    popup.rowconfigure(1, weight=1)
    def centra():
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (width // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (height // 2)
        popup.geometry(f"{width}x{height}+{x}+{y}")
        popup.deiconify()
        popup.lift()
        popup.focus_force()
    popup.after(0, centra)
    popup.bind("<Escape>", lambda e: popup.destroy())
    header_frame = ttk.Frame(popup)
    header_frame.grid(row=0, column=0, pady=(12, 5), padx=(15, 5), sticky="w")
    ttk.Label(
        header_frame,
        text="Log Importazioni",
        font=("Arial", 11, "bold")
    ).pack(side="left")

    var_sel_tutto = tk.BooleanVar()
    def _toggle_sel_tutto():
        if var_sel_tutto.get():
            tree.selection_set(tree.get_children())
        else:
            tree.selection_remove(tree.selection())
    f_toggle = tk.Frame(header_frame, bg=self.COLOR_TOPLEVEL)
    f_toggle.pack(side="left", padx=(15, 0))
    tk.Checkbutton(f_toggle, variable=var_sel_tutto, command=_toggle_sel_tutto,
                   bg=self.COLOR_TOPLEVEL, fg=self.COLOR_BLACK,
                   selectcolor=self.COLOR_WHITE,
                   activebackground=self.COLOR_TOPLEVEL,
                   highlightthickness=0, bd=0).pack(side="left")
    tk.Label(f_toggle, text=" Seleziona Tutto/Nessuno", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 10, "bold italic")).pack(side="left")

    img_mouse = self.icone_gui.get("mouse")
    ttk.Label(
        header_frame,
        text="  Doppio clic → Vai alla spesa sulla Dashboard  |  Clic destro → popola campi inserimento  |  Ctrl/Maiusc+clic → selezione multipla, Canc → elimina selezionate ",
        image=img_mouse,
        compound="right",
        foreground="gray",
        font=("Arial", 8, "italic")
    ).pack(side="left", padx=(10, 0))
    colonne = ["Timestamp", "Tipo", "Data Mov.", "Descrizione", "Importo", "Direzione", "Categoria", "Conto", "ID", "Metodo", "Tag"]
    larghezze = [130, 90, 80, 420, 90, 80, 150, 120, 0, 110, 130]
    frame_tree = ttk.Frame(popup)
    frame_tree.columnconfigure(0, weight=1)
    frame_tree.rowconfigure(1, weight=1)
    frame_tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
    ttk.Separator(frame_tree, orient="horizontal").grid(row=0, column=0, columnspan=2, sticky="ew")
    tree = ttk.Treeview(frame_tree, columns=colonne, show="headings",
                        displaycolumns=[c for c in colonne if c != "ID"], selectmode="extended")
    sb = ttk.Scrollbar(frame_tree, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.grid(row=1, column=0, sticky="nsew")
    sb.grid(row=1, column=1, sticky="ns")
    idx_riga = {}
    def carica_righe():
        idx_riga.clear()
        tree.delete(*tree.get_children())
        if not os.path.exists(LOG_IMPORTAZIONI):
            tree.insert("", "end", values=["Nessun record"] + [""] * (len(colonne) - 1))
            return
        try:
            with open(LOG_IMPORTAZIONI, "r", encoding="utf-8") as f:
                righe = f.readlines()
        except Exception as e:
            tree.insert("", "end", values=[f"Errore lettura log: {e}"] + [""] * (len(colonne) - 1))
            return
        if not righe:
            tree.insert("", "end", values=["Nessun record"] + [""] * (len(colonne) - 1))
            return
        for n_riga, riga in enumerate(righe):
            if not riga.strip():
                continue
            parti = [p.strip() for p in riga.strip().split("|")]
            while len(parti) < len(colonne):
                parti.append("")
            iid = tree.insert("", "end", values=parti[:len(colonne)])
            idx_riga[iid] = n_riga
    carica_righe()
    for i, col in enumerate(colonne):
        tree.heading(col, text=col, anchor="w",
             command=lambda c=col: self.treeview_sort_column(tree, c, False))
        tree.column(col, width=larghezze[i], minwidth=larghezze[i],
            stretch=(col == "Tag"), anchor="w")

    def _parse_data_flessibile(data_str):
        if not data_str:
            return None
        data_str = str(data_str).strip()
        for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(data_str, fmt).date()
            except ValueError:
                pass
        return None

    def vai_a_movimento(event):
        sel = tree.selection()
        if not sel:
            return
        valori = tree.item(sel[0], "values")
        if not valori or len(valori) < 3:
            return
        desc_cerca = valori[3].strip() if len(valori) > 3 else ""
        giorno = None
        scd_match = re.search(r"SCD:\s*(\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2})", desc_cerca, re.IGNORECASE)
        if scd_match:
            giorno = _parse_data_flessibile(scd_match.group(1))
        if not giorno:
            giorno = _parse_data_flessibile(valori[2])
        if not giorno:
            return
        popup.destroy()
        if hasattr(self, "cal"):
            self.cal.selection_set(giorno)
            self.cal._sel_date = giorno
            if hasattr(self, "estratto_year_var"):
                self.estratto_year_var.set(str(giorno.year))
            if hasattr(self, "estratto_month_var") and hasattr(self, "months"):
                self.estratto_month_var.set(self.months[giorno.month - 1])
            if hasattr(self, "on_calendar_change"):
                self.on_calendar_change()
        self.after(400, lambda: _seleziona_in_tree(giorno, desc_cerca))

    def _seleziona_in_tree(giorno, desc_cerca):
        if not hasattr(self, "spese_mese_tree"):
            return
        desc_pulita = desc_cerca.replace("RIC·", "").replace("ALL·", "").strip().lower()
        for iid in self.spese_mese_tree.get_children():
            v = self.spese_mese_tree.item(iid, "values")
            if not v:
                continue
            d = _parse_data_flessibile(v[0])
            if d == giorno:
                v_desc = str(v[2]).strip().lower() if len(v) > 2 else ""
                if not desc_pulita or desc_pulita[:15] in v_desc or v_desc[:15] in desc_pulita:
                    self.spese_mese_tree.selection_set(iid)
                    self.spese_mese_tree.see(iid)
                    break
    def copia_spesa_nel_form(event):
        item = tree.identify_row(event.y)
        if not item:
            return
        valori = tree.item(item, "values")
        conto = str(valori[7]).strip()
        if conto and conto != "—":
            if hasattr(self, "cb_conto_movimento"):
                self.cb_conto_movimento.set(conto)
        categoria   = str(valori[6]).strip()
        descrizione = str(valori[3]).strip()
        importo_str = str(valori[4]).replace("€", "").strip()
        direzione   = str(valori[5]).strip()
        cat_match = next(
            (c for c in self.categorie if c.strip().lower() == categoria.lower()),
            None
        )
        if cat_match:
            self.cat_sel.set(cat_match)
            self.cat_menu.set(cat_match)
            self.on_categoria_changed(manuale=False)
        try:
            self.imp_entry.delete(0, tk.END)
            self.imp_entry.insert(0, f"{_app._parse_it_float(importo_str):.2f}".replace(".", ","))
        except ValueError:
            pass
        desc_pulita = descrizione.replace("RIC·", "").replace("ALL·", "").strip()
        self.desc_entry.delete(0, 'end')
        self.desc_entry.insert(0, desc_pulita[:30])
        if self.tipo_spesa_var.get() != direzione:
                self.toggle_tipo_spesa()
        popup.destroy()

    def _trova_spesa(giorno, desc, imp, direzione, id_spesa=""):
        if id_spesa:
            for g, lista in self.spese.items():
                for i, v in enumerate(lista):
                    if getattr(v, "id_spesa", None) == id_spesa:
                        return g, i
            return None
        if not giorno or imp is None:
            return None
        varianti = {desc, "🤖 " + desc, "ALL· " + desc}
        for i, v in enumerate(self.spese.get(giorno, [])):
            if (str(v[1]).strip() in varianti
                    and abs(float(v[2]) - imp) < 0.01
                    and str(v[3]) == direzione):
                return giorno, i
        return None

    def elimina_selezionate():
        sel = [i for i in tree.selection() if i in idx_riga]
        if not sel:
            self.show_custom_warning("Attenzione", "Seleziona una o più righe (Ctrl+clic, Maiusc+clic, oppure Seleziona Tutto).")
            return
        if not self.show_custom_askyesno(
                "Elimina a blocco",
                f"Eliminare {len(sel)} righe selezionate?\n\nVengono cancellate le spese corrispondenti "
                f"dal database e le righe dal log. Operazione non annullabile."):
            return
        eliminate = mancanti = 0
        for iid in sel:
            v = tree.item(iid, "values")
            if str(v[1]).strip().upper() == "SALTATA":
                continue
            giorno = _parse_data_flessibile(v[2])
            try:
                imp = abs(_app._parse_it_float(str(v[4]).replace("€", "").strip()))
            except Exception:
                imp = None
            trovata = _trova_spesa(giorno, str(v[3]).strip(), imp, str(v[5]).strip(), str(v[8]).strip())
            if trovata is None:
                mancanti += 1
                continue
            giorno, i = trovata
            voce = self.spese[giorno][i]
            if hasattr(self, "elimina_piano_per_spesa"):
                self.elimina_piano_per_spesa(getattr(voce, "id_spesa", None))
            del self.spese[giorno][i]
            if not self.spese[giorno]:
                del self.spese[giorno]
            if hasattr(self, "annulla_azione_gamification"):
                self.annulla_azione_gamification("movimento")
            eliminate += 1
        da_togliere = {idx_riga[i] for i in sel}
        try:
            with open(LOG_IMPORTAZIONI, "r", encoding="utf-8") as f:
                righe = f.readlines()
            with open(LOG_IMPORTAZIONI, "w", encoding="utf-8") as f:
                f.writelines(r for n, r in enumerate(righe) if n not in da_togliere)
        except Exception as e:
            self.show_custom_warning("Errore", f"Log non aggiornato: {e}")
        if hasattr(self, "_cache_tutti_tag"):
            del self._cache_tutti_tag
        self.save_db()
        if hasattr(self, "reset_modifica_form"):
            self.reset_modifica_form()
        self.refresh_gui()
        self.colora_giorni_spese()
        carica_righe()
        var_sel_tutto.set(False)
        msg = f"{eliminate} spese eliminate"
        if mancanti:
            msg += f", {mancanti} non trovate (già modificate o cancellate)"
        self.show_toast(msg, duration=3500)

    def _aggiorna_toggle(event=None):
        tot = len(idx_riga)
        var_sel_tutto.set(tot > 0 and len(tree.selection()) == tot)

    tree.bind("<Double-1>", vai_a_movimento)
    tree.bind("<Button-3>", copia_spesa_nel_form)
    tree.bind("<Delete>", lambda e: elimina_selezionate())
    tree.bind("<<TreeviewSelect>>", _aggiorna_toggle)

    def _righe_allineate():
        if not os.path.exists(LOG_IMPORTAZIONI):
            return []
        with open(LOG_IMPORTAZIONI, "r", encoding="utf-8") as f:
            righe = [r for r in f.read().splitlines() if r.strip()]
        dati = []
        for r in righe:
            p = [x.strip() for x in r.split("|")]
            p += [""] * (len(colonne) - len(p))
            dati.append(p[:len(colonne)])
        if not dati:
            return []
        facoltative = ("Conto", "Metodo", "Tag")
        usa = [i for i, c in enumerate(colonne)
               if c != "ID" and not (c in facoltative and all(d[i] in ("", "—") for d in dati))]
        larg = {i: max(len(colonne[i]), *(len(d[i]) for d in dati)) for i in usa}
        def cella(v, i):
            return v[i].rjust(larg[i]) if colonne[i] == "Importo" else v[i].ljust(larg[i])
        def fmt(v):
            return " | ".join(cella(v, i) for i in usa).rstrip()
        return [fmt(colonne), "-+-".join("-" * larg[i] for i in usa)] + [fmt(d) for d in dati]

    def _crea_pdf(dest, lines):
        doc = fitz.open()
        page_w, page_h, margin = 842, 595, 30
        max_len = max((len(l) for l in lines), default=1)
        font_size = max(4, min(7, (page_w - 2 * margin) / (max_len * 0.6)))
        line_height = font_size + 2
        page = doc.new_page(width=page_w, height=page_h)
        y = margin
        for line in lines:
            if y > (page_h - margin):
                page = doc.new_page(width=page_w, height=page_h)
                y = margin
            page.insert_text((margin, y), line, fontname="cour", fontsize=font_size)
            y += line_height
        doc.save(dest)
        doc.close()

    def anteprima_esporta():
        if hasattr(anteprima_esporta, '_win') and anteprima_esporta._win.winfo_exists():
            anteprima_esporta._win.lift()
            anteprima_esporta._win.focus_force()
            return
        lines = _righe_allineate()
        if not lines:
            self.show_custom_warning("Errore", "Nessun log da esportare.")
            return
        now = datetime.now()
        testo = f"LOG IMPORTAZIONI - {now.strftime('%d/%m/%Y %H:%M')}\n\n" + "\n".join(lines) + "\n"
        nome_base = f"Log_Importazioni_{now.day:02d}-{now.month:02d}-{now.year}"
        prev_win = tk.Toplevel(popup, bg=self.COLOR_TOPLEVEL)
        anteprima_esporta._win = prev_win
        prev_win.withdraw()
        prev_win.title("Esportazione Log Importazioni")
        prev_win.bind("<Escape>", lambda e: prev_win.destroy())
        prev_win.transient(popup)
        def centra_prev():
            if not prev_win.winfo_exists():
                return
            w_a, h_a = 1100, 600
            x = popup.winfo_rootx() + (popup.winfo_width() // 2) - (w_a // 2)
            y = popup.winfo_rooty() + (popup.winfo_height() // 2) - (h_a // 2)
            prev_win.geometry(f"{w_a}x{h_a}+{x}+{y}")
            prev_win.minsize(w_a, h_a)
            prev_win.deiconify()
        prev_win.after(0, centra_prev)
        def do_pdf():
            f_path = filedialog.asksaveasfilename(
                defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
                initialdir=EXPORT_FILES, initialfile=nome_base + ".pdf",
                confirmoverwrite=False, parent=prev_win)
            if f_path:
                try:
                    _crea_pdf(f_path, testo.split("\n"))
                    self.show_toast("PDF salvato.")
                except Exception as ex:
                    self.show_custom_warning("Errore PDF", str(ex))
        def do_txt():
            f_path = filedialog.asksaveasfilename(
                defaultextension=".txt", filetypes=[("TXT", "*.txt")],
                initialdir=EXPORT_FILES, initialfile=nome_base + ".txt",
                confirmoverwrite=False, parent=prev_win)
            if f_path:
                try:
                    with open(f_path, "w", encoding="utf-8") as fh:
                        fh.write(testo)
                    self.show_toast("File TXT salvato.")
                except Exception as ex:
                    self.show_custom_warning("Errore", f"Impossibile salvare il TXT: {ex}")
        txt_area_frame = tk.Frame(prev_win, bg=self.COLOR_TOPLEVEL)
        txt_area_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        v_scroll = ttk.Scrollbar(txt_area_frame, orient="vertical")
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll = ttk.Scrollbar(prev_win, orient="horizontal")
        txt_area = tk.Text(txt_area_frame, font=("Courier New", 9),
                           bg=self.COLOR_WHITE, fg=self.COLOR_BLACK,
                           wrap="none",
                           yscrollcommand=v_scroll.set,
                           xscrollcommand=h_scroll.set)
        txt_area.pack(fill=tk.BOTH, expand=True)
        v_scroll.config(command=txt_area.yview)
        h_scroll.config(command=txt_area.xview)
        h_scroll.pack(fill=tk.X, padx=10)
        txt_area.insert("1.0", testo)
        txt_area.config(state="disabled")
        bf = tk.Frame(prev_win, bg=self.COLOR_TOPLEVEL)
        bf.pack(fill=tk.X, pady=8)
        for lbl_txt, ico, cmd in [(" PDF", "salva", do_pdf), (" TXT", "salva", do_txt),
                                  (" Stampa", "stampa", lambda: self._stampa_lista_diretta(
                                      testo, self.show_custom_warning))]:
            img = self.icone_gui.get(ico)
            b = ttk.Label(bf, compound="left", image=img, text=lbl_txt,
                          background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                          cursor="hand2", padding=(10, 5))
            b.pack(side=tk.LEFT, padx=5)
            b.bind("<Button-1>", lambda e, c=cmd: c())
        img_c = self.icone_gui.get("chiudi")
        bc = ttk.Label(bf, compound="left", image=img_c, text=" Chiudi",
                       background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                       cursor="hand2", padding=(10, 5))
        bc.pack(side=tk.RIGHT, padx=10)
        bc.bind("<Button-1>", lambda e: prev_win.destroy())

    def azzera():
        if not self.show_custom_askyesno("Conferma", "Azzerare il log importazioni?"):
            return
        with open(LOG_IMPORTAZIONI, "w", encoding="utf-8") as f:
            f.write("")
        carica_righe()
        var_sel_tutto.set(False)
        self.show_toast("Log azzerato.", duration=2000)

    btns = tk.Frame(popup, bg=self.COLOR_BACKGROUND)
    btns.grid(row=2, column=0, pady=10, padx=15, sticky="ew")
    for i in range(4):
        btns.columnconfigure(i, weight=1)
    lbl_esporta = ttk.Label(btns, image=self.icone_gui.get("salva"),
            text=" Esporta", compound="left", cursor="hand2",
            background=self.COLOR_BACKGROUND, foreground=self.COLOR_HEADER,
            font=("Arial", 9, "bold"))
    lbl_esporta.grid(row=0, column=0, padx=5, sticky="ew")
    lbl_esporta.bind("<Button-1>", lambda e: anteprima_esporta())
    lbl_elimina = ttk.Label(btns, image=self.icone_gui.get("delete"),
            text=" Elimina selezionate", compound="left", cursor="hand2",
            background=self.COLOR_BACKGROUND, foreground=self.COLOR_RED_SMOOTH,
            font=("Arial", 9, "bold"))
    lbl_elimina.grid(row=0, column=1, padx=5, sticky="ew")
    lbl_elimina.bind("<Button-1>", lambda e: elimina_selezionate())
    lbl_azzera = ttk.Label(btns, image=self.icone_gui.get("delete"),
            text=" Azzera Log", compound="left", cursor="hand2",
            background=self.COLOR_BACKGROUND, foreground=self.COLOR_RED_SMOOTH,
            font=("Arial", 9, "bold"))
    lbl_azzera.grid(row=0, column=2, padx=5, sticky="ew")
    lbl_azzera.bind("<Button-1>", lambda e: azzera())
    lbl_chiudi = ttk.Label(btns, image=self.icone_gui.get("chiudi"),
            text=" Chiudi", compound="left", cursor="hand2",
            background=self.COLOR_BACKGROUND, foreground=self.COLOR_HEADER,
            font=("Arial", 9, "bold"))
    lbl_chiudi.grid(row=0, column=3, padx=5, sticky="ew")
    lbl_chiudi.bind("<Button-1>", lambda e: popup.destroy())
