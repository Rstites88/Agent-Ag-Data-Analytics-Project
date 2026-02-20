# ADR-008: Persistent Review Memory Governance

| Field               | Value                                      |
| ------------------- | ------------------------------------------ |
| **Status**          | Accepted                                   |
| **Date**            | 2026-02-15                                 |
| **Decision makers** | Repo maintainers                           |
| **Consulted**       | AI agents and CrewAI subsystem maintainers |
| **Informed**        | Contributors and reviewers                 |

---

## 📋 Context

The repository uses AI-assisted review workflows where repeated low-signal findings can waste time and tokens. The CrewAI subsystem introduced persistent memory controls and a local memory-management CLI.

Because this directly affects cross-repo review behavior and contributor workflow, the governance model must be documented at global ADR scope.

---

## 🎯 Decision

1. Adopt version-controlled persistent review memory as part of repository governance.
2. Keep local JSON memory as the default persistence layer.
3. Permit optional mem0 cloud or self-hosted augmentation when explicitly configured.
4. Require memory updates to follow source-of-truth workflow updates (PR/issue/kanban + ADR where durable).
5. Treat `*.env.example` placeholder values as acceptable examples unless real credentials are present.
6. Require text-first persistence artifacts (`.json` and `.sql`) in-repo, and keep runtime database binaries out of git.

---

## ⚡ Consequences

### Positive

- Review guidance is durable, auditable, and shared across runs.
- Maintainers can reduce repeated false-positive findings with explicit policy.
- Human and agent workflows can use a simple memory command interface.

### Negative

- Memory policy must be periodically reviewed to avoid stale suppressions.
- Over-broad suppressions can hide real findings if governance is weak.
- Multi-backend support adds operational configuration complexity for maintainers.

---

## 🔗 References

- [CrewAI ADR-006](../../.crewai/adr/ADR-006-persistent-review-memory-and-cli.md)
- [Global ADR governance](./ADR-006-federated-adr-governance.md)

---

_Last updated: 2026-02-15 16:12 EST_
