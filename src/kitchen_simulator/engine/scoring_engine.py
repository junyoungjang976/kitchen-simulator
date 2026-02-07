"""점수화 엔진"""
from typing import Dict, List, Tuple
from dataclasses import dataclass
from shapely.geometry import Polygon
import math

from ..domain.zone import Zone, ZoneType, WORKFLOW_ORDER
from ..domain.equipment import EquipmentPlacement
from ..domain.constraint import ConstraintViolation, CONSTRAINTS
from ..geometry.polygon import create_polygon, get_area, get_centroid, get_bounds

@dataclass
class ScoreBreakdown:
    """점수 세부 내역"""
    workflow_efficiency: float  # 동선 효율 (0-1)
    space_utilization: float    # 공간 활용 (0-1)
    safety_compliance: float    # 안전 준수 (0-1)
    accessibility: float        # 접근성 (0-1)
    overall: float              # 종합 점수 (0-100)

class ScoringEngine:
    """배치 품질 점수화 엔진"""

    # 가중치
    WEIGHTS = {
        "workflow": 0.40,
        "space": 0.25,
        "safety": 0.20,
        "accessibility": 0.15,
    }

    def calculate_scores(
        self,
        zones: List[Zone],
        placements: List[EquipmentPlacement],
        violations: List[ConstraintViolation],
        zone_polys: Dict[ZoneType, Polygon],
        placement_polys: Dict[ZoneType, List[Polygon]]
    ) -> ScoreBreakdown:
        """점수 계산

        Args:
            zones: 구역 리스트
            placements: 장비 배치 리스트
            violations: 제약 위반 리스트
            zone_polys: 구역 폴리곤
            placement_polys: 장비 배치 폴리곤

        Returns:
            ScoreBreakdown
        """
        # 1. 동선 효율 점수
        workflow = self._calculate_workflow_efficiency(zones, zone_polys)

        # 2. 공간 활용 점수
        space = self._calculate_space_utilization(zones, placement_polys)

        # 3. 안전 준수 점수
        safety = self._calculate_safety_compliance(violations)

        # 4. 접근성 점수
        accessibility = self._calculate_accessibility(zones, placement_polys)

        # 종합 점수 (가중 평균)
        overall = (
            workflow * self.WEIGHTS["workflow"] +
            space * self.WEIGHTS["space"] +
            safety * self.WEIGHTS["safety"] +
            accessibility * self.WEIGHTS["accessibility"]
        ) * 100

        return ScoreBreakdown(
            workflow_efficiency=round(workflow, 3),
            space_utilization=round(space, 3),
            safety_compliance=round(safety, 3),
            accessibility=round(accessibility, 3),
            overall=round(overall, 1)
        )

    def _calculate_workflow_efficiency(
        self,
        zones: List[Zone],
        zone_polys: Dict[ZoneType, Polygon]
    ) -> float:
        """동선 효율 계산

        작업 흐름 순서(저장→전처리→조리→세척)에 따른
        구역 간 이동 거리가 짧을수록 높은 점수
        """
        zone_centers = {}
        for zone in zones:
            if zone.zone_type in zone_polys:
                poly = zone_polys[zone.zone_type]
                center = poly.centroid
                zone_centers[zone.zone_type] = (center.x, center.y)

        if len(zone_centers) < 2:
            return 0.5

        # 워크플로우 순서대로 거리 합산
        total_distance = 0
        for i in range(len(WORKFLOW_ORDER) - 1):
            from_zone = WORKFLOW_ORDER[i]
            to_zone = WORKFLOW_ORDER[i + 1]

            if from_zone in zone_centers and to_zone in zone_centers:
                c1 = zone_centers[from_zone]
                c2 = zone_centers[to_zone]
                dist = math.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)
                total_distance += dist

        # 주방 크기 기반 적응형 점수
        all_bounds = [poly.bounds for poly in zone_polys.values()]
        if all_bounds:
            overall_minx = min(b[0] for b in all_bounds)
            overall_miny = min(b[1] for b in all_bounds)
            overall_maxx = max(b[2] for b in all_bounds)
            overall_maxy = max(b[3] for b in all_bounds)
            kitchen_w = overall_maxx - overall_minx
            kitchen_h = overall_maxy - overall_miny
        else:
            kitchen_w, kitchen_h = 10.0, 8.0

        perimeter = 2 * (kitchen_w + kitchen_h)
        optimal = (kitchen_w + kitchen_h) * 0.75  # 2D 배치 현실 반영
        max_dist = perimeter

        if max_dist <= optimal:
            return 0.5

        efficiency = (max_dist - total_distance) / (max_dist - optimal)
        efficiency = max(0.0, min(1.0, efficiency))

        return efficiency

    def _calculate_space_utilization(
        self,
        zones: List[Zone],
        placement_polys: Dict[ZoneType, List[Polygon]]
    ) -> float:
        """공간 활용도 계산

        배치된 장비 면적 / 전체 구역 면적
        """
        total_zone_area = sum(z.area for z in zones)
        if total_zone_area == 0:
            return 0.0

        total_equipment_area = 0
        for polys in placement_polys.values():
            for poly in polys:
                total_equipment_area += poly.area

        # 상업용 주방 현실 반영: 장비 면적 비율 12-35%가 이상적
        utilization = total_equipment_area / total_zone_area

        if 0.12 <= utilization <= 0.35:
            return 1.0
        elif utilization < 0.12:
            return utilization / 0.12
        else:
            return max(0, 1 - (utilization - 0.35) / 0.35)

    def _calculate_safety_compliance(
        self,
        violations: List[ConstraintViolation]
    ) -> float:
        """안전 준수 점수

        위반 건수에 따른 감점
        """
        if not violations:
            return 1.0

        error_count = sum(1 for v in violations if v.severity == "error")
        warning_count = sum(1 for v in violations if v.severity == "warning")

        # 에러당 -0.2, 경고당 -0.05
        penalty = error_count * 0.2 + warning_count * 0.05

        return max(0, 1 - penalty)

    def _calculate_accessibility(
        self,
        zones: List[Zone],
        placement_polys: Dict[ZoneType, List[Polygon]]
    ) -> float:
        """접근성 점수

        각 장비의 최근접 이웃 간격으로 평가 (전체 쌍이 아닌 인접 장비만)
        """
        all_gaps = []

        for zone_type, polys in placement_polys.items():
            if len(polys) < 2:
                continue

            for i in range(len(polys)):
                min_gap = float('inf')
                for j in range(len(polys)):
                    if i != j:
                        gap = polys[i].distance(polys[j])
                        min_gap = min(min_gap, gap)
                if min_gap < float('inf'):
                    all_gaps.append(min_gap)

        if not all_gaps:
            return 0.8

        avg_gap = sum(all_gaps) / len(all_gaps)

        # 이상적 간격: 0.3m(장비 간격) ~ 1.5m
        # 벽면 라인 배치 시 측면 간격 0.30m은 정상
        min_ideal = CONSTRAINTS["equipment_spacing"]  # 0.30m
        if min_ideal <= avg_gap <= 1.5:
            return 1.0
        elif avg_gap < min_ideal:
            return avg_gap / min_ideal
        else:
            return max(0.5, 1 - (avg_gap - 1.5) / 3)
