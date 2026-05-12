# No typed state-contract enforcement layer

`AgentState` is a 16-key `TypedDict` shared by every node in the LangGraph pipeline. Each node reads and writes an ad-hoc subset of those keys, and nothing enforces that reads or writes match a declared contract — a typo in a state-key write silently lands in nowhere. The architecture-review skill flagged this as a candidate for adding typed node signatures + runtime validation. We considered this and rejected it.

The class of bug this would catch — a misspelled key, a node writing to a key not in `AgentState`, a node reading a key that may not be set — has not appeared in this repo's history. `git log --all -S "state["` shows no incidents matching the pattern. The current `NotRequired[Optional[...]]` annotations on state.py keys already give Python's static analysis (and IDE) enough to flag the obvious cases.

Adding a runtime enforcement harness would mean:

- Declaring read-set and write-set for every node (~14 nodes × 2 lists each = ~28 new declarations).
- A wrapper layer at registration time + per-invocation validation cost.
- A second source of truth (signatures vs. the `TypedDict`) that must be kept in sync.

That is *adding infrastructure for a hypothetical problem*. The LANGUAGE.md principle "one adapter = hypothetical seam" applies: we have zero observed incidents, so we'd be building protection against a problem we don't have.

**Decision:** Keep `AgentState` as a `TypedDict` with field-level annotations. Rely on Python's static analysis and on integration tests to catch state-shape bugs.

**When to revisit:** If we ship a state-key bug to production (or eval), or if state grows past ~25 keys and the cognitive load becomes a problem, reconsider. Also revisit if we add multi-team contribution to the agents/ layer — the implicit contract is harder to learn for new contributors than for the original authors.
