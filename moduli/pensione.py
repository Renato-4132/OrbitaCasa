#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import datetime
import tkinter as tk
from tkinter import ttk

def _fmt_it(v, spec=",.2f"):
    s = format(v, spec)
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")

TIPI_VERSAMENTO   = ["TFR", "Lavoratore", "Datore di Lavoro", "Volontario"]
TIPI_RISCATTO     = ["Anticipazione", "Riscatto Parziale", "Riscatto Totale", "Trasferimento ad altro fondo"]
TIPI_PIANO        = ["Negoziale", "Aperto", "PIP"]
LIMITE_DEDUCIBILE_ANNUO = 5164.57
ALIQUOTA_PRESTAZIONE_BASE = 0.15
ALIQUOTA_PRESTAZIONE_MIN  = 0.09
RIDUZIONE_ALIQUOTA_ANNUA  = 0.003
COLORE_VERSATO    = "#4A90D9"
COLORE_CONTROVAL  = "#50C878"
COLORE_TFR_TEO    = "#C45E00"


def _key_data_str(s):
    try:
        return datetime.datetime.strptime(s, "%d-%m-%Y").date()
    except Exception:
        return datetime.date.min


def apri_fondo_pensione(self):
    import __main__ as _app
    PENSIONE_FILE = _app.PENSIONE_FILE
    DB_DIR        = _app.DB_DIR
    if hasattr(self, '_win_fondo_pensione') and self._win_fondo_pensione and \
            self._win_fondo_pensione.winfo_exists():
        self._win_fondo_pensione.lift()
        self._win_fondo_pensione.focus_force()
        return

    def _default_db():
        return {
            "anagrafica": {
                "nome_fondo": "", "gestore": "", "comparto": "",
                "tipo": "Negoziale", "data_adesione": "", "note": "",
                "tasso_inflazione_stimato": 2.0,
                "data_pensione": "",
                "versamento_annuo_stimato": 0.0,
                "rendimento_atteso_pct": 3.0,
                "costo_gestione_pct": 1.0,
            },
            "versamenti": [],
            "valorizzazioni": [],
            "riscatti": [],
        }

    def carica_db():
        try:
            if os.path.exists(PENSIONE_FILE):
                with open(PENSIONE_FILE, "r", encoding="utf-8") as f:
                    dati = json.load(f)
                    base = _default_db()
                    base.update(dati)
                    base["anagrafica"] = {**base["anagrafica"], **dati.get("anagrafica", {})}
                    return base
        except Exception:
            pass
        return _default_db()

    def salva_db(dati):
        try:
            os.makedirs(DB_DIR, exist_ok=True)
            with open(PENSIONE_FILE, "w", encoding="utf-8") as f:
                json.dump(dati, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.show_toast(f"Errore salvataggio: {e}")

    db = carica_db()

    def nuovo_id(prefisso, lista):
        ids = {x.get("id", "") for x in lista}
        i = 1
        while f"{prefisso}{i}" in ids:
            i += 1
        return f"{prefisso}{i}"

    win = tk.Toplevel(self)
    self._win_fondo_pensione = win
    win.transient(self)
    win.withdraw()
    win.title("Fondo Pensione")
    win.configure(bg=self.COLOR_BACKGROUND)
    w_win, h_win = 1320, 660
    self.update_idletasks()
    root_x = self.winfo_rootx()
    root_y = self.winfo_rooty()
    root_w = self.winfo_width()
    root_h = self.winfo_height()
    pos_x  = root_x + (root_w // 2) - (w_win // 2)
    pos_y  = root_y + (root_h // 2) - (h_win // 2)
    win.geometry(f"{w_win}x{h_win}+{max(0, pos_x)}+{max(0, pos_y)}")
    win.minsize(w_win, h_win)
    win.bind("<Escape>", lambda e: win.destroy())
    win.deiconify()

    bg = self.COLOR_BACKGROUND
    fg = self.TEXT_COLOR

    def _btn(parent, ico, testo, cmd, side="left", padx=6):
        img = self.icone_gui.get(ico)
        b = tk.Label(parent, image=img, text=f" {testo}", compound="left",
                     bg=bg, fg=fg, cursor="hand2", font=("Arial", 9, "bold"))
        if img:
            b.image = img
        b.pack(side=side, padx=padx, pady=4)
        b.bind("<Button-1>", lambda e: cmd())
        return b

    def _valida_data(s):
        if s == "":
            return True
        parti = s.split("-")
        if len(parti) > 3:
            return False
        limiti = [2, 2, 4]
        for i, p in enumerate(parti):
            if not p.isdigit() and p != "":
                return False
            if len(p) > limiti[i]:
                return False
        return len(s) <= 10

    nb = ttk.Notebook(win)
    nb.pack(fill="both", expand=True, padx=8, pady=(8, 0))
    tab_dash  = tk.Frame(nb, bg=bg)
    tab_anag  = tk.Frame(nb, bg=bg)
    tab_vers  = tk.Frame(nb, bg=bg)
    tab_valor = tk.Frame(nb, bg=bg)
    tab_risc  = tk.Frame(nb, bg=bg)

    def _add_tab(frame, ico_key, testo):
        img = self.icone_gui.get(ico_key)
        if img:
            nb.add(frame, image=img, text=f"  {testo}  ", compound="left")
        else:
            nb.add(frame, text=testo)
    _add_tab(tab_dash,  "report",        "Dashboard")
    _add_tab(tab_anag,  "anagrafica",    "Piano")
    _add_tab(tab_vers,  "saldo",         "Versamenti")
    _add_tab(tab_valor, "grafico_linea", "Valorizzazioni")
    _add_tab(tab_risc,  "reset_campo",   "Riscatti/Anticipazioni")

    bar_bottom = tk.Frame(win, bg=bg)
    bar_bottom.pack(fill=tk.X, side=tk.BOTTOM, pady=(4, 8))
    img_chiudi = self.icone_gui.get("chiudi")
    btn_chiudi = tk.Label(bar_bottom, compound="left", image=img_chiudi,
                          text=" Chiudi" if img_chiudi else "❌ Chiudi",
                          background=bg, foreground=fg,
                          cursor="hand2", padx=15, pady=6, font=("Arial", 9, "bold"))
    if img_chiudi:
        btn_chiudi.image = img_chiudi
    btn_chiudi.pack()
    btn_chiudi.bind("<Button-1>", lambda e: win.destroy())

    def _totali():
        vers = db.get("versamenti", [])
        per_tipo = {t: 0.0 for t in TIPI_VERSAMENTO}
        for v in vers:
            per_tipo[v.get("tipo", "Volontario")] = per_tipo.get(v.get("tipo", "Volontario"), 0.0) + float(v.get("importo", 0))
        tot_versato = sum(per_tipo.values())
        risc = db.get("riscatti", [])
        tot_riscattato = sum(float(r.get("importo", 0)) for r in risc)
        valor = sorted(db.get("valorizzazioni", []), key=lambda x: _key_data_str(x.get("data", "")))
        controvalore = float(valor[-1].get("controvalore", 0)) if valor else 0.0
        rendimento_eur = controvalore + tot_riscattato - tot_versato
        rendimento_pct = (rendimento_eur / tot_versato * 100) if tot_versato > 0 else 0.0
        oggi = datetime.date.today()
        tot_deducibile_anno = sum(
            float(v.get("importo", 0)) for v in vers
            if v.get("tipo") in ("Lavoratore", "Datore di Lavoro", "Volontario")
            and _key_data_str(v.get("data", "")).year == oggi.year
        )
        anni_iscr_oggi = _anni_iscrizione(oggi)
        aliquota_oggi = _aliquota_prestazione(anni_iscr_oggi)
        controvalore_netto_oggi = controvalore * (1 - aliquota_oggi)
        return {
            "per_tipo":            per_tipo,
            "tot_versato":         tot_versato,
            "tot_riscattato":      tot_riscattato,
            "controvalore":        controvalore,
            "ultima_valorizz":     valor[-1] if valor else None,
            "rendimento_eur":      rendimento_eur,
            "rendimento_pct":      rendimento_pct,
            "tot_deducibile_anno": tot_deducibile_anno,
            "anni_iscrizione_oggi":       anni_iscr_oggi,
            "aliquota_prestazione_oggi":  aliquota_oggi,
            "controvalore_netto_oggi":    controvalore_netto_oggi,
        }

    def _confronto_tfr():
        try:
            infl = float(db.get("anagrafica", {}).get("tasso_inflazione_stimato", 2.0)) / 100.0
        except (TypeError, ValueError):
            infl = 0.02
        tasso_annuo = 0.015 + 0.75 * infl
        oggi = datetime.date.today()
        tot_tfr = 0.0
        tot_teorico = 0.0
        for v in db.get("versamenti", []):
            if v.get("tipo") != "TFR":
                continue
            imp = float(v.get("importo", 0))
            d = _key_data_str(v.get("data", ""))
            anni = max((oggi - d).days / 365.25, 0) if d != datetime.date.min else 0
            tot_tfr     += imp
            tot_teorico += imp * ((1 + tasso_annuo) ** anni)
        return tot_tfr, tot_teorico, tasso_annuo

    def _anni_iscrizione(rif=None):
        ades = _key_data_str(db.get("anagrafica", {}).get("data_adesione", ""))
        if ades == datetime.date.min:
            return 0.0
        fine = rif or datetime.date.today()
        return max((fine - ades).days / 365.25, 0.0)

    def _aliquota_prestazione(anni):
        if anni <= 15:
            return ALIQUOTA_PRESTAZIONE_BASE
        riduzione = RIDUZIONE_ALIQUOTA_ANNUA * (anni - 15)
        return max(ALIQUOTA_PRESTAZIONE_BASE - riduzione, ALIQUOTA_PRESTAZIONE_MIN)

    def _proiezione_pensione():
        anag = db.get("anagrafica", {})
        data_pens = _key_data_str(anag.get("data_pensione", ""))
        oggi = datetime.date.today()
        if data_pens == datetime.date.min or data_pens <= oggi:
            return None
        tot = _totali()
        capitale = tot["controvalore"]
        try:
            vers_annuo = float(anag.get("versamento_annuo_stimato", 0.0))
        except (TypeError, ValueError):
            vers_annuo = 0.0
        try:
            rend_pct = float(anag.get("rendimento_atteso_pct", 3.0)) / 100.0
        except (TypeError, ValueError):
            rend_pct = 0.03
        try:
            costo_pct = float(anag.get("costo_gestione_pct", 1.0)) / 100.0
        except (TypeError, ValueError):
            costo_pct = 0.01
        tasso_netto = rend_pct - costo_pct
        anni_mancanti = (data_pens - oggi).days / 365.25
        n_anni_interi = int(anni_mancanti)
        for _ in range(n_anni_interi):
            capitale = capitale * (1 + tasso_netto) + vers_annuo
        frazione = anni_mancanti - n_anni_interi
        capitale += capitale * tasso_netto * frazione + vers_annuo * frazione
        anni_iscr_a_pensione = _anni_iscrizione(data_pens)
        aliquota = _aliquota_prestazione(anni_iscr_a_pensione)
        capitale_netto = capitale * (1 - aliquota)
        return {
            "anni_mancanti":         anni_mancanti,
            "capitale_lordo":        capitale,
            "aliquota_prestazione":  aliquota,
            "capitale_netto":        capitale_netto,
            "tasso_netto_annuo":     tasso_netto,
            "anni_iscrizione":       anni_iscr_a_pensione,
        }

    def _build_lista_crud(parent, titolo, chiave, prefisso, colonne, campi_form, after_change=None):
        for w in parent.winfo_children():
            w.destroy()
        money_keys = {c["key"] for c in campi_form if c["tipo"] == "importo"}
        top = tk.Frame(parent, bg=bg)
        top.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        lf_tree = ttk.LabelFrame(top, text=titolo, padding=6)
        lf_tree.pack(side="left", fill=tk.BOTH, expand=True, padx=(0, 6))
        tb_e = tk.Frame(lf_tree, bg=bg)
        tb_e.pack(fill=tk.X, pady=(0, 4))

        def _esporta_testo():
            lista = sorted(db.get(chiave, []), key=lambda x: _key_data_str(x.get("data", "")))
            larghezze = {c["key"]: max(c["larghezza"] // 8, len(c["label"]) + 2) for c in colonne}
            header = " ".join(f"{c['label']:<{larghezze[c['key']]}}" for c in colonne)
            sep = "─" * len(header)
            lines = ["═" * len(header), titolo.upper().center(len(header)),
                      "═" * len(header), "", header, sep]
            totale = 0.0
            if not lista:
                lines.append("Nessuna voce presente.")
            else:
                for r in lista:
                    riga = []
                    for c in colonne:
                        val = r.get(c["key"], "")
                        if c["key"] in money_keys:
                            imp = float(val or 0)
                            totale += imp
                            val = _fmt_it(imp)
                        w_c = larghezze[c["key"]]
                        riga.append(f"{str(val):<{w_c}.{w_c}}")
                    lines.append(" ".join(riga))
            lines.append(sep)
            lines.append(f"Totale voci: {len(lista)}")
            if money_keys:
                lines.append(f"Totale importi: {_fmt_it(totale)} €")
            lines.append("═" * len(header))
            oggi = datetime.date.today()
            self.show_export_preview("\n".join(lines),
                default_filename=f"{titolo.replace('/', '_').replace(' ', '_')}_{oggi.strftime('%d-%m-%Y')}.txt")

        _btn(tb_e, "salva", "Esporta", _esporta_testo, side="right", padx=10)
        cols = [c["key"] for c in colonne]
        tree = ttk.Treeview(lf_tree, columns=cols, show="headings", height=16, selectmode="browse")
        for c in colonne:
            tree.heading(c["key"], text=c["label"],
                         command=lambda _c=c["key"]: self.treeview_sort_column(tree, _c, False))
            tree.column(c["key"], width=c["larghezza"], anchor=c["anchor"])
        vsb = ttk.Scrollbar(lf_tree, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(fill=tk.BOTH, expand=True)

        lf_form = ttk.LabelFrame(top, text="Dettaglio", padding=10)
        lf_form.pack(side="left", fill=tk.Y, ipadx=4)
        vars_  = {}
        sel_id = [None]
        row_i  = 0
        for campo in campi_form:
            key = campo["key"]
            tk.Label(lf_form, text=campo["label"], font=("Arial", 9, "bold"),
                     bg=bg, fg=fg, anchor="w").grid(row=row_i, column=0, sticky="w", padx=(0, 6), pady=3)
            if campo["tipo"] == "combo":
                v = tk.StringVar(value=campo["valori"][0] if campo["valori"] else "")
                w = ttk.Combobox(lf_form, textvariable=v, values=campo["valori"], state="readonly",
                                 width=campo.get("larghezza", 18), style="Border.TCombobox")
            elif campo["tipo"] == "data":
                v = tk.StringVar(value=datetime.date.today().strftime("%d-%m-%Y"))
                frm_w = tk.Frame(lf_form, bg=bg)
                w = ttk.Entry(frm_w, textvariable=v, width=campo.get("larghezza", 14),
                             validate="key", validatecommand=(lf_form.register(_valida_data), "%P"))
                w.pack(side="left")
                def _apri_cal(e=None, _w=w, _v=v):
                    self.mostra_calendario_popup_semplice(_w, _v)
                img_cal = self.icone_gui.get("calendario")
                lbl_cal = tk.Label(frm_w, image=img_cal, cursor="hand2", bg=bg)
                if img_cal:
                    lbl_cal.image = img_cal
                lbl_cal.pack(side="left", padx=(4, 0))
                lbl_cal.bind("<Button-1>", _apri_cal)
            elif campo["tipo"] == "importo":
                v = tk.StringVar(value="")
                w = ttk.Entry(lf_form, textvariable=v, width=campo.get("larghezza", 14),
                             validate="key", validatecommand=(lf_form.register(lambda s: len(s) <= 12), "%P"))
            else:
                v = tk.StringVar(value="")
                maxchar = campo.get("maxchar", 40)
                w = ttk.Entry(lf_form, textvariable=v, width=campo.get("larghezza", 20),
                             validate="key", validatecommand=(lf_form.register(lambda s, _m=maxchar: len(s) <= _m), "%P"))
            if campo["tipo"] == "data":
                frm_w.grid(row=row_i, column=1, sticky="w", pady=3)
            else:
                w.grid(row=row_i, column=1, sticky="w", pady=3)
            vars_[key] = v
            row_i += 1

        def ricarica():
            tree.delete(*tree.get_children())
            lista = sorted(db.get(chiave, []), key=lambda x: _key_data_str(x.get("data", "")), reverse=True)
            for r in lista:
                valori = [
                    _fmt_it(float(r.get(c["key"], 0))) if c["key"] in money_keys else r.get(c["key"], "")
                    for c in colonne
                ]
                tree.insert("", "end", iid=r["id"], values=valori)

        def reset_form():
            for campo in campi_form:
                key = campo["key"]
                if campo["tipo"] == "data":
                    vars_[key].set(datetime.date.today().strftime("%d-%m-%Y"))
                elif campo["tipo"] == "combo":
                    vars_[key].set(campo["valori"][0] if campo["valori"] else "")
                else:
                    vars_[key].set("")
            sel_id[0] = None
            tree.selection_remove(tree.selection())

        def on_sel(e=None):
            sel = tree.selection()
            if not sel:
                return
            iid = sel[0]
            r = next((x for x in db.get(chiave, []) if x["id"] == iid), None)
            if r:
                for campo in campi_form:
                    key = campo["key"]
                    if campo["tipo"] == "importo":
                        vars_[key].set(f"{float(r.get(key, 0)):.2f}".replace(".", ","))
                    else:
                        vars_[key].set(r.get(key, ""))
                sel_id[0] = iid
        tree.bind("<<TreeviewSelect>>", on_sel)

        def salva():
            dati_riga = {}
            for campo in campi_form:
                key = campo["key"]
                val = vars_[key].get().strip()
                if campo["tipo"] == "importo":
                    try:
                        imp = float(val.replace(",", "."))
                        if imp <= 0:
                            raise ValueError
                    except ValueError:
                        self.show_toast(f"{campo['label']} non valido.")
                        return
                    dati_riga[key] = imp
                elif campo["tipo"] == "data":
                    try:
                        datetime.datetime.strptime(val, "%d-%m-%Y")
                    except ValueError:
                        self.show_toast("Data non valida.")
                        return
                    dati_riga[key] = val
                else:
                    dati_riga[key] = val
            lista = db.setdefault(chiave, [])
            if sel_id[0]:
                for r in lista:
                    if r["id"] == sel_id[0]:
                        r.update(dati_riga)
                        break
            else:
                dati_riga["id"] = nuovo_id(prefisso, lista)
                lista.append(dati_riga)
            salva_db(db)
            ricarica()
            reset_form()
            if after_change:
                after_change()

        def elimina():
            if not sel_id[0]:
                self.show_toast("Seleziona una riga.")
                return
            if not self.show_custom_askyesno("Conferma", "Eliminare la voce selezionata?"):
                return
            db[chiave] = [r for r in db.get(chiave, []) if r["id"] != sel_id[0]]
            salva_db(db)
            ricarica()
            reset_form()
            if after_change:
                after_change()

        btn_f = tk.Frame(lf_form, bg=bg)
        btn_f.grid(row=row_i, column=0, columnspan=3, pady=(10, 0))
        _btn(btn_f, "aggiungi", "Nuovo",   reset_form)
        _btn(btn_f, "salva",    "Salva",   salva)
        _btn(btn_f, "cancella", "Elimina", elimina)
        ricarica()
        return ricarica

    def _build_dashboard():
        for w in tab_dash.winfo_children():
            w.destroy()
        tot = _totali()

        def kpi_box(parent, label, valore, colore=None):
            f = tk.Frame(parent, bg=self.COLOR_WIDGET_BG,
                         highlightbackground=self.COLOR_HIGHLIGHT, highlightthickness=1)
            f.pack(side="left", expand=True, fill="both", padx=3)
            tk.Label(f, text=label, font=("Arial", 8),
                     bg=self.COLOR_WIDGET_BG, fg=fg).pack(pady=(7, 0))
            tk.Label(f, text=valore, font=("Arial", 11, "bold"),
                     bg=self.COLOR_WIDGET_BG, fg=colore or fg).pack(pady=(2, 7))

        frm_kpi1 = tk.Frame(tab_dash, bg=bg)
        frm_kpi1.pack(fill="x", padx=12, pady=(10, 4))
        colore_rend = self.COLOR_GREEN if tot["rendimento_eur"] >= 0 else self.COLOR_RED
        kpi_box(frm_kpi1, "Totale Versato",      f"€ {_fmt_it(tot['tot_versato'])}")
        kpi_box(frm_kpi1, "Controvalore Attuale", f"€ {_fmt_it(tot['controvalore'])}")
        kpi_box(frm_kpi1, "Totale Riscattato",    f"€ {_fmt_it(tot['tot_riscattato'])}")
        kpi_box(frm_kpi1, "Rendimento",
                f"€ {_fmt_it(tot['rendimento_eur'])}  ({tot['rendimento_pct']:.1f}%)", colore_rend)

        frm_kpi2 = tk.Frame(tab_dash, bg=bg)
        frm_kpi2.pack(fill="x", padx=12, pady=4)
        for t in TIPI_VERSAMENTO:
            kpi_box(frm_kpi2, f"Versato — {t}", f"€ {_fmt_it(tot['per_tipo'].get(t, 0))}")

        if tot["tot_deducibile_anno"] > LIMITE_DEDUCIBILE_ANNUO:
            tk.Label(tab_dash,
                     text=f"⚠ Superato il limite deducibile {datetime.date.today().year}: "
                          f"€ {_fmt_it(tot['tot_deducibile_anno'])} versati (lavoratore + datore + volontari) "
                          f"contro un tetto di € {_fmt_it(LIMITE_DEDUCIBILE_ANNUO)}.",
                     font=("Arial", 8, "bold"), bg=bg, fg=self.COLOR_ORANGE,
                     anchor="w").pack(fill="x", padx=12, pady=(6, 0))

        tot_tfr, tot_tfr_teo, tasso_annuo = _confronto_tfr()
        frm_tfr = tk.LabelFrame(tab_dash, text=" Confronto con TFR lasciato in azienda (stima) ",
                                bg=self.COLOR_WIDGET_BG, fg=fg, font=("Arial", 9, "bold"))
        frm_tfr.pack(fill="x", padx=12, pady=(10, 4))
        row_tfr = tk.Frame(frm_tfr, bg=self.COLOR_WIDGET_BG)
        row_tfr.pack(fill="x", padx=8, pady=8)
        diff_tfr = tot_tfr_teo - tot_tfr
        tk.Label(row_tfr,
                 text=f"TFR versato al fondo: € {_fmt_it(tot_tfr)}   |   "
                      f"Rivalutazione teorica in azienda (tasso stimato {tasso_annuo*100:.2f}%/anno): "
                      f"€ {_fmt_it(tot_tfr_teo)}  (+€ {_fmt_it(diff_tfr)})",
                 font=("Arial", 9), bg=self.COLOR_WIDGET_BG, fg=fg, anchor="w", justify="left",
                 wraplength=1200).pack(anchor="w")
        tk.Label(frm_tfr,
                 text="Stima approssimativa: applica 1,5% fisso + 75% dell'inflazione stimata "
                      "(impostabile nella scheda Piano) a ciascun versamento TFR dalla propria data ad oggi. "
                      "Non tiene conto della fiscalità agevolata del fondo pensione né di quella del TFR in azienda.",
                 font=("Arial", 7), bg=self.COLOR_WIDGET_BG, fg="gray",
                 anchor="w", wraplength=1200, justify="left").pack(anchor="w", padx=0, pady=(2, 0))

        frm_graf = tk.LabelFrame(tab_dash, text=" Andamento — Versato Netto vs Controvalore ",
                                 bg=bg, fg=fg, font=("Arial", 9, "bold"))
        frm_graf.pack(fill="both", expand=True, padx=12, pady=(10, 10))
        cvs = tk.Canvas(frm_graf, bg=self.COLOR_WIDGET_BG,
                        highlightbackground=self.COLOR_HIGHLIGHT, highlightthickness=1)
        cvs.pack(fill="both", expand=True, padx=8, pady=8)

        def _dati_andamento():
            valor = sorted(db.get("valorizzazioni", []), key=lambda x: _key_data_str(x.get("data", "")))
            punti = []
            for v in valor:
                d = _key_data_str(v.get("data", ""))
                versato_netto = (
                    sum(float(x.get("importo", 0)) for x in db.get("versamenti", []) if _key_data_str(x.get("data", "")) <= d)
                    - sum(float(x.get("importo", 0)) for x in db.get("riscatti", []) if _key_data_str(x.get("data", "")) <= d)
                )
                punti.append({"data": d, "versato": versato_netto, "controvalore": float(v.get("controvalore", 0))})
            return punti

        def _draw_andamento(event=None):
            cvs.delete("all")
            W = cvs.winfo_width()
            H = cvs.winfo_height()
            punti = _dati_andamento()
            if W < 20 or H < 20:
                return
            if len(punti) < 1:
                cvs.create_text(W // 2, H // 2, text="Aggiungi almeno una valorizzazione per vedere il grafico.",
                                font=("Arial", 9), fill="gray")
                return
            pad_l, pad_r, pad_t, pad_b = 60, 20, 34, 24
            max_v = max(max(p["versato"], p["controvalore"]) for p in punti) or 1.0
            step  = (W - pad_l - pad_r) / max(len(punti) - 1, 1)

            def ty(v):
                return H - pad_b - (v / max_v) * (H - pad_t - pad_b)
            for frac in (0, 0.5, 1.0):
                yy = ty(max_v * frac)
                cvs.create_line(pad_l, yy, W - pad_r, yy, fill="#DDDDDD", dash=(3, 2))
                cvs.create_text(pad_l - 6, yy, text=f"{_fmt_it(max_v * frac, ',.0f')}", anchor="e",
                                font=("Arial", 7), fill="gray")
            for serie, colore in (("versato", COLORE_VERSATO), ("controvalore", COLORE_CONTROVAL)):
                pts = [(pad_l + i * step, ty(p[serie])) for i, p in enumerate(punti)]
                for i in range(len(pts) - 1):
                    cvs.create_line(*pts[i], *pts[i + 1], fill=colore, width=2)
                for i, (x, y) in enumerate(pts):
                    tag = f"{serie}_{i}"
                    cvs.create_oval(x - 3, y - 3, x + 3, y + 3, fill=colore, outline="", tags=tag)
                    p = punti[i]
                    cvs.tag_bind(tag, "<Enter>", lambda e, _p=p, _s=serie: self.show_tooltip(
                        e, f"{_p['data'].strftime('%d/%m/%Y')} — {'Versato netto' if _s == 'versato' else 'Controvalore'}: "
                           f"€ {_fmt_it(_p[_s])}"))
                    cvs.tag_bind(tag, "<Leave>", self.hide_tooltip)
            for i, p in enumerate(punti):
                cvs.create_text(pad_l + i * step, H - 10, text=p["data"].strftime("%m/%y"),
                                font=("Arial", 7), fill=fg)
            leg_y = 6
            leg_font = ("Arial", 7)
            leg_gap = 20
            x = pad_l
            cvs.create_rectangle(x, leg_y, x + 10, leg_y + 8, fill=COLORE_VERSATO, outline="")
            txt1 = cvs.create_text(x + 14, leg_y + 4, text="Versato netto", anchor="w", font=leg_font, fill=fg)
            x1, y1, x2, y2 = cvs.bbox(txt1)
            x = x2 + leg_gap
            cvs.create_rectangle(x, leg_y, x + 10, leg_y + 8, fill=COLORE_CONTROVAL, outline="")
            cvs.create_text(x + 14, leg_y + 4, text="Controvalore", anchor="w", font=leg_font, fill=fg)
        cvs.bind("<Configure>", _draw_andamento)
        win.after(150, _draw_andamento)

    def _build_anagrafica():
        for w in tab_anag.winfo_children():
            w.destroy()
        anag = db.setdefault("anagrafica", _default_db()["anagrafica"])
        frm = ttk.LabelFrame(tab_anag, text="Dati del Piano", padding=14)
        frm.pack(padx=16, pady=(16, 8), anchor="nw")
        v_nome  = tk.StringVar(value=anag.get("nome_fondo", ""))
        v_gest  = tk.StringVar(value=anag.get("gestore", ""))
        v_comp  = tk.StringVar(value=anag.get("comparto", ""))
        v_tipo  = tk.StringVar(value=anag.get("tipo", "Negoziale"))
        v_ades  = tk.StringVar(value=anag.get("data_adesione", ""))
        v_infl  = tk.StringVar(value=f"{float(anag.get('tasso_inflazione_stimato', 2.0)):.2f}".replace(".", ","))
        v_note  = tk.StringVar(value=anag.get("note", ""))
        v_pens       = tk.StringVar(value=anag.get("data_pensione", ""))
        v_vers_stim  = tk.StringVar(value=f"{float(anag.get('versamento_annuo_stimato', 0.0)):.2f}".replace(".", ","))
        v_rend_att   = tk.StringVar(value=f"{float(anag.get('rendimento_atteso_pct', 3.0)):.2f}".replace(".", ","))
        v_costo_gest = tk.StringVar(value=f"{float(anag.get('costo_gestione_pct', 1.0)):.2f}".replace(".", ","))

        tk.Label(frm, text="Nome fondo:", font=("Arial", 9, "bold"), anchor="w",bg=bg, fg=fg).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=5)
        ttk.Entry(frm, textvariable=v_nome, width=30).grid(row=0, column=1, sticky="w", pady=5)
        tk.Label(frm, text="Gestore:", font=("Arial", 9, "bold"), anchor="w",bg=bg, fg=fg).grid(row=1, column=0, sticky="w", padx=(0, 8), pady=5)
        ttk.Entry(frm, textvariable=v_gest, width=30).grid(row=1, column=1, sticky="w", pady=5)
        tk.Label(frm, text="Comparto:", font=("Arial", 9, "bold"), anchor="w",bg=bg, fg=fg).grid(row=2, column=0, sticky="w", padx=(0, 8), pady=5)
        ttk.Entry(frm, textvariable=v_comp, width=30).grid(row=2, column=1, sticky="w", pady=5)
        tk.Label(frm, text="Tipo piano:", font=("Arial", 9, "bold"), anchor="w",bg=bg, fg=fg).grid(row=3, column=0, sticky="w", padx=(0, 8), pady=5)
        ttk.Combobox(frm, textvariable=v_tipo, values=TIPI_PIANO, state="readonly",
                     width=27, style="Border.TCombobox").grid(row=3, column=1, sticky="w", pady=5)
        tk.Label(frm, text="Data adesione:", font=("Arial", 9, "bold"), anchor="w",bg=bg, fg=fg).grid(row=4, column=0, sticky="w", padx=(0, 8), pady=5)
        frm_data = tk.Frame(frm, bg=bg)
        frm_data.grid(row=4, column=1, sticky="w", pady=5)

        ent_ades = ttk.Entry(frm_data, textvariable=v_ades, width=14,
                     validate="key", validatecommand=(frm.register(_valida_data), "%P"))
        ent_ades.pack(side="left")

        img_cal = self.icone_gui.get("calendario")
        lbl_cal = tk.Label(frm_data, image=img_cal, cursor="hand2", bg=bg, fg=fg)
        if img_cal:
            lbl_cal.image = img_cal
        lbl_cal.pack(side="left", padx=(4, 0))
        lbl_cal.bind("<Button-1>", lambda e: self.mostra_calendario_popup_semplice(ent_ades, v_ades))
        tk.Label(frm, text="Inflazione media stimata %/anno:", font=("Arial", 9, "bold"), anchor="w",bg=bg, fg=fg).grid(row=5, column=0, sticky="w", padx=(0, 8), pady=5)
        ttk.Entry(frm, textvariable=v_infl, width=10,
                 validate="key", validatecommand=(frm.register(lambda s: len(s) <= 6), "%P")).grid(row=5, column=1, sticky="w", pady=5)
        tk.Label(frm, text="(usata per il confronto con la rivalutazione del TFR nella scheda Dashboard)",
                 font=("Arial", 7),bg=bg, fg=fg).grid(row=6, column=1, sticky="w")
        tk.Label(frm, text="Note:", font=("Arial", 9, "bold"), anchor="w",bg=bg, fg=fg).grid(row=7, column=0, sticky="w", padx=(0, 8), pady=5)
        ttk.Entry(frm, textvariable=v_note, width=40).grid(row=7, column=1, sticky="w", pady=5)

        frm2 = ttk.LabelFrame(tab_anag, text="Proiezione a Scadenza e Costi", padding=14)
        frm2.pack(padx=16, pady=(0, 16), anchor="nw")
        tk.Label(frm2, text="Data prevista pensionamento:", font=("Arial", 9, "bold"), anchor="w",
                 bg=bg, fg=fg).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=5)
        frm_pens = tk.Frame(frm2, bg=bg)
        frm_pens.grid(row=0, column=1, sticky="w", pady=5)
        ent_pens = ttk.Entry(frm_pens, textvariable=v_pens, width=14,
                     validate="key", validatecommand=(frm2.register(_valida_data), "%P"))
        ent_pens.pack(side="left")
        img_cal2 = self.icone_gui.get("calendario")
        lbl_cal2 = tk.Label(frm_pens, image=img_cal2, cursor="hand2", bg=bg, fg=fg)
        if img_cal2:
            lbl_cal2.image = img_cal2
        lbl_cal2.pack(side="left", padx=(4, 0))
        lbl_cal2.bind("<Button-1>", lambda e: self.mostra_calendario_popup_semplice(ent_pens, v_pens))
        tk.Label(frm2, text="Versamento annuo stimato €:", font=("Arial", 9, "bold"), anchor="w",
                 bg=bg, fg=fg).grid(row=1, column=0, sticky="w", padx=(0, 8), pady=5)
        ttk.Entry(frm2, textvariable=v_vers_stim, width=12,
                 validate="key", validatecommand=(frm2.register(lambda s: len(s) <= 10), "%P")).grid(row=1, column=1, sticky="w", pady=5)
        tk.Label(frm2, text="Rendimento atteso %/anno:", font=("Arial", 9, "bold"), anchor="w",
                 bg=bg, fg=fg).grid(row=2, column=0, sticky="w", padx=(0, 8), pady=5)
        ttk.Entry(frm2, textvariable=v_rend_att, width=10,
                 validate="key", validatecommand=(frm2.register(lambda s: len(s) <= 6), "%P")).grid(row=2, column=1, sticky="w", pady=5)
        tk.Label(frm2, text="Costo di gestione annuo % (ISC):", font=("Arial", 9, "bold"), anchor="w",
                 bg=bg, fg=fg).grid(row=3, column=0, sticky="w", padx=(0, 8), pady=5)
        ttk.Entry(frm2, textvariable=v_costo_gest, width=10,
                 validate="key", validatecommand=(frm2.register(lambda s: len(s) <= 6), "%P")).grid(row=3, column=1, sticky="w", pady=5)
        tk.Label(frm2, text="(usati per la proiezione stimata nella scheda Dashboard; l'ISC riduce il rendimento atteso)",
                 font=("Arial", 7), bg=bg, fg=fg).grid(row=4, column=1, sticky="w")

        def salva_anag():
            try:
                infl = float(v_infl.get().replace(",", "."))
            except ValueError:
                self.show_toast("Inflazione stimata non valida.")
                return
            if v_ades.get():
                try:
                    datetime.datetime.strptime(v_ades.get(), "%d-%m-%Y")
                except ValueError:
                    self.show_toast("Data adesione non valida.")
                    return
            if v_pens.get():
                try:
                    datetime.datetime.strptime(v_pens.get(), "%d-%m-%Y")
                except ValueError:
                    self.show_toast("Data pensionamento non valida.")
                    return
            try:
                vers_stim = float(v_vers_stim.get().replace(",", ".") or 0)
            except ValueError:
                self.show_toast("Versamento annuo stimato non valido.")
                return
            try:
                rend_att = float(v_rend_att.get().replace(",", "."))
            except ValueError:
                self.show_toast("Rendimento atteso non valido.")
                return
            try:
                costo_gest = float(v_costo_gest.get().replace(",", "."))
            except ValueError:
                self.show_toast("Costo di gestione non valido.")
                return
            db["anagrafica"] = {
                "nome_fondo": v_nome.get().strip(),
                "gestore":    v_gest.get().strip(),
                "comparto":   v_comp.get().strip(),
                "tipo":       v_tipo.get(),
                "data_adesione": v_ades.get().strip(),
                "tasso_inflazione_stimato": infl,
                "note":       v_note.get().strip(),
                "data_pensione": v_pens.get().strip(),
                "versamento_annuo_stimato": vers_stim,
                "rendimento_atteso_pct": rend_att,
                "costo_gestione_pct": costo_gest,
            }
            salva_db(db)
            self.show_toast("Dati piano salvati.")
            _build_dashboard()
        frm_btn_anag = tk.Frame(frm, bg=bg)
        frm_btn_anag.grid(row=8, column=0, columnspan=2, pady=(14, 0))
        _btn(frm_btn_anag, "salva", "Salva", salva_anag)

    def _build_versamenti():
        _build_lista_crud(
            tab_vers, "Versamenti", "versamenti", "V",
            colonne=[
                {"key": "data",    "label": "Data",       "larghezza": 90,  "anchor": "center"},
                {"key": "tipo",    "label": "Tipo",       "larghezza": 140, "anchor": "w"},
                {"key": "importo", "label": "Importo €",  "larghezza": 90,  "anchor": "e"},
                {"key": "note",    "label": "Note",       "larghezza": 220, "anchor": "w"},
            ],
            campi_form=[
                {"key": "data",    "label": "Data:",       "tipo": "data"},
                {"key": "tipo",    "label": "Tipo:",       "tipo": "combo", "valori": TIPI_VERSAMENTO, "larghezza": 18},
                {"key": "importo", "label": "Importo €:",  "tipo": "importo"},
                {"key": "note",    "label": "Note:",       "tipo": "testo", "maxchar": 40, "larghezza": 20},
            ],
            after_change=_build_dashboard,
        )

    def _build_valorizzazioni():
        _build_lista_crud(
            tab_valor, "Valorizzazioni", "valorizzazioni", "Z",
            colonne=[
                {"key": "data",         "label": "Data",             "larghezza": 90,  "anchor": "center"},
                {"key": "controvalore", "label": "Controvalore €",   "larghezza": 120, "anchor": "e"},
                {"key": "note",         "label": "Note",             "larghezza": 220, "anchor": "w"},
            ],
            campi_form=[
                {"key": "data",         "label": "Data:",            "tipo": "data"},
                {"key": "controvalore", "label": "Controvalore €:",  "tipo": "importo"},
                {"key": "note",         "label": "Note:",            "tipo": "testo", "maxchar": 40, "larghezza": 20},
            ],
            after_change=_build_dashboard,
        )

    def _build_riscatti():
        _build_lista_crud(
            tab_risc, "Riscatti / Anticipazioni", "riscatti", "R",
            colonne=[
                {"key": "data",    "label": "Data",       "larghezza": 90,  "anchor": "center"},
                {"key": "tipo",    "label": "Tipo",       "larghezza": 170, "anchor": "w"},
                {"key": "importo", "label": "Importo €",  "larghezza": 90,  "anchor": "e"},
                {"key": "motivo",  "label": "Motivo",     "larghezza": 150, "anchor": "w"},
                {"key": "note",    "label": "Note",       "larghezza": 140, "anchor": "w"},
            ],
            campi_form=[
                {"key": "data",    "label": "Data:",       "tipo": "data"},
                {"key": "tipo",    "label": "Tipo:",       "tipo": "combo", "valori": TIPI_RISCATTO, "larghezza": 20},
                {"key": "importo", "label": "Importo €:",  "tipo": "importo"},
                {"key": "motivo",  "label": "Motivo:",     "tipo": "testo", "maxchar": 30, "larghezza": 20},
                {"key": "note",    "label": "Note:",       "tipo": "testo", "maxchar": 30, "larghezza": 20},
            ],
            after_change=_build_dashboard,
        )

    _build_dashboard()
    _build_anagrafica()
    _build_versamenti()
    _build_valorizzazioni()
    _build_riscatti()
