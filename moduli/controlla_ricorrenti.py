#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import datetime

from __main__ import CHECK_MESE, SOGLIA_GIORNI_RICORRENTI, CONTROLLO_F_M

# Analisi e Promemoria Categorie di Spesa Ricorrenti Mancanti Manuale
def controlla_ricorrenti_manual(self):
    from datetime import datetime
    oggi = datetime.today().date()
    def converti_data(d):
        if isinstance(d, str):
            try:
                return datetime.strptime(d, "%d-%m-%Y").date()
            except:
                return None
        elif isinstance(d, datetime):
            return d.date()
        return d
    categorie_base = {cat.title() for cat in self.categorie if cat}
    if not categorie_base:
        return
    categorie_mancanti_nel_mese = []
    presenti_questo_mese = set()
    conteggio_storico = {}
    MESI_INDIETRO = 12
    for d, sp in self.spese.items():
        dd = converti_data(d)
        if not dd:
            continue
        diff_mesi = (oggi.year - dd.year) * 12 + (oggi.month - dd.month)
        if diff_mesi == 0:
            for voce in sp:
                if len(voce) > 0 and voce[0].strip():
                    presenti_questo_mese.add(voce[0].strip().title())
        elif 1 <= diff_mesi <= MESI_INDIETRO:
            viste_in_data = set()
            for voce in sp:
                if len(voce) > 0 and voce[0].strip():
                    cat = voce[0].strip().title()
                    if cat in categorie_base and cat not in viste_in_data:
                        conteggio_storico[cat] = conteggio_storico.get(cat, 0) + 1
                        viste_in_data.add(cat)
    for cat in categorie_base:
        presenze_passate = conteggio_storico.get(cat, 0)
        if presenze_passate >= 4 and cat not in presenti_questo_mese:
            categorie_mancanti_nel_mese.append(cat)
    if categorie_mancanti_nel_mese:
        elenco_mancanti = "\n".join(sorted(categorie_mancanti_nel_mese))
        messaggio = (
            f"PROMEMORIA MOVIMENTI RICORRENTI!\n\n"
            f"Hai dimenticato qualcosa? Le seguenti categorie, registrate "
            f"abitualmente negli ultimi mesi, non risultano ancora presenti nel mese corrente:\n\n"
            f"{elenco_mancanti}\n\n"
            f"Premi Sì per aprire la verifica dettagliata, oppure No per chiudere."
        )
        risposta = self.show_custom_askyesno(
            "Promemoria Movimenti Ricorrenti",
            messaggio
        )
        if risposta:
            self.calcola_mancanti()

# Analisi e Promemoria Categorie di Spesa Ricorrenti Mancanti Automatico
def controlla_ricorrenti_a_fine_mese(self):
    from datetime import datetime, timedelta
    if hasattr(self, 'changelog_window') and \
       self.changelog_window is not None and \
       self.changelog_window.winfo_exists():
        self.after(5000, self.controlla_ricorrenti_a_fine_mese)
        return
    try:
        oggi = datetime.today().date()
        prossimo_mese = oggi.replace(day=28) + timedelta(days=4)
        ultimo_giorno_mese = prossimo_mese - timedelta(days=prossimo_mese.day)
        giorni_alla_fine = (ultimo_giorno_mese - oggi).days
        if giorni_alla_fine > SOGLIA_GIORNI_RICORRENTI or giorni_alla_fine < 0:
            return
        if self._last_dismiss_date and self._last_dismiss_date.year == oggi.year and self._last_dismiss_date.month == oggi.month:
            return
        def converti_data(d):
            if isinstance(d, str):
                try: return datetime.strptime(d, "%d-%m-%Y").date()
                except: return None
            elif isinstance(d, datetime): return d.date()
            return d
        categorie_base = {cat.title() for cat in self.categorie if cat}
        if not categorie_base:
            return
        categorie_mancanti_nel_mese = []
        presenti_questo_mese = set()
        conteggio_storico = {}
        MESI_INDIETRO = 12
        for d, sp in self.spese.items():
            dd = converti_data(d)
            if not dd: continue
            diff_mesi = (oggi.year - dd.year) * 12 + (oggi.month - dd.month)
            if diff_mesi == 0:
                for voce in sp:
                    if len(voce) > 0 and voce[0].strip():
                        presenti_questo_mese.add(voce[0].strip().title())
            elif 1 <= diff_mesi <= MESI_INDIETRO:
                viste_oggi = set()
                for voce in sp:
                    if len(voce) > 0 and voce[0].strip():
                        cat = voce[0].strip().title()
                        if cat in categorie_base and cat not in viste_oggi:
                            conteggio_storico[cat] = conteggio_storico.get(cat, 0) + 1
                            viste_oggi.add(cat)
        for cat in categorie_base:
            presenze_passate = conteggio_storico.get(cat, 0)
            if presenze_passate >= 4 and cat not in presenti_questo_mese:
                categorie_mancanti_nel_mese.append(cat)
        if categorie_mancanti_nel_mese:
            if self.wm_state() == 'iconic':
                self.deiconify()
                self.lift()
            elenco_mancanti = "\n".join(sorted(categorie_mancanti_nel_mese))
            messaggio = (
                f"PROMEMORIA MOVIMENTI RICORRENTI (Fine Mese)!\n\n"
                f"Hai dimenticato qualcosa? Le seguenti categorie, registrate "
                f"abitualmente nei mesi scorsi, non risultano ancora presenti:\n\n"
                f"{elenco_mancanti}\n\n"
                f"Premi Sì per aprire la verifica dettagliata, oppure No per nascondere l'avviso fino al mese prossimo."
            )
            risposta = self.show_custom_askyesno("Promemoria Movimenti Ricorrenti", messaggio)
            if risposta:
                self.calcola_mancanti()
            else:
                self._last_dismiss_date = oggi
                self._salva_dismiss_fm(oggi)
    finally:
        if CHECK_MESE:
            self._job_ricorrenti = self.after(3600000, self.controlla_ricorrenti_a_fine_mese)

# Persistenza e Gestione della Data di "Dismiss" Promemoria Ricorrenti
def _carica_dismiss_fm(self):
    if not os.path.exists(CONTROLLO_F_M):
        return None
    try:
        with open(CONTROLLO_F_M, 'r') as f:
            data = json.load(f)
            data_str = data.get('last_recurring_dismiss')
            if data_str:
                return datetime.datetime.strptime(data_str, "%Y-%m-%d").date()
            return None
    except Exception as e:
        print(f"Errore nel caricamento del dismiss ricorrenti: {e}")
        return None

def _salva_dismiss_fm(self, data_da_salvare):
    try:
        data_str = data_da_salvare.strftime("%Y-%m-%d")
        dati = {'last_recurring_dismiss': data_str}
        dir_path = os.path.dirname(CONTROLLO_F_M)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        with open(CONTROLLO_F_M, 'w') as f:
            json.dump(dati, f, indent=4)
        return True
    except Exception as e:
        errore_messaggio = (
            f"Errore critico durante il salvataggio della data di 'dismiss' "
            f"nel file di controllo ({os.path.basename(CONTROLLO_F_M)}).\n"
            f"L'avviso delle ricorrenti ricomparirà al prossimo avvio.\n"
            f"Dettagli: {e}"
        )
        if hasattr(self, 'show_custom_warning'):
            self.show_custom_warning("⚠️ Errore di Persistenza", errore_messaggio)
        else:
            print(errore_messaggio)
        return False
