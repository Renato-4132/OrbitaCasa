#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import datetime
import webbrowser


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
            tk_app.refresh_portafoglio_web()
            return redirect("/?salvato=1", code=303)
        return redirect("/", code=303)

    @flask_app.route("/gestione_categorie")
    @richiede_login
    def gestione_categorie():
        return html_resp(tk_app.html_gestione_categorie())

    @flask_app.route("/stats")
    @richiede_login
    def stats():
        conto_sel = request.args.get("conto", "")
        return html_resp(tk_app.stats_mensili_html(conto_sel))

    @flask_app.route("/lista")
    @richiede_login
    def lista():
        conto_sel = request.args.get("conto", "")
        return html_resp(tk_app.html_lista_spese_mensili(conto_sel))

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
        conto_sel = request.args.get("conto", "")
        return html_resp(tk_app.pagina_grafici_web(conto_sel))

    @flask_app.route("/portafoglio_web")
    @richiede_login
    def portafoglio_web():
        return html_resp(tk_app.pagina_portafoglio_web())

    @flask_app.route("/portafoglio_web/salva_conto", methods=["POST"])
    @richiede_login
    def portafoglio_salva_conto():
        from urllib.parse import quote
        p = {k: [v] for k, v in request.form.items()}
        errore = tk_app.salva_conto_web(p)
        aggiorna_ui()
        if errore:
            return redirect(f"/portafoglio_web?errore={quote(errore)}#conti", code=303)
        return redirect("/portafoglio_web#conti", code=303)

    @flask_app.route("/portafoglio_web/elimina_conto", methods=["POST"])
    @richiede_login
    def portafoglio_elimina_conto():
        p = {k: [v] for k, v in request.form.items()}
        tk_app.elimina_conto_web(p)
        aggiorna_ui()
        return redirect("/portafoglio_web#conti", code=303)

    @flask_app.route("/portafoglio_web/salva_trasferimento", methods=["POST"])
    @richiede_login
    def portafoglio_salva_trasferimento():
        p = {k: [v] for k, v in request.form.items()}
        tk_app.salva_trasferimento_web(p)
        aggiorna_ui()
        return redirect("/portafoglio_web#trasferimenti", code=303)

    @flask_app.route("/portafoglio_web/elimina_trasferimento", methods=["POST"])
    @richiede_login
    def portafoglio_elimina_trasferimento():
        p = {k: [v] for k, v in request.form.items()}
        tk_app.elimina_trasferimento_web(p)
        aggiorna_ui()
        return redirect("/portafoglio_web#trasferimenti", code=303)

    @flask_app.route("/api/dati_saldo")
    @richiede_login
    def api_dati_saldo():
        conto = request.args.get("conto", "").strip()
        return Response(tk_app.get_dati_saldo_json(conto or None), mimetype="application/json")

    @flask_app.route("/api/dati_saldo_annuale")
    @richiede_login
    def api_dati_saldo_annuale():
        conto = request.args.get("conto", "").strip()
        return Response(tk_app.get_dati_saldo_annuale_json(conto or None), mimetype="application/json")

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
        tk_app.refresh_portafoglio_web()
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
        tk_app.refresh_portafoglio_web()
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
    aggiungi_rotte_webauthn(flask_app, tk_app, richiede_login, html_resp, get_ip)

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

# Html Info sistema
def html_info_sys(self):
    import __main__ as _app
    DB_FILE = _app.DB_FILE
    LOGIN_WEB = _app.LOGIN_WEB
    NAME = _app.NAME
    VERSION = _app.VERSION
    import shutil, multiprocessing, datetime, platform, os, json
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
                <a href="/portafoglio_web">🏦 Portafoglio Bancario</a>
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
