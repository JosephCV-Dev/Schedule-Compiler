"""Transforma estructura Lark ya reconocida a nodos propios del lenguaje."""

import re

from lark import Discard, Token, Transformer, v_args

from schedule_compiler.compiler.models import (
    EnrollmentDeclaration, IntegerLiteral, LocatedValue, OfferDeclaration,
    Program, ScheduleDeclaration, SessionDeclaration, TextLiteral,
)
from schedule_compiler.compiler.positions import source_span
from schedule_compiler.domain.models import FieldValue, Position, Span, ValueState, Weekday


def token_span(token: Token) -> Span:
    return Span(Position(token.start_pos, token.line, token.column),
                Position(token.end_pos, token.end_line, token.end_column))


class IntegerRepresentationError(ValueError):
    def __init__(self, span: Span):
        super().__init__("El entero supera el límite de conversión del intérprete Python.")
        self.span = span


@v_args(meta=True)
class AstBuilder(Transformer):
    def __init__(self, source: str):
        super().__init__()
        self.source = source

    def CADENA(self, token: Token) -> TextLiteral:
        # Una sola pasada: solo se decodifican los dos escapes que admite el lexer.
        value = re.sub(r'\\(["\\])', lambda match: match[1], str(token)[1:-1])
        return TextLiteral(value, token_span(token))

    def HORA_LITERAL(self, token: Token) -> TextLiteral:
        return TextLiteral(str(token), token_span(token))

    def ENTERO(self, token: Token) -> IntegerLiteral:
        try:
            value = int(str(token))
        except ValueError as error:
            raise IntegerRepresentationError(token_span(token)) from error
        return IntegerLiteral(value, token_span(token))

    def __default_token__(self, token: Token):
        if token.type in {f"KW_{day.value}" for day in Weekday}:
            return TextLiteral(str(token), token_span(token))
        if token.type in {"KW_DESCONOCIDO", "KW_SIN_ASIGNAR"}:
            state = ValueState.UNKNOWN if token.type == "KW_DESCONOCIDO" else ValueState.UNASSIGNED
            return LocatedValue(FieldValue(state), token_span(token))
        return Discard

    def _span(self, meta) -> Span:
        return Span(Position(meta.start_pos, meta.line, meta.column),
                    Position(meta.end_pos, meta.end_line, meta.end_column))

    def _located(self, child: TextLiteral | LocatedValue) -> LocatedValue:
        if isinstance(child, LocatedValue):
            return child
        return LocatedValue(FieldValue(ValueState.KNOWN, child.value), child.span)

    def group_value(self, meta, children):
        return self._located(children[0])

    def optional_value(self, meta, children):
        return self._located(children[0])

    def program(self, meta, children) -> Program:
        return Program(tuple(children), source_span(self.source, 0, len(self.source)))

    def offer(self, meta, children) -> OfferDeclaration:
        identifier, subject, group, teacher, *sessions = children
        return OfferDeclaration(identifier, subject, group, teacher, tuple(sessions), self._span(meta))

    def session(self, meta, children) -> SessionDeclaration:
        room, day, hour, duration = children
        return SessionDeclaration(room, day, hour, duration, self._span(meta))

    def schedule(self, meta, children) -> ScheduleDeclaration:
        name, *enrollments = children
        return ScheduleDeclaration(name, tuple(enrollments), self._span(meta))

    def enrollment(self, meta, children) -> EnrollmentDeclaration:
        return EnrollmentDeclaration(children[0], self._span(meta))
