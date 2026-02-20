# Agent Instructions

> **🤖 YOU are the AI agent.** These instructions are for you — the AI assistant working on this codebase. When this documentation says "you" or "agent," that means you.
>
> Your job: autonomously write code, create PRs, and iterate on feedback — while humans control via design review, code review, and merge decisions.
>
> **Canonical entrypoint:** Start from [../AGENTS.md](../AGENTS.md). It defines repo-wide rules and routes to this file.

---

## 📖 Startup checklist

Read these files in order before starting any task:

1. **[agentic_coding.md](agentic_coding.md)** — What you CAN, MUST escalate, and NEVER do. Complete 14-step workflow.
2. **[autonomy_boundaries.md](autonomy_boundaries.md)** — Capability matrix and escalation procedures.
3. **[workflow_guide.md](workflow_guide.md)** — 14-step transparent process with human checkpoints.
4. → Ask the human to describe their task.
5. → You decide what else to read based on task complexity (see below).

---

## 📋 What to load by task type

### Simple fixes or small features

- ✅ [contribute_standards.md](contribute_standards.md) — code style, testing, commits
- ✅ [custom-instructions.md](custom-instructions.md) — project-specific rules

### Complex refactors or infrastructure changes

- ✅ Everything above, plus:
- ✅ [operational_readiness.md](operational_readiness.md) — system constraints and limits
- ✅ [context_budget_guide.md](context_budget_guide.md) — token management strategies

### Scripting and automation work

- ✅ [idempotent_design_patterns.md](idempotent_design_patterns.md) — required patterns for safe re-runnable scripts
- ✅ [operational_readiness.md](operational_readiness.md) — execution constraints and failure boundaries

### Documentation or diagram work

- ✅ [markdown_style_guide.md](markdown_style_guide.md) — formatting rules for ALL markdown
- ✅ [mermaid_style_guide.md](mermaid_style_guide.md) — standards for ALL diagrams
- ✅ [markdown_templates/](markdown_templates/) — check if a template exists for your document type
- ✅ [mermaid_diagrams/](mermaid_diagrams/) — open the specific diagram type file

### When something goes wrong

- ✅ [agent_error_recovery.md](agent_error_recovery.md) — 9 error categories with recovery steps
- ✅ [file_organization.md](file_organization.md) — where files live, source of truth
- ✅ [context_budget_guide.md](context_budget_guide.md) — if context window is running low

---

## ✍️ Documentation standards

> 📌 **Before creating ANY markdown document or Mermaid diagram, you MUST read the relevant style guide.** These are not optional — they define the formatting, structure, citation, accessibility, and visual standards for this project.

| Creating...                  | Read first                                                                                                                     |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Any `.md` document           | [markdown_style_guide.md](markdown_style_guide.md)                                                                             |
| Any Mermaid diagram          | [mermaid_style_guide.md](mermaid_style_guide.md), then the [specific type file](mermaid_diagrams/)                             |
| A PR, issue, or kanban board | [markdown_style_guide.md](markdown_style_guide.md) (Everything is Code section) + the relevant [template](markdown_templates/) |
| An ADR or decision record    | [decision_record.md template](markdown_templates/decision_record.md)                                                           |

Key rules enforced by the style guides:

- **Citations** — every external claim gets a footnote with full URL
- **Diagrams** — `accTitle` + `accDescr` on every diagram, `classDef` color classes (no inline `style`), emoji on key nodes
- **Structure** — one H1, emoji on H2 only, no H5+, horizontal rules after `</details>` blocks
- **Everything is Code** — PRs, issues, boards are markdown files in `docs/`, not platform-locked data

---

## 🎯 Your capabilities (summary)

✅ **What you CAN do autonomously:**

- Write code following project standards
- Create branches (`feat/`, `fix/`, `docs/`, `chore/`)
- Make commits with Scoped Conventional Commits format — `type(scope): description`
- Create PRs with comprehensive documentation
- Create and update documentation following style guides
- Respond to feedback and iterate
- Run `./scripts/ci-local.sh` before commit/push when local environment supports it
- If local CI is unavailable in the current environment, document the skip reason in PR/issue files

❌ **What you NEVER do:**

- Merge PRs (only humans merge)
- Deploy to production (only humans deploy)
- Approve your own PR
- Access secrets or hardcode credentials
- Force-push or rewrite history

⚠️ **When you MUST escalate (ask first):**

- Breaking API changes
- Security/authentication modifications
- Major architectural decisions
- Changes to deployment or CI/CD config
- Large refactorings affecting multiple modules

See [agentic_coding.md](agentic_coding.md) for the complete lists.

---

## 🔄 The 3 workflow checkpoints

| Checkpoint          | Step    | What happens                                               |
| ------------------- | ------- | ---------------------------------------------------------- |
| **Design review**   | Step 5  | You document approach → human reviews before you code      |
| **Code review**     | Step 9  | You implement → human reviews code quality                 |
| **Status approval** | Step 10 | Human explicitly confirms → you mark PR "Ready for Review" |

See [workflow_guide.md](workflow_guide.md) for the full 14-step process.

---

## 🗂️ File locations

| What                           | Where                                                               |
| ------------------------------ | ------------------------------------------------------------------- |
| Agent instructions & standards | `agentic/`                                                          |
| Style guides & templates       | `agentic/markdown_style_guide.md`, `agentic/mermaid_style_guide.md` |
| Document templates             | `agentic/markdown_templates/`                                       |
| Diagram type guides            | `agentic/mermaid_diagrams/`                                         |
| Architecture decisions         | `agentic/adr/` (global) + subsystem `adr/` directories              |
| Deployable apps                | `apps/`                                                             |
| Backend services/workers       | `services/`                                                         |
| Shared packages                | `packages/`                                                         |
| SQL schemas/migrations         | `data/sql/`                                                         |
| PR records                     | `docs/project/pr/`                                                  |
| Issue records                  | `docs/project/issues/`                                              |
| Kanban boards                  | `docs/project/kanban/`                                              |
| Idempotent script standards    | `agentic/idempotent_design_patterns.md`                             |
| Jupyter notebooks              | `notebooks/`                                                        |
| Language-focused source area   | `src/`                                                              |
| Agent entry point              | `AGENTS.md` at repo root → points to `agentic/instructions.md`      |

See [file_organization.md](file_organization.md) for the complete directory map.

---

## ✅ Required before task completion

Before you report a task as done, update source-of-truth records in-repo:

- Update the active PR file in `docs/project/pr/`
- Update impacted issue file(s) in `docs/project/issues/`
- Update the active kanban board in `docs/project/kanban/`
- Create/update ADRs in the right location when a durable decision was introduced:
  - `agentic/adr/` for repo-wide/cross-subsystem decisions
  - subsystem `adr/` directories for local implementation decisions (for example `.crewai/adr/`)
  - if a subsystem decision has cross-repo impact, add or update a mirror ADR in `agentic/adr/`

If no ADR is needed, state `No ADR required` in the PR record.

---

## 🔄 Live progress sync loop

These updates are required while work is in progress (not only at the end):

1. **Before implementation starts**: update active PR/issue/kanban with planned scope and `in progress` status.
2. **Before editing implementation files**: ensure PR/issue/kanban describe the exact change about to be made.
3. **After each milestone**: update PR/issue/kanban with progress, decisions, blockers, and scope changes.
4. **Before tests/verification**: update PR/issue/kanban with what will be validated, then run `./scripts/ci-local.sh` when local environment supports it.
5. **After tests/verification**: update PR/issue/kanban with outcomes and next actions.

Humans should be able to monitor work from markdown records in real time.

---

## 📚 All files in this framework

| File                                                           | Purpose                                                   |
| -------------------------------------------------------------- | --------------------------------------------------------- |
| [README.md](README.md)                                         | Directory overview with architecture diagram              |
| [instructions.md](instructions.md)                             | This file — agent entry point                             |
| [agentic_coding.md](agentic_coding.md)                         | CAN/MUST/NEVER + 14-step workflow                         |
| [autonomy_boundaries.md](autonomy_boundaries.md)               | Capability matrix and escalation rules                    |
| [workflow_guide.md](workflow_guide.md)                         | 14-step workflow with checkpoints                         |
| [contribute_standards.md](contribute_standards.md)             | Code style, commits, PR standards                         |
| [custom-instructions.md](custom-instructions.md)               | Project-specific rules (template — customize per project) |
| [operational_readiness.md](operational_readiness.md)           | System constraints and limits                             |
| [context_budget_guide.md](context_budget_guide.md)             | Token management strategies                               |
| [agent_error_recovery.md](agent_error_recovery.md)             | Error recovery procedures                                 |
| [file_organization.md](file_organization.md)                   | File locations and source of truth                        |
| [idempotent_design_patterns.md](idempotent_design_patterns.md) | Idempotent standards for all automation scripts           |
| [markdown_style_guide.md](markdown_style_guide.md)             | Markdown formatting standards                             |
| [mermaid_style_guide.md](mermaid_style_guide.md)               | Mermaid diagram standards                                 |

---

**Last updated:** 2026-02-13
**Status:** Production-ready
