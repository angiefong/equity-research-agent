export function fmtCompact(n: number): string {
  const abs = Math.abs(n);
  if (abs >= 1e12) return `${(n / 1e12).toFixed(1)}T`;
  if (abs >= 1e9)  return `${(n / 1e9).toFixed(1)}B`;
  if (abs >= 1e6)  return `${(n / 1e6).toFixed(1)}M`;
  if (abs >= 1e3)  return `${(n / 1e3).toFixed(1)}K`;
  return `${n}`;
}

export function fmtPct(fraction: number): string {
  return `${(fraction * 100).toFixed(2)}%`;
}

export function fmtCurrency(n: number): string {
  const sign = n < 0 ? "-" : "";
  return `${sign}$${Math.abs(n).toFixed(2)}`;
}

export function fmtVolume(n: number): string {
  return fmtCompact(n);
}

export function fmtOrDash<T>(v: T | null | undefined, fmt: (x: T) => string): string {
  if (v === null || v === undefined) return "—";
  return fmt(v);
}
