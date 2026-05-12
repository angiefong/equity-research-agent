# No shared `Step` framework for LLM-call agents

The LLM-call agents (`bull`, `bear`, `verifier`, `evidence_contradiction`, `debate_contradiction`, `moderator`) follow a similar surface recipe — format state into context, call `get_structured_llm(Schema)`, invoke with `[system, user]` messages, map the result back into state. The file sizes (40–200 LOC, dominated by long system prompts) suggest an opportunity to extract a declarative `Step` framework where each agent is a record of *(state_reads, prompt, schema, state_writes)*. We considered this and rejected it.

The *actually shared* code across these agents is roughly five lines (`llm = get_structured_llm(Schema, method=...)`, `result = llm.invoke([...])`, `return {...}`). Everything else varies in non-uniform ways:

- Drift-tolerance validators unwrap different wrapper keys per agent (`bull_case`, `bear_case`, no wrapper for verifier, nested `memo` for moderator). They look structurally similar but share no code.
- State-formatting helpers differ: `format_evidence` is shared, but `_format_debate`, `_format_contradictions`, and moderator's `_coerce_to_str` are bespoke.
- Output mapping varies (DebatePoint with side enum, VerificationIssue list with severity-driven status classification, ResearchMemo with weight computation and metadata join).
- The bull and verifier system prompts encode load-bearing per-agent rules (arithmetic-sanity check, severity policy, data-recency rule) that recent evaluation lift (2026-05-09, +1.08) came from. Flattening agents into config makes targeted per-agent prompt tweaks harder, not easier.

A `Step` framework would have to subsume all of this variation, which collapses the leverage. By the deletion test: deleting the framework would expose the same bespoke code in each agent — it isn't earning locality.

**Decision:** Keep agents as bespoke modules. The shared 5-LOC LLM-call pattern is a code-duplication concern small enough that addressing it would cost more than it saves.

**When to revisit:** If Phase 2 fine-tuning standardises prompt shape and removes the per-agent rule variation, the case for shared infrastructure may strengthen. Reassess after the fine-tuned model lands.
