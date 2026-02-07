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
from ..schemas.input import FixedElement

# 장비 카테고리와 구역 매핑
CATEGORY_TO_ZONE = {
    EquipmentCategory.STORAGE: ZoneType.STORAGE,
    EquipmentCategory.PREPARATION: ZoneType.PREPARATION,
    EquipmentCategory.COOKING: ZoneType.COOKING,
    EquipmentCategory.WASHING: ZoneType.WASHING,
}

# 장비 친밀도 규칙 (주방장의 작업 동선 기반)
# key: frozenset({equip_id_base_a, equip_id_base_b}), value: bonus score
EQUIPMENT_AFFINITY = {
    # 세척 흐름: 잔반→전처리싱크→세척기→건조대
    frozenset({"scrap_table", "dishwasher_pre_sink"}): 15,
    frozenset({"scrap_table", "one_comp_sink"}): 12,
    frozenset({"scrap_table", "two_comp_sink"}): 12,
    frozenset({"dishwasher_pre_sink", "dishwasher_undercounter"}): 15,
    frozenset({"dishwasher_pre_sink", "dishwasher_door_type"}): 15,
    frozenset({"one_comp_sink", "dishwasher_undercounter"}): 12,
    frozenset({"two_comp_sink", "dishwasher_undercounter"}): 12,
    frozenset({"dishwasher_undercounter", "dish_drying_rack"}): 15,
    frozenset({"dishwasher_undercounter", "drying_rack"}): 12,
    frozenset({"dishwasher_door_type", "dish_drying_rack"}): 15,
    frozenset({"dishwasher_door_type", "drying_rack"}): 12,
    frozenset({"one_comp_sink", "dish_drying_rack"}): 10,
    frozenset({"two_comp_sink", "dish_drying_rack"}): 10,
    # 조리 핫라인: 그리들-레인지-튀김기 한 줄
    frozenset({"gas_range_3burner", "gas_range_4burner"}): 12,
    frozenset({"gas_range_3burner", "deep_fryer_single"}): 10,
    frozenset({"gas_range_3burner", "deep_fryer_double"}): 10,
    frozenset({"gas_range_3burner", "griddle"}): 10,
    frozenset({"gas_range_4burner", "deep_fryer_single"}): 10,
    frozenset({"gas_range_4burner", "deep_fryer_double"}): 10,
    frozenset({"gas_range_4burner", "griddle"}): 10,
    frozenset({"deep_fryer_single", "griddle"}): 8,
    frozenset({"deep_fryer_double", "griddle"}): 8,
    frozenset({"convection_oven", "gas_range_3burner"}): 8,
    frozenset({"convection_oven", "gas_range_4burner"}): 8,
    # 전처리 흐름: 작업대-싱크대-가공기
    frozenset({"work_table_medium", "prep_sink"}): 10,
    frozenset({"work_table_small", "prep_sink"}): 10,
    frozenset({"work_table_medium", "food_processor_station"}): 8,
    frozenset({"work_table_small", "food_processor_station"}): 8,
    frozenset({"prep_sink", "food_processor_station"}): 8,
    # 저장: 테이블냉장고는 작업대와 가까이 (구역 경계)
    frozenset({"table_refrigerator", "batt_table_refrigerator"}): 8,
}

# 구역 간 동선 방향: {현재구역: 인접해야 할 다음 구역}
# 장비의 workflow_order가 높을수록 다음 구역 경계 가까이 배치
ZONE_FLOW_NEXT = {
    ZoneType.STORAGE: ZoneType.PREPARATION,
    ZoneType.PREPARATION: ZoneType.COOKING,
    ZoneType.COOKING: ZoneType.WASHING,
    ZoneType.WASHING: None,
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
        # 배치된 장비 ID→폴리곤 매핑 (친밀도 점수 계산용)
        self._placed_equip_map: Dict[str, Polygon] = {}

    def place_equipment(
        self,
        zones: List[Zone],
        equipment_list: List[EquipmentSpec],
        restaurant_type: str = "casual",
        fixed_elements: Optional[List[FixedElement]] = None
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

        # 고정 요소를 모든 구역에 장애물로 추가
        if fixed_elements:
            for fe in fixed_elements:
                fixed_poly = create_rectangle(fe.x, fe.y, fe.width, fe.width)
                for zone_type in self.placed_polys:
                    self.placed_polys[zone_type].append(fixed_poly)

        placements = []
        unplaced = []
        warnings = []

        # 주방장 동선 기반 정렬:
        # 1차: 구역별 그룹 (WORKFLOW_ORDER 순)
        # 2차: 구역 내 작업 순서 (workflow_order)
        # 3차: 같은 순서 내에서 큰 것부터 (bin packing)
        zone_order = {
            ZoneType.STORAGE: 0,
            ZoneType.PREPARATION: 1,
            ZoneType.COOKING: 2,
            ZoneType.WASHING: 3,
        }
        sorted_equipment = sorted(
            equipment_list,
            key=lambda e: (
                zone_order.get(CATEGORY_TO_ZONE.get(e.category, ZoneType.STORAGE), 99),
                e.workflow_order,
                -(e.width * e.depth),  # 같은 순서 내에서 큰 것 우선
            )
        )

        for i, equip in enumerate(sorted_equipment):
            # 해당 카테고리의 구역 찾기
            target_zone = CATEGORY_TO_ZONE.get(equip.category)

            if target_zone not in zone_polys:
                warnings.append(f"{equip.name_ko}: 대상 구역({target_zone.value})이 없습니다")
                unplaced.append(equip.id)
                continue

            zone_poly = zone_polys[target_zone]

            # 장비별 측면 간격 기반 배치 (벽면 라인 배치 허용)
            per_equip_clearance = max(
                equip.clearance_sides,
                CONSTRAINTS["equipment_spacing"]
            )

            # 배치 후보 위치 찾기
            candidates = find_placement_candidates(
                container=zone_poly,
                item_width=equip.width,
                item_height=equip.depth,
                existing=self.placed_polys[target_zone],
                clearance=CONSTRAINTS["wall_clearance"],
                grid_step=0.2,
                equip_clearance=per_equip_clearance
            )

            if not candidates:
                # 90도 회전해서 재시도
                candidates = find_placement_candidates(
                    container=zone_poly,
                    item_width=equip.depth,  # 회전
                    item_height=equip.width,
                    existing=self.placed_polys[target_zone],
                    clearance=CONSTRAINTS["wall_clearance"],
                    grid_step=0.2,
                    equip_clearance=per_equip_clearance
                )
                rotation = 90
            else:
                rotation = 0

            if not candidates:
                warnings.append(f"{equip.name_ko}: 배치 가능한 위치가 없습니다")
                unplaced.append(equip.id)
                continue

            # 최적 위치 선택 (주방장 동선 기반)
            best_pos = self._select_best_position(
                candidates, zone_poly, equip, rotation, zone_polys
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
                self._placed_equip_map[equip.id] = placed_poly
            else:
                unplaced.append(equip.id)

        return PlacementResult(
            placements=placements,
            unplaced=unplaced,
            warnings=warnings
        )

    @staticmethod
    def _base_id(equipment_id: str) -> str:
        """장비 ID에서 인덱스 제거 (work_table_medium_0 → work_table_medium)"""
        parts = equipment_id.rsplit("_", 1)
        return parts[0] if len(parts) > 1 and parts[-1].isdigit() else equipment_id

    def _select_best_position(
        self,
        candidates: List[Tuple[float, float]],
        zone_poly: Polygon,
        equip: EquipmentSpec,
        rotation: int,
        all_zone_polys: Dict[ZoneType, Polygon] = None,
    ) -> Optional[Tuple[float, float]]:
        """주방장 동선 기반 최적 배치 위치 선택

        우선순위:
        1. 벽면 밀착 (기존)
        2. 행(row) 정렬 (기존)
        3. ★ 장비 친밀도 (동선상 연결 장비 인접)
        4. ★ 구역 경계 동선 (workflow 후반 장비 → 다음 구역 경계 가까이)
        5. ★ 핫라인/세척라인 형성 (같은 축 정렬)
        6. 통로 보존 (기존)
        """
        if not candidates:
            return None

        minx, miny, maxx, maxy = zone_poly.bounds
        w = equip.depth if rotation == 90 else equip.width
        h = equip.width if rotation == 90 else equip.depth

        target_zone = CATEGORY_TO_ZONE.get(equip.category)
        existing = self.placed_polys.get(target_zone, [])

        # 다음 구역 경계 계산 (동선 흐름)
        next_zone_boundary = None
        if all_zone_polys:
            next_zone_type = ZONE_FLOW_NEXT.get(target_zone)
            if next_zone_type and next_zone_type in all_zone_polys:
                next_poly = all_zone_polys[next_zone_type]
                # 공유 경계 찾기: 현재 구역과 다음 구역의 가장 가까운 변
                npb = next_poly.bounds
                # 4가지 경계 중 가장 가까운 것 사용
                # (현재 구역의 어느 변이 다음 구역에 가장 가까운지)
                distances = [
                    ("right", abs(maxx - npb[0])),   # 현재 우변 ↔ 다음 좌변
                    ("left", abs(minx - npb[2])),     # 현재 좌변 ↔ 다음 우변
                    ("top", abs(maxy - npb[1])),      # 현재 상변 ↔ 다음 하변
                    ("bottom", abs(miny - npb[3])),   # 현재 하변 ↔ 다음 상변
                ]
                closest_side, _ = min(distances, key=lambda d: d[1])
                next_zone_boundary = closest_side

        def score_position(pos: Tuple[float, float]) -> float:
            x, y = pos
            score = 0.0

            # ── 1. 벽면 밀착 (기존 로직 유지) ──
            dist_to_wall = min(
                abs(x - minx), abs(x + w - maxx),
                abs(y - miny), abs(y + h - maxy)
            )
            if equip.requires_wall:
                score -= dist_to_wall * 15
            else:
                score -= dist_to_wall * 5

            if dist_to_wall < 0.2:
                score += 10
                if equip.requires_wall:
                    score += 5

            # ── 2. 행 정렬 (기존 로직 유지) ──
            ALIGN_TOL = 0.05
            for ep in existing:
                epb = ep.bounds
                if (abs(x - epb[0]) < ALIGN_TOL or abs(x - epb[2]) < ALIGN_TOL or
                    abs(x + w - epb[0]) < ALIGN_TOL or abs(x + w - epb[2]) < ALIGN_TOL):
                    score += 4
                if (abs(y - epb[1]) < ALIGN_TOL or abs(y - epb[3]) < ALIGN_TOL or
                    abs(y + h - epb[1]) < ALIGN_TOL or abs(y + h - epb[3]) < ALIGN_TOL):
                    score += 4

            # ── 3. ★ 장비 친밀도 점수 (주방장 동선) ──
            item_poly = create_rectangle(x, y, w, h) if existing else None
            for placed_id, placed_poly in self._placed_equip_map.items():
                placed_base = self._base_id(placed_id)
                pair = frozenset({equip.id, placed_base})
                affinity = EQUIPMENT_AFFINITY.get(pair, 0)
                if affinity > 0 and item_poly:
                    dist = item_poly.distance(placed_poly)
                    if dist < 0.5:
                        score += affinity  # 가까우면 풀 보너스
                    elif dist < 1.5:
                        score += affinity * 0.5  # 적당히 가까우면 반 보너스
                    # 멀면 보너스 없음

            # ── 4. ★ 구역 경계 동선 점수 ──
            # workflow_order가 높은 장비(후공정)는 다음 구역 경계 쪽에 배치
            if next_zone_boundary and equip.workflow_order > 0:
                max_wf = 5  # workflow_order 최대값
                boundary_weight = equip.workflow_order / max_wf  # 0~1

                if next_zone_boundary == "right":
                    # 우측 경계가 다음 구역: x가 클수록 좋음
                    score += boundary_weight * 8 * ((x + w - minx) / (maxx - minx))
                elif next_zone_boundary == "left":
                    score += boundary_weight * 8 * ((maxx - x) / (maxx - minx))
                elif next_zone_boundary == "top":
                    score += boundary_weight * 8 * ((y + h - miny) / (maxy - miny))
                elif next_zone_boundary == "bottom":
                    score += boundary_weight * 8 * ((maxy - y) / (maxy - miny))

                # 반대로 workflow_order가 낮은(초공정) 장비는 반대편 선호
                if equip.workflow_order <= 1:
                    if next_zone_boundary == "right":
                        score += 5 * ((maxx - x - w) / (maxx - minx))
                    elif next_zone_boundary == "left":
                        score += 5 * ((x - minx) / (maxx - minx))
                    elif next_zone_boundary == "top":
                        score += 5 * ((maxy - y - h) / (maxy - miny))
                    elif next_zone_boundary == "bottom":
                        score += 5 * ((y - miny) / (maxy - miny))

            # ── 5. ★ 핫라인/세척라인 형성 ──
            # 조리/세척 장비는 같은 축(Y 또는 X)에 정렬되면 보너스
            if target_zone in (ZoneType.COOKING, ZoneType.WASHING) and existing:
                for ep in existing:
                    epb = ep.bounds
                    # Y축 정렬 (같은 행 = 같은 Y 시작)
                    if abs(y - epb[1]) < 0.1:
                        score += 10  # 강한 라인 형성 보너스
                        break
                    # X축 정렬 (같은 열 = 같은 X 시작)
                    if abs(x - epb[0]) < 0.1:
                        score += 10
                        break

            # ── 6. 인접 밀착 및 통로 보존 (기존 로직 유지) ──
            if existing:
                if item_poly is None:
                    item_poly = create_rectangle(x, y, w, h)
                min_dist = min(item_poly.distance(ep) for ep in existing)
                score -= min_dist * 2

                for ep in existing:
                    dist = item_poly.distance(ep)
                    if dist < 0.35:
                        score += 6
                        break

                for ep in existing:
                    dist = item_poly.distance(ep) if item_poly else 999
                    if 0.3 < dist < 0.8:
                        epb = ep.bounds
                        same_row = (abs(y - epb[1]) < 0.1 or abs(y + h - epb[3]) < 0.1 or
                                   abs(x - epb[0]) < 0.1 or abs(x + w - epb[2]) < 0.1)
                        if not same_row:
                            score -= 8

            # ── 7. 약간의 랜덤성 ──
            score += self.rng.random() * 0.3

            return score

        best = max(candidates, key=score_position)
        return best

    def get_placement_polygons(self) -> Dict[ZoneType, List[Polygon]]:
        """배치된 장비 폴리곤 반환"""
        return self.placed_polys
