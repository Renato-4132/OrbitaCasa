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

def _fmt_it(v, spec=",.2f"):
    s = format(v, spec)
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")

# Apri WebServer nel Browser   
def apri_webserver(self):
    import __main__ as _app
    DB_DIR = _app.DB_DIR
    PORTA = _app.PORTA
    USA_SSL = _app.USA_SSL
    protocollo = "https" if USA_SSL and os.path.exists(os.path.join(DB_DIR, "cert.pem")) and os.path.exists(os.path.join(DB_DIR, "key.pem")) else "http"
    IP = self.get_ip_locale_reale()         
    url = f"{protocollo}://{IP}:{PORTA}"
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Apertura WebUI: {url}")
    webbrowser.open(url)

# Avvio Server Web Locale (Interfaccia HTTP-HTTPS)
def _crea_flask_app(self):
    import __main__ as _app
    ACCESS_CONTROL_WEB = _app.ACCESS_CONTROL_WEB
    API_KEY = _app.API_KEY
    APP_PASSWORD = _app.APP_PASSWORD
    DB_DIR = _app.DB_DIR
    DOC_DIR = _app.DOC_DIR
    DOC_PERS_DIR = _app.DOC_PERS_DIR
    EMAIL_USER = _app.EMAIL_USER
    FR_FILE = _app.FR_FILE
    LOGIN_LCL = _app.LOGIN_LCL
    LOGIN_WEB = _app.LOGIN_WEB
    LOGIN_WEB_FAIL = _app.LOGIN_WEB_FAIL
    PAROLE_CHIAVE = _app.PAROLE_CHIAVE
    REGISTRY_FILE = _app.REGISTRY_FILE
    UTENZE_DB = _app.UTENZE_DB
    from flask import Flask, request, redirect, make_response, Response, send_file
    import os, time, json, hashlib, logging, datetime as dt
    tk_app    = self
    flask_app = Flask(__name__)
    flask_app.secret_key = os.urandom(24)
    class _FiltroHTTP2(logging.Filter):
        def filter(self, record):
            return 'Invalid HTTP version' not in record.getMessage()
    logging.getLogger('werkzeug').addFilter(_FiltroHTTP2())
    
    def get_ip():
        return request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()

    def is_logged():
        token = request.cookies.get(f"session_id_{_app.PORTA}", "")
        ora   = time.time()
        return (token == tk_app.web_token and
                (ora - tk_app.ultimo_accesso_web) < tk_app.timeout_sessione)

    def touch():
        tk_app.ultimo_accesso_web = time.time()

    def html_resp(html, code=200):
        r = make_response(html, code)
        r.headers["Content-Type"]  = "text/html; charset=utf-8"
        r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        r.headers["Connection"]    = "close"
        return r

    def aggiorna_ui():
        if hasattr(tk_app, "update_spese_mese_corrente"):
            tk_app.after(0, tk_app.update_spese_mese_corrente)

    def richiede_login(f):
        from functools import wraps
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not is_logged():
                aveva = f"session_id_{_app.PORTA}" in request.cookies
                return redirect("/login?expired=1" if aveva else "/login", code=303)
            touch()
            return f(*args, **kwargs)
        return wrapper

    @flask_app.route("/ping")
    def ping():
        return Response("ok", mimetype="text/plain")

    @flask_app.route("/login")
    def login_get():
        r = html_resp(tk_app.html_login(request.full_path))
        r.set_cookie(f"session_id_{_app.PORTA}", "", max_age=0, httponly=True, samesite="Strict")
        return r

    @flask_app.route("/check_login", methods=["POST"])
    def check_login():
        pwd = request.form.get("password", "").strip()
        ora = time.time()
        try:
            if os.path.exists(ACCESS_CONTROL_WEB):
                with open(ACCESS_CONTROL_WEB, "r", encoding="utf-8") as f:
                    status_ban = json.load(f).get("web_user", {})
                if ora < status_ban.get("ban_until", 0):
                    return redirect("/login?error=banned", code=303)
        except Exception:
            pass
        ok  = (tk_app.salva_hash(pwd) or True
               if not tk_app.leggi_hash()
               else tk_app.verifica_password(pwd))
        ua  = request.headers.get("User-Agent", "sconosciuto")
        ip  = get_ip()
        if ok:
            tk_app.registra_accesso(ip=ip, user_agent=ua)
            tk_app.ultimo_accesso_web = time.time()
            resp = make_response(redirect("/", code=303))
            resp.set_cookie(f"session_id_{_app.PORTA}", tk_app.web_token,
                            max_age=tk_app.timeout_sessione,
                            httponly=True, samesite="Strict", secure=request.is_secure)
            return resp
        else:
            tk_app.registra_accesso_fallito(ip=ip, pwd_tentata=pwd, user_agent=ua)
            resp = make_response(redirect("/login?error=1", code=303))
            resp.set_cookie(f"session_id_{_app.PORTA}", "", max_age=0)
            return resp

    @flask_app.route("/logoff")
    def logoff():
        resp = make_response(tk_app.html_saluto())
        resp.headers["Content-Type"] = "text/html; charset=utf-8"
        resp.set_cookie(f"session_id_{_app.PORTA}", "", max_age=0,
                        httponly=True, samesite="Strict", secure=request.is_secure)
        return resp

    @flask_app.route("/")
    @richiede_login
    def home_get():
        return html_resp(tk_app.html_form())

    @flask_app.route("/", methods=["POST"])
    @richiede_login
    def home_post():
        d = request.form.get("data", "")
        if d:
            v = {"date": d,
                 "categoria":   request.form.get("categoria",   "Generica"),
                 "descrizione": request.form.get("descrizione", ""),
                 "importo":     float(request.form.get("importo", "0").replace(",", ".")),
                 "tipo":        request.form.get("tipo", "Uscita"),
                 "conto":       request.form.get("conto", "")}
            tk_app.aggiungi_voce_web(v)
            tk_app.save_db()
            aggiorna_ui()
            return redirect("/?salvato=1", code=303)
        return redirect("/", code=303)

    @flask_app.route("/gestione_categorie")
    @richiede_login
    def gestione_categorie():
        return html_resp(tk_app.html_gestione_categorie())

    @flask_app.route("/stats")
    @richiede_login
    def stats():
        return html_resp(tk_app.stats_mensili_html())

    @flask_app.route("/lista")
    @richiede_login
    def lista():
        return html_resp(tk_app.html_lista_spese_mensili())

    @flask_app.route("/scadenze_web")
    @richiede_login
    def scadenze_web():
        return html_resp(tk_app.html_scadenze_mese())

    @flask_app.route("/utenze")
    @richiede_login
    def utenze():
        anno = request.args.get("anno", str(dt.datetime.now().year))
        return html_resp(tk_app.genera_html_utenze(UTENZE_DB, anno))

    @flask_app.route("/salva_utenza_web", methods=["POST"])
    @richiede_login
    def salva_utenza_web():
        MESI_NOMI = ["Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno",
                     "Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"]
        utenza = request.form.get("utenza", "")
        anno   = request.form.get("anno", str(dt.datetime.now().year))
        if utenza not in ("Acqua", "Luce", "Gas"):
            return redirect(f"/utenze?anno={anno}", code=303)
        try:
            with open(UTENZE_DB, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {"letture_salvate": {}, "anagrafiche": {}}
        letture = data.setdefault("letture_salvate", {})
        letture.setdefault(utenza, {})
        righe = []
        for i, mese in enumerate(MESI_NOMI):
            prec_key = f"prec_{i}"
            att_key  = f"att_{i}"
            try:
                prec = float(request.form.get(prec_key, "0").replace(",", "."))
            except ValueError:
                prec = 0.0
            try:
                att = float(request.form.get(att_key, "0").replace(",", "."))
            except ValueError:
                att = 0.0
            cons = round(max(0.0, att - prec), 1)
            righe.append([f"{i+1:02d}/{anno}", prec, att, cons])
        letture[utenza][str(anno)] = righe
        try:
            with open(UTENZE_DB, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
        return redirect(f"/utenze?anno={anno}", code=303)

    @flask_app.route("/cerca_avanzata")
    @richiede_login
    def cerca_avanzata():
        params = {k: [v] for k, v in request.args.items()}
        return html_resp(tk_app.pagina_risultati_avanzati(params))

    @flask_app.route("/modifica")
    @richiede_login
    def modifica():
        params = {k: [v] for k, v in request.args.items()}
        return html_resp(tk_app.modifica_voce_form(params))

    @flask_app.route("/grafici_web")
    @richiede_login
    def grafici_web():
        return html_resp(tk_app.pagina_grafici_web())

    @flask_app.route("/fondo_risparmio_web", methods=["GET", "POST"])
    @richiede_login
    def fondo_risparmio_web():
        if request.method == "POST":
            action = request.form.get("action", "")
            try:
                if os.path.exists(FR_FILE):
                    with open(FR_FILE, "r", encoding="utf-8") as f:
                        fr_dati = json.load(f)
                else:
                    fr_dati = {"obiettivo_annuale": 0.0, "fondo_attuale": 0.0, "obiettivi": []}
            except Exception:
                fr_dati = {"obiettivo_annuale": 0.0, "fondo_attuale": 0.0, "obiettivi": []}
            if action == "salva_obiettivo":
                try:
                    fr_dati["obiettivo_annuale"] = float(request.form.get("obiettivo_annuale", "0").replace(",", "."))
                except ValueError:
                    pass
            elif action == "salva_fondo":
                try:
                    fr_dati["fondo_attuale"] = float(request.form.get("fondo_attuale", "0").replace(",", "."))
                except ValueError:
                    pass
            elif action == "aggiungi_obiettivo":
                nome = request.form.get("nome", "").strip()
                try:
                    importo = float(request.form.get("importo", "0").replace(",", "."))
                except ValueError:
                    importo = 0.0
                data_str = request.form.get("data_scadenza", "").strip()
                if nome and importo > 0 and data_str:
                    try:
                        parts = data_str.split("/")
                        dt = datetime.date(int(parts[1]), int(parts[0]), 1)
                        today_d = datetime.date.today()
                        mesi_disp = (dt.year - today_d.year) * 12 + (dt.month - today_d.month)
                        if mesi_disp > 0:
                            fr_dati.setdefault("obiettivi", []).append({
                                "nome": nome, "importo": importo,
                                "data": data_str, "mesi": mesi_disp,
                            })
                    except Exception:
                        pass
            elif action == "elimina_obiettivo":
                try:
                    idx = int(request.form.get("idx", -1))
                    obiettivi = fr_dati.get("obiettivi", [])
                    if 0 <= idx < len(obiettivi):
                        del obiettivi[idx]
                        fr_dati["obiettivi"] = obiettivi
                except (ValueError, IndexError):
                    pass
            try:
                os.makedirs(DB_DIR, exist_ok=True)
                with open(FR_FILE, "w", encoding="utf-8") as f:
                    json.dump(fr_dati, f, indent=2, ensure_ascii=False)
            except Exception:
                pass
            return redirect("/fondo_risparmio_web", code=303)
        return html_resp(tk_app.pagina_fondo_risparmio_web())

    @flask_app.route("/consultazione_supermercati")
    @richiede_login
    def consultazione_supermercati():
        return html_resp(tk_app.genera_html_consultazione())

    @flask_app.route("/documenti_personali_web")
    @richiede_login
    def documenti_personali_web():
        return html_resp(tk_app.documenti_personali_web())

    @flask_app.route("/documenti_pdf_web")
    @richiede_login
    def documenti_pdf_web():
        return html_resp(tk_app.documenti_pdf_web())

    @flask_app.route("/menu_esplora")
    @richiede_login
    def menu_esplora():
        return html_resp(tk_app.pagina_menu_esplora())

    @flask_app.route("/log_web")
    @richiede_login
    def log_web():
        return html_resp(tk_app.html_log_web())

    @flask_app.route("/cambia_pw_web")
    @richiede_login
    def cambia_pw_web():
        return html_resp(tk_app.html_cambia_pw_web())

    @flask_app.route("/fairshare_web")
    @richiede_login
    def fairshare_web():
        return html_resp(tk_app.html_fairshare_web())

    @flask_app.route("/get_fairshare_data")
    @richiede_login
    def get_fairshare_data():
        anno   = request.args.get("anno",   "0")
        mese   = request.args.get("mese",   "0")
        utente = request.args.get("utente", "tutti")
        return Response(tk_app.get_fairshare_data_json(anno, mese, utente),
                        mimetype="application/json; charset=utf-8")

    @flask_app.route("/info_sys_web")
    @richiede_login
    def info_sys_web():
        return html_resp(tk_app.html_info_sys())

    @flask_app.route("/get_pdf")
    @richiede_login
    def get_pdf():
        nome_file = request.args.get("file")
        if nome_file:
            nome_file = os.path.basename(nome_file)
            file_path = os.path.join(DOC_DIR, nome_file)
            if os.path.exists(file_path):
                return send_file(file_path, mimetype="application/pdf",
                                 download_name=nome_file, as_attachment=False)
        return Response("File non trovato", status=404)

    @flask_app.route("/get_pdf_pers")
    @richiede_login
    def get_pdf_pers():
        nome_file = request.args.get("file")
        profilo   = request.args.get("profilo")
        if nome_file:
            nome_file = os.path.basename(nome_file)
            profilo = os.path.basename(profilo) if profilo else None
            fp = (os.path.join(DOC_PERS_DIR, profilo, "documenti", nome_file)
                  if profilo else os.path.join(DOC_PERS_DIR, nome_file))
            if os.path.exists(fp):
                return send_file(fp, mimetype="application/pdf",
                                 download_name=nome_file, as_attachment=False)
        return Response("File non trovato", status=404)

    @flask_app.route("/log_action", methods=["POST"])
    @richiede_login
    def log_action():
        action = request.form.get("action", "")
        if action == "remove_ban":
            with open(ACCESS_CONTROL_WEB, "w", encoding="utf-8") as f:
                json.dump({"web_user": {"count": 0, "ban_until": 0, "last_attempt": 0}}, f)
        elif action == "clear_all":
            for lpath in [LOGIN_WEB, LOGIN_WEB_FAIL, LOGIN_LCL]:
                with open(lpath, "w", encoding="utf-8") as f:
                    json.dump([], f)
            with open(ACCESS_CONTROL_WEB, "w", encoding="utf-8") as f:
                json.dump({"web_user": {"count": 0, "ban_until": 0, "last_attempt": 0}}, f)
        return Response("ok", status=200)

    @flask_app.route("/check_cambia_pw", methods=["POST"])
    @richiede_login
    def check_cambia_pw():
        attuale  = request.form.get("attuale", "")
        nuova    = request.form.get("nuova", "")
        conferma = request.form.get("conferma", "")
        salvata  = tk_app.leggi_hash()
        if hashlib.sha256(attuale.encode()).hexdigest() != salvata:
            return redirect("/cambia_pw_web?error=1", code=303)
        if nuova != conferma:
            return redirect("/cambia_pw_web?error=2", code=303)
        tk_app.salva_hash(nuova)
        return redirect("/cambia_pw_web?ok=1", code=303)

    @flask_app.route("/salva_categoria", methods=["POST"])
    @richiede_login
    def salva_categoria():
        p  = {k: [v] for k, v in request.form.items()}
        op = request.form.get("operazione", "")
        if op == "aggiungi":
            tk_app.add_categoria_web(p)
        else:
            tk_app.modifica_categoria_web(p)
        tk_app.save_db()
        aggiorna_ui()
        return redirect("/gestione_categorie?status=success", code=303)

    @flask_app.route("/cancella_categoria", methods=["POST"])
    @richiede_login
    def cancella_categoria():
        p = {k: [v] for k, v in request.form.items()}
        tk_app.cancella_categoria_web(p)
        tk_app.save_db()
        aggiorna_ui()
        return redirect("/gestione_categorie?status=deleted", code=303)

    @flask_app.route("/salva_modifica", methods=["POST"])
    @richiede_login
    def salva_modifica():
        p = {k: [v] for k, v in request.form.items()}
        destinazione = tk_app.salva_modifica_voce(p)
        tk_app.save_db()
        aggiorna_ui()
        return redirect(destinazione, code=303)

    @flask_app.route("/cancella", methods=["POST"])
    @richiede_login
    def cancella():
        g = request.form.get("data", "")
        i = int(request.form.get("idx", -1))
        elimina_pdf = request.form.get("elimina_pdf", "0") == "1"
        if i != -1 and g:
            if elimina_pdf:
                try:
                    data_obj = datetime.datetime.strptime(g, "%d-%m-%Y").date()
                    if data_obj in tk_app.spese and 0 <= i < len(tk_app.spese[data_obj]):
                        voce = tk_app.spese[data_obj][i]
                        if "ALL·" in str(voce[1]):
                            o_s = data_obj.strftime("%d%m%Y")
                            o_i = str(int(round(float(voce[2]) * 100)))
                            o_t = voce[3]
                            if os.path.exists(REGISTRY_FILE):
                                with open(REGISTRY_FILE, 'r', encoding='utf-8') as rf:
                                    r = json.load(rf)
                                for f_k in list(r.keys()):
                                    if f_k.startswith(o_s) and o_i in f_k and o_t in f_k:
                                        pdf_path = os.path.join(DOC_DIR, f_k)
                                        if os.path.exists(pdf_path):
                                            os.remove(pdf_path)
                                        del r[f_k]
                                        break
                                with open(REGISTRY_FILE, 'w', encoding='utf-8') as rf:
                                    json.dump(r, rf, indent=4, ensure_ascii=False)
                except Exception as e:
                    print(f"[cancella] Errore rimozione PDF: {e}")
            tk_app.cancella_voce_web(g, i)
            tk_app.save_db()
        aggiorna_ui()
        return redirect("/", code=303)

    @flask_app.route("/avvia_sync_web", methods=["POST"])
    @richiede_login
    def avvia_sync_web():
        if not EMAIL_USER or "@gmail.com" not in EMAIL_USER.lower():
            return Response(json.dumps({"ok": False, "errore": "Gmail non configurata nelle impostazioni"}), status=200, mimetype="application/json")
        if not APP_PASSWORD or len(APP_PASSWORD.replace(" ", "")) != 16:
            return Response(json.dumps({"ok": False, "errore": "Password App Google non valida (16 cifre)"}), status=200, mimetype="application/json")
        if not API_KEY:
            return Response(json.dumps({"ok": False, "errore": "Chiave API Gemini mancante"}), status=200, mimetype="application/json")
        if not PAROLE_CHIAVE:
            return Response(json.dumps({"ok": False, "errore": "Nessuna email mittente configurata"}), status=200, mimetype="application/json")
        tk_app.after(0, lambda: tk_app.avvia_sincronizzazione(manuale=True))
        return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")

    @flask_app.route("/carica_pdf_web", methods=["POST"])
    @richiede_login
    def carica_pdf_web():
        if not API_KEY:
            return Response(json.dumps({"ok": False, "errore": "Chiave API Gemini mancante"}), status=200, mimetype="application/json")
        f = request.files.get("pdf_file")
        if not f or not f.filename.lower().endswith(".pdf"):
            return Response(json.dumps({"ok": False, "errore": "Seleziona un file PDF valido"}), status=200, mimetype="application/json")
        pdf_bytes = f.read()
        if len(pdf_bytes) > 20 * 1024 * 1024:
            return Response(json.dumps({"ok": False, "errore": "File troppo grande (max 20 MB)"}), status=200, mimetype="application/json")
        try:
            risultato = tk_app.analizza_pdf_web(pdf_bytes, f.filename)
            return Response(json.dumps(risultato, ensure_ascii=False), status=200, mimetype="application/json")
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                msg = "Limite giornaliero API Gemini raggiunto"
            elif "503" in err or "UNAVAILABLE" in err:
                msg = "Gemini sovraccarico, riprova tra poco"
            else:
                msg = f"Errore analisi: {err[:120]}"
            return Response(json.dumps({"ok": False, "errore": msg}), status=200, mimetype="application/json")

    @flask_app.route("/cambia_profilo_web")
    @richiede_login
    def cambia_profilo_web_page():
        return html_resp(tk_app.pagina_cambia_profilo_web())

    @flask_app.route("/switch_profilo_web", methods=["POST"])
    @richiede_login
    def switch_profilo_web_route():
        from urllib.parse import quote
        azione = request.form.get("azione", "switch")
        nome   = request.form.get("profilo", "").strip()
        risultato = tk_app.esegui_switch_profilo_web(nome, crea_nuovo=(azione == "nuovo"))
        if risultato.get("ok"):
            return html_resp(tk_app.pagina_switch_in_corso_web(risultato["profilo"], nuovo=risultato.get("nuovo", False)))
        return redirect(f"/cambia_profilo_web?errore={quote(risultato.get('errore', 'Errore sconosciuto'))}", code=303)

    from moduli.webauthn_login import aggiungi_rotte_webauthn
    aggiungi_rotte_webauthn(flask_app, tk_app, richiede_login, html_resp, get_ip, request)

    return flask_app

def start_web_server(self):
    import __main__ as _app
    DB_DIR = _app.DB_DIR
    MANDA_PUSH = _app.MANDA_PUSH
    NAME = _app.NAME
    USA_SSL = _app.USA_SSL
    from werkzeug.serving import make_server
    import ssl as ssl_mod, logging, socket
    def _porta_libera(porta):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("0.0.0.0", porta))
            return True
        except OSError:
            return False
        finally:
            s.close()
    if USA_SSL:
        self.genera_certificati_auto()
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    flask_app = self._crea_flask_app()
    while getattr(self, "_server_running", True):
        self.server = None
        try:
            while not _porta_libera(_app.PORTA):
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Porta {_app.PORTA} occupata, provo su {_app.PORTA + 1}...")
                _app.PORTA += 1
            cert_file = os.path.join(DB_DIR, "cert.pem")
            key_file  = os.path.join(DB_DIR, "key.pem")
            ssl_context = None
            if USA_SSL and os.path.exists(cert_file) and os.path.exists(key_file):
                ctx = ssl_mod.SSLContext(ssl_mod.PROTOCOL_TLS_SERVER)
                ctx.check_hostname = False
                ctx.verify_mode    = ssl_mod.CERT_NONE
                ctx.load_cert_chain(certfile=cert_file, keyfile=key_file)
                ssl_context = ctx
                protocollo  = "https"
            else:
                protocollo = "http"
            srv = make_server("0.0.0.0", _app.PORTA, flask_app,
                              threaded=True, ssl_context=ssl_context)
            srv.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            srv.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
            srv.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
            srv.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
            self.server = srv
            if hasattr(self, "lbl_webport"):
                self.after(0, lambda p=protocollo: self.lbl_webport.config(
                    text=f"Port: {_app.PORTA} ({p.upper()})"))
            if MANDA_PUSH:
                self.manda_push(f"⚠️ {NAME} Server",
                                f"{NAME} Risponde sulla porta {_app.PORTA} ({protocollo})")
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Web server Flask pronto su {protocollo}://localhost:{_app.PORTA}")
            srv.serve_forever()
        except (OSError, SystemExit):
            _app.PORTA += 1
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Porta occupata, provo su {_app.PORTA}...")
        except BaseException as e:
            import traceback
            msg = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Flask server crashato ({e})\n{traceback.format_exc()}"
            print(msg)
            try:
                log_path = os.path.join(DB_DIR, "error_log.txt")
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(msg + "\n")
            except Exception:
                pass
        finally:
            self.server = None
        if not getattr(self, "_server_running", True):
            break
        time.sleep(5)

# Invia una notifica push via Gmail su topic univoco derivato dal MAC address, con link diretto al webserver locale
def manda_push(self, titolo, messaggio):
    import __main__ as _app
    EMAIL_USER = _app.EMAIL_USER
    APP_PASSWORD = _app.APP_PASSWORD
    USA_SSL = _app.USA_SSL
    DB_DIR = _app.DB_DIR
    PORTA = _app.PORTA
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        if not EMAIL_USER or not APP_PASSWORD:
            self.show_toast("Email o AppPassword non configurate.", duration=2000)
            print(f"Email o password non configurate.")
            return False
        prot = "https" if USA_SSL and os.path.exists(os.path.join(DB_DIR, "cert.pem")) else "http"
        ip_reale = self.get_ip_locale_reale()
        link_web = f"{prot}://{ip_reale}:{PORTA}"
        msg = MIMEMultipart("alternative")
        msg["Subject"] = titolo
        msg["From"]    = EMAIL_USER
        msg["To"]      = EMAIL_USER
        corpo_testo = f"{messaggio}\n\n🔗 {link_web}"
        corpo_html  = f"""
        <html><body>
          <p>{messaggio}</p>
          <p><a href="{link_web}">🔗 Apri WebServer</a></p>
        </body></html>
        """
        msg.attach(MIMEText(corpo_testo, "plain"))
        msg.attach(MIMEText(corpo_html,  "html"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, APP_PASSWORD)
            server.sendmail(EMAIL_USER, EMAIL_USER, msg.as_string())
        self.show_toast("Indirizzo IP notificato con successo su Gmail.", duration=2000)
        print("-" * 50)
        print(f"📧 EMAIL INVIATA!")
        print(f"📬 A: {EMAIL_USER}")
        print(f"📌 OGGETTO: {titolo}")
        print(f"💬 MESSAGGIO: {messaggio}")
        print(f"🌐 LINK: {link_web}")
        print("-" * 50)
        return True
    except Exception as e:
        self.show_toast("Errore SMTP: controlla connessione e credenziali.", duration=3000)
        print(f"Errore invio email: {e}")
        return False

# HTML Login
def html_login(self, path):
    import __main__ as _app
    DB_DIR = _app.DB_DIR
    LOGIN_WEB = _app.LOGIN_WEB
    NAME = _app.NAME
    VERSION = _app.VERSION
    ora = time.time()
    is_banned = False
    secondi_restanti = 0
    current_count = 0
    ultimo_login = "Benvenuto nel tuo spazio sicuro"
    BAN_FILE = globals().get('ACCESS_CONTROL_WEB', os.path.join(DB_DIR, "web_access_control.json"))
    if os.path.exists(BAN_FILE):
        try:
            with open(BAN_FILE, "r") as f:
                  data = json.load(f)
                  status = data.get("web_user", {})
                  current_count = status.get("count", 0)
                  ban_until = status.get("ban_until", 0)
                  last_attempt = status.get("last_attempt", 0)
            if ora < ban_until:
                  is_banned = True
                  secondi_restanti = int(ban_until - ora)
            elif ban_until != 0 or (last_attempt != 0 and ora - last_attempt > 300 and current_count > 0):
                  current_count = 0
                  data["web_user"] = {"count": 0, "ban_until": 0, "last_attempt": 0}
                  with open(BAN_FILE, "w") as f:
                      json.dump(data, f, indent=4)
        except:
                  pass
    SESSION_ID = self.SESSION_ID
    ultimo_login = "Benvenuto nel tuo spazio sicuro"
    if os.path.exists(LOGIN_WEB):
        try:
            with open(LOGIN_WEB, "r", encoding="utf-8") as f:
                logs = json.load(f)
                if len(logs) > 1:
                    ultimo_login = f"Ultimo accesso: {logs[1]['data_ora']}"
                elif len(logs) == 1:
                    ultimo_login = f"Ultimo accesso: {logs[0]['data_ora']}"
        except: pass
    PROFILO_ATTIVO = _app.PROFILO_ATTIVO
    folder = (PROFILO_ATTIVO if PROFILO_ATTIVO != "Principale" else os.path.basename(os.getcwd()))
    if is_banned:
            current_count = 3 
            contenuto_centrale = f"""
            <div class="ban-ui" style="display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 200px; text-align: center;">
                    <div id="fase-badge" style="display: block; opacity: 1; transition: opacity 0.5s;">
                            <div class="fail-badge" style="color: #ff4444; font-size: 20px; font-weight: bold; margin-bottom: 10px;">
                                    🚫 Tentativi esauriti: 3/3
                            </div>
                            <div style="font-size: 14px; opacity: 0.8;">Accesso temporaneamente bloccato</div>
                    </div>
                    <div id="fase-timer" style="display: none; opacity: 0; transition: opacity 0.5s;">
                            <div class="ban-icon" style="font-size: 48px; margin-bottom: 10px;">🛡️</div>
                            <div class="ban-title" style="margin-bottom: 15px;">Accesso Bloccato</div>
                            <div class="ban-timer-box" style="background: rgba(255,255,255,0.05); padding: 15px; border-radius: 10px;">
                                    <div class="ban-timer-label" style="font-size: 13px; margin-bottom: 5px;">Riprova tra</div>
                                    <div id="countdown_timer" class="ban-timer" style="font-size: 28px; font-weight: bold; color: #ffcc00;">--:--</div>
                            </div>
                    </div>
            </div>
            <script>
            setTimeout(function() {{
                    var badge = document.getElementById('fase-badge');
                    var timer = document.getElementById('fase-timer');
                    badge.style.opacity = '0';
                    setTimeout(function() {{
                            badge.style.display = 'none';
                            timer.style.display = 'block';
                            setTimeout(() => {{ 
                                    timer.style.opacity = '1'; 
                                    if (typeof startTimer === 'function') {{
                                            startTimer({secondi_restanti});
                                    }}
                            }}, 50);
                    }}, 500);
            }}, 1000);
            </script>
            """
    else:
        fail_badge = ""
        if current_count > 0:
            fail_badge = f'<div class="fail-badge">⚠️ Tentativi falliti: {current_count}/3</div>'
        contenuto_centrale = f"""
        <div class="profilo-row">
            <span class="profilo-name">{folder}</span>
            <span class="profilo-sub">{ultimo_login}</span>
        </div>
        <form method="post" action="/check_login" id="loginForm">
            <div class="field-label" style="margin-bottom:4px;">Chiave di Accesso</div>
            <div class="input-wrap">
                <input type="password" name="password" id="pass" autofocus autocomplete="off" placeholder="••••••••">
                <span class="toggle-pass" onclick="togglePassword()">👁️</span>
            </div>
            <div class="badge-slot">{fail_badge}</div>
            <button type="submit" class="btn-submit">ACCEDI 🔓</button>
        </form>
        <button id="btnBiometrico" type="button" class="btn-submit" style="display:none; margin-top:8px;" onclick="accediBiometrico()">👆 Accesso Biometrico</button>
        <div id="msgBiometrico" style="font-size:12px; text-align:center; margin-top:6px; min-height:16px;"></div>
        <script>
        function b64uToBuf(s) {{
            s = s.replace(/-/g, '+').replace(/_/g, '/');
            while (s.length % 4) s += '=';
            const bin = atob(s);
            const buf = new Uint8Array(bin.length);
            for (let i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
            return buf.buffer;
        }}
        function bufToB64u(buf) {{
            const bytes = new Uint8Array(buf);
            let bin = '';
            for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
            return btoa(bin).replace(/\\+/g, '-').replace(/\\//g, '_').replace(/=+$/, '');
        }}
        (async function initBiometrico() {{
            if (!window.PublicKeyCredential) return;
            try {{
                const r = await fetch('/webauthn/login/opzioni');
                if (r.status === 404) return; // nessun dispositivo registrato
                if (!r.ok) return;
                document.getElementById('btnBiometrico').style.display = 'block';
            }} catch (e) {{}}
        }})();
        async function accediBiometrico() {{
            const msg = document.getElementById('msgBiometrico');
            msg.textContent = 'Attendi la richiesta del browser...';
            try {{
                const optResp = await fetch('/webauthn/login/opzioni');
                const opts = await optResp.json();
                if (opts.errore) {{ msg.textContent = '⚠️ ' + opts.errore; return; }}
                opts.challenge = b64uToBuf(opts.challenge);
                if (opts.allowCredentials) opts.allowCredentials.forEach(c => c.id = b64uToBuf(c.id));
                const cred = await navigator.credentials.get({{ publicKey: opts }});
                const payload = {{
                    id: cred.id,
                    rawId: bufToB64u(cred.rawId),
                    type: cred.type,
                    response: {{
                        clientDataJSON: bufToB64u(cred.response.clientDataJSON),
                        authenticatorData: bufToB64u(cred.response.authenticatorData),
                        signature: bufToB64u(cred.response.signature),
                        userHandle: cred.response.userHandle ? bufToB64u(cred.response.userHandle) : null,
                    }}
                }};
                const verResp = await fetch('/webauthn/login/verifica', {{
                    method: 'POST', headers: {{'Content-Type': 'application/json'}}, body: JSON.stringify(payload)
                }});
                const risultato = await verResp.json();
                if (risultato.ok) {{
                    window.location.href = '/';
                }} else {{
                    msg.textContent = '⚠️ ' + (risultato.errore || 'Accesso non riuscito.');
                }}
            }} catch (e) {{
                msg.textContent = '⚠️ ' + e.message;
            }}
        }}
        </script>
        """
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>🔓 Login — {NAME}</title>
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<script>
    (function() {{
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    }})();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg: #050505; --surface: #0f0f0f; --surface2: #161616;
        --border: rgba(255,255,255,0.07); --gold: #c9a84c; --blue: #63a0f0;
        --green: #4caf82; --red: #e05a5a; --text: #e8e8e8;
        --text-dim: #555; --text-mid: #888; --radius-lg: 18px;
    }}
    :root.light {{
        --bg: #f5f5f0; --surface: #ffffff; --surface2: #f0efe8;
        --border: rgba(0,0,0,0.09); --gold: #b8902a; --blue: #3d7fd4;
        --green: #3a9068; --red: #cc3333; --text: #1a1a1a;
        --text-dim: #999; --text-mid: #555;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        font-family: 'DM Sans', sans-serif; background: var(--bg); color: var(--text);
        min-height: 100vh; min-height: 100dvh;
        display: flex; flex-direction: column; align-items: center; justify-content: flex-start;
        padding: 16px 12px; transition: background 0.3s, color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 50% at 50% -5%, rgba(99,160,240,0.09) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 90%, rgba(201,168,76,0.05) 0%, transparent 60%);
    }}
    .main-container {{
        width: 100%; max-width: 420px;
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius-lg); overflow: hidden; position: relative;
        box-shadow: 0 20px 60px rgba(0,0,0,0.6); animation: fadeIn 0.3s ease;
    }}
    :root.light .main-container {{ box-shadow: 0 8px 40px rgba(0,0,0,0.12); }}
    .main-container::before {{
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(10px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .brand-header {{ padding: 16px 20px 12px; border-bottom: 1px solid var(--border); position: relative; }}
    .brand-title {{ font-family: 'DM Sans', sans-serif; font-size: 1.2em; font-weight: 800; color: var(--gold); letter-spacing: 0.5px; margin-bottom: 2px; }}
    .brand-tagline {{ font-size: 0.75em; color: var(--text-dim); }}
    .theme-toggle {{
        position: absolute; top: 14px; right: 16px;
        background: var(--surface2); border: 1px solid var(--border);
        border-radius: 8px; width: 34px; height: 34px;
        display: flex; align-items: center; justify-content: center;
        cursor: pointer; font-size: 1em; transition: all 0.2s;
    }}
    .theme-toggle:hover {{ border-color: var(--gold); }}
    .icon-bar {{
        display: flex; justify-content: space-between;
        margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border);
    }}
    @media (max-height: 560px) {{ .icon-bar {{ display: none; }} }}
    .icon-item {{ display: flex; flex-direction: column; align-items: center; gap: 3px; }}
    .icon-item span {{ font-size: 1.3em; }}
    .icon-label {{ font-size: 0.6em; color: var(--text-dim); text-transform: uppercase; font-weight: 700; letter-spacing: 0.8px; }}
    .login-content {{ padding: 12px 20px 14px; }}
    .profilo-row {{
        display: flex; align-items: baseline; gap: 8px;
        margin-bottom: 10px; padding-bottom: 10px; border-bottom: 1px solid var(--border);
    }}
    .profilo-name {{ font-family: 'DM Sans', sans-serif; font-size: 1em; font-weight: 700; color: var(--text); }}
    .profilo-sub {{ font-size: 0.7em; color: var(--text-dim); }}
    .field-label {{ font-size: 0.65em; font-weight: 600; color: var(--text-dim); letter-spacing: 2px; text-transform: uppercase; margin-bottom: 4px; }}
    .input-wrap {{ position: relative; border-bottom: 1px solid var(--border); transition: border-color 0.2s; }}
    .input-wrap:focus-within {{ border-bottom-color: var(--gold); }}
    input[type="password"], input[type="text"] {{
        width: calc(100% - 36px); background: transparent; border: none; outline: none;
        padding: 10px 0; font-family: 'DM Sans', sans-serif; font-size: 1.1em;
        color: var(--text); letter-spacing: 2px;
    }}
    input::placeholder {{ color: var(--text-dim); letter-spacing: 1px; font-size: 0.9em; }}
    input.error-state {{ color: var(--red) !important; font-weight: bold; letter-spacing: 1px; }}
    .toggle-pass {{
        position: absolute; right: 0; top: 50%; transform: translateY(-50%);
        cursor: pointer; font-size: 1.1em; opacity: 0.5; transition: opacity 0.15s;
    }}
    .toggle-pass:hover {{ opacity: 1; }}
    .badge-slot {{ height: 28px; display: flex; align-items: center; margin-top: 4px; }}
    .fail-badge {{
        display: inline-block; background: rgba(224,90,90,0.1);
        border: 1px solid rgba(224,90,90,0.25); color: var(--red);
        font-size: 0.72em; font-weight: 600; padding: 3px 9px; border-radius: 6px;
    }}
    .btn-submit {{
        width: 100%; padding: 14px;
        background: linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color: #000; border: none; border-radius: 10px;
        font-family: 'DM Sans', sans-serif; font-size: 0.95em; font-weight: 700;
        line-height: 1.5; letter-spacing: 1px; cursor: pointer; transition: all 0.2s; margin-top: 6px;
    }}
    .btn-submit:hover {{ transform: translateY(-1px); box-shadow: 0 6px 18px rgba(201,168,76,0.25); }}
    .btn-submit:active {{ transform: translateY(0); }}
    .ban-ui {{ text-align: center; padding: 8px 0 14px; }}
    .ban-icon {{ font-size: 2.2em; margin-bottom: 8px; }}
    .ban-title {{ font-family: 'DM Sans', sans-serif; font-size: 1.05em; font-weight: 700; color: var(--red); margin-bottom: 12px; }}
    .ban-timer-box {{ display: inline-block; background: var(--surface2); border: 1px solid var(--border); border-radius: 10px; padding: 10px 24px; }}
    .ban-timer {{ font-family: 'DM Sans', sans-serif; font-size: 1.8em; font-weight: 800; color: var(--red); letter-spacing: 2px; }}
    .ban-timer-label {{ font-size: 0.62em; color: var(--text-dim); letter-spacing: 2px; text-transform: uppercase; margin-bottom: 2px; }}
    .login-footer {{ padding: 10px 20px 14px; border-top: 1px solid var(--border); }}
    .footer-link {{ display: block; font-size: 0.65em; color: var(--text-dim); text-decoration: none; margin-bottom: 8px; }}
    .footer-link span {{ color: var(--blue); }}
    .footer-boxes {{ display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }}
    .legal-box, .security-box {{ background: var(--surface2); border: 1px solid var(--border); border-radius: 8px; padding: 7px 10px; }}
    .legal-title, .security-title {{ font-size: 0.6em; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 3px; }}
    .legal-title {{ color: var(--red); }}
    .security-title {{ color: var(--blue); }}
    .legal-text, .security-text {{ font-size: 0.67em; color: var(--text-dim); line-height: 1.4; }}
</style>
</head>
<body>
<div class="main-container">
    <div class="brand-header">
        <div class="brand-title">🏠 {NAME} </div>
        <div class="brand-tagline">La tua finanza domestica, in perfetto ordine.</div>
        <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
        <div class="icon-bar">
            <div class="icon-item"><span>📈</span><div class="icon-label">Finanza</div></div>
            <div class="icon-item"><span>💰</span><div class="icon-label">Risparmio</div></div>
            <div class="icon-item"><span>🛒</span><div class="icon-label">Spesa</div></div>
            <div class="icon-item"><span>⚡</span><div class="icon-label">Utenze</div></div>
            <div class="icon-item"><span>📂</span><div class="icon-label">Documenti</div></div>
        </div>
    </div>
    <div class="login-content">
        {contenuto_centrale}
    </div>
    <div class="login-footer">
        <a href="mailto:helporbitacasa@gmail.com" class="footer-link">
            v{VERSION} · S-ID: {SESSION_ID} · Supporto: <span>helporbitacasa@gmail.com</span>
        </a>
        <div class="footer-boxes">
            <div class="legal-box">
                <div class="legal-title">⚠️ Avviso Legale</div>
                <div class="legal-text">Accesso non autorizzato perseguibile ai sensi dell'<strong>Art. 615-ter C.P.</strong> Ogni tentativo sarà perseguito a tutela dei dati.</div>
            </div>
            <div class="security-box">
                <div class="security-title">🛡️ Sicurezza Sessione</div>
                <div class="security-text">Protetto da <strong>Token Dinamico</strong>. Accessi monitorati e archiviati per sicurezza.</div>
            </div>
        </div>
    </div>
</div>
<script>
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{
            root.classList.add('light');
            if (btn) btn.textContent = '🌙';
        }} else {{
            root.classList.remove('light');
            if (btn) btn.textContent = '☀️';
        }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        applyTheme(next);
    }}
    applyTheme(localStorage.getItem('theme') || 'dark');
    function togglePassword() {{
        var x = document.getElementById("pass");
        if (x) x.type = (x.type === "password") ? "text" : "password";
    }}
    var passInput = document.getElementById('pass');
    if (passInput) {{
        passInput.addEventListener('focus', function() {{
            setTimeout(function() {{
                var btn = document.querySelector('.btn-submit');
                if (btn) btn.scrollIntoView({{behavior: 'smooth', block: 'nearest'}});
            }}, 350);
        }});
    }}
    if ({'true' if is_banned else 'false'}) {{
        var timeleft = {secondi_restanti};
        var timerElem = document.getElementById("countdown_timer");
        var downloadTimer = setInterval(function() {{
            if (timeleft <= 0) {{
                clearInterval(downloadTimer);
                window.location.href = window.location.pathname;
            }}
            var m = Math.floor(timeleft / 60);
            var s = timeleft % 60;
            if (timerElem) timerElem.innerHTML = (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
            timeleft -= 1;
        }}, 1000);
    }}
    
    window.onload = function() {{
        const urlParams = new URLSearchParams(window.location.search);
        const passInput = document.getElementById("pass");
        if (window.history.replaceState)
            window.history.replaceState({{}}, document.title, window.location.pathname);
        if (urlParams.has('expired')) {{
            if (passInput) {{
                passInput.type = "text";
                passInput.value = "🔒 Sessione scaduta!";
                passInput.classList.add("error-state");
                setTimeout(() => {{
                    passInput.value = "";
                    passInput.type = "password";
                    passInput.classList.remove("error-state");
                    passInput.focus();
                }}, 1800);
            }}
        }} else if (urlParams.has('error')) {{
            if (passInput) {{
                passInput.type = "text";
                passInput.value = "⛈️ Password errata!";
                passInput.classList.add("error-state");
                passInput.readOnly = true;
                setTimeout(() => {{
                    passInput.value = "";
                    passInput.type = "password";
                    passInput.classList.remove("error-state");
                    passInput.readOnly = false;
                    passInput.focus();
                }}, 1200);
            }}
        }}
    }};
    
</script>
</body>
</html>"""

# Html cambia password
def html_cambia_pw_web(self):
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>🔑 Cambia Password</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
    (function() {{
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    }})();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg: #050505; --surface: #0f0f0f; --surface2: #161616; --surface3: #1e1e1e;
        --border: rgba(255,255,255,0.07); --gold: #c9a84c; --blue: #63a0f0;
        --green: #4caf82; --red: #e05a5a; --text: #e8e8e8;
        --text-dim: #555; --text-mid: #888; --radius-lg: 18px;
    }}
    :root.light {{
        --bg: #f5f5f0; --surface: #ffffff; --surface2: #f0efe8; --surface3: #e8e7df;
        --border: rgba(0,0,0,0.09); --gold: #b8902a; --blue: #3d7fd4;
        --green: #3a9068; --red: #cc3333; --text: #1a1a1a; --text-dim: #999; --text-mid: #555;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        font-family: 'DM Sans', sans-serif; background: var(--bg); color: var(--text);
        min-height: 100vh; min-height: 100dvh;
        display: flex; flex-direction: column; align-items: center;
        padding: 24px 16px; transition: background 0.3s, color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 50% at 50% -5%, rgba(99,160,240,0.09) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 90%, rgba(201,168,76,0.05) 0%, transparent 60%);
    }}
    .main-container {{
        width: 100%; max-width: 400px;
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius-lg); overflow: hidden; position: relative;
        box-shadow: 0 20px 60px rgba(0,0,0,0.6); animation: fadeIn 0.3s ease;
    }}
    :root.light .main-container {{ box-shadow: 0 8px 40px rgba(0,0,0,0.12); }}
    .main-container::before {{
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(10px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .brand-header {{
        padding: 16px 20px 14px; border-bottom: 1px solid var(--border);
        display: flex; align-items: center; justify-content: space-between;
    }}
    .brand-title {{ font-size: 1.1em; font-weight: 800; color: var(--gold); }}
    .theme-toggle {{
        background: var(--surface2); border: 1px solid var(--border);
        border-radius: 8px; width: 34px; height: 34px;
        display: flex; align-items: center; justify-content: center;
        cursor: pointer; font-size: 1em; transition: all 0.2s;
    }}
    .theme-toggle:hover {{ border-color: var(--gold); }}
    .form-body {{ padding: 20px; }}
    .field-label {{
        font-size: 0.65em; font-weight: 600; color: var(--text-dim);
        letter-spacing: 2px; text-transform: uppercase; margin-bottom: 5px; margin-top: 14px;
    }}
    .field-label:first-child {{ margin-top: 0; }}
    .input-wrap {{
        position: relative; border-bottom: 1px solid var(--border); transition: border-color 0.2s;
    }}
    .input-wrap:focus-within {{ border-bottom-color: var(--gold); }}
    input[type="password"], input[type="text"] {{
        width: calc(100% - 36px); background: transparent; border: none; outline: none;
        padding: 10px 0; font-family: 'DM Sans', sans-serif; font-size: 1em;
        color: var(--text); letter-spacing: 2px;
    }}
    input::placeholder {{ color: var(--text-dim); letter-spacing: 1px; font-size: 0.9em; }}
    .toggle-pass {{
        position: absolute; right: 0; top: 50%; transform: translateY(-50%);
        cursor: pointer; font-size: 1em; opacity: 0.5; transition: opacity 0.15s;
    }}
    .toggle-pass:hover {{ opacity: 1; }}
    .btn-submit {{
        width: 100%; padding: 13px; margin-top: 22px;
        background: linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color: #000; border: none; border-radius: 10px;
        font-family: 'DM Sans', sans-serif; font-size: 0.95em; font-weight: 700;
        letter-spacing: 0.5px; cursor: pointer; transition: all 0.2s;
    }}
    .btn-submit:hover {{ transform: translateY(-1px); box-shadow: 0 6px 18px rgba(201,168,76,0.25); }}
    .msg {{ text-align: center; font-size: 0.82em; padding: 10px 0 0; display: none; }}
    .msg-ok {{ color: var(--green); }}
    .msg-err {{ color: var(--red); }}
    .footer {{ padding: 14px 20px; border-top: 1px solid var(--border); text-align: center; }}
    .back-link {{ font-size: 0.75em; color: var(--text-dim); text-decoration: none; transition: color 0.2s; }}
    .back-link:hover {{ color: var(--blue); }}
    .btn-home {{
        display: block; text-align: center; padding: 14px;
        background: linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color: #000; border-radius: 10px; text-decoration: none;
        font-family: 'DM Sans', sans-serif; font-weight: 700; font-size: 0.9em;
        line-height: 1.5; letter-spacing: 0.5px; margin-top: 4px; transition: all 0.2s;
    }}
    .btn-home:hover {{ transform: translateY(-1px); box-shadow: 0 6px 20px rgba(201,168,76,0.25); }}
</style>
</head>
<body>
<div class="main-container">
    <div class="brand-header">
        <div class="brand-title">🔑 Cambia Password</div>
        <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()">🌙</button>
    </div>
    <div class="form-body">
        <form method="post" action="/check_cambia_pw" id="pwForm">
            <div class="field-label">Password Attuale</div>
            <div class="input-wrap">
                <input type="password" name="attuale" id="attuale" autofocus placeholder="••••••••">
                <span class="toggle-pass" onclick="toggleVis('attuale')">👁️</span>
            </div>
            <div class="field-label">Nuova Password</div>
            <div class="input-wrap">
                <input type="password" name="nuova" id="nuova" placeholder="••••••••">
                <span class="toggle-pass" onclick="toggleVis('nuova')">👁️</span>
            </div>
            <div class="field-label">Conferma Nuova</div>
            <div class="input-wrap">
                <input type="password" name="conferma" id="conferma" placeholder="••••••••">
                <span class="toggle-pass" onclick="toggleVis('conferma')">👁️</span>
            </div>
            <div class="msg msg-err" id="msg_err"></div>
            <div class="msg msg-ok" id="msg_ok"></div>
            <button type="submit" class="btn-submit">AGGIORNA PASSWORD 🔐</button>
        </form>
    </div>
    <div class="footer">
        <a href="/" class="btn-home">🏠 Torna alla Home</a>
    </div>
</div>
<script>
    function toggleVis(id) {{
        const el = document.getElementById(id);
        el.type = el.type === 'password' ? 'text' : 'password';
    }}
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if (btn) btn.textContent = '🌙'; }}
        else               {{ root.classList.remove('light'); if (btn) btn.textContent = '☀️'; }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        applyTheme(next);
    }}
    applyTheme(localStorage.getItem('theme') || 'dark');
    const p = new URLSearchParams(window.location.search);
    if (p.get('error') === '1') {{
        const el = document.getElementById('msg_err');
        el.textContent = '❌ Password attuale errata!';
        el.style.display = 'block';
    }}
    if (p.get('error') === '2') {{
        const el = document.getElementById('msg_err');
        el.textContent = '❌ Le password non corrispondono!';
        el.style.display = 'block';
    }}
    if (p.get('ok') === '1') {{
        const el = document.getElementById('msg_ok');
        el.textContent = '✅ Password aggiornata con successo!';
        el.style.display = 'block';
        setTimeout(() => {{ window.location.href = '/info_sys_web'; }}, 2000);
    }}
</script>
</body>
</html>"""

# Html Log 
def html_log_web(self):
    import __main__ as _app
    ACCESS_CONTROL_WEB = _app.ACCESS_CONTROL_WEB
    LOGIN_LCL = _app.LOGIN_LCL
    LOGIN_WEB = _app.LOGIN_WEB
    LOGIN_WEB_FAIL = _app.LOGIN_WEB_FAIL
    import json, os, time
    def carica_json(path):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return []
    def carica_access_control():
        if os.path.exists(ACCESS_CONTROL_WEB):
            try:
                with open(ACCESS_CONTROL_WEB, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}
    web_ok = [r for r in carica_json(LOGIN_WEB) if isinstance(r, dict)]
    righe_ok = ""
    for r in reversed(web_ok):
        ua = r.get("browser", "")
        extra = f'<span class="log-extra">🌐 {ua}</span>' if ua else ""
        righe_ok += f"""
            <div class="log-row">
                <span class="log-data">{r.get("data_ora","N/D")}</span>
                <span class="log-ip">{r.get("ip","N/D")}</span>
                {extra}
            </div>"""
    if not righe_ok:
        righe_ok = '<p class="no-logs">Nessun accesso registrato</p>'
    web_fail = [r for r in carica_json(LOGIN_WEB_FAIL) if isinstance(r, dict)]
    righe_fail = ""
    for r in reversed(web_fail):
        ua = r.get("browser", "")
        extra = f'<span class="log-extra">🌐 {ua}</span>' if ua else ""
        righe_fail += f"""
            <div class="log-row">
                <span class="log-data">{r.get("data_ora","N/D")}</span>
                <span class="log-ip log-red">{r.get("ip","N/D")}</span>
                <span class="log-user log-red">🔑 {r.get("pwd_tentata","")}</span>
                {extra}
            </div>"""
    if not righe_fail:
        righe_fail = '<p class="no-logs">Nessun tentativo fallito</p>'
    lcl = carica_json(LOGIN_LCL)
    if isinstance(lcl, dict):
        lcl = lcl.get("eventi", [])
    lcl = [r for r in lcl if isinstance(r, dict)]
    righe_lcl = ""
    for r in reversed(lcl):
        tipo = r.get("tipo", "")
        if "ok" in tipo.lower() or "success" in tipo.lower():
            tipo_class = "log-green"
        elif "fail" in tipo.lower():
            tipo_class = "log-red"
        else:
            tipo_class = ""
        righe_lcl += f"""
        <div class="log-row">
            <span class="log-data">{r.get("timestamp","N/D")}</span>
            <span class="log-ip {tipo_class}">{tipo}</span>
            <span class="log-user">{r.get("utente","")}</span>
            <span class="log-extra">{r.get("password_tentata","")}</span>
        </div>"""
    if not righe_lcl:
        righe_lcl = '<p class="no-logs">Nessun login locale registrato</p>'
    ac = carica_access_control()
    user = ac.get("web_user", {})
    count = user.get("count", 0)
    ban_until = user.get("ban_until", 0)
    ora = time.time()
    if ban_until > ora:
        restanti = int(ban_until - ora)
        stato_ban = f"🔴 Bannato — sblocco tra {restanti // 60}m {restanti % 60}s"
        ban_class = "ban-red"
    else:
        stato_ban = "🟢 Libero"
        ban_class = "ban-green"
    count_class = "ban-red" if count > 0 else "ban-green"
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>📋 Log Accessi</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
    (function() {{
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    }})();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg: #050505; --surface: #0f0f0f; --surface2: #161616; --surface3: #1e1e1e;
        --border: rgba(255,255,255,0.07); --gold: #c9a84c; --blue: #63a0f0;
        --green: #4caf82; --red: #e05a5a; --text: #e8e8e8;
        --text-dim: #555; --text-mid: #888; --radius-lg: 18px;
    }}
    :root.light {{
        --bg: #f5f5f0; --surface: #ffffff; --surface2: #f0efe8; --surface3: #e8e7df;
        --border: rgba(0,0,0,0.09); --gold: #b8902a; --blue: #3d7fd4;
        --green: #3a9068; --red: #cc3333; --text: #1a1a1a; --text-dim: #999; --text-mid: #555;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        font-family: 'DM Sans', sans-serif; background: var(--bg); color: var(--text);
        min-height: 100vh; padding-bottom: 40px; transition: background 0.3s, color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 40% at 50% -10%, rgba(99,160,240,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 60%);
    }}
    header {{
        padding: 16px 16px 12px; display: flex; align-items: center; justify-content: center;
        border-bottom: 1px solid var(--border); background: rgba(5,5,5,0.95);
        backdrop-filter: blur(20px); position: sticky; top: 0; z-index: 100;
    }}
    :root.light header {{ background: rgba(245,245,240,0.95); }}
    .back-btn {{
        position: absolute; left: 16px; top: 50%; transform: translateY(-50%);
        background: var(--surface3); border: 1px solid var(--border); color: var(--gold);
        padding: 6px 14px; border-radius: 10px; font-size: 0.85em;
        cursor: pointer; text-decoration: none; transition: all 0.2s;
    }}
    .back-btn:hover {{ border-color: var(--gold); box-shadow: 0 0 12px rgba(201,168,76,0.2); }}
    .header-title {{ font-size: 1em; font-weight: 700; color: var(--text); }}
    .theme-toggle {{
        position: absolute; right: 16px; top: 50%; transform: translateY(-50%);
        background: var(--surface3); border: 1px solid var(--border);
        border-radius: 8px; width: 34px; height: 34px;
        display: flex; align-items: center; justify-content: center;
        cursor: pointer; font-size: 1em; transition: all 0.2s;
    }}
    .theme-toggle:hover {{ border-color: var(--gold); }}
    main {{ padding: 14px; max-width: 600px; margin: 0 auto; animation: fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    .tabs {{ display: flex; gap: 6px; margin-bottom: 10px; flex-wrap: wrap; }}
    .tab-btn {{
        padding: 7px 14px; border-radius: 10px; border: 1px solid var(--border);
        background: var(--surface2); color: var(--text-mid); font-size: 0.82em;
        cursor: pointer; transition: all 0.2s; font-family: 'DM Sans', sans-serif;
    }}
    .tab-btn.active {{ background: var(--surface3); border-color: var(--gold); color: var(--text); }}
    .tab-btn:hover {{ border-color: var(--blue); color: var(--text); }}
    .tab-content {{ display: none; }}
    .tab-content.active {{ display: block; }}
    .card {{
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius-lg); overflow: hidden; position: relative;
    }}
    .card::before {{
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .card-title {{
        font-size: 0.7em; font-weight: 700; color: var(--text-dim);
        letter-spacing: 2px; text-transform: uppercase;
        padding: 12px 16px 8px; border-bottom: 1px solid var(--border);
        display: flex; justify-content: space-between; align-items: center;
    }}
    .count-badge {{
        background: var(--surface3); border: 1px solid var(--border);
        border-radius: 20px; padding: 2px 10px; font-size: 0.9em; color: var(--text-mid);
    }}
    .log-row {{
        display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
        padding: 9px 16px; border-bottom: 1px solid var(--border); font-size: 0.83em;
    }}
    .log-row:last-child {{ border-bottom: none; }}
    .log-data {{ color: var(--text-mid); min-width: 130px; }}
    .log-ip {{ color: var(--blue); min-width: 100px; }}
    .log-user {{ color: var(--text); font-weight: 600; }}
    .log-extra {{ color: var(--text-mid); font-size: 0.9em; }}
    .log-red {{ color: var(--red) !important; }}
    .log-green {{ color: var(--green) !important; }}
    .no-logs {{ text-align: center; padding: 24px; color: var(--text-mid); font-size: 0.88em; }}
    .ban-card {{
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius-lg); padding: 20px; position: relative; overflow: hidden;
    }}
    .ban-card::before {{
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .ban-row {{
        padding: 10px 0; border-bottom: 1px solid var(--border);
        font-size: 0.9em; display: flex; justify-content: space-between;
    }}
    .ban-row:last-child {{ border-bottom: none; }}
    .ban-label {{ color: var(--text-mid); }}
    .ban-red {{ color: var(--red); font-weight: 700; }}
    .ban-green {{ color: var(--green); font-weight: 700; }}
    .action-btns {{ display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }}
    .btn-action {{
        flex: 1; padding: 11px; border-radius: 10px; border: 1px solid var(--border);
        background: var(--surface2); color: var(--text-mid); font-size: 0.85em;
        cursor: pointer; transition: all 0.2s; font-family: 'DM Sans', sans-serif; text-align: center;
    }}
    .btn-action:hover {{ border-color: var(--blue); color: var(--text); }}
    .btn-action.danger:hover {{ border-color: var(--red); color: var(--red); }}
    .modal-overlay {{
        display: none; position: fixed; inset: 0;
        background: rgba(0,0,0,0.75); z-index: 999;
        align-items: center; justify-content: center;
    }}
    .modal-box {{
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius-lg); padding: 24px 20px;
        width: 90%; max-width: 340px; position: relative; overflow: hidden;
        animation: fadeIn 0.2s ease;
    }}
    .modal-box::before {{
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .modal-title {{ font-size: 1em; font-weight: 700; color: var(--text); margin-bottom: 8px; }}
    .modal-text {{ font-size: 0.85em; color: var(--text-mid); margin-bottom: 20px; line-height: 1.5; }}
    .modal-btns {{ display: flex; gap: 8px; }}
    .m-btn {{
        flex: 1; padding: 10px; border-radius: 10px; border: 1px solid var(--border);
        font-family: 'DM Sans', sans-serif; font-size: 0.85em; font-weight: 600;
        cursor: pointer; transition: all 0.2s;
    }}
    .m-cancel {{ background: var(--surface2); color: var(--text-mid); }}
    .m-cancel:hover {{ border-color: var(--blue); color: var(--text); }}
    .m-confirm {{ background: var(--surface2); color: var(--red); border-color: rgba(224,90,90,0.3); }}
    .m-confirm:hover {{ background: rgba(224,90,90,0.1); border-color: var(--red); }}
</style>
</head>
<body>
<header>
    <a href="/info_sys_web" class="back-btn">← Monitor</a>
    <div class="header-title">📋 Log Accessi</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()">🌙</button>
</header>
<main>
    <div class="tabs">
        <button class="tab-btn active" onclick="switchTab('web_ok', this)">✅ WEB OK</button>
        <button class="tab-btn" onclick="switchTab('web_fail', this)">❌ WEB Falliti</button>
        <button class="tab-btn" onclick="switchTab('lcl', this)">🖥️ Locali</button>
        <button class="tab-btn" onclick="switchTab('ban', this)">🛡️ Ban</button>
    </div>
    <div id="tab_web_ok" class="tab-content active">
        <div class="card">
            <div class="card-title">
                ✅ Accessi WEB riusciti
                <span class="count-badge">{len(web_ok)}</span>
            </div>
            {righe_ok}
        </div>
    </div>
    <div id="tab_web_fail" class="tab-content">
        <div class="card">
            <div class="card-title">
                ❌ Tentativi falliti
                <span class="count-badge">{len(web_fail)}</span>
            </div>
            {righe_fail}
        </div>
    </div>

    <div id="tab_lcl" class="tab-content">
        <div class="card">
            <div class="card-title">
                🖥️ Login Locali
                <span class="count-badge">{len(lcl)}</span>
            </div>
            {righe_lcl}
        </div>
    </div>
    <div id="tab_ban" class="tab-content">
        <div class="ban-card">
            <div class="ban-row">
                <span class="ban-label">Tentativi falliti correnti</span>
                <span class="{count_class}">{count}</span>
            </div>
            <div class="ban-row">
                <span class="ban-label">Stato</span>
                <span class="{ban_class}">{stato_ban}</span>
            </div>
        </div>
        <div class="action-btns">
            <button class="btn-action" onclick="apriModal('ban')">🔓 Rimuovi Ban</button>
            <button class="btn-action danger" onclick="apriModal('clear')">🗑️ Azzera Tutti i Log</button>
        </div>
    </div>
</main>
<div id="deleteModal" class="modal-overlay">
    <div class="modal-box">
        <div class="modal-title" id="modalTitle"></div>
        <div class="modal-text" id="modalText"></div>
        <div class="modal-btns">
            <button class="m-btn m-cancel" onclick="closeDeleteModal()">Annulla</button>
            <button id="finalDeleteBtn" class="m-btn m-confirm">Conferma</button>
        </div>
    </div>
</div>
<script>
    function switchTab(name, btn) {{
        document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.getElementById('tab_' + name).classList.add('active');
        btn.classList.add('active');
    }}
    function apriModal(tipo) {{
        var title = document.getElementById('modalTitle');
        var text  = document.getElementById('modalText');
        var btn   = document.getElementById('finalDeleteBtn');
        if (tipo === 'ban') {{
            title.textContent = '🔓 Rimuovi Ban';
            text.textContent  = 'Vuoi rimuovere il ban e azzerare i tentativi falliti?';
            btn.onclick = function() {{
                closeDeleteModal();
                fetch('/log_action', {{method:'POST', headers:{{'Content-Type':'application/x-www-form-urlencoded'}}, body:'action=remove_ban'}})
                .then(() => location.reload());
            }};
        }} else {{
            title.textContent = '🗑️ Azzera Tutti i Log';
            text.textContent  = 'Operazione irreversibile. Tutti i log e il ban verranno cancellati definitivamente.';
            btn.onclick = function() {{
                closeDeleteModal();
                fetch('/log_action', {{method:'POST', headers:{{'Content-Type':'application/x-www-form-urlencoded'}}, body:'action=clear_all'}})
                .then(() => location.reload());
            }};
        }}
        document.getElementById('deleteModal').style.cssText = 'display:flex;';
    }}
    function closeDeleteModal() {{
        document.getElementById('deleteModal').style.display = 'none';
    }}
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if (btn) btn.textContent = '🌙'; }}
        else               {{ root.classList.remove('light'); if (btn) btn.textContent = '☀️'; }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        applyTheme(next);
    }}
    applyTheme(localStorage.getItem('theme') || 'dark');
</script>
</body>
</html>"""

# Html Movimenti Mese Web
def pagina_risultati_avanzati(self, params):
    from datetime import datetime
    from collections import defaultdict
    import html as html_escape
    categoria_filtro = params.get("categoria", [""])[0].strip().lower()
    anno = params.get("anno", [""])[0].strip()
    mese = params.get("mese", [""])[0].strip()
    tipo = params.get("tipo", [""])[0].strip().lower()
    min_importo = float(params.get("min_importo", ["0"])[0] or 0)
    max_importo = float(params.get("max_importo", ["999999"])[0] or 999999)
    query = params.get("q", [""])[0].strip().lower()
    risultati_categorizzati = defaultdict(list)
    for data in sorted(self.spese.keys(), reverse=True):
        if anno and str(data.year) != anno:
            continue
        if mese and f"{data.month:02d}" != mese:
            continue
        for idx_voce, voce in enumerate(self.spese[data]):
            if len(voce) < 4:
                continue
            cat, descrizione, importo, tipo_voce = voce[:4]
            if categoria_filtro and cat.strip().lower() != categoria_filtro:
                continue
            if tipo and tipo_voce.strip().lower() != tipo:
                continue
            if not (min_importo <= importo <= max_importo):
                continue
            if query and not (
                query in descrizione.lower()
                or query in tipo_voce.lower()
                or query in cat.lower()
                or query in str(importo)
            ):
                continue
            risultati_categorizzati[cat].append({
                "data": data.strftime("%d-%m-%Y"),
                "desc": html_escape.escape(descrizione),
                "imp": float(importo),
                "tipo": tipo_voce.strip(),
                "idx": idx_voce,
                "cat": cat
            })
    entrate_totali = sum(v["imp"] for vlist in risultati_categorizzati.values() for v in vlist if v["tipo"].lower() == "entrata")
    uscite_totali = sum(v["imp"] for vlist in risultati_categorizzati.values() for v in vlist if v["tipo"].lower() != "entrata")
    saldo = entrate_totali - uscite_totali
    colore_saldo = "#4caf82" if saldo >= 0 else "#e05a5a"
    segno_saldo = "+" if saldo >= 0 else ""
    anno_corrente = datetime.now().year
    schede_html = ""
    for cat, voci in sorted(risultati_categorizzati.items()):
        totale_cat = sum(v["imp"] if v["tipo"].lower() == "entrata" else -v["imp"] for v in voci)
        colore_tot = "#4caf82" if totale_cat >= 0 else "#e05a5a"
        simbolo_tot = "+" if totale_cat >= 0 else "−"
        voce_html = ""
        for v in voci:
            simbolo = "+" if v["tipo"].lower() == "entrata" else "−"
            colore_tipo = "#4caf82" if v["tipo"].lower() == "entrata" else "#e05a5a"
            voce_html += f"""
            <li class="voce-item">
                <div class="voce-actions">
                    <form method="get" action="/modifica" style="display:inline;">
                        <input type="hidden" name="data" value="{v['data']}">
                        <input type="hidden" name="idx" value="{v['idx']}">
                        <input type="hidden" name="from" value="/cerca_avanzata">
                        <button type="submit" class="btn-action btn-edit">✏️</button>
                    </form>
                    <button type="button" class="btn-action btn-delete"
                        onclick="apriModal('{v['data']}', '{v['idx']}', '{v['cat'].replace("'", "\\'")}', '{_fmt_it(v['imp'])}', {'1' if 'ALL·' in v['desc'] else '0'})">❌</button>
                    <span class="voce-data">{v['data']}</span>
                </div>
                <div class="voce-body">
                    <span class="voce-imp" style="color:{colore_tipo}">€ {simbolo}{_fmt_it(v['imp'])}</span>
                    <span class="voce-tipo" style="color:{colore_tipo}">{v['tipo']}</span>
                    <div class="voce-desc">{v['desc']}</div>
                </div>
            </li>"""
        schede_html += f"""
        <div class="cat-block">
            <button class="cat-toggle" onclick="toggleCategoria(this)">
                <span class="freccia">▶</span>
                <span class="cat-name">{html_escape.escape(cat)}</span>
                <span class="cat-totale" style="color:{colore_tot}">€ {simbolo_tot}{_fmt_it(abs(totale_cat))} · {len(voci)} voci</span>
            </button>
            <div class="cat-content">
                <ul class="voce-list">{voce_html}</ul>
            </div>
        </div>"""
    nessun_risultato = "" if schede_html else "<div class='empty-msg'>Nessuna voce trovata.</div>"
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>🔍 Risultati Ricerca</title>
<script>
    (function() {{
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    }})();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg: #050505; --surface: #0f0f0f; --surface2: #161616; --surface3: #1e1e1e;
        --border: rgba(255,255,255,0.07); --border-active: rgba(99,160,240,0.5);
        --gold: #c9a84c; --blue: #63a0f0; --green: #4caf82; --red: #e05a5a;
        --text: #e8e8e8; --text-dim: #555; --text-mid: #888; --radius-lg: 18px;
    }}
    :root.light {{
        --bg: #f5f5f0; --surface: #ffffff; --surface2: #f0efe8; --surface3: #e8e7df;
        --border: rgba(0,0,0,0.09); --gold: #b8902a; --blue: #3d7fd4;
        --green: #3a9068; --red: #cc3333; --text: #1a1a1a; --text-dim: #999; --text-mid: #555;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        font-family: 'DM Sans', sans-serif; background: var(--bg); color: var(--text);
        min-height: 100vh; padding-bottom: 50px; transition: background 0.3s, color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 40% at 50% -10%, rgba(99,160,240,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 60%);
    }}
    header {{
        padding: 18px 20px 14px; display: flex; align-items: center; justify-content: center;
        border-bottom: 1px solid var(--border); background: rgba(5,5,5,0.95);
        backdrop-filter: blur(20px); position: sticky; top: 0; z-index: 100;
    }}
    :root.light header {{ background: rgba(245,245,240,0.95); }}
    .menu-btn {{
        position: absolute; left: 16px; top: 50%; transform: translateY(-50%);
        background: var(--surface3); border: 1px solid var(--border); color: var(--gold);
        width: 38px; height: 38px; border-radius: 10px; font-size: 1.1em;
        cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s;
    }}
    .menu-btn:hover {{ border-color: var(--gold); box-shadow: 0 0 14px rgba(201,168,76,0.2); }}
    .header-title {{ font-family: 'DM Sans', sans-serif; font-size: 1.05em; font-weight: 700; color: var(--text); }}
    .theme-toggle {{
        position: absolute; right: 16px; top: 50%; transform: translateY(-50%);
        background: var(--surface3); border: 1px solid var(--border);
        border-radius: 8px; width: 34px; height: 34px;
        display: flex; align-items: center; justify-content: center;
        cursor: pointer; font-size: 1em; transition: all 0.2s;
    }}
    .theme-toggle:hover {{ border-color: var(--gold); }}
    .nav-dropdown {{
        position: absolute; top: calc(100% + 8px); left: 10px;
        background: var(--surface2); border: 1px solid var(--border);
        border-radius: var(--radius-lg); display: none; z-index: 1000;
        width: 275px; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.7);
    }}
    .nav-dropdown a {{
        display: flex; align-items: center; gap: 10px; padding: 11px 18px;
        text-decoration: none; color: var(--text-mid); border-bottom: 1px solid var(--border);
        font-size: 0.88em; transition: all 0.15s;
    }}
    .nav-dropdown a:last-child {{ border-bottom: none; }}
    .nav-dropdown a:hover {{ background: var(--surface3); color: var(--text); padding-left: 24px; }}
    .nav-group-btn {{ display:flex; justify-content:space-between; align-items:center; width:100%;
        padding:8px 16px; background:none; border:none; font-family:inherit; color:var(--gold);
        font-size:0.7em; font-weight:700; letter-spacing:1px; text-transform:uppercase; cursor:pointer; opacity:0.85; }}
    .nav-group-btn:hover {{ opacity:1; background:var(--surface3); }}
    .nav-arrow {{ font-size:0.85em; transition:transform 0.15s; }}
    .nav-group-items {{ display:none; flex-direction:column; }}
    .nav-group-items.open {{ display:flex; }}
    main {{ padding: 16px; max-width: 640px; margin: 0 auto; animation: fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    .riepilogo {{
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius-lg); margin: 16px 0; overflow: hidden; position: relative;
    }}
    .riepilogo::before {{
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .riepilogo-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; }}
    .riepilogo-item {{ padding: 16px 12px; text-align: center; border-right: 1px solid var(--border); }}
    .riepilogo-item:last-child {{ border-right: none; }}
    .riepilogo-item small {{ display: block; font-size: 0.65em; color: var(--text-dim); letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 5px; }}
    .riepilogo-item b {{ font-size: 0.95em; font-weight: 600; }}
    .cat-block {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); margin-bottom: 10px; overflow: hidden; }}
    .cat-toggle {{ width: 100%; background: none; border: none; padding: 14px 18px; display: flex; align-items: center; gap: 10px; cursor: pointer; text-align: left; transition: background 0.15s; }}
    .cat-toggle:hover {{ background: var(--surface2); }}
    .freccia {{ font-size: 0.7em; color: var(--text-dim); transition: transform 0.2s; min-width: 12px; }}
    .cat-name {{ font-family: 'DM Sans', sans-serif; font-size: 0.9em; font-weight: 700; color: var(--text); flex: 1; }}
    .cat-totale {{ font-size: 0.82em; font-weight: 600; white-space: nowrap; }}
    .cat-content {{ display: none; border-top: 1px solid var(--border); }}
    .voce-list {{ list-style: none; padding: 0; margin: 0; }}
    .voce-item {{ padding: 12px 18px; border-bottom: 1px solid var(--border); }}
    .voce-item:last-child {{ border-bottom: none; }}
    .voce-actions {{ display: flex; align-items: center; gap: 6px; margin-bottom: 6px; }}
    .btn-action {{ background: var(--surface2); border: 1px solid var(--border); border-radius: 6px; padding: 4px 8px; cursor: pointer; font-size: 0.8em; transition: all 0.15s; }}
    .btn-action:hover {{ background: var(--surface3); border-color: rgba(255,255,255,0.15); }}
    .voce-data {{ font-size: 0.78em; color: var(--text-mid); margin-left: 4px; font-weight: 500; }}
    .voce-body {{ padding-left: 2px; }}
    .voce-imp {{ font-size: 1.05em; font-weight: 700; margin-right: 8px; }}
    .voce-tipo {{ font-size: 0.75em; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; opacity: 0.8; }}
    .voce-desc {{ font-size: 0.82em; color: var(--text-mid); margin-top: 3px; }}
    .btn-nav {{
        display: block; text-align: center; padding: 14px; border-radius: 10px;
        text-decoration: none; font-family: 'DM Sans', sans-serif; font-weight: 700;
        font-size: 0.9em; line-height: 1.5; cursor: pointer; border: none;
        width: 100%; margin-bottom: 10px; transition: all 0.2s;
    }}
    .btn-gold {{ background: linear-gradient(135deg, var(--gold) 0%, #8a6820 100%); color: #000; }}
    .btn-outline {{ background: var(--surface); border: 1px solid var(--border); color: var(--text-mid); }}
    .btn-nav:hover {{ transform: translateY(-1px); box-shadow: 0 6px 20px rgba(0,0,0,0.3); }}
    .empty-msg {{ text-align: center; padding: 40px 20px; color: var(--text-dim); font-size: 0.9em; letter-spacing: 1px; }}
    #deleteModal {{
        display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0,0,0,0.8); backdrop-filter: blur(6px); z-index: 3000;
        align-items: center; justify-content: center;
    }}
    .modal-box {{
        background: var(--surface2); border: 1px solid var(--border); padding: 28px 24px;
        border-radius: var(--radius-lg); width: 85%; max-width: 340px;
        text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.6);
    }}
    .modal-box h3 {{ font-family: 'DM Sans', sans-serif; font-size: 1.05em; color: var(--red); margin-bottom: 12px; }}
    .modal-box p {{ color: var(--text-mid); font-size: 0.87em; line-height: 1.5; }}
    .modal-actions {{ display: flex; gap: 10px; margin-top: 22px; justify-content: center; }}
    .btn-ok {{ background: var(--red); color: white; border: none; padding: 11px 24px; border-radius: 8px; font-weight: 700; font-family: 'DM Sans', sans-serif; cursor: pointer; font-size: 0.87em; line-height: 1.5; }}
    .btn-no {{ background: var(--surface3); color: var(--text-mid); border: 1px solid var(--border); padding: 11px 24px; border-radius: 8px; cursor: pointer; font-size: 0.87em; line-height: 1.5; }}
</style>
</head>
<body>
<div id="deleteModal" style="display:none;">
    <div class="modal-box">
        <h3>🗑️ Conferma Eliminazione</h3>
        <p id="modalText"></p>
        <div class="modal-actions">
            <button class="btn-no" onclick="closeModal()">Annulla</button>
            <button class="btn-ok" id="finalDeleteBtn">Elimina</button>
        </div>
    </div>
</div>
<div id="pdfModal" style="display:none; position:fixed; z-index:9999; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.75); align-items:center; justify-content:center;">
    <div class="modal-box">
        <h3>ALL· Documento Allegato</h3>
        <p>Vuoi eliminare anche il documento PDF dal registro?</p>
        <div class="modal-actions">
            <button class="btn-no" onclick="confermaCancella(0)">Solo Movimento</button>
            <button class="btn-ok" onclick="confermaCancella(1)">Elimina Tutto</button>
        </div>
    </div>
</div>
<header>
    <button class="menu-btn" onclick="toggleMenu()">⚙️</button>
    <div id="extraMenu" class="nav-dropdown">
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Finanze</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/">🏠 Aggiungi Operazione</a>
                <a href="/lista">📈 Gestione Movimenti Mese</a>
                <a href="/stats">📊 Bilancio Mese</a>
                <a href="/fondo_risparmio_web">💰 Fondo Risparmio</a>
                <a href="/scadenze_web">📅 Scadenze del Mese</a>
                <a href="/fairshare_web">⚖️ FairShare</a>
                <a href="/menu_esplora">🔍 Esplora</a>
                <a href="/grafici_web">📅 Grafici e Statistiche</a>
                <a href="/gestione_categorie">⚙️ Gestione Categorie</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Casa</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/utenze?anno={anno_corrente}">💧 Utenze</a>
                <a href="/consultazione_supermercati">🛒 Gestione Supermercati</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Documenti</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/documenti_pdf_web">🗄️ Documenti Contabili</a>
                <a href="/documenti_personali_web">🗄️ Documenti Personali</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Sistema</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/info_sys_web">📡 Monitor Server</a>
                <a href="/cambia_pw_web">🔑 Cambia Password</a>
                <a href="/webauthn_web">👆 Biometrico</a>
                <a href="/cambia_profilo_web">👤 Cambia Profilo</a>
                <a href="/logoff">🔓 Logout</a>
            </div>
        </div>
    </div>
    <div class="header-title">🔍 Risultati Ricerca</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="riepilogo">
        <div class="riepilogo-grid">
            <div class="riepilogo-item">
                <small>Entrate</small>
                <b style="color:var(--green)">€ {_fmt_it(entrate_totali)}</b>
            </div>
            <div class="riepilogo-item">
                <small>Uscite</small>
                <b style="color:var(--red)">€ {_fmt_it(uscite_totali)}</b>
            </div>
            <div class="riepilogo-item">
                <small>Saldo</small>
                <b style="color:{colore_saldo}">€ {segno_saldo}{_fmt_it(saldo)}</b>
            </div>
        </div>
    </div>
    {schede_html}
    {nessun_risultato}
    <div style="margin-top: 20px;">
        <form method="get" action="/menu_esplora">
            <button type="submit" class="btn-nav btn-gold">🔙 Torna al Menu Esplora</button>
        </form>
        <form method="get" action="/">
            <button type="submit" class="btn-nav btn-outline">🏠 Torna alla Home</button>
        </form>
    </div>
</main>
<script>
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if (btn) btn.textContent = '🌙'; }}
        else               {{ root.classList.remove('light'); if (btn) btn.textContent = '☀️'; }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        applyTheme(next);
    }}
    applyTheme(localStorage.getItem('theme') || 'dark');
    let dData = null, dIdx = null, dHaPdf = false;
    function apriModal(data, idx, cat, imp, ha_pdf) {{
        dData = data; dIdx = idx; dHaPdf = (ha_pdf === '1' || ha_pdf === 1);
        document.getElementById("modalText").innerHTML = "Eliminare <b>" + cat + "</b> — <b>€ " + imp + "</b>?";
        document.getElementById("deleteModal").style.display = "flex";
    }}
    function closeModal() {{ document.getElementById("deleteModal").style.display = "none"; }}
    document.getElementById("finalDeleteBtn").onclick = function() {{
        closeModal();
        if (dHaPdf) {{
            document.getElementById("pdfModal").style.display = "flex";
        }} else {{
            confermaCancella(0);
        }}
    }};
    function confermaCancella(elimina_pdf) {{
        document.getElementById("pdfModal").style.display = "none";
        fetch('/cancella', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
            body: 'data=' + encodeURIComponent(dData) + '&idx=' + encodeURIComponent(dIdx) + '&elimina_pdf=' + elimina_pdf
        }}).then(() => window.location.reload());
    }}
    function toggleNavGroup(btn, ev) {{
        if (ev) ev.stopPropagation();
        const items = btn.nextElementSibling;
        const giaAperto = items.classList.contains('open');
        btn.closest('.nav-dropdown').querySelectorAll('.nav-group-items.open').forEach(function(el) {{
            el.classList.remove('open');
            el.previousElementSibling.querySelector('.nav-arrow').textContent = '▶';
        }});
        if (!giaAperto) {{
            items.classList.add('open');
            btn.querySelector('.nav-arrow').textContent = '▼';
        }}
    }}
    function toggleMenu() {{
        const m = document.getElementById("extraMenu");
        m.style.display = m.style.display === "block" ? "none" : "block";
    }}
    function toggleCategoria(btn) {{
        const content = btn.nextElementSibling;
        const isVisible = content.style.display === "block";
        content.style.display = isVisible ? "none" : "block";
        btn.querySelector(".freccia").textContent = isVisible ? "▶" : "▼";
    }}
    document.addEventListener("click", function(e) {{
        const menu = document.getElementById("extraMenu");
        const btn = document.querySelector(".menu-btn");
        if (menu && menu.style.display === "block" && !menu.contains(e.target) && e.target !== btn)
            menu.style.display = "none";
    }});
</script>
</body>
</html>"""

# Html Info sistema
def html_info_sys(self):
    import __main__ as _app
    DB_FILE = _app.DB_FILE
    LOGIN_WEB = _app.LOGIN_WEB
    NAME = _app.NAME
    VERSION = _app.VERSION
    import shutil, sys, multiprocessing, datetime, platform, os, json
    PROFILO_ATTIVO = _app.PROFILO_ATTIVO
    folder = (PROFILO_ATTIVO if PROFILO_ATTIVO != "Principale" else os.path.basename(os.getcwd())).upper()
    sistema = platform.system()
    os_name = "Windows" if sistema == "Windows" else "Linux" if sistema == "Linux" else "Mac" if sistema == "Darwin" else sistema
    arch = platform.machine()
    nome_pc = platform.node().upper()
    python_v = platform.python_version()
    ora_server = datetime.datetime.now().strftime("%H:%M - %d/%m/%Y")
    anno_corrente = datetime.datetime.now().year
    ram_info = "N/D"
    try:
        if sistema == "Windows":
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("sullAvailExtendedPhys", ctypes.c_ulonglong)]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(stat)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            ram_info = f"{round(stat.ullAvailPhys/1024**3, 1)}GB liberi / {round(stat.ullTotalPhys/1024**3, 1)}GB"
        else:
            with open('/proc/meminfo', 'r') as f:
                m = {l.split(':')[0]: int(l.split()[1]) for l in f.readlines()[:3]}
            ram_info = f"{round(m.get('MemAvailable', m.get('MemFree'))/1024**2, 1)}GB liberi / {round(m['MemTotal']/1024**2, 1)}GB"
    except: pass
    try:
        t, u, f = shutil.disk_usage("/")
        disco = f"{f // (2**30)}GB liberi ({(u/t)*100:.0f}% uso)"
        peso_db = f"{os.path.getsize(DB_FILE) / (1024**2):.1f}MB" if os.path.exists(DB_FILE) else "0MB"
    except: disco = peso_db = "N/D"
    ultimo_log = "Primo accesso"
    if os.path.exists(LOGIN_WEB):
        try:
            with open(LOGIN_WEB, "r", encoding="utf-8") as f:
                logs = json.load(f)
                ultimo_log = logs[1]['data_ora'] if len(logs) > 1 else ultimo_log
        except: pass
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]; s.close()
    except: ip = "127.0.0.1"
    porta = getattr(_app, 'PORTA', "8080")
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>📡 Monitor Server</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
    (function() {{
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    }})();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg: #050505; --surface: #0f0f0f; --surface2: #161616; --surface3: #1e1e1e;
        --border: rgba(255,255,255,0.07); --gold: #c9a84c; --blue: #63a0f0;
        --green: #4caf82; --red: #e05a5a; --text: #e8e8e8;
        --text-dim: #555; --text-mid: #888; --radius-lg: 18px;
    }}
    :root.light {{
        --bg: #f5f5f0; --surface: #ffffff; --surface2: #f0efe8; --surface3: #e8e7df;
        --border: rgba(0,0,0,0.09); --gold: #b8902a; --blue: #3d7fd4;
        --green: #3a9068; --red: #cc3333; --text: #1a1a1a; --text-dim: #999; --text-mid: #555;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        font-family: 'DM Sans', sans-serif; background: var(--bg); color: var(--text);
        min-height: 100vh; padding-bottom: 40px; transition: background 0.3s, color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 40% at 50% -10%, rgba(99,160,240,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 60%);
    }}
    header {{
        padding: 16px 16px 12px; display: flex; align-items: center; justify-content: center;
        border-bottom: 1px solid var(--border); background: rgba(5,5,5,0.95);
        backdrop-filter: blur(20px); position: sticky; top: 0; z-index: 100;
    }}
    :root.light header {{ background: rgba(245,245,240,0.95); }}
    .menu-btn {{
        position: absolute; left: 16px; top: 50%; transform: translateY(-50%);
        background: var(--surface3); border: 1px solid var(--border); color: var(--gold);
        width: 36px; height: 36px; border-radius: 10px; font-size: 1em;
        cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s;
    }}
    .menu-btn:hover {{ border-color: var(--gold); box-shadow: 0 0 12px rgba(201,168,76,0.2); }}
    .header-title {{ font-family: 'DM Sans', sans-serif; font-size: 1em; font-weight: 700; color: var(--text); }}
    .theme-toggle {{
        position: absolute; right: 16px; top: 50%; transform: translateY(-50%);
        background: var(--surface3); border: 1px solid var(--border);
        border-radius: 8px; width: 34px; height: 34px;
        display: flex; align-items: center; justify-content: center;
        cursor: pointer; font-size: 1em; transition: all 0.2s;
    }}
    .theme-toggle:hover {{ border-color: var(--gold); }}
    .nav-dropdown {{
        position: absolute; top: calc(100% + 6px); left: 10px;
        background: var(--surface2); border: 1px solid var(--border);
        border-radius: var(--radius-lg); display: none; z-index: 1000;
        width: 270px; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.7);
    }}
    .nav-dropdown a {{
        display: flex; align-items: center; gap: 10px; padding: 10px 16px;
        text-decoration: none; color: var(--text-mid); border-bottom: 1px solid var(--border);
        font-size: 0.87em; transition: all 0.15s;
    }}
    .nav-dropdown a:last-child {{ border-bottom: none; }}
    .nav-dropdown a:hover {{ background: var(--surface3); color: var(--text); padding-left: 22px; }}
    .nav-group-btn {{ display:flex; justify-content:space-between; align-items:center; width:100%;
        padding:8px 16px; background:none; border:none; font-family:inherit; color:var(--gold);
        font-size:0.7em; font-weight:700; letter-spacing:1px; text-transform:uppercase; cursor:pointer; opacity:0.85; }}
    .nav-group-btn:hover {{ opacity:1; background:var(--surface3); }}
    .nav-arrow {{ font-size:0.85em; transition:transform 0.15s; }}
    .nav-group-items {{ display:none; flex-direction:column; }}
    .nav-group-items.open {{ display:flex; }}
    main {{ padding: 14px 14px 0; max-width: 560px; margin: 0 auto; animation: fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    .card {{
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius-lg); margin-bottom: 10px; overflow: hidden; position: relative;
    }}
    .card::before {{
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .card-title {{
        font-family: 'DM Sans', sans-serif; font-size: 0.7em; font-weight: 700;
        color: var(--text-dim); letter-spacing: 2px; text-transform: uppercase;
        padding: 12px 16px 8px; border-bottom: 1px solid var(--border);
    }}
    .row {{
        display: flex; justify-content: space-between; align-items: center;
        padding: 9px 16px; border-bottom: 1px solid var(--border); font-size: 0.88em;
    }}
    .row:last-child {{ border-bottom: none; }}
    .row span {{ color: var(--text-mid); }}
    .row b {{ color: var(--text); font-weight: 600; }}
    .log-card {{
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius-lg); margin-bottom: 10px; overflow: hidden; position: relative;
    }}
    .log-card::before {{
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .log-inner {{ padding: 14px 16px; }}
    .log-folder {{ font-family: 'DM Sans', sans-serif; font-size: 1em; font-weight: 800; color: var(--gold); margin-bottom: 4px; }}
    .log-time {{ font-size: 0.8em; color: var(--text-mid); }}
    .log-links {{ display: flex; flex-wrap: wrap; gap: 10px; padding: 10px 16px; border-top: 1px solid var(--border); }}
    .log-link {{
        display: flex; align-items: center; gap: 6px; text-decoration: none;
        background: var(--surface2); border: 1px solid var(--border);
        border-radius: 8px; padding: 7px 14px; font-size: 0.8em; color: var(--text-mid); transition: all 0.15s;
    }}
    .log-link:hover {{ border-color: var(--blue); color: var(--text); }}
    .log-timestamp {{ text-align: center; font-size: 0.68em; color: var(--text-dim); padding: 8px 16px 12px; letter-spacing: 1px; }}
    .btn-home {{
        display: block; text-align: center; padding: 14px;
        background: linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color: #000; border-radius: 10px; text-decoration: none;
        font-family: 'DM Sans', sans-serif; font-weight: 700; font-size: 0.9em;
        line-height: 1.5; letter-spacing: 0.5px; margin-top: 4px; transition: all 0.2s;
    }}
    .btn-home:hover {{ transform: translateY(-1px); box-shadow: 0 6px 20px rgba(201,168,76,0.25); }}
</style>
</head>
<body>
<header>
    <button class="menu-btn" onclick="toggleMenu()">⚙️</button>
    <div id="extraMenu" class="nav-dropdown">
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Finanze</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/">🏠 Aggiungi Operazione</a>
                <a href="/lista">📈 Gestione Movimenti Mese</a>
                <a href="/stats">📊 Bilancio Mese</a>
                <a href="/fondo_risparmio_web">💰 Fondo Risparmio</a>
                <a href="/scadenze_web">📅 Scadenze del Mese</a>
                <a href="/fairshare_web">⚖️ FairShare</a>
                <a href="/menu_esplora">🔍 Esplora</a>
                <a href="/grafici_web">📅 Grafici e Statistiche</a>
                <a href="/gestione_categorie">⚙️ Gestione Categorie</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Casa</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/utenze?anno={anno_corrente}">💧 Utenze</a>
                <a href="/consultazione_supermercati">🛒 Gestione Supermercati</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Documenti</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/documenti_pdf_web">🗄️ Documenti Contabili</a>
                <a href="/documenti_personali_web">🗄️ Documenti Personali</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Sistema</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/info_sys_web">📡 Monitor Server</a>
                <a href="/cambia_pw_web">🔑 Cambia Password</a>
                <a href="/webauthn_web">👆 Biometrico</a>
                <a href="/cambia_profilo_web">👤 Cambia Profilo</a>
                <a href="/logoff">🔓 Logout</a>
            </div>
        </div>
    </div>
    <div class="header-title">📡 Monitor Server</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="card">
        <div class="card-title">🖥️ Hardware — {nome_pc}</div>
        <div class="row"><span>RAM</span><b>{ram_info}</b></div>
        <div class="row"><span>CPU</span><b>{multiprocessing.cpu_count()} Core ({arch})</b></div>
        <div class="row"><span>Disco</span><b>{disco}</b></div>
        <div class="row"><span>Database</span><b>{peso_db}</b></div>
    </div>
    <div class="card">
        <div class="card-title">⚙️ Software</div>
        <div class="row"><span>{NAME} </span><b>v.{VERSION}</b></div>
        <div class="row"><span>Python</span><b>v{python_v}</b></div>
        <div class="row"><span>OS</span><b>{os_name}</b></div>
        <div class="row"><span>IP</span><b>{ip}:{porta}</b></div>
    </div>
    <div class="log-card">
        <div class="log-inner">
            <div class="log-folder">📁 {folder}</div>
            <div class="log-time">🕒 Ultimo accesso: {ultimo_log}</div>
        </div>
        <div class="log-links">
            <a href="https://github.com/Renato-4132/OrbitaCasa/blob/main/" target="_blank" class="log-link">🐙 GitHub</a>
            <a href="mailto:helporbitacasa@gmail.com" class="log-link">✉️ Supporto</a>
            <a href="/log_web" class="log-link">📋 Log</a>
        </div>
    </div>
    <a href="/" class="btn-home">🏠 Torna alla Home</a>
</main>
<script>
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if (btn) btn.textContent = '🌙'; }}
        else               {{ root.classList.remove('light'); if (btn) btn.textContent = '☀️'; }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        applyTheme(next);
    }}
    applyTheme(localStorage.getItem('theme') || 'dark');
    function toggleNavGroup(btn, ev) {{
        if (ev) ev.stopPropagation();
        const items = btn.nextElementSibling;
        const giaAperto = items.classList.contains('open');
        btn.closest('.nav-dropdown').querySelectorAll('.nav-group-items.open').forEach(function(el) {{
            el.classList.remove('open');
            el.previousElementSibling.querySelector('.nav-arrow').textContent = '▶';
        }});
        if (!giaAperto) {{
            items.classList.add('open');
            btn.querySelector('.nav-arrow').textContent = '▼';
        }}
    }}
    function toggleMenu() {{
        const m = document.getElementById("extraMenu");
        m.style.display = m.style.display === "block" ? "none" : "block";
    }}
    document.addEventListener("click", function(e) {{
        const menu = document.getElementById("extraMenu");
        const btn = document.querySelector(".menu-btn");
        if (menu && menu.style.display === "block" && !menu.contains(e.target) && e.target !== btn)
            menu.style.display = "none";
    }});
</script>
</body>
</html>"""

# Html Pagina inserimenti Web
def html_form(self):
    import __main__ as _app
    LOGIN_WEB = _app.LOGIN_WEB
    NAME = _app.NAME
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    app_config_globale = _app.app_config_globale
    SMARTCAT_ABILITATO = app_config_globale.get("smartcat_enabled", True)
    smartcat_js = "true" if SMARTCAT_ABILITATO else "false"
    smartcat_text = "SmartCat Idle..." if SMARTCAT_ABILITATO else "SmartCat Off"
    smartcat_icon = "🛠️" if SMARTCAT_ABILITATO else "❌"
    PROFILO_ATTIVO = _app.PROFILO_ATTIVO
    folder = (PROFILO_ATTIVO if PROFILO_ATTIVO != "Principale" else os.path.basename(os.getcwd())).upper()
    ultimo_log_str = "Primo accesso"
    if os.path.exists(LOGIN_WEB):
        try:
            with open(LOGIN_WEB, "r", encoding="utf-8") as f:
                logs = json.load(f)
                if len(logs) > 1:
                    prec = logs[1]
                    ultimo_log_str = prec['data_ora']
                elif len(logs) == 1:
                    ultimo_log_str = "Primo accesso!"
        except:
            pass
    oggi = datetime.date.today()
    un_anno_fa = oggi - datetime.timedelta(days=365)
    frequenze = {}
    mappa_ricorrenti = {}
    spese_valide = []
    for d_reg, lista in self.spese.items():
        if d_reg < un_anno_fa: continue
        for voce in lista:
            try:
                cat, desc, imp, tipo = voce[:4]
                if not cat or cat == "Categoria Rimossa" or cat not in self.categorie:
                    continue
                importo_f = float(imp)
                spese_valide.append({
                    "cat": cat,
                    "imp": importo_f,
                    "tipo": tipo,
                    "desc": str(desc).lower().strip(),
                    "data": d_reg.strftime("%Y-%m-%d"),
                    "mese": d_reg.month,
                    "anno": d_reg.year
                })
                if cat not in frequenze: frequenze[cat] = 0
                frequenze[cat] += 1
                chiave_esatta = f"{cat}|{round(importo_f, 2)}"
                mappa_ricorrenti[chiave_esatta] = mappa_ricorrenti.get(chiave_esatta, 0) + 1
            except: continue
    smart_data_json = json.dumps({
        "spese": spese_valide,
        "frequenze": frequenze,
        "ricorrenti_esatti": mappa_ricorrenti
    })
    tipi_default_json = json.dumps(self.categorie_tipi)
    entrate_mese = 0.0
    uscite_mese = 0.0
    movimenti_mese_corrente = []
    for d, lista in self.spese.items():
        if d.month == oggi.month and d.year == oggi.year:
            for voce in lista:
                cat, desc, importo, tipo = voce[:4]
                if not cat or cat == "Categoria Rimossa" or cat not in self.categorie:
                    continue
                if tipo == "Entrata": entrate_mese += importo
                else: uscite_mese += importo
                movimenti_mese_corrente.append({
                    "data": d,
                    "cat": cat,
                    "desc": desc,
                    "imp": importo,
                    "tipo": tipo
                })
    movimenti_mese_corrente.sort(key=lambda x: x["data"], reverse=True)
    ultimi_movimenti_html = ""
    if not movimenti_mese_corrente:
        ultimi_movimenti_html = "<div style='text-align:center; padding:12px; color:#444; font-size:0.85em; letter-spacing:1px;'>NESSUN MOVIMENTO QUESTO MESE</div>"
    else:
        for mov in movimenti_mese_corrente[:10]:
            colore = "#4caf82" if mov["tipo"] == "Entrata" else "#e05a5a"
            segno = "+" if mov["tipo"] == "Entrata" else "-"
            data_str = mov["data"].strftime("%d/%m")
            ultimi_movimenti_html += f"""
            <div class="mov-item">
                <div class="mov-left">
                    <div class="mov-date">{data_str}</div>
                    <div class="mov-cat">{mov["cat"]}</div>
                    <div class="mov-desc">{mov["desc"]}</div>
                </div>
                <div class="mov-amount" style="color:{colore}">€ {segno}{_fmt_it(mov["imp"])}</div>
            </div>"""
    today = oggi.isoformat()
    anno_corrente = oggi.year
    categorie_options = "\n".join(
        f"<option value='{c}'>{c}</option>"
        for c in self.categorie if c != "Generica"
    )
    saldo_mese = entrate_mese - uscite_mese
    icona_saldo = "☀️" if saldo_mese >= 0 else "⛈️"
    saldo_colore = "#4caf82" if saldo_mese >= 0 else "#e05a5a"
    segno_saldo_mese = "+" if saldo_mese >= 0 else ""
    check_doppi_js = "true" if self.CHECK_DOPPI_MOV else "false"
    partecipanti_fs = []
    for p in self.nomi_partecipanti:
        tipo = p.get("tipo", "persona")
        ico = "CNT·" if tipo == "contenitore" else ("CTP·" if tipo == "personale" else "PER·")
        partecipanti_fs.append({"nome": p["nome"], "tipo": tipo, "ico": ico})
    partecipanti_json = json.dumps(partecipanti_fs)
    smartcat_toll = app_config_globale.get("smartcat_toll", 15)
    try:
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
            _db_portaf = json.load(_pf)
        _conti_lista = _db_portaf.get("conti", [])
        _conto_princ = next((c.get("nome","") for c in _conti_lista if c.get("principale")), "")
        conti_options = "\n".join(
            f'<option value="{c.get("nome","")}" {"selected" if c.get("nome","") == _conto_princ else ""}>{c.get("nome","")}\u2002(\u20ac {_fmt_it(float(c.get("saldo",0)))})</option>'
            for c in _conti_lista
        )
        mostra_conto_stile = "block" if _conti_lista else "none"
    except Exception:
        conti_options = ""
        mostra_conto_stile = "none"
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>💰 {NAME}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
    (function() {{
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    }})();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg: #050505; --surface: #0f0f0f; --surface2: #161616; --surface3: #1e1e1e;
        --border: rgba(255,255,255,0.07); --border-active: rgba(99,160,240,0.5);
        --gold: #c9a84c; --blue: #63a0f0; --green: #4caf82; --red: #e05a5a;
        --text: #e8e8e8; --text-dim: #555; --text-mid: #888;
        --radius: 10px; --radius-lg: 16px;
    }}
    :root.light {{
        --bg: #f5f5f0; --surface: #ffffff; --surface2: #f0efe8; --surface3: #e8e7df;
        --border: rgba(0,0,0,0.09); --border-active: rgba(61,127,212,0.5);
        --gold: #b8902a; --blue: #3d7fd4; --green: #3a9068; --red: #cc3333;
        --text: #1a1a1a; --text-dim: #999; --text-mid: #555;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        font-family: 'DM Sans', sans-serif; background: var(--bg); color: var(--text);
        min-height: 100vh; transition: background 0.3s, color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 40% at 50% -10%, rgba(99,160,240,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 60%);
    }}
    header {{
        padding: 12px 16px 10px; display: flex; align-items: center; justify-content: center;
        border-bottom: 1px solid var(--border); background: rgba(5,5,5,0.95);
        backdrop-filter: blur(20px); position: sticky; top: 0; z-index: 100;
    }}
    :root.light header {{ background: rgba(245,245,240,0.95); }}
    .menu-btn {{
        position: absolute; left: 14px; top: 50%; transform: translateY(-50%);
        background: var(--surface3); border: 1px solid var(--border); color: var(--gold);
        width: 34px; height: 34px; border-radius: 9px; font-size: 1em;
        cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s;
    }}
    .menu-btn:hover {{ border-color: var(--gold); box-shadow: 0 0 12px rgba(201,168,76,0.2); }}
    .header-title {{
        font-family: 'DM Sans', sans-serif; font-size: 0.95em; font-weight: 700;
        letter-spacing: 0.5px; color: var(--text); text-align: center; line-height: 1.3;
    }}
    .header-sub {{
        font-size: 0.6em; color: var(--text-dim); font-weight: 400; letter-spacing: 2px;
        text-transform: uppercase; margin-top: 2px; cursor: pointer; transition: color 0.2s; text-align: center;
    }}
    .header-sub:hover {{ color: var(--blue); }}
    .theme-toggle {{
        position: absolute; right: 14px; top: 50%; transform: translateY(-50%);
        background: var(--surface3); border: 1px solid var(--border);
        border-radius: 8px; width: 34px; height: 34px;
        display: flex; align-items: center; justify-content: center;
        cursor: pointer; font-size: 1em; transition: all 0.2s;
    }}
    .theme-toggle:hover {{ border-color: var(--gold); }}
    .nav-dropdown {{
        position: absolute; top: calc(100% + 6px); left: 10px;
        background: var(--surface2); border: 1px solid var(--border);
        border-radius: var(--radius-lg); display: none; z-index: 1000;
        width: 270px; overflow: hidden; box-shadow: 0 20px 60px rgba(0,0,0,0.7);
    }}
    .nav-dropdown a {{
        display: flex; align-items: center; gap: 10px; padding: 10px 16px;
        text-decoration: none; color: var(--text-mid); border-bottom: 1px solid var(--border);
        font-size: 0.87em; transition: all 0.15s;
    }}
    .nav-dropdown a:last-child {{ border-bottom: none; }}
    .nav-dropdown a:hover {{ background: var(--surface3); color: var(--text); padding-left: 22px; }}
    .nav-group-btn {{ display:flex; justify-content:space-between; align-items:center; width:100%;
        padding:8px 16px; background:none; border:none; font-family:inherit; color:var(--gold);
        font-size:0.7em; font-weight:700; letter-spacing:1px; text-transform:uppercase; cursor:pointer; opacity:0.85; }}
    .nav-group-btn:hover {{ opacity:1; background:var(--surface3); }}
    .nav-arrow {{ font-size:0.85em; transition:transform 0.15s; }}
    .nav-group-items {{ display:none; flex-direction:column; }}
    .nav-group-items.open {{ display:flex; }}
    main {{ padding: 0 14px; max-width: 480px; margin: 0 auto; padding-bottom: 20px; animation: fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    .saldo-card {{
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius-lg); margin-top: 10px; margin-bottom: 10px; overflow: hidden;
    }}
    .saldo-header {{
        padding: 8px 16px; cursor: pointer; display: flex; justify-content: space-between;
        align-items: center; font-size: 0.85em; font-weight: 500; color: var(--text-mid);
        transition: background 0.15s; user-select: none;
    }}
    .saldo-header:hover {{ background: var(--surface2); }}
    .saldo-content {{ display: none; padding: 0 12px 12px; }}
    .saldo-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px; margin-bottom: 10px; }}
    .saldo-item {{
        background: var(--surface2); border-radius: 8px; padding: 8px 6px;
        text-align: center; border: 1px solid var(--border);
    }}
    .saldo-item small {{ display: block; font-size: 0.62em; color: var(--text-dim); letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 4px; }}
    .saldo-item b {{ font-size: 0.88em; font-weight: 600; }}
    .movimenti-section {{ border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }}
    .movimenti-header {{
        padding: 8px 12px; font-size: 0.78em; color: var(--text-dim); cursor: pointer;
        display: flex; justify-content: space-between; background: var(--surface2); user-select: none;
    }}
    .movimenti-content {{ display: none; }}
    .mov-item {{
        display: flex; justify-content: space-between; align-items: center;
        padding: 8px 12px; border-bottom: 1px solid var(--border);
    }}
    .mov-item:last-child {{ border-bottom: none; }}
    .mov-left {{ line-height: 1.25; overflow: hidden; }}
    .mov-date {{ font-size: 0.65em; color: var(--text-dim); }}
    .mov-cat {{ font-size: 0.83em; font-weight: 500; color: var(--text); }}
    .mov-desc {{ font-size: 0.7em; color: var(--text-dim); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 190px; }}
    .mov-amount {{ font-weight: 600; font-size: 0.88em; white-space: nowrap; margin-left: 8px; }}
    .form-card {{
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius-lg); padding: 16px 16px 0; position: relative; overflow: hidden;
    }}
    .form-card::before {{
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .smartcat-badge {{
        display: inline-flex; align-items: center; gap: 5px;
        background: var(--surface2); border: 1px solid var(--border);
        border-radius: 20px; padding: 4px 11px; font-size: 0.7em; color: var(--text-dim);
        letter-spacing: 0.3px; transition: all 0.3s;
    }}
    .smartcat-badge.active {{ border-color: rgba(76,175,130,0.4); color: var(--green); }}
    .badge-row {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }}
    .btn-sync-mini {{
        display: inline-flex; align-items: center; gap: 4px;
        background: var(--surface2); border: 1px solid rgba(99,160,240,0.3);
        border-radius: 20px; padding: 4px 10px; font-size: 0.7em; color: var(--blue);
        cursor: pointer; letter-spacing: 0.3px; transition: all 0.2s;
    }}
    .btn-sync-mini:hover {{ border-color: var(--blue); background: rgba(99,160,240,0.08); }}
    .btn-sync-mini:disabled {{ opacity: 0.45; cursor: default; }}
    .form-group {{ margin-bottom: 10px; }}
    label {{
        display: block; font-size: 0.68em; font-weight: 500; color: var(--text-dim);
        letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 5px;
    }}
    input, select {{
        width: 100%; padding: 10px 13px; background: var(--surface2);
        border: 1px solid var(--border); border-radius: 9px; color: var(--text);
        font-family: 'DM Sans', sans-serif; font-size: 0.93em;
        transition: all 0.2s; outline: none; -webkit-appearance: none; appearance: none;
    }}
    input:focus, select:focus {{
        border-color: var(--border-active); background: var(--surface3);
        box-shadow: 0 0 0 3px rgba(99,160,240,0.07);
    }}
    input::placeholder {{ color: var(--text-dim); }}
    select {{
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='7' viewBox='0 0 12 7'%3E%3Cpath fill='none' stroke='%23555' stroke-width='1.5' d='M1 1l5 5 5-5'/%3E%3C/svg%3E");
        background-repeat: no-repeat; background-position: right 12px center;
        padding-right: 32px; cursor: pointer;
    }}
    select option {{ background: var(--surface2); color: var(--text); }}
    .importo-wrap {{ position: relative; }}
    .importo-wrap input {{ padding-left: 30px; font-size: 1.05em; font-weight: 500; }}
    .euro-sign {{
        position: absolute; left: 12px; top: 50%; transform: translateY(-50%);
        color: var(--gold); font-weight: 700; font-size: 0.95em; pointer-events: none;
    }}
    .error-inline {{
        display: none; position: absolute; right: 10px; top: 50%; transform: translateY(-50%);
        color: var(--red); font-size: 0.68em; font-weight: 600; pointer-events: none; white-space: nowrap;
    }}
    #tipo_select.uscita {{ border-color: rgba(224,90,90,0.3); color: #e05a5a; }}
    #tipo_select.entrata {{ border-color: rgba(76,175,130,0.3); color: #4caf82; }}
    .highlight-smart {{ border-color: rgba(76,175,130,0.5) !important; background: rgba(76,175,130,0.04) !important; }}
    input::-webkit-outer-spin-button, input::-webkit-inner-spin-button {{ -webkit-appearance: none; margin: 0; }}
    input[type=number] {{ -moz-appearance: textfield; }}
    #fs_select.persona {{ border-color: rgba(99,160,240,0.3); color: var(--blue); }}
    #fs_select.contenitore {{ border-color: rgba(201,168,76,0.3); color: var(--gold); }}
    #fs_select.personale {{ border-color: rgba(76,175,130,0.3); color: var(--green); }}
    .btn-submit {{
        width: 100%; padding: 13px; margin-top: 8px;
        background: linear-gradient(135deg, #c9a84c 0%, #8a6820 100%);
        color: #000; border: none; border-radius: 9px;
        font-family: 'DM Sans', sans-serif; font-size: 0.92em; font-weight: 700;
        line-height: 1.5; letter-spacing: 0.5px; cursor: pointer; transition: all 0.2s;
    }}
    .btn-submit:hover {{ transform: translateY(-1px); box-shadow: 0 6px 20px rgba(201,168,76,0.25); }}
    .btn-submit:active {{ transform: translateY(0); }}
    .pdf-upload-card {{
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius-lg); margin-top: 10px; overflow: hidden;
    }}
    .pdf-upload-header {{
        padding: 11px 16px; cursor: pointer; display: flex; justify-content: space-between;
        align-items: center; font-size: 0.85em; font-weight: 500; color: var(--text-mid);
        transition: background 0.15s; user-select: none;
    }}
    .pdf-upload-header:hover {{ background: var(--surface2); }}
    .pdf-upload-body {{ display: none; padding: 12px 14px 14px; }}
    .drop-zone {{
        border: 2px dashed var(--border); border-radius: 10px;
        padding: 20px 12px; text-align: center; cursor: pointer;
        transition: all 0.2s; color: var(--text-dim); font-size: 0.82em;
    }}
    .drop-zone:hover, .drop-zone.dragover {{
        border-color: var(--blue); background: rgba(99,160,240,0.04); color: var(--text);
    }}
    .drop-zone .dz-icon {{ font-size: 1.8em; display: block; margin-bottom: 6px; }}
    .drop-zone .dz-filename {{ font-size: 0.88em; color: var(--blue); margin-top: 4px; font-weight: 500; }}
    .btn-analizza {{
        width: 100%; padding: 11px; margin-top: 10px;
        background: linear-gradient(135deg, #3d7fd4 0%, #1a4f8a 100%);
        color: #fff; border: none; border-radius: 9px;
        font-family: 'DM Sans', sans-serif; font-size: 0.88em; font-weight: 700;
        cursor: pointer; transition: all 0.2s;
    }}
    .btn-analizza:hover {{ transform: translateY(-1px); box-shadow: 0 6px 20px rgba(61,127,212,0.25); }}
    .btn-analizza:disabled {{ opacity: 0.5; cursor: default; transform: none; box-shadow: none; }}
    .pdf-result {{
        margin-top: 10px; padding: 10px 12px; border-radius: 8px;
        font-size: 0.82em; line-height: 1.6; display: none;
        border: 1px solid var(--border); background: var(--surface2);
    }}
    .pdf-result.ok {{ border-color: rgba(76,175,130,0.4); }}
    .pdf-result.err {{ border-color: rgba(224,90,90,0.4); color: var(--red); }}
    #customConfirm {{
        display: none; position: fixed; z-index: 9999; left: 0; top: 0;
        width: 100%; height: 100%; background: rgba(0,0,0,0.8); backdrop-filter: blur(6px);
    }}
    .modal-box {{
        background: var(--surface2); border: 1px solid var(--border);
        margin: 22% auto; padding: 24px 20px; border-radius: var(--radius-lg);
        width: 85%; max-width: 340px; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.6);
    }}
    .modal-box h3 {{ font-family: 'DM Sans', sans-serif; font-size: 1em; margin-bottom: 10px; color: var(--gold); }}
    .modal-box p {{ color: var(--text-mid); font-size: 0.85em; line-height: 1.5; }}
    .modal-actions {{ display: flex; gap: 10px; margin-top: 18px; justify-content: center; }}
    .btn-ok {{ background: var(--blue); color: #000; border: none; padding: 10px 22px; border-radius: 8px; font-weight: 700; font-family: 'DM Sans', sans-serif; cursor: pointer; font-size: 0.85em; line-height: 1.5; }}
    .btn-no {{ background: var(--surface3); color: var(--text-mid); border: 1px solid var(--border); padding: 10px 22px; border-radius: 8px; cursor: pointer; font-size: 0.85em; line-height: 1.5; }}
</style>
</head>
<body>
<div id="customConfirm">
    <div class="modal-box">
        <h3>⚠️ Movimento Duplicato</h3>
        <p id="confirmMsg"></p>
        <div class="modal-actions">
            <button class="btn-no" onclick="rispostaModal(false)">Annulla</button>
            <button class="btn-ok" onclick="rispostaModal(true)">Inserisci</button>
        </div>
    </div>
</div>
<header>
    <button class="menu-btn" onclick="toggleMenu()">⚙️</button>
    <div id="extraMenu" class="nav-dropdown">
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Finanze</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/">🏠 Aggiungi Operazione</a>
                <a href="/lista">📈 Gestione Movimenti Mese</a>
                <a href="/stats">📊 Bilancio Mese</a>
                <a href="/fondo_risparmio_web">💰 Fondo Risparmio</a>
                <a href="/scadenze_web">📅 Scadenze del Mese</a>
                <a href="/fairshare_web">⚖️ FairShare</a>
                <a href="/menu_esplora">🔍 Esplora</a>
                <a href="/grafici_web">📅 Grafici e Statistiche</a>
                <a href="/gestione_categorie">⚙️ Gestione Categorie</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Casa</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/utenze?anno={anno_corrente}">💧 Utenze</a>
                <a href="/consultazione_supermercati">🛒 Gestione Supermercati</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Documenti</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/documenti_pdf_web">🗄️ Documenti Contabili</a>
                <a href="/documenti_personali_web">🗄️ Documenti Personali</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Sistema</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/info_sys_web">📡 Monitor Server</a>
                <a href="/cambia_pw_web">🔑 Cambia Password</a>
                <a href="/webauthn_web">👆 Biometrico</a>
                <a href="/cambia_profilo_web">👤 Cambia Profilo</a>
                <a href="/logoff">🔓 Logout</a>
            </div>
        </div>
    </div>
    <div>
        <div class="header-title">🏠 Inserisci Operazione</div>
        <div class="header-sub" id="user-badge" onclick="mostraLog()">👤 {folder}</div>
    </div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="saldo-card">
        <div class="saldo-header" onclick="toggleSection('summaryContent','summaryArrow')">
            <span>📊 Saldo Mensile {icona_saldo}</span>
            <span id="summaryArrow" style="font-size:0.75em;">▼</span>
        </div>
        <div id="summaryContent" class="saldo-content">
            <div class="saldo-grid">
                <div class="saldo-item">
                    <small>Entrate</small>
                    <b style="color:var(--green)">€ {_fmt_it(entrate_mese)}</b>
                </div>
                <div class="saldo-item">
                    <small>Uscite</small>
                    <b style="color:var(--red)">€ {_fmt_it(uscite_mese)}</b>
                </div>
                <div class="saldo-item">
                    <small>Saldo</small>
                    <b style="color:{saldo_colore}">€ {segno_saldo_mese}{_fmt_it(saldo_mese)}</b>
                </div>
            </div>
            <div class="movimenti-section">
                <div class="movimenti-header" onclick="event.stopPropagation(); toggleSection('movimentiContent','movimentiArrow')">
                    <span>🕒 Ultimi 10 Movimenti Mese</span>
                    <span id="movimentiArrow">▼</span>
                </div>
                <div id="movimentiContent" class="movimenti-content">
                    {ultimi_movimenti_html}
                </div>
            </div>
        </div>
    </div>
    <div class="form-card">
        <div class="badge-row">
            <div class="smartcat-badge" id="smartcat_badge">
                <span>{smartcat_icon}</span> {smartcat_text}
            </div>
            <button type="button" class="btn-sync-mini" id="btn_sync_web" onclick="avviaSyncWeb()">🔄 Sync Gmail</button>
        </div>
        <form method="post" action="/" onsubmit="return validaForm(event)">
            <div class="form-group">
                <label>Importo</label>
                <div class="importo-wrap">
                    <span class="euro-sign">€</span>
                    <input name="importo" id="importo_input" type="number" step="0.01"
                        placeholder="0.00" autofocus oninput="aggiornaSmartCat(this.value)">
                    <span id="local_error" class="error-inline">⚠️ Importo non valido!</span>
                </div>
            </div>
            <div class="form-group">
                <label>Categoria</label>
                <select name="categoria" id="categoria_select" onchange="applicaTipoDefault(this.value)">
                    <option value="Generica">Generica</option>
                    {categorie_options}
                </select>
            </div>
            <div style="display:flex; gap:8px; margin-bottom:10px;">
                <div style="flex:1">
                    <label>Tipo</label>
                    <select name="tipo" id="tipo_select" class="uscita" onchange="aggiornaColoreTipo()">
                        <option value="Uscita">Uscita</option>
                        <option value="Entrata">Entrata</option>
                    </select>
                </div>
                <div style="flex:1">
                    <label>Data</label>
                    <input name="data" id="data_input" type="date" value="{today}">
                </div>
            </div>
            <div class="form-group">
                <label>Descrizione</label>
                <input name="descrizione" id="desc_input"
                    placeholder="Es: Pizza, Colazione, Fattura, Regali">
            </div>
            <div class="form-group" id="fs_group" style="display:none">
                <label>Partecipante FairShare</label>
                <select id="fs_select" name="fairshare" onchange="applicaPartecipante(this.value)">
                    <option value="">— Nessuno —</option>
                </select>
            </div>
            <div class="form-group" id="conto_group" style="display:{mostra_conto_stile}">
                <label>Conto</label>
                <select name="conto" id="conto_select">
                    <option value="">(nessuno)</option>
                    {conti_options}
                </select>
            </div>
            <button type="submit" class="btn-submit" style="position:sticky; bottom:16px; box-shadow:0 4px 20px rgba(0,0,0,0.4);">➕ Aggiungi Movimento</button>
        </form>
    </div>

    <div class="pdf-upload-card">
        <div class="pdf-upload-header" onclick="toggleSection('pdfUploadBody','pdfUploadArrow')">
            <span>📎 Carica PDF → Crea Movimento</span>
            <span id="pdfUploadArrow" style="font-size:0.75em;">▼</span>
        </div>
        <div id="pdfUploadBody" class="pdf-upload-body">
            <div class="drop-zone" id="dropZone" onclick="document.getElementById('pdfFileInput').click()"
                 ondragover="event.preventDefault(); this.classList.add('dragover')"
                 ondragleave="this.classList.remove('dragover')"
                 ondrop="gestisciDrop(event)">
                <span class="dz-icon">📄</span>
                Trascina qui il PDF oppure tocca per selezionare
                <div class="dz-filename" id="dz_filename"></div>
            </div>
            <input type="file" id="pdfFileInput" accept=".pdf" style="display:none" onchange="selezionaPdf(this)">
            <button type="button" class="btn-analizza" id="btn_analizza" onclick="caricaPdfWeb()" disabled>
                🤖 Analizza con Gemini e Crea Movimento
            </button>
            <div class="pdf-result" id="pdf_result"></div>
        </div>
    </div>
</main>
<script>
    const dbSmart = {smart_data_json};
    const tipiDefault = {tipi_default_json};
    const checkDoppiAbilitato = {check_doppi_js};
    const smartCatActive = {smartcat_js};
    const smartCatToll = {smartcat_toll};
    const partecipantiFS = {partecipanti_json};

    function inizializzaFS() {{
        const sel = document.getElementById("fs_select");
        const grp = document.getElementById("fs_group");
        if (!partecipantiFS || partecipantiFS.length === 0) return;
        grp.style.display = "block";
        partecipantiFS.forEach(p => {{
            const opt = document.createElement("option");
            opt.value = p.ico + p.nome;
            opt.textContent = p.ico + " " + p.nome;
            opt.dataset.tipo = p.tipo;
            sel.appendChild(opt);
        }});
    }}

    function applicaPartecipante(prefisso) {{
        const desc = document.getElementById("desc_input");
        const sel = document.getElementById("fs_select");
        let testo = desc.value.trim();
        partecipantiFS.forEach(p => {{
            const tag = p.ico + p.nome;
            if (testo.startsWith(tag)) testo = testo.slice(tag.length).trim();
        }});
        desc.value = prefisso ? prefisso + " " + testo : testo;
        const opt = sel.options[sel.selectedIndex];
        if (opt && opt.dataset.tipo) {{
            sel.className = opt.dataset.tipo;
        }} else {{
            sel.className = "";
        }}
    }}

    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if (btn) btn.textContent = '🌙'; }}
        else               {{ root.classList.remove('light'); if (btn) btn.textContent = '☀️'; }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        applyTheme(next);
    }}
    applyTheme(localStorage.getItem('theme') || 'dark');
    function aggiornaColoreTipo() {{
        const st = document.getElementById("tipo_select");
        st.className = st.value === "Entrata" ? "entrata" : "uscita";
    }}
    function toggleSection(contentId, arrowId) {{
        const content = document.getElementById(contentId);
        const arrow = document.getElementById(arrowId);
        const isOpen = content.style.display === "block";
        content.style.display = isOpen ? "none" : "block";
        if (arrow) arrow.innerHTML = isOpen ? "▼" : "▲";
    }}
    function toggleNavGroup(btn, ev) {{
        if (ev) ev.stopPropagation();
        const items = btn.nextElementSibling;
        const giaAperto = items.classList.contains('open');
        btn.closest('.nav-dropdown').querySelectorAll('.nav-group-items.open').forEach(function(el) {{
            el.classList.remove('open');
            el.previousElementSibling.querySelector('.nav-arrow').textContent = '▶';
        }});
        if (!giaAperto) {{
            items.classList.add('open');
            btn.querySelector('.nav-arrow').textContent = '▼';
        }}
    }}
    function toggleMenu() {{
        const m = document.getElementById("extraMenu");
        m.style.display = m.style.display === "block" ? "none" : "block";
    }}
    function applicaTipoDefault(categoria) {{
        const st = document.getElementById("tipo_select");
        const tipoPredefinito = tipiDefault[categoria];
        if (tipoPredefinito) st.value = tipoPredefinito;
        aggiornaColoreTipo();
    }}
    function aggiornaSmartCat(valore) {{
        if (!smartCatActive) return;
        const sc = document.getElementById("categoria_select");
        const st = document.getElementById("tipo_select");
        const badge = document.getElementById("smartcat_badge");
        const inp = document.getElementById("importo_input");
        inp.style.borderColor = "var(--border)";
        document.getElementById("local_error").style.display = "none";
        if (!valore || valore.trim() === "") {{
            sc.value = "Generica";
            applicaTipoDefault("Generica");
            badge.className = "smartcat-badge";
            badge.innerHTML = "<span>🛠️</span> SmartCat in attesa...";
            return;
        }}
        const impCorrente = parseFloat(valore);
        if (isNaN(impCorrente)) return;
        let migliorPunteggio = Infinity;
        let categoriaMigliore = null;
        let tipoMigliore = "Uscita";
        if (dbSmart.ricorrenti_esatti) {{
            for (let chiave in dbSmart.ricorrenti_esatti) {{
                let parti = chiave.split('|');
                let cat = parti[0];
                let impStorico = parseFloat(parti[1]);
                let diff = Math.abs(impStorico - impCorrente);
                if (diff < 0.01) {{
                    let freq = dbSmart.ricorrenti_esatti[chiave];
                    let punteggio = -2000 - freq;
                    if (punteggio < migliorPunteggio) {{
                        migliorPunteggio = punteggio;
                        categoriaMigliore = cat;
                        tipoMigliore = tipiDefault[cat] || "Uscita";
                    }}
                }}
            }}
        }}
        if (migliorPunteggio > -1000) {{
            for (let chiave in dbSmart.ricorrenti_esatti) {{
                let parti = chiave.split('|');
                let cat = parti[0];
                let impStorico = parseFloat(parti[1]);
                let freq = dbSmart.ricorrenti_esatti[chiave];
                let diff = Math.abs(impStorico - impCorrente);
                let punteggio;
                if (diff <= 0.05) {{
                    punteggio = -1000 - freq + (diff * 10);
                }} else if (diff <= impCorrente * 0.02) {{
                    punteggio = diff - (freq * 2);
                }} else if (diff <= smartCatToll) {{
                    punteggio = diff - freq;
                }} else {{
                    continue;
                }}
                if (punteggio < migliorPunteggio) {{
                    migliorPunteggio = punteggio;
                    categoriaMigliore = cat;
                    tipoMigliore = tipiDefault[cat] || "Uscita";
                }}
            }}
        }}
        if (categoriaMigliore) {{
            if (sc.value !== categoriaMigliore || st.value !== tipoMigliore) {{
                sc.value = categoriaMigliore;
                st.value = tipoMigliore;
                sc.classList.add("highlight-smart");
                setTimeout(() => sc.classList.remove("highlight-smart"), 500);
            }}
            badge.className = "smartcat-badge active";
            badge.innerHTML = "<span>💡</span> SmartCat attiva";
        }}
        aggiornaColoreTipo();
    }}
    window.addEventListener('load', function() {{
        const inp = document.getElementById("importo_input");
        if (inp) inp.focus();
        applicaTipoDefault(document.getElementById("categoria_select").value);
        aggiornaColoreTipo();
        inizializzaFS();
        const p = new URLSearchParams(window.location.search);
        if (p.get('salvato') === '1' && inp) {{
            const t = document.createElement("div");
            t.innerText = "✓ Salvato";
            Object.assign(t.style, {{
                position: "absolute", right: "10px", top: "50%",
                transform: "translateY(-50%)", backgroundColor: "var(--green)",
                color: "black", padding: "3px 9px", borderRadius: "6px",
                fontSize: "11px", fontWeight: "bold", zIndex: "5",
                pointerEvents: "none", boxShadow: "0 2px 8px rgba(76,175,130,0.3)"
            }});
            inp.parentElement.appendChild(t);
            window.history.replaceState({{}}, document.title, window.location.pathname);
            setTimeout(() => {{
                t.style.transition = "opacity 0.5s";
                t.style.opacity = "0";
                setTimeout(() => t.remove(), 500);
            }}, 1500);
        }}
    }});
    window.onclick = function(event) {{
        if (!event.target.matches('.menu-btn') && !event.target.matches('.theme-toggle')) {{
            const dropdowns = document.getElementsByClassName("nav-dropdown");
            for (let i = 0; i < dropdowns.length; i++) {{
                if (dropdowns[i].style.display === "block") dropdowns[i].style.display = "none";
            }}
        }}
    }}
    function mostraLog() {{
        const badge = document.getElementById('user-badge');
        const originale = "PER· {folder}";
        const dataLog = "🕒 {ultimo_log_str}";
        if (badge.innerText.toUpperCase().includes("{folder}".toUpperCase())) {{
            badge.style.opacity = "0";
            setTimeout(() => {{
                badge.innerText = dataLog;
                badge.style.color = "var(--blue)";
                badge.style.opacity = "1";
            }}, 200);
            setTimeout(() => {{
                badge.style.opacity = "0";
                setTimeout(() => {{
                    badge.innerText = originale;
                    badge.style.color = "";
                    badge.style.opacity = "1";
                }}, 200);
            }}, 3000);
        }}
    }}
    let formInAttesa = null;
    function rispostaModal(procedi) {{
        document.getElementById("customConfirm").style.display = "none";
        if (procedi && formInAttesa) formInAttesa.submit();
    }}
    function validaForm(e) {{
        const form = e.target;
        const inp = document.getElementById("importo_input");
        const errorMsg = document.getElementById("local_error");
        const cat = document.getElementById("categoria_select").value;
        const data = document.getElementById("data_input").value;
        const valore = parseFloat(inp.value);
        if (!inp.value || isNaN(valore) || valore <= 0) {{
            e.preventDefault();
            inp.value = "";
            inp.style.borderColor = "rgba(224,90,90,0.5)";
            errorMsg.style.display = "block";
            setTimeout(() => {{
                errorMsg.style.display = "none";
                inp.style.borderColor = "var(--border)";
                inp.placeholder = "0.00";
            }}, 2000);
            return false;
        }}
        if (checkDoppiAbilitato && typeof dbSmart !== 'undefined' && dbSmart.spese) {{
            const mese = data.substring(0, 7);
            const trovato = dbSmart.spese.find(s =>
                s.imp === valore &&
                s.cat === cat &&
                s.data.substring(0, 7) === mese
            );
            if (trovato) {{
                e.preventDefault();
                formInAttesa = form;
                const d = trovato.data.split("-");
                const catSelect = document.getElementById("categoria_select");
                const catName = catSelect.options[catSelect.selectedIndex].text;
                const msg = "Hai già inserito € " + valore.toFixed(2) + " per '" + catName + "' il " + d[2]+"-"+d[1]+"-"+d[0] + ". Vuoi continuare?";
                document.getElementById("confirmMsg").innerText = msg;
                document.getElementById("customConfirm").style.display = "block";
                return false;
            }}
        }}
        return true;
    }}

    let _pdfFile = null;

    function selezionaPdf(input) {{
        if (input.files && input.files[0]) {{
            _pdfFile = input.files[0];
            document.getElementById("dz_filename").textContent = _pdfFile.name;
            document.getElementById("btn_analizza").disabled = false;
        }}
    }}

    function gestisciDrop(event) {{
        event.preventDefault();
        document.getElementById("dropZone").classList.remove("dragover");
        const file = event.dataTransfer.files[0];
        if (file && file.name.toLowerCase().endsWith(".pdf")) {{
            _pdfFile = file;
            document.getElementById("dz_filename").textContent = file.name;
            document.getElementById("btn_analizza").disabled = false;
        }}
    }}

    function caricaPdfWeb() {{
        if (!_pdfFile) return;
        const btn = document.getElementById("btn_analizza");
        const res = document.getElementById("pdf_result");
        btn.disabled = true;
        btn.textContent = "⏳ Analisi in corso...";
        res.style.display = "none";
        const fd = new FormData();
        fd.append("pdf_file", _pdfFile);
        fetch("/carica_pdf_web", {{method: "POST", body: fd}})
            .then(r => r.json())
            .then(data => {{
                btn.textContent = "🤖 Analizza con Gemini e Crea Movimento";
                btn.disabled = false;
                res.style.display = "block";
                if (data.ok) {{
                    const segno = data.direzione === "Entrata" ? "+" : "-";
                    const col   = data.direzione === "Entrata" ? "var(--green)" : "var(--red)";
                    res.className = "pdf-result ok";
                    res.innerHTML =
                        "<b style='color:var(--green)'>✅ Movimento creato!</b><br>" +
                        "<b>" + data.desc + "</b><br>" +
                        "Importo: <span style='color:" + col + ";font-weight:700'>" +
                        "€ " + segno + data.importo.toFixed(2) + "</span> · " +
                        data.categoria + " · " + data.data;
                    _pdfFile = null;
                    document.getElementById("dz_filename").textContent = "";
                    document.getElementById("pdfFileInput").value = "";
                }} else {{
                    res.className = "pdf-result err";
                    res.innerHTML = "⚠️ " + (data.errore || "Errore sconosciuto");
                }}
            }})
            .catch(() => {{
                btn.textContent = "🤖 Analizza con Gemini e Crea Movimento";
                btn.disabled = false;
                res.style.display = "block";
                res.className = "pdf-result err";
                res.innerHTML = "❌ Errore di connessione";
            }});
    }}

    function avviaSyncWeb() {{
        const btn = document.getElementById("btn_sync_web");
        if (btn.disabled) return;
        btn.disabled = true;
        btn.textContent = "⏳ Sincronizzazione in corso...";
        fetch("/avvia_sync_web", {{method: "POST"}})
            .then(r => r.json())
            .then(data => {{
                if (data.ok) {{
                    btn.textContent = "✅ Avviata sull\u2019app!";
                }} else {{
                    btn.textContent = "⚠️ " + (data.errore || "Configurazione mancante");
                }}
                setTimeout(() => {{
                    btn.disabled = false;
                    btn.textContent = "🔄 Sincronizza Email (Gmail)";
                }}, 3500);
            }})
            .catch(() => {{
                btn.textContent = "❌ Errore connessione";
                setTimeout(() => {{
                    btn.disabled = false;
                    btn.textContent = "🔄 Sincronizza Email (Gmail)";
                }}, 2500);
            }});
    }}
</script>
</body>
</html>"""
    
# Html Genera la pagina di logoff con redirect automatico al login dopo 5 secondi
def html_saluto(self):
    import __main__ as _app
    NAME = _app.NAME
    VERSION = _app.VERSION
    ora_fine = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{NAME} - Logoff</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
    (function() {{
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    }})();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg: #050505; --surface: #0f0f0f; --surface2: #161616;
        --border: rgba(255,255,255,0.07); --gold: #c9a84c; --blue: #63a0f0;
        --green: #4caf82; --red: #e05a5a; --text: #e8e8e8;
        --text-dim: #555; --text-mid: #888; --radius-lg: 18px;
    }}
    :root.light {{
        --bg: #f5f5f0; --surface: #ffffff; --surface2: #f0efe8;
        --border: rgba(0,0,0,0.09); --gold: #b8902a; --blue: #3d7fd4;
        --green: #3a9068; --red: #cc3333; --text: #1a1a1a;
        --text-dim: #999; --text-mid: #555;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
        font-family: 'DM Sans', sans-serif; background: var(--bg); color: var(--text);
        min-height: 100vh; display: flex; justify-content: center;
        padding: 20px; transition: background 0.3s, color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 50% at 50% -5%, rgba(99,160,240,0.09) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 90%, rgba(201,168,76,0.05) 0%, transparent 60%);
    }}
    .card {{
        width: 100%; max-width: 400px; background: var(--surface);
        border: 1px solid var(--border); border-radius: var(--radius-lg);
        overflow: hidden; position: relative;
        box-shadow: 0 30px 80px rgba(0,0,0,0.6); animation: fadeIn 0.35s ease; text-align: center;
    }}
    :root.light .card {{ box-shadow: 0 8px 40px rgba(0,0,0,0.12); }}
    .card::before {{
        content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
        background: linear-gradient(90deg, transparent, var(--red), var(--gold), transparent);
    }}
    @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(12px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    .card-top {{ padding: 22px 24px 16px; border-bottom: 1px solid var(--border); position: relative; }}
    .logo {{ font-family: 'DM Sans', sans-serif; font-size: 1.2em; font-weight: 800; color: var(--gold); margin-bottom: 3px; }}
    .subtitle {{ font-size: 0.72em; color: var(--text-dim); }}
    .theme-toggle {{
        position: absolute; top: 16px; right: 16px;
        background: var(--surface2); border: 1px solid var(--border);
        border-radius: 8px; width: 32px; height: 32px;
        display: flex; align-items: center; justify-content: center;
        cursor: pointer; font-size: 0.95em; transition: all 0.2s;
    }}
    .theme-toggle:hover {{ border-color: var(--gold); }}
    .session-box {{ padding: 16px 24px; border-bottom: 1px solid var(--border); }}
    .session-label {{ font-size: 0.62em; font-weight: 700; color: var(--red); letter-spacing: 2px; text-transform: uppercase; margin-bottom: 4px; }}
    .session-title {{ font-family: 'DM Sans', sans-serif; font-size: 1.3em; font-weight: 800; color: var(--text); }}
    .status-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; padding: 14px 24px; border-bottom: 1px solid var(--border); }}
    .status-item {{ background: var(--surface2); border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; text-align: left; }}
    .status-item small {{ display: block; font-size: 0.6em; color: var(--text-dim); letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 4px; }}
    .status-item b {{ font-size: 0.85em; font-weight: 700; }}
    .card-actions {{ padding: 14px 24px; border-bottom: 1px solid var(--border); }}
    .btn-login {{
        display: block; padding: 13px;
        background: linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color: #000; border-radius: 10px; text-decoration: none;
        font-family: 'DM Sans', sans-serif; font-weight: 700;
        font-size: 0.92em; line-height: 1.5; letter-spacing: 0.5px; transition: all 0.2s;
    }}
    .btn-login:hover {{ transform: translateY(-1px); box-shadow: 0 6px 20px rgba(201,168,76,0.25); }}
    .progress-bar {{ height: 3px; background: var(--surface2); border-radius: 0; overflow: hidden; margin-top: 8px; }}
    .progress-fill {{ height: 100%; background: var(--gold); width: 100%; animation: drain 5s linear forwards; }}
    @keyframes drain {{ from {{ width: 100%; }} to {{ width: 0%; }} }}
    .card-footer {{ padding: 12px 24px 16px; }}
    .footer-link {{ display: block; font-size: 0.65em; color: var(--text-dim); text-decoration: none; margin-bottom: 10px; }}
    .footer-link span {{ color: var(--blue); }}
    .legal-box {{ background: var(--surface2); border: 1px solid var(--border); border-radius: 8px; padding: 8px 12px; text-align: left; }}
    .legal-title {{ font-size: 0.6em; font-weight: 700; color: var(--red); letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 3px; }}
    .legal-text {{ font-size: 0.67em; color: var(--text-dim); line-height: 1.4; }}
</style>
<script>
    setTimeout(function() {{ window.location.href = "/login"; }}, 5000);
</script>
</head>
<body>
<div class="card">
    <div class="card-top">
        <div class="logo">🏠 {NAME} </div>
        <div class="subtitle">La tua finanza domestica, in perfetto ordine.</div>
        <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
    </div>
    <div class="session-box">
        <div class="session-label">🔴 Sessione Terminata — {ora_fine}</div>
        <div class="session-title">Logoff Eseguito</div>
    </div>
    <div class="status-grid">
        <div class="status-item">
            <small>Token Stato</small>
            <b style="color:var(--red)">REVOCATO</b>
        </div>
        <div class="status-item">
            <small>Database</small>
            <b style="color:var(--green)">PROTETTO</b>
        </div>
    </div>
    <div class="card-actions">
        <a href="/login" class="btn-login">RE-LOGIN 🔐</a>
        <div class="progress-bar">
            <div class="progress-fill"></div>
        </div>
    </div>
    <div class="card-footer">
        <a href="mailto:helporbitacasa@gmail.com" class="footer-link">
            v{VERSION} — Supporto: <span>helporbitacasa@gmail.com</span>
        </a>
        <div class="legal-box">
            <div class="legal-title">⚠️ Disconnessione Sicura</div>
            <div class="legal-text">I dati di sessione sono stati rimossi. L'accesso non autorizzato è perseguibile ai sensi dell'<strong>Art. 615-ter C.P.</strong></div>
        </div>
    </div>
</div>
<script>
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if (btn) btn.textContent = '🌙'; }}
        else               {{ root.classList.remove('light'); if (btn) btn.textContent = '☀️'; }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        applyTheme(next);
    }}
    applyTheme(localStorage.getItem('theme') || 'dark');
</script>
</body>
</html>"""


def html_fairshare_web(self):
    anno_corrente = str(datetime.date.today().year)
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>⚖️ FairShare</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>(function() {{ if (localStorage.getItem('theme') === 'light') document.documentElement.classList.add('light'); }})();</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<style>
    :root {{
        --bg:#050505; --surface:#0f0f0f; --surface2:#161616; --surface3:#1e1e1e;
        --border:rgba(255,255,255,0.07); --gold:#c9a84c; --blue:#63a0f0;
        --green:#4caf82; --red:#e05a5a; --text:#e8e8e8; --text-dim:#555; --text-mid:#888;
        --radius-lg:16px;
    }}
    :root.light {{
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --gold:#b8902a; --blue:#3d7fd4;
        --green:#3a9068; --red:#cc3333; --text:#1a1a1a; --text-dim:#999; --text-mid:#555;
    }}
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{
        font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text);
        min-height:100vh; padding-bottom:40px;
    }}
    header {{
        padding:12px 16px; display:flex; align-items:center; justify-content:center;
        border-bottom:1px solid var(--border); background:rgba(5,5,5,0.95);
        backdrop-filter:blur(20px); position:sticky; top:0; z-index:100;
    }}
    :root.light header {{ background:rgba(245,245,240,0.95); }}
    .menu-btn {{
        position:absolute; left:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border); color:var(--gold);
        width:34px; height:34px; border-radius:9px; font-size:1em;
        cursor:pointer; display:flex; align-items:center; justify-content:center;
    }}
    .theme-toggle {{
        position:absolute; right:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border);
        border-radius:8px; width:34px; height:34px;
        display:flex; align-items:center; justify-content:center; cursor:pointer;
    }}
    .nav-dropdown {{
        position:absolute; top:calc(100% + 6px); left:10px;
        background:var(--surface2); border:1px solid var(--border);
        border-radius:var(--radius-lg); display:none; z-index:1000;
        width:270px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.7);
    }}
    .nav-dropdown a {{
        display:flex; align-items:center; gap:10px; padding:10px 16px;
        text-decoration:none; color:var(--text-mid); border-bottom:1px solid var(--border);
        font-size:0.87em; transition:all 0.15s;
    }}
    .nav-dropdown a:last-child {{ border-bottom:none; }}
    .nav-dropdown a:hover {{ background:var(--surface3); color:var(--text); padding-left:22px; }}
    .nav-group-btn {{ display:flex; justify-content:space-between; align-items:center; width:100%;
        padding:8px 16px; background:none; border:none; font-family:inherit; color:var(--gold);
        font-size:0.7em; font-weight:700; letter-spacing:1px; text-transform:uppercase; cursor:pointer; opacity:0.85; }}
    .nav-group-btn:hover {{ opacity:1; background:var(--surface3); }}
    .nav-arrow {{ font-size:0.85em; transition:transform 0.15s; }}
    .nav-group-items {{ display:none; flex-direction:column; }}
    .nav-group-items.open {{ display:flex; }}
    main {{ padding:12px 14px; max-width:680px; margin:0 auto; }}
    .filtri {{ display:flex; gap:8px; flex-wrap:wrap; margin:12px 0; }}
    .filtri select {{
        flex:1; min-width:100px; padding:9px 12px;
        background:var(--surface2); border:1px solid var(--border);
        border-radius:9px; color:var(--text); font-family:'DM Sans',sans-serif;
        font-size:0.88em; outline:none; cursor:pointer;
        -webkit-appearance:none; appearance:none;
    }}
    .btn-aggiorna {{
        padding:9px 20px; background:linear-gradient(135deg,var(--gold),#8a6820);
        color:#000; border:none; border-radius:9px; font-family:'DM Sans',sans-serif;
        font-weight:700; font-size:0.88em; cursor:pointer; white-space:nowrap;
    }}
    .section-title {{
        font-size:0.7em; font-weight:700; letter-spacing:2px; text-transform:uppercase;
        color:var(--text-dim); margin:18px 0 8px;
    }}
    .card {{
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); overflow:hidden; margin-bottom:10px;
    }}
    .totali-bar {{ display:grid; grid-template-columns:1fr 1fr; gap:6px; padding:12px; }}
    .tot-item {{
        background:var(--surface2); border-radius:8px; padding:9px 8px;
        text-align:center; border:1px solid var(--border);
    }}
    .tot-item small {{
        display:block; font-size:0.6em; color:var(--text-dim);
        letter-spacing:1.2px; text-transform:uppercase; margin-bottom:3px;
    }}
    .tot-item b {{ font-size:0.95em; font-weight:700; }}
    table {{ width:100%; border-collapse:collapse; font-size:0.82em; }}
    th {{
        padding:8px 10px; text-align:left; font-size:0.65em; font-weight:700;
        letter-spacing:1.5px; text-transform:uppercase; color:var(--text-dim);
        border-bottom:1px solid var(--border);
    }}
    td {{ padding:9px 10px; border-bottom:1px solid var(--border); vertical-align:middle; }}
    tr:last-child td {{ border-bottom:none; }}
    tr:hover td {{ background:var(--surface2); }}
    .saldo-ok  {{ color:var(--green); font-weight:700; }}
    .saldo-no  {{ color:var(--red);   font-weight:700; }}
    .saldo-zer {{ color:var(--text-mid); }}
    .chart-wrap {{ padding:14px; position:relative; height:220px; }}
    .tabs {{ display:flex; border-bottom:1px solid var(--border); }}
    .tab {{
        padding:10px 16px; font-size:0.78em; font-weight:600; cursor:pointer;
        color:var(--text-mid); border-bottom:2px solid transparent; transition:all 0.2s;
    }}
    .tab.active {{ color:var(--gold); border-bottom-color:var(--gold); }}
    .tab-content {{ display:none; }}
    .tab-content.active {{ display:block; }}
    .chi-row {{
        display:flex; justify-content:space-between; align-items:center;
        padding:10px 14px; border-bottom:1px solid var(--border); font-size:0.88em;
    }}
    .chi-row:last-of-type {{ border-bottom:none; }}
    .pers-card {{
        background:var(--surface2); border-radius:10px; padding:12px;
        margin-bottom:8px; border:1px solid var(--border);
    }}
    .pers-name {{ font-size:0.88em; font-weight:700; margin-bottom:8px; }}
    .pers-totali {{ display:flex; gap:6px; margin-bottom:10px; }}
    .pers-tot {{
        flex:1; background:var(--surface); border-radius:7px; padding:6px 8px;
        text-align:center; border:1px solid var(--border);
    }}
    .pers-tot small {{ display:block; font-size:0.58em; color:var(--text-dim); letter-spacing:1px; text-transform:uppercase; }}
    .pers-tot b {{ font-size:0.85em; font-weight:700; }}
    .pers-chart-wrap {{ position:relative; height:160px; }}
    #loading {{ text-align:center; padding:40px; color:var(--text-dim); font-size:0.85em; }}
</style>
</head>
<body>
<header>
    <button class="menu-btn" onclick="toggleMenu()">⚙️</button>
    <div id="extraMenu" class="nav-dropdown">
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Finanze</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/">🏠 Aggiungi Operazione</a>
                <a href="/lista">📈 Gestione Movimenti Mese</a>
                <a href="/stats">📊 Bilancio Mese</a>
                <a href="/fondo_risparmio_web">💰 Fondo Risparmio</a>
                <a href="/scadenze_web">📅 Scadenze del Mese</a>
                <a href="/fairshare_web">⚖️ FairShare</a>
                <a href="/menu_esplora">🔍 Esplora</a>
                <a href="/grafici_web">📅 Grafici e Statistiche</a>
                <a href="/gestione_categorie">⚙️ Gestione Categorie</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Casa</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/utenze?anno={anno_corrente}">💧 Utenze</a>
                <a href="/consultazione_supermercati">🛒 Supermercati</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Documenti</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/documenti_pdf_web">🗄️ Documenti Contabili</a>
                <a href="/documenti_personali_web">🗄️ Documenti Personali</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Sistema</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/info_sys_web">📡 Monitor Server</a>
                <a href="/cambia_pw_web">🔑 Cambia Password</a>
                <a href="/webauthn_web">👆 Biometrico</a>
                <a href="/cambia_profilo_web">👤 Cambia Profilo</a>
                <a href="/logoff">🔓 Logout</a>
            </div>
        </div>
    </div>
    <div style="text-align:center">
        <div style="font-size:0.95em;font-weight:700">⚖️ FairShare</div>
        <div style="font-size:0.6em;color:var(--text-dim);letter-spacing:2px;text-transform:uppercase">Dare & Avere</div>
    </div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()">🌙</button>
</header>
<main>
    <div class="filtri">
        <select id="f_anno"><option value="0">Tutti gli anni</option></select>
        <select id="f_mese">
            <option value="0">Tutti i mesi</option>
            <option value="1">Gennaio</option><option value="2">Febbraio</option>
            <option value="3">Marzo</option><option value="4">Aprile</option>
            <option value="5">Maggio</option><option value="6">Giugno</option>
            <option value="7">Luglio</option><option value="8">Agosto</option>
            <option value="9">Settembre</option><option value="10">Ottobre</option>
            <option value="11">Novembre</option><option value="12">Dicembre</option>
        </select>
        <select id="f_utente"><option value="tutti">Tutti</option></select>
        <button class="btn-aggiorna" onclick="carica()">↻ Aggiorna</button>
    </div>
    <div id="loading">⏳ Caricamento...</div>
    <div id="contenuto" style="display:none">
        <div class="tabs">
            <div class="tab active" onclick="switchTab('tab_da')">👥 Dare & Avere</div>
            <div class="tab" onclick="switchTab('tab_pers')">⚖️ Personali</div>
        </div>
        <div id="tab_da" class="tab-content active">
            <div class="section-title">Riepilogo</div>
            <div class="card">
                <div class="totali-bar">
                    <div class="tot-item">
                        <small>Totale Dovuto</small>
                        <b id="tot_dovuto" style="color:var(--gold)">-</b>
                    </div>
                    <div class="tot-item">
                        <small>Residuo Aperto</small>
                        <b id="tot_residuo" style="color:var(--red)">-</b>
                    </div>
                </div>
                <div class="chart-wrap">
                    <canvas id="chartDA"></canvas>
                </div>
            </div>
            <div class="section-title">Per Persona</div>
            <div class="card" style="overflow-x:auto">
                <table>
                    <thead>
                        <tr>
                            <th>Persona</th>
                            <th>Dovuto</th>
                            <th>Versato</th>
                            <th>Residuo</th>
                        </tr>
                    </thead>
                    <tbody id="tbody_da"></tbody>
                </table>
            </div>
            <div class="section-title">💸 Chi Deve a Chi</div>
            <div class="card">
                <div id="chi_deve_list"></div>
            </div>
        </div>
        <div id="tab_pers" class="tab-content">
            <div class="section-title">Conti Personali ⚖️</div>
            <div id="pers_container"></div>
        </div>
    </div>
</main>
<script>
    const ANNO_CORRENTE = "{anno_corrente}";
    let chartDA = null;
    let chartsPers = {{}};
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if(btn) btn.textContent='🌙'; }}
        else {{ root.classList.remove('light'); if(btn) btn.textContent='☀️'; }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme')||'dark')==='dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next); applyTheme(next);
    }}
    applyTheme(localStorage.getItem('theme')||'dark');

    function toggleNavGroup(btn, ev) {{
        if (ev) ev.stopPropagation();
        const items = btn.nextElementSibling;
        const giaAperto = items.classList.contains('open');
        btn.closest('.nav-dropdown').querySelectorAll('.nav-group-items.open').forEach(function(el) {{
            el.classList.remove('open');
            el.previousElementSibling.querySelector('.nav-arrow').textContent = '▶';
        }});
        if (!giaAperto) {{
            items.classList.add('open');
            btn.querySelector('.nav-arrow').textContent = '▼';
        }}
    }}
    function toggleMenu() {{
        const m = document.getElementById("extraMenu");
        m.style.display = m.style.display==="block" ? "none" : "block";
    }}
    document.addEventListener("click", function(e) {{
        const m = document.getElementById("extraMenu");
        if (m && m.style.display==="block" && !m.contains(e.target) && !e.target.matches('.menu-btn'))
            m.style.display = "none";
    }});
    function switchTab(id) {{
        document.querySelectorAll('.tab').forEach((t,i) => {{
            t.classList.toggle('active', ['tab_da','tab_pers'][i] === id);
        }});
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.getElementById(id).classList.add('active');
    }}
    function fmt(v) {{
        v = Number(v || 0);
        const neg = v < 0;
        const parts = Math.abs(v).toFixed(2).split('.');
        parts[0] = parts[0].replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, '.');
        return "€ " + (neg ? '-' : '') + parts[0] + ',' + parts[1];
    }}
    async function carica() {{
        const anno   = document.getElementById("f_anno").value;
        const mese   = document.getElementById("f_mese").value;
        const utente = document.getElementById("f_utente").value;
        document.getElementById("loading").style.display = "block";
        document.getElementById("contenuto").style.display = "none";
        try {{
            const r = await fetch(`/get_fairshare_data?anno=${{anno}}&mese=${{mese}}&utente=${{encodeURIComponent(utente)}}`);
            const d = await r.json();
            renderDA(d);
            renderPersonali(d);
            aggiornaFiltriUtenti(d);
            document.getElementById("loading").style.display = "none";
            document.getElementById("contenuto").style.display = "block";
        }} catch(e) {{
            document.getElementById("loading").innerHTML = "❌ Errore caricamento dati";
        }}
    }}
    function aggiornaFiltriUtenti(d) {{
        const sel = document.getElementById("f_utente");
        const cur = sel.value;
        while (sel.options.length > 1) sel.remove(1);
        (d.utenti_personali||[]).forEach(n => {{
            const o = document.createElement("option");
            o.value = n; o.textContent = "⚖️ " + n;
            sel.appendChild(o);
        }});
        sel.value = cur || "tutti";
    }}
    function renderDA(d) {{
        document.getElementById("tot_dovuto").textContent  = fmt(d.tot_dovuto);
        document.getElementById("tot_residuo").textContent = fmt(d.tot_residuo);
        const tbody = document.getElementById("tbody_da");
        tbody.innerHTML = "";
        (d.persone||[]).forEach(p => {{
            const tr = document.createElement("tr");
            let cls = "saldo-zer";
            if (p.residuo > 0.01) cls = "saldo-no";
            else if (p.residuo < -0.01) cls = "saldo-ok";
            tr.innerHTML = `
                <td><b>PER· ${{p.nome}}</b></td>
                <td style="color:var(--gold)">${{fmt(p.dovuto)}}</td>
                <td style="color:var(--green)">${{fmt(p.versato)}}</td>
                <td class="${{cls}}">${{p.residuo < 0.01 ? '✅ Saldato' : '🔴 ' + fmt(p.residuo)}}</td>`;
            tbody.appendChild(tr);
        }});
        if (chartDA) chartDA.destroy();
        const ctx = document.getElementById("chartDA").getContext("2d");
        const labels  = (d.persone||[]).map(p => p.nome);
        const dovuti  = (d.persone||[]).map(p => p.dovuto);
        const versati = (d.persone||[]).map(p => p.versato);
        chartDA = new Chart(ctx, {{
            type: "bar",
            data: {{
                labels,
                datasets: [
                    {{ label:"Dovuto",  data:dovuti,  backgroundColor:"rgba(201,168,76,0.7)",  borderRadius:4 }},
                    {{ label:"Versato", data:versati, backgroundColor:"rgba(76,175,130,0.7)", borderRadius:4 }}
                ]
            }},
            options: {{
                responsive:true, maintainAspectRatio:false,
                plugins:{{ legend:{{ labels:{{ color:"#888", font:{{ size:10 }} }} }} }},
                scales:{{
                    x:{{ ticks:{{ color:"#888", font:{{ size:10 }} }}, grid:{{ color:"rgba(255,255,255,0.04)" }} }},
                    y:{{ ticks:{{ color:"#888", font:{{ size:10 }}, callback: v => fmt(v) }}, grid:{{ color:"rgba(255,255,255,0.04)" }} }}
                }}
            }}
        }});
        const chiList = document.getElementById("chi_deve_list");
        if (!d.chi_deve || d.chi_deve.length === 0) {{
            chiList.innerHTML = "<div style='padding:14px;color:var(--text-dim);font-size:0.85em'>Tutti in pari ✅</div>";
        }} else {{
            chiList.innerHTML = d.chi_deve.map(t => `
                <div class="chi-row">
                    <div>
                        <span style="color:var(--red);font-weight:700">${{t.da}}</span>
                        <span style="color:var(--text-dim);margin:0 8px">→</span>
                        <span style="color:var(--green);font-weight:700">${{t.a}}</span>
                    </div>
                    <div style="font-weight:700;color:var(--gold)">${{fmt(t.importo)}}</div>
                </div>`).join("");
        }}
    }}
    function renderPersonali(d) {{
        const container = document.getElementById("pers_container");
        container.innerHTML = "";
        Object.values(chartsPers).forEach(c => c.destroy());
        chartsPers = {{}};
        if (!d.personali || d.personali.length === 0) {{
            container.innerHTML = "<div style='text-align:center;padding:30px;color:var(--text-dim);font-size:0.85em'>Nessun conto personale configurato</div>";
            return;
        }}
        d.personali.forEach((p, idx) => {{
            const saldo    = p.tot_ent - p.tot_usc;
            const saldoCol = saldo >= 0 ? "var(--green)" : "var(--red)";
            const chartId  = `chartPers_${{idx}}`;
            const div      = document.createElement("div");
            div.className  = "pers-card";
            div.innerHTML  = `
                <div class="pers-name">CTP· ${{p.nome}}</div>
                <div class="pers-totali">
                    <div class="pers-tot"><small>Entrate</small><b style="color:var(--green)">${{fmt(p.tot_ent)}}</b></div>
                    <div class="pers-tot"><small>Uscite</small><b style="color:var(--red)">${{fmt(p.tot_usc)}}</b></div>
                    <div class="pers-tot"><small>Saldo</small><b style="color:${{saldoCol}}">${{fmt(saldo)}}</b></div>
                </div>
                <div class="pers-chart-wrap"><canvas id="${{chartId}}"></canvas></div>`;
            container.appendChild(div);
            if (p.categorie && p.categorie.length > 0) {{
                const top = p.categorie.slice(0,10);
                const ctx = document.getElementById(chartId).getContext("2d");
                chartsPers[chartId] = new Chart(ctx, {{
                    type:"bar",
                    data:{{
                        labels: top.map(c=>c.cat),
                        datasets:[
                            {{label:"Entrate",data:top.map(c=>c.ent),backgroundColor:"rgba(76,175,130,0.7)",borderRadius:3}},
                            {{label:"Uscite", data:top.map(c=>c.usc),backgroundColor:"rgba(224,90,90,0.7)", borderRadius:3}}
                        ]
                    }},
                    options:{{
                        responsive:true,maintainAspectRatio:false,
                        plugins:{{legend:{{labels:{{color:"#888",font:{{size:9}}}}}}}},
                        scales:{{
                            x:{{ticks:{{color:"#888",font:{{size:9}},maxRotation:30}},grid:{{color:"rgba(255,255,255,0.04)"}}}},
                            y:{{ticks:{{color:"#888",font:{{size:9}},callback:v=>fmt(v)}},grid:{{color:"rgba(255,255,255,0.04)"}}}}
                        }}
                    }}
                }});
            }} else {{
                document.getElementById(chartId).parentElement.innerHTML =
                    "<div style='text-align:center;padding:20px;color:var(--text-dim);font-size:0.8em'>Nessun movimento</div>";
            }}
        }});
    }}
    window.addEventListener('load', async function() {{
        try {{
            const r = await fetch("/get_fairshare_data?anno=0&mese=0&utente=tutti");
            const d = await r.json();
            const sel = document.getElementById("f_anno");
            (d.anni||[]).forEach(a => {{
                const o = document.createElement("option");
                o.value = a; o.textContent = a;
                if (a === ANNO_CORRENTE) o.selected = true;
                sel.appendChild(o);
            }});
            aggiornaFiltriUtenti(d);
        }} catch(e) {{}}
        carica();
    }});
</script>
</body>
</html>"""
        
# Html Gestione Documenti Contabili Web
def documenti_pdf_web(self):
    import datetime
    from datetime import datetime as dt
    import os
    import __main__ as _app
    DB_DIR = _app.DB_DIR
    DOC_DIR = _app.DOC_DIR
    REGISTRY_FILE = _app.REGISTRY_FILE
    oggi = datetime.date.today()
    def bytes_to_human(byte_count):
        if byte_count is None: return "0 B"
        byte_count = int(byte_count)
        if byte_count < 1024: return f"{byte_count} B"
        elif byte_count < 1024 ** 2: return f"{byte_count / 1024:.2f} KB"
        else: return f"{byte_count / (1024 ** 2):.2f} MB"
    registry_file_path = REGISTRY_FILE
    doc_dir = DOC_DIR
    dati_json = getattr(self, 'archivi_pdf', {})
    if not dati_json and os.path.exists(registry_file_path):
        try:
            with open(registry_file_path, "r", encoding="utf-8") as f:
                dati_json = json.load(f)
        except:
            dati_json = {}
    archivi_dati_strutturati = []
    categorie_set = set()
    for nome_file, dettagli in dati_json.items():
        percorso_fisico_check = os.path.join(doc_dir, nome_file)
        if not os.path.exists(percorso_fisico_check):
            continue
        try:
            data_raw = dettagli.get("data_raw")
            data_obj = dt.strptime(data_raw, "%d%m%Y").date() if data_raw else datetime.date.today()
        except:
            data_obj = datetime.date.today()
        cat = dettagli.get('categoria_esatta', 'Generico')
        categorie_set.add(cat)
        importo_raw = dettagli.get('importo_raw', 0)
        tipo_doc = dettagli.get('tipo_esatto', 'Uscita')
        segno_doc = "+" if tipo_doc == "Entrata" else "-"
        try:
            importo_val = float(importo_raw) / 100 if isinstance(importo_raw, (int, float)) else 0.0
        except:
            importo_val = 0.0
        archivi_dati_strutturati.append({
            "nome_file": nome_file,
            "data_caricamento": data_obj,
            "data_str": data_obj.strftime("%d/%m/%Y"),
            "data_iso": data_obj.isoformat(),
            "descrizione": dettagli.get('descrizione_esatta', 'N/D'),
            "categoria": cat,
            "importo_val": importo_val,
            "importo_str": f"€ {segno_doc}{_fmt_it(importo_val)}",
            "dimensione": bytes_to_human(os.path.getsize(percorso_fisico_check))
        })
    archivi_ordinati = sorted(archivi_dati_strutturati, key=lambda x: x["data_caricamento"], reverse=True)
    categorie_options = "".join(
        f"<option value='{c}'>{c}</option>"
        for c in sorted(categorie_set)
    )
    docs_js = json.dumps([{
        "nome": a["nome_file"],
        "data": a["data_str"],
        "data_iso": a["data_iso"],
        "desc": a["descrizione"],
        "cat": a["categoria"],
        "imp": a["importo_val"],
        "imp_str": a["importo_str"],
        "dim": a["dimensione"]
    } for a in archivi_ordinati])
    anno_corrente = oggi.year
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>🗄️ Documenti Contabili</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
    (function() {{
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    }})();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg:#050505; --surface:#0f0f0f; --surface2:#161616; --surface3:#1e1e1e;
        --border:rgba(255,255,255,0.07); --border-active:rgba(99,160,240,0.5);
        --gold:#c9a84c; --blue:#63a0f0; --green:#4caf82; --red:#e05a5a;
        --text:#e8e8e8; --text-dim:#555; --text-mid:#888; --radius-lg:18px;
    }}
    :root.light {{
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --border-active:rgba(61,127,212,0.5);
        --gold:#b8902a; --blue:#3d7fd4; --green:#3a9068; --red:#cc3333;
        --text:#1a1a1a; --text-dim:#999; --text-mid:#555;
    }}
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{
        font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text);
        min-height:100vh; padding-bottom:50px; transition:background 0.3s,color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 40% at 50% -10%, rgba(99,160,240,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 60%);
    }}
    header {{
        padding:14px 16px 12px; display:flex; align-items:center; justify-content:center;
        border-bottom:1px solid var(--border); background:rgba(5,5,5,0.95);
        backdrop-filter:blur(20px); position:sticky; top:0; z-index:100;
    }}
    :root.light header {{ background:rgba(245,245,240,0.95); }}
    .menu-btn {{
        position:absolute; left:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border); color:var(--gold);
        width:36px; height:36px; border-radius:10px; font-size:1em;
        cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.2s;
    }}
    .menu-btn:hover {{ border-color:var(--gold); box-shadow:0 0 12px rgba(201,168,76,0.2); }}
    .header-title {{ font-family:'DM Sans',sans-serif; font-size:1em; font-weight:700; color:var(--text); }}
    .theme-toggle {{
        position:absolute; right:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border);
        border-radius:8px; width:34px; height:34px;
        display:flex; align-items:center; justify-content:center;
        cursor:pointer; font-size:1em; transition:all 0.2s;
    }}
    .theme-toggle:hover {{ border-color:var(--gold); }}
    .nav-dropdown {{
        position:absolute; top:calc(100% + 6px); left:10px;
        background:var(--surface2); border:1px solid var(--border);
        border-radius:var(--radius-lg); display:none; z-index:1000;
        width:270px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.7);
    }}
    .nav-dropdown a {{
        display:flex; align-items:center; gap:10px; padding:10px 16px;
        text-decoration:none; color:var(--text-mid); border-bottom:1px solid var(--border);
        font-size:0.87em; transition:all 0.15s;
    }}
    .nav-dropdown a:last-child {{ border-bottom:none; }}
    .nav-dropdown a:hover {{ background:var(--surface3); color:var(--text); padding-left:22px; }}
    .nav-group-btn {{ display:flex; justify-content:space-between; align-items:center; width:100%;
        padding:8px 16px; background:none; border:none; font-family:inherit; color:var(--gold);
        font-size:0.7em; font-weight:700; letter-spacing:1px; text-transform:uppercase; cursor:pointer; opacity:0.85; }}
    .nav-group-btn:hover {{ opacity:1; background:var(--surface3); }}
    .nav-arrow {{ font-size:0.85em; transition:transform 0.15s; }}
    .nav-group-items {{ display:none; flex-direction:column; }}
    .nav-group-items.open {{ display:flex; }}
    main {{ padding:14px; max-width:680px; margin:0 auto; animation:fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .filter-card {{
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); padding:14px 16px 16px;
        margin-bottom:10px; position:relative; overflow:hidden; margin-top:14px;
    }}
    .filter-card::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .filter-row {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:8px; }}
    .filter-group label {{
        display:block; font-size:0.6em; font-weight:700; color:var(--text-dim);
        letter-spacing:1.5px; text-transform:uppercase; margin-bottom:5px;
    }}
    input[type="text"], input[type="number"], input[type="date"], select {{
        width:100%; padding:9px 12px;
        background:var(--surface2); border:1px solid var(--border);
        border-radius:8px; color:var(--text);
        font-family:'DM Sans',sans-serif; font-size:0.88em;
        outline:none; transition:all 0.2s;
        -webkit-appearance:none; appearance:none;
    }}
    input:focus, select:focus {{ border-color:var(--border-active); background:var(--surface3); }}
    input::placeholder {{ color:var(--text-dim); }}
    select {{
        background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='7' viewBox='0 0 12 7'%3E%3Cpath fill='none' stroke='%23555' stroke-width='1.5' d='M1 1l5 5 5-5'/%3E%3C/svg%3E");
        background-repeat:no-repeat; background-position:right 10px center;
        padding-right:28px; cursor:pointer;
    }}
    select option {{ background:var(--surface2); color:var(--text); }}
    .filter-actions {{ display:flex; gap:8px; margin-top:6px; }}
    .btn-filter {{
        flex:1; padding:10px; border:none; border-radius:8px;
        font-family:'DM Sans',sans-serif; font-size:0.88em; font-weight:700;
        line-height:1.5; cursor:pointer; transition:all 0.2s;
    }}
    .btn-filter.apply {{ background:linear-gradient(135deg, var(--gold), #8a6820); color:#000; }}
    .btn-filter.apply:hover {{ transform:translateY(-1px); box-shadow:0 4px 16px rgba(201,168,76,0.25); }}
    .btn-filter.reset {{ background:var(--surface2); border:1px solid var(--border); color:var(--text-mid); }}
    .btn-filter.reset:hover {{ border-color:var(--border-active); color:var(--text); }}
    .results-bar {{
        display:flex; justify-content:space-between; align-items:center;
        margin-bottom:8px; font-size:0.75em; color:var(--text-dim);
    }}
    .results-count {{ color:var(--blue); font-weight:700; font-size:1.1em; }}
    .doc-list {{
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); overflow:hidden;
        position:relative; margin-bottom:10px; min-height:60px;
    }}
    .doc-list::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .doc-item {{
        display:flex; align-items:center; justify-content:space-between;
        padding:11px 16px; border-bottom:1px solid var(--border); gap:10px; transition:background 0.15s;
    }}
    .doc-item:last-child {{ border-bottom:none; }}
    .doc-item:hover {{ background:var(--surface2); }}
    .doc-main {{ flex:1; overflow:hidden; }}
    .doc-date {{ font-size:0.65em; color:var(--text-dim); margin-bottom:2px; }}
    .doc-cat {{
        font-size:0.88em; font-weight:700; color:var(--blue);
        text-decoration:none; display:block; margin-bottom:2px; transition:color 0.15s;
    }}
    .doc-cat:hover {{ color:var(--gold); }}
    .doc-desc {{ font-size:0.77em; color:var(--text-mid); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; margin-bottom:3px; }}
    .doc-meta {{ display:flex; gap:10px; align-items:center; }}
    .doc-importo {{ font-size:0.75em; font-weight:700; color:var(--gold); }}
    .doc-dim {{ font-size:0.7em; color:var(--text-dim); }}
    .doc-dl {{ font-size:1.2em; text-decoration:none; opacity:0.5; transition:opacity 0.15s; flex-shrink:0; }}
    .doc-dl:hover {{ opacity:1; }}
    .empty-msg {{ text-align:center; padding:30px; color:var(--text-dim); font-size:0.85em; font-style:italic; }}
    .pagination {{ display:flex; justify-content:center; gap:6px; margin-bottom:10px; flex-wrap:wrap; }}
    .pg-btn {{
        padding:7px 13px; border:1px solid var(--border); border-radius:8px;
        background:var(--surface); color:var(--text-mid);
        font-family:'DM Sans',sans-serif; font-size:0.8em; font-weight:700;
        cursor:pointer; transition:all 0.15s; line-height:1.5;
    }}
    .pg-btn:hover {{ border-color:var(--border-active); color:var(--text); }}
    .pg-btn.active {{ background:var(--gold); color:#000; border-color:var(--gold); }}
    .pg-btn[disabled] {{ opacity:0.3; cursor:default; pointer-events:none; }}
    .pg-ellipsis {{ padding:7px 4px; color:var(--text-dim); font-size:0.8em; }}
    .btn-home {{
        display:block; text-align:center; padding:13px;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; border-radius:10px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.9em;
        line-height:1.5; transition:all 0.2s;
    }}
    .btn-home:hover {{ transform:translateY(-1px); box-shadow:0 6px 20px rgba(201,168,76,0.25); }}
</style>
</head>
<body>
<header>
    <button class="menu-btn" onclick="toggleMenu()">⚙️</button>
    <div id="extraMenu" class="nav-dropdown">
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Finanze</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/">🏠 Aggiungi Operazione</a>
                <a href="/lista">📈 Gestione Movimenti Mese</a>
                <a href="/stats">📊 Bilancio Mese</a>
                <a href="/fondo_risparmio_web">💰 Fondo Risparmio</a>
                <a href="/scadenze_web">📅 Scadenze del Mese</a>
                <a href="/fairshare_web">⚖️ FairShare</a>
                <a href="/menu_esplora">🔍 Esplora</a>
                <a href="/grafici_web">📅 Grafici e Statistiche</a>
                <a href="/gestione_categorie">⚙️ Gestione Categorie</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Casa</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/utenze?anno={anno_corrente}">💧 Utenze</a>
                <a href="/consultazione_supermercati">🛒 Gestione Supermercati</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Documenti</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/documenti_pdf_web">🗄️ Documenti Contabili</a>
                <a href="/documenti_personali_web">🗄️ Documenti Personali</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Sistema</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/info_sys_web">📡 Monitor Server</a>
                <a href="/cambia_pw_web">🔑 Cambia Password</a>
                <a href="/webauthn_web">👆 Biometrico</a>
                <a href="/cambia_profilo_web">👤 Cambia Profilo</a>
                <a href="/logoff">🔓 Logout</a>
            </div>
        </div>
    </div>
    <div class="header-title">🗄️ Documenti Contabili</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="filter-card">
        <div class="filter-row">
            <div class="filter-group">
                <label>Descrizione</label>
                <input type="text" id="f_desc" placeholder="es: bolletta, fattura...">
            </div>
            <div class="filter-group">
                <label>Categoria</label>
                <select id="f_cat">
                    <option value="">-- Tutte --</option>
                    {categorie_options}
                </select>
            </div>
        </div>
        <div class="filter-row">
            <div class="filter-group">
                <label>Data da</label>
                <input type="date" id="f_data_da">
            </div>
            <div class="filter-group">
                <label>Data a</label>
                <input type="date" id="f_data_a">
            </div>
        </div>
        <div class="filter-row">
            <div class="filter-group">
                <label>Importo da (€)</label>
                <input type="number" id="f_imp_da" step="0.01" min="0" placeholder="es: 10.00">
            </div>
            <div class="filter-group">
                <label>Importo a (€)</label>
                <input type="number" id="f_imp_a" step="0.01" min="0" placeholder="es: 500.00">
            </div>
        </div>
        <div class="filter-actions">
            <button class="btn-filter apply" onclick="applicaFiltri()">🔍 Filtra</button>
            <button class="btn-filter reset" onclick="resetFiltri()">✕ Reset</button>
        </div>
    </div>
    <div class="results-bar">
        <span id="results_label">Tutti i documenti</span>
        <span class="results-count" id="results_count">0 risultati</span>
    </div>
    <div class="doc-list" id="docList"></div>
    <div class="pagination" id="pagination"></div>
    <a href="/" class="btn-home">🏠 Torna alla Home</a>
</main>
<script>
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if (btn) btn.textContent = '🌙'; }}
        else               {{ root.classList.remove('light'); if (btn) btn.textContent = '☀️'; }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        applyTheme(next);
    }}
    applyTheme(localStorage.getItem('theme') || 'dark');
    const DOCS = {docs_js};
    const PER_PAGE = 15;
    let filtered = [...DOCS];
    let currentPage = 1;
    function applicaFiltri() {{
        const desc  = document.getElementById('f_desc').value.toLowerCase().trim();
        const cat   = document.getElementById('f_cat').value;
        const daDt  = document.getElementById('f_data_da').value || null;
        const aDt   = document.getElementById('f_data_a').value  || null;
        const impDa = document.getElementById('f_imp_da').value !== '' ? parseFloat(document.getElementById('f_imp_da').value) : null;
        const impA  = document.getElementById('f_imp_a').value  !== '' ? parseFloat(document.getElementById('f_imp_a').value)  : null;
        filtered = DOCS.filter(d => {{
            if (desc && !d.desc.toLowerCase().includes(desc) && !d.cat.toLowerCase().includes(desc) && !d.data.includes(desc)) return false;
            if (cat  && d.cat !== cat) return false;
            if (daDt && d.data_iso < daDt) return false;
            if (aDt  && d.data_iso > aDt)  return false;
            if (impDa !== null && d.imp < impDa) return false;
            if (impA  !== null && d.imp > impA)  return false;
            return true;
        }});
        currentPage = 1;
        renderPage();
    }}
    function resetFiltri() {{
        ['f_desc','f_cat','f_data_da','f_data_a','f_imp_da','f_imp_a'].forEach(id => {{
            document.getElementById(id).value = '';
        }});
        filtered = [...DOCS];
        currentPage = 1;
        renderPage();
    }}
    function esc(s) {{
        return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }}
    function renderPage() {{
        const list  = document.getElementById('docList');
        const count = document.getElementById('results_count');
        const label = document.getElementById('results_label');
        const total = filtered.length;
        count.textContent = total + ' risultat' + (total === 1 ? 'o' : 'i');
        label.textContent = total === DOCS.length ? 'Tutti i documenti' : 'Risultati filtrati';
        list.innerHTML = '';
        const start = (currentPage - 1) * PER_PAGE;
        const page  = filtered.slice(start, start + PER_PAGE);
        if (page.length === 0) {{
            list.innerHTML = "<div class='empty-msg'>Nessun documento trovato con i filtri selezionati.</div>";
        }} else {{
            page.forEach(d => {{
                const link = '/get_pdf?file=' + encodeURIComponent(d.nome);
                const el = document.createElement('div');
                el.className = 'doc-item';
                el.innerHTML =
                    '<div class="doc-main">' +
                        '<div class="doc-date">' + esc(d.data) + '</div>' +
                        '<a href="' + link + '" target="_blank" class="doc-cat">' + esc(d.cat) + '</a>' +
                        '<div class="doc-desc">' + esc(d.desc) + '</div>' +
                        '<div class="doc-meta">' +
                            '<span class="doc-importo">' + esc(d.imp_str) + '</span>' +
                            '<span class="doc-dim">' + esc(d.dim) + '</span>' +
                        '</div>' +
                    '</div>' +
                    '<a href="' + link + '" download="' + esc(d.nome) + '" class="doc-dl" title="Scarica">⬇️</a>';
                list.appendChild(el);
            }});
        }}
        renderPagination(total);
    }}
    function renderPagination(total) {{
        const pg = document.getElementById('pagination');
        pg.innerHTML = '';
        const pages = Math.ceil(total / PER_PAGE);
        if (pages <= 1) return;
        const btn = (label, page, active, disabled) => {{
            const b = document.createElement('button');
            b.className = 'pg-btn' + (active ? ' active' : '');
            b.textContent = label;
            if (disabled) b.setAttribute('disabled', '');
            else b.onclick = () => {{ currentPage = page; renderPage(); window.scrollTo(0,0); }};
            pg.appendChild(b);
        }};
        const ellipsis = () => {{
            const s = document.createElement('span');
            s.className = 'pg-ellipsis'; s.textContent = '…'; pg.appendChild(s);
        }};
        btn('◀', currentPage-1, false, currentPage===1);
        for (let i=1; i<=pages; i++) {{
            if (pages > 7 && i>2 && i<pages-1 && Math.abs(i-currentPage)>1) {{
                if (i===3 || i===pages-2) ellipsis();
                continue;
            }}
            btn(i, i, i===currentPage, false);
        }}
        btn('▶', currentPage+1, false, currentPage===pages);
    }}
    function toggleNavGroup(btn, ev) {{
        if (ev) ev.stopPropagation();
        const items = btn.nextElementSibling;
        const giaAperto = items.classList.contains('open');
        btn.closest('.nav-dropdown').querySelectorAll('.nav-group-items.open').forEach(function(el) {{
            el.classList.remove('open');
            el.previousElementSibling.querySelector('.nav-arrow').textContent = '▶';
        }});
        if (!giaAperto) {{
            items.classList.add('open');
            btn.querySelector('.nav-arrow').textContent = '▼';
        }}
    }}
    function toggleMenu() {{
        const m = document.getElementById("extraMenu");
        m.style.display = m.style.display === "block" ? "none" : "block";
    }}
    document.addEventListener("click", function(e) {{
        const menu = document.getElementById("extraMenu");
        const btn  = document.querySelector(".menu-btn");
        if (menu && menu.style.display === "block" && !menu.contains(e.target) && e.target !== btn)
            menu.style.display = "none";
    }});
    renderPage();
</script>
</body>
</html>"""

# Html Documenti Personali Web 
def documenti_personali_web(self):
    import __main__ as _app
    DOC_PERS_DIR = _app.DOC_PERS_DIR
    import datetime
    from datetime import datetime as dt
    import os
    oggi = datetime.date.today()
    anno_corrente = oggi.year
    def bytes_to_human(n):
        n = int(n) if n else 0
        if n < 1024: return f"{n} B"
        elif n < 1024**2: return f"{n/1024:.1f} KB"
        else: return f"{n/1024**2:.1f} MB"
    PROFILI_FILE = os.path.join(DOC_PERS_DIR, "profili.json")
    profili = []
    if os.path.exists(PROFILI_FILE):
        try:
            with open(PROFILI_FILE, "r", encoding="utf-8") as f:
                profili = json.load(f)
        except Exception:
            profili = []
    profili = sorted(profili)
    tutti = []
    categorie_set = set()
    for nome_profilo in profili:
        reg_path = os.path.join(DOC_PERS_DIR, nome_profilo, "registry.json")
        docs_dir = os.path.join(DOC_PERS_DIR, nome_profilo, "documenti")
        dati = {}
        if os.path.exists(reg_path):
            try:
                with open(reg_path, "r", encoding="utf-8") as f:
                    dati = json.load(f)
            except Exception:
                dati = {}
        for fname, d in dati.items():
            fpath = os.path.join(docs_dir, fname)
            if not os.path.exists(fpath):
                continue
            try:
                data_obj = dt.strptime(d.get("data_raw", ""), "%d%m%Y").date()
            except Exception:
                data_obj = oggi
            cat = d.get("categoria", "Altro")
            categorie_set.add(cat)
            tutti.append({
                "nome_file":   fname,
                "data_obj":    data_obj,
                "data_str":    data_obj.strftime("%d/%m/%Y"),
                "data_iso":    data_obj.isoformat(),
                "descrizione": d.get("descrizione", ""),
                "note":        d.get("note", ""),
                "categoria":   cat,
                "dimensione":  bytes_to_human(os.path.getsize(fpath)),
                "profilo":     nome_profilo,
            })
    tutti.sort(key=lambda x: x["data_obj"], reverse=True)
    docs_js = json.dumps([{
        "nome":     a["nome_file"],
        "data":     a["data_str"],
        "data_iso": a["data_iso"],
        "desc":     a["descrizione"],
        "note":     a["note"],
        "cat":      a["categoria"],
        "dim":      a["dimensione"],
        "profilo":  a["profilo"],
    } for a in tutti])
    categorie_options = "".join(
        f"<option value='{c}'>{c}</option>"
        for c in sorted(categorie_set)
    )
    profili_options = "".join(
        f"<option value='{p}'>{p}</option>"
        for p in profili
    )
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>📄 Documenti Personali</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
    (function() {{
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    }})();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg:#050505; --surface:#0f0f0f; --surface2:#161616; --surface3:#1e1e1e;
        --border:rgba(255,255,255,0.07); --border-active:rgba(99,160,240,0.5);
        --gold:#c9a84c; --blue:#63a0f0; --green:#4caf82; --red:#e05a5a;
        --text:#e8e8e8; --text-dim:#555; --text-mid:#888; --radius-lg:18px;
    }}
    :root.light {{
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --border-active:rgba(61,127,212,0.5);
        --gold:#b8902a; --blue:#3d7fd4; --green:#3a9068; --red:#cc3333;
        --text:#1a1a1a; --text-dim:#999; --text-mid:#555;
    }}
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{
        font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text);
        min-height:100vh; padding-bottom:50px; transition:background 0.3s,color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 40% at 50% -10%, rgba(99,160,240,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 60%);
    }}
    header {{
        padding:14px 16px 12px; display:flex; align-items:center; justify-content:center;
        border-bottom:1px solid var(--border); background:rgba(5,5,5,0.95);
        backdrop-filter:blur(20px); position:sticky; top:0; z-index:100;
    }}
    :root.light header {{ background:rgba(245,245,240,0.95); }}
    .menu-btn {{
        position:absolute; left:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border); color:var(--gold);
        width:36px; height:36px; border-radius:10px; font-size:1em;
        cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.2s;
    }}
    .menu-btn:hover {{ border-color:var(--gold); box-shadow:0 0 12px rgba(201,168,76,0.2); }}
    .header-title {{ font-family:'DM Sans',sans-serif; font-size:1em; font-weight:700; color:var(--text); }}
    .theme-toggle {{
        position:absolute; right:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border);
        border-radius:8px; width:34px; height:34px;
        display:flex; align-items:center; justify-content:center;
        cursor:pointer; font-size:1em; transition:all 0.2s;
    }}
    .theme-toggle:hover {{ border-color:var(--gold); }}
    .nav-dropdown {{
        position:absolute; top:calc(100% + 6px); left:10px;
        background:var(--surface2); border:1px solid var(--border);
        border-radius:var(--radius-lg); display:none; z-index:1000;
        width:270px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.7);
    }}
    .nav-dropdown a {{
        display:flex; align-items:center; gap:10px; padding:10px 16px;
        text-decoration:none; color:var(--text-mid); border-bottom:1px solid var(--border);
        font-size:0.87em; transition:all 0.15s;
    }}
    .nav-dropdown a:last-child {{ border-bottom:none; }}
    .nav-dropdown a:hover {{ background:var(--surface3); color:var(--text); padding-left:22px; }}
    .nav-group-btn {{ display:flex; justify-content:space-between; align-items:center; width:100%;
        padding:8px 16px; background:none; border:none; font-family:inherit; color:var(--gold);
        font-size:0.7em; font-weight:700; letter-spacing:1px; text-transform:uppercase; cursor:pointer; opacity:0.85; }}
    .nav-group-btn:hover {{ opacity:1; background:var(--surface3); }}
    .nav-arrow {{ font-size:0.85em; transition:transform 0.15s; }}
    .nav-group-items {{ display:none; flex-direction:column; }}
    .nav-group-items.open {{ display:flex; }}
    main {{ padding:14px; max-width:680px; margin:0 auto; animation:fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .filter-card {{
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); padding:14px 16px 16px;
        margin-bottom:10px; position:relative; overflow:hidden; margin-top:14px;
    }}
    .filter-card::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .filter-row {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:8px; }}
    .filter-row-3 {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-bottom:8px; }}
    @media (max-width:520px) {{
        .filter-row, .filter-row-3 {{ grid-template-columns:1fr; }}
    }}
    .filter-group label {{
        display:block; font-size:0.6em; font-weight:700; color:var(--text-dim);
        letter-spacing:1.5px; text-transform:uppercase; margin-bottom:5px;
    }}
    input[type="text"], input[type="date"], select {{
        width:100%; padding:9px 12px;
        background:var(--surface2); border:1px solid var(--border);
        border-radius:8px; color:var(--text);
        font-family:'DM Sans',sans-serif; font-size:0.88em;
        outline:none; transition:all 0.2s;
        -webkit-appearance:none; appearance:none;
    }}
    input:focus, select:focus {{ border-color:var(--border-active); background:var(--surface3); }}
    input::placeholder {{ color:var(--text-dim); }}
    select {{
        background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='7' viewBox='0 0 12 7'%3E%3Cpath fill='none' stroke='%23555' stroke-width='1.5' d='M1 1l5 5 5-5'/%3E%3C/svg%3E");
        background-repeat:no-repeat; background-position:right 10px center;
        padding-right:28px; cursor:pointer;
    }}
    select option {{ background:var(--surface2); color:var(--text); }}
    .filter-actions {{ display:flex; gap:8px; margin-top:6px; }}
    .btn-filter {{
        flex:1; padding:10px; border:none; border-radius:8px;
        font-family:'DM Sans',sans-serif; font-size:0.88em; font-weight:700;
        line-height:1.5; cursor:pointer; transition:all 0.2s;
    }}
    .btn-filter.apply {{ background:linear-gradient(135deg, var(--gold), #8a6820); color:#000; }}
    .btn-filter.apply:hover {{ transform:translateY(-1px); box-shadow:0 4px 16px rgba(201,168,76,0.25); }}
    .btn-filter.reset {{ background:var(--surface2); border:1px solid var(--border); color:var(--text-mid); }}
    .btn-filter.reset:hover {{ border-color:var(--border-active); color:var(--text); }}
    .results-bar {{
        display:flex; justify-content:space-between; align-items:center;
        margin-bottom:8px; font-size:0.75em; color:var(--text-dim);
    }}
    .results-count {{ color:var(--blue); font-weight:700; font-size:1.1em; }}
    .doc-list {{
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); overflow:hidden;
        position:relative; margin-bottom:10px; min-height:60px;
    }}
    .doc-list::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .doc-item {{
        display:flex; align-items:flex-start; justify-content:space-between;
        padding:14px 16px; border-bottom:1px solid var(--border); gap:12px; transition:background 0.15s;
    }}
    .doc-item:last-child {{ border-bottom:none; }}
    .doc-item:hover {{ background:var(--surface2); }}
    .doc-main {{ flex:1; min-width:0; }}
    .doc-header {{
        display:flex; align-items:center; gap:10px; margin-bottom:6px;
        flex-wrap:wrap; row-gap:4px;
    }}
    .doc-date {{ font-size:0.82em; color:var(--text-mid); white-space:nowrap; }}
    .doc-profilo {{
        font-size:0.75em; font-weight:700; color:var(--gold);
        text-transform:uppercase; letter-spacing:0.8px; white-space:nowrap;
    }}
    .doc-dim {{ font-size:0.75em; color:var(--text-dim); white-space:nowrap; }}
    .doc-cat {{
        font-size:1em; font-weight:700; color:var(--blue);
        text-decoration:none; display:block; margin-bottom:6px; transition:color 0.15s;
    }}
    .doc-cat:hover {{ color:var(--gold); }}
    .doc-desc {{ font-size:0.88em; color:var(--text-mid); margin-bottom:4px; word-break:break-word; line-height:1.4; }}
    .doc-note {{ font-size:0.82em; color:var(--text-dim); font-style:italic; word-break:break-word; line-height:1.4; margin-bottom:2px; }}
    .doc-dl {{ font-size:1.5em; text-decoration:none; opacity:0.6; transition:opacity 0.15s; flex-shrink:0; padding-top:2px; }}
    .doc-dl:hover {{ opacity:1; }}
    .doc-dl {{ font-size:1.2em; text-decoration:none; opacity:0.5; transition:opacity 0.15s; flex-shrink:0; }}
    .doc-dl:hover {{ opacity:1; }}
    .empty-msg {{ text-align:center; padding:30px; color:var(--text-dim); font-size:0.85em; font-style:italic; }}
    .pagination {{ display:flex; justify-content:center; gap:6px; margin-bottom:10px; flex-wrap:wrap; }}
    .pg-btn {{
        padding:7px 13px; border:1px solid var(--border); border-radius:8px;
        background:var(--surface); color:var(--text-mid);
        font-family:'DM Sans',sans-serif; font-size:0.8em; font-weight:700;
        cursor:pointer; transition:all 0.15s; line-height:1.5;
    }}
    .pg-btn:hover {{ border-color:var(--border-active); color:var(--text); }}
    .pg-btn.active {{ background:var(--gold); color:#000; border-color:var(--gold); }}
    .pg-btn[disabled] {{ opacity:0.3; cursor:default; pointer-events:none; }}
    .pg-ellipsis {{ padding:7px 4px; color:var(--text-dim); font-size:0.8em; }}
    .btn-home {{
        display:block; text-align:center; padding:13px;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; border-radius:10px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.9em;
        line-height:1.5; transition:all 0.2s;
    }}
    .btn-home:hover {{ transform:translateY(-1px); box-shadow:0 6px 20px rgba(201,168,76,0.25); }}
</style>
</head>
<body>
<header>
    <button class="menu-btn" onclick="toggleMenu()">⚙️</button>
    <div id="extraMenu" class="nav-dropdown">
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Finanze</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/">🏠 Aggiungi Operazione</a>
                <a href="/lista">📈 Gestione Movimenti Mese</a>
                <a href="/stats">📊 Bilancio Mese</a>
                <a href="/fondo_risparmio_web">💰 Fondo Risparmio</a>
                <a href="/scadenze_web">📅 Scadenze del Mese</a>
                <a href="/fairshare_web">⚖️ FairShare</a>
                <a href="/menu_esplora">🔍 Esplora</a>
                <a href="/grafici_web">📅 Grafici e Statistiche</a>
                <a href="/gestione_categorie">⚙️ Gestione Categorie</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Casa</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/utenze?anno={anno_corrente}">💧 Utenze</a>
                <a href="/consultazione_supermercati">🛒 Gestione Supermercati</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Documenti</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/documenti_pdf_web">🗄️ Documenti Contabili</a>
                <a href="/documenti_personali_web">📄 Documenti Personali</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Sistema</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/info_sys_web">📡 Monitor Server</a>
                <a href="/cambia_pw_web">🔑 Cambia Password</a>
                <a href="/webauthn_web">👆 Biometrico</a>
                <a href="/cambia_profilo_web">👤 Cambia Profilo</a>
                <a href="/logoff">🔓 Logout</a>
            </div>
        </div>
    </div>
    <div class="header-title">📄 Documenti Personali</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="filter-card">
        <div class="filter-row">
            <div class="filter-group">
                <label>Descrizione / Note</label>
                <input type="text" id="f_desc" placeholder="cerca...">
            </div>
            <div class="filter-group">
                <label>Profilo</label>
                <select id="f_profilo">
                    <option value="">-- Tutti --</option>
                    {profili_options}
                </select>
            </div>
        </div>
        <div class="filter-row-3">
            <div class="filter-group">
                <label>Categoria</label>
                <select id="f_cat">
                    <option value="">-- Tutte --</option>
                    {categorie_options}
                </select>
            </div>
            <div class="filter-group">
                <label>Data da</label>
                <input type="date" id="f_data_da">
            </div>
            <div class="filter-group">
                <label>Data a</label>
                <input type="date" id="f_data_a">
            </div>
        </div>
        <div class="filter-actions">
            <button class="btn-filter apply" onclick="applicaFiltri()">🔍 Filtra</button>
            <button class="btn-filter reset"  onclick="resetFiltri()">✕ Reset</button>
        </div>
    </div>
    <div class="results-bar">
        <span id="results_label">Tutti i documenti</span>
        <span class="results-count" id="results_count">0 risultati</span>
    </div>
    <div class="doc-list" id="docList"></div>
    <div class="pagination" id="pagination"></div>
    <a href="/" class="btn-home">🏠 Torna alla Home</a>
</main>
<script>
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if (btn) btn.textContent = '🌙'; }}
        else               {{ root.classList.remove('light'); if (btn) btn.textContent = '☀️'; }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        applyTheme(next);
    }}
    document.addEventListener("DOMContentLoaded", function() {{
        applyTheme(localStorage.getItem('theme') || 'dark');
    }});
    const DOCS = {docs_js};
    const PER_PAGE = 15;
    let filtered = [...DOCS];
    let currentPage = 1;
    function applicaFiltri() {{
        const desc    = document.getElementById('f_desc').value.toLowerCase().trim();
        const cat     = document.getElementById('f_cat').value;
        const profilo = document.getElementById('f_profilo').value;
        const daDt    = document.getElementById('f_data_da').value || null;
        const aDt     = document.getElementById('f_data_a').value  || null;
        filtered = DOCS.filter(d => {{
            if (desc    && !d.desc.toLowerCase().includes(desc) &&
                           !d.note.toLowerCase().includes(desc) &&
                           !d.cat.toLowerCase().includes(desc))  return false;
            if (cat     && d.cat     !== cat)     return false;
            if (profilo && d.profilo !== profilo) return false;
            if (daDt    && d.data_iso < daDt)     return false;
            if (aDt     && d.data_iso > aDt)      return false;
            return true;
        }});
        currentPage = 1;
        renderPage();
    }}
    function resetFiltri() {{
        ['f_desc','f_cat','f_profilo','f_data_da','f_data_a'].forEach(id => {{
            document.getElementById(id).value = '';
        }});
        filtered = [...DOCS];
        currentPage = 1;
        renderPage();
    }}
    function esc(s) {{
        return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }}
    function renderPage() {{
        const list  = document.getElementById('docList');
        const count = document.getElementById('results_count');
        const label = document.getElementById('results_label');
        const total = filtered.length;
        count.textContent = total + ' risultat' + (total === 1 ? 'o' : 'i');
        label.textContent = total === DOCS.length ? 'Tutti i documenti' : 'Risultati filtrati';
        list.innerHTML = '';
        const start = (currentPage - 1) * PER_PAGE;
        const page  = filtered.slice(start, start + PER_PAGE);
        if (page.length === 0) {{
            list.innerHTML = "<div class='empty-msg'>Nessun documento trovato.</div>";
        }} else {{
            page.forEach(d => {{
                const link = '/get_pdf_pers?profilo=' + encodeURIComponent(d.profilo) + '&file=' + encodeURIComponent(d.nome);
                const el = document.createElement('div');
                el.className = 'doc-item';
                el.innerHTML =
                    '<div class="doc-main">' +
                        '<div class="doc-header">' +
                            '<span class="doc-date">📅 ' + esc(d.data) + '</span>' +
                            '<span class="doc-profilo">👤 ' + esc(d.profilo) + '</span>' +
                            '<span class="doc-dim">' + esc(d.dim) + '</span>' +
                        '</div>' +
                        '<a href="' + link + '" target="_blank" class="doc-cat">' + esc(d.cat) + '</a>' +
                        (d.desc ? '<div class="doc-desc">' + esc(d.desc) + '</div>' : '') +
                        (d.note ? '<div class="doc-note">📝 ' + esc(d.note) + '</div>' : '') +
                    '</div>' +
                    '<a href="' + link + '" download="' + esc(d.nome) + '" class="doc-dl" title="Scarica">⬇️</a>';
                list.appendChild(el);
            }});
        }}
        renderPagination(total);
    }}
    function renderPagination(total) {{
        const pg = document.getElementById('pagination');
        pg.innerHTML = '';
        const pages = Math.ceil(total / PER_PAGE);
        if (pages <= 1) return;
        const btn = (label, page, active, disabled) => {{
            const b = document.createElement('button');
            b.className = 'pg-btn' + (active ? ' active' : '');
            b.textContent = label;
            if (disabled) b.setAttribute('disabled', '');
            else b.onclick = () => {{ currentPage = page; renderPage(); window.scrollTo(0,0); }};
            pg.appendChild(b);
        }};
        const ellipsis = () => {{
            const s = document.createElement('span');
            s.className = 'pg-ellipsis'; s.textContent = '…'; pg.appendChild(s);
        }};
        btn('◀', currentPage-1, false, currentPage===1);
        for (let i=1; i<=pages; i++) {{
            if (pages > 7 && i>2 && i<pages-1 && Math.abs(i-currentPage)>1) {{
                if (i===3 || i===pages-2) ellipsis();
                continue;
            }}
            btn(i, i, i===currentPage, false);
        }}
        btn('▶', currentPage+1, false, currentPage===pages);
    }}
    function toggleNavGroup(btn, ev) {{
        if (ev) ev.stopPropagation();
        const items = btn.nextElementSibling;
        const giaAperto = items.classList.contains('open');
        btn.closest('.nav-dropdown').querySelectorAll('.nav-group-items.open').forEach(function(el) {{
            el.classList.remove('open');
            el.previousElementSibling.querySelector('.nav-arrow').textContent = '▶';
        }});
        if (!giaAperto) {{
            items.classList.add('open');
            btn.querySelector('.nav-arrow').textContent = '▼';
        }}
    }}
    function toggleMenu() {{
        const m = document.getElementById("extraMenu");
        m.style.display = m.style.display === "block" ? "none" : "block";
    }}
    document.addEventListener("click", function(e) {{
        const menu = document.getElementById("extraMenu");
        const btn  = document.querySelector(".menu-btn");
        if (menu && menu.style.display === "block" && !menu.contains(e.target) && e.target !== btn)
            menu.style.display = "none";
    }});
    renderPage();
</script>
</body>
</html>"""


# Html Visualizza Utenze Web
def genera_html_utenze(self, percorso_db, anno):
    import __main__ as _app
    UTENZE_DB = _app.UTENZE_DB
    from datetime import datetime
    utenze = ["Acqua", "Luce", "Gas"]
    if not os.path.exists(percorso_db):
        return """<!DOCTYPE html>
<html><head><title>Errore DB</title><meta charset="utf-8">
<style>body{{font-family:'DM Sans',sans-serif;background:#050505;color:#e8e8e8;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px;}}.box{{background:#0f0f0f;border:1px solid rgba(255,255,255,0.07);border-radius:18px;padding:30px;max-width:400px;text-align:center;}}.t{{color:#e05a5a;font-size:1.2em;font-weight:800;margin-bottom:10px;}}.s{{color:#555;font-size:0.9em;margin-bottom:20px;}}.btn{{display:inline-block;padding:12px 24px;background:linear-gradient(135deg,#c9a84c,#8a6820);color:#000;border-radius:10px;text-decoration:none;font-weight:700;}}</style>
</head><body><div class="box"><div class="t">❌ Errore Database</div><div class="s">Il file UTENZE_DB non esiste o è vuoto.</div><a href="/" class="btn">🏠 Torna alla Home</a></div></body></html>"""
    try:
        with open(percorso_db, "r", encoding="utf-8") as f:
            contenuto = f.read().strip()
            if not contenuto:
                return "<p style='color:#e05a5a;padding:20px;'>⚠️ Il file database è vuoto.</p>"
            data = json.loads(contenuto)
    except Exception as e:
        return f"<p style='color:#e05a5a;padding:20px;'>❌ Errore nel file JSON: {e}</p>"
    letture = data.get("letture_salvate", {})
    anno_corrente = datetime.now().year
    anni_disponibili = [str(anno_corrente - i) for i in range(6)]
    select_html = "<div class='anno-select'><label>🗓️ Anno</label><select onchange=\"location.href='/utenze?anno=' + this.value\">"
    for a in anni_disponibili:
        selected = " selected" if a == str(anno) else ""
        select_html += f"<option value='{a}'{selected}>{a}</option>"
    select_html += "</select></div>"
    MESI_NOMI = ["Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno",
                  "Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"]
    utenze_html = ""
    for utenza in utenze:
        righe_db = letture.get(utenza, {}).get(str(anno), [])
        mese_map = {}
        for r in righe_db:
            try:
                mese_num = int(r[0].split("/")[0])
                mese_map[mese_num] = [float(r[1]), float(r[2]), float(r[3])]
            except Exception:
                pass
        uid = f"utenza_{utenza.lower()}"
        icone = {"Acqua": "💧", "Luce": "⚡", "Gas": "🔥"}
        ico = icone.get(utenza, "📊")
        rows_html = ""
        total = 0.0
        consumi = []
        for i, mese in enumerate(MESI_NOMI):
            vals = mese_map.get(i + 1, [0.0, 0.0, 0.0])
            prec, att, cons = vals[0], vals[1], vals[2]
            total += cons
            consumi.append(cons)
            _onchg = "calcCons(this.closest('tr'))"
            rows_html += (
                "<tr>"
                f"<td class='td-mese'>{mese}</td>"
                f"<td><input class='u-inp' type='number' step='0.1' min='0' name='prec_{i}' value='{prec:.1f}' onchange='{_onchg}'></td>"
                f"<td><input class='u-inp' type='number' step='0.1' min='0' name='att_{i}' value='{att:.1f}' onchange='{_onchg}'></td>"
                f"<td class='cons' id='cons_{utenza.lower()}_{i}'>{cons:.1f}</td>"
                "</tr>"
            )
        teardown_html = ""
        if any(c > 0 for c in consumi):
            media = total / len([c for c in consumi if c > 0]) if consumi else 0
            variazioni = [consumi[i] - consumi[i-1] for i in range(1, len(consumi)) if consumi[i-1] > 0 or consumi[i] > 0]
            ultima = variazioni[-1] if variazioni else 0
            ultima_color = "var(--green)" if ultima <= 0 else "var(--red)"
            teardown_html = f"""
            <div class='teardown'>
                <div class='td-item'><span>Totale</span><b>{total:.1f}</b></div>
                <div class='td-item'><span>Media mensile</span><b>{media:.1f}</b></div>
                <div class='td-item'><span>Ultima variazione</span><b style='color:{ultima_color}'>{ultima:+.1f}</b></div>
                <div class='td-item'><span>Mesi con dati</span><b>{len([c for c in consumi if c > 0])}</b></div>
            </div>"""
        utenze_html += f"""
        <div class='u-block'>
            <button class='u-toggle' onclick="toggleU('{uid}', this)" type='button'>
                <span>{ico} {utenza}</span>
                <span class='u-arrow'>▶</span>
            </button>
            <div class='u-content' id='{uid}' style='display:none;'>
                <form method='post' action='/salva_utenza_web'>
                    <input type='hidden' name='utenza' value='{utenza}'>
                    <input type='hidden' name='anno' value='{anno}'>
                    <table>
                        <thead><tr><th>Mese</th><th>Prec.</th><th>Att.</th><th>Consumo</th></tr></thead>
                        <tbody>{rows_html}</tbody>
                    </table>
                    {teardown_html}
                    <div class='form-save-row'>
                        <button type='submit' class='btn-salva-utenza'>💾 Salva {utenza}</button>
                    </div>
                </form>
            </div>
        </div>"""
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>💧 Utenze — {anno}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
    (function() {{
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    }})();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg:#050505; --surface:#0f0f0f; --surface2:#161616; --surface3:#1e1e1e;
        --border:rgba(255,255,255,0.07); --gold:#c9a84c; --blue:#63a0f0;
        --green:#4caf82; --red:#e05a5a; --text:#e8e8e8; --text-dim:#555; --text-mid:#888;
        --radius-lg:18px;
    }}
    :root.light {{
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --gold:#b8902a; --blue:#3d7fd4;
        --green:#3a9068; --red:#cc3333; --text:#1a1a1a; --text-dim:#999; --text-mid:#555;
    }}
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{
        font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text);
        min-height:100vh; padding-bottom:50px; transition:background 0.3s,color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 40% at 50% -10%, rgba(99,160,240,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 60%);
    }}
    header {{
        padding:14px 16px 12px; display:flex; align-items:center; justify-content:center;
        border-bottom:1px solid var(--border); background:rgba(5,5,5,0.95);
        backdrop-filter:blur(20px); position:sticky; top:0; z-index:100;
    }}
    :root.light header {{ background:rgba(245,245,240,0.95); }}
    .menu-btn {{
        position:absolute; left:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border); color:var(--gold);
        width:36px; height:36px; border-radius:10px; font-size:1em;
        cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.2s;
    }}
    .menu-btn:hover {{ border-color:var(--gold); box-shadow:0 0 12px rgba(201,168,76,0.2); }}
    .header-title {{ font-family:'DM Sans',sans-serif; font-size:1em; font-weight:700; color:var(--text); }}
    .theme-toggle {{
        position:absolute; right:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border);
        border-radius:8px; width:34px; height:34px;
        display:flex; align-items:center; justify-content:center;
        cursor:pointer; font-size:1em; transition:all 0.2s;
    }}
    .theme-toggle:hover {{ border-color:var(--gold); }}
    .nav-dropdown {{
        position:absolute; top:calc(100% + 6px); left:10px;
        background:var(--surface2); border:1px solid var(--border);
        border-radius:var(--radius-lg); display:none; z-index:1000;
        width:270px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.7);
    }}
    .nav-dropdown a {{
        display:flex; align-items:center; gap:10px; padding:10px 16px;
        text-decoration:none; color:var(--text-mid); border-bottom:1px solid var(--border);
        font-size:0.87em; transition:all 0.15s;
    }}
    .nav-dropdown a:last-child {{ border-bottom:none; }}
    .nav-dropdown a:hover {{ background:var(--surface3); color:var(--text); padding-left:22px; }}
    .nav-group-btn {{ display:flex; justify-content:space-between; align-items:center; width:100%;
        padding:8px 16px; background:none; border:none; font-family:inherit; color:var(--gold);
        font-size:0.7em; font-weight:700; letter-spacing:1px; text-transform:uppercase; cursor:pointer; opacity:0.85; }}
    .nav-group-btn:hover {{ opacity:1; background:var(--surface3); }}
    .nav-arrow {{ font-size:0.85em; transition:transform 0.15s; }}
    .nav-group-items {{ display:none; flex-direction:column; }}
    .nav-group-items.open {{ display:flex; }}
    main {{ padding:14px; max-width:580px; margin:0 auto; animation:fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .anno-select {{
        background:var(--surface); border:1px solid var(--border); border-radius:12px;
        padding:10px 14px; margin-bottom:12px; display:flex; align-items:center; gap:10px;
    }}
    .anno-select label {{ font-size:0.78em; color:var(--text-mid); }}
    .anno-select select {{
        background:var(--surface2); border:1px solid var(--border); border-radius:8px;
        color:var(--text); padding:6px 10px; font-family:'DM Sans',sans-serif;
        font-size:0.88em; outline:none; cursor:pointer;
    }}
    .u-block {{
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); margin-bottom:8px; overflow:hidden; position:relative;
    }}
    .u-block::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .u-toggle {{
        width:100%; background:none; border:none; padding:14px 18px;
        display:flex; justify-content:space-between; align-items:center;
        cursor:pointer; color:var(--text); font-family:'DM Sans',sans-serif;
        font-size:0.95em; font-weight:700; line-height:1.5; transition:background 0.15s;
    }}
    .u-toggle:hover {{ background:var(--surface2); }}
    .u-arrow {{ font-size:0.75em; color:var(--text-dim); transition:transform 0.2s; }}
    .u-content {{ border-top:1px solid var(--border); }}
    table {{ width:100%; border-collapse:collapse; }}
    thead tr {{ background:var(--surface2); }}
    th {{ padding:9px 12px; font-size:0.7em; font-weight:700; color:var(--text-dim); letter-spacing:1.5px; text-transform:uppercase; text-align:left; border-bottom:1px solid var(--border); }}
    td {{ padding:9px 12px; font-size:0.88em; border-bottom:1px solid var(--border); color:var(--text-mid); }}
    td.cons {{ font-weight:600; color:var(--text); }}
    tr:last-child td {{ border-bottom:none; }}
    .empty-row {{ text-align:center; color:var(--text-dim); font-style:italic; }}
    .teardown {{ display:grid; grid-template-columns:1fr 1fr; gap:6px; padding:12px; background:var(--surface2); border-top:1px solid var(--border); }}
    .td-item {{ background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:8px 10px; }}
    .td-item span {{ display:block; font-size:0.62em; color:var(--text-dim); letter-spacing:1.2px; text-transform:uppercase; margin-bottom:3px; }}
    .td-item b {{ font-size:0.9em; font-weight:700; color:var(--text); }}
    .btn-home {{
        display:block; text-align:center; padding:13px;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; border-radius:10px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.9em;
        line-height:1.5; margin-top:14px; transition:all 0.2s;
    }}
    .btn-home:hover {{ transform:translateY(-1px); box-shadow:0 6px 20px rgba(201,168,76,0.25); }}
    .u-inp {{
        background:var(--surface3); border:1px solid var(--border); color:var(--text);
        padding:5px 7px; border-radius:7px; font-family:'DM Sans',sans-serif;
        font-size:0.85em; width:90px; text-align:right;
    }}
    .u-inp:focus {{ outline:none; border-color:var(--gold); }}
    .u-inp::-webkit-outer-spin-button,
    .u-inp::-webkit-inner-spin-button {{ -webkit-appearance:none; margin:0; }}
    .u-inp[type=number] {{ -moz-appearance:textfield; }}
    .td-mese {{ font-weight:600; color:var(--text); min-width:80px; }}
    .form-save-row {{ padding:10px 12px; background:var(--surface2); border-top:1px solid var(--border); }}
    .btn-salva-utenza {{
        padding:9px 22px; border-radius:9px; border:none; cursor:pointer;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.88em;
        transition:all 0.2s;
    }}
    .btn-salva-utenza:hover {{ transform:translateY(-1px); box-shadow:0 4px 14px rgba(201,168,76,0.3); }}
</style>
</head>
<body>
<header>
    <button class="menu-btn" onclick="toggleMenu()">⚙️</button>
    <div id="extraMenu" class="nav-dropdown">
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Finanze</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/">🏠 Aggiungi Operazione</a>
                <a href="/lista">📈 Gestione Movimenti Mese</a>
                <a href="/stats">📊 Bilancio Mese</a>
                <a href="/fondo_risparmio_web">💰 Fondo Risparmio</a>
                <a href="/scadenze_web">📅 Scadenze del Mese</a>
                <a href="/fairshare_web">⚖️ FairShare</a>
                <a href="/menu_esplora">🔍 Esplora</a>
                <a href="/grafici_web">📅 Grafici e Statistiche</a>
                <a href="/gestione_categorie">⚙️ Gestione Categorie</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Casa</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/utenze?anno={anno_corrente}">💧 Utenze</a>
                <a href="/consultazione_supermercati">🛒 Gestione Supermercati</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Documenti</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/documenti_pdf_web">🗄️ Documenti Contabili</a>
                <a href="/documenti_personali_web">🗄️ Documenti Personali</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Sistema</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/info_sys_web">📡 Monitor Server</a>
                <a href="/cambia_pw_web">🔑 Cambia Password</a>
                <a href="/webauthn_web">👆 Biometrico</a>
                <a href="/cambia_profilo_web">👤 Cambia Profilo</a>
                <a href="/logoff">🔓 Logout</a>
            </div>
        </div>
    </div>
    <div class="header-title">💧 Utenze — {anno}</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    {select_html}
    {utenze_html}
    <a href="/" class="btn-home">🏠 Torna alla Home</a>
</main>
<script>
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if (btn) btn.textContent = '🌙'; }}
        else               {{ root.classList.remove('light'); if (btn) btn.textContent = '☀️'; }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        applyTheme(next);
    }}
    applyTheme(localStorage.getItem('theme') || 'dark');
    function toggleNavGroup(btn, ev) {{
        if (ev) ev.stopPropagation();
        const items = btn.nextElementSibling;
        const giaAperto = items.classList.contains('open');
        btn.closest('.nav-dropdown').querySelectorAll('.nav-group-items.open').forEach(function(el) {{
            el.classList.remove('open');
            el.previousElementSibling.querySelector('.nav-arrow').textContent = '▶';
        }});
        if (!giaAperto) {{
            items.classList.add('open');
            btn.querySelector('.nav-arrow').textContent = '▼';
        }}
    }}
    function toggleMenu() {{
        const m = document.getElementById("extraMenu");
        m.style.display = m.style.display === "block" ? "none" : "block";
    }}
    function toggleU(id, btn) {{
        const el = document.getElementById(id);
        const arrow = btn.querySelector(".u-arrow");
        const open = el.style.display === "block";
        el.style.display = open ? "none" : "block";
        arrow.textContent = open ? "▶" : "▼";
    }}
    function calcCons(row) {{
        const inputs = row.querySelectorAll("input[type='number']");
        if (inputs.length < 2) return;
        const prec = parseFloat(inputs[0].value) || 0;
        const att  = parseFloat(inputs[1].value) || 0;
        const cons = Math.max(0, att - prec).toFixed(1);
        const td = row.querySelector("td.cons");
        if (td) td.textContent = cons;
    }}
    document.addEventListener("click", function(e) {{
        const menu = document.getElementById("extraMenu");
        const btn = document.querySelector(".menu-btn");
        if (menu && menu.style.display === "block" && !menu.contains(e.target) && e.target !== btn)
            menu.style.display = "none";
    }});
</script>
</body>
</html>"""

# Lista Spesa Supermarket e Prezzi Promo
def genera_html_consultazione(self, file_selezionato=None):
    import __main__ as _app
    EXPORT_FILES = _app.EXPORT_FILES
    SUPERMERCATI_DB = _app.SUPERMERCATI_DB
    import datetime
    anno_corrente = datetime.datetime.now().year
    def inizializza_db_file(percorso_db, contenuto_iniziale="{}"):
        dir_path = os.path.dirname(percorso_db)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        if not os.path.exists(percorso_db):
            try:
                with open(percorso_db, "w", encoding="utf-8") as f:
                    f.write(contenuto_iniziale)
                return True
            except Exception as e:
                print(f"Errore nella creazione automatica di {percorso_db}: {e}")
                return False
        return True
    def get_file_list_internal():
        directory_esportazione = EXPORT_FILES
        if not os.path.isdir(directory_esportazione):
            try: os.makedirs(directory_esportazione)
            except: pass
            return []
        list_files = os.listdir(directory_esportazione)
        lista_spesa_files = [f for f in list_files if f.startswith("Lista_Spesa_") and f.endswith(".txt")]
        try:
            lista_spesa_files.sort(key=lambda f: os.path.getmtime(os.path.join(directory_esportazione, f)), reverse=True)
        except: pass
        return lista_spesa_files
    def leggi_lista_spesa_internal(nome_file):
        file_path = os.path.join(EXPORT_FILES, nome_file)
        if not os.path.exists(file_path): return []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"Errore lettura file {nome_file}: {e}")
            return []
        return [{"raw_content": content}]
    lista_file_disponibili = get_file_list_internal()
    file_visualizzato = lista_file_disponibili[0] if lista_file_disponibili else "Nessuna Lista Trovata"
    ultima_spesa_data = []
    if file_visualizzato != "Nessuna Lista Trovata":
        ultima_spesa_data = leggi_lista_spesa_internal(file_visualizzato)
    is_raw_content = ultima_spesa_data and 'raw_content' in ultima_spesa_data[0]
    percorso_db = SUPERMERCATI_DB
    dati_supermercati = {}
    if not inizializza_db_file(percorso_db):
        return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Errore</title><style>body{{font-family:'DM Sans',sans-serif;background:#050505;color:#e8e8e8;padding:30px;}}.e{{color:#e05a5a;}}</style></head><body><p class="e">❌ Impossibile creare il file {percorso_db}.</p><a href="/" style="color:#c9a84c;">🏠 Home</a></body></html>"""
    try:
        with open(percorso_db, "r", encoding="utf-8") as f:
            contenuto = f.read().strip()
            dati_supermercati = json.loads(contenuto) if contenuto else {}
    except Exception as e:
        return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Errore JSON</title><style>body{{font-family:'DM Sans',sans-serif;background:#050505;color:#e8e8e8;padding:30px;}}</style></head><body><p style="color:#e05a5a;">❌ Errore lettura database: {e}</p><a href="/" style="color:#c9a84c;">🏠 Home</a></body></html>"""
    supermercati = sorted(dati_supermercati.keys())
    if is_raw_content:
        raw_text = ultima_spesa_data[0]['raw_content']
        raw_safe = raw_text.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        lista_inner = f"<pre class='lista-pre'>{raw_safe}</pre>"
    else:
        lista_inner = "<p class='empty-msg'>❌ Nessun file lista spesa trovato nella cartella export.</p>"
    cataloghi_html = ""
    if supermercati:
        for superm in supermercati:
            articoli = dati_supermercati.get(superm, [])
            sid = f"cat_{superm.lower().replace(' ','_')}"
            rows = ""
            if articoli:
                for art in sorted(articoli, key=lambda x: x.get('nome','')):
                    nome = art.get("nome","N/D")
                    desc = art.get("descrizione","N/D")
                    cat  = art.get("categoria","Varie")
                    try: pn = f"{_fmt_it(float(art.get('prezzo','0')))}"
                    except: pn = art.get("prezzo","N/D")
                    promo_attiva = art.get("promo", False)
                    try: pp = float(art.get("prezzo_promo","0"))
                    except: pp = 0
                    promo_cell = f"<span class='promo'>€ {_fmt_it(pp)}</span>" if promo_attiva and pp > 0 else "—"
                    rows += f"<tr><td>{nome}</td><td class='td-desc'>{desc}</td><td>{cat}</td><td class='td-price'>€ {pn}</td><td class='td-price'>{promo_cell}</td></tr>"
                table = f"<table><thead><tr><th>Articolo</th><th>Descrizione</th><th>Categoria</th><th>Prezzo</th><th>Promo</th></tr></thead><tbody>{rows}</tbody></table>"
            else:
                table = "<p class='empty-msg'>Nessun articolo registrato.</p>"
            cataloghi_html += f"""
            <div class='u-block' style='margin-bottom:6px;'>
                <button class='u-toggle' onclick="toggleU('{sid}', this)">
                    <span>🛒 {superm} <small>({len(articoli)} articoli)</small></span>
                    <span class='u-arrow'>▶</span>
                </button>
                <div class='u-content' id='{sid}' style='display:none;overflow-x:auto;'>{table}</div>
            </div>"""
    else:
        cataloghi_html = "<p class='empty-msg'>⚠️ Nessun supermercato nel database.</p>"
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>🛒 Gestione Supermercati</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
    (function() {{
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    }})();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg:#050505; --surface:#0f0f0f; --surface2:#161616; --surface3:#1e1e1e;
        --border:rgba(255,255,255,0.07); --gold:#c9a84c; --blue:#63a0f0;
        --green:#4caf82; --red:#e05a5a; --text:#e8e8e8; --text-dim:#555; --text-mid:#888;
        --radius-lg:18px;
    }}
    :root.light {{
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --gold:#b8902a; --blue:#3d7fd4;
        --green:#3a9068; --red:#cc3333; --text:#1a1a1a; --text-dim:#999; --text-mid:#555;
    }}
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{
        font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text);
        min-height:100vh; padding-bottom:50px; transition:background 0.3s,color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 40% at 50% -10%, rgba(99,160,240,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 60%);
    }}
    header {{
        padding:14px 16px 12px; display:flex; align-items:center; justify-content:center;
        border-bottom:1px solid var(--border); background:rgba(5,5,5,0.95);
        backdrop-filter:blur(20px); position:sticky; top:0; z-index:100;
    }}
    :root.light header {{ background:rgba(245,245,240,0.95); }}
    .menu-btn {{
        position:absolute; left:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border); color:var(--gold);
        width:36px; height:36px; border-radius:10px; font-size:1em;
        cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.2s;
    }}
    .menu-btn:hover {{ border-color:var(--gold); }}
    .header-title {{ font-family:'DM Sans',sans-serif; font-size:1em; font-weight:700; color:var(--text); }}
    .theme-toggle {{
        position:absolute; right:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border);
        border-radius:8px; width:34px; height:34px;
        display:flex; align-items:center; justify-content:center;
        cursor:pointer; font-size:1em; transition:all 0.2s;
    }}
    .theme-toggle:hover {{ border-color:var(--gold); }}
    .nav-dropdown {{
        position:absolute; top:calc(100% + 6px); left:10px;
        background:var(--surface2); border:1px solid var(--border);
        border-radius:var(--radius-lg); display:none; z-index:1000;
        width:270px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.7);
    }}
    .nav-dropdown a {{
        display:flex; align-items:center; gap:10px; padding:10px 16px;
        text-decoration:none; color:var(--text-mid); border-bottom:1px solid var(--border);
        font-size:0.87em; transition:all 0.15s;
    }}
    .nav-dropdown a:last-child {{ border-bottom:none; }}
    .nav-dropdown a:hover {{ background:var(--surface3); color:var(--text); padding-left:22px; }}
    .nav-group-btn {{ display:flex; justify-content:space-between; align-items:center; width:100%;
        padding:8px 16px; background:none; border:none; font-family:inherit; color:var(--gold);
        font-size:0.7em; font-weight:700; letter-spacing:1px; text-transform:uppercase; cursor:pointer; opacity:0.85; }}
    .nav-group-btn:hover {{ opacity:1; background:var(--surface3); }}
    .nav-arrow {{ font-size:0.85em; transition:transform 0.15s; }}
    .nav-group-items {{ display:none; flex-direction:column; }}
    .nav-group-items.open {{ display:flex; }}
    main {{ padding:14px; max-width:680px; margin:0 auto; animation:fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .section-card {{
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); margin-bottom:10px; overflow:hidden; position:relative;
    }}
    .section-card::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .section-toggle {{
        width:100%; background:none; border:none; padding:14px 18px;
        display:flex; justify-content:space-between; align-items:center;
        cursor:pointer; color:var(--text); font-family:'DM Sans',sans-serif;
        font-size:0.92em; font-weight:700; line-height:1.5; transition:background 0.15s;
    }}
    .section-toggle:hover {{ background:var(--surface2); }}
    .u-block {{
        background:var(--surface2); border:1px solid var(--border);
        border-radius:12px; overflow:hidden; position:relative;
    }}
    .u-toggle {{
        width:100%; background:none; border:none; padding:12px 16px;
        display:flex; justify-content:space-between; align-items:center;
        cursor:pointer; color:var(--text); font-family:'DM Sans',sans-serif;
        font-size:0.88em; font-weight:700; line-height:1.5; transition:background 0.15s;
    }}
    .u-toggle:hover {{ background:var(--surface3); }}
    .u-toggle small {{ font-size:0.75em; color:var(--text-dim); font-weight:400; margin-left:6px; }}
    .u-arrow {{ font-size:0.72em; color:var(--text-dim); }}
    .u-content {{ border-top:1px solid var(--border); }}
    .section-inner {{ padding:12px; border-top:1px solid var(--border); display:none; }}
    table {{ width:100%; border-collapse:collapse; font-size:0.8em; }}
    thead tr {{ background:var(--surface3); }}
    th {{ padding:8px 10px; font-size:0.68em; font-weight:700; color:var(--text-dim); letter-spacing:1.2px; text-transform:uppercase; text-align:left; border-bottom:1px solid var(--border); }}
    td {{ padding:8px 10px; border-bottom:1px solid var(--border); color:var(--text-mid); vertical-align:top; }}
    td.td-price {{ text-align:right; font-weight:600; color:var(--text); }}
    td.td-desc {{ font-size:0.9em; color:var(--text-dim); }}
    tr:last-child td {{ border-bottom:none; }}
    .promo {{ color:var(--red); font-weight:700; }}
    .lista-pre {{
        white-space:pre-wrap; word-wrap:break-word; background:var(--surface2);
        border:1px solid var(--border); border-left:3px solid var(--gold);
        border-radius:8px; padding:12px; font-size:0.82em; color:var(--text-mid); line-height:1.5;
    }}
    .empty-msg {{ text-align:center; padding:16px; color:var(--text-dim); font-size:0.85em; font-style:italic; }}
    .btn-home {{
        display:block; text-align:center; padding:13px;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; border-radius:10px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.9em;
        line-height:1.5; margin-top:14px; transition:all 0.2s;
    }}
    .btn-home:hover {{ transform:translateY(-1px); box-shadow:0 6px 20px rgba(201,168,76,0.25); }}
</style>
</head>
<body>
<header>
    <button class="menu-btn" onclick="toggleMenu()">⚙️</button>
    <div id="extraMenu" class="nav-dropdown">
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Finanze</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/">🏠 Aggiungi Operazione</a>
                <a href="/lista">📈 Gestione Movimenti Mese</a>
                <a href="/stats">📊 Bilancio Mese</a>
                <a href="/fondo_risparmio_web">💰 Fondo Risparmio</a>
                <a href="/scadenze_web">📅 Scadenze del Mese</a>
                <a href="/fairshare_web">⚖️ FairShare</a>
                <a href="/menu_esplora">🔍 Esplora</a>
                <a href="/grafici_web">📅 Grafici e Statistiche</a>
                <a href="/gestione_categorie">⚙️ Gestione Categorie</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Casa</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/utenze?anno={anno_corrente}">💧 Utenze</a>
                <a href="/consultazione_supermercati">🛒 Gestione Supermercati</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Documenti</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/documenti_pdf_web">🗄️ Documenti Contabili</a>
                <a href="/documenti_personali_web">🗄️ Documenti Personali</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Sistema</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/info_sys_web">📡 Monitor Server</a>
                <a href="/cambia_pw_web">🔑 Cambia Password</a>
                <a href="/webauthn_web">👆 Biometrico</a>
                <a href="/cambia_profilo_web">👤 Cambia Profilo</a>
                <a href="/logoff">🔓 Logout</a>
            </div>
        </div>
    </div>
    <div class="header-title">🛒 Gestione Supermercati</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="section-card">
        <button class="section-toggle" onclick="toggleS('lista_spesa', this)">
            <span>📋 Ultima Lista: {file_visualizzato}</span>
            <span class="u-arrow">▶</span>
        </button>
        <div id="lista_spesa" class="section-inner">
            {lista_inner}
        </div>
    </div>
    <div class="section-card">
        <button class="section-toggle" onclick="toggleS('cataloghi', this)">
            <span>🛒 Cataloghi ({len(supermercati)} supermercati)</span>
            <span class="u-arrow">▶</span>
        </button>
        <div id="cataloghi" class="section-inner" style="display:flex; flex-direction:column; gap:6px;">
            {cataloghi_html}
        </div>
    </div>
    <a href="/" class="btn-home">🏠 Torna alla Home</a>
</main>
<script>
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if (btn) btn.textContent = '🌙'; }}
        else               {{ root.classList.remove('light'); if (btn) btn.textContent = '☀️'; }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        applyTheme(next);
    }}
    applyTheme(localStorage.getItem('theme') || 'dark');
    function toggleNavGroup(btn, ev) {{
        if (ev) ev.stopPropagation();
        const items = btn.nextElementSibling;
        const giaAperto = items.classList.contains('open');
        btn.closest('.nav-dropdown').querySelectorAll('.nav-group-items.open').forEach(function(el) {{
            el.classList.remove('open');
            el.previousElementSibling.querySelector('.nav-arrow').textContent = '▶';
        }});
        if (!giaAperto) {{
            items.classList.add('open');
            btn.querySelector('.nav-arrow').textContent = '▼';
        }}
    }}
    function toggleMenu() {{
        const m = document.getElementById("extraMenu");
        m.style.display = m.style.display === "block" ? "none" : "block";
    }}
    function toggleS(id, btn) {{
        const el = document.getElementById(id);
        const arrow = btn.querySelector(".u-arrow");
        const open = el.style.display !== "none" && el.style.display !== "";
        el.style.display = open ? "none" : "flex";
        if (id === "lista_spesa") el.style.display = open ? "none" : "block";
        arrow.textContent = open ? "▶" : "▼";
    }}
    function toggleU(id, btn) {{
        const el = document.getElementById(id);
        const arrow = btn.querySelector(".u-arrow");
        const open = el.style.display === "block";
        el.style.display = open ? "none" : "block";
        arrow.textContent = open ? "▶" : "▼";
    }}
    document.addEventListener("click", function(e) {{
        const menu = document.getElementById("extraMenu");
        const btn = document.querySelector(".menu-btn");
        if (menu && menu.style.display === "block" && !menu.contains(e.target) && e.target !== btn)
            menu.style.display = "none";
    }});
</script>
</body>
</html>"""

# Html Ricerca Globale Web
def pagina_menu_esplora(self):
    mesi_it_map = {
        "01": "Gennaio", "02": "Febbraio", "03": "Marzo",
        "04": "Aprile", "05": "Maggio", "06": "Giugno",
        "07": "Luglio", "08": "Agosto", "09": "Settembre",
        "10": "Ottobre", "11": "Novembre", "12": "Dicembre"
    }
    mesi = [f"{m:02d} - {mesi_it_map[f'{m:02d}']}" for m in range(1, 13)]
    categorie = sorted(set(self.categorie))
    anno_corrente = datetime.date.today().year
    anni = [str(anno) for anno in range(anno_corrente, anno_corrente - 6, -1)]
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>🔎 Esplorazione Avanzata</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
    (function() {{
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    }})();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg:#050505; --surface:#0f0f0f; --surface2:#161616; --surface3:#1e1e1e;
        --border:rgba(255,255,255,0.07); --border-active:rgba(99,160,240,0.5);
        --gold:#c9a84c; --blue:#63a0f0; --green:#4caf82; --red:#e05a5a;
        --text:#e8e8e8; --text-dim:#555; --text-mid:#888; --radius-lg:18px;
    }}
    :root.light {{
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --border-active:rgba(61,127,212,0.5);
        --gold:#b8902a; --blue:#3d7fd4; --green:#3a9068; --red:#cc3333;
        --text:#1a1a1a; --text-dim:#999; --text-mid:#555;
    }}
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{
        font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text);
        min-height:100vh; padding-bottom:50px; transition:background 0.3s,color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 40% at 50% -10%, rgba(99,160,240,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 60%);
    }}
    header {{
        padding:14px 16px 12px; display:flex; align-items:center; justify-content:center;
        border-bottom:1px solid var(--border); background:rgba(5,5,5,0.95);
        backdrop-filter:blur(20px); position:sticky; top:0; z-index:100;
    }}
    :root.light header {{ background:rgba(245,245,240,0.95); }}
    .menu-btn {{
        position:absolute; left:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border); color:var(--gold);
        width:36px; height:36px; border-radius:10px; font-size:1em;
        cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.2s;
    }}
    .menu-btn:hover {{ border-color:var(--gold); box-shadow:0 0 12px rgba(201,168,76,0.2); }}
    .header-title {{ font-family:'DM Sans',sans-serif; font-size:1em; font-weight:700; color:var(--text); }}
    .theme-toggle {{
        position:absolute; right:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border);
        border-radius:8px; width:34px; height:34px;
        display:flex; align-items:center; justify-content:center;
        cursor:pointer; font-size:1em; transition:all 0.2s;
    }}
    .theme-toggle:hover {{ border-color:var(--gold); }}
    .nav-dropdown {{
        position:absolute; top:calc(100% + 6px); left:10px;
        background:var(--surface2); border:1px solid var(--border);
        border-radius:var(--radius-lg); display:none; z-index:1000;
        width:270px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.7);
    }}
    .nav-dropdown a {{
        display:flex; align-items:center; gap:10px; padding:10px 16px;
        text-decoration:none; color:var(--text-mid); border-bottom:1px solid var(--border);
        font-size:0.87em; transition:all 0.15s;
    }}
    .nav-dropdown a:last-child {{ border-bottom:none; }}
    .nav-dropdown a:hover {{ background:var(--surface3); color:var(--text); padding-left:22px; }}
    .nav-group-btn {{ display:flex; justify-content:space-between; align-items:center; width:100%;
        padding:8px 16px; background:none; border:none; font-family:inherit; color:var(--gold);
        font-size:0.7em; font-weight:700; letter-spacing:1px; text-transform:uppercase; cursor:pointer; opacity:0.85; }}
    .nav-group-btn:hover {{ opacity:1; background:var(--surface3); }}
    .nav-arrow {{ font-size:0.85em; transition:transform 0.15s; }}
    .nav-group-items {{ display:none; flex-direction:column; }}
    .nav-group-items.open {{ display:flex; }}
    main {{ padding:14px; max-width:560px; margin:0 auto; animation:fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .form-card {{
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); padding:20px 18px 18px;
        position:relative; overflow:hidden; margin-top:14px;
    }}
    .form-card::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .form-group {{ margin-bottom:12px; }}
    label {{
        display:block; font-size:0.68em; font-weight:600; color:var(--text-dim);
        letter-spacing:1.8px; text-transform:uppercase; margin-bottom:6px;
    }}
    input, select {{
        width:100%; padding:10px 13px; background:var(--surface2);
        border:1px solid var(--border); border-radius:9px; color:var(--text);
        font-family:'DM Sans',sans-serif; font-size:0.92em;
        transition:all 0.2s; outline:none; -webkit-appearance:none; appearance:none;
    }}
    input:focus, select:focus {{
        border-color:var(--border-active); background:var(--surface3);
        box-shadow:0 0 0 3px rgba(99,160,240,0.07);
    }}
    input::placeholder {{ color:var(--text-dim); }}
    select {{
        background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='7' viewBox='0 0 12 7'%3E%3Cpath fill='none' stroke='%23555' stroke-width='1.5' d='M1 1l5 5 5-5'/%3E%3C/svg%3E");
        background-repeat:no-repeat; background-position:right 12px center;
        padding-right:32px; cursor:pointer;
    }}
    select option {{ background:var(--surface2); color:var(--text); }}
    .form-row {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
    .collapsible-wrap {{ margin-top:14px; padding-top:14px; border-top:1px solid var(--border); }}
    .collapsible-toggle {{
        background:none; border:none; width:100%;
        display:flex; align-items:center; gap:8px;
        color:var(--text-mid); font-family:'DM Sans',sans-serif;
        font-size:0.82em; font-weight:700; letter-spacing:0.5px;
        cursor:pointer; padding:0 0 10px 0; text-align:left;
        line-height:1.5; transition:color 0.15s;
    }}
    .collapsible-toggle:hover {{ color:var(--blue); }}
    .arrow {{ font-size:0.7em; transition:transform 0.25s; }}
    .collapsible-open .arrow {{ transform:rotate(90deg); }}
    .collapsible-content {{ display:none; }}
    .collapsible-open .collapsible-content {{ display:block; }}
    .btn-submit {{
        width:100%; padding:13px; margin-top:16px;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; border:none; border-radius:9px;
        font-family:'DM Sans',sans-serif; font-size:0.95em; font-weight:700;
        line-height:1.5; letter-spacing:0.5px; cursor:pointer; transition:all 0.2s;
    }}
    .btn-submit:hover {{ transform:translateY(-1px); box-shadow:0 6px 20px rgba(201,168,76,0.25); }}
    .btn-submit:active {{ transform:translateY(0); }}
    .btn-home {{
        display:block; text-align:center; padding:13px; margin-top:10px;
        background:var(--surface); border:1px solid var(--border);
        color:var(--text-mid); border-radius:9px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.88em;
        line-height:1.5; transition:all 0.2s;
    }}
    .btn-home:hover {{ border-color:var(--border-active); color:var(--text); }}
</style>
</head>
<body>
<header>
    <button class="menu-btn" onclick="toggleMenu()">⚙️</button>
    <div id="extraMenu" class="nav-dropdown">
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Finanze</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/">🏠 Aggiungi Operazione</a>
                <a href="/lista">📈 Gestione Movimenti Mese</a>
                <a href="/stats">📊 Bilancio Mese</a>
                <a href="/fondo_risparmio_web">💰 Fondo Risparmio</a>
                <a href="/scadenze_web">📅 Scadenze del Mese</a>
                <a href="/fairshare_web">⚖️ FairShare</a>
                <a href="/menu_esplora">🔍 Esplora</a>
                <a href="/grafici_web">📅 Grafici e Statistiche</a>
                <a href="/gestione_categorie">⚙️ Gestione Categorie</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Casa</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/utenze?anno={anno_corrente}">💧 Utenze</a>
                <a href="/consultazione_supermercati">🛒 Gestione Supermercati</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Documenti</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/documenti_pdf_web">🗄️ Documenti Contabili</a>
                <a href="/documenti_personali_web">🗄️ Documenti Personali</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Sistema</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/info_sys_web">📡 Monitor Server</a>
                <a href="/cambia_pw_web">🔑 Cambia Password</a>
                <a href="/webauthn_web">👆 Biometrico</a>
                <a href="/cambia_profilo_web">👤 Cambia Profilo</a>
                <a href="/logoff">🔓 Logout</a>
            </div>
        </div>
    </div>
    <div class="header-title">🔎 Esplorazione Avanzata</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="form-card">
        <form method="get" action="/cerca_avanzata">
            <div class="form-row">
                <div class="form-group">
                    <label>Categoria</label>
                    <select name="categoria">
                        <option value="">-- Qualsiasi --</option>
                        {''.join(f"<option value='{html.escape(str(cat))}'>{html.escape(str(cat))}</option>" for cat in categorie)}
                    </select>
                </div>
                <div class="form-group">
                    <label>Tipo</label>
                    <select name="tipo">
                        <option value="">-- Qualsiasi --</option>
                        <option value="Entrata">Entrata</option>
                        <option value="Uscita">Uscita</option>
                    </select>
                </div>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Anno</label>
                    <select name="anno">
                        <option value="">-- Tutti --</option>
                        {''.join(f"<option value='{html.escape(a)}'>{html.escape(a)}</option>" for a in anni)}
                    </select>
                </div>
                <div class="form-group">
                    <label>Mese</label>
                    <select name="mese">
                        <option value="">-- Tutti --</option>
                        {''.join(f"<option value='{m.split(' - ')[0]}'>{m}</option>" for m in mesi)}
                    </select>
                </div>
            </div>
            <div class="collapsible-wrap">
                <button type="button" class="collapsible-toggle" onclick="toggleCollapsible(this)">
                    <span class="arrow">▶</span> Filtri aggiuntivi
                </button>
                <div class="collapsible-content">
                    <div class="form-row">
                        <div class="form-group">
                            <label>Importo minimo (€)</label>
                            <input type="number" name="min_importo" step="0.01" placeholder="es: 10.50">
                        </div>
                        <div class="form-group">
                            <label>Importo massimo (€)</label>
                            <input type="number" name="max_importo" step="0.01" placeholder="es: 100.00">
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Testo libero</label>
                        <input type="text" name="q" placeholder="es: pane, bolletta, abbonamento">
                    </div>
                </div>
            </div>
            <button type="submit" class="btn-submit">🔍 Avvia Esplorazione</button>
        </form>
    </div>
    <a href="/" class="btn-home">🏠 Torna alla Home</a>
</main>
<script>
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if (btn) btn.textContent = '🌙'; }}
        else               {{ root.classList.remove('light'); if (btn) btn.textContent = '☀️'; }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        applyTheme(next);
    }}
    applyTheme(localStorage.getItem('theme') || 'dark');
    function toggleNavGroup(btn, ev) {{
        if (ev) ev.stopPropagation();
        const items = btn.nextElementSibling;
        const giaAperto = items.classList.contains('open');
        btn.closest('.nav-dropdown').querySelectorAll('.nav-group-items.open').forEach(function(el) {{
            el.classList.remove('open');
            el.previousElementSibling.querySelector('.nav-arrow').textContent = '▶';
        }});
        if (!giaAperto) {{
            items.classList.add('open');
            btn.querySelector('.nav-arrow').textContent = '▼';
        }}
    }}
    function toggleMenu() {{
        const m = document.getElementById("extraMenu");
        m.style.display = m.style.display === "block" ? "none" : "block";
    }}
    function toggleCollapsible(btn) {{
        btn.parentNode.classList.toggle('collapsible-open');
    }}
    document.addEventListener("click", function(e) {{
        const menu = document.getElementById("extraMenu");
        const btn = document.querySelector(".menu-btn");
        if (menu && menu.style.display === "block" && !menu.contains(e.target) && e.target !== btn)
            menu.style.display = "none";
    }});
</script>
</body>
</html>"""

# Cambia Profilo (Web) - Logica di switch, richiamata dalla rotta POST
def esegui_switch_profilo_web(self, nome_profilo, crea_nuovo=False):
    import __main__ as _app
    import threading
    from moduli.costanti import salva_profilo_attivo
    from moduli.profili import elenco_profili, _nome_profilo_valido, _restart_application

    nome_profilo = (nome_profilo or "").strip()
    if not nome_profilo:
        return {"ok": False, "errore": "Nome profilo mancante"}

    profili_esistenti = elenco_profili(self)

    if crea_nuovo:
        nome_valido = _nome_profilo_valido(nome_profilo)
        if not nome_valido:
            return {"ok": False, "errore": "Nome profilo non valido"}
        if nome_valido in profili_esistenti:
            return {"ok": False, "errore": "Esiste già un profilo con questo nome"}
        nome_profilo = nome_valido
    else:
        if nome_profilo not in profili_esistenti:
            return {"ok": False, "errore": "Profilo non trovato"}

    if nome_profilo == _app.PROFILO_ATTIVO:
        return {"ok": False, "errore": "Questo profilo è già attivo"}

    if nome_profilo != "Principale":
        cartella_nuovo_profilo = os.path.join(_app.PROFILI_DIR, nome_profilo)
        db_nuovo_profilo = os.path.join(cartella_nuovo_profilo, "db")
        os.makedirs(db_nuovo_profilo, exist_ok=True)
        if crea_nuovo:
            from moduli.profili import _copia_certificati_e_licenza, _propaga_config_webserver
            _copia_certificati_e_licenza(_app.DB_DIR, db_nuovo_profilo)
            _propaga_config_webserver(_app.DB_DIR, db_nuovo_profilo)
    else:
        db_nuovo_profilo = os.path.join(_app.PATH_LOCALE, "db")
    _salvataggio_fatto = threading.Event()
    _errore_salvataggio = []
    def _salva_su_thread_principale():
        try:
            self.save_db()
        except Exception as e:
            _errore_salvataggio.append(str(e))
        finally:
            _salvataggio_fatto.set()
    self.after(0, _salva_su_thread_principale)
    if not _salvataggio_fatto.wait(timeout=30):
        return {"ok": False, "errore": "Timeout durante il salvataggio dei dati"}
    if _errore_salvataggio:
        return {"ok": False, "errore": f"Impossibile salvare i dati correnti: {_errore_salvataggio[0]}"}
    try:
        os.makedirs(db_nuovo_profilo, exist_ok=True)
        with open(os.path.join(db_nuovo_profilo, ".web_switch_pending"), "w") as _f:
            _f.write(datetime.datetime.now().isoformat())
    except Exception:
        pass
    salva_profilo_attivo(_app.PATH_LOCALE, nome_profilo)
    try:
        self._on_close_lock()
    except Exception:
        pass
    self.after(900, _restart_application)
    return {"ok": True, "profilo": nome_profilo, "nuovo": crea_nuovo}

# Html Cambia Profilo (Web)
def pagina_cambia_profilo_web(self):
    import __main__ as _app
    from moduli.profili import elenco_profili, _etichetta_profilo

    profili = elenco_profili(self)
    attivo  = _app.PROFILO_ATTIVO

    righe_altri = []
    for nome in profili:
        if nome == attivo:
            continue
        etichetta = html.escape(_etichetta_profilo(self, nome))
        nome_esc  = html.escape(nome, quote=True)
        righe_altri.append(f"""
        <div class="profile-item">
            <span class="profile-name">👤 {etichetta}</span>
            <form method="post" action="/switch_profilo_web" data-etichetta="{etichetta}" onsubmit="return confermaSwitchProfilo(this)">
                <input type="hidden" name="azione" value="switch">
                <input type="hidden" name="profilo" value="{nome_esc}">
                <button type="submit" class="btn-switch">🔄 Attiva</button>
            </form>
        </div>""")
    lista_altri_html = "".join(righe_altri) if righe_altri else \
        '<div class="empty-hint">Nessun altro profilo disponibile. Creane uno qui sotto.</div>'

    etichetta_attivo = html.escape(_etichetta_profilo(self, attivo))

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>👤 Cambia Profilo</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
    (function() {{
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    }})();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg:#050505; --surface:#0f0f0f; --surface2:#161616; --surface3:#1e1e1e;
        --border:rgba(255,255,255,0.07); --border-active:rgba(99,160,240,0.5);
        --gold:#c9a84c; --blue:#63a0f0; --green:#4caf82; --red:#e05a5a;
        --text:#e8e8e8; --text-dim:#555; --text-mid:#888; --radius-lg:18px;
    }}
    :root.light {{
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --border-active:rgba(61,127,212,0.5);
        --gold:#b8902a; --blue:#3d7fd4; --green:#3a9068; --red:#cc3333;
        --text:#1a1a1a; --text-dim:#999; --text-mid:#555;
    }}
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{
        font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text);
        min-height:100vh; padding-bottom:50px; transition:background 0.3s,color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 40% at 50% -10%, rgba(99,160,240,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 60%);
    }}
    header {{
        padding:14px 16px 12px; display:flex; align-items:center; justify-content:center;
        border-bottom:1px solid var(--border); background:rgba(5,5,5,0.95);
        backdrop-filter:blur(20px); position:sticky; top:0; z-index:100;
    }}
    :root.light header {{ background:rgba(245,245,240,0.95); }}
    .menu-btn {{
        position:absolute; left:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border); color:var(--gold);
        width:36px; height:36px; border-radius:10px; font-size:1em;
        cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.2s;
    }}
    .menu-btn:hover {{ border-color:var(--gold); box-shadow:0 0 12px rgba(201,168,76,0.2); }}
    .header-title {{ font-family:'DM Sans',sans-serif; font-size:1em; font-weight:700; color:var(--text); }}
    .theme-toggle {{
        position:absolute; right:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border);
        border-radius:8px; width:34px; height:34px;
        display:flex; align-items:center; justify-content:center;
        cursor:pointer; font-size:1em; transition:all 0.2s;
    }}
    .theme-toggle:hover {{ border-color:var(--gold); }}
    .nav-dropdown {{
        position:absolute; top:calc(100% + 6px); left:10px;
        background:var(--surface2); border:1px solid var(--border);
        border-radius:var(--radius-lg); display:none; z-index:1000;
        width:270px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.7);
    }}
    .nav-dropdown a {{
        display:flex; align-items:center; gap:10px; padding:10px 16px;
        text-decoration:none; color:var(--text-mid); border-bottom:1px solid var(--border);
        font-size:0.87em; transition:all 0.15s;
    }}
    .nav-dropdown a:last-child {{ border-bottom:none; }}
    .nav-dropdown a:hover {{ background:var(--surface3); color:var(--text); padding-left:22px; }}
    .nav-group-btn {{ display:flex; justify-content:space-between; align-items:center; width:100%;
        padding:8px 16px; background:none; border:none; font-family:inherit; color:var(--gold);
        font-size:0.7em; font-weight:700; letter-spacing:1px; text-transform:uppercase; cursor:pointer; opacity:0.85; }}
    .nav-group-btn:hover {{ opacity:1; background:var(--surface3); }}
    .nav-arrow {{ font-size:0.85em; transition:transform 0.15s; }}
    .nav-group-items {{ display:none; flex-direction:column; }}
    .nav-group-items.open {{ display:flex; }}
    main {{ padding:14px; max-width:480px; margin:0 auto; animation:fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .sec-card {{
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); margin-bottom:12px; position:relative; overflow:hidden;
    }}
    .sec-card::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .sec-title {{
        font-size:0.68em; font-weight:700; color:var(--text-dim); letter-spacing:1.8px;
        text-transform:uppercase; padding:14px 16px 8px;
    }}
    .active-box {{
        display:flex; align-items:center; justify-content:space-between;
        padding:10px 16px 16px;
    }}
    .active-name {{ font-size:1.05em; font-weight:800; color:var(--gold); }}
    .active-badge {{
        font-size:0.62em; font-weight:700; letter-spacing:1px; text-transform:uppercase;
        color:var(--green); background:rgba(76,175,130,0.12);
        padding:4px 9px; border-radius:6px;
    }}
    .profile-item {{
        display:flex; align-items:center; justify-content:space-between;
        padding:12px 16px; border-top:1px solid var(--border);
    }}
    .profile-item form {{ margin:0; }}
    .profile-name {{ font-size:0.9em; font-weight:600; color:var(--text); }}
    .btn-switch {{
        padding:8px 14px; border:none; border-radius:8px; cursor:pointer;
        background:linear-gradient(135deg, var(--blue), #2f5faa); color:#fff;
        font-family:'DM Sans',sans-serif; font-size:0.78em; font-weight:700;
        transition:all 0.2s;
    }}
    .btn-switch:hover {{ transform:translateY(-1px); box-shadow:0 6px 16px rgba(99,160,240,0.3); }}
    .empty-hint {{ padding:8px 16px 16px; font-size:0.82em; color:var(--text-dim); }}
    .new-form {{ padding:4px 16px 16px; display:flex; flex-wrap:wrap; gap:8px; }}
    .new-form input[type="text"] {{
        flex:1 1 120px; min-width:0; padding:10px 13px; background:var(--surface2);
        border:1px solid var(--border); border-radius:9px; color:var(--text);
        font-family:'DM Sans',sans-serif; font-size:0.88em; outline:none; transition:all 0.2s;
    }}
    .new-form input[type="text"]:focus {{
        border-color:var(--border-active); background:var(--surface3);
        box-shadow:0 0 0 3px rgba(99,160,240,0.07);
    }}
    .btn-nuovo {{
        padding:10px 14px; border:none; border-radius:9px; cursor:pointer; white-space:nowrap;
        background:linear-gradient(135deg, var(--green), #2d7a56); color:#000;
        font-family:'DM Sans',sans-serif; font-size:0.82em; font-weight:700; transition:all 0.2s;
    }}
    .btn-nuovo:hover {{ transform:translateY(-1px); box-shadow:0 6px 16px rgba(76,175,130,0.25); }}
    .warn-box {{
        background:rgba(224,90,90,0.08); border:1px solid rgba(224,90,90,0.25);
        color:var(--red); font-size:0.78em; padding:10px 13px; border-radius:10px;
        margin-bottom:14px; line-height:1.5;
    }}
    .err-box {{
        background:rgba(224,90,90,0.1); border:1px solid rgba(224,90,90,0.25);
        color:var(--red); font-size:0.82em; padding:10px 13px; border-radius:10px;
        margin-bottom:14px; display:none;
    }}
    .btn-home {{ display:block; text-align:center; padding:13px; margin-top:12px;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; border-radius:10px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.9em;
        line-height:1.5; transition:all 0.2s; }}
    .btn-home:hover {{ transform:translateY(-1px); box-shadow:0 6px 20px rgba(201,168,76,0.25); }}
    .modal-overlay {{ display:none; position:fixed; inset:0;
        background:rgba(0,0,0,0.75); backdrop-filter:blur(6px);
        z-index:3000; align-items:center; justify-content:center; }}
    .modal-box {{ background:var(--surface2); border:1px solid var(--border);
        border-radius:var(--radius-lg); padding:24px 20px; width:88%; max-width:320px; text-align:center; }}
    .modal-title {{ font-family:'DM Sans',sans-serif; font-size:1em; font-weight:800; color:var(--gold); margin-bottom:10px; }}
    .modal-text {{ font-size:0.88em; color:var(--text-mid); margin-bottom:18px; line-height:1.5; }}
    .modal-btns {{ display:flex; gap:10px; }}
    .m-btn {{ flex:1; padding:12px; border-radius:9px; border:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.88em; cursor:pointer; transition:all 0.15s; }}
    .m-cancel {{ background:var(--surface3); color:var(--text-mid); }}
    .m-confirm {{ background:linear-gradient(135deg, var(--blue), #2f5faa); color:#fff; }}
    .m-confirm:hover {{ box-shadow:0 6px 16px rgba(99,160,240,0.3); }}
</style>
</head>
<body>
<header>
    <button class="menu-btn" onclick="toggleMenu()">⚙️</button>
    <div id="extraMenu" class="nav-dropdown">
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Finanze</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/">🏠 Aggiungi Operazione</a>
                <a href="/lista">📈 Gestione Movimenti Mese</a>
                <a href="/stats">📊 Bilancio Mese</a>
                <a href="/fondo_risparmio_web">💰 Fondo Risparmio</a>
                <a href="/scadenze_web">📅 Scadenze del Mese</a>
                <a href="/fairshare_web">⚖️ FairShare</a>
                <a href="/menu_esplora">🔍 Esplora</a>
                <a href="/grafici_web">📅 Grafici e Statistiche</a>
                <a href="/gestione_categorie">⚙️ Gestione Categorie</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Casa</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/utenze">💧 Utenze</a>
                <a href="/consultazione_supermercati">🛒 Gestione Supermercati</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Documenti</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/documenti_pdf_web">🗄️ Documenti Contabili</a>
                <a href="/documenti_personali_web">🗄️ Documenti Personali</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Sistema</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/info_sys_web">📡 Monitor Server</a>
                <a href="/cambia_pw_web">🔑 Cambia Password</a>
                <a href="/webauthn_web">👆 Biometrico</a>
                <a href="/cambia_profilo_web">👤 Cambia Profilo</a>
                <a href="/logoff">🔓 Logout</a>
            </div>
        </div>
    </div>
    <div class="header-title">👤 Cambia Profilo</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="err-box" id="errBox"></div>
    <div class="warn-box">⚠️ Il cambio profilo riavvia l'intera applicazione: tutte le sessioni web attive (anche su altri dispositivi) verranno temporaneamente disconnesse.</div>
    <div class="sec-card">
        <div class="sec-title">Profilo attivo</div>
        <div class="active-box">
            <span class="active-name">{etichetta_attivo}</span>
            <span class="active-badge">● Attivo</span>
        </div>
    </div>
    <div class="sec-card">
        <div class="sec-title">Passa ad un altro profilo</div>
        {lista_altri_html}
    </div>
    <div class="sec-card">
        <div class="sec-title">Crea nuovo profilo</div>
        <form class="new-form" method="post" action="/switch_profilo_web"
              onsubmit="return confermaCreaProfilo(this)">
            <input type="hidden" name="azione" value="nuovo">
            <input type="text" name="profilo" placeholder="Nome nuovo profilo" maxlength="40" required>
            <button type="submit" class="btn-nuovo">➕ Crea e Passa</button>
        </form>
    </div>
    <a href="/" class="btn-home">🏠 Torna alla Home</a>
</main>
<div id="switchModal" class="modal-overlay">
    <div class="modal-box">
        <div class="modal-title">🔄 Cambio Profilo</div>
        <div class="modal-text" id="modalText"></div>
        <div class="modal-btns">
            <button class="m-btn m-cancel" onclick="chiudiModalConferma()">Annulla</button>
            <button id="confermaSwitchBtn" class="m-btn m-confirm">Conferma</button>
        </div>
    </div>
</div>
<script>
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if (btn) btn.textContent = '🌙'; }}
        else               {{ root.classList.remove('light'); if (btn) btn.textContent = '☀️'; }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        applyTheme(next);
    }}
    applyTheme(localStorage.getItem('theme') || 'dark');
    function toggleNavGroup(btn, ev) {{
        if (ev) ev.stopPropagation();
        const items = btn.nextElementSibling;
        const giaAperto = items.classList.contains('open');
        btn.closest('.nav-dropdown').querySelectorAll('.nav-group-items.open').forEach(function(el) {{
            el.classList.remove('open');
            el.previousElementSibling.querySelector('.nav-arrow').textContent = '▶';
        }});
        if (!giaAperto) {{
            items.classList.add('open');
            btn.querySelector('.nav-arrow').textContent = '▼';
        }}
    }}
    function toggleMenu() {{
        const m = document.getElementById("extraMenu");
        m.style.display = m.style.display === "block" ? "none" : "block";
    }}
    document.addEventListener("click", function(e) {{
        const menu = document.getElementById("extraMenu");
        const btn = document.querySelector(".menu-btn");
        if (menu && menu.style.display === "block" && !menu.contains(e.target) && e.target !== btn)
            menu.style.display = "none";
    }});
    function confermaSwitchProfilo(form) {{
        const nome = form.dataset.etichetta || "";
        return apriModalConferma(form, "Passare al profilo '" + nome + "'?\\n\\nL'app verrà riavviata per tutti gli utenti connessi.");
    }}
    function confermaCreaProfilo(form) {{
        return apriModalConferma(form, "Creare il nuovo profilo e passare subito ad esso?\\n\\nL'app verrà riavviata.");
    }}
    let formInAttesa = null;
    function apriModalConferma(form, messaggio) {{
        formInAttesa = form;
        document.getElementById("modalText").textContent = messaggio;
        document.getElementById("switchModal").style.display = "flex";
        return false;
    }}
    function chiudiModalConferma() {{
        document.getElementById("switchModal").style.display = "none";
        formInAttesa = null;
    }}
    document.getElementById("confermaSwitchBtn").onclick = function() {{
        document.getElementById("switchModal").style.display = "none";
        if (formInAttesa) formInAttesa.submit();
    }};
    const p = new URLSearchParams(window.location.search);
    if (p.get('errore')) {{
        const el = document.getElementById('errBox');
        el.textContent = '❌ ' + p.get('errore');
        el.style.display = 'block';
    }}
</script>
</body>
</html>"""

# Html Switch Profilo In Corso (Web) - Interstiziale di riavvio
def pagina_switch_in_corso_web(self, nome_profilo, nuovo=False):
    from moduli.profili import _etichetta_profilo
    etichetta = html.escape(_etichetta_profilo(self, nome_profilo))
    delay_link_ms = 25000 if nuovo else 8000
    max_tentativi = 120 if nuovo else 60
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>🔄 Cambio Profilo in corso</title>
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<script>
    (function() {{
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    }})();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg:#050505; --surface:#0f0f0f; --surface2:#161616; --surface3:#1e1e1e;
        --border:rgba(255,255,255,0.07); --border-active:rgba(99,160,240,0.5);
        --gold:#c9a84c; --blue:#63a0f0; --green:#4caf82; --red:#e05a5a;
        --text:#e8e8e8; --text-dim:#666; --text-mid:#888; --radius-lg:18px;
    }}
    :root.light {{
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --border-active:rgba(61,127,212,0.5);
        --gold:#b8902a; --blue:#3d7fd4; --green:#3a9068; --red:#cc3333;
        --text:#1a1a1a; --text-dim:#888; --text-mid:#555;
    }}
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{
        font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text);
        min-height:100vh; min-height:100dvh; transition:background 0.3s,color 0.3s;
        display:flex; align-items:center; justify-content:center; padding:16px;
    }}
    .theme-toggle {{
        position:fixed; right:14px; top:14px;
        background:var(--surface3); border:1px solid var(--border);
        border-radius:8px; width:34px; height:34px;
        display:flex; align-items:center; justify-content:center;
        cursor:pointer; font-size:1em; transition:all 0.2s;
    }}
    .theme-toggle:hover {{ border-color:var(--gold); }}
    .box {{
        width:100%; max-width:380px; text-align:center;
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); padding:34px 24px; position:relative; overflow:hidden;
        box-shadow:0 20px 60px rgba(0,0,0,0.6);
    }}
    .box::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .spinner {{
        width:44px; height:44px; margin:0 auto 18px;
        border:3px solid var(--border); border-top-color:var(--gold);
        border-radius:50%; animation:spin 0.9s linear infinite;
    }}
    @keyframes spin {{ to {{ transform:rotate(360deg); }} }}
    .titolo {{ font-size:1.05em; font-weight:800; margin-bottom:8px; }}
    .sub {{ font-size:0.82em; color:var(--text-dim); line-height:1.5; }}
    .manual-link {{ display:inline-block; margin-top:18px; padding:10px 20px; font-size:0.82em; font-weight:700;
        color:#fff; text-decoration:none; border-radius:9px;
        background:linear-gradient(135deg, var(--blue), #2f5faa);
        opacity:0; transition:opacity 0.4s; }}
    .manual-link.visible {{ opacity:1; }}
</style>
</head>
<body>
<button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
<div class="box">
    <div class="spinner"></div>
    <div class="titolo">Passaggio al profilo "{etichetta}"</div>
    <div class="sub">L'applicazione si sta riavviando per caricare i dati del nuovo profilo.<br>Verrai reindirizzato automaticamente.</div>
    <a href="/login" class="manual-link" id="manualLink">🔄 Ricarica pagina</a>
</div>
<script>
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if (btn) btn.textContent = '🌙'; }}
        else               {{ root.classList.remove('light'); if (btn) btn.textContent = '☀️'; }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        applyTheme(next);
    }}
    applyTheme(localStorage.getItem('theme') || 'dark');
    setTimeout(function() {{
        document.getElementById('manualLink').classList.add('visible');
    }}, {delay_link_ms});
    let tentativi = 0;
    function provaPing() {{
        tentativi++;
        fetch('/ping', {{cache:'no-store'}})
            .then(r => {{
                if (r.ok) {{ setTimeout(() => {{ window.location.href = '/'; }}, 700); }}
                else {{ ritenta(); }}
            }})
            .catch(() => ritenta());
    }}
    function ritenta() {{
        if (tentativi < {max_tentativi}) setTimeout(provaPing, 1500);
        else window.location.href = '/login';
    }}
    setTimeout(provaPing, 2500);
</script>
</body>
</html>"""

# Html Gestione Categorie Web
def add_categoria_web(self, params):
    nome = params.get("nome_categoria", [""])[0].strip()
    tipo = params.get("tipo_categoria", ["Uscita"])[0]
    if not nome or nome in self.categorie or nome == self.CATEGORIA_RIMOSSA:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Errore: Categoria '{nome}' già esistente o non valida.")
        return self.html_gestione_categorie()
    self.categorie.append(nome)
    self.categorie_tipi[nome] = tipo
    self.categorie.sort()
    budget_val = params.get("budget_categoria", ["0"])[0].strip().replace(",", ".")
    try:
        budget_val = float(budget_val)
    except ValueError:
        budget_val = 0.0
    if budget_val > 0:
        self.budget_categorie[nome] = budget_val
    elif nome in self.budget_categorie:
        del self.budget_categorie[nome]
    budget_anno_val = params.get("budget_annuale_categoria", ["0"])[0].strip().replace(",", ".")
    try:
        budget_anno_val = float(budget_anno_val)
    except ValueError:
        budget_anno_val = 0.0
    if budget_anno_val > 0:
        self.budget_annuale_categorie[nome] = budget_anno_val
    elif nome in self.budget_annuale_categorie:
        del self.budget_annuale_categorie[nome]
    self.save_db()
    self.refresh_categorie_web()
    

def modifica_categoria_web(self, params):
    old_nome = params.get("categoria_selezionata", [""])[0]
    new_nome = params.get("nuovo_nome", [""])[0].strip()
    nuovo_tipo = params.get("nuovo_tipo", ["Uscita"])[0]
    if not old_nome or old_nome == "Generica":
        return
    if not new_nome:
        new_nome = old_nome
    if new_nome == old_nome:
        self.categorie_tipi[new_nome] = nuovo_tipo
    else:
        if new_nome in self.categorie:
            return
        idx = self.categorie.index(old_nome)
        self.categorie[idx] = new_nome
        self.categorie_tipi[new_nome] = nuovo_tipo
        self.categorie_tipi.pop(old_nome, None)
        for d in self.spese:
            new_entries = []
            for entry in self.spese[d]:
                if entry[0] == old_nome:
                    entry = entry.sostituisci(categoria=new_nome) if isinstance(entry, SpesaEntry) else (new_nome,) + entry[1:]
                new_entries.append(entry)
            self.spese[d] = new_entries
        self.categorie.sort()
    budget_val = params.get("budget_categoria", ["0"])[0].strip().replace(",", ".")
    try:
        budget_val = float(budget_val)
    except ValueError:
        budget_val = 0.0
    nome_finale = new_nome
    if budget_val > 0:
        self.budget_categorie[nome_finale] = budget_val
    elif nome_finale in self.budget_categorie:
        del self.budget_categorie[nome_finale]
    if new_nome != old_nome and old_nome in self.budget_categorie:
        del self.budget_categorie[old_nome]
    budget_anno_val = params.get("budget_annuale_categoria", ["0"])[0].strip().replace(",", ".")
    try:
        budget_anno_val = float(budget_anno_val)
    except ValueError:
        budget_anno_val = 0.0
    if budget_anno_val > 0:
        self.budget_annuale_categorie[nome_finale] = budget_anno_val
    elif nome_finale in self.budget_annuale_categorie:
        del self.budget_annuale_categorie[nome_finale]
    if new_nome != old_nome and old_nome in self.budget_annuale_categorie:
        del self.budget_annuale_categorie[old_nome]
    self.save_db()
    self.refresh_categorie_web()

def cancella_categoria_web(self, params):
    cat_da_cancellare = params.get("categoria_selezionata", [""])[0]
    if not cat_da_cancellare or cat_da_cancellare not in self.categorie or cat_da_cancellare == "Generica":
        return
    self.categorie.remove(cat_da_cancellare)
    self.categorie_tipi.pop(cat_da_cancellare, None)
    self.budget_categorie.pop(cat_da_cancellare, None)
    self.budget_annuale_categorie.pop(cat_da_cancellare, None)
    for d in self.spese:
        new_entries = []
        for entry in self.spese[d]:
            if entry[0] == cat_da_cancellare:
                entry = entry.sostituisci(categoria=self.CATEGORIA_RIMOSSA) if isinstance(entry, SpesaEntry) else (self.CATEGORIA_RIMOSSA,) + entry[1:]
            new_entries.append(entry)
        self.spese[d] = new_entries
    self.save_db()
    self.refresh_categorie_web()

def refresh_categorie_web(self):
    self.after(100, self._esegui_aggiornamento_gui)
                    
# Html Gestione Categorie Web             
def html_gestione_categorie(self):
    import datetime
    categorie_tipi_js = str(self.categorie_tipi).replace("'", '"')
    categorie_options = "".join(
        f"<option value='{cat}' data-budget='{self.budget_categorie.get(cat, 0):.2f}' data-budget-annuo='{self.budget_annuale_categorie.get(cat, 0):.2f}'>{cat}</option>"
        for cat in sorted(self.categorie, key=lambda x: x.strip().lower())
    )
    anno_corrente = datetime.datetime.now().year
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>⚙️ Gestione Categorie</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
    (function() {{
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    }})();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg:#050505; --surface:#0f0f0f; --surface2:#161616; --surface3:#1e1e1e;
        --border:rgba(255,255,255,0.07); --border-active:rgba(99,160,240,0.5);
        --gold:#c9a84c; --blue:#63a0f0; --green:#4caf82; --red:#e05a5a;
        --text:#e8e8e8; --text-dim:#555; --text-mid:#888; --radius-lg:18px;
    }}
    :root.light {{
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --border-active:rgba(61,127,212,0.5);
        --gold:#b8902a; --blue:#3d7fd4; --green:#3a9068; --red:#cc3333;
        --text:#1a1a1a; --text-dim:#999; --text-mid:#555;
    }}
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{
        font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text);
        min-height:100vh; padding-bottom:50px; transition:background 0.3s,color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 40% at 50% -10%, rgba(99,160,240,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 60%);
    }}
    header {{
        padding:14px 16px 12px; display:flex; align-items:center; justify-content:center;
        border-bottom:1px solid var(--border); background:rgba(5,5,5,0.95);
        backdrop-filter:blur(20px); position:sticky; top:0; z-index:100;
    }}
    :root.light header {{ background:rgba(245,245,240,0.95); }}
    .menu-btn {{
        position:absolute; left:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border); color:var(--gold);
        width:36px; height:36px; border-radius:10px; font-size:1em;
        cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.2s;
    }}
    .menu-btn:hover {{ border-color:var(--gold); box-shadow:0 0 12px rgba(201,168,76,0.2); }}
    .header-title {{ font-family:'DM Sans',sans-serif; font-size:1em; font-weight:700; color:var(--text); }}
    .theme-toggle {{
        position:absolute; right:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border);
        border-radius:8px; width:34px; height:34px;
        display:flex; align-items:center; justify-content:center;
        cursor:pointer; font-size:1em; transition:all 0.2s;
    }}
    .theme-toggle:hover {{ border-color:var(--gold); }}
    .nav-dropdown {{
        position:absolute; top:calc(100% + 6px); left:10px;
        background:var(--surface2); border:1px solid var(--border);
        border-radius:var(--radius-lg); display:none; z-index:1000;
        width:270px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.7);
    }}
    .nav-dropdown a {{
        display:flex; align-items:center; gap:10px; padding:10px 16px;
        text-decoration:none; color:var(--text-mid); border-bottom:1px solid var(--border);
        font-size:0.87em; transition:all 0.15s;
    }}
    .nav-dropdown a:last-child {{ border-bottom:none; }}
    .nav-dropdown a:hover {{ background:var(--surface3); color:var(--text); padding-left:22px; }}
    .nav-group-btn {{ display:flex; justify-content:space-between; align-items:center; width:100%;
        padding:8px 16px; background:none; border:none; font-family:inherit; color:var(--gold);
        font-size:0.7em; font-weight:700; letter-spacing:1px; text-transform:uppercase; cursor:pointer; opacity:0.85; }}
    .nav-group-btn:hover {{ opacity:1; background:var(--surface3); }}
    .nav-arrow {{ font-size:0.85em; transition:transform 0.15s; }}
    .nav-group-items {{ display:none; flex-direction:column; }}
    .nav-group-items.open {{ display:flex; }}
    main {{ padding:14px; max-width:480px; margin:0 auto; animation:fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .sec-card {{
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); margin-bottom:8px; position:relative;
    }}
    .sec-card::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        border-radius:var(--radius-lg) var(--radius-lg) 0 0; z-index:1;
    }}
    .sec-card.add::before {{ background:linear-gradient(90deg, transparent, var(--green), transparent); }}
    .sec-card.edit::before {{ background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent); }}
    .sec-card.del::before {{ background:linear-gradient(90deg, transparent, var(--red), transparent); }}
    details summary {{
        list-style:none; cursor:pointer; padding:15px 18px;
        display:flex; align-items:center; gap:10px;
        font-family:'DM Sans',sans-serif; font-size:0.92em; font-weight:700;
        border-radius:var(--radius-lg); transition:background 0.15s; user-select:none;
    }}
    details[open] summary {{ border-radius:var(--radius-lg) var(--radius-lg) 0 0; }}
    details summary::-webkit-details-marker {{ display:none; }}
    details summary:hover {{ background:var(--surface2); }}
    .sum-arrow {{ font-size:0.7em; color:var(--text-dim); margin-left:auto; transition:transform 0.22s; }}
    details[open] .sum-arrow {{ transform:rotate(90deg); }}
    .sum-add {{ color:var(--green); }}
    .sum-edit {{ color:var(--gold); }}
    .sum-del {{ color:var(--red); }}
    .form-body {{ padding:4px 18px 20px; border-top:1px solid var(--border); }}
    .form-group {{ margin-top:13px; }}
    label {{
        display:block; font-size:0.65em; font-weight:700; color:var(--text-dim);
        letter-spacing:1.8px; text-transform:uppercase; margin-bottom:6px;
    }}
    input[type="text"], select {{
        width:100%; padding:10px 13px; background:var(--surface2);
        border:1px solid var(--border); border-radius:9px; color:var(--text);
        font-family:'DM Sans',sans-serif; font-size:0.92em;
        transition:all 0.2s; outline:none; -webkit-appearance:none; appearance:none;
    }}
    input[type="text"]:focus, select:focus {{
        border-color:var(--border-active); background:var(--surface3);
        box-shadow:0 0 0 3px rgba(99,160,240,0.07);
    }}
    input::placeholder {{ color:var(--text-dim); }}
    select {{
        background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='7' viewBox='0 0 12 7'%3E%3Cpath fill='none' stroke='%23555' stroke-width='1.5' d='M1 1l5 5 5-5'/%3E%3C/svg%3E");
        background-repeat:no-repeat; background-position:right 12px center;
        padding-right:32px; cursor:pointer;
    }}
    select option {{ background:var(--surface2); color:var(--text); }}
    .btn-submit {{
        width:100%; padding:12px 13px; margin-top:16px; border:none; border-radius:9px;
        font-family:'DM Sans',sans-serif; font-size:0.92em; font-weight:700;
        line-height:1.5; cursor:pointer; transition:all 0.2s;
    }}
    .btn-submit:hover {{ transform:translateY(-1px); }}
    .btn-add {{ background:linear-gradient(135deg, var(--green), #2d7a56); color:#000; }}
    .btn-add:hover {{ box-shadow:0 6px 20px rgba(76,175,130,0.25); }}
    .btn-edit {{ background:linear-gradient(135deg, var(--gold), #8a6820); color:#000; }}
    .btn-edit:hover {{ box-shadow:0 6px 20px rgba(201,168,76,0.25); }}
    .btn-del {{ background:linear-gradient(135deg, var(--red), #9c2d2d); color:#fff; }}
    .btn-del:hover {{ box-shadow:0 6px 20px rgba(224,90,90,0.25); }}
    .btn-home {{
        display:block; text-align:center; padding:12px 13px; margin-top:10px;
        background:var(--surface); border:1px solid var(--border);
        color:var(--text-mid); border-radius:9px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.88em;
        line-height:1.5; transition:all 0.2s;
    }}
    .btn-home:hover {{ border-color:var(--border-active); color:var(--text); }}
</style>
<script>
    const CategorieTipi = {categorie_tipi_js};
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if (btn) btn.textContent = '🌙'; }}
        else               {{ root.classList.remove('light'); if (btn) btn.textContent = '☀️'; }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        applyTheme(next);
    }}
    function toggleNavGroup(btn, ev) {{
        if (ev) ev.stopPropagation();
        const items = btn.nextElementSibling;
        const giaAperto = items.classList.contains('open');
        btn.closest('.nav-dropdown').querySelectorAll('.nav-group-items.open').forEach(function(el) {{
            el.classList.remove('open');
            el.previousElementSibling.querySelector('.nav-arrow').textContent = '▶';
        }});
        if (!giaAperto) {{
            items.classList.add('open');
            btn.querySelector('.nav-arrow').textContent = '▼';
        }}
    }}
    function toggleMenu() {{
        const m = document.getElementById("extraMenu");
        m.style.display = m.style.display === "block" ? "none" : "block";
    }}
    function aggiornaTipoCategoria() {{
        const sel = document.getElementById("categoria_modifica");
        const tipo = document.getElementById("nuovo_tipo");
        tipo.value = (sel.value && CategorieTipi[sel.value]) ? CategorieTipi[sel.value] : "Uscita";
        const opt = sel.options[sel.selectedIndex];
        const budgetField = document.getElementById("budget_modifica");
        if (budgetField && opt) {{
            const b = parseFloat(opt.getAttribute("data-budget")) || 0;
            budgetField.value = b > 0 ? b.toFixed(2) : "";
        }}
        const budgetAnnoField = document.getElementById("budget_annuo_modifica");
        if (budgetAnnoField && opt) {{
            const ba = parseFloat(opt.getAttribute("data-budget-annuo")) || 0;
            budgetAnnoField.value = ba > 0 ? ba.toFixed(2) : "";
        }}
    }}
    document.addEventListener("DOMContentLoaded", function() {{
        applyTheme(localStorage.getItem('theme') || 'dark');
        const cm = document.getElementById("categoria_modifica");
        if (cm) {{
            cm.addEventListener("change", aggiornaTipoCategoria);
            if (cm.value) aggiornaTipoCategoria();
        }}
    }});
    document.addEventListener("click", function(e) {{
        const menu = document.getElementById("extraMenu");
        const btn = document.querySelector(".menu-btn");
        if (menu && menu.style.display === "block" && !menu.contains(e.target) && e.target !== btn)
            menu.style.display = "none";
    }});
</script>
</head>
<body>
<header>
    <button class="menu-btn" onclick="toggleMenu()">⚙️</button>
    <div id="extraMenu" class="nav-dropdown">
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Finanze</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/">🏠 Aggiungi Operazione</a>
                <a href="/lista">📈 Gestione Movimenti Mese</a>
                <a href="/stats">📊 Bilancio Mese</a>
                <a href="/fondo_risparmio_web">💰 Fondo Risparmio</a>
                <a href="/scadenze_web">📅 Scadenze del Mese</a>
                <a href="/fairshare_web">⚖️ FairShare</a>
                <a href="/menu_esplora">🔍 Esplora</a>
                <a href="/grafici_web">📅 Grafici e Statistiche</a>
                <a href="/gestione_categorie">⚙️ Gestione Categorie</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Casa</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/utenze?anno={anno_corrente}">💧 Utenze</a>
                <a href="/consultazione_supermercati">🛒 Gestione Supermercati</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Documenti</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/documenti_pdf_web">🗄️ Documenti Contabili</a>
                <a href="/documenti_personali_web">🗄️ Documenti Personali</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Sistema</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/info_sys_web">📡 Monitor Server</a>
                <a href="/cambia_pw_web">🔑 Cambia Password</a>
                <a href="/webauthn_web">👆 Biometrico</a>
                <a href="/cambia_profilo_web">👤 Cambia Profilo</a>
                <a href="/logoff">🔓 Logout</a>
            </div>
        </div>
    </div>
    <div class="header-title">⚙️ Gestione Categorie</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="sec-card add">
        <details>
            <summary>
                <span class="sum-add">➕</span>
                <span class="sum-add">Aggiungi Categoria</span>
                <span class="sum-arrow">▶</span>
            </summary>
            <div class="form-body">
                <form action="/salva_categoria" method="POST">
                    <input type="hidden" name="operazione" value="aggiungi">
                    <div class="form-group">
                        <label>Nome Categoria</label>
                        <input type="text" name="nome_categoria" required placeholder="es: Abbonamenti">
                    </div>
                    <div class="form-group">
                        <label>Tipo</label>
                        <select name="tipo_categoria">
                            <option value="Uscita">Uscita</option>
                            <option value="Entrata">Entrata</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Budget €/mese (opzionale)</label>
                        <input type="text" name="budget_categoria" placeholder="es: 500.00" inputmode="decimal">
                    </div>
                    <div class="form-group">
                        <label>Budget €/anno (opzionale)</label>
                        <input type="text" name="budget_annuale_categoria" placeholder="es: 6000.00" inputmode="decimal">
                    </div>
                    <button type="submit" class="btn-submit btn-add">➕ Aggiungi</button>
                </form>
            </div>
        </details>
    </div>
    <div class="sec-card edit">
        <details>
            <summary>
                <span class="sum-edit">✏️</span>
                <span class="sum-edit">Modifica Categoria</span>
                <span class="sum-arrow">▶</span>
            </summary>
            <div class="form-body">
                <form action="/salva_categoria" method="POST">
                    <input type="hidden" name="operazione" value="modifica">
                    <div class="form-group">
                        <label>Seleziona Categoria</label>
                        <select name="categoria_selezionata" id="categoria_modifica" required>
                            {categorie_options}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Nuovo Nome (opzionale)</label>
                        <input type="text" name="nuovo_nome" placeholder="Lascia vuoto per non modificare">
                    </div>
                    <div class="form-group">
                        <label>Nuovo Tipo</label>
                        <select name="nuovo_tipo" id="nuovo_tipo">
                            <option value="Uscita">Uscita</option>
                            <option value="Entrata">Entrata</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Budget €/mese (0 per rimuovere)</label>
                        <input type="text" name="budget_categoria" id="budget_modifica" placeholder="es: 500.00" inputmode="decimal">
                    </div>
                    <div class="form-group">
                        <label>Budget €/anno (0 per rimuovere)</label>
                        <input type="text" name="budget_annuale_categoria" id="budget_annuo_modifica" placeholder="es: 6000.00" inputmode="decimal">
                    </div>
                    <button type="submit" class="btn-submit btn-edit">✏️ Modifica</button>
                </form>
            </div>
        </details>
    </div>
    <div class="sec-card del">
        <details>
            <summary>
                <span class="sum-del">❌</span>
                <span class="sum-del">Cancella Categoria</span>
                <span class="sum-arrow">▶</span>
            </summary>
            <div class="form-body">
                <form action="/cancella_categoria" method="POST">
                    <div class="form-group">
                        <label>Seleziona Categoria da eliminare</label>
                        <select name="categoria_selezionata" required>
                            {categorie_options}
                        </select>
                    </div>
                    <button type="submit" class="btn-submit btn-del">❌ Cancella</button>
                </form>
            </div>
        </details>
    </div>
    <a href="/" class="btn-home">🏠 Torna alla Home</a>
</main>
</body>
</html>"""

# Html Genera la pagina web del Fondo Risparmio (proiezione, obiettivi, emergenza, trend)
def pagina_fondo_risparmio_web(self):
    import __main__ as _app
    FR_FILE = _app.FR_FILE
    oggi = datetime.date.today()
    anno_corrente = oggi.year
    oggi_formattata = oggi.strftime('%d/%m/%Y')
    MESI_BREVI  = ["Gen","Feb","Mar","Apr","Mag","Giu",
                   "Lug","Ago","Set","Ott","Nov","Dic"]
    MESI_ESTESI = ["Gennaio","Febbraio","Marzo","Aprile","Maggio","Giugno",
                   "Luglio","Agosto","Settembre","Ottobre","Novembre","Dicembre"]
    try:
        if os.path.exists(FR_FILE):
            with open(FR_FILE, "r", encoding="utf-8") as _f:
                fr_dati = json.load(_f)
        else:
            fr_dati = {"obiettivo_annuale": 0.0, "fondo_attuale": 0.0, "obiettivi": []}
    except Exception:
        fr_dati = {"obiettivo_annuale": 0.0, "fondo_attuale": 0.0, "obiettivi": []}
    obiettivo_annuale = fr_dati.get("obiettivo_annuale", 0.0)
    fondo_attuale     = fr_dati.get("fondo_attuale", 0.0)
    obiettivi         = fr_dati.get("obiettivi", [])
    def fmt(v):
        return f"€ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")
    def fmts(v):
        return f"{v:,.2f}".replace(",","X").replace(".",",").replace("X",".")
    inizio_365 = oggi - datetime.timedelta(days=364)
    entrate_tot = 0.0
    uscite_tot  = 0.0
    mesi_dati   = {}
    for d, sp in self.spese.items():
        if inizio_365 <= d <= oggi:
            for entry in sp:
                cat, desc, imp, tipo = entry[:4]
                key = (d.year, d.month)
                if key not in mesi_dati:
                    mesi_dati[key] = {"e": 0.0, "u": 0.0}
                if tipo == "Entrata":
                    entrate_tot        += imp
                    mesi_dati[key]["e"] += imp
                else:
                    uscite_tot         += imp
                    mesi_dati[key]["u"] += imp
    n_mesi  = len(mesi_dati) if mesi_dati else 1
    media_e = entrate_tot / n_mesi
    media_u = uscite_tot  / n_mesi
    media_r = (entrate_tot - uscite_tot) / n_mesi
    risparmio_365 = entrate_tot - uscite_tot
    anno_prec = anno_corrente - 1
    mesi_reali = {}
    for (y, m), v in mesi_dati.items():
        if y == anno_corrente:
            mesi_reali[m] = v
    mesi_anno_prec = {}
    for d, sp in self.spese.items():
        if d.year == anno_prec:
            key = d.month
            if key not in mesi_anno_prec:
                mesi_anno_prec[key] = {"e": 0.0, "u": 0.0}
            for entry in sp:
                imp, tipo = entry[2], entry[3]
                if tipo == "Entrata":
                    mesi_anno_prec[key]["e"] += imp
                else:
                    mesi_anno_prec[key]["u"] += imp
    proj = []
    e_proj = 0.0; u_proj = 0.0
    for m in range(1, 13):
        if m in mesi_reali:
            e, u, futuro = mesi_reali[m]["e"], mesi_reali[m]["u"], False
        else:
            if m in mesi_anno_prec:
                e = mesi_anno_prec[m]["e"]
                u = mesi_anno_prec[m]["u"]
            else:
                e, u = media_e, media_u
            futuro = True
        proj.append({"m": m, "e": e, "u": u, "r": e - u, "futuro": futuro})
        e_proj += e; u_proj += u
    r_proj = e_proj - u_proj
    dati_12 = []
    for i in range(11, -1, -1):
        total = oggi.year * 12 + oggi.month - 1 - i
        y = total // 12; m = total % 12 + 1
        e12 = 0.0; u12 = 0.0
        for d, sp in self.spese.items():
            if d.year == y and d.month == m:
                for entry in sp:
                    imp, tipo = entry[2], entry[3]
                    if tipo == "Entrata": e12 += imp
                    else: u12 += imp
        dati_12.append({"y": y, "m": m, "e": e12, "u": u12, "r": e12 - u12})
    best  = max(dati_12, key=lambda x: x["r"], default={"m":1,"y":oggi.year,"r":0})
    worst = min(dati_12, key=lambda x: x["r"], default={"m":1,"y":oggi.year,"r":0})
    spesa_mm = media_u
    fe3  = spesa_mm * 3
    fe6  = spesa_mm * 6
    fe12 = spesa_mm * 12
    pct3  = max(0.0, min(fondo_attuale / fe3,  1.0)) if fe3  > 0 else 0.0
    pct6  = max(0.0, min(fondo_attuale / fe6,  1.0)) if fe6  > 0 else 0.0
    pct12 = max(0.0, min(fondo_attuale / fe12, 1.0)) if fe12 > 0 else 0.0
    def bar_col(pct):
        if pct >= 1.0:  return "var(--green)"
        if pct >= 0.5:  return "var(--orange)"
        return "var(--red)"
    rata_mensile = obiettivo_annuale / 12 if obiettivo_annuale > 0 else 0.0
    diff_obj = media_r - rata_mensile
    pct_obj  = max(0.0, min(risparmio_365 / obiettivo_annuale, 1.0)) if obiettivo_annuale > 0 else 0.0
    proj_rows = ""
    for p in proj:
        futuro_cls = " futuro" if p["futuro"] else ""
        segno = "+" if p["r"] >= 0 else ""
        col_r = "var(--green)" if p["r"] >= 0 else "var(--red)"
        proj_rows += (
            f"<tr class='pr-row{futuro_cls}'>"
            f"<td>{MESI_BREVI[p['m']-1]}</td>"
            f"<td class='num'>{fmts(p['e'])}</td>"
            f"<td class='num'>{fmts(p['u'])}</td>"
            f"<td class='num' style='color:{col_r}'>{segno}{fmts(p['r'])}</td>"
            f"<td class='futuro-badge'>{'📊 stimato' if p['futuro'] else '✓ reale'}</td>"
            f"</tr>"
        )
    trend_rows = ""
    prev_r = None
    for row in dati_12:
        if prev_r is None:
            delta_s = "—"
        elif row["r"] >= prev_r:
            delta_s = f"▲ +{fmts(row['r'] - prev_r)}"
        else:
            delta_s = f"▼ {fmts(row['r'] - prev_r)}"
        col_r = "var(--green)" if row["r"] >= 0 else "var(--red)"
        trend_rows += (
            f"<tr>"
            f"<td>{MESI_ESTESI[row['m']-1]} {row['y']}</td>"
            f"<td class='num'>{fmts(row['e'])}</td>"
            f"<td class='num'>{fmts(row['u'])}</td>"
            f"<td class='num' style='color:{col_r}'>{fmts(row['r'])}</td>"
            f"<td class='num'>{delta_s}</td>"
            f"</tr>"
        )
        prev_r = row["r"]
    obj_rows = ""
    for i, ob in enumerate(obiettivi):
        rata  = ob["importo"] / ob["mesi"] if ob.get("mesi", 0) > 0 else ob["importo"]
        ok    = media_r >= rata
        mesi_r = int(ob["importo"] / media_r) if media_r > 0 else 9999
        col_ok = "var(--green)" if ok else "var(--red)"
        obj_rows += (
            f"<tr>"
            f"<td>{html.escape(ob['nome'])}</td>"
            f"<td class='num'>{fmts(ob['importo'])}</td>"
            f"<td>{ob.get('data','—')}</td>"
            f"<td class='num'>{ob.get('mesi','—')}</td>"
            f"<td class='num'>{fmts(rata)}</td>"
            f"<td style='color:{col_ok}'>{'Sì' if ok else 'No'}</td>"
            f"<td class='num'>{'N/D' if media_r <= 0 else f'{mesi_r} mesi'}</td>"
            f"<td><form method='post' action='/fondo_risparmio_web' style='margin:0'>"
            f"<input type='hidden' name='action' value='elimina_obiettivo'>"
            f"<input type='hidden' name='idx' value='{i}'>"
            f"<button class='btn-del' type='submit' title='Elimina'>✕</button>"
            f"</form></td>"
            f"</tr>"
        )
    if not obj_rows:
        obj_rows = "<tr><td colspan='8' style='text-align:center;color:var(--text-dim);padding:18px'>Nessun obiettivo impostato</td></tr>"
    valori_12 = [r["r"] for r in dati_12]
    max_v12   = max(abs(v) for v in valori_12) or 1.0
    sw, sh    = 560, 90
    pad_s     = 24
    step_s    = (sw - 2 * pad_s) / max(len(valori_12) - 1, 1)
    y_zero_s  = sh // 2
    spark_lines = ""
    spark_pts   = ""
    spark_lbls  = ""
    pts_s = []
    for i, v in enumerate(valori_12):
        x = pad_s + i * step_s
        y = y_zero_s - (v / max_v12) * (y_zero_s - 10)
        pts_s.append((x, y))
    for i in range(len(pts_s) - 1):
        col = "#4caf82" if valori_12[i] >= 0 else "#e05a5a"
        spark_lines += f"<line x1='{pts_s[i][0]:.1f}' y1='{pts_s[i][1]:.1f}' x2='{pts_s[i+1][0]:.1f}' y2='{pts_s[i+1][1]:.1f}' stroke='{col}' stroke-width='2'/>"
    for i, (x, y) in enumerate(pts_s):
        col = "#4caf82" if valori_12[i] >= 0 else "#e05a5a"
        spark_pts  += f"<circle cx='{x:.1f}' cy='{y:.1f}' r='4' fill='{col}'/>"
        spark_lbls += f"<text x='{x:.1f}' y='{sh - 4}' text-anchor='middle' font-size='9' fill='#888'>{MESI_BREVI[dati_12[i]['m']-1]}</text>"
    col_r_proj = "var(--green)" if r_proj >= 0 else "var(--red)"
    col_r_365  = "var(--green)" if risparmio_365 >= 0 else "var(--red)"
    col_media  = "var(--green)" if media_r >= 0 else "var(--red)"
    col_diff   = "var(--green)" if diff_obj >= 0 else "var(--red)"
    diff_testo = (f"Sei in linea (+{fmt(diff_obj)}/mese)" if diff_obj >= 0
                  else f"Mancano {fmt(abs(diff_obj))}/mese")
    nav_anno = anno_corrente
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>💰 Fondo Risparmio {oggi_formattata}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
    (function() {{
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    }})();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg:#050505; --surface:#0f0f0f; --surface2:#161616; --surface3:#1e1e1e;
        --border:rgba(255,255,255,0.07); --gold:#c9a84c; --blue:#63a0f0;
        --green:#4caf82; --red:#e05a5a; --orange:#e09a3a;
        --text:#e8e8e8; --text-dim:#555; --text-mid:#888; --radius-lg:18px;
    }}
    :root.light {{
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --gold:#b8902a; --blue:#3d7fd4;
        --green:#3a9068; --red:#cc3333; --orange:#c07820;
        --text:#1a1a1a; --text-dim:#999; --text-mid:#555;
    }}
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{
        font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text);
        min-height:100vh; padding-bottom:60px; transition:background 0.3s,color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 40% at 50% -10%, rgba(99,160,240,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 60%);
    }}
    header {{
        padding:14px 16px 12px; display:flex; align-items:center; justify-content:center;
        border-bottom:1px solid var(--border); background:rgba(5,5,5,0.95);
        backdrop-filter:blur(20px); position:sticky; top:0; z-index:100;
    }}
    :root.light header {{ background:rgba(245,245,240,0.95); }}
    .menu-btn {{
        position:absolute; left:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border); color:var(--gold);
        width:36px; height:36px; border-radius:10px; font-size:1em;
        cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.2s;
    }}
    .menu-btn:hover {{ border-color:var(--gold); box-shadow:0 0 12px rgba(201,168,76,0.2); }}
    .header-title {{ font-size:1em; font-weight:700; color:var(--text); }}
    .theme-toggle {{
        position:absolute; right:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border);
        border-radius:8px; width:34px; height:34px;
        display:flex; align-items:center; justify-content:center;
        cursor:pointer; font-size:1em; transition:all 0.2s;
    }}
    .theme-toggle:hover {{ border-color:var(--gold); }}
    .nav-dropdown {{
        position:absolute; top:calc(100% + 6px); left:10px;
        background:var(--surface2); border:1px solid var(--border);
        border-radius:var(--radius-lg); display:none; z-index:1000;
        width:270px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.7);
    }}
    .nav-dropdown a {{
        display:flex; align-items:center; gap:10px; padding:10px 16px;
        text-decoration:none; color:var(--text-mid); border-bottom:1px solid var(--border);
        font-size:0.87em; transition:all 0.15s;
    }}
    .nav-dropdown a:last-child {{ border-bottom:none; }}
    .nav-dropdown a:hover {{ background:var(--surface3); color:var(--text); padding-left:22px; }}
    .nav-group-btn {{ display:flex; justify-content:space-between; align-items:center; width:100%;
        padding:8px 16px; background:none; border:none; font-family:inherit; color:var(--gold);
        font-size:0.7em; font-weight:700; letter-spacing:1px; text-transform:uppercase; cursor:pointer; opacity:0.85; }}
    .nav-group-btn:hover {{ opacity:1; background:var(--surface3); }}
    .nav-arrow {{ font-size:0.85em; transition:transform 0.15s; }}
    .nav-group-items {{ display:none; flex-direction:column; }}
    .nav-group-items.open {{ display:flex; }}
    main {{ padding:14px; max-width:860px; margin:0 auto; animation:fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .tabs {{ display:flex; gap:6px; margin-bottom:14px; flex-wrap:wrap; }}
    .tab-btn {{
        padding:8px 18px; border-radius:10px; border:1px solid var(--border);
        background:var(--surface3); color:var(--text-mid); cursor:pointer;
        font-family:'DM Sans',sans-serif; font-size:0.85em; font-weight:600;
        transition:all 0.18s;
    }}
    .tab-btn.active, .tab-btn:hover {{
        background:var(--gold); color:#000; border-color:var(--gold);
    }}
    .tab-panel {{ display:none; }}
    .tab-panel.active {{ display:block; }}
    .card {{
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); padding:18px 16px; margin-bottom:14px;
        position:relative; overflow:hidden;
    }}
    .card::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .card-title {{
        font-size:0.8em; font-weight:700; color:var(--text-mid);
        text-transform:uppercase; letter-spacing:0.05em; margin-bottom:12px;
    }}
    .kpi-grid {{ display:grid; grid-template-columns:repeat(3, 1fr); gap:10px; }}
    .kpi {{
        background:var(--surface2); border:1px solid var(--border);
        border-radius:12px; padding:12px 10px; text-align:center;
    }}
    .kpi-label {{ font-size:0.72em; color:var(--text-dim); margin-bottom:4px; }}
    .kpi-value {{ font-size:1.05em; font-weight:700; }}
    .tbl-wrap {{ overflow-x:auto; }}
    table {{ width:100%; border-collapse:collapse; font-size:0.83em; }}
    th {{
        padding:8px 10px; text-align:left; border-bottom:1px solid var(--border);
        color:var(--text-dim); font-weight:600; font-size:0.78em; text-transform:uppercase;
    }}
    td {{ padding:7px 10px; border-bottom:1px solid var(--border); color:var(--text-mid); }}
    tr:last-child td {{ border-bottom:none; }}
    tr:hover td {{ background:var(--surface2); color:var(--text); }}
    td.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
    tr.futuro td {{ opacity:0.6; }}
    .futuro-badge {{ font-size:0.75em; color:var(--text-dim); }}
    .prog-wrap {{ background:var(--surface3); border-radius:8px; height:14px; overflow:hidden; margin-bottom:4px; }}
    .prog-fill {{ height:100%; border-radius:8px; transition:width 0.6s ease; }}
    .prog-label {{ font-size:0.75em; color:var(--text-mid); margin-bottom:10px; }}
    .form-row {{ display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-top:10px; }}
    .form-row input[type=text], .form-row input[type=number] {{
        background:var(--surface3); border:1px solid var(--border); color:var(--text);
        padding:7px 10px; border-radius:8px; font-family:'DM Sans',sans-serif; font-size:0.85em;
        width:120px;
    }}
    .form-row input:focus {{ outline:none; border-color:var(--gold); }}
    .btn-save {{
        padding:7px 18px; border-radius:8px; border:none; cursor:pointer;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.85em;
        transition:all 0.2s;
    }}
    .btn-save:hover {{ transform:translateY(-1px); box-shadow:0 4px 14px rgba(201,168,76,0.3); }}
    .btn-del {{
        background:none; border:1px solid var(--red); color:var(--red);
        border-radius:6px; padding:3px 8px; cursor:pointer; font-size:0.8em; transition:all 0.15s;
    }}
    .btn-del:hover {{ background:var(--red); color:#fff; }}
    .hint {{ font-size:0.78em; color:var(--text-dim); margin-top:6px; }}
    .badge-best {{ color:var(--green); font-weight:700; }}
    .badge-worst {{ color:var(--red); font-weight:700; }}
    svg.spark {{ width:100%; height:90px; }}
</style>
<script>
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if (btn) btn.textContent = '🌙'; }}
        else               {{ root.classList.remove('light'); if (btn) btn.textContent = '☀️'; }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        applyTheme(next);
    }}
    function toggleNavGroup(btn, ev) {{
        if (ev) ev.stopPropagation();
        const items = btn.nextElementSibling;
        const giaAperto = items.classList.contains('open');
        btn.closest('.nav-dropdown').querySelectorAll('.nav-group-items.open').forEach(function(el) {{
            el.classList.remove('open');
            el.previousElementSibling.querySelector('.nav-arrow').textContent = '▶';
        }});
        if (!giaAperto) {{
            items.classList.add('open');
            btn.querySelector('.nav-arrow').textContent = '▼';
        }}
    }}
    function toggleMenu() {{
        const m = document.getElementById("extraMenu");
        m.style.display = m.style.display === "block" ? "none" : "block";
    }}
    function showTab(id) {{
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.getElementById(id).classList.add('active');
        document.querySelector('[data-tab="' + id + '"]').classList.add('active');
        localStorage.setItem('fr_tab', id);
    }}
    document.addEventListener("DOMContentLoaded", function() {{
        applyTheme(localStorage.getItem('theme') || 'dark');
        const saved = localStorage.getItem('fr_tab') || 'tab-proiezione';
        showTab(saved);
    }});
    document.addEventListener("click", function(e) {{
        const menu = document.getElementById("extraMenu");
        const btn = document.querySelector(".menu-btn");
        if (menu && menu.style.display === "block" && !menu.contains(e.target) && e.target !== btn)
            menu.style.display = "none";
    }});
</script>
</head>
<body>
<header>
<button class="menu-btn" onclick="toggleMenu()">⚙️</button>
<div id="extraMenu" class="nav-dropdown">
    <div class="nav-group">
        <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Finanze</span><span class="nav-arrow">▶</span></button>
        <div class="nav-group-items">
            <a href="/">🏠 Aggiungi Operazione</a>
            <a href="/lista">📈 Gestione Movimenti Mese</a>
            <a href="/stats">📊 Bilancio Mese</a>
            <a href="/fondo_risparmio_web">💰 Fondo Risparmio</a>
            <a href="/scadenze_web">📅 Scadenze del Mese</a>
            <a href="/fairshare_web">⚖️ FairShare</a>
            <a href="/menu_esplora">🔍 Esplora</a>
            <a href="/grafici_web">📅 Grafici e Statistiche</a>
            <a href="/gestione_categorie">⚙️ Gestione Categorie</a>
        </div>
    </div>
    <div class="nav-group">
        <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Casa</span><span class="nav-arrow">▶</span></button>
        <div class="nav-group-items">
            <a href="/utenze?anno={nav_anno}">💧 Utenze</a>
            <a href="/consultazione_supermercati">🛒 Gestione Supermercati</a>
        </div>
    </div>
    <div class="nav-group">
        <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Documenti</span><span class="nav-arrow">▶</span></button>
        <div class="nav-group-items">
            <a href="/documenti_pdf_web">🗄️ Documenti Contabili</a>
            <a href="/documenti_personali_web">🗄️ Documenti Personali</a>
        </div>
    </div>
    <div class="nav-group">
        <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Sistema</span><span class="nav-arrow">▶</span></button>
        <div class="nav-group-items">
            <a href="/info_sys_web">📡 Monitor Server</a>
            <a href="/cambia_pw_web">🔑 Cambia Password</a>
            <a href="/webauthn_web">👆 Biometrico</a>
            <a href="/cambia_profilo_web">👤 Cambia Profilo</a>
            <a href="/logoff">🔓 Logout</a>
        </div>
    </div>
</div>
<div class="header-title">💰 Fondo Risparmio {oggi_formattata}</div>
<button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
<div class="tabs">
    <button class="tab-btn" data-tab="tab-proiezione" onclick="showTab('tab-proiezione')">📊 Proiezione {anno_corrente}</button>
    <button class="tab-btn" data-tab="tab-mensile"   onclick="showTab('tab-mensile')">📅 Fondo Mensile</button>
    <button class="tab-btn" data-tab="tab-obiettivi" onclick="showTab('tab-obiettivi')">🎯 Obiettivi</button>
    <button class="tab-btn" data-tab="tab-trend"     onclick="showTab('tab-trend')">📈 Trend 12 Mesi</button>
    <button class="tab-btn" data-tab="tab-emergenza" onclick="showTab('tab-emergenza')">🛡 Fondo Emergenza</button>
</div>
<!-- TAB PROIEZIONE -->
<div id="tab-proiezione" class="tab-panel">
    <div class="card">
        <div class="card-title">Ultimi 365 giorni</div>
        <div class="kpi-grid">
            <div class="kpi"><div class="kpi-label">Entrate</div><div class="kpi-value">{fmt(entrate_tot)}</div></div>
            <div class="kpi"><div class="kpi-label">Uscite</div><div class="kpi-value">{fmt(uscite_tot)}</div></div>
            <div class="kpi"><div class="kpi-label">Risparmio</div><div class="kpi-value" style="color:{col_r_365}">{fmt(risparmio_365)}</div></div>
            <div class="kpi"><div class="kpi-label">Media Entrate/mese</div><div class="kpi-value">{fmt(media_e)}</div></div>
            <div class="kpi"><div class="kpi-label">Media Uscite/mese</div><div class="kpi-value">{fmt(media_u)}</div></div>
            <div class="kpi"><div class="kpi-label">Media Risparmio/mese</div><div class="kpi-value" style="color:{col_media}">{fmt(media_r)}</div></div>
        </div>
    </div>
    <div class="card">
        <div class="card-title">Proiezione {anno_corrente} — Entrate stimate {fmt(e_proj)} · Uscite stimate {fmt(u_proj)} · Risparmio atteso <span style="color:{col_r_proj}">{fmt(r_proj)}</span></div>
        <p class="hint">I mesi con sfondo attenuato (📊 stimato) usano dati dell'anno precedente o la media degli ultimi 365 giorni.</p>
        <div class="tbl-wrap" style="margin-top:12px">
            <table>
                <thead><tr><th>Mese</th><th>Entrate</th><th>Uscite</th><th>Risparmio</th><th>Fonte</th></tr></thead>
                <tbody>{proj_rows}</tbody>
            </table>
        </div>
    </div>
</div>
<!-- TAB FONDO MENSILE -->
<div id="tab-mensile" class="tab-panel">
    <div class="card">
        <div class="card-title">Medie mensili ({n_mesi} mesi analizzati)</div>
        <div class="kpi-grid">
            <div class="kpi"><div class="kpi-label">Media Entrate/mese</div><div class="kpi-value">{fmt(media_e)}</div></div>
            <div class="kpi"><div class="kpi-label">Media Uscite/mese</div><div class="kpi-value">{fmt(media_u)}</div></div>
            <div class="kpi"><div class="kpi-label">Risparmio Medio/mese</div><div class="kpi-value" style="color:{col_media}">{fmt(media_r)}</div></div>
        </div>
    </div>
    <div class="card">
        <div class="card-title">Obiettivo Risparmio Annuale</div>
        <form method="post" action="/fondo_risparmio_web">
            <input type="hidden" name="action" value="salva_obiettivo">
            <div class="form-row">
                <span style="font-size:0.85em">Obiettivo annuale (€):</span>
                <input type="number" name="obiettivo_annuale" value="{int(obiettivo_annuale)}" min="0" step="100">
                <button class="btn-save" type="submit">Salva</button>
            </div>
        </form>
        <div style="margin-top:14px">
            <div class="prog-wrap">
                <div class="prog-fill" style="width:{pct_obj*100:.1f}%;background:{bar_col(pct_obj)}"></div>
            </div>
            <div class="prog-label">Risparmio 365gg: {fmt(risparmio_365)} / Obiettivo: {fmt(obiettivo_annuale) if obiettivo_annuale > 0 else '—'} ({pct_obj*100:.1f}%)</div>
            <p style="font-size:0.83em;margin-top:6px">
                Rata mensile necessaria: <strong>{fmt(rata_mensile)}</strong> &nbsp;·&nbsp;
                <span style="color:{col_diff}">{diff_testo}</span>
            </p>
        </div>
    </div>
</div>
<!-- TAB OBIETTIVI -->
<div id="tab-obiettivi" class="tab-panel">
    <div class="card">
        <div class="card-title">➕ Nuovo Obiettivo</div>
        <form method="post" action="/fondo_risparmio_web">
            <input type="hidden" name="action" value="aggiungi_obiettivo">
            <div class="form-row">
                <input type="text"   name="nome"           placeholder="Nome"       style="width:160px">
                <input type="number" name="importo"        placeholder="Importo €"  min="0" step="0.01">
                <input type="text"   name="data_scadenza"  placeholder="MM/AAAA"    style="width:90px">
                <button class="btn-save" type="submit">Aggiungi</button>
            </div>
        </form>
        <p class="hint">Data nel formato MM/AAAA — deve essere futura</p>
    </div>
    <div class="card">
        <div class="card-title">I Tuoi Obiettivi</div>
        <p class="hint" style="margin-bottom:10px">Risparmio medio mensile attuale: <strong>{fmt(media_r)}</strong></p>
        <div class="tbl-wrap">
            <table>
                <thead><tr><th>Nome</th><th>Importo</th><th>Entro</th><th>Mesi</th><th>Rata/mese</th><th>Fattibile</th><th>Mesi realistici</th><th></th></tr></thead>
                <tbody>{obj_rows}</tbody>
            </table>
        </div>
    </div>
</div>
<!-- TAB TREND -->
<div id="tab-trend" class="tab-panel">
    <div class="card">
        <div class="card-title">Trend Risparmio — ultimi 12 mesi</div>
        <p>
            <span class="badge-best">Mese migliore: {MESI_ESTESI[best['m']-1]} {best['y']} (+{fmt(best['r'])})</span>
            &nbsp;·&nbsp;
            <span class="badge-worst">Mese peggiore: {MESI_ESTESI[worst['m']-1]} {worst['y']} ({fmt(worst['r'])})</span>
        </p>
        <svg class="spark" viewBox="0 0 {sw} {sh}" xmlns="http://www.w3.org/2000/svg" style="margin-top:10px">
            <line x1="{pad_s}" y1="{y_zero_s}" x2="{sw-pad_s}" y2="{y_zero_s}" stroke="#444" stroke-dasharray="4 2"/>
            {spark_lines}
            {spark_pts}
            {spark_lbls}
        </svg>
    </div>
    <div class="card">
        <div class="card-title">Andamento Mensile — ultimi 12 mesi</div>
        <div class="tbl-wrap">
            <table>
                <thead><tr><th>Mese</th><th>Entrate</th><th>Uscite</th><th>Saldo</th><th>Delta vs precedente</th></tr></thead>
                <tbody>{trend_rows}</tbody>
            </table>
        </div>
    </div>
</div>
<!-- TAB EMERGENZA -->
<div id="tab-emergenza" class="tab-panel">
    <div class="card">
        <div class="card-title">Calcolo Fondo Emergenza</div>
        <div class="kpi-grid">
            <div class="kpi"><div class="kpi-label">Spesa media/mese</div><div class="kpi-value">{fmt(spesa_mm)}</div></div>
            <div class="kpi"><div class="kpi-label">Consigliato 3 mesi</div><div class="kpi-value">{fmt(fe3)}</div></div>
            <div class="kpi"><div class="kpi-label">Consigliato 6 mesi</div><div class="kpi-value">{fmt(fe6)}</div></div>
            <div class="kpi"><div class="kpi-label">Consigliato 12 mesi</div><div class="kpi-value">{fmt(fe12)}</div></div>
        </div>
    </div>
    <div class="card">
        <div class="card-title">Il Tuo Fondo Attuale</div>
        <form method="post" action="/fondo_risparmio_web">
            <input type="hidden" name="action" value="salva_fondo">
            <div class="form-row">
                <span style="font-size:0.85em">Fondo emergenza attuale (€):</span>
                <input type="number" name="fondo_attuale" value="{int(fondo_attuale)}" min="0" step="100">
                <button class="btn-save" type="submit">Salva</button>
            </div>
        </form>
        <div style="margin-top:16px;display:flex;flex-direction:column;gap:10px">
            <div>
                <div class="prog-wrap">
                    <div class="prog-fill" style="width:{pct3*100:.1f}%;background:{bar_col(pct3)}"></div>
                </div>
                <div class="prog-label">Obiettivo 3 mesi: {fmt(fondo_attuale)} / {fmt(fe3)} ({pct3*100:.1f}%)</div>
            </div>
            <div>
                <div class="prog-wrap">
                    <div class="prog-fill" style="width:{pct6*100:.1f}%;background:{bar_col(pct6)}"></div>
                </div>
                <div class="prog-label">Obiettivo 6 mesi: {fmt(fondo_attuale)} / {fmt(fe6)} ({pct6*100:.1f}%)</div>
            </div>
            <div>
                <div class="prog-wrap">
                    <div class="prog-fill" style="width:{pct12*100:.1f}%;background:{bar_col(pct12)}"></div>
                </div>
                <div class="prog-label">Obiettivo 12 mesi: {fmt(fondo_attuale)} / {fmt(fe12)} ({pct12*100:.1f}%)</div>
            </div>
        </div>
        <p class="hint" style="margin-top:10px">Un fondo emergenza ideale copre almeno 3–6 mesi di spese. 12 mesi garantisce la massima sicurezza.</p>
    </div>
</div>
</main>
</body>
</html>"""

# Html Grafici Web
def get_dati_entrate_uscite_tutti_gli_anni_json(self):
    totali_annuali = {}
    for giorno, voci in self.spese.items():
        try:
            anno = giorno.year
        except AttributeError:
            continue 
        if anno not in totali_annuali:
            totali_annuali[anno] = {'Entrate': 0.0, 'Uscite': 0.0}
        for voce in voci:
            if len(voce) < 4: continue
            raw_importo = voce[2]
            tipo = voce[3] 
            try:
                importo_str = str(raw_importo).strip().replace(',', '.')
                importo = float(importo_str)
            except (TypeError, ValueError):
                continue 
            if tipo == "Entrata":
                totali_annuali[anno]['Entrate'] += importo
            elif tipo == "Uscita":
                totali_annuali[anno]['Uscite'] += importo
    anni_ordinati = sorted(totali_annuali.keys()) 
    data_entrate = [totali_annuali[anno]['Entrate'] for anno in anni_ordinati]
    data_uscite = [totali_annuali[anno]['Uscite'] for anno in anni_ordinati]
    dati_json = {
        "labels": [str(anno) for anno in anni_ordinati],
        "datasets": [
            {
                "label": "Entrate",
                "data": data_entrate,
                "backgroundColor": "rgba(40, 167, 69, 0.7)"
            },
            {
                "label": "Uscite",
                "data": data_uscite,
                "backgroundColor": "rgba(220, 53, 69, 0.7)"
            }
        ]
    }
    return json.dumps(dati_json)

def get_dati_saldo_annuale_json(self):
    saldo_per_anno = {} 
    for d, voci in self.spese.items():
        anno = d.year
        if anno not in saldo_per_anno:
            saldo_per_anno[anno] = 0.0
        for voce in voci:
            importo = float(voce[2]) 
            tipo = voce[3].strip().lower()
            if tipo == "entrata":
                saldo_per_anno[anno] += importo
            elif tipo == "uscita":
                saldo_per_anno[anno] -= importo
    anni_ordinati = sorted(saldo_per_anno.keys())
    dati_json = {
        "labels": [str(anno) for anno in anni_ordinati],
        "datasets": [{
            "label": "Saldo Netto Annuale",
            "data": [saldo_per_anno[anno] for anno in anni_ordinati],
            "backgroundColor": ["#228B22" if saldo_per_anno[anno] >= 0 else "#c43b2e" for anno in anni_ordinati]
        }]
    }
    return json.dumps(dati_json)

def get_dati_entrate_uscite_json(self):
    oggi = datetime.date.today()
    anno_corrente = oggi.year
    entrate_mensili = [0.0] * 12
    uscite_mensili = [0.0] * 12
    for data, entries in self.spese.items():
        if data.year == anno_corrente:
            mese_indice = data.month - 1  
            for entry in entries:
                importo = entry[2]
                tipo = entry[3].strip() if len(entry) > 3 else 'Uscita'
                if tipo == 'Entrata':
                    entrate_mensili[mese_indice] += importo
                else: 
                    uscite_mensili[mese_indice] += importo
    mesi = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic']
    dati = {
        'labels': mesi,
        'datasets': [
            {'label': 'Entrate (€)', 'data': entrate_mensili, 'borderColor': 'rgba(75, 192, 192, 1)', 'backgroundColor': 'rgba(75, 192, 192, 0.5)'},
            {'label': 'Uscite (€)', 'data': uscite_mensili, 'borderColor': 'rgba(255, 99, 132, 1)', 'backgroundColor': 'rgba(255, 99, 132, 0.5)'}
        ]
    }
    return json.dumps(dati)

def get_dati_saldo_json(self):
    oggi = datetime.date.today()
    anno_corrente = oggi.year
    saldo_mensile_netto = [0.0] * 12
    for data, entries in self.spese.items():
        if data.year == anno_corrente:
            mese_indice = data.month - 1
            for entry in entries:
                categoria = entry[0]
                importo = entry[2]
                tipo = entry[3].strip() if len(entry) > 3 else 'Uscita'
                
                if tipo == 'Entrata':
                    saldo_mensile_netto[mese_indice] += importo
                else:
                    saldo_mensile_netto[mese_indice] -= importo
    saldo_progressivo = []
    saldo_accumulato = 0.0
    for saldo_netto in saldo_mensile_netto:
        saldo_accumulato += saldo_netto
        saldo_progressivo.append(round(saldo_accumulato, 2))
    mesi = ['Gen', 'Feb', 'Mar', 'Apr', 'Mag', 'Giu', 'Lug', 'Ago', 'Set', 'Ott', 'Nov', 'Dic']
    dati = {
        'labels': mesi,
        'datasets': [{
            'label': 'Saldo Progressivo (€)',
            'data': saldo_progressivo,
            'fill': False,
            'borderColor': 'rgb(75, 192, 192)',
            'tension': 0.1
        }]
    }
    return json.dumps(dati)

def pagina_grafici_web(self):
    oggi = datetime.date.today()
    anno_corrente = oggi.year
    oggi_formattata = oggi.strftime('%d/%m/%Y')
    anno_corrente_format = str(anno_corrente)
    fallback_storico     = '{"labels": ["N/D"], "datasets": [{"label": "Dati non caricati", "data": [0], "backgroundColor": ["#333"]}]}'
    fallback_mensile     = '{"labels": ["N/D"], "datasets": [{"label": "Dati non caricati", "data": [0], "backgroundColor": ["#333"]}]}'
    fallback_cat         = '{"labels": ["N/D"], "datasets": [{"data": [1], "backgroundColor": ["#333"], "label": "Dati non caricati"}]}'
    fallback_saldo       = '{"labels": ["N/D"], "datasets": [{"label": "Dati non caricati", "data": [0], "borderColor": "#333"}]}'
    fallback_cat_storico = '{"labels": ["N/D"], "datasets": [{"data": [1], "backgroundColor": ["#333"], "label": "Dati non caricati"}]}'
    fallback_saldo_annuale = '{"labels": ["N/D"], "datasets": [{"label": "Dati non caricati", "data": [0], "borderColor": "#333", "backgroundColor": ["#333"]}]}'
    try:
        dati_entrate_uscite_storici = self.get_dati_entrate_uscite_tutti_gli_anni_json()
    except Exception:
        dati_entrate_uscite_storici = fallback_storico
    try:
        dati_entrate_uscite_mensili = self.get_dati_entrate_uscite_json()
    except Exception:
        dati_entrate_uscite_mensili = fallback_mensile
    try:
        dati_categorie = self.get_dati_categorie_json()
    except Exception:
        dati_categorie = fallback_cat
    try:
        dati_saldo = self.get_dati_saldo_json()
    except Exception:
        dati_saldo = fallback_saldo
    try:
        dati_categorie_storiche = self.get_dati_categorie_storiche_json()
    except Exception:
        dati_categorie_storiche = fallback_cat_storico
    try:
        dati_saldo_annuale = self.get_dati_saldo_annuale_json()
    except Exception:
        dati_saldo_annuale = fallback_saldo_annuale

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>📊 Grafici e Statistiche</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
    (function() {{
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    }})();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
    :root {{
        --bg:#050505; --surface:#0f0f0f; --surface2:#161616; --surface3:#1e1e1e;
        --border:rgba(255,255,255,0.07); --gold:#c9a84c; --blue:#63a0f0;
        --green:#4caf82; --red:#e05a5a; --text:#e8e8e8;
        --text-dim:#555; --text-mid:#888; --radius-lg:18px;
    }}
    :root.light {{
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --gold:#b8902a; --blue:#3d7fd4;
        --green:#3a9068; --red:#cc3333; --text:#1a1a1a;
        --text-dim:#999; --text-mid:#555;
    }}
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{
        font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text);
        min-height:100vh; padding-bottom:50px; transition:background 0.3s,color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 40% at 50% -10%, rgba(99,160,240,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 60%);
    }}
    header {{
        padding:14px 16px 12px; display:flex; align-items:center; justify-content:center;
        border-bottom:1px solid var(--border); background:rgba(5,5,5,0.95);
        backdrop-filter:blur(20px); position:sticky; top:0; z-index:100;
    }}
    :root.light header {{ background:rgba(245,245,240,0.95); }}
    .menu-btn {{
        position:absolute; left:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border); color:var(--gold);
        width:36px; height:36px; border-radius:10px; font-size:1em;
        cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.2s;
    }}
    .menu-btn:hover {{ border-color:var(--gold); box-shadow:0 0 12px rgba(201,168,76,0.2); }}
    .header-title {{ font-family:'DM Sans',sans-serif; font-size:1em; font-weight:700; color:var(--text); }}
    .theme-toggle {{
        position:absolute; right:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border);
        border-radius:8px; width:34px; height:34px;
        display:flex; align-items:center; justify-content:center;
        cursor:pointer; font-size:1em; transition:all 0.2s;
    }}
    .theme-toggle:hover {{ border-color:var(--gold); }}
    .nav-dropdown {{
        position:absolute; top:calc(100% + 6px); left:10px;
        background:var(--surface2); border:1px solid var(--border);
        border-radius:var(--radius-lg); display:none; z-index:1000;
        width:270px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.7);
    }}
    .nav-dropdown a {{
        display:flex; align-items:center; gap:10px; padding:10px 16px;
        text-decoration:none; color:var(--text-mid); border-bottom:1px solid var(--border);
        font-size:0.87em; transition:all 0.15s;
    }}
    .nav-dropdown a:last-child {{ border-bottom:none; }}
    .nav-dropdown a:hover {{ background:var(--surface3); color:var(--text); padding-left:22px; }}
    .nav-group-btn {{ display:flex; justify-content:space-between; align-items:center; width:100%;
        padding:8px 16px; background:none; border:none; font-family:inherit; color:var(--gold);
        font-size:0.7em; font-weight:700; letter-spacing:1px; text-transform:uppercase; cursor:pointer; opacity:0.85; }}
    .nav-group-btn:hover {{ opacity:1; background:var(--surface3); }}
    .nav-arrow {{ font-size:0.85em; transition:transform 0.15s; }}
    .nav-group-items {{ display:none; flex-direction:column; }}
    .nav-group-items.open {{ display:flex; }}
    .main-container {{ max-width:960px; margin:0 auto; padding:14px; animation:fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .tab-bar {{ display:flex; flex-wrap:wrap; gap:4px; margin-bottom:0; padding:0; }}
    .tab-btn {{
        padding:8px 14px; cursor:pointer;
        font-family:'DM Sans',sans-serif; font-size:0.75em; font-weight:700;
        color:var(--text-dim); border:1px solid var(--border);
        background:var(--surface2); border-radius:9px 9px 0 0;
        transition:all 0.15s; white-space:nowrap; line-height:1.5;
    }}
    .tab-btn:hover {{ color:var(--text-mid); background:var(--surface3); }}
    .tab-btn.active {{
        color:var(--gold); background:var(--surface);
        border-color:var(--border); border-bottom-color:var(--surface);
    }}
    .chart-frame {{
        background:var(--surface); border:1px solid var(--border);
        border-radius:0 var(--radius-lg) var(--radius-lg) var(--radius-lg);
        padding:16px; position:relative; overflow:hidden;
    }}
    .chart-frame::before {{
        content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .chart-container {{
        position:relative; width:100%;
        height:58vh; min-height:320px; max-height:520px;
    }}
    .chart-container.donut {{
        height:auto; min-height:unset; max-height:unset;
        display:flex; flex-direction:column; align-items:center; gap:14px;
        padding:8px 0 4px;
    }}
    .donut-canvas-wrap {{
        position:relative;
        width:min(320px, 78vw);
        height:min(320px, 78vw);
        flex-shrink:0;
    }}
    .donut-legend {{
        width:100%; display:flex; flex-direction:column; gap:3px;
        max-height:220px; overflow-y:auto; padding:0 2px;
    }}
    .donut-legend::-webkit-scrollbar {{ width:4px; }}
    .donut-legend::-webkit-scrollbar-track {{ background:transparent; }}
    .donut-legend::-webkit-scrollbar-thumb {{ background:var(--border); border-radius:4px; }}
    .legend-item {{
        display:flex; align-items:center; gap:8px;
        font-size:0.78em; color:var(--text-mid); padding:4px 8px;
        border-radius:7px; transition:background 0.15s;
    }}
    .legend-item:hover {{ background:var(--surface2); color:var(--text); }}
    .legend-dot {{ width:9px; height:9px; border-radius:50%; flex-shrink:0; }}
    .legend-name {{ flex:1; display:flex; flex-direction:column; gap:1px; }}
    .legend-budget {{ font-size:0.78em; color:var(--text-dim); }}
    .legend-budget.over {{ color:var(--red); font-weight:700; }}
    .legend-item.over-budget {{ background:rgba(224,90,90,0.09); }}
    .legend-val {{ font-weight:700; color:var(--text); }}
    .legend-pct {{ color:var(--text-dim); font-size:0.88em; margin-left:3px; }}
    .tab-pane {{ display:none; }}
    .btn-home {{
        display:block; text-align:center; padding:13px; margin-top:12px;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; border-radius:10px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.9em;
        line-height:1.5; transition:all 0.2s;
    }}
    .btn-home:hover {{ transform:translateY(-1px); box-shadow:0 6px 20px rgba(201,168,76,0.25); }}
    @media (max-width:500px) {{
        .tab-btn {{ padding:7px 10px; font-size:0.7em; }}
        .chart-container {{ height:52vw; min-height:260px; }}
        .donut-canvas-wrap {{ width:min(260px, 82vw); height:min(260px, 82vw); }}
    }}
</style>
</head>
<body>
<header>
    <button class="menu-btn" onclick="toggleMenu()">⚙️</button>
    <div id="extraMenu" class="nav-dropdown">
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Finanze</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/">🏠 Aggiungi Operazione</a>
                <a href="/lista">📈 Gestione Movimenti Mese</a>
                <a href="/stats">📊 Bilancio Mese</a>
                <a href="/fondo_risparmio_web">💰 Fondo Risparmio</a>
                <a href="/scadenze_web">📅 Scadenze del Mese</a>
                <a href="/fairshare_web">⚖️ FairShare</a>
                <a href="/menu_esplora">🔍 Esplora</a>
                <a href="/grafici_web">📅 Grafici e Statistiche</a>
                <a href="/gestione_categorie">⚙️ Gestione Categorie</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Casa</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/utenze?anno={anno_corrente_format}">💧 Utenze</a>
                <a href="/consultazione_supermercati">🛒 Gestione Supermercati</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Documenti</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/documenti_pdf_web">🗄️ Documenti Contabili</a>
                <a href="/documenti_personali_web">🗄️ Documenti Personali</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Sistema</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/info_sys_web">📡 Monitor Server</a>
                <a href="/cambia_pw_web">🔑 Cambia Password</a>
                <a href="/webauthn_web">👆 Biometrico</a>
                <a href="/cambia_profilo_web">👤 Cambia Profilo</a>
                <a href="/logoff">🔓 Logout</a>
            </div>
        </div>
    </div>
    <div class="header-title">📊 Grafici e Statistiche</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main class="main-container">
    <div class="tab-bar">
        <button class="tab-btn" onclick="openTab('tabStoricoEU', this)">📅 Storico</button>
        <button class="tab-btn" onclick="openTab('tabMensileEU', this)">🗓️ Mensile</button>
        <button class="tab-btn" onclick="openTab('tabSaldo', this)">📈 Saldo Mese</button>
        <button class="tab-btn" onclick="openTab('tabSaldoAnnuale', this)">⚖️ Saldo Annuale</button>
        <button class="tab-btn" onclick="openTab('tabCategorie', this)">🍩 Uscite</button>
        <button class="tab-btn" onclick="openTab('tabStoricoCat', this)">📊 Uscite Storiche</button>
    </div>
    <div class="chart-frame">
        <div id="tabStoricoEU"    class="tab-pane"><div class="chart-container"><canvas></canvas></div></div>
        <div id="tabMensileEU"    class="tab-pane"><div class="chart-container"><canvas></canvas></div></div>
        <div id="tabSaldo"        class="tab-pane"><div class="chart-container"><canvas></canvas></div></div>
        <div id="tabSaldoAnnuale" class="tab-pane"><div class="chart-container"><canvas></canvas></div></div>
        <div id="tabCategorie" class="tab-pane">
            <div class="chart-container donut">
                <div class="donut-canvas-wrap"><canvas></canvas></div>
                <div class="donut-legend" id="legendTabCategorie"></div>
            </div>
        </div>
        <div id="tabStoricoCat" class="tab-pane">
            <div class="chart-container donut">
                <div class="donut-canvas-wrap"><canvas></canvas></div>
                <div class="donut-legend" id="legendTabStoricoCat"></div>
            </div>
        </div>
    </div>
    <a href="/" class="btn-home">🏠 Torna alla Home</a>
</main>
<script>
    const chartInstances = {{}};
    const chartData = {{
        tabStoricoEU:    {dati_entrate_uscite_storici},
        tabMensileEU:    {dati_entrate_uscite_mensili},
        tabSaldo:        {dati_saldo},
        tabSaldoAnnuale: {dati_saldo_annuale},
        tabCategorie:    {dati_categorie},
        tabStoricoCat:   {dati_categorie_storiche}
    }};
    function fmtIt(v) {{
        v = Number(v || 0);
        const neg = v < 0;
        const parts = Math.abs(v).toFixed(2).split('.');
        parts[0] = parts[0].replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, '.');
        return (neg ? '-' : '') + parts[0] + ',' + parts[1];
    }}
    function getChartColors() {{
        const light = document.documentElement.classList.contains('light');
        return {{
            tick:   light ? '#777' : '#555',
            grid:   light ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.04)',
            legend: light ? '#555' : '#888'
        }};
    }}
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if (btn) btn.textContent = '🌙'; }}
        else               {{ root.classList.remove('light'); if (btn) btn.textContent = '☀️'; }}
        const activeTab = document.querySelector('.tab-btn.active');
        if (activeTab) {{
            const tabName = activeTab.getAttribute('onclick').match(/'([^']+)'/)[1];
            renderChart(tabName);
        }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        applyTheme(next);
    }}
    applyTheme(localStorage.getItem('theme') || 'dark');
    function sortData(data) {{
        if (!data.labels) return data;
        const budgets = data.datasets[0].budget || [];
        let combined = data.labels.map((l, i) => ({{
            label: l,
            val: data.datasets[0].data[i],
            color: data.datasets[0].backgroundColor[i],
            budget: budgets[i] || 0
        }}));
        combined.sort((a, b) => b.val - a.val);
        data.labels = combined.map(x => x.label);
        data.datasets[0].data = combined.map(x => x.val);
        data.datasets[0].backgroundColor = combined.map(x => x.color);
        data.datasets[0].budget = combined.map(x => x.budget);
        return data;
    }}
    function buildDonutLegend(legendId, data) {{
        const legendEl = document.getElementById(legendId);
        if (!legendEl) return;
        const labels = data.labels || [];
        const vals = data.datasets[0].data || [];
        const colors = data.datasets[0].backgroundColor || [];
        const budgets = data.datasets[0].budget || [];
        const total = vals.reduce((a, b) => a + b, 0);
        legendEl.innerHTML = labels.map((lbl, i) => {{
            const pct = total > 0 ? ((vals[i] / total) * 100).toFixed(1) : '0.0';
            const budget = budgets[i] || 0;
            const sfora = budget > 0 && vals[i] > budget;
            const budgetInfo = budget > 0
                ? `<span class="legend-budget${{sfora ? ' over' : ''}}">${{sfora ? '⚠️ ' : ''}}budget € ${{fmtIt(budget)}}</span>`
                : '';
            return `<div class="legend-item${{sfora ? ' over-budget' : ''}}">
                <span class="legend-dot" style="background:${{colors[i] || '#888'}}"></span>
                <span class="legend-name">${{lbl}}${{budgetInfo}}</span>
                <span class="legend-val">€ ${{fmtIt(vals[i])}}</span>
                <span class="legend-pct">${{pct}}%</span>
            </div>`;
        }}).join('');
    }}
    function toggleNavGroup(btn, ev) {{
        if (ev) ev.stopPropagation();
        const items = btn.nextElementSibling;
        const giaAperto = items.classList.contains('open');
        btn.closest('.nav-dropdown').querySelectorAll('.nav-group-items.open').forEach(function(el) {{
            el.classList.remove('open');
            el.previousElementSibling.querySelector('.nav-arrow').textContent = '▶';
        }});
        if (!giaAperto) {{
            items.classList.add('open');
            btn.querySelector('.nav-arrow').textContent = '▼';
        }}
    }}
    function toggleMenu() {{
        const m = document.getElementById("extraMenu");
        m.style.display = m.style.display === "block" ? "none" : "block";
    }}
    function openTab(tabName, btn) {{
        document.querySelectorAll(".tab-pane").forEach(p => p.style.display = "none");
        document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
        document.getElementById(tabName).style.display = "block";
        btn.classList.add("active");
        renderChart(tabName);
    }}
    function renderChart(tabName) {{
        if (chartInstances[tabName]) chartInstances[tabName].destroy();
        const isDonut = tabName === 'tabCategorie' || tabName === 'tabStoricoCat';
        const ctx = document.querySelector(`#${{tabName}} canvas`).getContext('2d');
        const cc = getChartColors();
        let type = 'bar';
        let opts = {{
            responsive: true,
            maintainAspectRatio: isDonut,
            plugins: {{ legend: {{ display: false }} }},
            scales: {{}}
        }};
        if (tabName === 'tabSaldo' || tabName === 'tabSaldoAnnuale') {{
            type = 'line';
        }}
        if (isDonut) {{
            type = 'doughnut';
            opts.cutout = '58%';
            opts.plugins.tooltip = {{
                callbacks: {{
                    label: function(ctx) {{
                        const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                        const pct = total > 0 ? ((ctx.parsed / total) * 100).toFixed(1) : 0;
                        return ` ${{ctx.label}}: € ${{fmtIt(ctx.parsed)}} (${{pct}}%)`;
                    }}
                }}
            }};
        }} else {{
            opts.plugins.legend = {{ labels: {{ color: cc.legend, font: {{ family: 'DM Sans' }} }} }};
            opts.plugins.tooltip = {{
                callbacks: {{
                    label: function(ctx) {{
                        const dsLabel = ctx.dataset.label ? ctx.dataset.label + ': ' : '';
                        return ` ${{dsLabel}}€ ${{fmtIt(ctx.parsed.y)}}`;
                    }}
                }}
            }};
            opts.scales = {{
                x: {{ ticks: {{ color: cc.tick, font: {{ family: 'DM Sans' }} }}, grid: {{ color: cc.grid }} }},
                y: {{ ticks: {{ color: cc.tick, font: {{ family: 'DM Sans' }}, callback: v => '€ ' + fmtIt(v) }}, grid: {{ color: cc.grid }} }}
            }};
        }}
        let data = JSON.parse(JSON.stringify(chartData[tabName]));
        if (isDonut) {{
            data = sortData(data);
            if (tabName === 'tabCategorie') {{
                const budgets = data.datasets[0].budget || [];
                const vals = data.datasets[0].data || [];
                const normalBorder = getComputedStyle(document.documentElement).getPropertyValue('--surface').trim() || '#0f0f0f';
                data.datasets[0].borderColor = vals.map((v, i) => (budgets[i] > 0 && v > budgets[i]) ? '#dc3545' : normalBorder);
                data.datasets[0].borderWidth = vals.map((v, i) => (budgets[i] > 0 && v > budgets[i]) ? 3 : 2);
            }}
            const legendId = 'legend' + tabName.charAt(0).toUpperCase() + tabName.slice(1);
            buildDonutLegend(legendId, data);
        }}
        chartInstances[tabName] = new Chart(ctx, {{ type, data, options: opts }});
    }}
    document.addEventListener("click", function(e) {{
        const menu = document.getElementById("extraMenu");
        const btn = document.querySelector(".menu-btn");
        if (menu && menu.style.display === "block" && !menu.contains(e.target) && e.target !== btn)
            menu.style.display = "none";
    }});
    document.querySelector('.tab-btn').click();
</script>
</body>
</html>"""

# Html Genera la pagina web delle scadenze/ricorrenze del mese corrente (equivalente web del popup scadenze_mese)
def html_scadenze_mese(self):
    import datetime
    from moduli.modello_spesa import campo
    def calcola_data_fine(data_inizio, n_volte, periodo):
        if not data_inizio or not isinstance(n_volte, int) or n_volte < 1:
            return "N/D"
        periodo = periodo.lower().strip()
        if periodo == "ogni giorno":
            data_fine_obj = data_inizio + datetime.timedelta(days=n_volte - 1)
        elif periodo == "ogni mese":
            total_months = data_inizio.month + n_volte - 1
            anno_fine = data_inizio.year + (total_months - 1) // 12
            mese_fine = (total_months - 1) % 12 + 1
            giorno_inizio = data_inizio.day
            try:
                data_fine_obj = datetime.date(anno_fine, mese_fine, giorno_inizio)
            except ValueError:
                if mese_fine == 12:
                    primo_giorno_mese_successivo = datetime.date(anno_fine + 1, 1, 1)
                else:
                    primo_giorno_mese_successivo = datetime.date(anno_fine, mese_fine + 1, 1)
                ultimo_giorno_mese_fine = (primo_giorno_mese_successivo - datetime.timedelta(days=1)).day
                data_fine_obj = datetime.date(anno_fine, mese_fine, ultimo_giorno_mese_fine)
        elif periodo == "ogni anno":
            anno_fine = data_inizio.year + n_volte - 1
            try:
                data_fine_obj = data_inizio.replace(year=anno_fine)
            except ValueError:
                data_fine_obj = data_inizio.replace(year=anno_fine, day=28)
        else:
            return "N/D"
        return data_fine_obj.strftime("%d-%m-%Y")
    oggi = datetime.date.today()
    mese_corrente = oggi.month
    anno_corrente = oggi.year
    mesi_italiani = [
        "Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
        "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"
    ]
    mese_nome = mesi_italiani[mese_corrente - 1]
    righe = []
    for item_id, dati in self.ricorrenze.items():
        try:
            ric_type = dati.get("tipo", "").lower()
            n = dati.get("n", 0)
            data_inizio = datetime.datetime.strptime(dati.get("data_inizio", ""), "%d-%m-%Y").date()
            categoria = dati.get("cat", "N/D")
            descrizione_base = dati.get("desc", "—")
            tipo_voce = dati.get("tipo_voce", "N/D")
            importo_base = float(str(dati.get("imp", "0")).replace(",", "."))
            date_nel_mese = []
            for i in range(n):
                if ric_type == "ogni mese":
                    mese = (data_inizio.month - 1 + i) % 12 + 1
                    anno = data_inizio.year + (data_inizio.month - 1 + i) // 12
                    giorno = min(
                        data_inizio.day,
                        [31, 29 if anno % 4 == 0 and (anno % 100 != 0 or anno % 400 == 0) else 28,
                         31, 30, 31, 30, 31, 31, 30, 31, 30, 31][mese - 1]
                    )
                    data_movimento = datetime.date(anno, mese, giorno)
                elif ric_type == "ogni anno":
                    try:
                        data_movimento = data_inizio.replace(year=data_inizio.year + i)
                    except ValueError:
                        data_movimento = data_inizio.replace(year=data_inizio.year + i, day=28)
                else:
                    data_movimento = data_inizio + datetime.timedelta(days=i)
                if data_movimento.month == mese_corrente and data_movimento.year == anno_corrente:
                    date_nel_mese.append((i + 1, data_movimento))
            data_fine_serie = calcola_data_fine(data_inizio, n, ric_type)
            for indice, data_movimento in date_nel_mese:
                voce_trovata = False
                importo_effettivo = importo_base
                if data_movimento in self.spese:
                    for voce in self.spese[data_movimento]:
                        if len(voce) >= 5 and voce[4] == item_id:
                            importo_effettivo = voce[2]
                            voce_trovata = True
                            break
                pagato = data_movimento <= oggi and voce_trovata
                righe.append({
                    "data": data_movimento, "categoria": categoria, "descrizione": descrizione_base,
                    "importo": importo_effettivo, "tipo": tipo_voce, "scadenza_serie": data_fine_serie,
                    "pagato": pagato, "trovata": voce_trovata, "progressione": f"{indice}/{n}",
                })
        except Exception as e:
            print(f"Errore nella ricorrenza con ID {item_id}: {e}")
            continue
    fine_mese = datetime.date(anno_corrente, mese_corrente, 28)
    while True:
        try:
            fine_mese = fine_mese.replace(day=fine_mese.day + 1)
        except ValueError:
            break
    for data_voce in sorted(self.spese.keys()):
        if oggi <= data_voce <= fine_mese:
            for voce in self.spese[data_voce]:
                if len(voce) < 5 or voce[4] not in self.ricorrenze:
                    try:
                        categoria, descrizione, importo, tipo_voce = voce[:4]
                        righe.append({
                            "data": data_voce, "categoria": categoria, "descrizione": descrizione,
                            "importo": importo, "tipo": tipo_voce, "scadenza_serie": data_voce.strftime("%d-%m-%Y"),
                            "pagato": data_voce <= oggi, "trovata": True, "progressione": "—",
                        })
                    except Exception as e:
                        print(f"Errore nella voce normale del {data_voce}: {e}")
                        continue
    righe.sort(key=lambda r: r["data"])
    righe_html = ""
    if not righe:
        righe_html = "<p style='text-align:center; color:#555; padding:20px; font-style:italic;'>Nessuna scadenza per questo mese.</p>"
    else:
        for r in righe:
            colore = "#4caf82" if r["tipo"].strip().lower() != "uscita" and r["trovata"] else ("#e05a5a" if r["tipo"].strip().lower() == "uscita" else "#888")
            segno = "-" if r["tipo"].strip().lower() == "uscita" else "+"
            stato_icona = "✔️" if r["pagato"] else "❌"
            stato_testo = "Pagato" if r["pagato"] else "Da pagare"
            valore_importo = f"{segno}€{_fmt_it(r['importo'])}" if r["trovata"] else "—"
            righe_html += f"""
            <div class="scad-item">
                <div class="scad-date">{r['data'].strftime('%d-%m-%Y')}</div>
                <div class="scad-body">
                    <div class="scad-top">
                        <span class="scad-cat">{r['categoria']}</span>
                        <span class="scad-amt" style="color:{colore};">{valore_importo}</span>
                    </div>
                    <div class="scad-desc">{r['descrizione']}</div>
                    <div class="scad-meta">
                        <span class="scad-badge">{stato_icona} {stato_testo}</span>
                        <span class="scad-badge">{r['progressione']}</span>
                        <span class="scad-badge">{r['tipo']}</span>
                    </div>
                </div>
            </div>"""
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>📅 Scadenze del Mese</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
    (function() {{
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    }})();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg:#050505; --surface:#0f0f0f; --surface2:#161616; --surface3:#1e1e1e;
        --border:rgba(255,255,255,0.07); --gold:#c9a84c; --blue:#63a0f0;
        --green:#4caf82; --red:#e05a5a; --text:#e8e8e8; --text-dim:#555; --text-mid:#888;
        --radius-lg:18px;
    }}
    :root.light {{
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --gold:#b8902a; --blue:#3d7fd4;
        --green:#3a9068; --red:#cc3333; --text:#1a1a1a; --text-dim:#999; --text-mid:#555;
    }}
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{ font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text);
        min-height:100vh; padding-bottom:50px; transition:background 0.3s,color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 40% at 50% -10%, rgba(99,160,240,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 60%); }}
    header {{ padding:14px 16px 12px; display:flex; align-items:center; justify-content:center;
        border-bottom:1px solid var(--border); background:rgba(5,5,5,0.95);
        backdrop-filter:blur(20px); position:sticky; top:0; z-index:100; }}
    :root.light header {{ background:rgba(245,245,240,0.95); }}
    .menu-btn {{ position:absolute; left:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border); color:var(--gold);
        width:36px; height:36px; border-radius:10px; font-size:1em;
        cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.2s; }}
    .menu-btn:hover {{ border-color:var(--gold); }}
    .header-title {{ font-family:'DM Sans',sans-serif; font-size:1em; font-weight:700; color:var(--text); }}
    .theme-toggle {{
        position:absolute; right:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border);
        border-radius:8px; width:34px; height:34px;
        display:flex; align-items:center; justify-content:center;
        cursor:pointer; font-size:1em; transition:all 0.2s; }}
    .theme-toggle:hover {{ border-color:var(--gold); }}
    .nav-dropdown {{ position:absolute; top:calc(100% + 6px); left:10px;
        background:var(--surface2); border:1px solid var(--border); border-radius:var(--radius-lg);
        display:none; z-index:1000; width:270px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.7); }}
    .nav-dropdown a {{ display:flex; align-items:center; gap:10px; padding:10px 16px;
        text-decoration:none; color:var(--text-mid); border-bottom:1px solid var(--border);
        font-size:0.87em; transition:all 0.15s; }}
    .nav-dropdown a:last-child {{ border-bottom:none; }}
    .nav-dropdown a:hover {{ background:var(--surface3); color:var(--text); padding-left:22px; }}
    .nav-group-btn {{ display:flex; justify-content:space-between; align-items:center; width:100%;
        padding:8px 16px; background:none; border:none; font-family:inherit; color:var(--gold);
        font-size:0.7em; font-weight:700; letter-spacing:1px; text-transform:uppercase; cursor:pointer; opacity:0.85; }}
    .nav-group-btn:hover {{ opacity:1; background:var(--surface3); }}
    .nav-arrow {{ font-size:0.85em; transition:transform 0.15s; }}
    .nav-group-items {{ display:none; flex-direction:column; }}
    .nav-group-items.open {{ display:flex; }}
    main {{ padding:14px; max-width:580px; margin:0 auto; animation:fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .summary-card {{ background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-lg);
        padding:16px 18px; margin-bottom:12px; text-align:center; position:relative; overflow:hidden; }}
    .summary-card::before {{ content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent); }}
    .summary-title {{ font-family:'DM Sans',sans-serif; font-size:1.05em; font-weight:800; }}
    .scad-item {{ background:var(--surface); border:1px solid var(--border); border-radius:12px;
        margin-bottom:8px; display:flex; overflow:hidden; }}
    .scad-date {{ background:var(--surface3); color:var(--text-dim); font-size:0.72em; font-weight:700;
        writing-mode:vertical-rl; text-orientation:mixed; padding:10px 6px; flex-shrink:0;
        display:flex; align-items:center; justify-content:center; letter-spacing:1px; }}
    .scad-body {{ padding:10px 14px; flex:1; min-width:0; }}
    .scad-top {{ display:flex; justify-content:space-between; align-items:baseline; gap:8px; }}
    .scad-cat {{ font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.9em; }}
    .scad-amt {{ font-weight:700; font-size:0.9em; flex-shrink:0; }}
    .scad-desc {{ font-size:0.78em; color:var(--text-mid); margin-top:2px; }}
    .scad-meta {{ display:flex; gap:6px; margin-top:8px; flex-wrap:wrap; }}
    .scad-badge {{ background:var(--surface2); border:1px solid var(--border); border-radius:6px;
        padding:2px 8px; font-size:0.68em; color:var(--text-dim); }}
    .btn-home {{ display:block; text-align:center; padding:13px; margin-top:12px;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; border-radius:10px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.9em;
        line-height:1.5; transition:all 0.2s; }}
    .btn-home:hover {{ transform:translateY(-1px); box-shadow:0 6px 20px rgba(201,168,76,0.25); }}
</style>
</head>
<body>
<header>
    <button class="menu-btn" onclick="toggleMenu(event)">⚙️</button>
    <div id="extraMenu" class="nav-dropdown">
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Finanze</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/">🏠 Aggiungi Operazione</a>
                <a href="/lista">📈 Gestione Movimenti Mese</a>
                <a href="/stats">📊 Bilancio Mese</a>
                <a href="/fondo_risparmio_web">💰 Fondo Risparmio</a>
                <a href="/scadenze_web">📅 Scadenze del Mese</a>
                <a href="/fairshare_web">⚖️ FairShare</a>
                <a href="/menu_esplora">🔍 Esplora</a>
                <a href="/grafici_web">📅 Grafici e Statistiche</a>
                <a href="/gestione_categorie">⚙️ Gestione Categorie</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Casa</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/utenze?anno={oggi.year}">💧 Utenze</a>
                <a href="/consultazione_supermercati">🛒 Supermercati</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Documenti</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/documenti_pdf_web">🗄️ Documenti Contabili</a>
                <a href="/documenti_personali_web">🗄️ Documenti Personali</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Sistema</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/info_sys_web">📡 Monitor Server</a>
                <a href="/cambia_pw_web">🔑 Cambia Password</a>
                <a href="/webauthn_web">👆 Biometrico</a>
                <a href="/cambia_profilo_web">👤 Cambia Profilo</a>
                <a href="/logoff">🔓 Logout</a>
            </div>
        </div>
    </div>
    <div class="header-title">📅 Scadenze del Mese</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="summary-card">
        <div class="summary-title">Scadenze di {mese_nome} {anno_corrente}</div>
    </div>
    {righe_html}
    <a href="/" class="btn-home">🏠 Torna alla Home</a>
</main>
<script>
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if (btn) btn.textContent = '🌙'; }}
        else               {{ root.classList.remove('light'); if (btn) btn.textContent = '☀️'; }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        applyTheme(next);
    }}
    applyTheme(localStorage.getItem('theme') || 'dark');
    function toggleNavGroup(btn, ev) {{
        if (ev) ev.stopPropagation();
        const items = btn.nextElementSibling;
        const giaAperto = items.classList.contains('open');
        btn.closest('.nav-dropdown').querySelectorAll('.nav-group-items.open').forEach(function(el) {{
            el.classList.remove('open');
            el.previousElementSibling.querySelector('.nav-arrow').textContent = '▶';
        }});
        if (!giaAperto) {{
            items.classList.add('open');
            btn.querySelector('.nav-arrow').textContent = '▼';
        }}
    }}
    function toggleMenu(e) {{
        e.stopPropagation();
        const m = document.getElementById("extraMenu");
        m.style.display = (m.style.display === "block") ? "none" : "block";
    }}
    document.addEventListener("click", function(e) {{
        const m = document.getElementById("extraMenu");
        if (m && m.style.display === "block" && !m.contains(e.target)) m.style.display = "none";
    }});
</script>
</body>
</html>"""

# Html Genera la pagina web dei movimenti del mese corrente con riepilogo entrate/uscite/saldo e azioni di modifica e cancellazione
def html_lista_spese_mensili(self):
    import datetime
    mesi_it = {
        "January": "gennaio", "February": "febbraio", "March": "marzo",
        "April": "aprile", "May": "maggio", "June": "giugno",
        "July": "luglio", "August": "agosto", "September": "settembre",
        "October": "ottobre", "November": "novembre", "December": "dicembre"
    }
    oggi = datetime.date.today()
    mese_en = oggi.strftime('%B')
    mese_it_corrente = mesi_it.get(mese_en, mese_en)
    titolo_mese = f"{mese_it_corrente.capitalize()} {oggi.year}"
    current_month_expenses = []
    tot_entrate = 0.0
    tot_uscite = 0.0
    for d, voci in self.spese.items():
        if d.month == oggi.month and d.year == oggi.year:
            for idx, voce in enumerate(voci):
                if isinstance(voce, dict):
                    categoria = voce.get("categoria", "")
                    descrizione = voce.get("descrizione", "")
                    importo = float(voce.get("importo", 0))
                    tipo = voce.get("tipo", "")
                else:
                    categoria = voce[0] if len(voce) >= 1 else ""
                    descrizione = voce[1] if len(voce) >= 2 else ""
                    importo = float(voce[2]) if len(voce) >= 3 else 0.0
                    tipo = voce[3] if len(voce) >= 4 else ""
                tipo = tipo or ""
                current_month_expenses.append((d, idx, categoria, descrizione, importo, tipo))
                if tipo.strip().lower() == "entrata":
                    tot_entrate += importo
                else:
                    tot_uscite += importo
    saldo_mese = tot_entrate - tot_uscite
    icona_meteo = "☀️" if saldo_mese >= 0 else "⛈️"
    colore_saldo = "#4caf82" if saldo_mese >= 0 else "#e05a5a"
    segno_saldo_mese = "+" if saldo_mese >= 0 else ""
    current_month_expenses.sort(key=lambda x: x[0], reverse=True)
    schede_html = ""
    if not current_month_expenses:
        schede_html = "<p style='text-align:center; color:#555; padding:20px; font-style:italic;'>Nessun movimento registrato.</p>"
    else:
        for d, idx, cat, desc, imp, tipo in current_month_expenses:
            data_str = d.strftime('%d-%m-%Y')
            details_id = f"details_{d.strftime('%Y%m%d')}_{idx}"
            colore_imp = "#4caf82" if tipo.strip().lower() == "entrata" else "#e05a5a"
            segno = "+" if tipo.strip().lower() == "entrata" else "-"
            schede_html += f"""
            <div class="op-item">
                <div class="op-summary" onclick="toggleVisibility('{details_id}', this)">
                    <span class="op-arrow">▶</span>
                    <span class="op-date">{data_str}</span>
                    <span class="op-cat">{cat}</span>
                    <span class="op-amt" style="color:{colore_imp};">€ {segno}{_fmt_it(imp)}</span>
                </div>
                <div id="{details_id}" class="op-details">
                    <div class="op-row"><span class="op-lbl">Tipo</span><span>{tipo}</span></div>
                    <div class="op-row"><span class="op-lbl">Dettaglio</span><span>{desc}</span></div>
                    <div class="op-row op-actions">
                        <form method="get" action="/modifica" style="flex:1;">
                            <input type="hidden" name="data" value="{data_str}">
                            <input type="hidden" name="idx" value="{idx}">
                            <button type="submit" class="op-btn">✏️ Modifica</button>
                        </form>
                        <button type="button" class="op-btn danger"
                            onclick="event.stopPropagation(); apriModal('{data_str}', '{idx}', '{cat}', '{_fmt_it(imp)}', {'1' if 'ALL·' in desc else '0'})">
                            ❌ Cancella
                        </button>
                    </div>
                </div>
            </div>"""
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>📈 Movimenti Mese</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
    (function() {{
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    }})();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg:#050505; --surface:#0f0f0f; --surface2:#161616; --surface3:#1e1e1e;
        --border:rgba(255,255,255,0.07); --gold:#c9a84c; --blue:#63a0f0;
        --green:#4caf82; --red:#e05a5a; --text:#e8e8e8; --text-dim:#555; --text-mid:#888;
        --radius-lg:18px;
    }}
    :root.light {{
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --gold:#b8902a; --blue:#3d7fd4;
        --green:#3a9068; --red:#cc3333; --text:#1a1a1a; --text-dim:#999; --text-mid:#555;
    }}
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{ font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text);
        min-height:100vh; padding-bottom:50px; transition:background 0.3s,color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 40% at 50% -10%, rgba(99,160,240,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 60%); }}
    header {{ padding:14px 16px 12px; display:flex; align-items:center; justify-content:center;
        border-bottom:1px solid var(--border); background:rgba(5,5,5,0.95);
        backdrop-filter:blur(20px); position:sticky; top:0; z-index:100; }}
    :root.light header {{ background:rgba(245,245,240,0.95); }}
    .menu-btn {{ position:absolute; left:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border); color:var(--gold);
        width:36px; height:36px; border-radius:10px; font-size:1em;
        cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.2s; }}
    .menu-btn:hover {{ border-color:var(--gold); }}
    .header-title {{ font-family:'DM Sans',sans-serif; font-size:1em; font-weight:700; color:var(--text); }}
    .theme-toggle {{
        position:absolute; right:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border);
        border-radius:8px; width:34px; height:34px;
        display:flex; align-items:center; justify-content:center;
        cursor:pointer; font-size:1em; transition:all 0.2s; }}
    .theme-toggle:hover {{ border-color:var(--gold); }}
    .nav-dropdown {{ position:absolute; top:calc(100% + 6px); left:10px;
        background:var(--surface2); border:1px solid var(--border); border-radius:var(--radius-lg);
        display:none; z-index:1000; width:270px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.7); }}
    .nav-dropdown a {{ display:flex; align-items:center; gap:10px; padding:10px 16px;
        text-decoration:none; color:var(--text-mid); border-bottom:1px solid var(--border);
        font-size:0.87em; transition:all 0.15s; }}
    .nav-dropdown a:last-child {{ border-bottom:none; }}
    .nav-dropdown a:hover {{ background:var(--surface3); color:var(--text); padding-left:22px; }}
    .nav-group-btn {{ display:flex; justify-content:space-between; align-items:center; width:100%;
        padding:8px 16px; background:none; border:none; font-family:inherit; color:var(--gold);
        font-size:0.7em; font-weight:700; letter-spacing:1px; text-transform:uppercase; cursor:pointer; opacity:0.85; }}
    .nav-group-btn:hover {{ opacity:1; background:var(--surface3); }}
    .nav-arrow {{ font-size:0.85em; transition:transform 0.15s; }}
    .nav-group-items {{ display:none; flex-direction:column; }}
    .nav-group-items.open {{ display:flex; }}
    main {{ padding:14px; max-width:580px; margin:0 auto; animation:fadeIn 0.3s ease; }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(8px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .summary-card {{ background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-lg);
        padding:16px 18px; margin-bottom:12px; text-align:center; position:relative; overflow:hidden; }}
    .summary-card::before {{ content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent); }}
    .summary-title {{ font-family:'DM Sans',sans-serif; font-size:1.05em; font-weight:800; margin-bottom:10px; }}
    .summary-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:10px; }}
    .sg-box {{ background:var(--surface2); border:1px solid var(--border); border-radius:10px; padding:9px 12px; }}
    .sg-label {{ display:block; font-size:0.6em; color:var(--text-dim); letter-spacing:1.5px; text-transform:uppercase; margin-bottom:3px; }}
    .sg-val {{ font-family:'DM Sans',sans-serif; font-size:1.05em; font-weight:800; }}
    .saldo-row {{ padding-top:10px; border-top:1px solid var(--border); }}
    .saldo-lbl {{ font-size:0.6em; color:var(--text-dim); letter-spacing:1.5px; text-transform:uppercase; }}
    .saldo-num {{ font-family:'DM Sans',sans-serif; font-size:1.5em; font-weight:800; }}
    .op-item {{ background:var(--surface); border:1px solid var(--border); border-radius:12px; margin-bottom:6px; overflow:hidden; }}
    .op-summary {{ display:flex; align-items:center; padding:11px 14px; cursor:pointer; gap:8px; transition:background 0.15s; }}
    .op-summary:hover {{ background:var(--surface2); }}
    .op-arrow {{ font-size:0.65em; color:var(--text-dim); transition:transform 0.2s; flex-shrink:0; }}
    .op-date {{ color:var(--text-dim); font-size:0.75em; width:72px; flex-shrink:0; }}
    .op-cat {{ font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.85em; flex:1; }}
    .op-amt {{ font-weight:700; font-size:0.9em; flex-shrink:0; }}
    .op-details {{ display:none; border-top:1px solid var(--border); padding:10px 14px; background:var(--surface2); }}
    .op-details.active {{ display:block; }}
    .op-row {{ display:flex; gap:8px; font-size:0.83em; margin-bottom:6px; }}
    .op-lbl {{ color:var(--blue); font-weight:700; width:72px; flex-shrink:0; font-size:0.9em; }}
    .op-actions {{ margin-top:8px; gap:8px; }}
    .op-btn {{ flex:1; padding:9px; border-radius:8px; border:1px solid var(--border);
        background:var(--surface); color:var(--text-mid); font-size:0.82em; cursor:pointer; transition:all 0.15s;
        font-family:'DM Sans',sans-serif; line-height:1.5; }}
    .op-btn:hover {{ border-color:var(--blue); color:var(--text); }}
    .op-btn.danger {{ border-color:var(--red); color:var(--red); }}
    .op-btn.danger:hover {{ background:rgba(224,90,90,0.1); }}
    .modal-overlay {{ display:none; position:fixed; inset:0;
        background:rgba(0,0,0,0.75); backdrop-filter:blur(6px);
        z-index:3000; align-items:center; justify-content:center; }}
    .modal-box {{ background:var(--surface2); border:1px solid var(--border);
        border-radius:var(--radius-lg); padding:24px 20px; width:88%; max-width:320px; text-align:center; }}
    .modal-title {{ font-family:'DM Sans',sans-serif; font-size:1em; font-weight:800; color:var(--red); margin-bottom:10px; }}
    .modal-text {{ font-size:0.88em; color:var(--text-mid); margin-bottom:18px; }}
    .modal-btns {{ display:flex; gap:10px; }}
    .m-btn {{ flex:1; padding:12px; border-radius:9px; border:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.88em; cursor:pointer; transition:all 0.15s; }}
    .m-cancel {{ background:var(--surface3); color:var(--text-mid); }}
    .m-confirm {{ background:var(--red); color:white; }}
    .m-confirm:hover {{ box-shadow:0 4px 14px rgba(224,90,90,0.3); }}
    .btn-home {{ display:block; text-align:center; padding:13px; margin-top:12px;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; border-radius:10px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.9em;
        line-height:1.5; transition:all 0.2s; }}
    .btn-home:hover {{ transform:translateY(-1px); box-shadow:0 6px 20px rgba(201,168,76,0.25); }}
</style>
</head>
<body>
<header>
    <button class="menu-btn" onclick="toggleMenu(event)">⚙️</button>
    <div id="extraMenu" class="nav-dropdown">
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Finanze</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/">🏠 Aggiungi Operazione</a>
                <a href="/lista">📈 Gestione Movimenti Mese</a>
                <a href="/stats">📊 Bilancio Mese</a>
                <a href="/fondo_risparmio_web">💰 Fondo Risparmio</a>
                <a href="/scadenze_web">📅 Scadenze del Mese</a>
                <a href="/fairshare_web">⚖️ FairShare</a>
                <a href="/menu_esplora">🔍 Esplora</a>
                <a href="/grafici_web">📅 Grafici e Statistiche</a>
                <a href="/gestione_categorie">⚙️ Gestione Categorie</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Casa</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/utenze?anno={oggi.year}">💧 Utenze</a>
                <a href="/consultazione_supermercati">🛒 Supermercati</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Documenti</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/documenti_pdf_web">🗄️ Documenti Contabili</a>
                <a href="/documenti_personali_web">🗄️ Documenti Personali</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Sistema</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/info_sys_web">📡 Monitor Server</a>
                <a href="/cambia_pw_web">🔑 Cambia Password</a>
                <a href="/webauthn_web">👆 Biometrico</a>
                <a href="/cambia_profilo_web">👤 Cambia Profilo</a>
                <a href="/logoff">🔓 Logout</a>
            </div>
        </div>
    </div>
    <div class="header-title">📈 Gestione Movimenti Mese</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="summary-card">
        <div class="summary-title">{titolo_mese} {icona_meteo}</div>
        <div class="summary-grid">
            <div class="sg-box">
                <span class="sg-label">Entrate</span>
                <span class="sg-val" style="color:var(--green);">€ +{_fmt_it(tot_entrate)}</span>
            </div>
            <div class="sg-box">
                <span class="sg-label">Uscite</span>
                <span class="sg-val" style="color:var(--red);">€ -{_fmt_it(tot_uscite)}</span>
            </div>
        </div>
        <div class="saldo-row">
            <div class="saldo-lbl">Saldo attuale</div>
            <div class="saldo-num" style="color:{colore_saldo};">€ {segno_saldo_mese}{_fmt_it(saldo_mese)}</div>
        </div>
    </div>
    {schede_html}
    <a href="/" class="btn-home">🏠 Torna alla Home</a>
</main>
<div id="deleteModal" class="modal-overlay">
    <div class="modal-box">
        <div class="modal-title">❌ Conferma Eliminazione</div>
        <div class="modal-text" id="modalText"></div>
        <div class="modal-btns">
            <button class="m-btn m-cancel" onclick="closeDeleteModal()">Annulla</button>
            <button id="finalDeleteBtn" class="m-btn m-confirm">Elimina</button>
        </div>
    </div>
</div>
<div id="pdfModal" class="modal-overlay" style="display:none;">
    <div class="modal-box">
        <div class="modal-title">📎 Documento Allegato</div>
        <div class="modal-text">Vuoi eliminare anche il documento PDF dal registro?</div>
        <div class="modal-btns">
            <button class="m-btn m-cancel" onclick="confermaCancella(0)">Solo Movimento</button>
            <button class="m-btn m-confirm" onclick="confermaCancella(1)">Elimina Tutto</button>
        </div>
    </div>
</div>
<script>
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if (btn) btn.textContent = '🌙'; }}
        else               {{ root.classList.remove('light'); if (btn) btn.textContent = '☀️'; }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        applyTheme(next);
    }}
    applyTheme(localStorage.getItem('theme') || 'dark');
    let dData = null, dIdx = null, dHaPdf = false;
    function apriModal(data, idx, cat, imp, ha_pdf) {{
        dData = data; dIdx = idx; dHaPdf = (ha_pdf === '1' || ha_pdf === 1);
        document.getElementById("modalText").innerHTML = "Vuoi eliminare <b>" + cat + "</b> da <b>€ " + imp + "</b>?";
        document.getElementById("deleteModal").style.display = "flex";
    }}
    function closeDeleteModal() {{ document.getElementById("deleteModal").style.display = "none"; }}
    document.getElementById("finalDeleteBtn").onclick = function() {{
        closeDeleteModal();
        if (dHaPdf) {{
            document.getElementById("pdfModal").style.display = "flex";
        }} else {{
            confermaCancella(0);
        }}
    }};
    function confermaCancella(elimina_pdf) {{
        document.getElementById("pdfModal").style.display = "none";
        fetch('/cancella', {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
            body: 'data=' + encodeURIComponent(dData) + '&idx=' + encodeURIComponent(dIdx) + '&elimina_pdf=' + elimina_pdf
        }}).then(() => window.location.reload());
    }}
    function toggleNavGroup(btn, ev) {{
        if (ev) ev.stopPropagation();
        const items = btn.nextElementSibling;
        const giaAperto = items.classList.contains('open');
        btn.closest('.nav-dropdown').querySelectorAll('.nav-group-items.open').forEach(function(el) {{
            el.classList.remove('open');
            el.previousElementSibling.querySelector('.nav-arrow').textContent = '▶';
        }});
        if (!giaAperto) {{
            items.classList.add('open');
            btn.querySelector('.nav-arrow').textContent = '▼';
        }}
    }}
    function toggleMenu(e) {{
        e.stopPropagation();
        const m = document.getElementById("extraMenu");
        m.style.display = (m.style.display === "block") ? "none" : "block";
    }}
    document.addEventListener("click", function(e) {{
        const m = document.getElementById("extraMenu");
        if (m && m.style.display === "block" && !m.contains(e.target)) m.style.display = "none";
    }});
    function toggleVisibility(id, el) {{
        const c = document.getElementById(id);
        const a = el.querySelector(".op-arrow");
        if (c) c.classList.toggle("active");
        if (a) a.style.transform = c.classList.contains("active") ? "rotate(90deg)" : "rotate(0deg)";
    }}
</script>
</body>
</html>"""

# Html Bilancio Mese corrente con riepilogo entrate/uscite/saldo per categoria
def stats_mensili_html(self):
    mesi_it = {
        "January": "gennaio", "February": "febbraio", "March": "marzo",
        "April": "aprile", "May": "maggio", "June": "giugno",
        "July": "luglio", "August": "agosto", "September": "settembre",
        "October": "ottobre", "November": "novembre", "December": "dicembre"
    }
    oggi = datetime.date.today()
    mese_en = oggi.strftime('%B')
    mese_it_corrente = mesi_it.get(mese_en, mese_en)
    titolo_mese = f"{mese_it_corrente.capitalize()} {oggi.year}"
    entrate = 0.0
    uscite = 0.0
    entrate_categorie = {}
    uscite_categorie = {}
    raw_entrate_dettaglio = {}
    raw_uscite_dettaglio = {}
    entrate_count = {}
    uscite_count = {}
    for d, voci in self.spese.items():
        if d.month == oggi.month and d.year == oggi.year:
            for voce in voci:
                categoria, descrizione, importo, tipo = voce[:4]
                if tipo == "Entrata":
                    entrate += importo
                    entrate_categorie[categoria] = entrate_categorie.get(categoria, 0.0) + importo
                    raw_entrate_dettaglio.setdefault(categoria, []).append((d, descrizione, importo))
                    entrate_count[categoria] = entrate_count.get(categoria, 0) + 1
                else:
                    uscite += importo
                    uscite_categorie[categoria] = uscite_categorie.get(categoria, 0.0) + importo
                    raw_uscite_dettaglio.setdefault(categoria, []).append((d, descrizione, importo))
                    uscite_count[categoria] = uscite_count.get(categoria, 0) + 1
    saldo = entrate - uscite
    saldo_colore = "#4caf82" if saldo >= 0 else "#e05a5a"
    meteo_saldo = "☀️" if saldo >= 0 else "🌧️"
    segno_saldo = "+" if saldo >= 0 else ""

    def genera_html_categorie(categorie_totals, raw_dettaglio, prefix, counts_dict):
        html_content = ""
        if not categorie_totals:
            return f"<p class='no-data-msg'>Nessuna {prefix} per categoria da mostrare.</p>"
        html_content += "<ul class='category-list'>"
        for cat, totale in sorted(categorie_totals.items()):
            voci_dettaglio = raw_dettaglio.get(cat, [])
            dettagli_id = f"{prefix}_{''.join(filter(str.isalnum, cat))}"
            arrow_button_html = ''
            if voci_dettaglio:
                arrow_button_html = f"""<button type="button" class="cat-arrow-btn" onclick="toggleCat('{dettagli_id}', this)" aria-expanded="false"><span class="cat-arrow">▶</span></button>"""
            color_class = "amt-income" if prefix == "entrate" else "amt-expense"
            segno_cat = "+" if prefix == "entrate" else "-"
            dettaglio_items_html = ''.join(
                f'<li class="det-item"><span class="det-text">{data.strftime("%d-%m-%Y")}{" — " + desc if desc else ""}</span><span class="det-amt {color_class}">€ {segno_cat}{_fmt_it(imp)}</span></li>'
                for data, desc, imp, *_ in voci_dettaglio
            )
            if not dettaglio_items_html:
                dettaglio_items_html = '<li class="det-item" style="color:var(--text-dim)">Nessun dettaglio.</li>'
            num_ops = counts_dict.get(cat, 0)
            budget_cat = self.budget_categorie.get(cat, 0) if prefix == "uscite" else 0
            sfora_budget = budget_cat > 0 and totale > budget_cat
            budget_info_html = ''
            if budget_cat > 0:
                budget_info_html = f'<span class="cat-budget{" over" if sfora_budget else ""}">{"⚠️ " if sfora_budget else ""}budget € {_fmt_it(budget_cat)}</span>'
            item_class = "cat-item over-budget" if sfora_budget else "cat-item"
            html_content += f"""
            <li class="{item_class}">
                <div class="cat-summary">
                    {arrow_button_html}
                    <span class="cat-name"><span class="cat-name-row">{cat} <small>({num_ops})</small></span>{budget_info_html}</span>
                    <span class="cat-total {color_class}">€ {segno_cat}{_fmt_it(totale)}</span>
                </div>
                <ul id="{dettagli_id}" class="cat-details hidden">{dettaglio_items_html}</ul>
            </li>"""
        html_content += "</ul>"
        return html_content
    categorie_uscite_html  = genera_html_categorie(uscite_categorie,  raw_uscite_dettaglio,  "uscite",  uscite_count)
    categorie_entrate_html = genera_html_categorie(entrate_categorie, raw_entrate_dettaglio, "entrate", entrate_count)
    COMMON_HEAD = """
<script>
    (function() {
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    })();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>
    :root {
        --bg:#050505; --surface:#0f0f0f; --surface2:#161616; --surface3:#1e1e1e;
        --border:rgba(255,255,255,0.07); --gold:#c9a84c; --blue:#63a0f0;
        --green:#4caf82; --red:#e05a5a; --text:#e8e8e8;
        --text-dim:#555; --text-mid:#888; --radius-lg:18px;
    }
    :root.light {
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --gold:#b8902a; --blue:#3d7fd4;
        --green:#3a9068; --red:#cc3333; --text:#1a1a1a;
        --text-dim:#999; --text-mid:#555;
    }
    * { box-sizing:border-box; margin:0; padding:0; }
    body { font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text);
        min-height:100vh; padding-bottom:50px; transition:background 0.3s,color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 40% at 50% -10%, rgba(99,160,240,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 60%); }
    header { padding:14px 16px 12px; display:flex; align-items:center; justify-content:center;
        border-bottom:1px solid var(--border); background:rgba(5,5,5,0.95);
        backdrop-filter:blur(20px); position:sticky; top:0; z-index:100; }
    :root.light header { background:rgba(245,245,240,0.95); }
    .menu-btn { position:absolute; left:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border); color:var(--gold);
        width:36px; height:36px; border-radius:10px; font-size:1em;
        cursor:pointer; display:flex; align-items:center; justify-content:center; transition:all 0.2s; }
    .menu-btn:hover { border-color:var(--gold); box-shadow:0 0 12px rgba(201,168,76,0.2); }
    .header-title { font-family:'DM Sans',sans-serif; font-size:1em; font-weight:700; color:var(--text); }
    .theme-toggle {
        position:absolute; right:14px; top:50%; transform:translateY(-50%);
        background:var(--surface3); border:1px solid var(--border);
        border-radius:8px; width:34px; height:34px;
        display:flex; align-items:center; justify-content:center;
        cursor:pointer; font-size:1em; transition:all 0.2s; }
    .theme-toggle:hover { border-color:var(--gold); }
    .nav-dropdown { position:absolute; top:calc(100% + 6px); left:10px;
        background:var(--surface2); border:1px solid var(--border); border-radius:var(--radius-lg);
        display:none; z-index:1000; width:270px; overflow:hidden; box-shadow:0 20px 60px rgba(0,0,0,0.7); }
    .nav-dropdown a { display:flex; align-items:center; gap:10px; padding:10px 16px;
        text-decoration:none; color:var(--text-mid); border-bottom:1px solid var(--border);
        font-size:0.87em; transition:all 0.15s; }
    .nav-dropdown a:last-child { border-bottom:none; }
    .nav-dropdown a:hover { background:var(--surface3); color:var(--text); padding-left:22px; }
    .nav-group-btn { display:flex; justify-content:space-between; align-items:center; width:100%;
        padding:8px 16px; background:none; border:none; font-family:inherit; color:var(--gold);
        font-size:0.7em; font-weight:700; letter-spacing:1px; text-transform:uppercase; cursor:pointer; opacity:0.85; }
    .nav-group-btn:hover { opacity:1; background:var(--surface3); }
    .nav-arrow { font-size:0.85em; transition:transform 0.15s; }
    .nav-group-items { display:none; flex-direction:column; }
    .nav-group-items.open { display:flex; }
    main { padding:14px; max-width:580px; margin:0 auto; animation:fadeIn 0.3s ease; }
    @keyframes fadeIn { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
    .btn-home { display:block; text-align:center; padding:13px; margin-top:12px;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; border-radius:10px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.9em;
        line-height:1.5; transition:all 0.2s; }
    .btn-home:hover { transform:translateY(-1px); box-shadow:0 6px 20px rgba(201,168,76,0.25); }
    .amt-income { color:var(--green); }
    .amt-expense { color:var(--red); }
</style>"""
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>📊 Bilancio Mese</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
{COMMON_HEAD}
<style>
    .stats-card {{ background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-lg);
        padding:18px; margin-bottom:12px; position:relative; overflow:hidden; text-align:center; }}
    .stats-card::before {{ content:''; position:absolute; top:0; left:0; right:0; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent); }}
    .stats-title {{ font-family:'DM Sans',sans-serif; font-size:1.05em; font-weight:800; margin-bottom:12px; }}
    .stats-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-bottom:12px; }}
    .stat-box {{ background:var(--surface2); border:1px solid var(--border); border-radius:10px; padding:10px; }}
    .stat-label {{ display:block; font-size:0.6em; color:var(--text-dim); letter-spacing:1.5px; text-transform:uppercase; margin-bottom:3px; }}
    .stat-val {{ font-family:'DM Sans',sans-serif; font-size:1.1em; font-weight:800; }}
    .saldo-row {{ padding-top:10px; border-top:1px solid var(--border); }}
    .saldo-label {{ font-size:0.62em; color:var(--text-dim); letter-spacing:1.5px; text-transform:uppercase; }}
    .saldo-val {{ font-family:'DM Sans',sans-serif; font-size:1.5em; font-weight:800; }}
    .sec-toggle {{ width:100%; padding:13px 16px; margin-bottom:6px;
        background:var(--surface); border:1px solid var(--border); border-radius:12px;
        color:var(--text); font-family:'DM Sans',sans-serif; font-size:0.88em; font-weight:700;
        line-height:1.5; display:flex; justify-content:space-between; align-items:center;
        cursor:pointer; transition:background 0.15s; }}
    .sec-toggle:hover {{ background:var(--surface2); }}
    .sec-arrow {{ font-size:0.7em; color:var(--text-dim); transition:transform 0.22s; }}
    .collapsible-content {{ display:none; }}
    .collapsible-content.active {{ display:block; }}
    .no-data-msg {{ text-align:center; color:var(--text-dim); font-size:0.85em; padding:16px; font-style:italic; }}
    .category-list {{ list-style:none; padding:0; margin:0 0 10px 0; display:flex; flex-direction:column; gap:5px; }}
    .cat-item {{ background:var(--surface2); border:1px solid var(--border); border-radius:10px; overflow:hidden; }}
    .cat-summary {{ display:flex; align-items:center; gap:8px; padding:10px 14px; }}
    .cat-arrow-btn {{ background:none; border:none; cursor:pointer; padding:0; display:flex; align-items:center; color:var(--text-dim); }}
    .cat-arrow {{ font-size:0.7em; transition:transform 0.22s; }}
    .cat-arrow.open {{ transform:rotate(90deg); }}
    .cat-name {{ flex:1; font-size:0.88em; color:var(--text); display:flex; flex-direction:column; gap:1px; }}
    .cat-name small {{ color:var(--text-dim); font-size:0.8em; }}
    .cat-budget {{ font-size:0.78em; color:var(--text-dim); }}
    .cat-budget.over {{ color:var(--red); font-weight:700; }}
    .cat-item.over-budget {{ background:rgba(224,90,90,0.09); }}
    .cat-total {{ font-weight:700; font-size:0.9em; }}
    .cat-details {{ list-style:none; padding:8px 14px 10px; border-top:1px solid var(--border); display:flex; flex-direction:column; gap:5px; }}
    .cat-details.hidden {{ display:none; }}
    .det-item {{ display:flex; justify-content:space-between; align-items:baseline; font-size:0.82em; color:var(--text-mid); padding:2px 0; }}
    .det-text {{ flex:1; padding-right:10px; }}
    .det-amt {{ font-weight:600; flex-shrink:0; }}
</style>
</head>
<body>
<header>
    <button class="menu-btn" onclick="toggleMenu(event)">⚙️</button>
    <div id="extraMenu" class="nav-dropdown">
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Finanze</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/">🏠 Aggiungi Operazione</a>
                <a href="/lista">📈 Gestione Movimenti Mese</a>
                <a href="/stats">📊 Bilancio Mese</a>
                <a href="/fondo_risparmio_web">💰 Fondo Risparmio</a>
                <a href="/scadenze_web">📅 Scadenze del Mese</a>
                <a href="/fairshare_web">⚖️ FairShare</a>
                <a href="/menu_esplora">🔍 Esplora</a>
                <a href="/grafici_web">📅 Grafici e Statistiche</a>
                <a href="/gestione_categorie">⚙️ Gestione Categorie</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Casa</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/utenze?anno={datetime.date.today().year}">💧 Utenze</a>
                <a href="/consultazione_supermercati">🛒 Gestione Supermercati</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Documenti</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/documenti_pdf_web">🗄️ Documenti Contabili</a>
                <a href="/documenti_personali_web">🗄️ Documenti Personali</a>
            </div>
        </div>
        <div class="nav-group">
            <button class="nav-group-btn" onclick="toggleNavGroup(this, event)"><span>Sistema</span><span class="nav-arrow">▶</span></button>
            <div class="nav-group-items">
                <a href="/info_sys_web">📡 Monitor Server</a>
                <a href="/cambia_pw_web">🔑 Cambia Password</a>
                <a href="/webauthn_web">👆 Biometrico</a>
                <a href="/cambia_profilo_web">👤 Cambia Profilo</a>
                <a href="/logoff">🔓 Logout</a>
            </div>
        </div>
    </div>
    <div class="header-title">⚖️ Andamento Mensile</div>
    <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Cambia tema">🌙</button>
</header>
<main>
    <div class="stats-card">
        <div class="stats-title">📊 {titolo_mese} {meteo_saldo}</div>
        <div class="stats-grid">
            <div class="stat-box">
                <span class="stat-label">Entrate</span>
                <span class="stat-val amt-income">€ +{_fmt_it(entrate)}</span>
            </div>
            <div class="stat-box">
                <span class="stat-label">Uscite</span>
                <span class="stat-val amt-expense">€ -{_fmt_it(uscite)}</span>
            </div>
        </div>
        <div class="saldo-row">
            <div class="saldo-label">Saldo attuale</div>
            <div class="saldo-val" style="color:{saldo_colore};">€ {segno_saldo}{_fmt_it(saldo)}</div>
        </div>
    </div>
    <button type="button" class="sec-toggle" onclick="toggleSec('usciteCatContent', this)">
        <span>🧮 Uscite per Categoria</span>
        <span class="sec-arrow">▶</span>
    </button>
    <div id="usciteCatContent" class="collapsible-content">
        {categorie_uscite_html}
    </div>
    <button type="button" class="sec-toggle" onclick="toggleSec('entrateCatContent', this)">
        <span>📥 Entrate per Categoria</span>
        <span class="sec-arrow">▶</span>
    </button>
    <div id="entrateCatContent" class="collapsible-content">
        {categorie_entrate_html}
    </div>
    <a href="/" class="btn-home">🏠 Torna alla Home</a>
</main>
<script>
    function applyTheme(t) {{
        const root = document.documentElement;
        const btn  = document.getElementById('themeBtn');
        if (t === 'light') {{ root.classList.add('light'); if (btn) btn.textContent = '🌙'; }}
        else               {{ root.classList.remove('light'); if (btn) btn.textContent = '☀️'; }}
    }}
    function toggleTheme() {{
        const next = (localStorage.getItem('theme') || 'dark') === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        applyTheme(next);
    }}
    applyTheme(localStorage.getItem('theme') || 'dark');
    function toggleNavGroup(btn, ev) {{
        if (ev) ev.stopPropagation();
        const items = btn.nextElementSibling;
        const giaAperto = items.classList.contains('open');
        btn.closest('.nav-dropdown').querySelectorAll('.nav-group-items.open').forEach(function(el) {{
            el.classList.remove('open');
            el.previousElementSibling.querySelector('.nav-arrow').textContent = '▶';
        }});
        if (!giaAperto) {{
            items.classList.add('open');
            btn.querySelector('.nav-arrow').textContent = '▼';
        }}
    }}
    function toggleMenu(e) {{
        e.stopPropagation();
        const m = document.getElementById("extraMenu");
        m.style.display = m.style.display === "block" ? "none" : "block";
    }}
    document.addEventListener("click", function(e) {{
        const m = document.getElementById("extraMenu");
        const btn = document.querySelector(".menu-btn");
        if (m && m.style.display === "block" && !m.contains(e.target) && e.target !== btn)
            m.style.display = "none";
    }});
    function toggleSec(id, btn) {{
        const c = document.getElementById(id);
        const a = btn.querySelector(".sec-arrow");
        const open = c.classList.toggle("active");
        if (a) a.style.transform = open ? "rotate(90deg)" : "rotate(0deg)";
    }}
    function toggleCat(id, btn) {{
        const c = document.getElementById(id);
        const a = btn.querySelector(".cat-arrow");
        c.classList.toggle("hidden");
        if (a) a.classList.toggle("open");
    }}
</script>
</body>
</html>"""

# Html Form Modifica Voce esistente (data/categoria/descrizione/importo/conto)
def modifica_voce_form(self, params):
    import __main__ as _app
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    from datetime import datetime
    data_str = params.get("data", [""])[0]
    idx = int(params.get("idx", ["0"])[0])
    provenienza = params.get("from", ["/lista"])[0]
    d_obj = datetime.strptime(data_str, "%d-%m-%Y").date()
    data_html = d_obj.strftime("%Y-%m-%d")
    if d_obj not in self.spese or idx >= len(self.spese[d_obj]):
        return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
        <meta http-equiv="refresh" content="2;url={provenienza}">
        <title>Errore</title></head><body style="background:#050505;color:#e05a5a;font-family:sans-serif;padding:2rem;">
        ⚠️ Voce non trovata (indice obsoleto). Reindirizzamento in corso...</body></html>"""
    voce = self.spese[d_obj][idx]
    categoria_corrente, descrizione, importo, tipo = voce[:4]
    categorie_options = "\n".join(
        f"<option value='{c}' {'selected' if c == categoria_corrente else ''}>{c}</option>"
        for c in sorted(self.categorie)
    )
    _conto_corrente = campo(voce, "conto", "")
    if not _conto_corrente:
        try:
            _conto_corrente = self._trova_conto_da_portafoglio(d_obj, round(float(importo), 2), tipo)
        except Exception:
            _conto_corrente = ""
    if not _conto_corrente:
        _conto_corrente = "(nessuno)"
    try:
        with open(PORTAFOGLIO_BANCARIO, "r", encoding="utf-8") as _pf:
            _db_portaf_m = json.load(_pf)
        _conti_lista_m = _db_portaf_m.get("conti", [])
        conti_options_mod = '<option value="">(nessuno)</option>\n' + "\n".join(
            f'<option value="{c.get("nome","")}" {"selected" if c.get("nome","") == _conto_corrente else ""}>'
            f'{c.get("nome","")}\u2002(\u20ac {_fmt_it(float(c.get("saldo",0)))})</option>'
            for c in _conti_lista_m
        )
        mostra_conto_mod = "block" if _conti_lista_m else "none"
    except Exception:
        conti_options_mod = '<option value="">(nessuno)</option>'
        mostra_conto_mod = "none"
    _metodo_corrente = campo(voce, "metodo_pagamento", "")
    metodo_options_mod = '<option value="">— (nessuno)</option>\n' + "\n".join(
        f'<option value="{m}" {"selected" if m == _metodo_corrente else ""}>{m}</option>'
        for m in METODI_PAGAMENTO
    )
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>✏️ Modifica Voce</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<script>
    (function() {{
        if (localStorage.getItem('theme') === 'light')
            document.documentElement.classList.add('light');
    }})();
</script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>
    :root {{
        --bg:#050505; --surface:#0f0f0f; --surface2:#161616; --surface3:#1e1e1e;
        --border:rgba(255,255,255,0.07); --border-active:rgba(99,160,240,0.5);
        --gold:#c9a84c; --blue:#63a0f0; --green:#4caf82; --red:#e05a5a;
        --text:#e8e8e8; --text-dim:#555; --text-mid:#888; --radius-lg:18px;
    }}
    :root.light {{
        --bg:#f5f5f0; --surface:#ffffff; --surface2:#f0efe8; --surface3:#e8e7df;
        --border:rgba(0,0,0,0.09); --border-active:rgba(61,127,212,0.5);
        --gold:#b8902a; --blue:#3d7fd4; --green:#3a9068; --red:#cc3333;
        --text:#1a1a1a; --text-dim:#999; --text-mid:#555;
    }}
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{
        font-family:'DM Sans',sans-serif; background:var(--bg); color:var(--text);
        min-height:100vh; display:flex; align-items:center; justify-content:center;
        padding:20px; transition:background 0.3s,color 0.3s;
        background-image:
            radial-gradient(ellipse 60% 40% at 50% -10%, rgba(99,160,240,0.07) 0%, transparent 70%),
            radial-gradient(ellipse 40% 30% at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 60%);
    }}
    .card {{
        width:100%; max-width:440px;
        background:var(--surface); border:1px solid var(--border);
        border-radius:var(--radius-lg); overflow:hidden;
        box-shadow:0 30px 80px rgba(0,0,0,0.6);
        animation:fadeIn 0.3s ease;
    }}
    @keyframes fadeIn {{ from {{ opacity:0; transform:translateY(10px); }} to {{ opacity:1; transform:translateY(0); }} }}
    .card::before {{
        content:''; display:block; height:2px;
        background:linear-gradient(90deg, transparent, var(--gold), var(--blue), transparent);
    }}
    .card-head {{
        padding:16px 20px 14px; border-bottom:1px solid var(--border);
        font-family:'DM Sans',sans-serif; font-size:1em; font-weight:800;
        text-align:center; color:var(--text);
    }}
    .card-body {{ padding:18px 20px 20px; }}
    .form-group {{ margin-bottom:12px; }}
    label {{
        display:block; font-size:0.65em; font-weight:700; color:var(--text-dim);
        letter-spacing:1.8px; text-transform:uppercase; margin-bottom:6px;
    }}
    input, select {{
        width:100%; padding:10px 13px; background:var(--surface2);
        border:1px solid var(--border); border-radius:9px; color:var(--text);
        font-family:'DM Sans',sans-serif; font-size:0.92em;
        outline:none; transition:all 0.2s; -webkit-appearance:none; appearance:none;
    }}
    input:focus, select:focus {{
        border-color:var(--border-active); background:var(--surface3);
        box-shadow:0 0 0 3px rgba(99,160,240,0.07);
    }}
    input[type="date"]::-webkit-calendar-picker-indicator {{ filter:invert(0.5); }}
    select {{
        background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='7' viewBox='0 0 12 7'%3E%3Cpath fill='none' stroke='%23555' stroke-width='1.5' d='M1 1l5 5 5-5'/%3E%3C/svg%3E");
        background-repeat:no-repeat; background-position:right 12px center;
        padding-right:32px; cursor:pointer;
    }}
    select option {{ background:var(--surface2); color:var(--text); }}
    .form-row {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
    .btn-save {{
        width:100%; padding:13px; margin-top:6px; border:none;
        background:linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color:#000; border-radius:9px;
        font-family:'DM Sans',sans-serif; font-size:0.95em; font-weight:700;
        line-height:1.5; letter-spacing:0.5px; cursor:pointer; transition:all 0.2s;
    }}
    .btn-save:hover {{ transform:translateY(-1px); box-shadow:0 6px 20px rgba(201,168,76,0.25); }}
    .btn-cancel {{
        display:block; text-align:center; padding:12px; margin-top:8px;
        background:var(--surface2); border:1px solid var(--border);
        color:var(--text-mid); border-radius:9px; text-decoration:none;
        font-family:'DM Sans',sans-serif; font-weight:700; font-size:0.88em;
        line-height:1.5; transition:all 0.2s;
    }}
    .btn-cancel:hover {{ border-color:var(--border-active); color:var(--text); }}
</style>
<script>
    function applyTheme(t) {{
        document.documentElement.classList.toggle('light', t === 'light');
    }}
    applyTheme(localStorage.getItem('theme') || 'dark');
</script>
</head>
<body>
<div class="card">
    <div class="card-head">✏️ Modifica Voce</div>
    <div class="card-body">
        <form method="post" action="/salva_modifica">
            <input type="hidden" name="vecchia_data" value="{data_str}">
            <input type="hidden" name="vecchio_idx" value="{idx}">
            <input type="hidden" name="provenienza" value="{provenienza}">

            <div class="form-row">
                <div class="form-group">
                    <label>Data</label>
                    <input name="nuova_data" type="date" value="{data_html}" required>
                </div>
                <div class="form-group">
                    <label>Tipo</label>
                    <select name="tipo">
                        <option value="Entrata" {"selected" if tipo == "Entrata" else ""}>Entrata</option>
                        <option value="Uscita"  {"selected" if tipo != "Entrata" else ""}>Uscita</option>
                    </select>
                </div>
            </div>

            <div class="form-group">
                <label>Categoria</label>
                <select name="categoria" required>{categorie_options}</select>
            </div>

            <div class="form-group">
                <label>Descrizione</label>
                <input name="descrizione" type="text" value="{descrizione}">
            </div>

            <div class="form-group">
                <label>Importo (€)</label>
                <input name="importo" type="number" step="0.01" value="{importo}" required>
            </div>

            <div class="form-group" id="conto_group_mod" style="display:{mostra_conto_mod}">
                <label>Conto</label>
                <select name="conto">
                    {conti_options_mod}
                </select>
            </div>

            <div class="form-group">
                <label>Metodo Pagamento</label>
                <select name="metodo">
                    {metodo_options_mod}
                </select>
            </div>

            <button type="submit" class="btn-save">💾 Salva Modifiche</button>
        </form>
        <a href="{provenienza}" class="btn-cancel">🔙 Annulla</a>
    </div>
</div>
</body>
</html>"""


def cancella_voce_web(self, giorno_str, idx):
    try:
        data_obj = datetime.datetime.strptime(giorno_str, "%d-%m-%Y").date()
        if data_obj in self.spese:
            if 0 <= idx < len(self.spese[data_obj]):
                voce_rimossa = self.spese[data_obj].pop(idx)
                self.annulla_azione_gamification("movimento")
                if not self.spese[data_obj]:
                    del self.spese[data_obj]
                self.save_db()
                self._sync_fairshare_e_aggiorna()
                self.carica_db_web()
                self.refresh_gui()
                return True
    except Exception as e:
        print(f"Errore dati cancellazione: {e}")
    return False


def aggiungi_voce_web(self, voce):
    import __main__ as _app
    DB_FILE = _app.DB_FILE
    PORTAFOGLIO_BANCARIO = _app.PORTAFOGLIO_BANCARIO
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            dati = json.load(f)
    except Exception:
        dati = {"spese": []}
    try:
        d_obj = datetime.datetime.strptime(voce["date"], "%Y-%m-%d").date()
        data_str = d_obj.strftime("%d-%m-%Y")
    except Exception as e:
        print(f"Data non valida: {voce['date']} → {e}")
        return
    try:
        voce_normalizzata = SpesaEntry.da_dict({
            "categoria":   voce.get("categoria", ""),
            "descrizione": voce.get("descrizione", ""),
            "importo":     voce.get("importo", 0.0),
            "tipo":        voce.get("tipo", "Uscita"),
            "id_ricorrenza": voce.get("id_ricorrenza"),
            "id_spesa":    voce.get("id_spesa"),
            "conto":       voce.get("conto", ""),
            "ora":         voce.get("ora") or datetime.datetime.now().strftime("%H:%M"),
            "hashtag":     voce.get("hashtag", []),
            "metodo_pagamento": voce.get("metodo_pagamento", ""),
        }).a_dict()
        voce_normalizzata["date"] = data_str
        voce = voce_normalizzata
    except Exception as e:
        print(f"[aggiungi_voce_web] Normalizzazione fallita, uso voce originale: {e}")
        voce["date"] = data_str
    for giorno in dati["spese"]:
        if giorno["date"] == data_str:
            giorno["entries"].append(voce)
            break
    else:
        dati["spese"].append({
            "date": data_str,
            "entries": [voce]
        })
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(dati, f, indent=2, ensure_ascii=False)
    self.carica_db_web()
    self.registra_azione_gamification("movimento")
    self.refresh_gui()
 
def carica_db_web(self):
    import __main__ as _app
    DB_FILE = _app.DB_FILE
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            dati = json.load(f)
    except Exception as e:
        print(f"Errore lettura DB: {e}")
        return
    self.spese = {}
    for giorno in dati.get("spese", []):
        try:
            d = datetime.datetime.strptime(giorno["date"], "%d-%m-%Y").date()
            entries = [SpesaEntry.da_dict(e) for e in giorno["entries"]]
            self.spese[d] = entries
        except Exception as ex:
            print(f"Errore parsing giorno {giorno.get('date')}: {ex}")

def analizza_pdf_web(self, pdf_bytes, filename_originale="documento.pdf"):
    import __main__ as _app
    API_KEY = _app.API_KEY
    DOC_DIR = _app.DOC_DIR
    GEMINI = _app.GEMINI
    LOG_IMPORTAZIONI = _app.LOG_IMPORTAZIONI
    REGISTRY_FILE = _app.REGISTRY_FILE
    genai_client = _app.genai_client
    types = _app.types
    import re, json, shutil
    from datetime import datetime
    CATEGORIA_PDF = "Zona @Web/Bank"
    if CATEGORIA_PDF not in self.categorie:
        self.categorie.append(CATEGORIA_PDF)
        self.categorie_tipi[CATEGORIA_PDF] = "Uscita"
        self.aggiorna_combobox_categorie()
    if not os.path.exists(DOC_DIR):
        os.makedirs(DOC_DIR)
    client = genai_client.Client(api_key=API_KEY)
    lista_cat = ", ".join(f'"{c}"' for c in self.categorie)
    prompt = (
        f"Analizza questo documento PDF.\n"
        f"PRIMA DI TUTTO: se il documento è un estratto conto bancario, lista movimenti bancari, "
        f"rendiconto con più di 3 transazioni elencate in tabella, o qualsiasi documento che "
        f"riepiloga più operazioni finanziarie distinte, restituisci SOLO questo JSON:\n"
        f'{{\"tipo_documento\": \"estratto_conto\"}}\n'
        f"Altrimenti, se è una singola fattura, ricevuta, cedolino, scontrino o documento con UN SOLO importo principale, estrai:\n"
        f'{{\"tipo_documento\": \"singolo\", \"importo\": float, \"azienda\": \"nome\", '
        f'\"data\": \"YYYY-MM-DD\", '
        f'\"fattura\": \"numero o null\", \"direzione\": \"Entrata/Uscita\", '
        f'\"scadenza\": \"GG/MM/YYYY o null\", '
        f'\"categoria\": \"categoria più adatta tra [{lista_cat}]\"}}\n'
        f"REGOLE:\n"
        f"1. Se non trovi l'importo scrivi 0.01.\n"
        f"2. Determina Entrata o Uscita dal contesto. Un cedolino pensione, uno stipendio "
        f"o un accredito/bonifico ricevuto sono sempre un'ENTRATA, mai un'Uscita.\n"
        f"3. Per il campo 'azienda': se è una bolletta/fattura usa il nome del fornitore; "
        f"se è un cedolino pensione o stipendio, usa SEMPRE e SOLO la dicitura "
        f"\"prestazione rata MM/AAAA\" con il mese e l'anno di competenza della rata — NON "
        f"il nome del beneficiario, NON il numero di prestazione/pratica. Nessuna emoji o "
        f"prefisso in 'azienda'.\n"
        f"4. Per la data usa quella del fatto economico (data valuta, data pagamento, "
        f"data emissione/fattura, scadenza/competenza), MAI la data di stampa/generazione "
        f"del documento (es. \"Stampa elaborata il\", \"Generato il\"); se non leggibile "
        f"usa la data odierna.\n"
        f"5. Restituisci SOLO il JSON, senza testo aggiuntivo né backtick."
    )
    r = client.models.generate_content(
        model=GEMINI,
        contents=[
            types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
            prompt
        ]
    )
    raw = r.text.strip().replace("```json", "").replace("```", "").strip()
    dati = json.loads(raw)
    if dati.get("tipo_documento") == "estratto_conto":
        return {"ok": False, "errore": "Estratto conto non supportato — usa Importa Movimenti dal menu principale."}
    importo   = float(dati.get("importo") or 0.01)
    azienda   = str(dati.get("azienda") or "Documento").strip()
    fattura   = dati.get("fattura")
    direzione = dati.get("direzione") or "Uscita"
    scadenza  = dati.get("scadenza")
    cat_ia    = dati.get("categoria", "")
    categoria = cat_ia if cat_ia in self.categorie else CATEGORIA_PDF
    data_str_ia = dati.get("data")
    _testo_web = ""
    try:
        import pymupdf as _fitz_web
        _doc_web = _fitz_web.open(stream=pdf_bytes, filetype="pdf")
        _testo_web = "".join(p.get_text() for p in _doc_web).lower()
        _doc_web.close()
        for _pat in (
            r"data\s+valuta\s*:?\s*(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})",
            r"data\s+pagamento\s*:?\s*(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})",
            r"data\s+scadenza\s*:?\s*(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})",
            r"data\s+emissione\s*:?\s*(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})",
        ):
            _m = re.search(_pat, _testo_web)
            if _m:
                _gg, _mm, _aaaa = _m.groups()
                if len(_aaaa) == 2:
                    _aaaa = "20" + _aaaa
                data_str_ia = f"{_aaaa}-{int(_mm):02d}-{int(_gg):02d}"
                break
    except Exception:
        pass
    try:
        data_oggi = datetime.strptime(data_str_ia, "%Y-%m-%d").date()
    except Exception:
        data_oggi = datetime.now().date()
    _m_pens = re.search(r"prestazione\s+rata\s+(\d{1,2})[/\-](\d{2,4})", _testo_web) if _testo_web else None
    if _m_pens:
        _mm_p, _aaaa_p = _m_pens.groups()
        if len(_aaaa_p) == 2:
            _aaaa_p = "20" + _aaaa_p
        desc      = f"prestazione rata {int(_mm_p):02d}/{_aaaa_p}"
        direzione = "Entrata"
    else:
        desc = azienda
        if fattura: desc += f" {fattura}"
        if scadenza and scadenza != "null": desc += f" SCD:{scadenza}"
    desc_spesa = f"ALL· {desc}"
    for s in self.spese.get(data_oggi, []):
        if s[1] in (desc_spesa, desc) and abs(s[2] - importo) < 0.01:
            return {"ok": False, "errore": "Movimento già presente (duplicato)"}
    def _san(s, n=30):
        return re.sub(r'[^\w\.-]', '', s.strip().replace(' ', '_').upper())[:n]
    data_ggmmaaaa   = data_oggi.strftime("%d%m%Y")
    imp_centesimi   = int(round(importo * 100))
    nome_reg        = f"{data_ggmmaaaa}_{_san(desc)}_{direzione}_{_san(categoria)}_{imp_centesimi}.pdf"
    percorso_doc    = os.path.join(DOC_DIR, nome_reg)
    with open(percorso_doc, "wb") as f:
        f.write(pdf_bytes)
    cartella_pdf = os.path.join(os.getcwd(), "Fatture_GMail")
    if not os.path.exists(cartella_pdf):
        os.makedirs(cartella_pdf)
    azienda_safe  = re.sub(r'[\\/*?:"<>|]', "-", azienda).strip()
    fattura_safe  = re.sub(r'[\\/*?:"<>|]', "-", str(fattura or "mancante")).strip()
    nome_fattura  = f"{data_oggi.strftime('%d-%m-%Y')}_{azienda_safe}_fatt_{fattura_safe}.pdf"
    shutil.copy2(percorso_doc, os.path.join(cartella_pdf, nome_fattura))
    try:
        with open(REGISTRY_FILE, 'r', encoding='utf-8') as rf:
            registry = json.load(rf)
    except Exception:
        registry = {}
    registry[nome_reg] = {
        "data_raw":           data_ggmmaaaa,
        "categoria_esatta":   categoria,
        "descrizione_esatta": desc_spesa,
        "importo_raw":        imp_centesimi,
        "tipo_esatto":        direzione,
        "timestamp":          datetime.now().isoformat()
    }
    with open(REGISTRY_FILE, 'w', encoding='utf-8') as rf:
        json.dump(registry, rf, indent=4, ensure_ascii=False)
    self.spese.setdefault(data_oggi, []).append(SpesaEntry.nuova(categoria, desc_spesa, importo, direzione))
    self.save_db()
    self.after(0, self.refresh_gui)
    with open(LOG_IMPORTAZIONI, "a", encoding="utf-8") as log:
        log.write(
            f"{datetime.now().strftime('%d/%m/%Y %H:%M'):<17} | {'WEB-PDF':<8} | "
            f"{data_oggi.strftime('%d/%m/%Y'):<10} | {desc_spesa:<50} | "
            f"{_app._fmt_it(abs(importo)):>10} € | {direzione:<7} | {categoria}\n"
        )
    return {
        "ok":        True,
        "azienda":   azienda,
        "importo":   importo,
        "direzione": direzione,
        "categoria": categoria,
        "desc":      desc_spesa,
        "data":      data_oggi.strftime("%d/%m/%Y")
    }

def ricalcola_operazioni_web(self):
    contatore = 0
    categoria_target = "Zona @Web/Bank" 
    for entries in self.spese.values():
        for e in entries:
            if e[0] == categoria_target:
                contatore += 1
    self.operazioni_scaricate_sessione = contatore
    contatore_pdf = 0
    path_pdf = os.path.join(os.getcwd(), "Fatture_GMail")
    if os.path.exists(path_pdf):
        contatore_pdf = len([f for f in os.listdir(path_pdf) if f.lower().endswith('.pdf')])
    def applica_stato_visivo():
        if hasattr(self, 'lbl_sync_count_widget') and self.lbl_sync_count_widget.winfo_exists():
            try:
                self.lbl_sync_count_widget.config(text=f" Sync: {self.operazioni_scaricate_sessione}")
                if self.operazioni_scaricate_sessione > 0 or contatore_pdf > 0:
                    colore_stato = self.COLOR_RED
                else:
                    colore_stato = self.COLOR_GREEN
                if hasattr(self, 'btn_open_pdf_folder'):
                    self.btn_open_pdf_folder.config(foreground=colore_stato)
                self.lbl_sync_count_widget.config(foreground=colore_stato)
            except:
                pass
    if hasattr(self, 'lbl_sync_count_widget') and self.lbl_sync_count_widget.winfo_exists():
        applica_stato_visivo()
    else:
        self.after(200, applica_stato_visivo)
 
def notifica_modifica_web(self):
    import __main__ as _app
    UDP_PORT_1 = _app.UDP_PORT_1
    UDP_PORT_2 = _app.UDP_PORT_2
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        messaggio = f"REFRESH_NOW|{self.SESSION_ID}".encode('utf-8')
        for porta in [UDP_PORT_1, UDP_PORT_2]:
            sock.sendto(messaggio, ('255.255.255.255', porta))
        sock.close()
    except Exception as e:
        print(f"Errore invio: {e}")

def pianifica_sincro_web(self):
    import __main__ as _app
    SYNC_INT_MIN = _app.SYNC_INT_MIN
    from datetime import datetime
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Avvio sincronizzazione web automatica...")
        threading.Thread(target=self._esegui_sincro_thread, daemon=True).start()
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Errore durante il trigger della sincronizzazione: {e}")
    SYNC_INTERVALLO_MS = SYNC_INT_MIN * 60 * 1000
    self.after(SYNC_INTERVALLO_MS, self.pianifica_sincro_web)
