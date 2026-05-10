export type MatrixClaim = { side: "bull" | "bear"; topic: string; confidence: number };
type Props = { claims: MatrixClaim[] };

function tileClass(c: MatrixClaim): string {
  const high = c.confidence >= 0.8;
  const mid = c.confidence >= 0.6;
  if (c.side === "bull") {
    if (high) return "bg-bull text-paper";
    if (mid) return "bg-[#4DA77A] text-paper";
    return "bg-[#E8F5EE] text-ink";
  } else {
    if (high) return "bg-bear text-paper";
    if (mid) return "bg-[#D26060] text-paper";
    return "bg-[#FBE9E9] text-ink";
  }
}

export function ThesisMatrix({ claims }: Props) {
  return (
    <div>
      <div className="grid grid-cols-6 border-[1.5px] border-ink">
        {claims.map((c, i) => {
          const isLastInRow = (i + 1) % 6 === 0;
          return (
            <div
              key={`${c.topic}-${i}`}
              className={`p-2 ${isLastInRow ? "" : "border-r"} border-b border-ink min-h-[64px] flex flex-col justify-between text-[10px] ${tileClass(c)}`}
            >
              <div className="font-bold uppercase text-[9px] tracking-wider">{c.topic}</div>
              <div className="font-mono text-[9px] opacity-90 mt-1">
                {c.side.toUpperCase()} · {c.confidence.toFixed(2)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
