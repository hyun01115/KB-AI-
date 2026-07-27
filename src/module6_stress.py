"""
[모듈6] 스트레스 테스트
금리+1%p / 임대료+10% / 매출-30% 시나리오별 재계산
"""
from __future__ import annotations
from config.settings import STRESS_SCENARIOS, COX_BETA
from src.survival_model import compute_survival_probability
from src.module5_signal import compute_burden_signal
import math


def run_stress_test(candidate: dict,
                     survival_result: dict,
                     cost_result: dict,
                     burden_result: dict,
                     category: str = "카페") -> dict:
    """
    3가지 시나리오 일괄 실행

    Returns
    -------
    dict: 시나리오명 → 각 결과
    """
    output = {}
    for scenario_name, delta in STRESS_SCENARIOS.items():
        output[scenario_name] = _apply_scenario(
            candidate, survival_result, cost_result, burden_result,
            delta, category, scenario_name
        )
    return output


def _apply_scenario(candidate: dict, survival_result: dict,
                     cost_result: dict, burden_result: dict,
                     delta: dict, category: str, name: str) -> dict:
    rate_d   = delta["rate_delta"]
    rent_d   = delta["rent_delta"]
    rev_d    = delta["revenue_delta"]

    # 변경된 후보 데이터 복사 (target_survival_3y 제거 → Cox 수식으로 재계산)
    c = {k: v for k, v in candidate.items() if k != "target_survival_3y"}

    # 임대료 상승 → rent_growth_3y + 비용 반영
    if rent_d != 0:
        c["rent_growth_3y"] = c.get("rent_growth_3y", 10.0) + rent_d * 100
        c["rent_monthly"]   = int(c.get("rent_monthly", 1500000) * (1 + rent_d))

    # 재생존확률 계산 (Cox 수식 직접 사용)
    new_surv = compute_survival_probability(c, category)
    # 베이스라인에서 상대 변화만 반영 (시연 일관성 유지)
    base_surv = survival_result.get("survival_3y", 0.65)
    base_cox  = compute_survival_probability(candidate, category)
    # 스트레스 전후 Cox 비율로 실제 생존확률 조정
    import math
    cox_before = max(0.001, base_cox.get("hazard_ratio", 1.0))
    cox_after  = max(0.001, new_surv.get("hazard_ratio", 1.0))
    ratio = cox_after / cox_before
    adjusted_surv = min(0.95, max(0.10, base_surv / ratio))
    new_surv["survival_3y"] = round(adjusted_surv, 3)

    # 매출 변화 반영
    base_revenue = candidate.get("est_monthly_revenue", 20000000)
    new_revenue  = int(base_revenue * (1 + rev_d))

    # 금리 변화 → 월 부담 재계산
    base_burden = burden_result.get("monthly_burden", 0)
    # 단순 추정: 대출 잔액 × 금리 인상분 / 12
    loan_est    = cost_result.get("total_cost", 0) - candidate.get("deposit", 0)
    extra_int   = int(max(0, loan_est) * rate_d / 12)
    new_burden  = base_burden + extra_int

    # 신호등 재계산
    new_signal = compute_burden_signal(new_revenue, new_burden)

    # 운영자금 고갈 예상 시점 (매출-비용 음수가 되는 달)
    monthly_fixed = (
        candidate.get("rent_monthly", 1500000)
        + new_burden
        + int(candidate.get("est_monthly_revenue", 20000000) * 0.30)  # 인건비 추정
    )
    monthly_cm = new_revenue - monthly_fixed  # 공헌이익
    working = cost_result.get("working_capital", 0)
    if monthly_cm < 0 and working > 0:
        months_to_zero = math.ceil(working / abs(monthly_cm))
        cashflow_warning = f"현재 시나리오에서 {months_to_zero}개월 후 운영자금 소진 예상"
    else:
        months_to_zero = None
        cashflow_warning = "운영자금 소진 위험 없음"

    return {
        "scenario":              name,
        "survival_3y":           new_surv["survival_3y"],
        "survival_change":       round(new_surv["survival_3y"] - survival_result["survival_3y"], 3),
        "monthly_revenue":       new_revenue,
        "monthly_burden":        new_burden,
        "burden_ratio_pct":      new_signal["burden_ratio_pct"],
        "signal":                new_signal["signal"],
        "signal_label":          new_signal["signal_label"],
        "months_to_zero":        months_to_zero,
        "cashflow_warning":      cashflow_warning,
        "delta_applied":         delta,
    }
