# Sprint W07 2026 — Kanban Board

_Sprint W07: Feb 10–14, 2026 · opencode repo_
_Human · Last updated: 2026-02-15 16:12_

---

> 📌 **Sprint rollover:** Sprint W07 tracking is now closed. Active backlog and in-progress work moved to `docs/project/kanban/sprint-2026-w08-crewai-review-hardening-and-memory.md`.

## 📋 Board Overview

**Period:** 2026-02-10 → 2026-02-14
**Goal:** Ship the agentic documentation system plus production-ready local CI/CrewAI review reliability improvements, root scaffolding, and idempotent script standards.
**WIP Limit:** 3 items In Progress

### Visual board

_Kanban board showing Sprint W07 work distribution across workflow columns, including explicit Won't Do transparency:_

```mermaid
kanban
  Backlog
    task1[🔍 Verify Mermaid rendering on GitHub]
    task14[✅ Commit and push current uncommitted work]
  In Progress
    task10[🧾 Finalize source-of-truth records and publish branch updates]
  In Review
  Done
    task6[📊 Mermaid style guide + 23 type files]
    task7[📝 Markdown style guide + 9 templates]
    task8[🗂️ Everything is Code philosophy]
    task9[📋 New ADRs for project decisions]
    task3["🧹 Legacy file cleanup (10 files)"]
    task4[📄 AGENTS.md created at repo root]
    task5["🤖 CrewAI review bug fixes (5/5)"]
    task11[📓 notebooks/ + src/ scaffolding added]
    task12[♻️ Idempotent script guide + read-in wiring]
    task13[🧪 Local --review rerun passes end-to-end]
    task15[💰 Local pricing/cost breakdown shown in terminal output]
    task16[⚡ Fail-fast timeout guard for no-response/out-of-credit paths]
    task17["🧾 Cost tracker parity verified (non-empty audit table)"]
    task18[🧹 markdownlint excludes .crewai/workspace artifacts]
    task19[✅ Full ./scripts/ci-local.sh --review pass verified]
    task20[📚 AGENTS completion gate + ADR-004 source-of-truth sync]
    task21[🔁 Live progress sync loop enforced in AGENTS/workflow docs]
    task22[🧪 ci-local pre-push rule + hosted-env skip rationale policy]
    task23[⚡ NVIDIA timeout handling hardened with explicit error surfacing]
    task24[🧠 Local quick-review now runs 3 reviewer passes with per-pass summaries]
    task25[📐 Local pricing/cost panel now renders aligned terminal columns]
    task26[🗂️ Monorepo layout modernized: website moved to apps/web]
    task27[🏗️ New workspace scaffold: apps/services/packages/data-sql]
    task28["📚 Federated ADR governance added (global + subsystem logs)"]
    task29[🤖 CrewAI local ADR log created with initial subsystem ADRs]
    task30[🧭 Global baseline ADR added for monorepo decision map]
    task31["🔁 CrewAI provider chain clarified (NVIDIA -> OpenRouter)"]
    task32[🧱 CI regrouped into stage gates with CrewAI review last]
    task33[🧪 Local CI parity rerun passed after stage-gate regrouping]
    task34[🧩 CI README Mermaid parse error fixed and phase naming normalized]
    task35[🔒 CI/deploy concurrency guards added and stage-gate dependencies clarified]
    task36[🧪 Post-hardening local CI parity rerun completed; quick-review instability remains tracked]
    task37[🧼 Phase-1 commitlint ELIFECYCLE lifecycle noise removed in local CI]
    task38[🧪 Full local CI rerun passed after commitlint UX polish]
    task39[⚡ Local provider baseline switched to OpenRouter default with explicit NVIDIA opt-in]
    task40[📦 Full-review and specialist outputs now always materialize structured JSON artifacts]
    task43[🧠 Specialists now run with selective repo tools + parsed-result recovery]
    task44[🚫 Specialists now emit explicit not-applicable outputs instead of simulated findings]
    task45[🧾 Final summary UX overhaul: executive-first layout + optimized cost section]
    task46[🎯 Quick-review signal polish: remove low-value fallback noise]
    task47[🧠 Final sweep: scoped specialist findings + clean persistent memory baseline]
    task48[⚖️ License policy finalized: Apache-2.0 + NOTICE attribution baseline]
    task49[🧭 Executive summary rewrite: action-first, less workflow narration]
    task50[🧪 Local full-review multipass restored + remove forced details separators]
    task51[🧹 Remove duplicate specialist status rows from top workflow guide]
    task52[🔒 Local CI lock + workspace reset + specialist domain-focus tightening]
    task53["🌐 Add complete-full-review mode (local flag + PR label trigger semantics)"]
    task54[🛠️ Fix GHA CrewAI prep crash for list-shaped commits.json context pack]
    task55[🧠 Add persistent memory CLI + prompt-memory propagation]
    task56[⚖️ Fix legal metadata drift: pyproject license aligned to Apache-2.0]
  Blocked
  Won't Do
    task41[⛔ Keep NVIDIA as default local provider]
    task42[⛔ Depend only on CrewAI tool-write side effects for local artifacts]
```

> ⚠️ **Always show all 6 columns** — Even if a column has no items, include it with a placeholder. This makes the board structure explicit and ensures categories are never forgotten. Use a placeholder like `[No items yet]` when a column is empty.

---

## 🚦 Board Status

| Column             | Count | WIP Limit | Status                              |
| ------------------ | ----- | --------- | ----------------------------------- |
| 📋 **Backlog**     | 0     | —         | Moved to Sprint W08 board           |
| 🔄 **In Progress** | 0     | 3         | Moved to Sprint W08 board           |
| 🔍 **In Review**   | 0     | —         | —                                   |
| ✅ **Done**        | 50    | —         | Core docs + CI/review + scaffolding |
| 🚫 **Blocked**     | 0     | —         | Clear                               |
| 🚫 **Won't Do**    | 2     | —         | Explicitly declined with rationale  |

> ⚠️ **Always include all 6 columns** — Each column represents a workflow state. Even if count is 0, keep the row visible. This prevents categories from being overlooked.

---

## 🔄 Rollover map

_Rollover mapping from closed W07 columns into active W08 tracking, keeping only historical records in this board:_

```mermaid
flowchart LR
    accTitle: Sprint W07 to W08 rollover map
    accDescr: Shows how W07 active items were moved to W08 while completed records remained in W07 history.

    w07b["W07 Backlog (2)"] --> w08b["W08 Backlog (2)"]
    w07p["W07 In Progress (1)"] --> w08p["W08 In Progress (1)"]
    w07d["W07 Done (historical)"] --> archive["W07 archived tracking"]

    classDef source fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e3a5f
    classDef target fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d

    class w07b,w07p,w07d source
    class w08b,w08p,archive target
```

---

## 📋 Backlog

_Prioritized top-to-bottom. Top items are next to be pulled. Include at least one placeholder item if empty._

> 🔄 **Moved to Sprint W08:** All remaining backlog items were rolled into `docs/project/kanban/sprint-2026-w08-crewai-review-hardening-and-memory.md` for active tracking.

| #   | Item                    | Priority | Estimate | Assignee | Notes                                    |
| --- | ----------------------- | -------- | -------- | -------- | ---------------------------------------- |
| -   | _(Moved to Sprint W08)_ | —        | —        | —        | Active backlog tracking continues in W08 |

---

## 🔄 In Progress

_Items currently being worked on. Include at least one placeholder item if empty._

> 🔄 **Moved to Sprint W08:** In-progress execution was carried forward to the new weekly board.

| Item                    | Assignee | Started | Expected | Days in column | Aging | Status                                       |
| ----------------------- | -------- | ------- | -------- | -------------- | ----- | -------------------------------------------- |
| _(Moved to Sprint W08)_ | —        | —       | —        | —              | —     | Active in-progress tracking now lives in W08 |

> 💡 **Aging indicator:** 🟢 Under expected time · 🟡 At expected time · 🔴 Over expected time — items aging red need attention or re-scoping.

> ⚠️ **WIP limit:** 0 / 3. Under limit.

---

## 🔍 In Review

_Items awaiting or in code review. Include at least one placeholder item if empty._

| Item | Author | Reviewer | PR  | Days in review | Aging | Status           |
| ---- | ------ | -------- | --- | -------------- | ----- | ---------------- |
|      |        |          |     |                |       | _[No items yet]_ |

---

## ✅ Done

_Completed this period. Include at least one placeholder item if empty._

| Item                                                                                                                         | Assignee   | Completed | Cycle time | PR                                                                 |
| ---------------------------------------------------------------------------------------------------------------------------- | ---------- | --------- | ---------- | ------------------------------------------------------------------ |
| Mermaid style guide + 24 diagram files (23 types + complex examples)                                                         | Human + AI | Feb 13    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| Markdown style guide + 9 templates (upgraded to 2026 standards)                                                              | Human + AI | Feb 13    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| "Everything is Code" philosophy — woven into style guide + 3 templates                                                       | Human + AI | Feb 13    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| New ADRs (docs system, Mermaid standards, Everything is Code)                                                                | Human + AI | Feb 13    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| Legacy file cleanup — 10 files rewritten/cleaned, perplexity/ deleted                                                        | Human + AI | Feb 13    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| AGENTS.md created at repo root — routes agents to style guides                                                               | Human + AI | Feb 13    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| Example files (PR, issue, kanban) updated to reflect all cleanup work                                                        | Human + AI | Feb 13    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| Local review pipeline fixes (5 bugs resolved in CrewAI + CI script)                                                          | Human + AI | Feb 13    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| Added root scaffolding for `notebooks/` and `src/` with README files                                                         | Human + AI | Feb 13    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| Added idempotent script design standards + read-in references                                                                | Human + AI | Feb 13    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| End-to-end local `./scripts/ci-local.sh --review` rerun (passes; model outputs limited by external credit availability)      | Human + AI | Feb 13    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| Local terminal now displays pricing/cost section from review summary                                                         | Human + AI | Feb 13    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| Fail-fast timeout guard added (`CREWAI_REVIEW_TIMEOUT_SECONDS`, default 90s)                                                 | Human + AI | Feb 13    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| NVIDIA timeout handling hardened (`CREWAI_NVIDIA_TIMEOUT_SECONDS`, explicit timeout error output)                            | Human + AI | Feb 13    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| Monorepo modernization: moved `website/` to `apps/web/` and updated CI/deploy path usage                                     | Human + AI | Feb 14    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| Added polyglot workspace scaffolding (`apps/`, `services/`, `packages/`, `data/sql/`) and linked AGENTS entrypoints          | Human + AI | Feb 14    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| Federated ADR governance adopted for global + subsystem decision logs                                                        | Human + AI | Feb 14    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| CrewAI subsystem ADR log initialized with provider/failover and review-shape ADRs                                            | Human + AI | Feb 14    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| CI workflow regrouped into stage-gated orchestration with CrewAI review last                                                 | Human + AI | Feb 14    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| Local CI parity rerun verified after CI regrouping (`./scripts/ci-local.sh --review`)                                        | Human + AI | Feb 14    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| CI README Mermaid parse error fixed and phase labels normalized to 1/2/3/4 structure                                         | Human + AI | Feb 14    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| Added workflow/deploy concurrency controls and explicit stage-gate dependency visualization                                  | Human + AI | Feb 14    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| Post-hardening local parity rerun validated CI phase behavior; quick-review NVIDIA instability remains non-fatal and tracked | Human + AI | Feb 14    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| Removed local Phase-1 commitlint `ELIFECYCLE` lifecycle noise while preserving warning semantics                             | Human + AI | Feb 14    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| Full local `./scripts/ci-local.sh --review` rerun passed after commitlint UX polish; fallback behavior remains deterministic | Human + AI | Feb 14    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| Local provider baseline switched to OpenRouter default (`gemini-2.5-flash-lite`) with explicit `--nvidia-nim` opt-in path    | Human + AI | Feb 14    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| Full-review and specialist runs now synthesize missing JSON artifacts to keep final summary generation complete and readable | Human + AI | Feb 14    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| Added review-scope contract artifact (`scope.json`) in local + CI prep for merge-base-aware tiered analysis                  | Human + AI | Feb 14    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| Added output validation ledger and new data-engineering specialist crew with full-router coverage                            | Human + AI | Feb 14    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| Added local context-pack generation plus resilient structured local full/specialist review path                              | Human + AI | Feb 14    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| Enabled selective-retrieval specialist execution (repo tools per specialist + parsed-result recovery before local fallback)  | Human + AI | Feb 14    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |
| Eliminated simulated specialist findings with deterministic no-relevant domain outputs                                       | Human + AI | Feb 14    | 1 day      | [#1](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md) |

---

## 🚫 Blocked

_Items that cannot proceed. Always include at least the placeholder — blocked items are high-signal and should never be hidden._

| Item | Assignee | Blocked since | Blocked by | Escalated to | Unblock action       |
| ---- | -------- | ------------- | ---------- | ------------ | -------------------- |
|      |          |               |            |              | _[No blocked items]_ |

> 🔴 **0 items blocked.** Clear sprint.

---

## 🚫 Won't Do

_Explicitly out of scope for this board period. Capture rationale so these decisions are transparent and auditable. Include placeholder if empty._

| Item                                                        | Date decided | Decision owner | Rationale                                                                                    | Revisit trigger                                     |
| ----------------------------------------------------------- | ------------ | -------------- | -------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| Keep NVIDIA as default local provider                       | 2026-02-14   | Human + AI     | Default-path speed/reliability was better with OpenRouter baseline; NVIDIA remains opt-in.   | Revisit if OpenRouter reliability degrades          |
| Depend only on CrewAI tool-write side effects for artifacts | 2026-02-14   | Human + AI     | Local reliability required resilient structured persistence plus validation-ledger tracking. | Revisit if CrewAI persistence becomes deterministic |

### Why these were declined

- The template repo optimizes for first-run reliability and clear operational behavior for new adopters.
- The declined items increased variance in local outcomes and made troubleshooting harder for students and maintainers.
- Equivalent capability is preserved with safer alternatives (explicit NVIDIA opt-in, validation-aware structured persistence).

---

## 📊 Metrics

### This period

| Metric                             | Value   | Target | Trend |
| ---------------------------------- | ------- | ------ | ----- |
| **Throughput** (items completed)   | 50      | 4      | ↑     |
| **Avg cycle time** (start → done)  | 1.0 day | —      | —     |
| **Avg lead time** (created → done) | 1.0 day | —      | —     |
| **Avg review time**                | —       | —      | —     |
| **Flow efficiency**                | ~85%    | 40%    | ↑     |
| **Blocked items**                  | 0       | 0      | →     |
| **WIP limit breaches**             | 0       | 0      | →     |
| **Items aging red**                | 0       | 0      | →     |

> 💡 **Flow efficiency** = active work time ÷ total cycle time × 100. A healthy team targets 40%+. Below 15% means items spend most of their time waiting, not being worked on.

> 📌 **Note:** This is the first sprint using this kanban template. Historical data begins next period.

---

## 📝 Board Notes

### Decisions made this period

- **Feb 13:** Decided to build comprehensive documentation system rather than lightweight linter approach — see [ADR-001](../../../agentic/adr/ADR-001-agent-optimized-documentation-system.md)
- **Feb 13:** Chose `classDef` palette over `%%{init}` theming for Mermaid — see [ADR-002](../../../agentic/adr/ADR-002-mermaid-diagram-standards.md)
- **Feb 13:** Adopted "Everything is Code" for project management — see [ADR-003](../../../agentic/adr/ADR-003-everything-is-code.md)
- **Feb 13:** Removed all 7 ported ADRs (perplexity spaces, monorepo structure, Walmart procurement, USB backup, etc.) — not relevant to this project
- **Feb 13:** Upgraded PR template to 2026 standards: added security review, breaking changes, deployment strategy, observability plan sections
- **Feb 13:** Upgraded issue template: added customer impact quantification, workaround section, SLA tracking
- **Feb 13:** Upgraded kanban template: added aging indicators, flow efficiency, lead time metrics
- **Feb 13:** Rewrote example files from fictional payment scenario to real project data (this documentation system)
- **Feb 13:** Fixed all identified local `--review` failure modes (including ANSI output consistency)
- **Feb 13:** Added `notebooks/` and `src/` as first-class root directories for future class work
- **Feb 13:** Added `agentic/idempotent_design_patterns.md` and wired it into agent read-in guidance
- **Feb 13:** Verified local `--review` completes end-to-end; external OpenRouter credits can limit LLM findings content but pipeline remains resilient
- **Feb 13:** Added NVIDIA-first provider routing with OpenRouter fallback-by-presence policy
- **Feb 13:** Added local fail-fast timeout boundary so degraded LLM runs terminate predictably
- **Feb 13:** Added local pricing/cost visibility from `final_summary.md` to terminal output
- **Feb 13:** Fixed markdownlint flakiness by excluding `.crewai/workspace/**` artifacts from `lint:md`
- **Feb 13:** Verified local cost tracker parity: pricing table now shows per-call entries and totals
- **Feb 13:** Verified full `./scripts/ci-local.sh --review` pipeline passes with fallback behavior
- **Feb 13:** Added mandatory task-completion sync gate in `AGENTS.md` and `agentic/instructions.md` for PR/issue/kanban/ADR updates
- **Feb 13:** Added ADR-004 formalizing source-of-truth synchronization as required completion behavior
- **Feb 13:** Expanded process to require live PR/issue/kanban updates before implementation, at milestones, and before/after verification for human monitoring
- **Feb 13:** Added policy to run `./scripts/ci-local.sh` before commit/push when possible, with explicit skip-reason documentation for hosted/non-local environments
- **Feb 13:** Hardened NVIDIA timeout behavior with explicit error surfacing and deterministic primary timeout window
- **Feb 14:** Updated local quick-review shortcut to run 3 reviewer passes with aggregated/deduplicated output and reviewer-pass summaries in final report
- **Feb 14:** Reworked local pricing/cost panel rendering to fixed-width aligned columns for classroom readability
- **Feb 14:** Modernized monorepo layout by moving the frontend from `website/` to `apps/web/` and aligning local CI/deploy paths
- **Feb 14:** Added new polyglot starter workspaces (`apps`, `services`, `packages`, `data/sql`) and updated repo maps to support Python, SQL, TypeScript, API, and service backends
- **Feb 14:** Accepted workspace architecture direction in ADR-005 (polyglot monorepo layout)
- **Feb 14:** Adopted federated ADR governance (global `agentic/adr/` + subsystem ADR logs) in ADR-006
- **Feb 14:** Added `.crewai/adr/` local decision log with initial ADRs for provider/failover and quick-review synthesis behavior
- **Feb 14:** Added ADR-007 as baseline global monorepo decision map for onboarding and architecture orientation
- **Feb 14:** Re-aligned CrewAI fallback chain to NVIDIA primary and OpenRouter fallback only (OpenCode agent model remains separate)
- **Feb 14:** Regrouped `.github/workflows/ci.yml` into explicit stage gates (`validate`, `test-build`, `deploy`) and moved CrewAI review to run last
- **Feb 14:** Re-ran local CI (`./scripts/ci-local.sh --review`) after workflow regrouping; local behavior remained consistent (deploy skipped locally, review path preserved)
- **Feb 14:** Fixed CI README Architecture Overview Mermaid parse error and normalized phase labels to Validate/Test/Build/Deploy/CrewAI Review naming
- **Feb 14:** Added CI/deploy concurrency guards and made stage-gate dependency waiting explicit in architecture diagrams
- **Feb 14:** Re-ran `./scripts/ci-local.sh --review` after concurrency/provider hardening; all CI phases passed with expected local deploy skips, while quick-review still showed intermittent NVIDIA response issues and remained tracked in Issue #2
- **Feb 14:** Cleaned local commitlint execution path to remove `ELIFECYCLE` lifecycle failure noise from Phase 1 output while keeping commit-style warnings
- **Feb 14:** Re-ran full local CI after commitlint UX polish; all phase gates passed and NVIDIA timeout still failed over cleanly to OpenRouter
- **Feb 14:** Switched local provider baseline to OpenRouter default and moved NVIDIA to explicit `--nvidia-nim` opt-in to remove default-path latency from repeated NVIDIA failures
- **Feb 14:** Added synthesis path for full-review/specialist outputs so missing per-crew JSON files no longer degrade final summary completeness
- **Feb 14:** Added `scope.json` review-scope contract and merge-base metadata to local and CI review preparation
- **Feb 14:** Added `validation_report.json` artifact-validation ledger and introduced data-engineering specialist routing/coverage
- **Feb 14:** Hardened CrewAI result parsing to avoid `.json` accessor exceptions and safely persist parsed task/raw payloads
- **Feb 14:** Tightened full/specialist task prompts to require JSON-only final responses for stronger structured-output consistency
- **Feb 14:** Added context-pack resilience path and targeted specialist repair logic for local quick/full reliability
- **Feb 14:** Aligned GitHub Actions review prep with local context artifacts (`context_pack.*`, `commit_messages.txt`, `scope.json`) for crew parity
- **Feb 14:** Added explicit Won't Do column and rationale logging for board transparency
- **Feb 14:** Enabled specialist selective repo exploration via `FileContentTool`/`RelatedFilesTool`/`CommitInfoTool`/`CommitDiffTool` and switched local specialist path to crew-first execution with parsed-result recovery
- **Feb 14:** Added specialist domain relevance gates so no-relevant crews emit explicit not-applicable outputs instead of simulated findings
- **Feb 14:** Re-ran `./scripts/ci-local.sh --full-review --step review` and confirmed all 13 workflows passed with deterministic `no-relevant-changes` outputs for unrelated specialist domains.
- **Feb 14:** Reworked fallback `final_summary.md` into executive-first structure with workflow-level recommendations and rebuilt cost reporting (`Cost and efficiency` with crew totals first and collapsible per-call detail), plus fixed terminal pricing panel section targeting.
- **Feb 14:** Polished quick-review signal quality by suppressing synthetic fallback findings for non-JSON reviewer responses, reducing speculative priority-action noise, and clarifying validation source labels in final summaries.
- **Feb 14:** Final quality sweep added changed-file scope filtering for specialist recovered findings and prevented local/non-PR runs from polluting persistent memory trend history; revalidated with full local review pass.
- **Feb 14:** Added top-level `NOTICE` and updated agent/contributor guidance to enforce Apache-2.0 redistribution attribution requirements.
- **Feb 14:** Refined final summary executive section to focus on decision-critical actions and pruned repeated quick-review low-signal placeholders from reviewer breakdowns.
- **Feb 14:** Replaced local full-review single-shot shortcut with 4-call multipass (quality/architecture/security/synthesis) and removed forced `---` separators after `</details>` in final-summary formatting rules.
- **Feb 14:** Removed duplicate specialist status lines from the top workflow guide in fallback summaries; specialist status remains in dedicated specialist sections only.
- **Feb 14:** Added `.ci-local.lock` single-run guard and forced workspace cleanup at local CI start; upgraded specialist local prompts to stronger domain-only focus and extended cost reporting with agent-level attribution.
- **Feb 14:** Added `--complete-full-review` local mode and `crewai:complete-full-review` routing semantics so full + all specialists can run in complete-repository perspective mode.
- **Feb 14:** Fixed CrewAI reusable workflow context-pack generator to handle list-based `commits.json` safely and prevent PR-review job crashes.
- **Feb 15:** Added persistent memory management tooling (`scripts/memory.sh` + `.crewai/tools/memory_cli.py`) and prompt memory propagation for local quick/full/specialist review paths.
- **Feb 15:** Added explicit memory policy for placeholder credential examples in `*.env.example` and aligned root `pyproject.toml` license metadata to Apache-2.0.

### Carryover from last period

- N/A — first sprint for this project

### Rollover to Sprint W08

- Active tracking now continues in `docs/project/kanban/sprint-2026-w08-crewai-review-hardening-and-memory.md`.
- Carried over from this board: both backlog items plus the single in-progress item.
- Completed on Feb 15 moved to W08 Done to keep week boundaries clean.

_Week-one closure timeline with rollover checkpoint:_

```mermaid
timeline
    accTitle: Sprint W07 closure timeline
    accDescr: Timeline of Sprint W07 completion and rollover actions into Sprint W08.

    title Sprint W07 closeout
    Feb 10 : Sprint W07 start
    Feb 13 : Documentation + CI reliability foundation completed
    Feb 14 : Review hardening + complete-full-review semantics landed
    Feb 15 : Rollover executed to Sprint W08 board
```

### Week-one closeout notes

- Strong first week: documentation system, CI hardening, and CrewAI reliability foundations are in place.
- Biggest leverage point going forward: keep specialist quality high while tightening routing and token efficiency.
- Operational baseline is now good enough to iterate on deeper memory + router quality improvements in W08.

### Upcoming dependencies

- **Feb 14:** GitHub rendering verification needed before merge — architecture, requirement, C4, radar, treemap diagrams are most fragile
- **Post-commit:** Push branch and validate Mermaid rendering in GitHub UI
- **Feb 14:** Validate NVIDIA opt-in path quality/reliability separately from default OpenRouter baseline for [Issue #2](../issues/issue-00000002-provider-priority-fail-fast-review-cost-visibility.md)
- **Before merge:** Commit and push latest local reliability/output updates so humans can verify GitHub rendering and final linked records
- ~~**Post-merge:** AGENTS.md needs an entry pointing agents to the style guides~~ — Done: `AGENTS.md` created at repo root

---

## 🔗 References

- [Issue-#1: Create agent-optimized documentation system](../issues/issue-00000001-agentic-documentation-system.md)
- [Issue-#2: Provider priority + fail-fast + local pricing visibility](../issues/issue-00000002-provider-priority-fail-fast-review-cost-visibility.md)
- [Issue-#3: Local review context pack and resilience](../issues/issue-00000003-local-review-context-pack-and-resilience.md)
- [PR-#1: Agentic documentation system + repo cleanup](../pr/pr-00000001-agentic-docs-and-monorepo-modernization.md)
- [ADR-001: Documentation system decision](../../../agentic/adr/ADR-001-agent-optimized-documentation-system.md)
- [ADR-002: Mermaid standards decision](../../../agentic/adr/ADR-002-mermaid-diagram-standards.md)
- [ADR-003: Everything is Code decision](../../../agentic/adr/ADR-003-everything-is-code.md)
- [ADR-004: Source-of-truth sync loop decision](../../../agentic/adr/ADR-004-task-completion-source-of-truth-sync.md)
- [ADR-005: Polyglot monorepo workspace layout](../../../agentic/adr/ADR-005-polyglot-monorepo-workspace-layout.md)
- [ADR-006: Federated ADR governance](../../../agentic/adr/ADR-006-federated-adr-governance.md)
- [ADR-007: Monorepo foundation and decision baseline](../../../agentic/adr/ADR-007-monorepo-foundation-and-decision-baseline.md)
- [ADR-008: Persistent review memory governance](../../../agentic/adr/ADR-008-persistent-review-memory-governance.md)
- [CrewAI ADR index](../../../.crewai/adr/README.md)
- [CrewAI ADR-004: Review scope contract and tiered diff strategy](../../../.crewai/adr/ADR-004-review-scope-contract-and-tiering.md)
- [CrewAI ADR-005: Output validation and data engineering specialist](../../../.crewai/adr/ADR-005-output-validation-and-data-engineering-specialist.md)
- [CrewAI ADR-006: Persistent review memory policy and memory CLI](../../../.crewai/adr/ADR-006-persistent-review-memory-and-cli.md)
- [Idempotent script design patterns](../../../agentic/idempotent_design_patterns.md)

---

_Next update: Closed; tracking moved to Sprint W08 · Board owner: Human_
