from schedule_compiler.api.schemas.analysis import (
    DTO, DiagnosticResponse, FieldValueResponse, OriginResponse, SessionResponse,
)
from schedule_compiler.application.contracts import Scope


class CatalogSourceResponse(DTO):
    file: str
    sha256: str
    sheet: str


class OfferResponse(DTO):
    id: str
    subject: str
    group: FieldValueResponse
    teacher: FieldValueResponse
    sessions: list[SessionResponse]
    origins: list[OriginResponse]
    subject_id: str | None
    weekly_hours: int | None


class RoomResponse(DTO):
    id: str
    capacity: int | None
    type: str | None


class GroupResponse(DTO):
    id: str
    students: int | None


class SubjectResponse(DTO):
    id: str
    source_names: list[str]
    requires_lab: bool | None


class AdjustmentResponse(DTO):
    session_id: str
    previous_room: str | None
    new_room: str | None
    reason: str
    origin: OriginResponse


class CatalogSummaryResponse(DTO):
    id: str
    source: CatalogSourceResponse
    snapshot_sha256: str
    offers: int
    sessions: int


class CatalogResponse(DTO):
    id: str
    source: CatalogSourceResponse
    snapshot_sha256: str
    offers: list[OfferResponse]
    rooms: list[RoomResponse]
    groups: list[GroupResponse]
    subjects: list[SubjectResponse]
    adjustments: list[AdjustmentResponse]
    limitations: list[str]
    source_audit_scope: str


class AuditResponse(DTO):
    catalog_id: str
    snapshot_sha256: str
    stored_audit_scope: str
    diagnostics: list[DiagnosticResponse]
    adjustments: list[AdjustmentResponse]


class PolicyResponse(DTO):
    id: str
    version: str
    teacher_rules_enabled: bool
    allow_new_rooms: bool
    check_room_occupancy: bool
    unassigned_room_status: str
    auto_assign_rooms: bool
    capacity: str
    laboratory: str
    permitted_hours: str


class ExampleSummaryResponse(DTO):
    id: str
    title: str
    source_name: str
    scope: Scope


class ExampleResponse(ExampleSummaryResponse):
    source: str
