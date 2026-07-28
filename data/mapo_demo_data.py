"""
마포구 카페 창업 시연용 사전 수집 데이터 (하위 호환 래퍼)
실제 데이터는 seoul_demo_data.py에 통합되어 있습니다.
"""
from data.seoul_demo_data import (
    get_candidates,
    get_candidate_by_id,
    get_similar_cases,
    get_map_center,
    get_all_gu_names,
)

__all__ = [
    "get_candidates",
    "get_candidate_by_id",
    "get_similar_cases",
    "get_map_center",
    "get_all_gu_names",
]
