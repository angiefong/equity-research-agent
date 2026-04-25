type Stat = { label: string; value: string };

type Props = {
  ticker: string;
  query: string;
  stats: Stat[];
};

export function RunHeader({ ticker, query, stats }: Props) {
  return (
    <div className="px-5 py-3.5 border-b-2 border-ink flex justify-between items-baseline gap-6">
      <div>
        <h3 className="font-extrabold text-[22px] tracking-display m-0">{ticker}</h3>
        <div className="text-[11px] text-muted mt-0.5 italic">&quot;{query}&quot;</div>
      </div>
      <div className="flex gap-5 font-mono text-[11px]">
        {stats.map(s => (
          <div key={s.label}>
            <div className="label-tiny">{s.label}</div>
            <div className="font-extrabold text-[14px]">{s.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
