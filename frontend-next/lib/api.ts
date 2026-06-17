import type { Artifacts, ResearchMemo, RunSummary } from "./types";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

function withAccess(path: string, accessCode?: string): string {
  if (!accessCode) return path;
  const sep = path.includes("?") ? "&" : "?";
  return `${path}${sep}access_code=${encodeURIComponent(accessCode)}`;
}

async function get<T>(path: string, accessCode?: string): Promise<T> {
  const resp = await fetch(`${BACKEND}${withAccess(path, accessCode)}`, { cache: "no-store" });
  if (!resp.ok) throw new Error(`${resp.status} on ${path}`);
  return resp.json() as Promise<T>;
}

export const api = {
  recentRuns: (limit = 10, accessCode?: string) => get<RunSummary[]>(`/runs?limit=${limit}`, accessCode),
  memo: (runId: string, accessCode?: string) => get<ResearchMemo>(`/run/${runId}/memo`, accessCode),
  artifacts: (runId: string, accessCode?: string) => get<Artifacts>(`/run/${runId}/artifacts`, accessCode),
  streamUrl: (ticker: string, query: string, accessCode?: string) =>
    `${BACKEND}${withAccess(`/run/stream?ticker=${encodeURIComponent(ticker)}&query=${encodeURIComponent(query)}`, accessCode)}`,
};
