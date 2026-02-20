# Notebooks

> Jupyter notebooks for exploration, prototyping, and interactive development.

> **For AI agents:** start at [../AGENTS.md](../AGENTS.md) before creating or modifying notebook artifacts.

---

## 📋 Purpose

This directory holds Jupyter notebooks (`.ipynb`) used for:

- **Data exploration** — inspecting datasets, APIs, and system outputs
- **Prototyping** — testing ideas before moving them into `src/`
- **Documentation** — interactive walkthroughs and tutorials
- **Analysis** — CrewAI output analysis, CI metrics, and review trends

---

## 📂 Organization

```text
notebooks/
├── README.md              # This file
├── exploration/           # Quick experiments and data inspection
├── prototypes/            # Pre-production concept validation
└── analysis/              # Metrics, trends, and review analysis
```

Create subdirectories as needed. Name notebooks descriptively:

```text
✅ 2026-02-13-crewai-output-analysis.ipynb
✅ auth-flow-prototype.ipynb
❌ Untitled1.ipynb
❌ test.ipynb
```

---

## 🔧 Setup

### Prerequisites

```bash
# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows

# Install Jupyter
pip install jupyter jupyterlab

# Start Jupyter
jupyter lab
```

### Kernel management

If the project uses a specific virtual environment, register it as a kernel:

```bash
pip install ipykernel
python -m ipykernel install --user --name opencode --display-name "opencode"
```

---

## 🚨 Rules

1. **Never commit secrets** — use environment variables, not hardcoded keys
2. **Clear outputs before committing** — large outputs bloat git history
3. **Keep notebooks focused** — one notebook per investigation or prototype
4. **Graduate to `src/`** — when a notebook becomes production code, move it to `src/`
5. **`.ipynb_checkpoints/` is gitignored** — Jupyter's autosave directory is excluded automatically

---

## 🔗 References

- [src/](../src/) — Production Python code (notebooks graduate here)
- [.crewai/](../.crewai/) — CrewAI review system
- [AGENTS.md](../AGENTS.md) — Repo-wide agent entrypoint and completion requirements
- [agentic/](../agentic/) — Agent instructions and standards

---

_Part of the [Boreal Bytes GitHub org](https://github.com/borealBytes)._
