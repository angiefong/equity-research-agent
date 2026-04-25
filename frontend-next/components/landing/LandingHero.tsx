"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";

const EXAMPLES = [
  "NVDA — earnings preview",
  "TSLA — thesis drift YTD",
  "META — bear case on AI capex",
  "SHOP — long-term outlook",
];

export function LandingHero() {
  const router = useRouter();
  const [ticker, setTicker] = useState("AAPL");
  const [query, setQuery] = useState("Build a bull and bear case for AAPL");

  function start() {
    const params = new URLSearchParams({ ticker, query });
    router.push(`/run/new?${params.toString()}`);
  }

  return (
    <div className="px-5 pt-9 pb-7 border-b-2 border-ink">
      <div className="label-tiny mb-2.5">★ MULTI-AGENT EQUITY RESEARCH</div>
      <h1 className="font-extrabold text-[44px] leading-[1.05] tracking-big mb-3.5 max-w-[18ch]">
        A 14-agent research desk for <span className="bg-accent px-1.5 box-decoration-clone">any ticker</span>, in 2 minutes.
      </h1>
      <p className="text-[14px] text-[#444] leading-[1.55] max-w-[56ch] mb-5">
        Type a ticker and a question. Watch fourteen specialized agents fetch filings, news, and market data, debate bull and bear, surface contradictions, and assemble a verifiable research memo.
      </p>
      <div className="grid grid-cols-[120px_1fr_auto] border-2 border-ink">
        <input
          value={ticker}
          onChange={e => setTicker(e.target.value.toUpperCase())}
          className="px-3.5 py-3 text-[14px] font-mono font-bold border-r-[1.5px] border-ink focus:outline-none focus:bg-accentSoft"
          placeholder="AAPL"
        />
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          className="px-3.5 py-3 text-[14px] border-r-[1.5px] border-ink focus:outline-none focus:bg-accentSoft"
          placeholder="Build a bull and bear case for AAPL"
        />
        <button
          onClick={start}
          className="bg-ink text-paper font-extrabold text-[11px] uppercase tracking-[1.5px] px-6 hover:bg-accent hover:text-ink"
        >
          Run Research →
        </button>
      </div>
      <div className="flex gap-2 mt-3 flex-wrap">
        {EXAMPLES.map(ex => (
          <span key={ex} className="font-mono text-[10px] px-2 py-1 border border-ink bg-inset cursor-pointer hover:bg-accent">
            {ex}
          </span>
        ))}
      </div>
    </div>
  );
}
