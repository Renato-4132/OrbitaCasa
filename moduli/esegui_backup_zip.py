#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import tempfile
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
        popup.overrideredirect(True)
        popup.configure(bg=self.COLOR_WIDGET_BG, highlightbackground=self.COLOR_HIGHLIGHT, highlightthickness=2)
        w, h = 380, 115
        x = self.winfo_x() + (self.winfo_width() // 2) - (w // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (h // 2)
        popup.geometry(f"{w}x{h}+{x}+{y}")
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
