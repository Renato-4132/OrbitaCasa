#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import math
import threading
import tkinter as tk
from tkinter import ttk, filedialog

# Analisi e Confronto Bollette/Documenti con Gemini AI
def confronta_bollette_ia(self):
    import __main__ as _app
    API_KEY = _app.API_KEY
    GEMINI = _app.GEMINI
    genai_client = _app.genai_client
    types = _app.types
    EXPORT_FILES = _app.EXPORT_FILES
    if not API_KEY:
        self.show_custom_warning("Configurazione AI Necessaria",
            "Questa funzione richiede una chiave API Gemini (gratuita).\n\n"
            "Vai nella sezione Impostazioni e clicca sul pulsante 'Ottieni'.\n")
        return
    if hasattr(self, '_confronta_bollette_win') and self._confronta_bollette_win.winfo_exists():
        self._confronta_bollette_win.lift()
        self._confronta_bollette_win.focus_force()
        return
    popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    self._confronta_bollette_win = popup
    popup.withdraw()
    popup.title("Analisi e Confronto Documenti — Gemini AI")
    w, h = 1000, 630
    x = self.winfo_rootx() + (self.winfo_width()  // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    popup.geometry(f"{w}x{h}+{max(0,x)}+{max(0,y)}")
    popup.minsize(w, h)
    popup.resizable(True, True)
    popup.bind("<Escape>", lambda e: popup.destroy())
    hdr = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    hdr.pack(fill="x", padx=18, pady=(14, 4))
    ico_ai = self.icone_gui.get("sync")
    ttk.Label(hdr, image=ico_ai, text="  Analisi e Confronto Documenti AI",
              compound="left", style="Header.TLabel",
              font=("Segoe UI", 12, "bold")).pack(side="left")
    file_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    file_frame.pack(fill="x", padx=18, pady=(4, 0))
    tk.Label(file_frame, text="Documenti caricati (PDF / immagini):",
             bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
             font=("Segoe UI", 9, "bold")).pack(anchor="w")
    list_outer = tk.Frame(file_frame, bg=self.COLOR_TOPLEVEL)
    list_outer.pack(fill="x", pady=(4, 0))
    lb_scroll = ttk.Scrollbar(list_outer, orient="vertical")
    lb_scroll.pack(side="right", fill="y")
    listbox = tk.Listbox(list_outer, height=5,
                         bg=self.COLOR_WHITE, fg=self.COLOR_BLACK,
                         selectbackground=self.COLOR_HIGHLIGHT,
                         font=("Segoe UI", 9),
                         yscrollcommand=lb_scroll.set,
                         activestyle="none", borderwidth=0,
                         highlightthickness=1,
                         highlightbackground=self.COLOR_HIGHLIGHT)
    listbox.pack(side="left", fill="x", expand=True)
    lb_scroll.config(command=listbox.yview)
    file_paths = []
    btn_row = tk.Frame(file_frame, bg=self.COLOR_TOPLEVEL)
    btn_row.pack(fill="x", pady=5)
    def aggiungi_file():
        paths = filedialog.askopenfilenames(
            title="Seleziona documenti",
            filetypes=[("Documenti", "*.pdf *.png *.jpg *.jpeg *.webp"),
                       ("PDF", "*.pdf"), ("Immagini", "*.png *.jpg *.jpeg *.webp")],
            parent=popup)
        for p in paths:
            if p not in file_paths:
                file_paths.append(p)
                listbox.insert("end", os.path.basename(p))
    def rimuovi_file():
        sel = listbox.curselection()
        for i in reversed(sel):
            listbox.delete(i)
            file_paths.pop(i)
    for txt, ico_k, cmd in [
        (" Aggiungi", "carica", aggiungi_file),
        (" Rimuovi",  "chiudi", rimuovi_file),
    ]:
        img = self.icone_gui.get(ico_k)
        b = ttk.Label(btn_row, text=txt, image=img, compound="left",
                      cursor="hand2", background=self.COLOR_WIDGET_BG,
                      foreground=self.TEXT_COLOR, padding=(8, 3))
        b.pack(side="left", padx=(0, 8))
        b.bind("<Button-1>", lambda e, c=cmd: c())
    tk.Label(popup, text="Cosa vuoi sapere / confrontare?",
             bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
             font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=18, pady=(10, 2))
    comm_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    comm_frame.pack(fill="x", padx=18)
    comm_scroll = ttk.Scrollbar(comm_frame, orient="vertical")
    comm_scroll.pack(side="right", fill="y")
    commento = tk.Text(comm_frame, height=4,
                       bg=self.COLOR_WHITE, fg=self.COLOR_BLACK,
                       font=("Segoe UI", 10), wrap="word",
                       yscrollcommand=comm_scroll.set,
                       borderwidth=0, highlightthickness=1,
                       highlightbackground=self.COLOR_HIGHLIGHT,
                       padx=8, pady=6)
    commento.pack(side="left", fill="x", expand=True)
    comm_scroll.config(command=commento.yview)
    commento.insert("1.0",
        "Es: Confronta queste bollette e dimmi quale fornitore conviene di più, "
        "evidenzia anomalie e suggerisci come risparmiare.")
    run_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    run_frame.pack(fill="x", padx=18, pady=10)
    img_run = self.icone_gui.get("sync")
    btn_analizza = ttk.Label(run_frame, text=" Analizza con Gemini",
                             image=img_run, compound="left",
                             cursor="hand2", background=self.COLOR_WIDGET_BG,
                             foreground=self.COLOR_HIGHLIGHT,
                             font=("Segoe UI", 10, "bold"), padding=(12, 5))
    btn_analizza.pack(side="left")
    ttk.Separator(popup, orient="horizontal").pack(fill="x", padx=18, pady=(0, 6))
    bot_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    bot_frame.pack(side="bottom", fill="x", padx=18, pady=(0, 12))
    res_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    res_frame.pack(fill="both", expand=True, padx=18, pady=(0, 4))
    res_scroll = ttk.Scrollbar(res_frame, orient="vertical", style="Vertical.TScrollbar")
    res_scroll.pack(side="right", fill="y")
    text_area = tk.Text(res_frame, bg=self.COLOR_WHITE, fg=self.COLOR_BLACK,
                        font=("Consolas", 10), wrap="word",
                        yscrollcommand=res_scroll.set,
                        borderwidth=0, highlightthickness=1,
                        highlightbackground=self.COLOR_HIGHLIGHT,
                        padx=14, pady=12, state="disabled")
    text_area.pack(side="left", fill="both", expand=True)
    res_scroll.config(command=text_area.yview)
    def _get_testo():
        return text_area.get("1.0", "end").strip()
    def salva_txt_result():
        t = _get_testo()
        if not t:
            return
        f = filedialog.asksaveasfilename(
            initialdir=EXPORT_FILES, confirmoverwrite=False,
            defaultextension=".txt", filetypes=[("TXT", "*.txt")],
            initialfile="Analisi_Bollette.txt", parent=popup)
        if f:
            with open(f, "w", encoding="utf-8") as fh:
                fh.write(t)
            self.show_toast("TXT salvato.")
    def salva_pdf_result():
        t = _get_testo()
        if not t:
            return
        f = filedialog.asksaveasfilename(
            initialdir=EXPORT_FILES, confirmoverwrite=False,
            defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
            initialfile="Analisi_Bollette.pdf", parent=popup)
        if f:
            try:
                import fitz
                doc  = fitz.open()
                page = doc.new_page(width=595, height=842)
                page.insert_text((40, 40), t, fontname="cour", fontsize=10)
                doc.save(f); doc.close()
                self.show_toast("PDF salvato.")
            except Exception as e:
                self.show_custom_warning("Errore PDF", str(e))
    def stampa_result():
        t = _get_testo()
        if t:
            self._stampa_lista_diretta(t, self.show_custom_warning)
    for txt, ico_k, cmd, side in [
        (" TXT",    "salva",  salva_txt_result, "left"),
        (" PDF",    "salva",  salva_pdf_result, "left"),
        (" Stampa", "stampa", stampa_result,    "left"),
        (" Chiudi", "chiudi", popup.destroy,    "right"),
    ]:
        img = self.icone_gui.get(ico_k)
        b = ttk.Label(bot_frame, text=txt, image=img, compound="left",
                      cursor="hand2", background=self.COLOR_WIDGET_BG,
                      foreground=self.TEXT_COLOR, padding=(10, 4))
        b.pack(side=side, padx=4)
        b.bind("<Button-1>", lambda e, c=cmd: c())
    def avvia_analisi():
        if not file_paths:
            self.show_custom_warning("Nessun File", "Aggiungi almeno un documento da analizzare.")
            return
        testo_commento = commento.get("1.0", "end").strip()
        splash = tk.Toplevel(popup, bg=self.COLOR_WIDGET_BG)
        splash.overrideredirect(True)
        splash.attributes("-topmost", True)
        sw, sh = 320, 75
        sx = popup.winfo_rootx() + (popup.winfo_width()  // 2) - (sw // 2)
        sy = popup.winfo_rooty() + (popup.winfo_height() // 2) - (sh // 2)
        splash.geometry(f"{sw}x{sh}+{sx}+{sy}")
        frm_s = tk.Frame(splash, bg=self.COLOR_WIDGET_BG,
                         highlightbackground=self.COLOR_HIGHLIGHT, highlightthickness=1)
        frm_s.pack(expand=True, fill="both")
        inn = tk.Frame(frm_s, bg=self.COLOR_WIDGET_BG)
        inn.pack(expand=True)
        gemini_colors = ["#0055FF", "#AA00FF", "#FF0055", "#00C853"]
        cvs_sz = 28
        cvs2 = tk.Canvas(inn, width=cvs_sz, height=cvs_sz,
                         bg=self.COLOR_WIDGET_BG, highlightthickness=0)
        cvs2.pack(side="left", padx=(0, 8))
        n_doc = len(file_paths)
        tk.Label(inn, text=f"Gemini sta analizzando {n_doc} document{'o' if n_doc==1 else 'i'}...",
                 font=("Segoe UI", 9, "bold"),
                 bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HIGHLIGHT).pack(side="left")
        anim_st = {"angle": 0, "cs": 0}
        def _anim():
            if not splash.winfo_exists(): return
            cvs2.delete("all")
            anim_st["angle"] = (anim_st["angle"] + 15) % 360
            anim_st["cs"] += 1
            col = gemini_colors[(anim_st["cs"] // 5) % len(gemini_colors)]
            c = cvs_sz // 2; r = 8
            cvs2.create_oval(c-r, c-r, c+r, c+r, outline=self.COLOR_HIGHLIGHT, width=1)
            rad = math.radians(anim_st["angle"])
            cvs2.create_arc(c-r, c-r, c+r, c+r,
                            start=anim_st["angle"]-40, extent=40,
                            outline=col, width=3, style="arc")
            cvs2.create_oval(c+r*math.cos(rad)-3, c+r*math.sin(rad)-3,
                             c+r*math.cos(rad)+3, c+r*math.sin(rad)+3,
                             fill=col, outline=col)
            splash.after(20, _anim)
        _anim()
        splash.update()
        def _run():
            try:
                client = genai_client.Client(api_key=API_KEY)
                mime_map = {".pdf": "application/pdf",
                            ".png": "image/png", ".jpg": "image/jpeg",
                            ".jpeg": "image/jpeg", ".webp": "image/webp"}
                parts = []
                for fp in file_paths:
                    ext = os.path.splitext(fp)[1].lower()
                    mime = mime_map.get(ext)
                    if not mime:
                        continue
                    with open(fp, "rb") as fh:
                        data = fh.read()
                    parts.append(types.Part.from_bytes(data=data, mime_type=mime))
                    parts.append(f"[File: {os.path.basename(fp)}]")
                istruzione = (
                    "Sei un esperto analista finanziario domestico.\n"
                    "REGOLE DI RISPOSTA (OBBLIGATORIE, NON IGNORARE):\n"
                    "1. VIETATO usare qualsiasi simbolo Markdown: niente **, *, #, -, `, [].\n"
                    "   Per enfatizzare usa le MAIUSCOLE. Per gli elenchi usa numeri (1. 2. 3.).\n"
                    "2. I TITOLI DI SEZIONE vanno scritti in MAIUSCOLO.\n"
                    "   Il testo del corpo va scritto in minuscolo normale, come in una lettera.\n"
                    "   Esempio corretto:\n"
                    "   ANALISI DEI COSTI\n"
                    "   il costo medio dell'energia risulta inferiore rispetto al periodo precedente.\n"
                    "3. Sii preciso, concreto e orientato al risparmio.\n\n"
                    "Analizza i documenti forniti seguendo questi punti:\n"
                    "1. confronta importi, fornitori e consumi;\n"
                    "2. evidenzia anomalie o aumenti ingiustificati;\n"
                    "3. suggerisci azioni concrete per risparmiare.\n\n"
                )
                if testo_commento:
                    istruzione += f"RICHIESTA UTENTE:\n{testo_commento}\n\n"
                istruzione += "RICORDA: niente simboli Markdown, titoli in MAIUSCOLO, corpo in minuscolo normale.\n"
                parts.append(istruzione)
                response = client.models.generate_content(model=GEMINI, contents=parts)
                testo_ris = response.text if response.text else "Nessuna risposta generata."                
            except Exception as err:
                testo_ris = f"ERRORE API GEMINI:\n{str(err)}"

            def _mostra():
                if splash.winfo_exists():
                    splash.destroy()
                text_area.config(state="normal")
                text_area.delete("1.0", "end")
                text_area.insert("1.0", testo_ris)
                text_area.config(state="disabled")
                text_area.see("1.0")
            self.after(0, _mostra)
        threading.Thread(target=_run, daemon=True).start()
    btn_analizza.bind("<Button-1>", lambda e: avvia_analisi())
    popup.deiconify()
    popup.focus_set()
