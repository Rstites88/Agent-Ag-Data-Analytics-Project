"""Commit summarizer tool for handling large commit histories."""

import logging
from typing import Any

from crewai.tools import BaseTool

logger = logging.getLogger(__name__)


class CommitSummarizerTool(BaseTool):
    """Summarize commit history when >10 commits."""

    name: str = "Commit Summarizer Tool"
    description: str = (
        "Summarize a list of commits into key themes and patterns. "
        "Use this when commit history exceeds 10 commits to keep context minimal. "
        "Input: List of commit objects with sha, message, author, date."
    )

    def _run(self, commits: list[dict[str, Any]]) -> dict[str, Any]:
        """Summarize commits into patterns and themes.

        Args:
            commits: List of commit dicts with sha, message, author, date

        Returns:
            Summary with themes, patterns, and key commits
        """
        if not commits:
            return {"total": 0, "summary": "No commits to summarize"}

        logger.info(f"📊 Summarizing {len(commits)} commits")

        # Extract patterns
        commit_types = {}
        authors = set()
        messages = []

        for commit in commits:
            msg = commit.get("message", "").split("\n")[0]  # First line only
            messages.append(msg)

            # Count conventional commit types
            if ":" in msg:
                commit_type = msg.split(":")[0].strip()
                commit_types[commit_type] = commit_types.get(commit_type, 0) + 1

            # Track authors
            author = commit.get("author", {}).get("name", "Unknown")
            authors.add(author)

        # Build summary
        summary = {
            "total": len(commits),
            "commit_types": commit_types,
            "author_count": len(authors),
            "authors": list(authors),
            "first_commit": commits[0].get("message", "").split("\n")[0],
            "last_commit": commits[-1].get("message", "").split("\n")[0],
            "sample_messages": messages[:5],  # First 5 for context
        }

        # Generate human-readable summary
        type_summary = ", ".join(
            [f"{count} {type}" for type, count in sorted(commit_types.items())]
        )
        summary["summary"] = (
            f"{len(commits)} commits by {len(authors)} author(s): {type_summary or 'mixed types'}"
        )

        logger.info(f"✅ Summary: {summary['summary']}")
        return summary
