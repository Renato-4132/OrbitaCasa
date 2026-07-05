#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import platform
import subprocess
import tempfile
import datetime
import tkinter as tk
from tkinter import ttk, filedialog

from __main__ import EXPORT_FILES

# Anteprima e Stampa Diretta File Testo (.txt)
def anteprima_e_stampa_txt(self):
    now = datetime.date.today()
    default_dir = EXPORT_FILES
    default_filename = ""
    path = filedialog.askopenfilename(
           filetypes=[("File txt", "*.txt")],
           initialdir=default_dir,
           initialfile=default_filename,
           title="Stampa Testi"
           )
    if not path:
        return
    with open(path, "r", encoding="utf-8") as f:
        contenuto = f.read()
    anteprima = tk.Toplevel(bg=self.COLOR_TOPLEVEL)
    anteprima.withdraw()
    anteprima.title(f"Anteprima stampa: {os.path.basename(path)}")
    anteprima.resizable(True, True) 
    larghezza_finestra = 1300
    altezza_finestra = 600
    def centra_finestra():
        larghezza_schermo = anteprima.winfo_screenwidth()
        altezza_schermo = anteprima.winfo_screenheight()
        x = (larghezza_schermo // 2) - (larghezza_finestra // 2)
        y = (altezza_schermo // 2) - (altezza_finestra // 2)
        anteprima.geometry(f"{larghezza_finestra}x{altezza_finestra}+{x}+{y}")
        anteprima.minsize(larghezza_finestra, altezza_finestra)
        anteprima.deiconify()
        anteprima.lift()
        anteprima.focus_force()
    anteprima.after(0, centra_finestra)
    txt = tk.Text(anteprima, wrap="word", font=("Courier new", 10))
    txt.insert("1.0", contenuto)
    txt.config(state="disabled")
    txt.pack(padx=10, pady=10, fill="both", expand=True)
    def stampa():
        try:
            sistema = platform.system()
            if not os.path.exists(path):
                raise FileNotFoundError("File non trovato per la stampa")
            if sistema == "Windows":
                import win32print # type: ignore
                import win32ui    # type: ignore
                import win32con   # type: ignore
                printer_name = win32print.GetDefaultPrinter()
                hprinter = win32print.OpenPrinter(printer_name)
                properties = win32print.GetPrinter(hprinter, 2)
                devmode = properties["pDevMode"]
                devmode.Orientation = 2  # 2 = Landscape
                win32print.ClosePrinter(hprinter)
                pdc = win32ui.CreateDC()
                pdc.CreatePrinterDC(printer_name)
                pdc.SetMapMode(win32con.MM_TEXT)
                if hasattr(pdc, "ResetDC"):
                      pdc.ResetDC(devmode)
                else:
                      print("⚠️ Attenzione: ResetDC non disponibile su questo oggetto DC")                                       
                HORZRES = pdc.GetDeviceCaps(win32con.HORZRES)  
                VERTRES = pdc.GetDeviceCaps(win32con.VERTRES)  
                font = win32ui.CreateFont({
                     "name": "Courier New",     
                     "height": -int(VERTRES / 60),  
                     "width": int(HORZRES / 160),  
                })
                pdc.SelectObject(font)
                pdc.StartDoc("Stampa compatibile")
                pdc.StartPage()
                margin_x = 100  # Margine sinistro
                margin_y = 100  # Margine superiore
                line_height = int(VERTRES / 70)     #60 righe circa dal fondo def.
                with open(path, "r", encoding="utf-8") as file:
                    y = margin_y
                    for line in file:
                        pdc.TextOut(margin_x, y, line.rstrip())
                        y += line_height
                        if y + line_height > VERTRES:
                    
                               pdc.EndPage()
                               pdc.StartPage()
                               y = margin_y
                pdc.EndPage()
                pdc.EndDoc()
                pdc.DeleteDC()
            elif sistema in ["Linux", "Darwin"]:
                subprocess.run([
                    "lp",
                    "-o", "orientation-requested=4",
                    "-o", "fit-to-page",
                    "-o", "cpi=17",
                    "-o", "lpi=8",
                    path
                ], check=True)
            else:
                raise OSError(f"Sistema non supportato: {sistema}")
            self.show_custom_warning("Stampa Avviata", f"Inviato alla stampante predefinita ({sistema})")
        except subprocess.CalledProcessError as e:
            self.show_custom_warning("Stampa Errore", f"Errore di stampa: {e}")
        except Exception as ex:
            self.show_custom_warning("Errore imprevisto", str(ex))
    frame_bottoni = tk.Frame(anteprima, bg=self.COLOR_TOPLEVEL)
    frame_bottoni.pack(pady=10, fill="x")
    img_stampa_ant = self.icone_gui.get("stampa")
    btn_stampa_ant = ttk.Label(frame_bottoni, compound="left", image=img_stampa_ant, text=" Stampa" if img_stampa_ant else "Stampa", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
    btn_stampa_ant.pack(side="left", padx=20)
    btn_stampa_ant.bind("<Button-1>", lambda e: stampa())
    img_chiudi_ant = self.icone_gui.get("chiudi")
    btn_chiudi_ant = ttk.Label(frame_bottoni, compound="left", image=img_chiudi_ant, text=" Chiudi" if img_chiudi_ant else "Chiudi", background=self.COLOR_WIDGET_BG, foreground=self.TEXT_COLOR, cursor="hand2", padding=(10, 5))
    btn_chiudi_ant.pack(side="right", padx=20)
    btn_chiudi_ant.bind("<Button-1>", lambda e: anteprima.destroy())

# Funzione di Utilità per la Stampa Diretta Cross-Platform
def _stampa_lista_diretta(self, testo_da_stampare, show_warning_func):
    temp_file_path = ""
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding="utf-8", suffix=".txt") as tmp_file:
            tmp_file.write(testo_da_stampare)
            temp_file_path = tmp_file.name
        path = temp_file_path
        sistema = platform.system()
        if sistema == "Windows":
            import win32print # type: ignore
            import win32ui    # type: ignore
            import win32con   # type: ignore
            printer_name = win32print.GetDefaultPrinter()
            hprinter = win32print.OpenPrinter(printer_name)
            properties = win32print.GetPrinter(hprinter, 2)
            devmode = properties["pDevMode"]
            devmode.Orientation = 2 # 2 = Landscape
            win32print.ClosePrinter(hprinter)
            pdc = win32ui.CreateDC()
            pdc.CreatePrinterDC(printer_name)
            pdc.SetMapMode(win32con.MM_TEXT)
            if hasattr(pdc, "ResetDC"):
                 pdc.ResetDC(devmode)
            HORZRES = pdc.GetDeviceCaps(win32con.HORZRES)
            VERTRES = pdc.GetDeviceCaps(win32con.VERTRES)
            font = win32ui.CreateFont({
                 "name": "Courier New",
                 "height": -int(VERTRES / 70), 
                 "width": int(HORZRES / 160),
            })
            pdc.SelectObject(font)
            pdc.StartDoc(f"Stampa {os.path.basename(path)}")
            pdc.StartPage()
            margin_x = 100
            margin_y = 100
            line_height = int(VERTRES / 70) 
            with open(path, "r", encoding="utf-8") as file:
                y = margin_y
                for line in file:
                    try:
                        pdc.TextOut(margin_x, y, line.rstrip())
                    except Exception:
                        pdc.TextOut(margin_x, y, line.encode('ascii', 'ignore').decode('ascii').rstrip())
                    
                    y += line_height
                    
                    if y + line_height > VERTRES:
                        pdc.EndPage()
                        pdc.StartPage()
                        y = margin_y
            pdc.EndPage()
            pdc.EndDoc()
            pdc.DeleteDC()
            show_warning_func("Stampa Avviata", f"Inviato alla stampante predefinita (Windows).")
        elif sistema in ["Linux", "Darwin"]:
            subprocess.run([
                "lp",
                "-o", "orientation-requested=4", # Landscape
                "-o", "fit-to-page",
                "-o", "cpi=17",
                "-o", "lpi=8", 
                path
            ], check=True)
            show_warning_func("Stampa Avviata", f"Inviato alla stampante predefinita ({sistema}).")
        else:
            show_warning_func("Stampa Fallita", f"Sistema operativo '{sistema}' non supportato per la stampa diretta.")
            return
    except subprocess.CalledProcessError as e:
        show_warning_func("Stampa Errore", f"Errore del comando di stampa: {e}.")
    except Exception as ex:
        show_warning_func("Errore imprevisto", f"Impossibile completare la stampa: {str(ex)}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                show_warning_func("Attenzione", f"Impossibile cancellare il file temporaneo: {e}")

# Invia un PDF alla stampante di sistema usando il metodo nativo per Windows, Linux e macOS
def stampa_pdf(self, file_path, show_warning_func):
    import platform
    import subprocess
    import os
    if not os.path.exists(file_path):
        return show_warning_func("Errore", "Il file da stampare non esiste.")
    sistema = platform.system()
    try:
        if sistema == "Windows":
            import os
            try:
                os.startfile(file_path, "print")
                show_warning_func("Stampa", "Documento inviato alla stampante.")
            except Exception as e:
                show_warning_func("Errore Stampa", f"Errore: {e}")
        elif sistema in ["Linux", "Darwin"]:
            subprocess.run(["lp", "-o", "fit-to-page", file_path], check=True)
            show_warning_func("Stampa", f"Inviato alla stampante ({sistema}).")
        else:
            show_warning_func("Errore", f"Sistema {sistema} non supportato.")
    except Exception as ex:
        show_warning_func("Errore", f"Impossibile completare la stampa: {str(ex)}")
