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

from data.seoul_demo_data import get_candidates, get_similar_cases, get_map_center, get_all_gu_names
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

# ─── CSS ──────────────────────────────────────────────────────
st.markdown("""
<style>
/* ===== 0. 전역 폰트 — 크기는 텍스트 요소에만, div/span은 건드리지 않음 ===== */
* { font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif !important; box-sizing: border-box !important; }
/* 아이콘 폰트는 예외 (화살표 등이 글자로 깨지는 것 방지) */
[data-testid="stIconMaterial"], .material-symbols-rounded {
    font-family: 'Material Symbols Rounded' !important;
}
.material-symbols-outlined { font-family: 'Material Symbols Outlined' !important; }
html, body, .stApp { font-size: 17px; }
.stMarkdown p, .stMarkdown li, td, th, label { font-size: 17px; }
.stMarkdown div, .stMarkdown p { word-break: keep-all; overflow-wrap: break-word; text-align: left; }
.stApp { background-color: #F4F5F7; }

/* 컨테이너 중앙 정렬 */
.block-container { max-width: 1200px; margin: 0 auto; padding: 3rem 40px 2rem !important; }
header[data-testid="stHeader"] { display: none !important; }
.main > div:first-child { margin-top: 0 !important; }

/* ===== 섹션 카드 래퍼 — 래퍼 자체에 padding (DOM 구조 무관하게 적용) ===== */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF !important;
    border: none !important;
    border-radius: 16px !important;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06) !important;
    margin-bottom: 32px !important;
    padding: 40px 48px !important;
}

/* ===== 사이드바 ===== */
[data-testid="stSidebar"] { background-color: #F0F2F5 !important; }
[data-testid="stSidebar"] label { color: #333 !important; font-size: 15px !important; font-weight: 600; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span { color: #444 !important; font-size: 15px !important; }
[data-testid="stSidebar"] b { color: #1C1C1E !important; }
[data-testid="stSidebar"] .stSelectbox > div > div {
    background-color: #FFF !important; color: #1C1C1E !important; border: 1px solid #D1D5DB !important;
}
[data-testid="stSidebar"] input[type="number"] {
    background-color: #FFF !important; color: #1C1C1E !important; border: 1px solid #D1D5DB !important;
}
[data-testid="stSidebar"] .stMultiSelect input {
    background-color: transparent !important; border: none !important;
    box-shadow: none !important; min-width: 2px !important; width: auto !important;
}
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="select"] > div:first-child {
    background-color: #FFF !important; border: 1px solid #D1D5DB !important; min-height: 38px !important;
}
[data-testid="stSidebar"] hr { border-color: #D1D5DB !important; }
[data-testid="stSidebar"] .stCaption { color: #666 !important; font-size: 14px !important; }
[data-testid="stSidebar"] [data-baseweb="tag"] {
    background-color: #FFB800 !important; color: #1C1C1E !important; font-weight: 700 !important;
}

/* 버튼 */
.stButton > button {
    background-color: #FFB800 !important; color: #1C1C1E !important;
    font-weight: 800 !important; font-size: 17px !important;
    border: 2px solid #E6A500 !important; border-radius: 8px !important;
    height: 48px !important;
}
.stButton > button:hover { background-color: #E6A500 !important; }

/* ===== 타이포그래피 위계 ===== */
h1 { color: #1A1A1A !important; font-size: 28px !important; font-weight: 800 !important; }
/* 섹션 제목 — 배경 밴드로 확실히 구분 */
h2 {
    color: #1A1A1A !important; font-size: 26px !important; font-weight: 800 !important;
    background: #F7F8FA !important;
    border-left: 6px solid #FFBC00 !important;
    border-radius: 0 10px 10px 0 !important;
    padding: 16px 24px !important;
    margin: 0 0 28px 0 !important;
    display: block !important;
}
/* 소제목 22px / 800 */
h3 {
    color: #1A1A1A !important; font-size: 22px !important; font-weight: 800 !important;
    margin-bottom: 20px !important; margin-top: 16px !important;
}
h5 {
    color: #1A1A1A !important; font-size: 22px !important; font-weight: 800 !important;
    margin-bottom: 20px !important;
}

/* 탭 */
.stTabs [data-baseweb="tab-list"] { gap: 32px !important; }
.stTabs [data-baseweb="tab"] {
    font-size: 18px !important; font-weight: 700 !important;
    color: #999 !important; padding: 12px 16px !important;
}
.stTabs [aria-selected="true"] {
    color: #1C1C1E !important; border-bottom: 3px solid #FFB800 !important;
}

/* ===== 지표 박스 (커스텀 HTML) ===== */
.metric-grid {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;
    margin-bottom: 24px;
}
.metric-box {
    background: #F7F8FA; border-radius: 12px; padding: 28px 16px;
    text-align: center;
}
.metric-box .metric-label {
    font-size: 16px !important; color: #777; margin-bottom: 8px;
}
.metric-box .metric-value {
    font-size: 34px !important; font-weight: 800; color: #1C1C1E; line-height: 1.2;
}
.metric-box .metric-delta {
    font-size: 15px !important; color: #888; margin-top: 6px;
}

/* st.metric 숨기기 방지용 — 혹시 남아있다면 */
[data-testid="metric-container"] {
    background-color: #F7F8FA; border: none; border-radius: 12px;
    padding: 28px 16px !important; box-shadow: none; text-align: center;
    display: flex !important; flex-direction: column !important;
    align-items: center !important; justify-content: center !important;
}
[data-testid="stMetricLabel"],
[data-testid="stMetricLabel"] > div,
[data-testid="stMetricLabel"] label {
    color: #777 !important; font-size: 16px !important;
    justify-content: center !important; width: 100% !important; text-align: center !important;
}
[data-testid="stMetricValue"],
[data-testid="stMetricValue"] > div {
    color: #1C1C1E !important; font-size: 34px !important; font-weight: 800 !important;
    justify-content: center !important; width: 100% !important; text-align: center !important;
}
[data-testid="stMetricDelta"],
[data-testid="stMetricDelta"] > div {
    font-size: 15px !important;
    justify-content: center !important; width: 100% !important; text-align: center !important;
}

/* 테이블 */
thead tr th { background-color: #1C1C1E !important; color: #FFF !important; font-size: 15px !important; }
tbody tr td { font-size: 15px !important; }
tbody tr:nth-child(even) { background-color: #F7F8FA; }

/* 알림 */
.stAlert { border-radius: 8px !important; font-size: 16px !important; }

/* ===== KB 상단 헤더 ===== */
.kb-top-bar {
    background: linear-gradient(135deg, #1C1C1E 0%, #2C2C2E 100%);
    color: #FFF; padding: 14px 22px; border-radius: 10px; margin-bottom: 24px;
    display: flex; align-items: center; gap: 14px;
}
.kb-logo { color: #FFB800; font-size: 22px !important; font-weight: 900; letter-spacing: 2px; }
.kb-sub  { color: #AAA; font-size: 15px !important; }
.kb-badge {
    background: #FFB800; color: #1C1C1E;
    padding: 3px 10px; border-radius: 20px;
    font-size: 14px !important; font-weight: 700; margin-left: auto;
}

/* ===== 신호등 ===== */
.signal-green  { background:#E8F8EF; color:#1A7A45; border:1px solid #34C759;
                 border-radius:8px; padding:12px 20px; font-weight:700; font-size:16px !important; display:inline-block; }
.signal-yellow { background:#FFF8E0; color:#7A5A00; border:1px solid #FFB800;
                 border-radius:8px; padding:12px 20px; font-weight:700; font-size:16px !important; display:inline-block; }
.signal-red    { background:#FFECEC; color:#8B1A1A; border:1px solid #FF3B30;
                 border-radius:8px; padding:12px 20px; font-weight:700; font-size:16px !important; display:inline-block; }

/* ===== 추천 근거 카드 — 방향별 배경색 (좋음=초록 / 나쁨=빨강 / 중립=파랑) ===== */
.evidence-good {
    border-left: 4px solid #34C759; background: #EDFAF1;
    padding: 20px 24px; border-radius: 0 8px 8px 0; margin-bottom: 16px; color: #1C1C1E;
}
.evidence-bad {
    border-left: 4px solid #FF3B30; background: #FFF0EF;
    padding: 20px 24px; border-radius: 0 8px 8px 0; margin-bottom: 16px; color: #1C1C1E;
}
.evidence-info {
    border-left: 4px solid #3B82F6; background: #EEF4FF;
    padding: 20px 24px; border-radius: 0 8px 8px 0; margin-bottom: 16px; color: #1C1C1E;
}
.evidence-good .ev-icon { color:#34C759; }
.evidence-bad  .ev-icon { color:#FF3B30; }
.evidence-info .ev-icon { color:#3B82F6; }

/* Streamlit 구분선(hr) 위 과도한 여백 제거 */
.stMarkdown hr { margin-top: 24px !important; margin-bottom: 24px !important; }

/* 캡션 */
.stCaption p { font-size: 15px !important; color: #777 !important; }
</style>
""", unsafe_allow_html=True)

# ─── 브라우저 자동번역 차단 (한글 깨짐 방지) ─────────────────
st.markdown("""
<meta name="google" content="notranslate">
<meta http-equiv="Content-Language" content="ko">
<script>document.documentElement.lang='ko'; document.documentElement.translate=false;</script>
""", unsafe_allow_html=True)

# ─── 상단 KB 헤더 ─────────────────────────────────────────────
st.markdown("""
<div class="kb-top-bar" translate="no">
  <div class="kb-logo">KB</div>
  <div>
    <div style="color:#FFFFFF; font-weight:700; font-size:18px;">소상공인 창업 입지 추천</div>
    <div class="kb-sub">AI 기반 3년 생존 가능성 분석 · 금융서비스 연결</div>
  </div>
  <div class="kb-badge">2026 KB AI Challenge</div>
</div>
""", unsafe_allow_html=True)

# ─── 세션 상태 초기화 ────────────────────────────────────────
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
      <div style="font-size:14px; color:#666; margin-top:8px; font-weight:600;">창업 입지 추천 서비스</div>
    </div>
    <hr style="border:none; border-top:1px solid #D1D5DB; margin:0 0 16px 0;">
    """, unsafe_allow_html=True)

    st.markdown("**업종 / 지역**")
    category = st.selectbox("업종 선택", ["카페", "음식점", "편의점", "의류", "기타"],
                             label_visibility="collapsed")
    region   = st.selectbox("지역 선택", get_all_gu_names(), index=get_all_gu_names().index("마포구"), label_visibility="collapsed")

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

# ─── 분석 실행 ───────────────────────────────────────────────
if run_btn:
    user_prefs = {
        "priority": priority,
        "max_rent": max_rent,
        "max_total": max_budget,
        "max_monthly_burden": max_burden,
    }

    with st.spinner("입지 분석 중..."):
        candidates   = get_candidates(region)
        surv_results = compute_all_candidates(candidates, category)
        surv_map     = {r["candidate_id"]: r for r in surv_results}

        all_results = []
        for cand in candidates:
            cid       = cand["id"]
            surv      = surv_map[cid]
            cases_raw = get_similar_cases(cid, region, category)
            cost_r    = compute_total_cost(cand)
            gap_r     = compute_funding_gap(cost_r, self_fund)
            products  = match_financial_products(gap_r["funding_gap"], max_burden)
            combined  = compute_combined_burden(products)
            signal_r  = compute_burden_signal(cand["est_monthly_revenue"],
                                               combined["total_monthly"], max_burden)
            evidence  = generate_evidence_cards(cand, surv, category)
            case_card = generate_similar_case_card(cases_raw, cand["name"], category)
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

    st.session_state.all_results      = all_results
    st.session_state.results_ready    = True
    st.session_state.analysis_region  = region
    st.session_state.analysis_params  = {
        "category": category, "region": region,
        "self_fund": self_fund, "max_budget": max_budget,
        "max_rent": max_rent, "max_burden": max_burden,
        "priority": priority,
    }
    st.toast("분석이 완료되었습니다!", icon="✅")

# ─── 결과 표시 ────────────────────────────────────────────────
if not st.session_state.results_ready:
    st.markdown("""
    <div style="background:#FFFFFF; border-radius:12px; padding:48px; text-align:center;
                border:1px solid #E5E5EA; box-shadow:0 1px 4px rgba(0,0,0,0.06); margin-top:20px;">
      <div style="font-size:48px; margin-bottom:16px;">🏪</div>
      <div style="font-size:22px; font-weight:700; color:#1C1C1E; margin-bottom:8px;">
        창업 입지 분석 서비스
      </div>
      <div style="color:#6B6B6B; font-size:16px; line-height:1.8;">
        왼쪽에서 <b>업종 · 지역 · 자금 조건</b>을 입력하고<br>
        <b>입지 분석 시작</b> 버튼을 누르면<br>
        AI가 후보 입지 3곳을 분석해 드립니다.
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

all_results = sorted(st.session_state.all_results, key=lambda r: r["surv"]["stability_rank"])
final_rec   = build_final_recommendation(all_results)

# ─── 분석 조건 요약 배너 ─────────────────────────────────────
ap = st.session_state.get("analysis_params", {})
if ap:
    prio_str = " · ".join(ap.get("priority", [])) if ap.get("priority") else "없음"
    st.markdown(f"""
    <div style="background:#1C1C1E; color:#FFF; border-radius:10px; padding:14px 24px;
                margin-bottom:24px; display:flex; flex-wrap:wrap; gap:12px 28px; align-items:center; font-size:15px;">
      <span style="color:#FFB800; font-weight:800; font-size:16px;">현재 분석 조건</span>
      <span>{ap.get('region','')} · {ap.get('category','')}</span>
      <span>자기자금 <b>{ap.get('self_fund',0)//10000:,}만원</b></span>
      <span>최대예산 <b>{ap.get('max_budget',0)//10000:,}만원</b></span>
      <span>월임대료 한도 <b>{ap.get('max_rent',0)//10000:,}만원</b></span>
      <span>월부담 한도 <b>{ap.get('max_burden',0)//10000:,}만원</b></span>
      <span>우선순위 <b>{prio_str}</b></span>
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# SECTION 1 — 후보 입지 요약 카드
# ════════════════════════════════════════════════════════════
with st.container(border=True):
    st.header("후보 입지 3곳 비교")

    cols = st.columns(3, gap="large")
    rank_labels = {1: "1위 (안정성)", 2: "2위", 3: "3위"}
    for i, r in enumerate(all_results):
        with cols[i]:
            surv_pct = r["surv"]["survival_3y"] * 100
            rank     = r["surv"]["stability_rank"]
            border   = "2px solid #FFB800" if rank == 1 else "1px solid #E5E5EA"
            sig      = r["signal_r"]["signal"]
            display_sig = sig if not r["warnings"] else ("yellow" if sig == "green" else sig)
            sig_color = {"green": "#34C759", "yellow": "#FFB800", "red": "#FF3B30"}.get(display_sig, "#888")
            sig_text  = {"green": "금융부담 안전", "yellow": "금융부담 주의", "red": "금융부담 위험"}.get(display_sig, "")
            st.markdown(f"""
            <div style="background:#FFF; border:{border}; border-radius:14px;
                        padding:32px; text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.07);
                        margin-bottom:40px;">
              <div style="font-size:16px; font-weight:700; color:#888; margin-bottom:8px;">{rank_labels.get(rank,'')}</div>
              <div style="font-size:22px; font-weight:800; color:#1C1C1E; margin-bottom:6px;">{r['candidate_name']}</div>
              <div style="font-size:16px; color:#555; margin-bottom:16px;">{r['cand']['dong']} | {r['cand']['floor_area']}㎡</div>
              <div style="font-size:52px; font-weight:900; color:#1C1C1E; line-height:1.1;">{surv_pct:.0f}%</div>
              <div style="font-size:16px; color:#888; margin:6px 0 14px;">3년 생존 가능성</div>
              <div style="font-size:16px; color:#555; margin-bottom:14px;">종합점수 <b style="color:#1C1C1E;">{r['composite_balanced']:.0f}점</b></div>
              <div>
                <span style="background:{sig_color}20; color:{sig_color}; border:1px solid {sig_color};
                             font-size:15px; font-weight:700; padding:6px 16px; border-radius:20px;">
                  {sig_text}
                </span>
              </div>
              {"<div style='margin-top:10px; font-size:15px; color:#FF6B00; font-weight:600;'>예산 조건 확인 필요</div>" if r['warnings'] else ""}
            </div>
            """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# SECTION 2 — 지도
# ════════════════════════════════════════════════════════════
with st.container(border=True):
    st.header("후보 입지 지도")
    try:
        import folium
        from streamlit_folium import st_folium
        map_lat, map_lng = get_map_center(st.session_state.get("analysis_region", "마포구"))
        m = folium.Map(location=[map_lat, map_lng], zoom_start=14, tiles="CartoDB positron")
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
with st.container(border=True):
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

            # ── 핵심 지표 4개 — 커스텀 HTML metric-box ──
            delta_html = f'<div class="metric-delta">자기자금 {sf//10000:,}만원</div>'
            st.markdown(f"""
            <div class="metric-grid">
              <div class="metric-box">
                <div class="metric-label">3년 생존 가능성</div>
                <div class="metric-value">{surv['survival_3y']*100:.0f}%</div>
              </div>
              <div class="metric-box">
                <div class="metric-label">예상 월매출</div>
                <div class="metric-value">{cand['est_monthly_revenue']//10000:,}만원</div>
              </div>
              <div class="metric-box">
                <div class="metric-label">총 필요자금</div>
                <div class="metric-value">{cost['total_cost']//10000:,}만원</div>
              </div>
              <div class="metric-box">
                <div class="metric-label">추가 조달 필요액</div>
                <div class="metric-value">{gap['funding_gap']//10000:,}만원</div>
                {delta_html}
              </div>
            </div>
            """, unsafe_allow_html=True)

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
                      <div style="font-size:18px; font-weight:700; margin-bottom:6px;"><span class="ev-icon">{icon}</span> {ev['item']}</div>
                      <div style="font-size:16px; line-height:1.7; color:#333;">{ev['sentence']}</div>
                      <div style="font-size:14px; color:#999; margin-top:6px;">출처: {ev['data_source']}</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

                # 유사 사례
                st.markdown("### 유사 사례 통계")
                cc = r["case_card"]
                rate_pct = cc["survival_rate_3y"] * 100
                st.markdown(f"""
                <div style="background:#F7F8FA; border-radius:12px; padding:24px; border:1px solid #E5E5EA;">
                  <div style="font-size:40px; font-weight:800; color:#1C1C1E; margin-bottom:4px;">{rate_pct:.0f}%</div>
                  <div style="font-size:16px; color:#777; margin-bottom:12px;">유사 조건 {r['category']}의 3년 생존율</div>
                  <div style="font-size:17px; color:#333; line-height:1.7;">{cc['summary_sentence']}</div>
                  <div style="font-size:14px; color:#999; margin-top:10px;">
                    필터: {cc['filter_criteria']}<br>출처: {cc['data_source']}
                  </div>
                </div>
                """, unsafe_allow_html=True)
                if cc["sample_warning"]:
                    st.warning(cc["sample_warning_msg"])

            with right:
                # 자금 계획
                st.markdown("### 자금 계획")
                cost_items = list(cost["breakdown"].items())
                cost_df = pd.DataFrame([
                    {"항목": k, "금액": f"{v//10000:,}만원", "비중": f"{v/cost['total_cost']*100:.0f}%"}
                    for k, v in cost_items
                ] + [{"항목": "합계", "금액": f"{cost['total_cost']//10000:,}만원", "비중": "100%"}])
                st.dataframe(cost_df, hide_index=True, use_container_width=True)

                st.markdown(f"""
                <div style="background:#FFF8E7; border:1px solid #FFB800; border-radius:8px;
                            padding:16px 20px; margin-top:8px; line-height:1.8; font-size:16px;">
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
                <div style="font-size:14px; color:#999; margin-top:8px;">{sig['threshold_info']}</div>
                """, unsafe_allow_html=True)
                if sig["user_limit_exceeded"]:
                    st.warning(sig["user_limit_msg"])

            # 스트레스 테스트
            st.markdown("---")
            st.markdown("### 스트레스 테스트")
            st.caption("조건이 나빠지는 상황을 가정해 생존 가능성 변화를 확인합니다.")
            sc_cols = st.columns(3, gap="medium")
            scenario_icons = {"금리+1%p": "금리 인상", "임대료+10%": "임대료 상승", "매출-30%": "매출 감소"}
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
                    <div style="background:#F7F8FA; border:1px solid #E5E5EA; border-radius:12px;
                                padding:24px 16px; text-align:center;">
                      <div style="font-size:15px; color:#888; margin-bottom:6px;">{scenario_icons.get(sc_name, sc_name)}</div>
                      <div style="font-size:18px; font-weight:700; color:#1C1C1E;">{sc_name}</div>
                      <div style="font-size:34px; font-weight:900; color:#1C1C1E; margin:10px 0;">{sc_r['survival_3y']*100:.0f}%</div>
                      <div style="font-size:15px; font-weight:600; color:{'#FF3B30' if change < 0 else '#34C759'};">{change_str}</div>
                      <div style="margin-top:10px;">
                        <span style="background:{sig_c}20; color:{sig_c}; border:1px solid {sig_c};
                                     font-size:15px; font-weight:700; padding:5px 14px; border-radius:20px;">
                          {sc_r['signal_label']}
                        </span>
                      </div>
                      <div style="font-size:15px; color:#666; margin-top:10px; line-height:1.5;">{sc_r['cashflow_warning']}</div>
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
with st.container(border=True):
    st.header("종합 비교 · 최종 추천")

    chart_col, rec_col = st.columns([1, 1], gap="large")

    with chart_col:
        st.markdown("##### 항목별 지표 비교")
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
            polar=dict(radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=12))),
            showlegend=True,
            legend=dict(orientation="h", x=0.5, y=-0.15, xanchor="center", font=dict(size=14)),
            height=400,
            margin=dict(t=30, b=80, l=30, r=30),
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
            ("balanced", "균형형 추천",  "#FFB800", "#1C1C1E", "안정성·수익성·금융부담 균형이 가장 우수합니다"),
            ("growth",   "성장형 추천",  "#1C1C1E", "#FFFFFF", "수익성과 유동인구 잠재력이 높은 입지"),
            ("stable",   "안정형 추천",  "#F0F0F0", "#1C1C1E", "생존 가능성과 자금 안정성이 높은 입지"),
        ]
        for key, label, bg, fg, desc in rec_types:
            rec = final_rec[key]
            name = rec["candidate"]
            st.markdown(f"""
            <div style="background:{bg}; color:{fg}; border-radius:10px; padding:22px 24px; margin-bottom:16px;">
              <div style="font-size:15px; opacity:0.7; margin-bottom:4px;">{label}</div>
              <div style="font-size:22px; font-weight:800; margin-bottom:6px;">{name}</div>
              <div style="font-size:16px; opacity:0.85; line-height:1.6;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:#F7F8FA; border-radius:8px; padding:16px 20px; margin-bottom:24px;
                    font-size:14px; color:#888; line-height:1.8; width:100%;">
          <b style="color:#555;">유의사항</b><br>
          본 서비스는 과거 데이터 기반의 통계적 참고 정보입니다.<br>
          개별 사업자의 성공을 보장하지 않으며, 금융상품 가입 확정 안내가 아닙니다.<br>
          실제 대출 승인은 금융기관 별도 심사에 따릅니다.
        </div>
        <div style="height:8px;"></div>
        """, unsafe_allow_html=True)
