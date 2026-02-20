# ADR-001: CrewAI Local ADR Log Scope and Ownership

| Field               | Value                                |
| ------------------- | ------------------------------------ |
| **Status**          | Accepted                             |
| **Date**            | 2026-02-14                           |
| **Decision makers** | Repo maintainers                     |
| **Consulted**       | AI agents (CrewAI subsystem updates) |
| **Informed**        | Contributors working in `.crewai/`   |

---

## 📋 Context

CrewAI has subsystem-specific architecture choices (crew orchestration, model routing, review schema contracts, cost reporting) that evolve independently from the rest of the monorepo.

Keeping those choices only in the global ADR log reduces discoverability for contributors working inside `.crewai/`.

---

## 🎯 Decision

Create and maintain a local ADR log in `.crewai/adr/`.

Scope rules:

- Write CrewAI-only decisions in `.crewai/adr/`.
- Mirror to `agentic/adr/` when a decision affects repo-wide policy, shared workflow, or other subsystems.
- Never delete old ADRs; supersede when needed.

---

## ⚡ Consequences

### Positive

- Faster onboarding for CrewAI maintainers.
- Clear ownership boundaries for subsystem decisions.

### Negative

- Requires explicit judgment about local vs global impact.

---

## 🔗 References

- [Global ADR governance](../../agentic/adr/ADR-006-federated-adr-governance.md)
- [CrewAI subsystem guide](../README.md)

---

_Last updated: 2026-02-14_
