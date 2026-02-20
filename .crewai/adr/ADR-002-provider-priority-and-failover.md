# ADR-002: LLM Provider Priority and Failover Behavior

| Field               | Value                                |
| ------------------- | ------------------------------------ |
| **Status**          | Accepted                             |
| **Date**            | 2026-02-14                           |
| **Decision makers** | Repo maintainers                     |
| **Consulted**       | AI agents (CrewAI reliability work)  |
| **Informed**        | Contributors running local/CI review |

---

## 📋 Context

CrewAI review runs need predictable behavior when a provider times out or lacks credit. The subsystem currently includes explicit provider resolution and fallback behavior in both orchestration code and local runner scripts.

---

## 🎯 Decision

Use the following provider behavior for local CrewAI review execution:

1. OpenRouter (`OPENROUTER_API_KEY`) default path
2. NVIDIA NIM (`NVIDIA_API_KEY` or `NVIDIA_NIM_API_KEY`) only when explicitly opted in

Operational rules:

- Local runner defaults to OpenRouter for speed/cost stability.
- NVIDIA is opt-in via `--nvidia-nim` (sets `FORCE_NVIDIA=true` for that run).
- Default local model key is ultra-cheap `gemini-flash-lite` (`openrouter/google/gemini-2.5-flash-lite`).
- If NVIDIA is enabled and fails during quick-review, disable NVIDIA for the remaining passes and continue on OpenRouter.
- Full/specialist runs always produce required workspace JSON outputs by synthesizing structured files when crews return non-persisted text.

---

## ⚡ Consequences

### Positive

- Deterministic local runtime and faster baseline feedback loops.
- Lower default inference cost while keeping tool-calling compatible models.
- Single-failure NVIDIA fallback behavior avoids repeated per-pass retries.
- Final report pipeline remains readable because expected JSON artifacts are always present for summary synthesis.

### Negative

- Slightly more local CLI complexity (`--nvidia-nim` opt-in path).
- Synthesized structured outputs can contain less detail than ideal when an upstream crew does not emit strict JSON.

---

## 📋 Evidence in code

- `scripts/ci-local.sh` (`--nvidia-nim`, default provider resolution, `FORCE_NVIDIA` export)
- `.crewai/utils/model_config.py` (OpenRouter-default model key and opt-in NVIDIA resolution)
- `.crewai/main.py` (single-failure NVIDIA disable in multipass quick-review; synthesized `full_review.json` and specialist outputs)

---

## 🔗 References

- [CrewAI model config](../utils/model_config.py)
- [Local CI review runner](../../scripts/ci-local.sh)

---

_Last updated: 2026-02-14_
