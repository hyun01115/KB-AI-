"""
서울 열린데이터광장 - 서울시 생활인구(내국인) 데이터 수집
https://data.seoul.go.kr/dataList/OA-14991/S/1/datasetView.do

사용법:
  SEOUL_DATA_API_KEY=xxx python collect_population.py --dong 망원동
"""
import os
import sys
import argparse
import requests
import pandas as pd
from pathlib import Path


SEOUL_API_BASE = "http://openapi.seoul.go.kr:8088"


def fetch_living_population(service_key: str, dong_name: str,
                              date: str = "20260601") -> list[dict]:
    """
    서울시 생활인구(내국인) 조회
    date: YYYYMMDD 형식 (시간대별 데이터)
    """
    url = f"{SEOUL_API_BASE}/{service_key}/json/Seoul_Resi_Pop/{1}/{100}/{date}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    rows = data.get("Seoul_Resi_Pop", {}).get("row", [])
    if dong_name:
        rows = [r for r in rows if dong_name in r.get("ADSTRD_NM", "")]
    return rows


def calc_hourly_avg(rows: list[dict]) -> dict:
    """시간대별 평균 생활인구 계산"""
    hour_cols = [c for c in (rows[0].keys() if rows else []) if c.startswith("TO")]
    if not hour_cols:
        return {}
    df = pd.DataFrame(rows)
    return {col: df[col].astype(float).mean() for col in hour_cols}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dong", default="망원동")
    parser.add_argument("--date", default="20260601")
    parser.add_argument("--output", default="population.csv")
    args = parser.parse_args()

    key = os.environ.get("SEOUL_DATA_API_KEY")
    if not key:
        print("[ERROR] SEOUL_DATA_API_KEY 환경변수를 설정하세요.")
        sys.exit(1)

    print(f"[서울 생활인구] {args.dong} {args.date} 데이터 수집 중...")
    rows = fetch_living_population(key, args.dong, args.date)
    print(f"  데이터 행: {len(rows)}개")

    df = pd.DataFrame(rows)
    out_path = Path(__file__).parent.parent / args.output
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"[저장 완료] {out_path}")


if __name__ == "__main__":
    main()
