#!/usr/bin/env python3
"""CLI for managing persistent CrewAI review memory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _load_manager():
    root = Path(__file__).resolve().parents[2]
    crewai_dir = root / ".crewai"
    if str(crewai_dir) not in sys.path:
        sys.path.insert(0, str(crewai_dir))
    from tools.memory_manager import get_memory_manager

    return get_memory_manager()


def _print_patterns(patterns: list[dict]) -> None:
    if not patterns:
        print("No learned patterns stored.")
        return
    print("Learned patterns:")
    for item in patterns:
        print(
            "- {id} [{confidence}] ({source}, {date}): {observation}".format(
                id=item.get("id", "unknown"),
                confidence=item.get("confidence", "n/a"),
                source=item.get("source", "unknown"),
                date=item.get("learned_date", "unknown"),
                observation=item.get("observation", ""),
            )
        )


def _print_suppressions(suppressions: list[dict]) -> None:
    if not suppressions:
        print("No suppression rules stored.")
        return
    print("Suppressions:")
    for item in suppressions:
        scope = item.get("file_glob", "")
        scope_suffix = f" (files: {scope})" if scope else ""
        print(
            "- {id} [{status}] {pattern}{scope}: {reason}".format(
                id=item.get("id", "unknown"),
                status="active" if item.get("active", True) else "inactive",
                pattern=item.get("pattern", ""),
                scope=scope_suffix,
                reason=item.get("reason", "no reason provided"),
            )
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage CrewAI persistent review memory")
    parser.add_argument("--add-memory", dest="add_memory", help="Add or update a learned memory")
    parser.add_argument(
        "--no-optimize",
        action="store_true",
        help="Disable LLM optimization for --add-memory",
    )
    parser.add_argument(
        "--optimize-model",
        help="Override model for memory optimization",
    )
    parser.add_argument("--list-memories", action="store_true", help="List learned memories")
    parser.add_argument(
        "--compact-memory",
        action="store_true",
        help="Deduplicate and compact stored memory",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview compaction changes without writing",
    )
    parser.add_argument(
        "--max-trend-entries",
        type=int,
        default=50,
        help="Max review history trend entries to keep during compaction",
    )
    parser.add_argument("--add-suppression", help="Add suppression pattern")
    parser.add_argument("--reason", help="Reason for suppression")
    parser.add_argument("--file-glob", default="", help="Optional suppression file glob")
    parser.add_argument("--list-suppressions", action="store_true", help="List suppression rules")
    parser.add_argument("--all", action="store_true", help="Show inactive entries where supported")
    parser.add_argument("--deactivate-suppression", help="Deactivate suppression by id")
    parser.add_argument(
        "--export-sql",
        action="store_true",
        help="Write SQL seed snapshot from JSON memory",
    )
    parser.add_argument("--sql-output", help="Custom output path for --export-sql")
    parser.add_argument(
        "--materialize-sqlite",
        nargs="?",
        const=".crewai/workspace/memory_runtime.sqlite3",
        help="Create runtime SQLite DB from memory SQL seed (default path in workspace)",
    )
    parser.add_argument(
        "--backend-status", action="store_true", help="Print configured memory backend"
    )
    parser.add_argument("--show-context", action="store_true", help="Print rendered memory context")
    parser.add_argument("--source", default="manual", help="Source tag for --add-memory")
    parser.add_argument(
        "--confidence", type=float, default=0.95, help="Confidence for --add-memory"
    )
    parser.add_argument("--json", action="store_true", help="Output list commands as JSON")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    manager = _load_manager()

    if args.add_memory:
        optimized_observation, strategy = manager.optimize_observation(
            args.add_memory,
            use_llm=not args.no_optimize,
            model=args.optimize_model,
        )
        pattern_id = manager.add_learned_pattern(
            observation=optimized_observation,
            source=args.source,
            confidence=args.confidence,
        )
        manager.save()
        print(f"Saved memory {pattern_id} (strategy={strategy})")
        return 0

    if args.list_memories:
        rows = manager.list_learned_patterns()
        if args.json:
            print(json.dumps(rows, indent=2, ensure_ascii=False))
        else:
            _print_patterns(rows)
        return 0

    if args.compact_memory:
        stats = manager.compact_memory(
            max_trend_entries=args.max_trend_entries,
            dry_run=args.dry_run,
        )
        if args.json:
            print(json.dumps(stats, indent=2, ensure_ascii=False))
        else:
            print(
                "Compaction: patterns_removed={learned_patterns_removed}, "
                "suppressions_removed={suppressions_removed}, "
                "trend_removed={trend_entries_removed}".format(**stats)
            )
        if not args.dry_run:
            manager.save()
        return 0

    if args.add_suppression:
        if not args.reason:
            parser.error("--reason is required with --add-suppression")
        suppression_id = manager.add_suppression(
            pattern=args.add_suppression,
            reason=args.reason,
            file_glob=args.file_glob,
            added_by="memory-cli",
        )
        manager.save()
        print(f"Saved suppression {suppression_id}")
        return 0

    if args.list_suppressions:
        rows = manager.list_suppressions(active_only=not args.all)
        if args.json:
            print(json.dumps(rows, indent=2, ensure_ascii=False))
        else:
            _print_suppressions(rows)
        return 0

    if args.deactivate_suppression:
        ok = manager.deactivate_suppression(args.deactivate_suppression)
        if not ok:
            print(f"Suppression not found or already inactive: {args.deactivate_suppression}")
            return 1
        manager.save()
        print(f"Deactivated suppression {args.deactivate_suppression}")
        return 0

    if args.export_sql:
        output_path = Path(args.sql_output).expanduser().resolve() if args.sql_output else None
        exported = manager.export_sql_seed(output_path=output_path)
        print(f"Exported SQL seed: {exported}")
        return 0

    if args.materialize_sqlite:
        sqlite_path = Path(args.materialize_sqlite).expanduser().resolve()
        sql_seed_path = Path(args.sql_output).expanduser().resolve() if args.sql_output else None
        db_path = manager.materialize_sqlite_db(
            sqlite_path=sqlite_path, sql_seed_path=sql_seed_path
        )
        print(f"Materialized SQLite DB: {db_path}")
        return 0

    if args.backend_status:
        status = manager.backend_status()
        if args.json:
            print(json.dumps(status, indent=2, ensure_ascii=False))
        else:
            print(
                "Backend: {mode} (mem0_enabled={mem0_enabled})\n"
                "memory: {memory_file}\n"
                "suppressions: {suppressions_file}\n"
                "sql-seed: {sql_seed_file}".format(**status)
            )
        return 0

    if args.show_context:
        context = manager.get_context_for_review()
        print(context if context else "No memory context available.")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
