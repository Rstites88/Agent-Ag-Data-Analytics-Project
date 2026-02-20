# ADR-005: Output Validation Ledger and Data Engineering Specialist Crew

| Field               | Value                                        |
| ------------------- | -------------------------------------------- |
| **Status**          | Accepted                                     |
| **Date**            | 2026-02-14                                   |
| **Decision makers** | Repo maintainers                             |
| **Consulted**       | AI agents (reliability and architecture)     |
| **Informed**        | Contributors using CrewAI specialist reviews |

---

## 📋 Context

Specialist/full-review runs can return useful analysis text while failing to persist expected workspace artifacts via tool calls. This creates hidden quality risk even when final summary generation succeeds.

The review stack also lacked a dedicated data engineering specialist for SQL/schema/migration/ETL/ELT risk, creating inconsistent domain coverage.

---

## 🎯 Decision

1. Add explicit artifact validation tracking in workspace as `validation_report.json`.
2. Validate specialist outputs using registry schema checks before considering artifacts valid.
3. Validate full-review artifact structure and record repair/missing-output provenance.
4. Persist parsed crew-result payloads when crews do not write expected files, and track source provenance in validation metadata.
5. Add a first-class `data_engineering` specialist crew and route label: `crewai:data-engineering`.
6. Make specialist execution tool-driven and selective: run specialist crews with targeted repo-inspection tools (`FileContentTool`, `RelatedFilesTool`, `CommitInfoTool`, `CommitDiffTool`) and use parsed-result recovery before structured local fallback.
7. Enforce non-simulated specialist outputs: if no domain-relevant changed files are detected, write explicit not-applicable artifacts with zero findings.

Data engineering coverage includes:

- SQL/query correctness and performance
- schema and migration safety
- ETL/ELT reliability and idempotency
- data quality and contract compatibility
- lineage and downstream blast-radius concerns

---

## ⚡ Consequences

### Positive

- Each expected artifact now has auditable validity/provenance metadata.
- Final summaries can expose output health directly.
- Broader domain coverage with dedicated data engineering review.
- Router and full-review expansion remain registry-driven and extensible.

### Negative

- Additional orchestration logic in `main.py`.
- More specialist runtime when `crewai:full-review` runs.

---

## 📋 Evidence in code

- `.crewai/main.py` (validation recording, specialist/full output validation, provenance)
- `.crewai/utils/specialist_output.py` (new `data_engineering` registry entry and autodetect rules)
- `.crewai/crews/data_engineering_review_crew.py` (new specialist crew)
- `.crewai/config/tasks/data_engineering_review_tasks.yaml` (new task contract)
- `.crewai/config/tasks/router_tasks.yaml` (new specialist label/routing)
- `.crewai/config/tasks/final_summary_tasks.yaml` (includes data engineering + validation report inputs)
- `.crewai/crews/*_review_crew.py` (specialist tools extended for selective repo traversal)
- `.crewai/config/tasks/*_review_tasks.yaml` (selective investigation steps + changed-files index/scope-aware guidance)
- `.crewai/main.py` (specialist relevance gate + no-relevant deterministic output path)
- `.crewai/tests/test_specialist_output.py` and `.crewai/tests/test_crew_integrity.py` (registry/coverage tests)
- `.crewai/tests/test_specialist_quality.py` (summary and relevance quality tests)

---

## 🔗 References

- [Specialist registry](../utils/specialist_output.py)
- [Main orchestrator](../main.py)

---

_Last updated: 2026-02-14 17:27 EST_
