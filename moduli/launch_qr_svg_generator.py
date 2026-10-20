#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io
import webbrowser
from urllib.parse import quote

import tkinter as tk
from tkinter import ttk

import segno
from PIL import Image, ImageTk

# Generatore QR Code / Link Promemoria Google Calendar
def launch_qr_svg_generator(self, initial_category="", initial_amount="", initial_date="", initial_description="", initial_type=""):
    from datetime import datetime, timedelta
    categories_list = getattr(self, 'categorie', [])
    CATEGORIES = ["Promemoria"] + categories_list
    TYPE_OPTIONS = ["Promemoria", "uscita", "entrata"]
    TYPE_COLORS = {"Promemoria": "#3b82f6", "uscita": "#e5484d", "entrata": "#30a46c"}
    ACCENT = "#3b82f6"
    COLOR_ERR = "#e5484d"
    COLOR_OK = "#30a46c"
    COLOR_INFO = "gray"
    QR_PX = 250
    FONT = "Segoe UI"
    def create_google_calendar_url(category, description, amount, date_obj, transaction_type):
        description = description.strip()
        display_category = category if category else ""
        event_date = date_obj.date() if isinstance(date_obj, datetime) else date_obj
        start_date_fmt = event_date.strftime("%Y%m%d")
        end_date_fmt = (event_date + timedelta(days=1)).strftime("%Y%m%d")
        title = f"PROMEMORIA: {display_category}"
        details = (f"Descrizione: {description}\n"
                   f"Importo: {amount} €\n"
                   f"Categoria: {display_category}\n"
                   f"Tipo: {transaction_type.upper()}")
        encoded_title = quote(title)
        encoded_details = quote(details)
        base_url = "https://www.google.com/calendar/event?action=TEMPLATE"
        dates_part = f"&dates={start_date_fmt}/{end_date_fmt}"
        title_part = f"&text={encoded_title}"
        details_part = f"&details={encoded_details}"
        return f"{base_url}{dates_part}{title_part}{details_part}"
    def show_unified_qr_generator(self):
        qr_popup = tk.Toplevel(self, bg=self.COLOR_TOPLEVEL)
        qr_popup.title("Promemoria Google Calendar")
        qr_popup.transient(self)
        qr_popup.withdraw()
        W, H = 800, 640
        qr_popup.resizable(False, False)
        qr_popup.geometry(f'{W}x{H}')
        qr_popup.minsize(width=W, height=H)
        qr_popup.update_idletasks()
        screen_width = qr_popup.winfo_screenwidth()
        screen_height = qr_popup.winfo_screenheight()
        x = (screen_width // 2) - (W // 2)
        y = (screen_height // 2) - (H // 2)
        qr_popup.geometry(f'{W}x{H}+{x}+{y}')
        qr_popup.deiconify()
        current_url_var = tk.StringVar(value="")
        update_job = {"id": None}
        def close_and_cleanup():
            if update_job["id"]:
                try:
                    qr_popup.after_cancel(update_job["id"])
                except Exception:
                    pass
            try:
                self.popup_calendario.destroy()
            except Exception:
                pass
            self.popup_calendario = None
            qr_popup.destroy()
        def open_agenda_url():
            webbrowser.open("https://calendar.google.com/calendar/u/0/r/agenda")
        qr_popup.protocol("WM_DELETE_WINDOW", close_and_cleanup)
        qr_popup.bind('<Escape>', lambda e: close_and_cleanup())
        def make_button(parent, text, icon_key, command):
            icon = self.icone_gui.get(icon_key) if icon_key else None
            btn = ttk.Label(
                parent,
                image=icon,
                text=" " + text if icon else text,
                compound="left",
                cursor="hand2",
                background=self.COLOR_WIDGET_BG,
                font=(FONT, 10, "bold"),
                padding=(14, 8),
                anchor="center"
            )
            btn.image = icon
            btn.bind("<Button-1>", lambda e: command())
            return btn
        def field_label(parent, text):
            return ttk.Label(parent, text=text, font=(FONT, 9, "bold"))
        qr_cat_var = tk.StringVar(qr_popup, value=initial_category or CATEGORIES[0])
        qr_type_var = tk.StringVar(qr_popup, value=initial_type if initial_type in TYPE_OPTIONS else TYPE_OPTIONS[0])
        qr_amount_var = tk.StringVar(qr_popup, value=initial_amount)
        date_to_use = initial_date if initial_date else datetime.now().strftime("%d-%m-%Y")
        qr_date_var = tk.StringVar(qr_popup, value=date_to_use)
        root = ttk.Frame(qr_popup, padding=(24, 18, 24, 16))
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Promemoria Google Calendar", font=(FONT, 16, "bold")).pack(anchor="w")
        ttk.Label(root, text="Crea l'evento e condividilo con un QR code o un link.", foreground=COLOR_INFO).pack(anchor="w", pady=(0, 14))
        footer = ttk.Frame(root)
        footer.pack(side="bottom", fill="x")
        ttk.Separator(root, orient='horizontal').pack(side="bottom", fill="x", pady=(14, 10))
        body = ttk.Frame(root)
        body.pack(fill="both", expand=True)
        left = ttk.Frame(body)
        left.pack(side="left", fill="both", expand=True)
        right = ttk.Frame(body)
        right.pack(side="right", fill="y", padx=(26, 0))
        left.grid_columnconfigure(0, weight=1, uniform="col")
        left.grid_columnconfigure(1, weight=1, uniform="col")
        left.grid_rowconfigure(7, weight=1)
        field_label(left, "Categoria").grid(row=0, column=0, columnspan=2, sticky="w")
        cat_combobox = ttk.Combobox(left, textvariable=qr_cat_var, values=CATEGORIES, state="readonly", style='Border.TCombobox')
        cat_combobox.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(3, 12))
        field_label(left, "Tipo").grid(row=2, column=0, columnspan=2, sticky="w")
        seg_frame = tk.Frame(left, bg=self.COLOR_WIDGET_BG, highlightthickness=1, highlightbackground=self.COLOR_HIGHLIGHT)
        seg_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(3, 12))
        seg_buttons = {}
        for i, opt in enumerate(TYPE_OPTIONS):
            seg_frame.grid_columnconfigure(i, weight=1, uniform="seg")
            seg_btn = tk.Label(seg_frame, text=opt.capitalize(), cursor="hand2", font=(FONT, 10, "bold"), pady=7)
            seg_btn.grid(row=0, column=i, sticky="ew")
            seg_btn.bind("<Button-1>", lambda e, o=opt: qr_type_var.set(o))
            seg_buttons[opt] = seg_btn
        def paint_segments(*_):
            for opt, btn in seg_buttons.items():
                if opt == qr_type_var.get():
                    btn.config(bg=TYPE_COLORS[opt], fg="white")
                else:
                    btn.config(bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR)
        field_label(left, "Data").grid(row=4, column=0, sticky="w")
        field_label(left, "Importo").grid(row=4, column=1, sticky="w", padx=(8, 0))
        date_frame = ttk.Frame(left)
        date_frame.grid(row=5, column=0, sticky="ew", pady=(3, 12))
        date_entry_input = ttk.Entry(date_frame, textvariable=qr_date_var)
        date_entry_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.calendar_label_qr = ttk.Label(
            date_frame,
            image=self.icone_gui.get("calendario"),
            cursor="hand2",
            background=self.COLOR_WIDGET_BG
        )
        self.calendar_label_qr.image = self.icone_gui.get("calendario")
        self.calendar_label_qr.pack(side=tk.RIGHT, padx=(6, 0))
        self.calendar_label_qr.bind(
            "<Button-1>",
            lambda e: self.mostra_calendario_popup(date_entry_input, qr_date_var)
        )
        def validate_importo(P):
            if P == "": return True
            try:
                float(P.replace(',', '.'))
                return True if (P.count('.') + P.count(',')) <= 1 else False
            except ValueError:
                return False
        vcmd = left.register(validate_importo)
        amount_frame = ttk.Frame(left)
        amount_frame.grid(row=5, column=1, sticky="ew", pady=(3, 12), padx=(8, 0))
        qr_amount_entry = ttk.Entry(
            amount_frame,
            textvariable=qr_amount_var,
            validate='key',
            validatecommand=(vcmd, '%P')
        )
        qr_amount_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(amount_frame, text="€", font=(FONT, 10, "bold")).pack(side=tk.RIGHT, padx=(6, 0))
        field_label(left, "Descrizione (Note)").grid(row=6, column=0, columnspan=2, sticky="w")
        desc_text_widget = tk.Text(
            left,
            height=5,
            width=30,
            wrap="word",
            bg=self.COLOR_WIDGET_BG,
            fg=self.TEXT_COLOR,
            insertbackground=self.TEXT_COLOR,
            font=(FONT, 10),
            relief="flat",
            padx=8,
            pady=6,
            highlightthickness=1,
            highlightbackground=self.COLOR_HIGHLIGHT,
            highlightcolor=ACCENT
        )
        desc_text_widget.grid(row=7, column=0, columnspan=2, sticky="nsew", pady=(3, 0))
        if initial_description:
            desc_text_widget.insert(tk.END, initial_description)
        qr_tile = tk.Frame(right, bg="white", width=QR_PX + 30, height=QR_PX + 30, highlightthickness=1, highlightbackground=self.COLOR_HIGHLIGHT)
        qr_tile.pack()
        qr_tile.pack_propagate(False)
        qr_label = tk.Label(qr_tile, bg="white", fg="#888888", font=(FONT, 10), justify="center", text="Il QR code\ncomparirà qui")
        qr_label.place(relx=0.5, rely=0.5, anchor="center")
        ttk.Label(right, text="Inquadra con la fotocamera", foreground=COLOR_INFO).pack(pady=(8, 10))
        url_entry = ttk.Entry(right, textvariable=current_url_var, state="readonly")
        url_entry.pack(fill="x", pady=(0, 8))
        def copy_link():
            url = current_url_var.get()
            if not url: return
            self.clipboard_clear()
            self.clipboard_append(url)
            set_status("Link copiato negli appunti", COLOR_OK)
        def open_link_in_browser():
            url = current_url_var.get()
            if not url: return
            webbrowser.open(url)
            set_status("Link aperto nel browser", ACCENT)
        make_button(right, "Copia link", "link", copy_link).pack(fill="x", pady=(0, 6))
        make_button(right, "Apri nel browser", "calendario", open_link_in_browser).pack(fill="x")
        status_label = ttk.Label(footer, text="", foreground=COLOR_INFO)
        status_label.pack(side="left")
        def set_status(text, color=COLOR_INFO):
            status_label.config(text=text, foreground=color)
        def show_qr(url):
            q = segno.make(url)
            w, _ = q.symbol_size(scale=1, border=2)
            scale = max(1, QR_PX // w)
            out = io.BytesIO()
            q.save(out, kind='png', scale=scale, border=2, dark="black", light="white")
            out.seek(0)
            img_qr = ImageTk.PhotoImage(Image.open(out))
            qr_label.config(image=img_qr, text="")
            qr_label.image = img_qr
        def clear_qr():
            qr_label.config(image="", text="Il QR code\ncomparirà qui")
            qr_label.image = None
            current_url_var.set("")
        def update_output():
            update_job["id"] = None
            description = desc_text_widget.get("1.0", tk.END).strip()
            try:
                date_obj = datetime.strptime(qr_date_var.get(), "%d-%m-%Y")
            except ValueError:
                clear_qr()
                set_status("Data non valida (formato gg-mm-aaaa)", COLOR_ERR)
                return
            url = create_google_calendar_url(qr_cat_var.get(), description, qr_amount_var.get().replace(',', '.'), date_obj, qr_type_var.get())
            try:
                show_qr(url)
            except Exception as e:
                clear_qr()
                set_status(f"Errore generazione QR: {e}", COLOR_ERR)
                return
            current_url_var.set(url)
            set_status("QR aggiornato", COLOR_INFO)
        def schedule_update(*_):
            if update_job["id"]:
                qr_popup.after_cancel(update_job["id"])
            update_job["id"] = qr_popup.after(250, update_output)
        def reset_fields():
            qr_cat_var.set(CATEGORIES[0])
            qr_type_var.set(TYPE_OPTIONS[0])
            qr_amount_var.set("")
            qr_date_var.set(datetime.now().strftime("%d-%m-%Y"))
            desc_text_widget.delete('1.0', tk.END)
            set_status("Campi azzerati", COLOR_INFO)
        make_button(footer, "Chiudi", "chiudi", close_and_cleanup).pack(side="right", padx=(8, 0))
        make_button(footer, "Agenda Calendar", "calendario", open_agenda_url).pack(side="right", padx=(8, 0))
        make_button(footer, "Reset", "reset", reset_fields).pack(side="right", padx=(8, 0))
        for var in (qr_cat_var, qr_type_var, qr_amount_var, qr_date_var):
            var.trace_add("write", schedule_update)
        qr_type_var.trace_add("write", paint_segments)
        desc_text_widget.bind("<KeyRelease>", schedule_update)
        paint_segments()
        update_output()
    show_unified_qr_generator(self)
