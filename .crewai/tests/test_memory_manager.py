from __future__ import annotations

import json
from pathlib import Path

from tools import memory_manager


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def test_add_learned_pattern_dedupes(tmp_path, monkeypatch):
    memory_file = tmp_path / "memory.json"
    suppressions_file = tmp_path / "suppressions.json"

    _write_json(memory_file, {"learned_patterns": [], "review_history": {}})
    _write_json(suppressions_file, {"suppressions": []})

    monkeypatch.setattr(memory_manager, "MEMORY_FILE", memory_file)
    monkeypatch.setattr(memory_manager, "SUPPRESSIONS_FILE", suppressions_file)

    manager = memory_manager.MemoryManager()
    first_id = manager.add_learned_pattern("Example memory", source="test", confidence=0.7)
    second_id = manager.add_learned_pattern("example memory", source="test", confidence=0.9)

    assert first_id == second_id
    patterns = manager.list_learned_patterns()
    assert len(patterns) == 1
    assert patterns[0]["confidence"] == 0.9


def test_add_suppression_dedupes_and_deactivates(tmp_path, monkeypatch):
    memory_file = tmp_path / "memory.json"
    suppressions_file = tmp_path / "suppressions.json"

    _write_json(memory_file, {"learned_patterns": [], "review_history": {}})
    _write_json(suppressions_file, {"suppressions": []})

    monkeypatch.setattr(memory_manager, "MEMORY_FILE", memory_file)
    monkeypatch.setattr(memory_manager, "SUPPRESSIONS_FILE", suppressions_file)

    manager = memory_manager.MemoryManager()
    first_id = manager.add_suppression(
        pattern="placeholder api keys and tokens",
        reason="template placeholders",
        file_glob="*.env.example",
    )
    second_id = manager.add_suppression(
        pattern="placeholder api keys and tokens",
        reason="template placeholders",
        file_glob="*.env.example",
    )

    assert first_id == second_id
    assert len(manager.list_suppressions(active_only=False)) == 1

    assert manager.deactivate_suppression(first_id) is True
    assert manager.deactivate_suppression(first_id) is False


def test_context_contains_learned_patterns_and_active_suppressions(tmp_path, monkeypatch):
    memory_file = tmp_path / "memory.json"
    suppressions_file = tmp_path / "suppressions.json"

    _write_json(memory_file, {"learned_patterns": [], "review_history": {}})
    _write_json(suppressions_file, {"suppressions": []})

    monkeypatch.setattr(memory_manager, "MEMORY_FILE", memory_file)
    monkeypatch.setattr(memory_manager, "SUPPRESSIONS_FILE", suppressions_file)

    manager = memory_manager.MemoryManager()
    manager.add_learned_pattern("Do not flag fake placeholders", source="test", confidence=1.0)
    manager.add_suppression(
        pattern="placeholder api keys and tokens",
        reason="template placeholders",
        file_glob="*.env.example",
    )

    context = manager.get_context_for_review()

    assert "Learned Patterns About This Codebase" in context
    assert "Active Review Suppressions" in context
    assert "placeholder api keys and tokens" in context


def test_optimize_observation_heuristic_without_api_key(tmp_path, monkeypatch):
    memory_file = tmp_path / "memory.json"
    suppressions_file = tmp_path / "suppressions.json"
    sql_seed_file = tmp_path / "sql" / "memory_seed.sql"

    _write_json(memory_file, {"learned_patterns": [], "review_history": {}})
    _write_json(suppressions_file, {"suppressions": []})

    monkeypatch.setattr(memory_manager, "MEMORY_FILE", memory_file)
    monkeypatch.setattr(memory_manager, "SUPPRESSIONS_FILE", suppressions_file)
    monkeypatch.setattr(memory_manager, "MEMORY_SQL_SEED_FILE", sql_seed_file)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    manager = memory_manager.MemoryManager()
    text, strategy = manager.optimize_observation("  keep   this   compact  ")

    assert text == "keep this compact"
    assert strategy == "heuristic"


def test_compact_memory_dry_run_and_apply(tmp_path, monkeypatch):
    memory_file = tmp_path / "memory.json"
    suppressions_file = tmp_path / "suppressions.json"
    sql_seed_file = tmp_path / "sql" / "memory_seed.sql"

    _write_json(
        memory_file,
        {
            "learned_patterns": [
                {
                    "id": "pat-001",
                    "observation": "Use explicit labels",
                    "confidence": 0.6,
                    "source": "test",
                    "learned_date": "2026-02-15",
                },
                {
                    "id": "pat-002",
                    "observation": "use explicit labels",
                    "confidence": 0.9,
                    "source": "test",
                    "learned_date": "2026-02-15",
                },
            ],
            "review_history": {
                "findings_trend": [
                    {"pr": "1", "findings": 1, "date": "2026-02-10"},
                    {"pr": "2", "findings": 2, "date": "2026-02-11"},
                    {"pr": "3", "findings": 3, "date": "2026-02-12"},
                ]
            },
        },
    )
    _write_json(
        suppressions_file,
        {
            "suppressions": [
                {
                    "id": "sup-001",
                    "pattern": "placeholder",
                    "file_glob": "*.env.example",
                    "reason": "ok",
                    "added_by": "test",
                    "added_date": "2026-02-15",
                    "expires": None,
                    "active": True,
                },
                {
                    "id": "sup-002",
                    "pattern": "placeholder",
                    "file_glob": "*.env.example",
                    "reason": "ok",
                    "added_by": "test",
                    "added_date": "2026-02-15",
                    "expires": None,
                    "active": True,
                },
            ]
        },
    )

    monkeypatch.setattr(memory_manager, "MEMORY_FILE", memory_file)
    monkeypatch.setattr(memory_manager, "SUPPRESSIONS_FILE", suppressions_file)
    monkeypatch.setattr(memory_manager, "MEMORY_SQL_SEED_FILE", sql_seed_file)

    manager = memory_manager.MemoryManager()
    preview = manager.compact_memory(max_trend_entries=2, dry_run=True)
    assert preview["learned_patterns_removed"] == 1
    assert preview["suppressions_removed"] == 1
    assert preview["trend_entries_removed"] == 1

    applied = manager.compact_memory(max_trend_entries=2, dry_run=False)
    assert applied == preview
    assert len(manager.list_learned_patterns()) == 1
    assert len(manager.list_suppressions(active_only=False)) == 1
    assert len(manager._memory["review_history"]["findings_trend"]) == 2


def test_export_sql_and_materialize_sqlite(tmp_path, monkeypatch):
    memory_file = tmp_path / "memory.json"
    suppressions_file = tmp_path / "suppressions.json"
    sql_seed_file = tmp_path / "sql" / "memory_seed.sql"
    sqlite_file = tmp_path / "runtime" / "memory.sqlite3"

    _write_json(memory_file, {"learned_patterns": [], "review_history": {}})
    _write_json(suppressions_file, {"suppressions": []})

    monkeypatch.setattr(memory_manager, "MEMORY_FILE", memory_file)
    monkeypatch.setattr(memory_manager, "SUPPRESSIONS_FILE", suppressions_file)
    monkeypatch.setattr(memory_manager, "MEMORY_SQL_SEED_FILE", sql_seed_file)

    manager = memory_manager.MemoryManager()
    manager.add_learned_pattern("Keep deterministic outputs", source="test", confidence=1.0)
    manager.add_suppression(
        pattern="placeholder",
        reason="expected",
        file_glob="*.env.example",
    )
    manager.record_review(pr_number="101", findings_count=4)
    manager.save()

    assert sql_seed_file.exists()
    sql_text = sql_seed_file.read_text()
    assert "CREATE TABLE IF NOT EXISTS learned_patterns" in sql_text
    assert "INSERT INTO suppressions" in sql_text

    db_path = manager.materialize_sqlite_db(sqlite_path=sqlite_file)
    assert db_path.exists()

    import sqlite3

    connection = sqlite3.connect(db_path)
    try:
        row = connection.execute("SELECT COUNT(*) FROM learned_patterns").fetchone()
    finally:
        connection.close()

    assert row is not None
    assert row[0] == 1
