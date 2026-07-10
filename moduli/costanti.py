#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import datetime

def leggi_configurazione_globale(path_locale):
    c_file = os.path.join(path_locale, "db", "config.json")
    try:
        if os.path.exists(c_file):
            with open(c_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def carica_costanti(path_locale):
    g = {}
    app_config_globale = leggi_configurazione_globale(path_locale)
    g['app_config_globale'] = app_config_globale
    DB_CONDIVISO = app_config_globale.get("shared_db", False)
    PATH_RETE = app_config_globale.get("shared_db_path", path_locale)
    g['DB_CONDIVISO'] = DB_CONDIVISO
    g['PATH_RETE'] = PATH_RETE
    if DB_CONDIVISO and os.path.exists(PATH_RETE):
        BASE_DIR = PATH_RETE
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 📡 Modalità Rete Attiva")
    else:
        BASE_DIR = path_locale
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] 🏠 Modalità Locale Attiva")
    g['BASE_DIR'] = BASE_DIR

    g['URL_PDF'] = "https://raw.githubusercontent.com/Renato-4132/OrbitaCasa/refs/heads/main/OrbitaCasa.pdf"
    g['URL_PDF_CONSUMI'] = "https://raw.githubusercontent.com/Renato-4132/OrbitaCasa/main/Tabella%20Contatori.pdf"
    g['URL_PDF_SSL'] = "https://raw.githubusercontent.com/Renato-4132/OrbitaCasa/main/Manuale_CertBot_SSL.pdf"
    g['URL_LOGO'] = "https://github.com/Renato-4132/OrbitaCasa/raw/main/resources/info_image.png"
    g['GITHUB_FILE_URL'] = "https://raw.githubusercontent.com/Renato-4132/OrbitaCasa/refs/heads/main/OrbitaCasa.pyw"
    g['GITHUB_SUPERMARKET'] = "https://raw.githubusercontent.com/Renato-4132/OrbitaCasa/main/supermarket.pyw"
    g['ALIMENTI'] = "https://raw.githubusercontent.com/Renato-4132/OrbitaCasa/main/resources/alimenti.json"
    g['NOME_EDITOR_LOCALE'] = "supermarket.pyw"
    g['NOME_FILE'] = "OrbitaCasa.pyw"
    g['REPO_OWNER'] = "Renato-4132"
    g['REPO_NAME'] = "OrbitaCasa"
    g['NAME'] = "Orbita Casa"
    g['MODULI_DIR'] = os.path.join(path_locale, "moduli")
    g['BRANCH_PRINCIPALE'] = "main"
    g['EXPORTDB_DIR'] = "export"

    DB_DIR = os.path.join(BASE_DIR, "db")
    g['EXPORT_DIR'] = os.path.join(BASE_DIR, "export")
    g['DB_DIR'] = DB_DIR
    g['DB_FILE'] = os.path.join(DB_DIR, "spese_db.json")
    g['DATI_FILE'] = os.path.join(DB_DIR, "rubrica.json")
    g['UTENZE_DB'] = os.path.join(DB_DIR, "utenze_db.json")
    g['DOC_DIR'] = os.path.join(DB_DIR, "documenti")
    g['REGISTRY_FILE'] = os.path.join(DB_DIR, "documenti_archiviati.json")
    g['EXPORT_FATTURE_DIR'] = os.path.join(DB_DIR, "Fatture")
    g['PORTAFOGLIO_BANCARIO'] = os.path.join(DB_DIR, "portafoglio_db.json")
    g['TAGS_DB'] = os.path.join(DB_DIR, "tags_db.json")
    g['SUPERMERCATI_DB'] = os.path.join(DB_DIR, "supermercati.json")
    g['EXPORT_FILES'] = os.path.join(BASE_DIR, "export")
    g['EXP_DB'] = os.path.join(DB_DIR, g['EXPORTDB_DIR'])
    g['PW_FILE'] = os.path.join(DB_DIR, "password.json")
    g['MEM_CAT'] = os.path.join(DB_DIR, "memoria_categorie.json")
    g['CONFIG_FILE'] = os.path.join(path_locale, "db", "config.json")
    g['RIMANDA_FILE'] = os.path.join(DB_DIR, "update.json")
    g['PROMEMORIA_FILE'] = os.path.join(DB_DIR, "promemoria.json")
    g['PORTAFOGLIO_AZIONI'] = os.path.join(DB_DIR, "portafoglio.json")
    g['ICON_NAME'] = "resources/meteo_sole.png"
    g['DEFAULT_API'] = os.path.join(DB_DIR, "api.json")
    g['CONTROLLO_F_M'] = os.path.join(DB_DIR, "controllo_fm.json")
    g['APRI_BROWSER'] = False
    g['URL_QST'] = "https://forms.gle/VidTCh7ySkWHCAE6A"
    g['LINK_BANCA'] = ""
    g['LOGIN_WEB'] = os.path.join(DB_DIR, "login_web.json")
    g['LOGIN_WEB_FAIL'] = os.path.join(DB_DIR, "login_web_fail.json")
    g['LOGIN_LCL'] = os.path.join(DB_DIR, "login_lcl.json")
    g['ACCESS_CONTROL_WEB'] = os.path.join(DB_DIR, "web_access_control.json")
    g['PARTECIPANTI'] = os.path.join(DB_DIR, "fairshare.json")
    g['FAIRSHARE_STATE'] = os.path.join(DB_DIR, "fairshare_state.json")
    g['FR_FILE'] = os.path.join(DB_DIR, "fondo_risparmio.json")
    g['DIETA_FILE'] = os.path.join(DB_DIR, "dieta_piano.json")
    g['CUSTOM_FILE'] = os.path.join(DB_DIR, "alimenti_custom.json")
    g['PESO_FILE'] = os.path.join(DB_DIR, "peso_storico.json")
    g['FABB_FILE'] = os.path.join(DB_DIR, "fabbisogno_dati.json")
    g['PEDOMETRO_FILE'] = os.path.join(DB_DIR, "pedometro.json")
    g['STUDIO_CLIENTI'] = os.path.join(DB_DIR, "studio_clienti.json")
    g['STUDIO_APPUNTAMENTI'] = os.path.join(DB_DIR, "studio_appuntamenti.json")
    g['STUDIO_PRESTAZIONI'] = os.path.join(DB_DIR, "studio_prestazioni.json")
    g['STUDIO_FATTURE'] = os.path.join(DB_DIR, "studio_fatture.json")
    g['STUDIO_EMITTENTE'] = os.path.join(DB_DIR, "studio_emittente.json")
    g['STUDIO_CASSA'] = os.path.join(DB_DIR, "studio_cassa.json")
    g['STUDIO_MAGAZZINO'] = os.path.join(DB_DIR, "studio_magazzino.json")
    g['IMMOBIL_FILE'] = os.path.join(DB_DIR, "immobil.json")
    g['SCHEDULE_FILE'] = os.path.join(DB_DIR, "schedule.json")
    g['EMAIL_USER'] = ""
    g['APP_PASSWORD'] = ""
    g['PAROLE_CHIAVE'] = ["no-reply-ML@aceaenergia.it, no-reply.acque@acque.net, contotelefonico@fatturazione.windtre.it"]
    g['SYNC_INT_MIN'] = 720
    g['SYNC_H'] = "a9d038b985412b44659f74b5c1bcf1c730b9e3f53f4b6b64eccf8e485a3103b1"
    g['API_KEY'] = ""
    g['LOG_IMPORTAZIONI'] = os.path.join(DB_DIR, "log_importazioni.txt")
    g['DOC_PERS_DIR'] = os.path.join(DB_DIR, "documenti_personali")
    g['VEICOLI_FILE'] = os.path.join(DB_DIR, "veicoli.json")
    
    g['CAT_DEFAULT'] = [
        "Atto Notarile", "Altro", "Assicurazione", "Carta d'Identità",
        "Certificato", "Codice Fiscale", "Contratto", "Curriculum",
        "Dichiarazione Redditi", "Diploma", "Garanzia", "Laurea",
        "Manuale", "Passaporto", "Patente", "Polizza",
        "Proprietà Immobile", "Referto Medico", "Tessera Sanitaria",
        "Utenza Casa", "Verbale"
    ]

    g['GEMINI'] = "gemini-2.5-flash"                # Modello Gemini
    g['MANDA_PUSH'] = False                         # Manda un messaggio push con ip
    g['MANDA_MAIL_FAIL'] = True                     # Manda mail su accesso bloccato
    g['CHECK_DOPPI_MOV'] = False                    # Controlla Doppi Movimenti
    g['WARN_TIMEOUT'] = 20000                       # Timeout Messaggi Popup (ms)
    g['USE_WAIT_WINDOW'] = False                    # Timeout chiusura self.show_custom_warning
    g['TOLL'] = 15                                  # Tolleranza Movimenti simili (SmartCat) - Euro
    g['VERSION'] = "2.2.7"
    g['ICONIZZA_INATTIVITA'] = True                 # Attiva/disattiva Timer Minimizza
    g['TIMEOUT_INATTIVITA_MS'] = 1200000            # 20 minuti in ms - Timer Minimizza
    g['ANNI_DA_MANTENERE'] = 10                     # Anni conservati nel db
    g['SALVA_GEOMETRIA_INIZIALE'] = False           # Salva la posizione della gui
    g['ICO_SET_DATE'] = True                        # Set data quando iconizza/deiconizza
    g['SMARTCAT'] = True                            # Riconoscimento automatico categorie
    g['CHECK_MESE'] = True                          # Check categorie mancanti a fine mese
    g['SOGLIA_GIORNI_RICORRENTI'] = 5               # Avviso gg prima del termine mese
    g['MAX_BACKUP'] = 5                             # Copie backup da conservare
    g['CAROSELLO'] = True                           # Rotazione automatica contenuti visuali
    g['CAL_TOOLTIPS'] = True                        # Tooltips su Calendario
    g['ANIMAZIONI'] = True                          # Animazione Totalizzatori
    g['SYNC_DATI'] = False                          # Sync dati esterni
    g['USA_SSL'] = True                             # Abilita SSL
    g['CONTEXT_MENU'] = True                        # Menu Copia Incolla
    g['THEMA'] = "OBSIDIAN"                         # Default tema avvio
    g['SYS_BUF_CHECK'] = True                       # Paramentri Risorse
    g['SOGLIA_CHECKOUT'] = 4                        # Lista categorie mancanti
    g['CLOSE'] = False                              # Paramentri bottone chiusura
    g['BEEP'] = True                                # Abilita Suoni

    g['DEFAULT_CONFIG'] = {
        "enable_auto_login_flow": False,
        "webserver_enabled": False,
        "iconizza_inattivita": True,
        "inactivity_timeout_ms": 1200000,
        "webserver_port": 8080,
        "usa_ssl": True,
        "load_saved_geometry": False,
        "anni_da_mantenere": 10,
        "ico_set_date": True,
        "enable_recurring_reminder": True,
        "soglia_giorni_ricorrenti": 5,
        "max_backup": 5,
        "smartcat_enabled": True,
        "smartcat_toll": 15,
        "use_wait_window": False,
        "warn_timeout_ms": 20000,
        "bank_link": "",
        "thema": "OBSIDIAN",
        "carosello_enabled": True,
        "carosello_intervallo": 10000,
        "cal_tooltips_enabled": True,
        "anima_tot_enabled": True,
        "shared_db": False,
        "shared_db_path": path_locale,
        "udp_port_1": 5555,
        "udp_port_2": 5556,
        "target_mese": 0,
        "target_anno": 0,
        "sync_dati_enabled": False,
        "manda_push_enabled": False,
        "email_user": "",
        "app_password": "",
        "parole_chiave": ["no-reply-ML@aceaenergia.it, no-reply.acque@acque.net, contotelefonico@fatturazione.windtre.it"],
        "gemini_api_key": "",
        "sync_intervallo_min": 720,
        "check_double": False,
        "close_behavior": False,
        "gemini_model": "gemini-2.5-flash",
        "beep_enabled": True,
        "budget_categorie": {},
    }

    g['CATEGORIE_PREDEFINITE'] = [
        "Affettati", "Acqua", "Animali Domestici", "Articoli Bimbi",
        "Assorbenza", "Auto e Elettronica", "Birre", "Biscotti", "Bucato",
        "Caffè e Bevande", "Cancelleria/Party", "Carne", "Carta Casa/Igiene",
        "Carta e Alluminio", "Casalinghi/Tessile", "Cereali Colazione",
        "Cibi Etnici", "Cioccolato", "Conserve Pesce", "Cosmetici",
        "Cura dei Capelli", "Cura del Corpo", "Dolciumi e Caramelle",
        "Farine e Lieviti", "Formaggi Freschi", "Formaggi Stagionati",
        "Frutta Fresca", "Gastronomia", "Gelati", "Giardino e Fai da",
        "Igiene Persona", "Insalate Pronte", "Integratori/Sanitari",
        "Latte e Burro", "Latticini e Yogurt", "Legumi Secchi/Scatole",
        "Liquori e Distillati", "Marmellate/Creme", "Merende e Snack",
        "Molluschi/Crostacei", "Olio", "Ortaggi e Tuberi", "Pane e Panini",
        "Pasta Fresca", "Pasta Secca", "Pesce", "Piatti Pronti",
        "Pizze Surgelate", "Pollame", "Prodotti Bio", "Prodotti Dietetici",
        "Prodotti Veg/Vegan", "Pulizia Casa", "Riso", "Salumi",
        "Salse e Condimenti", "Snack Panetteria", "Snack Salati",
        "Sottoli/Sottaceti", "Spugne e Guanti", "Succhi/Bibite",
        "Surgelati Pesce", "Surgelati Vari", "Surgelati Verdura",
        "Sushi e Tartare", "Uova", "Varie", "Verdura Fresca",
        "Vini e Spumanti",
    ]

    g['MAP_ICONE'] = [
        ("iconizza_B", ("2796", "🗗")),
        ("tastiera_B", ("2328", "⌨️")),
        ("info_B", ("2139", "ℹ️")),
        ("report_B", ("1f4ca", "📊")),
        ("qr_B", ("1f310", "🌐")),
        ("promemoria_B", ("1f4cc", "📌")),
        ("timer_B", ("23f0", "⏰")),
        ("scadenze_B", ("1f4e2", "📢")),
        ("spesa_B", ("1f6d2", "🛒")),
        ("banca_B", ("1f3e6", "🏦")),
        ("saldo_B", ("1f4b0", "💰")),
        ("sync_B", ("1f4e1", "📡")),
        ("reset_B", ("1f504", "🔙")),
        ("mobile_B", ("1f4f1", "📱")),
        ("timer_sync_B", ("23f3", "⌛")),
        ("documenti_B", ("1f4c1", "📁")),
        ("documentiP_B", ("1f4cb", "📋")),
        ("help_B", ("2754", "❓")),
        ("tools_B", ("1f527", "🔧")),
        ("calendario_B", ("1f4c5", "📅")),
        ("chiudi_B", ("274c", "❌")),
        ("filtri_B", ("2699", "⚙️")),
        ("sparkles_B", ("2728", "✨")),
        ("lavoro_B", ("1f4bc", "💼")),
        ("occhio_B", ("1f441", "👁️")),
        ("spina_B", ("1f50c", "🔌")),
        ("veicoli", ("1f697", "🚗")),
        ("iconizza", ("2796", "🗗")),
        ("tag", ("1f3f7", "🏷️")),
        ("report", ("1f4ca", "📊")),
        ("qr", ("1f310", "🌐")),
        ("promemoria", ("1f4cc", "📌")),
        ("timer", ("23f0", "⏰")),
        ("scadenze", ("1f4e2", "📢")),
        ("spesa", ("1f6d2", "🛒")),
        ("banca", ("1f3e6", "🏦")),
        ("saldo", ("1f4b0", "💰")),
        ("sync", ("1f4e1", "📡")),
        ("reset", ("1f504", "🔙")),
        ("mobile", ("1f4f1", "📱")),
        ("timer_sync", ("23f3", "⌛")),
        ("chiudi", ("274c", "❌")),
        ("salva", ("1f4be", "💾")),
        ("stampa", ("1f5a8", "🖨️")),
        ("check", ("2714", "✅")),
        ("delete", ("1f5d1", "🗑️")),
        ("search", ("1f50d", "🔍")),
        ("help", ("2754", "❓")),
        ("grafico_linea", ("1f4c8", "📈")),
        ("grafico_torta", ("1f4c9", "📉")),
        ("calendario", ("1f4c5", "📅")),
        ("carica", ("1f4e5", "📥")),
        ("documenti", ("1f4c1", "📁")),
        ("descrizione", ("1f4dd", "📝")),
        ("oggi", ("1f5d3", "🗓️")),
        ("calcolatrice", ("2797", "➗")),
        ("link", ("1f517", "🔗")),
        ("qr_code", ("1f4f2", "📲")),
        ("archivia", ("1f4e5", "📥")),
        ("reset_campo", ("1f504", "🔄")),
        ("filtri", ("2699", "⚙️")),
        ("cancella", ("1f5d1", "🗑️")),
        ("google", ("1f310", "🌐")),
        ("api_key", ("1f511", "🔑")),
        ("aggiungi", ("2795", "➕")),
        ("icc", ("1f3e6", "🏦")),
        ("ccv", ("1f4b3", "💳")),
        ("tools", ("1f527", "🔧")),
        ("occhio", ("1f441", "👁️")),
        ("occhio_chiuso", ("1f512", "🔒")),
        ("modifica", ("270f", "✏️")),
        ("mouse", ("1f5b1", "🖱️")),
        ("salute", ("1f48a", "💊")),
        ("fitness", ("1f3cb", "🏋️")),
        ("auto_manutenzione", ("1f6e0", "🛠️")),
        ("bus", ("1f68c", "🚌")),
        ("regalo", ("1f381", "🎁")),
        ("cinema", ("1f3ac", "🎬")),
        ("vestiti", ("1f455", "👕")),
        ("beauty", ("2702", "✂️")),
        ("aereo", ("2708", "✈️")),
        ("cloud", ("2601", "☁️")),
        ("studio", ("1f4da", "📚")),
        ("lavoro", ("1f4bc", "💼")),
        ("alert", ("26a0", "⚠️")),
        ("info", ("2139", "ℹ️")),
        ("home", ("1f3e0", "🏠")),
        ("meteo_sole", ("2600", "☀️")),
        ("meteo_pioggia", ("1f327", "🌧️")),
        ("meteo_temporale", ("26c8", "⛈️")),
        ("utenti", ("1f464", "👤")),
    ]

    return g
