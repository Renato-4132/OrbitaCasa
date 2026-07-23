#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import os
import tkinter as tk
from tkinter import ttk, filedialog
from moduli.modello_spesa import campo

# Time Machine: Simulazione di Risparmio per Categoria
def time_machine(self):
    import __main__ as _app
    EXPORT_FILES = _app.EXPORT_FILES
    popup = tk.Toplevel()
    popup.title("Time Machine – Simulazione per categoria")
    popup.geometry("1200x650")
    popup.withdraw()
    self.update_idletasks()
    main_x = self.winfo_x()
    main_y = self.winfo_y()
    main_width = self.winfo_width()
    main_height = self.winfo_height()
    popup_width = 1200
    popup_height = 650
    center_x = main_x + (main_width // 2) - (popup_width // 2)
    center_y = main_y + (main_height // 2) - (popup_height // 2)
    popup.geometry(f"{popup_width}x{popup_height}+{center_x}+{center_y}")
    popup.minsize(popup_width, popup_height)
    popup.transient(self)
    popup.update_idletasks()
    popup.deiconify()
    popup.update()
    main = ttk.Frame(popup, padding=10)
    main.pack(fill="both", expand=True)
    anni_disponibili = sorted({datetime.datetime.strptime(str(d), "%d-%m-%Y").year
                               if isinstance(d, str) else d.year for d in self.spese}, reverse=True)
    anno_var = tk.IntVar(value=datetime.date.today().year)
    mostra_future_var = tk.BooleanVar(value=True)
    top_bar = ttk.Frame(main)
    top_bar.pack(fill="x", pady=(0, 10))
    ttk.Label(top_bar, text="Anno:", font=("Arial", 10)).pack(side="left", padx=(0, 5))
    anno_combo = ttk.Combobox(top_bar, textvariable=anno_var, values=anni_disponibili, style="Border.TCombobox", state="readonly", width=8)
    anno_combo.pack(side="left")
    img_indietro_anno = self.icone_gui.get("reset")
    btn_reset_anno = tk.Label(top_bar, compound="left", image=img_indietro_anno, text=" 🔙" if not img_indietro_anno else "", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padx=10, pady=5, font=("Arial", 9, "bold"))
    btn_reset_anno.pack(side="left", padx=(5, 0))
    btn_reset_anno.bind("<Button-1>", lambda e: [anno_var.set(datetime.date.today().year), aggiorna_interfaccia()])
    ttk.Checkbutton(
        top_bar,
        text="Includi movimenti futuri nei totali",
        variable=mostra_future_var
    ).pack(side="left", padx=(30, 0))
    colonne = ttk.Frame(main)
    colonne.pack(fill="x", padx=5)
    sinistra = ttk.Frame(colonne)
    destra = tk.Frame(colonne, bg=self.COLOR_TOPLEVEL)
    sinistra.pack(side="left", fill="both", expand=True, padx=(0, 40))
    destra.pack(side="right", fill="both", expand=True)
    ttk.Label(sinistra, text="Selezione manuale", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 6))
    destra_label = tk.Label(destra, bg=self.COLOR_TOPLEVEL ,fg=self.TEXT_COLOR, text="Top 10 categorie per risparmio", font=("Arial", 10, "bold"))
    destra_label.pack(anchor="w", pady=(0, 6))
    combo_vars = []
    combo_widgets = []
    for _ in range(10):
        var = tk.StringVar()
        cbx = ttk.Combobox(sinistra, textvariable=var, style="Border.TCombobox", state="readonly", width=30)
        cbx.set("— Nessuna —")
        cbx.pack(pady=2, anchor="w")
        combo_vars.append(var)
        combo_widgets.append(cbx)
    selezioni = {}
    ttk.Separator(main, orient="horizontal").pack(fill="x", pady=14)
    ttk.Label(main, text="Risultato della simulazione:", font=("Arial", 10, "bold")).pack(anchor="w", padx=5)
    text_frame = ttk.Frame(main)
    text_frame.pack(fill="both", expand=True, padx=5, pady=(0, 10))
    text_frame.columnconfigure(0, weight=1)
    text_frame.rowconfigure(0, weight=1)
    scroll_y = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, style="Vertical.TScrollbar")
    scroll_y.grid(row=0, column=1, sticky="ns")
    text_output = tk.Text(
        text_frame, 
        height=10, 
        wrap="word",
        yscrollcommand=scroll_y.set
    )
    text_output.configure(font=("Courier New", 10), bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR)
    text_output.grid(row=0, column=0, sticky="nsew")
    scroll_y.config(command=text_output.yview) 
    text_output.config(state="disabled")
    def aggiorna_categorie():
        anno = anno_var.get()
        contatori = {}
        oggi = datetime.date.today()
        for d, sp in self.spese.items():
            try:
                if isinstance(d, str):
                    d_conv = datetime.datetime.strptime(d, "%d-%m-%Y").date()
                else:
                    d_conv = d
            except:
                continue
            if not mostra_future_var.get() and d_conv > oggi:
                continue
            if d_conv.year != anno:
                continue
            for voce in sp:
                cat = campo(voce, "categoria", "").strip().lower()
                if not cat:
                    continue
                imp = campo(voce, "importo", 0.0)
                tipo = campo(voce, "tipo", "")
                key = cat
                if key not in contatori:
                    contatori[key] = {"count": 0, "uscite": 0.0, "entrate": 0.0}
                contatori[key]["count"] += 1
                if tipo == "Uscita":
                    contatori[key]["uscite"] += imp
                elif tipo == "Entrata":
                    contatori[key]["entrate"] += imp
        for key in contatori:
            contatori[key]["risparmio"] = contatori[key]["uscite"] - contatori[key]["entrate"]
        return contatori
    def aggiorna_interfaccia(*_):
        contatori = aggiorna_categorie()
        tutte_categorie_da_spese = [k.lower() for k in contatori.keys()]
        tutte_categorie_principali = [k.lower() for k in self.categorie_tipi.keys()]
        tutte_categorie = sorted(list(set(tutte_categorie_da_spese) | set(tutte_categorie_principali)))
        valori_combo = ["— Nessuna —"] + tutte_categorie
        for var, cb in zip(combo_vars, combo_widgets):
            cb["values"] = valori_combo
            if var.get().strip().lower() not in tutte_categorie:
                var.set("— Nessuna —")
        for w in destra.winfo_children():
            if w != destra_label:
                w.destroy()
        top_cat = sorted(contatori.items(), key=lambda x: -x[1]["risparmio"])[:10]
        spuntate_precedenti = {cat for cat, (var, _) in selezioni.items() if var.get()}
        selezioni.clear()
        for cat, dati in top_cat:
            var = tk.BooleanVar(value=(cat in spuntate_precedenti))
            selezioni[cat] = (var, dati)
            txt = f"{cat.title()} – {dati['count']}×, Risparmio: {dati['risparmio']:.2f} € (Uscite: {dati['uscite']:.2f} - Entrate: {dati['entrate']:.2f})"
            chk = tk.Checkbutton(
                    destra, 
                    text=txt, 
                    variable=var,
                    bg=self.COLOR_TOPLEVEL, 
                    fg=self.TEXT_COLOR,     
                    selectcolor=self.COLOR_TOPLEVEL,
                    activebackground=self.COLOR_TOPLEVEL,
                    activeforeground=self.TEXT_COLOR,
                    highlightthickness=0,
                    bd=0
            )
            chk.pack(anchor="w", pady=2)
    def esegui_simulazione():
        contatori = aggiorna_categorie()
        text_output.config(state="normal")
        text_output.delete("1.0", tk.END)
        lines = [f"Time Machine – Anno {anno_var.get()}\n"]
        totale = 0.0
        scelte = set()
        for cat, (var, _) in selezioni.items():
            if var.get():
                scelte.add(cat)
        for var in combo_vars:
            val = var.get().strip().lower()
            if val and val != "— nessuna —" and val in contatori:
                scelte.add(val)
        risultati = []
        for cat in scelte:
            dati = contatori.get(cat)
            if dati:
                risultati.append((cat, dati["count"], dati["uscite"], dati["entrate"], dati["risparmio"]))
        risultati.sort(key=lambda x: -x[4])
        lines.append(f"Proiezione del risparmio ottenibile nel {anno_var.get()}, escludendo le categorie selezionate: ➤\n")
        lines.append(f"{'Categoria':<25} {'Num':>4}   {'Uscite (€)':>12}   {'Entrate (€)':>12}   {'Risparmio (€)':>14}")
        lines.append("─" * 77)
        for cat, n, usc, ent, risp in risultati:
            lines.append(f"{cat.title():<25} {n:>4}   {usc:>12.2f}   {ent:>12.2f}   {risp:>14.2f}")
            totale += risp
        lines.append("─" * 77)
        lines.append(f"\nRisparmio totale teorico: {totale:.2f} € (Uscite - Entrate delle categorie selezionate)")
        text_output.insert("1.0", "\n".join(lines))
        text_output.config(state="disabled")
    def reset_tutto():
        anno_var.set(datetime.date.today().year)
        mostra_future_var.set(True)
        for var in combo_vars:
            var.set("— Nessuna —")
        for var, _ in selezioni.values():
            var.set(False)
        text_output.config(state="normal")
        text_output.delete("1.0", tk.END)
        text_output.config(state="disabled")
        aggiorna_interfaccia()
    def esporta_simulazione():
        text_output.config(state="normal")
        content = text_output.get("1.0", "end").strip()
        text_output.config(state="disabled")
        if not content:
            self.show_toast("Non c'è nessuna simulazione da esportare.")
            return
        preview = tk.Toplevel(popup, bg=self.COLOR_TOPLEVEL)
        preview.title("Preview esportazione")
        preview.withdraw()
        larghezza_finestra = 1200
        altezza_finestra = 620
        x = popup.winfo_rootx() + (popup.winfo_width() // 2) - (larghezza_finestra // 2)
        y = popup.winfo_rooty() + (popup.winfo_height() // 2) - (altezza_finestra // 2)
        preview.geometry(f"{larghezza_finestra}x{altezza_finestra}+{x}+{y}")
        preview.minsize(larghezza_finestra, altezza_finestra)
        preview.transient(popup)
        preview.resizable(True, True)
        preview.update_idletasks()
        preview.deiconify()
        preview.focus_set()
        preview.grab_set()
        preview.bind('<Escape>', lambda e: preview.destroy())
        tx = tk.Text(preview, font=("Courier new", 10), wrap="none")
        tx.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        contenuto_preview = "\n".join(" " + l for l in content.splitlines())
        tx.insert(tk.END, contenuto_preview)
        tx.config(state="disabled")
        frm = tk.Frame(preview, bg=self.COLOR_TOPLEVEL)
        frm.pack(fill=tk.X, padx=10, pady=8)
        def do_save():
            now = datetime.date.today()
            default_filename = f"Time_Machine_{now.day:02d}_{now.month:02d}_{now.year}.txt"
            file = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("File txt", "*.txt")],
                initialdir=EXPORT_FILES,
                title="Esporta risultato simulazione",
                initialfile=default_filename,
                confirmoverwrite=False,
                parent=preview)
            if file:
                if os.path.exists(file):
                    conferma = self.show_custom_askyesno(
                        "Sovrascrivere file?",
                        f"Il file '{os.path.basename(file)}' \nesiste già. Vuoi sovrascriverlo?"
                    )
                    if not conferma:
                        return
                try:
                    with open(file, "w", encoding="utf-8") as f:
                        f.write(contenuto_preview)
                    self.show_custom_warning("Esportazione completata", f"✓ Simulazione esportata in:\n{file}")
                    preview.destroy()
                except Exception as e:
                    self.show_custom_warning("Errore", f"❌ Salvataggio fallito:\n{e}")
        def do_save_pdf():
            import fitz
            now = datetime.date.today()
            default_filename = f"Time_Machine_{now.day:02d}_{now.month:02d}_{now.year}.pdf"
            file = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("Documento PDF", "*.pdf")],
                initialdir=EXPORT_FILES,
                title="Esporta risultato simulazione come PDF",
                initialfile=default_filename,
                confirmoverwrite=False,
                parent=preview
            )
            if file:
                if os.path.exists(file):
                    conferma = self.show_custom_askyesno(
                        "Sovrascrivere file?",
                        f"Il file '{os.path.basename(file)}' \nesiste già. Vuoi sovrascriverlo?"
                    )
                    if not conferma:
                        return
                try:
                    doc = fitz.open()
                    lines = contenuto_preview.split('\n')
                    page_w, page_h = 842, 595
                    margin = 40
                    font_size = 8
                    line_height = font_size + 3
                    page = doc.new_page(width=page_w, height=page_h)
                    y = margin
                    for line in lines:
                        if y > (page_h - margin):
                            page = doc.new_page(width=page_w, height=page_h)
                            y = margin
                        page.insert_text((margin, y), line, fontname="cour", fontsize=font_size)
                        y += line_height
                    doc.save(file)
                    doc.close()
                    self.show_custom_warning("Esportazione completata", f"✓ PDF salvato:\n{file}")
                    preview.destroy()
                except Exception as e:
                    self.show_custom_warning("Errore", f"❌ Creazione PDF fallita:\n{e}")
        img_salva = self.icone_gui.get("salva")
        btn_salva = ttk.Label(frm, compound="left", image=img_salva, text=" Esporta TXT" if img_salva else "💾 Esporta TXT", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_salva.pack(side=tk.LEFT, padx=6)
        btn_salva.bind("<Button-1>", lambda e: do_save())
        img_esporta_pdf = self.icone_gui.get("salva")
        btn_esporta_pdf = ttk.Label(frm, compound="left", image=img_esporta_pdf, text=" Esporta PDF" if img_esporta_pdf else "📕 Esporta PDF", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_esporta_pdf.pack(side=tk.LEFT, padx=6)
        btn_esporta_pdf.bind("<Button-1>", lambda e: do_save_pdf())
        img_stampa = self.icone_gui.get("stampa")
        btn_stampa = ttk.Label(frm, compound="left", image=img_stampa, text=" Stampa" if img_stampa else "📄 Stampa", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_stampa.pack(side=tk.LEFT, padx=6)
        btn_stampa.bind("<Button-1>", lambda e: self._stampa_lista_diretta(contenuto_preview.rstrip('\n'), self.show_custom_warning))
        img_chiudi = self.icone_gui.get("chiudi")
        btn_chiudi = ttk.Label(frm, compound="left", image=img_chiudi, text=" Chiudi" if img_chiudi else "❌ Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_chiudi.pack(side=tk.RIGHT, padx=6)
        btn_chiudi.bind("<Button-1>", lambda e: preview.destroy())
        preview.lift()
        preview.attributes('-topmost', True)
        preview.after(100, lambda: preview.attributes('-topmost', False))
    anno_combo.bind("<<ComboboxSelected>>", lambda e: aggiorna_interfaccia())
    mostra_future_var.trace_add("write", lambda *a: aggiorna_interfaccia())
    aggiorna_interfaccia()
    pulsanti = ttk.Frame(main)
    pulsanti.pack(pady=5)
    img_simula = self.icone_gui.get("report")
    btn_simula = tk.Label(pulsanti, compound="left", image=img_simula, text="Simula Risparmio" if img_simula else "Simula Risparmio", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padx=12, pady=6, font=("Arial", 9, "bold"))
    btn_simula.pack(side="left", padx=10)
    btn_simula.bind("<Button-1>", lambda e: esegui_simulazione())
    img_esp_sim = self.icone_gui.get("salva")
    btn_esp_sim = tk.Label(pulsanti, compound="left", image=img_esp_sim, text="Esporta" if img_esp_sim else "Esporta", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padx=12, pady=6, font=("Arial", 9, "bold"))
    btn_esp_sim.pack(side="left", padx=10)
    btn_esp_sim.bind("<Button-1>", lambda e: esporta_simulazione())
    img_res_sim = self.icone_gui.get("reset")
    btn_res_sim = tk.Label(pulsanti, compound="left", image=img_res_sim, text="Reset campi" if img_res_sim else "Reset campi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padx=12, pady=6, font=("Arial", 9, "bold"))
    btn_res_sim.pack(side="left", padx=10)
    btn_res_sim.bind("<Button-1>", lambda e: reset_tutto())
    img_chiudi_sim = self.icone_gui.get("chiudi")
    btn_chiudi_sim = tk.Label(pulsanti, compound="left", image=img_chiudi_sim, text="Chiudi" if img_chiudi_sim else "Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padx=12, pady=6, font=("Arial", 9, "bold"))
    btn_chiudi_sim.pack(side="left", padx=10)
    btn_chiudi_sim.bind("<Button-1>", lambda e: popup.destroy())
    popup.bind("<Escape>", lambda e: popup.destroy())
    
