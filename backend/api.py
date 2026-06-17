import asyncio
import json
import logging
import os
import secrets
import uuid
from datetime import date, datetime
from enum import Enum
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse


def _jsonable(obj):
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    raise TypeError(f"Not JSON serializable: {type(obj).__name__}")


def _dumps(payload: dict) -> str:
    return json.dumps(payload, default=_jsonable)

load_dotenv()

from backend.graph.builder import build_graph
from backend.persistence.checkpointer import get_checkpointer
from backend.persistence.snapshot_store import load_latest_snapshot
from backend.persistence.runs_index import append_run, list_runs

app = FastAPI(title="Financial Research Agent API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

AGENT_NODES = {
    "supervisor", "market_data", "filings", "news", "quant_data",
    "quant_interpretation", "evidence_contradiction",
    "bull", "bear", "debate_contradiction", "verifier",
    "reroute", "thesis_replay", "moderator", "snapshot_writer",
}

_run_results: dict[str, dict] = {}


def _demo_access_code() -> str | None:
    return os.environ.get("DEMO_ACCESS_CODE") or None


def _require_demo_access(access_code: str | None) -> None:
    expected = _demo_access_code()
    if expected and not secrets.compare_digest(access_code or "", expected):
        raise HTTPException(status_code=401, detail="Demo access code required")


@app.get("/run/stream")
async def run_stream(ticker: str, query: str, access_code: str | None = None):
    _require_demo_access(access_code)
    run_id = str(uuid.uuid4())

    async def event_gen() -> AsyncGenerator:
        yield {"event": "run_started", "data": _dumps({"run_id": run_id, "ticker": ticker})}

        import time
        run_start_time = time.time()

        active_agents: set[str] = set()
        completed_agents: set[str] = set()
        merged: asyncio.Queue = asyncio.Queue()
        SENTINEL = object()

        async def heartbeat_producer():
            while True:
                interval = 1.0 if active_agents else 5.0
                await asyncio.sleep(interval)
                await merged.put({"event": "heartbeat", "data": _dumps({})})

        async def graph_producer(graph, config):
            agent_timings: dict[str, float] = {}
            try:
                async for event in graph.astream_events(
                    {"query": query, "ticker": ticker},
                    config=config,
                    version="v2",
                ):
                    name = event.get("name", "")
                    etype = event.get("event", "")

                    if etype == "on_chain_start" and name in AGENT_NODES:
                        agent_timings[name] = time.time()
                        active_agents.add(name)
                        await merged.put({
                            "event": "agent_started",
                            "data": _dumps({"agent": name, "run_id": run_id}),
                        })

                    elif etype == "on_chain_end" and name in AGENT_NODES:
                        elapsed = time.time() - agent_timings.get(name, time.time())
                        output = event.get("data", {}).get("output", {})
                        summary = _summarize_output(name, output)
                        active_agents.discard(name)
                        completed_agents.add(name)
                        await merged.put({
                            "event": "agent_completed",
                            "data": _dumps({
                                "agent": name,
                                "summary": summary,
                                "elapsed_s": round(elapsed, 2),
                                "run_id": run_id,
                            }),
                        })
                        await merged.put({
                            "event": "artifact_emitted",
                            "data": _dumps({"agent": name, "artifact": output, "run_id": run_id}),
                        })

                    elif etype == "on_chain_error" and name in AGENT_NODES:
                        active_agents.discard(name)
                        await merged.put({
                            "event": "agent_failed",
                            "data": _dumps({"agent": name, "error": str(event.get("data", {}).get("error", "")), "run_id": run_id}),
                        })

                state = await graph.aget_state(config)
                final = dict(state.values) if state else {}
                _run_results[run_id] = final
                _run_results[run_id]["duration_s"] = round(time.time() - run_start_time, 2)
                _run_results[run_id]["agent_count"] = len(completed_agents)
            finally:
                await merged.put(SENTINEL)

        try:
            async with get_checkpointer() as checkpointer:
                graph = build_graph(checkpointer=checkpointer)
                config = {"configurable": {"thread_id": run_id}}
                hb_task = asyncio.create_task(heartbeat_producer())
                graph_task = asyncio.create_task(graph_producer(graph, config))

                try:
                    while True:
                        item = await merged.get()
                        if item is SENTINEL:
                            break
                        yield item
                finally:
                    hb_task.cancel()
                    if not graph_task.done():
                        graph_task.cancel()
                    for t in (hb_task, graph_task):
                        try:
                            await t
                        except asyncio.CancelledError:
                            pass
                        except Exception:
                            logger.exception("producer task failed")

            try:
                stored = _run_results.get(run_id, {})
                final_memo = stored.get("final_memo")
                if final_memo is not None:
                    memo_dict = final_memo.model_dump() if hasattr(final_memo, "model_dump") else dict(final_memo)
                    lede = (memo_dict.get("research_summary") or "").split(".")[0][:200]
                    append_run({
                        "run_id": run_id,
                        "ticker": ticker,
                        "verdict": _classify_verdict(memo_dict),
                        "bull_weight": memo_dict.get("bull_weight"),
                        "bear_weight": memo_dict.get("bear_weight"),
                        "lede": lede,
                        "duration_s": round(time.time() - run_start_time, 2),
                        "agent_count": len(completed_agents),
                    })
            except Exception:
                logger.exception("failed to append run to runs_index")

            yield {
                "event": "run_completed",
                "data": _dumps({"run_id": run_id, "ticker": ticker}),
            }

        except Exception as e:
            yield {"event": "agent_failed", "data": _dumps({"agent": "graph", "error": str(e), "run_id": run_id})}

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
    if agent == "snapshot_writer":
        return "thesis snapshot saved"
    return "done"


def _classify_verdict(memo: dict) -> str:
    bw = memo.get("bull_weight") or 0.0
    br = memo.get("bear_weight") or 0.0
    if bw - br > 0.15: return "Strong Bull"
    if bw - br > 0.0: return "Cautious Bull"
    if br - bw > 0.15: return "Strong Bear"
    if br - bw > 0.0: return "Cautious Bear"
    return "Neutral"


@app.get("/runs")
async def get_runs(limit: int = 10, access_code: str | None = None):
    _require_demo_access(access_code)
    return list_runs(limit=limit)


@app.get("/run/{run_id}/memo")
async def get_memo(run_id: str, access_code: str | None = None):
    _require_demo_access(access_code)
    result = _run_results.get(run_id)
    if not result or not result.get("final_memo"):
        raise HTTPException(status_code=404, detail="Run not found or not completed")
    return result["final_memo"]


@app.get("/run/{run_id}/artifacts")
async def get_artifacts(run_id: str, access_code: str | None = None):
    _require_demo_access(access_code)
    result = _run_results.get(run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        k: v for k, v in result.items()
        if k in (
            "evidence", "bull_points", "bear_points", "evidence_contradictions",
            "debate_contradictions", "verification_issues", "thesis_delta",
            "market_snapshot", "duration_s", "agent_count",
        )
    }


@app.get("/ticker/{ticker}/thesis-drift")
async def get_thesis_drift(ticker: str, access_code: str | None = None):
    _require_demo_access(access_code)
    snapshot = load_latest_snapshot(ticker)
    if not snapshot:
        return {"message": f"No prior run found for {ticker}"}
    return snapshot
