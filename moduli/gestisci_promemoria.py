#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import datetime
import tkinter as tk
from tkinter import ttk, filedialog

from __main__ import PROMEMORIA_FILE, EXPORT_FILES

# Gestione Promemoria
def gestisci_promemoria(self):
    if hasattr(self, '_promemoria_popup') and self._promemoria_popup and self._promemoria_popup.winfo_exists():
        self._promemoria_popup.lift()
        return
    def chiudi_promemoria_popup():
        promemoria_popup.destroy()
        self._promemoria_popup = None
    def salva_promemoria():
        promemoria_text = promemoria_text_widget.get("1.0", tk.END).strip()
        data = {"promemoria": promemoria_text} 
        try:
            with open(PROMEMORIA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self.show_toast("Promemoria salvato.")
            chiudi_promemoria_popup()
        except Exception as e:
            self.show_custom_warning("Errore", f"Impossibile salvare il file: {e}")
    def carica_promemoria():
        if os.path.exists(PROMEMORIA_FILE):
            try:
                with open(PROMEMORIA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                promemoria = data.get("promemoria", "")
                promemoria_text_widget.delete("1.0", tk.END)
                promemoria_text_widget.insert("1.0", promemoria)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                self.show_custom_warning("Errore", f"Impossibile caricare il file promemoria.json: {e}")
                pass
    def esporta_promemoria():
        now = datetime.date.today()
        promemoria_text = promemoria_text_widget.get("1.0", tk.END).strip()
        filename = f"Promemoria_Export_{now.day:02d}-{now.month:02d}-{now.year}.txt"
        file = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("File di testo", "*.txt"), ("Tutti i file", "*.*")],
            initialdir=EXPORT_FILES,
            initialfile=filename,
            title="Esporta Promemoria",
            confirmoverwrite=False,
            parent=promemoria_popup
        )
        if file:
            if os.path.exists(file):
                conferma = self.show_custom_askyesno(
                    "Sovrascrivere file?",
                    f"Il file '{os.path.basename(file)}' \nesiste già. Vuoi sovrascriverlo?"
                )
                if not conferma:
                    return
            try:
                with open(file, "w", encoding="utf-8") as f:
                    f.write(promemoria_text)  
                self.show_toast("Promemoria esportato.")
            except Exception as e:
                self.show_custom_warning("Errore", f"Impossibile salvare il file: {e}")
    if hasattr(self, 'popup_calendario') and self.popup_calendario and self.popup_calendario.winfo_exists():
        self.popup_calendario.destroy()
        self.popup_calendario = None
    promemoria_popup = tk.Toplevel(self)
    self._promemoria_popup = promemoria_popup
    promemoria_popup.title("Promemoria")
    promemoria_popup.resizable(True, True)
    promemoria_popup.withdraw()
    promemoria_popup.transient(self)
    promemoria_popup.protocol("WM_DELETE_WINDOW", chiudi_promemoria_popup) 
    promemoria_popup.bind('<Escape>', lambda e: chiudi_promemoria_popup())
    main_frame = ttk.Frame(promemoria_popup, padding=10)
    main_frame.pack(fill="both", expand=True)
    main_frame.columnconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)
    main_frame.columnconfigure(2, weight=1) 
    main_frame.rowconfigure(0, weight=1)
    promemoria_text_widget = tk.Text(
        main_frame, 
        wrap="word", 
        width=50, 
        height=15, 
        bg="#ADD8E6",
        fg="black",
        selectforeground="white",
        relief=tk.FLAT,
        borderwidth=1
    )
    promemoria_text_widget.grid(row=0, column=0, columnspan=3, pady=(0, 10), sticky="nsew") 
    scrollbar = ttk.Scrollbar(main_frame, command=promemoria_text_widget.yview, style="Vertical.TScrollbar")
    scrollbar.grid(row=0, column=3, sticky='ns')
    promemoria_text_widget['yscrollcommand'] = scrollbar.set
    button_container = tk.Frame(main_frame, bg=self.COLOR_WIDGET_BG)
    button_container.grid(row=1, column=0, columnspan=3, pady=(10, 5), sticky="ew")
    for i in range(4): button_container.columnconfigure(i, weight=1)
    img_salva = self.icone_gui.get("check")
    self.btn_salva_promemoria = ttk.Label(button_container, compound="left", cursor="hand2",
            background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, font=("Arial", 9, "bold"))
    if img_salva and not isinstance(img_salva, str):
            self.btn_salva_promemoria.config(image=img_salva, text=" Salva")
            self.btn_salva_promemoria.image = img_salva
    else:
            self.btn_salva_promemoria.config(text="Salva")
    self.btn_salva_promemoria.grid(row=0, column=0, padx=5)
    self.btn_salva_promemoria.bind("<Button-1>", lambda e: salva_promemoria())
    img_stampa = self.icone_gui.get("stampa")
    self.btn_stampa_promemoria = ttk.Label(button_container, compound="left", cursor="hand2",
            background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, font=("Arial", 9, "bold"))
    if img_stampa and not isinstance(img_stampa, str):
            self.btn_stampa_promemoria.config(image=img_stampa, text=" Stampa")
            self.btn_stampa_promemoria.image = img_stampa
    else:
            self.btn_stampa_promemoria.config(text="Stampa")
    self.btn_stampa_promemoria.grid(row=0, column=1, padx=5)
    self.btn_stampa_promemoria.bind("<Button-1>", lambda e: self._stampa_lista_diretta(
            promemoria_text_widget.get("1.0", tk.END).strip(), self.show_custom_warning))
    img_esporta = self.icone_gui.get("carica")
    self.btn_esporta_promemoria = ttk.Label(button_container, compound="left", cursor="hand2",
            background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, font=("Arial", 9, "bold"))
    if img_esporta and not isinstance(img_esporta, str):
            self.btn_esporta_promemoria.config(image=img_esporta, text=" Esporta")
            self.btn_esporta_promemoria.image = img_esporta
    else:
            self.btn_esporta_promemoria.config(text="Esporta")
    self.btn_esporta_promemoria.grid(row=0, column=2, padx=5)
    self.btn_esporta_promemoria.bind("<Button-1>", lambda e: esporta_promemoria())
    img_chiudi = self.icone_gui.get("chiudi")
    self.btn_cancella_promemoria = ttk.Label(button_container, compound="left", cursor="hand2",
            background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, font=("Arial", 9, "bold"))
    if img_chiudi and not isinstance(img_chiudi, str):
            self.btn_cancella_promemoria.config(image=img_chiudi, text=" Chiudi")
            self.btn_cancella_promemoria.image = img_chiudi
    else:
            self.btn_cancella_promemoria.config(text="Chiudi")
    self.btn_cancella_promemoria.grid(row=0, column=3, padx=5)
    self.btn_cancella_promemoria.bind("<Button-1>", lambda e: chiudi_promemoria_popup())
    carica_promemoria()
    self.update_idletasks() 
    window_width = 800  
    window_height = 400     
    app_x = self.winfo_rootx()
    app_y = self.winfo_rooty()
    app_width = self.winfo_width()
    app_height = self.winfo_height()
    center_x = app_x + (app_width // 2) - (window_width // 2)
    center_y = app_y + (app_height // 2) - (window_height // 2)
    promemoria_popup.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    promemoria_popup.minsize(window_width, window_height)
    promemoria_popup.deiconify() 
