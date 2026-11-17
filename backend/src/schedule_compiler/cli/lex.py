"""Probar el analizador léxico con un archivo .hor o texto de entrada estándar."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

from schedule_compiler.compiler.lexer import tokenize
from schedule_compiler.compiler.models import LexicalResult


def _table(result: LexicalResult) -> None:
    patterns = {p.id: p.expression for p in result.patterns}
    rows = [("TOKEN", "LEXEMA", "PATRÓN", "LÍNEA", "COLUMNA")]
    rows.extend((t.kind, json.dumps(t.lexeme, ensure_ascii=False), patterns[t.pattern_id],
                 str(t.span.start.line), str(t.span.start.column)) for t in result.tokens)
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    for row in rows:
        print(" | ".join(value.ljust(width) for value, width in zip(row, widths)))
    state = "completado" if result.success else "con errores"
    print(f"\nAnálisis léxico {state}: {len(result.tokens)} tokens reconocidos.")
    for diagnostic in result.diagnostics:
        assert diagnostic.origin is not None and diagnostic.origin.span is not None
        position = diagnostic.origin.span.start
        print(f"{result.source_name}:{position.line}:{position.column}: "
              f"{diagnostic.code}: {diagnostic.message}", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, nargs="?", help="Archivo .hor; omitir para leer stdin.")
    parser.add_argument("--json", action="store_true", help="Salida estructurada en JSON.")
    args = parser.parse_args()
    if args.file is None and sys.stdin.isatty():
        parser.error("Indica un archivo .hor o proporciona texto por la entrada estándar.")
    try:
        source = args.file.read_bytes().decode("utf-8-sig") if args.file else sys.stdin.read()
    except (OSError, UnicodeError) as error:
        parser.exit(2, f"No se pudo leer la entrada: {error}\n")
    result = tokenize(source, str(args.file) if args.file else "stdin")
    if args.json:
        payload = {"stage": "LEXICO", "state": "COMPLETADA" if result.success else "CON_ERRORES",
                   **asdict(result)}
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _table(result)
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
