from contextlib import contextmanager
from collections.abc import Iterator
import logging

from fastapi import HTTPException, Request

from schedule_compiler.infrastructure.catalogs import DataRepository
from schedule_compiler.infrastructure.resources import ExampleRepository

logger = logging.getLogger(__name__)


def get_repository(request: Request) -> DataRepository:
    return request.app.state.data_repository


def get_examples(request: Request) -> ExampleRepository:
    return request.app.state.example_repository


@contextmanager
def resource_errors() -> Iterator[None]:
    try:
        yield
    except (OSError, ValueError, KeyError, TypeError) as error:
        logger.exception("No se pudo cargar un recurso configurado.")
        raise HTTPException(503, "Catálogo, política o ejemplos no disponibles; revisa la configuración del servidor.") from error
