#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import base64
import hashlib
import datetime
import tkinter as tk

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
        "livello_massimo_raggiunto": 0,
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
            dati["livello_massimo_raggiunto"] = max(
                dati.get("livello_massimo_raggiunto", 0), dati.get("livello_corrente", 0))
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

def annulla_azione_gamification(self, tipo="generico"):
    dati = getattr(self, "_gami_dati", None) or self._gami_carica()

    dati["azioni_totali"] = max(0, dati.get("azioni_totali", 0) - 1)
    dati.setdefault("azioni_per_tipo", {})
    if tipo in dati["azioni_per_tipo"]:
        dati["azioni_per_tipo"][tipo] = max(0, dati["azioni_per_tipo"][tipo] - 1)
    punti = _gami_punteggio(dati)
    dati["livello_corrente"] = _gami_livello_da_punti(punti)[0]

    if dati.get("mese_chiave") == _gami_chiave_mese():
        dati["mese_azioni"] = max(0, dati.get("mese_azioni", 0) - 1)
    if dati.get("anno_chiave") == _gami_chiave_anno():
        dati["anno_azioni"] = max(0, dati.get("anno_azioni", 0) - 1)
    dati["mese_livello"], dati["anno_livello"] = _gami_livelli_periodo_correnti(dati)

    self._gami_dati = dati
    self._gami_salva(dati)
    self.aggiorna_badge_header()

def registra_azione_gamification(self, tipo="generico"):
    dati = getattr(self, "_gami_dati", None) or self._gami_carica()
    oggi_iso = datetime.date.today().isoformat()

    dati["azioni_totali"] = dati.get("azioni_totali", 0) + 1
    dati.setdefault("azioni_per_tipo", {})
    dati["azioni_per_tipo"][tipo] = dati["azioni_per_tipo"].get(tipo, 0) + 1
    livello_massimo_prima = dati.get("livello_massimo_raggiunto", 0)
    punti = _gami_punteggio(dati)
    livello_ora = _gami_livello_da_punti(punti)[0]
    dati["livello_corrente"] = livello_ora
    if livello_ora > livello_massimo_prima:
        dati["livello_massimo_raggiunto"] = livello_ora

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
    if livello_ora > livello_massimo_prima:
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
        

def _gami_dettaglio_livello_vita(punti):
    idx, nome, prossima_soglia = _gami_livello_da_punti(punti)
    if idx < len(_SOGLIE_BASE):
        soglia_corrente = _SOGLIE_BASE[idx]
    else:
        grado_extra = idx - (len(_SOGLIE_BASE) - 1)
        soglia_corrente = _SOGLIE_BASE[-1] + (grado_extra - 1) * _INCREMENTO_OLTRE
    return idx, nome, soglia_corrente, prossima_soglia

def _gami_dettaglio_livello_periodo(punti, soglie):
    idx, nome, prossima_soglia = _gami_livello_periodo(punti, soglie)
    soglia_corrente = soglie[idx]
    return idx, nome, soglia_corrente, prossima_soglia

def _gami_disegna_barra(canvas, percentuale, colore_pieno="#66BB6A", colore_vuoto="#3A3A3A"):
    canvas.delete("all")
    canvas.update_idletasks()
    w = canvas.winfo_width() or int(canvas["width"])
    h = canvas.winfo_height() or int(canvas["height"])
    percentuale = max(0.0, min(1.0, percentuale))
    canvas.create_rectangle(0, 0, w, h, fill=colore_vuoto, outline="")
    if percentuale > 0:
        canvas.create_rectangle(0, 0, int(w * percentuale), h, fill=colore_pieno, outline="")

def _gami_costruisci_scheda(self, parent, icone_gui, idx_attuale, punti, soglia_corrente, soglia_prossima,
                             soglie_legenda, nomi_legenda, righe_extra):

    frame = tk.Frame(parent, bg=self.COLOR_BACKGROUND)
    frame.columnconfigure(0, weight=3, minsize=520)
    frame.columnconfigure(1, weight=2, minsize=340)

    colonna_sx = tk.Frame(frame, bg=self.COLOR_BACKGROUND)
    colonna_sx.grid(row=0, column=0, sticky="new", padx=(4, 10))
    colonna_dx = tk.Frame(frame, bg=self.COLOR_BACKGROUND)
    colonna_dx.grid(row=0, column=1, sticky="new", padx=(10, 4))

    riga_top = tk.Frame(colonna_sx, bg=self.COLOR_BACKGROUND)
    riga_top.pack(fill="x", pady=(6, 4))
    icona_attuale = icone_gui.get(_gami_icona_livello(idx_attuale))
    if icona_attuale:
        lbl_ic = tk.Label(riga_top, image=icona_attuale, bg=self.COLOR_BACKGROUND)
        lbl_ic.image = icona_attuale
        lbl_ic.pack(side="left", padx=(0, 10))
    testo_top = tk.Frame(riga_top, bg=self.COLOR_BACKGROUND)
    testo_top.pack(side="left", fill="x", expand=True)
    tk.Label(testo_top, text=nomi_legenda[min(idx_attuale, len(nomi_legenda) - 1)] if idx_attuale < len(nomi_legenda)
             else f"{nomi_legenda[-1]} (grado {idx_attuale - len(nomi_legenda) + 2})",
             bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR, font=("Arial", 12, "bold"), anchor="w").pack(fill="x")
    tk.Label(testo_top, text=f"{punti} punti totali", bg=self.COLOR_BACKGROUND, fg="#BDBDBD",
             font=("Arial", 9), anchor="w").pack(fill="x")

    barra_frame = tk.Frame(colonna_sx, bg=self.COLOR_BACKGROUND)
    barra_frame.pack(fill="x", pady=(2, 2))
    canvas_barra = tk.Canvas(barra_frame, height=14, bg=self.COLOR_BACKGROUND, highlightthickness=0, bd=0)
    canvas_barra.pack(fill="x")
    if soglia_prossima is not None:
        percentuale = (punti - soglia_corrente) / max(1, (soglia_prossima - soglia_corrente))
        canvas_barra.after(10, lambda: _gami_disegna_barra(canvas_barra, percentuale))
        mancano = soglia_prossima - punti
        tk.Label(colonna_sx, text=f"Mancano {mancano} punti per il prossimo livello ({soglia_prossima} punti totali)",
                 bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR, font=("Arial", 9), anchor="w",
                 justify="left", wraplength=480).pack(fill="x", pady=(0, 8))
    else:
        canvas_barra.after(10, lambda: _gami_disegna_barra(canvas_barra, 1.0))
        tk.Label(colonna_sx, text="Livello massimo raggiunto per questo periodo!",
                 bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR, font=("Arial", 9, "bold"), anchor="w",
                 justify="left", wraplength=480).pack(fill="x", pady=(0, 8))

    if righe_extra:
        box = tk.Frame(colonna_sx, bg=self.COLOR_WIDGET_BG)
        box.pack(fill="x", pady=(0, 10))
        for riga_testo in righe_extra:
            tk.Label(box, text=riga_testo, bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                     font=("Arial", 8), anchor="w", justify="left", wraplength=470).pack(fill="x", padx=8, pady=(4, 4))

    tk.Label(colonna_dx, text="Legenda livelli", bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
             font=("Arial", 9, "bold"), anchor="w").pack(fill="x", pady=(6, 4))
    for i, (soglia_i, nome_i) in enumerate(zip(soglie_legenda, nomi_legenda)):
        raggiunto = punti >= soglia_i
        e_attuale = (i == idx_attuale) or (idx_attuale >= len(nomi_legenda) - 1 and i == len(nomi_legenda) - 1)
        bg_riga = "#37474F" if e_attuale else (self.COLOR_WIDGET_BG if i % 2 == 0 else self.COLOR_BACKGROUND)
        riga = tk.Frame(colonna_dx, bg=bg_riga)
        riga.pack(fill="x", pady=1)
        icona_i = icone_gui.get(_gami_icona_livello(i))
        if icona_i:
            lbl_i = tk.Label(riga, image=icona_i, bg=bg_riga)
            lbl_i.image = icona_i
            lbl_i.pack(side="left", padx=(6, 8), pady=3)
        tk.Label(riga, text=nome_i, bg=bg_riga, fg=self.TEXT_COLOR, font=("Arial", 9, "bold" if e_attuale else "normal"),
                 anchor="w", width=16).pack(side="left")
        tk.Label(riga, text=f"{soglia_i} punti", bg=bg_riga, fg="#BDBDBD", font=("Arial", 8), anchor="w", width=10
                 ).pack(side="left")
        stato = "✓ Raggiunto" if raggiunto else "🔒 Da sbloccare"
        colore_stato = "#81C784" if raggiunto else "#9E9E9E"
        tk.Label(riga, text=stato, bg=bg_riga, fg=colore_stato, font=("Arial", 8, "bold"), anchor="e"
                 ).pack(side="right", padx=(0, 8))
    if idx_attuale >= len(nomi_legenda):
        riga_extra = tk.Frame(colonna_dx, bg="#37474F")
        riga_extra.pack(fill="x", pady=1)
        icona_ext = icone_gui.get(_gami_icona_livello(idx_attuale))
        if icona_ext:
            lbl_ext = tk.Label(riga_extra, image=icona_ext, bg="#37474F")
            lbl_ext.image = icona_ext
            lbl_ext.pack(side="left", padx=(6, 8), pady=3)
        grado_extra = idx_attuale - len(nomi_legenda) + 2
        tk.Label(riga_extra, text=f"{nomi_legenda[-1]} {_gami_numero_romano(grado_extra)}", bg="#37474F",
                 fg=self.TEXT_COLOR, font=("Arial", 9, "bold"), anchor="w", width=16).pack(side="left")
        tk.Label(riga_extra, text=f"{soglia_corrente} punti", bg="#37474F", fg="#BDBDBD",
                 font=("Arial", 8), anchor="w", width=10).pack(side="left")
        tk.Label(riga_extra, text="✓ Livello attuale", bg="#37474F", fg="#81C784",
                 font=("Arial", 8, "bold"), anchor="e").pack(side="right", padx=(0, 8))

    return frame

def mostra_dettaglio_gamification(self):
    if hasattr(self, '_win_gami_dettaglio') and self._win_gami_dettaglio and self._win_gami_dettaglio.winfo_exists():
        self._win_gami_dettaglio.lift()
        self._win_gami_dettaglio.focus_force()
        return

    dati = getattr(self, "_gami_dati", None) or self._gami_carica()
    icone_gui = getattr(self, "icone_gui", {})

    punti_vita = _gami_punteggio(dati)
    idx_vita, nome_vita, soglia_corr_vita, soglia_pros_vita = _gami_dettaglio_livello_vita(punti_vita)

    punti_mese, punti_anno = _gami_punti_periodo(dati)
    idx_mese, nome_mese, soglia_corr_mese, soglia_pros_mese = _gami_dettaglio_livello_periodo(punti_mese, _SOGLIE_MESE)
    idx_anno, nome_anno, soglia_corr_anno, soglia_pros_anno = _gami_dettaglio_livello_periodo(punti_anno, _SOGLIE_ANNO)

    azioni_totali = dati.get("azioni_totali", 0)
    streak_record = dati.get("streak_record", 0)
    streak_conteggiato = min(streak_record, 90)
    punti_da_streak = streak_conteggiato * 5
    righe_vita = [
        "🔥 Cos'è lo streak? È il numero di giorni consecutivi in cui apri l'app, senza saltarne nemmeno uno. "
        "Se un giorno non la apri, il conteggio riparte da zero — ma il tuo record migliore resta per sempre "
        "e continua a valere per i punti.",
        "",
        "Come si fanno i punti: 1 punto per ogni azione registrata + 5 punti per ogni giorno del tuo streak "
        "record, fino a un massimo di 90 giorni (450 punti).",
        "Cosa conta come \"azione\"? Ogni movimento (spesa o entrata) che registri nell'app.",
        f"Azioni totali: {azioni_totali} → {azioni_totali} punti",
        f"Streak record (il tuo massimo storico): {streak_record} giorni ({streak_conteggiato} conteggiati) → {punti_da_streak} punti",
        f"Streak attuale (giorni di fila fino a oggi): {dati.get('streak_corrente', 0)} giorni",
        "",
        f"Ogni nuovo livello a vita regala +30 giorni di licenza!",
    ]
    righe_mese = [
        f"Come si fanno i punti del mese: 1 punto per ogni azione del mese + 5 punti per ogni giorno attivo nel mese.",
        "Cosa conta come \"azione\"? Ogni movimento (spesa o entrata) che registri nell'app.",
        f"Azioni questo mese: {dati.get('mese_azioni', 0)}",
        f"Giorni attivi questo mese: {len(dati.get('mese_giorni', []))}",
        f"Si azzera automaticamente all'inizio di ogni mese.",
    ]
    righe_anno = [
        f"Come si fanno i punti dell'anno: 1 punto per ogni azione dell'anno + 5 punti per ogni giorno attivo nell'anno.",
        "Cosa conta come \"azione\"? Ogni movimento (spesa o entrata) che registri nell'app.",
        f"Azioni quest'anno: {dati.get('anno_azioni', 0)}",
        f"Giorni attivi quest'anno: {len(dati.get('anno_giorni', []))}",
        f"Si azzera automaticamente ogni 1° gennaio.",
    ]

    win = tk.Toplevel(self, bg=self.COLOR_BACKGROUND)
    self._win_gami_dettaglio = win
    win.withdraw()
    win.transient(self)
    win.overrideredirect(True)
    win.resizable(False, False)
    win.bind("<Escape>", lambda e: win.destroy())
    w, h = 980, 480
    x = self.winfo_rootx() + (self.winfo_width() // 2) - (w // 2)
    y = self.winfo_rooty() + (self.winfo_height() // 2) - (h // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")


    tk.Label(win, text="I Tuoi Traguardi", bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
             font=("Arial", 12, "bold")).pack(pady=(14, 6))

    barra_schede = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    barra_schede.pack(fill="x", padx=16)
    img_chiudi = icone_gui.get("chiudi")
    btn_chiudi = tk.Frame(win, bg=self.COLOR_BACKGROUND, cursor="hand2")
    if img_chiudi:
        lbl_ic = tk.Label(btn_chiudi, image=img_chiudi, bg=self.COLOR_BACKGROUND, cursor="hand2")
        lbl_ic.image = img_chiudi
        lbl_ic.pack(side="left", padx=(0, 5))
    tk.Label(btn_chiudi, text="Chiudi", bg=self.COLOR_BACKGROUND, fg=self.TEXT_COLOR,
             font=("Arial", 9, "bold"), cursor="hand2").pack(side="left")
    btn_chiudi.pack(side="bottom", pady=(10, 16))
    for w_ in btn_chiudi.winfo_children():
        w_.bind("<Button-1>", lambda e: win.destroy())
    btn_chiudi.bind("<Button-1>", lambda e: win.destroy())

    contenitore = tk.Frame(win, bg=self.COLOR_BACKGROUND)
    contenitore.pack(fill="both", expand=True, padx=16, pady=(6, 0))

    scheda_vita = _gami_costruisci_scheda(self, contenitore, icone_gui, idx_vita, punti_vita,
                                           soglia_corr_vita, soglia_pros_vita, _SOGLIE_BASE, _NOMI_BASE, righe_vita)
    scheda_mese = _gami_costruisci_scheda(self, contenitore, icone_gui, idx_mese, punti_mese,
                                           soglia_corr_mese, soglia_pros_mese, _SOGLIE_MESE, _NOMI_PERIODO, righe_mese)
    scheda_anno = _gami_costruisci_scheda(self, contenitore, icone_gui, idx_anno, punti_anno,
                                           soglia_corr_anno, soglia_pros_anno, _SOGLIE_ANNO, _NOMI_PERIODO, righe_anno)
    for scheda in (scheda_vita, scheda_mese, scheda_anno):
        scheda.grid(row=0, column=0, sticky="nsew")
    contenitore.rowconfigure(0, weight=1)
    contenitore.columnconfigure(0, weight=1)

    schede = {"vita": scheda_vita, "mese": scheda_mese, "anno": scheda_anno}
    tab_labels = {}

    def _mostra_scheda(chiave):
        schede[chiave].tkraise()
        for k, lbl in tab_labels.items():
            lbl.config(bg="#37474F" if k == chiave else self.COLOR_WIDGET_BG,
                       font=("Arial", 9, "bold" if k == chiave else "normal"))

    for chiave, etichetta, chiave_icona in (
        ("vita", " A Vita", "badge_maestro"),
        ("mese", " Mese", "calendario"),
        ("anno", " Anno", "oggi"),
    ):
        icona_tab = icone_gui.get(chiave_icona)
        lbl = tk.Label(barra_schede, text=etichetta, image=icona_tab, compound="left",
                        bg=self.COLOR_WIDGET_BG, fg=self.TEXT_COLOR,
                        font=("Arial", 9), cursor="hand2", padx=10, pady=6)
        if icona_tab:
            lbl.image = icona_tab
        lbl.pack(side="left", padx=(0, 4))
        lbl.bind("<Button-1>", lambda e, k=chiave: _mostra_scheda(k))
        tab_labels[chiave] = lbl

    _mostra_scheda("vita")
    win.deiconify()
    win.lift()
    win.attributes("-topmost", True)
    win.after(100, lambda: win.attributes("-topmost", False))
    win.focus_force()
