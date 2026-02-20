# ADR-001: Agent-Optimized Documentation System

| Field               | Value                                            |
| ------------------- | ------------------------------------------------ |
| **Status**          | Accepted                                         |
| **Date**            | 2026-02-13                                       |
| **Decision makers** | Clayton Young                                    |
| **Consulted**       | AI agents (during iterative development)         |
| **Informed**        | All contributors and agents working in this repo |

---

## 📋 Context

### What prompted this decision?

The `opencode` repo accumulated documentation files over time — ADRs, workflow guides, coding standards, custom instructions — but no unified system governed how documents should be written, formatted, or structured. AI agents producing markdown output inconsistently: different heading conventions, no citation standards, Mermaid diagrams rarely used or poorly formatted, and every document was a one-off.

The result: every agent-generated document needed manual formatting corrections, reviewers spent time on style instead of substance, and there was no way to ensure quality without per-document instructions.

### Current state

Before this decision, documentation was ad hoc:

- Scattered files in `agentic/` with no style guide
- No Mermaid diagram conventions — agents defaulted to flowcharts for everything or skipped diagrams entirely
- No templates — every document started from scratch
- No citation requirements — external claims went unsourced
- No project management files in the repo — PRs, issues, and boards lived only in GitHub's UI

### Constraints

- **No build step:** Everything must render natively on GitHub — no static site generators, no custom CSS, no pre-processing
- **Agent-first audience:** Guides must be machine-readable and unambiguous. Agents are the primary consumers; humans are secondary
- **GitHub theming:** All visual elements (colors, emoji, diagrams) must look good in both GitHub light and dark mode
- **Low maintenance:** The system must be self-contained. No external dependencies, no version pinning, no toolchain to maintain

### Requirements

This decision must:

- [x] Establish a single source of truth for all markdown formatting conventions
- [x] Cover all 23 Mermaid diagram types so agents pick the right one, not just flowcharts
- [x] Provide copy-paste templates for the most common document types
- [x] Work on GitHub without any build step or custom rendering

---

## 🔍 Options Considered

### Option A: Comprehensive in-repo style guide system

**Description:** Build two interlinked style guides (Mermaid + Markdown) with per-diagram-type reference files and 9+ templates. Everything lives in the repo as markdown files. Agents read the guides before producing any document.

**Pros:**

- Agents get unambiguous, specific instructions for every scenario
- Templates eliminate the "blank page" problem — consistent structure from day one
- Per-diagram-type files mean agents can find the right exemplar without reading a 2,000-line monolith
- Fully portable — works on any Git platform, no vendor lock-in

**Cons:**

- Large initial effort (~36 files, ~4,000+ lines of content)
- Maintenance burden if Mermaid syntax changes upstream
- Risk of guides becoming stale if not referenced regularly

**Estimated effort:** L — multiple days of focused authoring and iteration

### Option B: Lightweight linter + minimal README

**Description:** Use markdownlint or a similar tool with a `.markdownlint.yml` config to enforce basic rules. Add a short README with conventions. No templates, no Mermaid guide.

**Pros:**

- Fast to implement (hours, not days)
- Automated enforcement via CI
- Low maintenance

**Cons:**

- Linters enforce syntax, not quality — can't teach agents when to use a sequence diagram vs. a flowchart
- No templates means every document still starts from scratch
- No Mermaid guidance means diagrams remain inconsistent or absent
- Doesn't solve the "right diagram type" problem at all

**Estimated effort:** S — a few hours

### Option C: External documentation site (Docusaurus, MkDocs)

**Description:** Set up a documentation site with a static site generator. Author guides in markdown, build to HTML with custom styling, deploy to GitHub Pages.

**Pros:**

- Richer formatting (custom CSS, interactive elements)
- Better navigation (sidebar, search)
- Professional appearance

**Cons:**

- Introduces a build step and toolchain dependency
- Agents can't read rendered HTML — they need raw markdown
- Maintenance overhead (dependency updates, build config, deployment)
- Violates the "no build step" constraint
- Content is split between source markdown and rendered output

**Estimated effort:** M — setup + content authoring + deployment pipeline

### Decision matrix

| Criterion         | Weight | Option A: In-repo guides             | Option B: Linter + README            | Option C: External site             |
| ----------------- | ------ | ------------------------------------ | ------------------------------------ | ----------------------------------- |
| Agent usability   | High   | ✅ Agents read raw markdown directly | ⚠️ Linter rules, no content guidance | ❌ Agents can't use rendered HTML   |
| Diagram guidance  | High   | ✅ All 23 types covered              | ❌ Not addressed                     | ⚠️ Possible but requires HTML build |
| Template coverage | High   | ✅ 9 templates                       | ❌ None                              | ⚠️ Possible but adds complexity     |
| Maintenance       | Medium | ⚠️ Manual updates needed             | ✅ Low maintenance                   | ❌ Build system + dependencies      |
| Setup effort      | Low    | ❌ Large initial effort              | ✅ Quick                             | ⚠️ Moderate                         |
| Portability       | High   | ✅ Just files, any Git platform      | ✅ Just config, any CI               | ❌ Platform-specific deployment     |

---

## 🎯 Decision

**We chose Option A: Comprehensive in-repo style guide system.**

The primary audience is AI agents, and agents consume raw markdown files — not rendered HTML, not linter configs. A comprehensive style guide with per-diagram-type files gives agents exactly the right reference material for any documentation task. The large initial effort is a one-time cost; the ongoing benefit is every document produced by any agent being consistent without per-document instructions.

### Why not the others?

- **Option B (Linter + README) was rejected because:** It solves syntax enforcement but not quality or decision-making. A linter can't teach an agent when to use an ER diagram instead of a flowchart, or that citations are required for external claims. The documentation problems we had were about content quality and diagram selection, not missing semicolons.
- **Option C (External site) was rejected because:** It introduces a build step, creates a dependency chain, and most critically — agents can't read rendered HTML. The entire point is that agents read these files directly. Adding a build-and-deploy pipeline for documentation violates our "no build step" and "agent-first" constraints.

---

## ⚡ Consequences

### Positive

- Every agent-generated document follows the same structure, formatting, and citation standards
- Mermaid diagrams are used appropriately — agents pick the specific type that matches the content, not just flowcharts
- Templates eliminate review friction — structure is right from the start
- Future contributors (human or AI) have a clear, self-contained reference

### Negative

- ~36 files to maintain — if Mermaid adds or changes diagram types, the type files need updating
- Agents must be instructed to read the style guides — the system doesn't enforce itself automatically
- Large PR for the initial merge — review burden is significant

### Risks

| Risk                                       | Likelihood | Impact | Mitigation                                                                   |
| ------------------------------------------ | ---------- | ------ | ---------------------------------------------------------------------------- |
| Guides become stale as Mermaid evolves     | Medium     | Medium | Note Mermaid version assumptions in the guide; review annually               |
| Agents ignore the guides if not referenced | Medium     | High   | Reference guides in `AGENTS.md` and system prompts                           |
| Templates are too rigid for edge cases     | Low        | Low    | Templates are starting points, not mandates — style guide handles edge cases |

---

## 📋 Implementation plan

| Step                                                    | Owner      | Target date | Status      |
| ------------------------------------------------------- | ---------- | ----------- | ----------- |
| Mermaid style guide + 24 diagram files                  | Human + AI | 2026-02-13  | ✅ Done     |
| Markdown style guide + 9 templates                      | Human + AI | 2026-02-13  | ✅ Done     |
| "Everything is Code" philosophy section                 | Human + AI | 2026-02-13  | ✅ Done     |
| Template upgrades (security, deployment, observability) | Human + AI | 2026-02-13  | ✅ Done     |
| Example files in `docs/`                                | Human + AI | 2026-02-13  | ✅ Done     |
| GitHub rendering verification                           | Human      | 2026-02-14  | Not started |
| Merge to main                                           | Human      | 2026-02-14  | Not started |

---

## 🔗 References

- [Mermaid Style Guide](../mermaid_style_guide.md)
- [Markdown Style Guide](../markdown_style_guide.md)
- [ADR-002: Mermaid Diagram Standards](./ADR-002-mermaid-diagram-standards.md)
- [ADR-003: Everything is Code](./ADR-003-everything-is-code.md)
- [Issue-#1: Create agent-optimized documentation system](../../docs/project/issues/issue-00000001-agentic-documentation-system.md)

---

## Review log

| Date       | Reviewer      | Outcome                                         |
| ---------- | ------------- | ----------------------------------------------- |
| 2026-02-13 | Clayton Young | Accepted — built iteratively throughout the day |

---

_Last updated: 2026-02-13_
