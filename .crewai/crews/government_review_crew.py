"""Government regulatory review crew."""

import logging

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from tools.github_tools import CommitDiffTool, CommitInfoTool, FileContentTool
from tools.related_files_tool import RelatedFilesTool
from tools.workspace_tool import WorkspaceTool
from utils.model_config import get_llm, get_rate_limiter

logger = logging.getLogger(__name__)


@CrewBase
class GovernmentReviewCrew:
    """WCAG, Section 508, audit trails, and regulatory compliance review."""

    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/government_review_tasks.yaml"

    def __init__(self):
        self.llm = get_llm()
        logger.info(f"GovernmentReview using model: {self.llm.model}")

    @agent
    def public_sector_compliance(self) -> Agent:
        return Agent(
            config=self.agents_config["public_sector_compliance"],
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
    def review_government_compliance(self) -> Task:
        return Task(
            config=self.tasks_config["review_government_compliance"],
            agent=self.public_sector_compliance(),
            output_file="government_regulatory_review.json",
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.public_sector_compliance()],
            tasks=[self.review_government_compliance()],
            process=Process.sequential,
            verbose=True,
            max_rpm=get_rate_limiter().current_limit,
        )
