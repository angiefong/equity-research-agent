import json
import os
import uuid
from typing import AsyncGenerator

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

load_dotenv()

from backend.graph.builder import build_graph
from backend.persistence.checkpointer import get_checkpointer
from backend.persistence.snapshot_store import load_latest_snapshot

app = FastAPI(title="Financial Research Agent API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

AGENT_NODES = {
    "supervisor", "market_data", "filings", "news", "quant_data",
    "evidence_merge", "quant_interpretation", "evidence_contradiction",
    "bull", "bear", "debate_contradiction", "verifier",
    "reroute", "thesis_replay", "moderator",
}

_run_results: dict[str, dict] = {}


@app.get("/run/stream")
async def run_stream(ticker: str, query: str):
    run_id = str(uuid.uuid4())

    async def event_gen() -> AsyncGenerator:
        yield {"event": "run_started", "data": json.dumps({"run_id": run_id, "ticker": ticker})}

        import time
        try:
            with get_checkpointer() as checkpointer:
                graph = build_graph(checkpointer=checkpointer)
                config = {"configurable": {"thread_id": run_id}}
                agent_timings: dict[str, float] = {}

                async for event in graph.astream_events(
                    {"query": query, "ticker": ticker},
                    config=config,
                    version="v2",
                ):
                    name = event.get("name", "")
                    etype = event.get("event", "")

                    if etype == "on_chain_start" and name in AGENT_NODES:
                        agent_timings[name] = time.time()
                        yield {
                            "event": "agent_started",
                            "data": json.dumps({"agent": name, "run_id": run_id}),
                        }

                    elif etype == "on_chain_end" and name in AGENT_NODES:
                        elapsed = time.time() - agent_timings.get(name, time.time())
                        output = event.get("data", {}).get("output", {})
                        summary = _summarize_output(name, output)
                        yield {
                            "event": "agent_completed",
                            "data": json.dumps({
                                "agent": name,
                                "summary": summary,
                                "elapsed_s": round(elapsed, 2),
                                "run_id": run_id,
                            }),
                        }
                        yield {
                            "event": "artifact_emitted",
                            "data": json.dumps({"agent": name, "artifact": output, "run_id": run_id}),
                        }

                    elif etype == "on_chain_error" and name in AGENT_NODES:
                        yield {
                            "event": "agent_failed",
                            "data": json.dumps({"agent": name, "error": str(event.get("data", {}).get("error", "")), "run_id": run_id}),
                        }

                state = graph.get_state(config)
                final = dict(state.values) if state else {}
                _run_results[run_id] = final

            yield {
                "event": "run_completed",
                "data": json.dumps({"run_id": run_id, "ticker": ticker}),
            }

        except Exception as e:
            yield {"event": "agent_failed", "data": json.dumps({"agent": "graph", "error": str(e), "run_id": run_id})}

    return EventSourceResponse(event_gen())


def _summarize_output(agent: str, output: dict) -> str:
    if agent in ("market_data", "filings", "news", "quant_data", "quant_interpretation"):
        n = len(output.get("evidence", []))
        return f"{n} evidence span(s)"
    if agent in ("evidence_contradiction", "debate_contradiction"):
        n = len(output.get("evidence_contradictions", output.get("debate_contradictions", [])))
        return f"{n} contradiction(s)"
    if agent == "bull":
        return f"{len(output.get('bull_points', []))} bull point(s)"
    if agent == "bear":
        return f"{len(output.get('bear_points', []))} bear point(s)"
    if agent == "verifier":
        return f"status: {output.get('verification_status', 'unknown')}"
    if agent == "moderator":
        return "memo assembled"
    return "done"


@app.get("/run/{run_id}/memo")
async def get_memo(run_id: str):
    result = _run_results.get(run_id)
    if not result or not result.get("final_memo"):
        raise HTTPException(status_code=404, detail="Run not found or not completed")
    return result["final_memo"]


@app.get("/run/{run_id}/artifacts")
async def get_artifacts(run_id: str):
    result = _run_results.get(run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        k: v for k, v in result.items()
        if k in ("evidence", "bull_points", "bear_points", "evidence_contradictions",
                  "debate_contradictions", "verification_issues", "thesis_delta")
    }


@app.get("/ticker/{ticker}/thesis-drift")
async def get_thesis_drift(ticker: str):
    snapshot = load_latest_snapshot(ticker)
    if not snapshot:
        return {"message": f"No prior run found for {ticker}"}
    return snapshot
