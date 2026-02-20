"""Agentic consistency review crew."""

import logging

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from tools.github_tools import CommitDiffTool, CommitInfoTool, FileContentTool
from tools.related_files_tool import RelatedFilesTool
from tools.workspace_tool import WorkspaceTool
from utils.model_config import get_llm, get_rate_limiter

logger = logging.getLogger(__name__)


@CrewBase
class AgenticReviewCrew:
    """AGENTS.md and agentic convention compliance review."""

    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/agentic_review_tasks.yaml"

    def __init__(self):
        self.llm = get_llm()
        logger.info(f"AgenticReview using model: {self.llm.model}")

    @agent
    def agentic_steward(self) -> Agent:
        return Agent(
            config=self.agents_config["agentic_steward"],
            tools=[
                WorkspaceTool(),
                FileContentTool,
                RelatedFilesTool,
                CommitInfoTool,
                CommitDiffTool,
            ],
            llm=self.llm,
            function_calling_llm=self.llm,
            max_iter=10,
            verbose=True,
            allow_delegation=False,
        )

    @task
    def review_agentic_consistency(self) -> Task:
        return Task(
            config=self.tasks_config["review_agentic_consistency"],
            agent=self.agentic_steward(),
            output_file="agentic_consistency_review.json",
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.agentic_steward()],
            tasks=[self.review_agentic_consistency()],
            process=Process.sequential,
            verbose=True,
            max_rpm=get_rate_limiter().current_limit,
        )
