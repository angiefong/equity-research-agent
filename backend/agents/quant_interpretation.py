from backend.tools.quant import compute_pe_ratio, compute_ev_ebitda, generate_price_chart
from backend.graph.state import AgentState


def quant_interpretation_agent(state: AgentState) -> dict:
    ticker = state["ticker"]
    spans = [
        compute_pe_ratio(ticker),
        compute_ev_ebitda(ticker),
        generate_price_chart(ticker),
    ]
    return {"evidence": spans}
