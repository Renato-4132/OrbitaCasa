#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import platform
import shutil

NOME_APP = "OrbitaCasa"
SOTTOCARTELLA = "license"

NOMI_FILE_LICENZA = (
    ".key_reg", 
    "._reg.json", 
    "._trial.json", 
    "._sync_chk", 
    "._bn_cache", 
    "web_access_control.json", 
)

def ottieni_cartella_licenza():
    sistema = platform.system()
    try:
        if sistema == "Windows":
            base = os.environ.get("APPDATA") or os.path.expanduser("~")
            cartella = os.path.join(base, NOME_APP, SOTTOCARTELLA)
        elif sistema == "Darwin":
            base = os.path.expanduser("~/Library/Application Support")
            cartella = os.path.join(base, NOME_APP, SOTTOCARTELLA)
        else:
            base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
            cartella = os.path.join(base, NOME_APP, SOTTOCARTELLA)
        os.makedirs(cartella, exist_ok=True)
    except Exception:
        # Fallback estremo: cartella nascosta nella home dell'utente
        cartella = os.path.join(os.path.expanduser("~"), f".{NOME_APP.lower()}", SOTTOCARTELLA)
        os.makedirs(cartella, exist_ok=True)
    return cartella

def _cartelle_dati_da_ripulire(path_locale):
    cartelle = [os.path.join(path_locale, "db")]
    profili_dir = os.path.join(path_locale, "profili")
    if os.path.isdir(profili_dir):
        try:
            for nome in os.listdir(profili_dir):
                cartella_profilo = os.path.join(profili_dir, nome, "db")
                if os.path.isdir(cartella_profilo):
                    cartelle.append(cartella_profilo)
        except Exception:
            pass
    return cartelle

def migra_e_ripulisci(path_locale):
    cartella_licenza = ottieni_cartella_licenza()

    for cartella_dati in _cartelle_dati_da_ripulire(path_locale):
        if not os.path.isdir(cartella_dati):
            continue
        for nome_file in NOMI_FILE_LICENZA:
            vecchio_percorso = os.path.join(cartella_dati, nome_file)
            if not os.path.exists(vecchio_percorso):
                continue
            nuovo_percorso = os.path.join(cartella_licenza, nome_file)
            if os.path.exists(nuovo_percorso):
                try:
                    os.remove(vecchio_percorso)
                except Exception:
                    pass
                continue
            try:
                shutil.move(vecchio_percorso, nuovo_percorso)
            except Exception:
                try:
                    shutil.copy2(vecchio_percorso, nuovo_percorso)
                    os.remove(vecchio_percorso)
                except Exception:
                    pass

    return cartella_licenza

def percorsi_file_licenza(cartella_licenza):
    return {nome: os.path.join(cartella_licenza, nome) for nome in NOMI_FILE_LICENZA}
