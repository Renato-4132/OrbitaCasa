#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import time
import socket
import hashlib
import logging
import platform
import ctypes
import shutil
import html
import datetime
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk
from moduli.modello_spesa import SpesaEntry, campo, METODI_PAGAMENTO
from moduli.mappa_conti_trasferimenti import costruisci_mappa_conti_da_trasferimenti, conto_da_mappa, e_trasferimento_virtuale


def _fmt_it(v, spec=",.2f"):
    s = format(v, spec)
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")

def _saldo_effettivo_web(self, conto, db):
    oggi = datetime.date.today()
    nome = conto.get("nome", "")
    saldo = float(conto.get("saldo", 0))
    for d, voci in self.spese.items():
        if d > oggi:
            continue
        for v in voci:
            if campo(v, "conto", "") == nome:
                try:
                    imp = float(v[2])
                    saldo += imp if str(v[3]) == "Entrata" else -imp
                except Exception:
                    pass
    for t in db.get("trasferimenti", []):
        if e_trasferimento_virtuale(t):
            continue
        try:
            data_t = datetime.datetime.strptime(t["data"], "%d-%m-%Y").date()
        except Exception:
            continue
        if data_t > oggi:
            continue
        try:
            imp = round(float(t.get("importo", 0)), 2)
        except Exception:
            continue
        if t.get("da") == conto.get("id"):
            saldo -= imp
        elif t.get("a") == conto.get("id"):
            saldo += imp
    return saldo
