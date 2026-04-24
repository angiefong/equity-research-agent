from typing import Literal
from pydantic import BaseModel
from backend.agents.llm import get_structured_llm
from backend.graph.state import AgentState

VALID_QUERY_TYPES = Literal["earnings", "bull_bear", "thesis_drift"]


class SupervisorOutput(BaseModel):
    query_type: VALID_QUERY_TYPES
    reasoning: str


_SYSTEM = """You classify financial research queries into one of three types:
- earnings: questions about recent earnings results, EPS, revenue, guidance
- bull_bear: requests to build bull and bear thesis or analyze upside/downside
- thesis_drift: questions about how a thesis has changed over time

Return the query_type and a one-sentence reasoning."""


def supervisor_agent(state: AgentState) -> dict:
    llm = get_structured_llm(SupervisorOutput)
    result = llm.invoke([
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": f"Query: {state['query']}\nTicker: {state['ticker']}"},
    ])
    return {"query_type": result.query_type}
