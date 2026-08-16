#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import datetime
import tkinter as tk
from tkinter import ttk, filedialog
from moduli.modello_spesa import campo

# Esportazione Forzata delle Statistiche in Modalità Giornaliera
def export_giorno_forzato(self):
    old_mode = self.stats_mode.get()
    self.stats_mode.set("giorno")
    self.export_stats()
    self.stats_mode.set(old_mode)

# Generazione di Report Testuale Formattato per Esportazione Statistiche Giornaliere
def export_stats(self):
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    lines = []
    label_width = 20
    desc_width = 30
    value_width = 14
    tipo_width = 10
    conto_width = 16
    metodo_width = 14
    ora_width = 8
    tag_width = 18
    tot_entrate, tot_uscite = 0.0, 0.0
    _agganci_st = {}
    _agganci_uso_st = {}
    try:
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
            _db_p_st = json.load(_pf)
        _id_a_nome_st = {c["id"]: c.get("nome", "") for c in _db_p_st.get("conti", [])}
        for _t in _db_p_st.get("trasferimenti", []):
            if _t.get("da") in ("__spese__", "Contabilità") or _t.get("a") in ("__spese__", "Contabilità"):
                _data_t = _t.get("data", "")
                _imp_t = round(float(_t.get("importo", 0)), 2)
                _tipo_t = "Entrata" if _t.get("da") in ("__spese__", "Contabilità") else "Uscita"
                _cnome = _id_a_nome_st.get(_t.get("a") if _tipo_t == "Entrata" else _t.get("da"), "")
                _agganci_st.setdefault((_data_t, _imp_t, _tipo_t), []).append(_cnome)
    except Exception:
        _agganci_st = {}
    try:
        giorno = datetime.datetime.strptime(self.cal.get_date(), "%d-%m-%Y").date()
    except Exception:
        giorno = datetime.date.today()
    spese = self.spese.get(giorno, []) or self.spese.get(giorno.strftime("%d-%m-%Y"), [])
    header = f"{'Categoria':<{label_width}} {'Descrizione':<{desc_width}} {'Importo (€)':>{value_width}}  {'Tipo':<{tipo_width}} {'Conto':<{conto_width}} {'Metodo':<{metodo_width}} {'Ora':<{ora_width}} {'Tag':<{tag_width}}"
    sep = "─" * len(header)
    lines.append("═" * len(header))
    lines.append(f"{('Riepilogo Giornaliero - ' + giorno.strftime('%d-%m-%Y')).center(len(header))}")
    lines.append("═" * len(header))
    lines.append("")
    lines.append(header)
    lines.append(sep)
    if not spese:
        lines.append("Nessuna spesa trovata per il giorno selezionato.")
    else:
        for entry in spese:
            cat = campo(entry, "categoria", "")
            desc = campo(entry, "descrizione", "")
            imp = campo(entry, "importo", 0.0)
            tipo = campo(entry, "tipo", "")
            _key_st = (giorno.strftime("%d-%m-%Y"), round(float(imp), 2), tipo)
            _lista_conti = _agganci_st.get(_key_st, [])
            _conto_espl_st = campo(entry, "conto", "")
            if _conto_espl_st:
                nome_conto = _conto_espl_st
            else:
                _uso = _agganci_uso_st.get(_key_st, 0)
                nome_conto = _lista_conti[_uso] if _uso < len(_lista_conti) else ""
                _agganci_uso_st[_key_st] = _uso + 1
            metodo_val = campo(entry, "metodo_pagamento", "")
            ora_val = campo(entry, "ora", "")
            tag_val = " ".join(campo(entry, "hashtag", []))
            lines.append(f"{cat:<{label_width}.{label_width}} {desc:<{desc_width}.{desc_width}} {imp:>{value_width}.2f}  {tipo:<{tipo_width}} {nome_conto:<{conto_width}.{conto_width}} {metodo_val:<{metodo_width}.{metodo_width}} {ora_val:<{ora_width}.{ora_width}} {tag_val:<{tag_width}.{tag_width}}")
            if tipo == "Entrata":
                tot_entrate += imp
            else:
                tot_uscite += imp
    lines.append(sep)
    diff = tot_entrate - tot_uscite
    lines.append(f"{'Totale Entrate:':<{label_width}} {tot_entrate:>{value_width}.2f}")
    lines.append(f"{'Totale Uscite:':<{label_width}} {tot_uscite:>{value_width}.2f}")
    lines.append(f"{'Differenza:':<{label_width}} {diff:>{value_width}.2f} €")
    lines.append("═" * len(header))
    filename = f"Riepilogo_Giorno_{giorno.strftime('%d-%m-%Y')}.txt"
    self.show_export_preview("\n".join(lines), default_filename=filename)

# Generazione di Report Mensile Dettagliato con Ripartizione Giornaliera
def export_month_detail(self):
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO

    ref = self.stats_refdate
    month = ref.month
    year = ref.year
    monthname = self.get_month_name(month)
    oggi = datetime.date.today()
    tot_entrate, tot_uscite = 0.0, 0.0
    cat_spese = {}
    cat_conteggi = {}
    _agganci_st = {}
    _agganci_uso_st = {}
    try:
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
            _db_p_st = json.load(_pf)
        _id_a_nome_st = {c["id"]: c.get("nome", "") for c in _db_p_st.get("conti", [])}
        for _t in _db_p_st.get("trasferimenti", []):
            if _t.get("da") in ("__spese__", "Contabilità") or _t.get("a") in ("__spese__", "Contabilità"):
                _data_t = _t.get("data", "")
                _imp_t = round(float(_t.get("importo", 0)), 2)
                _tipo_t = "Entrata" if _t.get("da") in ("__spese__", "Contabilità") else "Uscita"
                _cnome = _id_a_nome_st.get(_t.get("a") if _tipo_t == "Entrata" else _t.get("da"), "")
                _agganci_st.setdefault((_data_t, _imp_t, _tipo_t), []).append(_cnome)
    except Exception:
        _agganci_st = {}
    days_in_month = [
        d for d in sorted(self.spese.keys())
        if d.year == year and d.month == month
    ]
    tutti_movimenti = []
    for d in days_in_month:
        for entry in self.spese.get(d, []):
            if not self.considera_ricorrenze_var.get() and d > oggi:
                continue
            cat = campo(entry, "categoria", "")
            desc = campo(entry, "descrizione", "")
            imp = campo(entry, "importo", 0.0)
            tipo = campo(entry, "tipo", "")
            categoria = str(cat) if cat else "Varie"
            importo_v = float(imp)
            _key_st = (d.strftime("%d-%m-%Y"), round(importo_v, 2), tipo)
            _lista_conti = _agganci_st.get(_key_st, [])
            _conto_espl_st = campo(entry, "conto", "")
            if _conto_espl_st:
                nome_conto = _conto_espl_st
            else:
                _uso = _agganci_uso_st.get(_key_st, 0)
                nome_conto = _lista_conti[_uso] if _uso < len(_lista_conti) else ""
                _agganci_uso_st[_key_st] = _uso + 1
            metodo_mov = campo(entry, "metodo_pagamento", "")
            ora_mov = campo(entry, "ora", "")
            tag_mov = " ".join(campo(entry, "hashtag", []))
            tutti_movimenti.append((d, categoria, desc, tipo, importo_v, nome_conto, metodo_mov, ora_mov, tag_mov))
            if tipo == "Entrata":
                tot_entrate += importo_v
            else:
                tot_uscite += importo_v
                cat_spese[categoria] = cat_spese.get(categoria, 0.0) + importo_v
                cat_conteggi[categoria] = cat_conteggi.get(categoria, 0) + 1
    lines = []
    lines.append("═" * 96)
    lines.append(f"{('RIEPILOGO MENSILE - ' + monthname.upper() + ' ' + str(year)).center(96)}")
    lines.append("═" * 96 + "\n")
    if not tutti_movimenti:
        lines.append("Nessuna spesa o movimento registrato in questo mese.\n")
    else:
        saldo_finale = tot_entrate - tot_uscite
        lines.append(f" • ENTRATE: {tot_entrate:>12.2f} €")
        lines.append(f" • USCITE:  {tot_uscite:>12.2f} €")
        lines.append(f" • SALDO:   {saldo_finale:>12.2f} €" + "\n")
        lines.append("═" * 96)
        lines.append(f"{'SPESE RIPARTITE PER CATEGORIA'.center(96)}")
        lines.append("═" * 96)
        lines.append(f" {'Categoria':<22}{'Voci':<8}{'Totale (€)':>14}{'Perc. (%)':>12}")
        lines.append("─" * 96)
        if cat_spese:
            for cat in sorted(cat_spese, key=cat_spese.get, reverse=True):
                importo_cat = cat_spese[cat]
                conteggio = cat_conteggi[cat]
                percentuale = (importo_cat / tot_uscite * 100) if tot_uscite > 0 else 0
                lines.append(f" {cat:<22.22}{conteggio:<8}{importo_cat:>12.2f} €{percentuale:>10.1f} %")
        else:
            lines.append(" Nessuna uscita registrata nel mese.")
        lines.append("\n" + "═" * 146)
        lines.append(f"{'DETTAGLIO MOVIMENTI'.center(146)}")
        lines.append("═" * 146)
        lines.append(f"{'Data':<11}{'Categoria':<18}{'Descrizione':<38}{'Tipo':<10}{'Importo':>11}  {'Conto':<16}{'Metodo':<14}{'Ora':<8}{'Tag':<18}")
        lines.append("─" * 146)
        tutti_movimenti.sort(key=lambda x: x[0])
        for mov in tutti_movimenti:
            data_mov, cat_mov, desc_mov, tipo_mov, imp_mov, conto_mov, metodo_mov, ora_mov, tag_mov = mov
            data_str = data_mov.strftime('%d/%m/%Y')
            segno = "+" if tipo_mov == "Entrata" else "-"
            imp_str = f"{segno}{imp_mov:.2f}"
            lines.append(f"{data_str:<11}{cat_mov:<18.18}{desc_mov:<38.38}{tipo_mov:<10}{imp_str:>11}  {conto_mov:<16.16}{metodo_mov:<14.14}{ora_mov:<8.8}{tag_mov:<18.18}")
        lines.append("─" * 146)
        lines.append(f"Totale movimenti: {len(tutti_movimenti)}\n")
    lines.append(f"Report generato il {oggi.strftime('%d/%m/%Y')} da OrbitaCasa.\n")
    now = datetime.date.today()
    month_str = now.strftime("%m-%Y")
    filename = f"Riepilogo_Mese_{month_str}.txt"
    self.show_export_preview("\n".join(lines), default_filename=filename)

# Esportazione di un Report Annuale Dettagliato (Matrice Categoria vs. Mese)
def export_anno_dettagliato(self):
    try:
        year = int(self.estratto_year_var.get())
    except Exception:
        year = datetime.date.today().year

    mesi = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu",
            "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
    label_width = 22
    categorie = sorted(
        set(
            campo(entry, "categoria", "")
            for sp in self.spese.values()
            for entry in sp
        ).union(self.categorie)
    )
    tot_entrate_mese = [0.0] * 12
    tot_uscite_mese = [0.0] * 12
    cat_entrate = {cat: [0.0] * 12 for cat in categorie}
    cat_uscite = {cat: [0.0] * 12 for cat in categorie}
    tot_entrate_anno = 0.0
    tot_uscite_anno = 0.0
    oggi = datetime.date.today()

    def date_from_key(d):
        if isinstance(d, datetime.date):
            return d
        try:
            return datetime.datetime.strptime(d, "%d-%m-%Y").date()
        except Exception:
            return None

    for d, sp in self.spese.items():
        d2 = date_from_key(d)
        if d2 and d2.year == year:
            m = d2.month - 1
            for entry in sp:
                if hasattr(self, "considera_ricorrenze_var") and not self.considera_ricorrenze_var.get():
                    if year == oggi.year:
                        if d2 > oggi:
                            continue
                cat = campo(entry, "categoria", "")
                desc = campo(entry, "descrizione", "")
                imp = campo(entry, "importo", 0.0)
                tipo = campo(entry, "tipo", "")
                if tipo == "Entrata":
                    tot_entrate_mese[m] += imp
                    tot_entrate_anno += imp
                    cat_entrate[cat][m] += imp
                else:
                    tot_uscite_mese[m] += imp
                    tot_uscite_anno += imp
                    cat_uscite[cat][m] += imp

    def format_row(label, values):
        label_fmt = f"{label:<{label_width}.{label_width}}"
        numeri = "".join(f"{v:10.2f}" for v in values)
        return f"{label_fmt}{numeri}{sum(values):12.2f}"

    header = f"{'Categoria':<{label_width}}" + "".join(f"{m:>10}" for m in mesi) + f"{'Totale':>12}"
    sep = "─" * len(header)
    lines = []
    lines.append("═" * len(header))
    lines.append(f"{('RIEPILOGO ENTRATE/USCITE ANNO ' + str(year)).center(len(header))}")
    lines.append("═" * len(header))
    lines.append("")
    lines.append(header)
    lines.append(sep)
    lines.append("")
    lines.append("ENTRATE PER CATEGORIA:")
    lines.append(header)
    for cat in categorie:
        if any(cat_entrate[cat]):
            lines.append(format_row(cat, cat_entrate[cat]))
    lines.append(sep)
    lines.append(format_row("• Totale Entrate", tot_entrate_mese))
    lines.append(sep)
    lines.append("")
    lines.append("USCITE PER CATEGORIA:")
    lines.append(header)
    for cat in categorie:
        if any(cat_uscite[cat]):
            lines.append(format_row(cat, cat_uscite[cat]))
    lines.append("")
    lines.append(sep)
    lines.append(format_row("• Totale Uscite", tot_uscite_mese))
    lines.append("─" * len(header))
    saldo = tot_entrate_anno - tot_uscite_anno
    lines.append(f"{'SALDO FINALE:':<{label_width}}{saldo:>{len(header) - label_width}.2f} €")
    lines.append("═" * len(header))
    text = "\n".join(lines)
    self.show_export_preview(text, default_filename=f"Riepilogo_Anno_{year}.txt")

# Esportazione Report Storico Totale Dettagliato (Matrice Categoria vs. Anno)
def export_storico_totale(self):
    anni_presenti = set()
    def get_year(d):
        if isinstance(d, datetime.date):
            return d.year
        try:
            return datetime.datetime.strptime(d, "%d-%m-%Y").date().year
        except Exception:
            return None

    for d in self.spese.keys():
        y = get_year(d)
        if y:
            anni_presenti.add(y)
    anni_lista = sorted(list(anni_presenti))
    if not anni_lista:
        return
    label_width = 32
    col_width = 10
    categorie = sorted(
        set(
            campo(entry, "categoria", "")
            for sp in self.spese.values()
            for entry in sp
        ).union(self.categorie)
    )
    cat_entrate = {cat: {anno: 0.0 for anno in anni_lista} for cat in categorie}
    cat_uscite = {cat: {anno: 0.0 for anno in anni_lista} for cat in categorie}
    tot_entrate_anno = {anno: 0.0 for anno in anni_lista}
    tot_uscite_anno = {anno: 0.0 for anno in anni_lista}
    for d, sp in self.spese.items():
        y = get_year(d)
        if y in anni_lista:
            for entry in sp:
                cat = campo(entry, "categoria", "")
                imp = campo(entry, "importo", 0.0)
                tipo = campo(entry, "tipo", "")
                if str(tipo).lower() == "entrata":
                    cat_entrate[cat][y] += imp
                    tot_entrate_anno[y] += imp
                else:
                    cat_uscite[cat][y] += imp
                    tot_uscite_anno[y] += imp

    def format_row(label, data_dict):
        label_display = label[:label_width - 1]
        row = f"{label_display:<{label_width}}"
        riga_sum = 0.0
        for anno in anni_lista:
            val = data_dict[anno]
            row += f"{val:>{col_width}.2f}"
            riga_sum += val
        row += f"{riga_sum:>{col_width+2}.2f}"
        return row

    header = f"{'CATEGORIA':<{label_width}}" + "".join(f"{str(a):>{col_width}}" for a in anni_lista) + f"{'TOT.CAT.':>{col_width+2}}"
    sep = "─" * len(header)
    lines = []
    lines.append("═" * len(header))
    lines.append(f"{'MATRICE STORICA CATEGORIE'.center(len(header))}")
    lines.append("═" * len(header))
    lines.append("")
    lines.append("RIEPILOGO ENTRATE:")
    lines.append(header)
    lines.append(sep)
    for cat in categorie:
        if any(cat_entrate[cat].values()):
            lines.append(format_row(cat, cat_entrate[cat]))
    lines.append(sep)
    lines.append(format_row("TOTALI ENTRATE", tot_entrate_anno))
    lines.append("")
    lines.append("RIEPILOGO USCITE:")
    lines.append(header)
    lines.append(sep)
    for cat in categorie:
        if any(cat_uscite[cat].values()):
            lines.append(format_row(cat, cat_uscite[cat]))
    lines.append(sep)
    lines.append(format_row("TOTALI USCITE", tot_uscite_anno))
    lines.append(sep)
    saldo_riga = f"{'SALDO NETTO':<{label_width}}"
    risparmio_totale = 0.0
    for anno in anni_lista:
        s = tot_entrate_anno[anno] - tot_uscite_anno[anno]
        saldo_riga += f"{s:>{col_width}.2f}"
        risparmio_totale += s
    saldo_riga += f"{risparmio_totale:>{col_width+2}.2f}"
    lines.append(saldo_riga)
    lines.append("═" * len(header))
    text = "\n".join(lines)
    self.show_export_preview(text, default_filename="Report_Storico_Allargato.txt")

# Finestra di Anteprima, Salvataggio e Stampa del Report Testuale
def show_export_preview(self, content, default_filename=None):
    import __main__ as _app
    EXPORT_FILES = _app.EXPORT_FILES

    def save_as_pdf():
        import pymupdf as fitz
        now = datetime.date.today()
        filename = (default_filename or f"Riepilogo_Export_{now.day:02d}-{now.month:02d}-{now.year}").replace(".txt", ".pdf")
        if not filename.endswith(".pdf"):
            filename += ".pdf"
        file = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("Documento PDF", "*.pdf")],
                    initialdir=EXPORT_FILES,
                    initialfile=filename,
                    title="Salva come PDF",
                    confirmoverwrite=False,
                    parent=preview)
        if file:
            try:
                doc = fitz.open()
                lines = content.split('\n')
                page_w, page_h = 842, 595
                margin = 40
                font_size = 7
                line_height = font_size + 2
                page = doc.new_page(width=page_w, height=page_h)
                y = margin
                for line in lines:
                    if y > (page_h - margin):
                        page = doc.new_page(width=page_w, height=page_h)
                        y = margin
                    page.insert_text(
                        (margin, y),
                        line,
                        fontname="cour",
                        fontsize=font_size
                    )
                    y += line_height
                doc.save(file)
                doc.close()
                self.show_custom_info("Successo", f"PDF creato correttamente:\n{os.path.basename(file)}")
            except Exception as e:
                self.show_custom_warning("Errore", f"Impossibile creare il PDF: {e}")

    preview = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    preview.transient(self)
    self._export_preview_win = preview
    preview.bind("<Destroy>", lambda e: setattr(self, '_export_preview_win', None) if e.widget is preview else None)
    preview.withdraw()
    preview.title("Anteprima Esportazione Riepilogo")
    preview.attributes("-topmost", True)
    larghezza_finestra = 1300
    altezza_finestra = 600

    def centra_finestra():
        screen_width = preview.winfo_screenwidth()
        screen_height = preview.winfo_screenheight()
        x = (screen_width - larghezza_finestra) // 2
        y = (screen_height - altezza_finestra) // 2
        preview.geometry(f"{larghezza_finestra}x{altezza_finestra}+{x}+{y}")
        preview.minsize(larghezza_finestra, altezza_finestra)
        preview.deiconify()
        preview.lift()
        preview.focus_force()

    preview.after(0, centra_finestra)
    preview.bind("<Escape>", lambda e: preview.destroy())
    container = tk.Frame(preview)
    container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    v_scroll = ttk.Scrollbar(container, orient="vertical")
    h_scroll = ttk.Scrollbar(container, orient="horizontal")
    text = tk.Text(container, wrap="none", font=("Courier new", 10),
                   yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
    v_scroll.config(command=text.yview)
    h_scroll.config(command=text.xview)
    v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
    text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    text.insert("1.0", content)
    text.config(state="disabled")

    def save_file():
        now = datetime.date.today()
        filename = default_filename or f"Riepilogo_Export_{now.day:02d}-{now.month:02d}-{now.year}.txt"
        file = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("File txt", "*.txt")],
            initialdir=EXPORT_FILES,
            initialfile=filename,
            title="Salva Riepilogo",
            confirmoverwrite=False,
            parent=preview)
        if file:
            if os.path.exists(file):
                conferma = self.show_custom_askyesno(
                    "Sovrascrivere file?",
                    f"Il file '{os.path.basename(file)}' \nesiste già. Vuoi sovrascriverlo?"
                )
                if not conferma:
                    return
            with open(file, "w", encoding="utf-8") as f:
                f.write(content)
            preview.destroy()
            self.show_custom_warning("Esportazione completata", f"Riepilogo esportato in {file}")

    bot_f = tk.Frame(preview, bg=self.COLOR_TOPLEVEL)
    bot_f.pack(fill=tk.X, side=tk.BOTTOM, pady=10)
    for testo, ico, cmd, side in [
        ("  Salva TXT ", "salva", save_file, tk.LEFT),
        ("  Salva PDF ", "salva", save_as_pdf, tk.LEFT),
        ("  Stampa ", "stampa", lambda: self._stampa_lista_diretta(content, self.show_custom_warning), tk.LEFT),
        ("  Chiudi ", "chiudi", preview.destroy, tk.RIGHT),
    ]:
        b = tk.Label(bot_f, image=self.icone_gui.get(ico), text=testo,
                     compound="left", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                     cursor="hand2", font=("Arial", 10, "bold"))
        b.pack(side=side, padx=20)
        b.bind("<Button-1>", lambda e, c=cmd: c())
    preview.update()
