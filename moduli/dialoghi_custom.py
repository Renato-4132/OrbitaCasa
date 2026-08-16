#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import tkinter as tk
from tkinter import ttk

from moduli.spinner_animato import crea_spinner_animato

# Popup Messaggi di Sistema
def show_custom_warning(self, title, message):
    self._show_toast_dialog(title, message, bg="yellow", fg="black", kind="warning")
def show_custom_info(self, title, message):
    self._show_toast_dialog(title, message, bg="lightblue", fg="black", kind="info")
def show_custom_askyesno(self, title, message):
    if hasattr(self, '_yesno_popup') and self._yesno_popup and self._yesno_popup.winfo_exists():
        self._yesno_popup.lift()
        self._yesno_popup.focus_force()
        return False
    return self._show_toast_dialog(title, message, bg="orange", fg="black", kind="yesno")

def _show_toast_dialog(self, title, message, bg, fg, kind="ok"):
    import __main__ as _app
    WARN_TIMEOUT = _app.WARN_TIMEOUT
    USE_WAIT_WINDOW = _app.USE_WAIT_WINDOW
    attr = {"yesno": "_yesno_popup", "warning": "_warn_popup", "info": "_info_popup"}.get(kind, "_msg_popup")
    if hasattr(self, attr) and getattr(self, attr) and getattr(self, attr).winfo_exists():
        getattr(self, attr).lift()
        getattr(self, attr).focus_force()
        return False if kind == "yesno" else None
    result = {"value": False if kind == "yesno" else None}
    timer_data = {"id": None, "bar_id": None}
    dialog = tk.Toplevel(self)
    dialog.transient(self)
    setattr(self, attr, dialog)
    dialog.overrideredirect(True)
    dialog.attributes("-topmost", True)
    dialog.withdraw()
    dialog.config(bg=bg)
    outer = tk.Frame(dialog, bg=bg, padx=20, pady=14)
    outer.pack(fill="both", expand=True)
    tk.Label(outer, text=title, font=("Arial", 10, "bold"), bg=bg, fg=fg, anchor="center").pack(fill="x")
    tk.Label(outer, text=message, font=("Arial", 10), bg=bg, fg=fg, justify="center", anchor="center", wraplength=400).pack(fill="x", pady=(4, 10))
    RAGGIERA_SIZE = 36
    bar_cvs = tk.Canvas(outer, width=RAGGIERA_SIZE, height=RAGGIERA_SIZE, bg=bg, highlightthickness=0, bd=0)
    if not USE_WAIT_WINDOW:
        bar_cvs.pack(pady=(0, 10))
    btn_frame = tk.Frame(outer, bg=bg)
    btn_frame.pack(fill="x")
    def close_clean(value):
        if timer_data["id"]: dialog.after_cancel(timer_data["id"])
        if timer_data["bar_id"]: dialog.after_cancel(timer_data["bar_id"])
        result["value"] = value
        dialog.destroy()
    if kind == "yesno":
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        b_yes = ttk.Label(btn_frame, image=self.icone_gui.get("check"), text=" Sì", compound="left", cursor="hand2", background=bg, foreground=fg, font=("Arial", 10, "bold"), anchor="center")
        b_yes.grid(row=0, column=0, padx=5, sticky="nsew")
        b_yes.bind("<Button-1>", lambda e: close_clean(True))
        b_no = ttk.Label(btn_frame, image=self.icone_gui.get("chiudi"), text=" No", compound="left", cursor="hand2", background=bg, foreground=fg, font=("Arial", 10, "bold"), anchor="center")
        b_no.grid(row=0, column=1, padx=5, sticky="nsew")
        b_no.bind("<Button-1>", lambda e: close_clean(False))
    else:
        b_ok = ttk.Label(btn_frame, image=self.icone_gui.get("check"), text=" OK", compound="left", cursor="hand2", background=bg, foreground=fg, font=("Arial", 10, "bold"), anchor="center")
        b_ok.pack(ipadx=10, ipady=5)
        b_ok.bind("<Button-1>", lambda e: close_clean(None))
    dialog.update_idletasks()
    w, h = max(dialog.winfo_reqwidth(), 320), dialog.winfo_reqheight()
    px, py, pw, ph = self.winfo_rootx(), self.winfo_rooty(), self.winfo_width(), self.winfo_height()
    dialog.geometry(f"{w}x{h}+{px + pw // 2 - w // 2}+{py + ph // 2 - h // 2}")
    dialog.deiconify()
    dialog.wait_visibility()
    dialog.grab_set()
    if not USE_WAIT_WINDOW:
        N_RAGGI = 10
        R_EST = RAGGIERA_SIZE * 0.46
        R_INT = RAGGIERA_SIZE * 0.20
        SPESSORE = max(2, int(RAGGIERA_SIZE * 0.11))
        centro = RAGGIERA_SIZE / 2
        angoli = [math.radians(360 * i / N_RAGGI - 90) for i in range(N_RAGGI)]
        raggiera = [
            bar_cvs.create_line(
                centro + R_INT * math.cos(a), centro + R_INT * math.sin(a),
                centro + R_EST * math.cos(a), centro + R_EST * math.sin(a),
                fill=fg, width=SPESSORE, capstyle="round"
            ) for a in angoli
        ]
        elapsed = [0]
        TICK_MS = 20
        COLOR_WARN = self.COLOR_RED
        def get_fade_color(f_color, t_color, ratio):
            f_r, f_g, f_b = dialog.winfo_rgb(f_color)
            t_r, t_g, t_b = dialog.winfo_rgb(t_color)
            r = int(f_r + (t_r - f_r) * (1-ratio)) >> 8
            g = int(f_g + (t_g - f_g) * (1-ratio)) >> 8
            b = int(f_b + (t_b - f_b) * (1-ratio)) >> 8
            return f"#{r:02x}{g:02x}{b:02x}"
        def tick_bar():
            elapsed[0] += TICK_MS
            ratio = max(0.0, 1.0 - elapsed[0] / WARN_TIMEOUT)
            if ratio > 0:
                current_color = get_fade_color(fg, COLOR_WARN, ratio)
                n_spenti = int((1 - ratio) * N_RAGGI)
                for i, seg_id in enumerate(raggiera):
                    if i < n_spenti:
                        bar_cvs.itemconfig(seg_id, state="hidden")
                    else:
                        bar_cvs.itemconfig(seg_id, state="normal", fill=current_color)
                timer_data["bar_id"] = dialog.after(TICK_MS, tick_bar)
            else:
                close_clean(False if kind == "yesno" else None)
        timer_data["bar_id"] = dialog.after(TICK_MS, tick_bar)
        timer_data["id"] = dialog.after(WARN_TIMEOUT, lambda: close_clean(False if kind == "yesno" else None))
    dialog.wait_window()
    return result["value"]

# Popup Messaggi Toast di Sistema
def show_toast(self, message, duration=1500, parent=None):
    if parent is None: parent = self
    if hasattr(self, '_toast_after_id') and self._toast_after_id:
        try: self.after_cancel(self._toast_after_id)
        except: pass
    if hasattr(self, '_toast_win') and self._toast_win:
        try: self._toast_win.destroy()
        except: pass
    bg, fg = self.COLOR_ORANGE, self.COLOR_BLACK
    toast = tk.Toplevel(self)
    self._toast_win = toast
    toast.withdraw()
    toast.overrideredirect(True)
    toast.attributes("-topmost", True)
    toast.config(bg=self.COLOR_HIGHLIGHT)
    inner = tk.Frame(toast, bg=bg, padx=15, pady=10, highlightbackground=self.COLOR_HIGHLIGHT, highlightthickness=1)
    inner.pack(expand=True, fill="both")
    cvs, _ = crea_spinner_animato(inner, bg, size=28, tick_ms=30)
    cvs.pack(side="left", padx=(0, 10))
    tk.Label(inner, text=message, font=("Arial", 10, "bold"), bg=bg, fg=fg).pack(side="left")
    toast.update_idletasks()
    w, h = toast.winfo_reqwidth(), toast.winfo_reqheight()
    px, py, pw, ph = parent.winfo_rootx(), parent.winfo_rooty(), parent.winfo_width(), parent.winfo_height()
    toast.geometry(f"+{px+(pw//2)-(w//2)}+{py+(ph//2)-(h//2)}")
    toast.deiconify()
    self._toast_after_id = self.after(duration, lambda: toast.destroy() if toast.winfo_exists() else None)
