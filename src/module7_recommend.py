"""
[모듈7] 지표 정규화 및 최종 추천
- 각 지표를 0~100으로 정규화
- 가중합 기반 종합 추천점수 계산
- 균형형/성장형/안정형 목적별 추천
- 조건 경고 부여
"""
from __future__ import annotations
from config.settings import WEIGHTS_BY_TYPE


def normalize_score(value: float, v_min: float, v_max: float) -> float:
    """선형 정규화 → 0~100"""
    if v_max == v_min:
        return 50.0
    return max(0.0, min(100.0, (value - v_min) / (v_max - v_min) * 100))


def compute_individual_scores(candidate: dict,
                               survival_result: dict,
                               cost_result: dict,
                               gap_result: dict,
                               signal_result: dict,
                               all_candidates_survival: list[dict],
                               user_prefs: dict) -> dict:
    """
    개별 지표 점수화 (0~100)

    user_prefs 예시:
        {
            "priority": ["임대료", "유동인구", "경쟁"],
            "max_rent": 2500000,
            "max_total": 100000000,
            "max_monthly_burden": 700000,
        }
    """
    all_survivals = [r["survival_3y"] for r in all_candidates_survival]
    s_min, s_max = min(all_survivals), max(all_survivals)

    # ─ 안정성 점수: 생존확률 정규화
    stability_score = normalize_score(survival_result["survival_3y"], s_min, s_max)

    # ─ 수익성 점수: 예상 영업이익 정규화
    profit = candidate.get("est_monthly_profit", 0)
    # 마포구 카페 범위 기준값 (시연용)
    profitability_score = normalize_score(profit, 4_000_000, 6_000_000)

    # ─ 금융 실행 가능성 점수
    self_ratio     = gap_result.get("self_ratio", 0.5)
    signal         = signal_result.get("signal", "red")
    signal_pts     = {"green": 100, "yellow": 60, "red": 20}.get(signal, 50)
    limit_ok       = not signal_result.get("user_limit_exceeded", False)
    financial_score = (
        normalize_score(self_ratio, 0.3, 1.0) * 0.4
        + signal_pts * 0.4
        + (100 if limit_ok else 0) * 0.2
    )

    # ─ 선호 적합성 점수
    preference_score = _preference_score(candidate, user_prefs)

    return {
        "stability_score":     round(stability_score, 1),
        "profitability_score": round(profitability_score, 1),
        "financial_score":     round(financial_score, 1),
        "preference_score":    round(preference_score, 1),
    }


def compute_composite_score(individual_scores: dict,
                              weights_type: str = "balanced") -> float:
    """가중합 종합 추천점수"""
    w = WEIGHTS_BY_TYPE.get(weights_type, WEIGHTS_BY_TYPE["balanced"])
    score = (
        w["stability"]      * individual_scores["stability_score"]
        + w["profitability"] * individual_scores["profitability_score"]
        + w["financial"]     * individual_scores["financial_score"]
        + w["preference"]    * individual_scores["preference_score"]
    )
    return round(score, 1)


def check_condition_warnings(candidate: dict, gap_result: dict,
                               user_prefs: dict) -> list[str]:
    """실행 조건 경고 생성"""
    warnings = []
    max_rent  = user_prefs.get("max_rent")
    max_total = user_prefs.get("max_total")

    if max_rent and candidate.get("rent_monthly", 0) > max_rent:
        warnings.append(
            f"⚠ 입력 최대 임대료({max_rent:,}원) 초과 "
            f"— 현재 {candidate.get('rent_monthly',0):,}원"
        )
    if max_total and gap_result.get("total_cost", 0) > max_total:
        warnings.append(
            f"⚠ 총 필요자금({gap_result['total_cost']:,}원)이 최대 예산({max_total:,}원) 초과 "
            "— 추가 조달 또는 예산 조정 필요"
        )
    if gap_result.get("funding_gap", 0) > 0:
        warnings.append(
            f"추가 자금 조달이 필요함: {gap_result['funding_gap']:,}원"
        )
    return warnings


def build_final_recommendation(all_results: list[dict]) -> dict:
    """
    전체 후보 중 균형형/성장형/안정형 추천 생성

    all_results: 각 후보별 compute_composite_score 결과 포함 dict 목록
    """
    # 균형형: 종합점수(balanced) 1위
    balanced = max(all_results, key=lambda r: r.get("composite_balanced", 0))
    # 성장형: 수익성 점수 1위
    growth   = max(all_results, key=lambda r: r.get("scores", {}).get("profitability_score", 0))
    # 안정형: 안정성 점수 1위
    stable   = max(all_results, key=lambda r: r.get("scores", {}).get("stability_score", 0))

    return {
        "balanced": {
            "candidate": balanced["candidate_name"],
            "reason": "안정성·수익성·금융부담 균형이 가장 우수합니다",
            "composite_score": balanced.get("composite_balanced"),
        },
        "growth": {
            "candidate": growth["candidate_name"],
            "reason": "수익성과 유동인구 잠재력이 높은 입지",
            "profitability_score": growth.get("scores", {}).get("profitability_score"),
        },
        "stable": {
            "candidate": stable["candidate_name"],
            "reason": "생존 가능성과 자금 안정성이 높은 입지",
            "stability_score": stable.get("scores", {}).get("stability_score"),
        },
    }


def _preference_score(candidate: dict, user_prefs: dict) -> float:
    """사용자 우선순위 기반 선호 적합성 점수 (0~100)"""
    priority = user_prefs.get("priority", [])
    score = 50.0  # 기본

    def _has(keyword):
        return any(keyword in p for p in priority)

    if _has("임대료"):
        max_rent = user_prefs.get("max_rent", float("inf"))
        rent = candidate.get("rent_monthly", 0)
        score += 20 if rent <= max_rent else -10

    if _has("유동인구"):
        ratio = candidate.get("floating_pop_ratio", 1.0)
        score += 20 * min(1.0, (ratio - 1.0))

    if _has("경쟁"):
        comp = candidate.get("competitor_count_300m", 15)
        score += 20 if comp <= 10 else (10 if comp <= 15 else -5)

    return max(0.0, min(100.0, score))
