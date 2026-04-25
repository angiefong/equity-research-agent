import type { ClaimPoint } from "@/lib/types";

type Props = {
  bullPoints: ClaimPoint[];
  bearPoints: ClaimPoint[];
};

function ClaimColumn({ side, points }: { side: "bull" | "bear"; points: ClaimPoint[] }) {
  const isBull = side === "bull";
  const avg = points.length
    ? points.reduce((a, b) => a + b.confidence, 0) / points.length
    : 0;
  return (
    <div className={`px-4 py-4 ${isBull ? "" : "border-l-[1.5px] border-ink"}`}>
      <div className="flex justify-between items-baseline mb-3 pb-2 border-b-[1.5px] border-ink">
        <span className={`label-section ${isBull ? "text-bull" : "text-bear"}`}>
          {isBull ? "↗ Bull Case" : "↘ Bear Case"}
        </span>
        <span className="font-mono text-[10px]">avg conf {avg.toFixed(2)}</span>
      </div>
      {points.map((p, i) => (
        <div key={i} className="py-3 b-hairline last:border-b-0 last:pb-0 first:pt-0 text-[12px] leading-[1.6]">
          <div className="flex justify-between items-baseline gap-2.5 mb-1.5">
            <span className="font-bold text-[13px]">{p.claim}</span>
            <span className="font-mono text-[9px] text-muted shrink-0">{p.confidence.toFixed(2)}</span>
          </div>
          <div className="text-[#222]">{p.rationale}</div>
          {p.evidence_span_ids?.length ? (
            <div className="font-mono text-[9px] text-muted mt-1.5 pt-1.5 border-t border-[#f0f0f0]">
              ↳ {p.evidence_span_ids.join(" · ")}
            </div>
          ) : null}
        </div>
      ))}
    </div>
  );
}

export function ClaimGrid({ bullPoints, bearPoints }: Props) {
  return (
    <div className="grid grid-cols-2 border-b-2 border-ink">
      <ClaimColumn side="bull" points={bullPoints} />
      <ClaimColumn side="bear" points={bearPoints} />
    </div>
  );
}
