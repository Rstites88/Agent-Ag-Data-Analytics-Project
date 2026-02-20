from __future__ import annotations

from pathlib import Path

from tools import memory_cli


class _FakeManager:
    def __init__(self):
        self.saved = False

    def optimize_observation(self, observation, *, use_llm=True, model=None):
        return (observation.strip(), "heuristic")

    def add_learned_pattern(self, observation, source="manual", confidence=0.95):
        assert observation
        return "pat-001"

    def save(self):
        self.saved = True
        return True

    def compact_memory(self, max_trend_entries=50, dry_run=False):
        return {
            "learned_patterns_removed": 1,
            "suppressions_removed": 0,
            "trend_entries_removed": 2,
        }

    def export_sql_seed(self, output_path=None):
        path = output_path or Path("/tmp/memory_seed.sql")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("BEGIN;\nCOMMIT;\n", encoding="utf-8")
        return path

    def materialize_sqlite_db(self, sqlite_path, sql_seed_path=None):
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        sqlite_path.write_text("sqlite", encoding="utf-8")
        return sqlite_path

    def backend_status(self):
        return {
            "mode": "local",
            "mem0_enabled": "false",
            "memory_file": "/tmp/memory.json",
            "suppressions_file": "/tmp/suppressions.json",
            "sql_seed_file": "/tmp/memory_seed.sql",
        }

    def list_learned_patterns(self):
        return []

    def list_suppressions(self, active_only=True):
        return []

    def deactivate_suppression(self, suppression_id):
        return suppression_id == "sup-001"

    def get_context_for_review(self):
        return ""


def test_memory_cli_compact_memory_dry_run(monkeypatch, capsys):
    manager = _FakeManager()
    monkeypatch.setattr(memory_cli, "_load_manager", lambda: manager)
    monkeypatch.setattr(memory_cli.sys, "argv", ["memory_cli.py", "--compact-memory", "--dry-run"])

    exit_code = memory_cli.main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Compaction:" in output
    assert manager.saved is False


def test_memory_cli_backend_status_json(monkeypatch, capsys):
    manager = _FakeManager()
    monkeypatch.setattr(memory_cli, "_load_manager", lambda: manager)
    monkeypatch.setattr(memory_cli.sys, "argv", ["memory_cli.py", "--backend-status", "--json"])

    exit_code = memory_cli.main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"mode": "local"' in output


def test_memory_cli_materialize_sqlite(monkeypatch, tmp_path, capsys):
    manager = _FakeManager()
    sqlite_path = tmp_path / "memory.sqlite3"
    monkeypatch.setattr(memory_cli, "_load_manager", lambda: manager)
    monkeypatch.setattr(
        memory_cli.sys,
        "argv",
        ["memory_cli.py", "--materialize-sqlite", str(sqlite_path)],
    )

    exit_code = memory_cli.main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Materialized SQLite DB" in output
    assert sqlite_path.exists()
