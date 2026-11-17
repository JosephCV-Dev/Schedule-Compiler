"""Exporta esquemas y casos reales del motor; --check comprueba sincronización."""

import argparse
import json
from pathlib import Path

from fixtures_contrato import serialized_examples
from schedule_compiler.api.schemas.analysis import AnalysisRequest, AnalysisResponse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    artifacts = {
        "analysis-request.schema.json": AnalysisRequest.model_json_schema(),
        "analysis-response.schema.json": AnalysisResponse.model_json_schema(),
    }
    for name, example in serialized_examples(root / "data").items():
        artifacts[f"examples/{name}.json"] = example
    for relative, data in artifacts.items():
        path = root / "contracts" / relative
        text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                raise SystemExit(f"Contrato desactualizado: {path.relative_to(root)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
    print(f"{len(artifacts)} archivos de contrato {'verificados' if args.check else 'exportados'}.")


if __name__ == "__main__":
    main()
