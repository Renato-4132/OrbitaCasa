#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import shutil
import subprocess
import sys

import tkinter as tk
from tkinter import ttk

FS_PARTECIPANTI = "#fairshare-partecipanti"
FS_PAGAMENTI = "#fairshare-pagamenti"
PIANI = "#pianificate"
BUDGET = "#budget-categorie"
TARGET = "#target-spesa"
A_CALDO = (BUDGET, TARGET, PIANI, FS_PARTECIPANTI, FS_PAGAMENTI)
CHIAVI_BUDGET = ("budget_categorie", "budget_annuale_categorie")
CHIAVI_TARGET = ("target_mese", "target_anno")

def _leggi_db_fairshare(db_file):
    with open(db_file, "r", encoding="utf-8") as f:
        return json.load(f)

def _scrivi_json_atomico(db_file, dati, indent=2):
    tmp = db_file + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dati, f, indent=indent, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, db_file)

def _contenitori_budget(dati):
    cont = []
    if isinstance(dati, dict):
        if any(k in dati for k in CHIAVI_BUDGET):
            cont.append(dati)
        for v in dati.values():
            if isinstance(v, dict) and any(k in v for k in CHIAVI_BUDGET):
                cont.append(v)
    return cont

def _testo_budget(percorso):
    try:
        dati = _leggi_db_fairshare(percorso.split("#", 1)[0])
    except Exception:
        return "—"
    cats = set()
    for c in _contenitori_budget(dati):
        for k in CHIAVI_BUDGET:
            for cat, v in (c.get(k) or {}).items():
                try:
                    if float(v) > 0:
                        cats.add(str(cat).strip().lower())
                except (TypeError, ValueError):
                    pass
    return f"{len(cats)} {'categoria' if len(cats) == 1 else 'categorie'} con budget"

def _testo_target(percorso):
    try:
        cfg = _leggi_db_fairshare(percorso.split("#", 1)[0])
    except Exception:
        return "—"
    vals = []
    for k in CHIAVI_TARGET:
        try:
            vals.append(float(cfg.get(k, 0) or 0))
        except (TypeError, ValueError):
            vals.append(0.0)
    if not any(v > 0 for v in vals):
        return "non impostati"
    return f"mese € {vals[0]:.2f} · anno € {vals[1]:.2f}".replace(".", ",")

def _azzera_budget(percorso):
    db_file = percorso.split("#", 1)[0]
    if not os.path.exists(db_file):
        return
    dati = _leggi_db_fairshare(db_file)
    for c in _contenitori_budget(dati):
        for k in CHIAVI_BUDGET:
            if k in c:
                c[k] = {}
    _scrivi_json_atomico(db_file, dati)

def _azzera_target(percorso):
    cfg_file = percorso.split("#", 1)[0]
    if not os.path.exists(cfg_file):
        return
    cfg = _leggi_db_fairshare(cfg_file)
    for k in CHIAVI_TARGET:
        cfg[k] = 0
    _scrivi_json_atomico(cfg_file, cfg, indent=4)

def _conta_fairshare(percorso):
    db_file = percorso.split("#", 1)[0]
    try:
        dati = _leggi_db_fairshare(db_file)
    except Exception:
        return None
    if percorso.endswith(PIANI):
        return len((dati.get("pianificate") or {}).get("piani", []))
    if percorso.endswith(FS_PARTECIPANTI):
        return len((dati.get("fairshare") or {}).get("partecipanti", []))
    return sum(1 for g in dati.get("spese", []) if isinstance(g, dict)
               for e in g.get("entries", []) if isinstance(e, dict) and e.get("fairshare"))

def _azzera_fairshare(percorso):
    db_file = percorso.split("#", 1)[0]
    if not os.path.exists(db_file):
        return
    dati = _leggi_db_fairshare(db_file)
    if percorso.endswith(PIANI):
        dati["pianificate"] = {"piani": []}
    elif percorso.endswith(FS_PARTECIPANTI):
        gestore = (dati.get("fairshare") or {}).get("gestore_partecipa", True)
        dati["fairshare"] = {"gestore_partecipa": gestore, "partecipanti": []}
    else:
        for g in dati.get("spese", []):
            if isinstance(g, dict):
                for e in g.get("entries", []):
                    if isinstance(e, dict):
                        e.pop("fairshare", None)
    tmp = db_file + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(dati, f, indent=2, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, db_file)

def _elenco_file_variabili(_app):

    def g(nome):
        return getattr(_app, nome, None)
    voci_raw = [
        ("Movimenti, Categorie e Ricorrenze", "Spese, entrate, categorie personalizzate, ricorrenze, budget e FairShare (partecipanti e pagamenti) (spese_db.json)", "DB_FILE", False),
        ("Rubrica Contatti",                  "Contatti salvati in rubrica (rubrica.json)", "DATI_FILE", False),
        ("Utenze e Bollette",                 "Utenze domestiche e relative bollette (utenze_db.json)", "UTENZE_DB", False),
        ("Archivio Documenti (indice)",       "Indice dei documenti PDF/immagini archiviati (documenti_archiviati.json)", "REGISTRY_FILE", False),
        ("Documenti Archiviati (file)",       "Cartella con i PDF/immagini archiviati fisicamente", "DOC_DIR", True),
        ("Documenti Personali (file)",        "Cartella documenti personali (carte, certificati, ecc.)", "DOC_PERS_DIR", True),
        ("Fatture Esportate",                 "Cartella con le fatture esportate", "EXPORT_FATTURE_DIR", True),
        ("Portafoglio Bancario",              "Conti, movimenti e trasferimenti bancari (portafoglio_db.json)", "PORTAFOGLIO_BANCARIO", False),
        ("Portafoglio Investimenti",          "Portafoglio azionario e storico investimenti (portafoglio.json)", "PORTAFOGLIO_AZIONI", False),
        ("Prezzi Supermercati",               "Prezzi salvati dal modulo Supermercati (supermercati.json)", "SUPERMERCATI_DB", False),
        ("Memoria Categorie IA (SmartCat)",   "Associazioni descrizione → categoria apprese (memoria_categorie.json)", "MEM_CAT", False),
        ("Promemoria",                        "Promemoria e scadenze impostate (promemoria.json)", "PROMEMORIA_FILE", False),
        ("Traguardi e Badge (Gamification)",  "Streak, punti e badge sbloccati (gamification.json)", "GAMIFICATION_FILE", False),
        ("Aggiornamenti Rimandati",           "Notifiche di aggiornamento posticipate (update.json)", "RIMANDA_FILE", False),
        ("Chiave API Salvata",                "Chiave API (Gemini) salvata in locale (api.json)", "DEFAULT_API", False),
        ("Controllo Fine Mese",               "Stato dei controlli automatici di fine mese (controllo_fm.json)", "CONTROLLO_F_M", False),
        ("Fondo Risparmio",                   "Obiettivi e progressi del fondo risparmio (fondo_risparmio.json)", "FR_FILE", False),
        ("Fondo Pensione",                    "Dati anagrafica, versamenti, valorizzazioni e riscatti del fondo pensione (fondo_pensione.json)", "PENSIONE_FILE", False),
        ("CommunityPool - Collegamenti",      "Collegamenti tra le tue spese e le voci del CommunityPool (communitypool_link.json). Il pool condiviso resta", "COMMUNITY_POOL_LINK_FILE", False),
        ("Piano Dieta",                       "Piano alimentare impostato (dieta_piano.json)", "DIETA_FILE", False),
        ("Alimenti Personalizzati",           "Alimenti custom aggiunti al database dieta (alimenti_custom.json)", "CUSTOM_FILE", False),
        ("Storico Peso",                      "Storico del peso corporeo registrato (peso_storico.json)", "PESO_FILE", False),
        ("Fabbisogno Calorico",               "Dati per il calcolo del fabbisogno calorico (fabbisogno_dati.json)", "FABB_FILE", False),
        ("Dati Pedometro",                    "Passi giornalieri registrati (pedometro.json)", "PEDOMETRO_FILE", False),
        ("MyBusiness - Clienti",              "Anagrafica clienti di MyBusiness (studio_clienti.json)", "STUDIO_CLIENTI", False),
        ("MyBusiness - Appuntamenti",         "Calendario appuntamenti di MyBusiness (studio_appuntamenti.json)", "STUDIO_APPUNTAMENTI", False),
        ("MyBusiness - Prestazioni",          "Elenco prestazioni/servizi da MyBusiness (studio_prestazioni.json)", "STUDIO_PRESTAZIONI", False),
        ("MyBusiness - Fatture",              "Fatture emesse da MyBusiness (studio_fatture.json)", "STUDIO_FATTURE", False),
        ("MyBusiness - Dati Emittente",       "Dati anagrafici/fiscali dell'emittente (studio_emittente.json)", "STUDIO_EMITTENTE", False),
        ("MyBusiness - Cassa",                "Registro di cassa di MyBusiness (studio_cassa.json)", "STUDIO_CASSA", False),
        ("MyBusiness - Magazzino",            "Inventario magazzino di MyBusiness (studio_magazzino.json)", "STUDIO_MAGAZZINO", False),
        ("ImmoBil ",                          "Elenco immobili gestiti (immobil.json)", "IMMOBIL_FILE", False),
        ("AutoPark",                          "Veicoli, scadenze e registro movimenti (veicoli.json)", "VEICOLI_FILE", False),
        ("Pet Care",                          "Anagrafica animali, spese e scadenze (animali.json)", "ANIMALI_FILE", False),
        ("StockBox",                          "Articoli, scorte e movimenti del magazzino (magazzino.json)", "MAGAZZINO_FILE", False),
        ("Scanner",                           "Impostazioni della finestra di scansione: ultimo scanner, scanner di rete salvati, risoluzione, colore, sorgente", "SCANNER_FILE", False),
        ("Casa Care",                         "Manutenzione e Risparmio Casa (manutenzione_casa.json)", "MANUTENZIONE_CASA_FILE", False),
        ("Schedulatore Email",                "Regole dello schedulatore email (schedule.json)", "SCHEDULE_FILE", False),
        ("Password di Accesso",               "Password impostata per l'accesso all'app (password.json)", "PW_FILE", False),
        ("Configurazione Generale",           "⚠ Tema, soglie e opzioni dell'app, incluse le impostazioni di rete (config.json)", "CONFIG_FILE", False),
        ("Cartella Export",                   "File esportati manualmente (PDF/CSV/estratti)", "EXPORT_FILES", True),
        ("Log Importazioni",                  "Registro delle operazioni di importazione (log_importazioni.txt)", "LOG_IMPORTAZIONI", False),
        ("Login Web - Accessi Riusciti",      "Storico dei login riusciti dall'interfaccia web (login_web.json)", "LOGIN_WEB", False),
        ("Login Web - Accessi Falliti",       "Storico dei tentativi di login falliti dal web (login_web_fail.json)", "LOGIN_WEB_FAIL", False),
        ("Login Web - Passkey / WebAuthn",    "Credenziali passkey/WebAuthn salvate (webauthn_credentials.json)", "CREDENTIALS_FILE", False),
        ("Login Locale",                      "Storico degli accessi dall'app desktop (login_lcl.json)", "LOGIN_LCL", False),
        ("Controllo Accessi Web",             "Whitelist/blacklist IP per l'accesso web (web_access_control.json)", "ACCESS_CONTROL_WEB", False),
        ("Messaggi di Servizio (Visti)",      "Elenco degli ID dei messaggi di servizio già letti: azzerandolo, tutti i messaggi ancora validi verranno rinotificati (messaggi_servizio_visti.json)", "MESSAGGI_VISTI_FILE", False),
    ]
    voci = []
    for etichetta, descrizione, nome_costante, is_dir in voci_raw:
        percorso = g(nome_costante)
        if percorso:
            voci.append((etichetta, descrizione, percorso, is_dir))
            if nome_costante == "DB_FILE":
                voci.append(("FairShare - Partecipanti",
                             "Elenco partecipanti e opzione gestore (dentro spese_db.json). Movimenti e pagamenti restano",
                             percorso + FS_PARTECIPANTI, False))
                voci.append(("FairShare - Pagamenti",
                             "Stato dei pagamenti segnati sulle spese condivise (dentro spese_db.json). Movimenti e partecipanti restano",
                             percorso + FS_PAGAMENTI, False))
                voci.append(("Spese Pianificate",
                             "Piani di accantonamento per spese future (dentro spese_db.json). Movimenti e il resto restano",
                             percorso + PIANI, False))
                voci.append(("Budget per Categoria",
                             "Limiti di spesa mensili e annuali delle categorie (dentro spese_db.json). Movimenti e categorie restano",
                             percorso + BUDGET, False))
                if g("CONFIG_FILE"):
                    voci.append(("Target di Spesa",
                                 "Target mese e Target anno impostati in Configurazione (dentro config.json). Il resto della configurazione resta",
                                 g("CONFIG_FILE") + TARGET, False))

    DB_DIR = g("DB_DIR")
    BASE_DIR = g("BASE_DIR")
    if DB_DIR:
        voci.extend([
            ("Log Errori Applicativi",       "Registro degli errori dell'app (error_log.txt)", os.path.join(DB_DIR, "error_log.txt"), False),
            ("Cache Risorse/Icone",          "Icone e risorse scaricate in cache: verranno riscaricate al riavvio", os.path.join(DB_DIR, "resources"), True),
            ("CommunityPool - Novità viste", "Data dell'ultimo accesso al CommunityPool: azzerandola, le novità ripartono da zero (communitypool_visto.json)", os.path.join(DB_DIR, "communitypool_visto.json"), False),
            ("Profilo Utente Dieta",         "Utente attivo selezionato nel modulo Dieta (utente_attivo.json)", os.path.join(DB_DIR, "utente_attivo.json"), False),
            ("Profili Dieta Salvati",        "Cartella con i profili utente del modulo Dieta", os.path.join(DB_DIR, "utenti"), True),
            ("Certificato SSL",              "Certificato/chiave HTTPS del server locale: si rigenera da sola al riavvio (cert.pem/key.pem)", _app.SSL_CERT, False),
        ])
    if BASE_DIR:
        voci.extend([
            ("Cartella Backup", "Backup e snapshot creati manualmente o automaticamente", os.path.join(BASE_DIR, "backup"), True),
            ("Cartella Moduli", "Cartella contenente i moduli e i componenti aggiuntivi", os.path.join(BASE_DIR, "moduli"), True)
            
        ])
    return voci

def _dimensione_leggibile(percorso, is_dir):
    if percorso.endswith(BUDGET):
        return _testo_budget(percorso)
    if percorso.endswith(TARGET):
        return _testo_target(percorso)
    if percorso.endswith((FS_PARTECIPANTI, FS_PAGAMENTI, PIANI)):
        n = _conta_fairshare(percorso)
        if n is None:
            return "—"
        return f"{n} {'partecipanti' if percorso.endswith(FS_PARTECIPANTI) else ('piani' if percorso.endswith(PIANI) else 'spese con pagamenti')}"
    try:
        if is_dir:
            if not os.path.isdir(percorso):
                return "—"
            tot = 0
            for root, _dirs, files in os.walk(percorso):
                for f in files:
                    try:
                        tot += os.path.getsize(os.path.join(root, f))
                    except OSError:
                        pass
        else:
            if not os.path.exists(percorso):
                return "—"
            tot = os.path.getsize(percorso)
    except OSError:
        return "—"
    if tot < 1024:
        return f"{tot} B"
    if tot < 1024 * 1024:
        return f"{tot / 1024:.1f} KB"
    return f"{tot / 1024 / 1024:.2f} MB"

def show_reset_dialog(self):
    import __main__ as _app
    DB_DIR = _app.DB_DIR
    EXPORT_FILES = _app.EXPORT_FILES

    if hasattr(self, '_win_reset_istanza') and self._win_reset_istanza.winfo_exists():
        self._win_reset_istanza.lift()
        self._win_reset_istanza.focus_set()
        return

    voci = _elenco_file_variabili(_app)

    win = tk.Toplevel(self, bg=self.COLOR_BACKGROUND)
    self._win_reset_istanza = win
    win.withdraw()
    win.title("Reset Dati")
    win.transient(self)
    w_win, h_win = 700, 620
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w_win // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h_win // 2)
    win.geometry(f"{w_win}x{h_win}+{x}+{y}")
    win.minsize(560, 400)
    win.resizable(True, True)
    win.bind("<Escape>", lambda e: win.destroy())

    header = tk.Frame(win, bg=self.COLOR_BACKGROUND, height=42)
    header.pack(fill="x")
    header.pack_propagate(False)
    dot = tk.Canvas(header, width=10, height=10, bg=self.COLOR_HEADER_BG, highlightthickness=0)
    dot.create_oval(0, 0, 10, 10, fill=self.COLOR_HIGHLIGHT, outline="")
    dot.pack(side="left", padx=(16, 8), pady=16)
    tk.Label(header, text="RESET DATI", bg=self.COLOR_BACKGROUND, fg=self.COLOR_HEADER,
             font=("Segoe UI", 8, "bold")).pack(side="left")

    toolbar = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    toolbar.pack(fill="x", padx=12, pady=(10, 4))
    tk.Label(toolbar, text="Filtra:", bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
             font=("Arial", 9)).pack(side="left")
    var_filtro = tk.StringVar()
    entry_filtro = ttk.Entry(toolbar, textvariable=var_filtro, width=22, style="Border.TEntry")
    entry_filtro.pack(side="left", padx=(6, 14))
    lbl_count = tk.Label(toolbar, text="", bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR, font=("Arial", 9))
    lbl_count.pack(side="right")

    tk.Label(win, text="Seleziona i dati da azzerare. L'operazione non è reversibile. Budget, Target, Spese Pianificate e FairShare si aggiornano subito; per gli altri dati l'app viene riavviata.",
             bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR, font=("Arial", 9), wraplength=w_win - 40,
             justify="left").pack(anchor="w", padx=14, pady=(0, 6))

    contenitore = tk.Frame(win, bg=self.COLOR_BACKGROUND, highlightbackground=self.COLOR_HEADER_BG, highlightthickness=1)
    contenitore.pack(fill="both", expand=True, padx=12, pady=(0, 6))
    canvas = tk.Canvas(contenitore, bg=self.COLOR_BACKGROUND, highlightthickness=0)
    scrollbar = ttk.Scrollbar(contenitore, orient="vertical", command=canvas.yview, style="Vertical.TScrollbar")
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    scroll_frame = tk.Frame(canvas, bg=self.COLOR_BACKGROUND)
    window_id = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")

    def _resize_scroll_frame(event):
        canvas.itemconfig(window_id, width=event.width)
    canvas.bind("<Configure>", _resize_scroll_frame)

    def _aggiorna_scroll(event=None):
        canvas.configure(scrollregion=canvas.bbox("all"))
    scroll_frame.bind("<Configure>", _aggiorna_scroll)

    def _scroll(e):
        canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
    def _scroll_up(e):
        canvas.yview_scroll(-1, "units")
    def _scroll_down(e):
        canvas.yview_scroll(1, "units")
    win.bind_all("<MouseWheel>", _scroll)
    win.bind_all("<Button-4>", _scroll_up)
    win.bind_all("<Button-5>", _scroll_down)
    def _pulisci_binding(e):
        if e.widget is win:
            win.unbind_all("<MouseWheel>")
            win.unbind_all("<Button-4>")
            win.unbind_all("<Button-5>")
    win.bind("<Destroy>", _pulisci_binding)

    righe = []
    selezioni_correnti = set()

    def _aggiorna_contatore(*_a):
        lbl_count.config(text=f"{len(selezioni_correnti)} selezionati su {len(voci)}")

    def _on_toggle(percorso, var):
        if var.get():
            selezioni_correnti.add(percorso)
        else:
            selezioni_correnti.discard(percorso)
        _aggiorna_contatore()

    def _popola(filtro=""):
        for w in scroll_frame.winfo_children():
            w.destroy()
        righe.clear()
        filtro = filtro.strip().lower()
        for etichetta, descrizione, percorso, is_dir in voci:
            if filtro and filtro not in etichetta.lower() and filtro not in descrizione.lower():
                continue
            riga = tk.Frame(scroll_frame, bg=self.COLOR_BACKGROUND)
            riga.pack(fill="x", padx=4, pady=3)
            var = tk.BooleanVar(value=(percorso in selezioni_correnti))
            var.trace_add("write", lambda *a, p=percorso, v=var: _on_toggle(p, v))
            chk = tk.Checkbutton(
                riga, variable=var, bg=self.COLOR_BACKGROUND,
                activebackground=self.COLOR_BACKGROUND, selectcolor=self.COLOR_WHITE,
                highlightthickness=0, bd=0
            )
            chk.pack(side="left", anchor="n", padx=(4, 6), pady=1)
            testo = tk.Frame(riga, bg=self.COLOR_BACKGROUND)
            testo.pack(side="left", fill="x", expand=True)
            dimensione = _dimensione_leggibile(percorso, is_dir)
            lbl_nome = tk.Label(testo, text=f"{etichetta}   ·   {dimensione}", bg=self.COLOR_BACKGROUND,
                                 fg=self.TEXT_COLOR, font=("Arial", 9, "bold"), anchor="w", justify="left")
            lbl_nome.pack(fill="x", anchor="w")
            lbl_desc = tk.Label(testo, text=descrizione, bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
                                 font=("Arial", 8), anchor="w", justify="left", wraplength=w_win - 140)
            lbl_desc.pack(fill="x", anchor="w")
            for w in (riga, testo, lbl_nome, lbl_desc):
                w.bind("<Button-1>", lambda e, v=var: v.set(not v.get()))
            righe.append((riga, var, etichetta, descrizione, percorso, is_dir))
        _aggiorna_contatore()
        win.after(10, _aggiorna_scroll)

    var_filtro.trace_add("write", lambda *a: _popola(var_filtro.get()))
    _popola()

    def _seleziona_tutto():
        for _r, v, *_ in righe:
            v.set(True)

    def _deseleziona_tutto():
        for _r, v, *_ in righe:
            v.set(False)

    footer_sel = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    footer_sel.pack(fill="x", padx=12, pady=(0, 4))
    btn_tutti = ttk.Label(footer_sel, text="Seleziona Tutto", background=self.COLOR_BACKGROUND,
                           foreground=self.TEXT_COLOR, cursor="hand2", padding=(8, 3))
    btn_tutti.pack(side="left")
    btn_tutti.bind("<Button-1>", lambda e: _seleziona_tutto())
    btn_nessuno = ttk.Label(footer_sel, text="Deseleziona Tutto", background=self.COLOR_BACKGROUND,
                             foreground=self.TEXT_COLOR, cursor="hand2", padding=(8, 3))
    btn_nessuno.pack(side="left")
    btn_nessuno.bind("<Button-1>", lambda e: _deseleziona_tutto())

    def _restart_application():
        script_path = os.path.abspath(sys.argv[0])
        args = [sys.executable, script_path] + sys.argv[1:]
        try:
            if os.name == 'nt':
                subprocess.Popen(args, creationflags=0x00000008, shell=False, close_fds=True)
            else:
                subprocess.Popen(args, start_new_session=True, close_fds=True)
        except Exception as e:
            self.show_custom_warning(
                "Errore Riavvio",
                f"Impossibile riavviare automaticamente l'applicazione:\n{e}\n\nChiudi e riavvia manualmente."
            )
            return
        os._exit(0)

    def _aggiorna_a_caldo(selezionati):
        if any(p.endswith(TARGET) for _e, p, _d in selezionati):
            try:
                self.lbl_budget_mese_widget.config(text="Target Mese: N/D")
                self.lbl_budget_anno_widget.config(text="Target Anno: N/D")
            except Exception:
                pass
        if any(p.endswith(PIANI) for _e, p, _d in selezionati):
            try:
                from moduli.spese_pianificate import _aggiorna_finestra_pianifica
                _aggiorna_finestra_pianifica(self)
            except Exception:
                pass
        if any(p.endswith(FS_PARTECIPANTI) for _e, p, _d in selezionati):
            try:
                gestore = _app.PROFILO_ATTIVO if _app.PROFILO_ATTIVO != "Principale" else os.path.basename(os.getcwd())
                nomi = [f"PER· {gestore}"] if self._gestore_partecipa() else []
                self.nomi_con_icone = list(nomi)
                valori = [""] + nomi + ["⚙️ Gestisci Partecipanti"]
                for attr in ("partecipante_combobox", "ric_partecipante_combobox"):
                    cb = getattr(self, attr, None)
                    try:
                        if cb is not None and cb.winfo_exists():
                            cb["values"] = valori
                    except Exception:
                        pass
                self.partecipante_var.set("")
            except Exception:
                pass
        if any(p.endswith((FS_PARTECIPANTI, FS_PAGAMENTI)) for _e, p, _d in selezionati):
            try:
                if getattr(self, "_dare_avere_aggiorna", None):
                    self._dare_avere_aggiorna()
            except Exception:
                pass
        for nome in ("aggiorna_monitoraggio_budget", "refresh_gui", "aggiorna_barre_503020"):
            try:
                getattr(self, nome)()
            except Exception:
                pass

    def _esegui_reset():
        selezionati =[(e, p, d) for e, _de, p, d in voci if p in selezioni_correnti]
        if not selezionati:
            self.show_toast("Nessun elemento selezionato")
            return
        elenco = "\n".join(f"• {e}" for e, _p, _d in selezionati[:12])
        if len(selezionati) > 12:
            elenco += f"\n… e altri {len(selezionati) - 12}"
        a_caldo = all(p.endswith(A_CALDO) for _e, p, _d in selezionati)
        esito = ("I dati vengono azzerati subito, senza riavvio." if a_caldo else "L'app verrà riavviata.")
        msg = f"Azzerare {len(selezionati)} elemento/i selezionato/i?\n\n{elenco}\n\n{esito} L'operazione non è reversibile."
        if not self.show_custom_askyesno("Conferma Reset", msg):
            return
        win.destroy()
        errori = []
        for etichetta, percorso, is_dir in selezionati:
            try:
                if percorso.endswith(BUDGET):
                    _azzera_budget(percorso)
                elif percorso.endswith(TARGET):
                    _azzera_target(percorso)
                elif percorso.endswith((FS_PARTECIPANTI, FS_PAGAMENTI, PIANI)):
                    _azzera_fairshare(percorso)
                elif is_dir:
                    if os.path.isdir(percorso):
                        shutil.rmtree(percorso)
                else:
                    if os.path.exists(percorso):
                        os.remove(percorso)
            except Exception as e:
                errori.append(f"{etichetta}: {e}")
        if any(p == getattr(_app, "DB_FILE", None) for _e, p, _d in selezionati):
            try:
                from moduli.community_pool import community_pool_segna_riallinea
                community_pool_segna_riallinea()
            except Exception:
                pass
        if any(p.endswith(PIANI) for _e, p, _d in selezionati):
            self.pianificate = {"piani": []}
        if any(p.endswith(FS_PARTECIPANTI) for _e, p, _d in selezionati):
            nomi_mem = getattr(self, "nomi_partecipanti", None)
            if isinstance(nomi_mem, list):
                nomi_mem.clear()
        if any(p.endswith(FS_PAGAMENTI) for _e, p, _d in selezionati):
            for lista_mem in (getattr(self, "spese", None) or {}).values():
                for e_mem in lista_mem:
                    if getattr(e_mem, "fairshare", None):
                        e_mem.fairshare = None
        if any(p.endswith(BUDGET) for _e, p, _d in selezionati):
            for nome in CHIAVI_BUDGET:
                d_mem = getattr(self, nome, None)
                if isinstance(d_mem, dict):
                    d_mem.clear()
        if any(p.endswith(TARGET) for _e, p, _d in selezionati):
            _app.TARGET_MESE = _app.TARGET_ANNO = 0
            self.budget_mensile = self.budget_annuale = 0
            cfg_mem = getattr(_app, "app_config_globale", None)
            if isinstance(cfg_mem, dict):
                for k in CHIAVI_TARGET:
                    cfg_mem[k] = 0
        if errori:
            self.show_custom_warning(
                "Errore Reset",
                "Alcuni elementi non sono stati azzerati:\n" + "\n".join(errori) +
                "\n\nPer sicurezza l'app verrà comunque riavviata, per evitare che i dati "
                "ancora in memoria vengano risalvati sugli elementi cancellati con successo."
            )
        elif a_caldo:
            _aggiorna_a_caldo(selezionati)
            self.show_toast("Dati azzerati.", duration=2200)
            return
        self.show_toast("Riavvio in corso. Dati azzerati!", duration=2600)
        self._on_close_lock()
        self.after(2600, _restart_application)

    def _reset_completo():
        if not self.show_custom_askyesno(
            "Conferma RESET COMPLETO",
            "Azzerare TUTTI i dati e le configurazioni dell'app (l'intera cartella dati e la cartella export)?\n\n"
            "L'app verrà riavviata allo stato predefinito. L'operazione non è reversibile."
        ):
            return
        win.destroy()
        try:
            if os.path.exists(DB_DIR):
                shutil.rmtree(DB_DIR)
            if os.path.exists(EXPORT_FILES):
                shutil.rmtree(EXPORT_FILES)
        except Exception as e:
            self.show_custom_warning(
                "Errore Reset",
                f"Errore durante l'azzeramento completo:\n{e}\n\n"
                "Per sicurezza l'app verrà comunque riavviata."
            )
        self.show_toast("Riavvio in corso. Dati azzerati allo stato predefinito!", duration=2600)
        self._on_close_lock()
        self.after(2600, _restart_application)

    footer = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    footer.pack(fill="x", padx=12, pady=(0, 12))

    img_reset = self.icone_gui.get("cancella")
    btn_reset_sel = ttk.Label(footer, compound="left", image=img_reset,
                               text=" Azzera Selezionati" if img_reset else "Azzera Selezionati",
                               background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                               cursor="hand2", padding=(10, 5))
    btn_reset_sel.pack(side="left", padx=(0, 6))
    btn_reset_sel.bind("<Button-1>", lambda e: _esegui_reset())

    img_completo = self.icone_gui.get("chiudi")
    btn_reset_completo = ttk.Label(footer, compound="left", image=img_completo,
                                    text=" RESET COMPLETO" if img_completo else "RESET COMPLETO",
                                    background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                                    cursor="hand2", padding=(10, 5))
    btn_reset_completo.pack(side="left", padx=(0, 6))
    btn_reset_completo.bind("<Button-1>", lambda e: _reset_completo())

    img_chiudi = self.icone_gui.get("chiudi")
    btn_chiudi = ttk.Label(footer, compound="left", image=img_chiudi,
                            text=" Chiudi" if img_chiudi else "✖ Chiudi",
                            background=self.COLOR_BACKGROUND, foreground=self.TEXT_COLOR,
                            cursor="hand2", padding=(10, 5))
    btn_chiudi.pack(side="right")
    btn_chiudi.bind("<Button-1>", lambda e: win.destroy())

    win.deiconify()
    win.focus_force()
