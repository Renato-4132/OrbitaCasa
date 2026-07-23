#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import os
import tempfile

import requests
import fitz
import tkinter as tk
from tkinter import ttk

# Scarica e Apri Tabella Consumi (PDF)
def scarica_tabella(self):
    import __main__ as _app
    URL_PDF_CONSUMI = _app.URL_PDF_CONSUMI
    try:
        response = requests.get(URL_PDF_CONSUMI, timeout=15)
        response.raise_for_status()
        temp_path = os.path.join(tempfile.gettempdir(), "tabella_consumi.pdf")
        with open(temp_path, "wb") as f:
            f.write(response.content)
        self._apri_viewer_tabella(temp_path)
    except Exception as e:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore nel download della tabella consumi:", e)
        self.show_custom_warning("Attenzione", "Download NON completato!\n\nSembra ci sia stato un problema. 😕")

def _apri_viewer_tabella(self, temp_path):
    import __main__ as _app
    NAME = _app.NAME
    EXPORT_FILES = _app.EXPORT_FILES
    doc = fitz.open(temp_path)
    pagina_corrente = [0]
    zoom_level = [1.5]
    toc = doc.get_toc()
    win = tk.Toplevel(self, bg=self.COLOR_BACKGROUND)
    self._viewer_tabella_win = win
    win.title(f"Tabella Consumi — {NAME}")
    win.configure(bd=0)
    win.bind('<Escape>', lambda e: win.destroy())
    header = tk.Frame(win, bg=self.COLOR_HEADER_BG, height=42)
    header.pack(fill="x")
    header.pack_propagate(False)
    dot_canvas = tk.Canvas(header, width=10, height=10,
                           bg=self.COLOR_HEADER_BG, highlightthickness=0)
    dot_canvas.create_oval(0, 0, 10, 10, fill=self.COLOR_HIGHLIGHT, outline="")
    dot_canvas.pack(side="left", padx=(16, 8), pady=16)
    tk.Label(header, text="Tabella Consumi",
             bg=self.COLOR_HEADER_BG, fg=self.COLOR_HEADER,
             font=("Segoe UI", 8, "bold")).pack(side="left")
    tk.Frame(win, bg=self.COLOR_BACKGROUND, height=1).pack(fill="x")
    frame_corpo = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    frame_corpo.pack(padx=16, pady=(12, 0), fill='both', expand=True)
    if toc:
        frame_indice = tk.Frame(frame_corpo, bg=self.COLOR_WIDGET_BG,
                                highlightbackground=self.COLOR_HEADER_BG,
                                highlightthickness=1)
        frame_indice.pack(side="left", fill="y", padx=(0, 8))

        tk.Label(frame_indice, text="Indice",
                 bg=self.COLOR_HEADER_BG, fg=self.COLOR_HEADER,
                 font=("Segoe UI", 8, "bold"),
                 padx=8, pady=6).pack(fill="x")
        sb_indice = ttk.Scrollbar(frame_indice, style="Vertical.TScrollbar")
        sb_indice.pack(side="right", fill="y")
        listbox = tk.Listbox(frame_indice,
                             yscrollcommand=sb_indice.set,
                             bg=self.COLOR_WIDGET_BG,
                             fg=self.TEXT_COLOR,
                             selectbackground=self.COLOR_HIGHLIGHT,
                             selectforeground=self.COLOR_WHITE,
                             font=("Segoe UI", 8),
                             relief="flat", bd=0,
                             activestyle="none",
                             width=28,
                             highlightthickness=0)
        listbox.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)
        sb_indice.config(command=listbox.yview)
        toc_pagine = []
        for livello, titolo, pagina in toc:
            indent = "  " * (livello - 1)
            listbox.insert(tk.END, f"{indent}{titolo}")
            toc_pagine.append(pagina - 1)
        def vai_a_voce(event):
            sel = listbox.curselection()
            if sel:
                pagina_corrente[0] = max(0, min(toc_pagine[sel[0]], len(doc) - 1))
                render_pagina()

        listbox.bind("<<ListboxSelect>>", vai_a_voce)
    frame_pdf = tk.Frame(frame_corpo, bg=self.COLOR_WIDGET_BG,
                         highlightbackground=self.COLOR_HEADER_BG,
                         highlightthickness=1)
    frame_pdf.pack(side="left", fill='both', expand=True)
    scrollbar_y = ttk.Scrollbar(frame_pdf, style="Vertical.TScrollbar")
    scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
    scrollbar_x = ttk.Scrollbar(frame_pdf, orient="horizontal")
    scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
    canvas_pdf = tk.Canvas(frame_pdf,
                           bg=self.COLOR_WIDGET_BG,
                           yscrollcommand=scrollbar_y.set,
                           xscrollcommand=scrollbar_x.set,
                           highlightthickness=0)
    canvas_pdf.pack(side=tk.LEFT, fill='both', expand=True)
    scrollbar_y.config(command=canvas_pdf.yview)
    scrollbar_x.config(command=canvas_pdf.xview)
    tk.Frame(win, bg=self.COLOR_BACKGROUND, height=1).pack(fill="x", pady=(10, 0))
    frame_ctrl = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    frame_ctrl.pack(pady=10)
    img_prev = self.icone_gui.get("indietro")
    btn_prev = ttk.Label(frame_ctrl, compound="left", image=img_prev,
                         text=" Indietro" if img_prev else "◀ Indietro",
                         background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                         cursor="hand2", padding=(10, 5))
    btn_prev.image = img_prev
    btn_prev.pack(side="left", padx=5)
    lbl_pagina = tk.Label(frame_ctrl,
                          text=f"Pagina 1 / {len(doc)}",
                          bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
                          font=("Segoe UI", 9))
    lbl_pagina.pack(side="left", padx=12)
    img_next = self.icone_gui.get("avanti")
    btn_next = ttk.Label(frame_ctrl, compound="left", image=img_next,
                         text=" Avanti" if img_next else "Avanti ▶",
                         background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                         cursor="hand2", padding=(10, 5))
    btn_next.image = img_next
    btn_next.pack(side="left", padx=5)
    tk.Frame(frame_ctrl, bg=self.COLOR_BACKGROUND, width=20).pack(side="left")
    btn_zoom_out = ttk.Label(frame_ctrl, text="  −  ",
                             background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                             cursor="hand2", padding=(8, 5), font=("Segoe UI", 11, "bold"))
    btn_zoom_out.pack(side="left", padx=2)
    lbl_zoom = tk.Label(frame_ctrl, text="150%",
                        bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
                        font=("Segoe UI", 9), width=5)
    lbl_zoom.pack(side="left")
    btn_zoom_in = ttk.Label(frame_ctrl, text="  +  ",
                            background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                            cursor="hand2", padding=(8, 5), font=("Segoe UI", 11, "bold"))
    btn_zoom_in.pack(side="left", padx=2)
    tk.Frame(frame_ctrl, bg=self.COLOR_BACKGROUND, width=20).pack(side="left")
    img_stampa = self.icone_gui.get("stampa")
    btn_stampa = ttk.Label(frame_ctrl, compound="left", image=img_stampa,
                           text=" Stampa" if img_stampa else "Stampa",
                           background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                           cursor="hand2", padding=(10, 5))
    btn_stampa.image = img_stampa
    btn_stampa.pack(side="left", padx=5)
    img_salva = self.icone_gui.get("salva")
    btn_salva = ttk.Label(frame_ctrl, compound="left", image=img_salva,
                          text=" Salva" if img_salva else "Salva",
                          background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                          cursor="hand2", padding=(10, 5))
    btn_salva.image = img_salva
    btn_salva.pack(side="left", padx=5)
    tk.Frame(frame_ctrl, bg=self.COLOR_BACKGROUND, width=20).pack(side="left")
    img_chiudi = self.icone_gui.get("chiudi")
    btn_chiudi = ttk.Label(frame_ctrl, compound="left", image=img_chiudi,
                           text=" Chiudi" if img_chiudi else "Chiudi",
                           background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                           cursor="hand2", padding=(10, 5))
    btn_chiudi.image = img_chiudi
    btn_chiudi.pack(side="left", padx=5)
    img_ref = [None]
    def render_pagina():
        page = doc[pagina_corrente[0]]
        mat = fitz.Matrix(zoom_level[0], zoom_level[0])
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("ppm")
        img = tk.PhotoImage(data=img_data)
        img_ref[0] = img
        canvas_pdf.delete("all")
        canvas_pdf.create_image(0, 0, anchor="nw", image=img)
        canvas_pdf.config(scrollregion=(0, 0, pix.width, pix.height))
        canvas_pdf.yview_moveto(0)
        lbl_pagina.config(text=f"Pagina {pagina_corrente[0] + 1} / {len(doc)}")
        lbl_zoom.config(text=f"{int(zoom_level[0] * 100)}%")
        if toc:
            pagina_att = pagina_corrente[0]
            voce_attiva = 0
            for i, p in enumerate(toc_pagine):
                if p <= pagina_att:
                    voce_attiva = i
            listbox.selection_clear(0, tk.END)
            listbox.selection_set(voce_attiva)
            listbox.see(voce_attiva)
    def vai_prev():
        if pagina_corrente[0] > 0:
            pagina_corrente[0] -= 1
            render_pagina()
    def vai_next():
        if pagina_corrente[0] < len(doc) - 1:
            pagina_corrente[0] += 1
            render_pagina()
    def zoom_in():
        if zoom_level[0] < 3.0:
            zoom_level[0] = round(zoom_level[0] + 0.25, 2)
            render_pagina()
    def zoom_out():
        if zoom_level[0] > 0.5:
            zoom_level[0] = round(zoom_level[0] - 0.25, 2)
            render_pagina()
    def stampa():
        import subprocess, os
        if os.name == 'nt':
            os.startfile(temp_path, "print")
        else:
            subprocess.run(["lp", temp_path])
    def salva():
        from tkinter import filedialog
        dest = filedialog.asksaveasfilename(
            parent=win,
            title="Salva Tabella",
            confirmoverwrite=False,
            initialdir=EXPORT_FILES,
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="Tabella Consumi.pdf"
        )
        if dest:
            import shutil
            try:
                shutil.copy2(temp_path, dest)
                self.show_custom_info("Salvataggio", f"✅ Tabella Consumi salvata in:\n{dest}")
            except Exception as e:
                self.show_custom_warning("Errore", f"❌ Salvataggio fallito:\n{e}")
    btn_stampa.bind("<Button-1>", lambda e: stampa())
    btn_salva.bind("<Button-1>", lambda e: salva())
    btn_prev.bind("<Button-1>", lambda e: vai_prev())
    btn_next.bind("<Button-1>", lambda e: vai_next())
    btn_zoom_in.bind("<Button-1>", lambda e: zoom_in())
    btn_zoom_out.bind("<Button-1>", lambda e: zoom_out())
    btn_chiudi.bind("<Button-1>", lambda e: win.destroy())
    win.bind("<Left>", lambda e: vai_prev())
    win.bind("<Right>", lambda e: vai_next())
    canvas_pdf.bind("<MouseWheel>", lambda e: canvas_pdf.yview_scroll(int(-1*(e.delta/120)), "units"))
    canvas_pdf.bind("<Button-4>", lambda e: canvas_pdf.yview_scroll(-1, "units"))
    canvas_pdf.bind("<Button-5>", lambda e: canvas_pdf.yview_scroll(1, "units"))
    win.withdraw()
    win.update_idletasks()
    min_w, min_h = 1200, 650
    w = max(win.winfo_width(), min_w)
    h = max(win.winfo_height(), min_h)
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")
    win.resizable(True, True)
    win.minsize(min_w, min_h)
    win.deiconify()
    win.attributes('-topmost', True)
    win.grab_set()
    win.focus_set()
    render_pagina()
    win.wait_window()
    doc.close()
    try:
        os.remove(temp_path)
    except Exception:
        pass

