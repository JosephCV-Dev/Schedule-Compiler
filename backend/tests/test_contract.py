import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from schedule_compiler.api.schemas.analysis import AnalysisRequest, AnalysisResponse, to_response
from schedule_compiler.api.tree import ast_to_tree
from schedule_compiler.compiler.models import (
    IntegerLiteral, LocatedValue, OfferDeclaration, Program, SessionDeclaration, TextLiteral,
)
from schedule_compiler.domain.models import FieldValue, Position, Span, ValueState

ROOT = Path(__file__).resolve().parents[2]


def test_editor_and_file_share_plain_text_contract():
    text = AnalysisRequest(source="")
    upload = AnalysisRequest(source="", source_name="amigo.hor")
    assert text.source == upload.source
    with pytest.raises(ValidationError):
        AnalysisRequest(source="texto", file_path="/tmp/amigo.hor")
    with pytest.raises(ValidationError):
        AnalysisRequest(source="texto", language_version="0.1")


@pytest.mark.parametrize("name", ["valido", "invalido", "incompleto"])
def test_exported_examples_match_typed_results(contract_examples, name):
    request, internal = contract_examples[name]
    fixture = json.loads((ROOT / "contracts/examples" / f"{name}.json").read_text())
    assert request.model_dump(mode="json") == fixture["request"]
    assert to_response(internal).model_dump(mode="json") == fixture["response"]
    assert AnalysisResponse.model_validate(fixture["response"]).model_dump(mode="json") == fixture["response"]


def test_tree_has_unique_stable_nodes_children_and_source_ranges():
    span = Span(Position(0, 1, 1), Position(5, 1, 6))
    text = TextLiteral("Ejemplo", span)
    marker = LocatedValue(FieldValue(ValueState.UNASSIGNED), span)
    known = LocatedValue(FieldValue(ValueState.KNOWN, "Docente libre"), span)
    session = SessionDeclaration(marker, text, TextLiteral("25:00", span), IntegerLiteral(0, span), span)
    program = Program((OfferDeclaration(text, text, known, known, (session,), span),), span)
    tree = ast_to_tree(program)
    def flatten(node):
        return [node, *(child for nested in node.children for child in flatten(nested))]
    nodes = flatten(tree)
    assert len({n.id for n in nodes}) == len(nodes)
    assert tree.model_dump() == ast_to_tree(program).model_dump()
    room = next(n for n in nodes if n.label == "Aula")
    assert room.value is None and room.value_state == ValueState.UNASSIGNED
    assert all(n.span.start.line == 1 for n in nodes)
    assert next(n for n in nodes if n.label == "Hora").value == "25:00"
    assert next(n for n in nodes if n.label == "Duración (horas)").value == 0
