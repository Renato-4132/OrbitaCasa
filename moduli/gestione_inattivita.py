#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk

from moduli.spinner_animato import crea_spinner_animato


# Gestione Avanzata di Inattività e Minimizzazione (Auto-Lock)
def _attiva_timer_inattivita(self):
    if hasattr(self, '_timer_inattivita') and self._timer_inattivita:
        self.after_cancel(self._timer_inattivita)
        self._timer_inattivita = None
    timeout = getattr(self, '_timeout_inattivita', 1200000)
    self._timer_inattivita = self.after(timeout, self._iconizza_finestra)

def _reset_inattivita(self, cancel_countdown=False): 
    if cancel_countdown:
        if getattr(self, '_countdown_timer_id', None):
            self.after_cancel(self._countdown_timer_id)
            self._countdown_timer_id = None
        if getattr(self, '_countdown_splash', None):
            try: self._countdown_splash.destroy()
            except: pass
            self._countdown_splash = None
        self._attiva_timer_inattivita() 
        return 
    if self.state() == "iconic":
        self._attiva_timer_inattivita()
        return
    self._attiva_timer_inattivita()

def _iconizza_finestra(self):
    if self.state() == "iconic":
        self._attiva_timer_inattivita()
        return
    if getattr(self, '_win_reg', None) and self._win_reg.winfo_exists():
        self._attiva_timer_inattivita()
        return    
    toplevel_active = False
    for widget in self.winfo_children():
        if isinstance(widget, tk.Toplevel) and widget.winfo_ismapped():
            if widget != getattr(self, '_countdown_splash', None):
                toplevel_active = True
                break
    if toplevel_active:
        self._attiva_timer_inattivita() 
        return
    self._mostra_avviso_countdown()

def _finalizza_iconizzazione(self):
    if getattr(self, '_win_reg', None) and self._win_reg.winfo_exists():
            if getattr(self, '_countdown_splash', None):
                    try: self._countdown_splash.destroy()
                    except: pass
                    self._countdown_splash = None
            self._attiva_timer_inattivita()
            return
    if getattr(self, '_countdown_splash', None):
        try: self._countdown_splash.destroy()
        except: pass
        self._countdown_splash = None
    self.iconify()
    self.mostra_avviso_iconizzata()
    self._attiva_timer_inattivita()

def mostra_avviso_iconizzata(self):
    import __main__ as _app
    NAME = _app.NAME
    VERSION = _app.VERSION
    splash = tk.Toplevel(self)
    splash.overrideredirect(True)
    splash.attributes("-topmost", True)
    splash.configure(
        bg=self.COLOR_WIDGET_BG, 
        highlightthickness=1, 
        highlightbackground=self.COLOR_HIGHLIGHT
    )
    width, height = 300, 145
    sw = splash.winfo_screenwidth()
    sh = splash.winfo_screenheight()
    splash.geometry(f"{width}x{height}+{(sw - width) // 2}+{(sh - height) // 2}")
    tk.Frame(splash, bg=self.COLOR_HIGHLIGHT, height=1).pack(fill="x", side="top")
    container = tk.Frame(splash, bg=self.COLOR_WIDGET_BG, padx=15, pady=10)
    container.pack(fill="both", expand=True)
    label = tk.Label(
        container,
        text=f"{NAME} v.{VERSION}\n\nFinestra minimizzata per inattività.",
        font=("Arial", 9, "bold"),
        fg=self.TEXT_COLOR,
        bg=self.COLOR_WIDGET_BG,
        justify="center"
    )
    label.pack(expand=True, fill="x")
    cvs, _ = crea_spinner_animato(container, self.COLOR_WIDGET_BG, size=36, tick_ms=30)
    cvs.pack(side="top", pady=(5, 0))
    splash.update()
    splash.after(1000, splash.destroy)

def _mostra_avviso_countdown(self):
    if getattr(self, '_win_reg', None) and self._win_reg.winfo_exists():
            self._attiva_timer_inattivita()
            return
    for attr in ('_timer_inattivita', '_countdown_timer_id'):
        timer = getattr(self, attr, None)
        if timer:
            self.after_cancel(timer)
            setattr(self, attr, None)
    if self._countdown_splash:
        self._countdown_splash.destroy()
        self._countdown_splash = None
    splash = tk.Toplevel(self)
    splash.overrideredirect(True)
    splash.attributes("-topmost", True)
    splash.configure(
        bg=self.COLOR_WIDGET_BG,
        highlightthickness=1,
        highlightbackground=self.COLOR_HIGHLIGHT
    )
    width, height = 300, 140
    sw = splash.winfo_screenwidth()
    sh = splash.winfo_screenheight()
    splash.geometry(f"{width}x{height}+{(sw - width) // 2}+{(sh - height) // 2}")
    tk.Frame(splash, bg=self.COLOR_HIGHLIGHT, height=1).pack(fill="x", side="top")
    container = tk.Frame(splash, bg=self.COLOR_WIDGET_BG, padx=15, pady=10)
    container.pack(fill="both", expand=True)
    label = tk.Label(
        container,
        text="",
        font=("Arial", 9, "bold"),
        fg=self.TEXT_COLOR,
        bg=self.COLOR_WIDGET_BG,
        justify="center"
    )
    label.pack(expand=True, fill="x")
    splash.update()
    self._countdown_splash = splash
    self._countdown_label = label
    
    for widget in (splash, container, label):
        widget.bind("<Motion>", lambda e: self._reset_inattivita(cancel_countdown=True))
    self._aggiorna_countdown(self._countdown_delay)

def _aggiorna_countdown(self, remaining_ms):
    import __main__ as _app
    NAME = _app.NAME
    VERSION = _app.VERSION
    if getattr(self, '_win_reg', None) and self._win_reg.winfo_exists():
            if self._countdown_splash:
                    try: self._countdown_splash.destroy()
                    except: pass
                    self._countdown_splash = None
            self._attiva_timer_inattivita()
            return
    if not self._countdown_splash:
        return
    if remaining_ms <= 0:
        self._finalizza_iconizzazione()
        return
    seconds = remaining_ms // 1000
    self._countdown_label.config(
        text=f"{NAME} v.{VERSION}\n\nNessuna attività rilevata.\nMinimizzazione tra {seconds} secondi."
    )
    self._countdown_timer_id = self.after(
        1000,
        lambda: self._aggiorna_countdown(remaining_ms - 1000)
    )
    
def _iconizza_finestra_startup(self):
    if getattr(self, '_win_reg', None) and self._win_reg.winfo_exists():
            return 
    toplevel_active = False
    for widget in self.winfo_children():
        if isinstance(widget, tk.Toplevel) and widget.winfo_ismapped():
            toplevel_active = True
            break
    if toplevel_active:
        return 
    self.iconify()
    self.mostra_avviso_x()
    
def _iconizza_finestra_x(self):
    import __main__ as _app
    CLOSE = _app.CLOSE
    if getattr(self, '_win_reg', None) and self._win_reg.winfo_exists():
            try:
                    self._on_close()
            except tk.TclError:
                    pass
            return
    stato = self.wm_state()
    if CLOSE and stato == "normal":
        try:
            self.save_db()
        except:
            pass
        if hasattr(self, "_splash_reg"):
            try:
                if self._splash_reg.winfo_exists():
                    self._splash_reg.withdraw()
            except:
                pass
        self.mostra_avviso_x()
        self.iconify()
    else:
        try:
            self._on_close()
        except tk.TclError:
            pass

def mostra_avviso_x(self):
    import __main__ as _app
    NAME = _app.NAME
    splash = tk.Toplevel(self)
    splash.overrideredirect(True)
    splash.attributes("-topmost", True)
    splash.configure(
        bg=self.COLOR_WIDGET_BG,
        highlightthickness=1,
        highlightbackground=self.COLOR_HIGHLIGHT
    )
    width, height = 340, 160
    sw = splash.winfo_screenwidth()
    sh = splash.winfo_screenheight()
    splash.geometry(f"{width}x{height}+{(sw - width) // 2}+{(sh - height) // 2}")
    tk.Frame(splash, bg=self.COLOR_HIGHLIGHT, height=1).pack(fill="x", side="top")
    container = tk.Frame(splash, bg=self.COLOR_WIDGET_BG, padx=22, pady=10)
    container.pack(fill="both", expand=True)
    tk.Label(
        container,
        text=f"{NAME} — Attivo in background",
        font=("Arial", 10, "bold"),
        fg=self.TEXT_COLOR,
        bg=self.COLOR_WIDGET_BG
    ).pack(side="top")
    tk.Frame(container, bg=self.COLOR_HEADER_BG, height=1).pack(fill="x", pady=(8, 8))
    tk.Label(
        container,
        text="Tasto destro sull'icona Tray per chiudere\n"
             "(disponibile solo quando l'app è minimizzata)",
        font=("Arial", 8),
        fg=self.TEXT_COLOR,
        bg=self.COLOR_WIDGET_BG,
        justify="center"
    ).pack(side="top")
    cvs, _ = crea_spinner_animato(container, self.COLOR_WIDGET_BG, size=36, tick_ms=30)
    cvs.pack(side="top", pady=(10, 0))
    splash.update()
    splash.after(1000, splash.destroy)
