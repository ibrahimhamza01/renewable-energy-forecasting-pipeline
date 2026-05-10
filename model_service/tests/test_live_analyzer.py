from app.live_analyzer import classify_condition, estimate_24h_outlook


def test_classify_above_normal():
    label = classify_condition(current_cf=0.30, avg_cf=0.20, volatility=0.05)
    assert label == "above_normal"


def test_outlook_range_is_clipped():
    outlook = estimate_24h_outlook(current_cf=0.98, avg_cf=0.90, volatility=0.20)
    low, high = outlook["estimated_capacity_factor_range"]
    assert 0.0 <= low <= 1.0
    assert 0.0 <= high <= 1.0
