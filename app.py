"""
KB AI 해커톤 — 소상공인 창업 입지 추천 서비스
Streamlit 프론트엔드

실행: streamlit run app.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
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

# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="KB 소상공인 창업 입지 추천",
    page_icon="🏪",
    layout="wide",
)

# ─── 사이드바: 사용자 조건 입력 ──────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/KB_Financial_Group_logo.svg/200px-KB_Financial_Group_logo.svg.png",
             width=120)
    st.title("창업 조건 입력")

    category = st.selectbox("업종", ["카페", "음식점", "편의점", "의류", "기타"])
    region   = st.selectbox("지역", ["마포구"])  # 시연: 마포구 고정
    self_fund = st.number_input("자기자금 (만원)", min_value=1000, max_value=50000,
                                 value=5000, step=500) * 10_000
    max_budget = st.number_input("최대 총 예산 (만원)", min_value=1000, max_value=100000,
                                  value=10000, step=500) * 10_000
    max_rent   = st.number_input("최대 월 임대료 (만원)", min_value=50, max_value=1000,
                                  value=250, step=10) * 10_000
    max_burden = st.number_input("희망 월 금융부담 한도 (만원)", min_value=10, max_value=500,
                                  value=100, step=10) * 10_000

    priority_options = ["임대료", "유동인구", "경쟁", "면적", "수익성"]
    priority = st.multiselect("우선순위 (중요한 순서대로)", priority_options,
                               default=["임대료", "유동인구", "경쟁"])

    run_btn = st.button("🔍 입지 분석 시작", type="primary", use_container_width=True)

st.title("🏪 소상공인 창업 입지 추천")
st.caption(f"업종: **{category}** | 지역: **{region}** | 자기자금: **{self_fund/10000:,.0f}만원**")

if not run_btn:
    st.info("왼쪽 사이드바에서 창업 조건을 입력하고 **입지 분석 시작**을 누르세요.")
    st.stop()

user_prefs = {
    "priority": priority,
    "max_rent": max_rent,
    "max_total": max_budget,
    "max_monthly_burden": max_burden,
}

# ─── 데이터 로드 및 모듈 실행 ────────────────────────────────
candidates   = get_candidates()
surv_results = compute_all_candidates(candidates, category)
surv_map     = {r["candidate_id"]: r for r in surv_results}

all_results = []
for cand in candidates:
    cid         = cand["id"]
    surv        = surv_map[cid]
    cases_raw   = get_similar_cases(cid)

    cost_r      = compute_total_cost(cand)
    gap_r       = compute_funding_gap(cost_r, self_fund)
    products    = match_financial_products(gap_r["funding_gap"], max_burden)
    combined    = compute_combined_burden(products)
    signal_r    = compute_burden_signal(
                      cand["est_monthly_revenue"],
                      combined["total_monthly"],
                      max_burden,
                  )
    evidence    = generate_evidence_cards(cand, surv, category)
    case_card   = generate_similar_case_card(cases_raw, cand["name"])
    warnings    = check_condition_warnings(cand, gap_r, user_prefs)

    scores      = compute_individual_scores(
                      cand, surv, cost_r, gap_r, signal_r,
                      surv_results, user_prefs
                  )
    comp_bal    = compute_composite_score(scores, "balanced")
    comp_grow   = compute_composite_score(scores, "growth")
    comp_stab   = compute_composite_score(scores, "stable")

    stress      = run_stress_test(cand, surv, cost_r, signal_r, category)

    all_results.append({
        "candidate_id":   cid,
        "candidate_name": cand["name"],
        "cand":           cand,
        "surv":           surv,
        "cost_r":         cost_r,
        "gap_r":          gap_r,
        "products":       products,
        "combined":       combined,
        "signal_r":       signal_r,
        "evidence":       evidence,
        "case_card":      case_card,
        "warnings":       warnings,
        "scores":         scores,
        "composite_balanced": comp_bal,
        "composite_growth":   comp_grow,
        "composite_stable":   comp_stab,
        "stress":         stress,
    })

final_rec = build_final_recommendation(all_results)

# ════════════════════════════════════════════════════════════
# 섹션 1: 후보 지도 + 생존확률 요약
# ════════════════════════════════════════════════════════════
st.header("📍 후보 입지 3곳")

try:
    import folium
    from streamlit_folium import st_folium
    m = folium.Map(location=[37.555, 126.92], zoom_start=14)
    colors = {"A": "blue", "B": "red", "C": "green"}
    for r in all_results:
        c = r["cand"]
        surv_pct = r["surv"]["survival_3y"] * 100
        folium.Marker(
            [c["lat"], c["lng"]],
            popup=folium.Popup(
                f"<b>{c['name']}</b><br>3년 생존확률: {surv_pct:.1f}%<br>"
                f"월 임대료: {c['rent_monthly']:,}원",
                max_width=200,
            ),
            tooltip=f"{c['name']} ({surv_pct:.1f}%)",
            icon=folium.Icon(color=colors.get(c["id"], "gray")),
        ).add_to(m)
    st_folium(m, width=700, height=400)
except Exception:
    st.info("지도는 streamlit-folium 설치 후 표시됩니다.")

# ─── 후보 카드 요약 ───────────────────────────────────────────
cols = st.columns(3)
for i, r in enumerate(all_results):
    with cols[i]:
        surv_pct = r["surv"]["survival_3y"] * 100
        sig = r["signal_r"]
        st.metric(r["candidate_name"],
                  f"생존확률 {surv_pct:.1f}%",
                  f"종합점수 {r['composite_balanced']:.0f}점")
        st.write(sig["signal_label"])
        if r["warnings"]:
            st.warning(r["warnings"][0])

# ════════════════════════════════════════════════════════════
# 섹션 2: 후보 상세 탭
# ════════════════════════════════════════════════════════════
st.header("📊 후보별 상세 분석")
tabs = st.tabs([r["candidate_name"] for r in all_results])

for tab, r in zip(tabs, all_results):
    with tab:
        cand = r["cand"]
        surv = r["surv"]
        cost = r["cost_r"]
        gap  = r["gap_r"]
        sig  = r["signal_r"]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("3년 생존확률",    f"{surv['survival_3y']*100:.1f}%")
        col2.metric("예상 월매출",     f"{cand['est_monthly_revenue']//10000:,}만원")
        col3.metric("총 필요자금",     f"{cost['total_cost']//10000:,}만원")
        col4.metric("추가 조달 필요",  f"{gap['funding_gap']//10000:,}만원")

        # ── 근거 카드
        st.subheader("📋 추천 근거")
        for ev in r["evidence"]:
            icon = "✅" if ev["direction"] == "good" else ("⚠️" if ev["direction"] == "bad" else "ℹ️")
            st.markdown(
                f"{icon} **{ev['item']}** — {ev['sentence']}  \n"
                f"<small>출처: {ev['data_source']} ({ev['data_date']})</small>",
                unsafe_allow_html=True,
            )

        # ── 유사 사례
        st.subheader("📁 유사 사례")
        cc = r["case_card"]
        st.info(cc["summary_sentence"])
        if cc["sample_warning"]:
            st.warning(cc["sample_warning_msg"])
        st.caption(f"출처: {cc['data_source']} | 필터: {cc['filter_criteria']}")

        # ── 비용 구성
        st.subheader("💰 비용 및 금융")
        cost_df = pd.DataFrame([
            {"항목": k, "금액 (원)": f"{v:,}"}
            for k, v in cost["breakdown"].items()
        ] + [{"항목": "합계", "금액 (원)": f"{cost['total_cost']:,}"}])
        st.table(cost_df)

        st.write(f"**자기자금**: {self_fund//10000:,}만원 → "
                 f"**추가 조달**: {gap['funding_gap']//10000:,}만원")

        # ── 금융상품
        if r["products"]:
            st.subheader("🏦 추천 금융상품")
            for p in r["products"]:
                with st.expander(f"{p['name']} — 월 {p['monthly_burden']//10000:,}만원"):
                    st.write(f"- 제공: {p['provider']}")
                    st.write(f"- 금리: {p['rate_min']*100:.2f}~{p['rate_max']*100:.2f}%")
                    st.write(f"- 한도: {p['max_amount']//10000:,}만원")
                    st.write(f"- 기간: {p['tenor_years']}년")
                    st.write(f"- {p['note']}")

        # ── 신호등
        st.subheader("🚦 금융부담 신호등")
        sig_label = sig["signal_label"]
        st.markdown(f"### {sig_label}")
        st.write(sig["signal_message"])
        st.write(f"예상 월매출 대비 금융부담 비율: **{sig['burden_ratio_pct']:.1f}%**")
        st.caption(sig["threshold_info"])

        # ── 스트레스 테스트
        st.subheader("🔬 스트레스 테스트")
        stress_rows = []
        for sc_name, sc_r in r["stress"].items():
            stress_rows.append({
                "시나리오":     sc_name,
                "3년 생존확률":  f"{sc_r['survival_3y']*100:.1f}%"
                                 f" ({sc_r['survival_change']*100:+.1f}%p)",
                "월 금융부담비율": f"{sc_r['burden_ratio_pct']:.1f}%",
                "신호등":        sc_r["signal_label"],
                "현금흐름":      sc_r["cashflow_warning"],
            })
        st.table(pd.DataFrame(stress_rows))

        # ── 조건 경고
        if r["warnings"]:
            st.subheader("⚠️ 실행 조건 경고")
            for w in r["warnings"]:
                st.warning(w)

# ════════════════════════════════════════════════════════════
# 섹션 3: 지표 비교 + 최종 추천
# ════════════════════════════════════════════════════════════
st.header("🏆 최종 추천")

# 레이더 차트
categories_radar = ["안정성", "수익성", "금융 실행 가능성", "선호 적합성"]
fig = go.Figure()
for r in all_results:
    s = r["scores"]
    vals = [s["stability_score"], s["profitability_score"],
            s["financial_score"], s["preference_score"]]
    vals.append(vals[0])
    fig.add_trace(go.Scatterpolar(
        r=vals,
        theta=categories_radar + [categories_radar[0]],
        name=r["candidate_name"],
        fill="toself",
    ))
fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100])),
                  title="후보별 지표 비교 레이더 차트")
st.plotly_chart(fig, use_container_width=True)

# 개별 지표 표
score_rows = []
for r in all_results:
    s = r["scores"]
    score_rows.append({
        "후보":         r["candidate_name"],
        "3년 생존확률": f"{r['surv']['survival_3y']*100:.1f}%",
        "안정성":       f"{s['stability_score']:.0f}점",
        "수익성":       f"{s['profitability_score']:.0f}점",
        "금융가능성":   f"{s['financial_score']:.0f}점",
        "선호 적합성":  f"{s['preference_score']:.0f}점",
        "종합점수":     f"{r['composite_balanced']:.0f}점",
    })
st.table(pd.DataFrame(score_rows))

# 목적별 추천
st.subheader("목적별 추천")
c1, c2, c3 = st.columns(3)
with c1:
    rec = final_rec["balanced"]
    st.success(f"**균형형 추천**\n\n{rec['candidate']}  \n{rec['reason']}  \n종합점수: {rec['composite_score']:.0f}점")
with c2:
    rec = final_rec["growth"]
    st.info(f"**성장형 추천**\n\n{rec['candidate']}  \n{rec['reason']}  \n수익성: {rec['profitability_score']:.0f}점")
with c3:
    rec = final_rec["stable"]
    st.warning(f"**안정형 추천**\n\n{rec['candidate']}  \n{rec['reason']}  \n안정성: {rec['stability_score']:.0f}점")

# 면책 고지
st.divider()
st.caption(
    "⚠ 본 서비스는 동일/유사 조건의 과거 데이터를 기반으로 한 통계적 참고 정보입니다. "
    "개별 사업자의 성공 여부를 예측하거나 보장하지 않으며, "
    "금융상품 가입 확정 안내가 아닙니다. "
    "실제 대출 승인은 금융기관의 별도 심사에 따릅니다.  \n"
    "데이터 출처: 소상공인시장진흥공단 / 서울시 생활인구 / 공공데이터포털 지방행정인허가 / KB금융그룹 공시 금리"
)
