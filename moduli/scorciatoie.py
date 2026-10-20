#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import datetime
import tkinter as tk
from tkinter import filedialog

# Schema:
#   Ctrl+lettera        azioni principali e strumenti quotidiani
#   Alt+lettera         moduli (casa, lavoro, finanze extra) ed export
#   Ctrl+Shift+lettera  categorie, dati, backup, web e sistema
#   F1..F11             aiuto, ricerca, impostazioni, hub, form movimenti
# Ogni voce: (sequenza Tk, etichetta, metodo dell'app, descrizione)

SCORCIATOIE_GRUPPI = [
    ("Generali", [
        ("<F1>",              "F1",           "mostra_popup_scorciatoie", "Scorciatoie"),
        ("<F3>",              "F3",           "_toggle_ricerca_globale",  "Ricerca Globale"),
        ("<F4>",              "F4",           "gestisci_configurazione",  "Impostazioni"),
        ("<Control-Shift-C>", "Ctrl+Shift+C", "apri_personalizza_icone",  "Personalizza Icone"),
        ("<F5>",              "F5",           "goto_today",               "Torna a Oggi"),
        ("<F6>",              "F6",           "mostra_piramide",          "Hub Moduli"),
        ("<F11>",             "F11",          "cicla_visualizzazione_statistiche", "Cicla Statistiche"),
        ("<Control-m>",       "Ctrl+M",       "scarica_manuale",          "Manuale"),
        ("<Control-i>",       "Ctrl+I",       "show_info_app",            "Info App"),
        ("<Control-x>",       "Ctrl+X",       "iconify",                  "Iconizza"),
        ("<Control-q>",       "Ctrl+Q",       "_on_close",                "Esci"),
    ]),
    ("Movimenti", [
        ("<Control-f>",       "Ctrl+F",       "cerca_operazioni",         "Cerca Operaz."),
        ("<Control-n>",       "Ctrl+N",       "open_compare_window",      "Confronto Dati"),
        ("<Control-a>",       "Ctrl+A",       "apri_fondo_risparmio",     "Stat. Annuali"),
        ("<Control-z>",       "Ctrl+Z",       "calcola_mancanti",         "Mancanti"),
        ("<F7>",              "F7",           "mostra_spese_simili",      "Spese Simili"),
        ("<F8>",              "F8",           "avvia_modifica_da_selezione", "Modifica Selezione"),
        ("<F9>",              "F9",           "avvia_spalma_da_selezione",   "Spalma Selezione"),
        (None,                "F2 / Ctrl+Shift+O", None,                  "Apri Allegato (su riga)"),
        ("<Control-b>",       "Ctrl+B",       "apri_finestra_importa",    "Importa AI"),
        ("<Control-Shift-G>", "Ctrl+Shift+G", "avvia_sincronizzazione",   "Sync Gmail"),
        ("<Control-Shift-L>", "Ctrl+Shift+L", "mostra_log_importazioni",  "Log Importazioni"),
        ("<Control-Shift-H>", "Ctrl+Shift+H", "apri_gestione_tag",        "Gestione Tag"),
        ("<Control-Shift-M>", "Ctrl+Shift+M", "apri_estratti_metodo",     "Estratti per Metodo"),
        ("<Control-Shift-D>", "Ctrl+Shift+D", "apri_cancella_spese_treeview_unica", "Elimina Multiple"),
    ]),
    ("Finanze", [
        ("<Control-s>",       "Ctrl+S",       "open_saldo_conto",         "Portafoglio Bancario"),
        ("<Alt-b>",           "Alt+B",        "chiama_banca",             "Banca Online"),
        ("<Alt-t>",           "Alt+T",        "apri_portafoglio",         "Investimenti"),
        ("<Alt-f>",           "Alt+F",        "apri_gestione_spese_pianificate", "Spese Pianificate"),
        ("<Control-o>",       "Ctrl+O",       "calcolo_mutuo_prestito",   "Mutuo/Prestito"),
        ("<Control-d>",       "Ctrl+D",       "mostra_dare_avere",        "FairShare"),
        ("<Alt-o>",           "Alt+O",        "apri_community_pool",     "CommunityPool"),
        ("<Alt-y>",           "Alt+Y",        "apri_calcolatore_inflazione", "Inflazione"),
        ("<Control-e>",       "Ctrl+E",       "apri_calcolatrice",        "Calcolatrice"),
    ]),
    ("Ricorrenze e Scadenze", [
        ("<Control-t>",       "Ctrl+T",       "mostra_ricorrenza_popup",  "Nuova Ricorr."),
        ("<Control-l>",       "Ctrl+L",       "mostra_lista_ricorrenze",  "Lista Ricorr."),
        ("<Control-j>",       "Ctrl+J",       "scadenze_mese",            "Scadenze Mese"),
        ("<Control-Shift-J>", "Ctrl+Shift+J", "controlla_ricorrenti_manual", "Controlla Ricorr."),
        ("<Control-y>",       "Ctrl+Y",       "gestisci_promemoria",      "Promemoria"),
    ]),
    ("Analisi e Report", [
        ("<Alt-h>",           "Alt+H",        "mostra_analisi_grafici",   "Analisi Grafici"),
        ("<Control-k>",       "Ctrl+K",       "analisi_categorie",        "Analisi Cat."),
        ("<Alt-e>",           "Alt+E",        "popup_scelta_estratto",    "Analisi e Bilanci"),
        ("<Alt-j>",           "Alt+J",        "export_giorno_forzato",    "Export Giorno"),
        ("<Alt-k>",           "Alt+K",        "export_month_detail",      "Export Mese"),
        ("<Alt-l>",           "Alt+L",        "export_anno_dettagliato",  "Export Anno"),
        ("<Alt-g>",           "Alt+G",        "export_storico_totale",    "Export Storico"),
        ("<Alt-r>",           "Alt+R",        "genera_report_pdf",        "Report PDF"),
        ("<Control-p>",       "Ctrl+P",       "anteprima_e_stampa_txt",   "Stampa TXT"),
        ("<Control-h>",       "Ctrl+H",       "chiedi_ia_database",       "Chiedi IA"),
        ("<Control-Shift-Y>", "Ctrl+Shift+Y", "analizza_andamento_ia",    "Bilancio IA"),
    ]),
    ("Categorie", [
        ("<Control-Shift-K>", "Ctrl+Shift+K", "apri_categorie_suggerite", "Suggerim. Cat."),
        ("<Control-Shift-T>", "Ctrl+Shift+T", "mostra_categorie_popup",   "Popup Cat."),
        ("<Control-Shift-S>", "Ctrl+Shift+S", "apri_gestione_categorie",  "Editor Cat."),
        ("<Control-Shift-E>", "Ctrl+Shift+E", "mostra_editor_memoria_categorie", "Regole Cat."),
    ]),
    ("Moduli Casa e Lavoro", [
        ("<Control-u>",       "Ctrl+U",       "utenze",                   "Utenze"),
        ("<Control-r>",       "Ctrl+R",       "rubrica_app",              "Rubrica"),
        ("<Alt-s>",           "Alt+S",        "spesa_supermercato",       "Lista Spesa"),
        ("<Alt-a>",           "Alt+A",        "gestisci_archivi_pdf",     "Archivio Contabile"),
        ("<Alt-p>",           "Alt+P",        "gestisci_documenti_personali", "Doc. Personali"),
        ("<Alt-i>",           "Alt+I",        "immobil",                  "Immobili"),
        ("<Alt-v>",           "Alt+V",        "veicoli",                  "Veicoli"),
        ("<Alt-n>",           "Alt+N",        "animali",                  "Pet Care"),
        ("<Alt-c>",           "Alt+C",        "manutenzione_casa",        "Casa Care"),
        ("<Alt-m>",           "Alt+M",        "magazzino_app",            "StockBox"),
        ("<Alt-u>",           "Alt+U",        "apri_studio",              "MyBusiness"),
        ("<Alt-d>",           "Alt+D",        "apri_dieta",               "Dieta"),
        ("<Alt-x>",           "Alt+X",        "apri_schedulatore",        "Schedulatore"),
        ("<Alt-z>",           "Alt+Z",        "scansiona_e_salva",        "Scansiona"),
        ("<Alt-q>",           "Alt+Q",        "launch_qr_svg_generator",  "QR e Timer"),
    ]),
    ("Dati e Sistema", [
        ("<Control-Shift-B>", "Ctrl+Shift+B", "gestisci_backup_popup",    "Backup"),
        ("<Control-Shift-X>", "Ctrl+Shift+X", "export_db",                "Esporta Dati"),
        ("<Control-Shift-I>", "Ctrl+Shift+I", "import_db",                "Importa Dati"),
        ("<Control-Shift-W>", "Ctrl+Shift+W", "apri_webserver",           "Web Server"),
        ("<Control-Shift-Q>", "Ctrl+Shift+Q", "mostra_qr_popup_label",    "QR Accesso Web"),
        ("<Control-Shift-P>", "Ctrl+Shift+P", "mostra_selettore_profilo", "Profili"),
        ("<Control-Shift-U>", "Ctrl+Shift+U", "forza_check_aggiornamento_con_api", "Aggiornamenti"),
        ("<Control-Shift-R>", "Ctrl+Shift+R", "mostra_registro_errori",   "Registro Errori"),
    ]),
]

SCORCIATOIE = [v for _t, voci in SCORCIATOIE_GRUPPI for v in voci if v[0] and v[2]]

SCORCIATOIA_ESC = ("Esc", "Chiudi")

SCORCIATOIE_LOCALI = {
    "apri_allegato":    (("<F2>", "<Control-Shift-O>", "<Control-Shift-o>"), "F2 o Ctrl+Shift+O"),
}

def tasti_locali(nome):
    return SCORCIATOIE_LOCALI[nome][0]

def etichetta_locale(nome):
    return SCORCIATOIE_LOCALI[nome][1]

def lega_locale(widget, nome, funzione, add=None):
    for seq in tasti_locali(nome):
        if add:
            widget.bind(seq, funzione, add=add)
        else:
            widget.bind(seq, funzione)

def etichetta_per_metodo(nome):
    """Restituisce la scorciatoia globale (es. 'Alt+S') assegnata al metodo dell'app, o ''."""
    for _k, label, metodo, _d in SCORCIATOIE:
        if metodo == nome:
            return label
    return ""

def configura_scorciatoie(self):
    visti = {}
    for tk_key, _label, metodo_nome, _descr in SCORCIATOIE:
        if tk_key in visti:
            print(f"[Scorciatoie] Tasto duplicato {tk_key}: {visti[tk_key]} / {metodo_nome}")
            continue
        visti[tk_key] = metodo_nome
        try:
            metodo = getattr(self, metodo_nome)
        except AttributeError:
            print(f"[Scorciatoie] Metodo non trovato: {metodo_nome} ({tk_key})")
            continue
        self.bind_all(tk_key, lambda e, f=metodo: f())
        # Con Caps Lock attivo Tk riceve la lettera minuscola: lega anche quella variante
        if "Shift-" in tk_key:
            ultimo = tk_key[-2]
            if ultimo.isalpha() and ultimo.isupper():
                self.bind_all(tk_key[:-2] + ultimo.lower() + ">", lambda e, f=metodo: f())

def _gruppi_visualizzati():
    gruppi = [(t, list(v)) for t, v in SCORCIATOIE_GRUPPI]
    gruppi[0][1].append((None, SCORCIATOIA_ESC[0], None, SCORCIATOIA_ESC[1]))
    return gruppi

def _testo_scorciatoie():
    righe = ["SCORCIATOIE DA TASTIERA", f"Generato il {datetime.date.today():%d-%m-%Y}", ""]
    for titolo, voci in _gruppi_visualizzati():
        righe.append(titolo.upper())
        righe.append("-" * len(titolo))
        for _k, label, _m, descr in voci:
            righe.append(f"  {label:<20} {descr}")
        righe.append("")
    return "\n".join(righe)

def _cartella_export():
    try:
        import __main__ as _app
        return getattr(_app, "EXPORT_FILES", None) or os.path.expanduser("~")
    except Exception:
        return os.path.expanduser("~")

def _scorciatoie_esporta_txt(self, parent=None):
    dest = filedialog.asksaveasfilename(
        defaultextension=".txt", filetypes=[("File di testo", "*.txt")],
        initialdir=_cartella_export(),
        initialfile=f"Scorciatoie_{datetime.date.today():%d-%m-%Y}.txt",
        confirmoverwrite=False, title="Esporta Scorciatoie TXT", parent=parent)
    if not dest:
        return
    if os.path.exists(dest) and not self.show_custom_askyesno(
            "Sovrascrivere file?", f"Il file '{os.path.basename(dest)}' \nesiste già. Vuoi sovrascriverlo?"):
        return
    try:
        with open(dest, "w", encoding="utf-8") as f:
            f.write(_testo_scorciatoie())
        self.show_toast(f"TXT salvato: {os.path.basename(dest)}")
    except Exception as e:
        self.show_custom_warning("Errore", f"Impossibile esportare il file: {e}")

def _scorciatoie_genera_pdf(self, dest):
    try:
        import pymupdf as fitz
    except ImportError:
        self.show_custom_warning("Libreria mancante",
            "PyMuPDF non è installato.\nVai in Sistema → Aggiorna Librerie Python.")
        return None
    try:
        doc = fitz.open()
        W, H = 842, 595                      # A4 orizzontale
        ML, MT, MB = 30, 30, 30
        N_COL = 3
        COL_W = (W - 2 * ML) / N_COL
        LH, X_DESCR = 11.5, 100
        BLU, VERDE, GRIGIO = (0.15, 0.35, 0.65), (0.10, 0.42, 0.18), (0.45, 0.45, 0.45)
        pagina = None
        col, y = 0, 0

        def nuova_pagina():
            nonlocal pagina, col, y
            pagina = doc.new_page(width=W, height=H)
            col, y = 0, MT
            if len(doc) == 1:
                pagina.insert_text((ML, y + 12), "SCORCIATOIE DA TASTIERA", fontname="hebo", fontsize=14, color=BLU)
                pagina.insert_text((W - ML - 110, y + 12), f"{datetime.date.today():%d-%m-%Y}",
                                   fontname="helv", fontsize=9, color=GRIGIO)
                y += 30

        nuova_pagina()
        for titolo, voci in _gruppi_visualizzati():
            altezza = LH * (len(voci) + 1) + 8
            if y + altezza > H - MB:
                col += 1
                y = MT + (30 if len(doc) == 1 else 0)
                if col >= N_COL:
                    nuova_pagina()
            x = ML + col * COL_W
            pagina.insert_text((x, y + 9), titolo, fontname="hebo", fontsize=9.5, color=BLU)
            pagina.draw_line((x, y + 12), (x + COL_W - 14, y + 12), color=BLU, width=0.5)
            yy = y + 12 + LH
            for _k, label, _m, descr in voci:
                pagina.insert_text((x, yy), label, fontname="cobo", fontsize=8, color=VERDE)
                pagina.insert_text((x + X_DESCR, yy), descr, fontname="helv", fontsize=8.5, color=(0, 0, 0))
                yy += LH
            y = yy + 8
        doc.save(dest)
        doc.close()
        return dest
    except Exception as e:
        self.show_custom_warning("Errore PDF", f"Impossibile creare il PDF: {e}")
        return None

def _scorciatoie_esporta_pdf(self, parent=None):
    dest = filedialog.asksaveasfilename(
        defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
        initialdir=_cartella_export(),
        initialfile=f"Scorciatoie_{datetime.date.today():%d-%m-%Y}.pdf",
        confirmoverwrite=False, title="Esporta Scorciatoie PDF", parent=parent)
    if not dest:
        return
    if os.path.exists(dest) and not self.show_custom_askyesno(
            "Sovrascrivere file?", f"Il file '{os.path.basename(dest)}' \nesiste già. Vuoi sovrascriverlo?"):
        return
    if _scorciatoie_genera_pdf(self, dest):
        self.show_toast(f"PDF salvato: {os.path.basename(dest)}")

def _scorciatoie_stampa(self):
    import tempfile
    tmp = os.path.join(tempfile.gettempdir(), "scorciatoie_stampa.pdf")
    try:
        import pymupdf  # noqa: F401
        if _scorciatoie_genera_pdf(self, tmp):
            self.stampa_pdf(tmp, self.show_custom_warning)
            return
    except ImportError:
        pass
    self._stampa_lista_diretta(_testo_scorciatoie(), self.show_custom_warning)

def mostra_popup_scorciatoie(self, event=None):
    if hasattr(self, '_scorciatoie_popup') and self._scorciatoie_popup and self._scorciatoie_popup.winfo_exists():
        self._scorciatoie_popup.lift()
        self._scorciatoie_popup.focus_force()
        return
    popup = tk.Toplevel(self)
    self._scorciatoie_popup = popup
    popup.bind("<Destroy>", lambda e: setattr(self, '_scorciatoie_popup', None) if e.widget is popup else None)
    popup.title("Scorciatoie")
    popup.withdraw()
    popup.configure(background=self.COLOR_WIDGET_BG)
    popup.resizable(False, False)
    popup.transient(self)
    popup.bind("<Escape>", lambda e: popup.destroy())
    tk.Label(popup, text="⌨️ SHORTCUT RAPIDI", font=("Arial", 11, "bold"),
             foreground="#61AFEF", background=self.COLOR_WIDGET_BG).pack(pady=(8, 4))
    main_container = tk.Frame(popup, background=self.COLOR_WIDGET_BG)
    main_container.pack(fill="both", expand=True, padx=16)

    N_COL = 4
    colonne = []
    for c in range(N_COL):
        f = tk.Frame(main_container, background=self.COLOR_WIDGET_BG)
        f.grid(row=0, column=c, sticky="n", padx=8)
        colonne.append(f)

    gruppi = _gruppi_visualizzati()
    # distribuzione bilanciata: i gruppi più lunghi per primi nella colonna meno piena
    righe = [0] * N_COL
    assegna = [[] for _ in range(N_COL)]
    for idx in sorted(range(len(gruppi)), key=lambda i: -len(gruppi[i][1])):
        c = righe.index(min(righe))
        assegna[c].append(idx)
        righe[c] += len(gruppi[idx][1]) + 1
    for c, indici in enumerate(assegna):
        for idx in sorted(indici):
            titolo, voci = gruppi[idx]
            box = tk.Frame(colonne[c], background=self.COLOR_WIDGET_BG)
            box.pack(anchor="w", fill="x", pady=(0, 5))
            tk.Label(box, text=titolo, font=("Arial", 9, "bold"), foreground="#61AFEF",
                     background=self.COLOR_WIDGET_BG, anchor="w").grid(row=0, column=0, columnspan=2, sticky="w")
            for r, (_tk_key, label, _metodo, descr) in enumerate(voci, start=1):
                tk.Label(box, text=label, font=("Consolas", 9, "bold"), foreground="#98C379",
                         background=self.COLOR_WIDGET_BG, anchor="e").grid(row=r, column=0, padx=(0, 6), pady=0, sticky="e")
                tk.Label(box, text=descr, font=("Arial", 9), foreground=self.TEXT_COLOR,
                         background=self.COLOR_WIDGET_BG, anchor="w").grid(row=r, column=1, pady=0, sticky="w")

    barra = tk.Frame(popup, background=self.COLOR_WIDGET_BG)
    barra.pack(pady=(2, 8))

    def _pulsante(testo, icona, comando, bold=False):
        img = self.icone_gui.get(icona)
        lbl = tk.Label(barra, image=img, text=testo, compound="left", cursor="hand2",
                       background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                       font=("Arial", 9, "bold" if bold else "normal"))
        lbl.image = img
        lbl.pack(side="left", padx=14)
        lbl.bind("<Button-1>", lambda e: comando())
        return lbl

    _pulsante(" Esporta TXT", "salva", lambda: _scorciatoie_esporta_txt(self, popup))
    _pulsante(" Esporta PDF", "salva", lambda: _scorciatoie_esporta_pdf(self, popup))
    _pulsante(" Stampa", "stampa", lambda: _scorciatoie_stampa(self))
    _pulsante(" Chiudi", "chiudi", popup.destroy, bold=True)

    popup.update_idletasks()
    w = min(popup.winfo_reqwidth(), popup.winfo_screenwidth() - 20, 1366)
    h = min(popup.winfo_reqheight(), popup.winfo_screenheight() - 60, 630)
    x = max(0, self.winfo_x() + (self.winfo_width() // 2) - (w // 2))
    y = max(0, self.winfo_y() + (self.winfo_height() // 2) - (h // 2))
    popup.geometry(f"{w}x{h}+{x}+{y}")
    popup.deiconify()
    popup.wait_visibility()
    popup.focus_force()
