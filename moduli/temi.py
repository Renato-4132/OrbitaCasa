#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from tkinter import ttk

SPESSORE_SCROLL = 7
TEMA_PREDEFINITO = "OBSIDIAN"

TEMI = {
    "CHIARO": {
        "scuro": False,
        "palette": {
            "MENU_BG_DARK": "white",              # Sfondo Barra menu superiore
            "MENU_FG_LIGHT": "black",             # Colore di primo piano chiaro (bianco)
            "MENU_BG": "white",                   # Sfondo dei sottomenu
            "MENU_ACT_BG_COLOR": "#00AADD",       # Colore di evidenziazione
            "MENU_ACT_FG_COLOR": "black",         # Nero
            "COLOR_BACKGROUND": "#FFFFFF",        # Sfondo principale (Bianco Puro)
            "COLOR_WIDGET_BG": "white",           # Sfondo widget leggero (Bianco)
            "TEXT_COLOR": "black",                # Testo nero
            "COLOR_HIGHLIGHT": "#007ACC",         # Blu Windows/VSCode per la selezione
            "COLOR_TEXT": "#333333",              # Testo scuro/nero
            "COLOR_HEADER": "black",              # Testo scuro per le intestazioni
            "COLOR_RED": "red",                   # Rosso standard
            "COLOR_GREEN": "green",               # Verde standard
            "COLOR_ORANGE": "orange",             # Arancio standard
            "COLOR_RED_SMOOTH": "red",            # Rosso standard
            "COLOR_GREEN_SMOOTH": "green",        # Verde standard
            "COLOR_HEADER_BG": "#AAAAAA",         # Grigio medio per sfondo header Treeview
            "COLOR_BUTTON_BG": "#DDDDDD",         # Grigio chiaro per bottoni standard
            "COLOR_BLINK_OFF": "#333333",         # Il colore "spento" è Bianco
            "COLOR_UPDATE": "#FFFFAA",            # Giallo acceso per l'avviso (come richiesto in precedenza)
            "COLOR_BLACK": "black",               # Nero
            "COLOR_YELLOW": "yellow",             # Giallo
            "COLOR_WHITE": "white",               # Bianco
            "COLOR_LIGHTGREEN": "lightgreen",     # LightGreen
            "COLOR_LIGHTCORAL": "lightcoral",     # LightCoral
            "COLOR_KHAKI": "khaki",               # Khaki
            "COLOR_TOOLTIP": "#F9F9F9",           # grigio chiarissimo, quasi bianco.
            "COLOR_TEXT_TOOLTIP": "black",        # nero Testo tooltip.
        },
    },
    "MATERIAL": {
        "scuro": True,
        "palette": {
            "MENU_BG_DARK": "#2A273F",            # Sfondo Barra menu superiore
            "MENU_FG_LIGHT": "white",             # Colore di primo piano chiaro (bianco)
            "MENU_BG": "#4B4673",                 # Sfondo dei sottomenu
            "MENU_ACT_BG_COLOR": "#509FE2",       # Colore di evidenziazione (ciano)
            "MENU_ACT_FG_COLOR": "black",         # Nero
            "COLOR_BACKGROUND": "#20232A",        # Grigio Ardesia Scuro / Quasi Nero (Sfondo Principale)
            "COLOR_WIDGET_BG": "#2A273F",         # Blu Violaceo Scuro (Sfondo per Widget/Frame)
            "TEXT_COLOR": "white",                # Bianco Puro (Testo Primario)
            "COLOR_HIGHLIGHT": "#61AFEF",         # Azzurro Ciano Brillante (Colore di Enfasi/Selezione Attiva)
            "COLOR_TEXT": "#ABB2BF",              # Grigio Chiaro Freddo (Testo Secondario)
            "COLOR_HEADER": "#E0E0E0",            # Grigio Molto Chiaro (Titoli/Intestazioni)
            "COLOR_RED": "red",                   # Rosso
            "COLOR_GREEN": "green",               # Verde
            "COLOR_RED_SMOOTH": "#E06C75",        # Rosso Salmone Tenue (Avvisi, Negativo/Uscite)
            "COLOR_GREEN_SMOOTH": "#98C379",      # Verde Oliva/Salvia (Successo, Positivo/Entrate)
            "COLOR_ORANGE": "orange",             # Arancio standard
            "COLOR_HEADER_BG": "#39355C",         # Viola Scuro Melanzana (Sfondo Intestazioni/Barre Titolo)
            "COLOR_BUTTON_BG": "#4B4673",         # Viola Scuro/Indaco (Sfondo Pulsanti)
            "COLOR_BLINK_OFF": "@COLOR_TEXT",     # Grigio Chiaro Freddo (Stato di Non Lampeggio)
            "COLOR_UPDATE": "#FFFFAA",            # Giallo Molto Chiaro/Crema (Notifiche di Aggiornamento/Blink)
            "COLOR_BLACK": "black",               # Nero (Interni Combobox)
            "COLOR_YELLOW": "yellow",             # Giallo (Pulsante combobox)
            "COLOR_WHITE": "white",               # Bianco (Sfondo combobox)
            "COLOR_LIGHTGREEN": "lightgreen",     # LightGreen
            "COLOR_LIGHTCORAL": "lightcoral",     # LightCoral
            "COLOR_KHAKI": "khaki",               # Khaki
            "COLOR_TOOLTIP": "#4B4673",           # Viola Scuro Desaturato (blu-viola scuro)
            "COLOR_TEXT_TOOLTIP": "white",        # Bianco (Sfondo Tooltip)
        },
    },
    "BLU": {
        "scuro": True,
        "palette": {
            "MENU_BG_DARK": "#08121F",            # Sfondo Barra menu superiore (blu notte)
            "MENU_FG_LIGHT": "white",             # Bianco
            "MENU_BG": "#0B1B30",                 # Sfondo dei sottomenu
            "MENU_ACT_BG_COLOR": "#509FE2",       # Azzurro in selezione
            "MENU_ACT_FG_COLOR": "black",         # Nero su selezione
            "COLOR_BACKGROUND": "#08121F",        # Sfondo principale blu notte
            "COLOR_WIDGET_BG": "#0B1B30",         # Sfondo Widget/Frame/Treeview
            "TEXT_COLOR": "white",                # Bianco Puro
            "COLOR_HIGHLIGHT": "#61AFEF",         # Azzurro (come righe pianificate)
            "COLOR_TEXT": "#B8C7DC",              # Grigio azzurro chiaro
            "COLOR_HEADER": "#E6EEF8",            # Azzurro quasi bianco
            "COLOR_ORANGE": "orange",             # Arancio standard
            "COLOR_RED": "red",                   # Rosso puro
            "COLOR_GREEN": "green",               # Verde puro
            "COLOR_RED_SMOOTH": "#E06C75",        # Rosso Salmone Soft
            "COLOR_GREEN_SMOOTH": "#98C379",      # Verde Oliva Soft
            "COLOR_HEADER_BG": "#16335A",         # Sfondo Intestazioni
            "COLOR_BUTTON_BG": "#1B3A66",         # Blu pulsanti
            "COLOR_BLINK_OFF": "@COLOR_TEXT",
            "COLOR_UPDATE": "#FFF176",            # Sfondo Blink
            "COLOR_BLACK": "black",               # Nero standard
            "COLOR_YELLOW": "yellow",             # Giallo standard
            "COLOR_WHITE": "white",               # Bianco standard
            "COLOR_LIGHTGREEN": "lightgreen",     # Verde chiaro di sistema
            "COLOR_LIGHTCORAL": "lightcoral",     # Rosso chiaro di sistema
            "COLOR_KHAKI": "khaki",               # Cachi / Sabbia
            "COLOR_TOOLTIP": "#16335A",           # Tooltip blu scuro
            "COLOR_TEXT_TOOLTIP": "white",        # Testo bianco su tooltip
        },
    },
    "OBSIDIAN": {
        "scuro": True,
        "palette": {
            "COLOR_BACKGROUND": "#000000",        # Nero assoluto per lo sfondo principale
            "COLOR_WIDGET_BG": "#000000",         # Sfondo Widget/Frame
            "MENU_BG_DARK": "#000000",            # Sfondo Barra menu superiore
            "MENU_FG_LIGHT": "white",             # Bianco
            "MENU_BG": "#0A0A0A",                 # Sfondo dei sottomenu
            "MENU_ACT_BG_COLOR": "#509FE2",       # Azzurro Ciano
            "MENU_ACT_FG_COLOR": "black",         # Nero
            "TEXT_COLOR": "white",                # Bianco Puro
            "COLOR_HIGHLIGHT": "#61AFEF",         # Azzurro Obsidian
            "COLOR_TEXT": "#ABB2BF",              # Grigio Chiaro Freddo
            "COLOR_HEADER": "#E0E0E0",            # Grigio Molto Chiaro
            "COLOR_ORANGE": "orange",             # Arancio standard
            "COLOR_RED": "red",                   # Rosso puro
            "COLOR_GREEN": "green",               # Verde puro
            "COLOR_RED_SMOOTH": "#E06C75",        # Rosso Salmone Soft
            "COLOR_GREEN_SMOOTH": "#98C379",      # Verde Oliva Soft
            "COLOR_HEADER_BG": "#0A0A0A",         # Sfondo Intestazioni
            "COLOR_BUTTON_BG": "#2A2A2A",         # Grigio grafite
            "COLOR_BLINK_OFF": "@COLOR_TEXT",
            "COLOR_UPDATE": "#FFF176",            # Sfondo Blink
            "COLOR_BLACK": "black",               # Riferimento nero standard
            "COLOR_YELLOW": "yellow",             # Riferimento giallo standard
            "COLOR_WHITE": "white",               # Riferimento bianco standard
            "COLOR_LIGHTGREEN": "lightgreen",     # Verde chiaro di sistema
            "COLOR_LIGHTCORAL": "lightcoral",     # Rosso chiaro di sistema
            "COLOR_KHAKI": "khaki",               # Tonalità neutra Sabbia
            "COLOR_TOOLTIP": "#1A1A1A",           # Grigio Antracite molto scuro
            "COLOR_TEXT_TOOLTIP": "white",        # Testo bianco su tooltip
        },
    },
    "GOLD": {
        "scuro": True,
        "palette": {
            "COLOR_BACKGROUND": "#0A0800",        # Nero assoluto per lo sfondo principale
            "COLOR_WIDGET_BG": "#0D0A00",         # Sfondo Widget/Frame
            "MENU_BG_DARK": "#0A0800",            # Sfondo Barra menu superiore
            "MENU_FG_LIGHT": "white",             # Bianco
            "MENU_BG": "#0D0A00",                 # Sfondo dei sottomenu
            "MENU_ACT_BG_COLOR": "#C9A84C",       # Azzurro Ciano
            "MENU_ACT_FG_COLOR": "black",         # Nero
            "TEXT_COLOR": "#F5E6C8",              # Bianco Puro
            "COLOR_HIGHLIGHT": "#C9A84C",         # Azzurro Obsidian
            "COLOR_TEXT": "#D4B896",              # Grigio Chiaro Freddo
            "COLOR_HEADER": "#FFD700",            # Grigio Molto Chiaro
            "COLOR_ORANGE": "orange",             # Arancio standard
            "COLOR_RED": "red",                   # Rosso puro
            "COLOR_GREEN": "green",               # Verde puro
            "COLOR_RED_SMOOTH": "#E06C75",        # Rosso Salmone Soft
            "COLOR_GREEN_SMOOTH": "#98C379",      # Verde Oliva Soft
            "COLOR_HEADER_BG": "#1A1200",         # Sfondo Intestazioni
            "COLOR_BUTTON_BG": "#1E1600",         # Grigio grafite
            "COLOR_BLINK_OFF": "@COLOR_TEXT",
            "COLOR_UPDATE": "#C9A84C",            # Sfondo Blink
            "COLOR_BLACK": "black",               # Riferimento nero standard
            "COLOR_YELLOW": "yellow",             # Riferimento giallo standard
            "COLOR_WHITE": "white",               # Riferimento bianco standard
            "COLOR_LIGHTGREEN": "lightgreen",     # Verde chiaro di sistema
            "COLOR_LIGHTCORAL": "lightcoral",     # Rosso chiaro di sistema
            "COLOR_KHAKI": "khaki",               # Tonalità neutra Sabbia
            "COLOR_TOOLTIP": "#1A1200",           # Grigio Antracite molto scuro
            "COLOR_TEXT_TOOLTIP": "white",        # Testo bianco su tooltip
        },
    },
}

# Stili ttk

STILI_BASE = {
    ("configure", "TFrame"): {"background": "@COLOR_WIDGET_BG"},
    ("configure", "BlackFrame.TFrame"): {"background": "@COLOR_WIDGET_BG"},
    ("configure", "TLabelframe"): {"background": "@COLOR_WIDGET_BG"},
    ("configure", "TLabelframe.Label"): {"background": "@COLOR_WIDGET_BG", "foreground": "@COLOR_HEADER"},
    ("configure", "RedBold.TLabelframe.Label"): {"foreground": "@COLOR_RED_SMOOTH", "background": "@COLOR_WIDGET_BG", "font": ("Arial", 10, "bold")},
    ("configure", "Rosso.TSeparator"): {"background": "red", "thickness": 2},
    ("configure", "Treeview"): {
        "background": "@COLOR_WHITE",
        "foreground": "@COLOR_TEXT",
        "rowheight": 25,
        "fieldbackground": "@COLOR_WHITE",
        "font": ("Arial", 10),
        "borderwidth": 0,
    },
    ("configure", "Treeview.Heading"): {
        "background": "#F2F2F2",
        "foreground": "@COLOR_HEADER",
        "font": ("Arial", 10, "bold"),
        "relief": "flat",
        "borderwidth": 1,
    },
    ("map", "Treeview"): {
        "foreground": [("selected", "@COLOR_WHITE")],
        "background": [("selected", "@COLOR_HIGHLIGHT")],
        "fieldbackground": [("!disabled", "@COLOR_WIDGET_BG")],
    },
    ("map", "Treeview.Heading"): {
        "foreground": [("active", "@COLOR_HIGHLIGHT"), ("pressed", "@COLOR_HIGHLIGHT")],
        "background": [("active", "#EAEAEA"), ("pressed", "#DDDDDD")],
    },
    ("configure", "TNotebook"): {"background": "@COLOR_WIDGET_BG", "borderwidth": 0},
    ("configure", "TNotebook.Tab"): {
        "background": "@COLOR_BACKGROUND",
        "foreground": "@COLOR_TEXT",
        "font": ("Arial", 10, "normal"),
        "padding": [6, 2],
    },
    ("map", "TNotebook.Tab"): {
        "background": [("selected", "@COLOR_HIGHLIGHT")],
        "foreground": [("selected", "@COLOR_WHITE")],
        "expand": [("active", [1, 1, 1, 0])],
    },
    ("configure", "Custom.TRadiobutton"): {"background": "@COLOR_WIDGET_BG", "foreground": "@TEXT_COLOR", "font": ("Arial", 10)},
    ("map", "Custom.TRadiobutton"): {
        "background": [("active", "@COLOR_WIDGET_BG"), ("alternate", "@COLOR_WIDGET_BG")],
        "foreground": [("active", "@TEXT_COLOR"), ("alternate", "@TEXT_COLOR")],
    },
    ("configure", "Highlight.TCombobox"): {
        "fieldbackground": "@COLOR_WIDGET_BG",
        "background": "@COLOR_BUTTON_BG",
        "foreground": "@COLOR_RED_SMOOTH",
        "relief": "solid",
        "arrowsize": 8,
        "borderwidth": 1,
    },
    ("map", "Highlight.TCombobox"): {
        "arrowcolor": [("!disabled", "@COLOR_RED_SMOOTH")],
        "fieldbackground": [
            ("readonly", "@COLOR_WIDGET_BG"),
            ("focus", "@COLOR_WIDGET_BG"),
            ("active", "@COLOR_WIDGET_BG"),
            ("!disabled", "@COLOR_WIDGET_BG"),
        ],
        "foreground": [
            ("readonly", "@COLOR_RED_SMOOTH"),
            ("focus", "@COLOR_RED_SMOOTH"),
            ("active", "@COLOR_RED_SMOOTH"),
            ("!disabled", "@COLOR_RED_SMOOTH"),
        ],
    },
    ("configure", "Custom.TSpinbox"): {
        "fieldbackground": "@COLOR_WHITE",
        "background": "@COLOR_BUTTON_BG",
        "foreground": "@COLOR_BLACK",
        "arrowcolor": "@COLOR_HIGHLIGHT",
        "borderwidth": 1,
        "relief": "solid",
        "insertcolor": "@COLOR_BLACK",
        "selectbackground": "@COLOR_WHITE",
        "selectforeground": "@COLOR_HIGHLIGHT",
    },
    ("map", "Custom.TSpinbox"): {
        "fieldbackground": [("readonly", "@COLOR_WHITE"), ("focus", "@COLOR_WHITE")],
        "arrowcolor": [("active", "@COLOR_BLACK"), ("disabled", "#CCCCCC")],
        "background": [("active", "#EEEEEE")],
        "selectbackground": [("focus", "@COLOR_WHITE")],
        "selectforeground": [("focus", "@COLOR_HIGHLIGHT")],
    },
    ("configure", "Border.TCombobox"): {
        "fieldbackground": "@COLOR_WHITE",
        "background": "@COLOR_YELLOW",
        "foreground": "@COLOR_BLACK",
        "relief": "flat",
        "arrowsize": 8,
        "borderwidth": 1,
    },
    ("map", "Border.TCombobox"): {
        "arrowcolor": [("!disabled", "@COLOR_HIGHLIGHT")],
        "fieldbackground": [("readonly", "@COLOR_WHITE"), ("!focus", "@COLOR_WHITE"), ("!disabled", "@COLOR_WHITE")],
        "foreground": [("readonly", "@TEXT_COLOR"), ("focus", "@TEXT_COLOR"), ("!disabled", "@TEXT_COLOR")],
        "selectbackground": [("readonly", "@COLOR_WIDGET_BG"), ("focus", "@COLOR_WIDGET_BG")],
        "selectforeground": [("readonly", "@TEXT_COLOR"), ("focus", "@TEXT_COLOR")],
    },
    ("configure", "TEntry"): {
        "fieldbackground": "@COLOR_WIDGET_BG",
        "foreground": "@COLOR_TEXT",
        "insertcolor": "@COLOR_BLACK",
        "borderwidth": 1,
        "relief": "flat",
    },
    ("map", "TEntry"): {
        "fieldbackground": [("focus", "@COLOR_WIDGET_BG"), ("readonly", "@COLOR_WIDGET_BG")],
        "foreground": [("disabled", "@COLOR_TEXT"), ("readonly", "@COLOR_TEXT")],
    },
    ("configure", "TLabel"): {"background": "@COLOR_WIDGET_BG", "foreground": "@COLOR_TEXT"},
    ("configure", "Timer.TLabel"): {"foreground": "@COLOR_BLACK", "background": "@COLOR_UPDATE", "font": ("Helvetica", 10, "bold")},
    ("configure", "Legend.TLabel"): {"background": "@COLOR_WIDGET_BG", "foreground": "@COLOR_TEXT", "font": ("Arial", 10), "anchor": "w"},
    ("configure", "White.TLabel"): {"foreground": "@COLOR_TEXT", "background": "@COLOR_WIDGET_BG", "font": ("Arial", 11)},
    ("configure", "WhiteSmall.TLabel"): {"foreground": "@COLOR_TEXT", "background": "@COLOR_WIDGET_BG", "font": ("Arial", 10)},
    ("configure", "Verde.TLabel"): {
        "foreground": "@COLOR_GREEN_SMOOTH",
        "background": "@COLOR_WIDGET_BG",
        "font": ("Arial", 10, "bold"),
        "padding": 5,
    },
    ("configure", "Saldo.TLabel"): {"foreground": "@COLOR_GREEN_SMOOTH", "background": "@COLOR_WIDGET_BG", "font": ("Arial", 14, "bold")},
    ("map", "Saldo.TLabel"): {
        "background": [("active", "@COLOR_WIDGET_BG")],
        "foreground": [("active", "@COLOR_GREEN_SMOOTH")],
        "relief": [("active", "flat")],
    },
    ("configure", "Doc.TLabel"): {"foreground": "@COLOR_GREEN_SMOOTH", "background": "@COLOR_WIDGET_BG", "font": ("Arial", 14, "bold")},
    ("map", "Doc.TLabel"): {
        "background": [("active", "@COLOR_WIDGET_BG")],
        "foreground": [("active", "@COLOR_GREEN_SMOOTH")],
        "relief": [("active", "flat")],
    },
    ("configure", "GSaldo.TLabel"): {"font": ("Arial", 10, "bold"), "background": "@COLOR_WIDGET_BG"},
    ("configure", "GSaldoPositivo.TLabel"): {"font": ("Arial", 10, "bold"), "background": "@COLOR_WIDGET_BG"},
    ("map", "GSaldoPositivo.TLabel"): {"foreground": [("active", "@COLOR_GREEN_SMOOTH"), ("!disabled", "@COLOR_GREEN_SMOOTH")]},
    ("configure", "GSaldoNegativo.TLabel"): {"font": ("Arial", 10, "bold"), "background": "@COLOR_WIDGET_BG"},
    ("map", "GSaldoNegativo.TLabel"): {"foreground": [("active", "@COLOR_RED_SMOOTH"), ("!disabled", "@COLOR_RED_SMOOTH")]},
    ("configure", "BlinkAllarme.TLabel"): {"foreground": "@COLOR_BLINK_OFF", "background": "@COLOR_WIDGET_BG", "font": ("Arial", 10, "bold")},
    ("map", "BlinkAllarme.TLabel"): {
        "foreground": [("!disabled", "@COLOR_RED_SMOOTH")],
        "background": [("!disabled", "@COLOR_WIDGET_BG"), ("disabled", "@COLOR_WIDGET_BG")],
    },
    ("configure", "Vertical.TScrollbar"): {
        "background": "#f5f5f5",
        "troughcolor": "white",
        "arrowcolor": "@COLOR_HEADER",
        "borderwidth": 0,
        "relief": "flat",
        "arrowsize": SPESSORE_SCROLL,
        "width": SPESSORE_SCROLL,
    },
    ("configure", "Horizontal.TScrollbar"): {
        "background": "#f5f5f5",
        "troughcolor": "white",
        "arrowcolor": "@COLOR_HEADER",
        "borderwidth": 0,
        "relief": "flat",
        "arrowsize": SPESSORE_SCROLL,
        "width": SPESSORE_SCROLL,
    },
    ("map", "Vertical.TScrollbar"): {"background": [("active", "@COLOR_HIGHLIGHT")]},
    ("map", "Horizontal.TScrollbar"): {"background": [("active", "@COLOR_HIGHLIGHT")]},
    ("configure", "TScale"): {
        "background": "@COLOR_WIDGET_BG",
        "foreground": "@COLOR_HIGHLIGHT",
        "troughcolor": "#E0E0E0",
        "sliderthickness": 10,
        "troughthickness": 2,
        "sliderlength": 15,
        "relief": "flat",
    },
    ("map", "TScale"): {"background": [("active", "@COLOR_HIGHLIGHT")], "troughcolor": [("disabled", "@COLOR_WIDGET_BG")]},
    ("configure", "TCheckbutton"): {"background": "@COLOR_WIDGET_BG", "foreground": "@COLOR_HEADER", "font": ("Arial", 10)},
    ("map", "TCheckbutton"): {
        "background": [("active", "@COLOR_WIDGET_BG")],
        "foreground": [("active", "@COLOR_HEADER"), ("selected", "@COLOR_HEADER")],
    },
    ("configure", "Tooltip.TLabel"): {
        "background": "@COLOR_TOOLTIP",
        "foreground": "@COLOR_BLACK",
        "font": ("Arial", 9),
        "borderwidth": 1,
        "relief": "solid",
        "anchor": "w",
        "padding": 2,
    },
    ("configure", "TButton"): {
        "relief": "flat",
        "borderwidth": 0,
        "font": ("Arial", 9, "bold"),
        "padding": 5,
        "background": "@COLOR_BUTTON_BG",
        "foreground": "@COLOR_TEXT",
    },
    ("map", "TButton"): {"background": [("active", "#CCCCCC")]},
    ("configure", "Yellow.TButton"): {"background": "@COLOR_YELLOW", "foreground": "@COLOR_BLACK", "font": ("Arial", 8, "bold"), "width": 2},
    ("map", "Yellow.TButton"): {"background": [("active", "#FFE680")]},
    ("configure", "Giallo.TButton"): {"background": "@COLOR_YELLOW", "foreground": "@COLOR_BLACK", "font": ("Arial", 8, "bold")},
    ("map", "Giallo.TButton"): {"background": [("active", "#FFE680")]},
    ("configure", "Verde.TButton"): {"background": "@COLOR_GREEN_SMOOTH", "foreground": "@COLOR_BLACK", "font": ("Arial", 8, "bold")},
    ("map", "Verde.TButton"): {"background": [("active", "#8AAB6F")], "foreground": [("disabled", "@COLOR_YELLOW")]},
    ("configure", "Rosso.TButton"): {"background": "@COLOR_RED_SMOOTH", "foreground": "@COLOR_BLACK", "font": ("Arial", 8, "bold")},
    ("map", "Rosso.TButton"): {"background": [("active", "#C8606B")], "foreground": [("disabled", "@COLOR_YELLOW")]},
    ("configure", "Arancio.TButton"): {"background": "#FFA500", "foreground": "@COLOR_BLACK", "font": ("Arial", 8, "bold")},
    ("map", "Arancio.TButton"): {"background": [("active", "#FFC766")]},
    ("configure", "Blu.TButton"): {"background": "@COLOR_HIGHLIGHT", "foreground": "@COLOR_WHITE", "font": ("Arial", 8, "bold")},
    ("map", "Blu.TButton"): {"background": [("active", "#00AADD")]},
    ("configure", "Verde_Low.TButton"): {
        "background": "@COLOR_GREEN_SMOOTH",
        "foreground": "@COLOR_WHITE",
        "font": ("Arial", 8, "bold"),
        "padding": (2, 0),
    },
    ("map", "Verde_Low.TButton"): {"background": [("active", "#8AAB6F")], "foreground": [("disabled", "@COLOR_YELLOW")]},
    ("configure", "Yellow_Low.TButton"): {
        "background": "@COLOR_YELLOW",
        "foreground": "@COLOR_BLACK",
        "font": ("Arial", 8, "bold"),
        "width": 2,
        "padding": (2, 0),
    },
    ("map", "Yellow_Low.TButton"): {"background": [("active", "#FFE680")]},
    ("configure", "Low.Blu.TButton"): {"background": "@COLOR_HIGHLIGHT", "foreground": "@COLOR_WHITE", "font": ("Arial", 6, "bold"), "padding": (4, 1)},
    ("map", "Low.Blu.TButton"): {"background": [("active", "#00AADD")]},
    ("configure", "Num.TButton"): {
        "foreground": "@COLOR_TEXT",
        "background": "@COLOR_WIDGET_BG",
        "borderwidth": 1,
        "relief": "raised",
        "font": ("Arial", 8, "bold"),
        "padding": 6,
    },
    ("map", "Num.TButton"): {"background": [("active", "@COLOR_HEADER_BG")]},
    ("configure", "GreenOutline.TButton"): {
        "foreground": "@COLOR_GREEN_SMOOTH",
        "background": "@COLOR_WIDGET_BG",
        "borderwidth": 1,
        "relief": "solid",
        "padding": (5, 1),
        "font": ("Arial", 10, "bold"),
    },
    ("map", "GreenOutline.TButton"): {
        "background": [("active", "#E6FFE6"), ("pressed", "#CCFFCC")],
        "bordercolor": [("!disabled", "@COLOR_GREEN_SMOOTH")],
        "foreground": [("!disabled", "@COLOR_GREEN_SMOOTH")],
    },
    ("configure", "RedOutline.TButton"): {
        "foreground": "@COLOR_RED_SMOOTH",
        "background": "@COLOR_WIDGET_BG",
        "borderwidth": 1,
        "relief": "solid",
        "cursor": "hand2",
        "padding": (5, 1),
        "font": ("Arial", 10, "bold"),
    },
    ("map", "RedOutline.TButton"): {
        "background": [("active", "#FFEEEE"), ("pressed", "#FFCCCC")],
        "bordercolor": [("!disabled", "@COLOR_RED_SMOOTH")],
        "foreground": [("!disabled", "@COLOR_RED_SMOOTH")],
    },
    ("configure", "Backup.Horizontal.TProgressbar"): {"troughcolor": "@COLOR_WIDGET_BG", "background": "@COLOR_HIGHLIGHT", "thickness": 10},
    ("configure", "Horizontal.TProgressbar"): {"thickness": 6},
}

STILI_SCURO = {
    ("map", "Treeview"): {
        "foreground": [("selected", "@COLOR_BLACK")],
        "background": [("selected", "@COLOR_HIGHLIGHT")],
        "fieldbackground": [("!disabled", "@COLOR_WIDGET_BG")],
    },
    ("map", "TNotebook.Tab"): {
        "background": [("selected", "@COLOR_HIGHLIGHT")],
        "foreground": [("selected", "@COLOR_BLACK")],
        "expand": [("active", [1, 1, 1, 0])],
    },
    ("configure", "Treeview"): {
        "background": "@COLOR_WIDGET_BG",
        "foreground": "@COLOR_TEXT",
        "rowheight": 25,
        "fieldbackground": "@COLOR_WIDGET_BG",
        "font": ("Arial", 10),
    },
    ("map", "Treeview.Heading"): {
        "background": [("active", "@COLOR_HIGHLIGHT"), ("pressed", "@COLOR_HIGHLIGHT")],
        "foreground": [("active", "@COLOR_BLACK"), ("pressed", "@COLOR_BLACK")],
    },
    ("configure", "TNotebook.Tab"): {
        "background": "@COLOR_BUTTON_BG",
        "foreground": "@COLOR_TEXT",
        "font": ("Arial", 10, "normal"),
        "padding": [6, 2],
    },
    ("configure", "Border.TCombobox"): {
        "fieldbackground": "@COLOR_WIDGET_BG",
        "background": "@COLOR_BUTTON_BG",
        "foreground": "@COLOR_WHITE",
        "relief": "flat",
        "arrowsize": 8,
        "borderwidth": 1,
    },
    ("map", "Border.TCombobox"): {
        "arrowcolor": [("!disabled", "@COLOR_HIGHLIGHT")],
        "fieldbackground": [
            ("readonly", "@COLOR_WIDGET_BG"),
            ("focus", "@COLOR_WIDGET_BG"),
            ("active", "@COLOR_WIDGET_BG"),
            ("!disabled", "@COLOR_WIDGET_BG"),
        ],
        "foreground": [("readonly", "@COLOR_WHITE"), ("focus", "@COLOR_WHITE"), ("!disabled", "@COLOR_WHITE")],
        "selectbackground": [("readonly", "@COLOR_WIDGET_BG"), ("focus", "@COLOR_WIDGET_BG")],
        "selectforeground": [("readonly", "@TEXT_COLOR"), ("focus", "@TEXT_COLOR")],
    },
    ("configure", "White.TLabel"): {"foreground": "@COLOR_HEADER", "background": "@COLOR_WIDGET_BG", "font": ("Arial", 11)},
    ("configure", "WhiteSmall.TLabel"): {"foreground": "@COLOR_HEADER", "background": "@COLOR_WIDGET_BG", "font": ("Arial", 10)},
    ("configure", "Vertical.TScrollbar"): {
        "background": "@COLOR_BUTTON_BG",
        "troughcolor": "@COLOR_BACKGROUND",
        "arrowcolor": "@COLOR_HEADER",
        "relief": "flat",
        "borderwidth": 0,
        "arrowsize": SPESSORE_SCROLL,
        "width": SPESSORE_SCROLL,
    },
    ("configure", "Horizontal.TScrollbar"): {
        "background": "@COLOR_BUTTON_BG",
        "troughcolor": "@COLOR_BACKGROUND",
        "arrowcolor": "@COLOR_HEADER",
        "relief": "flat",
        "borderwidth": 0,
        "arrowsize": SPESSORE_SCROLL,
        "width": SPESSORE_SCROLL,
    },
    ("configure", "Tooltip.TLabel"): {
        "background": "@COLOR_TOOLTIP",
        "foreground": "#FFFFFF",
        "font": ("Arial", 9),
        "borderwidth": 1,
        "relief": "solid",
        "anchor": "w",
        "padding": 2,
    },
    ("configure", "TButton"): {
        "relief": "flat",
        "borderwidth": 0,
        "font": ("Arial", 9, "bold"),
        "padding": 5,
        "background": "@COLOR_BUTTON_BG",
        "foreground": "@COLOR_HEADER",
    },
    ("configure", "Yellow.TButton"): {"background": "#E5C07B", "foreground": "@COLOR_BLACK", "font": ("Arial", 8, "bold"), "width": 2},
    ("map", "Yellow.TButton"): {"background": [("active", "#CFB076")]},
    ("configure", "Giallo.TButton"): {"background": "#E5C07B", "foreground": "@COLOR_BLACK", "font": ("Arial", 8, "bold")},
    ("map", "Giallo.TButton"): {"background": [("active", "#CFB076")]},
    ("configure", "Arancio.TButton"): {"background": "#D19A66", "foreground": "@COLOR_BLACK", "font": ("Arial", 8, "bold")},
    ("map", "Arancio.TButton"): {"background": [("active", "#C18B5C")]},
    ("configure", "Blu.TButton"): {"background": "@COLOR_HIGHLIGHT", "foreground": "@COLOR_BLACK", "font": ("Arial", 8, "bold")},
    ("map", "Blu.TButton"): {"background": [("active", "#509FE2")]},
    ("configure", "Verde_Low.TButton"): {
        "background": "@COLOR_GREEN_SMOOTH",
        "foreground": "@COLOR_BLACK",
        "font": ("Arial", 8, "bold"),
        "padding": (2, 0),
    },
    ("configure", "Yellow_Low.TButton"): {
        "background": "#E5C07B",
        "foreground": "@COLOR_BLACK",
        "font": ("Arial", 8, "bold"),
        "width": 2,
        "padding": (2, 0),
    },
    ("map", "Yellow_Low.TButton"): {"background": [("active", "#CFB076")]},
    ("configure", "Low.Blu.TButton"): {"background": "@COLOR_HIGHLIGHT", "foreground": "@COLOR_BLACK", "font": ("Arial", 8, "bold"), "padding": (5, 2)},
    ("map", "Low.Blu.TButton"): {"background": [("active", "#509FE2")]},
    ("configure", "Num.TButton"): {
        "foreground": "@COLOR_HEADER",
        "background": "@COLOR_WIDGET_BG",
        "borderwidth": 1,
        "relief": "raised",
        "font": ("Arial", 8, "bold"),
        "padding": 6,
    },
    ("map", "GreenOutline.TButton"): {
        "background": [("active", "#1B3D1B"), ("pressed", "#142E14")],
        "bordercolor": [("!disabled", "@COLOR_GREEN_SMOOTH")],
        "foreground": [("!disabled", "@COLOR_GREEN_SMOOTH")],
    },
    ("map", "RedOutline.TButton"): {
        "background": [("active", "#3D1B1B"), ("pressed", "#2E1414")],
        "bordercolor": [("!disabled", "@COLOR_RED_SMOOTH")],
        "foreground": [("!disabled", "@COLOR_RED_SMOOTH")],
    },
}

STILI_TEMA = {
    "MATERIAL": {
        ("configure", "Treeview.Heading"): {
            "background": "@COLOR_HEADER_BG",
            "foreground": "@COLOR_HEADER",
            "font": ("Arial", 10, "bold"),
            "relief": "flat",
        },
        ("configure", "Custom.TSpinbox"): {
            "fieldbackground": "@COLOR_WIDGET_BG",
            "background": "@COLOR_BUTTON_BG",
            "foreground": "@COLOR_WHITE",
            "arrowcolor": "@COLOR_HIGHLIGHT",
            "borderwidth": 1,
            "relief": "flat",
            "selectbackground": "@COLOR_WIDGET_BG",
            "selectforeground": "@COLOR_HIGHLIGHT",
            "insertcolor": "@COLOR_HIGHLIGHT",
        },
        ("map", "Custom.TSpinbox"): {
            "fieldbackground": [("readonly", "@COLOR_WIDGET_BG"), ("focus", "@COLOR_WIDGET_BG")],
            "arrowcolor": [("active", "@COLOR_WHITE"), ("disabled", "@COLOR_TEXT")],
            "background": [("active", "@COLOR_HIGHLIGHT")],
            "selectbackground": [("focus", "@COLOR_WIDGET_BG")],
            "selectforeground": [("focus", "@COLOR_HIGHLIGHT")],
        },
        ("configure", "TEntry"): {
            "fieldbackground": "@COLOR_WIDGET_BG",
            "foreground": "@COLOR_WHITE",
            "insertcolor": "@COLOR_WHITE",
            "borderwidth": 1,
            "relief": "flat",
        },
        ("map", "TEntry"): {
            "fieldbackground": [("focus", "@COLOR_WIDGET_BG"), ("readonly", "@COLOR_WIDGET_BG")],
            "foreground": [("disabled", "@COLOR_TEXT")],
        },
        ("map", "TButton"): {"background": [("active", "#5E598F")]},
    },
    "BLU": {
        ("configure", "Treeview.Heading"): {
            "background": "@COLOR_HEADER_BG",
            "foreground": "@COLOR_HEADER",
            "font": ("Arial", 10, "bold"),
            "relief": "flat",
        },
        ("configure", "Custom.TSpinbox"): {
            "fieldbackground": "@COLOR_BACKGROUND",
            "background": "@COLOR_BUTTON_BG",
            "foreground": "@COLOR_WHITE",
            "arrowcolor": "@COLOR_HIGHLIGHT",
            "borderwidth": 1,
            "relief": "flat",
            "selectbackground": "@COLOR_BACKGROUND",
            "selectforeground": "@COLOR_WHITE",
            "insertcolor": "@COLOR_WHITE",
        },
        ("map", "Custom.TSpinbox"): {
            "fieldbackground": [("readonly", "@COLOR_BACKGROUND"), ("focus", "@COLOR_BACKGROUND")],
            "selectbackground": [("focus", "@COLOR_BACKGROUND")],
            "selectforeground": [("focus", "@COLOR_WHITE")],
        },
        ("configure", "TEntry"): {
            "fieldbackground": "@COLOR_BACKGROUND",
            "foreground": "@COLOR_WHITE",
            "insertcolor": "@COLOR_WHITE",
            "borderwidth": 1,
            "relief": "flat",
        },
        ("map", "TEntry"): {
            "fieldbackground": [("focus", "@COLOR_BACKGROUND"), ("readonly", "@COLOR_BACKGROUND")],
            "foreground": [("disabled", "@COLOR_TEXT")],
        },
        ("configure", "TScale"): {
            "background": "@COLOR_WIDGET_BG",
            "foreground": "@COLOR_HIGHLIGHT",
            "troughcolor": "#24497F",
            "sliderthickness": 10,
            "troughthickness": 2,
            "sliderlength": 15,
            "relief": "flat",
        },
        ("map", "TButton"): {"background": [("active", "#24497F")]},
    },
    "OBSIDIAN": {
        ("configure", "Treeview.Heading"): {
            "background": "@COLOR_HEADER_BG",
            "foreground": "@COLOR_HEADER",
            "font": ("Arial", 10, "bold"),
            "relief": "flat",
        },
        ("configure", "Custom.TSpinbox"): {
            "fieldbackground": "#0A0A0A",
            "background": "@COLOR_BUTTON_BG",
            "foreground": "@COLOR_WHITE",
            "arrowcolor": "@COLOR_HIGHLIGHT",
            "borderwidth": 1,
            "relief": "flat",
            "selectbackground": "#0A0A0A",
            "selectforeground": "@COLOR_WHITE",
            "insertcolor": "@COLOR_WHITE",
        },
        ("map", "Custom.TSpinbox"): {
            "fieldbackground": [("readonly", "#0A0A0A"), ("focus", "#0A0A0A")],
            "selectbackground": [("focus", "#0A0A0A")],
            "selectforeground": [("focus", "@COLOR_WHITE")],
        },
        ("configure", "TEntry"): {
            "fieldbackground": "#0A0A0A",
            "foreground": "@COLOR_WHITE",
            "insertcolor": "@COLOR_WHITE",
            "borderwidth": 1,
            "relief": "flat",
        },
        ("map", "TEntry"): {
            "fieldbackground": [("focus", "#0A0A0A"), ("readonly", "#0A0A0A")],
            "foreground": [("disabled", "@COLOR_TEXT")],
        },
        ("configure", "TScale"): {
            "background": "@COLOR_WIDGET_BG",
            "foreground": "@COLOR_HIGHLIGHT",
            "troughcolor": "#333333",
            "sliderthickness": 10,
            "troughthickness": 2,
            "sliderlength": 15,
            "relief": "flat",
        },
        ("map", "TButton"): {"background": [("active", "#1E1E1E")]},
    },
    "GOLD": {
        ("configure", "TLabelframe"): {"background": "@COLOR_WIDGET_BG", "bordercolor": "#C9A84C", "relief": "solid"},
        ("configure", "Treeview.Heading"): {"background": "@COLOR_HEADER_BG", "foreground": "#FFD700", "font": ("Arial", 10, "bold"), "relief": "flat"},
        ("configure", "Custom.TSpinbox"): {
            "fieldbackground": "#0A0A0A",
            "background": "@COLOR_BUTTON_BG",
            "foreground": "@COLOR_WHITE",
            "arrowcolor": "@COLOR_HIGHLIGHT",
            "borderwidth": 1,
            "relief": "flat",
            "selectbackground": "#0A0A0A",
            "selectforeground": "@COLOR_WHITE",
            "insertcolor": "@COLOR_WHITE",
        },
        ("map", "Custom.TSpinbox"): {
            "fieldbackground": [("readonly", "#0A0A0A"), ("focus", "#0A0A0A")],
            "selectbackground": [("focus", "#0A0A0A")],
            "selectforeground": [("focus", "@COLOR_WHITE")],
        },
        ("configure", "TEntry"): {
            "fieldbackground": "#1A1200",
            "foreground": "@COLOR_WHITE",
            "insertcolor": "@COLOR_WHITE",
            "borderwidth": 1,
            "relief": "flat",
        },
        ("map", "TEntry"): {
            "fieldbackground": [("focus", "#1A1200"), ("readonly", "#1A1200")],
            "foreground": [("disabled", "@COLOR_TEXT")],
        },
        ("configure", "TScale"): {
            "background": "@COLOR_WIDGET_BG",
            "foreground": "@COLOR_HIGHLIGHT",
            "troughcolor": "#333333",
            "sliderthickness": 10,
            "troughthickness": 2,
            "sliderlength": 15,
            "relief": "flat",
        },
        ("map", "TButton"): {"background": [("active", "#1E1E1E")]},
    },
}

# Opzioni Tk (option_add)

OPZIONI_BASE = {
    "*selectBackground": "@COLOR_HIGHLIGHT",
    "*selectForeground": "@COLOR_WHITE",
    "*Focus.background": "@COLOR_WIDGET_BG",
    "*Focus.relief": "solid",
    "*Focus.borderwidth": 1,
    "*TCombobox*Listbox.background": "@COLOR_WIDGET_BG",
    "*TCombobox*Listbox.foreground": "@TEXT_COLOR",
    "*TCombobox*Listbox.selectBackground": "@COLOR_HIGHLIGHT",
    "*TCombobox*Listbox.selectForeground": "@COLOR_WHITE",
}

OPZIONI_SCURO = {
    "*selectForeground": "@COLOR_BLACK",
    "*TCombobox*Listbox.foreground": "@COLOR_WHITE",
    "*TCombobox*Listbox.selectBackground": "@COLOR_HIGHLIGHT",
    "*TCombobox*Listbox.selectForeground": "@COLOR_BLACK",
    "*TCombobox*Listbox.font": ("Arial", 10),
    "*TCombobox*Listbox.borderWidth": 0,
}

OPZIONI_TEMA = {
    "MATERIAL": {
        "*TCombobox*Listbox.background": "@COLOR_WIDGET_BG",
    },
    "BLU": {
    },
    "OBSIDIAN": {
        "*TCombobox*Listbox.background": "#0A0A0A",
    },
    "GOLD": {
        "*TCombobox*Listbox.background": "#1A1200",
    },
}

# Extra: sfondo finestra e colori calendario

EXTRA_BASE = {
    "finestra_bg": "@COLOR_BACKGROUND",
    "cal_bg": "@COLOR_WIDGET_BG",
    "cal_fg": "@TEXT_COLOR",
    "cal_weekend_bg": "@COLOR_WIDGET_BG",
    "cal_weekend_fg": "@COLOR_HIGHLIGHT",
    "cal_weekday_bg": "@COLOR_WIDGET_BG",
    "cal_weekday_fg": "@COLOR_HEADER",
    "cal_select_bg": "@COLOR_HIGHLIGHT",
    "cal_select_fg": "@COLOR_BLACK",
    "cal_header_bg": "@COLOR_WIDGET_BG",
    "cal_header_fg": "@COLOR_HEADER",
}

EXTRA_SCURO = {
    "finestra_bg": "@COLOR_WIDGET_BG",
}

EXTRA_TEMA = {
    "MATERIAL": {
    },
    "BLU": {
    },
    "OBSIDIAN": {
    },
    "GOLD": {
        "cal_weekend_fg": "#FFD700",
    },
}


def _ris(c, v):
    if isinstance(v, str):
        return c[v[1:]] if v.startswith("@") else v
    if isinstance(v, list):
        return [_ris(c, x) for x in v]
    if isinstance(v, tuple):
        return tuple(_ris(c, x) for x in v)
    if isinstance(v, dict):
        return {k: _ris(c, x) for k, x in v.items()}
    return v


def _livelli(base, scuro, tema, nome, e_scuro):
    dati = dict(base)
    if e_scuro:
        dati.update(scuro)
    dati.update(tema.get(nome, {}))
    return dati


def _palette(tema):
    grezza = tema["palette"]

    def risolvi(k, visti=()):
        v = grezza[k]
        if isinstance(v, str) and v.startswith("@"):
            if v[1:] in visti or v[1:] not in grezza:
                raise KeyError(f"Riferimento non valido nella palette: {k} -> {v}")
            return risolvi(v[1:], visti + (k,))
        return v

    return {k: risolvi(k) for k in grezza}


def applica_temi(self, THEMA):
    if THEMA not in TEMI:
        THEMA = TEMA_PREDEFINITO
    tema = TEMI[THEMA]
    e_scuro = tema["scuro"]
    c = _palette(tema)
    self._tema_corrente = THEMA
    style = ttk.Style()
    style.theme_use("default")

    for nome, valore in c.items():
        setattr(self, nome, valore)
    self.COLOR_TOPLEVEL = c["COLOR_WIDGET_BG"]

    opzioni = _livelli(OPZIONI_BASE, OPZIONI_SCURO, OPZIONI_TEMA, THEMA, e_scuro)
    for opzione, valore in opzioni.items():
        self.option_add(opzione, _ris(c, valore))

    extra = _livelli(EXTRA_BASE, EXTRA_SCURO, EXTRA_TEMA, THEMA, e_scuro)
    self.configure(bg=_ris(c, extra.pop("finestra_bg")))

    stili = _livelli(STILI_BASE, STILI_SCURO, STILI_TEMA, THEMA, e_scuro)
    for (azione, nome), opzioni in stili.items():
        getattr(style, azione)(nome, **_ris(c, opzioni))

    stili_tabella = [
        ("mensile", "#E6FFE6", "#004C00"),
        ("regolare", "#F0FFF0", "#333333"),
        ("bimestrale", "#FFFFE0", "#8A6500"),
        ("trimestrale", "#FFF0E0", "#B34700"),
        ("irregolare", "#FFEEEE", "#CC0000"),
    ]
    for alias, bg, fg in stili_tabella:
        style.configure(
            f"Legenda.{alias}.TLabel",
            background=bg,
            foreground=fg,
            font=("Arial", 8, "bold"),
            padding=3,
        )

    for nome, valore in extra.items():
        setattr(self, nome, _ris(c, valore))


# ---------------------------------------------------------------------------
# Cambio tema a caldo (senza riavvio)
# ---------------------------------------------------------------------------
# Ruolo di ogni opzione colore dei widget Tk/ttk: serve a scegliere la voce di
# palette corretta quando lo stesso colore (es. "black") compare in piu' ruoli.
_RUOLO_OPZIONE = {
    "background": "bg", "bg": "bg", "activebackground": "bg", "troughcolor": "bg",
    "fieldbackground": "bg", "disabledbackground": "bg", "readonlybackground": "bg",
    "highlightbackground": "bg",
    "foreground": "fg", "fg": "fg", "activeforeground": "fg", "disabledforeground": "fg",
    "insertbackground": "fg",
    "highlightcolor": "gen", "selectbackground": "gen", "selectforeground": "gen",
    "selectcolor": "gen",
}

_PRIORITA_RUOLO = {
    "bg": ["COLOR_WIDGET_BG", "COLOR_BACKGROUND", "MENU_BG_DARK", "MENU_BG", "COLOR_HEADER_BG",
           "COLOR_BUTTON_BG", "COLOR_TOOLTIP", "COLOR_UPDATE", "MENU_ACT_BG_COLOR", "COLOR_HIGHLIGHT"],
    "fg": ["TEXT_COLOR", "COLOR_TEXT", "COLOR_HEADER", "MENU_FG_LIGHT", "COLOR_TEXT_TOOLTIP",
           "MENU_ACT_FG_COLOR", "COLOR_BLINK_OFF", "COLOR_HIGHLIGHT", "COLOR_RED", "COLOR_GREEN",
           "COLOR_RED_SMOOTH", "COLOR_GREEN_SMOOTH", "COLOR_ORANGE"],
    "gen": ["COLOR_HIGHLIGHT", "COLOR_WIDGET_BG", "TEXT_COLOR", "COLOR_BACKGROUND", "COLOR_BLACK"],
}


def _costruisci_mappe(self, vecchia, nuova):
    cache = {}

    def rgb(col):
        k = str(col).strip().lower()
        if k not in cache:
            try:
                cache[k] = self.winfo_rgb(k)
            except Exception:
                cache[k] = None
        return cache[k]

    mappe = {}
    for ruolo, priorita in _PRIORITA_RUOLO.items():
        ordine = priorita + [k for k in nuova if k not in priorita]
        m = {}
        for chiave in ordine:
            if chiave not in vecchia or chiave not in nuova:
                continue
            r = rgb(vecchia[chiave])
            if r is None or r in m:
                continue
            m[r] = nuova[chiave]
        mappe[ruolo] = m
    return mappe, rgb


def _ricolora_widget(w, mappe, rgb):
    import tkinter as tk

    def mappa(ruolo, valore):
        if not valore:
            return None
        r = rgb(valore)
        if r is None:
            return None
        nuovo = mappe[ruolo].get(r)
        if nuovo and str(nuovo).lower() != str(valore).lower():
            return nuovo
        return None

    try:
        opzioni = w.keys()
    except Exception:
        return
    # Prima si leggono tutti i valori, poi si scrive: cosi' un colore gia' convertito
    # non viene ricontrollato (e riconvertito) da un'altra opzione.
    modifiche = {}
    for opt in opzioni:
        ruolo = _RUOLO_OPZIONE.get(opt)
        if not ruolo or opt in ("bg", "fg"):
            continue
        try:
            nuovo = mappa(ruolo, str(w.cget(opt)))
        except tk.TclError:
            continue
        if nuovo:
            modifiche[opt] = nuovo
    for opt, nuovo in modifiche.items():
        try:
            w.configure(**{opt: nuovo})
        except tk.TclError:
            pass
    # Tag dei Text
    if isinstance(w, tk.Text):
        try:
            for tag in w.tag_names():
                for opt, ruolo in (("foreground", "fg"), ("background", "bg"),
                                   ("selectforeground", "gen"), ("selectbackground", "gen")):
                    try:
                        nuovo = mappa(ruolo, str(w.tag_cget(tag, opt)))
                        if nuovo:
                            w.tag_configure(tag, **{opt: nuovo})
                    except tk.TclError:
                        pass
        except Exception:
            pass
    # Tag delle Treeview
    elif isinstance(w, ttk.Treeview):
        try:
            tags = set()
            pila = list(w.get_children(""))
            while pila:
                it = pila.pop()
                tags.update(w.item(it, "tags") or ())
                pila.extend(w.get_children(it))
            for tag in tags:
                for opt, ruolo in (("foreground", "fg"), ("background", "bg")):
                    try:
                        nuovo = mappa(ruolo, str(w.tag_configure(tag, opt)))
                        if nuovo:
                            w.tag_configure(tag, **{opt: nuovo})
                    except tk.TclError:
                        pass
        except Exception:
            pass


def _ricolora_albero(radice, mappe, rgb):
    # La radice e' gia' stata aggiornata da applica_temi: si parte dai suoi figli
    pila = list(radice.winfo_children())
    while pila:
        w = pila.pop()
        _ricolora_widget(w, mappe, rgb)
        try:
            pila.extend(w.winfo_children())
        except Exception:
            pass


def _riapplica_calendario(self):
    cal = getattr(self, "cal", None)
    if cal is None:
        return
    try:
        cal.configure(
            background=self.cal_header_bg, foreground=self.cal_header_fg,
            headersbackground=self.cal_header_bg, headersforeground=self.cal_header_fg,
            normalbackground=self.cal_bg, normalforeground=self.cal_fg,
            weekendbackground=self.cal_weekend_bg, weekendforeground=self.cal_weekend_fg,
            selectbackground=self.cal_select_bg, selectforeground=self.cal_select_fg,
            bordercolor=self.cal_bg)
    except Exception:
        pass
    try:
        prefisso = cal._style_prefixe
        style = ttk.Style()
        for st in (f"L.{prefisso}.TButton", f"R.{prefisso}.TButton"):
            style.configure(st, arrowcolor=self.cal_weekend_fg, background=self.cal_header_bg,
                            borderwidth=0, relief="flat", focuscolor=self.cal_header_bg)
            style.map(st,
                      arrowcolor=[("active", self.COLOR_RED), ("pressed", self.cal_weekend_fg)],
                      background=[("active", self.cal_header_bg), ("pressed", self.cal_header_bg)],
                      relief=[("active", "flat"), ("pressed", "flat")])
    except Exception:
        pass


def cambia_tema_a_caldo(self, nuovo_tema):
    """Applica un tema a tutta l'interfaccia gia' aperta, senza riavviare."""
    import __main__ as _app
    nuovo_tema = str(nuovo_tema).upper()
    if nuovo_tema not in TEMI:
        nuovo_tema = TEMA_PREDEFINITO
    if getattr(self, "_tema_corrente", None) == nuovo_tema:
        return False
    chiavi = list(_palette(TEMI[nuovo_tema]).keys())
    vecchia = {k: getattr(self, k) for k in chiavi if hasattr(self, k)}
    vecchia_finestra = {k: getattr(self, k) for k in
                        ("cal_bg", "cal_fg", "cal_header_bg", "cal_header_fg") if hasattr(self, k)}
    applica_temi(self, nuovo_tema)
    nuova = {k: getattr(self, k) for k in chiavi}
    # Aggiunge i colori extra (calendario) alla mappa: stessa logica, ruolo bg/fg
    for k, v in vecchia_finestra.items():
        vecchia[f"__{k}"] = v
        nuova[f"__{k}"] = getattr(self, k)
    mappe, rgb = _costruisci_mappe(self, vecchia, nuova)
    _ricolora_albero(self, mappe, rgb)
    _riapplica_calendario(self)
    try:
        _app.THEMA = nuovo_tema
    except Exception:
        pass
    # Ridisegna le parti costruite con colori calcolati al momento del disegno
    try:
        self.update_idletasks()
        self.refresh_gui()
        modo = self.stats_view_mode.get() if hasattr(self, "stats_view_mode") else ""
        if modo == "grafico":
            self.draw_bar_chart()
        elif modo == "grafico_mensile":
            self.draw_mensile_chart()
        elif modo == "grafico_saldo":
            self.draw_saldo_chart()
        elif modo == "proiezione_fondo":
            self.toggle_stats_view("proiezione_fondo")
    except Exception:
        pass
    return True
