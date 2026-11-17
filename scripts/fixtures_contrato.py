"""Casos de contrato generados por el motor real de las tres fases."""

from pathlib import Path

from schedule_compiler.api.schemas.analysis import AnalysisRequest, to_response
from schedule_compiler.application.analyze import analyze
from schedule_compiler.infrastructure.catalogs import DataRepository


def examples(data_dir: Path) -> dict:
    repository = DataRepository(data_dir)
    catalog, policy = repository.load_catalog(), repository.load_policy()
    sources = {
        "valido": 'HORARIO "Ejemplo" { INSCRIBIR "ISC_7B_COMPILADORES" }',
        "incompleto": 'HORARIO "Ejemplo" { INSCRIBIR "ISC_1RA_ALGEBRA_SUPERIOR" }',
        "invalido": 'HORARIO "Sin cierre',
    }
    results = {}
    for name, source in sources.items():
        request = AnalysisRequest(source=source, source_name=f"{name}.hor")
        result = analyze(source, catalog, policy, request.source_name, request.scope)
        results[name] = (request, result)
    return results


def serialized_examples(data_dir: Path) -> dict:
    return {name: {"request": request.model_dump(mode="json"),
                   "response": to_response(result).model_dump(mode="json")}
            for name, (request, result) in examples(data_dir).items()}
