#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import tkinter as tk
from tkinter import ttk

MAX_SINISTRA = 1
MAX_DESTRA = 15
CHIAVE_CONFIG = "icone_barra"

CATALOGO = [
    ("Aggiorna Librerie Python", "aggiorna_librerie_pip", "sync_B"),
    ("Analisi Andamento IA", "analizza_andamento_ia", "sparkles_B"),
    ("Analisi Categorie", "analisi_categorie", "grafico_torta_B"),
    ("Analisi e Bilanci", "popup_scelta_estratto", "report_B"),
    ("Andamento Risparmio", "apri_andamento_risparmio", "grafico_linea_B"),
    ("Apri Manuale", "scarica_manuale", "help_B"),
    ("AutoPark - Veicoli", "veicoli", "veicoli_B"),
    ("Backup e Ripristino", "gestisci_backup_popup", "salva_B"),
    ("Bilancio Anno", "export_anno_dettagliato", "report_B"),
    ("Bilancio Giorno", "export_giorno_forzato", "report_B"),
    ("Bilancio Grafico PDF", "genera_report_pdf", "report_B"),
    ("Bilancio Mese", "export_month_detail", "report_B"),
    ("Bilancio Storico Totale", "export_storico_totale", "report_B"),
    ("Calcolatore Inflazione", "apri_calcolatore_inflazione", "calcolatrice_B"),
    ("Calcolatrice", "apri_calcolatrice", "calcolatrice_B"),
    ("Calcolo Mutuo/Prestiti", "calcolo_mutuo_prestito", "home_B"),
    ("Cambia Password", "apri_cambio_password", "filtri_B"),
    ("Cancella Voci Bulk", "apri_cancella_spese_treeview_unica", "delete_B"),
    ("CasaCare", "manutenzione_casa", "tools_B"),
    ("Cerca Operazioni (finestra)", "cerca_operazioni", "search_B"),
    ("Certificati SSL", "gestisci_certificati", "google_B"),
    ("Chiedi al Database (IA)", "chiedi_ia_database", "sparkles_B"),
    ("Cicla Statistiche", "cicla_visualizzazione_statistiche", "grafico_linea_B"),
    ("CommunityPool", "apri_community_pool", "utenti_B"),
    ("Confronta Periodi", "open_compare_window", "report_B"),
    ("Confronto Bollette IA", "confronta_bollette_ia", "sparkles_B"),
    ("Controlla Aggiornamenti", "forza_check_aggiornamento_con_api", "sync_B"),
    ("Controlla Ricorrenti", "controlla_ricorrenti_manual", "scadenze_B"),
    ("Documenti Contabili", "gestisci_archivi_pdf", "documenti_B"),
    ("Documenti Personali", "gestisci_documenti_personali", "documentiP_B"),
    ("Editor Categorie", "apri_gestione_categorie", "modifica_B"),
    ("Editor Memoria Categorie", "mostra_editor_memoria_categorie", "modifica_B"),
    ("Esporta DB Transazioni", "export_db", "salva_B"),
    ("Estratti per Metodo e Conti", "apri_estratti_metodo", "ccv_B"),
    ("FairShare Dare & Avere", "mostra_dare_avere", "utenti_B"),
    ("Fondo Pensione", "apri_fondo_pensione", "banca_B"),
    ("Fondo Risparmio", "apri_fondo_risparmio", "saldo_B"),
    ("Gamification", "mostra_dettaglio_gamification", "occhio_B"),
    ("Generatore QR e Timer", "launch_qr_svg_generator", "timer_B"),
    ("Gestione Categorie", "mostra_categorie_popup", "tag_B"),
    ("Gestione Ricorrenze", "mostra_ricorrenza_popup", "reset_B"),
    ("Gestione Supermercato", "spesa_supermercato", "spesa_B"),
    ("Gestione Tag #", "apri_gestione_tag", "tag_B"),
    ("Gestione Utenze", "utenze", "luce_B"),
    ("Gestisci Profili Utenti", "mostra_selettore_profilo", "utenti_B"),
    ("Grafici Interattivi", "mostra_analisi_grafici", "grafico_linea_B"),
    ("Hub Moduli (Piramide)", "mostra_piramide", "occhio_B"),
    ("Immobili", "immobil", "home_B"),
    ("Importa DB Transazioni", "import_db", "carica_B"),
    ("Importa Documento AI", "apri_finestra_importa", "carica_B"),
    ("Impostazioni App", "gestisci_configurazione", "filtri_B"),
    ("Info App", "show_info_app", "help_B"),
    ("Interfaccia Web Locale", "apri_webserver", "google_B"),
    ("Lista Ricorrenze", "mostra_lista_ricorrenze", "descrizione_B"),
    ("Log Accessi Web", "mostra_log_accessi", "scadenze_B"),
    ("Log Importazioni", "mostra_log_importazioni", "descrizione_B"),
    ("Manuale CertBot SSL", "scarica_manuale_ssl", "help_B"),
    ("MyBusiness", "apri_studio", "lavoro_B"),
    ("Pannello Controllo (Mancanti)", "calcola_mancanti", "alert_B"),
    ("Pet Care", "animali", "animali_B"),
    ("Pianifica (spese pianificate)", "apri_gestione_spese_pianificate", "calendario_B"),
    ("Piano Dieta", "apri_dieta", "salute_B"),
    ("Portafoglio Bancario", "open_saldo_conto", "saldo_B"),
    ("Portafoglio Investimenti", "apri_portafoglio", "banca_B"),
    ("Promemoria", "gestisci_promemoria", "promemoria_B"),
    ("QR Code Accesso Web", "mostra_qr_popup_label", "qr_B"),
    ("Registra Prodotto", "apri_registrazione", "filtri_B"),
    ("Ricerca rapida movimenti", "_toggle_ricerca_globale", "search_B"),
    ("Riduci a icona", "iconify", "iconizza_B"),
    ("Riepilogo FairShare (periodo)", "mostra_riepilogo_fairshare_periodo", "utenti_B"),
    ("Rubrica", "rubrica_app", "utenti_B"),
    ("Scadenze Mese", "scadenze_mese", "calendario_B"),
    ("Scansiona e salva PDF", "scansiona_e_salva", "scansiona_B"),
    ("Schedulatore Notifiche", "apri_schedulatore", "timer_B"),
    ("Scorciatoie da Tastiera", "mostra_popup_scorciatoie", "tastiera_B"),
    ("Sincronizza Acquisti Email", "avvia_sincronizzazione", "sync_B"),
    ("Stampa", "anteprima_e_stampa_txt", "stampa_B"),
    ("StockBox", "magazzino_app", "documenti_B"),
    ("Storico Aggiornamenti", "visualizza_changelog", "descrizione_B"),
    ("Storico Anomalie", "mostra_registro_errori", "alert_B"),
    ("Suggerisci Categorie", "apri_categorie_suggerite", "tag_B"),
    ("Torna a Oggi", "goto_today", "oggi_B"),
    ("Verifica Moduli (GitHub)", "verifica_moduli_git", "sync_B"),
]

TOOLTIP_SPECIALI = {
    "apri_personalizza_icone": (
        "Tasto destro (qui o su una icona): Editor icone rapide\n"
        "Scegli, ordina e cambia le icone della barra (Ctrl+Shift+C)"
    ),
    "_toggle_ricerca_globale": (
        "Ricerca Globale Movimenti (F3)\nCerca in tutti i movimenti, senza limite di periodo, su:\n"
        "• Data (gg-mm-aaaa, gg/mm/aaaa, aaaa-mm-gg)\n• Categoria e Descrizione\n• Importo (es. 12,50)\n"
        "• Tipo (Entrata / Uscita)\n• Conto e Metodo di pagamento\n• Ora e Hashtag (con o senza #)"
    ),
}

DEFAULT = {
    "sinistra": [
        {"m": "mostra_analisi_grafici", "i": "grafico_linea_B"},
    ],
    "destra": [
        {"m": "_toggle_ricerca_globale", "i": "search_B"},
        {"m": "scadenze_mese", "i": "calendario_B"},
        {"m": "analizza_andamento_ia", "i": "sparkles_B"},
        {"m": "chiedi_ia_database", "i": "sparkles_B"},
        {"m": "chiama_banca", "i": "banca_B"},
        {"m": "gestisci_documenti_personali", "i": "documentiP_B"},
        {"m": "gestisci_archivi_pdf", "i": "documenti_B"},
        {"m": "controlla_ricorrenti_manual", "i": "scadenze_B"},
        {"m": "apri_andamento_risparmio", "i": "grafico_linea_B"},
        {"m": "analisi_categorie", "i": "grafico_torta_B"},
        {"m": "genera_report_pdf", "i": "report_B"},
        {"m": "open_saldo_conto", "i": "saldo_B"},
        {"m": "scarica_manuale", "i": "help_B"},
        {"m": "mostra_popup_scorciatoie", "i": "tastiera_B"},
        {"m": "iconify", "i": "iconizza_B"},
    ],
}

_EXTRA = [("Banca Online", "chiama_banca", "banca_B")]

def _voci():
    return CATALOGO + _EXTRA

def _etichetta(metodo):
    for lab, m, _i in _voci():
        if m == metodo:
            return lab
    return metodo

def _icona_default(metodo):
    for _l, m, i in _voci():
        if m == metodo:
            return i
    return "tools_B"

def _copia_default():
    return {k: [dict(v) for v in lst] for k, lst in DEFAULT.items()}

def _carica(self):
    stato = _copia_default()
    try:
        import __main__ as _app
        with open(_app.CONFIG_FILE, "r", encoding="utf-8") as f:
            dati = json.load(f).get(CHIAVE_CONFIG)
        if not isinstance(dati, dict):
            return stato
        for lato in ("sinistra", "destra"):
            lista = dati.get(lato)
            if isinstance(lista, list):
                stato[lato] = [
                    {"m": str(v["m"]), "i": str(v.get("i") or _icona_default(v["m"]))}
                    for v in lista if isinstance(v, dict) and v.get("m")
                ]
    except Exception as e:
        print(f"Icone barra: configurazione non leggibile, uso i predefiniti ({e})")
    stato["sinistra"] = stato["sinistra"][:MAX_SINISTRA]
    stato["destra"] = stato["destra"][:MAX_DESTRA]
    return stato

def _salva(stato):
    import __main__ as _app
    _app._salva_chiave_config(CHIAVE_CONFIG, stato)

def _emoji(chiave):
    import __main__ as _app
    try:
        return chr(int(dict(_app.MAP_ICONE).get(chiave, ""), 16))
    except Exception:
        return "•"

def _tooltip(metodo):
    if metodo in TOOLTIP_SPECIALI:
        return TOOLTIP_SPECIALI[metodo]
    testo = _etichetta(metodo)
    try:
        from moduli.scorciatoie import etichetta_per_metodo
        tasto = etichetta_per_metodo(metodo)
        if tasto:
            testo += f" ({tasto})"
    except Exception:
        pass
    return testo

def costruisci_barra_icone(self, mode_frame=None):
    if mode_frame is not None:
        self._barra_mode_frame = mode_frame
        mode_frame.bind("<Button-3>", lambda e: self.apri_personalizza_icone())
        if callable(getattr(self, "_add_tt", None)):
            self._add_tt(mode_frame, lambda: _tooltip("apri_personalizza_icone"))
    mf = getattr(self, "_barra_mode_frame", None)
    if mf is None:
        return
    if getattr(self, "_ricerca_globale_aperta", False):
        self._toggle_ricerca_globale()
    for w in getattr(self, "_barra_icone_w", []):
        try:
            w.destroy()
        except Exception:
            pass
    self._barra_icone_w = []
    stato = _carica(self)

    def crea(voce, lato):
        m = voce["m"]
        fn = getattr(self, m, None)
        if not callable(fn):
            return
        chiave = voce.get("i") or _icona_default(m)
        img = self.icone_gui.get(chiave)
        lbl = tk.Label(mf, image=img, text="" if img else _emoji(chiave),
                       bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR, cursor="hand2")
        if lato == "sx":
            lbl.pack(side=tk.LEFT, padx=5, before=self.btn_oggi_stats)
        else:
            lbl.pack(side=tk.RIGHT, anchor="e", padx=(0, 1))
        lbl.bind("<Button-1>", lambda e, f=fn: f())
        lbl.bind("<Button-3>", lambda e: self.apri_personalizza_icone())
        self._add_tt(lbl, _tooltip(m))
        self._barra_icone_w.append(lbl)

    for v in stato["sinistra"]:
        crea(v, "sx")
    for v in reversed(stato["destra"]):
        crea(v, "dx")

def _pulsante(self, parent, testo, icona, comando, bold=False, lato=tk.LEFT, padx=8):
    img = self.icone_gui.get(icona) if icona else None
    lbl = tk.Label(parent, image=img, text=testo, compound="left", cursor="hand2",
                   bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                   font=("Arial", 9, "bold" if bold else "normal"))
    lbl.image = img
    lbl.pack(side=lato, padx=padx)
    lbl.bind("<Button-1>", lambda e: comando())
    return lbl

def _scegli_icona(self, parent, corrente, al_termine):
    import __main__ as _app
    esistente = getattr(self, "_pers_icone_scelta", None)
    try:
        if esistente is not None and esistente.winfo_exists():
            esistente.lift()
            esistente.focus_force()
            return
    except tk.TclError:
        pass
    chiavi = [k for k, _cp in _app.MAP_ICONE]
    win = tk.Toplevel(parent)
    self._pers_icone_scelta = win
    win.bind("<Destroy>", lambda e: setattr(self, "_pers_icone_scelta", None) if e.widget is win else None)
    win.withdraw()
    win.title("Scegli icona")
    win.configure(bg=self.COLOR_TOPLEVEL)
    win.resizable(False, False)
    win.transient(parent)
    win.bind("<Escape>", lambda e: win.destroy())
    cornice = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    cornice.pack(padx=8, pady=8)

    def scelta(k):
        win.destroy()
        al_termine(k)

    for n, k in enumerate(chiavi):
        img = self.icone_gui.get(k)
        b = tk.Label(cornice, image=img, text="" if img else _emoji(k), width=26, height=22,
                     relief="solid" if k == corrente else "flat", bd=1,
                     bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR, cursor="hand2")
        b.grid(row=n // 14, column=n % 14, padx=1, pady=1)
        b.bind("<Button-1>", lambda e, kk=k: scelta(kk))
    annulla = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    annulla.pack(pady=(0, 8))
    _pulsante(self, annulla, " Annulla", "chiudi", win.destroy, bold=True)
    win.update_idletasks()
    w, h = win.winfo_reqwidth(), win.winfo_reqheight()
    x = max(0, parent.winfo_rootx() + (parent.winfo_width() // 2) - (w // 2))
    y = max(0, parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2))
    win.geometry(f"{w}x{h}+{x}+{y}")
    win.deiconify()
    try:
        win.wait_visibility()
        win.grab_set()
    except tk.TclError:
        pass
    win.focus_force()

def apri_personalizza_icone(self, event=None):
    esistente = getattr(self, "_pers_icone_win", None)
    try:
        if esistente is not None and esistente.winfo_exists():
            esistente.deiconify()
            esistente.lift()
            esistente.focus_force()
            return
    except tk.TclError:
        pass

    stato = _carica(self)
    liste = {"sinistra": stato["sinistra"], "destra": stato["destra"]}
    limiti = {"sinistra": MAX_SINISTRA, "destra": MAX_DESTRA}
    attivo = {"lato": "destra"}
    immagini = []

    win = tk.Toplevel(self)
    self._pers_icone_win = win
    win.bind("<Destroy>", lambda e: setattr(self, "_pers_icone_win", None) if e.widget is win else None)
    win.withdraw()
    win.title("Personalizza icone rapide")
    win.configure(bg=self.COLOR_TOPLEVEL)
    win.resizable(False, False)
    win.transient(self)
    win.bind("<Escape>", lambda e: win.destroy())

    def riquadro(genitore, titolo):
        return tk.LabelFrame(genitore, text=f" {titolo} ", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                             font=("Arial", 9, "bold"), bd=1, relief="groove", padx=8, pady=6)

    col_a = riquadro(win, "Funzioni disponibili")
    col_a.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 4), pady=10)
    var_filtro = tk.StringVar()
    ttk.Entry(col_a, textvariable=var_filtro).pack(fill=tk.X, pady=(2, 4))
    tree_cat = ttk.Treeview(col_a, show="tree", selectmode="browse")
    sb_cat = ttk.Scrollbar(col_a, orient="vertical", command=tree_cat.yview)
    tree_cat.configure(yscrollcommand=sb_cat.set)
    sb_cat.pack(side=tk.RIGHT, fill=tk.Y)
    tree_cat.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    immagini_cat = []

    def riempi_cat(*_):
        tree_cat.delete(*tree_cat.get_children())
        immagini_cat.clear()
        f = var_filtro.get().strip().lower()
        for lab, m, _i in sorted(_voci(), key=lambda v: v[0].lower()):
            if not callable(getattr(self, m, None)):
                continue
            if f and f not in lab.lower():
                continue
            chiave = _icona_default(m)
            img = self.icone_gui.get(chiave)
            if img:
                immagini_cat.append(img)
                tree_cat.insert("", "end", iid=m, text=" " + lab, image=img)
            else:
                tree_cat.insert("", "end", iid=m, text=f" {_emoji(chiave)} {lab}")

    var_filtro.trace_add("write", riempi_cat)
    riempi_cat()

    col_b = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    col_b.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 10), pady=10)
    trees = {}
    for lato, titolo, alt in (("sinistra", f"Sinistra (max {MAX_SINISTRA}) - dopo il pulsante carosello", MAX_SINISTRA),
                              ("destra", f"Destra (max {MAX_DESTRA}) - da sinistra a destra", MAX_DESTRA)):
        box = riquadro(col_b, titolo)
        box.pack(fill=tk.BOTH, expand=(lato == "destra"), pady=(0 if lato == "sinistra" else 8, 0))
        t = ttk.Treeview(box, show="tree", selectmode="browse", height=alt)
        if lato == "destra":
            sb = ttk.Scrollbar(box, orient="vertical", command=t.yview)
            t.configure(yscrollcommand=sb.set)
            sb.pack(side=tk.RIGHT, fill=tk.Y)
        t.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        t.bind("<<TreeviewSelect>>", lambda e, l=lato: attivo.update(lato=l))
        trees[lato] = t

    def ridisegna(seleziona=None):
        immagini.clear()
        for lato, t in trees.items():
            t.delete(*t.get_children())
            for n, v in enumerate(liste[lato]):
                img = self.icone_gui.get(v["i"])
                testo = " " + _etichetta(v["m"])
                if img:
                    immagini.append(img)
                    t.insert("", "end", iid=str(n), text=testo, image=img)
                else:
                    t.insert("", "end", iid=str(n), text=f" {_emoji(v['i'])}{testo}")
        if seleziona:
            lato, n = seleziona
            if str(n) in trees[lato].get_children():
                trees[lato].selection_set(str(n))
                attivo["lato"] = lato

    def avviso(testo):
        try:
            self.show_toast(testo)
        except Exception:
            pass

    def aggiungi(lato):
        sel = tree_cat.selection()
        if not sel:
            return
        m = sel[0]
        for l, voci in liste.items():
            for n, v in enumerate(voci):
                if v["m"] == m:
                    ridisegna((l, n))
                    avviso(f"Funzione già presente nella barra ({l}, posizione {n + 1})")
                    return
        if len(liste[lato]) >= limiti[lato]:
            avviso(f"Posti esauriti (max {limiti[lato]}): rimuovi prima un'icona")
            return
        liste[lato].append({"m": m, "i": _icona_default(m)})
        ridisegna((lato, len(liste[lato]) - 1))

    def selezionata():
        lato = attivo["lato"]
        sel = trees[lato].selection()
        if not sel:
            return None, None
        return lato, int(sel[0])

    def rimuovi():
        lato, n = selezionata()
        if lato is None:
            return
        del liste[lato][n]
        ridisegna()

    def sposta(delta):
        lato, n = selezionata()
        if lato is None:
            return
        j = n + delta
        if 0 <= j < len(liste[lato]):
            liste[lato][n], liste[lato][j] = liste[lato][j], liste[lato][n]
            ridisegna((lato, j))

    def cambia_icona():
        lato, n = selezionata()
        if lato is None:
            return

        def fatto(k):
            liste[lato][n]["i"] = k
            ridisegna((lato, n))
        _scegli_icona(self, win, liste[lato][n]["i"], fatto)

    def ripristina():
        d = _copia_default()
        liste["sinistra"][:] = d["sinistra"]
        liste["destra"][:] = d["destra"]
        ridisegna()

    def salva():
        try:
            _salva({"sinistra": liste["sinistra"], "destra": liste["destra"]})
        except Exception as e:
            avviso(f"Impossibile salvare le icone: {e}")
            return
        win.destroy()
        self.costruisci_barra_icone()
        avviso("Icone rapide aggiornate")

    barra = tk.Frame(col_b, bg=self.COLOR_TOPLEVEL)
    barra.pack(fill=tk.X, pady=(8, 0))
    for testo, ico, cmd in ((" A sinistra", "aggiungi", lambda: aggiungi("sinistra")),
                            (" A destra", "aggiungi", lambda: aggiungi("destra")),
                            (" Rimuovi", "cancella", rimuovi), ("▲", None, lambda: sposta(-1)),
                            ("▼", None, lambda: sposta(1)), (" Cambia icona", "modifica", cambia_icona)):
        _pulsante(self, barra, testo, ico, cmd, padx=5)
    tree_cat.bind("<Double-1>", lambda e: aggiungi("destra"))

    fondo = tk.Frame(col_b, bg=self.COLOR_TOPLEVEL)
    fondo.pack(fill=tk.X, pady=(10, 0))
    _pulsante(self, fondo, " Ripristina predefinite", "reset", ripristina, padx=0)
    _pulsante(self, fondo, " Annulla", "chiudi", win.destroy, lato=tk.RIGHT, padx=(10, 0))
    _pulsante(self, fondo, " Salva", "salva", salva, bold=True, lato=tk.RIGHT, padx=(10, 0))

    ridisegna()
    larghezza, altezza = 860, 630
    x = max(0, self.winfo_rootx() + (self.winfo_width() // 2) - (larghezza // 2))
    y = max(0, self.winfo_rooty() + (self.winfo_height() // 2) - (altezza // 2))
    win.geometry(f"{larghezza}x{altezza}+{x}+{y}")
    win.deiconify()
    win.lift()
    win.focus_force()
