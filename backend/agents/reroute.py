from backend.graph.state import AgentState
from backend.tools.filings import fetch_recent_filings
from backend.tools.market_data import get_market_data_evidence
from backend.tools.news import get_news_evidence
from backend.tools.quant import compute_returns, compute_volatility


def reroute_agent(state: AgentState) -> dict:
    new_evidence = []
    for target in state["reroute_targets"]:
        if target == "market_data":
            new_evidence.extend(get_market_data_evidence(state["ticker"]))
        elif target == "filings":
            new_evidence.extend(fetch_recent_filings(state["ticker"]))
        elif target == "news":
            new_evidence.extend(get_news_evidence(state["ticker"]))
        elif target == "quant_data":
            new_evidence.extend([
                compute_returns(state["ticker"]),
                compute_volatility(state["ticker"]),
            ])
    return {
        "evidence": new_evidence,
        "reroute_count_total": state.get("reroute_count_total", 0) + 1,
        "reroute_targets": [],
        "verification_status": "pending",
    }
