#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import base64
import hashlib
import datetime

_SOGLIE_BASE = [0, 25, 75, 150, 300, 500, 900]
_NOMI_BASE   = ["Novizio", "Abitudinario", "Costante", "Affezionato", "Esperto", "Maestro", "Leggenda"]
_INCREMENTO_OLTRE = 1000

_SOGLIE_MESE = [0, 10, 25, 50, 100, 200, 400]
_SOGLIE_ANNO = [0, 50, 150, 400, 800, 1500, 3000]
_NOMI_PERIODO  = ["Novizio", "Abitudinario", "Costante", "Affezionato", "Esperto", "Maestro", "Leggenda"]

_ICONE_BASE = ["badge_novizio", "badge_abitudinario", "badge_costante",
               "badge_affezionato", "badge_esperto", "badge_maestro", "badge_leggenda"]

def _gami_icona_livello(idx):
    return _ICONE_BASE[max(0, min(idx, len(_ICONE_BASE) - 1))]

def _gami_numero_romano(n):
    valori = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
              (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    risultato = ""
    for valore, simbolo in valori:
        while n >= valore:
            risultato += simbolo
            n -= valore
    return risultato

def _gami_punteggio(dati):
    streak_bonus = min(dati.get("streak_record", 0), 90) * 5
    return dati.get("azioni_totali", 0) + streak_bonus
    
def _gami_livello_da_punti(punti):
    ultima_soglia = _SOGLIE_BASE[-1]
    if punti < ultima_soglia:
        idx = 0
        for i, soglia in enumerate(_SOGLIE_BASE):
            if punti >= soglia:
                idx = i
        nome = _NOMI_BASE[idx]
        prossima_soglia = _SOGLIE_BASE[idx + 1]
        indice_globale = idx
    else:
        extra = (punti - ultima_soglia) // _INCREMENTO_OLTRE
        grado_extra = extra + 1
        nome = f"{_NOMI_BASE[-1]} {_gami_numero_romano(grado_extra)}"
        prossima_soglia = ultima_soglia + (extra + 1) * _INCREMENTO_OLTRE
        indice_globale = (len(_SOGLIE_BASE) - 1) + grado_extra
    return indice_globale, nome, prossima_soglia

def _gami_livello_periodo(punti, soglie):
    idx = 0
    for i, soglia in enumerate(soglie):
        if punti >= soglia:
            idx = i
    nome = _NOMI_PERIODO[idx]
    prossima_soglia = soglie[idx + 1] if idx + 1 < len(soglie) else None
    return idx, nome, prossima_soglia

def _gami_calcola_streak(giorni_utilizzo):
    giorni_set = set(giorni_utilizzo)
    oggi = datetime.date.today()
    streak = 0
    cursore = oggi
    while cursore.isoformat() in giorni_set:
        streak += 1
        cursore -= datetime.timedelta(days=1)
    return streak

def _gami_chiave_mese(data=None):
    data = data or datetime.date.today()
    return data.strftime("%Y-%m")

def _gami_chiave_anno(data=None):
    data = data or datetime.date.today()
    return str(data.year)

def _gami_carica(self):
    import __main__ as _app
    GAMIFICATION_FILE = _app.GAMIFICATION_FILE
    default = {
        "primo_avvio": datetime.date.today().isoformat(),
        "giorni_utilizzo": [],
        "streak_corrente": 0,
        "streak_record": 0,
        "azioni_totali": 0,
        "azioni_per_tipo": {},
        "livello_corrente": 0,
        "mese_chiave": _gami_chiave_mese(),
        "mese_giorni": [],
        "mese_azioni": 0,
        "mese_livello": 0,
        "anno_chiave": _gami_chiave_anno(),
        "anno_giorni": [],
        "anno_azioni": 0,
        "anno_livello": 0,
    }
    if os.path.exists(GAMIFICATION_FILE):
        try:
            with open(GAMIFICATION_FILE, "r", encoding="utf-8") as f:
                dati = json.load(f)
            for k, v in default.items():
                dati.setdefault(k, v)
            return dati
        except Exception:
            pass
    return default

def _gami_salva(self, dati):
    import __main__ as _app
    GAMIFICATION_FILE = _app.GAMIFICATION_FILE
    try:
        with open(GAMIFICATION_FILE, "w", encoding="utf-8") as f:
            json.dump(dati, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore salvataggio gamification: {e}")

def _gami_estendi_licenza(self, giorni):
    import __main__ as _app
    from cryptography.fernet import Fernet
    DB_DIR = _app.DB_DIR
    reg_file = os.path.join(DB_DIR, "._reg.json")
    if not os.path.exists(reg_file):
        return False
    try:
        _f = _app.get_fernet_licenza()
        with open(reg_file, "r") as fh:
            dati_reg = json.load(fh)
        raw = dati_reg.get("key")
        if not raw or raw == "__MASTER__":
            return False
        payload = _f.decrypt(raw.encode()).decode()
        dev, scadenza = payload.split("|")
        if scadenza == "9999-12-31":
            return False
        nuova_scadenza = datetime.date.fromisoformat(scadenza) + datetime.timedelta(days=giorni)
        dati_reg["key"] = _f.encrypt(f"{dev}|{nuova_scadenza.isoformat()}".encode()).decode()
        with open(reg_file, "w") as fh:
            json.dump(dati_reg, fh)
        self.aggiorna_titolo_finestra()
        return True
    except Exception as e:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore estensione licenza gamification: {e}")
        return False

def _gami_aggiorna_periodo_giorno(dati, chiave_campo, giorni_campo, azioni_campo, chiave_attuale, oggi_iso):
    if dati.get(chiave_campo) != chiave_attuale:
        dati[chiave_campo] = chiave_attuale
        dati[giorni_campo] = []
        dati[azioni_campo] = 0
    if oggi_iso not in dati[giorni_campo]:
        dati[giorni_campo].append(oggi_iso)

def _gami_livelli_periodo_correnti(dati):
    punti_mese = dati.get("mese_azioni", 0) + len(dati.get("mese_giorni", [])) * 5
    punti_anno = dati.get("anno_azioni", 0) + len(dati.get("anno_giorni", [])) * 5
    idx_mese, _n, _p = _gami_livello_periodo(punti_mese, _SOGLIE_MESE)
    idx_anno, _n, _p = _gami_livello_periodo(punti_anno, _SOGLIE_ANNO)
    return idx_mese, idx_anno

def _gami_punti_periodo(dati):
    punti_mese = dati.get("mese_azioni", 0) + len(dati.get("mese_giorni", [])) * 5
    punti_anno = dati.get("anno_azioni", 0) + len(dati.get("anno_giorni", [])) * 5
    return punti_mese, punti_anno

def aggiorna_streak_gamification(self):
    dati = self._gami_carica()
    oggi_iso = datetime.date.today().isoformat()

    if oggi_iso not in dati["giorni_utilizzo"]:
        dati["giorni_utilizzo"].append(oggi_iso)
        dati["giorni_utilizzo"] = dati["giorni_utilizzo"][-730:]
    dati["streak_corrente"] = _gami_calcola_streak(dati["giorni_utilizzo"])
    dati["streak_record"] = max(dati.get("streak_record", 0), dati["streak_corrente"])
    punti = _gami_punteggio(dati)
    dati["livello_corrente"] = _gami_livello_da_punti(punti)[0]

    _gami_aggiorna_periodo_giorno(dati, "mese_chiave", "mese_giorni", "mese_azioni", _gami_chiave_mese(), oggi_iso)
    _gami_aggiorna_periodo_giorno(dati, "anno_chiave", "anno_giorni", "anno_azioni", _gami_chiave_anno(), oggi_iso)
    dati["mese_livello"], dati["anno_livello"] = _gami_livelli_periodo_correnti(dati)

    self._gami_dati = dati
    self._gami_salva(dati)
    self.aggiorna_badge_header()

    self.after(30 * 60 * 1000, self.aggiorna_streak_gamification)

def _gami_nome_scope(self, scope, livello):
    if scope == "vita":
        dati = getattr(self, "_gami_dati", None) or self._gami_carica()
        _idx, nome, _p = _gami_livello_da_punti(_gami_punteggio(dati))
        return nome
    idx = max(0, min(livello, len(_NOMI_PERIODO) - 1))
    return _NOMI_PERIODO[idx]

def _gami_mostra_notifiche_badge(self, eventi, licenza_estesa=False):
    etichette = {"vita": "A VITA", "mese": "DEL MESE", "anno": "DELL'ANNO"}
    righe = []
    for scope, livello in eventi:
        nome = self._gami_nome_scope(scope, livello)
        righe.append(f"Nuovo livello {etichette[scope]}: {nome}")
    if licenza_estesa:
        righe.append("Licenza estesa di 30 giorni!")
    testo = "\n".join(righe)
    durata = 3500 + 1200 * len(righe)
    self.show_toast(testo, duration=durata)

def aggiorna_badge_header(self):
    if not hasattr(self, "lbl_badge_gamification"):
        return
    dati = getattr(self, "_gami_dati", None) or self._gami_carica()
    punti = _gami_punteggio(dati)
    idx, nome, prossima_soglia = _gami_livello_da_punti(punti)
    icona = getattr(self, "icone_gui", {}).get(_gami_icona_livello(idx))
    self.lbl_badge_gamification.config(
        image=icona, text=f" {nome}", compound="left")
    self.lbl_badge_gamification.image = icona

    punti_mese = dati.get("mese_azioni", 0) + len(dati.get("mese_giorni", [])) * 5
    punti_anno = dati.get("anno_azioni", 0) + len(dati.get("anno_giorni", [])) * 5
    _im, nome_mese, prossima_mese = _gami_livello_periodo(punti_mese, _SOGLIE_MESE)
    _ia, nome_anno, prossima_anno = _gami_livello_periodo(punti_anno, _SOGLIE_ANNO)

    righe = [
        f"BADGE A VITA: {nome}",
        f"Punti: {punti}  (mancano {prossima_soglia - punti} al prossimo livello)",
        f"Al prossimo livello: +30 giorni di licenza!",
        "",
        f"BADGE DEL MESE: {nome_mese}",
        f"Punti mese: {punti_mese}"
        + (f"  (mancano {prossima_mese - punti_mese})" if prossima_mese is not None else "  (massimo)"),
        "",
        f"BADGE DELL'ANNO: {nome_anno}",
        f"Punti anno: {punti_anno}"
        + (f"  (mancano {prossima_anno - punti_anno})" if prossima_anno is not None else "  (massimo)"),
        "",
        f"Streak attuale: {dati.get('streak_corrente', 0)} giorni (record: {dati.get('streak_record', 0)})",
        f"Azioni totali: {dati.get('azioni_totali', 0)}",
    ]
    self._gami_tooltip_testo = "\n".join(righe)

def registra_azione_gamification(self, tipo="generico"):
    dati = getattr(self, "_gami_dati", None) or self._gami_carica()
    oggi_iso = datetime.date.today().isoformat()

    dati["azioni_totali"] = dati.get("azioni_totali", 0) + 1
    dati.setdefault("azioni_per_tipo", {})
    dati["azioni_per_tipo"][tipo] = dati["azioni_per_tipo"].get(tipo, 0) + 1
    livello_prima = dati.get("livello_corrente", 0)
    punti = _gami_punteggio(dati)
    livello_ora = _gami_livello_da_punti(punti)[0]
    dati["livello_corrente"] = livello_ora

    _gami_aggiorna_periodo_giorno(dati, "mese_chiave", "mese_giorni", "mese_azioni", _gami_chiave_mese(), oggi_iso)
    _gami_aggiorna_periodo_giorno(dati, "anno_chiave", "anno_giorni", "anno_azioni", _gami_chiave_anno(), oggi_iso)
    dati["mese_azioni"] = dati.get("mese_azioni", 0) + 1
    dati["anno_azioni"] = dati.get("anno_azioni", 0) + 1
    mese_livello_prima = dati.get("mese_livello", 0)
    anno_livello_prima = dati.get("anno_livello", 0)
    dati["mese_livello"], dati["anno_livello"] = _gami_livelli_periodo_correnti(dati)

    self._gami_dati = dati
    self._gami_salva(dati)
    self.aggiorna_badge_header()

    eventi = []
    if livello_ora > livello_prima:
        eventi.append(("vita", livello_ora))
    if dati["mese_livello"] > mese_livello_prima:
        eventi.append(("mese", dati["mese_livello"]))
    if dati["anno_livello"] > anno_livello_prima:
        eventi.append(("anno", dati["anno_livello"]))

    licenza_estesa = False
    if any(scope == "vita" for scope, _ in eventi):
        licenza_estesa = self._gami_estendi_licenza(30)

    if eventi:
        self._gami_mostra_notifiche_badge(eventi, licenza_estesa)
