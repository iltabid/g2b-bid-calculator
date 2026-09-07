"""나라장터 적격심사 표준 공식 계산.

예측·수집·머신러닝은 포함하지 않는다. 공개된 조달 규칙만 계산한다.

표준 낙찰하한가:
    (예정가격 - A값) × 낙찰하한율 + A값

예정가격 시나리오:
    예정가격 = 기초금액 × 사정률
    사정률은 예비가격 범위(예: 97% ~ 103%)에서 고른다.
"""

from __future__ import annotations

from collections import Counter
from decimal import Decimal, ROUND_DOWN
from itertools import combinations
from typing import Any

DEFAULT_LOWER_LIMIT_RATE_SERVICE = Decimal("88.0")
DEFAULT_LOWER_LIMIT_RATE_GOODS = Decimal("88.0")
DEFAULT_ASSESSMENT_RATE = Decimal("100.0")
DEFAULT_RESERVE_PRICE_RANGE_START = Decimal("-3.0")
DEFAULT_RESERVE_PRICE_RANGE_END = Decimal("3.0")


def _as_decimal(value: Decimal | int | float | str | None, default: Decimal = Decimal("0")) -> Decimal:
    if value is None:
        return default
    return Decimal(str(value))


def lower_limit_rate_for_construction(amount: Decimal | int | float | None) -> Decimal:
    """공사 낙찰하한율 구간표 (2025.1.30 시행, 조달청 적격심사 기준).

    공고 API의 ``sucsfbidLwltRate`` 가 없을 때만 쓰는 fallback.

    - 10억 미만: 89.745%
    - 10억 이상 ~ 50억 미만: 88.745%
    - 50억 이상: 87.495% (100억 이상은 종합심사인 경우가 많아 참고치)
    """
    try:
        value = float(amount or 0)
    except (TypeError, ValueError):
        value = 0.0
    if value <= 0:
        return Decimal("88.745")
    if value < 1_000_000_000:
        return Decimal("89.745")
    if value < 5_000_000_000:
        return Decimal("88.745")
    return Decimal("87.495")


def get_default_lower_limit_rate(
    task_type: str,
    estimated_price: Decimal | int | float | None = None,
    base_amount: Decimal | int | float | None = None,
) -> Decimal:
    """업무구분별 기본 낙찰하한율(%).

    공사는 기초금액(없으면 추정가격) 구간표를 쓴다.
    """
    if task_type == "공사":
        return lower_limit_rate_for_construction(base_amount or estimated_price)
    if task_type == "용역":
        return DEFAULT_LOWER_LIMIT_RATE_SERVICE
    if task_type in ("물품", "외자"):
        return DEFAULT_LOWER_LIMIT_RATE_GOODS
    return Decimal("88.0")


def get_default_reserve_price_range() -> tuple[Decimal, Decimal]:
    """기본 예비가격 범위율 (%, 시작/종료)."""
    return DEFAULT_RESERVE_PRICE_RANGE_START, DEFAULT_RESERVE_PRICE_RANGE_END


def calculate_bid_amount_range(
    base_amount: Decimal | int | float,
    a_value: Decimal | int | float | None = None,
    lower_limit_rate: Decimal | int | float | None = None,
    reserve_start_rate: Decimal | int | float | None = None,
    reserve_end_rate: Decimal | int | float | None = None,
    task_type: str = "공사",
    estimated_price: Decimal | int | float | None = None,
    use_a_value: bool = True,
) -> tuple[Decimal, Decimal, Decimal]:
    """유효 투찰가 범위 (최저, 중립, 최대).

    ``중립`` 은 사정률 100%(예정가격 = 기초금액) 가정이다.
    """
    base = _as_decimal(base_amount)
    if base <= 0:
        raise ValueError("base_amount must be positive")

    if lower_limit_rate is None:
        lower_limit_rate = get_default_lower_limit_rate(task_type, estimated_price, base)
    else:
        lower_limit_rate = _as_decimal(lower_limit_rate)

    default_start, default_end = get_default_reserve_price_range()
    if reserve_start_rate is None:
        reserve_start_rate = default_start
    if reserve_end_rate is None:
        reserve_end_rate = default_end
    reserve_start_rate = _as_decimal(reserve_start_rate)
    reserve_end_rate = _as_decimal(reserve_end_rate)

    start_ratio = (Decimal("100") + reserve_start_rate) / Decimal("100")
    end_ratio = (Decimal("100") + reserve_end_rate) / Decimal("100")

    effective_a = Decimal("0")
    if use_a_value:
        a = _as_decimal(a_value)
        if a > 0:
            effective_a = a

    lower_rate = lower_limit_rate / Decimal("100")

    def _bound(ratio: Decimal) -> Decimal:
        estimated = base * ratio
        if effective_a > 0:
            return ((estimated - effective_a) * lower_rate + effective_a).quantize(
                Decimal("1"), rounding=ROUND_DOWN
            )
        return (estimated * lower_rate).quantize(Decimal("1"), rounding=ROUND_DOWN)

    return _bound(start_ratio), _bound(Decimal("1.0")), _bound(end_ratio)


def generate_reserve_prices(
    base_amount: Decimal | int | float,
    total_count: int = 15,
    start_rate: Decimal | int | float | None = None,
    end_rate: Decimal | int | float | None = None,
) -> list[Decimal]:
    """등간격 복수예비가격 목록."""
    base = _as_decimal(base_amount)
    if start_rate is None or end_rate is None:
        default_start, default_end = get_default_reserve_price_range()
        if start_rate is None:
            start_rate = default_start
        if end_rate is None:
            end_rate = default_end
    start_rate = _as_decimal(start_rate)
    end_rate = _as_decimal(end_rate)

    min_price = base * (Decimal("100") + start_rate) / Decimal("100")
    max_price = base * (Decimal("100") + end_rate) / Decimal("100")

    if total_count <= 1:
        return [base.quantize(Decimal("1"), rounding=ROUND_DOWN)]

    step = (max_price - min_price) / (total_count - 1)
    return [
        (min_price + step * i).quantize(Decimal("1"), rounding=ROUND_DOWN)
        for i in range(total_count)
    ]


def calculate_average_probability_distribution(
    reserve_prices: list[Decimal | int | float],
    draw_count: int = 4,
) -> list[dict[str, Any]]:
    """복수예가 추첨 평균의 확률 분포.

    Returns:
        ``[{average, probability, count}, ...]``
    """
    prices = [_as_decimal(p) for p in reserve_prices]
    total_count = len(prices)
    if total_count < draw_count:
        return []

    all_combinations = list(combinations(prices, draw_count))
    total_combinations = len(all_combinations)
    averages = [
        int((sum(combo) / draw_count).quantize(Decimal("1"), rounding=ROUND_DOWN))
        for combo in all_combinations
    ]
    counter = Counter(averages)
    return [
        {
            "average": avg,
            "probability": round((count / total_combinations) * 100, 4),
            "count": count,
        }
        for avg, count in sorted(counter.items())
    ]


def calculate_top_candidate_bids(
    base_amount: Decimal | int | float,
    a_value: Decimal | int | float | None = None,
    lower_limit_rate: Decimal | int | float | None = None,
    reserve_start_rate: Decimal | int | float | None = None,
    reserve_end_rate: Decimal | int | float | None = None,
    total_count: int = 15,
    draw_count: int = 4,
    use_a_value: bool = True,
    n: int = 10,
    task_type: str = "공사",
    estimated_price: Decimal | int | float | None = None,
) -> list[dict[str, Any]]:
    """4/15 분포에서 누적확률을 균등 분할한 후보 투찰가 ``n`` 선.

    각 후보는 분위 위치의 평균예가를 예정가격으로 보고
    ``(예정가격 - A) × 낙찰하한율 + A`` 를 적용한 하한가이다.
    """
    base = _as_decimal(base_amount)
    if base <= 0:
        return []

    if lower_limit_rate is None:
        lower_limit_rate = get_default_lower_limit_rate(task_type, estimated_price, base)
    else:
        lower_limit_rate = _as_decimal(lower_limit_rate)

    default_start, default_end = get_default_reserve_price_range()
    if reserve_start_rate is None:
        reserve_start_rate = default_start
    if reserve_end_rate is None:
        reserve_end_rate = default_end

    reserve_prices = generate_reserve_prices(
        base, total_count, reserve_start_rate, reserve_end_rate
    )
    distribution = calculate_average_probability_distribution(reserve_prices, draw_count)
    if not distribution:
        return []

    sorted_dist = sorted(distribution, key=lambda d: d["average"])
    cumulative: list[tuple[int, float]] = []
    cum_prob = 0.0
    for item in sorted_dist:
        cum_prob += float(item["probability"])
        cumulative.append((item["average"], cum_prob))
    total_prob = cum_prob if cum_prob > 0 else 100.0

    effective_a = Decimal("0")
    if use_a_value:
        a = _as_decimal(a_value)
        if a > 0:
            effective_a = a

    lower_rate = lower_limit_rate / Decimal("100")
    candidates: list[dict[str, Any]] = []
    for k in range(1, n + 1):
        target = total_prob * (k - 0.5) / n
        chosen_avg = cumulative[-1][0]
        for avg, cp in cumulative:
            if cp >= target:
                chosen_avg = avg
                break

        estimated = Decimal(str(chosen_avg))
        rate_pct = (estimated / base * Decimal("100")).quantize(Decimal("0.0001"))
        if effective_a > 0:
            bid_amount = ((estimated - effective_a) * lower_rate + effective_a).quantize(
                Decimal("1"), rounding=ROUND_DOWN
            )
        else:
            bid_amount = (estimated * lower_rate).quantize(Decimal("1"), rounding=ROUND_DOWN)

        candidates.append(
            {
                "rank": k,
                "quantile_percent": round(target, 1),
                "assumed_rate_percent": float(rate_pct),
                "assumed_estimated_price": estimated,
                "bid_amount": bid_amount,
            }
        )
    return candidates


def calculate_actual_lower_bid(
    planned_price: Decimal | int | float | None,
    a_value: Decimal | int | float | None,
    lower_limit_rate: Decimal | int | float | None,
) -> Decimal | None:
    """확정 예정가격(개찰 후 plnprc)으로 투찰하한가를 계산.

    ``(예정가격 - A) × 낙찰하한율 + A``
    """
    if planned_price is None:
        return None
    planned = _as_decimal(planned_price)
    if planned <= 0 or lower_limit_rate is None:
        return None
    rate = _as_decimal(lower_limit_rate)
    if rate <= 0:
        return None
    effective_a = _as_decimal(a_value)
    if effective_a <= 0:
        effective_a = Decimal("0")
    raw = (planned - effective_a) * (rate / Decimal("100")) + effective_a
    return raw.quantize(Decimal("1"), rounding=ROUND_DOWN)


def calculate_qualification_score(
    base_amount: Decimal | int | float,
    five_year_revenue: Decimal | int | float | None = None,
    management_score: Decimal | int | float | None = None,
    credibility_score: Decimal | int | float | None = None,
) -> dict[str, float | None]:
    """적격심사 수행능력 점수 (조달청 100억 미만 공사 프레임).

    - 시공경험: 5년 실적 / (기초금액 × 실적배수), 최대 15점
      실적배수: 10억 미만 0.5, 10억~50억 1.0, 50억 이상 2.0
    - 경영상태: 입력값 (0~15)
    - 신인도: 입력값 (-8~+4)
    """
    base = _as_decimal(base_amount)
    if base <= 0:
        return {
            "experience_score": None,
            "management_score": None,
            "credibility_score": None,
            "performance_total": None,
        }

    if base < Decimal("1000000000"):
        ratio = Decimal("0.5")
    elif base < Decimal("5000000000"):
        ratio = Decimal("1.0")
    else:
        ratio = Decimal("2.0")

    experience = 0.0
    if five_year_revenue is not None:
        revenue = _as_decimal(five_year_revenue)
        target = base * ratio
        if target > 0:
            experience = min(15.0, max(0.0, float(revenue / target) * 15.0))

    management = float(management_score) if management_score is not None else 0.0
    management = min(15.0, max(0.0, management))
    credibility = float(credibility_score) if credibility_score is not None else 0.0
    credibility = max(-8.0, min(4.0, credibility))

    return {
        "experience_score": round(experience, 2),
        "management_score": round(management, 2),
        "credibility_score": round(credibility, 2),
        "performance_total": round(experience + management + credibility, 2),
    }


def calculate_eligible_bid_range(
    estimated_price: Decimal | int | float,
    a_value: Decimal | int | float | None,
    performance_total: float,
    pass_score: float = 95.0,
    price_score_max: float = 70.0,
    base_rate: float = 90.0,
    score_slope: float = 4.0,
) -> dict[str, Any]:
    """적격 통과를 위한 투찰가 허용 범위 역산 (3억~100억 공사 가격평점 프레임).

    평점 = price_score_max - score_slope × |base_rate - (입찰가-A)/(예정가-A)×100|
    """
    estimated = _as_decimal(estimated_price)
    if estimated <= 0:
        return {
            "required_price_score": None,
            "min_bid_amount": None,
            "neutral_bid_amount": None,
            "max_bid_amount": None,
            "feasible": False,
        }

    a = _as_decimal(a_value)
    if a <= 0:
        a = Decimal("0")

    required_price_score = pass_score - max(0.0, float(performance_total or 0))
    if required_price_score > price_score_max:
        return {
            "required_price_score": round(required_price_score, 2),
            "min_bid_amount": None,
            "neutral_bid_amount": None,
            "max_bid_amount": None,
            "feasible": False,
        }

    delta_pct = max(0.0, (price_score_max - required_price_score) / score_slope)
    base_ratio = Decimal(str(base_rate / 100.0))
    delta = Decimal(str(delta_pct / 100.0))
    low_ratio = max(Decimal("0"), base_ratio - delta)
    high_ratio = base_ratio + delta

    def _bid(ratio: Decimal) -> int:
        value = (estimated - a) * ratio + a if a > 0 else estimated * ratio
        return int(value.quantize(Decimal("1"), rounding=ROUND_DOWN))

    return {
        "required_price_score": round(required_price_score, 2),
        "min_bid_amount": _bid(low_ratio),
        "neutral_bid_amount": _bid(base_ratio),
        "max_bid_amount": _bid(high_ratio),
        "feasible": True,
    }
