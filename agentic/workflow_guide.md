# 14-Step Transparent Agentic Workflow

> Detailed walkthrough of the complete process with human checkpoints.

**Read this before creating a branch for new work.**

---

## 🔄 The 14 steps

### Step 1: Human creates task

```text
Human: "Add search functionality to the product catalog"
```

Agent receives clear task description.

---

### Step 2: Agent creates branch

```bash
git checkout -b feat/product-search
```

Branch naming: `feat/`, `fix/`, `docs/`, `chore/` prefix.

---

### Step 3: Agent documents approach

```text
Agent creates design doc:
- What: Full-text search with typeahead
- Why: Users need to find products quickly
- How: Client-side index with server fallback
- Alternatives: External search service, DB full-text search

Commit: "docs: add design notes for product search"
Push to remote
```

**Purpose:** Get feedback on APPROACH before spending time coding.

---

### Step 4: Agent creates draft PR

```text
PR title: "feat(search): implement product search"

Agent creates PR record: docs/project/pr/pr-NNNNNNNN-short-description.md
- Uses the PR template from markdown_templates/pull_request.md
- Includes: Summary, changes, checklist, related docs
- Links to design doc from Step 3

GitHub PR description contains ONLY the full branch URL to the PR file
Example: https://github.com/<org>/<repo>/blob/<branch>/docs/project/pr/pr-NNNNNNNN-short-description.md
Mark as DRAFT (not Ready for Review)
```

**Purpose:** Make intent transparent before implementation.

---

### Step 4.5: Agent syncs source-of-truth tracking files

```text
Before editing implementation files:

✅ Update PR record in docs/project/pr/ with planned scope and next actions
✅ Update issue file(s) in docs/project/issues/ with current status and plan
✅ Update kanban board in docs/project/kanban/ moving work to In Progress

These files are live monitoring surfaces for humans.
```

**Purpose:** Human observers can track execution before code changes begin.

---

### Step 5: Human reviews design ← CHECKPOINT 1

```text
Human reviews:
✅ Design doc from Step 3
✅ PR description

Human provides feedback:
✅ "Design looks good, proceed with implementation"
💬 "Let's discuss alternative approach"
⚠️ "Need to address [concern] before building"

Agent responds to feedback in PR comments
```

**Purpose:** Human steers approach BEFORE coding begins (saves hours if wrong direction).

---

### Step 6: Agent implements (after design approval)

```text
Once human approves approach:
✅ Write feature code
✅ Add tests (unit + integration)
✅ Update documentation (following style guides)
✅ Add accessibility features if applicable

Commit with descriptive multi-line message (see contribute_standards.md):
  Subject: "feat(search): implement product search"
  Body: why the change was made, key files touched, behavioral impact
Run `./scripts/ci-local.sh` before commit/push when available
If local CI cannot run in this environment, document why in PR/issue files
Push to remote
```

**Purpose:** Code with confidence that approach is correct.

---

### Step 7: CI runs (automatic)

```bash
{package-manager} run format     # Fix formatting
{package-manager} run lint       # Fix linting issues
{package-manager} test           # Run tests
{package-manager} run build      # Build project
```

**If issues found:**
→ CI auto-commits: `chore: format and lint [skip ci]`
→ Branch shows green checks when resolved

---

### Step 8: Agent updates PR status

```text
After each milestone (not just once):

✅ Update PR file with progress and scope changes
✅ Update issue file(s) with investigation/fix details
✅ Update kanban board column/status and blockers

Before tests:
✅ Record what validations will run

After tests:
✅ Record pass/fail evidence and next actions

DO NOT change from Draft to Ready yet
```

**Purpose:** Continuous, real-time status visibility for humans via repo files.

---

### Step 9: Human provides code review ← CHECKPOINT 2

```text
Human reviews:
✅ Actual implementation (code, tests, docs)
✅ Test coverage and results
✅ Accessibility and performance

Human provides feedback:
✅ "Code looks good. Mark as Ready for Review when ready."
💬 "Let's improve this edge case"
⚠️ "Need to add test for this scenario"

Agent responds to feedback (see Step 12 if needed)
```

**Purpose:** Human verifies implementation quality and explicitly confirms readiness.

---

### Step 10: Agent marks PR ready ← CHECKPOINT 3 (with permission)

```text
ONLY after human confirmation from Step 9:

Agent updates PR file:
🎯 Status: "Ready for Review - Approved by [human]"

Change from Draft to Ready for Review

Signals to other reviewers:
✅ Design approved
✅ Code approved
✅ Ready for merge decision
```

**Purpose:** Status change is intentional, not automatic. Clear audit trail.

---

### Step 11: Agent waits for final approval

```text
Agent monitors PR for:
✅ Watching for additional feedback
✅ Responding to comments if needed
✅ Awaiting final approval to merge

Agent CANNOT approve own PR
Agent CANNOT request approval from another agent
```

---

### Step 12: Agent responds to feedback (if any)

```text
If human provided feedback in Step 9:

Agent:
✅ Reads review comments carefully
✅ Makes requested changes
✅ Commits with descriptive multi-line message: "fix(search): address review feedback on edge case" + body explaining what changed and why
✅ Pushes to same branch
✅ Responds in PR comments explaining changes
✅ Go back to Step 7 (CI runs again)
```

---

### Step 13: Human merges

```text
Human:
✅ Final approval
✅ Clicks "Squash and merge" or "Merge"
✅ Branch auto-deleted
```

---

### Step 14: Deployment (if applicable)

```text
CI may trigger:
✅ Staging deploy (if configured)

Production deploy requires:
✅ Additional human approval (humans only)
```

---

## 🎯 The 3 transparent checkpoints

This workflow includes **3 clear human approval gates:**

| Checkpoint          | Step | When                   | Who   | Why                                         |
| ------------------- | ---- | ---------------------- | ----- | ------------------------------------------- |
| **Design review**   | 5    | BEFORE coding          | Human | Steer approach early, prevent wasted effort |
| **Code review**     | 9    | AFTER implementation   | Human | Verify quality before "Ready" status        |
| **Status approval** | 10   | BEFORE marking "Ready" | Human | Intentional status change, not automatic    |

---

## 📊 Why this workflow

### Old workflow (no checkpoints)

- Agent codes → Human reviews → Issue discovered → Agent rewrites
- **Cost:** 8+ hours for mistakes caught too late
- **Frustration:** Wasted effort on wrong direction

### New workflow (3 checkpoints)

- Agent designs → Human approves → Agent codes → Human reviews
- **Cost:** 4.5 hours with early course correction
- **Clarity:** Transparent intent at every stage

**Time saved per rejected approach:** ~3.5 hours ⏱️

---

## 🔑 Key principles

### Transparency

- ✅ PR file documents progress
- ✅ Status is explicit (Draft vs. Ready)
- ✅ Human feedback is clear
- ✅ Audit trail shows all approvals

### Human control

- ✅ Humans steer design early
- ✅ Humans approve approach before coding
- ✅ Humans review implementation
- ✅ Humans control PR status changes
- ✅ Humans decide merge

### Efficiency

- ✅ Design checkpoint prevents wasted coding
- ✅ Status updates prevent surprises
- ✅ Selective file loading manages context
- ✅ Clear boundaries reduce escalations

---

## 📋 Common scenarios

### Design gets rejected

```text
Step 5: Human: "This direction won't work. Try approach B instead."

Agent response:
✅ Acknowledge feedback
✅ Update design doc with new approach
✅ Ask clarifying questions if needed
✅ Wait for approval
✅ THEN implement

Time saved: ~6 hours (avoided coding wrong approach)
```

### Code needs changes

```text
Step 9: Human: "Add test for edge case X"

Agent response:
✅ Implement edge case test
✅ Commit: "test(search): add test for edge case X" + body with context
✅ Push to branch
✅ Respond in PR comment
✅ CI runs again
✅ Wait for re-approval
```

### Build fails in CI

```text
Step 7: Build fails: "Lint error on line 42"

Agent response:
✅ See agent_error_recovery.md for error procedures
✅ Fix lint error
✅ Commit: "fix(lint): resolve lint error on line 42" (trivial — body optional)
✅ Push to branch
✅ CI runs again
```

### Breaking change needed

```text
Step 3 (Design): Agent recognizes breaking change

Agent action:
✅ STOP (don't proceed)
✅ Ask in PR: "Is this breaking change intentional?"
✅ Wait for human decision
✅ Proceed based on answer
```

---

## 🔍 Quick reference

| Step | Who       | Action                   | Status                  |
| ---- | --------- | ------------------------ | ----------------------- |
| 1    | Human     | Create task              | —                       |
| 2    | Agent     | Create branch            | In progress             |
| 3    | Agent     | Document approach        | Awaiting review         |
| 4    | Agent     | Create Draft PR          | Awaiting design review  |
| 5    | **Human** | **Review design**        | **CHECKPOINT 1**        |
| 6    | Agent     | Implement (if approved)  | In progress             |
| 7    | CI        | Run tests/lint           | In progress             |
| 8    | Agent     | Update PR status         | Awaiting code review    |
| 9    | **Human** | **Review code**          | **CHECKPOINT 2**        |
| 10   | Agent     | Mark Ready (if approved) | Awaiting merge          |
| 11   | Agent     | Wait                     | Awaiting final approval |
| 12   | Agent     | Respond to feedback      | Back to Step 7          |
| 13   | **Human** | **Merge**                | Complete                |
| 14   | CI        | Deploy (if configured)   | Done                    |

---

## 📚 For more information

- **Autonomy boundaries** → [autonomy_boundaries.md](autonomy_boundaries.md)
- **Error recovery** → [agent_error_recovery.md](agent_error_recovery.md)
- **Project-specific rules** → [custom-instructions.md](custom-instructions.md)
- **Code standards** → [contribute_standards.md](contribute_standards.md)
- **Documentation standards** → [markdown_style_guide.md](markdown_style_guide.md) and [mermaid_style_guide.md](mermaid_style_guide.md)

---

**Remember:** This workflow is designed to catch issues early and keep humans in control. When in doubt, ask.
