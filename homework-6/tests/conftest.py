import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def sample_transactions() -> list[dict]:
    path = PROJECT_ROOT / "sample-transactions.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def sample_transactions_file(tmp_path: Path, sample_transactions: list[dict]) -> Path:
    dest = tmp_path / "sample-transactions.json"
    dest.write_text(json.dumps(sample_transactions), encoding="utf-8")
    return dest
