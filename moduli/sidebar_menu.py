#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import tkinter as tk
from collections import namedtuple

class MenuPersonalizzato(tk.Frame):
    def __init__(self, master, bg, fg, active_bg, border_color, font=("Arial", 9)):
        super().__init__(master, bg=border_color, bd=0)
        self._master_ref = master
        self._bg = bg
        self._fg = fg
        self._active_bg = active_bg
        self._font = font
        self._accent = border_color
        self._inner = tk.Frame(self, bg=bg, bd=0)
        self._inner.pack(fill="both", expand=True, padx=1, pady=1)

    def add_command(self, label="", image=None, compound="left", command=None, accelerator=""):
        row = tk.Frame(self._inner, bg=self._bg)
        row.pack(fill="x")
        widgets = [row]
        if image:
            l_icona = tk.Label(row, image=image, bg=self._bg)
            l_icona.image = image
            l_icona.pack(side="left", padx=(10, 6), pady=2)
            widgets.append(l_icona)
        l_testo = tk.Label(row, text=label, bg=self._bg, fg=self._fg,
                            font=self._font, anchor="w")
        l_testo.pack(side="left", fill="x", expand=True, pady=2)
        widgets.append(l_testo)
        if accelerator:
            l_acc = tk.Label(row, text=accelerator, bg=self._bg, fg=self._fg,
                              font=self._font)
            l_acc.pack(side="right", padx=(6, 12))
            widgets.append(l_acc)

        def _esegui(event=None, _c=command):
            self.unpost()
            if _c:
                _c()

        def _enter(event=None, _w=widgets):
            for w in _w:
                w.configure(bg=self._active_bg)

        def _leave(event=None, _w=widgets):
            for w in _w:
                w.configure(bg=self._bg)

        for w in widgets:
            w.bind("<Button-1>", _esegui)
            w.bind("<Enter>", _enter)
            w.bind("<Leave>", _leave)

    def add_titolo(self, testo):
        tk.Label(self._inner, text=testo.upper(), bg=self._bg, fg=self._accent,
                 font=(self._font[0], 7, "bold"), anchor="w", padx=10).pack(fill="x", pady=(3, 0))

    def add_separator(self):
        sep = tk.Frame(self._inner, bg=self._fg, height=1)
        sep.pack(fill="x", padx=8, pady=5)

    def post(self, x, y):
        self.update_idletasks()
        altezza = self.winfo_reqheight()
        larghezza = self.winfo_reqwidth()
        root = self._master_ref.winfo_toplevel()
        root_top = root.winfo_rooty()
        root_bottom = root_top + root.winfo_height()
        root_right = root.winfo_rootx() + root.winfo_width()
        if y + altezza > root_bottom:
            y = max(root_top, root_bottom - altezza)
        if x + larghezza > root_right:
            x = max(root.winfo_rootx(), root_right - larghezza)
        rel_x = int(x) - root.winfo_rootx()
        rel_y = int(y) - root.winfo_rooty()
        self.place(x=rel_x, y=rel_y)
        self.lift()

    def unpost(self):
        try:
            self.place_forget()
            self.destroy()
        except Exception:
            pass

Voce = namedtuple("Voce", "label icona metodo cmd alias se")

def V(label, icona, metodo=None, *, cmd=None, alias=(), se=None):
    return Voce(label, icona, metodo, cmd, tuple(alias), se)

def _in_demo(app):
    import __main__ as _app
    return _app.PROFILO_ATTIVO == _app.NOME_PROFILO_DEMO

SEZIONI = [
    ("archivio", "documenti_B", "Archivio", [
        ("Documenti e magazzino", [
            V("Gestione Documenti",             "documenti",    "gestisci_archivi_pdf"),
            V("Gestione Documenti Personali",   "documenti",    "gestisci_documenti_personali"),
            V("Scansiona e salva PDF",          "scansiona",    "scansiona_e_salva"),
            V("StockBox — Magazzino e Scorte",  "documenti",    "magazzino_app", alias=("StockBox",)),
        ]),
        ("Stampa e manuale", [
            V("Stampa",                         "stampa",       "anteprima_e_stampa_txt"),
            V("Apri Manuale",                   "documenti",    "scarica_manuale"),
        ]),
        ("Strumenti", [
            V("Pannello Controllo",             "timer",        "calcola_mancanti"),
            V("Calcolatrice",                   "calcolatrice", "apri_calcolatrice"),
        ]),
    ]),

    ("casa", "utenti_B", "Casa e Vita", [
        ("Casa e veicoli", [
            V("ImmoBil — Gestione Immobili",                    "home",              "immobil"),
            V("CasaCare — Manutenzione e Risparmio Casa",       "auto_manutenzione", "manutenzione_casa"),
            V("AutoPark — Gestione Veicoli",                    "veicoli",           "veicoli", alias=("AutoPark",)),
            V("Gestione Utenze",                                "mobile",            "utenze"),
        ]),
        ("Famiglia e quotidiano", [
            V("Gestione SuperMarket",                           "spesa",             "spesa_supermercato"),
            V("PetCare — Gestione Animali",                     "animali",           "animali", alias=("Pet Care",)),
            V("Piano Dieta",                                    "spesa",             "apri_dieta"),
        ]),
        ("Lavoro", [
            V("MyBusiness",                                     "lavoro",            "apri_studio"),
        ]),
    ]),

    ("agenda", "promemoria_B", "Agenda", [
        ("Contatti e promemoria", [
            V("Rubrica",                        "oggi",         "rubrica_app"),
            V("Promemoria",                     "promemoria",   "gestisci_promemoria"),
            V("GCalendar",                      "calendario",   "launch_qr_svg_generator"),
        ]),
        ("Ricorrenze e scadenze", [
            V("Gestione Ricorrenze",            "descrizione",  "mostra_ricorrenza_popup"),
            V("Lista Ricorrenze",               "descrizione",  "mostra_lista_ricorrenze"),
            V("Controlla Ricorrenti",           "timer",        "controlla_ricorrenti_manual"),
            V("Scadenze Mese",                  "scadenze",     "scadenze_mese"),
            V("Pianifica",                      "timer",        "apri_gestione_spese_pianificate"),
            V("Schedulatore Notifiche",         "timer_sync",   "apri_schedulatore"),
        ]),
    ]),

    ("finanze", "banca_B", "Finanze", [
        ("Patrimonio e prestiti", [
            V("Portafoglio Bancario",           "saldo",         "open_saldo_conto"),
            V("Portafoglio Investimenti",       "lavoro",        "apri_portafoglio"),
            V("Fondo Pensione",                 "badge_maestro", "apri_fondo_pensione"),
            V("Proiezione - Fondo Risparmio",   "ccv",           "apri_fondo_risparmio", alias=("Fondo Risparmio",)),
            V("Calcolo Mutuo/Prestiti",         "banca",         "calcolo_mutuo_prestito"),
        ]),
    ]),

    ("analisi", "report_B", "Analisi", [
        ("Bilanci ed estratti", [
            V("Bilancio Giorno",                "calendario",   "export_giorno_forzato"),
            V("Bilancio Mese",                  "calendario",   "export_month_detail"),
            V("Bilancio Anno",                  "report",       "export_anno_dettagliato"),
            V("Bilancio Storico Totale",        "report",       "export_storico_totale"),
            V("Bilancio Grafico PDF",           "grafico_linea","genera_report_pdf"),
            V("Analisi e Bilanci",              "report",       "popup_scelta_estratto"),
            V("Estratti per Metodo e Conti",    "ccv",          "apri_estratti_metodo"),
            V("Controllo Estratto Conto",       "check",        "apri_controllo_estratto", alias=("Riconciliazione", "Controllo Estratto")),
        ]),
        ("Ricerca e confronti", [
            V("Ricerca Globale",                "search",       "cerca_operazioni"),
            V("Gestione Tag #",                 "filtri",       "apri_gestione_tag"),
            V("Confronta Periodi",              "report",       "open_compare_window"),
            V("FairShare Partecipanti",         "utenti",       "mostra_dare_avere", alias=("FairShare Dare & Avere", "Dare Avere")),
            V("CommunityPool",                  "utenti",       "apri_community_pool", alias=("Community Pool",)),
        ]),
        ("Grafici e andamenti", [
            V("Grafici Interattivi",            "grafico_linea","mostra_analisi_grafici"),
            V("Andamento Risparmio",            "grafico_linea","apri_andamento_risparmio"),
            V("Calcolatore Inflazione",         "calcolatrice", "apri_calcolatore_inflazione"),
        ]),
    ]),

    ("ai", "sparkles_B", "AI", [
        ("Chiedi e analizza", [
            V("Chiedi al Database (Gemini AI)",             "sparkles", "chiedi_ia_database"),
            V("Analisi Andamento Bilancio OpenAI",          "report",   "analizza_andamento_ia", alias=("Analisi Andamento OpenAI",)),
            V("Analisi e Confronto Documenti OpenAI",       "report",   "confronta_bollette_ia", alias=("Confronto Bollette OpenAI", "Confronto Bollette")),
        ]),
        ("Importazione", [
            V("Importa Documento AI (Gemini)",              "documenti","apri_finestra_importa"),
            V("Sincronizza Acquisti Email (Gmail)",         "sync",     "avvia_sincronizzazione"),
            V("Log Importazioni",                           "sync",     "mostra_log_importazioni"),
        ]),
    ]),

    ("categorie", "calendario_B", "Categorie", [
        ("Analisi", [
            V("Analisi Categorie",              "timer",     "analisi_categorie"),
        ]),
        ("Modifica", [
            V("Suggerisci Categorie",           "filtri",    "apri_categorie_suggerite"),
            V("Gestione Categorie",             "filtri",    "mostra_categorie_popup"),
            V("Editor Categorie",               "documenti", "apri_gestione_categorie"),
            V("Editor Categorie Estratti",      "filtri",    "mostra_editor_memoria_categorie", alias=("Editor Memoria Categorie",)),
        ]),
        ("Spostamento", [
            V("Migra Movimenti Categorie",      "filtri",    cmd=lambda s: s.apri_gestione_categorie(tab="sposta")),
        ]),
    ]),

    ("dati", "scadenze_B", "Dati", [
        ("Import / Export", [
            V("Esporta DB Transazioni",         "carica",   "export_db"),
            V("Importa DB Transazioni",         "archivia", "import_db"),
        ]),
        ("Backup", [
            V("Gestisci Backup e Ripristino",   "archivia", "gestisci_backup_popup"),
            V("Esegui Backup Completo Zip",     "archivia", "esegui_backup_zip", alias=("Backup Completo Zip",)),
        ]),
        ("Pulizia", [
            V("Reset Database",                 "reset",    "show_reset_dialog", alias=("Reset DB",)),
            V("Cancella Voci Bulk",             "delete",   "apri_cancella_spese_treeview_unica"),
        ]),
    ]),

    ("sistema", "tools_B", "Sistema", [
        ("Impostazioni", [
            V("Impostazioni App",               "filtri",        "gestisci_configurazione"),
            V("Personalizza Icone",             "tools",         "apri_personalizza_icone"),
            V("Gamification",                   "badge_novizio", "mostra_dettaglio_gamification"),
        ]),
        ("Account e licenza", [
            V("Gestisci Profili Utenti",        "api_key",  "mostra_selettore_profilo"),
            V("Esci da Modalità Demo",          "reset",    "esci_modalita_demo",  alias=("Modalità Demo",), se=lambda s: _in_demo(s)),
            V("Attiva Modalità Demo",           "sync",     "attiva_modalita_demo", alias=("Modalità Demo",), se=lambda s: not _in_demo(s)),
            V("Cambia Password",                "api_key",  "apri_cambio_password"),
            V("Registra Prodotto",              "api_key",  "apri_registrazione"),
        ]),
        ("Finestra", [
            V("Riduci a Icona",                 "iconizza", "iconify"),
            V("Salva ed Esci",                  "chiudi",   "_on_close"),
        ]),
    ]),

    ("manutenzione", "timer_B", "Manutenzione", [
        ("Aggiornamenti software", [
            V("Controlla Aggiornamento Software",   "sync",        "forza_check_aggiornamento_con_api", alias=("Controlla Aggiornamenti",)),
            V("Forza Aggiornamento Software",       "sync",        "forza_aggiorna"),
            V("Annulla Ultimo Aggiornamento",       "reset",       "ripristina_da_backup"),
            V("Visualizza Storico Aggiornamenti",   "descrizione", "visualizza_changelog"),
        ]),
        ("Diagnostica", [
            V("Storico Anomalie",               "scadenze", "mostra_registro_errori"),
            V("Log Accessi",                    "scadenze", "mostra_log_accessi", alias=("Log Accessi Web",)),
        ]),
        ("Librerie e moduli", [
            V("Aggiorna Librerie Python",       "sync",     "aggiorna_librerie_pip"),
            V("Verifica Moduli (GitHub)",       "sync",     "verifica_moduli_git"),
        ]),
        ("Supporto", [
            V("Contatta Assistenza",            "help",     cmd=lambda s: s.apri_pannello_topic(s.topic_unico)),
        ]),
    ]),

    ("webui", "qr_B", "WebUI", [
        ("Interfaccia", [
            V("Visualizza Interfaccia Web Locale",      "google",  "apri_webserver", alias=("Interfaccia Web Locale",)),
            V("QRcode Connessioni Gateway Remoti",      "qr_code", "mostra_qr_popup_label", alias=("QR Code Connessioni",)),
        ]),
        ("Certificati SSL", [
            V("Gestisci Certificati SSL",       "google",  "gestisci_certificati", alias=("Certificati SSL",)),
            V("Manuale CertBot SSL",            "info",    "scarica_manuale_ssl"),
        ]),
    ]),
]

SEZIONI_PER_CHIAVE = {s[0]: s for s in SEZIONI}

PAD_VOCE = 9
PAD_MIN = 0
ALTEZZA_ICONA = 20

def _voci_attive(self, sezione):
    gruppi = []
    for titolo, voci in sezione[3]:
        ok = [v for v in voci if v.se is None or v.se(self)]
        if ok:
            gruppi.append((titolo, ok))
    return gruppi

def _comando_voce(self, v):
    if v.cmd:
        return lambda c=v.cmd: c(self)
    try:
        return getattr(self, v.metodo)
    except AttributeError:
        return lambda n=v.metodo: print(f"[MENU] metodo non trovato: {n}")

def _tutte_le_voci(self):
    out = []
    for sez in SEZIONI:
        for _titolo, voci in _voci_attive(self, sez):
            for v in voci:
                testo = " | ".join((v.label,) + v.alias).lower()
                out.append((v, testo))
    return out

def _trova_voci(self, testo, limite=10):
    testo = testo.strip().lower()
    if not testo:
        return []
    trovate = []
    for v, hay in _tutte_le_voci(self):
        if testo not in hay:
            continue
        lab = v.label.lower()
        rango = 0 if lab == testo else (1 if lab.startswith(testo) else 2)
        trovate.append((rango, v))
    trovate.sort(key=lambda t: t[0])
    return [(v.label, _comando_voce(self, v), v.icona) for _r, v in trovate[:limite]]

def _costruisci_menu(self, chiave):
    sezione = SEZIONI_PER_CHIAVE[chiave]
    m = MenuPersonalizzato(
        self, bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT,
        active_bg=self.MENU_ACT_BG_COLOR, border_color=self.COLOR_HIGHLIGHT,
        font=("Arial", 9)
    )
    primo = True
    for titolo, voci in _voci_attive(self, sezione):
        if not primo:
            m.add_separator()
        primo = False
        m.add_titolo(titolo)
        for v in voci:
            self._add_m_item(m, v.label, v.icona, _comando_voce(self, v))
    return m

def _apri_sezione(self, chiave):
    riga = getattr(self, "_righe_sezioni", {}).get(chiave)
    try:
        y = riga.winfo_rooty() - self.sidebar.winfo_rooty()
    except Exception:
        y = 50
    self._mostra_popup(_costruisci_menu(self, chiave), y)

def _carica_icona_scintille(self, size=(20, 20), nome="scintille_B", alpha=1.0):
    import os
    import __main__ as _app
    from PIL import Image, ImageTk
    p = os.path.join(_app.DB_DIR, "resources", f"{nome}.png")
    if not os.path.exists(p):
        return None
    try:
        img = Image.open(p).convert("RGBA").resize(size, Image.LANCZOS)
        if alpha < 1.0:
            img.putalpha(img.getchannel("A").point(lambda a: int(a * alpha)))
        return ImageTk.PhotoImage(img)
    except Exception:
        return None

def toggle_sidebar(self):
    if not self.sidebar_espansa:
        self.espandi_sidebar()
        self.btn_toggle.configure(text="◀")
        self.sidebar_espansa = True
    else:
        self.contrai_sidebar_manuale()
        self.btn_toggle.configure(text="➤")
        self.sidebar_espansa = False
        
def contrai_sidebar_manuale(self):
    self.sidebar.place_configure(width=45)
    self.sidebar_espansa = False
    if hasattr(self, 'lbl_logo_testo'):
        self.lbl_logo_testo.pack_forget()
    if hasattr(self, '_search_entry'):
        self._search_entry.pack_forget()
    if hasattr(self, '_search_results_frame'):
        self._search_results_frame.pack_forget()
        for w in self._search_results_frame.winfo_children():
            w.destroy()

def _chiudi_overlay_ricerca(self):
    ov = getattr(self, "_search_overlay", None)
    if ov is not None:
        try:
            if ov.winfo_exists():
                ov.place_forget()
                ov.destroy()
        except Exception:
            pass
    self._search_overlay = None

def _pulisci_ricerca(self):
    _chiudi_overlay_ricerca(self)
    try:
        if self._search_var.get():
            self._search_var.set("")
    except Exception:
        pass

def _esc_ricerca(self):
    _pulisci_ricerca(self)
    if getattr(self, "sidebar_espansa", False):
        self.contrai_sidebar_manuale()
        self.btn_toggle.configure(text="➤")
        self.sidebar_espansa = False

def _click_fuori_ricerca(self, event):
    w = str(event.widget)
    ov = getattr(self, "_search_overlay", None)
    try:
        if ov is not None and w.startswith(str(ov)):
            return
        if w.startswith(str(self.sidebar)):
            return
    except Exception:
        return
    if getattr(self, "sidebar_espansa", False):
        _esc_ricerca(self)
    elif ov is not None or self._search_var.get():
        _pulisci_ricerca(self)

def _pad_corrente(self):
    return getattr(self, "_pad_voce", PAD_VOCE)

def _crea_voce_sidebar(self, icon_key, testo, comando, icon_fallback="•", basso=False):
    f = tk.Frame(self.sidebar, bg=self.MENU_BG_DARK, cursor="hand2")
    f.pack(fill="x", side="bottom" if basso else "top")
    img = self.icone_gui.get(icon_key)
    l_icona = tk.Label(f, bg=self.MENU_BG_DARK)
    if img:
        l_icona.configure(image=img)
        l_icona.image = img
    else:
        l_icona.configure(text=icon_fallback, fg=self.MENU_FG_LIGHT)
    l_icona.pack(side="left", pady=_pad_corrente(self), padx=(13, 4))
    l_testo = tk.Label(f, text=testo, font=("Arial", 9, "bold"),
                       bg=self.MENU_BG_DARK, fg=self.MENU_FG_LIGHT)
    l_testo.pack(side="left", padx=(2, 6))
    f._icona = l_icona
    f._testo = l_testo
    for w in (f, l_icona, l_testo):
        w.bind("<Button-1>", lambda e, c=comando: c())

    def _on_enter(e):
        p = _pad_corrente(self)
        l_testo.config(fg=self.COLOR_HIGHLIGHT)
        if p >= 2:
            l_icona.pack_configure(pady=(p - 2, p + 2))
            f.after(120, lambda: l_icona.pack_configure(pady=_pad_corrente(self)) if f.winfo_exists() else None)

    def _on_leave(e):
        l_testo.config(fg=self.MENU_FG_LIGHT)
        l_icona.pack_configure(pady=_pad_corrente(self))
    for w in (f, l_icona, l_testo):
        w.bind("<Enter>", _on_enter)
        w.bind("<Leave>", _on_leave)
    self.widgets_voci.append(f)
    return f

def _adatta_sidebar(self, event=None):
    try:
        if not self.sidebar.winfo_exists():
            return
        H = self.sidebar.winfo_height()
        if H < 50 or not self.widgets_voci:
            return
        self.update_idletasks()
        pad_att = getattr(self, "_pad_voce", PAD_VOCE)
        base = max(max(max(f._icona.winfo_reqheight(), f._testo.winfo_reqheight())
                       for f in self.widgets_voci), 16)
        fisso = self.btn_toggle.winfo_reqheight() + 10 + self.lbl_logo_container.winfo_reqheight()
        if getattr(self, "sidebar_espansa", False):
            try:
                if self._search_entry.winfo_ismapped():
                    fisso += self._search_entry.winfo_reqheight() + 6
            except Exception:
                pass
        n = len(self.widgets_voci)
        margine = 6
        per_riga = (H - fisso - margine) / n
        pad = int((per_riga - base) // 2)
        pad = max(PAD_MIN, min(PAD_VOCE, pad))
        if per_riga < base:
            fissa = max(14, int(per_riga))
            for f in self.widgets_voci:
                f.pack_propagate(False)
                f.configure(height=fissa)
        else:
            for f in self.widgets_voci:
                f.pack_propagate(True)
                f.configure(height=1)
        if pad != pad_att:
            self._pad_voce = pad
            for f in self.widgets_voci:
                try:
                    f._icona.pack_configure(pady=pad)
                except Exception:
                    pass
    except Exception as ex:
        print(f"[SIDEBAR] adattamento: {ex}")

def _adatta_sidebar_differito(self, event=None):
    job = getattr(self, "_adatta_job", None)
    if job:
        try:
            self.after_cancel(job)
        except Exception:
            pass
    self._adatta_job = self.after(30, lambda: _adatta_sidebar(self))

def setup_sidebar(self):
    import __main__ as _app
    self.menu_aperto = None 
    self.sidebar_espansa = False
    if not hasattr(self, 'icone_gui'): self.icone_gui = {} 

    self._sidebar_slot = tk.Frame(self, bg=self.MENU_BG_DARK, width=45, bd=0)
    self._sidebar_slot.pack(side="left", fill="y")
    self._sidebar_slot.pack_propagate(False)
    self.sidebar = tk.Frame(self, bg=self.MENU_BG_DARK, width=45, bd=0)
    self.sidebar.place(x=0, y=0, width=45, relheight=1.0)
    self.sidebar.pack_propagate(False)
    self.sidebar.lift()
    self.btn_toggle = tk.Button(self.sidebar, text="➤", font=("Arial", 11),
                               bg=self.MENU_BG_DARK, fg=self.COLOR_GREEN,
                               bd=0, activebackground=self.MENU_ACT_BG_COLOR,
                               command=self.toggle_sidebar, cursor="hand2")
    self.btn_toggle.pack(fill="x", pady=5)
    self.lbl_logo_container = tk.Frame(self.sidebar, bg=self.MENU_BG_DARK, height=43)
    self.lbl_logo_container.pack(fill="x")
    self.lbl_logo_container.pack_propagate(False)
    self._logo_img = _carica_icona_scintille(self)
    self._busta_img = _carica_icona_scintille(self, nome="scadenze_B")
    self._busta_img_dim = _carica_icona_scintille(self, nome="scadenze_B", alpha=0.3)
    self._pool_img = _carica_icona_scintille(self, nome="utenti_B")
    self._pool_img_dim = _carica_icona_scintille(self, nome="utenti_B", alpha=0.3)
    self._agenda_img = _carica_icona_scintille(self, nome="promemoria_B")
    self._agenda_img_dim = _carica_icona_scintille(self, nome="promemoria_B", alpha=0.3)
    self.lbl_logo = tk.Label(self.lbl_logo_container, bg=self.MENU_BG_DARK)
    if self._logo_img:
        self.lbl_logo.configure(image=self._logo_img)
        self.lbl_logo.image = self._logo_img
    self.lbl_logo.pack(side="left", pady=12, padx=(13, 4))
    self.lbl_logo_container.bind("<Button-1>", lambda e: self.mostra_piramide())
    VERSION = getattr(_app, 'VERSION', '')
    self.lbl_logo_testo = tk.Label(
        self.lbl_logo_container, text=f"O.C. v.{VERSION}", font=("Arial", 9, "bold"),
        bg=self.MENU_BG_DARK, fg=self.COLOR_GREEN
    )
    self.lbl_logo_testo.bind("<Button-1>", lambda e: self.mostra_piramide())
    from moduli.messaggi_servizio import _aggiorna_badge_messaggi_servizio, click_logo_sidebar
    self.lbl_logo.bind("<Button-1>", lambda e: click_logo_sidebar(self, e))
    if getattr(self, "_messaggi_servizio_pendenti", []) or getattr(self, "_pool_novita_pendenti", 0) or getattr(self, "_agenda_novita_pendenti", 0):
        _aggiorna_badge_messaggi_servizio(self)
    self._search_var = tk.StringVar()
    self._search_entry = tk.Entry(
        self.sidebar, textvariable=self._search_var,
        font=("Arial", 8), bg=self.COLOR_WIDGET_BG, fg=self.MENU_FG_LIGHT,
        insertbackground=self.MENU_FG_LIGHT, relief="flat", bd=4,
        highlightthickness=1, highlightbackground=self.COLOR_HIGHLIGHT, highlightcolor=self.COLOR_HIGHLIGHT
    )
    self._search_var.trace_add("write", self._filtra_sidebar)
    if not getattr(self, "_click_fuori_legato", False):
        self._click_fuori_legato = True
        _h = lambda e: _click_fuori_ricerca(self, e)
        for _cl in ("Tk", "Toplevel", "Frame", "Label", "Canvas", "Text", "Listbox", "Entry", "Button",
                    "Checkbutton", "Radiobutton", "Scale", "Spinbox", "Labelframe",
                    "TFrame", "TLabel", "TLabelframe", "TButton", "TCheckbutton", "TRadiobutton",
                    "TEntry", "TCombobox", "TSpinbox", "TNotebook", "TScrollbar", "TSeparator",
                    "TProgressbar", "TScale", "Treeview", "Scrollbar"):
            try:
                self.bind_class(_cl, "<Button-1>", _h, add="+")
            except Exception:
                pass
    self._search_entry.bind("<Escape>", lambda e: _esc_ricerca(self), add="+")
    self._search_results_frame = tk.Frame(self.sidebar, bg=self.MENU_BG_DARK)
    self._search_overlay = None
    self._search_results_frame.pack_propagate(False)
    self.widgets_voci = []
    self._righe_sezioni = {}
    self.menu_sidebar_data = []
    self._pad_voce = PAD_VOCE
    self._crea_voce_sidebar("spina_B", "Esci", self._on_close, icon_fallback="✖", basso=True)
    self._crea_voce_sidebar("filtri_B", "Configura", self.gestisci_configurazione, basso=True)
    self._crea_voce_sidebar("help_B", "Info", self.show_info_app, basso=True)
    for chiave, icon_key, testo, _gruppi in SEZIONI:
        comando = lambda k=chiave: _apri_sezione(self, k)
        self.menu_sidebar_data.append((icon_key, testo, comando))
        self._righe_sezioni[chiave] = self._crea_voce_sidebar(icon_key, testo, comando)
    self._crea_voce_sidebar("lavoro_B", "Risparmio", self.apri_fondo_risparmio)
    self.spacer = tk.Frame(self.sidebar, bg=self.MENU_BG_DARK)
    self.spacer.pack(fill="both", expand=True)
    self.sidebar.bind("<Configure>", lambda e: _adatta_sidebar_differito(self))
    self.after(50, lambda: _adatta_sidebar(self))
    self.after(400, lambda: _adatta_sidebar(self))
    self.configura_scorciatoie() 

def pop_gestione(self):   _apri_sezione(self, "archivio")
def pop_analisi(self):    _apri_sezione(self, "analisi")
def pop_finanze(self):    _apri_sezione(self, "finanze")
def pop_ricorrenze(self): _apri_sezione(self, "agenda")
def pop_opzioni(self):    _apri_sezione(self, "sistema")
def pop_categorie(self):  _apri_sezione(self, "categorie")
def pop_info(self):       _apri_sezione(self, "dati")
def web_info(self):       _apri_sezione(self, "webui")

def _mostra_popup(self, menu, y_offset): 
    _pulisci_ricerca(self)
    if self.menu_aperto == menu: return 
    if self.menu_aperto: 
        try: self.menu_aperto.unpost() 
        except Exception: pass 
    self.menu_aperto = menu 
    self._menu_opened_at = time.monotonic()
    x = self.sidebar.winfo_rootx() + self.sidebar.winfo_width() 
    y = self.sidebar.winfo_rooty() + y_offset 
    try: 
        menu.post(x, y) 
        self.unbind_all("<Button-1>")
        self.unbind_all("<FocusIn>")
        self.bind_all("<Button-1>", self._verifica_chiusura_menu, add="+")
        self.bind_all("<FocusIn>", self._verifica_chiusura_menu, add="+")
        root = self.winfo_toplevel()
        root.bind("<Escape>", self._chiudi_menu_orfano)
    except Exception as e: 
        print(f"Errore apertura menu: {e}")

def _chiudi_menu_orfano(self, event=None):
    if self.menu_aperto:
        try:
            self.menu_aperto.unpost()
        except Exception:
            pass
        self.menu_aperto = None
        self.unbind_all("<Button-1>") 
        self.unbind_all("<FocusIn>")
        root = self.winfo_toplevel()
        root.unbind("<Escape>")
        if hasattr(self, "_esc_torna_treeview"):
            root.bind("<Escape>", lambda e: self._esc_torna_treeview())

def _verifica_chiusura_menu(self, event): 
    if time.monotonic() - getattr(self, '_menu_opened_at', 0) < 0.2:
        return
    if self.menu_aperto: 
        w = event.widget
        try:
            if w == self.menu_aperto or str(w).startswith(str(self.menu_aperto)):
                return
        except Exception:
            pass
        try: self.menu_aperto.unpost() 
        except Exception: pass
        self.menu_aperto = None
        self.unbind_all("<Button-1>")
        self.unbind_all("<FocusIn>")
            
def espandi_sidebar(self):
    self.update_idletasks()
    larg = max([f.winfo_reqwidth() for f in getattr(self, "widgets_voci", [])] + [120]) + 6
    self.sidebar.place_configure(width=larg)
    self.sidebar.lift()
    if hasattr(self, 'lbl_logo_testo'):
        self.lbl_logo_testo.pack(side="left", padx=(0, 6))

    if hasattr(self, '_search_entry'):
        self._search_entry.pack(after=self.lbl_logo_container, fill="x", padx=6, pady=(2, 4))
    if hasattr(self, '_search_results_frame'):
        self._search_results_frame.pack(after=self._search_entry, fill="x")
    if hasattr(self, '_search_var'):
        self._search_var.set("")
    self.after(100, lambda: self._search_entry.focus_set() if hasattr(self, '_search_entry') else None)
    _adatta_sidebar_differito(self)
            
def _add_m_item(self, target, label, icon_key, command, acc=""): 
    img = self.icone_gui.get(icon_key) 
    from moduli.scorciatoie import etichetta_per_metodo
    acc = etichetta_per_metodo(getattr(command, "__name__", "")) or acc
    def wrapped(c=command):
        if self.menu_aperto:
            try: self.menu_aperto.unpost()
            except Exception: pass
            self.menu_aperto = None
            self.unbind_all("<Button-1>")
            self.unbind_all("<FocusIn>")
        c()
    target.add_command(label=f" {label}", image=img, compound="left",  
                        command=wrapped, accelerator=acc)
                        
def _filtra_sidebar(self, *_):
    testo = self._search_var.get().strip().lower()
    if hasattr(self, '_search_overlay') and self._search_overlay and self._search_overlay.winfo_exists():
        self._search_overlay.place_forget()
        self._search_overlay.destroy()
        self._search_overlay = None
    if not testo:
        return
    trovati = _trova_voci(self, testo, limite=10)
    if not trovati:
        return
    self.update_idletasks()
    entry_abs_x = self._search_entry.winfo_rootx()
    entry_abs_y = self._search_entry.winfo_rooty()
    self_abs_x  = self.winfo_rootx()
    self_abs_y  = self.winfo_rooty()
    self_h      = self.winfo_height()
    overlay_x = entry_abs_x - self_abs_x + self._search_entry.winfo_width() + 2
    entry_y   = entry_abs_y - self_abs_y
    row_h     = 26
    from tkinter import font as _tkfont
    _f = _tkfont.Font(family="Arial", size=9)
    popup_w = max(260, max(_f.measure(l) for l, _c, _i in trovati) + 28 + 26)
    popup_w = min(popup_w, max(260, self.winfo_width() - overlay_x - 6))
    popup_h   = len(trovati) * row_h
    overlay_y = entry_y
    if overlay_y + popup_h > self_h - 10:
        overlay_y = self_h - popup_h - 10
    overlay = tk.Frame(self, bg=self.MENU_BG_DARK, bd=0,
                       highlightthickness=1, highlightbackground=self.COLOR_HIGHLIGHT,
                       highlightcolor=self.COLOR_HIGHLIGHT)
    overlay.place(x=overlay_x, y=overlay_y, width=popup_w, height=popup_h + 2)
    overlay.lift()
    self._search_overlay = overlay
    
    def _chiudi():
        if hasattr(self, '_search_overlay') and self._search_overlay and self._search_overlay.winfo_exists():
            self._search_overlay.place_forget()
            self._search_overlay.destroy()
            self._search_overlay = None
    for i, (label, cmd, icona) in enumerate(trovati):
        bg = self.MENU_BG_DARK
        def _esegui(c=cmd):
            _chiudi()
            self._search_var.set("")
            for w in self._search_results_frame.winfo_children():
                w.destroy()
            self.contrai_sidebar_manuale()
            self.btn_toggle.configure(text="➤")
            self.sidebar_espansa = False
            try:
                c()
            except Exception as ex:
                print(f"[SEARCH] {ex}")
        row = tk.Frame(overlay, bg=bg, height=row_h)
        row.pack(fill="x")
        row.pack_propagate(False)
        img = self.icone_gui.get(icona)
        l_ico = tk.Label(row, bg=bg, cursor="hand2")
        if img:
            l_ico.configure(image=img)
            l_ico.image = img
        l_ico.pack(side="left", padx=(8, 2))
        lbl = tk.Label(
            row, text=label,
            font=("Arial", 9), bg=bg, fg=self.MENU_FG_LIGHT,
            anchor="w", padx=4, cursor="hand2"
        )
        lbl.pack(side="left", fill="both", expand=True)
        def _on_enter(e, w=row, l=lbl, li=l_ico):
            w.config(bg=self.COLOR_HIGHLIGHT)
            l.config(bg=self.COLOR_HIGHLIGHT, fg="#ffffff")
            li.config(bg=self.COLOR_HIGHLIGHT)
        def _on_leave(e, w=row, l=lbl, li=l_ico, b=bg):
            w.config(bg=b)
            l.config(bg=b, fg=self.MENU_FG_LIGHT)
            li.config(bg=b)
        for _w in (lbl, l_ico, row):
            _w.bind("<Button-1>", lambda e, f=_esegui: f())
        for _w in (lbl, l_ico):
            _w.bind("<Enter>", _on_enter)
            _w.bind("<Leave>", _on_leave)
