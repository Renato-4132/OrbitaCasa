#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import ast
import json
import shutil
import tempfile
import stat
import datetime
import threading
import requests
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Toplevel, Label, Button, TclError

from moduli.spinner_animato import crea_spinner_animato

def apri_dieta(self):

    import __main__ as _app
    DB_DIR         = _app.DB_DIR
    EXPORT_FILES   = _app.EXPORT_FILES
    PEDOMETRO_FILE = _app.PEDOMETRO_FILE
    FABB_FILE      = _app.FABB_FILE
    PESO_FILE      = _app.PESO_FILE
    CUSTOM_FILE    = _app.CUSTOM_FILE
    API_KEY        = _app.API_KEY
    GEMINI         = _app.GEMINI
    ALIMENTI       = _app.ALIMENTI
    genai_client   = _app.genai_client

    try:
        import json as _json_ua
        _ua_conf = os.path.join(DB_DIR, "utente_attivo.json")
        _utente_attivo = _json_ua.load(open(_ua_conf, encoding="utf-8"))["utente"] \
            if os.path.exists(_ua_conf) else "Generico"
    except Exception:
        _utente_attivo = "Generico"
    if _utente_attivo != "Generico":
        _profilo_dir = os.path.join(DB_DIR, "utenti", _utente_attivo)
        os.makedirs(_profilo_dir, exist_ok=True)
        DIETA_FILE     = os.path.join(_profilo_dir, "dieta.json")
        PESO_FILE      = os.path.join(_profilo_dir, "peso.json")
        FABB_FILE      = os.path.join(_profilo_dir, "fabbisogno.json")
        PEDOMETRO_FILE = os.path.join(_profilo_dir, "pedometro.json")
        CUSTOM_FILE    = os.path.join(_profilo_dir, "alimenti_custom.json")
    else:
        DIETA_FILE     = os.path.join(DB_DIR, "dieta_piano.json")
        PESO_FILE      = os.path.join(DB_DIR, "peso_storico.json")
        FABB_FILE      = os.path.join(DB_DIR, "fabbisogno_dati.json")
        PEDOMETRO_FILE = os.path.join(DB_DIR, "pedometro.json")
        CUSTOM_FILE    = os.path.join(DB_DIR, "alimenti_custom.json")
        
    DIETA_DEFAULT = [
      {"titolo": "Settimana 1", "giorni": [
        ["Lunedì",    "Pane, olio EVO, caffè",             "Pasta al pomodoro, insalata",        "Zuppa di ceci, pane",         "Frutta, noci",     1850, 72, 52, 240, 45, 22],
        ["Martedì",   "Yogurt greco, miele, noci",          "Spaghetti aglio olio peperoncino",  "Tonno alla piastra, patate",  "Arancia",          1780, 88, 48, 210, 38, 20],
        ["Mercoledì", "Pane integrale, ricotta, miele",     "Pasta e fagioli, pane",             "Frittata di zucchine",        "Mandorle, mela",   1720, 79, 55, 200, 35, 24],
        ["Giovedì",   "Avena, latte, banana",               "Risotto allo zafferano",            "Pollo alla brace, peperoni",  "Yogurt",           1900, 95, 50, 225, 42, 18],
        ["Venerdì",   "Uova strapazzate, pane",             "Zuppa lenticchie, pane",            "Branzino al forno, patate",   "Frutta secca",     1760, 85, 47, 215, 40, 26],
        ["Sabato",    "Pane, olio EVO, pomodoro",           "Tagliata di manzo, rucola",         "Insalata di farro, feta",     "Kiwi",             2050,102, 70, 220, 38, 20],
        ["Domenica",  "Cornetto integrale, succo arancia",  "Pasta al forno, melanzane",         "Minestrone, pane",            "Yogurt greco",     1950, 80, 60, 255, 50, 28],
      ]},
      {"titolo": "Settimana 2", "giorni": [
        ["Lunedì",    "Yogurt bianco, frutta, mandorle",    "Pasta pesto genovese, caprese",     "Crema di piselli, crostini",  "Noci, arancia",    1830, 70, 54, 235, 44, 22],
        ["Martedì",   "Pane, olio EVO, pomodoro",           "Riso integrale, verdure, feta",     "Tonno al forno, pomodorini",  "Mela",             1760, 86, 46, 215, 38, 20],
        ["Mercoledì", "Avena, latte, miele, noci",          "Zuppa cannellini e salvia, pane",   "Uova al tegamino, asparagi",  "Pera, mandorle",   1700, 77, 53, 205, 36, 25],
        ["Giovedì",   "Pane integrale, ricotta, marmellata","Pasta e ceci al rosmarino",         "Tacchino alla brace, zucch.", "Frutta",           1880, 98, 48, 225, 40, 20],
        ["Venerdì",   "Yogurt greco, miele, banana",        "Risotto asparagi e parmigiano",     "Orata al forno, patate",      "Kiwi",             1770, 83, 49, 220, 40, 22],
        ["Sabato",    "Uova strapazzate, pane",             "Costata di manzo, insalata",        "Taboulé, cetrioli, menta",    "Frutta secca",     2030,100, 68, 225, 38, 20],
        ["Domenica",  "Pane, olio EVO, latte",              "Lasagne ragù di verdure",           "Ribollita toscana, pane",     "Yogurt",           1920, 78, 58, 250, 48, 26],
      ]},
      {"titolo": "Settimana 3", "giorni": [
        ["Lunedì",    "Avena, latte, frutta fresca",        "Pasta al pomodoro, finocchi",       "Minestra lenticchie, spinaci","Mandorle",         1800, 71, 50, 235, 44, 24],
        ["Martedì",   "Yogurt greco, noci, miele",          "Spaghetti alle vongole",            "Tonno al sesamo, patate",     "Arancia",          1790, 90, 48, 212, 38, 20],
        ["Mercoledì", "Pane, olio EVO, pomodoro",           "Pasta melanzane ricotta salata",    "Frittata cipolle e patate",   "Mela, noci",       1730, 76, 56, 208, 36, 22],
        ["Giovedì",   "Uova strapazzate, pane",             "Zuppa farro e borlotti, pane",      "Pollo alla brace, timo",      "Yogurt",           1910, 97, 52, 222, 40, 18],
        ["Venerdì",   "Yogurt bianco, frutta, mandorle",    "Risotto al limone con gamberi",     "Pesce spada alla brace",      "Kiwi",             1780, 88, 50, 218, 38, 22],
        ["Sabato",    "Cornetto integrale, succo",          "Bistecca, fagioli all'uccelletto",  "Insalata di orzo, feta",      "Frutta",           2060,103, 72, 228, 40, 20],
        ["Domenica",  "Pane, olio EVO, latte",              "Pasta al forno, ricotta, spinaci",  "Vellutata di zucca, crostini","Yogurt greco",     1930, 79, 61, 248, 48, 26],
      ]},
      {"titolo": "Settimana 4", "giorni": [
        ["Lunedì",    "Yogurt greco, miele, noci",          "Pasta sugo olive, insalata",        "Zuppa ceci e bietole, pane",  "Pera",             1820, 73, 51, 238, 44, 24],
        ["Martedì",   "Pane, olio EVO, pomodoro",           "Pasta e piselli, insalata",         "Tonno alla siciliana",        "Mandorle",         1770, 87, 47, 213, 38, 20],
        ["Mercoledì", "Avena, latte, banana",               "Riso verdure e curcuma",            "Frittata asparagi, formaggio","Mela, noci",       1710, 75, 54, 206, 36, 22],
        ["Giovedì",   "Pane integrale, ricotta, marmellata","Minestrone, pane rustico",          "Spiedini pollo e verdure",    "Frutta",           1890, 96, 49, 228, 40, 20],
        ["Venerdì",   "Uova strapazzate, pane",             "Pasta alle sarde, finocchietto",    "Salmone al forno, patate",    "Kiwi",             1800, 90, 55, 210, 38, 24],
        ["Sabato",    "Yogurt greco, noci, arancia",        "Arrosticini, peperoni arrosto",     "Insalata farro, mozz.",       "Frutta secca",     2040,101, 69, 222, 38, 20],
        ["Domenica",  "Cornetto integrale, succo",          "Pasta al pesto di pistacchi",       "Caponata siciliana, uovo",    "Yogurt",           1940, 78, 62, 250, 48, 26],
      ]},
    ]

    def carica_alimenti_da_github():
        try:
            response = requests.get(ALIMENTI, timeout=10)
            response.raise_for_status()
            testo = response.text
            if "ALIMENTI_DB =" in testo:
                    inizio = testo.find("[")
                    fine = testo.rfind("]") + 1
                    lista_str = testo[inizio:fine]
                    return ast.literal_eval(lista_str)
            else:
                    return response.json()
        except Exception as e:
            self.show_toast("Errore nel download database dal server.")
            print(f"Errore nel download dal server: {e}")
            return []
    ALIMENTI_DB = carica_alimenti_da_github()
    def _carica_custom():
        try:
            if os.path.exists(CUSTOM_FILE):
                with open(CUSTOM_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return []
    def _salva_custom(lista):
        try:
            os.makedirs(DB_DIR, exist_ok=True)
            with open(CUSTOM_FILE, 'w', encoding='utf-8') as f:
                json.dump(lista, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.show_custom_warning("Errore", f"Salvataggio custom fallito:\n{e}")
    alimenti_custom = _carica_custom()
    _nomi_custom = {r[0] for r in alimenti_custom}
    ALIMENTI_MERGED   = [r for r in ALIMENTI_DB if r[0] not in _nomi_custom] + \
                        [tuple(r) for r in alimenti_custom]
    ALIMENTI_ORDINATI = sorted(ALIMENTI_MERGED, key=lambda r: r[0].lower())
    _ali_map   = {r[0]: r for r in ALIMENTI_ORDINATI}
    _categorie = ["Tutte"] + sorted({r[1] for r in ALIMENTI_MERGED})
    def _apri_form_custom(prefill=None):
        fc = tk.Toplevel(popup)
        fc.title("Nuovo alimento" if not prefill else "Modifica alimento")
        fc.resizable(False, False)
        fc.transient(popup)
        fc.configure(bg=self.COLOR_WIDGET_BG)
        fc.bind("<Escape>", lambda e: fc.destroy())

        ttk.Label(fc, text="➕  Aggiungi alimento personalizzato",
                  font=("Arial", 10, "bold"),
                  background=self.COLOR_WIDGET_BG,
                  foreground=self.COLOR_HIGHLIGHT).grid(
                  row=0, column=0, columnspan=4, padx=16, pady=(12,8), sticky="w")

        campi = [
            ("Nome",      "nome",    str,   ""),
            ("Categoria", "cat",     str,   "Piatti Pronti"),
            ("Kcal",      "kcal",    float, "0"),
            ("Proteine g","prot",    float, "0"),
            ("Grassi g",  "grassi",  float, "0"),
            ("Carb g",    "carb",    float, "0"),
            ("Zuccheri g","zucc",    float, "0"),
            ("Fibre g",   "fibre",   float, "0"),
        ]
        vars_ = {}
        cat_valori = sorted({r[1] for r in ALIMENTI_MERGED})
        for i, (lbl, key, tipo, default) in enumerate(campi):
            row = 1 + i // 2
            col = (i % 2) * 2
            tk.Label(fc, text=f"{lbl}:", bg=self.COLOR_WIDGET_BG,
                     fg=self.TEXT_COLOR, font=("Arial", 9)).grid(
                     row=row, column=col, padx=(16,4), pady=4, sticky="e")
            if key == "cat":
                v = tk.StringVar(value=prefill[1] if prefill else default)
                w = ttk.Combobox(fc, textvariable=v, values=cat_valori,
                                 width=18, style="Border.TCombobox")
                w.grid(row=row, column=col+1, padx=(0,16), pady=4, sticky="w")
            else:
                v = tk.StringVar(value=str(prefill[campi.index((lbl,key,tipo,default))]) 
                                 if prefill else default)
                tk.Entry(fc, textvariable=v, width=20,
                         bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                         insertbackground=self.TEXT_COLOR,
                         highlightthickness=1,
                         highlightbackground=self.COLOR_HIGHLIGHT).grid(
                         row=row, column=col+1, padx=(0,16), pady=4, sticky="w")
            vars_[key] = (v, tipo)
        def _conferma():
            nonlocal alimenti_custom, ALIMENTI_MERGED, ALIMENTI_ORDINATI, _ali_map, _categorie
            nome = vars_["nome"][0].get().strip()
            if not nome:
                self.show_custom_warning("Errore", "Il nome non può essere vuoto.")
                return
            try:
                riga = [
                    nome,
                    vars_["cat"][0].get().strip() or "Altro",
                    round(float(vars_["kcal"][0].get()),   1),
                    round(float(vars_["prot"][0].get()),   1),
                    round(float(vars_["grassi"][0].get()), 1),
                    round(float(vars_["carb"][0].get()),   1),
                    round(float(vars_["zucc"][0].get()),   1),
                    round(float(vars_["fibre"][0].get()),  1),
                ]
            except ValueError:
                self.show_custom_warning("Errore", "I valori numerici non sono validi.")
                return
            alimenti_custom = [r for r in alimenti_custom if r[0] != nome]
            alimenti_custom.append(riga)
            _salva_custom(alimenti_custom)
            _nomi_c = {r[0] for r in alimenti_custom}
            ALIMENTI_MERGED   = [r for r in ALIMENTI_DB if r[0] not in _nomi_c] + \
                                [tuple(r) for r in alimenti_custom]
            ALIMENTI_ORDINATI[:] = sorted(ALIMENTI_MERGED, key=lambda r: r[0].lower())
            _ali_map.clear();   _ali_map.update({r[0]: r for r in ALIMENTI_ORDINATI})
            _categorie[:] = ["Tutte"] + sorted({r[1] for r in ALIMENTI_MERGED})
            fc.destroy()
            self.show_toast(f"Alimento '{nome}' salvato.")
        bot = tk.Frame(fc, bg=self.COLOR_WIDGET_BG)
        bot.grid(row=10, column=0, columnspan=4, pady=(8,14))
        def _mk(parent, ico, txt, cmd, fg=None):
            img = self.icone_gui.get(ico)
            fg  = fg or self.TEXT_COLOR
            l   = ttk.Label(parent, text=f" {txt}", image=img, compound="left",
                            background=self.COLOR_WIDGET_BG, foreground=fg,
                            cursor="hand2", font=("Arial", 9, "bold"), padding=(6,2))
            if img: l.image = img
            l.pack(side="left", padx=6)
            l.bind("<Button-1>", lambda e: cmd())
        _mk(bot, "check",  "Salva",   _conferma, "#98C379")
        _mk(bot, "chiudi", "Annulla", fc.destroy)
        fc.update_idletasks()
        w2, h2 = 520, 220
        x2 = popup.winfo_x() + popup.winfo_width()//2  - w2//2
        y2 = popup.winfo_y() + popup.winfo_height()//2 - h2//2
        fc.geometry(f"{w2}x{h2}+{x2}+{y2}")
        fc.grab_set()
        fc.focus_force()
    def _elimina_custom():
        if not alimenti_custom:
            self.show_custom_warning("Nessun custom",
                "Non ci sono alimenti personalizzati da eliminare.")
            return
        ed = tk.Toplevel(popup)
        ed.title("Elimina alimento custom")
        ed.resizable(False, False)
        ed.transient(popup)
        ed.configure(bg=self.COLOR_WIDGET_BG)
        ed.bind("<Escape>", lambda e: ed.destroy())
        ttk.Label(ed, text="Seleziona le voci da eliminare:",
                  font=("Arial", 9, "bold"),
                  background=self.COLOR_WIDGET_BG,
                  foreground=self.TEXT_COLOR).pack(padx=14, pady=(10,4), anchor="w")
        fr_list = tk.Frame(ed, bg=self.COLOR_WIDGET_BG)
        fr_list.pack(fill="both", expand=True, padx=14, pady=4)
        vsb_e = ttk.Scrollbar(fr_list, orient="vertical", style="Vertical.TScrollbar")
        vsb_e.pack(side="right", fill="y")
        lb = tk.Listbox(fr_list, selectmode="multiple",
                        bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                        selectbackground=self.COLOR_HIGHLIGHT,
                        font=("Arial", 9), yscrollcommand=vsb_e.set,
                        highlightthickness=1,
                        highlightbackground=self.COLOR_HIGHLIGHT,
                        height=12)
        lb.pack(fill="both", expand=True)
        vsb_e.config(command=lb.yview)
        for r in sorted(alimenti_custom, key=lambda x: x[0].lower()):
            lb.insert("end", f"{r[0]}  ({r[1]}, {r[2]} kcal)")
        def _conferma_elim():
            nonlocal alimenti_custom, ALIMENTI_MERGED, ALIMENTI_ORDINATI, _ali_map, _categorie
            sel = lb.curselection()
            if not sel:
                ed.destroy(); return
            nomi_elim = {lb.get(i).split("  (")[0] for i in sel}
            if not self.show_custom_askyesno("Conferma",
                    f"Eliminare {len(nomi_elim)} alimento/i?"):
                return
            alimenti_custom[:] = [r for r in alimenti_custom if r[0] not in nomi_elim]
            _salva_custom(alimenti_custom)
            _nomi_c = {r[0] for r in alimenti_custom}
            ALIMENTI_MERGED   = [r for r in ALIMENTI_DB if r[0] not in _nomi_c] + \
                                [tuple(r) for r in alimenti_custom]
            ALIMENTI_ORDINATI[:] = sorted(ALIMENTI_MERGED, key=lambda r: r[0].lower())
            _ali_map.clear();   _ali_map.update({r[0]: r for r in ALIMENTI_ORDINATI})
            _categorie[:] = ["Tutte"] + sorted({r[1] for r in ALIMENTI_MERGED})
            ed.destroy()
            self.show_toast(f"Eliminati {len(nomi_elim)} alimento/i.")
        bot_e = tk.Frame(ed, bg=self.COLOR_WIDGET_BG)
        bot_e.pack(pady=(6,12))
        def _mk2(parent, ico, txt, cmd, fg=None):
            img = self.icone_gui.get(ico)
            fg  = fg or self.TEXT_COLOR
            l   = ttk.Label(parent, text=f" {txt}", image=img, compound="left",
                            background=self.COLOR_WIDGET_BG, foreground=fg,
                            cursor="hand2", font=("Arial", 9, "bold"), padding=(6,2))
            if img: l.image = img
            l.pack(side="left", padx=6)
            l.bind("<Button-1>", lambda e: cmd())
        _mk2(bot_e, "delete", "Elimina selezionati", _conferma_elim, self.COLOR_ORANGE)
        _mk2(bot_e, "chiudi", "Annulla",             ed.destroy)
        ed.update_idletasks()
        w2, h2 = 500, 320
        x2 = popup.winfo_x() + popup.winfo_width()//2  - w2//2
        y2 = popup.winfo_y() + popup.winfo_height()//2 - h2//2
        ed.geometry(f"{w2}x{h2}+{x2}+{y2}")
        ed.grab_set()
        ed.focus_force()
    def _confronta_settimane():
        cs = tk.Toplevel(popup)
        cs.title("Confronto Settimane")
        cs.resizable(False, False)
        cs.transient(popup)
        cs.configure(bg=self.COLOR_WIDGET_BG)
        cs.bind("<Escape>", lambda e: cs.destroy())
        ttk.Label(cs, text="📊  Confronto Settimane — Media giornaliera",
                  font=("Arial", 11, "bold"),
                  background=self.COLOR_WIDGET_BG,
                  foreground=self.COLOR_HIGHLIGHT).pack(padx=16, pady=(12, 8))
        colonne = ("settimana", "kcal", "prot", "grassi", "carb", "zucc", "fibre")
        labels  = ("Settimana", "Kcal", "Prot. g", "Gras. g", "Carb. g", "Zucc. g", "Fibre g")
        widths  = (160, 70, 70, 70, 70, 70, 70)
        fr_tv = tk.Frame(cs, bg=self.COLOR_WIDGET_BG)
        fr_tv.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        tv = ttk.Treeview(fr_tv, columns=colonne, selectmode='browse', show="headings",
                          style="Treeview", height=len(piano_dati) + 1)
        tv.pack(fill="both", expand=True)
        for col, lbl, w in zip(colonne, labels, widths):
            tv.heading(col, text=lbl)
            tv.column(col, width=w, anchor="w" if col == "settimana" else "center")
        righe_medie = []
        for sett in piano_dati:
            giorni = sett["giorni"]
            n = len(giorni)
            if n == 0:
                continue
            media = [round(sum(r[i] for r in giorni if len(r) > i) / n)
                     for i in range(5, 11)]
            righe_medie.append((sett["titolo"], *media))
        if righe_medie:
            n_sett = len(righe_medie)
            media_glob = [round(sum(r[i] for r in righe_medie) / n_sett)
                          for i in range(1, 7)]
            righe_medie.append(("MEDIA GLOBALE", *media_glob))
        kcal_vals = [r[1] for r in righe_medie[:-1]]
        kcal_max  = max(kcal_vals) if kcal_vals else 0
        kcal_min  = min(kcal_vals) if kcal_vals else 0
        for i, riga in enumerate(righe_medie):
            is_global = riga[0] == "MEDIA GLOBALE"
            if is_global:
                tag = "globale"
            elif riga[1] == kcal_max:
                tag = "max"
            elif riga[1] == kcal_min:
                tag = "min"
            else:
                tag = "alt" if i % 2 == 0 else "norm"
            tv.insert("", "end", values=riga, tags=(tag,))
        tv.tag_configure("max",     background="#3a2000", foreground=self.COLOR_ORANGE)
        tv.tag_configure("min",     background="#0d2e0d", foreground="#98C379")
        tv.tag_configure("globale", background=self.COLOR_HIGHLIGHT,
                                    foreground=self.COLOR_WHITE,
                                    font=("Arial", 9, "bold"))
        tv.tag_configure("alt",     background=self.COLOR_WIDGET_BG)
        tv.tag_configure("norm",    background=self.COLOR_WIDGET_BG)
        leg = tk.Frame(cs, bg=self.COLOR_WIDGET_BG)
        leg.pack(padx=16, pady=(0, 6), anchor="w")
        for col, txt in [("#98C379", "▮  Kcal più basse"),
                         (self.COLOR_ORANGE, "▮  Kcal più alte")]:
            tk.Label(leg, text=txt, bg=self.COLOR_WIDGET_BG,
                     fg=col, font=("Arial", 8)).pack(side="left", padx=(0, 16))
        ttk.Separator(cs, orient="horizontal").pack(fill="x", padx=16, pady=(4, 6))
        ttk.Label(cs, text="Dettaglio macro (media giornaliera per settimana):",
                  background=self.COLOR_WIDGET_BG,
                  foreground=self.TEXT_COLOR,
                  font=("Arial", 8, "italic")).pack(padx=16, anchor="w")
        fr_bar = tk.Frame(cs, bg=self.COLOR_WIDGET_BG)
        fr_bar.pack(fill="x", padx=16, pady=(4, 4))
        MACRO_COLS  = [("Prot. g", "#61AFEF"),
                       ("Gras. g", "#E06C75"),
                       ("Carb. g", "#E5C07B")]
        BAR_MAX_W   = 180
        ROW_H       = 22
        for ri, riga in enumerate(righe_medie[:-1]):
            tk.Label(fr_bar, text=riga[0], width=14, anchor="w",
                     bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                     font=("Arial", 8)).grid(row=ri, column=0, pady=1, sticky="w")
            totale = sum(riga[j] for j in (2, 3, 4)) or 1
            cx = 1
            for mi, (mlbl, mcol) in enumerate(MACRO_COLS):
                val  = riga[2 + mi]
                bw   = max(4, int(val / totale * BAR_MAX_W))
                fr_b = tk.Frame(fr_bar, bg=mcol,
                                width=bw, height=ROW_H - 4)
                fr_b.grid(row=ri, column=cx, padx=1, pady=1, sticky="w")
                fr_b.grid_propagate(False)
                tk.Label(fr_b, text=f"{val}g", bg=mcol,
                         fg="black", font=("Arial", 7)).pack(
                         side="left", padx=2)
                cx += 1
        leg2 = tk.Frame(cs, bg=self.COLOR_WIDGET_BG)
        leg2.pack(padx=16, pady=(2, 10), anchor="w")
        for col, txt in [("#61AFEF", "▮ Proteine"),
                         ("#E06C75", "▮ Grassi"),
                         ("#E5C07B", "▮ Carboidrati")]:
            tk.Label(leg2, text=txt, bg=self.COLOR_WIDGET_BG,
                     fg=col, font=("Arial", 8)).pack(side="left", padx=(0, 12))

        bot = tk.Frame(cs, bg=self.COLOR_WIDGET_BG)
        bot.pack(pady=(0, 12))
        img_c = self.icone_gui.get("chiudi")
        btn_c = ttk.Label(bot, text=" Chiudi", image=img_c, compound="left",
                          background=self.COLOR_WIDGET_BG,
                          foreground=self.TEXT_COLOR,
                          cursor="hand2", font=("Arial", 10, "bold"))
        btn_c.pack()
        btn_c.bind("<Button-1>", lambda e: cs.destroy())
        cs.update_idletasks()
        w2, h2 = 620, 480
        x2 = popup.winfo_x() + popup.winfo_width()  // 2 - w2 // 2
        y2 = popup.winfo_y() + popup.winfo_height() // 2 - h2 // 2
        cs.geometry(f"{w2}x{h2}+{x2}+{y2}")
        cs.grab_set()
        cs.focus_force()
    if hasattr(self, '_dieta_popup') and self._dieta_popup and self._dieta_popup.winfo_exists():
        self._dieta_popup.lift()
        return
    def _carica_piano():
        try:
            if os.path.exists(DIETA_FILE):
                with open(DIETA_FILE, 'r', encoding='utf-8') as f:
                    d = json.load(f)
                    return d.get("piano", []), d.get("composizioni", {})
        except json.JSONDecodeError:
            self.show_custom_warning("Attenzione",
                "Il file del piano dieta è corrotto.\nVerrà caricato il piano predefinito.")
        except Exception:
            pass
        piano = [{"titolo": s["titolo"], "giorni": [list(g) for g in s["giorni"]]}
                 for s in DIETA_DEFAULT]
        return piano, {}
    def _salva_piano():
        try:
            os.makedirs(DB_DIR, exist_ok=True)
            with open(DIETA_FILE, 'w', encoding='utf-8') as f:
                json.dump({"piano": piano_dati, "composizioni": composizioni},
                          f, indent=2, ensure_ascii=False)
            self.show_toast("Piano dieta salvato.")
        except Exception as e:
            self.show_custom_warning("Errore", f"Salvataggio fallito:\n{e}")
    def _ripristina_default():
        nonlocal piano_dati, composizioni
        if not self.show_custom_askyesno("Ripristina",
                "Ripristinare il piano predefinito?\nLe modifiche andranno perse."):
            return
        piano_dati = [{"titolo": s["titolo"], "giorni": [list(g) for g in s["giorni"]]}
                      for s in DIETA_DEFAULT]
        composizioni = {}
        _ricarica_settimane()
        self.show_toast("Piano ripristinato.")
    def _genera_pdf(dest=None):
        try:
            import pymupdf as fitz
        except ImportError:
            self.show_custom_warning("Libreria mancante",
                "PyMuPDF non è installato.\nVai in Sistema → Aggiorna Librerie Python.")
            return None
        if dest is None:
            now   = datetime.date.today()
            fname = f"Dieta_{now.strftime('%d-%m-%Y')}.pdf"
            dest  = filedialog.asksaveasfilename(
                defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
                initialdir=EXPORT_FILES,
                initialfile=fname,
                confirmoverwrite=False,
                title="Salva Piano Dieta PDF", parent=popup)
            if not dest:
                return None
        try:
            doc = fitz.open()
            GREEN      = (0.10, 0.42, 0.18)
            GREEN2     = (0.18, 0.55, 0.29)
            GREEN_LITE = (0.94, 0.97, 0.95)
            GRAY       = (0.55, 0.55, 0.55)
            WHITE      = (1.0,  1.0,  1.0)
            BLACK      = (0.0,  0.0,  0.0)
            ROW_ALT    = (0.96, 0.99, 0.97)
            PAGE_H, PAGE_W = fitz.paper_size("a4")
            ML, MR, MT, MB = 38, 38, 48, 48
            # Giorno | Col. | Pranzo | Cena | Spunt. | Kcal | Prot | Gras | Carb | Zucc | Fibre
            CW = [62, 115, 115, 115, 90, 38, 36, 36, 36, 36, 36]
            tw = sum(CW)
            HDR = ["Giorno","Colazione","Pranzo","Cena","Spuntino","Kcal","Prot.","Gras.","Carb.","Zucc.","Fibre"]
            def _dr(page, x, y, w, h, fill, stroke=None, lw=0.4):
                page.draw_rect(fitz.Rect(x,y,x+w,y+h), color=stroke, fill=fill, width=lw)
            def _tx(page, txt, x, y, fs=8, col=BLACK, bold=False, cw=None, center=False):
                fn = "hebo" if bold else "helv"
                s  = str(txt)
                if center and cw:
                    tw = fitz.get_text_length(s, fontname=fn, fontsize=fs)
                    x  = x + (cw - tw) / 2
                page.insert_text(fitz.Point(x, y), s, fontname=fn, fontsize=fs, color=col)
            ultimo_peso = peso_storico[-1]["peso"] if peso_storico else "--"
            data_peso = peso_storico[-1]["data"] if peso_storico else ""
            altezza = altezza_v.get() or "--"
            obiettivo = obiettivo_v.get() or "--"
            bmi_txt = "--"
            try:
                p = float(str(ultimo_peso).replace(",", "."))
                h = float(altezza.replace(",", ".")) / 100
                if h > 0:
                    bmi_val = round(p / (h * h), 1)
                    if bmi_val < 18.5:
                        bmi_cat = "Sottopeso — Peso insufficiente, rischio malnutrizione"
                    elif bmi_val < 25.0:
                        bmi_cat = "Normopeso — Peso nella norma, mantieni lo stile di vita"
                    elif bmi_val < 30.0:
                        bmi_cat = "Sovrappeso — Peso eccessivo, rischio cardiovascolare lieve"
                    elif bmi_val < 35.0:
                        bmi_cat = "Obesità I — Rischio moderato, consulta il medico"
                    elif bmi_val < 40.0:
                        bmi_cat = "Obesità II — Rischio elevato, intervento consigliato"
                    else:
                        bmi_cat = "Obesità III — Rischio molto elevato, consulta subito il medico"
                    bmi_txt = f"{bmi_val} — {bmi_cat}"
            except: pass
            for si, sett in enumerate(piano_dati):
                    page = doc.new_page(width=PAGE_W, height=PAGE_H)
                    cy = MT
                    _tx(page, "Piano Dieta Mediterranea", ML, cy, fs=15, col=GREEN, bold=True)
                    cy += 18
                    _tx(page, sett["titolo"], ML, cy, fs=10, col=GREEN2)
                    cy += 10
                    page.draw_line(fitz.Point(ML, cy), fitz.Point(PAGE_W - MR, cy), color=GREEN, width=1.0)
                    cy += 12
                    if si == 0:
                        _dr(page, ML, cy, tw, 25, fill=GREEN_LITE, stroke=GRAY, lw=0.3)
                        info_fisico = (f"Peso Attuale: {ultimo_peso} kg ({data_peso})  |  "
                        f"Altezza: {altezza} cm  |  Obiettivo: {obiettivo} kg  |  "
                        f"BMI: {bmi_txt}")
                    _tx(page, info_fisico, ML + 10, cy + 16, fs=8.5, col=BLACK, bold=True)
                    cy += 35
                    _dr(page, ML, cy, tw, 18, fill=GREEN2)
                    xc = ML
                    for h, w in zip(HDR, CW):
                            _tx(page, h, xc + 2, cy + 12, fs=7.5, col=WHITE, bold=True, cw=w-2, center=True)
                            xc += w
                    cy += 18
                    RH = 48
                    for ri, riga in enumerate(sett["giorni"]):
                            fill = ROW_ALT if ri % 2 == 0 else WHITE
                            _dr(page, ML, cy, tw, RH, fill=fill, stroke=(0.80, 0.88, 0.82))
                            xc = ML
                            _tx(page, riga[0], xc + 3, cy + 26, fs=8, col=GREEN, bold=True)
                            xc += CW[0]
                            for vi, (val, w) in enumerate(zip(riga[1:5], CW[1:5])):
                                    t = str(val).strip()
                                    parole = t.split()
                                    righe_pasto = []
                                    riga_curr = ""
                                    for p in parole:
                                            if len(riga_curr + p) < 22:
                                                    riga_curr += p + " "
                                            else:
                                                    righe_pasto.append(riga_curr.strip())
                                                    riga_curr = p + " "
                                    righe_pasto.append(riga_curr.strip())
                                    for i, txt_riga in enumerate(righe_pasto[:4]):
                                            _tx(page, txt_riga, xc + 2, cy + 12 + (i * 9), fs=6.5)
                                    xc += w
                            for val, w in zip(riga[5:], CW[5:]):
                                    _tx(page, str(val), xc + 1, cy + 26, fs=7.5, center=True, cw=w - 1)
                                    xc += w
                            page.draw_rect(fitz.Rect(ML, cy, ML + tw, cy + RH), color=(0.80, 0.88, 0.82), width=0.3)
                            cy += RH
                    tot = [sum(r[i] for r in sett["giorni"] if len(r) > 5) for i in range(5, 11)]
                    _dr(page, ML, cy, tw, 18, fill=GREEN_LITE, stroke=GREEN2, lw=0.6)
                    _tx(page, "TOTALE SETTIMANA", ML + 3, cy + 12, fs=7.5, col=GREEN, bold=True)
                    xc = ML + sum(CW[:5])
                    for val, w in zip(tot, CW[5:]):
                            _tx(page, str(val), xc + 1, cy + 12, fs=7.5, col=GREEN, bold=True, center=True, cw=w - 1)
                            xc += w
                    cy += 22
                    n = len(sett["giorni"])
                    med = [round(v / n) for v in tot]
                    _tx(page, f"Media/giorno: {med[0]} kcal | Prot {med[1]}g | Grassi {med[2]}g | Carb {med[3]}g | Zucc {med[4]}g | Fibre {med[5]}g",
                        ML, cy + 9, fs=7.5, col=GRAY)
                    fy = PAGE_H - MB + 8
                    page.draw_line(fitz.Point(ML, fy - 4), fitz.Point(PAGE_W - MR, fy - 4), color=(0.80, 0.88, 0.82), width=0.5)
                    _tx(page, "Piano indicativo. Consultare un nutrizionista per esigenze specifiche.", ML, fy + 6, fs=7, col=GRAY)
                    _tx(page, f"Pag. {si + 1}/{len(piano_dati)}", PAGE_W - MR - 40, fy + 6, fs=7, col=GRAY)
            if peso_storico:
                page = doc.new_page(width=PAGE_W, height=PAGE_H)
                cy = MT
                _tx(page, "Monitoraggio Peso", ML, cy, fs=15, col=GREEN, bold=True)
                cy += 18
                page.draw_line(fitz.Point(ML, cy), fitz.Point(PAGE_W - MR, cy),
                               color=GREEN, width=1.0)
                cy += 14
                _dr(page, ML, cy, PAGE_W - ML - MR, 22, fill=GREEN_LITE, stroke=GRAY, lw=0.3)
                _tx(page, info_fisico, ML + 8, cy + 15, fs=8.5, col=BLACK, bold=True)
                cy += 32
                CW_P = [90, 70, 70, 80]
                HDR_P = ["Data", "Peso kg", "Variaz.", "BMI"]
                tw_p = sum(CW_P)
                _dr(page, ML, cy, tw_p, 18, fill=GREEN2)
                xc = ML
                for h2, w2 in zip(HDR_P, CW_P):
                    _tx(page, h2, xc + 2, cy + 12, fs=8, col=WHITE, bold=True,
                        cw=w2 - 2, center=True)
                    xc += w2
                cy += 18
                for i, r in enumerate(peso_storico):
                    fill = ROW_ALT if i % 2 == 0 else WHITE
                    _dr(page, ML, cy, tw_p, 18, fill=fill, stroke=(0.80, 0.88, 0.82))
                    xc = ML
                    var_str = "—"
                    var_col = BLACK
                    if i > 0:
                        diff = round(r["peso"] - peso_storico[i-1]["peso"], 1)
                        var_str = f"{'+' if diff >= 0 else ''}{diff}"
                        var_col = (0.8, 0.3, 0.0) if diff > 0 else (0.1, 0.5, 0.1)
                    bmi_r = "—"
                    try:
                        h_cm = float(altezza.replace(",", ".")) / 100
                        if h_cm > 0:
                            bmi_r = str(round(r["peso"] / (h_cm * h_cm), 1))
                    except: pass
                    vals_p = [r["data"], str(r["peso"]), var_str, bmi_r]
                    for vi, (val, w2) in enumerate(zip(vals_p, CW_P)):
                        col = var_col if vi == 2 else BLACK
                        _tx(page, val, xc + 2, cy + 13, fs=8,
                            col=col, cw=w2 - 2, center=True)
                        xc += w2
                    cy += 18
                cy += 10
                pesi = [r["peso"] for r in peso_storico]
                delta = round(pesi[-1] - pesi[0], 1)
                delta_str = f"{'+' if delta >= 0 else ''}{delta}"
                stats_txt = (f"Pesate: {len(pesi)}   |   "
                             f"Min: {min(pesi)} kg   |   "
                             f"Max: {max(pesi)} kg   |   "
                             f"Media: {round(sum(pesi)/len(pesi),1)} kg   |   "
                             f"Variazione totale: {delta_str} kg")
                _dr(page, ML, cy, PAGE_W - ML - MR, 20, fill=GREEN_LITE, stroke=GREEN2, lw=0.5)
                _tx(page, stats_txt, ML + 8, cy + 14, fs=8, col=GREEN, bold=True)
                cy += 30
                try:
                    ob = float(obiettivo.replace(",", "."))
                    dist = round(pesi[-1] - ob, 1)
                    dist_str = (f"Distanza dall'obiettivo: {'+' if dist >= 0 else ''}{dist} kg"
                                f"  ({'da perdere' if dist > 0 else 'obiettivo raggiunto!'})")
                    _tx(page, dist_str, ML, cy, fs=9, col=GREEN2, bold=True)
                    cy += 16
                except: pass
                fy = PAGE_H - MB + 8
                page.draw_line(fitz.Point(ML, fy - 4), fitz.Point(PAGE_W - MR, fy - 4),
                               color=(0.80, 0.88, 0.82), width=0.5)
                _tx(page, "Piano indicativo. Consultare un nutrizionista per esigenze specifiche.",
                    ML, fy + 6, fs=7, col=GRAY)
                _tx(page, f"Pag. {len(piano_dati) + 1}/{len(piano_dati) + 1}",
                    PAGE_W - MR - 40, fy + 6, fs=7, col=GRAY)
            try:
                s = inputs["Sesso"].get()
                p = float(inputs["Peso (kg)"].get().replace(',', '.'))
                a = float(inputs["Altezza (cm)"].get().replace(',', '.'))
                e = int(inputs["Età"].get())
                if p > 0 and a > 0 and e > 0:
                    if s == "Uomo":
                        bmr = (10 * p) + (6.25 * a) - (5 * e) + 5
                    else:
                        bmr = (10 * p) + (6.25 * a) - (5 * e) - 161
                    fabbisogni = {
                        "Sedentario (Ufficio)":    round(bmr * 1.2),
                        "Leggero (Attività 1-2v)": round(bmr * 1.375),
                        "Moderato (Sport 3-5v)":   round(bmr * 1.55),
                        "Attivo (Lavoro Fisico)":  round(bmr * 1.725),
                    }
                    page = doc.new_page(width=PAGE_W, height=PAGE_H)
                    cy = MT
                    _tx(page, "Fabbisogno Calorico", ML, cy, fs=15, col=GREEN, bold=True)
                    cy += 18
                    page.draw_line(fitz.Point(ML, cy), fitz.Point(PAGE_W - MR, cy),
                                   color=GREEN, width=1.0)
                    cy += 14
                    _dr(page, ML, cy, PAGE_W - ML - MR, 22, fill=GREEN_LITE, stroke=GRAY, lw=0.3)
                    _tx(page,
                        f"Sesso: {s}   |   Peso: {p} kg   |   Altezza: {a} cm   |   Età: {e} anni   |   BMI: {bmi_txt}",
                        ML + 8, cy + 15, fs=8.5, col=BLACK, bold=True)
                    cy += 32
                    _dr(page, ML, cy, PAGE_W - ML - MR, 22, fill=GREEN2)
                    _tx(page, f"Metabolismo Basale (BMR): {round(bmr)} kcal/giorno",
                        ML + 8, cy + 15, fs=10, col=WHITE, bold=True)
                    cy += 32
                    tw_f = PAGE_W - ML - MR
                    for i2, (desc, kcal) in enumerate(fabbisogni.items()):
                        fill = ROW_ALT if i2 % 2 == 0 else WHITE
                        _dr(page, ML, cy, tw_f, 20, fill=fill, stroke=(0.80, 0.88, 0.82))
                        _tx(page, f"Fabbisogno: {desc}", ML + 8, cy + 14, fs=9)
                        _tx(page, f"{kcal} kcal", PAGE_W - MR - 60, cy + 14, fs=9, bold=True)
                        cy += 20
                    cy += 16
                    base_kcal = fabbisogni["Moderato (Sport 3-5v)"]
                    obiettivi_cal = [
                        ("Per perdere peso (Deficit 15%)", round(base_kcal * 0.85), (0.8, 0.2, 0.2)),
                        ("Per mantenere il peso attuale",  base_kcal,                (0.1, 0.4, 0.8)),
                        ("Per aumentare massa (+10%)",     round(base_kcal * 1.10),  (0.1, 0.6, 0.2)),
                    ]
                    _tx(page, "Obiettivi Consigliati", ML, cy, fs=10, col=GREEN2, bold=True)
                    cy += 14
                    for desc, kcal, col2 in obiettivi_cal:
                        _dr(page, ML, cy, tw_f, 20, fill=GREEN_LITE, stroke=(0.80, 0.88, 0.82))
                        _tx(page, desc, ML + 8, cy + 14, fs=9)
                        _tx(page, f"{kcal} kcal", PAGE_W - MR - 60, cy + 14,
                            fs=9, col=col2, bold=True)
                        cy += 20
                    cy += 16
                    medie_piano = []
                    for sett in piano_dati:
                        giorni = sett["giorni"]
                        n = len(giorni)
                        if n:
                            medie_piano.append(round(sum(r[5] for r in giorni if len(r) > 5) / n))
                    if medie_piano:
                        media_dieta = round(sum(medie_piano) / len(medie_piano))
                        delta_kcal  = media_dieta - base_kcal
                        delta_str2  = f"{'+' if delta_kcal >= 0 else ''}{delta_kcal}"
                        _dr(page, ML, cy, tw_f, 24, fill=GREEN_LITE, stroke=GREEN2, lw=0.5)
                        _tx(page,
                            f"Media piano dieta: {media_dieta} kcal/giorno   |   "
                            f"Differenza vs mantenimento: {delta_str2} kcal",
                            ML + 8, cy + 16, fs=9, col=GREEN, bold=True)
                        cy += 30
                    tot_pag = len(piano_dati) + (2 if peso_storico else 1)
                    fy2 = PAGE_H - MB + 8
                    page.draw_line(fitz.Point(ML, fy2 - 4), fitz.Point(PAGE_W - MR, fy2 - 4),
                                   color=(0.80, 0.88, 0.82), width=0.5)
                    _tx(page, "Piano indicativo. Consultare un nutrizionista per esigenze specifiche.",
                        ML, fy2 + 6, fs=7, col=GRAY)
                    _tx(page, f"Pag. {tot_pag}/{tot_pag}",
                        PAGE_W - MR - 40, fy2 + 6, fs=7, col=GRAY)
            except Exception:
                pass
            try:
                ped_dati, _ = _carica_pedometro()
                if ped_dati:
                    BLUE       = (0.07, 0.34, 0.56)
                    BLUE2      = (0.18, 0.47, 0.70)
                    BLUE_LITE  = (0.93, 0.96, 0.99)
                    oggi_d     = datetime.date.today()
                    n_pag_tot  = len(piano_dati) + (1 if peso_storico else 0) + 1
                    try:
                        p2 = float(inputs["Peso (kg)"].get().replace(",", "."))
                        a2 = float(inputs["Altezza (cm)"].get().replace(",", "."))
                        e2 = int(inputs["Età"].get())
                        if p2 > 0 and a2 > 0 and e2 > 0:
                            n_pag_tot += 1
                    except Exception:
                        pass
                    n_pag_ped = n_pag_tot
                    page = doc.new_page(width=PAGE_W, height=PAGE_H)
                    cy = MT
                    _tx(page, "Storico Passi", ML, cy, fs=15, col=BLUE, bold=True)
                    cy += 18
                    page.draw_line(fitz.Point(ML, cy), fitz.Point(PAGE_W - MR, cy),
                                   color=BLUE, width=1.0)
                    cy += 14
                    voci_ordinate = sorted(
                        ped_dati.items(),
                        key=lambda x: datetime.datetime.strptime(x[0], "%d-%m-%Y").date()
                    )
                    vals_p = [int(r.get("passi", 0)) for _, r in voci_ordinate]
                    obs_p  = [int(r.get("obiettivo", 10000)) for _, r in voci_ordinate]
                    giorni_ok = sum(1 for v, o in zip(vals_p, obs_p) if v >= o)
                    media30 = [v for (ds, _), v in zip(voci_ordinate, vals_p)
                               if 0 <= (oggi_d - datetime.datetime.strptime(ds, "%d-%m-%Y").date()).days < 30]
                    riepilogo = (
                        f"Giorni registrati: {len(vals_p)}   |   "
                        f"Record: {max(vals_p):,} passi   |   "
                        f"Media (30gg): {round(sum(media30)/len(media30)):,}" if media30 else
                        f"Giorni registrati: {len(vals_p)}   |   "
                        f"Record: {max(vals_p):,} passi"
                    )
                    riepilogo += f"   |   Giorni obiettivo raggiunto: {giorni_ok}/{len(vals_p)}"
                    _dr(page, ML, cy, PAGE_W - ML - MR, 22, fill=BLUE_LITE, stroke=GRAY, lw=0.3)
                    _tx(page, riepilogo, ML + 8, cy + 15, fs=8.5, col=BLACK, bold=True)
                    cy += 32
                    CW_PED = [80, 65, 70, 45, 100, PAGE_W - ML - MR - 80 - 65 - 70 - 45 - 100]
                    HDR_PED = ["Data", "Passi", "Obiettivo", "%", "Esito", "Note"]
                    tw_ped = sum(CW_PED)
                    _dr(page, ML, cy, tw_ped, 18, fill=BLUE2)
                    xc = ML
                    for h3, w3 in zip(HDR_PED, CW_PED):
                        _tx(page, h3, xc + 2, cy + 12, fs=8, col=WHITE, bold=True,
                            cw=w3 - 2, center=True)
                        xc += w3
                    cy += 18
                    RH_PED = 16
                    for i, (data_str, rec) in enumerate(voci_ordinate):
                        if cy + RH_PED > PAGE_H - MB - 20:
                            fy3 = PAGE_H - MB + 8
                            page.draw_line(fitz.Point(ML, fy3 - 4), fitz.Point(PAGE_W - MR, fy3 - 4),
                                           color=(0.80, 0.88, 0.95), width=0.5)
                            _tx(page, "Piano indicativo. Consultare un nutrizionista per esigenze specifiche.",
                                ML, fy3 + 6, fs=7, col=GRAY)
                            page = doc.new_page(width=PAGE_W, height=PAGE_H)
                            cy = MT
                            _tx(page, "Storico Passi (continua)", ML, cy, fs=13, col=BLUE, bold=True)
                            cy += 22
                            _dr(page, ML, cy, tw_ped, 18, fill=BLUE2)
                            xc = ML
                            for h3, w3 in zip(HDR_PED, CW_PED):
                                _tx(page, h3, xc + 2, cy + 12, fs=8, col=WHITE, bold=True,
                                    cw=w3 - 2, center=True)
                                xc += w3
                            cy += 18
                        p_val  = int(rec.get("passi", 0))
                        ob_val = int(rec.get("obiettivo", 10000))
                        pct    = round(p_val / ob_val * 100) if ob_val > 0 else 0
                        esito  = "✓ Raggiunto" if p_val >= ob_val else "✗ Mancato"
                        col_e  = (0.10, 0.42, 0.18) if p_val >= ob_val else (0.75, 0.20, 0.10)
                        fill   = BLUE_LITE if i % 2 == 0 else WHITE
                        _dr(page, ML, cy, tw_ped, RH_PED, fill=fill, stroke=(0.75, 0.88, 0.95))
                        xc = ML
                        vals_ped = [data_str, f"{p_val:,}", f"{ob_val:,}", f"{pct}%", esito, rec.get("note","")]
                        for vi, (val, w3) in enumerate(zip(vals_ped, CW_PED)):
                            col_t = col_e if vi == 4 else BLACK
                            _tx(page, val, xc + 2, cy + 11, fs=7.5,
                                col=col_t, cw=w3 - 2,
                                center=(vi != 5))
                            xc += w3
                        cy += RH_PED
                    cy += 8
                    _dr(page, ML, cy, tw_ped, 20, fill=BLUE_LITE, stroke=BLUE2, lw=0.5)
                    stats_ped = (
                        f"Totale passi: {sum(vals_p):,}   |   "
                        f"Media giornaliera: {round(sum(vals_p)/len(vals_p)):,}   |   "
                        f"Record: {max(vals_p):,}   |   "
                        f"Giorni obiettivo: {giorni_ok}/{len(vals_p)}"
                    )
                    _tx(page, stats_ped, ML + 8, cy + 14, fs=8, col=BLUE, bold=True)
                    cy += 28
                    fy_ped = PAGE_H - MB + 8
                    page.draw_line(fitz.Point(ML, fy_ped - 4), fitz.Point(PAGE_W - MR, fy_ped - 4),
                                   color=(0.80, 0.88, 0.95), width=0.5)
                    _tx(page, "Piano indicativo. Consultare un nutrizionista per esigenze specifiche.",
                        ML, fy_ped + 6, fs=7, col=GRAY)
                    _tx(page, f"Pag. {n_pag_ped}/{n_pag_ped}",
                        PAGE_W - MR - 40, fy_ped + 6, fs=7, col=GRAY)
            except Exception:
                pass
            doc.save(dest)
            doc.close()
            return dest
        except Exception as e:
            self.show_custom_warning("Errore PDF", str(e))
            return None
    def _esporta_pdf():
        path = _genera_pdf()
        if path:
            self.show_toast(f"PDF salvato: {os.path.basename(path)}")
    def _stampa():
        import tempfile as _tmp
        tmp = os.path.join(_tmp.gettempdir(), "dieta_stampa.pdf")
        dest = _genera_pdf(dest=tmp)
        if dest:
            self.stampa_pdf(dest, self.show_custom_warning)
    def _consulta_ai():
        if not API_KEY:
            self.show_custom_warning("AI non configurata",
                "Inserisci la chiave API Gemini in Sistema → Impostazioni App.")
            return
        idx_sett = nb.index(nb.select()) if nb.tabs() else -1
        if idx_sett < 0 or idx_sett >= len(piano_dati):
            self.show_custom_warning("Nessun piano selezionato",
                "Seleziona una scheda Settimana prima di consultare l'AI.")
            return
        sett = piano_dati[idx_sett]
        righe_txt = "\n".join(
            f"  {r[0]}: col={r[1]} | pranzo={r[2]} | cena={r[3]} | spunt={r[4]} | "
            f"{r[5]}kcal / {r[6]}g prot / {r[7]}g grassi / {r[8]}g carb / {r[9]}g zucc / {r[10]}g fibre"
            for r in sett["giorni"] if len(r) >= 11
        )
        prompt = (f"Analizza il piano alimentare settimanale mediterraneo e fornisci:\n"
                  f"1. VALUTAZIONE NUTRIZIONALE: equilibrio macronutrienti e calorie.\n"
                  f"2. PUNTI DI FORZA: aspetti positivi.\n"
                  f"3. MIGLIORAMENTI: 2-3 modifiche concrete.\n"
                  f"4. CONSIGLI PRATICI: porzioni, orari, idratazione.\n\n"
                  f"PIANO - {sett['titolo']}:\n{righe_txt}\n\n"
                  f"REGOLE: no Markdown (*, #), titoli in MAIUSCOLO, italiano conciso.")
        splash = tk.Toplevel(self, bg=self.COLOR_WIDGET_BG)
        splash.withdraw()
        splash.overrideredirect(True)
        splash.attributes('-topmost', True)
        w2, h2 = 320, 70
        sx = self.winfo_rootx() + self.winfo_width()  // 2 - w2 // 2
        sy = self.winfo_rooty() + self.winfo_height() // 2 - h2 // 2
        splash.geometry(f"{w2}x{h2}+{sx}+{sy}")
        fr_s = tk.Frame(splash, bg=self.COLOR_WIDGET_BG, bd=0,
                        highlightbackground=self.COLOR_HIGHLIGHT, highlightthickness=1)
        fr_s.pack(expand=True, fill='both')
        inner = tk.Frame(fr_s, bg=self.COLOR_WIDGET_BG)
        inner.pack(expand=True)
        cvs, _ = crea_spinner_animato(inner, self.COLOR_WIDGET_BG, size=28, tick_ms=30)
        cvs.pack(side="left", padx=(0,8))
        tk.Label(inner, text="Analisi AI in corso...", font=("Segoe UI",9,"bold"),
                 bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HIGHLIGHT).pack(side="left")
        splash.deiconify()
        splash.update()
        def _mostra_risposta(testo):
            if splash.winfo_exists(): splash.destroy()
            ai_pop = tk.Toplevel(self, bg=self.COLOR_WIDGET_BG)
            ai_pop.withdraw()
            ai_pop.title(f"Consulenza AI — {sett['titolo']}")
            ai_pop.transient(self)
            ai_pop.bind("<Escape>", lambda e: ai_pop.destroy())
            ttk.Label(ai_pop, text=f"🤖 Analisi Nutrizionale — {sett['titolo']}",
                      font=("Arial", 11, "bold"),
                      background=self.COLOR_WIDGET_BG,
                      foreground=self.COLOR_HIGHLIGHT).pack(pady=(12, 4), side="top")
            bf2 = tk.Frame(ai_pop, bg=self.COLOR_WIDGET_BG)
            bf2.pack(side="bottom", fill="x", pady=(10, 15))
            img_c = self.icone_gui.get("chiudi")
            btn_c = ttk.Label(bf2, text=" Chiudi", image=img_c, compound="left",
                              background=self.COLOR_WIDGET_BG, 
                              foreground=self.TEXT_COLOR,
                              cursor="hand2", font=("Arial", 10, "bold"))
            btn_c.pack(anchor="center")
            btn_c.bind("<Button-1>", lambda e: ai_pop.destroy())
            cont = tk.Frame(ai_pop, bg=self.COLOR_WIDGET_BG)
            cont.pack(fill="both", expand=True, padx=15, pady=5)
            vsb2 = ttk.Scrollbar(cont, orient="vertical", style="Vertical.TScrollbar")
            vsb2.pack(side="right", fill="y")
            txt = tk.Text(cont, bg=self.COLOR_WHITE, fg=self.COLOR_BLACK,
                          font=("Consolas", 10), wrap="word", padx=20, pady=15,
                          borderwidth=0, yscrollcommand=vsb2.set, spacing1=5,
                          height=15)
            txt.pack(fill="both", expand=True)
            vsb2.config(command=txt.yview)
            txt.insert("1.0", testo)
            txt.config(state="disabled")
            W_POP, H_POP = 1000, 600 
            x3 = self.winfo_rootx() + (self.winfo_width() // 2) - (W_POP // 2)
            y3 = self.winfo_rooty() + (self.winfo_height() // 2) - (H_POP // 2)
            ai_pop.geometry(f"{W_POP}x{H_POP}+{max(0, x3)}+{max(0, y3)}")
            ai_pop.deiconify()
            ai_pop.focus_set()
        def _run():
            try:
                client = genai_client.Client(api_key=API_KEY)
                resp   = client.models.generate_content(model=GEMINI, contents=prompt)
                testo  = resp.text if resp.text else "Nessuna risposta generata."
            except Exception as err:
                testo = f"ERRORE API:\n{str(err)}"
            self.after(0, lambda: _mostra_risposta(testo))
        threading.Thread(target=_run, daemon=True).start()
    COL_PIANO  = ("giorno","colazione","pranzo","cena","spuntino","kcal","prot","grassi","carb","zucc","fibre")
    COL_LABEL  = ("Giorno","Colazione","Pranzo","Cena","Spuntino","Kcal","Prot.g","Gras.g","Carb.g","Zucc.g","Fibre g")
    COL_W_TV   = (140, 200, 200, 200, 100, 10, 10, 10, 10, 10, 10)
    PASTO_COLS = {1:"colazione", 2:"pranzo", 3:"cena", 4:"spuntino"}
    trees = []
    def _popola_tree(tree, s_idx):
        tree.delete(*tree.get_children())
        for riga in piano_dati[s_idx]["giorni"]:
            r = list(riga) + [0]*(11-len(riga))
            tree.insert("", "end", values=tuple(r[:11]))
        if trees_footer:
            _aggiorna_footer(s_idx)
    def _aggiorna_footer(s_idx):
        tree_foot = trees_footer[s_idx]
        tree_foot.delete(*tree_foot.get_children())
        giorni = piano_dati[s_idx]["giorni"]
        n = len(giorni)
        if n == 0:
            return
        tot  = [sum(r[i] for r in giorni if len(r) > i) for i in range(5, 11)]
        med  = [round(v / n) for v in tot]
        vuoto = ("", "", "", "")
        tree_foot.insert("", "end",
            values=("TOTALE SETTIMANA", *vuoto, *tot),
            tags=("totale",))
        tree_foot.insert("", "end",
            values=("MEDIA GIORNO", *vuoto, *med),
            tags=("media",))
        tree_foot.tag_configure("totale",
            foreground=self.COLOR_HIGHLIGHT,
            font=("Arial", 8, "bold"))
        tree_foot.tag_configure("media",
            foreground=self.COLOR_ORANGE,
            font=("Arial", 8))
    def _ricarica_settimane():
        for i, t in enumerate(trees):
            _popola_tree(t, i)
    def _ricalcola_totali_riga(s_idx, g_idx):
        riga = piano_dati[s_idx]["giorni"][g_idx]
        tot = [0.0] * 6
        for pk in ("colazione","pranzo","cena","spuntino"):
            chiave = f"{s_idx}_{g_idx}_{pk}"
            items  = composizioni.get(chiave, [])
            for item in items:
                for ti in range(6):
                    tot[ti] += item[2+ti]
        for ti, val in enumerate(tot):
            riga[5+ti] = round(val)
    def _apri_composizione(s_idx, g_idx, pasto_key):
        giorno_nome = piano_dati[s_idx]["giorni"][g_idx][0]
        pasto_label = {"colazione":"Colazione","pranzo":"Pranzo",
                       "cena":"Cena","spuntino":"Spuntino"}[pasto_key]
        chiave = f"{s_idx}_{g_idx}_{pasto_key}"
        items = [list(x) for x in composizioni.get(chiave, [])]
        cp = tk.Toplevel(popup)
        cp.title(f"{giorno_nome} — {pasto_label} ({piano_dati[s_idx]['titolo']})")
        cp.resizable(True, True)
        cp.transient(popup)
        cp.configure(bg=self.COLOR_WIDGET_BG)
        cp.bind("<Escape>", lambda e: cp.destroy())
        ttk.Label(cp, text=f"🍽️  {giorno_nome} — {pasto_label}",
                  font=("Arial",11,"bold"),
                  background=self.COLOR_WIDGET_BG,
                  foreground=self.COLOR_HIGHLIGHT).pack(pady=(10,4), padx=10, anchor="w")
        main_fr = tk.Frame(cp, bg=self.COLOR_WIDGET_BG)
        main_fr.pack(fill="both", expand=True, padx=8, pady=(0,4))
        left = tk.Frame(main_fr, bg=self.COLOR_WIDGET_BG)
        left.pack(side="left", fill="both", expand=True, padx=(0,6))
        tk.Label(left, text="Alimento:", font=("Arial",8,"bold"),
                 bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR).pack(anchor="w")
        flt_fr = tk.Frame(left, bg=self.COLOR_WIDGET_BG)
        flt_fr.pack(fill="x", pady=(2,4))
        srch_v = tk.StringVar()
        cat_v  = tk.StringVar(value="Tutte")
        ttk.Entry(flt_fr, textvariable=srch_v, width=18).pack(side="left", padx=(0,4))
        ttk.Combobox(flt_fr, values=_categorie, textvariable=cat_v,
                     state="readonly", width=12, style="Border.TCombobox").pack(side="left")
        vsb_l = ttk.Scrollbar(left, orient="vertical", style="Vertical.TScrollbar")
        vsb_l.pack(side="right", fill="y")
        tr_ali = ttk.Treeview(left,
                              columns=("nome","kcal","prot","grassi","carb","zucc","fibre"),
                              show="headings", yscrollcommand=vsb_l.set,
                              style="Treeview", height=13, selectmode='browse')
        vsb_l.config(command=tr_ali.yview)
        tr_ali.pack(fill="both", expand=True)
        for col, lbl, w in [("nome","Alimento",160),("kcal","Kcal",48),
                 ("prot","Prot.",44),("grassi","Gras.",44),
                 ("carb","Carb.",44),("zucc","Zucc.",44),("fibre","Fibre",44)]:
            tr_ali.heading(col, text=lbl,
               command=lambda _c=col: self.treeview_sort_column(tr_ali, _c, False))
            tr_ali.column(col, width=w, minwidth=30,
              anchor="w" if col=="nome" else "center")
        def _flt(*_):
            q   = srch_v.get().lower().strip()
            cat = cat_v.get()
            tr_ali.delete(*tr_ali.get_children())
            for row in ALIMENTI_ORDINATI:
                if cat != "Tutte" and row[1] != cat: continue
                if q and q not in row[0].lower(): continue
                tr_ali.insert("", "end", values=(row[0],row[2],row[3],row[4],row[5],row[6],row[7]))
        _flt()
        srch_v.trace_add("write", _flt)
        cat_v.trace_add("write",  _flt)
        gr_fr = tk.Frame(left, bg=self.COLOR_WIDGET_BG)
        gr_fr.pack(fill="x", pady=4)
        tk.Label(gr_fr, text="Grammi:", bg=self.COLOR_WIDGET_BG,
                 fg=self.TEXT_COLOR, font=("Arial",9)).pack(side="left")
        gr_v = tk.StringVar(value="100")
        tk.Entry(gr_fr, textvariable=gr_v, width=7, justify="center",
                 bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                 insertbackground=self.TEXT_COLOR,
                 highlightthickness=1,
                 highlightbackground=self.COLOR_HIGHLIGHT).pack(side="left", padx=6)
        right = tk.Frame(main_fr, bg=self.COLOR_WIDGET_BG)
        right.pack(side="left", fill="both", expand=True)
        tk.Label(right, text="Composizione pasto:", font=("Arial",8,"bold"),
                 bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR).pack(anchor="w")
        vsb_r = ttk.Scrollbar(right, orient="vertical", style="Vertical.TScrollbar")
        vsb_r.pack(side="right", fill="y")
        tr_cp = ttk.Treeview(right,
                             columns=("nome","g","kcal","prot","grassi","carb","zucc","fibre"),
                             show="headings", yscrollcommand=vsb_r.set,
                             style="Treeview", height=13, selectmode='browse')
        vsb_r.config(command=tr_cp.yview)
        tr_cp.pack(fill="both", expand=True)
        for col, lbl, w in [("nome","Alimento",145),("g","g",38),
                 ("kcal","Kcal",45),("prot","Prot.",43),
                 ("grassi","Gras.",43),("carb","Carb.",43),
                 ("zucc","Zucc.",43),("fibre","Fibre",43)]:
            tr_cp.heading(col, text=lbl,
              command=lambda _c=col: self.treeview_sort_column(tr_cp, _c, False))
            tr_cp.column(col, width=w, minwidth=28,
             anchor="w" if col=="nome" else "center")
        tot_fr = tk.Frame(right, bg=self.COLOR_WIDGET_BG,
                          highlightthickness=1, highlightbackground=self.COLOR_HIGHLIGHT)
        tot_fr.pack(fill="x", pady=(5,2))
        lbl_vals = {}
        for k, txt in [("kcal","Kcal: —"),("prot","Prot.: —"),("grassi","Gras.: —"),
                        ("carb","Carb.: —"),("zucc","Zucc.: —"),("fibre","Fibre: —")]:
            bold = k=="kcal"
            l = tk.Label(tot_fr, text=txt,
                         font=("Arial",8,"bold" if bold else "normal"),
                         bg=self.COLOR_WIDGET_BG,
                         fg=self.COLOR_HIGHLIGHT if bold else self.TEXT_COLOR)
            l.pack(side="left", padx=8, pady=4)
            lbl_vals[k] = l
        def _aggiorna_tree_cp():
            tr_cp.delete(*tr_cp.get_children())
            for it in items:
                tr_cp.insert("", "end", values=tuple(it))
            if items:
                t = [round(sum(it[2+i] for it in items),1) for i in range(6)]
                lbl_vals["kcal"].config(  text=f"Kcal: {t[0]}")
                lbl_vals["prot"].config(  text=f"Prot.: {t[1]}g")
                lbl_vals["grassi"].config(text=f"Gras.: {t[2]}g")
                lbl_vals["carb"].config(  text=f"Carb.: {t[3]}g")
                lbl_vals["zucc"].config(  text=f"Zucc.: {t[4]}g")
                lbl_vals["fibre"].config( text=f"Fibre: {t[5]}g")
            else:
                for k, txt in [("kcal","Kcal: —"),("prot","Prot.: —"),("grassi","Gras.: —"),
                               ("carb","Carb.: —"),("zucc","Zucc.: —"),("fibre","Fibre: —")]:
                    lbl_vals[k].config(text=txt)
        _aggiorna_tree_cp()
        def _azzera_composizione():
            if not items:
                return
            if not self.show_custom_askyesno("Azzera", 
                f"Azzerare tutta la composizione di {pasto_label}?"):
                return
            items.clear()
            _aggiorna_tree_cp()
        def _aggiungi():
            sel = tr_ali.selection()
            if not sel: return
            nome_sel = tr_ali.item(sel[0], "values")[0]
            try:
                g = float(gr_v.get())
                if g <= 0: raise ValueError
            except ValueError:
                return
            row_db = _ali_map.get(nome_sel)
            if not row_db: return
            f = g / 100.0
            vals = [round(row_db[i]*f, 1) for i in range(2,8)]
            items.append([nome_sel, g] + vals)
            _aggiorna_tree_cp()
        def _rimuovi():
            sel = tr_cp.selection()
            if not sel: return
            idx = tr_cp.index(sel[0])
            if 0 <= idx < len(items):
                items.pop(idx)
                _aggiorna_tree_cp()
        def _salva_e_chiudi():
            composizioni[chiave] = [list(x) for x in items]
            riga = piano_dati[s_idx]["giorni"][g_idx]
            if items:
                nomi = ", ".join(it[0] for it in items)
                riga[{"colazione":1,"pranzo":2,"cena":3,"spuntino":4}[pasto_key]] = nomi
            _ricalcola_totali_riga(s_idx, g_idx)
            _popola_tree(trees[s_idx], s_idx)
            cp.destroy()
        tr_ali.bind("<Double-Button-1>", lambda e: _aggiungi())
        btn_fr = tk.Frame(right, bg=self.COLOR_WIDGET_BG)
        btn_fr.pack(fill="x", pady=(2,0))
        def _mk(parent, ico, txt, cmd, fg=None):
            img = self.icone_gui.get(ico)
            fg  = fg or self.TEXT_COLOR
            l   = ttk.Label(parent, text=f" {txt}", image=img, compound="left",
                            background=self.COLOR_WIDGET_BG, foreground=fg,
                            cursor="hand2", font=("Arial",9,"bold"), padding=(4,2))
            if img: l.image = img
            l.pack(side="left", padx=4)
            l.bind("<Button-1>", lambda e: cmd())
            return l
        _mk(btn_fr, "aggiungi",    "Aggiungi", _aggiungi,       "#98C379")
        _mk(btn_fr, "delete", "Rimuovi",  _rimuovi,        self.COLOR_ORANGE)
        _mk(btn_fr, "reset",  "Azzera",   _azzera_composizione, self.COLOR_ORANGE)
        bot_fr = tk.Frame(cp, bg=self.COLOR_WIDGET_BG,
                          highlightthickness=1, highlightbackground=self.COLOR_HIGHLIGHT)
        bot_fr.pack(fill="x", padx=8, pady=(0,8))
        _mk(bot_fr, "check",  "Salva e chiudi", _salva_e_chiudi, "#98C379")
        _mk(bot_fr, "chiudi", "Annulla",         lambda: cp.destroy())
        cp.update_idletasks()
        w2 = 1200; h2 = 560
        x2 = popup.winfo_x() + popup.winfo_width()//2  - w2//2
        y2 = popup.winfo_y() + popup.winfo_height()//2 - h2//2
        cp.geometry(f"{w2}x{h2}+{x2}+{y2}")
        cp.grab_set()
        cp.focus_force()
    def _on_double_click(event, s_idx):
        tree = trees[s_idx]
        if tree.identify_region(event.x, event.y) != "cell": return
        col_id = tree.identify_column(event.x)
        row_id = tree.identify_row(event.y)
        if not row_id: return
        col_num = int(col_id.replace("#","")) - 1
        if col_num not in PASTO_COLS: return
        g_idx     = tree.index(row_id)
        pasto_key = PASTO_COLS[col_num]
        _apri_composizione(s_idx, g_idx, pasto_key)
    def _copia_giorno(s_idx_src, g_idx_src):
        riga_src  = piano_dati[s_idx_src]["giorni"][g_idx_src]
        giorno_nome = riga_src[0]
        cp = tk.Toplevel(popup)
        cp.title("Copia giorno")
        cp.resizable(False, False)
        cp.transient(popup)
        cp.configure(bg=self.COLOR_WIDGET_BG)
        cp.bind("<Escape>", lambda e: cp.destroy())
        ttk.Label(cp,
                  text=f"Copia  '{giorno_nome}'  ({piano_dati[s_idx_src]['titolo']})",
                  font=("Arial", 10, "bold"),
                  background=self.COLOR_WIDGET_BG,
                  foreground=self.COLOR_HIGHLIGHT).pack(padx=16, pady=(12, 6))
        ttk.Label(cp, text="Settimana di destinazione:",
                  background=self.COLOR_WIDGET_BG,
                  foreground=self.TEXT_COLOR,
                  font=("Arial", 9)).pack(padx=16, anchor="w")
        sett_nomi = [s["titolo"] for s in piano_dati]
        sett_v = tk.StringVar(value=sett_nomi[s_idx_src])
        cb_sett = ttk.Combobox(cp, values=sett_nomi, textvariable=sett_v,
                               state="readonly", width=22,
                               style="Border.TCombobox")
        cb_sett.pack(padx=16, pady=(2, 10))
        ttk.Label(cp, text="Giorno di destinazione:",
                  background=self.COLOR_WIDGET_BG,
                  foreground=self.TEXT_COLOR,
                  font=("Arial", 9)).pack(padx=16, anchor="w")
        giorni_nomi = [r[0] for r in piano_dati[s_idx_src]["giorni"]]
        giorno_v = tk.StringVar(value=giorno_nome)
        def _aggiorna_giorni(*_):
            idx = sett_nomi.index(sett_v.get())
            nomi = [r[0] for r in piano_dati[idx]["giorni"]]
            cb_giorno["values"] = nomi
            if giorno_v.get() not in nomi:
                giorno_v.set(nomi[0])
        cb_giorno = ttk.Combobox(cp, values=giorni_nomi, textvariable=giorno_v,
                                 state="readonly", width=22,
                                 style="Border.TCombobox")
        cb_giorno.pack(padx=16, pady=(2, 6))
        sett_v.trace_add("write", _aggiorna_giorni)
        def _esegui():
            s_idx_dst = sett_nomi.index(sett_v.get())
            g_idx_dst = [r[0] for r in piano_dati[s_idx_dst]["giorni"]].index(giorno_v.get())
            if s_idx_src == s_idx_dst and g_idx_src == g_idx_dst:
                self.show_custom_warning("Attenzione",
                    "Sorgente e destinazione sono lo stesso giorno.")
                return
            nome_dst  = piano_dati[s_idx_dst]["giorni"][g_idx_dst][0]
            nuova_riga = [nome_dst] + list(riga_src[1:])
            piano_dati[s_idx_dst]["giorni"][g_idx_dst] = nuova_riga
            for pk in ("colazione", "pranzo", "cena", "spuntino"):
                chiave_src = f"{s_idx_src}_{g_idx_src}_{pk}"
                chiave_dst = f"{s_idx_dst}_{g_idx_dst}_{pk}"
                if chiave_src in composizioni:
                    composizioni[chiave_dst] = [list(x) for x in composizioni[chiave_src]]
                else:
                    composizioni.pop(chiave_dst, None)
            _popola_tree(trees[s_idx_dst], s_idx_dst)
            cp.destroy()
            self.show_toast(
                f"'{giorno_nome}' copiato in "
                f"{piano_dati[s_idx_dst]['titolo']} → {nome_dst}."
            )
        bot = tk.Frame(cp, bg=self.COLOR_WIDGET_BG)
        bot.pack(pady=(4, 14))
        def _mk(parent, ico, txt, cmd, fg=None):
            img = self.icone_gui.get(ico)
            fg  = fg or self.TEXT_COLOR
            l   = ttk.Label(parent, text=f" {txt}", image=img, compound="left",
                            background=self.COLOR_WIDGET_BG, foreground=fg,
                            cursor="hand2", font=("Arial", 9, "bold"), padding=(6, 2))
            if img: l.image = img
            l.pack(side="left", padx=6)
            l.bind("<Button-1>", lambda e: cmd())
        _mk(bot, "check",  "Copia",   _esegui,    "#98C379")
        _mk(bot, "chiudi", "Annulla", cp.destroy)
        cp.update_idletasks()
        w2, h2 = 340, 220
        x2 = popup.winfo_x() + popup.winfo_width()  // 2 - w2 // 2
        y2 = popup.winfo_y() + popup.winfo_height() // 2 - h2 // 2
        cp.geometry(f"{w2}x{h2}+{x2}+{y2}")
        cp.grab_set()
        cp.focus_force()
    def _azzera_giorno(s_idx, g_idx):
            riga = piano_dati[s_idx]["giorni"][g_idx]
            nome = riga[0]
            if not self.show_custom_askyesno("Azzera", f"Azzerare tutti i pasti di {nome}?"):
                return
            for i in range(1, 5):
                riga[i] = ""
            for i in range(5, 11):
                 riga[i] = 0
            for pk in ("colazione", "pranzo", "cena", "spuntino"):
                composizioni.pop(f"{s_idx}_{g_idx}_{pk}", None)
            _popola_tree(trees[s_idx], s_idx)
    def _on_right_click(event, s_idx):
        tree = trees[s_idx]
        row_id = tree.identify_row(event.y)
        if not row_id:
            return
        tree.selection_set(row_id)
        g_idx = tree.index(row_id)
        m = tk.Menu(popup, tearoff=0,
            bg=self.MENU_BG,
            fg=self.MENU_FG_LIGHT,
            activebackground=self.MENU_ACT_BG_COLOR,
            activeforeground=self.MENU_FG_LIGHT,
            font=("Arial", 9))
        img_copia  = self.icone_gui.get("report")
        img_azzera = self.icone_gui.get("delete")
        m.add_command(label="  Copia giorno in...",
              image=img_copia,  compound="left",
              command=lambda: _copia_giorno(s_idx, g_idx))
        m.add_separator()
        m.add_command(label="  Azzera giorno",
              image=img_azzera, compound="left",
              command=lambda: _azzera_giorno(s_idx, g_idx))
        m.tk_popup(event.x_root, event.y_root)
    piano_dati, composizioni = _carica_piano()
    popup = tk.Toplevel(self)
    self._dieta_popup = popup
    popup.title("Piano Dieta Mediterranea")
    popup.resizable(True, True)
    popup.withdraw()
    popup.transient(self)
    popup.protocol("WM_DELETE_WINDOW",
                   lambda: [popup.destroy(), setattr(self, '_dieta_popup', None)])
    popup.bind("<Escape>",
               lambda e: [popup.destroy(), setattr(self, '_dieta_popup', None)])
    nb = ttk.Notebook(popup)
    nb.pack(fill="both", expand=True, padx=10, pady=(10,0))
    def _add_tab(frame, ico_key, testo):
        img = self.icone_gui.get(ico_key)
        if img:
            nb.add(frame, image=img, text=f" {testo} ", compound="left")
        else:
            nb.add(frame, text=f" {testo} ")
    trees_footer = []
    for s_idx, sett in enumerate(piano_dati):
        frame = ttk.Frame(nb)
        _add_tab(frame, "calendario", sett['titolo'])
        vsb = ttk.Scrollbar(frame, orient="vertical", style="Vertical.TScrollbar")
        vsb.pack(side="right", fill="y")
        tree_foot = ttk.Treeview(frame, columns=COL_PIANO, show="headings",
                                 style="Treeview", height=2, selectmode='browse')
        tree_foot.pack(fill="x", side="bottom")
        for col, lbl, w in zip(COL_PIANO, COL_LABEL, COL_W_TV):
            tree_foot.heading(col, text="")
            anch = "w" if col in ("giorno","colazione","pranzo","cena","spuntino") else "center"
            tree_foot.column(col, width=w, minwidth=30, anchor=anch)
        tree = ttk.Treeview(frame, columns=COL_PIANO, show="headings",
                            yscrollcommand=vsb.set, style="Treeview", selectmode='browse')
        vsb.config(command=tree.yview)
        tree.pack(fill="both", expand=True)
        for col, lbl, w in zip(COL_PIANO, COL_LABEL, COL_W_TV):
            tree.heading(col, text=lbl)
            anch = "w" if col in ("giorno","colazione","pranzo","cena","spuntino") else "center"
            tree.column(col, width=w, minwidth=30, anchor=anch)
        tree.bind("<Double-Button-1>", lambda e, i=s_idx: _on_double_click(e, i))
        tree.bind("<Button-3>",        lambda e, i=s_idx: _on_right_click(e, i))
        trees.append(tree)
        trees_footer.append(tree_foot)
        _popola_tree(tree, s_idx)
    def _carica_peso():
        try:
            if os.path.exists(PESO_FILE):
                with open(PESO_FILE, 'r', encoding='utf-8') as f:
                    d = json.load(f)
                    if isinstance(d, list):
                        return d, "", ""
                    return d.get("pesate", []), d.get("altezza", ""), d.get("obiettivo", "")
        except Exception:
            pass
        return [], "", ""
    def _salva_peso():
        try:
            os.makedirs(DB_DIR, exist_ok=True)
            with open(PESO_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    "pesate":    peso_storico,
                    "altezza":   altezza_v.get().strip(),
                    "obiettivo": obiettivo_v.get().strip()
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.show_custom_warning("Errore", f"Salvataggio peso fallito:\n{e}")
    peso_storico, _alt_saved, _ob_saved = _carica_peso()
    tab_peso = tk.Frame(nb, bg=self.COLOR_WIDGET_BG)
    _add_tab(tab_peso, "grafico_linea", "Peso")
    fr_left  = tk.Frame(tab_peso, bg=self.COLOR_WIDGET_BG)
    fr_left.pack(side="left", fill="y", padx=(10,4), pady=8)
    fr_right = tk.Frame(tab_peso, bg=self.COLOR_WIDGET_BG)
    fr_right.pack(side="left", fill="both", expand=True, padx=(4,10), pady=8)
    fr_inp = tk.LabelFrame(fr_left, text=" Nuova pesata ",
                           bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HIGHLIGHT,
                           font=("Arial", 9, "bold"), padx=10, pady=8)
    fr_inp.pack(fill="x", pady=(0,8))
    tk.Label(fr_inp, text="Data:", bg=self.COLOR_WIDGET_BG,
             fg=self.TEXT_COLOR, font=("Arial", 9)).grid(row=0, column=0, sticky="e", pady=3)
    fr_data = tk.Frame(fr_inp, bg=self.COLOR_WIDGET_BG)
    fr_data.grid(row=0, column=1, padx=(6,0), pady=3, sticky="w")
    data_v = tk.StringVar(value=datetime.date.today().strftime("%d-%m-%Y"))
    entry_data_peso = tk.Entry(fr_data, textvariable=data_v, width=11,
             bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
             insertbackground=self.TEXT_COLOR,
             highlightthickness=1,
             highlightbackground=self.COLOR_HIGHLIGHT)
    entry_data_peso.pack(side="left")
    img_cal = self.icone_gui.get("calendario")
    btn_cal_peso = ttk.Label(fr_data, image=img_cal, compound="left",
                             background=self.COLOR_WIDGET_BG,
                             cursor="hand2", padding=(4,0))
    if img_cal: btn_cal_peso.image = img_cal
    btn_cal_peso.pack(side="left", padx=(4,0))
    btn_cal_peso.bind("<Button-1>",
        lambda e: self.mostra_calendario_popup_semplice(entry_data_peso, data_v))
    tk.Label(fr_inp, text="Peso (kg):", bg=self.COLOR_WIDGET_BG,
             fg=self.TEXT_COLOR, font=("Arial", 9)).grid(row=1, column=0, sticky="e", pady=3)
    peso_v = tk.StringVar()
    tk.Entry(fr_inp, textvariable=peso_v, width=8,
             bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
             insertbackground=self.TEXT_COLOR,
             highlightthickness=1,
             highlightbackground=self.COLOR_HIGHLIGHT).grid(row=1, column=1, padx=(6,0),
                                                            pady=3, sticky="w")
    tk.Label(fr_inp, text="Obiettivo (kg):", bg=self.COLOR_WIDGET_BG,
             fg=self.TEXT_COLOR, font=("Arial", 9)).grid(row=2, column=0, sticky="e", pady=3)
    obiettivo_v = tk.StringVar()
    tk.Entry(fr_inp, textvariable=obiettivo_v, width=8,
             bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
             insertbackground=self.TEXT_COLOR,
             highlightthickness=1,
             highlightbackground=self.COLOR_HIGHLIGHT).grid(row=2, column=1, padx=(6,0),
                                                            pady=3, sticky="w")
    tk.Label(fr_inp, text="Altezza (cm):", bg=self.COLOR_WIDGET_BG,
             fg=self.TEXT_COLOR, font=("Arial", 9)).grid(row=3, column=0, sticky="e", pady=3)
    altezza_v = tk.StringVar()
    tk.Entry(fr_inp, textvariable=altezza_v, width=8,
             bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
             insertbackground=self.TEXT_COLOR,
             highlightthickness=1,
             highlightbackground=self.COLOR_HIGHLIGHT).grid(row=3, column=1, padx=(6,0),pady=3, sticky="w")
    altezza_v.set(_alt_saved)
    obiettivo_v.set(_ob_saved)
    lbl_bmi = tk.Label(fr_inp, text="BMI: —",
                       bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HIGHLIGHT,
                       font=("Arial", 9, "bold"),
                       wraplength=220, justify="center")
    lbl_bmi.grid(row=4, column=0, columnspan=2, pady=(6,2))
    def _calcola_bmi(*_):
        try:
            p = float(peso_v.get().replace(",","."))
            h = float(altezza_v.get().replace(",",".")) / 100
            if h <= 0: raise ValueError
            bmi = round(p / (h * h), 1)
            if bmi < 18.5:
                cat = "Sottopeso"
            elif bmi < 25.0:
                cat = "Normopeso"
            elif bmi < 30.0:
                cat = "Sovrappeso"
            elif bmi < 35.0:
                cat = "Obesità I"
            elif bmi < 40.0:
                cat = "Obesità II"
            else:
                cat = "Obesità III"
            lbl_bmi.config(text=f"BMI: {bmi}  —  {cat}")
        except Exception:
            lbl_bmi.config(text="BMI: —")
    peso_v.trace_add("write",    _calcola_bmi)
    altezza_v.trace_add("write", _calcola_bmi)
    altezza_v.trace_add("write",   lambda *_: _salva_peso() if altezza_v.get().strip() or obiettivo_v.get().strip() else None)
    obiettivo_v.trace_add("write", lambda *_: _salva_peso() if altezza_v.get().strip() or obiettivo_v.get().strip() else None)
    def _aggiungi_pesata():
        try:
            data_str = data_v.get().strip()
            datetime.datetime.strptime(data_str, "%d-%m-%Y")
            p = float(peso_v.get().replace(",","."))
            if p <= 0: raise ValueError
        except Exception:
            self.show_custom_warning("Errore", "Data (gg-mm-aaaa) e peso validi richiesti.")
            return
        nuova = [r for r in peso_storico if r["data"] != data_str]
        nuova.append({"data": data_str, "peso": round(p, 1)})
        nuova.sort(key=lambda r: datetime.datetime.strptime(r["data"], "%d-%m-%Y"))
        peso_storico[:] = nuova
        _salva_peso()
        _aggiorna_lista_peso()
        _disegna_grafico()
        self.show_toast(f"Pesata {data_str} — {p} kg salvata.")
        data_v.set(datetime.date.today().strftime("%d-%m-%Y"))
        peso_v.set("")
    def _elimina_pesata():
        sel = tv_peso.selection()
        if not sel: return
        vals = tv_peso.item(sel[0], "values")
        data_sel = vals[0]
        if not self.show_custom_askyesno("Conferma", f"Eliminare la pesata del {data_sel}?"):
            return
        peso_storico[:] = [r for r in peso_storico if r["data"] != data_sel]
        _salva_peso()
        _aggiorna_lista_peso()
        _disegna_grafico()
    fr_btns = tk.Frame(fr_inp, bg=self.COLOR_WIDGET_BG)
    fr_btns.grid(row=5, column=0, columnspan=2, pady=(6,0))
    def _mk_p(parent, ico, txt, cmd, fg=None):
        img = self.icone_gui.get(ico)
        fg  = fg or self.TEXT_COLOR
        l   = ttk.Label(parent, text=f" {txt}", image=img, compound="left",
                        background=self.COLOR_WIDGET_BG, foreground=fg,
                        cursor="hand2", font=("Arial", 9, "bold"), padding=(4,2))
        if img: l.image = img
        l.pack(side="left", padx=4)
        l.bind("<Button-1>", lambda e: cmd())
    def _azzera_peso():
        if not peso_storico: return
        if not self.show_custom_askyesno("Azzera",
                "Eliminare TUTTE le pesate?\nL'operazione non è reversibile."):
            return
        peso_storico[:] = []
        _salva_peso()
        _aggiorna_lista_peso()
        _disegna_grafico()
        self.show_toast("Storico peso azzerato.")
    _mk_p(fr_btns, "aggiungi",    "Aggiungi",    _aggiungi_pesata, "#98C379")
    _mk_p(fr_btns, "delete", "Elimina",     _elimina_pesata,  self.COLOR_ORANGE)
    _mk_p(fr_btns, "reset",  "Azzera", _azzera_peso,    self.COLOR_RED)
    fr_tv_p = tk.Frame(fr_left, bg=self.COLOR_WIDGET_BG)
    fr_tv_p.pack(fill="both", expand=True)
    vsb_p = ttk.Scrollbar(fr_tv_p, orient="vertical", style="Vertical.TScrollbar")
    vsb_p.pack(side="right", fill="y")
    tv_peso = ttk.Treeview(fr_tv_p,
                           columns=("data","peso","variaz","bmi"),
                           show="headings", style="Treeview",
                           yscrollcommand=vsb_p.set, height=10, selectmode='browse')
    vsb_p.config(command=tv_peso.yview)
    tv_peso.pack(fill="both", expand=True)
    for col, lbl, w in [("data","Data",90),("peso","Peso kg",70),
                         ("variaz","Variaz.",70),("bmi","BMI",60)]:
        tv_peso.heading(col, text=lbl)
        tv_peso.column(col, width=w, anchor="center")

    lbl_stats = tk.Label(fr_left, text="",
                         bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                         font=("Arial", 8), justify="left")
    lbl_stats.pack(anchor="w", pady=(6,0))
    def _aggiorna_lista_peso():
        tv_peso.delete(*tv_peso.get_children())
        if not peso_storico: return
        for i, r in enumerate(peso_storico):
            var_str = "—"
            tag     = ""
            if i > 0:
                diff = round(r["peso"] - peso_storico[i-1]["peso"], 1)
                var_str = f"{'+' if diff >= 0 else ''}{diff}"
                tag = "su" if diff > 0 else ("giu" if diff < 0 else "")
            try:
                h = float(altezza_v.get().replace(",",".")) / 100
                bmi_str = str(round(r["peso"] / (h*h), 1)) if h > 0 else "—"
            except Exception:
                bmi_str = "—"
            tv_peso.insert("", "end",
                           values=(r["data"], r["peso"], var_str, bmi_str),
                           tags=(tag,))
        tv_peso.tag_configure("su",  foreground=self.COLOR_ORANGE)
        tv_peso.tag_configure("giu", foreground="#98C379")
        pesi = [r["peso"] for r in peso_storico]
        stats = (f"Min: {min(pesi)} kg   Max: {max(pesi)} kg   "
                 f"Media: {round(sum(pesi)/len(pesi),1)} kg   "
                 f"Pesate: {len(pesi)}")
        lbl_stats.config(text=stats)
    cvs_peso = tk.Canvas(fr_right, bg=self.COLOR_WIDGET_BG,
                         highlightthickness=1,
                         highlightbackground=self.COLOR_HIGHLIGHT)
    cvs_peso.pack(fill="both", expand=True)
    def _disegna_grafico(*_):
        cvs_peso.delete("all")
        W = cvs_peso.winfo_width()  or 600
        H = cvs_peso.winfo_height() or 350
        PAD_L, PAD_R, PAD_T, PAD_B = 55, 20, 20, 40
        if not peso_storico or len(peso_storico) < 1:
            cvs_peso.create_text(W//2, H//2,
                text="Nessuna pesata registrata",
                fill=self.TEXT_COLOR, font=("Arial", 10))
            return
        pesi  = [r["peso"] for r in peso_storico]
        n     = len(pesi)
        p_min = min(pesi)
        p_max = max(pesi)
        p_med = sum(pesi) / n
        margin = max(1.0, (p_max - p_min) * 0.15) if p_max != p_min else 2.0
        y_min = p_min - margin
        y_max = p_max + margin
        def _px(i):
            if n == 1: return PAD_L + (W - PAD_L - PAD_R) // 2
            return PAD_L + int(i / (n-1) * (W - PAD_L - PAD_R))
        def _py(v):
            return PAD_T + int((1 - (v - y_min) / (y_max - y_min)) * (H - PAD_T - PAD_B))
        steps = 5
        for si in range(steps + 1):
            vy = y_min + si * (y_max - y_min) / steps
            y  = _py(vy)
            cvs_peso.create_line(PAD_L, y, W - PAD_R, y,
                                 fill="#333333",
                                 dash=(2,4))
            cvs_peso.create_text(PAD_L - 4, y,
                                 text=f"{vy:.1f}",
                                 anchor="e", fill=self.TEXT_COLOR,
                                 font=("Arial", 7))
        try:
            ob = float(obiettivo_v.get().replace(",","."))
            if y_min <= ob <= y_max:
                yo = _py(ob)
                cvs_peso.create_line(PAD_L, yo, W - PAD_R, yo,
                                     fill="#E5C07B", dash=(6,3), width=1.5)
                cvs_peso.create_text(W - PAD_R - 2, yo - 6,
                                     text=f"Obiettivo {ob} kg",
                                     anchor="e", fill="#E5C07B",
                                     font=("Arial", 7))
        except Exception:
            pass
        ym = _py(p_med)
        cvs_peso.create_line(PAD_L, ym, W - PAD_R, ym,
                              fill="#61AFEF", dash=(4,4), width=1)
        cvs_peso.create_text(PAD_L + 4, ym - 7,
                              text=f"Media {p_med:.1f} kg",
                              anchor="w", fill="#61AFEF",
                              font=("Arial", 7))
        pts = [(_px(i), _py(pesi[i])) for i in range(n)]
        if n > 1:
            for i in range(n - 1):
                col = "#98C379" if pesi[i+1] <= pesi[i] else self.COLOR_ORANGE
                cvs_peso.create_line(pts[i][0], pts[i][1],
                                      pts[i+1][0], pts[i+1][1],
                                      fill=col, width=2)
        for i, (x, y) in enumerate(pts):
            cvs_peso.create_oval(x-4, y-4, x+4, y+4,
                                  fill=self.COLOR_HIGHLIGHT, outline="")
            cvs_peso.create_text(x, y - 12,
                                  text=f"{pesi[i]}",
                                  fill=self.TEXT_COLOR, font=("Arial", 7))
        step_x = max(1, n // 8)
        for i in range(0, n, step_x):
            cvs_peso.create_text(_px(i), H - PAD_B + 10,
                                  text=peso_storico[i]["data"][:5],
                                  fill=self.TEXT_COLOR, font=("Arial", 7))
    cvs_peso.bind("<Configure>", _disegna_grafico)
    obiettivo_v.trace_add("write", lambda *_: _disegna_grafico())
    _aggiorna_lista_peso()
    _disegna_grafico()
    fr_top_info = tk.Frame(popup, bg=self.COLOR_WIDGET_BG)
    fr_top_info.pack(side="top", fill="x")
    lbl_istruzioni = tk.Label(fr_top_info,
            text="Doppio clic su Colazione / Pranzo / Cena / Spuntino per comporre il pasto  |  Tasto destro su un giorno per copiarlo",
            font=("Arial", 8, "italic"),
            bg=self.COLOR_WIDGET_BG, fg=self.COLOR_ORANGE)
    lbl_istruzioni.pack(pady=(2,0))
    def _gestisci_visibilita_label(event=None):
        try:
                idx = nb.index(nb.select())
                if idx in [0, 1, 2, 3]:
                    if not lbl_istruzioni.winfo_ismapped():
                       lbl_istruzioni.pack(pady=(2,0))
                else:
                    lbl_istruzioni.pack_forget()
        except Exception:
                pass
    nb.bind("<<NotebookTabChanged>>", _gestisci_visibilita_label)
    _gestisci_visibilita_label()
    tab_fabb = tk.Frame(nb, bg=self.COLOR_WIDGET_BG)
    def _carica_fabb():
        try:
            if os.path.exists(FABB_FILE):
                with open(FABB_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    def _salva_fabb():
        try:
            p = inputs["Peso (kg)"].get().strip()
            a = inputs["Altezza (cm)"].get().strip()
            e = inputs["Età"].get().strip()
            if not any([p not in ("", "0"), a not in ("", "0"), e not in ("", "0")]):
                return
            os.makedirs(DB_DIR, exist_ok=True)
            with open(FABB_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    "sesso":   inputs["Sesso"].get(),
                    "peso":    p, "altezza": a, "eta": e
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.show_custom_warning("Errore", f"Salvataggio fabbisogno fallito:\n{e}")
    _fabb_saved = _carica_fabb()
    _add_tab(tab_fabb, "calcolatrice", "Fabbisogno")
    fr_input = tk.LabelFrame(tab_fabb, text=" Dati Biometrici ", bg=self.COLOR_WIDGET_BG, 
                             fg=self.COLOR_HIGHLIGHT, font=("Arial", 9, "bold"), padx=15, pady=15)
    fr_input.pack(fill="x", padx=20, pady=20)
    inputs = {}
    for i, label in enumerate(["Sesso", "Peso (kg)", "Altezza (cm)", "Età"]):
            tk.Label(fr_input, text=label+":", bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR).grid(row=0, column=i*2, padx=5)
            if label == "Sesso":
                    var = tk.StringVar(value="Donna")
                    ent = ttk.Combobox(fr_input, textvariable=var, values=["Donna", "Uomo"], state="readonly", width=8, style="Border.TCombobox")
            else:
                    var = tk.StringVar(value="0")
                    ent = ttk.Entry(fr_input, textvariable=var, width=8, justify="center")
            ent.grid(row=0, column=i*2+1, padx=10)
            inputs[label] = var
    fr_res = tk.Frame(tab_fabb, bg=self.COLOR_WIDGET_BG)
    fr_res.pack(fill="both", expand=True, padx=20)
    def _aggiorna_tabella_fabbisogno():
            try:
                    s = inputs["Sesso"].get()
                    p = float(inputs["Peso (kg)"].get().replace(',', '.'))
                    a = float(inputs["Altezza (cm)"].get().replace(',', '.'))
                    e = int(inputs["Età"].get())
                    if p <= 0 or a <= 0 or e <= 0: return
                    if s == "Uomo":
                            bmr = (10 * p) + (6.25 * a) - (5 * e) + 5
                    else:
                            bmr = (10 * p) + (6.25 * a) - (5 * e) - 161
                    fabbisogni = {
                            "Sedentario": round(bmr * 1.2),
                            "Leggero": round(bmr * 1.375),
                            "Moderato": round(bmr * 1.55),
                            "Attivo": round(bmr * 1.725)
                    }
                    desc_mappa = {
                            "Sedentario": "Fabbisogno: Sedentario (Ufficio)",
                            "Leggero": "Fabbisogno: Leggero (Attività 1-2v)",
                            "Moderato": "Fabbisogno: Moderato (Sport 3-5v)",
                            "Attivo": "Fabbisogno: Attivo (Lavoro Fisico)"
                    }
                    for widget in fr_res.winfo_children():
                            widget.destroy()
                    tk.Label(fr_res, text=f"Metabolismo Basale (BMR): {round(bmr)} kcal/giorno", 
                             font=("Arial", 11, "bold"), bg=self.COLOR_WIDGET_BG, 
                             fg=self.COLOR_HIGHLIGHT).pack(pady=(10, 15))
                    for chiave, kcal in fabbisogni.items():
                            row = tk.Frame(fr_res, bg=self.COLOR_WHITE, pady=4)
                            row.pack(fill="x", pady=1)
                            tk.Label(row, text=desc_mappa[chiave], bg=self.COLOR_WHITE, 
                                     fg="#333333", font=("Arial", 9)).pack(side="left", padx=15)
                            tk.Label(row, text=f"{kcal} kcal", bg=self.COLOR_WHITE, 
                                     fg="#000000", font=("Arial", 9, "bold")).pack(side="right", padx=15)
                    base_kcal = fabbisogni["Moderato"]
                    fr_obiettivi = tk.LabelFrame(fr_res, text=" Obiettivi Consigliati ", bg=self.COLOR_WIDGET_BG, 
                                                fg=self.COLOR_HIGHLIGHT, font=("Arial", 9, "bold"), padx=10, pady=10)
                    fr_obiettivi.pack(fill="x", pady=20)
                    piani = [
                            ("Per perdere peso (Deficit 15%)", round(base_kcal * 0.85), "#ff5555"),
                            ("Per mantenere il peso attuale", base_kcal, "#55aaff"),
                            ("Per aumentare massa (+10%)", round(base_kcal * 1.10), "#55ff77")
                    ]
                    for label, valore, colore in piani:
                            o_row = tk.Frame(fr_obiettivi, bg=self.COLOR_WIDGET_BG)
                            o_row.pack(fill="x", pady=2)
                            tk.Label(o_row, text=label, bg=self.COLOR_WIDGET_BG, 
                                     fg="#FFFFFF", font=("Arial", 9)).pack(side="left", padx=5)
                            tk.Label(o_row, text=f"{valore} kcal", bg=self.COLOR_WIDGET_BG, 
                                     fg=colore, font=("Arial", 10, "bold")).pack(side="right", padx=5)
            except (ValueError, KeyError):
                    pass
    if _fabb_saved:
        inputs["Sesso"].set(_fabb_saved.get("sesso", "Donna"))
        inputs["Peso (kg)"].set(_fabb_saved.get("peso", "0"))
        inputs["Altezza (cm)"].set(_fabb_saved.get("altezza", "0"))
        inputs["Età"].set(_fabb_saved.get("eta", "0"))
    for _v in inputs.values():
        _v.trace_add("write", lambda *_: _salva_fabb())
    popup.after(150, _aggiorna_tabella_fabbisogno)
    icona_calc = self.icone_gui.get("search")
    btn_container = tk.Frame(fr_input, bg=self.COLOR_WIDGET_BG, cursor="hand2")
    btn_container.grid(row=0, column=8, padx=20)
    lbl_icon = tk.Label(btn_container, image=icona_calc, bg=self.COLOR_WIDGET_BG)
    lbl_icon.pack(side="left")
    lbl_text = tk.Label(btn_container, text=" Cerca", font=("Arial", 9, "bold"),
                        bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HIGHLIGHT)
    lbl_text.pack(side="left")
    btn_container.bind("<Button-1>", lambda e: _aggiorna_tabella_fabbisogno())
    lbl_icon.bind("<Button-1>", lambda e: _aggiorna_tabella_fabbisogno())
    lbl_text.bind("<Button-1>", lambda e: _aggiorna_tabella_fabbisogno())
    def _carica_pedometro():
        try:
            if os.path.exists(PEDOMETRO_FILE):
                with open(PEDOMETRO_FILE, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    return d.get("passi", {}), int(d.get("obiettivo_default", 10000))
        except Exception:
            pass
        return {}, 10000
    def _salva_pedometro():
        try:
            os.makedirs(DB_DIR, exist_ok=True)
            with open(PEDOMETRO_FILE, "w", encoding="utf-8") as f:
                json.dump({"passi": passi_db, "obiettivo_default": int(ped_obiettivo_var.get() or 10000)},
                          f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.show_custom_warning("Errore", f"Salvataggio pedometro fallito:\n{e}")
    passi_db, _ped_ob_default = _carica_pedometro()
    tab_ped = tk.Frame(nb, bg=self.COLOR_WIDGET_BG)
    _add_tab(tab_ped, "fitness", "Passi")
    ped_left  = tk.Frame(tab_ped, bg=self.COLOR_WIDGET_BG, width=280)
    ped_left.pack(side="left", fill="y", padx=(10, 4), pady=8)
    ped_left.pack_propagate(False)
    ped_right = tk.Frame(tab_ped, bg=self.COLOR_WIDGET_BG)
    ped_right.pack(side="left", fill="both", expand=True, padx=(4, 10), pady=8)
    fr_ins = tk.LabelFrame(ped_left, text=" Registra Passi ",
                           bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HIGHLIGHT,
                           font=("Arial", 9, "bold"), padx=10, pady=8)
    fr_ins.pack(fill="x", pady=(0, 8))
    tk.Label(fr_ins, text="Data:", bg=self.COLOR_WIDGET_BG,
             fg=self.TEXT_COLOR, font=("Arial", 9)).grid(row=0, column=0, sticky="w", pady=3)
    ped_data_var = tk.StringVar(value=datetime.date.today().strftime("%d-%m-%Y"))
    ped_data_entry = tk.Entry(fr_ins, textvariable=ped_data_var, width=13,
                              bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                              insertbackground=self.TEXT_COLOR,
                              highlightthickness=1, highlightbackground=self.COLOR_HIGHLIGHT,
                              font=("Arial", 9))
    ped_data_entry.grid(row=0, column=1, sticky="w", padx=(6,0), pady=3)
    img_cal = self.icone_gui.get("calendario")
    btn_cal_ped = tk.Label(fr_ins, image=img_cal, bg=self.COLOR_WIDGET_BG, cursor="hand2")
    if img_cal: btn_cal_ped.image = img_cal
    btn_cal_ped.grid(row=0, column=2, padx=(4,0), pady=3)
    btn_cal_ped.bind("<Button-1>", lambda e: self.mostra_calendario_popup_semplice(ped_data_entry, ped_data_var))
    tk.Label(fr_ins, text="Passi:", bg=self.COLOR_WIDGET_BG,
             fg=self.TEXT_COLOR, font=("Arial", 9)).grid(row=1, column=0, sticky="w", pady=3)
    ped_passi_var = tk.StringVar()
    ped_passi_entry = tk.Entry(fr_ins, textvariable=ped_passi_var, width=10,
                               bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                               insertbackground=self.TEXT_COLOR,
                               highlightthickness=1, highlightbackground=self.COLOR_HIGHLIGHT,
                               font=("Arial", 9))
    ped_passi_entry.grid(row=1, column=1, sticky="w", padx=(6,0), pady=3)
    tk.Label(fr_ins, text="Obiettivo:", bg=self.COLOR_WIDGET_BG,
             fg=self.TEXT_COLOR, font=("Arial", 9)).grid(row=2, column=0, sticky="w", pady=3)
    ped_obiettivo_var = tk.StringVar(value=str(_ped_ob_default))
    ped_ob_entry = tk.Entry(fr_ins, textvariable=ped_obiettivo_var, width=10,
                            bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                            insertbackground=self.TEXT_COLOR,
                            highlightthickness=1, highlightbackground=self.COLOR_HIGHLIGHT,
                            font=("Arial", 9))
    ped_ob_entry.grid(row=2, column=1, sticky="w", padx=(6,0), pady=3)
    tk.Label(fr_ins, text="Note:", bg=self.COLOR_WIDGET_BG,
             fg=self.TEXT_COLOR, font=("Arial", 9)).grid(row=3, column=0, sticky="w", pady=3)
    ped_note_var = tk.StringVar()
    ped_note_entry = tk.Entry(fr_ins, textvariable=ped_note_var, width=16,
                              bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                              insertbackground=self.TEXT_COLOR,
                              highlightthickness=1, highlightbackground=self.COLOR_HIGHLIGHT,
                              font=("Arial", 9))
    ped_note_entry.grid(row=3, column=1, columnspan=2, sticky="we", padx=(6,0), pady=3)
    def _ped_salva_voce():
        data_str = ped_data_var.get().strip()
        try:
            datetime.datetime.strptime(data_str, "%d-%m-%Y")
        except ValueError:
            self.show_custom_warning("Errore", "Data non valida. Usa il formato gg-mm-aaaa.")
            return
        try:
            passi = int(ped_passi_var.get().strip().replace(".", "").replace(",", ""))
            if passi < 0: raise ValueError
        except ValueError:
            self.show_custom_warning("Errore", "Inserisci un numero di passi valido.")
            return
        try:
            ob = int(ped_obiettivo_var.get().strip().replace(".", "").replace(",", ""))
            if ob <= 0: ob = 10000
        except ValueError:
            ob = 10000
        passi_db[data_str] = {"passi": passi, "obiettivo": ob, "note": ped_note_var.get().strip()}
        _salva_pedometro()
        ped_passi_var.set("")
        ped_note_var.set("")
        _ped_aggiorna_tutto()
        self.show_toast(f" {passi:,} passi salvati per il {data_str}.")
    def _ped_elimina_voce():
        sel = ped_tree.selection()
        if not sel: return
        data_str = ped_tree.item(sel[0], "values")[0]
        if not self.show_custom_askyesno("Elimina", f"Eliminare la voce del {data_str}?"): return
        passi_db.pop(data_str, None)
        _salva_pedometro()
        _ped_aggiorna_tutto()
    fr_btn_ins = tk.Frame(fr_ins, bg=self.COLOR_WIDGET_BG)
    fr_btn_ins.grid(row=4, column=0, columnspan=3, pady=(8, 2))
    def _mk_ped_btn(parent, ico, txt, cmd, fg=None):
        img = self.icone_gui.get(ico)
        fg  = fg or self.TEXT_COLOR
        l = tk.Label(parent, text=f" {txt}", image=img, compound="left",
                     bg=self.COLOR_WIDGET_BG, fg=fg, cursor="hand2",
                     font=("Arial", 9, "bold"), padx=6, pady=3)
        if img: l.image = img
        l.pack(side="left", padx=4)
        l.bind("<Button-1>", lambda e: cmd())
    def _ped_azzera():
        if not passi_db: return
        if not self.show_custom_askyesno("Azzera",
                "Eliminare TUTTI i dati del pedometro?\nL'operazione non è reversibile."):
            return
        passi_db.clear()
        _salva_pedometro()
        _ped_aggiorna_tutto()
        self.show_toast("Pedometro azzerato.")
    _mk_ped_btn(fr_btn_ins, "check",  "Salva",   _ped_salva_voce, "#98C379")
    _mk_ped_btn(fr_btn_ins, "delete", "Elimina", _ped_elimina_voce, self.COLOR_ORANGE)
    _mk_ped_btn(fr_btn_ins, "reset",  "Azzera", _ped_azzera, self.COLOR_RED)

    fr_stats = tk.LabelFrame(ped_left, text=" Statistiche ",
                             bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HIGHLIGHT,
                             font=("Arial", 9, "bold"), padx=10, pady=6)
    fr_stats.pack(fill="x", pady=(0, 8))
    ped_stat_labels = {}
    for i, (chiave, testo) in enumerate([
        ("oggi",     "Oggi:"),
        ("media7",   "Media 7gg:"),
        ("media30",  "Media 30gg:"),
        ("record",   "Record:"),
        ("tot_mese", "Totale mese:"),
        ("ob_pct",   "Obiettivo oggi:"),
        ("giorni_ok","Giorni obiettivo:"),
    ]):
        tk.Label(fr_stats, text=testo, bg=self.COLOR_WIDGET_BG,
                 fg=self.TEXT_COLOR, font=("Arial", 8), anchor="w").grid(
                 row=i, column=0, sticky="w", pady=1)
        lbl = tk.Label(fr_stats, text="—", bg=self.COLOR_WIDGET_BG,
                       fg=self.COLOR_HIGHLIGHT, font=("Arial", 8, "bold"), anchor="w")
        lbl.grid(row=i, column=1, sticky="w", padx=(8, 0), pady=1)
        ped_stat_labels[chiave] = lbl
    fr_filt = tk.Frame(ped_left, bg=self.COLOR_WIDGET_BG)
    fr_filt.pack(fill="x", pady=(0, 4))
    tk.Label(fr_filt, text="Mese:", bg=self.COLOR_WIDGET_BG,
             fg=self.TEXT_COLOR, font=("Arial", 8)).pack(side="left")
    ped_mese_var = tk.StringVar(value="Tutti")
    ped_mese_cb = ttk.Combobox(fr_filt, textvariable=ped_mese_var,
                               values=["Tutti"] + [f"{m:02d}" for m in range(1, 13)],
                               state="readonly", width=6, style="Border.TCombobox")
    ped_mese_cb.pack(side="left", padx=(4, 8))
    tk.Label(fr_filt, text="Anno:", bg=self.COLOR_WIDGET_BG,
             fg=self.TEXT_COLOR, font=("Arial", 8)).pack(side="left")
    anno_corrente = datetime.date.today().year
    ped_anno_var = tk.StringVar(value=str(anno_corrente))
    ped_anno_cb = ttk.Combobox(fr_filt, textvariable=ped_anno_var,
                               values=["Tutti"] + [str(a) for a in range(anno_corrente, anno_corrente - 6, -1)],
                               state="readonly", width=7, style="Border.TCombobox")
    ped_anno_cb.pack(side="left", padx=(4, 0))
    ped_mese_cb.bind("<<ComboboxSelected>>", lambda e: _ped_aggiorna_tutto())
    ped_anno_cb.bind("<<ComboboxSelected>>", lambda e: _ped_aggiorna_tutto())
    ped_canvas_frame = tk.Frame(ped_right, bg=self.COLOR_WIDGET_BG, height=210)
    ped_canvas_frame.pack(fill="x", side="top", pady=(0, 6))
    ped_canvas_frame.pack_propagate(False)
    ped_canvas = tk.Canvas(ped_canvas_frame, bg=self.COLOR_WIDGET_BG, highlightthickness=0)
    ped_canvas.pack(fill="both", expand=True)
    fr_tree_ped = tk.Frame(ped_right, bg=self.COLOR_WIDGET_BG)
    fr_tree_ped.pack(fill="both", expand=True)
    vsb_ped = ttk.Scrollbar(fr_tree_ped, orient="vertical", style="Vertical.TScrollbar")
    vsb_ped.pack(side="right", fill="y")
    ped_tree = ttk.Treeview(fr_tree_ped, columns=("data","passi","obiettivo","pct","note"),
                            show="headings", yscrollcommand=vsb_ped.set,
                            style="Treeview", height=8, selectmode='browse')
    vsb_ped.config(command=ped_tree.yview)
    ped_tree.pack(fill="both", expand=True)
    for col, lbl, w in zip(("data","passi","obiettivo","pct","note"),
                           ("Data","Passi","Obiettivo","%","Note"),
                           (90, 70, 80, 50, 120)):
        ped_tree.heading(col, text=lbl, command=lambda c=col: _ped_sort(c))
        ped_tree.column(col, width=w, anchor="center" if col != "note" else "w")
    ped_tree.tag_configure("ok",   background="#0d2e0d", foreground="#98C379")
    ped_tree.tag_configure("warn", background="#3a2000", foreground=self.COLOR_ORANGE)
    ped_tree.tag_configure("alt",  background=self.COLOR_WIDGET_BG)
    ped_tree.tag_configure("norm", background=self.COLOR_WIDGET_BG)
    _ped_sort_col = ["data"]
    _ped_sort_rev = [False]
    def _ped_sort(col):
        if _ped_sort_col[0] == col:
            _ped_sort_rev[0] = not _ped_sort_rev[0]
        else:
            _ped_sort_col[0] = col
            _ped_sort_rev[0] = False
        _ped_aggiorna_tutto()
    def _ped_righe_filtrate():
        mese_f = ped_mese_var.get()
        anno_f = ped_anno_var.get()
        righe = []
        for data_str, rec in passi_db.items():
            try:
                d = datetime.datetime.strptime(data_str, "%d-%m-%Y").date()
            except ValueError:
                continue
            if anno_f != "Tutti" and str(d.year) != anno_f: continue
            if mese_f != "Tutti" and f"{d.month:02d}" != mese_f: continue
            p  = int(rec.get("passi", 0))
            ob = int(rec.get("obiettivo", 10000))
            pct = round(p / ob * 100) if ob > 0 else 0
            righe.append((data_str, p, ob, pct, rec.get("note", ""), d))
        idx = {"data": 5, "passi": 1, "obiettivo": 2, "pct": 3, "note": 4}.get(_ped_sort_col[0], 5)
        righe.sort(key=lambda r: r[idx], reverse=_ped_sort_rev[0])
        return righe
    def _ped_aggiorna_stats(righe):
        oggi_str = datetime.date.today().strftime("%d-%m-%Y")
        oggi_rec = passi_db.get(oggi_str)
        if oggi_rec:
            p_oggi = int(oggi_rec.get("passi", 0))
            ob_oggi = int(oggi_rec.get("obiettivo", 10000))
            pct_oggi = round(p_oggi / ob_oggi * 100) if ob_oggi > 0 else 0
            ped_stat_labels["oggi"].config(text=f"{p_oggi:,}",
                fg="#98C379" if p_oggi >= ob_oggi else self.COLOR_ORANGE)
            ped_stat_labels["ob_pct"].config(text=f"{pct_oggi}%",
                fg="#98C379" if pct_oggi >= 100 else self.COLOR_ORANGE)
        else:
            ped_stat_labels["oggi"].config(text="—", fg=self.TEXT_COLOR)
            ped_stat_labels["ob_pct"].config(text="—", fg=self.TEXT_COLOR)
        tutti = [(ds, int(r.get("passi",0)), int(r.get("obiettivo",10000)))
                 for ds, r in passi_db.items()]
        if tutti:
            vals = [t[1] for t in tutti]
            ped_stat_labels["record"].config(text=f"{max(vals):,}")
            oggi_d = datetime.date.today()
            ultimi7  = [t[1] for t in tutti
                        if 0 <= (oggi_d - datetime.datetime.strptime(t[0],"%d-%m-%Y").date()).days < 7]
            ultimi30 = [t[1] for t in tutti
                        if 0 <= (oggi_d - datetime.datetime.strptime(t[0],"%d-%m-%Y").date()).days < 30]
            ped_stat_labels["media7"].config(
                text=f"{round(sum(ultimi7)/len(ultimi7)):,}" if ultimi7 else "—")
            ped_stat_labels["media30"].config(
                text=f"{round(sum(ultimi30)/len(ultimi30)):,}" if ultimi30 else "—")
            ped_stat_labels["tot_mese"].config(text=f"{sum(r[1] for r in righe):,}")
            giorni_ok = sum(1 for t in tutti if t[1] >= t[2])
            ped_stat_labels["giorni_ok"].config(text=f"{giorni_ok} / {len(tutti)}")
        else:
            for k in ("record","media7","media30","tot_mese","giorni_ok"):
                ped_stat_labels[k].config(text="—", fg=self.TEXT_COLOR)
    def _ped_disegna_grafico(righe):
        ped_canvas.delete("all")
        ped_canvas.update_idletasks()
        W = ped_canvas.winfo_width()
        H = ped_canvas.winfo_height()
        if W < 10 or H < 10 or not righe: return
        righe_graf = sorted(righe, key=lambda r: r[5])[-30:]
        n = len(righe_graf)
        pad_l, pad_r, pad_t, pad_b = 44, 12, 14, 38
        area_w = W - pad_l - pad_r
        area_h = H - pad_t - pad_b
        max_p = max(r[1] for r in righe_graf) or 1
        ob_ref = righe_graf[-1][2]
        scale_max = max(max_p * 1.1, ob_ref * 1.1)
        bar_w = max(4, area_w // n - 3)
        step  = area_w / n
        grid_col = "#CCCCCC" if self.COLOR_BACKGROUND == "#FFFFFF" else "#444444"
        for k in range(5):
            gy = pad_t + area_h - int(area_h * k / 4)
            ped_canvas.create_line(pad_l, gy, W - pad_r, gy, fill=grid_col, dash=(2,4))
            val = int(scale_max * k / 4)
            ped_canvas.create_text(pad_l - 4, gy,
                text=f"{val//1000}k" if val >= 1000 else str(val),
                anchor="e", font=("Arial", 7), fill=self.TEXT_COLOR)
        ob_y = pad_t + area_h - int(area_h * ob_ref / scale_max)
        ped_canvas.create_line(pad_l, ob_y, W - pad_r, ob_y,
                               fill=self.COLOR_ORANGE, dash=(4,3), width=1)
        ped_canvas.create_text(W - pad_r - 2, ob_y - 5,
            text=f"Ob. {ob_ref//1000}k" if ob_ref >= 1000 else f"Ob. {ob_ref}",
            anchor="e", font=("Arial", 7), fill=self.COLOR_ORANGE)
        media_pts = []
        for i, r in enumerate(righe_graf):
            start = max(0, i - 6)
            media7 = sum(righe_graf[j][1] for j in range(start, i+1)) / (i - start + 1)
            cx = pad_l + int(step * i + step / 2)
            cy = pad_t + area_h - int(area_h * media7 / scale_max)
            media_pts.append((cx, cy))
        if len(media_pts) > 1:
            for i in range(len(media_pts) - 1):
                ped_canvas.create_line(media_pts[i][0], media_pts[i][1],
                                       media_pts[i+1][0], media_pts[i+1][1],
                                       fill=self.COLOR_HIGHLIGHT, width=2)
        for i, r in enumerate(righe_graf):
            cx = pad_l + int(step * i + step / 2)
            bar_h = max(2, int(area_h * r[1] / scale_max))
            x0, x1 = cx - bar_w // 2, cx + bar_w // 2
            y0, y1 = pad_t + area_h - bar_h, pad_t + area_h
            ped_canvas.create_rectangle(x0, y0, x1, y1,
                fill="#98C379" if r[1] >= r[2] else "#E06C75", outline="")
            if n <= 10 or i % max(1, n // 10) == 0:
                ped_canvas.create_text(cx, H - pad_b + 4, text=r[0][:5],
                                       anchor="n", font=("Arial", 7), fill=self.TEXT_COLOR)
        leg_x, leg_y = pad_l + 4, pad_t + 4
        ped_canvas.create_rectangle(leg_x, leg_y, leg_x+10, leg_y+8, fill="#98C379", outline="")
        ped_canvas.create_text(leg_x+14, leg_y+4, text="Obiettivo raggiunto",
                               anchor="w", font=("Arial", 7), fill=self.TEXT_COLOR)
        ped_canvas.create_rectangle(leg_x+130, leg_y, leg_x+140, leg_y+8, fill="#E06C75", outline="")
        ped_canvas.create_text(leg_x+144, leg_y+4, text="Sotto obiettivo",
                               anchor="w", font=("Arial", 7), fill=self.TEXT_COLOR)
        ped_canvas.create_line(leg_x+260, leg_y+4, leg_x+272, leg_y+4,
                               fill=self.COLOR_HIGHLIGHT, width=2)
        ped_canvas.create_text(leg_x+276, leg_y+4, text="Media 7gg",
                               anchor="w", font=("Arial", 7), fill=self.TEXT_COLOR)
    def _ped_aggiorna_tutto():
        righe = _ped_righe_filtrate()
        for item in ped_tree.get_children():
            ped_tree.delete(item)
        for i, r in enumerate(righe):
            data_str, p, ob, pct, note, _ = r
            tag = "ok" if p >= ob else ("warn" if pct < 50 else ("alt" if i % 2 == 0 else "norm"))
            ped_tree.insert("", "end",
                            values=(data_str, f"{p:,}", f"{ob:,}", f"{pct}%", note),
                            tags=(tag,))
        _ped_aggiorna_stats(righe)
        ped_canvas.after(50, lambda: _ped_disegna_grafico(righe))
    oggi_str2 = datetime.date.today().strftime("%d-%m-%Y")
    if oggi_str2 in passi_db:
        ped_passi_var.set(str(passi_db[oggi_str2].get("passi", "")))
        ped_note_var.set(passi_db[oggi_str2].get("note", ""))
        ped_obiettivo_var.set(str(passi_db[oggi_str2].get("obiettivo", _ped_ob_default)))
    def _ped_on_select(event):
        sel = ped_tree.selection()
        if not sel: return
        data_str = ped_tree.item(sel[0], "values")[0]
        if data_str in passi_db:
            rec = passi_db[data_str]
            ped_data_var.set(data_str)
            ped_passi_var.set(str(rec.get("passi", "")))
            ped_obiettivo_var.set(str(rec.get("obiettivo", _ped_ob_default)))
            ped_note_var.set(rec.get("note", ""))
    ped_tree.bind("<<TreeviewSelect>>", _ped_on_select)
    ped_canvas.bind("<Configure>", lambda e: _ped_aggiorna_tutto())
    popup.after(120, _ped_aggiorna_tutto)
    
    # Gestione utenti
    UTENTI_DIR = os.path.join(DB_DIR, "utenti")
    FILE_KEYS  = ["dieta.json", "peso.json", "fabbisogno.json",
                   "pedometro.json", "alimenti_custom.json"]
    _MAPPA_FILE_GENERICO = {
        "dieta.json":           "dieta_piano.json",
        "peso.json":            "peso_storico.json",
        "fabbisogno.json":      "fabbisogno_dati.json",
        "pedometro.json":       "pedometro.json",
        "alimenti_custom.json": "alimenti_custom.json",
    }
    def _get_utenti():
        nomi = ["Generico"]
        if os.path.isdir(UTENTI_DIR):
            nomi += sorted(
                n for n in os.listdir(UTENTI_DIR)
                if os.path.isdir(os.path.join(UTENTI_DIR, n))
            )
        return nomi
    def _path_for(nome_utente, filename):
        if nome_utente == "Generico":
            return os.path.join(DB_DIR, _MAPPA_FILE_GENERICO.get(filename, filename))
        return os.path.join(UTENTI_DIR, nome_utente, filename)
    def _copia_profilo(src_nome, dst_nome):
        for fname in FILE_KEYS:
            src = _path_for(src_nome, fname)
            dst = _path_for(dst_nome, fname)
            if os.path.exists(src):
                import shutil
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
    def _carica_profilo_utente(nome):
        nonlocal _utente_corrente
        if nome == _utente_corrente:
            return
        risposta = self.show_custom_askyesno(
            "Cambia utente",
            f"Per caricare il profilo «{nome}» il pannello verrà riaperto.\nContinuare?"
        )
        if not risposta:
            utente_var.set(_utente_corrente)
            return
        _utente_corrente = nome
        nb.tab(tab_utenti, text=f"Utenti > {nome} ")
        try:
            os.makedirs(DB_DIR, exist_ok=True)
            import json as _json
            with open(os.path.join(DB_DIR, "utente_attivo.json"), "w", encoding="utf-8") as f:
                _json.dump({"utente": nome}, f)
        except Exception:
            pass
        popup.destroy()
        setattr(self, '_dieta_popup', None)
        self.after(100, self.apri_dieta)
    def _aggiungi_utente():
        aw = tk.Toplevel(popup)
        aw.withdraw()
        aw.title("Nuovo utente")
        aw.resizable(False, False)
        aw.transient(popup)
        aw.configure(bg=self.COLOR_WIDGET_BG)
        aw.bind("<Escape>", lambda e: aw.destroy())
        ttk.Label(aw, text="Nome utente:",
                  background=self.COLOR_WIDGET_BG,
                  foreground=self.TEXT_COLOR,
                  font=("Arial", 9)).pack(padx=20, pady=(16, 4), anchor="w")
        nome_v = tk.StringVar()
        tk.Entry(aw, textvariable=nome_v, width=22,
                 bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                 insertbackground=self.TEXT_COLOR,
                 highlightthickness=1,
                 highlightbackground=self.COLOR_HIGHLIGHT).pack(padx=20, pady=(0, 6))
        copia_v = tk.BooleanVar(value=True)
        ttk.Checkbutton(aw, text="Copia profilo Generico come base",
                variable=copia_v).pack(padx=20, pady=(0, 10), anchor="w")
        def _conferma_aggiungi():
            nome = nome_v.get().strip()
            if not nome or nome == "Generico":
                self.show_custom_warning("Errore", "Nome non valido.")
                return
            cartella = os.path.join(UTENTI_DIR, nome)
            if os.path.exists(cartella):
                self.show_custom_warning("Esiste già", f"L'utente «{nome}» esiste già.")
                return
            os.makedirs(cartella, exist_ok=True)
            if copia_v.get():
                _copia_profilo("Generico", nome)
            aw.destroy()
            _aggiorna_lista_utenti()
            self.show_toast(f"Utente «{nome}» creato.")
        bot_aw = tk.Frame(aw, bg=self.COLOR_WIDGET_BG)
        bot_aw.pack(pady=(0, 14))
        for ico, txt, cmd, fg in [
            ("check",  "Crea",    _conferma_aggiungi, "#98C379"),
            ("chiudi", "Annulla", aw.destroy,         None),
        ]:
            img = self.icone_gui.get(ico)
            l = ttk.Label(bot_aw, text=f" {txt}", image=img, compound="left",
                  background=self.COLOR_WIDGET_BG,
                  foreground=fg or self.TEXT_COLOR,
                  cursor="hand2", font=("Arial", 9, "bold"), padding=(6, 2))
            if img: l.image = img
            l.pack(side="left", padx=6)
            l.bind("<Button-1>", lambda e, c=cmd: c())
        aw.update_idletasks()
        w2, h2 = 340, 130
        aw.geometry(f"{w2}x{h2}+"
                    f"{popup.winfo_x()+popup.winfo_width()//2-w2//2}+"
                    f"{popup.winfo_y()+popup.winfo_height()//2-h2//2}")
        aw.deiconify()
        aw.grab_set(); aw.focus_force()
    def _elimina_utente():
        nome = utente_var.get()
        if nome == "Generico":
            self.show_custom_warning("Attenzione", "Non puoi eliminare il profilo Generico.")
            return
        if not self.show_custom_askyesno(
                "Elimina utente",
                f"Eliminare il profilo «{nome}» e tutti i suoi dati?\nOperazione irreversibile."):
            return
        import shutil
        cartella = os.path.join(UTENTI_DIR, nome)
        try:
            if os.path.exists(cartella):
                def on_error(func, path, exc_info):
                    import stat
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                shutil.rmtree(cartella, onerror=on_error)
            if nome == _utente_corrente:
                self.show_toast(f"Profilo attivo eliminato. Ritorno a Generico...")
                try:
                    with open(os.path.join(DB_DIR, "utente_attivo.json"), "w", encoding="utf-8") as f:
                        import json as _j
                        _j.dump({"utente": "Generico"}, f)
                except Exception:
                    pass
                popup.destroy()
                setattr(self, '_dieta_popup', None)
                self.after(100, self.apri_dieta)
                return
            utente_var.set(_utente_corrente)
            _aggiorna_lista_utenti()
            self.show_toast(f"Utente «{nome}» eliminato.")
        except Exception as e:
            self.show_custom_warning("Errore", f"Impossibile eliminare: {str(e)}")
    def _copia_da_generico():
        nome = utente_var.get()
        if nome == "Generico":
            self.show_custom_warning("Attenzione", "Seleziona prima un utente diverso da Generico.")
            return
        if not self.show_custom_askyesno(
                "Copia da Generico",
                f"Copiare tutti i dati del Generico nel profilo «{nome}»?\nI dati esistenti verranno sovrascritti."):
            return
        _copia_profilo("Generico", nome)
        self.show_toast(f"Dati Generico copiati in «{nome}».")
    def _copia_a_generico():
        nome = utente_var.get()
        if nome == "Generico":
            self.show_custom_warning("Attenzione", "Seleziona prima un utente diverso da Generico.")
            return
        if not self.show_custom_askyesno(
                "Copia verso Generico",
                f"Copiare i dati di «{nome}» nel profilo Generico?\nI dati Generico verranno sovrascritti."):
            return
        _copia_profilo(nome, "Generico")
        self.show_toast(f"Dati «{nome}» copiati nel profilo Generico.")
    def _aggiorna_lista_utenti():
        nomi = _get_utenti()
        cb_utenti["values"] = nomi
        if utente_var.get() not in nomi:
            utente_var.set("Generico")
        _popola_tv_utenti()
        _aggiorna_info_utente()
    def _aggiorna_info_utente(*_):
        nome = utente_var.get()
        if nome == "Generico":
            lbl_profilo_info.config(
                text="Profilo predefinito — dati nella cartella principale dell'app",
                fg=self.TEXT_COLOR)
        else:
            cartella = os.path.join(UTENTI_DIR, nome)
            n_file = sum(1 for f in FILE_KEYS if os.path.exists(os.path.join(cartella, f)))
            lbl_profilo_info.config(
                text=f"Cartella: {cartella}\nFile dati presenti: {n_file}/{len(FILE_KEYS)}",
                fg=self.TEXT_COLOR)
    try:
        import json as _json2
        _ua_path = os.path.join(DB_DIR, "utente_attivo.json")
        _utente_corrente = _json2.load(open(_ua_path, encoding="utf-8"))["utente"] \
            if os.path.exists(_ua_path) else "Generico"
    except Exception:
        _utente_corrente = "Generico"
    tab_utenti = tk.Frame(nb, bg=self.COLOR_WIDGET_BG)
    _add_tab(tab_utenti, "utenti", f"Utenti > {_utente_corrente}")
    fr_u_left  = tk.Frame(tab_utenti, bg=self.COLOR_WIDGET_BG, width=340)
    fr_u_left.pack(side="left", fill="y", padx=(16, 8), pady=12)
    fr_u_left.pack_propagate(False)
    fr_u_right = tk.Frame(tab_utenti, bg=self.COLOR_WIDGET_BG)
    fr_u_right.pack(side="left", fill="both", expand=True, padx=(8, 16), pady=12)
    fr_sel = tk.LabelFrame(fr_u_left, text=" Utente attivo ",
                    bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HIGHLIGHT,
                    font=("Arial", 9, "bold"), padx=12, pady=10)
    fr_sel.pack(fill="x", pady=(0, 10))
    utente_var = tk.StringVar(value=_utente_corrente)
    cb_utenti = ttk.Combobox(fr_sel, textvariable=utente_var,
                      values=_get_utenti(),
                      state="readonly", width=26,
                      style="Border.TCombobox")
    cb_utenti.pack(pady=(4, 8))
    lbl_attivo_badge = tk.Label(fr_sel,
        text=f"▶  Caricato ora: {_utente_corrente}",
        bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HIGHLIGHT,
        font=("Arial", 9, "bold"))
    lbl_attivo_badge.pack(anchor="w")
    ttk.Separator(fr_sel, orient="horizontal").pack(fill="x", pady=(8, 6))
    lbl_profilo_info = tk.Label(fr_sel, text="", bg=self.COLOR_WIDGET_BG,
                         fg=self.TEXT_COLOR, font=("Arial", 8),
                         justify="left", wraplength=280)
    lbl_profilo_info.pack(anchor="w")
    def _mk_u(parent, ico, txt, cmd, fg=None):
        img = self.icone_gui.get(ico)
        fg  = fg or self.TEXT_COLOR
        l   = ttk.Label(parent, text=f" {txt}", image=img, compound="left",
                background=self.COLOR_WIDGET_BG, foreground=fg,
                cursor="hand2", font=("Arial", 9, "bold"), padding=(6, 3))
        if img: l.image = img
        l.pack(side="left", padx=5, pady=4)
        l.bind("<Button-1>", lambda e: cmd())
        return l
    fr_carica_btn = tk.Frame(fr_sel, bg=self.COLOR_WIDGET_BG)
    fr_carica_btn.pack(fill="x", pady=(6, 0))
    _mk_u(fr_carica_btn, "check", "Carica profilo selezionato",
          lambda: _carica_profilo_utente(utente_var.get()), "#98C379")
    fr_gest = tk.LabelFrame(fr_u_left, text=" Gestisci utenti ",
                     bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HIGHLIGHT,
                     font=("Arial", 9, "bold"), padx=12, pady=10)
    fr_gest.pack(fill="x", pady=(0, 10))
    fr_g1 = tk.Frame(fr_gest, bg=self.COLOR_WIDGET_BG)
    fr_g1.pack(fill="x")
    _mk_u(fr_g1, "aggiungi", "Nuovo utente",    _aggiungi_utente,  "#98C379")
    _mk_u(fr_g1, "delete",   "Elimina utente",  _elimina_utente,   self.COLOR_ORANGE)
    ttk.Separator(fr_gest, orient="horizontal").pack(fill="x", pady=(8, 6))
    tk.Label(fr_gest, text="Copia dati tra profili:",
             bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
             font=("Arial", 8, "italic")).pack(anchor="w", pady=(0, 4))
    fr_g2 = tk.Frame(fr_gest, bg=self.COLOR_WIDGET_BG)
    fr_g2.pack(fill="x")
    _mk_u(fr_g2, "report", "Generico → Utente", _copia_da_generico)
    _mk_u(fr_g2, "report", "Utente → Generico", _copia_a_generico)
    tk.Label(fr_u_right, text="Tutti i profili",
             bg=self.COLOR_WIDGET_BG, fg=self.COLOR_HIGHLIGHT,
             font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 6))
    fr_tv_u = tk.Frame(fr_u_right, bg=self.COLOR_WIDGET_BG)
    fr_tv_u.pack(fill="both", expand=True)
    vsb_u = ttk.Scrollbar(fr_tv_u, orient="vertical", style="Vertical.TScrollbar")
    vsb_u.pack(side="right", fill="y")
    tv_utenti = ttk.Treeview(fr_tv_u,
                      columns=("nome", "file", "cartella"),
                      show="headings",
                      style="Treeview",
                      yscrollcommand=vsb_u.set,
                      height=12,
                      selectmode='browse')
    vsb_u.config(command=tv_utenti.yview)
    tv_utenti.pack(fill="both", expand=True)
    for col, lbl, w in [("nome","Nome profilo",140),
                 ("file","File presenti",100),
                 ("cartella","Percorso",400)]:
        tv_utenti.heading(col, text=lbl, anchor="w")
        tv_utenti.column(col, width=w, anchor="w")
    tv_utenti.tag_configure("attivo", foreground=self.COLOR_HIGHLIGHT,
                     font=("Arial", 9, "bold"))
    def _popola_tv_utenti():
        tv_utenti.delete(*tv_utenti.get_children())
        for nome in _get_utenti():
            if nome == "Generico":
                cartella_disp = DB_DIR
            else:
                cartella_disp = os.path.join(UTENTI_DIR, nome)
            n_file = sum(1 for f in FILE_KEYS
                         if os.path.exists(_path_for(nome, f)))
            tag = ("attivo",) if nome == _utente_corrente else ()
            tv_utenti.insert("", "end",
                     values=(nome, f"{n_file}/{len(FILE_KEYS)}", cartella_disp),
                     tags=tag)
    def _on_tv_utenti_select(event):
        sel = tv_utenti.selection()
        if sel:
            nome = tv_utenti.item(sel[0], "values")[0]
            utente_var.set(nome)
            _aggiorna_info_utente()
    tv_utenti.bind("<<TreeviewSelect>>", _on_tv_utenti_select)
    utente_var.trace_add("write", _aggiorna_info_utente)
    _aggiorna_info_utente()
    _popola_tv_utenti()

    bot_bar = tk.Frame(popup, bg=self.COLOR_WIDGET_BG, highlightthickness=0)
    bot_bar.pack(fill="x", padx=10, pady=(10, 15))
    def _mk_btn(ico_key, testo, comando, colore=None):
        img = self.icone_gui.get(ico_key)
        fg  = colore or self.TEXT_COLOR
        lbl = tk.Label(bot_bar, text=f" {testo}", image=img, compound="left",
            cursor="hand2", font=("Arial", 9, "bold"), padx=10, pady=5,
            bg=self.COLOR_WIDGET_BG, fg=fg)
        if img: lbl.image = img
        lbl.pack(side="left", padx=5)
        lbl.bind("<Button-1>", lambda e: comando())
    _mk_btn("salva",      "Salva",        _salva_piano,        "#98c379")
    _mk_btn("report",     "Esporta PDF",  _esporta_pdf)
    _mk_btn("stampa",     "Stampa",       _stampa)
    _mk_btn("sparkles_B", "Consulta AI",  _consulta_ai,        self.COLOR_HIGHLIGHT)
    _mk_btn("report", "Confronta settimane", _confronta_settimane)
    _mk_btn("reset",      "Ripristina",   _ripristina_default)
    _mk_btn("aggiungi",    "Nuovo alimento",    _apri_form_custom,  "#98C379")
    _mk_btn("delete", "Elimina custom",    _elimina_custom,    self.COLOR_ORANGE)
    img_c2 = self.icone_gui.get("chiudi")
    btn_close = tk.Label(bot_bar, text=" Chiudi", image=img_c2, compound="left",
        bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR, cursor="hand2", 
        font=("Arial", 9, "bold"), padx=10, pady=5)
    if img_c2: btn_close.image = img_c2
    btn_close.pack(side="right", padx=5)
    btn_close.bind("<Button-1>",
        lambda e: [popup.destroy(), setattr(self, '_dieta_popup', None)])
    popup.update_idletasks()
    popup.configure(bg=self.COLOR_WIDGET_BG)
    w, h = 1360, 630
    x = self.winfo_x() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_y() + (self.winfo_height() // 2) - (h // 2)
    popup.geometry(f"{w}x{h}+{x}+{y}")
    popup.minsize(1360, 630)
    popup.deiconify()
    popup.focus_force()
