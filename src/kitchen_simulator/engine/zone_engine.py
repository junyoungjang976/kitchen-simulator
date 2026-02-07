"""4구역 자동 분할 엔진"""
from typing import Dict, List, Optional
from shapely.geometry import Polygon

from ..domain.kitchen import Kitchen, KitchenShape
from ..domain.zone import Zone, ZoneType, ZONE_RATIOS
from ..geometry.polygon import create_polygon, create_rectangle, get_area, get_vertices
from ..geometry.partitioner import (
    partition_rectangle_for_zones,
    partition_l_shape_for_zones,
    partition_u_shape_for_zones,
    adjust_zone_ratios_for_restaurant_type,
    adjust_zone_ratios_from_patterns,
)

class ZoneEngine:
    """주방 공간을 4개 작업 구역으로 분할하는 엔진"""

    def __init__(self):
        self.zone_ratios: Dict[ZoneType, float] = {}

    def divide_kitchen(
        self,
        kitchen: Kitchen,
        custom_ratios: Optional[Dict[ZoneType, float]] = None
    ) -> List[Zone]:
        """주방을 4구역으로 분할

        Args:
            kitchen: 주방 객체
            custom_ratios: 사용자 지정 비율 (None이면 식당 유형 기반)

        Returns:
            Zone 리스트 [STORAGE, PREPARATION, COOKING, WASHING]
        """
        # 비율 결정
        if custom_ratios:
            self.zone_ratios = custom_ratios
        else:
            self.zone_ratios = adjust_zone_ratios_from_patterns(
                kitchen.restaurant_type.value
            )

        # 주방 다각형 생성
        kitchen_poly = create_polygon(kitchen.vertices)

        # 형태에 따른 분할
        if kitchen.shape == KitchenShape.RECTANGLE:
            zone_polys = partition_rectangle_for_zones(kitchen_poly, self.zone_ratios)
        elif kitchen.shape == KitchenShape.L_SHAPED:
            zone_polys = partition_l_shape_for_zones(kitchen_poly, self.zone_ratios)
        elif kitchen.shape == KitchenShape.U_SHAPED:
            zone_polys = partition_u_shape_for_zones(kitchen_poly, self.zone_ratios)
        else:
            # 불규칙 형태는 바운딩 박스 기반 분할
            zone_polys = partition_rectangle_for_zones(kitchen_poly, self.zone_ratios)

        # Zone 객체 생성
        zones = []
        for zone_type in [ZoneType.STORAGE, ZoneType.PREPARATION,
                          ZoneType.COOKING, ZoneType.WASHING]:
            poly = zone_polys.get(zone_type)
            if poly and not poly.is_empty:
                zones.append(Zone(
                    zone_type=zone_type,
                    polygon=get_vertices(poly),
                    area=get_area(poly),
                ))

        return zones

    def validate_zones(self, zones: List[Zone], kitchen: Kitchen) -> List[str]:
        """구역 분할 유효성 검증

        Returns:
            경고/오류 메시지 리스트
        """
        issues = []
        total_area = kitchen.area

        for zone in zones:
            zone_ratio = zone.area / total_area if total_area > 0 else 0
            min_ratio, max_ratio = ZONE_RATIOS[zone.zone_type]

            if zone_ratio < min_ratio:
                issues.append(
                    f"{zone.zone_type.value} 구역이 권장 최소 비율({min_ratio*100:.0f}%)보다 작습니다 "
                    f"(현재: {zone_ratio*100:.1f}%)"
                )
            elif zone_ratio > max_ratio:
                issues.append(
                    f"{zone.zone_type.value} 구역이 권장 최대 비율({max_ratio*100:.0f}%)보다 큽니다 "
                    f"(현재: {zone_ratio*100:.1f}%)"
                )

        return issues

    def get_zone_summary(self, zones: List[Zone], kitchen: Kitchen) -> Dict:
        """구역 분할 요약 정보"""
        total_area = kitchen.area
        return {
            "total_area_sqm": total_area,
            "zones": {
                zone.zone_type.value: {
                    "area_sqm": round(zone.area, 2),
                    "ratio": round(zone.area / total_area, 3) if total_area > 0 else 0,
                }
                for zone in zones
            }
        }
