type Props = { contradictions: number; unresolved: number; agentCount: number; sourceCount: number; durationS: number };

export function AlertStrip({ contradictions, unresolved, agentCount, sourceCount, durationS }: Props) {
  const min = Math.floor(durationS / 60);
  const sec = Math.round(durationS % 60).toString().padStart(2, "0");
  return (
    <div className="bg-accent border-t-2 border-ink px-5 py-2.5 text-[11px] font-bold uppercase tracking-wider flex justify-between">
      <span>⚠ {contradictions} contradictions detected · {unresolved} unresolved</span>
      <span>{agentCount} agents · {sourceCount} sources · {min}m {sec}s</span>
    </div>
  );
}
