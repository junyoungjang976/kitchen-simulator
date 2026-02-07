"""최적화 엔진"""
from typing import List, Optional, Tuple
from dataclasses import dataclass
import random
import time

from ..domain.kitchen import Kitchen
from ..domain.zone import Zone
from ..domain.equipment import EquipmentSpec
from .zone_engine import ZoneEngine
from .placement_engine import PlacementEngine, PlacementResult
from .validation_engine import ValidationEngine
from .scoring_engine import ScoringEngine, ScoreBreakdown
from ..geometry.polygon import create_polygon

@dataclass
class OptimizationResult:
    """최적화 결과"""
    best_zones: List[Zone]
    best_placements: PlacementResult
    best_score: ScoreBreakdown
    iterations_run: int
    computation_time_ms: float
    all_scores: List[float]  # 모든 반복의 점수

class Optimizer:
    """배치 최적화 엔진"""

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        self.rng = random.Random(seed)

    def optimize(
        self,
        kitchen: Kitchen,
        equipment_list: Optional[List[EquipmentSpec]] = None,
        iterations: int = 100,
        early_stop_threshold: float = 95.0,
        fixed_elements: Optional[List] = None
    ) -> OptimizationResult:
        """최적 배치 탐색

        Args:
            kitchen: 주방 객체
            equipment_list: 장비 목록 (None이면 기본 세트)
            iterations: 반복 횟수
            early_stop_threshold: 조기 종료 점수 임계값

        Returns:
            OptimizationResult
        """
        start_time = time.time()

        best_zones = None
        best_placements = None
        best_score = None
        all_scores = []

        # 패턴 기반 기본 장비 (equipment_list가 없을 때)
        if not equipment_list:
            equipment_list = self._get_default_equipment(kitchen)

        for i in range(iterations):
            # 각 반복마다 약간 다른 비율로 구역 분할
            zone_engine = ZoneEngine()
            zones = zone_engine.divide_kitchen(
                kitchen,
                custom_ratios=self._randomize_ratios(kitchen.restaurant_type.value)
            )

            # 장비 배치
            placement_engine = PlacementEngine(seed=self.seed + i if self.seed else None)
            placements = placement_engine.place_equipment(
                zones,
                equipment_list,
                kitchen.restaurant_type.value,
                fixed_elements=fixed_elements
            )

            # 폴리곤 준비
            zone_polys = {z.zone_type: create_polygon(z.polygon) for z in zones}
            placement_polys = placement_engine.get_placement_polygons()

            # 검증
            validation_engine = ValidationEngine()
            passed, violations = validation_engine.validate_all(
                zones, placements.placements, zone_polys, placement_polys,
                fixed_elements=fixed_elements
            )

            # 점수 계산
            scoring_engine = ScoringEngine()
            score = scoring_engine.calculate_scores(
                zones, placements.placements, violations,
                zone_polys, placement_polys
            )

            all_scores.append(score.overall)

            # 최고 점수 갱신
            if best_score is None or score.overall > best_score.overall:
                best_zones = zones
                best_placements = placements
                best_score = score

            # 조기 종료
            if score.overall >= early_stop_threshold:
                break

        end_time = time.time()

        return OptimizationResult(
            best_zones=best_zones,
            best_placements=best_placements,
            best_score=best_score,
            iterations_run=len(all_scores),
            computation_time_ms=(end_time - start_time) * 1000,
            all_scores=all_scores
        )

    def _get_default_equipment(self, kitchen: Kitchen):
        """패턴 기반 기본 장비 목록 (fallback: 하드코딩)"""
        try:
            from ..data.equipment_catalog import get_equipment_from_patterns
            area_py = kitchen.area / 3.306  # m² → 평 변환
            return get_equipment_from_patterns(
                kitchen.restaurant_type.value, area_py
            )
        except Exception:
            from ..data.equipment_catalog import get_equipment_for_restaurant
            return get_equipment_for_restaurant(kitchen.restaurant_type.value)

    def _randomize_ratios(self, restaurant_type: str = "casual"):
        """패턴 기반 구역 비율 + ±5% 변동"""
        from ..domain.zone import ZoneType
        from ..geometry.partitioner import adjust_zone_ratios_from_patterns

        base = adjust_zone_ratios_from_patterns(restaurant_type)

        # ±5% 변동
        ratios = {}
        for zone_type, base_ratio in base.items():
            variation = self.rng.uniform(-0.05, 0.05)
            ratios[zone_type] = max(0.1, min(0.5, base_ratio + variation))

        # 정규화
        total = sum(ratios.values())
        return {k: v / total for k, v in ratios.items()}
