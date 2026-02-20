"""Specialist crew registry and output schema utilities.

Central registry for all specialist review crews. Used by the router
for label-to-crew mapping, autodetect heuristics, and by main.py for
orchestration. Also provides schema validation for standardized JSON output.
"""

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Crew Registry
# ---------------------------------------------------------------------------

SPECIALIST_CREWS = {
    "security": {
        "label": "crewai:security",
        "output_file": "security_review.json",
        "agent_key": "owasp_sentinel",
        "id_prefix": "SEC",
        "crew_class": "SecurityReviewCrew",
        "module": "crews.security_review_crew",
        "description": "OWASP-grade security analysis",
    },
    "legal": {
        "label": "crewai:legal",
        "output_file": "legal_review.json",
        "agent_key": "license_counsel",
        "id_prefix": "LEGAL",
        "crew_class": "LegalReviewCrew",
        "module": "crews.legal_review_crew",
        "description": "License, copyright, and compliance review",
    },
    "finance": {
        "label": "crewai:finance",
        "output_file": "finance_review.json",
        "agent_key": "revenue_auditor",
        "id_prefix": "FIN",
        "crew_class": "FinanceReviewCrew",
        "module": "crews.finance_review_crew",
        "description": "Billing, payments, and financial controls",
    },
    "documentation": {
        "label": "crewai:docs",
        "output_file": "documentation_review.json",
        "agent_key": "docs_curator",
        "id_prefix": "DOC",
        "crew_class": "DocumentationReviewCrew",
        "module": "crews.documentation_review_crew",
        "description": "Documentation quality and completeness",
    },
    "agentic": {
        "label": "crewai:agentic",
        "output_file": "agentic_consistency_review.json",
        "agent_key": "agentic_steward",
        "id_prefix": "AGENT",
        "crew_class": "AgenticReviewCrew",
        "module": "crews.agentic_review_crew",
        "description": "AGENTS.md and agentic convention compliance",
    },
    "marketing": {
        "label": "crewai:marketing",
        "output_file": "marketing_review.json",
        "agent_key": "brand_editor",
        "id_prefix": "MKT",
        "crew_class": "MarketingReviewCrew",
        "module": "crews.marketing_review_crew",
        "description": "Brand copy, UX text, and messaging review",
    },
    "science": {
        "label": "crewai:science",
        "output_file": "science_review.json",
        "agent_key": "repro_scientist",
        "id_prefix": "SCI",
        "crew_class": "ScienceReviewCrew",
        "module": "crews.science_review_crew",
        "description": "Reproducibility, statistical rigor, data integrity",
    },
    "government": {
        "label": "crewai:government",
        "output_file": "government_regulatory_review.json",
        "agent_key": "public_sector_compliance",
        "id_prefix": "GOV",
        "crew_class": "GovernmentReviewCrew",
        "module": "crews.government_review_crew",
        "description": "WCAG, Section 508, audit trails, regulatory compliance",
    },
    "strategy": {
        "label": "crewai:strategy",
        "output_file": "strategic_review.json",
        "agent_key": "strategy_consultant",
        "id_prefix": "STRAT",
        "crew_class": "StrategyReviewCrew",
        "module": "crews.strategy_review_crew",
        "description": "Business impact, ROI, and strategic alignment",
    },
    "data_engineering": {
        "label": "crewai:data-engineering",
        "output_file": "data_engineering_review.json",
        "agent_key": "data_engineering_reviewer",
        "id_prefix": "DATA",
        "crew_class": "DataEngineeringReviewCrew",
        "module": "crews.data_engineering_review_crew",
        "description": "Data models, ETL/ELT jobs, query safety, and pipeline reliability",
    },
}

# Reverse lookup: label → crew key
LABEL_TO_CREW = {v["label"]: k for k, v in SPECIALIST_CREWS.items()}

# All specialist labels for router reference
ALL_SPECIALIST_LABELS = [v["label"] for v in SPECIALIST_CREWS.values()]

# ---------------------------------------------------------------------------
# Autodetect Heuristics (file path patterns → suggested crews)
# ---------------------------------------------------------------------------

AUTODETECT_RULES = {
    "security": {
        "path_patterns": [
            "auth",
            "session",
            "crypto",
            "security",
            "password",
            "token",
            "oauth",
            "jwt",
            "secret",
            "credential",
        ],
        "file_patterns": ["*.env*", "*secret*", "*key*"],
        "reason": "Security-sensitive files detected",
    },
    "legal": {
        "path_patterns": ["license", "notice", "copying", "terms", "legal", "privacy"],
        "file_patterns": ["LICENSE*", "NOTICE*", "COPYING*", "TERMS*"],
        "lockfile_trigger": True,
        "reason": "Legal/license files detected",
    },
    "finance": {
        "path_patterns": [
            "billing",
            "payment",
            "invoice",
            "subscription",
            "pricing",
            "stripe",
            "checkout",
            "currency",
            "price",
            "charge",
            "refund",
        ],
        "file_patterns": [],
        "reason": "Financial/billing code detected",
    },
    "documentation": {
        "path_patterns": ["docs", "doc", "readme", "changelog", "wiki", "guide"],
        "file_patterns": ["README*", "CHANGELOG*", "docs/**", "*.md"],
        "reason": "Documentation files detected",
    },
    "agentic": {
        "path_patterns": ["agentic", "agents", "crew", ".crewai"],
        "file_patterns": ["AGENTS.md", "agentic/**", ".crewai/**"],
        "reason": "Agentic configuration files detected",
    },
    "marketing": {
        "path_patterns": [
            "marketing",
            "landing",
            "copy",
            "campaign",
            "brand",
            "pricing",
            "plans",
        ],
        "file_patterns": [],
        "reason": "Marketing/user-facing copy detected",
    },
    "science": {
        "path_patterns": [
            "notebook",
            "experiment",
            "evaluation",
            "metric",
            "model",
            "dataset",
            "analysis",
            "research",
        ],
        "file_patterns": ["*.ipynb", "notebooks/**", "experiments/**"],
        "reason": "Scientific/research files detected",
    },
    "government": {
        "path_patterns": [
            "accessibility",
            "a11y",
            "wcag",
            "508",
            "aria",
            "compliance",
            "audit",
            "gov",
        ],
        "file_patterns": [],
        "ui_trigger": True,
        "reason": "Accessibility/government compliance files detected",
    },
    "strategy": {
        "path_patterns": [],
        "file_patterns": [],
        "reason": "Strategic review requested",
    },
    "data_engineering": {
        "path_patterns": [
            "data/sql",
            "migration",
            "schema",
            "warehouse",
            "pipeline",
            "etl",
            "elt",
            "dbt",
            "airflow",
            "dag",
            "bigquery",
            "snowflake",
            "redshift",
            "query",
            "database",
            "postgres",
            "mysql",
            "sqlite",
            "clickhouse",
        ],
        "file_patterns": ["*.sql", "dbt/**", "migrations/**", "data/**"],
        "reason": "Data engineering artifacts detected",
    },
}


# ---------------------------------------------------------------------------
# Output Schema Validation
# ---------------------------------------------------------------------------

SEVERITY_LEVELS = ("critical", "high", "medium", "low", "info")

FINDING_REQUIRED_KEYS = {"id", "title", "severity", "description", "recommendation"}
FINDING_OPTIONAL_KEYS = {"file", "line", "verification"}


def validate_specialist_output(data: dict, crew_key: str) -> list[str]:
    """Validate specialist crew JSON output against the standard schema.

    Args:
        data: Parsed JSON output from a specialist crew.
        crew_key: Key in SPECIALIST_CREWS (e.g. "security").

    Returns:
        List of validation error strings. Empty list means valid.
    """
    errors: list[str] = []
    prefix = SPECIALIST_CREWS.get(crew_key, {}).get("id_prefix", "???")

    # Top-level keys
    if "summary" not in data:
        errors.append("Missing required key: summary")
    elif not isinstance(data["summary"], str) or len(data["summary"]) < 20:
        errors.append("summary must be a string with at least 20 characters")

    if "severity_counts" not in data:
        errors.append("Missing required key: severity_counts")
    else:
        counts = data["severity_counts"]
        for level in SEVERITY_LEVELS:
            if level not in counts:
                errors.append(f"severity_counts missing level: {level}")
            elif not isinstance(counts[level], int):
                errors.append(f"severity_counts.{level} must be an integer")

    if "findings" not in data:
        errors.append("Missing required key: findings")
    elif not isinstance(data["findings"], list):
        errors.append("findings must be a list")
    else:
        for i, finding in enumerate(data["findings"]):
            if not isinstance(finding, dict):
                errors.append(f"findings[{i}] must be a dict")
                continue
            for key in FINDING_REQUIRED_KEYS:
                if key not in finding:
                    errors.append(f"findings[{i}] missing required key: {key}")
            if "severity" in finding and finding["severity"] not in SEVERITY_LEVELS:
                errors.append(f"findings[{i}].severity must be one of {SEVERITY_LEVELS}")
            if "id" in finding and not finding["id"].startswith(f"{prefix}-"):
                errors.append(
                    f"findings[{i}].id must start with '{prefix}-' (got '{finding['id']}')"
                )

    return errors


def get_all_output_files() -> list[str]:
    """Return all specialist output filenames for use in summary/suppression."""
    return [v["output_file"] for v in SPECIALIST_CREWS.values()]


def get_crew_for_label(label: str) -> str | None:
    """Look up crew key by label string."""
    return LABEL_TO_CREW.get(label)


def autodetect_crews(changed_files: list[str]) -> dict[str, str]:
    """Given a list of changed file paths, suggest specialist crews.

    Args:
        changed_files: List of file paths from the PR diff.

    Returns:
        Dict mapping crew_key → reason string for each suggested crew.
    """
    suggestions: dict[str, str] = {}
    lower_files = [f.lower() for f in changed_files]

    for crew_key, rules in AUTODETECT_RULES.items():
        # Check path patterns (substring match on any file)
        for pattern in rules.get("path_patterns", []):
            if any(pattern in f for f in lower_files):
                suggestions[crew_key] = rules["reason"]
                break

        # Already matched? Skip file_patterns
        if crew_key in suggestions:
            continue

        # Check lockfile trigger (legal crew)
        if rules.get("lockfile_trigger"):
            lockfiles = [
                "package-lock.json",
                "pnpm-lock.yaml",
                "yarn.lock",
                "poetry.lock",
                "Pipfile.lock",
                "Cargo.lock",
                "go.sum",
            ]
            if any(f.split("/")[-1] in lockfiles for f in lower_files):
                suggestions[crew_key] = "Lockfile changed — license check recommended"
                continue

        # Check UI trigger (government crew)
        if rules.get("ui_trigger"):
            ui_extensions = (".tsx", ".jsx", ".vue", ".svelte", ".html", ".css")
            if any(f.endswith(ext) for f in lower_files for ext in ui_extensions):
                suggestions[crew_key] = "UI components changed — accessibility check recommended"

    return suggestions
