"""유사 사례 검색 엔진 - 396건 실데이터에서 조건 기반 검색"""
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import SimilarCase

# 기본 데이터셋 경로
DEFAULT_DATASET_PATH = Path(__file__).parent.parent.parent.parent / "data" / "extracted" / "dataset.json"


class CaseRetriever:
    """유사 사례 검색"""

    def __init__(self, dataset_path: Optional[str] = None):
        path = Path(dataset_path) if dataset_path else DEFAULT_DATASET_PATH
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.cases: List[dict] = data.get("cases", [])
        # Add case_number as index since dataset doesn't have it
        for idx, case in enumerate(self.cases):
            if "basic_info" not in case:
                case["basic_info"] = {}
            case["basic_info"]["case_number"] = idx

    def find_similar(
        self,
        business_type: str,
        kitchen_area_py: float,
        shape_type: Optional[str] = None,
        top_k: int = 5,
    ) -> List[SimilarCase]:
        """유사 사례 검색

        유사도 함수:
        - 업종 일치: 0.5 (완전일치) / 0.1 (불일치)
        - 면적 유사도: 0.3 * gaussian(area_diff)
        - 형태 일치: 0.2 (일치) / 0.0 (불일치)

        Args:
            business_type: 업종
            kitchen_area_py: 주방 면적 (평)
            shape_type: 주방 형태 (optional)
            top_k: 반환할 사례 수

        Returns:
            유사도 내림차순 사례 리스트
        """
        scored_cases = []

        for case in self.cases:
            score = self._calculate_similarity(
                case, business_type, kitchen_area_py, shape_type
            )
            if score > 0:
                scored_cases.append((case, score))

        # 유사도 내림차순 정렬
        scored_cases.sort(key=lambda x: x[1], reverse=True)

        results = []
        for case, score in scored_cases[:top_k]:
            basic = case.get("basic_info", {})
            equipment_list = case.get("equipment_list", [])
            zones = case.get("zones", [])

            results.append(SimilarCase(
                case_number=basic.get("case_number", 0),
                business_type=basic.get("business_type_category", "unknown"),
                kitchen_area_py=basic.get("kitchen_area_py"),
                equipment_count=len(equipment_list),
                similarity_score=round(score, 3),
                equipment_names=[
                    eq.get("name", "") for eq in equipment_list if eq.get("name")
                ],
                zone_names=[
                    z.get("zone_name", "") for z in zones if z.get("zone_name")
                ],
            ))

        return results

    def _calculate_similarity(
        self,
        case: dict,
        target_biz: str,
        target_area: float,
        target_shape: Optional[str],
    ) -> float:
        """유사도 계산"""
        basic = case.get("basic_info", {})
        dims = case.get("kitchen_dimensions") or {}

        score = 0.0

        # 1. 업종 유사도 (가중치 0.5)
        case_biz = basic.get("business_type_category", "")
        if case_biz == target_biz:
            score += 0.5
        else:
            score += 0.1  # 다른 업종이라도 최소 점수

        # 2. 면적 유사도 (가중치 0.3, 가우시안)
        case_area = basic.get("kitchen_area_py")
        if case_area and case_area > 0:
            # 면적 차이 비율 기반 가우시안 (σ=0.3 → 30% 차이에서 급감)
            area_ratio = abs(case_area - target_area) / max(target_area, 1)
            area_sim = math.exp(-(area_ratio ** 2) / (2 * 0.3 ** 2))
            score += 0.3 * area_sim

        # 3. 형태 유사도 (가중치 0.2)
        if target_shape:
            case_shape = dims.get("shape_type", "")
            if case_shape and case_shape.lower() == target_shape.lower():
                score += 0.2
        else:
            score += 0.1  # 형태 미지정 시 기본점

        return score

    def get_equipment_union(
        self, cases: List[SimilarCase]
    ) -> Dict[str, Tuple[str, float]]:
        """유사 사례들의 장비 합집합 (가중 빈도)

        Returns:
            {장비명: (카테고리, 가중평균_신뢰도)}
        """
        # 원본 데이터에서 장비 정보 추출 필요
        equipment_scores: Dict[str, List[Tuple[str, float]]] = {}

        for similar in cases:
            weight = similar.similarity_score
            # similar_case에는 equipment_names만 있으므로
            # 원본 케이스에서 카테고리도 가져와야 함
            original = self._find_case(similar.case_number)
            if not original:
                continue

            for eq in original.get("equipment_list", []):
                name = eq.get("name") or ""
                cat = eq.get("category") or "other"
                if name:
                    if name not in equipment_scores:
                        equipment_scores[name] = []
                    equipment_scores[name].append((cat, weight))

        # 가중 평균
        result = {}
        for name, entries in equipment_scores.items():
            # 가장 빈번한 카테고리
            cat = max(set(c for c, _ in entries), key=lambda c: sum(1 for cc, _ in entries if cc == c))
            avg_score = sum(w for _, w in entries) / len(cases) if cases else 0
            result[name] = (cat, round(avg_score, 3))

        return result

    def _find_case(self, case_number: int) -> Optional[dict]:
        """케이스 번호로 원본 데이터 찾기"""
        for case in self.cases:
            if case.get("basic_info", {}).get("case_number") == case_number:
                return case
        return None
