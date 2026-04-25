import Link from "next/link";

export function Nav({ active }: { active?: "research" | "history" | "how" }) {
  const linkClass = (key: string) =>
    `text-[11px] font-bold uppercase tracking-[1.5px] pb-0.5 ${active === key ? "border-b-2 border-ink" : ""}`;
  return (
    <div className="border-b-2 border-ink px-5 py-3.5 flex justify-between items-center">
      <Link href="/" className="font-extrabold text-[18px] tracking-display">
        EQUITY<span className="text-accent" style={{ WebkitTextStroke: "1px #000" }}>.</span>RESEARCH
      </Link>
      <div className="flex gap-4">
        <Link href="/" className={linkClass("research")}>RESEARCH</Link>
        <Link href="#" className={linkClass("history")}>HISTORY</Link>
        <Link href="#" className={linkClass("how")}>HOW IT WORKS</Link>
      </div>
    </div>
  );
}
