from decimal import Decimal

from g2b_bid_calculator import (
    calculate_bid_amount_range,
    calculate_qualification_score,
    calculate_top_candidate_bids,
)

base = Decimal("1_000_000_000")
a_value = Decimal("40_000_000")

min_bid, mid_bid, max_bid = calculate_bid_amount_range(
    base_amount=base,
    a_value=a_value,
    task_type="공사",
    reserve_start_rate=Decimal("-2"),
    reserve_end_rate=Decimal("2"),
)
print(f"유효 투찰가: {min_bid:,} ~ {mid_bid:,} ~ {max_bid:,}")

for row in calculate_top_candidate_bids(
    base_amount=base,
    a_value=a_value,
    reserve_start_rate=Decimal("-2"),
    reserve_end_rate=Decimal("2"),
    n=5,
):
    print(
        f"#{row['rank']} 사정률 {row['assumed_rate_percent']:.4f}% → {row['bid_amount']:,}원"
    )

score = calculate_qualification_score(
    base_amount=base,
    five_year_revenue=Decimal("800_000_000"),
    management_score=15,
    credibility_score=1,
)
print("수행능력:", score)
