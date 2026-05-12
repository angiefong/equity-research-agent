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

## Architecture decisions

ADRs under [`docs/adr/`](docs/adr/) record decisions made during the architecture review pass, including which deepening candidates were considered and rejected. Three so far:

- [0001](docs/adr/0001-keep-tool-agent-mirror-layer.md) — Keep the per-source agent layer; a generic fetch-node factory would leak because two of the four agents do real domain work (state metadata extraction, peer-comp orchestration).
- [0002](docs/adr/0002-no-step-framework-for-agents.md) — No shared `Step` framework for LLM-call agents; the actually-shared code is ~5 LOC and the recent eval lift came from targeted per-agent prompt tweaks.
- [0003](docs/adr/0003-no-state-contract-enforcement.md) — No typed state-contract enforcement; the class of bug it would catch has not appeared in history.

## Setup

```bash
cp .env.example .env
# fill in GROQ_KEY, OPENAI_API_KEY (fallback), ALPHA_VANTAGE_KEY, TAVILY_API_KEY

pip install -r requirements.txt
pytest                                              # 110 tests

uvicorn backend.api:app --reload                    # backend
cd frontend-next && npm install && npm run dev      # frontend
```

## License

MIT
