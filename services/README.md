# Services

> Long-running backend services, workers, and internal service processes.

> **For AI agents:** start at [../AGENTS.md](../AGENTS.md) before creating or modifying service code.

---

## 📋 Purpose

Use `services/` for backend components that are not user-facing apps but still run continuously or on schedules.

Examples:

- event consumers
- job workers
- webhook processors
- internal RPC/HTTP services

---

## 📂 Organization

```text
services/
├── README.md
└── <service-name>/
```

---

## 🔗 References

- [apps/](../apps/) - deployable products
- [packages/](../packages/) - shared libraries
- [data/sql/](../data/sql/) - schema and migration assets
