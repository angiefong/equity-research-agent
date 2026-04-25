"use client";
import { Suspense, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { useRunStream } from "@/lib/useRunStream";

function NewRunInner() {
  const params = useSearchParams();
  const router = useRouter();
  const ticker = params.get("ticker") || "";
  const query = params.get("query") || "";
  const url = ticker && query ? api.streamUrl(ticker, query) : null;
  const state = useRunStream(url);

  useEffect(() => {
    if (state.runId) router.replace(`/run/${state.runId}?ticker=${encodeURIComponent(ticker)}&query=${encodeURIComponent(query)}`);
  }, [state.runId, ticker, query, router]);

  return (
    <main className="b-frame max-w-[920px] mx-auto my-6 p-6">
      <p className="font-mono text-[12px]">Starting run for {ticker}…</p>
    </main>
  );
}

export default function NewRunPage() {
  return (
    <Suspense fallback={<main className="b-frame max-w-[920px] mx-auto my-6 p-6"><p className="font-mono text-[12px]">Starting run…</p></main>}>
      <NewRunInner />
    </Suspense>
  );
}
