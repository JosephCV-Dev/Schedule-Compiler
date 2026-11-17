"""Datos del dominio. Este módulo usa únicamente la biblioteca estándar."""

from dataclasses import dataclass
from enum import StrEnum


class ValueState(StrEnum):
    KNOWN = "CONOCIDO"
    UNKNOWN = "DESCONOCIDO"
    UNASSIGNED = "SIN_ASIGNAR"


class Weekday(StrEnum):
    MONDAY = "LUNES"
    TUESDAY = "MARTES"
    WEDNESDAY = "MIERCOLES"
    THURSDAY = "JUEVES"
    FRIDAY = "VIERNES"
    SATURDAY = "SABADO"
    SUNDAY = "DOMINGO"


@dataclass(frozen=True)
class Position:
    """Offset en caracteres desde 0; línea y columna desde 1."""

    offset: int
    line: int
    column: int

    def __post_init__(self) -> None:
        if self.offset < 0 or self.line < 1 or self.column < 1:
            raise ValueError("Posición de texto fuera de rango.")


@dataclass(frozen=True)
class Span:
    """Intervalo de texto [start, end), con fin exclusivo."""

    start: Position
    end: Position

    def __post_init__(self) -> None:
        if self.end.offset < self.start.offset or (
            self.end.line, self.end.column
        ) < (self.start.line, self.start.column):
            raise ValueError("El fin de un rango no puede preceder a su inicio.")


@dataclass(frozen=True)
class Origin:
    """Texto, celdas de Excel o ubicación en un recurso JSON."""

    kind: str
    source_id: str
    span: Span | None = None
    sheet: str | None = None
    cells: tuple[str, ...] = ()
    pointer: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("El origen necesita identificar su fuente.")
        if self.kind not in {"TEXTO", "EXCEL", "JSON"}:
            raise ValueError("Tipo de origen no reconocido.")
        if self.kind == "TEXTO" and self.span is None:
            raise ValueError("Un origen de texto requiere un rango.")
        if self.kind == "EXCEL" and (not self.sheet or not self.cells):
            raise ValueError("Un origen de Excel requiere hoja y celdas.")
        if self.kind == "JSON" and self.pointer is None:
            raise ValueError("Un origen JSON requiere un JSON Pointer.")


@dataclass(frozen=True)
class FieldValue:
    state: ValueState
    value: str | None = None

    def __post_init__(self) -> None:
        if (self.state == ValueState.KNOWN) != (self.value is not None):
            raise ValueError("Solo un dato conocido puede contener un valor.")


@dataclass(frozen=True)
class Interval:
    """Intervalo ya normalizado. Los valores inválidos permanecen en el AST."""

    start_minute: int
    end_minute: int

    def __post_init__(self) -> None:
        if not 0 <= self.start_minute < self.end_minute <= 1440:
            raise ValueError("Intervalo normalizado inválido.")


@dataclass(frozen=True)
class RoomIdentity:
    original: str
    key: str
    rule: str


@dataclass(frozen=True)
class Session:
    id: str
    offer_id: str
    day: Weekday
    interval: Interval
    room: FieldValue
    origins: tuple[Origin, ...]


@dataclass(frozen=True)
class Offer:
    id: str
    subject: str
    group: FieldValue
    teacher: FieldValue
    sessions: tuple[Session, ...]
    origins: tuple[Origin, ...]
    subject_id: str | None = None
    weekly_hours: int | None = None


@dataclass(frozen=True)
class PersonalSchedule:
    name: str
    offer_ids: tuple[str, ...]


@dataclass(frozen=True)
class Room:
    id: str
    capacity: int | None
    type: str | None


@dataclass(frozen=True)
class Group:
    id: str
    students: int | None


@dataclass(frozen=True)
class Subject:
    id: str
    source_names: tuple[str, ...]
    requires_lab: bool | None


@dataclass(frozen=True)
class CatalogSource:
    file: str
    sha256: str
    sheet: str


@dataclass(frozen=True)
class CatalogAdjustment:
    session_id: str
    previous_room: str | None
    new_room: str | None
    reason: str
    origin: Origin


@dataclass(frozen=True)
class Catalog:
    id: str
    source: CatalogSource
    snapshot_sha256: str
    offers: tuple[Offer, ...]
    rooms: tuple[Room, ...]
    groups: tuple[Group, ...]
    subjects: tuple[Subject, ...]
    adjustments: tuple[CatalogAdjustment, ...] = ()
    limitations: tuple[str, ...] = ()
    source_audit_scope: str = "FUENTE_ORIGINAL"


@dataclass(frozen=True)
class ValidationPolicy:
    id: str
    version: str
    teacher_rules_enabled: bool
    allow_new_rooms: bool
    check_room_occupancy: bool
    unassigned_room_status: str
    auto_assign_rooms: bool
    capacity: str
    laboratory: str
    permitted_hours: str
