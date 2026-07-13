#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import tkinter as tk
from tkinter import ttk


# Popup di Selezione Periodo per Analisi e Bilanci (Giorno/Mese/Anno/Totale)
def popup_scelta_estratto(self):
    if hasattr(self, '_scelta_estratto_win') and self._scelta_estratto_win and self._scelta_estratto_win.winfo_exists():
        self._scelta_estratto_win.lift()
        self._scelta_estratto_win.focus_force()
        return
    popup = tk.Toplevel(self, bg=self.COLOR_WIDGET_BG)
    popup.transient(self)
    self._scelta_estratto_win = popup
    popup.bind("<Destroy>", lambda e: setattr(self, '_scelta_estratto_win', None) if e.widget is popup else None)
    popup.withdraw()
    popup.title("Analisi e Bilanci")
    popup.update_idletasks()
    w_popup, h_popup = 420, 400
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w_popup // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h_popup // 2)
    popup.geometry(f"{w_popup}x{h_popup}+{x}+{y}")
    popup.resizable(False, False)
    popup.deiconify()
    popup.bind("<Escape>", lambda e: popup.destroy())
    ttk.Label(popup, text="Seleziona Periodo di Analisi",
              font=("Arial", 12, "bold")).pack(pady=15)
    scelta_tipo = tk.StringVar(value="anno")
    def aggiorna_interfaccia():
        tipo = scelta_tipo.get()
        if tipo != "totale": f_anno.pack(fill="x", pady=2)
        else: f_anno.pack_forget()
        if tipo in ["mese", "giorno"]: f_mese.pack(fill="x", pady=2)
        else: f_mese.pack_forget()
        if tipo == "giorno": f_giorno.pack(fill="x", pady=2)
        else: f_giorno.pack_forget()
    frame_opzioni = tk.Frame(popup, bg=self.COLOR_WIDGET_BG)
    frame_opzioni.pack(pady=5, padx=30, fill="x")
    opzioni = [("Bilancio Giornaliero", "giorno"), ("Bilancio Mensile", "mese"),
               ("Bilancio Annuale", "anno"), ("Matrice Storica Totale", "totale")]
    for text, mode in opzioni:
        rb = ttk.Radiobutton(frame_opzioni,
                             text=text,
                             variable=scelta_tipo,
                             value=mode,
                             command=aggiorna_interfaccia,
                             style="Custom.TRadiobutton")
        rb.pack(anchor="w", pady=2)
    frame_sel = ttk.Labelframe(popup, text=" Selezione Periodo ", padding=10)
    frame_sel.pack(pady=15, padx=20, fill="x")
    WIDTH_COMBO = 15
    f_anno = tk.Frame(frame_sel, bg=self.COLOR_WIDGET_BG)
    ttk.Label(f_anno, text="Anno:", width=10, anchor="e").pack(side="left")
    anni = [str(y) for y in range(2016, datetime.date.today().year + 2)]
    c_anno = ttk.Combobox(f_anno, values=anni, width=WIDTH_COMBO, style="Border.TCombobox", state="readonly")
    c_anno.set(str(datetime.date.today().year))
    c_anno.pack(side="left", padx=10)
    f_mese = tk.Frame(frame_sel, bg=self.COLOR_WIDGET_BG)
    ttk.Label(f_mese, text="Mese:", width=10, anchor="e").pack(side="left")
    mesi_nomi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                 "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    c_mese = ttk.Combobox(f_mese, values=mesi_nomi, width=WIDTH_COMBO, style="Border.TCombobox", state="readonly")
    c_mese.current(datetime.date.today().month - 1)
    c_mese.pack(side="left", padx=10)
    f_giorno = tk.Frame(frame_sel, bg=self.COLOR_WIDGET_BG)
    ttk.Label(f_giorno, text="Giorno:", width=10, anchor="e").pack(side="left")
    giorni = [str(g) for g in range(1, 32)]
    c_giorno = ttk.Combobox(f_giorno, values=giorni, width=WIDTH_COMBO, style="Border.TCombobox", state="readonly")
    c_giorno.set(str(datetime.date.today().day))
    c_giorno.pack(side="left", padx=10)
    aggiorna_interfaccia()
    def procedi_generazione():
        mode = scelta_tipo.get()
        self.estratto_year_var.set(c_anno.get())
        if mode == "totale": self.export_storico_totale()
        elif mode == "anno": self.export_anno_dettagliato()
        elif mode == "mese":
            m_idx = mesi_nomi.index(c_mese.get()) + 1
            self.stats_refdate = datetime.date(int(c_anno.get()), m_idx, 1)
            self.export_month_detail()
        elif mode == "giorno":
            self.stats_mode.set(mode)
            self.export_stats()
        popup.destroy()
    frame_footer = tk.Frame(popup, bg=self.COLOR_WIDGET_BG)
    frame_footer.pack(side="bottom", pady=25)
    img_ok = self.icone_gui.get("salva")
    btn_ok = ttk.Label(frame_footer, compound="left", image=img_ok,
                       text=" Genera" if img_ok else "💾 Genera",
                       background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                       cursor="hand2", padding=(10, 5))
    btn_ok.pack(side="left", padx=10)
    btn_ok.bind("<Button-1>", lambda e: procedi_generazione())
    img_chiudi = self.icone_gui.get("chiudi")
    btn_chiudi = ttk.Label(frame_footer, compound="left", image=img_chiudi,
                        text=" Chiudi" if img_chiudi else "✖ Chiudi",
                        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                        cursor="hand2", padding=(10, 5))
    btn_chiudi.pack(side="left", padx=10)
    btn_chiudi.bind("<Button-1>", lambda e: popup.destroy())
