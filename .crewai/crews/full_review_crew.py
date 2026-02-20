"""Full technical review crew — 3-agent deep analysis pipeline."""

import logging

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from tools.workspace_tool import WorkspaceTool
from utils.model_config import get_llm, get_rate_limiter

logger = logging.getLogger(__name__)


@CrewBase
class FullReviewCrew:
    """Code quality + architecture + security deep dive pipeline."""

    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/full_review_tasks.yaml"

    def __init__(self):
        self.llm = get_llm()
        logger.info(f"FullReview using model: {self.llm.model}")

    @agent
    def code_quality_reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config["code_quality_reviewer"],
            tools=[WorkspaceTool()],
            llm=self.llm,
            function_calling_llm=self.llm,
            max_iter=10,
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def architecture_impact_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["architecture_impact_analyst"],
            tools=[WorkspaceTool()],
            llm=self.llm,
            function_calling_llm=self.llm,
            max_iter=10,
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def security_performance_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["security_performance_analyst"],
            tools=[WorkspaceTool()],
            llm=self.llm,
            function_calling_llm=self.llm,
            max_iter=10,
            verbose=True,
            allow_delegation=False,
        )

    @task
    def full_technical_review(self) -> Task:
        return Task(
            config=self.tasks_config["full_technical_review"],
            agent=self.code_quality_reviewer(),
        )

    @task
    def architecture_review(self) -> Task:
        return Task(
            config=self.tasks_config["architecture_review"],
            agent=self.architecture_impact_analyst(),
        )

    @task
    def security_deep_dive(self) -> Task:
        return Task(
            config=self.tasks_config["security_deep_dive"],
            agent=self.security_performance_analyst(),
        )

    @task
    def synthesize_full_review(self) -> Task:
        return Task(
            config=self.tasks_config["synthesize_full_review"],
            agent=self.code_quality_reviewer(),
            output_file="full_review.json",
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.code_quality_reviewer(),
                self.architecture_impact_analyst(),
                self.security_performance_analyst(),
            ],
            tasks=[
                self.full_technical_review(),
                self.architecture_review(),
                self.security_deep_dive(),
                self.synthesize_full_review(),
            ],
            process=Process.sequential,
            verbose=True,
            max_rpm=get_rate_limiter().current_limit,
        )
