"""CrewAI crews for modular review workflows."""

# CRITICAL: Register Trinity model BEFORE importing any crew classes
# CrewAI checks model capabilities during class decoration, so this must happen first
from utils.model_config import register_trinity_model

register_trinity_model()

from crews.agentic_review_crew import AgenticReviewCrew  # noqa: E402
from crews.ci_log_analysis_crew import CILogAnalysisCrew  # noqa: E402
from crews.data_engineering_review_crew import DataEngineeringReviewCrew  # noqa: E402
from crews.documentation_review_crew import DocumentationReviewCrew  # noqa: E402
from crews.final_summary_crew import FinalSummaryCrew  # noqa: E402
from crews.finance_review_crew import FinanceReviewCrew  # noqa: E402
from crews.full_review_crew import FullReviewCrew  # noqa: E402
from crews.government_review_crew import GovernmentReviewCrew  # noqa: E402
from crews.legal_review_crew import LegalReviewCrew  # noqa: E402
from crews.marketing_review_crew import MarketingReviewCrew  # noqa: E402
from crews.quick_review_crew import QuickReviewCrew  # noqa: E402
from crews.router_crew import RouterCrew  # noqa: E402
from crews.science_review_crew import ScienceReviewCrew  # noqa: E402
from crews.security_review_crew import SecurityReviewCrew  # noqa: E402
from crews.strategy_review_crew import StrategyReviewCrew  # noqa: E402

__all__ = [
    "AgenticReviewCrew",
    "CILogAnalysisCrew",
    "DataEngineeringReviewCrew",
    "DocumentationReviewCrew",
    "FinanceReviewCrew",
    "FinalSummaryCrew",
    "FullReviewCrew",
    "GovernmentReviewCrew",
    "LegalReviewCrew",
    "MarketingReviewCrew",
    "QuickReviewCrew",
    "RouterCrew",
    "ScienceReviewCrew",
    "SecurityReviewCrew",
    "StrategyReviewCrew",
]
