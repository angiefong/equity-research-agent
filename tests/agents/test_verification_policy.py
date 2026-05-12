from backend.agents.verification_policy import should_reroute, MAX_REROUTE_ATTEMPTS


def test_reroute_when_needed_and_under_cap():
    assert should_reroute("needs_reroute", 0) is True
    assert should_reroute("needs_reroute", MAX_REROUTE_ATTEMPTS - 1) is True


def test_no_reroute_at_or_above_cap():
    assert should_reroute("needs_reroute", MAX_REROUTE_ATTEMPTS) is False
    assert should_reroute("needs_reroute", MAX_REROUTE_ATTEMPTS + 1) is False


def test_no_reroute_for_other_statuses():
    for status in ("pass", "fail", "pending", ""):
        assert should_reroute(status, 0) is False
