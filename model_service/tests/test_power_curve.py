from app.power_curve import estimate_capacity_factor


def test_power_curve_below_cut_in():
    assert estimate_capacity_factor(2.0) == 0.0


def test_power_curve_rated_region():
    assert estimate_capacity_factor(12.0) == 1.0


def test_power_curve_cut_out():
    assert estimate_capacity_factor(30.0) == 0.0


def test_power_curve_ramp_between_zero_and_one():
    cf = estimate_capacity_factor(8.0)
    assert 0.0 < cf < 1.0
