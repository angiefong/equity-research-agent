type Props = {
  bullWeight: number;
  bearWeight: number;
  bullClaims: number;
  bearClaims: number;
};

export function WeightBar({ bullWeight, bearWeight, bullClaims, bearClaims }: Props) {
  const total = bullWeight + bearWeight || 1;
  const bullPct = (bullWeight / total) * 100;

  return (
    <div className="bg-inset border-y-2 border-ink p-5">
      <div className="flex justify-between mb-2 items-baseline">
        <div>
          <div className="label-section text-bull">↗ BULL</div>
          <div className="font-mono font-extrabold text-[18px] text-bull">{bullWeight.toFixed(2)}</div>
        </div>
        <div className="text-right">
          <div className="label-section text-bear">BEAR ↘</div>
          <div className="font-mono font-extrabold text-[18px] text-bear">{bearWeight.toFixed(2)}</div>
        </div>
      </div>
      <div className="relative pt-5">
        <div className="relative h-9 border-2 border-ink flex">
          <div
            data-side="bull"
            className="relative"
            style={{
              width: `${bullPct}%`,
              background: "repeating-linear-gradient(45deg, #006633 0 4px, #00773c 4px 8px)",
            }}
          />
          <div
            data-side="bear"
            className="relative"
            style={{
              width: `${100 - bullPct}%`,
              background: "repeating-linear-gradient(45deg, #B40000 0 4px, #c41010 4px 8px)",
            }}
          />
          <div
            className="absolute -top-2 -bottom-2 w-1 bg-accent border-x-[1.5px] border-ink"
            style={{ left: `${bullPct}%`, transform: "translateX(-50%)" }}
          >
            <span className="absolute -top-4 left-1/2 -translate-x-1/2 text-[14px]">★</span>
          </div>
        </div>
        <div className="flex justify-between mt-2 font-mono text-[9px] text-muted">
          <span>{bullClaims} BULL CLAIMS</span>
          <span>{bearClaims} BEAR CLAIMS</span>
        </div>
      </div>
    </div>
  );
}
