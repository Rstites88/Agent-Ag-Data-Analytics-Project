# Agent Error Recovery Procedures

> What to do when things break. Self-recovery procedures for 9 common errors.

**Read this when**: An error occurs during work.  
**Don't read this**: Until you hit an error (saves context).

---

## Error Categories

1. Git Conflicts
2. Build Failures
3. Test Failures
4. API Rate Limits
5. Database/Schema Errors
6. File System Issues
7. Workspace State Corruption
8. Context Window Exhaustion
9. Session/Connectivity Issues

---

## 1. Git Merge Conflicts

### What Happens

```bash
$ git pull origin main
Auto-merging src/components/Button.tsx
CONFLICT (content): Merge conflict in src/components/Button.tsx
Automatic merge failed; fix conflicts and then commit the result.
```

### Why It Happened

Someone else modified the same file and merged to `main` while you were working.

### Recovery Steps

```bash
# Step 1: See which files have conflicts
$ git status

# Output shows:
# both modified:   src/components/Button.tsx
# both modified:   src/utils/helpers.ts

# Step 2: Open conflicted files and look for markers
<<<<<<< HEAD (your changes)
const ButtonA = () => { ... }
=======
const ButtonB = () => { ... }
>>>>>>> origin/main (main branch)

# Step 3: Decide which version to keep
# Option A: Keep your version
# Option B: Keep their version
# Option C: Merge both intelligently

# Step 4: Remove conflict markers
# Edit the file, delete <<<<<<, ======, >>>>>>> markers
# Keep the code you want

# Step 5: Mark as resolved
$ git add src/components/Button.tsx

# Step 6: Complete the merge
$ git commit -m "resolve: merge conflicts from main"

# Step 7: Push
$ git push origin your-branch
```

### When to Escalate

✅ **Escalate** if:

- Conflict is in critical business logic
- You're unsure which version is correct
- Both versions have important changes
- Conflict involves 3+ files

### Example Resolution

```typescript
// BEFORE (conflict)
<<<<<<< HEAD
const Button = ({ label, color = 'blue' }) => {
  return <button className={color}>{label}</button>
}
=======
const Button = ({ label, variant = 'primary' }) => {
  return <button className={`btn-${variant}`}>{label}</button>
}
>>>>>>> origin/main

// AFTER (resolved - merge both)
const Button = ({ label, color = 'blue', variant = 'primary' }) => {
  const className = variant || color;
  return <button className={className}>{label}</button>
}
```

---

## 2. Build Failures

### What Happens

```bash
$ pnpm build
> Next.js build
error - ./src/pages/index.tsx:5:0
Module not found: Can't resolve './components/Button'
```

### Why It Happened

1. Import path is wrong
2. File doesn't exist
3. File was deleted
4. Typo in filename

### Recovery Steps

```bash
# Step 1: Read the error carefully
error - ./src/pages/index.tsx:5:0
       └─ Line 5 in this file

Module not found: Can't resolve './components/Button'
                                  └─ This path doesn't exist

# Step 2: Check if file exists
$ ls -la src/components/Button.tsx
# If not found, it doesn't exist

# Step 3: Find the correct file
$ find src -name "Button*"
src/components/Button.tsx
# Found it! Now check the actual name

# Step 4: Fix the import path
# In src/pages/index.tsx, line 5:
// WRONG: import { Button } from './components/Button'
// RIGHT: import { Button } from '@/components/Button'  (if using aliases)
// RIGHT: import { Button } from '../components/Button'  (if using relative)

# Step 5: Test the build
$ pnpm build

# Step 6: If successful, commit
$ git add .
$ git commit -m "fix(build): correct import paths" \
  -m "Build failed due to wrong import path for Button component in
src/pages/index.tsx. Updated to use the correct path alias.

Key changes:
- src/pages/index.tsx: fix Button import path"
```

### Common Build Errors

| Error                              | Cause                 | Fix                                       |
| ---------------------------------- | --------------------- | ----------------------------------------- |
| `Module not found`                 | Import path wrong     | Fix import path                           |
| `Cannot find module`               | File deleted          | Restore file or remove import             |
| `Unexpected token`                 | Syntax error          | Fix syntax (missing comma, bracket, etc.) |
| `ReferenceError: X is not defined` | Variable not declared | Declare variable or import it             |
| `Type mismatch`                    | TypeScript error      | Fix type annotation                       |

### When to Escalate

✅ **Escalate** if:

- Build fails for unknown reason
- Error message doesn't make sense
- You've tried common fixes and still broken
- Build was working 1 commit ago and no code changes

---

## 3. Test Failures

### What Happens

```bash
$ pnpm test
FAIL  src/utils/helpers.test.ts
  ✓ sum adds numbers correctly
  ✗ multiply handles zero (12ms)

Expected: 0
Received: undefined
```

### Why It Happened

1. Code behavior changed
2. Test expectation is wrong
3. Function isn't exported
4. Test setup is missing

### Recovery Steps

```bash
# Step 1: Read the failing test
$ cat src/utils/helpers.test.ts | grep -A 10 "multiply handles zero"

test('multiply handles zero', () => {
  expect(multiply(5, 0)).toBe(0);
});

# Step 2: Check the implementation
$ cat src/utils/helpers.ts | grep -A 5 "export function multiply"

export function multiply(a, b) {
  return a * b;  // This should work...
}

# Step 3: Test manually
$ node
> const { multiply } = require('./src/utils/helpers.ts')
> multiply(5, 0)
0  // Works!

# Step 4: Debug the test
# Maybe function isn't exported correctly?
$ npm test -- --verbose src/utils/helpers.test.ts

# Step 5: Fix the issue
# Often it's one of:
// A) Function not exported
// B) Test import path wrong
// C) Mock not set up correctly

# Step 6: Re-run test
$ pnpm test src/utils/helpers.test.ts

# Step 7: All green, commit
$ git add .
$ git commit -m "fix(test): correct multiply test assertion" \
  -m "The multiply function test expected 6 but the function returns
the correct value of 8 for inputs (2, 4). Updated the expected
value in the assertion.

Key changes:
- src/utils/helpers.test.ts: fix expected value in multiply test"
```

### When to Escalate

✅ **Escalate** if:

- Test is checking correct behavior
- Implementation matches test expectations
- But test still fails
- Test setup is complex (mocks, fixtures, etc.)

---

## 4. API Rate Limits

### What Happens

```
Error: 429 Too Many Requests
Rate limit exceeded: 5,000 requests/hour
Reset at: 2026-01-12 14:30:00 UTC
Retry after: 3,600 seconds
```

### Why It Happened

1. Made too many API calls too fast
2. Forgot to batch requests
3. Loop making requests without delays
4. Hitting API limit in CI/CD

### Recovery Steps

```bash
# Step 1: STOP making API calls
# Don't retry immediately (you'll hit limit again)

# Step 2: Wait for rate limit reset
echo "Rate limit resets in 1 hour"
echo "Current time: $(date)"
echo "Reset time: (add 1 hour)"

# Step 3: Fix the root cause
# Common fixes:

# A) Add delays between calls
for item in items:
    await api.call(item)
    await delay(100)  # 100ms between calls

# B) Batch requests
const results = await api.batchCall(items)  # 1 call instead of 100

# C) Reduce request count
# Instead of: Check every file individually
// Changed to: Check all files in one request

# Step 4: Test with reduced load
$ pnpm test  # Local test with small dataset

# Step 5: After rate limit resets, try again
# The issue is fixed, so it won't happen again

# Step 6: Commit the fix
$ git add .
$ git commit -m "fix(api): add delays between API calls to respect rate limits" \
  -m "Rapid sequential API calls were triggering 429 rate limit errors.
Added configurable delay between calls and batched file checks into
a single request where possible.

Key changes:
- src/services/api-client.ts: add throttle delay between requests
- src/services/file-checker.ts: batch individual checks into bulk endpoint"
```

### Prevention

- ✅ Always check API docs for rate limits
- ✅ Add delays between calls
- ✅ Batch requests when possible
- ✅ Cache responses
- ✅ Test locally with small datasets first

---

## 5. Database/Schema Errors

### What Happens

```
Error: Column "new_field" does not exist
Syntax error: Foreign key constraint violated
Error: Duplicate key value violates unique constraint
```

### Why It Happened

1. Migration not run
2. Schema changed, code didn't
3. Trying to insert invalid data
4. Foreign key constraint violated

### Recovery Steps

```bash
# Step 1: Check if migration exists
$ ls migrations/
001_create_users.sql
002_add_email_field.sql
003_create_posts.sql  # ← New one you added

# Step 2: Check if migration was applied
$ psql -d mydb -c "SELECT name FROM migrations_run;"
Output:
001_create_users
002_add_email_field
# 003 NOT in the list!

# Step 3: Run pending migrations
$ pnpm db:migrate
Applying: 003_create_posts.sql
✓ Migration applied

# Step 4: If data constraint issue
# Problem: Foreign key violation
# Solution: Ensure referenced data exists

# Step 5: Test again
$ pnpm test:db

# Step 6: Commit
$ git add .
$ git commit -m "fix(db): apply pending database migration" \
  -m "Database tests failed because migration 003 had not been applied
to the local dev database. Ran pending migration to add the
user_preferences table that the new tests depend on.

Key changes:
- db/migrations/003-add-user-preferences.sql: applied (no file change)"
```

### When to Escalate

✅ **Escalate** if:

- Data corruption suspected
- Production database affected
- Need to rollback migration
- Complex data transformation needed

---

## 6. File System Issues

### What Happens

```
Error: ENOENT: no such file or directory, open '/path/to/file'
Error: EACCES: permission denied, mkdir '/path/to/dir'
Error: EISDIR: illegal operation on a directory
```

### Recovery Steps

```bash
# Step 1: Check if file/directory exists
$ ls -la /path/to/file
# If not found, file doesn't exist

# Step 2: Create it or fix the path
$ mkdir -p /path/to/directory

# Step 3: Fix file permissions if needed
$ chmod 755 /path/to/file

# Step 4: Check if path in code is correct
# Common issue: Using Windows path on Linux (or vice versa)
// WRONG: const file = 'C:\\path\\to\\file'  (Windows only)
// RIGHT: const file = path.join(process.cwd(), 'relative', 'path')

# Step 5: Test
$ node script.js

# Step 6: Commit
$ git add .
$ git commit -m "fix(env): use cross-platform file paths" \
  -m "Script used hardcoded Windows-style backslash paths which broke
on Linux/macOS CI runners. Replaced with path.join() for
cross-platform compatibility.

Key changes:
- scripts/process-data.js: replace hardcoded paths with path.join()"
```

---

## 7. Workspace State Corruption

### What Happens

```
Error: Workspace is in an inconsistent state
Error: Build cache corrupted
Error: Node modules out of sync
```

### Recovery Steps

```bash
# Step 1: Clean everything
$ rm -rf node_modules pnpm-lock.yaml
$ pnpm install  # Fresh install

# Step 2: Clear build cache
$ rm -rf .next dist build
$ pnpm build

# Step 3: If still broken, nuclear option
$ git clean -fdx
$ git reset --hard HEAD
$ pnpm install
$ pnpm build

# Step 4: Test
$ pnpm test

# Step 5: If working now, don't commit anything
# (You only reset to clean state)
```

---

## 8. Context Window Exhaustion

### What Happens

```
Warning: You're at 85% context usage
Warning: Thread context limit approaching
Notice: Consider creating new Thread
```

### Recovery Steps

1. **Create new Thread**
   - Copy task description
   - Provide current context (what was done, next steps)
   - Continue work in fresh thread

2. **Provide context in new thread**

   ```
   Task: Implement dark mode toggle
   Progress: Completed 70%, working on button styling
   Next: Test dark mode in all components
   ```

3. **Continue work** in new thread with fresh context

See `context_budget_guide.md` for full strategy.

---

## 9. Session/Connectivity Issues

### What Happens

```
Error: Session timed out
Error: Connection lost
Error: 503 Service Unavailable
```

### Recovery Steps

1. **If session timed out**:
   - Refresh browser
   - Create new Thread
   - Provide context and continue

2. **If connection lost**:
   - Wait for reconnection
   - Don't retry immediately
   - Check your internet connection

3. **If service down**:
   - Wait for service to recover
   - Check status page
   - Ask human if urgent

---

## Error Decision Tree

```
Error occurred
    |
    ├─ Git conflict?
    │  └─ See: Git Merge Conflicts
    ├─ Build failed?
    │  └─ See: Build Failures
    ├─ Test failed?
    │  └─ See: Test Failures
    ├─ API rate limit?
    │  └─ See: API Rate Limits
    ├─ Database error?
    │  └─ See: Database Errors
    ├─ File system error?
    │  └─ See: File System Issues
    ├─ Workspace corrupted?
    │  └─ See: Workspace Corruption
    ├─ Context exhausted?
    │  └─ See: Context Exhaustion
    ├─ Session/connection issue?
    │  └─ See: Session/Connectivity Issues
    └─ Unknown error?
       └─ Ask human for help
```

---

## When to Self-Recover vs. Escalate

### ✅ Self-Recover (Try These First)

- Git merge conflicts (9/10 times)
- Build failures (8/10 times)
- Test failures (8/10 times)
- File system issues (9/10 times)
- Most errors with clear error messages

### ⚠️ Ask Human

- Database data corruption
- Security/authentication errors
- Deployment issues
- Unknown errors (not in this guide)
- Errors you've tried to fix but still broken
- If unsure, always ask

---

## Summary

**Most errors are recoverable** if you:

1. Read the error message carefully
2. Understand what went wrong
3. Follow the recovery steps
4. Test the fix
5. Commit the changes

**Don't hesitate to ask** if error is unclear or recovery fails.
