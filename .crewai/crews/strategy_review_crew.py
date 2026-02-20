"""Strategy review crew — 3-agent global expansion pipeline."""

import logging

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from tools.github_tools import CommitDiffTool, CommitInfoTool, FileContentTool
from tools.related_files_tool import RelatedFilesTool
from tools.workspace_tool import WorkspaceTool
from utils.model_config import get_llm, get_rate_limiter

logger = logging.getLogger(__name__)


@CrewBase
class StrategyReviewCrew:
    """Strategic impact + global expansion + competitive intelligence pipeline."""

    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/strategy_review_tasks.yaml"

    def __init__(self):
        self.llm = get_llm()
        logger.info(f"StrategyReview using model: {self.llm.model}")

    @agent
    def strategy_consultant(self) -> Agent:
        return Agent(
            config=self.agents_config["strategy_consultant"],
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
    def global_expansion_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["global_expansion_analyst"],
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
    def competitive_intel_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["competitive_intel_analyst"],
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
    def analyze_strategic_impact(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_strategic_impact"],
            agent=self.strategy_consultant(),
        )

    @task
    def analyze_global_expansion(self) -> Task:
        return Task(
            config=self.tasks_config["analyze_global_expansion"],
            agent=self.global_expansion_analyst(),
        )

    @task
    def synthesize_strategic_review(self) -> Task:
        return Task(
            config=self.tasks_config["synthesize_strategic_review"],
            agent=self.competitive_intel_analyst(),
            output_file="strategic_review.json",
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.strategy_consultant(),
                self.global_expansion_analyst(),
                self.competitive_intel_analyst(),
            ],
            tasks=[
                self.analyze_strategic_impact(),
                self.analyze_global_expansion(),
                self.synthesize_strategic_review(),
            ],
            process=Process.sequential,
            verbose=True,
            max_rpm=get_rate_limiter().current_limit,
        )
