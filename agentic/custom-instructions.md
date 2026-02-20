# Project-Specific Rules

> **This file is a template.** Copy it and fill in the sections below with your project's specific rules, conventions, and structure. For universal standards that apply to any project, see [contribute_standards.md](contribute_standards.md).
>
> **For AI agents:** This file contains rules specific to THIS project. It overrides general guidance when there's a conflict. Read [contribute_standards.md](contribute_standards.md) first for universal rules, then this file for project-specific additions.

**Template by:** Clayton Young ([@borealBytes](https://github.com/borealBytes)), Superior Byte Works, LLC

---

## 📋 Project overview

<!-- CUSTOMIZE: Replace the placeholder content below with your actual project details -->

| Field                 | Value                                                            |
| --------------------- | ---------------------------------------------------------------- |
| **Project name**      | `{project-name}`                                                 |
| **Description**       | Brief one-line description of what this project does             |
| **Tech stack**        | `{language}`, `{framework}`, `{database}`, `{deployment-target}` |
| **Package manager**   | `{package-manager}` (npm, pnpm, yarn, pip, cargo, etc.)          |
| **Repository type**   | Mono-repo / single-package / workspace                           |
| **Deployment target** | `{platform}` (Vercel, AWS, Cloudflare, bare metal, etc.)         |

### Architecture summary

<!-- CUSTOMIZE: Describe how your project is structured at a high level. What are the main components? How do they interact? Consider adding a Mermaid diagram — see mermaid_style_guide.md -->

```text
{project-name}/
├── src/                    # Application source code
├── tests/                  # Test suite
├── docs/                   # Documentation + Everything is Code
├── agentic/                # Agent instructions (this framework)
└── ...
```

---

## 📚 Repository structure

<!-- CUSTOMIZE: Replace the tree below with your actual project structure. Include every directory that agents need to know about. -->

```text
{project-name}/
├── apps/                          # Deployed applications (if mono-repo)
│   └── {app-name}/               # Primary application
├── packages/                      # Shared packages (if mono-repo)
│   └── {shared-package}/         # Shared utilities
├── src/                           # Source code (if single-package)
│   ├── index.ts                  # Application entry point
│   ├── ...
│   └── types.ts                  # Type definitions
├── tests/                         # Test suite
│   ├── unit/
│   └── integration/
├── docs/                          # Everything is Code project management
│   ├── pr/                       # Pull request records
│   ├── issues/                   # Issue records
│   └── kanban/                   # Sprint boards
├── agentic/                       # Agent instructions (this framework)
├── .github/workflows/             # CI/CD pipelines
├── package.json                   # Dependencies and scripts
└── README.md                      # Project overview
```

---

## ✅ Scoped Conventional Commits

<!-- CUSTOMIZE: Define the scopes specific to your project. These appear in commit messages: feat(scope): description -->

For this project, use scope prefixes based on the area affected:

### Examples

```text
feat({app}): implement user authentication
fix({api}): handle rate limit errors gracefully
docs: add deployment guide
chore(deps): bump typescript to 5.7
test({core}): add integration tests for payment flow
refactor({ui}): simplify form validation logic
```

### Scope rules

<!-- CUSTOMIZE: Replace these with your actual project scopes -->

| Scope          | When to use                                  |
| -------------- | -------------------------------------------- |
| `{app}`        | Changes to the main application              |
| `{api}`        | API endpoints, routing, middleware           |
| `{ui}`         | Frontend components, styling, layouts        |
| `{core}`       | Core business logic, shared utilities        |
| `{db}`         | Database schema, migrations, queries         |
| `{auth}`       | Authentication, authorization, permissions   |
| _(omit scope)_ | Root config, docs, CI/CD, dependency updates |

---

## 🎯 Development workflow

<!-- CUSTOMIZE: Replace the commands below with your actual project commands -->

### Common tasks

#### Start local development

```bash
# Install dependencies
{package-manager} install

# Start dev server
{package-manager} run dev

# Run in specific workspace (if mono-repo)
{package-manager} --filter {app-name} dev
```

#### Create a feature branch

```bash
git checkout -b feat/{feature-name}

# Make changes in the relevant directory

# Commit with scope
git commit -m "feat({scope}): implement {feature-description}"

# Push and open PR
git push origin feat/{feature-name}
```

---

## 📚 Source of truth hierarchy

When working on this repo, check for guidance in this order:

1. **This file** (`custom-instructions.md`) — project-specific rules (most specific)
2. **`agentic_coding.md`** — agent autonomy boundaries
3. **`contribute_standards.md`** — universal coding and PR standards
4. **`markdown_style_guide.md`** / **`mermaid_style_guide.md`** — documentation standards
5. **`adr/`** — architecture decision records (rationale for past decisions)

If you find **conflicting guidance**, stop and ask for confirmation.

---

## 🔐 Environment and secrets

<!-- CUSTOMIZE: Replace the example variables below with your actual environment configuration -->

### `.env.example`

```bash
# Authentication
AUTH_SECRET=your-secret-here-minimum-32-chars
OAUTH_CLIENT_ID=get-from-provider-console

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/{project-name}

# Third-party APIs
API_KEY=your-api-key-here
WEBHOOK_SECRET=your-webhook-secret

# Deployment
DEPLOY_TOKEN=get-from-deployment-platform
```

### Local development

1. Copy `.env.example` to `.env.local`
2. Fill in actual values (get from team lead or secrets manager)
3. **Never** commit `.env.local` or other `.env.*` files
4. `.gitignore` already excludes `.env*` files

### CI/CD and production

- Secrets stored in CI/CD platform (GitHub Secrets, etc.)
- CI injects secrets into runner environment
- Agent **cannot** read or write secrets (humans only)

---

## 🔄 PR guidelines

### PR title format

Use Scoped Conventional Commits format in PR titles:

```text
feat({scope}): implement {feature}
fix({scope}): correct {bug-description}
docs: add {documentation-topic}
chore: update dependencies
```

### PR documentation

Follow the [Everything is Code](markdown_style_guide.md#-everything-is-code) philosophy:

1. Create a PR record file in `docs/project/pr/pr-NNNNNNNN-short-description.md`
2. Use the [PR template](markdown_templates/pull_request.md)
3. The GitHub PR description contains only the full branch URL to the file — it does **not** duplicate content
   - Format: `https://github.com/<org>/<repo>/blob/<branch>/docs/project/pr/pr-NNNNNNNN-short-description.md`
4. The file is the single source of truth

See [contribute_standards.md](contribute_standards.md) for full PR standards.

---

## 🧪 Testing and CI/CD

<!-- CUSTOMIZE: Replace the commands below with your actual test/build commands -->

### Local testing before push

```bash
# Install dependencies
{package-manager} install

# Preferred in repos that provide it: single local CI entrypoint
./scripts/ci-local.sh

# Run all tests
{package-manager} test

# Type check (if applicable)
{package-manager} run type-check

# Lint code
{package-manager} run lint

# Format code
{package-manager} run format

# Build
{package-manager} run build
```

If `./scripts/ci-local.sh` exists, treat it as the default pre-commit/pre-push validation command unless explicitly told to skip it.

If the environment cannot run local CI (for example, missing local secrets/tools in hosted agent environments), document the skip reason in PR/issue records and run all available checks.

### CI pipeline (automatic on every push)

1. **Format and lint** — auto-fix if needed, commit back
2. **Test** — run test suite
3. **Build** — verify compilation succeeds
4. **Deploy** — if configured, deploy to staging on merge

See `.github/workflows/` for workflow definitions.

---

## 🚨 Project-specific constraints

<!-- CUSTOMIZE: Add constraints specific to your project. Below are common examples — delete the ones that don't apply and add your own. -->

### Critical file protection

<!-- CUSTOMIZE: List files that should never be modified without explicit human approval -->

- **Never modify** `{critical-config-file}` without explicit human approval
- **Never modify** core identity or safety constraints
- **Never modify** production deployment configs without review

### Sensitive operations

<!-- CUSTOMIZE: List operations that require extra scrutiny in your project -->

- Changes to payment processing or financial logic require human approval
- Changes to PII handling or data privacy code require human approval
- Changes to audit-critical paths require human approval

### Deployment awareness

<!-- CUSTOMIZE: Add deployment-specific constraints -->

- This project deploys to `{platform}`
- Changes to `{deployment-config}` affect production
- Always test locally before submitting infrastructure changes

---

## 📝 Documentation standards

> 📌 **All documentation and diagrams in this project MUST follow the style guides.** These are not optional.

| Resource                | When to use                              | Link                                               |
| ----------------------- | ---------------------------------------- | -------------------------------------------------- |
| **Markdown formatting** | Every `.md` file you create or edit      | [markdown_style_guide.md](markdown_style_guide.md) |
| **Mermaid diagrams**    | Every diagram you create                 | [mermaid_style_guide.md](mermaid_style_guide.md)   |
| **Document templates**  | When creating PRs, issues, ADRs, reports | [markdown_templates/](markdown_templates/)         |
| **Diagram type guides** | When creating a specific diagram type    | [mermaid_diagrams/](mermaid_diagrams/)             |

Key requirements:

- **One emoji per H2 heading** — no emoji on H3/H4
- **Footnote citations** for every external claim with full URL
- **`accTitle` + `accDescr`** on every Mermaid diagram
- **`classDef` color classes** for Mermaid styling — no inline `style`, no `%%{init}`
- **Everything is Code** — PRs, issues, and boards are markdown files in `docs/`

---

## 🔗 References

- **Universal standards** → [contribute_standards.md](contribute_standards.md)
- **Agent autonomy** → [agentic_coding.md](agentic_coding.md)
- **Markdown formatting** → [markdown_style_guide.md](markdown_style_guide.md)
- **Mermaid diagrams** → [mermaid_style_guide.md](mermaid_style_guide.md)
- **Architecture decisions** → [adr/](adr/) (global) + subsystem `adr/` directories (for example `.crewai/adr/`)

---

**Last updated:** 2026-02-13
**Status:** Template — customize per project
