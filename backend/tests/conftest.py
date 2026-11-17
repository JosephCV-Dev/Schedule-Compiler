from pathlib import Path
import sys

import pytest

from schedule_compiler.infrastructure.catalogs import DataRepository

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from fixtures_contrato import examples  # noqa: E402


@pytest.fixture(scope="session")
def repository():
    return DataRepository(ROOT / "data")


@pytest.fixture(scope="session")
def working(repository):
    return repository.load_catalog()


@pytest.fixture(scope="session")
def contract_examples():
    return examples(ROOT / "data")
