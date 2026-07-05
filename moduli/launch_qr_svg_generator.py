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
        qr_popup = tk.Toplevel(self)
        qr_popup.title("Generatore Promemoria QRCODE Google Calendar")
        qr_popup.transient(self)
        qr_popup.withdraw()
        W, H = 550, 500
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
        def close_and_cleanup():
            try:
                self.popup_calendario.destroy() 
            except:
                pass
            self.popup_calendario = None
            qr_popup.destroy()
        def open_agenda_url():
            webbrowser.open("https://calendar.google.com/calendar/u/0/r/agenda")
        qr_popup.protocol("WM_DELETE_WINDOW", close_and_cleanup)
        qr_popup.bind('<Escape>', lambda e: close_and_cleanup())
        main_frame = ttk.Frame(qr_popup, padding="15")
        main_frame.pack(fill="both", expand=True)
        qr_cat_var = tk.StringVar(qr_popup, value=initial_category or CATEGORIES[0]) 
        qr_type_var = tk.StringVar(qr_popup, value=initial_type if initial_type in TYPE_OPTIONS else TYPE_OPTIONS[0])
        qr_amount_var = tk.StringVar(qr_popup, value=initial_amount) 
        
        desc_text_widget = tk.Text(
            main_frame, 
            height=3, 
            width=30, 
            wrap="word",
            bg=self.COLOR_WIDGET_BG,
            fg=self.TEXT_COLOR,
            insertbackground=self.TEXT_COLOR,
            font=("Arial", 10),
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.COLOR_HIGHLIGHT
        )
        if initial_description:
            desc_text_widget.insert(tk.END, initial_description)
        date_to_use = initial_date if initial_date else datetime.now().strftime("%d-%m-%Y")
        qr_date_var = tk.StringVar(main_frame, value=date_to_use)
        date_entry_widget_frame = ttk.Frame(main_frame) 
        date_entry_input = ttk.Entry(date_entry_widget_frame, textvariable=qr_date_var, width=24)
        date_entry_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.calendar_label_qr = ttk.Label(
            date_entry_widget_frame, 
            image=self.icone_gui.get("calendario"), 
            cursor="hand2", 
            background=self.COLOR_WIDGET_BG
        )
        self.calendar_label_qr.image = self.icone_gui.get("calendario")
        self.calendar_label_qr.pack(side=tk.RIGHT, padx=(4, 2))
        self.calendar_label_qr.bind(
            "<Button-1>", 
            lambda e: self.mostra_calendario_popup(date_entry_input, qr_date_var)
        )
        def validate_importo(P):
            if P == "": return True
            try:
                float(P)
                return True if P.count('.') <= 1 else False
            except ValueError:
                return False
        vcmd = main_frame.register(validate_importo)
        qr_amount_entry = ttk.Entry(
            main_frame, 
            textvariable=qr_amount_var, 
            width=30,
            validate='key',
            validatecommand=(vcmd, '%P')
        )
        cat_combobox = ttk.Combobox(main_frame, textvariable=qr_cat_var, values=CATEGORIES, width=30, style='Border.TCombobox', state="readonly")
        def reset_fields():
            qr_cat_var.set(CATEGORIES[0])
            qr_type_var.set(TYPE_OPTIONS[0])
            qr_amount_var.set("")
            qr_date_var.set(datetime.now().strftime("%d-%m-%Y"))
            desc_text_widget.delete('1.0', tk.END)
            url_display_label.grid_remove()
            url_text.grid_remove()
            browser_button.grid_remove()
            link_button.grid_remove()
            browser_message.grid_remove()
            browser_message.config(text="")
            generate_button.config(text="Genera QR Code/Link")
            current_url_var.set("")
        def show_qr_popup_window():
            url = current_url_var.get()
            if not url: return
            qr_view = tk.Toplevel(qr_popup)
            qr_view.title("QR Code Promemoria")
            qr_view.configure(bg=self.COLOR_WIDGET_BG)
            vw, vh = 450, 500 
            vx = qr_popup.winfo_rootx() + (qr_popup.winfo_width() // 2) - (vw // 2)
            vy = qr_popup.winfo_rooty() + (qr_popup.winfo_height() // 2) - (vh // 2)
            qr_view.geometry(f"{vw}x{vh}+{vx}+{vy}")
            qr_view.resizable(False, False)
            qr_view.bind("<Escape>", lambda e: qr_view.destroy())
            try:
                q = segno.make(url)
                out = io.BytesIO()
                is_dark = True if self.COLOR_BACKGROUND != "#FFFFFF" else False
                color_dark = "white" if is_dark else "black"
                q.save(out, kind='png', scale=5, dark=color_dark, light=self.COLOR_WIDGET_BG)
                out.seek(0)
                img_qr = ImageTk.PhotoImage(Image.open(out))
                
                titolo_testo = f"Promemoria: {qr_cat_var.get()}" if qr_cat_var.get() else "Promemoria Calendar"
                
                tk.Label(qr_view, text=titolo_testo, font=("Arial", 13, "bold"), 
                         bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR).pack(pady=(15, 0))
                
                tk.Label(qr_view, text=f"Data: {qr_date_var.get()}", font=("Arial", 10), 
                         bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR).pack(pady=(2, 5))
                
                lbl_img = tk.Label(qr_view, image=img_qr, bg=self.COLOR_WIDGET_BG, bd=0)
                lbl_img.image = img_qr
                lbl_img.pack(pady=10)
                
                ttk.Label(qr_view, text="Inquadra con la fotocamera", 
                          style="WhiteSmall.TLabel").pack(pady=5)
                self.btn_chiudi_qr_view = ttk.Label(
                    qr_view, 
                    image=self.icone_gui.get("chiudi"), 
                    text=" Chiudi", 
                    compound="left", 
                    cursor="hand2", 
                    background=self.COLOR_WIDGET_BG,
                    font=("Arial", 10, "bold")
                )
                self.btn_chiudi_qr_view.image = self.icone_gui.get("chiudi")
                self.btn_chiudi_qr_view.pack(pady=(10, 15))
                self.btn_chiudi_qr_view.bind("<Button-1>", lambda e: qr_view.destroy())
                qr_view.transient(qr_popup)
                qr_view.wait_visibility()
                qr_view.grab_set()
            except Exception as e:
                print(f"Errore: {e}")
                if 'browser_message' in locals() or 'browser_message' in globals():
                    browser_message.config(text=f"Errore visualizzazione QR: {e}", foreground="red")
                    browser_message.grid()
        def open_link_in_browser():
            url = current_url_var.get()
            if url:
                webbrowser.open(url)
                browser_message.config(text="Link promemoria aperto nel browser!", foreground="dodgerblue")
        def generate_qr_logic():
            browser_message.config(text="", foreground="blue")
            description = desc_text_widget.get("1.0", tk.END).strip()
            date_str = qr_date_var.get()
            try:
                date_obj = datetime.strptime(date_str, "%d-%m-%Y") 
            except ValueError:
                browser_message.config(text="Errore: Data non valida (formato gg-mm-aaaa).", foreground="red")
                browser_message.grid()
                return
            url = create_google_calendar_url(qr_cat_var.get(), description, qr_amount_var.get().replace(',', '.'), date_obj, qr_type_var.get())
            current_url_var.set(url)
            url_text.delete('1.0', tk.END)
            url_text.insert(tk.END, url)
            self.clipboard_clear()
            self.clipboard_append(url)
            browser_message.config(text="Link copiato negli appunti!", foreground="green")
            url_display_label.grid()
            url_text.grid()
            link_button.grid()
            browser_button.grid()
            browser_message.grid()
            generate_button.config(text="Rigenera QR Code/Link")
        fields = [
            ("Categoria:", cat_combobox),
            ("Data:", date_entry_widget_frame),
            ("Descrizione (Note):", desc_text_widget),
            ("Tipo:", ttk.Combobox(main_frame, textvariable=qr_type_var, values=TYPE_OPTIONS, state="readonly", width=30, style='Border.TCombobox')),
            ("Importo:", qr_amount_entry) 
        ]
        current_row = 0
        for label_text, widget in fields:
            sticky_val = "nw" if isinstance(widget, tk.Text) else "w"
            ttk.Label(main_frame, text=label_text).grid(row=current_row, column=0, sticky=sticky_val, pady=5, padx=5)
            if isinstance(widget, tk.Text):
                widget.grid(row=current_row, column=1, sticky="ew", pady=5, padx=5, rowspan=3)
                current_row += 3
            else:
                widget.grid(row=current_row, column=1, sticky="ew", pady=5, padx=5)
                current_row += 1
        ttk.Separator(main_frame, orient='horizontal').grid(row=current_row, columnspan=2, sticky="ew", pady=10)
        current_row += 1
        generate_button = ttk.Label(
            main_frame, 
            image=self.icone_gui.get("qr_code"), 
            text=" Genera QR Code/Link", 
            compound="left", 
            cursor="hand2", 
            background=self.COLOR_WIDGET_BG,
            font=("Arial", 9, "bold")
        )
        generate_button.image = self.icone_gui.get("qr_code")
        generate_button.grid(row=current_row, column=0, sticky="ew", pady=5, padx=(0, 5))
        generate_button.bind("<Button-1>", lambda e: generate_qr_logic())
        close_button = ttk.Label(
            main_frame, 
            image=self.icone_gui.get("chiudi"), 
            text=" Chiudi", 
            compound="left", 
            cursor="hand2", 
            background=self.COLOR_WIDGET_BG,
            font=("Arial", 9, "bold")
        )
        close_button.image = self.icone_gui.get("chiudi")
        close_button.grid(row=current_row, column=1, sticky="ew", pady=5, padx=(5, 0))
        close_button.bind("<Button-1>", lambda e: close_and_cleanup())
        current_row += 1
        reset_button = ttk.Label(
            main_frame, 
            image=self.icone_gui.get("reset"), 
            text=" Reset Campi", 
            compound="left", 
            cursor="hand2", 
            background=self.COLOR_WIDGET_BG,
            font=("Arial", 9, "bold")
        )
        reset_button.image = self.icone_gui.get("reset")
        reset_button.grid(row=current_row, column=0, sticky="ew", pady=5, padx=(0, 5))
        reset_button.bind("<Button-1>", lambda e: reset_fields())
        agenda_button = ttk.Label(
            main_frame, 
            image=self.icone_gui.get("calendario"), 
            text=" Vai ad Agenda Calendar", 
            compound="left", 
            cursor="hand2", 
            background=self.COLOR_WIDGET_BG,
            font=("Arial", 9, "bold")
        )
        agenda_button.image = self.icone_gui.get("calendario")
        agenda_button.grid(row=current_row, column=1, sticky="ew", pady=5, padx=(5, 0))
        agenda_button.bind("<Button-1>", lambda e: open_agenda_url())
        current_row += 1
        url_display_label = ttk.Label(main_frame, text="LINK GENERATO:", font=('Arial', 10, 'bold'))
        url_display_label.grid(row=current_row, columnspan=2, sticky="w", pady=(10, 5))
        url_display_label.grid_remove()
        url_text = tk.Text(
            main_frame, height=3, width=50, wrap="word", 
            bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR, insertbackground=self.TEXT_COLOR,
            font=("Courier new", 9), relief="flat", highlightthickness=1, highlightbackground=self.COLOR_HIGHLIGHT
        )
        url_text.grid(row=current_row + 1, columnspan=2, sticky="ew")
        url_text.grid_remove()
        browser_button = ttk.Label(
            main_frame, 
            image=self.icone_gui.get("qr_code"), 
            text=" Mostra QR Code", 
            compound="left", 
            cursor="hand2", 
            background=self.COLOR_WIDGET_BG,
            font=("Arial", 9, "bold")
        )
        browser_button.image = self.icone_gui.get("qr_code")
        browser_button.grid(row=current_row + 2, column=0, sticky="ew", pady=10, padx=(0, 5))
        browser_button.bind("<Button-1>", lambda e: show_qr_popup_window())
        browser_button.grid_remove()
        link_button = ttk.Label(
            main_frame, 
            image=self.icone_gui.get("link"), 
            text=" Apri Link Promemoria", 
            compound="left", 
            cursor="hand2", 
            background=self.COLOR_WIDGET_BG,
            font=("Arial", 9, "bold")
        )
        link_button.image = self.icone_gui.get("link")
        link_button.grid(row=current_row + 2, column=1, sticky="ew", pady=10, padx=(5, 0))
        link_button.bind("<Button-1>", lambda e: open_link_in_browser())
        link_button.grid_remove()
        browser_message = ttk.Label(main_frame, text="", foreground="blue")
        browser_message.grid(row=current_row + 3, columnspan=2, pady=5)
        browser_message.grid_remove()
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
    show_unified_qr_generator(self)
