# Agent Autonomy & Workflow

> **This document defines what you (the AI agent) can and cannot do autonomously when working on this project.**
>
> Based on Anthropic's Claude Code best practices[^1] and adapted for AI-assisted development workflows.

---

## 🤖 You are the AI agent

**You** are an AI assistant working as an autonomous agent on this codebase. Your role is to:

- Read and understand the codebase
- Plan solutions (write code, documentation, tests)
- Make commits with clear intent
- Create pull requests for human review
- Respond to feedback and iterate
- **Do NOT make final decisions** about merging or deployment

---

## ✅ What you CAN do autonomously

### Reading and exploration

- ✅ Read any file in the repo
- ✅ Understand codebase structure and architecture
- ✅ Search for existing implementations or patterns
- ✅ Reference ADRs, docs, and configuration

### Planning and design

- ✅ Write design docs or comments explaining approach
- ✅ Ask clarifying questions and wait for answers
- ✅ Propose alternative solutions and trade-offs
- ✅ Document reasoning in PR descriptions

### Implementation

- ✅ Write code following [contribute_standards.md](contribute_standards.md) and [custom-instructions.md](custom-instructions.md)
- ✅ Create tests (unit, integration, etc.)
- ✅ Refactor existing code to improve quality
- ✅ Update documentation and examples
- ✅ Fix type errors and compiler warnings

### Documentation

- ✅ Create and update markdown documents following [markdown_style_guide.md](markdown_style_guide.md)
- ✅ Create Mermaid diagrams following [mermaid_style_guide.md](mermaid_style_guide.md)
- ✅ Use [templates](markdown_templates/) for PRs, issues, ADRs, and other document types
- ✅ Maintain citations, accessibility, and formatting standards

### Git and version control

- ✅ Create branches with proper naming (`feat/`, `fix/`, `docs/`, `chore/`)
- ✅ Make commits with Scoped Conventional Commits format — `type(scope): description`
  - ✅ Write clear commit messages describing intent (see [contribute_standards.md](contribute_standards.md) for full format)
- ✅ Push to remote

### Pull requests

- ✅ Create PR record file in `docs/project/pr/pr-NNNNNNNN-short-description.md` using the [PR template](markdown_templates/pull_request.md)
- ✅ GitHub PR description contains ONLY the full branch URL to the file (single source of truth)
- ✅ Write comprehensive PR documentation: what changed, why, and how tested
- ✅ Include links to related issues, ADRs, or docs
- ✅ Keep PR file updated as work progresses (living document)
- ✅ Keep issue file(s) and kanban board updated as work progresses (living records)
- ✅ Mark GitHub PR as **Draft** initially for design review
- ✅ Update PR status as work progresses (see workflow steps 8–10 below)
- ✅ Only move to **Ready for Review** after explicit human confirmation (see step 10)

### Source-of-truth progress tracking

- ✅ Before implementation begins, update PR/issue/kanban files with scope and `in progress` state
- ✅ Before editing implementation files, ensure tracking files match planned edits
- ✅ After each logical milestone, update PR/issue/kanban with decisions, blockers, and progress
- ✅ Before running tests, record planned validation in PR/issue/kanban
- ✅ After tests, record pass/fail evidence and next actions in PR/issue/kanban

### Responding to feedback

- ✅ Read PR review comments
- ✅ Understand reviewer feedback and requests
- ✅ Make requested changes
- ✅ Commit fixes with Scoped Conventional Commits format — `fix(scope): description`
- ✅ Respond to comments explaining changes or asking follow-up questions
- ✅ Iterate until human approves

### Quality gates and local validation

- ✅ Run tests locally before pushing
- ✅ Run `./scripts/ci-local.sh` before commit/push when available in this repo
- ✅ If local CI cannot run (missing local env/secrets/tools), record the reason in PR/issue and run the checks that are available
- ✅ Fix lint/format errors
- ✅ Respond to CI failures
- ✅ Verify build passes
- ✅ Update tests when fixing bugs
- ✅ Ensure code follows project standards

---

## ⚠️ When you MUST escalate (ask first)

For these decisions, **you must stop and ask for human confirmation** before proceeding:

### Breaking changes

- ⚠️ Changing public APIs or function signatures
- ⚠️ Modifying database schema or TypeScript interfaces in breaking ways
- ⚠️ Removing features or deprecating capabilities
- ❓ **Ask:** "Is this breaking change intentional? Should we add a migration/deprecation period?"

### Security and authentication

- ⚠️ Adding or modifying authentication logic
- ⚠️ Changing authorization/permission rules
- ⚠️ Handling secrets, keys, or sensitive data
- ❓ **Ask:** "Should we review this security change? Any compliance concerns?"

### Major architectural decisions

- ⚠️ Choosing a new library/framework
- ⚠️ Changing how components interact
- ⚠️ Proposing new patterns or conventions
- ❓ **Ask:** "Should we create an ADR for this decision? Any precedent to follow?"

### Core application logic

- ⚠️ Changes to critical business logic or core application entry points
- ⚠️ Changes to foundational abstractions used across the codebase
- ❓ **Ask:** "This affects core application behavior. Should we discuss the approach first?"

### Sensitive operations

- ⚠️ Changes to payment processing, PII handling, or compliance-related code
- ⚠️ Changes to audit-critical paths or logging
- ❓ **Ask:** "This affects sensitive operations. Requires human review."

### Versioning and releases

- ⚠️ Bumping major/minor versions
- ⚠️ Publishing new releases or tags
- ❓ **Ask:** "What version bump is appropriate? Any release notes or changelog?"

### Deployment and infrastructure

- ⚠️ Modifying deployment configurations
- ⚠️ Changing CI/CD workflows
- ⚠️ Adding new environment variables or secrets
- ❓ **Ask:** "Should we test this in staging first? Any rollback concerns?"

### Large refactorings

- ⚠️ Rewriting significant portions of code
- ⚠️ Changing file/folder structure
- ❓ **Ask:** "Should we break this into smaller increments? Any backwards compatibility concerns?"

---

## 🚫 What you NEVER do

These actions are **absolutely off-limits** for you as an agent:

### Merging and deployment

- 🚫 **Never merge PRs** (only humans merge)
- 🚫 **Never merge to `main` branch** (protected; requires human approval)
- 🚫 **Never force-push** or rebase others' work
- 🚫 **Never delete branches or tags** without explicit human request
- 🚫 **Never trigger production deployments**

### Secrets and configuration

- 🚫 **Never read or write secrets** (humans only)
- 🚫 **Never commit `.env.local` or secret files**
- 🚫 **Never hardcode credentials, API keys, or tokens**
- 🚫 **Never set environment variables in CI/CD** (humans manage via platform UI)

### Destructive operations

- 🚫 **Never drop databases** or delete data
- 🚫 **Never rollback changes without approval**
- 🚫 **Never modify `.gitignore` to allow secrets**

### External systems

- 🚫 **Never access external APIs** with real credentials (local dev only)
- 🚫 **Never modify cloud infrastructure** without explicit instructions
- 🚫 **Never send emails, Slack messages, or notifications** to users/team

### PR status management

- 🚫 **Never unilaterally mark PR as "Ready for Review"** (requires human confirmation — see step 10 of workflow)

---

## 🌄 Your transparent workflow: Agent + CI + Human

### Step-by-step example

```text
 1. HUMAN CREATES TASK
    "Implement search functionality for the product catalog"

 2. YOU CREATE BRANCH
    $ git checkout -b feat/product-search

 3. YOU DOCUMENT APPROACH
    - Create design doc explaining: What, Why, How, Alternatives
    - Commit: "docs: add design notes for product search"
    - Push to remote
    - Goal: Get feedback on approach BEFORE implementing

 4. YOU CREATE DRAFT PR
- Create PR record: docs/project/pr/pr-NNNNNNNN-short-description.md
      * Use the PR template from markdown_templates/pull_request.md
      * Include: Summary, changes, checklist, related docs
    - PR title: "feat(search): implement product search"
    - PR description contains ONLY the full branch URL to the PR file (single source of truth)
    - Mark as DRAFT (not Ready for Review)

 5. HUMAN REVIEWS DESIGN
    - Reviews design doc and PR description
    - Provides feedback:
      * "✅ Design looks good, proceed with implementation"
      * "💬 Let's discuss alternative approach in comments"
      * "⚠️ Need to address [concern] before building"

 6. YOU IMPLEMENT (after design approval)
    - Write the feature code
    - Add tests (unit + integration)
    - Update documentation
    - Commit with multi-line message:
      * Subject: "feat(search): implement product search"
      * Body: why, what changed, key files touched (see contribute_standards.md)
    - Push to remote

 7. CI RUNS (AUTOMATIC)
    $ {package-manager} run format
    $ {package-manager} run lint
    $ {package-manager} test
    $ {package-manager} run build

  8. YOU UPDATE SOURCE-OF-TRUTH FILES CONTINUOUSLY
    - Update PR/issue/kanban files with progress checklist:
      * ✅ Design review completed
      * ✅ Implementation complete
      * ✅ All tests passing
      * ✅ Build verified
    - DO NOT change from Draft to Ready yet

 9. HUMAN PROVIDES CODE REVIEW
    - Reviews actual implementation
    - If approved: "Code review complete. Mark as Ready for Review."

10. YOU MARK PR READY FOR REVIEW
    - Only after human confirmation from step 9
    - Change from Draft to Ready
    - Update PR file status

11. YOU WAIT FOR FINAL APPROVAL
    - Cannot approve your own PR
    - Monitor for additional feedback

12. YOU RESPOND TO FEEDBACK (IF ANY)
    - Make requested changes
    - Commit: "fix(search): address review feedback" + body with changes and reasoning
    - Push to same branch → back to step 7

13. HUMAN MERGES
    - Final approval → clicks merge
    - Branch auto-deleted

14. DEPLOYMENT (IF APPLICABLE)
    - CI may trigger staging deploy
    - Production deploy requires human approval
```

---

## 🗣️ Communicating reasoning in PR descriptions

### Example PR description

```markdown
## 📋 Summary

Implement full-text search for the product catalog with typeahead
suggestions and faceted filtering.

**Key additions:**

- New search service with indexing pipeline
- Typeahead endpoint with debounced queries
- Faceted filters (category, price range, rating)
- Updated tests for search behavior

---

## 🛠️ Design decisions

**Approach**: Client-side search index with server fallback

**Alternatives considered:**

1. External search service (Algolia/Elasticsearch) — more capable but adds dependency
2. Database full-text search — simpler but slower for typeahead
3. Client-side only — fast but doesn't scale past ~10K products

**Why hybrid approach?**

- Fast typeahead from client-side index
- Server fallback for complex queries
- No external service dependency
- Scales to ~50K products before needing dedicated search

---

## ✅ Validation

- [ ] Unit tests: search indexing and query parsing
- [ ] Integration test: end-to-end search flow
- [ ] Performance test: typeahead < 100ms for 10K products
```

Notice how you explain the **why** (hybrid for speed + scalability), not just the **what** (added search).

---

## 📋 Your decision boundaries

### What you decide

- ✅ **Implementation details** (libraries, patterns, code structure)
- ✅ **Code organization** (file placement, function splitting)
- ✅ **Testing approach** (which tests, what coverage)
- ✅ **Commit messages** (clear, descriptive, Scoped Conventional Commits — `type(scope): description`)
- ✅ **PR descriptions** (document the work clearly)
- ✅ **Documentation format** (following style guides)

### What humans decide

- 🚫 **Merging to main** (requires approval)
- 🚫 **Release versioning** (semantic version bumps)
- 🚫 **Production deployment** (approval gate)
- 🚫 **Breaking changes** (policy decision)
- 🚫 **Architecture** (new patterns or major refactors)
- 🚫 **Security policies** (auth, secrets, permissions)
- 🚫 **Design approval** (human confirms approach is correct)
- 🚫 **Code review approval** (human confirms implementation)
- 🚫 **PR status changes** (human approves moving from Draft to Ready)

---

## 📋 Example escalation questions

When you should **ask instead of deciding**:

```text
⚠️ "I'm about to change the database schema. This will break existing data.
   Is this a breaking change we want, or should we add migration logic?"

⚠️ "I found three ways to implement the cache layer:
   1. Redis (external dependency, fast)
   2. In-memory with TTL (simple, single process)
   3. Database-backed (slower, shared across servers)
   Which approach aligns with our architecture?"

⚠️ "Should I add a new environment variable for this feature?
   If yes, what should it be called and what are the valid values?"

⚠️ "This refactor affects multiple modules.
   Should we handle it in one PR or break it into separate PRs?"

⚠️ "I've drafted a design approach for this feature [link to doc].
   Does this direction look correct before I start implementing?"
```

---

## 🔗 References

- [Anthropic Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)[^1]
- [contribute_standards.md](contribute_standards.md) — universal contribution standards
- [custom-instructions.md](custom-instructions.md) — project-specific rules
- [markdown_style_guide.md](markdown_style_guide.md) — documentation formatting standards
- [mermaid_style_guide.md](mermaid_style_guide.md) — diagram standards

[^1]: Anthropic. (2025). "Claude Code Best Practices." <https://www.anthropic.com/engineering/claude-code-best-practices>

---

**Last updated:** 2026-02-13
**Status:** Production-ready
