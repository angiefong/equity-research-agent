from backend.tools.news import get_news_evidence
from backend.graph.state import AgentState


def news_agent(state: AgentState) -> dict:
    spans = get_news_evidence(state["ticker"])
    return {"evidence": spans}
