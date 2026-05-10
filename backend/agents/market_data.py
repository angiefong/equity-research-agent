from backend.tools.market_data import get_market_data_evidence, get_company_overview
from backend.graph.state import AgentState


def market_data_agent(state: AgentState) -> dict:
    ticker = state["ticker"]
    overview = get_company_overview(ticker)
    spans = get_market_data_evidence(ticker, overview=overview)
    return {
        "evidence": spans,
        "company_name": overview.get("Name"),
        "exchange": overview.get("Exchange"),
        "sector": overview.get("Sector"),
    }
