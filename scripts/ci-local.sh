#!/usr/bin/env bash
# =============================================================================
# Local CI Runner — mirrors the GitHub Actions pipeline
# =============================================================================
# Single idempotent entry point. Runs the same checks as CI, locally.
# Prompts for any missing environment variables when needed.
# Deploy steps are SKIPPED unless --deploy flag is passed.
# CrewAI review is SKIPPED unless --review flag is passed.
#
# Usage:
#   ./scripts/ci-local.sh              # Full CI (no deploy, no review)
#   ./scripts/ci-local.sh --review     # Full CI + CrewAI code review
#   ./scripts/ci-local.sh --deploy     # Full CI + deploy (requires CF creds)
#   ./scripts/ci-local.sh --step lint  # Run a single step
#
# Available steps: format, lint, lint-md, lint-css, typecheck, commitlint,
#                  link-check, test-crewai, test-website, build-website, review
#
# Environment:
#   Reads .env if present. Prompts interactively for missing vars when needed.
# =============================================================================

set -euo pipefail

# --- Configuration ---
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Flags
RUN_DEPLOY=false
RUN_REVIEW=false
RUN_FULL_REVIEW=false
RUN_COMPLETE_FULL_REVIEW=false
REVIEW_LABELS=""
SINGLE_STEP=""
VERBOSE=false

LOCK_FILE="${REPO_ROOT}/.ci-local.lock"
LOCK_FD=9

# --- Colors & Symbols ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

PASS="✅"
FAIL="❌"
SKIP="⏭️ "
WARN="⚠️ "
RUNNING="🔄"
PHASE="═══"

# --- State Tracking ---
declare -A STEP_RESULTS
declare -A STEP_DURATIONS
declare -a STEP_ORDER
TOTAL_START=$(date +%s)
STEPS_PASSED=0
STEPS_FAILED=0
STEPS_SKIPPED=0

# --- Load .env (if present) ---
if [[ -f "${REPO_ROOT}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${REPO_ROOT}/.env"
  set +a
fi

# --- Parse Args ---
while [[ $# -gt 0 ]]; do
  case $1 in
    --deploy)   RUN_DEPLOY=true; shift ;;
    --review)   RUN_REVIEW=true; shift ;;
    --full-review)
      RUN_REVIEW=true
      RUN_FULL_REVIEW=true
      shift ;;
    --complete-full-review)
      RUN_REVIEW=true
      RUN_FULL_REVIEW=true
      RUN_COMPLETE_FULL_REVIEW=true
      shift ;;
    --crew)
      RUN_REVIEW=true
      REVIEW_LABELS="${REVIEW_LABELS:+$REVIEW_LABELS,}crewai:$2"
      shift 2 ;;
    --verbose)  VERBOSE=true; shift ;;
    --step)     SINGLE_STEP="$2"; shift 2 ;;
    --help|-h)
      echo "Usage: ./scripts/ci-local.sh [--review] [--full-review] [--complete-full-review] [--crew <name>] [--deploy] [--step <name>] [--verbose]"
      echo ""
      echo "Flags:"
      echo "  --review        Run quick CrewAI code review (OpenRouter default)"
  echo "  --full-review   Enable deep routing: full review + broader specialist coverage"
      echo "  --complete-full-review   Run full review + all specialists in complete-repo mode"
      echo "  --crew <name>   Run specific crew(s) — can be repeated (e.g. --crew security --crew legal)"
      echo "  --deploy        Run Cloudflare deploy (requires CF credentials)"
      echo "  --step <name>   Run a single step by name"
      echo "  --verbose       Show full command output"
      echo ""
      echo "Environment overrides:"
      echo "  CREWAI_REVIEW_TIMEOUT_SECONDS   Timeout for review subprocess (default: 90)"
      echo ""
      echo ""
      echo "Specialist crews (use with --crew <name> or --full-review for all):"
      echo "  security     OWASP-grade vulnerability analysis (1 agent)"
      echo "  legal        OSS licenses, 50-state US law, export controls, global privacy (4 agents)"
      echo "  finance      Billing logic, payment flows, SOX, PCI-DSS (1 agent)"
      echo "  docs         README accuracy, API docs, code examples (1 agent)"
      echo "  agentic      AGENTS.md compliance, convention enforcement (1 agent)"
      echo "  marketing    Copy quality, i18n, regional ad law, dark patterns (3 agents)"
      echo "  science      Reproducibility, statistical rigor, data leakage (1 agent)"
      echo "  government   WCAG 2.1 AA, Section 508, audit trails (1 agent)"
      echo "  strategy     Business impact, global expansion, competitive intel (3 agents)"
      echo ""
      echo "Always-run crews (included in every --review):"
      echo "  router       Analyzes diff, decides which crews to run"
      echo "  ci-log       CI log triage and error analysis (3 agents)"
      echo "  quick        Code quality, style, and basic security (3 agents)"
      echo "  summary      Synthesizes all crew outputs into final_summary.md"
      echo ""
      echo "Steps (use with --step <name>):"
      echo "  format, lint, lint-md, lint-css, typecheck, commitlint,"
      echo "  link-check, test-crewai, test-website, build-website, review"
      echo ""
      echo "Examples:"
      echo "  ./scripts/ci-local.sh                                # Full CI (no review)"
      echo "  ./scripts/ci-local.sh --review                       # Quick review"
  echo "  ./scripts/ci-local.sh --full-review                  # Deep routing with broader specialist coverage"
      echo "  ./scripts/ci-local.sh --complete-full-review         # Full repo perspective for all specialists"
      echo "  ./scripts/ci-local.sh --crew security                # Just security crew"
      echo "  ./scripts/ci-local.sh --crew security --crew legal   # Multiple specific crews"
      echo "  ./scripts/ci-local.sh --step test-crewai             # Just run CrewAI tests"
      echo "  ./scripts/ci-local.sh --review --verbose             # Review with full output"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# =============================================================================
# Environment Validation & Interactive Prompts
# =============================================================================

prompt_env_var() {
  local var_name="$1"
  local description="$2"
  local is_secret="${3:-false}"

  if [[ -n "${!var_name:-}" ]]; then
    return 0
  fi

  echo ""
  echo -e "  ${YELLOW}${WARN}${NC} ${BOLD}${var_name}${NC} is not set."
  echo -e "  ${DIM}${description}${NC}"
  echo ""

  if [[ -t 0 ]]; then
    if [[ "$is_secret" == "true" ]]; then
      read -rsp "  Enter ${var_name} (hidden): " value
      echo ""
    else
      read -rp "  Enter ${var_name}: " value
    fi

    if [[ -n "$value" ]]; then
      export "${var_name}=${value}"
      echo -e "  ${PASS} ${var_name} set for this session."

      read -rp "  Save to .env for next time? [y/N] " save_answer
      if [[ "$save_answer" =~ ^[Yy] ]]; then
        echo "${var_name}=${value}" >> "${REPO_ROOT}/.env"
        echo -e "  ${PASS} Saved to .env"
      fi
      return 0
    fi
  fi

  return 1
}

check_env_for_review() {
  if [[ -n "${OPENROUTER_API_KEY:-}" ]]; then
    return 0
  fi

  if prompt_env_var "OPENROUTER_API_KEY" \
    "Default provider for local AI code review. Get one at https://openrouter.ai/keys" \
    "true"; then
    return 0
  fi

  echo -e "  ${DIM}Skipping review — set OPENROUTER_API_KEY.${NC}"
  return 1
}

resolve_review_provider() {
  if [[ -n "${OPENROUTER_API_KEY:-}" ]]; then
    echo "openrouter"
  else
    echo "none"
  fi
}

check_env_for_deploy() {
  local ok=true
  if ! prompt_env_var "CLOUDFLARE_API_TOKEN" \
    "Required for Cloudflare Pages deploy. Create at https://dash.cloudflare.com/profile/api-tokens" \
    "true"; then
    ok=false
  fi
  if ! prompt_env_var "CLOUDFLARE_ACCOUNT_ID" \
    "Your Cloudflare Account ID. Found in the dashboard sidebar." \
    "false"; then
    ok=false
  fi
  $ok
}

# =============================================================================
# Dependency Check
# =============================================================================

check_dependencies() {
  local missing=()

  if ! command -v node &>/dev/null; then
    missing+=("node (install via nvm or https://nodejs.org)")
  fi
  if ! command -v pnpm &>/dev/null; then
    missing+=("pnpm (npm install -g pnpm)")
  fi
  if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    missing+=("python3 (install via pyenv or https://python.org)")
  fi
  if ! command -v flock &>/dev/null; then
    missing+=("flock (install util-linux package)")
  fi

  if [[ ${#missing[@]} -gt 0 ]]; then
    echo ""
    echo -e "  ${RED}${FAIL} Missing required tools:${NC}"
    for tool in "${missing[@]}"; do
      echo -e "     ${RED}•${NC} $tool"
    done
    echo ""
    exit 1
  fi

  # Install node deps if needed
  if [[ ! -d "${REPO_ROOT}/node_modules" ]]; then
    echo -e "  ${RUNNING} Installing Node dependencies..."
    (cd "${REPO_ROOT}" && pnpm install --frozen-lockfile 2>/dev/null || pnpm install 2>/dev/null)
    echo -e "  ${PASS} Dependencies installed."
  fi

  ensure_lychee_tool || true
}

ensure_lychee_tool() {
  if command -v lychee &>/dev/null; then
    return 0
  fi

  local tools_bin="${REPO_ROOT}/.tools/bin"
  local os
  local arch
  local asset_match
  local url
  local tmp_dir

  os=$(uname -s | tr '[:upper:]' '[:lower:]')
  arch=$(uname -m)

  case "${os}/${arch}" in
    linux/x86_64)
      asset_match="x86_64-unknown-linux"
      ;;
    linux/aarch64)
      asset_match="aarch64-unknown-linux"
      ;;
    darwin/x86_64)
      asset_match="x86_64-apple-darwin"
      ;;
    darwin/arm64)
      asset_match="aarch64-apple-darwin"
      ;;
    *)
      echo -e "  ${WARN} Lychee auto-install unsupported on ${os}/${arch}; internal link checker only."
      return 1
      ;;
  esac

  mkdir -p "${tools_bin}"
  tmp_dir=$(mktemp -d)

  if command -v curl &>/dev/null && command -v tar &>/dev/null; then
    url=$(ASSET_MATCH="${asset_match}" python3 - <<'PY'
import json
import os
import urllib.request

repo_api = "https://api.github.com/repos/lycheeverse/lychee/releases/latest"
asset_match = os.environ.get("ASSET_MATCH", "")

with urllib.request.urlopen(repo_api, timeout=15) as resp:
    data = json.load(resp)

for asset in data.get("assets", []):
    name = str(asset.get("name", ""))
    if asset_match in name and name.endswith(".tar.gz") and ".sha256" not in name:
        print(asset.get("browser_download_url", ""))
        break
PY
)

    if [[ -n "${url}" ]] \
      && curl -fsSL "${url}" -o "${tmp_dir}/lychee.tar.gz" \
      && tar -xzf "${tmp_dir}/lychee.tar.gz" -C "${tmp_dir}" \
      && [[ -f "${tmp_dir}/lychee" ]]; then
      install -m 0755 "${tmp_dir}/lychee" "${tools_bin}/lychee"
      export PATH="${tools_bin}:${PATH}"
      rm -rf "${tmp_dir}"
      echo -e "  ${PASS} Installed lychee to ${tools_bin}/lychee"
      return 0
    fi
  fi

  rm -rf "${tmp_dir}"
  echo -e "  ${WARN} Could not auto-install lychee; internal link checker still active."
  return 1
}

acquire_run_lock() {
  exec {LOCK_FD}>"${LOCK_FILE}"
  if ! flock -n "${LOCK_FD}"; then
    local holder
    holder=$(cat "${LOCK_FILE}" 2>/dev/null || true)
    echo ""
    echo -e "  ${RED}${FAIL} Another local CI run is already active.${NC}"
    if [[ -n "${holder}" ]]; then
      echo -e "  ${DIM}Lock owner: ${holder}${NC}"
    fi
    echo -e "  ${DIM}Wait for it to finish, then retry.${NC}"
    exit 1
  fi

  echo "pid=$$ started=$(date -u '+%Y-%m-%dT%H:%M:%SZ') cwd=${REPO_ROOT}" 1>&"${LOCK_FD}"
}

release_run_lock() {
  flock -u "${LOCK_FD}" 2>/dev/null || true
  rm -f "${LOCK_FILE}" 2>/dev/null || true
}

# =============================================================================
# Idempotent Workspace Setup
# =============================================================================

clean_workspace() {
  local workspace_dir="${REPO_ROOT}/.crewai/workspace"
  local crewai_root="${REPO_ROOT}/.crewai"
  if [[ -d "$workspace_dir" ]]; then
    rm -rf "$workspace_dir"
  fi
  rm -f \
    "${crewai_root}/ci_summary.json" \
    "${crewai_root}/full_review.json" \
    "${crewai_root}/security_review.json" \
    "${crewai_root}/legal_review.json" \
    "${crewai_root}/finance_review.json" \
    "${crewai_root}/documentation_review.json" \
    "${crewai_root}/agentic_consistency_review.json" \
    "${crewai_root}/marketing_review.json" \
    "${crewai_root}/science_review.json" \
    "${crewai_root}/government_regulatory_review.json" \
    "${crewai_root}/strategic_review.json" \
    "${crewai_root}/data_engineering_review.json" \
    "${crewai_root}/brand_analysis.json" \
    "${crewai_root}/global_market_analysis.json" \
    "${crewai_root}/license_analysis.json" \
    "${crewai_root}/us_regulatory_analysis.json" \
    "${crewai_root}/intl_trade_analysis.json" \
    "${crewai_root}/strategy_analysis.json" \
    "${crewai_root}/expansion_analysis.json" \
    "${crewai_root}/code_quality_deep.json" \
    "${crewai_root}/architecture_analysis.json" \
    "${crewai_root}/security_deep_dive.json" \
    "${crewai_root}/quick_review.json" \
    "${crewai_root}/router_decision.json" \
    "${crewai_root}/context_pack.json" \
    "${crewai_root}/diff_context.json"
  mkdir -p "${workspace_dir}/trace"
}

# =============================================================================
# Helper Functions
# =============================================================================

print_header() {
  echo ""
  echo -e "${BLUE}${PHASE}${PHASE}${PHASE}${PHASE}${PHASE}${PHASE}${PHASE}${PHASE}${PHASE}${NC}"
  echo -e "${BOLD}${BLUE}  $1${NC}"
  echo -e "${BLUE}${PHASE}${PHASE}${PHASE}${PHASE}${PHASE}${PHASE}${PHASE}${PHASE}${PHASE}${NC}"
}

print_step() {
  echo -e "  ${RUNNING} ${BOLD}$1${NC} ${DIM}$2${NC}"
}

print_result() {
  local name="$1"
  local status="$2"
  local duration="$3"
  local detail="${4:-}"

  if [[ -z "${STEP_RESULTS[$name]+x}" ]]; then
    STEP_ORDER+=("$name")
  fi

  case "$status" in
    pass)
      echo -e "  ${PASS} ${GREEN}${name}${NC} ${DIM}(${duration}s)${NC}"
      STEPS_PASSED=$((STEPS_PASSED + 1))
      STEP_RESULTS["$name"]="pass"
      ;;
    fail)
      echo -e "  ${FAIL} ${RED}${name}${NC} ${DIM}(${duration}s)${NC}"
      if [[ -n "$detail" ]]; then
        echo -e "     ${DIM}${detail}${NC}"
      fi
      STEPS_FAILED=$((STEPS_FAILED + 1))
      STEP_RESULTS["$name"]="fail"
      ;;
    skip)
      echo -e "  ${SKIP} ${YELLOW}${name}${NC} ${DIM}— ${detail}${NC}"
      STEPS_SKIPPED=$((STEPS_SKIPPED + 1))
      STEP_RESULTS["$name"]="skip"
      ;;
    warn)
      echo -e "  ${WARN} ${YELLOW}${name}${NC} ${DIM}(${duration}s) — ${detail}${NC}"
      STEPS_PASSED=$((STEPS_PASSED + 1))
      STEP_RESULTS["$name"]="warn"
      ;;
  esac
  STEP_DURATIONS["$name"]="$duration"
}

run_step() {
  local name="$1"
  shift
  local start
  start=$(date +%s)

  if $VERBOSE; then
    if "$@"; then
      local end; end=$(date +%s)
      print_result "$name" "pass" "$((end - start))"
      return 0
    else
      local end; end=$(date +%s)
      print_result "$name" "fail" "$((end - start))"
      return 1
    fi
  else
    local output
    if output=$("$@" 2>&1); then
      local end; end=$(date +%s)
      print_result "$name" "pass" "$((end - start))"
      return 0
    else
      local end; end=$(date +%s)
      local last_lines
      last_lines=$(echo "$output" | tail -5)
      print_result "$name" "fail" "$((end - start))" "$last_lines"
      return 1
    fi
  fi
}

has_files() {
  local pattern="$1"
  local dir="${2:-.}"
  find "$dir" -type f -name "$pattern" \
    -not -path "*/node_modules/*" \
    -not -path "*/.git/*" \
    -not -path "*/.venv/*" \
    -not -path "*/venv/*" \
    -not -path "*/dist/*" \
    -print -quit 2>/dev/null | grep -q .
}

check_command() {
  command -v "$1" &>/dev/null
}

should_run() {
  local step="$1"
  if [[ -n "$SINGLE_STEP" ]]; then
    [[ "$SINGLE_STEP" == "$step" ]]
  else
    true
  fi
}

run_internal_markdown_link_check() {
  local report_file="$1"
  python3 - "$REPO_ROOT" "$report_file" <<'PY'
import re
import sys
from pathlib import Path


repo_root = Path(sys.argv[1]).resolve()
report_path = Path(sys.argv[2]).resolve()

skip_parts = {"node_modules", ".git", ".crewai", "dist", "coverage", ".venv", "venv"}


def gh_anchor(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\-\s]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text


def heading_anchors(path: Path) -> set[str]:
    anchors = set()
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("#"):
                title = line.lstrip("#").strip()
                if title:
                    anchors.add(gh_anchor(title))
    except Exception:
        return anchors
    return anchors


def should_skip(path: Path) -> bool:
    return any(part in skip_parts for part in path.parts)


all_md = [p for p in repo_root.rglob("*.md") if not should_skip(p)]
link_re = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
broken = []
checked = 0

for md_file in all_md:
    text = md_file.read_text(encoding="utf-8", errors="replace")
    for raw_target in link_re.findall(text):
        target = raw_target.strip()
        if not target:
            continue
        if target.startswith(("http://", "https://", "mailto:", "tel:")):
            continue

        checked += 1
        target_path, _, target_anchor = target.partition("#")

        if target_path.startswith("/"):
            resolved = (repo_root / target_path.lstrip("/")).resolve()
        elif target_path == "":
            resolved = md_file.resolve()
        else:
            resolved = (md_file.parent / target_path).resolve()

        if not resolved.exists():
            broken.append((md_file.relative_to(repo_root), target, "missing file"))
            continue

        if target_anchor and resolved.suffix.lower() == ".md":
            anchors = heading_anchors(resolved)
            if gh_anchor(target_anchor) not in anchors:
                broken.append((md_file.relative_to(repo_root), target, "missing anchor"))


lines = [
    "# Internal Markdown Link Check",
    "",
    f"Files scanned: {len(all_md)}",
    f"Links checked: {checked}",
    f"Broken links: {len(broken)}",
    "",
]

if broken:
    lines.append("| Source file | Link target | Error |")
    lines.append("| --- | --- | --- |")
    for source, target, error in broken[:300]:
        lines.append(f"| `{source}` | `{target}` | {error} |")
    if len(broken) > 300:
        lines.append("")
        lines.append(f"... and {len(broken) - 300} more broken links")
else:
    lines.append("All checked internal markdown links resolved.")

report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
sys.exit(1 if broken else 0)
PY
}

write_workspace_ci_summary_markdown() {
  local workspace_dir="${REPO_ROOT}/.crewai/workspace"
  local ci_results_dir="${workspace_dir}/ci_results"
  local summary_file="${workspace_dir}/local_ci_summary.md"
  local ci_stage_file="${ci_results_dir}/core-ci/summary.md"
  local docs_stage_file="${ci_results_dir}/test-docs-links/summary.md"
  local crewai_test_file="${ci_results_dir}/test-crewai/summary.md"
  local website_test_file="${ci_results_dir}/test-website/summary.md"
  local deploy_preview_file="${ci_results_dir}/deploy-preview/summary.md"
  local deploy_production_file="${ci_results_dir}/deploy-production/summary.md"
  local review_file="${ci_results_dir}/crewai-review/summary.md"

  mkdir -p \
    "${ci_results_dir}/core-ci" \
    "${ci_results_dir}/test-docs-links" \
    "${ci_results_dir}/test-crewai" \
    "${ci_results_dir}/test-website" \
    "${ci_results_dir}/deploy-preview" \
    "${ci_results_dir}/deploy-production" \
    "${ci_results_dir}/crewai-review"

  {
    echo "# Local CI Summary"
    echo ""
    echo "Generated: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    echo ""
    echo "## ✅ Validate Environment"
    echo ""
    echo "- format/lint/typecheck/commitlint steps are tracked in the table below"
    echo ""
    echo "## ✅ Test & Build"
    echo ""
    if [[ -f "${workspace_dir}/link-check-report.md" ]]; then
      echo '- test-docs-links: completed (see `link-check-report.md`)'
    elif [[ "${STEP_RESULTS[Link Check]:-skip}" == "pass" ]]; then
      echo "- test-docs-links: pass"
    elif [[ "${STEP_RESULTS[Link Check]:-skip}" == "fail" ]]; then
      echo "- test-docs-links: fail"
    else
      echo "- test-docs-links: skipped"
    fi
    echo ""
    echo "## 🚀 Deploy"
    echo ""
    echo "- deploy-preview: ${STEP_RESULTS[Preview Deploy]:-skip}"
    echo "- deploy-production: ${STEP_RESULTS[Production Deploy]:-skip}"
    echo ""
    echo "## 🤖 CrewAI Review"
    echo ""
    echo "- crewai-review: ${STEP_RESULTS[CrewAI Review]:-pending}"
    echo ""
    echo "## 📊 Step table"
    echo ""
    echo "| Step | Status | Duration |"
    echo "| --- | --- | --- |"
    for step in "${STEP_ORDER[@]}"; do
      echo "| ${step} | ${STEP_RESULTS[$step]} | ${STEP_DURATIONS[$step]}s |"
    done
  } > "${summary_file}"

  cp "${summary_file}" "${ci_stage_file}"

  if [[ -f "${workspace_dir}/link-check-summary.md" ]]; then
    cp "${workspace_dir}/link-check-summary.md" "${docs_stage_file}"
  else
    {
      echo "# Docs Link Check Summary"
      echo ""
      echo "No local docs link summary available."
    } > "${docs_stage_file}"
  fi

  {
    echo "# CrewAI tests summary"
    echo ""
    echo "- status: ${STEP_RESULTS[CrewAI Tests]:-not-run}"
    echo "- duration: ${STEP_DURATIONS[CrewAI Tests]:-0}s"
  } > "${crewai_test_file}"

  {
    echo "# Website test/build summary"
    echo ""
    echo "- status: ${STEP_RESULTS[Website Build]:-not-run}"
    echo "- duration: ${STEP_DURATIONS[Website Build]:-0}s"
  } > "${website_test_file}"

  {
    echo "# Preview deploy summary"
    echo ""
    echo "- status: ${STEP_RESULTS[Preview Deploy]:-not-run}"
    echo "- duration: ${STEP_DURATIONS[Preview Deploy]:-0}s"
  } > "${deploy_preview_file}"

  {
    echo "# Production deploy summary"
    echo ""
    echo "- status: ${STEP_RESULTS[Production Deploy]:-not-run}"
    echo "- duration: ${STEP_DURATIONS[Production Deploy]:-0}s"
  } > "${deploy_production_file}"

  {
    echo "# CrewAI review summary"
    echo ""
    echo "- status: ${STEP_RESULTS[CrewAI Review]:-not-run}"
    echo "- duration: ${STEP_DURATIONS[CrewAI Review]:-0}s"
  } > "${review_file}"
}

# =============================================================================
# PHASE 1: Format & Lint
# =============================================================================

run_phase_1() {
  print_header "PHASE 1: Format & Lint"

  local phase_failed=false

  # --- Prettier ---
  if should_run "format"; then
    print_step "Prettier" "formatting all files..."
    if check_command pnpm; then
      run_step "Prettier Format" pnpm format 2>/dev/null || phase_failed=true
    else
      print_result "Prettier Format" "skip" "0" "pnpm not installed"
    fi
  fi

  # --- ESLint ---
  if should_run "lint"; then
    if has_files "*.ts" || has_files "*.tsx" || has_files "*.js" || has_files "*.jsx"; then
      print_step "ESLint" "linting JS/TS files..."
      run_step "ESLint" pnpm lint:fix 2>/dev/null || phase_failed=true
    else
      print_result "ESLint" "skip" "0" "no JS/TS files found"
    fi
  fi

  # --- Markdownlint ---
  if should_run "lint-md"; then
    if has_files "*.md"; then
      print_step "Markdownlint" "checking markdown files..."
      run_step "Markdownlint" pnpm lint:md 2>/dev/null || phase_failed=true
    else
      print_result "Markdownlint" "skip" "0" "no markdown files"
    fi
  fi

  # --- Stylelint ---
  if should_run "lint-css"; then
    if has_files "*.css" || has_files "*.scss"; then
      print_step "Stylelint" "checking stylesheets..."
      run_step "Stylelint" pnpm lint:css 2>/dev/null || phase_failed=true
    else
      print_result "Stylelint" "skip" "0" "no CSS/SCSS files"
    fi
  fi

  # --- Python: ruff ---
  if should_run "lint"; then
    if has_files "*.py"; then
      print_step "Ruff" "linting Python files..."
      if check_command ruff; then
        run_step "Ruff Lint" ruff check . --fix --exit-zero --quiet || phase_failed=true
        run_step "Ruff Format" ruff format . --quiet || phase_failed=true
      else
        print_result "Ruff" "skip" "0" "ruff not installed (pip install ruff)"
      fi
    fi
  fi

  # --- Commitlint ---
  if should_run "commitlint"; then
    if git -C "${REPO_ROOT}" rev-parse HEAD~1 &>/dev/null; then
      print_step "Commitlint" "checking last commit message..."
      local cl_start; cl_start=$(date +%s)
      if pnpm exec commitlint --from HEAD~1 --to HEAD --verbose >/dev/null 2>&1; then
        local cl_end; cl_end=$(date +%s)
        print_result "Commitlint" "pass" "$((cl_end - cl_start))"
      else
        local cl_end; cl_end=$(date +%s)
        print_result "Commitlint" "warn" "$((cl_end - cl_start))" "commit message style"
      fi
    else
      print_result "Commitlint" "skip" "0" "not enough commit history"
    fi
  fi

  # --- TypeScript ---
  if should_run "typecheck"; then
    if [[ -f "${REPO_ROOT}/tsconfig.json" ]]; then
      print_step "TypeScript" "type-checking..."
      run_step "TypeScript" pnpm typecheck 2>/dev/null || phase_failed=true
    else
      print_result "TypeScript" "skip" "0" "no tsconfig.json"
    fi
  fi

  $phase_failed && return 1 || return 0
}

# =============================================================================
# PHASE 2: Tests & Builds
# =============================================================================

run_phase_2() {
  print_header "PHASE 2: Tests & Builds"

  local phase_failed=false

  # --- Link Check ---
  if should_run "link-check"; then
    local workspace_dir="${REPO_ROOT}/.crewai/workspace"
    local ci_results_docs_dir="${workspace_dir}/ci_results/test-docs-links"
    local internal_report_md="${workspace_dir}/link-check-internal.md"
    local lychee_report_md="${workspace_dir}/link-check-lychee.md"
    local link_report_md="${workspace_dir}/link-check-report.md"
    local link_summary_md="${workspace_dir}/link-check-summary.md"

    mkdir -p "${workspace_dir}" "${ci_results_docs_dir}"

    print_step "Link Check" "checking documentation links..."
    local start end
    local internal_status="pass"
    local lychee_status="not-run"
    start=$(date +%s)

    if ! run_internal_markdown_link_check "${internal_report_md}"; then
      internal_status="fail"
    fi

    if check_command lychee; then
      local lychee_config="${REPO_ROOT}/.lychee.toml"
      local lychee_cmd=(
        lychee
        --no-progress
        "**/*.md"
        --exclude-path node_modules
        --exclude-path .git
        --format markdown
        --root-dir "${REPO_ROOT}"
        --output "${lychee_report_md}"
      )

      if [[ -f "${lychee_config}" ]]; then
        lychee_cmd+=(--config "${lychee_config}")
      fi

      if "${lychee_cmd[@]}"; then
        lychee_status="pass"
      else
        lychee_status="fail"
      fi
    else
      lychee_status="unavailable"
    fi

    {
      echo "# Documentation Link Check Report"
      echo ""
      echo "Generated: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
      echo ""
      echo "- Internal markdown checker: ${internal_status}"
      echo "- Lychee checker: ${lychee_status}"
      echo ""
      echo "## Internal markdown checker"
      echo ""
      if [[ -f "${internal_report_md}" ]]; then
        cat "${internal_report_md}"
      else
        echo "Internal checker report missing."
      fi
      echo ""
      echo "## Lychee checker"
      echo ""
      if [[ "${lychee_status}" == "unavailable" ]]; then
        echo 'Lychee not installed locally (`cargo install lychee`).'
      elif [[ -f "${lychee_report_md}" ]]; then
        cat "${lychee_report_md}"
      else
        echo "Lychee report missing."
      fi
    } > "${link_report_md}"

    if [[ "${internal_status}" == "pass" && ( "${lychee_status}" == "pass" || "${lychee_status}" == "unavailable" ) ]]; then
      end=$(date +%s)
      print_result "Link Check" "pass" "$((end - start))"
    else
      end=$(date +%s)
      print_result "Link Check" "fail" "$((end - start))"
      phase_failed=true
    fi

      {
        echo "# Docs Link Check Summary"
        echo ""
        echo "Generated: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
        echo ""
        if [[ "${STEP_RESULTS[Link Check]:-skip}" == "pass" ]]; then
          echo "✅ All checked links passed."
        else
          echo "⚠️ Link check reported issues."
        fi
        echo ""
        echo "- Internal checker: ${internal_status}"
        echo "- Lychee checker: ${lychee_status}"
        echo "- Report file: \`link-check-report.md\`"
        echo "- Status: ${STEP_RESULTS[Link Check]:-unknown}"
      } > "${link_summary_md}"

    cp "${link_summary_md}" "${ci_results_docs_dir}/summary.md"
  fi

  # --- CrewAI Tests ---
  if should_run "test-crewai"; then
    if [[ -d "${REPO_ROOT}/.crewai/tests" ]]; then
      print_step "CrewAI Tests" "running pytest..."
      if check_command pytest; then
        run_step "CrewAI Tests" pytest "${REPO_ROOT}/.crewai/tests/" -v --tb=short || phase_failed=true
      else
        run_step "CrewAI Tests" python3 -m pytest "${REPO_ROOT}/.crewai/tests/" -v --tb=short || phase_failed=true
      fi
    else
      print_result "CrewAI Tests" "skip" "0" "no .crewai/tests/ directory"
    fi
  fi

  # --- Website Build ---
  if should_run "test-website" || should_run "build-website"; then
    if [[ -d "${REPO_ROOT}/apps/web" ]]; then
      print_step "Website Build" "building website..."
      run_step "Website Build" pnpm --filter @template/web run build || phase_failed=true
    else
      print_result "Website Build" "skip" "0" "no apps/web directory"
    fi
  fi

  $phase_failed && return 1 || return 0
}

# =============================================================================
# PHASE 3: Deploy (skipped locally by default)
# =============================================================================

run_phase_3() {
  if ! $RUN_DEPLOY; then
    print_header "PHASE 3: Deploy"
    print_result "Preview Deploy" "skip" "0" "local mode (use --deploy to enable)"
    print_result "Production Deploy" "skip" "0" "local mode (use --deploy to enable)"
    return 0
  fi

  print_header "PHASE 3: Deploy"

  if ! check_env_for_deploy; then
    print_result "Deploy" "fail" "0" "missing Cloudflare credentials"
    return 1
  fi

  if ! check_command wrangler; then
    print_result "Deploy" "fail" "0" "wrangler not installed (npm i -g wrangler)"
    return 1
  fi

  print_step "Deploy" "deploying to Cloudflare Pages..."
  run_step "Cloudflare Deploy" wrangler pages deploy "${REPO_ROOT}/apps/web/dist" \
    --project-name=website \
    --branch=local-preview \
    || return 1
}

# =============================================================================
# PHASE 4: CrewAI Review (optional)
# =============================================================================

run_phase_4() {
  if ! $RUN_REVIEW && ! should_run "review"; then
    print_header "PHASE 4: AI Code Review"
    print_result "CrewAI Review" "skip" "0" "use --review to enable"
    return 0
  fi

  print_header "PHASE 4: AI Code Review"

  if ! check_env_for_review; then
    print_result "CrewAI Review" "skip" "0" "OPENROUTER_API_KEY not provided"
    return 0
  fi

  local provider
  provider=$(resolve_review_provider)
  case "$provider" in
    openrouter)
      echo -e "  ${DIM}LLM Provider: OpenRouter (default)${NC}"
      ;;
  esac

  local is_git_repo=false
  local has_commits=false
  if git -C "${REPO_ROOT}" rev-parse --git-dir &>/dev/null; then
    is_git_repo=true
    if git -C "${REPO_ROOT}" rev-parse HEAD &>/dev/null; then
      has_commits=true
    fi
  fi

  if ! $is_git_repo; then
    print_result "CrewAI Review" "skip" "0" "not a git repository"
    return 0
  fi

  local crewai_dir="${REPO_ROOT}/.crewai"
  local workspace_dir="${crewai_dir}/workspace"
  mkdir -p "${workspace_dir}/trace"

  print_step "Diff Generation" "creating diff for review..."
  local diff_file="${workspace_dir}/diff.txt"
  local diff_source="unknown"
  local diff_strategy="unknown"
  local diff_size=0
  local base_ref=""
  local merge_base=""

  local has_working_changes=false
  local has_staged_changes=false
  if $has_commits; then
    if ! git -C "${REPO_ROOT}" diff --quiet 2>/dev/null; then
      has_working_changes=true
    fi
    if ! git -C "${REPO_ROOT}" diff --cached --quiet 2>/dev/null; then
      has_staged_changes=true
    fi
  fi

  if $has_working_changes || $has_staged_changes; then
    git -C "${REPO_ROOT}" diff HEAD > "${diff_file}" 2>/dev/null
    diff_size=$(wc -l < "${diff_file}")
    diff_source="working tree vs HEAD (uncommitted changes)"
    diff_strategy="working-tree-vs-head"
    base_ref="HEAD"
    merge_base="HEAD"

  elif $has_commits; then
    local base_branch
    base_branch=$(git -C "${REPO_ROOT}" rev-parse --abbrev-ref HEAD 2>/dev/null)
    local default_base="main"
    if [[ "$base_branch" == "main" || "$base_branch" == "master" ]]; then
      default_base="HEAD~1"
    fi

    base_ref="${default_base}"
    if git -C "${REPO_ROOT}" show-ref --verify --quiet "refs/remotes/origin/${default_base}"; then
      base_ref="origin/${default_base}"
    fi

    merge_base=$(git -C "${REPO_ROOT}" merge-base "${base_ref}" HEAD 2>/dev/null || echo "")

    if git -C "${REPO_ROOT}" diff "${base_ref}"...HEAD > "${diff_file}" 2>/dev/null; then
      diff_size=$(wc -l < "${diff_file}")
    fi

    if [[ "$diff_size" -eq 0 ]]; then
      if [[ -n "$merge_base" ]]; then
        git -C "${REPO_ROOT}" diff "${merge_base}"...HEAD > "${diff_file}" 2>/dev/null || true
        diff_size=$(wc -l < "${diff_file}")
      fi
    fi

    if [[ "$diff_size" -eq 0 ]]; then
      git -C "${REPO_ROOT}" show HEAD > "${diff_file}" 2>/dev/null || true
      diff_size=$(wc -l < "${diff_file}")
      diff_source="last commit (git show HEAD)"
      diff_strategy="last-commit-show"
    else
      diff_source="branch diff (${base_ref}...HEAD)"
      diff_strategy="branch-merge-base-diff"
    fi
  else
    git -C "${REPO_ROOT}" diff --cached > "${diff_file}" 2>/dev/null || true
    diff_size=$(wc -l < "${diff_file}")
    diff_source="staged changes (initial commit)"
    diff_strategy="staged-initial"
    base_ref="(none)"
    merge_base=""
  fi

  echo -e "  ${DIM}Source: ${diff_source}${NC}"
  if [[ -n "$base_ref" ]]; then
    echo -e "  ${DIM}Base ref: ${base_ref}${NC}"
  fi
  if [[ -n "$merge_base" ]]; then
    echo -e "  ${DIM}Merge base: ${merge_base}${NC}"
  fi
  echo -e "  ${DIM}Generated diff: ${diff_size} lines${NC}"

  if [[ "$diff_size" -eq 0 ]]; then
    echo -e "  ${WARN} No changes detected — nothing to review."
    print_result "CrewAI Review" "skip" "0" "no changes to review"
    return 0
  fi

  local commit_sha
  commit_sha=$(git -C "${REPO_ROOT}" rev-parse HEAD 2>/dev/null || echo "local")
  local repo_name
  repo_name=$(basename "${REPO_ROOT}")

  local changed_files
  local compare_ref=""
  local snapshot_mode=""
  if $has_working_changes || $has_staged_changes; then
    changed_files=$(git -C "${REPO_ROOT}" diff --name-only HEAD 2>/dev/null || echo "")
    compare_ref="HEAD"
    snapshot_mode="working-tree"
  elif $has_commits; then
    changed_files=$(git -C "${REPO_ROOT}" diff --name-only "${default_base}"...HEAD 2>/dev/null || git -C "${REPO_ROOT}" diff --name-only HEAD 2>/dev/null || echo "")
    compare_ref="${merge_base:-${base_ref}}"
    snapshot_mode="branch"
  else
    changed_files=$(git -C "${REPO_ROOT}" diff --cached --name-only 2>/dev/null || echo "")
    compare_ref=""
    snapshot_mode="initial"
  fi

  local additions deletions file_count
  if $has_working_changes || $has_staged_changes; then
    additions=$(git -C "${REPO_ROOT}" diff --numstat HEAD 2>/dev/null | awk '{s+=$1} END {print s+0}')
    deletions=$(git -C "${REPO_ROOT}" diff --numstat HEAD 2>/dev/null | awk '{s+=$2} END {print s+0}')
  elif $has_commits; then
    additions=$(git -C "${REPO_ROOT}" diff --numstat "${default_base}"...HEAD 2>/dev/null | awk '{s+=$1} END {print s+0}' || echo "0")
    deletions=$(git -C "${REPO_ROOT}" diff --numstat "${default_base}"...HEAD 2>/dev/null | awk '{s+=$2} END {print s+0}' || echo "0")
  else
    additions=$(git -C "${REPO_ROOT}" diff --cached --numstat 2>/dev/null | awk '{s+=$1} END {print s+0}' || echo "0")
    deletions=$(git -C "${REPO_ROOT}" diff --cached --numstat 2>/dev/null | awk '{s+=$2} END {print s+0}' || echo "0")
  fi
  file_count=$(echo "$changed_files" | grep -c . || echo "0")

  local review_labels_json="[]"
  if $RUN_COMPLETE_FULL_REVIEW; then
    review_labels_json='["crewai:full-review","crewai:complete-full-review"]'
    echo -e "  ${DIM}Labels: crewai:full-review, crewai:complete-full-review (all specialists, full repo scope)${NC}"
  elif $RUN_FULL_REVIEW; then
    review_labels_json='["crewai:full-review"]'
    echo -e "  ${DIM}Labels: crewai:full-review (all 10 specialist crews)${NC}"
  elif [[ -n "$REVIEW_LABELS" ]]; then
    review_labels_json=$(echo "$REVIEW_LABELS" | python3 -c "import json,sys; print(json.dumps(sys.stdin.read().strip().split(',')))")
    echo -e "  ${DIM}Labels: ${REVIEW_LABELS}${NC}"
  fi

  python3 -c "
import json, sys
files = [f for f in '''${changed_files}'''.strip().split('\n') if f]
data = {
    'pr_number': 'local',
    'commit_sha': '${commit_sha}',
    'base_ref': '''${base_ref}''',
    'merge_base': '''${merge_base}''',
    'diff_strategy': '''${diff_strategy}''',
    'labels': ${review_labels_json},
    'files_changed': ${file_count},
    'additions': ${additions},
    'deletions': ${deletions},
    'file_list': files,
}
with open('${workspace_dir}/diff.json', 'w') as f:
    json.dump(data, f, indent=2)
" 2>/dev/null || true

  python3 -c "
import json
scope = {
  'contract_version': '2026-02-14',
  'tier': 'quick' if '''${RUN_FULL_REVIEW}''' != 'true' else 'branch',
  'diff_strategy': '''${diff_strategy}''',
  'base_ref': '''${base_ref}''',
  'head_ref': 'HEAD',
  'head_sha': '''${commit_sha}''',
  'merge_base': '''${merge_base}''',
}
with open('${workspace_dir}/scope.json', 'w') as f:
    json.dump(scope, f, indent=2)
" 2>/dev/null || true

  local commit_messages
  commit_messages=$(git -C "${REPO_ROOT}" log --oneline -5 2>/dev/null || echo "local run")
  python3 -c "
import json
msgs = '''${commit_messages}'''.strip().split('\n')
data = {'commit_count': len(msgs), 'commit_messages': msgs}
with open('${workspace_dir}/commits.json', 'w') as f:
    json.dump(data, f, indent=2)
" 2>/dev/null || true

  # Write commit_messages.txt for quick review agent (expects plain text)
  echo "${commit_messages}" > "${workspace_dir}/commit_messages.txt"

  REPO_ROOT="${REPO_ROOT}" \
  WORKSPACE_DIR="${workspace_dir}" \
  COMPARE_REF="${compare_ref}" \
  SNAPSHOT_MODE="${snapshot_mode}" \
  CHANGED_FILES_RAW="${changed_files}" \
  python3 - <<'PY'
import json
import os
import re
import subprocess
from pathlib import Path

repo_root = Path(os.environ["REPO_ROOT"])
workspace_dir = Path(os.environ["WORKSPACE_DIR"])
compare_ref = os.environ.get("COMPARE_REF", "").strip()
snapshot_mode = os.environ.get("SNAPSHOT_MODE", "").strip() or "unknown"
changed_files_raw = os.environ.get("CHANGED_FILES_RAW", "")

changed_files = [line.strip() for line in changed_files_raw.splitlines() if line.strip()]
max_files = 50
max_chars = 18000
target_dir = workspace_dir / "changed_files"
target_dir.mkdir(parents=True, exist_ok=True)


def read_truncated_file(path: Path):
    if not path.exists() or not path.is_file():
        return "", False, False
    text = path.read_text(errors="replace")
    truncated = len(text) > max_chars
    if truncated:
        text = text[: max_chars - 120] + "\n...\n[truncated local file snapshot]"
    return text, True, truncated


def git_show(ref: str, rel_path: str):
    if not ref:
        return "", False, False
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{ref}:{rel_path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return "", False, False
    text = proc.stdout
    truncated = len(text) > max_chars
    if truncated:
        text = text[: max_chars - 120] + "\n...\n[truncated baseline snapshot]"
    return text, True, truncated


def git_patch(ref: str, rel_path: str):
    cmd = ["git", "-C", str(repo_root), "diff"]
    if ref:
        cmd.append(ref)
    cmd.extend(["--", rel_path])
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    text = proc.stdout if proc.returncode == 0 else ""
    truncated = len(text) > max_chars
    if truncated:
        text = text[: max_chars - 120] + "\n...\n[truncated per-file patch]"
    return text, bool(text), truncated


manifest_items = []
for idx, rel_path in enumerate(changed_files[:max_files], start=1):
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", rel_path)
    prefix = f"{idx:03d}_{safe_name}"

    after_text, after_exists, after_truncated = read_truncated_file(repo_root / rel_path)
    before_text, before_exists, before_truncated = git_show(compare_ref, rel_path)
    patch_text, patch_exists, patch_truncated = git_patch(compare_ref, rel_path)

    after_file = f"changed_files/{prefix}.after.txt"
    before_file = f"changed_files/{prefix}.before.txt"
    patch_file = f"changed_files/{prefix}.patch.diff"

    (workspace_dir / after_file).write_text(after_text)
    (workspace_dir / before_file).write_text(before_text)
    (workspace_dir / patch_file).write_text(patch_text)

    manifest_items.append(
        {
            "path": rel_path,
            "mode": snapshot_mode,
            "compare_ref": compare_ref,
            "after_file": after_file,
            "before_file": before_file,
            "patch_file": patch_file,
            "after_exists": after_exists,
            "before_exists": before_exists,
            "patch_exists": patch_exists,
            "after_truncated": after_truncated,
            "before_truncated": before_truncated,
            "patch_truncated": patch_truncated,
        }
    )

manifest = {
    "contract_version": "2026-02-14",
    "mode": snapshot_mode,
    "compare_ref": compare_ref,
    "total_changed_files": len(changed_files),
    "captured_files": len(manifest_items),
    "capture_limit": max_files,
    "items": manifest_items,
}

(workspace_dir / "changed_files_index.json").write_text(json.dumps(manifest, indent=2))

lines = [
    "# Changed file snapshots",
    "",
    f"- Mode: {snapshot_mode}",
    f"- Compare ref: {compare_ref or '(none)'}",
    f"- Captured files: {len(manifest_items)}/{len(changed_files)}",
    "",
    "Read `changed_files_index.json` first, then load only needed per-file artifacts.",
    "",
]
for item in manifest_items:
    lines.append(f"- `{item['path']}`")
    lines.append(f"  - before: `{item['before_file']}`")
    lines.append(f"  - after: `{item['after_file']}`")
    lines.append(f"  - patch: `{item['patch_file']}`")

(workspace_dir / "changed_files_manifest.md").write_text("\n".join(lines))
PY

  python3 -c "
import json
from pathlib import Path

workspace = Path('${workspace_dir}')
diff_path = workspace / 'diff.txt'
scope_path = workspace / 'scope.json'
quick_path = workspace / 'quick_review.json'
ci_path = workspace / 'ci_summary.json'
commits_path = workspace / 'commits.json'

def load_json(path):
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}

diff_text = diff_path.read_text() if diff_path.exists() else ''
if len(diff_text) > 12000:
    diff_excerpt = diff_text[:7000] + '\n...\n' + diff_text[-5000:]
else:
    diff_excerpt = diff_text

scope = load_json(scope_path)
commits = load_json(commits_path)
ci = load_json(ci_path)
quick = load_json(quick_path)
local_ci_md = (workspace / 'local_ci_summary.md').read_text() if (workspace / 'local_ci_summary.md').exists() else ''
link_check_summary_md = (workspace / 'link-check-summary.md').read_text() if (workspace / 'link-check-summary.md').exists() else ''
link_check_report_md = (workspace / 'link-check-report.md').read_text() if (workspace / 'link-check-report.md').exists() else ''

pack = {
    'contract_version': '2026-02-14',
    'purpose': 'compact_review_context',
    'scope': scope,
    'commit_messages': commits.get('commit_messages', []),
    'ci_summary': ci.get('summary', ''),
    'quick_summary': quick.get('summary', ''),
    'local_ci_summary_markdown': local_ci_md,
    'link_check_summary_markdown': link_check_summary_md,
    'link_check_report_markdown': link_check_report_md,
    'changed_files_index': load_json(workspace / 'changed_files_index.json'),
    'diff_excerpt': diff_excerpt,
}

(workspace / 'context_pack.json').write_text(json.dumps(pack, indent=2))

lines = [
    '# Context Pack',
    '',
    '## Scope',
    '- Tier: ' + str(scope.get('tier', 'unknown')),
    '- Diff strategy: ' + str(scope.get('diff_strategy', 'unknown')),
    '- Base ref: ' + str(scope.get('base_ref', 'unknown')),
    '- Merge base: ' + str(scope.get('merge_base', '')),
    '',
    '## Recent commits',
]
for msg in commits.get('commit_messages', [])[:8]:
    lines.append('- ' + str(msg))

if ci.get('summary'):
    lines.extend(['', '## CI summary', ci.get('summary', '')])

if quick.get('summary'):
    lines.extend(['', '## Quick review summary', quick.get('summary', '')])

if local_ci_md:
    lines.extend(['', '## Local CI summary markdown', local_ci_md])

if link_check_summary_md:
    lines.extend(['', '## Docs link-check summary markdown', link_check_summary_md])

if link_check_report_md:
    lines.extend(['', '## Docs link-check report markdown', link_check_report_md])

changed_index = load_json(workspace / 'changed_files_index.json')
if changed_index:
    lines.extend([
        '',
        '## Changed file snapshots',
        '- Read changed_files_index.json for full mapping',
        '- Read only the specific file snapshots you need from changed_files/',
        '- This avoids loading all code/diffs into context at once',
    ])

lines.extend(['', '## Diff excerpt', '[DIFF BEGIN]', diff_excerpt, '[DIFF END]'])
(workspace / 'context_pack.md').write_text('\n'.join(lines))
" 2>/dev/null || true

  export PR_NUMBER="local"
  export COMMIT_SHA="${commit_sha}"
  export GITHUB_REPOSITORY="local/${repo_name}"
  export GITHUB_WORKSPACE="${REPO_ROOT}"
  export CORE_CI_RESULT="success"

  # Run CrewAI
  print_step "CrewAI Review" "running AI code review..."
  local start
  start=$(date +%s)
  local review_timeout_seconds="${CREWAI_REVIEW_TIMEOUT_SECONDS:-}"
  if [[ -z "$review_timeout_seconds" ]]; then
    if [[ "$RUN_FULL_REVIEW" == "true" ]]; then
      review_timeout_seconds="240"
    else
      review_timeout_seconds="90"
    fi
  fi
  local summary_file="${workspace_dir}/final_summary.md"
  echo -e "  ${DIM}Review timeout: ${review_timeout_seconds}s${NC}"

  local review_success=false
  local primary_exit=0

  if (cd "${crewai_dir}" && timeout "${review_timeout_seconds}" python3 main.py) 2>&1 | {
    if $VERBOSE; then
      cat
    else
      while IFS= read -r line; do
        case "$line" in
          *"STEP"*|*"✅"*|*"❌"*|*"⚠️"*|*"🔬"*|*"complete"*)
            echo -e "     ${DIM}${line}${NC}"
            ;;
        esac
      done
    fi
  }; then
    review_success=true
  else
    primary_exit=$?
    if [[ $primary_exit -eq 124 ]]; then
      echo -e "  ${YELLOW}${WARN}${NC} CrewAI review timed out after ${review_timeout_seconds}s"
      if [[ ! -f "$summary_file" ]]; then
        printf '%s\n' \
          "## ❌ Review Aborted" \
          "" \
          "The review timed out before completion." \
          "" \
          "- Error: Timed out after ${review_timeout_seconds}s" \
          "- Behavior: fail-fast timeout guard triggered" \
          "- Action: reduce diff scope or switch provider, then rerun." \
          "" \
          "---" \
          "" \
          "## 💰 Cost Tracking" \
          "" \
          "No API calls recorded." \
          > "$summary_file"
      fi
    fi
  fi

  local end; end=$(date +%s)
  if [[ "$review_success" == "true" ]]; then
    print_result "CrewAI Review" "pass" "$((end - start))"
  else
    print_result "CrewAI Review" "fail" "$((end - start))"
  fi

  # Display summary if it exists
  if [[ -f "$summary_file" ]]; then
    echo ""
    echo -e "${CYAN}${BOLD}  ┌─ Review Summary ───────────────────────────────────┐${NC}"
    head -30 "$summary_file" | while IFS= read -r line; do
      echo -e "${CYAN}  │${NC} $line"
    done
    local total_lines
    total_lines=$(wc -l < "$summary_file")
    if [[ "$total_lines" -gt 30 ]]; then
      echo -e "${CYAN}  │${NC} ${DIM}... ($((total_lines - 30)) more lines in .crewai/workspace/final_summary.md)${NC}"
    fi
    echo -e "${CYAN}  └──────────────────────────────────────────────────────┘${NC}"
    echo ""
    echo -e "  ${DIM}Full review: .crewai/workspace/final_summary.md${NC}"
    echo -e "  ${DIM}All outputs: .crewai/workspace/*.json${NC}"

    if grep -q "^## 💰 Cost" "$summary_file"; then
      echo ""
      echo -e "${CYAN}${BOLD}  ┌─ Pricing / Cost ───────────────────────────────────┐${NC}"
      local cost_panel
      cost_panel=$(python3 - "$summary_file" <<'PY'
import sys


def flush_table(rows, out):
    if not rows:
        return
    col_count = max(len(row) for row in rows)
    widths = []
    for idx in range(col_count):
        widths.append(max(len(row[idx]) if idx < len(row) else 0 for row in rows))

    def format_row(row):
        cells = row + [""] * (col_count - len(row))
        return " | ".join(cells[idx].ljust(widths[idx]) for idx in range(col_count))

    out.append(format_row(rows[0]))
    out.append("-+-".join("-" * width for width in widths))
    for row in rows[1:]:
        out.append(format_row(row))


summary_path = sys.argv[1]
with open(summary_path, encoding="utf-8") as handle:
    lines = handle.read().splitlines()

start = None
for idx, line in enumerate(lines):
    if line.startswith("## 💰 Cost"):
        start = idx
        break

if start is None:
    raise SystemExit(0)

section = []
for line in lines[start + 1:]:
    if line.startswith("## ") and not line.startswith("## 💰 Cost"):
        break
    section.append(line.rstrip())

while section and not section[0].strip():
    section.pop(0)
while section and not section[-1].strip():
    section.pop()

output = []
table_rows = []

for line in section:
    stripped = line.strip()
    if stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 3:
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if cells and all(set(cell) <= set("-: ") for cell in cells):
            continue
        table_rows.append(cells)
        continue

    flush_table(table_rows, output)
    table_rows = []
    output.append(line)

flush_table(table_rows, output)

for line in output:
    print(line)
PY
)
      while IFS= read -r line; do
        echo -e "${CYAN}  │${NC} $line"
      done <<< "$cost_panel"
      echo -e "${CYAN}  └──────────────────────────────────────────────────────┘${NC}"
    fi
  fi

  if [[ "$review_success" == "false" ]]; then
    return 1
  fi
}

# =============================================================================
# Summary
# =============================================================================

print_summary() {
  local total_end
  total_end=$(date +%s)
  local total_duration=$((total_end - TOTAL_START))

  echo ""
  echo -e "${BOLD}${BLUE}${PHASE}${PHASE}${PHASE}${PHASE}${PHASE}${PHASE}${PHASE}${PHASE}${PHASE}${NC}"
  echo -e "${BOLD}  📊 CI Results${NC}"
  echo -e "${BOLD}${BLUE}${PHASE}${PHASE}${PHASE}${PHASE}${PHASE}${PHASE}${PHASE}${PHASE}${PHASE}${NC}"
  echo ""

  printf "  ${BOLD}%-24s %-10s %s${NC}\n" "Step" "Status" "Duration"
  printf "  %-24s %-10s %s\n" "────────────────────────" "──────────" "────────"

  for step in "${!STEP_RESULTS[@]}"; do
    local status="${STEP_RESULTS[$step]}"
    local duration="${STEP_DURATIONS[$step]:-0}"
    local status_icon

    case "$status" in
      pass) status_icon="${GREEN}${PASS} pass${NC}" ;;
      fail) status_icon="${RED}${FAIL} FAIL${NC}" ;;
      skip) status_icon="${YELLOW}${SKIP}skip${NC}" ;;
      warn) status_icon="${YELLOW}${WARN} warn${NC}" ;;
    esac

    printf "  %-24s %b %b\n" "$step" "$status_icon" "${DIM}${duration}s${NC}"
  done

  echo ""
  echo -e "  ${GREEN}Passed: ${STEPS_PASSED}${NC}  ${RED}Failed: ${STEPS_FAILED}${NC}  ${YELLOW}Skipped: ${STEPS_SKIPPED}${NC}  ${DIM}Total: ${total_duration}s${NC}"
  echo ""

  if [[ $STEPS_FAILED -gt 0 ]]; then
    echo -e "  ${RED}${BOLD}${FAIL} CI FAILED${NC}"
    return 1
  else
    echo -e "  ${GREEN}${BOLD}${PASS} CI PASSED${NC}"
    return 0
  fi
}

# =============================================================================
# Main
# =============================================================================

main() {
  cd "${REPO_ROOT}"

  trap release_run_lock EXIT
  acquire_run_lock

  echo ""
  echo -e "${BOLD}${BLUE}  🚀 Local CI Runner${NC}"
  echo -e "${DIM}  Same pipeline as GitHub Actions — minus the cloud.${NC}"
  echo -e "${DIM}  $(date '+%Y-%m-%d %H:%M:%S')${NC}"

  # Check required tools
  check_dependencies

  clean_workspace

  # Single step mode
  if [[ -n "$SINGLE_STEP" ]]; then
    print_header "Running: ${SINGLE_STEP}"
    case "$SINGLE_STEP" in
      format|lint|lint-md|lint-css|typecheck|commitlint)
        run_phase_1 || true ;;
      link-check|test-crewai|test-website|build-website)
        run_phase_2 || true ;;
      review)
        RUN_REVIEW=true
        run_phase_4 || true ;;
      deploy)
        RUN_DEPLOY=true
        run_phase_3 || true ;;
      *)
        echo -e "${RED}Unknown step: ${SINGLE_STEP}${NC}"
        exit 1 ;;
    esac
    write_workspace_ci_summary_markdown
    print_summary
    return $?
  fi

  # Full pipeline
  run_phase_1 || true
  run_phase_2 || true
  run_phase_3 || true

  write_workspace_ci_summary_markdown

  run_phase_4 || true

  write_workspace_ci_summary_markdown
  print_summary
}

main "$@"
