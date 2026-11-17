"""Diagnósticos compartidos por las fases y los casos de uso, sin frameworks."""

from dataclasses import dataclass
from enum import StrEnum

from schedule_compiler.domain.models import Origin


class Severity(StrEnum):
    ERROR = "ERROR"
    WARNING = "ADVERTENCIA"
    INFO = "INFO"


@dataclass(frozen=True)
class Diagnostic:
    code: str
    stage: str
    severity: Severity
    message: str
    origin: Origin | None = None
    related: tuple[Origin, ...] = ()
