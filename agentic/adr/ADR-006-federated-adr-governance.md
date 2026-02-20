# ADR-006: Federated ADR Governance for Monorepo Subsystems

| Field               | Value                                            |
| ------------------- | ------------------------------------------------ |
| **Status**          | Accepted                                         |
| **Date**            | 2026-02-14                                       |
| **Decision makers** | Clayton Young                                    |
| **Consulted**       | AI agents (architecture/docs update pass)        |
| **Informed**        | All contributors and agents working in this repo |

---

## 📋 Context

This monorepo now contains multiple distinct workspaces (`agentic/`, `.crewai/`, `apps/`, `services/`, `packages/`, `data/sql/`). A single ADR log for all decisions causes noise and weak ownership when decisions are subsystem-specific.

Public ADR guidance supports both centralized logs and categorized or subdirectory logs in larger projects.[^backstage-adr][^madr-categories]

---

## 🎯 Decision

Adopt a federated ADR model:

- `agentic/adr/` is the **global ADR log** for repo-wide or cross-subsystem decisions.
- `<subsystem>/adr/` is the **local ADR log** for implementation decisions scoped to that subsystem (for example `.crewai/adr/`).
- If a subsystem decision changes repo-wide behavior, governance, or contracts, add a mirrored global ADR in `agentic/adr/`.
- ADRs are never deleted; they can be superseded by newer ADRs.

---

## ⚡ Consequences

### Positive

- Decisions stay close to the code and operators of each subsystem.
- Global ADR log remains high-signal for cross-cutting policy.
- Agents can infer impact scope faster from ADR location.

### Negative

- Contributors must classify decision scope correctly.
- Some decisions require dual updates (local + global mirror).

---

## 📋 Implementation impact

- Added subsystem ADR workflow language to `AGENTS.md` and `agentic/instructions.md`.
- Added CrewAI local ADR directory `.crewai/adr/` and initial ADR set.
- Updated directory maps to include subsystem ADR placement.

---

## 🔗 References

- [Backstage ADR guide](https://backstage.io/docs/architecture-decisions)
- [MADR: usage of categories in large projects](https://adr.github.io/madr/)
- [AGENTS.md](../../AGENTS.md)
- [.crewai ADR index](../../.crewai/adr/README.md)

---

[^backstage-adr]: Backstage ADR documentation keeps substantial project architecture decisions in a dedicated ADR directory and formalizes superseding behavior: <https://backstage.io/docs/architecture-decisions>

[^madr-categories]: MADR guidance documents category/subdirectory organization for larger projects and product developments: <https://adr.github.io/madr/>

---

_Last updated: 2026-02-14_
