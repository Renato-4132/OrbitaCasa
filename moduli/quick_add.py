#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import tkinter as tk

from moduli.modello_spesa import campo

# HUD budget giornaliero: calcola e mostra il limite di spesa disponibile per giorno nel mese corrente
def quick_add(self, event):
    try:
        if hasattr(self, '_quick_add_hud') and self._quick_add_hud:
            try:
                if self._quick_add_hud.winfo_exists():
                    self._quick_add_hud.destroy()
            except Exception:
                pass
            self._quick_add_hud = None
        if hasattr(self, 'tooltip_win') and self.tooltip_win:
            try:
                if self.tooltip_win.winfo_exists():
                    self.tooltip_win.destroy()
            except Exception:
                pass
            self.tooltip_win = None
        if hasattr(self, 'tooltip_timer') and self.tooltip_timer:
            self.after_cancel(self.tooltip_timer)
            self.tooltip_timer = None
        try:
            celle_giorno = set()
            for riga_celle in getattr(self.cal, "_calendar", []):
                celle_giorno.update(riga_celle)
            if event.widget in celle_giorno:
                testo = event.widget.cget("text")
                if testo.isdigit():
                    m, a = self.cal.get_displayed_month()
                    data_sel = datetime.date(a, m, int(testo))
                else:
                    data_sel = self.cal.selection_get()
            else:
                data_sel = self.cal.selection_get()
        except Exception:
            data_sel = self.cal.selection_get()
        if not data_sel:
            return
        fine_mese = (data_sel.replace(day=28) + datetime.timedelta(days=4)).replace(day=1) - datetime.timedelta(days=1)
        giorni_rimanenti = (fine_mese - data_sel).days + 1
        if giorni_rimanenti <= 0: giorni_rimanenti = 1
        entrate_mese = sum(float(campo(e, "importo", 0.0)) for d, entries in self.spese.items() 
            if d.month == data_sel.month and d.year == data_sel.year 
            for e in entries if campo(e, "tipo", "") == "Entrata")
        uscite_mese = sum(float(campo(e, "importo", 0.0)) for d, entries in self.spese.items() 
            if d.month == data_sel.month and d.year == data_sel.year 
            for e in entries if campo(e, "tipo", "") == "Uscita")
        diff_mese = entrate_mese - uscite_mese
        impegni_futuri = sum(float(campo(e, "importo", 0.0)) for d, entries in self.spese.items() 
            if data_sel < d <= fine_mese 
            for e in entries if campo(e, "tipo", "") == "Uscita")
        budget_residuo = diff_mese
        safe_spend_day = budget_residuo / giorni_rimanenti if budget_residuo > 0 else 0
        hud = tk.Toplevel(self)
        self._quick_add_hud = hud
        hud.overrideredirect(True)
        hud.attributes("-topmost", True)
        color_stato = self.COLOR_GREEN if safe_spend_day > 50 else "#FFAA00"
        if safe_spend_day <= 0: color_stato = "#FF4444"
        bg_hud = self.COLOR_WIDGET_BG
        hud.configure(bg=bg_hud, highlightbackground=color_stato, highlightthickness=1)
        hud.geometry(f"280x165+{event.x_root + 20}+{event.y_root + 10}")
        tk.Label(hud, text="Budget Reale Disponibile", font=("Arial", 9, "bold"), 
                 bg=self.COLOR_WIDGET_BG, fg=color_stato).pack(fill="x", ipady=4)
        f = tk.Frame(hud, bg=bg_hud, padx=15, pady=10)
        f.pack(fill="both", expand=True)
        tk.Label(f, text=f"Avanzo Mese: {diff_mese:.2f} €", 
                 bg=bg_hud, fg=self.TEXT_COLOR, font=("Arial", 10)).pack(anchor="w")
        tk.Label(f, text=f"Impegni previsti: -{impegni_futuri:.2f} €", 
                 bg=bg_hud, fg="#FF6B6B", font=("Arial", 9)).pack(anchor="w")
        tk.Frame(f, height=1, bg="#333333").pack(fill="x", pady=10)
        tk.Label(f, text=f"Limite al Giorno ({data_sel.day}-{fine_mese.day}):", 
                 bg=bg_hud, fg="#888888", font=("Arial", 8, "bold")).pack(anchor="w")
        tk.Label(f, text=f"{safe_spend_day:.2f} €", 
                 bg=bg_hud, fg=color_stato, font=("Arial", 18, "bold")).pack(anchor="w")
        def _chiudi_hud():
            try:
                if hud.winfo_exists():
                    hud.destroy()
            except Exception:
                pass
            self._quick_add_hud = None
        hud.after(4000, _chiudi_hud)
        hud.bind("<Button-1>", lambda e: _chiudi_hud())
    except Exception as e:
        print(f"Errore: {e}")
