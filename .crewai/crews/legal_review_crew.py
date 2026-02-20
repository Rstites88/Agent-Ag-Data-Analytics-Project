"""Legal compliance review crew — 4-agent multi-jurisdiction pipeline."""

import logging

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from tools.github_tools import CommitDiffTool, CommitInfoTool, FileContentTool
from tools.related_files_tool import RelatedFilesTool
from tools.workspace_tool import WorkspaceTool
from utils.model_config import get_llm, get_rate_limiter

logger = logging.getLogger(__name__)


@CrewBase
class LegalReviewCrew:
    """OSS license + US regulatory + international trade + global privacy pipeline."""

    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/legal_review_tasks.yaml"

    def __init__(self):
        self.llm = get_llm()
        logger.info(f"LegalReview using model: {self.llm.model}")

    @agent
    def license_counsel(self) -> Agent:
        return Agent(
            config=self.agents_config["license_counsel"],
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

    @agent
    def us_regulatory_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["us_regulatory_analyst"],
            tools=[
                WorkspaceTool(),
                FileContentTool,
                RelatedFilesTool,
                CommitInfoTool,
                CommitDiffTool,
            ],
            llm=self.llm,
            function_calling_llm=self.llm,
            max_iter=12,
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def intl_trade_counsel(self) -> Agent:
        return Agent(
            config=self.agents_config["intl_trade_counsel"],
            tools=[
                WorkspaceTool(),
                FileContentTool,
                RelatedFilesTool,
                CommitInfoTool,
                CommitDiffTool,
            ],
            llm=self.llm,
            function_calling_llm=self.llm,
            max_iter=12,
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def global_privacy_counsel(self) -> Agent:
        return Agent(
            config=self.agents_config["global_privacy_counsel"],
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
    def analyze_oss_licenses(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_oss_licenses"],
            agent=self.license_counsel(),
        )

    @task
    def analyze_us_regulatory(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_us_regulatory"],
            agent=self.us_regulatory_analyst(),
        )

    @task
    def analyze_intl_trade(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_intl_trade"],
            agent=self.intl_trade_counsel(),
        )

    @task
    def synthesize_legal_review(self) -> Task:
        return Task(
            config=self.tasks_config["synthesize_legal_review"],
            agent=self.global_privacy_counsel(),
            output_file="legal_review.json",
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.license_counsel(),
                self.us_regulatory_analyst(),
                self.intl_trade_counsel(),
                self.global_privacy_counsel(),
            ],
            tasks=[
                self.analyze_oss_licenses(),
                self.analyze_us_regulatory(),
                self.analyze_intl_trade(),
                self.synthesize_legal_review(),
            ],
            process=Process.sequential,
            verbose=True,
            max_rpm=get_rate_limiter().current_limit,
        )
