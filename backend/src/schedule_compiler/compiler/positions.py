"""Coordenadas Unicode del texto recibido, sin normalizar sus saltos de línea."""

from schedule_compiler.domain.models import Position, Span


def position_at(source: str, offset: int) -> Position:
    if not 0 <= offset <= len(source):
        raise ValueError("Offset fuera de la fuente.")
    return Position(offset, source.count("\n", 0, offset) + 1,
                    offset - source.rfind("\n", 0, offset))


def source_span(source: str, start: int, end: int) -> Span:
    return Span(position_at(source, start), position_at(source, end))
