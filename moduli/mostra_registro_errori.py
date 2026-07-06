#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tkinter as tk
from tkinter import ttk, filedialog

# Visualizzazione e Gestione del Registro Errori di Sistema
def mostra_registro_errori(self, event=None):
    import __main__ as _app
    DB_DIR = _app.DB_DIR
    EXPORT_FILES = _app.EXPORT_FILES
    log_path = os.path.join(DB_DIR, "error_log.txt")
    if not os.path.exists(log_path) or os.path.getsize(log_path) == 0:
        self.show_toast("Non ci sono errori registrati nel log.")
        return
    with open(log_path, "r", encoding="utf-8") as f:
        contenuto = f.read()
    anteprima = tk.Toplevel(bg=self.COLOR_TOPLEVEL)
    anteprima.withdraw()
    anteprima.title("Registro Anomalie di Sistema (Log)")
    anteprima.resizable(False, False)
    larghezza_finestra = 1000
    altezza_finestra = 600
    def centra_finestra():
        larghezza_schermo = anteprima.winfo_screenwidth()
        altezza_schermo = anteprima.winfo_screenheight()
        x = (larghezza_schermo // 2) - (larghezza_finestra // 2)
        y = (altezza_schermo // 2) - (altezza_finestra // 2)
        anteprima.geometry(f"{larghezza_finestra}x{altezza_finestra}+{x}+{y}")
        anteprima.resizable(True, True)
        anteprima.minsize(larghezza_finestra, altezza_finestra)
        anteprima.deiconify()
        anteprima.lift()
        anteprima.focus_force()
    anteprima.after(0, centra_finestra)
    anteprima.bind("<Escape>", lambda e: anteprima.destroy())
    frame_testo = tk.Frame(anteprima, bg=self.COLOR_BACKGROUND)
    frame_testo.pack(padx=10, pady=10, fill="both", expand=True)
    txt = tk.Text(frame_testo, wrap="word", font=("Courier New", 10),
                  bg=self.COLOR_WHITE, fg=self.COLOR_BLACK, insertbackground="white")
    scrollbar = ttk.Scrollbar(frame_testo, orient="vertical", command=txt.yview)
    txt.configure(yscrollcommand=scrollbar.set)
    txt.insert("1.0", contenuto)
    txt.config(state="disabled")
    scrollbar.pack(side="right", fill="y")
    txt.pack(side="left", fill="both", expand=True)
    def esporta_log():
        import datetime
        now = datetime.date.today()
        nome_file_default = f"Registro_Anomalie_{now:%d-%m-%Y}.txt"
        file_dest = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("File di testo", "*.txt")],
            initialfile=nome_file_default,
            initialdir=EXPORT_FILES,
            title="Esporta Registro Errori",
            confirmoverwrite=False,
            parent=anteprima
        )
        if file_dest:
            if os.path.exists(file_dest):
                conferma = self.show_custom_askyesno(
                    "Sovrascrivere file?",
                    f"Il file '{os.path.basename(file_dest)}' \nesiste già. Vuoi sovrascriverlo?"
                )
                if not conferma:
                    return
            try:
                with open(file_dest, "w", encoding="utf-8") as f:
                    f.write(contenuto)
                self.show_custom_warning("Esportazione completata", f"File salvato:\n{file_dest}")
            except Exception as e:
                self.show_custom_warning("Errore", f"Impossibile esportare il file: {e}")
    def cancella_log():
        if self.show_custom_askyesno("Conferma", "Vuoi svuotare definitivamente il registro anomalie ?"):
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("")
            txt.config(state="normal")
            txt.delete("1.0", "end")
            txt.config(state="disabled")
            self.show_toast("Registro svuotato.")
    def stampa_log():
        self._stampa_lista_diretta(contenuto, self.show_custom_warning)
    frame_bottoni = tk.Frame(anteprima, bg=self.COLOR_TOPLEVEL)
    frame_bottoni.pack(pady=10, fill="x")
    btn_esporta = ttk.Label(
        frame_bottoni, text=" Esporta", image=self.icone_gui.get("salva"),
        compound="left", cursor="hand2", font=("Arial", 9),
        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR
    )
    btn_esporta.pack(side="left", padx=10)
    btn_esporta.bind("<Button-1>", lambda e: esporta_log())
    btn_stampa = ttk.Label(
        frame_bottoni, text=" Stampa", image=self.icone_gui.get("stampa"),
        compound="left", cursor="hand2", font=("Arial", 9),
        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR
    )
    btn_stampa.pack(side="left", padx=10)
    btn_stampa.bind("<Button-1>", lambda e: stampa_log())
    btn_cancella = ttk.Label(
        frame_bottoni, text=" Cancella Registro", image=self.icone_gui.get("delete"),
        compound="left", cursor="hand2", font=("Arial", 9),
        background=self.COLOR_WIDGET_BG, foreground=self.COLOR_RED
    )
    btn_cancella.pack(side="left", padx=10)
    btn_cancella.bind("<Button-1>", lambda e: cancella_log())
    btn_chiudi = ttk.Label(
        frame_bottoni, text=" Chiudi", image=self.icone_gui.get("chiudi"),
        compound="left", cursor="hand2", font=("Arial", 9, "bold"),
        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR
    )
    btn_chiudi.pack(side="right", padx=10)
    btn_chiudi.bind("<Button-1>", lambda e: anteprima.destroy())
