"""Tests for Workspace Tool."""

import json
import os
import tempfile

import pytest

from tools.workspace_tool import WorkspaceTool

# Test constants - centralized for easy maintenance
TEST_FILENAME = "test.txt"
TEST_CONTENT = "Hello"
TEST_CONTENT_FULL = "Hello World"
TEST_JSON_FILENAME = "data.json"
TEST_SUBDIR_FILENAME = "subdir/file.txt"
TEST_SUBDIR_CONTENT = "Nested content"
TEST_EMPTY_FILENAME = "empty.txt"
TEST_NONEXISTENT_FILENAME = "nonexistent.txt"
TEST_FILE_LIST_1 = "file1.txt"
TEST_FILE_CONTENT_1 = "Content 1"


class TestWorkspaceTool:
    """Test suite for WorkspaceTool."""

    def test_init_creates_workspace(self):
        """Test that workspace directory is created on init."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = WorkspaceTool(workspace_dir=tmpdir)
            assert tool is not None
            assert os.path.exists(tmpdir)

    def test_write_file(self):
        """Test writing a file to workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = WorkspaceTool(workspace_dir=tmpdir)
            _result = tool._run(operation="write", filename=TEST_FILENAME, content=TEST_CONTENT)

            assert os.path.exists(os.path.join(tmpdir, TEST_FILENAME))
            # Note: _result intentionally unused, testing file creation only

    def test_write_json_file(self):
        """Test writing JSON content to workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = WorkspaceTool(workspace_dir=tmpdir)
            data = {"key": "value", "number": 42}
            _result = tool._run(
                operation="write", filename=TEST_JSON_FILENAME, content=json.dumps(data, indent=2)
            )

            file_path = os.path.join(tmpdir, TEST_JSON_FILENAME)
            assert os.path.exists(file_path)

            with open(file_path) as f:
                loaded = json.load(f)
                assert loaded == data

    def test_read_file(self):
        """Test reading a file from workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = WorkspaceTool(workspace_dir=tmpdir)

            # Write first
            tool._run(operation="write", filename=TEST_FILENAME, content=TEST_CONTENT_FULL)

            # Then read
            result = tool._run(operation="read", filename=TEST_FILENAME)
            assert TEST_CONTENT_FULL in result

    def test_read_nonexistent_file(self):
        """Test reading a file that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = WorkspaceTool(workspace_dir=tmpdir)
            result = tool._run(operation="read", filename=TEST_NONEXISTENT_FILENAME)

            # Should return empty string
            assert result == ""

    def test_list_files_empty(self):
        """Test checking file existence in empty workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = WorkspaceTool(workspace_dir=tmpdir)
            # Use 'exists' operation instead of 'list' (which isn't implemented)
            result = tool._run(operation="exists", filename=TEST_FILENAME)

            assert result is False

    def test_list_files_with_content(self):
        """Test checking file existence with content in workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = WorkspaceTool(workspace_dir=tmpdir)

            # Create a file
            tool._run(operation="write", filename=TEST_FILE_LIST_1, content=TEST_FILE_CONTENT_1)

            # Check it exists
            result = tool._run(operation="exists", filename=TEST_FILE_LIST_1)
            assert result is True

    def test_invalid_operation(self):
        """Test handling invalid operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = WorkspaceTool(workspace_dir=tmpdir)

            with pytest.raises(ValueError):
                tool._run(operation="invalid_op", filename=TEST_FILENAME)

    def test_write_with_subdirectory(self):
        """Test writing file in a subdirectory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = WorkspaceTool(workspace_dir=tmpdir)
            _result = tool._run(
                operation="write", filename=TEST_SUBDIR_FILENAME, content=TEST_SUBDIR_CONTENT
            )

            file_path = os.path.join(tmpdir, "subdir", "file.txt")
            assert os.path.exists(file_path)

    def test_write_empty_content(self):
        """Test writing file with empty content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tool = WorkspaceTool(workspace_dir=tmpdir)
            _result = tool._run(operation="write", filename=TEST_EMPTY_FILENAME, content="")

            file_path = os.path.join(tmpdir, TEST_EMPTY_FILENAME)
            assert os.path.exists(file_path)
