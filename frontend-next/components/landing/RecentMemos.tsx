import Link from "next/link";
import type { RunSummary } from "@/lib/types";

function MiniBar({ bw, br }: { bw: number; br: number }) {
  const total = bw + br || 1;
  return (
    <div className="flex h-1 mt-2.5 border border-ink">
      <div className="bg-bull" style={{ width: `${(bw / total) * 100}%` }} />
      <div className="bg-bear" style={{ width: `${(br / total) * 100}%` }} />
    </div>
  );
}

function pillClass(verdict: string): string {
  if (verdict.includes("Bull")) return "bg-accent";
  if (verdict.includes("Bear")) return "bg-[#FBE9E9]";
  return "bg-[#f5f5f5]";
}

function fmtDate(s: string | undefined | null): string {
  if (!s) return "—";
  const d = new Date(s);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toISOString().slice(0, 10);
}

export function RecentMemos({ runs }: { runs: RunSummary[] }) {
  const padded = runs.slice(0, 3);
  return (
    <section className="px-5 py-6 border-b-2 border-ink">
      <div className="label-section mb-3.5 pb-1.5 border-b-[1.5px] border-ink flex justify-between">
        <span>Recent Memos</span>
        <span className="font-mono normal-case tracking-normal text-muted">view all →</span>
      </div>
      <div className="grid grid-cols-3 border-[1.5px] border-ink">
        {padded.map((r, i) => (
          <Link
            key={r.run_id}
            href={`/memo/${r.run_id}`}
            className={`p-3.5 ${i < 2 ? "border-r border-ink" : ""} hover:bg-accentSoft`}
          >
            <div className="font-extrabold text-[26px] leading-none tracking-big">{r.ticker}</div>
            <div className={`inline-block mt-1.5 px-1.5 py-0.5 text-[8px] font-extrabold uppercase tracking-[1.5px] border-[1.5px] border-ink ${pillClass(r.verdict)}`}>
              ★ {r.verdict}
            </div>
            <div className="text-[11px] leading-[1.4] text-[#333] mt-2">{r.lede}</div>
            <MiniBar bw={r.bull_weight ?? 0} br={r.bear_weight ?? 0} />
            <div className="font-mono text-[9px] text-muted mt-2">
              {fmtDate(r.created_at)} · {Math.round(r.duration_s ?? 0)}s · {r.agent_count} agents
            </div>
          </Link>
        ))}
        {padded.length === 0 && (
          <div className="col-span-3 p-6 text-center text-muted text-[12px]">
            No runs yet. Start one above.
          </div>
        )}
      </div>
    </section>
  );
}
