"use client";
import { useEffect, useReducer, useRef } from "react";
import type { AgentStatus } from "@/lib/types";

export type RunState = {
  runId: string | null;
  status: "idle" | "streaming" | "completed" | "failed";
  startedAt: number | null;
  agents: Record<string, { status: AgentStatus; summary?: string; elapsedS?: number; startedAt?: number }>;
  log: { agent: string; type: string; message: string; t: number }[];
  reroutes: number;
  failed: number;
};

type Event =
  | { type: "init" }
  | { type: "started"; runId: string }
  | { type: "agent_started"; agent: string; t: number }
  | { type: "agent_completed"; agent: string; summary: string; elapsedS: number; t: number }
  | { type: "agent_failed"; agent: string; error: string; t: number }
  | { type: "completed" };

function reducer(state: RunState, ev: Event): RunState {
  switch (ev.type) {
    case "init": return state;
    case "started": return { ...state, runId: ev.runId, status: "streaming", startedAt: Date.now() };
    case "agent_started": {
      const agents = { ...state.agents, [ev.agent]: { status: "running" as AgentStatus, startedAt: ev.t } };
      const log = [...state.log, { agent: ev.agent, type: "started", message: "started", t: ev.t }];
      return { ...state, agents, log };
    }
    case "agent_completed": {
      const agents = { ...state.agents, [ev.agent]: { status: "completed" as AgentStatus, summary: ev.summary, elapsedS: ev.elapsedS } };
      const reroutes = ev.agent === "reroute" ? state.reroutes + 1 : state.reroutes;
      const log = [...state.log, { agent: ev.agent, type: "completed", message: ev.summary, t: ev.t }];
      return { ...state, agents, reroutes, log };
    }
    case "agent_failed": {
      const agents = { ...state.agents, [ev.agent]: { status: "failed" as AgentStatus, summary: ev.error } };
      const log = [...state.log, { agent: ev.agent, type: "failed", message: ev.error, t: ev.t }];
      return { ...state, agents, log, failed: state.failed + 1 };
    }
    case "completed": return { ...state, status: "completed" };
  }
}

const initial: RunState = {
  runId: null, status: "idle", startedAt: null, agents: {}, log: [], reroutes: 0, failed: 0,
};

export function useRunStream(streamUrl: string | null): RunState {
  const [state, dispatch] = useReducer(reducer, initial);
  const ref = useRef<EventSource | null>(null);
  useEffect(() => {
    if (!streamUrl) return;
    const es = new EventSource(streamUrl);
    ref.current = es;
    const now = () => Date.now() / 1000;

    es.addEventListener("run_started", (e: MessageEvent) => {
      const d = JSON.parse(e.data); dispatch({ type: "started", runId: d.run_id });
    });
    es.addEventListener("agent_started", (e: MessageEvent) => {
      const d = JSON.parse(e.data); dispatch({ type: "agent_started", agent: d.agent, t: now() });
    });
    es.addEventListener("agent_completed", (e: MessageEvent) => {
      const d = JSON.parse(e.data);
      dispatch({ type: "agent_completed", agent: d.agent, summary: d.summary, elapsedS: d.elapsed_s, t: now() });
    });
    es.addEventListener("agent_failed", (e: MessageEvent) => {
      const d = JSON.parse(e.data); dispatch({ type: "agent_failed", agent: d.agent, error: d.error || "unknown", t: now() });
    });
    es.addEventListener("run_completed", () => { dispatch({ type: "completed" }); es.close(); });
    es.onerror = () => { /* let EventSource auto-reconnect */ };
    return () => { es.close(); };
  }, [streamUrl]);
  return state;
}
