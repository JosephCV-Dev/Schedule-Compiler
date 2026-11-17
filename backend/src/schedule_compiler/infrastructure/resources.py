"""Directorios configurables y lista explícita de ejemplos para la app local."""

import os
from pathlib import Path

from schedule_compiler.application.contracts import Scope

EXAMPLES = {
    "carolina": ("horario_carolina.hor", "Horario completo de Carolina", Scope.PERSONAL),
    "carolina-seleccion": ("horario_carolina_seleccion.hor", "Selección de Carolina", Scope.PERSONAL),
    "personal": ("horario_personal.hor", "Horario personal", Scope.PERSONAL),
    "compiladores": ("oferta_compiladores.hor", "Oferta de Compiladores", Scope.PROPOSAL),
    "error-lexico": ("lexico/error_caracter.hor", "Error léxico", Scope.PERSONAL),
    "error-sintactico": ("sintactico/error_tipo.hor", "Error sintáctico", Scope.PROPOSAL),
    "error-semantico": ("sintactico/valores_para_semantica.hor", "Hora y duración inválidas", Scope.PROPOSAL),
    "aula-pendiente": ("semantico/aula_pendiente.hor", "Aula pendiente", Scope.PROPOSAL),
    "aula-ocupada": ("semantico/aula_ocupada.hor", "Aula ocupada", Scope.PROPOSAL),
}


def default_directories() -> tuple[Path, Path]:
    root = Path(__file__).resolve().parents[4]
    return (Path(os.environ.get("SCHEDULE_COMPILER_DATA_DIR", str(root / "data"))),
            Path(os.environ.get("SCHEDULE_COMPILER_EXAMPLES_DIR", str(root / "examples"))))


class ExampleRepository:
    def __init__(self, directory: Path):
        self.directory = directory.resolve()

    def read(self, identifier: str) -> tuple[str, str, Scope]:
        if identifier not in EXAMPLES:
            raise ValueError("Ejemplo no reconocido.")
        filename, _, scope = EXAMPLES[identifier]
        return (self.directory / filename).read_bytes().decode("utf-8-sig"), filename, scope
