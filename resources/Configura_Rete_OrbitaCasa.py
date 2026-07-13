#!/usr/bin/env python3
import subprocess
import sys
import ctypes
import os
"""
=============================================================================
CONFIGURAZIONE RETE ORBITA CASA - SBLOCCO FIREWALL WINDOWS  
=============================================================================
A COSA SERVE:
Questo script autorizza CasaFacilePro a ricevere connessioni dai tuoi 
dispositivi (Smartphone/Tablet) attraverso la rete Wi-Fi di casa.

COME USARLO:
1. Salva questo file sul PC dove hai installato ORBITA CASA.
2. Fai TASTO DESTRO sul file e seleziona "ESEGUI COME AMMINISTRATORE".
3. Al termine, riavvia ORBITA CASA se era già aperto.

SICUREZZA:
Lo script non apre porte a caso, ma autorizza specificamente solo l'app 
ORBITA CASA a comunicare, garantendo che il tuo PC resti protetto.
=============================================================================
"""
def abilita_python_completo():
    if not ctypes.windll.shell32.IsUserAnAdmin():
        print("❌ ERRORE: Eseguire come AMMINISTRATORE.")
        return
    python_exe = sys.executable
    nome_regola = "OrbitaCasa_Python_Global"
    print(f"⚙️ Autorizzazione totale per: {python_exe}")
    subprocess.run(
        f'netsh advfirewall firewall delete rule name="{nome_regola}"', 
        shell=True, capture_output=True
    )
    comando = (
        f'netsh advfirewall firewall add rule name="{nome_regola}" '
        f'dir=in action=allow program="{python_exe}" enable=yes'
    )
    risultato = subprocess.run(comando, shell=True, capture_output=True, text=True)
    if risultato.returncode == 0:
        print("✅ Python è ora autorizzato nel Firewall su qualsiasi porta!")
    else:
        print(f"❌ Errore: {risultato.stderr}")

if __name__ == "__main__":
    abilita_python_completo()
    input("\nFine. Premi Invio...")
