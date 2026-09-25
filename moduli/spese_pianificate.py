#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import uuid
import datetime
import tkinter as tk
from tkinter import ttk

MESI_ESTESI = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
               "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
MESI_BREVI = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu",
              "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]

COLORE_PROMEMORIA = "#61AFEF"

def _sp_file():
    import __main__ as _app
    return _app.PIANIFICA_FILE
    
def _carica_sp():
    f = _sp_file()
    try:
        if os.path.exists(f):
            with open(f, "r", encoding="utf-8") as fh:
                dati = json.load(fh)
                if isinstance(dati, dict) and isinstance(dati.get("piani"), list):
                    return _pulisci_piani_scaduti(dati)
    except Exception:
        pass
    return {"piani": []}

def _pulisci_piani_scaduti(dati):
    oggi = datetime.date.today()
    piani_validi = []
    scaduti = False
    for p in dati.get("piani", []):
        try:
            scad = _parse_data(p["data_scadenza"])
        except Exception:
            piani_validi.append(p)
            continue
        if (scad.year, scad.month) <= (oggi.year, oggi.month):
            scaduti = True
        else:
            piani_validi.append(p)
    if scaduti:
        dati = {"piani": piani_validi}
        _salva_sp(dati)
    return dati

def _salva_sp(dati):
    import __main__ as _app
    try:
        os.makedirs(_app.DB_DIR, exist_ok=True)
        percorso = _sp_file()
        percorso_tmp = f"{percorso}.tmp"
        with open(percorso_tmp, "w", encoding="utf-8") as fh:
            json.dump(dati, fh, indent=2, ensure_ascii=False)
        os.replace(percorso_tmp, percorso)
        return True
    except Exception:
        return False

def _fmt(v):
    try:
        return f"€ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "€ 0,00"

def _parse_data(s):
    return datetime.datetime.strptime(s, "%Y-%m-%d").date()

def _sottrai_mesi(data, n):
    y = data.year
    m = data.month - n
    while m <= 0:
        m += 12
        y -= 1
    return datetime.date(y, m, 1)

def _mesi_coperti(inizio, scadenza):
    mesi = []
    y, m = inizio.year, inizio.month
    while (y, m) < (scadenza.year, scadenza.month):
        mesi.append((y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return mesi

def esiste_piano_per_spesa(self, id_spesa):
    if not id_spesa:
        return False
    dati = _carica_sp()
    return any(p.get("id_spesa_collegata") == id_spesa for p in dati["piani"])

def elimina_piano(self, id_piano):
    dati = _carica_sp()
    dati["piani"] = [p for p in dati["piani"] if p.get("id") != id_piano]
    _salva_sp(dati)

def elimina_piano_per_spesa(self, id_spesa):
    if not id_spesa:
        return
    dati = _carica_sp()
    prima = len(dati["piani"])
    dati["piani"] = [p for p in dati["piani"] if p.get("id_spesa_collegata") != id_spesa]
    if len(dati["piani"]) != prima:
        _salva_sp(dati)

def _quote_mensili(importo_totale, mesi):
    if mesi <= 0:
        return []
    base = round(importo_totale / mesi, 2)
    quote = [base] * mesi
    diff = round(importo_totale - base * mesi, 2)
    quote[-1] = round(quote[-1] + diff, 2)
    return quote

def _quota_effettiva(piano, anno, mese):
    try:
        mesi_lista = _mesi_coperti(_parse_data(piano["inizio"]), _parse_data(piano["data_scadenza"]))
    except Exception:
        return None
    if (anno, mese) not in mesi_lista:
        return None
    quote = _quote_mensili(float(piano.get("importo_totale", 0) or 0), len(mesi_lista))
    return quote[mesi_lista.index((anno, mese))]

def piani_puliti(self):
    return _carica_sp()

def ids_spese_pianificate(self):
    dati = _carica_sp()
    return {p.get("id_spesa_collegata") for p in dati.get("piani", []) if p.get("id_spesa_collegata")}

def ottieni_promemoria_mese(self, anno, mese):
    dati = _carica_sp()
    risultato = []
    for p in dati.get("piani", []):
        try:
            scad = _parse_data(p["data_scadenza"])
            inizio = _parse_data(p["inizio"])
        except Exception:
            continue
        mesi_lista = _mesi_coperti(inizio, scad)
        if (anno, mese) in mesi_lista:
            idx = mesi_lista.index((anno, mese))
            quote = _quote_mensili(float(p.get("importo_totale", 0) or 0), len(mesi_lista))
            piano_copia = dict(p)
            piano_copia["quota_mese"] = quote[idx] if idx < len(quote) else piano_copia.get("quota", 0.0)
            risultato.append(piano_copia)
    return risultato

def apri_spalma_spesa(self, entry, data_spesa):
    from moduli.modello_spesa import campo
    import __main__ as _app

    id_spesa = campo(entry, "id_spesa", None)
    if esiste_piano_per_spesa(self, id_spesa):
        self.show_custom_warning("Ammortamento", "Questa spesa è già in un piano di accantonamento.")
        return
    if data_spesa <= datetime.date.today():
        self.show_custom_warning("Ammortamento", "Puoi accantonare solo spese con data futura.")
        return

    nome = campo(entry, "descrizione", "").strip() or campo(entry, "categoria", "Spesa")
    categoria = campo(entry, "categoria", "")
    conto = campo(entry, "conto", "")
    hashtag = campo(entry, "hashtag", []) or []
    metodo_pagamento = campo(entry, "metodo_pagamento", "")
    importo = float(campo(entry, "importo", 0.0))

    oggi = datetime.date.today()
    mesi_max = (data_spesa.year - oggi.year) * 12 + (data_spesa.month - oggi.month)
    if mesi_max < 1:
        self.show_custom_warning(
            "Ammortamento",
            "Questa spesa scade nel mese corrente: non ci sono mesi precedenti disponibili in cui accantonarla."
        )
        return
    mesi_max_tot = min(mesi_max, 36)   # con il mese corrente incluso
    stato = {"max": mesi_max_tot}
    mesi_default = mesi_max_tot

    ico = getattr(self, "icone_gui", {}) or {}
    WIN_W, WIN_H = 480, 330

    win = tk.Toplevel(self)
    win.transient(self)
    win.withdraw()
    win.title("Fondo di ammortamento")
    win.configure(bg=self.COLOR_BACKGROUND)
    win.resizable(False, False)
    win.bind("<Escape>", lambda e: win.destroy())
    self.update_idletasks()
    root_x, root_y = self.winfo_rootx(), self.winfo_rooty()
    root_w, root_h = self.winfo_width(), self.winfo_height()
    pos_x = root_x + (root_w // 2) - (WIN_W // 2)
    pos_y = root_y + (root_h // 2) - (WIN_H // 2)
    win.geometry(f"{WIN_W}x{WIN_H}+{max(0, pos_x)}+{max(0, pos_y)}")

    frm = tk.Frame(win, bg=self.COLOR_BACKGROUND, padx=18, pady=14)
    frm.pack(fill="both", expand=True)
    frm.pack_propagate(False)

    wrap = WIN_W - 60

    lbl_titolo = tk.Label(frm, text=" " + nome, font=("Arial", 11, "bold"),
                           image=ico.get("spesa"), compound="left",
                           bg=self.COLOR_BACKGROUND, fg=self.COLOR_HEADER, anchor="w")
    lbl_titolo.image = ico.get("spesa")
    lbl_titolo.pack(anchor="w", fill="x")

    lbl_importo = tk.Label(frm, text=f" Importo: {_fmt(importo)}", font=("Arial", 9),
                            image=ico.get("saldo"), compound="left",
                            bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR, anchor="w")
    lbl_importo.image = ico.get("saldo")
    lbl_importo.pack(anchor="w", fill="x", pady=(6, 2))

    lbl_scadenza = tk.Label(frm, text=f" Scadenza: {data_spesa.strftime('%d/%m/%Y')}", font=("Arial", 9),
                             image=ico.get("calendario"), compound="left",
                             bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR, anchor="w")
    lbl_scadenza.image = ico.get("calendario")
    lbl_scadenza.pack(anchor="w", fill="x", pady=(0, 12))

    riga_mesi = tk.Frame(frm, bg=self.COLOR_BACKGROUND)
    riga_mesi.pack(anchor="w", fill="x")
    lbl_mesi = tk.Label(riga_mesi, text=" Pianifica in quanti mesi:", font=("Arial", 9, "bold"),
                         image=ico.get("timer"), compound="left",
                         bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR)
    lbl_mesi.image = ico.get("timer")
    lbl_mesi.pack(side="left")
    v_mesi = tk.IntVar(value=mesi_default)
    combo_mesi = ttk.Combobox(riga_mesi, textvariable=v_mesi, values=list(range(1, mesi_max + 1)),
                               width=6, justify="center", state="readonly", style="Border.TCombobox")
    combo_mesi.pack(side="left", padx=(8, 0))
    v_corrente = tk.BooleanVar(value=True)
    chk_corrente = ttk.Checkbutton(frm, text="Includi il mese corrente come primo mese di accantonamento",
                                    variable=v_corrente)
    chk_corrente.pack(anchor="w", pady=(8, 0))
    if mesi_max_tot < 2:
        chk_corrente.state(["disabled"])

    lbl_quota = tk.Label(frm, text="", font=("Arial", 10, "bold"),
                          image=ico.get("saldo"), compound="left",
                          wraplength=wrap, justify="left", anchor="w",
                          bg=self.COLOR_BACKGROUND, fg=self.COLOR_RED)
    lbl_quota.image = ico.get("saldo")
    lbl_quota.pack(anchor="w", fill="x", pady=(10, 4))

    lbl_periodo = tk.Label(frm, text="", font=("Arial", 8, "italic"),
                            image=ico.get("calendario"), compound="left",
                            wraplength=wrap, justify="left", anchor="w",
                            bg=self.COLOR_BACKGROUND, fg="gray")
    lbl_periodo.image = ico.get("calendario")
    lbl_periodo.pack(anchor="w", fill="x")

    def _aggiorna(*_):
        stato["max"] = mesi_max_tot if v_corrente.get() else max(1, mesi_max_tot - 1)
        combo_mesi.config(values=list(range(1, stato["max"] + 1)))
        try:
            n = int(v_mesi.get())
        except Exception:
            n = stato["max"]
        n_clamp = min(max(1, n), stato["max"])
        if n_clamp != n:
            v_mesi.set(n_clamp)
            return
        n = n_clamp
        quote = _quote_mensili(importo, n)
        inizio = _sottrai_mesi(data_spesa, n)
        if n > 1 and quote[-1] != quote[0]:
            lbl_quota.config(text=f" Quota mensile: {_fmt(quote[0])} / mese  (ultima rata: {_fmt(quote[-1])})")
        else:
            lbl_quota.config(text=f" Quota mensile: {_fmt(quote[0])} / mese")
        lbl_periodo.config(text=f" Da {MESI_ESTESI[inizio.month-1]} {inizio.year} "
                                 f"a {MESI_ESTESI[data_spesa.month-1]} {data_spesa.year} (escluso)")

    v_mesi.trace_add("write", _aggiorna)
    v_corrente.trace_add("write", _aggiorna)
    _aggiorna()

    btn_frame = tk.Frame(frm, bg=self.COLOR_BACKGROUND)
    btn_frame.pack(side="bottom", fill="x", pady=(20, 0))

    def _conferma():
        try:
            n = min(max(1, int(v_mesi.get())), stato["max"])
        except Exception:
            n = stato["max"]
        inizio = _sottrai_mesi(data_spesa, n)
        dati = _carica_sp()
        dati["piani"].append({
            "id": uuid.uuid4().hex[:12],
            "nome": nome,
            "descrizione": campo(entry, "descrizione", "").strip(),
            "categoria": categoria,
            "conto": conto,
            "hashtag": hashtag,
            "metodo_pagamento": metodo_pagamento,
            "importo_totale": importo,
            "data_scadenza": data_spesa.isoformat(),
            "inizio": inizio.isoformat(),
            "mesi": n,
            "quota": _quote_mensili(importo, n)[0],
            "id_spesa_collegata": id_spesa,
            "creato_il": datetime.date.today().isoformat(),
        })
        _salva_sp(dati)
        self.show_toast("Piano di accantonamento creato")
        win.destroy()
        if hasattr(self, "update_spese_mese_corrente"):
            self.update_spese_mese_corrente(
                year=getattr(self, "_view_year", None),
                month=getattr(self, "_view_month", None)
            )

    btn_conferma = ttk.Label(btn_frame, image=ico.get("check"), text=" Conferma",
                          compound="left", cursor="hand2", background=self.COLOR_BACKGROUND,
                          foreground=self.TEXT_COLOR, font=("Arial", 9, "bold"))
    btn_conferma.image = ico.get("check")
    btn_conferma.pack(side="left")
    btn_conferma.bind("<Button-1>", lambda e: _conferma())

    btn_annulla = ttk.Label(btn_frame, image=ico.get("chiudi"), text=" Annulla",
                         compound="left", cursor="hand2", background=self.COLOR_BACKGROUND,
                         foreground=self.TEXT_COLOR, font=("Arial", 9, "bold"))
    btn_annulla.image = ico.get("chiudi")
    btn_annulla.pack(side="right")
    btn_annulla.bind("<Button-1>", lambda e: win.destroy())

    win.deiconify()
    win.grab_set()

def on_piano_doppio_click(self, event):
    tree = event.widget
    item_id = tree.focus()
    if not item_id:
        return
    dati = _carica_sp()
    piano = next((p for p in dati.get("piani", []) if p.get("id") == item_id), None)
    if not piano:
        return
    try:
        giorno = _parse_data(piano["data_scadenza"])
    except Exception:
        return
    self.set_stats_mode("giorno")
    if hasattr(self, "cal"):
        self.cal.selection_set(giorno)
        self.cal._sel_date = giorno
        self.stats_refdate = giorno
    self.update_stats()
    if hasattr(self, "estratto_month_var"):
        self.estratto_month_var.set(f"{giorno.month:02d}")
    if hasattr(self, "estratto_year_var"):
        self.estratto_year_var.set(str(giorno.year))
    if hasattr(self, "stats_label"):
        self.stats_label.config(
            text=f"Riepilogo Giornaliero - {giorno.strftime('%d-%m-%Y')}",
            foreground="purple", font=("Arial", 10, "bold"))
        if giorno != datetime.date.today():
            self.blink_label_colors(self.stats_label, "purple", "yellow")
        else:
            self.stop_blink_label_colors(self.stats_label, final_color="purple")
    if hasattr(self, "_win_spese_pianificate") and self._win_spese_pianificate:
        try:
            self._win_spese_pianificate.destroy()
        except Exception:
            pass
        self._win_spese_pianificate = None

def apri_gestione_spese_pianificate(self):
    if hasattr(self, "_win_spese_pianificate") and self._win_spese_pianificate and self._win_spese_pianificate.winfo_exists():
        self._win_spese_pianificate.lift()
        self._win_spese_pianificate.focus_force()
        return

    win = tk.Toplevel(self)
    self._win_spese_pianificate = win
    win.transient(self)
    win.withdraw()
    win.title("Pianifica")
    win.configure(bg=self.COLOR_BACKGROUND)
    w_win, h_win = 1366, 420
    self.update_idletasks()
    root_x, root_y = self.winfo_rootx(), self.winfo_rooty()
    root_w, root_h = self.winfo_width(), self.winfo_height()
    pos_x = root_x + (root_w // 2) - (w_win // 2)
    pos_y = root_y + (root_h // 2) - (h_win // 2)
    win.geometry(f"{w_win}x{h_win}+{max(0, pos_x)}+{max(0, pos_y)}")
    win.minsize(w_win, h_win)
    win.bind("<Escape>", lambda e: win.destroy())

    frm = ttk.Frame(win, padding=10)
    frm.pack(fill="both", expand=True)

    cols = ("nome", "descrizione", "conto", "metodo", "tag", "importo", "quota", "periodo")

    def _cancella_selezionato():
        sel = tree.selection()
        if not sel:
            self.show_toast("Seleziona almeno un piano da eliminare")
            return
        n = len(sel)
        msg = "Eliminare il piano di accantonamento selezionato?" if n == 1 \
            else f"Eliminare i {n} piani di accantonamento selezionati?"
        if self.show_custom_askyesno("Conferma", msg):
            for id_piano in sel:
                elimina_piano(self, id_piano)
            _ricarica()
            self.show_toast("Piano eliminato" if n == 1 else f"{n} piani eliminati")
            if hasattr(self, "update_spese_mese_corrente"):
                self.update_spese_mese_corrente(
                    year=getattr(self, "_view_year", None),
                    month=getattr(self, "_view_month", None)
                )

    ico = getattr(self, "icone_gui", {}) or {}
    btn_frame = ttk.Frame(frm)
    btn_frame.pack(side="bottom", fill="x", pady=(10, 0))

    btn_elimina = ttk.Label(
        btn_frame, image=ico.get("delete"), text=" Elimina piano selezionato",
        compound="left", cursor="hand2", background=self.COLOR_WIDGET_BG,
        foreground=self.TEXT_COLOR, font=("Arial", 9, "bold")
    )
    btn_elimina.image = ico.get("delete")
    btn_elimina.pack(side="left")
    btn_elimina.bind("<Button-1>", lambda e: _cancella_selezionato())

    btn_esporta = ttk.Label(
        btn_frame, image=ico.get("salva"), text=" Esporta/Stampa",
        compound="left", cursor="hand2", background=self.COLOR_WIDGET_BG,
        foreground=self.TEXT_COLOR, font=("Arial", 9, "bold")
    )
    btn_esporta.image = ico.get("salva")
    btn_esporta.pack(side="left", padx=(10, 0))
    btn_esporta.bind("<Button-1>", lambda e: _esporta_piani_testo())
    
    btn_chiudi = ttk.Label(
        btn_frame, image=ico.get("chiudi"), text=" Chiudi",
        compound="left", cursor="hand2", background=self.COLOR_WIDGET_BG,
        foreground=self.TEXT_COLOR, font=("Arial", 9, "bold")
    )
    btn_chiudi.image = ico.get("chiudi")
    btn_chiudi.pack(side="right")
    btn_chiudi.bind("<Button-1>", lambda e: win.destroy())

    img_mouse = ico.get("mouse")
    lbl_hint = ttk.Label(
        btn_frame, text="Doppio clic → Vai alla spesa sulla Dashboard",
        image=img_mouse, compound="right",
        foreground="gray", font=("Arial", 8, "italic")
    )
    if img_mouse:
        lbl_hint.image = img_mouse
    lbl_hint.pack(side="right", padx=10)

    tree_frame = ttk.Frame(frm)
    tree_frame.pack(side="top", fill="both", expand=True)
    vsb = ttk.Scrollbar(tree_frame, orient="vertical")
    tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=14,
                         yscrollcommand=vsb.set)
    vsb.config(command=tree.yview)
    vsb.pack(side="right", fill="y")
    intestazioni = {"descrizione": "Descrizione", "nome": "Categoria", "conto": "Conto",
                     "metodo": "Metodo", "tag": "Tag", "importo": "Importo totale",
                     "quota": "Quota mensile", "periodo": "Periodo accantonamento"}
    for c in cols:
        tree.heading(c, text=intestazioni[c], command=lambda _c=c: self.treeview_sort_column(tree, _c, False))
    tree.column("nome", width=130)
    tree.column("descrizione", width=160)
    tree.column("conto", width=110, anchor="center")
    tree.column("metodo", width=110, anchor="center")
    tree.column("tag", width=110, anchor="center")
    tree.column("importo", width=100, anchor="center")
    tree.column("quota", width=100, anchor="center")
    tree.column("periodo", width=230, anchor="center")
    tree.pack(side="left", fill="both", expand=True)
    tree.tag_configure("orfano", foreground="#E5C07B")
    tree.bind("<Double-1>", lambda e: self.on_piano_doppio_click(e))

    def _esporta_piani_testo():
        piani = sorted(_carica_sp().get("piani", []), key=lambda x: x.get("data_scadenza", ""))
        col_desc, col_nome, col_conto, col_metodo, col_tag, col_imp, col_quota, col_per = 20, 18, 12, 12, 14, 16, 16, 22
        header = (f"{'Categoria':<{col_nome}} {'Descrizione':<{col_desc}} {'Conto':<{col_conto}} "
                  f"{'Metodo':<{col_metodo}} {'Tag':<{col_tag}} {'Importo totale':>{col_imp}} "
                  f"{'Quota mensile':>{col_quota}} {'Periodo':<{col_per}}")
        sep = "─" * len(header)
        lines = ["═" * len(header), "SPESE PIANIFICATE (ACCANTONAMENTO)".center(len(header)),
                  "═" * len(header), "", header, sep]
        tot_importo = tot_quota = 0.0
        if not piani:
            lines.append("Nessun piano di accantonamento presente.")
        else:
            for p in piani:
                importo = float(p.get("importo_totale", 0) or 0)
                oggi_e = datetime.date.today()
                q_eff = _quota_effettiva(p, oggi_e.year, oggi_e.month)
                quota = q_eff if q_eff is not None else float(p.get("quota", 0) or 0)
                tot_importo += importo
                if q_eff is not None:
                    tot_quota += quota
                try:
                    inizio = _parse_data(p["inizio"])
                    scad = _parse_data(p["data_scadenza"])
                    periodo = f"{MESI_BREVI[inizio.month-1]} {inizio.year} → {MESI_BREVI[scad.month-1]} {scad.year}"
                except Exception:
                    periodo = "-"
                desc_p = str(p.get("descrizione", "") or "-")
                nome_p = str(p.get("categoria", "") or p.get("nome", ""))
                conto_p = str(p.get("conto", "") or "-")
                metodo_p = str(p.get("metodo_pagamento", "") or "-")
                tag_p = str(" ".join(p.get("hashtag", []) or []) or "-")
                lines.append(
                    f"{nome_p:<{col_nome}.{col_nome}} {desc_p:<{col_desc}.{col_desc}} {conto_p:<{col_conto}.{col_conto}} "
                    f"{metodo_p:<{col_metodo}.{col_metodo}} {tag_p:<{col_tag}.{col_tag}} {_fmt(importo):>{col_imp}} "
                    f"{_fmt(quota):>{col_quota}} {periodo:<{col_per}.{col_per}}"
                )
        lines.append(sep)
        lines.append(f"Totale piani: {len(piani)}")
        lines.append(f"Totale importo: {_fmt(tot_importo)}")
        lines.append(f"Totale quota del mese corrente: {_fmt(tot_quota)}")
        lines.append("═" * len(header))
        oggi = datetime.date.today()
        self.show_export_preview(
            "\n".join(lines),
            default_filename=f"Spese_Pianificate_{oggi.strftime('%d-%m-%Y')}.txt"
        )

    def _trova_spesa_viva(id_spesa):
        if not id_spesa:
            return None
        from moduli.modello_spesa import campo
        for voci in getattr(self, "spese", {}).values():
            for v in voci:
                if campo(v, "id_spesa", None) == id_spesa:
                    return v
        return None

    def _ricarica():
        from moduli.modello_spesa import campo
        for i in tree.get_children():
            tree.delete(i)
        dati = _carica_sp()
        for p in sorted(dati.get("piani", []), key=lambda x: x.get("data_scadenza", "")):
            try:
                inizio = _parse_data(p["inizio"])
                scad = _parse_data(p["data_scadenza"])
                periodo = f"{MESI_BREVI[inizio.month-1]} {inizio.year} → {MESI_BREVI[scad.month-1]} {scad.year}"
            except Exception:
                periodo = "-"
            spesa_viva = _trova_spesa_viva(p.get("id_spesa_collegata"))
            if spesa_viva is not None:
                categoria_v = campo(spesa_viva, "categoria", "") or (p.get("categoria") or p.get("nome", ""))
                descrizione_v = campo(spesa_viva, "descrizione", "") or p.get("descrizione", "")
                conto_v = campo(spesa_viva, "conto", "") or p.get("conto", "")
                metodo_v = campo(spesa_viva, "metodo_pagamento", "") or p.get("metodo_pagamento", "")
                tag_v = " ".join(campo(spesa_viva, "hashtag", []) or p.get("hashtag", []) or [])
                riga_tags = ()
            else:
                categoria_v = p.get("categoria", "") or p.get("nome", "")
                descrizione_v = (p.get("descrizione", "") or "") + " ⚠️ spesa non trovata"
                conto_v = p.get("conto", "")
                metodo_v = p.get("metodo_pagamento", "")
                tag_v = " ".join(p.get("hashtag", []) or [])
                riga_tags = ("orfano",)
            tree.insert("", "end", iid=p.get("id"), values=(
                categoria_v, descrizione_v,
                conto_v, metodo_v, tag_v,
                _fmt(p.get("importo_totale", 0)), _fmt(p.get("quota", 0)), periodo
            ), tags=riga_tags)

    def _verifica_importi_variati():
        from moduli.modello_spesa import campo
        dati = _carica_sp()
        modificato = False
        for p in dati.get("piani", []):
            spesa_viva = _trova_spesa_viva(p.get("id_spesa_collegata"))
            if spesa_viva is None:
                continue
            try:
                importo_live = round(float(campo(spesa_viva, "importo", 0.0)), 2)
            except Exception:
                continue
            importo_salvato = round(float(p.get("importo_totale", 0) or 0), 2)
            if abs(importo_live - importo_salvato) < 0.01:
                if "_importo_confermato" in p:
                    del p["_importo_confermato"]
                    modificato = True
                continue
            if p.get("_importo_confermato") == importo_live:
                continue
            nome_p = p.get("categoria") or p.get("nome") or "Spesa"
            try:
                ini_d = _parse_data(p["inizio"])
                scad_d = _parse_data(p["data_scadenza"])
                periodo_txt = f"{MESI_BREVI[ini_d.month-1]} {ini_d.year} → {MESI_BREVI[scad_d.month-1]} {scad_d.year}"
            except Exception:
                periodo_txt = "l'intero periodo del piano"
            msg = (
                f"L'importo della spesa pianificata '{nome_p}' è cambiato "
                f"da {_fmt(importo_salvato)} a {_fmt(importo_live)}.\n\n"
                f"Vuoi ricalcolare la quota mensile distribuendo il nuovo importo "
                f"su {periodo_txt}?\n\n"
                f"(Se scegli No, il piano resta invariato con l'importo precedente.)"
            )
            if self.show_custom_askyesno("Importo modificato", msg):
                try:
                    mesi_lista = _mesi_coperti(_parse_data(p["inizio"]), _parse_data(p["data_scadenza"]))
                    n_mesi = len(mesi_lista) or 1
                except Exception:
                    n_mesi = p.get("mesi", 1) or 1
                p["importo_totale"] = importo_live
                p["quota"] = _quote_mensili(importo_live, n_mesi)[0]
                p.pop("_importo_confermato", None)
            else:
                p["_importo_confermato"] = importo_live
            modificato = True
        if modificato:
            _salva_sp(dati)
            _ricarica()
            vy = getattr(self, "_view_year", None)
            vm = getattr(self, "_view_month", None)
            if hasattr(self, "update_stats"):
                self.update_stats()
            if hasattr(self, "update_totalizzatore_anno_corrente"):
                self.update_totalizzatore_anno_corrente(year=vy)
            if hasattr(self, "update_totalizzatore_mese_corrente"):
                self.update_totalizzatore_mese_corrente(year=vy, month=vm)
            if hasattr(self, "update_spese_mese_corrente"):
                self.update_spese_mese_corrente(year=vy, month=vm)

    _ricarica()
    win.deiconify()
    win.after(150, _verifica_importi_variati)
