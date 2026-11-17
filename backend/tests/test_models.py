from dataclasses import replace
import subprocess
import sys

import pytest

from schedule_compiler.application.contracts import (
    AnalysisStatus, Check, CheckState, Diagnostic, PhaseReport, PhaseState, Severity, Stage,
)
from schedule_compiler.compiler.models import IntegerLiteral, TextLiteral
from schedule_compiler.domain.models import FieldValue, Interval, Position, Span, ValueState


@pytest.mark.parametrize("args", [(-1, 1, 1), (0, 0, 1), (0, 1, 0)])
def test_positions_are_zero_based_offsets_and_one_based_coordinates(args):
    with pytest.raises(ValueError):
        Position(*args)


def test_spans_reject_reverse_offsets():
    with pytest.raises(ValueError):
        Span(Position(4, 1, 5), Position(2, 1, 3))


@pytest.mark.parametrize("start,end", [(0, 0), (12, 10), (-1, 20), (0, 1441)])
def test_only_normalized_intervals_enforce_time_validity(start, end):
    with pytest.raises(ValueError):
        Interval(start, end)


def test_ast_preserves_values_for_semantic_errors():
    span = Span(Position(0, 1, 1), Position(5, 1, 6))
    assert TextLiteral("25:00", span).value == "25:00"
    assert IntegerLiteral(0, span).value == 0
    assert Interval(1380, 1440).end_minute == 1440


def test_markers_and_literal_marker_text_are_different():
    literal = FieldValue(ValueState.KNOWN, "DESCONOCIDO")
    marker = FieldValue(ValueState.UNKNOWN)
    assert literal != marker and marker.value is None
    with pytest.raises(ValueError):
        FieldValue(ValueState.UNASSIGNED, "AULA-1")
    with pytest.raises(ValueError):
        FieldValue(ValueState.KNOWN)


def test_success_cannot_hide_required_pending_checks(contract_examples):
    _, incomplete = contract_examples["incompleto"]
    with pytest.raises(ValueError):
        replace(incomplete, status=AnalysisStatus.VALID)


def test_phase_dependencies_prevent_fake_success(contract_examples):
    _, invalid = contract_examples["invalido"]
    with pytest.raises(ValueError):
        replace(invalid, phases=(invalid.phases[0],
                                PhaseReport(Stage.SYNTACTIC, PhaseState.COMPLETED),
                                invalid.phases[2]))


def test_catalog_audit_errors_do_not_invalidate_a_personal_result(contract_examples):
    _, valid = contract_examples["valido"]
    audit = Diagnostic("CHOQUE_HISTORICO", "CATALOGO", Severity.ERROR, "Otro grupo.")
    assert replace(valid, catalog_diagnostics=(audit,)).status == AnalysisStatus.VALID


def test_disabled_teacher_checks_are_visible_but_not_required(contract_examples):
    _, valid = contract_examples["valido"]
    teacher = next(c for c in valid.checks if c.code == "REGLAS_DOCENTES")
    assert teacher.state == CheckState.DISABLED and not teacher.required
    with pytest.raises(ValueError):
        replace(valid, checks=(Check("DOCENTE", CheckState.DISABLED, True, "Incorrecto"),))


def test_core_imports_without_web_or_parser_frameworks():
    code = """
import sys
import schedule_compiler.domain.models
import schedule_compiler.compiler.models
import schedule_compiler.application.contracts
assert not any(name in sys.modules for name in ('fastapi', 'pydantic', 'lark'))
"""
    subprocess.run([sys.executable, "-c", code], check=True, capture_output=True, text=True)
