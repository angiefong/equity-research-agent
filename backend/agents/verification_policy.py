MAX_REROUTE_ATTEMPTS = 2


def should_reroute(status: str, reroute_count: int) -> bool:
    return status == "needs_reroute" and reroute_count < MAX_REROUTE_ATTEMPTS
