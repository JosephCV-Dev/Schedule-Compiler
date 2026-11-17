"""Punto de entrada HTTP; las reglas del lenguaje pertenecen al núcleo."""

from pathlib import Path

from fastapi import FastAPI

from schedule_compiler.api.routes.analysis import router as analysis_router
from schedule_compiler.api.routes.health import router as health_router
from schedule_compiler.api.routes.resources import router as resources_router
from schedule_compiler.infrastructure.catalogs import DataRepository
from schedule_compiler.infrastructure.resources import ExampleRepository, default_directories


def create_app(data_dir: Path | None = None, examples_dir: Path | None = None) -> FastAPI:
    default_data, default_examples = default_directories()
    app = FastAPI(
        title="Schedule Compiler API",
        version="0.1.0",
        description="Análisis léxico, sintáctico y semántico de horarios .hor v0.2.",
    )
    app.state.data_repository = DataRepository(data_dir if data_dir is not None else default_data)
    app.state.example_repository = ExampleRepository(examples_dir if examples_dir is not None else default_examples)
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(analysis_router, prefix="/api/v1")
    app.include_router(resources_router, prefix="/api/v1")
    return app


app = create_app()
