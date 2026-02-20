"""CI log analysis crew with enhanced log intelligence."""

import logging

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from tools.ci_output_parser_tool import CIOutputParserTool
from tools.ci_tools import (
    check_log_size,
    get_log_stats,
    read_full_log,
    read_job_index,
    read_job_summary,
    search_log,
)
from tools.workspace_tool import WorkspaceTool
from utils.model_config import get_llm, get_rate_limiter

logger = logging.getLogger(__name__)


@CrewBase
class CILogAnalysisCrew:
    """CI log analysis crew with enhanced log intelligence."""

    agents_config = "../config/agents.yaml"
    tasks_config = "../config/tasks/ci_log_analysis_tasks.yaml"

    def __init__(self):
        """Initialize CI log analysis crew."""
        # Get LLM from centralized config
        self.llm = get_llm()
        logger.info(f"CILogAnalysis using model: {self.llm.model}")

    # --- AGENTS ---

    @agent
    def ci_pipeline_lead(self) -> Agent:
        """Create CI Pipeline Lead (Director)."""
        return Agent(
            config=self.agents_config["ci_pipeline_lead"],
            tools=[
                # Triage & Reporting tools
                read_job_index,
                read_job_summary,
                CIOutputParserTool(),
                WorkspaceTool(),
            ],
            llm=self.llm,
            function_calling_llm=self.llm,
            max_iter=10,
            verbose=True,
            allow_delegation=True,  # Director can delegate
        )

    @agent
    def log_pattern_specialist(self) -> Agent:
        """Create Log Pattern Specialist (Investigator)."""
        return Agent(
            config=self.agents_config["log_pattern_specialist"],
            tools=[
                # Heavy lifting log tools
                check_log_size,
                search_log,
                read_full_log,
                get_log_stats,
            ],
            llm=self.llm,
            function_calling_llm=self.llm,
            max_iter=15,  # Needs iterations for searching logs
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def error_resolution_specialist(self) -> Agent:
        """Create Error Resolution Specialist (Fixer)."""
        return Agent(
            config=self.agents_config["error_resolution_specialist"],
            tools=[],  # Pure analysis agent - relies on context
            llm=self.llm,
            function_calling_llm=self.llm,
            max_iter=5,
            verbose=True,
            allow_delegation=False,
        )

    # --- TASKS ---

    @task
    def triage_failures(self) -> Task:
        """Task 1: Identify failed jobs."""
        return Task(
            config=self.tasks_config["triage_failures"],
            agent=self.ci_pipeline_lead(),
        )

    @task
    def investigate_logs(self) -> Task:
        """Task 2: Extract error evidence."""
        return Task(
            config=self.tasks_config["investigate_logs"],
            agent=self.log_pattern_specialist(),
        )

    @task
    def determine_root_cause(self) -> Task:
        """Task 3: Analyze and recommend fixes."""
        return Task(
            config=self.tasks_config["determine_root_cause"],
            agent=self.error_resolution_specialist(),
        )

    @task
    def compile_ci_report(self) -> Task:
        """Task 4: Write final JSON report."""
        return Task(
            config=self.tasks_config["compile_ci_report"],
            agent=self.ci_pipeline_lead(),
            output_file="ci_summary.json",
        )

    @crew
    def crew(self) -> Crew:
        """Create CI log analysis crew."""
        return Crew(
            agents=[
                self.ci_pipeline_lead(),
                self.log_pattern_specialist(),
                self.error_resolution_specialist(),
            ],
            tasks=[
                self.triage_failures(),
                self.investigate_logs(),
                self.determine_root_cause(),
                self.compile_ci_report(),
            ],
            process=Process.sequential,
            verbose=True,
            max_rpm=get_rate_limiter().current_limit,
        )
