from fastapi import APIRouter, Depends

from schedule_compiler.api.dependencies import get_repository, resource_errors
from schedule_compiler.api.schemas.analysis import AnalysisRequest, AnalysisResponse, to_response
from schedule_compiler.application.analyze import analyze
from schedule_compiler.infrastructure.catalogs import DataRepository

router = APIRouter(tags=["analysis"])


@router.post("/analyses", response_model=AnalysisResponse)
def analyze_source(request: AnalysisRequest, repository: DataRepository = Depends(get_repository)) -> AnalysisResponse:
    with resource_errors():
        catalog = repository.load_catalog(request.catalog_id)
        policy = repository.load_policy(request.policy_id)
    return to_response(analyze(request.source, catalog, policy, request.source_name, request.scope))
