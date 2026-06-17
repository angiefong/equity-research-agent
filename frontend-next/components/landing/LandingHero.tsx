"use client";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

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
  const [accessCode, setAccessCode] = useState("");

  useEffect(() => {
    setAccessCode(window.localStorage.getItem("demoAccessCode") || "");
  }, []);

  function start() {
    if (!ticker.trim() || !query.trim()) return;
    const code = accessCode.trim();
    if (code) window.localStorage.setItem("demoAccessCode", code);
    const params = new URLSearchParams({ ticker, query });
    if (code) params.set("access_code", code);
    router.push(`/run?${params.toString()}`);
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
      <form onSubmit={(e) => { e.preventDefault(); start(); }} className="border-2 border-ink">
        <div className="grid grid-cols-[120px_1fr_auto] border-b-[1.5px] border-ink">
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
            type="submit"
            disabled={!ticker.trim() || !query.trim()}
            className="bg-ink text-paper font-extrabold text-[11px] uppercase tracking-[1.5px] px-6 hover:bg-accent hover:text-ink disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Run Research →
          </button>
        </div>
        <input
          value={accessCode}
          onChange={e => setAccessCode(e.target.value)}
          className="w-full px-3.5 py-2.5 text-[12px] font-mono focus:outline-none focus:bg-accentSoft"
          placeholder="Demo access code"
          autoComplete="off"
        />
      </form>
      <div className="flex gap-2 mt-3 flex-wrap">
        {EXAMPLES.map(ex => (
          <button
            key={ex}
            type="button"
            onClick={() => { const { t, q } = pickExample(ex); setTicker(t); setQuery(q); }}
            className="font-mono text-[10px] px-2 py-1 border border-ink bg-inset cursor-pointer hover:bg-accent text-left"
          >
            {ex}
          </button>
        ))}
      </div>
    </div>
  );
}

function pickExample(ex: string) {
  const [t, ...rest] = ex.split(" — ");
  return { t: t.trim().toUpperCase(), q: rest.join(" — ").trim() };
}
