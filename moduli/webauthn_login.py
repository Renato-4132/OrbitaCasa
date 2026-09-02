#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import base64
import datetime
import threading

_LOCK = threading.Lock()

def _carica_credenziali(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _salva_credenziali(path, lista):
    with _LOCK:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(lista, f, indent=2, ensure_ascii=False)

def _b64u(dato_bytes):
    return base64.urlsafe_b64encode(dato_bytes).decode().rstrip("=")

def _da_b64u(s):
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + padding)

def aggiungi_rotte_webauthn(flask_app, tk_app, richiede_login, html_resp, get_ip, request_module):
    try:
        import webauthn
        from webauthn import (
            generate_registration_options, verify_registration_response,
            generate_authentication_options, verify_authentication_response,
        )
        from webauthn.helpers.structs import (
            PublicKeyCredentialDescriptor, AuthenticatorSelectionCriteria,
            UserVerificationRequirement, ResidentKeyRequirement,
            RegistrationCredential, AuthenticationCredential,
            AuthenticatorAttachment,
        )
        from webauthn.helpers import parse_registration_credential_json, parse_authentication_credential_json
        LIBRERIA_OK = True
    except ImportError:
        LIBRERIA_OK = False

    from flask import request, Response, redirect, make_response

    import __main__ as _app
    CREDENTIALS_FILE = _app.CREDENTIALS_FILE

    def _rp_id_e_origin():
        host_intero = request.host
        rp_id = host_intero.split(":")[0]
        origin = f"{request.scheme}://{host_intero}"
        return rp_id, origin

    @flask_app.route("/webauthn/supportato")
    def webauthn_supportato():
        return Response(
            json.dumps({"ok": LIBRERIA_OK}),
            mimetype="application/json",
        )

    @flask_app.route("/webauthn/registra/opzioni")
    @richiede_login
    def webauthn_registra_opzioni():
        if not LIBRERIA_OK:
            return Response(json.dumps({"ok": False, "errore": "Libreria 'webauthn' non installata sul server."}),
                             status=500, mimetype="application/json")
        rp_id, _ = _rp_id_e_origin()
        credenziali_note = _carica_credenziali(CREDENTIALS_FILE)
        escludi = [
            PublicKeyCredentialDescriptor(id=bytes(_da_b64u(c["credential_id"])))
            for c in credenziali_note
        ]
        opzioni = generate_registration_options(
            rp_id=rp_id,
            rp_name="OrbitaCasa",
            user_id=b"utente-unico",
            user_name="utente",
            user_display_name="Utente OrbitaCasa",
            exclude_credentials=escludi,
            authenticator_selection=AuthenticatorSelectionCriteria(
                authenticator_attachment=AuthenticatorAttachment.PLATFORM,
                resident_key=ResidentKeyRequirement.PREFERRED,
                user_verification=UserVerificationRequirement.REQUIRED,
            ),
        )
        tk_app._webauthn_challenge = opzioni.challenge
        return Response(webauthn.options_to_json(opzioni), mimetype="application/json")

    @flask_app.route("/webauthn/registra/verifica", methods=["POST"])
    @richiede_login
    def webauthn_registra_verifica():
        if not LIBRERIA_OK:
            return Response(json.dumps({"ok": False, "errore": "Libreria mancante."}),
                             status=500, mimetype="application/json")
        rp_id, origin = _rp_id_e_origin()
        try:
            cred = parse_registration_credential_json(request.data.decode("utf-8"))
            risultato = verify_registration_response(
                credential=cred,
                expected_challenge=tk_app._webauthn_challenge,
                expected_rp_id=rp_id,
                expected_origin=origin,
            )
        except Exception as e:
            return Response(json.dumps({"ok": False, "errore": str(e)}), status=400, mimetype="application/json")

        etichetta = request.args.get("etichetta", "").strip() or request.headers.get("User-Agent", "Dispositivo")[:60]
        credenziali = _carica_credenziali(CREDENTIALS_FILE)
        credenziali.append({
            "credential_id": _b64u(risultato.credential_id),
            "public_key": _b64u(risultato.credential_public_key),
            "sign_count": risultato.sign_count,
            "etichetta": etichetta,
            "creato": datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
        })
        _salva_credenziali(CREDENTIALS_FILE, credenziali)
        return Response(json.dumps({"ok": True}), mimetype="application/json")

    @flask_app.route("/webauthn/lista")
    @richiede_login
    def webauthn_lista():
        credenziali = _carica_credenziali(CREDENTIALS_FILE)
        return Response(
            json.dumps([{"credential_id": c["credential_id"], "etichetta": c["etichetta"], "creato": c["creato"]}
                        for c in credenziali]),
            mimetype="application/json",
        )

    @flask_app.route("/webauthn/rimuovi", methods=["POST"])
    @richiede_login
    def webauthn_rimuovi():
        cred_id = request.form.get("credential_id", "")
        credenziali = _carica_credenziali(CREDENTIALS_FILE)
        credenziali = [c for c in credenziali if c["credential_id"] != cred_id]
        _salva_credenziali(CREDENTIALS_FILE, credenziali)
        return redirect("/webauthn_web", code=303)

    @flask_app.route("/webauthn/login/opzioni")
    def webauthn_login_opzioni():
        if not LIBRERIA_OK:
            return Response(json.dumps({"ok": False, "errore": "Libreria mancante."}), status=500, mimetype="application/json")
        rp_id, _ = _rp_id_e_origin()
        credenziali_note = _carica_credenziali(CREDENTIALS_FILE)
        if not credenziali_note:
            return Response(json.dumps({"ok": False, "errore": "Nessun dispositivo registrato."}), status=404, mimetype="application/json")
        consentite = [
            PublicKeyCredentialDescriptor(id=_da_b64u(c["credential_id"]))
            for c in credenziali_note
        ]
        opzioni = generate_authentication_options(
            rp_id=rp_id,
            allow_credentials=consentite,
            user_verification=UserVerificationRequirement.REQUIRED,
        )
        tk_app._webauthn_challenge = opzioni.challenge
        return Response(webauthn.options_to_json(opzioni), mimetype="application/json")

    @flask_app.route("/webauthn/login/verifica", methods=["POST"])
    def webauthn_login_verifica():
        if not LIBRERIA_OK:
            return Response(json.dumps({"ok": False, "errore": "Libreria mancante."}), status=500, mimetype="application/json")
        rp_id, origin = _rp_id_e_origin()
        try:
            cred = parse_authentication_credential_json(request.data.decode("utf-8"))
        except Exception as e:
            return Response(json.dumps({"ok": False, "errore": f"Dati non validi: {e}"}), status=400, mimetype="application/json")

        credenziali = _carica_credenziali(CREDENTIALS_FILE)
        cred_id_richiesta = _b64u(cred.raw_id)
        trovata = next((c for c in credenziali if c["credential_id"] == cred_id_richiesta), None)
        if not trovata:
            return Response(json.dumps({"ok": False, "errore": "Dispositivo non riconosciuto."}), status=401, mimetype="application/json")

        try:
            risultato = verify_authentication_response(
                credential=cred,
                expected_challenge=tk_app._webauthn_challenge,
                expected_rp_id=rp_id,
                expected_origin=origin,
                credential_public_key=_da_b64u(trovata["public_key"]),
                credential_current_sign_count=trovata["sign_count"],
                require_user_verification=True,
            )
        except Exception as e:
            return Response(json.dumps({"ok": False, "errore": str(e)}), status=401, mimetype="application/json")

        # Aggiorna il contatore anti-clonazione della chiave usata
        trovata["sign_count"] = risultato.new_sign_count
        _salva_credenziali(CREDENTIALS_FILE, credenziali)

        import time
        ip = get_ip()
        ua = request.headers.get("User-Agent", "sconosciuto")
        tk_app.registra_accesso(ip=ip, user_agent=f"{ua} (biometrico: {trovata['etichetta']})")
        tk_app.ultimo_accesso_web = time.time()
        resp = make_response(Response(json.dumps({"ok": True}), mimetype="application/json"))
        import __main__ as _app
        resp.set_cookie(f"session_id_{_app.PORTA}", tk_app.web_token,
                         max_age=tk_app.timeout_sessione,
                         httponly=True, samesite="Strict", secure=request.is_secure)
        return resp

    @flask_app.route("/webauthn_web")
    @richiede_login
    def webauthn_web():
        return html_resp(tk_app.html_webauthn_web())

def html_webauthn_web(self):
    import __main__ as _app
    NAME = _app.NAME
    credenziali = _carica_credenziali(_app.CREDENTIALS_FILE)
    righe = ""
    for c in credenziali:
        righe += f"""
            <div class="device-row">
                <div>
                    <div class="device-nome">👆 {c['etichetta']}</div>
                    <div class="device-data">Registrato il {c['creato']}</div>
                </div>
                <form method="post" action="/webauthn/rimuovi" onsubmit="return confirm('Rimuovere questo dispositivo?');">
                    <input type="hidden" name="credential_id" value="{c['credential_id']}">
                    <button type="submit" class="btn-rimuovi">Rimuovi</button>
                </form>
            </div>"""
    if not righe:
        righe = '<div class="device-vuoto">Nessun dispositivo biometrico registrato.</div>'

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>🔐 Accesso Biometrico — {NAME}</title>
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
        width: 100%; max-width: 440px;
        background: var(--surface); border: 1px solid var(--border);
        border-radius: var(--radius-lg); overflow: hidden; position: relative;
        box-shadow: 0 20px 60px rgba(0,0,0,0.6); animation: fadeIn 0.3s ease;
        margin-top: 0;
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
    .body-pad {{ padding: 20px; }}
    .sub {{ color: var(--text-mid); font-size: 0.82em; margin-bottom: 16px; line-height: 1.4; }}
    .device-row {{
        display: flex; justify-content: space-between; align-items: center;
        background: var(--surface2); border: 1px solid var(--border);
        border-radius: 10px; padding: 12px 14px; margin-bottom: 8px;
    }}
    .device-nome {{ font-size: 0.88em; font-weight: 600; color: var(--text); }}
    .device-data {{ font-size: 0.75em; color: var(--text-mid); margin-top: 2px; }}
    .device-vuoto {{ color: var(--text-mid); font-size: 0.85em; padding: 14px 0; text-align: center; }}
    .btn-rimuovi {{
        background: rgba(224,90,90,0.12); color: var(--red); border: 1px solid rgba(224,90,90,0.3);
        border-radius: 8px; padding: 6px 12px; font-size: 0.75em; font-weight: 600; cursor: pointer;
        transition: all 0.15s;
    }}
    .btn-rimuovi:hover {{ background: rgba(224,90,90,0.2); }}
    .btn-registra {{
        width: 100%; padding: 13px; margin-top: 16px;
        background: linear-gradient(135deg, var(--gold) 0%, #8a6820 100%);
        color: #000; border: none; border-radius: 10px;
        font-family: 'DM Sans', sans-serif; font-size: 0.95em; font-weight: 700;
        letter-spacing: 0.5px; cursor: pointer; transition: all 0.2s;
    }}
    .btn-registra:hover {{ transform: translateY(-1px); box-shadow: 0 6px 18px rgba(201,168,76,0.25); }}
    #msg {{ font-size: 0.8em; margin-top: 10px; min-height: 18px; color: var(--text-mid); text-align: center; }}
    .footer {{ padding: 14px 20px; border-top: 1px solid var(--border); text-align: center; }}
    .back-link {{ font-size: 0.75em; color: var(--text-dim); text-decoration: none; transition: color 0.2s; }}
    .back-link:hover {{ color: var(--blue); }}
</style>
</head>
<body>
<div class="main-container">
    <div class="brand-header">
        <div class="brand-title">🔐 Accesso Biometrico</div>
        <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()">🌙</button>
    </div>
    <div class="body-pad">
        <p class="sub">Registra questo dispositivo per accedere in futuro con impronta o volto, invece della password. Richiede HTTPS oppure accesso da "localhost".</p>
        <div id="lista">{righe}</div>
        <button class="btn-registra" id="btnRegistra" onclick="registraDispositivo()">➕ Registra questo dispositivo</button>
        <div id="msg"></div>
    </div>
    <div class="footer">
        <a href="/info_sys_web" class="back-link">← Torna al Monitor</a>
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

    async function registraDispositivo() {{
        const msg = document.getElementById('msg');
        if (!window.PublicKeyCredential) {{
            msg.textContent = '⚠️ Questo browser/contesto non supporta l\\'accesso biometrico (serve HTTPS o "localhost").';
            return;
        }}
        msg.textContent = 'Attendi la richiesta del browser...';
        try {{
            const optResp = await fetch('/webauthn/registra/opzioni');
            const opts = await optResp.json();
            if (opts.errore) {{ msg.textContent = '⚠️ ' + opts.errore; return; }}
            opts.challenge = b64uToBuf(opts.challenge);
            opts.user.id = b64uToBuf(opts.user.id);
            if (opts.excludeCredentials) {{
                opts.excludeCredentials.forEach(c => c.id = b64uToBuf(c.id));
            }}
            const cred = await navigator.credentials.create({{ publicKey: opts }});
            const payload = {{
                id: cred.id,
                rawId: bufToB64u(cred.rawId),
                type: cred.type,
                response: {{
                    clientDataJSON: bufToB64u(cred.response.clientDataJSON),
                    attestationObject: bufToB64u(cred.response.attestationObject),
                }}
            }};
            const verResp = await fetch('/webauthn/registra/verifica', {{
                method: 'POST', headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(payload)
            }});
            const risultato = await verResp.json();
            if (risultato.ok) {{
                msg.textContent = '✅ Dispositivo registrato. Ricarico la pagina...';
                setTimeout(() => window.location.reload(), 900);
            }} else {{
                msg.textContent = '⚠️ ' + (risultato.errore || 'Registrazione fallita.');
            }}
        }} catch (e) {{
            if (e.name === 'InvalidStateError') {{
                msg.textContent = '⚠️ Questo dispositivo è già stato registrato.';
            }} else {{
                msg.textContent = '⚠️ ' + e.message;
            }}
        }}
    }}
</script>
</body>
</html>"""
