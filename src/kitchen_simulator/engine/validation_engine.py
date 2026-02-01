"""제약 조건 검증 엔진"""
from typing import List, Dict, Tuple
from shapely.geometry import Polygon

from ..domain.zone import Zone, ZoneType, ADJACENCY_RULES
from ..domain.equipment import EquipmentPlacement
from ..domain.constraint import ConstraintType, ConstraintViolation, CONSTRAINTS
from ..geometry.polygon import create_polygon, create_rectangle, get_bounds
from ..geometry.collision import check_aisle_width, get_distance, check_overlap
from ..data.equipment_catalog import EQUIPMENT_CATALOG

class ValidationEngine:
    """제약 조건 검증 엔진"""

    def __init__(self):
        self.violations: List[ConstraintViolation] = []

    def validate_all(
        self,
        zones: List[Zone],
        placements: List[EquipmentPlacement],
        zone_polys: Dict[ZoneType, Polygon],
        placement_polys: Dict[ZoneType, List[Polygon]]
    ) -> Tuple[bool, List[ConstraintViolation]]:
        """모든 제약 조건 검증

        Returns:
            (통과 여부, 위반 목록)
        """
        self.violations = []

        # 1. 통로 폭 검증
        self._validate_aisle_widths(zone_polys, placement_polys)

        # 2. 구역 인접성 검증
        self._validate_zone_adjacency(zones)

        # 3. 장비 충돌 검증
        self._validate_equipment_collision(placement_polys)

        # 4. 벽 이격 거리 검증
        self._validate_wall_clearance(zone_polys, placement_polys)

        # 에러만 있으면 실패
        has_errors = any(v.severity == "error" for v in self.violations)
        return not has_errors, self.violations

    def _validate_aisle_widths(
        self,
        zone_polys: Dict[ZoneType, Polygon],
        placement_polys: Dict[ZoneType, List[Polygon]]
    ):
        """통로 폭 검증"""
        min_aisle = CONSTRAINTS["min_aisle_single"]

        for zone_type, placements in placement_polys.items():
            if zone_type not in zone_polys:
                continue

            zone_poly = zone_polys[zone_type]
            violations = check_aisle_width(zone_poly, placements, min_aisle)

            for location, actual_width in violations:
                self.violations.append(ConstraintViolation(
                    constraint_type=ConstraintType.AISLE_WIDTH,
                    message=f"통로 폭이 최소 기준({min_aisle*100:.0f}cm)보다 좁습니다 "
                           f"(실제: {actual_width*100:.0f}cm)",
                    location=location,
                    severity="error" if actual_width < min_aisle * 0.8 else "warning"
                ))

    def _validate_zone_adjacency(self, zones: List[Zone]):
        """구역 인접성 규칙 검증"""
        zone_by_type = {z.zone_type: z for z in zones}

        for zone_type, required_neighbors in ADJACENCY_RULES.items():
            if zone_type not in zone_by_type:
                continue

            zone = zone_by_type[zone_type]
            zone_poly = create_polygon(zone.polygon)

            for required in required_neighbors:
                if required not in zone_by_type:
                    continue

                neighbor = zone_by_type[required]
                neighbor_poly = create_polygon(neighbor.polygon)

                # 인접 여부 확인 (접촉 또는 0.5m 이내)
                distance = get_distance(zone_poly, neighbor_poly)
                if distance > 0.5:
                    center = zone_poly.centroid
                    self.violations.append(ConstraintViolation(
                        constraint_type=ConstraintType.ZONE_ADJACENCY,
                        message=f"{zone_type.value} 구역이 {required.value} 구역과 인접하지 않습니다 "
                               f"(거리: {distance:.1f}m)",
                        location=(center.x, center.y),
                        severity="warning"
                    ))

    def _validate_equipment_collision(
        self,
        placement_polys: Dict[ZoneType, List[Polygon]]
    ):
        """장비 간 충돌 검증"""
        all_polys = []
        for polys in placement_polys.values():
            all_polys.extend(polys)

        for i in range(len(all_polys)):
            for j in range(i + 1, len(all_polys)):
                if check_overlap(all_polys[i], all_polys[j]):
                    center = all_polys[i].centroid
                    self.violations.append(ConstraintViolation(
                        constraint_type=ConstraintType.EQUIPMENT_SPACING,
                        message="장비가 서로 겹칩니다",
                        location=(center.x, center.y),
                        severity="error"
                    ))

    def _validate_wall_clearance(
        self,
        zone_polys: Dict[ZoneType, Polygon],
        placement_polys: Dict[ZoneType, List[Polygon]]
    ):
        """벽 이격 거리 검증"""
        min_clearance = CONSTRAINTS["wall_clearance"]

        for zone_type, placements in placement_polys.items():
            if zone_type not in zone_polys:
                continue

            zone_poly = zone_polys[zone_type]
            zone_bounds = get_bounds(zone_poly)

            for place_poly in placements:
                minx, miny, maxx, maxy = place_poly.bounds

                # 각 변의 벽 거리 확인
                distances = [
                    abs(minx - zone_bounds[0]),  # 좌측
                    abs(maxx - zone_bounds[2]),  # 우측
                    abs(miny - zone_bounds[1]),  # 하단
                    abs(maxy - zone_bounds[3]),  # 상단
                ]

                for dist in distances:
                    if 0 < dist < min_clearance:
                        center = place_poly.centroid
                        self.violations.append(ConstraintViolation(
                            constraint_type=ConstraintType.WALL_CLEARANCE,
                            message=f"벽 이격 거리가 최소 기준({min_clearance*100:.0f}cm)보다 작습니다 "
                                   f"(실제: {dist*100:.0f}cm)",
                            location=(center.x, center.y),
                            severity="warning"
                        ))

    def get_summary(self) -> Dict:
        """검증 결과 요약"""
        errors = [v for v in self.violations if v.severity == "error"]
        warnings = [v for v in self.violations if v.severity == "warning"]

        return {
            "passed": len(errors) == 0,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": [v.message for v in errors],
            "warnings": [v.message for v in warnings],
        }
