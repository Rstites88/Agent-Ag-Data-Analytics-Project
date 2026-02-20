"""Final summary crew."""

import logging

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from tools.workspace_tool import WorkspaceTool
from utils.model_config import get_llm, get_rate_limiter

logger = logging.getLogger(__name__)


@CrewBase
class FinalSummaryCrew:
    """Final summary crew."""

    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/final_summary_tasks.yaml"

    def __init__(self):
        """Initialize final summary crew."""
        # Get LLM from centralized config
        self.llm = get_llm()
        logger.info(f"FinalSummary using model: {self.llm.model}")

    @agent
    def executive_summary_agent(self) -> Agent:
        """Create executive summary agent."""
        return Agent(
            config=self.agents_config["executive_summary_agent"],
            tools=[WorkspaceTool()],
            llm=self.llm,
            function_calling_llm=self.llm,  # Enable function calling
            max_iter=10,
            verbose=True,
            allow_delegation=False,
        )

    @task
    def synthesize_summary(self) -> Task:
        """Synthesize final summary task."""
        # CRITICAL: Use filename only (not full path) - CrewAI writes to CWD
        return Task(
            config=self.tasks_config["synthesize_summary"],
            agent=self.executive_summary_agent(),
            output_file="final_summary.md",  # Just filename - CrewAI handles path
        )

    @crew
    def crew(self) -> Crew:
        """Create final summary crew."""
        return Crew(
            agents=[self.executive_summary_agent()],
            tasks=[self.synthesize_summary()],
            process=Process.sequential,
            verbose=True,
            max_rpm=get_rate_limiter().current_limit,
        )
