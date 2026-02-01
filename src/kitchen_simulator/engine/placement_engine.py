"""장비 배치 엔진"""
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from shapely.geometry import Polygon
import random

from ..domain.zone import Zone, ZoneType
from ..domain.equipment import EquipmentSpec, EquipmentPlacement, EquipmentCategory
from ..domain.constraint import CONSTRAINTS
from ..geometry.polygon import create_polygon, create_rectangle, get_bounds
from ..geometry.collision import (
    check_overlap, check_contains,
    find_placement_candidates, get_distance
)
from ..data.equipment_catalog import get_equipment_for_restaurant, EQUIPMENT_CATALOG

# 장비 카테고리와 구역 매핑
CATEGORY_TO_ZONE = {
    EquipmentCategory.STORAGE: ZoneType.STORAGE,
    EquipmentCategory.PREPARATION: ZoneType.PREPARATION,
    EquipmentCategory.COOKING: ZoneType.COOKING,
    EquipmentCategory.WASHING: ZoneType.WASHING,
}

@dataclass
class PlacementResult:
    """배치 결과"""
    placements: List[EquipmentPlacement]
    unplaced: List[str]  # 배치 실패한 장비 ID
    warnings: List[str]

class PlacementEngine:
    """장비 배치 엔진"""

    def __init__(self, seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self.placed_polys: Dict[ZoneType, List[Polygon]] = {}

    def place_equipment(
        self,
        zones: List[Zone],
        equipment_list: List[EquipmentSpec],
        restaurant_type: str = "casual"
    ) -> PlacementResult:
        """장비를 구역에 배치

        Args:
            zones: 구역 리스트
            equipment_list: 배치할 장비 목록
            restaurant_type: 식당 유형 (기본 장비 선택용)

        Returns:
            PlacementResult
        """
        # 장비 목록이 없으면 기본 세트 사용
        if not equipment_list:
            equipment_list = get_equipment_for_restaurant(restaurant_type)

        # 구역별 폴리곤 준비
        zone_polys: Dict[ZoneType, Polygon] = {}
        for zone in zones:
            zone_polys[zone.zone_type] = create_polygon(zone.polygon)
            self.placed_polys[zone.zone_type] = []

        placements = []
        unplaced = []
        warnings = []

        # 장비 크기 순으로 정렬 (큰 것부터)
        sorted_equipment = sorted(
            equipment_list,
            key=lambda e: e.width * e.depth,
            reverse=True
        )

        for i, equip in enumerate(sorted_equipment):
            # 해당 카테고리의 구역 찾기
            target_zone = CATEGORY_TO_ZONE.get(equip.category)

            if target_zone not in zone_polys:
                warnings.append(f"{equip.name_ko}: 대상 구역({target_zone.value})이 없습니다")
                unplaced.append(equip.id)
                continue

            zone_poly = zone_polys[target_zone]

            # 배치 후보 위치 찾기
            candidates = find_placement_candidates(
                container=zone_poly,
                item_width=equip.width,
                item_height=equip.depth,
                existing=self.placed_polys[target_zone],
                clearance=max(equip.clearance_sides, CONSTRAINTS["wall_clearance"]),
                grid_step=0.1
            )

            if not candidates:
                # 90도 회전해서 재시도
                candidates = find_placement_candidates(
                    container=zone_poly,
                    item_width=equip.depth,  # 회전
                    item_height=equip.width,
                    existing=self.placed_polys[target_zone],
                    clearance=max(equip.clearance_sides, CONSTRAINTS["wall_clearance"]),
                    grid_step=0.1
                )
                rotation = 90
            else:
                rotation = 0

            if not candidates:
                warnings.append(f"{equip.name_ko}: 배치 가능한 위치가 없습니다")
                unplaced.append(equip.id)
                continue

            # 최적 위치 선택 (벽 가까이, 통로 확보)
            best_pos = self._select_best_position(
                candidates, zone_poly, equip, rotation
            )

            if best_pos:
                x, y = best_pos
                w = equip.depth if rotation == 90 else equip.width
                h = equip.width if rotation == 90 else equip.depth

                placement = EquipmentPlacement(
                    equipment_id=f"{equip.id}_{i}",
                    zone_type=target_zone,
                    x=x,
                    y=y,
                    rotation=rotation
                )
                placements.append(placement)

                # 배치된 폴리곤 기록
                placed_poly = create_rectangle(x, y, w, h)
                self.placed_polys[target_zone].append(placed_poly)
            else:
                unplaced.append(equip.id)

        return PlacementResult(
            placements=placements,
            unplaced=unplaced,
            warnings=warnings
        )

    def _select_best_position(
        self,
        candidates: List[Tuple[float, float]],
        zone_poly: Polygon,
        equip: EquipmentSpec,
        rotation: int
    ) -> Optional[Tuple[float, float]]:
        """최적 배치 위치 선택

        우선순위:
        1. 벽면 장비는 벽 가까이
        2. 중앙 접근성 확보
        3. 기존 장비와의 간격
        """
        if not candidates:
            return None

        minx, miny, maxx, maxy = zone_poly.bounds
        zone_center = ((minx + maxx) / 2, (miny + maxy) / 2)

        def score_position(pos: Tuple[float, float]) -> float:
            x, y = pos
            score = 0.0

            # 벽 가까이 (벽면 장비인 경우)
            if equip.requires_wall:
                dist_to_wall = min(
                    abs(x - minx), abs(x + equip.width - maxx),
                    abs(y - miny), abs(y + equip.depth - maxy)
                )
                score -= dist_to_wall * 10  # 벽에서 멀수록 감점

            # 중앙 접근성 (비벽면 장비)
            else:
                dist_to_center = ((x - zone_center[0])**2 + (y - zone_center[1])**2)**0.5
                score -= dist_to_center * 2

            # 약간의 랜덤성
            score += self.rng.random() * 0.5

            return score

        best = max(candidates, key=score_position)
        return best

    def get_placement_polygons(self) -> Dict[ZoneType, List[Polygon]]:
        """배치된 장비 폴리곤 반환"""
        return self.placed_polys
