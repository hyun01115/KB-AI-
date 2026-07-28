"""
KB AI 해커톤 — 소상공인 창업 입지 추천 서비스
실행: streamlit run app.py
"""
import sys, os
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
from src.module4_cost import (compute_total_cost, compute_funding_gap,
                               match_financial_products, compute_combined_burden)
from src.module5_signal import compute_burden_signal
from src.module6_stress import run_stress_test
from src.module7_recommend import (compute_individual_scores, compute_composite_score,
                                    check_condition_warnings, build_final_recommendation)

# ─── 페이지 설정 ──────────────────────────────────────────────
st.set_page_config(
    page_title="KB 창업 입지 추천",
    page_icon="K",
    layout="wide",
)

# ─── CSS: KB 브랜드 (노랑은 포인트만, 텍스트는 항상 진한 색) ──
st.markdown("""
<style>
/* 전체 */
.stApp { background-color: #F7F8FA; font-family: 'Apple SD Gothic Neo', sans-serif; }
.block-container { padding-top: 1.5rem !important; max-width: 1200px; }

/* 사이드바 — 밝은 회색 배경 */
[data-testid="stSidebar"] { background-color: #F0F2F5 !important; }
[data-testid="stSidebar"] label { color: #333333 !important; font-size: 13px; font-weight: 600; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span { color: #444444 !important; }
[data-testid="stSidebar"] b { color: #1C1C1E !important; }
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] .stSelectbox > div > div {
    background-color: #FFFFFF !important;
    color: #1C1C1E !important;
    border: 1px solid #D1D5DB !important;
}
/* 사이드바 구분선 */
[data-testid="stSidebar"] hr { border-color: #D1D5DB !important; }
/* 사이드바 캡션 */
[data-testid="stSidebar"] .stCaption { color: #666666 !important; }

/* 입지 분석 시작 버튼 — KB노랑 배경 + 검정 글씨 */
.stButton > button {
    background-color: #FFB800 !important;
    color: #1C1C1E !important;
    font-weight: 800 !important;
    font-size: 15px !important;
    border: 2px solid #E6A500 !important;
    border-radius: 8px !important;
    height: 48px !important;
    letter-spacing: 0.5px;
}
.stButton > button:hover {
    background-color: #E6A500 !important;
    color: #1C1C1E !important;
}
/* multiselect 태그 — KB노랑+검정 */
[data-testid="stSidebar"] [data-baseweb="tag"] {
    background-color: #FFB800 !important;
    color: #1C1C1E !important;
    font-weight: 700 !important;
}

/* 메인 제목 */
h1 { color: #1C1C1E !important; font-size: 26px !important; font-weight: 800 !important; }
h2 { color: #1C1C1E !important; font-size: 20px !important; font-weight: 700 !important;
     border-left: 4px solid #FFB800; padding-left: 10px; margin-top: 2rem !important; }
h3 { color: #1C1C1E !important; font-size: 16px !important; font-weight: 600 !important; }

/* 탭 */
.stTabs [data-baseweb="tab"] { font-size: 15px; font-weight: 600; color: #555 !important; }
.stTabs [aria-selected="true"] {
    color: #1C1C1E !important;
    border-bottom: 3px solid #FFB800 !important;
}

/* 지표 카드 (metric) */
[data-testid="metric-container"] {
    background-color: #FFFFFF;
    border: 1px solid #E5E5EA;
    border-radius: 10px;
    padding: 16px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
[data-testid="stMetricLabel"] { color: #6B6B6B !important; font-size: 13px !important; }
[data-testid="stMetricValue"] { color: #1C1C1E !important; font-size: 22px !important; font-weight: 700 !important; }
[data-testid="stMetricDelta"] { font-size: 12px !important; }

/* 테이블 */
thead tr th {
    background-color: #1C1C1E !important;
    color: #FFFFFF !important;
    font-size: 13px !important;
}
tbody tr:nth-child(even) { background-color: #F7F8FA; }

/* 알림 박스 */
.stAlert { border-radius: 8px !important; }

/* KB 섹션 헤더 카드 */
.kb-section {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
    border: 1px solid #E5E5EA;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}
.kb-top-bar {
    background: linear-gradient(135deg, #1C1C1E 0%, #2C2C2E 100%);
    color: #FFFFFF;
    padding: 14px 22px;
    border-radius: 10px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 14px;
}
.kb-logo { color: #FFB800; font-size: 22px; font-weight: 900; letter-spacing: 2px; }
.kb-sub  { color: #AAAAAA; font-size: 13px; }
.kb-badge {
    background: #FFB800; color: #1C1C1E;
    padding: 3px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 700; margin-left: auto;
}
.signal-green  { background:#E8F8EF; color:#1A7A45; border:1px solid #34C759;
                 border-radius:8px; padding:10px 16px; font-weight:700; display:inline-block; }
.signal-yellow { background:#FFF8E0; color:#7A5A00; border:1px solid #FFB800;
                 border-radius:8px; padding:10px 16px; font-weight:700; display:inline-block; }
.signal-red    { background:#FFECEC; color:#8B1A1A; border:1px solid #FF3B30;
                 border-radius:8px; padding:10px 16px; font-weight:700; display:inline-block; }
.evidence-good { border-left: 3px solid #34C759; padding: 8px 12px;
                 background:#F0FFF4; border-radius:0 6px 6px 0; margin:6px 0; color:#1C1C1E; }
.evidence-bad  { border-left: 3px solid #FF3B30; padding: 8px 12px;
                 background:#FFF0F0; border-radius:0 6px 6px 0; margin:6px 0; color:#1C1C1E; }
.evidence-info { border-left: 3px solid #007AFF; padding: 8px 12px;
                 background:#F0F6FF; border-radius:0 6px 6px 0; margin:6px 0; color:#1C1C1E; }
</style>
""", unsafe_allow_html=True)

# ─── 상단 KB 헤더 ─────────────────────────────────────────────
st.markdown("""
<div class="kb-top-bar">
  <div class="kb-logo">KB</div>
  <div>
    <div style="color:#FFFFFF; font-weight:700; font-size:16px;">소상공인 창업 입지 추천</div>
    <div class="kb-sub">AI 기반 3년 생존 가능성 분석 · 금융서비스 연결</div>
  </div>
  <div class="kb-badge">AI 해커톤 2026</div>
</div>
""", unsafe_allow_html=True)

# ─── 세션 상태 초기화 (결과가 사라지지 않도록) ───────────────
if "results_ready" not in st.session_state:
    st.session_state.results_ready = False
if "all_results" not in st.session_state:
    st.session_state.all_results = []

# ─── 사이드바: 조건 입력 ──────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:12px 0 16px 0;">
      <div style="display:inline-block; background:#1C1C1E; color:#FFB800;
                  font-size:22px; font-weight:900; letter-spacing:3px;
                  padding:6px 18px; border-radius:8px;">KB</div>
      <div style="font-size:11px; color:#666; margin-top:8px; font-weight:600;">창업 입지 추천 서비스</div>
    </div>
    <hr style="border:none; border-top:1px solid #D1D5DB; margin:0 0 16px 0;">
    """, unsafe_allow_html=True)

    st.markdown("**업종 / 지역**")
    category = st.selectbox("업종 선택", ["카페", "음식점", "편의점", "의류", "기타"],
                             label_visibility="collapsed")
    region   = st.selectbox("지역 선택", ["마포구"], label_visibility="collapsed")

    st.markdown("---")
    st.markdown("**자금 조건**")
    self_fund  = st.number_input("보유 자기자금 (만원)",  min_value=1000, max_value=50000, value=5000, step=500) * 10_000
    max_budget = st.number_input("최대 총 예산 (만원)",  min_value=1000, max_value=100000, value=10000, step=500) * 10_000
    max_rent   = st.number_input("최대 월 임대료 (만원)", min_value=50,   max_value=1000,  value=250,   step=10)  * 10_000
    max_burden = st.number_input("월 금융부담 한도 (만원)",min_value=10,   max_value=500,   value=100,   step=10)  * 10_000

    st.markdown("---")
    OPTS = ["임대료", "유동인구", "경쟁 점포", "매장 면적", "수익성"]
    priority = st.multiselect(
        "중요하게 생각하는 조건을 선택하세요",
        options=OPTS,
        default=["임대료", "유동인구", "경쟁 점포"],
        key="priority_v3",
    )

    st.markdown("---")
    run_btn = st.button("입지 분석 시작", use_container_width=True)

# ─── 분석 실행 (버튼 클릭 시 session_state 저장) ─────────────
if run_btn:
    user_prefs = {
        "priority": priority,
        "max_rent": max_rent,
        "max_total": max_budget,
        "max_monthly_burden": max_burden,
    }

    with st.spinner("입지 분석 중..."):
        candidates   = get_candidates()
        surv_results = compute_all_candidates(candidates, category)
        surv_map     = {r["candidate_id"]: r for r in surv_results}

        all_results = []
        for cand in candidates:
            cid       = cand["id"]
            surv      = surv_map[cid]
            cases_raw = get_similar_cases(cid)
            cost_r    = compute_total_cost(cand)
            gap_r     = compute_funding_gap(cost_r, self_fund)
            products  = match_financial_products(gap_r["funding_gap"], max_burden)
            combined  = compute_combined_burden(products)
            signal_r  = compute_burden_signal(cand["est_monthly_revenue"],
                                               combined["total_monthly"], max_burden)
            evidence  = generate_evidence_cards(cand, surv, category)
            case_card = generate_similar_case_card(cases_raw, cand["name"])
            warnings  = check_condition_warnings(cand, gap_r, user_prefs)
            scores    = compute_individual_scores(cand, surv, cost_r, gap_r, signal_r,
                                                  surv_results, user_prefs)
            stress    = run_stress_test(cand, surv, cost_r, signal_r, category)
            all_results.append({
                "candidate_id":       cid,
                "candidate_name":     cand["name"],
                "cand": cand, "surv": surv,
                "cost_r": cost_r, "gap_r": gap_r,
                "products": products, "combined": combined,
                "signal_r": signal_r, "evidence": evidence,
                "case_card": case_card, "warnings": warnings,
                "scores": scores,
                "composite_balanced": compute_composite_score(scores, "balanced"),
                "composite_growth":   compute_composite_score(scores, "growth"),
                "composite_stable":   compute_composite_score(scores, "stable"),
                "stress": stress,
                "self_fund": self_fund,
                "category": category,
            })

    st.session_state.all_results   = all_results
    st.session_state.results_ready = True

# ─── 결과 표시 ────────────────────────────────────────────────
if not st.session_state.results_ready:
    st.markdown("""
    <div style="background:#FFFFFF; border-radius:12px; padding:40px; text-align:center;
                border:1px solid #E5E5EA; box-shadow:0 1px 4px rgba(0,0,0,0.06); margin-top:20px;">
      <div style="font-size:48px; margin-bottom:16px;">🏪</div>
      <div style="font-size:20px; font-weight:700; color:#1C1C1E; margin-bottom:8px;">
        창업 입지 분석 서비스
      </div>
      <div style="color:#6B6B6B; font-size:14px; line-height:1.8;">
        왼쪽에서 <b>업종 · 지역 · 자금 조건</b>을 입력하고<br>
        <b>입지 분석 시작</b> 버튼을 누르면<br>
        AI가 후보 입지 3곳을 분석해 드립니다.
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

all_results = sorted(st.session_state.all_results, key=lambda r: r["surv"]["stability_rank"])
final_rec   = build_final_recommendation(all_results)

# ════════════════════════════════════════════════════════════
# SECTION 1 — 후보 입지 요약 카드
# ════════════════════════════════════════════════════════════
st.header("후보 입지 3곳 비교")

cols = st.columns(3)
rank_labels = {1: "1위 (안정성)", 2: "2위", 3: "3위"}
for i, r in enumerate(all_results):
    with cols[i]:
        surv_pct = r["surv"]["survival_3y"] * 100
        rank     = r["surv"]["stability_rank"]
        border   = "2px solid #FFB800" if rank == 1 else "1px solid #E5E5EA"
        sig      = r["signal_r"]["signal"]
        # 예산 초과 경고가 있으면 신호등을 최소 yellow로 표시
        display_sig = sig if not r["warnings"] else ("yellow" if sig == "green" else sig)
        sig_color = {"green": "#34C759", "yellow": "#FFB800", "red": "#FF3B30"}.get(display_sig, "#888")
        sig_text  = {"green": "금융부담 안전", "yellow": "금융부담 주의", "red": "금융부담 위험"}.get(display_sig, "")
        st.markdown(f"""
        <div style="background:#FFF; border:{border}; border-radius:12px;
                    padding:20px; text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.07);">
          <div style="font-size:13px; color:#888; margin-bottom:4px;">{rank_labels.get(rank,'')}</div>
          <div style="font-size:18px; font-weight:800; color:#1C1C1E;">{r['candidate_name']}</div>
          <div style="font-size:13px; color:#555; margin:4px 0 12px;">{r['cand']['dong']} | {r['cand']['floor_area']}㎡</div>
          <div style="font-size:36px; font-weight:900; color:#1C1C1E;">{surv_pct:.0f}%</div>
          <div style="font-size:12px; color:#888; margin-bottom:12px;">3년 생존 가능성</div>
          <div style="font-size:13px; color:#555;">종합점수 <b>{r['composite_balanced']:.0f}점</b></div>
          <div style="margin-top:10px;">
            <span style="background:{sig_color}20; color:{sig_color}; border:1px solid {sig_color};
                         font-size:11px; font-weight:700; padding:3px 10px; border-radius:20px;">
              {sig_text}
            </span>
          </div>
          {"<div style='margin-top:8px; font-size:11px; color:#FF6B00;'>예산 조건 확인 필요</div>" if r['warnings'] else ""}
        </div>
        """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# SECTION 2 — 지도
# ════════════════════════════════════════════════════════════
st.header("입지 위치 지도")
try:
    import folium
    from streamlit_folium import st_folium
    m = folium.Map(location=[37.555, 126.92], zoom_start=14, tiles="CartoDB positron")
    colors = {"A": "orange", "B": "red", "C": "green"}
    for r in all_results:
        c = r["cand"]
        surv_pct = r["surv"]["survival_3y"] * 100
        folium.Marker(
            [c["lat"], c["lng"]],
            popup=folium.Popup(
                f"<b>{c['name']}</b><br>3년 생존 가능성: {surv_pct:.0f}%<br>"
                f"월 임대료: {c['rent_monthly']//10000:,}만원<br>"
                f"경쟁 점포: {c['competitor_count_300m']}개",
                max_width=200,
            ),
            tooltip=f"{c['name']} — {surv_pct:.0f}%",
            icon=folium.Icon(color=colors.get(c["id"], "gray"), icon="store", prefix="fa"),
        ).add_to(m)
    st_folium(m, width="100%", height=380, returned_objects=[])
except Exception:
    st.info("지도 표시를 위해 streamlit-folium 패키지가 필요합니다. (pip install streamlit-folium folium)")

# ════════════════════════════════════════════════════════════
# SECTION 3 — 후보별 상세 탭
# ════════════════════════════════════════════════════════════
st.header("후보별 상세 분석")
tabs = st.tabs([f"  {r['candidate_name']}  " for r in all_results])

for tab, r in zip(tabs, all_results):
    with tab:
        cand = r["cand"]
        surv = r["surv"]
        cost = r["cost_r"]
        gap  = r["gap_r"]
        sig  = r["signal_r"]
        sf   = r["self_fund"]

        # 핵심 지표 4개
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("3년 생존 가능성",  f"{surv['survival_3y']*100:.0f}%")
        c2.metric("예상 월매출",      f"{cand['est_monthly_revenue']//10000:,}만원")
        c3.metric("총 필요자금",      f"{cost['total_cost']//10000:,}만원")
        c4.metric("추가 조달 필요액", f"{gap['funding_gap']//10000:,}만원",
                  delta=f"자기자금 {sf//10000:,}만원",
                  delta_color="off")

        st.markdown("---")

        left, right = st.columns([1, 1], gap="large")

        with left:
            # 추천 근거
            st.markdown("### 추천 근거")
            for ev in r["evidence"]:
                css_class = {"good": "evidence-good",
                             "bad":  "evidence-bad",
                             "neutral": "evidence-info"}.get(ev["direction"], "evidence-info")
                icon = {"good": "▲", "bad": "▼", "neutral": "●"}.get(ev["direction"], "●")
                st.markdown(f"""
                <div class="{css_class}">
                  <b>{icon} {ev['item']}</b><br>
                  <span style="font-size:13px;">{ev['sentence']}</span><br>
                  <span style="font-size:11px; color:#888;">출처: {ev['data_source']}</span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # 유사 사례
            st.markdown("### 유사 사례 통계")
            cc = r["case_card"]
            rate_pct = cc["survival_rate_3y"] * 100
            st.markdown(f"""
            <div style="background:#F7F8FA; border-radius:10px; padding:16px; border:1px solid #E5E5EA;">
              <div style="font-size:28px; font-weight:900; color:#1C1C1E;">{rate_pct:.0f}%</div>
              <div style="font-size:13px; color:#555; margin-bottom:8px;">유사 조건 카페의 3년 생존율</div>
              <div style="font-size:13px; color:#333;">{cc['summary_sentence']}</div>
              <div style="font-size:11px; color:#888; margin-top:8px;">
                필터: {cc['filter_criteria']}<br>출처: {cc['data_source']}
              </div>
            </div>
            """, unsafe_allow_html=True)
            if cc["sample_warning"]:
                st.warning(cc["sample_warning_msg"])

        with right:
            # 비용 구성
            st.markdown("### 자금 계획")
            cost_items = list(cost["breakdown"].items())
            cost_df = pd.DataFrame([
                {"항목": k, "금액": f"{v//10000:,}만원", "비중": f"{v/cost['total_cost']*100:.0f}%"}
                for k, v in cost_items
            ] + [{"항목": "합계", "금액": f"{cost['total_cost']//10000:,}만원", "비중": "100%"}])
            st.dataframe(cost_df, hide_index=True, use_container_width=True)

            st.markdown(f"""
            <div style="background:#FFF8E7; border:1px solid #FFB800; border-radius:8px; padding:14px 18px; margin-top:8px; line-height:1.8;">
              <b style="color:#1C1C1E;">자기자금 {sf//10000:,}만원</b>으로<br>
              <b style="color:#1C1C1E;">{gap['funding_gap']//10000:,}만원</b> 추가 조달 필요
            </div>
            """, unsafe_allow_html=True)

            # 금융상품
            st.markdown("### 추천 금융상품")
            if r["products"]:
                for p in r["products"]:
                    with st.expander(f"{p['name']}  —  월 {p['monthly_burden']//10000:,}만원"):
                        st.markdown(f"""
                        - **제공**: {p['provider']}
                        - **금리**: {p['rate_min']*100:.2f} ~ {p['rate_max']*100:.2f}%
                        - **한도**: {p['max_amount']//10000:,}만원 / 기간 {p['tenor_years']}년
                        - {p['note']}
                        """)
            else:
                st.info("현재 조건에 맞는 금융상품을 찾지 못했습니다. 조달 금액이나 부담 한도를 조정해보세요.")

            # 신호등
            st.markdown("### 금융부담 신호등")
            sig_css = {"green": "signal-green", "yellow": "signal-yellow", "red": "signal-red"}.get(sig["signal"], "signal-info")
            st.markdown(f"""
            <div class="{sig_css}">
              {sig['signal_label']} &nbsp; | &nbsp; 예상 월매출 대비 {sig['burden_ratio_pct']:.1f}%
            </div>
            <div style="font-size:12px; color:#888; margin-top:6px;">{sig['threshold_info']}</div>
            """, unsafe_allow_html=True)
            if sig["user_limit_exceeded"]:
                st.warning(sig["user_limit_msg"])

        # 스트레스 테스트
        st.markdown("---")
        st.markdown("### 스트레스 테스트")
        st.caption("조건이 불리하게 바뀔 경우 어떻게 달라지는지 미리 확인합니다.")
        sc_cols = st.columns(3)
        scenario_icons = {"금리+1%p": "금리 인상", "임대료+10%": "임대료 상승", "매출-30%": "매출 하락"}
        for (sc_name, sc_r), col in zip(r["stress"].items(), sc_cols):
            with col:
                change = sc_r["survival_change"] * 100
                if change < 0:
                    change_str = f"기존보다 {abs(change):.1f}%p 하락"
                elif change > 0:
                    change_str = f"기존보다 {abs(change):.1f}%p 상승"
                else:
                    change_str = "변화 없음"
                sig_c = {"green": "#34C759", "yellow": "#FFB800", "red": "#FF3B30"}.get(sc_r["signal"], "#888")
                st.markdown(f"""
                <div style="background:#F7F8FA; border:1px solid #E5E5EA; border-radius:10px; padding:16px; text-align:center;">
                  <div style="font-size:12px; color:#888; margin-bottom:4px;">{scenario_icons.get(sc_name, sc_name)}</div>
                  <div style="font-size:15px; font-weight:700; color:#1C1C1E;">{sc_name}</div>
                  <div style="font-size:24px; font-weight:900; color:#1C1C1E; margin:8px 0;">{sc_r['survival_3y']*100:.0f}%</div>
                  <div style="font-size:12px; color:{'#FF3B30' if change < 0 else '#34C759'};">{change_str}</div>
                  <div style="margin-top:8px;">
                    <span style="background:{sig_c}20; color:{sig_c}; border:1px solid {sig_c};
                                 font-size:11px; font-weight:700; padding:2px 8px; border-radius:20px;">
                      {sc_r['signal_label']}
                    </span>
                  </div>
                  <div style="font-size:11px; color:#888; margin-top:8px;">{sc_r['cashflow_warning']}</div>
                </div>
                """, unsafe_allow_html=True)

        # 조건 경고
        if r["warnings"]:
            st.markdown("---")
            for w in r["warnings"]:
                st.warning(w)

# ════════════════════════════════════════════════════════════
# SECTION 4 — 지표 비교 + 최종 추천
# ════════════════════════════════════════════════════════════
st.header("최종 추천")

chart_col, rec_col = st.columns([1, 1], gap="large")

with chart_col:
    st.markdown("##### 후보별 지표 레이더")
    radar_cats = ["안정성", "수익성", "금융\n실행가능성", "선호\n적합성"]
    colors_radar = ["#FFB800", "#1C1C1E", "#34C759"]
    fig = go.Figure()
    for r, color in zip(all_results, colors_radar):
        s = r["scores"]
        vals = [s["stability_score"], s["profitability_score"],
                s["financial_score"],  s["preference_score"]]
        vals.append(vals[0])
        fig.add_trace(go.Scatterpolar(
            r=vals,
            theta=radar_cats + [radar_cats[0]],
            name=r["candidate_name"],
            fill="toself",
            line_color=color,
            fillcolor=color,
            opacity=0.3,
        ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=10))),
        showlegend=True,
        legend=dict(orientation="h", x=0.5, y=-0.15, xanchor="center", font=dict(size=12)),
        height=380,
        margin=dict(t=20, b=60, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

    # 점수 표
    score_df = pd.DataFrame([{
        "후보":       r["candidate_name"],
        "생존확률":   f"{r['surv']['survival_3y']*100:.0f}%",
        "안정성":     f"{r['scores']['stability_score']:.0f}",
        "수익성":     f"{r['scores']['profitability_score']:.0f}",
        "금융가능성": f"{r['scores']['financial_score']:.0f}",
        "선호적합":   f"{r['scores']['preference_score']:.0f}",
        "종합":       f"{r['composite_balanced']:.0f}",
    } for r in all_results])
    st.dataframe(score_df, hide_index=True, use_container_width=True)

with rec_col:
    st.markdown("##### 목적별 최종 추천")
    rec_types = [
        ("balanced", "균형형 추천",  "#FFB800", "#1C1C1E", "안정성·수익성·금융부담이 고르게 우수"),
        ("growth",   "성장형 추천",  "#1C1C1E", "#FFFFFF", "수익성과 유동인구 잠재력이 높은 입지"),
        ("stable",   "안정형 추천",  "#F0F0F0", "#1C1C1E", "생존 가능성과 자금 안정성이 높은 입지"),
    ]
    for key, label, bg, fg, desc in rec_types:
        rec = final_rec[key]
        name = rec["candidate"]
        st.markdown(f"""
        <div style="background:{bg}; color:{fg}; border-radius:10px; padding:18px 20px; margin-bottom:12px;">
          <div style="font-size:12px; opacity:0.7; margin-bottom:4px;">{label}</div>
          <div style="font-size:20px; font-weight:800; margin-bottom:4px;">{name}</div>
          <div style="font-size:13px; opacity:0.85;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#F7F8FA; border-radius:8px; padding:14px 16px; font-size:12px; color:#888; line-height:1.8;">
      <b style="color:#555;">유의사항</b><br>
      본 서비스는 과거 데이터 기반의 통계적 참고 정보입니다.<br>
      개별 사업자의 성공을 보장하지 않으며, 금융상품 가입 확정 안내가 아닙니다.<br>
      실제 대출 승인은 금융기관 별도 심사에 따릅니다.
    </div>
    """, unsafe_allow_html=True)
