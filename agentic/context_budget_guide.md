# Context Budget Management Guide

> How to work efficiently with limited context. Token management strategies for long sessions.

**Read this when:** Planning a large task or session getting long.
**Don't read this:** Until you need context management strategies (saves context).

---

## 🧠 Context basics

### What is context?

**Context = tokens available per session.** Every message you send + every response generated uses tokens.

Context varies by model and tool. Common ranges:

| Model tier | Typical context    |
| ---------- | ------------------ |
| Standard   | ~128,000 tokens    |
| Extended   | ~200,000 tokens    |
| Large      | ~1,000,000+ tokens |

Check your tool's documentation for exact limits.

```text
Available:     ~128K–200K+ tokens (varies by model)
Base files:    ~4,000 tokens (instructions, boundaries, workflow)
Your task:     Variable
Conversation:  Grows with each message
Remaining:     What's left for code, analysis, output
```

### Token usage example

```text
Your first message: "Build a dark mode toggle"
Tokens used: ~100 tokens

Agent response: ~500 tokens
Running total: ~600 tokens

Your follow-up: "Here's the code, review it"
Tokens: ~2,000 tokens (code is large)
Running total: ~2,600 tokens

Agent review: ~1,500 tokens
Running total: ~4,100 tokens

Available remaining: ~124K–196K tokens ✅ Plenty of room
```

---

## 📊 Context budget allocation

### Recommended distribution

For a typical task session:

```text
Base instructions:           ~4,000 tokens (5%)
  - instructions.md
  - autonomy_boundaries.md
  - workflow_guide.md

Task context:              ~10,000 tokens (10%)
  - Task description
  - Requirements
  - Background info

Working context:          ~80,000 tokens (60%)
  - File contents
  - Code snippets
  - Analysis
  - Explanations

Buffer/safety:            ~30,000 tokens (25%)
  - Don't use this
  - Keep it free
  - For unexpected needs
```

### Real-world allocation

**Simple task** (bug fix):

```text
Base:     4,000
Task:     2,000
Working: 20,000
Buffer:  102,000+ ← Tons of room
```

**Complex task** (refactor):

```text
Base:     4,000
Task:    10,000
Working: 80,000
Buffer:  34,000+ ← Still safe
```

**Very complex task** (architecture):

```text
Base:     4,000
Task:    20,000
Working: 100,000
Buffer:  4,000+ ← Getting tight, consider new session
```

---

## 🔄 When to create a new session

### Signs you should start fresh

✅ **Create new session when:**

- Context usage > 70%
- Conversation has 50+ messages
- Task changes significantly
- You've been working > 2 hours
- Conversation history getting long
- Work feels slow (agent struggling)

❌ **Don't create new session:**

- You have < 5 messages
- Task is almost done
- Context usage < 50%
- Working smoothly

### Creating new session (checklist)

When context is getting full:

```text
1. ✅ Save current work
   - Push code to remote
   - Commit in-progress work
   - Note where you left off

2. ✅ Write summary for new session
   "Task: Implement dark mode
   Progress: 70% complete
   - Button created
   - Styles working
   - Testing next
   Files changed: src/components/DarkMode.tsx
   Current branch: feat/dark-mode"

3. ✅ Create new session
   - Copy the summary above
   - Paste as first message
   - Continue work from there

4. ✅ Reference old session if needed
   "Earlier in a different session, we decided..."
```

---

## ⚡ Context-efficient workflows

### Strategy 1: Reference files by name

❌ **Bad** (uses lots of context):

```text
You: "Here's the Button component I want to fix:

[Pastes entire 500-line Button.tsx file]

Can you add a new prop?"

Context used: ~2,000 tokens
```

✅ **Good** (saves context):

```text
You: "Fix the Button component (src/components/Button.tsx).
Add a 'disabled' prop that greys out the button."

Context used: ~50 tokens
```

### Strategy 2: Ask for specific sections

❌ **Bad:**

```text
You: "Review the entire codebase and find performance issues."
Context used: ~50,000 tokens (entire repo loaded)
```

✅ **Good:**

```text
You: "Review the database query in
QueryBuilder.ts (lines 45-60) for performance issues."
Context used: ~500 tokens (specific section)
```

### Strategy 3: Keep tasks focused

❌ **Bad** (multiple tasks):

```text
"Build dark mode, add animations, refactor DB, optimize images"
Context used: Explodes because each task needs full context
```

✅ **Good** (single focus):

```text
"Build dark mode toggle. That's it.
Animations and refactoring in separate sessions."
Context used: ~40% of budget
```

### Strategy 4: Summarize frequently

❌ **Bad** (scroll through history):

```text
Session has 100 messages. Need to reference decision from message 15.
Context used: Need to load all 100 messages to find it.
```

✅ **Good** (save summaries):

```text
Every 20 messages: "Summary so far:
- Decided to use React for UI
- Database is PostgreSQL
- Styling with Tailwind"
Context used: Cleaner history, easier to reference
```

---

## 📁 File reference guide

### How to reference files efficiently

```text
✅ GOOD: "Fix the bug in src/utils/helpers.ts, line 45"
❌ BAD:  "Here's the entire helpers.ts file [pastes 5KB]"

✅ GOOD: "Update the Button component's onClick handler"
❌ BAD:  "Here's Button.tsx, PageHeader.tsx, Footer.tsx [pastes 10KB]"

✅ GOOD: "Check the database schema for the users table"
❌ BAD:  "Here's the entire schema.sql file [pastes 20KB]"
```

### Reference shorthand

```text
Instead of:              Use this shorthand:
───────────────────────────────────────────────────
"In src/components       "In Button.tsx
Button.tsx, line 45"     (line 45)"

"In the entire           "In the User model
models/User.ts file"     (see models/User.ts)"

"In src/pages/index      "In the home page
within the Component"    (pages/index.tsx)"
```

---

## 📈 Conversation pacing

### Fast pace (more context)

```text
Session: 10 messages, 50K tokens
Pacing: 5K tokens per message
Length: 2 hours
Risk: Getting full

Solution: Summarize or create new session
```

### Slow pace (less context)

```text
Session: 50 messages, 50K tokens
Pacing: 1K tokens per message
Length: 5 hours
Risk: Low, you can keep going

Solution: Continue in same session
```

### Typical pace (comfortable)

```text
Session: 20 messages, 60K tokens
Pacing: 3K tokens per message
Length: 1-2 hours
Risk: Moderate

Solution: Monitor and create new session at 70%
```

---

## 📦 Large file handling

### Scenario: Editing a large file

```text
File: components/ComplexForm.tsx (3,000 lines)
Task: Add a new field to the form

❌ WRONG:
You: "Here's the entire ComplexForm.tsx"
[Pastes entire 3,000 lines = ~12K tokens]

✅ RIGHT:
You: "In ComplexForm.tsx, the renderFields() function
(lines 500-650) needs a new email field.

Current structure:
- Name field at line 550
- Email field should go after it
- Validation follows same pattern

Can you implement it?"
[~200 tokens of description instead]
```

### Scenario: Multiple file changes

```text
Changes needed in:
- src/components/Form.tsx
- src/utils/validation.ts
- src/pages/settings.tsx

❌ WRONG:
You: "Update all these files"
[Pastes entire content = 10K tokens]

✅ RIGHT:
You: "Update these three files:
1. Form.tsx: Add submit button (around line 200)
2. validation.ts: Add email validation (after line 100)
3. settings.tsx: Update import (line 5)

Here's the exact changes needed:
- Form: Add <button>Submit</button>
- Validation: export function validateEmail()
- Settings: import { validateEmail }

Can you implement?"
[~500 tokens instead of 10K]
```

---

## 📊 Monitoring context usage

### Visual indicators

**Watch for these signs:**

```text
Context at 50% used
✅ Safe, continue normally

Context at 70% used
⚠️ Getting full, start wrapping up

Context at 85% used
🔴 Very full, create new session NOW
```

### How to check

Most AI tools will warn you when context is getting full. You can also estimate:

- Simple conversation: ~1K tokens per message
- With code: ~2–5K tokens per message
- With large files: ~5–10K tokens per message

---

## ✅ Best practices

### DO

- ✅ Reference files by name instead of pasting
- ✅ Ask for specific code sections
- ✅ Keep tasks focused and narrow
- ✅ Create new session when > 70% full
- ✅ Summarize frequently (every 20 messages)
- ✅ Push code regularly (don't lose work)
- ✅ Write clear task descriptions upfront

### DON'T

- ❌ Paste entire files into chat
- ❌ Ask for analysis of whole codebase
- ❌ Try multiple tasks in one session
- ❌ Keep conversation going past 80% full
- ❌ Re-explain the same thing repeatedly
- ❌ Leave code uncommitted
- ❌ Use vague descriptions

---

## 🔍 Quick decision tree

```text
Starting new task
    |
    ├─ Simple (< 1 hour)?
    │  └─ Same session, no worries
    │
    ├─ Complex (1-3 hours)?
    │  └─ Same session, monitor usage
    │
    └─ Very complex (> 3 hours)?
       └─ Plan for new session at 70%

In middle of task
    |
    ├─ < 50% context used?
    │  └─ Continue, lots of room
    │
    ├─ 50-70% used?
    │  └─ Monitor, wrap up soon
    │
    └─ > 70% used?
       └─ Create new session now
```

---

## 📋 Summary

**Context = token budget per session**

- You have ~128K–200K+ tokens (varies by model)
- Use ~4K for base files
- Use ~10–100K for your task
- Keep 20–30K as buffer

**To use context efficiently:**

1. Reference files by name (don't paste)
2. Ask for specific sections (not whole files)
3. Keep tasks focused (one per session)
4. Create new session when > 70% full
5. Summarize periodically

**When in doubt:** Create a new session and continue. It's free, and you get fresh context.
