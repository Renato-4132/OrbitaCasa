#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def registra_tutti_i_moduli(GestioneSpese):
    def _registra(*funzioni):
        for _f in funzioni:
            setattr(GestioneSpese, _f.__name__, _f)

    from moduli.sidebar_menu import (
        setup_sidebar, _animate_logo_text, toggle_sidebar, contrai_sidebar_manuale, _crea_voce_sidebar, pop_gestione,
        pop_analisi, pop_finanze, pop_ricorrenze, pop_opzioni, pop_info, _mostra_popup, _chiudi_menu_orfano, _verifica_chiusura_menu,
        espandi_sidebar, _add_m_item,_filtra_sidebar,)
    _registra(setup_sidebar, _animate_logo_text, toggle_sidebar, contrai_sidebar_manuale, _crea_voce_sidebar, pop_gestione, 
    pop_analisi, pop_finanze, pop_ricorrenze, pop_opzioni, pop_info, _mostra_popup, _chiudi_menu_orfano, _verifica_chiusura_menu, 
    espandi_sidebar, _add_m_item, _filtra_sidebar)
            
    from moduli.dialoghi_custom import (
        show_custom_warning, show_custom_info, show_custom_askyesno, _show_toast_dialog, show_toast,)
    _registra(show_custom_warning, show_custom_info, show_custom_askyesno, _show_toast_dialog, show_toast)
    
    from moduli.menu_contestuale import (
        configura_menu_contestuale_globale, _esegui_comando_menu, _mostra_menu_globale, _chiudi_menu_sicuro,
        _avvia_timer_chiusura, _annulla_timer_chiusura,_global_select_all,)
    _registra(configura_menu_contestuale_globale, _esegui_comando_menu, _mostra_menu_globale, _chiudi_menu_sicuro, 
    _avvia_timer_chiusura, _annulla_timer_chiusura, _global_select_all)

    from moduli.temi import applica_temi
    _registra(applica_temi)

    from moduli.mostra_calendario_popup import mostra_calendario_popup_semplice, mostra_calendario_popup
    _registra(mostra_calendario_popup_semplice, mostra_calendario_popup)
    
    from moduli.dieta import apri_dieta
    _registra(apri_dieta)

    from moduli.supermercati import spesa_supermercato, mostra_help_supermercati
    _registra(spesa_supermercato, mostra_help_supermercati)

    from moduli.supermarket_updater import (
        check_supermarket_update, check_supermarket_update_manuale, _rimuovi_editor_esterno, _scarica_editor_esterno, _avvia_editor_esterno,)
    _registra(check_supermarket_update, check_supermarket_update_manuale, _rimuovi_editor_esterno, _scarica_editor_esterno, _avvia_editor_esterno)

    from moduli.utenze import utenze
    _registra(utenze)

    from moduli.veicoli import (
        _veicoli_carica, _veicoli_salva, _veicoli_giorni_a_scadenza, _veicoli_colore_giorni, _veicoli_testo_scadenza,
        _veicoli_costo_al_km, _veicoli_consumo_medio, veicoli, _veicoli_crea_tab, _veicoli_nuovo, _veicoli_elimina,
        _veicoli_grafici, _veicoli_estratto, _veicoli_estratto_totale,)
    _registra(_veicoli_carica, _veicoli_salva, _veicoli_giorni_a_scadenza, _veicoli_colore_giorni, _veicoli_testo_scadenza,
    _veicoli_costo_al_km, _veicoli_consumo_medio, veicoli, _veicoli_crea_tab, _veicoli_nuovo, _veicoli_elimina,
    _veicoli_grafici, _veicoli_estratto, _veicoli_estratto_totale)
    
    from moduli.immobil import (
        _immobil_carica, _immobil_salva, immobil, _immobil_crea_tab, _immobil_nuovo, _immobil_elimina, _immobil_grafici,
        _immobil_estratto, _immobil_estratto_totale,)
    _registra(_immobil_carica, _immobil_salva, immobil, _immobil_crea_tab, _immobil_nuovo, _immobil_elimina, 
    _immobil_grafici, _immobil_estratto, _immobil_estratto_totale)

    from moduli.documenti_personali import (
        gestisci_documenti_personali, backup_documenti_personali, mostra_help_documenti_personali,
        _genera_testo_scadenze_documenti,)
    _registra(gestisci_documenti_personali, backup_documenti_personali, mostra_help_documenti_personali,
              _genera_testo_scadenze_documenti)

    from moduli.archivi_pdf import (
        gestisci_archivi_pdf, mostra_help_pdf, esegui_export_documenti_pdf, esegui_import_documenti_pdf,backup_documenti,)
    _registra(gestisci_archivi_pdf, mostra_help_pdf, esegui_export_documenti_pdf, esegui_import_documenti_pdf, backup_documenti)

    from moduli.grafici_statistiche import (
        draw_bar_chart, draw_mensile_chart, show_tooltip, hide_tooltip, draw_saldo_chart,)
    _registra(draw_bar_chart, draw_mensile_chart, show_tooltip, hide_tooltip, draw_saldo_chart)
    
    from moduli.report_testuali import (
        export_giorno_forzato, export_stats, export_month_detail, export_anno_dettagliato, export_storico_totale, show_export_preview,)
    _registra(export_giorno_forzato, export_stats, export_month_detail, export_anno_dettagliato, export_storico_totale, show_export_preview)
    
    from moduli.categorie import (
        mostra_categorie_popup, on_categoria_modifica_changed_popup, on_categoria_modifica_changed, reset_campi_categoria,
        aggiorna_categoria_automatica, aggiorna_combobox_categorie, on_categoria_changed, mostra_tutte_le_categorie,
        add_categoria, modifica_categoria, conferma_cancella_categoria, cancella_categoria, draw_top_categorie, mostra_storico_categoria,
        suggerisci_tipo_categoria, open_analisi_categoria, _ottieni_categorie_ricorrenti_mancanti, gruppo_categorie, cancella_categorie_checkbox,
        apri_categorie_suggerite, get_dati_categorie_storiche_json, get_dati_categorie_json, mostra_editor_memoria_categorie,
        pop_categorie, _aggiorna_stile_pulsante_tipo_popup,)
    _registra(mostra_categorie_popup, on_categoria_modifica_changed_popup, on_categoria_modifica_changed, 
    reset_campi_categoria, aggiorna_categoria_automatica, aggiorna_combobox_categorie, on_categoria_changed, 
    mostra_tutte_le_categorie, add_categoria, modifica_categoria, conferma_cancella_categoria, cancella_categoria, 
    draw_top_categorie, mostra_storico_categoria, suggerisci_tipo_categoria, open_analisi_categoria, 
    _ottieni_categorie_ricorrenti_mancanti, gruppo_categorie, cancella_categorie_checkbox, apri_categorie_suggerite, 
    get_dati_categorie_storiche_json, get_dati_categorie_json, mostra_editor_memoria_categorie, pop_categorie, _aggiorna_stile_pulsante_tipo_popup)

    from moduli.open_compare_window import open_compare_window, crea_grafico_confronto
    _registra(open_compare_window, crea_grafico_confronto)

    from moduli.rubrica import rubrica_app
    _registra(rubrica_app)

    from moduli.studio import apri_studio
    _registra(apri_studio)

    from moduli.portafoglio import apri_portafoglio, _porta_load, _porta_save, _porta_prezzo_live, _porta_calcola_titolo
    _registra(apri_portafoglio, _porta_load, _porta_save, _porta_prezzo_live, _porta_calcola_titolo)

    from moduli.saldo_conto import open_saldo_conto
    _registra(open_saldo_conto)

    from moduli.fondo_risparmio import apri_fondo_risparmio
    _registra(apri_fondo_risparmio)

    from moduli.calcolo_mutuo_prestito import calcolo_mutuo_prestito
    _registra(calcolo_mutuo_prestito)

    from moduli.gestisci_configurazione import gestisci_configurazione, fetch_gemini_models
    _registra(gestisci_configurazione, fetch_gemini_models)

    from moduli.cerca_operazioni import cerca_operazioni, cerca_doppio_click
    _registra(cerca_operazioni, cerca_doppio_click)

    from moduli.crea_grafico_categorie import crea_grafico_categorie, _build_filter_data
    _registra(crea_grafico_categorie, _build_filter_data)

    from moduli.apri_gestione_tag import apri_gestione_tag
    _registra(apri_gestione_tag)

    from moduli.apri_cancella_spese_treeview_unica import apri_cancella_spese_treeview_unica
    _registra(apri_cancella_spese_treeview_unica)

    from moduli.mostra_analisi_grafici import mostra_analisi_grafici
    _registra(mostra_analisi_grafici)

    from moduli.gestisci_backup_popup import gestisci_backup_popup
    _registra(gestisci_backup_popup)

    from moduli.genera_report_pdf_core import _genera_report_pdf_core, _apri_viewer_report
    _registra(_genera_report_pdf_core, _apri_viewer_report)

    from moduli.gestione_login import gestione_login
    _registra(gestione_login)

    from moduli.gestisci_partecipanti import gestisci_partecipanti
    _registra(gestisci_partecipanti)

    from moduli.mostra_grafici_fairshare import mostra_grafici_fairshare
    _registra(mostra_grafici_fairshare)

    from moduli.mostra_dare_avere import mostra_dare_avere
    _registra(mostra_dare_avere)

    from moduli.schedulatore import (
        apri_schedulatore, _tick_scheduler, _esegui_scheduler, _genera_testo_ricorrenti_mancanti, _genera_testo_estratto_mensile,
        _genera_testo_estratto_annuale, _calcola_saldo_mese_corrente, _genera_testo_allerta_saldo, _invia_email_scheduler,
        _genera_testo_scadenze_veicoli, _genera_testo_riepilogo_cronologico,)
    _registra(apri_schedulatore, _tick_scheduler, _esegui_scheduler,
              _genera_testo_ricorrenti_mancanti, _genera_testo_estratto_mensile,
              _genera_testo_estratto_annuale, _calcola_saldo_mese_corrente,
              _genera_testo_allerta_saldo, _invia_email_scheduler, _genera_testo_scadenze_veicoli,
              _genera_testo_riepilogo_cronologico)

    from moduli.toggle_stats_view import toggle_stats_view
    _registra(toggle_stats_view)

    from moduli.goto_dettaglio_mese import goto_dettaglio_mese
    _registra(goto_dettaglio_mese)

    from moduli.calcola_mancanti import calcola_mancanti, get_lista_categorie_mancanti
    _registra(calcola_mancanti, get_lista_categorie_mancanti)

    from moduli.controlla_ricorrenti import controlla_ricorrenti_manual, controlla_ricorrenti_a_fine_mese, _carica_dismiss_fm, _salva_dismiss_fm
    _registra(controlla_ricorrenti_manual, controlla_ricorrenti_a_fine_mese, _carica_dismiss_fm, _salva_dismiss_fm)
    
    from moduli.mostra_ricorrenza_popup import mostra_ricorrenza_popup, reset_ricorrenza_popup
    _registra(mostra_ricorrenza_popup, reset_ricorrenza_popup)

    from moduli.launch_qr_svg_generator import launch_qr_svg_generator
    _registra(launch_qr_svg_generator)
    
    from moduli.mostra_transazioni_popup import mostra_transazioni_popup
    _registra(mostra_transazioni_popup)
    
    from moduli.confronta_bollette_ia import confronta_bollette_ia
    _registra(confronta_bollette_ia)
    
    from moduli.mostra_lista_ricorrenze import mostra_lista_ricorrenze, on_ricorrenza_double_click
    _registra(mostra_lista_ricorrenze, on_ricorrenza_double_click)
    
    from moduli.apri_calcolatore_inflazione import apri_calcolatore_inflazione
    _registra(apri_calcolatore_inflazione)
    
    from moduli.apri_andamento_risparmio import apri_andamento_risparmio
    _registra(apri_andamento_risparmio)
    
    from moduli.apri_inserimento_rapido import apri_inserimento_rapido
    _registra(apri_inserimento_rapido)
    
    from moduli.mostra_log_importazioni import mostra_log_importazioni
    _registra(mostra_log_importazioni)
    
    from moduli.apri_viewer_tabella import scarica_tabella, _apri_viewer_tabella
    _registra(scarica_tabella, _apri_viewer_tabella)
    
    from moduli.apri_finestra_importa import apri_finestra_importa
    _registra(apri_finestra_importa)
    
    from moduli.apri_finestra_revisione_universale import apri_finestra_revisione_universale
    _registra(apri_finestra_revisione_universale)
    
    from moduli.time_machine import time_machine
    _registra(time_machine)
    
    from moduli.scadenze_mese import scadenze_mese, on_scadenza_doppio_click
    _registra(scadenze_mese, on_scadenza_doppio_click)
    
    from moduli.analizza_andamento_ia import analizza_andamento_ia
    _registra(analizza_andamento_ia)
    
    from moduli.mostra_spese_simili import mostra_spese_simili
    _registra(mostra_spese_simili)
    
    from moduli.mostra_qr_popup_label import mostra_qr_popup_label
    _registra(mostra_qr_popup_label)
    
    from moduli.on_stats_table_double_click import on_stats_table_double_click
    _registra(on_stats_table_double_click)
    
    from moduli.mostra_piramide import mostra_piramide
    _registra(mostra_piramide)
    
    from moduli.apri_calcolatrice import apri_calcolatrice
    _registra(apri_calcolatrice)
    
    from moduli.contatta_assistenza import apri_pannello_topic, invia_email_assistenza
    _registra(apri_pannello_topic, invia_email_assistenza)
    
    from moduli.show_info_app import show_info_app
    _registra(show_info_app)
    
    from moduli.apri_cancella_multiplo import apri_cancella_multiplo
    _registra(apri_cancella_multiplo)
    
    from moduli.stampa import anteprima_e_stampa_txt, _stampa_lista_diretta, stampa_pdf
    _registra(anteprima_e_stampa_txt, _stampa_lista_diretta, stampa_pdf)
    
    from moduli.gestisci_promemoria import gestisci_promemoria
    _registra(gestisci_promemoria)
    
    from moduli.avvia_tutorial import _avvia_tutorial
    _registra(_avvia_tutorial)

    from moduli.quick_add import quick_add
    _registra(quick_add)
    
    from moduli.scorciatoie import configura_scorciatoie, mostra_popup_scorciatoie
    _registra(configura_scorciatoie, mostra_popup_scorciatoie)

    from moduli.apri_viewer_pdf import _apri_viewer_pdf
    _registra(_apri_viewer_pdf)

    from moduli.apri_estratti_metodo import apri_estratti_metodo, _esporta_estratti_metodo
    _registra(apri_estratti_metodo, _esporta_estratti_metodo)

    from moduli.mostra_registro_errori import mostra_registro_errori
    _registra(mostra_registro_errori)
    
    from moduli.avvia_sincronizzazione import avvia_sincronizzazione
    _registra(avvia_sincronizzazione)

    from moduli.esegui_backup_zip import esegui_backup_zip
    _registra(esegui_backup_zip)
    
    from moduli.genera_report_pdf import genera_report_pdf
    _registra(genera_report_pdf)
    
    from moduli.changelog import (visualizza_changelog, _visualizza_changelog_thread, _mostra_popup_changelog,)
    _registra(visualizza_changelog, _visualizza_changelog_thread, _mostra_popup_changelog)

    from moduli.popup_scelta_estratto import popup_scelta_estratto
    _registra(popup_scelta_estratto)
    
    from moduli.show_reset_dialog import show_reset_dialog
    _registra(show_reset_dialog)

    from moduli.fairshare import (
        _on_partecipante_selected, _aggiorna_descrizione_con_partecipante, _on_ric_partecipante_selected, _aggiorna_descrizione_con_ric_partecipante,
        _gestore_partecipa, carica_fairshare_state, salva_fairshare_state, _sync_fairshare_e_aggiorna, sincronizza_fairshare_state,
        mostra_riepilogo_fairshare_periodo, popup_personali, popup_grafico_categorie_personali, mostra_guida_dare_avere,
        get_fairshare_data_json,)
    _registra(_on_partecipante_selected, _aggiorna_descrizione_con_partecipante, 
    _on_ric_partecipante_selected, _aggiorna_descrizione_con_ric_partecipante, 
    _gestore_partecipa, carica_fairshare_state, salva_fairshare_state, 
    _sync_fairshare_e_aggiorna, sincronizza_fairshare_state, mostra_riepilogo_fairshare_periodo,
    popup_personali, popup_grafico_categorie_personali, mostra_guida_dare_avere, 
    get_fairshare_data_json)

    from moduli.webserver import (
        apri_webserver, _crea_flask_app, start_web_server, html_login, html_cambia_pw_web, html_log_web, pagina_risultati_avanzati,
        html_info_sys, html_form, html_saluto, html_fairshare_web, documenti_pdf_web, documenti_personali_web, genera_html_utenze,
        genera_html_consultazione, pagina_menu_esplora, add_categoria_web, modifica_categoria_web, cancella_categoria_web,
        refresh_categorie_web, html_gestione_categorie, pagina_fondo_risparmio_web, pagina_grafici_web, html_lista_spese_mensili,
        stats_mensili_html, modifica_voce_form, cancella_voce_web, aggiungi_voce_web, carica_db_web, analizza_pdf_web,
        ricalcola_operazioni_web, notifica_modifica_web, web_info, pianifica_sincro_web,
        manda_push, get_dati_entrate_uscite_tutti_gli_anni_json, get_dati_saldo_annuale_json,
        get_dati_entrate_uscite_json, get_dati_saldo_json,)
    _registra(apri_webserver, _crea_flask_app, start_web_server, html_login, 
    html_cambia_pw_web, html_log_web, pagina_risultati_avanzati, html_info_sys, 
    html_form, html_saluto, html_fairshare_web, documenti_pdf_web, documenti_personali_web, 
    genera_html_utenze, genera_html_consultazione, pagina_menu_esplora, add_categoria_web, 
    modifica_categoria_web, cancella_categoria_web, refresh_categorie_web, html_gestione_categorie, 
    pagina_fondo_risparmio_web, pagina_grafici_web, html_lista_spese_mensili, stats_mensili_html, 
    modifica_voce_form, cancella_voce_web, aggiungi_voce_web, carica_db_web, analizza_pdf_web, 
    ricalcola_operazioni_web, notifica_modifica_web, web_info, pianifica_sincro_web,
    manda_push, get_dati_entrate_uscite_tutti_gli_anni_json, get_dati_saldo_annuale_json,
    get_dati_entrate_uscite_json, get_dati_saldo_json)

    from moduli.sicurezza_rete import (
        apri_cambio_password, scarica_manuale_ssl, _apri_viewer_ssl, start_watchdog_server, genera_certificati_auto,
        leggi_hash,salva_hash, verifica_password, registra_accesso, registra_accesso_fallito, invia_notifica_fallimento,
        get_ip_locale_reale, get_dominio_ssl, gestisci_certificati, mostra_log_accessi,)
    _registra(apri_cambio_password, scarica_manuale_ssl, _apri_viewer_ssl, start_watchdog_server, 
    genera_certificati_auto, leggi_hash, salva_hash, verifica_password, registra_accesso, registra_accesso_fallito, 
    invia_notifica_fallimento, get_ip_locale_reale, get_dominio_ssl, gestisci_certificati, mostra_log_accessi)

    from moduli.aggiornamenti_app import (
        forza_aggiorna, aggiorna, _check_librerie_in_background, check_aggiornamento_con_api, check_aggiornamento_thread,
        _mostra_popup_aggiornamento, forza_check_aggiornamento_con_api, _forza_check_thread, _mostra_popup_forza_aggiornamento,
        aggiorna_librerie_pip, ripristina_da_backup,)
    _registra(forza_aggiorna, aggiorna, _check_librerie_in_background, check_aggiornamento_con_api, check_aggiornamento_thread, 
    _mostra_popup_aggiornamento, forza_check_aggiornamento_con_api, _forza_check_thread, _mostra_popup_forza_aggiornamento, 
    aggiorna_librerie_pip, ripristina_da_backup)

