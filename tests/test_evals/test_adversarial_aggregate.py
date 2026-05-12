from backend.evals.adversarial import (
    AdversarialCategory,
    AdversarialJudgment,
    AdversarialResult,
    CatchBreakdown,
    aggregate_results,
    build_adversarial_summary,
)


def _result(case_id, category, absorbed, *, verifier=False, agent_refused=True, citation_caught=True):
    return AdversarialResult(
        case_id=case_id,
        ticker="AAPL",
        category=category,
        judgment=AdversarialJudgment(absorbed=absorbed, rationale="r"),
        breakdown=CatchBreakdown(
            verifier_flagged=verifier,
            agent_refused=agent_refused,
            citation_layer_caught=citation_caught,
            absorbed=absorbed,
        ),
    )


def test_aggregate_computes_absorption_rate():
    results = [
        _result("a", AdversarialCategory.EXPLICIT_INSTRUCTION, absorbed=True),
        _result("b", AdversarialCategory.EXPLICIT_INSTRUCTION, absorbed=False),
        _result("c", AdversarialCategory.ROLE_HIJACK, absorbed=False),
        _result("d", AdversarialCategory.ROLE_HIJACK, absorbed=False),
    ]
    agg = aggregate_results(results)
    assert agg.total_cases == 4
    assert agg.absorbed == 1
    assert agg.absorption_rate == 0.25


def test_aggregate_per_category_rates():
    results = [
        _result("a", AdversarialCategory.EXPLICIT_INSTRUCTION, absorbed=True),
        _result("b", AdversarialCategory.EXPLICIT_INSTRUCTION, absorbed=False),
        _result("c", AdversarialCategory.ROLE_HIJACK, absorbed=False),
        _result("d", AdversarialCategory.ROLE_HIJACK, absorbed=False),
    ]
    agg = aggregate_results(results)
    assert agg.by_category["explicit_instruction"]["rate"] == 0.5
    assert agg.by_category["role_hijack"]["rate"] == 0.0


def test_aggregate_catch_breakdown_counts():
    results = [
        _result("a", AdversarialCategory.EXPLICIT_INSTRUCTION, absorbed=False, verifier=True),
        _result("b", AdversarialCategory.EXPLICIT_INSTRUCTION, absorbed=False, verifier=False),
        _result("c", AdversarialCategory.ROLE_HIJACK, absorbed=False, verifier=True),
    ]
    agg = aggregate_results(results)
    assert agg.catch_breakdown["verifier_flagged"] == 2
    assert agg.catch_breakdown["agent_refused"] == 3
    assert agg.catch_breakdown["citation_layer_caught"] == 3


def test_aggregate_empty_results():
    agg = aggregate_results([])
    assert agg.total_cases == 0
    assert agg.absorbed == 0
    assert agg.absorption_rate == 0.0


def test_build_summary_renders_key_sections():
    results = [
        _result("a", AdversarialCategory.EXPLICIT_INSTRUCTION, absorbed=True),
        _result("b", AdversarialCategory.ROLE_HIJACK, absorbed=False, verifier=True),
    ]
    agg = aggregate_results(results)
    md = build_adversarial_summary(agg, {"branch": "main", "agent_model": "x", "judge_model": "y"})
    assert "Adversarial Eval Report" in md
    assert "Absorption rate" in md
    assert "50%" in md  # 1 of 2 absorbed
    assert "explicit_instruction" in md
    assert "role_hijack" in md
    assert "verifier_flagged" in md
    assert "| a |" in md  # per-case row
    assert "| b |" in md
