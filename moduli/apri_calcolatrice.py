#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk

# Calcolatrice Interattiva
def apri_calcolatrice(self):
    if hasattr(self, '_calcolatrice_popup') and self._calcolatrice_popup and self._calcolatrice_popup.winfo_exists():
        self._calcolatrice_popup.lift()
        return
    def chiudi_calcolatrice():
        calcolatrice.destroy()
        self._calcolatrice_popup = None
    def inserisci(valore):
        entry_var.set(entry_var.get() + valore)
    def cancella():
        entry_var.set("")
        cronologia_text.config(state="normal")
        cronologia_text.delete("1.0", tk.END)
        cronologia_text.config(state="disabled")
    def calcola(event=None):
        try:
            import ast, operator
            espressione = entry_var.get().replace('%', '/100')
            operatori = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.Pow: operator.pow,
                ast.USub: operator.neg,
            }
            def valuta(nodo):
                if isinstance(nodo, ast.Constant):
                    return nodo.value
                elif isinstance(nodo, ast.BinOp):
                    return operatori[type(nodo.op)](valuta(nodo.left), valuta(nodo.right))
                elif isinstance(nodo, ast.UnaryOp):
                    return operatori[type(nodo.op)](valuta(nodo.operand))
                else:
                    raise ValueError("Operazione non supportata")
            risultato = valuta(ast.parse(espressione, mode='eval').body)
            risultato = round(risultato, 10)
            cronologia_text.config(state="normal")
            cronologia_text.insert(tk.END, f"  {espressione} = {risultato}\n")
            cronologia_text.see(tk.END)
            cronologia_text.config(state="disabled")
            entry_var.set(str(risultato))
        except Exception:
            entry_var.set("Errore")
    def usa_risultato_ricorrenze():
        try:
            self.ricorrenza_imp.set(entry_var.get())
            chiudi_calcolatrice()
        except Exception:
            entry_var.set("Errore")
    def usa_risultato_principale():
        try:
            self.imp_entry.delete(0, tk.END)
            self.imp_entry.insert(0, entry_var.get())
            chiudi_calcolatrice()
        except Exception:
            entry_var.set("Errore")
    calcolatrice = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    calcolatrice.transient(self)
    self._calcolatrice_popup = calcolatrice
    calcolatrice.withdraw()
    calcolatrice.title("Calcolatrice")
    calcolatrice.resizable(False, False)
    calcolatrice.protocol("WM_DELETE_WINDOW", chiudi_calcolatrice)
    calcolatrice.bind("<Escape>", lambda e: chiudi_calcolatrice())
    calcolatrice.bind("<Return>", calcola)
    calcolatrice.bind("<KP_Enter>", calcola)
    larghezza, altezza = 280, 320
    x = (calcolatrice.winfo_screenwidth() // 2) - (larghezza // 2)
    y = (calcolatrice.winfo_screenheight() // 2) - (altezza // 2)
    calcolatrice.geometry(f"{larghezza}x{altezza}+{x}+{y}")
    calcolatrice.deiconify()
    calcolatrice.after(100, lambda: entry.focus_set())
    entry_var = tk.StringVar()
    def valida_input(P):
        return all(c in set("0123456789.+-*/%()")  for c in P)
    vcmd = (calcolatrice.register(valida_input), '%P')
    entry = ttk.Entry(calcolatrice, textvariable=entry_var,
                     font=("Arial", 13, "bold"),
                     justify="right", validate="key",
                     validatecommand=vcmd)
    entry.pack(fill="x", padx=6, pady=(6, 2), ipady=2)
    cronologia_text = tk.Text(calcolatrice, height=4,
                              bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                              font=("Arial", 7), relief="flat", bd=0,
                              padx=4, pady=1, state="disabled")
    cronologia_text.pack(fill="x", padx=6, pady=(0, 2))
    tasti = [
        ["7", "8", "9", "/"],
        ["4", "5", "6", "*"],
        ["1", "2", "3", "-"],
        ["0", ".", "%", "+"],
    ]
    def crea_lbl_tasto(parent, testo, comando):
        def esegui():
            comando()
            entry.focus_set()
        lbl = ttk.Label(parent, text=testo,
                        font=("Arial", 11, "bold"),
                        background=self.COLOR_WIDGET_BG,
                        foreground=self.TEXT_COLOR,
                        anchor="center", cursor="hand2",
                        padding=(0, 3))
        lbl.bind("<Button-1>", lambda e: esegui())
        return lbl
    grid_frame = tk.Frame(calcolatrice, bg=self.COLOR_TOPLEVEL)
    grid_frame.pack(fill="both", expand=True, padx=6, pady=1)
    grid_frame.columnconfigure((0,1,2,3), weight=1)
    for r, riga in enumerate(tasti):
        grid_frame.rowconfigure(r, weight=1)
        for c, tasto in enumerate(riga):
            lbl = crea_lbl_tasto(grid_frame, tasto, lambda v=tasto: inserisci(v))
            lbl.grid(row=r, column=c, sticky="nsew", padx=2, pady=1)
    act_frame = tk.Frame(calcolatrice, bg=self.COLOR_TOPLEVEL)
    act_frame.pack(fill="x", padx=6, pady=(1, 6))
    act_frame.columnconfigure((0,1,2,3), weight=1)
    img_clear = self.icone_gui.get("delete")
    img_ric   = self.icone_gui.get("descrizione")
    img_princ = self.icone_gui.get("aggiungi")
    img_eq    = self.icone_gui.get("check")
    azioni = [
        (img_clear, " C",              cancella,                self.COLOR_RED_SMOOTH),
        (img_ric,   " → Ricorrenze",   usa_risultato_ricorrenze, self.TEXT_COLOR),
        (img_princ, " → Principale",   usa_risultato_principale, self.TEXT_COLOR),
        (img_eq,    " =",              calcola,                 self.COLOR_GREEN_SMOOTH),
    ]
    for i, (img, testo, cmd, fg) in enumerate(azioni):
        lbl = ttk.Label(act_frame, compound="left", image=img,
                        text=testo, background=self.COLOR_WIDGET_BG,
                        foreground=fg, font=("Arial", 8, "bold"),
                        cursor="hand2", anchor="center", padding=(1, 3))
        if img:
            lbl.image = img
        lbl.grid(row=0, column=i, sticky="nsew", padx=2)
        lbl.bind("<Button-1>", lambda e, c=cmd: c())
