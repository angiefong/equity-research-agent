"""Markdown summary builder for eval runs (PR comments + local files)."""
from __future__ import annotations
from typing import Any

from backend.evals.rubric import FullEval

_METRIC_ROWS = [
    ("evidence_coverage",   "Evidence coverage"),
    ("insight",             "Insight"),
    ("factual_accuracy",    "Factual accuracy"),
    ("logical_consistency", "Logical consistency"),
    ("causal_reasoning",    "Causal reasoning"),
    ("synthesis_quality",   "Synthesis quality"),
    ("data_integrity",      "Data integrity"),
    ("agent_coordination",  "Agent coordination"),
    ("overall_memo",        "**Overall (memo)**"),
]


def _per_ticker_score(full: FullEval | None, key: str) -> str:
    if full is None:
        return "❌"
    if key == "overall_memo":
        return f"{full.memo.average:.2f}"
    if key == "evidence_coverage":
        return f"{full.evidence.evidence_coverage.score}"
    return f"{getattr(full.memo, key).score}"


def _avg_for_key(per_ticker: dict[str, FullEval | None], key: str) -> float | None:
    succeeded = [v for v in per_ticker.values() if v is not None]
    if not succeeded:
        return None
    if key == "overall_memo":
        return sum(v.memo.average for v in succeeded) / len(succeeded)
    if key == "evidence_coverage":
        return sum(v.evidence.evidence_coverage.score for v in succeeded) / len(succeeded)
    return sum(getattr(v.memo, key).score for v in succeeded) / len(succeeded)


def _format_delta(current: float, baseline: float) -> str:
    delta = current - baseline
    if abs(delta) < 0.05:
        return "0.00"
    sign = "+" if delta > 0 else ""
    icon = "✅" if delta > 0 else "❌"
    return f"{sign}{delta:.2f} {icon}"


def build_summary(
    per_ticker: dict[str, FullEval | None],
    baseline_avgs: dict[str, float] | None,
    run_meta: dict[str, str],
) -> str:
    has_baseline = baseline_avgs is not None
    tickers = list(per_ticker.keys())

    lines: list[str] = []
    lines.append(f"## 📊 Eval Run — `{run_meta['branch']}` vs `main`")
    lines.append("")
    lines.append(
        f"**Set:** {run_meta['ticker_set']} ({', '.join(tickers)}) | "
        f"**Epoch:** {run_meta['epoch']} | "
        f"**Judge:** {run_meta['judge_model']}"
    )
    lines.append(
        f"**Agent model:** {run_meta['agent_model']} | "
        f"**Run:** [DagsHub →]({run_meta.get('dagshub_url', '')})"
    )
    lines.append("")

    if not has_baseline:
        lines.append("### Score table — _Establishing baseline_")
    else:
        lines.append("### Score deltas vs. main baseline")
    lines.append("")

    header = "| Metric | Avg | " + ("Δ vs main | " if has_baseline else "") + \
             f"Per-ticker ({' / '.join(tickers)}) |"
    sep = "| --- | --- | " + ("--- | " if has_baseline else "") + "--- |"
    lines.append(header)
    lines.append(sep)

    for key, label in _METRIC_ROWS:
        avg = _avg_for_key(per_ticker, key)
        avg_str = f"{avg:.2f}" if avg is not None else "—"
        per_t = " / ".join(_per_ticker_score(per_ticker[t], key) for t in tickers)
        if has_baseline:
            base = baseline_avgs.get(f"avg_{key}")
            delta_str = _format_delta(avg, base) if (avg is not None and base is not None) else "—"
            lines.append(f"| {label} | {avg_str} | {delta_str} | {per_t} |")
        else:
            lines.append(f"| {label} | {avg_str} | {per_t} |")

    lines.append("")
    lines.append("### Evidence gaps surfaced")
    any_gaps = False
    for ticker, full in per_ticker.items():
        if full is None or not full.evidence.missing_items:
            continue
        any_gaps = True
        lines.append(f"- **{ticker}:** {', '.join(full.evidence.missing_items)}")
    if not any_gaps:
        lines.append("_None — all required items present._")

    lines.append("")
    lines.append("### Top judge comments")
    for ticker, full in per_ticker.items():
        if full is None:
            lines.append(f"> **{ticker}:** _pipeline failed — see run artifacts_")
        else:
            lines.append(f"> **{ticker}:** {full.memo.overall_comment}")

    return "\n".join(lines) + "\n"


def exceeds_regression(
    avg_overall: float | None,
    baseline_overall: float | None,
    threshold: float,
) -> bool:
    if avg_overall is None or baseline_overall is None:
        return False
    return (baseline_overall - avg_overall) > threshold
