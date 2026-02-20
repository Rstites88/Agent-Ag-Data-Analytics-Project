# ADR-002: Mermaid Diagram Standards

| Field               | Value                                                 |
| ------------------- | ----------------------------------------------------- |
| **Status**          | Accepted                                              |
| **Date**            | 2026-02-13                                            |
| **Decision makers** | Clayton Young                                         |
| **Consulted**       | AI agents (iterative testing against GitHub renderer) |
| **Informed**        | All contributors and agents working in this repo      |

---

## 📋 Context

### What prompted this decision?

When adding Mermaid diagrams to documentation, several questions kept recurring: What colors should we use? Can we add emoji? How complex is too complex? Should we use `%%{init}` directives or `classDef`? Do all diagram types support accessibility tags? The answers were inconsistent — sometimes diagrams looked great in light mode and illegible in dark mode, sometimes the parser choked on syntax that seemed valid.

We needed explicit standards so any agent or contributor could produce a Mermaid diagram that renders correctly, looks professional, and is accessible — without trial and error.

### Current state

Before this decision:

- No color palette — agents used arbitrary hex colors or no styling at all
- No accessibility conventions — diagrams had no `accTitle` or `accDescr`
- No guidance on complexity — some diagrams had 50+ nodes and were unreadable
- Flowcharts used for everything — sequence diagrams, ER diagrams, state diagrams all crammed into flowchart syntax
- Parser errors discovered at render time — no documented workarounds for known gotchas

### Constraints

- **GitHub default theming only:** No `%%{init}` directives — they override GitHub's theme switching and break dark mode
- **Both light and dark mode:** Colors must maintain contrast and readability in both GitHub themes
- **No external plugins:** Everything must render with GitHub's built-in Mermaid support (no ZenUML runtime, limited treemap/radar support)
- **Accessible:** Diagrams must have text alternatives for screen readers

### Requirements

This decision must:

- [x] Define a color palette that works in both GitHub light and dark mode
- [x] Establish rules for emoji, bold text, and node labeling
- [x] Cover all 23 Mermaid diagram types with syntax examples
- [x] Document parser gotchas so agents don't waste cycles on trial-and-error
- [x] Provide a complexity management system for large diagrams

---

## 🔍 Options Considered

### Option A: Minimal flair — `classDef` palette, strategic emoji, no `%%{init}`

**Description:** Define 7 approved color classes using `classDef`. One emoji per key node, bold on critical labels. Let GitHub handle theming. Document accessibility via `accTitle`/`accDescr` where supported, Markdown paragraph fallback where not.

**Pros:**

- Colors tested and verified in both GitHub themes
- `classDef` doesn't fight GitHub's theme engine — degrades gracefully
- Emoji add visual scanning cues without overwhelming the diagram
- Simple rules: agents don't need to make judgment calls about styling

**Cons:**

- Less visually striking than fully custom-themed diagrams
- 7 colors may feel limiting for very complex diagrams
- Emoji in some diagram types cause parser errors (architecture, sankey)

**Estimated effort:** M — palette design + testing + 23 type files

### Option B: Full custom theming with `%%{init}` directives

**Description:** Use `%%{init}` JSON blocks to set custom fonts, background colors, line widths, and theme variables per diagram.

**Pros:**

- Maximum visual control — diagrams can be pixel-perfect
- Consistent look regardless of surrounding page theme

**Cons:**

- `%%{init}` overrides GitHub's theme engine — diagrams look good in one mode, terrible in the other
- Fragile — different Mermaid versions interpret `%%{init}` differently
- Verbose — every diagram needs a 10+ line init block
- Not portable — theme vars may not work on GitLab or other platforms

**Estimated effort:** L — design + per-diagram testing in both modes

### Option C: No styling — plain diagrams with default rendering

**Description:** Write diagrams with no color, no emoji, no `classDef`. Rely entirely on GitHub's default Mermaid rendering.

**Pros:**

- Zero maintenance — no palette to maintain or test
- Guaranteed to render since no custom syntax is used
- Fast to author

**Cons:**

- All nodes look identical — no visual hierarchy or emphasis
- Hard to scan — readers can't quickly identify the critical path
- Diagrams feel generic and undifferentiated
- Missing accessibility metadata

**Estimated effort:** S — just syntax, no design

### Decision matrix

| Criterion                     | Weight | Option A: classDef palette    | Option B: %%{init} theming         | Option C: No styling         |
| ----------------------------- | ------ | ----------------------------- | ---------------------------------- | ---------------------------- |
| Light/dark mode compatibility | High   | ✅ Tested both                | ❌ Breaks one mode                 | ✅ Default handles it        |
| Visual clarity                | High   | ✅ Color + emoji for scanning | ✅ Full control                    | ❌ Everything looks the same |
| Agent simplicity              | High   | ✅ 7 classes, clear rules     | ❌ Verbose init blocks             | ✅ Nothing to learn          |
| Portability                   | Medium | ✅ classDef is standard       | ❌ Init vars are platform-specific | ✅ Universal                 |
| Maintenance                   | Medium | ⚠️ 7 colors to maintain       | ❌ Per-diagram configs             | ✅ None                      |

---

## 🎯 Decision

**We chose Option A: Minimal flair with `classDef` palette, strategic emoji, no `%%{init}`.**

The deciding factor was light/dark mode compatibility. `%%{init}` directives override GitHub's theme engine, which means diagrams that look great in light mode become illegible in dark mode (or vice versa). Since we can't control which mode readers use, we need diagrams that work in both. `classDef` with carefully chosen fill/stroke colors provides visual hierarchy without fighting the theme engine.

### Why not the others?

- **Option B (`%%{init}` theming) was rejected because:** It breaks GitHub's automatic theme switching. We tested this — diagrams with custom init themes look great in one mode and unreadable in the other. There's no way to serve both modes with a single init block. This is a dealbreaker for a multi-user repo.
- **Option C (No styling) was rejected because:** Diagrams without visual hierarchy are harder to scan and communicate less effectively. The whole point of adding diagrams is to make information more accessible — unstyled diagrams with identically-colored nodes defeat that purpose.

---

## ⚡ Consequences

### Positive

- Diagrams render correctly in both GitHub light and dark mode without author intervention
- 7 semantic color classes (primary, success, warning, danger, neutral, accent, warm) give agents a simple vocabulary for diagram styling
- Emoji on key nodes provide instant visual scanning cues
- Accessibility (`accTitle`/`accDescr`) is standard on all supporting diagram types
- Parser gotchas are documented — agents don't waste time discovering them

### Negative

- Emoji cause parser errors in architecture (`[]` labels) and sankey diagrams — documented as exceptions
- Some diagram types (kanban, mindmap, pie) don't support `accTitle`/`accDescr` — requires a Markdown paragraph fallback
- 7 colors may feel constraining for extremely complex diagrams (mitigated by the 4-tier complexity system — if you need more colors, the diagram is probably too complex)

### Risks

| Risk                                           | Likelihood | Impact | Mitigation                                                                 |
| ---------------------------------------------- | ---------- | ------ | -------------------------------------------------------------------------- |
| GitHub changes Mermaid rendering engine        | Low        | High   | Pin assumptions in the style guide; re-test palette periodically           |
| New Mermaid diagram types added                | Medium     | Low    | Add a new type file following the existing pattern                         |
| Color palette needs revision for accessibility | Low        | Medium | Palette was tested with contrast checkers; re-evaluate if complaints arise |
| ZenUML/treemap/radar don't render on GitHub    | Medium     | Low    | Documented as caveats in respective type files                             |

### Specific technical decisions

| Decision                                                      | Rationale                                                                                                            |
| ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **No `%%{init}` directives**                                  | Overrides GitHub's theme engine, breaks dark mode                                                                    |
| **No inline `style` on nodes**                                | Same theme-fighting problem; `classDef` is declarative and reusable                                                  |
| **One emoji per key node, not every node**                    | Too many emoji creates visual noise; one per key node provides scanning cues                                         |
| **Bold only on critical labels**                              | Mermaid bold (`**text**`) is rendered differently across diagram types; use sparingly                                |
| **4-tier complexity system**                                  | Simple (4–8 nodes), Moderate (8–15), Complex (15–25 with subgraphs), Very Complex (25+ split into multiple diagrams) |
| **Subgraph-to-subgraph connections for leadership audiences** | Leaders care about system boundaries, not internal wiring                                                            |
| **Internal-node connections for engineer audiences**          | Engineers need to see the specific integration points                                                                |

---

## 📋 Implementation plan

| Step                                           | Owner      | Target date | Status      |
| ---------------------------------------------- | ---------- | ----------- | ----------- |
| Design and test 7-color palette in both themes | Human + AI | 2026-02-13  | ✅ Done     |
| Write core Mermaid style guide                 | Human + AI | 2026-02-13  | ✅ Done     |
| Create 23 diagram type files with exemplars    | Human + AI | 2026-02-13  | ✅ Done     |
| Add complex examples to 11 diagram types       | Human + AI | 2026-02-13  | ✅ Done     |
| Document 3 composition patterns                | Human + AI | 2026-02-13  | ✅ Done     |
| GitHub rendering verification                  | Human      | 2026-02-14  | Not started |

---

## 🔗 References

- [Mermaid Style Guide](../mermaid_style_guide.md) — the output of this decision
- [ADR-001: Agent-Optimized Documentation System](./ADR-001-agent-optimized-documentation-system.md)
- [Mermaid Documentation](https://mermaid.js.org/)
- [GitHub Mermaid Support Announcement](https://github.blog/2022-02-14-include-diagrams-markdown-files-mermaid/)

---

## Review log

| Date       | Reviewer      | Outcome                                                |
| ---------- | ------------- | ------------------------------------------------------ |
| 2026-02-13 | Clayton Young | Accepted — palette tested iteratively during authoring |

---

_Last updated: 2026-02-13_
