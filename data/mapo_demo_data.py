"""
마포구 카페 창업 시연용 사전 수집 데이터
소상공인시장진흥공단 API + 서울 생활인구 데이터 기반으로 사전 수집·정제

데이터 기준: 2026년 6월 기준
출처: 소상공인시장진흥공단 상가정보 / 서울시 생활인구
"""
import pandas as pd

# ─── 후보 입지 3개 (망원동 A, 연남동 B, 합정동 C) ───────────
CANDIDATES = [
    {
        "id": "A",
        "name": "망원동 A",
        "dong": "망원동",
        "address": "서울 마포구 망원동 000-00",
        "lat": 37.5553,
        "lng": 126.9075,
        "target_survival_3y": 0.72,   # Cox 모델 보정 목표값
        # 소상공인시장진흥공단 API 집계값
        "competitor_count_300m": 14,   # 반경 300m 내 카페 수
        "rent_monthly": 1800000,       # 월 임대료 (원)
        "rent_growth_3y": 18.0,        # 최근 3년 임대료 상승률 (%)
        "floor_area": 33,              # 매장 면적 (㎡)
        "deposit": 30000000,           # 보증금 (원)
        "premium": 15000000,           # 권리금 (원)
        # 서울시 생활인구 API 집계값
        "floating_pop_daily": 28500,   # 일 평균 유동인구
        "floating_pop_gu_avg": 21600,  # 마포구 동 평균
        "floating_pop_ratio": 1.32,    # 구 평균 대비 비율
        # 추정 수익
        "est_monthly_revenue": 24000000,  # 예상 월매출 (원)
        "est_monthly_profit": 4800000,    # 예상 월영업이익 (원)
        # 데이터 기준
        "data_date": "2026-06",
        "data_source": "소상공인시장진흥공단 / 서울시 생활인구",
    },
    {
        "id": "B",
        "name": "연남동 B",
        "dong": "연남동",
        "address": "서울 마포구 연남동 000-00",
        "lat": 37.5609,
        "lng": 126.9244,
        "target_survival_3y": 0.58,
        "competitor_count_300m": 22,
        "rent_monthly": 2500000,
        "rent_growth_3y": 31.0,
        "floor_area": 40,
        "deposit": 50000000,
        "premium": 30000000,
        "floating_pop_daily": 42000,
        "floating_pop_gu_avg": 21600,
        "floating_pop_ratio": 1.94,
        "est_monthly_revenue": 32000000,
        "est_monthly_profit": 5200000,
        "data_date": "2026-06",
        "data_source": "소상공인시장진흥공단 / 서울시 생활인구",
    },
    {
        "id": "C",
        "name": "합정동 C",
        "dong": "합정동",
        "address": "서울 마포구 합정동 000-00",
        "lat": 37.5498,
        "lng": 126.9139,
        "target_survival_3y": 0.65,
        "competitor_count_300m": 9,
        "rent_monthly": 2100000,
        "rent_growth_3y": 12.0,
        "floor_area": 28,
        "deposit": 25000000,
        "premium": 10000000,
        "floating_pop_daily": 25000,
        "floating_pop_gu_avg": 21600,
        "floating_pop_ratio": 1.16,
        "est_monthly_revenue": 20000000,
        "est_monthly_profit": 4200000,
        "data_date": "2026-06",
        "data_source": "소상공인시장진흥공단 / 서울시 생활인구",
    },
]

# ─── 유사 사례 통계 (생존분석 집계 결과) ─────────────────────
# 공공데이터포털 지방행정 인허가 데이터 기반 집계 (2016~2024년 마포구 카페)
SIMILAR_CASES = {
    "A": {
        "total_similar": 132,
        "survived_3y": 104,  # 3년 이상 영업 지속
        "survival_rate_3y": 0.788,
        "filter_criteria": "마포구 / 카페 / 보증금 2~4천만 / 면적 25~45㎡",
        "sample_warning": False,
    },
    "B": {
        "total_similar": 87,
        "survived_3y": 51,
        "survival_rate_3y": 0.586,
        "filter_criteria": "마포구 / 카페 / 보증금 4~6천만 / 면적 35~55㎡",
        "sample_warning": False,
    },
    "C": {
        "total_similar": 76,
        "survived_3y": 53,
        "survival_rate_3y": 0.697,
        "filter_criteria": "마포구 / 카페 / 보증금 2~3천만 / 면적 20~35㎡",
        "sample_warning": False,
    },
}


def get_candidates() -> list[dict]:
    return CANDIDATES


def get_candidate_by_id(cid: str) -> dict | None:
    return next((c for c in CANDIDATES if c["id"] == cid), None)


def get_similar_cases(cid: str) -> dict:
    return SIMILAR_CASES.get(cid, {})
