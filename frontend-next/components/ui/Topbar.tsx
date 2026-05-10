type Props = { left: string; right: string };

export function Topbar({ left, right }: Props) {
  return (
    <div className="bg-ink text-paper px-4 py-2.5 flex justify-between items-center text-[10px] uppercase tracking-[2px] border-b-2 border-ink">
      <span>{left}</span>
      <span className="font-mono normal-case tracking-normal">{right}</span>
    </div>
  );
}
