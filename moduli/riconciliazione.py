#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import difflib
import datetime

from moduli.modello_spesa import campo, metodo_pagamento_pulito, METODI_PAGAMENTO

GIORNI_TOLLERANZA = 5
GIORNI_SCADENZA = 22
SOGLIA_DESC = 0.0

METODI_CREDITO = ("C.Credito 1", "C.Credito 2")

PAROLE_ADDEBITO_CARTA = ("NEXI", "CARTASI", "CARTA SI", "ADDEBITO CARTA", "SALDO CARTA",
                         "ESTRATTO CARTA", "AMERICAN EXPRESS", "AMEX", "MASTERCARD", "VISA",
                         "CARTA DI CREDITO", "CARTA CREDITO", "PAGAMENTO CARTA")

def _norm(s):
    return re.sub(r"[^A-Z0-9 ]+", " ", str(s or "").upper()).strip()

def _sim(a, b):
    a, b = _norm(a), _norm(b)
    if not a or not b:
        return 0.0
    r = difflib.SequenceMatcher(None, a, b).ratio()
    ta, tb = set(a.split()), set(b.split())
    if ta and tb:
        r = max(r, len(ta & tb) / min(len(ta), len(tb)) * 0.9)
    return r

def movimenti_db(spese, conto=None, metodo=None, escludi_metodi=()):
    out = []
    for d, voci in spese.items():
        for v in voci:
            try:
                imp = float(campo(v, "importo", 0.0))
            except Exception:
                continue
            if conto and campo(v, "conto", "") != conto:
                continue
            met = metodo_pagamento_pulito(campo(v, "metodo_pagamento", ""))
            if metodo and met != metodo:
                continue
            if met in escludi_metodi:
                continue
            tipo = str(campo(v, "tipo", "Uscita"))
            out.append({
                "data": d,
                "descrizione": campo(v, "descrizione", ""),
                "categoria": campo(v, "categoria", ""),
                "importo": imp if tipo == "Entrata" else -imp,
                "conto": campo(v, "conto", ""),
                "metodo": met,
                "tag": ", ".join(str(t) for t in (campo(v, "hashtag", []) or [])),
                "id_spesa": campo(v, "id_spesa", ""),
            })
    return out

def riconcilia(righe, db, giorni=GIORNI_TOLLERANZA):
    if not righe:
        return [], [], []

    d_min = min(r["data"] for r in righe)
    d_max = max(r["data"] for r in righe)
    delta = datetime.timedelta(days=giorni)
    delta_scd = datetime.timedelta(days=GIORNI_SCADENZA)
    candidati_db = [m for m in db
                    if (d_min - delta <= m["data"] <= d_max + delta)
                    or ("SCD:" in str(m["descrizione"]).upper()
                        and d_min - delta <= m["data"] <= d_max + delta_scd)]

    coppie = []
    for i, r in enumerate(righe):
        for j, m in enumerate(candidati_db):
            if abs(r["importo"] - m["importo"]) > 0.005:
                continue
            dd = abs((r["data"] - m["data"]).days)
            da_scadenza = False
            if dd > giorni:
                anticipo = (m["data"] - r["data"]).days
                if not ("SCD:" in str(m["descrizione"]).upper() and 0 < anticipo <= GIORNI_SCADENZA):
                    continue
                da_scadenza = True
                dd = giorni
            s = _sim(r["descrizione"], m["descrizione"])
            if s < SOGLIA_DESC:
                continue
            score = 0.6 * s + 0.4 * (1 - dd / (giorni + 1))
            if da_scadenza:
                score -= anticipo * 0.001
            coppie.append((score, i, j))

    coppie.sort(key=lambda t: t[0], reverse=True)
    usate_r, usate_m, abbinate = set(), set(), {}
    for score, i, j in coppie:
        if i in usate_r or j in usate_m:
            continue
        usate_r.add(i)
        usate_m.add(j)
        abbinate[i] = j

    ok = [(righe[i], candidati_db[j]) for i, j in sorted(abbinate.items())]
    mancanti = [r for i, r in enumerate(righe) if i not in abbinate]
    in_piu = [m for j, m in enumerate(candidati_db)
              if j not in usate_m and d_min <= m["data"] <= d_max]
    return ok, mancanti, in_piu

def _mese_precedente(d):
    return (d.year - 1, 12) if d.month == 1 else (d.year, d.month - 1)

def riconcilia_estratto(righe, spese, conto=None, metodo=None, giorni=GIORNI_TOLLERANZA):
    if metodo:
        db = movimenti_db(spese, conto=conto, metodo=metodo)
    else:
        db = movimenti_db(spese, conto=conto, escludi_metodi=METODI_CREDITO)
    ok, mancanti, in_piu = riconcilia(righe, db, giorni)
    esito = {"ok": ok, "mancanti": mancanti, "in_piu": in_piu,
             "addebiti_carta": [], "quadratura": None}

    if righe:
        d_min = min(r["data"] for r in righe)
        d_max = max(r["data"] for r in righe)

    if metodo:
        if righe:
            tot_estratto = round(sum(r["importo"] for r in righe), 2)
            tot_db = round(sum(m["importo"] for m in db if d_min <= m["data"] <= d_max), 2)
            esito["quadratura"] = {"estratto": tot_estratto, "db": tot_db,
                                   "differenza": round(tot_estratto - tot_db, 2)}
        return esito

    veri_mancanti = []
    tutte_credito = None
    for r in mancanti:
        testo = _norm(r["descrizione"])
        if r["importo"] < 0 and any(k in testo for k in PAROLE_ADDEBITO_CARTA):
            if tutte_credito is None:
                tutte_credito = []
                for met in METODI_CREDITO:
                    tutte_credito += movimenti_db(spese, metodo=met)
            anno, mese = _mese_precedente(r["data"])
            atteso = round(sum(m["importo"] for m in tutte_credito
                               if (m["data"].year, m["data"].month) == (anno, mese)), 2)
            esito["addebiti_carta"].append({
                "riga": r, "atteso_db": atteso,
                "differenza": round(r["importo"] - atteso, 2),
                "mese": f"{mese:02d}/{anno}",
            })
        else:
            veri_mancanti.append(r)
    esito["mancanti"] = veri_mancanti
    return esito

def _fmt(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def apri_riconciliazione(self, movimenti):
    import tkinter as tk
    from tkinter import ttk, filedialog
    import __main__ as _app
    righe = [m for m in movimenti if m.get("data") and m.get("importo") is not None]
    if not righe:
        self.show_custom_warning("Controllo estratto", "Nessuna riga utilizzabile nell'estratto.")
        return
        
    win = tk.Toplevel(self)
    win.resizable(True, True)
    win.title("Controllo Estratto Conto")
    win.configure(background=self.COLOR_TOPLEVEL)
    win.minsize(1366, 630)
    larghezza, altezza = 1366, 630
    x = (win.winfo_screenwidth() // 2) - (larghezza // 2)
    y = (win.winfo_screenheight() // 2) - (altezza // 2)
    win.geometry(f"{larghezza}x{altezza}+{x}+{y}")
    win.transient(self)
    win.bind("<Escape>", lambda e: win.destroy())
    
    conti = sorted({campo(v, "conto", "") for voci in self.spese.values() for v in voci} - {""})
    var_conto = tk.StringVar(value="(tutti i conti)")
    var_metodo = tk.StringVar(value="Conto corrente")
    var_filtro = tk.StringVar(value="Tutti")
    var_giorni = tk.IntVar(value=GIORNI_TOLLERANZA)

    barra = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    barra.pack(fill="x", padx=10, pady=8)
    tk.Label(barra, text="Estratto di:", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR).pack(side="left")
    cb_met = ttk.Combobox(barra, textvariable=var_metodo, state="readonly", width=15,
                          style="Border.TCombobox", values=["Conto corrente"] + list(METODI_PAGAMENTO))
    cb_met.pack(side="left", padx=(4, 12))
    tk.Label(barra, text="Conto:", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR).pack(side="left")
    cb_conto = ttk.Combobox(barra, textvariable=var_conto, state="readonly", width=24,
                            style="Border.TCombobox", values=["(tutti i conti)"] + conti)
    cb_conto.pack(side="left", padx=(4, 12))
    tk.Label(barra, text="Tolleranza giorni:", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR).pack(side="left")
    sp = ttk.Combobox(barra, textvariable=var_giorni, state="readonly", width=3,
                      style="Border.TCombobox", values=list(range(0, 11)))
    sp.pack(side="left", padx=(4, 12))
    tk.Label(barra, text="Mostra:", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR).pack(side="left")
    cb_f = ttk.Combobox(barra, textvariable=var_filtro, state="readonly", width=14,
                        style="Border.TCombobox",
                        values=["Tutti", "Mancanti", "In più", "Riconciliati", "Addebiti carta"])
    cb_f.pack(side="left", padx=4)

    frm_riep = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    frm_riep.pack(fill="x", padx=10)
    frm_riep_riga = tk.Frame(frm_riep, bg=self.COLOR_TOPLEVEL)
    frm_riep_riga.pack(fill="x")
    lbl_quad = tk.Label(frm_riep, anchor="w", justify="left", bg=self.COLOR_TOPLEVEL,
                        fg=self.TEXT_COLOR, font=("Arial", 10, "bold"))
    lbl_quad.pack(fill="x")

    cols = ("stato", "data", "descrizione", "importo", "conto", "metodo", "tag", "db")
    frm = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    frm.pack(fill="both", expand=True, padx=10, pady=8)
    tree = ttk.Treeview(frm, columns=cols, show="headings", selectmode="extended")
    for c, t, w, a in (("stato", "Esito", 90, "center"), ("data", "Data", 90, "center"),
                       ("descrizione", "Descrizione", 320, "w"), ("importo", "Importo €", 90, "e"),
                       ("conto", "Conto", 110, "w"), ("metodo", "Metodo", 100, "w"),
                       ("tag", "Tag", 100, "w"),
                       ("db", "Corrispondenza nel database", 320, "w")):
        tree.heading(c, text=t)
        tree.column(c, width=w, minwidth=w, anchor=a, stretch=(c == "db"))
    vsb = ttk.Scrollbar(frm, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    tree.tag_configure("ok", foreground="#50C878")
    tree.tag_configure("manca", foreground="#E06C75")
    tree.tag_configure("piu", foreground="#E5C07B")
    tree.tag_configure("carta", foreground="#61AFEF")

    col_labels = {
        "stato": "Esito", "data": "Data", "descrizione": "Descrizione",
        "importo": "Importo €", "conto": "Conto", "metodo": "Metodo",
        "tag": "Tag", "db": "Corrispondenza nel database"
    }

    def _conv_imp(s):
        s = str(s).strip().replace('€', '').replace('.', '').replace(',', '.').strip()
        try:
            return float(s)
        except ValueError:
            return float('-inf')

    def _conv_data(s):
        s = str(s).strip()
        if not s or s in ("—", "-", "None"):
            return datetime.datetime.min
        for fmt in ('%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%y', '%d/%m/%y'):
            try:
                return datetime.datetime.strptime(s, fmt)
            except ValueError:
                continue
        return datetime.datetime.min

    sort_state = {"col": None, "rev": False}

    def sort_by_column(tv, col, reverse):
        cols = list(tv["columns"])
        try:
            col_index = cols.index(col)
        except ValueError:
            return
        l = []
        for k in tv.get_children(''):
            item_values = tv.item(k, 'values')
            if item_values and len(item_values) > col_index:
                val = item_values[col_index]
                if col == "importo":
                    sort_value = _conv_imp(val)
                elif col == "data":
                    sort_value = _conv_data(val)
                else:
                    sort_value = str(val).lower()
                l.append((sort_value, k))
            else:
                l.append(('', k))
        
        l.sort(key=lambda t: t[0], reverse=reverse)
        sort_state["col"], sort_state["rev"] = col, reverse
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)
        
        for c in cols:
            base_text = col_labels.get(c, c)
            freccia = (" ▼" if reverse else " ▲") if c == col else ""
            tv.heading(c, text=base_text + freccia, command=lambda _c=c: sort_by_column(tv, _c, not reverse if _c == col else False))

    def on_doppio_click_riconciliazione(event):
        if tree.identify_region(event.x, event.y) != "cell":
            return
        item_id = tree.identify_row(event.y)
        if not item_id:
            return
        vals = tree.item(item_id, "values")
        if not vals or len(vals) < 2:
            return
        data_str = vals[1]
        try:
            giorno = datetime.datetime.strptime(data_str, "%d-%m-%Y").date()
        except Exception:
            return
            
        self.set_stats_mode("giorno")
        if hasattr(self, "cal"):
            self.cal.selection_set(giorno)
            self.cal._sel_date = giorno
            self.stats_refdate = giorno
        self.update_stats()
        self.estratto_month_var.set(f"{giorno.month:02d}")
        self.estratto_year_var.set(str(giorno.year))
        self.stats_label.config(
            text=f"Riepilogo Giornaliero - {giorno.strftime('%d-%m-%Y')}",
            foreground="purple", font=("Arial", 10, "bold"))
            
        if giorno != datetime.date.today():
            self.blink_label_colors(self.stats_label, "purple", "yellow")
        else:
            self.stop_blink_label_colors(self.stats_label, final_color="purple")
            
        try:
            event.widget.winfo_toplevel().destroy()
        except Exception:
            pass
            
        desc_ric = str(vals[2])[:20] if len(vals) > 2 else ""
        _id_sp = (getattr(tree, "_metodo_lookup", {}).get(item_id) or {}).get("id_spesa", "")
        self.after(400, lambda: self.seleziona_spesa_in_lista(giorno, desc_ric, _id_sp))

    tree.bind("<Double-1>", on_doppio_click_riconciliazione)

    for c, t, w, a in (("stato", "Esito", 90, "center"), ("data", "Data", 90, "center"),
                       ("descrizione", "Descrizione", 320, "w"), ("importo", "Importo €", 90, "e"),
                       ("conto", "Conto", 110, "w"), ("metodo", "Metodo", 100, "w"),
                       ("tag", "Tag", 100, "w"),
                       ("db", "Corrispondenza nel database", 320, "w")):
        tree.heading(c, text=t, command=lambda _c=c: sort_by_column(tree, _c, False))
        tree.column(c, width=w, minwidth=w, anchor=a, stretch=(c == "db"))
        
    stato = {"mancanti": [], "testata": []}

    def ricalcola(*_):
        conto = var_conto.get()
        conto = None if conto.startswith("(") else conto
        try:
            g = int(var_giorni.get())
        except Exception:
            g = GIORNI_TOLLERANZA
        metodo = var_metodo.get()
        metodo = None if metodo == "Conto corrente" else metodo
        cb_conto.config(state="disabled" if metodo else "readonly")
        if metodo:
            conto = None
        es = riconcilia_estratto(righe, self.spese, conto=conto, metodo=metodo, giorni=g)
        ok, mancanti, in_piu = es["ok"], es["mancanti"], es["in_piu"]
        stato["mancanti"] = mancanti
        tree.delete(*tree.get_children())
        tree._metodo_lookup = {}
        f = var_filtro.get()
        if f in ("Tutti", "Mancanti"):
            for r in sorted(mancanti, key=lambda x: x["data"]):
                tree.insert("", "end", tags=("manca",), values=(
                    "MANCA", r["data"].strftime("%d-%m-%Y"), r["descrizione"], _fmt(r["importo"]), "", "", "", "—"))
        if f in ("Tutti", "Addebiti carta"):
            for ad in es["addebiti_carta"]:
                r = ad["riga"]
                if abs(ad["differenza"]) < 0.01:
                    nota = f'Quadra con le carte di credito {ad["mese"]} nel DB ({_fmt(ad["atteso_db"])} €)'
                else:
                    nota = (f'Carte di credito {ad["mese"]} nel DB: {_fmt(ad["atteso_db"])} € '
                            f'→ differenza {_fmt(ad["differenza"])} €')
                tree.insert("", "end", tags=("carta",), values=(
                    "ADDEB. CARTA", r["data"].strftime("%d-%m-%Y"), r["descrizione"], _fmt(r["importo"]), "", "", "", nota))
        if f in ("Tutti", "In più"):
            for m in sorted(in_piu, key=lambda x: x["data"]):
                iid = tree.insert("", "end", tags=("piu",), values=(
                    "IN PIÙ", m["data"].strftime("%d-%m-%Y"), "—", _fmt(m["importo"]),
                    m["conto"], m["metodo"], m["tag"],
                    (m["categoria"] + " · " if m["categoria"] else "") + m["descrizione"]))
                tree._metodo_lookup[iid] = {"id_spesa": m["id_spesa"]}
        if f in ("Tutti", "Riconciliati"):
            for r, m in ok:
                dd = (r["data"] - m["data"]).days
                nota = (m["categoria"] + " · " if m["categoria"] else "") + m["descrizione"] + (f"  [data DB {m['data'].strftime('%d-%m')}, {dd:+d}g]" if dd else "")
                iid = tree.insert("", "end", tags=("ok",), values=(
                    "OK", r["data"].strftime("%d-%m-%Y"), r["descrizione"], _fmt(r["importo"]),
                    m["conto"], m["metodo"], m["tag"], nota))
                tree._metodo_lookup[iid] = {"id_spesa": m["id_spesa"]}
        if sort_state["col"]:
            sort_by_column(tree, sort_state["col"], sort_state["rev"])
        tot_manc = sum(r["importo"] for r in mancanti)
        tot_piu = sum(m["importo"] for m in in_piu)
        for w in frm_riep_riga.winfo_children():
            w.destroy()

        def _seg(testo, icona=None, sep=True):
            if sep:
                tk.Label(frm_riep_riga, text="   |   ", bg=self.COLOR_TOPLEVEL,
                         fg=self.TEXT_COLOR, font=("Arial", 10, "bold")).pack(side="left")
            img = self.icone_gui.get(icona) if icona else None
            lb = tk.Label(frm_riep_riga, text=(" " + testo) if img else testo, image=img,
                          compound="left", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                          font=("Arial", 10, "bold"))
            lb.image = img
            lb.pack(side="left")

        _seg(f"Estratto: {len(righe)} righe", sep=False)
        _seg(f"{len(ok)} riconciliate", "check")
        _seg(f"{len(mancanti)} mancanti ({_fmt(tot_manc)} €)", "chiudi")
        _seg(f"{len(in_piu)} in più nel DB ({_fmt(tot_piu)} €)", "alert")
        if es["addebiti_carta"]:
            _seg(f"{len(es['addebiti_carta'])} addebiti carta", "ccv")
        if es["quadratura"]:
            q = es["quadratura"]
            lbl_quad.config(text=f"Quadratura {metodo}: estratto {_fmt(q['estratto'])} € — database {_fmt(q['db'])} € "
                                 f"= differenza {_fmt(q['differenza'])} €")
        else:
            lbl_quad.config(text="")
        testata = [f"Estratto di: {var_metodo.get()} | Conto: {var_conto.get()} | "
                   f"Tolleranza: {g}g | Mostra: {var_filtro.get()}",
                   f"Estratto: {len(righe)} righe | {len(ok)} riconciliate | "
                   f"{len(mancanti)} mancanti ({_fmt(tot_manc)} €) | "
                   f"{len(in_piu)} in più nel DB ({_fmt(tot_piu)} €)"]
        if es["addebiti_carta"]:
            testata[1] += f" | {len(es['addebiti_carta'])} addebiti carta"
        if es["quadratura"]:
            testata.append(lbl_quad.cget("text"))
        stato["testata"] = testata

    cb_conto.bind("<<ComboboxSelected>>", ricalcola)
    cb_f.bind("<<ComboboxSelected>>", ricalcola)
    cb_met.bind("<<ComboboxSelected>>", ricalcola)
    sp.bind("<<ComboboxSelected>>", ricalcola)

    def _righe_allineate():
        dati = [[str(x) for x in tree.item(i, "values")] for i in tree.get_children()]
        if not dati:
            return []
        max_c = {"descrizione": 32, "conto": 14, "metodo": 12, "tag": 16, "db": 38}
        def tronca(t, n):
            return t if len(t) <= n else t[:n - 1] + "…"
        dati = [[tronca(x, max_c.get(cols[k], 99)) for k, x in enumerate(d)] for d in dati]
        facoltative = ("conto", "metodo", "tag")
        usa = [k for k, c in enumerate(cols)
               if not (c in facoltative and all(d[k] in ("", "—") for d in dati))]
        larg = {k: max(len(col_labels[cols[k]]), *(len(d[k]) for d in dati)) for k in usa}
        def cella(v, k):
            return v[k].rjust(larg[k]) if cols[k] == "importo" else v[k].ljust(larg[k])
        def fmt(v):
            return " | ".join(cella(v, k) for k in usa).rstrip()
        return [fmt([col_labels[c] for c in cols]), "-+-".join("-" * larg[k] for k in usa)] + [fmt(d) for d in dati]

    def _crea_pdf(dest, lines):
        import pymupdf as fitz
        doc = fitz.open()
        page_w, page_h, margin = 842, 595, 30
        max_len = max((len(l) for l in lines), default=1)
        font_size = max(4, min(7, (page_w - 2 * margin) / (max_len * 0.6)))
        line_height = font_size + 2
        page = doc.new_page(width=page_w, height=page_h)
        y = margin
        for line in lines:
            if y > (page_h - margin):
                page = doc.new_page(width=page_w, height=page_h)
                y = margin
            page.insert_text((margin, y), line, fontname="cour", fontsize=font_size)
            y += line_height
        doc.save(dest)
        doc.close()

    def anteprima_esporta():
        EXPORT_FILES = _app.EXPORT_FILES
        if hasattr(anteprima_esporta, '_win') and anteprima_esporta._win.winfo_exists():
            anteprima_esporta._win.lift()
            anteprima_esporta._win.focus_force()
            return
        lines = _righe_allineate()
        if not lines:
            self.show_custom_warning("Errore", "Nessun dato da esportare.")
            return
        now = datetime.datetime.now()
        import textwrap
        w_tab = max(len(l) for l in lines)
        testata = [r for t in stato["testata"] if t for r in textwrap.wrap(t, width=max(w_tab, 60))]
        testo = (f"CONTROLLO ESTRATTO CONTO - {now.strftime('%d/%m/%Y %H:%M')}\n\n"
                 + "\n".join(testata) + "\n\n"
                 + "\n".join(lines) + "\n")
        nome_base = f"Controllo_Estratto_{now.day:02d}-{now.month:02d}-{now.year}"
        prev_win = tk.Toplevel(win, bg=self.COLOR_TOPLEVEL)
        anteprima_esporta._win = prev_win
        prev_win.withdraw()
        prev_win.title("Esportazione Controllo Estratto")
        prev_win.bind("<Escape>", lambda e: prev_win.destroy())
        prev_win.transient(win)
        def centra_prev():
            if not prev_win.winfo_exists():
                return
            w_a, h_a = 1100, 600
            x = win.winfo_rootx() + (win.winfo_width() // 2) - (w_a // 2)
            y = win.winfo_rooty() + (win.winfo_height() // 2) - (h_a // 2)
            prev_win.geometry(f"{w_a}x{h_a}+{x}+{y}")
            prev_win.minsize(w_a, h_a)
            prev_win.deiconify()
        prev_win.after(0, centra_prev)
        def do_pdf():
            f_path = filedialog.asksaveasfilename(
                defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
                initialdir=EXPORT_FILES, initialfile=nome_base + ".pdf",
                confirmoverwrite=False, parent=prev_win)
            if f_path:
                try:
                    _crea_pdf(f_path, [l.replace("→", "->") for l in testo.split("\n")])
                    self.show_toast("PDF salvato.")
                except Exception as ex:
                    self.show_custom_warning("Errore PDF", str(ex))
        def do_txt():
            f_path = filedialog.asksaveasfilename(
                defaultextension=".txt", filetypes=[("TXT", "*.txt")],
                initialdir=EXPORT_FILES, initialfile=nome_base + ".txt",
                confirmoverwrite=False, parent=prev_win)
            if f_path:
                try:
                    with open(f_path, "w", encoding="utf-8") as fh:
                        fh.write(testo)
                    self.show_toast("File TXT salvato.")
                except Exception as ex:
                    self.show_custom_warning("Errore", f"Impossibile salvare il TXT: {ex}")
        txt_area_frame = tk.Frame(prev_win, bg=self.COLOR_TOPLEVEL)
        txt_area_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        v_scroll = ttk.Scrollbar(txt_area_frame, orient="vertical")
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll = ttk.Scrollbar(prev_win, orient="horizontal")
        txt_area = tk.Text(txt_area_frame, font=("Courier New", 9),
                           bg=self.COLOR_WHITE, fg=self.COLOR_BLACK,
                           wrap="none",
                           yscrollcommand=v_scroll.set,
                           xscrollcommand=h_scroll.set)
        txt_area.pack(fill=tk.BOTH, expand=True)
        v_scroll.config(command=txt_area.yview)
        h_scroll.config(command=txt_area.xview)
        h_scroll.pack(fill=tk.X, padx=10)
        txt_area.insert("1.0", testo)
        txt_area.config(state="disabled")
        bf = tk.Frame(prev_win, bg=self.COLOR_TOPLEVEL)
        bf.pack(fill=tk.X, pady=8)
        for lbl_txt, ico, cmd in [(" PDF", "salva", do_pdf), (" TXT", "salva", do_txt),
                                  (" Stampa", "stampa", lambda: self._stampa_lista_diretta(
                                      testo, self.show_custom_warning))]:
            img = self.icone_gui.get(ico)
            b = ttk.Label(bf, compound="left", image=img, text=lbl_txt,
                          background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                          cursor="hand2", padding=(10, 5))
            b.image = img
            b.pack(side=tk.LEFT, padx=5)
            b.bind("<Button-1>", lambda e, c=cmd: c())
        img_c = self.icone_gui.get("chiudi")
        bc = ttk.Label(bf, compound="left", image=img_c, text=" Chiudi",
                       background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                       cursor="hand2", padding=(10, 5))
        bc.image = img_c
        bc.pack(side=tk.RIGHT, padx=10)
        bc.bind("<Button-1>", lambda e: prev_win.destroy())

    def importa_mancanti():
        sel = stato["mancanti"]
        if not sel:
            self.show_toast("Nessun movimento mancante da importare.")
            return
        metodo = var_metodo.get()
        metodo = "" if metodo == "Conto corrente" else metodo
        win.destroy()
        self.apri_finestra_revisione_universale([dict(r, metodo=metodo) for r in sel])

    bar = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    bar.pack(fill="x", padx=10, pady=(0, 10))
    img_imp = self.icone_gui.get("carica")
    img_chi = self.icone_gui.get("chiudi")
    b1 = ttk.Label(bar, image=img_imp, text=" Importa Mancanti", compound="left",
                   cursor="hand2", background=self.COLOR_WIDGET_BG,
                   foreground=self.TEXT_COLOR, font=("Arial", 10, "bold"), padding=(12, 4))
    b1.image = img_imp
    b1.pack(side="left")
    b1.bind("<Button-1>", lambda e: importa_mancanti())
    img_sal = self.icone_gui.get("salva")
    b3 = ttk.Label(bar, image=img_sal, text=" Esporta", compound="left",
                   cursor="hand2", background=self.COLOR_WIDGET_BG,
                   foreground=self.TEXT_COLOR, font=("Arial", 10, "bold"), padding=(12, 4))
    b3.image = img_sal
    b3.pack(side="left", padx=(10, 0))
    b3.bind("<Button-1>", lambda e: anteprima_esporta())
    b2 = ttk.Label(bar, image=img_chi, text=" Chiudi", compound="left",
                   cursor="hand2", background=self.COLOR_WIDGET_BG,
                   foreground=self.TEXT_COLOR, font=("Arial", 10, "bold"), padding=(12, 4))
    b2.image = img_chi
    b2.pack(side="right")
    b2.bind("<Button-1>", lambda e: win.destroy())

    ricalcola()

def apri_controllo_estratto(self, path=None):
    self.apri_finestra_importa(path=path, solo_controllo=True)
