#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tkinter as tk
from tkinter import ttk, filedialog

# Log Importazioni
def mostra_log_importazioni(self):
    import __main__ as _app
    LOG_IMPORTAZIONI = _app.LOG_IMPORTAZIONI
    EXPORT_FILES = _app.EXPORT_FILES
    import fitz
    from datetime import datetime
    popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    popup.transient(self)
    popup.withdraw()
    popup.title(" Log Importazioni")
    popup.resizable(True, True)
    width, height = 1300, 550
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

    img_mouse = self.icone_gui.get("mouse")
    ttk.Label(
        header_frame,
        text="  Doppio clic → Vai alla spesa sulla Dashboard  |  Clic destro → popola campi inserimento ",
        image=img_mouse,
        compound="right",
        foreground="gray",
        font=("Arial", 8, "italic")
    ).pack(side="left", padx=(10, 0))
    colonne = ["Timestamp", "Tipo", "Data Mov.", "Descrizione", "Importo", "Direzione", "Categoria", "Conto"]
    larghezze = [130, 90, 80, 500, 90, 80, 180, 130]
    frame_tree = ttk.Frame(popup)
    frame_tree.columnconfigure(0, weight=1)
    frame_tree.rowconfigure(1, weight=1)
    frame_tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
    ttk.Separator(frame_tree, orient="horizontal").grid(row=0, column=0, columnspan=2, sticky="ew")
    tree = ttk.Treeview(frame_tree, columns=colonne, show="headings")
    sb = ttk.Scrollbar(frame_tree, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    tree.grid(row=1, column=0, sticky="nsew")
    sb.grid(row=1, column=1, sticky="ns")
    def carica_righe():
        tree.delete(*tree.get_children())
        if not os.path.exists(LOG_IMPORTAZIONI):
            tree.insert("", "end", values=["Nessun record"] + [""] * (len(colonne) - 1))
            return
        with open(LOG_IMPORTAZIONI, "r", encoding="utf-8") as f:
            righe = f.readlines()
        if not righe:
            tree.insert("", "end", values=["Nessun record"] + [""] * (len(colonne) - 1))
            return
        for riga in righe:
            parti = [p.strip() for p in riga.strip().split("|")]
            while len(parti) < len(colonne):
                parti.append("")
            tree.insert("", "end", values=parti[:len(colonne)])
    carica_righe()
    for i, col in enumerate(colonne):
        tree.heading(col, text=col, anchor="w",
             command=lambda c=col: self.treeview_sort_column(tree, c, False))
        tree.column(col, width=larghezze[i], minwidth=larghezze[i],
            stretch=(i == len(colonne) - 1), anchor="w")
    def vai_a_movimento(event):
        sel = tree.selection()
        if not sel: return
        valori = tree.item(sel[0], "values")
        try:
            data_str = valori[2].strip()
            giorno = datetime.strptime(data_str, "%d/%m/%Y").date()
        except Exception:
            return
        popup.destroy()
        if hasattr(self, "cal"):
            self.cal.selection_set(giorno)
            self.cal._sel_date = giorno
            self.estratto_month_var.set(f"{giorno.month:02d}")
            self.estratto_year_var.set(str(giorno.year))
            self.estratto_month_var.set(self.months[giorno.month - 1])
            self.on_calendar_change()
        desc_cerca = valori[3].strip() if len(valori) > 3 else ""
        self.after(400, lambda: _seleziona_in_tree(giorno, desc_cerca))
    def _seleziona_in_tree(giorno, desc_cerca):
        for iid in self.spese_mese_tree.get_children():
            v = self.spese_mese_tree.item(iid, "values")
            try:
                d = datetime.strptime(v[0].strip(), "%d/%m/%Y").date()
            except Exception:
                continue
            if d == giorno and desc_cerca and desc_cerca[:20] in str(v[2]):
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
            self.imp_entry.insert(0, f"{float(importo_str):.2f}")
        except ValueError:
            pass
        desc_pulita = descrizione.replace("♻️", "").replace("⚡", "").strip()
        self.desc_entry.delete(0, 'end')
        self.desc_entry.insert(0, desc_pulita[:30])
        if self.tipo_spesa_var.get() != direzione:
                self.toggle_tipo_spesa()
        popup.destroy()
    tree.bind("<Double-1>", vai_a_movimento)
    tree.bind("<Button-3>", copia_spesa_nel_form)
    btns = tk.Frame(popup, bg=self.COLOR_BACKGROUND)
    btns.grid(row=2, column=0, pady=10, padx=15, sticky="ew")
    for i in range(5):
        btns.columnconfigure(i, weight=1)
    def salva_txt():
        now = datetime.now()
        filename = f"Log_Importazioni_{now.day:02d}-{now.month:02d}-{now.year}.txt"
        if not os.path.exists(LOG_IMPORTAZIONI):
            self.show_custom_warning("Errore", "Nessun log da salvare.")
            return
        dest = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("File TXT", "*.txt")],
            initialdir=EXPORT_FILES,
            confirmoverwrite=False,
            initialfile=filename,
            parent=popup)
        if not dest: return
        import shutil
        shutil.copy2(LOG_IMPORTAZIONI, dest)
        self.show_toast("TXT salvato.", duration=2000)
    def salva_pdf():
        now = datetime.now()
        filename = f"Log_Importazioni_{now.day:02d}-{now.month:02d}-{now.year}.pdf"
        if not os.path.exists(LOG_IMPORTAZIONI):
            self.show_custom_warning("Errore", "Nessun log da salvare.")
            return
        dest = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("Documento PDF", "*.pdf")],
            initialfile=filename,
            initialdir=EXPORT_FILES,
            confirmoverwrite=False,
            parent=popup)
        if not dest: return
        try:
            with open(LOG_IMPORTAZIONI, "r", encoding="utf-8") as f:
                content = f.read()
            doc = fitz.open()
            lines = content.split("\n")
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
                page.insert_text((margin, y), line, fontname="cour", fontsize=font_size)
                y += line_height
            doc.save(dest)
            doc.close()
            self.show_custom_info("Successo", f"PDF creato:\n{os.path.basename(dest)}")
        except Exception as e:
            self.show_custom_warning("Errore", f"Impossibile creare il PDF: {e}")
    def stampa():
        if not os.path.exists(LOG_IMPORTAZIONI):
            self.show_custom_warning("Errore", "Nessun log da stampare.")
            return
        self.stampa_pdf(LOG_IMPORTAZIONI, self.show_custom_warning)
    def azzera():
        if not self.show_custom_askyesno("Conferma", "Azzerare il log importazioni?"):
            return
        with open(LOG_IMPORTAZIONI, "w", encoding="utf-8") as f:
            f.write("")
        carica_righe()
        self.show_toast("Log azzerato.", duration=2000)
    lbl_txt = ttk.Label(btns, image=self.icone_gui.get("salva"),
            text=" Salva TXT", compound="left", cursor="hand2",
            background=self.COLOR_BACKGROUND, foreground=self.COLOR_HEADER,
            font=("Arial", 9, "bold"))
    lbl_txt.grid(row=0, column=0, padx=5, sticky="ew")
    lbl_txt.bind("<Button-1>", lambda e: salva_txt())
    lbl_pdf = ttk.Label(btns, image=self.icone_gui.get("archivia"),
            text=" Salva PDF", compound="left", cursor="hand2",
            background=self.COLOR_BACKGROUND, foreground=self.COLOR_HEADER,
            font=("Arial", 9, "bold"))
    lbl_pdf.grid(row=0, column=1, padx=5, sticky="ew")
    lbl_pdf.bind("<Button-1>", lambda e: salva_pdf())
    lbl_stampa = ttk.Label(btns, image=self.icone_gui.get("stampa"),
            text=" Stampa", compound="left", cursor="hand2",
            background=self.COLOR_BACKGROUND, foreground=self.COLOR_HEADER,
            font=("Arial", 9, "bold"))
    lbl_stampa.grid(row=0, column=2, padx=5, sticky="ew")
    lbl_stampa.bind("<Button-1>", lambda e: stampa())
    lbl_azzera = ttk.Label(btns, image=self.icone_gui.get("delete"),
            text=" Azzera Log", compound="left", cursor="hand2",
            background=self.COLOR_BACKGROUND, foreground=self.COLOR_RED_SMOOTH,
            font=("Arial", 9, "bold"))
    lbl_azzera.grid(row=0, column=3, padx=5, sticky="ew")
    lbl_azzera.bind("<Button-1>", lambda e: azzera())
    lbl_chiudi = ttk.Label(btns, image=self.icone_gui.get("chiudi"),
            text=" Chiudi", compound="left", cursor="hand2",
            background=self.COLOR_BACKGROUND, foreground=self.COLOR_HEADER,
            font=("Arial", 9, "bold"))
    lbl_chiudi.grid(row=0, column=4, padx=5, sticky="ew")
    lbl_chiudi.bind("<Button-1>", lambda e: popup.destroy())
    
