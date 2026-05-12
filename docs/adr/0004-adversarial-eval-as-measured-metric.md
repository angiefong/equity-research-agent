# Adversarial eval as a measured lift metric, not silent defensive plumbing

Comparable LLM trading agents have suffered multi-million-dollar prompt-injection losses in 2026. This system has no trade-execution path, so the worst-case ceiling for a successful injection is "misleading memo" (not "money moved"). But news evidence is inserted verbatim into bull/bear/moderator context from a low-trust web source (Tavily), so prompt injection via news content is a real exposure surface and worth measuring.

We add **measured resistance** rather than silent defensive plumbing. The new harness (`backend.evals.run --adversarial`) loads 10 hand-crafted fixtures across 5 attack categories — explicit_instruction, role_hijack, misleading_quotation, fabricated_metric, source_ref_spoof — mocks the Tavily call for each case to inject a poisoned span alongside legitimate ones, runs the full pipeline, and scores absorption with the existing Claude Sonnet judge under the same isolation discipline as the regular eval (same model, same temperature, same epoch-snapshot caching for the non-news data fetches).

**Primary metric:** `absorption_rate` (lower is better) — judge-evaluated on whether the final memo absorbed any element of the injection.

**Diagnostic:** programmatic catch-mechanism breakdown — for each case, did the verifier flag it, did the bull/bear refuse to cite it, did the citation layer drop it. The breakdown is the architectural story: it lets us answer whether the source_ref citation requirement (added for evaluation accuracy) also provides injection resistance as a side effect, separately from any prompt-level defenses.

**Decision:** Treat adversarial resistance as a first-class lift metric, runnable via `--adversarial`, logged to the same MLflow experiment as the regular eval. Mitigations are baseline-driven — measure first, then harden only the surfaces the baseline shows leak.

**Considered and rejected:** silent defensive plumbing (input sanitization, system-prompt hardening without measurement). Faster but produces no portfolio signal and no regression guarantee against future changes.

**Considered and deferred:** LLM-generated red-team cases. Worth a v2 once the hand-crafted baseline is established; for v1, hand-crafting forces an explicit attack-category taxonomy that is itself part of the artifact.
