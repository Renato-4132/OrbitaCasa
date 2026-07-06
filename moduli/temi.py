#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter import ttk

def applica_temi(self, THEMA):
        if THEMA == "CHIARO":
            style = ttk.Style()
            style.theme_use('default')
            MENU_BG_DARK = "white"              # Sfondo Barra menu superiore
            MENU_FG_LIGHT = "black"             # Colore di primo piano chiaro (bianco)
            MENU_BG = "white"                   # Sfondo dei sottomenu
            MENU_ACT_BG_COLOR = "#00AADD"       # Colore di evidenziazione 
            MENU_ACT_FG_COLOR = "black"         # Nero 
            COLOR_BACKGROUND = "#FFFFFF"        # Sfondo principale (Bianco Puro)
            COLOR_WIDGET_BG = "white"           # Sfondo widget leggero (Bianco)
            TEXT_COLOR = "black"                # Testo nero
            COLOR_HIGHLIGHT = "#007ACC"         # Blu Windows/VSCode per la selezione
            COLOR_TEXT = "#333333"              # Testo scuro/nero
            COLOR_HEADER = "black"              # Testo scuro per le intestazioni
            COLOR_RED = "red"                   # Rosso standard
            COLOR_GREEN = "green"               # Verde standard
            COLOR_ORANGE = "orange"             # Arancio standard
            COLOR_RED_SMOOTH = "red"            # Rosso standard
            COLOR_GREEN_SMOOTH = "green"        # Verde standard
            COLOR_HEADER_BG = "#AAAAAA"         # Grigio medio per sfondo header Treeview
            COLOR_BUTTON_BG = "#DDDDDD"         # Grigio chiaro per bottoni standard
            COLOR_BLINK_OFF = "#333333"         # Il colore "spento" è Bianco
            COLOR_UPDATE = "#FFFFAA"            # Giallo acceso per l'avviso (come richiesto in precedenza)
            COLOR_BLACK = "black"               # Nero 
            COLOR_YELLOW = "yellow"             # Giallo 
            COLOR_WHITE = "white"               # Bianco 
            COLOR_LIGHTGREEN = "lightgreen"     # LightGreen
            COLOR_LIGHTCORAL = "lightcoral"     # LightCoral
            COLOR_KHAKI = "khaki"               # Khaki
            COLOR_TOOLTIP = "#F9F9F9"           # grigio chiarissimo, quasi bianco.
            COLOR_TEXT_TOOLTIP = "black"        # nero Testo tooltip.
            self.MENU_BG_DARK = MENU_BG_DARK
            self.MENU_FG_LIGHT = MENU_FG_LIGHT
            self.MENU_BG = MENU_BG   
            self.MENU_ACT_BG_COLOR = MENU_ACT_BG_COLOR
            self.MENU_ACT_FG_COLOR = MENU_ACT_FG_COLOR                        
            self.COLOR_TOPLEVEL = COLOR_WIDGET_BG
            self.TEXT_COLOR = TEXT_COLOR
            self.COLOR_BACKGROUND = COLOR_BACKGROUND
            self.COLOR_WIDGET_BG = COLOR_WIDGET_BG
            self.COLOR_HIGHLIGHT = COLOR_HIGHLIGHT
            self.COLOR_TEXT = COLOR_TEXT
            self.COLOR_HEADER = COLOR_HEADER
            self.COLOR_RED = COLOR_RED
            self.COLOR_GREEN = COLOR_GREEN
            self.COLOR_RED_SMOOTH = COLOR_RED_SMOOTH
            self.COLOR_GREEN_SMOOTH = COLOR_GREEN_SMOOTH
            self.COLOR_ORANGE = COLOR_ORANGE
            self.COLOR_HEADER_BG = COLOR_HEADER_BG
            self.COLOR_BUTTON_BG = COLOR_BUTTON_BG
            self.COLOR_BLINK_OFF = COLOR_BLINK_OFF
            self.COLOR_UPDATE = COLOR_UPDATE
            self.COLOR_BLACK = COLOR_BLACK
            self.COLOR_YELLOW = COLOR_YELLOW
            self.COLOR_WHITE = COLOR_WHITE     
            self.COLOR_LIGHTGREEN = COLOR_LIGHTGREEN
            self.COLOR_LIGHTCORAL = COLOR_LIGHTCORAL
            self.COLOR_KHAKI = COLOR_KHAKI
            self.COLOR_TOOLTIP = COLOR_TOOLTIP
            self.COLOR_TEXT_TOOLTIP = COLOR_TEXT_TOOLTIP            
            try:
                self.option_add('*selectBackground', COLOR_HIGHLIGHT)
                self.option_add('*selectForeground', COLOR_WHITE)
                self.option_add('*Focus.background', COLOR_WIDGET_BG)
                self.option_add('*Focus.relief', 'solid')
                self.option_add('*Focus.borderwidth', 1)
            except Exception:
                pass                
            self.configure(bg=COLOR_BACKGROUND)                  
            style.configure("TFrame", background=COLOR_WIDGET_BG)
            style.configure("BlackFrame.TFrame", background=COLOR_WIDGET_BG)
            style.configure("TLabelframe", background=COLOR_WIDGET_BG) 
            style.configure("TLabelframe.Label", background=COLOR_WIDGET_BG, foreground=COLOR_HEADER)
            style.configure("RedBold.TLabelframe.Label", foreground=COLOR_RED_SMOOTH, background=COLOR_WIDGET_BG, font=("Arial", 10, "bold"))            
            style.configure("Rosso.TSeparator", background="red", thickness=2)               
            style.configure("Treeview", 
                            background=COLOR_WHITE, 
                            foreground=COLOR_TEXT, 
                            rowheight=25,
                            fieldbackground=COLOR_WHITE, 
                            font=("Arial", 10),
                            borderwidth=0)
            style.configure("Treeview.Heading", 
                            background="#F2F2F2",
                            foreground=COLOR_HEADER, 
                            font=('Arial', 10, 'bold'), 
                            relief="flat",
                            borderwidth=1) 
            style.map('Treeview', 
                      foreground=[('selected', COLOR_WHITE)], 
                      background=[('selected', COLOR_HIGHLIGHT)],
                      fieldbackground=[('!disabled', COLOR_WIDGET_BG)]
            )
            style.map('Treeview.Heading', 
                foreground=[('active', COLOR_HIGHLIGHT), ('pressed', COLOR_HIGHLIGHT)], 
                background=[('active', "#EAEAEA"), ('pressed', "#DDDDDD")] 
            )
            style.configure("TNotebook", background=COLOR_WIDGET_BG, borderwidth=0)
            style.configure("TNotebook.Tab", 
                            background=COLOR_BACKGROUND,
                            foreground=COLOR_TEXT,
                            font=('Arial', 10, 'normal'),
                            padding=[6, 2])            
            style.map("TNotebook.Tab",
                      background=[('selected', COLOR_HIGHLIGHT)], 
                      foreground=[('selected', COLOR_WHITE)],
                      expand=[('active', [1, 1, 1, 0])])
            style.configure("Custom.TRadiobutton", background=COLOR_WIDGET_BG, foreground=TEXT_COLOR, font=('Arial', 10))
            style.map("Custom.TRadiobutton",
                  background=[('active', self.COLOR_WIDGET_BG), ('alternate', self.COLOR_WIDGET_BG)],
                  foreground=[('active', self.TEXT_COLOR), ('alternate', self.TEXT_COLOR)])                  
            style.configure('Highlight.TCombobox', 
                fieldbackground=COLOR_WIDGET_BG,
                background=COLOR_BUTTON_BG, 
                foreground=COLOR_RED_SMOOTH,
                relief='solid', 
                arrowsize=8, 
                borderwidth=1)
            style.map('Highlight.TCombobox', 
                arrowcolor=[('!disabled', COLOR_RED_SMOOTH)],
                fieldbackground=[
                    ('readonly', COLOR_WIDGET_BG), 
                    ('focus', COLOR_WIDGET_BG), 
                    ('active', COLOR_WIDGET_BG),
                    ('!disabled', COLOR_WIDGET_BG)
                ],
                foreground=[
                    ('readonly', COLOR_RED_SMOOTH), 
                    ('focus', COLOR_RED_SMOOTH), 
                    ('active', COLOR_RED_SMOOTH),
                    ('!disabled', COLOR_RED_SMOOTH)
                ])            
            style.configure(
                "Custom.TSpinbox",
                fieldbackground=COLOR_WHITE,
                background=COLOR_BUTTON_BG,
                foreground=COLOR_BLACK,
                arrowcolor=COLOR_HIGHLIGHT,
                borderwidth=1,
                relief="solid",
                insertcolor=COLOR_BLACK,
                selectbackground=COLOR_WHITE,
                selectforeground=COLOR_HIGHLIGHT 
            )
            style.map(
                "Custom.TSpinbox",
                fieldbackground=[("readonly", COLOR_WHITE), ("focus", COLOR_WHITE)],
                arrowcolor=[("active", COLOR_BLACK), ("disabled", "#CCCCCC")],
                background=[("active", "#EEEEEE")],
                selectbackground=[("focus", COLOR_WHITE)], 
                selectforeground=[("focus", COLOR_HIGHLIGHT)] 
            )
            style.configure('Border.TCombobox', 
                fieldbackground=COLOR_WHITE, 
                background=COLOR_YELLOW, 
                foreground=COLOR_BLACK, 
                relief='flat',
                arrowsize=8,
                borderwidth=1)
            style.map('Border.TCombobox', 
                arrowcolor=[('!disabled', COLOR_HIGHLIGHT)],
                fieldbackground=[('readonly', COLOR_WHITE), ('!focus', COLOR_WHITE), ('!disabled', COLOR_WHITE)],
                selectbackground=[('readonly', COLOR_WIDGET_BG), ('focus', COLOR_WIDGET_BG)],
                selectforeground=[('readonly', TEXT_COLOR), ('focus', TEXT_COLOR)])
            style.configure("TEntry", 
                fieldbackground=COLOR_WIDGET_BG, 
                foreground=COLOR_TEXT,
                insertcolor=COLOR_BLACK,
                borderwidth=1, 
                relief="flat")
            style.map("TEntry", 
                fieldbackground=[('focus', COLOR_WIDGET_BG), ('readonly', COLOR_WIDGET_BG)],
                foreground=[('disabled', COLOR_TEXT), ('readonly', COLOR_TEXT)])
            style.configure("TLabel", background=COLOR_WIDGET_BG, foreground=COLOR_TEXT) 
            style.configure("Timer.TLabel", foreground=COLOR_TEXT, background=COLOR_UPDATE, font=("Helvetica", 10, "bold"))
            style.configure("Legend.TLabel", background=COLOR_WIDGET_BG, foreground=COLOR_TEXT, font=("Arial", 10), anchor="w")
            style.configure("White.TLabel", foreground=COLOR_TEXT, background=COLOR_WIDGET_BG, font=("Arial", 11))
            style.configure("WhiteSmall.TLabel", foreground=COLOR_TEXT, background=COLOR_WIDGET_BG, font=("Arial", 10))
            style.configure("Verde.TLabel", foreground=COLOR_GREEN_SMOOTH, background=COLOR_WIDGET_BG, font=("Arial", 10, "bold"), padding=5)
            style.configure("Saldo.TLabel", foreground=COLOR_GREEN_SMOOTH, background=COLOR_WIDGET_BG, font=("Arial", 14, "bold"))
            style.map("Saldo.TLabel", background=[('active', COLOR_WIDGET_BG)], foreground=[('active', COLOR_GREEN_SMOOTH)], relief=[('active', 'flat')])
            style.configure("Doc.TLabel", foreground=COLOR_GREEN_SMOOTH, background=COLOR_WIDGET_BG, font=("Arial", 14, "bold"))
            style.map("Doc.TLabel", background=[('active', COLOR_WIDGET_BG)], foreground=[('active', COLOR_GREEN_SMOOTH)], relief=[('active', 'flat')])            
            style.configure("GSaldo.TLabel", font=("Arial", 10, "bold"), background=COLOR_WIDGET_BG) 
            style.map("GSaldoPositivo.TLabel", foreground=[('active', COLOR_GREEN_SMOOTH), ('!disabled', COLOR_GREEN_SMOOTH)], parent="GSaldo.TLabel")
            style.map("GSaldoNegativo.TLabel", foreground=[('active', COLOR_RED_SMOOTH), ('!disabled', COLOR_RED_SMOOTH)], parent="GSaldo.TLabel")
            style.configure("BlinkAllarme.TLabel", foreground=COLOR_BLINK_OFF, background=COLOR_WIDGET_BG, font=("Arial", 10, "bold"))
            style.map("BlinkAllarme.TLabel", foreground=[('!disabled', COLOR_RED_SMOOTH)], background=[('!disabled', COLOR_WIDGET_BG), ('disabled', COLOR_WIDGET_BG)])
            SPESSORE_SCROLL = 7
            style.configure("Vertical.TScrollbar", 
                background="#f5f5f5", 
                troughcolor="white",
                arrowcolor=COLOR_HEADER,
                borderwidth=0, 
                relief="flat",
                arrowsize=SPESSORE_SCROLL,
                width=SPESSORE_SCROLL)
            style.configure("Horizontal.TScrollbar", 
                background="#f5f5f5", 
                troughcolor="white",
                arrowcolor=COLOR_HEADER, 
                borderwidth=0, 
                relief="flat",
                arrowsize=SPESSORE_SCROLL,
                width=SPESSORE_SCROLL)
            style.map("Vertical.TScrollbar", background=[('active', COLOR_HIGHLIGHT)])
            style.map("Horizontal.TScrollbar", background=[('active', COLOR_HIGHLIGHT)])
            style.configure("TScale", 
                background=COLOR_WIDGET_BG, 
                foreground=COLOR_HIGHLIGHT,
                troughcolor="#E0E0E0",
                sliderthickness=10,
                troughthickness=2,
                sliderlength=15,
                relief='flat')
            style.map("TScale", 
                background=[('active', COLOR_HIGHLIGHT)],
               troughcolor=[('disabled', COLOR_WIDGET_BG)])
            style.configure("TCheckbutton", background=COLOR_WIDGET_BG, foreground=COLOR_HEADER, font=("Arial", 10))
            style.map("TCheckbutton", background=[('active', COLOR_WIDGET_BG)], foreground=[('active', COLOR_HEADER),('selected', COLOR_HEADER)])
            style.configure("Tooltip.TLabel", background=COLOR_TOOLTIP, foreground=COLOR_BLACK, font=("Arial", 9), borderwidth=1, relief="solid", anchor='w', padding=2)            
            style.configure("TButton", relief='flat', borderwidth=0, font=("Arial", 9, "bold"), padding=5, background=COLOR_BUTTON_BG, foreground=COLOR_TEXT) 
            style.map("TButton", background=[("active", "#CCCCCC")])
            style.configure("Yellow.TButton", background=COLOR_YELLOW, foreground=COLOR_BLACK, font=("Arial", 8, "bold"), width=2)
            style.map("Yellow.TButton", background=[("active", "#FFE680")])
            style.configure("Giallo.TButton", background=COLOR_YELLOW, foreground=COLOR_BLACK, font=("Arial", 8, "bold"))
            style.map("Giallo.TButton", background=[("active", "#FFE680")])
            style.configure("Verde.TButton", background=COLOR_GREEN_SMOOTH, foreground=COLOR_BLACK, font=("Arial", 8, "bold"))
            style.map("Verde.TButton", background=[('active', '#8AAB6F')], foreground=[('disabled', COLOR_YELLOW)])
            style.configure("Rosso.TButton", background=COLOR_RED_SMOOTH, foreground=COLOR_BLACK, font=("Arial", 8, "bold"))
            style.map("Rosso.TButton", background=[('active', '#C8606B')], foreground=[('disabled', COLOR_YELLOW)])
            style.configure("Arancio.TButton", background="#FFA500", foreground=COLOR_BLACK, font=("Arial", 8, "bold"))
            style.map("Arancio.TButton", background=[("active", "#FFC766")])
            style.configure("Blu.TButton", background=COLOR_HIGHLIGHT, foreground=COLOR_WHITE, font=("Arial", 8, "bold"))
            style.map("Blu.TButton", background=[("active", "#00AADD")])
            style.configure("Verde_Low.TButton", background=COLOR_GREEN_SMOOTH, foreground=COLOR_WHITE, font=("Arial", 8, "bold"), padding=(2, 0))
            style.map("Verde_Low.TButton", background=[('active', '#8AAB6F')], foreground=[('disabled', COLOR_YELLOW)])
            style.configure("Yellow_Low.TButton", background=COLOR_YELLOW, foreground=COLOR_BLACK, font=("Arial", 8, "bold"), width=2, padding=(2, 0))
            style.map("Yellow_Low.TButton", background=[("active", "#FFE680")])
            style.configure("Low.Blu.TButton", background=COLOR_HIGHLIGHT, foreground=COLOR_WHITE, font=("Arial", 6, "bold"), padding=(4, 1))
            style.map("Low.Blu.TButton", background=[("active", "#00AADD")])
            style.configure("Num.TButton", foreground=COLOR_TEXT, background=COLOR_WIDGET_BG, borderwidth=1, relief="raised", font=("Arial", 8, "bold"), padding=6) 
            style.map("Num.TButton", background=[("active", COLOR_HEADER_BG)])             
            style.configure("GreenOutline.TButton", foreground=COLOR_GREEN_SMOOTH, background=COLOR_WIDGET_BG, borderwidth=1, relief="solid", padding=(5, 1), font=("Arial", 10, "bold")) 
            style.map("GreenOutline.TButton", 
                      background=[("active", "#E6FFE6"), ("pressed", "#CCFFCC")],
                      bordercolor=[("!disabled", COLOR_GREEN_SMOOTH)], 
                      foreground=[("!disabled", COLOR_GREEN_SMOOTH)])
            style.configure("RedOutline.TButton", foreground=COLOR_RED_SMOOTH, background=COLOR_WIDGET_BG, borderwidth=1, relief="solid", cursor="hand2", padding=(5, 1), font=("Arial", 10, "bold")) 
            style.map("RedOutline.TButton", 
                      background=[("active", "#FFEEEE"), ("pressed", "#FFCCCC")],
                      bordercolor=[("!disabled", COLOR_RED_SMOOTH)], 
                      foreground=[("!disabled", COLOR_RED_SMOOTH)])
            style.configure(
                "Backup.Horizontal.TProgressbar",
                troughcolor=self.COLOR_WIDGET_BG,
                background=self.COLOR_HIGHLIGHT,
                thickness=10
            )
            
            style.configure("Horizontal.TProgressbar", thickness=6)
                                   
            stili_tabella = [
            ("mensile", "#E6FFE6", "#004C00"),
            ("regolare", "#F0FFF0", "#333333"),
            ("bimestrale", "#FFFFE0", "#CC9900"),
            ("trimestrale", "#FFF0E0", "#FF6600"),
            ("irregolare", "#FFEEEE", "#CC0000"),
            ]        
            for alias, bg, fg in stili_tabella:
                style.configure(
                    f"Legenda.{alias}.TLabel", 
                    background=bg, 
                    foreground=fg, 
                    font=("Arial", 8, "bold"),
                    padding=3
                )
            self.cal_bg = COLOR_WIDGET_BG
            self.cal_fg = TEXT_COLOR
            self.cal_weekend_bg = COLOR_WIDGET_BG  
            self.cal_weekend_fg = COLOR_HIGHLIGHT
            self.cal_weekday_bg = COLOR_WIDGET_BG  
            self.cal_weekday_fg = COLOR_HEADER
            self.cal_select_bg = COLOR_HIGHLIGHT 
            self.cal_select_fg = COLOR_BLACK     
            self.cal_header_bg = COLOR_WIDGET_BG   
            self.cal_header_fg = COLOR_HEADER
        if THEMA == "MATERIAL":
            style = ttk.Style()
            style.theme_use('default')
            MENU_BG_DARK = "#2A273F"               # Sfondo Barra menu superiore
            MENU_FG_LIGHT = "white"                # Colore di primo piano chiaro (bianco)
            MENU_BG = "#4B4673"                    # Sfondo dei sottomenu
            MENU_ACT_BG_COLOR = "#509FE2"          # Colore di evidenziazione (ciano)
            MENU_ACT_FG_COLOR = "black"            # Nero
            COLOR_BACKGROUND = "#20232A"           # Grigio Ardesia Scuro / Quasi Nero (Sfondo Principale)
            COLOR_WIDGET_BG = "#2A273F"            # Blu Violaceo Scuro (Sfondo per Widget/Frame)
            TEXT_COLOR = "white"                   # Bianco Puro (Testo Primario)
            COLOR_HIGHLIGHT = "#61AFEF"            # Azzurro Ciano Brillante (Colore di Enfasi/Selezione Attiva)
            COLOR_TEXT = "#ABB2BF"                 # Grigio Chiaro Freddo (Testo Secondario)
            COLOR_HEADER = "#E0E0E0"               # Grigio Molto Chiaro (Titoli/Intestazioni)
            COLOR_RED = "red"                      # Rosso
            COLOR_GREEN = "green"                  # Verde
            COLOR_RED_SMOOTH = "#E06C75"           # Rosso Salmone Tenue (Avvisi, Negativo/Uscite)
            COLOR_GREEN_SMOOTH = "#98C379"         # Verde Oliva/Salvia (Successo, Positivo/Entrate)
            COLOR_ORANGE = "orange"                # Arancio standard
            COLOR_HEADER_BG = "#39355C"            # Viola Scuro Melanzana (Sfondo Intestazioni/Barre Titolo)
            COLOR_BUTTON_BG = "#4B4673"            # Viola Scuro/Indaco (Sfondo Pulsanti)
            COLOR_BLINK_OFF = COLOR_TEXT           # Grigio Chiaro Freddo (Stato di Non Lampeggio)
            COLOR_UPDATE = "#FFFFAA"               # Giallo Molto Chiaro/Crema (Notifiche di Aggiornamento/Blink)
            COLOR_BLACK = "black"                  # Nero (Interni Combobox)
            COLOR_YELLOW = "yellow"                # Giallo (Pulsante combobox)
            COLOR_WHITE = "white"                  # Bianco (Sfondo combobox)
            COLOR_LIGHTGREEN = "lightgreen"        # LightGreen
            COLOR_LIGHTCORAL = "lightcoral"        # LightCoral
            COLOR_KHAKI = "khaki"                  # Khaki
            COLOR_TOOLTIP = "#4B4673"              # Viola Scuro Desaturato (blu-viola scuro)
            COLOR_TEXT_TOOLTIP = "white"           # Bianco (Sfondo Tooltip)
            self.MENU_BG_DARK = MENU_BG_DARK
            self.MENU_FG_LIGHT = MENU_FG_LIGHT
            self.MENU_BG = MENU_BG   
            self.MENU_ACT_BG_COLOR = MENU_ACT_BG_COLOR
            self.MENU_ACT_FG_COLOR = MENU_ACT_FG_COLOR                        
            self.COLOR_TOPLEVEL = COLOR_WIDGET_BG
            self.TEXT_COLOR = TEXT_COLOR
            self.COLOR_BACKGROUND = COLOR_BACKGROUND
            self.COLOR_WIDGET_BG = COLOR_WIDGET_BG
            self.COLOR_HIGHLIGHT = COLOR_HIGHLIGHT
            self.COLOR_TEXT = COLOR_TEXT
            self.COLOR_HEADER = COLOR_HEADER
            self.COLOR_ORANGE = COLOR_ORANGE
            self.COLOR_RED = COLOR_RED
            self.COLOR_GREEN = COLOR_GREEN
            self.COLOR_RED_SMOOTH = COLOR_RED_SMOOTH
            self.COLOR_GREEN_SMOOTH = COLOR_GREEN_SMOOTH
            self.COLOR_HEADER_BG = COLOR_HEADER_BG
            self.COLOR_BUTTON_BG = COLOR_BUTTON_BG
            self.COLOR_BLINK_OFF = COLOR_BLINK_OFF
            self.COLOR_UPDATE = COLOR_UPDATE
            self.COLOR_BLACK = COLOR_BLACK
            self.COLOR_YELLOW = COLOR_YELLOW
            self.COLOR_WHITE = COLOR_WHITE
            self.COLOR_LIGHTGREEN = COLOR_LIGHTGREEN
            self.COLOR_LIGHTCORAL = COLOR_LIGHTCORAL
            self.COLOR_KHAKI = COLOR_KHAKI
            self.COLOR_TOOLTIP = COLOR_TOOLTIP
            self.COLOR_TEXT_TOOLTIP = COLOR_TEXT_TOOLTIP            
            try:
                self.option_add('*selectBackground', COLOR_HIGHLIGHT)
                self.option_add('*selectForeground', COLOR_WHITE)
                self.option_add('*Focus.background', COLOR_WIDGET_BG)
                self.option_add('*Focus.relief', 'solid')
                self.option_add('*Focus.borderwidth', 1)
                self.option_add('*TCombobox*Listbox.background', COLOR_WIDGET_BG)
                self.option_add('*TCombobox*Listbox.foreground', COLOR_WHITE)
                self.option_add('*TCombobox*Listbox.selectBackground', COLOR_HIGHLIGHT)
                self.option_add('*TCombobox*Listbox.selectForeground', COLOR_BLACK)
                self.option_add('*TCombobox*Listbox.font', ("Arial", 10))
                self.option_add('*TCombobox*Listbox.borderWidth', 0)  
            except Exception:
                pass
            self.configure(bg=COLOR_WIDGET_BG)
            style.configure("TFrame", background=COLOR_WIDGET_BG)
            style.configure("BlackFrame.TFrame", background=COLOR_WIDGET_BG)
            style.configure("TLabelframe", background=COLOR_WIDGET_BG) 
            style.configure("TLabelframe.Label", background=COLOR_WIDGET_BG, foreground=COLOR_HEADER)
            style.configure("RedBold.TLabelframe.Label", foreground=COLOR_RED_SMOOTH, background=COLOR_WIDGET_BG, font=("Arial", 10, "bold"))
            style.configure("Rosso.TSeparator", background="red", thickness=2)   
            style.configure("Treeview", 
                background=COLOR_WIDGET_BG, 
                foreground=COLOR_TEXT, 
                rowheight=25,
                fieldbackground=COLOR_WIDGET_BG, 
                font=("Arial", 10),
                )
            style.configure("Treeview.Heading", 
                background=COLOR_HEADER_BG, 
                foreground=COLOR_HEADER, 
                font=('Arial', 10, 'bold'), 
                relief="flat")
            style.map('Treeview', 
                background=[('selected', COLOR_HIGHLIGHT)], 
                foreground=[('selected', COLOR_WHITE)],
                fieldbackground=[('!disabled', COLOR_WIDGET_BG)]
            )
            style.map('Treeview.Heading', 
                 background=[('active', COLOR_HIGHLIGHT), ('pressed', COLOR_HIGHLIGHT)],
                 foreground=[('active', COLOR_BLACK), ('pressed', COLOR_BLACK)])        
            style.configure("TNotebook", background=COLOR_WIDGET_BG, borderwidth=0)
            style.configure("TNotebook.Tab", 
                            background=COLOR_BUTTON_BG,
                            foreground=COLOR_TEXT,
                            font=('Arial', 10, 'normal'),
                            padding=[6, 2])            
            style.map("TNotebook.Tab",
                      background=[('selected', COLOR_HIGHLIGHT)], 
                      foreground=[('selected', COLOR_WHITE)],
                      expand=[('active', [1, 1, 1, 0])])
            style.configure("Custom.TRadiobutton", background=COLOR_WIDGET_BG, foreground=TEXT_COLOR, font=('Arial', 10))
            style.map("Custom.TRadiobutton",
                  background=[('active', self.COLOR_WIDGET_BG), ('alternate', self.COLOR_WIDGET_BG)],
                  foreground=[('active', self.TEXT_COLOR), ('alternate', self.TEXT_COLOR)])                  
            style.configure('Highlight.TCombobox', 
                fieldbackground=COLOR_WIDGET_BG,
                background=COLOR_BUTTON_BG,
                foreground=COLOR_RED_SMOOTH,
                relief='solid',
                arrowsize=8,
                borderwidth=1)
            style.map('Highlight.TCombobox', 
                arrowcolor=[('!disabled', COLOR_RED_SMOOTH)],
                fieldbackground=[
                    ('readonly', COLOR_WIDGET_BG), 
                    ('focus', COLOR_WIDGET_BG), 
                    ('active', COLOR_WIDGET_BG),
                    ('!disabled', COLOR_WIDGET_BG)
                ],
                foreground=[
                    ('readonly', COLOR_RED_SMOOTH), 
                    ('focus', COLOR_RED_SMOOTH), 
                    ('active', COLOR_RED_SMOOTH),
                    ('!disabled', COLOR_RED_SMOOTH)
                ])          
            style.configure(
                "Custom.TSpinbox",
                fieldbackground=COLOR_WIDGET_BG,
                background=COLOR_BUTTON_BG,
                foreground=COLOR_WHITE,
                arrowcolor=COLOR_HIGHLIGHT,
                borderwidth=1,
                relief="flat",
                selectbackground=COLOR_WIDGET_BG, 
                selectforeground=COLOR_HIGHLIGHT,
                insertcolor=COLOR_HIGHLIGHT
            )
            style.map(
                "Custom.TSpinbox",
                fieldbackground=[("readonly", COLOR_WIDGET_BG), ("focus", COLOR_WIDGET_BG)],
                arrowcolor=[("active", COLOR_WHITE), ("disabled", COLOR_TEXT)],
                background=[("active", COLOR_HIGHLIGHT)],
                selectbackground=[("focus", COLOR_WIDGET_BG)],
                selectforeground=[("focus", COLOR_HIGHLIGHT)]
            )
            style.configure('Border.TCombobox', 
                fieldbackground=COLOR_WIDGET_BG,
                background=COLOR_BUTTON_BG,
                foreground=COLOR_WHITE,
                relief='flat',
                arrowsize=8,
                borderwidth=1)
            style.map('Border.TCombobox', 
                arrowcolor=[('!disabled', COLOR_HIGHLIGHT)],
                fieldbackground=[
                    ('readonly', COLOR_WIDGET_BG), 
                    ('focus', COLOR_WIDGET_BG), 
                    ('active', COLOR_WIDGET_BG),
                    ('!disabled', COLOR_WIDGET_BG)
                ],
                foreground=[
                    ('readonly', COLOR_WHITE), 
                    ('focus', COLOR_WHITE), 
                    ('!disabled', COLOR_WHITE)
                ], selectbackground=[('readonly', COLOR_WIDGET_BG), ('focus', COLOR_WIDGET_BG)],
                selectforeground=[('readonly', TEXT_COLOR), ('focus', TEXT_COLOR)])
            style.configure("TEntry", 
                            fieldbackground=COLOR_WIDGET_BG, 
                            foreground=COLOR_WHITE, 
                            insertcolor=COLOR_WHITE,
                            borderwidth=1, 
                            relief="flat")            
            style.map("TEntry", 
                      fieldbackground=[('focus', COLOR_WIDGET_BG), ('readonly', COLOR_WIDGET_BG)],
                      foreground=[('disabled', COLOR_TEXT)])            
            style.configure("TLabel", background=COLOR_WIDGET_BG, foreground=COLOR_TEXT)         
            style.configure("Timer.TLabel", foreground=COLOR_TEXT, background=self.COLOR_UPDATE, font=("Helvetica", 10, "bold"))
            style.configure("Legend.TLabel", background=COLOR_WIDGET_BG, foreground=COLOR_TEXT, font=("Arial", 10), anchor="w")
            style.configure("White.TLabel", foreground=COLOR_HEADER, background=COLOR_WIDGET_BG, font=("Arial", 11))
            style.configure("WhiteSmall.TLabel", foreground=COLOR_HEADER, background=COLOR_WIDGET_BG, font=("Arial", 10))
            style.configure("Verde.TLabel", foreground=COLOR_GREEN_SMOOTH, background=COLOR_WIDGET_BG, font=("Arial", 10, "bold"), padding=5)
            style.configure("Saldo.TLabel", foreground=COLOR_GREEN_SMOOTH, background=COLOR_WIDGET_BG, font=("Arial", 14, "bold"))
            style.map("Saldo.TLabel", background=[('active', COLOR_WIDGET_BG)], foreground=[('active', COLOR_GREEN_SMOOTH)], relief=[('active', 'flat')])
            style.configure("Doc.TLabel", foreground=COLOR_GREEN_SMOOTH, background=COLOR_WIDGET_BG, font=("Arial", 14, "bold"))
            style.map("Doc.TLabel", background=[('active', COLOR_WIDGET_BG)], foreground=[('active', COLOR_GREEN_SMOOTH)], relief=[('active', 'flat')])        
            style.configure("GSaldo.TLabel", font=("Arial", 10, "bold"), background=COLOR_WIDGET_BG) 
            style.map("GSaldoPositivo.TLabel", foreground=[('active', COLOR_GREEN_SMOOTH), ('!disabled', COLOR_GREEN_SMOOTH)], parent="GSaldo.TLabel")
            style.map("GSaldoNegativo.TLabel", foreground=[('active', COLOR_RED_SMOOTH), ('!disabled', COLOR_RED_SMOOTH)], parent="GSaldo.TLabel")
            style.configure("BlinkAllarme.TLabel", foreground=COLOR_BLINK_OFF, background=COLOR_WIDGET_BG, font=("Arial", 10, "bold"))
            style.map("BlinkAllarme.TLabel", foreground=[('!disabled', COLOR_RED_SMOOTH)], background=[('!disabled', COLOR_WIDGET_BG), ('disabled', COLOR_WIDGET_BG)])            
            SPESSORE_SCROLL = 7
            style.configure("Vertical.TScrollbar", 
                background=COLOR_BUTTON_BG, 
                troughcolor=COLOR_BACKGROUND, 
                arrowcolor=COLOR_HEADER, 
                relief="flat", 
                borderwidth=0,
                arrowsize=SPESSORE_SCROLL,
                width=SPESSORE_SCROLL)
            style.configure("Horizontal.TScrollbar", 
                background=COLOR_BUTTON_BG, 
                troughcolor=COLOR_BACKGROUND, 
                arrowcolor=COLOR_HEADER, 
                relief="flat", 
                borderwidth=0,
                arrowsize=SPESSORE_SCROLL,
                width=SPESSORE_SCROLL)
            style.map("Vertical.TScrollbar", background=[('active', COLOR_HIGHLIGHT)])
            style.map("Horizontal.TScrollbar", background=[('active', COLOR_HIGHLIGHT)])            
            style.configure("TScale", 
                background=COLOR_WIDGET_BG, 
                foreground=COLOR_HIGHLIGHT,
                troughcolor="#E0E0E0",
                sliderthickness=10,
                troughthickness=2,
                sliderlength=15,
                relief='flat')
            style.map("TScale", 
                background=[('active', COLOR_HIGHLIGHT)],
               troughcolor=[('disabled', COLOR_WIDGET_BG)])            
            style.configure("TCheckbutton", background=COLOR_WIDGET_BG, foreground=COLOR_HEADER, font=("Arial", 10))
            style.map("TCheckbutton", background=[('active', COLOR_WIDGET_BG)], foreground=[('active', COLOR_HEADER),('selected', COLOR_HEADER)])            
            style.configure("Tooltip.TLabel", background=COLOR_TOOLTIP, foreground="#FFFFFF", font=("Arial", 9), borderwidth=1, relief="solid", anchor='w', padding=2)            
            style.configure("TButton", relief='flat', borderwidth=0, font=("Arial", 9, "bold"), padding=5, background=COLOR_BUTTON_BG, foreground=COLOR_HEADER) 
            style.map("TButton", background=[("active", "#5E598F")])             
            style.configure("Yellow.TButton", background="#E5C07B", foreground=COLOR_BLACK, font=("Arial", 8, "bold"), width=2)
            style.map("Yellow.TButton", background=[("active", "#CFB076")])
            style.configure("Giallo.TButton", background="#E5C07B", foreground=COLOR_BLACK, font=("Arial", 8, "bold"))
            style.map("Giallo.TButton", background=[("active", "#CFB076")])
            style.configure("Verde.TButton", background=COLOR_GREEN_SMOOTH, foreground=COLOR_BLACK, font=("Arial", 8, "bold"))
            style.map("Verde.TButton", background=[('active', '#8AAB6F')], foreground=[('disabled', COLOR_YELLOW)])
            style.configure("Rosso.TButton", background=COLOR_RED_SMOOTH, foreground=COLOR_BLACK, font=("Arial", 8, "bold"))
            style.map("Rosso.TButton", background=[('active', '#C8606B')], foreground=[('disabled', COLOR_YELLOW)])
            style.configure("Arancio.TButton", background="#D19A66", foreground=COLOR_BLACK, font=("Arial", 8, "bold"))
            style.map("Arancio.TButton", background=[("active", "#C18B5C")])
            style.configure("Blu.TButton", background=COLOR_HIGHLIGHT, foreground=COLOR_BLACK, font=("Arial", 8, "bold"))
            style.map("Blu.TButton", background=[("active", "#509FE2")])
            style.configure("Num.TButton", foreground=COLOR_HEADER, background=COLOR_WIDGET_BG, borderwidth=1, relief="raised", font=("Arial", 8, "bold"), padding=6) 
            style.map("Num.TButton", background=[("active", COLOR_HEADER_BG)]) 
            style.configure("Verde_Low.TButton", background=COLOR_GREEN_SMOOTH, foreground=COLOR_BLACK, font=("Arial", 8, "bold"), padding=(2, 0))
            style.map("Verde_Low.TButton", background=[('active', '#8AAB6F')], foreground=[('disabled', COLOR_YELLOW)])
            style.configure("Yellow_Low.TButton", background="#E5C07B", foreground=COLOR_BLACK, font=("Arial", 8, "bold"), width=2, padding=(2, 0))
            style.map("Yellow_Low.TButton", background=[("active", "#CFB076")])            
            style.configure("Low.Blu.TButton", background=COLOR_HIGHLIGHT, foreground=COLOR_BLACK, font=("Arial", 8, "bold"), padding=(5, 2))
            style.map("Low.Blu.TButton", background=[("active", "#509FE2")])            
            style.configure("GreenOutline.TButton", 
                            foreground=COLOR_GREEN_SMOOTH, 
                            background=COLOR_WIDGET_BG, 
                            borderwidth=1, 
                            relief="solid", 
                            padding=(5, 1), 
                            font=("Arial", 10, "bold")) 
            style.map("GreenOutline.TButton", 
                      background=[("active", "#1B3D1B"), ("pressed", "#142E14")], 
                      bordercolor=[("!disabled", COLOR_GREEN_SMOOTH)], 
                      foreground=[("!disabled", COLOR_GREEN_SMOOTH)])
            style.configure("RedOutline.TButton", 
                            foreground=COLOR_RED_SMOOTH, 
                            background=COLOR_WIDGET_BG, 
                            borderwidth=1, 
                            relief="solid", 
                            padding=(5, 1),
                            cursor="hand2", 
                            font=("Arial", 10, "bold")) 
            style.map("RedOutline.TButton", 
                      background=[("active", "#3D1B1B"), ("pressed", "#2E1414")], 
                      bordercolor=[("!disabled", COLOR_RED_SMOOTH)], 
                      foreground=[("!disabled", COLOR_RED_SMOOTH)])
                      
            style.configure(
                "Backup.Horizontal.TProgressbar",
                troughcolor=self.COLOR_WIDGET_BG,
                background=self.COLOR_HIGHLIGHT,
                thickness=10
            )
            
            style.configure("TProgressbar", thickness=6)
            
            stili_tabella = [
            ("mensile", "#E6FFE6", "#004C00"),
            ("regolare", "#F0FFF0", "#333333"),
            ("bimestrale", "#FFFFE0", "#CC9900"),
            ("trimestrale", "#FFF0E0", "#FF6600"),
            ("irregolare", "#FFEEEE", "#CC0000"),
            ]        
            for alias, bg, fg in stili_tabella:
                style.configure(
                    f"Legenda.{alias}.TLabel", 
                    background=bg, 
                    foreground=fg, 
                    font=("Arial", 8, "bold"),
                    padding=3
                ) 
            self.cal_bg = COLOR_WIDGET_BG
            self.cal_fg = TEXT_COLOR
            self.cal_weekend_bg = COLOR_WIDGET_BG  
            self.cal_weekend_fg = COLOR_HIGHLIGHT
            self.cal_weekday_bg = COLOR_WIDGET_BG  
            self.cal_weekday_fg = COLOR_HEADER
            self.cal_select_bg = COLOR_HIGHLIGHT 
            self.cal_select_fg = COLOR_BLACK     
            self.cal_header_bg = COLOR_WIDGET_BG   
            self.cal_header_fg = COLOR_HEADER
        if THEMA == "BLU":
            style = ttk.Style()
            style.theme_use('default')            
            MENU_BG_DARK = "#B3E5FC"              # Celeste medio (Barra superiore)
            MENU_FG_LIGHT = "#004B8D"             # Blu scuro per contrasto testo
            MENU_BG = "#E1F5FE"                   # Celeste chiarissimo per i sottomenu
            MENU_ACT_BG_COLOR = "#0288D1"         # Blu brillante in selezione
            MENU_ACT_FG_COLOR = "white"           # Bianco su selezione
            COLOR_BACKGROUND = "#B3E5FC"          # SFONDO PRINCIPALE CELESTE
            COLOR_WIDGET_BG = "#B3E5FC"           # Sfondo widget celeste chiaro
            TEXT_COLOR = "#002F6C"                # Testo principale Blu notte
            COLOR_HIGHLIGHT = "#0091EA"           # Blu elettrico per la selezione
            COLOR_TEXT = "#004B8D"                # Testo secondario
            COLOR_HEADER = "#004B8D"              # Testo intestazioni
            COLOR_ORANGE = "orange"               # Arancio standard
            COLOR_RED = "red"                     # Rosso standard
            COLOR_GREEN = "#2ed573"               # Verde standard
            COLOR_RED_SMOOTH = "red"              # Rosso standard
            COLOR_GREEN_SMOOTH = "#2ed573"        # Verde smeraldo brillante
            COLOR_HEADER_BG = "#81D4FA"           # Intestazioni coordinate al celeste
            COLOR_BUTTON_BG = "#E1F5FE"           # Bottoni chiari
            COLOR_BLINK_OFF = "#4FC3F7"           # Colore spento azzurro
            COLOR_UPDATE = "#FFF176"              # Giallo avviso solare
            COLOR_BLACK = "black"                 # Nero standard
            COLOR_YELLOW = "#FBC02D"              # Giallo Ambra (Material Design)
            COLOR_WHITE = "white"                 # Bianco puro
            COLOR_LIGHTGREEN = "#7bed9f"          # Verde menta chiaro
            COLOR_LIGHTCORAL = "#ff6b81"          # Corallo pastello
            COLOR_KHAKI = "khaki"                 # Cachi / Sabbia
            COLOR_TOOLTIP = "#E1F5FE"             # Tooltip coerente col tema
            COLOR_TEXT_TOOLTIP = "#004B8D"        # Testo blu scuro
            self.MENU_BG_DARK = MENU_BG_DARK
            self.MENU_FG_LIGHT = MENU_FG_LIGHT
            self.MENU_BG = MENU_BG   
            self.MENU_ACT_BG_COLOR = MENU_ACT_BG_COLOR
            self.MENU_ACT_FG_COLOR = MENU_ACT_FG_COLOR
            self.COLOR_TOPLEVEL = COLOR_WIDGET_BG
            self.TEXT_COLOR = TEXT_COLOR
            self.COLOR_BACKGROUND = COLOR_BACKGROUND
            self.COLOR_WIDGET_BG = COLOR_WIDGET_BG
            self.COLOR_HIGHLIGHT = COLOR_HIGHLIGHT
            self.COLOR_TEXT = COLOR_TEXT
            self.COLOR_HEADER = COLOR_HEADER
            self.COLOR_ORANGE = COLOR_ORANGE
            self.COLOR_RED = COLOR_RED
            self.COLOR_GREEN = COLOR_GREEN
            self.COLOR_RED_SMOOTH = COLOR_RED_SMOOTH
            self.COLOR_GREEN_SMOOTH = COLOR_GREEN_SMOOTH
            self.COLOR_HEADER_BG = COLOR_HEADER_BG
            self.COLOR_BUTTON_BG = COLOR_BUTTON_BG
            self.COLOR_BLINK_OFF = COLOR_BLINK_OFF
            self.COLOR_UPDATE = COLOR_UPDATE
            self.COLOR_BLACK = COLOR_BLACK
            self.COLOR_YELLOW = COLOR_YELLOW
            self.COLOR_WHITE = COLOR_WHITE     
            self.COLOR_LIGHTGREEN = COLOR_LIGHTGREEN
            self.COLOR_LIGHTCORAL = COLOR_LIGHTCORAL
            self.COLOR_KHAKI = COLOR_KHAKI
            self.COLOR_TOOLTIP = COLOR_TOOLTIP
            self.COLOR_TEXT_TOOLTIP = COLOR_TEXT_TOOLTIP
            try:
                self.option_add('*selectBackground', COLOR_HIGHLIGHT)
                self.option_add('*selectForeground', COLOR_WHITE)
                self.option_add('*Focus.background', COLOR_WIDGET_BG)
                self.option_add('*Focus.relief', 'solid')
                self.option_add('*Focus.borderwidth', 1)
            except Exception:
                pass
            self.configure(bg=COLOR_BACKGROUND)                  
            style.configure("TFrame", background=COLOR_WIDGET_BG)
            style.configure("BlackFrame.TFrame", background=COLOR_WIDGET_BG)
            style.configure("TLabelframe", background=COLOR_WIDGET_BG) 
            style.configure("TLabelframe.Label", background=COLOR_WIDGET_BG, foreground=COLOR_HEADER)
            style.configure("RedBold.TLabelframe.Label", foreground=COLOR_RED_SMOOTH, background=COLOR_WIDGET_BG, font=("Arial", 10, "bold"))
            style.configure("Rosso.TSeparator", background="red", thickness=2)   
            style.configure("Treeview", 
                            background=COLOR_WIDGET_BG, 
                            foreground=COLOR_TEXT, 
                            rowheight=25,
                            fieldbackground=COLOR_WHITE, 
                            font=("Arial", 10),
                            borderwidth=0)
            style.configure("Treeview.Heading", 
                            background="#F2F2F2",
                            foreground=COLOR_HEADER, 
                            font=('Arial', 10, 'bold'), 
                            relief="flat",
                            borderwidth=1) 
            style.map('Treeview', 
                      foreground=[('selected', COLOR_WHITE)], 
                      background=[('selected', COLOR_HIGHLIGHT)],
                      fieldbackground=[('!disabled', COLOR_WIDGET_BG)]
            )
            style.map('Treeview.Heading', 
                foreground=[('active', COLOR_HIGHLIGHT), ('pressed', COLOR_HIGHLIGHT)], 
                background=[('active', "#EAEAEA"), ('pressed', "#DDDDDD")] 
            )
            style.configure("TNotebook", background=COLOR_WIDGET_BG, borderwidth=0)
            style.configure("TNotebook.Tab", 
                            background=COLOR_BACKGROUND,
                            foreground=COLOR_TEXT,
                            font=('Arial', 10, 'normal'),
                            padding=[6, 2])
            style.map("TNotebook.Tab",
                      background=[('selected', COLOR_HIGHLIGHT)], 
                      foreground=[('selected', COLOR_WHITE)],
                      expand=[('active', [1, 1, 1, 0])])
            style.configure("Custom.TRadiobutton", background=COLOR_WIDGET_BG, foreground=TEXT_COLOR, font=('Arial', 10))
            style.map("Custom.TRadiobutton",
                  background=[('active', self.COLOR_WIDGET_BG), ('alternate', self.COLOR_WIDGET_BG)],
                  foreground=[('active', self.TEXT_COLOR), ('alternate', self.TEXT_COLOR)])
            style.configure('Highlight.TCombobox', 
                fieldbackground=COLOR_WHITE, 
                background=COLOR_BUTTON_BG, 
                foreground=COLOR_RED_SMOOTH,
                relief='solid', 
                arrowsize=8, 
                borderwidth=1)
            style.map('Highlight.TCombobox', 
                arrowcolor=[('!disabled', COLOR_RED_SMOOTH)],
                fieldbackground=[
                        ('readonly', COLOR_WHITE), 
                        ('focus', COLOR_WHITE), 
                        ('!disabled', COLOR_WHITE)
                ],
                selectbackground=[
                        ('readonly', COLOR_WHITE), 
                        ('focus', COLOR_WHITE)
                ],
                selectforeground=[
                        ('readonly', COLOR_RED_SMOOTH), 
                        ('focus', COLOR_RED_SMOOTH)
                ])
            style.configure(
                    "Custom.TSpinbox",
                    fieldbackground=COLOR_WHITE,
                    background=COLOR_BUTTON_BG,
                    foreground=TEXT_COLOR,
                    arrowcolor=COLOR_HIGHLIGHT,
                    borderwidth=1,
                    relief="flat",
                    selectbackground=COLOR_WHITE, 
                    selectforeground=TEXT_COLOR,
                    insertcolor=TEXT_COLOR 
            )
            style.map(
                    "Custom.TSpinbox",
                    fieldbackground=[("readonly", COLOR_WHITE), ("focus", COLOR_WHITE)],
                    arrowcolor=[("active", COLOR_HIGHLIGHT), ("disabled", COLOR_TEXT)],
                    background=[("active", "#B3E5FC")],
                    selectbackground=[("focus", COLOR_WHITE)],
                    selectforeground=[("focus", TEXT_COLOR)]
            )
            style.configure('Border.TCombobox', 
                fieldbackground=COLOR_WHITE, 
                background=COLOR_YELLOW, 
                foreground=COLOR_BLACK, 
                relief='flat',
                arrowsize=8,
                borderwidth=1)
            style.map('Border.TCombobox', 
                arrowcolor=[('!disabled', COLOR_HIGHLIGHT)],
                fieldbackground=[
                        ('readonly', COLOR_WHITE), 
                        ('!focus', COLOR_WHITE), 
                        ('focus', COLOR_WHITE),
                        ('!disabled', COLOR_WHITE)
                ],
                selectbackground=[
                        ('readonly', COLOR_WHITE), 
                        ('focus', COLOR_WHITE)
                ],
                selectforeground=[
                        ('readonly', TEXT_COLOR), 
                        ('focus', TEXT_COLOR)
                ])
            style.configure("TEntry", 
                fieldbackground=COLOR_WIDGET_BG, 
                foreground=COLOR_TEXT,
                insertcolor=COLOR_BLACK,
                borderwidth=1, 
                relief="flat")
            style.map("TEntry", 
                fieldbackground=[('focus', COLOR_WIDGET_BG), ('readonly', COLOR_WIDGET_BG)],
                foreground=[('disabled', COLOR_TEXT), ('readonly', COLOR_TEXT)])
            style.configure("TLabel", background=COLOR_WIDGET_BG, foreground=COLOR_TEXT) 
            style.configure("Timer.TLabel", foreground=COLOR_TEXT, background=COLOR_UPDATE, font=("Helvetica", 10, "bold"))
            style.configure("Legend.TLabel", background=COLOR_WIDGET_BG, foreground=COLOR_TEXT, font=("Arial", 10), anchor="w")
            style.configure("White.TLabel", foreground=COLOR_TEXT, background=COLOR_WIDGET_BG, font=("Arial", 11))
            style.configure("WhiteSmall.TLabel", foreground=COLOR_TEXT, background=COLOR_WIDGET_BG, font=("Arial", 10))
            style.configure("Verde.TLabel", foreground=COLOR_GREEN_SMOOTH, background=COLOR_WIDGET_BG, font=("Arial", 10, "bold"), padding=5)
            style.configure("Saldo.TLabel", foreground=COLOR_GREEN_SMOOTH, background=COLOR_WIDGET_BG, font=("Arial", 14, "bold"))
            style.map("Saldo.TLabel", background=[('active', COLOR_WIDGET_BG)], foreground=[('active', COLOR_GREEN_SMOOTH)], relief=[('active', 'flat')])
            style.configure("Doc.TLabel", foreground=COLOR_GREEN_SMOOTH, background=COLOR_WIDGET_BG, font=("Arial", 14, "bold"))
            style.map("Doc.TLabel", background=[('active', COLOR_WIDGET_BG)], foreground=[('active', COLOR_GREEN_SMOOTH)], relief=[('active', 'flat')])
            style.configure("GSaldo.TLabel", font=("Arial", 10, "bold"), background=COLOR_WIDGET_BG) 
            style.map("GSaldoPositivo.TLabel", foreground=[('active', COLOR_GREEN_SMOOTH), ('!disabled', COLOR_GREEN_SMOOTH)], parent="GSaldo.TLabel")
            style.map("GSaldoNegativo.TLabel", foreground=[('active', COLOR_RED_SMOOTH), ('!disabled', COLOR_RED_SMOOTH)], parent="GSaldo.TLabel")
            style.configure("BlinkAllarme.TLabel", foreground=COLOR_BLINK_OFF, background=COLOR_WIDGET_BG, font=("Arial", 10, "bold"))
            style.map("BlinkAllarme.TLabel", foreground=[('!disabled', COLOR_RED_SMOOTH)], background=[('!disabled', COLOR_WIDGET_BG), ('disabled', COLOR_WIDGET_BG)])
            SPESSORE_SCROLL = 7
            style.configure("Vertical.TScrollbar", 
                background="#0288D1", 
                troughcolor="#E1F5FE",
                arrowcolor=COLOR_HEADER,
                borderwidth=0, 
                relief="flat",
                arrowsize=SPESSORE_SCROLL,
                width=SPESSORE_SCROLL)
            style.configure("Horizontal.TScrollbar", 
                background="#0288D1", 
                troughcolor="#E1F5FE",
                arrowcolor=COLOR_HEADER, 
                borderwidth=0, 
                relief="flat",
                arrowsize=SPESSORE_SCROLL,
                width=SPESSORE_SCROLL)
            style.map("Vertical.TScrollbar", background=[('active', COLOR_HIGHLIGHT)])
            style.map("Horizontal.TScrollbar", background=[('active', COLOR_HIGHLIGHT)])
            style.configure("TScale", 
                background=COLOR_WIDGET_BG, 
                foreground=COLOR_HIGHLIGHT,
                troughcolor="#E0E0E0",
                sliderthickness=10,
                troughthickness=2,
                sliderlength=15,
                relief='flat')
            style.map("TScale", 
                background=[('active', COLOR_HIGHLIGHT)],
               troughcolor=[('disabled', COLOR_WIDGET_BG)])
            style.configure("TCheckbutton", background=COLOR_WIDGET_BG, foreground=COLOR_HEADER, font=("Arial", 10))
            style.map("TCheckbutton", background=[('active', COLOR_WIDGET_BG)], foreground=[('active', COLOR_HEADER),('selected', COLOR_HEADER)])
            style.configure("Tooltip.TLabel", background=COLOR_TOOLTIP, foreground=COLOR_BLACK, font=("Arial", 9), borderwidth=1, relief="solid", anchor='w', padding=2)
            style.configure("TButton", relief='flat', borderwidth=0, font=("Arial", 9, "bold"), padding=5, background=COLOR_BUTTON_BG, foreground=COLOR_TEXT) 
            style.map("TButton", background=[("active", "#CCCCCC")])
            style.configure("Yellow.TButton", background=COLOR_YELLOW, foreground=COLOR_BLACK, font=("Arial", 8, "bold"), width=2)
            style.map("Yellow.TButton", background=[("active", "#FFE680")])
            style.configure("Giallo.TButton", background=COLOR_YELLOW, foreground=COLOR_BLACK, font=("Arial", 8, "bold"))
            style.map("Giallo.TButton", background=[("active", "#FFE680")])
            style.configure("Verde.TButton", background=COLOR_GREEN_SMOOTH, foreground=COLOR_BLACK, font=("Arial", 8, "bold"))
            style.map("Verde.TButton", background=[('active', '#8AAB6F')], foreground=[('disabled', COLOR_YELLOW)])
            style.configure("Rosso.TButton", background=COLOR_RED_SMOOTH, foreground=COLOR_BLACK, font=("Arial", 8, "bold"))
            style.map("Rosso.TButton", background=[('active', '#C8606B')], foreground=[('disabled', COLOR_YELLOW)])
            style.configure("Arancio.TButton", background="#FFA500", foreground=COLOR_BLACK, font=("Arial", 8, "bold"))
            style.map("Arancio.TButton", background=[("active", "#FFC766")])
            style.configure("Blu.TButton", background=COLOR_HIGHLIGHT, foreground=COLOR_WHITE, font=("Arial", 8, "bold"))
            style.map("Blu.TButton", background=[("active", "#00AADD")])
            style.configure("Verde_Low.TButton", background=COLOR_GREEN_SMOOTH, foreground=COLOR_BLACK, font=("Arial", 8, "bold"), padding=(2, 0))
            style.map("Verde_Low.TButton", background=[('active', '#8AAB6F')], foreground=[('disabled', COLOR_YELLOW)])
            style.configure("Yellow_Low.TButton", background=COLOR_YELLOW, foreground=COLOR_BLACK, font=("Arial", 8, "bold"), width=2, padding=(2, 0))
            style.map("Yellow_Low.TButton", background=[("active", "#FFE680")])
            style.configure("Low.Blu.TButton", background=COLOR_HIGHLIGHT, foreground=COLOR_WHITE, font=("Arial", 6, "bold"), padding=(4, 1))
            style.map("Low.Blu.TButton", background=[("active", "#00AADD")])
            style.configure("Num.TButton", foreground=COLOR_TEXT, background=COLOR_WIDGET_BG, borderwidth=1, relief="raised", font=("Arial", 8, "bold"), padding=6) 
            style.map("Num.TButton", background=[("active", COLOR_HEADER_BG)]) 
            style.configure("GreenOutline.TButton", foreground=COLOR_GREEN_SMOOTH, background=COLOR_WIDGET_BG, borderwidth=1, relief="solid", padding=(5, 1), font=("Arial", 10, "bold")) 
            style.map("GreenOutline.TButton", 
                      background=[("active", "#E6FFE6"), ("pressed", "#CCFFCC")],
                      bordercolor=[("!disabled", COLOR_GREEN_SMOOTH)], 
                      foreground=[("!disabled", COLOR_GREEN_SMOOTH)])
            style.configure("RedOutline.TButton", foreground=COLOR_RED_SMOOTH, background=COLOR_WIDGET_BG, borderwidth=1, relief="solid", cursor="hand2", padding=(5, 1), font=("Arial", 10, "bold")) 
            style.map("RedOutline.TButton", 
                      background=[("active", "#FFEEEE"), ("pressed", "#FFCCCC")],
                      bordercolor=[("!disabled", COLOR_RED_SMOOTH)], 
                      foreground=[("!disabled", COLOR_RED_SMOOTH)])
            style.configure(
                "Backup.Horizontal.TProgressbar",
                troughcolor=self.COLOR_WIDGET_BG,
                background=self.COLOR_HIGHLIGHT,
                thickness=10
            )
            
            style.configure("TProgressbar", thickness=6)
            
            stili_tabella = [
            ("mensile", "#E6FFE6", "#004C00"),
            ("regolare", "#F0FFF0", "#333333"),
            ("bimestrale", "#FFFFE0", "#CC9900"),
            ("trimestrale", "#FFF0E0", "#FF6600"),
            ("irregolare", "#FFEEEE", "#CC0000"),
            ]
            for alias, bg, fg in stili_tabella:
                style.configure(
                    f"Legenda.{alias}.TLabel", 
                    background=bg, 
                    foreground=fg, 
                    font=("Arial", 8, "bold"),
                    padding=3
                )
            self.cal_bg = COLOR_WIDGET_BG
            self.cal_fg = TEXT_COLOR
            self.cal_weekend_bg = COLOR_WIDGET_BG  
            self.cal_weekend_fg = COLOR_HIGHLIGHT
            self.cal_weekday_bg = COLOR_WIDGET_BG  
            self.cal_weekday_fg = COLOR_HEADER
            self.cal_select_bg = COLOR_HIGHLIGHT 
            self.cal_select_fg = COLOR_BLACK     
            self.cal_header_bg = COLOR_WIDGET_BG   
            self.cal_header_fg = COLOR_HEADER
        if THEMA == "OBSIDIAN":
            style = ttk.Style()
            style.theme_use('default')
            COLOR_BACKGROUND = "#000000"            # Nero assoluto per lo sfondo principale
            COLOR_WIDGET_BG = "#000000"             # Sfondo Widget/Frame
            MENU_BG_DARK = "#000000"                # Sfondo Barra menu superiore
            MENU_FG_LIGHT = "white"                 # Bianco
            MENU_BG = "#0A0A0A"                     # Sfondo dei sottomenu
            MENU_ACT_BG_COLOR = "#509FE2"           # Azzurro Ciano
            MENU_ACT_FG_COLOR = "black"             # Nero
            TEXT_COLOR = "white"                    # Bianco Puro
            COLOR_HIGHLIGHT = "#61AFEF"             # Azzurro Obsidian
            COLOR_TEXT = "#ABB2BF"                  # Grigio Chiaro Freddo
            COLOR_HEADER = "#E0E0E0"                # Grigio Molto Chiaro
            COLOR_ORANGE = "orange"                 # Arancio standard
            COLOR_RED = "red"                       # Rosso puro
            COLOR_GREEN = "green"                   # Verde puro
            COLOR_RED_SMOOTH = "#E06C75"            # Rosso Salmone Soft
            COLOR_GREEN_SMOOTH = "#98C379"          # Verde Oliva Soft
            COLOR_HEADER_BG = "#0A0A0A"             # Sfondo Intestazioni
            COLOR_BUTTON_BG = "#2A2A2A"             # Grigio grafite
            COLOR_BLINK_OFF = COLOR_TEXT
            COLOR_UPDATE = "#FFF176"                # Sfondo Blink
            COLOR_BLACK = "black"                   # Riferimento nero standard
            COLOR_YELLOW = "yellow"                 # Riferimento giallo standard
            COLOR_WHITE = "white"                   # Riferimento bianco standard
            COLOR_LIGHTGREEN = "lightgreen"         # Verde chiaro di sistema
            COLOR_LIGHTCORAL = "lightcoral"         # Rosso chiaro di sistema
            COLOR_KHAKI = "khaki"                   # Tonalità neutra Sabbia
            COLOR_TOOLTIP = "#1A1A1A"               # Grigio Antracite molto scuro
            COLOR_TEXT_TOOLTIP = "white"            # Testo bianco su tooltip
            self.MENU_BG_DARK = MENU_BG_DARK
            self.MENU_FG_LIGHT = MENU_FG_LIGHT
            self.MENU_BG = MENU_BG   
            self.MENU_ACT_BG_COLOR = MENU_ACT_BG_COLOR
            self.MENU_ACT_FG_COLOR = MENU_ACT_FG_COLOR
            self.COLOR_TOPLEVEL = COLOR_WIDGET_BG
            self.TEXT_COLOR = TEXT_COLOR
            self.COLOR_BACKGROUND = COLOR_BACKGROUND
            self.COLOR_WIDGET_BG = COLOR_WIDGET_BG
            self.COLOR_HIGHLIGHT = COLOR_HIGHLIGHT
            self.COLOR_TEXT = COLOR_TEXT
            self.COLOR_HEADER = COLOR_HEADER
            self.COLOR_ORANGE = COLOR_ORANGE
            self.COLOR_RED = COLOR_RED
            self.COLOR_GREEN = COLOR_GREEN
            self.COLOR_RED_SMOOTH = COLOR_RED_SMOOTH
            self.COLOR_GREEN_SMOOTH = COLOR_GREEN_SMOOTH
            self.COLOR_HEADER_BG = COLOR_HEADER_BG
            self.COLOR_BUTTON_BG = COLOR_BUTTON_BG
            self.COLOR_BLINK_OFF = COLOR_BLINK_OFF
            self.COLOR_UPDATE = COLOR_UPDATE
            self.COLOR_BLACK = COLOR_BLACK
            self.COLOR_YELLOW = COLOR_YELLOW
            self.COLOR_WHITE = COLOR_WHITE
            self.COLOR_LIGHTGREEN = COLOR_LIGHTGREEN
            self.COLOR_LIGHTCORAL = COLOR_LIGHTCORAL
            self.COLOR_KHAKI = COLOR_KHAKI
            self.COLOR_TOOLTIP = COLOR_TOOLTIP
            self.COLOR_TEXT_TOOLTIP = COLOR_TEXT_TOOLTIP
            try:
                self.option_add('*selectBackground', COLOR_HIGHLIGHT)
                self.option_add('*selectForeground', COLOR_WHITE)
                self.option_add('*Focus.background', COLOR_WIDGET_BG)
                self.option_add('*Focus.relief', 'solid')
                self.option_add('*Focus.borderwidth', 1)
                self.option_add('*TCombobox*Listbox.background', "#0A0A0A")
                self.option_add('*TCombobox*Listbox.foreground', COLOR_WHITE)
                self.option_add('*TCombobox*Listbox.selectBackground', COLOR_HIGHLIGHT)
                self.option_add('*TCombobox*Listbox.selectForeground', COLOR_BLACK)
                self.option_add('*TCombobox*Listbox.font', ("Arial", 10))
                self.option_add('*TCombobox*Listbox.borderWidth', 0)  
            except Exception:
                pass
                
            self.configure(bg=COLOR_WIDGET_BG)
            style.configure("TFrame", background=COLOR_WIDGET_BG)
            style.configure("BlackFrame.TFrame", background=COLOR_WIDGET_BG)
            style.configure("TLabelframe", background=COLOR_WIDGET_BG) 
            style.configure("TLabelframe.Label", background=COLOR_WIDGET_BG, foreground=COLOR_HEADER)
            style.configure("RedBold.TLabelframe.Label", foreground=COLOR_RED_SMOOTH, background=COLOR_WIDGET_BG, font=("Arial", 10, "bold"))
            style.configure("Rosso.TSeparator", background="red", thickness=2)   
            style.configure("Treeview", 
                background=COLOR_WIDGET_BG, 
                foreground=COLOR_TEXT, 
                rowheight=25,
                fieldbackground=COLOR_WIDGET_BG, 
                font=("Arial", 10),
                )
            style.configure("Treeview.Heading", 
                background=COLOR_HEADER_BG, 
                foreground=COLOR_HEADER, 
                font=('Arial', 10, 'bold'), 
                relief="flat")
            style.map('Treeview', 
                background=[('selected', COLOR_HIGHLIGHT)], 
                foreground=[('selected', COLOR_WHITE)],
                fieldbackground=[('!disabled', COLOR_WIDGET_BG)]
            )
            style.map('Treeview.Heading', 
                 background=[('active', COLOR_HIGHLIGHT), ('pressed', COLOR_HIGHLIGHT)],
                 foreground=[('active', COLOR_BLACK), ('pressed', COLOR_BLACK)])
            style.configure("TNotebook", background=COLOR_WIDGET_BG, borderwidth=0)
            style.configure("TNotebook.Tab", 
                            background=COLOR_BUTTON_BG,
                            foreground=COLOR_TEXT,
                            font=('Arial', 10, 'normal'),
                            padding=[6, 2])
            style.map("TNotebook.Tab",
                      background=[('selected', COLOR_HIGHLIGHT)], 
                      foreground=[('selected', COLOR_WHITE)],
                      expand=[('active', [1, 1, 1, 0])])
            style.configure("Custom.TRadiobutton", background=COLOR_WIDGET_BG, foreground=TEXT_COLOR, font=('Arial', 10))
            style.map("Custom.TRadiobutton",
                  background=[('active', self.COLOR_WIDGET_BG), ('alternate', self.COLOR_WIDGET_BG)],
                  foreground=[('active', self.TEXT_COLOR), ('alternate', self.TEXT_COLOR)])
            style.configure('Highlight.TCombobox', 
                fieldbackground=COLOR_WIDGET_BG,
                background=COLOR_BUTTON_BG,
                foreground=COLOR_RED_SMOOTH,
                relief='solid',
                arrowsize=8,
                borderwidth=1)
            style.map('Highlight.TCombobox', 
                arrowcolor=[('!disabled', COLOR_RED_SMOOTH)],
                fieldbackground=[
                    ('readonly', COLOR_WIDGET_BG), 
                    ('focus', COLOR_WIDGET_BG), 
                    ('active', COLOR_WIDGET_BG),
                    ('!disabled', COLOR_WIDGET_BG)
                ],
                foreground=[
                    ('readonly', COLOR_RED_SMOOTH), 
                    ('focus', COLOR_RED_SMOOTH), 
                    ('active', COLOR_RED_SMOOTH),
                    ('!disabled', COLOR_RED_SMOOTH)
                ])
            style.configure(
                    "Custom.TSpinbox",
                    fieldbackground="#0A0A0A",
                    background=COLOR_BUTTON_BG,
                    foreground=COLOR_WHITE,
                    arrowcolor=COLOR_HIGHLIGHT,
                    borderwidth=1,
                    relief="flat",
                    selectbackground="#0A0A0A", 
                    selectforeground=COLOR_WHITE,
                    insertcolor=COLOR_WHITE 
            )
            style.map(
                    "Custom.TSpinbox",
                    fieldbackground=[("readonly", "#0A0A0A"), ("focus", "#0A0A0A")],
                    selectbackground=[("focus", "#0A0A0A")],
                    selectforeground=[("focus", COLOR_WHITE)]
            )
            style.configure('Border.TCombobox', 
                fieldbackground=COLOR_WIDGET_BG,
                background=COLOR_BUTTON_BG,
                foreground=COLOR_WHITE,
                relief='flat',
                arrowsize=8,
                borderwidth=1)
            style.map('Border.TCombobox', 
                arrowcolor=[('!disabled', COLOR_HIGHLIGHT)],
                fieldbackground=[
                    ('readonly', COLOR_WIDGET_BG), 
                    ('focus', COLOR_WIDGET_BG), 
                    ('active', COLOR_WIDGET_BG),
                    ('!disabled', COLOR_WIDGET_BG)
                ],
                foreground=[
                    ('readonly', COLOR_WHITE), 
                    ('focus', COLOR_WHITE), 
                    ('!disabled', COLOR_WHITE)
                ], selectbackground=[('readonly', COLOR_WIDGET_BG), ('focus', COLOR_WIDGET_BG)],
                selectforeground=[('readonly', TEXT_COLOR), ('focus', TEXT_COLOR)])
            style.configure("TEntry", 
                            fieldbackground="#0A0A0A", 
                            foreground=COLOR_WHITE, 
                            insertcolor=COLOR_WHITE,
                            borderwidth=1, 
                            relief="flat")
            style.map("TEntry", 
                      fieldbackground=[('focus', "#0A0A0A"), ('readonly', "#0A0A0A")],
                      foreground=[('disabled', COLOR_TEXT)])
            style.configure("TLabel", background=COLOR_WIDGET_BG, foreground=COLOR_TEXT) 
            style.configure("Timer.TLabel", foreground=COLOR_TEXT, background=self.COLOR_UPDATE, font=("Helvetica", 10, "bold"))
            style.configure("Legend.TLabel", background=COLOR_WIDGET_BG, foreground=COLOR_TEXT, font=("Arial", 10), anchor="w")
            style.configure("White.TLabel", foreground=COLOR_HEADER, background=COLOR_WIDGET_BG, font=("Arial", 11))
            style.configure("WhiteSmall.TLabel", foreground=COLOR_HEADER, background=COLOR_WIDGET_BG, font=("Arial", 10))
            style.configure("Verde.TLabel", foreground=COLOR_GREEN_SMOOTH, background=COLOR_WIDGET_BG, font=("Arial", 10, "bold"), padding=5)
            style.configure("Saldo.TLabel", foreground=COLOR_GREEN_SMOOTH, background=COLOR_WIDGET_BG, font=("Arial", 14, "bold"))
            style.map("Saldo.TLabel", background=[('active', COLOR_WIDGET_BG)], foreground=[('active', COLOR_GREEN_SMOOTH)], relief=[('active', 'flat')])
            style.configure("Doc.TLabel", foreground=COLOR_GREEN_SMOOTH, background=COLOR_WIDGET_BG, font=("Arial", 14, "bold"))
            style.map("Doc.TLabel", background=[('active', COLOR_WIDGET_BG)], foreground=[('active', COLOR_GREEN_SMOOTH)], relief=[('active', 'flat')])
            style.configure("GSaldo.TLabel", font=("Arial", 10, "bold"), background=COLOR_WIDGET_BG) 
            style.map("GSaldoPositivo.TLabel", foreground=[('active', COLOR_GREEN_SMOOTH), ('!disabled', COLOR_GREEN_SMOOTH)], parent="GSaldo.TLabel")
            style.map("GSaldoNegativo.TLabel", foreground=[('active', COLOR_RED_SMOOTH), ('!disabled', COLOR_RED_SMOOTH)], parent="GSaldo.TLabel")
            style.configure("BlinkAllarme.TLabel", foreground=COLOR_BLINK_OFF, background=COLOR_WIDGET_BG, font=("Arial", 10, "bold"))
            style.map("BlinkAllarme.TLabel", foreground=[('!disabled', COLOR_RED_SMOOTH)], background=[('!disabled', COLOR_WIDGET_BG), ('disabled', COLOR_WIDGET_BG)])
            SPESSORE_SCROLL = 7
            style.configure("Vertical.TScrollbar", 
                background=COLOR_BUTTON_BG, 
                troughcolor=COLOR_BACKGROUND, 
                arrowcolor=COLOR_HEADER, 
                relief="flat", 
                borderwidth=0,
                arrowsize=SPESSORE_SCROLL,
                width=SPESSORE_SCROLL)
            style.configure("Horizontal.TScrollbar", 
                background=COLOR_BUTTON_BG, 
                troughcolor=COLOR_BACKGROUND, 
                arrowcolor=COLOR_HEADER, 
                relief="flat", 
                borderwidth=0,
                arrowsize=SPESSORE_SCROLL,
                width=SPESSORE_SCROLL)
            style.map("Vertical.TScrollbar", background=[('active', COLOR_HIGHLIGHT)])
            style.map("Horizontal.TScrollbar", background=[('active', COLOR_HIGHLIGHT)])
            style.configure("TScale", 
                background=COLOR_WIDGET_BG, 
                foreground=COLOR_HIGHLIGHT,
                troughcolor="#333333",
                sliderthickness=10,
                troughthickness=2,
                sliderlength=15,
                relief='flat')
            style.map("TScale", 
                background=[('active', COLOR_HIGHLIGHT)],
               troughcolor=[('disabled', COLOR_WIDGET_BG)])
            style.configure("TCheckbutton", background=COLOR_WIDGET_BG, foreground=COLOR_HEADER, font=("Arial", 10))
            style.map("TCheckbutton", background=[('active', COLOR_WIDGET_BG)], foreground=[('active', COLOR_HEADER),('selected', COLOR_HEADER)])
            style.configure("Tooltip.TLabel", background=COLOR_TOOLTIP, foreground="#FFFFFF", font=("Arial", 9), borderwidth=1, relief="solid", anchor='w', padding=2)
            style.configure("TButton", relief='flat', borderwidth=0, font=("Arial", 9, "bold"), padding=5, background=COLOR_BUTTON_BG, foreground=COLOR_HEADER) 
            style.map("TButton", background=[("active", "#1E1E1E")]) 
            style.configure("Yellow.TButton", background="#E5C07B", foreground=COLOR_BLACK, font=("Arial", 8, "bold"), width=2)
            style.map("Yellow.TButton", background=[("active", "#CFB076")])
            style.configure("Giallo.TButton", background="#E5C07B", foreground=COLOR_BLACK, font=("Arial", 8, "bold"))
            style.map("Giallo.TButton", background=[("active", "#CFB076")])
            style.configure("Verde.TButton", background=COLOR_GREEN_SMOOTH, foreground=COLOR_BLACK, font=("Arial", 8, "bold"))
            style.map("Verde.TButton", background=[('active', '#8AAB6F')], foreground=[('disabled', COLOR_YELLOW)])
            style.configure("Rosso.TButton", background=COLOR_RED_SMOOTH, foreground=COLOR_BLACK, font=("Arial", 8, "bold"))
            style.map("Rosso.TButton", background=[('active', '#C8606B')], foreground=[('disabled', COLOR_YELLOW)])
            style.configure("Arancio.TButton", background="#D19A66", foreground=COLOR_BLACK, font=("Arial", 8, "bold"))
            style.map("Arancio.TButton", background=[("active", "#C18B5C")])
            style.configure("Blu.TButton", background=COLOR_HIGHLIGHT, foreground=COLOR_BLACK, font=("Arial", 8, "bold"))
            style.map("Blu.TButton", background=[("active", "#509FE2")])
            style.configure("Num.TButton", foreground=COLOR_HEADER, background=COLOR_WIDGET_BG, borderwidth=1, relief="raised", font=("Arial", 8, "bold"), padding=6) 
            style.map("Num.TButton", background=[("active", COLOR_HEADER_BG)]) 
            style.configure("Verde_Low.TButton", background=COLOR_GREEN_SMOOTH, foreground=COLOR_BLACK, font=("Arial", 8, "bold"), padding=(2, 0))
            style.map("Verde_Low.TButton", background=[('active', '#8AAB6F')], foreground=[('disabled', COLOR_YELLOW)])
            style.configure("Yellow_Low.TButton", background="#E5C07B", foreground=COLOR_BLACK, font=("Arial", 8, "bold"), width=2, padding=(2, 0))
            style.map("Yellow_Low.TButton", background=[("active", "#CFB076")])
            style.configure("Low.Blu.TButton", background=COLOR_HIGHLIGHT, foreground=COLOR_BLACK, font=("Arial", 8, "bold"), padding=(5, 2))
            style.map("Low.Blu.TButton", background=[("active", "#509FE2")])
            style.configure("GreenOutline.TButton", 
                            foreground=COLOR_GREEN_SMOOTH, 
                            background=COLOR_WIDGET_BG, 
                            borderwidth=1, 
                            relief="solid", 
                            padding=(5, 1), 
                            font=("Arial", 10, "bold")) 
            style.map("GreenOutline.TButton", 
                      background=[("active", "#1B3D1B"), ("pressed", "#142E14")], 
                      bordercolor=[("!disabled", COLOR_GREEN_SMOOTH)], 
                      foreground=[("!disabled", COLOR_GREEN_SMOOTH)])
            style.configure("RedOutline.TButton", 
                            foreground=COLOR_RED_SMOOTH, 
                            background=COLOR_WIDGET_BG, 
                            borderwidth=1, 
                            relief="solid", 
                            padding=(5, 1),
                            cursor="hand2", 
                            font=("Arial", 10, "bold")) 
            style.map("RedOutline.TButton", 
                      background=[("active", "#3D1B1B"), ("pressed", "#2E1414")], 
                      bordercolor=[("!disabled", COLOR_RED_SMOOTH)], 
                      foreground=[("!disabled", COLOR_RED_SMOOTH)])
            style.configure(
                "Backup.Horizontal.TProgressbar",
                troughcolor=self.COLOR_WIDGET_BG,
                background=self.COLOR_HIGHLIGHT,
                thickness=10
            )
            
            style.configure("TProgressbar", thickness=6)
            
            stili_tabella = [
            ("mensile", "#E6FFE6", "#004C00"),
            ("regolare", "#F0FFF0", "#333333"),
            ("bimestrale", "#FFFFE0", "#CC9900"),
            ("trimestrale", "#FFF0E0", "#FF6600"),
            ("irregolare", "#FFEEEE", "#CC0000"),
            ]
            for alias, bg, fg in stili_tabella:
                style.configure(
                    f"Legenda.{alias}.TLabel", 
                    background=bg, 
                    foreground=fg, 
                    font=("Arial", 8, "bold"),
                    padding=3
                )
            self.cal_bg = COLOR_WIDGET_BG
            self.cal_fg = TEXT_COLOR
            self.cal_weekend_bg = COLOR_WIDGET_BG  
            self.cal_weekend_fg = COLOR_HIGHLIGHT
            self.cal_weekday_bg = COLOR_WIDGET_BG  
            self.cal_weekday_fg = COLOR_HEADER
            self.cal_select_bg = COLOR_HIGHLIGHT 
            self.cal_select_fg = COLOR_BLACK     
            self.cal_header_bg = COLOR_WIDGET_BG   
            self.cal_header_fg = COLOR_HEADER
        if THEMA == "GOLD":
            style = ttk.Style()
            style.theme_use('default')
            COLOR_BACKGROUND = "#0A0800"            # Nero assoluto per lo sfondo principale
            COLOR_WIDGET_BG = "#0D0A00"             # Sfondo Widget/Frame
            MENU_BG_DARK = "#0A0800"                # Sfondo Barra menu superiore
            MENU_FG_LIGHT = "white"                 # Bianco
            MENU_BG = "#0D0A00"                     # Sfondo dei sottomenu
            MENU_ACT_BG_COLOR = "#C9A84C"           # Azzurro Ciano
            MENU_ACT_FG_COLOR = "black"             # Nero
            TEXT_COLOR = "#F5E6C8"                  # Bianco Puro
            COLOR_HIGHLIGHT = "#C9A84C"             # Azzurro Obsidian
            COLOR_TEXT = "#D4B896"                  # Grigio Chiaro Freddo
            COLOR_HEADER = "#FFD700"                # Grigio Molto Chiaro
            COLOR_ORANGE = "orange"                 # Arancio standard
            COLOR_RED = "red"                       # Rosso puro
            COLOR_GREEN = "green"                   # Verde puro
            COLOR_RED_SMOOTH = "#E06C75"            # Rosso Salmone Soft
            COLOR_GREEN_SMOOTH = "#98C379"          # Verde Oliva Soft
            COLOR_HEADER_BG = "#1A1200"             # Sfondo Intestazioni
            COLOR_BUTTON_BG = "#1E1600"             # Grigio grafite
            COLOR_BLINK_OFF = COLOR_TEXT
            COLOR_UPDATE = "#C9A84C"                # Sfondo Blink
            COLOR_BLACK = "black"                   # Riferimento nero standard
            COLOR_YELLOW = "yellow"                 # Riferimento giallo standard
            COLOR_WHITE = "white"                   # Riferimento bianco standard
            COLOR_LIGHTGREEN = "lightgreen"         # Verde chiaro di sistema
            COLOR_LIGHTCORAL = "lightcoral"         # Rosso chiaro di sistema
            COLOR_KHAKI = "khaki"                   # Tonalità neutra Sabbia
            COLOR_TOOLTIP = "#1A1200"               # Grigio Antracite molto scuro
            COLOR_TEXT_TOOLTIP = "white"            # Testo bianco su tooltip
            self.MENU_BG_DARK = MENU_BG_DARK
            self.MENU_FG_LIGHT = MENU_FG_LIGHT
            self.MENU_BG = MENU_BG   
            self.MENU_ACT_BG_COLOR = MENU_ACT_BG_COLOR
            self.MENU_ACT_FG_COLOR = MENU_ACT_FG_COLOR
            self.COLOR_TOPLEVEL = COLOR_WIDGET_BG
            self.TEXT_COLOR = TEXT_COLOR
            self.COLOR_BACKGROUND = COLOR_BACKGROUND
            self.COLOR_WIDGET_BG = COLOR_WIDGET_BG
            self.COLOR_HIGHLIGHT = COLOR_HIGHLIGHT
            self.COLOR_TEXT = COLOR_TEXT
            self.COLOR_HEADER = COLOR_HEADER
            self.COLOR_ORANGE = COLOR_ORANGE
            self.COLOR_RED = COLOR_RED
            self.COLOR_GREEN = COLOR_GREEN
            self.COLOR_RED_SMOOTH = COLOR_RED_SMOOTH
            self.COLOR_GREEN_SMOOTH = COLOR_GREEN_SMOOTH
            self.COLOR_HEADER_BG = COLOR_HEADER_BG
            self.COLOR_BUTTON_BG = COLOR_BUTTON_BG
            self.COLOR_BLINK_OFF = COLOR_BLINK_OFF
            self.COLOR_UPDATE = COLOR_UPDATE
            self.COLOR_BLACK = COLOR_BLACK
            self.COLOR_YELLOW = COLOR_YELLOW
            self.COLOR_WHITE = COLOR_WHITE
            self.COLOR_LIGHTGREEN = COLOR_LIGHTGREEN
            self.COLOR_LIGHTCORAL = COLOR_LIGHTCORAL
            self.COLOR_KHAKI = COLOR_KHAKI
            self.COLOR_TOOLTIP = COLOR_TOOLTIP
            self.COLOR_TEXT_TOOLTIP = COLOR_TEXT_TOOLTIP
            try:
                self.option_add('*selectBackground', COLOR_HIGHLIGHT)
                self.option_add('*selectForeground', COLOR_WHITE)
                self.option_add('*Focus.background', COLOR_WIDGET_BG)
                self.option_add('*Focus.relief', 'solid')
                self.option_add('*Focus.borderwidth', 1)
                self.option_add('*TCombobox*Listbox.background', "#1A1200")
                self.option_add('*TCombobox*Listbox.foreground', COLOR_WHITE)
                self.option_add('*TCombobox*Listbox.selectBackground', COLOR_HIGHLIGHT)
                self.option_add('*TCombobox*Listbox.selectForeground', COLOR_BLACK)
                self.option_add('*TCombobox*Listbox.font', ("Arial", 10))
                self.option_add('*TCombobox*Listbox.borderWidth', 0)  
            except Exception:
                pass
            self.configure(bg=COLOR_WIDGET_BG)
            style.configure("TFrame", background=COLOR_WIDGET_BG)
            style.configure("BlackFrame.TFrame", background=COLOR_WIDGET_BG)
            style.configure("TLabelframe", background=COLOR_WIDGET_BG, bordercolor="#C9A84C", relief="solid") 
            style.configure("TLabelframe.Label", background=COLOR_WIDGET_BG, foreground=COLOR_HEADER)
            style.configure("RedBold.TLabelframe.Label", foreground=COLOR_RED_SMOOTH, background=COLOR_WIDGET_BG, font=("Arial", 10, "bold"))
            style.configure("Rosso.TSeparator", background="red", thickness=2)   
            style.configure("Treeview", 
                background=COLOR_WIDGET_BG, 
                foreground=COLOR_TEXT, 
                rowheight=25,
                fieldbackground=COLOR_WIDGET_BG, 
                font=("Arial", 10),
                )
            style.configure("Treeview.Heading", 
                background=COLOR_HEADER_BG, 
                foreground="#FFD700", 
                font=('Arial', 10, 'bold'), 
                relief="flat")
            style.map('Treeview', 
                background=[('selected', COLOR_HIGHLIGHT)], 
                foreground=[('selected', COLOR_WHITE)],
                fieldbackground=[('!disabled', COLOR_WIDGET_BG)]
            )
            style.map('Treeview.Heading', 
                 background=[('active', COLOR_HIGHLIGHT), ('pressed', COLOR_HIGHLIGHT)],
                 foreground=[('active', COLOR_BLACK), ('pressed', COLOR_BLACK)])
            style.configure("TNotebook", background=COLOR_WIDGET_BG, borderwidth=0)
            style.configure("TNotebook.Tab", 
                            background=COLOR_BUTTON_BG,
                            foreground=COLOR_TEXT,
                            font=('Arial', 10, 'normal'),
                            padding=[6, 2])
            style.map("TNotebook.Tab",
                      background=[('selected', COLOR_HIGHLIGHT)], 
                      foreground=[('selected', COLOR_WHITE)],
                      expand=[('active', [1, 1, 1, 0])])
            style.configure("Custom.TRadiobutton", background=COLOR_WIDGET_BG, foreground=TEXT_COLOR, font=('Arial', 10))
            style.map("Custom.TRadiobutton",
                  background=[('active', self.COLOR_WIDGET_BG), ('alternate', self.COLOR_WIDGET_BG)],
                  foreground=[('active', self.TEXT_COLOR), ('alternate', self.TEXT_COLOR)])
            style.configure('Highlight.TCombobox', 
                fieldbackground=COLOR_WIDGET_BG,
                background=COLOR_BUTTON_BG,
                foreground=COLOR_RED_SMOOTH,
                relief='solid',
                arrowsize=8,
                borderwidth=1)
            style.map('Highlight.TCombobox', 
                arrowcolor=[('!disabled', COLOR_RED_SMOOTH)],
                fieldbackground=[
                    ('readonly', COLOR_WIDGET_BG), 
                    ('focus', COLOR_WIDGET_BG), 
                    ('active', COLOR_WIDGET_BG),
                    ('!disabled', COLOR_WIDGET_BG)
                ],
                foreground=[
                    ('readonly', COLOR_RED_SMOOTH), 
                    ('focus', COLOR_RED_SMOOTH), 
                    ('active', COLOR_RED_SMOOTH),
                    ('!disabled', COLOR_RED_SMOOTH)
                ])
            style.configure(
                    "Custom.TSpinbox",
                    fieldbackground="#0A0A0A",
                    background=COLOR_BUTTON_BG,
                    foreground=COLOR_WHITE,
                    arrowcolor=COLOR_HIGHLIGHT,
                    borderwidth=1,
                    relief="flat",
                    selectbackground="#0A0A0A", 
                    selectforeground=COLOR_WHITE,
                    insertcolor=COLOR_WHITE 
            )
            style.map(
                    "Custom.TSpinbox",
                    fieldbackground=[("readonly", "#0A0A0A"), ("focus", "#0A0A0A")],
                    selectbackground=[("focus", "#0A0A0A")],
                    selectforeground=[("focus", COLOR_WHITE)]
            )
            style.configure('Border.TCombobox', 
                fieldbackground=COLOR_WIDGET_BG,
                background=COLOR_BUTTON_BG,
                foreground=COLOR_WHITE,
                relief='flat',
                arrowsize=8,
                borderwidth=1)
            style.map('Border.TCombobox', 
                arrowcolor=[('!disabled', COLOR_HIGHLIGHT)],
                fieldbackground=[
                    ('readonly', COLOR_WIDGET_BG), 
                    ('focus', COLOR_WIDGET_BG), 
                    ('active', COLOR_WIDGET_BG),
                    ('!disabled', COLOR_WIDGET_BG)
                ],
                foreground=[
                    ('readonly', COLOR_WHITE), 
                    ('focus', COLOR_WHITE), 
                    ('!disabled', COLOR_WHITE)
                ], selectbackground=[('readonly', COLOR_WIDGET_BG), ('focus', COLOR_WIDGET_BG)],
                selectforeground=[('readonly', TEXT_COLOR), ('focus', TEXT_COLOR)])
            style.configure("TEntry", 
                            fieldbackground="#1A1200", 
                            foreground=COLOR_WHITE, 
                            insertcolor=COLOR_WHITE,
                            borderwidth=1, 
                            relief="flat")
            style.map("TEntry", 
                      fieldbackground=[('focus', "#1A1200"), ('readonly', "#1A1200")],
                      foreground=[('disabled', COLOR_TEXT)])
            style.configure("TLabel", background=COLOR_WIDGET_BG, foreground=COLOR_TEXT) 
            style.configure("Timer.TLabel", foreground=COLOR_TEXT, background=self.COLOR_UPDATE, font=("Helvetica", 10, "bold"))
            style.configure("Legend.TLabel", background=COLOR_WIDGET_BG, foreground=COLOR_TEXT, font=("Arial", 10), anchor="w")
            style.configure("White.TLabel", foreground=COLOR_HEADER, background=COLOR_WIDGET_BG, font=("Arial", 11))
            style.configure("WhiteSmall.TLabel", foreground=COLOR_HEADER, background=COLOR_WIDGET_BG, font=("Arial", 10))
            style.configure("Verde.TLabel", foreground=COLOR_GREEN_SMOOTH, background=COLOR_WIDGET_BG, font=("Arial", 10, "bold"), padding=5)
            style.configure("Saldo.TLabel", foreground=COLOR_GREEN_SMOOTH, background=COLOR_WIDGET_BG, font=("Arial", 14, "bold"))
            style.map("Saldo.TLabel", background=[('active', COLOR_WIDGET_BG)], foreground=[('active', COLOR_GREEN_SMOOTH)], relief=[('active', 'flat')])
            style.configure("Doc.TLabel", foreground=COLOR_GREEN_SMOOTH, background=COLOR_WIDGET_BG, font=("Arial", 14, "bold"))
            style.map("Doc.TLabel", background=[('active', COLOR_WIDGET_BG)], foreground=[('active', COLOR_GREEN_SMOOTH)], relief=[('active', 'flat')])
            style.configure("GSaldo.TLabel", font=("Arial", 10, "bold"), background=COLOR_WIDGET_BG) 
            style.map("GSaldoPositivo.TLabel", foreground=[('active', COLOR_GREEN_SMOOTH), ('!disabled', COLOR_GREEN_SMOOTH)], parent="GSaldo.TLabel")
            style.map("GSaldoNegativo.TLabel", foreground=[('active', COLOR_RED_SMOOTH), ('!disabled', COLOR_RED_SMOOTH)], parent="GSaldo.TLabel")
            style.configure("BlinkAllarme.TLabel", foreground=COLOR_BLINK_OFF, background=COLOR_WIDGET_BG, font=("Arial", 10, "bold"))
            style.map("BlinkAllarme.TLabel", foreground=[('!disabled', COLOR_RED_SMOOTH)], background=[('!disabled', COLOR_WIDGET_BG), ('disabled', COLOR_WIDGET_BG)])
            SPESSORE_SCROLL = 7
            style.configure("Vertical.TScrollbar", 
                background=COLOR_BUTTON_BG, 
                troughcolor=COLOR_BACKGROUND, 
                arrowcolor=COLOR_HEADER, 
                relief="flat", 
                borderwidth=0,
                arrowsize=SPESSORE_SCROLL,
                width=SPESSORE_SCROLL)
            style.configure("Horizontal.TScrollbar", 
                background=COLOR_BUTTON_BG, 
                troughcolor=COLOR_BACKGROUND, 
                arrowcolor=COLOR_HEADER, 
                relief="flat", 
                borderwidth=0,
                arrowsize=SPESSORE_SCROLL,
                width=SPESSORE_SCROLL)
            style.map("Vertical.TScrollbar", background=[('active', COLOR_HIGHLIGHT)])
            style.map("Horizontal.TScrollbar", background=[('active', COLOR_HIGHLIGHT)])
            style.configure("TScale", 
                background=COLOR_WIDGET_BG, 
                foreground=COLOR_HIGHLIGHT,
                troughcolor="#333333",
                sliderthickness=10,
                troughthickness=2,
                sliderlength=15,
                relief='flat')
            style.map("TScale", 
                background=[('active', COLOR_HIGHLIGHT)],
               troughcolor=[('disabled', COLOR_WIDGET_BG)])
            style.configure("TCheckbutton", background=COLOR_WIDGET_BG, foreground=COLOR_HEADER, font=("Arial", 10))
            style.map("TCheckbutton", background=[('active', COLOR_WIDGET_BG)], foreground=[('active', COLOR_HEADER),('selected', COLOR_HEADER)])
            style.configure("Tooltip.TLabel", background=COLOR_TOOLTIP, foreground="#FFFFFF", font=("Arial", 9), borderwidth=1, relief="solid", anchor='w', padding=2)
            style.configure("TButton", relief='flat', borderwidth=0, font=("Arial", 9, "bold"), padding=5, background=COLOR_BUTTON_BG, foreground=COLOR_HEADER) 
            style.map("TButton", background=[("active", "#1E1E1E")]) 
            style.configure("Yellow.TButton", background="#E5C07B", foreground=COLOR_BLACK, font=("Arial", 8, "bold"), width=2)
            style.map("Yellow.TButton", background=[("active", "#CFB076")])
            style.configure("Giallo.TButton", background="#E5C07B", foreground=COLOR_BLACK, font=("Arial", 8, "bold"))
            style.map("Giallo.TButton", background=[("active", "#CFB076")])
            style.configure("Verde.TButton", background=COLOR_GREEN_SMOOTH, foreground=COLOR_BLACK, font=("Arial", 8, "bold"))
            style.map("Verde.TButton", background=[('active', '#8AAB6F')], foreground=[('disabled', COLOR_YELLOW)])
            style.configure("Rosso.TButton", background=COLOR_RED_SMOOTH, foreground=COLOR_BLACK, font=("Arial", 8, "bold"))
            style.map("Rosso.TButton", background=[('active', '#C8606B')], foreground=[('disabled', COLOR_YELLOW)])
            style.configure("Arancio.TButton", background="#D19A66", foreground=COLOR_BLACK, font=("Arial", 8, "bold"))
            style.map("Arancio.TButton", background=[("active", "#C18B5C")])
            style.configure("Blu.TButton", background=COLOR_HIGHLIGHT, foreground=COLOR_BLACK, font=("Arial", 8, "bold"))
            style.map("Blu.TButton", background=[("active", "#509FE2")])
            style.configure("Num.TButton", foreground=COLOR_HEADER, background=COLOR_WIDGET_BG, borderwidth=1, relief="raised", font=("Arial", 8, "bold"), padding=6) 
            style.map("Num.TButton", background=[("active", COLOR_HEADER_BG)]) 
            style.configure("Verde_Low.TButton", background=COLOR_GREEN_SMOOTH, foreground=COLOR_BLACK, font=("Arial", 8, "bold"), padding=(2, 0))
            style.map("Verde_Low.TButton", background=[('active', '#8AAB6F')], foreground=[('disabled', COLOR_YELLOW)])
            style.configure("Yellow_Low.TButton", background="#E5C07B", foreground=COLOR_BLACK, font=("Arial", 8, "bold"), width=2, padding=(2, 0))
            style.map("Yellow_Low.TButton", background=[("active", "#CFB076")])
            style.configure("Low.Blu.TButton", background=COLOR_HIGHLIGHT, foreground=COLOR_BLACK, font=("Arial", 8, "bold"), padding=(5, 2))
            style.map("Low.Blu.TButton", background=[("active", "#509FE2")])
            style.configure("GreenOutline.TButton", 
                            foreground=COLOR_GREEN_SMOOTH, 
                            background=COLOR_WIDGET_BG, 
                            borderwidth=1, 
                            relief="solid", 
                            padding=(5, 1), 
                            font=("Arial", 10, "bold")) 
            style.map("GreenOutline.TButton", 
                      background=[("active", "#1B3D1B"), ("pressed", "#142E14")], 
                      bordercolor=[("!disabled", COLOR_GREEN_SMOOTH)], 
                      foreground=[("!disabled", COLOR_GREEN_SMOOTH)])
            style.configure("RedOutline.TButton", 
                            foreground=COLOR_RED_SMOOTH, 
                            background=COLOR_WIDGET_BG, 
                            borderwidth=1, 
                            relief="solid", 
                            padding=(5, 1),
                            cursor="hand2", 
                            font=("Arial", 10, "bold")) 
            style.map("RedOutline.TButton", 
                      background=[("active", "#3D1B1B"), ("pressed", "#2E1414")], 
                      bordercolor=[("!disabled", COLOR_RED_SMOOTH)], 
                      foreground=[("!disabled", COLOR_RED_SMOOTH)])
            style.configure(
                "Backup.Horizontal.TProgressbar",
                troughcolor=self.COLOR_WIDGET_BG,
                background=self.COLOR_HIGHLIGHT,
                thickness=10
            )
            
            style.configure("TProgressbar", thickness=6)
            
            stili_tabella = [
            ("mensile", "#E6FFE6", "#004C00"),
            ("regolare", "#F0FFF0", "#333333"),
            ("bimestrale", "#FFFFE0", "#CC9900"),
            ("trimestrale", "#FFF0E0", "#FF6600"),
            ("irregolare", "#FFEEEE", "#CC0000"),
            ]
            for alias, bg, fg in stili_tabella:
                style.configure(
                    f"Legenda.{alias}.TLabel", 
                    background=bg, 
                    foreground=fg, 
                    font=("Arial", 8, "bold"),
                    padding=3
                )
            self.cal_bg = COLOR_WIDGET_BG
            self.cal_fg = TEXT_COLOR
            self.cal_weekend_bg = COLOR_WIDGET_BG  
            self.cal_weekend_fg = "#FFD700"
            self.cal_weekday_bg = COLOR_WIDGET_BG  
            self.cal_weekday_fg = COLOR_HEADER
            self.cal_select_bg = COLOR_HIGHLIGHT 
            self.cal_select_fg = COLOR_BLACK     
            self.cal_header_bg = COLOR_WIDGET_BG   
            self.cal_header_fg = COLOR_HEADER
