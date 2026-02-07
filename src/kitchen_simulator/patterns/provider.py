"""패턴 기반 데이터 제공자 - patterns.json을 엔진에 연결하는 브릿지"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .models import PatternDatabase

# 장비 카테고리 → 4구역 가중치 매핑
# 냉장 장비는 저장구역과 조리구역에 분산 배치되므로 가중치로 분할
CATEGORY_TO_ZONE_WEIGHTS = {
    "cooking":       {"cooking": 1.0},
    "prep":          {"preparation": 1.0},
    "preparation":   {"preparation": 1.0},
    "refrigeration": {"storage": 0.5, "cooking": 0.3, "preparation": 0.2},
    "storage":       {"storage": 0.7, "preparation": 0.3},
    "dishwashing":   {"washing": 1.0},
    "washing":       {"washing": 1.0},
    "serving":       {"cooking": 0.6, "preparation": 0.4},
    "ventilation":   {"cooking": 1.0},
    "other":         {"preparation": 0.5, "cooking": 0.3, "storage": 0.2},
}

# 기본 패턴 DB 경로
DEFAULT_PATTERNS_PATH = Path(__file__).parent.parent.parent.parent / "data" / "extracted" / "patterns.json"


class PatternProvider:
    """패턴 DB에서 데이터 기반 추천을 제공"""

    def __init__(self, patterns_path: Optional[str] = None):
        path = Path(patterns_path) if patterns_path else DEFAULT_PATTERNS_PATH
        with open(path, "r", encoding="utf-8") as f:
            self.db = PatternDatabase.model_validate_json(f.read())

    def get_zone_ratios(self, business_type: str) -> Dict[str, float]:
        """업종별 데이터 기반 구역 비율 반환

        실데이터의 카테고리 분포를 4구역 비율로 변환.

        Returns:
            {"storage": 0.20, "preparation": 0.25, "cooking": 0.35, "washing": 0.20}
        """
        pattern = self.db.business_type_patterns.get(business_type)
        if not pattern or not pattern.category_distribution:
            return self._default_ratios()

        # 카테고리 분포 → 4구역 비율 집계
        zone_weights = {
            "storage": 0.0,
            "preparation": 0.0,
            "cooking": 0.0,
            "washing": 0.0,
        }

        for cat, ratio in pattern.category_distribution.items():
            weights = CATEGORY_TO_ZONE_WEIGHTS.get(cat, {"preparation": 1.0})
            for zone, weight in weights.items():
                if zone in zone_weights:
                    zone_weights[zone] += ratio * weight

        # 정규화
        total = sum(zone_weights.values())
        if total == 0:
            return self._default_ratios()

        ratios = {k: round(v / total, 3) for k, v in zone_weights.items()}

        # 최소 비율 보장 (어떤 구역도 10% 미만이 되지 않도록)
        min_ratio = 0.10
        for zone in ratios:
            if ratios[zone] < min_ratio:
                deficit = min_ratio - ratios[zone]
                ratios[zone] = min_ratio
                # 가장 큰 구역에서 차감
                max_zone = max(ratios, key=ratios.get)
                ratios[max_zone] -= deficit

        # 재정규화
        total = sum(ratios.values())
        return {k: round(v / total, 3) for k, v in ratios.items()}

    def get_equipment_count_estimate(
        self, business_type: str, kitchen_area_py: float
    ) -> int:
        """업종+면적 기반 예상 장비 수 반환"""
        # 면적 구간에서 기본 장비 수
        area_count = None
        for bucket in self.db.area_patterns:
            if bucket.area_min_py <= kitchen_area_py < bucket.area_max_py:
                area_count = bucket.avg_equipment_count
                break

        # 업종 평균 장비 수
        biz_pattern = self.db.business_type_patterns.get(business_type)
        biz_count = biz_pattern.avg_equipment_count if biz_pattern else None

        # 둘 다 있으면 가중 평균 (면적 60%, 업종 40%)
        if area_count and biz_count:
            return round(area_count * 0.6 + biz_count * 0.4)
        return round(area_count or biz_count or 15)

    def get_category_distribution(
        self, business_type: str
    ) -> Dict[str, float]:
        """업종별 장비 카테고리 분포 반환"""
        pattern = self.db.business_type_patterns.get(business_type)
        if pattern and pattern.category_distribution:
            return dict(pattern.category_distribution)
        return self.db.global_category_distribution

    def get_top_equipment(
        self, business_type: str, top_n: int = 20
    ) -> List[Tuple[str, str, float]]:
        """업종별 상위 빈출 장비 반환

        Returns:
            [(장비명, 카테고리, 출현비율), ...]
        """
        pattern = self.db.business_type_patterns.get(business_type)
        if not pattern:
            return []

        return [
            (ef.equipment_name, ef.category, ef.ratio)
            for ef in pattern.equipment_frequencies[:top_n]
        ]

    def get_co_occurrence_ratio(self, cat_a: str, cat_b: str) -> float:
        """두 카테고리의 공존 비율 반환"""
        for entry in self.db.co_occurrence_matrix:
            if (entry.equipment_a == cat_a and entry.equipment_b == cat_b) or \
               (entry.equipment_a == cat_b and entry.equipment_b == cat_a):
                return entry.co_occurrence_ratio
        return 0.0

    def get_zone_equipment_stats(self, zone_name: str) -> Optional[dict]:
        """구역별 장비 통계 반환"""
        for zm in self.db.zone_equipment_mappings:
            if zm.zone_name_normalized == zone_name:
                return {
                    "total_appearances": zm.total_appearances,
                    "avg_equipment_count": zm.avg_equipment_count,
                    "equipment_frequencies": zm.equipment_frequencies,
                }
        return None

    def lookup_category(self, equipment_name: str) -> str:
        """장비명으로 카테고리 조회 (1,416개 사전 활용)"""
        return self.db.equipment_name_to_category.get(equipment_name, "other")

    def get_area_bucket(self, kitchen_area_py: float) -> Optional[dict]:
        """면적 구간 패턴 반환"""
        for bucket in self.db.area_patterns:
            if bucket.area_min_py <= kitchen_area_py < bucket.area_max_py:
                return {
                    "case_count": bucket.case_count,
                    "avg_equipment_count": bucket.avg_equipment_count,
                    "category_distribution": bucket.category_distribution,
                    "common_equipment": bucket.common_equipment,
                }
        return None

    @staticmethod
    def _default_ratios() -> Dict[str, float]:
        return {
            "storage": 0.200,
            "preparation": 0.250,
            "cooking": 0.350,
            "washing": 0.200,
        }
