"""
Diff parsing helpers for quick code review crews.

This module provides a small, self-contained set of utilities that can be
used by higher-level agents (like the Diff Intelligence Specialist) to turn
raw git-style unified diffs into structured summaries, and to apply an
adaptive reading strategy based on diff size and risk.

The goal is to keep all heavy parsing and sampling logic in one place so
agents can work from focused, token-efficient context instead of loading an
entire diff into the model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

# Heuristic keywords for identifying higher-risk files.
RISKY_PATH_KEYWORDS: Tuple[str, ...] = (
    "auth",
    "login",
    "signup",
    "user",
    "payment",
    "billing",
    "checkout",
    "transaction",
    "order",
    "invoice",
    "config",
    "settings",
    "env",
    "secret",
    "token",
    "key",
    "crypto",
    "hash",
    "password",
    "database",
    "db",
    "schema",
)


@dataclass
class FileSummary:
    """Lightweight summary of changes for a single file in a diff."""

    path: str
    additions: int = 0
    deletions: int = 0

    @property
    def total_changes(self) -> int:
        return self.additions + self.deletions

    @property
    def is_test(self) -> bool:
        lowered = self.path.lower()
        return "test" in lowered or "/tests/" in lowered or lowered.endswith("_test.py")

    @property
    def is_config(self) -> bool:
        lowered = self.path.lower()
        return any(
            lowered.endswith(ext) for ext in (".yml", ".yaml", ".json", ".toml", ".ini", ".env")
        ) or any(part in ("config", "settings") for part in lowered.split("/"))

    @property
    def risk_score(self) -> int:
        """Simple risk score based on path heuristics and size."""
        score = 0
        lowered = self.path.lower()

        if any(keyword in lowered for keyword in RISKY_PATH_KEYWORDS):
            score += 3

        if self.is_config:
            score += 2

        if self.total_changes >= 200:
            score += 3
        elif self.total_changes >= 50:
            score += 1

        if self.is_test:
            score -= 2

        return max(score, 0)


def _iter_unified_diff_lines(diff_text: str) -> Iterable[str]:
    """Yield non-empty lines from a unified diff."""
    for raw in diff_text.splitlines():
        line = raw.rstrip("\n")
        if not line:
            continue
        yield line


def summarize_diff(diff_text: str) -> Dict[str, FileSummary]:
    """Produce a per-file summary from a unified diff string."""
    summaries: Dict[str, FileSummary] = {}
    current_path: str | None = None

    for line in _iter_unified_diff_lines(diff_text):
        if line.startswith("+++ b/"):
            current_path = line[6:]
            summaries.setdefault(current_path, FileSummary(path=current_path))
            continue

        if current_path is None:
            continue

        if line.startswith("+++") or line.startswith("---"):
            continue

        if line.startswith("+"):
            summaries[current_path].additions += 1
        elif line.startswith("-"):
            summaries[current_path].deletions += 1

    return summaries


def total_changed_lines(diff_text: str) -> int:
    """Return a coarse count of changed lines (+/-) in the diff."""
    count = 0
    for line in _iter_unified_diff_lines(diff_text):
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+") or line.startswith("-"):
            count += 1
    return count


def extract_intent_keywords(commit_messages: str, max_keywords: int = 8) -> List[str]:
    """Extract simple intent keywords from commit messages."""
    stopwords = {
        "the",
        "and",
        "for",
        "this",
        "that",
        "into",
        "with",
        "from",
        "add",
        "adds",
        "fix",
        "update",
        "refactor",
        "improve",
        "change",
        "changes",
        "wip",
    }

    tokens: List[str] = []
    for raw in commit_messages.replace("\n", " ").split(" "):
        word = raw.strip().lower().strip(",.()[]:{}")
        if not word or len(word) < 4:
            continue
        if word in stopwords:
            continue
        if word not in tokens:
            tokens.append(word)
        if len(tokens) >= max_keywords:
            break

    return tokens


def identify_critical_paths(summaries: Dict[str, FileSummary], max_files: int = 12) -> List[str]:
    """Return a list of high-risk files based on heuristic risk score."""
    ranked = sorted(summaries.values(), key=lambda f: f.risk_score, reverse=True)
    return [f.path for f in ranked if f.risk_score > 0][:max_files]


def smart_diff_sample(
    diff_text: str,
    commit_messages: str,
    small_threshold: int = 100,
    medium_threshold: int = 500,
) -> str:
    """Apply an adaptive diff sampling strategy.

    - If total changes < small_threshold: return the full diff.
    - If total changes < medium_threshold: keep only hunks from files whose
      paths contain commit-intent keywords.
    - Otherwise: keep only hunks from high-risk files.
    """
    diff_size = total_changed_lines(diff_text)
    if diff_size < small_threshold:
        return diff_text

    summaries = summarize_diff(diff_text)

    if diff_size < medium_threshold:
        keywords = set(extract_intent_keywords(commit_messages))
        target_paths = {path for path in summaries if any(kw in path.lower() for kw in keywords)}
    else:
        target_paths = set(identify_critical_paths(summaries))

    if not target_paths:
        lines = diff_text.splitlines()
        return "\n".join(lines[: medium_threshold * 2])

    filtered_lines: List[str] = []
    current_path: str | None = None
    include_current_file = False

    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current_path = line[6:]
            include_current_file = current_path in target_paths
            if include_current_file:
                filtered_lines.append(line)
            continue

        if current_path is None:
            if (
                line.startswith("diff --git")
                or line.startswith("index ")
                or line.startswith("--- a/")
            ):
                filtered_lines.append(line)
            continue

        if not include_current_file:
            continue

        filtered_lines.append(line)

    return "\n".join(filtered_lines)
