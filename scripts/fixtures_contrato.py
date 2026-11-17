"""Ejemplos construidos a mano del contrato, NO resultados de un analizador.

Se usan para revisar el JSON antes de implementar las etapas 3, 4 y 5.
"""

from pathlib import Path

from schedule_compiler.api.schemas.analysis import AnalysisRequest, to_response
from schedule_compiler.application.contracts import (
    AnalysisMetadata, AnalysisResult, AnalysisStatus, Check, CheckState, Diagnostic,
    PhaseReport, PhaseState, ScheduleView, Scope, Severity, Stage, Symbol,
)
from schedule_compiler.compiler.models import (
    EnrollmentDeclaration, Pattern, Program, ScheduleDeclaration, TextLiteral, Token,
)
from schedule_compiler.domain.models import Origin, Position, Span
from schedule_compiler.infrastructure.catalogs import DataRepository


def span_at(source: str, start: int, end: int) -> Span:
    def position(offset: int) -> Position:
        before = source[:offset]
        return Position(offset, before.count("\n") + 1, len(before.rsplit("\n", 1)[-1]) + 1)
    return Span(position(start), position(end))


def examples(data_dir: Path) -> dict:
    catalog = DataRepository(data_dir).load_catalog()
    result = {}
    for name, offer_id in (
        ("valido", "ISC_7B_COMPILADORES"),
        ("incompleto", "ISC_1RA_ALGEBRA_SUPERIOR"),
    ):
        source = f'HORARIO "Ejemplo" {{\n    INSCRIBIR "{offer_id}"\n}}\n'
        request = AnalysisRequest(source=source, source_name=f"{name}.hor")
        patterns = (
            Pattern("kw_horario", "Palabra HORARIO", "HORARIO"),
            Pattern("kw_inscribir", "Palabra INSCRIBIR", "INSCRIBIR"),
            Pattern("cadena", "Texto entre comillas", r'"(?:[^"\\\r\n]|\\["\\])*"'),
            Pattern("abrir", "Llave de apertura", r"\{"),
            Pattern("cerrar", "Llave de cierre", r"\}"),
        )
        tokens = []
        cursor = 0
        # Lexemas de este ejemplo conocido; no hay reconocimiento de texto general.
        for kind, lexeme, pattern in (
            ("KW_HORARIO", "HORARIO", "kw_horario"),
            ("CADENA", '"Ejemplo"', "cadena"),
            ("LLAVE_APERTURA", "{", "abrir"),
            ("KW_INSCRIBIR", "INSCRIBIR", "kw_inscribir"),
            ("CADENA", f'"{offer_id}"', "cadena"),
            ("LLAVE_CIERRE", "}", "cerrar"),
        ):
            start = source.index(lexeme, cursor)
            cursor = start + len(lexeme)
            tokens.append(Token(kind, lexeme, pattern, span_at(source, start, cursor)))
        ast = Program((ScheduleDeclaration(
            TextLiteral("Ejemplo", tokens[1].span),
            (EnrollmentDeclaration(TextLiteral(offer_id, tokens[4].span),
                                   Span(tokens[3].span.start, tokens[4].span.end)),),
            Span(tokens[0].span.start, tokens[-1].span.end),
        ),), span_at(source, 0, len(source)))
        offer = next(o for o in catalog.offers if o.id == offer_id)
        pending = name == "incompleto"
        checks = (
            Check("OCUPACION_AULA", CheckState.UNKNOWN if pending else CheckState.PASSED,
                  True, "Aula pendiente de asignar." if pending else "Ejemplo de comprobación cumplida."),
            Check("REGLAS_DOCENTES", CheckState.DISABLED, False, "Profesor como texto libre."),
        )
        internal = AnalysisResult(
            metadata=AnalysisMetadata("0.2", catalog.id, catalog.snapshot_sha256,
                                      "proyecto-v0.2", "0.2", Scope.PERSONAL, request.source_name),
            status=AnalysisStatus.INCOMPLETE if pending else AnalysisStatus.VALID,
            phases=tuple(PhaseReport(s, PhaseState.COMPLETED) for s in Stage),
            patterns=patterns, tokens=tuple(tokens), ast=ast, checks=checks,
            symbols=(Symbol(offer.id, "OFERTA", offer.subject, (), offer.origins),),
            schedules=(ScheduleView("Ejemplo", offer.sessions),),
        )
        result[name] = (request, internal)
    source = 'HORARIO "Sin cierre'
    request = AnalysisRequest(source=source, source_name="invalido.hor")
    lexical_error = Diagnostic(
        "CADENA_SIN_CIERRE", "LEXICO", Severity.ERROR, "La cadena no tiene comillas de cierre.",
        Origin("TEXTO", request.source_name, span=span_at(source, 8, len(source))),
    )
    invalid = AnalysisResult(
        metadata=AnalysisMetadata("0.2", catalog.id, catalog.snapshot_sha256,
                                  "proyecto-v0.2", "0.2", Scope.PERSONAL, request.source_name),
        status=AnalysisStatus.INVALID,
        phases=(PhaseReport(Stage.LEXICAL, PhaseState.FAILED),
                PhaseReport(Stage.SYNTACTIC, PhaseState.NOT_RUN),
                PhaseReport(Stage.SEMANTIC, PhaseState.NOT_RUN)),
        diagnostics=(lexical_error,),
    )
    result["invalido"] = (request, invalid)
    return result


def serialized_examples(data_dir: Path) -> dict:
    return {name: {"request": request.model_dump(mode="json"),
                   "response": to_response(result).model_dump(mode="json")}
            for name, (request, result) in examples(data_dir).items()}
