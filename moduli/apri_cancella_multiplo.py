#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk

# Finestra di Cancellazione Multipla Categorie
def apri_cancella_multiplo(self):
    popup = tk.Toplevel(self,bg=self.COLOR_TOPLEVEL)
    popup.transient(self)
    popup.title("Cancella Categorie")
    popup.resizable(True, True)
    larghezza, altezza = 400, 500
    x = self.winfo_x() + (self.winfo_width() // 2) - (larghezza // 2)
    y = self.winfo_y() + (self.winfo_height() // 2) - (altezza // 2)
    popup.geometry(f"{larghezza}x{altezza}+{x}+{y}")
    popup.minsize(larghezza, altezza)
    popup.wait_visibility()
    popup.grab_set()
    tk.Label(
        popup,
        text="Seleziona le categorie da cancellare:",
        bg=self.COLOR_TOPLEVEL,
        fg=self.TEXT_COLOR,
        font=("Arial", 10, "bold")
    ).pack(pady=(10, 5))
    self.elimina_spese_var = tk.BooleanVar()
    tk.Checkbutton(
        popup,
        text="Elimina anche Movimenti associati",
        variable=self.elimina_spese_var,
        anchor="w",
        bg="yellow",       
        activebackground="gold"  
    ).pack(fill="x", padx=15, pady=(5, 0))
    contenitore = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    contenitore.pack(fill="both", expand=True, padx=10, pady=5)
    canvas = tk.Canvas(contenitore, bg=self.COLOR_TOPLEVEL)
    scrollbar = ttk.Scrollbar(contenitore, orient="vertical", command=canvas.yview, style="Vertical.TScrollbar")
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    scroll_frame = tk.Frame(canvas, bg=self.COLOR_TOPLEVEL)
    window_id = canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    def resize_scroll_frame(event):
        canvas.itemconfig(window_id, width=event.width)
    canvas.bind("<Configure>", resize_scroll_frame)
    def aggiorna_scroll(event):
         canvas.configure(scrollregion=canvas.bbox("all"))
    scroll_frame.bind("<Configure>", aggiorna_scroll)
    def _scroll(e):
        canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
    def _scroll_up(e):
        canvas.yview_scroll(-1, "units")
    def _scroll_down(e):
        canvas.yview_scroll(1, "units")
    popup.bind_all("<MouseWheel>", _scroll)
    popup.bind_all("<Button-4>", _scroll_up)
    popup.bind_all("<Button-5>", _scroll_down)
    popup.bind("<Destroy>", lambda e: (
        popup.unbind_all("<MouseWheel>"),
        popup.unbind_all("<Button-4>"),
        popup.unbind_all("<Button-5>")
    ) if e.widget is popup else None)
    self.checkbox_vars = {}
    for cat in sorted(set(self.categorie), key=lambda c: c.lower()):
        if cat not in ("Generica", self.CATEGORIA_RIMOSSA):
            var = tk.BooleanVar()
            chk = tk.Checkbutton(
                scroll_frame,
                text=cat, 
                variable=var, 
                anchor="w",
                bg=self.COLOR_TOPLEVEL,
                fg=self.TEXT_COLOR,
                activebackground=self.COLOR_TOPLEVEL,
                activeforeground=self.TEXT_COLOR,
                selectcolor=self.COLOR_TOPLEVEL,
                highlightthickness=0
            )
            chk.pack(fill="x", padx=5, pady=2)
            self.checkbox_vars[cat] = var
    btn_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    btn_frame.pack(pady=10)
    img_elimina = self.icone_gui.get("cancella")
    btn_elimina = ttk.Label(btn_frame, compound="left", image=img_elimina, text=" Elimina Selezionate" if img_elimina else "Elimina Selezionate", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
    btn_elimina.pack(side="left", padx=5)
    btn_elimina.bind("<Button-1>", lambda e: self.cancella_categorie_checkbox(popup))
    img_chiudi_pop = self.icone_gui.get("chiudi")
    btn_chiudi_pop = ttk.Label(btn_frame, compound="left", image=img_chiudi_pop, text=" Chiudi" if img_chiudi_pop else "Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
    btn_chiudi_pop.pack(side="left", padx=5)
    btn_chiudi_pop.bind("<Button-1>", lambda e: popup.destroy())
