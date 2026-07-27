"""
[모듈4] 비용 계산 및 금융 매칭
후보 입지별 총 필요자금 → 추가 조달 필요금액 → 금융상품 매칭
"""
from __future__ import annotations
import json
import math
from pathlib import Path

_FP_PATH = Path(__file__).parent.parent / "config" / "financial_products.json"


def _load_products() -> list[dict]:
    with open(_FP_PATH, encoding="utf-8") as f:
        return json.load(f)


def compute_total_cost(candidate: dict,
                        interior_cost: int | None = None,
                        equipment_cost: int | None = None,
                        working_capital: int | None = None) -> dict:
    """
    총 필요자금 산정
    = 보증금 + 권리금 + 인테리어 + 집기/설비 + 초기운영자금

    입력값 없으면 면적 기반 추정치 사용
    """
    deposit  = candidate.get("deposit", 0)
    premium  = candidate.get("premium", 0)
    area     = candidate.get("floor_area", 30)
    rent     = candidate.get("rent_monthly", 1500000)

    # 인테리어: 없으면 면적×100만원 추정
    interior = interior_cost if interior_cost is not None else area * 1_000_000
    # 집기/설비: 인테리어의 30% 추정
    equipment = equipment_cost if equipment_cost is not None else int(interior * 0.3)
    # 운영자금: 임대료 3개월분
    working = working_capital if working_capital is not None else rent * 3

    total = deposit + premium + interior + equipment + working

    return {
        "deposit":          deposit,
        "premium":          premium,
        "interior":         interior,
        "equipment":        equipment,
        "working_capital":  working,
        "total_cost":       total,
        "breakdown": {
            "보증금":      deposit,
            "권리금":      premium,
            "인테리어/시설": interior,
            "집기/설비":   equipment,
            "초기운영자금": working,
        },
    }


def compute_funding_gap(cost_result: dict, self_funding: int) -> dict:
    """추가 조달 필요금액 계산"""
    total = cost_result["total_cost"]
    gap   = max(0, total - self_funding)
    ratio = round(self_funding / total, 3) if total > 0 else 1.0
    return {
        "total_cost":    total,
        "self_funding":  self_funding,
        "funding_gap":   gap,
        "self_ratio":    ratio,
        "needs_funding": gap > 0,
    }


def match_financial_products(funding_gap: int,
                               monthly_burden_limit: int | None = None,
                               purpose_hint: str = "창업") -> list[dict]:
    """
    금융상품 매칭
    - funding_gap 이상 한도를 가진 상품
    - purpose_hint 와 용도가 일치하는 상품
    - 예상 월 부담(원리금 균등) 계산
    """
    products = _load_products()
    matched = []

    for p in products:
        # 한도 확인
        if p["max_amount"] < funding_gap * 0.5:
            continue
        # 용도 확인
        if not any(purpose_hint in pu for pu in p.get("purpose", [])):
            continue

        # 실제 대출 금액: funding_gap 또는 한도 중 작은 값
        loan_amount = min(funding_gap, p["max_amount"])
        rate = (p["rate_min"] + p["rate_max"]) / 2  # 중간 금리
        tenor_months = p["tenor_years"] * 12
        grace_months = p.get("grace_period_months", 0)
        repay_months = tenor_months - grace_months

        # 원리금 균등 상환 월 부담
        monthly = _pmt(rate / 12, repay_months, loan_amount)

        if monthly_burden_limit and monthly > monthly_burden_limit:
            continue

        matched.append({
            **p,
            "loan_amount":    loan_amount,
            "monthly_burden": round(monthly),
            "assumed_rate":   rate,
            "repay_months":   repay_months,
        })

    # 예상 월 부담 오름차순 정렬 (부담이 낮은 순)
    matched.sort(key=lambda x: x["monthly_burden"])
    return matched[:4]  # 최대 4개


def compute_combined_burden(matched_products: list[dict]) -> dict:
    """추천 금융조합의 총 월 부담 계산"""
    if not matched_products:
        return {"total_monthly": 0, "products": []}
    # 1순위 + 2순위 조합 (보완 관계)
    selected = matched_products[:2]
    total = sum(p["monthly_burden"] for p in selected)
    return {
        "total_monthly": total,
        "products": [{"name": p["name"], "monthly": p["monthly_burden"]} for p in selected],
    }


def _pmt(rate_monthly: float, nper: int, pv: float) -> float:
    """원리금 균등 상환 월 납입액"""
    if rate_monthly == 0:
        return pv / nper if nper > 0 else 0
    return pv * rate_monthly / (1 - (1 + rate_monthly) ** (-nper))
