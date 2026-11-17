"""Auditoría calculada del catálogo cargado; no reutiliza la auditoría histórica."""

from schedule_compiler.domain.diagnostics import Diagnostic, Severity
from schedule_compiler.domain.models import Catalog, ValueState
from schedule_compiler.domain.validation import RoomCollision, room_collisions


def collision_diagnostic(collision: RoomCollision, stage: str = "SEMANTICO") -> Diagnostic:
    a, b = collision.first, collision.second
    if (stage == "SEMANTICO" and b.origins and b.origins[0].kind == "TEXTO"
            and (not a.origins or a.origins[0].kind != "TEXTO")):
        a, b = b, a
    if collision.uncertain:
        code, severity = "IDENTIDAD_AULA_PENDIENTE", Severity.WARNING
        message = (f"{a.offer_id} y {b.offer_id} se superponen el {a.day.value}; no se ha confirmado "
                   f"si {a.room.value!r} y {b.room.value!r} son el mismo espacio.")
    else:
        code, severity = "CHOQUE_AULA", Severity.ERROR
        message = (f"Aula ocupada: {a.room.value!r}, {a.day.value}; se superponen "
                   f"{a.offer_id} y {b.offer_id}.")
    return Diagnostic(code, stage, severity, message,
                      a.origins[0] if a.origins else None, b.origins + a.origins[1:])


def audit_catalog(catalog: Catalog) -> tuple[Diagnostic, ...]:
    sessions = tuple(s for offer in catalog.offers for s in offer.sessions)
    diagnostics = [collision_diagnostic(c, "CATALOGO") for c in room_collisions(sessions)]
    for session in sessions:
        if session.room.state != ValueState.KNOWN:
            diagnostics.append(Diagnostic(
                "AULA_PENDIENTE", "CATALOGO", Severity.WARNING,
                f"{session.offer_id}, {session.day.value}: aula pendiente; no reserva un espacio.",
                session.origins[0] if session.origins else None, session.origins[1:],
            ))
    for change in catalog.adjustments:
        diagnostics.append(Diagnostic(
            "AJUSTE_CATALOGO", "CATALOGO", Severity.INFO,
            f"{change.session_id}: aula anterior {change.previous_room!r}; sigue sin asignación resuelta. {change.reason}",
            change.origin,
        ))
    return tuple(diagnostics)
