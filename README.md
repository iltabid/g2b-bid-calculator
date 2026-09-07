# g2b-bid-calculator

나라장터(조달청 G2B) **적격심사**에서 쓰는 공개 산식을 파이썬으로 계산합니다.

- 유효 투찰가 범위 (최저 / 중립 / 최대)
- 복수예비가격 4/15 평균 분포
- 후보 투찰가 n선
- 적격심사 수행능력 점수와 통과 가능 투찰 구간

예측·낙찰 통계·공고 수집은 포함하지 않습니다. 그 데이터는 [일타비드](https://ilta.kr)에서 확인하세요.

## 설치

```bash
pip install g2b-bid-calculator
```

저장소에서 바로 쓰려면:

```bash
pip install -e .
```

## 빠른 예제

```python
from decimal import Decimal
from g2b_bid_calculator import calculate_bid_amount_range

min_bid, mid_bid, max_bid = calculate_bid_amount_range(
    base_amount=Decimal("1_000_000_000"),
    a_value=Decimal("40_000_000"),
    lower_limit_rate=Decimal("88.745"),
    reserve_start_rate=Decimal("-2"),
    reserve_end_rate=Decimal("2"),
)
print(min_bid, mid_bid, max_bid)
```

공사 낙찰하한율(2025.1.30 구간표)을 기초금액으로 고르려면 `task_type="공사"` 만 넘기면 됩니다. 공고에 `sucsfbidLwltRate`가 있으면 그 값을 `lower_limit_rate`로 넣는 편이 정확합니다.

## 공식

낙찰하한가:

```
(예정가격 − A값) × 낙찰하한율 + A값
예정가격 = 기초금액 × 사정률
```

A값을 쓰지 않으면 A=0으로 계산합니다. 금액은 원 단위 `ROUND_DOWN`입니다.

공사 낙찰하한율 fallback (API 값이 없을 때):

| 추정/기초금액 | 낙찰하한율 |
|---|---|
| 10억 미만 | 89.745% |
| 10억 이상 ~ 50억 미만 | 88.745% |
| 50억 이상 | 87.495% |

100억 이상 종합심사 공고는 이 라이브러리 범위를 벗어납니다.

## API

| 함수 | 역할 |
|---|---|
| `calculate_bid_amount_range` | 유효 투찰가 최저·중립·최대 |
| `generate_reserve_prices` | 등간격 복수예비가격 |
| `calculate_average_probability_distribution` | 4/15 평균 확률 분포 |
| `calculate_top_candidate_bids` | 분포 분위 후보 n선 |
| `calculate_actual_lower_bid` | 개찰 후 확정 예정가 기준 하한가 |
| `calculate_qualification_score` | 시공경험·경영·신인도 합산 |
| `calculate_eligible_bid_range` | 적격 통과 투찰 구간 역산 |
| `lower_limit_rate_for_construction` | 공사 하한율 구간표 |

문서: [iltabid.github.io/g2b-bid-calculator](https://iltabid.github.io/g2b-bid-calculator/)

## 일타비드

과거 낙찰 통계, 유사 공고, AI 추천 투찰가는 [ilta.kr](https://ilta.kr)에서 볼 수 있습니다.

- [지식창고](https://ilta.kr/learn/)
- [예측 정확도](https://ilta.kr/analysis/accuracy/)
- [적격심사 계산기](https://ilta.kr/analysis/qualification-calculator/)
- [투찰 시뮬레이터](https://ilta.kr/analysis/bids/simulate/)

이 패키지는 규칙 계산만 합니다. 낙찰을 보장하지 않습니다.

## 라이선스

MIT
