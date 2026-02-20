"""Finance review crew."""

import logging

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from tools.github_tools import CommitDiffTool, CommitInfoTool, FileContentTool
from tools.related_files_tool import RelatedFilesTool
from tools.workspace_tool import WorkspaceTool
from utils.model_config import get_llm, get_rate_limiter

logger = logging.getLogger(__name__)


@CrewBase
class FinanceReviewCrew:
    """Billing, payments, and financial controls review."""

    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/finance_review_tasks.yaml"

    def __init__(self):
        self.llm = get_llm()
        logger.info(f"FinanceReview using model: {self.llm.model}")

    @agent
    def revenue_auditor(self) -> Agent:
        return Agent(
            config=self.agents_config["revenue_auditor"],
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
    def review_finance(self) -> Task:
        return Task(
            config=self.tasks_config["review_finance"],
            agent=self.revenue_auditor(),
            output_file="finance_review.json",
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.revenue_auditor()],
            tasks=[self.review_finance()],
            process=Process.sequential,
            verbose=True,
            max_rpm=get_rate_limiter().current_limit,
        )
