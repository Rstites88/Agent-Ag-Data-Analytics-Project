"""Tests for CI Output Parser Tool."""

import os

from tools.ci_output_parser_tool import CIOutputParserTool


class TestCIOutputParserTool:
    """Test suite for CIOutputParserTool."""

    def test_parse_success_result(self):
        """Test parsing successful CI output."""
        os.environ["COMMIT_SHA"] = "abc123"
        tool = CIOutputParserTool()
        result = tool._run("success")

        # Result is a dict with status field
        assert isinstance(result, dict)
        assert result["status"] == "success"
        assert result["passed"] is True

    def test_parse_failure_result(self):
        """Test parsing failed CI output."""
        os.environ["COMMIT_SHA"] = "abc123"
        tool = CIOutputParserTool()
        result = tool._run("failure")

        # Result is a dict
        assert isinstance(result, dict)
        assert result["status"] == "failure"
        assert result["passed"] is False

    def test_parse_missing_env_var(self):
        """Test handling missing COMMIT_SHA."""
        # Remove COMMIT_SHA if it exists
        os.environ.pop("COMMIT_SHA", None)
        tool = CIOutputParserTool()
        result = tool._run("success")

        # Should still return something, even without COMMIT_SHA
        assert result is not None

    def test_output_includes_context(self):
        """Test that output includes useful context."""
        os.environ["COMMIT_SHA"] = "abc123"
        tool = CIOutputParserTool()
        result = tool._run("success")

        # Result is a dict with multiple fields
        assert isinstance(result, dict)
        assert len(result) > 2  # Should have multiple keys
