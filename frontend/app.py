import json
import os
import time
from datetime import datetime

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

AGENT_ORDER = [
    "supervisor", "market_data", "filings", "news", "quant_data",
    "quant_interpretation", "evidence_contradiction",
    "bull", "bear", "debate_contradiction",
    "verifier", "reroute", "thesis_replay", "moderator",
]

st.set_page_config(page_title="Equity Research Agent", layout="wide")
st.title("Equity Research Agent")

with st.form("research_form"):
    col1, col2 = st.columns([1, 3])
    ticker = col1.text_input("Ticker", value="AAPL").upper().strip()
    query = col2.text_input("Query", value="Build a bull and bear case for AAPL")
    submitted = st.form_submit_button("Run Research")

if not submitted:
    st.stop()

st.session_state.setdefault("agent_status", {})
st.session_state.setdefault("agent_summary", {})
st.session_state.setdefault("agent_timing", {})
st.session_state.setdefault("artifacts", {})
st.session_state.setdefault("run_id", None)
st.session_state.setdefault("contradiction_count", 0)
st.session_state.setdefault("verifier_status", "pending")
st.session_state.setdefault("reroute_count", 0)
st.session_state.setdefault("run_complete", False)
st.session_state.setdefault("start_time", time.time())

for a in AGENT_ORDER:
    st.session_state["agent_status"].setdefault(a, "pending")

summary_strip = st.empty()

def _render_summary_strip(status="Running..."):
    elapsed = int(time.time() - st.session_state["start_time"])
    n_contradictions = st.session_state["contradiction_count"]
    v_status = st.session_state["verifier_status"]
    retries = st.session_state["reroute_count"]
    summary_strip.markdown(
        f"**{ticker}** &nbsp;|&nbsp; {status} &nbsp;|&nbsp; "
        f"Elapsed: {elapsed}s &nbsp;|&nbsp; Retries: {retries} &nbsp;|&nbsp; "
        f"Contradictions: {n_contradictions} &nbsp;|&nbsp; Verifier: `{v_status}`"
    )

_render_summary_strip()

panel_containers = {a: st.empty() for a in AGENT_ORDER}

def _render_agent_panel(agent: str):
    status = st.session_state["agent_status"].get(agent, "pending")
    summary = st.session_state["agent_summary"].get(agent, "")
    elapsed = st.session_state["agent_timing"].get(agent, "")
    timing_str = f" — {elapsed}s" if elapsed else ""

    with panel_containers[agent].container():
        if status == "running":
            with st.expander(f"⚡ {agent}", expanded=True):
                st.spinner(f"{agent} running...")
        elif status == "completed":
            with st.expander(f"✅ {agent}{timing_str} — {summary}", expanded=False):
                artifact = st.session_state["artifacts"].get(agent, {})
                st.json(artifact, expanded=False)
        elif status == "failed":
            with st.expander(f"❌ {agent} — FAILED", expanded=True):
                st.error(st.session_state["agent_summary"].get(agent, "Unknown error"))
        else:
            panel_containers[agent].markdown(f"⬜ `{agent}` — pending")

for a in AGENT_ORDER:
    _render_agent_panel(a)

def consume_sse():
    url = f"{BACKEND_URL}/run/stream"
    params = {"ticker": ticker, "query": query}
    with requests.get(url, params=params, stream=True, timeout=300) as resp:
        event_type = None
        for raw_line in resp.iter_lines():
            if not raw_line:
                continue
            line = raw_line.decode("utf-8") if isinstance(raw_line, bytes) else raw_line
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data = json.loads(line.split(":", 1)[1].strip())
                _handle_event(event_type, data)
                _render_summary_strip()
                for a in AGENT_ORDER:
                    _render_agent_panel(a)
                if event_type == "run_completed":
                    return


def _handle_event(event_type: str, data: dict):
    agent = data.get("agent", "")
    if event_type == "run_started":
        st.session_state["run_id"] = data.get("run_id")
    elif event_type == "agent_started" and agent in AGENT_ORDER:
        st.session_state["agent_status"][agent] = "running"
    elif event_type == "agent_completed" and agent in AGENT_ORDER:
        st.session_state["agent_status"][agent] = "completed"
        st.session_state["agent_summary"][agent] = data.get("summary", "")
        st.session_state["agent_timing"][agent] = data.get("elapsed_s", "")
        if agent == "verifier":
            st.session_state["verifier_status"] = data.get("summary", "unknown")
        if agent == "reroute":
            st.session_state["reroute_count"] += 1
    elif event_type == "artifact_emitted" and agent in AGENT_ORDER:
        artifact = data.get("artifact", {})
        st.session_state["artifacts"][agent] = artifact
        n = len(artifact.get("evidence_contradictions", []) + artifact.get("debate_contradictions", []))
        if n > 0:
            st.session_state["contradiction_count"] = max(st.session_state["contradiction_count"], n)
    elif event_type == "agent_failed" and agent in AGENT_ORDER:
        st.session_state["agent_status"][agent] = "failed"
        st.session_state["agent_summary"][agent] = data.get("error", "unknown error")
    elif event_type == "run_completed":
        st.session_state["run_complete"] = True


consume_sse()

if not st.session_state["run_complete"]:
    st.stop()

_render_summary_strip(status="Complete ✓")

run_id = st.session_state["run_id"]
memo_resp = requests.get(f"{BACKEND_URL}/run/{run_id}/memo")
artifacts_resp = requests.get(f"{BACKEND_URL}/run/{run_id}/artifacts")

memo = memo_resp.json() if memo_resp.ok else {}
artifacts = artifacts_resp.json() if artifacts_resp.ok else {}

tab_memo, tab_debate, tab_contradictions, tab_drift, tab_trace = st.tabs(
    ["📄 Memo", "⚖️ Bull vs Bear", "⚠️ Contradictions", "📈 Thesis Drift", "🔍 Trace"]
)

with tab_memo:
    if memo:
        st.subheader(f"Research Memo — {ticker}")
        st.markdown(f"**Summary:** {memo.get('research_summary', '')}")
        st.markdown(f"**Bull Case:** {memo.get('bull_case', '')}")
        st.markdown(f"**Bear Case:** {memo.get('bear_case', '')}")
        st.markdown(f"**Synthesis:** {memo.get('moderator_synthesis', '')}")
        if memo.get("scenarios"):
            st.markdown("**Scenarios (analytical framework, not advice):**")
            for s in memo["scenarios"]:
                st.markdown(f"- {s}")
        if memo.get("contradictions_detected"):
            st.markdown("**Contradictions Detected:**")
            for c in memo["contradictions_detected"]:
                st.markdown(f"- {c}")
        if memo.get("contradiction_resolutions"):
            st.markdown("**Contradiction Resolutions:**")
            for r in memo["contradiction_resolutions"]:
                st.markdown(f"- {r}")
        if memo.get("unresolved_questions"):
            st.markdown("**Unresolved Questions:**")
            for q in memo["unresolved_questions"]:
                st.markdown(f"- {q}")
        if memo.get("thesis_drift_summary"):
            st.markdown(f"**Thesis Drift:** {memo['thesis_drift_summary']}")
        st.markdown(f"**Confidence Notes:** {memo.get('confidence_notes', '')}")
        with st.expander("Citations"):
            for c in memo.get("citations", []):
                st.markdown(f"- `{c}`")

with tab_debate:
    bull_col, bear_col = st.columns(2)
    bull_points = artifacts.get("bull_points", [])
    bear_points = artifacts.get("bear_points", [])
    with bull_col:
        st.subheader("🐂 Bull Case")
        for p in bull_points:
            with st.expander(f"{p['claim']} (conf: {p['confidence']:.0%})"):
                st.markdown(p["rationale"])
                if p.get("evidence_span_ids"):
                    st.caption(f"Evidence: {', '.join(p['evidence_span_ids'])}")
    with bear_col:
        st.subheader("🐻 Bear Case")
        for p in bear_points:
            with st.expander(f"{p['claim']} (conf: {p['confidence']:.0%})"):
                st.markdown(p["rationale"])

with tab_contradictions:
    all_contradictions = (
        artifacts.get("evidence_contradictions", []) +
        artifacts.get("debate_contradictions", [])
    )
    if not all_contradictions:
        st.info("No contradictions detected.")
    else:
        severity_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        for c in all_contradictions:
            sev = c.get("severity", "low")
            icon = severity_color.get(sev, "⚪")
            with st.container(border=True):
                st.markdown(f"{icon} **{sev.upper()}** — {c.get('rationale', '')}")
                st.markdown(f"- **Claim A:** {c.get('claim_a', '')}")
                st.markdown(f"- **Claim B:** {c.get('claim_b', '')}")
                st.caption(f"Status: {c.get('status', 'open')}")
        with st.expander("Raw contradiction table"):
            import pandas as pd
            st.dataframe(pd.DataFrame(all_contradictions))

with tab_drift:
    thesis_drift_resp = requests.get(f"{BACKEND_URL}/ticker/{ticker}/thesis-drift")
    drift_data = thesis_drift_resp.json() if thesis_drift_resp.ok else {}

    if "message" in drift_data:
        st.info(drift_data["message"])
    else:
        delta = artifacts.get("thesis_delta")
        if not delta:
            st.info(f"No prior run found for {ticker} — thesis drift will be available after the second run.")
        else:
            col_s, col_w, col_n, col_d = st.columns(4)
            col_s.metric("Strengthened", len(delta.get("strengthened", [])))
            col_w.metric("Weakened", len(delta.get("weakened", [])))
            col_n.metric("New", len(delta.get("new", [])))
            col_d.metric("Disappeared", len(delta.get("disappeared", [])))

            for label, items, color in [
                ("✅ Strengthened", delta.get("strengthened", []), "green"),
                ("📉 Weakened", delta.get("weakened", []), "red"),
                ("🆕 New", delta.get("new", []), "blue"),
                ("👻 Disappeared", delta.get("disappeared", []), "gray"),
            ]:
                if items:
                    st.markdown(f"**{label}**")
                    for item in items:
                        st.markdown(f"- {item}")

            drifts = delta.get("confidence_drift", [])
            if drifts:
                import pandas as pd
                import matplotlib.pyplot as plt
                df = pd.DataFrame(drifts)
                fig, ax = plt.subplots(figsize=(8, max(3, len(df) * 0.4)))
                colors = ["green" if d > 0 else "red" for d in df["delta"]]
                ax.barh(df["topic"], df["delta"], color=colors)
                ax.axvline(0, color="black", linewidth=0.8)
                ax.set_xlabel("Confidence Delta")
                ax.set_title("Confidence Drift by Topic")
                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

with tab_trace:
    st.subheader("Agent Execution Trace")
    for agent in AGENT_ORDER:
        status = st.session_state["agent_status"].get(agent, "pending")
        summary = st.session_state["agent_summary"].get(agent, "")
        timing = st.session_state["agent_timing"].get(agent, "")
        if status == "completed":
            label = f"✅ {agent} — {summary} ({timing}s)"
        elif status == "failed":
            label = f"❌ {agent} — FAILED"
        else:
            label = f"⬜ {agent} — {status}"
        with st.expander(label, expanded=False):
            artifact = st.session_state["artifacts"].get(agent)
            if artifact:
                st.json(artifact)
            else:
                st.caption("No artifact recorded.")
