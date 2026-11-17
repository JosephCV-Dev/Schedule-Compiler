"""Caso de uso completo. No conoce FastAPI, archivos ni la interfaz web."""

from schedule_compiler.application.audit import audit_catalog
from schedule_compiler.application.contracts import (
    AnalysisMetadata, AnalysisResult, AnalysisStatus, PhaseReport, PhaseState, Scope, Stage,
)
from schedule_compiler.application.semantics import analyze_semantics
from schedule_compiler.compiler.parser import parse
from schedule_compiler.domain.diagnostics import Severity
from schedule_compiler.domain.models import Catalog, ValidationPolicy
from schedule_compiler.domain.validation import CheckState


def analyze(source: str, catalog: Catalog, policy: ValidationPolicy,
            source_name: str = "editor", scope: Scope = Scope.PERSONAL) -> AnalysisResult:
    parsed = parse(source, source_name)
    metadata = AnalysisMetadata("0.2", catalog.id, catalog.snapshot_sha256,
                                policy.id, policy.version, scope, source_name)
    phases = [PhaseReport(Stage.LEXICAL, PhaseState.COMPLETED if parsed.lexical.success else PhaseState.FAILED),
              PhaseReport(Stage.SYNTACTIC, PhaseState.COMPLETED if parsed.success else
                          PhaseState.FAILED if parsed.executed else PhaseState.NOT_RUN)]
    common = dict(metadata=metadata, patterns=parsed.lexical.patterns, tokens=parsed.lexical.tokens,
                  ast=parsed.ast, catalog_diagnostics=audit_catalog(catalog))
    if not parsed.success:
        return AnalysisResult(status=AnalysisStatus.INVALID,
                              phases=tuple(phases + [PhaseReport(Stage.SEMANTIC, PhaseState.NOT_RUN)]),
                              diagnostics=parsed.lexical.diagnostics + parsed.diagnostics, **common)
    report = analyze_semantics(parsed.ast, catalog, policy, source_name, scope)
    failed = any(d.severity == Severity.ERROR for d in report.diagnostics)
    failed = failed or any(c.state == CheckState.FAILED for c in report.checks)
    pending = any(c.required and c.state == CheckState.UNKNOWN for c in report.checks)
    status = AnalysisStatus.INVALID if failed else AnalysisStatus.INCOMPLETE if pending else AnalysisStatus.VALID
    return AnalysisResult(status=status,
                          phases=tuple(phases + [PhaseReport(Stage.SEMANTIC, PhaseState.FAILED if failed else PhaseState.COMPLETED)]),
                          diagnostics=report.diagnostics, checks=report.checks, symbols=report.symbols,
                          schedules=report.schedules, **common)
