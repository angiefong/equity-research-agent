import type { AgentStatus } from "@/lib/types";

type Row = { agent: string; status: AgentStatus; summary?: string; elapsedS?: number };
type Props = { rows: Row[] };

const ICON: Record<AgentStatus, string> = { pending: "○", running: "⚡", completed: "✓", failed: "✗" };

const ROW_BG: Record<AgentStatus, string> = {
  pending: "text-[#aaa]",
  running: "bg-accentSoft font-semibold text-ink",
  completed: "text-[#444]",
  failed: "bg-[#FBE9E9] text-bear",
};

export function BuildLog({ rows }: Props) {
  return (
    <div className="px-5 py-4">
      <div className="label-section mb-2.5 pb-1.5 border-b-[1.5px] border-ink flex justify-between">
        <span>Build Log</span>
        <span className="font-mono normal-case tracking-normal text-muted">{rows.length} steps</span>
      </div>
      <div className="border-[1.5px] border-ink max-h-[320px] overflow-auto font-mono text-[11px]">
        {rows.map((r, i) => (
          <div
            key={i}
            className={`grid grid-cols-[24px_140px_1fr_56px] gap-3 px-2.5 py-1.5 border-b border-[#eee] items-center ${ROW_BG[r.status]}`}
          >
            <span className="text-center font-extrabold">{ICON[r.status]}</span>
            <span className="font-bold">{r.agent}</span>
            <span className="font-sans text-[11px]">{r.summary ?? "—"}</span>
            <span className="text-right text-muted text-[10px]">
              {r.elapsedS != null ? `${r.elapsedS.toFixed(1)}s` : r.status === "running" ? "+…" : "—"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
