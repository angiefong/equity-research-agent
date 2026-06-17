# Equity Research Agent

[![Evals](https://img.shields.io/badge/evals-DagsHub-blue)](https://dagshub.com/fwtangie/equity-research-agent.mlflow)

A verifiable multi-agent equity research system that produces source-backed memos with bull/bear debate, contradiction detection, and thesis-drift tracking. Every factual claim traces back to a specific evidence span; quantitative errors caught by an LLM judge get fixed in the verification loop, not in the final memo.

## What makes this different

- **Eval-driven.** Every change is measured against an 8-metric LLM-as-judge rubric tracked on DagsHub/MLflow. The lift log below records each scored iteration.
- **Verifiable citations.** Every factual claim cites a specific evidence span (e.g. `sec:AAPL-10K-2024:revenue`), not a numeric reference. Agents cannot invent sources; citations are validated end-to-end against the evidence list.
- **Reroute on failure.** A verifier agent inspects bull/bear claims against the evidence; high-severity issues trigger a targeted re-fetch from the source agent (capped at 2 attempts) before the memo is assembled.
- **Same-model isolation.** Each prompt change is evaluated against the same base model and same eval set, so lift figures reflect prompt engineering — not model upgrades.

## Lift log

- **2026-04-27** — first baseline on `--quick` set (AAPL, RIVN): avg overall **2.21/5**. Judge surfaced concrete analytical errors — inverted P/E comparison in AAPL bull; negative EV/EBITDA misused as bullish in RIVN bull. ([run](https://dagshub.com/fwtangie/equity-research-agent.mlflow/#/experiments/0/runs/7294cee0cdd54203bfec82eb2b73ca61))
- **2026-05-09** — `feature/sharper-debate` merged. Four targeted prompt fixes driven by judge feedback: arithmetic-sanity rule, source_ref-based citation system, moderator data-recency + numeric-format consistency rules. **Same-model isolation: 2.21 → 3.29 (+1.08, ~49% lift)**, AAPL 2.00 → 3.57, RIVN 2.43 → 3.00. Logical consistency 4/4, synthesis quality 4/4 across both tickers. ([run](https://dagshub.com/fwtangie/equity-research-agent.mlflow/#/experiments/0/runs/dab1aa38d5d54b5bab2797f47ed66d9d))
- **2026-05-12** — architecture review pass. Removed an empty join node, extracted reroute policy to its own module, split snapshot writing out of the moderator. Three ADRs recorded under `docs/adr/`. Tests: 105 → 110. Semantically neutral — no expected eval movement.
- **2026-05-12** — adversarial-eval harness landed (`backend.evals.run --adversarial`). 10 hand-crafted news-injection fixtures across 5 attack categories (explicit_instruction, role_hijack, misleading_quotation, fabricated_metric, source_ref_spoof). Primary metric: `absorption_rate` (judge-scored). Diagnostic: catch-mechanism breakdown by defense layer. ADR 0004 documents the design.
- **2026-05-12** — adversarial baseline: **absorption_rate 50% (5/10)**. By category: `explicit_instruction` 0% (2/2 caught), `role_hijack` 50%, `fabricated_metric` 50%, `source_ref_spoof` 50%, **`misleading_quotation` 100%** (2/2 absorbed — fabricated executive quotes are the weakest surface). RIVN was 4× more vulnerable than AAPL (4 absorbed vs 1) — the bull/bear debate on contested fundamentals is easier to tip with fakes. Verifier flagged 5/10 cases but reroute did not retract already-cited claims, so flagging ≠ catching. ([DagsHub run](https://dagshub.com/fwtangie/equity-research-agent.mlflow/#/experiments/0/runs/79f1f6d287e142b9bc8919a8ae0ed411))

## How it works

Given a ticker and a query type, a 15-node LangGraph pipeline runs:

1. **Supervisor** classifies the query type (`earnings`, `bull_bear`, or `thesis_drift`).
2. **Four evidence streams** fetch in parallel: market data (yfinance + Alpha Vantage), SEC filings (EDGAR), news (Tavily), and quant data (peer-comp returns/volatility).
3. **Quant interpretation** computes P/E, EV/EBITDA, and a 90-day price chart.
4. **Evidence contradiction** flags conflicts *within* the evidence pool (e.g. SEC filing says +15% revenue, news article says +8%).
5. **Bull and bear agents** synthesize cases in parallel, each constrained to cite evidence spans and avoid generic claims — phrases like "strong", "robust", "premium" are banned without a metric.
6. **Debate contradiction** flags conflicts *between* bull and bear claims.
7. **Verifier** checks all claims against evidence; high-severity issues trigger a **reroute** to the relevant source agent (max 2 reroutes before giving up).
8. **Thesis replay** loads the prior snapshot for this ticker and computes the delta (strengthened / weakened / new / disappeared).
9. **Moderator** assembles the final memo, reconciling bull and bear into a falsifiable synthesis with named conditions that would flip the call.
10. **Snapshot writer** persists the current thesis for the next run's drift comparison.

### Supported queries
1. Earnings investigation — *"What happened in AAPL's last earnings call?"*
2. Bull/bear thesis — *"Build a bull and bear case for NVDA"*
3. Thesis drift — *"How has the investment thesis for MSFT changed since last run?"*

**Not financial advice.** No buy/sell/hold recommendations.

## Architecture

```
FastAPI (SSE) ──▶ LangGraph StateGraph ──▶ Next.js dashboard
                          │
                     Supervisor
                          │
       ┌──────────────────┼──────────────────┬──────────────────┐
   MarketData          Filings              News           QuantData
       └──────────────────┴──────────────────┴──────────────────┘
                          │  (parallel fan-in, dedupe_by_id reducer)
                  QuantInterpretation
                          │
                  EvidenceContradiction
                          │
                  Bull Agent  ║  Bear Agent
                          │
                  DebateContradiction
                          │
                      Verifier  ◀─loop (max 2 reroutes)
                       │   │
                       │   └─ needs_reroute ─▶  Reroute  ─┘
                       │
                  ThesisReplay
                          │
                      Moderator
                          │
                  SnapshotWriter
```

## Tech stack

| Layer | Tool |
|---|---|
| Agent orchestration | LangGraph StateGraph |
| LLM (primary) | Groq llama-3.3-70b-versatile |
| LLM (fallback) | OpenAI gpt-4o |
| Market data | yfinance + Alpha Vantage |
| SEC filings | EDGAR |
| Web search | Tavily API |
| Schemas | Pydantic v2 |
| Backend API | FastAPI (SSE streaming) |
| Frontend | Next.js (Tailwind, Playwright e2e) |
| Eval harness | MLflow → DagsHub, 8-metric LLM-as-judge rubric |
| Persistence | SQLite checkpointer + JSON snapshot store |
| Deployment | Railway (backend + frontend services) |

## Eval methodology

See [`docs/evaluation.md`](docs/evaluation.md) for the full rubric and harness architecture. Briefly: the judge scores each memo across 8 metrics (logical consistency, synthesis quality, evidence coverage, citation accuracy, calibration, falsifiability, contradiction handling, balance) on a 1–5 scale; runs are logged to MLflow with experiment-level isolation. The `--quick` set is 2 tickers (AAPL, RIVN) — a tech mega-cap and a money-losing EV maker — chosen so prompt changes can be iterated against meaningfully different ticker profiles in under five minutes.

## Security posture

The threat model for an LLM equity-research system is **prompt injection via news content** — Tavily indexes the open web, so an adversarial article can be planted in the evidence pool. Unlike comparable LLM *trading* agents (which have seen multi-million-dollar losses from this vector in 2026), this system has no trade-execution path; the worst case is a misleading memo, not money moved.

Resistance to news-injection is measured, not just plumbed. The adversarial harness:

```bash
python -m backend.evals.run --adversarial
```

loads 10 hand-crafted fixtures across 5 attack categories (`backend/evals/adversarial_fixtures/`), mocks the Tavily call to inject a poisoned span alongside legitimate ones, runs the full pipeline, and scores:

- **Primary metric**: `absorption_rate` — judge-evaluated, lower is better.
- **Diagnostic**: catch-mechanism breakdown — which defense layer caught each non-absorbed case (`verifier_flagged` / `agent_refused` / `citation_layer_caught`). This separates *prompt-level defenses* from the *citation-requirement architecture* (source_ref system).

See [ADR 0004](docs/adr/0004-adversarial-eval-as-measured-metric.md) for the design rationale.

## Architecture decisions

ADRs under [`docs/adr/`](docs/adr/) record decisions made during the architecture review and security-posture passes:

- [0001](docs/adr/0001-keep-tool-agent-mirror-layer.md) — Keep the per-source agent layer; a generic fetch-node factory would leak because two of the four agents do real domain work (state metadata extraction, peer-comp orchestration).
- [0002](docs/adr/0002-no-step-framework-for-agents.md) — No shared `Step` framework for LLM-call agents; the actually-shared code is ~5 LOC and the recent eval lift came from targeted per-agent prompt tweaks.
- [0003](docs/adr/0003-no-state-contract-enforcement.md) — No typed state-contract enforcement; the class of bug it would catch has not appeared in history.
- [0004](docs/adr/0004-adversarial-eval-as-measured-metric.md) — Adversarial prompt-injection resistance as a measured lift metric, not silent defensive plumbing; mitigations are baseline-driven.

## Setup

```bash
cp .env.example .env
# fill in ALPHA_VANTAGE_KEY, TAVILY_KEY, and either:
# - LLM_PROVIDER=groq with GROQ_KEY plus optional OPENAI_API_KEY fallback
# - LLM_PROVIDER=openrouter with OPENROUTER_API_KEY

pip install -r requirements.txt
pytest                                              # 110 tests

uvicorn backend.api:app --reload                    # backend
cd frontend-next && npm install && npm run dev      # frontend
```

### Railway environment

Backend service variables:

```bash
ALPHA_VANTAGE_KEY=...
TAVILY_KEY=...
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=...
OPENROUTER_MODEL_LARGE=deepseek/deepseek-v4-flash
OPENROUTER_MODEL_SMALL=meta-llama/llama-3.1-8b-instruct
OPENROUTER_HTTP_REFERER=https://your-portfolio-site.example
OPENROUTER_APP_TITLE=Equity Research Agent
DEMO_ACCESS_CODE=...
RUNTIME_DATA_DIR=/app/runtime_data
RUNS_INDEX_FILE=/app/runtime_data/runs.jsonl
```

Frontend service variable:

```bash
NEXT_PUBLIC_BACKEND_URL=https://your-backend-service.up.railway.app
```

The default OpenRouter large model is `deepseek/deepseek-v4-flash`; the small tier uses `meta-llama/llama-3.1-8b-instruct` to keep lightweight agents cheap. Other lower-cost small-tier candidates include `qwen/qwen3.5-flash-02-23` and `z-ai/glm-4.7-flash`; run the eval harness before using them in the demo.

Set `DEMO_ACCESS_CODE` on the backend service to require a shared access code before users can start runs or fetch memo data. Leave it unset for open local development.

## License

MIT
