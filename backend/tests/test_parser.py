from dataclasses import fields
from pathlib import Path
import sys

import pytest

from schedule_compiler.api.tree import ast_to_tree
from schedule_compiler.compiler.lexer import tokenize
from schedule_compiler.compiler.models import (
    EnrollmentDeclaration, IntegerLiteral, LocatedValue, OfferDeclaration,
    ParseResult, Program, ScheduleDeclaration, SessionDeclaration, TextLiteral,
)
from schedule_compiler.compiler.parser import parse
from schedule_compiler.domain.models import ValueState

ROOT = Path(__file__).resolve().parents[2]
OFFER = '''OFERTA "CLASE" {
    MATERIA "Compiladores"
    GRUPO "ISC 7B"
    DOCENTE "Docente libre"
    SESION {
        AULA "LAB-1"
        DIA MARTES
        HORA 12:00
        DURACION 2
    }
}'''


@pytest.mark.parametrize("path", sorted((ROOT / "examples").glob("*.hor")), ids=lambda p: p.name)
def test_real_examples_build_own_ast_and_reuse_exact_lexical_tokens(path):
    source = path.read_bytes().decode("utf-8")
    result = parse(source, path.name)
    assert result.success and isinstance(result.ast, Program)
    assert result.lexical == tokenize(source, path.name)
    assert result.ast.span.start.offset == 0
    assert result.ast.span.end.offset == len(source)


def test_carolina_ast_preserves_courses_tramos_and_selection():
    source = (ROOT / "examples/horario_carolina.hor").read_text()
    ast = parse(source).ast
    offers = [d for d in ast.declarations if isinstance(d, OfferDeclaration)]
    schedules = [d for d in ast.declarations if isinstance(d, ScheduleDeclaration)]
    assert len(offers) == 8 and len(schedules) == 1
    assert sum(len(o.sessions) for o in offers) == 16
    assert sum(s.duration.value for o in offers for s in o.sessions) == 29
    assert {e.offer_id.value for e in schedules[0].enrollments} == {o.identifier.value for o in offers}
    methodology = next(o for o in offers if "METODOLOGIA" in o.identifier.value)
    assert [s.hour.value for s in methodology.sessions] == ["16:00", "18:00"]
    assert [s.duration.value for s in methodology.sessions] == [2, 1]


@pytest.mark.parametrize("day", ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"])
def test_all_days_produce_located_text_literals(day):
    source = OFFER.replace("MARTES", day)
    result = parse(source)
    assert result.success
    literal = result.ast.declarations[0].sessions[0].day
    assert literal.value == day
    assert source[literal.span.start.offset:literal.span.end.offset] == day


@pytest.mark.parametrize("field,value,state", [
    ("GRUPO", '"DESCONOCIDO"', ValueState.KNOWN),
    ("GRUPO", "DESCONOCIDO", ValueState.UNKNOWN),
    ("DOCENTE", '"SIN_ASIGNAR"', ValueState.KNOWN),
    ("DOCENTE", "DESCONOCIDO", ValueState.UNKNOWN),
    ("DOCENTE", "SIN_ASIGNAR", ValueState.UNASSIGNED),
    ("AULA", '"SIN_ASIGNAR"', ValueState.KNOWN),
    ("AULA", "DESCONOCIDO", ValueState.UNKNOWN),
    ("AULA", "SIN_ASIGNAR", ValueState.UNASSIGNED),
])
def test_markers_and_quoted_text_are_preserved_in_the_ast(field, value, state):
    original = {"GRUPO": '"ISC 7B"', "DOCENTE": '"Docente libre"', "AULA": '"LAB-1"'}
    source = OFFER.replace(f"{field} {original[field]}", f"{field} {value}")
    result = parse(source)
    assert result.success
    offer = result.ast.declarations[0]
    node = {"GRUPO": offer.group, "DOCENTE": offer.teacher, "AULA": offer.sessions[0].room}[field]
    assert node.value.state == state
    assert node.value.value == (value[1:-1] if state == ValueState.KNOWN else None)


def test_string_decoding_is_single_pass_and_preserves_unicode_and_tabs():
    raw = r'"López 😀 # \\n \"A\""'
    source = OFFER.replace('"Docente libre"', raw).replace('"Compiladores"', '"Compiladores\tWeb"')
    result = parse(source)
    assert result.success
    offer = result.ast.declarations[0]
    assert offer.teacher.value.value == 'López 😀 # \\n "A"'
    assert offer.subject.value == "Compiladores\tWeb"
    assert source[offer.teacher.span.start.offset:offer.teacher.span.end.offset] == raw


def test_durations_and_hours_keep_invalid_semantic_values():
    source = OFFER.replace("12:00", "25:99").replace("DURACION 2", "DURACION 0")
    result = parse(source)
    assert result.success
    session = result.ast.declarations[0].sessions[0]
    assert session.hour.value == "25:99" and session.duration.value == 0


def test_forward_unknown_references_and_duplicate_ids_are_not_syntax_errors():
    source = 'HORARIO "Uno" { INSCRIBIR "No existe" INSCRIBIR "No existe" }\n' + OFFER + OFFER
    result = parse(source)
    assert result.success and len(result.ast.declarations) == 3


@pytest.mark.parametrize("source,expected", [
    (OFFER.replace('DURACION 2', 'DURACION "dos"'), "un entero"),
    (OFFER.replace('HORA 12:00', 'HORA 12'), "una hora HH:MM"),
    (OFFER.replace('    DOCENTE "Docente libre"\n', ''), "DOCENTE"),
    (OFFER.replace('    GRUPO "ISC 7B"\n', ''), "GRUPO"),
    (OFFER.replace('        AULA "LAB-1"\n', ''), "AULA"),
    (OFFER.replace('GRUPO "ISC 7B"', 'GRUPO SIN_ASIGNAR'), "DESCONOCIDO"),
    ('OFERTA "X" { MATERIA "X" GRUPO DESCONOCIDO DOCENTE DESCONOCIDO }', "SESION"),
    ('HORARIO "X" { }', "INSCRIBIR"),
    ('HORARIO "X" INSCRIBIR "Y" }', "'{'"),
    ('HORARIO "X" { INSCRIBIR 12 }', "una cadena entre comillas"),
    ('HORARIO "X" { INSCRIBIR "Y" } }', "el fin del archivo"),
    (OFFER.replace('MATERIA "Compiladores"', 'MATERIA "X" MATERIA "Y"'), "GRUPO"),
])
def test_structure_errors_return_expected_tokens_without_ast(source, expected):
    result = parse(source, "prueba.hor")
    assert result.lexical.success and result.executed and not result.success
    assert result.ast is None and len(result.diagnostics) == 1
    error = result.diagnostics[0]
    assert error.stage == "SINTACTICO" and error.code == "TOKEN_INESPERADO"
    assert expected in error.message and error.origin.source_id == "prueba.hor"


@pytest.mark.parametrize("source", ["", " \t\r\n", '# comentario sin declaraciones\r\n'])
def test_empty_programs_are_syntax_errors_with_eof_position(source):
    result = parse(source)
    assert result.lexical.success and result.ast is None
    error = result.diagnostics[0]
    assert error.code == "PROGRAMA_VACIO"
    assert error.origin.span.start.offset == error.origin.span.end.offset == len(source)


def test_missing_final_brace_points_to_actual_eof_after_comments():
    source = 'HORARIO "X" {\r\n\tINSCRIBIR "Y"\r\n# falta llave\r\n'
    result = parse(source)
    error = result.diagnostics[0]
    assert error.code == "FIN_INESPERADO" and "'}'" in error.message
    assert error.origin.span.start.offset == len(source)
    assert (error.origin.span.start.line, error.origin.span.start.column) == (4, 1)


def test_syntax_error_preserves_the_unexpected_token_location():
    source = OFFER.replace("DURACION 2", 'DURACION "dos"')
    result = parse(source)
    span = result.diagnostics[0].origin.span
    assert source[span.start.offset:span.end.offset] == '"dos"'
    assert (span.start.line, span.start.column) == (9, 18)


@pytest.mark.parametrize("source", ['} @', 'HORARIO "X" { INSCRIBIR "Y"; }', 'HORARIO "X'])
def test_lexical_errors_block_all_syntax_work(source):
    result = parse(source)
    assert not result.executed and not result.success
    assert result.ast is None and result.diagnostics == ()
    assert result.lexical.diagnostics[0].stage == "LEXICO"


def test_node_spans_include_structure_and_contain_children():
    source = '# inicio\r\n' + OFFER.replace("\n", "\r\n") + '\r\n# fin\r\n'
    result = parse(source)
    assert result.success
    def nodes(value):
        if isinstance(value, tuple):
            for item in value:
                yield from nodes(item)
        elif isinstance(value, (Program, OfferDeclaration, SessionDeclaration, ScheduleDeclaration,
                                EnrollmentDeclaration, TextLiteral, IntegerLiteral, LocatedValue)):
            yield value
            for field in fields(value):
                child = getattr(value, field.name)
                for descendant in nodes(child):
                    assert value.span.start.offset <= descendant.span.start.offset
                    assert descendant.span.end.offset <= value.span.end.offset
                    yield descendant
    all_nodes = list(nodes(result.ast))
    assert len(all_nodes) > 10
    offer = result.ast.declarations[0]
    assert source[offer.span.start.offset:offer.span.end.offset] == OFFER.replace("\n", "\r\n")
    assert (offer.span.start.line, offer.span.start.column) == (2, 1)
    assert source[offer.subject.span.start.offset:offer.subject.span.end.offset] == '"Compiladores"'


def test_tree_adapter_accepts_real_ast_with_unique_source_linked_nodes():
    source = OFFER.replace('"Docente libre"', '"López 😀"')
    result = parse(source)
    tree = ast_to_tree(result.ast)
    def flatten(node):
        return [node, *(n for child in node.children for n in flatten(child))]
    nodes = flatten(tree)
    assert len({n.id for n in nodes}) == len(nodes)
    teacher = next(n for n in nodes if n.label == "Docente")
    assert teacher.value == "López 😀"
    assert source[teacher.span.start.offset:teacher.span.end.offset] == '"López 😀"'


def test_large_integer_conversion_errors_are_reported_without_crashing():
    limit = sys.get_int_max_str_digits()
    if not limit:
        pytest.skip("El intérprete no tiene límite de conversión de enteros.")
    source = OFFER.replace("DURACION 2", "DURACION " + "9" * (limit + 1))
    result = parse(source)
    assert result.executed and result.ast is None
    assert result.diagnostics[0].code == "ENTERO_NO_REPRESENTABLE"


def test_parser_reuse_does_not_leak_a_previous_failure():
    assert not parse('HORARIO "X" { }').success
    result = parse(OFFER)
    assert result.success and result.ast.declarations[0].identifier.value == "CLASE"


def test_result_cannot_invent_an_ast_after_a_lexical_failure():
    bad = tokenize("@")
    with pytest.raises(ValueError):
        ParseResult(bad, ast=parse(OFFER).ast)
    with pytest.raises(ValueError):
        ParseResult(tokenize(""))
