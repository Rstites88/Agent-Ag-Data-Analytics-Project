# Universal Contribution Standards

> **This document defines universal best practices for code, documentation, and collaboration in repos using AI-assisted development workflows.**
>
> These standards are **generic and apply to any project**. For project-specific rules, see [custom-instructions.md](custom-instructions.md).

---

## 🌿 DRY and single source of truth (SSOT)

These principles apply to **all work**: code, docs, PRs, and AI-assisted changes.

### Canonical locations

For each type of information, there must be **one canonical home**:

- **Contribution rules and workflows** → this file (`contribute_standards.md`)
- **Project-specific rules** → `custom-instructions.md`
- **Architecture and product decisions** → ADRs in `adr/`
- **Configuration and environment** → `.env.example` and configuration docs
- **Shared code behavior** → reusable functions/modules, not copy-pasted logic
- **Documentation formatting** → [markdown_style_guide.md](markdown_style_guide.md)
- **Diagram standards** → [mermaid_style_guide.md](mermaid_style_guide.md)

If you need to add a new rule:

1. Choose or create **one canonical file/section** for it
2. Add or update it **there** first
3. In other places, **refer back** to that canonical section instead of repeating

### Documentation DRY rules

When working with documentation:

- **Before writing**, search the repo for existing coverage of the same topic
- If something already exists:
  - **Link or reference it** (optionally with a short summary)
  - Avoid creating a second "full" version
- If documentation must appear in multiple places:
  - The **reference doc is canonical**
  - Other docs should give a brief summary and point to the canonical doc
- For examples and snippets:
  - Keep **runnable examples in code files** (`examples/`, test files)
  - Docs should **embed small snippets** or **link to those files**, not maintain large copies

### Code DRY rules

For code changes:

- Avoid duplicating business logic, validation rules, or formatting in multiple places
- When you see copy-paste or near-duplicate code:
  - Extract a **shared function, class, or utility module**
  - Update all call sites to use the shared abstraction
- Prefer:
  - **Small, composable functions** with clear responsibilities
  - **Shared helpers** for cross-cutting concerns (logging, error handling, formatting)

### PR and issue template rules

- Do **not** re-define repo-wide rules in each PR or issue
- Use PR descriptions to describe **this change set** specifically
- Reference sections in contribution standards rather than re-specifying global rules

---

## ✅ Commit standards

### Philosophy: commits are the project's history

The commit log is the **authoritative record** of every decision made in this codebase. Anyone — human or agent — reading `git log` should fully understand **what changed, why it changed, and which files were affected** without opening a single diff.

- **What** → the subject line + body describe the change
- **Why** → the body explains motivation and context
- **When** → the timestamp on the commit
- **Where** → the body names key files and modules touched

If a commit was merged, it was official. The history is the truth. Write commits accordingly.[^cc]

[^cc]: [Conventional Commits v1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) — the full specification.

### Full format

```text
<type>(<scope>): <description>
                                          ← blank line
<body — REQUIRED for non-trivial changes>
                                          ← blank line
<footer(s) — optional>
```

Use **Scoped Conventional Commits**. **Scope is strongly recommended** — only omit for root-level changes that genuinely span the whole project (e.g., `docs: add contributing guide`).

### Types

| Type           | Purpose                                                 | Example                                                |
| -------------- | ------------------------------------------------------- | ------------------------------------------------------ |
| **`feat`**     | New feature or capability                               | `feat(auth): add OAuth2 PKCE flow`                     |
| **`fix`**      | Bug fix                                                 | `fix(cart): prevent negative quantities`               |
| **`docs`**     | Documentation only                                      | `docs(api): add rate limit section to README`          |
| **`style`**    | Formatting, whitespace, semicolons (no logic change)    | `style(ui): apply prettier to form components`         |
| **`refactor`** | Code change that neither fixes a bug nor adds a feature | `refactor(db): replace raw SQL with query builder`     |
| **`perf`**     | Performance improvement                                 | `perf(search): add index on user_email column`         |
| **`test`**     | Adding or updating tests                                | `test(payments): add Stripe webhook integration tests` |
| **`build`**    | Build system or external dependency changes             | `build(docker): multi-stage build for smaller image`   |
| **`ci`**       | CI configuration and scripts                            | `ci(actions): add matrix testing for Node 20/22`       |
| **`chore`**    | Maintenance that doesn't fit above                      | `chore(deps): bump typescript to 5.8`                  |
| **`revert`**   | Reverts a previous commit                               | `revert: feat(auth): add OAuth2 PKCE flow`             |

### Scope

Scope identifies the **module, component, or area** affected. Always use lowercase, no spaces.

```text
feat(auth): implement JWT token refresh strategy
fix(api): handle missing env var gracefully
chore(deps): update eslint to v9.0
test(e2e): add checkout flow smoke tests
```

Project-specific scopes are defined in [custom-instructions.md](custom-instructions.md).

### Subject line rules

- Use **imperative mood** ("add feature" not "added feature")
- **Lowercase** first letter after the colon
- **No period** (.) at the end
- Max **72 characters** for the full header (`type(scope): description`)
- Describe the **what** at a glance — details go in the body

### Body — REQUIRED for non-trivial changes

The body is **mandatory** for any commit that isn't a one-line typo fix or config tweak. Separate from the subject with a blank line. Wrap at **72 characters**.

The body MUST include:

1. **Why** — what motivated this change? What problem existed?
2. **What** — what specifically changed? Name the key files, modules, or components touched
3. **Impact** — how does behavior differ from before? What should reviewers or future readers know?

> **Rule of thumb:** if someone reads only your commit message (no diff), they should understand the change well enough to explain it to a teammate.

**Only skip the body for truly trivial commits** — a typo fix, a single config value change, a version bump. When in doubt, write the body.

### Body examples

```text
feat(auth): add JWT refresh token rotation

Add automatic token rotation on refresh to prevent token reuse attacks.
When a refresh token is used, it is invalidated and a new refresh token
is issued alongside the new access token.

Key changes:
- src/auth/token-service.ts: add rotateRefreshToken() method
- src/auth/middleware.ts: call rotation on /auth/refresh endpoint
- src/db/migrations/004-add-token-family.ts: track token lineage
- src/auth/token-service.test.ts: add rotation and reuse detection tests

Previously, refresh tokens were long-lived and reusable. Now each
refresh token is single-use, with a token family chain for detecting
stolen token reuse (which invalidates the entire family).
```

```text
fix(upload): validate file size before requesting S3 presigned URL

Users could initiate uploads for files exceeding the 50MB limit, which
would succeed at presign but fail during the actual S3 PUT — wasting
time and bandwidth. Now we reject oversized files client-side before
any network call.

Key changes:
- src/components/FileUpload.tsx: add size check before presign fetch
- src/lib/constants.ts: extract MAX_UPLOAD_SIZE_BYTES (50 * 1024 * 1024)
- src/components/FileUpload.test.tsx: add test for oversized file rejection
```

```text
refactor(middleware): replace callback chain with async/await

The auth middleware used 4 levels of nested callbacks which made error
handling inconsistent and the control flow hard to follow. Converted
to async/await with a single try/catch at the top level.

Key changes:
- src/middleware/auth.ts: rewrite from callbacks to async/await
- src/middleware/auth.test.ts: update tests for async signatures

No behavior change — all existing tests pass without modification.
```

```text
docs(adr): add ADR-004 for caching strategy decision

Document the decision to use Redis for API response caching instead
of in-memory LRU or CDN-level caching. Captures the tradeoffs
evaluated and the performance requirements that drove the choice.

Key changes:
- agentic/adr/ADR-004-caching-strategy.md: new decision record
- agentic/adr/README.md: add ADR-004 to index
```

### Footers

Footers go after the body, separated by a blank line. Each footer is `<token>: <value>` or `<token> #<value>`.

| Footer                           | Purpose                                  |
| -------------------------------- | ---------------------------------------- |
| `BREAKING CHANGE: <description>` | Documents a breaking API/behavior change |
| `Refs: #123`                     | References related issue(s)              |
| `Closes: #456`                   | Auto-closes issue on merge               |
| `Co-authored-by: Name <email>`   | Credit co-authors                        |
| `Reviewed-by: Name <email>`      | Credit reviewer                          |

### Breaking changes

Two ways to signal a breaking change — use **both** together:

1. **`!` after the scope** — visible in git log at a glance
2. **`BREAKING CHANGE:` footer** — explains what broke and migration path

```text
feat(api)!: redesign auth endpoint response format

Consolidate token endpoints into a single /auth/token route that
returns both access and refresh tokens in a structured response.

Key changes:
- src/routes/auth.ts: merge /token and /refresh into unified endpoint
- src/types/auth.ts: update AuthResponse type definition
- docs/api/auth.md: update endpoint documentation
- src/routes/auth.test.ts: update all token endpoint tests

BREAKING CHANGE: /auth/token now returns { accessToken, refreshToken }
instead of { token }. All clients must update to use the accessToken
field. See migration guide in docs/migrations/auth-v2.md.
Refs: #142
```

### Good vs. bad

```text
# ✅ Good — scoped, descriptive body, names files, explains why
feat(search): add fuzzy matching for product names

Product search was exact-match only, causing users to miss results
for minor typos (e.g., "iphne" → "iphone"). Add Levenshtein-based
fuzzy matching with a configurable distance threshold.

Key changes:
- src/search/fuzzy.ts: new fuzzy matching module
- src/search/index.ts: integrate fuzzy into search pipeline
- src/search/fuzzy.test.ts: add tests for distance thresholds
- src/lib/config.ts: add FUZZY_MATCH_DISTANCE env var (default: 2)

# ❌ Bad — no body, vague, no files, no context
fix: fixed stuff

# ❌ Bad — no scope, wrong tense, no body
feat: updates

# ❌ Bad — subject too long, no body to compensate
refactor: refactoring code to make it better and more maintainable

# ❌ Bad — not a commit message
WIP
```

### Trivial commits — body optional

For genuinely trivial changes, a subject-only commit is acceptable:

```text
# These are fine without a body:
fix(typo): correct "recieve" → "receive" in error message
chore(deps): bump eslint from 9.1 to 9.2
style(ui): remove trailing whitespace in Button.tsx
```

### Multi-commit PR — keep each commit atomic

Each commit in a PR should be a **single logical change** that builds and passes tests independently. Every commit gets its own descriptive body.

```text
# PR: "Add user profile page"
# Each of these has a full body (shown as subject-only for brevity):

feat(ui): add profile page layout and routing          # skeleton
feat(api): add GET /users/:id endpoint                 # backend
feat(ui): wire profile page to user API                # integration
test(e2e): add profile page smoke tests                # verification
docs(api): document user profile endpoint              # documentation
```

---

## 📋 PR description standards

PR descriptions must be **easy to scan**, consistent, and professional.

### Required sections

Every PR MUST include:

- **Summary** — what changed and why, with key highlights
- **Success criteria** — definition of done (checklist)
- **Task plan** — items that satisfy those outcomes (checklist)
- **Validation** — how you tested the change
- **Status** — current state (In progress | Ready for review | Ready to merge | Blocked)

### Styling rules

- Use emoji headers for major sections (professional + minimal; one emoji per section)
- Use `---` horizontal rules between major sections
- Use **bold** only for key status indicators and high-signal callouts
- Use `inline code` for file paths, commands, branches, and technical terms
- Use `>` blockquotes for warnings/corrections/important notes
- Use bullets for lists; use numbers only when order matters
- Keep paragraphs short (2–3 sentences max)

For comprehensive formatting rules, see [markdown_style_guide.md](markdown_style_guide.md).

---

## 📝 File-based PR management

This framework uses a **file-based PR tracking system** following the [Everything is Code](markdown_style_guide.md#-everything-is-code) philosophy. Every pull request has a corresponding markdown file in `docs/project/pr/`.

### Why file-based?

- ✅ **Everything is code** — version controlled, searchable, agent-readable
- ✅ **Single source of truth** — PR description links to file, not duplicated
- ✅ **Historical record** — all merged PRs preserved forever in `docs/project/pr/`
- ✅ **Agent-native** — agents read files locally, no API needed
- ✅ **Portable** — GitHub → GitLab → Gitea, your PR history comes with you

### PR file naming convention

Format: `docs/project/pr/pr-NNNNNNNN-short-description.md`

- **Zero-padded 8-digit numbering:** `00000001`, `00000002`, `00000003`...
- **Append a clear slug:** short lowercase hyphenated description after the number
- **Examples:**
  - `docs/project/pr/pr-00000001-agentic-docs-and-monorepo-modernization.md` ✓
  - `docs/project/pr/pr-00000042-fix-preview-deploy-timeout.md` ✓
  - `docs/project/pr/42-fix-bug.md` ✗ (wrong format)

Use the [PR template](markdown_templates/pull_request.md) for structure.

### GitHub PR requirements

When creating the GitHub PR:

1. **Title:** Scoped Conventional Commits format — `type(scope): description`
2. **Description:** Include ONLY the full branch URL to the PR record file — do NOT duplicate content
   - Format: `https://github.com/<org>/<repo>/blob/<branch>/docs/project/pr/pr-NNNNNNNN-short-description.md`
3. **The file is the single source of truth** — all details, changes, and decisions live there

### Directory structure

```text
docs/
└── project/
    ├── pr/                # Pull request records
    │   ├── pr-00000001-agentic-docs-and-monorepo-modernization.md
    │   ├── pr-00000002-fix-preview-timeout.md
    │   └── ...
    ├── issues/            # Issue records
    │   ├── issue-00000001-agentic-documentation-system.md
    │   └── ...
    └── kanban/            # Sprint/project boards
        ├── sprint-2026-w07-agentic-template-modernization.md
        └── ...
```

### Agent workflow for PRs

**When creating a PR:**

1. Create branch with descriptive name
2. Make code changes
3. Create `docs/project/pr/pr-NNNNNNNN-short-description.md` using the [PR template](markdown_templates/pull_request.md)
4. Push branch
5. Create GitHub PR with body set to only the full branch URL to the PR record file
6. Mark as Draft for design review

**When reviewing a PR:**

1. Read the PR file (source of truth)
2. Check checklist completion
3. Review code changes
4. Comment in GitHub
5. Approve when ready

---

## 🗣️ Comments and review standards

When writing PR comments, issue comments, or review feedback:

- Keep comments concise, actionable, and specific
- Use Markdown formatting to improve clarity:
  - Bullet lists for multiple points
  - `inline code` for identifiers and paths
  - Code blocks for snippets
- Prefer "what + why + suggested fix" in 1–4 sentences
- Use light structure for longer comments:

```markdown
**Issue**

- Describe the problem

**Why it matters**

- Explain the impact

**Suggested change**

- Provide a solution or question
```

---

## 📋 Documentation styling standards

Documentation should be **high-signal and skimmable**. The authoritative references for formatting are:

- **[markdown_style_guide.md](markdown_style_guide.md)** — comprehensive formatting rules for all markdown
- **[mermaid_style_guide.md](mermaid_style_guide.md)** — standards for all Mermaid diagrams

This section provides a summary. When in doubt, the style guides are authoritative.

### Preferred structure

- Use `##` for primary sections and `###` for subsections
- Use `---` between major sections when it improves readability
- Keep headers concise and meaningful
- One emoji per H2 heading — no emoji on H3/H4

### Callouts

Use blockquotes for important notes:

```markdown
> **Note:** Helpful context.
> **Warning:** Important risk or gotcha.
```

### Lists and tables

- Use bullet lists for sets of related items
- Use numbered lists only for sequences or instructions
- Use tables for comparisons and structured reference information

### Code and diagrams

- Use fenced code blocks with language tags (`javascript`, `bash`, `python`, etc.)
- **Prefer Mermaid diagrams** for architecture, workflows, data flows, or state diagrams
- When a diagram is warranted, read [mermaid_style_guide.md](mermaid_style_guide.md) first, then the [specific type file](mermaid_diagrams/)
- Keep diagrams **close to the section they explain**
- Keep diagrams small and high-signal rather than sprawling

---

## 🔐 Secrets policy

- **Never commit secrets** (API keys, tokens, passwords, credentials)
- Use `.env.example` for documented config with placeholder values
- Ensure `.env`, `.env.local`, `.env.*.local`, and similar are in `.gitignore`
- For sensitive configuration:
  - Document the key name in `.env.example`
  - Provide instructions on how to set it
  - Store actual values in CI/CD secrets or secure vaults

### Example `.env.example`

```bash
# Authentication
JWT_SECRET=your-secret-here-minimum-32-chars
OAUTH_CLIENT_ID=get-from-provider-console

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/mydb

# Third-party APIs
API_KEY=your-api-key-here
WEBHOOK_SECRET=your-webhook-secret
```

---

## 📚 Monorepo expectations

For projects using monorepo structure:

- **Respect workspace boundaries** (`apps/`, `packages/`, etc.)
- **Follow project-specific conventions** (see [custom-instructions.md](custom-instructions.md))
- **Maintain canonical docs** in `docs/` (one source of truth per topic)
- **Keep examples runnable** (in `examples/` or test files, not drift-prone docs)
- **Extract shared logic** to `packages/` or `shared/` (avoid duplication across workspaces)

---

## 🤐 CI/CD and quality gates

All repos should implement automated quality checks on every commit:

- **Local pre-push CI run** — if the repo provides `./scripts/ci-local.sh`, run it before commit/push unless explicitly instructed not to
- **Environment exception handling** — if local CI cannot run in the current environment (missing secrets/tools or hosted runner constraints), document the skip reason in PR/issue records and proceed with available checks

- **Formatting** — code style consistency (e.g., Prettier, Black)
- **Linting** — code quality rules (e.g., ESLint, Ruff)
- **Testing** — unit and integration tests for affected packages
- **Building** — verify affected packages build successfully

See your project's `.github/workflows/` for workflow definitions and [custom-instructions.md](custom-instructions.md) for project-specific CI commands.

---

## ⚖️ License and attribution

- This repository is licensed under **Apache-2.0**.
- For redistributions and derivative works, keep both `LICENSE` and `NOTICE`.
- Preserve attribution to **Superior Byte Works, LLC** and **Clayton Young (Boreal Bytes)** where existing notices are present.
- Do not add policy text that conflicts with Apache-2.0 warranty/liability disclaimers.

---

## 🔗 References

- [Conventional Commits](https://www.conventionalcommits.org/) — commit message specification
- [Semantic Versioning](https://semver.org/) — version numbering scheme
- [Architecture Decision Records](https://adr.github.io/) — capturing design decisions
- [Mermaid Diagrams](https://mermaid.js.org/) — documentation visualization
- [markdown_style_guide.md](markdown_style_guide.md) — formatting standards for this project
- [mermaid_style_guide.md](mermaid_style_guide.md) — diagram standards for this project
