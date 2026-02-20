"""Pytest configuration and shared fixtures."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    env_vars = {
        "PR_NUMBER": "123",
        "COMMIT_SHA": "abc123def456",
        "GITHUB_REPOSITORY": "test-owner/test-repo",
        "CORE_CI_RESULT": "success",
        "GITHUB_TOKEN": "fake_token_12345",
        "OPENROUTER_API_KEY": "fake_openrouter_key",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def mock_github_api():
    """Mock GitHub API responses."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "sha": "abc123def456",
        "files": [
            {"filename": "src/app.py", "status": "modified", "additions": 10, "deletions": 5},
            {"filename": "README.md", "status": "modified", "additions": 2, "deletions": 1},
        ],
        "stats": {"additions": 12, "deletions": 6, "total": 18},
    }

    with patch("requests.get", return_value=mock_response):
        yield mock_response


@pytest.fixture
def sample_diff():
    """Sample git diff output."""
    return {
        "sha": "abc123def456",
        "files": [
            {
                "filename": "src/app.py",
                "status": "modified",
                "additions": 10,
                "deletions": 5,
                "patch": """@@ -1,5 +1,10 @@
 import os
+import sys

 def main():
-    print('Hello')
+    print('Hello, World!')
+    return 0
""",
            },
            {
                "filename": "README.md",
                "status": "modified",
                "additions": 2,
                "deletions": 1,
                "patch": """@@ -1,3 +1,4 @@
 # Test Project
+
 This is a test.
""",
            },
        ],
        "stats": {"additions": 12, "deletions": 6, "total": 18},
    }


@pytest.fixture
def sample_commits():
    """Sample commit history."""
    return [
        {
            "sha": "abc123",
            "commit": {
                "message": "feat: add new feature",
                "author": {"name": "Test User", "email": "test@example.com"},
            },
        },
        {
            "sha": "def456",
            "commit": {
                "message": "fix: resolve bug",
                "author": {"name": "Test User", "email": "test@example.com"},
            },
        },
    ]


@pytest.fixture
def sample_pr_metadata():
    """Sample PR metadata."""
    return {
        "commit_sha": "abc123def456",
        "repository": "test-owner/test-repo",
        "pr_number": 123,
        "labels": ["crewai:full-review", "enhancement"],
        "files_changed": 15,
        "lines_added": 200,
        "lines_removed": 50,
    }


@pytest.fixture
def sample_ci_output():
    """Sample CI output."""
    return {
        "status": "success",
        "jobs": [
            {"name": "format-and-lint", "conclusion": "success"},
            {"name": "link-check", "conclusion": "success"},
        ],
    }
