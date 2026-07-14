#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk

# Popup di Selezione Periodo/Sezioni e Avvio Generazione Report PDF
def genera_report_pdf(self):
    import datetime
    oggi = datetime.date.today()
    anni_disponibili = sorted(
        set(str(d.year) for d in self.spese.keys() if isinstance(d, datetime.date)),
        reverse=True
    )
    if not anni_disponibili:
        self.show_custom_warning("Report PDF", "Nessun dato disponibile per generare il report.")
        return
    if hasattr(self, '_report_periodo_popup') and self._report_periodo_popup and \
            self._report_periodo_popup.winfo_exists():
        self._report_periodo_popup.lift()
        self._report_periodo_popup.focus_force()
        return
    sel = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    self._report_periodo_popup = sel
    sel.title("Report PDF — Seleziona Periodo")
    sel.withdraw()
    self.update_idletasks()
    w, h = 500, 240
    x = self.winfo_rootx() + (self.winfo_width()  // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    sel.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")
    sel.resizable(False, False)
    sel.transient(self)
    sel.deiconify()
    sel.lift()
    sel.focus_force()
    sel.bind("<Escape>", lambda e: sel.destroy())
    sel.bind("<Destroy>", lambda e: setattr(self, '_report_periodo_popup', None)
              if e.widget is sel else None)
    MESI_NOMI = ["Tutti", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio",
                 "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    def _riga(parent, etichetta, var, valori, larghezza):
        row = ttk.Frame(parent, padding=(10, 4, 10, 4))
        row.pack(fill=tk.X)
        ttk.Label(row, text=etichetta, font=("Arial", 9, "bold"), width=14,
                  anchor="w").pack(side=tk.LEFT)
        ttk.Combobox(row, textvariable=var, values=valori,
                     width=larghezza, state="readonly",
                     style="Border.TCombobox").pack(side=tk.LEFT)
    anno_da_var = tk.StringVar(value=anni_disponibili[-1])
    anno_a_var  = tk.StringVar(value=anni_disponibili[0])
    mese_var    = tk.StringVar(value="Tutti")
    ttk.Frame(sel, height=14).pack()
    _riga(sel, "Anno iniziale:", anno_da_var, anni_disponibili, 10)
    _riga(sel, "Anno finale:",   anno_a_var,  anni_disponibili, 10)
    _riga(sel, "Mese:",          mese_var,    MESI_NOMI,        14)
    sep = ttk.Frame(sel, height=1)
    sep.pack(fill=tk.X, padx=20, pady=(8, 4))
    sezioni_var = {
        "mesi":        tk.BooleanVar(value=True),
        "categorie":   tk.BooleanVar(value=True),
        "storico":     tk.BooleanVar(value=True),
        "portafoglio": tk.BooleanVar(value=True),
    }
    sezioni_lbl = {
        "mesi":        "Dettaglio mesi",
        "categorie":   "Categorie",
        "storico":     "Bilancio storico",
        "portafoglio": "Portafoglio bancario",
    }
    ttk.Label(sel, text="Sezioni da includere:", font=("Arial", 8, "bold"),
              anchor="w").pack(padx=20, anchor="w")
    chk_frame = ttk.Frame(sel, padding=(10, 0, 10, 0))
    chk_frame.pack(fill=tk.X)

    for chiave, etichetta in sezioni_lbl.items():
        ttk.Checkbutton(chk_frame, text=etichetta,
                        variable=sezioni_var[chiave]).pack(side=tk.LEFT, padx=4)
    ttk.Label(sel, text="Il report includerà tutti i movimenti nel periodo selezionato.",
              font=("Arial", 8)).pack(padx=20, pady=(6, 0), anchor="w")
    btn_frame = ttk.Frame(sel, padding=(10, 16, 10, 8))
    btn_frame.pack(fill=tk.X)
    def _avvia(e=None):
        import threading
        try:
            a_da = int(anno_da_var.get())
            a_a  = int(anno_a_var.get())
            if a_da > a_a:
                a_da, a_a = a_a, a_da
        except ValueError:
            self.show_custom_warning("Report PDF", "Anno non valido.")
            return
        mese_idx = MESI_NOMI.index(mese_var.get())
        sezioni = {k: v.get() for k, v in sezioni_var.items()}
        sel.destroy()
        prog = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
        prog.transient(self)
        prog.overrideredirect(True)
        prog.resizable(False, False)
        pw, ph = 340, 72
        px = self.winfo_rootx() + (self.winfo_width()  // 2) - (pw // 2)
        py = self.winfo_rooty() + (self.winfo_height() // 2) - (ph // 2)
        prog.geometry(f"{pw}x{ph}+{px}+{py}")
        pf = tk.Frame(prog, bg=self.COLOR_WIDGET_BG, bd=0,
                      highlightbackground=self.COLOR_HIGHLIGHT, highlightthickness=1)
        pf.pack(expand=True, fill='both')
        label_testo = str(a_da) if a_da == a_a else f"{a_da}–{a_a}"
        if mese_idx > 0:
            label_testo += f"  ·  {MESI_NOMI[mese_idx]}"
        tk.Label(pf, text=f"Generazione report in corso…\n({label_testo})",
                 font=("Segoe UI", 9, "bold"), justify="center",
                 bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HIGHLIGHT).pack(expand=True)
        prog.lift()
        prog.attributes('-topmost', True)
        self.update()
        def _genera():
            try:
                self._genera_report_pdf_core(anno_da=a_da, anno_a=a_a, mese_filtro=mese_idx, sezioni=sezioni)
            except Exception as e:
                _err = str(e)
                self.after(0, lambda: self.show_custom_warning(
                    "Errore Report", f"Errore durante la generazione:\n{_err}"))
            finally:
                self.after(0, prog.destroy)
        threading.Thread(target=_genera, daemon=True).start()
    pulsanti = [
        ("report", " Genera PDF", _avvia,                  "LEFT"),
        ("chiudi", " Annulla",    lambda e: sel.destroy(),  "RIGHT"),
    ]
    for ico, testo, cmd, lato in pulsanti:
        img = self.icone_gui.get(ico)
        btn = ttk.Label(btn_frame, compound="left", image=img,
                        text=testo if img else testo.strip(),
                        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                        cursor="hand2", padding=(10, 5))
        btn.pack(side=tk.LEFT if lato == "LEFT" else tk.RIGHT, padx=4)
        btn.bind("<Button-1>", cmd)
