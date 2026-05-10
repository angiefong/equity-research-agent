import type { Artifacts, ResearchMemo, RunSummary } from "./types";

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

async function get<T>(path: string): Promise<T> {
  const resp = await fetch(`${BACKEND}${path}`, { cache: "no-store" });
  if (!resp.ok) throw new Error(`${resp.status} on ${path}`);
  return resp.json() as Promise<T>;
}

export const api = {
  recentRuns: (limit = 10) => get<RunSummary[]>(`/runs?limit=${limit}`),
  memo: (runId: string) => get<ResearchMemo>(`/run/${runId}/memo`),
  artifacts: (runId: string) => get<Artifacts>(`/run/${runId}/artifacts`),
  streamUrl: (ticker: string, query: string) =>
    `${BACKEND}/run/stream?ticker=${encodeURIComponent(ticker)}&query=${encodeURIComponent(query)}`,
};
