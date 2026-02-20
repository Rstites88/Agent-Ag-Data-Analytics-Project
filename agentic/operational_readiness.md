# Operational Readiness & Constraints

> System limits, context budgets, and operational boundaries.

**Read this before:** Starting complex work (refactors, infrastructure changes).
**Don't read this:** Until you need to know about constraints (saves context).

---

## 🧠 Context window management

### Context budget

**Available context per session** varies by model and tool. Common ranges:

| Model tier | Typical context    | Notes                          |
| ---------- | ------------------ | ------------------------------ |
| Standard   | ~128,000 tokens    | Most common default            |
| Extended   | ~200,000 tokens    | Available on many platforms    |
| Large      | ~1,000,000+ tokens | Gemini, some specialized tools |

**What uses context:**

- ✅ Base instructions (loaded at session start)
- ✅ Your task description
- ✅ Files you reference or read
- ✅ All conversation history in the session
- ✅ Code snippets shown or generated

**Rule of thumb:**

- 1 KB of text ≈ ~400 tokens
- 1 large file (5,000 lines) ≈ ~20,000 tokens

### Context management

**When context is low** (< 30% remaining):

1. Work may get slower or less accurate
2. Agent might miss nuances
3. **Action:** Create a new session, provide context summary, continue

**How to manage:**

- ✅ Reference files by name (don't paste full content)
- ✅ Ask for specific sections (not entire files)
- ✅ Keep tasks focused and narrow
- ✅ Create new sessions if conversation gets long

See [context_budget_guide.md](context_budget_guide.md) for complete strategies.

---

## 🌐 GitHub and repository constraints

### API rate limits

**GitHub API limits** (if accessing via integrations):

- Personal: 60 requests/hour (unauthenticated)
- Authenticated: 5,000 requests/hour
- Per-user: 15 requests/second

**Action if hit:**

- Stop making API calls
- Wait 1 hour for reset
- If critical, ask human for help

### File size limits

**GitHub limits:**

- Max file size in UI: 1 MB (but can be larger if pushed)
- Recommended: Keep files < 500 KB for performance
- Max repo size: 100 GB (soft limit)

**Rule of thumb:**

- Single files > 100 KB → consider splitting
- Single files > 500 KB → definitely split

### Push/pull performance

**Large files** can cause:

- Slow pushes
- Slow pulls
- CI/CD delays
- Context window overflow

**Best practice:** Keep files focused and smaller.

---

## ⚙️ CI/CD pipeline constraints

### GitHub Actions limits

**Per-month quotas** (free tier):

- 2,000 minutes/month for private repos
- Unlimited for public repos

**Per-workflow:**

- Max runtime: 6 hours
- Max jobs: 256
- Max matrix: 256 combinations

**Action if approaching limits:**

- Optimize workflows (parallelize, cache dependencies)
- Ask human for guidance
- Consider paid plan if needed

### Workflow execution time

**Typical workflow:**

- Format check: 1–2 minutes
- Lint: 2–3 minutes
- Tests: 5–10 minutes
- Build: 5–15 minutes
- **Total:** 15–30 minutes

**If consistently > 30 minutes:**

- Something is wrong (infinite loop? massive dependency?)
- See [agent_error_recovery.md](agent_error_recovery.md) for troubleshooting

---

## 🔗 Session management

### Session timeouts

Sessions can expire after extended inactivity. Timeout varies by tool — typically 1–4 hours.

**Action:**

1. If session expires, start a new one
2. Provide task context summary
3. Continue work

### Network issues

**If disconnected:**

- Unsaved work might be lost
- Wait for reconnection
- Create new session to resume

**Prevention:**

- Commit regularly (don't keep local changes long)
- Push frequently (keeps backup in remote)

---

## 🔐 Security and access constraints

### Secrets

**Agent can NOT:**

- 🚫 Read or modify secrets
- 🚫 Access secret values

**Why:** Secrets are for humans only (security boundary).

**If you need secret values:**

- Ask human to provide them
- Or ask human to configure in CI/CD platform

### Environment variables

**Agent can NOT:**

- 🚫 Hardcode credentials
- 🚫 Commit `.env.local` files
- 🚫 Set environment variables in CI/CD

**Proper way:**

- Use CI/CD secrets (humans configure)
- Reference in workflows
- Agent never sees actual values

---

## 📊 Project-specific constraints

> 📌 **Define your project's specific resource limits in [custom-instructions.md](custom-instructions.md).** The section below provides a template.

### Example project constraints

<!-- CUSTOMIZE in custom-instructions.md for your project -->

| Constraint                   | Limit                | Action if hit                 |
| ---------------------------- | -------------------- | ----------------------------- |
| Max simultaneous deployments | 1 per environment    | Don't run parallel deploys    |
| Max concurrent builds        | 3                    | Wait for one to finish        |
| API rate limits (project)    | Check project docs   | Batch calls, add delays       |
| Database size                | Check with team lead | Alert human, optimize queries |

---

## 💾 Data and database constraints

### Database size

- Current size: check with project owner
- Max recommended: varies by plan
- If approaching limit: alert human, consider archiving

### Query performance

**Queries should complete:**

- < 100 ms (ideal)
- < 1 second (acceptable)
- > 5 seconds (investigate)

**If query is slow:**

- Add database indexes
- Optimize query logic
- Ask human for database help

### Backup and data safety

**Agent can NOT:**

- 🚫 Drop tables or databases
- 🚫 Delete significant data
- 🚫 Run destructive migrations without approval

**Proper way:**

- Ask human before any destructive operation
- Create backups first (human responsibility)
- Test migrations in dev environment first

---

## 📦 Computational and storage constraints

### Build artifact storage

**GitHub Actions default:** 5 GB cache storage

**If hitting storage limits:**

- Clean old artifacts
- Compress build outputs
- Ask human for guidance

### Container image size (if applicable)

- Free tier: 500 MB storage
- Each image should be < 200 MB if possible

**If image too large:**

- Remove unnecessary dependencies
- Use multi-stage builds
- Minimize layer count

---

## 🕐 Time and scheduling constraints

### Working hours

**Recommendation:**

- Create branches during active hours
- Push complete, tested code
- Humans review when available

### Merge freezes

**Your repo might have:**

- Friday afternoon freezes (no merges)
- Release weeks (restricted changes)
- Holiday freezes

**Check with human before:**

- Major refactors
- Breaking changes
- Infrastructure changes

---

## 🚨 Escalation rules

**For complete escalation rules,** see [autonomy_boundaries.md](autonomy_boundaries.md).

Quick reference:

- 🏠 Breaking changes → Ask
- 🏠 Security modifications → Ask
- 🏠 Architecture decisions → Ask
- 🏠 Uncertain about boundaries → Ask

---

## 🔍 Quick reference

| Constraint            | Limit              | Action if hit          |
| --------------------- | ------------------ | ---------------------- |
| **Context window**    | ~128K–200K+ tokens | Create new session     |
| **GitHub API**        | 5,000/hour         | Wait 1 hour            |
| **Session timeout**   | 1–4 hours idle     | Start new session      |
| **CI/CD runtime**     | 6 hours max        | Optimize workflow      |
| **File size**         | ~100 MB            | Split file             |
| **Database query**    | 5 sec limit        | Optimize query         |
| **Concurrent builds** | 5 max              | Wait for one to finish |

---

## 📌 Remember

- 📊 Constraints exist for **reliability and efficiency**
- 📊 Most constraints are **generous** (rarely hit in normal work)
- 📊 If you hit a constraint, **ask for guidance**
- 📊 Prevention through awareness **saves time**

---

**Operational readiness = fewer surprises, smoother development.**
