# Equity Research Agent

A verifiable multi-agent equity research system that produces source-backed research memos with bull/bear debate, contradiction detection, and thesis drift tracking.

> **Status:** In development — Phase 1 (multi-agent pipeline) in progress.

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

## Evaluation

Three-way comparison: single-agent baseline vs multi-agent + base model vs multi-agent + fine-tuned Moderator.

Metrics: factual accuracy, citation coverage, unsupported claim rate, groundedness (manual rubric /15).

## Setup

```bash
cp .env.example .env
# fill in API keys
pip install -r requirements.txt
```

## License

MIT
