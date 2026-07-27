"""
소상공인시장진흥공단 상가(상권)정보 API 데이터 수집 스크립트
https://www.data.go.kr/data/15083033/openapi.do

사용법:
  SMFG_API_KEY=xxx python collect_stores.py --gu 마포구 --category 카페
"""
import os
import sys
import argparse
import requests
import pandas as pd
from pathlib import Path

BASE_URL = "https://apis.data.go.kr/B553077/api/open/sdsc2"

def fetch_stores_by_gu(service_key: str, gu_name: str, category: str = None,
                        page_no: int = 1, num_rows: int = 1000) -> list[dict]:
    """행정구 + 업종으로 상가 목록 조회"""
    url = f"{BASE_URL}/storeListInDong"
    params = {
        "serviceKey": service_key,
        "pageNo": page_no,
        "numOfRows": num_rows,
        "type": "json",
        "inqSttsCd": "01",  # 영업 중
    }
    if gu_name:
        params["signguNm"] = gu_name
    if category:
        params["indsMclsNm"] = category

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("body", {}).get("items", [])
    return items if isinstance(items, list) else [items]


def fetch_closed_stores(service_key: str, gu_name: str, category: str = None) -> list[dict]:
    """폐업 점포 목록 조회 (생존분석용)"""
    url = f"{BASE_URL}/storeListInDong"
    params = {
        "serviceKey": service_key,
        "pageNo": 1,
        "numOfRows": 1000,
        "type": "json",
        "inqSttsCd": "02",  # 폐업
    }
    if gu_name:
        params["signguNm"] = gu_name
    if category:
        params["indsMclsNm"] = category

    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("body", {}).get("items", [])
    return items if isinstance(items, list) else [items]


def calculate_competitor_count(stores: list[dict], lat: float, lng: float,
                                radius_m: int = 300, category: str = None) -> int:
    """반경 radius_m 내 경쟁 점포 수 계산 (Haversine)"""
    import math
    count = 0
    for s in stores:
        try:
            s_lat = float(s.get("lat", 0))
            s_lng = float(s.get("lng", 0))
        except (TypeError, ValueError):
            continue

        # Haversine 거리 계산
        R = 6371000  # 지구 반지름 (m)
        phi1, phi2 = math.radians(lat), math.radians(s_lat)
        dphi = math.radians(s_lat - lat)
        dlambda = math.radians(s_lng - lng)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        dist = 2 * R * math.asin(math.sqrt(a))

        if dist <= radius_m:
            count += 1
    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gu", default="마포구")
    parser.add_argument("--category", default="카페")
    parser.add_argument("--output", default="mapo_stores.csv")
    args = parser.parse_args()

    key = os.environ.get("SMFG_API_KEY")
    if not key:
        print("[ERROR] SMFG_API_KEY 환경변수를 설정하세요.")
        sys.exit(1)

    print(f"[소상공인시장진흥공단] {args.gu} {args.category} 데이터 수집 중...")
    active = fetch_stores_by_gu(key, args.gu, args.category)
    closed = fetch_closed_stores(key, args.gu, args.category)
    print(f"  영업 중: {len(active)}개 / 폐업: {len(closed)}개")

    all_stores = active + closed
    df = pd.DataFrame(all_stores)
    out_path = Path(__file__).parent.parent / args.output
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[저장 완료] {out_path}")


if __name__ == "__main__":
    main()
