"""Workspace tool for shared context between agents."""

import json
import logging
from pathlib import Path
from typing import Any, Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Maximum file size to read in full (100KB)
MAX_FILE_SIZE = 100 * 1024
# When truncating, include this many bytes from start and end
TRUNCATE_CONTEXT_SIZE = 30 * 1024


class WorkspaceToolInput(BaseModel):
    """Input schema for WorkspaceTool."""

    operation: str = Field(description="Operation to perform: 'read', 'write', or 'exists'")
    filename: str = Field(description="Filename (relative to workspace directory)")
    # Changed from Union[str, dict, list, None] to Any to simplify JSON Schema for Gemini
    # Gemini struggles with complex anyOf schemas and returns MALFORMED_FUNCTION_CALL errors
    content: Any = Field(
        default=None,
        description="Content to write (string, dict, or list). Dicts/lists auto-convert to JSON.",
    )


class WorkspaceTool(BaseTool):
    """Read/write shared workspace to minimize duplicate API calls."""

    name: str = "WorkspaceTool"
    description: str = (
        "Read and write files to shared workspace. "
        "Use this to cache data fetched by other agents and avoid duplicate API calls. "
        "Available operations: read(filename), write(filename, content), exists(filename). "
        "For JSON data, you can pass a dictionary and it will be auto-stringified. "
        "Note: Large files (>100KB) are automatically truncated with context from start and end."
    )
    args_schema: type[BaseModel] = WorkspaceToolInput

    # Pydantic v2 requires fields to be declared
    # Use absolute path to avoid CWD issues when workflow sets working-directory
    workspace_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent / "workspace")
    trace_dir: Optional[Path] = Field(default=None)

    def model_post_init(self, __context: Any) -> None:
        """Initialize workspace directories after Pydantic validation."""
        super().model_post_init(__context)
        # Ensure we're using an absolute path
        self.workspace_dir = self.workspace_dir.resolve()
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.trace_dir = self.workspace_dir / "trace"
        logger.info(f"📁 WorkspaceTool initialized: {self.workspace_dir}")

    def _run(self, operation: str, filename: str, content: Any = None) -> Any:
        """Execute workspace operation.

        Args:
            operation: One of 'read', 'write', 'exists'
            filename: File to operate on (relative to workspace/)
            content: Content to write - can be string, dict, or list.
                    Dicts/lists are auto-converted to JSON strings.

        Returns:
            For 'read': File content as string (truncated if >100KB)
            For 'write': Success message
            For 'exists': Boolean
        """
        if operation == "read":
            return self.read(filename)
        elif operation == "write":
            # Handle None content
            if content is None:
                content = ""

            # Auto-stringify JSON if dict/list is passed
            if isinstance(content, (dict, list)):
                try:
                    content = json.dumps(content, indent=2)
                    logger.info(f"🔄 Auto-stringified JSON for {filename} ({len(content)} bytes)")
                except Exception as e:
                    logger.error(f"❌ Failed to stringify JSON: {e}")
                    return f"Error: Could not stringify JSON - {e}"

            return self.write(filename, str(content))
        elif operation == "exists":
            return self.exists(filename)
        else:
            raise ValueError(f"Unknown operation: {operation}")

    def read(self, filename: str) -> str:
        """Read file from workspace with intelligent size limiting.

        For files larger than MAX_FILE_SIZE (100KB), returns:
        - Summary header with file size and truncation notice
        - First TRUNCATE_CONTEXT_SIZE (30KB) of content
        - Truncation marker
        - Last TRUNCATE_CONTEXT_SIZE (30KB) of content

        This ensures LLM context limits aren't exceeded while still
        providing useful context from both ends of the file.
        """
        filepath = self.workspace_dir / filename
        if not filepath.exists():
            logger.warning(f"⚠️ Workspace file not found: {filepath}")
            return ""

        try:
            file_size = filepath.stat().st_size

            # For small files, read normally
            if file_size <= MAX_FILE_SIZE:
                with open(filepath) as f:
                    content = f.read()
                logger.info(f"📖 Read {len(content)} bytes from {filepath}")
                return content

            # For large files, provide truncated view with context from both ends
            with open(filepath) as f:
                start_content = f.read(TRUNCATE_CONTEXT_SIZE)
                # Seek to near end
                f.seek(max(0, file_size - TRUNCATE_CONTEXT_SIZE))
                end_content = f.read(TRUNCATE_CONTEXT_SIZE)

            truncated_size = len(start_content) + len(end_content)
            truncation_notice = f"""\n\n{"=" * 80}
[FILE TRUNCATED - Too large for LLM context]
Original size: {file_size:,} bytes ({file_size / 1024:.1f} KB)
Showing: First {len(start_content):,} + Last {len(end_content):,} bytes
Omitted: {file_size - truncated_size:,} bytes from middle
{"=" * 80}\n\n"""

            result = start_content + truncation_notice + end_content

            logger.warning(
                f"⚠️ Large file truncated: {filepath} ({file_size:,} bytes -> {len(result):,} bytes)"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Error reading {filepath}: {e}")
            return ""

    def write(self, filename: str, content: str) -> str:
        """Write file to workspace."""
        filepath = self.workspace_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(filepath, "w") as f:
                f.write(content)
            logger.info(f"💾 Wrote {len(content)} bytes to {filepath}")
            return f"Successfully wrote to {filepath}"
        except Exception as e:
            error_msg = f"❌ Error writing to {filepath}: {e}"
            logger.error(error_msg)
            return error_msg

    def exists(self, filename: str) -> bool:
        """Check if file exists in workspace."""
        filepath = self.workspace_dir / filename
        exists = filepath.exists()
        logger.info(f"🔍 Check {filepath}: {'EXISTS' if exists else 'NOT FOUND'}")
        return exists

    def read_json(self, filename: str) -> dict:
        """Read JSON file from workspace."""
        content = self.read(filename)
        if not content:
            return {}
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parsing JSON from {filename}: {e}")
            return {}

    def write_json(self, filename: str, data: dict) -> str:
        """Write JSON file to workspace."""
        try:
            content = json.dumps(data, indent=2)
            return self.write(filename, content)
        except Exception as e:
            error_msg = f"❌ Error serializing JSON to {filename}: {e}"
            logger.error(error_msg)
            return error_msg
