"""Estados de comprobación y reglas de intervalos, sin dependencias web."""

from dataclasses import dataclass
from enum import StrEnum
from itertools import combinations

from schedule_compiler.domain.models import Origin, Session, ValueState
from schedule_compiler.domain.rooms import room_identity


class CheckState(StrEnum):
    PASSED = "CUMPLE"
    FAILED = "INCUMPLE"
    UNKNOWN = "NO_EVALUABLE"
    NOT_APPLICABLE = "NO_APLICA"
    DISABLED = "DESACTIVADA"


@dataclass(frozen=True)
class Check:
    code: str
    state: CheckState
    required: bool
    message: str
    origins: tuple[Origin, ...] = ()


@dataclass(frozen=True)
class RoomCollision:
    first: Session
    second: Session
    uncertain: bool = False


def overlaps(first: Session, second: Session) -> bool:
    return (first.day == second.day
            and first.interval.start_minute < second.interval.end_minute
            and second.interval.start_minute < first.interval.end_minute)


def room_collisions(sessions: tuple[Session, ...]) -> tuple[RoomCollision, ...]:
    """No reserva aulas desconocidas ni fusiona las equivalencias pendientes."""
    known = [(s, room_identity(s.room.value).key) for s in sessions
             if s.room.state == ValueState.KNOWN and s.room.value and s.room.value.strip()]
    pending_alias = {"NOMBRE:CENTRO DE CÓMPUTO", "AC:FIE1:0001"}
    collisions = []
    for (a, room_a), (b, room_b) in combinations(known, 2):
        if a.id == b.id or not overlaps(a, b):
            continue
        if room_a == room_b:
            collisions.append(RoomCollision(a, b))
        elif {room_a, room_b} == pending_alias:
            collisions.append(RoomCollision(a, b, uncertain=True))
    return tuple(collisions)
