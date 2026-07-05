#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog

def gestisci_documenti_personali(self):
    import __main__ as _app
    DOC_PERS_DIR = _app.DOC_PERS_DIR
    CAT_DEFAULT  = _app.CAT_DEFAULT
    DB_CONDIVISO = _app.DB_CONDIVISO
    EXPORT_FILES = _app.EXPORT_FILES
    API_KEY      = _app.API_KEY
    genai_client = _app.genai_client
    GEMINI       = _app.GEMINI
    types        = _app.types
    _HAS_DND     = _app._HAS_DND
    _DND_FILES   = _app._DND_FILES
    import json, os, shutil, threading, re
    from datetime import datetime
    PROFILI_FILE = os.path.join(DOC_PERS_DIR, "profili.json")
    os.makedirs(DOC_PERS_DIR, exist_ok=True)
    def profilo_dir(nome):      return os.path.join(DOC_PERS_DIR, nome)
    def profilo_reg(nome):      return os.path.join(profilo_dir(nome), "registry.json")
    def profilo_cat(nome):      return os.path.join(profilo_dir(nome), "categorie.json")
    def profilo_docs(nome):     return os.path.join(profilo_dir(nome), "documenti")
    def load_profili():
        if os.path.exists(PROFILI_FILE):
            try:
                with open(PROFILI_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []
    def save_profili(profili):
        with open(PROFILI_FILE, "w", encoding="utf-8") as f:
            json.dump(profili, f, indent=2, ensure_ascii=False)
    def init_profilo(nome):
        os.makedirs(profilo_docs(nome), exist_ok=True)
        if not os.path.exists(profilo_cat(nome)):
            with open(profilo_cat(nome), "w", encoding="utf-8") as f:
                json.dump(sorted(CAT_DEFAULT), f, indent=2, ensure_ascii=False)
        if not os.path.exists(profilo_reg(nome)):
            with open(profilo_reg(nome), "w", encoding="utf-8") as f:
                json.dump({}, f, indent=2, ensure_ascii=False)
    def load_registry(nome):
        p = profilo_reg(nome)
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    def save_registry(nome, reg):
        with open(profilo_reg(nome), "w", encoding="utf-8") as f:
            json.dump(reg, f, indent=4, ensure_ascii=False)
        if DB_CONDIVISO:
            self.notifica_modifica_web()
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 📡 Notifica di aggiornamento inviata .")
    def load_categorie(nome):
        p = profilo_cat(nome)
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return list(CAT_DEFAULT)
    def save_categorie(nome, cats):
        with open(profilo_cat(nome), "w", encoding="utf-8") as f:
            json.dump(sorted(cats), f, indent=2, ensure_ascii=False)
    if hasattr(self, '_win_doc_pers') and self._win_doc_pers.winfo_exists():
        self._win_doc_pers.lift()
        return
    win = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    self._win_doc_pers = win
    win.title("Documenti Personali")
    win.withdraw()
    win.minsize(1100, 620)
    def chiudi_win():
        if hasattr(self, '_popup_calendario') and self._popup_calendario.winfo_exists():
            self._popup_calendario.destroy()
        threading.Thread(target=self.backup_documenti_personali, daemon=False).start()
        win.destroy()
    win.protocol("WM_DELETE_WINDOW", chiudi_win)
    win.bind("<Escape>", lambda e: chiudi_win())
    barra_menu = tk.Menu(win, bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT,
                         activebackground=self.MENU_ACT_BG_COLOR,
                         activeforeground=self.MENU_ACT_FG_COLOR)
    win.config(menu=barra_menu)
    menu_arch = tk.Menu(barra_menu, tearoff=0,
                        bg=self.MENU_BG, fg=self.MENU_FG_LIGHT,
                        activebackground=self.MENU_ACT_BG_COLOR,
                        activeforeground=self.MENU_ACT_FG_COLOR)
    barra_menu.add_cascade(label="📂 Archivio", menu=menu_arch)
    nb = ttk.Notebook(win)
    nb.pack(fill="both", expand=True, padx=6, pady=6)
    def costruisci_tab(nome_profilo):
        init_profilo(nome_profilo)
        categorie = load_categorie(nome_profilo)
        frm = ttk.Frame(nb)
        nb.add(frm, text=f"  👤 {nome_profilo}  ")
        COLS     = ["data", "categoria", "descrizione", "note", "file"]
        COL_HDRS = {"data": "Data", "categoria": "Categoria",
                    "descrizione": "Descrizione", "note": "Note", "file": "File"}
        _sort = {}
        frm_top = ttk.Frame(frm, padding="8 8 8 4")
        frm_top.pack(fill="x")
        ttk.Label(frm_top, text="Data:").grid(row=0, column=0, sticky="e", padx=4, pady=3)
        data_var   = tk.StringVar(value=datetime.now().strftime("%d-%m-%Y"))
        entry_data = ttk.Entry(frm_top, textvariable=data_var, width=12)
        entry_data.grid(row=0, column=1, sticky="w", padx=4, pady=3)
        btn_cal = ttk.Label(frm_top, image=self.icone_gui.get("calendario"),
                            text="", background=self.COLOR_WIDGET_BG, cursor="hand2")
        btn_cal.image = self.icone_gui.get("calendario")
        btn_cal.grid(row=0, column=2, padx=2)
        btn_cal.bind("<Button-1>", lambda e: self.mostra_calendario_popup(entry_data, data_var))
        ttk.Label(frm_top, text="Categoria:").grid(row=0, column=3, sticky="e", padx=4, pady=3)
        combo_cat = ttk.Combobox(frm_top, values=sorted(categorie),
                                 style="Border.TCombobox", state="readonly", width=18)
        combo_cat.grid(row=0, column=4, sticky="w", padx=4, pady=3)
        if categorie:
            combo_cat.current(0)
        ttk.Label(frm_top, text="Descrizione:").grid(row=0, column=5, sticky="e", padx=4, pady=3)
        entry_desc = ttk.Entry(frm_top, width=28)
        entry_desc.grid(row=0, column=6, sticky="w", padx=4, pady=3)
        def val_desc(v): return len(v) <= 30
        def val_note(v): return len(v) <= 30
        vcmd_desc = frm_top.register(val_desc)
        vcmd_note = frm_top.register(val_note)
        entry_desc.config(validate="key", validatecommand=(vcmd_desc, "%P"))
        ttk.Label(frm_top, text="Note:").grid(row=1, column=0, sticky="e", padx=4, pady=3)
        entry_note = ttk.Entry(frm_top, width=70)
        entry_note.grid(row=1, column=1, columnspan=6, sticky="ew", padx=4, pady=3)
        entry_note.config(validate="key", validatecommand=(vcmd_note, "%P"))
        _drop_path_ref = [None]
        _dnd_txt2 = "Trascina un PDF sul tab, clicca Archivia PDF per salvare." if _HAS_DND else "Compila i campi, clicca Archivia PDF per selezionare e salvare il documento."
        sub_frame_hint_dp = ttk.Frame(frm_top)
        sub_frame_hint_dp.grid(row=2, column=0, columnspan=7, padx=(5, 0), pady=(0, 2), sticky="w")
        lbl_hint_dp = ttk.Label(sub_frame_hint_dp, text=_dnd_txt2, foreground="gray", font=("Arial", 8, "italic"))
        lbl_hint_dp.pack(side="left")
        frame_progress_dp = ttk.Frame(sub_frame_hint_dp)
        frame_progress_dp.pack(side="left", padx=(12, 0))
        lbl_progress_dp = ttk.Label(frame_progress_dp, text="", foreground="#61AFEF", font=("Arial", 8, "italic"))
        lbl_progress_dp.pack(side="left", padx=(0, 8))
        progress_dp = ttk.Progressbar(frame_progress_dp, mode="indeterminate", length=160, style="Horizontal.TProgressbar")
        progress_dp.pack(side="left")
        frame_progress_dp.pack_forget()
        def _mostra_progress_dp(testo="Analisi AI in corso…"):
            lbl_progress_dp.config(text=testo)
            frame_progress_dp.pack(side="left", padx=(12, 0))
            progress_dp.start(12)
        def _nascondi_progress_dp():
            progress_dp.stop()
            frame_progress_dp.pack_forget()
        frm_srch = ttk.Frame(frm, padding="8 0 8 4")
        frm_srch.pack(fill="x")
        ttk.Label(frm_srch, text="Cerca:").pack(side="left", padx=(0, 4))
        campo_cerca = ttk.Entry(frm_srch, width=32)
        campo_cerca.pack(side="left")
        lbl_count = ttk.Label(frm_srch, text="Documenti: 0",
                              foreground=self.COLOR_HIGHLIGHT)
        lbl_count.pack(side="left", padx=12)
        frm_tree = ttk.Frame(frm)
        frm_tree.pack(fill="both", expand=True, padx=8, pady=4)
        vsb  = ttk.Scrollbar(frm_tree, orient="vertical", style="Vertical.TScrollbar")
        tree = ttk.Treeview(frm_tree, columns=COLS, show="headings",
                            selectmode="extended", yscrollcommand=vsb.set)
        vsb.config(command=tree.yview)
        vsb.pack(side="right", fill="y")
        tree.pack(fill="both", expand=True)
        COL_W = {"data": 90, "categoria": 130, "descrizione": 280, "note": 260, "file": 0}
        COL_A = {"data": "center", "categoria": "center",
                 "descrizione": "center", "note": "center", "file": "w"}
        for c in COLS:
            tree.heading(c, text=COL_HDRS[c], command=lambda x=c: sort_col(x))
            tree.column(c, width=COL_W[c], anchor=COL_A[c], stretch=(c != "file"))
        tree.column("file", width=0, minwidth=0, stretch=tk.NO)
        def sort_col(col):
            rev = _sort.get(col, False)
            rows = [(tree.set(k, col), k) for k in tree.get_children("")]
            if col == "data":
                def _k(x):
                    try: return datetime.strptime(x[0], "%d-%m-%Y")
                    except: return datetime.min
                rows.sort(key=_k, reverse=rev)
            else:
                rows.sort(reverse=rev)
            for i, (_, k) in enumerate(rows):
                tree.move(k, "", i)
            _sort[col] = not rev
            for c in COLS:
                arr = (" ▲" if not rev else " ▼") if c == col else ""
                tree.heading(c, text=COL_HDRS[c] + arr, command=lambda x=c: sort_col(x))
        def load_tree(filtro=""):
            for r in tree.get_children():
                tree.delete(r)
            reg = load_registry(nome_profilo)
            fl  = filtro.lower().strip()
            for fname, d in sorted(reg.items(),
                                   key=lambda x: x[1].get("data_raw", ""), reverse=True):
                df   = d.get("data_fmt", "")
                cat  = d.get("categoria", "")
                desc = d.get("descrizione", "")
                note = d.get("note", "")
                if fl and fl not in f"{df} {cat} {desc} {note} {fname}".lower():
                    continue
                tree.insert("", "end", values=(df, cat, desc, note, fname))
            lbl_count.config(text=f"Documenti: {len(tree.get_children())}")
        campo_cerca.bind("<KeyRelease>", lambda e: load_tree(campo_cerca.get()))
        def modifica():
            sels = tree.selection()
            if not sels:
                    return self.show_toast("Seleziona un documento da modificare.")
            if len(sels) > 1:
                    return self.show_toast("Seleziona un solo documento alla volta.")
            vals  = tree.item(sels[0], "values")
            fname = vals[4]
            reg   = load_registry(nome_profilo)
            if fname not in reg:
                    return self.show_custom_warning("Errore", "Record non trovato nel registro.")
            rec = reg[fname]
            ewin = tk.Toplevel(win, bg=self.COLOR_TOPLEVEL)
            ewin.title(f"Modifica Documento")
            ewin.resizable(False, False)
            ewin.transient(win)
            ewin.withdraw()
            def chiudi_ewin():
                if hasattr(self, 'popup_calendario') and self.popup_calendario and self.popup_calendario.winfo_exists():
                    self.popup_calendario.destroy()
                    self.popup_calendario = None
                ewin.destroy()
            ewin.bind("<Escape>", lambda e: chiudi_ewin())
            pad = ttk.Frame(ewin, padding=14)
            pad.pack(fill="both", expand=True)
            ttk.Label(pad, text="Data:").grid(row=0, column=0, sticky="e", padx=6, pady=5)
            e_data_var = tk.StringVar(value=rec.get("data_fmt", ""))
            frm_data = ttk.Frame(pad)
            frm_data.grid(row=0, column=1, columnspan=2, sticky="w", padx=6, pady=5)
            e_data = ttk.Entry(frm_data, textvariable=e_data_var, width=14)
            e_data.pack(side="left")
            btn_cal2 = ttk.Label(frm_data, image=self.icone_gui.get("calendario"),
                                 text="", background=self.COLOR_WIDGET_BG, cursor="hand2")
            btn_cal2.image = self.icone_gui.get("calendario")
            btn_cal2.pack(side="left", padx=4)
            btn_cal2.bind("<Button-1>", lambda e: self.mostra_calendario_popup_semplice(e_data, e_data_var))
            ttk.Label(pad, text="Categoria:").grid(row=1, column=0, sticky="e", padx=6, pady=5)
            e_cat = ttk.Combobox(pad, values=sorted(categorie),
                                 style="Border.TCombobox", state="readonly", width=20)
            e_cat.grid(row=1, column=1, columnspan=2, sticky="w", padx=6, pady=5)
            if rec.get("categoria", "") in categorie:
                    e_cat.set(rec["categoria"])
            elif categorie:
                    e_cat.current(0)
            ttk.Label(pad, text="Descrizione:").grid(row=2, column=0, sticky="e", padx=6, pady=5)
            def val_d(v): return len(v) <= 30
            def val_n(v): return len(v) <= 30
            vcmd_d = ewin.register(val_d)
            vcmd_n = ewin.register(val_n)
            e_desc_var = tk.StringVar(value=rec.get("descrizione", ""))
            e_desc     = ttk.Entry(pad, textvariable=e_desc_var, width=32,
                                   validate="key", validatecommand=(vcmd_d, "%P"))
            e_desc.grid(row=2, column=1, columnspan=2, sticky="w", padx=6, pady=5)
            ttk.Label(pad, text="Note:").grid(row=3, column=0, sticky="e", padx=6, pady=5)
            e_note_var = tk.StringVar(value=rec.get("note", ""))
            e_note     = ttk.Entry(pad, textvariable=e_note_var, width=32,
                                   validate="key", validatecommand=(vcmd_n, "%P"))
            e_note.grid(row=3, column=1, columnspan=2, sticky="w", padx=6, pady=5)
            def salva_modifica():
                    data_s = e_data_var.get().strip()
                    cat    = e_cat.get().strip()
                    desc   = e_desc_var.get().strip()
                    note   = e_note_var.get().strip()
                    if not cat:  return self.show_toast("Seleziona una categoria.")
                    if not desc: return self.show_toast("Inserisci una descrizione.")
                    try:
                            data_obj = datetime.strptime(data_s, "%d-%m-%Y")
                            data_raw = data_obj.strftime("%d%m%Y")
                    except Exception:
                            return self.show_custom_warning("Data non valida", "Formato richiesto: GG-MM-AAAA")
                    reg[fname]["data_raw"]    = data_raw
                    reg[fname]["data_fmt"]    = data_obj.strftime("%d-%m-%Y")
                    reg[fname]["categoria"]   = cat
                    reg[fname]["descrizione"] = desc
                    reg[fname]["note"]        = note
                    save_registry(nome_profilo, reg)
                    load_tree(campo_cerca.get())
                    ewin.destroy()
                    self.show_toast("Documento aggiornato.")
            frm_eb = ttk.Frame(pad)
            frm_eb.grid(row=4, column=0, columnspan=3, pady=10)
            btn_ok2 = ttk.Label(frm_eb, text=" Salva", compound="left",
                                image=self.icone_gui.get("check"),
                                background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                                cursor="hand2", font=("Arial", 9, "bold"))
            btn_ok2.image = self.icone_gui.get("check")
            btn_ok2.pack(side="left", padx=10)
            btn_ok2.bind("<Button-1>", lambda e: salva_modifica())
            e_desc.bind("<Return>", lambda e: salva_modifica())
            btn_ch2 = ttk.Label(frm_eb, text=" Annulla", compound="left",
                                image=self.icone_gui.get("chiudi"),
                                background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                                cursor="hand2", font=("Arial", 9, "bold"))
            btn_ch2.image = self.icone_gui.get("chiudi")
            btn_ch2.pack(side="left", padx=10)
            btn_ch2.bind("<Button-1>", lambda e: chiudi_ewin())
            ewin.update_idletasks()
            w  = 420
            h  = 220
            sw = ewin.winfo_screenwidth()
            sh = ewin.winfo_screenheight()
            ewin.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
            ewin.minsize(w, h)
            ewin.deiconify()
            e_desc.focus_set()
            ewin.protocol("WM_DELETE_WINDOW", chiudi_ewin)
            
        def stampa_documento(fpath, fname):
            import platform
            cur_os = platform.system()
            try:
                if cur_os == "Windows":   os.startfile(fpath, 'print')
                elif cur_os in ["Linux", "Darwin"]: subprocess.Popen(['lp', fpath])
                else: return self.show_custom_warning("OS non supportato", f"Stampa non disponibile su {cur_os}.")
                self.show_custom_info("Stampa avviata", f"Comando inviato per:\n{fname}")
            except Exception as e:
                self.show_custom_warning("Errore stampa", f"Impossibile stampare '{fname}':\n{e}")
        def apri_pdf(event=None):
            sel = tree.selection()
            if not sel: return
            fname = tree.item(sel[0], "values")[4]
            fpath = os.path.join(profilo_docs(nome_profilo), fname)
            if not os.path.exists(fpath):
                return self.show_custom_warning("Errore", f"File non trovato:\n{fname}")
            try:
                import fitz
                from PIL import Image, ImageTk
                pwin = tk.Toplevel(win)
                pwin.title(fname)
                pwin.withdraw()
                pwin.configure(bg=self.COLOR_WIDGET_BG)
                pwin.bind("<Escape>", lambda e: pwin.destroy())
                cv  = tk.Canvas(pwin, bg=self.COLOR_WIDGET_BG, highlightthickness=0)
                vsb2 = ttk.Scrollbar(pwin, orient="vertical",   command=cv.yview, style="Vertical.TScrollbar")
                hsb  = ttk.Scrollbar(pwin, orient="horizontal", command=cv.xview, style="Horizontal.TScrollbar")
                cv.configure(yscrollcommand=vsb2.set, xscrollcommand=hsb.set)
                vsb2.pack(side="right", fill="y")
                hsb.pack(side="bottom", fill="x")
                cv.pack(fill="both", expand=True)
                fitz.TOOLS.mupdf_display_errors(False)
                doc = fitz.open(fpath)
                pwin._imgs = []
                y_off = 20; max_w = 0; zoom = 1.4
                mat = fitz.Matrix(zoom, zoom)
                for pn in range(len(doc)):
                    page = doc.load_page(pn)
                    pix  = page.get_pixmap(matrix=mat, annots=False)
                    img  = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    ph   = ImageTk.PhotoImage(img)
                    pwin._imgs.append(ph)
                    px = max(20, (900 - pix.width) // 2)
                    cv.create_image(px, y_off, anchor="nw", image=ph)
                    y_off += pix.height + 20
                    if pix.width > max_w: max_w = pix.width
                doc.close()
                cv.config(scrollregion=(0, 0, max(900, max_w + 40), y_off + 40))
                def _mw(e):
                    if cv.winfo_exists():
                        if e.num == 4 or e.delta > 0: cv.yview_scroll(-1, "units")
                        elif e.num == 5 or e.delta < 0: cv.yview_scroll(1, "units")
                cv.bind_all("<MouseWheel>", _mw)
                cv.bind_all("<Button-4>",   _mw)
                cv.bind_all("<Button-5>",   _mw)
                frm_cb = tk.Frame(pwin, bg=self.COLOR_WIDGET_BG)
                frm_cb.pack(side="bottom", fill="x", padx=10, pady=6)
                bs = ttk.Label(frm_cb, text=" Stampa", compound="left",
                    image=self.icone_gui.get("stampa"),
                    background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2")
                bs.image = self.icone_gui.get("stampa")
                bs.pack(side="left", padx=8)
                bs.bind("<Button-1>", lambda e: stampa_documento(fpath, fname))
                bsalva = ttk.Label(frm_cb, text=" Salva copia", compound="left",
                    image=self.icone_gui.get("salva"),
                    background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2")
                bsalva.image = self.icone_gui.get("salva")
                bsalva.pack(side="left", padx=8)
                def _salva_copia(fp=fpath, fn=fname):
                    dst = filedialog.asksaveasfilename(parent=pwin, defaultextension=".pdf",
                        filetypes=[("PDF", "*.pdf")], initialfile=fn)
                    if dst:
                        shutil.copy2(fp, dst)
                        self.show_custom_info("Salvato", f"Copia salvata in:\n{dst}")
                bsalva.bind("<Button-1>", lambda e: _salva_copia())
                bc = ttk.Label(frm_cb, text=" Chiudi", compound="left",
                    image=self.icone_gui.get("chiudi"),
                    background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2")
                bc.image = self.icone_gui.get("chiudi")
                bc.pack(side="right", padx=8)
                bc.bind("<Button-1>", lambda e: pwin.destroy())
                pwin.update_idletasks()
                sw = pwin.winfo_screenwidth(); sh = pwin.winfo_screenheight()
                w = 950; h = 630
                pwin.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
                pwin.minsize(w, h)
                pwin.deiconify()
            except Exception as ex:
                self.show_custom_warning("Errore", f"Impossibile aprire il PDF:\n{ex}")
        def archivia():
            data_s = entry_data.get().strip()
            cat    = combo_cat.get().strip()
            desc   = entry_desc.get().strip()
            note   = entry_note.get().strip()
            if not cat:  return self.show_toast("Seleziona una categoria.")
            if not desc: return self.show_toast("Inserisci una descrizione.")
            try:
                data_obj = datetime.strptime(data_s, "%d-%m-%Y")
                data_raw = data_obj.strftime("%d%m%Y")
            except Exception:
                return self.show_custom_warning("Data non valida", "Formato richiesto: GG-MM-AAAA")
            path = _drop_path_ref[0] or filedialog.askopenfilename(parent=win, filetypes=[("PDF", "*.pdf")])
            if not path: return
            def san(s):
                return re.sub(r'[^\w\.-]', '', s.strip().replace(' ', '_'))[:30].upper()
            fname = f"{data_raw}_{san(desc)}_{san(cat)}.pdf"
            dst   = os.path.join(profilo_docs(nome_profilo), fname)
            try:
                shutil.copy2(path, dst)
            except Exception as e:
                return self.show_custom_warning("Errore copia", f"Impossibile copiare il file:\n{e}")
            reg = load_registry(nome_profilo)
            reg[fname] = {
                "data_raw":    data_raw,
                "data_fmt":    data_obj.strftime("%d-%m-%Y"),
                "categoria":   cat,
                "descrizione": desc,
                "note":        note,
                "timestamp":   datetime.now().isoformat()
            }
            save_registry(nome_profilo, reg)
            load_tree(campo_cerca.get())
            _drop_path_ref[0] = None
            entry_desc.delete(0, tk.END)
            entry_note.delete(0, tk.END)
            data_var.set(datetime.now().strftime("%d-%m-%Y"))
            if categorie:
                combo_cat.set(categorie[0])
            self.show_toast("Documento archiviato correttamente.")
        def cancella():
            sels = tree.selection()
            if not sels:
                return self.show_toast("Seleziona almeno un documento.")
            if not self.show_custom_askyesno("Conferma eliminazione",
                    f"Eliminare {len(sels)} documento/i?\nL'operazione non è reversibile."):
                return
            reg = load_registry(nome_profilo)
            for s in sels:
                fname = tree.item(s, "values")[4]
                fpath = os.path.join(profilo_docs(nome_profilo), fname)
                if os.path.exists(fpath): os.remove(fpath)
                reg.pop(fname, None)
                tree.delete(s)
            save_registry(nome_profilo, reg)
            lbl_count.config(text=f"Documenti: {len(tree.get_children())}")
        def esporta():
            sels = tree.selection()
            if not sels:
                return self.show_toast("Seleziona almeno un documento.")
            dst = filedialog.askdirectory(parent=win, title="Cartella di destinazione")
            if not dst: return
            ok = 0
            for s in sels:
                fname = tree.item(s, "values")[4]
                src   = os.path.join(profilo_docs(nome_profilo), fname)
                if os.path.exists(src):
                    shutil.copy2(src, os.path.join(dst, fname))
                    ok += 1
            if ok: self.show_custom_info("Esportazione completata", f"Esportati {ok} file in:\n{dst}")
            else:  self.show_custom_warning("Esportazione", "Nessun file trovato da esportare.")
        def stampa_selezionati():
            sels = tree.selection()
            if not sels:
                return self.show_toast("Seleziona almeno un documento.")
            import platform
            stampati = 0; errori = 0
            cur_os = platform.system()
            for item_id in sels:
                fname = tree.item(item_id, "values")[4]
                if not fname or fname == "N/D": errori += 1; continue
                fpath = os.path.join(profilo_docs(nome_profilo), fname)
                if not os.path.exists(fpath):
                    self.show_custom_warning("File mancante", f"File non trovato:\n{fname}")
                    errori += 1; continue
                try:
                    if cur_os == "Windows":   os.startfile(fpath, "print")
                    elif cur_os in ("Linux", "Darwin"): subprocess.Popen(["lp", fpath])
                    else: self.show_custom_warning("OS non supportato", f"Non supportato su {cur_os}."); errori += 1; continue
                    stampati += 1
                except Exception as e:
                    self.show_custom_warning("Errore stampa", f"Impossibile stampare '{fname}':\n{e}")
                    errori += 1
            if stampati > 0:
                msg = f"Comando inviato per {stampati} documento/i."
                if errori: msg += f"\n{errori} non elaborati."
                self.show_custom_info("Stampa avviata", msg)
            elif errori:
                self.show_custom_warning("Stampa fallita", f"Nessun documento stampato. {errori} errori.")
        def gestisci_categorie():
            nonlocal categorie
            cwin = tk.Toplevel(win, bg=self.COLOR_TOPLEVEL)
            cwin.title(f"Categorie — {nome_profilo}")
            cwin.transient(win)
            cwin.resizable(False, False)
            cwin.bind("<Escape>", lambda e: cwin.destroy())
            cwin.withdraw()
            pad = ttk.Frame(cwin, padding=12)
            pad.pack(fill="both", expand=True)
            lf_add = ttk.LabelFrame(pad, text="  ➕  Nuova categoria  ")
            lf_add.pack(fill="x", pady=(0, 8))
            ttk.Label(lf_add, text="Nome:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
            nuova_var = tk.StringVar()
            def convalida(v): return len(v) <= 25
            vcmd = cwin.register(convalida)
            en_add = ttk.Entry(lf_add, textvariable=nuova_var, width=26,
                               validate="key", validatecommand=(vcmd, "%P"))
            en_add.grid(row=0, column=1, padx=6, pady=6, sticky="w")
            lf_mod = ttk.LabelFrame(pad, text="  ✏️  Modifica / Cancella  ")
            lf_mod.pack(fill="x", pady=(0, 8))
            sel_var = tk.StringVar(); mod_var = tk.StringVar()
            ttk.Label(lf_mod, text="Seleziona:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
            cb = ttk.Combobox(lf_mod, textvariable=sel_var, values=sorted(categorie),
                              style="Border.TCombobox", state="readonly", width=26)
            cb.grid(row=0, column=1, columnspan=2, padx=6, pady=6, sticky="w")
            ttk.Label(lf_mod, text="Nuovo nome:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
            en_mod = ttk.Entry(lf_mod, textvariable=mod_var, width=26,
                               validate="key", validatecommand=(vcmd, "%P"))
            en_mod.grid(row=1, column=1, padx=6, pady=6, sticky="w")
            cb.bind("<<ComboboxSelected>>", lambda e: (mod_var.set(sel_var.get()), cb.selection_clear(), en_mod.focus_set()))
            def agg_cb():
                vals = sorted(categorie, key=lambda x: x.lower())
                cb["values"]        = vals
                combo_cat["values"] = vals
            def add_c():
                n = nuova_var.get().strip()
                if not n: return self.show_toast("Seleziona almeno un documento.")
                if n in categorie: return self.show_custom_warning("Già esistente", f"'{n}' esiste già.")
                categorie.append(n)
                categorie.sort(key=lambda x: x.lower())
                save_categorie(nome_profilo, categorie)
                agg_cb()
                combo_cat.set(n)
                nuova_var.set(""); en_add.focus_set()
                self.show_custom_info("Creata", f"Categoria '{n}' creata.")
            def mod_c():
                v = sel_var.get(); n = mod_var.get().strip()
                if not v: return self.show_custom_warning("Nessuna selezione", "Seleziona una categoria.")
                if not n: return self.show_custom_warning("Campo vuoto", "Inserisci il nuovo nome.")
                if n == v: return
                if n in categorie: return self.show_custom_warning("Già esistente", f"'{n}' esiste già.")
                categorie[categorie.index(v)] = n
                categorie.sort(key=lambda x: x.lower())
                save_categorie(nome_profilo, categorie)
                agg_cb()
                combo_cat.set(n)
                sel_var.set(""); mod_var.set("")
                self.show_custom_info("Modificata", f"'{v}' → '{n}'")
            def del_c():
                v = sel_var.get()
                if not v: return self.show_custom_warning("Nessuna selezione", "Seleziona una categoria.")
                if not self.show_custom_askyesno("Conferma", f"Cancellare '{v}'?"): return
                categorie.remove(v)
                save_categorie(nome_profilo, categorie)
                agg_cb()
                if categorie: combo_cat.set(categorie[0])
                sel_var.set(""); mod_var.set("")
                self.show_custom_info("Cancellata", f"Categoria '{v}' cancellata.")
            btn_add = ttk.Label(lf_add, text=" Aggiungi", compound="left",
                                image=self.icone_gui.get("check"),
                                background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                                cursor="hand2", font=("Arial", 9, "bold"))
            btn_add.image = self.icone_gui.get("check")
            btn_add.grid(row=0, column=2, padx=8, pady=6)
            btn_add.bind("<Button-1>", lambda e: add_c())
            en_add.bind("<Return>", lambda e: add_c())
            en_mod.bind("<Return>", lambda e: mod_c())
            bf_mod = ttk.Frame(lf_mod)
            bf_mod.grid(row=2, column=0, columnspan=3, sticky="ew", padx=6, pady=(2, 8))
            bf_mod.columnconfigure(1, weight=1)
            btn_mod = ttk.Label(bf_mod, text=" Rinomina", compound="left",
                                image=self.icone_gui.get("descrizione"),
                                background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                                cursor="hand2", font=("Arial", 9, "bold"))
            btn_mod.image = self.icone_gui.get("descrizione")
            btn_mod.grid(row=0, column=0, sticky="w")
            btn_mod.bind("<Button-1>", lambda e: mod_c())
            btn_del = ttk.Label(bf_mod, text=" Cancella", compound="left",
                                image=self.icone_gui.get("delete"),
                                background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                                cursor="hand2", font=("Arial", 9, "bold"))
            btn_del.image = self.icone_gui.get("delete")
            btn_del.grid(row=0, column=2, sticky="e")
            btn_del.bind("<Button-1>", lambda e: del_c())
            btn_ch = ttk.Label(pad, text=" Chiudi", compound="left",
                               image=self.icone_gui.get("chiudi"),
                               background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                               cursor="hand2", font=("Arial", 9, "bold"))
            btn_ch.image = self.icone_gui.get("chiudi")
            btn_ch.pack(anchor="center", pady=4)
            btn_ch.bind("<Button-1>", lambda e: cwin.destroy())
            cwin.update_idletasks()
            sw = cwin.winfo_screenwidth(); sh = cwin.winfo_screenheight()
            w  = cwin.winfo_reqwidth();   h  = cwin.winfo_reqheight()
            cwin.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
            cwin.deiconify()
            en_add.focus_set()
            cwin.wait_window()
        def esegui_backup_manuale():
            try:
                import tempfile
                ts       = datetime.now().strftime("%d%m%Y_%H%M")
                nome_def = f"{nome_profilo}_Documenti_Personali_{ts}"
                dst = filedialog.asksaveasfilename(
                    parent=win,
                    title="Salva backup ZIP",
                    initialdir=EXPORT_FILES,
                    initialfile=nome_def,
                    confirmoverwrite=False,
                    defaultextension=".zip",
                    filetypes=[("ZIP", "*.zip")])
                if not dst: return
                tmp = tempfile.mkdtemp()
                shutil.copytree(profilo_docs(nome_profilo),
                                os.path.join(tmp, "documenti"), dirs_exist_ok=True)
                shutil.copy2(profilo_reg(nome_profilo), tmp)
                arc = os.path.splitext(dst)[0]
                shutil.make_archive(arc, "zip", tmp, "")
                shutil.rmtree(tmp, ignore_errors=True)
                self.show_custom_info("Backup completato", f"File salvato in:\n{arc}.zip")
            except Exception as e:
                self.show_custom_warning("Errore backup", f"Impossibile creare il backup:\n{e}")
        def esegui_importa():
            path = filedialog.askopenfilename(parent=win, title="Seleziona archivio ZIP",
                                              filetypes=[("ZIP", "*.zip")])
            if not path: return
            if not self.show_custom_askyesno("Conferma importazione",
                    "I documenti verranno uniti con quelli esistenti.\nContinuare?"): return
            try:
                import zipfile, tempfile
                tmp = tempfile.mkdtemp()
                with zipfile.ZipFile(path, "r") as z:
                    z.extractall(tmp)
                src_pdf = os.path.join(tmp, "documenti")
                if os.path.isdir(src_pdf):
                    for f in os.listdir(src_pdf):
                        shutil.copy2(os.path.join(src_pdf, f),
                                     os.path.join(profilo_docs(nome_profilo), f))
                src_reg = os.path.join(tmp, "registry.json")
                if os.path.exists(src_reg):
                    with open(src_reg, "r", encoding="utf-8") as f:
                        imp = json.load(f)
                    reg = load_registry(nome_profilo)
                    reg.update(imp)
                    save_registry(nome_profilo, reg)
                    if DB_CONDIVISO:
                        self.notifica_modifica_web()
                        print(f"📡 [{datetime.datetime.now().strftime('%H:%M:%S')}] Notifica di aggiornamento inviata .")
                shutil.rmtree(tmp, ignore_errors=True)
                load_tree(campo_cerca.get())
                self.show_custom_info("Importazione completata",
                                      f"Importati documenti da:\n{os.path.basename(path)}")
            except Exception as e:
                self.show_custom_warning("Errore importazione", f"Impossibile importare:\n{e}")
        if _HAS_DND:
            def on_drop_dp(event):
                raw = event.data.strip()
                if raw.startswith("{") and raw.endswith("}"):
                    raw = raw[1:-1]
                paths = [p.strip() for p in raw.split("} {") if p.strip()]
                pdf_path = paths[0] if paths else raw
                if not pdf_path.lower().endswith(".pdf"):
                    self.show_toast("Trascina solo file PDF.")
                    return
                _drop_path_ref[0] = pdf_path
                if not API_KEY:
                    self.show_toast(f"📎 {os.path.basename(pdf_path)} — imposta API Key Gemini per l'analisi automatica")
                    return
                self.show_toast(f"Analisi AI: {os.path.basename(pdf_path)}…")
                _mostra_progress_dp()
                def _analizza_dp():
                    try:
                        import json as _json
                        with open(pdf_path, "rb") as _pf:
                            pdf_bytes = _pf.read()
                        client_dp = genai_client.Client(api_key=API_KEY)
                        lista_cat_dp = ", ".join(f'"{c}"' for c in categorie)
                        prompt_dp = (
                            f"Analizza questo documento PDF (fattura, ricevuta, certificato o simile).\n"
                            f"Estrai i seguenti campi e restituisci SOLO un JSON (senza backtick):\n"
                            f'{{\\"descrizione\\": \\"titolo breve del documento (max 30 car.)\\", '
                            f'\\"categoria\\": \\"la più adatta tra [{lista_cat_dp}]\\"}}\n'
                            f"REGOLE: descrizione concisa senza emoji; SOLO JSON."
                        )
                        r_dp = client_dp.models.generate_content(
                            model=GEMINI,
                            contents=[
                                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                                prompt_dp
                            ]
                        )
                        raw_json = r_dp.text.strip().replace("```json", "").replace("```", "").strip()
                        dati_dp = _json.loads(raw_json)
                        desc_ia  = str(dati_dp.get("descrizione") or "").strip()[:30]
                        cat_ia   = dati_dp.get("categoria", "")
                        cat_ok   = cat_ia if cat_ia in categorie else ""
                        def _aggiorna_gui_dp():
                            _nascondi_progress_dp()
                            if desc_ia:
                                entry_desc.delete(0, tk.END)
                                entry_desc.insert(0, desc_ia)
                            if cat_ok:
                                combo_cat.set(cat_ok)
                            self.show_toast(f"📎 {os.path.basename(pdf_path)} — campi compilati, verifica e archivia")
                        frm.after(0, _aggiorna_gui_dp)
                    except Exception as e_dp:
                        err_dp = str(e_dp)
                        if "429" in err_dp or "RESOURCE_EXHAUSTED" in err_dp:
                            msg_dp = "Quota API Gemini esaurita. Riprova domani."
                        elif "503" in err_dp or "UNAVAILABLE" in err_dp:
                            msg_dp = "Gemini non disponibile. Riprova tra poco."
                        else:
                            msg_dp = f"Analisi AI fallita: {err_dp[:80]}"
                        def _on_errore_dp(m=msg_dp):
                            _nascondi_progress_dp()
                            self.show_toast(m)
                        frm.after(0, _on_errore_dp)
                threading.Thread(target=_analizza_dp, daemon=True).start()
            try:
                frm.drop_target_register(_DND_FILES)
                frm.dnd_bind("<<Drop>>", on_drop_dp)
            except Exception:
                pass
        frm_btn = ttk.Frame(frm, padding="8 4 8 10")
        frm_btn.pack(fill="x")
        for lbl, cmd, ik in [
            (" Archivia PDF", archivia,             "archivia"),
            (" Modifica",     modifica,              "descrizione"),
            (" Cancella",     cancella,              "cancella"),
            (" Salva",        esporta,               "salva"),
            (" Stampa",       stampa_selezionati,    "stampa"),
            (" Categorie",    gestisci_categorie,    "filtri"),
            (" Esporta Zip",  esegui_backup_manuale, "backup" if "backup" in self.icone_gui else "salva"),
            (" Importa Zip",  esegui_importa,        "import" if "import" in self.icone_gui else "archivia"),
            (" Help",         self.mostra_help_documenti_personali, "help" if "help" in self.icone_gui else "info"),
        ]:
            lb = ttk.Label(frm_btn, text=lbl, compound="left",
                           image=self.icone_gui.get(ik),
                           background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                           cursor="hand2", font=("Arial", 9, "bold"))
            lb.image = self.icone_gui.get(ik)
            lb.pack(side="left", padx=6)
            lb.bind("<Button-1>", lambda e, f=cmd: f())
        btn_ch = ttk.Label(frm_btn, text=" Chiudi", compound="left",
                           image=self.icone_gui.get("chiudi"),
                           background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                           cursor="hand2", font=("Arial", 9, "bold"))
        btn_ch.image = self.icone_gui.get("chiudi")
        btn_ch.pack(side="right", padx=8)
        btn_ch.bind("<Button-1>", lambda e: chiudi_win())

        tree.bind("<Double-1>", apri_pdf)
        tree.bind("<Delete>",   lambda e: cancella())
        load_tree()
        return load_tree, esegui_backup_manuale
    def costruisci_tab_profili():
        frm_p = ttk.Frame(nb)
        nb.add(frm_p, text="  ⚙️ Profili  ")
        lf = ttk.LabelFrame(frm_p, text="  👤  Aggiungi profilo  ", padding=10)
        lf.pack(fill="x", padx=16, pady=16)
        ttk.Label(lf, text="Nome:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        nome_var = tk.StringVar()
        def convalida_nome(v): return len(v) <= 20
        vcmd_p = frm_p.register(convalida_nome)
        en_nome = ttk.Entry(lf, textvariable=nome_var, width=22,
                            validate="key", validatecommand=(vcmd_p, "%P"))
        en_nome.grid(row=0, column=1, padx=6, pady=6)
        def aggiungi_profilo():
            n = nome_var.get().strip()
            if not n:
                return self.show_toast("Inserisci un Nome.")
            profili = load_profili()
            if n in profili:
                return self.show_custom_warning("Già esistente", f"Il profilo '{n}' esiste già.")
            if len(profili) >= 5:
                return self.show_custom_warning("Limite raggiunto", "Puoi creare al massimo 5 profili.")
            profili.append(n)
            profili.sort()
            save_profili(profili)
            init_profilo(n)
            lt = costruisci_tab(n)
            if lt:
                load_tree_refs[n] = lt[0]
                backup_refs[n]    = lt[1]
            tab_ids = list(nb.tabs())
            profilo_tabs = [(nb.tab(t, "text").strip(), t) for t in tab_ids
                            if nb.tab(t, "text").strip() != "⚙️ Profili"]
            profilo_tabs.sort(key=lambda x: x[0])
            for pos, (_, tid) in enumerate(profilo_tabs):
                nb.insert(pos, tid)
            nb.insert("end", frm_p)
            cb_del["values"] = load_profili()
            nome_var.set("")
            self.show_custom_info("Profilo creato", f"Profilo '{n}' aggiunto.")
        btn_add = ttk.Label(lf, text=" Aggiungi", compound="left",
                            image=self.icone_gui.get("check"),
                            background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                            cursor="hand2", font=("Arial", 9, "bold"))
        btn_add.image = self.icone_gui.get("check")
        btn_add.grid(row=0, column=2, padx=8)
        btn_add.bind("<Button-1>", lambda e: aggiungi_profilo())
        en_nome.bind("<Return>", lambda e: aggiungi_profilo())
        lf2 = ttk.LabelFrame(frm_p, text="  🗑️  Elimina profilo  ", padding=10)
        lf2.pack(fill="x", padx=16, pady=(0, 16))
        ttk.Label(lf2, text="Profilo:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        del_var = tk.StringVar()
        cb_del = ttk.Combobox(lf2, textvariable=del_var,
                               values=load_profili(),
                               style="Border.TCombobox", state="readonly", width=22)
        cb_del.grid(row=0, column=1, padx=6, pady=6)
        def elimina_profilo():
            n = del_var.get().strip()
            if not n: return self.show_toast("Seleziona un profilo.")
            if not self.show_custom_askyesno("Conferma eliminazione",
                    f"Eliminare il profilo '{n}' e tutti i suoi documenti?\nL'operazione non è reversibile."):
                return
            profili = load_profili()
            if n in profili: profili.remove(n)
            save_profili(profili)
            import shutil as _sh
            pd = profilo_dir(n)
            if os.path.exists(pd): _sh.rmtree(pd, ignore_errors=True)
            for i in range(nb.index("end")):
                try:
                    if nb.tab(i, "text").strip() == f"👤 {n}":
                        nb.forget(i)
                        break
                except Exception:
                    pass
            load_tree_refs.pop(n, None)
            cb_del["values"] = load_profili()
            del_var.set("")
            self.show_custom_info("Eliminato", f"Profilo '{n}' eliminato.")
        btn_del = ttk.Label(lf2, text=" Elimina", compound="left",
                            image=self.icone_gui.get("delete"),
                            background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                            cursor="hand2", font=("Arial", 9, "bold"))
        btn_del.image = self.icone_gui.get("delete")
        btn_del.grid(row=0, column=2, padx=8)
        btn_del.bind("<Button-1>", lambda e: elimina_profilo())
        frm_btn_p = ttk.Frame(frm_p, padding="8 4 8 10")
        frm_btn_p.pack(fill="x", side="bottom")
        btn_help = ttk.Label(frm_btn_p, text=" Help", compound="left",
                             image=self.icone_gui.get("help"),
                             background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                             cursor="hand2", font=("Arial", 9, "bold"))
        btn_help.image = self.icone_gui.get("help")
        btn_help.pack(side="left", padx=8)
        btn_help.bind("<Button-1>", lambda e: self.mostra_help_documenti_personali())
        btn_ch = ttk.Label(frm_btn_p, text=" Chiudi", compound="left",
                           image=self.icone_gui.get("chiudi"),
                           background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                           cursor="hand2", font=("Arial", 9, "bold"))
        btn_ch.image = self.icone_gui.get("chiudi")
        btn_ch.pack(side="right", padx=8)
        btn_ch.bind("<Button-1>", lambda e: chiudi_win())
    def esporta_zip_completo():
        try:
            import tempfile
            ts       = datetime.now().strftime("%d%m%Y_%H%M")
            nome_def = f"Archivio_Documenti_Personali_{ts}"
            dst = filedialog.asksaveasfilename(
                parent=win,
                title="Salva archivio ZIP",
                initialdir=EXPORT_FILES,
                initialfile=nome_def,
                confirmoverwrite=False,
                defaultextension=".zip",
                filetypes=[("ZIP", "*.zip")])
            if not dst: return
            tmp = tempfile.mkdtemp()
            shutil.copytree(DOC_PERS_DIR, os.path.join(tmp, "documenti_personali"), dirs_exist_ok=True)
            arc = os.path.splitext(dst)[0]
            shutil.make_archive(arc, "zip", tmp, "")
            shutil.rmtree(tmp, ignore_errors=True)
            self.show_custom_info("Esportazione completata", f"Archivio ZIP salvato in:\n{arc}.zip")
        except Exception as e:
            self.show_custom_warning("Errore esportazione", f"Impossibile creare lo ZIP:\n{e}")
    def importa_zip_completo():
        path = filedialog.askopenfilename(parent=win, title="Seleziona archivio ZIP completo",
                                          filetypes=[("ZIP", "*.zip")], initialdir=EXPORT_FILES)
        if not path: return
        if not self.show_custom_askyesno("Conferma importazione",
                "I profili e documenti verranno uniti con quelli esistenti.\nContinuare?"): return
        try:
            import zipfile, tempfile
            tmp = tempfile.mkdtemp()
            with zipfile.ZipFile(path, "r") as z:
                z.extractall(tmp)
            src_root = os.path.join(tmp, "documenti_personali")
            if not os.path.isdir(src_root):
                src_root = tmp
            src_profili = os.path.join(src_root, "profili.json")
            nuovi_profili = []
            if os.path.exists(src_profili):
                with open(src_profili, "r", encoding="utf-8") as f:
                    nuovi_profili = json.load(f)
            profili_attuali = load_profili()
            aggiunti = 0
            for np_ in nuovi_profili:
                src_p = os.path.join(src_root, np_)
                if not os.path.isdir(src_p): continue
                init_profilo(np_)
                src_d = os.path.join(src_p, "documenti")
                dst_d = profilo_docs(np_)
                src_r = os.path.join(src_p, "registry.json")
                imp = {}
                if os.path.exists(src_r):
                    with open(src_r, "r", encoding="utf-8") as f_:
                        imp = json.load(f_)
                reg = load_registry(np_)
                doppioni = [k for k in imp if k in reg]
                sovrascrivi = True
                if doppioni:
                    msg = f"Profilo '{np_}': trovati {len(doppioni)} documento/i già esistenti:\n"
                    msg += "\n".join(f"  • {d}" for d in doppioni[:8])
                    if len(doppioni) > 8: msg += f"\n  ... e altri {len(doppioni)-8}"
                    msg += "\n\nSovrascrivere i documenti esistenti?"
                    sovrascrivi = self.show_custom_askyesno("Documenti duplicati", msg)
                if os.path.isdir(src_d):
                    for f_ in os.listdir(src_d):
                        dst_f = os.path.join(dst_d, f_)
                        if os.path.exists(dst_f) and not sovrascrivi:
                            continue
                        shutil.copy2(os.path.join(src_d, f_), dst_f)
                if sovrascrivi:
                    reg.update(imp)
                else:
                    for k, v in imp.items():
                        if k not in reg:
                            reg[k] = v
                save_registry(np_, reg)
                if np_ not in profili_attuali:
                    profili_attuali.append(np_)
                    aggiunti += 1
            save_profili(profili_attuali)
            shutil.rmtree(tmp, ignore_errors=True)
            for p_, lt_ in load_tree_refs.items():
                lt_()
            if DB_CONDIVISO:
                self.notifica_modifica_web()
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 📡 Notifica di aggiornamento inviata .")
            self.show_custom_info("Importazione completata",
                f"Importazione da ZIP completata.\nNuovi profili aggiunti: {aggiunti}\n"
                f"Riavvia la finestra per vedere eventuali nuovi tab.")
            win.destroy()
            self.after(100, self.gestisci_documenti_personali)
        except Exception as e:
            self.show_custom_warning("Errore importazione", f"Impossibile importare:\n{e}")
    menu_arch.add_command(label="💾 Esporta ZIP completo", command=esporta_zip_completo)
    menu_arch.add_command(label="📥 Importa ZIP completo", command=importa_zip_completo)
    menu_arch.add_separator()
    profili = load_profili()
    load_tree_refs = {}
    backup_refs    = {}
    for p in profili:
        result = costruisci_tab(p)
        if result:
            load_tree_refs[p] = result[0]
            backup_refs[p]    = result[1]
    menu_arch.add_command(label="❌ Chiudi (ESC)", command=chiudi_win)
    costruisci_tab_profili()
    def refresh_tutti():
        for p, lt in load_tree_refs.items():
            lt()
    self._doc_pers_load_tree = refresh_tutti
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    w, h = 1100, 620
    win.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")
    win.transient(self)
    win.deiconify()

def backup_documenti_personali(self):
    import __main__ as _app
    DOC_PERS_DIR = _app.DOC_PERS_DIR
    BASE_DIR = _app.BASE_DIR
    from datetime import datetime
    try:
        import tempfile
        bk_dir = os.path.join(BASE_DIR, "backup")
        os.makedirs(bk_dir, exist_ok=True)
        files = sorted(
            [os.path.join(bk_dir, f) for f in os.listdir(bk_dir) if f.startswith("Archivio_Doc_Personali_")],
            key=os.path.getmtime
        )
        for f in files[:-2]:
            os.remove(f)
        ts  = datetime.now().strftime("%d%m%Y_%H%M")
        tmp = tempfile.mkdtemp()
        shutil.copytree(DOC_PERS_DIR, os.path.join(tmp, "documenti_personali"), dirs_exist_ok=True)
        profili_file = os.path.join(DOC_PERS_DIR, "profili.json")
        if os.path.exists(profili_file):
            shutil.copy2(profili_file, tmp)
        arc = os.path.join(bk_dir, f"Archivio_Doc_Personali_{ts}")
        shutil.make_archive(arc, "zip", tmp, "")
        shutil.rmtree(tmp, ignore_errors=True)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Backup Documenti Personali (ZIP) completato.")
        return arc + ".zip"
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Backup Archivio_Doc_Personali errore: {e}")
        return None
        
def mostra_help_documenti_personali(self):
    if hasattr(self, '_help_doc_pers_popup') and self._help_doc_pers_popup.winfo_exists():
        self._help_doc_pers_popup.destroy()
    popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    popup.title("Guida: Archivio Documenti Personali")
    popup_width = 950
    popup_height = 560
    sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
    popup.geometry(f"{popup_width}x{popup_height}+{(sw-popup_width)//2}+{(sh-popup_height)//2}")
    popup.resizable(False, False)
    popup.transient(self)
    popup.update_idletasks()
    popup.grab_set()
    popup.focus_set()
    self._help_doc_pers_popup = popup
    main_frame = ttk.Frame(popup, padding="15")
    main_frame.pack(fill="both", expand=True)
    content_frame = tk.Frame(main_frame)
    content_frame.pack(fill="both", expand=True)
    def ottieni_contenuto_testo():
        t = ""
        t += "=================================================\n"
        t += "       HELP: ARCHIVIO DOCUMENTI PERSONALI\n"
        t += "=================================================\n"
        t += "\nProfili:\n"
        t += "---------------------------------------\n"
        t += "• Ogni persona ha un tab dedicato. Massimo 5 profili.\n"
        t += "• Tab ⚙️ Profili: aggiungi o elimina profili. L'eliminazione cancella tutti i documenti del profilo.\n"
        t += "\nArchiviazione Documenti:\n"
        t += "---------------------------------------\n"
        t += "• Compila Data, Categoria, Descrizione (max 30 car.) e Note (max 30 car.), poi clicca Archivia PDF.\n"
        t += "• Il file viene copiato nella cartella del profilo con nome univoco basato su data+descrizione+categoria.\n"
        t += "• Se esiste già un file con lo stesso nome viene sovrascritto.\n"
        t += "\nNavigazione:\n"
        t += "---------------------------------------\n"
        t += "• Doppio clic su una riga per aprire il PDF nel viewer interno.\n"
        t += "• Clicca l'intestazione di una colonna per ordinare.\n"
        t += "• Usa il campo Cerca per filtrare in tempo reale su tutti i campi.\n"
        t += "• Tasto CANC per eliminare i documenti selezionati.\n"
        t += "• CTRL+Click per selezione multipla, SHIFT+Click per intervallo.\n"
        t += "\nCategorie:\n"
        t += "---------------------------------------\n"
        t += "• Ogni profilo ha le proprie categorie (21 preimpostate).\n"
        t += "• Bottone Categorie: aggiungi (max 25 car.), rinomina o cancella categorie.\n"
        t += "• Le categorie sono ordinate alfabeticamente (case-insensitive).\n"
        t += "\nBackup e Importa/Esporta:\n"
        t += "---------------------------------------\n"
        t += "• Esporta Zip: salva i documenti del profilo corrente in un archivio ZIP.\n"
        t += "• Importa Zip: importa un archivio ZIP nel profilo corrente. Unisce i documenti esistenti.\n"
        t += "• Menu 📂 Archivio → Esporta ZIP completo: salva tutti i profili in un unico ZIP.\n"
        t += "• Menu 📂 Archivio → Importa ZIP completo: ripristina tutti i profili. Se trova doppioni chiede per ogni profilo.\n"
        t += "• Backup automatico (max 3 rotanti) eseguito ad ogni apertura/chiusura finestra e ogni 12 ore.\n"
        return t.strip()
    def sezione(testo, bold=False):
        tk.Label(content_frame, text=testo,
                 font=("Arial", 10, "bold") if bold else ("Arial", 9),
                 justify=tk.LEFT, anchor='w',
                 wraplength=900).pack(fill='x', padx=5, pady=(8 if bold else 0, 3))
    sezione("Profili:", bold=True)
    sezione("• Ogni persona ha un tab dedicato. Massimo 5 profili.\n"
            "• Tab ⚙️ Profili: aggiungi o elimina profili. L'eliminazione cancella tutti i documenti del profilo.")
    sezione("Archiviazione Documenti:", bold=True)
    sezione("• Compila Data, Categoria, Descrizione (max 60 car.) e Note (max 120 car.), poi clicca Archivia PDF.\n"
            "• Il file viene copiato nella cartella del profilo con nome univoco basato su data+descrizione+categoria.\n"
            "• Se esiste già un file con lo stesso nome viene sovrascritto.")
    sezione("Navigazione:", bold=True)
    sezione("• Doppio clic su una riga per aprire il PDF nel viewer interno.\n"
            "• Clicca l'intestazione di una colonna per ordinare.\n"
            "• Usa il campo Cerca per filtrare in tempo reale su tutti i campi.\n"
            "• Tasto CANC per eliminare i documenti selezionati.\n"
            "• CTRL+Click per selezione multipla, SHIFT+Click per intervallo.")
    sezione("Categorie:", bold=True)
    sezione("• Ogni profilo ha le proprie categorie (21 preimpostate).\n"
            "• Bottone Categorie: aggiungi (max 25 car.), rinomina o cancella categorie.\n"
            "• Le categorie sono ordinate alfabeticamente (case-insensitive).")
    sezione("Backup e Importa/Esporta:", bold=True)
    sezione("• Esporta Zip: salva i documenti del profilo corrente in un archivio ZIP.\n"
            "• Importa Zip: importa nel profilo corrente. Se trova doppioni chiede se sovrascrivere.\n"
            "• Menu 📂 Archivio → Esporta ZIP completo: salva tutti i profili in un unico ZIP.\n"
            "• Menu 📂 Archivio → Importa ZIP completo: ripristina tutti i profili. Chiede per ogni profilo in caso di doppioni.\n"
            "• Backup automatico (max 3 rotanti) eseguito ad ogni apertura/chiusura e ogni 12 ore.")
    bottom_frame = tk.Frame(main_frame, bg=self.COLOR_TOPLEVEL)
    bottom_frame.pack(side=tk.BOTTOM, fill='x', pady=5)
    img_stampa = self.icone_gui.get("stampa")
    btn_stampa = ttk.Label(bottom_frame, compound="left", image=img_stampa,
                           text=" Stampa Guida", background=self.COLOR_WIDGET_BG,
                           foreground=self.TEXT_COLOR, cursor="hand2")
    btn_stampa.image = img_stampa
    btn_stampa.pack(side=tk.LEFT, pady=5, padx=10)
    btn_stampa.bind("<Button-1>", lambda e: self._stampa_lista_diretta(
        ottieni_contenuto_testo(), self.show_custom_warning))

    img_check = self.icone_gui.get("check")
    btn_ok = ttk.Label(bottom_frame, compound="left", image=img_check,
                       text=" Ho Capito (OK)", background=self.COLOR_WIDGET_BG,
                       foreground=self.TEXT_COLOR, cursor="hand2")
    btn_ok.image = img_check
    btn_ok.pack(side=tk.RIGHT, pady=5, padx=10)
    btn_ok.bind("<Button-1>", lambda e: popup.destroy())
    popup.bind("<Escape>", lambda e: popup.destroy())
    popup.wait_visibility()
    popup.grab_set()
    popup.focus_set()
    
