# File Organization & Source of Truth

> Where files live, which version to trust, and how the repository is structured.

**Read this when:** Confused about file locations or which version is authoritative.
**Don't read this:** Until you need file location clarity (saves context).

---

## 📂 Repository structure

```text
{project-root}/
├── AGENTS.md                        # Agent entry point (points to agentic/)
├── agentic/                         # Agent instructions & standards
│   ├── README.md                    # Directory overview with architecture diagram
│   ├── instructions.md              # Agent entry point — what to read and when
│   ├── agentic_coding.md            # CAN/MUST/NEVER rules + 14-step workflow
│   ├── autonomy_boundaries.md       # Capability matrix and escalation procedures
│   ├── workflow_guide.md            # 14-step transparent workflow
│   ├── contribute_standards.md      # Code style, commits, PR standards
│   ├── custom-instructions.md       # Project-specific rules (customize per project)
│   ├── operational_readiness.md     # System constraints and limits
│   ├── context_budget_guide.md      # Token management strategies
│   ├── agent_error_recovery.md      # Error recovery procedures (9 categories)
│   ├── idempotent_design_patterns.md # Script idempotency standards and examples
│   ├── file_organization.md         # This file
│   ├── markdown_style_guide.md      # Markdown formatting standards
│   ├── mermaid_style_guide.md       # Mermaid diagram standards
│   ├── markdown_templates/          # 9 document templates
│   │   ├── presentation.md
│   │   ├── research_paper.md
│   │   ├── project_documentation.md
│   │   ├── decision_record.md
│   │   ├── how_to_guide.md
│   │   ├── status_report.md
│   │   ├── pull_request.md
│   │   ├── issue.md
│   │   └── kanban.md
│   ├── mermaid_diagrams/            # 23 diagram type guides + complex examples
│   │   ├── flowchart.md
│   │   ├── sequence.md
│   │   ├── class.md
│   │   ├── state.md
│   │   ├── er.md
│   │   ├── gantt.md
│   │   ├── pie.md
│   │   ├── git_graph.md
│   │   ├── mindmap.md
│   │   ├── timeline.md
│   │   ├── user_journey.md
│   │   ├── quadrant.md
│   │   ├── requirement.md
│   │   ├── c4.md
│   │   ├── sankey.md
│   │   ├── xy_chart.md
│   │   ├── block.md
│   │   ├── kanban.md
│   │   ├── packet.md
│   │   ├── architecture.md
│   │   ├── radar.md
│   │   ├── treemap.md
│   │   ├── zenuml.md
│   │   └── complex_examples.md
│   └── adr/                         # Architecture Decision Records
│       ├── ADR-001-agent-optimized-documentation-system.md
│       ├── ADR-002-mermaid-diagram-standards.md
│       ├── ADR-003-everything-is-code.md
│       ├── ADR-004-task-completion-source-of-truth-sync.md
│       ├── ADR-005-polyglot-monorepo-workspace-layout.md
│       ├── ADR-006-federated-adr-governance.md
│       └── ADR-007-monorepo-foundation-and-decision-baseline.md
├── docs/                            # Everything is Code — project management
│   └── project/
│       ├── pr/                      # Pull request records (pr-NNNNNNNN-short-description.md)
│       ├── issues/                  # Issue records (issue-NNNNNNNN-short-description.md)
│       └── kanban/                  # Sprint/project boards ({scope}-{id}-short-description.md)
├── .crewai/
│   ├── README.md                    # CrewAI subsystem guide
│   └── adr/                         # CrewAI-local architecture decisions
├── apps/                            # Deployable applications (web/api/cli/mobile)
│   └── README.md
├── services/                        # Long-running backend services and workers
│   └── README.md
├── packages/                        # Shared libraries across runtimes
│   └── README.md
├── data/
│   ├── README.md
│   └── sql/                         # SQL schema, migrations, and seed assets
│       └── README.md
├── notebooks/                       # Jupyter notebooks, prototypes, analyses
└── src/                             # Language-focused source workspace (Python-first)
```

---

## 🎯 Source of truth

### The repository is authoritative

- ✅ **All official files** live in this repo
- ✅ **Complete history** tracked by git commits
- ✅ **Latest version** is always the repo version
- ✅ **Agent entry point** is `AGENTS.md` at the repo root

### Precedence hierarchy

When you find conflicting guidance, check in this order:

1. **`custom-instructions.md`** — project-specific rules (most specific)
2. **`agentic_coding.md`** — agent autonomy boundaries
3. **`contribute_standards.md`** — universal standards
4. **`markdown_style_guide.md` / `mermaid_style_guide.md`** — documentation formatting
5. **`adr/`** — architecture decision records (for rationale behind decisions)
6. **Subsystem `adr/` directories** — local decision logs for subsystem-specific implementation choices (for example `.crewai/adr/`)

If guidance still conflicts after checking all sources, **stop and ask the human**.

---

## 📋 File categories

### Agent operating instructions

| File                            | Purpose                             | When to read         |
| ------------------------------- | ----------------------------------- | -------------------- |
| `instructions.md`               | Entry point — what to read and when | Every task (first)   |
| `agentic_coding.md`             | Autonomy rules + workflow           | Every task           |
| `autonomy_boundaries.md`        | Capability matrix                   | Every task           |
| `workflow_guide.md`             | 14-step process                     | Every task           |
| `contribute_standards.md`       | Code style, commits, PRs            | When writing code    |
| `custom-instructions.md`        | Project-specific rules              | When writing code    |
| `operational_readiness.md`      | System constraints                  | Complex work         |
| `context_budget_guide.md`       | Token management                    | Long sessions        |
| `agent_error_recovery.md`       | Error procedures                    | When errors occur    |
| `idempotent_design_patterns.md` | Idempotent script standards         | When writing scripts |

### Style guides and templates

| Resource                  | Purpose                           | When to read                          |
| ------------------------- | --------------------------------- | ------------------------------------- |
| `markdown_style_guide.md` | Formatting rules for all markdown | Before writing any document           |
| `mermaid_style_guide.md`  | Standards for all diagrams        | Before creating any diagram           |
| `markdown_templates/`     | 9 pre-built document structures   | When creating a new document          |
| `mermaid_diagrams/`       | 23 diagram type guides            | When creating a specific diagram type |

### Project management (Everything is Code)

| Directory              | Contents              | Convention                                  |
| ---------------------- | --------------------- | ------------------------------------------- |
| `docs/project/pr/`     | Pull request records  | `pr-NNNNNNNN-short-description.md`          |
| `docs/project/issues/` | Issue records         | `issue-NNNNNNNN-short-description.md`       |
| `docs/project/kanban/` | Sprint/project boards | `{scope}-{identifier}-short-description.md` |

See the [Everything is Code](markdown_style_guide.md#-everything-is-code) section and [ADR-003](adr/ADR-003-everything-is-code.md) for the full philosophy.

---

## 🔍 Quick answers

- **Where are agent instructions?** → `agentic/`
- **Where are style guides?** → `agentic/markdown_style_guide.md` and `agentic/mermaid_style_guide.md`
- **Where are templates?** → `agentic/markdown_templates/`
- **Where are diagram guides?** → `agentic/mermaid_diagrams/`
- **Where are idempotent script standards?** → `agentic/idempotent_design_patterns.md`
- **Where are PRs/issues/boards?** → `docs/project/pr/`, `docs/project/issues/`, `docs/project/kanban/`
- **Where are apps?** → `apps/`
- **Where are backend services/workers?** → `services/`
- **Where are shared packages?** → `packages/`
- **Where are SQL schemas/migrations?** → `data/sql/`
- **Where are notebooks?** → `notebooks/`
- **Where is language-focused source code?** → `src/`
- **Which version is authoritative?** → The repo version, always
- **Where do I start?** → `AGENTS.md` at repo root → `agentic/instructions.md`
