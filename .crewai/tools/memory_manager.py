"""Persistent review memory with local JSON and optional mem0 backends.

This module provides a unified memory interface for the CrewAI review system.
By default, memories are stored as JSON files in .crewai/memory/ and committed
to the repository, making review preferences version-controlled and portable.

Backend options:
- local (default): JSON + SQL seed files in-repo
- cloud: mem0 Cloud via USE_MEM0_CLOUD=true and MEM0_API_KEY
- self-hosted: mem0 self-hosted via USE_MEM0_SELF_HOSTED=true and
  MEM0_SELF_HOSTED_URL
"""

from __future__ import annotations

import importlib
import json
import logging
import os
import sqlite3
from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

MEMORY_DIR = (Path(__file__).parent.parent / "memory").resolve()
SUPPRESSIONS_FILE = MEMORY_DIR / "suppressions.json"
MEMORY_FILE = MEMORY_DIR / "memory.json"
MEMORY_SQL_DIR = MEMORY_DIR / "sql"
MEMORY_SQL_SEED_FILE = MEMORY_SQL_DIR / "memory_seed.sql"


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"Could not load {path.name}: {e}")
        return {}


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


class MemoryManager:
    """Unified memory interface with local-first persistence."""

    def __init__(self):
        self._suppressions = _load_json(SUPPRESSIONS_FILE)
        self._memory = _load_json(MEMORY_FILE)
        self._mem0_client: Optional[Any] = None
        self._mem0_mode = self._resolve_mem0_mode()
        self._dirty = False

        if self._mem0_mode != "local":
            self._init_mem0(self._mem0_mode)

    @staticmethod
    def _is_truthy(value: str) -> bool:
        return value.strip().lower() in {"1", "true", "yes", "on"}

    def _resolve_mem0_mode(self) -> str:
        backend = os.getenv("MEM0_BACKEND", "").strip().lower()
        if backend in {"local", "cloud", "self-hosted", "self_hosted", "selfhosted"}:
            if backend.startswith("self"):
                return "self-hosted"
            return backend

        if self._is_truthy(os.getenv("USE_MEM0_SELF_HOSTED", "")):
            return "self-hosted"
        if self._is_truthy(os.getenv("USE_MEM0_CLOUD", "")):
            return "cloud"
        return "local"

    def _init_mem0(self, mode: str) -> None:
        try:
            mem0_module = importlib.import_module("mem0")
            MemoryClient = getattr(mem0_module, "MemoryClient")
        except Exception:
            logger.warning("mem0 package not installed, install mem0ai or use local backend")
            self._mem0_mode = "local"
            return

        candidates: list[dict[str, str]] = []
        if mode == "cloud":
            api_key = os.getenv("MEM0_API_KEY", "").strip()
            if not api_key:
                logger.warning("mem0 cloud requested but MEM0_API_KEY missing; using local backend")
                self._mem0_mode = "local"
                return
            candidates.append({"api_key": api_key})
            base_url = os.getenv("MEM0_BASE_URL", "").strip()
            if base_url:
                candidates.append({"api_key": api_key, "base_url": base_url})
                candidates.append({"api_key": api_key, "host": base_url})
        else:
            base_url = (
                os.getenv("MEM0_SELF_HOSTED_URL", "").strip()
                or os.getenv("MEM0_BASE_URL", "").strip()
            )
            if not base_url:
                logger.warning(
                    "mem0 self-hosted requested but MEM0_SELF_HOSTED_URL missing; using local"
                )
                self._mem0_mode = "local"
                return

            api_key = os.getenv("MEM0_API_KEY", "").strip()
            base_kwargs: dict[str, str] = {"api_key": api_key} if api_key else {}
            candidates.append({**base_kwargs, "base_url": base_url})
            candidates.append({**base_kwargs, "host": base_url})

        for kwargs in candidates:
            try:
                self._mem0_client = MemoryClient(**kwargs)
                logger.info(f"mem0 connected ({mode})")
                return
            except TypeError:
                continue
            except Exception as e:
                logger.warning(f"mem0 init attempt failed ({mode}): {e}")

        logger.warning(f"mem0 {mode} unavailable, using local backend")
        self._mem0_mode = "local"

    @staticmethod
    def _normalize_observation_text(observation: str) -> str:
        return " ".join(part for part in observation.split()).strip()

    @staticmethod
    def _sql_escape(value: Optional[str]) -> str:
        if value is None:
            return ""
        return str(value).replace("'", "''")

    def optimize_observation(
        self,
        observation: str,
        *,
        use_llm: bool = True,
        model: Optional[str] = None,
    ) -> tuple[str, str]:
        cleaned = self._normalize_observation_text(observation)
        if not cleaned:
            return "", "empty"
        if not use_llm:
            return cleaned, "heuristic"

        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            return cleaned, "heuristic"

        try:
            from litellm import completion

            target_model = model or os.getenv(
                "MEMORY_OPTIMIZER_MODEL", "openrouter/openai/gpt-4o-mini"
            )
            response = completion(
                model=target_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Compress operational engineering memories while preserving"
                            " constraints, exceptions, and scope qualifiers."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "Rewrite this memory as one concise sentence. Keep all critical "
                            "details. Return plain text only.\n\n"
                            f"Memory: {cleaned}"
                        ),
                    },
                ],
                temperature=0,
                max_tokens=180,
                api_key=api_key,
            )
            response_obj: Any = response
            choices = getattr(response_obj, "choices", None)
            if choices and len(choices) > 0:
                first_choice = choices[0]
                message = getattr(first_choice, "message", None)
                candidate = getattr(message, "content", "") if message else ""
            else:
                candidate = ""
            optimized = self._normalize_observation_text(candidate or "")
            if optimized:
                return optimized, f"llm:{target_model}"
        except Exception as e:
            logger.warning(f"memory optimization fallback to heuristic: {e}")

        return cleaned, "heuristic"

    def is_suppressed(self, finding_title: str, file_path: str = "") -> bool:
        for sup in self._suppressions.get("suppressions", []):
            if not sup.get("active", True):
                continue

            if sup.get("expires"):
                try:
                    if datetime.fromisoformat(sup["expires"]) < datetime.now():
                        continue
                except ValueError:
                    pass

            pattern = sup.get("pattern", "").lower()
            if pattern and pattern in finding_title.lower():
                file_glob = sup.get("file_glob", "")
                if not file_glob or fnmatch(file_path, file_glob):
                    logger.info(f"Suppressed: '{finding_title}' (rule: {sup['id']})")
                    return True

        return False

    def filter_findings(self, findings: list[dict]) -> tuple[list[dict], int]:
        kept = []
        suppressed_count = 0
        for finding in findings:
            title = finding.get("title", "")
            file_path = finding.get("file", "")
            if self.is_suppressed(title, file_path):
                suppressed_count += 1
            else:
                kept.append(finding)
        return kept, suppressed_count

    def add_suppression(
        self,
        pattern: str,
        reason: str,
        file_glob: str = "",
        added_by: str = "crewai",
        expires: Optional[str] = None,
    ) -> str:
        suppressions = self._suppressions.setdefault("suppressions", [])
        normalized_pattern = pattern.strip().lower()
        normalized_glob = file_glob.strip()
        for existing in suppressions:
            if not existing.get("active", True):
                continue
            existing_pattern = str(existing.get("pattern", "")).strip().lower()
            existing_glob = str(existing.get("file_glob", "")).strip()
            if existing_pattern == normalized_pattern and existing_glob == normalized_glob:
                logger.info(f"Suppression already exists: {existing.get('id', 'unknown')}")
                return str(existing.get("id", ""))

        existing_ids = [s.get("id", "") for s in suppressions]
        next_num = 1
        while f"sup-{next_num:03d}" in existing_ids:
            next_num += 1
        sup_id = f"sup-{next_num:03d}"

        suppressions.append(
            {
                "id": sup_id,
                "pattern": pattern.strip(),
                "file_glob": normalized_glob,
                "reason": reason,
                "added_by": added_by,
                "added_date": datetime.now().strftime("%Y-%m-%d"),
                "expires": expires,
                "active": True,
            }
        )
        self._dirty = True
        logger.info(f"Added suppression {sup_id}: '{pattern}'")

        if self._mem0_client:
            try:
                self._mem0_client.add(
                    f"Suppress finding: {pattern}. Reason: {reason}. Files: {file_glob or 'all'}",
                    user_id="crewai-review",
                    metadata={"type": "suppression", "id": sup_id},
                )
            except Exception as e:
                logger.warning(f"mem0 add failed: {e}")

        return sup_id

    def add_learned_pattern(
        self,
        observation: str,
        source: str = "review",
        confidence: float = 0.8,
    ) -> str:
        normalized_observation = self._normalize_observation_text(observation)
        if not normalized_observation:
            raise ValueError("observation cannot be empty")

        patterns = self._memory.setdefault("learned_patterns", [])
        for existing in patterns:
            if (
                str(existing.get("observation", "")).strip().lower()
                == normalized_observation.lower()
            ):
                existing["confidence"] = max(
                    float(existing.get("confidence", 0.0) or 0.0), confidence
                )
                existing["source"] = source
                existing["learned_date"] = datetime.now().strftime("%Y-%m-%d")
                self._dirty = True
                return str(existing.get("id", ""))

        existing_ids = [p.get("id", "") for p in patterns]
        next_num = 1
        while f"pat-{next_num:03d}" in existing_ids:
            next_num += 1
        pattern_id = f"pat-{next_num:03d}"

        patterns.append(
            {
                "id": pattern_id,
                "observation": normalized_observation,
                "confidence": confidence,
                "source": source,
                "learned_date": datetime.now().strftime("%Y-%m-%d"),
            }
        )
        self._dirty = True

        if self._mem0_client:
            try:
                self._mem0_client.add(
                    f"Learned pattern: {observation} (confidence: {confidence})",
                    user_id="crewai-review",
                    metadata={"type": "learned_pattern", "source": source},
                )
            except Exception as e:
                logger.warning(f"mem0 add failed: {e}")

        return pattern_id

    def list_learned_patterns(self) -> list[dict]:
        patterns = self._memory.get("learned_patterns", [])
        if not isinstance(patterns, list):
            return []
        return [p for p in patterns if isinstance(p, dict)]

    def list_suppressions(self, active_only: bool = False) -> list[dict]:
        suppressions = self._suppressions.get("suppressions", [])
        if not isinstance(suppressions, list):
            return []
        rows = [s for s in suppressions if isinstance(s, dict)]
        if active_only:
            rows = [s for s in rows if s.get("active", True)]
        return rows

    def deactivate_suppression(self, suppression_id: str) -> bool:
        suppression_id = suppression_id.strip()
        if not suppression_id:
            return False
        for suppression in self.list_suppressions(active_only=False):
            if str(suppression.get("id", "")) == suppression_id and suppression.get("active", True):
                suppression["active"] = False
                self._dirty = True
                return True
        return False

    def compact_memory(self, max_trend_entries: int = 50, dry_run: bool = False) -> dict[str, int]:
        changes = {
            "learned_patterns_removed": 0,
            "suppressions_removed": 0,
            "trend_entries_removed": 0,
        }

        patterns = self.list_learned_patterns()
        deduped_patterns: dict[str, dict] = {}
        for row in patterns:
            key = str(row.get("observation", "")).strip().lower()
            if not key:
                changes["learned_patterns_removed"] += 1
                continue
            existing = deduped_patterns.get(key)
            if existing is None:
                deduped_patterns[key] = row
                continue
            existing_conf = float(existing.get("confidence", 0.0) or 0.0)
            row_conf = float(row.get("confidence", 0.0) or 0.0)
            if row_conf >= existing_conf:
                deduped_patterns[key] = row
            changes["learned_patterns_removed"] += 1

        suppressions = self.list_suppressions(active_only=False)
        deduped_suppressions: dict[tuple[str, str, bool], dict] = {}
        for row in suppressions:
            key = (
                str(row.get("pattern", "")).strip().lower(),
                str(row.get("file_glob", "")).strip(),
                bool(row.get("active", True)),
            )
            if not key[0]:
                changes["suppressions_removed"] += 1
                continue
            if key in deduped_suppressions:
                changes["suppressions_removed"] += 1
                continue
            deduped_suppressions[key] = row

        history = self._memory.setdefault("review_history", {})
        trend = history.setdefault("findings_trend", [])
        if not isinstance(trend, list):
            trend = []
        trimmed_trend = trend[-max_trend_entries:] if len(trend) > max_trend_entries else trend
        changes["trend_entries_removed"] = len(trend) - len(trimmed_trend)

        if dry_run:
            return changes

        next_patterns = list(deduped_patterns.values())
        next_suppressions = list(deduped_suppressions.values())
        if (
            len(next_patterns) != len(patterns)
            or len(next_suppressions) != len(suppressions)
            or len(trimmed_trend) != len(trend)
        ):
            self._memory["learned_patterns"] = next_patterns
            self._suppressions["suppressions"] = next_suppressions
            history["findings_trend"] = trimmed_trend
            self._dirty = True

        return changes

    def export_sql_seed(self, output_path: Optional[Path] = None) -> Path:
        target = output_path or MEMORY_SQL_SEED_FILE
        target.parent.mkdir(parents=True, exist_ok=True)

        patterns = sorted(self.list_learned_patterns(), key=lambda row: str(row.get("id", "")))
        suppressions = sorted(
            self.list_suppressions(active_only=False), key=lambda row: str(row.get("id", ""))
        )
        history = self._memory.get("review_history", {})
        trend = history.get("findings_trend", []) if isinstance(history, dict) else []

        lines: list[str] = [
            "-- CrewAI review memory seed (generated)",
            "BEGIN TRANSACTION;",
            "CREATE TABLE IF NOT EXISTS learned_patterns (",
            "  id TEXT PRIMARY KEY,",
            "  observation TEXT NOT NULL,",
            "  confidence REAL NOT NULL,",
            "  source TEXT NOT NULL,",
            "  learned_date TEXT NOT NULL",
            ");",
            "CREATE TABLE IF NOT EXISTS suppressions (",
            "  id TEXT PRIMARY KEY,",
            "  pattern TEXT NOT NULL,",
            "  file_glob TEXT NOT NULL,",
            "  reason TEXT NOT NULL,",
            "  added_by TEXT NOT NULL,",
            "  added_date TEXT NOT NULL,",
            "  expires TEXT NOT NULL,",
            "  active INTEGER NOT NULL",
            ");",
            "CREATE TABLE IF NOT EXISTS review_history (",
            "  id INTEGER PRIMARY KEY CHECK (id = 1),",
            "  total_reviews INTEGER NOT NULL,",
            "  last_review TEXT NOT NULL",
            ");",
            "CREATE TABLE IF NOT EXISTS review_history_trend (",
            "  idx INTEGER PRIMARY KEY,",
            "  pr TEXT NOT NULL,",
            "  findings INTEGER NOT NULL,",
            "  date TEXT NOT NULL",
            ");",
            "DELETE FROM learned_patterns;",
            "DELETE FROM suppressions;",
            "DELETE FROM review_history;",
            "DELETE FROM review_history_trend;",
        ]

        for row in patterns:
            pattern_insert_template = (
                "INSERT INTO learned_patterns (id, observation, confidence, source, learned_date) "
                "VALUES ('{id}', '{observation}', {confidence}, '{source}', '{learned_date}');"
            )
            lines.append(
                pattern_insert_template.format(
                    id=self._sql_escape(str(row.get("id", ""))),
                    observation=self._sql_escape(str(row.get("observation", ""))),
                    confidence=float(row.get("confidence", 0.0) or 0.0),
                    source=self._sql_escape(str(row.get("source", "manual"))),
                    learned_date=self._sql_escape(str(row.get("learned_date", ""))),
                )
            )

        for row in suppressions:
            lines.append(
                "INSERT INTO suppressions (id, pattern, file_glob, reason, added_by, added_date, "
                "expires, active) VALUES ('{id}', '{pattern}', '{file_glob}', '{reason}', "
                "'{added_by}', '{added_date}', '{expires}', {active});".format(
                    id=self._sql_escape(str(row.get("id", ""))),
                    pattern=self._sql_escape(str(row.get("pattern", ""))),
                    file_glob=self._sql_escape(str(row.get("file_glob", ""))),
                    reason=self._sql_escape(str(row.get("reason", ""))),
                    added_by=self._sql_escape(str(row.get("added_by", "crewai"))),
                    added_date=self._sql_escape(str(row.get("added_date", ""))),
                    expires=self._sql_escape(str(row.get("expires", ""))),
                    active=1 if row.get("active", True) else 0,
                )
            )

        total_reviews = 0
        last_review = ""
        if isinstance(history, dict):
            total_reviews = int(history.get("total_reviews", 0) or 0)
            last_review = str(history.get("last_review", "") or "")
        lines.append(
            "INSERT INTO review_history (id, total_reviews, last_review) VALUES "
            f"(1, {total_reviews}, '{self._sql_escape(last_review)}');"
        )

        for idx, row in enumerate(trend, start=1):
            if not isinstance(row, dict):
                continue
            lines.append(
                "INSERT INTO review_history_trend (idx, pr, findings, date) VALUES "
                "({idx}, '{pr}', {findings}, '{date}');".format(
                    idx=idx,
                    pr=self._sql_escape(str(row.get("pr", ""))),
                    findings=int(row.get("findings", 0) or 0),
                    date=self._sql_escape(str(row.get("date", ""))),
                )
            )

        lines.extend(["COMMIT;", ""])
        target.write_text("\n".join(lines), encoding="utf-8")
        return target

    def materialize_sqlite_db(
        self,
        sqlite_path: Path,
        sql_seed_path: Optional[Path] = None,
    ) -> Path:
        seed_path = sql_seed_path or self.export_sql_seed()
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        if sqlite_path.exists():
            sqlite_path.unlink()
        connection = sqlite3.connect(sqlite_path)
        try:
            connection.executescript(seed_path.read_text(encoding="utf-8"))
            connection.commit()
        finally:
            connection.close()
        return sqlite_path

    def backend_status(self) -> dict[str, str]:
        return {
            "mode": self._mem0_mode,
            "mem0_enabled": "true" if self._mem0_client else "false",
            "memory_file": str(MEMORY_FILE),
            "suppressions_file": str(SUPPRESSIONS_FILE),
            "sql_seed_file": str(MEMORY_SQL_SEED_FILE),
        }

    def record_review(self, pr_number: str, findings_count: int) -> None:
        history = self._memory.setdefault("review_history", {})
        history["total_reviews"] = history.get("total_reviews", 0) + 1
        history["last_review"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        trend = history.setdefault("findings_trend", [])
        trend.append(
            {
                "pr": pr_number,
                "findings": findings_count,
                "date": datetime.now().strftime("%Y-%m-%d"),
            }
        )
        if len(trend) > 50:
            trend[:] = trend[-50:]

        self._dirty = True

    def get_context_for_review(self) -> str:
        lines = []

        patterns = self._memory.get("learned_patterns", [])
        if patterns:
            lines.append("## Learned Patterns About This Codebase")
            for p in patterns[-10:]:
                lines.append(f"- {p['observation']} (confidence: {p.get('confidence', 'N/A')})")
            lines.append("")

        suppressions = self._suppressions.get("suppressions", [])
        active = [s for s in suppressions if s.get("active", True)]
        if active:
            lines.append("## Active Review Suppressions")
            lines.append("Do NOT flag these patterns, the team has marked them acceptable:")
            for s in active:
                scope = f" (files: {s['file_glob']})" if s.get("file_glob") else ""
                lines.append(f"- {s['pattern']}{scope} - {s.get('reason', 'no reason given')}")
            lines.append("")

        if self._mem0_client:
            try:
                results = self._mem0_client.search(
                    "codebase patterns and review preferences",
                    user_id="crewai-review",
                    limit=10,
                )
                if results:
                    title = (
                        "## mem0 Self-Hosted Memories"
                        if self._mem0_mode == "self-hosted"
                        else "## mem0 Cloud Memories"
                    )
                    lines.append(title)
                    for mem in results:
                        lines.append(f"- {mem.get('memory', mem.get('text', str(mem)))}")
                    lines.append("")
            except Exception as e:
                logger.warning(f"mem0 search failed: {e}")

        return "\n".join(lines) if lines else ""

    def save(self) -> bool:
        if not self._dirty:
            return False
        _save_json(SUPPRESSIONS_FILE, self._suppressions)
        _save_json(MEMORY_FILE, self._memory)
        self.export_sql_seed()
        logger.info("Memory saved to disk")
        return True


_instance: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    global _instance
    if _instance is None:
        _instance = MemoryManager()
    return _instance
