"use client";
import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { useRunStream } from "@/lib/useRunStream";

function RunPageInner() {
  const params = useSearchParams();
  const router = useRouter();
  const ticker = params.get("ticker") || "";
  const query = params.get("query") || "";
  const urlRunId = params.get("runId");
  const url = ticker && query ? api.streamUrl(ticker, query) : null;
  const state = useRunStream(url);

  useEffect(() => {
    if (state.runId && state.runId !== urlRunId) {
      const next = new URLSearchParams({ ticker, query, runId: state.runId });
      router.replace(`/run?${next.toString()}`);
    }
  }, [state.runId, urlRunId, ticker, query, router]);

  useEffect(() => {
    if (state.status === "completed" && state.runId) {
      router.replace(`/memo/${state.runId}`);
    }
  }, [state.status, state.runId, router]);

  if (!state.runId) {
    return (
      <main className="b-frame max-w-[920px] mx-auto my-6 p-6">
        <p className="font-mono text-[12px]">Starting run for {ticker}…</p>
      </main>
    );
  }

  return (
    <main className="b-frame max-w-[920px] mx-auto my-6 p-6 font-mono text-[11px]">
      <p>run_id: {state.runId}</p>
      <p>status: {state.status}</p>
      <p>reroutes: {state.reroutes}</p>
      <p>failed: {state.failed}</p>
      <p>agents seen: {Object.keys(state.agents).length} / 14</p>
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
