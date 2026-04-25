type Props = { lede: string; paragraphs: string[]; pullQuote?: string };

export function Synthesis({ lede, paragraphs, pullQuote }: Props) {
  return (
    <div className="px-5 py-5 border-b-2 border-ink">
      <p className="text-[17px] leading-[1.5] font-medium mb-3.5">{lede}</p>
      {paragraphs.map((p, i) => (
        <p key={i} className="text-[14px] leading-[1.65] mb-3 max-w-[68ch] last:mb-0">{p}</p>
      ))}
      {pullQuote && (
        <p className="border-l-[3px] border-accent pl-3.5 py-1 italic text-[14px] text-[#333] my-3.5">
          {pullQuote}
        </p>
      )}
    </div>
  );
}
