# Frontend Revamp — Design Spec

**Date:** 2026-04-25
**Author:** Angie Fong
**Status:** Approved (pending implementation plan)

## Goal

Replace the existing Streamlit frontend with a custom Next.js application that presents the equity research agent system as a polished, portfolio-grade product. The research memo is the centerpiece; the multi-agent run is a supporting (but visually distinctive) experience.

The current Streamlit app is functional but reads as a developer tool, not a product. Recruiters reviewing this work should walk away with two impressions:
1. **"This person can ship a real product"** (memo as polished editorial artifact)
2. **"This person can build agentic systems"** (live run page visualizes a 14-agent DAG)

## Visual Direction

**Brutalist editorial — Stripe-meets-FT.** Hard 1.5–2px black borders, no shadows, no rounded corners (or 2px max). Bold sans-serif (Inter) for UI; JetBrains Mono for all numbers and code-like content. A single yellow accent (#FFE100) is reserved for the verdict marker, the live "running" state, and primary CTAs.

### Palette
- `#FFFFFF` — surface
- `#000000` — borders, primary text
- `#FFE100` — accent (verdict, running state, primary CTA)
- `#FAFAF7` — subtle inset background
- `#006633` — bull (semantic only)
- `#B40000` — bear (semantic only)
- `#666666` — secondary text

### Typography
- **Headings & UI:** Inter, weights 400/600/700/900
- **Numbers, code, evidence IDs:** JetBrains Mono
- Tight letter-spacing on display sizes (`-0.04em` to `-0.05em`)
- Section labels are uppercase 10–11px with `letter-spacing: 1.5–2px`

### Layout primitives
- Hard rules between sections (1.5–2px borders)
- Grid-based fact strips and matrices (no gaps; cells share borders)
- Mockup files: `.superpowers/brainstorm/39057-1777091002/content/memo-v4-expanded.html`, `landing.html`, `run-page-v2-combined.html`

## App Structure

Three pages plus a history/list view.

| Route | Purpose | Notes |
|---|---|---|
| `/` | Landing — form + recent memos + how-it-works | Marketing-shaped entry point |
| `/run/[id]` | Live agent stream | DAG + focus card + log tail; auto-redirects to `/memo/[id]` on completion |
| `/memo/[id]` | Memo viewer | SSR'd for shareable URLs (LinkedIn previews) |
| `/history` | Past runs grouped by ticker | Secondary; can ship in v1.1 if time-constrained |
| `/ticker/[symbol]` | All memos for one ticker + thesis drift | Optional |

Each memo URL is shareable. SSR ensures pasting `/memo/[id]` into LinkedIn/Twitter renders a clean preview with the ticker, verdict, and lede.

## Page Designs

### Landing (`/`)

- **Nav** (full-width, bordered): brand mark "EQUITY.RESEARCH" + RESEARCH / HISTORY / HOW IT WORKS
- **Hero**:
  - Kicker label: "★ Multi-agent equity research"
  - H1 (44px, weight 900): "A 14-agent research desk for **any ticker**, in 2 minutes." (yellow highlight on "any ticker")
  - Sub paragraph (~50ch max-width)
  - Inline form: `[Ticker] | [Query input] | [Run Research →]` — single bordered row, focus state highlights yellow
  - Example chip row (clickable to pre-fill form)
- **Recent Memos**: 3-column grid showing the 3 most recent memos with ticker, verdict pill, lede snippet, mini bull/bear weight bar, metadata. Hits `GET /runs?limit=3` — does not depend on the `/history` page existing.
- **How it works**: 7×2 grid of all 14 agent tiles; bull/bear/moderator tiles are yellow

### Live Run Page (`/run/[id]`)

Reads top-to-bottom:

1. **Topbar**: black bar with "Live Run · run_id ..." + datetime + "streaming" indicator
2. **Header**: ticker (22px bold) + query (italic) + stat row (Elapsed / Done / Failed / Reroutes) in mono
3. **Pipeline DAG**: SVG visualization of the agent dependency graph
   - Fan-out from supervisor to data fetchers (market_data, filings, news, quant_data)
   - Fan-in to quant_interpretation
   - Linear through evidence_contradiction
   - Split to bull / bear
   - Merge to debate_contradiction → verifier → moderator
   - Reroute and thesis_replay shown as side-loops
   - Node states: pending (gray), running (yellow, thicker stroke), done (light green), failed (light red)
4. **Now Running** focus card: yellow background, agent name, elapsed time, live tail of what the agent is doing (streamed lines, blinking cursor)
5. **Build Log**: dense vertical scrollback of every step with status icon + agent name + summary + timing in mono

On `run_completed` event, the page transitions to `/memo/[id]`.

### Memo Page (`/memo/[id]`)

Single scroll, no tabs. Reads top-to-bottom:

1. **Topbar**: "Equity Research Memo" + datetime + "live" indicator
2. **Hero**: 280px-wide left column (ticker / company / price / change / verdict pill) + right column with **1Y price chart (SVG)** with dashed 52W high/low rails, earnings tick marks, yellow current-price dot
3. **Facts strip**: 6 mono cells (Mkt Cap, P/E Fwd, EPS TTM, Div Yield, 52W Range, Volume)
4. **Synthesis**: multi-paragraph lede (max 68ch), 17px lede sentence + 14px body paragraphs, optional pull-quote with yellow rule
5. **Bull-Bear weight bar**: horizontal bar with bull/bear weights as numbers, diagonal-stripe fill, yellow verdict marker (★) at the meet point, claim count tick marks
6. **Bull/Bear claim grid**: two columns with hard divider, each claim has heading + confidence pill + body + evidence IDs in mono
7. **Thesis Matrix**: 6-column grid of all claims as colored tiles (bull green / bear red, saturation = confidence)
8. **Alert strip** (yellow, full-width): contradictions count + run metadata (agents · sources · duration)

All sections use semantic max-heights and `min-height: auto` so they grow with content.

## Three Hero Visualizations

All hand-rolled SVG (no chart library). Each plays a distinct role:

### 1. Price Chart (in hero)
- 1Y price line, 2.5px black stroke, no axes
- Dashed horizontal rules for 52W high/low with mono labels
- Tick marks on the baseline for earnings dates
- Yellow current-price dot with black stroke

### 2. Bull-Bear Weight Bar (above claim grid)
- Single horizontal bar, full-width, 2px black border
- Left: bull (green diagonal stripes), width = bull_weight / (bull_weight + bear_weight)
- Right: bear (red diagonal stripes)
- Yellow vertical "verdict marker" at the meet, with ★ above
- Tick marks at the bottom for individual claims (positioned by their confidence)

### 3. Thesis Matrix (below claim grid)
- 6-column grid of tiles, one per claim
- Bull tiles: green (3 saturation steps for confidence bands)
- Bear tiles: red (3 saturation steps)
- Tile shows topic name (uppercase, 9px, bold) + confidence in mono

## Stack

| Layer | Choice | Rationale |
|---|---|---|
| Framework | Next.js 14 (App Router) + TypeScript | SSR for shareable memo URLs |
| Styling | Tailwind CSS | Brutalist style is borders + mono — Tailwind handles directly |
| Charts | Hand-rolled SVG | Full brutalist control; no library overhead |
| Data fetching | TanStack Query | Memo + history pages |
| Streaming | Native EventSource API | For `/run/stream` SSE on the run page |
| Fonts | Inter + JetBrains Mono | Both via `next/font` |
| Deployment | Vercel (frontend) + Railway (backend) | Vercel for SSR; Railway already configured |

## Backend Changes

The existing FastAPI backend covers ~95% of what's needed. Required additions:

1. **`market_data` agent**: extend output to include `company_name`, `exchange`, `sector` (currently the memo only knows the ticker)
2. **New endpoint `GET /runs?limit=N`**: returns recent runs across all tickers for the landing page "Recent Memos" grid and `/history`. Include: `run_id`, `ticker`, `verdict`, `bull_weight`, `bear_weight`, `lede` (first sentence), `created_at`, `duration_s`, `agent_count`
3. **New endpoint `GET /memo/[id]`**: returns the same shape as the existing `/run/[id]/memo` but indexed by memo ID. May just be an alias.
4. **CORS**: open the existing FastAPI to the Vercel domain.

No DB schema changes — the checkpointer already persists runs.

## Out of Scope (v1)

- Authentication / per-user runs
- Editable / re-runnable memos
- Streaming agent artifacts mid-run (current SSE only emits status + summary; full artifact streams later)
- Mobile responsive (designed for desktop demo; basic mobile fallback is acceptable)
- `/ticker/[symbol]` page with thesis drift visualization (can ship in v1.1)
- Dark mode

## Open Questions / Risks

- **DAG layout**: the static SVG works for the canonical 14-agent flow, but if the graph topology changes the SVG will need rework. Acceptable risk — the topology is unlikely to change before the demo.
- **EventSource reconnection**: existing Streamlit app has retry logic; Next.js client must replicate this for the SSE stream.
- **Demo data**: for the landing page "Recent Memos", we need at least 3 real memo runs in the DB before the demo is presentable. Plan to run AAPL/NVDA/TSLA before deploying.

## Implementation Sequencing (preview)

1. Backend additions (company metadata, `/runs`, CORS)
2. Next.js scaffold + Tailwind + fonts + global brutalist tokens
3. Memo page (no streaming dependency; can be built and tested in isolation against a fixed run_id)
4. Three hero visualizations as standalone components
5. Landing page (depends on `/runs` endpoint)
6. Live run page (DAG + SSE streaming)
7. Deploy to Vercel + wire to Railway backend

A detailed plan will be produced separately by the writing-plans skill.
