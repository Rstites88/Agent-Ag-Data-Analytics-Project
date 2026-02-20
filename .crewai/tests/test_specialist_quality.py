"""Tests for specialist relevance and output quality hardening."""

import json
from pathlib import Path

import main


def test_clean_summary_text_strips_json_wrapper():
    text = 'json {"summary": "Concrete actionable summary."}'
    assert main._clean_summary_text(text) == "Concrete actionable summary."


def test_clean_summary_text_rejects_simulation_language():
    text = "Simulated data engineering review based on assumed changed files."
    assert main._clean_summary_text(text) == ""


def test_specialist_relevance_for_data_engineering_matches_sql_changes(tmp_path, monkeypatch):
    workspace = Path(main.__file__).parent / "workspace"
    workspace.mkdir(exist_ok=True)
    diff_json = workspace / "diff.json"
    diff_json.write_text(json.dumps({"file_list": ["data/sql/orders.sql"]}))

    monkeypatch.setattr(main, "_CHANGED_FILE_CANDIDATES", None)
    relevant, reason = main._specialist_relevance("data_engineering")
    assert relevant is True
    assert "Matched" in reason


def test_specialist_relevance_for_data_engineering_ignores_unrelated_changes(monkeypatch):
    monkeypatch.setattr(main, "_CHANGED_FILE_CANDIDATES", ["src/ui/button.tsx"])
    relevant, _reason = main._specialist_relevance("data_engineering")
    assert relevant is False


def test_specialist_relevance_complete_mode_relaxes_filters(monkeypatch):
    monkeypatch.setattr(main, "_CHANGED_FILE_CANDIDATES", ["src/ui/button.tsx"])
    relevant, reason = main._specialist_relevance("data_engineering", complete_mode=True)
    assert relevant is True
    assert "complete full review mode" in reason.lower()


def test_build_no_relevant_output_is_explicit():
    data = main._build_no_relevant_output("data_engineering", "No SQL/schema files changed.")
    assert data["findings"] == []
    assert data["severity_counts"]["critical"] == 0
    assert "did not detect relevant changed files" in data["summary"].lower()


def test_mode_aware_specialist_decision_default_is_conservative():
    workflows, specialists, suggestions, mode = main._mode_aware_specialist_decision(
        labels=[],
        changed_files=["src/utils/helpers.py"],
        additions=20,
        deletions=5,
    )
    assert mode == "default"
    assert workflows == ["ci-log-analysis", "quick-review"]
    assert specialists == []
    assert all(isinstance(item, str) for item in suggestions)


def test_mode_aware_specialist_decision_full_review_is_broader():
    workflows, specialists, _suggestions, mode = main._mode_aware_specialist_decision(
        labels=["crewai:full-review"],
        changed_files=[
            "src/auth/login.py",
            "README.md",
            "data/sql/pipeline.sql",
            "apps/web/src/components/Form.tsx",
        ],
        additions=300,
        deletions=120,
    )
    assert mode == "full-review"
    assert "full-review" in workflows
    assert 3 <= len(specialists) <= 6
    assert "security" in specialists


def test_mode_aware_specialist_decision_complete_mode_runs_all():
    workflows, specialists, _suggestions, mode = main._mode_aware_specialist_decision(
        labels=["crewai:complete-full-review"],
        changed_files=["src/main.py"],
        additions=10,
        deletions=4,
    )
    assert mode == "complete-full-review"
    assert workflows == ["ci-log-analysis", "quick-review", "full-review"]
    assert specialists == list(main.SPECIALIST_CREWS.keys())
