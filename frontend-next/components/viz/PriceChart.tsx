type Point = { date: string; price: number };
type Props = {
  data: Point[];
  high52w: number;
  low52w: number;
  current: number;
};

export function PriceChart({ data, high52w, low52w, current }: Props) {
  const W = 400, H = 180, padTop = 20, padBottom = 20;
  const range = high52w - low52w || 1;

  const points = data.map((p, i) => {
    const x = (i / Math.max(data.length - 1, 1)) * W;
    const y = padTop + ((high52w - p.price) / range) * (H - padTop - padBottom);
    return `${x},${y}`;
  }).join(" ");

  const currentY = padTop + ((high52w - current) / range) * (H - padTop - padBottom);

  return (
    <div className="relative">
      <div className="b-frame border-[1.5px] h-[180px] bg-inset">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          preserveAspectRatio="none"
          className="w-full h-full block"
          role="img"
          aria-label="Price chart"
        >
          <line x1="0" y1={padTop} x2={W} y2={padTop} stroke="#bbb" strokeWidth="0.5" strokeDasharray="3,3" />
          <text x="6" y={padTop - 6} className="fill-[#999] font-sans" style={{ fontSize: 8, letterSpacing: "1px", textTransform: "uppercase" }}>
            52W HIGH {Math.round(high52w)}
          </text>
          <line x1="0" y1={H - padBottom} x2={W} y2={H - padBottom} stroke="#bbb" strokeWidth="0.5" strokeDasharray="3,3" />
          <text x="6" y={H - padBottom + 14} className="fill-[#999] font-sans" style={{ fontSize: 8, letterSpacing: "1px", textTransform: "uppercase" }}>
            52W LOW {Math.round(low52w)}
          </text>
          <polyline points={points} fill="none" stroke="#000" strokeWidth="2.5" strokeLinejoin="round" />
          <circle cx={W} cy={currentY} r="4" fill="#FFE100" stroke="#000" strokeWidth="1.5" />
        </svg>
      </div>
    </div>
  );
}
