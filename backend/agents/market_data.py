from backend.tools.market_data import get_market_data_evidence
from backend.graph.state import AgentState


def market_data_agent(state: AgentState) -> dict:
    spans = get_market_data_evidence(state["ticker"])
    return {"evidence": spans}
