#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import datetime
import tkinter as tk
from tkinter import ttk

def apri_schedulatore(self):
    import __main__ as _app
    SCHEDULE_FILE = _app.SCHEDULE_FILE
    EMAIL_USER = _app.EMAIL_USER
    APP_PASSWORD = _app.APP_PASSWORD

    if hasattr(self, '_win_scheduler') and self._win_scheduler and self._win_scheduler.winfo_exists():
        self._win_scheduler.lift()
        self._win_scheduler.focus_force()
        return
    TIPI = [
        ("estratto_mensile",      "Estratto Mensile"),
        ("estratto_annuale",      "Estratto Annuale"),
        ("riepilogo_settimanale", "Riepilogo Settimanale"),
        ("giornaliero",           "Registro Giornaliero"),
        ("controllo_ricorrenti",  "Ricorrenti Mancanti"),
        ("allerta_saldo_negativo","Allerta Saldo Negativo"),
        ("promemoria_libero",     "Promemoria Libero"),
    ]
    TIPI_LABEL   = [t[1] for t in TIPI]
    TIPI_ID      = {t[1]: t[0] for t in TIPI}
    TIPI_LABEL_R = {t[0]: t[1] for t in TIPI}
    FREQUENZE  = ["giornaliero", "settimanale", "mensile", "annuale", "5gg fine mese"]
    MESI_NOMI  = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                  "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
    VALID_TYPES = [t[0] for t in TIPI]
    def _carica():
        if os.path.exists(SCHEDULE_FILE):
            try:
                with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []
    def _salva(tasks):
        try:
            with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
                json.dump(tasks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.show_toast(f"Errore salvataggio schedule: {e}", duration=3000)
    tasks = _carica()
    win = tk.Toplevel(self)
    self._win_scheduler = win
    win.transient(self)
    win.withdraw()
    win.title("Schedulatore Notifiche Email — OrbitaCasa")
    win.configure(bg=self.COLOR_TOPLEVEL)
    win.resizable(False, False)
    W, H = 1360, 600
    self.update_idletasks()
    pos_x = self.winfo_rootx() + (self.winfo_width() // 2) - (W // 2)
    pos_y = self.winfo_rooty() + (self.winfo_height() // 2) - (H // 2)
    win.geometry(f"{W}x{H}+{max(0, pos_x)}+{max(0, pos_y)}")
    def _chiudi():
        self.unbind("<Map>")
        self.unbind("<Unmap>")
        win.destroy()
    win.bind("<Escape>", lambda e: _chiudi())
    win.protocol("WM_DELETE_WINDOW", _chiudi)
    def _on_iconify(e):
        if self.state() == "iconic":
            win.withdraw()
        else:
            win.deiconify()
    self.bind("<Map>", _on_iconify)
    self.bind("<Unmap>", _on_iconify)
    hdr = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    hdr.pack(fill=tk.X, padx=15, pady=(12, 4))
    img_timer = self.icone_gui.get("timer_sync")
    tk.Label(hdr, image=img_timer, text="  Schedulatore Notifiche Email",
             compound="left", bg=self.COLOR_TOPLEVEL, fg=self.COLOR_HEADER,
             font=("Arial", 13, "bold")).pack(side=tk.LEFT)
    ttk.Separator(win, orient="horizontal").pack(fill=tk.X, padx=15, pady=(0, 8))
    corpo = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    corpo.pack(fill=tk.BOTH, expand=True, padx=15)
    col_sx = tk.Frame(corpo, bg=self.COLOR_TOPLEVEL)
    col_sx.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
    tk.Label(col_sx, text="Notifiche email pianificate", bg=self.COLOR_TOPLEVEL,
             fg=self.COLOR_HEADER, font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 4))
    cols = ("nome", "tipo", "frequenza", "orario", "giorno", "email", "ultima", "prossima")
    tree = ttk.Treeview(col_sx, columns=cols, show="headings", height=14)
    hdrs = {
        "nome":     ("Nome Notifica / Oggetto", 160),
        "tipo":     ("Tipo Report",             160),
        "frequenza":("Frequenza",                90),
        "orario":   ("Orario",                   60),
        "giorno":   ("Giorno",                   55),
        "email":    ("Invio",                    45),
        "ultima":   ("Ultimo Invio",             95),
        "prossima": ("Prossimo Invio",           95),
    }
    for c, (lbl, w) in hdrs.items():
        tree.heading(c, text=lbl, anchor="w" if c == "nome" else "center")
        tree.column(c, width=w, anchor="w" if c == "nome" else "center")
    sb = ttk.Scrollbar(col_sx, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=sb.set)
    sb.pack(side=tk.RIGHT, fill=tk.Y)
    tree.pack(fill=tk.BOTH, expand=True)
    col_dx = tk.Frame(corpo, bg=self.COLOR_TOPLEVEL, width=440)
    col_dx.pack(side=tk.LEFT, fill=tk.Y)
    col_dx.pack_propagate(False)
    tk.Label(col_dx, text="Configurazione Notifica", bg=self.COLOR_TOPLEVEL,
             fg=self.COLOR_HEADER, font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 6))
    _editing_idx = [None]
    def _lbl(testo):
        tk.Label(col_dx, text=testo, bg=self.COLOR_TOPLEVEL,
                 fg=self.TEXT_COLOR, font=("Arial", 9, "bold")).pack(anchor="w", pady=(5, 1))
    var_tipo = tk.StringVar(value=TIPI_LABEL[0])
    var_nome = tk.StringVar(value=TIPI_LABEL[0])
    def _on_tipo_cambiato(event=None):
        if _editing_idx[0] is None:
            var_nome.set(var_tipo.get())
    _lbl("Tipo di Report:")
    cb_tipo = ttk.Combobox(col_dx, textvariable=var_tipo, values=TIPI_LABEL,
                           state="readonly", style="Border.TCombobox", width=38)
    cb_tipo.pack(fill=tk.X)
    cb_tipo.bind("<<ComboboxSelected>>", _on_tipo_cambiato)
    _lbl("Nome notifica / Oggetto Email:")
    ttk.Entry(col_dx, textvariable=var_nome, width=40).pack(fill=tk.X)
    _lbl("Frequenza Invio:")
    var_freq = tk.StringVar(value="mensile")
    cb_freq = ttk.Combobox(col_dx, textvariable=var_freq, values=FREQUENZE,
                           state="readonly", style="Border.TCombobox", width=38)
    cb_freq.pack(fill=tk.X)
    f_gg = tk.Frame(col_dx, bg=self.COLOR_TOPLEVEL)
    f_gg.pack(fill=tk.X, pady=(4, 0))
    tk.Label(f_gg, text="Giorno del mese:", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 9, "bold")).pack(side=tk.LEFT)
    var_giorno = tk.StringVar(value="1")
    ttk.Spinbox(f_gg, from_=1, to=31, textvariable=var_giorno,
                width=5, style="Custom.TSpinbox", state="readonly").pack(side=tk.LEFT, padx=6)
    tk.Label(f_gg, text="  Mese (per annuale):", bg=self.COLOR_TOPLEVEL,
             fg=self.TEXT_COLOR, font=("Arial", 9, "bold")).pack(side=tk.LEFT)
    var_mese_anno = tk.StringVar(value="Gennaio")
    ttk.Combobox(f_gg, textvariable=var_mese_anno, values=MESI_NOMI,
                 state="readonly", style="Border.TCombobox", width=10).pack(side=tk.LEFT, padx=4)
    _lbl("Orario di invio (HH:MM):")
    var_orario = tk.StringVar(value="08:00")
    _orari_rapidi = [f"{h:02d}:{m:02d}" for h in range(24) for m in range(0, 60, 5)]
    ttk.Combobox(col_dx, textvariable=var_orario, values=_orari_rapidi,
         style="Border.TCombobox", width=9).pack(anchor="w")
    var_email = tk.BooleanVar(value=True)
    _lbl("Destinatario email:")
    var_dest = tk.StringVar(value=EMAIL_USER or "")
    ttk.Entry(col_dx, textvariable=var_dest, width=40).pack(fill=tk.X)
    _lbl("Note / Testo personalizzato promemoria:")
    var_note = tk.StringVar()
    ttk.Entry(col_dx, textvariable=var_note, width=40).pack(fill=tk.X)
    var_attivo = tk.BooleanVar(value=True)
    ttk.Checkbutton(col_dx, text="Pianificazione Attiva", variable=var_attivo,
                    style="Custom.TRadiobutton").pack(anchor="w", pady=(8, 0))
    ttk.Separator(col_dx, orient="horizontal").pack(fill=tk.X, pady=10)
    def _calcola_prossima(task):
        freq = task.get("frequenza", "mensile")
        orario = task.get("orario", "08:00")
        gg = int(task.get("giorno_mese", 1))
        mese_config = task.get("mese_anno", 1)
        if isinstance(mese_config, str):
            mese_a = MESI_NOMI.index(mese_config) + 1 if mese_config in MESI_NOMI else 1
        else:
            mese_a = int(mese_config)
        oggi = datetime.date.today()
        try:
            hh, mm = map(int, orario.split(":"))
        except Exception:
            hh, mm = 8, 0
        if freq == "giornaliero":
            dt = datetime.datetime.combine(oggi, datetime.time(hh, mm))
            if dt <= datetime.datetime.now():
                dt += datetime.timedelta(days=1)
        elif freq == "settimanale":
            dt = datetime.datetime.combine(oggi + datetime.timedelta(days=7), datetime.time(hh, mm))
        elif freq == "mensile":
            m, y = oggi.month, oggi.year
            if oggi.day >= gg:
                m += 1
                if m > 12:
                    m, y = 1, y + 1
            try:
                dt = datetime.datetime(y, m, gg, hh, mm)
            except ValueError:
                dt = datetime.datetime(y, m, 28, hh, mm)
        elif freq == "annuale":
            y = oggi.year
            try:
                dt = datetime.datetime(y, mese_a, gg, hh, mm)
                if dt.date() <= oggi:
                    dt = datetime.datetime(y + 1, mese_a, gg, hh, mm)
            except ValueError:
                dt = datetime.datetime(y + 1, mese_a, 28, hh, mm)
        elif freq == "5gg fine mese":
            m, y = oggi.month, oggi.year
            if m == 12:
                ultimo_giorno = datetime.date(y, 12, 31)
            else:
                ultimo_giorno = datetime.date(y, m + 1, 1) - datetime.timedelta(days=1)
            data_target = ultimo_giorno - datetime.timedelta(days=5)
            dt = datetime.datetime(data_target.year, data_target.month, data_target.day, hh, mm)
            if dt.date() <= oggi:
                if m == 12:
                    y_next, m_next = y + 1, 1
                else:
                    y_next, m_next = y, m + 1
                if m_next == 12:
                    ultimo_giorno_next = datetime.date(y_next, 12, 31)
                else:
                    ultimo_giorno_next = datetime.date(y_next, m_next + 1, 1) - datetime.timedelta(days=1)
                data_target_next = ultimo_giorno_next - datetime.timedelta(days=5)
                dt = datetime.datetime(data_target_next.year, data_target_next.month, data_target_next.day, hh, mm)
        else:
            dt = datetime.datetime.now() + datetime.timedelta(days=1)
        return dt.strftime("%d/%m/%Y %H:%M")
    def _aggiorna_tree():
        if not win.winfo_exists():
            return
        sel = tree.selection()
        tree.delete(*tree.get_children())
        current_tasks = _carica()
        tasks.clear()
        tasks.extend(current_tasks)
        for i, t in enumerate(tasks):
            if t.get("tipo") not in VALID_TYPES:
                continue
            email_s  = "✉" if t.get("email", True) else "—"
            attivo_s = "" if t.get("attivo", True) else "⏸ "
            prossima = _calcola_prossima(t)
            tag = "attivo" if t.get("attivo", True) else "pausa"
            tree.insert("", "end", iid=str(i), tags=(tag,),
                        values=(attivo_s + t.get("nome", ""),
                                TIPI_LABEL_R.get(t.get("tipo", ""), t.get("tipo", "")),
                                t.get("frequenza", ""),
                                t.get("orario", ""),
                                t.get("giorno_mese", ""),
                                email_s,
                                t.get("ultima_esecuzione", "—"),
                                prossima))
        tree.tag_configure("attivo", foreground=self.COLOR_GREEN)
        tree.tag_configure("pausa",  foreground=self.TEXT_COLOR)
        if sel and tree.exists(sel[0]):
            tree.selection_set(sel[0])
            tree.focus(sel[0])
    def _tick():
        if win.winfo_exists():
            _aggiorna_tree()
            win.after(30000, _tick)
    def _form_svuota():
        _editing_idx[0] = None
        tree.selection_remove(tree.selection())
        var_tipo.set(TIPI_LABEL[0])
        var_nome.set(TIPI_LABEL[0])
        var_freq.set("mensile")
        var_giorno.set("1")
        var_mese_anno.set("Gennaio")
        var_orario.set("08:00")
        var_email.set(True)
        var_dest.set(EMAIL_USER or "")
        var_note.set("")
        var_attivo.set(True)
    def _form_carica(idx):
        t = tasks[idx]
        _editing_idx[0] = idx
        var_tipo.set(TIPI_LABEL_R.get(t.get("tipo", ""), TIPI_LABEL[0]))
        var_nome.set(t.get("nome", ""))
        var_freq.set(t.get("frequenza", "mensile"))
        var_giorno.set(str(t.get("giorno_mese", 1)))
        m_conf = t.get("mese_anno", 1)
        if isinstance(m_conf, str):
            var_mese_anno.set(m_conf if m_conf in MESI_NOMI else "Gennaio")
        else:
            var_mese_anno.set(MESI_NOMI[int(m_conf) - 1])
        var_orario.set(t.get("orario", "08:00"))
        var_email.set(t.get("email", True))
        var_dest.set(t.get("destinatario", EMAIL_USER or ""))
        var_note.set(t.get("note", ""))
        var_attivo.set(t.get("attivo", True))
    def _on_tree_select(e):
        sel = tree.selection()
        if sel:
            _form_carica(int(sel[0]))
    tree.bind("<<TreeviewSelect>>", _on_tree_select)
    def _form_to_dict():
        try:
            hh, mm = var_orario.get().strip().split(":")
            assert 0 <= int(hh) <= 23 and 0 <= int(mm) <= 59
            orario_ok = f"{int(hh):02d}:{int(mm):02d}"
        except Exception:
            self.show_toast("Orario non valido — usa HH:MM", duration=3000)
            return None
        return {
            "nome":             var_nome.get().strip() or var_tipo.get(),
            "tipo":             TIPI_ID.get(var_tipo.get(), "promemoria_libero"),
            "frequenza":        var_freq.get(),
            "giorno_mese":      int(var_giorno.get()),
            "mese_anno":        MESI_NOMI.index(var_mese_anno.get()) + 1,
            "orario":           orario_ok,
            "email":            var_email.get(),
            "destinatario":     var_dest.get().strip(),
            "note":             var_note.get().strip(),
            "attivo":           var_attivo.get(),
            "ultima_esecuzione": "",
        }
    def _salva_task():
        d = _form_to_dict()
        if d is None:
            return
        idx = _editing_idx[0]
        if idx is None:
            tasks.append(d)
        else:
            d["ultima_esecuzione"] = tasks[idx].get("ultima_esecuzione", "")
            tasks[idx] = d
        _salva(tasks)
        _aggiorna_tree()
        _form_svuota()
        self.show_toast("Pianificazione salvata.", duration=2000)
    def _elimina_task():
        sel = tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        nome = tasks[idx].get("nome", "?")
        if not self.show_custom_askyesno("Elimina", f"Eliminare la pianificazione '{nome}'?"):
            return
        tasks.pop(idx)
        _salva(tasks)
        _aggiorna_tree()
        _form_svuota()
    def _toggle_attivo():
        sel = tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        tasks[idx]["attivo"] = not tasks[idx].get("attivo", True)
        _salva(tasks)
        _aggiorna_tree()
    def _esegui_ora():
        sel = tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        task = tasks[idx]
        nome = task.get("nome", "")
        tipo = task.get("tipo", "")
        dest = task.get("destinatario", EMAIL_USER) or EMAIL_USER
        def _run():
            try:
                corpo = ""
                if tipo == "estratto_mensile":
                    corpo = self._genera_testo_estratto_mensile()
                elif tipo == "estratto_annuale":
                    corpo = self._genera_testo_estratto_annuale()
                elif tipo in ("riepilogo_settimanale", "giornaliero"):
                    corpo = self._genera_testo_riepilogo_cronologico(tipo)
                elif tipo == "promemoria_libero":
                    corpo = (
                        f"PROMEMORIA DIRETTO\n"
                        f"────────────────────────────\n"
                        f" 📝 Nota:\n"
                        f" {task.get('note', '')}\n\n"
                        f"────────────────────────────\n"
                        f" 📊 Report generato il {datetime.date.today().strftime('%d/%m/%Y')}."
                    )
                elif tipo == "controllo_ricorrenti":
                    corpo = self._genera_testo_ricorrenti_mancanti()
                if corpo and EMAIL_USER and APP_PASSWORD:
                    import threading
                    threading.Thread(
                        target=self._invia_email_scheduler,
                        args=(nome, corpo, dest),
                        daemon=True
                    ).start()
                tasks[idx]["ultima_esecuzione"] = datetime.date.today().strftime("%d/%m/%Y")
                _salva(tasks)
                self.after(0, _aggiorna_tree)
                self.after(0, lambda: self.show_toast(f"Email Inviata Ora: {nome}", duration=3000))
            except Exception as ex:
                print(f"[SCHEDULER] Errore invio manuale: {ex}")
        import threading
        threading.Thread(target=_run, daemon=True).start()
    def _apri_gcalendar():
        sel = tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        task = tasks[idx]
        self.launch_qr_svg_generator(
            initial_category=task.get("nome", ""),
            initial_description=task.get("note", ""),
            initial_type="Promemoria"
        )
    f_btn_form = tk.Frame(col_dx, bg=self.COLOR_TOPLEVEL)
    f_btn_form.pack(fill=tk.X)
    pulsanti_form = [
        ("salva", " Salva Notifica",  lambda e: _salva_task()),
        ("reset", " Nuova Notifica",  lambda e: _form_svuota()),
    ]
    for ico, testo, cmd in pulsanti_form:
        img = self.icone_gui.get(ico)
        b = ttk.Label(f_btn_form, compound="left", image=img,
                      text=testo if img else testo.strip(),
                      background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                      cursor="hand2", padding=(10, 5))
        b.pack(side=tk.LEFT, padx=3)
        b.bind("<Button-1>", cmd)
    ttk.Separator(win, orient="horizontal").pack(fill=tk.X, padx=15, pady=(8, 0))
    btn_frame = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    btn_frame.pack(fill=tk.X, padx=15, pady=8)
    pulsanti = [
        ("check",      " Invia Ora via Email", lambda e: _esegui_ora(),     "LEFT"),
        ("timer_sync", " Attiva/Pausa",         lambda e: _toggle_attivo(),  "LEFT"),
        ("delete",     " Elimina",              lambda e: _elimina_task(),   "LEFT"),
        ("qr_code",    " GCalendar",            lambda e: _apri_gcalendar(), "LEFT"),
        ("chiudi",     " Chiudi",               lambda e: _chiudi(),         "RIGHT"),
    ]
    for ico, testo, cmd, lato in pulsanti:
        img = self.icone_gui.get(ico)
        b = ttk.Label(btn_frame, compound="left", image=img,
                      text=testo if img else testo.strip(),
                      background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR,
                      cursor="hand2", padding=(10, 5))
        b.pack(side=tk.LEFT if lato == "LEFT" else tk.RIGHT, padx=4)
        b.bind("<Button-1>", cmd)
    win.deiconify()
    win.lift()
    win.focus_force()
    _aggiorna_tree()
    _tick()

    # Andamento Risparmio
