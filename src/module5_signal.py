"""
[모듈5] 예상 금융부담 신호등
예상 월매출 대비 월 금융부담 비율 → 초록/노랑/빨강
"""
from __future__ import annotations
from config.settings import SIGNAL_GREEN_MAX, SIGNAL_YELLOW_MAX, SIGNAL_LABELS


def compute_burden_signal(monthly_revenue: int, monthly_burden: int,
                           user_limit: int | None = None) -> dict:
    """
    신호등 등급 계산

    Parameters
    ----------
    monthly_revenue : int   예상 월매출 (원)
    monthly_burden  : int   예상 월 금융부담 (원)
    user_limit      : int   사용자 희망 월 부담 한도 (원, 선택)

    Returns
    -------
    dict:
        burden_ratio        : float  부담 비율 (0~1)
        signal              : str    "green" | "yellow" | "red"
        signal_label        : str    화면 표시 레이블
        signal_message      : str    안내 문구
        user_limit_exceeded : bool
        threshold_info      : str    임계치 공개 문구
    """
    if monthly_revenue <= 0:
        ratio = 1.0
    else:
        ratio = monthly_burden / monthly_revenue

    if ratio <= SIGNAL_GREEN_MAX:
        signal = "green"
    elif ratio <= SIGNAL_YELLOW_MAX:
        signal = "yellow"
    else:
        signal = "red"

    label, message = SIGNAL_LABELS[signal]
    user_exceeded = user_limit is not None and monthly_burden > user_limit

    return {
        "burden_ratio":         round(ratio, 4),
        "burden_ratio_pct":     round(ratio * 100, 1),
        "monthly_burden":       monthly_burden,
        "monthly_revenue":      monthly_revenue,
        "signal":               signal,
        "signal_label":         label,
        "signal_message":       message,
        "user_limit_exceeded":  user_exceeded,
        "user_limit_msg": (
            f"⚠ 희망 월 부담 한도({user_limit:,}원)를 초과합니다." if user_exceeded else ""
        ),
        "threshold_info": (
            f"신호등 기준: 초록 ≤{SIGNAL_GREEN_MAX*100:.0f}% / "
            f"노랑 ≤{SIGNAL_YELLOW_MAX*100:.0f}% / 빨강 >{SIGNAL_YELLOW_MAX*100:.0f}%"
        ),
    }
