"""Ejecutar las tres fases del compilador con catálogo y política locales."""

import argparse
from collections import Counter
import json
from pathlib import Path

from schedule_compiler.api.schemas.analysis import to_response
from schedule_compiler.application.analyze import analyze
from schedule_compiler.application.contracts import AnalysisStatus, Scope
from schedule_compiler.cli.common import print_diagnostics, read_source
from schedule_compiler.infrastructure.catalogs import CATALOG_FILES, POLICY_FILES, DataRepository
from schedule_compiler.infrastructure.resources import default_directories


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, nargs="?")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--scope", choices=[s.value for s in Scope], default=Scope.PERSONAL.value)
    parser.add_argument("--catalog", choices=list(CATALOG_FILES), default="isc-26-1-trabajo")
    parser.add_argument("--policy", choices=list(POLICY_FILES), default="proyecto-v0.2")
    parser.add_argument("--data-dir", type=Path, default=default_directories()[0])
    args = parser.parse_args()
    source, name = read_source(args.file, parser)
    repository = DataRepository(args.data_dir)
    try:
        catalog, policy = repository.load_catalog(args.catalog), repository.load_policy(args.policy)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(2, f"No se pudieron cargar catálogo o política: {error}\n")
    result = analyze(source, catalog, policy, name, Scope(args.scope))
    if args.json:
        print(json.dumps(to_response(result).model_dump(mode="json"), ensure_ascii=False, indent=2))
    else:
        print(f"Resultado: {result.status.value} · Alcance: {result.metadata.scope.value}")
        for phase in result.phases:
            print(f"{phase.stage.value}: {phase.state.value}")
        print(f"{len(result.tokens)} tokens · {len(result.symbols)} símbolos")
        print("Comprobaciones:", dict(Counter(c.state.value for c in result.checks)))
        print("Capacidad, laboratorio y límites horarios: no configurados. Profesores: texto libre.")
        for view in result.schedules:
            print(f"\nHorario: {view.name}")
            for session in view.sessions:
                start, end = session.interval.start_minute, session.interval.end_minute
                room = session.room.value if session.room.value is not None else session.room.state.value
                print(f"{session.day.value:10} {start // 60:02d}:{start % 60:02d}–"
                      f"{end // 60:02d}:{end % 60:02d} | {session.offer_id} | {room}")
        print_diagnostics(result.diagnostics)
        print(f"\nAuditoría del catálogo: {len(result.catalog_diagnostics)} hallazgos separados del resultado personal.")
        print("Disponibilidad limitada a las ocupaciones cargadas y la política indicada.")
    return 0 if result.status == AnalysisStatus.VALID else 1


if __name__ == "__main__":
    raise SystemExit(main())
