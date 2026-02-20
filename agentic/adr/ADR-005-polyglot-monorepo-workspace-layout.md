# ADR-005: Adopt Polyglot Monorepo Workspace Layout

| Field               | Value                                            |
| ------------------- | ------------------------------------------------ |
| **Status**          | Accepted                                         |
| **Date**            | 2026-02-14                                       |
| **Decision makers** | Clayton Young                                    |
| **Consulted**       | AI agents (repo modernization pass)              |
| **Informed**        | All contributors and agents working in this repo |

---

## 📋 Context

The template repo started with a root-level `website/` directory and a Python-focused `src/` workspace. That shape works for a single stack, but it is weaker for a starter template that must support mixed stacks (TypeScript frontend, API backends, workers, Python modules, and SQL assets) from day one.

The project goal is a generic agentic starter where contributors can add almost any runtime without restructuring the repository later.

---

## 🔍 Options considered

### Option A: Keep root-level `website/` and ad-hoc additions

**Pros:**

- Lowest immediate change cost

**Cons:**

- Inconsistent top-level conventions over time
- Harder to scale to multiple deployable apps

### Option B: Move frontend to `src/website/`

**Pros:**

- Single top-level source root

**Cons:**

- Conflicts with current `src/` usage as language-focused workspace
- Blurs app/workspace boundaries in a polyglot monorepo

### Option C: Adopt explicit monorepo workspaces (`apps/`, `services/`, `packages/`, `data/sql/`)

**Pros:**

- Clear separation between deployable apps, backend services, shared packages, and data assets
- Scales cleanly for Python + TypeScript + SQL + API/service backends
- Aligns with modern monorepo starter conventions

**Cons:**

- Requires path migration and docs updates

---

## 🎯 Decision

**We chose Option C.**

Adopt explicit monorepo workspace roots:

- `apps/` for deployable products (`apps/web`, `apps/api`, ...)
- `services/` for long-running backend services and workers
- `packages/` for shared modules/libraries
- `data/sql/` for SQL schemas, migrations, and seed assets
- keep `src/` as language-focused workspace (Python-first), not as the primary app root

As part of this decision, move the frontend from `website/` to `apps/web/` and update local CI/deploy paths.

---

## ⚡ Consequences

### Positive

- Better starter ergonomics for polyglot teams
- Reduced future repo churn when adding new runtimes
- Clearer subsystem ownership and navigation for agents/humans

### Negative

- Short-term migration overhead for existing paths and docs

### Risks

| Risk                                    | Likelihood | Impact | Mitigation                                         |
| --------------------------------------- | ---------- | ------ | -------------------------------------------------- |
| Missed path references during migration | Medium     | Medium | Validate with local CI steps and path grep checks  |
| Confusion between `apps/` and `src/`    | Medium     | Low    | Keep explicit workspace READMEs and AGENTS mapping |

---

## 📋 Implementation impact

- Moved `website/` to `apps/web/`
- Updated local script paths in `scripts/ci-local.sh`
- Updated workspace patterns in `pnpm-workspace.yaml` and lockfile importers
- Added workspace READMEs: `apps/`, `services/`, `packages/`, `data/sql/`
- Updated repo maps in `AGENTS.md`, `agentic/file_organization.md`, `agentic/instructions.md`, and `src/README.md`

---

## 🔗 References

- [AGENTS.md](../../AGENTS.md)
- [File organization](../file_organization.md)
- [PR-00000001](../../docs/project/pr/pr-00000001-agentic-docs-and-monorepo-modernization.md)

---

_Last updated: 2026-02-14_
