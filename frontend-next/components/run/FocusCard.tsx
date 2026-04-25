type Props = { agent: string | null; elapsedS: number | null; lines: string[] };

export function FocusCard({ agent, elapsedS, lines }: Props) {
  return (
    <div className="px-5 py-4 border-b-2 border-ink">
      <div className="label-section mb-2.5 pb-1.5 border-b-[1.5px] border-ink flex justify-between">
        <span>Now Running</span>
        <span className="font-mono normal-case tracking-normal text-muted">live tail</span>
      </div>
      <div className="border-[1.5px] border-ink p-3 bg-accentSoft">
        <div className="flex justify-between items-baseline pb-1.5 border-b-[1.5px] border-ink mb-2">
          <span className="font-extrabold text-[12px] uppercase tracking-[1.5px]">
            ⚡ {agent ?? "WAITING"}
          </span>
          <span className="font-mono text-[10px] text-muted">
            {elapsedS != null ? `running ${elapsedS.toFixed(0)}s` : "—"}
          </span>
        </div>
        <div className="font-mono text-[11px] leading-[1.6] text-[#222]">
          {lines.map((l, i) => <div key={i}>&gt; {l}</div>)}
          {agent && <div>&gt; <span className="animate-pulse">▌</span></div>}
        </div>
      </div>
    </div>
  );
}
