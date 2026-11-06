#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import json
import os
import tkinter as tk
from tkinter import ttk, filedialog

def _fmt_quando(q):
    try:
        return datetime.datetime.fromisoformat(q).strftime("%d/%m/%Y %H:%M")
    except Exception:
        return str(q or "")[:16].replace("T", " ")

def apri_notifiche_ricevute(self):
    import __main__ as _app
    from moduli import notifiche_spese as ns
    from moduli import log_importazioni as li
    from moduli.webhook_notifiche import _leggi_ultime, svuota
    from moduli.modello_spesa import METODI_PAGAMENTO, METODI_PAGAMENTO_EMOJI, metodo_con_emoji, metodo_pagamento_pulito, campo
    SpesaEntry = _app.SpesaEntry

    if getattr(self, "_notifiche_popup", None) and self._notifiche_popup.winfo_exists():
        self._notifiche_popup.lift()
        self._notifiche_popup.focus_force()
        return

    popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
    self._notifiche_popup = popup
    popup.bind("<Destroy>", lambda e: setattr(self, "_notifiche_popup", None) if e.widget is popup else None)
    popup.transient(self)
    popup.withdraw()
    popup.title(" Notifiche e spese da confermare")
    popup.resizable(True, True)
    w, h = 1200, 640
    popup.minsize(980, 540)
    popup.columnconfigure(0, weight=1)
    popup.rowconfigure(0, weight=1)

    def centra():
        x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
        y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
        popup.geometry(f"{w}x{h}+{max(x, 0)}+{max(y, 0)}")
        popup.deiconify()
        popup.lift()
        popup.focus_force()
    popup.after(0, centra)
    popup.bind("<Escape>", lambda e: popup.destroy())

    def _nomi_conti():
        try:
            with open(_app.PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as f:
                db = json.load(f)
            return [c.get("nome", "") for c in db.get("conti", []) if c.get("nome")]
        except Exception:
            return []
    conti = ["(nessuno)"] + _nomi_conti()
    metodi = [""] + list(METODI_PAGAMENTO)
    metodi_emoji = [""] + list(METODI_PAGAMENTO_EMOJI)

    def _bottone(parent, icona, testo, colore):
        return ttk.Label(parent, image=self.icone_gui.get(icona), text=testo, compound="left",
                         cursor="hand2", background=self.COLOR_BACKGROUND, foreground=colore,
                         font=("Arial", 9, "bold"))

    nb = ttk.Notebook(popup)
    nb.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

    tab1 = ttk.Frame(nb)
    tab1.columnconfigure(0, weight=1)
    tab1.rowconfigure(0, weight=1)
    nb.add(tab1, text="Da confermare")

    col1 = ("Data", "App", "Descrizione", "Importo", "Tipo", "Fonte", "Notifica")
    lar1 = (130, 110, 220, 80, 70, 70, 400)
    tv = ttk.Treeview(tab1, columns=col1, show="headings", selectmode="browse")
    for c, l in zip(col1, lar1):
        tv.heading(c, text=c, anchor="w")
        tv.column(c, width=l, minwidth=l, anchor="w", stretch=(c == "Notifica"))
    sb = ttk.Scrollbar(tab1, orient="vertical", command=tv.yview)
    tv.configure(yscrollcommand=sb.set)
    tv.grid(row=0, column=0, sticky="nsew")
    sb.grid(row=0, column=1, sticky="ns")
    prop = {}

    form = ttk.Frame(tab1)
    form.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
    v_desc, v_imp = tk.StringVar(), tk.StringVar()
    v_tipo, v_cat = tk.StringVar(value="Uscita"), tk.StringVar()
    v_conto, v_metodo, v_tag = tk.StringVar(value="(nessuno)"), tk.StringVar(), tk.StringVar()

    ttk.Label(form, text="Descrizione").grid(row=0, column=0, padx=4, pady=2)
    ttk.Entry(form, textvariable=v_desc, width=34).grid(row=0, column=1, padx=4)
    ttk.Label(form, text="Importo").grid(row=0, column=2, padx=4)
    ttk.Entry(form, textvariable=v_imp, width=10).grid(row=0, column=3, padx=4)
    ttk.Combobox(form, textvariable=v_tipo, values=("Uscita", "Entrata"), width=8,
                 state="readonly", style="Border.TCombobox").grid(row=0, column=4, padx=4)
    ttk.Label(form, text="Categoria").grid(row=0, column=5, padx=4)
    ttk.Combobox(form, textvariable=v_cat, values=list(self.categorie), width=22,
                 state="readonly", style="Border.TCombobox").grid(row=0, column=6, padx=4)

    ttk.Label(form, text="Conto").grid(row=1, column=0, padx=4, pady=(6, 2), sticky="e")
    ttk.Combobox(form, textvariable=v_conto, values=conti, width=31,
                 state="readonly", style="Border.TCombobox").grid(row=1, column=1, padx=4, pady=(6, 2), sticky="w")
    ttk.Label(form, text="Metodo").grid(row=1, column=2, padx=4, pady=(6, 2))
    ttk.Combobox(form, textvariable=v_metodo, values=metodi_emoji, width=16,
                 state="readonly", style="Border.TCombobox").grid(row=1, column=3, columnspan=2, padx=4, pady=(6, 2), sticky="w")
    ttk.Label(form, text="Tag").grid(row=1, column=5, padx=4, pady=(6, 2))
    ttk.Entry(form, textvariable=v_tag, width=25).grid(row=1, column=6, padx=4, pady=(6, 2), sticky="w")

    btn_ok = _bottone(form, "check", " Conferma", self.COLOR_GREEN)
    btn_no = _bottone(form, "delete", " Scarta", self.COLOR_RED_SMOOTH)
    btn_ok.grid(row=0, column=7, rowspan=2, padx=(12, 4))
    btn_no.grid(row=0, column=8, rowspan=2, padx=4)
    lbl = ttk.Label(tab1, text="", foreground="gray")
    lbl.grid(row=2, column=0, columnspan=2, sticky="w", pady=(6, 0))

    def ricarica_coda():
        sel = tv.selection()
        sel_id = sel[0] if sel else None
        tv.delete(*tv.get_children())
        prop.clear()
        for p in ns.elenco():
            nota = (p.get("title", "") + " — " + p.get("text", "")).replace("\n", " ")[:200]
            iid = tv.insert("", "end", iid=p["id"], values=(
                _fmt_quando(p.get("quando", "")), p.get("app", ""), p["desc"],
                f"{p['importo']:.2f}", p["tipo"], p.get("fonte", ""), nota))
            prop[iid] = p
        if sel_id in prop:
            tv.selection_set(sel_id)
        lbl.config(text=f"{len(prop)} spese in attesa" if prop else "Nessuna spesa da confermare.")
        ns.aggiorna_indicatore(self)

    def su_selezione(_e=None):
        sel = tv.selection()
        if not sel:
            return
        p = prop[sel[0]]
        r = ns.regola_app(p.get("app", ""))
        memoria = getattr(self, "memoria_descrizioni_categoria", {}) or {}
        cat = memoria.get(p["desc"].strip().upper()) or ns.categoria_da_testo(self, p) or r["categoria"]
        if cat not in self.categorie:
            cat = "Generica" if "Generica" in self.categorie else self.categorie[0]
        v_desc.set(p["desc"])
        v_imp.set(f"{p['importo']:.2f}")
        v_tipo.set(p["tipo"])
        v_cat.set(cat)
        conto_p = (p.get("conto") or "").strip()
        conto_p = next((c for c in conti if c.lower() == conto_p.lower()), "") if conto_p else ""
        conto_r = conto_p or r["conto"]
        v_conto.set(conto_r if conto_r in conti else "(nessuno)")
        metodo_p = (p.get("metodo") or "").strip()
        metodo_p = next((m for m in metodi if m and m.lower() == metodo_p.lower()), "") if metodo_p else ""
        metodo_r = metodo_p or r["metodo"]
        v_metodo.set(metodo_con_emoji(metodo_r) if metodo_r in metodi else "")
        tag_p = " ".join("#" + t.lstrip("#") for t in (p.get("tags") or []))
        v_tag.set(tag_p or r["tag"])
    tv.bind("<<TreeviewSelect>>", su_selezione)

    def conferma():
        sel = tv.selection()
        if not sel:
            self.show_toast("Seleziona una voce.")
            return
        p = prop[sel[0]]
        try:
            imp = float(v_imp.get().replace(",", "."))
            if imp <= 0:
                raise ValueError
        except ValueError:
            self.show_toast("Importo non valido.")
            return
        try:
            d = datetime.datetime.fromisoformat(p["quando"]).date()
        except Exception:
            d = datetime.date.today()
        tipo = v_tipo.get()
        cat = v_cat.get() or "Generica"
        desc = v_desc.get().strip()[:60]
        conto = v_conto.get() if v_conto.get() != "(nessuno)" else ""
        metodo = metodo_pagamento_pulito(v_metodo.get())
        tags = self._normalizza_tags(v_tag.get())
        from moduli.sync_mail_opzioni import leggi_opzioni
        if leggi_opzioni(_app.app_config_globale)["controllo_doppioni"] and any(
                campo(e, "descrizione", "") == desc and abs(float(campo(e, "importo", 0.0)) - imp) < 0.01
                for e in self.spese.get(d, [])):
            li.scrivi_riga("DOPPIA", d, desc, imp, tipo, cat)
            ns.scarta(p["id"])
            ricarica_coda()
            self.show_toast("Doppione scartato: era già presente (vedi Log, tipo DOPPIA).", duration=3000)
            return
        voce = SpesaEntry.nuova(cat, desc, imp, tipo, conto=conto, hashtag=tags, metodo_pagamento=metodo)
        self.spese.setdefault(d, []).append(voce) 
        try:
            self.memoria_descrizioni_categoria[desc.upper()] = cat
            with open(_app.MEM_CAT, "w", encoding="utf-8") as f:
                json.dump(self.memoria_descrizioni_categoria, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Notifiche: memoria descrizioni non salvata: {e}")
        ns.ricorda_app(p.get("app", ""), cat, conto, metodo, " ".join(tags))
        li.scrivi_riga("NOTIF", d, desc, imp, tipo, cat, voce)
        self.save_db()
        ns.segna_confermata(p["id"])
        try:
            self.registra_azione_gamification("movimento")
        except Exception:
            pass
        self.refresh_gui()
        self.show_toast("Spesa registrata.")
        ricarica_coda()
        ricarica_ricevute(forza=True)

    def scarta():
        sel = tv.selection()
        if sel:
            ns.scarta(sel[0])
            ricarica_coda()
    btn_ok.bind("<Button-1>", lambda e: conferma())
    btn_no.bind("<Button-1>", lambda e: scarta())
    tv.bind("<Delete>", lambda e: scarta())

    tab2 = ttk.Frame(nb)
    tab2.columnconfigure(0, weight=1)
    tab2.rowconfigure(1, weight=1)
    nb.add(tab2, text="Ricevute")
    ttk.Label(tab2, text="  Doppio clic → Vai alla spesa sulla Dashboard", foreground="gray",
              font=("Arial", 8, "italic")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))
    col2 = ("Registrata", "Data Mov.", "Descrizione", "Importo", "Direzione", "Categoria",
            "Conto", "ID", "Metodo", "Tag")
    lar2 = (160, 80, 300, 90, 80, 140, 120, 0, 100, 130)
    tv2 = ttk.Treeview(tab2, columns=col2, show="headings", selectmode="extended",
                       displaycolumns=[c for c in col2 if c != "ID"])
    for c, l in zip(col2, lar2):
        tv2.heading(c, text=c, anchor="w")
        tv2.column(c, width=l, minwidth=l, anchor="w", stretch=(c == "Tag"))
    sb2 = ttk.Scrollbar(tab2, orient="vertical", command=tv2.yview)
    tv2.configure(yscrollcommand=sb2.set)
    tv2.grid(row=1, column=0, sticky="nsew")
    sb2.grid(row=1, column=1, sticky="ns")
    idx_riga = {}
    stato_log = {"mtime": None}

    def _mtime():
        try:
            return os.path.getmtime(_app.LOG_IMPORTAZIONI)
        except OSError:
            return None

    def ricarica_ricevute(forza=False):
        m = _mtime()
        if not forza and m == stato_log["mtime"]:
            return
        stato_log["mtime"] = m
        tv2.delete(*tv2.get_children())
        idx_riga.clear()
        for n, v in reversed(sorted(li.leggi("NOTIF") + li.leggi("AUTO"), key=lambda x: x[0])):
            iid = tv2.insert("", "end", values=(v[0] + (" · auto" if v[1].upper() == "AUTO" else ""), v[2], v[3], v[4], v[5], v[6], v[7], v[8], v[9], v[10]))
            idx_riga[iid] = n

    def _giorno(testo):
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"):
            try:
                return datetime.datetime.strptime(testo.strip(), fmt).date()
            except ValueError:
                pass
        return None

    def _cerca_per_id(id_spesa):
        if not id_spesa:
            return None
        for g, lista in self.spese.items():
            for v in lista:
                if getattr(v, "id_spesa", None) == id_spesa:
                    return g
        return None

    def vai_alla_spesa(_e=None):
        sel = tv2.selection()
        if not sel:
            return
        v = tv2.item(sel[0], "values")
        id_spesa = str(v[7]).strip()
        giorno = _cerca_per_id(id_spesa) or _giorno(str(v[1]))
        if not giorno or (id_spesa and _cerca_per_id(id_spesa) is None):
            self.show_toast("Spesa non trovata: è stata cancellata o modificata.")
            return
        self.vai_a_spesa(giorno, popup=popup, desc=str(v[2]).strip(), id_spesa=id_spesa)
    tv2.bind("<Double-1>", vai_alla_spesa)

    def pulisci_log():
        orfane = [n for iid, n in idx_riga.items()
                  if _cerca_per_id(str(tv2.item(iid, "values")[7]).strip()) is None]
        if not orfane:
            self.show_toast("Niente da rimuovere: ogni riga ha ancora la sua spesa.", duration=3000)
            return
        if not self.show_custom_askyesno(
                "Pulisci log",
                f"Righe da togliere: {len(orfane)}\n\nSono notifiche registrate la cui spesa non esiste più "
                "(cancellata o modificata). Vengono tolte solo dal log, le spese non vengono toccate. Procedere?"):
            return
        try:
            li.togli(orfane)
        except Exception as e:
            self.show_custom_warning("Errore", f"Log non aggiornato: {e}")
            return
        ricarica_ricevute(forza=True)
        self.show_toast(f"{len(orfane)} {'riga rimossa' if len(orfane) == 1 else 'righe rimosse'} dal log.", duration=3000)

    def azzera_log():
        if nb.select() == str(tab3):
            if not self.show_custom_askyesno(
                    "Azzera notifiche",
                    "Cancellare tutte le notifiche ricevute?\n\n"
                    "Le spese già registrate e il log importazioni non vengono toccati."):
                return
            try:
                svuota()
            except Exception as e:
                self.show_custom_warning("Errore", f"Notifiche non azzerate: {e}")
                return
            ricarica_grezze()
            self.show_toast("Notifiche ricevute azzerate.", duration=2000)
            return
        if not idx_riga:
            self.show_toast("Il log delle notifiche è già vuoto.", duration=2000)
            return
        if not self.show_custom_askyesno(
                "Azzera log",
                f"Togliere dal log le {len(idx_riga)} righe delle notifiche?\n\n"
                "Le righe delle mail e delle altre importazioni non vengono toccate, e le spese restano."):
            return
        try:
            li.togli(list(idx_riga.values()))
        except Exception as e:
            self.show_custom_warning("Errore", f"Log non aggiornato: {e}")
            return
        ricarica_ricevute(forza=True)
        self.show_toast("Log notifiche azzerato.", duration=2000)

    tab3 = ttk.Frame(nb)
    tab3.columnconfigure(0, weight=1)
    tab3.rowconfigure(0, weight=1)
    nb.add(tab3, text="Notifiche")
    col3 = ("Quando", "App", "Titolo", "Testo")
    lar3 = (130, 110, 220, 600)
    tv3 = ttk.Treeview(tab3, columns=col3, show="headings", selectmode="browse")
    for c, l in zip(col3, lar3):
        tv3.heading(c, text=c, anchor="w")
        tv3.column(c, width=l, minwidth=l, anchor="w", stretch=(c == "Testo"))
    sb3 = ttk.Scrollbar(tab3, orient="vertical", command=tv3.yview)
    tv3.configure(yscrollcommand=sb3.set)
    tv3.grid(row=0, column=0, sticky="nsew")
    sb3.grid(row=0, column=1, sticky="ns")

    def ricarica_grezze():
        tv3.delete(*tv3.get_children())
        for n in _leggi_ultime(200):
            tv3.insert("", "end", values=(
                _fmt_quando(n.get("quando", "")), n.get("app", ""),
                n.get("title", "").replace("\n", " ")[:120], n.get("text", "").replace("\n", " ")[:400]))

    def aggiorna():
        if not popup.winfo_exists():
            return
        try:
            if [x["id"] for x in ns.elenco()] != list(tv.get_children()):
                ricarica_coda()
            ricarica_ricevute()
            ricarica_grezze()
        except Exception as e:
            print(f"Notifiche: aggiornamento fallito: {e}")
        popup.after(5000, aggiorna)

    ricarica_coda()
    ricarica_ricevute(forza=True)
    ricarica_grezze()
    popup.after(5000, aggiorna)

    def _righe_export():
        sel = nb.select()
        if sel == str(tab2):
            titolo, colonne, albero = "RICEVUTE", col2, tv2
        elif sel == str(tab3):
            titolo, colonne, albero = "NOTIFICHE", col3, tv3
        else:
            titolo, colonne, albero = "DA CONFERMARE", col1, tv
        dati = []
        for iid in albero.get_children():
            vals = albero.item(iid, "values")
            riga = [str(x).replace("\n", " ").strip() for x in vals]
            riga += [""] * (len(colonne) - len(riga))
            dati.append(riga[:len(colonne)])
        if not dati:
            return titolo, []
        usa = [i for i, c in enumerate(colonne) if c != "ID"]
        dati = [[(d[i] if len(d[i]) <= 80 else d[i][:79] + "…") for i in range(len(colonne))] for d in dati]
        larg = {i: max(len(colonne[i]), *(len(d[i]) for d in dati)) for i in usa}
        def cella(v, i):
            return v[i].rjust(larg[i]) if colonne[i] == "Importo" else v[i].ljust(larg[i])
        def fmt(v):
            return " | ".join(cella(v, i) for i in usa).rstrip()
        return titolo, [fmt(colonne), "-+-".join("-" * larg[i] for i in usa)] + [fmt(d) for d in dati]

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
        if hasattr(anteprima_esporta, "_win") and anteprima_esporta._win.winfo_exists():
            anteprima_esporta._win.lift()
            anteprima_esporta._win.focus_force()
            return
        titolo, lines = _righe_export()
        if not lines:
            self.show_custom_warning("Errore", "Nessun dato da esportare in questa scheda.")
            return
        now = datetime.datetime.now()
        testo = f"NOTIFICHE {titolo} - {now.strftime('%d/%m/%Y %H:%M')}\n\n" + "\n".join(lines) + "\n"
        nome_base = f"Notifiche_{titolo.title().replace(' ', '_')}_{now.day:02d}-{now.month:02d}-{now.year}"
        prev_win = tk.Toplevel(popup, bg=self.COLOR_TOPLEVEL)
        anteprima_esporta._win = prev_win
        prev_win.withdraw()
        prev_win.title("Esportazione Notifiche")
        prev_win.bind("<Escape>", lambda e: prev_win.destroy())
        prev_win.transient(popup)
        def centra_prev():
            if not prev_win.winfo_exists():
                return
            w_a, h_a = 1100, 600
            x = popup.winfo_rootx() + (popup.winfo_width() // 2) - (w_a // 2)
            y = popup.winfo_rooty() + (popup.winfo_height() // 2) - (h_a // 2)
            prev_win.geometry(f"{w_a}x{h_a}+{x}+{y}")
            prev_win.minsize(w_a, h_a)
            prev_win.deiconify()
        prev_win.after(0, centra_prev)
        def do_pdf():
            f_path = filedialog.asksaveasfilename(
                defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
                initialdir=_app.EXPORT_FILES, initialfile=nome_base + ".pdf",
                confirmoverwrite=False, parent=prev_win)
            if f_path:
                try:
                    _crea_pdf(f_path, testo.split("\n"))
                    self.show_toast("PDF salvato.")
                except Exception as ex:
                    self.show_custom_warning("Errore PDF", str(ex))
        def do_txt():
            f_path = filedialog.asksaveasfilename(
                defaultextension=".txt", filetypes=[("TXT", "*.txt")],
                initialdir=_app.EXPORT_FILES, initialfile=nome_base + ".txt",
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
            b.pack(side=tk.LEFT, padx=5)
            b.bind("<Button-1>", lambda e, c=cmd: c())
        img_c = self.icone_gui.get("chiudi")
        bc = ttk.Label(bf, compound="left", image=img_c, text=" Chiudi",
                       background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                       cursor="hand2", padding=(10, 5))
        bc.pack(side=tk.RIGHT, padx=10)
        bc.bind("<Button-1>", lambda e: prev_win.destroy())

    btns = tk.Frame(popup, bg=self.COLOR_BACKGROUND)
    btns.grid(row=1, column=0, pady=10, padx=15, sticky="ew")
    for i in range(4):
        btns.columnconfigure(i, weight=1)
    lbl_esporta = _bottone(btns, "salva", " Esporta", self.COLOR_HEADER)
    lbl_esporta.grid(row=0, column=0, padx=5, sticky="ew")
    lbl_esporta.bind("<Button-1>", lambda e: anteprima_esporta())
    lbl_pulisci = ttk.Label(btns, image=self.icone_gui.get("filtri"), text=" Pulisci log", compound="left",
                            cursor="hand2", background=self.COLOR_BACKGROUND, foreground=self.COLOR_HEADER,
                            font=("Arial", 9, "bold"))
    lbl_pulisci.grid(row=0, column=1, padx=5, sticky="ew")
    lbl_pulisci.bind("<Button-1>", lambda e: pulisci_log())
    lbl_azzera = _bottone(btns, "delete", " Azzera Log", self.COLOR_RED_SMOOTH)
    lbl_azzera.grid(row=0, column=2, padx=5, sticky="ew")
    lbl_azzera.bind("<Button-1>", lambda e: azzera_log())
    lbl_chiudi = ttk.Label(btns, image=self.icone_gui.get("chiudi"), text=" Chiudi", compound="left",
                           cursor="hand2", background=self.COLOR_BACKGROUND, foreground=self.COLOR_HEADER,
                           font=("Arial", 9, "bold"))
    lbl_chiudi.grid(row=0, column=3, padx=5, sticky="ew")
    lbl_chiudi.bind("<Button-1>", lambda e: popup.destroy())
