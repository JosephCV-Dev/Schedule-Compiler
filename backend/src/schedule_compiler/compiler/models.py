"""Salida léxica y AST propios: no dependen de Lark ni de HTTP."""

from dataclasses import dataclass

from schedule_compiler.domain.diagnostics import Diagnostic, Severity
from schedule_compiler.domain.models import FieldValue, Span


@dataclass(frozen=True)
class Pattern:
    id: str
    description: str
    expression: str


@dataclass(frozen=True)
class Token:
    kind: str
    lexeme: str
    pattern_id: str
    span: Span


@dataclass(frozen=True)
class LexicalResult:
    source_name: str
    patterns: tuple[Pattern, ...]
    tokens: tuple[Token, ...]
    diagnostics: tuple[Diagnostic, ...] = ()

    @property
    def success(self) -> bool:
        """Solo indica éxito léxico, nunca validez del horario."""
        return not any(d.severity == Severity.ERROR for d in self.diagnostics)


@dataclass(frozen=True)
class TextLiteral:
    value: str
    span: Span


@dataclass(frozen=True)
class IntegerLiteral:
    """Puede contener cero: su validez se decide durante la semántica."""

    value: int
    span: Span


@dataclass(frozen=True)
class LocatedValue:
    value: FieldValue
    span: Span


@dataclass(frozen=True)
class SessionDeclaration:
    room: LocatedValue
    day: TextLiteral
    hour: TextLiteral
    duration: IntegerLiteral
    span: Span


@dataclass(frozen=True)
class OfferDeclaration:
    identifier: TextLiteral
    subject: TextLiteral
    group: LocatedValue
    teacher: LocatedValue
    sessions: tuple[SessionDeclaration, ...]
    span: Span


@dataclass(frozen=True)
class EnrollmentDeclaration:
    offer_id: TextLiteral
    span: Span


@dataclass(frozen=True)
class ScheduleDeclaration:
    name: TextLiteral
    enrollments: tuple[EnrollmentDeclaration, ...]
    span: Span


@dataclass(frozen=True)
class Program:
    declarations: tuple[OfferDeclaration | ScheduleDeclaration, ...]
    span: Span


AstNode = Program | OfferDeclaration | SessionDeclaration | ScheduleDeclaration | EnrollmentDeclaration
