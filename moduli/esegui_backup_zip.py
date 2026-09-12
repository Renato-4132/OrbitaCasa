#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, Toplevel, Label

# Creazione e Archiviazione (ZIP/Formato Specifico) Completa
def esegui_backup_zip(self):
    from datetime import datetime
    import __main__ as _app
    PATH_LOCALE = _app.PATH_LOCALE
    percorso_archivio = ""
    cartella_temp_path = None
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Tentativo di backup di '{self.current_folder}'...")
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"{self.current_folder}_backup_{timestamp}"
        percorso_completo_output = filedialog.asksaveasfilename(
            title="Scegli dove salvare il file di backup",
            initialdir=os.path.expanduser('~'),
            initialfile=default_name,
            confirmoverwrite=False,
            defaultextension=f".{self.backup_formato}",
            filetypes=[(f"Archivi {self.backup_formato.upper()}", f"*.{self.backup_formato}")]
        )
        if not percorso_completo_output:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Backup annullato dall'utente.")
            return ""
        popup = Toplevel(self)
        popup.withdraw()
        popup.overrideredirect(True)
        popup.configure(bg=self.COLOR_WIDGET_BG, highlightbackground=self.COLOR_HIGHLIGHT, highlightthickness=2)
        w, h = 380, 115
        x = self.winfo_x() + (self.winfo_width() // 2) - (w // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (h // 2)
        popup.geometry(f"{w}x{h}+{x}+{y}")
        popup.deiconify()
        popup.grab_set()
        lbl_status = Label(popup, text="Inizializzazione backup...", font=("Arial", 10, "bold"), bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HEADER)
        lbl_status.pack(pady=(18, 4))
        BAR_W, BAR_H = 320, 12
        bar_cv = tk.Canvas(popup, width=BAR_W, height=BAR_H, bg=self.COLOR_HEADER_BG, highlightthickness=0)
        bar_cv.pack(pady=2)
        _segmenti = []
        _colori_base = []
        for i in range(BAR_W):
            t = i / BAR_W
            if t < 0.5:
                t2 = t / 0.5
                r = int(0x00 + (0xFF - 0x00) * t2)
                g = int(0xC8 + (0xD7 - 0xC8) * t2)
                b = 0x00
            else:
                t2 = (t - 0.5) / 0.5
                r = int(0xFF + (0xE0 - 0xFF) * t2)
                g = int(0xD7 + (0x6C - 0xD7) * t2)
                b = int(0x00 + (0x75 - 0x00) * t2)
            _colori_base.append((r, g, b))
            seg = bar_cv.create_rectangle(i, 0, i+1, BAR_H, fill=f"#{r:02x}{g:02x}{b:02x}", outline="", state="hidden")
            _segmenti.append(seg)
        lbl_sub = Label(popup, text="", font=("Arial", 9), bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR)
        lbl_sub.pack(pady=(4, 0))
        popup.update()
        def aggiorna_UI(valore, testo):
            soglia = int(BAR_W * max(0.0, min(valore, 100.0)) / 100.0)
            for idx, seg in enumerate(_segmenti):
                bar_cv.itemconfig(seg, state="normal" if idx < soglia else "hidden")
            lbl_status.config(text=testo)
            popup.update()
        aggiorna_UI(15, "Preparazione file temporanei...")
        percorso_output_senza_ext, _ = os.path.splitext(percorso_completo_output)
        cartella_destinazione = os.path.dirname(percorso_output_senza_ext)
        cartella_sorgente = PATH_LOCALE
        cartella_temp_path = tempfile.mkdtemp()
        cartella_dati_nel_temp_nome = self.current_folder
        cartella_dati_nel_temp_path = os.path.join(cartella_temp_path, cartella_dati_nel_temp_nome)
        aggiorna_UI(40, f"Copia dati: {self.current_folder}...")
        PATTERNS_DA_IGNORARE = ('*.lock', '*-journal', '*.db-wal', '*.tmp')
        shutil.copytree(
            cartella_sorgente,
            cartella_dati_nel_temp_path,
            ignore=shutil.ignore_patterns(*PATTERNS_DA_IGNORARE)
        )
        aggiorna_UI(75, "Compressione archivio finale...")
        os.makedirs(cartella_destinazione, exist_ok=True)
        percorso_archivio = shutil.make_archive(
            base_name=percorso_output_senza_ext,
            format=self.backup_formato,
            root_dir=cartella_temp_path,
            base_dir=cartella_dati_nel_temp_nome
        )
        aggiorna_UI(100, "Operazione completata!")
        popup.after(400, popup.destroy)
        self.show_custom_warning("Backup", f"Salvataggio di '{self.current_folder}' eseguito con successo!")
    except Exception as e:
        if 'popup' in locals():
            popup.destroy()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ERRORE: {e}")
        self.show_custom_warning("Errore", f"Errore durante il backup:\n{e}")
    finally:
        if cartella_temp_path and os.path.exists(cartella_temp_path):
            shutil.rmtree(cartella_temp_path, ignore_errors=True)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Pulizia file temporanei eseguita.")


# Backup Incrementale
def backup_incrementale(file_path, cartella_backup=None, max_backup=None):
    import datetime
    import __main__ as _app
    if max_backup is None:
        max_backup = _app.MAX_BACKUP
    if cartella_backup is None:
        cartella_backup = os.path.join(_app.BASE_DIR, "backup")
    if not os.path.exists(file_path):
        return
    os.makedirs(cartella_backup, exist_ok=True)
    nome_completo = os.path.basename(file_path)
    data = datetime.datetime.today().strftime("%d-%m-%Y")
    backup_file_name = f"{data}-{nome_completo}"
    backup_file_path = os.path.join(cartella_backup, backup_file_name)
    shutil.copy2(file_path, backup_file_path)
    stringa_filtro = f"-{nome_completo}"
    files_to_check = [f for f in os.listdir(cartella_backup) if f.endswith(stringa_filtro)]
    if not files_to_check:
        return
    def get_sort_key(filename):
        date_str = filename[:10]
        return datetime.datetime.strptime(date_str, "%d-%m-%Y")
    files_ordinati = sorted(
        files_to_check,
        key=get_sort_key,
        reverse=True
    )
    files_da_cancellare = files_ordinati[max_backup:]
    if files_da_cancellare:
        for f in files_da_cancellare:
            os.remove(os.path.join(cartella_backup, f))


# Timing Backup Incrementale threading
def pianifica_backup_orario(self):
    from datetime import datetime
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Avvio backup automatico...")
        threading.Thread(target=self._esegui_backup_json).start()
        threading.Thread(target=self.backup_documenti).start()
        threading.Thread(target=self.backup_documenti_personali).start()
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Errore durante il trigger del backup: {e}")
    # Backup Ogni 12 ore
    self.after(43200000, self.pianifica_backup_orario)


# Snapshot automatico DB post-backup
def _esegui_snapshot_db(self):
    import zipfile, glob
    import datetime
    import __main__ as _app
    BASE_DIR = _app.BASE_DIR
    DB_DIR = _app.DB_DIR
    MAX_BACKUP = _app.MAX_BACKUP
    try:
        cartella_backup = os.path.join(BASE_DIR, "backup")
        os.makedirs(cartella_backup, exist_ok=True)
        data = datetime.datetime.today().strftime("%d-%m-%Y")
        nome_snapshot = f"{data}-snapshot_db.zip"
        percorso_snapshot = os.path.join(cartella_backup, nome_snapshot)
        nome_cartella_db = os.path.basename(DB_DIR)
        with zipfile.ZipFile(percorso_snapshot, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
            for root, _, fnames in os.walk(DB_DIR):
                for fn in fnames:
                    percorso_completo = os.path.join(root, fn)
                    percorso_nello_zip = os.path.join(nome_cartella_db, os.path.relpath(percorso_completo, DB_DIR))
                    zf.write(percorso_completo, percorso_nello_zip)
        snapshots = sorted(
            glob.glob(os.path.join(cartella_backup, "*-snapshot_db.zip")),
            key=os.path.getmtime,
            reverse=True
        )
        for vecchio in snapshots[MAX_BACKUP:]:
            try:
                os.remove(vecchio)
            except Exception:
                pass
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Snapshot DB salvato: {nome_snapshot}")
    except Exception as e:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore snapshot DB: {e}")


# Backup Incrementale threading
def _esegui_backup_json(self):
    from datetime import datetime
    import __main__ as _app
    lista_file = [
        _app.DB_FILE, _app.DATI_FILE, _app.UTENZE_DB, _app.REGISTRY_FILE,
        _app.PW_FILE, _app.MEM_CAT, _app.CONFIG_FILE, _app.RIMANDA_FILE,
        _app.PROMEMORIA_FILE, _app.SUPERMERCATI_DB, _app.DEFAULT_API, _app.CONTROLLO_F_M,
        _app.PARTECIPANTI, _app.FAIRSHARE_STATE, _app.PORTAFOGLIO_AZIONI, _app.DIETA_FILE,
        _app.CUSTOM_FILE, _app.PESO_FILE, _app.FABB_FILE, _app.PEDOMETRO_FILE, _app.STUDIO_CLIENTI,
        _app.STUDIO_APPUNTAMENTI, _app.STUDIO_PRESTAZIONI, _app.STUDIO_FATTURE, _app.STUDIO_EMITTENTE,
        _app.STUDIO_CASSA, _app.STUDIO_MAGAZZINO, _app.IMMOBIL_FILE, _app.FR_FILE, _app.PORTAFOGLIO_BANCARIO,
        _app.SCHEDULE_FILE, _app.VEICOLI_FILE, _app.GAMIFICATION_FILE, _app.CREDENTIALS_FILE, _app.PENSIONE_FILE,
        _app.ANIMALI_FILE
    ]
    file_copiati = 0
    for f in lista_file:
        try:
            if os.path.exists(f):
                backup_incrementale(f)
                file_copiati += 1
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Errore backup nel thread per {f}: {e}")
    self._esegui_snapshot_db()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Backup Database terminato ({file_copiati} file salvati).")
