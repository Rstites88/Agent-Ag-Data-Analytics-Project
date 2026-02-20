# Applications

> Deployable products and user-facing apps (web, API, workers, CLI frontends).

> **For AI agents:** start at [../AGENTS.md](../AGENTS.md) before creating or modifying application code.

---

## 📋 Purpose

Use `apps/` for independently deployable products.

Examples:

- **Web app** (`apps/web/`) - TypeScript/React/Next/Vite frontend
- **API app** (`apps/api/`) - backend API service (Node/Python/Go/etc.)
- **Mobile app** (`apps/mobile/`) - React Native/Flutter client
- **CLI app** (`apps/cli/`) - user-facing command-line product

---

## 📂 Organization

```text
apps/
├── README.md
├── web/
├── api/
└── <app-name>/
```

Each app should own its runtime config, dependencies, and local scripts.

---

## 🔗 References

- [services/](../services/) - long-running backend services and workers
- [packages/](../packages/) - shared libraries for reuse across apps/services
- [data/sql/](../data/sql/) - SQL migrations and schemas
- [src/](../src/) - language-focused source area (Python-first workspace)
