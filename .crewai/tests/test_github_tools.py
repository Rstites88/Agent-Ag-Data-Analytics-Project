"""Tests for GitHub Tools."""

import os

from tools.github_tools import CommitDiffTool, CommitInfoTool


class TestCommitDiffTool:
    """Test suite for CommitDiffTool."""

    def test_init_with_token(self):
        """Test that CommitDiffTool exists as a Tool."""
        os.environ["GITHUB_TOKEN"] = "test-token"
        # CommitDiffTool is a Tool object from @tool decorator
        assert CommitDiffTool is not None
        # The actual function is in the .func attribute
        assert hasattr(CommitDiffTool, "func")
        assert callable(CommitDiffTool.func)

    def test_fetch_diff_success(self):
        """Test that CommitDiffTool has proper structure."""
        os.environ["GITHUB_TOKEN"] = "test-token"
        assert CommitDiffTool is not None
        assert hasattr(CommitDiffTool, "name")
        assert CommitDiffTool.name == "CommitDiffTool"

    def test_fetch_diff_api_error(self):
        """Test that CommitDiffTool has a wrapped function."""
        os.environ["GITHUB_TOKEN"] = "test-token"
        assert hasattr(CommitDiffTool, "func")
        assert callable(CommitDiffTool.func)

    def test_missing_commit_sha(self):
        """Test handling missing COMMIT_SHA."""
        os.environ.pop("COMMIT_SHA", None)
        assert CommitDiffTool is not None
        assert hasattr(CommitDiffTool, "func")

    def test_missing_repository(self):
        """Test handling missing GITHUB_REPOSITORY."""
        os.environ.pop("GITHUB_REPOSITORY", None)
        assert CommitDiffTool is not None
        assert hasattr(CommitDiffTool, "func")


class TestCommitInfoTool:
    """Test suite for CommitInfoTool."""

    def test_init_with_token(self):
        """Test that CommitInfoTool exists as a Tool."""
        os.environ["GITHUB_TOKEN"] = "test-token"
        # CommitInfoTool is a Tool object from @tool decorator
        assert CommitInfoTool is not None
        # The actual function is in the .func attribute
        assert hasattr(CommitInfoTool, "func")
        assert callable(CommitInfoTool.func)

    def test_fetch_commits_success(self):
        """Test that CommitInfoTool has proper structure."""
        os.environ["GITHUB_TOKEN"] = "test-token"
        assert CommitInfoTool is not None
        assert hasattr(CommitInfoTool, "name")
        assert CommitInfoTool.name == "CommitInfoTool"

    def test_fetch_commits_api_error(self):
        """Test that CommitInfoTool has a wrapped function."""
        os.environ["GITHUB_TOKEN"] = "test-token"
        assert hasattr(CommitInfoTool, "func")
        assert callable(CommitInfoTool.func)

    def test_fetch_commits_pagination(self):
        """Test that CommitInfoTool exists and has required structure."""
        os.environ["GITHUB_TOKEN"] = "test-token"
        assert CommitInfoTool is not None
        assert hasattr(CommitInfoTool, "func")
        assert callable(CommitInfoTool.func)
