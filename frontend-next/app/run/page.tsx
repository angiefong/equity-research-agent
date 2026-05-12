"use client";
import { Suspense, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { useRunStream } from "@/lib/useRunStream";
import { Topbar } from "@/components/ui/Topbar";
import { RunHeader } from "@/components/run/RunHeader";
import { FocusCard } from "@/components/run/FocusCard";
import { BuildLog } from "@/components/run/BuildLog";
import { PipelineDAG } from "@/components/viz/PipelineDAG";
import type { AgentStatus } from "@/lib/types";

const AGENT_ORDER = [
  "supervisor", "market_data", "filings", "news", "quant_data",
  "quant_interpretation", "evidence_contradiction",
  "bull", "bear", "debate_contradiction",
  "verifier", "reroute", "thesis_replay", "moderator", "snapshot_writer",
] as const;

function RunPageInner() {
  const search = useSearchParams();
  const router = useRouter();
  const ticker = search.get("ticker") || "";
  const query = search.get("query") || "";
  const urlRunId = search.get("runId");
  const url = ticker && query ? api.streamUrl(ticker, query) : null;
  const state = useRunStream(url);

  const [, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(id);
  }, []);

  // Reflect run_id into the URL once so it's shareable, without re-mounting.
  useEffect(() => {
    if (state.runId && state.runId !== urlRunId) {
      const next = new URLSearchParams({ ticker, query, runId: state.runId });
      router.replace(`/run?${next.toString()}`);
    }
  }, [state.runId, urlRunId, ticker, query, router]);

  // On completion, navigate to the memo viewer.
  useEffect(() => {
    if (state.status !== "completed" || !state.runId) return;
    const id = setTimeout(() => {
      router.replace(`/memo/${state.runId}`);
    }, 800);
    return () => clearTimeout(id);
  }, [state.status, state.runId, router]);

  const elapsed = state.startedAt ? Math.round((Date.now() - state.startedAt) / 1000) : 0;
  const min = Math.floor(elapsed / 60).toString().padStart(2, "0");
  const sec = (elapsed % 60).toString().padStart(2, "0");
  const done = AGENT_ORDER.filter(n => state.agents[n]?.status === "completed").length;

  const runningAgent = AGENT_ORDER.find(n => state.agents[n]?.status === "running") ?? null;
  const runningSince = runningAgent ? state.agents[runningAgent]?.startedAt ?? null : null;
  const runningElapsed = runningSince ? Date.now() / 1000 - runningSince : null;

  const focusLines = useMemo(() => state.log.slice(-6).map(l => `${l.agent} ${l.type}: ${l.message}`), [state.log]);

  const rows = AGENT_ORDER.map(name => {
    const ag = state.agents[name];
    const status: AgentStatus = ag?.status ?? "pending";
    return { agent: name, status, summary: ag?.summary, elapsedS: ag?.elapsedS };
  });

  const runIdShort = state.runId ? state.runId.slice(0, 8) : "—";

  return (
    <main className="b-frame max-w-[920px] mx-auto my-6">
      <Topbar
        left={`Live Run · run_id ${runIdShort}…`}
        right={`${new Date().toISOString().replace("T", " ").slice(0, 19)} · ${state.status}`}
      />
      <RunHeader
        ticker={ticker}
        query={query}
        stats={[
          { label: "Elapsed", value: `${min}:${sec}` },
          { label: "Done", value: `${done}/${AGENT_ORDER.length}` },
          { label: "Failed", value: `${state.failed}` },
          { label: "Reroutes", value: `${state.reroutes}` },
        ]}
      />
      <div className="px-5 py-4 border-b-2 border-ink bg-inset">
        <div className="label-section mb-2.5 pb-1.5 border-b-[1.5px] border-ink flex justify-between">
          <span>Pipeline</span>
          <span className="font-mono normal-case tracking-normal text-muted">{AGENT_ORDER.length} agents · streaming via SSE</span>
        </div>
        <PipelineDAG agents={state.agents} />
      </div>
      <FocusCard agent={runningAgent} elapsedS={runningElapsed} lines={focusLines} />
      <BuildLog rows={rows} />
    </main>
  );
}

export default function RunPage() {
  return (
    <Suspense fallback={<main className="b-frame max-w-[920px] mx-auto my-6 p-6"><p className="font-mono text-[12px]">Loading…</p></main>}>
      <RunPageInner />
    </Suspense>
  );
}
