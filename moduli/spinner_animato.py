#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import tkinter as tk

def crea_spinner_animato(parent, bg, size=36, tick_ms=35, n_raggi=10, colori=None):
    colori = colori or ["#0055FF", "#AA00FF", "#FF0055", "#00C853"]
    cvs = tk.Canvas(parent, width=size, height=size, bg=bg, highlightthickness=0, bd=0)
    stato = {"attivo": True, "frame": 0}
    _rgb_cache = {}

    def _rgb_di(colore_hex):
        rgb = _rgb_cache.get(colore_hex)
        if rgb is None:
            rgb = cvs.winfo_rgb(colore_hex)
            _rgb_cache[colore_hex] = rgb
        return rgb

    def _sfuma(colore_hex, ratio):
        c_r, c_g, c_b = _rgb_di(colore_hex)
        b_r, b_g, b_b = _rgb_di(bg)
        r = int(b_r + (c_r - b_r) * ratio) >> 8
        g = int(b_g + (c_g - b_g) * ratio) >> 8
        b = int(b_b + (c_b - b_b) * ratio) >> 8
        return f"#{r:02x}{g:02x}{b:02x}"

    def _step():
        if not stato["attivo"] or not cvs.winfo_exists():
            return
        cvs.delete("all")
        centro = size / 2
        r_est = size * 0.46
        r_int = size * 0.20
        spessore = max(2, int(size * 0.11))
        colore_base = colori[(stato["frame"] // (n_raggi * 2)) % len(colori)]
        testa = stato["frame"] % n_raggi
        for i in range(n_raggi):
            distanza = (testa - i) % n_raggi
            ratio = max(0.10, 1 - distanza / n_raggi)
            ang = math.radians(360 * i / n_raggi - 90)
            x1 = centro + r_int * math.cos(ang)
            y1 = centro + r_int * math.sin(ang)
            x2 = centro + r_est * math.cos(ang)
            y2 = centro + r_est * math.sin(ang)
            cvs.create_line(x1, y1, x2, y2, fill=_sfuma(colore_base, ratio),
                             width=spessore, capstyle="round")
        stato["frame"] += 1
        cvs.after(tick_ms, _step)

    _step()

    def stop():
        stato["attivo"] = False

    return cvs, stop
