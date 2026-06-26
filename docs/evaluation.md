# Evaluation

This project ships with an LLM-as-judge eval harness so every change has a measurable lift signal — not vibes.

## What gets measured

Every memo run through the harness is scored on **8 metrics**:

### 1. Evidence coverage (0–5)

Scored *before* the memo is even generated. The judge sees only the ticker and the evidence the agents had access to, and asks: "Is this enough to write a senior-analyst memo?" Low scores here mean the **data pipeline** is the bottleneck.

| Score | Meaning |
| --- | --- |
| 0 | Missing or irrelevant |
| 3 | Competent intern coverage — fundamentals + news + filings, no segment/geo depth |
| 5 | Publication-grade — segment revenue, geo mix, forward guidance, multi-year trends |

### 2–8. Memo quality (0–5 each)

Scored after the memo is generated, with the judge seeing both the memo and the evidence:

- **Insight** — non-obvious, ticker-specific claims vs. peer-applicable platitudes
- **Factual accuracy** — every number traceable; level/growth not confused
- **Logical consistency** — internal contradictions detected and adjudicated
- **Causal reasoning** — driver → mechanism → financial impact → valuation impact chains
- **Synthesis quality** — bull/bear synthesized vs. restated
- **Data integrity** — every claim cites a span in evidence
- **Agent coordination** — bull and bear engage each other's specific claims

## Why two judging calls

A single judging call can't tell you *why* the memo is weak — is it because the evidence pipeline failed to gather segment data, or because the agents had the data and used it badly? By scoring evidence quality in a separate call (without showing the memo), the harness produces clean attribution: low evidence_coverage + high causal_reasoning means "fix the data pipeline." Reverse means "fix the prompts."

## Reproducibility — eval epochs

The pipeline pulls live data (yfinance, Tavily news, SEC filings). Same prompt + same model run today vs. tomorrow can produce different memos because the underlying news changed.

To make score deltas attributable to the change being evaluated (not to a quiet news day), the harness uses **epoch-scoped snapshots**: the first run in an epoch hits live APIs and writes fixtures; subsequent runs read fixtures and skip the APIs. Refresh the snapshot quarterly:

```bash
python -m backend.evals.snapshot refresh --epoch=2026-Q3
```

All comparisons within an epoch are deterministic. Cross-epoch comparisons are intentionally suppressed in the summary report.

## Architecture

```
backend/evals/
  config.py     ticker sets + env validation
  rubric.py     Pydantic schemas + anchor text
  snapshot.py   epoch-scoped tool monkeypatch
  judge.py      two-call Sonnet judge (langchain_anthropic)
  tracking.py   MLflow / DagsHub wrapper
  report.py     markdown summary builder
  run.py        CLI orchestrator
```

## How to use

```bash
# Quick run (AAPL, RIVN) — ~2 min, ~$0.20
python -m backend.evals.run --quick

# Full run (AAPL, MSFT, F, PLTR, TSLA) — ~5 min, ~$0.50
python -m backend.evals.run --full

# Run + post markdown summary to current GitHub PR
GITHUB_PR_NUMBER=42 python -m backend.evals.run --quick --publish
```

## CI

`.github/workflows/eval.yml` runs `--quick` on every PR and merge to main so CI does not exhaust hosted LLM daily-token quotas. Manual `--full` runs are available via workflow_dispatch when you want the broader five-ticker regression check. If the hosted LLM provider is already out of daily tokens, the workflow emits a warning and exits neutral instead of marking unrelated code changes red.

## Public experiment tracking

All runs are logged to a DagsHub-hosted MLflow project. Click the badge at the top of the README to browse runs, compare experiments, and download per-ticker artifacts (memo JSON, evidence summary, judge rationale).
