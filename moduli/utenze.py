#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import datetime
import threading
import tkinter as tk
from tkinter import ttk, filedialog
import pymupdf as fitz

_USI_GAS = ["Cottura + acqua calda + riscaldamento", "Cottura + acqua calda", "Solo cottura", "Non ho il gas (bombole / altro)"]
_COMUNI_CACHE = None

def _carica_comuni():
    global _COMUNI_CACHE
    if _COMUNI_CACHE is None:
        try:
            from moduli.comuni_it import COMUNI
            _COMUNI_CACHE = list(COMUNI)
        except Exception:
            _COMUNI_CACHE = []
    return _COMUNI_CACHE

def _risolvi_comune(testo):
    import difflib
    elenco = _carica_comuni()
    t = " ".join(testo.split()).casefold()
    if not t:
        return "", "Indica il comune."
    if not elenco:
        return testo.strip(), ""
    esatto = [c for c in elenco if c.casefold() == t]
    if esatto:
        return esatto[0], ""
    stesso_nome = [c for c in elenco if c.rsplit(" (", 1)[0].casefold() == t]
    if len(stesso_nome) == 1:
        return stesso_nome[0], ""
    if len(stesso_nome) > 1:
        return "", "Più comuni con questo nome: scegli dall'elenco (es. " + stesso_nome[0] + ")."
    nomi = {c.rsplit(" (", 1)[0].casefold(): c for c in elenco}
    simili = [nomi[n] for n in difflib.get_close_matches(t, list(nomi), n=3, cutoff=0.7)]
    return "", "Comune non trovato." + (" Intendevi: " + ", ".join(simili) + "?" if simili else "")

def utenze(self):
    _w = getattr(self, '_win_utenze', None)
    try:
        if _w is not None and _w.winfo_exists():
            _w.deiconify(); _w.lift(); _w.focus_force()
            return
    except Exception:
        pass
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
            except Exception:
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
        except Exception:
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

    def _boll_mese(utenza, mese):
        rec = _bollette_cache().get(utenza, {}).get(mese)
        return rec[0] if rec else None

    def _media_consumo(righe):
        validi = [r[3] for r in righe if r[3] > 0]
        return (sum(validi) / len(validi), len(validi)) if validi else (0.0, 0)

    win = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    self._win_utenze = win
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
    win.protocol("WM_DELETE_WINDOW", lambda: (chiudi_viewer_tabella(), self.after(0, self.imp_entry.focus_set), win.destroy()))
    win.deiconify()
    win.update_idletasks()
    win.minsize(larghezza, altezza)
    pass

    def mostra_guida_utenze():
        testo_consumi = (
            "💧⚡🔥 Gestione Consumi Utenze - Guida Rapida\n\n"
            "# SELEZIONE ANNO E TABELLE\n"
            "• Combo Anno: Scegli l'anno da consultare, oppure 'Tutti' per lo storico completo.\n"
            "• 🔄 (accanto alla combo): Torna rapidamente all'anno corrente.\n"
            "• Ogni utenza (Acqua/Luce/Gas) ha la propria tabella con Mese, Lettura Prec., Lettura Att., Consumo, Stima € e Bolletta €.\n"
            "• Sotto la tabella: totale, media mensile (sui mesi con consumo), stima spesa e bollette registrate.\n"
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
            "• Pulsante Esporta (in alto): apre l'anteprima del riepilogo consumi (anno selezionato o 'Tutti'), con totali, media mensile e bollette.\n"
            "• Dall'anteprima puoi: Esporta TXT, Esporta PDF oppure Stampa direttamente.\n"
        )
        testo_anagrafica = (
            "📋 Anagrafica, Costi e Fattura AI - Guida Rapida\n\n"
            "# DATI ANAGRAFICI\n"
            "• Ogni utenza ha una propria scheda: Ragione sociale, Telefono, Email, Numero contratto, Codice Cliente, Codice Utenza/Fornitura, POD/PDR, Note.\n"
            "• Premi Salva nella scheda per confermare le modifiche.\n"
            "• Azzera: svuota tutta l'anagrafica dell'utenza (contatti, offerta, costi, storico fatture). Le letture dei consumi NON vengono toccate.\n"
            "\n# OFFERTA & COSTO UNITARIO\n"
            "• Costo Unitario tutto incluso (€/Unità): se compilato, abilita la colonna 'Stima €' nelle tabelle consumi.\n"
            "• Quota Fissa: campo puramente informativo, NON entra nel calcolo della stima.\n"
            "• Se il Costo Unitario è vuoto, le stime in tabella/grafico/esportazioni mostrano '—'.\n"
            "\n# CARICA FATTURA (AI)\n"
            "• Trascina un PDF/foto della fattura nella casella, oppure clicca per selezionarlo.\n"
            "• Richiede una chiave API Gemini configurata in Impostazioni (gratuita).\n"
            "• L'IA legge la fattura ed estrae automaticamente: consumo del periodo, costo unitario stimato, dati del fornitore, codici contratto, POD/PDR, scadenze, modalità di pagamento, ecc.\n"
            "• I campi individuati vengono precompilati nella scheda: verifica i valori e premi Salva per confermarli.\n"
            "• Il Costo Unitario è la media sulle ultime 3 fatture analizzate (storico mostrato nella casella).\n"
            "• Importa auto: SÌ/NO: se attivo, l'app analizza da sola le ultime 3 fatture nuove dell'Archivio (serve la categoria bollette).\n"
        )
        testo_database = (
            "🗄️ Menu Database - Guida Rapida\n\n"
            "# 📤 Esporta Consumi\n"
            "• Salva un file JSON con tutte le letture e le anagrafiche, utile per backup o trasferimento su un altro PC.\n"
            "\n# 📥 Importa Consumi\n"
            "• Carica un file JSON esportato in precedenza, sostituendo letture e anagrafiche delle utenze presenti nel file.\n"
            "\n# 🗑️ Azzera Consumi\n"
            "• ATTENZIONE: elimina TUTTO lo storico delle letture di tutte le utenze. Viene sempre richiesta conferma.\n"
            "\n# 📊 Scarica Tabella Consumi\n"
            "• Genera un file scaricabile con la tabella dei consumi, pronta per essere condivisa o archiviata.\n"
        )
        testo_bollette = (
            "🧾 Bollette e Analisi - Guida Rapida\n\n"
            "# CATEGORIE BOLLETTE\n"
            "• Pulsante Categorie Bollette: scegli in quale categoria di spesa registri le bollette di Acqua, Luce e Gas.\n"
            "• Se usi la stessa categoria per tutte, l'app distingue le utenze dalla descrizione (acqua, luce/energia/kWh, gas/metano/GPL).\n"
            "• Senza categoria la colonna Bolletta € resta vuota e Importa auto non funziona.\n"
            "\n# COLONNA BOLLETTA E DOCUMENTI\n"
            "• Bolletta €: somma delle uscite registrate in quel mese nella categoria associata; tra parentesi il numero di spese se più di una.\n"
            "• Passa il mouse su una cella Bolletta: dopo un istante compare l'anteprima del documento archiviato.\n"
            "• Doppio clic sulla cella Bolletta: apre il documento completo, con Stampa e Salva.\n"
            "\n# ANALISI DI MERCATO (AI)\n"
            "• Chiede pochi dati sulla casa (persone, comune, mq, uso del gas, riscaldamento), che restano salvati.\n"
            "• L'IA confronta i tuoi consumi con le medie, segnala andamento e anomalie e propone azioni di risparmio sui consumi.\n"
            "• Richiede la chiave API Gemini. Il risultato si può salvare in TXT/PDF o stampare.\n"
            "\n# CONFRONTA DOCUMENTI\n"
            "• Apre il modulo di confronto bollette con l'AI.\n"
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
            testo_consumi + "\n" + testo_anagrafica + "\n" + testo_bollette + "\n" + testo_database, self.show_custom_warning))
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
        _crea_tab("Bollette e Analisi", testo_bollette, "fattura_ai")
        _crea_tab("Database", testo_database, "salva")

        guida_win.update_idletasks()
        w, h = guida_win.winfo_reqwidth(), guida_win.winfo_reqheight()
        x = win.winfo_rootx() + (win.winfo_width() // 2) - (w // 2)
        y = win.winfo_rooty() + (win.winfo_height() // 2) - (h // 2)
        guida_win.geometry(f"1000x560+{x}+{y}")
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
        pass
        self.after(0, self.imp_entry.focus_set)
    def chiudi_viewer_tabella():
        v = getattr(self, '_viewer_tabella_win', None)
        if v and v.winfo_exists():
           v.destroy()
    win.bind("<Escape>", lambda e: (chiudi_viewer_tabella(), self.after(0, self.imp_entry.focus_set), win.destroy()))

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
                pass
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

        _bollette_cache(forza=True)
        grand_tot = {u: 0.0 for u in utenze}
        grand_tot_stima = {u: 0.0 for u in utenze}
        grand_boll = {u: 0.0 for u in utenze}
        grand_cons_validi = {u: [] for u in utenze}
        cat_ok = {u: bool(_categoria_bollette(u)) for u in utenze}
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
            media_riga = f"{'Media mens':<10}"
            boll_riga = f"{'Bollette':<10}"
            for utenza in utenze:
                righe_u = righe_per_utenza[utenza]
                media_u, n_u = _media_consumo(righe_u)
                grand_cons_validi[utenza].extend(r[3] for r in righe_u if r[3] > 0)
                tot_b = sum((_boll_mese(utenza, r[0]) or 0.0) for r in righe_u)
                grand_boll[utenza] += tot_b
                media_riga += f"{'':8}{'':10}{media_u:10.2f}{('(' + str(n_u) + ' mesi)'):>12}  "
                boll_riga += f"{'':8}{'':10}{'':10}{(f'{tot_b:12.2f}' if cat_ok[utenza] else f'{chr(8212):>12}')}  "
            txt.insert(tk.END, media_riga + "\n")
            txt.insert(tk.END, boll_riga + "\n")
            if any(cat_ok.values()):
                txt.insert(tk.END, "\nBollette registrate per mese (€)\n")
                txt.insert(tk.END, f"{'':<10}" + "".join(f"{u:>14}" for u in utenze) + "\n")
                for i in range(12):
                    mese = righe_per_utenza[utenze[0]][i][0]
                    valori = [_boll_mese(u, mese) for u in utenze]
                    if not any(v is not None for v in valori):
                        continue
                    riga_b = f"{mese:<10}"
                    for v in valori:
                        riga_b += f"{(f'{v:.2f}' if v is not None else chr(8212)):>14}"
                    txt.insert(tk.END, riga_b + "\n")
        if tutti_anni and len(anni_x) > 1:
            txt.insert(tk.END, "\n" + "═" * len(header) + "\n")
            gtot_riga = f"{'Tot.Compl.':<10}"
            for utenza in utenze:
                stima_g_txt = f"{grand_tot_stima[utenza]:12.2f}" if cu_disp[utenza] else f"{'—':>12}"
                gtot_riga += f"{'':8}{'':10}{grand_tot[utenza]:10.2f}{stima_g_txt}  "
            txt.insert(tk.END, gtot_riga + "\n")
            gmedia_riga = f"{'Media mens':<10}"
            gboll_riga = f"{'Bollette':<10}"
            for utenza in utenze:
                v = grand_cons_validi[utenza]
                gm = (sum(v) / len(v)) if v else 0.0
                gmedia_riga += f"{'':8}{'':10}{gm:10.2f}{('(' + str(len(v)) + ' mesi)'):>12}  "
                gboll_riga += f"{'':8}{'':10}{'':10}{(f'{grand_boll[utenza]:12.2f}' if cat_ok[utenza] else f'{chr(8212):>12}')}  "
            txt.insert(tk.END, gmedia_riga + "\n")
            txt.insert(tk.END, gboll_riga + "\n")
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
            pg.insert_text((MARG + 450, y[0] + 11), "Bolletta €", fontsize=7.5, fontname="Helvetica-Bold")
            y[0] += 16

        _bollette_cache(forza=True)
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
                totale_boll = 0.0
                cat_pdf = bool(_categoria_bollette(utenza))
                cu_ok = _get_costo_unitario(utenza) is not None
                righe_pdf = righe_anno_export(utenza, anno_x)
                media_pdf, n_mesi_pdf = _media_consumo(righe_pdf)
                for mese, prec, att, cons in righe_pdf:
                    totale += cons
                    b_val = _boll_mese(utenza, mese)
                    if b_val is not None:
                        totale_boll += b_val
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
                    pg.insert_text((MARG + 450, y[0] + 11), (f"{b_val:.2f}" if b_val is not None else ("—" if cat_pdf else "")), fontsize=7.5, fontname="Helvetica")
                    y[0] += 14
                if y[0] > H - 65:
                    pg = doc.new_page(width=W, height=H)
                    intestazione_pagina(pg, f"Anno {anno_x} (segue)" if tutti_anni else None)
                totale_txt = f"Totale {utenza}: {totale:.2f}"
                if cu_ok:
                    totale_txt += f"   —   Stima spesa: {totale_stima:.2f} €"
                pg.insert_text((MARG + 4, y[0] + 11), totale_txt, fontsize=8, fontname="Helvetica-Bold", color=colori_pdf[utenza])
                y[0] += 13
                riga2 = f"Media mensile consumo: {media_pdf:.2f} ({n_mesi_pdf} mesi)"
                if cat_pdf:
                    riga2 += f"   —   Bollette registrate: {totale_boll:.2f} €"
                pg.insert_text((MARG + 4, y[0] + 11), riga2, fontsize=8, fontname="Helvetica-Bold", color=colori_pdf[utenza])
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

    def _bottone_label(parent, chiave, testo, emoji, cmd, side=tk.LEFT, padx=4, padding=(10, 5), width=None):
        img = self.icone_gui.get(chiave)
        b = ttk.Label(parent, compound="left", image=img, text=f" {testo}" if img else f"{emoji} {testo}",
                      background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=padding)
        if width:
            b.config(width=width, anchor="w")
        b.image = img
        b.pack(side=side, padx=padx)
        b.bind("<Button-1>", lambda e: cmd())
        return b

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
    _bottone_label(contenuto_controls, "fattura_ai", "Analisi di Mercato", "🔎", lambda: _apri_analisi_mercato())
    _bottone_label(contenuto_controls, "fattura_ai", "Confronta Documenti", "📑", lambda: _apri_confronta_bollette())
    _bottone_label(contenuto_controls, "anagrafica", "Categorie Bollette", "🏷️", lambda: _apri_dialogo_categorie_bollette())
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
    toggle_labels = {}

    def _import_auto_attivo(utenza):
        return bool(anagrafiche.get(utenza, {}).get("_import_auto"))

    def _aggiorna_toggle(utenza):
        lbl = toggle_labels.get(utenza)
        if lbl is None or not lbl.winfo_exists():
            return
        on = _import_auto_attivo(utenza)
        t = f"Importa auto: {'SÌ' if on else 'NO'}"
        lbl.config(text=f" {t}" if getattr(lbl, "image", None) else f"⚡ {t}",
                   foreground="#1b7a2b" if on else self.TEXT_COLOR)

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

    def _applica_estrazione_fattura(utenza, dati, silenzioso=False):
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
        if not silenzioso:
            self.show_toast(
                f"Fattura {utenza} analizzata ({len(storico)}/3 in storico). "
                f"Premi Salva per confermare il costo unitario."
            )

    def _msg_errore_gemini(e):
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err:
            return "Quota API Gemini esaurita. Riprova più tardi."
        if "503" in err or "UNAVAILABLE" in err:
            return "Gemini non disponibile al momento. Riprova tra poco."
        return f"Analisi fattura fallita: {err[:120]}"

    def _chiama_gemini_fattura(path):
        mime = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg", ".webp": "image/webp"}[os.path.splitext(path)[1].lower()]
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
        return dati

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
            ai_status_labels[utenza].config(text="⏳ Gemini sta analizzando …")

        def _run():
            dati = None
            msg_errore = None
            try:
                dati = _chiama_gemini_fattura(path)
            except Exception as e:
                msg_errore = _msg_errore_gemini(e)

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
                pass
                win.destroy()
                self.utenze()
                self.show_custom_warning("Importazione riuscita", "Utenze importate correttamente!")
            except Exception as e:
                self.show_custom_warning("Errore", f"Errore durante l'importazione:\n{e}")

    def esporta_letture_data(UTENZE_DB):
        now = datetime.date.today()
        default_dir = EXP_DB
        default_filename = f"{now.day:02d}-{now.month:02d}-{now.year}-utenze_db.json"
        win.wm_attributes('-topmost', 1)
        file = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("File JSON", "*utenze_db.json"), ("Tutti i file", "*.*")],
            initialdir=default_dir,
            initialfile=default_filename,
            confirmoverwrite=False,
            title="Esporta utenze",
            parent=win,
        )
        win.wm_attributes('-topmost', 0)
        if file:
            if os.path.exists(file):
                conferma = self.show_custom_askyesno(
                    "Sovrascrivere file?",
                    f"Il file '{os.path.basename(file)}' \nesiste già. Vuoi sovrascriverlo?"
                )
                if not conferma:
                    return
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

    def salva_dati(u, silenzioso=False):
        for field, ent in anag_entries[u].items():
            if field == "Note":
                anagrafiche[u][field] = ent.get("1.0", "end-1c")
            else:
                anagrafiche[u][field] = ent.get()
        scrivi_db()
        aggiorna_colonna_stima(u)
        if not silenzioso:
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
        ai_frame.grid_rowconfigure(2, weight=1)

        img_drop = self.icone_gui.get("report")
        pref_drop = "" if img_drop else "📎 "
        drop_txt = (pref_drop + "Trascina qui il PDF/foto\ndella fattura, oppure clicca\nper selezionarla."
                    if _HAS_DND else
                    pref_drop + "Clicca per selezionare\nil PDF/foto della fattura.")
        drop_zone = tk.Label(ai_frame, text=drop_txt, image=img_drop, compound="top",
                              bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER,
                              font=("Arial", 9), justify="center", cursor="hand2",
                              relief="groove", borderwidth=2, padx=8, pady=8, width=230 if img_drop else 30)
        drop_zone.image = img_drop
        drop_zone.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))

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
        status_lbl.grid(row=2, column=0, sticky="new", padx=8, pady=(0, 6))
        ai_status_labels[utenza] = status_lbl

        riga_btn_ai = tk.Frame(ai_frame, bg=self.COLOR_WIDGET_BG)
        riga_btn_ai.grid(row=1, column=0, sticky="w", padx=8, pady=(0, 4))
        toggle_labels[utenza] = _bottone_label(riga_btn_ai, "fattura_ai", "Importa auto: NO", "⚡",
                                               lambda u=utenza: _toggle_import_auto(u),
                                               side=tk.LEFT, padx=(0, 6), padding=(8, 4), width=17)
        _aggiorna_toggle(utenza)

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
            _aggiorna_toggle(u)
            if u in ai_status_labels and ai_status_labels[u].winfo_exists():
                ai_status_labels[u].config(text=_testo_storico(u))
            aggiorna_colonna_stima(u)
            self.show_toast(f"Anagrafica {u} azzerata.")

        _bottone_label(riga_btn_ai, "reset", "Azzera", "🗑️", lambda u=utenza: _azzera_anagrafica(u),
                       side=tk.LEFT, padx=0, padding=(8, 4))

    tab_consumi = ttk.Frame(notebook)
    img_tab_consumi = self.icone_gui.get("report")
    if img_tab_consumi:
        notebook.insert(0, tab_consumi, image=img_tab_consumi, text=" Consumi Utenze", compound="left")
    else:
        notebook.insert(0, tab_consumi, text="📊 Consumi Utenze")
    notebook.select(tab_consumi)
    consumi_notebook = ttk.Notebook(tab_consumi)
    consumi_notebook.pack(fill="both", expand=True, padx=4, pady=4)

    totali_lbl = {}
    for utenza in utenze:
        sub_tab = ttk.Frame(consumi_notebook)
        icon_key_utenza = {"Acqua": "acqua", "Luce": "luce", "Gas": "gas"}.get(utenza)
        img_tab_utenza = self.icone_gui.get(icon_key_utenza)
        emoji_utenza = '💧' if utenza == 'Acqua' else '💡' if utenza == 'Luce' else '🔥'
        if img_tab_utenza:
            consumi_notebook.add(sub_tab, image=img_tab_utenza, text=f" {utenza}", compound="left")
        else:
            consumi_notebook.add(sub_tab, text=f"{emoji_utenza} {utenza}")
        frame = ttk.Frame(sub_tab, relief="flat", borderwidth=0)
        frame.pack(fill="both", expand=True, padx=8, pady=8)
        tree_container = tk.Frame(frame, bg=self.COLOR_WIDGET_BG)
        tree_container.pack(padx=8, pady=(8, 4), fill="both", expand=True)
        tree = ttk.Treeview(tree_container, columns=("Mese", "Prec", "Att", "Consumo", "Stima", "Bolletta"), show="headings", height=10, selectmode='browse')
        for col in ("Mese", "Prec", "Att", "Consumo", "Stima", "Bolletta"):
                tree.column(col, anchor="center", width=110 if col == "Bolletta" else (90 if col == "Stima" else 80))
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
        intestazioni = {"Stima": "Stima €", "Bolletta": "Bolletta €"}
        for col in ("Mese", "Prec", "Att", "Consumo", "Stima", "Bolletta"):
            tree.heading(col, text=intestazioni.get(col, col), command=lambda c=col, t=tree: self.treeview_sort_column(t, c, False))
        tree.bind("<<TreeviewSelect>>", lambda event, utenza=utenza: on_tree_select(utenza))
        totali_lbl[utenza] = tk.Label(frame, text="", bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                                      font=("Arial", 10, "bold"), anchor="w", padx=8, pady=4)
        totali_lbl[utenza].pack(fill="x", padx=8, pady=(0, 6))
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
    _UNITA_TOT = {"Acqua": "m³", "Luce": "kWh", "Gas": "Smc"}
    _KEYWORDS_UTENZA = {
        "Acqua": ("acqua", "idric", "acquedott"),
        "Luce":  ("luce", "elettric", "energia", "kwh"),
        "Gas":   ("gas", "metano", "gpl"),
    }
    _cache_bollette = {"ts": 0.0, "dati": {}}

    def _categoria_bollette(utenza):
        return (anagrafiche.get(utenza, {}).get("_categoria_bollette") or "").strip()

    def _calcola_bollette():
        out = {u: {} for u in utenze}
        for utenza in utenze:
            cat = _categoria_bollette(utenza)
            if not cat:
                continue
            condivisa = sum(1 for u in utenze if _categoria_bollette(u) == cat) > 1
            for d, voci in list(getattr(self, "spese", {}).items()):
                try:
                    chiave = f"{d.month:02d}/{d.year}"
                except AttributeError:
                    continue
                for v in voci:
                    try:
                        if v[0] != cat or v[3] != "Uscita":
                            continue
                        if condivisa:
                            descr = str(v[1]).lower()
                            match = [u for u, kws in _KEYWORDS_UTENZA.items() if any(k in descr for k in kws)]
                            if match != [utenza]:
                                continue
                        rec = out[utenza].setdefault(chiave, [0.0, 0, set()])
                        rec[0] += float(v[2])
                        rec[1] += 1
                        rec[2].add(str(v[1]).lower())
                    except (ValueError, TypeError, IndexError):
                        continue
        return out

    def _bollette_cache(forza=False):
        import time as _t
        if forza or _t.time() - _cache_bollette["ts"] > 3:
            _cache_bollette["dati"] = _calcola_bollette()
            _cache_bollette["ts"] = _t.time()
        return _cache_bollette["dati"]

    def _fmt_num_it(v):
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def aggiorna_totali_consumi():
        try:
            if not win.winfo_exists():
                return
            anno_txt = anno_var.get()
            etichetta = "generale" if anno_txt == "Tutti" else anno_txt
            bollette = _bollette_cache()
            for utenza in utenze:
                tr = self.trees.get(utenza)
                lbl = totali_lbl.get(utenza)
                if tr is None or lbl is None:
                    continue
                cat = _categoria_bollette(utenza)
                per_mese = bollette.get(utenza, {})
                tot = 0.0
                tot_stima = 0.0
                tot_boll = 0.0
                n_mesi = 0
                boll_anno = {}
                for iid in tr.get_children():
                    if any(t.startswith("totale") for t in tr.item(iid, "tags")):
                        continue
                    vals = tr.item(iid)["values"]
                    try:
                        cons = float(vals[3])
                    except (ValueError, IndexError, TypeError):
                        continue
                    tot += cons
                    if cons > 0:
                        n_mesi += 1
                    tot_stima += (_stima_costo(utenza, cons) or 0.0)
                    mese_k = str(vals[0]).strip()
                    rec = per_mese.get(mese_k)
                    if rec:
                        tot_boll += rec[0]
                        boll_anno[mese_k[-4:]] = boll_anno.get(mese_k[-4:], 0.0) + rec[0]
                        testo_b = f"{_fmt_num_it(rec[0])} €" + (f" ({rec[1]})" if rec[1] > 1 else "")
                    else:
                        testo_b = "—" if cat else ""
                    if tr.set(iid, "Bolletta") != testo_b:
                        tr.set(iid, "Bolletta", testo_b)
                for iid in tr.get_children():
                    if not any(t.startswith("totale") for t in tr.item(iid, "tags")):
                        continue
                    etic = str(tr.item(iid)["values"][0])
                    if not cat:
                        testo_b = ""
                    elif etic.startswith("Tot. Generale"):
                        testo_b = f"{_fmt_num_it(tot_boll)} €"
                    else:
                        testo_b = f"{_fmt_num_it(boll_anno.get(etic[-4:], 0.0))} €"
                    if tr.set(iid, "Bolletta") != testo_b:
                        tr.set(iid, "Bolletta", testo_b)
                testo = f"Σ Totale {etichetta}:  {_fmt_num_it(tot)} {_UNITA_TOT.get(utenza, '')}"
                if n_mesi:
                    testo += f"   —   Media mensile: {_fmt_num_it(tot / n_mesi)} {_UNITA_TOT.get(utenza, '')} ({n_mesi} mesi)"
                if _get_costo_unitario(utenza) is not None:
                    testo += f"   —   Stima spesa: {_fmt_euro(tot_stima)}"
                if cat:
                    testo += f"   —   Bollette registrate: {_fmt_num_it(tot_boll)} €"
                if lbl.cget("text") != testo:
                    lbl.config(text=testo)
            win.after(400, aggiorna_totali_consumi)
        except tk.TclError:
            pass

    def _apri_dialogo_categorie_bollette(primo_avvio=False):
        cats = sorted(getattr(self, "categorie", []), key=lambda c: c.lower())
        if not cats:
            return
        NESSUNA = "(nessuna)"
        dlg = tk.Toplevel(win, bg=self.COLOR_TOPLEVEL)
        dlg.title("Categorie delle bollette")
        dlg.transient(win)
        dlg.resizable(False, False)
        tk.Label(dlg, bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR, justify="left", font=("Arial", 10),
                 text="In quale categoria registri le bollette?\n"
                      "Serve per mostrare accanto a ogni lettura la bolletta arrivata in quel mese.\n"
                      "Puoi usare la stessa categoria per tutte (es. «Bollette»): in quel caso\n"
                      "riconosco acqua/luce/gas dalla descrizione della spesa."
                 ).pack(padx=16, pady=(14, 8), anchor="w")
        righe_dlg = tk.Frame(dlg, bg=self.COLOR_TOPLEVEL)
        righe_dlg.pack(padx=16, pady=4, fill="x")
        vars_cat = {}
        for riga, utenza in enumerate(utenze):
            img_u = self.icone_gui.get({"Acqua": "acqua", "Luce": "luce", "Gas": "gas"}.get(utenza))
            emoji = '💧' if utenza == 'Acqua' else '💡' if utenza == 'Luce' else '🔥'
            lbl_u = tk.Label(righe_dlg, image=img_u, text=f" {utenza}:" if img_u else f"{emoji} {utenza}:",
                             compound="left", bg=self.COLOR_TOPLEVEL, fg=self.COLOR_HEADER,
                             font=("Arial", 10, "bold"), width=90 if img_u else 10, anchor="w")
            lbl_u.image = img_u
            lbl_u.grid(row=riga, column=0, pady=4)
            attuale = _categoria_bollette(utenza)
            if not attuale:
                kws = _KEYWORDS_UTENZA[utenza]
                attuale = next((c for c in cats if any(k in c.lower() for k in kws)), "")
                if not attuale:
                    attuale = next((c for c in cats if "bollett" in c.lower() or "utenz" in c.lower()), "")
            v = tk.StringVar(value=attuale if attuale in cats else NESSUNA)
            ttk.Combobox(righe_dlg, textvariable=v, values=[NESSUNA] + cats, state="readonly", width=32,
                         style="Border.TCombobox").grid(row=riga, column=1, pady=4, padx=(6, 0))
            vars_cat[utenza] = v
        def salva(evt=None):
            for u, v in vars_cat.items():
                sel = v.get()
                anagrafiche.setdefault(u, {})["_categoria_bollette"] = "" if sel == NESSUNA else sel
            scrivi_db()
            _bollette_cache(forza=True)
            dlg.destroy()
        def annulla(evt=None):
            if primo_avvio:
                for u in utenze:
                    anagrafiche.setdefault(u, {}).setdefault("_categoria_bollette", "")
                scrivi_db()
            dlg.destroy()
        bt = tk.Frame(dlg, bg=self.COLOR_TOPLEVEL)
        bt.pack(pady=(8, 14))
        _bottone_label(bt, "salva", "Salva", "💾", salva, padx=6)
        _bottone_label(bt, "chiudi", "Più tardi" if primo_avvio else "Annulla", "❌", annulla, padx=6)
        dlg.protocol("WM_DELETE_WINDOW", annulla)
        dlg.bind("<Escape>", annulla)
        dlg.update_idletasks()
        x = win.winfo_rootx() + (win.winfo_width() - dlg.winfo_width()) // 2
        y = win.winfo_rooty() + (win.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        dlg.grab_set()
        dlg.focus_force()

    def _chiedi_categorie_se_servono():
        try:
            if not win.winfo_exists():
                return
        except tk.TclError:
            return
        if any("_categoria_bollette" not in anagrafiche.get(u, {}) for u in utenze):
            _apri_dialogo_categorie_bollette(primo_avvio=True)

    _cache_reg = {"ts": 0.0, "dati": {}}

    def _registro_documenti():
        import time as _t
        if _t.time() - _cache_reg["ts"] > 3:
            dati = {}
            try:
                rf = getattr(_app, "REGISTRY_FILE", None)
                if rf and os.path.exists(rf):
                    with open(rf, "r", encoding="utf-8") as f:
                        dati = json.load(f) or {}
            except Exception:
                dati = {}
            _cache_reg["dati"] = dati
            _cache_reg["ts"] = _t.time()
        return _cache_reg["dati"]

    def _documenti_bolletta(utenza, mese_k):
        cat = _categoria_bollette(utenza)
        if not cat or "/" not in mese_k:
            return []
        mm, aaaa = mese_k.split("/", 1)
        condivisa = sum(1 for u in utenze if _categoria_bollette(u) == cat) > 1
        trovati = []
        doc_dir = getattr(_app, "DOC_DIR", "")
        for nome, d in _registro_documenti().items():
            try:
                if d.get("categoria_esatta") != cat:
                    continue
                raw = str(d.get("data_raw", ""))
                if len(raw) != 8 or raw[2:4] != mm or raw[4:8] != aaaa:
                    continue
                if condivisa:
                    descr = str(d.get("descrizione_esatta", "")).lower()
                    match = [u for u, kws in _KEYWORDS_UTENZA.items() if any(k in descr for k in kws)]
                    if match != [utenza]:
                        continue
                for base in (doc_dir, os.path.join(os.getcwd(), "Fatture_GMail")):
                    fp = os.path.join(base, nome)
                    if os.path.exists(fp):
                        trovati.append((raw[4:8] + raw[2:4] + raw[0:2], fp))
                        break
            except Exception:
                continue
        trovati.sort(reverse=True)
        return [fp for _, fp in trovati]
    _FORMATI_FATTURA = (".pdf", ".png", ".jpg", ".jpeg", ".webp")
    MAX_IMPORT_AUTO = 3
    _import_in_corso = set()

    def _fatture_da_importare(utenza):
        cat = _categoria_bollette(utenza)
        if not cat:
            return []
        gia = set(anagrafiche.get(utenza, {}).get("_fatture_importate", []) or [])
        condivisa = sum(1 for u in utenze if _categoria_bollette(u) == cat) > 1
        doc_dir = getattr(_app, "DOC_DIR", "")
        trovati = []
        for nome, d in _registro_documenti().items():
            try:
                if nome in gia or d.get("categoria_esatta") != cat:
                    continue
                if os.path.splitext(nome)[1].lower() not in _FORMATI_FATTURA:
                    continue
                raw = str(d.get("data_raw", ""))
                if len(raw) != 8:
                    continue
                if condivisa:
                    descr = str(d.get("descrizione_esatta", "")).lower()
                    match = [u for u, kws in _KEYWORDS_UTENZA.items() if any(k in descr for k in kws)]
                    if match != [utenza]:
                        continue
                for base in (doc_dir, os.path.join(os.getcwd(), "Fatture_GMail")):
                    fp = os.path.join(base, nome)
                    if os.path.exists(fp):
                        trovati.append((raw[4:8] + raw[2:4] + raw[0:2], nome, fp))
                        break
            except Exception:
                continue
        trovati.sort()
        return trovati

    def _diagnosi_import(utenza):
        cat = _categoria_bollette(utenza)
        gia = set(anagrafiche.get(utenza, {}).get("_fatture_importate", []) or [])
        condivisa = sum(1 for u in utenze if _categoria_bollette(u) == cat) > 1
        doc_dir = getattr(_app, "DOC_DIR", "")
        n_cat = n_gia = n_fmt = n_kw = n_file = 0
        for nome, d in _registro_documenti().items():
            try:
                if d.get("categoria_esatta") != cat:
                    continue
                n_cat += 1
                if nome in gia:
                    n_gia += 1
                    continue
                if os.path.splitext(nome)[1].lower() not in _FORMATI_FATTURA:
                    n_fmt += 1
                    continue
                if condivisa:
                    descr = str(d.get("descrizione_esatta", "")).lower()
                    match = [u for u, kws in _KEYWORDS_UTENZA.items() if any(k in descr for k in kws)]
                    if match != [utenza]:
                        n_kw += 1
                        continue
                if not any(os.path.exists(os.path.join(b, nome)) for b in (doc_dir, os.path.join(os.getcwd(), "Fatture_GMail"))):
                    n_file += 1
            except Exception:
                continue
        if n_cat == 0:
            return f"{utenza}: nessun documento in Archivio nella categoria '{cat}'."
        parti = []
        if n_gia:
            parti.append(f"{n_gia} già importati")
        if n_fmt:
            parti.append(f"{n_fmt} non PDF/immagine")
        if n_kw:
            parti.append(f"{n_kw} scartati perché la descrizione non indica solo '{utenza}'")
        if n_file:
            parti.append(f"{n_file} con file non trovato")
        return f"{utenza}: {n_cat} documenti nella categoria, nessuno da importare (" + ", ".join(parti) + ")."

    def _importa_automatico(utenza, manuale=False):
        if utenza in _import_in_corso:
            return
        if not _categoria_bollette(utenza):
            if manuale:
                self.show_toast("Imposta prima la categoria delle bollette.")
            return
        if not API_KEY:
            if manuale:
                self.show_toast("Serve la chiave API Gemini (Impostazioni).")
            return
        _cache_reg["ts"] = 0.0
        tutti = _fatture_da_importare(utenza)
        ultimi = tutti[-MAX_IMPORT_AUTO:]
        if not ultimi:
            if manuale:
                self.show_toast(_diagnosi_import(utenza))
            return
        _import_in_corso.add(utenza)
        st = ai_status_labels.get(utenza)
        if st is not None and st.winfo_exists():
            st.config(text=f"⏳ Importazione automatica: {len(ultimi)} fatture in analisi …")

        def _run():
            risultati, errore = [], None
            for _, nome, fp in ultimi:
                try:
                    risultati.append((nome, _chiama_gemini_fattura(fp)))
                except Exception as e:
                    errore = _msg_errore_gemini(e)
                    break

            def _fine():
                _import_in_corso.discard(utenza)
                try:
                    if not win.winfo_exists():
                        return
                except tk.TclError:
                    return
                applicate = 0
                for nome, dati in risultati:
                    if isinstance(dati, dict) and not (dati.get("consumo_periodo") in (None, "") and dati.get("spesa_totale_periodo") in (None, "")):
                        _applica_estrazione_fattura(utenza, dati, silenzioso=True)
                        applicate += 1
                imp = anagrafiche.setdefault(utenza, {}).setdefault("_fatture_importate", [])
                for nome, _ in risultati:
                    if nome not in imp:
                        imp.append(nome)
                if not errore:
                    for _, nome, _fp in tutti:
                        if nome not in imp:
                            imp.append(nome)
                if applicate:
                    salva_dati(utenza, silenzioso=True)
                else:
                    scrivi_db()
                st2 = ai_status_labels.get(utenza)
                if st2 is not None and st2.winfo_exists():
                    st2.config(text=(f"⚠ {errore}" if errore and not applicate else _testo_storico(utenza)))
                if errore:
                    self.show_toast(errore)
                else:
                    self.show_toast(f"Importazione automatica {utenza}: {applicate} fattur{'a' if applicate == 1 else 'e'} analizzat{'a' if applicate == 1 else 'e'}.")
            self.after(0, _fine)
        threading.Thread(target=_run, daemon=True).start()

    def _toggle_import_auto(utenza):
        anagrafiche.setdefault(utenza, {})["_import_auto"] = not _import_auto_attivo(utenza)
        scrivi_db()
        _aggiorna_toggle(utenza)
        if _import_auto_attivo(utenza):
            _importa_automatico(utenza, manuale=True)

    def _ultimo_documento(utenza):
        cat = _categoria_bollette(utenza)
        if not cat:
            return None
        condivisa = sum(1 for u in utenze if _categoria_bollette(u) == cat) > 1
        doc_dir = getattr(_app, "DOC_DIR", "")
        trovati = []
        for nome, d in _registro_documenti().items():
            try:
                if d.get("categoria_esatta") != cat or os.path.splitext(nome)[1].lower() != ".pdf":
                    continue
                raw = str(d.get("data_raw", ""))
                if len(raw) != 8:
                    continue
                if condivisa:
                    descr = str(d.get("descrizione_esatta", "")).lower()
                    match = [u for u, kws in _KEYWORDS_UTENZA.items() if any(k in descr for k in kws)]
                    if match != [utenza]:
                        continue
                for base in (doc_dir, os.path.join(os.getcwd(), "Fatture_GMail")):
                    fp = os.path.join(base, nome)
                    if os.path.exists(fp):
                        trovati.append((raw[4:8] + raw[2:4] + raw[0:2], fp))
                        break
            except Exception:
                continue
        return max(trovati)[1] if trovati else None

    def _confronta_documenti_tutte():
        # nessuna verifica/analisi: apre l'ultimo documento di ogni utenza
        _cache_reg["ts"] = 0.0
        aperti = 0
        for u in utenze:
            fp = _ultimo_documento(u)
            if fp:
                _mostra_viewer_bolletta(fp, os.path.basename(fp))
                aperti += 1
        if not aperti:
            self.show_toast("Nessun documento in Archivio.")

    def _importa_automatico_tutte():
        try:
            if not win.winfo_exists():
                return
        except tk.TclError:
            return
        for u in utenze:
            if _import_auto_attivo(u):
                _importa_automatico(u)

    def _riga_mese(tr, iid):
        vals = tr.item(iid)["values"]
        if not vals or any(t.startswith("totale") for t in tr.item(iid, "tags")):
            return None
        m = str(vals[0]).strip()
        return m if len(m) == 7 and m[2] == "/" else None

    def _mostra_viewer_bolletta(file_path, file_name):
        try:
            Image_ = _app.Image
            ImageTk_ = _app.ImageTk
            vw = tk.Toplevel(win)
            vw.title(f"Bolletta - {file_name}")
            vw.transient(win)
            vw.withdraw()
            W, H = 950, 630
            vw.bind("<Escape>", lambda e: vw.destroy())
            sw, sh = vw.winfo_screenwidth(), vw.winfo_screenheight()
            vw.geometry(f"{W}x{H}+{(sw // 2) - (W // 2)}+{(sh // 2) - (H // 2)}")
            vw.minsize(W, H)
            vw.configure(bg=self.COLOR_WIDGET_BG)
            cont = tk.Frame(vw, bg=self.COLOR_WIDGET_BG)
            cont.pack(fill=tk.BOTH, expand=True)
            cv = tk.Canvas(cont, bg=self.COLOR_WIDGET_BG, highlightthickness=0)
            vs = ttk.Scrollbar(cont, orient="vertical", command=cv.yview, style="Vertical.TScrollbar")
            hs = ttk.Scrollbar(cont, orient="horizontal", command=cv.xview, style="Horizontal.TScrollbar")
            cv.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
            vs.pack(side=tk.RIGHT, fill=tk.Y)
            hs.pack(side=tk.BOTTOM, fill=tk.X)
            cv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            fitz.TOOLS.mupdf_display_errors(False)
            immagini = []
            y_off, max_w = 20, 0
            with fitz.open(file_path) as d:
                mat = fitz.Matrix(1.4, 1.4)
                for n in range(len(d)):
                    pix = d.load_page(n).get_pixmap(matrix=mat, annots=False)
                    foto = ImageTk_.PhotoImage(Image_.frombytes("RGB", [pix.width, pix.height], pix.samples))
                    immagini.append(foto)
                    cv.create_image(max(20, (W - pix.width) // 2), y_off, anchor="nw", image=foto)
                    y_off += pix.height + 25
                    max_w = max(max_w, pix.width)
            cv.image_refs = immagini
            cv.config(scrollregion=(0, 0, max(W, max_w + 40), y_off + 50))
            def _rotella(event):
                if event.num == 4 or event.delta > 0:
                    cv.yview_scroll(-1, "units")
                elif event.num == 5 or event.delta < 0:
                    cv.yview_scroll(1, "units")
            for ev in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                cv.bind(ev, _rotella)
            btns = tk.Frame(vw, bg=self.COLOR_WIDGET_BG)
            btns.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=10)
            def _bottone(chiave, testo, comando, lato):
                img = self.icone_gui.get(chiave)
                b = ttk.Label(btns, compound="left", image=img, text=f" {testo}" if img else testo,
                              background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2")
                b.image = img
                b.pack(side=lato, padx=10)
                b.bind("<Button-1>", lambda e: comando())
            def _salva():
                import shutil
                vw.wm_attributes('-topmost', 1)
                dest = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF", "*.pdf"), ("Tutti i file", "*.*")],
                                                    initialdir=EXPORT_FILES, initialfile=file_name, title="Esporta PDF",
                                                    confirmoverwrite=False, parent=vw)
                vw.wm_attributes('-topmost', 0)
                if dest:
                    if os.path.exists(dest):
                        conferma = self.show_custom_askyesno(
                            "Sovrascrivere file?",
                            f"Il file '{os.path.basename(dest)}' \nesiste già. Vuoi sovrascriverlo?"
                        )
                        if not conferma:
                            return
                    shutil.copy2(file_path, dest)
                    self.show_toast("Documento salvato!")
            _bottone("stampa", "Stampa", lambda: self.stampa_pdf(file_path, self.show_custom_warning), "left")
            _bottone("salva", "Salva", _salva, "left")
            _bottone("chiudi", "Chiudi", vw.destroy, "right")
            vw.deiconify()
            vw.lift()
            vw.focus_force()
        except Exception as e:
            self.show_custom_warning("Errore", f"Impossibile aprire la bolletta:\n{e}")

    def _apri_bolletta(utenza, event):
        tr = self.trees[utenza]
        if tr.identify_region(event.x, event.y) != "cell":
            return
        iid = tr.identify_row(event.y)
        mese_k = _riga_mese(tr, iid) if iid else None
        if not mese_k:
            return
        if not _categoria_bollette(utenza):
            _apri_dialogo_categorie_bollette()
            return "break"
        docs = _documenti_bolletta(utenza, mese_k)
        if not docs:
            self.show_toast(f"Nessuna bolletta {utenza} archiviata per {mese_k}.")
            return "break"
        if len(docs) > 1:
            self.show_toast(f"{len(docs)} documenti per {mese_k}: apro il più recente.")
        _anteprima_chiudi()
        _mostra_viewer_bolletta(docs[0], os.path.basename(docs[0]))
        return "break"

    _anteprima = {"popup": None, "job": None, "key": None, "img": None, "img_key": None}

    def _anteprima_chiudi(event=None):
        if _anteprima["job"]:
            try:
                win.after_cancel(_anteprima["job"])
            except Exception:
                pass
            _anteprima["job"] = None
        if _anteprima["popup"]:
            try:
                _anteprima["popup"].destroy()
            except Exception:
                pass
            _anteprima["popup"] = None
        _anteprima["key"] = None

    def _anteprima_render(path, altezza):
        try:
            import pymupdf as fitz
            Image_ = getattr(_app, "Image", None)
            ImageTk_ = getattr(_app, "ImageTk", None)
            if Image_ is None or ImageTk_ is None:
                return None
            fitz.TOOLS.mupdf_display_errors(False)
            with fitz.open(path) as d:
                if len(d) == 0:
                    return None
                pg = d.load_page(0)
                z = altezza / pg.rect.height
                pix = pg.get_pixmap(matrix=fitz.Matrix(z, z), alpha=False, annots=False)
                img = Image_.frombytes("RGB", [pix.width, pix.height], pix.samples)
            return ImageTk_.PhotoImage(img)
        except Exception:
            return None

    def _anteprima_mostra(key, utenza, mese_k):
        _anteprima["job"] = None
        if _anteprima["popup"] or _anteprima["key"] != key:
            return
        docs = _documenti_bolletta(utenza, mese_k)
        if not docs:
            return
        path = docs[0]
        h = max(300, min(600, win.winfo_screenheight() - 160))
        if _anteprima["img_key"] != path or _anteprima["img"] is None:
            _anteprima["img"] = _anteprima_render(path, h)
            _anteprima["img_key"] = path
        img = _anteprima["img"]
        if img is None:
            return
        top = tk.Toplevel(win)
        top.withdraw()
        top.overrideredirect(True)
        try:
            top.attributes("-topmost", True)
        except Exception:
            pass
        lbl = tk.Label(top, image=img, bd=0, bg="#222222", highlightthickness=2, highlightbackground="#888888")
        lbl.image = img
        lbl.pack()
        top.update_idletasks()
        sw, sh = top.winfo_screenwidth(), top.winfo_screenheight()
        pw, ph = top.winfo_reqwidth(), top.winfo_reqheight()
        px, py = win.winfo_pointerx(), win.winfo_pointery()
        x = px + 24
        if x + pw > sw:
            x = max(0, px - pw - 24)
        y = max(0, min(py - 20, sh - ph - 40))
        top.geometry(f"+{x}+{y}")
        top.deiconify()
        top.lift()
        _anteprima["popup"] = top

    def _anteprima_motion(event, utenza):
        tr = self.trees[utenza]
        iid = tr.identify_row(event.y)
        col = tr.identify_column(event.x)
        colonne = list(tr["columns"])
        if not iid or col != f"#{colonne.index('Bolletta') + 1}":
            if _anteprima["key"] is not None or _anteprima["popup"]:
                _anteprima_chiudi()
            return
        mese_k = _riga_mese(tr, iid)
        if not mese_k:
            _anteprima_chiudi()
            return
        key = (utenza, iid, mese_k)
        if key == _anteprima["key"]:
            return
        _anteprima_chiudi()
        _anteprima["key"] = key
        _anteprima["job"] = win.after(450, lambda: _anteprima_mostra(key, utenza, mese_k))

    for _u in utenze:
        _tr = self.trees[_u]
        _tr.bind("<Double-1>", lambda e, u=_u: _apri_bolletta(u, e), add="+")
        _tr.bind("<Motion>", lambda e, u=_u: _anteprima_motion(e, u), add="+")
        _tr.bind("<Leave>", _anteprima_chiudi, add="+")
        _tr.bind("<ButtonPress>", _anteprima_chiudi, add="+")
        _tr.bind("<MouseWheel>", _anteprima_chiudi, add="+")
    win.bind("<Destroy>", lambda e: _anteprima_chiudi() if e.widget is win else None, add="+")

    def _profilo_casa():
        return anagrafiche.get(utenze[0], {}).get("_profilo_casa", {}) or {}

    def _raccogli_dati_analisi():
        if not modalita_corrente["tutti"]:
            anno_v = modalita_corrente["anno"]
            for u in utenze:
                tr = self.trees.get(u)
                if tr is not None and tr.get_children():
                    letture_salvate[u][anno_v] = [tuple(tr.item(i)["values"])[:4] for i in tr.get_children()]
        blocchi = []
        for u in utenze:
            unita = _UNITA_TOT.get(u, "")
            serie = []
            per_anno = {}
            for anno_k, righe in letture_salvate.get(u, {}).items():
                for r in righe:
                    try:
                        mese_k = str(r[0]).strip()
                        cons = float(r[3])
                    except (ValueError, IndexError, TypeError):
                        continue
                    if cons > 0 and len(mese_k) == 7:
                        serie.append((mese_k[3:] + "-" + mese_k[:2], cons))
                        per_anno.setdefault(mese_k[3:], []).append(cons)
            serie.sort()
            righe_txt = [f"{u.upper()} (unità: {unita})"]
            if per_anno:
                for a in sorted(per_anno):
                    v = per_anno[a]
                    righe_txt.append(f"  anno {a}: totale {sum(v):.1f}, media mensile {sum(v)/len(v):.1f} su {len(v)} mesi con lettura")
                righe_txt.append("  ultimi 24 mesi (aaaa-mm: consumo): " + ", ".join(f"{m}: {c:.1f}" for m, c in serie[-24:]))
            else:
                righe_txt.append("  nessuna lettura di consumo registrata")
            blocchi.append("\n".join(righe_txt))
        return "\n\n".join(blocchi), any(letture_salvate.get(u) for u in utenze)

    def _avvia_analisi_ia(profilo):
        import datetime as _dt
        if not API_KEY:
            self.show_custom_warning("Configurazione AI Necessaria",
                "L'analisi di mercato richiede una chiave API Gemini (gratuita).\n\n"
                "Vai nella sezione Impostazioni e clicca sul pulsante 'Ottieni'.\n")
            return
        dati_txt, _ = _raccogli_dati_analisi()
        if "nessuna lettura" in dati_txt and dati_txt.count("nessuna lettura") == len(utenze):
            self.show_custom_warning("Nessun Dato", "Registra almeno qualche lettura di consumo prima di avviare l'analisi.")
            return
        oggi = _dt.date.today()
        pers = profilo.get("persone", 1)
        prompt = f"""Sei un consulente indipendente sui consumi domestici di acqua, luce e gas per famiglie italiane. Oggi è il {oggi.strftime('%d/%m/%Y')}.
Analizza SOLO i consumi di acqua, luce e gas di questa famiglia. Non interessano costi, tariffe, fornitori o contratti: non parlarne.

PROFILO ABITAZIONE:
- persone in famiglia: {pers}
- località (comune/provincia): {profilo.get('localita') or 'non indicata'}
- superficie abitazione: {profilo.get('mq') or 'non indicata'} mq
- uso del gas in casa: {profilo.get('uso_gas') or 'non indicato'}
- riscaldamento principale: {profilo.get('riscaldamento') or 'non indicato'}

COME USARE IL PROFILO (importante):
- usa la località per zona climatica e clima.
- confronta il consumo di gas SOLO con l'uso dichiarato: se il gas serve solo per cottura e/o acqua calda NON confrontarlo con le medie del gas da riscaldamento; cerca i consumi tipici per quell'uso e per {pers} persone.
- se il riscaldamento è a pellet, legna, elettrico o teleriscaldamento, il combustibile (sacchi di pellet, legna) non compare nei consumi registrati: dillo esplicitamente; se è elettrico o a pompa di calore tienine conto nei consumi di luce invernali.
- se l'uso del gas è "Non ho il gas", non giudicare il gas.
- se il profilo contraddice i consumi registrati (es. gas "solo cottura" ma consumi invernali alti) segnalalo in ANDAMENTO E ANOMALIE e in AVVERTENZE invece di ignorarlo.

REGOLE (importante):
- parla esclusivamente di consumi (quantità), mai di euro, prezzi, tariffe, offerte, fornitori, contratti o scadenze.
- le bombole di GPL e il combustibile di pellet e legna non compaiono nei consumi registrati: non valutarli senza dati.
- se i consumi sono molto bassi, di' chiaramente che il margine di miglioramento è piccolo.
- tono sempre pacato: niente allarmi, niente "urgente".

DATI REGISTRATI DALLA FAMIGLIA:
{dati_txt}

USA LA RICERCA WEB per dati aggiornati sui consumi medi (ARERA, ISTAT, ENEA, ISPRA, fonti ufficiali). Non inventare numeri: se un dato non è reperibile dichiaralo e indica che è una stima.

STRUTTURA DELLA RISPOSTA (titoli in MAIUSCOLO, uno per ciascuna sezione):
1. SINTESI: tre o quattro righe con il giudizio complessivo sui consumi.
2. CONSUMI RISPETTO ALLA MEDIA: per acqua, luce e gas confronta i consumi annui e per persona con le medie italiane (nazionali e, se disponibile, della zona) per un nucleo di {pers} persone. Dì chiaramente se siamo sopra, in linea o sotto la media e di quanto in percentuale.
3. ANDAMENTO E ANOMALIE: stagionalità, picchi, mesi anomali, trend rispetto agli anni precedenti, possibili perdite o sprechi (per esempio consumi d'acqua o gas fuori stagione).
4. AZIONI CONCRETE DI RISPARMIO SUI CONSUMI: elenco di azioni pratiche in ordine di rendimento, ognuna con effetto atteso a parole (alto, medio, basso).
5. PIANO IN TRE PASSI: cosa fare adesso, entro tre mesi, entro un anno.
6. AVVERTENZE: limiti dell'analisi e dati che ti mancano e che migliorerebbero la stima.

REGOLE DI FORMATO:
- NON usare simboli Markdown (asterischi, cancelletti, trattini doppi per il grassetto, tabelle con barre).
- Usa il minuscolo per il corpo del testo e le MAIUSCOLE solo per i titoli delle sezioni.
- Numeri in formato italiano (virgola decimale, punto per le migliaia).
- Se ricavi un dato dal web scrivi tra parentesi la fonte e la data. Sii concreto e sintetico.
"""
        from moduli.spinner_animato import crea_spinner_animato
        if getattr(self, "_win_analisi_utenze", None) is not None:
            try:
                if self._win_analisi_utenze.winfo_exists():
                    self._win_analisi_utenze.destroy()
            except Exception:
                pass
        aw = tk.Toplevel(win, bg=self.COLOR_TOPLEVEL)
        self._win_analisi_utenze = aw
        aw.title("Analisi Consumi Utenze — IA")
        aw.withdraw()
        W2, H2 = 1100, 660
        x2 = win.winfo_rootx() + (win.winfo_width() - W2) // 2
        y2 = win.winfo_rooty() + (win.winfo_height() - H2) // 2
        aw.geometry(f"{W2}x{H2}+{max(x2, 0)}+{max(y2, 0)}")
        aw.minsize(900, 560)
        aw.bind("<Escape>", lambda e: aw.destroy())
        ttk.Label(aw, text="Analisi di Mercato: consumi e costi di Acqua, Luce e Gas",
                  style="Header.TLabel", font=("Consolas", 12, "bold")).pack(side="top", pady=(14, 6))
        barra = tk.Frame(aw, bg=self.COLOR_TOPLEVEL)
        barra.pack(side="bottom", fill="x", pady=10)
        stato = tk.Frame(aw, bg=self.COLOR_TOPLEVEL)
        stato.pack(side="top", pady=(0, 4))
        cvs, _ = crea_spinner_animato(stato, self.COLOR_TOPLEVEL, size=24, tick_ms=30)
        cvs.pack(side="left", padx=(0, 8))
        lbl_stato = tk.Label(stato, text="Ricerca dei prezzi di mercato e analisi in corso…",
                             bg=self.COLOR_TOPLEVEL, fg=self.COLOR_HIGHLIGHT, font=("Segoe UI", 9, "bold"))
        lbl_stato.pack(side="left")
        cont = tk.Frame(aw, bg=self.COLOR_TOPLEVEL)
        cont.pack(side="top", expand=True, fill="both", padx=20, pady=5)
        sb = ttk.Scrollbar(cont, orient="vertical", style="Vertical.TScrollbar")
        sb.pack(side="right", fill="y")
        area = tk.Text(cont, bg=self.COLOR_WHITE, fg=self.COLOR_BLACK, font=("Consolas", 11), wrap="word",
                       padx=25, pady=25, borderwidth=0, yscrollcommand=sb.set, spacing1=6)
        area.pack(side="left", expand=True, fill="both")
        sb.config(command=area.yview)
        area.config(state="disabled")

        def _chiedi_percorso(titolo, estensione, tipo_file):
            now = datetime.date.today()
            aw.wm_attributes('-topmost', 1)
            dest = filedialog.asksaveasfilename(
                defaultextension=estensione, filetypes=[(tipo_file, f"*{estensione}")], initialdir=EXPORT_FILES,
                initialfile=f"Analisi_Utenze_{now.day:02d}-{now.month:02d}-{now.year}{estensione}",
                title=titolo, confirmoverwrite=False, parent=aw)
            aw.wm_attributes('-topmost', 0)
            if not dest:
                return None
            if os.path.exists(dest):
                conferma = self.show_custom_askyesno(
                    "Sovrascrivere file?",
                    f"Il file '{os.path.basename(dest)}' \nesiste già. Vuoi sovrascriverlo?"
                )
                if not conferma:
                    return None
            return dest

        def _salva_txt():
            dest = _chiedi_percorso("Salva analisi", ".txt", "File txt")
            if dest:
                with open(dest, "w", encoding="utf-8") as f:
                    f.write(area.get("1.0", tk.END))
                self.show_custom_warning("Esportazione completata", f"Analisi salvata in\n{dest}")
        def _salva_pdf():
            testo_a = area.get("1.0", tk.END).strip()
            if not testo_a:
                self.show_toast("Analisi non ancora pronta.")
                return
            now = datetime.date.today()
            dest = _chiedi_percorso("Salva PDF", ".pdf", "File PDF")
            if not dest:
                return
            W, H, MARG, FS = 595, 842, 40, 9.5
            sost = {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2013": "-", "\u2014": "-",
                    "\u2022": "-", "\u2192": "->", "\u2248": "~", "\u2026": "...", "\u00a0": " ", "\t": "    "}
            for k_, v_ in sost.items():
                testo_a = testo_a.replace(k_, v_)
            testo_a = "".join(c if ord(c) < 256 else "?" for c in testo_a)
            doc = fitz.open()
            try:
                font = fitz.Font("helv")
                now_txt = f"{now.day:02d}/{now.month:02d}/{now.year}"
                def nuova_pagina():
                    pg = doc.new_page(width=W, height=H)
                    pg.draw_rect(fitz.Rect(0, 0, W, 56), color=None, fill=(0.12, 0.30, 0.45))
                    pg.insert_text((MARG, 34), "Analisi di Mercato Utenze", fontsize=15, color=(1, 1, 1), fontname="Helvetica-Bold")
                    pg.insert_text((W - MARG - 55, 34), now_txt, fontsize=9, color=(1, 1, 1), fontname="Helvetica")
                    return pg
                rimasto = testo_a
                while rimasto:
                    pg = nuova_pagina()
                    tw = fitz.TextWriter(pg.rect)
                    rect = fitz.Rect(MARG, 72, W - MARG, H - 36)
                    ovf = tw.fill_textbox(rect, rimasto, font=font, fontsize=FS, align=fitz.TEXT_ALIGN_LEFT, warn=None)
                    tw.write_text(pg)
                    if not ovf:
                        break
                    rimasto = "\n".join(t_[0] if isinstance(t_, (tuple, list)) else str(t_) for t_ in ovf)
                n_tot = doc.page_count
                for i, pp in enumerate(doc):
                    pp.insert_text((W - MARG - 60, H - 14), f"Pagina {i+1} / {n_tot}", fontsize=6.5, color=(0.5, 0.5, 0.5), fontname="Helvetica")
                doc.set_metadata({"title": "Analisi di Mercato Utenze", "author": "Gestione Utenze"})
                doc.save(dest)
            finally:
                doc.close()
            self.show_custom_warning("Esportazione completata", f"PDF esportato in\n{dest}")

        def _stampa_analisi():
            testo_a = area.get("1.0", tk.END).strip()
            if not testo_a:
                self.show_toast("Analisi non ancora pronta.")
                return
            self._stampa_lista_diretta(testo_a, self.show_custom_warning)
        for chiave, testo, cmd, lato in (("salva", "Salva TXT", _salva_txt, "left"), ("report", "Salva PDF", _salva_pdf, "left"),
                                         ("stampa", "Stampa", _stampa_analisi, "left"), ("chiudi", "Chiudi", aw.destroy, "right")):
            img = self.icone_gui.get(chiave)
            b = ttk.Label(barra, compound="left", image=img, text=f" {testo}" if img else testo, cursor="hand2",
                          background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, padding=(10, 5))
            b.image = img
            b.pack(side=lato, padx=12)
            b.bind("<Button-1>", lambda e, c=cmd: c())
        aw.deiconify()
        aw.lift()

        def _mostra(testo):
            try:
                if not aw.winfo_exists():
                    return
                cvs.destroy()
                lbl_stato.config(text="Analisi completata.", fg=self.TEXT_COLOR)
                area.config(state="normal")
                area.delete("1.0", tk.END)
                area.insert("1.0", testo)
                area.config(state="disabled")
            except tk.TclError:
                pass

        def _run():
            testo = ""
            fonti = []
            try:
                client = genai_client.Client(api_key=API_KEY)
                try:
                    cfg = types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())], temperature=0.3)
                    resp = client.models.generate_content(model=GEMINI, contents=prompt, config=cfg)
                    ricerca_web = True
                except Exception as e_ws:
                    err_ws = str(e_ws)
                    if "429" in err_ws or "RESOURCE_EXHAUSTED" in err_ws or "503" in err_ws or "UNAVAILABLE" in err_ws:
                        raise
                    resp = client.models.generate_content(model=GEMINI, contents=prompt)
                    ricerca_web = False
                testo = (resp.text or "").strip() or "Nessun testo generato."
                if ricerca_web:
                    try:
                        visti = set()
                        for ch in resp.candidates[0].grounding_metadata.grounding_chunks or []:
                            w = getattr(ch, "web", None)
                            if w and w.uri not in visti:
                                visti.add(w.uri)
                                fonti.append(f"- {w.title or 'fonte'}: {w.uri}")
                    except Exception:
                        pass
                else:
                    testo = ("ATTENZIONE: la ricerca web non è disponibile con il modello configurato, "
                             "i prezzi di mercato sono stime basate sulle conoscenze del modello e possono non essere aggiornati.\n\n") + testo
            except Exception as err:
                e_s = str(err)
                if "429" in e_s or "RESOURCE_EXHAUSTED" in e_s:
                    testo = "Quota API Gemini esaurita. Riprova più tardi."
                elif "503" in e_s or "UNAVAILABLE" in e_s:
                    testo = "Gemini non disponibile al momento. Riprova tra poco."
                else:
                    testo = f"ERRORE API:\n{e_s[:300]}"
            if fonti:
                testo += "\n\nFONTI WEB CONSULTATE\n" + "\n".join(fonti)
            self.after(0, lambda: _mostra(testo))
        threading.Thread(target=_run, daemon=True).start()

    def _apri_confronta_bollette():
        import inspect
        try:
            from moduli import confronta_bollette_ia as _cb
            f = getattr(_cb, "confronta_bollette_ia")
            n = len(inspect.signature(f).parameters)
            f(self, win) if n >= 2 else f(self)
        except Exception as e:
            self.show_custom_warning("Errore", f"Impossibile aprire Confronta Bollette:\n{e}")

    def _apri_analisi_mercato():
        prof = _profilo_casa()
        dlg = tk.Toplevel(win, bg=self.COLOR_TOPLEVEL)
        dlg.title("Analisi di mercato — profilo casa")
        dlg.transient(win)
        dlg.resizable(False, False)
        tk.Label(dlg, bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR, justify="left", font=("Arial", 10),
                 text="Per confrontare i tuoi consumi con la media per persona e con i prezzi di mercato\n"
                      "servono pochi dati sulla casa. Restano salvati per le prossime analisi."
                 ).pack(padx=16, pady=(14, 8), anchor="w")
        form = tk.Frame(dlg, bg=self.COLOR_TOPLEVEL)
        form.pack(padx=16, pady=4, fill="x")
        v_pers = tk.StringVar(value=str(prof.get("persone", 2)))
        v_loc = tk.StringVar(value=prof.get("localita", ""))
        v_mq = tk.StringVar(value=str(prof.get("mq", "") or ""))
        v_risc = tk.StringVar(value=prof.get("riscaldamento", "Gas metano"))
        v_uso = tk.StringVar(value=prof.get("uso_gas", _USI_GAS[0]))
        ent_loc = ttk.Entry(form, textvariable=v_loc, width=34, style="Border.TEntry")
        fr_lb = tk.Frame(dlg, bg=self.COLOR_TOPLEVEL)
        lb_loc = tk.Listbox(fr_lb, height=5, exportselection=False, bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR, font=("Arial", 10))
        sb_loc = ttk.Scrollbar(fr_lb, orient="vertical", command=lb_loc.yview)
        lb_loc.configure(yscrollcommand=sb_loc.set)
        sb_loc.pack(side="right", fill="y")
        lb_loc.pack(side="left", fill="both", expand=True)
        def _scegli_comune(evt=None):
            sel = lb_loc.curselection()
            if sel:
                v_loc.set(lb_loc.get(sel[0]))
                fr_lb.pack_forget()
                ent_loc.focus_set()
                ent_loc.icursor("end")
        def _filtra_comuni(evt=None):
            if evt is not None and evt.keysym in ("Up", "Left", "Right", "Return", "Escape", "Tab"):
                return
            if evt is not None and evt.keysym == "Down" and fr_lb.winfo_ismapped():
                lb_loc.focus_set()
                lb_loc.selection_set(0)
                lb_loc.activate(0)
                return
            t = v_loc.get().strip().casefold()
            trovati = [c for c in _carica_comuni() if c.casefold().startswith(t)][:50] if len(t) >= 2 else []
            if trovati and not (len(trovati) == 1 and trovati[0].casefold() == t):
                lb_loc.delete(0, "end")
                for c in trovati:
                    lb_loc.insert("end", c)
                lb_loc.yview_moveto(0)
                if not fr_lb.winfo_ismapped():
                    fr_lb.pack(padx=16, pady=(0, 4), fill="x", after=form)
            else:
                fr_lb.pack_forget()
        ent_loc.bind("<KeyRelease>", _filtra_comuni)
        lb_loc.bind("<ButtonRelease-1>", _scegli_comune)
        lb_loc.bind("<Return>", _scegli_comune)
        campi_f = [
            ("Persone in famiglia:", ttk.Combobox(form, textvariable=v_pers, values=[str(n) for n in range(1, 13)], state="readonly", width=6, style="Border.TCombobox")),
            ("Comune:", ent_loc),
            ("Superficie (mq):", ttk.Entry(form, textvariable=v_mq, width=10, style="Border.TEntry")),
            ("Uso del gas:", ttk.Combobox(form, textvariable=v_uso, state="readonly", width=36, style="Border.TCombobox", values=_USI_GAS)),
            ("Riscaldamento:", ttk.Combobox(form, textvariable=v_risc, state="readonly", width=36, style="Border.TCombobox",
                                            values=["Gas metano", "Elettrico / pompa di calore", "GPL", "Teleriscaldamento", "Pellet / legna", "Non so"])),
        ]
        for r, (etich, w_) in enumerate(campi_f):
            tk.Label(form, text=etich, bg=self.COLOR_TOPLEVEL, fg=self.COLOR_HEADER, font=("Arial", 10, "bold"),
                     anchor="e", width=20).grid(row=r, column=0, pady=4)
            w_.grid(row=r, column=1, pady=4, padx=(6, 0), sticky="w")
        def _avvia(evt=None):
            try:
                persone = max(1, min(12, int(str(v_pers.get()).strip())))
            except ValueError:
                self.show_toast("Inserisci un numero di persone valido.")
                return
            comune, errore = _risolvi_comune(v_loc.get())
            if errore:
                self.show_toast(errore)
                return
            v_loc.set(comune)
            mq = v_mq.get().strip().replace(",", ".")
            if mq:
                try:
                    if not 10 <= float(mq) <= 2000:
                        raise ValueError
                except ValueError:
                    self.show_toast("Superficie non valida (tra 10 e 2000 mq).")
                    return
            profilo = {"persone": persone, "localita": comune, "mq": mq,
                       "uso_gas": v_uso.get(), "riscaldamento": v_risc.get()}
            anagrafiche.setdefault(utenze[0], {})["_profilo_casa"] = profilo
            scrivi_db()
            dlg.destroy()
            _avvia_analisi_ia(profilo)
        bt = tk.Frame(dlg, bg=self.COLOR_TOPLEVEL)
        bt.pack(pady=(8, 14))
        _bottone_label(bt, "fattura_ai", "Avvia analisi", "🔎", _avvia, padx=6)
        _bottone_label(bt, "chiudi", "Annulla", "❌", dlg.destroy, padx=6)
        dlg.bind("<Escape>", lambda e: dlg.destroy())
        dlg.update_idletasks()
        x = win.winfo_rootx() + (win.winfo_width() - dlg.winfo_width()) // 2
        y = win.winfo_rooty() + (win.winfo_height() - dlg.winfo_height()) // 2
        dlg.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        dlg.grab_set()
        dlg.focus_force()

    aggiorna_totali_consumi()
    win.after(500, _chiedi_categorie_se_servono)
    win.after(1500, _importa_automatico_tutte)
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

    def _fmt_var(corr, prec):
        if corr is None or prec is None or prec <= 0:
            return "n/d"
        v = (corr - prec) / prec * 100
        freccia = "▲" if v > 0.05 else "▼" if v < -0.05 else "="
        return f"{freccia} {v:+.1f}%"

    def _consumo_mese(utenza, mese_num, anno):
        mese_str = f"{mese_num:02d}/{anno}"
        riga = next((r for r in letture_salvate.get(utenza, {}).get(str(anno), []) if r[0] == mese_str), None)
        if not riga:
            return None
        try:
            return float(riga[3])
        except (ValueError, TypeError, IndexError):
            return None

    def _tot_bollette_anno(utenza, anno_i):
        dati = _bollette_cache().get(utenza, {})
        return sum(rec[0] for k, rec in dati.items() if k.endswith(f"/{anno_i}"))

    def _tt_mensile(utenza, mese_num, anno_sel):
        mese_str = f"{mese_num:02d}/{anno_sel}"
        prec, att, cons = _valori_mese(utenza, anno_sel, mese_str)
        un = _UNITA_TOT.get(utenza, "")
        righe = [f"{utenza} — {mesi_lbl_full[mese_num-1]} {anno_sel}",
                 f"Lettura prec.: {prec:.2f}",
                 f"Lettura att.:  {att:.2f}",
                 f"Consumo:       {cons:.2f} {un}"]
        stima = _stima_costo(utenza, cons) if cons > 0 else None
        if stima is not None:
            righe.append(f"Stima costo:   {_fmt_euro(stima)}")
        if _categoria_bollette(utenza):
            rec = _bollette_cache().get(utenza, {}).get(mese_str)
            if rec:
                riga_b = f"Bolletta:      {_fmt_euro(rec[0])}"
                if stima is not None:
                    riga_b += f" ({rec[0] - stima:+.2f} €)"
                righe.append(riga_b)
            else:
                righe.append("Bolletta:      —")
        try:
            anno_n = int(anno_sel)
            prev_m, prev_a = (12, anno_n - 1) if mese_num == 1 else (mese_num - 1, anno_n)
            righe.append(f"vs {mesi_lbl_full[prev_m-1]} {prev_a}: {_fmt_var(cons, _consumo_mese(utenza, prev_m, prev_a))}")
            righe.append(f"vs {mesi_lbl_full[mese_num-1]} {anno_n - 1}: {_fmt_var(cons, _consumo_mese(utenza, mese_num, anno_n - 1))}")
        except (ValueError, TypeError):
            pass
        return "\n".join(righe)

    def _tt_annuale(utenza, anno_i):
        righe = letture_salvate.get(utenza, {}).get(anno_i, [])
        by_mese = {}
        for r in righe:
            try:
                mm = r[0].split("/")[0]
                by_mese[mm] = by_mese.get(mm, 0.0) + float(r[3])
            except Exception:
                pass
        un = _UNITA_TOT.get(utenza, "")
        corpo = "\n".join(f"  {mesi_lbl_full[m-1]}: {by_mese.get(f'{m:02d}', 0.0):.2f}" for m in range(1, 13))
        tot = sum(by_mese.get(f"{m:02d}", 0.0) for m in range(1, 13))
        out = [f"{utenza} — Anno {anno_i}", corpo, f"Totale anno:    {tot:.2f} {un}"]
        attivi = {m: by_mese[f"{m:02d}"] for m in range(1, 13) if by_mese.get(f"{m:02d}", 0.0) > 0}
        if attivi:
            m_max = max(attivi, key=attivi.get)
            m_min = min(attivi, key=attivi.get)
            out.append(f"Media mensile:  {tot / len(attivi):.2f} {un}")
            out.append(f"Mese più alto:  {mesi_lbl_full[m_max-1]} ({attivi[m_max]:.2f})")
            out.append(f"Mese più basso: {mesi_lbl_full[m_min-1]} ({attivi[m_min]:.2f})")
        stima = _stima_costo(utenza, tot) if tot > 0 else None
        if stima is not None:
            out.append(f"Stima costo:    {_fmt_euro(stima)}")
        if _categoria_bollette(utenza):
            tb = _tot_bollette_anno(utenza, anno_i)
            out.append(f"Bollette anno:  {_fmt_euro(tb) if tb > 0 else '—'}")
        try:
            anno_prec = str(int(anno_i) - 1)
            if anno_prec in letture_salvate.get(utenza, {}):
                out.append(f"vs {anno_prec}:       {_fmt_var(tot, _totale_anno(utenza, anno_prec))}")
        except (ValueError, TypeError):
            pass
        return "\n".join(out)

    def _tt_totale(utenza, anni_presenti):
        un = _UNITA_TOT.get(utenza, "")
        corpo = "\n".join(f"  {a}: {_totale_anno(utenza, a):.2f}" for a in anni_presenti) or "  (nessun dato)"
        grand = sum(_totale_anno(utenza, a) for a in anni_presenti)
        out = [f"{utenza} — Totale complessivo", corpo, f"Totale completo: {grand:.2f} {un}"]
        anni_validi = [a for a in anni_presenti if _totale_anno(utenza, a) > 0]
        if anni_validi:
            out.append(f"Media annua:     {grand / len(anni_validi):.2f} {un}")
            a_max = max(anni_validi, key=lambda a: _totale_anno(utenza, a))
            a_min = min(anni_validi, key=lambda a: _totale_anno(utenza, a))
            out.append(f"Anno più alto:   {a_max} ({_totale_anno(utenza, a_max):.2f})")
            out.append(f"Anno più basso:  {a_min} ({_totale_anno(utenza, a_min):.2f})")
        stima = _stima_costo(utenza, grand) if grand > 0 else None
        if stima is not None:
            out.append(f"Stima costo:     {_fmt_euro(stima)}")
        if _categoria_bollette(utenza):
            tb = sum(_tot_bollette_anno(utenza, a) for a in anni_presenti)
            out.append(f"Bollette:        {_fmt_euro(tb) if tb > 0 else '—'}")
        return "\n".join(out)

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
                    chart_canvas.tag_bind(tag, "<Enter>", lambda e, u=utenza, l=label: _tt_show(e, tooltip_for(u, l)))
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
