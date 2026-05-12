from backend.graph.state import AgentState
from backend.persistence.snapshot_store import save_snapshot
from backend.schemas.thesis import ThesisSnapshot


def snapshot_writer_agent(state: AgentState) -> dict:
    snapshot = ThesisSnapshot(
        ticker=state["ticker"],
        bull_points=state["bull_points"],
        bear_points=state["bear_points"],
        confidence_by_topic={
            p.claim[:40]: p.confidence
            for p in state["bull_points"] + state["bear_points"]
        },
    )
    save_snapshot(snapshot)
    return {"thesis_snapshot_current": snapshot}
