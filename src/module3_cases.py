"""
[모듈3] 유사 사례 카드
업종·지역·예산대가 비슷한 과거 점포의 생존 통계 제공
"""
from __future__ import annotations
from config.settings import SURVIVAL_MIN_SAMPLE


def generate_similar_case_card(cases: dict, candidate_name: str) -> dict:
    """
    유사 사례 통계 카드 생성

    Parameters
    ----------
    cases : dict  data_fetcher.fetch_survival_cases() 반환값

    Returns
    -------
    dict:
        total_similar       : int
        survived_3y         : int
        survival_rate_3y    : float
        summary_sentence    : str   화면 표시용 문장
        filter_criteria     : str
        sample_warning      : bool  (표본 부족 경고)
        sample_warning_msg  : str
    """
    total   = cases.get("total_similar", 0)
    survived = cases.get("survived_3y", 0)
    rate    = cases.get("survival_rate_3y", 0.0)
    warning = total < SURVIVAL_MIN_SAMPLE

    rate_pct = round(rate * 100, 1)
    if total > 0:
        sentence = (
            f"'{candidate_name}'과 조건이 비슷한 카페 {total}곳 중 "
            f"{survived}곳({rate_pct}%)이 3년 이상 영업을 지속했습니다."
        )
    else:
        sentence = "유사 사례 데이터가 충분하지 않습니다. 참고용으로만 활용하세요."

    return {
        "total_similar":    total,
        "survived_3y":      survived,
        "survival_rate_3y": rate,
        "summary_sentence": sentence,
        "filter_criteria":  cases.get("filter_criteria", ""),
        "sample_warning":   warning,
        "sample_warning_msg": (
            f"⚠ 유사 사례 표본({total}개)이 기준({SURVIVAL_MIN_SAMPLE}개)보다 "
            f"적어 통계 신뢰도가 낮습니다. 참고용으로만 활용하세요."
            if warning else ""
        ),
        "data_source": "공공데이터포털 지방행정 인허가 데이터 (2016~2024)",
    }
