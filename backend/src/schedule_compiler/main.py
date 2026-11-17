"""Punto de entrada HTTP; las reglas del lenguaje pertenecen al núcleo."""

from fastapi import FastAPI

from schedule_compiler.api.routes.health import router as health_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Schedule Compiler API",
        version="0.1.0",
        description="Base del proyecto. El análisis de horarios aún no está implementado.",
    )
    app.include_router(health_router, prefix="/api/v1")
    return app


app = create_app()
