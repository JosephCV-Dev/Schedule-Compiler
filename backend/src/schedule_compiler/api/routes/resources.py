from fastapi import APIRouter, Depends, HTTPException

from schedule_compiler.api.dependencies import get_examples, get_repository, resource_errors
from schedule_compiler.api.schemas.resources import (
    AuditResponse, CatalogResponse, CatalogSummaryResponse, ExampleResponse,
    ExampleSummaryResponse, PolicyResponse,
)
from schedule_compiler.application.audit import audit_catalog
from schedule_compiler.domain.models import Catalog, ValidationPolicy
from schedule_compiler.infrastructure.catalogs import CATALOG_FILES, POLICY_FILES, DataRepository
from schedule_compiler.infrastructure.resources import EXAMPLES, ExampleRepository

router = APIRouter(tags=["resources"])


@router.get("/catalogs", response_model=list[CatalogSummaryResponse])
def list_catalogs(repository: DataRepository = Depends(get_repository)) -> list[CatalogSummaryResponse]:
    summaries = []
    with resource_errors():
        for identifier in CATALOG_FILES:
            catalog = repository.load_catalog(identifier)
            summaries.append(CatalogSummaryResponse(
                id=catalog.id, source=catalog.source, snapshot_sha256=catalog.snapshot_sha256,
                offers=len(catalog.offers), sessions=sum(len(o.sessions) for o in catalog.offers),
            ))
    return summaries


def load_catalog(identifier: str, repository: DataRepository) -> Catalog:
    if identifier not in CATALOG_FILES:
        raise HTTPException(404, "Catálogo no encontrado.")
    with resource_errors():
        return repository.load_catalog(identifier)


@router.get("/catalogs/{catalog_id}", response_model=CatalogResponse)
def get_catalog(catalog_id: str, repository: DataRepository = Depends(get_repository)) -> Catalog:
    return load_catalog(catalog_id, repository)


@router.get("/catalogs/{catalog_id}/audit", response_model=AuditResponse)
def get_audit(catalog_id: str, repository: DataRepository = Depends(get_repository)) -> AuditResponse:
    catalog = load_catalog(catalog_id, repository)
    return AuditResponse(catalog_id=catalog.id, snapshot_sha256=catalog.snapshot_sha256,
                         stored_audit_scope=catalog.source_audit_scope,
                         diagnostics=audit_catalog(catalog), adjustments=catalog.adjustments)


@router.get("/policies/{policy_id}", response_model=PolicyResponse)
def get_policy(policy_id: str, repository: DataRepository = Depends(get_repository)) -> ValidationPolicy:
    if policy_id not in POLICY_FILES:
        raise HTTPException(404, "Política no encontrada.")
    with resource_errors():
        return repository.load_policy(policy_id)


@router.get("/examples", response_model=list[ExampleSummaryResponse])
def list_examples() -> list[ExampleSummaryResponse]:
    return [ExampleSummaryResponse(id=key, source_name=file, title=title, scope=scope)
            for key, (file, title, scope) in EXAMPLES.items()]


@router.get("/examples/{example_id}", response_model=ExampleResponse)
def get_example(example_id: str, examples: ExampleRepository = Depends(get_examples)) -> ExampleResponse:
    if example_id not in EXAMPLES:
        raise HTTPException(404, "Ejemplo no encontrado.")
    with resource_errors():
        source, filename, scope = examples.read(example_id)
    return ExampleResponse(id=example_id, title=EXAMPLES[example_id][1], scope=scope,
                           source_name=filename, source=source)
