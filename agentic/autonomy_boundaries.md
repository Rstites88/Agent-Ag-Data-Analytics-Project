# Agent Autonomy & Boundaries

> What AI agents can and cannot do when working on this project.

**This is your operating manual. Read it before every task.**

---

## ✅ Agent CAN autonomously do

### Reading and exploration

- ✅ Read any file in the repo
- ✅ Understand codebase structure
- ✅ Search for existing implementations
- ✅ Reference docs, ADRs, configuration

### Planning and design

- ✅ Write design docs explaining approach
- ✅ Ask clarifying questions and wait for answers
- ✅ Propose alternative solutions
- ✅ Document reasoning in PR descriptions

### Implementation

- ✅ Write code following standards
- ✅ Create tests (unit, integration)
- ✅ Refactor existing code
- ✅ Update documentation
- ✅ Fix type errors and warnings

### Documentation

- ✅ Create and update markdown documents following [markdown_style_guide.md](markdown_style_guide.md)
- ✅ Create Mermaid diagrams following [mermaid_style_guide.md](mermaid_style_guide.md)
- ✅ Use [templates](markdown_templates/) for PRs, issues, ADRs, and other document types

### Git and version control

- ✅ Create branches with proper naming (`feat/`, `fix/`, `docs/`, `chore/`)
- ✅ Make commits with Scoped Conventional Commits format — `type(scope): description`
- ✅ Write clear commit messages describing intent (see [contribute_standards.md](contribute_standards.md))
- ✅ Push to remote

### Pull requests

- ✅ Create PRs immediately after starting work
- ✅ Write comprehensive PR documentation
- ✅ Document what changed, why, and how tested
- ✅ Include links to related issues, ADRs, docs
- ✅ Keep PR file updated (living document)
- ✅ Mark PR as **Draft** initially for design review
- ✅ Update PR status as work progresses
- ✅ Move to **Ready for Review** ONLY after explicit human confirmation

### Responding to feedback

- ✅ Read PR review comments
- ✅ Understand reviewer feedback
- ✅ Make requested changes
- ✅ Commit fixes with clear messages
- ✅ Respond to comments
- ✅ Iterate until human approves

### Quality gates

- ✅ Run tests locally before pushing
- ✅ Run `./scripts/ci-local.sh` before commit/push when available in this repo
- ✅ If local CI cannot run (missing local env/secrets/tools), document the skip reason in PR/issue records
- ✅ Fix lint/format errors
- ✅ Respond to CI failures
- ✅ Verify build passes
- ✅ Follow project standards

---

## ⚠️ Agent MUST escalate (ask first)

For these decisions, **stop and ask for human confirmation:**

### Breaking changes

- ⚠️ Changing public APIs or function signatures
- ⚠️ Modifying database schema in breaking ways
- ⚠️ Removing features or deprecating endpoints
- ❓ **Ask:** "Is this breaking change intentional? Should we add a deprecation period?"

### Security and authentication

- ⚠️ Adding/modifying authentication logic
- ⚠️ Changing authorization/permission rules
- ⚠️ Handling secrets, keys, sensitive data
- ❓ **Ask:** "Should we review this security change? Any compliance concerns?"

### Major architectural decisions

- ⚠️ Choosing new library/framework for shared code
- ⚠️ Changing how multiple modules interact
- ⚠️ Proposing new patterns or conventions
- ❓ **Ask:** "Should we create an ADR for this? Any precedent to follow?"

### Core application logic

- ⚠️ Changes to critical business logic or core entry points
- ⚠️ Changes to foundational abstractions used across the codebase
- ❓ **Ask:** "This affects core behavior. Should we discuss the approach first?"

### Sensitive operations

- ⚠️ Changes to payment processing, PII handling, or compliance-related code
- ⚠️ Changes to audit-critical paths or logging
- ❓ **Ask:** "This affects sensitive operations. Requires human review."

### Multi-module changes

- ⚠️ Changes affecting 3+ modules or packages
- ⚠️ Moving shared code between packages
- ❓ **Ask:** "Is this refactoring aligned with our architecture strategy?"

### Versioning and releases

- ⚠️ Bumping major/minor versions
- ⚠️ Publishing new releases or tags
- ❓ **Ask:** "What version bump is appropriate? Release notes needed?"

### Deployment and infrastructure

- ⚠️ Modifying deployment configurations
- ⚠️ Changing CI/CD workflows
- ⚠️ Adding new environment variables or secrets
- ❓ **Ask:** "Should we test in staging first? Any rollback concerns?"

### Large refactorings

- ⚠️ Rewriting significant portions of code
- ⚠️ Changing file/folder structure significantly
- ❓ **Ask:** "Should we break this into smaller increments?"

---

## 🚫 Agent NEVER does

**Absolutely off-limits:**

### Merging and deployment

- 🚫 **Never merge PRs** (only humans merge)
- 🚫 **Never merge to `main` branch** (protected)
- 🚫 **Never force-push** or rebase others' work
- 🚫 **Never delete branches/tags** without explicit request
- 🚫 **Never trigger production deployments**

### Secrets and configuration

- 🚫 **Never read/write secrets** (humans only)
- 🚫 **Never commit `.env.local` or secret files**
- 🚫 **Never hardcode credentials, API keys, tokens**
- 🚫 **Never set environment variables in CI/CD**

### Destructive operations

- 🚫 **Never drop databases** or delete data
- 🚫 **Never rollback changes without approval**
- 🚫 **Never modify `.gitignore` to allow secrets**

### External systems

- 🚫 **Never access external APIs** with real credentials
- 🚫 **Never modify cloud infrastructure** without instructions
- 🚫 **Never send emails, Slack, notifications** to users/team

### PR status management

- 🚫 **Never unilaterally mark PR "Ready for Review"** (see workflow step 10)
- 🚫 **Never force-change PR status** without human confirmation

---

## 🎯 Decision boundaries

### Agent decides

- ✅ Implementation details (libraries, patterns, code structure)
- ✅ Code organization (file placement, function splitting)
- ✅ Testing approach (which tests, what coverage)
- ✅ Commit messages (clear, descriptive)
- ✅ PR descriptions (document work clearly)
- ✅ Documentation format (following style guides)

### Human decides

- 🚫 Merging to main (approval required)
- 🚫 Release versioning (semantic version)
- 🚫 Production deployment (approval required)
- 🚫 Breaking changes (policy decision)
- 🚫 Architecture (new patterns, major refactors)
- 🚫 Security policies (auth, secrets, permissions)
- 🚫 Design approach (human confirms before implementation)
- 🚫 Code quality (human confirms before "Ready")
- 🚫 PR status changes (human approves moving to "Ready for Review")

---

## 📝 Example escalation questions

When to **ask instead of deciding:**

```text
⚠️ "I'm about to change the API response format. This breaks existing clients.
   Is this intentional, or should we add backwards compatibility?"

⚠️ "I found three ways to implement the cache layer:
   1. Redis (external dependency, fast)
   2. In-memory with TTL (simple, single process)
   3. Database-backed (slower, shared across servers)
   Which aligns with our architecture?"

⚠️ "I've drafted a design approach for this feature [link to doc].
   Does this direction look correct before I implement?"

⚠️ "Should I add a new environment variable for this feature?
   If yes, what should it be called and what are valid values?"

⚠️ "This refactor affects 4 modules. Should we:
   A) Handle in one PR, or
   B) Break into separate PRs per module?"
```

---

## 🔄 Quick reference

| Scenario                | Your action                                                              |
| ----------------------- | ------------------------------------------------------------------------ |
| **New feature request** | Ask clarifying questions → Design → Wait for approval → Code → PR        |
| **Bug fix**             | Reproduce → Root cause analysis → Fix → Tests → PR                       |
| **Refactor**            | Understand impact → Propose alternatives → Wait for approval → Implement |
| **Breaking change**     | **STOP** → Ask human → Wait for decision → Proceed                       |
| **Security concern**    | **STOP** → Ask human → Wait for security review → Proceed                |
| **PR review feedback**  | Read comments → Understand requests → Fix → Commit → Respond             |
| **Test failure**        | Investigate → Fix → Re-run → Verify → Commit                             |
| **Merge conflicts**     | See [agent_error_recovery.md](agent_error_recovery.md)                   |

---

## 📚 For more information

- **Workflow details** → [workflow_guide.md](workflow_guide.md)
- **Error recovery** → [agent_error_recovery.md](agent_error_recovery.md)
- **Project-specific rules** → [custom-instructions.md](custom-instructions.md)
- **Code standards** → [contribute_standards.md](contribute_standards.md)
- **Documentation standards** → [markdown_style_guide.md](markdown_style_guide.md) and [mermaid_style_guide.md](mermaid_style_guide.md)

---

**Remember:** When in doubt, **ask**. Humans appreciate clear questions more than silent mistakes.
