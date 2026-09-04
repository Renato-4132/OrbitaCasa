#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
import sys

import tkinter as tk
from tkinter import ttk

def _elenco_file_variabili(_app):

    def g(nome):
        return getattr(_app, nome, None)
    voci_raw = [
        ("Movimenti, Categorie e Ricorrenze", "Spese, entrate, categorie personalizzate, ricorrenze e budget (spese_db.json)", "DB_FILE", False),
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
        ("FairShare - Partecipanti",          "Elenco partecipanti alle spese condivise (fairshare.json)", "PARTECIPANTI", False),
        ("FairShare - Stato Condiviso",       "Saldi e stato delle spese condivise (fairshare_state.json)", "FAIRSHARE_STATE", False),
        ("Fondo Risparmio",                   "Obiettivi e progressi del fondo risparmio (fondo_risparmio.json)", "FR_FILE", False),
        ("Fondo Pensione",                     "Dati anagrafica, versamenti, valorizzazioni e riscatti del fondo pensione (fondo_pensione.json)", "PENSIONE_FILE", False),
        ("Piano Dieta",                       "Piano alimentare impostato (dieta_piano.json)", "DIETA_FILE", False),
        ("Alimenti Personalizzati",           "Alimenti custom aggiunti al database dieta (alimenti_custom.json)", "CUSTOM_FILE", False),
        ("Storico Peso",                      "Storico del peso corporeo registrato (peso_storico.json)", "PESO_FILE", False),
        ("Fabbisogno Calorico",               "Dati per il calcolo del fabbisogno calorico (fabbisogno_dati.json)", "FABB_FILE", False),
        ("Dati Pedometro",                    "Passi giornalieri registrati (pedometro.json)", "PEDOMETRO_FILE", False),
        ("Studio - Clienti",                  "Anagrafica clienti dello Studio (studio_clienti.json)", "STUDIO_CLIENTI", False),
        ("Studio - Appuntamenti",             "Calendario appuntamenti dello Studio (studio_appuntamenti.json)", "STUDIO_APPUNTAMENTI", False),
        ("Studio - Prestazioni",              "Elenco prestazioni/servizi dello Studio (studio_prestazioni.json)", "STUDIO_PRESTAZIONI", False),
        ("Studio - Fatture",                  "Fatture emesse dallo Studio (studio_fatture.json)", "STUDIO_FATTURE", False),
        ("Studio - Dati Emittente",           "Dati anagrafici/fiscali dell'emittente (studio_emittente.json)", "STUDIO_EMITTENTE", False),
        ("Studio - Cassa",                    "Registro di cassa dello Studio (studio_cassa.json)", "STUDIO_CASSA", False),
        ("Studio - Magazzino",                "Inventario magazzino dello Studio (studio_magazzino.json)", "STUDIO_MAGAZZINO", False),
        ("Immobili",                          "Elenco immobili gestiti (immobil.json)", "IMMOBIL_FILE", False),
        ("Veicoli",                            "Veicoli, scadenze e registro movimenti (veicoli.json)", "VEICOLI_FILE", False),
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
    ]
    voci = []
    for etichetta, descrizione, nome_costante, is_dir in voci_raw:
        percorso = g(nome_costante)
        if percorso:
            voci.append((etichetta, descrizione, percorso, is_dir))

    DB_DIR = g("DB_DIR")
    BASE_DIR = g("BASE_DIR")
    if DB_DIR:
        voci.extend([
            ("Log Errori Applicativi", "Registro degli errori dell'app (error_log.txt)", os.path.join(DB_DIR, "error_log.txt"), False),
            ("Cache Risorse/Icone",    "Icone e risorse scaricate in cache: verranno riscaricate al riavvio", os.path.join(DB_DIR, "resources"), True),
            ("Profilo Utente Dieta",   "Utente attivo selezionato nel modulo Dieta (utente_attivo.json)", os.path.join(DB_DIR, "utente_attivo.json"), False),
            ("Profili Dieta Salvati",  "Cartella con i profili utente del modulo Dieta", os.path.join(DB_DIR, "utenti"), True),
            ("Certificato SSL",        "Certificato/chiave HTTPS del server locale: si rigenera da sola al riavvio (cert.pem/key.pem)", os.path.join(DB_DIR, "cert.pem"), False),
        ])
    if BASE_DIR:
        voci.extend([
            ("Cartella Backup", "Backup e snapshot creati manualmente o automaticamente", os.path.join(BASE_DIR, "backup"), True),
            ("Cartella Moduli", "Cartella contenente i moduli e i componenti aggiuntivi", os.path.join(BASE_DIR, "moduli"), True)
            
        ])
    return voci

def _dimensione_leggibile(percorso, is_dir):
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

    tk.Label(win, text="Seleziona i dati da azzerare. L'operazione richiede il riavvio dell'app e non è reversibile.",
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

    def _blocca_finestra_principale(messaggio):
        blocco = tk.Toplevel(self, bg=self.COLOR_BACKGROUND)
        blocco.overrideredirect(True)
        blocco.transient(self)
        w_b, h_b = 340, 90
        x_b = self.winfo_rootx() + (self.winfo_width() // 2) - (w_b // 2)
        y_b = self.winfo_rooty() + (self.winfo_height() // 2) - (h_b // 2)
        blocco.geometry(f"{w_b}x{h_b}+{x_b}+{y_b}")
        tk.Label(blocco, text=messaggio, bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
                 font=("Arial", 10, "bold"), wraplength=w_b - 20, justify="center").pack(expand=True, fill="both", padx=10, pady=10)
        blocco.focus_force()
        blocco.update()
        blocco.grab_set()
        return blocco

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

    def _esegui_reset():
        selezionati = [(e, p, d) for e, _de, p, d in voci if p in selezioni_correnti]
        if not selezionati:
            self.show_toast("Nessun elemento selezionato")
            return
        elenco = "\n".join(f"• {e}" for e, _p, _d in selezionati[:12])
        if len(selezionati) > 12:
            elenco += f"\n… e altri {len(selezionati) - 12}"
        msg = f"Azzerare {len(selezionati)} elemento/i selezionato/i?\n\n{elenco}\n\nL'app verrà riavviata. L'operazione non è reversibile."
        if not self.show_custom_askyesno("Conferma Reset", msg):
            return
        win.destroy()
        errori = []
        for etichetta, percorso, is_dir in selezionati:
            try:
                if is_dir:
                    if os.path.isdir(percorso):
                        shutil.rmtree(percorso)
                else:
                    if os.path.exists(percorso):
                        os.remove(percorso)
            except Exception as e:
                errori.append(f"{etichetta}: {e}")
        if errori:
            self.show_custom_warning(
                "Errore Reset",
                "Alcuni elementi non sono stati azzerati:\n" + "\n".join(errori) +
                "\n\nPer sicurezza l'app verrà comunque riavviata, per evitare che i dati "
                "ancora in memoria vengano risalvati sugli elementi cancellati con successo."
            )
        self.show_toast("Riavvio in corso. Dati azzerati!")
        _blocca_finestra_principale("Riavvio in corso...\nNon chiudere l'applicazione.")
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
            self.show_custom_warning("Errore Reset", f"Errore durante l'azzeramento completo:\n{e}")
            return
        self.show_toast("Riavvio in corso. Dati azzerati allo stato predefinito!")
        _blocca_finestra_principale("Riavvio in corso...\nNon chiudere l'applicazione.")
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
