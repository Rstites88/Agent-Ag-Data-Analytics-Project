# ADR-004: Review Scope Contract and Tiered Diff Strategy

| Field               | Value                                     |
| ------------------- | ----------------------------------------- |
| **Status**          | Accepted                                  |
| **Date**            | 2026-02-14                                |
| **Decision makers** | Repo maintainers                          |
| **Consulted**       | AI agents (scope and routing analysis)    |
| **Informed**        | Contributors running local and CI reviews |

---

## 📋 Context

CrewAI review quality depends on review scope quality. The prior local flow generated a single diff without a durable scope contract, while CI and local selection behavior diverged across branch, merge-base, and working-tree cases.

---

## 🎯 Decision

Adopt a tiered scope strategy with a persisted `scope.json` contract in workspace for both local and CI runs.

Scope tiers:

1. Quick review tier: prioritize near-HEAD/most-recent changes and CI/log context.
2. Branch tier (full review): use merge-base anchored branch evolution context.
3. Specialist tier: changed-code emphasis with targeted broader posture checks where domain requires it.

Contract fields written to `scope.json`:

- `contract_version`
- `tier`
- `diff_strategy`
- `base_ref`
- `head_ref`
- `head_sha`
- `merge_base`

Operational rules:

- Local runner computes merge-base when reviewing committed branch history and records selected strategy.
- CI reusable workflow writes `scope.json` using base/head refs and merge-base context.
- Tasks that benefit from scope awareness read `scope.json` when available (quick/full/legal/data engineering).

---

## ⚡ Consequences

### Positive

- Clear and inspectable review scope per run.
- Better local/CI parity for branch-evolution analysis.
- Reduced ambiguity for full and specialist crews.

### Negative

- Additional workspace artifact to maintain.
- Slight increase in prompt/tool input size for crews that read scope metadata.

---

## 📋 Evidence in code

- `scripts/ci-local.sh` (merge-base-aware diff selection and `scope.json` creation)
- `.github/workflows/crewai-review-reusable.yml` (`scope.json` creation during PR data preparation)
- `.crewai/config/tasks/quick_review_tasks.yaml` (scope-aware quick review input)
- `.crewai/config/tasks/full_review_tasks.yaml` (branch-context full review inputs)
- `.crewai/config/tasks/legal_review_tasks.yaml` (scope-aware legal analysis inputs)

---

## 🔗 References

- [Local CI review runner](../../scripts/ci-local.sh)
- [CrewAI review reusable workflow](../../.github/workflows/crewai-review-reusable.yml)

---

_Last updated: 2026-02-14_
