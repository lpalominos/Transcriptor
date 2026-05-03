import argparse
import sys
from pathlib import Path

from core import FORMATOS, MODELOS, guardar_resultado, transcribir


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Transcriptor de audio a texto usando Whisper de OpenAI."
    )
    parser.add_argument("audio", type=Path, help="Ruta al archivo de audio o video.")
    parser.add_argument("-m", "--modelo", default="base", choices=list(MODELOS))
    parser.add_argument("-l", "--idioma", default=None)
    parser.add_argument("-f", "--formato", default="txt", choices=list(FORMATOS))
    parser.add_argument("-o", "--salida", type=Path, default=None)
    parser.add_argument("--traducir", action="store_true")
    parser.add_argument("--device", default=None)
    args = parser.parse_args()

    if not args.audio.exists():
        print(f"Error: no se encontró '{args.audio}'.", file=sys.stderr)
        return 1

    salida = args.salida or args.audio.with_suffix(f".{args.formato}")

    print(f"Cargando modelo '{args.modelo}'...", file=sys.stderr)
    print(f"Transcribiendo '{args.audio.name}'...", file=sys.stderr)
    resultado = transcribir(
        args.audio,
        modelo=args.modelo,
        idioma=args.idioma,
        traducir=args.traducir,
        device=args.device,
    )

    guardar_resultado(resultado, salida, args.formato)
    print(f"Listo. Salida: {salida}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
