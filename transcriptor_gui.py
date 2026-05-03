import os
import queue
import subprocess
import sys
import threading
import traceback
from pathlib import Path

# Bajo pythonw.exe no hay consola: stdout/stderr son None y tqdm/whisper revientan.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

import customtkinter as ctk
from tkinter import filedialog, messagebox

from core import FORMATOS, MODELOS, guardar_resultado, transcribir


IDIOMAS = [
    ("Autodetectar", None),
    ("Español", "es"),
    ("Inglés", "en"),
    ("Portugués", "pt"),
    ("Francés", "fr"),
    ("Alemán", "de"),
    ("Italiano", "it"),
]
DEVICES = [("Auto", None), ("CPU", "cpu"), ("GPU (CUDA)", "cuda")]


ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Transcriptor Whisper")
        self.geometry("760x620")
        self.minsize(680, 560)

        self.cola = queue.Queue()
        self.archivo_audio: Path | None = None
        self.archivo_salida: Path | None = None
        self.trabajando = False

        self._construir()
        self.after(120, self._procesar_cola)

    def _construir(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)

        ctk.CTkLabel(
            self, text="Transcriptor de Audio", font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Audio
        marco_audio = ctk.CTkFrame(self)
        marco_audio.grid(row=1, column=0, padx=20, pady=8, sticky="ew")
        marco_audio.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(marco_audio, text="Audio:").grid(row=0, column=0, padx=10, pady=10)
        self.var_audio = ctk.StringVar(value="(ningún archivo seleccionado)")
        ctk.CTkLabel(marco_audio, textvariable=self.var_audio, anchor="w").grid(
            row=0, column=1, padx=10, pady=10, sticky="ew"
        )
        ctk.CTkButton(marco_audio, text="Examinar...", width=120, command=self._elegir_audio).grid(
            row=0, column=2, padx=10, pady=10
        )

        # Parámetros
        marco_param = ctk.CTkFrame(self)
        marco_param.grid(row=2, column=0, padx=20, pady=8, sticky="ew")
        for c in range(4):
            marco_param.grid_columnconfigure(c, weight=1)

        ctk.CTkLabel(marco_param, text="Modelo").grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        self.opt_modelo = ctk.CTkOptionMenu(marco_param, values=list(MODELOS))
        self.opt_modelo.set("base")
        self.opt_modelo.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(marco_param, text="Idioma").grid(row=0, column=1, padx=10, pady=(10, 0), sticky="w")
        self.opt_idioma = ctk.CTkOptionMenu(marco_param, values=[n for n, _ in IDIOMAS])
        self.opt_idioma.set("Español")
        self.opt_idioma.grid(row=1, column=1, padx=10, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(marco_param, text="Formato").grid(row=0, column=2, padx=10, pady=(10, 0), sticky="w")
        self.opt_formato = ctk.CTkOptionMenu(
            marco_param, values=list(FORMATOS), command=self._on_formato
        )
        self.opt_formato.set("txt")
        self.opt_formato.grid(row=1, column=2, padx=10, pady=(0, 10), sticky="ew")

        ctk.CTkLabel(marco_param, text="Dispositivo").grid(row=0, column=3, padx=10, pady=(10, 0), sticky="w")
        self.opt_device = ctk.CTkOptionMenu(marco_param, values=[n for n, _ in DEVICES])
        self.opt_device.set("Auto")
        self.opt_device.grid(row=1, column=3, padx=10, pady=(0, 10), sticky="ew")

        self.var_traducir = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            marco_param, text="Traducir al inglés", variable=self.var_traducir
        ).grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="w")

        # Salida
        marco_salida = ctk.CTkFrame(self)
        marco_salida.grid(row=3, column=0, padx=20, pady=8, sticky="ew")
        marco_salida.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(marco_salida, text="Salida:").grid(row=0, column=0, padx=10, pady=10)
        self.var_salida = ctk.StringVar(value="(automática, junto al audio)")
        ctk.CTkLabel(marco_salida, textvariable=self.var_salida, anchor="w").grid(
            row=0, column=1, padx=10, pady=10, sticky="ew"
        )
        ctk.CTkButton(
            marco_salida, text="Cambiar...", width=120, command=self._elegir_salida
        ).grid(row=0, column=2, padx=10, pady=10)

        # Botonera
        marco_btn = ctk.CTkFrame(self, fg_color="transparent")
        marco_btn.grid(row=4, column=0, padx=20, pady=8, sticky="ew")
        marco_btn.grid_columnconfigure(0, weight=1)
        self.btn_play = ctk.CTkButton(
            marco_btn, text="▶  Transcribir", height=42,
            font=ctk.CTkFont(size=15, weight="bold"), command=self._iniciar
        )
        self.btn_play.grid(row=0, column=0, sticky="ew")
        self.btn_abrir = ctk.CTkButton(
            marco_btn, text="Abrir carpeta", width=140, height=42,
            command=self._abrir_carpeta, state="disabled"
        )
        self.btn_abrir.grid(row=0, column=1, padx=(10, 0))

        # Progreso
        self.barra = ctk.CTkProgressBar(self, mode="indeterminate")
        self.barra.grid(row=5, column=0, padx=20, pady=(0, 8), sticky="ew")
        self.barra.set(0)

        # Log
        self.log = ctk.CTkTextbox(self, height=180)
        self.log.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="nsew")
        self.log.configure(state="disabled")

        # Estado
        self.var_estado = ctk.StringVar(value="Listo.")
        ctk.CTkLabel(self, textvariable=self.var_estado, anchor="w").grid(
            row=7, column=0, padx=20, pady=(0, 12), sticky="ew"
        )

    # ---------- handlers ----------
    def _on_formato(self, _v: str) -> None:
        if self.archivo_audio and not self.archivo_salida:
            self._refrescar_etiqueta_salida()

    def _refrescar_etiqueta_salida(self) -> None:
        if self.archivo_salida:
            self.var_salida.set(str(self.archivo_salida))
        elif self.archivo_audio:
            ext = self.opt_formato.get()
            self.var_salida.set(str(self.archivo_audio.with_suffix(f".{ext}")))
        else:
            self.var_salida.set("(automática, junto al audio)")

    def _elegir_audio(self) -> None:
        ruta = filedialog.askopenfilename(
            title="Selecciona el audio",
            filetypes=[
                ("Audio/Video", "*.mp3 *.wav *.m4a *.ogg *.flac *.mp4 *.mkv *.aac *.webm *.opus"),
                ("Todos", "*.*"),
            ],
        )
        if ruta:
            self.archivo_audio = Path(ruta)
            self.var_audio.set(str(self.archivo_audio))
            self.archivo_salida = None
            self._refrescar_etiqueta_salida()

    def _elegir_salida(self) -> None:
        ext = self.opt_formato.get()
        inicial = self.archivo_audio.with_suffix(f".{ext}") if self.archivo_audio else None
        ruta = filedialog.asksaveasfilename(
            title="Guardar como",
            defaultextension=f".{ext}",
            initialfile=inicial.name if inicial else f"transcripcion.{ext}",
            filetypes=[(ext.upper(), f"*.{ext}"), ("Todos", "*.*")],
        )
        if ruta:
            self.archivo_salida = Path(ruta)
            self._refrescar_etiqueta_salida()

    def _abrir_carpeta(self) -> None:
        if self.archivo_salida and self.archivo_salida.exists():
            subprocess.Popen(["explorer", "/select,", str(self.archivo_salida)])

    def _logear(self, texto: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", texto + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _iniciar(self) -> None:
        if self.trabajando:
            return
        if not self.archivo_audio or not self.archivo_audio.exists():
            messagebox.showwarning("Falta audio", "Selecciona un archivo de audio primero.")
            return

        modelo = self.opt_modelo.get()
        idioma = dict(IDIOMAS)[self.opt_idioma.get()]
        formato = self.opt_formato.get()
        device = dict(DEVICES)[self.opt_device.get()]
        traducir = self.var_traducir.get()
        salida = self.archivo_salida or self.archivo_audio.with_suffix(f".{formato}")

        self.trabajando = True
        self.btn_play.configure(state="disabled", text="Procesando...")
        self.btn_abrir.configure(state="disabled")
        self.barra.start()
        self.var_estado.set("Trabajando...")
        self._logear(f"→ Audio: {self.archivo_audio}")
        self._logear(f"→ Modelo: {modelo}  Idioma: {idioma or 'auto'}  Formato: {formato}")
        if traducir:
            self._logear("→ Traducción al inglés activada.")

        hilo = threading.Thread(
            target=self._worker,
            args=(self.archivo_audio, modelo, idioma, traducir, device, salida, formato),
            daemon=True,
        )
        hilo.start()

    def _worker(self, audio, modelo, idioma, traducir, device, salida, formato):
        try:
            self.cola.put(("log", f"Cargando modelo '{modelo}' (puede tardar la primera vez)..."))
            resultado = transcribir(
                audio, modelo=modelo, idioma=idioma, traducir=traducir, device=device
            )
            self.cola.put(("log", "Guardando resultado..."))
            guardar_resultado(resultado, salida, formato)
            self.cola.put(("ok", str(salida)))
        except FileNotFoundError as e:
            msg = str(e)
            if "WinError 2" in msg or "ffmpeg" in msg.lower():
                self.cola.put((
                    "error",
                    "No se encontró ffmpeg. Instálalo con: winget install Gyan.FFmpeg "
                    "y reinicia la app.",
                ))
            else:
                self.cola.put(("error", msg))
        except Exception:
            self.cola.put(("error", traceback.format_exc()))

    def _procesar_cola(self) -> None:
        try:
            while True:
                tipo, dato = self.cola.get_nowait()
                if tipo == "log":
                    self._logear(dato)
                elif tipo == "ok":
                    self._logear(f"✓ Listo: {dato}")
                    self.var_estado.set(f"Completado: {dato}")
                    self.barra.stop()
                    self.barra.set(1)
                    self.btn_play.configure(state="normal", text="▶  Transcribir")
                    self.btn_abrir.configure(state="normal")
                    self.archivo_salida = Path(dato)
                    self.trabajando = False
                elif tipo == "error":
                    self._logear(f"✗ Error: {dato}")
                    self.var_estado.set("Error.")
                    self.barra.stop()
                    self.barra.set(0)
                    self.btn_play.configure(state="normal", text="▶  Transcribir")
                    self.trabajando = False
                    messagebox.showerror("Error", dato)
        except queue.Empty:
            pass
        self.after(120, self._procesar_cola)


if __name__ == "__main__":
    App().mainloop()
