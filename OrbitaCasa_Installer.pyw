#!/usr/bin/env python3
"""
OrbitaCasa — Installer Web Linux/Mac/Win
Doppio clic (o: python3 OrbitaCasa_Installer.pyw)
Si apre automaticamente nel browser. Zero dipendenze.
Funziona solo con python gia' installato.
"""

import http.server, threading, webbrowser, subprocess
import sys, os, platform, urllib.request, json, time

PORT   = 7474
SO     = platform.system()
DEPS   = ["tkcalendar","google-genai","requests","segno",
          "cryptography","pystray","pymupdf","yfinance"]
PYW_URL = "https://raw.githubusercontent.com/Renato-4132/OrbitaCasa/main/OrbitaCasa.pyw"

SO_LABEL = {"Darwin":"macOS","Linux":"Linux","Windows":"Windows"}.get(SO, SO)
def _desktop():
    if SO in ("Windows", "Darwin"):
        return os.path.join(os.path.expanduser("~"), "Desktop")
    for candidate in ["Scrivania", "Desktop", "scrivania", "desktop"]:
        p = os.path.join(os.path.expanduser("~"), candidate)
        if os.path.isdir(p):
            return p
    try:
        r = subprocess.run(["xdg-user-dir", "DESKTOP"], capture_output=True, text=True)
        p = r.stdout.strip()
        if p and os.path.isdir(p):
            return p
    except Exception:
        pass
    return os.path.expanduser("~")
BASE = _desktop()
HTML = r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OrbitaCasa — Installer</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:#0f1117;color:#e0e6f0;font-family:'Segoe UI',system-ui,sans-serif;
       min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
  .card{background:#1a1f2e;border-radius:18px;width:100%;max-width:580px;
        box-shadow:0 8px 40px #0008;overflow:hidden}
  .header{background:#151b2d;padding:36px 20px 28px;text-align:center;
          border-bottom:1px solid #2a3050}
  .icon{font-size:56px;line-height:1;margin-bottom:10px}
  h1{font-size:2rem;font-weight:700;color:#fff;margin-bottom:4px}
  .subtitle{color:#6b7a9e;font-size:.95rem}
  .body{padding:32px}
  label{display:block;color:#6b7a9e;font-size:.85rem;
        font-weight:600;letter-spacing:.05em;text-transform:uppercase;margin-bottom:8px}
  .input-wrap{background:#0d1117;border:2px solid #2a3050;border-radius:10px;
              transition:border .2s;margin-bottom:6px}
  .input-wrap:focus-within{border-color:#4a90d9}
  input[type=text]{width:100%;background:transparent;border:none;outline:none;
                   color:#fff;font-size:1.25rem;font-weight:600;padding:14px 16px}
  .path-preview{color:#4a90d9;font-size:.8rem;font-family:monospace;
                margin-bottom:24px;min-height:18px;word-break:break-all}
  .btn{width:100%;padding:18px;border:none;border-radius:12px;
       font-size:1.15rem;font-weight:700;cursor:pointer;
       background:#e8a838;color:#1a1000;transition:all .15s;letter-spacing:.02em}
  .btn:hover:not(:disabled){background:#f0b84a;transform:translateY(-1px)}
  .btn:disabled{opacity:.5;cursor:not-allowed;transform:none}
  .btn.success{background:#4caf50;color:#fff}
  .divider{height:1px;background:#2a3050;margin:24px 0}
  .log-label{color:#6b7a9e;font-size:.85rem;font-weight:600;
             letter-spacing:.05em;text-transform:uppercase;margin-bottom:8px}
  .log{background:#0d1117;border-radius:10px;padding:16px;height:220px;
       overflow-y:auto;font-family:monospace;font-size:.82rem;line-height:1.7;
       border:1px solid #1e2535}
  .log .ok  {color:#4caf50}
  .log .err {color:#f44336}
  .log .warn{color:#ff9800}
  .log .info{color:#4a90d9}
  .log .dim {color:#4a5568}
  .progress{height:6px;background:#1e2535;border-radius:3px;
            margin-top:16px;overflow:hidden}
  .progress-bar{height:100%;background:#4a90d9;border-radius:3px;
                width:0%;transition:width .3s;position:relative}
  .progress-bar.anim{animation:slide 1.2s infinite linear;width:30%}
  @keyframes slide{0%{margin-left:-30%}100%{margin-left:100%}}
  .status{text-align:center;color:#6b7a9e;font-size:.85rem;margin-top:10px;min-height:18px}
  .tag{display:inline-block;padding:2px 10px;border-radius:20px;
       font-size:.75rem;font-weight:600;margin-left:8px;vertical-align:middle}
  .tag-mac{background:#2a3050;color:#8899cc}
</style>
</head>
<body>
<div class="card">
  <div class="header">
    <div class="icon">🏠</div>
    <h1>OrbitaCasa <span class="tag tag-mac">__SO__</span></h1>
    <div class="subtitle">Installer — doppio clic sul file e sei qui</div>
  </div>
  <div class="body">
    <label for="nome">① Nome Profilo</label>
    <div class="input-wrap">
      <input type="text" id="nome" value="MiaCasa" autocomplete="off"
             placeholder="Es: MiaCasa, Famiglia Rossi …" oninput="aggiorna()">
    </div>
    <div class="path-preview" id="preview"></div>
    <button class="btn" id="btn" onclick="installa()">
      ▶&nbsp;&nbsp;INSTALLA ORBITA CASA
    </button>
    <div class="divider"></div>
    <div class="log-label">② Log installazione</div>
    <div class="log" id="log">
      <span class="info">Pronto — inserisci un nome profilo e premi il pulsante arancione.</span><br>
    </div>
    <div class="progress"><div class="progress-bar" id="bar"></div></div>
    <div class="status" id="status"></div>
  </div>
</div>
<script>
const BASE = "__BASE__";
function aggiorna(){
  const n = document.getElementById("nome").value.trim();
  document.getElementById("preview").textContent =
    n ? "📁  "+BASE+"/"+n+"/OrbitaCasa.pyw" : "";
}
aggiorna();
function log(msg, cls=""){
  const d = document.getElementById("log");
  const line = document.createElement("span");
  if(cls) line.className = cls;
  line.textContent = msg;
  d.appendChild(line);
  d.appendChild(document.createElement("br"));
  d.scrollTop = d.scrollHeight;
}
function status(msg, col="#6b7a9e"){
  const s = document.getElementById("status");
  s.textContent = msg; s.style.color = col;
}
function setBar(pct, anim=false){
  const b = document.getElementById("bar");
  b.style.width = pct+"%";
  b.classList.toggle("anim", anim);
}
async function installa(){
  const nome = document.getElementById("nome").value.trim()
    .replace(/[/:*?"<>|\\\\]/g,"");
  if(!nome){
    alert("Inserisci un nome valido per il profilo.\nEsempio: MiaCasa");
    return;
  }
  document.getElementById("btn").disabled = true;
  document.getElementById("btn").textContent = "⏳  Installazione in corso…";
  document.getElementById("nome").disabled = true;
  setBar(0, true);
  const es = new EventSource("/installa?nome="+encodeURIComponent(nome));
  es.onmessage = e => {
    const d = JSON.parse(e.data);
    if(d.type === "log")    log(d.msg, d.cls||"");
    if(d.type === "status") status(d.msg, d.col||"#6b7a9e");
    if(d.type === "bar")    setBar(d.pct, d.anim||false);
    if(d.type === "done"){
      es.close();
      setBar(100, false);
      const btn = document.getElementById("btn");
      btn.textContent = "▶   AVVIA ORBITA CASA";
      btn.className = "btn success";
      btn.disabled = false;
      btn.onclick = () => avvia(nome);
    }
    if(d.type === "error"){
      es.close();
      setBar(0, false);
      const btn = document.getElementById("btn");
      btn.textContent = "↺   Riprova";
      btn.disabled = false;
      document.getElementById("nome").disabled = false;
      status("❌ Errore — vedi log", "#f44336");
    }
  };
}
async function avvia(nome){
  await fetch("/avvia?nome="+encodeURIComponent(nome));
  status("🚀 OrbitaCasa avviato! Puoi chiudere questa finestra.", "#4caf50");
  document.getElementById("btn").disabled = true;
}
</script>
</body>
</html>
"""
class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path == "/":
            self._serve_html()
        elif self.path.startswith("/installa"):
            self._installa()
        elif self.path.startswith("/avvia"):
            self._avvia()
        else:
            self.send_response(404); self.end_headers()
    def _serve_html(self):
        html = HTML.replace("__SO__", SO_LABEL).replace("__BASE__", BASE.replace("\\","\\\\"))
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def _sse(self, data: dict):
        msg = "data: " + json.dumps(data, ensure_ascii=False) + "\n\n"
        self.wfile.write(msg.encode())
        self.wfile.flush()
    def _installa(self):
        from urllib.parse import urlparse, parse_qs
        nome = parse_qs(urlparse(self.path).query).get("nome",["MiaCasa"])[0]
        nome = "".join(c for c in nome if c not in r'/:*?"<>|\\')
        install_dir = os.path.join(BASE, nome)
        pyw = os.path.join(install_dir, "OrbitaCasa.pyw")
        self.send_response(200)
        self.send_header("Content-Type","text/event-stream")
        self.send_header("Cache-Control","no-cache")
        self.send_header("Access-Control-Allow-Origin","*")
        self.end_headers()
        def log(msg, cls=""): self._sse({"type":"log","msg":msg,"cls":cls})
        def st(msg, col="#6b7a9e"): self._sse({"type":"status","msg":msg,"col":col})
        def bar(p, anim=False): self._sse({"type":"bar","pct":p,"anim":anim})
        try:
            log(f"\n📁  Cartella: {install_dir}", "info")
            os.makedirs(install_dir, exist_ok=True)
            log("   ✅  Creata", "ok"); bar(10)
            log("\n⬇️   Download OrbitaCasa.pyw …", "info")
            st("Download in corso…", "#4a90d9")
            def hook(c, b, t):
                if t > 0: bar(10 + int(c * b * 30 / t))
            urllib.request.urlretrieve(PYW_URL, pyw, hook)
            log(f"   ✅  {os.path.getsize(pyw)//1024} KB scaricati", "ok"); bar(40)
            log("\n🐍  Dipendenze Python …", "info")
            for i, dep in enumerate(DEPS, 1):
                st(f"pip install {dep}  ({i}/{len(DEPS)})", "#4a90d9")
                r = subprocess.run(
                    [sys.executable, "-m", "pip", "install", dep,
                     "--quiet", "--disable-pip-version-check"],
                    capture_output=True)
                if r.returncode != 0:
                    subprocess.run([sys.executable, "-m", "pip", "install", dep,
                                    "--user", "--quiet", "--disable-pip-version-check"],
                                   capture_output=True)
                ok = r.returncode == 0
                log(f"   {'✅' if ok else '⚠️ '}  {dep}", "ok" if ok else "warn")
                bar(40 + int(i * 55 / len(DEPS)))
            if SO == "Windows":
                lpath = os.path.join(install_dir, "Avvia OrbitaCasa.bat")
                open(lpath, "w").write(
                    f'@echo off\ncd /d "{install_dir}"\n"{sys.executable}" "{pyw}"\n')
                log(f"   🖥️   Launcher: {lpath}", "ok")
                desk_lnk = os.path.join(BASE, f"OrbitaCasa — {nome}.lnk")
                ps = (
                    f'$s=(New-Object -COM WScript.Shell).CreateShortcut("{desk_lnk}");'
                    f'$s.TargetPath="{sys.executable}";'
                    f'$s.Arguments=\'"{pyw}"\';'
                    f'$s.WorkingDirectory="{install_dir}";'
                    f'$s.Description="OrbitaCasa — {nome}";'
                    f'$s.Save()'
                )
                subprocess.run(["powershell", "-Command", ps], capture_output=True)
                log(f"   🖥️   Collegamento desktop: {desk_lnk}", "ok")
            elif SO == "Darwin":
                lpath = os.path.join(install_dir, "Avvia OrbitaCasa.command")
                open(lpath, "w").write(
                    f'#!/bin/bash\ncd "{install_dir}"\n"{sys.executable}" "{pyw}"\n')
                os.chmod(lpath, 0o755)
                desk_alias = os.path.join(BASE, f"OrbitaCasa — {nome}.command")
                try:
                    import shutil
                    shutil.copy2(lpath, desk_alias)
                    os.chmod(desk_alias, 0o755)
                    log(f"   🖥️   Collegamento desktop: {desk_alias}", "ok")
                except Exception as e2:
                    log(f"   ⚠️   Desktop shortcut non creato: {e2}", "warn")
            else:
                lpath = os.path.join(install_dir, "Avvia_OrbitaCasa.sh")
                open(lpath, "w").write(
                    f'#!/bin/bash\ncd "{install_dir}"\n"{sys.executable}" "{pyw}"\n')
                os.chmod(lpath, 0o755)
                desk_file = os.path.join(BASE, f"OrbitaCasa_{nome}.desktop")
                content = (
                    "[Desktop Entry]\n"
                    "Version=1.0\n"
                    f"Name=OrbitaCasa — {nome}\n"
                    "Comment=Gestionale personale OrbitaCasa\n"
                    f"Exec={sys.executable} \"{pyw}\"\n"
                    f"Path={install_dir}\n"
                    "Icon=accessories-calculator\n"
                    "Terminal=false\n"
                    "Type=Application\n"
                    "Categories=Office;Finance;\n"
                )
                with open(desk_file, "w") as f:
                    f.write(content)
                os.chmod(desk_file, 0o755)
                trusted = False
                try:
                    r = subprocess.run(["gio", "set", desk_file,
                                        "metadata::trusted", "true"], capture_output=True)
                    trusted = r.returncode == 0
                except Exception:
                    pass
                if not trusted:
                    try:
                        import ctypes, ctypes.util
                        libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
                        libc.setxattr(desk_file.encode(), b"user.metadata::trusted",
                                      b"true", 4, 0)
                        trusted = True
                    except Exception:
                        pass
                log(f"   🖥️   Collegamento desktop: {desk_file}", "ok")
            log("\n" + "─" * 44, "dim")
            log("✅  Installazione completata!", "ok")
            log(f"   Profilo  : {nome}", "ok")
            log(f"   Cartella : {install_dir}", "ok")
            log("─" * 44, "dim")
            st("✅  Completato! Premi il pulsante verde.", "#4caf50")
            self._sse({"type": "done"})
        except Exception as e:
            log(f"\n❌  {e}", "err")
            self._sse({"type": "error"})
    def _avvia(self):
        from urllib.parse import urlparse, parse_qs
        nome = parse_qs(urlparse(self.path).query).get("nome", ["MiaCasa"])[0]
        pyw  = os.path.join(BASE, nome, "OrbitaCasa.pyw")
        if os.path.isfile(pyw):
            subprocess.Popen([sys.executable, pyw],
                             cwd=os.path.dirname(pyw), close_fds=True)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')
def find_free_port():
    import socket
    for p in range(7474, 7600):
        try:
            s = socket.socket(); s.bind(("127.0.0.1", p)); s.close(); return p
        except OSError:
            continue
    raise OSError("Nessuna porta libera trovata (7474-7600)")
def main():
    port = find_free_port()
    server = http.server.HTTPServer(("127.0.0.1", port), Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    url = f"http://127.0.0.1:{port}"
    print(f"OrbitaCasa Installer → {url}")
    time.sleep(0.3)
    webbrowser.open(url)
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        server.shutdown()

if __name__ == "__main__":
    main()
