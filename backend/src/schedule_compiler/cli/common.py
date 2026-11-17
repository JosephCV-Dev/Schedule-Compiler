"""Entrada y presentación de diagnósticos compartidas por las herramientas CLI."""

import argparse
from dataclasses import asdict
from pathlib import Path
import sys

from schedule_compiler.compiler.models import LexicalResult
from schedule_compiler.domain.diagnostics import Diagnostic


def read_source(file: Path | None, parser: argparse.ArgumentParser) -> tuple[str, str]:
    if file is None and sys.stdin.isatty():
        parser.error("Indica un archivo .hor o proporciona texto por la entrada estándar.")
    try:
        source = file.read_bytes().decode("utf-8-sig") if file else sys.stdin.read()
    except (OSError, UnicodeError) as error:
        parser.exit(2, f"No se pudo leer la entrada: {error}\n")
    return source, str(file) if file else "stdin"


def lexical_payload(result: LexicalResult) -> dict:
    return {"stage": "LEXICO", "state": "COMPLETADA" if result.success else "CON_ERRORES",
            **asdict(result)}


def print_diagnostics(diagnostics: tuple[Diagnostic, ...]) -> None:
    for diagnostic in diagnostics:
        assert diagnostic.origin is not None and diagnostic.origin.span is not None
        position = diagnostic.origin.span.start
        print(f"{diagnostic.origin.source_id}:{position.line}:{position.column}: "
              f"{diagnostic.code}: {diagnostic.message}", file=sys.stderr)
