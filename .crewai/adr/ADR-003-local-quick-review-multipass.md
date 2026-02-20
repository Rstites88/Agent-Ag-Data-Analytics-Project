# ADR-003: Local Quick-Review Multi-Pass Synthesis and Output Schema

| Field               | Value                                       |
| ------------------- | ------------------------------------------- |
| **Status**          | Accepted                                    |
| **Date**            | 2026-02-14                                  |
| **Decision makers** | Repo maintainers                            |
| **Consulted**       | AI agents (review-output quality updates)   |
| **Informed**        | Contributors reviewing local summary output |

---

## 📋 Context

Single-pass quick review produced low-depth findings and weak final summary context for local runs. Reviewers needed richer output showing what each pass concluded and how final findings were aggregated.

---

## 🎯 Decision

For local quick review in `.crewai/main.py`:

- Execute multiple reviewer passes with distinct focus areas.
- Aggregate and deduplicate findings into a single `quick_review.json`.
- Record pass-level metadata (`reviewer_summaries`, `calls_executed`, `provider_used`).
- Include reviewer-pass summaries and reviewer call count in `final_summary.md`.

---

## ⚡ Consequences

### Positive

- Better review depth and transparency in local output.
- Clear audit trail for how conclusions were synthesized.

### Negative

- Slightly higher token and runtime cost during local review.

---

## 📋 Evidence in code

- `.crewai/main.py` (`run_quick_review`, `create_fallback_summary`)
- `scripts/ci-local.sh` (local summary rendering and pricing/cost panel output)

---

## 🔗 References

- [Quick review orchestration](../main.py)
- [Local runner summary panel](../../scripts/ci-local.sh)

---

_Last updated: 2026-02-14_
