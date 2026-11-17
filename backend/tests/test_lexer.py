from pathlib import Path
import re

import pytest

from schedule_compiler.compiler.lexer import lexical_patterns, tokenize

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("path", sorted((ROOT / "examples").glob("*.hor")), ids=lambda p: p.name)
def test_real_examples_are_tokenized_with_traceable_lexemes(path):
    source = path.read_bytes().decode("utf-8")
    result = tokenize(source, path.name)
    assert result.success, result.diagnostics
    assert result.tokens
    patterns = {p.id: p.expression for p in result.patterns}
    for token in result.tokens:
        assert source[token.span.start.offset:token.span.end.offset] == token.lexeme
        assert re.fullmatch(patterns[token.pattern_id], token.lexeme)
    assert all(a.span.end.offset <= b.span.start.offset for a, b in zip(result.tokens, result.tokens[1:]))


def test_keyword_tokens_and_marker_strings_are_distinct():
    result = tokenize('OFERTA MATERIA GRUPO DOCENTE SESION AULA DIA HORA DURACION HORARIO INSCRIBIR '
                      'DESCONOCIDO SIN_ASIGNAR "DESCONOCIDO" "SIN_ASIGNAR"')
    assert result.success
    assert [t.kind for t in result.tokens[:13]] == [f"KW_{t.lexeme}" for t in result.tokens[:13]]
    assert [t.kind for t in result.tokens[-2:]] == ["CADENA", "CADENA"]


@pytest.mark.parametrize("day", ["LUNES", "MARTES", "MIERCOLES", "JUEVES", "VIERNES", "SABADO", "DOMINGO"])
def test_weekdays_are_reserved_words(day):
    result = tokenize(f"DIA {day}")
    assert result.success and result.tokens[1].kind == f"KW_{day}"


@pytest.mark.parametrize("word", ["MATERIAX", "HORA1", "HORARIO_EXTRA", "horario", "MIÉRCOLES", "HORAé"])
def test_words_are_not_split_into_keyword_prefixes(word):
    result = tokenize(word)
    assert not result.success and not result.tokens
    diagnostic = result.diagnostics[0]
    assert diagnostic.code == "LEXEMA_NO_RECONOCIDO"
    assert diagnostic.origin.span.end.offset == len(word)


def test_hours_are_single_tokens_even_when_out_of_semantic_range():
    result = tokenize("HORA 10:00 HORA 25:99 DURACION 0")
    assert result.success
    assert [(t.kind, t.lexeme) for t in result.tokens] == [
        ("KW_HORA", "HORA"), ("HORA_LITERAL", "10:00"),
        ("KW_HORA", "HORA"), ("HORA_LITERAL", "25:99"),
        ("KW_DURACION", "DURACION"), ("ENTERO", "0"),
    ]


@pytest.mark.parametrize("time", ["8:00", "100:00", "10:000", "10:00:00", "12:0", "10:00x"])
def test_malformed_hours_do_not_become_a_sequence_of_valid_number_tokens(time):
    result = tokenize(f"HORA {time}")
    assert not result.success
    assert [t.kind for t in result.tokens] == ["KW_HORA"]
    assert result.diagnostics[0].code == "FORMATO_HORA_INVALIDO"


def test_strings_preserve_accents_emoji_hash_and_allowed_escapes():
    source = r'DOCENTE "Dra. López 😀 # grupo \"A\" \\ oficina"'
    result = tokenize(source)
    assert result.success
    assert result.tokens[1].lexeme == source[8:]
    assert result.tokens[1].kind == "CADENA"


def test_comments_do_not_consume_strings_and_are_not_tokens():
    result = tokenize('# " @ ;\nMATERIA "Web # 1" # comentario sin cierre "\n{}')
    assert result.success
    assert [t.lexeme for t in result.tokens] == ["MATERIA", '"Web # 1"', "{", "}"]


@pytest.mark.parametrize("source", ["", " \t\r\n", '# solo comentario " @'])
def test_empty_or_ignored_input_is_lexically_valid_not_a_valid_program(source):
    result = tokenize(source)
    assert result.success and result.tokens == ()


@pytest.mark.parametrize("source,code,start,end", [
    ('DOCENTE "Sin cierre', "CADENA_SIN_CIERRE", 8, 19),
    ('DOCENTE "Sin cierre\\', "CADENA_SIN_CIERRE", 8, 20),
    ('DOCENTE "Línea\nnueva"', "SALTO_LINEA_EN_CADENA", 8, 14),
    ('DOCENTE "Línea\r\nnueva"', "SALTO_LINEA_EN_CADENA", 8, 14),
    ('DOCENTE "a\\\nb"', "SALTO_LINEA_EN_CADENA", 8, 11),
    (r'DOCENTE "a\nb"', "ESCAPE_INVALIDO", 10, 12),
    (r'DOCENTE "a\qb"', "ESCAPE_INVALIDO", 10, 12),
])
def test_string_errors_have_precise_spans_and_preserve_prior_tokens(source, code, start, end):
    result = tokenize(source, "prueba.hor")
    assert not result.success
    assert [t.lexeme for t in result.tokens] == ["DOCENTE"]
    error = result.diagnostics[0]
    assert error.code == code and error.origin.source_id == "prueba.hor"
    assert error.origin.span.start.offset == start
    assert error.origin.span.end.offset == end


@pytest.mark.parametrize("char", ["@", ";", "-", ".", "\ufeff"])
def test_undefined_characters_are_located_and_stop_the_scan(char):
    result = tokenize(f"DURACION 2 {char} AULA", "editor")
    assert not result.success and len(result.diagnostics) == 1
    assert [t.lexeme for t in result.tokens] == ["DURACION", "2"]
    error = result.diagnostics[0]
    assert error.code == "CARACTER_NO_PERMITIDO"
    assert error.origin.span.start.column == 12


def test_positions_preserve_crlf_tabs_and_unicode_codepoints():
    source = '# nota\r\n\tMATERIA "Árbol 😀"\r\nHORA 10:00'
    result = tokenize(source)
    assert result.success
    assert (result.tokens[0].span.start.offset, result.tokens[0].span.start.line,
            result.tokens[0].span.start.column) == (9, 2, 2)
    assert (result.tokens[2].span.start.line, result.tokens[2].span.start.column) == (3, 1)
    result = tokenize('MATERIA "😀" HORA 10:00')
    assert result.tokens[2].span.start.offset == 12
    assert result.tokens[2].span.start.column == 13


def test_error_line_and_column_after_comment_and_crlf():
    result = tokenize('# nota\r\n\tAULA "A"\r\n    @')
    position = result.diagnostics[0].origin.span.start
    assert (position.line, position.column) == (3, 5)


def test_lexer_does_not_parse_or_repair_structure():
    result = tokenize('} DURACION "dos" {')
    assert result.success
    assert [t.lexeme for t in result.tokens] == ["}", "DURACION", '"dos"', "{"]


def test_cached_engine_does_not_retain_state_from_an_invalid_input():
    assert not tokenize('"abierta').success
    result = tokenize("HORA 10:00", "nuevo.hor")
    assert result.success and result.tokens[0].span.start.offset == 0
    assert result.source_name == "nuevo.hor"


def test_pattern_catalog_comes_from_recognition_rules():
    patterns = lexical_patterns()
    assert len({p.id for p in patterns}) == len(patterns)
    assert all(p.id not in {"espacio", "comentario"} for p in patterns)
    result = tokenize('HORARIO "A" { INSCRIBIR "B" }')
    by_id = {p.id: p for p in patterns}
    assert all(re.fullmatch(by_id[t.pattern_id].expression, t.lexeme) for t in result.tokens)
