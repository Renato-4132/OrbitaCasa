#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk

# Menu Copia Incolla
def configura_menu_contestuale_globale(self):
    self.menu_contestuale = tk.Menu(self, tearoff=0,
                                    background=self.COLOR_WIDGET_BG,
                                    foreground=self.TEXT_COLOR,
                                    activebackground="#61AFEF",
                                    activeforeground="white")
    self.last_focused_widget = None
    self.menu_contestuale.add_command(label="Taglia", command=lambda: self._esegui_comando_menu("<<Cut>>"))
    self.menu_contestuale.add_command(label="Copia", command=lambda: self._esegui_comando_menu("<<Copy>>"))
    self.menu_contestuale.add_command(label="Incolla", command=lambda: self._esegui_comando_menu("<<Paste>>"))
    self.menu_contestuale.add_separator()
    self.menu_contestuale.add_command(label="Seleziona Tutto", command=self._global_select_all)
    for cls in ("TEntry", "TCombobox", "Entry", "Text"):
        self.bind_class(cls, "<Button-3>", self._mostra_menu_globale)
    self.menu_contestuale.bind("<Leave>", self._avvia_timer_chiusura)
    self.menu_contestuale.bind("<Enter>", self._annulla_timer_chiusura)

def _esegui_comando_menu(self, comando):
    if self.last_focused_widget:
        try:
            self.last_focused_widget.event_generate(comando)
        finally:
            self._chiudi_menu_sicuro()

def _mostra_menu_globale(self, event):
    try:
        self._annulla_timer_chiusura()
        self.last_focused_widget = event.widget
        if hasattr(self.last_focused_widget, 'focus_set'):
            self.last_focused_widget.focus_set()
        self.menu_contestuale.tk_popup(event.x_root, event.y_root)
    finally:
        self.menu_contestuale.grab_release()

def _chiudi_menu_sicuro(self):
    try:
        self.menu_contestuale.unpost()
        self.menu_contestuale.grab_release()
    except tk.TclError:
        pass

def _avvia_timer_chiusura(self, event=None):
    self.timer_menu = self.after(400, self._chiudi_menu_sicuro)

def _annulla_timer_chiusura(self, event=None):
    if hasattr(self, 'timer_menu'):
        self.after_cancel(self.timer_menu)

def _global_select_all(self):
    w = self.last_focused_widget
    if w and isinstance(w, (tk.Entry, ttk.Entry, ttk.Combobox)):
        w.selection_range(0, 'end')
        w.icursor('end')
    elif w and hasattr(w, "tag_add"):
        w.tag_add("sel", "1.0", "end")
    self._chiudi_menu_sicuro()
