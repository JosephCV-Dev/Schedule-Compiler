"""Lexer .hor v0.2 con Lark basic, independiente del contexto sintáctico."""

from functools import lru_cache
from importlib.resources import files
import re

from lark import Lark
from lark.exceptions import UnexpectedCharacters

from schedule_compiler.compiler.models import LexicalResult, Pattern, Token
from schedule_compiler.domain.diagnostics import Diagnostic, Severity
from schedule_compiler.domain.models import Origin, Position, Span


@lru_cache(maxsize=1)
def _engine() -> Lark:
    grammar = files("schedule_compiler.compiler").joinpath("terminals.lark").read_text(encoding="utf-8")
    return Lark(grammar, parser=None, lexer="basic")


@lru_cache(maxsize=1)
def lexical_patterns() -> tuple[Pattern, ...]:
    """Patrones tomados del mismo lexer, no una segunda copia de sus regex."""
    descriptions = {
        "CADENA": "Texto entre comillas; escapes permitidos: comilla y barra inversa.",
        "HORA_LITERAL": "Hora HH:MM; el rango numérico se revisa en semántica.",
        "ENTERO": "Entero sin signo; su valor se revisa según el campo.",
        "LLAVE_APERTURA": "Inicio de bloque.",
        "LLAVE_CIERRE": "Fin de bloque.",
    }
    return tuple(Pattern(
        id=terminal.name.lower(),
        description=(f"Palabra reservada {terminal.name.removeprefix('KW_')}."
                     if terminal.name.startswith("KW_") else descriptions[terminal.name]),
        expression=terminal.pattern.to_regexp(),
    ) for terminal in _engine().terminals if terminal.name not in {"ESPACIO", "COMENTARIO"})


def _position(source: str, offset: int) -> Position:
    line = source.count("\n", 0, offset) + 1
    column = offset - source.rfind("\n", 0, offset)
    return Position(offset, line, column)


def _diagnostic(source: str, source_name: str, start: int, end: int,
                code: str, message: str) -> Diagnostic:
    return Diagnostic(
        code=code, stage="LEXICO", severity=Severity.ERROR, message=message,
        origin=Origin("TEXTO", source_name, span=Span(_position(source, start), _position(source, end))),
    )


def _string_error(source: str, source_name: str, start: int) -> Diagnostic:
    """Explica el fallo de una cadena que Lark no pudo reconocer completa."""
    i = start + 1
    while i < len(source):
        if source[i] in "\r\n":
            return _diagnostic(source, source_name, start, i, "SALTO_LINEA_EN_CADENA",
                               "La cadena debe cerrar sus comillas en la misma línea.")
        if source[i] == "\\":
            if i + 1 == len(source):
                break
            escaped = source[i + 1]
            if escaped in "\r\n":
                return _diagnostic(source, source_name, start, i + 1, "SALTO_LINEA_EN_CADENA",
                                   "La cadena no admite saltos de línea, ni precedidos de una barra inversa.")
            if escaped not in {'"', "\\"}:
                return _diagnostic(source, source_name, i, i + 2, "ESCAPE_INVALIDO",
                                   f"Escape {source[i:i + 2]!r} no permitido; usa solo comilla o barra inversa escapadas.")
            i += 2
        else:
            i += 1
    return _diagnostic(source, source_name, start, len(source), "CADENA_SIN_CIERRE",
                       "La cadena no tiene comillas de cierre.")


def _unexpected(source: str, source_name: str, start: int) -> Diagnostic:
    if source[start] == '"':
        return _string_error(source, source_name, start)
    fragment = re.match(r"[\w:]+", source[start:])
    if fragment:
        text = fragment.group()
        if text[0].isdigit() and ":" in text:
            code = "FORMATO_HORA_INVALIDO"
            message = f"Hora {text!r} no reconocida; escribe dos dígitos, dos puntos y dos dígitos (HH:MM)."
        else:
            code = "LEXEMA_NO_RECONOCIDO"
            message = f"Lexema {text!r} no reconocido; usa palabras reservadas en mayúsculas sin acentos y textos entre comillas."
        return _diagnostic(source, source_name, start, start + len(text), code, message)
    char = source[start]
    return _diagnostic(source, source_name, start, start + 1, "CARACTER_NO_PERMITIDO",
                       f"Carácter {char!r} (U+{ord(char):04X}) no definido en .hor v0.2.")


def tokenize(source: str, source_name: str = "editor") -> LexicalResult:
    """Devuelve tokens y, al fallar, el primer error con el prefijo reconocido.

    No repara el texto ni comprueba estructura, referencias o reglas de horarios.
    Los lexemas y posiciones siempre corresponden al texto recibido sin alterarlo.
    """
    if not source_name:
        raise ValueError("La fuente necesita un nombre no vacío.")
    tokens = []
    diagnostics = ()
    try:
        for token in _engine().lex(source):
            tokens.append(Token(
                kind=token.type, lexeme=str(token), pattern_id=token.type.lower(),
                span=Span(Position(token.start_pos, token.line, token.column),
                          Position(token.end_pos, token.end_line, token.end_column)),
            ))
    except UnexpectedCharacters as error:
        diagnostics = (_unexpected(source, source_name, error.pos_in_stream),)
    return LexicalResult(source_name, lexical_patterns(), tuple(tokens), diagnostics)
