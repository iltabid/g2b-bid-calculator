from decimal import Decimal

from g2b_bid_calculator import (
    calculate_actual_lower_bid,
    calculate_average_probability_distribution,
    calculate_bid_amount_range,
    calculate_eligible_bid_range,
    calculate_qualification_score,
    calculate_top_candidate_bids,
    generate_reserve_prices,
    get_default_lower_limit_rate,
    lower_limit_rate_for_construction,
)


BANDS = [
    (Decimal("500000000"), Decimal("89.745")),
    (Decimal("999999999"), Decimal("89.745")),
    (Decimal("1000000000"), Decimal("88.745")),
    (Decimal("4999999999"), Decimal("88.745")),
    (Decimal("5000000000"), Decimal("87.495")),
    (Decimal("20000000000"), Decimal("87.495")),
]


def test_construction_lower_limit_bands():
    for amount, expected in BANDS:
        assert lower_limit_rate_for_construction(amount) == expected


def test_construction_fallback_is_not_pre_2025_rate():
    assert get_default_lower_limit_rate("공사", None, Decimal("500000000")) != Decimal("87.745")


def test_range_uses_base_amount_band():
    base = Decimal("500000000")
    _, neutral, _ = calculate_bid_amount_range(base, task_type="공사")
    assert neutral == (base * Decimal("89.745") / Decimal("100")).to_integral_value()


def test_a_value_standard_formula():
    base = Decimal("1000000000")
    a_value = Decimal("50000000")
    lower = Decimal("88.745")
    min_bid, neutral, max_bid = calculate_bid_amount_range(
        base,
        a_value=a_value,
        lower_limit_rate=lower,
        reserve_start_rate=Decimal("-2"),
        reserve_end_rate=Decimal("2"),
        use_a_value=True,
    )
    rate = lower / Decimal("100")
    expected_neutral = ((base - a_value) * rate + a_value).to_integral_value()
    assert neutral == expected_neutral
    assert min_bid < neutral < max_bid


def test_actual_lower_bid_matches_standard_formula():
    result = calculate_actual_lower_bid(Decimal("1000000000"), Decimal("40000000"), Decimal("89.745"))
    expected = (
        (Decimal("1000000000") - Decimal("40000000")) * Decimal("0.89745") + Decimal("40000000")
    ).to_integral_value()
    assert result == expected


def test_reserve_distribution_stays_in_plus_minus_2():
    base = Decimal("1000000000")
    prices = generate_reserve_prices(base, start_rate=Decimal("-2"), end_rate=Decimal("2"))
    distribution = calculate_average_probability_distribution(prices, draw_count=4)
    averages = [row["average"] for row in distribution]
    assert min(averages) >= 980_000_000
    assert max(averages) <= 1_020_000_000
    assert abs(sum(row["probability"] for row in distribution) - 100.0) < 0.01


def test_candidate_bids_use_same_range():
    candidates = calculate_top_candidate_bids(
        Decimal("1000000000"),
        lower_limit_rate=Decimal("88.745"),
        reserve_start_rate=Decimal("-2"),
        reserve_end_rate=Decimal("2"),
        n=10,
    )
    assert len(candidates) == 10
    estimates = [int(c["assumed_estimated_price"]) for c in candidates]
    assert min(estimates) >= 980_000_000
    assert max(estimates) <= 1_020_000_000


def test_qualification_score_and_eligible_range():
    scores = calculate_qualification_score(
        Decimal("3000000000"),
        five_year_revenue=Decimal("3000000000"),
        management_score=15,
        credibility_score=2,
    )
    assert scores["experience_score"] == 15.0
    assert scores["performance_total"] == 32.0

    eligible = calculate_eligible_bid_range(
        Decimal("3000000000"),
        a_value=None,
        performance_total=32.0,
    )
    assert eligible["feasible"] is True
    assert eligible["min_bid_amount"] < eligible["neutral_bid_amount"] < eligible["max_bid_amount"]


def test_infeasible_when_performance_too_low():
    eligible = calculate_eligible_bid_range(
        Decimal("3000000000"),
        a_value=None,
        performance_total=20.0,
        pass_score=95.0,
        price_score_max=70.0,
    )
    assert eligible["feasible"] is False
    assert eligible["min_bid_amount"] is None
