from dataclasses import replace
from pathlib import Path

import pytest

from schedule_compiler.api.schemas.analysis import to_response
from schedule_compiler.application.analyze import analyze
from schedule_compiler.application.audit import audit_catalog
from schedule_compiler.application.contracts import AnalysisStatus, CheckState, Scope
from schedule_compiler.domain.models import FieldValue, Interval, ValueState, Weekday
from schedule_compiler.domain.validation import overlaps

ROOT = Path(__file__).resolve().parents[2]


def offer(identifier="NUEVA", room='"Aula nueva"', day="MARTES", hour="10:00", duration=2, teacher='"Profe cualquiera"'):
    return f'''OFERTA "{identifier}" {{ MATERIA "Demo" GRUPO DESCONOCIDO DOCENTE {teacher}
        SESION {{ AULA {room} DIA {day} HORA {hour} DURACION {duration} }} }}'''


def schedule(*ids, name="Mi horario"):
    return f'HORARIO "{name}" {{ ' + " ".join(f'INSCRIBIR "{i}"' for i in ids) + " }"


@pytest.fixture
def run(repository, working):
    def execute(source, scope=Scope.PERSONAL, catalog=None, policy=None):
        return analyze(source, catalog or working, policy or repository.load_policy(), "editor", scope)
    return execute


@pytest.mark.parametrize("name,scope", [
    ("horario_carolina.hor", Scope.PERSONAL), ("horario_carolina_seleccion.hor", Scope.PERSONAL),
    ("horario_personal.hor", Scope.PERSONAL), ("oferta_compiladores.hor", Scope.PROPOSAL),
])
def test_real_examples_complete_all_phases(run, name, scope):
    result = run((ROOT / "examples" / name).read_text(), scope)
    assert result.status == AnalysisStatus.VALID
    assert all(p.state.value == "COMPLETADA" for p in result.phases)
    assert result.ast is not None and result.symbols and result.schedules
    assert not any(d.severity.value == "ERROR" for d in result.diagnostics)
    to_response(result)


def test_carolina_preserves_29_hours_without_false_duplicates(run):
    result = run((ROOT / "examples/horario_carolina.hor").read_text())
    sessions = result.schedules[0].sessions
    assert len(sessions) == 16 and len({s.id for s in sessions}) == 16
    assert sum(s.interval.end_minute - s.interval.start_minute for s in sessions) == 29 * 60
    assert not any(d.code in {"CHOQUE_AULA", "CHOQUE_PERSONAL"} for d in result.diagnostics)
    assert len({s.id for s in result.symbols}) == len(result.symbols)


@pytest.mark.parametrize("scope", [Scope.PERSONAL, Scope.PROPOSAL])
def test_two_friends_sharing_a_class_do_not_create_room_collisions(run, scope):
    source = offer() + schedule("NUEVA", name="Persona A") + schedule("NUEVA", name="Persona B")
    result = run(source, scope)
    assert result.status == AnalysisStatus.VALID and len(result.schedules) == 2
    assert result.schedules[0].sessions[0].id == result.schedules[1].sessions[0].id


@pytest.mark.parametrize("start,end,expected", [(600, 720, True), (660, 780, True), (720, 840, False), (480, 600, False)])
def test_intervals_use_exclusive_ends(working, start, end, expected):
    template = working.offers[0].sessions[0]
    a = replace(template, interval=Interval(600, 720))
    b = replace(template, id="other", interval=Interval(start, end))
    assert overlaps(a, b) is expected
    assert not overlaps(a, replace(b, day=Weekday.SUNDAY))


def test_personal_conflict_in_different_rooms_is_an_error(run):
    source = offer("A", '"Aula A"') + offer("B", '"Aula B"', hour="11:00") + schedule("A", "B")
    result = run(source)
    assert result.status == AnalysisStatus.INVALID
    assert any(d.code == "CHOQUE_PERSONAL" for d in result.diagnostics)
    assert not any(d.code == "CHOQUE_AULA" for d in result.diagnostics)


def test_adjacent_personal_classes_and_same_room_are_valid(run):
    result = run(offer("A") + offer("B", hour="12:00") + schedule("A", "B"))
    assert result.status == AnalysisStatus.VALID


def test_new_room_names_and_arbitrary_professors_are_accepted(run):
    source = offer("A", teacher='"Nombre no registrado"') + offer("B", room='"Otra aula"', teacher='"Nombre no registrado"')
    result = run(source, Scope.PROPOSAL)
    assert result.status == AnalysisStatus.VALID
    teachers = [s for s in result.symbols if s.kind == "DOCENTE"]
    assert not teachers
    assert next(c for c in result.checks if c.code == "REGLAS_DOCENTES").state == CheckState.DISABLED


@pytest.mark.parametrize("teacher", ['""', '"DESCONOCIDO"', "DESCONOCIDO", "SIN_ASIGNAR"])
def test_no_assignment_or_name_rule_is_applied_to_teachers(run, teacher):
    assert run(offer(teacher=teacher), Scope.PROPOSAL).status == AnalysisStatus.VALID


@pytest.mark.parametrize("room", ["SIN_ASIGNAR", "DESCONOCIDO"])
def test_missing_room_is_incomplete_not_invalid_or_automatically_assigned(run, room):
    result = run(offer(room=room), Scope.PROPOSAL)
    assert result.status == AnalysisStatus.INCOMPLETE
    assert result.schedules[0].sessions[0].room.value is None
    assert any(c.required and c.state == CheckState.UNKNOWN for c in result.checks)


def test_occupied_room_normalizes_codes_and_reports_source_and_excel_origins(run):
    result = run(offer(room='"FIE2AUL032"', hour="12:00"), Scope.PROPOSAL)
    assert result.status == AnalysisStatus.INVALID
    diagnostic = next(d for d in result.diagnostics if d.code == "CHOQUE_AULA")
    assert any(o.kind == "EXCEL" for o in (diagnostic.origin,) + diagnostic.related)
    assert any(o.kind == "TEXTO" for o in (diagnostic.origin,) + diagnostic.related)


def test_same_offer_replaces_catalog_without_self_collision(run):
    result = run((ROOT / "examples/oferta_compiladores.hor").read_text(), Scope.PROPOSAL)
    assert result.status == AnalysisStatus.VALID and len(result.schedules[0].sessions) == 2
    assert not any(d.code == "CHOQUE_AULA" for d in result.diagnostics)


def test_pending_room_identity_is_not_guessed(run, working):
    template = working.offers[0]
    session = replace(template.sessions[0], id="CENTRO", offer_id="CENTRO", day=Weekday.TUESDAY,
                      interval=Interval(600, 720), room=FieldValue(ValueState.KNOWN, "CENTRO DE CÓMPUTO"))
    base = replace(working, offers=(replace(template, id="CENTRO", sessions=(session,)),))
    result = run(offer(room='"FIE1AC0001"'), Scope.PROPOSAL, catalog=base)
    assert result.status == AnalysisStatus.INCOMPLETE
    assert any(d.code == "IDENTIDAD_AULA_PENDIENTE" for d in result.diagnostics)
    assert not any(d.code == "CHOQUE_AULA" for d in result.diagnostics)
    # Una posible equivalencia no importa si los intervalos no se cruzan.
    assert run(offer(room='"FIE1AC0001"', hour="12:00"), Scope.PROPOSAL, catalog=base).status == AnalysisStatus.VALID


@pytest.mark.parametrize("source,scope,code", [
    (schedule("NO_EXISTE"), Scope.PERSONAL, "REFERENCIA_INEXISTENTE"),
    (offer() + offer(), Scope.PROPOSAL, "DECLARACION_DUPLICADA"),
    (offer() + schedule("NUEVA", "NUEVA"), Scope.PERSONAL, "INSCRIPCION_DUPLICADA"),
    (offer() + schedule("NUEVA") + schedule("NUEVA"), Scope.PERSONAL, "HORARIO_DUPLICADO"),
    (offer(hour="25:00"), Scope.PROPOSAL, "HORA_INVALIDA"),
    (offer(hour="10:99"), Scope.PROPOSAL, "HORA_INVALIDA"),
    (offer(duration=0), Scope.PROPOSAL, "DURACION_INVALIDA"),
    (offer(hour="23:00", duration=2), Scope.PROPOSAL, "DURACION_INVALIDA"),
    (offer(room='" "'), Scope.PROPOSAL, "AULA_VACIA"),
    (offer(identifier=""), Scope.PROPOSAL, "IDENTIFICADOR_VACIO"),
    (offer().replace('MATERIA "Demo"', 'MATERIA ""'), Scope.PROPOSAL, "MATERIA_VACIA"),
    (offer(), Scope.PERSONAL, "HORARIO_REQUERIDO"),
    (schedule("ISC_7B_COMPILADORES"), Scope.PROPOSAL, "OFERTA_REQUERIDA"),
    (schedule("ISC_7B_COMPILADORES", name=""), Scope.PERSONAL, "NOMBRE_HORARIO_VACIO"),
])
def test_semantic_failures_preserve_ast_and_produce_diagnostics(run, source, scope, code):
    result = run(source, scope)
    assert result.status == AnalysisStatus.INVALID and result.ast is not None
    assert result.phases[-1].state.value == "CON_ERRORES"
    diagnostic = next(d for d in result.diagnostics if d.code == code)
    assert diagnostic.origin.kind == "TEXTO" and diagnostic.origin.span is not None
    to_response(result)


def test_midnight_end_is_valid_but_not_a_start(run):
    result = run(offer(hour="23:00", duration=1), Scope.PROPOSAL)
    assert result.status == AnalysisStatus.VALID
    assert result.schedules[0].sessions[0].interval.end_minute == 1440


def test_unconfigured_checks_are_explicit_and_not_required(run):
    result = run(offer(), Scope.PROPOSAL)
    for code in ("CAPACIDAD", "LABORATORIO", "HORARIO_PERMITIDO"):
        check = next(c for c in result.checks if c.code == code)
        assert check.state == CheckState.UNKNOWN and not check.required
    assert result.status == AnalysisStatus.VALID


def test_unknown_room_name_can_be_rejected_only_by_an_explicit_policy(run, repository):
    policy = replace(repository.load_policy(), allow_new_rooms=False)
    assert run(offer(), Scope.PROPOSAL, policy=policy).status == AnalysisStatus.INVALID


def test_original_and_working_audits_are_calculated_separately(repository, working, run):
    original = repository.load_catalog("isc-26-1-original")
    assert len([d for d in audit_catalog(original) if d.code == "CHOQUE_AULA"]) == 1
    assert not any(d.code == "CHOQUE_AULA" for d in audit_catalog(working))
    assert len([d for d in audit_catalog(working) if d.code == "AULA_PENDIENTE"]) == 2
    assert len([d for d in audit_catalog(working) if d.code == "AJUSTE_CATALOGO"]) == 2
    result = run(schedule("ISC_7B_COMPILADORES"), catalog=original)
    assert result.status == AnalysisStatus.VALID
    assert any(d.code == "CHOQUE_AULA" for d in result.catalog_diagnostics)


def test_working_pending_offer_is_incomplete_when_it_is_selected(run):
    result = run(schedule("ISC_1RA_ALGEBRA_SUPERIOR"))
    assert result.status == AnalysisStatus.INCOMPLETE


@pytest.mark.parametrize("source,last_completed", [('HORARIO "abierta', -1), ('HORARIO "X" {}', 0)])
def test_previous_phase_failures_block_semantics(run, source, last_completed):
    result = run(source)
    assert result.status == AnalysisStatus.INVALID and result.ast is None
    assert result.phases[-1].state.value == "NO_EJECUTADA"
    assert not result.checks and not result.symbols and not result.schedules


def test_analysis_does_not_mutate_catalog_or_keep_previous_proposals(run, working):
    before = working.offers
    assert run(offer(room='"FIE2-AUL32"', hour="12:00"), Scope.PROPOSAL).status == AnalysisStatus.INVALID
    assert working.offers is before
    assert run(schedule("ISC_7B_COMPILADORES")).status == AnalysisStatus.VALID
