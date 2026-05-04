import contextlib
import json
from pathlib import Path
from threading import Event
from typing import Callable, Optional

import tqdm as tqdm_module
import whisper


FORMATOS = ("txt", "srt", "vtt", "json")
MODELOS = ("tiny", "base", "small", "medium", "large", "turbo")


class TranscripcionCancelada(Exception):
    pass


@contextlib.contextmanager
def _tqdm_redirect(on_progress=None, evento_cancelar=None):
    """Reemplaza tqdm temporalmente para capturar progreso y soportar cancelación."""
    original = tqdm_module.tqdm

    class TqdmProxy(original):
        def __init__(self, *args, **kwargs):
            kwargs.setdefault("disable", False)
            super().__init__(*args, **kwargs)

        def update(self, n=1):
            if evento_cancelar and evento_cancelar.is_set():
                raise TranscripcionCancelada()
            super().update(n)
            if on_progress and self.total:
                on_progress(self.n / self.total)

        def display(self, *args, **kwargs):
            pass  # suprimir salida a stderr

    tqdm_module.tqdm = TqdmProxy
    try:
        yield
    finally:
        tqdm_module.tqdm = original


def formatear_timestamp(segundos: float, separador: str = ",") -> str:
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    seg = segundos % 60
    return f"{horas:02d}:{minutos:02d}:{seg:06.3f}".replace(".", separador)


def a_srt(segmentos) -> str:
    lineas = []
    for i, seg in enumerate(segmentos, start=1):
        inicio = formatear_timestamp(seg["start"], ",")
        fin = formatear_timestamp(seg["end"], ",")
        lineas.append(f"{i}\n{inicio} --> {fin}\n{seg['text'].strip()}\n")
    return "\n".join(lineas)


def a_vtt(segmentos) -> str:
    lineas = ["WEBVTT", ""]
    for seg in segmentos:
        inicio = formatear_timestamp(seg["start"], ".")
        fin = formatear_timestamp(seg["end"], ".")
        lineas.append(f"{inicio} --> {fin}")
        lineas.append(seg["text"].strip())
        lineas.append("")
    return "\n".join(lineas)


def guardar_resultado(resultado: dict, ruta_salida: Path, formato: str) -> None:
    if formato == "txt":
        ruta_salida.write_text(resultado["text"].strip() + "\n", encoding="utf-8")
    elif formato == "srt":
        ruta_salida.write_text(a_srt(resultado["segments"]), encoding="utf-8")
    elif formato == "vtt":
        ruta_salida.write_text(a_vtt(resultado["segments"]), encoding="utf-8")
    elif formato == "json":
        ruta_salida.write_text(
            json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    else:
        raise ValueError(f"Formato no soportado: {formato}")


_modelos_cache: dict = {}


def cargar_modelo(nombre: str, device: Optional[str] = None):
    clave = (nombre, device)
    if clave not in _modelos_cache:
        _modelos_cache[clave] = whisper.load_model(nombre, device=device)
    return _modelos_cache[clave]


def transcribir(
    audio: Path,
    modelo: str = "base",
    idioma: Optional[str] = None,
    traducir: bool = False,
    device: Optional[str] = None,
    on_progress: Optional[Callable[[float], None]] = None,
    evento_cancelar: Optional[Event] = None,
) -> dict:
    mdl = cargar_modelo(modelo, device)
    with _tqdm_redirect(on_progress=on_progress, evento_cancelar=evento_cancelar):
        resultado = mdl.transcribe(
            str(audio),
            language=idioma,
            task="translate" if traducir else "transcribe",
            verbose=False,
            fp16=False if device == "cpu" else None,
        )
    return resultado
