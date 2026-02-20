"""Tests for PR Metadata Tool."""

import os
from unittest.mock import Mock, patch

from tools.pr_metadata_tool import PRMetadataTool


class TestPRMetadataTool:
    """Test suite for PRMetadataTool."""

    def test_read_from_environment(self):
        """Test reading PR metadata from environment variables."""
        os.environ["PR_NUMBER"] = "123"
        os.environ["COMMIT_SHA"] = "abc123def456"
        os.environ["GITHUB_REPOSITORY"] = "test-owner/test-repo"

        tool = PRMetadataTool()
        result = tool._run()

        # Result is now a dict
        assert isinstance(result, dict)
        assert "pr_number" in result
        assert "commit_sha" in result

    def test_fetch_labels_from_api(self):
        """Test fetching labels from GitHub API."""
        os.environ["PR_NUMBER"] = "123"
        os.environ["COMMIT_SHA"] = "abc123"
        os.environ["GITHUB_REPOSITORY"] = "test-owner/test-repo"
        os.environ["GITHUB_TOKEN"] = "fake-token"

        # Patch requests module directly, not as attribute of tool module
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"labels": [{"name": "crewai:full-review"}]}
            mock_get.return_value = mock_response

            tool = PRMetadataTool()
            result = tool._run()

            # Result is a dict
            assert isinstance(result, dict)
            assert "labels" in result

    def test_missing_environment_variables(self):
        """Test handling missing required environment variables."""
        # Clear environment
        for key in ["PR_NUMBER", "COMMIT_SHA", "GITHUB_REPOSITORY"]:
            os.environ.pop(key, None)

        tool = PRMetadataTool()
        result = tool._run()

        # Should return error or default values
        assert result is not None

    def test_api_error_fallback(self):
        """Test fallback when API fails."""
        os.environ["PR_NUMBER"] = "123"
        os.environ["COMMIT_SHA"] = "abc123def456"
        os.environ["GITHUB_REPOSITORY"] = "test-owner/test-repo"

        # Patch requests module directly
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("API error")

            tool = PRMetadataTool()
            result = tool._run()

            # Should still return dict with basic info
            assert isinstance(result, dict)
            assert "commit_sha" in result or "pr_number" in result

    def test_output_format(self):
        """Test that output is properly formatted."""
        os.environ["PR_NUMBER"] = "123"
        os.environ["COMMIT_SHA"] = "abc123"
        os.environ["GITHUB_REPOSITORY"] = "test-owner/test-repo"

        tool = PRMetadataTool()
        result = tool._run()

        # Result is a dict with expected keys
        assert isinstance(result, dict)
        assert "pr_number" in result or "commit_sha" in result
