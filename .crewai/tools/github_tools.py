"""Local Git tools for CrewAI code review.

These tools work with the locally checked-out repository instead of making
GitHub API calls. Since GitHub Actions already checks out the repo with
actions/checkout@v4, we can use git commands directly.

All output goes to GitHub Actions summary (GITHUB_STEP_SUMMARY) - no PR comments.
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict

from crewai.tools import tool

logger = logging.getLogger(__name__)


def run_git_command(args: list[str], cwd: str = None) -> tuple[str, str, int]:
    """Run a git command and return stdout, stderr, returncode.

    Args:
        args: Git command arguments (e.g., ['show', 'HEAD'])
        cwd: Working directory (defaults to repo root)

    Returns:
        Tuple of (stdout, stderr, returncode)
    """
    if cwd is None:
        # Default to repository root (GitHub Actions sets GITHUB_WORKSPACE)
        cwd = os.getenv("GITHUB_WORKSPACE", ".")

    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        logger.error(f"Git command timed out: git {' '.join(args)}")
        return "", "Command timed out", 1
    except Exception as e:
        logger.error(f"Git command failed: {e}")
        return "", str(e), 1


@tool
def CommitDiffTool(commit_sha: str, repository: str) -> Dict[str, Any]:
    """
    Get the diff for a specific commit using local git commands.

    Args:
        commit_sha: The commit SHA to get diff for
        repository: Repository name in format 'owner/repo' (used for context only)

    Returns:
        Dictionary with diff content, file stats, and added/removed lines
    """
    try:
        # Get commit message and author
        msg_out, msg_err, msg_code = run_git_command(["log", "-1", "--format=%s%n%an", commit_sha])

        if msg_code != 0:
            logger.error(f"Failed to get commit info: {msg_err}")
            return {
                "error": f"Commit not found: {commit_sha}",
                "commit_sha": commit_sha,
            }

        lines = msg_out.strip().split("\n")
        commit_message = lines[0] if lines else "Unknown"
        author_name = lines[1] if len(lines) > 1 else "Unknown"

        # Get commit stats (files changed, insertions, deletions)
        stat_out, stat_err, stat_code = run_git_command(["show", "--stat", "--format=", commit_sha])

        if stat_code != 0:
            logger.error(f"Failed to get commit stats: {stat_err}")
            return {
                "error": f"Failed to get stats for {commit_sha}",
                "commit_sha": commit_sha,
            }

        # Parse stats from last line (e.g., "5 files changed, 100 insertions(+), 20 deletions(-)")
        total_additions = 0
        total_deletions = 0
        files_changed = 0

        if stat_out:
            summary_line = stat_out.strip().split("\n")[-1]
            if "file" in summary_line and "changed" in summary_line:
                parts = summary_line.split(",")
                for part in parts:
                    part = part.strip()
                    if "insertion" in part:
                        total_additions = int(part.split()[0])
                    elif "deletion" in part:
                        total_deletions = int(part.split()[0])
                files_changed = int(summary_line.split()[0])

        # Get full diff
        diff_out, diff_err, diff_code = run_git_command(["show", "--format=", commit_sha])

        if diff_code != 0:
            logger.error(f"Failed to get diff: {diff_err}")
            diff_content = "(diff unavailable)"
        else:
            diff_content = diff_out

        # Get list of changed files with per-file stats
        files_out, files_err, files_code = run_git_command(
            ["diff-tree", "--no-commit-id", "--numstat", "-r", commit_sha]
        )

        files_list = []
        if files_code == 0 and files_out:
            for line in files_out.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) >= 3:
                    additions = parts[0]
                    deletions = parts[1]
                    filename = parts[2]

                    # Handle binary files (show "-" for additions/deletions)
                    try:
                        add_count = int(additions) if additions != "-" else 0
                        del_count = int(deletions) if deletions != "-" else 0
                    except ValueError:
                        add_count = 0
                        del_count = 0

                    files_list.append(
                        {
                            "filename": filename,
                            "additions": add_count,
                            "deletions": del_count,
                            "changes": add_count + del_count,
                            "status": "modified",  # Git diff-tree doesn't show status explicitly
                        }
                    )

        result = {
            "commit_sha": commit_sha[:8],
            "message": commit_message,
            "author": author_name,
            "files": files_list,
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "total_changes": total_additions + total_deletions,
            "diff_content": diff_content,
        }

        logger.info(
            f"✅ Retrieved diff for {commit_sha[:8]}: "
            f"{files_changed} files, +{total_additions}/-{total_deletions}"
        )
        return result

    except Exception as e:
        logger.error(f"❌ CommitDiffTool error: {e}", exc_info=True)
        return {
            "error": str(e),
            "commit_sha": commit_sha,
        }


@tool
def CommitInfoTool(commit_sha: str, repository: str) -> Dict[str, Any]:
    """
    Get detailed commit information using local git commands.

    Args:
        commit_sha: The commit SHA
        repository: Repository name in format 'owner/repo' (used for context only)

    Returns:
        Commit metadata: message, author, date, stats
    """
    try:
        # Get commit info using git log with custom format
        log_out, log_err, log_code = run_git_command(
            ["log", "-1", "--format=%H%n%s%n%an%n%ae%n%aI", commit_sha]
        )

        if log_code != 0:
            logger.error(f"Failed to get commit info: {log_err}")
            return {"error": f"Commit not found: {commit_sha}"}

        lines = log_out.strip().split("\n")
        full_sha = lines[0] if lines else commit_sha
        message = lines[1] if len(lines) > 1 else "Unknown"
        author_name = lines[2] if len(lines) > 2 else "Unknown"
        author_email = lines[3] if len(lines) > 3 else "unknown@example.com"
        author_date = lines[4] if len(lines) > 4 else ""

        # Get commit stats
        stat_out, stat_err, stat_code = run_git_command(["show", "--stat", "--format=", commit_sha])

        total_additions = 0
        total_deletions = 0
        files_changed = 0

        if stat_code == 0 and stat_out:
            summary_line = stat_out.strip().split("\n")[-1]
            if "file" in summary_line and "changed" in summary_line:
                parts = summary_line.split(",")
                for part in parts:
                    part = part.strip()
                    if "insertion" in part:
                        total_additions = int(part.split()[0])
                    elif "deletion" in part:
                        total_deletions = int(part.split()[0])
                files_changed = int(summary_line.split()[0])

        result = {
            "sha": full_sha[:8],
            "message": message,
            "author": {
                "name": author_name,
                "email": author_email,
                "date": author_date,
            },
            "stats": {
                "additions": total_additions,
                "deletions": total_deletions,
                "total_changes": total_additions + total_deletions,
            },
            "files_changed": files_changed,
        }

        logger.info(
            f"✅ Retrieved commit info for {commit_sha[:8]}: "
            f"{files_changed} files, {total_additions + total_deletions} changes"
        )
        return result

    except Exception as e:
        logger.error(f"❌ CommitInfoTool error: {e}", exc_info=True)
        return {"error": str(e)}


@tool
def FileContentTool(file_path: str, repository: str, ref: str = "HEAD") -> Dict[str, Any]:
    """
    Read file content from local repository.

    Args:
        file_path: Path to file in repository
        repository: Repository name in format 'owner/repo' (used for context only)
        ref: Git ref (branch, tag, commit SHA) - defaults to HEAD

    Returns:
        File content and metadata
    """
    try:
        # Get repository root
        repo_root = os.getenv("GITHUB_WORKSPACE", ".")
        full_path = Path(repo_root) / file_path

        # Try to read file at specific ref using git show
        if ref != "HEAD":
            show_out, show_err, show_code = run_git_command(["show", f"{ref}:{file_path}"])

            if show_code == 0:
                content = show_out
            else:
                logger.error(f"File not found at ref {ref}: {show_err}")
                return {
                    "error": f"File not found: {file_path} at ref {ref}",
                    "path": file_path,
                }
        else:
            # Read from filesystem (current checkout)
            if not full_path.exists():
                return {
                    "error": f"File not found: {file_path}",
                    "path": file_path,
                }

            try:
                content = full_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                # Binary file
                return {
                    "error": f"Binary file: {file_path}",
                    "path": file_path,
                    "is_binary": True,
                }

        # Get file hash
        hash_out, hash_err, hash_code = run_git_command(["hash-object", file_path])
        file_hash = hash_out.strip()[:8] if hash_code == 0 else "unknown"

        result = {
            "path": file_path,
            "content": content,
            "size": len(content),
            "sha": file_hash,
        }

        logger.info(f"✅ Read file {file_path}: {len(content)} bytes")
        return result

    except Exception as e:
        logger.error(f"❌ FileContentTool error: {e}", exc_info=True)
        return {"error": str(e), "path": file_path}
