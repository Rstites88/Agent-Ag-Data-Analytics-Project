"""Data engineering review crew."""

import logging

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from tools.github_tools import CommitDiffTool, CommitInfoTool, FileContentTool
from tools.related_files_tool import RelatedFilesTool
from tools.workspace_tool import WorkspaceTool
from utils.model_config import get_llm, get_rate_limiter

logger = logging.getLogger(__name__)


@CrewBase
class DataEngineeringReviewCrew:
    """Data modeling, SQL, and pipeline reliability review."""

    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/data_engineering_review_tasks.yaml"

    def __init__(self):
        self.llm = get_llm()
        logger.info(f"DataEngineeringReview using model: {self.llm.model}")

    @agent
    def data_engineering_reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config["data_engineering_reviewer"],
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
    def review_data_engineering(self) -> Task:
        return Task(
            config=self.tasks_config["review_data_engineering"],
            agent=self.data_engineering_reviewer(),
            output_file="data_engineering_review.json",
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.data_engineering_reviewer()],
            tasks=[self.review_data_engineering()],
            process=Process.sequential,
            verbose=True,
            max_rpm=get_rate_limiter().current_limit,
        )
