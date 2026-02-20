# SQL Workspace

> SQL schemas, migrations, and database bootstrap assets.

> **For AI agents:** start at [../../AGENTS.md](../../AGENTS.md) before modifying schema or migration files.

---

## 📋 Purpose

Use `data/sql/` for relational database artifacts that support apps and services.

Include:

- schema definitions
- migrations
- seed scripts
- rollback scripts

---

## 📂 Organization

```text
data/
└── sql/
    ├── README.md
    ├── migrations/
    ├── seeds/
    └── schema/
```

---

## 🔗 References

- [apps/](../../apps/) - application code using these databases
- [services/](../../services/) - workers/services using these databases
- [agentic/idempotent_design_patterns.md](../../agentic/idempotent_design_patterns.md) - idempotent execution standards
