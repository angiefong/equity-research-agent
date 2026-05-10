export type Fact = { label: string; value: string };
type Props = { facts: Fact[] };

export function FactsStrip({ facts }: Props) {
  return (
    <div className="grid border-b-2 border-ink" style={{ gridTemplateColumns: `repeat(${facts.length}, 1fr)` }}>
      {facts.map((f, i) => (
        <div key={f.label} className={`p-3 font-mono ${i < facts.length - 1 ? "border-r border-ink" : ""}`}>
          <div className="label-tiny mb-1">{f.label}</div>
          <div className="text-[14px] font-bold">{f.value}</div>
        </div>
      ))}
    </div>
  );
}
