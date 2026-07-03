import json
from pathlib import Path

from integrator import main, print_summary, run_pipeline


def test_pipeline_produces_one_result_per_transaction(tmp_path: Path, sample_transactions_file: Path):
    shared_root = tmp_path / "shared"

    summary = run_pipeline(sample_transactions_file, shared_root)

    result_files = list((shared_root / "results").glob("TXN*.json"))
    assert len(result_files) == summary["total_transactions"] == 8


def test_pipeline_status_counts_match_expected_distribution(tmp_path: Path, sample_transactions_file: Path):
    shared_root = tmp_path / "shared"

    summary = run_pipeline(sample_transactions_file, shared_root)

    assert summary["status_counts"] == {
        "approved": 3,
        "flagged_for_review": 3,
        "rejected": 2,
    }


def test_pipeline_writes_summary_and_log(tmp_path: Path, sample_transactions_file: Path):
    shared_root = tmp_path / "shared"

    run_pipeline(sample_transactions_file, shared_root)

    summary_path = shared_root / "results" / "pipeline_summary.json"
    log_path = shared_root / "results" / "pipeline_run.log"
    assert summary_path.exists()
    assert log_path.exists()
    assert len(log_path.read_text(encoding="utf-8").splitlines()) > 0


def test_rejected_transaction_never_reaches_fraud_detector(tmp_path: Path, sample_transactions_file: Path):
    shared_root = tmp_path / "shared"

    run_pipeline(sample_transactions_file, shared_root)

    fraud_output = shared_root / "output" / "TXN006_fraud_detector.json"
    assert not fraud_output.exists()


def test_pipeline_never_touches_real_project_shared_dir(tmp_path: Path, sample_transactions_file: Path):
    project_shared = Path(__file__).resolve().parent.parent / "shared"
    before = set(project_shared.rglob("*")) if project_shared.exists() else set()

    run_pipeline(sample_transactions_file, tmp_path / "shared")

    after = set(project_shared.rglob("*")) if project_shared.exists() else set()
    assert before == after


def test_clear_flag_wipes_previous_run(tmp_path: Path, sample_transactions_file: Path):
    shared_root = tmp_path / "shared"
    stale = shared_root / "results" / "stale.json"
    stale.parent.mkdir(parents=True, exist_ok=True)
    stale.write_text("{}", encoding="utf-8")

    run_pipeline(sample_transactions_file, shared_root, clear=True)

    assert not stale.exists()


def test_print_summary_includes_status_and_reason(capsys):
    summary = {
        "total_transactions": 1,
        "status_counts": {"flagged_for_review": 1},
        "outcomes": [
            {"transaction_id": "TXN002", "status": "flagged_for_review", "reason": "fraud_risk_flagged", "risk_score": 0.9}
        ],
    }
    print_summary(summary)
    captured = capsys.readouterr()
    assert "Total transactions: 1" in captured.out
    assert "TXN002: flagged_for_review risk=0.9 (fraud_risk_flagged)" in captured.out


def test_main_runs_pipeline_end_to_end(tmp_path: Path, sample_transactions_file: Path, capsys):
    shared_root = tmp_path / "shared"
    exit_code = main(["--input", str(sample_transactions_file), "--shared-root", str(shared_root), "--clear"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Pipeline Summary" in captured.out
    assert (shared_root / "results" / "pipeline_summary.json").exists()
