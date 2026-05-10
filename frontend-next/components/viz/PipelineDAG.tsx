import type { AgentStatus } from "@/lib/types";

type AgentMap = Record<string, { status: AgentStatus; elapsedS?: number }>;

const LAYOUT = {
  supervisor:            { x: 10,  y: 110, w: 70, h: 40 },
  market_data:           { x: 105, y: 20,  w: 75, h: 40, label: "MARKET" },
  filings:               { x: 105, y: 70,  w: 75, h: 40 },
  news:                  { x: 105, y: 140, w: 75, h: 40 },
  quant_data:            { x: 105, y: 190, w: 75, h: 40, label: "QUANT" },
  quant_interpretation:  { x: 205, y: 110, w: 85, h: 40, label: "Q.INTERP" },
  evidence_contradiction:{ x: 315, y: 110, w: 70, h: 40, label: "EV CONTR" },
  bull:                  { x: 415, y: 60,  w: 60, h: 40 },
  bear:                  { x: 415, y: 160, w: 60, h: 40 },
  debate_contradiction:  { x: 500, y: 110, w: 70, h: 40, label: "DEBATE" },
  verifier:              { x: 600, y: 110, w: 65, h: 40 },
  reroute:               { x: 600, y: 200, w: 65, h: 40 },
  thesis_replay:         { x: 695, y: 110, w: 75, h: 40, label: "REPLAY" },
  moderator:             { x: 800, y: 110, w: 75, h: 40 },
} as const;

const EDGES: { from: keyof typeof LAYOUT; to: keyof typeof LAYOUT }[] = [
  { from: "supervisor", to: "market_data" },
  { from: "supervisor", to: "filings" },
  { from: "supervisor", to: "news" },
  { from: "supervisor", to: "quant_data" },
  { from: "market_data", to: "quant_interpretation" },
  { from: "filings", to: "quant_interpretation" },
  { from: "news", to: "quant_interpretation" },
  { from: "quant_data", to: "quant_interpretation" },
  { from: "quant_interpretation", to: "evidence_contradiction" },
  { from: "evidence_contradiction", to: "bull" },
  { from: "evidence_contradiction", to: "bear" },
  { from: "bull", to: "debate_contradiction" },
  { from: "bear", to: "debate_contradiction" },
  { from: "debate_contradiction", to: "verifier" },
  { from: "verifier", to: "reroute" },
  { from: "verifier", to: "thesis_replay" },
  { from: "thesis_replay", to: "moderator" },
];

function fillFor(status: AgentStatus | undefined): string {
  switch (status) {
    case "running": return "#FFE100";
    case "completed": return "#E8F5EE";
    case "failed": return "#FBE9E9";
    default: return "#f5f5f5";
  }
}

function strokeWidthFor(status: AgentStatus | undefined): number {
  return status === "running" ? 2.5 : 1.5;
}

function edgePath(a: typeof LAYOUT[keyof typeof LAYOUT], b: typeof LAYOUT[keyof typeof LAYOUT]): string {
  const x1 = a.x + a.w, y1 = a.y + a.h / 2;
  const x2 = b.x, y2 = b.y + b.h / 2;
  return `M ${x1},${y1} L ${x2},${y2}`;
}

export function PipelineDAG({ agents }: { agents: AgentMap }) {
  return (
    <div className="bg-paper border-[1.5px] border-ink p-3 h-[280px]">
      <svg viewBox="0 0 890 260" className="w-full h-full">
        {EDGES.map((e, i) => {
          const fromStatus = agents[e.from]?.status;
          const toStatus = agents[e.to]?.status;
          const dashed = fromStatus !== "completed";
          return (
            <path
              key={i}
              d={edgePath(LAYOUT[e.from], LAYOUT[e.to])}
              stroke={dashed ? "#ccc" : "#000"}
              strokeWidth={toStatus === "running" ? 2 : 1}
              strokeDasharray={dashed ? "3,3" : undefined}
              fill="none"
            />
          );
        })}
        {(Object.keys(LAYOUT) as (keyof typeof LAYOUT)[]).map(name => {
          const node = LAYOUT[name];
          const ag = agents[name];
          const label = ("label" in node && node.label) ? node.label : name.toUpperCase();
          return (
            <g key={name}>
              <rect
                x={node.x} y={node.y} width={node.w} height={node.h} rx={2}
                fill={fillFor(ag?.status)} stroke="#000" strokeWidth={strokeWidthFor(ag?.status)}
              />
              <text
                x={node.x + node.w / 2} y={node.y + node.h / 2 + 1}
                textAnchor="middle"
                style={{ fontFamily: "Inter, sans-serif", fontSize: 9, fontWeight: 700, letterSpacing: "0.5px" }}
              >
                {label}{ag?.status === "running" ? " ⚡" : ""}
              </text>
              <text
                x={node.x + node.w / 2} y={node.y + node.h / 2 + 14}
                textAnchor="middle"
                style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 8, fill: "#666" }}
              >
                {ag?.elapsedS ? `${ag.elapsedS.toFixed(1)}s` : "—"}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
