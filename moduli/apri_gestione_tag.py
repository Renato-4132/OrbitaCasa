#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import json
import tkinter as tk
from tkinter import ttk
from moduli.modello_spesa import campo, METODI_PAGAMENTO_EMOJI, metodo_pagamento_pulito
from moduli.mappa_conti_trasferimenti import costruisci_mappa_conti_da_trasferimenti, conto_da_mappa

def _data_libera(s):
    s = str(s or "").strip().replace("/", "-").replace(".", "-")
    if not s:
        return None
    try:
        return datetime.datetime.strptime(s, "%d-%m-%Y").date()
    except Exception:
        return None

def _fmt_it(v, spec=",.2f"):
    s = format(v, spec)
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")

def apri_gestione_tag(self):
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    if hasattr(self, '_win_tag') and self._win_tag and self._win_tag.winfo_exists():
        self._win_tag.lift()
        self._win_tag.focus_force()
        return
    NOMI_MESI_IT = ["Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno",
                     "Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"]
    _riga_map = {}
    def _carica():
        tdb = {}
        _riga_map.clear()
        for d, entries in sorted(self.spese.items()):
            for v in entries:
                tags = getattr(v, "hashtag", None)
                if tags:
                    chiave = getattr(v, "id_spesa", None)
                    if not chiave:
                        continue
                    tdb[chiave] = list(tags)
                    _riga_map[chiave] = (d, v)
        return tdb
    def _trova_entry(chiave):
        return _riga_map.get(chiave, (None, None))
    def _imposta_tag(chiave, tags):
        d, entry = _trova_entry(chiave)
        if entry is None:
            return False
        entry.hashtag = list(tags)
        if hasattr(self, '_cache_tutti_tag'):
            del self._cache_tutti_tag
        self.save_db()
        self.refresh_gui()
        return True
    def _rimuovi_tag_multipli(chiavi):
        modificati = 0
        for chiave in chiavi:
            d, entry = _trova_entry(chiave)
            if entry is not None:
                entry.hashtag = []
                modificati += 1
        if modificati:
            if hasattr(self, '_cache_tutti_tag'):
                del self._cache_tutti_tag
            self.save_db()
            self.refresh_gui()
        return modificati
    def _genera_testo_export():
        lines = []
        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        lines.append(f"RIEPILOGO TAG — {now}")
        lines.append("")
        lines.append(f"  {'Data':<12} {'Categoria':<20} {'Descrizione':<30} {'Importo':>10}  {'Tipo':<8}  {'Conto':<16}  {'Metodo':<14}  {'Ora':<6}  {'Tag'}")
        lines.append(f"  {'─'*12} {'─'*20} {'─'*30} {'─'*10}  {'─'*8}  {'─'*16}  {'─'*14}  {'─'*6}  {'─'*20}")
        lines.append("")
        items = tv.get_children()
        if not items:
                lines.append("  (nessun risultato da esportare)")
                return "\n".join(lines)
        tot_entrate = 0.0
        tot_uscite = 0.0
        for iid in items:
                vals = tv.item(iid, "values")
                data_str  = str(vals[0])
                cat       = str(vals[1])
                desc      = str(vals[2])
                imp_str   = str(vals[3]).replace("€","").replace(",",".").strip()
                tipo      = str(vals[4])
                conto     = str(vals[5])
                metodo    = str(vals[6])
                ora       = str(vals[7])
                tags_str  = str(vals[8])
                try:
                        imp = float(imp_str)
                        if tipo.lower() == "entrata":
                                tot_entrate += imp
                        elif tipo.lower() == "uscita":
                                tot_uscite += imp
                except Exception:
                        pass
                lines.append(f"  {data_str:<12} {cat:<20} {desc:<30} {vals[3]:>10}  {tipo:<8}  {conto:<16}  {metodo:<14}  {ora:<6}  {tags_str}")
        saldo = tot_entrate - tot_uscite
        lines.append("")
        lines.append(f"Totale Entrate: {_fmt_it(tot_entrate, '10,.2f')} €")
        lines.append(f"Totale Uscite:  {_fmt_it(tot_uscite, '10,.2f')} €")
        lines.append(f"SALDO FINALE:   {_fmt_it(saldo, '10,.2f')} €")
        lines.append("")
        lines.append(f"Totale voci: {len(items)}")
        return "\n".join(lines)
    def _popola(filtri=None):
        tv.delete(*tv.get_children())
        tv._metodo_lookup = {}
        tdb = _carica()
        _agganci_conto = costruisci_mappa_conti_da_trasferimenti(PORTAFOGLIO_BANCARIO)
        _uso_ordinale_conto = {}
        def _trova_conto_cached(d, imp, tipo):
            if not d:
                return "(nessuno)"
            return conto_da_mappa(_agganci_conto, _uso_ordinale_conto, d.strftime("%d-%m-%Y"), imp, tipo) or "(nessuno)"
        filtro_tag  = (filtri or {}).get("tag",  "").lower().strip()
        filtro_cat  = (filtri or {}).get("cat",  "")
        filtro_tipo = (filtri or {}).get("tipo", "")
        filtro_anno = (filtri or {}).get("anno", "")
        filtro_mese = (filtri or {}).get("mese", "")
        filtro_da   = (filtri or {}).get("da",   "")
        filtro_a    = (filtri or {}).get("a",    "")
        filtro_conto  = (filtri or {}).get("conto",  "")
        filtro_metodo = (filtri or {}).get("metodo", "")
        filtro_dal  = _data_libera((filtri or {}).get("dal", ""))
        filtro_al   = _data_libera((filtri or {}).get("al",  ""))
        try:
            da_f = float(filtro_da) if filtro_da else 0.0
        except Exception:
            da_f = 0.0
        try:
            a_f = float(filtro_a) if filtro_a else float("inf")
        except Exception:
            a_f = float("inf")
        inserted = 0
        date_ordinamento = []
        oggi = datetime.date.today()
        for chiave, tags in tdb.items():
            d, entry_match = _riga_map.get(chiave, (None, None))
            if entry_match is None:
                continue
            cat  = entry_match.categoria
            desc = entry_match.descrizione
            imp  = float(entry_match.importo)
            tipo = entry_match.tipo.capitalize() if isinstance(entry_match.tipo, str) else entry_match.tipo
            conto  = self._conto_effettivo(entry_match) or _trova_conto_cached(d, imp, tipo)
            metodo = campo(entry_match, "metodo_pagamento", "")
            ora    = campo(entry_match, "ora", "")
            tags_str = " ".join(tags)
            if filtro_tag and filtro_tag not in tags_str.lower():
                continue
            if filtro_cat and cat != filtro_cat:
                continue
            if filtro_tipo and tipo != filtro_tipo:
                continue
            if d:
                if filtro_anno and str(d.year) != filtro_anno:
                    continue
                if filtro_mese:
                    try:
                        idx_m = NOMI_MESI_IT.index(filtro_mese) + 1
                        if d.month != idx_m:
                            continue
                    except ValueError:
                        pass
            if filtro_conto and conto != filtro_conto:
                continue
            if filtro_metodo and metodo != filtro_metodo:
                continue
            if filtro_dal and (not d or d < filtro_dal):
                continue
            if filtro_al and (not d or d > filtro_al):
                continue
            if not (da_f <= imp <= a_f):
                continue
            imp_fmt = f"{imp:.2f}".replace(".", ",") + " €"
            data_fmt = d.strftime("%d-%m-%Y") if d else ""
            color_tag = "futuro" if (d and d > oggi) else (
                "entrata" if tipo == "Entrata" else "uscita" if tipo == "Uscita" else "")
            if (tipo == "Uscita" and d and d <= oggi
                    and (d.year, d.month) == (oggi.year, oggi.month)
                    and cat in getattr(self, "_budget_sforati", set())):
                color_tag = "sforato"
            tv.insert("", "end", iid=chiave,
                      values=(data_fmt, cat, desc, imp_fmt, tipo, conto, metodo, ora, tags_str),
                      tags=(color_tag,) if color_tag else ())
            tv._metodo_lookup[chiave] = {
                "metodo": metodo,
                "conto": conto,
                "ora": ora,
                "hashtag": list(tags),
                "id_ricorrenza": campo(entry_match, "id_ricorrenza", ""),
                "data": data_fmt,
                "categoria": cat,
                "importo": imp,
                "tipo": tipo,
                "id_spesa": campo(entry_match, "id_spesa", ""),
            }
            date_ordinamento.append((d, chiave))
            inserted += 1
        lbl_count.config(text=f"{inserted} voci")
        date_ordinamento.sort(key=lambda t: t[0] or datetime.date.min, reverse=True)
        for index, (_, chiave_ord) in enumerate(date_ordinamento):
            tv.move(chiave_ord, "", index)
        for c in tv["columns"]:
            testo_pulito = tv.heading(c, "text").replace(" ▲", "").replace(" ▼", "")
            tv.heading(c, text=(testo_pulito + " ▼") if c == "Data" else testo_pulito)
        _aggiorna_riepilogo()
    def _aggiorna_riepilogo():
        items = tv.get_children()
        tot_imp = 0.0
        freq = {}
        for iid in items:
            vals = tv.item(iid, "values")
            try:
                tot_imp += float(str(vals[3]).replace("€","").replace(",",".").strip())
            except Exception:
                pass
            for t in str(vals[8]).split():
                freq[t] = freq.get(t, 0) + 1
        top_tag = max(freq, key=freq.get) if freq else ""
        self._lbl_tag_tot_voci.config(text=f"Voci taggate: {len(items)}")
        self._lbl_tag_uniq.config(text=f"Tag unici: {len(freq)}")
        self._lbl_tag_importo.config(text=f"Totale importi: {_fmt_it(tot_imp)} €")
        self._lbl_tag_tag_freq.config(text=f"Tag più usato: {top_tag}")
    def _on_double_click(event):
            iid = tv.identify_row(event.y)
            if not iid:
                    return
            vals = tv.item(iid, "values")
            if not vals:
                    return
            try:
                    d = datetime.datetime.strptime(str(vals[0]).strip(), "%d-%m-%Y").date()
            except ValueError:
                    return
            self.mostra_treeview_statistiche()
            self.stats_view_mode.set("giorno")
            if hasattr(self, "cal"):
                    self.cal.selection_set(d)
                    self.cal._sel_date = d
                    self.cal.event_generate("<<CalendarSelected>>")
            self.update_stats()
            self.stats_label.config(
                    text=f"Riepilogo Giornaliero - {d.strftime('%d-%m-%Y')}",
                    foreground="purple", font=("Arial", 10, "bold"))
            _desc_sel = str(vals[2])[:20]
            _id_sp = (getattr(tv, "_metodo_lookup", {}).get(iid) or {}).get("id_spesa", "")
            self.after(400, lambda: self.seleziona_spesa_in_lista(d, _desc_sel, _id_sp))
            win.destroy()
    def _modifica_tag_selezionato():
        sel = tv.selection()
        if not sel:
            self.show_toast("Seleziona una voce dalla lista.")
            return
        if len(sel) > 1:
            self.show_toast("Seleziona solo una voce per la modifica.")
            return
        iid = sel[0]
        vals = tv.item(iid, "values")
        tags_correnti = str(vals[8]) if len(vals) > 8 else ""
        dlg = tk.Toplevel(win, bg=self.COLOR_TOPLEVEL)
        dlg.withdraw()
        dlg.title("Modifica Tag")
        dlg.resizable(False, False)
        dlg.transient(win)
        dlg.bind("<Escape>", lambda e: dlg.destroy())
        larg_d, alt_d = 380, 130
        x = win.winfo_rootx() + (win.winfo_width()  // 2) - (larg_d // 2)
        y = win.winfo_rooty() + (win.winfo_height() // 2) - (alt_d  // 2)
        dlg.geometry(f"{larg_d}x{alt_d}+{x}+{y}")
        tk.Label(dlg, text="Tag (separati da spazio o virgola):",
                 bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR).pack(padx=12, pady=(12,4), anchor="w")
        var_t = tk.StringVar(value=tags_correnti)
        ent = ttk.Entry(dlg, textvariable=var_t, width=40, style="Border.TEntry")
        ent.pack(padx=12, pady=4, fill="x")
        ent.focus_set()
        def _salva_modifica():
            nuovi = self._normalizza_tags(var_t.get())
            if _imposta_tag(iid, nuovi):
                _popola(filtri_attivi)
            else:
                self.show_toast("Movimento originale non trovato.")
            dlg.destroy()
        ent.bind("<Return>", lambda e: _salva_modifica())
        f_d = tk.Frame(dlg, bg=self.COLOR_TOPLEVEL)
        f_d.pack(pady=6)
        img_s = self.icone_gui.get("salva")
        b_s = ttk.Label(f_d, compound="left", image=img_s,
                        text=" Salva" if img_s else "Salva",
                        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                        cursor="hand2", padding=(8, 4))
        b_s.image = img_s
        b_s.pack(side="left", padx=8)
        b_s.bind("<Button-1>", lambda e: _salva_modifica())
        img_c = self.icone_gui.get("chiudi")
        b_c = ttk.Label(f_d, compound="left", image=img_c,
                        text=" Chiudi" if img_c else "Chiudi",
                        background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                        cursor="hand2", padding=(8, 4))
        b_c.image = img_c
        b_c.pack(side="left", padx=8)
        b_c.bind("<Button-1>", lambda e: dlg.destroy())
        dlg.deiconify()
    def _elimina_tag_selezionati():
        sel = tv.selection()
        if not sel:
            self.show_toast("Seleziona almeno una voce da eliminare.")
            return
        if not self.show_custom_askyesno("Conferma", f"Eliminare i tag di {len(sel)} voce/i selezionata/e?"):
            return
        _rimuovi_tag_multipli(sel)
        _popola(filtri_attivi)
    def _salva_e_preview():
        testo = _genera_testo_export()
        now = datetime.datetime.now()
        fname = f"Tag_Export_{now.strftime('%d-%m-%Y')}.txt"
        self.show_export_preview(testo, default_filename=fname)
    def _reset_filtri():
        stato_f["sosp"] = True
        try:
            for k, v in fv.items():
                v.set("")
        finally:
            stato_f["sosp"] = False
        for k in filtri_attivi:
            filtri_attivi[k] = ""
        ricerca_var.set("")
        aggiorna_testata_f()
        _popola(filtri_attivi)
    def _chiudi():
        self._win_tag = None
        win.destroy()
    filtri_attivi = {"tag":"","cat":"","tipo":"","anno":"","mese":"","conto":"","metodo":"","da":"","a":"","dal":"","al":""}
    win = tk.Toplevel(self.master, bg=self.COLOR_TOPLEVEL)
    win.withdraw()
    self._win_tag = win
    win.title("Gestione Tag Movimenti")
    larg, alt = 1366, 600
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    win.geometry(f"{larg}x{alt}+{(sw-larg)//2}+{(sh-alt)//2}")
    win.minsize(larg, alt)
    win.protocol("WM_DELETE_WINDOW", _chiudi)
    win.bind("<Escape>", lambda e: _chiudi())
    top_bar = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    top_bar.pack(fill="x", padx=10, pady=(8,2))
    tk.Label(top_bar, text="🔍", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR).pack(side="left")
    ricerca_var = tk.StringVar()
    ent_ricerca = ttk.Entry(top_bar, textvariable=ricerca_var,
                            width=22, style="Border.TEntry")
    ent_ricerca.pack(side="left", padx=(2,8))
    def _cerca_rapida(*_):
        filtri_attivi["tag"] = ricerca_var.get()
        aggiorna_testata_f()
        _popola(filtri_attivi)
    ent_ricerca.bind("<KeyRelease>", _cerca_rapida)
    img_r  = self.icone_gui.get("reset")
    btn_reset_ric = ttk.Label(top_bar, compound="left", image=img_r,
                               text=" Reset" if img_r else "Reset",
                               background=self.COLOR_WIDGET_BG,
                               foreground=self.TEXT_COLOR, cursor="hand2")
    btn_reset_ric.image = img_r
    btn_reset_ric.pack(side="left", padx=4)
    btn_reset_ric.bind("<Button-1>", lambda e: _reset_filtri())
    img_mouse = self.icone_gui.get("mouse")
    ttk.Label(
        top_bar,
        text="  Doppio clic → Dashboard  |  Clic destro → Copia nel form",
        image=img_mouse,
        compound="right",
        foreground="gray",
        font=("Arial", 8, "italic")
    ).pack(side="left", padx=(10, 0))
    lbl_count = tk.Label(top_bar, text="",
                         bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                         font=("Arial", 8))
    lbl_count.pack(side="right", padx=8)
    bg_f = self.COLOR_TOPLEVEL
    _tdb_f = _carica()
    _cat_f = [""] + sorted({_riga_map[k][1].categoria for k in _tdb_f if k in _riga_map})
    _anni_f = [""] + sorted({str(_riga_map[k][0].year) for k in _tdb_f
                              if k in _riga_map and _riga_map[k][0]}, reverse=True)
    _conti_f = [""]
    try:
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
            _conti_f += [c.get("nome", "?") for c in json.load(_pf).get("conti", [])]
    except Exception:
        pass
    fv = {"cat": tk.StringVar(value=""), "tipo": tk.StringVar(value=""),
          "anno": tk.StringVar(value=""), "mese": tk.StringVar(value=""),
          "conto": tk.StringVar(value=""), "metodo": tk.StringVar(value=""),
          "da": tk.StringVar(value=""), "a": tk.StringVar(value=""),
          "dal": tk.StringVar(value=""), "al": tk.StringVar(value="")}
    stato_f = {"aperta": False, "sosp": False, "job": None}
    head_f = tk.Frame(win, bg=bg_f)
    head_f.pack(fill="x", padx=10, pady=(0, 2))
    lbl_freccia = tk.Label(head_f, bg=bg_f, fg="#DC3545", cursor="hand2", font=("Arial", 11, "bold"), width=2)
    lbl_freccia.pack(side="left")
    lbl_head = tk.Label(head_f, bg=bg_f, fg=self.TEXT_COLOR, cursor="hand2", font=("Arial", 9, "bold"), anchor="w")
    lbl_head.pack(side="left")
    body_f = tk.Frame(win, bg=bg_f)
    riga_f = tk.Frame(body_f, bg=bg_f)
    riga_f.pack(fill="x", pady=2, padx=10)
    riga_f2 = tk.Frame(body_f, bg=bg_f)
    riga_f2.pack(fill="x", pady=2, padx=10)
    def _etich_f(testo, pad=(10, 4), r=None):
        tk.Label(r or riga_f, text=testo, bg=bg_f, fg=self.TEXT_COLOR).pack(side="left", padx=pad)
    def _combo_f(chiave, valori, w):
        ttk.Combobox(riga_f, values=valori, textvariable=fv[chiave], style="Border.TCombobox",
                     state="readonly", width=w).pack(side="left")
    _etich_f("Categoria:", (4, 4))
    _combo_f("cat", _cat_f, 20)
    _etich_f("Tipo:")
    _combo_f("tipo", ["", "Entrata", "Uscita"], 9)
    _etich_f("Anno:")
    _combo_f("anno", _anni_f, 7)
    _etich_f("Mese:")
    _combo_f("mese", [""] + NOMI_MESI_IT, 11)
    _etich_f("Conto:")
    _combo_f("conto", _conti_f, 16)
    _etich_f("Metodo Pag.:")
    _combo_f("metodo", [""] + METODI_PAGAMENTO_EMOJI, 20)
    _etich_f("Tag:", (4, 4), riga_f2)
    ent_tag_f = ttk.Entry(riga_f2, textvariable=ricerca_var, width=18)
    ent_tag_f.pack(side="left")
    ent_tag_f.bind("<KeyRelease>", _cerca_rapida)
    _etich_f("Importo da €:", (10, 4), riga_f2)
    ttk.Entry(riga_f2, textvariable=fv["da"], width=10).pack(side="left")
    _etich_f("a €:", (6, 4), riga_f2)
    ttk.Entry(riga_f2, textvariable=fv["a"], width=10).pack(side="left")
    def _cal_btn_f(entry, var):
        def apri(_e=None):
            self.mostra_calendario_popup(entry, var)
            try:
                pc = getattr(self, "popup_calendario", None)
                if pc is not None and pc.winfo_exists():
                    pc.attributes("-topmost", True)
                    pc.lift()
            except tk.TclError:
                pass
        img = self.icone_gui.get("calendario")
        b = tk.Label(riga_f2, image=img, bg=bg_f, cursor="hand2", padx=2)
        if img is None:
            b.config(text="📅")
        else:
            b.image = img
        b.pack(side="left", padx=(2, 0))
        b.bind("<Button-1>", apri)
    _etich_f("Dal:", (10, 4), riga_f2)
    e_dal_f = ttk.Entry(riga_f2, textvariable=fv["dal"], width=11)
    e_dal_f.pack(side="left")
    _cal_btn_f(e_dal_f, fv["dal"])
    _etich_f("Al:", (8, 4), riga_f2)
    e_al_f = ttk.Entry(riga_f2, textvariable=fv["al"], width=11)
    e_al_f.pack(side="left")
    _cal_btn_f(e_al_f, fv["al"])
    tk.Label(riga_f2, text="(GG-MM-AAAA)", bg=bg_f, fg="gray", font=("Arial", 8, "italic")).pack(side="left", padx=(4, 0))
    def aggiorna_testata_f():
        parti = []
        if filtri_attivi.get("tag", "").strip():
            parti.append(f"«{filtri_attivi['tag'].strip()}»")
        for k, etich in (("cat", "Categoria "), ("tipo", ""), ("anno", "Anno "), ("mese", ""),
                         ("conto", "Conto "), ("metodo", "Metodo ")):
            if filtri_attivi.get(k, ""):
                parti.append(f"{etich}{filtri_attivi[k]}")
        if filtri_attivi.get("dal") or filtri_attivi.get("al"):
            parti.append(f"{filtri_attivi.get('dal') or '…'} → {filtri_attivi.get('al') or '…'}")
        if filtri_attivi.get("da") or filtri_attivi.get("a"):
            parti.append(f"Importo {filtri_attivi.get('da') or '…'} → {filtri_attivi.get('a') or '…'} €")
        stato_txt = ("filtri attivi: " + ", ".join(parti)) if parti else "nessun filtro attivo"
        lbl_freccia.config(text="▾" if stato_f["aperta"] else "▸")
        lbl_head.config(text=f"Filtri avanzati  ({stato_txt})",
                        fg=getattr(self, "COLOR_HIGHLIGHT", self.TEXT_COLOR) if parti else self.TEXT_COLOR)
    def applica_f(*_):
        if stato_f["sosp"]:
            return
        stato_f["job"] = None
        try:
            if not win.winfo_exists():
                return
        except tk.TclError:
            return
        for k in ("cat", "tipo", "anno", "mese", "conto"):
            filtri_attivi[k] = fv[k].get()
        filtri_attivi["metodo"] = metodo_pagamento_pulito(fv["metodo"].get()) if fv["metodo"].get() else ""
        for k in ("da", "a"):
            filtri_attivi[k] = fv[k].get().strip().replace(",", ".")
        for k, e in (("dal", e_dal_f), ("al", e_al_f)):
            filtri_attivi[k] = fv[k].get().strip()
            sbagliata = bool(filtri_attivi[k]) and _data_libera(filtri_attivi[k]) is None
            try:
                e.configure(foreground="#DC3545" if sbagliata else self.TEXT_COLOR)
            except tk.TclError:
                pass
        aggiorna_testata_f()
        _popola(filtri_attivi)
    def rinvia_f(*_):
        if stato_f["job"]:
            win.after_cancel(stato_f["job"])
        stato_f["job"] = win.after(400, applica_f)
    def apri_chiudi_f(*_):
        stato_f["aperta"] = not stato_f["aperta"]
        if stato_f["aperta"]:
            body_f.pack(fill="x", before=tv_frame)
        else:
            body_f.pack_forget()
        aggiorna_testata_f()
    for k in ("cat", "tipo", "anno", "mese", "conto", "metodo"):
        fv[k].trace_add("write", applica_f)
    for k in ("da", "a", "dal", "al"):
        fv[k].trace_add("write", rinvia_f)
    for _w in (lbl_freccia, lbl_head):
        _w.bind("<Button-1>", apri_chiudi_f)
    aggiorna_testata_f()
    COLS = ("Data", "Categoria", "Descrizione", "Importo", "Tipo", "Conto", "Metodo", "Ora", "Tag")
    tv_frame = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    tv_frame.pack(fill="both", expand=True, padx=10, pady=(2,0))
    vsb = ttk.Scrollbar(tv_frame, orient="vertical",   style="Vertical.TScrollbar")
    tv  = ttk.Treeview(tv_frame, columns=COLS, show="headings", yscrollcommand=vsb.set)
    vsb.config(command=tv.yview)
    vsb.pack(side="right",  fill="y")
    tv.pack(side="left", fill="both", expand=True)
    col_cfg = {
        "Data":        (90,  "center"),
        "Categoria":   (130, "center"),
        "Descrizione": (200, "w"),
        "Importo":     (90,  "e"),
        "Tipo":        (70,  "center"),
        "Conto":       (110, "w"),
        "Metodo":      (110, "w"),
        "Ora":         (60,  "center"),
        "Tag":         (180, "w"),
    }
    for c, (w, anc) in col_cfg.items():
        tv.column(c, width=w, anchor=anc, stretch=True)
        tv.heading(c, text=c, command=lambda _c=c: self.treeview_sort_column(tv, _c, False))
    tv.tag_configure("entrata", foreground="green")
    tv.tag_configure("uscita",  foreground="red")
    tv.tag_configure("futuro",  foreground="#E5C07B", font=("Arial", 9, "italic"))
    tv.tag_configure("sforato", foreground='#C08081', font=("Arial", 9, "bold"))
    def _on_right_click(event):
        item = tv.identify_row(event.y)
        if not item:
            return
        tv.selection_set(item)
        vals = tv.item(item, "values")
        if not vals or len(vals) < 9:
            return
        categoria   = str(vals[1]).strip()
        descrizione = str(vals[2]).strip()
        importo_str = str(vals[3]).replace("€", "").replace(",", ".").strip()
        tipo        = str(vals[4]).strip()
        cat_match = next(
            (c for c in self.categorie if c.strip().lower() == categoria.lower()),
            None
        )
        if cat_match:
            self.cat_sel.set(cat_match)
            self.cat_menu.set(cat_match)
            self.on_categoria_changed(manuale=False)
        try:
            self.imp_entry.delete(0, tk.END)
            self.imp_entry.insert(0, f"{float(importo_str):.2f}".replace(".", ","))
        except ValueError:
            pass
        self.desc_entry.delete(0, tk.END)
        desc_pulita = descrizione.replace("ALL·", "").strip()
        self.desc_entry.insert(0, desc_pulita[:30])
        if self.tipo_spesa_var.get() != tipo:
            self.toggle_tipo_spesa()
        tags_str = str(vals[8]).strip()
        if tags_str:
            self.tag_entry.delete(0, tk.END)
            self.tag_entry.insert(0, tags_str[:15])
        win.destroy()
        self.show_toast("Movimento copiato nel form")
    tv.bind("<Button-3>", _on_right_click)
    tv.bind("<Double-1>", _on_double_click)
    self._bind_tooltip_metodo(tv, col_desc=2)
    riepilogo_frame = ttk.LabelFrame(win, text=" Riepilogo Avanzato",
                                     style="RedBold.TLabelframe")
    riepilogo_frame.pack(fill="x", padx=10, pady=(4,2))

    self._lbl_tag_tot_voci  = tk.Label(riepilogo_frame, text="Voci taggate:",
                                        bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                                        font=("Arial", 8))
    self._lbl_tag_tot_voci.pack(side="left", padx=12, pady=3)
    self._lbl_tag_uniq      = tk.Label(riepilogo_frame, text="Tag unici:",
                                        bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                                        font=("Arial", 8))
    self._lbl_tag_uniq.pack(side="left", padx=12)
    self._lbl_tag_importo   = tk.Label(riepilogo_frame, text="Totale importi:",
                                        bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                                        font=("Arial", 8))
    self._lbl_tag_importo.pack(side="left", padx=12)
    self._lbl_tag_tag_freq  = tk.Label(riepilogo_frame, text="Tag più usato:",
                                        bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                                        font=("Arial", 8))
    self._lbl_tag_tag_freq.pack(side="left", padx=12)
    btn_bar = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    btn_bar.pack(fill="x", padx=10, pady=(4,8))
    def _mk_btn(icona_key, testo, comando, side="left", padx=6):
        img = self.icone_gui.get(icona_key)
        b = ttk.Label(btn_bar, compound="left", image=img,
                      text=f" {testo}" if img else testo,
                      background=self.COLOR_WIDGET_BG,
                      foreground=self.TEXT_COLOR,
                      cursor="hand2", padding=(8, 4))
        b.image = img
        b.pack(side=side, padx=padx)
        b.bind("<Button-1>", lambda e: comando())
        return b
    _mk_btn("filtri",   "Modifica Tag",   _modifica_tag_selezionato)
    _mk_btn("delete",   "Elimina Tag",    _elimina_tag_selezionati)
    _mk_btn("reset",    "Reset Filtri",   _reset_filtri)
    _mk_btn("salva",    "Salva / Preview", _salva_e_preview)
    _mk_btn("chiudi",   "Chiudi",         _chiudi, side="right")
    _popola(filtri_attivi)
    win.deiconify()
    win.after(50, win.focus_force)
    
