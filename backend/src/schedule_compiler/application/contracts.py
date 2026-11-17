"""Contrato interno de resultados; no ejecuta ninguna fase del compilador."""

from dataclasses import dataclass
from enum import StrEnum

from schedule_compiler.compiler.models import Pattern, Program, Token
from schedule_compiler.domain.diagnostics import Diagnostic, Severity
from schedule_compiler.domain.models import FieldValue, Origin, Session


class AnalysisStatus(StrEnum):
    VALID = "VALIDO"
    INVALID = "INVALIDO"
    INCOMPLETE = "INCOMPLETO"


class Scope(StrEnum):
    PERSONAL = "PERSONAL"
    PROPOSAL = "PROPUESTA"


class Stage(StrEnum):
    LEXICAL = "LEXICO"
    SYNTACTIC = "SINTACTICO"
    SEMANTIC = "SEMANTICO"


class PhaseState(StrEnum):
    COMPLETED = "COMPLETADA"
    FAILED = "CON_ERRORES"
    NOT_RUN = "NO_EJECUTADA"


class CheckState(StrEnum):
    PASSED = "CUMPLE"
    FAILED = "INCUMPLE"
    UNKNOWN = "NO_EVALUABLE"
    NOT_APPLICABLE = "NO_APLICA"
    DISABLED = "DESACTIVADA"


@dataclass(frozen=True)
class PhaseReport:
    stage: Stage
    state: PhaseState


@dataclass(frozen=True)
class Check:
    code: str
    state: CheckState
    required: bool
    message: str
    origins: tuple[Origin, ...] = ()


@dataclass(frozen=True)
class SymbolAttribute:
    name: str
    value: FieldValue


@dataclass(frozen=True)
class Symbol:
    id: str
    kind: str
    label: str
    attributes: tuple[SymbolAttribute, ...]
    origins: tuple[Origin, ...]


@dataclass(frozen=True)
class ScheduleView:
    name: str
    sessions: tuple[Session, ...]


@dataclass(frozen=True)
class AnalysisMetadata:
    language_version: str
    catalog_id: str
    catalog_sha256: str
    policy_id: str
    policy_version: str
    scope: Scope
    source_name: str


@dataclass(frozen=True)
class AnalysisResult:
    metadata: AnalysisMetadata
    status: AnalysisStatus
    phases: tuple[PhaseReport, ...]
    patterns: tuple[Pattern, ...] = ()
    tokens: tuple[Token, ...] = ()
    ast: Program | None = None
    symbols: tuple[Symbol, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()
    catalog_diagnostics: tuple[Diagnostic, ...] = ()
    checks: tuple[Check, ...] = ()
    schedules: tuple[ScheduleView, ...] = ()

    def __post_init__(self) -> None:
        if tuple(p.stage for p in self.phases) != tuple(Stage):
            raise ValueError("Se requieren las tres fases en orden léxico/sintáctico/semántico.")
        for previous, current in zip(self.phases, self.phases[1:]):
            if previous.state != PhaseState.COMPLETED and current.state != PhaseState.NOT_RUN:
                raise ValueError("Una fase no puede ejecutarse si falló su dependencia.")
        syntax_completed = self.phases[1].state == PhaseState.COMPLETED
        if syntax_completed != (self.ast is not None):
            raise ValueError("Solo una sintaxis completada entrega un AST.")
        patterns = {p.id for p in self.patterns}
        if len(patterns) != len(self.patterns) or any(t.pattern_id not in patterns for t in self.tokens):
            raise ValueError("Los patrones deben ser únicos y resolver todos los tokens.")
        failed = (
            any(d.severity == Severity.ERROR for d in self.diagnostics)
            or any(c.state == CheckState.FAILED for c in self.checks)
            or any(p.state == PhaseState.FAILED for p in self.phases)
        )
        pending = any(c.required and c.state == CheckState.UNKNOWN for c in self.checks)
        if any(c.required and c.state == CheckState.DISABLED for c in self.checks):
            raise ValueError("Una comprobación desactivada no puede declararse requerida.")
        if failed != (self.status == AnalysisStatus.INVALID):
            raise ValueError("El estado debe reflejar los incumplimientos del análisis.")
        if not failed:
            if self.phases[-1].state != PhaseState.COMPLETED:
                raise ValueError("Un resultado final sin errores requiere completar las fases.")
            if pending != (self.status == AnalysisStatus.INCOMPLETE):
                raise ValueError("Las comprobaciones requeridas pendientes producen INCOMPLETO.")
