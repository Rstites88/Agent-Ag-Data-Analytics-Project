# ADR-007: Monorepo Foundation and Decision Baseline

| Field               | Value                                            |
| ------------------- | ------------------------------------------------ |
| **Status**          | Accepted                                         |
| **Date**            | 2026-02-14                                       |
| **Decision makers** | Clayton Young                                    |
| **Consulted**       | AI agents (repo architecture consolidation pass) |
| **Informed**        | All contributors and agents working in this repo |

---

## 📋 Context

The repository has accumulated multiple accepted ADRs that define documentation governance, project-management source-of-truth behavior, monorepo structure, and federated decision logging.

New contributors and agents need one global baseline ADR that explains the current architecture direction and how the existing ADR set composes.

---

## 🎯 Decision

Adopt this baseline for the repository:

1. This is a polyglot monorepo with explicit workspace boundaries (`apps/`, `services/`, `packages/`, `data/sql/`, `src/`).
2. Project-management artifacts are repository-native files under `docs/project/`.
3. Documentation and diagram output must follow agentic style guides and templates.
4. ADR governance is federated:
   - global and cross-subsystem decisions in `agentic/adr/`
   - subsystem-local implementation decisions in subsystem `adr/` logs (for example `.crewai/adr/`)
   - subsystem decisions with repo-wide impact must be mirrored in `agentic/adr/`
5. Source-of-truth records (PR/issue/kanban/ADR) are updated continuously during execution, not only at the end.

---

## ⚡ Consequences

### Positive

- One canonical orientation point for repo architecture and governance.
- Faster onboarding for humans and agents.
- Lower ambiguity between global policy and local subsystem decisions.

### Negative

- Baseline ADR must be kept current when core repo direction changes.

---

## 📚 Decision map

This ADR is a baseline index over accepted decisions:

- [ADR-001: Agent-Optimized Documentation System](./ADR-001-agent-optimized-documentation-system.md)
- [ADR-002: Mermaid Diagram Standards](./ADR-002-mermaid-diagram-standards.md)
- [ADR-003: Everything is Code](./ADR-003-everything-is-code.md)
- [ADR-004: Mandatory Source-of-Truth Sync](./ADR-004-task-completion-source-of-truth-sync.md)
- [ADR-005: Polyglot Monorepo Workspace Layout](./ADR-005-polyglot-monorepo-workspace-layout.md)
- [ADR-006: Federated ADR Governance](./ADR-006-federated-adr-governance.md)

Subsystem decision logs currently in use:

- [CrewAI ADR index](../../.crewai/adr/README.md)

---

## 🔗 References

- [AGENTS.md](../../AGENTS.md)
- [File organization](../file_organization.md)
- [PR-00000001 record](../../docs/project/pr/pr-00000001-agentic-docs-and-monorepo-modernization.md)

---

_Last updated: 2026-02-14_
