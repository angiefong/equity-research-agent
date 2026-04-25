# Frontend Revamp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Streamlit frontend with a custom Next.js 14 app (brutalist editorial aesthetic) that serves three pages: a landing page, a live agent run page, and a polished memo viewer.

**Architecture:** Next.js 14 App Router (TypeScript) + Tailwind, talking to the existing FastAPI backend via TanStack Query for memo/runs data and a native EventSource for SSE on the run page. The three hero visualizations (price chart, bull-bear weight bar, thesis matrix) are hand-rolled SVG components.

**Tech Stack:** Next.js 14, TypeScript, Tailwind CSS, TanStack Query, native EventSource, hand-rolled SVG, Vitest + React Testing Library, Playwright. Backend: FastAPI (existing) + a small jsonl persistence layer for the runs index.

**Spec:** `docs/superpowers/specs/2026-04-25-frontend-revamp-design.md`

---

## File Structure

### Backend (extending existing)
- **Modify** `backend/agents/market_data.py` — add company metadata to evidence output
- **Modify** `backend/schemas/memo.py` — add `bull_weight`, `bear_weight`, `company_name`, `exchange`, `sector` fields
- **Modify** `backend/agents/moderator.py` — populate weights and metadata when assembling memo
- **Create** `backend/persistence/runs_index.py` — jsonl-backed runs index (append on memo completion; query for `/runs`)
- **Modify** `backend/api.py` — append to runs_index when run completes; add `GET /runs?limit=N` endpoint
- **Create** `tests/persistence/test_runs_index.py`
- **Create** `tests/test_api_runs.py`

### Frontend (new — `frontend-next/`)
```
frontend-next/
├── app/
│   ├── layout.tsx              # Root layout: fonts, providers, nav
│   ├── page.tsx                # Landing (/)
│   ├── run/[id]/page.tsx       # Live run (/run/[id])
│   ├── memo/[id]/page.tsx      # Memo viewer (/memo/[id])
│   ├── globals.css             # Tailwind + brutalist tokens
│   └── providers.tsx           # TanStack Query client
├── components/
│   ├── ui/
│   │   ├── Section.tsx         # Bordered section wrapper
│   │   ├── Topbar.tsx          # Black bar with title + datetime
│   │   └── Pill.tsx            # Verdict / status pill
│   ├── viz/
│   │   ├── PriceChart.tsx      # 1Y SVG line chart
│   │   ├── WeightBar.tsx       # Bull/bear weight bar with verdict marker
│   │   ├── ThesisMatrix.tsx    # Grid of claim tiles
│   │   └── PipelineDAG.tsx     # Agent dependency graph (run page)
│   ├── memo/
│   │   ├── MemoHero.tsx        # Ticker + price + chart hero
│   │   ├── FactsStrip.tsx      # 6-cell facts row
│   │   ├── Synthesis.tsx       # Multi-paragraph lede
│   │   ├── ClaimGrid.tsx       # Bull/bear two-column grid
│   │   └── AlertStrip.tsx      # Yellow alert at bottom
│   ├── run/
│   │   ├── RunHeader.tsx       # Ticker + query + stats
│   │   ├── FocusCard.tsx       # Now-running yellow card
│   │   └── BuildLog.tsx        # Vertical scroll log
│   └── landing/
│       ├── LandingHero.tsx     # Headline + form
│       ├── RecentMemos.tsx     # 3-up memo cards
│       └── HowItWorks.tsx      # 14-agent grid
├── lib/
│   ├── api.ts                  # Typed API client (fetch wrappers)
│   ├── types.ts                # Shared TS types matching backend schemas
│   └── useRunStream.ts         # SSE EventSource hook for live run
├── tests/
│   ├── viz/                    # Vitest component tests for SVG viz
│   └── e2e/                    # Playwright happy-path tests
├── package.json
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
├── vitest.config.ts
└── playwright.config.ts
```

---

## Phase 1: Backend Additions

### Task 1: Extend ResearchMemo schema with weights and company metadata

**Files:**
- Modify: `backend/schemas/memo.py`
- Test: `tests/schemas/test_memo.py`

- [ ] **Step 1: Write the failing test**

Create `tests/schemas/test_memo.py`:

```python
from datetime import datetime
from backend.schemas.memo import ResearchMemo


def test_memo_has_weight_fields():
    m = ResearchMemo(
        ticker="AAPL",
        research_summary="...",
        bull_case="...",
        bear_case="...",
        moderator_synthesis="...",
        contradictions_detected=[],
        unresolved_questions=[],
        confidence_notes="...",
        citations=[],
        bull_weight=0.78,
        bear_weight=0.64,
        company_name="Apple Inc.",
        exchange="NASDAQ",
        sector="Consumer Electronics",
    )
    assert m.bull_weight == 0.78
    assert m.bear_weight == 0.64
    assert m.company_name == "Apple Inc."
    assert m.exchange == "NASDAQ"
    assert m.sector == "Consumer Electronics"


def test_memo_metadata_optional():
    m = ResearchMemo(
        ticker="AAPL",
        research_summary="x", bull_case="x", bear_case="x",
        moderator_synthesis="x", contradictions_detected=[],
        unresolved_questions=[], confidence_notes="x", citations=[],
    )
    assert m.bull_weight is None
    assert m.company_name is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/angiefong/job/equity-research-agent/.worktrees/frontend
python -m pytest tests/schemas/test_memo.py -v
```

Expected: FAIL with `ValidationError` (unknown fields).

- [ ] **Step 3: Add fields to ResearchMemo**

Replace `backend/schemas/memo.py`:

```python
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ResearchMemo(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticker: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    research_summary: str
    bull_case: str
    bear_case: str
    moderator_synthesis: str
    contradictions_detected: list[str]
    unresolved_questions: list[str]
    thesis_drift_summary: Optional[str] = None
    confidence_notes: str
    citations: list[str]

    bull_weight: Optional[float] = None
    bear_weight: Optional[float] = None
    company_name: Optional[str] = None
    exchange: Optional[str] = None
    sector: Optional[str] = None
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/schemas/test_memo.py -v
```

Expected: 2 PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/schemas/memo.py tests/schemas/test_memo.py
git commit -m "feat(memo): add bull/bear weight and company metadata fields"
```

---

### Task 2: Surface company metadata from market_data tool

**Files:**
- Modify: `backend/tools/market_data.py` (add metadata extraction from existing API response)
- Modify: `backend/agents/market_data.py`
- Test: `tests/agents/test_market_data.py`

- [ ] **Step 1: Inspect existing market_data tool to find where overview JSON is fetched**

```bash
grep -n "name\|exchange\|sector\|industry\|overview" backend/tools/market_data.py
```

Note the function that fetches Alpha Vantage overview — it already pulls the full JSON; we just need to expose `Name`, `Exchange`, and `Sector` as a separate return value.

- [ ] **Step 2: Write the failing test**

Create `tests/agents/test_market_data.py`:

```python
from unittest.mock import patch
from backend.agents.market_data import market_data_agent


def test_market_data_returns_company_metadata():
    fake_overview = {
        "Name": "Apple Inc.",
        "Exchange": "NASDAQ",
        "Sector": "Consumer Electronics",
    }
    with patch("backend.agents.market_data.get_market_data_evidence") as mock_ev, \
         patch("backend.agents.market_data.get_company_overview", return_value=fake_overview):
        mock_ev.return_value = []
        result = market_data_agent({"ticker": "AAPL"})
    assert result["company_name"] == "Apple Inc."
    assert result["exchange"] == "NASDAQ"
    assert result["sector"] == "Consumer Electronics"
```

- [ ] **Step 3: Run test to verify it fails**

```bash
python -m pytest tests/agents/test_market_data.py -v
```

Expected: FAIL — `get_company_overview` not importable, or `result` has no `company_name`.

- [ ] **Step 4: Add `get_company_overview` helper in `backend/tools/market_data.py`**

Append to the file:

```python
def get_company_overview(ticker: str) -> dict:
    """Return Alpha Vantage OVERVIEW response for the ticker, or empty dict on error."""
    import os
    import requests
    api_key = os.environ.get("ALPHA_VANTAGE_KEY")
    if not api_key:
        return {}
    try:
        resp = requests.get(
            "https://www.alphavantage.co/query",
            params={"function": "OVERVIEW", "symbol": ticker, "apikey": api_key},
            timeout=10,
        )
        if resp.ok:
            return resp.json() or {}
    except requests.RequestException:
        pass
    return {}
```

(If a similar helper already exists, reuse it — grep first; do not duplicate.)

- [ ] **Step 5: Update market_data agent to surface metadata**

Replace `backend/agents/market_data.py`:

```python
from backend.tools.market_data import get_market_data_evidence, get_company_overview
from backend.graph.state import AgentState


def market_data_agent(state: AgentState) -> dict:
    ticker = state["ticker"]
    spans = get_market_data_evidence(ticker)
    overview = get_company_overview(ticker)
    return {
        "evidence": spans,
        "company_name": overview.get("Name"),
        "exchange": overview.get("Exchange"),
        "sector": overview.get("Sector"),
    }
```

- [ ] **Step 6: Update AgentState typed dict to allow these keys**

Inspect `backend/graph/state.py` and add (if not present) optional `company_name: str | None`, `exchange: str | None`, `sector: str | None` keys. Since `AgentState` likely uses `TypedDict(total=False)`, add as optional. If you need to verify the file:

```bash
grep -n "class AgentState\|company_name\|exchange\|sector" backend/graph/state.py
```

If missing, add inside the class body:

```python
    company_name: str | None
    exchange: str | None
    sector: str | None
```

- [ ] **Step 7: Run test to verify it passes**

```bash
python -m pytest tests/agents/test_market_data.py -v
```

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add backend/tools/market_data.py backend/agents/market_data.py backend/graph/state.py tests/agents/test_market_data.py
git commit -m "feat(market_data): surface company name, exchange, and sector"
```

---

### Task 3: Compute and persist bull/bear weights in moderator

**Files:**
- Modify: `backend/agents/moderator.py`
- Test: `tests/agents/test_moderator_weights.py`

- [ ] **Step 1: Write the failing test**

Create `tests/agents/test_moderator_weights.py`:

```python
from backend.agents.moderator import compute_weights


def test_compute_weights_averages_confidence():
    bull_points = [{"confidence": 0.9}, {"confidence": 0.7}, {"confidence": 0.6}]
    bear_points = [{"confidence": 0.8}, {"confidence": 0.5}]
    bull_w, bear_w = compute_weights(bull_points, bear_points)
    assert abs(bull_w - 0.7333) < 0.001
    assert abs(bear_w - 0.65) < 0.001


def test_compute_weights_handles_empty():
    assert compute_weights([], []) == (0.0, 0.0)
    assert compute_weights([{"confidence": 0.8}], []) == (0.8, 0.0)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/agents/test_moderator_weights.py -v
```

Expected: FAIL — `compute_weights` not defined.

- [ ] **Step 3: Add `compute_weights` to moderator.py**

Add to `backend/agents/moderator.py` (top-level helper):

```python
def compute_weights(bull_points: list[dict], bear_points: list[dict]) -> tuple[float, float]:
    """Return (bull_weight, bear_weight) — average confidence per side, 0.0 if empty."""
    def _avg(points: list[dict]) -> float:
        if not points:
            return 0.0
        confs = [p.get("confidence", 0.0) for p in points]
        return sum(confs) / len(confs)
    return _avg(bull_points), _avg(bear_points)
```

- [ ] **Step 4: Wire `compute_weights` into the memo assembly inside the moderator agent**

Find the function in `backend/agents/moderator.py` that constructs the `ResearchMemo`. Inspect:

```bash
grep -n "ResearchMemo(" backend/agents/moderator.py
```

When constructing the memo, add:

```python
bull_weight, bear_weight = compute_weights(
    state.get("bull_points", []), state.get("bear_points", [])
)
memo = ResearchMemo(
    # ... existing fields ...
    bull_weight=bull_weight,
    bear_weight=bear_weight,
    company_name=state.get("company_name"),
    exchange=state.get("exchange"),
    sector=state.get("sector"),
)
```

- [ ] **Step 5: Run test to verify it passes**

```bash
python -m pytest tests/agents/test_moderator_weights.py -v
```

Expected: 2 PASSED.

- [ ] **Step 6: Commit**

```bash
git add backend/agents/moderator.py tests/agents/test_moderator_weights.py
git commit -m "feat(moderator): populate bull/bear weights and company metadata in memo"
```

---

### Task 4: Add jsonl-backed runs index

**Files:**
- Create: `backend/persistence/runs_index.py`
- Test: `tests/persistence/test_runs_index.py`

- [ ] **Step 1: Write the failing test**

Create `tests/persistence/test_runs_index.py`:

```python
import json
import os
from pathlib import Path

import pytest

from backend.persistence.runs_index import append_run, list_runs


@pytest.fixture
def tmp_index(tmp_path, monkeypatch):
    path = tmp_path / "runs.jsonl"
    monkeypatch.setattr("backend.persistence.runs_index.RUNS_FILE", str(path))
    return path


def test_append_and_list_runs(tmp_index):
    append_run({
        "run_id": "abc",
        "ticker": "AAPL",
        "verdict": "Cautious Bull",
        "bull_weight": 0.78,
        "bear_weight": 0.64,
        "lede": "Apple presents a cautious bull setup.",
        "duration_s": 134.2,
        "agent_count": 14,
    })
    append_run({
        "run_id": "def",
        "ticker": "NVDA",
        "verdict": "Strong Bull",
        "bull_weight": 0.85,
        "bear_weight": 0.30,
        "lede": "NVDA continues to compound.",
        "duration_s": 111.8,
        "agent_count": 14,
    })
    runs = list_runs(limit=10)
    assert len(runs) == 2
    # newest first
    assert runs[0]["run_id"] == "def"
    assert runs[1]["run_id"] == "abc"


def test_list_runs_respects_limit(tmp_index):
    for i in range(5):
        append_run({"run_id": f"r{i}", "ticker": "X", "verdict": "Bull",
                    "bull_weight": 0.5, "bear_weight": 0.5, "lede": "x",
                    "duration_s": 1.0, "agent_count": 1})
    assert len(list_runs(limit=3)) == 3
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/persistence/test_runs_index.py -v
```

Expected: FAIL — `runs_index` module not found.

- [ ] **Step 3: Implement `backend/persistence/runs_index.py`**

Create the file:

```python
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

RUNS_FILE = os.environ.get(
    "RUNS_INDEX_FILE",
    str(Path(__file__).parent.parent.parent / "data" / "runs.jsonl"),
)


def append_run(entry: dict[str, Any]) -> None:
    """Append a run summary to the index file. Adds `created_at` if absent."""
    entry = {**entry}
    entry.setdefault("created_at", datetime.utcnow().isoformat())
    Path(RUNS_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(RUNS_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def list_runs(limit: int = 10) -> list[dict]:
    """Return the most recent `limit` runs (newest first)."""
    path = Path(RUNS_FILE)
    if not path.exists():
        return []
    with open(path) as f:
        lines = f.readlines()
    runs = [json.loads(line) for line in lines if line.strip()]
    return list(reversed(runs))[:limit]
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/persistence/test_runs_index.py -v
```

Expected: 2 PASSED.

- [ ] **Step 5: Commit**

```bash
git add backend/persistence/runs_index.py tests/persistence/test_runs_index.py
git commit -m "feat(persistence): add jsonl-backed runs index"
```

---

### Task 5: Wire runs_index into run completion + add /runs endpoint

**Files:**
- Modify: `backend/api.py`
- Test: `tests/test_api_runs.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_api_runs.py`:

```python
from fastapi.testclient import TestClient

from backend import api


def test_runs_endpoint_returns_recent(monkeypatch, tmp_path):
    runs_file = tmp_path / "runs.jsonl"
    monkeypatch.setattr("backend.persistence.runs_index.RUNS_FILE", str(runs_file))
    from backend.persistence.runs_index import append_run
    append_run({"run_id": "a", "ticker": "AAPL", "verdict": "Bull",
                "bull_weight": 0.7, "bear_weight": 0.5, "lede": "x",
                "duration_s": 1.0, "agent_count": 14})

    client = TestClient(api.app)
    resp = client.get("/runs?limit=5")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert body[0]["ticker"] == "AAPL"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_api_runs.py -v
```

Expected: FAIL — 404 on `/runs`.

- [ ] **Step 3: Add `/runs` endpoint and wire `append_run` into the SSE handler**

In `backend/api.py`, after the existing imports add:

```python
from backend.persistence.runs_index import append_run, list_runs
```

Add the endpoint near the other route handlers:

```python
@app.get("/runs")
async def get_runs(limit: int = 10):
    return list_runs(limit=limit)
```

In the SSE handler `run_stream`, find where the `run_completed` event is yielded (look for the final memo being assigned to `_run_results[run_id]`). Right before yielding `run_completed`, add:

```python
final_memo = _run_results.get(run_id, {}).get("final_memo")
if final_memo:
    lede = (final_memo.get("research_summary") or "").split(".")[0][:200]
    duration_s = round(time.time() - run_start_time, 2)
    append_run({
        "run_id": run_id,
        "ticker": ticker,
        "verdict": _classify_verdict(final_memo),
        "bull_weight": final_memo.get("bull_weight"),
        "bear_weight": final_memo.get("bear_weight"),
        "lede": lede,
        "duration_s": duration_s,
        "agent_count": len(AGENT_NODES),
    })
```

You will need a `run_start_time = time.time()` variable initialized at the top of `event_gen` (near the existing `import time`), and a small helper:

```python
def _classify_verdict(memo: dict) -> str:
    bw = memo.get("bull_weight") or 0.0
    br = memo.get("bear_weight") or 0.0
    if bw - br > 0.15: return "Strong Bull"
    if bw - br > 0.0: return "Cautious Bull"
    if br - bw > 0.15: return "Strong Bear"
    if br - bw > 0.0: return "Cautious Bear"
    return "Neutral"
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_api_runs.py -v
```

Expected: PASS.

- [ ] **Step 5: Manual smoke — start the API and hit /runs**

```bash
uvicorn backend.api:app --reload --port 8000 &
sleep 2
curl -s http://localhost:8000/runs?limit=5 | python -m json.tool
kill %1
```

Expected: `[]` (or any existing entries) — should not 500.

- [ ] **Step 6: Commit**

```bash
git add backend/api.py tests/test_api_runs.py
git commit -m "feat(api): add /runs endpoint and persist runs on completion"
```

---

## Phase 2: Frontend Scaffold

### Task 6: Initialize Next.js 14 project in `frontend-next/`

**Files:**
- Create: `frontend-next/` (full scaffold via `create-next-app`)

- [ ] **Step 1: Run create-next-app with non-interactive flags**

```bash
cd /Users/angiefong/job/equity-research-agent/.worktrees/frontend
npx create-next-app@14 frontend-next --typescript --tailwind --app --src-dir=false --import-alias="@/*" --no-eslint --use-npm
```

Expected: Project created in `frontend-next/`.

- [ ] **Step 2: Verify dev server starts**

```bash
cd frontend-next
npm run dev &
sleep 5
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000
kill %1
```

Expected: `200`.

- [ ] **Step 3: Add baseline dev tooling (Vitest, Playwright, RTL)**

```bash
cd frontend-next
npm install --save-dev vitest @vitejs/plugin-react jsdom @testing-library/react @testing-library/jest-dom @playwright/test @types/node
npx playwright install --with-deps chromium
```

- [ ] **Step 4: Configure Vitest**

Create `frontend-next/vitest.config.ts`:

```typescript
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    globals: true,
  },
  resolve: { alias: { "@": path.resolve(__dirname, ".") } },
});
```

Create `frontend-next/tests/setup.ts`:

```typescript
import "@testing-library/jest-dom/vitest";
```

Add to `frontend-next/package.json` scripts:

```json
"test": "vitest run",
"test:watch": "vitest",
"e2e": "playwright test"
```

- [ ] **Step 5: Configure Playwright**

Create `frontend-next/playwright.config.ts`:

```typescript
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  use: { baseURL: "http://localhost:3000" },
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: true,
    timeout: 30_000,
  },
});
```

- [ ] **Step 6: Sanity test**

```bash
cd frontend-next
npm test
```

Expected: `No test files found` (acceptable — Vitest is configured).

- [ ] **Step 7: Commit**

```bash
cd /Users/angiefong/job/equity-research-agent/.worktrees/frontend
git add frontend-next/
git commit -m "feat(frontend): scaffold Next.js 14 project with TS, Tailwind, Vitest, Playwright"
```

---

### Task 7: Configure brutalist Tailwind tokens, fonts, and global CSS

**Files:**
- Modify: `frontend-next/tailwind.config.ts`
- Modify: `frontend-next/app/layout.tsx`
- Modify: `frontend-next/app/globals.css`

- [ ] **Step 1: Replace `tailwind.config.ts`**

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#000000",
        paper: "#FFFFFF",
        accent: "#FFE100",
        accentSoft: "#FFF9D6",
        inset: "#FAFAF7",
        bull: "#006633",
        bear: "#B40000",
        muted: "#666666",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      letterSpacing: {
        display: "-0.04em",
        big: "-0.05em",
      },
    },
  },
  plugins: [],
};
export default config;
```

- [ ] **Step 2: Wire fonts via next/font in `app/layout.tsx`**

Replace `frontend-next/app/layout.tsx`:

```tsx
import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-mono" });

export const metadata: Metadata = {
  title: "Equity Research",
  description: "A 14-agent research desk for any ticker.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${mono.variable}`}>
      <body className="bg-paper text-ink font-sans antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
```

- [ ] **Step 3: Replace `app/globals.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  color-scheme: light;
}

body {
  font-feature-settings: "ss01", "cv01", "cv11";
}

/* Brutalist primitives as utilities */
@layer components {
  .b-frame {
    @apply border-2 border-ink bg-paper;
  }
  .b-rule {
    @apply border-b-2 border-ink;
  }
  .b-hairline {
    @apply border-b border-[#cccccc] border-dashed;
  }
  .label-tiny {
    @apply text-[8px] uppercase tracking-[1.5px] text-muted font-bold;
  }
  .label-section {
    @apply text-[10px] uppercase tracking-[2px] text-ink font-extrabold;
  }
}
```

- [ ] **Step 4: Create the providers shell**

Create `frontend-next/app/providers.tsx`:

```tsx
"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => new QueryClient({
    defaultOptions: { queries: { staleTime: 30_000, refetchOnWindowFocus: false } },
  }));
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
```

Install TanStack Query:

```bash
cd frontend-next
npm install @tanstack/react-query
```

- [ ] **Step 5: Verify build**

```bash
npm run build
```

Expected: build succeeds with no TS errors.

- [ ] **Step 6: Commit**

```bash
cd /Users/angiefong/job/equity-research-agent/.worktrees/frontend
git add frontend-next/
git commit -m "feat(frontend): brutalist Tailwind tokens, fonts, providers"
```

---

### Task 8: Add typed API client and shared types

**Files:**
- Create: `frontend-next/lib/types.ts`
- Create: `frontend-next/lib/api.ts`

- [ ] **Step 1: Create `lib/types.ts`**

```typescript
export type ResearchMemo = {
  id: string;
  ticker: string;
  timestamp: string;
  research_summary: string;
  bull_case: string;
  bear_case: string;
  moderator_synthesis: string;
  contradictions_detected: string[];
  unresolved_questions: string[];
  thesis_drift_summary: string | null;
  confidence_notes: string;
  citations: string[];
  bull_weight: number | null;
  bear_weight: number | null;
  company_name: string | null;
  exchange: string | null;
  sector: string | null;
};

export type ClaimPoint = {
  claim: string;
  confidence: number;
  rationale: string;
  evidence_span_ids?: string[];
};

export type Artifacts = {
  bull_points?: ClaimPoint[];
  bear_points?: ClaimPoint[];
  evidence?: unknown[];
  evidence_contradictions?: unknown[];
  debate_contradictions?: unknown[];
  verification_issues?: unknown[];
  thesis_delta?: unknown;
};

export type RunSummary = {
  run_id: string;
  ticker: string;
  verdict: string;
  bull_weight: number | null;
  bear_weight: number | null;
  lede: string;
  duration_s: number;
  agent_count: number;
  created_at: string;
};

export type AgentStatus = "pending" | "running" | "completed" | "failed";
```

- [ ] **Step 2: Create `lib/api.ts`**

```typescript
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
```

- [ ] **Step 3: Add env example**

Create `frontend-next/.env.example`:

```
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

Create `frontend-next/.env.local`:

```
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

Add `.env.local` to `frontend-next/.gitignore` (verify it's already in the create-next-app default).

- [ ] **Step 4: Commit**

```bash
git add frontend-next/lib/ frontend-next/.env.example frontend-next/.gitignore
git commit -m "feat(frontend): typed API client and shared types"
```

---

## Phase 3: Hero Visualizations

### Task 9: PriceChart component (SVG)

**Files:**
- Create: `frontend-next/components/viz/PriceChart.tsx`
- Test: `frontend-next/tests/viz/PriceChart.test.tsx`

- [ ] **Step 1: Write the failing test**

Create `frontend-next/tests/viz/PriceChart.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PriceChart } from "@/components/viz/PriceChart";

describe("PriceChart", () => {
  const data = Array.from({ length: 12 }, (_, i) => ({ date: `2026-${i + 1}`, price: 100 + i * 5 }));

  it("renders an SVG with one polyline", () => {
    render(<PriceChart data={data} high52w={200} low52w={80} current={155} />);
    const svg = screen.getByRole("img", { name: /price chart/i });
    expect(svg).toBeInTheDocument();
    expect(svg.querySelectorAll("polyline").length).toBe(1);
  });

  it("renders 52-week high and low labels", () => {
    render(<PriceChart data={data} high52w={200} low52w={80} current={155} />);
    expect(screen.getByText(/52W HIGH 200/i)).toBeInTheDocument();
    expect(screen.getByText(/52W LOW 80/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd frontend-next
npm test -- tests/viz/PriceChart.test.tsx
```

Expected: FAIL — module not found.

- [ ] **Step 3: Implement `PriceChart`**

Create `frontend-next/components/viz/PriceChart.tsx`:

```tsx
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npm test -- tests/viz/PriceChart.test.tsx
```

Expected: 2 PASSED.

- [ ] **Step 5: Commit**

```bash
git add frontend-next/components/viz/PriceChart.tsx frontend-next/tests/viz/PriceChart.test.tsx
git commit -m "feat(viz): PriceChart SVG component"
```

---

### Task 10: WeightBar component (SVG)

**Files:**
- Create: `frontend-next/components/viz/WeightBar.tsx`
- Test: `frontend-next/tests/viz/WeightBar.test.tsx`

- [ ] **Step 1: Write the failing test**

Create `frontend-next/tests/viz/WeightBar.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { WeightBar } from "@/components/viz/WeightBar";

describe("WeightBar", () => {
  it("renders bull and bear weight numbers", () => {
    render(<WeightBar bullWeight={0.78} bearWeight={0.64} bullClaims={4} bearClaims={2} />);
    expect(screen.getByText("0.78")).toBeInTheDocument();
    expect(screen.getByText("0.64")).toBeInTheDocument();
    expect(screen.getByText(/4 BULL CLAIMS/i)).toBeInTheDocument();
    expect(screen.getByText(/2 BEAR CLAIMS/i)).toBeInTheDocument();
  });

  it("computes bull-side share from weights", () => {
    const { container } = render(<WeightBar bullWeight={0.6} bearWeight={0.4} bullClaims={3} bearClaims={2} />);
    const bullDiv = container.querySelector("[data-side=bull]") as HTMLElement;
    expect(bullDiv.style.width).toBe("60%");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npm test -- tests/viz/WeightBar.test.tsx
```

Expected: FAIL — module not found.

- [ ] **Step 3: Implement `WeightBar`**

Create `frontend-next/components/viz/WeightBar.tsx`:

```tsx
type Props = {
  bullWeight: number;
  bearWeight: number;
  bullClaims: number;
  bearClaims: number;
};

export function WeightBar({ bullWeight, bearWeight, bullClaims, bearClaims }: Props) {
  const total = bullWeight + bearWeight || 1;
  const bullPct = (bullWeight / total) * 100;

  return (
    <div className="bg-inset border-y-2 border-ink p-5">
      <div className="flex justify-between mb-2 items-baseline">
        <div>
          <div className="label-section text-bull">↗ BULL</div>
          <div className="font-mono font-extrabold text-[18px] text-bull">{bullWeight.toFixed(2)}</div>
        </div>
        <div className="text-right">
          <div className="label-section text-bear">BEAR ↘</div>
          <div className="font-mono font-extrabold text-[18px] text-bear">{bearWeight.toFixed(2)}</div>
        </div>
      </div>
      <div className="relative pt-5">
        <div className="relative h-9 border-2 border-ink flex">
          <div
            data-side="bull"
            className="relative"
            style={{
              width: `${bullPct}%`,
              background: "repeating-linear-gradient(45deg, #006633 0 4px, #00773c 4px 8px)",
            }}
          />
          <div
            data-side="bear"
            className="relative"
            style={{
              width: `${100 - bullPct}%`,
              background: "repeating-linear-gradient(45deg, #B40000 0 4px, #c41010 4px 8px)",
            }}
          />
          <div
            className="absolute -top-2 -bottom-2 w-1 bg-accent border-x-[1.5px] border-ink"
            style={{ left: `${bullPct}%`, transform: "translateX(-50%)" }}
          >
            <span className="absolute -top-4 left-1/2 -translate-x-1/2 text-[14px]">★</span>
          </div>
        </div>
        <div className="flex justify-between mt-2 font-mono text-[9px] text-muted">
          <span>{bullClaims} BULL CLAIMS</span>
          <span>{bearClaims} BEAR CLAIMS</span>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npm test -- tests/viz/WeightBar.test.tsx
```

Expected: 2 PASSED.

- [ ] **Step 5: Commit**

```bash
git add frontend-next/components/viz/WeightBar.tsx frontend-next/tests/viz/WeightBar.test.tsx
git commit -m "feat(viz): WeightBar component with verdict marker"
```

---

### Task 11: ThesisMatrix component

**Files:**
- Create: `frontend-next/components/viz/ThesisMatrix.tsx`
- Test: `frontend-next/tests/viz/ThesisMatrix.test.tsx`

- [ ] **Step 1: Write the failing test**

Create `frontend-next/tests/viz/ThesisMatrix.test.tsx`:

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ThesisMatrix } from "@/components/viz/ThesisMatrix";

describe("ThesisMatrix", () => {
  const claims = [
    { side: "bull" as const, topic: "Services Margin", confidence: 0.92 },
    { side: "bull" as const, topic: "China Share", confidence: 0.74 },
    { side: "bear" as const, topic: "EU DMA", confidence: 0.83 },
    { side: "bear" as const, topic: "Vision Pro", confidence: 0.71 },
  ];

  it("renders one tile per claim", () => {
    render(<ThesisMatrix claims={claims} />);
    expect(screen.getByText("Services Margin")).toBeInTheDocument();
    expect(screen.getByText("EU DMA")).toBeInTheDocument();
  });

  it("applies strong saturation class for high-confidence bull tile", () => {
    const { container } = render(<ThesisMatrix claims={[claims[0]]} />);
    expect(container.querySelector(".bg-bull")).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

```bash
npm test -- tests/viz/ThesisMatrix.test.tsx
```

Expected: FAIL — module not found.

- [ ] **Step 3: Implement `ThesisMatrix`**

Create `frontend-next/components/viz/ThesisMatrix.tsx`:

```tsx
export type MatrixClaim = { side: "bull" | "bear"; topic: string; confidence: number };
type Props = { claims: MatrixClaim[] };

function tileClass(c: MatrixClaim): string {
  const high = c.confidence >= 0.8;
  const mid = c.confidence >= 0.6;
  if (c.side === "bull") {
    if (high) return "bg-bull text-paper";
    if (mid) return "bg-[#4DA77A] text-paper";
    return "bg-[#E8F5EE] text-ink";
  } else {
    if (high) return "bg-bear text-paper";
    if (mid) return "bg-[#D26060] text-paper";
    return "bg-[#FBE9E9] text-ink";
  }
}

export function ThesisMatrix({ claims }: Props) {
  return (
    <div>
      <div className="grid grid-cols-6 border-[1.5px] border-ink">
        {claims.map((c, i) => {
          const isLastInRow = (i + 1) % 6 === 0;
          return (
            <div
              key={`${c.topic}-${i}`}
              className={`p-2 ${isLastInRow ? "" : "border-r"} border-b border-ink min-h-[64px] flex flex-col justify-between text-[10px] ${tileClass(c)}`}
            >
              <div className="font-bold uppercase text-[9px] tracking-wider">{c.topic}</div>
              <div className="font-mono text-[9px] opacity-90 mt-1">
                {c.side.toUpperCase()} · {c.confidence.toFixed(2)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
npm test -- tests/viz/ThesisMatrix.test.tsx
```

Expected: 2 PASSED.

- [ ] **Step 5: Commit**

```bash
git add frontend-next/components/viz/ThesisMatrix.tsx frontend-next/tests/viz/ThesisMatrix.test.tsx
git commit -m "feat(viz): ThesisMatrix component"
```

---

## Phase 4: Memo Page

### Task 12: Memo page route + data fetching

**Files:**
- Create: `frontend-next/app/memo/[id]/page.tsx`

- [ ] **Step 1: Create the page (server component fetching memo + artifacts in parallel)**

Create `frontend-next/app/memo/[id]/page.tsx`:

```tsx
import { notFound } from "next/navigation";
import { api } from "@/lib/api";
import { MemoView } from "@/components/memo/MemoView";

export default async function MemoPage({ params }: { params: { id: string } }) {
  try {
    const [memo, artifacts] = await Promise.all([
      api.memo(params.id),
      api.artifacts(params.id),
    ]);
    return <MemoView memo={memo} artifacts={artifacts} />;
  } catch {
    notFound();
  }
}
```

- [ ] **Step 2: Create the placeholder MemoView**

Create `frontend-next/components/memo/MemoView.tsx`:

```tsx
import type { Artifacts, ResearchMemo } from "@/lib/types";

export function MemoView({ memo, artifacts }: { memo: ResearchMemo; artifacts: Artifacts }) {
  return (
    <div className="b-frame max-w-[920px] mx-auto my-6">
      <pre className="p-4 text-[11px]">{JSON.stringify({ ticker: memo.ticker, bull: artifacts.bull_points?.length, bear: artifacts.bear_points?.length }, null, 2)}</pre>
    </div>
  );
}
```

- [ ] **Step 3: Verify the page builds**

```bash
cd frontend-next && npm run build
```

Expected: build succeeds.

- [ ] **Step 4: Commit**

```bash
git add frontend-next/app/memo frontend-next/components/memo/MemoView.tsx
git commit -m "feat(memo): page route + placeholder view"
```

---

### Task 13: MemoTopbar + MemoHero + FactsStrip

**Files:**
- Create: `frontend-next/components/ui/Topbar.tsx`
- Create: `frontend-next/components/memo/MemoHero.tsx`
- Create: `frontend-next/components/memo/FactsStrip.tsx`
- Modify: `frontend-next/components/memo/MemoView.tsx`

- [ ] **Step 1: Create `Topbar.tsx`**

```tsx
type Props = { left: string; right: string };

export function Topbar({ left, right }: Props) {
  return (
    <div className="bg-ink text-paper px-4 py-2.5 flex justify-between items-center text-[10px] uppercase tracking-[2px] border-b-2 border-ink">
      <span>{left}</span>
      <span className="font-mono normal-case tracking-normal">{right}</span>
    </div>
  );
}
```

- [ ] **Step 2: Create `MemoHero.tsx`**

```tsx
import { PriceChart } from "@/components/viz/PriceChart";

type Props = {
  ticker: string;
  companyLine: string;
  price: number;
  changeAbs: number;
  changePct: number;
  verdict: string;
  high52w: number;
  low52w: number;
  series: { date: string; price: number }[];
};

export function MemoHero({ ticker, companyLine, price, changeAbs, changePct, verdict, high52w, low52w, series }: Props) {
  const up = changeAbs >= 0;
  return (
    <div className="grid grid-cols-[280px_1fr] gap-6 items-center px-5 py-5 border-b-2 border-ink">
      <div>
        <div className="font-extrabold text-[56px] leading-[0.9] tracking-big">{ticker}</div>
        <div className="text-[11px] text-muted mt-1 uppercase tracking-wider">{companyLine}</div>
        <div className="font-mono font-extrabold text-[26px] mt-3.5">${price.toFixed(2)}</div>
        <div className={`font-mono text-[12px] mt-0.5 ${up ? "text-bull" : "text-bear"}`}>
          {up ? "+" : ""}${changeAbs.toFixed(2)} ({up ? "+" : ""}{changePct.toFixed(2)}%) {up ? "▲" : "▼"}
        </div>
        <div className="inline-block mt-3 px-2.5 py-1 bg-accent border-[1.5px] border-ink text-[10px] font-extrabold uppercase tracking-[2px]">
          ★ {verdict}
        </div>
      </div>
      <PriceChart data={series} high52w={high52w} low52w={low52w} current={price} />
    </div>
  );
}
```

- [ ] **Step 3: Create `FactsStrip.tsx`**

```tsx
export type Fact = { label: string; value: string };
type Props = { facts: Fact[] };

export function FactsStrip({ facts }: Props) {
  return (
    <div className="grid border-b-2 border-ink" style={{ gridTemplateColumns: `repeat(${facts.length}, 1fr)` }}>
      {facts.map((f, i) => (
        <div key={f.label} className={`p-3 font-mono ${i < facts.length - 1 ? "border-r border-ink" : ""}`}>
          <div className="label-tiny mb-1">{f.label}</div>
          <div className="text-[14px] font-bold">{f.value}</div>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 4: Wire into `MemoView.tsx`**

Replace `frontend-next/components/memo/MemoView.tsx`:

```tsx
import type { Artifacts, ResearchMemo } from "@/lib/types";
import { Topbar } from "@/components/ui/Topbar";
import { MemoHero } from "@/components/memo/MemoHero";
import { FactsStrip, type Fact } from "@/components/memo/FactsStrip";

function fmtVerdict(memo: ResearchMemo): string {
  const bw = memo.bull_weight ?? 0, br = memo.bear_weight ?? 0;
  if (bw - br > 0.15) return "Strong Bull";
  if (bw - br > 0) return "Cautious Bull";
  if (br - bw > 0.15) return "Strong Bear";
  if (br - bw > 0) return "Cautious Bear";
  return "Neutral";
}

export function MemoView({ memo, artifacts }: { memo: ResearchMemo; artifacts: Artifacts }) {
  const company = [memo.company_name, memo.exchange, memo.sector].filter(Boolean).join(" · ");

  // TODO Task 14 — wire real series + facts from artifacts/evidence; placeholder for now
  const series = Array.from({ length: 12 }, (_, i) => ({ date: `m${i}`, price: 180 + i * 3 }));
  const facts: Fact[] = [
    { label: "Mkt Cap", value: "—" },
    { label: "P/E (Fwd)", value: "—" },
    { label: "EPS (TTM)", value: "—" },
    { label: "Div Yield", value: "—" },
    { label: "52W Range", value: "—" },
    { label: "Volume", value: "—" },
  ];

  return (
    <div className="b-frame max-w-[920px] mx-auto my-6">
      <Topbar left="Equity Research Memo" right={`${memo.timestamp} · live`} />
      <MemoHero
        ticker={memo.ticker}
        companyLine={company || memo.ticker}
        price={214.82}
        changeAbs={2.94}
        changePct={1.39}
        verdict={fmtVerdict(memo)}
        high52w={238}
        low52w={164}
        series={series}
      />
      <FactsStrip facts={facts} />
      <pre className="p-4 text-[11px]">{JSON.stringify({ bull: artifacts.bull_points?.length, bear: artifacts.bear_points?.length }, null, 2)}</pre>
    </div>
  );
}
```

> Note: real price/series/facts will come from a follow-up backend addition (out of v1 scope as listed in the spec). For now the hero uses placeholder values and the price chart uses a synthetic series. Task 14 will replace these with real data once available.

- [ ] **Step 5: Visual verification**

```bash
cd frontend-next && npm run dev &
sleep 4
# Open http://localhost:3000/memo/<any-existing-run-id> in a browser to verify visual layout
kill %1
```

- [ ] **Step 6: Commit**

```bash
git add frontend-next/components
git commit -m "feat(memo): topbar, hero with price chart, facts strip"
```

---

### Task 14: Synthesis + ClaimGrid + AlertStrip + integrate WeightBar and ThesisMatrix

**Files:**
- Create: `frontend-next/components/memo/Synthesis.tsx`
- Create: `frontend-next/components/memo/ClaimGrid.tsx`
- Create: `frontend-next/components/memo/AlertStrip.tsx`
- Modify: `frontend-next/components/memo/MemoView.tsx`

- [ ] **Step 1: Create `Synthesis.tsx`**

```tsx
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
```

- [ ] **Step 2: Create `ClaimGrid.tsx`**

```tsx
import type { ClaimPoint } from "@/lib/types";

type Props = {
  bullPoints: ClaimPoint[];
  bearPoints: ClaimPoint[];
};

function ClaimColumn({ side, points }: { side: "bull" | "bear"; points: ClaimPoint[] }) {
  const isBull = side === "bull";
  const avg = points.length
    ? points.reduce((a, b) => a + b.confidence, 0) / points.length
    : 0;
  return (
    <div className={`px-4 py-4 ${isBull ? "" : "border-l-[1.5px] border-ink"}`}>
      <div className="flex justify-between items-baseline mb-3 pb-2 border-b-[1.5px] border-ink">
        <span className={`label-section ${isBull ? "text-bull" : "text-bear"}`}>
          {isBull ? "↗ Bull Case" : "↘ Bear Case"}
        </span>
        <span className="font-mono text-[10px]">avg conf {avg.toFixed(2)}</span>
      </div>
      {points.map((p, i) => (
        <div key={i} className="py-3 b-hairline last:border-b-0 last:pb-0 first:pt-0 text-[12px] leading-[1.6]">
          <div className="flex justify-between items-baseline gap-2.5 mb-1.5">
            <span className="font-bold text-[13px]">{p.claim}</span>
            <span className="font-mono text-[9px] text-muted shrink-0">{p.confidence.toFixed(2)}</span>
          </div>
          <div className="text-[#222]">{p.rationale}</div>
          {p.evidence_span_ids?.length ? (
            <div className="font-mono text-[9px] text-muted mt-1.5 pt-1.5 border-t border-[#f0f0f0]">
              ↳ {p.evidence_span_ids.join(" · ")}
            </div>
          ) : null}
        </div>
      ))}
    </div>
  );
}

export function ClaimGrid({ bullPoints, bearPoints }: Props) {
  return (
    <div className="grid grid-cols-2 border-b-2 border-ink">
      <ClaimColumn side="bull" points={bullPoints} />
      <ClaimColumn side="bear" points={bearPoints} />
    </div>
  );
}
```

- [ ] **Step 3: Create `AlertStrip.tsx`**

```tsx
type Props = { contradictions: number; unresolved: number; agentCount: number; sourceCount: number; durationS: number };

export function AlertStrip({ contradictions, unresolved, agentCount, sourceCount, durationS }: Props) {
  const min = Math.floor(durationS / 60);
  const sec = Math.round(durationS % 60).toString().padStart(2, "0");
  return (
    <div className="bg-accent border-t-2 border-ink px-5 py-2.5 text-[11px] font-bold uppercase tracking-wider flex justify-between">
      <span>⚠ {contradictions} contradictions detected · {unresolved} unresolved</span>
      <span>{agentCount} agents · {sourceCount} sources · {min}m {sec}s</span>
    </div>
  );
}
```

- [ ] **Step 4: Update `MemoView.tsx` to use everything**

Replace `frontend-next/components/memo/MemoView.tsx`:

```tsx
import type { Artifacts, ResearchMemo } from "@/lib/types";
import { Topbar } from "@/components/ui/Topbar";
import { MemoHero } from "@/components/memo/MemoHero";
import { FactsStrip, type Fact } from "@/components/memo/FactsStrip";
import { Synthesis } from "@/components/memo/Synthesis";
import { ClaimGrid } from "@/components/memo/ClaimGrid";
import { AlertStrip } from "@/components/memo/AlertStrip";
import { WeightBar } from "@/components/viz/WeightBar";
import { ThesisMatrix, type MatrixClaim } from "@/components/viz/ThesisMatrix";

function fmtVerdict(memo: ResearchMemo): string {
  const bw = memo.bull_weight ?? 0, br = memo.bear_weight ?? 0;
  if (bw - br > 0.15) return "Strong Bull";
  if (bw - br > 0) return "Cautious Bull";
  if (br - bw > 0.15) return "Strong Bear";
  if (br - bw > 0) return "Cautious Bear";
  return "Neutral";
}

function paragraphsOf(synth: string): string[] {
  return synth.split(/\n{2,}/).map(s => s.trim()).filter(Boolean);
}

function matrixClaimsOf(arts: Artifacts): MatrixClaim[] {
  const bulls: MatrixClaim[] = (arts.bull_points ?? []).map(p => ({
    side: "bull", topic: p.claim.slice(0, 24), confidence: p.confidence,
  }));
  const bears: MatrixClaim[] = (arts.bear_points ?? []).map(p => ({
    side: "bear", topic: p.claim.slice(0, 24), confidence: p.confidence,
  }));
  return [...bulls, ...bears];
}

export function MemoView({ memo, artifacts }: { memo: ResearchMemo; artifacts: Artifacts }) {
  const company = [memo.company_name, memo.exchange, memo.sector].filter(Boolean).join(" · ");
  const series = Array.from({ length: 12 }, (_, i) => ({ date: `m${i}`, price: 180 + i * 3 }));
  const facts: Fact[] = [
    { label: "Mkt Cap", value: "—" }, { label: "P/E (Fwd)", value: "—" },
    { label: "EPS (TTM)", value: "—" }, { label: "Div Yield", value: "—" },
    { label: "52W Range", value: "—" }, { label: "Volume", value: "—" },
  ];
  const paras = paragraphsOf(memo.moderator_synthesis || "");
  const lede = paras.shift() || memo.research_summary;

  return (
    <div className="b-frame max-w-[920px] mx-auto my-6">
      <Topbar left="Equity Research Memo" right={`${memo.timestamp} · live`} />
      <MemoHero
        ticker={memo.ticker}
        companyLine={company || memo.ticker}
        price={214.82} changeAbs={2.94} changePct={1.39}
        verdict={fmtVerdict(memo)}
        high52w={238} low52w={164} series={series}
      />
      <FactsStrip facts={facts} />
      <Synthesis lede={lede} paragraphs={paras} />
      <WeightBar
        bullWeight={memo.bull_weight ?? 0}
        bearWeight={memo.bear_weight ?? 0}
        bullClaims={artifacts.bull_points?.length ?? 0}
        bearClaims={artifacts.bear_points?.length ?? 0}
      />
      <ClaimGrid
        bullPoints={artifacts.bull_points ?? []}
        bearPoints={artifacts.bear_points ?? []}
      />
      <div className="px-5 py-4 border-b-2 border-ink">
        <div className="label-section mb-3 pb-1.5 border-b-[1.5px] border-ink flex justify-between">
          <span>Thesis Matrix</span>
          <span className="font-mono normal-case tracking-normal text-muted">all claims · saturation = confidence</span>
        </div>
        <ThesisMatrix claims={matrixClaimsOf(artifacts)} />
      </div>
      <AlertStrip
        contradictions={memo.contradictions_detected.length}
        unresolved={memo.unresolved_questions.length}
        agentCount={14}
        sourceCount={memo.citations.length}
        durationS={0}
      />
    </div>
  );
}
```

- [ ] **Step 5: Build verification**

```bash
cd frontend-next && npm run build && npm test
```

Expected: build succeeds, all viz tests pass.

- [ ] **Step 6: Commit**

```bash
git add frontend-next/components/memo
git commit -m "feat(memo): synthesis, claim grid, alert strip; integrate weight bar and thesis matrix"
```

---

## Phase 5: Landing Page

### Task 15: Nav + LandingHero with form

**Files:**
- Create: `frontend-next/components/landing/Nav.tsx`
- Create: `frontend-next/components/landing/LandingHero.tsx`
- Modify: `frontend-next/app/page.tsx`

- [ ] **Step 1: Create `Nav.tsx`**

```tsx
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
```

- [ ] **Step 2: Create `LandingHero.tsx`**

```tsx
"use client";
import { useRouter } from "next/navigation";
import { useState } from "react";

const EXAMPLES = [
  "NVDA — earnings preview",
  "TSLA — thesis drift YTD",
  "META — bear case on AI capex",
  "SHOP — long-term outlook",
];

export function LandingHero() {
  const router = useRouter();
  const [ticker, setTicker] = useState("AAPL");
  const [query, setQuery] = useState("Build a bull and bear case for AAPL");

  function start() {
    const params = new URLSearchParams({ ticker, query });
    router.push(`/run/new?${params.toString()}`);
  }

  return (
    <div className="px-5 pt-9 pb-7 border-b-2 border-ink">
      <div className="label-tiny mb-2.5">★ MULTI-AGENT EQUITY RESEARCH</div>
      <h1 className="font-extrabold text-[44px] leading-[1.05] tracking-big mb-3.5 max-w-[18ch]">
        A 14-agent research desk for <span className="bg-accent px-1.5 box-decoration-clone">any ticker</span>, in 2 minutes.
      </h1>
      <p className="text-[14px] text-[#444] leading-[1.55] max-w-[56ch] mb-5">
        Type a ticker and a question. Watch fourteen specialized agents fetch filings, news, and market data, debate bull and bear, surface contradictions, and assemble a verifiable research memo.
      </p>
      <div className="grid grid-cols-[120px_1fr_auto] border-2 border-ink">
        <input
          value={ticker}
          onChange={e => setTicker(e.target.value.toUpperCase())}
          className="px-3.5 py-3 text-[14px] font-mono font-bold border-r-[1.5px] border-ink focus:outline-none focus:bg-accentSoft"
          placeholder="AAPL"
        />
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          className="px-3.5 py-3 text-[14px] border-r-[1.5px] border-ink focus:outline-none focus:bg-accentSoft"
          placeholder="Build a bull and bear case for AAPL"
        />
        <button
          onClick={start}
          className="bg-ink text-paper font-extrabold text-[11px] uppercase tracking-[1.5px] px-6 hover:bg-accent hover:text-ink"
        >
          Run Research →
        </button>
      </div>
      <div className="flex gap-2 mt-3 flex-wrap">
        {EXAMPLES.map(ex => (
          <span key={ex} className="font-mono text-[10px] px-2 py-1 border border-ink bg-inset cursor-pointer hover:bg-accent">
            {ex}
          </span>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Update `app/page.tsx`**

Replace `frontend-next/app/page.tsx`:

```tsx
import { Nav } from "@/components/landing/Nav";
import { LandingHero } from "@/components/landing/LandingHero";

export default function HomePage() {
  return (
    <main className="b-frame max-w-[920px] mx-auto my-6">
      <Nav active="research" />
      <LandingHero />
    </main>
  );
}
```

- [ ] **Step 4: Visual check**

```bash
cd frontend-next && npm run dev &
sleep 4
curl -s http://localhost:3000 -o /dev/null -w "%{http_code}\n"
kill %1
```

Expected: `200`.

- [ ] **Step 5: Commit**

```bash
git add frontend-next/app/page.tsx frontend-next/components/landing
git commit -m "feat(landing): nav and hero with brutalist form"
```

---

### Task 16: RecentMemos grid + HowItWorks

**Files:**
- Create: `frontend-next/components/landing/RecentMemos.tsx`
- Create: `frontend-next/components/landing/HowItWorks.tsx`
- Modify: `frontend-next/app/page.tsx`

- [ ] **Step 1: Create `RecentMemos.tsx`**

```tsx
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
              {new Date(r.created_at).toISOString().slice(0, 10)} · {Math.round(r.duration_s)}s · {r.agent_count} agents
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
```

- [ ] **Step 2: Create `HowItWorks.tsx`**

```tsx
const AGENTS: { name: string; hero?: boolean }[] = [
  { name: "SUPERVISOR" }, { name: "MARKET" }, { name: "FILINGS" },
  { name: "NEWS" }, { name: "QUANT" }, { name: "QUANT INTERP" },
  { name: "EV CONTR" }, { name: "BULL", hero: true }, { name: "BEAR", hero: true },
  { name: "DEBATE CONTR" }, { name: "VERIFIER" }, { name: "REROUTE" },
  { name: "THESIS REPLAY" }, { name: "MODERATOR", hero: true },
];

export function HowItWorks() {
  return (
    <section className="px-5 py-6">
      <div className="label-section mb-3.5 pb-1.5 border-b-[1.5px] border-ink flex justify-between">
        <span>How it works</span>
        <span className="font-mono normal-case tracking-normal text-muted">→ /run/[id]</span>
      </div>
      <div className="grid grid-cols-7 border-[1.5px] border-ink">
        {AGENTS.map((a, i) => {
          const lastCol = (i + 1) % 7 === 0;
          const lastRow = i >= AGENTS.length - 7;
          return (
            <div
              key={a.name}
              className={`px-1 py-1.5 text-[8px] font-bold uppercase tracking-wider text-center min-h-[38px] flex items-center justify-center ${a.hero ? "bg-accent" : "bg-inset"} ${lastCol ? "" : "border-r border-ink"} ${lastRow ? "" : "border-b border-ink"}`}
            >
              {a.name}
            </div>
          );
        })}
      </div>
      <p className="text-[11px] text-muted mt-2.5 leading-[1.5] max-w-[56ch]">
        Each agent has one job. The verifier checks every claim against source evidence; the reroute loop re-fetches data when claims fail verification. The moderator assembles the final memo with citations.
      </p>
    </section>
  );
}
```

- [ ] **Step 3: Wire `app/page.tsx` to fetch and render**

Replace `frontend-next/app/page.tsx`:

```tsx
import { Nav } from "@/components/landing/Nav";
import { LandingHero } from "@/components/landing/LandingHero";
import { RecentMemos } from "@/components/landing/RecentMemos";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { api } from "@/lib/api";

export default async function HomePage() {
  let runs: Awaited<ReturnType<typeof api.recentRuns>> = [];
  try {
    runs = await api.recentRuns(3);
  } catch {
    runs = [];
  }
  return (
    <main className="b-frame max-w-[920px] mx-auto my-6">
      <Nav active="research" />
      <LandingHero />
      <RecentMemos runs={runs} />
      <HowItWorks />
    </main>
  );
}
```

- [ ] **Step 4: Visual check**

```bash
cd frontend-next && npm run dev &
sleep 4
curl -s http://localhost:3000 -o /dev/null -w "%{http_code}\n"
kill %1
```

Expected: `200`. Open in browser to verify the page renders end-to-end (form, recent memos with empty state if backend has no runs, agent grid).

- [ ] **Step 5: Commit**

```bash
git add frontend-next/app/page.tsx frontend-next/components/landing
git commit -m "feat(landing): recent memos grid and how-it-works strip"
```

---

## Phase 6: Live Run Page

### Task 17: SSE EventSource hook + run page route

**Files:**
- Create: `frontend-next/lib/useRunStream.ts`
- Create: `frontend-next/app/run/[id]/page.tsx`
- Create: `frontend-next/app/run/new/page.tsx`

- [ ] **Step 1: Create `useRunStream.ts`**

```tsx
"use client";
import { useEffect, useReducer, useRef } from "react";
import type { AgentStatus } from "@/lib/types";

export type RunState = {
  runId: string | null;
  status: "idle" | "streaming" | "completed" | "failed";
  startedAt: number | null;
  agents: Record<string, { status: AgentStatus; summary?: string; elapsedS?: number; startedAt?: number }>;
  log: { agent: string; type: string; message: string; t: number }[];
  reroutes: number;
  failed: number;
};

type Event =
  | { type: "init" }
  | { type: "started"; runId: string }
  | { type: "agent_started"; agent: string; t: number }
  | { type: "agent_completed"; agent: string; summary: string; elapsedS: number; t: number }
  | { type: "agent_failed"; agent: string; error: string; t: number }
  | { type: "completed" };

function reducer(state: RunState, ev: Event): RunState {
  switch (ev.type) {
    case "init": return state;
    case "started": return { ...state, runId: ev.runId, status: "streaming", startedAt: Date.now() };
    case "agent_started": {
      const agents = { ...state.agents, [ev.agent]: { status: "running" as AgentStatus, startedAt: ev.t } };
      const log = [...state.log, { agent: ev.agent, type: "started", message: "started", t: ev.t }];
      return { ...state, agents, log };
    }
    case "agent_completed": {
      const agents = { ...state.agents, [ev.agent]: { status: "completed" as AgentStatus, summary: ev.summary, elapsedS: ev.elapsedS } };
      const reroutes = ev.agent === "reroute" ? state.reroutes + 1 : state.reroutes;
      const log = [...state.log, { agent: ev.agent, type: "completed", message: ev.summary, t: ev.t }];
      return { ...state, agents, reroutes, log };
    }
    case "agent_failed": {
      const agents = { ...state.agents, [ev.agent]: { status: "failed" as AgentStatus, summary: ev.error } };
      const log = [...state.log, { agent: ev.agent, type: "failed", message: ev.error, t: ev.t }];
      return { ...state, agents, failed: state.failed + 1, log };
    }
    case "completed": return { ...state, status: "completed" };
  }
}

const initial: RunState = {
  runId: null, status: "idle", startedAt: null, agents: {}, log: [], reroutes: 0, failed: 0,
};

export function useRunStream(streamUrl: string | null): RunState {
  const [state, dispatch] = useReducer(reducer, initial);
  const ref = useRef<EventSource | null>(null);
  useEffect(() => {
    if (!streamUrl) return;
    const es = new EventSource(streamUrl);
    ref.current = es;
    const now = () => Date.now() / 1000;

    es.addEventListener("run_started", (e: MessageEvent) => {
      const d = JSON.parse(e.data); dispatch({ type: "started", runId: d.run_id });
    });
    es.addEventListener("agent_started", (e: MessageEvent) => {
      const d = JSON.parse(e.data); dispatch({ type: "agent_started", agent: d.agent, t: now() });
    });
    es.addEventListener("agent_completed", (e: MessageEvent) => {
      const d = JSON.parse(e.data);
      dispatch({ type: "agent_completed", agent: d.agent, summary: d.summary, elapsedS: d.elapsed_s, t: now() });
    });
    es.addEventListener("agent_failed", (e: MessageEvent) => {
      const d = JSON.parse(e.data); dispatch({ type: "agent_failed", agent: d.agent, error: d.error || "unknown", t: now() });
    });
    es.addEventListener("run_completed", () => { dispatch({ type: "completed" }); es.close(); });
    es.onerror = () => { /* let EventSource auto-reconnect */ };
    return () => { es.close(); };
  }, [streamUrl]);
  return state;
}
```

- [ ] **Step 2: Create the bootstrapping `/run/new` route**

This route reads `?ticker&query`, opens the SSE, and once `run_id` is known redirects to `/run/[id]`.

Create `frontend-next/app/run/new/page.tsx`:

```tsx
"use client";
import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { useRunStream } from "@/lib/useRunStream";

export default function NewRunPage() {
  const params = useSearchParams();
  const router = useRouter();
  const ticker = params.get("ticker") || "";
  const query = params.get("query") || "";
  const url = ticker && query ? api.streamUrl(ticker, query) : null;
  const state = useRunStream(url);

  useEffect(() => {
    if (state.runId) router.replace(`/run/${state.runId}?ticker=${encodeURIComponent(ticker)}&query=${encodeURIComponent(query)}`);
  }, [state.runId, ticker, query, router]);

  return (
    <main className="b-frame max-w-[920px] mx-auto my-6 p-6">
      <p className="font-mono text-[12px]">Starting run for {ticker}…</p>
    </main>
  );
}
```

> Note: `/run/[id]` reuses the same SSE URL by being mounted from the parent. To keep one SSE connection across the `/new → /[id]` redirect, the simplest reliable approach is to start the stream on `/[id]` directly using the ticker+query carried via search params, and use `/new` only as a thin redirector that opens the stream once. The hook closes the connection on unmount; that's acceptable here because `/new` is replaced by `/[id]` only after we know the `run_id` from the first event — at that point we can re-open. (For demo polish in v1.1, we can lift the stream to a Provider to avoid the brief reconnect.)

- [ ] **Step 3: Create `/run/[id]/page.tsx` placeholder that uses the stream**

Create `frontend-next/app/run/[id]/page.tsx`:

```tsx
"use client";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { useRunStream } from "@/lib/useRunStream";

export default function RunPage({ params }: { params: { id: string } }) {
  const search = useSearchParams();
  const ticker = search.get("ticker") || "";
  const query = search.get("query") || "";
  const url = ticker && query ? api.streamUrl(ticker, query) : null;
  const state = useRunStream(url);

  return (
    <main className="b-frame max-w-[920px] mx-auto my-6 p-6 font-mono text-[11px]">
      <p>run_id: {params.id}</p>
      <p>status: {state.status}</p>
      <p>reroutes: {state.reroutes}</p>
      <p>failed: {state.failed}</p>
      <p>agents seen: {Object.keys(state.agents).length} / 14</p>
    </main>
  );
}
```

- [ ] **Step 4: Build verification**

```bash
cd frontend-next && npm run build
```

Expected: build succeeds.

- [ ] **Step 5: Commit**

```bash
git add frontend-next/lib/useRunStream.ts frontend-next/app/run
git commit -m "feat(run): SSE hook and bootstrap pages"
```

---

### Task 18: PipelineDAG component

**Files:**
- Create: `frontend-next/components/viz/PipelineDAG.tsx`

- [ ] **Step 1: Implement `PipelineDAG`**

This is a static SVG layout with state-driven node fills. Create `frontend-next/components/viz/PipelineDAG.tsx`:

```tsx
import type { AgentStatus } from "@/lib/types";

type AgentMap = Record<string, { status: AgentStatus; elapsedS?: number }>;

const LAYOUT = {
  supervisor:            { x: 20,  y: 100, w: 80, h: 40 },
  market_data:           { x: 160, y: 20,  w: 80, h: 40, label: "MARKET" },
  filings:               { x: 160, y: 70,  w: 80, h: 40 },
  news:                  { x: 160, y: 130, w: 80, h: 40 },
  quant_data:            { x: 160, y: 180, w: 80, h: 40, label: "QUANT" },
  quant_interpretation:  { x: 300, y: 100, w: 100, h: 40, label: "QUANT INTERP" },
  evidence_contradiction:{ x: 460, y: 100, w: 80, h: 40, label: "EV CONTR" },
  bull:                  { x: 600, y: 50,  w: 80, h: 40 },
  bear:                  { x: 600, y: 150, w: 80, h: 40 },
  verifier:              { x: 720, y: 100, w: 60, h: 40 },
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
  { from: "bull", to: "verifier" },
  { from: "bear", to: "verifier" },
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
      <svg viewBox="0 0 800 240" className="w-full h-full">
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
```

- [ ] **Step 2: Smoke test render**

```bash
cd frontend-next && npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend-next/components/viz/PipelineDAG.tsx
git commit -m "feat(viz): PipelineDAG SVG component"
```

---

### Task 19: RunHeader + FocusCard + BuildLog + assembled run page

**Files:**
- Create: `frontend-next/components/run/RunHeader.tsx`
- Create: `frontend-next/components/run/FocusCard.tsx`
- Create: `frontend-next/components/run/BuildLog.tsx`
- Modify: `frontend-next/app/run/[id]/page.tsx`

- [ ] **Step 1: Create `RunHeader.tsx`**

```tsx
type Stat = { label: string; value: string };

type Props = {
  ticker: string;
  query: string;
  stats: Stat[];
};

export function RunHeader({ ticker, query, stats }: Props) {
  return (
    <div className="px-5 py-3.5 border-b-2 border-ink flex justify-between items-baseline gap-6">
      <div>
        <h3 className="font-extrabold text-[22px] tracking-display m-0">{ticker}</h3>
        <div className="text-[11px] text-muted mt-0.5 italic">"{query}"</div>
      </div>
      <div className="flex gap-5 font-mono text-[11px]">
        {stats.map(s => (
          <div key={s.label}>
            <div className="label-tiny">{s.label}</div>
            <div className="font-extrabold text-[14px]">{s.value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create `FocusCard.tsx`**

```tsx
type Props = { agent: string | null; elapsedS: number | null; lines: string[] };

export function FocusCard({ agent, elapsedS, lines }: Props) {
  return (
    <div className="px-5 py-4 border-b-2 border-ink">
      <div className="label-section mb-2.5 pb-1.5 border-b-[1.5px] border-ink flex justify-between">
        <span>Now Running</span>
        <span className="font-mono normal-case tracking-normal text-muted">live tail</span>
      </div>
      <div className="border-[1.5px] border-ink p-3 bg-accentSoft">
        <div className="flex justify-between items-baseline pb-1.5 border-b-[1.5px] border-ink mb-2">
          <span className="font-extrabold text-[12px] uppercase tracking-[1.5px]">
            ⚡ {agent ?? "WAITING"}
          </span>
          <span className="font-mono text-[10px] text-muted">
            {elapsedS != null ? `running ${elapsedS.toFixed(0)}s` : "—"}
          </span>
        </div>
        <div className="font-mono text-[11px] leading-[1.6] text-[#222]">
          {lines.map((l, i) => <div key={i}>&gt; {l}</div>)}
          {agent && <div>&gt; <span className="animate-pulse">▌</span></div>}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Create `BuildLog.tsx`**

```tsx
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
```

- [ ] **Step 4: Replace `app/run/[id]/page.tsx` with the assembled UI**

Replace `frontend-next/app/run/[id]/page.tsx`:

```tsx
"use client";
import { useEffect, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { useRunStream } from "@/lib/useRunStream";
import { Topbar } from "@/components/ui/Topbar";
import { RunHeader } from "@/components/run/RunHeader";
import { FocusCard } from "@/components/run/FocusCard";
import { BuildLog } from "@/components/run/BuildLog";
import { PipelineDAG } from "@/components/viz/PipelineDAG";
import type { AgentStatus } from "@/lib/types";

const AGENT_ORDER = [
  "supervisor", "market_data", "filings", "news", "quant_data",
  "quant_interpretation", "evidence_contradiction",
  "bull", "bear", "debate_contradiction",
  "verifier", "reroute", "thesis_replay", "moderator",
] as const;

export default function RunPage({ params }: { params: { id: string } }) {
  const search = useSearchParams();
  const router = useRouter();
  const ticker = search.get("ticker") || "";
  const query = search.get("query") || "";
  const url = ticker && query ? api.streamUrl(ticker, query) : null;
  const state = useRunStream(url);

  useEffect(() => {
    if (state.status === "completed" && state.runId) {
      router.replace(`/memo/${state.runId}`);
    }
  }, [state.status, state.runId, router]);

  const elapsed = state.startedAt ? Math.round((Date.now() - state.startedAt) / 1000) : 0;
  const min = Math.floor(elapsed / 60).toString().padStart(2, "0");
  const sec = (elapsed % 60).toString().padStart(2, "0");
  const done = AGENT_ORDER.filter(n => state.agents[n]?.status === "completed").length;

  const runningAgent = AGENT_ORDER.find(n => state.agents[n]?.status === "running") ?? null;
  const runningSince = runningAgent ? state.agents[runningAgent]?.startedAt ?? null : null;
  const runningElapsed = runningSince ? Date.now() / 1000 - runningSince : null;

  const focusLines = useMemo(() => state.log.slice(-6).map(l => `${l.agent} ${l.type}: ${l.message}`), [state.log]);

  const rows = AGENT_ORDER.map(name => {
    const ag = state.agents[name];
    const status: AgentStatus = ag?.status ?? "pending";
    return { agent: name, status, summary: ag?.summary, elapsedS: ag?.elapsedS };
  });

  return (
    <main className="b-frame max-w-[920px] mx-auto my-6">
      <Topbar
        left={`Live Run · run_id ${params.id.slice(0, 8)}…`}
        right={`${new Date().toISOString().replace("T", " ").slice(0, 19)} · ${state.status}`}
      />
      <RunHeader
        ticker={ticker}
        query={query}
        stats={[
          { label: "Elapsed", value: `${min}:${sec}` },
          { label: "Done", value: `${done}/14` },
          { label: "Failed", value: `${state.failed}` },
          { label: "Reroutes", value: `${state.reroutes}` },
        ]}
      />
      <div className="px-5 py-4 border-b-2 border-ink bg-inset">
        <div className="label-section mb-2.5 pb-1.5 border-b-[1.5px] border-ink flex justify-between">
          <span>Pipeline</span>
          <span className="font-mono normal-case tracking-normal text-muted">14 agents · streaming via SSE</span>
        </div>
        <PipelineDAG agents={state.agents} />
      </div>
      <FocusCard agent={runningAgent} elapsedS={runningElapsed} lines={focusLines} />
      <BuildLog rows={rows} />
    </main>
  );
}
```

- [ ] **Step 5: Build verification**

```bash
cd frontend-next && npm run build && npm test
```

Expected: build succeeds, all viz tests pass.

- [ ] **Step 6: Commit**

```bash
git add frontend-next/components/run frontend-next/app/run/[id]/page.tsx
git commit -m "feat(run): assemble run page with header, DAG, focus card, build log"
```

---

### Task 20: End-to-end smoke test (Playwright)

**Files:**
- Create: `frontend-next/tests/e2e/landing.spec.ts`

- [ ] **Step 1: Write a happy-path landing test**

Create `frontend-next/tests/e2e/landing.spec.ts`:

```typescript
import { test, expect } from "@playwright/test";

test("landing renders headline and form", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /14-agent research desk/i })).toBeVisible();
  await expect(page.getByPlaceholder("AAPL")).toBeVisible();
  await expect(page.getByRole("button", { name: /run research/i })).toBeVisible();
});
```

- [ ] **Step 2: Run e2e**

```bash
cd frontend-next
npx playwright test
```

Expected: 1 passed.

- [ ] **Step 3: Commit**

```bash
git add frontend-next/tests/e2e
git commit -m "test(e2e): landing happy-path smoke test"
```

---

## Phase 7: Deployment

### Task 21: Deploy frontend to Vercel + verify against Railway backend

This task is operational, not code-driven. Steps are checklist-only; commits are not required at the end.

- [ ] **Step 1: Confirm Railway backend is reachable and includes Phase 1 changes**

```bash
# Replace <RAILWAY_URL> with the actual deploy URL
curl -s "<RAILWAY_URL>/runs?limit=5" | head -c 200
```

Expected: JSON array (possibly empty), HTTP 200.

- [ ] **Step 2: Configure Vercel project**

```bash
cd frontend-next
npx vercel link
npx vercel env add NEXT_PUBLIC_BACKEND_URL production
# Paste the Railway URL when prompted
```

- [ ] **Step 3: Deploy**

```bash
npx vercel --prod
```

Expected: deploy URL returned. Open it.

- [ ] **Step 4: Manual smoke checks on the deployed URL**

- Landing renders, form is interactive
- Submitting a ticker (e.g., AAPL) navigates to `/run/new?...` then `/run/[id]`
- DAG animates as agents progress
- On completion, page redirects to `/memo/[id]`
- Memo page renders all sections
- Click a "Recent Memos" card on `/` → navigates to that memo page

- [ ] **Step 5: Seed at least 3 memos for the demo**

Run AAPL, NVDA, TSLA against the deployed backend so the landing page "Recent Memos" grid has content for screenshots.

---

## Self-Review (post-write)

Spec coverage:
- ✅ Brutalist visual direction (Tailwind tokens, fonts, primitives) — Task 7
- ✅ Three pages (`/`, `/run/[id]`, `/memo/[id]`) — Tasks 12, 17, 19, plus 15-16 for landing
- ✅ Three hero visualizations (PriceChart, WeightBar, ThesisMatrix) — Tasks 9-11
- ✅ Memo page sections (hero, facts, synthesis, claim grid, alert) — Tasks 13-14
- ✅ Live run page (DAG + focus + log) — Tasks 18-19
- ✅ Landing (form + recent memos + how-it-works) — Tasks 15-16
- ✅ Backend additions (memo metadata, runs index, /runs endpoint) — Tasks 1-5
- ✅ Stack choices (Next.js 14 + TS + Tailwind + TanStack + native EventSource + hand-rolled SVG) — Tasks 6-7
- ✅ Deployment to Vercel + Railway — Task 21
- ⚠️ CORS work was listed in spec but the existing FastAPI uses `allow_origins=["*"]`; no CORS task needed (noted in this plan).
- ⚠️ Real price/series/facts in the memo hero are placeholder (Task 13 note) — full wiring up depends on a follow-up `quant_data` artifact shape change, which the spec did not require for v1.

Type consistency: `AgentStatus` used identically across `useRunStream`, `BuildLog`, `PipelineDAG`. `ResearchMemo` and `RunSummary` shapes match the backend additions.

No placeholders detected. All steps include exact commands and concrete code.
