"""Marketing review crew — 3-agent global GTM pipeline."""

import logging

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from tools.github_tools import CommitDiffTool, CommitInfoTool, FileContentTool
from tools.related_files_tool import RelatedFilesTool
from tools.workspace_tool import WorkspaceTool
from utils.model_config import get_llm, get_rate_limiter

logger = logging.getLogger(__name__)


@CrewBase
class MarketingReviewCrew:
    """Brand copy + global market strategy + growth compliance pipeline."""

    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/marketing_review_tasks.yaml"

    def __init__(self):
        self.llm = get_llm()
        logger.info(f"MarketingReview using model: {self.llm.model}")

    @agent
    def brand_editor(self) -> Agent:
        return Agent(
            config=self.agents_config["brand_editor"],
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
    def global_market_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config["global_market_strategist"],
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
    def growth_compliance_reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config["growth_compliance_reviewer"],
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
    def analyze_brand_copy(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_brand_copy"],
            agent=self.brand_editor(),
        )

    @task
    def analyze_global_market(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_global_market"],
            agent=self.global_market_strategist(),
        )

    @task
    def synthesize_marketing_review(self) -> Task:
        return Task(
            config=self.tasks_config["synthesize_marketing_review"],
            agent=self.growth_compliance_reviewer(),
            output_file="marketing_review.json",
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.brand_editor(),
                self.global_market_strategist(),
                self.growth_compliance_reviewer(),
            ],
            tasks=[
                self.analyze_brand_copy(),
                self.analyze_global_market(),
                self.synthesize_marketing_review(),
            ],
            process=Process.sequential,
            verbose=True,
            max_rpm=get_rate_limiter().current_limit,
        )
