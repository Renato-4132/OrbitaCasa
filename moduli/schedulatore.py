#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import datetime
import tkinter as tk
from tkinter import ttk

from moduli.modello_spesa import campo
from moduli.mappa_conti_trasferimenti import e_trasferimento_virtuale

def _fmt_it(v, spec=",.2f"):
    s = format(v, spec)
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")

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
        ("estratto_trasferimenti","Trasferimenti tra Conti"),
        ("riepilogo_settimanale", "Riepilogo Settimanale"),
        ("giornaliero",           "Registro Giornaliero"),
        ("controllo_ricorrenti",  "Ricorrenti Mancanti"),
        ("scadenze_veicoli",      "Scadenze Veicoli"),
        ("documenti_scadenza",    "Documenti in Scadenza"),
        ("allerta_saldo_negativo","Allerta Saldo Negativo"),
        ("sforamento_budget",     "Budget Superato"),
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
    def _on_iconify(e):
        if self.state() == "iconic":
            win.withdraw()
        else:
            win.deiconify()
    _map_bind_id = self.bind("<Map>", _on_iconify, add="+")
    _unmap_bind_id = self.bind("<Unmap>", _on_iconify, add="+")
    def _chiudi():
        self.unbind("<Map>", _map_bind_id)
        self.unbind("<Unmap>", _unmap_bind_id)
        win.destroy()
    win.bind("<Escape>", lambda e: _chiudi())
    win.protocol("WM_DELETE_WINDOW", _chiudi)
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
    tree = ttk.Treeview(col_sx, columns=cols, show="headings", height=14, selectmode="browse")
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
            giorni_al_lunedi = (7 - oggi.weekday()) % 7
            prossimo_lunedi = oggi + datetime.timedelta(days=giorni_al_lunedi)
            dt = datetime.datetime.combine(prossimo_lunedi, datetime.time(hh, mm))
            if dt <= datetime.datetime.now():
                dt += datetime.timedelta(days=7)
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
        corpo = ""
        if tipo == "estratto_mensile":
            corpo = self._genera_testo_estratto_mensile()
        elif tipo == "estratto_annuale":
            corpo = self._genera_testo_estratto_annuale()
        elif tipo == "estratto_trasferimenti":
            corpo = self._genera_testo_estratto_trasferimenti()
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
        elif tipo == "scadenze_veicoli":
            corpo = self._genera_testo_scadenze_veicoli()
        elif tipo == "documenti_scadenza":
            profilo_filtro = (task.get("note") or "").strip() or None
            corpo = self._genera_testo_scadenze_documenti(profilo=profilo_filtro)
        elif tipo == "sforamento_budget":
            sforamenti_mese, sforamenti_anno = self._calcola_sforamenti_budget()
            if sforamenti_mese or sforamenti_anno:
                corpo = self._genera_testo_sforamento_budget(sforamenti_mese, sforamenti_anno)
        def _fine(esito, errore=None):
            tasks[idx]["ultima_esecuzione"] = datetime.date.today().strftime("%d/%m/%Y")
            _salva(tasks)
            _aggiorna_tree()
            if esito == "ok":
                self.show_toast(f"Email Inviata Ora: {nome}", duration=3000)
            elif esito == "vuoto":
                self.show_toast(f"Nessuna scadenza da segnalare: email non inviata ({nome})", duration=3500)
            elif esito == "credenziali":
                self.show_toast(f"Email mittente o app password non configurate: '{nome}' non inviata", duration=4500)
            elif esito == "errore":
                self.show_toast(f"Invio '{nome}' fallito: {errore}", duration=4500)
        if not corpo:
            _fine("vuoto")
        elif not (EMAIL_USER and APP_PASSWORD):
            _fine("credenziali")
        else:
            import threading
            def _invia_bg():
                ok, errore = self._invia_email_scheduler(nome, corpo, dest)
                self.after(0, lambda: _fine("ok" if ok else "errore", errore))
            threading.Thread(target=_invia_bg, daemon=True).start()
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

# Motore dello schedulatore: tick periodico, esecuzione task, generazione testi
def _tick_scheduler(self):
    try:
        self._esegui_scheduler()
    except Exception as e:
        ora = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{ora}] [SCHEDULER] Errore tick: {e}")
    self.after(60000, self._tick_scheduler)

def _esegui_scheduler(self):
    import __main__ as _app
    SCHEDULE_FILE = _app.SCHEDULE_FILE
    EMAIL_USER = _app.EMAIL_USER
    APP_PASSWORD = _app.APP_PASSWORD
    if not os.path.exists(SCHEDULE_FILE):
        return
    if not hasattr(self, '_scheduler_lock'):
        import threading
        self._scheduler_lock = threading.Lock()
    with self._scheduler_lock:
        try:
            with open(SCHEDULE_FILE, "r", encoding="utf-8") as f:
                tasks = json.load(f)
        except Exception as e:
            ora = datetime.datetime.now().strftime("%H:%M:%S")
            print(f"[{ora}] [SCHEDULER] ERRORE CRITICO LETTURA JSON: {e}")
            return
        ora_now = datetime.datetime.now()
        oggi = ora_now.date()
        hh_mm_now = ora_now.strftime("%H:%M")
        modificato = False
        for task in tasks:
            if not task.get("attivo", True):
                continue
            orario = task.get("orario", "08:00")
            if hh_mm_now < orario:
                continue
            ultima = task.get("ultima_esecuzione", "")
            try:
                ultima_dt = datetime.datetime.strptime(ultima, "%d/%m/%Y").date() if ultima else None
            except Exception:
                ultima_dt = None
            freq = task.get("frequenza", "mensile")
            try:
                giorno_x = int(task.get("giorno_mese", 1))
                mese_config = task.get("mese_anno", 1)
                if isinstance(mese_config, str):
                    mesi_nomi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                                 "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
                    mese_x = mesi_nomi.index(mese_config) + 1 if mese_config in mesi_nomi else 1
                else:
                    mese_x = int(mese_config)
            except Exception as e:
                ora = datetime.datetime.now().strftime("%H:%M:%S")
                print(f"[{ora}] [SCHEDULER] Errore parsing parametri task '{task.get('nome')}': {e}")
                continue
            deve_girare = False
            if freq == "giornaliero":
                deve_girare = (ultima_dt != oggi)
            elif freq == "settimanale":
                deve_girare = (oggi.weekday() == 0 and ultima_dt != oggi)
            elif freq == "mensile":
                deve_girare = (oggi.day == giorno_x and ultima_dt != oggi)
            elif freq == "annuale":
                deve_girare = (oggi.day == giorno_x and oggi.month == mese_x and ultima_dt != oggi)
            elif freq == "5gg fine mese":
                if oggi.month == 12:
                    ultimo = datetime.date(oggi.year, 12, 31)
                else:
                    ultimo = datetime.date(oggi.year, oggi.month + 1, 1) - datetime.timedelta(days=1)
                target = ultimo - datetime.timedelta(days=5)
                deve_girare = (oggi == target and ultima_dt != oggi)
            if not deve_girare:
                continue
            task["ultima_esecuzione"] = oggi.strftime("%d/%m/%Y")
            modificato = True
            tipo = task.get("tipo", "")
            nome = task.get("nome", tipo)
            invia_email = task.get("email", False)
            dest = task.get("destinatario", EMAIL_USER) or EMAIL_USER
            def _operazioni_gui(t=tipo, n=nome, ie=invia_email, d=dest, tk_task=task):
                try:
                    corpo_mail = ""
                    if t == "estratto_mensile":
                        corpo_mail = self._genera_testo_estratto_mensile()
                    elif t == "estratto_annuale":
                        corpo_mail = self._genera_testo_estratto_annuale()
                    elif t == "estratto_trasferimenti":
                        corpo_mail = self._genera_testo_estratto_trasferimenti()
                    elif t == "riepilogo_settimanale" or t == "giornaliero":
                        corpo_mail = self._genera_testo_riepilogo_cronologico(t)
                    elif t == "controllo_ricorrenti":
                        corpo_mail = self._genera_testo_ricorrenti_mancanti()
                    elif t == "scadenze_veicoli":
                        corpo_mail = self._genera_testo_scadenze_veicoli()
                    elif t == "documenti_scadenza":
                        profilo_filtro = (tk_task.get("note") or "").strip() or None
                        corpo_mail = self._genera_testo_scadenze_documenti(profilo=profilo_filtro)
                    elif t == "allerta_saldo_negativo":
                        saldo_mese = self._calcola_saldo_mese_corrente()
                        ultimo_notificato = tk_task.get("ultimo_saldo_notificato", None)
                        mese_notificato = tk_task.get("mese_saldo_notificato", None)
                        mese_corrente = f"{datetime.date.today().year}-{datetime.date.today().month:02d}"
                        if mese_notificato != mese_corrente:
                            ultimo_notificato = None
                        if saldo_mese >= 0:
                            if ultimo_notificato is not None:
                                try:
                                    with open(SCHEDULE_FILE, "r", encoding="utf-8") as _f:
                                        _tasks = json.load(_f)
                                    for _ti in _tasks:
                                        if _ti.get("nome") == tk_task.get("nome") and _ti.get("tipo") == tk_task.get("tipo"):
                                            _ti["ultimo_saldo_notificato"] = None
                                            _ti["mese_saldo_notificato"] = None
                                            break
                                    with open(SCHEDULE_FILE, "w", encoding="utf-8") as _f:
                                        json.dump(_tasks, _f, indent=2, ensure_ascii=False)
                                except Exception as _e:
                                    ora = datetime.datetime.now().strftime("%H:%M:%S")
                                    print(f"[{ora}] [SCHEDULER] Errore reset saldo notificato: {_e}")
                            ie = False
                        elif saldo_mese != ultimo_notificato:
                            corpo_mail = self._genera_testo_allerta_saldo(saldo_mese)
                            tk_task["ultimo_saldo_notificato"] = saldo_mese
                            tk_task["mese_saldo_notificato"] = mese_corrente
                            try:
                                with open(SCHEDULE_FILE, "r", encoding="utf-8") as _f:
                                    _tasks = json.load(_f)
                                for _ti in _tasks:
                                    if _ti.get("nome") == tk_task.get("nome") and _ti.get("tipo") == tk_task.get("tipo"):
                                        _ti["ultimo_saldo_notificato"] = saldo_mese
                                        _ti["mese_saldo_notificato"] = mese_corrente
                                        break
                                with open(SCHEDULE_FILE, "w", encoding="utf-8") as _f:
                                    json.dump(_tasks, _f, indent=2, ensure_ascii=False)
                            except Exception as _e:
                                ora = datetime.datetime.now().strftime("%H:%M:%S")
                                print(f"[{ora}] [SCHEDULER] Errore salvataggio saldo notificato: {_e}")
                        else:
                            ie = False
                    elif t == "sforamento_budget":
                        oggi_dt = datetime.date.today()
                        sforamenti_mese, sforamenti_anno = self._calcola_sforamenti_budget()
                        mese_corrente = f"{oggi_dt.year}-{oggi_dt.month:02d}"
                        anno_corrente = oggi_dt.year
                        stato_mese = {cat: tot for cat, tot, _b in sforamenti_mese}
                        stato_anno = {cat: tot for cat, tot, _b in sforamenti_anno}
                        notif_mese = tk_task.get("budget_notificati_mese", {}) \
                            if tk_task.get("mese_budget_notificato") == mese_corrente else {}
                        notif_anno = tk_task.get("budget_notificati_anno", {}) \
                            if tk_task.get("anno_budget_notificato") == anno_corrente else {}
                        if stato_mese != notif_mese or stato_anno != notif_anno:
                            if stato_mese or stato_anno:
                                corpo_mail = self._genera_testo_sforamento_budget(sforamenti_mese, sforamenti_anno)
                            else:
                                ie = False
                            try:
                                with open(SCHEDULE_FILE, "r", encoding="utf-8") as _f:
                                    _tasks = json.load(_f)
                                for _ti in _tasks:
                                    if _ti.get("nome") == tk_task.get("nome") and _ti.get("tipo") == tk_task.get("tipo"):
                                        _ti["budget_notificati_mese"] = stato_mese
                                        _ti["mese_budget_notificato"] = mese_corrente
                                        _ti["budget_notificati_anno"] = stato_anno
                                        _ti["anno_budget_notificato"] = anno_corrente
                                        break
                                with open(SCHEDULE_FILE, "w", encoding="utf-8") as _f:
                                    json.dump(_tasks, _f, indent=2, ensure_ascii=False)
                            except Exception as _e:
                                ora = datetime.datetime.now().strftime("%H:%M:%S")
                                print(f"[{ora}] [SCHEDULER] Errore salvataggio stato budget notificato: {_e}")
                        else:
                            ie = False
                    elif t == "promemoria_libero":
                        nota_testo = tk_task.get('note', 'Promemoria schedulato da OrbitaCasa.')
                        data_oggi = datetime.date.today().strftime('%d/%m/%Y')
                        corpo_mail = (
                            f"\n"
                            f"PROMEMORIA DIRETTO     \n"
                            f"{'─' * 31}\n"
                            f"📌 *NOTA:*\n"
                            f"{nota_testo}\n\n"
                            f"{'┈' * 31}\n"
                            f"📅 Report generato il {data_oggi}"
                        )
                    if ie and corpo_mail and EMAIL_USER and APP_PASSWORD:
                        import threading
                        threading.Thread(
                            target=self._invia_email_scheduler,
                            args=(n, corpo_mail, d),
                            daemon=True
                        ).start()
                        self.after(0, lambda: self.show_toast(f"✉ Email Schedulata Inviata: {n}", duration=4000))
                except Exception as ex:
                    ora = datetime.datetime.now().strftime("%H:%M:%S")
                    print(f"[{ora}] [SCHEDULER] Errore interno durante l'invio di '{n}': {ex}")
            self.after(0, _operazioni_gui)
        if modificato:
            try:
                with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
                    json.dump(tasks, f, indent=2, ensure_ascii=False)
            except Exception as e:
                ora = datetime.datetime.now().strftime("%H:%M:%S")
                print(f"[{ora}] [SCHEDULER] Errore scrittura file: {e}")

# Genera il testo del riepilogo giornaliero/settimanale (spostata da fairshare.py: non c'entrava nulla con FairShare)
def _genera_testo_riepilogo_cronologico(self, frequenza_tipo):
    oggi = datetime.date.today()
    if frequenza_tipo == "giornaliero":
        inizio = oggi
        titolo = f"REGISTRO GIORNALIERO - {oggi.strftime('%d/%m/%Y')}"
    else:
        inizio = oggi - datetime.timedelta(days=7)
        titolo = f"REGISTRO SETTIMANALE\n   {inizio.strftime('%d/%m')} → {oggi.strftime('%d/%m/%Y')}"
    tot_e = tot_u = 0.0
    movimenti = []
    for d, voci in self.spese.items():
        d_date = d.date() if isinstance(d, datetime.datetime) else d
        if not isinstance(d_date, datetime.date):
            continue
        if inizio <= d_date <= oggi:
            for v in voci:
                desc = campo(v, "descrizione", "")
                imp = campo(v, "importo", 0.0)
                tipo = campo(v, "tipo", "")
                cat = campo(v, "categoria", "")
                if tipo == "Entrata":
                    tot_e += imp
                else:
                    tot_u += imp
                movimenti.append((d_date, cat, desc, tipo, imp))
    movimenti.sort(key=lambda x: x[0])
    saldo = tot_e - tot_u
    lines = []
    lines.append(f"📊 {titolo.upper()}")
    lines.append("─" * 24)
    lines.append(f"🟢 ENTRATE: {_fmt_it(tot_e)} €")
    lines.append(f"🔴 USCITE:  {_fmt_it(tot_u)} €")
    emoji_saldo = "💰" if saldo >= 0 else "⚠️"
    lines.append(f"{emoji_saldo} SALDO:   {_fmt_it(saldo)} €")
    lines.append("")
    lines.append("📝 MOVIMENTI RILEVATI")
    lines.append("─" * 24)
    for mov in movimenti:
        data, cat, desc, tipo, importo = mov[0], mov[1], mov[2], mov[3], mov[4]
        desc_str = desc.strip()
        desc_pulita = desc_str[:20] + "..." if len(desc_str) > 20 else desc_str
        segno = "🟢" if tipo.lower() in ["entrata", "e"] else "🔴"
        lines.append(f"{segno} {data}  {_fmt_it(importo)} €")
        lines.append(f"   📂 {cat}")
        lines.append(f"   ✏️ {desc_pulita}")
        lines.append("   " + "┈" * 22)
    return "\n".join(lines)

def _genera_testo_ricorrenti_mancanti(self):
    oggi = datetime.date.today()
    data_oggi = oggi.strftime('%d/%m/%Y')
    mancanti = self._ottieni_categorie_ricorrenti_mancanti()
    lines = []
    lines.append("")
    testo_centrato = "AVVISO SCADENZE MENSILE".center(28)
    lines.append(f"")
    lines.append(f"{testo_centrato}")
    lines.append(f"─" * 31)
    lines.append("")
    lines.append("⚠️ MOVIMENTI MANCANTI RILEVATI")
    lines.append("─" * 31)
    lines.append("")
    lines.append("Facendo un confronto con le tue abitudini dei mesi scorsi,")
    lines.append("risulta che in questo mese non hai ancora registrato:")
    lines.append("")
    if mancanti:
        for cat in mancanti:
            lines.append(f"    📌 {cat}")
        lines.append("")
        lines.append("┈" * 30)
        lines.append("Controlla la tua contabilità su OrbitaCasa se hai")
        lines.append("dimenticato di segnare queste scadenze.")
    else:
        lines.append("🟩 Tutto sotto controllo!")
        lines.append("Hai inserito tutte le categorie ricorrenti abituali.")
    lines.append("")
    lines.append(f"📊 Report generato il {data_oggi}.")
    return "\n".join(lines)

def _genera_testo_scadenze_veicoli(self, soglia_giorni=30):
    oggi = datetime.date.today()
    data_oggi = oggi.strftime('%d/%m/%Y')
    db = self._veicoli_carica()
    veicoli = db.get("veicoli", [])
    CAMPI_SCAD = [
        ("scad_bollo",         "Bollo"),
        ("scad_assicurazione", "Assicurazione"),
        ("scad_revisione",     "Revisione"),
    ]
    scadute = []
    in_scadenza = []
    for v in veicoli:
        nome = v.get("nome", "Veicolo")
        for chiave, etichetta in CAMPI_SCAD:
            data_str = v.get(chiave, "")
            giorni = self._veicoli_giorni_a_scadenza(data_str)
            if giorni is None:
                continue
            if giorni < 0:
                scadute.append((nome, etichetta, data_str, giorni))
            elif giorni <= soglia_giorni:
                in_scadenza.append((nome, etichetta, data_str, giorni))
    scadute.sort(key=lambda x: x[3])
    in_scadenza.sort(key=lambda x: x[3])
    if not scadute and not in_scadenza:
        return ""
    lines = []
    lines.append("")
    testo_centrato = "SCADENZE VEICOLI".center(28)
    lines.append(f"{testo_centrato}")
    lines.append("─" * 31)
    lines.append("")
    if scadute:
        lines.append("🔴 SCADUTE")
        lines.append("─" * 31)
        lines.append("")
        for nome, etichetta, data_str, giorni in scadute:
            lines.append(f"    🚗 {nome} — {etichetta}")
            lines.append(f"       Scaduta da {abs(giorni)} gg ({data_str})")
        lines.append("")
    if in_scadenza:
        lines.append("🟡 IN SCADENZA")
        lines.append("─" * 31)
        lines.append("")
        for nome, etichetta, data_str, giorni in in_scadenza:
            testo_gg = "Scade OGGI" if giorni == 0 else f"tra {giorni} gg"
            lines.append(f"    🚗 {nome} — {etichetta}")
            lines.append(f"       {testo_gg} ({data_str})")
        lines.append("")
    lines.append("┈" * 30)
    lines.append("Controlla la sezione Veicoli su OrbitaCasa per i dettagli")
    lines.append("e per rinnovare le scadenze in tempo.")
    lines.append("")
    lines.append(f"📊 Report generato il {data_oggi}.")
    return "\n".join(lines)

def _genera_testo_estratto_mensile(self):
    oggi = datetime.date.today()
    if oggi.day == 1:
        # Il mese in corso è appena iniziato: mandiamo quello appena concluso.
        primo_del_mese = oggi.replace(day=1)
        ultimo_mese_prec = primo_del_mese - datetime.timedelta(days=1)
        mese = ultimo_mese_prec.month
        anno = ultimo_mese_prec.year
    else:
        mese = oggi.month
        anno = oggi.year
    mesi = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO",
            "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
    nome_mese = mesi[mese - 1]
    tot_e = tot_u = 0.0
    cat_entrate = {}
    cat_uscite = {}
    movimenti = []
    for d, voci in self.spese.items():
        d_date = d.date() if isinstance(d, datetime.datetime) else d
        if not isinstance(d_date, datetime.date):
            continue
        if d_date.year == anno and d_date.month == mese:
            for v in voci:
                desc = campo(v, "descrizione", "")
                imp = campo(v, "importo", 0.0)
                tipo = campo(v, "tipo", "")
                cat = campo(v, "categoria", "")
                if tipo == "Entrata":
                    tot_e += imp
                    cat_entrate[cat] = cat_entrate.get(cat, {"voci": 0, "totale": 0.0})
                    cat_entrate[cat]["voci"] += 1
                    cat_entrate[cat]["totale"] += imp
                else:
                    tot_u += imp
                    cat_uscite[cat] = cat_uscite.get(cat, {"voci": 0, "totale": 0.0})
                    cat_uscite[cat]["voci"] += 1
                    cat_uscite[cat]["totale"] += imp
                movimenti.append((d_date, cat, desc, tipo, imp))
    movimenti.sort(key=lambda x: x[0])
    saldo = tot_e - tot_u
    lines = []
    lines.append("")
    lines.append(f"📊 RIEPILOGO MENSILE - {nome_mese.upper()} {anno}")
    lines.append("─" * 24)
    lines.append("")
    lines.append(f"🟢 ENTRATE: {_fmt_it(tot_e)} €")
    lines.append(f"🔴 USCITE:  {_fmt_it(tot_u)} €")
    emoji_saldo = "💰" if saldo >= 0 else "⚠️"
    lines.append(f"{emoji_saldo} SALDO: {_fmt_it(saldo)} €")
    lines.append("")
    if cat_entrate:
        lines.append("💰 ENTRATE PER CATEGORIA")
        lines.append("─" * 24)
        lines.append("")
        for cat, data in sorted(cat_entrate.items(), key=lambda x: x[1]["totale"], reverse=True):
            p = (data["totale"] / tot_e * 100) if tot_e > 0 else 0.0
            quadratini = max(1, min(10, int(round(p / 10)))) if p > 0 else 0
            barra = "■" * quadratini + "□" * (10 - quadratini)
            lines.append(f"🟩  {cat[:16]} ({p:.1f}%)")
            lines.append(f"   Ricevuto: {_fmt_it(data['totale'])} €  Voci: {data['voci']}")
            lines.append(f"   [{barra}]")
            lines.append("┈" * 22)
        lines.append("")
    if cat_uscite:
        lines.append("💸 USCITE PER CATEGORIA")
        lines.append("─" * 24)
        lines.append("")
        for cat, data in sorted(cat_uscite.items(), key=lambda x: x[1]["totale"], reverse=True):
            p = (data["totale"] / tot_u * 100) if tot_u > 0 else 0.0
            quadratini = max(1, min(10, int(round(p / 10)))) if p > 0 else 0
            barra = "■" * quadratini + "□" * (10 - quadratini)
            lines.append(f"🟥  {cat[:16]} ({p:.1f}%)")
            lines.append(f"   Speso:    {_fmt_it(data['totale'])} €  Voci: {data['voci']}")
            lines.append(f"   [{barra}]")
            lines.append("┈" * 22)
        lines.append("")
    lines.append("📜 REGISTRO CRONOLOGICO COMPATTO")
    lines.append("─" * 24)
    lines.append("")
    for m in movimenti:
        data_str = m[0].strftime('%d/%m/%Y')
        categoria = m[1]
        desc_str = m[2].strip()
        desc_pulita = desc_str[:20] + "..." if len(desc_str) > 20 else desc_str
        segno_emoji = "🟩 +" if m[3] == "Entrata" else "🟥 -"
        lines.append(f"{segno_emoji} {_fmt_it(m[4])} €  {data_str}")
        lines.append(f"   📂 {categoria} -> {desc_pulita}")
        lines.append("   " + "┈" * 28)
    lines.append("")
    lines.append(f"🔢 Totale movimenti: {len(movimenti)}")
    lines.append("")
    lines.append(f"📅 Report generato il {oggi.strftime('%d/%m/%Y')}")
    return "\n".join(lines)

def _genera_testo_estratto_trasferimenti(self):
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    oggi = datetime.date.today()
    if oggi.day == 1:
        # Il mese in corso è appena iniziato: mandiamo quello appena concluso.
        primo_del_mese = oggi.replace(day=1)
        ultimo_mese_prec = primo_del_mese - datetime.timedelta(days=1)
        mese, anno = ultimo_mese_prec.month, ultimo_mese_prec.year
    else:
        mese, anno = oggi.month, oggi.year
    mesi = ["GENNAIO", "FEBBRAIO", "MARZO", "APRILE", "MAGGIO", "GIUGNO",
            "LUGLIO", "AGOSTO", "SETTEMBRE", "OTTOBRE", "NOVEMBRE", "DICEMBRE"]
    nome_mese = mesi[mese - 1]
    try:
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as f:
            db = json.load(f)
    except Exception:
        db = {"conti": [], "trasferimenti": []}
    nome_da_id = {c["id"]: c.get("nome", "?") for c in db.get("conti", [])}
    movimenti = []
    saldo_conto = {}
    for t in db.get("trasferimenti", []):
        if e_trasferimento_virtuale(t):
            continue
        try:
            d = datetime.datetime.strptime(t.get("data", ""), "%d-%m-%Y").date()
        except Exception:
            continue
        if d.year != anno or d.month != mese:
            continue
        imp = round(float(t.get("importo", 0)), 2)
        da_n = nome_da_id.get(t.get("da", ""), "?")
        a_n  = nome_da_id.get(t.get("a", ""), "?")
        movimenti.append((d, da_n, a_n, imp, t.get("note", ""), bool(t.get("id_ricorrenza"))))
        saldo_conto[da_n] = saldo_conto.get(da_n, 0.0) - imp
        saldo_conto[a_n]  = saldo_conto.get(a_n, 0.0) + imp
    movimenti.sort(key=lambda x: x[0])
    lines = []
    lines.append("")
    lines.append(f"🔄 TRASFERIMENTI CONTI {nome_mese} {anno}")
    lines.append("─" * 31)
    lines.append("")
    if not movimenti:
        lines.append("Nessun trasferimento tra conti nel mese.")
    else:
        totale = sum(m[3] for m in movimenti)
        lines.append(f"🔢 Movimenti: {len(movimenti)}")
        lines.append(f"💶 Totale spostato: {_fmt_it(totale)} €")
        lines.append("")
        lines.append("📜 DETTAGLIO")
        lines.append("─" * 31)
        lines.append("")
        for d, da_n, a_n, imp, note, ric in movimenti:
            ric_s = " 🔁" if ric else ""
            lines.append(f"↪ {_fmt_it(imp)} €  {d.strftime('%d/%m/%Y')}{ric_s}")
            lines.append(f"   {da_n} → {a_n}")
            if note:
                lines.append(f"   📝 {note}")
            lines.append("   " + "┈" * 28)
        lines.append("")
        lines.append("📊 NETTO TRASFERIMENTI (nel periodo)")
        lines.append("─" * 31)
        for nome, netto in sorted(saldo_conto.items(), key=lambda x: -x[1]):
            segno = "🟢" if netto >= 0 else "🔴"
            lines.append(f"{segno} {nome}: {_fmt_it(netto)} €")
    lines.append("")
    lines.append(f"📅 Report generato il {oggi.strftime('%d/%m/%Y')}")
    return "\n".join(lines)

def _genera_testo_estratto_annuale(self):
    oggi = datetime.date.today()
    if oggi.month == 1 and oggi.day == 1:
        anno = oggi.year - 1
    else:
        anno = oggi.year
    tot_e = tot_u = 0.0
    cat_entrate = {}
    cat_uscite = {}
    for d, voci in self.spese.items():
        d_date = d.date() if isinstance(d, datetime.datetime) else d
        if not isinstance(d_date, datetime.date):
            continue
        if d_date.year == anno:
            for v in voci:
                imp = campo(v, "importo", 0.0)
                tipo = campo(v, "tipo", "")
                cat = campo(v, "categoria", "")
                if tipo == "Entrata":
                    tot_e += imp
                    cat_entrate[cat] = cat_entrate.get(cat, {"voci": 0, "totale": 0.0})
                    cat_entrate[cat]["voci"] += 1
                    cat_entrate[cat]["totale"] += imp
                else:
                    tot_u += imp
                    cat_uscite[cat] = cat_uscite.get(cat, {"voci": 0, "totale": 0.0})
                    cat_uscite[cat]["voci"] += 1
                    cat_uscite[cat]["totale"] += imp
    saldo = tot_e - tot_u
    lines = []
    lines.append("")
    lines.append(f"📊 *RIEPILOGO ANNUALE {anno}*")
    lines.append("─" * 31)
    lines.append("")
    lines.append(f"🟢 TOTALE ENTRATE ANNO: {_fmt_it(tot_e)} €")
    lines.append(f"🔴 TOTALE USCITE ANNO:  {_fmt_it(tot_u)} €")
    emoji_saldo = "💰" if saldo >= 0 else "⚠️"
    lines.append(f"{emoji_saldo} SALDO PROGRESSIVO:   {_fmt_it(saldo)} €")
    lines.append("")
    if cat_entrate:
        lines.append("💰 ENTRATE PER CATEGORIA")
        lines.append("─" * 31)
        lines.append("")
        for cat, data in sorted(cat_entrate.items(), key=lambda x: x[1]['totale'], reverse=True):
            p = (data["totale"] / tot_e * 100) if tot_e > 0 else 0.0
            quadratini = max(1, min(10, int(round(p / 10)))) if p > 0 else 0
            barra = "■" * quadratini + "□" * (10 - quadratini)
            lines.append(f"🟩 {cat} ({p:4.1f}%)")
            lines.append(f"   Ricevuto: {_fmt_it(data['totale'])} €  Voci: {data['voci']}")
            lines.append(f"   `[{barra}]`")
            lines.append("┈" * 28)
        lines.append("")
    if cat_uscite:
        lines.append("💸 USCITE PER CATEGORIA")
        lines.append("─" * 31)
        lines.append("")
        for cat, data in sorted(cat_uscite.items(), key=lambda x: x[1]['totale'], reverse=True):
            p = (data["totale"] / tot_u * 100) if tot_u > 0 else 0.0
            quadratini = max(1, min(10, int(round(p / 10)))) if p > 0 else 0
            barra = "■" * quadratini + "□" * (10 - quadratini)
            lines.append(f"🟥 {cat} ({p:4.1f}%)")
            lines.append(f"   Speso: {_fmt_it(data['totale'])} €  Voci: {data['voci']}")
            lines.append(f"   `[{barra}]`")
            lines.append("┈" * 28)
        lines.append("")
    lines.append("")
    lines.append(f"📅 Report generato il {oggi.strftime('%d/%m/%Y')}")
    return "\n".join(lines)

def _calcola_saldo_mese_corrente(self):
    oggi = datetime.date.today()
    tot_e = tot_u = 0.0
    for d, voci in self.spese.items():
        d_date = d.date() if isinstance(d, datetime.datetime) else d
        if not isinstance(d_date, datetime.date):
            continue
        if d_date.year == oggi.year and d_date.month == oggi.month:
            for v in voci:
                imp = campo(v, "importo", 0.0)
                tipo = campo(v, "tipo", "")
                if tipo == "Entrata":
                    tot_e += imp
                else:
                    tot_u += imp
    return round(tot_e - tot_u, 2)

def _calcola_sforamenti_budget(self):
    oggi = datetime.date.today()
    tot_mese, tot_anno = {}, {}
    for d, voci in self.spese.items():
        d_date = d.date() if isinstance(d, datetime.datetime) else d
        if not isinstance(d_date, datetime.date):
            continue
        if d_date.year != oggi.year:
            continue
        for v in voci:
            if campo(v, "tipo", "") != "Uscita":
                continue
            cat = campo(v, "categoria", "")
            imp = campo(v, "importo", 0.0)
            tot_anno[cat] = tot_anno.get(cat, 0.0) + imp
            if d_date.month == oggi.month:
                tot_mese[cat] = tot_mese.get(cat, 0.0) + imp
    sforamenti_mese = [
        (cat, round(tot_mese.get(cat, 0.0), 2), round(budget, 2))
        for cat, budget in getattr(self, "budget_categorie", {}).items()
        if budget and budget > 0 and tot_mese.get(cat, 0.0) > budget
    ]
    sforamenti_anno = [
        (cat, round(tot_anno.get(cat, 0.0), 2), round(budget, 2))
        for cat, budget in getattr(self, "budget_annuale_categorie", {}).items()
        if budget and budget > 0 and tot_anno.get(cat, 0.0) > budget
    ]
    sforamenti_mese.sort(key=lambda x: x[1] - x[2], reverse=True)
    sforamenti_anno.sort(key=lambda x: x[1] - x[2], reverse=True)
    return sforamenti_mese, sforamenti_anno

def _genera_testo_sforamento_budget(self, sforamenti_mese, sforamenti_anno):
    oggi = datetime.date.today()
    lines = [
        "",
        "⚠️ BUDGET SUPERATO",
        f"📅 {oggi.strftime('%d/%m/%Y')}",
        "─" * 24,
    ]
    if sforamenti_mese:
        lines.append("")
        lines.append("📅 BUDGET MENSILE")
        lines.append("─" * 24)
        for cat, tot, budget in sforamenti_mese:
            lines.append("")
            lines.append(f"📂 {cat}")
            lines.append(f"   Speso:   {_fmt_it(tot)} €")
            lines.append(f"   Budget:  {_fmt_it(budget)} €")
            lines.append(f"   Sforato: {_fmt_it(tot - budget)} €")
            lines.append("┈" * 24)
    if sforamenti_anno:
        lines.append("")
        lines.append("📆 BUDGET ANNUALE")
        lines.append("─" * 24)
        for cat, tot, budget in sforamenti_anno:
            lines.append("")
            lines.append(f"📂 {cat}")
            lines.append(f"   Speso:   {_fmt_it(tot)} €")
            lines.append(f"   Budget:  {_fmt_it(budget)} €")
            lines.append(f"   Sforato: {_fmt_it(tot - budget)} €")
            lines.append("┈" * 24)
    lines.append("")
    lines.append("─" * 24)
    lines.append(f"📅 Rilevato il {oggi.strftime('%d/%m/%Y')}")
    return "\n".join(lines)

def _genera_testo_allerta_saldo(self, saldo):
    oggi = datetime.date.today()
    mesi = ["Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno",
            "Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"]
    nome_mese = mesi[oggi.month - 1]
    lines = [
        "",
        f"⚠️  ALLERTA SALDO NEGATIVO — {nome_mese.upper()} {oggi.year}",
        "─" * 31,
        "",
        f"Il saldo del mese corrente è in rosso:",
        "",
        f"  💸 Saldo:  {_fmt_it(saldo)} €",
        "",
        "─" * 31,
        f"📅 Rilevato il {oggi.strftime('%d/%m/%Y')}",
    ]
    return "\n".join(lines)

def _invia_email_scheduler(self, nome, corpo, destinatario):
    import __main__ as _app
    EMAIL_USER = _app.EMAIL_USER
    APP_PASSWORD = _app.APP_PASSWORD
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"⏰ OrbitaCasa — {nome}"
        msg["From"] = EMAIL_USER
        msg["To"] = destinatario
        msg.attach(MIMEText(corpo, "plain", "utf-8"))
        html_corpo = f"<html><body><pre style='font-family: monospace; font-size: 12px; line-height: 14px;'>{corpo}</pre></body></html>"
        msg.attach(MIMEText(html_corpo, "html", "utf-8"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, APP_PASSWORD)
            server.sendmail(EMAIL_USER, destinatario, msg.as_string())
        ora = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{ora}] [SCHEDULER] Email inviata con successo: {nome} → {destinatario}")
        return True, None
    except Exception as e:
        ora = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{ora}] [SCHEDULER] Errore critico invio email '{nome}': {e}")
        return False, str(e)

