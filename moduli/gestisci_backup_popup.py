#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import threading
import tkinter as tk
from tkinter import ttk


def gestisci_backup_popup(self):
    import __main__ as _app
    BASE_DIR = _app.BASE_DIR
    DB_DIR = _app.DB_DIR
    DB_FILE = _app.DB_FILE
    DATI_FILE = _app.DATI_FILE
    UTENZE_DB = _app.UTENZE_DB
    REGISTRY_FILE = _app.REGISTRY_FILE
    PW_FILE = _app.PW_FILE
    MEM_CAT = _app.MEM_CAT
    CONFIG_FILE = _app.CONFIG_FILE
    RIMANDA_FILE = _app.RIMANDA_FILE
    PROMEMORIA_FILE = _app.PROMEMORIA_FILE
    SUPERMERCATI_DB = _app.SUPERMERCATI_DB
    DEFAULT_API = _app.DEFAULT_API
    CONTROLLO_F_M = _app.CONTROLLO_F_M
    PARTECIPANTI = _app.PARTECIPANTI
    FAIRSHARE_STATE = _app.FAIRSHARE_STATE
    PORTAFOGLIO_AZIONI = _app.PORTAFOGLIO_AZIONI
    DIETA_FILE = _app.DIETA_FILE
    CUSTOM_FILE = _app.CUSTOM_FILE
    PESO_FILE = _app.PESO_FILE
    FABB_FILE = _app.FABB_FILE
    PEDOMETRO_FILE = _app.PEDOMETRO_FILE
    STUDIO_CLIENTI = _app.STUDIO_CLIENTI
    STUDIO_APPUNTAMENTI = _app.STUDIO_APPUNTAMENTI
    STUDIO_PRESTAZIONI = _app.STUDIO_PRESTAZIONI
    STUDIO_FATTURE = _app.STUDIO_FATTURE
    STUDIO_EMITTENTE = _app.STUDIO_EMITTENTE
    STUDIO_CASSA = _app.STUDIO_CASSA
    STUDIO_MAGAZZINO = _app.STUDIO_MAGAZZINO
    IMMOBIL_FILE = _app.IMMOBIL_FILE
    FR_FILE = _app.FR_FILE
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    SCHEDULE_FILE = _app.SCHEDULE_FILE
    TAGS_DB = _app.TAGS_DB

    import os, time, subprocess, sys
    if hasattr(self, '_win_backup_istanza') and self._win_backup_istanza.winfo_exists():
        self._win_backup_istanza.lift()
        self._win_backup_istanza.focus_set()
        return
    cartella_backup = os.path.join(BASE_DIR, "backup")
    TIPI = {
        "spese_db.json":                  "Spese",
        "rubrica.json":                   "Rubrica",
        "utenze_db.json":                 "Utenze",
        "documenti_archiviati.json":      "Archivio Docs",
        "portafoglio_db.json":            "Portafoglio Bancario",
        "supermercati.json":              "Supermercati",
        "password.json":                  "Password",
        "config.json":                    "Configurazione",
        "update.json":                    "Aggiornamenti",
        "promemoria.json":                "Promemoria",
        "memoria_categorie.json":         "SmartCat",
        "api.json":                       "API Key",
        "controllo_fm.json":              "Controllo FM",
        "fairshare.json":                 "FairShare Partecipanti",
        "fairshare_state.json":           "FairShare Stato",
        "portafoglio.json":               "Portafoglio Azioni",
        "dieta_piano.json":               "Dieta",
        "alimenti_custom.json":           "Alimenti Custom",
        "peso_storico.json":              "Peso",
        "fabbisogno_dati.json":           "Fabbisogno",
        "pedometro.json":                 "Pedometro",
        "studio_clienti.json":            "Studio Clienti",
        "studio_appuntamenti.json":       "Studio Appuntamenti",
        "studio_prestazioni.json":        "Studio Prestazioni",
        "studio_fatture.json":            "Studio Fatture",
        "studio_emittente.json":          "Studio Emittente",
        "studio_cassa.json":              "Studio Cassa",
        "studio_magazzino.json":          "Studio Magazzino",
        "immobil.json":                   "Immobili",
        "fondo_risparmio.json":           "Fondo Risparmio",
        "schedule.json":                  "Schedulatore",
        "tags_db.json":                   "Tag",
        "snapshot_db.zip":                "Snapshot DB Completo",
    }
    win = tk.Toplevel(self, bg=self.COLOR_BACKGROUND)
    self._win_backup_istanza = win
    win.withdraw()
    win.title("Gestione Backup")
    win.bind("<Escape>", lambda e: win.destroy())
    w_win, h_win = 900, 600
    x = self.winfo_rootx() + (self.winfo_width()  // 2) - (w_win // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h_win // 2)
    win.geometry(f"{w_win}x{h_win}+{x}+{y}")
    win.resizable(False, False)
    win.transient(self)
    header = tk.Frame(win, bg=self.COLOR_HEADER_BG, height=42)
    header.pack(fill="x")
    header.pack_propagate(False)
    dot = tk.Canvas(header, width=10, height=10,
                    bg=self.COLOR_HEADER_BG, highlightthickness=0)
    dot.create_oval(0, 0, 10, 10, fill=self.COLOR_HIGHLIGHT, outline="")
    dot.pack(side="left", padx=(16, 8), pady=16)
    tk.Label(header, text="GESTIONE BACKUP",
             bg=self.COLOR_HEADER_BG, fg=self.COLOR_HEADER,
             font=("Segoe UI", 8, "bold")).pack(side="left")
    toolbar = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    toolbar.pack(fill="x", padx=12, pady=(8, 4))
    tk.Label(toolbar, text="Filtra:",
             bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
             font=("Arial", 9)).pack(side="left")
    var_filtro = tk.StringVar()
    entry_filtro = ttk.Entry(toolbar, textvariable=var_filtro, width=20,
                             style="Border.TEntry")
    entry_filtro.pack(side="left", padx=(6, 12))
    tk.Label(toolbar, text="Data:",
             bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
             font=("Arial", 9)).pack(side="left")
    var_data = tk.StringVar(value="Tutte")
    c_data = ttk.Combobox(toolbar, textvariable=var_data,
                          width=12, style="Border.TCombobox", state="readonly")
    c_data.pack(side="left", padx=(4, 12))
    var_solo_snapshot = tk.BooleanVar(value=True)
    chk_snapshot = tk.Checkbutton(toolbar, text="Solo Snapshot",
                                  variable=var_solo_snapshot,
                                  bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
                                  selectcolor=self.COLOR_WIDGET_BG,
                                  activebackground=self.COLOR_BACKGROUND,
                                  activeforeground=self.TEXT_COLOR,
                                  font=("Arial", 9), cursor="hand2",
                                  relief="flat", bd=0,
                                  highlightthickness=0)
    chk_snapshot.pack(side="left", padx=(0, 12))
    var_solo_snapshot.trace_add("write", lambda *a: _carica_lista(var_filtro.get()))
    lbl_count = tk.Label(toolbar, text="",
                         bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
                         font=("Arial", 9))
    lbl_count.pack(side="left")
    frame_tree = tk.Frame(win, bg=self.COLOR_BACKGROUND,
                          highlightbackground=self.COLOR_HEADER_BG,
                          highlightthickness=1)
    frame_tree.pack(fill="both", expand=True, padx=12, pady=(0, 2))
    cols = ("Data", "Tipo", "File", "Dimensione")
    tree = ttk.Treeview(frame_tree, columns=cols, show="headings",
                        style="Treeview", selectmode="extended")
    for c in cols:
        tree.heading(c, text=c,
                     anchor="e" if c == "Dimensione" else "w",
                     command=lambda _c=c: self.treeview_sort_column(tree, _c, False))
    tree.column("Data",       width=110, minwidth=90,  anchor="w")
    tree.column("Tipo",       width=160, minwidth=120, anchor="w")
    tree.column("File",       width=400, minwidth=200, anchor="w")
    tree.column("Dimensione", width=100, minwidth=80,  anchor="e")
    tree.tag_configure("pari",    background=self.COLOR_WIDGET_BG,  foreground=self.TEXT_COLOR)
    tree.tag_configure("dispari", background=self.COLOR_BACKGROUND, foreground=self.TEXT_COLOR)
    sb_v = ttk.Scrollbar(frame_tree, orient="vertical",   command=tree.yview,
                         style="Vertical.TScrollbar")
    sb_v.pack(side="right",  fill="y")
    tree.configure(yscrollcommand=sb_v.set)
    tree.pack(fill="both", expand=True)
    tk.Label(win, text="💡 Ctrl o Shift per selezione multipla  |  Ripristino snapshot: sovrascrive l'intera cartella db",
             bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
             font=("Arial", 8)).pack(anchor="w", padx=14, pady=(0, 4))
    def _estrai_data_da_nome(nome):
        import re
        m = re.search(r"-(\d{2})(\d{2})(\d{4})_", nome)
        if m:
            return f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
        m = re.search(r"_(\d{2})(\d{2})(\d{4})_", nome)
        if m:
            return f"{m.group(1)}/{m.group(2)}/{m.group(3)}"
        return "—"
    def _carica_lista(filtro=""):
        for i in tree.get_children():
            tree.delete(i)
        if not os.path.exists(cartella_backup):
            lbl_count.config(text="Cartella backup non trovata")
            return
        files = sorted(os.listdir(cartella_backup), reverse=True)
        date_set = ["Tutte"]
        for nome in files:
            parts = nome.split("-", 3)
            try:
                datetime.datetime.strptime(f"{parts[0]}-{parts[1]}-{parts[2]}", "%d-%m-%Y")
                data_completa = f"{parts[0]}/{parts[1]}/{parts[2]}"
                if data_completa not in date_set:
                    date_set.append(data_completa)
            except Exception:
                pass
        c_data["values"] = date_set
        filtro_data = var_data.get()
        count = 0
        for idx, nome in enumerate(files):
            if filtro and filtro.lower() not in nome.lower():
                continue
            if var_solo_snapshot.get() and "snapshot_db" not in nome:
                continue
            percorso = os.path.join(cartella_backup, nome)
            try:
                sz = os.path.getsize(percorso)
                sz_str = f"{sz/1024:.1f} KB" if sz < 1024*1024 else f"{sz/1024/1024:.2f} MB"
            except Exception:
                sz_str = "?"
            parts = nome.split("-", 3)
            try:
                datetime.datetime.strptime(f"{parts[0]}-{parts[1]}-{parts[2]}", "%d-%m-%Y")
                data_str = f"{parts[0]}/{parts[1]}/{parts[2]}"
            except Exception:
                data_str = _estrai_data_da_nome(nome)
            if filtro_data != "Tutte":
                if data_str != filtro_data:
                    continue
            nome_originale = parts[3] if len(parts) >= 4 else nome
            if nome.lower().endswith(".zip"):
                if "snapshot_db" in nome:
                    tipo_str = "Snapshot DB Completo"
                elif "Personali" in nome:
                    tipo_str = "Docs Personali (ZIP)"
                else:
                    tipo_str = "Docs Contabili (ZIP)"
            else:
                tipo_str = TIPI.get(nome_originale, "File dati")
            tag = "pari" if idx % 2 == 0 else "dispari"
            tree.insert("", "end", values=(data_str, tipo_str, nome, sz_str), tags=(tag,))
            count += 1
        lbl_count.config(text=f"{count} file trovati")
    var_filtro.trace_add("write", lambda *a: _carica_lista(var_filtro.get()))
    var_data.trace_add("write",   lambda *a: _carica_lista(var_filtro.get()))
    _carica_lista()
    frame_footer = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    frame_footer.pack(fill="x", padx=12, pady=(0, 12))
    def _ripristina():
        import zipfile, shutil
        selezione = tree.selection()
        if not selezione:
            self.show_custom_warning("Nessuna selezione", "Seleziona uno o più file di backup.")
            return
        contiene_zip = any(tree.set(s, "File").lower().endswith(".zip") for s in selezione)
        if contiene_zip and len(selezione) > 1:
            self.show_custom_warning("Attenzione", "Se selezioni un archivio ZIP, non puoi selezionare altri file.")
            return
        if contiene_zip:
            nome_bak = tree.set(selezione[0], "File")
            is_snapshot = "snapshot_db" in nome_bak
            if is_snapshot:
                msg = f"Ripristinare lo snapshot '{nome_bak}'?\n\nL'intera cartella db verrà sostituita e l'app si riavvierà."
            else:
                msg = f"Ripristinare l'archivio '{nome_bak}'?\n\nL'applicazione si riavvierà."
            if not self.show_custom_askyesno("Conferma Ripristino", msg):
                return
            if is_snapshot:
                db_old = DB_DIR + "_old"
                try:
                    if os.path.exists(db_old):
                        shutil.rmtree(db_old, ignore_errors=True)
                    shutil.move(DB_DIR, db_old)
                    with zipfile.ZipFile(os.path.join(cartella_backup, nome_bak), "r") as z:
                        z.extractall(os.path.dirname(DB_DIR))
                    shutil.rmtree(db_old, ignore_errors=True)
                except Exception as e:
                    if os.path.exists(db_old):
                        if os.path.exists(DB_DIR):
                            shutil.rmtree(DB_DIR, ignore_errors=True)
                        shutil.move(db_old, DB_DIR)
                    self.show_custom_warning("Errore Ripristino", f"Ripristino fallito, dati originali recuperati:\n{e}")
                    return
            else:
                try:
                    with zipfile.ZipFile(os.path.join(cartella_backup, nome_bak), "r") as z:
                        z.extractall(DB_DIR)
                except Exception as e:
                    self.show_custom_warning("Errore Ripristino", f"Impossibile estrarre il ZIP:\n{e}")
                    return
        else:
            msg = f"Ripristinare i {len(selezione)} file selezionati?\n\nI file correnti verranno sovrascritti e l'applicazione si riavvierà."
            if not self.show_custom_askyesno("Conferma Ripristino", msg):
                return
            lista_file = [
                DB_FILE, DATI_FILE, UTENZE_DB, REGISTRY_FILE,
                PW_FILE, MEM_CAT, CONFIG_FILE, RIMANDA_FILE,
                PROMEMORIA_FILE, SUPERMERCATI_DB, DEFAULT_API, CONTROLLO_F_M,
                PARTECIPANTI, FAIRSHARE_STATE, PORTAFOGLIO_AZIONI, DIETA_FILE,
                CUSTOM_FILE, PESO_FILE, FABB_FILE, PEDOMETRO_FILE, STUDIO_CLIENTI,
                STUDIO_APPUNTAMENTI, STUDIO_PRESTAZIONI, STUDIO_FATTURE, STUDIO_EMITTENTE,
                STUDIO_CASSA, STUDIO_MAGAZZINO, IMMOBIL_FILE, FR_FILE, PORTAFOGLIO_BANCARIO,
                SCHEDULE_FILE, TAGS_DB
            ]
            for s in selezione:
                nome_bak = tree.set(s, "File")
                parts = nome_bak.split("-", 3)
                if len(parts) < 4: continue
                nome_originale = parts[3]
                destinazione = next((f for f in lista_file if os.path.basename(f) == nome_originale), None)
                if not destinazione:
                    self.show_custom_warning("File non riconosciuto", f"'{nome_originale}' non gestito.")
                    return
                try:
                    shutil.copy2(os.path.join(cartella_backup, nome_bak), destinazione)
                except Exception as e:
                    self.show_custom_warning("Errore Ripristino", f"Impossibile ripristinare:\n{e}")
                    return
        win.destroy()
        w, h = 350, 80
        parent = self
        parent.update_idletasks()
        xp = (parent.winfo_width() // 2) - (w // 2)
        yp = (parent.winfo_height() // 2) - (h // 2)
        pf = tk.Frame(parent, bg="orange", bd=3, relief="raised")
        pf.place(x=xp, y=yp, width=w, height=h)
        pf.lift()
        tk.Label(pf, text="Ripristino completato. Riavvio in corso...",
                 font=("Arial", 10, "bold"), justify="center", padx=10, pady=10,
                 bg="orange", fg="black").pack(expand=True, fill="both")
        parent.update()
        time.sleep(2)
        args = [sys.executable, os.path.abspath(sys.argv[0])] + sys.argv[1:]
        if os.name == "nt":
            subprocess.Popen(args, creationflags=0x00000008, shell=False, close_fds=True)
        else:
            subprocess.Popen(args, start_new_session=True, close_fds=True)
        os._exit(0)
    def _elimina():
        selezione = tree.selection()
        if not selezione:
            self.show_toast("Nessun file selezionato")
            return
        nomi = [tree.set(s, "File") for s in selezione]
        msg = f"Eliminare {len(nomi)} file di backup?" if len(nomi) > 1 else f"Eliminare '{nomi[0]}'?"
        if not self.show_custom_askyesno("Elimina Backup", msg):
            return
        errori = []
        for s in selezione:
            try:
                os.remove(os.path.join(cartella_backup, tree.set(s, "File")))
            except Exception as e:
                errori.append(str(e))
        if errori:
            self.show_custom_warning("Errore", "Alcuni file non eliminati:\n" + "\n".join(errori))
        else:
            self.show_toast(f"{len(nomi)} file eliminati")
        _carica_lista(var_filtro.get())
    def _apri_cartella():
        if os.path.exists(cartella_backup):
            if os.name == "nt":
                os.startfile(cartella_backup)
            else:
                subprocess.Popen(["xdg-open", cartella_backup])
    img_backup  = self.icone_gui.get("salva")
    img_restore = self.icone_gui.get("aggiorna")
    img_folder  = self.icone_gui.get("cartella")
    img_del     = self.icone_gui.get("cancella")
    img_close   = self.icone_gui.get("chiudi")
    def _esegui_backup_ora():
        self.show_toast("Backup in corso...")
        def _thread():
            self._esegui_backup_json()
            self._esegui_snapshot_db()
            win.after(0, lambda: _carica_lista(var_filtro.get()) if win.winfo_exists() else None)
            win.after(0, lambda: self.show_toast("Backup e snapshot completati") if win.winfo_exists() else None)
        threading.Thread(target=_thread, daemon=True).start()
    for img, testo, cmd in [
        (img_backup,  "Backup Ora",    _esegui_backup_ora),
        (img_restore, "Ripristina",    _ripristina),
        (img_folder,  "Apri Cartella", _apri_cartella),
        (img_del,     "Elimina",       _elimina),
    ]:
        btn = ttk.Label(frame_footer, compound="left", image=img,
                        text=f" {testo}" if img else f" {testo}",
                        background=self.COLOR_BACKGROUND, foreground=self.TEXT_COLOR,
                        cursor="hand2", padding=(10, 5))
        btn.pack(side="left", padx=(0, 6))
        btn.bind("<Button-1>", lambda e, f=cmd: f())
    btn_close = ttk.Label(frame_footer, compound="left", image=img_close,
                          text=" Chiudi" if img_close else "✖ Chiudi",
                          background=self.COLOR_BACKGROUND, foreground=self.TEXT_COLOR,
                          cursor="hand2", padding=(10, 5))
    btn_close.pack(side="right")
    btn_close.bind("<Button-1>", lambda e: win.destroy())
    win.deiconify()
    win.focus_force()
           
    # Snapshot automatico DB post-backup
