# Transcriptor Whisper

Aplicación de escritorio para Windows que transcribe audio a texto usando [Whisper de OpenAI](https://github.com/openai/whisper) en local. Incluye interfaz gráfica y CLI.

---

## Instalación rápida

### Requisitos previos

- **Windows 10/11**
- **Python 3.9+** ([descarga aquí](https://www.python.org/downloads/)). Marca **"Add Python to PATH"** durante la instalación.
- **winget** (viene preinstalado en Windows 11; en Windows 10 se instala desde Microsoft Store como "App Installer").

### Pasos

1. Clona o descarga este proyecto en una carpeta.
2. Doble clic en **`instalar.bat`** (o ejecútalo desde PowerShell):
   - Verifica Python.
   - Instala **ffmpeg** vía winget si falta.
   - Crea un entorno virtual aislado (`.venv`).
   - Instala las dependencias (`openai-whisper`, `customtkinter`).
3. Una vez termine, doble clic en **`Transcriptor.bat`** para abrir la app.

> Si ffmpeg se acaba de instalar, puede que necesites cerrar y reabrir la terminal (o reiniciar la sesión) la primera vez para que el sistema lo detecte en el PATH.

---

## Uso de la interfaz gráfica

1. **Examinar...** → seleccionas el archivo de audio o video.
2. Elige **Modelo**, **Idioma**, **Formato** y **Dispositivo**.
3. Marca **Traducir al inglés** si quieres traducción automática (cualquier idioma → inglés).
4. (Opcional) **Cambiar...** la ruta de salida. Por defecto se guarda junto al audio.
5. Clic en **▶ Transcribir**. El log muestra el progreso.
6. Al terminar, **Abrir carpeta** te lleva al archivo en el Explorador.

> Los modelos cargados quedan en memoria mientras la app está abierta: la segunda transcripción con el mismo modelo es inmediata.

---

## Uso por línea de comandos (CLI)

Activa primero el entorno virtual:

```powershell
.\.venv\Scripts\activate
```

Ejemplos:

```powershell
# Básico (modelo "base", autodetecta idioma, salida .txt junto al audio)
python transcriptor.py audio.mp3

# Modelo más preciso, idioma español, salida en SRT
python transcriptor.py audio.mp3 -m medium -l es -f srt

# Traducir al inglés y guardar en una ruta personalizada
python transcriptor.py video.mp4 --traducir -o subs\salida.vtt -f vtt

# Forzar uso de CPU
python transcriptor.py audio.wav --device cpu
```

### Opciones

| Flag | Descripción | Valores | Default |
|---|---|---|---|
| `audio` | Ruta al archivo de entrada (posicional) | — | — |
| `-m`, `--modelo` | Tamaño del modelo Whisper | `tiny`, `base`, `small`, `medium`, `large`, `turbo` | `base` |
| `-l`, `--idioma` | Código ISO del idioma | `es`, `en`, `pt`, `fr`, `de`, `it`, ... | autodetecta |
| `-f`, `--formato` | Formato de salida | `txt`, `srt`, `vtt`, `json` | `txt` |
| `-o`, `--salida` | Ruta del archivo de salida | — | mismo nombre del audio |
| `--traducir` | Traduce al inglés en vez de transcribir | flag | desactivado |
| `--device` | Dispositivo de cómputo | `cpu`, `cuda` | autodetecta |

---

## Modelos disponibles

| Modelo | Parámetros | VRAM aprox. | Velocidad relativa | Calidad |
|---|---|---|---|---|
| `tiny` | 39 M | ~1 GB | ~10x | Baja |
| `base` | 74 M | ~1 GB | ~7x | Aceptable |
| `small` | 244 M | ~2 GB | ~4x | Buena |
| `medium` | 769 M | ~5 GB | ~2x | Muy buena |
| `large` | 1550 M | ~10 GB | 1x | Excelente |
| `turbo` | 809 M | ~6 GB | ~8x | Casi `large` |

**Recomendaciones:**
- **Sin GPU** → usa `base` o `small`.
- **CPU moderna y audio en español/inglés** → `medium` da gran calidad pero lento.
- **Con GPU CUDA** → `turbo` es la mejor relación calidad/velocidad para uso general.
- **Calidad máxima** (subtítulos, transcripción profesional) → `large`.

> Los modelos se descargan la primera vez que los usas (a `~/.cache/whisper`) y quedan cacheados en disco.

---

## Formatos de salida

| Formato | Uso | Contenido |
|---|---|---|
| `txt` | Texto plano | Solo el texto transcrito, sin marcas de tiempo. |
| `srt` | Subtítulos clásicos | Texto + timestamps `HH:MM:SS,mmm`. Compatible con la mayoría de reproductores. |
| `vtt` | Subtítulos web | Igual que SRT pero en formato WebVTT (HTML5/`<video>`). |
| `json` | Datos completos | Texto + segmentos + timestamps + idioma detectado + metadatos. Útil para post-procesar. |

---

## Formatos de entrada soportados

Cualquier formato que pueda leer **ffmpeg**, incluyendo:

- **Audio:** `mp3`, `wav`, `m4a`, `aac`, `ogg`, `flac`, `opus`, `wma`.
- **Video:** `mp4`, `mkv`, `mov`, `webm`, `avi` (se extrae la pista de audio automáticamente).

No hay límite de duración por configuración: el audio se procesa en bloques de 30 s internamente.

---

## Idiomas

Whisper soporta ~100 idiomas. Algunos códigos comunes:

`es` (español), `en` (inglés), `pt` (portugués), `fr` (francés), `de` (alemán), `it` (italiano), `ja` (japonés), `zh` (chino), `ru` (ruso), `ar` (árabe), `ko` (coreano).

Si no especificas idioma, Whisper lo detecta automáticamente a partir de los primeros segundos.

---

## Estructura del proyecto

```
Transcriptor\
├── instalar.bat          Instalador (ffmpeg + venv + dependencias)
├── Transcriptor.bat      Lanzador de la GUI
├── transcriptor_gui.py   Interfaz gráfica
├── transcriptor.py       CLI
├── core.py               Lógica compartida de transcripción
├── requirements.txt      Dependencias Python
└── README.md
```

---

## Solución de problemas

**`FileNotFoundError: [WinError 2]`**
ffmpeg no está instalado o no está en el PATH. Ejecuta:
```powershell
winget install Gyan.FFmpeg
```
Luego reinicia la terminal.

**`AttributeError: 'NoneType' object has no attribute 'write'`**
Ya está corregido en el código actual. Si lo ves, asegúrate de tener la última versión de `transcriptor_gui.py`.

**El modelo descarga muy lento la primera vez**
Es normal: `medium` pesa ~1.4 GB, `large` ~3 GB. Quedan cacheados en `%USERPROFILE%\.cache\whisper`.

**No reconoce mi GPU**
Whisper requiere PyTorch con CUDA. Instálalo en el venv:
```powershell
.\.venv\Scripts\activate
pip install torch --index-url https://download.pytorch.org/whl/cu121
```
Ajusta `cu121` a tu versión de CUDA.

**La GUI se cierra sin mostrar nada**
Lanza `transcriptor_gui.py` con `python` (no `pythonw`) para ver el error en consola:
```powershell
.\.venv\Scripts\activate
python transcriptor_gui.py
```

---

## Licencia

Whisper es de OpenAI, licencia MIT. Este wrapper se distribuye sin restricciones — úsalo como te sirva.
