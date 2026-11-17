"""Probar el analizador léxico con un archivo .hor o texto de entrada estándar."""

import argparse
import json
from pathlib import Path

from schedule_compiler.cli.common import lexical_payload, print_diagnostics, read_source
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
    print_diagnostics(result.diagnostics)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, nargs="?", help="Archivo .hor; omitir para leer stdin.")
    parser.add_argument("--json", action="store_true", help="Salida estructurada en JSON.")
    args = parser.parse_args()
    source, source_name = read_source(args.file, parser)
    result = tokenize(source, source_name)
    if args.json:
        print(json.dumps(lexical_payload(result), ensure_ascii=False, indent=2))
    else:
        _table(result)
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
