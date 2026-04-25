"""LLM-as-judge: two Sonnet calls per ticker (evidence quality, memo quality)."""
from __future__ import annotations
import json
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.evals.config import resolve_judge_model
from backend.evals.rubric import (
    EVIDENCE_RUBRIC_TEXT,
    MEMO_RUBRIC_TEXT,
    EvidenceEval,
    MemoEval,
)


def _judge_llm():
    return ChatAnthropic(model=resolve_judge_model(), temperature=0)


def _build_evidence_chain():
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You evaluate equity-research evidence pipelines. {rubric}"),
        ("user",
         "Ticker: {ticker}\n\n{evidence_summary}\n\n"
         "Score `evidence_coverage` and list specific `missing_items` by name."),
    ]).partial(rubric=EVIDENCE_RUBRIC_TEXT)
    return prompt | _judge_llm().with_structured_output(EvidenceEval)


def _build_memo_chain():
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You evaluate equity-research memos against a 7-metric rubric. {rubric}"),
        ("user",
         "Memo (JSON):\n{memo_json}\n\nEvidence the agents had:\n{evidence_summary}\n\n"
         "Score each metric 0-5 with a 1-3 sentence rationale citing specific memo content."),
    ]).partial(rubric=MEMO_RUBRIC_TEXT)
    return prompt | _judge_llm().with_structured_output(MemoEval)


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, max=10), reraise=True)
def score_evidence(ticker: str, evidence_summary: str) -> EvidenceEval:
    chain = _build_evidence_chain()
    return chain.invoke({"ticker": ticker, "evidence_summary": evidence_summary})


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, max=10), reraise=True)
def score_memo(memo: dict, evidence_summary: str) -> MemoEval:
    chain = _build_memo_chain()
    return chain.invoke({
        "memo_json": json.dumps(memo, indent=2),
        "evidence_summary": evidence_summary,
    })


def summarize_evidence(spans: list[dict], max_chars: int = 8000) -> str:
    """Compact a list of evidence spans into a string for the judge prompt."""
    header = f"Evidence ({len(spans)} spans):\n"
    body_parts: list[str] = []
    used = len(header)
    for s in spans:
        text = s.get("text", "")
        ref = s.get("source_ref", "?")
        line = f"- [{ref}] {text}\n"
        if used + len(line) > max_chars:
            body_parts.append(f"... ({len(spans) - len(body_parts)} more spans truncated)\n")
            break
        body_parts.append(line)
        used += len(line)
    return header + "".join(body_parts)
