"""Probar sintaxis .hor v0.2 y mostrar su AST sin validar reglas de horarios."""

import argparse
from dataclasses import asdict
import json
from pathlib import Path

from schedule_compiler.api.schemas.analysis import AstNodeResponse
from schedule_compiler.api.tree import ast_to_tree
from schedule_compiler.cli.common import lexical_payload, print_diagnostics, read_source
from schedule_compiler.compiler.parser import parse


def _label(node: AstNodeResponse) -> str:
    if node.value is not None:
        return f"{node.label}: {json.dumps(node.value, ensure_ascii=False)}"
    if node.value_state is not None:
        return f"{node.label}: [{node.value_state}]"
    return node.label


def _print_tree(node: AstNodeResponse, prefix: str = "") -> None:
    for i, child in enumerate(node.children):
        last = i == len(node.children) - 1
        print(prefix + ("└── " if last else "├── ") + _label(child))
        _print_tree(child, prefix + ("    " if last else "│   "))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, nargs="?", help="Archivo .hor; omitir para leer stdin.")
    parser.add_argument("--json", action="store_true", help="AST visual, rangos y diagnósticos en JSON.")
    args = parser.parse_args()
    source, source_name = read_source(args.file, parser)
    result = parse(source, source_name)
    state = "COMPLETADA" if result.success else "CON_ERRORES" if result.executed else "NO_EJECUTADA"
    tree = ast_to_tree(result.ast) if result.ast is not None else None
    if args.json:
        print(json.dumps({
            "stage": "SINTACTICO", "state": state, "source_name": source_name,
            "lexical": lexical_payload(result.lexical),
            "ast": tree.model_dump(mode="json") if tree is not None else None,
            "diagnostics": [asdict(d) for d in result.diagnostics],
        }, ensure_ascii=False, indent=2))
    else:
        lexical_state = "completado" if result.lexical.success else "con errores"
        print(f"Análisis léxico {lexical_state}: {len(result.lexical.tokens)} tokens.")
        if tree is not None:
            print("Análisis sintáctico completado: AST generado.\n")
            print(_label(tree))
            _print_tree(tree)
        elif result.executed:
            print("Análisis sintáctico con errores. No se generó un AST.")
        else:
            print("Análisis sintáctico no ejecutado: hay errores léxicos.")
        print_diagnostics(result.lexical.diagnostics + result.diagnostics)
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
