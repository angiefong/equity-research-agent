# Equity Research Agent

[![Evals](https://img.shields.io/badge/evals-DagsHub-blue)](https://dagshub.com/fwtangie/equity-research-agent.mlflow)

A verifiable multi-agent equity research system that produces source-backed research memos with bull/bear debate, contradiction detection, and thesis drift tracking.

> **Status:** In development — Phase 1 (multi-agent pipeline) in progress.

## Evaluation

Every change to this project is measured against an 8-metric LLM-as-judge rubric and tracked on DagsHub. See [`docs/evaluation.md`](docs/evaluation.md) for the rubric, harness architecture, and methodology.

### Lift log

- **2026-04-25** — eval harness scaffolded; 14 commits, 97 tests, MLflow logging to DagsHub.
- **2026-04-27** — first end-to-end run on `--quick` set (AAPL, RIVN). Harness infra validated end-to-end; both tickers failed at the pipeline layer (`llama-3.1-8b-instant` exhausted output tokens generating structured JSON; rate-limited on second ticker). Pipeline-level model upgrade is the next bottleneck. ([run](https://dagshub.com/fwtangie/equity-research-agent.mlflow/#/experiments/0/runs/20ea73d9e01444108f32736bd944b390))
- **2026-04-27** — agent upgraded to `llama-3.3-70b-versatile` + judge `max_tokens=4096`. **First real baseline:** avg overall **2.21/5** on quick set (AAPL: 2.00, RIVN: 2.43). Judge surfaced concrete analytical errors (e.g., AAPL bull case had inverted P/E comparison; RIVN bull misused negative EV/EBITDA as bullish). ([run](https://dagshub.com/fwtangie/equity-research-agent.mlflow/#/experiments/0/runs/7294cee0cdd54203bfec82eb2b73ca61))
- **2026-05-09** — `feature/sharper-debate` merged. Four targeted prompt fixes driven by judge feedback: (1) bull/bear arithmetic-sanity rule (kills inverted P/E and negative-multiple-as-bullish errors), (2) snapshot import-site patch (real bug — fixtures weren't being written), (3) source_ref-based citation system (replaces broken numeric `[N]` references that didn't map to the citations array), (4) moderator data-recency + numeric-format-consistency rules. **Result on same-model isolation: avg overall 2.21 → 3.29 (+1.08, ~49% lift)**, AAPL 2.00 → 3.57, RIVN 2.43 → 3.00. Logical consistency 4/4, synthesis quality 4/4 across both tickers. ([run](https://dagshub.com/fwtangie/equity-research-agent.mlflow/#/experiments/0/runs/dab1aa38d5d54b5bab2797f47ed66d9d))

## What it does

Given a ticker and a query type, the system runs a 13-node LangGraph pipeline that:
- Fetches market data, SEC filings, and news in parallel
- Runs quantitative analysis (P/E, EV/EBITDA, peer comps, price chart)
- Constructs bull and bear cases with cited evidence
- Detects contradictions within evidence and between bull/bear claims
- Verifies all claims against source evidence; rereroutes if issues found
- Tracks how the investment thesis has changed across runs
- Assembles a structured research memo with citations

**Supported queries (Phase 1):**
1. Earnings investigation — "What happened in AAPL's last earnings call?"
2. Bull/bear thesis — "Build a bull and bear case for NVDA"
3. Thesis drift — "How has the investment thesis for MSFT changed since last run?"

**Not financial advice.** No buy/sell/hold recommendations.

## Architecture

```
FastAPI (SSE) → LangGraph StateGraph → Streamlit Dashboard
                     │
          ┌──────────┼──────────┐
     Market Data  Filings    News  QuantData
          └──────────┼──────────┘
               EvidenceContradiction
               Bull Agent ║ Bear Agent
               DebateContradiction
               Verifier → (reroute if needed)
               ThesisReplay
               Moderator → ResearchMemo
```

## Tech Stack

| Layer | Tool |
|-------|------|
| Agent orchestration | LangGraph StateGraph |
| LLM (base) | Groq llama-3.1-8b-instant |
| LLM (fine-tuned, Phase 2) | Llama-3.1-8B QLoRA via PEFT + TRL |
| Market data | yfinance + Alpha Vantage |
| Web search | Tavily API |
| Data schemas | Pydantic v2 |
| Backend API | FastAPI (SSE streaming) |
| Frontend | Streamlit |
| Experiment tracking | MLflow → DagsHub |
| Deployment | Railway (2 services) |
| Model registry | HuggingFace Hub |

## Setup

```bash
cp .env.example .env
# fill in API keys
pip install -r requirements.txt
```

## License

MIT
