#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import tkinter as tk
from tkcalendar import Calendar

from moduli.modello_spesa import campo

# Gestore Popup Calendario Selettore Data senza movimenti
def mostra_calendario_popup_semplice(self, entry_widget, var_data):
    if hasattr(self, "popup_calendario") and self.popup_calendario and self.popup_calendario.winfo_exists():
        self.popup_calendario.destroy()
        self.popup_calendario = None
        self.unbind_all('<Button-1>')
        if hasattr(self, '_focus_poll_id') and self._focus_poll_id:
            self.after_cancel(self._focus_poll_id)
            self._focus_poll_id = None
        return
    entry_widget.update_idletasks()
    x_entry = entry_widget.winfo_rootx()
    y_entry = entry_widget.winfo_rooty()
    w_entry = entry_widget.winfo_width()
    h_entry = entry_widget.winfo_height()
    POPUP_WIDTH = 270
    POPUP_HEIGHT = 240
    screen_height = self.winfo_screenheight()
    y_sopra = y_entry - POPUP_HEIGHT
    y_sotto = y_entry + h_entry
    if y_sotto + POPUP_HEIGHT > screen_height and y_sopra > 0:
         final_y = y_sopra
    else:
         final_y = y_sotto
    self.popup_calendario = tk.Toplevel(self)
    self.popup_calendario.transient(self)
    self.popup_calendario.withdraw() 
    self.popup_calendario.title("Seleziona Data")
    self.popup_calendario.overrideredirect(True) 
    self.popup_calendario.config(
            highlightthickness=1, 
            highlightbackground=self.COLOR_HIGHLIGHT
    )
    self.popup_calendario.geometry(f"{POPUP_WIDTH}x{POPUP_HEIGHT}+{x_entry}+{final_y}")
    self.popup_calendario.configure(bg=self.cal_bg)
    cal = Calendar(
        self.popup_calendario,
        selectmode='day',
        locale="it_IT",
        date_pattern="dd-mm-yyyy",
        font=("Arial", 10),
        cursor="hand2",
        background=self.cal_header_bg,
        foreground=self.cal_header_fg,
        headersbackground=self.cal_header_bg,
        headersforeground=self.cal_header_fg,
        normalbackground=self.cal_bg,
        normalforeground=self.cal_fg,
        weekendbackground=self.cal_weekend_bg,
        weekendforeground=self.cal_weekend_fg,
        selectbackground=self.cal_select_bg,
        selectforeground=self.cal_select_fg,
        showweeknumbers=False,
        bordercolor=self.cal_bg,
        showothermonthdays=False
    )
    cal.pack(fill="both", expand=True, padx=1, pady=1)
    oggi = datetime.date.today()
    cal.calevent_create(oggi, "Oggi", "today")
    cal.tag_config("today", background=self.cal_select_bg, foreground=self.cal_select_fg) 
    def chiudi_popup():
        self.unbind_all('<Button-1>')
        if hasattr(self, '_focus_poll_id') and self._focus_poll_id:
            self.after_cancel(self._focus_poll_id)
            self._focus_poll_id = None
        if hasattr(self, 'popup_calendario') and self.popup_calendario:
            try:
                self.popup_calendario.destroy()
            except:
                pass
            self.popup_calendario = None
        self.focus_set()
    def on_date_select(event):
        data_sel = cal.selection_get()
        var_data.set(data_sel.strftime("%d-%m-%Y"))
        chiudi_popup()
    def check_click_outside(event):
        if not self.popup_calendario or not self.popup_calendario.winfo_exists():
            self.unbind_all('<Button-1>')
            return
        try:
            x, y = event.x_root, event.y_root
            cx = self.popup_calendario.winfo_rootx()
            cy = self.popup_calendario.winfo_rooty()
            cw = self.popup_calendario.winfo_width()
            ch = self.popup_calendario.winfo_height()
            if not (cx <= x <= cx + cw and cy <= y <= cy + ch):
                if event.widget != self.btn_cal_btm:
                    chiudi_popup()
        except:
            chiudi_popup()
    def poll_focus():
        if not hasattr(self, 'popup_calendario') or not self.popup_calendario:
            return
        try:
            if not self.popup_calendario.winfo_exists():
                return
        except:
            return
        if self.focus_get() is None:
            chiudi_popup()
            return
        self._focus_poll_id = self.after(50, poll_focus)
    cal.bind("<<CalendarSelected>>", on_date_select)
    self.popup_calendario.deiconify()
    self._focus_poll_id = self.after(100, poll_focus)
    self.after(300, lambda: self.bind_all('<Button-1>', check_click_outside))

# Gestore Popup Calendario Selettore Data con movimenti
def mostra_calendario_popup(self, entry_widget, var_data):
    import __main__ as _app
    CAL_TOOLTIPS = _app.CAL_TOOLTIPS
    if hasattr(self, "popup_calendario") and self.popup_calendario and self.popup_calendario.winfo_exists():
        self.popup_calendario.destroy()
        self.popup_calendario = None
        self.unbind_all('<Button-1>')
        return
    entry_widget.update_idletasks()
    x_entry = entry_widget.winfo_rootx()
    y_entry = entry_widget.winfo_rooty()
    h_entry = entry_widget.winfo_height()
    POPUP_WIDTH, POPUP_HEIGHT = 270, 240
    final_y = y_entry - POPUP_HEIGHT if (y_entry + h_entry + POPUP_HEIGHT > self.winfo_screenheight()) else y_entry + h_entry
    self.popup_calendario = tk.Toplevel(self)
    self.popup_calendario.transient(self)
    self.popup_calendario.withdraw() 
    self.popup_calendario.overrideredirect(True) 
    self.popup_calendario.config(
            highlightthickness=1, 
            highlightbackground=self.COLOR_HIGHLIGHT
    )
    self.popup_calendario.geometry(f"{POPUP_WIDTH}x{POPUP_HEIGHT}+{x_entry}+{final_y}")
    self.popup_calendario.configure(bg=self.cal_bg)
    cal = Calendar(
        self.popup_calendario,
        selectmode='day',
        locale="it_IT",
        date_pattern="dd-mm-yyyy",
        font=("Arial", 10),
        cursor="hand2",
        showothermonthdays=False,
        background=self.cal_header_bg,
        foreground=self.cal_header_fg,
        headersbackground=self.cal_header_bg,
        headersforeground=self.cal_header_fg,
        normalbackground=self.cal_bg,
        normalforeground=self.cal_fg,
        weekendbackground=self.cal_weekend_bg,
        weekendforeground=self.cal_weekend_fg,
        selectbackground=self.cal_select_bg,
        selectforeground=self.cal_select_fg,
        showweeknumbers=False,
        bordercolor=self.cal_bg,
        tooltipdelay=999999
    )
    cal.pack(fill="both", expand=True)
    self.cal_popup = cal
    cal.tag_config("verde", background=self.COLOR_LIGHTGREEN, foreground=self.COLOR_BLACK)
    cal.tag_config("rosso", background=self.COLOR_LIGHTCORAL, foreground=self.COLOR_BLACK)
    cal.tag_config("misto", background=self.COLOR_KHAKI, foreground=self.COLOR_BLACK)
    cal.tag_config("today", background=self.COLOR_YELLOW, foreground=self.COLOR_BLACK)
    try:
        if hasattr(self, 'spese') and self.spese:
            for d_str, entries in self.spese.items():
                d_obj = datetime.datetime.strptime(d_str, "%d-%m-%Y").date() if isinstance(d_str, str) else d_str
                txt, e_sum, u_sum = "", 0, 0
                for e in entries:
                    tipo = campo(e, "tipo", "")
                    cat = campo(e, "categoria", "")
                    imp = campo(e, "importo", 0.0)
                    segno = "+" if str(tipo).lower() == "entrata" else "-"
                    txt += f"{segno} {cat}: {float(imp):.2f}\n"
                    if segno == "+": e_sum += 1
                    else: u_sum += 1
                tag = "misto" if e_sum > 0 and u_sum > 0 else ("verde" if e_sum > 0 else "rosso")
                cal.calevent_create(d_obj, txt.strip(), tag)
        cal._draw_calendar()
    except: pass 
    def chiudi_popup():
        if hasattr(self, 'tw') and self.tw and self.tw.winfo_exists(): self.tw.destroy()
        if hasattr(self, 'popup_calendario') and self.popup_calendario:
            try: self.popup_calendario.destroy()
            except: pass
            self.popup_calendario = None
            self.unbind_all('<Button-1>')
    def on_date_select(event):
        data_sel = cal.selection_get()
        var_data.set(data_sel.strftime("%d-%m-%Y"))
        self.cal_popup = None
        chiudi_popup()
    def check_click_outside(event):
        if not self.popup_calendario or not self.popup_calendario.winfo_exists(): return
        x, y = self.popup_calendario.winfo_pointerxy()
        widget_sotto = self.popup_calendario.winfo_containing(x, y)
        if widget_sotto is None or str(widget_sotto).find(str(self.popup_calendario)) == -1:
            if widget_sotto != entry_widget: chiudi_popup()
    def gestisci_tooltip(event):
        if hasattr(self, 'tooltip_timer') and self.tooltip_timer:
            self.after_cancel(self.tooltip_timer)
            self.tooltip_timer = None
        if hasattr(self, 'tw') and self.tw and self.tw.winfo_exists():
            self.tw.withdraw()
        def mostra_reale():
            try:
                x_m, y_m = self.popup_calendario.winfo_pointerxy()
                widget = self.popup_calendario.winfo_containing(x_m, y_m)
                if widget and "label" in str(widget) and widget.cget("text").isdigit():
                    giorno = int(widget.cget("text"))
                    mese, anno = cal.get_displayed_month()
                    data_h = datetime.date(anno, mese, giorno)
                    evs = cal.get_calevents(data_h)
                    righe_raw = [cal.calevent_cget(i, "text") for i in evs if cal.calevent_cget(i, "text") != "Oggi"]
                    if righe_raw or data_h == datetime.date.today():
                        if not hasattr(self, 'tw') or not self.tw.winfo_exists():
                            self.tw = tk.Toplevel(self.popup_calendario)
                            self.tw.overrideredirect(True)
                            self.tw.attributes("-topmost", True)
                        self.tw.withdraw()
                        for c in self.tw.winfo_children(): c.destroy()
                        self.tw.minsize(180, 0)
                        main_f = tk.Frame(
                           self.tw, 
                           bg=self.COLOR_TOOLTIP, 
                           highlightthickness=1, 
                           highlightbackground=self.COLOR_HIGHLIGHT
                        )
                        main_f.pack(fill="both", expand=True)   
                        self.tw.minsize(200, 0)
                        entrate, uscite = [], []
                        tot_e, tot_u = 0.0, 0.0
                        for blocco in righe_raw:
                            for r in blocco.split('\n'):
                                if not r.strip(): continue
                                try:
                                    parti = r.split(':')
                                    desc = parti[0].replace("+ ", "").replace("- ", "").strip()
                                    valore = float(parti[1].strip().replace(',', '.'))
                                    r_data = (desc, f"{valore:.2f}")
                                    if "+" in r:
                                        entrate.append(r_data); tot_e += valore
                                    elif "-" in r:
                                        uscite.append(r_data); tot_u += valore
                                except: pass
                        def crea_riga(parent, sx, dx, col, bold=False):
                            f = tk.Frame(parent, bg=self.COLOR_TOOLTIP)
                            f.pack(fill="x", padx=10, pady=1)
                            fnt = ("Arial", 9, "bold")
                            lbl_sx = tk.Label(f, text=sx, fg=col, bg=self.COLOR_TOOLTIP, font=fnt, anchor="w")
                            lbl_sx.pack(side="left", fill="x", expand=True)
                            testo_dx = f"€ {dx}" if bold else dx
                            lbl_dx = tk.Label(f, text=testo_dx, fg=col, bg=self.COLOR_TOOLTIP, font=fnt, anchor="e")
                            lbl_dx.pack(side="right")
                        if entrate:
                            crea_riga(main_f, "▲ SALDO (+):", f"{tot_e:.2f}", self.COLOR_GREEN_SMOOTH, True)
                            for d, v in entrate: crea_riga(main_f, d, v, self.COLOR_TEXT_TOOLTIP)
                        if uscite:
                            if entrate: tk.Frame(main_f, height=1, bg="gray").pack(fill="x", padx=5, pady=2)
                            crea_riga(main_f, "▼ SALDO (-):", f"{tot_u:.2f}", self.COLOR_RED_SMOOTH, True)
                            for d, v in uscite: crea_riga(main_f, d, v, self.COLOR_TEXT_TOOLTIP)
                        if not entrate and not uscite:
                            tk.Label(main_f, text="Oggi", fg=self.COLOR_TEXT_TOOLTIP, bg=self.COLOR_TOOLTIP,
                                     font=("Arial", 9, "bold"), padx=10).pack(anchor="w")
                        self.tw.update_idletasks()
                        tw_w, tw_h = self.tw.winfo_reqwidth(), self.tw.winfo_reqheight()
                        scr_w, scr_h = self.winfo_screenwidth(), self.winfo_screenheight()
                        px, py = x_m + 15, y_m + 10
                        if px + tw_w > scr_w: px = x_m - tw_w - 15
                        if py + tw_h > scr_h: py = y_m - tw_h - 10
                        self.tw.geometry(f"{tw_w}x{tw_h}+{max(0, px)}+{max(0, py)}")
                        self.tw.deiconify()
                        self.tw.lift()
            except:
                if hasattr(self, 'tw') and self.tw.winfo_exists():
                    self.tw.withdraw()
        self.tooltip_timer = self.after(1000, mostra_reale)
    def applica_ricorsivo(w):
        def safe_withdraw(e):
            if hasattr(self, 'tw') and self.tw:
                try:
                    if self.tw.winfo_exists():
                        self.tw.withdraw()
                except:
                        pass
        w.bind("<Motion>", gestisci_tooltip, add="+")
        w.bind("<Leave>", safe_withdraw, add="+")
        for child in w.winfo_children():
             applica_ricorsivo(child)
    if CAL_TOOLTIPS:
        applica_ricorsivo(cal)
    else:
        try:
            cal.configure(tooltipdelay=999999)
        except:
            pass
    def on_app_focus_out(event):
        if event.widget != self:
            return
        try:
           x, y = self.winfo_pointerxy()
           widget_sotto = self.winfo_containing(x, y)
           if widget_sotto and str(self.popup_calendario) in str(widget_sotto):
              return
        except:
              pass
        chiudi_popup()
    cal.bind("<<CalendarSelected>>", on_date_select)
    self.bind_all('<Button-1>', check_click_outside)
    self.bind("<FocusOut>", on_app_focus_out)
    self.popup_calendario.deiconify()

