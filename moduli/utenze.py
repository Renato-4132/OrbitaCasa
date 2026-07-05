#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import datetime
import tkinter as tk
from tkinter import ttk, filedialog

def utenze(self):
    import __main__ as _app
    UTENZE_DB     = _app.UTENZE_DB
    EXPORT_FILES  = _app.EXPORT_FILES
    EXP_DB        = _app.EXP_DB

    self.check_UTENZE_DB()
    def get_consumi_per_anno(anno):
        return {
            "Acqua": [(f"{m:02d}/{anno}", 0.0, 0.0, 0.0) for m in range(1, 13)],
            "Luce":  [(f"{m:02d}/{anno}", 0.0, 0.0, 0.0) for m in range(1, 13)],
            "Gas":   [(f"{m:02d}/{anno}", 0.0, 0.0, 0.0) for m in range(1, 13)],
        }
    utenze = ["Acqua", "Luce", "Gas"]
    def carica_db():
        if os.path.exists(UTENZE_DB):
            try:
                with open(UTENZE_DB, "r", encoding="utf-8") as f:
                    data = json.load(f)
                letture = data.get("letture_salvate", {u: {} for u in utenze})
                for utenza, per_anno in letture.items():
                    for anno, righe in per_anno.items():
                        letture_norm = []
                        for r in righe:
                            if len(r) == 4:
                               mese, prec, att, _ = r
                               try:
                                   consumo = max(0.0, float(att) - float(prec))
                               except:
                                   prec, att, consumo = 0.0, 0.0, 0.0
                               letture_norm.append((mese, prec, att, consumo))
                            else:
                               letture_norm.append(tuple(r))
                        letture[utenza][anno] = letture_norm
                anagrafiche = data.get("anagrafiche", {u: {
                    "Ragione sociale": "",
                    "Telefono": "",
                    "Email": "",
                    "Numero contratto": "",
                    "POD": "",
                    "Note": ""
                } for u in utenze})
                for utenza in utenze:
                    if utenza not in anagrafiche:
                        anagrafiche[utenza] = {
                            "Ragione sociale": "",
                            "Telefono": "",
                            "Email": "",
                            "Numero contratto": "",
                            "POD": "",
                            "Note": ""
                        }
                    else:
                        for campo in ["Ragione sociale", "Telefono", "Email", "Numero contratto", "POD", "Note"]:
                            if campo not in anagrafiche[utenza]:
                                anagrafiche[utenza][campo] = ""
                return letture, anagrafiche
            except Exception as e:
                return {u: {} for u in utenze}, {u: {
                    "Ragione sociale": "",
                    "Telefono": "",
                    "Email": "",
                    "Numero contratto": "",
                    "POD": "",
                    "Note": ""
                } for u in utenze}
        else:
            return {u: {} for u in utenze}, {u: {
                "Ragione sociale": "",
                "Telefono": "",
                "Email": "",
                "Numero contratto": "",
                "POD": "",
                "Note": ""
            } for u in utenze}

    def scrivi_db():
        try:
            data = {
                "letture_salvate": {
                    u: {a: [list(r) for r in anni] for a, anni in letture_salvate[u].items()}
                    for u in utenze
                },
                "anagrafiche": anagrafiche
            }
            with open(UTENZE_DB, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=1, ensure_ascii=False)
        except Exception as e:
             self.show_custom_warning("Errore", "Errore scrittura dati")
    letture_salvate, anagrafiche = carica_db()
    self.letture_salvate_utenze = letture_salvate
    self.anagrafiche_salvate_utenze = anagrafiche
    anno_corrente = str(datetime.datetime.now().year)
    year_current = int(anno_corrente)
    anni = [str(a) for a in range(year_current, year_current-11, -1)]
    consumi = get_consumi_per_anno(anno_corrente)
    win = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    win.withdraw() 
    larghezza = 1200
    altezza = 670
    self.update_idletasks()
    self_x = self.winfo_rootx()
    self_y = self.winfo_rooty()
    self_width = self.winfo_width()
    self_height = self.winfo_height()
    x = self_x + (self_width // 2) - (larghezza // 2)
    y = self_y + (self_height // 2) - (altezza // 2)
    win.geometry(f"{larghezza}x{altezza}+{x}+{y}")
    win.minsize(larghezza, altezza)
    win.title("Gestione Consumi Utenze")
    win.protocol("WM_DELETE_WINDOW", lambda: (chiudi_viewer_tabella(), self.deiconify(), self.after(0, self.imp_entry.focus_set), win.destroy()))
    win.deiconify()
    win.update_idletasks()
    win.grab_set()
    self.withdraw()
    menu_win = tk.Menu(win, background=self.MENU_BG_DARK, foreground=self.MENU_FG_LIGHT, activebackground=self.MENU_ACT_BG_COLOR, activeforeground=self.MENU_ACT_FG_COLOR)
    menu_funzioni = tk.Menu(menu_win, tearoff=0, bg=self.MENU_BG, fg=self.MENU_FG_LIGHT, activebackground=self.MENU_ACT_BG_COLOR, activeforeground=self.MENU_ACT_FG_COLOR)
    menu_funzioni.add_command(label="📂 Esporta Preview", command=lambda: esporta_preview())
    menu_funzioni.add_command(label="⚙️ Analizza", command=lambda: crea_tabella_consumi(win, UTENZE_DB))
    menu_funzioni.add_separator()
    menu_funzioni.add_command(label="📥 Tabella Consumi PDF", command=lambda: self.scarica_tabella())
    menu_funzioni.add_separator()
    menu_funzioni.add_command(label="❌ Chiudi (ESC)", command=lambda: (self.deiconify(), self.after(0, self.imp_entry.focus_set), win.destroy()))
    menu_win.add_cascade(label="📂 Opzioni", menu=menu_funzioni)
    menu_database = tk.Menu(menu_win, tearoff=0, bg=self.MENU_BG, fg=self.MENU_FG_LIGHT, activebackground=self.MENU_ACT_BG_COLOR, activeforeground=self.MENU_ACT_FG_COLOR)
    menu_database.add_command(label="📤 Esporta Consumi", command=lambda: esporta_letture_data(UTENZE_DB))
    menu_database.add_command(label="📥 Importa Consumi", command=lambda: importa_letture_data(letture_salvate, anagrafiche))
    menu_database.add_separator()
    menu_database.add_command(label="📥 Azzera Consumi", command=lambda: reset_utenze_letture())
    menu_win.add_cascade(label="🗄️ Database", menu=menu_database)
    win.config(menu=menu_win)
    win.bind("<Escape>", lambda e: (chiudi_viewer_tabella(), self.deiconify(), self.after(0, self.imp_entry.focus_set), win.destroy()))
    top_controls = tk.Frame(win, bg=self.COLOR_TOPLEVEL )
    top_controls.pack(pady=(0, 6))
    tk.Label(top_controls, text="Gestione Consumi Utenze", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR, font=("Arial", 14, "bold")).pack(side=tk.LEFT, padx=(0, 25))
    tk.Label(top_controls, text="Anno: ", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR).pack(side=tk.LEFT)
    anno_var = tk.StringVar(value=anno_corrente)
    def reset_utenze_letture():
        conferma = self.show_custom_askyesno(
            "Azzeramento Letture",
            "Sei sicuro di voler azzerare TUTTE le letture delle utenze?\n"
            "Questa azione eliminerà lo storico delle letture."
        )
        if conferma:
            try:
                if os.path.exists(UTENZE_DB):
                    os.remove(UTENZE_DB)
                if not os.path.exists(UTENZE_DB):
                    with open(UTENZE_DB, "w") as file:
                        file.write("{\n}\n")  
                self.deiconify()
                win.destroy()
                self.utenze()
                self.show_custom_warning("Letture", "Letture utenze azzerate con successo.")      
            except Exception as e:
                self.show_custom_warning("Errore Azzeramento", f"Si è verificato un errore durante l'azzeramento:\n{e}")
    def salva_letture_preview(txt, preview_win):
        now = datetime.date.today()
        default_filename = f"Letture_Export_{now.day:02d}-{now.month:02d}-{now.year}.txt"
        preview_win.wm_attributes('-topmost', 1)
        file = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("File txt", "*.txt")],
            initialdir=EXPORT_FILES,
            initialfile=default_filename,
            title="Salva Preview",
            confirmoverwrite=False,
            parent=preview_win)
        preview_win.wm_attributes('-topmost', 0)
        if file:
            if os.path.exists(file):
                conferma = self.show_custom_askyesno(
                    "Sovrascrivere file?",
                    f"Il file '{os.path.basename(file)}' \nesiste già. Vuoi sovrascriverlo?"
                )
                if not conferma:
                    return 
            with open(file, "w", encoding="utf-8") as f:
                lines = txt.get("1.0", tk.END)
                f.write(lines)
            preview_win.destroy()
            self.show_custom_warning("Esportazione completata", f"Riepilogo esportate in\n{file}")
    def esporta_preview():
        preview_win = tk.Toplevel(win, bg=self.COLOR_TOPLEVEL)
        preview_win.title("Preview Esportazione")
        preview_win.geometry("1050x600")
        screen_width = preview_win.winfo_screenwidth()
        screen_height = preview_win.winfo_screenheight()
        x = (screen_width - 1050) // 2
        y = (screen_height - 600) // 2
        preview_win.geometry(f"1050x600+{x}+{y}")
        preview_win.minsize(1050, 600)
        preview_win.after(10, lambda: preview_win.focus_force())
        txt = tk.Text(preview_win, font=("Courier New", 10), wrap="none")
        txt.pack(fill=tk.BOTH, expand=True)
        anno_x = anno_var.get()
        txt.insert(tk.END, f"Consumi utenze per anno {anno_x}\n\n")
        header = f"{'Mese':<10}"
        for utenza in utenze:
            header += f"{utenza:^30}"
        txt.insert(tk.END, header + "\n")
        sub_header = f"{'':<10}"
        for _ in utenze:
            sub_header += f"{'Prec':>8}{'Att':>10}{'Cons':>10}  "
        txt.insert(tk.END, sub_header + "\n")
        txt.insert(tk.END, "─" * len(header) + "\n")
        mesi = [self.trees[utenze[0]].item(iid)['values'][0] for iid in self.trees[utenze[0]].get_children()]
        for i, mese in enumerate(mesi):
            riga = f"{mese:<10}"
            for utenza in utenze:
                values = self.trees[utenza].item(self.trees[utenza].get_children()[i])['values']
                prec, att, cons = float(values[1]), float(values[2]), float(values[3])
                riga += f"{prec:8.2f}{att:10.2f}{cons:10.2f}  "
            txt.insert(tk.END, riga + "\n")
        txt.insert(tk.END, "─" * len(header) + "\n")
        tot_riga = f"{'Totale':<10}"
        for utenza in utenze:
            somma = sum(float(self.trees[utenza].item(iid)['values'][3]) for iid in self.trees[utenza].get_children())
            tot_riga += f"{'':8}{'':10}{somma:10.2f}  "
        txt.insert(tk.END, tot_riga + "\n")
        txt.config(state="disabled")
        btn_frame = tk.Frame(preview_win, bg=self.COLOR_TOPLEVEL)
        btn_frame.pack(fill=tk.X, pady=12)
        img_esp_lett = self.icone_gui.get("salva")
        btn_esp_lett = ttk.Label(btn_frame, compound="left", image=img_esp_lett, text=" Esporta" if img_esp_lett else "💾 Esporta", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_esp_lett.pack(side=tk.LEFT, padx=10)
        btn_esp_lett.bind("<Button-1>", lambda e: salva_letture_preview(txt, preview_win))
        img_stampa_lett = self.icone_gui.get("stampa")
        btn_stampa_lett = ttk.Label(btn_frame, compound="left", image=img_stampa_lett, text=" Stampa" if img_stampa_lett else "📄 Stampa", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_stampa_lett.pack(side=tk.LEFT, padx=10)
        btn_stampa_lett.bind("<Button-1>", lambda e: self._stampa_lista_diretta(txt.get("1.0", tk.END), self.show_custom_warning))
        img_chiudi_lett = self.icone_gui.get("chiudi")
        btn_chiudi_lett = ttk.Label(btn_frame, compound="left", image=img_chiudi_lett, text=" Chiudi" if img_chiudi_lett else "❌ Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_chiudi_lett.pack(side=tk.RIGHT, padx=10)
        btn_chiudi_lett.bind("<Button-1>", lambda e: preview_win.destroy())
        preview_win.lift()
        preview_win.attributes('-topmost', True)
        preview_win.after(200, lambda: preview_win.attributes('-topmost', False))
        preview_win.bind("<Escape>", lambda e: preview_win.destroy())
    def chiudi():
        chiudi_viewer_tabella()
        win.destroy()
        self.deiconify()
        self.after(0, self.imp_entry.focus_set)
    def chiudi_viewer_tabella():
        v = getattr(self, '_viewer_tabella_win', None)
        if v and v.winfo_exists():
           v.destroy()
    def cambia_anno(*args):
        nonlocal consumi
        for utenza in utenze:
            if self.trees[utenza].get_children():
                anno_attuale = self.trees[utenza].item(self.trees[utenza].get_children()[0])['values'][0].split("/")[1]
                letture_salvate[utenza][anno_attuale] = [
                    tuple(self.trees[utenza].item(iid)['values']) for iid in self.trees[utenza].get_children()
                ]
        scrivi_db()
        for utenza in utenze:
            self.trees[utenza].delete(*self.trees[utenza].get_children())
        anno_sel = anno_var.get()
        consumi = get_consumi_per_anno(anno_sel)
        for utenza in utenze:
            if (anno_sel not in letture_salvate[utenza]) or (not letture_salvate[utenza][anno_sel]):
                letture_salvate[utenza][anno_sel] = [
                    (f"{m:02d}/{anno_sel}", 0.0, 0.0, 0.0) for m in range(1, 13)
                ]
            righe = letture_salvate[utenza][anno_sel]
            righe_norm = []
            for r in righe:
                if len(r) == 4:
                    mese, prec, att, consumo = r
                    consumo = max(0.0, float(att) - float(prec))
                    righe_norm.append((mese, float(prec), float(att), float(consumo)))
                else:
                    righe_norm.append(tuple(r))
            letture_salvate[utenza][anno_sel] = righe_norm
            for mese, prec, att, consumo in righe_norm:
                self.trees[utenza].insert("", "end", values=(mese, float(prec), float(att), float(consumo)))
    anno_cb = ttk.Combobox(top_controls, values=anni, textvariable=anno_var, style="Border.TCombobox", state="readonly", width=8)
    anno_cb.pack(side=tk.LEFT)
    def reset_anno():
        anno_var.set(anno_corrente)
    img_reset_anno = self.icone_gui.get("reset")
    btn_reset_anno = ttk.Label(top_controls, compound="left", image=img_reset_anno, text=" 🔄" if not img_reset_anno else "", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(5, 5))
    btn_reset_anno.pack(side=tk.LEFT, padx=2)
    btn_reset_anno.bind("<Button-1>", lambda e: reset_anno())
    img_chiudi_top = self.icone_gui.get("chiudi")
    btn_chiudi_top = ttk.Label(top_controls, compound="left", image=img_chiudi_top, text=" Chiudi" if img_chiudi_top else "Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
    btn_chiudi_top.pack(side=tk.LEFT, padx=7)
    btn_chiudi_top.bind("<Button-1>", lambda e: chiudi())
    anno_var.trace_add("write", cambia_anno)
    main_frame = ttk.Frame(win)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=18, pady=6)
    for c in range(len(utenze)):
        main_frame.grid_columnconfigure(c, weight=1)
    colori = {"Acqua": "#ccefff", "Luce": "#fff9cc", "Gas": "#ffe0cc"}
    self.trees = {}
    anag_entries = {}
    def importa_letture_data(letture_salvate, anagrafiche):
        now = datetime.date.today()
        default_dir = EXP_DB
        default_filename = f"{now.day:02d}-{now.month:02d}-{now.year}-utenze_db.json"
        file = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("File JSON", "*utenze_db.json"), ("Tutti i file", "*.*")],
            initialdir=default_dir,
            initialfile=default_filename,
            title="Importa utenze",
        )
        if file:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                letture = data.get("letture_salvate", {})
                anagrafiche = data.get("anagrafiche", {})
                self.letture_salvate_utenze.update(letture)
                self.anagrafiche_salvate_utenze.update(anagrafiche)     
                scrivi_db()
                self.deiconify()
                win.destroy()
                self.utenze()
                self.show_custom_warning("Importazione riuscita", "Utenze importate correttamente!")
            except Exception as e:
                self.show_custom_warning("Errore", f"Errore durante l'importazione:\n{e}")
    def esporta_letture_data(UTENZE_DB):
        now = datetime.date.today()
        default_dir = EXP_DB
        default_filename = f"{now.day:02d}-{now.month:02d}-{now.year}-utenze_db.json"
        file = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("File JSON", "*utenze_db.json"), ("Tutti i file", "*.*")],
            initialdir=default_dir,
            initialfile=default_filename,
            confirmoverwrite=False,
            title="Esporta utenze",
        )
        if file:
            try:
                data = {
                    "letture_salvate": self.letture_salvate_utenze,
                    "anagrafiche": self.anagrafiche_salvate_utenze
                }
                with open(file, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self.show_custom_warning("Esportazione completata", f"Database utenze salvato in:\n{file}")
            except Exception as e:
                self.show_custom_warning("Errore", f"Errore durante l'esportazione:\n{e}")
    def crea_tabella_consumi(parent, UTENZE_DB):
        try:
            with open(UTENZE_DB, "r", encoding="utf-8") as f:
                data = json.load(f)
                letture_salvate = data.get("letture_salvate", {})
        except Exception as e:
            print(f"Errore lettura file: {e}")
            return
        utenze = ["Acqua", "Luce", "Gas"]
        win = tk.Toplevel(parent, bg=self.COLOR_TOPLEVEL )
        win.bind("<Escape>", lambda e: win.destroy())
        win.title("Consumi Utenze - Anteprima")
        win.geometry("1150x600")
        win.transient(parent)
        win.grab_set()
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x_coordinate = (screen_width - 1150) // 2
        y_coordinate = (screen_height - 600) // 2
        win.geometry(f"1150x600+{x_coordinate}+{y_coordinate}")
        win.minsize(1150, 600)
        frame_principale = ttk.Frame(win)
        frame_principale.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        canvas = tk.Canvas(frame_principale, bg=self.COLOR_TOPLEVEL)
        scrollbar = ttk.Scrollbar(frame_principale, orient="vertical", command=canvas.yview, style="Vertical.TScrollbar")
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        frame_interno = ttk.Frame(canvas)
        canvas_window = canvas.create_window((0, 0), window=frame_interno, anchor="nw")
        def aggiorna_scrollregion(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())
        frame_interno.bind("<Configure>", aggiorna_scrollregion)
        for utenza in utenze:
            frame_tabella = ttk.Frame(frame_interno)
            frame_tabella.pack(fill=tk.BOTH, expand=True, pady=10)
            ttk.Label(
                frame_tabella,
                text=f"Consumi {utenza}",
                font=("Arial", 12, "bold")
            ).pack(pady=5)
            colonne = [
                "Anno", "Gen", "Feb", "Mar", "Apr", "Mag", "Giu",
                "Lug", "Ago", "Set", "Ott", "Nov", "Dic", "Totale"
            ]
            tree = ttk.Treeview(
                frame_tabella,
                columns=colonne,
                show="headings",
                height=4
            )
            for col in colonne:
                tree.heading(col, text=col)
                tree.column(col, width=80, anchor="center")
            tree.pack(fill=tk.BOTH, expand=True)
            for anno in sorted(letture_salvate.get(utenza, {}).keys(), reverse=True):
                row = [anno]
                tot_consumi = 0.0
                for mese in range(1, 13):
                    mese_str = f"{mese:02d}/{anno}"
                    consumo = sum(
                        float(r[3])
                        for r in letture_salvate.get(utenza, {}).get(anno, [])
                        if r[0] == mese_str
                    )
                    row.append(consumo)
                    tot_consumi += consumo
                row.append(tot_consumi)
                tree.insert("", tk.END, values=row)
        frame_bottoni = tk.Frame(win, bg=self.COLOR_TOPLEVEL )
        frame_bottoni.pack(fill=tk.X, padx=10, pady=10)
        img_salva_lett = self.icone_gui.get("salva")
        btn_salva_lett = ttk.Label(frame_bottoni, compound="left", image=img_salva_lett, text=" Salva" if img_salva_lett else "Salva", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_salva_lett.pack(side=tk.LEFT, padx=10)
        btn_salva_lett.bind("<Button-1>", lambda e: salva_dati_letture(letture_salvate))
        img_chiudi_lett_w = self.icone_gui.get("chiudi")
        btn_chiudi_lett_w = ttk.Label(frame_bottoni, compound="left", image=img_chiudi_lett_w, text=" Chiudi" if img_chiudi_lett_w else "Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_chiudi_lett_w.pack(side=tk.RIGHT, padx=10)
        btn_chiudi_lett_w.bind("<Button-1>", lambda e: win.destroy())
    def salva_dati_letture(letture_salvate):
        win.focus_force()
        now = datetime.date.today()
        default_filename = f"Letture_anno_Export_{now.day:02d}-{now.month:02d}-{now.year}.txt"
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("File txt", "*.txt")],
            initialdir=EXPORT_FILES,
            initialfile=default_filename,
            confirmoverwrite=False,
            title="Salva i dati dei consumi"
           )
        if file_path:
            if os.path.exists(file_path):
                conferma = self.show_custom_askyesno(
                    "Sovrascrivere file?",
                    f"Il file '{os.path.basename(file_path)}' \nesiste già. Vuoi sovrascriverlo?"
                )
                if not conferma:
                    return
        if not file_path:
            return
        mesi = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu",
        "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                for utenza, anni in letture_salvate.items():
                    f.write(f"Consumi {utenza}:\n")
                    intestazione = f"{'Anno':>6} " + "".join([f"{mese:>8}" for mese in mesi]) + f"{'Totale':>10}\n"
                    f.write(intestazione)
                    f.write("-" * len(intestazione) + "\n")
                    for anno in sorted(anni.keys(), reverse=True):
                        valori_mensili = {r[0]: float(r[3]) for r in anni[anno]}
                        riga = f"{anno:>6} "
                        totale = 0.0
                        for m in range(1, 13):
                            mese_str = f"{m:02d}/{anno}"
                            consumo = valori_mensili.get(mese_str, 0.0)
                            riga += f"{consumo:8.2f}"
                            totale += consumo
                        riga += f"{totale:10.2f}\n"
                        f.write(riga)
                    f.write("\n")
            self.show_custom_warning("Esportazione", f"Riepilogo esportato correttamente in:\n{file_path}")
        except Exception as e:
            self.show_custom_warning("Errore", f"Errore durante il salvataggio:\n{e}")
    def centra_su_padre(finestra, padre):
        padre.update_idletasks()
        larghezza = finestra.winfo_reqwidth()
        altezza = finestra.winfo_reqheight()
        px = padre.winfo_rootx() + (padre.winfo_width() // 2) - (larghezza // 2)
        py = padre.winfo_rooty() + (padre.winfo_height() // 2) - (altezza // 2)
        finestra.geometry(f"+{px}+{py}")
    def salva_letture_utenza(utenza):
        anno_sel = anno_var.get()
        letture_salvate[utenza][anno_sel] = [
            tuple(self.trees[utenza].item(iid)['values']) for iid in self.trees[utenza].get_children()
        ]
        scrivi_db()
    def salva_anagrafica_utenza(utenza):
        for field, ent in anag_entries[utenza].items():
            if field == "Note":
                anagrafiche[utenza][field] = ent.get("1.0", "end-1c")
            else:
                anagrafiche[utenza][field] = ent.get()
        scrivi_db()
    def on_tree_double_click(event, utenza):
        tree = self.trees[utenza]
        item_id = tree.identify_row(event.y)
        if item_id:
            tree.selection_set(item_id)
            tree.focus(item_id)
            apri_modale(utenza)
    def on_tree_right_click(event, utenza):
        tree = self.trees[utenza]
        item_id = tree.identify_row(event.y)
        if not item_id:
            return
        tree.selection_set(item_id)
        tree.focus(item_id)
        apri_modale_solo_totale(utenza)
    def apri_modale_solo_totale(utenza):
        selected = self.trees[utenza].focus()
        if not selected:
            self.show_toast("Seleziona un mese dalla tabella.")
            return
        item = self.trees[utenza].item(selected)
        mese, prec, att, consumo = item['values']
        try:
            consumo = float(consumo)
        except:
            consumo = 0.0
        modal = tk.Toplevel(win, bg=self.COLOR_TOPLEVEL)
        modal.title(f"Consumo {utenza}")
        modal.geometry("300x140")
        modal.resizable(False, False)
        modal.transient(win)
        centra_su_padre(modal, win)
        modal.after_idle(modal.grab_set)
        def only_numeric_8char(val):
            if len(val) > 8:
                return False
            if val == "":
                return True
            if val.count(".") > 1:
                return False
            return all(c.isdigit() or c == "." for c in val)
        vcmd = modal.register(only_numeric_8char)
        tk.Label(modal, text=f"{utenza} - {mese}", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR, font=("Arial", 12, "bold")).pack(pady=10)
        tk.Label(modal, text="Consumo:", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR).pack()
        consumo_var = tk.DoubleVar(value=consumo)
        e_cons = tk.Entry(modal, textvariable=consumo_var, font=("Arial", 10), width=15,
                  validate="key", validatecommand=(vcmd, "%P"))
        e_cons.pack()
        e_cons.focus_set()
        modal.bind("<Return>", lambda event: salva()) 
        modal.bind("<KP_Enter>", lambda event: salva()) 
        def salva():
            val = e_cons.get().strip()
            if not val:
                self.show_toast("Inserisci il valore del consumo.")
                return
            try:
                cons = float(consumo_var.get())
                if cons < 0:
                    self.show_toast("Il Consumo non può essere negativo.")
                    return
                nuovo_att = float(prec) + cons
                self.trees[utenza].item(selected, values=(mese, prec, nuovo_att, cons))
                anno_sel = anno_var.get()
                righe = [
                    tuple(self.trees[utenza].item(iid)['values'])
                    for iid in self.trees[utenza].get_children()
                ]
                letture_salvate[utenza][anno_sel] = righe
                scrivi_db()
                modal.destroy()
            except ValueError:
                self.show_custom_warning("Errore", "Valore non valido.")
        btn_frame = tk.Frame(modal, bg=self.COLOR_TOPLEVEL)
        btn_frame.pack(fill="x", pady=10, padx=10)
        img_salva_modal = self.icone_gui.get("salva")
        btn_salva = ttk.Label(btn_frame, compound="left", image=img_salva_modal, text=" Salva" if img_salva_modal else "Salva", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_salva.pack(side=tk.LEFT, padx=(0, 10))
        btn_salva.bind("<Button-1>", lambda e: salva())
        img_chiudi_modal = self.icone_gui.get("chiudi")
        btn_chiudi = ttk.Label(btn_frame, compound="left", image=img_chiudi_modal, text=" Chiudi" if img_chiudi_modal else "Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_chiudi.pack(side=tk.RIGHT, padx=(10, 0))
        btn_chiudi.bind("<Button-1>", lambda e: modal.destroy())
        modal.bind("<Escape>", lambda e: modal.destroy())
    def apri_modale(utenza):
        selected = self.trees[utenza].focus()
        if not selected:
            self.show_custom_warning("Errore", "Seleziona un mese dalla tabella")
            return
        item = self.trees[utenza].item(selected)
        mese, prec, att, _ = item['values']
        items = self.trees[utenza].get_children()
        idx = items.index(selected)
        if idx > 0:
            prev_item = self.trees[utenza].item(items[idx - 1])
            try:
                prec = float(prev_item['values'][2])
            except:
                prec = 0.0
        try:
            prec = float(prec)
        except:
            prec = 0.0
        try:
            att = float(att)
        except:
            att = 0.0
        modal = tk.Toplevel(win, bg=self.COLOR_TOPLEVEL)
        modal.title(f"Letture {utenza}")
        modal.geometry("300x180")
        modal.resizable(False, False)
        modal.transient(win)
        centra_su_padre(modal, win)
        modal.after_idle(modal.grab_set)
        modal.bind("<Return>", lambda e: salva())
        modal.bind("<KP_Enter>", lambda e: salva())
        def only_numeric_8char(val):
            if len(val) > 8:
                return False
            if val == "":
                return True
            if val.count(".") > 1:
                return False
            return all(c.isdigit() or c == "." for c in val)
        vcmd = modal.register(only_numeric_8char)
        tk.Label(modal, text=f"{utenza} - {mese}", bg=self.COLOR_TOPLEVEL,fg=self.TEXT_COLOR , font=("Arial", 12, "bold")).pack(pady=10)
        tk.Label(modal, text="Lettura precedente:", bg=self.COLOR_TOPLEVEL,fg=self.TEXT_COLOR).pack()
        prec_var = tk.DoubleVar(value=prec)
        e_prec = tk.Entry(modal, textvariable=prec_var, font=("Arial", 10), width=22,
                  validate="key", validatecommand=(vcmd, "%P"))
        e_prec.pack()
        tk.Label(modal, text="Lettura attuale:", bg=self.COLOR_TOPLEVEL,fg=self.TEXT_COLOR).pack()
        att_var = tk.DoubleVar(value=att)
        e_att = tk.Entry(modal, textvariable=att_var, font=("Arial", 10), width=22,
                 validate="key", validatecommand=(vcmd, "%P"))
        e_att.pack()
        modal.e_prec = e_prec
        modal.e_att = e_att
        modal.prec_var = prec_var
        modal.att_var = att_var
        modal.mese = mese
        modal.utenza = utenza
        def salva():
            try:
                if not e_prec.get().strip() or not e_att.get().strip():
                    self.show_custom_warning("Campo vuoto", "Compila entrambi i campi prima di salvare.")
                    return
                p = float(prec_var.get())
                a = float(att_var.get())
                if a < p:
                    conferma = tk.Toplevel(modal, bg=self.COLOR_TOPLEVEL)
                    conferma.title("Conferma Forzatura")
                    conferma.geometry("350x120")
                    conferma.resizable(False, False)
                    conferma.transient(modal)
                    conferma.update_idletasks()
                    conferma.grab_set()
                    centra_su_padre(conferma, modal)
                    msg = ttk.Label(conferma,
                                   text="La lettura attuale è minore della precedente.\nVuoi forzare l'inserimento?")
                    msg.pack(pady=15)
                    btn_frame = ttk.Frame(conferma)
                    btn_frame.pack()
                    def ok():
                        consumo = round(max(0.0, a - p), 2)
                        self.trees[utenza].item(selected, values=(mese, p, a, consumo))
                        if idx + 1 < len(items):
                            next_item = self.trees[utenza].item(items[idx + 1])
                            next_mese, _, next_att, _ = next_item['values']
                            next_att_f = float(next_att)
                            next_cons = round(next_att_f - a, 2)
                            self.trees[utenza].item(items[idx + 1], values=(next_mese, a, next_att_f, next_cons))
                        conferma.destroy()
                        modal.destroy()
                        salva_letture_utenza(utenza)
                    def annulla():
                        conferma.destroy()
                    img_forza = self.icone_gui.get("modifica")
                    btn_forza = ttk.Label(btn_frame, compound="left", image=img_forza, text=" Forza" if img_forza else "Forza", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5), width=10, anchor="center")
                    btn_forza.pack(side=tk.LEFT, padx=12)
                    btn_forza.bind("<Button-1>", lambda e: ok())
                    img_annulla = self.icone_gui.get("chiudi")
                    btn_annulla = ttk.Label(btn_frame, compound="left", image=img_annulla, text=" Annulla" if img_annulla else "Annulla", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5), width=10, anchor="center")
                    btn_annulla.pack(side=tk.LEFT, padx=12)
                    btn_annulla.bind("<Button-1>", lambda e: annulla())
                    return
                consumo = round(a - p, 2)
                self.trees[utenza].item(selected, values=(mese, p, a, consumo))
                if idx + 1 < len(items):
                    next_item = self.trees[utenza].item(items[idx + 1])
                    next_mese, _, next_att, _ = next_item['values']
                    next_att_f = float(next_att)
                    next_cons = max(0.0, next_att_f - a)
                    self.trees[utenza].item(items[idx + 1], values=(next_mese, a, next_att_f, next_cons))
                modal.destroy()
                salva_letture_utenza(utenza)
            except ValueError:
                self.show_custom_warning("Errore", "Valori non validi")
        img_salva_mod = self.icone_gui.get("salva")
        btn_salva_mod = ttk.Label(modal, compound="left", image=img_salva_mod, text=" Salva" if img_salva_mod else "Salva", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_salva_mod.pack(side=tk.LEFT, padx=10)
        btn_salva_mod.bind("<Button-1>", lambda e: salva())
        img_chiudi_mod = self.icone_gui.get("chiudi")
        btn_chiudi_mod = ttk.Label(modal, compound="left", image=img_chiudi_mod, text=" Chiudi" if img_chiudi_mod else "Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_chiudi_mod.pack(side=tk.RIGHT, padx=10)
        btn_chiudi_mod.bind("<Button-1>", lambda e: modal.destroy())
        modal.bind("<Escape>", lambda e: modal.destroy())
    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)
    for utenza in utenze:
            tab = ttk.Frame(notebook)
            notebook.add(tab, text=f"{'💧' if utenza=='Acqua' else '💡' if utenza=='Luce' else '🔥'} {utenza}")
            colore_bg = colori[utenza]
            frame = tk.Frame(tab, bg=colore_bg, bd=2, relief="groove")
            frame.pack(fill="both", expand=True, padx=8, pady=8)
            top_btn_fr = tk.Frame(frame, bg=colore_bg)
            top_btn_fr.pack(fill="x", padx=4, pady=(2, 0))
            bg_utenza = colori.get(utenza, "#f0f0f0")
            img_mod_lett = self.icone_gui.get("modifica")
            btn_mod_lett = ttk.Label(top_btn_fr, compound="left", image=img_mod_lett, text=" Modifica Letture" if img_mod_lett else "Modifica Letture", background=bg_utenza, foreground=self.COLOR_BLACK, cursor="hand2", padding=(10, 5))
            btn_mod_lett.pack(side=tk.LEFT, padx=5, pady=2)
            btn_mod_lett.bind("<Button-1>", lambda e, u=utenza: apri_modale(u))
            img_mod_cons = self.icone_gui.get("modifica")
            btn_mod_cons = ttk.Label(top_btn_fr, compound="left", image=img_mod_cons, text=" Modifica Consumo" if img_mod_cons else "Modifica Consumo", background=bg_utenza, foreground=self.COLOR_BLACK, cursor="hand2", padding=(10, 5))
            btn_mod_cons.pack(side=tk.LEFT, padx=5, pady=2)
            btn_mod_cons.bind("<Button-1>", lambda e, u=utenza: apri_modale_solo_totale(u))
            tk.Label(
                top_btn_fr,
                text="🖱️ 2 Click sx: Mod.letture | Click dx: Mod.consumo",
                font=("Arial", 9, "bold"),
                fg="black",
                bg=bg_utenza
            ).pack(side=tk.LEFT, padx=10, pady=2)
            tree = ttk.Treeview(frame, columns=("Mese", "Prec", "Att", "Consumo"), show="headings", height=12)
            for col in ("Mese", "Prec", "Att", "Consumo"):
                    tree.heading(col, text=col)
                    tree.column(col, anchor="center", width=80)
            tree.pack(padx=8, pady=6, fill="both", expand=True)
            anno_sel = anno_var.get()
            if (anno_sel not in letture_salvate[utenza]) or (not letture_salvate[utenza][anno_sel]):
                    letture_salvate[utenza][anno_sel] = [(f"{m:02d}/{anno_sel}", 0.0, 0.0, 0.0) for m in range(1, 13)]
            righe = letture_salvate[utenza][anno_sel]
            righe_norm = []
            for r in righe:
                    if len(r) == 4:
                            mese, prec, att, consumo = r
                            consumo = max(0.0, float(att) - float(prec))
                            righe_norm.append((mese, float(prec), float(att), float(consumo)))
                    else:
                            righe_norm.append(tuple(r))
            letture_salvate[utenza][anno_sel] = righe_norm
            for mese, prec, att, consumo in righe_norm:
                    tree.insert("", "end", values=(mese, float(prec), float(att), float(consumo)))
            self.trees[utenza] = tree
            tree.bind("<Double-1>", lambda event, utenza=utenza: on_tree_double_click(event, utenza))
            tree.bind("<Button-3>", lambda event, utenza=utenza: on_tree_right_click(event, utenza))
            SFONDO_EDITABILE = 'yellow'
            SFONDO_BLOCCATO = 'white'
            anag_frame = tk.LabelFrame(frame, text="Dati Anagrafici", bg=colore_bg)
            anag_frame.pack(fill="x", padx=8, pady=8)
            anag_frame.grid_columnconfigure(3, weight=1)
            anag_frame.grid_columnconfigure(4, weight=0)
            anag_entries[utenza] = {}
            campi = [("Ragione sociale", 40), ("Telefono", 40), ("Email", 40), ("Numero contratto", 40), ("POD", 40)]
            for row, (label, width) in enumerate(campi):
                tk.Label(anag_frame, text=label+":", bg=colore_bg).grid(row=row, column=0, sticky="e", padx=5, pady=2)
                ent = tk.Entry(anag_frame, 
                               width=width, 
                               bg=SFONDO_EDITABILE, 
                               readonlybackground=SFONDO_BLOCCATO, 
                               disabledbackground=SFONDO_BLOCCATO) 
                ent.grid(row=row, column=1, sticky="w", padx=5, pady=2)
                ent.insert(0, anagrafiche[utenza][label])
                ent.config(state="readonly") 
                anag_entries[utenza][label] = ent
            tk.Label(anag_frame, text="Note:", bg=colore_bg).grid(row=0, column=2, sticky="ne", padx=5, pady=2)
            note_container = tk.Frame(anag_frame, bg=colore_bg)
            note_container.grid(row=0, column=3, rowspan=6, sticky="nsew", padx=5, pady=2)
            note_scrollbar = ttk.Scrollbar(note_container, orient=tk.VERTICAL, style="Vertical.TScrollbar")
            note_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            note_txt = tk.Text(
                note_container, 
                width=60, 
                height=8, 
                wrap="word",
                bg=SFONDO_BLOCCATO,
                yscrollcommand=note_scrollbar.set
            )
            note_txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True) 
            note_scrollbar.config(command=note_txt.yview)
            note_txt.insert("1.0", anagrafiche[utenza]["Note"])
            note_txt.config(state="disabled")
            anag_entries[utenza]["Note"] = note_txt
            btns = ttk.Frame(anag_frame)
            btns.grid(row=0, column=4, rowspan=6, sticky="n", padx=(5,10), pady=2)
            def set_editable(editable, u=utenza):
                colore_sfondo = SFONDO_EDITABILE if editable else SFONDO_BLOCCATO
                for k, ent in anag_entries[u].items():
                    if k == "Note":
                        ent.config(state="normal" if editable else "disabled")
                        ent.config(background=colore_sfondo) 
                    else:
                        ent.config(state="normal" if editable else "readonly")
                        ent.config(bg=colore_sfondo)
            def salva_dati(u=utenza):
                for field, ent in anag_entries[u].items():
                    if field == "Note":
                        anagrafiche[u][field] = ent.get("1.0", "end-1c")
                    else:
                        anagrafiche[u][field] = ent.get()
                set_editable(False, u)
                scrivi_db()
                self.show_custom_warning("Attenzione", f"Dati {u} Salvati correttamente !")
            def modifica_dati(u=utenza):
                set_editable(True, u)
            btns = tk.Frame(anag_frame, bg=bg_utenza)
            btns.grid(row=0, column=4, rowspan=6, sticky="n", padx=(5,10), pady=2)
            img_salva_u = self.icone_gui.get("salva")
            btn_salva_u = ttk.Label(btns, compound="left", image=img_salva_u, text=" Salva" if img_salva_u else "Salva", background=bg_utenza, foreground=self.COLOR_BLACK, cursor="hand2", padding=(10, 5), width=10, anchor="center")
            btn_salva_u.pack(pady=(0, 5))
            btn_salva_u.bind("<Button-1>", lambda e, u=utenza: salva_dati(u))
            img_modifica_u = self.icone_gui.get("modifica")
            btn_modifica_u = ttk.Label(btns, compound="left", image=img_modifica_u, text=" Modifica" if img_modifica_u else "Modifica", background=bg_utenza, foreground=self.COLOR_BLACK, cursor="hand2", padding=(10, 5), width=10, anchor="center")
            btn_modifica_u.pack()
            btn_modifica_u.bind("<Button-1>", lambda e, u=utenza: modifica_dati(u))
            
