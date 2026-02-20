# ADR-006: Persistent Review Memory Policy and Memory CLI

| Field               | Value                                               |
| ------------------- | --------------------------------------------------- |
| **Status**          | Accepted                                            |
| **Date**            | 2026-02-15                                          |
| **Decision makers** | Repo maintainers                                    |
| **Consulted**       | AI agents (review reliability and signal quality)   |
| **Informed**        | Contributors using local/CI CrewAI review workflows |

---

## 📋 Context

Specialist reviews repeatedly produced low-value findings about placeholder keys in `*.env.example`, even when placeholders were clearly fake template values.

The subsystem already had a local JSON memory mechanism plus optional mem0 cloud support, but there was no simple operator-facing CLI to manage memories and suppressions during normal project work.

---

## 🎯 Decision

1. Treat persistent review memory as a first-class signal in all local structured review prompts.
2. Add an operator-friendly command at `scripts/memory.sh` for adding/listing memories and suppression rules.
3. Keep local JSON as default backend and support optional mem0 cloud/self-hosted paths behind explicit configuration.
4. Add a persisted suppression for placeholder secret findings in `*.env.example` files.
5. Add a persisted learned memory that placeholder examples are acceptable when clearly fake.
6. Persist a text SQL seed snapshot (`.crewai/memory/sql/memory_seed.sql`) so runtime DBs can be materialized on demand without committing binary artifacts.

---

## ⚡ Consequences

### Positive

- Less repeated low-signal findings across runs.
- Faster operator feedback loop for updating review preferences.
- Memory controls become scriptable for future PR-comment ingestion workflows.

### Negative

- Additional policy surface area to maintain (memory rules can become stale).
- Suppression misuse can hide true risk if rules are too broad.
- Self-hosted backend configuration drift can silently fall back to local mode if not validated.

---

## ✅ Guardrails

- Suppress only low-signal patterns explicitly accepted by maintainers.
- Never suppress actual credential leakage findings.
- Keep memory files in version control for auditability.
- Keep SQL seed export text-only in repo; runtime SQLite artifacts remain local-only.

---

## 📋 Evidence in code

- `.crewai/tools/memory_manager.py` (dedupe, list/deactivate APIs)
- `.crewai/tools/memory_cli.py` (memory management CLI)
- `scripts/memory.sh` (human/agent wrapper command)
- `.crewai/main.py` (memory context prompt injection)
- `.crewai/memory/memory.json` (learned memory entry)
- `.crewai/memory/suppressions.json` (placeholder suppression entry)
- `.crewai/memory/sql/memory_seed.sql` (text SQL seed export)
- `.crewai/tests/test_memory_manager.py`, `.crewai/tests/test_memory_cli.py` (backend/CLI coverage)

---

## 🔗 References

- [Subsystem ADR index](./README.md)
- [Issue-00000003](../../docs/project/issues/issue-00000003-local-review-context-pack-and-resilience.md)

---

_Last updated: 2026-02-15 16:12 EST_
