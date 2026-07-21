#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import tkinter as tk
from tkinter import ttk, filedialog
import datetime

import __main__ as _app
from moduli.modello_spesa import SIMBOLI_METODO, campo

# Gestione Partecipanti 
def _on_partecipante_selected(self, event=None):
    scelta = self.partecipante_var.get()
    if "Gestisci Partecipanti" in scelta:
        self.partecipante_var.set("")
        self.gestisci_partecipanti()
        return
    self._aggiorna_descrizione_con_partecipante(scelta)
def _aggiorna_descrizione_con_partecipante(self, scelta_combo, target_var=None):
    if scelta_combo and "Gestisci Partecipanti" in scelta_combo:
            return
    def _gn(p): return p.get("nome", p) if isinstance(p, dict) else p
    nome_nuovo = ""
    nuova_ico = ""
    if scelta_combo:
            nome_nuovo = scelta_combo[2:].strip() if " " in scelta_combo else scelta_combo.strip()
            nome_nuovo = nome_nuovo.strip()
            nuova_ico = "👤"
            for p in self.nomi_partecipanti:
                    if _gn(p) == nome_nuovo and isinstance(p, dict):
                            if p.get("tipo") == "personale":
                                    nuova_ico = "⚖️"
                            elif p.get("tipo") == "contenitore":
                                    nuova_ico = "🏠"
                            break
    desc = target_var.get().strip() if target_var else self.desc_entry.get().strip()
    simboli_pag = set(SIMBOLI_METODO.values())
    prefisso_pag = ""
    for s in simboli_pag:
            if desc.startswith(s):
                    prefisso_pag = s
                    desc = desc[len(s):].strip()
                    break
    icone_possibili = ["🏠", "👤", "⚖️"]
    _gestore_n = os.path.basename(os.getcwd())
    nomi_noti = sorted([_gn(p) for p in self.nomi_partecipanti] + [_gestore_n], key=len, reverse=True)
    blocco_trovato = False
    for ico_v in icone_possibili:
            for n_v in nomi_noti:
                   stringa_da_togliere = f"{ico_v}{n_v}"
                   if desc.startswith(stringa_da_togliere):
                            desc = desc[len(stringa_da_togliere):].strip()
                            blocco_trovato = True
                            break
            if blocco_trovato: break
    if not blocco_trovato:
            for ico_v in icone_possibili:
                    if desc.startswith(ico_v):
                            desc = desc[1:].strip()
                            break
    parti = []
    if prefisso_pag:
            parti.append(prefisso_pag)
    if nome_nuovo:
            parti.append(f"{nuova_ico}{nome_nuovo}")
    if desc:
            parti.append(desc)
    self.desc_entry.delete(0, "end")
    self.desc_entry.insert(0, " ".join(parti))
    self.desc_entry.icursor("end")
def _on_ric_partecipante_selected(self, event=None):
    scelta = self.ric_partecipante_var.get()
    if "Gestisci Partecipanti" in scelta:
        self.ric_partecipante_var.set("")
        self.gestisci_partecipanti()
        return
    self._aggiorna_descrizione_con_ric_partecipante(scelta)
def _aggiorna_descrizione_con_ric_partecipante(self, scelta_combo, target_var=None):
    if scelta_combo and "Gestisci Partecipanti" in scelta_combo:
        return
    def _gn(p): return p.get("nome", p) if isinstance(p, dict) else p
    nome_nuovo = ""
    nuova_ico = ""
    if scelta_combo:
        nome_nuovo = scelta_combo[2:].strip() if " " in scelta_combo else scelta_combo.strip()
        nome_nuovo = nome_nuovo.strip()
        nuova_ico = "👤"
        for p in self.nomi_partecipanti:
            if _gn(p) == nome_nuovo and isinstance(p, dict):
                if p.get("tipo") == "personale":
                    nuova_ico = "⚖️"
                elif p.get("tipo") == "contenitore":
                    nuova_ico = "🏠"
                break
    desc = target_var.get().strip() if target_var else self.ricorrenza_desc.get().strip()
    simboli_pag = set(SIMBOLI_METODO.values())
    prefisso_pag = ""
    for s in simboli_pag:
        if desc.startswith(s):
            prefisso_pag = s
            desc = desc[len(s):].strip()
            break
    icone_possibili = ["🏠", "👤", "⚖️"]
    _gestore_n = os.path.basename(os.getcwd())
    nomi_noti = sorted([_gn(p) for p in self.nomi_partecipanti] + [_gestore_n], key=len, reverse=True)
    blocco_trovato = False
    for ico_v in icone_possibili:
        for n_v in nomi_noti:
            stringa_da_togliere = f"{ico_v}{n_v}"
            if desc.startswith(stringa_da_togliere):
                desc = desc[len(stringa_da_togliere):].strip()
                blocco_trovato = True
                break
        if blocco_trovato: break
    if not blocco_trovato:
        for ico_v in icone_possibili:
            if desc.startswith(ico_v):
                desc = desc[1:].strip()
                break
    parti = []
    if prefisso_pag:
        parti.append(prefisso_pag)
    if nome_nuovo:
        parti.append(f"{nuova_ico}{nome_nuovo}")
    if desc:
        parti.append(desc)
    self.ricorrenza_desc.set(" ".join(parti))

def _gestore_partecipa(self):
    try:
        if os.path.exists(_app.PARTECIPANTI):
            with open(_app.PARTECIPANTI, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                return raw.get("gestore_partecipa", True)
    except Exception:
        pass
    return True
def carica_fairshare_state(self):
    try:
        if os.path.exists(_app.FAIRSHARE_STATE):
            with open(_app.FAIRSHARE_STATE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []
def salva_fairshare_state(self, debiti):
    try:
        os.makedirs(_app.DB_DIR, exist_ok=True)
        with open(_app.FAIRSHARE_STATE, "w", encoding="utf-8") as f:
            json.dump(debiti, f, ensure_ascii=False, indent=2)
    except Exception as e:
        self.show_custom_warning("Errore", f"Impossibile salvare fairshare_state.json:\n{e}")
def _sync_fairshare_e_aggiorna(self):
    self.sincronizza_fairshare_state()
    def _aggiorna_se_aperta():
        try:
            if (hasattr(self, '_dare_avere_aggiorna') and
                    self._dare_avere_aggiorna and
                    hasattr(self, '_dare_avere_popup') and
                    self._dare_avere_popup and
                    self._dare_avere_popup.winfo_exists()):
                self._dare_avere_aggiorna()
        except Exception:
            pass
    self.after(50, _aggiorna_se_aperta)
def sincronizza_fairshare_state(self):
    NOME_GESTORE = os.path.basename(os.getcwd())
    debiti_esistenti = self.carica_fairshare_state()
    idx = {}
    for d in debiti_esistenti:
        k = d.get("_key", "")
        if k:
            idx[k] = d
    tutti_partecipanti = self.nomi_partecipanti
    persone_fisiche = [pp["nome"] for pp in tutti_partecipanti
                       if pp.get("tipo", "persona") == "persona"]
    gestore_partecipa = self._gestore_partecipa()
    if gestore_partecipa and NOME_GESTORE not in persone_fisiche:
        persone_fisiche.append(NOME_GESTORE)
    soci_per_cont = {
        p["nome"]: [s for s in p.get("soci", []) if s in persone_fisiche]
        for p in tutti_partecipanti if p.get("tipo") == "contenitore"
    }
    nuove_chiavi = set()
    for data_obj in sorted(self.spese.keys()):
        if not isinstance(data_obj, datetime.date):
            continue
        voci     = self.spese[data_obj]
        data_str = data_obj.strftime("%d/%m/%Y")
        for idx_v, voce in enumerate(voci):
            try:
                cat      = campo(voce, "categoria", "").strip()
                desc_str = campo(voce, "descrizione", "").strip()
                imp      = float(campo(voce, "importo", 0.0))
                tipo_mov = campo(voce, "tipo", "").strip()
            except Exception:
                continue
            if tipo_mov != "Uscita":
                continue
            parti_trovati = []
            for p in tutti_partecipanti:
                nome_p = p["nome"]
                tipo_p = p.get("tipo", "persona")
                if tipo_p not in ("persona", "contenitore"):
                    continue
                if tipo_p == "contenitore":
                    if f"🏠{nome_p}" in desc_str:
                        soci = soci_per_cont.get(nome_p, [])
                        if soci:
                            parti_trovati = list(soci)
                        break
                else:
                    if f"👤{nome_p}" in desc_str:
                        parti_trovati = list(persone_fisiche) if persone_fisiche else [nome_p]
                        break
            if not parti_trovati and gestore_partecipa and f"👤{NOME_GESTORE}" in desc_str:
                parti_trovati = list(persone_fisiche) if persone_fisiche else [NOME_GESTORE]

            parti_sorted = sorted(set(parti_trovati))
            n = len(parti_sorted)
            if n == 0:
                continue
            quota      = round(imp / n, 2)
            key        = f"{data_str}#{idx_v}|{cat}|{imp:.2f}"
            desc_pulita = desc_str
            for p in tutti_partecipanti:
                desc_pulita = desc_pulita.replace(f"👤{p['nome']}", "").replace(f"🏠{p['nome']}", "").replace(f"⚖️{p['nome']}", "")
            if gestore_partecipa:
                desc_pulita = desc_pulita.replace(f"👤{NOME_GESTORE}", "")
            desc_pulita = desc_pulita.strip()
            nuove_chiavi.add(key)
            creditore = None
            for pf in persone_fisiche:
                if f"👤{pf}" in desc_str:
                    creditore = pf
                    break
            if creditore is None:
                creditore = NOME_GESTORE
            if key not in idx:
                pagamenti = {}
                for nm in parti_sorted:
                    if nm == creditore:
                        pagamenti[nm] = {"pagato": True, "data": data_str, "sorgente": "creditore"}
                    else:
                        pagamenti[nm] = {"pagato": False, "data": None}
                idx[key] = {
                    "_key":           key,
                    "data":           data_str,
                    "categoria":      cat,
                    "descrizione":    desc_pulita,
                    "importo_totale": imp,
                    "quota":          quota,
                    "n_partecipanti": n,
                    "creditore":      creditore,
                    "partecipanti":   parti_sorted,
                    "pagamenti":      pagamenti,
                    "stato":          "aperto",
                }
            else:
                d = idx[key]
                d["importo_totale"] = imp
                d["quota"]          = quota
                d["n_partecipanti"] = n
                d["descrizione"]    = desc_pulita
                d["creditore"]      = creditore
                for nm in parti_sorted:
                    if nm not in d["pagamenti"]:
                        if nm == creditore:
                            d["pagamenti"][nm] = {"pagato": True, "data": data_str, "sorgente": "creditore"}
                        else:
                            d["pagamenti"][nm] = {"pagato": False, "data": None}
                    elif nm == creditore and not d["pagamenti"][nm].get("pagato"):
                        d["pagamenti"][nm] = {"pagato": True, "data": data_str, "sorgente": "creditore"}
    entrate_valide = set()
    for data_obj in sorted(self.spese.keys()):
        if not isinstance(data_obj, datetime.date):
            continue
        for voce in self.spese[data_obj]:
            try:
                cat      = campo(voce, "categoria", "").strip()
                desc_str = campo(voce, "descrizione", "").strip()
                imp      = float(campo(voce, "importo", 0.0))
                tipo_mov = campo(voce, "tipo", "").strip()
            except Exception:
                continue
            if tipo_mov != "Entrata":
                continue
            pagante = None
            for p in tutti_partecipanti:
                if p.get("tipo") == "persona" and f"👤{p['nome']}" in desc_str:
                    pagante = p["nome"]
                    break
            if not pagante and f"👤{NOME_GESTORE}" in desc_str:
                pagante = NOME_GESTORE
            if pagante:
                entrate_valide.add((pagante, cat, round(imp, 2)))
    for deb in idx.values():
        if deb.get("stato") == "chiuso":
            continue
        cat_deb   = deb.get("categoria", "")
        quota_deb = round(deb.get("quota", 0.0), 2)
        for nm, info in deb.get("pagamenti", {}).items():
            sorgente = info.get("sorgente", "")
            if sorgente in ("manuale", "creditore"):
                continue
            entrata_trovata = (nm, cat_deb, quota_deb) in entrate_valide
            if entrata_trovata and not info.get("pagato"):
                info["pagato"]   = True
                info["data"]     = datetime.date.today().strftime("%d/%m/%Y")
                info["sorgente"] = "auto"
            elif not entrata_trovata and info.get("pagato"):
                info["pagato"] = False
                info["data"]   = None
                info.pop("sorgente", None)
    debiti_finali = []
    for k, deb in idx.items():
        if k not in nuove_chiavi:
            continue
        parti = deb.get("partecipanti", [])
        tutti_ok = bool(parti) and all(
            deb["pagamenti"].get(nm, {}).get("pagato", False)
            for nm in parti
        )
        deb["stato"] = "chiuso" if tutti_ok else "aperto"
        debiti_finali.append(deb)
    self.salva_fairshare_state(debiti_finali)
    return debiti_finali

def mostra_riepilogo_fairshare_periodo(self):
    if hasattr(self, '_analitico_popup') and self._analitico_popup and self._analitico_popup.winfo_exists():
        self._analitico_popup.lift(); self._analitico_popup.focus_force(); return
    debiti = self.carica_fairshare_state()
    parent = self._dare_avere_popup if hasattr(self, '_dare_avere_popup') and self._dare_avere_popup and self._dare_avere_popup.winfo_exists() else self
    popup = tk.Toplevel(parent, bg=self.COLOR_TOPLEVEL)
    popup.title("FairShare — Estratto Analitico per Spesa")
    self._analitico_popup = popup
    popup.bind("<Escape>", lambda e: popup.destroy())
    popup.bind("<Destroy>", lambda e: setattr(self, '_analitico_popup', None) if e.widget is popup else None)
    popup.withdraw()
    self.update_idletasks()
    w, h = 1250, 650
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    popup.geometry(f"{w}x{h}+{x}+{y}")
    popup.minsize(w, h)
    popup.transient(parent)
    popup.deiconify()
    popup.lift()
    popup.focus_force()
    oggi = datetime.date.today()
    mesi_nomi = ["Tutti", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                 "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    anni_db = sorted({d.year for d in self.spese if isinstance(d, datetime.date)}, reverse=True)
    if oggi.year not in anni_db:
        anni_db.insert(0, oggi.year)
    nomi_p_raw = {p["nome"]: p.get("tipo","persona") for p in self.nomi_partecipanti
                  if p.get("tipo") in ("persona","contenitore")}
    _gestore = os.path.basename(os.getcwd())
    if self._gestore_partecipa() and _gestore not in nomi_p_raw:
        nomi_p_raw[_gestore] = "persona"
    def _ico_p(nome):
        return "🏠" if nomi_p_raw.get(nome) == "contenitore" else "👤"
    nomi_p = ["Tutti"] + sorted([f"{_ico_p(n)} {n}" for n in nomi_p_raw], key=lambda x: x[2:].lower())
    cat_lst = ["Tutte"] + sorted(self.categorie, key=str.lower)
    filter_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL, pady=8)
    filter_f.pack(fill=tk.X, padx=15)
    def _lbl2(t):
        tk.Label(filter_f, text=t, bg=self.COLOR_TOPLEVEL,
                 fg=self.TEXT_COLOR, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(6, 2))
    _lbl2("Partecipante:")
    cb_part = ttk.Combobox(filter_f, values=nomi_p, width=18,
                           state="readonly", style="Border.TCombobox")
    cb_part.set("Tutti"); cb_part.pack(side=tk.LEFT, padx=3)
    _lbl2("Anno:")
    cb_anno = ttk.Combobox(filter_f, values=["Tutti"] + [str(a) for a in anni_db],
                           width=7, state="readonly", style="Border.TCombobox")
    cb_anno.set("Tutti"); cb_anno.pack(side=tk.LEFT, padx=3)
    _lbl2("Mese:")
    cb_mese = ttk.Combobox(filter_f, values=mesi_nomi, width=11,
                           state="readonly", style="Border.TCombobox")
    cb_mese.set("Tutti"); cb_mese.pack(side=tk.LEFT, padx=3)
    _lbl2("Categoria:")
    cb_cat = ttk.Combobox(filter_f, values=cat_lst, width=20,
                          state="readonly", style="Border.TCombobox")
    cb_cat.set("Tutte"); cb_cat.pack(side=tk.LEFT, padx=3)
    _lbl2("Stato:")
    cb_stato = ttk.Combobox(filter_f, values=["Tutti", "Aperto", "Chiuso"],
                            width=8, state="readonly", style="Border.TCombobox")
    cb_stato.set("Tutti"); cb_stato.pack(side=tk.LEFT, padx=3)

    tree_frame = ttk.Frame(popup)
    tree_frame.pack(fill=tk.X, padx=15, pady=5)
    cols_a = ("Data", "Categoria", "Descrizione", "Totale €", "Quota €",
              "N.Part.", "Paganti ✅", "In Attesa 🔴", "Stato")
    tree_a = ttk.Treeview(tree_frame, columns=cols_a, show="headings", height=15)
    vsb_a  = ttk.Scrollbar(tree_frame, orient="vertical", command=tree_a.yview)
    tree_a.configure(yscrollcommand=vsb_a.set)
    tree_a.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    vsb_a.pack(side=tk.RIGHT, fill=tk.Y)
    w_map = {"Data": 90, "Categoria": 110, "Descrizione": 260,
             "Totale €": 90, "Quota €": 80, "N.Part.": 55,
             "Paganti ✅": 110, "In Attesa 🔴": 120, "Stato": 90}
    for col in cols_a:
        tree_a.heading(col, text=col, command=lambda c=col: self.treeview_sort_column(tree_a, c, False))
        tree_a.column(col, width=w_map.get(col, 100),
                      anchor="w" if col == "Descrizione" else "center")
    tree_a.tag_configure("aperto",  foreground="#E06C75")
    tree_a.tag_configure("chiuso",  foreground="#61AFEF")
    self._bind_tooltip_metodo(tree_a, col_desc=2)
    det_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    det_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 4))
    vsb_det = ttk.Scrollbar(det_frame, orient="vertical", style="Vertical.TScrollbar")
    vsb_det.pack(side=tk.RIGHT, fill=tk.Y)
    lbl_det = tk.Text(det_frame, bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                      height=8, borderwidth=0, font=("Courier New", 9),
                      wrap="none", highlightthickness=0, relief="flat",
                      yscrollcommand=vsb_det.set)
    lbl_det.pack(fill=tk.BOTH, expand=True)
    vsb_det.config(command=lbl_det.yview)
    lbl_det.tag_config("verde",  foreground="#98C379")
    lbl_det.tag_config("rosso",  foreground="#E06C75")
    lbl_det.tag_config("giallo", foreground="#E5C07B")
    lbl_det.tag_config("neutro", foreground=self.TEXT_COLOR)
    lbl_det.tag_config("bold",   font=("Courier New", 9, "bold"))
    def aggiorna_tabella(*_args):
        tree_a.delete(*tree_a.get_children())
        p_sel  = cb_part.get()
        if p_sel not in ("", "Tutti") and " " in p_sel:
            p_sel = p_sel.split(" ", 1)[1].strip()
        a_sel  = cb_anno.get()
        m_idx  = mesi_nomi.index(cb_mese.get())
        c_sel  = cb_cat.get()
        st_sel = cb_stato.get()
        tot_dovuto = {}; tot_versato = {}; tot_debito = {}; chi_deve_a_chi_a = {}
        for deb in sorted(debiti, key=lambda d: d.get("data", "")):
            data_str = deb.get("data", "")
            try:
                d_obj = datetime.datetime.strptime(data_str, "%d/%m/%Y").date()
            except Exception:
                continue
            if a_sel != "Tutti" and str(d_obj.year) != a_sel: continue
            if m_idx > 0 and d_obj.month != m_idx: continue
            if c_sel != "Tutte" and deb.get("categoria") != c_sel: continue
            stato = deb.get("stato", "aperto")
            if st_sel != "Tutti" and stato != st_sel.lower(): continue
            pag   = deb.get("pagamenti", {})
            parti = deb.get("partecipanti", [])
            if p_sel != "Tutti" and p_sel not in parti:
                continue
            quota   = deb.get("quota", 0.0)
            imp     = deb.get("importo_totale", 0.0)
            paganti = [n for n in parti if pag.get(n, {}).get("pagato", False)]
            attesa  = [n for n in parti if not pag.get(n, {}).get("pagato", False)]
            st_ic   = "Chiuso" if stato == "chiuso" else "Aperto"
            tag_row = "chiuso" if stato == "chiuso" else "aperto"
            tree_a.insert("", "end", tags=(tag_row,), values=(
                data_str,
                deb.get("categoria", ""),
                deb.get("descrizione", ""),
                f"{imp:,.2f} €",
                f"{quota:,.2f} €",
                len(parti),
                len(paganti),
                len(attesa),
                st_ic,
            ))
            for nome in parti:
                if p_sel != "Tutti" and nome != p_sel: continue
                tot_dovuto.setdefault(nome, 0.0);  tot_dovuto[nome] += quota
                tot_versato.setdefault(nome, 0.0); tot_debito.setdefault(nome, 0.0)
                if pag.get(nome, {}).get("pagato", False):
                    tot_versato[nome] += quota
                else:
                    tot_debito[nome] += quota
                    creditore = deb.get("creditore", "")
                    if creditore and creditore != nome:
                        chi_deve_a_chi_a.setdefault((nome, creditore), 0.0)
                        chi_deve_a_chi_a[(nome, creditore)] += quota
        lbl_det.config(state="normal")
        lbl_det.delete("1.0", "end")
        lbl_det.insert("end",
            f"{'PERSONA':<20} {'DOVUTO':>12} {'VERSATO':>12} {'RESIDUO':>12}   SALDO\n",
            "bold")
        lbl_det.insert("end", "─" * 75 + "\n", "neutro")
        for nome in sorted(tot_dovuto.keys()):
            dov = tot_dovuto[nome]
            ver = tot_versato.get(nome, 0.0)
            res = tot_debito.get(nome, 0.0)
            sal_tag = "verde" if res < 0.01 else "rosso"
            lbl_det.insert("end", f"  {nome:<18} ", "neutro")
            lbl_det.insert("end", f"{dov:>11,.2f} €  ", "giallo")
            lbl_det.insert("end", f"{ver:>11,.2f} €  ", "verde")
            lbl_det.insert("end", f"{res:>11,.2f} €  ", sal_tag)
            lbl_det.insert("end",
                ("Saldato\n" if res < 0.01 else f"Deve {res:,.2f} EUR\n"),
                sal_tag)
        if tot_dovuto:
            lbl_det.insert("end", "─" * 75 + "\n", "neutro")
            td = sum(tot_dovuto.values()); tv = sum(tot_versato.values())
            tr = sum(tot_debito.values())
            lbl_det.insert("end", f"  {'TOTALE':<18} ", "bold")
            lbl_det.insert("end", f"{td:>11,.2f} €  ", "giallo")
            lbl_det.insert("end", f"{tv:>11,.2f} €  ", "verde")
            lbl_det.insert("end", f"{tr:>11,.2f} €\n",
                           "verde" if tr < 0.01 else "rosso")
            if chi_deve_a_chi_a:
                lbl_det.insert("end", "\n", "neutro")
                lbl_det.insert("end", "  CHI DEVE A CHI:\n", "bold")
                for (debitore, creditore), importo in sorted(
                        chi_deve_a_chi_a.items(), key=lambda x: (x[0][1], x[0][0])):
                    lbl_det.insert("end", f"  {debitore} → {creditore}: ", "neutro")
                    lbl_det.insert("end", f"{importo:,.2f} EUR\n", "rosso")
        else:
            lbl_det.insert("end", "  Nessun risultato per i filtri selezionati.\n", "neutro")
        lbl_det.config(state="disabled")

    def apri_anteprima_export():
        p_sel = cb_part.get(); a_sel = cb_anno.get()
        m_sel = cb_mese.get(); c_sel = cb_cat.get(); st_sel = cb_stato.get()
        sep = "═" * 105
        header  = f"FAIRSHARE — ESTRATTO ANALITICO\n"
        header += f"Partecipante: {p_sel}  Anno: {a_sel}  Mese: {m_sel}  "
        header += f"Categoria: {c_sel}  Stato: {st_sel}\n{sep}\n"
        header += (f"{'DATA':<10} {'CATEGORIA':<15} {'DESCRIZIONE':<25} "
                   f"{'TOTALE':>9} {'QUOTA':>9} {'N':>3} "
                   f"{'PAGATO':>7} {'ATTESA':>7}  STATO\n{'─'*105}\n")
        body = ""
        for iid in tree_a.get_children():
            v = tree_a.item(iid, "values")
            body += (f"{str(v[0]):<10} {str(v[1]):<15} {str(v[2])[:25]:<25} "
                     f"{str(v[3]):>9} {str(v[4]):>9} {str(v[5]):>3} "
                     f"{str(v[6]):>7} {str(v[7]):>7}  {str(v[8])}\n")
        footer  = f"\n{sep}\nRIEPILOGO PER PERSONA\n{sep}\n"
        footer += f"{'PERSONA':<20} {'DOVUTO':>15} {'VERSATO':>18} {'RESIDUO':>18}   SALDO\n"
        footer += "─" * 105 + "\n"
        m_idx2 = mesi_nomi.index(m_sel)
        st_sel2 = st_sel
        tot_d3 = {}; tot_v3 = {}; tot_r3 = {}
        for deb in debiti:
            ds = deb.get("data", "")
            try:
                d_obj = datetime.datetime.strptime(ds, "%d/%m/%Y").date()
            except Exception:
                continue
            if a_sel != "Tutti" and str(d_obj.year) != a_sel: continue
            if m_idx2 > 0 and d_obj.month != m_idx2: continue
            if c_sel != "Tutte" and deb.get("categoria") != c_sel: continue
            st2 = deb.get("stato", "aperto")
            if st_sel2 != "Tutti" and st2 != st_sel2.lower(): continue
            for nome in deb.get("partecipanti", []):
                if p_sel != "Tutti" and nome != p_sel: continue
                q = deb.get("quota", 0.0)
                pag2 = deb.get("pagamenti", {}).get(nome, {}).get("pagato", False)
                tot_d3.setdefault(nome, 0.0); tot_d3[nome] += q
                tot_v3.setdefault(nome, 0.0); tot_r3.setdefault(nome, 0.0)
                if pag2: tot_v3[nome] += q
                else:    tot_r3[nome] += q
        for nome in sorted(tot_d3.keys()):
            dov = tot_d3[nome]; ver = tot_v3.get(nome, 0); res = tot_r3.get(nome, 0)
            sal_s = "SALDATO" if res < 0.01 else f"DEVE {res:,.2f} EUR"
            footer += (f"  {nome:<18} {dov:>12,.2f} EUR  "
                       f"{ver:>12,.2f} EUR  {res:>12,.2f} EUR   {sal_s}\n")
        footer += "─" * 105 + "\n"
        td2 = sum(tot_d3.values()); tv2 = sum(tot_v3.values()); tr2 = sum(tot_r3.values())
        footer += (f"  {'TOTALE':<18} {td2:>12,.2f} EUR  "
                   f"{tv2:>12,.2f} EUR  {tr2:>12,.2f} EUR\n")
        chi3 = {}
        for deb in debiti:
            ds = deb.get("data", "")
            try:
                d_obj = datetime.datetime.strptime(ds, "%d/%m/%Y").date()
            except Exception:
                continue
            if a_sel != "Tutti" and str(d_obj.year) != a_sel: continue
            if m_idx2 > 0 and d_obj.month != m_idx2: continue
            if c_sel != "Tutte" and deb.get("categoria") != c_sel: continue
            st2 = deb.get("stato", "aperto")
            if st_sel2 != "Tutti" and st2 != st_sel2.lower(): continue
            creditore = deb.get("creditore", "")
            for nome in deb.get("partecipanti", []):
                if p_sel != "Tutti" and nome != p_sel: continue
                if not deb.get("pagamenti", {}).get(nome, {}).get("pagato", False):
                    if creditore and creditore != nome:
                        chi3.setdefault((nome, creditore), 0.0)
                        chi3[(nome, creditore)] += deb.get("quota", 0.0)
        if chi3:
            footer += "\nCHI DEVE A CHI:\n"
            for (debitore, creditore), importo in sorted(
                    chi3.items(), key=lambda x: (x[0][1], x[0][0])):
                footer += f"  {debitore} -> {creditore}: {importo:,.2f} EUR\n"
        self.show_export_preview(header + body + footer,
                                 f"FairShare_Analitico_{p_sel}_{a_sel}.txt")
    btn_frame = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    btn_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=10, padx=15)
    for ico, lbl_t, cmd in [
        ("salva",  " Esporta", lambda e: apri_anteprima_export()),
        ("chiudi", " Chiudi",  lambda e: popup.destroy())
    ]:
        img = self.icone_gui.get(ico)
        side = tk.RIGHT if ico == "chiudi" else tk.LEFT
        b = ttk.Label(btn_frame, compound="left", image=img,
                      text=lbl_t if img else lbl_t.strip(),
                      background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                      cursor="hand2", padding=(12, 6))
        b.pack(side=side, padx=5)
        b.bind("<Button-1>", cmd)
    for cb_w in [cb_part, cb_anno, cb_mese, cb_cat, cb_stato]:
        cb_w.bind("<<ComboboxSelected>>", aggiorna_tabella)
    aggiorna_tabella()

def popup_personali(self):
    if hasattr(self, '_popup_personali_win') and self._popup_personali_win.winfo_exists():
        self._popup_personali_win.lift()
        self._popup_personali_win.focus_force()
        return
    parent = self._dare_avere_popup if hasattr(self, '_dare_avere_popup') and self._dare_avere_popup and self._dare_avere_popup.winfo_exists() else self
    popup = tk.Toplevel(parent, bg=self.COLOR_TOPLEVEL)
    self._popup_personali_win = popup
    popup.title("Dettaglio Movimenti Personali ⚖️")
    popup.withdraw()
    self.update_idletasks()
    w, h = 1100, 650
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    popup.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")
    popup.minsize(w, h)
    popup.configure(background=self.COLOR_TOPLEVEL)
    popup.transient(parent)
    popup.deiconify()
    popup.lift()
    popup.focus_force()
    popup.bind("<Escape>", lambda e: popup.destroy())
    top_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    top_f.pack(fill=tk.X, padx=15, pady=15)
    style_cb = "Border.TCombobox"
    mese_nomi = ["Tutti", "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio",
                 "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    indips_names = [p["nome"] for p in self.nomi_partecipanti if p.get("tipo") == "personale"]
    indips_display = [f"⚖️ {n}" for n in indips_names]
    anni_disponibili = sorted(set(str(d.year) for d in self.spese.keys()), reverse=True)
    anno_v  = tk.StringVar(value="Tutti")
    mese_v  = tk.StringVar(value="Tutti")
    indip_v = tk.StringVar(value="Tutti")
    cat_v   = tk.StringVar(value="Tutti")
    filtri = [
        ("Anno:",      anno_v,  ["Tutti"] + anni_disponibili,    7),
        ("Mese:",      mese_v,  mese_nomi,                       10),
        ("Utente:",    indip_v, ["Tutti"] + indips_display,      25),
        ("Categoria:", cat_v,   ["Tutti"] + self.categorie,      25),
    ]
    combobox_lista = []
    for lbl_txt, var, vals, cw in filtri:
        tk.Label(top_f, text=lbl_txt, bg=self.COLOR_TOPLEVEL,
                 fg=self.TEXT_COLOR).pack(side=tk.LEFT, padx=(0, 5))
        cb = ttk.Combobox(top_f, textvariable=var, values=vals,
                          width=cw, state="readonly", style=style_cb)
        cb.pack(side=tk.LEFT, padx=(0, 15))
        combobox_lista.append(cb)
    tree_frame = ttk.Frame(popup)
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
    cols = ("Data", "Partecipante", "Categoria", "Descrizione", "Tipo", "Importo")
    tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")
    vsb  = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    col_cfg = {
        "Data":          (100, "center"),
        "Partecipante":  (130, "center"),
        "Categoria":     (130, "center"),
        "Descrizione":   (280, "w"),
        "Tipo":          (80,  "center"),
        "Importo":       (110, "center"),
    }
    for c in cols:
        w_col, anchor = col_cfg[c]
        tree.heading(c, text=c, command=lambda _c=c: self.treeview_sort_column(tree, _c, False))
        tree.column(c, width=w_col, anchor=anchor)
    tree.tag_configure("pos", foreground="#98C379")
    tree.tag_configure("neg", foreground="#E06C75")
    self._bind_tooltip_metodo(tree, col_desc=3)
    def _sort(col, reverse):
        rows = [(tree.set(k, col), k) for k in tree.get_children("")]
        if col == "Importo":
            rows.sort(reverse=reverse,
                      key=lambda t: float(t[0].replace("€", "").replace(".", "")
                                           .replace(",", ".").strip()))
        else:
            rows.sort(key=lambda t: t[0].lower(), reverse=reverse)
        for i, (_, k) in enumerate(rows):
            tree.move(k, "", i)
        tree.heading(col, command=lambda: _sort(col, not reverse))
    summary_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL,
                         highlightbackground=self.COLOR_WIDGET_BG, highlightthickness=1)
    summary_f.pack(fill=tk.X, padx=15, pady=5)
    lbl_ent_val = tk.Label(summary_f, text="0,00 €", font=("Arial", 11, "bold"),
                           bg=self.COLOR_TOPLEVEL, fg="#98C379")
    lbl_usc_val = tk.Label(summary_f, text="0,00 €", font=("Arial", 11, "bold"),
                           bg=self.COLOR_TOPLEVEL, fg="#E06C75")
    lbl_sal_val = tk.Label(summary_f, text="0,00 €", font=("Arial", 11, "bold"),
                           bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR)
    for etichetta, widget in [("Entrate:", lbl_ent_val),
                               ("Uscite:",  lbl_usc_val),
                               ("Saldo:",   lbl_sal_val)]:
        tk.Label(summary_f, text=etichetta, bg=self.COLOR_TOPLEVEL,
                 fg=self.TEXT_COLOR, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(10, 2))
        widget.pack(side=tk.LEFT, padx=(0, 20))
    def ricarica(*_):
        tree.delete(*tree.get_children())
        idx_m = mese_nomi.index(mese_v.get())
        t_ent = t_usc = 0.0
        for data, voci in self.spese.items():
            if anno_v.get() != "Tutti" and str(data.year) != anno_v.get():
                continue
            if idx_m > 0 and data.month != idx_m:
                continue
            for v in voci:
                categoria   = campo(v, "categoria", "") or "Varie"
                descrizione = campo(v, "descrizione", "")
                imp = campo(v, "importo", None)
                if imp is None:
                    continue
                imp = float(imp)
                tipo = campo(v, "tipo", "")
                nome_ind = next((n for n in indips_names if f"⚖️{n}" in descrizione or f"⚖{n}" in descrizione), None)
                if not nome_ind:
                    continue
                sel_ind = indip_v.get()
                if sel_ind != "Tutti":
                    sel_ind_puro = sel_ind.replace("⚖️ ", "").replace("⚖ ", "").strip()
                    if sel_ind_puro != nome_ind:
                        continue
                if cat_v.get() != "Tutti" and cat_v.get() != categoria:
                    continue
                tag = "pos" if tipo == "Entrata" else "neg"
                tree.insert("", "end",
                            values=(data.strftime("%d/%m/%Y"),
                                    f"⚖️ {nome_ind}",
                                    categoria,
                                    descrizione,
                                    tipo,
                                    f"{imp:,.2f} €"),
                            tags=(tag,))
                if tipo == "Entrata":
                    t_ent += imp
                else:
                    t_usc += imp
        saldo = t_ent - t_usc
        lbl_ent_val.config(text=f"{t_ent:,.2f} €")
        lbl_usc_val.config(text=f"{t_usc:,.2f} €")
        lbl_sal_val.config(text=f"{saldo:,.2f} €",
                           fg="#98C379" if saldo >= 0 else "#E06C75")
    for cb in combobox_lista:
        cb.bind("<<ComboboxSelected>>", ricarica)
    def anteprima_export():
        if hasattr(anteprima_export, '_win') and anteprima_export._win and anteprima_export._win.winfo_exists():
            anteprima_export._win.lift()
            anteprima_export._win.focus_force()
            return
        anno_sel = anno_v.get()
        mese_sel = mese_v.get()
        sep      = "─" * 110 + "\n"
        header   = (f"{'Data':<12} | {'Utente':<15} | {'Categoria':<18} | "
                    f"{'Descrizione':<25} | {'Tipo':<8} | {'Importo':>12}\n")
        contenuto = f"ESTRATTO MOVIMENTI PERSONALI - {mese_sel} {anno_sel}\n{sep}{header}{sep}"
        for item in tree.get_children():
            v = tree.item(item, "values")
            utente = v[1].replace("⚖️ ", "")[:15]
            contenuto += (f"{v[0]:<12} | {utente:<15} | {v[2]:<18} | "
                          f"{v[3][:24]:<25} | {v[4]:<8} | {v[5]:>12}\n")
        contenuto += (f"{sep}"
                      f"Entrate: {lbl_ent_val.cget('text'):>12} | "
                      f"Uscite: {lbl_usc_val.cget('text'):>12} | "
                      f"Saldo: {lbl_sal_val.cget('text'):>12}\n")
        prev_win = tk.Toplevel(popup)
        anteprima_export._win = prev_win
        prev_win.title("Esportazione Personali")
        prev_win.bind("<Escape>", lambda e: prev_win.destroy())
        prev_win.bind("<Destroy>", lambda e: setattr(anteprima_export, '_win', None) if e.widget is prev_win else None)
        prev_win.withdraw()
        prev_win.update_idletasks()
        w, h = 1000, 550
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
        prev_win.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")
        prev_win.minsize(w, h)
        prev_win.configure(background=self.COLOR_TOPLEVEL)
        prev_win.transient(popup)
        prev_win.deiconify()
        prev_win.lift()
        prev_win.focus_force()
        txt_frame = tk.Frame(prev_win, bg=self.COLOR_TOPLEVEL)
        txt_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        v_scroll = ttk.Scrollbar(txt_frame, orient="vertical")
        h_scroll = ttk.Scrollbar(txt_frame, orient="horizontal")
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        txt = tk.Text(txt_frame, font=("Courier New", 10),
                      bg=self.COLOR_WHITE, fg=self.COLOR_BLACK,
                      wrap="none",
                      yscrollcommand=v_scroll.set,
                      xscrollcommand=h_scroll.set)
        txt.pack(fill=tk.BOTH, expand=True)
        v_scroll.config(command=txt.yview)
        h_scroll.config(command=txt.xview)
        txt.insert("1.0", contenuto)
        txt.config(state="disabled")
        btn_f = tk.Frame(prev_win, bg=self.COLOR_TOPLEVEL)
        btn_f.pack(fill=tk.X, pady=10)
        def salva_pdf():
            f = filedialog.asksaveasfilename(
                initialdir=_app.EXPORT_FILES,
                confirmoverwrite=False,
                defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
                initialfile=f"Personali_{mese_sel}_{anno_sel}.pdf", parent=prev_win)
            if f:
                try:
                    import fitz
                    doc  = fitz.open()
                    page = doc.new_page(width=842, height=595)
                    page.insert_text((40, 40), contenuto, fontname="cour", fontsize=10)
                    doc.save(f); doc.close()
                    self.show_toast("PDF salvato.")
                except Exception as e:
                    self.show_custom_warning("Errore", str(e))
        def salva_txt():
            f = filedialog.asksaveasfilename(
                initialdir=_app.EXPORT_FILES,
                confirmoverwrite=False,
                defaultextension=".txt", filetypes=[("TXT", "*.txt")],
                initialfile=f"Personali_{mese_sel}_{anno_sel}.txt", parent=prev_win)
            if f:
                with open(f, "w", encoding="utf-8") as fh:
                    fh.write(contenuto)
                self.show_toast("TXT salvato.")
        for testo, ico, cmd, side in [
            (" Chiudi", "chiudi", prev_win.destroy, tk.RIGHT),
            (" PDF",    "salva",  salva_pdf,        tk.LEFT),
            (" TXT",    "salva",  salva_txt,        tk.LEFT),
            (" Stampa", "stampa", lambda: self._stampa_lista_diretta(contenuto, self.show_custom_warning), tk.LEFT),
        ]:
            b = ttk.Label(btn_f, compound="left", image=self.icone_gui.get(ico),
                          text=testo, background=self.COLOR_WIDGET_BG,
                          foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
            b.pack(side=side, padx=5)
            b.bind("<Button-1>", lambda e, c=cmd: c())
    bot_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    bot_f.pack(fill=tk.X, side=tk.BOTTOM, pady=15)
    for testo, ico, cmd, side in [
        ("  Esporta ", "salva",  anteprima_export, tk.LEFT),
        ("  Grafico ", "salva",  self.popup_grafico_categorie_personali, tk.LEFT),
        ("  Chiudi ",  "chiudi", popup.destroy,    tk.RIGHT),
    ]:
        b = tk.Label(bot_f, image=self.icone_gui.get(ico), text=testo,
                     compound="left", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                     cursor="hand2", font=("Arial", 10, "bold"))
        b.pack(side=side, padx=20)
        b.bind("<Button-1>", lambda e, c=cmd: c())
    ricarica()
def popup_grafico_categorie_personali(self):
    if hasattr(self, '_grafico_cat_personali_win') and self._grafico_cat_personali_win.winfo_exists():
        self._grafico_cat_personali_win.lift()
        self._grafico_cat_personali_win.focus_force()
        return
    popup = tk.Toplevel(self)
    self._grafico_cat_personali_win = popup 
    popup.title("Grafico Movimenti Personali per Categoria")
    popup.withdraw()
    self.update_idletasks()
    w, h = 1200, 650
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    popup.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")
    popup.minsize(w, h)
    popup.configure(bg=self.COLOR_TOPLEVEL)
    popup.attributes("-topmost", True)
    popup.resizable(True, True)
    popup.deiconify()
    popup.update_idletasks()
    popup.attributes("-topmost", False)
    popup.bind("<Escape>", lambda e: popup.destroy())
    MESI_NOMI = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                 "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    PALETTE = [
        "#61AFEF", "#E06C75", "#98C379", "#E5C07B", "#C678DD",
        "#56B6C2", "#FF9F43", "#A29BFE", "#FD79A8", "#6BCB77",
        "#F8961E", "#4D908E", "#F3722C", "#90BE6D", "#277DA1",
        "#D4AC0D", "#EB5757", "#48CAE4", "#B5838D", "#52B788",
    ]
    indips_names = [p["nome"] for p in self.nomi_partecipanti if p.get("tipo") == "personale"]
    top_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    top_f.pack(fill=tk.X, padx=15, pady=8)
    anni_disponibili = sorted(set(str(d.year) for d in self.spese.keys()), reverse=True)
    nomi_lista = ["Tutti"] + sorted(indips_names, key=lambda n: n.lower())
    anno_v = tk.StringVar(value="Tutti")
    mese_v = tk.StringVar(value="Tutti")
    tipo_v = tk.StringVar(value="Entrambi")
    nome_v = tk.StringVar(value="Tutti")
    def _lbl(t):
        return tk.Label(top_f, text=t, bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR)
    def _cb(var, vals, cw):
        return ttk.Combobox(top_f, textvariable=var, values=vals,
                            width=cw, state="readonly", style="Border.TCombobox")
    _lbl("Anno:").pack(side=tk.LEFT, padx=(0, 4))
    cb_anno = _cb(anno_v, ["Tutti"] + anni_disponibili, 7)
    cb_anno.pack(side=tk.LEFT, padx=(0, 15))
    _lbl("Mese:").pack(side=tk.LEFT, padx=(0, 4))
    cb_mese = _cb(mese_v, ["Tutti"] + MESI_NOMI, 10)
    cb_mese.pack(side=tk.LEFT, padx=(0, 15))
    _lbl("Tipo:").pack(side=tk.LEFT, padx=(0, 4))
    cb_tipo = _cb(tipo_v, ["Entrambi", "Uscita", "Entrata"], 9)
    cb_tipo.pack(side=tk.LEFT, padx=(0, 15))
    _lbl("Utente:").pack(side=tk.LEFT, padx=(0, 4))
    cb_nome = _cb(nome_v, nomi_lista, 25)
    cb_nome.pack(side=tk.LEFT, padx=(0, 15))
    main_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    main_f.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
    LEG_W = 200
    leg_outer = tk.Frame(main_f, bg=self.COLOR_TOPLEVEL, width=LEG_W)
    leg_outer.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))
    leg_outer.pack_propagate(False)
    leg_head = tk.Frame(leg_outer, bg=self.COLOR_TOPLEVEL)
    leg_head.pack(fill=tk.X, pady=(0, 4))
    tk.Label(leg_head, text="Categoria", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 8, "bold"), width=25, anchor="w").pack(side=tk.LEFT)
    tk.Label(leg_head, text="Saldo", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 8, "bold"), width=10, anchor="e").pack(side=tk.RIGHT)
    tk.Frame(leg_outer, bg=self.TEXT_COLOR, height=1).pack(fill=tk.X, pady=(0, 4))
    leg_cv = tk.Canvas(leg_outer, bg=self.COLOR_TOPLEVEL, highlightthickness=0)
    leg_sb = ttk.Scrollbar(leg_outer, orient="vertical", command=leg_cv.yview)
    leg_cv.configure(yscrollcommand=leg_sb.set)
    leg_sb.pack(side=tk.RIGHT, fill=tk.Y)
    leg_cv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    leg_inner = tk.Frame(leg_cv, bg=self.COLOR_TOPLEVEL)
    leg_cv.create_window((0, 0), window=leg_inner, anchor="nw")
    leg_inner.bind("<Configure>", lambda e: leg_cv.configure(scrollregion=leg_cv.bbox("all")))
    chart_f = tk.Frame(main_f, bg=self.COLOR_TOPLEVEL)
    chart_f.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    h_scroll = ttk.Scrollbar(chart_f, orient="horizontal")
    h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
    canvas = tk.Canvas(chart_f, bg=self.COLOR_WIDGET_BG,
                       highlightthickness=0, xscrollcommand=h_scroll.set)
    canvas.pack(fill=tk.BOTH, expand=True)
    h_scroll.config(command=canvas.xview)
    canvas.bind("<MouseWheel>", lambda e: canvas.xview_scroll(int(-1*(e.delta/120)), "units"))
    tot_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL,
                     highlightbackground=self.COLOR_WIDGET_BG, highlightthickness=1)
    tot_f.pack(fill=tk.X, padx=15, pady=(0, 4))
    riga_tot = tk.Frame(tot_f, bg=self.COLOR_TOPLEVEL)
    riga_tot.pack(fill=tk.X)

    lbl_ent_val = tk.Label(riga_tot, text="0,00 €", font=("Arial", 11, "bold"),
                           bg=self.COLOR_TOPLEVEL, fg="#98C379")
    lbl_usc_val = tk.Label(riga_tot, text="0,00 €", font=("Arial", 11, "bold"),
                           bg=self.COLOR_TOPLEVEL, fg="#E06C75")
    lbl_sal_val = tk.Label(riga_tot, text="0,00 €", font=("Arial", 11, "bold"),
                           bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR)
    for etichetta, widget in [("Entrate:", lbl_ent_val),
                               ("Uscite:",  lbl_usc_val),
                               ("Saldo:",   lbl_sal_val)]:
        tk.Label(riga_tot, text=etichetta, bg=self.COLOR_TOPLEVEL,
                 fg=self.TEXT_COLOR, font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(10, 2))
        widget.pack(side=tk.LEFT, padx=(0, 20))
    lbl_dettaglio_utenti = tk.Label(tot_f, text="", font=("Arial", 8),
                                    bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                                    wraplength=900, justify="left")
    lbl_dettaglio_utenti.pack(fill=tk.X, padx=10, pady=(0, 3))
    bot_f = tk.Frame(popup, bg=self.COLOR_TOPLEVEL)
    bot_f.pack(fill=tk.X, side=tk.BOTTOM, pady=8)
    b = tk.Label(bot_f, image=self.icone_gui.get("chiudi"), text="  Chiudi ",
                 compound="left", bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                 cursor="hand2", font=("Arial", 10, "bold"))
    b.pack(side=tk.RIGHT, padx=20)
    b.bind("<Button-1>", lambda e: popup.destroy())
    tooltip_lbl = tk.Label(popup, text="", bg="#2C313A", fg="white",
                           font=("Arial", 9), padx=6, pady=3,
                           relief="flat", borderwidth=0)
    def show_tip(event, testo):
        tooltip_lbl.config(text=testo)
        tooltip_lbl.place(x=event.x_root - popup.winfo_rootx() + 14,
                          y=event.y_root - popup.winfo_rooty() - 34)
    def hide_tip(_):
        tooltip_lbl.place_forget()
    _pronto = [False]
    _disegnando = [False]
    def disegna(*_):
        if not _pronto[0]:
            return
        if _disegnando[0]:
            return
        _disegnando[0] = True
        canvas.delete("all")
        for widget in leg_inner.winfo_children():
            widget.destroy()
        anno_sel = anno_v.get()
        mese_sel = mese_v.get()
        tipo_sel = tipo_v.get()
        nome_sel = nome_v.get()
        idx_mese = MESI_NOMI.index(mese_sel) + 1 if mese_sel != "Tutti" else 0
        dati_graf = {}
        saldi_cat = {}
        totali_utenti = {n: {"ent": 0.0, "usc": 0.0} for n in indips_names}
        t_ent = t_usc = 0.0
        for data, voci in self.spese.items():
            if anno_sel != "Tutti" and str(data.year) != anno_sel:
                continue
            if idx_mese > 0 and data.month != idx_mese:
                continue
            chiave = (data.year, data.month)
            for v in voci:
                cat  = campo(v, "categoria", "") or "Varie"
                desc = campo(v, "descrizione", "")
                imp = campo(v, "importo", None)
                if imp is None:
                    continue
                imp = float(imp)
                tipo = campo(v, "tipo", "")
                nome_trovato = next((n for n in indips_names
                                     if f"⚖️{n}" in desc or f"⚖{n}" in desc), None)
                if not nome_trovato:
                    continue
                if nome_sel != "Tutti" and nome_sel != nome_trovato:
                    continue
                if cat not in saldi_cat:
                    saldi_cat[cat] = {"ent": 0.0, "usc": 0.0}
                if tipo == "Entrata":
                    saldi_cat[cat]["ent"] += imp
                    t_ent += imp
                    totali_utenti[nome_trovato]["ent"] += imp
                else:
                    saldi_cat[cat]["usc"] += imp
                    t_usc += imp
                    totali_utenti[nome_trovato]["usc"] += imp
                if tipo_sel != "Entrambi" and tipo != tipo_sel:
                    continue
                if chiave not in dati_graf:
                    dati_graf[chiave] = {}
                if nome_trovato not in dati_graf[chiave]:
                    dati_graf[chiave][nome_trovato] = {}
                if cat not in dati_graf[chiave][nome_trovato]:
                    dati_graf[chiave][nome_trovato][cat] = {"ent": 0.0, "usc": 0.0}
                if tipo == "Entrata":
                    dati_graf[chiave][nome_trovato][cat]["ent"] += imp
                else:
                    dati_graf[chiave][nome_trovato][cat]["usc"] += imp
        saldo_tot = t_ent - t_usc
        lbl_ent_val.config(text=f"{t_ent:,.2f} €")
        lbl_usc_val.config(text=f"{t_usc:,.2f} €")
        lbl_sal_val.config(text=f"{saldo_tot:,.2f} €",
                           fg="#98C379" if saldo_tot >= 0 else "#E06C75")
        if nome_sel == "Tutti" and len(indips_names) > 1:
            parti = []
            for n in sorted(indips_names):
                e = totali_utenti[n]["ent"]
                u = totali_utenti[n]["usc"]
                s = e - u
                segno = "+" if s >= 0 else ""
                parti.append(f"{n}: {segno}{s:,.2f}€")
            lbl_dettaglio_utenti.config(text="  |  ".join(parti))
        else:
            lbl_dettaglio_utenti.config(text="")
        if not dati_graf or not any(dati_graf.values()):
            canvas.create_text(300, 150, text="Nessun dato disponibile",
                               fill=self.TEXT_COLOR, font=("Arial", 14))
            _disegnando[0] = False
            return
        mesi_ordinati   = sorted(dati_graf.keys())
        categorie_usate = set(cat for m in dati_graf.values()
                                  for utente in m.values()
                                  for cat in utente)
        categorie_lista = sorted(categorie_usate, key=lambda c: c.lower())
        n_cat  = len(categorie_lista)
        n_mesi = len(mesi_ordinati)
        colori = {cat: PALETTE[i % len(PALETTE)] for i, cat in enumerate(
            sorted(saldi_cat.keys(), key=lambda c: c.lower())
        )}
        popup.update_idletasks()
        CW      = max(canvas.winfo_width(), 500)
        CH      = max(canvas.winfo_height(), 300)
        PAD_L   = 75
        PAD_R   = 15
        PAD_T   = 20
        PAD_B   = 52
        CHART_H = CH - PAD_T - PAD_B
        base_y  = PAD_T + CHART_H
        bar_w   = 14
        bar_gap = 3
        group_w = max(n_cat * (bar_w + bar_gap) + 20, 80)
        total_w = PAD_L + n_mesi * group_w + PAD_R
        canvas.config(scrollregion=(0, 0, max(total_w, CW), CH))
        max_val = max(
            (d["ent"] + d["usc"] for mese in dati_graf.values()
                  for utente in mese.values()
                  for d in utente.values()), default=1
        ) or 1
        def val_to_y(v):
            return PAD_T + CHART_H - int((v / max_val) * CHART_H)
        for i in range(6):
            val = max_val * i / 5
            y   = val_to_y(val)
            canvas.create_line(PAD_L, y, total_w - PAD_R, y,
                               fill="#3a3a3a", dash=(3, 4))
            canvas.create_text(PAD_L - 5, y, text=f"{val:,.0f}€",
                               anchor="e", fill=self.TEXT_COLOR, font=("Arial", 8))
        canvas.create_line(PAD_L, base_y, total_w - PAD_R, base_y,
                           fill=self.TEXT_COLOR, width=1)
        for mi, mese_key in enumerate(mesi_ordinati):
            anno_m, mese_m = mese_key
            x_group  = PAD_L + mi * group_w
            centro_x = x_group + (n_cat * (bar_w + bar_gap)) // 2
            label_m  = f"{MESI_NOMI[mese_m-1]}\n{anno_m}" if anno_sel == "Tutti" else MESI_NOMI[mese_m-1]
            canvas.create_text(centro_x, base_y + 6, text=label_m,
                               anchor="n", fill=self.TEXT_COLOR, font=("Arial", 8))
            for ci, cat in enumerate(categorie_lista):
                for nome_u, cat_dict in dati_graf[mese_key].items():
                    d = cat_dict.get(cat, None)
                    if not d:
                        continue
                    val = d["ent"] + d["usc"]
                    if val == 0:
                        continue
                    x0    = x_group + ci * (bar_w + bar_gap)
                    x1    = x0 + bar_w
                    y0    = val_to_y(val)
                    barra = canvas.create_rectangle(x0, y0, x1, base_y,
                                                    fill=colori[cat], outline="",
                                                    tags="barra")
                    tip = (f"⚖️ {nome_u}  |  {cat}  ({MESI_NOMI[mese_m-1]} {anno_m})\n"
                           f"Entrate: +{d['ent']:,.2f}€   Uscite: -{d['usc']:,.2f}€")
                    canvas.tag_bind(barra, "<Enter>", lambda e, t=tip: show_tip(e, t))
                    canvas.tag_bind(barra, "<Leave>", hide_tip)
        for cat in sorted(saldi_cat.keys(), key=lambda c: c.lower()):
            ent    = saldi_cat[cat]["ent"]
            usc    = saldi_cat[cat]["usc"]
            sal    = ent - usc
            fg_sal = "#98C379" if sal >= 0 else "#E06C75"
            f_row  = tk.Frame(leg_inner, bg=self.COLOR_TOPLEVEL)
            f_row.pack(fill=tk.X, pady=1)
            tk.Canvas(f_row, width=11, height=11,
                      bg=colori.get(cat, "#888"),
                      highlightthickness=0).pack(side=tk.LEFT, padx=(0, 4))
            tk.Label(f_row, text=cat, bg=self.COLOR_TOPLEVEL,
                     fg=self.TEXT_COLOR, font=("Arial", 8),
                     anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)
            tk.Label(f_row, text=f"{sal:,.0f}€", bg=self.COLOR_TOPLEVEL,
                     fg=fg_sal, font=("Arial", 8, "bold"),
                     anchor="e").pack(side=tk.RIGHT, padx=(0, 4))
        _disegnando[0] = False
    canvas.bind("<Configure>", disegna)    
    for cb in [cb_anno, cb_mese, cb_tipo, cb_nome]:
        cb.bind("<<ComboboxSelected>>", disegna)
    def _avvia():
        _pronto[0] = True
        disegna()
    popup.after(150, _avvia)

def mostra_guida_dare_avere(self, popup=None):
    if hasattr(self, '_guida_popup') and self._guida_popup and self._guida_popup.winfo_exists():
        self._guida_popup.lift(); self._guida_popup.focus_force(); return
    guida_win = tk.Toplevel(popup, bg=self.COLOR_TOPLEVEL)
    self._guida_popup = guida_win
    guida_win.withdraw()
    guida_win.title("Guida FairShare — Dare & Avere per Spesa")
    guida_win.resizable(True, True)
    guida_win.bind("<Escape>", lambda e: guida_win.destroy())
    guida_win.bind("<Destroy>", lambda e: setattr(self, '_guida_popup', None))
    guida_win.transient(popup)
    NOME_GESTORE = os.path.basename(os.getcwd())
    testo_guida = (
        "1. LOGICA DI BASE\n"
        "   La quota di ogni Persona = totale uscite (incluse quelle dei Gruppi) / numero Persone.\n"
        "   Il Gestore (" + NOME_GESTORE + ") partecipa come qualsiasi altra Persona\n"
        "   se abilitato in 'Gestisci Partecipanti'.\n\n"
        "2. TIPI DI PARTECIPANTE\n"
        "   👤 Persona    → Partecipa alla divisione delle spese comuni.\n"
        "   🏠 Gruppo     → Fondo comune (es. Casa). Le spese vengono divise tra i soci.\n"
        "                   Non paga quota propria.\n"
        "   ⚖️ Personale  → Spese e entrate solo sue (stipendio, spese private).\n"
        "                   Non partecipa alla divisione.\n\n"
        "3. COME REGISTRARE UNA SPESA\n"
        "   - Seleziona il partecipante dalla combobox 👤/🏠:\n"
        "     il prefisso icona+Nome viene aggiunto in automatico alla descrizione.\n"
        "   - USCITA  → spesa pagata da quel partecipante (chi ha anticipato i soldi).\n"
        "   - ENTRATA → rimborso ricevuto (chi restituisce la quota).\n"
        "     L'entrata deve avere la STESSA CATEGORIA della spesa originale.\n"
        "   - Metodi di pagamento disponibili: simboli_pag = "
        + ", ".join(SIMBOLI_METODO.values()) + "\n\n"
        "4. SEGNARE UN PAGAMENTO\n"
        "   AUTOMATICO: se registri un'entrata con tag 👤Nome e stessa categoria\n"
        "   della spesa originale, il sistema segna il pagamento automaticamente.\n\n"
        "   MANUALE: doppio click sulla riga nella vista Dare & Avere.\n"
        "   - Primo doppio click  → segna PAGATO (con data odierna)\n"
        "   - Secondo doppio click → ANNULLA il pagamento\n"
        "   Il pagamento manuale non viene mai sovrascritto dal sync automatico.\n\n"
        "   Quando TUTTI i partecipanti hanno pagato, lo stato diventa Chiuso.\n\n"
        "5. CALCOLO DEL SALDO FAIRSHARE\n"
        "   Saldo = (Uscite pagate + Entrate ricevute) − Quota pro capite\n"
        "   La quota include anche la divisione delle spese dei Gruppi di cui si è soci.\n"
        "   Positivo → deve RICEVERE dagli altri.\n"
        "   Negativo → deve VERSARE agli altri.\n"
        "   Zero     → pari.\n\n"
        "6. GRUPPI 🏠\n"
        "   Crea un Gruppo in 'Gestisci Partecipanti' e seleziona i soci.\n"
        "   Le spese taggate 🏠NomeGruppo vengono divise automaticamente tra i soci.\n"
        "   Il Gestore può essere incluso tra i soci di un Gruppo.\n\n"
        "7. MOVIMENTI PERSONALI ⚖️\n"
        "   Accessibili da 'Personali' nel pannello FairShare.\n"
        "   Filtrabili per anno, mese, utente e categoria.\n\n"
        "8. RICORRENZE\n"
        "   Le spese ricorrenti vengono generate automaticamente alla data prevista.\n"
        "   Ogni ricorrenza può avere partecipante, categoria e metodo di pagamento.\n"
        "   Gestibili dal pannello Ricorrenze nel form principale.\n\n"
        "9. GRAFICI\n"
        "   Tab 1 → Dovuto vs Versato per persona.\n"
        "   Tab 2 → Importo Aperto vs Chiuso per categoria.\n"
        "   Tab 3 → Andamento mensile dovuto/versato.\n"
        "   Filtrabili per anno, mese, persona e categoria.\n"
        "   Hover sul grafico → tooltip con i valori.\n\n"
        "10. ESPORTAZIONE\n"
        "    Esporta → anteprima con salvataggio PDF o TXT.\n"
        "    Analitico → estratto completo per partecipante e periodo.\n"
        "    Entrambi includono il riepilogo 'Chi deve a chi'.\n"
    )
    def centra_guida():
        w_g, h_g = 960, 700
        if popup:
            x = popup.winfo_rootx() + (popup.winfo_width() // 2) - (w_g // 2)
            y = popup.winfo_rooty() + (popup.winfo_height() // 2) - (h_g // 2)
        else:
            x = (guida_win.winfo_screenwidth() // 2) - (w_g // 2)
            y = (guida_win.winfo_screenheight() // 2) - (h_g // 2)
        guida_win.geometry(f"{w_g}x{h_g}+{max(0, x)}+{max(0, y)}")
        guida_win.deiconify()
        guida_win.focus_force()
    guida_win.after(0, centra_guida)
    txt_frame = tk.Frame(guida_win, bg=self.COLOR_HIGHLIGHT, padx=2, pady=2)
    txt_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    vsb = ttk.Scrollbar(txt_frame, orient="vertical", style="Vertical.TScrollbar")
    vsb.pack(side=tk.RIGHT, fill=tk.Y)
    st_guida = tk.Text(txt_frame, font=("Courier New", 10),
                       bg=self.COLOR_WHITE, fg=self.COLOR_BLACK,
                       padx=15, pady=15, relief="flat", borderwidth=0,
                       wrap="word", yscrollcommand=vsb.set)
    st_guida.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    vsb.config(command=st_guida.yview)
    st_guida.insert("1.0", testo_guida)
    st_guida.config(state="disabled")
    btn_frame_g = tk.Frame(guida_win, bg=self.COLOR_TOPLEVEL)
    btn_frame_g.pack(fill=tk.X, pady=(0, 10))
    img_p = self.icone_gui.get("stampa")
    btn_p = ttk.Label(btn_frame_g, compound="left", image=img_p,
                      text=" Stampa" if img_p else "Stampa",
                      background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                      cursor="hand2", padding=(10, 5))
    btn_p.pack(side=tk.LEFT, padx=15)
    btn_p.bind("<Button-1>", lambda e: self._stampa_lista_diretta(testo_guida, self.show_custom_warning))
    img_ok = self.icone_gui.get("chiudi")
    btn_ok = ttk.Label(btn_frame_g, compound="left", image=img_ok,
                       text=" Ho Capito" if img_ok else "Ho Capito",
                       background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                       cursor="hand2", padding=(10, 5))
    btn_ok.pack(side=tk.RIGHT, padx=15)
    btn_ok.bind("<Button-1>", lambda e: guida_win.destroy())

def get_fairshare_data_json(self, anno_sel, mese_sel, utente_sel):
    mese_num = int(mese_sel) if mese_sel and mese_sel != "0" else 0
    debiti   = self.carica_fairshare_state()
    personali = [p for p in self.nomi_partecipanti if p.get("tipo") == "personale"]
    debiti_filtrati = []
    for deb in debiti:
        ds = deb.get("data", "")
        try:
            d_obj = datetime.datetime.strptime(ds, "%d/%m/%Y").date()
        except Exception:
            continue
        if anno_sel and anno_sel != "0" and str(d_obj.year) != anno_sel:
            continue
        if mese_num > 0 and d_obj.month != mese_num:
            continue
        debiti_filtrati.append(deb)
    tot_dovuto  = {}
    tot_versato = {}
    chi_deve    = {}
    for deb in debiti_filtrati:
        quota     = deb.get("quota", 0.0)
        creditore = deb.get("creditore", "")
        pag       = deb.get("pagamenti", {})
        for nome in deb.get("partecipanti", []):
            tot_dovuto.setdefault(nome, 0.0)
            tot_versato.setdefault(nome, 0.0)
            tot_dovuto[nome] += quota
            if pag.get(nome, {}).get("pagato", False):
                tot_versato[nome] += quota
            else:
                if creditore and creditore != nome:
                    chiave = (nome, creditore)
                    chi_deve.setdefault(chiave, 0.0)
                    chi_deve[chiave] += quota
    persone_list = []
    for nome in sorted(tot_dovuto.keys()):
        dov = tot_dovuto[nome]
        ver = tot_versato.get(nome, 0.0)
        res = round(dov - ver, 2)
        persone_list.append({
            "nome":    nome,
            "dovuto":  round(dov, 2),
            "versato": round(ver, 2),
            "residuo": res,
        })
    chi_deve_list = [
        {"da": d, "a": c, "importo": round(v, 2)}
        for (d, c), v in sorted(chi_deve.items(), key=lambda x: (x[0][1], x[0][0]))
    ]
    indips      = [p["nome"] for p in personali]
    saldi_cat_p = {n: {} for n in indips}
    totali_p    = {n: {"ent": 0.0, "usc": 0.0} for n in indips}
    for data, voci in self.spese.items():
        if anno_sel and anno_sel != "0" and str(data.year) != anno_sel:
            continue
        if mese_num > 0 and data.month != mese_num:
            continue
        for voce in voci:
            try:
                cat  = campo(voce, "categoria", "")
                imp  = float(campo(voce, "importo", 0.0))
                tipo = campo(voce, "tipo", "")
                desc_str = campo(voce, "descrizione", "")
            except:
                continue
            nome_trovato = next(
                (n for n in indips if f"⚖️{n}" in desc_str or f"⚖{n}" in desc_str), None
            )
            if not nome_trovato:
                continue
            if utente_sel and utente_sel != "tutti" and utente_sel != nome_trovato:
                continue
            saldi_cat_p[nome_trovato].setdefault(cat, {"ent": 0.0, "usc": 0.0})
            if tipo == "Entrata":
                saldi_cat_p[nome_trovato][cat]["ent"] += imp
                totali_p[nome_trovato]["ent"]          += imp
            else:
                saldi_cat_p[nome_trovato][cat]["usc"] += imp
                totali_p[nome_trovato]["usc"]          += imp
    personali_data = []
    for nome in indips:
        cats = [
            {"cat": cat, "ent": round(v["ent"], 2), "usc": round(v["usc"], 2)}
            for cat, v in saldi_cat_p[nome].items()
        ]
        cats.sort(key=lambda x: x["usc"] + x["ent"], reverse=True)
        personali_data.append({
            "nome":      nome,
            "tot_ent":   round(totali_p[nome]["ent"], 2),
            "tot_usc":   round(totali_p[nome]["usc"], 2),
            "categorie": cats
        })
    anni_disponibili = sorted(set(str(d.year) for d in self.spese.keys()), reverse=True)
    tot_dovuto_all  = round(sum(tot_dovuto.values()), 2)
    tot_residuo_all = round(sum(tot_dovuto.values()) - sum(tot_versato.values()), 2)
    return json.dumps({
        "persone":          persone_list,
        "chi_deve":         chi_deve_list,
        "personali":        personali_data,
        "anni":             anni_disponibili,
        "utenti_personali": indips,
        "tot_dovuto":       tot_dovuto_all,
        "tot_residuo":      tot_residuo_all,
    })

