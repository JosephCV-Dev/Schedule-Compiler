"""Contrato HTTP v1 propuesto. Todavía no se registra POST /analyses."""

from __future__ import annotations

from dataclasses import asdict
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from schedule_compiler.application.contracts import (
    AnalysisResult, AnalysisStatus, CheckState, PhaseState, Scope, Severity, Stage,
)
from schedule_compiler.domain.models import ValueState, Weekday


class DTO(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class AnalysisRequest(DTO):
    source: str
    source_name: str = "editor"
    language_version: Literal["0.2"] = "0.2"
    catalog_id: Literal["isc-26-1-trabajo", "isc-26-1-original"] = "isc-26-1-trabajo"
    policy_id: Literal["proyecto-v0.2"] = "proyecto-v0.2"
    scope: Scope = Scope.PERSONAL


class PositionResponse(DTO):
    offset: int = Field(ge=0)
    line: int = Field(ge=1)
    column: int = Field(ge=1)


class SpanResponse(DTO):
    start: PositionResponse
    end: PositionResponse


class OriginResponse(DTO):
    kind: Literal["TEXTO", "EXCEL", "JSON"]
    source_id: str
    span: SpanResponse | None
    sheet: str | None
    cells: list[str]
    pointer: str | None


class FieldValueResponse(DTO):
    state: ValueState
    value: str | None


class PatternResponse(DTO):
    id: str
    description: str
    expression: str


class TokenResponse(DTO):
    kind: str
    lexeme: str
    pattern_id: str
    span: SpanResponse


class AstNodeResponse(DTO):
    id: str
    kind: str
    label: str
    value: str | int | None = None
    value_state: ValueState | None = None
    span: SpanResponse
    children: list[AstNodeResponse] = Field(default_factory=list)


class PhaseResponse(DTO):
    stage: Stage
    state: PhaseState


class DiagnosticResponse(DTO):
    code: str
    stage: str
    severity: Severity
    message: str
    origin: OriginResponse | None
    related: list[OriginResponse]


class CheckResponse(DTO):
    code: str
    state: CheckState
    required: bool
    message: str
    origins: list[OriginResponse]


class SymbolAttributeResponse(DTO):
    name: str
    value: FieldValueResponse


class SymbolResponse(DTO):
    id: str
    kind: str
    label: str
    attributes: list[SymbolAttributeResponse]
    origins: list[OriginResponse]


class IntervalResponse(DTO):
    start_minute: int = Field(ge=0, lt=1440)
    end_minute: int = Field(gt=0, le=1440)


class SessionResponse(DTO):
    id: str
    offer_id: str
    day: Weekday
    interval: IntervalResponse
    room: FieldValueResponse
    origins: list[OriginResponse]


class ScheduleResponse(DTO):
    name: str
    sessions: list[SessionResponse]


class MetadataResponse(DTO):
    language_version: str
    catalog_id: str
    catalog_sha256: str
    policy_id: str
    policy_version: str
    scope: Scope
    source_name: str


class AnalysisResponse(DTO):
    schema_version: Literal["1"] = "1"
    metadata: MetadataResponse
    status: AnalysisStatus
    phases: list[PhaseResponse]
    patterns: list[PatternResponse]
    tokens: list[TokenResponse]
    ast: AstNodeResponse | None
    symbols: list[SymbolResponse]
    diagnostics: list[DiagnosticResponse]
    catalog_diagnostics: list[DiagnosticResponse]
    checks: list[CheckResponse]
    schedules: list[ScheduleResponse]


def to_response(result: AnalysisResult) -> AnalysisResponse:
    from schedule_compiler.api.tree import ast_to_tree

    data = asdict(result)
    data["ast"] = ast_to_tree(result.ast) if result.ast is not None else None
    return AnalysisResponse.model_validate(data)
