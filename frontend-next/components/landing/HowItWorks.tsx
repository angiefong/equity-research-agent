const AGENTS: { name: string; hero?: boolean }[] = [
  { name: "SUPERVISOR" }, { name: "MARKET" }, { name: "FILINGS" },
  { name: "NEWS" }, { name: "QUANT" }, { name: "QUANT INTERP" },
  { name: "EV CONTR" }, { name: "BULL", hero: true }, { name: "BEAR", hero: true },
  { name: "DEBATE CONTR" }, { name: "VERIFIER" }, { name: "REROUTE" },
  { name: "THESIS REPLAY" }, { name: "MODERATOR", hero: true },
];

export function HowItWorks() {
  return (
    <section className="px-5 py-6">
      <div className="label-section mb-3.5 pb-1.5 border-b-[1.5px] border-ink flex justify-between">
        <span>How it works</span>
        <span className="font-mono normal-case tracking-normal text-muted">→ /run/[id]</span>
      </div>
      <div className="grid grid-cols-7 border-[1.5px] border-ink">
        {AGENTS.map((a, i) => {
          const lastCol = (i + 1) % 7 === 0;
          const lastRow = i >= AGENTS.length - 7;
          return (
            <div
              key={a.name}
              className={`px-1 py-1.5 text-[8px] font-bold uppercase tracking-wider text-center min-h-[38px] flex items-center justify-center ${a.hero ? "bg-accent" : "bg-inset"} ${lastCol ? "" : "border-r border-ink"} ${lastRow ? "" : "border-b border-ink"}`}
            >
              {a.name}
            </div>
          );
        })}
      </div>
      <p className="text-[11px] text-muted mt-2.5 leading-[1.5] max-w-[56ch]">
        Each agent has one job. The verifier checks every claim against source evidence; the reroute loop re-fetches data when claims fail verification. The moderator assembles the final memo with citations.
      </p>
    </section>
  );
}
