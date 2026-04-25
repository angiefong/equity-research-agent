import { PriceChart } from "@/components/viz/PriceChart";

type Props = {
  ticker: string;
  companyLine: string;
  price: number;
  changeAbs: number;
  changePct: number;
  verdict: string;
  high52w: number;
  low52w: number;
  series: { date: string; price: number }[];
};

export function MemoHero({ ticker, companyLine, price, changeAbs, changePct, verdict, high52w, low52w, series }: Props) {
  const up = changeAbs >= 0;
  return (
    <div className="grid grid-cols-[280px_1fr] gap-6 items-center px-5 py-5 border-b-2 border-ink">
      <div>
        <div className="font-extrabold text-[56px] leading-[0.9] tracking-big">{ticker}</div>
        <div className="text-[11px] text-muted mt-1 uppercase tracking-wider">{companyLine}</div>
        <div className="font-mono font-extrabold text-[26px] mt-3.5">${price.toFixed(2)}</div>
        <div className={`font-mono text-[12px] mt-0.5 ${up ? "text-bull" : "text-bear"}`}>
          {up ? "+" : ""}${changeAbs.toFixed(2)} ({up ? "+" : ""}{changePct.toFixed(2)}%) {up ? "▲" : "▼"}
        </div>
        <div className="inline-block mt-3 px-2.5 py-1 bg-accent border-[1.5px] border-ink text-[10px] font-extrabold uppercase tracking-[2px]">
          ★ {verdict}
        </div>
      </div>
      <PriceChart data={series} high52w={high52w} low52w={low52w} current={price} />
    </div>
  );
}
