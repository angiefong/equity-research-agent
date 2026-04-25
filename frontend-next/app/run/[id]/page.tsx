"use client";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { useRunStream } from "@/lib/useRunStream";

function RunInner({ id }: { id: string }) {
  const search = useSearchParams();
  const ticker = search.get("ticker") || "";
  const query = search.get("query") || "";
  const url = ticker && query ? api.streamUrl(ticker, query) : null;
  const state = useRunStream(url);

  return (
    <main className="b-frame max-w-[920px] mx-auto my-6 p-6 font-mono text-[11px]">
      <p>run_id: {id}</p>
      <p>status: {state.status}</p>
      <p>reroutes: {state.reroutes}</p>
      <p>failed: {state.failed}</p>
      <p>agents seen: {Object.keys(state.agents).length} / 14</p>
    </main>
  );
}

export default function RunPage({ params }: { params: { id: string } }) {
  return (
    <Suspense fallback={<main className="b-frame max-w-[920px] mx-auto my-6 p-6 font-mono text-[11px]"><p>run_id: {params.id}</p></main>}>
      <RunInner id={params.id} />
    </Suspense>
  );
}
