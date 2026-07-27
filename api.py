"""
KB AI 해커톤 — FastAPI 백엔드
Streamlit 대신 REST API 로 사용하려면 이 파일을 실행

실행: uvicorn api:app --reload
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from data.mapo_demo_data import get_candidates, get_similar_cases
from src.survival_model import compute_all_candidates
from src.module2_evidence import generate_evidence_cards
from src.module3_cases import generate_similar_case_card
from src.module4_cost import compute_total_cost, compute_funding_gap, match_financial_products, compute_combined_burden
from src.module5_signal import compute_burden_signal
from src.module6_stress import run_stress_test
from src.module7_recommend import (
    compute_individual_scores, compute_composite_score,
    check_condition_warnings, build_final_recommendation
)

app = FastAPI(title="KB 소상공인 창업 입지 추천 API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class UserInput(BaseModel):
    category:        str   = "카페"
    region:          str   = "마포구"
    self_funding:    int   = 50_000_000   # 자기자금 (원)
    max_budget:      int   = 100_000_000  # 최대 예산 (원)
    max_rent:        int   = 2_500_000    # 최대 월 임대료 (원)
    max_burden:      int   = 1_000_000    # 희망 월 금융부담 한도 (원)
    priority:        list[str] = ["임대료", "유동인구", "경쟁"]


@app.get("/")
def root():
    return {"service": "KB 소상공인 창업 입지 추천", "version": "1.0.0"}


@app.get("/candidates")
def list_candidates():
    """후보 입지 목록"""
    return get_candidates()


@app.post("/analyze")
def analyze(user: UserInput):
    """
    사용자 조건 → 후보 3개 전체 분석 결과 반환
    """
    candidates   = get_candidates()
    surv_results = compute_all_candidates(candidates, user.category)
    surv_map     = {r["candidate_id"]: r for r in surv_results}

    user_prefs = {
        "priority":           user.priority,
        "max_rent":           user.max_rent,
        "max_total":          user.max_budget,
        "max_monthly_burden": user.max_burden,
    }

    all_results = []
    for cand in candidates:
        cid       = cand["id"]
        surv      = surv_map[cid]
        cases_raw = get_similar_cases(cid)

        cost_r    = compute_total_cost(cand)
        gap_r     = compute_funding_gap(cost_r, user.self_funding)
        products  = match_financial_products(gap_r["funding_gap"], user.max_burden)
        combined  = compute_combined_burden(products)
        signal_r  = compute_burden_signal(
                        cand["est_monthly_revenue"],
                        combined["total_monthly"],
                        user.max_burden,
                    )
        evidence  = generate_evidence_cards(cand, surv, user.category)
        case_card = generate_similar_case_card(cases_raw, cand["name"])
        warnings  = check_condition_warnings(cand, gap_r, user_prefs)
        scores    = compute_individual_scores(
                        cand, surv, cost_r, gap_r, signal_r,
                        surv_results, user_prefs
                    )
        stress    = run_stress_test(cand, surv, cost_r, signal_r, user.category)

        all_results.append({
            "candidate_id":        cid,
            "candidate_name":      cand["name"],
            "location":            {"lat": cand["lat"], "lng": cand["lng"], "address": cand["address"]},
            "survival_3y":         surv["survival_3y"],
            "stability_rank":      surv["stability_rank"],
            "model_version":       surv["model_version"],
            "data_date":           surv["data_date"],
            "cost":                cost_r,
            "funding_gap":         gap_r,
            "financial_products":  products,
            "combined_burden":     combined,
            "signal":              signal_r,
            "evidence_cards":      evidence,
            "similar_case":        case_card,
            "warnings":            warnings,
            "scores":              scores,
            "composite_balanced":  compute_composite_score(scores, "balanced"),
            "composite_growth":    compute_composite_score(scores, "growth"),
            "composite_stable":    compute_composite_score(scores, "stable"),
            "stress_test":         stress,
        })

    return {
        "user_input":         user.model_dump(),
        "candidates":         all_results,
        "final_recommendation": build_final_recommendation(all_results),
    }


@app.post("/stress/{candidate_id}")
def stress_test(candidate_id: str, user: UserInput):
    """단일 후보 스트레스 테스트"""
    candidates = get_candidates()
    cand = next((c for c in candidates if c["id"] == candidate_id), None)
    if not cand:
        raise HTTPException(status_code=404, detail="후보를 찾을 수 없습니다.")

    surv_results = compute_all_candidates(candidates, user.category)
    surv = next(r for r in surv_results if r["candidate_id"] == candidate_id)

    cost_r   = compute_total_cost(cand)
    products = match_financial_products(max(0, cost_r["total_cost"] - user.self_funding))
    combined = compute_combined_burden(products)
    signal_r = compute_burden_signal(cand["est_monthly_revenue"], combined["total_monthly"])

    return run_stress_test(cand, surv, cost_r, signal_r, user.category)
