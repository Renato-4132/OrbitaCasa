#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scansione da scanner (USB o di rete) e creazione di un PDF, per Windows, Linux e macOS.

Strade usate, in ordine di preferenza per ciascun sistema:
  - eSCL / AirScan  : scanner di rete (tutti i sistemi), solo HTTP, nessun driver
  - SANE (scanimage): Linux, e macOS se e' installato sane-backends
  - WIA             : Windows, tramite PowerShell (finestra di scansione di Windows)

La parte logica non usa tkinter (si puo' provare da sola); l'interfaccia e' in
apri_dialog_scansione(), che alla fine restituisce il percorso del PDF creato.
"""

import os
import re
import sys
import glob
import time
import uuid
import shutil
import queue
import ssl
import threading
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request

_WIN = os.name == "nt"
_MAC = sys.platform == "darwin"
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0) if _WIN else 0

RISOLUZIONI = ["100", "150", "200", "300", "600"]
DOPO = {"Analisi AI": True, "Compilo a mano": False}
MODI = {"Colore": "colore", "Grigio": "grigio", "Bianco e nero": "bn"}
SORGENTI = {"Vetro (una pagina)": "vetro", "Caricatore automatico": "adf"}

CARTELLA_PDF = os.path.join(tempfile.gettempdir(), "orbita_scansioni")

class ScannerErrore(Exception):
    pass

def _chiave_scanner(s):
    return f"{s.get('backend')}|{s.get('base') or ''}|{s.get('label')}"


def scarta_scansione(percorso):
    try:
        if percorso and os.path.dirname(os.path.abspath(percorso)) == os.path.abspath(CARTELLA_PDF):
            os.remove(percorso)
    except OSError:
        pass

def _file_impostazioni():
    try:
        import __main__ as _app
        return getattr(_app, "SCANNER_FILE", None) or os.path.join(_app.DB_DIR, "scanner_impostazioni.json")
    except Exception:
        return None

def _carica_impostazioni():
    import json
    p = _file_impostazioni()
    try:
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}

def _salva_impostazioni(d):
    import json
    p = _file_impostazioni()
    if not p:
        return
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def _pymupdf():
    try:
        import pymupdf
        return pymupdf
    except ImportError:
        import fitz as pymupdf
        return pymupdf

def _ctx():
    c = ssl.create_default_context()
    c.check_hostname = False
    c.verify_mode = ssl.CERT_NONE
    return c

def _esegui(cmd, timeout, stdout=None):
    return subprocess.run(
        cmd, stdout=stdout if stdout is not None else subprocess.PIPE,
        stderr=subprocess.PIPE, timeout=timeout, creationflags=_NO_WINDOW)

def _testo(b):
    return (b or b"").decode("utf-8", "replace").strip()

def _trova_sane():
    exe = shutil.which("scanimage")
    if not exe:
        return []
    try:
        r = _esegui([exe, "-L"], timeout=40)
    except Exception:
        return []
    trovati = []
    for riga in _testo(r.stdout).splitlines():
        m = re.match(r"\s*device\s+[`']([^`']+)[`']\s+is\s+an?\s+(.*)$", riga)
        if m:
            trovati.append({"backend": "sane", "dev": m.group(1),
                            "label": f"{m.group(2).strip()} (SANE)"})
    return trovati

def _trova_escl(attesa=3.0):
    try:
        from zeroconf import ServiceBrowser, Zeroconf
    except ImportError:
        return []
    trovati = {}

    class _L:
        def add_service(self, zc, tipo, nome):
            try:
                info = zc.get_service_info(tipo, nome, timeout=2000)
                if not info:
                    return
                ind = [a for a in info.parsed_addresses() if ":" not in a]
                if not ind:
                    return
                props = {(k.decode() if isinstance(k, bytes) else k):
                         (v.decode() if isinstance(v, bytes) else v)
                         for k, v in (info.properties or {}).items()}
                radice = (props.get("rs") or "eSCL").strip("/")
                schema = "https" if "_uscans" in tipo else "http"
                base = f"{schema}://{ind[0]}:{info.port}/{radice}"
                titolo = props.get("ty") or nome.split(".")[0]
                trovati[base] = {"backend": "escl", "base": base,
                                 "label": f"{titolo} (rete)"}
            except Exception:
                pass

        def update_service(self, *a):
            pass

        def remove_service(self, *a):
            pass

    zc = Zeroconf()
    try:
        l = _L()
        ServiceBrowser(zc, "_uscan._tcp.local.", l)
        ServiceBrowser(zc, "_uscans._tcp.local.", l)
        time.sleep(attesa)
    finally:
        try:
            zc.close()
        except Exception:
            pass
    return list(trovati.values())

def elenco_scanner():
    lista = []
    if _WIN:
        lista.append({"backend": "wia", "label": "Scanner di Windows (WIA)"})
    lista += _trova_sane()
    lista += _trova_escl()
    return lista

def aggiungi_scanner_rete(testo):
    t = (testo or "").strip()
    if not t:
        raise ScannerErrore("Inserisci l'indirizzo IP dello scanner.")
    if "://" in t:
        candidati = [t]
    elif t.rstrip("/").endswith(":443"):
        candidati = ["https://" + t, "http://" + t]
    else:
        candidati = ["http://" + t, "https://" + t]
    ultimo = None
    for c in candidati:
        u = urllib.parse.urlparse(c)
        if not u.hostname:
            raise ScannerErrore("Indirizzo non valido.")
        radice = u.path.strip("/") or "eSCL"
        base = f"{u.scheme}://{u.netloc}/{radice}"
        try:
            with urllib.request.urlopen(base + "/ScannerCapabilities", timeout=5,
                                        context=_ctx()) as r:
                corpo = r.read(4096)
                finale = r.geturl()
            if b"ScannerCapabilities" not in corpo:
                raise ScannerErrore("la risposta non e' quella di uno scanner eSCL")
            if finale.endswith("/ScannerCapabilities"):
                base = finale[:-len("/ScannerCapabilities")]
            return {"backend": "escl", "base": base, "label": f"Scanner di rete {u.hostname}"}
        except Exception as e:
            ultimo = (u.netloc, e)
    netloc, e = ultimo
    suggerimento = "" if ":" in netloc else (
        " Se lo scanner usa una porta diversa, scrivila dopo l'IP (per esempio 192.168.1.50:8080).")
    raise ScannerErrore(f"Nessuna risposta eSCL da {netloc}: {e}.{suggerimento}")

def _escl_xml(risoluzione, modo, sorgente):
    colore = {"colore": "RGB24", "grigio": "Grayscale8", "bn": "BlackAndWhite1"}[modo]
    sorg = "Feeder" if sorgente == "adf" else "Platen"
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<scan:ScanSettings xmlns:scan="http://schemas.hp.com/imaging/escl/2011/05/03" '
        'xmlns:pwg="http://www.pwg.org/schemas/2010/12/sm">'
        '<pwg:Version>2.0</pwg:Version>'
        '<pwg:ScanRegions><pwg:ScanRegion>'
        '<pwg:ContentRegionUnits>escl:ThreeHundredthsOfInches</pwg:ContentRegionUnits>'
        '<pwg:Width>2480</pwg:Width><pwg:Height>3508</pwg:Height>'
        '<pwg:XOffset>0</pwg:XOffset><pwg:YOffset>0</pwg:YOffset>'
        '</pwg:ScanRegion></pwg:ScanRegions>'
        f'<pwg:InputSource>{sorg}</pwg:InputSource>'
        f'<scan:ColorMode>{colore}</scan:ColorMode>'
        f'<scan:XResolution>{risoluzione}</scan:XResolution>'
        f'<scan:YResolution>{risoluzione}</scan:YResolution>'
        '<pwg:DocumentFormat>image/jpeg</pwg:DocumentFormat>'
        '</scan:ScanSettings>'
    )

def _escl_scansiona(base, risoluzione, modo, sorgente, cartella):
    xml = _escl_xml(risoluzione, modo, sorgente)
    url_jobs = base.rstrip("/") + "/ScanJobs"
    req = urllib.request.Request(
        url_jobs, data=xml.encode("utf-8"), method="POST",
        headers={"Content-Type": "text/xml"})
    try:
        with urllib.request.urlopen(req, timeout=30, context=_ctx()) as r:
            loc = r.headers.get("Location")
    except urllib.error.HTTPError as e:
        if e.code == 503:
            raise ScannerErrore("Lo scanner e' occupato. Riprova tra qualche secondo.")
        if e.code == 409:
            raise ScannerErrore("Lo scanner non e' pronto (coperchio aperto o carta inceppata?).")
        raise ScannerErrore(f"Lo scanner ha rifiutato la richiesta (errore {e.code}).")
    except Exception as e:
        raise ScannerErrore(f"Scanner non raggiungibile: {e}")
    if not loc:
        raise ScannerErrore("Lo scanner non ha indicato il lavoro di scansione.")
    job = urllib.parse.urljoin(url_jobs + "/", loc).rstrip("/")

    pagine = []
    try:
        for n in range(200):
            tentativi = 0
            while True:
                try:
                    with urllib.request.urlopen(job + "/NextDocument", timeout=180,
                                                context=_ctx()) as r:
                        dati = r.read()
                        ctype = (r.headers.get("Content-Type") or "").lower()
                    break
                except urllib.error.HTTPError as e:
                    if e.code == 404:
                        dati = None
                        break
                    if e.code == 503 and tentativi < 20:
                        tentativi += 1
                        time.sleep(1.0)
                        continue
                    raise ScannerErrore(f"Errore dallo scanner durante la scansione ({e.code}).")
            if dati is None:
                break
            ext = ".pdf" if "pdf" in ctype else (".png" if "png" in ctype else ".jpg")
            percorso = os.path.join(cartella, f"p_{uuid.uuid4().hex[:8]}{ext}")
            with open(percorso, "wb") as f:
                f.write(dati)
            pagine.append({"path": percorso, "dpi": int(risoluzione), "bn": modo == "bn"})
            if sorgente != "adf":
                break
    finally:
        try:
            urllib.request.urlopen(
                urllib.request.Request(job, method="DELETE"), timeout=5, context=_ctx()).close()
        except Exception:
            pass
    if not pagine:
        raise ScannerErrore("Nessuna pagina acquisita: il caricatore e' vuoto?"
                            if sorgente == "adf" else "Nessuna pagina acquisita.")
    return pagine

def _sane_nome_sorgente(dev, sorgente):
    if sorgente != "adf":
        return None
    try:
        r = _esegui([shutil.which("scanimage") or "scanimage", "-d", dev, "--help"], timeout=40)
    except Exception:
        return None
    m = re.search(r"--source\s+(.+?)(?:\s+\[|\n)", _testo(r.stdout))
    if not m:
        return None
    for opz in m.group(1).split("|"):
        if re.search(r"adf|feeder|automatic|caricat", opz, re.I):
            return opz.strip()
    return None

def _sane_scansiona(dev, risoluzione, modo, sorgente, cartella):
    exe = shutil.which("scanimage")
    if not exe:
        raise ScannerErrore("Il comando 'scanimage' non e' installato (pacchetto sane-utils / sane-backends).")
    mode = {"colore": "Color", "grigio": "Gray", "bn": "Lineart"}[modo]
    sorg = _sane_nome_sorgente(dev, sorgente)

    sub = tempfile.mkdtemp(dir=cartella)

    def _comando(con_mode, con_res, formato, batch):
        c = [exe, "-d", dev]
        if con_res:
            c.append(f"--resolution={risoluzione}")
        if con_mode:
            c.append(f"--mode={mode}")
        if sorg:
            c += ["--source", sorg]
        c.append(f"--format={formato}")
        if batch:
            c.append(f"--batch={os.path.join(sub, 'p_%03d.' + ('png' if formato == 'png' else 'tif'))}")
        return c

    con_mode, con_res, formato = True, True, "png"
    ultimo_err = ""
    for _ in range(4):
        batch = sorgente == "adf"
        cmd = _comando(con_mode, con_res, formato, batch)
        if batch:
            r = _esegui(cmd, timeout=900)
            files = sorted(glob.glob(os.path.join(sub, "p_*.*")))
            if files:
                return [{"path": f, "dpi": int(risoluzione), "bn": modo == "bn"} for f in files]
        else:
            out = os.path.join(cartella, f"p_{uuid.uuid4().hex[:8]}.{'png' if formato == 'png' else 'tif'}")
            with open(out, "wb") as fo:
                r = _esegui(cmd, timeout=600, stdout=fo)
            if r.returncode == 0 and os.path.getsize(out) > 0:
                return [{"path": out, "dpi": int(risoluzione), "bn": modo == "bn"}]
            try:
                os.remove(out)
            except OSError:
                pass
        err = _testo(r.stderr)
        ultimo_err = err or ultimo_err
        low = err.lower()
        if "format" in low and formato == "png":
            formato = "tiff"
        elif "mode" in low and con_mode:
            con_mode = False
        elif "resolution" in low and con_res:
            con_res = False
        else:
            break
    raise ScannerErrore(ultimo_err.splitlines()[-1] if ultimo_err else "Scansione non riuscita.")

def _porta_davanti_wia(pid_radice, fermo):
    try:
        import ctypes
        from ctypes import wintypes
        u32 = ctypes.windll.user32
        k32 = ctypes.windll.kernel32
    except Exception:
        return

    class _PE(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                    ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
                    ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", ctypes.c_long),
                    ("dwFlags", wintypes.DWORD), ("szExeFile", ctypes.c_wchar * 260)]

    k32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
    k32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    k32.Process32FirstW.argtypes = [ctypes.c_void_p, ctypes.POINTER(_PE)]
    k32.Process32NextW.argtypes = [ctypes.c_void_p, ctypes.POINTER(_PE)]
    k32.CloseHandle.argtypes = [ctypes.c_void_p]
    u32.SetWindowPos.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                                 ctypes.c_int, ctypes.c_int, wintypes.UINT]
    u32.SetForegroundWindow.argtypes = [ctypes.c_void_p]
    u32.ShowWindow.argtypes = [ctypes.c_void_p, ctypes.c_int]
    u32.IsIconic.argtypes = [ctypes.c_void_p]
    u32.IsWindowVisible.argtypes = [ctypes.c_void_p]
    u32.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD)]

    def _albero():
        figli = {}
        snap = k32.CreateToolhelp32Snapshot(0x2, 0)
        if not snap or snap == ctypes.c_void_p(-1).value:
            return {pid_radice}
        try:
            pe = _PE()
            pe.dwSize = ctypes.sizeof(_PE)
            ok = k32.Process32FirstW(snap, ctypes.byref(pe))
            while ok:
                figli.setdefault(pe.th32ParentProcessID, []).append(pe.th32ProcessID)
                ok = k32.Process32NextW(snap, ctypes.byref(pe))
        finally:
            k32.CloseHandle(snap)
        trovati, coda = {pid_radice}, [pid_radice]
        while coda:
            for f in figli.get(coda.pop(), []):
                if f not in trovati:
                    trovati.add(f)
                    coda.append(f)
        return trovati

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, ctypes.c_void_p, ctypes.c_void_p)
    gia = set()
    SWP = 0x0001 | 0x0002 | 0x0040  # NOSIZE | NOMOVE | SHOWWINDOW

    while not fermo.is_set():
        try:
            pids = _albero()
            nuove = []

            def _cb(hwnd, lp):
                if hwnd in gia or not u32.IsWindowVisible(hwnd):
                    return True
                pid = wintypes.DWORD(0)
                u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value in pids:
                    nuove.append(hwnd)
                return True

            u32.EnumWindows(WNDENUMPROC(_cb), 0)
            for hwnd in nuove:
                gia.add(hwnd)
                if u32.IsIconic(hwnd):
                    u32.ShowWindow(hwnd, 9)  # SW_RESTORE
                u32.SetWindowPos(hwnd, ctypes.c_void_p(-1), 0, 0, 0, 0, SWP)  # TOPMOST
                u32.SetWindowPos(hwnd, ctypes.c_void_p(-2), 0, 0, 0, 0, SWP)  # NOTOPMOST
                u32.SetForegroundWindow(hwnd)
        except Exception:
            pass
        fermo.wait(0.4)

def _wia_scansiona(cartella):
    out = os.path.join(cartella, f"wia_{uuid.uuid4().hex[:8]}.png")
    out_ps = out.replace("'", "''")
    ps = (
        "$ErrorActionPreference='Stop';"
        "try{"
        "$cd=New-Object -ComObject WIA.CommonDialog;"
        "$img=$cd.ShowAcquireImage(1,1,0,'{B96B3CAF-0728-11D3-9D7B-0000F81EF32E}',$false,$true,$false);"
        f"if($img -ne $null){{$img.SaveFile('{out_ps}')}}else{{exit 3}}"
        "}catch{[Console]::Error.WriteLine($_.Exception.Message);exit 2}"
    )
    p = subprocess.Popen(["powershell", "-NoProfile", "-STA", "-ExecutionPolicy", "Bypass",
                          "-Command", ps], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         creationflags=_NO_WINDOW)
    fermo = threading.Event()
    threading.Thread(target=_porta_davanti_wia, args=(p.pid, fermo), daemon=True).start()
    try:
        _o, err_b = p.communicate(timeout=900)
    except subprocess.TimeoutExpired:
        p.kill()
        p.communicate()
        raise ScannerErrore("Tempo scaduto durante la scansione.")
    finally:
        fermo.set()
    if p.returncode == 3:
        raise ScannerErrore("Scansione annullata.")
    if p.returncode != 0 or not os.path.exists(out):
        raise ScannerErrore(_testo(err_b) or "Scansione WIA non riuscita.")
    return [{"path": out, "dpi": None, "bn": False}]

def scansiona(scanner, risoluzione, modo, sorgente, cartella):
    b = scanner["backend"]
    if b == "escl":
        return _escl_scansiona(scanner["base"], risoluzione, modo, sorgente, cartella)
    if b == "sane":
        return _sane_scansiona(scanner["dev"], risoluzione, modo, sorgente, cartella)
    if b == "wia":
        return _wia_scansiona(cartella)
    raise ScannerErrore("Tipo di scanner non supportato.")

def _dpi_stimato(pix):
    lato = max(pix.width, pix.height)
    dpi_a4 = lato / 11.69
    xres = pix.xres or 0
    if xres >= 72 and dpi_a4 > 0 and abs(xres - dpi_a4) / dpi_a4 < 0.25:
        return xres
    if 72 <= dpi_a4 <= 1200:
        return dpi_a4
    return xres if xres >= 72 else 200

def crea_pdf(pagine, destinazione, qualita=80):
    if not pagine:
        raise ScannerErrore("Nessuna pagina da salvare.")
    pm = _pymupdf()
    doc = pm.open()
    for pg in pagine:
        p = pg["path"]
        if p.lower().endswith(".pdf"):
            with pm.open(p) as src:
                doc.insert_pdf(src)
            continue
        pix = pm.Pixmap(p)
        dpi = pg.get("dpi") or _dpi_stimato(pix)
        w_pt, h_pt = pix.width / dpi * 72.0, pix.height / dpi * 72.0
        pagina = doc.new_page(width=w_pt, height=h_pt)
        if p.lower().endswith((".jpg", ".jpeg")):
            pagina.insert_image(pagina.rect, filename=p)
            continue
        if pix.alpha:
            pix = pm.Pixmap(pix, 0)
        if pix.colorspace is not None and pix.colorspace.n == 4:
            pix = pm.Pixmap(pm.csRGB, pix)
        if pg.get("bn"):
            dati = pix.tobytes("png")
        else:
            try:
                dati = pix.tobytes("jpeg", jpg_quality=qualita)
            except Exception:
                dati = pix.tobytes("png")
        pagina.insert_image(pagina.rect, stream=dati)
    os.makedirs(os.path.dirname(destinazione) or ".", exist_ok=True)
    doc.save(destinazione, deflate=True, garbage=3)
    doc.close()
    return destinazione

def _pulisci_vecchi(giorni=3):
    try:
        limite = time.time() - giorni * 86400
        for f in glob.glob(os.path.join(CARTELLA_PDF, "*.pdf")):
            if os.path.getmtime(f) < limite:
                os.remove(f)
    except Exception:
        pass

def apri_dialog_scansione(self, parent, on_pdf, titolo="Scansiona documento", salva=False):
    import tkinter as tk
    from tkinter import ttk

    _pulisci_vecchi()
    tmp = tempfile.mkdtemp(prefix="orbita_scan_")

    win = tk.Toplevel(parent, bg=self.COLOR_TOPLEVEL)
    win.title(titolo)
    win.transient(parent)
    win.resizable(False, False)
    W, H = 680, 640
    try:
        parent.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (W // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (H // 2)
    except Exception:
        x, y = 200, 120
    win.geometry(f"{W}x{H}+{max(0, x)}+{max(0, y)}")

    pagine = []
    scanners = []
    stato = {"occupato": False, "chiuso": False, "sel": None}
    miniature = {}
    
    def _lbl(parent_, testo, **kw):
        return tk.Label(parent_, text=testo, bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR,
                        font=kw.pop("font", ("Arial", 10)), **kw)

    def _pulsante(parent_, testo, icona=None):
        img = self.icone_gui.get(icona) if icona else None
        lb = ttk.Label(parent_, text=(" " + testo) if img else testo, image=img,
                       compound="left", background=self.COLOR_WIDGET_BG,
                       foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 4),
                       font=("Arial", 9, "bold"))
        lb.image = img
        lb._cmd = None
        lb._on = True

        def _click(e, l=lb):
            if l._on and l._cmd:
                l._cmd()
        lb.bind("<Button-1>", _click)
        return lb

    def _abilita(lb, on):
        lb._on = bool(on)
        lb.config(foreground=self.TEXT_COLOR if on else "#777777",
                  cursor="hand2" if on else "arrow")

    f1 = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    f1.pack(fill="x", padx=12, pady=(12, 4))
    _lbl(f1, "Scanner:", font=("Arial", 10, "bold")).pack(side="left", padx=(0, 6))
    v_scanner = tk.StringVar()
    cb_scanner = ttk.Combobox(f1, textvariable=v_scanner, state="readonly", width=45, style="Border.TCombobox")
    cb_scanner.pack(side="left", padx=(0, 6))
    btn_cerca = _pulsante(f1, "Cerca", "search")
    btn_cerca.pack(side="left", padx=(0, 6))
    btn_rim = _pulsante(f1, "Rimuovi", "cancella")
    btn_rim.pack(side="left")

    f2 = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    f2.pack(fill="x", padx=12, pady=4)
    _lbl(f2, "Scanner di rete (IP):").pack(side="left", padx=(0, 6))
    v_ip = tk.StringVar()
    e_ip = ttk.Entry(f2, textvariable=v_ip, width=24)
    e_ip.pack(side="left", padx=(0, 6))
    btn_ip = _pulsante(f2, "Aggiungi", "aggiungi")
    btn_ip.pack(side="left")
    _lbl(f2, "es. 192.168.1.50 (la porta è facoltativa)", font=("Arial", 9, "italic")).pack(side="left", padx=(8, 0))

    f3 = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    f3.pack(fill="x", padx=12, pady=(8, 4))
    _lbl(f3, "Risoluzione (dpi):").pack(side="left", padx=(0, 4))
    v_res = tk.StringVar(value="200")
    cb_res = ttk.Combobox(f3, textvariable=v_res, values=RISOLUZIONI, state="readonly", width=5, style="Border.TCombobox")
    cb_res.pack(side="left", padx=(0, 10))
    _lbl(f3, "Colore:").pack(side="left", padx=(0, 4))
    v_modo = tk.StringVar(value="Colore")
    cb_modo = ttk.Combobox(f3, textvariable=v_modo, values=list(MODI), state="readonly", width=13, style="Border.TCombobox")
    cb_modo.pack(side="left", padx=(0, 10))
    _lbl(f3, "Sorgente:").pack(side="left", padx=(0, 4))
    v_sorg = tk.StringVar(value="Vetro (una pagina)")
    imp = _carica_impostazioni()
    if str(imp.get("risoluzione")) in RISOLUZIONI:
        v_res.set(str(imp["risoluzione"]))
    if imp.get("modo") in MODI:
        v_modo.set(imp["modo"])
    if imp.get("sorgente") in SORGENTI:
        v_sorg.set(imp["sorgente"])
    cb_sorg = ttk.Combobox(f3, textvariable=v_sorg, values=list(SORGENTI), state="readonly", width=21, style="Border.TCombobox")
    cb_sorg.pack(side="left")

    f3b = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    if not salva:
        f3b.pack(fill="x", padx=12, pady=(4, 0))
    _lbl(f3b, "Dopo la scansione:").pack(side="left", padx=(0, 4))
    try:
        import __main__ as _app
        _ha_ai = bool(getattr(_app, "API_KEY", None))
    except Exception:
        _ha_ai = False
    v_dopo = tk.StringVar(value="Analisi AI" if _ha_ai else "Compilo a mano")
    if _ha_ai and imp.get("dopo") in DOPO:
        v_dopo.set(imp["dopo"])
    cb_dopo = ttk.Combobox(f3b, textvariable=v_dopo, values=list(DOPO), state="readonly" if _ha_ai else "disabled",
                           width=16, style="Border.TCombobox")
    cb_dopo.pack(side="left", padx=(0, 8))
    if not _ha_ai:
        _lbl(f3b, "Chiave API Gemini non impostata: compili tu i campi, poi 'Archivia PDF'.",
             font=("Arial", 9, "italic")).pack(side="left")

    lbl_nota = _lbl(win, "", font=("Arial", 9, "italic"), anchor="w", justify="left", wraplength=W - 24)
    lbl_nota.pack(fill="x", padx=12)

    f4 = tk.Frame(win, bg=self.COLOR_TOPLEVEL, highlightthickness=1,
                  highlightbackground=self.COLOR_HIGHLIGHT)
    f4.pack(fill="both", expand=True, padx=12, pady=8)
    canvas = tk.Canvas(f4, bg=self.COLOR_TOPLEVEL, highlightthickness=0, height=250)
    hsb = ttk.Scrollbar(f4, orient="horizontal", command=canvas.xview, style="Horizontal.TScrollbar")
    canvas.configure(xscrollcommand=hsb.set)
    hsb.pack(side="bottom", fill="x")
    canvas.pack(side="top", fill="both", expand=True)
    inner = tk.Frame(canvas, bg=self.COLOR_TOPLEVEL)
    canvas.create_window((0, 0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    lbl_stato = _lbl(win, "", font=("Arial", 9), anchor="w", justify="left", wraplength=W - 24)
    lbl_stato.pack(fill="x", padx=12)
    lbl_info = _lbl(win, "", font=("Arial", 9, "italic"), anchor="w", justify="left", wraplength=W - 24)
    lbl_info.pack(fill="x", padx=12)

    f5 = tk.Frame(win, bg=self.COLOR_TOPLEVEL)
    f5.pack(fill="x", padx=12, pady=(6, 12))
    btn_scan = _pulsante(f5, "Scansiona pagina", "scansiona" if "scansiona" in self.icone_gui else "aggiungi")
    btn_scan.pack(side="left", padx=(0, 6))
    btn_del = _pulsante(f5, "Elimina pagina", "cancella")
    btn_del.pack(side="left", padx=(0, 6))
    btn_del_all = _pulsante(f5, "Elimina tutte", "cancella")
    btn_del_all.pack(side="left", padx=(0, 6))
    btn_pdf = _pulsante(f5, "Crea PDF e salva" if salva else "Crea PDF e usa", "archivia")
    btn_pdf.pack(side="left", padx=(0, 6))
    btn_ann = _pulsante(f5, "Annulla", "chiudi")
    btn_ann.pack(side="right")

    def _imposta_stato(t):
        if not stato["chiuso"]:
            lbl_stato.config(text=t)

    def _aggiorna_pulsanti():
        _azione = "Crea PDF e salva" if salva else "Crea PDF e usa"
        lbl_info.config(text=(f"Clicca una miniatura per selezionarla ed eliminarla; 'Scansiona pagina' ne aggiunge altre, "
                              f"'{_azione}' le unisce.") if pagine else "")
        occ = stato["occupato"]
        for b in (btn_cerca, btn_ip, btn_scan, btn_rim):
            _abilita(b, not occ)
        for b in (btn_del, btn_del_all, btn_pdf):
            _abilita(b, not (occ or not pagine))

    def _in_thread(lavoro, finito):
        q = queue.Queue()
        stato["occupato"] = True
        _aggiorna_pulsanti()

        def run():
            try:
                q.put(("ok", lavoro()))
            except Exception as e:
                q.put(("err", e))

        threading.Thread(target=run, daemon=True).start()

        def poll():
            if stato["chiuso"]:
                return
            try:
                esito, val = q.get_nowait()
            except queue.Empty:
                win.after(150, poll)
                return
            stato["occupato"] = False
            _aggiorna_pulsanti()
            finito(esito, val)

        win.after(150, poll)

    def _scanner_corrente():
        i = cb_scanner.current()
        return scanners[i] if 0 <= i < len(scanners) else None

    def _salva():
        s = _scanner_corrente()
        _salva_impostazioni({
            "risoluzione": v_res.get(), "dopo": v_dopo.get() if _ha_ai else imp.get("dopo"), "modo": v_modo.get(), "sorgente": v_sorg.get(),
            "scanner": ({"backend": s["backend"], "base": s.get("base"), "label": s["label"]} if s else imp.get("scanner")),
            "nascosti": imp.get("nascosti", []),
            "cartella_pdf": imp.get("cartella_pdf"),
            "reti": [{"backend": "escl", "base": x["base"], "label": x["label"]}
                     for x in scanners if x["backend"] == "escl" and x.get("base")] or imp.get("reti", []),
        })

    def _su_cambio_scanner(event=None):
        s = _scanner_corrente()
        wia = bool(s and s["backend"] == "wia")
        for cb in (cb_res, cb_modo, cb_sorg):
            cb.config(state="disabled" if wia else "readonly")
        lbl_nota.config(text="Risoluzione, colore e sorgente si scelgono nella finestra di Windows."
                        if wia else "")

    cb_scanner.bind("<<ComboboxSelected>>", lambda e: (_su_cambio_scanner(), _salva()))
    for _cb in (cb_res, cb_modo, cb_sorg, cb_dopo):
        _cb.bind("<<ComboboxSelected>>", lambda e: _salva(), add="+")

    def _imposta_scanners(lista, seleziona=None):
        scanners[:] = lista
        cb_scanner["values"] = [s["label"] for s in scanners]
        if scanners:
            idx = 0
            if seleziona:
                for i, s in enumerate(scanners):
                    if (s.get("base") == seleziona.get("base") and s["backend"] == seleziona.get("backend")
                            and s["label"] == seleziona.get("label")):
                        idx = i
            cb_scanner.current(idx)
        else:
            cb_scanner.set("")
        _su_cambio_scanner()

    def _cerca():
        _imposta_stato("Ricerca degli scanner in corso…")

        def fine(esito, val):
            if esito == "err":
                _imposta_stato("Ricerca non riuscita.")
                self.show_custom_warning("Errore", f"Ricerca degli scanner non riuscita:\n{val}")
                return
            nascosti = set(imp.get("nascosti", []))
            val = [x for x in val if _chiave_scanner(x) not in nascosti]
            salvati = [x for x in imp.get("reti", []) if isinstance(x, dict) and x.get("base")
                       and _chiave_scanner(x) not in nascosti
                       and not any(v.get("base") == x["base"] for v in val)]
            val = list(val) + salvati
            _imposta_scanners(val, seleziona=imp.get("scanner"))
            if val:
                _imposta_stato(f"Trovati {len(val)} scanner.")
            elif _WIN:
                _imposta_stato("Nessuno scanner trovato.")
            elif _MAC:
                _imposta_stato("Nessuno scanner trovato. Su Mac installa SANE (brew install sane-backends) "
                               "oppure inserisci l'IP di uno scanner di rete.")
            else:
                _imposta_stato("Nessuno scanner trovato. Controlla 'scanimage -L' (pacchetto sane-utils) "
                               "oppure inserisci l'IP di uno scanner di rete.")

        _in_thread(elenco_scanner, fine)

    def _aggiungi_ip():
        testo = v_ip.get()
        _imposta_stato("Verifica dello scanner di rete…")

        def fine(esito, val):
            if esito == "err":
                _imposta_stato("Scanner di rete non aggiunto.")
                self.show_custom_warning("Scanner di rete", str(val))
                return
            nuovi = [s for s in scanners if not (s["backend"] == "escl" and s.get("base") == val["base"])]
            nuovi.append(val)
            _imposta_scanners(nuovi, seleziona=val)
            imp["nascosti"] = [k for k in imp.get("nascosti", []) if k != _chiave_scanner(val)]
            _salva()
            _imposta_stato(f"Aggiunto: {val['label']}.")

        _in_thread(lambda: aggiungi_scanner_rete(testo), fine)

    def _rimuovi_scanner():
        s = _scanner_corrente()
        if s is None:
            self.show_custom_warning("Attenzione", "Seleziona prima lo scanner da rimuovere.")
            return
        if not self.show_custom_askyesno("Rimuovi scanner", f"Rimuovere '{s['label']}' dall'elenco?"):
            return
        k = _chiave_scanner(s)
        if k not in imp.setdefault("nascosti", []):
            imp["nascosti"].append(k)
        imp["reti"] = [x for x in imp.get("reti", []) if _chiave_scanner(x) != k]
        imp["scanner"] = None
        _imposta_scanners([x for x in scanners if x is not s])
        _salva()
        _imposta_stato("Scanner rimosso dall'elenco.")

    def _miniatura(percorso):
        if percorso in miniature:
            return miniature[percorso]
        foto = None
        try:
            pm = _pymupdf()
            with pm.open(percorso) as d:
                pg = d[0]
                z = 200.0 / max(1.0, pg.rect.height)
                pix = pg.get_pixmap(matrix=pm.Matrix(z, z), alpha=False)
                foto = tk.PhotoImage(data=pix.tobytes("png"))
        except Exception:
            foto = None
        miniature[percorso] = foto
        return foto

    def _seleziona(i):
        stato["sel"] = i
        _mostra_anteprima(scorri=False)

    def _mostra_anteprima(scorri=True):
        for w in inner.winfo_children():
            w.destroy()
        if not pagine:
            tk.Label(inner, text="Nessuna pagina acquisita", bg=self.COLOR_TOPLEVEL,
                     fg=self.TEXT_COLOR, font=("Arial", 10)).pack(padx=20, pady=100)
            return
        sel = stato["sel"]
        for i, pg in enumerate(pagine):
            cella = tk.Frame(inner, bg=self.COLOR_TOPLEVEL, highlightthickness=2,
                             highlightbackground=self.COLOR_HIGHLIGHT if i == sel else self.COLOR_TOPLEVEL)
            cella.pack(side="left", padx=6, pady=6)
            foto = _miniatura(pg["path"])
            img = tk.Label(cella, image=foto, text="" if foto else os.path.basename(pg["path"]),
                           bg=self.COLOR_TOPLEVEL, fg=self.TEXT_COLOR, cursor="hand2")
            img.pack()
            cap = tk.Label(cella, text=f"Pagina {i + 1}", bg=self.COLOR_TOPLEVEL,
                           fg=self.TEXT_COLOR, font=("Arial", 9, "bold" if i == sel else "normal"),
                           cursor="hand2")
            cap.pack()
            for w in (cella, img, cap):
                w.bind("<Button-1>", lambda e, k=i: _seleziona(k))
        if scorri:
            win.update_idletasks()
            canvas.xview_moveto(1.0)

    def _scansiona():
        s = _scanner_corrente()
        if s is None:
            self.show_custom_warning("Attenzione", "Seleziona prima uno scanner (oppure inserisci l'IP e premi Aggiungi).")
            return
        ris = v_res.get()
        modo = MODI.get(v_modo.get(), "colore")
        sorg = SORGENTI.get(v_sorg.get(), "vetro")
        _imposta_stato("Scansione in corso…" if s["backend"] != "wia"
                       else "Si apre la finestra di scansione di Windows…")

        def fine(esito, val):
            if esito == "err":
                _imposta_stato("Scansione non riuscita.")
                self.show_custom_warning("Errore", str(val) or "Scansione non riuscita.")
                return
            pagine.extend(val)
            _salva()
            stato["sel"] = len(pagine) - 1
            _mostra_anteprima()
            _aggiorna_pulsanti()
            _imposta_stato(f"Pagine acquisite: {len(pagine)}.")

        _in_thread(lambda: scansiona(s, ris, modo, sorg, tmp), fine)

    def _elimina_pagina():
        if not pagine:
            return
        i = stato["sel"]
        if i is None or not (0 <= i < len(pagine)):
            i = len(pagine) - 1
        p = pagine.pop(i)
        miniature.pop(p["path"], None)
        try:
            os.remove(p["path"])
        except OSError:
            pass
        stato["sel"] = min(i, len(pagine) - 1) if pagine else None
        _mostra_anteprima(scorri=False)
        _aggiorna_pulsanti()
        _imposta_stato(f"Pagine acquisite: {len(pagine)}.")

    def _elimina_tutte():
        if not pagine:
            return
        if not self.show_custom_askyesno("Scansione", f"Eliminare tutte le {len(pagine)} pagine acquisite?"):
            return
        for p in pagine:
            try:
                os.remove(p["path"])
            except OSError:
                pass
        pagine.clear()
        miniature.clear()
        stato["sel"] = None
        _mostra_anteprima(scorri=False)
        _aggiorna_pulsanti()
        _imposta_stato("Nessuna pagina acquisita.")

    def _chiudi(conferma=True):
        if stato["chiuso"]:
            return
        if conferma and pagine:
            if not self.show_custom_askyesno("Scansione", f"Scartare le {len(pagine)} pagine acquisite?"):
                return
        stato["chiuso"] = True
        shutil.rmtree(tmp, ignore_errors=True)
        win.destroy()

    def _crea_pdf():
        if not pagine:
            return
        nome = f"scansione_{time.strftime('%d-%m-%Y_%H%M%S')}.pdf"
        dest = os.path.join(CARTELLA_PDF, nome)
        if salva:
            from tkinter import filedialog
            iniz = imp.get("cartella_pdf")
            if not (iniz and os.path.isdir(iniz)):
                iniz = os.path.join(os.path.expanduser("~"), "Documents")
                if not os.path.isdir(iniz):
                    iniz = os.path.expanduser("~")
            dest = filedialog.asksaveasfilename(
                parent=win, title="Salva PDF scansionato", initialdir=iniz, initialfile=nome,
                defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
            if not dest:
                return
            dest = os.path.abspath(dest)
            imp["cartella_pdf"] = os.path.dirname(dest)
        try:
            crea_pdf(pagine, dest)
        except Exception as e:
            _imposta_stato("Creazione del PDF non riuscita.")
            self.show_custom_warning("Errore", f"Creazione del PDF non riuscita:\n{e}")
            return
        usa_ai = _ha_ai and DOPO.get(v_dopo.get(), False) and not salva
        _salva()
        _chiudi(conferma=False)
        if salva:
            try:
                self.show_toast(f"PDF salvato: {dest}")
            except Exception:
                pass
            if on_pdf:
                on_pdf(dest)
            return
        try:
            import inspect
            n_par = len(inspect.signature(on_pdf).parameters)
        except Exception:
            n_par = 1
        if n_par >= 2:
            on_pdf(dest, usa_ai)
        else:
            on_pdf(dest)

    btn_cerca._cmd = _cerca
    btn_ip._cmd = _aggiungi_ip
    btn_rim._cmd = _rimuovi_scanner
    btn_scan._cmd = _scansiona
    btn_del._cmd = _elimina_pagina
    btn_del_all._cmd = _elimina_tutte
    btn_pdf._cmd = _crea_pdf
    btn_ann._cmd = _chiudi
    e_ip.bind("<Return>", lambda e: _aggiungi_ip())
    win.bind("<Escape>", lambda e: _chiudi())
    win.protocol("WM_DELETE_WINDOW", _chiudi)

    _aggiorna_pulsanti()
    _mostra_anteprima()
    _cerca()
    win.focus_force()

def scansiona_e_salva(self):
    def _dopo(percorso):
        try:
            if self.show_custom_askyesno("PDF salvato", "PDF salvato.\nVuoi aprirlo ora?"):
                if _WIN:
                    os.startfile(percorso)
                elif _MAC:
                    subprocess.Popen(["open", percorso])
                else:
                    subprocess.Popen(["xdg-open", percorso])
        except Exception:
            pass

    apri_dialog_scansione(self, self, _dopo, titolo="Scansiona e salva PDF", salva=True)
