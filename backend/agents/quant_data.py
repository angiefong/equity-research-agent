from backend.tools.quant import compute_returns, compute_volatility, fetch_peer_comps
from backend.graph.state import AgentState

PEER_MAP = {
    "AAPL": ["MSFT", "GOOGL", "META"],
    "MSFT": ["AAPL", "GOOGL", "AMZN"],
    "GOOGL": ["META", "MSFT", "AMZN"],
    "NVDA": ["AMD", "INTC", "QCOM"],
    "TSLA": ["GM", "F", "RIVN"],
}
DEFAULT_PEERS = ["SPY", "QQQ", "IWM"]


def quant_data_agent(state: AgentState) -> dict:
    ticker = state["ticker"]
    peers = PEER_MAP.get(ticker.upper(), DEFAULT_PEERS)
    spans = [
        compute_returns(ticker),
        compute_volatility(ticker),
        *fetch_peer_comps(ticker, peers),
    ]
    return {"evidence": spans}
