"""CI output parser tool for analyzing core-ci results."""

import logging
import os
from typing import Any

from crewai.tools import BaseTool

logger = logging.getLogger(__name__)


class CIOutputParserTool(BaseTool):
    """Parse core-ci job outputs from GitHub Actions environment."""

    name: str = "CI Output Parser Tool"
    description: str = (
        "Parse CI job results from GitHub Actions environment. "
        "Returns: status (success/failure), errors, warnings, job summaries. "
        "Reads from environment variables passed by workflow."
    )

    def _run(self, core_ci_result: str = "") -> dict[str, Any]:
        """Parse CI outputs from environment.

        Args:
            core_ci_result: Job result from needs.core-ci.result

        Returns:
            Dict with CI status, errors, warnings
        """
        # Get result from env if not passed
        if not core_ci_result:
            core_ci_result = os.getenv("CORE_CI_RESULT", "success")

        logger.info(f"📊 Parsing CI results: {core_ci_result}")

        ci_summary = {
            "status": core_ci_result,
            "passed": core_ci_result == "success",
            "critical_errors": [],
            "warnings": [],
            "info": [],
            "summary": "",
        }

        # TODO: In future, parse actual job outputs when we expose them
        # For now, we'll work with the high-level pass/fail status
        # and can enhance this when core-ci job exposes detailed outputs

        if core_ci_result == "success":
            ci_summary["summary"] = "All CI checks passed ✅"
            logger.info("✅ Core CI passed")
        else:
            ci_summary["summary"] = "CI checks failed - review logs ❌"
            ci_summary["critical_errors"].append(
                {
                    "type": "ci_failure",
                    "message": "Core CI job failed. Check GitHub Actions logs for details.",
                    "severity": "critical",
                }
            )
            logger.warning("⚠️ Core CI failed")

        # Try to read GitHub step summary if available
        step_summary_file = os.getenv("GITHUB_STEP_SUMMARY")
        if step_summary_file and os.path.exists(step_summary_file):
            try:
                with open(step_summary_file) as f:
                    summary_content = f.read()
                if summary_content:
                    ci_summary["github_summary"] = summary_content
                    logger.info(f"📄 Read {len(summary_content)} bytes from step summary")
            except Exception as e:
                logger.warning(f"Could not read step summary: {e}")

        return ci_summary
