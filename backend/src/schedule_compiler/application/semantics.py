"""Resolución del AST y comprobaciones del alcance configurado para .hor v0.2."""

from dataclasses import dataclass
from itertools import combinations

from schedule_compiler.application.audit import collision_diagnostic
from schedule_compiler.application.catalogs import overlay_offers
from schedule_compiler.application.contracts import ScheduleView, Scope, Symbol, SymbolAttribute
from schedule_compiler.compiler.models import OfferDeclaration, Program, ScheduleDeclaration
from schedule_compiler.domain.diagnostics import Diagnostic, Severity
from schedule_compiler.domain.models import (
    Catalog, FieldValue, Interval, Offer, Origin, Session, Span, ValidationPolicy, ValueState, Weekday,
)
from schedule_compiler.domain.rooms import room_identity
from schedule_compiler.domain.validation import Check, CheckState, overlaps, room_collisions


@dataclass(frozen=True)
class SemanticReport:
    diagnostics: tuple[Diagnostic, ...]
    checks: tuple[Check, ...]
    symbols: tuple[Symbol, ...]
    schedules: tuple[ScheduleView, ...]


def analyze_semantics(program: Program, catalog: Catalog, policy: ValidationPolicy,
                      source_name: str, scope: Scope) -> SemanticReport:
    return _SemanticRun(catalog, policy, source_name, scope).run(program)


class _SemanticRun:
    """Estado local de una sola solicitud; nunca modifica catálogo ni política."""

    def __init__(self, catalog: Catalog, policy: ValidationPolicy, source_name: str, scope: Scope):
        self.catalog, self.policy, self.source_name, self.scope = catalog, policy, source_name, scope
        self.base = {o.id: o for o in catalog.offers}
        self.diagnostics: list[Diagnostic] = []
        self.checks: list[Check] = []

    def origin(self, span: Span) -> Origin:
        return Origin("TEXTO", self.source_name, span=span)

    def fail(self, code: str, message: str, origin: Origin, related: tuple[Origin, ...] = ()) -> None:
        self.diagnostics.append(Diagnostic(code, "SEMANTICO", Severity.ERROR, message, origin, related))
        self.checks.append(Check(code, CheckState.FAILED, True, message, (origin,) + related))

    def normalize(self, node: OfferDeclaration) -> Offer | None:
        identifier = node.identifier.value
        if not identifier.strip():
            self.fail("IDENTIFICADOR_VACIO", "La oferta necesita un identificador no vacío.", self.origin(node.identifier.span))
            return None
        if not node.subject.value.strip():
            self.fail("MATERIA_VACIA", "La materia necesita un nombre no vacío.", self.origin(node.subject.span))
        previous = self.base.get(identifier)
        sessions = []
        for i, session in enumerate(node.sessions):
            hour, minute = map(int, session.hour.value.split(":"))
            hour_ok = hour < 24 and minute < 60
            duration_ok = session.duration.value > 0
            if not hour_ok:
                self.fail("HORA_INVALIDA", "La hora de inicio debe estar entre 00:00 y 23:59.", self.origin(session.hour.span))
            else:
                self.checks.append(Check("HORA_VALIDA", CheckState.PASSED, True,
                                         "Hora de inicio válida.", (self.origin(session.hour.span),)))
            start = hour * 60 + minute
            end = start + session.duration.value * 60
            if not duration_ok or (hour_ok and end > 1440):
                duration_ok = False
                self.fail("DURACION_INVALIDA", "La duración debe ser positiva y terminar dentro del mismo día.",
                          self.origin(session.duration.span))
            else:
                self.checks.append(Check("DURACION_VALIDA", CheckState.PASSED, True,
                                         "Duración positiva.", (self.origin(session.duration.span),)))
            room = session.room.value
            room_ok = room.state != ValueState.KNOWN or bool(room.value.strip())
            if not room_ok:
                self.fail("AULA_VACIA", "Escribe un aula o un marcador explícito.", self.origin(session.room.span))
            if hour_ok and duration_ok and room_ok:
                sessions.append(Session(
                    id=f"{identifier}:sesion:{i}", offer_id=identifier,
                    day=Weekday(session.day.value), interval=Interval(start, end), room=room,
                    origins=(self.origin(session.span), self.origin(session.room.span), self.origin(session.hour.span)),
                ))
        return Offer(identifier, node.subject.value, node.group.value, node.teacher.value,
                     tuple(sessions), (self.origin(node.span),),
                     previous.subject_id if previous else None, previous.weekly_hours if previous else None)

    def run(self, program: Program) -> SemanticReport:
        if (self.policy.teacher_rules_enabled or self.policy.auto_assign_rooms
                or self.policy.unassigned_room_status != "PENDIENTE"):
            raise ValueError("La política requiere capacidades no soportadas por .hor v0.2.")
        self.checks.append(Check("REGLAS_DOCENTES", CheckState.DISABLED, False,
                                 "Docente como texto libre: sin catálogo, asignación ni cruces de profesores."))
        for code, setting in (("CAPACIDAD", self.policy.capacity), ("LABORATORIO", self.policy.laboratory),
                              ("HORARIO_PERMITIDO", self.policy.permitted_hours)):
            if setting not in {"NO_CONFIGURADA", "NO_CONFIGURADO"}:
                raise ValueError(f"Configuración no soportada para {code}; requiere datos y política explícitos.")
            self.checks.append(Check(code, CheckState.UNKNOWN, False,
                                     "No configurada; fuera del alcance de la política actual."))
        proposals = []
        declarations: dict[str, Origin] = {}
        schedule_nodes = []
        for node in program.declarations:
            if isinstance(node, ScheduleDeclaration):
                schedule_nodes.append(node)
                continue
            identifier = node.identifier.value
            if identifier in declarations:
                self.fail("DECLARACION_DUPLICADA", f"La oferta {identifier!r} está declarada dos veces.",
                          self.origin(node.identifier.span), (declarations[identifier],))
                continue
            declarations[identifier] = self.origin(node.identifier.span)
            offer = self.normalize(node)
            if offer is not None:
                proposals.append(offer)
        merged = overlay_offers(self.catalog, tuple(proposals))
        offers = {o.id: o for o in merged.offers}
        views = []
        selected: set[str] = set()
        names: dict[str, Origin] = {}
        for node in schedule_nodes:
            if not node.name.value.strip():
                self.fail("NOMBRE_HORARIO_VACIO", "El horario necesita un nombre.", self.origin(node.name.span))
            if node.name.value in names:
                self.fail("HORARIO_DUPLICADO", f"El horario {node.name.value!r} está repetido.",
                          self.origin(node.name.span), (names[node.name.value],))
            names[node.name.value] = self.origin(node.name.span)
            seen: dict[str, Origin] = {}
            sessions = []
            for enrollment in node.enrollments:
                identifier = enrollment.offer_id.value
                origin = self.origin(enrollment.offer_id.span)
                if identifier in seen:
                    self.fail("INSCRIPCION_DUPLICADA", f"{identifier!r} está inscrita dos veces en el mismo horario.",
                              origin, (seen[identifier],))
                    continue
                seen[identifier] = origin
                if identifier not in offers:
                    self.fail("REFERENCIA_INEXISTENTE", f"No existe la oferta {identifier!r}.", origin)
                    continue
                self.checks.append(Check("REFERENCIA_RESUELTA", CheckState.PASSED, True,
                                         f"Oferta {identifier!r} resuelta.", (origin,)))
                selected.add(identifier)
                sessions.extend(offers[identifier].sessions)
            view = ScheduleView(node.name.value, tuple(sessions))
            views.append(view)
            clashes = [(a, b) for a, b in combinations(view.sessions, 2) if a.id != b.id and overlaps(a, b)]
            for a, b in clashes:
                self.fail("CHOQUE_PERSONAL", f"En {view.name!r} se superponen {a.offer_id} y {b.offer_id} el {a.day.value}.",
                          a.origins[0], b.origins)
            if not clashes:
                self.checks.append(Check("CRUCES_PERSONALES", CheckState.PASSED, True,
                                         f"Sin cruces personales detectados en {view.name!r}.", (self.origin(node.span),)))
        if self.scope == Scope.PERSONAL and not schedule_nodes:
            self.fail("HORARIO_REQUERIDO", "El alcance PERSONAL requiere un bloque HORARIO.", self.origin(program.span))
        if self.scope == Scope.PROPOSAL and not proposals:
            self.fail("OFERTA_REQUERIDA", "El alcance PROPUESTA requiere una OFERTA.", self.origin(program.span))
        focus = selected if self.scope == Scope.PERSONAL else {o.id for o in proposals}
        target = tuple(o for o in merged.offers if o.id in focus)
        if not schedule_nodes and self.scope == Scope.PROPOSAL:
            views.append(ScheduleView("Propuesta", tuple(s for o in target for s in o.sessions)))
        self.assess_rooms(merged, target)
        for offer in target:
            if offer.weekly_hours is not None:
                actual = sum(s.interval.end_minute - s.interval.start_minute for s in offer.sessions)
                matches = actual == offer.weekly_hours * 60
                self.checks.append(Check("CARGA_SEMANAL", CheckState.PASSED if matches else CheckState.UNKNOWN, False,
                                         f"{offer.id}: {actual} minutos observados; {offer.weekly_hours * 60} declarados.", offer.origins))
                if not matches:
                    self.diagnostics.append(Diagnostic("CARGA_SEMANAL_DISTINTA", "SEMANTICO", Severity.WARNING,
                                                       f"La carga de {offer.id} difiere del catálogo; revisión informativa.", offer.origins[0]))
        symbol_offers = tuple(o for o in merged.offers if o.id in focus or o.id in {p.id for p in proposals})
        return SemanticReport(tuple(self.diagnostics), tuple(self.checks), self.symbols(symbol_offers, views), tuple(views))

    def assess_rooms(self, catalog: Catalog, targets: tuple[Offer, ...]) -> None:
        sessions = tuple(s for offer in targets for s in offer.sessions)
        focus = {o.id for o in targets}
        known_keys = {room_identity(r.id).key for r in catalog.rooms}
        pending = []
        for session in sessions:
            if session.room.state != ValueState.KNOWN:
                pending.append(session)
                message = f"{session.offer_id}, {session.day.value}: aula pendiente de asignación o identificación."
                self.checks.append(Check("ASIGNACION_AULA", CheckState.UNKNOWN, True, message, session.origins))
                self.diagnostics.append(Diagnostic("AULA_PENDIENTE", "SEMANTICO", Severity.WARNING,
                                                   message, session.origins[0], session.origins[1:]))
            elif not self.policy.allow_new_rooms and room_identity(session.room.value).key not in known_keys:
                self.fail("AULA_NO_REGISTRADA", f"El aula {session.room.value!r} no pertenece al catálogo permitido.", session.origins[0])
            else:
                self.checks.append(Check("ASIGNACION_AULA", CheckState.PASSED, True,
                                         f"Aula indicada: {session.room.value!r}.", session.origins))
        if not self.policy.check_room_occupancy:
            self.checks.append(Check("OCUPACION_AULA", CheckState.DISABLED, False, "Comprobación desactivada por política."))
            return
        relevant = tuple(c for c in room_collisions(tuple(s for o in catalog.offers for s in o.sessions))
                         if c.first.offer_id in focus or c.second.offer_id in focus)
        for collision in relevant:
            self.diagnostics.append(collision_diagnostic(collision))
        definite = [c for c in relevant if not c.uncertain]
        uncertain = [c for c in relevant if c.uncertain]
        state = (CheckState.FAILED if definite else CheckState.UNKNOWN if pending or uncertain
                 else CheckState.PASSED if sessions else CheckState.NOT_APPLICABLE)
        self.checks.append(Check("OCUPACION_AULA", state, bool(sessions),
                                 f"{len(definite)} choques de aula; {len(uncertain)} equivalencias pendientes; "
                                 f"{len(pending)} sesiones sin aula conocida. Solo ocupaciones cargadas.",
                                 tuple(o for c in relevant for o in c.first.origins + c.second.origins)))

    def symbols(self, offers: tuple[Offer, ...], views: list[ScheduleView]) -> tuple[Symbol, ...]:
        symbols: dict[str, Symbol] = {}
        def value(raw) -> FieldValue:
            if isinstance(raw, FieldValue):
                return raw
            return FieldValue(ValueState.UNKNOWN) if raw is None else FieldValue(ValueState.KNOWN, str(raw))
        def add(identifier, kind, label, attributes, origins):
            symbols.setdefault(identifier, Symbol(identifier, kind, label,
                                                  tuple(SymbolAttribute(k, value(v)) for k, v in attributes), origins))
        for offer in offers:
            add(f"oferta:{offer.id}", "OFERTA", offer.subject,
                (("identificador", offer.id), ("grupo", offer.group), ("docente", offer.teacher),
                 ("horas_semanales_catalogo", offer.weekly_hours)), offer.origins)
            add(f"materia:{offer.subject_id or offer.subject}", "MATERIA", offer.subject,
                (("nombre", offer.subject),), offer.origins)
            if offer.group.state == ValueState.KNOWN:
                students = next((g.students for g in self.catalog.groups if g.id == offer.group.value), None)
                add(f"grupo:{offer.group.value}", "GRUPO", offer.group.value,
                    (("alumnos", students),), offer.origins)
            for session in offer.sessions:
                add(f"sesion:{session.id}", "SESION", session.id,
                    (("oferta", offer.id), ("dia", session.day.value), ("inicio_minutos", session.interval.start_minute),
                     ("fin_minutos", session.interval.end_minute), ("aula", session.room)), session.origins)
                if session.room.state == ValueState.KNOWN:
                    identity = room_identity(session.room.value)
                    room = next((r for r in self.catalog.rooms if room_identity(r.id).key == identity.key), None)
                    add(f"aula:{identity.key}", "AULA", session.room.value,
                        (("clave_comparacion", identity.key), ("capacidad", room.capacity if room else None),
                         ("tipo", room.type if room else None)), session.origins)
        for i, view in enumerate(views):
            add(f"horario:{i}", "HORARIO", view.name, (("sesiones", len(view.sessions)),), ())
        return tuple(symbols.values())
