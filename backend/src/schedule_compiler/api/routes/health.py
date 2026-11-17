"""Comprobación de disponibilidad de la API, sin ejecutar el compilador."""

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: Literal["schedule-compiler"] = "schedule-compiler"
    language_version: Literal["0.2"] = "0.2"
    compiler_available: Literal[True] = True


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()
