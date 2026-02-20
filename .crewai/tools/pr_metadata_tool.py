"""PR metadata tool that parses GitHub event data."""

import json
import logging
import os
from typing import Any

from crewai.tools import BaseTool

logger = logging.getLogger(__name__)


class PRMetadataTool(BaseTool):
    """Parse PR metadata from GITHUB_EVENT_PATH (no API call)."""

    name: str = "PR Metadata Tool"
    description: str = (
        "Parse PR metadata from GitHub Actions environment. "
        "Returns: labels, files_changed, additions, deletions, draft status, commit_sha. "
        "No API calls needed - reads from GITHUB_EVENT_PATH."
    )

    def _run(self) -> dict[str, Any]:
        """Parse GitHub event JSON for PR metadata.

        Returns:
            Dict with PR metadata: labels, files_changed, additions, deletions, commit_sha
        """
        event_path = os.getenv("GITHUB_EVENT_PATH")
        commit_sha = os.getenv("COMMIT_SHA", "")

        if not event_path:
            logger.warning("GITHUB_EVENT_PATH not set - not running in GitHub Actions")
            return self._mock_metadata()

        try:
            with open(event_path) as f:
                event = json.load(f)

            pr = event.get("pull_request", {})

            metadata = {
                "labels": [label["name"] for label in pr.get("labels", [])],
                "files_changed": pr.get("changed_files", 0),
                "additions": pr.get("additions", 0),
                "deletions": pr.get("deletions", 0),
                "draft": pr.get("draft", False),
                "pr_number": pr.get("number"),
                "title": pr.get("title", ""),
                "base_ref": pr.get("base", {}).get("ref", "main"),
                "head_ref": pr.get("head", {}).get("ref", ""),
                "commit_sha": commit_sha,  # Add commit SHA from environment
            }

            logger.info(
                f"📋 PR Metadata: {metadata['files_changed']} files, "
                f"+{metadata['additions']}/-{metadata['deletions']}, "
                f"labels: {metadata['labels']}, commit: {commit_sha[:7] if commit_sha else 'N/A'}"
            )

            return metadata

        except Exception as e:
            logger.error(f"Error parsing GitHub event: {e}")
            return self._mock_metadata()

    def _mock_metadata(self) -> dict[str, Any]:
        """Return mock metadata for local testing."""
        logger.info("Using mock PR metadata for local testing")
        return {
            "labels": [],
            "files_changed": 5,
            "additions": 100,
            "deletions": 20,
            "draft": False,
            "pr_number": 999,
            "title": "Test PR",
            "base_ref": "main",
            "head_ref": "test-branch",
            "commit_sha": "mock-sha-1234567",
        }
