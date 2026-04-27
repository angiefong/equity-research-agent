from langgraph.graph import StateGraph, START, END
from backend.graph.state import AgentState, InputState, OutputState
from backend.agents.supervisor import supervisor_agent
from backend.agents.market_data import market_data_agent
from backend.agents.filings import filings_agent
from backend.agents.news import news_agent
from backend.agents.quant_data import quant_data_agent
from backend.agents.quant_interpretation import quant_interpretation_agent
from backend.agents.evidence_contradiction import evidence_contradiction_agent
from backend.agents.bull import bull_agent
from backend.agents.bear import bear_agent
from backend.agents.debate_contradiction import debate_contradiction_agent
from backend.agents.verifier import verifier_agent
from backend.agents.reroute import reroute_agent
from backend.agents.thesis_replay import thesis_replay_agent
from backend.agents.moderator import moderator_agent


def _evidence_merge(state: AgentState) -> dict:
    return {}


def _route_after_verifier(state: AgentState) -> str:
    if (
        state.get("verification_status") == "needs_reroute"
        and state.get("reroute_count_total", 0) < 2
    ):
        return "reroute"
    return "thesis_replay"


def build_graph(checkpointer=None) -> StateGraph:
    builder = StateGraph(AgentState, input=InputState, output=OutputState)

    builder.add_node("supervisor", supervisor_agent)
    builder.add_node("market_data", market_data_agent)
    builder.add_node("filings", filings_agent)
    builder.add_node("news", news_agent)
    builder.add_node("quant_data", quant_data_agent)
    builder.add_node("evidence_merge", _evidence_merge)
    builder.add_node("quant_interpretation", quant_interpretation_agent)
    builder.add_node("evidence_contradiction", evidence_contradiction_agent)
    builder.add_node("bull", bull_agent)
    builder.add_node("bear", bear_agent)
    builder.add_node("debate_contradiction", debate_contradiction_agent)
    builder.add_node("verifier", verifier_agent)
    builder.add_node("reroute", reroute_agent)
    builder.add_node("thesis_replay", thesis_replay_agent)
    builder.add_node("moderator", moderator_agent)

    builder.add_edge(START, "supervisor")

    builder.add_edge("supervisor", "market_data")
    builder.add_edge("supervisor", "filings")
    builder.add_edge("supervisor", "news")
    builder.add_edge("supervisor", "quant_data")

    builder.add_edge("market_data", "evidence_merge")
    builder.add_edge("filings", "evidence_merge")
    builder.add_edge("news", "evidence_merge")
    builder.add_edge("quant_data", "evidence_merge")

    builder.add_edge("evidence_merge", "quant_interpretation")
    builder.add_edge("quant_interpretation", "evidence_contradiction")

    builder.add_edge("evidence_contradiction", "bull")
    builder.add_edge("evidence_contradiction", "bear")

    builder.add_edge("bull", "debate_contradiction")
    builder.add_edge("bear", "debate_contradiction")

    builder.add_edge("debate_contradiction", "verifier")

    builder.add_conditional_edges(
        "verifier",
        _route_after_verifier,
        {"reroute": "reroute", "thesis_replay": "thesis_replay"},
    )

    builder.add_edge("reroute", "verifier")

    builder.add_edge("thesis_replay", "moderator")
    builder.add_edge("moderator", END)

    return builder.compile(checkpointer=checkpointer)
