"""Adapta un AST existente para dibujarlo; no analiza texto ni fija coordenadas."""

from schedule_compiler.api.schemas.analysis import AstNodeResponse
from schedule_compiler.compiler.models import (
    AstNode, EnrollmentDeclaration, IntegerLiteral, LocatedValue, OfferDeclaration,
    Program, ScheduleDeclaration, SessionDeclaration, TextLiteral,
)


def ast_to_tree(program: Program) -> AstNodeResponse:
    def leaf(node: TextLiteral | IntegerLiteral | LocatedValue, path: str, label: str) -> AstNodeResponse:
        if isinstance(node, LocatedValue):
            value, state = node.value.value, node.value.state
        else:
            value, state = node.value, None
        return AstNodeResponse(
            id=path, kind="Campo", label=label, span=node.span,
            value=value, value_state=state,
        )

    def branch(node: AstNode, path: str) -> AstNodeResponse:
        if isinstance(node, Program):
            label = "Programa"
            children = [branch(d, f"{path}.{i}") for i, d in enumerate(node.declarations)]
        elif isinstance(node, OfferDeclaration):
            label = "Oferta"
            children = [
                leaf(node.identifier, f"{path}.id", "Identificador"),
                leaf(node.subject, f"{path}.subject", "Materia"),
                leaf(node.group, f"{path}.group", "Grupo"),
                leaf(node.teacher, f"{path}.teacher", "Docente"),
                *[branch(s, f"{path}.session.{i}") for i, s in enumerate(node.sessions)],
            ]
        elif isinstance(node, SessionDeclaration):
            label = "Sesión"
            children = [
                leaf(node.room, f"{path}.room", "Aula"),
                leaf(node.day, f"{path}.day", "Día"),
                leaf(node.hour, f"{path}.hour", "Hora"),
                leaf(node.duration, f"{path}.duration", "Duración (horas)"),
            ]
        elif isinstance(node, ScheduleDeclaration):
            label = "Horario"
            children = [leaf(node.name, f"{path}.name", "Nombre")]
            children += [branch(e, f"{path}.enrollment.{i}") for i, e in enumerate(node.enrollments)]
        elif isinstance(node, EnrollmentDeclaration):
            label = "Inscripción"
            children = [leaf(node.offer_id, f"{path}.offer", "Oferta")]
        else:
            raise TypeError(f"Nodo AST no soportado: {type(node).__name__}")
        return AstNodeResponse(id=path, kind=type(node).__name__, label=label,
                               span=node.span, children=children)

    return branch(program, "ast")
