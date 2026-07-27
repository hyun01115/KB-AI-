"""
실시간 공공 API 연동 모듈
DEMO_MODE=true 일 때는 사전 수집 데이터(mapo_demo_data.py) 사용
DEMO_MODE=false 일 때는 실제 API 호출
"""
from __future__ import annotations
import os
import math
import requests
from typing import Optional

DEMO_MODE = os.environ.get("DEMO_MODE", "true").lower() == "true"
SMFG_API_KEY = os.environ.get("SMFG_API_KEY", "")
SEOUL_DATA_API_KEY = os.environ.get("SEOUL_DATA_API_KEY", "")
PUBLIC_DATA_API_KEY = os.environ.get("PUBLIC_DATA_API_KEY", "")

SMFG_BASE = "https://apis.data.go.kr/B553077/api/open/sdsc2"
SEOUL_BASE = "http://openapi.seoul.go.kr:8088"


# ─── 소상공인시장진흥공단: 주변 경쟁 점포 수 ──────────────────
def fetch_competitor_count(lat: float, lng: float, category: str,
                            radius_m: int = 300) -> dict:
    """반경 300m 내 동일 업종 경쟁 점포 수 조회"""
    if DEMO_MODE:
        from data.mapo_demo_data import get_candidates
        demo = {c["id"]: c for c in get_candidates()}
        # lat/lng 기준으로 가장 가까운 후보 반환
        best = min(demo.values(),
                   key=lambda c: _haversine(lat, lng, c["lat"], c["lng"]))
        return {
            "count": best["competitor_count_300m"],
            "source": "소상공인시장진흥공단 (시연용 사전 수집, 2026.06)",
        }

    if not SMFG_API_KEY:
        raise RuntimeError("SMFG_API_KEY 미설정")

    url = f"{SMFG_BASE}/storeListInRadius"
    params = {
        "serviceKey": SMFG_API_KEY,
        "pageNo": 1,
        "numOfRows": 500,
        "type": "json",
        "cx": lng,
        "cy": lat,
        "radius": radius_m,
        "indsMclsNm": category,
        "inqSttsCd": "01",
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("body", {}).get("items", [])
    count = len(items) if isinstance(items, list) else 0
    return {
        "count": count,
        "source": f"소상공인시장진흥공단 (실시간, {_today()})",
    }


# ─── 서울 열린데이터광장: 유동인구 ───────────────────────────
def fetch_floating_population(dong_name: str) -> dict:
    """행정동 기준 일 평균 생활인구 조회"""
    if DEMO_MODE:
        from data.mapo_demo_data import get_candidates
        c = next((x for x in get_candidates() if x["dong"] == dong_name), None)
        if c:
            return {
                "daily_avg": c["floating_pop_daily"],
                "gu_avg": c["floating_pop_gu_avg"],
                "ratio": c["floating_pop_ratio"],
                "source": "서울시 생활인구 (시연용 사전 수집, 2026.06)",
            }
        return {"daily_avg": 21600, "gu_avg": 21600, "ratio": 1.0,
                "source": "서울시 생활인구 (기본값)"}

    if not SEOUL_DATA_API_KEY:
        raise RuntimeError("SEOUL_DATA_API_KEY 미설정")

    date = "20260601"
    url = f"{SEOUL_BASE}/{SEOUL_DATA_API_KEY}/json/Seoul_Resi_Pop/1/100/{date}"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    rows = data.get("Seoul_Resi_Pop", {}).get("row", [])
    dong_rows = [r for r in rows if dong_name in r.get("ADSTRD_NM", "")]

    if not dong_rows:
        return {"daily_avg": 21600, "gu_avg": 21600, "ratio": 1.0,
                "source": "서울시 생활인구 (데이터 없음)"}

    # 시간대별 인구 합산 → 일 평균 추정
    import pandas as pd
    df = pd.DataFrame(dong_rows)
    hour_cols = [c for c in df.columns if c.startswith("TO")]
    daily = float(df[hour_cols].astype(float).sum(axis=1).mean()) if hour_cols else 21600
    gu_avg = 21600.0
    return {
        "daily_avg": round(daily),
        "gu_avg": int(gu_avg),
        "ratio": round(daily / gu_avg, 2),
        "source": f"서울시 생활인구 (실시간, {_today()})",
    }


# ─── 공공데이터포털: 개업·폐업 이력 (생존 통계용) ─────────────
def fetch_survival_cases(gu_name: str, category: str,
                          budget_min: int, budget_max: int) -> dict:
    """유사 조건 점포의 생존 통계 조회"""
    if DEMO_MODE:
        from data.mapo_demo_data import get_similar_cases
        # 시연용: 마포구 카페 기본값 반환
        return get_similar_cases("A")

    if not PUBLIC_DATA_API_KEY:
        raise RuntimeError("PUBLIC_DATA_API_KEY 미설정")

    # 지방행정 인허가 데이터 API
    url = "https://apis.data.go.kr/1741000/StoreListService1/getStoreList1"
    params = {
        "serviceKey": PUBLIC_DATA_API_KEY,
        "pageNo": 1,
        "numOfRows": 1000,
        "type": "json",
        "signguNm": gu_name,
        "indsMclsNm": category,
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    # 생존 통계 집계 (간략화)
    data = resp.json()
    items = data.get("body", {}).get("items", [])
    total = len(items)
    survived = sum(1 for i in items if i.get("inqSttsCd") == "01")
    return {
        "total_similar": total,
        "survived_3y": survived,
        "survival_rate_3y": round(survived / total, 3) if total > 0 else 0.6,
        "filter_criteria": f"{gu_name} / {category}",
        "sample_warning": total < 30,
    }


# ─── 유틸리티 ─────────────────────────────────────────────────
def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def _today() -> str:
    from datetime import date
    return date.today().strftime("%Y.%m")
