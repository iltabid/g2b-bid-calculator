---
layout: default
title: g2b-bid-calculator
---

# g2b-bid-calculator

나라장터 적격심사 **규칙 계산** 라이브러리입니다. 예측 모델이나 공고 수집기는 넣지 않았습니다.

소스: [github.com/iltabid/g2b-bid-calculator](https://github.com/iltabid/g2b-bid-calculator)

```bash
pip install g2b-bid-calculator
```

## 표준 공식

```
낙찰하한가 = (예정가격 − A값) × 낙찰하한율 + A값
예정가격   = 기초금액 × 사정률
```

A값이 없으면 0으로 봅니다. 원 단위 절사(`ROUND_DOWN`).

### 공사 낙찰하한율 fallback (2025.1.30)

공고 API `sucsfbidLwltRate`가 있을 때는 그 값을 우선하세요.

| 금액 | 낙찰하한율 |
|---|---|
| 10억 미만 | 89.745% |
| 10억 ~ 50억 미만 | 88.745% |
| 50억 이상 | 87.495% |

## 예제

```python
from decimal import Decimal
from g2b_bid_calculator import (
    calculate_bid_amount_range,
    calculate_top_candidate_bids,
    calculate_qualification_score,
)

min_bid, mid_bid, max_bid = calculate_bid_amount_range(
    base_amount=Decimal("1000000000"),
    a_value=Decimal("40000000"),
    lower_limit_rate=Decimal("88.745"),
    reserve_start_rate=Decimal("-2"),
    reserve_end_rate=Decimal("2"),
)

candidates = calculate_top_candidate_bids(
    base_amount=Decimal("1000000000"),
    a_value=Decimal("40000000"),
    reserve_start_rate=Decimal("-2"),
    reserve_end_rate=Decimal("2"),
    n=10,
)

score = calculate_qualification_score(
    base_amount=Decimal("1000000000"),
    five_year_revenue=Decimal("800000000"),
    management_score=15,
    credibility_score=1,
)
```

## API

| 함수 | 설명 |
|---|---|
| `calculate_bid_amount_range` | 유효 투찰가 최저·중립·최대 |
| `generate_reserve_prices` | 등간격 복수예비가격 |
| `calculate_average_probability_distribution` | 4/15 평균 확률 |
| `calculate_top_candidate_bids` | 분포 분위 후보 n선 |
| `calculate_actual_lower_bid` | 확정 예정가 기준 하한가 |
| `calculate_qualification_score` | 수행능력 점수 |
| `calculate_eligible_bid_range` | 적격 통과 투찰 구간 |
| `lower_limit_rate_for_construction` | 공사 하한율 구간표 |

## 일타비드

통계·유사 공고·AI 추천 투찰가는 본진에서 제공합니다. 이 문서는 라이브러리 레퍼런스입니다.

- [일타비드](https://ilta.kr)
- [지식창고](https://ilta.kr/learn/)
- [예측 정확도](https://ilta.kr/analysis/accuracy/)
- [적격심사 계산기](https://ilta.kr/analysis/qualification-calculator/)
