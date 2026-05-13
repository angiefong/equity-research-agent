# equity-research-agent

Multi-agent equity research pipeline (LangGraph + LangChain) with verifiable outputs and measurable safety properties.

## Working conventions

- **Eval-driven changes.** Behavior changes get a measured eval. Lifts are logged in `README.md` under the security-posture section and to DagsHub MLflow.
- **ADR-driven decisions.** Rejected refactors and architecture decisions are recorded under `docs/adr/` so they don't get re-suggested. Current ADRs: 0001–0004.
- **Plan docs stay uncommitted.** Working plans under `docs/superpowers/plans/` are intentionally untracked. The active workstream is `docs/superpowers/plans/2026-05-12-adversarial-mitigation.md`.

## Key commands

- `pytest tests/ -q` — full test suite (currently 148 tests)
- `python -m backend.evals.run --quick` — regular eval (10 cases)
- `python -m backend.evals.run --adversarial` — prompt-injection eval (10 cases; baseline 50% absorption)
- `python -m backend.run` — run the full agent pipeline

## Layout

- `backend/` — LangGraph agent pipeline and tools
- `backend/evals/` — eval harness (regular + adversarial)
- `frontend-next/` — Next.js UI
- `docs/adr/` — architecture decision records
- `runtime_data/eval_runs/` — eval run outputs (per-case JSONs)
