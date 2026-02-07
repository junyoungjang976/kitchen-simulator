"""C3 레이아웃 생성기 - 장비+배치 동시 생성"""
from typing import Dict, List, Optional, Tuple

from .models import GenerationResult, GeneratedEquipment
from .equipment_generator import EquipmentGenerator
from ..domain.kitchen import Kitchen, KitchenShape, RestaurantType
from ..domain.equipment import EquipmentSpec
from ..data.equipment_catalog import EQUIPMENT_CATALOG
from ..engine.optimizer import Optimizer, OptimizationResult
from ..patterns.provider import PatternProvider


class LayoutGenerator:
    """C3 통합 생성기 - 업종+면적+형태 → 장비 리스트 + 최적 배치"""

    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        self.equipment_gen = EquipmentGenerator(seed=seed)
        self.provider = PatternProvider()

    def generate(
        self,
        business_type: str,
        kitchen_area_py: float,
        shape: KitchenShape = KitchenShape.RECTANGLE,
        seat_count: int = 30,
        width: Optional[float] = None,
        depth: Optional[float] = None,
        fixed_elements: Optional[List] = None,
        iterations: int = 50,
    ) -> Tuple[GenerationResult, OptimizationResult]:
        """장비 리스트 생성 + 레이아웃 최적화 동시 실행

        파이프라인:
        1. EquipmentGenerator → 패턴 기반 장비 리스트
        2. 장비 리스트 → EquipmentSpec 변환 (카탈로그 매핑)
        3. Kitchen 객체 생성
        4. Optimizer → 최적 배치 탐색

        Args:
            business_type: 업종 (korean, cafe, etc.)
            kitchen_area_py: 주방 면적 (평)
            shape: 주방 형태
            seat_count: 좌석 수
            width: 주방 가로 (m), None이면 자동 계산
            depth: 주방 세로 (m), None이면 자동 계산
            fixed_elements: 고정 요소 리스트
            iterations: 최적화 반복 횟수

        Returns:
            (GenerationResult, OptimizationResult)
        """
        # 1. 장비 리스트 생성
        generated_equipment, similar_cases = self.equipment_gen.generate(
            business_type=business_type,
            kitchen_area_py=kitchen_area_py,
            shape_type=shape.value if shape else None,
        )

        # 2. EquipmentSpec 변환
        equipment_specs = self._to_equipment_specs(generated_equipment)

        # 3. Kitchen 객체 생성
        area_sqm = kitchen_area_py * 3.306  # 평 → m²
        if width and depth:
            w, d = width, depth
        else:
            # 정사각형에 가깝게 자동 계산 (가로:세로 = 1.2:1)
            w = (area_sqm ** 0.5) * 1.1
            d = area_sqm / w

        vertices = [(0, 0), (w, 0), (w, d), (0, d)]

        # RestaurantType enum 매핑 (업종 문자열 → enum)
        rest_type = self._map_restaurant_type(business_type)

        kitchen = Kitchen(
            shape=shape,
            vertices=vertices,
            restaurant_type=rest_type,
            seat_count=seat_count,
        )

        # 4. 최적화 실행
        optimizer = Optimizer(seed=self.seed)
        opt_result = optimizer.optimize(
            kitchen=kitchen,
            equipment_list=equipment_specs,
            iterations=iterations,
            fixed_elements=fixed_elements,
        )

        # 5. GenerationResult 조립
        zone_ratios = self.provider.get_zone_ratios(business_type)

        gen_result = GenerationResult(
            business_type=business_type,
            kitchen_area_py=kitchen_area_py,
            similar_cases=similar_cases,
            generated_equipment=generated_equipment,
            recommended_zone_ratios=zone_ratios,
            generation_method="retrieval_augmented_statistical",
            pattern_coverage=self._calc_coverage(generated_equipment),
        )

        return gen_result, opt_result

    def _to_equipment_specs(
        self, generated: List[GeneratedEquipment]
    ) -> List[EquipmentSpec]:
        """GeneratedEquipment → EquipmentSpec 변환"""
        specs = []
        seen_ids = set()

        for eq in generated:
            catalog_id = eq.catalog_id
            if catalog_id and catalog_id in EQUIPMENT_CATALOG:
                spec = EQUIPMENT_CATALOG[catalog_id]
                # 중복 허용 (같은 장비 여러 개 배치 가능)
                specs.append(spec)
            # catalog_id가 없는 장비는 스킵 (카탈로그에 없는 장비)

        return specs

    def _map_restaurant_type(self, business_type: str) -> RestaurantType:
        """업종 문자열 → RestaurantType enum 매핑"""
        # 직접 매핑 시도
        for rt in RestaurantType:
            if rt.value == business_type:
                return rt

        # 유사 매핑
        FALLBACK_MAP = {
            "franchise": RestaurantType.FAST_FOOD,
            "snack_bar": RestaurantType.FAST_FOOD,
            "other": RestaurantType.CASUAL,
        }
        return FALLBACK_MAP.get(business_type, RestaurantType.CASUAL)

    def _calc_coverage(self, equipment: List[GeneratedEquipment]) -> float:
        """패턴 커버리지 계산 (카탈로그 매핑 비율)"""
        if not equipment:
            return 0.0
        mapped = sum(1 for eq in equipment if eq.catalog_id)
        return round(mapped / len(equipment), 3)
