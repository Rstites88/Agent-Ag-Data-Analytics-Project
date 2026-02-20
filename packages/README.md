# Packages

> Shared libraries, SDKs, and reusable modules across apps and services.

> **For AI agents:** start at [../AGENTS.md](../AGENTS.md) before creating or modifying shared packages.

---

## 📋 Purpose

Use `packages/` for code reused by multiple runtimes.

Examples:

- TypeScript utility package
- shared API client
- design system tokens/components
- Python shared toolkit

---

## 📂 Organization

```text
packages/
├── README.md
└── <package-name>/
```

Keep package boundaries explicit to avoid hidden cross-project coupling.

---

## 🔗 References

- [apps/](../apps/) - consumer applications
- [services/](../services/) - backend consumers
- [src/](../src/) - Python-focused source workspace
