# Keep the per-source agent layer for evidence-fetching nodes

The four evidence-fetching graph nodes (`market_data`, `filings`, `news`, `quant_data`) each have a thin module in `backend/agents/` that wraps a function in `backend/tools/`. The file sizes (7–22 LOC) invite the suggestion to collapse them into a single generic fetch-node factory parameterised by tool. We considered this and rejected it.

Two of the four are **not** pass-throughs:

- `agents/market_data.py` also fetches `get_company_overview()` and extracts `company_name`, `exchange`, `sector` into `AgentState`. Those keys are read by the moderator (`agents/moderator.py:203-205`) into the final memo (`schemas/memo.py:24-26`). State-shape concern, not an evidence-fetching concern.
- `agents/quant_data.py` owns `PEER_MAP` and composes three tool calls (`compute_returns`, `compute_volatility`, `fetch_peer_comps`). Bespoke orchestration.

A factory absorbing all four would have to leak parameters for "extra state writes" and "tool composition", subsuming heterogeneous behaviour behind a narrow-looking interface — the anti-pattern the architecture-review skill flags ("interface as complex as implementation, just spread further"). Collapsing only `news` and `filings` leaves an inconsistent style that's worse than the current uniformity.

**Decision:** Keep the per-source agent layer as-is. The uniformity at the graph-builder level is worth more than the ~14 LOC the collapse would save.

**When to revisit:** If a fifth or sixth evidence-fetching source is added and most of them are pure pass-throughs, the balance shifts. Reassess then.
