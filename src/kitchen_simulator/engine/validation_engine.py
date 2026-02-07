"""제약 조건 검증 엔진"""
from typing import List, Dict, Tuple, Optional
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
        placement_polys: Dict[ZoneType, List[Polygon]],
        fixed_elements: Optional[List] = None
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

        # 5. 인프라 근접성 검증
        if fixed_elements:
            self._validate_infrastructure_proximity(zones, zone_polys, fixed_elements)

        # 6. 레인지 인접 간격 검증
        self._validate_range_spacing(placements, placement_polys)

        # 7. 구역 간 양방향 통로 검증
        self._validate_cross_zone_aisles(placement_polys)

        # 8. 인프라 요건 경고 (고정 요소 미지정 시)
        if not fixed_elements:
            self._warn_missing_infrastructure(placements)

        # 에러만 있으면 실패
        has_errors = any(v.severity == "error" for v in self.violations)
        return not has_errors, self.violations

    def _validate_aisle_widths(
        self,
        zone_polys: Dict[ZoneType, Polygon],
        placement_polys: Dict[ZoneType, List[Polygon]]
    ):
        """장비 간 간격 검증

        벽면 라인 배치를 허용하되, 물리적 최소 간격(equipment_spacing)은 확보.
        통로폭(min_aisle_single) 미달은 info로 표시.
        """
        min_spacing = CONSTRAINTS["equipment_spacing"]
        min_aisle = CONSTRAINTS["min_aisle_single"]

        for zone_type, placements in placement_polys.items():
            if zone_type not in zone_polys:
                continue

            zone_poly = zone_polys[zone_type]

            # 물리적 최소 간격 위반 검사
            spacing_violations = check_aisle_width(zone_poly, placements, min_spacing)
            for location, actual_width in spacing_violations:
                self.violations.append(ConstraintViolation(
                    constraint_type=ConstraintType.EQUIPMENT_SPACING,
                    message=f"장비 간격이 최소 기준({min_spacing*100:.0f}cm)보다 좁습니다 "
                           f"(실제: {actual_width*100:.0f}cm)",
                    location=location,
                    severity="error"
                ))

            # 통로폭 미달은 info (벽면 라인 배치 시 정상)
            aisle_violations = check_aisle_width(zone_poly, placements, min_aisle)
            for location, actual_width in aisle_violations:
                if actual_width >= min_spacing:
                    self.violations.append(ConstraintViolation(
                        constraint_type=ConstraintType.AISLE_WIDTH,
                        message=f"장비 간 통로 폭 {actual_width*100:.0f}cm "
                               f"(권장: {min_aisle*100:.0f}cm 이상)",
                        location=location,
                        severity="info"
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

    def _validate_infrastructure_proximity(
        self,
        zones: List[Zone],
        zone_polys: Dict[ZoneType, Polygon],
        fixed_elements: List
    ):
        """인프라 설비(환기/급수/배수) 근접성 검증"""
        from shapely.geometry import Point

        # 고정 요소를 유형별로 분류
        vents = [fe for fe in fixed_elements if fe.type == "vent"]
        waters = [fe for fe in fixed_elements if fe.type == "water"]
        drains = [fe for fe in fixed_elements if fe.type == "drain"]

        zone_by_type = {z.zone_type: z for z in zones}

        # 환기구 - 조리구역 근접성
        if vents and ZoneType.COOKING in zone_by_type:
            cooking_poly = zone_polys[ZoneType.COOKING]
            cooking_center = cooking_poly.centroid

            min_dist = min(
                Point(v.x, v.y).distance(cooking_center) for v in vents
            )
            max_allowed = CONSTRAINTS["max_vent_distance"]
            if min_dist > max_allowed:
                self.violations.append(ConstraintViolation(
                    constraint_type=ConstraintType.VENTILATION,
                    message=f"환기구가 조리구역에서 너무 멉니다 "
                           f"(거리: {min_dist:.1f}m, 기준: {max_allowed:.1f}m)",
                    location=(cooking_center.x, cooking_center.y),
                    severity="warning"
                ))

        # 급수 - 세척구역 근접성
        if waters and ZoneType.WASHING in zone_by_type:
            washing_poly = zone_polys[ZoneType.WASHING]
            washing_center = washing_poly.centroid

            min_dist = min(
                Point(w.x, w.y).distance(washing_center) for w in waters
            )
            max_allowed = CONSTRAINTS["max_water_distance"]
            if min_dist > max_allowed:
                self.violations.append(ConstraintViolation(
                    constraint_type=ConstraintType.WATER_ACCESS,
                    message=f"급수 시설이 세척구역에서 너무 멉니다 "
                           f"(거리: {min_dist:.1f}m, 기준: {max_allowed:.1f}m)",
                    location=(washing_center.x, washing_center.y),
                    severity="warning"
                ))

        # 배수 - 세척구역 근접성
        if drains and ZoneType.WASHING in zone_by_type:
            washing_poly = zone_polys[ZoneType.WASHING]
            washing_center = washing_poly.centroid

            min_dist = min(
                Point(d.x, d.y).distance(washing_center) for d in drains
            )
            max_allowed = CONSTRAINTS["max_drain_distance"]
            if min_dist > max_allowed:
                self.violations.append(ConstraintViolation(
                    constraint_type=ConstraintType.DRAIN_ACCESS,
                    message=f"배수구가 세척구역에서 너무 멉니다 "
                           f"(거리: {min_dist:.1f}m, 기준: {max_allowed:.1f}m)",
                    location=(washing_center.x, washing_center.y),
                    severity="warning"
                ))

    def _validate_range_spacing(
        self,
        placements: List[EquipmentPlacement],
        placement_polys: Dict[ZoneType, List[Polygon]]
    ):
        """레인지(가스레인지/튀김기 등) 인접 간격 검증"""
        from ..geometry.collision import get_distance as poly_distance

        range_spacing = CONSTRAINTS["range_spacing"]

        # 조리 구역 장비 중 레인지 류 식별
        cooking_placements = [
            p for p in placements if p.zone_type == ZoneType.COOKING
        ]
        cooking_polys = placement_polys.get(ZoneType.COOKING, [])

        if len(cooking_placements) < 2 or len(cooking_polys) < 2:
            return

        # 조리 장비 쌍 간 range_spacing 확인
        for i in range(len(cooking_polys)):
            equip_id_i = cooking_placements[i].equipment_id.rsplit("_", 1)[0]
            spec_i = EQUIPMENT_CATALOG.get(equip_id_i)
            if not spec_i or spec_i.clearance_sides < range_spacing:
                continue

            for j in range(i + 1, len(cooking_polys)):
                equip_id_j = cooking_placements[j].equipment_id.rsplit("_", 1)[0]
                spec_j = EQUIPMENT_CATALOG.get(equip_id_j)
                if not spec_j:
                    continue

                dist = cooking_polys[i].distance(cooking_polys[j])
                if 0 < dist < range_spacing:
                    center = cooking_polys[i].centroid
                    self.violations.append(ConstraintViolation(
                        constraint_type=ConstraintType.RANGE_SPACING,
                        message=f"{spec_i.name_ko}↔{spec_j.name_ko} 인접 간격이 "
                               f"기준({range_spacing*100:.0f}cm)보다 좁습니다 "
                               f"(실제: {dist*100:.0f}cm)",
                        location=(center.x, center.y),
                        severity="warning"
                    ))

    def _validate_cross_zone_aisles(
        self,
        placement_polys: Dict[ZoneType, List[Polygon]]
    ):
        """구역 간 양방향 통로 폭 검증"""
        from ..domain.zone import ADJACENCY_RULES
        min_double = CONSTRAINTS["min_aisle_double"]

        zone_types = list(placement_polys.keys())
        checked = set()

        for zt1 in zone_types:
            for zt2 in zone_types:
                if zt1 == zt2:
                    continue
                pair = (min(zt1.value, zt2.value), max(zt1.value, zt2.value))
                if pair in checked:
                    continue
                checked.add(pair)

                # 인접 구역 간만 검증
                if zt2 not in ADJACENCY_RULES.get(zt1, []) and \
                   zt1 not in ADJACENCY_RULES.get(zt2, []):
                    continue

                for p1 in placement_polys[zt1]:
                    for p2 in placement_polys[zt2]:
                        dist = p1.distance(p2)
                        if 0 < dist < min_double:
                            c1 = p1.centroid
                            c2 = p2.centroid
                            mid = ((c1.x + c2.x) / 2, (c1.y + c2.y) / 2)
                            self.violations.append(ConstraintViolation(
                                constraint_type=ConstraintType.AISLE_WIDTH,
                                message=f"구역 간 통로 폭이 양방향 기준({min_double*100:.0f}cm)보다 "
                                       f"좁습니다 (실제: {dist*100:.0f}cm)",
                                location=mid,
                                severity="warning"
                            ))

    def _warn_missing_infrastructure(
        self,
        placements: List[EquipmentPlacement]
    ):
        """인프라 요건 경고 (고정 요소 미지정 시)"""
        needs_vent = []
        needs_water = []
        needs_drain = []

        for p in placements:
            equip_id = p.equipment_id.rsplit("_", 1)[0]
            spec = EQUIPMENT_CATALOG.get(equip_id)
            if not spec:
                continue

            if spec.requires_ventilation:
                needs_vent.append(spec.name_ko)
            if spec.requires_water:
                needs_water.append(spec.name_ko)
            if spec.requires_drain:
                needs_drain.append(spec.name_ko)

        if needs_vent:
            names = ", ".join(sorted(set(needs_vent)))
            self.violations.append(ConstraintViolation(
                constraint_type=ConstraintType.VENTILATION,
                message=f"환기 시설 필요 장비: {names} (고정 요소 미지정)",
                location=(0, 0),
                severity="info"
            ))
        if needs_water:
            names = ", ".join(sorted(set(needs_water)))
            self.violations.append(ConstraintViolation(
                constraint_type=ConstraintType.WATER_ACCESS,
                message=f"급수 시설 필요 장비: {names} (고정 요소 미지정)",
                location=(0, 0),
                severity="info"
            ))
        if needs_drain:
            names = ", ".join(sorted(set(needs_drain)))
            self.violations.append(ConstraintViolation(
                constraint_type=ConstraintType.DRAIN_ACCESS,
                message=f"배수 시설 필요 장비: {names} (고정 요소 미지정)",
                location=(0, 0),
                severity="info"
            ))

    def get_summary(self) -> Dict:
        """검증 결과 요약"""
        errors = [v for v in self.violations if v.severity == "error"]
        warnings = [v for v in self.violations if v.severity == "warning"]
        infos = [v for v in self.violations if v.severity == "info"]

        return {
            "passed": len(errors) == 0,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "info_count": len(infos),
            "errors": [v.message for v in errors],
            "warnings": [v.message for v in warnings],
            "infos": [v.message for v in infos],
        }
