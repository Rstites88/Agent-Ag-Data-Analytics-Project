"""Tool to find files related to changed files in commit."""

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Set

from crewai.tools import tool

logger = logging.getLogger(__name__)


def parse_imports(content: str, file_path: str) -> Set[str]:
    """
    Parse import statements from file content.
    Supports: Python, JavaScript/TypeScript, Java, Go, etc.

    Args:
        content: File content
        file_path: Path to file (used to infer language)

    Returns:
        Set of imported module/file paths
    """
    imports = set()
    ext = Path(file_path).suffix.lower()

    if ext in [".py"]:
        # Python imports: from X import Y, import X.Y.Z
        patterns = [
            r"^from\s+([\w.]+)\s+import",
            r"^import\s+([\w.]+)",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                module = match.group(1).split(".")[0]
                imports.add(module)

    elif ext in [".js", ".ts", ".jsx", ".tsx"]:
        # JavaScript/TypeScript imports
        patterns = [
            r"from\s+['\"]([ ^'\"]+)['\"]\s+import",
            r"import\s+.*?\s+from\s+['\"]([ ^'\"]+)['\"]",
            r"require\(['\"]([^'\"]+)['\"]\)",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                module = match.group(1).split("/")[0]
                if not module.startswith("."):
                    imports.add(module)

    elif ext in [".java"]:
        # Java imports
        pattern = r"^import\s+([\w.]+);"
        for match in re.finditer(pattern, content, re.MULTILINE):
            package = match.group(1).split(".")[0]
            imports.add(package)

    elif ext in [".go"]:
        # Go imports
        pattern = r'"([^"]+)"'
        in_imports = False
        for line in content.split("\n"):
            if "import (" in line:
                in_imports = True
            elif in_imports and ")" in line:
                in_imports = False
            elif in_imports:
                for match in re.finditer(pattern, line):
                    imports.add(match.group(1))

    return imports


def find_files_importing(repo_path: str, target_modules: Set[str]) -> List[str]:
    """
    Find files that import from target modules.

    Args:
        repo_path: Path to repository root
        target_modules: Set of modules to search for

    Returns:
        List of file paths
    """
    importing_files = []

    try:
        for root, dirs, files in os.walk(repo_path):
            # Skip common non-code directories
            dirs[:] = [
                d
                for d in dirs
                if d
                not in [
                    ".git",
                    ".crewai",
                    "node_modules",
                    "__pycache__",
                    ".venv",
                    "dist",
                    "build",
                ]
            ]

            for file in files:
                # Only check code files
                if not any(
                    file.endswith(ext)
                    for ext in [
                        ".py",
                        ".js",
                        ".ts",
                        ".tsx",
                        ".jsx",
                        ".java",
                        ".go",
                    ]
                ):
                    continue

                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read(50000)  # Limit read size
                        imports = parse_imports(content, filepath)

                        if imports & target_modules:  # Intersection
                            rel_path = os.path.relpath(filepath, repo_path)
                            importing_files.append(rel_path)
                except Exception as e:
                    logger.warning(f"Error reading {filepath}: {e}")

    except Exception as e:
        logger.error(f"Error scanning repository: {e}")

    return importing_files


@tool
def RelatedFilesTool(changed_files: List[str], repository: str) -> Dict[str, Any]:
    """
    Find files related to changed files based on imports and dependencies.

    Args:
        changed_files: List of file paths changed in commit
        repository: Repository name (owner/repo) or local path

    Returns:
        Dictionary with related files and relationship details
    """
    try:
        # Try to use repository parameter as local path first
        repo_path = repository if os.path.isdir(repository) else os.getcwd()

        related = {
            "changed_files": changed_files,
            "related_files": [],
            "summary": {},
        }

        # Find what changed files import/depend on
        target_modules_from_changes = set()
        for changed_file in changed_files:
            try:
                # Extract module/package name from file path
                parts = Path(changed_file).parts
                if parts:
                    module_name = parts[0].replace(".py", "").replace(".js", "").replace(".ts", "")
                    if not module_name.startswith("."):
                        target_modules_from_changes.add(module_name)
            except Exception as e:
                logger.warning(f"Error parsing {changed_file}: {e}")

        # Find files that import the changed modules
        if target_modules_from_changes:
            importing_files = find_files_importing(repo_path, target_modules_from_changes)

            # Build detailed response
            for rel_file in importing_files:
                if rel_file not in changed_files:
                    related["related_files"].append(
                        {
                            "path": rel_file,
                            "relationship": "imports_changed_module",
                            "relatedness_score": 85,
                            "reason": "Imports from changed modules",
                        }
                    )

            related["summary"] = {
                "total_related_files": len(related["related_files"]),
                "relationship_types": ["imports_changed_module"],
                "requires_additional_testing": (len(related["related_files"]) > 0),
            }

        logger.info(
            f"Found {len(related['related_files'])} related files for "
            f"{len(changed_files)} changed files"
        )
        return related

    except Exception as e:
        logger.error(f"Error finding related files: {e}")
        return {
            "error": str(e),
            "changed_files": changed_files,
            "related_files": [],
        }
