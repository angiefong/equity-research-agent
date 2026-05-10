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
