"""Parser LALR de .hor v0.2. Consume los tokens del lexer basic existente."""

from functools import lru_cache
from importlib.resources import files

from lark import Lark, Token
from lark.exceptions import UnexpectedToken, VisitError

from schedule_compiler.compiler.ast_builder import AstBuilder, IntegerRepresentationError, token_span
from schedule_compiler.compiler.lexer import tokenize
from schedule_compiler.compiler.models import ParseResult
from schedule_compiler.compiler.positions import source_span
from schedule_compiler.domain.diagnostics import Diagnostic, Severity
from schedule_compiler.domain.models import Origin, Span


@lru_cache(maxsize=1)
def _engine() -> Lark:
    resources = files("schedule_compiler.compiler")
    terminals = resources.joinpath("terminals.lark").read_text(encoding="utf-8")
    grammar = resources.joinpath("grammar.lark").read_text(encoding="utf-8")
    return Lark(terminals + "\n" + grammar, parser="lalr", lexer="basic", start="program",
                propagate_positions=True)


def _expected(names: set[str]) -> str:
    labels = {"CADENA": "una cadena entre comillas", "ENTERO": "un entero",
              "HORA_LITERAL": "una hora HH:MM", "LLAVE_APERTURA": "'{'",
              "LLAVE_CIERRE": "'}'", "$END": "el fin del archivo"}
    return ", ".join(sorted(labels.get(name, name.removeprefix("KW_")) for name in names))


def _error(source_name: str, code: str, message: str, span: Span) -> Diagnostic:
    return Diagnostic(code, "SINTACTICO", Severity.ERROR, message,
                      Origin("TEXTO", source_name, span=span))


def parse(source: str, source_name: str = "editor") -> ParseResult:
    lexical = tokenize(source, source_name)
    if not lexical.success:
        return ParseResult(lexical)
    parser = _engine().parse_interactive()
    try:
        for token in lexical.tokens:
            start, end = token.span.start, token.span.end
            parser.feed_token(Token(token.kind, token.lexeme, start_pos=start.offset,
                                    line=start.line, column=start.column,
                                    end_pos=end.offset, end_line=end.line, end_column=end.column))
        tree = parser.feed_eof()
    except UnexpectedToken as error:
        if error.token.type == "$END":
            empty = not lexical.tokens
            code = "PROGRAMA_VACIO" if empty else "FIN_INESPERADO"
            message = ("El programa está vacío; declara al menos una OFERTA o un HORARIO." if empty else
                       f"Fin de entrada inesperado; se esperaba {_expected(error.expected)}.")
            span = source_span(source, len(source), len(source))
        else:
            code = "TOKEN_INESPERADO"
            message = f"Se encontró {str(error.token)!r}; se esperaba {_expected(error.expected)}."
            span = token_span(error.token)
        return ParseResult(lexical, diagnostics=(_error(source_name, code, message, span),))
    try:
        ast = AstBuilder(source).transform(tree)
    except VisitError as error:
        if not isinstance(error.orig_exc, IntegerRepresentationError):
            raise
        return ParseResult(lexical, diagnostics=(
            _error(source_name, "ENTERO_NO_REPRESENTABLE", str(error.orig_exc), error.orig_exc.span),
        ))
    return ParseResult(lexical, ast=ast)
