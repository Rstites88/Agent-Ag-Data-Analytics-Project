"""Cost tracking for LiteLLM API calls during CrewAI execution."""

import atexit
import logging
import os
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class APICallMetrics:
    """Metrics for a single API call."""

    call_number: int
    task_name: str
    crew_name: str  # NEW: Identify which crew made the call
    agent_name: str
    model: str
    tokens_in: int
    tokens_out: int
    total_tokens: int
    cost: float
    duration_seconds: float
    tokens_per_second: float
    timestamp: float
    generation_id: Optional[str] = None

    def __str__(self) -> str:
        """Format metrics as a table row."""
        # Shorten model name for display
        model_short = self.model.replace("gemini-2.0-flash", "gemini-flash").replace("-001", "")
        return (
            f"| #{self.call_number} | {self.crew_name} | {self.agent_name} | {model_short} "
            f"| {self.tokens_in:,} | {self.tokens_out:,} "
            f"| ${self.cost:.6f} | {self.tokens_per_second:.1f} tok/s |"
        )


class CostTracker:
    """Track costs and metrics for all LiteLLM API calls."""

    def __init__(self):
        """Initialize cost tracker."""
        self.calls: List[APICallMetrics] = []
        self.current_task: Optional[str] = None
        self.current_crew: Optional[str] = None  # NEW: Track current crew
        self.current_agent: Optional[str] = None
        self.call_counter = 0
        self.generation_ids: Dict[str, int] = {}  # Track generation_id -> call_number
        self._cleanup_registered = False
        logger.info("📊 Cost tracker initialized")

        # Register cleanup handler
        self._register_cleanup()

    def _register_cleanup(self):
        """Register cleanup handler for atexit."""
        if not self._cleanup_registered:
            try:
                atexit.register(self._cleanup)
                self._cleanup_registered = True
            except RuntimeError:
                # Already in shutdown, skip registration
                pass

    def _cleanup(self):
        """Cleanup method called on exit."""
        try:
            if self.calls:
                logger.debug(f"Cost tracker cleanup: {len(self.calls)} calls recorded")
        except Exception:
            pass  # Ignore errors during shutdown

    def _infer_crew_from_task(self, task_name: str) -> str:
        """Infer crew name from task name."""
        task_lower = task_name.lower()

        specialist_match = re.search(r"specialist[-_](?P<name>[a-z0-9_]+)", task_lower)
        if specialist_match:
            raw_name = specialist_match.group("name")
            cleaned = raw_name
            while True:
                stripped = re.sub(r"(?:_local|_attempt_\d+)$", "", cleaned)
                if stripped == cleaned:
                    break
                cleaned = stripped
            cleaned = cleaned.replace("_", " ").replace("-", " ")
            pretty = " ".join(part.capitalize() for part in cleaned.split())
            return f"Specialist: {pretty}" if pretty else "Specialist"

        if "route" in task_lower or "router" in task_lower:
            return "Router"
        elif "quick" in task_lower:
            return "Quick Review"
        elif "full" in task_lower:
            return "Full Review"
        elif "legal" in task_lower:
            return "Legal Review"
        elif "summary" in task_lower or "synthesize" in task_lower:
            return "Final Summary"
        elif re.search(r"\bci\b", task_lower) or "parse_ci" in task_lower or "log" in task_lower:
            return "CI Analysis"
        return "Unknown"

    def set_current_task(self, task_name: str):
        """Set the current task name for associating API calls."""
        self.current_task = task_name
        self.current_crew = self._infer_crew_from_task(task_name)
        self.current_agent = self._infer_agent_from_task(task_name)
        logger.info(
            f"🏷️  Tracking costs for: {task_name} "
            f"(Crew: {self.current_crew}, Agent: {self.current_agent})"
        )

    def _infer_agent_from_task(self, task_name: str) -> str:
        """Infer a human-readable agent name from task context."""
        task_lower = str(task_name or "").lower()

        if "analyze_pr_and_route" in task_lower:
            return "Router agent"
        if "parse_ci_output" in task_lower:
            return "CI analyst"

        if task_lower.startswith("quick_code_review_"):
            suffix = task_lower.replace("quick_code_review_", "", 1)
            return " ".join(part.capitalize() for part in suffix.split("_")) or "Quick reviewer"
        if "quick_code_review" in task_lower:
            return "Quick review coordinator"

        if "full_review_quality" in task_lower:
            return "Code quality reviewer"
        if "full_review_architecture" in task_lower:
            return "Architecture impact analyst"
        if "full_review_security" in task_lower:
            return "Security performance analyst"
        if "full_review_synthesis" in task_lower:
            return "Full review synthesizer"
        if "full_technical_review" in task_lower:
            return "Full review coordinator"

        if task_lower.startswith("specialist_"):
            name = task_lower.replace("specialist_", "", 1)
            name = re.sub(r"(?:_local|_attempt_\d+)$", "", name)
            pretty = " ".join(part.capitalize() for part in name.split("_"))
            return f"{pretty} specialist" if pretty else "Specialist reviewer"

        if "synthesize_final_summary" in task_lower:
            return "Summary synthesizer"

        return "Unknown"

    def log_api_call(
        self,
        model: str,
        tokens_in: int,
        tokens_out: int,
        cost: float,
        duration_seconds: float,
        generation_id: Optional[str] = None,
    ):
        """Log metrics for a single API call.

        Args:
            model: Model name (e.g., 'google/gemini-2.0-flash-001')
            tokens_in: Input tokens (prompt)
            tokens_out: Output tokens (completion)
            cost: Cost in USD
            duration_seconds: Call duration in seconds
            generation_id: OpenRouter generation ID for async retrieval
        """
        self.call_counter += 1
        total_tokens = tokens_in + tokens_out

        # Calculate tokens per second
        tokens_per_second = total_tokens / duration_seconds if duration_seconds > 0 else 0

        # Use current task or "Unknown" if not set
        task_name = self.current_task or "Unknown"
        crew_name = self.current_crew or self._infer_crew_from_task(task_name)
        agent_name = self.current_agent or self._infer_agent_from_task(task_name)

        metrics = APICallMetrics(
            call_number=self.call_counter,
            task_name=task_name,
            crew_name=crew_name,
            agent_name=agent_name,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            total_tokens=total_tokens,
            cost=cost,
            duration_seconds=duration_seconds,
            tokens_per_second=tokens_per_second,
            timestamp=time.time(),
            generation_id=generation_id,
        )

        self.calls.append(metrics)

        # Track generation ID for later enrichment
        if generation_id:
            self.generation_ids[generation_id] = self.call_counter

        logger.info(
            f"💸 Call #{self.call_counter} ({crew_name} / {agent_name}): {model} "
            f"({tokens_in:,} in, {tokens_out:,} out, "
            f"${cost:.6f}, {tokens_per_second:.1f} tok/s)"
        )

    def get_crew_summary(self) -> Dict[str, Dict]:
        """Get cost summary grouped by crew."""
        crew_stats = defaultdict(
            lambda: {
                "calls": 0,
                "tokens_in": 0,
                "tokens_out": 0,
                "total_tokens": 0,
                "cost": 0.0,
                "duration": 0.0,
            }
        )

        for call in self.calls:
            stats = crew_stats[call.crew_name]
            stats["calls"] += 1
            stats["tokens_in"] += call.tokens_in
            stats["tokens_out"] += call.tokens_out
            stats["total_tokens"] += call.total_tokens
            stats["cost"] += call.cost
            stats["duration"] += call.duration_seconds

        return dict(crew_stats)

    def get_agent_summary(self) -> Dict[str, Dict]:
        """Get cost summary grouped by inferred agent."""
        agent_stats = defaultdict(
            lambda: {
                "calls": 0,
                "tokens_in": 0,
                "tokens_out": 0,
                "total_tokens": 0,
                "cost": 0.0,
                "duration": 0.0,
            }
        )

        for call in self.calls:
            stats = agent_stats[call.agent_name]
            stats["calls"] += 1
            stats["tokens_in"] += call.tokens_in
            stats["tokens_out"] += call.tokens_out
            stats["total_tokens"] += call.total_tokens
            stats["cost"] += call.cost
            stats["duration"] += call.duration_seconds

        return dict(agent_stats)

    def enrich_from_openrouter(self):
        """Enrich metrics by fetching data from OpenRouter API using generation IDs.

        This is a fallback method when LiteLLM callbacks don't provide complete data.
        """
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            logger.warning("⚠️  No OPENROUTER_API_KEY, skipping enrichment")
            return

        enriched_count = 0
        for call in self.calls:
            if not call.generation_id:
                continue

            try:
                # Fetch detailed usage from OpenRouter
                response = requests.get(
                    f"https://openrouter.ai/api/v1/generation?id={call.generation_id}",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=5,
                )

                if response.status_code == 200:
                    data = response.json().get("data", {})

                    # Update with precise OpenRouter data
                    if "tokens_prompt" in data:
                        call.tokens_in = data["tokens_prompt"]
                    if "tokens_completion" in data:
                        call.tokens_out = data["tokens_completion"]
                    if "native_tokens_prompt" in data:
                        call.tokens_in = data["native_tokens_prompt"]
                    if "native_tokens_completion" in data:
                        call.tokens_out = data["native_tokens_completion"]

                    # Recalculate derived fields
                    call.total_tokens = call.tokens_in + call.tokens_out
                    if call.duration_seconds > 0:
                        call.tokens_per_second = call.total_tokens / call.duration_seconds

                    # Update cost if available
                    if "total_cost" in data:
                        call.cost = float(data["total_cost"])

                    enriched_count += 1
                    logger.debug(f"✅ Enriched call #{call.call_number} from OpenRouter")

            except Exception as e:
                logger.warning(f"⚠️  Failed to enrich call #{call.call_number}: {e}")

        if enriched_count > 0:
            logger.info(f"✅ Enriched {enriched_count} calls from OpenRouter API")

    def get_total_cost(self) -> float:
        """Get total cost across all API calls."""
        return sum(call.cost for call in self.calls)

    def get_total_tokens(self) -> int:
        """Get total tokens (in + out) across all API calls."""
        return sum(call.total_tokens for call in self.calls)

    def get_total_tokens_in(self) -> int:
        """Get total input tokens across all API calls."""
        return sum(call.tokens_in for call in self.calls)

    def get_total_tokens_out(self) -> int:
        """Get total output tokens across all API calls."""
        return sum(call.tokens_out for call in self.calls)

    def get_total_duration(self) -> float:
        """Get total duration across all API calls."""
        return sum(call.duration_seconds for call in self.calls)

    def get_average_tokens_per_second(self) -> float:
        """Get average tokens per second across all API calls."""
        if not self.calls:
            return 0.0
        return sum(call.tokens_per_second for call in self.calls) / len(self.calls)

    def get_summary(self) -> Dict:
        """Get summary statistics for all API calls.

        Returns:
            Dictionary containing:
            - total_calls: Number of API calls
            - total_tokens: Total tokens (input + output)
            - total_tokens_in: Total input tokens
            - total_tokens_out: Total output tokens
            - total_cost: Total cost in USD
            - total_duration: Total duration in seconds
            - average_tokens_per_second: Average throughput
            - crew_breakdown: Per-crew statistics
            - agent_breakdown: Per-agent statistics
        """
        return {
            "total_calls": len(self.calls),
            "total_tokens": self.get_total_tokens(),
            "total_tokens_in": self.get_total_tokens_in(),
            "total_tokens_out": self.get_total_tokens_out(),
            "total_cost": self.get_total_cost(),
            "total_duration": self.get_total_duration(),
            "average_tokens_per_second": self.get_average_tokens_per_second(),
            "crew_breakdown": self.get_crew_summary(),
            "agent_breakdown": self.get_agent_summary(),
        }

    def format_as_markdown_table(self) -> str:
        """Format all metrics as a markdown table with crew breakdowns.

        Returns:
            Markdown-formatted table string
        """
        if not self.calls:
            return "_No API calls recorded_"

        lines = [
            "| Call | Crew | Agent | Model | Input | Output | Cost | Speed |",
            "|------|------|-------|-------|-------|--------|------|-------|",
        ]

        # Group calls by crew and add crew subtotals
        crew_summary = self.get_crew_summary()
        current_crew = None

        for i, call in enumerate(self.calls):
            # Add crew subtotal before switching crews
            if current_crew and call.crew_name != current_crew:
                stats = crew_summary[current_crew]
                lines.append(
                    f"| **{current_crew} Total** | **{stats['calls']} calls** | - | - "
                    f"| **{stats['tokens_in']:,}** | **{stats['tokens_out']:,}** "
                    f"| **${stats['cost']:.6f}** | - |"
                )

            current_crew = call.crew_name
            lines.append(str(call))

        # Add final crew subtotal
        if current_crew:
            stats = crew_summary[current_crew]
            lines.append(
                f"| **{current_crew} Total** | **{stats['calls']} calls** | - | - "
                f"| **{stats['tokens_in']:,}** | **{stats['tokens_out']:,}** "
                f"| **${stats['cost']:.6f}** | - |"
            )

        # Add grand total
        lines.append(
            f"| **GRAND TOTAL** | **{len(self.calls)} calls** | - | - "
            f"| **{self.get_total_tokens_in():,}** "
            f"| **{self.get_total_tokens_out():,}** "
            f"| **${self.get_total_cost():.6f}** "
            f"| **{self.get_average_tokens_per_second():.1f} tok/s** |"
        )

        return "\n".join(lines)

    def format_summary(self) -> str:
        """Format a brief summary of costs with crew breakdown.

        Returns:
            Human-readable summary string
        """
        if not self.calls:
            return "No API calls recorded"

        crew_summary = self.get_crew_summary()
        agent_summary = self.get_agent_summary()
        crew_lines = []
        for crew_name in sorted(crew_summary.keys()):
            stats = crew_summary[crew_name]
            crew_lines.append(
                f"  • {crew_name}: {stats['calls']} calls, "
                f"${stats['cost']:.6f} ({stats['total_tokens']:,} tokens)"
            )

        agent_lines = []
        for agent_name in sorted(agent_summary.keys()):
            stats = agent_summary[agent_name]
            agent_lines.append(
                f"  • {agent_name}: {stats['calls']} calls, "
                f"${stats['cost']:.6f} ({stats['total_tokens']:,} tokens)"
            )

        return (
            f"📊 Total API Calls: {len(self.calls)}\n"
            f"💰 Total Cost: ${self.get_total_cost():.6f}\n"
            f"🔢 Total Tokens: {self.get_total_tokens():,} "
            f"({self.get_total_tokens_in():,} in, {self.get_total_tokens_out():,} out)\n"
            f"⚡ Average Speed: {self.get_average_tokens_per_second():.1f} tokens/sec\n"
            f"\n📋 By Crew:\n"
            + "\n".join(crew_lines)
            + "\n\n🧠 By Agent:\n"
            + "\n".join(agent_lines)
        )


# Global tracker instance
_global_tracker: Optional[CostTracker] = None


def get_tracker() -> CostTracker:
    """Get or create the global cost tracker instance."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = CostTracker()
    return _global_tracker


def reset_tracker():
    """Reset the global tracker (useful for testing)."""
    global _global_tracker
    _global_tracker = CostTracker()
