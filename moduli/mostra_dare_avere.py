#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import datetime
import tkinter as tk
from tkinter import ttk, filedialog

def mostra_dare_avere(self):
    import __main__ as _app
    EXPORT_FILES = _app.EXPORT_FILES

    if hasattr(self, '_dare_avere_popup') and self._dare_avere_popup and self._dare_avere_popup.winfo_exists():
        self._dare_avere_popup.lift()
        self._dare_avere_popup.focus_force()
        return
    debiti = self.sincronizza_fairshare_state()
    popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    popup.title("Fair Share — Dare & Avere per Spesa")
    self._dare_avere_popup = popup
    self._caller_popup = popup
    popup.bind("<Destroy>", lambda e: setattr(self, '_dare_avere_popup', None) if e.widget is popup else None)
    popup.withdraw()
    self.update_idletasks()
    w, h = 1280, 650
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    popup.geometry(f"{w}x{h}+{x}+{y}")
    popup.minsize(w, h)
    popup.transient(self)
    popup.deiconify()
    popup.lift()
    popup.focus_force()
    self._dare_avere_aggiorna = None
    popup.bind("<Escape>", lambda e: popup.destroy())
    mesi_nomi = ["Tutti", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio",
                 "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    oggi  = datetime.date.today()
    anni_db = sorted({d.year for d in self.spese if isinstance(d, datetime.date)}, reverse=True)
    if oggi.year not in anni_db:
        anni_db.insert(0, oggi.year)
    _gestore   = os.path.basename(os.getcwd())
    _nomi_ico  = {}
    for p in self.nomi_partecipanti:
        if p.get("tipo") not in ("persona", "contenitore"):
            continue
        _ico = "❍" if p.get("tipo") == "contenitore" else "✽"
        _nomi_ico[p["nome"]] = f"{_ico} {p['nome']}"
    if self._gestore_partecipa() and _gestore not in _nomi_ico:
        _nomi_ico[_gestore] = f"✽ {_gestore}"
    nomi_parti = ["Tutti"] + sorted(_nomi_ico.values(), key=lambda x: x[2:].lower())
    cat_list   = ["Tutte"] + sorted(self.categorie, key=str.lower)
    stato_list = ["Tutti", "Aperto", "Chiuso"]
    top_frame = ttk.Frame(popup, padding=(10, 8, 10, 4))
    top_frame.pack(fill=tk.X)
    def _lbl(parent, txt):
        ttk.Label(parent, text=txt, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(8, 2))
    anno_var    = tk.StringVar(value="Tutti")
    mese_var    = tk.StringVar(value="Tutti")
    parte_var   = tk.StringVar(value="Tutti")
    cat_var     = tk.StringVar(value="Tutte")
    stato_var   = tk.StringVar(value="Tutti")
    _lbl(top_frame, "Anno:")
    ttk.Combobox(top_frame, textvariable=anno_var,
                 values=["Tutti"] + [str(a) for a in anni_db],
                 state="readonly", style="Border.TCombobox", width=6).pack(side=tk.LEFT)
    _lbl(top_frame, "Mese:")
    ttk.Combobox(top_frame, textvariable=mese_var, values=mesi_nomi,
                 state="readonly", style="Border.TCombobox", width=10).pack(side=tk.LEFT)
    _lbl(top_frame, "Partecipante:")
    ttk.Combobox(top_frame, textvariable=parte_var, values=nomi_parti,
                 state="readonly", style="Border.TCombobox", width=18).pack(side=tk.LEFT)
    _lbl(top_frame, "Categoria:")
    ttk.Combobox(top_frame, textvariable=cat_var, values=cat_list,
                 state="readonly", style="Border.TCombobox", width=18).pack(side=tk.LEFT)
    _lbl(top_frame, "Stato:")
    ttk.Combobox(top_frame, textvariable=stato_var, values=stato_list,
                 state="readonly", style="Border.TCombobox", width=8).pack(side=tk.LEFT)
    tk.Label(top_frame,
             text="💡 Doppio click su una riga = segna pagato / annulla pagamento",
             bg=self.COLOR_TOPLEVEL, fg="#888888",
             font=("Arial", 8)).pack(side=tk.LEFT)
    tree_frame = ttk.Frame(popup)
    tree_frame.pack(fill=tk.X, padx=10, pady=(6, 2))
    vsb = ttk.Scrollbar(tree_frame, orient="vertical", style="Vertical.TScrollbar")
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    cols   = ("Data", "Categoria", "Descrizione", "Tot €", "Quota €",
              "Partecipante", "Pagato", "Data Pagam.", "Stato")
    widths = (90,     110,          220,            80,     80,
              130,         70,       100,            70)
    tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                        height=15, yscrollcommand=vsb.set)
    tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
    vsb.config(command=tree.yview)
    for col, w_ in zip(cols, widths):
        tree.heading(col, text=col, command=lambda c=col: self.treeview_sort_column(tree, c, False))
        tree.column(col, width=w_,
                    anchor="w" if col in ("Descrizione", "Partecipante") else "center")
    tree.tag_configure("pagato",  foreground="#98C379")
    tree.tag_configure("nonpag",  foreground="#E06C75")
    tree.tag_configure("chiuso",  foreground="#61AFEF")
    tree.tag_configure("sep",     foreground="#888888", font=("Arial", 7))
    self._bind_tooltip_metodo(tree, col_desc=2)
    riep_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    riep_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(2, 2))
    vsb_riep = ttk.Scrollbar(riep_frame, orient="vertical", style="Vertical.TScrollbar")
    vsb_riep.pack(side=tk.RIGHT, fill=tk.Y)
    lbl_riep = tk.Text(riep_frame, bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                       height=10, borderwidth=0, font=("Courier New", 9),
                       wrap="none", highlightthickness=0, relief="flat",
                       yscrollcommand=vsb_riep.set)
    lbl_riep.pack(fill=tk.BOTH, expand=True)
    vsb_riep.config(command=lbl_riep.yview)
    lbl_riep.tag_config("verde",  foreground="#98C379")
    lbl_riep.tag_config("rosso",  foreground="#E06C75")
    lbl_riep.tag_config("giallo", foreground="#E5C07B")
    lbl_riep.tag_config("neutro", foreground=self.TEXT_COLOR)
    lbl_riep.tag_config("bold",   font=("Courier New", 9, "bold"))
    _debiti_ref = [debiti]
    _row_map = {}
    def aggiorna_tree(*_args):
        nonlocal _row_map
        _row_map = {}
        try:
            _aggiorna_tree_impl()
        except Exception as _ex:
            import traceback; traceback.print_exc()
    def _aggiorna_tree_impl():
        tree.delete(*tree.get_children())
        a_sel  = anno_var.get()
        m_sel  = mese_var.get()
        p_sel  = parte_var.get()
        if p_sel not in ("", "Tutti") and " " in p_sel:
            p_sel = p_sel.split(" ", 1)[1].strip()
        c_sel  = cat_var.get()
        st_sel = stato_var.get()
        m_num  = mesi_nomi.index(m_sel) if m_sel != "Tutti" else 0
        tot_dovuto  = {}
        tot_versato = {}
        tot_debit   = {}
        chi_deve_a_chi = {}
        righe = []
        for deb in _debiti_ref[0]:
            data_str = deb.get("data", "")
            try:
                d_obj = datetime.datetime.strptime(data_str, "%d/%m/%Y").date()
            except Exception:
                continue
            if a_sel != "Tutti" and str(d_obj.year) != a_sel:
                continue
            if m_num > 0 and d_obj.month != m_num:
                continue
            if c_sel != "Tutte" and deb.get("categoria") != c_sel:
                continue
            if st_sel != "Tutti" and deb.get("stato", "aperto").lower() != st_sel.lower():
                continue
            parti = deb.get("partecipanti", [])
            pag   = deb.get("pagamenti", {})
            quota = deb.get("quota", 0.0)
            imp   = deb.get("importo_totale", 0.0)
            stato = deb.get("stato", "aperto")
            cat   = deb.get("categoria", "")
            desc  = deb.get("descrizione", "")
            key   = deb.get("_key", "")
            for nome in parti:
                if p_sel != "Tutti" and nome != p_sel:
                    continue
                info_p  = pag.get(nome, {})
                pagato  = info_p.get("pagato", False)
                data_p  = info_p.get("data") or ""
                paid_ic = "✅" if pagato else "🔴"
                st_ic   = "✅ Chiuso" if stato == "chiuso" else "🟡 Aperto"
                tag     = "pagato" if pagato else "nonpag"
                if stato == "chiuso":
                    tag = "chiuso"
                righe.append((d_obj, data_str, cat, desc, imp, quota,
                              nome, paid_ic, data_p, st_ic, tag, key, pagato))
                if nome not in tot_dovuto:
                    tot_dovuto[nome]  = 0.0
                    tot_versato[nome] = 0.0
                    tot_debit[nome]   = 0.0
                tot_dovuto[nome] += quota
                if pagato:
                    tot_versato[nome] += quota
                else:
                    tot_debit[nome] += quota
                    creditore = deb.get("creditore", "")
                    if creditore and creditore != nome:
                        chiave = (nome, creditore)
                        chi_deve_a_chi.setdefault(chiave, 0.0)
                        chi_deve_a_chi[chiave] += quota
        righe.sort(key=lambda r: r[0])
        for _ri, r in enumerate(righe):
            (d_obj, data_str, cat, desc, imp, quota,
             nome, paid_ic, data_p, st_ic, tag, key, pagato) = r
            row_iid = f"row_{_ri}"
            _row_map[row_iid] = (key, nome)
            tree.insert("", "end",
                        values=(data_str, cat, desc,
                                f"{imp:,.2f} €", f"{quota:,.2f} €",
                                nome, paid_ic, data_p, st_ic),
                        tags=(tag,),
                        iid=row_iid)
        if not righe:
            tree.insert("", "end",
                        values=("—", "Nessun dato",
                                "Nessuna spesa con tag ✽Nome o ❍Nome trovata.",
                                "", "", "", "", "", ""),
                        tags=("sep",))
        if righe:
            tree.insert("", "end",
                        values=("", "", "", "", "", "", "", "", ""),
                        tags=("sep",))
        lbl_riep.config(state="normal")
        lbl_riep.delete("1.0", "end")
        lbl_riep.insert("end",
            f"{'PERSONA':<20} {'DOVUTO':>12} {'VERSATO':>12} {'DEBITO':>12}   SALDO\n",
            "bold")
        lbl_riep.insert("end", "─" * 80 + "\n", "neutro")
        if tot_dovuto:
            for nome in sorted(tot_dovuto.keys()):
                dov = tot_dovuto[nome]
                ver = tot_versato[nome]
                deb = tot_debit[nome]
                sal_tag = "verde" if deb < 0.01 else "rosso"
                lbl_riep.insert("end", f"  {nome:<18} ", "neutro")
                lbl_riep.insert("end", f"{dov:>11,.2f} €  ", "giallo")
                lbl_riep.insert("end", f"{ver:>11,.2f} €  ", "verde")
                lbl_riep.insert("end", f"{deb:>11,.2f} €  ", sal_tag)
                sal_str = "Saldato" if deb < 0.01 else f"Deve {deb:,.2f} EUR"
                lbl_riep.insert("end", sal_str + "\n", sal_tag)
            tot_dov_all = sum(tot_dovuto.values())
            tot_ver_all = sum(tot_versato.values())
            tot_deb_all = sum(tot_debit.values())
            lbl_riep.insert("end", "─" * 80 + "\n", "neutro")
            lbl_riep.insert("end", f"  {'TOTALE':<18} ", "bold")
            lbl_riep.insert("end", f"{tot_dov_all:>11,.2f} €  ", "giallo")
            lbl_riep.insert("end", f"{tot_ver_all:>11,.2f} €  ", "verde")
            lbl_riep.insert("end", f"{tot_deb_all:>11,.2f} €\n",
                            "verde" if tot_deb_all < 0.01 else "rosso")
            if chi_deve_a_chi:
                lbl_riep.insert("end", "\n", "neutro")
                lbl_riep.insert("end", "  CHI DEVE A CHI:\n", "bold")
                for (debitore, creditore), importo in sorted(
                        chi_deve_a_chi.items(), key=lambda x: (x[0][1], x[0][0])):
                    lbl_riep.insert("end", f"  {debitore} → {creditore}: ", "neutro")
                    lbl_riep.insert("end", f"{importo:,.2f} EUR\n", "rosso")
        else:
            lbl_riep.insert("end", "  Nessun dato per i filtri selezionati.\n", "neutro")
        lbl_riep.config(state="disabled")

    def on_double_click(event):
        iid = tree.identify_row(event.y)
        if not iid or iid not in _row_map:
            return
        key, nome = _row_map[iid]
        for deb in _debiti_ref[0]:
            if deb.get("_key") != key:
                continue
            pag = deb.setdefault("pagamenti", {})
            era_pagato = pag.get(nome, {}).get("pagato", False)
            if era_pagato:
                pag[nome] = {"pagato": False, "data": None}
            else:
                pag[nome] = {"pagato": True,
                             "data": datetime.date.today().strftime("%d/%m/%Y"),
                             "sorgente": "manuale"}
            tutti_pag = all(pag.get(n, {}).get("pagato", False)
                            for n in deb.get("partecipanti", []))
            deb["stato"] = "chiuso" if tutti_pag else "aperto"
            break
        self.salva_fairshare_state(_debiti_ref[0])
        aggiorna_tree()
    tree.bind("<Double-1>", on_double_click)
    def _build_export_text():
        sep = "═" * 126
        titolo = (f"FAIR SHARE — DARE & AVERE PER SPESA\n"
                  f"Filtri: Anno={anno_var.get()}  Mese={mese_var.get()}  "
                  f"Partecipante={parte_var.get()}  Categoria={cat_var.get()}  "
                  f"Stato={stato_var.get()}\n")
        header = (f"\n{sep}\n{titolo}{sep}\n"
                  f"{'DATA':<10}  {'CATEGORIA':<15}  {'DESCRIZIONE':<28}  "
                  f"{'TOTALE':>9}  {'QUOTA':>9}  "
                  f"{'PERSONA':<16}  {'PAGATO':<7}  {'DATA PAG.':<10}  STATO\n"
                  f"{'─'*126}\n")
        body = ""
        for iid in tree.get_children():
            v = tree.item(iid, "values")
            if not v[0]:
                continue
            pagato_str = "SI" if str(v[6]) == "✅" else "NO"
            body += (f"{str(v[0]):<10}  {str(v[1]):<15}  {str(v[2])[:28]:<28}  "
                     f"{str(v[3]):>9}  {str(v[4]):>9}  "
                     f"{str(v[5]):<16}  {pagato_str:<7}  {str(v[7]):<10}  {str(v[8])}\n")
        riep_txt = "\n" + "═" * 120 + "\nRIEPILOGO PER PERSONA\n" + "═" * 120 + "\n"
        riep_txt += f"{'PERSONA':<20} {'DOVUTO':>12} {'VERSATO':>12} {'DEBITO RESIDUO':>15}   SALDO\n"
        riep_txt += "─" * 80 + "\n"
        a_sel  = anno_var.get()
        m_sel  = mese_var.get()
        p_sel  = parte_var.get()
        if p_sel not in ("", "Tutti") and " " in p_sel:
            p_sel = p_sel.split(" ", 1)[1].strip()
        c_sel  = cat_var.get()
        st_sel = stato_var.get()
        m_num  = mesi_nomi.index(m_sel) if m_sel != "Tutti" else 0
        tot_d2 = {}; tot_v2 = {}; tot_r2 = {}
        for deb in _debiti_ref[0]:
            data_str = deb.get("data", "")
            try:
                d_obj = datetime.datetime.strptime(data_str, "%d/%m/%Y").date()
            except Exception:
                continue
            if a_sel != "Tutti" and str(d_obj.year) != a_sel: continue
            if m_num > 0 and d_obj.month != m_num: continue
            if c_sel != "Tutte" and deb.get("categoria") != c_sel: continue
            if st_sel != "Tutti" and deb.get("stato","aperto").lower() != st_sel.lower(): continue
            for nome in deb.get("partecipanti", []):
                if p_sel != "Tutti" and nome != p_sel: continue
                q = deb.get("quota", 0.0)
                pagato = deb.get("pagamenti", {}).get(nome, {}).get("pagato", False)
                tot_d2.setdefault(nome, 0.0); tot_d2[nome] += q
                tot_v2.setdefault(nome, 0.0); tot_r2.setdefault(nome, 0.0)
                if pagato:
                    tot_v2[nome] += q
                else:
                    tot_r2[nome] += q
        for nome in sorted(tot_d2.keys()):
            dov = tot_d2[nome]; ver = tot_v2.get(nome,0); deb_r = tot_r2.get(nome,0)
            sal_str = "SALDATO" if deb_r < 0.01 else f"DEVE {deb_r:,.2f} EUR"
            riep_txt += (f"  {nome:<18} {dov:>12,.2f} EUR  "
                         f"{ver:>12,.2f} EUR  {deb_r:>15,.2f} EUR   {sal_str}\n")
        riep_txt += "─" * 80 + "\n"
        tot_all = sum(tot_d2.values())
        ver_all = sum(tot_v2.values())
        ris_all = sum(tot_r2.values())
        riep_txt += (f"  {'TOTALE':<18} {tot_all:>12,.2f} EUR  "
                     f"{ver_all:>12,.2f} EUR  {ris_all:>15,.2f} EUR\n")
        chi2 = {}
        for deb in _debiti_ref[0]:
            data_str2 = deb.get("data", "")
            try:
                d_obj2 = datetime.datetime.strptime(data_str2, "%d/%m/%Y").date()
            except Exception:
                continue
            if a_sel != "Tutti" and str(d_obj2.year) != a_sel: continue
            if m_num > 0 and d_obj2.month != m_num: continue
            if c_sel != "Tutte" and deb.get("categoria") != c_sel: continue
            if st_sel != "Tutti" and deb.get("stato","aperto").lower() != st_sel.lower(): continue
            creditore = deb.get("creditore", "")
            for nome in deb.get("partecipanti", []):
                if p_sel != "Tutti" and nome != p_sel: continue
                if not deb.get("pagamenti", {}).get(nome, {}).get("pagato", False):
                    if creditore and creditore != nome:
                        chi2.setdefault((nome, creditore), 0.0)
                        chi2[(nome, creditore)] += deb.get("quota", 0.0)
        if chi2:
            riep_txt += "\nCHI DEVE A CHI:\n"
            for (debitore, creditore), importo in sorted(
                    chi2.items(), key=lambda x: (x[0][1], x[0][0])):
                riep_txt += f"  {debitore} -> {creditore}: {importo:,.2f} EUR\n"
        return header + body + riep_txt
    def anteprima_esporta():
        if hasattr(anteprima_esporta, '_win') and anteprima_esporta._win.winfo_exists():
            anteprima_esporta._win.lift()
            anteprima_esporta._win.focus_force()
            return
        testo = _build_export_text()
        prev_win = tk.Toplevel(popup, bg=self.COLOR_TOPLEVEL)
        anteprima_esporta._win = prev_win
        prev_win.withdraw()
        prev_win.title("Esportazione Fair Share — Dare & Avere per Spesa")
        prev_win.bind("<Escape>", lambda e: prev_win.destroy())
        prev_win.transient(popup)
        def centra():
            w_a, h_a = 1100, 600
            x = popup.winfo_rootx() + (popup.winfo_width() // 2) - (w_a // 2)
            y = popup.winfo_rooty() + (popup.winfo_height() // 2) - (h_a // 2)
            prev_win.geometry(f"{w_a}x{h_a}+{x}+{y}")
            prev_win.minsize(w_a, h_a)
            prev_win.deiconify()
        prev_win.after(0, centra)
        def do_pdf():
            fname = f"FairShare_DareAvere_{mese_var.get()}_{anno_var.get()}.pdf"
            f_path = filedialog.asksaveasfilename(
                defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
                initialdir=EXPORT_FILES, initialfile=fname,
                confirmoverwrite=False, parent=prev_win)
            if f_path:
                try:
                    import fitz
                    doc = fitz.open()
                    page = doc.new_page(width=842, height=595)
                    page.insert_text((30, 30), testo, fontname="cour", fontsize=7)
                    doc.save(f_path); doc.close()
                    self.show_toast("PDF salvato.")
                except Exception as ex:
                    self.show_custom_warning("Errore PDF", str(ex))
        def do_txt():
            fname = f"FairShare_DareAvere_{mese_var.get()}_{anno_var.get()}.txt"
            f_path = filedialog.asksaveasfilename(
                defaultextension=".txt", filetypes=[("TXT", "*.txt")],
                initialdir=EXPORT_FILES, initialfile=fname,
                confirmoverwrite=False, parent=prev_win)
            if f_path:
                with open(f_path, "w", encoding="utf-8") as fh:
                    fh.write(testo)
                self.show_toast("File TXT salvato.")
        txt_area_frame = tk.Frame(prev_win, bg=self.COLOR_TOPLEVEL)
        txt_area_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        v_scroll = ttk.Scrollbar(txt_area_frame, orient="vertical")
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        txt_area = tk.Text(txt_area_frame, font=("Courier New", 9),
                           bg=self.COLOR_WHITE, fg=self.COLOR_BLACK,
                           wrap="none",
                           yscrollcommand=v_scroll.set)
        txt_area.pack(fill=tk.BOTH, expand=True)
        v_scroll.config(command=txt_area.yview)
        txt_area.insert("1.0", testo)
        txt_area.config(state="disabled")
        bf = tk.Frame(prev_win, bg=self.COLOR_TOPLEVEL)
        bf.pack(fill=tk.X, pady=8)
        for lbl_txt, cmd in [(" PDF", do_pdf), (" TXT", do_txt),
                              (" Stampa", lambda: self._stampa_lista_diretta(
                                  testo, self.show_custom_warning))]:
            img = self.icone_gui.get("salva")
            b = ttk.Label(bf, compound="left", image=img, text=lbl_txt,
                          background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                          cursor="hand2", padding=(10, 5))
            b.pack(side=tk.LEFT, padx=5)
            b.bind("<Button-1>", lambda e, c=cmd: c())
        img_c = self.icone_gui.get("chiudi")
        bc = ttk.Label(bf, compound="left", image=img_c, text=" Chiudi",
                       background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                       cursor="hand2", padding=(10, 5))
        bc.pack(side=tk.RIGHT, padx=10)
        bc.bind("<Button-1>", lambda e: prev_win.destroy())
    btn_frame = ttk.Frame(popup, padding=(10, 2, 10, 8))
    btn_frame.pack(fill=tk.X)
    def _aggiorna_tutto(e=None):
        _debiti_ref[0] = self.sincronizza_fairshare_state()
        aggiorna_tree()
    self._dare_avere_aggiorna = _aggiorna_tutto
    popup.bind("<Destroy>", lambda e: (
        setattr(self, '_dare_avere_popup', None),
        setattr(self, '_dare_avere_aggiorna', None)
    ))
    pulsanti = [
        ("salva",     " Esporta",   lambda e: anteprima_esporta(),                         "LEFT"),
        ("reset",     " Aggiorna",  _aggiorna_tutto,                                       "LEFT"),
        ("utenti",    " Gestisci",  lambda e: self.gestisci_partecipanti(popup),            "LEFT"),
        ("documenti", " Analitico", lambda e: self.mostra_riepilogo_fairshare_periodo(),    "LEFT"),
        ("documenti", " Personali", lambda e: self.popup_personali(),                       "LEFT"),
        ("info",      " Guida",     lambda e: self.mostra_guida_dare_avere(popup),          "LEFT"),
        ("utenti",    " Grafici",   lambda e: self.mostra_grafici_fairshare(
            anno_var.get(), mese_var.get()),                                               "LEFT"),
        ("chiudi",    " Chiudi",    lambda e: popup.destroy(),                              "RIGHT"),
    ]
    for ico, testo, cmd, lato in pulsanti:
        img = self.icone_gui.get(ico)
        btn = ttk.Label(btn_frame, compound="left", image=img,
                        text=testo if img else testo.strip(),
                        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                        cursor="hand2", padding=(10, 5))
        btn.pack(side=tk.LEFT if lato == "LEFT" else tk.RIGHT, padx=4)
        btn.bind("<Button-1>", cmd)
    for cb_widget in top_frame.winfo_children():
        if isinstance(cb_widget, ttk.Combobox):
            cb_widget.bind("<<ComboboxSelected>>", aggiorna_tree)
    try:
        aggiorna_tree()
    except Exception:
        import traceback; traceback.print_exc()

