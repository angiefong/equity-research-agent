from backend.graph.state import AgentState
from backend.persistence.snapshot_store import load_latest_snapshot
from backend.schemas.debate import DebatePoint
from backend.schemas.thesis import ConfidenceDrift, ThesisDelta, ThesisSnapshot


def _extract_claims(points: list[DebatePoint]) -> set[str]:
    return {p.claim for p in points}


def thesis_replay_agent(state: AgentState) -> dict:
    prior = load_latest_snapshot(state["ticker"])
    if prior is None:
        return {"thesis_snapshot_prior": None, "thesis_delta": None}

    current_bull = _extract_claims(state["bull_points"])
    current_bear = _extract_claims(state["bear_points"])
    prior_bull = _extract_claims(prior.bull_points)
    prior_bear = _extract_claims(prior.bear_points)

    current_all = current_bull | current_bear
    prior_all = prior_bull | prior_bear

    new_claims = list(current_all - prior_all)
    disappeared = list(prior_all - current_all)

    current_conf = {
        p.claim: p.confidence
        for p in state["bull_points"] + state["bear_points"]
    }
    prior_conf = {
        p.claim: p.confidence
        for p in prior.bull_points + prior.bear_points
    }

    strengthened, weakened, drifts = [], [], []
    for claim in current_all & prior_all:
        delta = current_conf.get(claim, 0.0) - prior_conf.get(claim, 0.0)
        if delta > 0.05:
            strengthened.append(claim)
        elif delta < -0.05:
            weakened.append(claim)
        drifts.append(ConfidenceDrift(
            topic=claim[:60],
            previous=prior_conf.get(claim, 0.0),
            current=current_conf.get(claim, 0.0),
            delta=delta,
        ))

    delta = ThesisDelta(
        ticker=state["ticker"],
        previous_run_id=prior.id,
        current_run_id="current",
        strengthened=strengthened,
        weakened=weakened,
        new=new_claims,
        disappeared=disappeared,
        confidence_drift=drifts,
    )
    return {"thesis_snapshot_prior": prior, "thesis_delta": delta}
