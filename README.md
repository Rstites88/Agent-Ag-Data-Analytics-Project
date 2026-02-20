# agent-project: AGENTS.md-First Agentic Coding Template

> **A production-ready template for teams shipping with AI coding agents.**

`agent-project` is a practical starter template built around an `AGENTS.md` entrypoint and an "everything as code" workflow. Standards, plans, PR records, issues, boards, and review policies live in the repository as versioned markdown files—accessible to both humans and AI agents.

**The philosophy is simple:** Point any agent at `AGENTS.md`, and it knows exactly how to work in your repo.

---

## 🏗️ System Architecture

_The template provides a complete development workflow from local development through CI/CD deployment, with AI-powered code reviews at every stage:_

```mermaid
flowchart TB
accTitle: Agent Project System Architecture
accDescr: Complete architecture showing local development, CI/CD pipelines, agent workflows, and deployment paths.

subgraph LocalDevelopment["💻 Local Development Environment"]
direction LR
VSCode["📝 VS Code<br/>IDE + Terminal"]
AgentTools["🤖 Agent Tools<br/>OpenCode / Claude Code / Roo Code / Copilot"]
LocalCI["⚡ Local CI Runner<br/>./scripts/ci-local.sh"]
Memory["🧠 Review Memory<br/>./scripts/memory.sh"]

VSCode --> AgentTools --> LocalCI --> Memory
end

subgraph SourceControl["📦 Source Control & Standards"]
    direction LR
    AgentsMD["📋 AGENTS.md<br/>Entry Point"]
    Standards["📚 Agentic Standards<br/>Style Guides & Templates"]
    ADRs["🏛️ Architecture Decisions<br/>agentic/adr/"]
    Tracking["📊 Project Tracking<br/>docs/project/"]

    AgentsMD --> Standards
    Standards --> ADRs
    Standards --> Tracking
end

subgraph CI_CD["🔄 CI/CD Pipeline"]
direction TB
subgraph Validation["✅ Validation Phase"]
direction LR
Lint["📝 Lint & Format"]
TypeCheck["🔍 Type Check"]
Test["🧪 Tests"]
Lint --> TypeCheck --> Test
end

subgraph Deploy["🚀 Deploy Phase"]
  direction LR
  Build["📦 Build"] --> Cloudflare["☁️ Cloudflare Pages"]
end

subgraph Review["👥 Review Phase"]
direction LR
CrewAI["🤖 CrewAI Review"]
Quick["⚡ Quick Mode"]
Full["🔬 Full Mode"]
Complete["🎯 Complete-Full Mode"]
CrewAI --> Quick
CrewAI --> Full
CrewAI --> Complete
end

Validation --> Deploy
Deploy --> Review
end

subgraph GitHubPlatform["☁️ GitHub Platform"]
Actions["🔷 GitHub Actions<br/>CI/CD Workflows"]
Secrets["🔐 Key Management<br/>Repository Secrets"]
PRs["👥 PRs & Reviews<br/>Collaboration Hub"]
end

LocalDevelopment --> SourceControl
SourceControl --> CI_CD
CI_CD --> Cloudflare
CI_CD --> GitHubPlatform

classDef local fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e3a5f
classDef source fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#78350f
classDef cicd fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d
classDef github fill:#fce7f3,stroke:#db2777,stroke-width:2px,color:#831843
classDef phase fill:#f3f4f6,stroke:#6b7280,stroke-width:2px,color:#374151

class LocalDevelopment,VSCode,AgentTools,LocalCI,Memory local
class SourceControl,AgentsMD,Standards,ADRs,Tracking source
class CI_CD,Validation,Review,Deploy,Build,Cloudflare cicd
class GitHubPlatform,Actions,Secrets,PRs github
class Lint,TypeCheck,Test,CrewAI,Quick,Full,Complete phase
```

---

## 🚀 Quickstart

Get up and running in minutes:

```bash
# Clone the template
git clone https://github.com/borealBytes/agent-project.git
cd agent-project

# Install dependencies
pnpm install

# Run local CI to validate everything works
./scripts/ci-local.sh
```

**Agent review modes:**

```bash
# Quick review - fast triage for daily iteration
./scripts/ci-local.sh --review

# Full review - deeper analysis with specialists
./scripts/ci-local.sh --full-review --step review

# Complete-full review - maximum coverage for critical changes
./scripts/ci-local.sh --complete-full-review --step review
```

---

## 🎯 Who This Is For

This template is designed for teams using any AI coding agent:

| Tool                            | How It Works                                                                   |
| ------------------------------- | ------------------------------------------------------------------------------ |
| **OpenCode**                    | Reads `AGENTS.md` at startup, follows instructions for PRs, issues, and kanban |
| **Claude Code**                 | Ingests repo rules from `AGENTS.md`, applies conventions automatically         |
| **Roo Code**                    | Uses `AGENTS.md` as system context for all operations                          |
| **GitHub Copilot**              | References `AGENTS.md` for code style and conventions                          |
| **Perplexity/Other Web Agents** | Point to `AGENTS.md` URL as entrypoint                                         |

**Perfect for teams that want:**

- ✅ Auditable, repo-native process standards (not UI-only metadata)
- ✅ AI agents that follow the same rules as humans
- ✅ Versioned project tracking in git
- ✅ Local-first CI with optional GitHub Actions integration

---

## 📋 Everything as Code

This template treats process records as first-class code artifacts:

```mermaid
flowchart TB
accTitle: Everything as Code Philosophy
accDescr: All project management data lives in versioned markdown files, not external tools.

subgraph ADRs["🏛️ Decisions"]
direction LR
A1["ADR-001-architecture.md"]
A2["ADR-002-standards.md"]
end

subgraph Kanban["📊 Kanban Boards"]
direction LR
K1["sprint-w07.md"]
K2["release-v2.0.md"]
end

subgraph Issues["🐛 Issues"]
direction LR
I1["issue-00000001-bug.md"]
I2["issue-00000002-feature.md"]
end

subgraph PRs["📋 Pull Requests"]
direction LR
PR1["pr-00000001-feature.md"]
PR2["pr-00000002-fix.md"]
end

ADRs --> Kanban
Kanban --> Issues
Issues --> PRs

classDef file fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e3a5f
class PR1,PR2,I1,I2,K1,K2,A1,A2 file
```

**Why this matters:**

- **Portable:** Your project history travels with the repo
- **Versioned:** Git tracks every change with attribution
- **Accessible:** Both humans and agents read the same files
- **Offline:** No dependency on external platforms

---

## 🔍 Agent Workflow

_How agents work with this template from task to completion:_

```mermaid
sequenceDiagram
accTitle: Agent Task Completion Workflow
accDescr: Sequence showing how an agent processes a task from intake through completion.

actor Human
participant Agent as AI Agent
participant AGENTS as AGENTS.md
participant Instructions as agentic/instructions.md
participant Standards as Style Guides
participant Work as Implementation
participant CI as Local CI
participant PR as PR Record

Human->>Agent: Submit task
Agent->>AGENTS: Read entry point
AGENTS->>Instructions: Load workflow
Instructions->>Standards: Load style guides
Standards->>Agent: Return conventions

Agent->>Work: Create branch
Agent->>Work: Write code
Agent->>PR: Update PR record
Agent->>CI: Run local CI
CI-->>Agent: Pass/Fail

alt CI Pass
    Agent->>PR: Mark ready for review
    PR-->>Human: PR record updated
else CI Fail
    Agent->>Work: Fix issues
    Agent->>CI: Re-run CI
end

Human->>Agent: Approve & merge
Agent->>PR: Update status to done
```

---

## ⚡ Local CI Pipeline

_The local CI runner validates code before it reaches GitHub:_

```mermaid
flowchart TB
accTitle: Local CI Pipeline Stages
accDescr: Flow showing the stages of local CI validation.

Start([Start]) --> Phase1

subgraph Phase1["Phase 1: Validation"]
direction LR
Lint["📝 Lint & Format"]
TypeCheck["🔍 Type Check"]
Lint --> TypeCheck
end

Phase1 --> Phase2

subgraph Phase2["Phase 2: Testing"]
direction LR
Test["🧪 Run Tests"]
Build["📦 Build Check"]
Test --> Build
end

Phase2 --> Phase3

subgraph Phase3["Phase 3: Review"]
direction LR
Review["🤖 CrewAI Review"]
Quick["⚡ Quick Mode"]
Full["🔬 Full Mode"]
Complete["🎯 Complete-Full"]

Review --> Quick
Review --> Full
Review --> Complete
end

Phase3 --> End([End])

classDef phase fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e3a5f
classDef review fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d
class Phase1,Phase2,Phase3 phase
class Review,Quick,Full,Complete review
```

### Review Modes Explained

| Mode              | Command                                                      | What It Does                     | When to Use            |
| ----------------- | ------------------------------------------------------------ | -------------------------------- | ---------------------- |
| **Quick**         | `./scripts/ci-local.sh --review`                             | Fast triage-oriented review      | Day-to-day iteration   |
| **Full**          | `./scripts/ci-local.sh --full-review --step review`          | Deeper synthesis + specialists   | Risky or broad changes |
| **Complete-Full** | `./scripts/ci-local.sh --complete-full-review --step review` | All specialists, full-repo scope | Pre-merge hardening    |

**Layered assurance:** Speed when you need flow, depth when you need confidence, complete coverage when touching multiple risk domains.

---

## 🏛️ Project Structure

_The monorepo layout supports polyglot development:_

```mermaid
graph TD
accTitle: Repository Structure
accDescr: Visual overview of the repository directory structure.

root["📁 agent-project/"] --> agentic["📁 agentic/<br/>Agent Framework"]
root --> crewai["📁 .crewai/<br/>Review System"]
root --> apps["📁 apps/<br/>Deployable Apps"]
root --> services["📁 services/<br/>Background Services"]
root --> packages["📁 packages/<br/>Shared Libraries"]
root --> data["📁 data/sql/<br/>Database Schemas"]
root --> docs["📁 docs/<br/>Documentation"]
root --> scripts["📁 scripts/<br/>CI Scripts"]

agentic --> agf1["instructions.md"]
agentic --> agf2["AGENTS.md"]
agentic --> agf3["adr/"]
agentic --> agf4["markdown_templates/"]

crewai --> crw1["crews/"]
crewai --> crw2["config/"]
crewai --> crw3["adr/"]

apps --> web["web/<br/>Next.js Site"]
apps --> api["api/<br/>API Server"]

docs --> pr["project/pr/<br/>PR Records"]
docs --> issues["project/issues/<br/>Issue Records"]
docs --> kanban["project/kanban/<br/>Kanban Boards"]

classDef root fill:#fee2e2,stroke:#dc2626,stroke-width:3px,color:#7f1d1d
classDef framework fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e3a5f
classDef workspace fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d
classDef docs fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#78350f

class root root
class agentic,crewai framework
class apps,services,packages,data workspace
class docs,scripts docs
```

### Key Directories

| Directory       | Purpose                       | Key Files                                    |
| --------------- | ----------------------------- | -------------------------------------------- |
| `agentic/`      | Agent framework and standards | `AGENTS.md`, `instructions.md`, style guides |
| `.crewai/`      | CrewAI review system          | Agent definitions, task contracts, crews     |
| `apps/`         | Deployable applications       | `web/`, `api/`, `cli/`                       |
| `services/`     | Background services/workers   | Long-running processes                       |
| `packages/`     | Shared libraries/modules      | Reusable code                                |
| `data/sql/`     | Database schemas/migrations   | SQL files                                    |
| `docs/project/` | Project tracking              | PRs, issues, kanban boards                   |
| `scripts/`      | CI and utility scripts        | `ci-local.sh`, `memory.sh`                   |

---

## 🔐 Key Management

**GitHub Actions secrets are cleanly managed:**

```mermaid
flowchart TB
accTitle: GitHub Secrets Management
accDescr: How secrets flow from GitHub to workflows and applications.

subgraph GitHub["☁️ GitHub Platform"]
    Secrets["🔐 Repository Secrets<br/>Settings > Secrets"]
    Environments["🌍 Environment Secrets<br/>Production / Staging"]
end

subgraph Workflows["⚙️ GitHub Workflows"]
    CI["🔄 CI Workflow"]
    Deploy["🚀 Deploy Workflow"]
    Review["👥 Review Workflow"]
end

subgraph Runtime["🏃 Runtime"]
    CrewAI["🤖 CrewAI Review<br/>API Keys"]
    DeployTarget["📦 Deployment Target<br/>Vercel / AWS / etc"]
end

Secrets --> Workflows
Environments --> Workflows
CI --> Runtime
Deploy --> Runtime
Review --> Runtime

classDef secrets fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#7f1d1d
classDef workflow fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e3a5f
classDef runtime fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d

class Secrets,Environments secrets
class CI,Deploy,Review workflow
class CrewAI,DeployTarget runtime
```

**Required Secrets:**

- `OPENROUTER_API_KEY` - For CrewAI reviews (or `NVIDIA_API_KEY` for NVIDIA NIM)
- Deployment tokens for your hosting platform (Vercel, AWS, etc.)

---

## 🎓 Usage Workflows

### Workflow 1: Web-Based Agent

Perfect for Perplexity, Claude web, or other hosted agents:

1. **Point the agent to `AGENTS.md`** as the entrypoint
2. **Connect the repository** (or provide diffs)
3. **Work in branches** with PR records in `docs/project/pr/`
4. **Track progress** in kanban boards

### Workflow 2: Local IDE Agent

For OpenCode, Roo Code, Claude Code, Copilot:

1. **Clone locally** and open in your IDE
2. **Agent reads `AGENTS.md`** automatically
3. **Run local CI** before committing
4. **Push to GitHub** for team review

### Workflow 3: Hybrid Mode

Best of both worlds:

1. **Local development** with agent assistance
2. **Local CI validation** before push
3. **GitHub Actions** for team CI/CD
4. **CrewAI review** for quality gates

---

## 🛠️ Customization

### Adding Specialists

Specialists are configured in `.crewai/` and can be adapted to your domain:

```yaml
# .crewai/config/agents.yaml
security_specialist:
  role: Security Specialist
  goal: Identify security vulnerabilities
  backstory: Expert in application security...
```

### Custom Standards

Add organization-specific context:

```markdown
# agentic/custom-instructions.md

## Our Team Standards

- We use tabs, not spaces
- Maximum line length: 100 characters
- Required reviewers: 2 for all PRs
```

---

## 📖 Entry Points

Start here based on what you're doing:

| If you want to...            | Start here                                                   |
| ---------------------------- | ------------------------------------------------------------ |
| **Use an agent**             | [`AGENTS.md`](AGENTS.md)                                     |
| **Understand the framework** | [`agentic/README.md`](agentic/README.md)                     |
| **Customize CI/CD**          | [`.github/workflows/README.md`](.github/workflows/README.md) |
| **Add specialists**          | [`.crewai/README.md`](.crewai/README.md)                     |
| **Create a PR**              | [`docs/project/pr/`](docs/project/pr/)                       |
| **Track work**               | [`docs/project/kanban/`](docs/project/kanban/)               |
| **Document decisions**       | [`agentic/adr/`](agentic/adr/)                               |
| **Run scripts**              | [`scripts/README.md`](scripts/README.md)                     |

---

## 📚 Additional Resources

- **License:** Apache-2.0 (see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE))
- **Author:** Clayton Young ([@borealBytes](https://github.com/borealBytes)), Superior Byte Works, LLC
- **Contributing:** See [`CONTRIBUTING.md`](CONTRIBUTING.md)

---

<p align="center">
  <strong>Built for agents. Designed for humans. Versioned in git.</strong>
</p>
