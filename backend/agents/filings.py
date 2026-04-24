from backend.tools.filings import fetch_recent_filings
from backend.graph.state import AgentState


def filings_agent(state: AgentState) -> dict:
    spans = fetch_recent_filings(state["ticker"], forms=["10-K", "10-Q", "8-K"], max_filings=3)
    return {"evidence": spans}
