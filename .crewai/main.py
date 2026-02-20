#!/usr/bin/env python3
"""Main orchestrator for CrewAI router-based review system."""

import json
import logging
import os
import re
import sys
import time
from datetime import datetime
from fnmatch import fnmatch
from pathlib import Path

# CRITICAL: Register models BEFORE importing any CrewAI components
# This must happen before CrewAI checks model capabilities during class decoration
from utils.model_config import get_model_config, get_rate_limit_delay, register_models

register_models()

# Configure LiteLLM for rate limit handling
import litellm  # noqa: E402

litellm.num_retries = 0
setattr(litellm, "request_timeout", 30)

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
from tools.cost_tracker import get_tracker  # noqa: E402
from tools.memory_manager import get_memory_manager  # noqa: E402
from tools.workspace_tool import WorkspaceTool  # noqa: E402
from utils.specialist_output import (  # noqa: E402
    AUTODETECT_RULES,
    SPECIALIST_CREWS,
    autodetect_crews,
    validate_specialist_output,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).parent.parent.resolve()
_REPO_FILE_BASENAME_INDEX = None
_REPO_RELATIVE_FILE_LIST = None
_REPO_TEXT_SNIPPET_CACHE = {}
_CHANGED_FILE_CANDIDATES = None
_LEGACY_ROOT_ARTIFACTS = [
    "ci_summary.json",
    "full_review.json",
    "security_review.json",
    "legal_review.json",
    "finance_review.json",
    "documentation_review.json",
    "agentic_consistency_review.json",
    "marketing_review.json",
    "science_review.json",
    "government_regulatory_review.json",
    "strategic_review.json",
    "data_engineering_review.json",
    "brand_analysis.json",
    "global_market_analysis.json",
    "license_analysis.json",
    "us_regulatory_analysis.json",
    "intl_trade_analysis.json",
    "strategy_analysis.json",
    "expansion_analysis.json",
    "code_quality_deep.json",
    "architecture_analysis.json",
    "security_deep_dive.json",
    "quick_review.json",
    "router_decision.json",
    "post_specialist_synthesis.json",
    "executive_synthesis.json",
    "context_pack.json",
    "diff_context.json",
]


def _get_review_labels() -> list[str]:
    diff_json_path = Path(__file__).parent / "workspace" / "diff.json"
    if not diff_json_path.exists():
        return []
    try:
        data = json.loads(diff_json_path.read_text())
    except Exception:
        return []
    labels = data.get("labels", [])
    if not isinstance(labels, list):
        return []
    return [str(label).strip() for label in labels if isinstance(label, str)]


def _is_complete_full_review_mode() -> bool:
    labels = {label.lower() for label in _get_review_labels()}
    return "crewai:complete-full-review" in labels


def _determine_review_mode(labels: set[str]) -> str:
    if "crewai:complete-full-review" in labels:
        return "complete-full-review"
    if "crewai:full-review" in labels:
        return "full-review"
    return "default"


def _score_specialist_candidates(changed_files: list[str]) -> dict[str, int]:
    lowered_files = [str(path).lower() for path in changed_files]
    scores: dict[str, int] = {crew_key: 0 for crew_key in SPECIALIST_CREWS}

    lockfiles = {
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "poetry.lock",
        "pipfile.lock",
        "cargo.lock",
        "go.sum",
    }
    ui_extensions = (".tsx", ".jsx", ".vue", ".svelte", ".html", ".css")

    for crew_key, rules in AUTODETECT_RULES.items():
        score = 0
        for pattern in rules.get("path_patterns", []):
            lowered_pattern = str(pattern).lower()
            if any(lowered_pattern in file_path for file_path in lowered_files):
                score += 2
        for pattern in rules.get("file_patterns", []):
            lowered_pattern = str(pattern).lower()
            if any(fnmatch(file_path, lowered_pattern) for file_path in lowered_files):
                score += 2
        if rules.get("lockfile_trigger") and any(
            file_path.split("/")[-1] in lockfiles for file_path in lowered_files
        ):
            score += 3
        if rules.get("ui_trigger") and any(
            file_path.endswith(ext) for file_path in lowered_files for ext in ui_extensions
        ):
            score += 2
        scores[crew_key] = score

    return scores


def _mode_aware_specialist_decision(
    labels: list[str],
    changed_files: list[str],
    additions: int = 0,
    deletions: int = 0,
    seed_specialists: list[str] | None = None,
    seed_suggestions: list[str] | None = None,
) -> tuple[list[str], list[str], list[str], str]:
    normalized_labels = {str(label).strip().lower() for label in labels}
    mode = _determine_review_mode(normalized_labels)

    label_to_specialist = {meta["label"]: crew for crew, meta in SPECIALIST_CREWS.items()}
    explicit_specialists = []
    for label in normalized_labels:
        crew_key = label_to_specialist.get(label)
        if crew_key and crew_key not in explicit_specialists:
            explicit_specialists.append(crew_key)

    autodetected = autodetect_crews(changed_files)
    candidate_scores = _score_specialist_candidates(changed_files)
    for crew_key in autodetected:
        candidate_scores[crew_key] = max(candidate_scores.get(crew_key, 0), 3)

    ranked_candidates = sorted(
        candidate_scores.items(),
        key=lambda item: (-item[1], item[0]),
    )

    specialists: list[str] = list(seed_specialists or [])
    suggestions: list[str] = list(seed_suggestions or [])
    workflows = ["ci-log-analysis", "quick-review"]

    if mode in {"full-review", "complete-full-review"}:
        workflows.append("full-review")

    if mode == "complete-full-review":
        specialists = list(SPECIALIST_CREWS.keys())
        suggestions.append(
            "complete-full-review mode: running all specialists with complete repository scope"
        )
    elif mode == "full-review":
        selected = []
        for crew_key, score in ranked_candidates:
            if score <= 0:
                continue
            if crew_key not in selected:
                selected.append(crew_key)
            if len(selected) >= 6:
                break
        for crew_key in explicit_specialists:
            if crew_key not in selected:
                selected.append(crew_key)
        if len(selected) < 3:
            for fallback in ["security", "documentation", "agentic"]:
                if fallback not in selected:
                    selected.append(fallback)
                if len(selected) >= 3:
                    break
        specialists = selected[:6]
    else:
        specialists = list(explicit_specialists)
        if not specialists:
            high_risk_autorun = {"security", "legal", "finance", "data_engineering", "government"}
            for crew_key, score in ranked_candidates:
                if crew_key in high_risk_autorun and score >= 4:
                    specialists = [crew_key]
                    break

    for crew_key, reason in sorted(autodetected.items()):
        label = SPECIALIST_CREWS[crew_key]["label"]
        suggestions.append(f"[{label}] recommended: {reason}")

    changed_count = len(changed_files)
    complexity_lines = int(additions or 0) + int(deletions or 0)
    if mode == "default" and (changed_count > 20 or complexity_lines > 500):
        suggestions.append(
            "[crewai:full-review] recommended: high diff complexity detected; broaden specialist depth"
        )

    deduped_specialists = []
    for crew_key in specialists:
        if crew_key in SPECIALIST_CREWS and crew_key not in deduped_specialists:
            deduped_specialists.append(crew_key)

    deduped_suggestions = []
    seen_suggestions = set()
    for suggestion in suggestions:
        cleaned = str(suggestion).strip()
        if not cleaned or cleaned in seen_suggestions:
            continue
        seen_suggestions.add(cleaned)
        deduped_suggestions.append(cleaned)

    return workflows, deduped_specialists, deduped_suggestions, mode


def _cleanup_root_artifact_leakage() -> None:
    crewai_root = Path(__file__).parent.resolve()
    removed = 0
    for filename in _LEGACY_ROOT_ARTIFACTS:
        candidate = crewai_root / filename
        if candidate.exists() and candidate.is_file():
            try:
                candidate.unlink()
                removed += 1
            except Exception as error:
                logger.warning(f"⚠️ Could not remove leaked root artifact {candidate}: {error}")
    if removed:
        logger.info(f"🧹 Removed {removed} leaked artifact file(s) from .crewai root")


class FatalLLMAvailabilityError(RuntimeError):
    pass


def _extract_text_payload(value):
    """Normalize provider payload values into plain text."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif isinstance(item.get("content"), str):
                    parts.append(item["content"])
        return "\n".join(p for p in parts if p).strip()
    if isinstance(value, dict):
        if isinstance(value.get("text"), str):
            return value["text"].strip()
        if isinstance(value.get("content"), str):
            return value["content"].strip()
    return ""


def _extract_json_object(text):
    """Extract the first parseable JSON object from arbitrary text."""
    if not text:
        return None

    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?", "", candidate, flags=re.IGNORECASE).strip()
        candidate = re.sub(r"```$", "", candidate).strip()

    try:
        json.loads(candidate)
        return candidate
    except Exception:
        pass

    start = candidate.find("{")
    while start != -1:
        depth = 0
        for idx in range(start, len(candidate)):
            ch = candidate[idx]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    snippet = candidate[start : idx + 1]
                    try:
                        json.loads(snippet)
                        return snippet
                    except Exception:
                        break
        start = candidate.find("{", start + 1)
    return None


def _build_repo_file_basename_index():
    index = {}
    skip_dirs = {".git", "node_modules", ".venv", "venv", "dist", "build", ".next"}
    for root, dirs, files in os.walk(_REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        root_path = Path(root)
        for file_name in files:
            rel_path = str((root_path / file_name).relative_to(_REPO_ROOT)).replace("\\", "/")
            index.setdefault(file_name, []).append(rel_path)
    return index


def _get_repo_relative_files():
    global _REPO_RELATIVE_FILE_LIST
    if _REPO_RELATIVE_FILE_LIST is not None:
        return _REPO_RELATIVE_FILE_LIST

    skip_dirs = {".git", "node_modules", ".venv", "venv", "dist", "build", ".next"}
    files = []
    for root, dirs, filenames in os.walk(_REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        root_path = Path(root)
        for file_name in filenames:
            rel_path = str((root_path / file_name).relative_to(_REPO_ROOT)).replace("\\", "/")
            files.append(rel_path)

    _REPO_RELATIVE_FILE_LIST = files
    return files


def _get_changed_file_candidates():
    global _CHANGED_FILE_CANDIDATES
    if _CHANGED_FILE_CANDIDATES is not None:
        return _CHANGED_FILE_CANDIDATES

    diff_json_path = Path(__file__).parent / "workspace" / "diff.json"
    candidates = []
    if diff_json_path.exists():
        try:
            diff_data = json.loads(diff_json_path.read_text())
            file_list = diff_data.get("file_list", [])
            if isinstance(file_list, list):
                candidates = [
                    str(file_name).replace("\\", "/")
                    for file_name in file_list
                    if isinstance(file_name, str)
                ]
        except Exception:
            candidates = []
    _CHANGED_FILE_CANDIDATES = candidates
    return candidates


def _qualify_repo_file_path(raw_path):
    global _REPO_FILE_BASENAME_INDEX

    file_path = str(raw_path or "").strip()
    if not file_path:
        return ""

    normalized = file_path.replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if not normalized:
        return ""

    abs_candidate = Path(normalized)
    if abs_candidate.is_absolute():
        try:
            return str(abs_candidate.resolve().relative_to(_REPO_ROOT)).replace("\\", "/")
        except Exception:
            return normalized

    rel_candidate = _REPO_ROOT / normalized
    if "/" in normalized and rel_candidate.exists():
        return normalized

    if "/" in normalized and not normalized.startswith("."):
        dotted_candidate = "." + normalized
        if (_REPO_ROOT / dotted_candidate).exists():
            return dotted_candidate

    if "/" not in normalized:
        changed_matches = [p for p in _get_changed_file_candidates() if Path(p).name == normalized]
        if len(changed_matches) == 1:
            return changed_matches[0]

        if _REPO_FILE_BASENAME_INDEX is None:
            _REPO_FILE_BASENAME_INDEX = _build_repo_file_basename_index()
        repo_matches = _REPO_FILE_BASENAME_INDEX.get(normalized, [])
        if len(repo_matches) == 1:
            return repo_matches[0]

    return normalized


def _read_repo_file_snippet(rel_path: str, max_chars: int = 900) -> str:
    candidate = (_REPO_ROOT / rel_path).resolve()
    try:
        if not candidate.is_file():
            return ""
        text = candidate.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

    if not text:
        return ""
    if len(text) > max_chars:
        return text[: max_chars - 40].rstrip() + "\n...\n[truncated]"
    return text


def _is_searchable_text_file(rel_path: str) -> bool:
    lowered = rel_path.lower()
    if "/.git/" in lowered or lowered.startswith(".git/"):
        return False
    if "/node_modules/" in lowered or lowered.startswith("node_modules/"):
        return False

    suffix = Path(lowered).suffix
    return suffix in {
        ".py",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".json",
        ".yml",
        ".yaml",
        ".md",
        ".txt",
        ".toml",
        ".ini",
        ".cfg",
        ".sql",
        ".sh",
        ".bash",
        ".zsh",
        ".dockerfile",
        ".env",
        ".example",
        ".lock",
    }


def _read_repo_text_for_search(rel_path: str, max_chars: int = 14000) -> str:
    if rel_path in _REPO_TEXT_SNIPPET_CACHE:
        return _REPO_TEXT_SNIPPET_CACHE[rel_path]

    candidate = (_REPO_ROOT / rel_path).resolve()
    text = ""
    try:
        if candidate.is_file() and candidate.stat().st_size <= 200_000:
            text = candidate.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        text = ""

    if len(text) > max_chars:
        text = text[:max_chars]

    _REPO_TEXT_SNIPPET_CACHE[rel_path] = text
    return text


def _build_specialist_probe_context(
    crew_key: str,
    domain_keywords: list[str],
    complete_mode: bool,
    max_files: int = 6,
    max_total_chars: int = 5200,
) -> tuple[str, list[str]]:
    rules = AUTODETECT_RULES.get(crew_key, {})
    path_patterns = [str(p).lower() for p in rules.get("path_patterns", [])]
    file_patterns = [str(p).lower() for p in rules.get("file_patterns", [])]
    keywords = [str(k).lower() for k in domain_keywords if isinstance(k, str)]

    def _matches(path: str) -> bool:
        lowered = path.lower()
        if any(pattern in lowered for pattern in path_patterns):
            return True
        if any(fnmatch(lowered, pattern) for pattern in file_patterns):
            return True
        return any(keyword in lowered for keyword in keywords)

    if complete_mode:
        max_files = max(max_files, 12)
        max_total_chars = max(max_total_chars, 10000)

    selected: list[str] = []
    reasons: dict[str, str] = {}

    def _add_candidate(path: str, reason: str):
        if not path or path in selected:
            return
        selected.append(path)
        reasons[path] = reason

    for changed_path in _get_changed_file_candidates():
        normalized = _qualify_repo_file_path(changed_path)
        if not normalized:
            continue
        if _matches(normalized):
            _add_candidate(normalized, "path/pattern match in changed files")
        if len(selected) >= max_files:
            break

    searchable_paths = []
    for changed_path in _get_changed_file_candidates():
        normalized = _qualify_repo_file_path(changed_path)
        if normalized and _is_searchable_text_file(normalized):
            searchable_paths.append(normalized)

    if complete_mode and len(selected) < max_files:
        for rel_path in _get_repo_relative_files():
            if not _is_searchable_text_file(rel_path):
                continue
            searchable_paths.append(rel_path)

    scanned = 0
    for rel_path in searchable_paths:
        if len(selected) >= max_files:
            break
        scanned += 1
        lowered_path = rel_path.lower()
        path_hits = [k for k in keywords if k and k in lowered_path]
        if path_hits and rel_path not in selected:
            _add_candidate(rel_path, f"path keyword match: {', '.join(path_hits[:3])}")
            continue

        text = _read_repo_text_for_search(rel_path)
        if not text:
            continue
        lowered_text = text.lower()
        content_hits = [k for k in keywords if k and k in lowered_text]
        if content_hits:
            _add_candidate(rel_path, f"content keyword match: {', '.join(content_hits[:3])}")

    if complete_mode and len(selected) < max_files:
        for rel_path in _get_repo_relative_files():
            if rel_path in selected:
                continue
            if _matches(rel_path):
                _add_candidate(rel_path, "fallback pattern match")
            if len(selected) >= max_files:
                break

    if not selected:
        return "", []

    listed_candidates = selected[: min(len(selected), 36)]

    lines = [
        "## Domain-specific repository probes",
        (
            "The following file excerpts were selected for this specialist domain. "
            "Use them as additional evidence, not as the only review source."
        ),
        (
            f"Scan mode: {'complete-repository' if complete_mode else 'changed-files-first'}; "
            f"search candidates scanned: {scanned}."
        ),
        "",
        "### Candidate files (domain-ranked)",
    ]

    for candidate in listed_candidates:
        lines.append(f"- {candidate}")
    lines.append("")
    lines.append("### Evidence excerpts")
    lines.append("")

    total_chars = 0
    for rel_path in selected:
        snippet = _read_repo_file_snippet(rel_path)
        if not snippet:
            continue
        reason = reasons.get(rel_path, "domain relevance")
        block = [f"### {rel_path} ({reason})", "```text", snippet, "```", ""]
        block_text = "\n".join(block)
        if total_chars + len(block_text) > max_total_chars and total_chars > 0:
            break
        lines.extend(block)
        total_chars += len(block_text)

    return "\n".join(lines).strip(), selected


def _specialist_probe_profile(crew_key: str, complete_mode: bool) -> tuple[int, int]:
    default_profiles = {
        "security": (7, 7000),
        "legal": (6, 6200),
        "finance": (6, 6200),
        "documentation": (8, 7600),
        "agentic": (8, 7600),
        "marketing": (7, 6800),
        "science": (7, 7000),
        "government": (7, 6800),
        "strategy": (8, 7600),
        "data_engineering": (9, 8200),
    }
    max_files, max_chars = default_profiles.get(crew_key, (7, 7000))
    if complete_mode:
        return int(max_files * 1.5), int(max_chars * 1.6)
    return max_files, max_chars


def _is_domain_specific_finding(finding: dict, domain_keywords: list[str]) -> bool:
    if not isinstance(finding, dict):
        return False
    combined_text = (
        f"{finding.get('title', '')} {finding.get('description', '')} "
        f"{finding.get('recommendation', '')} {finding.get('file', '')}"
    ).lower()
    if any(keyword in combined_text for keyword in domain_keywords):
        return True
    file_value = str(finding.get("file", "")).strip()
    return bool(file_value)


def _needs_refinement(parsed: dict, domain_keywords: list[str], complete_mode: bool) -> bool:
    if not complete_mode:
        return False
    findings = _normalize_findings_list(parsed.get("findings"))
    if not findings:
        return True

    specialized_count = sum(
        1 for finding in findings if _is_domain_specific_finding(finding, domain_keywords)
    )
    return specialized_count < max(1, len(findings) // 2)


def _clean_summary_text(summary_text):
    text = str(summary_text or "").strip()
    if not text:
        return ""

    text = re.sub(r"^json\s+", "", text, flags=re.IGNORECASE).strip()

    lower = text.lower()
    if lower.startswith("json"):
        nested = _extract_json_from_result(text, expected_keys=["summary", "critical", "warnings"])
        if isinstance(nested, dict):
            nested_summary = str(nested.get("summary", "")).strip()
            if nested_summary:
                text = nested_summary

    extracted = _extract_json_object(text)
    if extracted:
        try:
            nested_obj = json.loads(extracted)
            if isinstance(nested_obj, dict):
                nested_summary = str(nested_obj.get("summary", "")).strip()
                if nested_summary:
                    text = nested_summary
        except Exception:
            pass
    elif '"summary"' in text:
        regex_match = re.search(r'"summary"\s*:\s*"([^\"]+)', text)
        if regex_match:
            text = regex_match.group(1).strip()

    lowered = text.lower()
    if _looks_like_instruction_echo(text):
        return ""
    if _looks_like_json_blob(text):
        return ""
    if any(
        phrase in lowered
        for phrase in [
            "simulated",
            "assumed changed files",
            "hypothetical findings",
            "cannot complete the task",
            "non-json output; structured findings were not produced",
            "tool not found",
            "i should proceed",
            "assuming the",
            "you have not provided any files",
        ]
    ):
        return ""
    if re.search(r"\b1-3\s+sentences\b", lowered):
        return ""

    return " ".join(text.replace("```", " ").split())


def _looks_like_instruction_echo(text: str) -> bool:
    lowered = str(text or "").lower()
    if not lowered:
        return False

    markers = [
        "task:",
        "expected outcome:",
        "required tools:",
        "must do:",
        "must not do:",
        "required schema:",
        "return only json",
        "return json only",
        "step 1:",
        "step 2:",
        "output schema:",
    ]
    hits = sum(1 for marker in markers if marker in lowered)
    return hits >= 2


def _looks_like_json_blob(text: str) -> bool:
    raw = str(text or "").strip()
    if not raw:
        return False
    if raw.startswith("{") and raw.endswith("}"):
        return True
    if raw.lower().startswith("json {"):
        return True
    return raw.count("{") >= 2 and '"summary"' in raw


def _specialist_relevance(crew_key: str, complete_mode: bool = False) -> tuple[bool, str]:
    if complete_mode:
        return (
            True,
            "Complete full review mode enabled; specialist may review full repository scope.",
        )

    changed_files = [str(f).lower() for f in _get_changed_file_candidates() if isinstance(f, str)]
    if not changed_files:
        return False, "No changed files detected in this run."

    rules = AUTODETECT_RULES.get(crew_key, {})
    path_patterns = [str(p).lower() for p in rules.get("path_patterns", [])]
    file_patterns = [str(p) for p in rules.get("file_patterns", [])]

    for pattern in path_patterns:
        if any(pattern in file_path for file_path in changed_files):
            return True, f"Matched path pattern '{pattern}'."

    for file_pattern in file_patterns:
        if any(fnmatch(file_path, file_pattern.lower()) for file_path in changed_files):
            return True, f"Matched file pattern '{file_pattern}'."

    if rules.get("lockfile_trigger"):
        lockfiles = {
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "poetry.lock",
            "pipfile.lock",
            "cargo.lock",
            "go.sum",
        }
        if any(Path(file_path).name in lockfiles for file_path in changed_files):
            return True, "Matched lockfile trigger."

    if rules.get("ui_trigger"):
        ui_ext = (".tsx", ".jsx", ".vue", ".svelte", ".html", ".css")
        if any(file_path.endswith(ext) for file_path in changed_files for ext in ui_ext):
            return True, "Matched UI extension trigger."

    if crew_key == "strategy":
        return True, "Strategy review applies to changed business/product behavior by default."

    return False, "No domain-specific changed files detected for this specialist."


def _build_no_relevant_output(crew_key: str, reason: str) -> dict:
    return {
        "summary": (
            f"{crew_key.replace('_', ' ').title()} review did not detect relevant changed files "
            f"for this domain. {reason}"
        ),
        "severity_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
        "findings": [],
    }


def _sanitize_specialist_artifact(
    data: dict, crew_key: str, complete_mode: bool = False
) -> tuple[dict, bool]:
    sanitized = dict(data) if isinstance(data, dict) else {}
    changed = False

    cleaned_summary = _clean_summary_text(sanitized.get("summary", ""))
    if not cleaned_summary:
        cleaned_summary = (
            f"{crew_key.replace('_', ' ').title()} review completed with no actionable findings "
            "for this change set."
        )
    if cleaned_summary != str(sanitized.get("summary", "")).strip():
        changed = True
    sanitized["summary"] = cleaned_summary

    changed_files = [
        str(path).lower().lstrip("./")
        for path in _get_changed_file_candidates()
        if isinstance(path, str) and str(path).strip()
    ]
    changed_file_set = set(changed_files)
    changed_basename_set = {Path(path).name for path in changed_file_set}

    findings = _normalize_findings_list(sanitized.get("findings"))
    kept = []
    for index, finding in enumerate(findings, start=1):
        item = dict(finding)
        title = _clean_summary_text(item.get("title", ""))
        description = _clean_summary_text(item.get("description", ""))
        recommendation = _clean_summary_text(
            item.get("recommendation", item.get("fix_suggestion", ""))
        )
        verification = _clean_summary_text(item.get("verification", ""))

        lowered_title = title.lower()
        lowered_desc = description.lower()
        placeholder_like = (
            lowered_title in {"short title", "review finding"}
            or lowered_desc
            in {
                "why this matters",
                "no detailed description provided.",
            }
            or recommendation.lower()
            in {
                "concrete fix",
                "apply targeted remediation in changed files.",
            }
        )

        if not title and not description:
            changed = True
            continue
        if placeholder_like:
            changed = True
            continue

        qualified_file = _qualify_repo_file_path(item.get("file", ""))
        normalized_file = qualified_file.lower().lstrip("./") if qualified_file else ""
        if normalized_file and not complete_mode:
            file_matches_scope = (
                normalized_file in changed_file_set
                or Path(normalized_file).name in changed_basename_set
            )
            if not file_matches_scope:
                changed = True
                continue

        item["title"] = title or f"{crew_key.title()} finding {index}"
        item["description"] = description or "No additional details provided."
        item["recommendation"] = (
            recommendation or "Review the changed code and apply a targeted fix if needed."
        )
        if verification:
            item["verification"] = verification
        item["file"] = qualified_file
        kept.append(item)

    if len(kept) != len(findings):
        changed = True

    if (
        not kept
        and "did not detect relevant changed files" not in str(sanitized.get("summary", "")).lower()
    ):
        fallback_summary = (
            f"{crew_key.replace('_', ' ').title()} review completed with no actionable findings "
            "for this change set."
        )
        if sanitized.get("summary") != fallback_summary:
            changed = True
        sanitized["summary"] = fallback_summary

    sanitized["findings"] = kept
    sanitized["severity_counts"] = _compute_severity_counts(kept)
    return sanitized, changed


def _is_fatal_llm_availability_error(error: Exception) -> bool:
    message = str(error).lower()
    fatal_signatures = [
        "402",
        "insufficient credits",
        "out of credits",
        "quota exceeded",
        "no response",
        "none or empty",
        "empty response",
        "timed out",
        "timeout",
        "notfounderror",
        "404 page not found",
    ]
    return any(signature in message for signature in fatal_signatures)


def _raise_if_fatal_llm_error(stage: str, error: Exception) -> None:
    if _is_fatal_llm_availability_error(error):
        raise FatalLLMAvailabilityError(f"{stage} failed: {error}") from error


# Disable CrewAI tracing to prevent interactive prompts in CI
os.environ["CREWAI_TRACING_ENABLED"] = "false"


def setup_workspace():
    """Setup workspace directories.

    Uses absolute path based on this file's location to avoid CWD issues
    when workflow sets working-directory.
    """
    # Use absolute path: this file is in .crewai/, so workspace is .crewai/workspace
    workspace_dir = (Path(__file__).parent / "workspace").resolve()
    workspace_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"📁 Workspace initialized: {workspace_dir}")
    return workspace_dir


def get_env_vars():
    """Get required environment variables."""
    env_vars = {
        "pr_number": os.getenv("PR_NUMBER"),
        "commit_sha": os.getenv("COMMIT_SHA"),
        "repository": os.getenv("GITHUB_REPOSITORY"),
        "core_ci_result": os.getenv("CORE_CI_RESULT", "success"),
    }

    # Validate required vars
    if not env_vars["pr_number"]:
        logger.warning("PR_NUMBER not set - using mock mode")
        env_vars["pr_number"] = "999"

    if not env_vars["commit_sha"]:
        logger.warning("COMMIT_SHA not set - using mock mode")
        env_vars["commit_sha"] = "mock-sha"

    if not env_vars["repository"]:
        logger.warning("GITHUB_REPOSITORY not set - using mock mode")
        env_vars["repository"] = "owner/repo"

    logger.info(f"🎯 Environment: PR #{env_vars['pr_number']}, SHA {env_vars['commit_sha'][:7]}")
    logger.info(f"🎯 Repository: {env_vars['repository']}")
    logger.info(f"🎯 Core CI Result: {env_vars['core_ci_result']}")

    return env_vars


def get_workspace_diagnostics():
    """Get current workspace state for debugging.

    Returns:
        dict: Workspace state including files present and their sizes
    """
    try:
        workspace_dir = Path(__file__).parent / "workspace"

        files_info = {}
        if workspace_dir.exists():
            for file_path in workspace_dir.iterdir():
                if file_path.is_file():
                    files_info[file_path.name] = {"size": file_path.stat().st_size, "exists": True}

        return {
            "workspace_path": str(workspace_dir),
            "files": files_info,
            "file_count": len(files_info),
        }
    except Exception as e:
        return {"error": str(e)}


def run_router(env_vars):
    """Run router crew to decide workflows.

    Returns:
        dict: Router decision with workflows, suggestions, and metadata.
              Returns default workflows on failure.
    """
    logger.info("=" * 60)
    logger.info("🔀 STEP 1: Router - Analyzing PR and deciding workflows")
    logger.info("=" * 60)

    if env_vars.get("pr_number") == "local":
        workspace = WorkspaceTool()
        labels: list[str] = []
        changed_files: list[str] = []
        additions = 0
        deletions = 0
        if workspace.exists("diff.json"):
            try:
                diff_data = workspace.read_json("diff.json")
                labels = diff_data.get("labels", []) if isinstance(diff_data, dict) else []
                changed_files = (
                    diff_data.get("file_list", []) if isinstance(diff_data, dict) else []
                )
                additions = int(diff_data.get("additions", 0) or 0)
                deletions = int(diff_data.get("deletions", 0) or 0)
            except Exception:
                labels = []
                changed_files = []

        changed_files = [str(path) for path in changed_files if isinstance(path, str)]
        workflows, specialist, suggestions, mode = _mode_aware_specialist_decision(
            labels=labels,
            changed_files=changed_files,
            additions=additions,
            deletions=deletions,
        )

        decision = {
            "workflows": workflows,
            "specialist_crews": specialist,
            "suggestions": suggestions,
            "metadata": {
                "source": "local-short-circuit",
                "labels": labels,
                "mode": mode,
                "files_changed": len(changed_files),
                "lines_added": additions,
                "lines_removed": deletions,
            },
        }
        logger.info(f"✅ Local router shortcut: workflows={workflows}, specialist={specialist}")
        workspace.write_json("router_decision.json", decision)
        return decision

    # Track costs for this crew
    tracker = get_tracker()
    tracker.set_current_task("analyze_pr_and_route")

    try:
        router = RouterCrew()
        result = router.crew().kickoff(
            inputs={
                "pr_number": env_vars["pr_number"],
                "commit_sha": env_vars["commit_sha"],
                "repository": env_vars["repository"],
            }
        )

        # Debug: Log raw result
        logger.debug(f"Router result type: {type(result)}")
        logger.debug(f"Router result: {str(result)[:2000]}")

        # Read router decision from workspace
        workspace = WorkspaceTool()
        if workspace.exists("router_decision.json"):
            decision = workspace.read_json("router_decision.json")
            normalized_decision = dict(decision) if isinstance(decision, dict) else {}
            diff_data = workspace.read_json("diff.json") if workspace.exists("diff.json") else {}
            labels = diff_data.get("labels", []) if isinstance(diff_data, dict) else []
            changed_files = diff_data.get("file_list", []) if isinstance(diff_data, dict) else []
            additions = (
                int(diff_data.get("additions", 0) or 0) if isinstance(diff_data, dict) else 0
            )
            deletions = (
                int(diff_data.get("deletions", 0) or 0) if isinstance(diff_data, dict) else 0
            )
            seed_specialists = normalized_decision.get("specialist_crews", [])
            seed_suggestions = normalized_decision.get("suggestions", [])
            workflows, specialists, suggestions, mode = _mode_aware_specialist_decision(
                labels=labels if isinstance(labels, list) else [],
                changed_files=[str(path) for path in changed_files if isinstance(path, str)],
                additions=additions,
                deletions=deletions,
                seed_specialists=seed_specialists if isinstance(seed_specialists, list) else [],
                seed_suggestions=seed_suggestions if isinstance(seed_suggestions, list) else [],
            )
            normalized_decision["workflows"] = workflows
            normalized_decision["specialist_crews"] = specialists
            normalized_decision["suggestions"] = suggestions
            metadata = normalized_decision.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}
            metadata["mode"] = mode
            normalized_decision["metadata"] = metadata
            decision = normalized_decision
            workspace.write_json("router_decision.json", decision)
            logger.info(f"✅ Router decision: {decision.get('workflows', [])}")
            if decision.get("suggestions"):
                logger.info("💡 Router suggestions:")
                for suggestion in decision["suggestions"]:
                    logger.info(f"  - {suggestion}")

            # Debug: Log decision content
            logger.debug(f"Router decision content: {json.dumps(decision, indent=2)[:1000]}")
            return decision
        else:
            # Enhanced error logging with workspace diagnostics
            workspace_state = get_workspace_diagnostics()
            logger.warning(
                f"⚠️ Router did NOT write router_decision.json\n"
                f"  Agent: RouterCrew router_agent\n"
                f"  Workflow: analyze_pr_and_route\n"
                f"  Expected file: router_decision.json\n"
                f"  Workspace state: {json.dumps(workspace_state, indent=2)}"
            )

            logger.info("⚠️ Using default workflows due to missing router output")
            return {
                "workflows": ["ci-log-analysis", "quick-review"],
                "suggestions": [],
                "metadata": {},
            }

    except Exception as e:
        _raise_if_fatal_llm_error("router", e)
        workspace_state = get_workspace_diagnostics()
        logger.error(
            f"❌ Router failed: {e}\n"
            f"  Exception type: {type(e).__name__}\n"
            f"  Workspace state: {json.dumps(workspace_state, indent=2)}",
            exc_info=True,
        )
        # Return default workflows on failure
        return {
            "workflows": ["ci-log-analysis", "quick-review"],
            "suggestions": [f"⚠️ Router error: {str(e)}"],
            "metadata": {},
        }


def run_ci_analysis(env_vars):
    """Run CI log analysis crew.

    Returns:
        bool: True if analysis succeeded and produced output, False otherwise.
    """
    logger.info("=" * 60)
    logger.info("📊 STEP 2: CI Log Analysis - Parsing core-ci results")
    logger.info("=" * 60)

    if env_vars.get("pr_number") == "local":
        workspace = WorkspaceTool()
        diff_meta = workspace.read_json("diff.json") if workspace.exists("diff.json") else {}
        labels = diff_meta.get("labels", []) if isinstance(diff_meta, dict) else []
        files_changed = diff_meta.get("files_changed", 0) if isinstance(diff_meta, dict) else 0
        additions = diff_meta.get("additions", 0) if isinstance(diff_meta, dict) else 0
        deletions = diff_meta.get("deletions", 0) if isinstance(diff_meta, dict) else 0
        complete_mode = "crewai:complete-full-review" in [
            str(label).strip().lower() for label in (labels if isinstance(labels, list) else [])
        ]

        checks = [
            "local-short-circuit",
            "diff-metadata-loaded",
            "label-routing-ready",
        ]
        if complete_mode:
            checks.append("complete-full-review-mode")

        workspace.write_json(
            "ci_summary.json",
            {
                "status": env_vars["core_ci_result"],
                "passed": env_vars["core_ci_result"] == "success",
                "summary": (
                    f"Local run: core-ci marked {env_vars['core_ci_result']}; "
                    f"diff stats {files_changed} files (+{additions}/-{deletions}); "
                    f"mode={'complete-full-review' if complete_mode else 'standard-review'}"
                ),
                "critical_errors": [],
                "warnings": [],
                "checks_performed": checks,
                "metadata": {
                    "files_changed": files_changed,
                    "additions": additions,
                    "deletions": deletions,
                    "labels": labels if isinstance(labels, list) else [],
                },
            },
        )
        logger.info("✅ Local CI analysis shortcut: wrote deterministic ci_summary.json")
        return True

    # Track costs for this crew
    tracker = get_tracker()
    tracker.set_current_task("parse_ci_output")

    try:
        ci_crew = CILogAnalysisCrew()
        result = ci_crew.crew().kickoff(inputs={"core_ci_result": env_vars["core_ci_result"]})

        # Debug: Log raw result
        logger.debug(f"CI analysis result type: {type(result)}")
        logger.debug(f"CI analysis result: {str(result)[:2000]}")

        logger.info("✅ CI analysis complete")

        # Validate output file was created
        workspace = WorkspaceTool()
        if not workspace.exists("ci_summary.json"):
            workspace_state = get_workspace_diagnostics()
            logger.warning(
                f"⚠️ CI analysis did NOT write ci_summary.json\n"
                f"  Agent: CILogAnalysisCrew ci_analyst\n"
                f"  Workflow: parse_ci_output\n"
                f"  Expected file: ci_summary.json\n"
                f"  Workspace state: {json.dumps(workspace_state, indent=2)}"
            )

            workspace.write_json(
                "ci_summary.json",
                {
                    "status": env_vars["core_ci_result"],
                    "passed": env_vars["core_ci_result"] == "success",
                    "summary": f"Core CI: {env_vars['core_ci_result']}",
                    "critical_errors": [],
                    "warnings": [],
                },
            )
            return False
        else:
            # Debug: Log summary content
            summary = workspace.read_json("ci_summary.json")
            logger.debug(f"CI summary content: {json.dumps(summary, indent=2)[:1000]}")
            logger.info("✅ Verified ci_summary.json exists in workspace")
            return True

    except Exception as e:
        _raise_if_fatal_llm_error("ci-log-analysis", e)
        workspace_state = get_workspace_diagnostics()
        logger.error(
            f"❌ CI analysis failed: {e}\n"
            f"  Exception type: {type(e).__name__}\n"
            f"  Workspace state: {json.dumps(workspace_state, indent=2)}",
            exc_info=True,
        )
        # Write error to workspace
        workspace = WorkspaceTool()
        workspace.write_json(
            "ci_summary.json",
            {
                "status": "error",
                "error": str(e),
                "summary": "CI analysis failed",
            },
        )
        return False


def run_quick_review():
    """Run quick review crew.

    Returns:
        bool: True if review succeeded and produced output, False otherwise.
    """
    logger.info("=" * 60)
    logger.info("⚡ STEP 3: Quick Review - Fast code quality check")
    logger.info("=" * 60)

    workspace = WorkspaceTool()

    if os.getenv("PR_NUMBER") == "local":
        try:
            tracker = get_tracker()
            tracker.set_current_task("quick_code_review")

            diff_text = workspace.read("diff.txt") if workspace.exists("diff.txt") else ""
            commit_messages = (
                workspace.read("commit_messages.txt")
                if workspace.exists("commit_messages.txt")
                else ""
            )
            if len(diff_text) > 2000:
                diff_excerpt = diff_text[:1200] + "\n...\n" + diff_text[-800:]
            else:
                diff_excerpt = diff_text

            model_name = get_model_config().name
            openrouter_key = os.getenv("OPENROUTER_API_KEY")

            ci_summary = ""
            if workspace.exists("ci_summary.json"):
                try:
                    ci_summary = workspace.read_json("ci_summary.json").get("summary", "")
                except Exception:
                    ci_summary = ""

            def call_openrouter_quick_review(prompt_text, max_tokens):
                response = litellm.completion(
                    model=model_name,
                    api_key=openrouter_key,
                    base_url="https://openrouter.ai/api/v1",
                    messages=[{"role": "user", "content": prompt_text}],
                    max_tokens=max_tokens,
                    timeout=20,
                    num_retries=0,
                )
                choices = getattr(response, "choices", None)
                content_text_local = None
                if choices:
                    first_choice = choices[0]
                    message = getattr(first_choice, "message", None)
                    if message is not None:
                        content_text_local = _extract_text_payload(
                            getattr(message, "content", None)
                        )
                if not content_text_local:
                    raise RuntimeError("Invalid response from LLM call - None or empty content.")

                usage = getattr(response, "usage", None)
                tokens_in_local = int(getattr(usage, "prompt_tokens", 0) or 0)
                tokens_out_local = int(getattr(usage, "completion_tokens", 0) or 0)
                usage_cost_local = float(getattr(usage, "cost", 0.0) or 0.0)
                if usage_cost_local <= 0:
                    try:
                        usage_cost_local = float(
                            litellm.completion_cost(completion_response=response) or 0.0
                        )
                    except Exception:
                        usage_cost_local = 0.0

                return {
                    "content": content_text_local,
                    "tokens_in": tokens_in_local,
                    "tokens_out": tokens_out_local,
                    "cost": usage_cost_local,
                    "model": model_name,
                    "provider": "openrouter",
                }

            provider_calls = []

            def call_quick_review_model(prompt_text, max_tokens):
                llm_call_start = time.time()

                if openrouter_key:
                    result_payload = call_openrouter_quick_review(
                        prompt_text=prompt_text,
                        max_tokens=max_tokens,
                    )
                else:
                    raise RuntimeError("OPENROUTER_API_KEY is required for quick review.")

                llm_call_duration = max(time.time() - llm_call_start, 0.001)
                content_text = result_payload["content"]
                tokens_in_local = result_payload["tokens_in"]
                tokens_out_local = result_payload["tokens_out"]
                usage_cost_local = result_payload["cost"]
                model_used_local = result_payload["model"]
                provider_calls.append(result_payload["provider"])
                tracker.log_api_call(
                    model=model_used_local,
                    tokens_in=tokens_in_local,
                    tokens_out=tokens_out_local,
                    cost=usage_cost_local,
                    duration_seconds=llm_call_duration,
                )
                return content_text

            def normalize_finding_payload(item, reviewer_name, fallback_kind="info"):
                if not isinstance(item, dict):
                    item = {"description": str(item)}

                normalized = dict(item)
                title = str(normalized.get("title", "")).strip()
                description = str(normalized.get("description", "")).strip()
                fix_suggestion = str(
                    normalized.get("fix_suggestion", normalized.get("recommendation", ""))
                ).strip()
                recommendation_text = str(normalized.get("recommendation", "")).strip()
                verification_text = str(normalized.get("verification", "")).strip()

                description = _clean_summary_text(description)

                if not description:
                    description = "No additional details were provided by this reviewer pass."
                if title.endswith("..."):
                    title = ""
                if not title:
                    title = _derive_title_from_description(description, f"{reviewer_name} finding")
                if not fix_suggestion:
                    if fallback_kind == "positive":
                        fix_suggestion = "No action required; preserve this behavior."
                    elif fallback_kind == "warning":
                        fix_suggestion = (
                            "Review the related diff section and apply targeted remediation."
                        )
                    else:
                        fix_suggestion = "Consider this improvement in the next change set."

                normalized["title"] = title
                normalized["description"] = description
                normalized["fix_suggestion"] = fix_suggestion
                if recommendation_text and recommendation_text != fix_suggestion:
                    normalized["recommendation"] = recommendation_text
                else:
                    normalized.pop("recommendation", None)
                if verification_text:
                    normalized["verification"] = verification_text
                normalized["file"] = _qualify_repo_file_path(normalized.get("file", ""))
                normalized["source_reviewer"] = reviewer_name
                normalized.setdefault("kind", fallback_kind)
                normalized.setdefault("file", "")
                normalized.setdefault("line", "")
                return normalized

            def normalize_pass_payload(raw_content, reviewer_name):
                parsed_content = None
                try:
                    parsed_content = json.loads(raw_content)
                except json.JSONDecodeError:
                    extracted = _extract_json_object(raw_content)
                    if extracted:
                        try:
                            parsed_content = json.loads(extracted)
                        except json.JSONDecodeError:
                            parsed_content = None

                if not isinstance(parsed_content, dict):
                    parsed_content = {
                        "summary": (
                            "Review pass returned non-JSON output; structured findings were "
                            "not produced for this reviewer."
                        ),
                        "critical": [],
                        "warnings": [],
                        "info": [],
                        "positives": [],
                    }

                summary_text = _clean_summary_text(parsed_content.get("summary", ""))
                critical = [
                    normalize_finding_payload(i, reviewer_name, "critical")
                    for i in (parsed_content.get("critical", []) or [])
                ]
                warnings = [
                    normalize_finding_payload(i, reviewer_name, "warning")
                    for i in (parsed_content.get("warnings", []) or [])
                ]
                info = [
                    normalize_finding_payload(i, reviewer_name, "suggestion")
                    for i in (parsed_content.get("info", []) or [])
                ]
                positives = [
                    normalize_finding_payload(i, reviewer_name, "positive")
                    for i in (parsed_content.get("positives", []) or [])
                ]

                if summary_text and not any([critical, warnings, info, positives]):
                    generated_item = normalize_finding_payload(
                        {
                            "title": f"{reviewer_name} summary",
                            "description": summary_text,
                            "fix_suggestion": (
                                "No immediate action required unless this summary indicates risk."
                            ),
                        },
                        reviewer_name,
                        "warning" if reviewer_name == "Risk Reviewer" else "suggestion",
                    )
                    if reviewer_name == "Risk Reviewer":
                        warnings.append(generated_item)
                    else:
                        info.append(generated_item)

                if not summary_text:
                    total_items = len(critical) + len(warnings) + len(info) + len(positives)
                    if total_items > 0:
                        summary_text = (
                            f"{reviewer_name} produced {total_items} structured review finding(s)."
                        )
                    else:
                        text_hint = " ".join(str(raw_content).replace("```", " ").split())
                        if text_hint:
                            if len(text_hint) > 180:
                                text_hint = text_hint[:177].rstrip() + "..."
                            summary_text = text_hint
                        else:
                            summary_text = f"{reviewer_name} completed without structured findings."

                return {
                    "summary": summary_text,
                    "critical": critical,
                    "warnings": warnings,
                    "info": info,
                    "positives": positives,
                }

            reviewer_passes = [
                {
                    "name": "Diff Reviewer",
                    "prompt": (
                        "Return ONLY JSON with keys summary, critical, warnings, info, positives. "
                        "Find concrete code and logic defects in this diff.\n\n"
                        f"Diff excerpt:\n{diff_excerpt}"
                    ),
                    "max_tokens": 450,
                },
                {
                    "name": "Risk Reviewer",
                    "prompt": (
                        "Return ONLY JSON with keys summary, critical, warnings, info, positives. "
                        "Focus on security, reliability, and regression risks.\n\n"
                        f"CI Summary:\n{ci_summary}\n\n"
                        f"Diff excerpt:\n{diff_excerpt}"
                    ),
                    "max_tokens": 450,
                },
                {
                    "name": "Actionability Reviewer",
                    "prompt": (
                        "Return ONLY JSON with keys summary, critical, warnings, info, positives. "
                        "Focus on actionable improvements and test gaps.\n\n"
                        f"Commit messages:\n{commit_messages}\n\n"
                        f"Diff excerpt:\n{diff_excerpt}"
                    ),
                    "max_tokens": 450,
                },
            ]

            aggregated = {"critical": [], "warnings": [], "info": [], "positives": []}
            pass_summaries = []
            pass_details = []

            def prune_low_signal(items):
                markers = (
                    "no additional details were provided by this reviewer pass",
                    "reviewer pass returned no actionable details",
                )
                pruned = []
                for item in items or []:
                    if not isinstance(item, dict):
                        continue
                    title = str(item.get("title", "")).lower()
                    description = str(item.get("description", "")).lower()
                    if any(marker in title for marker in markers) or any(
                        marker in description for marker in markers
                    ):
                        continue
                    pruned.append(item)
                return pruned

            for review_pass in reviewer_passes:
                tracker.set_current_task(
                    f"quick_code_review_{review_pass['name'].lower().replace(' ', '_')}"
                )
                try:
                    raw_content = call_quick_review_model(
                        prompt_text=review_pass["prompt"],
                        max_tokens=review_pass["max_tokens"],
                    )
                    parsed = normalize_pass_payload(raw_content, review_pass["name"])

                    pass_total_findings = (
                        len(parsed.get("critical", []))
                        + len(parsed.get("warnings", []))
                        + len(parsed.get("info", []))
                        + len(parsed.get("positives", []))
                    )
                    if not str(parsed.get("summary", "")).strip() or pass_total_findings == 0:
                        retry_prompt = (
                            "Return ONLY JSON with keys summary, critical, warnings, info, "
                            "positives. Provide at least a one-sentence summary and at least "
                            "one finding unless there are truly no issues, in which case include "
                            "one positive note.\n\n" + review_pass["prompt"]
                        )
                        retry_content = call_quick_review_model(
                            prompt_text=retry_prompt,
                            max_tokens=review_pass["max_tokens"],
                        )
                        retry_parsed = normalize_pass_payload(retry_content, review_pass["name"])
                        retry_total = (
                            len(retry_parsed.get("critical", []))
                            + len(retry_parsed.get("warnings", []))
                            + len(retry_parsed.get("info", []))
                            + len(retry_parsed.get("positives", []))
                        )
                        if (
                            retry_total > pass_total_findings
                            or str(retry_parsed.get("summary", "")).strip()
                        ):
                            parsed = retry_parsed
                except Exception as pass_error:
                    logger.warning(
                        "⚠️ Quick review pass '%s' failed; normalizing empty result: %s",
                        review_pass["name"],
                        pass_error,
                    )
                    parsed = {
                        "summary": (
                            "Review pass encountered provider issues; "
                            "continuing with partial findings."
                        ),
                        "critical": [],
                        "warnings": [
                            {
                                "title": "Provider instability during review pass",
                                "file": "",
                                "line": "",
                                "description": str(pass_error),
                                "fix_suggestion": (
                                    "Re-run review or switch provider for this pass "
                                    "to improve finding completeness."
                                ),
                            }
                        ],
                        "info": [],
                        "positives": [],
                    }
                parsed_summary = str(parsed.get("summary") or "No summary provided.")
                parsed_total_findings = (
                    len(parsed.get("critical", []))
                    + len(parsed.get("warnings", []))
                    + len(parsed.get("info", []))
                    + len(parsed.get("positives", []))
                )
                low_signal_summary = (
                    "non-json output" in parsed_summary.lower() and parsed_total_findings == 0
                )

                if not low_signal_summary:
                    filtered_critical = prune_low_signal(parsed.get("critical", []))
                    filtered_warnings = prune_low_signal(parsed.get("warnings", []))
                    filtered_info = prune_low_signal(parsed.get("info", []))
                    filtered_positives = prune_low_signal(parsed.get("positives", []))

                    pass_summaries.append(
                        {
                            "reviewer": review_pass["name"],
                            "summary": parsed_summary,
                        }
                    )
                    pass_details.append(
                        {
                            "reviewer": review_pass["name"],
                            "summary": parsed_summary,
                            "critical": filtered_critical,
                            "warnings": filtered_warnings,
                            "suggestions": filtered_info,
                            "positives": filtered_positives,
                        }
                    )
                    aggregated["critical"].extend(filtered_critical)
                    aggregated["warnings"].extend(filtered_warnings)
                    aggregated["info"].extend(filtered_info)
                    aggregated["positives"].extend(filtered_positives)

            def dedupe_findings(items):
                deduped = []
                seen = set()
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    signature = (
                        item.get("title", ""),
                        item.get("file", ""),
                        str(item.get("line", "")),
                        item.get("description", ""),
                    )
                    if signature in seen:
                        continue
                    seen.add(signature)
                    deduped.append(item)
                return deduped

            def filter_low_signal_findings(items):
                low_signal_markers = (
                    "no additional details were provided by this reviewer pass",
                    "reviewer pass returned no actionable details",
                )
                filtered = []
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    title = str(item.get("title", "")).strip().lower()
                    description = str(item.get("description", "")).strip().lower()
                    if any(marker in title for marker in low_signal_markers) or any(
                        marker in description for marker in low_signal_markers
                    ):
                        continue
                    filtered.append(item)
                return filtered

            critical_items = filter_low_signal_findings(dedupe_findings(aggregated["critical"]))
            warning_items = filter_low_signal_findings(dedupe_findings(aggregated["warnings"]))
            info_items = filter_low_signal_findings(dedupe_findings(aggregated["info"]))
            positive_items = filter_low_signal_findings(dedupe_findings(aggregated["positives"]))

            provider_used = "openrouter"
            if provider_calls and not all(provider == "openrouter" for provider in provider_calls):
                provider_used = "openrouter"

            review_data = {
                "status": "completed",
                "summary": (
                    f"Local quick review completed with {len(reviewer_passes)} reviewer pass(es)."
                ),
                "critical": critical_items,
                "warnings": warning_items,
                "info": info_items,
                "positives": positive_items,
                "reviewer_summaries": pass_summaries,
                "reviewer_pass_details": pass_details,
                "provider_used": provider_used,
                "calls_executed": len(pass_summaries),
            }
            workspace.write_json("quick_review.json", review_data)
            logger.info("✅ Local quick review shortcut completed")
            return True
        except Exception as e:
            _raise_if_fatal_llm_error("quick-review", e)
            logger.error(f"❌ Local quick review shortcut failed: {e}", exc_info=True)
            workspace.write_json(
                "quick_review.json",
                {
                    "status": "error",
                    "error": str(e),
                    "summary": "Quick review failed",
                    "critical": [],
                    "warnings": [],
                    "info": [],
                },
            )
            return False

    # Track costs for this crew
    tracker = get_tracker()
    tracker.set_current_task("quick_code_review")

    try:
        quick_crew = QuickReviewCrew()
        result = quick_crew.crew().kickoff()

        # Debug: Log raw result
        logger.debug(f"Quick review result type: {type(result)}")
        logger.debug(f"Quick review result: {str(result)[:2000]}")

        logger.info("✅ Quick review task complete")

        # CRITICAL: Validate output file was created
        if not workspace.exists("quick_review.json"):
            workspace_state = get_workspace_diagnostics()
            logger.error(
                f"❌ CRITICAL: Quick review did NOT write quick_review.json!\n"
                f"  Agent: QuickReviewCrew code_reviewer\n"
                f"  Workflow: quick_code_review\n"
                f"  Expected file: quick_review.json\n"
                f"  Workspace state: {json.dumps(workspace_state, indent=2)}"
            )

            logger.warning("⚠️ Creating fallback quick_review.json with empty arrays")

            workspace.write_json(
                "quick_review.json",
                {
                    "status": "completed",
                    "summary": "Quick review completed but did not write structured output.",
                    "critical": [],
                    "warnings": [],
                    "info": [],
                },
            )
            return False
        else:
            # Validate the JSON has expected structure and log findings
            review_data = workspace.read_json("quick_review.json")
            total_findings = (
                len(review_data.get("critical", []))
                + len(review_data.get("warnings", []))
                + len(review_data.get("info", []))
            )
            logger.info(
                f"✅ Verified quick_review.json exists with {total_findings} total findings"
            )
            logger.info(f"   - Critical: {len(review_data.get('critical', []))}")
            logger.info(f"   - Warnings: {len(review_data.get('warnings', []))}")
            logger.info(f"   - Info: {len(review_data.get('info', []))}")

            # Debug: Log first few findings
            if review_data.get("critical"):
                logger.debug(
                    f"First critical issue: {json.dumps(review_data['critical'][0], indent=2)}"
                )

            return True

    except Exception as e:
        _raise_if_fatal_llm_error("quick-review", e)
        workspace_state = get_workspace_diagnostics()
        logger.error(
            f"❌ Quick review failed: {e}\n"
            f"  Exception type: {type(e).__name__}\n"
            f"  Workspace state: {json.dumps(workspace_state, indent=2)}",
            exc_info=True,
        )
        workspace = WorkspaceTool()
        workspace.write_json(
            "quick_review.json",
            {
                "status": "error",
                "error": str(e),
                "summary": "Quick review failed",
            },
        )
        return False


def run_full_review(env_vars):
    """Run full technical review crew.

    Returns:
        bool: True if review succeeded and produced output, False otherwise.
    """
    logger.info("=" * 60)
    logger.info("🔍 STEP 4: Full Technical Review - Deep analysis")
    logger.info("=" * 60)

    # Track costs for this crew
    tracker = get_tracker()
    tracker.set_current_task("full_technical_review")

    if env_vars.get("pr_number") == "local":
        success = _run_full_review_local(env_vars)
        if success:
            logger.info("✅ Local full review multi-pass completed")
        else:
            logger.warning("⚠️ Local full review multi-pass failed validation")
        return success

    try:
        full_crew = FullReviewCrew()
        result = full_crew.crew().kickoff(
            inputs={
                "pr_number": env_vars["pr_number"],
                "commit_sha": env_vars["commit_sha"],
                "repository": env_vars["repository"],
            }
        )

        # Debug: Log raw result
        logger.debug(f"Full review result type: {type(result)}")
        logger.debug(f"Full review result: {str(result)[:2000]}")

        logger.info("✅ Full review complete")

        # Validate output exists
        workspace = WorkspaceTool()
        if workspace.exists("full_review.json"):
            review_data = workspace.read_json("full_review.json")
            errors = _validate_full_review_output(review_data)
            if errors:
                logger.warning(
                    "⚠️ full_review.json failed validation; repairing from result payload"
                )
                review_data = synthesize_full_review_output(result)
                workspace.write_json("full_review.json", review_data)
                errors = _validate_full_review_output(review_data)

            _record_validation(
                "full_review.json",
                valid=len(errors) == 0,
                source="crew-output" if not errors else "parsed-result-repair",
                errors=errors,
                metadata={"workflow": "full-review"},
            )
            logger.debug(f"Full review data keys: {list(review_data.keys())}")
            return len(errors) == 0
        else:
            logger.warning("⚠️ Full review did not write full_review.json; persisting parsed result")
            synthesized = synthesize_full_review_output(result)
            workspace.write_json("full_review.json", synthesized)
            errors = _validate_full_review_output(synthesized)
            _record_validation(
                "full_review.json",
                valid=len(errors) == 0,
                source="parsed-result-missing-output",
                errors=errors,
                metadata={"workflow": "full-review"},
            )
            return len(errors) == 0

    except Exception as e:
        _raise_if_fatal_llm_error("full-review", e)
        workspace_state = get_workspace_diagnostics()
        logger.error(
            f"❌ Full review failed: {e}\n"
            f"  Exception type: {type(e).__name__}\n"
            f"  Workspace state: {json.dumps(workspace_state, indent=2)}",
            exc_info=True,
        )
        workspace = WorkspaceTool()
        workspace.write_json(
            "full_review.json",
            {
                "status": "error",
                "error": str(e),
                "summary": "Full review failed",
            },
        )
        _record_validation(
            "full_review.json",
            valid=False,
            source="execution-error",
            errors=[str(e)],
            metadata={"workflow": "full-review"},
        )
        return False


SPECIALIST_CREW_CLASSES = {
    "security": SecurityReviewCrew,
    "legal": LegalReviewCrew,
    "finance": FinanceReviewCrew,
    "documentation": DocumentationReviewCrew,
    "agentic": AgenticReviewCrew,
    "marketing": MarketingReviewCrew,
    "science": ScienceReviewCrew,
    "government": GovernmentReviewCrew,
    "strategy": StrategyReviewCrew,
    "data_engineering": DataEngineeringReviewCrew,
}


def _load_validation_report(workspace: WorkspaceTool) -> dict:
    if workspace.exists("validation_report.json"):
        data = workspace.read_json("validation_report.json")
        if isinstance(data, dict) and isinstance(data.get("artifacts"), list):
            return data
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "artifacts": [],
    }


def _record_validation(
    artifact: str,
    *,
    valid: bool,
    source: str,
    errors: list[str] | None = None,
    metadata: dict | None = None,
) -> None:
    workspace = WorkspaceTool()
    report = _load_validation_report(workspace)
    entries = [e for e in report["artifacts"] if e.get("artifact") != artifact]
    entries.append(
        {
            "artifact": artifact,
            "valid": valid,
            "source": source,
            "errors": errors or [],
            "metadata": metadata or {},
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        }
    )
    report["artifacts"] = entries
    report["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    workspace.write_json("validation_report.json", report)


def _normalize_findings_list(value):
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _compute_severity_counts(findings):
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for finding in findings:
        severity = str(finding.get("severity", "info")).lower()
        if severity not in counts:
            severity = "info"
        counts[severity] += 1
    return counts


def _validate_full_review_output(data: dict) -> list[str]:
    errors = []
    if not isinstance(data, dict):
        return ["full_review.json must be an object"]
    summary = data.get("summary")
    if not isinstance(summary, str) or len(summary.strip()) < 20:
        errors.append("summary must be a string with at least 20 characters")
    required_lists = ["architecture", "security", "performance", "testing"]
    for key in required_lists:
        if key not in data:
            errors.append(f"Missing required key: {key}")
            continue
        if not isinstance(data[key], list):
            errors.append(f"{key} must be a list")
    return errors


def _extract_json_from_result(result, expected_keys=None):
    """Extract best-effort JSON object from CrewAI result payloads."""

    def _candidate_texts(value):
        texts = []
        if value is None:
            return texts
        if isinstance(value, str):
            texts.append(value)
            return texts
        if isinstance(value, (dict, list)):
            try:
                texts.append(json.dumps(value))
            except Exception:
                pass
            return texts

        for attr in [
            "raw",
            "summary",
            "result",
            "output",
            "text",
            "content",
            "final_output",
            "json",
            "json_dict",
            "pydantic",
        ]:
            try:
                attr_value = getattr(value, attr)
            except Exception:
                continue
            if attr_value is None:
                continue
            if isinstance(attr_value, str):
                texts.append(attr_value)
            elif isinstance(attr_value, (dict, list)):
                try:
                    texts.append(json.dumps(attr_value))
                except Exception:
                    pass
            else:
                maybe_dump = getattr(attr_value, "model_dump", None)
                if callable(maybe_dump):
                    try:
                        texts.append(json.dumps(maybe_dump()))
                    except Exception:
                        pass

        tasks_output = getattr(value, "tasks_output", None)
        if isinstance(tasks_output, list):
            for task_output in tasks_output:
                texts.extend(_candidate_texts(task_output))

        texts.append(str(value))
        return texts

    for candidate in _candidate_texts(result):
        json_text = _extract_json_object(candidate)
        if not json_text:
            continue
        try:
            parsed = json.loads(json_text)
            if not isinstance(parsed, dict):
                continue
            if expected_keys and not any(key in parsed for key in expected_keys):
                continue
            return parsed
        except Exception:
            continue

    return {}


def _read_local_context_pack(workspace: WorkspaceTool, max_chars: int = 14000) -> str:
    memory_context = (
        workspace.read("memory_context.md") if workspace.exists("memory_context.md") else ""
    )

    def _combine_with_memory(base_context: str) -> str:
        if not memory_context.strip():
            return base_context
        if "## Persistent review memory" in base_context:
            return base_context
        return (
            base_context.rstrip()
            + "\n\n## Persistent review memory\n"
            + memory_context.strip()
            + "\n"
        )

    if workspace.exists("context_pack.md"):
        context = _combine_with_memory(workspace.read("context_pack.md"))
        if len(context) > max_chars:
            return context[: max_chars - 200] + "\n...\n[truncated context pack]"
        return context

    diff_text = workspace.read("diff.txt") if workspace.exists("diff.txt") else ""
    scope = workspace.read_json("scope.json") if workspace.exists("scope.json") else {}
    commits = workspace.read_json("commits.json") if workspace.exists("commits.json") else {}

    if len(diff_text) > max_chars:
        diff_text = diff_text[: max_chars - 200] + "\n...\n[truncated diff]"

    lines = [
        "# Context Pack",
        "",
        "## Scope",
        "- Tier: " + str(scope.get("tier", "unknown")),
        "- Diff strategy: " + str(scope.get("diff_strategy", "unknown")),
        "- Base ref: " + str(scope.get("base_ref", "unknown")),
        "",
        "## Commits",
    ]
    for msg in commits.get("commit_messages", [])[:8]:
        lines.append("- " + str(msg))
    lines.extend(["", "## Diff", "```diff", diff_text, "```"])
    return _combine_with_memory("\n".join(lines))


def _call_local_review_model(prompt_text: str, max_tokens: int, timeout_seconds: int = 30) -> dict:
    model_name = get_model_config().name
    openrouter_key = os.getenv("OPENROUTER_API_KEY")

    tracker = get_tracker()
    llm_call_start = time.time()

    def _log_usage(payload):
        llm_call_duration = max(time.time() - llm_call_start, 0.001)
        tracker.log_api_call(
            model=payload["model"],
            tokens_in=payload["tokens_in"],
            tokens_out=payload["tokens_out"],
            cost=payload["cost"],
            duration_seconds=llm_call_duration,
        )

    if not openrouter_key:
        raise RuntimeError("OPENROUTER_API_KEY is required for local structured review calls.")

    response = litellm.completion(
        model=model_name,
        api_key=openrouter_key,
        base_url="https://openrouter.ai/api/v1",
        messages=[{"role": "user", "content": prompt_text}],
        max_tokens=max_tokens,
        timeout=timeout_seconds,
        num_retries=0,
    )
    choices = getattr(response, "choices", None)
    content_text = None
    if choices:
        first_choice = choices[0]
        message = getattr(first_choice, "message", None)
        if message is not None:
            content_text = _extract_text_payload(getattr(message, "content", None))
    if not content_text:
        raise RuntimeError("Invalid response from LLM call - None or empty content.")

    usage = getattr(response, "usage", None)
    tokens_in = int(getattr(usage, "prompt_tokens", 0) or 0)
    tokens_out = int(getattr(usage, "completion_tokens", 0) or 0)
    usage_cost = float(getattr(usage, "cost", 0.0) or 0.0)
    if usage_cost <= 0:
        try:
            usage_cost = float(litellm.completion_cost(completion_response=response) or 0.0)
        except Exception:
            usage_cost = 0.0

    payload = {
        "content": content_text,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost": usage_cost,
        "model": model_name,
        "provider": "openrouter",
    }
    _log_usage(payload)
    return payload


def _request_json_with_retry(
    *,
    stage_name: str,
    context_text: str,
    schema_prompt: str,
    expected_keys: list[str],
    max_tokens: int = 1200,
) -> tuple[dict, str, list[str]]:
    tracker = get_tracker()
    last_errors: list[str] = []
    last_response = ""

    attempt_contexts = [context_text, context_text[:5000] + "\n...\n[reduced context]"]
    for attempt_index, context_candidate in enumerate(attempt_contexts, start=1):
        tracker.set_current_task(f"{stage_name}_attempt_{attempt_index}")
        prompt = (
            "Return JSON only. No markdown. No prose outside JSON.\n\n"
            + schema_prompt
            + "\n\nContext:\n"
            + context_candidate
        )
        if last_errors:
            prompt += (
                "\n\nPrevious validation errors:\n- "
                + "\n- ".join(last_errors[:5])
                + "\nFix these and return corrected JSON only."
            )
            if last_response:
                prompt += "\n\nPrevious response:\n" + last_response[:2000]

        response_payload = _call_local_review_model(
            prompt_text=prompt,
            max_tokens=max_tokens,
            timeout_seconds=30,
        )
        last_response = response_payload.get("content", "")
        parsed = _extract_json_from_result(last_response, expected_keys=expected_keys)
        if not parsed:
            last_errors = ["No parseable JSON object with expected keys"]
            continue

        missing = [key for key in expected_keys if key not in parsed]
        if missing:
            last_errors = ["Missing keys: " + ", ".join(missing)]
            continue
        return parsed, response_payload.get("provider", "unknown"), []

    return {}, "unknown", last_errors or ["Unable to produce valid JSON after targeted retry"]


def synthesize_full_review_output(result):
    """Synthesize full_review.json when crew did not persist file."""
    parsed = _extract_json_from_result(
        result,
        expected_keys=["architecture", "security", "performance", "testing", "summary"],
    )

    def _normalize(items):
        if isinstance(items, list):
            return [i for i in items if isinstance(i, dict)]
        return []

    synthesized = {
        "summary": parsed.get(
            "summary",
            "Full review completed; output persisted from crew response payload.",
        ),
        "architecture": _normalize(parsed.get("architecture")),
        "security": _normalize(parsed.get("security")),
        "performance": _normalize(parsed.get("performance")),
        "testing": _normalize(parsed.get("testing")),
    }
    if not synthesized["summary"]:
        synthesized["summary"] = "Full review persisted from parsed crew response."
    return synthesized


def synthesize_specialist_output(crew_key, result):
    """Synthesize specialist output when crew did not persist file."""
    parsed = _extract_json_from_result(
        result,
        expected_keys=["findings", "severity_counts", "summary"],
    )

    findings = parsed.get("findings", [])
    if not isinstance(findings, list):
        findings = []

    normalized_counts = _compute_severity_counts([f for f in findings if isinstance(f, dict)])

    synthesized = {
        "summary": parsed.get(
            "summary",
            f"{crew_key.title()} review completed; output persisted from crew response payload.",
        ),
        "severity_counts": normalized_counts,
        "findings": [f for f in findings if isinstance(f, dict)],
    }
    cleaned, _ = _sanitize_specialist_artifact(synthesized, crew_key)
    return cleaned


def _run_specialist_local(crew_key: str, output_file: str, complete_mode: bool = False) -> bool:
    workspace = WorkspaceTool()
    crew_info = SPECIALIST_CREWS[crew_key]
    context_text = _read_local_context_pack(workspace)
    domain_focus = {
        "security": {
            "focus": "vulnerabilities, authz/authn flaws, secret exposure, and exploit paths",
            "keywords": ["security", "auth", "token", "secret", "owasp", "xss", "injection"],
        },
        "legal": {
            "focus": "licenses, attribution obligations, redistribution/compliance, and regulatory/legal exposure",
            "keywords": ["license", "notice", "copyright", "compliance", "privacy", "terms"],
        },
        "finance": {
            "focus": "billing correctness, pricing/charge logic, revenue recognition, and payment safety",
            "keywords": [
                "billing",
                "payment",
                "invoice",
                "subscription",
                "price",
                "charge",
                "refund",
            ],
        },
        "documentation": {
            "focus": "docs accuracy/completeness, broken instructions, and mismatches with implemented behavior",
            "keywords": ["readme", "docs", "documentation", "changelog", "guide", "api docs"],
        },
        "agentic": {
            "focus": "AGENTS/agentic conventions, workflow integrity, and repo process contract compliance",
            "keywords": ["agentic", "agents", "workflow", "convention", "ci-local", "crewai"],
        },
        "marketing": {
            "focus": "messaging clarity, market positioning, conversion-risk copy, and brand/comms consistency",
            "keywords": ["copy", "messaging", "brand", "landing", "pricing", "plans", "cta"],
        },
        "science": {
            "focus": "reproducibility, data leakage, statistical validity, and measurement rigor",
            "keywords": ["experiment", "metric", "dataset", "model", "analysis", "reproduc"],
        },
        "government": {
            "focus": "accessibility and government/public-sector compliance (WCAG/508/auditability)",
            "keywords": ["accessibility", "wcag", "508", "aria", "audit", "compliance"],
        },
        "strategy": {
            "focus": "business impact, market/expansion implications, and strategic tradeoff quality",
            "keywords": ["strategy", "roi", "market", "expansion", "positioning", "roadmap"],
        },
        "data_engineering": {
            "focus": "schema/query correctness, pipeline reliability, and data model/contract risk",
            "keywords": ["sql", "schema", "migration", "etl", "pipeline", "warehouse", "query"],
        },
    }.get(
        crew_key,
        {
            "focus": crew_info.get("description", "domain-specific review"),
            "keywords": [],
        },
    )

    domain_keywords = [k.lower() for k in domain_focus.get("keywords", [])]
    probe_max_files, probe_max_chars = _specialist_probe_profile(crew_key, complete_mode)
    probe_context, probe_files = _build_specialist_probe_context(
        crew_key=crew_key,
        domain_keywords=domain_keywords,
        complete_mode=complete_mode,
        max_files=probe_max_files,
        max_total_chars=probe_max_chars,
    )
    review_context = context_text
    if probe_context:
        review_context = review_context + "\n\n" + probe_context

    schema_prompt = (
        "You are a domain specialist reviewer. "
        + crew_info.get("description", "Review changed code and provide actionable findings.")
        + "\nDomain focus: "
        + domain_focus["focus"]
        + (
            "\nReview scope: complete repository state (not only changed files)."
            if complete_mode
            else "\nReview scope: changed-code-first with selective broader context."
        )
        + "\nHard constraints:"
        + "\n- Do NOT report generic code-quality/style/architecture findings unless they directly create "
        + f"{crew_key} domain risk."
        + "\n- Avoid duplicating quick-review or full-review generic feedback."
        + "\n- If no true domain finding exists, return findings=[] and explain in summary why domain risk is low."
        + "\n- You may include at most one info-level educational FYI, but only if it is domain-specific."
        + "\n- In complete repository mode, inspect multiple domain-relevant files; do not rely on a single shared context block."
        + "\n- Every recommendation must be domain-specific and reference a concrete control, file, or process in this repository."
        + "\n- Avoid repeating advice that another specialist would own; stay in your domain lane."
        + "\n- Do not flag placeholder/example secrets in *.env.example files unless evidence suggests real credentials are committed."
        + "\nRequired schema:\n"
        + "{\n"
        + '  "summary": "1-3 sentence summary",\n'
        + '  "severity_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},\n'
        + '  "findings": [\n'
        + "    {\n"
        + f'      "id": "{crew_info.get("id_prefix", "FIND")}-001",\n'
        + '      "title": "Short title",\n'
        + '      "severity": "critical|high|medium|low|info",\n'
        + '      "file": "path/to/file",\n'
        + '      "description": "Why this matters",\n'
        + '      "recommendation": "Concrete fix",\n'
        + '      "verification": "How to verify"\n'
        + "    }\n"
        + "  ]\n"
        + "}\n"
        + (
            "Focus on full repository state and prioritize highest domain risk."
            if complete_mode
            else "Focus on changed code first; include broader context only when it changes domain risk materially."
        )
    )

    parsed, provider, parse_errors = _request_json_with_retry(
        stage_name=f"specialist_{crew_key}_local",
        context_text=review_context,
        schema_prompt=schema_prompt,
        expected_keys=["summary", "severity_counts", "findings"],
        max_tokens=1300,
    )
    if parse_errors:
        _record_validation(
            output_file,
            valid=False,
            source="local-structured-retry-failed",
            errors=parse_errors,
            metadata={"crew_key": crew_key, "provider": provider},
        )
        return False

    if _needs_refinement(parsed, domain_keywords, complete_mode):
        refine_prompt = (
            schema_prompt
            + "\nSecond-pass requirement: challenge the first-pass conclusions and tighten "
            "domain specificity. Keep only substantiated domain findings and include concrete file "
            "evidence where possible."
        )
        refine_context = (
            review_context + "\n\nFirst-pass JSON result:\n" + json.dumps(parsed, indent=2)
        )
        refined, refined_provider, refined_errors = _request_json_with_retry(
            stage_name=f"specialist_{crew_key}_local_refine",
            context_text=refine_context,
            schema_prompt=refine_prompt,
            expected_keys=["summary", "severity_counts", "findings"],
            max_tokens=1300,
        )
        if not refined_errors and refined:
            parsed = refined
            provider = refined_provider

    raw_findings = _normalize_findings_list(parsed.get("findings"))
    prefix = crew_info.get("id_prefix", "FIND")
    findings = []
    generic_markers = [
        "naming convention",
        "code style",
        "formatting issue",
        "refactor this",
        "separation of concerns",
        "maintainability",
        "generic best practice",
    ]
    for index, finding in enumerate(raw_findings, start=1):
        normalized = dict(finding)
        finding_id = str(normalized.get("id", "")).strip()
        if not finding_id.startswith(prefix):
            finding_id = f"{prefix}-{index:03d}"
        severity = str(normalized.get("severity", "info")).lower()
        if severity not in {"critical", "high", "medium", "low", "info"}:
            severity = "info"
        normalized["id"] = finding_id
        normalized["severity"] = severity
        normalized["title"] = (
            str(normalized.get("title", "Review finding")).strip() or "Review finding"
        )
        normalized["file"] = _qualify_repo_file_path(normalized.get("file", ""))
        normalized["description"] = (
            str(normalized.get("description", "No detailed description provided.")).strip()
            or "No detailed description provided."
        )
        normalized["recommendation"] = (
            str(
                normalized.get("recommendation", "Apply targeted remediation in changed files.")
            ).strip()
            or "Apply targeted remediation in changed files."
        )
        normalized["verification"] = (
            str(normalized.get("verification", "Re-run local review and relevant tests.")).strip()
            or "Re-run local review and relevant tests."
        )

        combined_text = (
            f"{normalized.get('title', '')} {normalized.get('description', '')} "
            f"{normalized.get('recommendation', '')} {normalized.get('file', '')}"
        ).lower()
        has_domain_signal = any(keyword in combined_text for keyword in domain_keywords)
        looks_generic = any(marker in combined_text for marker in generic_markers)
        if looks_generic and not has_domain_signal:
            continue

        findings.append(normalized)

    if not findings:
        baseline_title = f"{crew_key.replace('_', ' ').title()} baseline guardrail"
        baseline_desc = (
            "No direct high-severity domain risk detected in the current repository state. "
            f"Reviewed domain focus: {domain_focus['focus']}. "
            f"Domain probe files considered: {len(probe_files)}."
        )
        baseline_recommendation = (
            "Track this domain in subsequent cycles and re-evaluate after substantive changes."
        )
        findings.append(
            {
                "id": f"{prefix}-001",
                "title": baseline_title,
                "severity": "info",
                "file": "",
                "description": baseline_desc,
                "recommendation": baseline_recommendation,
                "verification": "Re-run complete full review and compare domain trend against prior run.",
            }
        )

    parsed["findings"] = findings
    parsed, _ = _sanitize_specialist_artifact(parsed, crew_key, complete_mode=complete_mode)
    findings = _normalize_findings_list(parsed.get("findings"))
    parsed["severity_counts"] = _compute_severity_counts(findings)
    if not isinstance(parsed.get("summary"), str) or not parsed.get("summary", "").strip():
        parsed["summary"] = f"{crew_key.title()} review completed with {len(findings)} finding(s)."

    validation_errors = validate_specialist_output(parsed, crew_key)
    workspace.write_json(output_file, parsed)
    _record_validation(
        output_file,
        valid=len(validation_errors) == 0,
        source="local-structured-review",
        errors=validation_errors,
        metadata={"crew_key": crew_key, "provider": provider, "findings": len(findings)},
    )
    return len(validation_errors) == 0


def _run_full_review_local(env_vars: dict) -> bool:
    workspace = WorkspaceTool()
    context_text = _read_local_context_pack(workspace)
    quick_json = (
        workspace.read_json("quick_review.json") if workspace.exists("quick_review.json") else {}
    )

    base_context = {
        "env": {
            "pr_number": env_vars.get("pr_number"),
            "commit_sha": env_vars.get("commit_sha"),
            "repository": env_vars.get("repository"),
        },
        "quick_review": quick_json,
    }

    quality_prompt = (
        "Perform deep code-quality review from diff/context and return JSON only.\n"
        "Schema:\n"
        "{\n"
        '  "summary": "1-2 sentence summary",\n'
        '  "quality_findings": [{"title":"...","severity":"critical|high|medium|low|info","file":"...","description":"...","recommendation":"..."}],\n'
        '  "performance_findings": [{"title":"...","severity":"critical|high|medium|low|info","file":"...","description":"...","recommendation":"..."}],\n'
        '  "testing_gaps": [{"title":"...","severity":"critical|high|medium|low|info","file":"...","description":"...","recommendation":"..."}],\n'
        '  "maintainability_findings": [{"title":"...","severity":"critical|high|medium|low|info","file":"...","description":"...","recommendation":"..."}]\n'
        "}"
    )
    quality_context = (
        context_text + "\n\nQuality review inputs:\n" + json.dumps(base_context, indent=2)
    )
    quality_json, provider_quality, quality_errors = _request_json_with_retry(
        stage_name="full_review_quality_local",
        context_text=quality_context,
        schema_prompt=quality_prompt,
        expected_keys=[
            "summary",
            "quality_findings",
            "performance_findings",
            "testing_gaps",
            "maintainability_findings",
        ],
        max_tokens=1500,
    )
    if quality_errors:
        _record_validation(
            "full_review.json",
            valid=False,
            source="local-full-review-quality-failed",
            errors=quality_errors,
            metadata={"provider": provider_quality},
        )
        return False
    workspace.write_json("code_quality_deep.json", quality_json)

    architecture_prompt = (
        "Perform architecture impact review from diff/context and quality outputs. Return JSON only.\n"
        "Schema:\n"
        "{\n"
        '  "summary": "1-2 sentence summary",\n'
        '  "architecture_findings": [{"title":"...","severity":"critical|high|medium|low|info","file":"...","description":"...","suggestion":"...","impact":"critical|high|medium|low"}],\n'
        '  "affected_modules": ["module/name"],\n'
        '  "breaking_changes_detected": false\n'
        "}"
    )
    architecture_context = (
        context_text
        + "\n\nArchitecture review inputs:\n"
        + json.dumps({"base": base_context, "code_quality": quality_json}, indent=2)
    )
    architecture_json, provider_arch, architecture_errors = _request_json_with_retry(
        stage_name="full_review_architecture_local",
        context_text=architecture_context,
        schema_prompt=architecture_prompt,
        expected_keys=[
            "summary",
            "architecture_findings",
            "affected_modules",
            "breaking_changes_detected",
        ],
        max_tokens=1500,
    )
    if architecture_errors:
        _record_validation(
            "full_review.json",
            valid=False,
            source="local-full-review-architecture-failed",
            errors=architecture_errors,
            metadata={"provider": provider_arch},
        )
        return False
    workspace.write_json("architecture_analysis.json", architecture_json)

    security_prompt = (
        "Perform OWASP/security and performance risk review from diff/context. Return JSON only.\n"
        "Schema:\n"
        "{\n"
        '  "summary": "1-2 sentence summary",\n'
        '  "critical_vulnerabilities": [{"title":"...","severity":"critical|high|medium|low|info","file":"...","description":"...","recommendation":"..."}],\n'
        '  "warnings": [{"title":"...","severity":"critical|high|medium|low|info","file":"...","description":"...","recommendation":"..."}],\n'
        '  "recommendations": [{"title":"...","severity":"critical|high|medium|low|info","file":"...","description":"...","recommendation":"..."}],\n'
        '  "owasp_categories_triggered": ["A01:2021"],\n'
        '  "hardcoded_secrets_found": false\n'
        "}"
    )
    security_context = (
        context_text
        + "\n\nSecurity review inputs:\n"
        + json.dumps({"base": base_context, "code_quality": quality_json}, indent=2)
    )
    security_json, provider_sec, security_errors = _request_json_with_retry(
        stage_name="full_review_security_local",
        context_text=security_context,
        schema_prompt=security_prompt,
        expected_keys=[
            "summary",
            "critical_vulnerabilities",
            "warnings",
            "recommendations",
            "owasp_categories_triggered",
            "hardcoded_secrets_found",
        ],
        max_tokens=1500,
    )
    if security_errors:
        _record_validation(
            "full_review.json",
            valid=False,
            source="local-full-review-security-failed",
            errors=security_errors,
            metadata={"provider": provider_sec},
        )
        return False
    workspace.write_json("security_deep_dive.json", security_json)

    synthesis_prompt = (
        "Synthesize final full_review.json from quality, architecture, and security analyses. "
        "Return JSON only with deduplicated findings and practical recommendations.\n"
        "Schema:\n"
        "{\n"
        '  "summary": "1-3 sentence executive summary",\n'
        '  "architecture": [{"title":"...","severity":"critical|high|medium|low|info","file":"...","description":"...","recommendation":"..."}],\n'
        '  "security": [{"title":"...","severity":"critical|high|medium|low|info","file":"...","description":"...","recommendation":"..."}],\n'
        '  "performance": [{"title":"...","severity":"critical|high|medium|low|info","file":"...","description":"...","recommendation":"..."}],\n'
        '  "testing": [{"title":"...","severity":"critical|high|medium|low|info","file":"...","description":"...","recommendation":"..."}]\n'
        "}"
    )
    synthesis_context = (
        context_text
        + "\n\nSynthesis inputs:\n"
        + json.dumps(
            {
                "base": base_context,
                "code_quality": quality_json,
                "architecture": architecture_json,
                "security": security_json,
            },
            indent=2,
        )
    )
    parsed, provider_syn, parse_errors = _request_json_with_retry(
        stage_name="full_review_synthesis_local",
        context_text=synthesis_context,
        schema_prompt=synthesis_prompt,
        expected_keys=["summary", "architecture", "security", "performance", "testing"],
        max_tokens=1600,
    )
    if parse_errors:
        _record_validation(
            "full_review.json",
            valid=False,
            source="local-full-review-synthesis-failed",
            errors=parse_errors,
            metadata={"provider": provider_syn},
        )
        return False

    for key in ["architecture", "security", "performance", "testing"]:
        parsed[key] = _normalize_findings_list(parsed.get(key))
    errors = _validate_full_review_output(parsed)
    workspace.write_json("full_review.json", parsed)
    _record_validation(
        "full_review.json",
        valid=len(errors) == 0,
        source="local-full-review-multipass",
        errors=errors,
        metadata={"provider": provider_syn},
    )
    return len(errors) == 0


def run_specialist_crew(crew_key, force_attempt: bool = False):
    """Run a single specialist review crew by registry key.

    Args:
        crew_key: Key in SPECIALIST_CREWS (e.g. "security", "legal").

    Returns:
        bool: True if crew succeeded and produced output.
    """
    crew_info = SPECIALIST_CREWS[crew_key]
    crew_class = SPECIALIST_CREW_CLASSES[crew_key]
    output_file = crew_info["output_file"]
    label = crew_info["label"]

    logger.info("=" * 60)
    logger.info(f"🔬 Specialist: {crew_key.title()} Review ({label})")
    logger.info("=" * 60)

    tracker = get_tracker()
    tracker.set_current_task(f"specialist_{crew_key}")
    complete_mode = _is_complete_full_review_mode()

    relevant, relevance_reason = _specialist_relevance(crew_key, complete_mode=complete_mode)
    if not relevant and not force_attempt and not complete_mode:
        workspace = WorkspaceTool()
        output = _build_no_relevant_output(crew_key, relevance_reason)
        workspace.write_json(output_file, output)
        _record_validation(
            output_file,
            valid=True,
            source="no-relevant-changes",
            metadata={"crew_key": crew_key, "reason": relevance_reason, "findings": 0},
        )
        logger.info(f"ℹ️ {crew_key.title()} review marked not-applicable: {relevance_reason}")
        return True
    if not relevant and (force_attempt or complete_mode):
        logger.info(
            f"ℹ️ {crew_key.title()} review forced for full-cycle guardrail check "
            f"despite limited file-match relevance: {relevance_reason}"
        )

    if os.getenv("PR_NUMBER") == "local":
        logger.info(
            f"ℹ️ Local specialist {crew_key}: running structured guardrail review"
            + (" (complete repo mode)" if complete_mode else "")
        )
        success = _run_specialist_local(crew_key, output_file, complete_mode=complete_mode)
        if success:
            logger.info(f"✅ Local specialist {crew_key} completed (structured local)")
        else:
            logger.warning(f"⚠️ Local specialist {crew_key} failed validation")
        return success

    try:
        crew_instance = crew_class()
        result = crew_instance.crew().kickoff()

        workspace = WorkspaceTool()
        source = "crew-output"
        if workspace.exists(output_file):
            data = workspace.read_json(output_file)
            data, _ = _sanitize_specialist_artifact(data, crew_key, complete_mode=complete_mode)
            validation_errors = validate_specialist_output(data, crew_key)
            if validation_errors:
                logger.warning(
                    f"⚠️ {crew_key.title()} output invalid; repairing from result payload"
                )
                source = "parsed-result-repair"
                data = synthesize_specialist_output(crew_key, result)
                workspace.write_json(output_file, data)
                data, _ = _sanitize_specialist_artifact(data, crew_key, complete_mode=complete_mode)
                validation_errors = validate_specialist_output(data, crew_key)
            if validation_errors:
                _record_validation(
                    output_file,
                    valid=False,
                    source=source,
                    errors=validation_errors,
                    metadata={"crew_key": crew_key},
                )
                logger.warning(
                    f"⚠️ {crew_key.title()} review output failed validation: "
                    + "; ".join(validation_errors[:3])
                )
                return False

            findings = _normalize_findings_list(data.get("findings"))
            counts = _compute_severity_counts(findings)
            data["findings"] = findings
            data["severity_counts"] = counts
            workspace.write_json(output_file, data)

            _record_validation(
                output_file,
                valid=True,
                source=source,
                metadata={"crew_key": crew_key, "findings": len(findings)},
            )
            counts = data.get("severity_counts", {})
            total = sum(counts.values()) if counts else 0
            logger.info(
                f"✅ {crew_key.title()} review complete: "
                f"{counts.get('critical', 0)} critical, "
                f"{counts.get('high', 0)} high, "
                f"{total} total findings"
            )
            return True
        else:
            logger.warning(
                f"⚠️ {crew_key.title()} review did not write {output_file}; persisting parsed result"
            )
            synthesized = synthesize_specialist_output(crew_key, result)
            synthesized, _ = _sanitize_specialist_artifact(
                synthesized, crew_key, complete_mode=complete_mode
            )
            workspace.write_json(output_file, synthesized)
            validation_errors = validate_specialist_output(synthesized, crew_key)
            _record_validation(
                output_file,
                valid=len(validation_errors) == 0,
                source="parsed-result-missing-output",
                errors=validation_errors,
                metadata={"crew_key": crew_key},
            )
            return len(validation_errors) == 0

    except Exception as e:
        _raise_if_fatal_llm_error(f"specialist-{crew_key}", e)
        logger.error(f"❌ {crew_key.title()} review failed: {e}", exc_info=True)
        workspace = WorkspaceTool()
        workspace.write_json(
            output_file,
            {
                "summary": f"{crew_key.title()} review failed: {str(e)}",
                "severity_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
                "findings": [],
            },
        )
        _record_validation(
            output_file,
            valid=False,
            source="execution-error",
            errors=[str(e)],
            metadata={"crew_key": crew_key},
        )
        return False


def run_final_summary(env_vars, workflows_executed):
    """Run final summary crew.

    Args:
        env_vars: Environment variables dictionary
        workflows_executed: List of workflows that were executed

    Returns:
        bool: True if summary was created successfully, False otherwise.
    """
    logger.info("=" * 60)
    logger.info("📋 STEP 6: Final Summary - Synthesizing all reviews")
    logger.info("=" * 60)

    if env_vars.get("pr_number") == "local":
        create_fallback_summary(Path(__file__).parent / "workspace", env_vars, workflows_executed)
        logger.info("✅ Local final summary shortcut completed")
        return True

    # Track costs for this crew
    tracker = get_tracker()
    tracker.set_current_task("synthesize_final_summary")

    try:
        # Count the number of reviews/workflows that were executed
        workflow_count = len(workflows_executed)

        summary_crew = FinalSummaryCrew()
        result = summary_crew.crew().kickoff(
            inputs={
                "pr_number": env_vars["pr_number"],
                "sha": env_vars["commit_sha"],
                "repository": env_vars["repository"],
                "time": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S UTC"
                ),  # Changed from timestamp to time
                "count": workflow_count,
                "list": ", ".join(workflows_executed),  # Changed from workflows to list
            }
        )

        # Debug: Log raw result
        logger.debug(f"Final summary result type: {type(result)}")
        logger.debug(f"Final summary result: {str(result)[:2000]}")

        logger.info("✅ Final summary complete")

        # Validate output exists
        workspace = WorkspaceTool()
        if workspace.exists("final_summary.md"):
            summary_content = workspace.read("final_summary.md")
            logger.debug(f"Final summary length: {len(summary_content)} chars")
            return True
        else:
            logger.warning("⚠️ Final summary did not write final_summary.md")
            return False

    except Exception as e:
        _raise_if_fatal_llm_error("final-summary", e)
        workspace_state = get_workspace_diagnostics()
        logger.error(
            f"❌ Final summary failed: {e}\n"
            f"  Exception type: {type(e).__name__}\n"
            f"  Workspace state: {json.dumps(workspace_state, indent=2)}",
            exc_info=True,
        )
        return False


def run_post_specialist_synthesis(workflows_executed):
    """Create a deterministic synthesis artifact after specialists complete.

    This runs after specialist crews (and suppression filtering) and before final summary.
    """
    logger.info("=" * 60)
    logger.info("🧩 STEP 5.7: Post-Specialist Synthesis")
    logger.info("=" * 60)

    workspace = WorkspaceTool()
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    try:
        rollup_rows = _specialist_rollup_rows(workspace)
        severity_totals = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for row in rollup_rows:
            for level in severity_totals:
                severity_totals[level] += int(row.get(level, 0) or 0)

        priority_items = _collect_priority_actions(workspace)
        top_priority = priority_items[:5]

        source_files = []
        for file_name in [
            "full_review.json",
            "security_review.json",
            "legal_review.json",
            "finance_review.json",
            "documentation_review.json",
            "agentic_consistency_review.json",
            "marketing_review.json",
            "science_review.json",
            "government_regulatory_review.json",
            "strategic_review.json",
            "data_engineering_review.json",
            "validation_report.json",
        ]:
            if workspace.exists(file_name):
                source_files.append(file_name)

        payload = {
            "generated_at": generated_at,
            "workflows_executed": list(workflows_executed),
            "summary": (
                "Post-specialist synthesis complete. "
                f"{len(top_priority)} priority item(s) extracted across "
                f"{len(source_files)} artifact(s)."
            ),
            "priority_actions": top_priority,
            "severity_totals": severity_totals,
            "specialist_rollup": rollup_rows,
            "source_files": source_files,
        }

        workspace.write_json("post_specialist_synthesis.json", payload)
        logger.info(
            "✅ Post-specialist synthesis complete: "
            f"{len(top_priority)} priority items, {len(rollup_rows)} specialist rows"
        )
        return True
    except Exception as e:
        logger.warning(f"⚠️ Post-specialist synthesis failed: {e}")
        return False


def _build_executive_synthesis_context(
    workspace: WorkspaceTool, workflows_executed: list[str], max_chars: int = 14000
) -> str:
    lines = [
        "# Review artifact context",
        "",
        "## Workflows executed",
    ]
    for workflow in workflows_executed:
        lines.append(f"- {workflow}")

    artifact_files = [
        "router_decision.json",
        "ci_summary.json",
        "quick_review.json",
        "full_review.json",
        "post_specialist_synthesis.json",
        "security_review.json",
        "legal_review.json",
        "finance_review.json",
        "documentation_review.json",
        "agentic_consistency_review.json",
        "marketing_review.json",
        "science_review.json",
        "government_regulatory_review.json",
        "strategic_review.json",
        "data_engineering_review.json",
        "validation_report.json",
    ]

    for file_name in artifact_files:
        if not workspace.exists(file_name):
            continue
        try:
            data = workspace.read_json(file_name)
            payload = json.dumps(data, ensure_ascii=True)
        except Exception:
            payload = workspace.read(file_name)
        lines.extend(["", f"## {file_name}", payload[:2200]])

    context = "\n".join(lines)
    if len(context) <= max_chars:
        return context
    return context[: max_chars - 200] + "\n...\n[truncated context]"


def run_executive_synthesis(workflows_executed):
    logger.info("=" * 60)
    logger.info("🧠 STEP 6.5: Executive Synthesis")
    logger.info("=" * 60)

    workspace = WorkspaceTool()
    context_text = _build_executive_synthesis_context(workspace, workflows_executed)

    schema_prompt = (
        "Return JSON with keys: executive_summary, priority_actions, summary_guidance.\n"
        "executive_summary: array of 3 concise sentences covering outcome, top risk, next action.\n"
        "priority_actions: array (max 5) of objects with keys: severity, source, title, file, why, action.\n"
        "summary_guidance: object with keys: first_section, must_read_artifacts, release_recommendation.\n"
        "Use only evidence from provided artifacts. If no critical/high findings, state that explicitly."
    )

    parsed, provider, errors = _request_json_with_retry(
        stage_name="synthesize_final_summary_executive",
        context_text=context_text,
        schema_prompt=schema_prompt,
        expected_keys=["executive_summary", "priority_actions", "summary_guidance"],
        max_tokens=1200,
    )

    if not parsed:
        logger.warning(
            "⚠️ Executive synthesis failed: "
            + ("; ".join(errors[:3]) if errors else "unknown error")
        )
        return False

    summary_lines = parsed.get("executive_summary", [])
    if not isinstance(summary_lines, list):
        summary_lines = []
    summary_lines = [
        _summarize_text(str(line), max_len=220) for line in summary_lines[:3] if str(line).strip()
    ]

    normalized_actions = []
    for item in parsed.get("priority_actions", [])[:5]:
        if not isinstance(item, dict):
            continue
        severity = str(item.get("severity", "info")).lower()
        if severity not in {"critical", "high", "medium", "low", "info"}:
            severity = "info"
        normalized_actions.append(
            {
                "severity": severity,
                "source": _summarize_text(item.get("source", "Review"), max_len=60),
                "title": _summarize_text(item.get("title", "Review finding"), max_len=120),
                "file": _qualify_repo_file_path(item.get("file", "")),
                "why": _summarize_text(item.get("why", ""), max_len=240),
                "action": _summarize_text(item.get("action", ""), max_len=240),
            }
        )

    guidance = parsed.get("summary_guidance", {})
    if not isinstance(guidance, dict):
        guidance = {}

    payload = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "provider": provider,
        "executive_summary": summary_lines,
        "priority_actions": normalized_actions,
        "summary_guidance": {
            "first_section": _summarize_text(
                guidance.get("first_section", "Executive summary"), max_len=80
            ),
            "must_read_artifacts": [
                _summarize_text(str(entry), max_len=80)
                for entry in guidance.get("must_read_artifacts", [])[:5]
                if str(entry).strip()
            ],
            "release_recommendation": _summarize_text(
                guidance.get("release_recommendation", "Proceed with standard validation gates."),
                max_len=180,
            ),
        },
    }

    workspace.write_json("executive_synthesis.json", payload)
    logger.info(
        "✅ Executive synthesis complete: "
        f"{len(summary_lines)} summary lines, {len(normalized_actions)} priority actions"
    )
    return True


def format_finding_item(finding, severity_emoji):
    """Format a single finding item with proper structure.

    Args:
        finding: Finding dictionary
        severity_emoji: Emoji to use for severity

    Returns:
        str: Formatted markdown for the finding
    """
    if not isinstance(finding, dict):
        raw_text = str(finding).strip()
        parsed = _extract_json_from_result(raw_text, expected_keys=["summary", "title"])
        if parsed:
            finding = parsed
        else:
            return f"- {severity_emoji} {raw_text}"

    lines = []
    normalized = _normalize_finding_for_display(finding)
    title = normalized.get("title", "Review finding")
    file_path = normalized.get("file", "")
    line_num = normalized.get("line", "")
    description = normalized.get("description", "")
    finding_kind = str(normalized.get("kind", "")).lower()
    fix_suggestion = normalized.get("fix_suggestion", "")
    verification = normalized.get("verification", "")

    # Title with file location
    if file_path:
        if line_num:
            lines.append(f"- {severity_emoji} **{title}** `{file_path}:{line_num}`")
        else:
            lines.append(f"- {severity_emoji} **{title}** `{file_path}`")
    else:
        lines.append(f"- {severity_emoji} **{title}**")

    # Description (indented)
    if description:
        lines.append(f"  - {description}")

    if fix_suggestion:
        if finding_kind == "positive":
            lines.append(f"  - ✅ **Note**: {fix_suggestion}")
        else:
            lines.append(f"  - 💡 **Fix**: {fix_suggestion}")

    if verification:
        lines.append(f"  - ✅ **Verify**: {verification}")

    return "\n".join(lines)


def _normalize_finding_for_display(finding):
    item = dict(finding) if isinstance(finding, dict) else {"description": str(finding)}

    title = _clean_summary_text(item.get("title", ""))
    description = _clean_summary_text(item.get("description", ""))
    summary_text = _clean_summary_text(item.get("summary", ""))
    recommendation = _clean_summary_text(item.get("recommendation", ""))
    fix_suggestion = _clean_summary_text(item.get("fix_suggestion", ""))
    verification = _clean_summary_text(item.get("verification", ""))

    if not description and summary_text:
        description = summary_text
    if not fix_suggestion and recommendation:
        fix_suggestion = recommendation

    if not title or title.lower() in {"review finding", "short title"}:
        title = _derive_title_from_description(description, "Review finding")

    title = title.replace("`", "").strip()
    title = _summarize_text(title, max_len=110)

    generic_fix_phrases = {
        "consider this improvement in the next change set.",
        "review the related diff section and apply targeted remediation.",
        "review the changed code and apply a targeted fix if needed.",
        "apply targeted remediation in changed files.",
    }
    if fix_suggestion.lower() in generic_fix_phrases:
        fix_suggestion = ""

    return {
        "title": title or "Review finding",
        "file": _qualify_repo_file_path(item.get("file", "")),
        "line": item.get("line", ""),
        "description": _summarize_text(description, max_len=320),
        "fix_suggestion": _summarize_text(fix_suggestion, max_len=240),
        "verification": _summarize_text(verification, max_len=200),
        "kind": item.get("kind", ""),
    }


def _dedupe_findings_for_display(items, max_items=None):
    deduped = []
    seen = set()
    for raw in items or []:
        normalized = _normalize_finding_for_display(raw)
        key = (
            normalized.get("title", "").lower(),
            normalized.get("description", "").lower(),
            normalized.get("file", "").lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(normalized)
    if max_items is not None:
        return deduped[:max_items]
    return deduped


def _severity_rank(level):
    normalized = str(level or "").lower()
    order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
    return order.get(normalized, 0)


def _summarize_text(value, max_len=180):
    cleaned = _clean_summary_text(value)
    if not cleaned:
        cleaned = " ".join(str(value or "").replace("```", " ").split())
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 1].rstrip() + "…"


def _derive_title_from_description(description, fallback):
    text = " ".join(str(description or "").split()).strip()
    if not text:
        return fallback

    sentence_break = len(text)
    for separator in [".", ";", "\n"]:
        index = text.find(separator)
        if index != -1:
            sentence_break = min(sentence_break, index)

    title = text[:sentence_break].strip() or text
    if len(title) > 120:
        shortened = title[:120]
        if " " in shortened:
            shortened = shortened.rsplit(" ", 1)[0]
        title = shortened.strip()

    return title or fallback


def _collect_priority_actions(workspace):
    items = []

    def push_item(source, severity, title, file_path, description, recommendation):
        items.append(
            {
                "source": source,
                "severity": str(severity or "info").lower(),
                "title": title or "Review finding",
                "file": _qualify_repo_file_path(file_path or ""),
                "description": _summarize_text(description),
                "recommendation": _summarize_text(recommendation),
            }
        )

    if workspace.exists("quick_review.json"):
        try:
            quick_data = workspace.read_json("quick_review.json")
            for issue in quick_data.get("critical", []) or []:
                if isinstance(issue, dict):
                    push_item(
                        "Quick Review",
                        issue.get("severity", "critical"),
                        issue.get("title", "Critical quick-review issue"),
                        issue.get("file", ""),
                        issue.get("description") or issue.get("summary", ""),
                        issue.get("fix_suggestion") or issue.get("recommendation", ""),
                    )
                else:
                    push_item(
                        "Quick Review",
                        "critical",
                        "Critical quick-review issue",
                        "",
                        str(issue),
                        "Review the diff section and apply targeted remediation.",
                    )

            for warning in quick_data.get("warnings", []) or []:
                if isinstance(warning, dict):
                    warning_severity = str(warning.get("severity", "")).lower() or "medium"
                    push_item(
                        "Quick Review",
                        warning_severity,
                        warning.get("title", "Quick-review warning"),
                        warning.get("file", ""),
                        warning.get("description") or warning.get("summary", ""),
                        warning.get("fix_suggestion") or warning.get("recommendation", ""),
                    )
                else:
                    push_item(
                        "Quick Review",
                        "medium",
                        "Quick-review warning",
                        "",
                        str(warning),
                        "Review this warning and decide whether to address it now.",
                    )
        except Exception as error:
            logger.warning(f"Could not extract quick-review priorities: {error}")

    if workspace.exists("full_review.json"):
        try:
            full_data = workspace.read_json("full_review.json")
            for section_name in ["architecture", "security", "performance", "testing"]:
                for finding in full_data.get(section_name, []) or []:
                    if not isinstance(finding, dict):
                        continue
                    severity = str(finding.get("severity", "info")).lower()
                    if _severity_rank(severity) < _severity_rank("high"):
                        continue
                    push_item(
                        "Full Review",
                        severity,
                        finding.get("title", f"{section_name.title()} finding"),
                        finding.get("file", ""),
                        finding.get("description", ""),
                        finding.get("recommendation", ""),
                    )
        except Exception as error:
            logger.warning(f"Could not extract full-review priorities: {error}")

    for crew_key, crew_info in SPECIALIST_CREWS.items():
        output_file = crew_info["output_file"]
        if not workspace.exists(output_file):
            continue
        try:
            data = workspace.read_json(output_file)
            crew_name = crew_key.replace("_", " ").title()
            for finding in data.get("findings", []) or []:
                if not isinstance(finding, dict):
                    continue
                severity = str(finding.get("severity", "info")).lower()
                if _severity_rank(severity) < _severity_rank("high"):
                    continue
                push_item(
                    crew_name,
                    severity,
                    finding.get("title", f"{crew_name} finding"),
                    finding.get("file", ""),
                    finding.get("description", ""),
                    finding.get("recommendation") or finding.get("fix_suggestion", ""),
                )
        except Exception as error:
            logger.warning(f"Could not extract {crew_key} priorities: {error}")

    unique_items = []
    seen = set()
    for item in items:
        key = (
            item["source"],
            item["severity"],
            item["title"],
            item["file"],
            item["description"],
        )
        if key in seen:
            continue
        seen.add(key)
        unique_items.append(item)

    high_signal_items = [
        item for item in unique_items if _severity_rank(item["severity"]) >= _severity_rank("high")
    ]

    high_signal_items.sort(
        key=lambda item: (
            -_severity_rank(item["severity"]),
            item["source"],
            item["title"],
        )
    )
    return high_signal_items


def _specialist_rollup_rows(workspace):
    rows = []
    for crew_key, crew_info in SPECIALIST_CREWS.items():
        output_file = crew_info["output_file"]
        if not workspace.exists(output_file):
            continue
        try:
            data = workspace.read_json(output_file)
            counts = data.get("severity_counts", {})
            row = {
                "crew": crew_key.replace("_", " ").title(),
                "critical": int(counts.get("critical", 0) or 0),
                "high": int(counts.get("high", 0) or 0),
                "medium": int(counts.get("medium", 0) or 0),
                "low": int(counts.get("low", 0) or 0),
                "info": int(counts.get("info", 0) or 0),
            }
            rows.append(row)
        except Exception as error:
            logger.warning(f"Could not parse specialist rollup for {crew_key}: {error}")

    rows.sort(key=lambda row: row["crew"])
    return rows


def create_fallback_summary(workspace_dir, env_vars, workflows_executed):
    """Create a comprehensive fallback summary extracting all available findings.

    Args:
        workspace_dir: Path to workspace directory
        env_vars: Environment variables
        workflows_executed: List of executed workflows
    """
    logger.info("🔧 Creating comprehensive fallback summary...")

    workspace = WorkspaceTool()

    summary_parts = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    summary_parts.append("# CrewAI Review Summary")
    summary_parts.append("")
    summary_parts.append(
        f"_PR #{env_vars['pr_number']} · `{env_vars['commit_sha'][:7]}` · "
        f"{env_vars['repository']} · {timestamp}_"
    )
    summary_parts.append("")
    summary_parts.append("---")
    summary_parts.append("")

    priority_items = _collect_priority_actions(workspace)
    executive_synthesis = {}
    if workspace.exists("executive_synthesis.json"):
        try:
            data = workspace.read_json("executive_synthesis.json")
            if isinstance(data, dict):
                executive_synthesis = data
        except Exception as e:
            logger.warning(f"Could not parse executive_synthesis.json: {e}")

    summary_parts.append("## 🧭 Executive summary")
    executive_lines = executive_synthesis.get("executive_summary", [])
    if isinstance(executive_lines, list):
        executive_lines = [str(line).strip() for line in executive_lines if str(line).strip()][:3]
    else:
        executive_lines = []

    if executive_lines:
        summary_parts.extend(executive_lines)
    elif priority_items:
        critical_count = sum(1 for item in priority_items if item.get("severity") == "critical")
        high_count = sum(1 for item in priority_items if item.get("severity") == "high")
        highest = priority_items[0]
        top_location = f" `{highest['file']}`" if highest.get("file") else ""
        actions_window = min(3, len(priority_items))
        summary_parts.append(
            f"Detected **{len(priority_items)}** high-priority finding(s) "
            f"({critical_count} critical, {high_count} high)."
        )
        summary_parts.append(
            f"Top risk: **{highest['source']} — {highest['title']}**{top_location}."
        )
        summary_parts.append(
            f"Immediate focus: complete Priority action items **1-{actions_window}** before merge, "
            "then rerun full review to confirm no critical/high regressions."
        )
    else:
        summary_parts.append("No critical or high findings were detected across current artifacts.")
        summary_parts.append(
            "Focus on medium-priority improvements and preserve current reliability safeguards."
        )
        summary_parts.append(
            "Rerun `./scripts/ci-local.sh --full-review --step review` after any substantive change."
        )
    summary_parts.append("")

    summary_parts.append("## 🎯 Priority action items")
    executive_actions = executive_synthesis.get("priority_actions", [])
    if isinstance(executive_actions, list) and executive_actions:
        for index, item in enumerate(executive_actions[:7], start=1):
            if not isinstance(item, dict):
                continue
            severity = str(item.get("severity", "info")).lower()
            severity_emoji = (
                "🔴" if severity == "critical" else "🟠" if severity == "high" else "🟡"
            )
            source = _summarize_text(item.get("source", "Review"), max_len=50)
            title = _summarize_text(item.get("title", "Review finding"), max_len=120)
            file_path = _qualify_repo_file_path(item.get("file", ""))
            location = f" `{file_path}`" if file_path else ""
            summary_parts.append(f"{index}. {severity_emoji} **[{source}] {title}**{location}")
            why = _summarize_text(item.get("why", ""), max_len=280)
            action = _summarize_text(item.get("action", ""), max_len=280)
            if why:
                summary_parts.append(f"   - Why it matters: {why}")
            if action:
                summary_parts.append(f"   - Recommended action: {action}")
    elif priority_items:
        for index, item in enumerate(priority_items[:7], start=1):
            severity_emoji = "🔴" if item["severity"] == "critical" else "🟠"
            location = f" `{item['file']}`" if item["file"] else ""
            summary_parts.append(
                f"{index}. {severity_emoji} **[{item['source']}] {item['title']}**{location}"
            )
            if item["description"]:
                summary_parts.append(f"   - Why it matters: {item['description']}")
            if item["recommendation"]:
                summary_parts.append(f"   - Recommended action: {item['recommendation']}")
    else:
        summary_parts.append(
            "1. ✅ No critical/high findings detected in available artifacts; continue with routine improvements and validation."
        )
    summary_parts.append("")

    rollup_rows = _specialist_rollup_rows(workspace)
    if rollup_rows:
        summary_parts.append("## 📊 Severity rollup")
        summary_parts.append("")
        summary_parts.append("| Crew | Critical | High | Medium | Low | Info |")
        summary_parts.append("| --- | ---: | ---: | ---: | ---: | ---: |")
        totals = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for row in rollup_rows:
            for key in totals:
                totals[key] += row[key]
            summary_parts.append(
                f"| {row['crew']} | {row['critical']} | {row['high']} | "
                f"{row['medium']} | {row['low']} | {row['info']} |"
            )
        summary_parts.append(
            f"| **Total** | **{totals['critical']}** | **{totals['high']}** | "
            f"**{totals['medium']}** | **{totals['low']}** | **{totals['info']}** |"
        )
        summary_parts.append("")

    summary_parts.append("## 🗺️ Workflow guide")
    summary_parts.append("")
    summary_parts.append("| Step | Purpose | Outcome | Recommendation |")
    summary_parts.append("| --- | --- | --- | --- |")

    # CI Analysis - Extract detailed findings
    if workspace.exists("ci_summary.json"):
        try:
            ci_data = workspace.read_json("ci_summary.json")
            status = ci_data.get("status", "unknown")
            passed = ci_data.get("passed", status == "success")
            status_emoji = "✅" if passed else "❌"
            summary_parts.append(
                f"| CI analysis | Parse CI outcomes and failures | {status_emoji} {status} | "
                + (
                    "Fix failing CI checks before code-level optimization."
                    if not passed
                    else "CI baseline is green; move to code-quality findings."
                )
                + " |"
            )
            summary_parts.append("")
            summary_parts.append("## ✅ CI analysis")
            summary_parts.append(f"**Status**: {status_emoji} {status}")

            # Get what was checked
            checks_performed = ci_data.get("checks_performed", [])
            if checks_performed:
                summary_parts.append(f"**Checks Performed**: {', '.join(checks_performed)}")

            summary_parts.append(f"**Summary**: {ci_data.get('summary', 'No summary available')}")

            # Extract issue analysis if available
            if "issue_analysis" in ci_data:
                analysis = ci_data["issue_analysis"]
                summary_parts.append("")
                summary_parts.append("**Issue Analysis**:")
                if analysis.get("root_cause"):
                    summary_parts.append(f"- **Root Cause**: {analysis['root_cause']}")
                if analysis.get("fix_applied"):
                    summary_parts.append(f"- **Fix Applied**: {analysis['fix_applied']}")
                if analysis.get("recommendation"):
                    summary_parts.append(f"- **Recommendation**: {analysis['recommendation']}")

            # Add critical errors if present
            critical_errors = ci_data.get("critical_errors", [])
            warnings = ci_data.get("warnings", [])

            if critical_errors or warnings:
                summary_parts.append("")
                summary_parts.append("<details>")
                summary_parts.append("<summary><b>🔍 View CI Issues</b></summary>")
                summary_parts.append("")

                if critical_errors:
                    summary_parts.append("**Critical Errors**:")
                    for idx, error in enumerate(critical_errors, 1):
                        error_type = (
                            error.get("type", "Error") if isinstance(error, dict) else "Error"
                        )
                        error_msg = (
                            error.get("message", str(error))
                            if isinstance(error, dict)
                            else str(error)
                        )
                        summary_parts.append(f"{idx}. **{error_type}**: {error_msg}")
                        if isinstance(error, dict) and error.get("fix_suggestion"):
                            summary_parts.append(f"   - 💡 **Fix**: {error['fix_suggestion']}")
                    summary_parts.append("")

                if warnings:
                    summary_parts.append("**Warnings**:")
                    for idx, warning in enumerate(warnings, 1):
                        warning_msg = (
                            warning.get("message", str(warning))
                            if isinstance(warning, dict)
                            else str(warning)
                        )
                        summary_parts.append(f"{idx}. {warning_msg}")
                    summary_parts.append("")

                summary_parts.append("</details>")

            summary_parts.append("")
        except Exception as e:
            logger.warning(f"Could not parse ci_summary.json: {e}")
            summary_parts.append(
                "| CI analysis | Parse CI outcomes and failures | ⚠️ parse error | "
                "Review `ci_summary.json` generation and parsing path. |"
            )
            summary_parts.append("")
            summary_parts.append("## ✅ CI analysis")
            summary_parts.append("Status: Error parsing results")
            summary_parts.append("")
    else:
        logger.warning("⚠️ ci_summary.json not found in workspace")
        summary_parts.append(
            "| CI analysis | Parse CI outcomes and failures | ⚠️ unavailable | "
            "Ensure `ci_summary.json` is produced in workflow execution. |"
        )
        summary_parts.append("")
        summary_parts.append("## ✅ CI analysis")
        summary_parts.append("Status: Not available")
        summary_parts.append("")

    # Quick Review - SHOW ALL FINDINGS with collapsible sections
    if workspace.exists("quick_review.json"):
        try:
            quick_data = workspace.read_json("quick_review.json")
            critical_count = len([i for i in quick_data.get("critical", []) if i])
            warning_count = len([i for i in quick_data.get("warnings", []) if i])
            suggestion_count = len([i for i in quick_data.get("info", []) if i])
            summary_parts.append(
                f"| Quick review | Fast multi-pass quality triage | "
                f"critical={critical_count}, warnings={warning_count}, suggestions={suggestion_count} | "
                + (
                    "Resolve critical items first, then warnings, then suggestions."
                    if critical_count or warning_count
                    else "No major blockers detected; proceed with deeper specialist validation."
                )
                + " |"
            )
            summary_parts.append("")
            summary_parts.append("## ⚡ Quick review")
            summary_parts.append(f"**Status**: {quick_data.get('status', 'completed')}")
            summary_parts.append(
                f"**Summary**: {_clean_summary_text(quick_data.get('summary', '')) or 'No summary available'}"
            )
            provider_used = quick_data.get("provider_used")
            calls_executed = quick_data.get("calls_executed")
            if provider_used:
                summary_parts.append(f"**Provider**: {provider_used}")
            if calls_executed is not None:
                summary_parts.append(f"**Reviewer Calls**: {calls_executed}")

            reviewer_summaries = quick_data.get("reviewer_summaries", [])
            if reviewer_summaries:
                summary_parts.append("")
                summary_parts.append("**Reviewer Pass Summaries**:")
                for pass_summary in reviewer_summaries:
                    if isinstance(pass_summary, dict):
                        reviewer_name = pass_summary.get("reviewer", "Reviewer")
                        reviewer_text = _clean_summary_text(
                            pass_summary.get("summary", "No summary provided.")
                        )
                        if not reviewer_text:
                            reviewer_text = "Summary suppressed due to low-signal content."
                        summary_parts.append(f"- **{reviewer_name}**: {reviewer_text}")
                    else:
                        summary_parts.append(f"- {pass_summary}")

            reviewer_details = quick_data.get("reviewer_pass_details", [])
            if reviewer_details:
                summary_parts.append("")
                summary_parts.append("<details>")
                summary_parts.append(
                    "<summary><b>🧩 Reviewer Task Breakdown "
                    + f"({len(reviewer_details)})"
                    + "</b></summary>"
                )
                summary_parts.append("")

                for detail in reviewer_details:
                    if not isinstance(detail, dict):
                        continue
                    reviewer_name = detail.get("reviewer", "Reviewer")
                    reviewer_summary = _clean_summary_text(
                        detail.get("summary", "No summary provided.")
                    )
                    if not reviewer_summary:
                        reviewer_summary = "Summary suppressed due to low-signal content."
                    reviewer_critical = [i for i in detail.get("critical", []) if i]
                    reviewer_warnings = [i for i in detail.get("warnings", []) if i]
                    reviewer_suggestions = [i for i in detail.get("suggestions", []) if i]
                    reviewer_positives = [i for i in detail.get("positives", []) if i]

                    summary_parts.append(f"**{reviewer_name}**")
                    summary_parts.append(f"- Summary: {reviewer_summary}")
                    summary_parts.append(
                        "- Findings: "
                        + f"{len(reviewer_critical)} critical, "
                        + f"{len(reviewer_warnings)} warnings, "
                        + f"{len(reviewer_suggestions)} suggestions, "
                        + f"{len(reviewer_positives)} positives"
                    )
                    summary_parts.append("")

                summary_parts.append("</details>")

            # Get all findings
            critical_issues = quick_data.get("critical", [])
            warnings = quick_data.get("warnings", [])
            suggestions = quick_data.get("info", [])
            positives = quick_data.get("positives", [])

            normalized_critical = _dedupe_findings_for_display([i for i in critical_issues if i])
            normalized_warnings = _dedupe_findings_for_display(
                [i for i in warnings if i], max_items=6
            )
            normalized_suggestions = _dedupe_findings_for_display(
                [i for i in suggestions if i], max_items=6
            )
            normalized_positives = _dedupe_findings_for_display(
                [i for i in positives if i], max_items=4
            )

            # High-level counts
            critical_count = len(normalized_critical)
            warning_count = len(normalized_warnings)
            info_count = len(normalized_suggestions)
            positive_count = len(normalized_positives)

            # CRITICAL ISSUES - always show if present
            if normalized_critical:
                summary_parts.append("")
                summary_parts.append("<details open>")
                summary_parts.append(
                    f"<summary><b>🔴 Critical Issues ({critical_count})</b></summary>"
                )
                summary_parts.append("")
                for issue in normalized_critical:
                    summary_parts.append(format_finding_item(issue, "🔴"))
                    summary_parts.append("")
                summary_parts.append("</details>")

            # WARNINGS - collapsible
            if normalized_warnings:
                summary_parts.append("")
                summary_parts.append("<details>")
                summary_parts.append(f"<summary><b>🟡 Warnings ({warning_count})</b></summary>")
                summary_parts.append("")
                for warning in normalized_warnings:
                    summary_parts.append(format_finding_item(warning, "🟡"))
                    summary_parts.append("")
                summary_parts.append("</details>")

            # SUGGESTIONS - collapsible
            if normalized_suggestions:
                summary_parts.append("")
                summary_parts.append("<details>")
                summary_parts.append(f"<summary><b>🔵 Suggestions ({info_count})</b></summary>")
                summary_parts.append("")
                for suggestion in normalized_suggestions:
                    summary_parts.append(format_finding_item(suggestion, "🔵"))
                    summary_parts.append("")
                summary_parts.append("</details>")

            if normalized_positives:
                summary_parts.append("")
                summary_parts.append("<details>")
                summary_parts.append(f"<summary><b>🟢 Positives ({positive_count})</b></summary>")
                summary_parts.append("")
                for positive in normalized_positives:
                    summary_parts.append(format_finding_item(positive, "🟢"))
                    summary_parts.append("")
                summary_parts.append("</details>")

            summary_parts.append("")
        except Exception as e:
            logger.warning(f"Could not parse quick_review.json: {e}")
            summary_parts.append(
                "| Quick review | Fast multi-pass quality triage | ⚠️ parse error | "
                "Review quick-review output serialization. |"
            )
            summary_parts.append("")
            summary_parts.append("## ⚡ Quick review")
            summary_parts.append("Status: Error parsing results")
            summary_parts.append("")
    else:
        logger.warning("⚠️ quick_review.json not found in workspace")
        summary_parts.append(
            "| Quick review | Fast multi-pass quality triage | ⚠️ unavailable | "
            "Ensure quick-review output file is generated. |"
        )
        summary_parts.append("")
        summary_parts.append("## ⚡ Quick review")
        summary_parts.append("Status: Not available")
        summary_parts.append("")

    # Full Review - Extract architectural and security findings
    if workspace.exists("full_review.json"):
        try:
            full_data = workspace.read_json("full_review.json")
            full_critical_high = 0
            for section_name in ["architecture", "security", "performance", "testing"]:
                for finding in full_data.get(section_name, []) or []:
                    if not isinstance(finding, dict):
                        continue
                    if _severity_rank(finding.get("severity", "info")) >= _severity_rank("high"):
                        full_critical_high += 1
            summary_parts.append(
                f"| Full technical review | Deep cross-domain architecture/security analysis | "
                f"high+ findings={full_critical_high} | "
                + (
                    "Address top architecture/security risks before merge."
                    if full_critical_high
                    else "No high-severity deep-review blockers detected."
                )
                + " |"
            )
            summary_parts.append("")
            summary_parts.append("## 🔍 Full technical review")
            summary_parts.append("")

            # Architecture issues
            arch_issues = full_data.get("architecture", [])
            critical_arch = [i for i in arch_issues if i.get("severity") == "critical"]
            if critical_arch:
                summary_parts.append("**Critical Architecture Issues**:")
                for idx, issue in enumerate(critical_arch[:2], 1):  # Top 2
                    summary_parts.append(f"{idx}. **{issue.get('title', 'Unknown')}**")
                    summary_parts.append(f"   - {issue.get('description', 'No description')}")
                summary_parts.append("")

            # Security vulnerabilities
            security_issues = full_data.get("security", [])
            critical_security = [
                i for i in security_issues if i.get("severity") in ["critical", "high"]
            ]
            if critical_security:
                summary_parts.append("**Security Vulnerabilities**:")
                for idx, issue in enumerate(critical_security[:2], 1):  # Top 2
                    severity_emoji = "🔴" if issue.get("severity") == "critical" else "🟡"
                    summary_parts.append(
                        f"{idx}. {severity_emoji} **{issue.get('title', 'Unknown')}**"
                    )
                    summary_parts.append(f"   - {issue.get('description', 'No description')}")
                summary_parts.append("")

        except Exception as e:
            logger.warning(f"Could not parse full_review.json: {e}")
            summary_parts.append(
                "| Full technical review | Deep cross-domain architecture/security analysis | "
                "⚠️ parse error | Validate full-review output schema. |"
            )
            summary_parts.append("")
            summary_parts.append("## 🔍 Full technical review")
            summary_parts.append("Status: Error parsing results")
            summary_parts.append("")
    else:
        if "full-review" in workflows_executed:
            logger.warning("⚠️ full_review.json not found but full-review was executed")
        summary_parts.append(
            "| Full technical review | Deep cross-domain architecture/security analysis | Did not run | "
            "Run full review when risk profile or scope requires deeper analysis. |"
        )
        summary_parts.append("")
        summary_parts.append("## 🔍 Full technical review")
        summary_parts.append("Status: Did not run")
        summary_parts.append("")

    summary_parts.append("")

    crew_emoji = {
        "security": "🛡️",
        "legal": "⚖️",
        "finance": "💰",
        "documentation": "📚",
        "agentic": "🤖",
        "marketing": "📢",
        "science": "🔬",
        "government": "🏛️",
        "strategy": "📊",
        "data_engineering": "🗄️",
    }
    for crew_key, crew_info in SPECIALIST_CREWS.items():
        output_file = crew_info["output_file"]
        if workspace.exists(output_file):
            try:
                data = workspace.read_json(output_file)
                emoji = crew_emoji.get(crew_key, "🔬")
                counts = data.get("severity_counts", {})
                count_str = ", ".join(
                    f"{counts.get(s, 0)} {s}"
                    for s in ["critical", "high", "medium"]
                    if counts.get(s, 0) > 0
                )
                pretty_crew_name = crew_key.replace("_", " ").title()
                header = f"{emoji} {pretty_crew_name} review"
                if count_str:
                    header += f" ({count_str})"
                summary_parts.append(f"## {header}")
                specialist_summary = _clean_summary_text(data.get("summary", ""))
                if not specialist_summary:
                    specialist_summary = "No actionable specialist summary provided."
                summary_parts.append(f"**Summary**: {specialist_summary}")
                summary_parts.append("")

                findings = data.get("findings", [])
                critical_high = [f for f in findings if f.get("severity") in ("critical", "high")]
                rest = [f for f in findings if f.get("severity") not in ("critical", "high")]

                if critical_high:
                    summary_parts.append("<details open>")
                    summary_parts.append(
                        f"<summary><b>🔴 Critical/High ({len(critical_high)})</b></summary>"
                    )
                    summary_parts.append("")
                    for finding in critical_high:
                        summary_parts.append(format_finding_item(finding, "🔴"))
                        summary_parts.append("")
                    summary_parts.append("</details>")
                    summary_parts.append("")

                if rest:
                    summary_parts.append("<details>")
                    summary_parts.append(f"<summary><b>Other Findings ({len(rest)})</b></summary>")
                    summary_parts.append("")
                    for finding in rest:
                        sev = finding.get("severity", "info")
                        sev_emoji = {"medium": "🟡", "low": "🔵", "info": "ℹ️"}.get(sev, "🔵")
                        summary_parts.append(format_finding_item(finding, sev_emoji))
                        summary_parts.append("")
                    summary_parts.append("</details>")
                    summary_parts.append("")
            except Exception as e:
                logger.warning(f"Could not parse {output_file}: {e}")

    if workspace.exists("router_decision.json"):
        try:
            router_data = workspace.read_json("router_decision.json")
            suggestions = router_data.get("suggestions", [])
            if suggestions:
                summary_parts.append("## 💡 Router suggestions")
                summary_parts.append("")
                for suggestion in suggestions:
                    summary_parts.append(f"- {suggestion}")
                summary_parts.append("")
        except Exception as e:
            logger.warning(f"Could not parse router_decision.json: {e}")

    if workspace.exists("validation_report.json"):
        try:
            validation = workspace.read_json("validation_report.json")
            artifacts = validation.get("artifacts", [])
            if artifacts:
                invalid = [a for a in artifacts if not a.get("valid")]
                summary_line = (
                    f"Validated {len(artifacts)} artifact(s): "
                    f"{len(artifacts) - len(invalid)} valid, {len(invalid)} invalid"
                )
                summary_parts.append("## ✅ Validation report")
                summary_parts.append(summary_line)
                summary_parts.append("")
                source_labels = {
                    "no-relevant-changes": "no relevant domain changes",
                    "local-parsed-result-missing-output": "parsed-result recovery",
                    "local-full-review": "local full review",
                    "local-crew-output": "crew output",
                }
                for artifact in artifacts:
                    status = "✅" if artifact.get("valid") else "⚠️"
                    source = artifact.get("source", "unknown")
                    source_display = source_labels.get(source, source)
                    summary_parts.append(
                        f"- {status} `{artifact.get('artifact')}` ({source_display})"
                    )
                summary_parts.append("")
        except Exception as e:
            logger.warning(f"Could not parse validation_report.json: {e}")

    summary_parts.append("## 🔗 Traceability")
    summary_parts.append("")
    for file_name in sorted(
        [
            "router_decision.json",
            "ci_summary.json",
            "quick_review.json",
            "full_review.json",
            "post_specialist_synthesis.json",
            "executive_synthesis.json",
            "security_review.json",
            "legal_review.json",
            "finance_review.json",
            "documentation_review.json",
            "agentic_consistency_review.json",
            "marketing_review.json",
            "science_review.json",
            "government_regulatory_review.json",
            "strategic_review.json",
            "data_engineering_review.json",
            "validation_report.json",
        ]
    ):
        if workspace.exists(file_name):
            summary_parts.append(f"- `{file_name}`")
    summary_parts.append("")
    summary_parts.append("---")
    summary_parts.append("")
    summary_parts.append(f"_Generated by CrewAI Router System · {timestamp}_")

    fallback_md = "\n".join(summary_parts)
    workspace.write("final_summary.md", fallback_md)
    logger.info(f"✅ Comprehensive fallback summary created ({len(fallback_md)} chars)")
    return fallback_md


def _fmt_running(tokens_in: int, tokens_out: int, total_tokens: int, cost: float) -> str:
    return f"{tokens_in:,}/{tokens_out:,}/{total_tokens:,}/${cost:.6f}"


def _cost_table_row(
    crew: str,
    agent: str,
    call: str,
    tokens_in: int,
    tokens_out: int,
    total_tokens: int,
    cost: float,
    crew_running: str = "",
    agent_running: str = "",
    global_running: str = "",
    *,
    bold_cost: bool = False,
) -> str:
    cost_cell = f"${cost:.6f}"
    if bold_cost:
        cost_cell = f"**{cost_cell}**"
    return (
        f"| {crew} | {agent} | {call} | {tokens_in:,} | {tokens_out:,} | "
        f"{total_tokens:,} | {cost_cell} | {crew_running} | {agent_running} | {global_running} |"
    )


def generate_cost_breakdown():
    """Generate a unified cost table with running totals by call, crew, and agent."""
    try:
        tracker = get_tracker()
        summary = tracker.get_summary()

        if summary["total_calls"] == 0:
            return "\n---\n\n## 💰 Cost and efficiency\n\nNo API calls recorded.\n"

        calls = sorted(tracker.calls, key=lambda call: call.call_number)
        crew_breakdown = summary.get("crew_breakdown", {})
        agent_breakdown = summary.get("agent_breakdown", {})

        crew_rows = sorted(
            crew_breakdown.items(),
            key=lambda item: item[1].get("cost", 0.0),
            reverse=True,
        )
        agent_rows = sorted(
            agent_breakdown.items(),
            key=lambda item: item[1].get("cost", 0.0),
            reverse=True,
        )

        lines = [
            "",
            "---",
            "",
            "## 💰 Cost and efficiency",
            "",
            (
                f"- Final total cost: **${summary['total_cost']:.6f}** "
                f"across **{summary['total_calls']}** calls"
            ),
            (
                "- Final total tokens: "
                f"**{summary['total_tokens_in']:,} in / {summary['total_tokens_out']:,} out "
                f"/ {summary['total_tokens']:,} total**"
            ),
        ]

        if crew_rows:
            lines.append(
                f"- Top crew total: **{crew_rows[0][0]}** at **${crew_rows[0][1].get('cost', 0.0):.6f}**"
            )
        if agent_rows:
            lines.append(
                f"- Top agent total: **{agent_rows[0][0]}** at **${agent_rows[0][1].get('cost', 0.0):.6f}**"
            )

        lines.extend(
            [
                "",
                "| Crew | Agent | Call | Input | Output | Tokens | Cost | Crew running (in/out/tok/$) | Agent running (in/out/tok/$) | Global running (in/out/tok/$) |",
                "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |",
            ]
        )

        global_in = 0
        global_out = 0
        global_tokens = 0
        global_cost = 0.0
        crew_running = {}
        agent_running = {}

        for call in calls:
            global_in += call.tokens_in
            global_out += call.tokens_out
            global_tokens += call.total_tokens
            global_cost += call.cost

            crew_state = crew_running.setdefault(
                call.crew_name,
                {"in": 0, "out": 0, "tokens": 0, "cost": 0.0},
            )
            crew_state["in"] += call.tokens_in
            crew_state["out"] += call.tokens_out
            crew_state["tokens"] += call.total_tokens
            crew_state["cost"] += call.cost

            agent_state = agent_running.setdefault(
                call.agent_name,
                {"in": 0, "out": 0, "tokens": 0, "cost": 0.0},
            )
            agent_state["in"] += call.tokens_in
            agent_state["out"] += call.tokens_out
            agent_state["tokens"] += call.total_tokens
            agent_state["cost"] += call.cost

            lines.append(
                _cost_table_row(
                    crew=call.crew_name,
                    agent=call.agent_name,
                    call=f"#{call.call_number}",
                    tokens_in=call.tokens_in,
                    tokens_out=call.tokens_out,
                    total_tokens=call.total_tokens,
                    cost=call.cost,
                    crew_running=_fmt_running(
                        crew_state["in"],
                        crew_state["out"],
                        crew_state["tokens"],
                        crew_state["cost"],
                    ),
                    agent_running=_fmt_running(
                        agent_state["in"],
                        agent_state["out"],
                        agent_state["tokens"],
                        agent_state["cost"],
                    ),
                    global_running=_fmt_running(global_in, global_out, global_tokens, global_cost),
                )
            )

        lines.append("")
        return "\n".join(lines)

    except Exception as e:
        logger.warning(f"⚠️ Could not generate cost breakdown: {e}")
        return "\n---\n\n## 💰 Cost and efficiency\n\nCost tracking unavailable.\n"


def post_results(env_vars, final_markdown):
    """Post results to GitHub Actions summary."""
    logger.info("=" * 60)
    logger.info("📤 STEP 7: Posting Results to GitHub Actions")
    logger.info("=" * 60)

    # Post to GitHub Actions summary (ONLY output location)
    step_summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if step_summary_file:
        try:
            with open(step_summary_file, "a") as f:
                f.write(final_markdown)
                f.write("\n")
            logger.info("✅ Posted to GitHub Actions summary")
            logger.info("📊 View results in Actions tab for this workflow run")
        except Exception as e:
            logger.error(f"❌ Failed to write to step summary: {e}")
    else:
        logger.warning("⚠️ GITHUB_STEP_SUMMARY not set - skipping Actions summary")
        logger.info("ℹ️ In local testing mode, review saved to workspace/final_summary.md")


def save_trace(workspace_dir):
    """Save execution trace for artifacts."""
    logger.info("=" * 60)
    logger.info("💾 STEP 8: Saving Execution Trace")
    logger.info("=" * 60)

    trace_dir = workspace_dir / "trace"
    trace_dir.mkdir(parents=True, exist_ok=True)
    trace_copy_enabled = os.getenv("CREWAI_TRACE_COPY", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    files_copied = 0
    if trace_copy_enabled:
        import shutil

        for json_file in workspace_dir.glob("*.json"):
            try:
                shutil.copy(json_file, trace_dir / json_file.name)
                logger.info(f"✅ Saved {json_file.name} to trace")
                files_copied += 1
            except Exception as e:
                logger.warning(f"⚠️ Could not copy {json_file.name}: {e}")

        summary_file = workspace_dir / "final_summary.md"
        if summary_file.exists():
            try:
                shutil.copy(summary_file, trace_dir / "final_summary.md")
                logger.info("✅ Saved final_summary.md to trace")
                files_copied += 1
            except Exception as e:
                logger.warning(f"⚠️ Could not copy final_summary.md: {e}")

        diff_file = workspace_dir / "diff.txt"
        if diff_file.exists():
            try:
                shutil.copy(diff_file, trace_dir / "diff.txt")
                logger.info("✅ Saved diff.txt to trace")
                files_copied += 1
            except Exception as e:
                logger.warning(f"⚠️ Could not copy diff.txt: {e}")
    else:
        logger.info("ℹ️ Trace copy disabled; writing metadata only")

    # Create a trace index file with metadata
    try:
        trace_index = {
            "timestamp": datetime.now().isoformat(),
            "files_copied": files_copied,
            "workspace_files": [f.name for f in workspace_dir.iterdir() if f.is_file()],
        }
        with open(trace_dir / "trace_index.json", "w") as f:
            json.dump(trace_index, f, indent=2)
        logger.info("✅ Created trace index")
        files_copied += 1
    except Exception as e:
        logger.warning(f"⚠️ Could not create trace index: {e}")

    logger.info(f"📊 Trace saved to {trace_dir} ({files_copied} files)")


def print_cost_summary():
    """Print cost tracking summary to console."""
    logger.info("=" * 60)
    logger.info("💰 Cost Summary")
    logger.info("=" * 60)

    try:
        tracker = get_tracker()
        summary = tracker.get_summary()

        logger.info(f"Total API Calls: {summary['total_calls']}")
        logger.info(f"Total Tokens: {summary['total_tokens']:,}")
        logger.info(f"  - Input: {summary['total_tokens_in']:,}")
        logger.info(f"  - Output: {summary['total_tokens_out']:,}")
        logger.info(f"Total Cost: ${summary['total_cost']:.4f}")
        logger.info(f"Total Duration: {summary['total_duration']:.2f}s")

        # Print per-crew breakdown
        if summary["crew_breakdown"]:
            logger.info("")
            logger.info("By Crew:")
            for crew_name in sorted(summary["crew_breakdown"].keys()):
                stats = summary["crew_breakdown"][crew_name]
                logger.info(
                    f"  • {crew_name}: {stats['calls']} calls, "
                    f"${stats['cost']:.4f} ({stats['total_tokens']:,} tokens)"
                )

    except Exception as e:
        logger.warning(f"⚠️ Could not generate cost summary: {e}")


def _apply_memory_suppressions(memory, workspace_dir):
    """Filter review findings through memory suppressions and record the review."""
    workspace = WorkspaceTool()
    total_suppressed = 0

    review_files = {
        "quick_review.json": ["critical", "warnings", "info"],
        "full_review.json": [
            "architecture",
            "security",
            "performance",
            "testing",
            "maintainability",
        ],
    }

    for crew_info in SPECIALIST_CREWS.values():
        review_files[crew_info["output_file"]] = ["findings"]

    for filename, finding_keys in review_files.items():
        if not workspace.exists(filename):
            continue
        try:
            data = workspace.read_json(filename)
            file_suppressed = 0
            for key in finding_keys:
                findings = data.get(key, [])
                if findings and isinstance(findings, list):
                    filtered, suppressed = memory.filter_findings(findings)
                    if suppressed > 0:
                        data[key] = filtered
                        file_suppressed += suppressed
            if file_suppressed > 0:
                workspace.write_json(filename, data)
                total_suppressed += file_suppressed
                logger.info(f"🧠 Suppressed {file_suppressed} findings in {filename}")
        except Exception as e:
            logger.warning(f"Could not apply suppressions to {filename}: {e}")

    if total_suppressed > 0:
        logger.info(f"🧠 Total suppressed: {total_suppressed} findings across all reviews")

    total_findings = 0
    for filename in review_files:
        if workspace.exists(filename):
            try:
                data = workspace.read_json(filename)
                for key in review_files[filename]:
                    total_findings += len(data.get(key, []))
            except Exception:
                pass

    pr_number = os.getenv("PR_NUMBER", "unknown")
    normalized_pr = str(pr_number).strip().lower()
    if normalized_pr in {"local", "unknown", "", "n/a"}:
        logger.info("🧠 Skipping persistent memory trend update for local/non-PR run")
    else:
        memory.record_review(pr_number=pr_number, findings_count=total_findings)
        memory.save()


def main():
    """Main orchestration function.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    logger.info("🚀 CrewAI Router-Based Review System Starting")
    logger.info("=" * 60)

    try:
        # Setup
        workspace_dir = setup_workspace()
        env_vars = get_env_vars()

        # Initialize review memory (loads suppressions + learned patterns)
        memory = get_memory_manager()
        memory_context = memory.get_context_for_review()
        if memory_context:
            logger.info("🧠 Memory context loaded — writing to workspace")
            workspace = WorkspaceTool()
            workspace.write("memory_context.md", memory_context)
            if workspace.exists("context_pack.md"):
                context_pack = workspace.read("context_pack.md")
                if "## Persistent review memory" not in context_pack:
                    merged_context_pack = (
                        context_pack.rstrip()
                        + "\n\n## Persistent review memory\n"
                        + memory_context.strip()
                        + "\n"
                    )
                    workspace.write("context_pack.md", merged_context_pack)
        else:
            logger.info("🧠 No prior memory context (fresh start)")

        # Track which workflows were executed and their success status
        workflows_executed = []
        workflow_success = {}

        # STEP 1: Router decides workflows
        decision = run_router(env_vars)
        workflows = decision.get("workflows", ["ci-log-analysis", "quick-review"])

        # Rate limit delay: centralized in MODEL_REGISTRY (0s for paid, 10s for free)
        rate_limit_delay = get_rate_limit_delay()

        # STEP 2: Always run CI analysis (default)
        if "ci-log-analysis" in workflows:
            success = run_ci_analysis(env_vars)
            workflows_executed.append("ci-log-analysis")
            workflow_success["ci-log-analysis"] = success
            if not success:
                logger.warning("⚠️ CI analysis had issues, but continuing...")
            # Rate limit buffer
            if rate_limit_delay > 0:
                logger.info(f"⏳ Waiting {rate_limit_delay}s for rate limit buffer...")
                time.sleep(rate_limit_delay)

        # STEP 3: Always run quick review (default)
        if "quick-review" in workflows:
            success = run_quick_review()
            workflows_executed.append("quick-review")
            workflow_success["quick-review"] = success
            if not success:
                logger.warning("⚠️ Quick review had issues, but continuing...")
            # Rate limit buffer
            if rate_limit_delay > 0:
                logger.info(f"⏳ Waiting {rate_limit_delay}s for rate limit buffer...")
                time.sleep(rate_limit_delay)

        # STEP 4: Conditional - Full review
        if "full-review" in workflows:
            success = run_full_review(env_vars)
            workflows_executed.append("full-review")
            workflow_success["full-review"] = success
            if not success:
                logger.warning("⚠️ Full review had issues, but continuing...")
            # Rate limit buffer
            if rate_limit_delay > 0:
                logger.info(f"⏳ Waiting {rate_limit_delay}s for rate limit buffer...")
                time.sleep(rate_limit_delay)
        else:
            logger.info("⏩ Skipping full review (no crewai:full-review label)")

        # STEP 5: Specialist crews (triggered by labels or full-review)
        specialist_crews_to_run = decision.get("specialist_crews", [])
        if specialist_crews_to_run:
            crew_list = ", ".join(specialist_crews_to_run)
            force_specialist_attempts = "full-review" in workflows
            logger.info(
                f"🔬 Running {len(specialist_crews_to_run)} specialist crew(s): {crew_list}"
            )
            for crew_key in specialist_crews_to_run:
                if crew_key not in SPECIALIST_CREWS:
                    logger.warning(f"⚠️ Unknown specialist crew: {crew_key}")
                    continue
                success = run_specialist_crew(crew_key, force_attempt=force_specialist_attempts)
                workflows_executed.append(f"specialist-{crew_key}")
                workflow_success[f"specialist-{crew_key}"] = success
                if not success:
                    logger.warning(f"⚠️ {crew_key.title()} review had issues, but continuing...")
                if rate_limit_delay > 0:
                    logger.info(f"⏳ Waiting {rate_limit_delay}s for rate limit buffer...")
                    time.sleep(rate_limit_delay)
        else:
            logger.info("⏩ No specialist crews requested")

        # STEP 5.5: Apply memory suppressions to review findings
        _apply_memory_suppressions(memory, workspace_dir)

        synthesis_success = run_post_specialist_synthesis(workflows_executed)
        workflows_executed.append("post-specialist-synthesis")
        workflow_success["post-specialist-synthesis"] = synthesis_success
        if not synthesis_success:
            logger.warning("⚠️ Post-specialist synthesis had issues, but continuing...")

        # STEP 6: Final summary (always run) - pass workflow count
        stale_summary_file = workspace_dir / "final_summary.md"
        if stale_summary_file.exists():
            try:
                stale_summary_file.unlink()
            except Exception as delete_error:
                logger.warning(f"⚠️ Could not remove stale final_summary.md: {delete_error}")

        summary_success = run_final_summary(env_vars, workflows_executed)
        if not summary_success:
            logger.warning("⚠️ Final summary had issues, will use fallback...")

        executive_success = run_executive_synthesis(workflows_executed)
        workflows_executed.append("executive-synthesis")
        workflow_success["executive-synthesis"] = executive_success
        if not executive_success:
            logger.warning(
                "⚠️ Executive synthesis had issues, falling back to deterministic summary."
            )

        # Read final markdown from workspace with validation
        workspace = WorkspaceTool()

        # Debug: List all files in workspace
        logger.info("📂 Workspace files:")
        for f in workspace_dir.iterdir():
            if f.is_file():
                logger.info(f"  - {f.name} ({f.stat().st_size} bytes)")

        # Try to read final_summary.md
        if workspace.exists("final_summary.md"):
            final_markdown = workspace.read("final_summary.md")
            logger.info(f"✅ Read final_summary.md ({len(final_markdown)} chars)")

            # CRITICAL VALIDATION: If summary is too short, it's likely just skeleton
            # A proper summary with actual content should be at least 1000 chars
            if len(final_markdown) < 1000:
                logger.warning(
                    f"⚠️ Final summary is too short ({len(final_markdown)} chars) - "
                    "likely incomplete"
                )
                logger.info("🔄 Replacing with comprehensive fallback summary")
                final_markdown = create_fallback_summary(
                    workspace_dir, env_vars, workflows_executed
                )
            else:
                logger.info("✅ Final summary has sufficient content")
        else:
            logger.warning("⚠️ final_summary.md not found - creating comprehensive fallback")
            final_markdown = create_fallback_summary(workspace_dir, env_vars, workflows_executed)

        has_deep_review = "full-review" in workflows_executed or any(
            workflow.startswith("specialist-") for workflow in workflows_executed
        )
        if has_deep_review or executive_success:
            logger.info(
                "🔄 Rebuilding final_summary.md from review artifacts with executive synthesis"
            )
            final_markdown = create_fallback_summary(workspace_dir, env_vars, workflows_executed)

        # CRITICAL: Wait for async cost tracking callbacks to fire
        logger.info("⏳ Waiting for cost tracking callbacks to complete...")
        time.sleep(2)  # Give async callbacks time to register

        # Generate cost breakdown and append to summary
        cost_breakdown = generate_cost_breakdown()
        final_markdown_with_cost = final_markdown + cost_breakdown

        workspace.write("final_summary.md", final_markdown_with_cost)

        # STEP 7: Post results to GitHub Actions summary (with cost table)
        post_results(env_vars, final_markdown_with_cost)

        # STEP 8: Save trace
        save_trace(workspace_dir)

        # Print cost summary to console
        print_cost_summary()

        # Log workflow success summary
        logger.info("=" * 60)
        logger.info("📊 Workflow Execution Summary")
        logger.info("=" * 60)
        for workflow, success in workflow_success.items():
            status = "✅ SUCCESS" if success else "⚠️ HAD ISSUES"
            logger.info(f"{workflow}: {status}")

        logger.info("=" * 60)
        logger.info("✅ CrewAI Review Complete!")
        logger.info("=" * 60)

        _cleanup_root_artifact_leakage()

        return 0

    except FatalLLMAvailabilityError as e:
        logger.error(f"❌ Fatal provider availability error: {e}")
        workspace = WorkspaceTool()
        workspace.write(
            "final_summary.md",
            "\n".join(
                [
                    "## ❌ Review Aborted",
                    "",
                    "The review stopped early due to provider availability.",
                    "",
                    f"- Error: `{e}`",
                    "- Behavior: fail-fast (no additional crews executed)",
                    "- Action: ensure provider has credits/responding, then rerun "
                    "`./scripts/ci-local.sh --review`",
                    "",
                    "---",
                    "",
                    "## 💰 Cost Tracking",
                    "",
                    "No API calls recorded.",
                ]
            ),
        )
        _cleanup_root_artifact_leakage()
        return 1
    except Exception as e:
        logger.error(f"❌ Review failed: {e}", exc_info=True)
        _cleanup_root_artifact_leakage()
        return 1


if __name__ == "__main__":
    sys.exit(main())
