"""Tools for analyzing CI/CD job results with intelligent log handling."""

import json
import re
from pathlib import Path
from typing import Optional

from crewai.tools import tool

WORKSPACE_DIR = Path(__file__).parent.parent / "workspace"
CI_RESULTS_DIR = WORKSPACE_DIR / "ci_results"

# Log size thresholds (in KB)
SMALL_LOG_THRESHOLD = 50  # < 50KB = small, read fully
MEDIUM_LOG_THRESHOLD = 200  # < 200KB = medium, use caution
# > 200KB = large, must grep/search


@tool("Read CI Job Index")
def read_job_index() -> str:
    """
    Read the index of all CI jobs that ran before CrewAI review.

    Returns a summary with job names, statuses, and log sizes.
    Use this FIRST to understand which jobs ran and their outcomes.
    """
    index_file = CI_RESULTS_DIR / "_job_index.json"
    if not index_file.exists():
        return "❌ No CI job index found. CI data may not have been collected."

    with open(index_file) as f:
        data = json.load(f)

    result = "# CI Job Index\n\n"
    result += (
        f"**Workflow Run:** {data.get('run_id', 'N/A')} (#{data.get('run_number', 'N/A')})\n\n"
    )
    result += f"## Jobs ({len(data['jobs'])} completed)\n\n"

    for job in data["jobs"]:
        conclusion = job.get("conclusion", "unknown")
        status_emoji = "✅" if conclusion == "success" else "❌" if conclusion == "failure" else "⚠️"

        log_size_kb = job.get("log_size_bytes", 0) / 1024
        if log_size_kb < SMALL_LOG_THRESHOLD:
            size_note = f"{log_size_kb:.1f}KB (small - safe to read)"
        elif log_size_kb < MEDIUM_LOG_THRESHOLD:
            size_note = f"{log_size_kb:.1f}KB (medium - read with caution)"
        else:
            size_note = f"{log_size_kb:.1f}KB (LARGE - use grep/search)"

        result += f"{status_emoji} **{job['job_name']}** ({conclusion})\n"
        result += f"   - Folder: `{job['job_folder']}`\n"
        result += f"   - Log size: {size_note}\n"
        result += f"   - Timestamp: {job.get('timestamp', 'N/A')}\n\n"

    return result


@tool("Check Log Size")
def check_log_size(folder_name: str) -> str:
    """
    Check the size of a job's log before reading it.

    Args:
        folder_name: The folder name from the job index (e.g., "core-ci")

    Returns: Log size and recommendation on how to read it.

    Use this before reading large logs to decide if you need to grep/search instead.
    """
    log_file = CI_RESULTS_DIR / folder_name / "log.txt"

    if not log_file.exists():
        return f"❌ No log found for job '{folder_name}'"

    size_bytes = log_file.stat().st_size
    size_kb = size_bytes / 1024
    size_mb = size_kb / 1024

    lines = sum(1 for _ in open(log_file))

    result = f"# Log Size for {folder_name}\n\n"
    result += f"**Size:** {size_bytes:,} bytes ({size_kb:.1f}KB / {size_mb:.2f}MB)\n"
    result += f"**Lines:** {lines:,}\n\n"

    if size_kb < SMALL_LOG_THRESHOLD:
        result += "✅ **Recommendation:** SAFE TO READ FULLY\n"
        result += "This log is small enough to read completely using `read_full_log`."
    elif size_kb < MEDIUM_LOG_THRESHOLD:
        result += "⚠️ **Recommendation:** READ WITH CAUTION\n"
        result += (
            "Consider reading the summary first, then use `search_log` to find specific errors."
        )
    else:
        result += "🚨 **Recommendation:** DO NOT READ FULLY\n"
        result += (
            f"This log is too large ({size_mb:.2f}MB). "
            "Use `search_log` to find specific patterns.\n"
        )
        result += "Common searches: 'error', 'failed', 'FAILED', 'exception', 'traceback'"

    return result


@tool("Read Job Summary")
def read_job_summary(folder_name: str) -> str:
    """
    Read the GitHub Actions summary for a specific job.

    Args:
        folder_name: The folder name from the job index (e.g., "core-ci")

    Returns: The job's summary showing step-by-step results.

    ALWAYS read summaries before logs. Summaries tell you WHAT failed.
    """
    summary_file = CI_RESULTS_DIR / folder_name / "summary.md"

    if not summary_file.exists():
        return f"❌ No summary found for job '{folder_name}'"

    with open(summary_file) as f:
        return f.read()


@tool("Search Log for Pattern")
def search_log(
    folder_name: str, pattern: str, context_lines: int = 3, max_matches: int = 50
) -> str:
    """
    Search a job's log for a specific pattern (case-insensitive grep).

    Args:
        folder_name: The folder name from the job index
        pattern: Search pattern (regex supported)
        context_lines: Number of lines before/after match to include (default: 3)
        max_matches: Maximum number of matches to return (default: 50)

    Returns: Matching lines with context.

    Use this for LARGE logs instead of reading the entire file.
    Good patterns: "error", "failed", "exception", "FAIL", specific test names
    """
    log_file = CI_RESULTS_DIR / folder_name / "log.txt"

    if not log_file.exists():
        return f"❌ No log found for job '{folder_name}'"

    try:
        pattern_re = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        return f"❌ Invalid regex pattern: {e}"

    matches = []
    with open(log_file) as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if pattern_re.search(line):
            start = max(0, i - context_lines)
            end = min(len(lines), i + context_lines + 1)

            context = {
                "line_number": i + 1,
                "match": line.strip(),
                "context": "".join(lines[start:end]),
            }
            matches.append(context)

            if len(matches) >= max_matches:
                break

    if not matches:
        return f"No matches found for pattern '{pattern}' in {folder_name} log"

    result = f"# Search Results for '{pattern}' in {folder_name}\n\n"
    result += f"**Found {len(matches)} matches** (showing up to {max_matches})\n\n"

    for i, match in enumerate(matches, 1):
        result += f"## Match {i} (Line {match['line_number']})\n"
        result += f"```\n{match['context']}```\n\n"

    if len(matches) == max_matches:
        result += f"\n⚠️ Reached maximum of {max_matches} matches. Pattern may occur more times.\n"

    return result


@tool("Read Full Log")
def read_full_log(folder_name: str, max_lines: Optional[int] = None) -> str:
    """
    Read the complete log output for a specific job.

    Args:
        folder_name: The folder name from the job index
        max_lines: Optional limit on number of lines to return (for safety)

    Returns: The complete (or truncated) job log.

    ⚠️ WARNING: Check log size first! Use `check_log_size` before calling this.
    For large logs, use `search_log` instead.
    """
    log_file = CI_RESULTS_DIR / folder_name / "log.txt"

    if not log_file.exists():
        return f"❌ No log found for job '{folder_name}'"

    size_kb = log_file.stat().st_size / 1024

    # Safety check
    if size_kb > MEDIUM_LOG_THRESHOLD and max_lines is None:
        return (
            f"🚨 ERROR: Log is {size_kb:.1f}KB - too large to read without limit!\n\n"
            f"Use `check_log_size('{folder_name}')` first, then either:\n"
            f"1. Use `search_log('{folder_name}', 'pattern')` to find specific errors\n"
            f"2. Call this again with max_lines parameter: `read_full_log('{folder_name}', 500)`"
        )

    with open(log_file) as f:
        if max_lines:
            lines = [next(f) for _ in range(max_lines) if True]
            content = "".join(lines)
            truncated = True
        else:
            content = f.read()
            truncated = False

    result = f"# Full Log: {folder_name}\n\n"

    if truncated:
        result += f"⚠️ **Truncated to {max_lines} lines** (log is {size_kb:.1f}KB)\n\n"
    else:
        result += f"**Size:** {size_kb:.1f}KB\n\n"

    result += "```\n" + content + "\n```"

    if truncated:
        result += "\n\n⚠️ Log truncated. Use `search_log` to find specific patterns."

    return result


@tool("Get Log Statistics")
def get_log_stats(folder_name: str) -> str:
    """
    Get statistics about a job log (error counts, warnings, etc.).

    Args:
        folder_name: The folder name from the job index

    Returns: Statistics to help decide if detailed log review is needed.

    Use this to quickly assess log content without reading the whole file.
    """
    log_file = CI_RESULTS_DIR / folder_name / "log.txt"

    if not log_file.exists():
        return f"❌ No log found for job '{folder_name}'"

    error_count = 0
    warning_count = 0
    failed_count = 0
    exception_count = 0
    total_lines = 0

    patterns = {
        "error": re.compile(r"\berror\b", re.IGNORECASE),
        "warning": re.compile(r"\bwarning\b", re.IGNORECASE),
        "failed": re.compile(r"\bfailed\b", re.IGNORECASE),
        "exception": re.compile(r"\bexception\b", re.IGNORECASE),
    }

    with open(log_file) as f:
        for line in f:
            total_lines += 1

            if patterns["error"].search(line):
                error_count += 1
            if patterns["warning"].search(line):
                warning_count += 1
            if patterns["failed"].search(line):
                failed_count += 1
            if patterns["exception"].search(line):
                exception_count += 1

    size_kb = log_file.stat().st_size / 1024

    result = f"# Log Statistics: {folder_name}\n\n"
    result += f"**Total lines:** {total_lines:,}\n"
    result += f"**File size:** {size_kb:.1f}KB\n\n"
    result += "## Pattern Counts\n\n"
    result += f"- 🔴 **Errors:** {error_count}\n"
    result += f"- ⚠️ **Warnings:** {warning_count}\n"
    result += f"- ❌ **Failed:** {failed_count}\n"
    result += f"- 💥 **Exceptions:** {exception_count}\n\n"

    if error_count > 0 or failed_count > 0 or exception_count > 0:
        result += "🚨 **Recommendation:** This log contains errors/failures. "
        result += f"Use `search_log('{folder_name}', 'error')` to investigate.\n"
    elif warning_count > 0:
        result += "⚠️ **Recommendation:** Log has warnings but may have passed. "
        result += "Check summary first.\n"
    else:
        result += "✅ **Recommendation:** Log appears clean. Review summary for details.\n"

    return result
