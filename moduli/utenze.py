#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import tempfile
import datetime
import threading
import tkinter as tk
from tkinter import ttk, filedialog
import pymupdf as fitz

def utenze(self):
    import __main__ as _app
    UTENZE_DB     = _app.UTENZE_DB
    EXPORT_FILES  = _app.EXPORT_FILES
    EXP_DB        = _app.EXP_DB
    API_KEY       = _app.API_KEY
    GEMINI        = _app.GEMINI
    genai_client  = _app.genai_client
    types         = _app.types
    _HAS_DND      = _app._HAS_DND
    _DND_FILES    = _app._DND_FILES

    self.check_UTENZE_DB()
    def get_consumi_per_anno(anno):
        return {
            "Acqua": [(f"{m:02d}/{anno}", 0.0, 0.0, 0.0) for m in range(1, 13)],
            "Luce":  [(f"{m:02d}/{anno}", 0.0, 0.0, 0.0) for m in range(1, 13)],
            "Gas":   [(f"{m:02d}/{anno}", 0.0, 0.0, 0.0) for m in range(1, 13)],
        }
    utenze = ["Acqua", "Luce", "Gas"]
    campi_anagrafica = ["Ragione sociale", "Telefono", "Email", "Numero contratto",
                        "Codice Cliente", "Codice Utenza / Fornitura", "POD / PDR", "Note"]
    def anagrafica_vuota():
        return {campo: "" for campo in campi_anagrafica}
    def carica_db():
        if os.path.exists(UTENZE_DB):
            try:
                with open(UTENZE_DB, "r", encoding="utf-8") as f:
                    data = json.load(f)
                letture = data.get("letture_salvate", {u: {} for u in utenze})
                for utenza in utenze:
                    if utenza not in letture:
                        letture[utenza] = {}
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
                anagrafiche = data.get("anagrafiche", {u: anagrafica_vuota() for u in utenze})
                for utenza in utenze:
                    if utenza not in anagrafiche:
                        anagrafiche[utenza] = anagrafica_vuota()
                    else:
                        for campo in campi_anagrafica:
                            if campo not in anagrafiche[utenza]:
                                anagrafiche[utenza][campo] = ""
                return letture, anagrafiche
            except Exception as e:
                return {u: {} for u in utenze}, {u: anagrafica_vuota() for u in utenze}
        else:
            return {u: {} for u in utenze}, {u: anagrafica_vuota() for u in utenze}

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
    modalita_corrente = {"tutti": False, "anno": anno_corrente}

    def anni_presenti_tutti():
        anni_presenti = sorted({a for u in utenze for a in letture_salvate.get(u, {}).keys()})
        if anno_corrente not in anni_presenti:
            anni_presenti = sorted(anni_presenti + [anno_corrente])
        return anni_presenti

    def righe_anno_export(utenza, anno_x):
        mesi_l = [f"{m:02d}/{anno_x}" for m in range(1, 13)]
        righe = letture_salvate.get(utenza, {}).get(anno_x, [])
        by_mese = {r[0]: r for r in righe}
        out = []
        for mese in mesi_l:
            r = by_mese.get(mese)
            if r:
                out.append((mese, float(r[1]), float(r[2]), float(r[3])))
            else:
                out.append((mese, 0.0, 0.0, 0.0))
        return out

    win = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    win.withdraw()
    larghezza = 1350
    altezza = 630
    self.update_idletasks()
    self_x = self.winfo_rootx()
    self_y = self.winfo_rooty()
    self_width = self.winfo_width()
    self_height = self.winfo_height()
    x = self_x + (self_width // 2) - (larghezza // 2)
    y = self_y + (self_height // 2) - (altezza // 2)
    win.geometry(f"{larghezza}x{altezza}+{x}+{y}")
    win.title("Gestione Consumi Utenze")
    win.protocol("WM_DELETE_WINDOW", lambda: (chiudi_viewer_tabella(), self.deiconify(), self.after(0, self.imp_entry.focus_set), win.destroy()))
    win.deiconify()
    win.update_idletasks()
    win.minsize(larghezza, altezza)
    win.grab_set()
    self.withdraw()

    def mostra_guida_utenze():
        testo_consumi = (
            "💧⚡🔥 Gestione Consumi Utenze - Guida Rapida\n\n"
            "# SELEZIONE ANNO E TABELLE\n"
            "• Combo Anno: Scegli l'anno da consultare, oppure 'Tutti' per lo storico completo.\n"
            "• 🔄 (accanto alla combo): Torna rapidamente all'anno corrente.\n"
            "• Ogni utenza (Acqua/Luce/Gas) ha la propria tabella con Mese, Lettura Prec., Lettura Att., Consumo e Stima €.\n"
            "• Clic sull'intestazione di colonna: ordina la tabella.\n"
            "• Clic su un mese in tabella: carica i valori nel pannello 'Modifica Lettura Mensile' sottostante.\n"
            "\n# MODIFICA DI UNA LETTURA\n"
            "• Seleziona il mese in tabella, correggi Prec./Att. e premi Salva.\n"
            "• Spunta 'Inserisci solo Consumo' se non conosci le letture ma solo il consumo del periodo.\n"
            "• Se la lettura attuale è minore della precedente, viene chiesta conferma prima di forzare il salvataggio.\n"
            "• Dopo il salvataggio, la lettura Precedente del mese successivo si aggiorna automaticamente.\n"
            "\n# SCHEDA GRAFICO\n"
            "• Vista Mensile: andamento dei consumi mese per mese nell'anno selezionato.\n"
            "• Vista Annuale: totale consumi anno per anno, per confrontare più anni.\n"
            "• Vista Totali: totale complessivo storico affiancato dall'andamento annuale.\n"
            "• Hover (passa il mouse) su una barra: mostra un tooltip con i dettagli (letture, consumo, totali).\n"
            "\n# ESPORTAZIONE E STAMPA\n"
            "• Pulsante Esporta (in alto): apre l'anteprima del riepilogo consumi (anno selezionato o 'Tutti').\n"
            "• Dall'anteprima puoi: Esporta TXT, Esporta PDF oppure Stampa direttamente.\n"
        )
        testo_anagrafica = (
            "📋 Anagrafica, Costi e Fattura AI - Guida Rapida\n\n"
            "# DATI ANAGRAFICI\n"
            "• Ogni utenza ha una propria scheda: Ragione sociale, Telefono, Email, Numero contratto, Codice Cliente, Codice Utenza/Fornitura, POD/PDR, Note.\n"
            "• Premi Salva nella scheda per confermare le modifiche.\n"
            "\n# OFFERTA & COSTO UNITARIO\n"
            "• Costo Unitario tutto incluso (€/Unità): se compilato, abilita la colonna 'Stima €' nelle tabelle consumi.\n"
            "• Quota Fissa: campo puramente informativo, NON entra nel calcolo della stima.\n"
            "• Se il Costo Unitario è vuoto, le stime in tabella/grafico/esportazioni mostrano '—'.\n"
            "\n# CARICA FATTURA (AI)\n"
            "• Trascina un PDF/foto della fattura nella casella, oppure clicca per selezionarlo.\n"
            "• Richiede una chiave API Gemini configurata in Impostazioni (gratuita).\n"
            "• L'IA legge la fattura ed estrae automaticamente: consumo del periodo, costo unitario stimato, dati del fornitore, codici contratto, POD/PDR, scadenze, modalità di pagamento, ecc.\n"
            "• I campi individuati vengono precompilati nella scheda: verifica i valori e premi Salva per confermarli.\n"
        )
        testo_database = (
            "🗄️ Menu Database - Guida Rapida\n\n"
            "# 📤 Esporta Consumi\n"
            "• Salva un file JSON con tutte le letture e le anagrafiche, utile per backup o trasferimento su un altro PC.\n"
            "\n# 📥 Importa Consumi\n"
            "• Carica un file JSON esportato in precedenza, unendo/sostituendo letture e anagrafiche esistenti.\n"
            "\n# 🗑️ Azzera Consumi\n"
            "• ATTENZIONE: elimina TUTTO lo storico delle letture di tutte le utenze. Viene sempre richiesta conferma.\n"
            "\n# 📊 Scarica Tabella Consumi\n"
            "• Genera un file scaricabile con la tabella dei consumi, pronta per essere condivisa o archiviata.\n"
        )
        guida_win = tk.Toplevel(win, bg=self.COLOR_TOPLEVEL)
        guida_win.transient(win)
        guida_win.title("Guida - Gestione Consumi Utenze")
        guida_win.resizable(False, False)
        guida_win.withdraw()
        bottom_frame = ttk.Frame(guida_win)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5, padx=10)
        img_stampa = self.icone_gui.get("stampa")
        btn_stampa = tk.Label(bottom_frame, compound="left", image=img_stampa, text=" Stampa Guida",
                              background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                              cursor="hand2", padx=15, pady=6, font=("Arial", 9, "bold"))
        btn_stampa.image = img_stampa
        btn_stampa.pack(side=tk.LEFT)
        btn_stampa.bind("<Button-1>", lambda e: self._stampa_lista_diretta(
            testo_consumi + "\n" + testo_anagrafica + "\n" + testo_database, self.show_custom_warning))
        img_chiudi = self.icone_gui.get("chiudi")
        btn_chiudi = tk.Label(bottom_frame, compound="left", image=img_chiudi, text=" Chiudi (ESC)",
                              background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                              cursor="hand2", padx=15, pady=6, font=("Arial", 9, "bold"))
        btn_chiudi.image = img_chiudi
        btn_chiudi.pack(side=tk.RIGHT)
        btn_chiudi.bind("<Button-1>", lambda e: guida_win.destroy())
        notebook_guida = ttk.Notebook(guida_win)
        notebook_guida.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        def _crea_tab(titolo, testo, ico_key=None):
            tab = ttk.Frame(notebook_guida)
            img = self.icone_gui.get(ico_key) if ico_key else None
            if img:
                notebook_guida.add(tab, image=img, text=f" {titolo} ", compound="left")
            else:
                notebook_guida.add(tab, text=titolo)
            container = tk.Frame(tab, bg=self.COLOR_WHITE, highlightbackground=self.COLOR_TOPLEVEL, highlightthickness=4, bd=0)
            container.pack(fill="both", expand=True, padx=15, pady=10)
            tk.Label(container, text=testo, font=("Arial", 10),
                     bg=self.COLOR_WHITE, fg=self.COLOR_BLACK, justify=tk.LEFT, anchor='nw',
                     wraplength=920).pack(fill='both', expand=True, padx=15, pady=5)
            return tab

        _crea_tab("Consumi e Grafico", testo_consumi, "grafico_linea")
        _crea_tab("Anagrafica e Fattura AI", testo_anagrafica, "fattura_ai")
        _crea_tab("Database", testo_database, "salva")

        guida_win.update_idletasks()
        w, h = guida_win.winfo_reqwidth(), guida_win.winfo_reqheight()
        x = win.winfo_rootx() + (win.winfo_width() // 2) - (w // 2)
        y = win.winfo_rooty() + (win.winfo_height() // 2) - (h // 2)
        guida_win.geometry(f"1000x660+{x}+{y}")
        guida_win.deiconify()
        guida_win.grab_set()
        guida_win.bind("<Escape>", lambda e: guida_win.destroy())

    menu_popup = tk.Menu(win, tearoff=0, bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT, activebackground=self.MENU_ACT_BG_COLOR, activeforeground=self.MENU_ACT_FG_COLOR)
    menu_database = tk.Menu(menu_popup, tearoff=0, bg=self.MENU_BG, fg=self.MENU_FG_LIGHT, activebackground=self.MENU_ACT_BG_COLOR, activeforeground=self.MENU_ACT_FG_COLOR)
    menu_database.add_command(label="📤 Esporta Consumi", command=lambda: esporta_letture_data(UTENZE_DB))
    menu_database.add_command(label="📥 Importa Consumi", command=lambda: importa_letture_data(letture_salvate, anagrafiche))
    menu_database.add_separator()
    menu_database.add_command(label="🗑️ Azzera Consumi", command=lambda: reset_utenze_letture())
    menu_database.add_separator()
    menu_database.add_command(label="📊 Scarica Tabella Consumi", command=lambda: self.scarica_tabella())
    menu_popup.add_cascade(label="🗄️ Database", menu=menu_database)
    menu_popup.add_command(label="❓ Guida", command=mostra_guida_utenze)

    def apri_menu_popup(widget):
        try:
            menu_popup.tk_popup(widget.winfo_rootx(), widget.winfo_rooty() + widget.winfo_height())
        finally:
            menu_popup.grab_release()

    def _chiudi_menu_popup_sicuro():
        try:
            menu_popup.unpost()
            menu_popup.grab_release()
        except tk.TclError:
            pass

    _timer_menu_popup = {"id": None}

    def _avvia_timer_chiusura_popup(event=None):
        _timer_menu_popup["id"] = win.after(400, _chiudi_menu_popup_sicuro)

    def _annulla_timer_chiusura_popup(event=None):
        if _timer_menu_popup["id"] is not None:
            win.after_cancel(_timer_menu_popup["id"])
            _timer_menu_popup["id"] = None

    menu_popup.bind("<Leave>", _avvia_timer_chiusura_popup)
    menu_popup.bind("<Enter>", _annulla_timer_chiusura_popup)
    menu_database.bind("<Leave>", _avvia_timer_chiusura_popup)
    menu_database.bind("<Enter>", _annulla_timer_chiusura_popup)

    def _chiudi_popup_su_spostamento(event=None):
        _chiudi_menu_popup_sicuro()
    win.bind("<Configure>", _chiudi_popup_su_spostamento, add="+")

    def chiudi():
        chiudi_viewer_tabella()
        win.destroy()
        self.deiconify()
        self.after(0, self.imp_entry.focus_set)
    def chiudi_viewer_tabella():
        v = getattr(self, '_viewer_tabella_win', None)
        if v and v.winfo_exists():
           v.destroy()
    win.bind("<Escape>", lambda e: (chiudi_viewer_tabella(), self.deiconify(), self.after(0, self.imp_entry.focus_set), win.destroy()))

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
        tutti_anni = (anno_var.get() == "Tutti")
        preview_win = tk.Toplevel(win, bg=self.COLOR_TOPLEVEL)
        preview_win.title("Preview Esportazione")
        preview_win.geometry("1200x600")
        screen_width = preview_win.winfo_screenwidth()
        screen_height = preview_win.winfo_screenheight()
        x = (screen_width - 1200) // 2
        y = (screen_height - 600) // 2
        preview_win.geometry(f"1200x600+{x}+{y}")
        preview_win.minsize(1200, 600)
        preview_win.after(10, lambda: preview_win.focus_force())
        txt_container = tk.Frame(preview_win, bg=self.COLOR_TOPLEVEL)
        txt_container.pack(fill=tk.BOTH, expand=True)
        txt_vsb = ttk.Scrollbar(txt_container, orient="vertical", style="Vertical.TScrollbar")
        txt_hsb = ttk.Scrollbar(txt_container, orient="horizontal")
        txt = tk.Text(txt_container, font=("Courier New", 10), wrap="none",
                      yscrollcommand=txt_vsb.set, xscrollcommand=txt_hsb.set)
        txt_vsb.config(command=txt.yview)
        txt_hsb.config(command=txt.xview)
        txt_vsb.pack(side="right", fill="y")
        txt_hsb.pack(side="bottom", fill="x")
        txt.pack(side="left", fill=tk.BOTH, expand=True)
        anni_x = anni_presenti_tutti() if tutti_anni else [anno_var.get()]
        titolo = "tutti gli anni" if tutti_anni else f"anno {anni_x[0]}"
        txt.insert(tk.END, f"Consumi utenze — {titolo}\n\n")
        cu_disp = {u: (_get_costo_unitario(u) is not None) for u in utenze}
        COL_W = 42
        header = f"{'Mese':<10}"
        for utenza in utenze:
            header += f"{utenza:^{COL_W}}"
        sub_header = f"{'':<10}"
        for _ in utenze:
            sub_header += f"{'Prec':>8}{'Att':>10}{'Cons':>10}{'Stima €':>12}  "

        def _stima_txt(u, cons):
            val = _stima_costo(u, cons)
            return f"{val:12.2f}" if val is not None else f"{'—':>12}"

        grand_tot = {u: 0.0 for u in utenze}
        grand_tot_stima = {u: 0.0 for u in utenze}
        for idx_anno, anno_x in enumerate(anni_x):
            if idx_anno > 0:
                txt.insert(tk.END, "\n")
            if tutti_anni:
                txt.insert(tk.END, f"── Anno {anno_x} ──\n")
            txt.insert(tk.END, header + "\n")
            txt.insert(tk.END, sub_header + "\n")
            txt.insert(tk.END, "─" * len(header) + "\n")
            righe_per_utenza = {u: righe_anno_export(u, anno_x) for u in utenze}
            for i in range(12):
                mese = righe_per_utenza[utenze[0]][i][0]
                riga = f"{mese:<10}"
                for utenza in utenze:
                    _, prec, att, cons = righe_per_utenza[utenza][i]
                    riga += f"{prec:8.2f}{att:10.2f}{cons:10.2f}{_stima_txt(utenza, cons)}  "
                txt.insert(tk.END, riga + "\n")
            txt.insert(tk.END, "─" * len(header) + "\n")
            tot_riga = f"{'Totale':<10}"
            for utenza in utenze:
                somma = sum(r[3] for r in righe_per_utenza[utenza])
                somma_stima = sum((_stima_costo(utenza, r[3]) or 0.0) for r in righe_per_utenza[utenza])
                grand_tot[utenza] += somma
                grand_tot_stima[utenza] += somma_stima
                stima_riga_txt = f"{somma_stima:12.2f}" if cu_disp[utenza] else f"{'—':>12}"
                tot_riga += f"{'':8}{'':10}{somma:10.2f}{stima_riga_txt}  "
            txt.insert(tk.END, tot_riga + "\n")
        if tutti_anni and len(anni_x) > 1:
            txt.insert(tk.END, "\n" + "═" * len(header) + "\n")
            gtot_riga = f"{'Tot.Compl.':<10}"
            for utenza in utenze:
                stima_g_txt = f"{grand_tot_stima[utenza]:12.2f}" if cu_disp[utenza] else f"{'—':>12}"
                gtot_riga += f"{'':8}{'':10}{grand_tot[utenza]:10.2f}{stima_g_txt}  "
            txt.insert(tk.END, gtot_riga + "\n")
        txt.config(state="disabled")
        btn_frame = tk.Frame(preview_win, bg=self.COLOR_TOPLEVEL)
        btn_frame.pack(fill=tk.X, pady=12)
        img_esp_lett = self.icone_gui.get("salva")
        btn_esp_lett = ttk.Label(btn_frame, compound="left", image=img_esp_lett, text=" Esporta TXT" if img_esp_lett else "💾 Esporta TXT", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_esp_lett.pack(side=tk.LEFT, padx=10)
        btn_esp_lett.bind("<Button-1>", lambda e: salva_letture_preview(txt, preview_win))
        img_esp_pdf_lett = self.icone_gui.get("report")
        btn_esp_pdf_lett = ttk.Label(btn_frame, compound="left", image=img_esp_pdf_lett, text=" Esporta PDF" if img_esp_pdf_lett else "📄 Esporta PDF", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
        btn_esp_pdf_lett.pack(side=tk.LEFT, padx=10)
        btn_esp_pdf_lett.bind("<Button-1>", lambda e: esporta_pdf_consumi(preview_win))
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

    def esporta_pdf_consumi(preview_win_ref):
        tutti_anni = (anno_var.get() == "Tutti")
        anni_x = anni_presenti_tutti() if tutti_anni else [anno_var.get()]
        oggi = datetime.date.today()
        colori_pdf = {"Acqua": (0.0, 0.45, 0.75), "Luce": (0.80, 0.60, 0.0), "Gas": (0.80, 0.32, 0.0)}
        W, H = 595, 842
        MARG = 40
        doc = fitz.open()
        titolo_pdf = "Tutti gli anni" if tutti_anni else f"Anno {anni_x[0]}"
        y = [0]

        def intestazione_pagina(pg, sotto_titolo=None):
            pg.draw_rect(fitz.Rect(0, 0, W, 56), color=None, fill=(0.12, 0.30, 0.45))
            pg.insert_text((MARG, 34), f"Consumi Utenze — {titolo_pdf}", fontsize=15, color=(1, 1, 1), fontname="Helvetica-Bold")
            pg.insert_text((W - MARG - 130, 34), f"Generato il {oggi.strftime('%d/%m/%Y')}", fontsize=7.5, color=(1, 1, 1), fontname="Helvetica")
            y[0] = 72
            if sotto_titolo:
                pg.draw_rect(fitz.Rect(MARG, y[0], W - MARG, y[0] + 20), color=None, fill=(0.85, 0.90, 0.95))
                pg.insert_text((MARG + 4, y[0] + 14), sotto_titolo, fontsize=10, fontname="Helvetica-Bold", color=(0.12, 0.30, 0.45))
                y[0] += 34

        def intestazione_tabella(pg, utenza, nota=""):
            pg.insert_text((MARG, y[0]), f"{utenza}{nota}", fontsize=12, fontname="Helvetica-Bold", color=colori_pdf[utenza])
            y[0] += 14
            pg.draw_rect(fitz.Rect(MARG, y[0], W - MARG, y[0] + 16), color=None, fill=(0.90, 0.90, 0.90))
            pg.insert_text((MARG + 4, y[0] + 11), "Mese", fontsize=7.5, fontname="Helvetica-Bold")
            pg.insert_text((MARG + 120, y[0] + 11), "Prec.", fontsize=7.5, fontname="Helvetica-Bold")
            pg.insert_text((MARG + 210, y[0] + 11), "Att.", fontsize=7.5, fontname="Helvetica-Bold")
            pg.insert_text((MARG + 300, y[0] + 11), "Consumo", fontsize=7.5, fontname="Helvetica-Bold")
            pg.insert_text((MARG + 390, y[0] + 11), "Stima €", fontsize=7.5, fontname="Helvetica-Bold")
            y[0] += 16

        pg = doc.new_page(width=W, height=H)
        intestazione_pagina(pg, f"Anno {anni_x[0]}" if tutti_anni else None)

        for idx_anno, anno_x in enumerate(anni_x):
            if tutti_anni and idx_anno > 0:
                pg = doc.new_page(width=W, height=H)
                intestazione_pagina(pg, f"Anno {anno_x}")
            for utenza in utenze:
                if y[0] > H - 100:
                    pg = doc.new_page(width=W, height=H)
                    intestazione_pagina(pg, f"Anno {anno_x} (segue)" if tutti_anni else None)
                intestazione_tabella(pg, utenza)
                totale = 0.0
                totale_stima = 0.0
                cu_ok = _get_costo_unitario(utenza) is not None
                for mese, prec, att, cons in righe_anno_export(utenza, anno_x):
                    totale += cons
                    stima_riga = _stima_costo(utenza, cons)
                    if stima_riga is not None:
                        totale_stima += stima_riga
                    if y[0] > H - 60:
                        pg = doc.new_page(width=W, height=H)
                        intestazione_pagina(pg, f"Anno {anno_x} (segue)" if tutti_anni else None)
                        intestazione_tabella(pg, utenza, " (segue)")
                    pg.insert_text((MARG + 4, y[0] + 11), str(mese), fontsize=7.5, fontname="Helvetica")
                    pg.insert_text((MARG + 120, y[0] + 11), f"{prec:.2f}", fontsize=7.5, fontname="Helvetica")
                    pg.insert_text((MARG + 210, y[0] + 11), f"{att:.2f}", fontsize=7.5, fontname="Helvetica")
                    pg.insert_text((MARG + 300, y[0] + 11), f"{cons:.2f}", fontsize=7.5, fontname="Helvetica")
                    pg.insert_text((MARG + 390, y[0] + 11), f"{stima_riga:.2f}" if stima_riga is not None else "—", fontsize=7.5, fontname="Helvetica")
                    y[0] += 14
                if y[0] > H - 40:
                    pg = doc.new_page(width=W, height=H)
                    intestazione_pagina(pg, f"Anno {anno_x} (segue)" if tutti_anni else None)
                totale_txt = f"Totale {utenza}: {totale:.2f}"
                if cu_ok:
                    totale_txt += f"   —   Stima spesa: {totale_stima:.2f} €"
                pg.insert_text((MARG + 4, y[0] + 11), totale_txt, fontsize=8, fontname="Helvetica-Bold", color=colori_pdf[utenza])
                y[0] += 26
        n_tot = doc.page_count
        for i, p in enumerate(doc):
            p.insert_text((W - MARG - 60, H - 14), f"Pagina {i+1} / {n_tot}", fontsize=6.5, color=(0.5, 0.5, 0.5), fontname="Helvetica")
        doc.set_metadata({"title": f"Consumi Utenze — {titolo_pdf}", "author": "Gestione Utenze"})
        nome_file = "Consumi_Utenze_Tutti_gli_anni.pdf" if tutti_anni else f"Consumi_Utenze_Anno_{anni_x[0]}.pdf"
        preview_win_ref.wm_attributes('-topmost', 1)
        file = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("File PDF", "*.pdf")],
            initialdir=EXPORT_FILES,
            initialfile=nome_file,
            title="Salva PDF",
            confirmoverwrite=False,
            parent=preview_win_ref)
        preview_win_ref.wm_attributes('-topmost', 0)
        if not file:
            doc.close()
            return
        if os.path.exists(file):
            conferma = self.show_custom_askyesno(
                "Sovrascrivere file?",
                f"Il file '{os.path.basename(file)}' \nesiste già. Vuoi sovrascriverlo?"
            )
            if not conferma:
                doc.close()
                return
        try:
            doc.save(file)
        finally:
            doc.close()
        self.show_custom_warning("Esportazione completata", f"PDF esportato in\n{file}")


    def cambia_anno(*args):
        nonlocal consumi
        if not modalita_corrente["tutti"]:
            anno_prec = modalita_corrente["anno"]
            for utenza in utenze:
                if self.trees[utenza].get_children():
                    letture_salvate[utenza][anno_prec] = [
                        tuple(self.trees[utenza].item(iid)['values'])[:4] for iid in self.trees[utenza].get_children()
                    ]
            scrivi_db()
        for utenza in utenze:
            self.trees[utenza].delete(*self.trees[utenza].get_children())
        anno_sel = anno_var.get()
        if anno_sel == "Tutti":
            modalita_corrente["tutti"] = True
            for utenza in utenze:
                tree = self.trees[utenza]
                tree.tag_configure("totale_anno", background="#e1f5fe", font=("Arial", 9, "bold"))
                tree.tag_configure("totale_gen", background="#e1f5fe", font=("Arial", 9, "bold"))
                cu_disponibile = _get_costo_unitario(utenza) is not None
                grand_tot = 0.0
                grand_tot_stima = 0.0
                for anno_x in anni_presenti_tutti():
                    tot_anno = 0.0
                    tot_anno_stima = 0.0
                    for mese, prec, att, consumo in righe_anno_export(utenza, anno_x):
                        tree.insert("", "end", values=(mese, prec, att, consumo, _fmt_stima(utenza, consumo)))
                        tot_anno += consumo
                        tot_anno_stima += (_stima_costo(utenza, consumo) or 0.0)
                    tot_anno_txt = _fmt_euro(tot_anno_stima) if cu_disponibile else "—"
                    tree.insert("", "end", values=(f"Tot. {anno_x}", "", "", round(tot_anno, 2), tot_anno_txt), tags=("totale_anno",))
                    grand_tot += tot_anno
                    grand_tot_stima += tot_anno_stima
                grand_tot_txt = _fmt_euro(grand_tot_stima) if cu_disponibile else "—"
                tree.insert("", "end", values=("Tot. Generale", "", "", round(grand_tot, 2), grand_tot_txt), tags=("totale_gen",))
                if utenza in form_vars:
                    fv = form_vars[utenza]
                    fv['mese_var'].set("")
                    fv['prec_var'].set("")
                    fv['att_var'].set("")
                    fv['consumo_var'].set("")
                    fv['solo_consumo_var'].set(False)
                    aggiorna_stato_campi(utenza)
        else:
            modalita_corrente["tutti"] = False
            modalita_corrente["anno"] = anno_sel
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
                    self.trees[utenza].insert("", "end", values=(mese, float(prec), float(att), float(consumo), _fmt_stima(utenza, consumo)))
                if utenza in form_vars:
                    fv = form_vars[utenza]
                    fv['mese_var'].set("")
                    fv['prec_var'].set("")
                    fv['att_var'].set("")
                    fv['consumo_var'].set("")
                    fv['solo_consumo_var'].set(False)
                    aggiorna_stato_campi(utenza)
        try:
            disegna_grafico()
        except Exception:
            pass

    top_controls = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    top_controls.pack(fill="x", pady=(0, 6))
    img_menu_top = self.icone_gui.get("tools")
    btn_menu_top = ttk.Label(top_controls, compound="left", image=img_menu_top, text=" Menu" if img_menu_top else "☰ Menu", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
    btn_menu_top.pack(side=tk.LEFT, padx=(10, 0))
    btn_menu_top.bind("<Button-1>", lambda e: apri_menu_popup(btn_menu_top))

    centro_controls = tk.Frame(top_controls, bg=self.COLOR_TOPLEVEL)
    centro_controls.pack(side=tk.LEFT, expand=True, fill="both")
    contenuto_controls = tk.Frame(centro_controls, bg=self.COLOR_TOPLEVEL)
    contenuto_controls.pack()

    tk.Label(contenuto_controls, text="Gestione Consumi Utenze", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR, font=("Arial", 14, "bold")).pack(side=tk.LEFT, padx=(0, 25))
    tk.Label(contenuto_controls, text="Anno: ", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR).pack(side=tk.LEFT)
    anno_var = tk.StringVar(value=anno_corrente)
    anno_cb = ttk.Combobox(contenuto_controls, values=["Tutti"] + anni, textvariable=anno_var, style="Border.TCombobox", state="readonly", width=8)
    anno_cb.pack(side=tk.LEFT)
    def reset_anno():
        anno_var.set(anno_corrente)
    img_reset_anno = self.icone_gui.get("reset")
    btn_reset_anno = ttk.Label(contenuto_controls, compound="left", image=img_reset_anno, text=" Anno corrente" if img_reset_anno else " 🔄 Anno corrente", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(5, 5))
    btn_reset_anno.pack(side=tk.LEFT, padx=2)
    btn_reset_anno.bind("<Button-1>", lambda e: reset_anno())
    tk.Frame(contenuto_controls, bg=self.COLOR_TOPLEVEL, width=20).pack(side=tk.LEFT)
    img_esporta_top = self.icone_gui.get("salva")
    btn_esporta_top = ttk.Label(contenuto_controls, compound="left", image=img_esporta_top, text=" Esporta" if img_esporta_top else "💾 Esporta", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
    btn_esporta_top.pack(side=tk.LEFT, padx=4)
    btn_esporta_top.bind("<Button-1>", lambda e: esporta_preview())
    img_chiudi_top = self.icone_gui.get("chiudi")
    btn_chiudi_top = ttk.Label(contenuto_controls, compound="left", image=img_chiudi_top, text=" Chiudi" if img_chiudi_top else "Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
    btn_chiudi_top.pack(side=tk.LEFT, padx=7)
    btn_chiudi_top.bind("<Button-1>", lambda e: chiudi())
    anno_var.trace_add("write", cambia_anno)

    main_frame = ttk.Frame(win)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=18, pady=6)
    colori = {"Acqua": "#ccefff", "Luce": "#fff9cc", "Gas": "#ffe0cc"}
    colori_grafico = {"Acqua": "#0d8ecf", "Luce": "#e6ac00", "Gas": "#e2570c"}
    self.trees = {}
    anag_entries = {}
    form_vars = {}
    ai_status_labels = {}

    def _get_costo_unitario(utenza):
        raw = anagrafiche.get(utenza, {}).get("Costo Unitario", "")
        if raw in (None, ""):
            return None
        try:
            return float(str(raw).strip().replace(",", "."))
        except (ValueError, TypeError):
            return None

    def _stima_costo(utenza, consumo):
        cu = _get_costo_unitario(utenza)
        if cu is None:
            return None
        try:
            return float(consumo) * cu
        except (ValueError, TypeError):
            return None

    def _fmt_stima(utenza, consumo):
        val = _stima_costo(utenza, consumo)
        return f"{val:.2f} €" if val is not None else "—"

    def _fmt_euro(val):
        return f"{val:.2f} €" if val is not None else "—"

    def aggiorna_colonna_stima(utenza):
        tree = self.trees.get(utenza)
        if not tree:
            return
        for iid in tree.get_children():
            tags = tree.item(iid, "tags")
            if "totale_anno" in tags or "totale_gen" in tags:
                continue
            vals = list(tree.item(iid)["values"])
            if len(vals) < 4:
                continue
            try:
                consumo_v = float(vals[3])
            except (ValueError, TypeError):
                continue
            tree.item(iid, values=(vals[0], vals[1], vals[2], vals[3], _fmt_stima(utenza, consumo_v)))

    def _testo_storico(utenza):
        storico = anagrafiche.get(utenza, {}).get("_storico_fatture", [])
        if not storico:
            return "Nessuna fattura analizzata finora.\nTrascina un PDF/foto per iniziare."
        righe = [f"Storico fatture ({len(storico)}/3):"]
        valori_cu = []
        for rec in storico:
            cu = rec.get("costo_unitario")
            if cu is not None:
                valori_cu.append(cu)
            data_r = rec.get("data") or "data n/d"
            cons_r = rec.get("consumo")
            unita_r = rec.get("unita") or ""
            cu_txt = f"{cu:.4f} €/{unita_r or 'unità'}" if cu is not None else "n/d"
            righe.append(f"• {data_r}: {cons_r} {unita_r} → {cu_txt}")
        if valori_cu:
            media = sum(valori_cu) / len(valori_cu)
            righe.append(f"→ Media su {len(valori_cu)} fattur{'a' if len(valori_cu)==1 else 'e'}: {media:.4f} €/unità")
        else:
            righe.append("→ Dati insufficienti per calcolare il costo unitario, verifica a mano.")
        return "\n".join(righe)

    def _applica_estrazione_fattura(utenza, dati):
        consumo   = dati.get("consumo_periodo")
        spesa     = dati.get("spesa_totale_periodo")
        unita     = dati.get("unita_misura") or ""
        quota     = dati.get("quota_fissa")
        giorni    = dati.get("giorni_periodo")
        data_fatt = dati.get("data_fattura") or datetime.datetime.now().strftime("%d-%m-%Y")
        costo_unitario_singolo = None
        try:
            if consumo not in (None, "") and spesa not in (None, "") and float(consumo) > 0:
                costo_unitario_singolo = float(spesa) / float(consumo)
        except (ValueError, TypeError):
            costo_unitario_singolo = None
        anagrafiche.setdefault(utenza, {})
        storico = anagrafiche[utenza].setdefault("_storico_fatture", [])
        storico.append({
            "data": data_fatt, "consumo": consumo, "unita": unita,
            "spesa": spesa, "quota": quota, "giorni": giorni,
            "costo_unitario": costo_unitario_singolo,
        })
        del storico[:-3]
        scrivi_db()

        valori_cu = [r["costo_unitario"] for r in storico if r.get("costo_unitario") is not None]
        costo_unitario_medio = (sum(valori_cu) / len(valori_cu)) if valori_cu else None

        entries_u = anag_entries.get(utenza, {})
        if costo_unitario_medio is not None and "Costo Unitario" in entries_u:
            entries_u["Costo Unitario"].delete(0, tk.END)
            entries_u["Costo Unitario"].insert(0, f"{costo_unitario_medio:.4f}")
        if quota not in (None, "") and "Quota Fissa" in entries_u:
            try:
                entries_u["Quota Fissa"].delete(0, tk.END)
                entries_u["Quota Fissa"].insert(0, f"{float(quota):.2f}")
            except (ValueError, TypeError):
                pass
        campi_id_estratti = {
            "Ragione sociale": dati.get("ragione_sociale"),
            "Numero contratto": dati.get("numero_contratto"),
            "Codice Cliente": dati.get("codice_cliente"),
            "Codice Utenza / Fornitura": dati.get("codice_utenza_fornitura"),
            "POD / PDR": dati.get("pod_pdr"),
            "Telefono": dati.get("telefono_assistenza"),
            "Email": dati.get("email_assistenza"),
            "Nome Offerta": dati.get("nome_offerta"),
            "Tipo Tariffa": dati.get("tipo_tariffa"),
            "Scadenza Contratto": dati.get("scadenza_contratto"),
            "Pronto Intervento": dati.get("numero_guasti"),
            "Modalita Pagamento": dati.get("modalita_pagamento"),
        }
        for campo, valore in campi_id_estratti.items():
            if valore in (None, ""):
                continue
            ent = entries_u.get(campo)
            if ent is None:
                continue
            ent.delete(0, tk.END)
            ent.insert(0, str(valore))

        if utenza in ai_status_labels and ai_status_labels[utenza].winfo_exists():
            ai_status_labels[utenza].config(text=_testo_storico(utenza))
        self.show_toast(
            f"Fattura {utenza} analizzata ({len(storico)}/3 in storico). "
            f"Premi Salva per confermare il costo unitario."
        )

    def avvia_estrazione_fattura(utenza, path):
        if not API_KEY:
            self.show_custom_warning("Configurazione AI Necessaria",
                "Il caricamento automatico della fattura richiede una chiave API Gemini (gratuita).\n\n"
                "Vai nella sezione Impostazioni e clicca sul pulsante 'Ottieni'.\n")
            return
        ext = os.path.splitext(path)[1].lower()
        mime_map = {".pdf": "application/pdf", ".png": "image/png",
                    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
        mime = mime_map.get(ext)
        if not mime:
            self.show_toast("Formato non supportato. Usa PDF o immagine (PNG/JPG/WEBP).")
            return
        if utenza in ai_status_labels and ai_status_labels[utenza].winfo_exists():
            ai_status_labels[utenza].config(text=f"⏳ Gemini sta analizzando …")

        def _run():
            dati = None
            msg_errore = None
            try:
                with open(path, "rb") as f:
                    doc_bytes = f.read()
                client = genai_client.Client(api_key=API_KEY)
                prompt = (
                    "Analizza questa bolletta/fattura di utenza domestica (acqua, luce o gas). "
                    "Restituisci SOLO un oggetto JSON, senza testo o backtick attorno, con questi campi:\n"
                    '{"consumo_periodo": numero — il consumo nel periodo fatturato SEMPRE '
                    'nell\'unità di misura del CONTATORE fisico (mc per acqua e gas, kWh per luce), '
                    'MAI in un\'altra unità di fatturazione. Esempio: se la bolletta è di GPL fatturato '
                    'in litri ma la lettura del contatore dice "Totale Consumo mc. 20,00 pari a LT. 80,00", '
                    'usa 20 (i mc), NON 80 (i litri). Se la fattura non riporta i mc ma solo i litri/kg '
                    'e non è possibile ricavare i mc, restituisci null per questo campo. '
                    'Se il documento non è una bolletta con contatore (es. gas in bombole, nessuna lettura), '
                    'usa null, '
                    '"unita_misura": "m3" oppure "kWh", '
                    '"giorni_periodo": numero di giorni coperti dalla fattura oppure null, '
                    '"spesa_totale_periodo": numero — l\'importo TOTALE dovuto per questo periodo '
                    'fatturato, IVA inclusa: energia/materia prima, quota fissa/nolo contatore, '
                    'trasporto e gestione contatore, oneri di sistema, depurazione/fognatura se acqua, '
                    'imposte. In pratica il "Totale fattura"/"Totale a pagare" del documento. '
                    'ESCLUDI sempre da questo totale il canone RAI ed eventuali importi di '
                    'conguaglio/arretrato di periodi precedenti, che vanno indicati separatamente sotto, '
                    '"quota_fissa": numero — SOLO a titolo informativo, la quota fissa/nolo contatore '
                    'del periodo fatturato se indicata separatamente nel documento, altrimenti null '
                    '(NON sottrarla da spesa_totale_periodo: deve restare inclusa lì), '
                    '"canone_rai": numero o null, '
                    '"conguaglio": numero o null, '
                    '"data_fattura": "GG-MM-AAAA" o null, '
                    '"ragione_sociale": nome del fornitore/gestore (es. "Acque SpA", "Octopus Energy") o null, '
                    '"numero_contratto": numero contratto o codice contratto (es. "CODICE CONTRATTO") o null, '
                    '"codice_cliente": codice cliente (es. "CODICE CLIENTE") o null, '
                    '"codice_utenza_fornitura": codice utenza per acqua/gas oppure codice fornitura/POD per luce '
                    '(es. "CODICE UTENZA", "Codice Fornitura") o null, '
                    '"pod_pdr": codice POD (luce) o PDR (gas) o matricola contatore (acqua) o null, '
                    '"telefono_assistenza": numero verde/telefono del servizio clienti generale o null, '
                    '"email_assistenza": email di contatto/reclami del fornitore o null, '
                    '"nome_offerta": nome commerciale dell\'offerta/tariffa sottoscritta o null, '
                    '"tipo_tariffa": "Fissa" o "Variabile" se indicato, altrimenti null, '
                    '"scadenza_contratto": data o dicitura di scadenza del contratto/offerta '
                    '(es. "Tempo indeterminato", una data, o null), '
                    '"numero_guasti": numero telefonico specifico per segnalare guasti/interruzioni '
                    '(se diverso dal telefono di assistenza generale) o null, '
                    '"modalita_pagamento": metodo di pagamento indicato in fattura '
                    '(es. "Addebito diretto SDD", "PagoPA", "Bollettino postale") o null}\n'
                    "Se un valore non è presente nel documento usa null. Rispondi SOLO con il JSON."
                )
                parts = [types.Part.from_bytes(data=doc_bytes, mime_type=mime), prompt]
                response = client.models.generate_content(model=GEMINI, contents=parts)
                raw = (response.text or "").strip()
                if "```json" in raw:
                    raw = raw.split("```json")[1].split("```")[0].strip()
                elif "```" in raw:
                    raw = raw.split("```")[1].split("```")[0].strip()
                dati = json.loads(raw)
            except Exception as e:
                err = str(e)
                if "429" in err or "RESOURCE_EXHAUSTED" in err:
                    msg_errore = "Quota API Gemini esaurita. Riprova più tardi."
                elif "503" in err or "UNAVAILABLE" in err:
                    msg_errore = "Gemini non disponibile al momento. Riprova tra poco."
                else:
                    msg_errore = f"Analisi fattura fallita: {err[:120]}"

            def _fine():
                if msg_errore:
                    if utenza in ai_status_labels and ai_status_labels[utenza].winfo_exists():
                        ai_status_labels[utenza].config(text=f"⚠ {msg_errore}")
                    self.show_toast(msg_errore)
                else:
                    _applica_estrazione_fattura(utenza, dati)
            self.after(0, _fine)
        threading.Thread(target=_run, daemon=True).start()

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

    def salva_letture_utenza(utenza):
        anno_sel = anno_var.get()
        if anno_sel == "Tutti":
            return
        letture_salvate[utenza][anno_sel] = [
            tuple(self.trees[utenza].item(iid)['values'])[:4] for iid in self.trees[utenza].get_children()
        ]
        scrivi_db()

    def only_numeric_8char(val):
        if len(val) > 8:
            return False
        if val == "":
            return True
        if val.count(".") > 1:
            return False
        return all(c.isdigit() or c == "." for c in val)
    vcmd_num = (win.register(only_numeric_8char), "%P")

    def aggiorna_stato_campi(utenza):
        fv = form_vars[utenza]
        if fv['solo_consumo_var'].get():
            fv['att_entry'].config(state="disabled")
            fv['consumo_entry'].config(state="normal")
        else:
            fv['att_entry'].config(state="normal")
            fv['consumo_entry'].config(state="disabled")

    def on_tree_select(utenza):
        if modalita_corrente["tutti"]:
            return
        tree = self.trees[utenza]
        sel = tree.selection()
        if not sel:
            return
        mese, prec, att, consumo = tree.item(sel[0])['values'][:4]
        fv = form_vars[utenza]
        fv['mese_var'].set(mese)
        fv['prec_var'].set(f"{float(prec):.2f}")
        fv['att_var'].set(f"{float(att):.2f}")
        fv['consumo_var'].set(f"{float(consumo):.2f}")
        fv['solo_consumo_var'].set(False)
        aggiorna_stato_campi(utenza)

    def applica_modifica(utenza):
        if modalita_corrente["tutti"]:
            self.show_toast("Seleziona un anno specifico per modificare le letture.")
            return
        tree = self.trees[utenza]
        sel = tree.selection()
        if not sel:
            self.show_toast("Seleziona un mese dalla tabella.")
            return
        selected = sel[0]
        items = tree.get_children()
        idx = items.index(selected)
        fv = form_vars[utenza]
        mese = fv['mese_var'].get()
        try:
            prec = float(fv['prec_var'].get().strip() or 0)
        except ValueError:
            self.show_custom_warning("Errore", "Valore lettura precedente non valido.")
            return
        if fv['solo_consumo_var'].get():
            try:
                consumo = float(fv['consumo_var'].get().strip() or 0)
            except ValueError:
                self.show_custom_warning("Errore", "Valore consumo non valido.")
                return
            att = round(prec + consumo, 2)
        else:
            try:
                att = float(fv['att_var'].get().strip() or 0)
            except ValueError:
                self.show_custom_warning("Errore", "Valore lettura attuale non valido.")
                return
            if att < prec:
                if not self.show_custom_askyesno(
                    "Conferma Forzatura",
                    "La lettura attuale è minore della precedente.\nVuoi forzare comunque l'inserimento?"
                ):
                    return
            consumo = round(max(0.0, att - prec), 2)
        tree.item(selected, values=(mese, prec, att, consumo, _fmt_stima(utenza, consumo)))
        if idx + 1 < len(items) and not fv['solo_consumo_var'].get():
            next_mese, _, next_att = tree.item(items[idx + 1])['values'][:3]
            next_att_f = float(next_att)
            next_cons = round(max(0.0, next_att_f - att), 2)
            tree.item(items[idx + 1], values=(next_mese, att, next_att_f, next_cons, _fmt_stima(utenza, next_cons)))
        salva_letture_utenza(utenza)
        fv['prec_var'].set(f"{prec:.2f}")
        fv['att_var'].set(f"{att:.2f}")
        fv['consumo_var'].set(f"{consumo:.2f}")
        self.show_toast(f"Lettura {utenza} - {mese} aggiornata.")
        try:
            disegna_grafico()
        except Exception:
            pass

    notebook = ttk.Notebook(main_frame)
    notebook.pack(fill="both", expand=True)

    def salva_dati(u):
        for field, ent in anag_entries[u].items():
            if field == "Note":
                anagrafiche[u][field] = ent.get("1.0", "end-1c")
            else:
                anagrafiche[u][field] = ent.get()
        scrivi_db()
        aggiorna_colonna_stima(u)
        self.show_toast(f"Dati anagrafici {u} salvati.")

    tab_anagrafica = ttk.Frame(notebook)
    img_tab_anagrafica = self.icone_gui.get("anagrafica")
    if img_tab_anagrafica:
        notebook.add(tab_anagrafica, image=img_tab_anagrafica, text=" Anagrafica", compound="left")
    else:
        notebook.add(tab_anagrafica, text="📋 Anagrafica")
    anagrafica_notebook = ttk.Notebook(tab_anagrafica)
    anagrafica_notebook.pack(fill="both", expand=True, padx=4, pady=4)

    for utenza in utenze:
        tab = ttk.Frame(anagrafica_notebook)
        icon_key_utenza = {"Acqua": "acqua", "Luce": "luce", "Gas": "gas"}.get(utenza)
        img_tab_utenza = self.icone_gui.get(icon_key_utenza)
        emoji_utenza = '💧' if utenza == 'Acqua' else '💡' if utenza == 'Luce' else '🔥'
        if img_tab_utenza:
            anagrafica_notebook.add(tab, image=img_tab_utenza, text=f" {utenza}", compound="left")
        else:
            anagrafica_notebook.add(tab, text=f"{emoji_utenza} {utenza}")
        colore_bg = colori[utenza]
        frame = ttk.Frame(tab, relief="flat", borderwidth=0)
        frame.pack(fill="both", expand=True, padx=8, pady=8)
        anag_frame = ttk.LabelFrame(frame, text="Dati Anagrafici & Contatti Direct", style="RedBold.TLabelframe")
        anag_frame.pack(fill="x", padx=8, pady=(8, 4))
        anag_frame.grid_columnconfigure(3, weight=1)
        anag_frame.grid_columnconfigure(4, weight=0)

        anag_entries[utenza] = {}
        campi_principali = [
                ("Ragione sociale", 35),
                ("Telefono", 35),
                ("Email", 35),
                ("Numero contratto", 35),
                ("Codice Cliente", 35),
                ("Codice Utenza / Fornitura", 35),
                ("POD / PDR", 35)
        ]

        for row, (label, width) in enumerate(campi_principali):

                p_bottom = 30 if label == "POD / PDR" else 2
                tk.Label(anag_frame, text=label+":", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER, font=("Arial", 9, "bold")).grid(row=row, column=0, sticky="e", padx=5, pady=(2, p_bottom))
                ent = ttk.Entry(anag_frame, width=width, style="Border.TEntry")
                ent.grid(row=row, column=1, sticky="w", padx=5, pady=(2, p_bottom))
                ent.insert(0, anagrafiche[utenza].get(label, ""))
                anag_entries[utenza][label] = ent

        tk.Label(anag_frame, text="Note:", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER, font=("Arial", 9, "bold")).grid(row=0, column=2, sticky="ne", padx=5, pady=2)
        note_container = tk.Frame(anag_frame, bg=self.COLOR_WIDGET_BG)
        note_container.grid(row=0, column=3, rowspan=10, sticky="nsew", padx=5, pady=2)
        note_scrollbar = ttk.Scrollbar(note_container, orient=tk.VERTICAL, style="Vertical.TScrollbar")
        note_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        note_txt = tk.Text(
                note_container,
                width=50,
                height=8,
                wrap="word",
                bg=self.COLOR_WIDGET_BG,
                fg=self.TEXT_COLOR,
                insertbackground=self.TEXT_COLOR,
                relief=tk.FLAT,
                highlightthickness=1,
                highlightbackground=self.COLOR_HEADER,
                highlightcolor=self.COLOR_HEADER,   
                yscrollcommand=note_scrollbar.set
        )
        note_txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        note_scrollbar.config(command=note_txt.yview)
        note_txt.insert("1.0", anagrafiche[utenza].get("Note", ""))
        anag_entries[utenza]["Note"] = note_txt

        btns = tk.Frame(anag_frame, bg=self.COLOR_WIDGET_BG)
        btns.grid(row=0, column=4, rowspan=10, sticky="n", padx=(5, 10), pady=2)
        img_salva_u = self.icone_gui.get("salva")
        btn_salva_u = ttk.Label(
                btns,
                compound="left",
                image=img_salva_u,
                text=" Salva" if img_salva_u else "Salva",
                background=self.COLOR_WIDGET_BG,
                foreground=self.TEXT_COLOR,
                cursor="hand2",
                padding=(10, 5),
                width=10,
                anchor="center"
        )
        btn_salva_u.image = img_salva_u
        btn_salva_u.pack(pady=(0, 5))
        btn_salva_u.bind("<Button-1>", lambda e, u=utenza: salva_dati(u))

        bottom_container = tk.Frame(frame, bg=self.COLOR_WIDGET_BG)
        bottom_container.pack(fill="both", expand=True, padx=8, pady=(4, 8))
        bottom_container.grid_columnconfigure(0, weight=1)
        bottom_container.grid_columnconfigure(1, weight=1)
        bottom_container.grid_columnconfigure(2, weight=1)
        bottom_container.grid_rowconfigure(0, weight=1)

        left_frame = ttk.LabelFrame(bottom_container, text="Offerta & Dati Tecnici", style="RedBold.TLabelframe")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 4), pady=0)
        left_frame.grid_columnconfigure(1, weight=1)

        campi_left = [
                ("Nome Offerta", "Nome Offerta"),
                ("Tipo Tariffa (Fissa/Var.)", "Tipo Tariffa"),
                ("Costo Unitario tutto incluso (€/Unità)", "Costo Unitario"),
                ("Quota Fissa (info, non nel calcolo)", "Quota Fissa"),
                ("Scadenza Contratto", "Scadenza Contratto"),
        ]

        for row, (label_text, key) in enumerate(campi_left):
                tk.Label(left_frame, text=label_text+":", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER, font=("Arial", 9, "bold")).grid(row=row, column=0, sticky="e", padx=5, pady=4)
                ent = ttk.Entry(left_frame, style="Border.TEntry")
                ent.grid(row=row, column=1, sticky="ew", padx=5, pady=4)
                ent.insert(0, anagrafiche[utenza].get(key, ""))
                anag_entries[utenza][key] = ent

        right_frame = ttk.LabelFrame(bottom_container, text="Assistenza & Pagamenti", style="RedBold.TLabelframe")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=4, pady=0)
        right_frame.grid_columnconfigure(1, weight=1)

        campi_right = [
                ("Pronto Intervento / Guasti", "Pronto Intervento"),
                ("Modalità Pagamento", "Modalita Pagamento"),
                ("IBAN Addebito Direct Debit", "IBAN"),
        ]

        for row, (label_text, key) in enumerate(campi_right):
                tk.Label(right_frame, text=label_text+":", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER, font=("Arial", 9, "bold")).grid(row=row, column=0, sticky="e", padx=5, pady=4)
                ent = ttk.Entry(right_frame, style="Border.TEntry")
                ent.grid(row=row, column=1, sticky="ew", padx=5, pady=4)
                ent.insert(0, anagrafiche[utenza].get(key, ""))
                anag_entries[utenza][key] = ent

        ai_frame = ttk.LabelFrame(bottom_container, text="Carica Fattura (AI)", style="RedBold.TLabelframe")
        ai_frame.grid(row=0, column=2, sticky="nsew", padx=(4, 0), pady=0)
        ai_frame.grid_columnconfigure(0, weight=1)

        drop_txt = ("📎 Trascina qui il PDF/foto\ndella fattura, oppure clicca\nper selezionarla."
                    if _HAS_DND else
                    "📎 Clicca per selezionare\nil PDF/foto della fattura.")
        drop_zone = tk.Label(ai_frame, text=drop_txt, bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
                              font=("Arial", 9), justify="center", cursor="hand2",
                              relief="groove", borderwidth=2, padx=8, pady=16, width=30)
        drop_zone.grid(row=0, column=0, sticky="ew", padx=8, pady=(10, 6))

        def _scegli_file_fattura(u=utenza):
            path = filedialog.askopenfilename(
                title="Seleziona fattura",
                filetypes=[("Documenti", "*.pdf *.png *.jpg *.jpeg *.webp"),
                           ("PDF", "*.pdf"), ("Immagini", "*.png *.jpg *.jpeg *.webp")],
                parent=win)
            if path:
                avvia_estrazione_fattura(u, path)
        drop_zone.bind("<Button-1>", lambda e, u=utenza: _scegli_file_fattura(u))

        if _HAS_DND:
            def _on_drop_fattura(event, u=utenza):
                raw = event.data.strip()
                if raw.startswith("{") and raw.endswith("}"):
                    raw = raw[1:-1]
                paths_d = [p.strip("{}") for p in raw.split("} {") if p.strip()]
                if not paths_d:
                    return
                p0 = paths_d[0]
                if os.path.splitext(p0)[1].lower() not in (".pdf", ".png", ".jpg", ".jpeg", ".webp"):
                    self.show_toast("Formato non supportato. Usa PDF o immagine.")
                    return
                avvia_estrazione_fattura(u, p0)
            try:
                drop_zone.drop_target_register(_DND_FILES)
                drop_zone.dnd_bind("<<Drop>>", _on_drop_fattura)
            except Exception:
                pass

        status_lbl = tk.Label(ai_frame, text=_testo_storico(utenza),
                               bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR, font=("Arial", 8),
                               justify="left", wraplength=280, anchor="nw", width=34)
        status_lbl.grid(row=1, column=0, sticky="new", padx=8, pady=(0, 10))
        ai_status_labels[utenza] = status_lbl

        def _azzera_anagrafica(u=utenza):
            if not self.show_custom_askyesno(
                "Azzera Anagrafica",
                f"Vuoi svuotare TUTTI i dati anagrafici di {u} ?\n"
                f"(contatti, offerta, costi e storico fatture)\n\n"
                f"Le letture dei consumi mensili (Smc/kWh) NON vengono toccate."
            ):
                return
            for campo, ent in anag_entries[u].items():
                if campo == "Note":
                    ent.delete("1.0", tk.END)
                else:
                    ent.delete(0, tk.END)
            anagrafiche[u] = anagrafica_vuota()
            for campo in anag_entries[u]:
                if campo not in anagrafiche[u]:
                    anagrafiche[u][campo] = ""
            scrivi_db()
            if u in ai_status_labels and ai_status_labels[u].winfo_exists():
                ai_status_labels[u].config(text=_testo_storico(u))
            aggiorna_colonna_stima(u)
            self.show_toast(f"Anagrafica {u} azzerata.")

        btn_azzera_anagrafica = tk.Label(ai_frame, text="🗑️ Azzera anagrafica", bg=self.COLOR_WIDGET_BG,
                                          fg=self.COLOR_HEADER, font=("Arial", 8, "underline"), cursor="hand2")
        btn_azzera_anagrafica.grid(row=2, column=0, sticky="w", padx=8, pady=(0, 8))
        btn_azzera_anagrafica.bind("<Button-1>", lambda e, u=utenza: _azzera_anagrafica(u))

    tab_consumi = ttk.Frame(notebook)
    img_tab_consumi = self.icone_gui.get("report")
    if img_tab_consumi:
        notebook.insert(0, tab_consumi, image=img_tab_consumi, text=" Consumi Utenze", compound="left")
    else:
        notebook.insert(0, tab_consumi, text="📊 Consumi Utenze")
    notebook.select(tab_consumi)
    consumi_notebook = ttk.Notebook(tab_consumi)
    consumi_notebook.pack(fill="both", expand=True, padx=4, pady=4)

    for utenza in utenze:
        sub_tab = ttk.Frame(consumi_notebook)
        icon_key_utenza = {"Acqua": "acqua", "Luce": "luce", "Gas": "gas"}.get(utenza)
        img_tab_utenza = self.icone_gui.get(icon_key_utenza)
        emoji_utenza = '💧' if utenza == 'Acqua' else '💡' if utenza == 'Luce' else '🔥'
        if img_tab_utenza:
            consumi_notebook.add(sub_tab, image=img_tab_utenza, text=f" {utenza}", compound="left")
        else:
            consumi_notebook.add(sub_tab, text=f"{emoji_utenza} {utenza}")
        colore_bg = colori[utenza]
        frame = ttk.Frame(sub_tab, relief="flat", borderwidth=0)
        frame.pack(fill="both", expand=True, padx=8, pady=8)
        tree_container = tk.Frame(frame, bg=self.COLOR_WIDGET_BG)
        tree_container.pack(padx=8, pady=(8, 4), fill="both", expand=True)
        tree = ttk.Treeview(tree_container, columns=("Mese", "Prec", "Att", "Consumo", "Stima"), show="headings", height=10, selectmode='browse')
        for col in ("Mese", "Prec", "Att", "Consumo", "Stima"):
                tree.column(col, anchor="center", width=90 if col == "Stima" else 80)
        vsb_tree = ttk.Scrollbar(tree_container, orient="vertical", style="Vertical.TScrollbar", command=tree.yview)
        tree.configure(yscrollcommand=vsb_tree.set)
        vsb_tree.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)
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
                tree.insert("", "end", values=(mese, float(prec), float(att), float(consumo), _fmt_stima(utenza, consumo)))
        self.trees[utenza] = tree
        intestazioni = {"Stima": "Stima €"}
        for col in ("Mese", "Prec", "Att", "Consumo", "Stima"):
            tree.heading(col, text=intestazioni.get(col, col), command=lambda c=col, t=tree: self.treeview_sort_column(t, c, False))
        tree.bind("<<TreeviewSelect>>", lambda event, utenza=utenza: on_tree_select(utenza))
        modifica_lf = ttk.LabelFrame(frame, text="Modifica Lettura Mensile", style="RedBold.TLabelframe")
        modifica_lf.pack(fill="x", padx=8, pady=(0, 8))
        riga_mod = tk.Frame(modifica_lf, bg=self.COLOR_WIDGET_BG)
        riga_mod.pack(fill="x", padx=6, pady=6)
        mese_var = tk.StringVar()
        prec_var = tk.StringVar()
        att_var = tk.StringVar()
        consumo_var = tk.StringVar()
        solo_consumo_var = tk.BooleanVar(value=False)
        tk.Label(riga_mod, text="Mese:", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
        tk.Label(riga_mod, textvariable=mese_var, bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR, font=("Arial", 9, "bold"), width=7, anchor="w").pack(side=tk.LEFT, padx=(0, 12))
        tk.Label(riga_mod, text="Lettura Prec.:", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
        ent_prec = ttk.Entry(riga_mod, textvariable=prec_var, width=10, style="Border.TEntry", validate="key", validatecommand=vcmd_num)
        ent_prec.pack(side=tk.LEFT, padx=(0, 12))
        tk.Label(riga_mod, text="Lettura Att.:", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
        ent_att = ttk.Entry(riga_mod, textvariable=att_var, width=10, style="Border.TEntry", validate="key", validatecommand=vcmd_num)
        ent_att.pack(side=tk.LEFT, padx=(0, 12))
        tk.Label(riga_mod, text="Consumo:", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))
        ent_consumo = ttk.Entry(riga_mod, textvariable=consumo_var, width=10, style="Border.TEntry", validate="key", validatecommand=vcmd_num, state="disabled")
        ent_consumo.pack(side=tk.LEFT, padx=(0, 12))
        form_vars[utenza] = {
            'mese_var': mese_var, 'prec_var': prec_var, 'att_var': att_var, 'consumo_var': consumo_var,
            'solo_consumo_var': solo_consumo_var, 'att_entry': ent_att, 'consumo_entry': ent_consumo
        }
        chk_solo = ttk.Checkbutton(riga_mod, text="Inserisci solo Consumo", variable=solo_consumo_var, command=lambda u=utenza: aggiorna_stato_campi(u))
        chk_solo.pack(side=tk.LEFT, padx=(0, 12))
        img_mod_riga = self.icone_gui.get("salva")
        btn_applica = ttk.Label(riga_mod, compound="left", image=img_mod_riga, text=" Salva" if img_mod_riga else "Salva", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 4))
        btn_applica.image = img_mod_riga
        btn_applica.pack(side=tk.LEFT)
        btn_applica.bind("<Button-1>", lambda e, u=utenza: applica_modifica(u))
        tk.Label(modifica_lf, text="👆 Seleziona un mese dalla tabella per caricarlo qui, poi modifica e salva.",
                 bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                 font=("Arial", 8, "italic")).pack(anchor="w", padx=6, pady=(0, 6))
    tab_grafico = ttk.Frame(consumi_notebook)
    img_tab_grafico = self.icone_gui.get("grafico_linea")
    if img_tab_grafico:
        consumi_notebook.add(tab_grafico, image=img_tab_grafico, text=" Grafico", compound="left")
    else:
        consumi_notebook.add(tab_grafico, text="📈 Grafico")
    controls_g = tk.Frame(tab_grafico, bg=self.COLOR_WIDGET_BG)
    controls_g.pack(fill="x", padx=8, pady=(8, 4))
    tk.Label(controls_g, text="Vista:", bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))
    vista_var = tk.StringVar(value="Mensile")
    vista_cb = ttk.Combobox(controls_g, values=["Mensile", "Annuale", "Totali"], textvariable=vista_var, state="readonly", style="Border.TCombobox", width=12)
    vista_cb.pack(side=tk.LEFT)
    canvas_frame_g = tk.Frame(tab_grafico, bg=self.COLOR_WIDGET_BG)
    canvas_frame_g.pack(fill="both", expand=True, padx=8, pady=(4, 8))
    hsb_g = ttk.Scrollbar(canvas_frame_g, orient="horizontal", style="Horizontal.TScrollbar")
    hsb_g.pack(side="bottom", fill="x")
    chart_canvas = tk.Canvas(canvas_frame_g, bg=self.COLOR_WIDGET_BG, highlightthickness=0, xscrollcommand=hsb_g.set)
    chart_canvas.pack(side="top", fill="both", expand=True)
    hsb_g.config(command=chart_canvas.xview)
    _tooltip_label = tk.Label(win, justify="left", bg=self.COLOR_TOOLTIP, fg=self.COLOR_TEXT_TOOLTIP,
                               font=("Consolas", 9), padx=8, pady=6,
                               highlightthickness=1, highlightbackground=self.COLOR_HIGHLIGHT)

    def _tt_hide(event=None):
        _tooltip_label.place_forget()

    def _tt_show(event, text):
        if not chart_canvas.winfo_exists():
            return
        _tooltip_label.config(text=text)
        _tooltip_label.update_idletasks()
        tw_w = _tooltip_label.winfo_reqwidth()
        tw_h = _tooltip_label.winfo_reqheight()
        c_w = chart_canvas.winfo_width()
        c_h = chart_canvas.winfo_height()
        x = event.x + 16
        y = event.y + 12
        if x + tw_w > c_w:
            x = max(0, event.x - tw_w - 12)
        if y + tw_h > c_h:
            y = max(0, event.y - tw_h - 12)
        _tooltip_label.place(in_=chart_canvas, x=x, y=y)
        _tooltip_label.lift()

    mesi_lbl_full = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]

    def _valori_mese(utenza, anno_sel, mese_str):
        riga = next((r for r in letture_salvate.get(utenza, {}).get(anno_sel, []) if r[0] == mese_str), None)
        if riga:
            return float(riga[1]), float(riga[2]), float(riga[3])
        return 0.0, 0.0, 0.0

    def _totale_anno(utenza, anno_i):
        return sum(float(r[3]) for r in letture_salvate.get(utenza, {}).get(anno_i, []))

    def _tt_mensile(utenza, mese_num, anno_sel):
        mese_str = f"{mese_num:02d}/{anno_sel}"
        prec, att, cons = _valori_mese(utenza, anno_sel, mese_str)
        return (f"{utenza} — {mesi_lbl_full[mese_num-1]} {anno_sel}\n"
                f"Lettura prec.: {prec:.2f}\n"
                f"Lettura att.:  {att:.2f}\n"
                f"Consumo:       {cons:.2f}")

    def _tt_annuale(utenza, anno_i):
        righe = letture_salvate.get(utenza, {}).get(anno_i, [])
        by_mese = {}
        for r in righe:
            try:
                mm = r[0].split("/")[0]
                by_mese[mm] = by_mese.get(mm, 0.0) + float(r[3])
            except Exception:
                pass
        corpo = "\n".join(f"  {mesi_lbl_full[m-1]}: {by_mese.get(f'{m:02d}', 0.0):.2f}" for m in range(1, 13))
        tot = sum(by_mese.get(f"{m:02d}", 0.0) for m in range(1, 13))
        return f"{utenza} — Anno {anno_i}\n{corpo}\nTotale anno:    {tot:.2f}"

    def _tt_totale(utenza, anni_presenti):
        corpo = "\n".join(f"  {a}: {_totale_anno(utenza, a):.2f}" for a in anni_presenti) or "  (nessun dato)"
        grand = sum(_totale_anno(utenza, a) for a in anni_presenti)
        return f"{utenza} — Totale complessivo\n{corpo}\nTotale completo: {grand:.2f}"

    def disegna_grafico(*args):
        if not chart_canvas.winfo_exists():
            return
        _tt_hide()
        chart_canvas.delete("all")
        chart_canvas.update_idletasks()
        c_w = chart_canvas.winfo_width() if chart_canvas.winfo_width() > 10 else 900
        c_h = chart_canvas.winfo_height() if chart_canvas.winfo_height() > 10 else 360
        CHART_LEFT, CHART_TOP, CHART_BOTTOM = 50, 34, c_h - 60
        modo = vista_var.get()
        n_series = len(utenze)
        MIN_GROUP_W, MAX_GROUP_W = 64, 190

        def max_per_utenza(dati_list):
            m = {}
            for u in utenze:
                valori = [vals[u] for _, vals in dati_list]
                m[u] = max(valori + [1.0])
            return m

        def disegna_barre(dati, tooltip_for, x_start, avail_w, ns, max_v):
            n_groups = max(len(dati), 1)
            ideal = avail_w / n_groups
            group_w = max(MIN_GROUP_W, min(ideal, MAX_GROUP_W))
            inner_pad, gap = 8, 3
            bar_w = max(9, (group_w - inner_pad * 2 - gap * (n_series - 1)) / n_series)
            for i, (label, vals) in enumerate(dati):
                gx = x_start + i * group_w + inner_pad
                for j, utenza in enumerate(utenze):
                    val = vals[utenza]
                    h = max((val / max_v[utenza]) * (CHART_BOTTOM - CHART_TOP), 3) if val > 0 else 0
                    x0 = gx + j * (bar_w + gap)
                    tag = f"bar_{ns}_{i}_{j}"
                    chart_canvas.create_rectangle(x0, CHART_BOTTOM - h, x0 + bar_w, CHART_BOTTOM,
                                                   fill=colori_grafico[utenza], outline="#333333", tags=tag)
                    tip = tooltip_for(utenza, label)
                    chart_canvas.tag_bind(tag, "<Enter>", lambda e, t=tip: _tt_show(e, t))
                    chart_canvas.tag_bind(tag, "<Leave>", _tt_hide)
                chart_canvas.create_text(gx + (group_w - inner_pad * 2) / 2, CHART_BOTTOM + 14,
                                          text=str(label), font=("Arial", 7, "bold"), fill=self.TEXT_COLOR)
            return x_start + n_groups * group_w

        if modo == "Mensile":
            anno_sel = anno_var.get()
            if anno_sel == "Tutti":
                anni_disp = anni_presenti_tutti()
                anno_sel = anni_disp[-1] if anni_disp else anno_corrente
            dati = [(mesi_lbl_full[m-1], {u: _valori_mese(u, anno_sel, f"{m:02d}/{anno_sel}")[2] for u in utenze}) for m in range(1, 13)]
            max_v = max_per_utenza(dati)
            avail_w = max(c_w - CHART_LEFT - 40, MIN_GROUP_W * len(dati))
            fine_x = disegna_barre(
                dati, lambda u, lbl: _tt_mensile(u, mesi_lbl_full.index(lbl) + 1, anno_sel),
                CHART_LEFT, avail_w, "m", max_v
            )
            total_w = fine_x + 30

        elif modo == "Annuale":
            anni_presenti = sorted({a for u in utenze for a in letture_salvate.get(u, {}).keys()}) or [anno_var.get()]
            dati = [(a, {u: _totale_anno(u, a) for u in utenze}) for a in anni_presenti]
            max_v = max_per_utenza(dati)
            avail_w = max(c_w - CHART_LEFT - 40, MIN_GROUP_W * len(dati))
            fine_x = disegna_barre(dati, lambda u, lbl: _tt_annuale(u, lbl), CHART_LEFT, avail_w, "a", max_v)
            total_w = fine_x + 30

        else:
            anni_presenti = sorted({a for u in utenze for a in letture_salvate.get(u, {}).keys()})
            dati_tot = [("Totale", {u: sum(_totale_anno(u, a) for a in anni_presenti) for u in utenze})]
            dati_anni = [(a, {u: _totale_anno(u, a) for u in utenze}) for a in anni_presenti] or [(anno_var.get(), {u: 0.0 for u in utenze})]
            max_tot_scalare = max(list(dati_tot[0][1].values()) + [1.0])
            max_tot = {u: max_tot_scalare for u in utenze}
            max_anni = max_per_utenza(dati_anni)
            avail_anni = max(c_w - CHART_LEFT - MAX_GROUP_W - 70, MIN_GROUP_W * len(dati_anni))
            fine_tot = disegna_barre(dati_tot, lambda u, lbl: _tt_totale(u, anni_presenti), CHART_LEFT, MAX_GROUP_W, "t", max_tot)
            divider_x = fine_tot + 16
            chart_canvas.create_line(divider_x, CHART_TOP - 12, divider_x, CHART_BOTTOM + 26, fill="#999999", dash=(3, 2))
            chart_canvas.create_text(divider_x + 8, CHART_TOP - 20, text="📈 Andamento annuale",
                                      anchor="w", font=("Arial", 8, "bold"), fill=self.TEXT_COLOR)
            fine_anni = disegna_barre(dati_anni, lambda u, lbl: _tt_annuale(u, lbl), divider_x + 22, avail_anni, "y", max_anni)
            total_w = fine_anni + 30

        chart_canvas.config(scrollregion=(0, 0, max(total_w, c_w), c_h))
        chart_canvas.create_line(CHART_LEFT, CHART_BOTTOM, total_w - 10, CHART_BOTTOM, fill="#AAAAAA", width=2)

        lx = CHART_LEFT
        for utenza in utenze:
            chart_canvas.create_rectangle(lx, 8, lx + 12, 20, fill=colori_grafico[utenza], outline="#333333")
            chart_canvas.create_text(lx + 16, 14, text=utenza, anchor="w", font=("Arial", 7, "bold"), fill=self.TEXT_COLOR)
            lx += 74

    _resize_job = {"id": None}

    def _on_chart_resize(event=None):
        if _resize_job["id"] is not None:
            try:
                chart_canvas.after_cancel(_resize_job["id"])
            except Exception:
                pass
        _resize_job["id"] = chart_canvas.after(120, disegna_grafico)

    vista_cb.bind("<<ComboboxSelected>>", disegna_grafico)
    chart_canvas.bind("<Configure>", _on_chart_resize)
    win.after(150, disegna_grafico)
