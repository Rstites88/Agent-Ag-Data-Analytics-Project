# CrewAI Tools - CI Log Analysis

> **Location:** `.crewai/tools/ci_tools.py`  
> **Purpose:** Intelligent analysis of CI job logs with size-aware reading strategies

---

## 📚 Overview

These tools enable CrewAI agents to analyze CI pipeline results efficiently by:

- ✅ Checking log sizes before reading (avoid token waste)
- ✅ Reading summaries first (know WHAT failed)
- ✅ Using grep/search for large logs (targeted investigation)
- ✅ Providing actionable feedback (file:line references)

---

## 🧰 Available Tools

### 1. `read_job_index()`

**Purpose:** Get overview of all CI jobs  
**Use Case:** ALWAYS call this first  
**Returns:** Job names, statuses, log sizes, timestamps

**Example Output:**

```
# CI Job Index

Workflow Run: 123456 (#42)

## Jobs (4 completed)

✅ credential-validation (success)
   - Folder: `credential-validation`
   - Log size: 12.3KB (small - safe to read)
   - Timestamp: 2026-01-30T01:09:38Z

❌ core-ci (failure)
   - Folder: `core-ci`
   - Log size: 245.7KB (LARGE - use grep/search)
   - Timestamp: 2026-01-30T01:10:15Z
```

**When to Use:**

- ✅ Start of every CI analysis
- ✅ To see which jobs ran
- ✅ To identify failed jobs

---

### 2. `check_log_size(folder_name)`

**Purpose:** Check size before reading  
**Use Case:** Before calling `read_full_log()`  
**Returns:** Size stats + recommendation

**Example:**

```python
size = check_log_size('core-ci')
# Returns:
# 🚨 Recommendation: DO NOT READ FULLY
# This log is too large (245.7KB). Use search_log instead.
```

**Size Thresholds:**

- **< 50KB:** Safe to read fully
- **50-200KB:** Read with caution
- **> 200KB:** MUST use search/grep

**When to Use:**

- ✅ Before calling `read_full_log()`
- ✅ To decide between full read vs search
- ❌ Don't use if log size already shown in index

---

### 3. `read_job_summary(folder_name)`

**Purpose:** Read GitHub Actions step summary  
**Use Case:** ALWAYS read summaries before logs  
**Returns:** Formatted summary showing what failed

**Example Output:**

```markdown
# Core CI Summary

❌ **Tests failed**

## Test Results

- ✅ Format checks: Passed
- ❌ Unit tests: 3 failed, 45 passed
- ❌ Integration tests: 1 failed, 12 passed

## Failed Tests

- test_user_login (auth/test_auth.py)
- test_api_rate_limit (api/test_limits.py)
- test_db_transaction (db/test_transactions.py)
```

**Why Summaries First:**

- Summaries tell you **WHAT** failed
- Logs tell you **HOW** it failed
- Summaries are always small (< 5KB)
- Saves tokens and time

**When to Use:**

- ✅ For EVERY job (even successful ones)
- ✅ Before reading any logs
- ✅ To identify which tests/checks failed

---

### 4. `search_log(folder_name, pattern, context_lines=3, max_matches=50)`

**Purpose:** Grep for specific patterns (case-insensitive)  
**Use Case:** For LARGE logs instead of full read  
**Returns:** Matching lines with context

**Good Patterns:**

```python
# Find errors
search_log('core-ci', 'error')

# Find test failures
search_log('core-ci', 'FAILED')

# Find exceptions
search_log('core-ci', 'exception')

# Find specific test
search_log('core-ci', 'test_user_login')

# Find file references
search_log('core-ci', 'auth/test_auth.py')
```

**Example Output:**

```
# Search Results for 'error' in core-ci

Found 3 matches (showing up to 50)

## Match 1 (Line 234)
```

Running test_user_login...
ERROR: Authentication failed
Expected: 200, Got: 401

```

## Match 2 (Line 567)
...
```

**Parameters:**

- `folder_name`: From job index (e.g., "core-ci")
- `pattern`: Regex pattern (case-insensitive)
- `context_lines`: Lines before/after match (default: 3)
- `max_matches`: Max results to return (default: 50)

**When to Use:**

- ✅ For logs > 200KB
- ✅ To find specific errors/tests
- ✅ To investigate failures found in summary
- ❌ Don't use for logs < 50KB (just read fully)

---

### 5. `read_full_log(folder_name, max_lines=None)`

**Purpose:** Read complete log output  
**Use Case:** For small logs (< 50KB)  
**Returns:** Full log content

**Safety Features:**

- ⚠️ Blocks reading logs > 200KB without limit
- ⚠️ Warns if log is 50-200KB
- ✅ Allows truncation with `max_lines` parameter

**Examples:**

```python
# Small log - safe
log = read_full_log('credential-validation')

# Large log - ERROR
log = read_full_log('core-ci')
# Returns: 🚨 ERROR: Log is 245.7KB - too large!

# Large log - with limit
log = read_full_log('core-ci', max_lines=500)
# Returns: First 500 lines
```

**When to Use:**

- ✅ For logs < 50KB
- ✅ After checking size with `check_log_size()`
- ❌ NEVER for logs > 200KB without limit

---

### 6. `get_log_stats(folder_name)`

**Purpose:** Quick error/warning counts  
**Use Case:** Assess severity without reading  
**Returns:** Pattern counts and recommendation

**Example Output:**

```
# Log Statistics: core-ci

Total lines: 5,432
File size: 245.7KB

## Pattern Counts

- 🔴 Errors: 23
- ⚠️ Warnings: 5
- ❌ Failed: 8
- 💥 Exceptions: 2

🚨 Recommendation: This log contains errors/failures.
Use `search_log('core-ci', 'error')` to investigate.
```

**When to Use:**

- ✅ For medium logs (50-200KB) to decide if deep dive needed
- ✅ To prioritize which jobs need attention
- ✅ To quantify severity
- ❌ Don't use as replacement for reading logs

---

## 📝 Recommended Workflow

### Complete Analysis Pattern

```python
# STEP 1: Get overview
index = read_job_index()
# See: Which jobs ran, their statuses, log sizes

# STEP 2: Read ALL summaries (always small)
for job in all_jobs:
    summary = read_job_summary(job.folder)
    # Know WHAT failed/passed

# STEP 3: Smart log analysis (only for failures)
for job in failed_jobs:
    # Option A: Small log
    if job.log_size < 50KB:
        log = read_full_log(job.folder)
        # Safe to read everything

    # Option B: Medium log
    elif job.log_size < 200KB:
        stats = get_log_stats(job.folder)
        # Check error density

        if stats.error_count > 10:
            errors = search_log(job.folder, 'error', max_matches=20)
            # Focus on errors

    # Option C: Large log
    else:
        # MUST use search, never full read
        errors = search_log(job.folder, 'error')
        failures = search_log(job.folder, 'FAILED')
        # Targeted investigation only
```

---

## ✅ Do's

1. **Always start with index**

   ```python
   index = read_job_index()  # First thing
   ```

2. **Read all summaries first**

   ```python
   for job in jobs:
       summary = read_job_summary(job.folder)
   ```

3. **Check size before reading**

   ```python
   size = check_log_size('core-ci')
   if size < 50KB:
       log = read_full_log('core-ci')
   ```

4. **Use search for large logs**

   ```python
   if log_size > 200KB:
       errors = search_log('core-ci', 'error')
   ```

5. **Provide specific references**

   ```python
   # Good
   "Fix auth/test_auth.py:45 - authentication check failing"

   # Bad
   "Fix authentication"
   ```

---

## ❌ Don'ts

1. **Don't read logs without checking size**

   ```python
   # BAD
   log = read_full_log('core-ci')  # Could be 500KB!

   # GOOD
   size = check_log_size('core-ci')
   if size < 50KB:
       log = read_full_log('core-ci')
   ```

2. **Don't skip summaries**

   ```python
   # BAD
   log = read_full_log('core-ci')  # Without context

   # GOOD
   summary = read_job_summary('core-ci')  # Know what to look for
   errors = search_log('core-ci', 'test_user_login')  # Targeted
   ```

3. **Don't use full read for large logs**

   ```python
   # BAD
   log = read_full_log('core-ci', max_lines=10000)  # Still too much!

   # GOOD
   errors = search_log('core-ci', 'error', max_matches=20)  # Focused
   ```

4. **Don't provide vague recommendations**

   ```python
   # BAD
   "Tests failed, please fix"

   # GOOD
   "3 tests failed in auth/test_auth.py:
   - test_user_login (line 45): Expected 200, got 401
   - Fix: Check JWT token validation logic"
   ```

---

## 💡 Real-World Scenarios

### Scenario 1: All Jobs Pass

```python
# 1. Check index
index = read_job_index()
# Shows: 4 jobs, all ✅ success

# 2. Read summaries (quick)
for job in jobs:
    summary = read_job_summary(job.folder)

# 3. Generate brief report
output = """
## ✅ CI Pipeline Analysis

**Overall Status:** All jobs passed

**Completed Jobs:**
- ✅ credential-validation: All credentials valid
- ✅ core-ci: Format + tests passed
- ✅ test-crewai: All agent tests passed
- ✅ test-build-website: Build successful

**Recommendation:** APPROVE - Ready to merge
"""
```

---

### Scenario 2: One Job Fails (Small Log)

```python
# 1. Index shows credential-validation failed
index = read_job_index()
# credential-validation: ❌ failure, 12.3KB (small)

# 2. Read summary
summary = read_job_summary('credential-validation')
# Shows: "Cloudflare API token invalid"

# 3. Log is small - read fully
log = read_full_log('credential-validation')
# Find: "❌ CLOUDFLARE_API_TOKEN: Token expired"

# 4. Provide specific fix
output = """
## ❌ CI Failure: Credential Validation

**Failed Job:** credential-validation
**Root Cause:** Cloudflare API token expired

**Error:**
```

❌ CLOUDFLARE_API_TOKEN: Token expired (401 Unauthorized)

```

**Fix Required:**
1. Generate new Cloudflare API token at: https://dash.cloudflare.com/profile/api-tokens
2. Update GitHub Secret: CLOUDFLARE_API_TOKEN
3. Re-run workflow

**Recommendation:** REQUEST CHANGES - Update secrets first
"""
```

---

### Scenario 3: Multiple Failures (Large Logs)

```python
# 1. Index shows 2 failures
index = read_job_index()
# core-ci: ❌ failure, 245.7KB (LARGE)
# test-crewai: ❌ failure, 156.2KB (medium)

# 2. Read summaries
core_summary = read_job_summary('core-ci')
# Shows: "3 tests failed"

crewai_summary = read_job_summary('test-crewai')
# Shows: "1 integration test failed"

# 3. Core CI: Large log - use search
core_errors = search_log('core-ci', 'FAILED', max_matches=10)
# Find specific test failures

core_test_login = search_log('core-ci', 'test_user_login', context_lines=5)
# Get details on first failure

# 4. Test CrewAI: Medium log - check stats
crewai_stats = get_log_stats('test-crewai')
# 🔴 Errors: 5

crewai_errors = search_log('test-crewai', 'error', max_matches=10)
# Get error details

# 5. Generate detailed report
output = """
## ❌ CI Pipeline Analysis

**Overall Status:** 2 jobs failed

### ❌ Failed: core-ci

**Root Cause:** 3 unit tests failing in authentication module

**Failed Tests:**
1. `test_user_login` (auth/test_auth.py:45)
   - Expected: 200 OK
   - Got: 401 Unauthorized
   - Fix: Check JWT token validation

2. `test_password_reset` (auth/test_auth.py:89)
   - Email not sent
   - Fix: Check SMTP configuration

3. `test_session_timeout` (auth/test_auth.py:134)
   - Session persisted after timeout
   - Fix: Review session cleanup logic

### ❌ Failed: test-crewai

**Root Cause:** Mock PR test failing

**Error:** `test_mock_pr_analysis` (line 67)
- Tool call to read_pr_diff timed out
- Fix: Increase timeout or mock response

**Recommendation:** REQUEST CHANGES
- Priority: Fix auth tests (core functionality)
- Can merge: After auth tests pass
"""
```

---

## 🔗 Related Documentation

- [Sprint W08 board](../../docs/project/kanban/sprint-2026-w08-crewai-review-hardening-and-memory.md)
- [PR-00000001 record](../../docs/project/pr/pr-00000001-agentic-docs-and-monorepo-modernization.md)
- [Issue-00000003 record](../../docs/project/issues/issue-00000003-local-review-context-pack-and-resilience.md)

---

**Last Updated:** 2026-01-30  
**Maintained By:** CI/CD Team
