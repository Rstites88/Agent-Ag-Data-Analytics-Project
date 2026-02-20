"""Quick review crew with optimized 3-agent architecture."""

import logging

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from tools.workspace_tool import WorkspaceTool
from utils.model_config import get_llm, get_rate_limiter

logger = logging.getLogger(__name__)


@CrewBase
class QuickReviewCrew:
    """Quick review crew with adaptive diff sampling."""

    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/quick_review_tasks.yaml"

    def __init__(self):
        """Initialize quick review crew."""
        self.llm = get_llm()
        logger.info(f"QuickReview using model: {self.llm.model}")

    @agent
    def diff_intelligence_specialist(self) -> Agent:
        """Diff Intelligence Specialist - parses diffs and builds focused context."""
        return Agent(
            config=self.agents_config["diff_intelligence_specialist"],
            tools=[WorkspaceTool()],
            llm=self.llm,
            function_calling_llm=self.llm,
            max_iter=1,
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def code_quality_investigator(self) -> Agent:
        """Code Quality Investigator - detects issues in focused context."""
        return Agent(
            config=self.agents_config["code_quality_investigator"],
            tools=[WorkspaceTool()],
            llm=self.llm,
            function_calling_llm=self.llm,
            max_iter=1,
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def review_synthesizer(self) -> Agent:
        """Review Synthesizer - consolidates findings into quick_review.json."""
        return Agent(
            config=self.agents_config["review_synthesizer"],
            tools=[WorkspaceTool()],
            llm=self.llm,
            function_calling_llm=self.llm,
            max_iter=1,
            verbose=True,
            allow_delegation=False,
        )

    @task
    def parse_and_contextualize(self) -> Task:
        """Parse diff and build focused review context."""
        return Task(
            config=self.tasks_config["parse_and_contextualize"],
            agent=self.diff_intelligence_specialist(),
        )

    @task
    def detect_code_issues(self) -> Task:
        """Detect issues in focused diff context."""
        return Task(
            config=self.tasks_config["detect_code_issues"],
            agent=self.code_quality_investigator(),
        )

    @task
    def synthesize_report(self) -> Task:
        """Synthesize findings into final quick_review.json."""
        return Task(
            config=self.tasks_config["synthesize_report"],
            agent=self.review_synthesizer(),
        )

    @crew
    def crew(self) -> Crew:
        """Create quick review crew."""
        return Crew(
            agents=[
                self.diff_intelligence_specialist(),
                self.code_quality_investigator(),
                self.review_synthesizer(),
            ],
            tasks=[
                self.parse_and_contextualize(),
                self.detect_code_issues(),
                self.synthesize_report(),
            ],
            process=Process.sequential,
            verbose=True,
            max_rpm=get_rate_limiter().current_limit,
        )
