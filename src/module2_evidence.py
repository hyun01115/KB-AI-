"""
[모듈2] 추천 근거 카드 생성
Cox 모델 해저드비 → 사람이 이해할 수 있는 설명 문장으로 변환
"""
from __future__ import annotations
from config.settings import COX_BETA
import math


# 항목별 해저드비 설명 템플릿
_TEMPLATES = {
    "competitor_count_300m": (
        "반경 300m 내 {category} {value}개 — "
        "경쟁 점포 1개 증가마다 폐업 위험 {hr_pct:.0f}% 상승 (통계적 경향)",
        "소상공인시장진흥공단",
    ),
    "rent_growth_3y": (
        "최근 3년 임대료 {value:.0f}% 상승 — "
        "임대료 상승률 1%p마다 폐업 위험 {hr_pct:.1f}% 상승 (통계적 경향)",
        "소상공인시장진흥공단",
    ),
    "floating_pop_ratio": (
        "일 평균 유동인구 구 평균 대비 +{value_pct:.0f}% — "
        "유동인구 비율이 높을수록 폐업 위험 감소 (통계적 경향)",
        "서울시 생활인구 (2026.06)",
    ),
    "floor_area": (
        "매장 면적 {value}㎡ — "
        "면적이 넓을수록 고정비 증가 부담 완화에 유리 (통계적 경향)",
        "소상공인시장진흥공단",
    ),
}


def generate_evidence_cards(candidate: dict,
                             survival_result: dict,
                             category: str = "카페") -> list[dict]:
    """
    후보 입지 1개에 대한 근거 카드 생성 (최소 3개 이상)

    Returns
    -------
    list[dict]:
        item        : str  항목명
        sentence    : str  설명 문장
        value_str   : str  수치 표시
        direction   : str  "good" | "bad" | "neutral"
        data_source : str
    """
    beta = COX_BETA
    cards = []

    # 1. 경쟁 점포 수
    competitor = candidate.get("competitor_count_300m", 10)
    hr = math.exp(beta["competitor_count_300m"])
    hr_pct = (hr - 1) * 100
    direction = "bad" if competitor > 15 else "neutral" if competitor > 8 else "good"
    tmpl, src = _TEMPLATES["competitor_count_300m"]
    cards.append({
        "item": "경쟁 점포 수",
        "sentence": tmpl.format(category=category, value=competitor, hr_pct=hr_pct),
        "value_str": f"반경 300m 내 {competitor}개",
        "direction": direction,
        "data_source": src,
        "data_date": candidate.get("data_date", "2026-06"),
    })

    # 2. 임대료 상승률
    rent_growth = candidate.get("rent_growth_3y", 10.0)
    hr = math.exp(beta["rent_growth_3y"])
    hr_pct = (hr - 1) * 100
    direction = "bad" if rent_growth > 20 else "neutral" if rent_growth > 10 else "good"
    tmpl, src = _TEMPLATES["rent_growth_3y"]
    cards.append({
        "item": "임대료 상승 추이",
        "sentence": tmpl.format(value=rent_growth, hr_pct=hr_pct),
        "value_str": f"3년 +{rent_growth:.0f}%",
        "direction": direction,
        "data_source": src,
        "data_date": candidate.get("data_date", "2026-06"),
    })

    # 3. 유동인구
    pop_ratio = candidate.get("floating_pop_ratio", 1.0)
    pop_daily = candidate.get("floating_pop_daily", 21600)
    gu_avg    = candidate.get("floating_pop_gu_avg", 21600)
    pct_above = (pop_ratio - 1.0) * 100
    direction = "good" if pop_ratio > 1.2 else "neutral" if pop_ratio > 0.9 else "bad"
    tmpl, src = _TEMPLATES["floating_pop_ratio"]
    cards.append({
        "item": "유동인구",
        "sentence": tmpl.format(value_pct=abs(pct_above)),
        "value_str": f"일 {pop_daily:,}명 (구 평균 {gu_avg:,}명)",
        "direction": direction,
        "data_source": src,
        "data_date": candidate.get("data_date", "2026-06"),
    })

    # 4. 면적
    area = candidate.get("floor_area", 30)
    direction = "good" if area >= 30 else "neutral"
    tmpl, src = _TEMPLATES["floor_area"]
    cards.append({
        "item": "매장 면적",
        "sentence": tmpl.format(value=area),
        "value_str": f"{area}㎡",
        "direction": direction,
        "data_source": src,
        "data_date": candidate.get("data_date", "2026-06"),
    })

    return cards
