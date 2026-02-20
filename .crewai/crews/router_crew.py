"""Router crew for workflow orchestration."""

import logging
import os

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from tools.workspace_tool import WorkspaceTool
from utils.model_config import get_llm, get_rate_limiter

logger = logging.getLogger(__name__)


@CrewBase
class RouterCrew:
    """Router crew that decides which review workflows to execute."""

    # Paths relative to this file (.crewai/crews/) → go up to .crewai/config/
    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/router_tasks.yaml"

    def __init__(self):
        """Initialize router crew with config."""
        if not (os.getenv("NVIDIA_API_KEY") or os.getenv("NVIDIA_NIM_API_KEY")):
            os.environ["OPENROUTER_API_BASE"] = "https://openrouter.ai/api/v1"

        # Register cost tracking callbacks (if available)
        try:
            import litellm

            # Import callbacks if they exist
            try:
                from crew import litellm_failure_callback, litellm_success_callback

                litellm.success_callback = [litellm_success_callback]
                litellm.failure_callback = [litellm_failure_callback]
                litellm.set_verbose = True
                logger.info("Cost tracking callbacks registered")
            except ImportError:
                logger.debug("Cost tracking callbacks not available")
        except ImportError:
            logger.debug("LiteLLM cost tracking not available")

        # Get LLM from centralized config
        self.llm = get_llm()
        logger.info(f"Router using model: {self.llm.model}")

    @agent
    def router_agent(self) -> Agent:
        """Create router agent with function calling enabled.

        IMPORTANT: The GitHub workflow has already prepared all data files
        (diff.txt, commits.json, diff.json) in the workspace. The router
        only needs WorkspaceTool to read these pre-prepared files.
        """
        return Agent(
            config=self.agents_config["router_agent"],
            tools=[WorkspaceTool()],  # Only need workspace tool - data is pre-prepared
            llm=self.llm,  # Use LLM instance
            function_calling_llm=self.llm,  # CRITICAL: Enable function calling
            max_iter=4,
            verbose=True,
            allow_delegation=False,  # Don't delegate to other agents
        )

    @task
    def analyze_and_route(self) -> Task:
        """Route workflow based on PR analysis."""
        return Task(
            config=self.tasks_config["analyze_pr_and_route"],
            agent=self.router_agent(),
        )

    @crew
    def crew(self) -> Crew:
        """Create router crew."""
        return Crew(
            agents=[self.router_agent()],
            tasks=[self.analyze_and_route()],
            process=Process.sequential,
            verbose=True,
            max_rpm=get_rate_limiter().current_limit,
        )
