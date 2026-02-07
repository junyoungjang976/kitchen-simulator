"""공간 분할 알고리즘"""
from typing import List, Dict, Tuple, Optional
from shapely.geometry import Polygon
from .polygon import (
    create_polygon, create_rectangle, get_bounds, get_area,
    split_rectangle_horizontal, split_rectangle_vertical, buffer_polygon
)
from ..domain.zone import ZoneType, ZONE_RATIOS, WORKFLOW_ORDER

def partition_rectangle_for_zones(
    kitchen_poly: Polygon,
    zone_ratios: Optional[Dict[ZoneType, float]] = None
) -> Dict[ZoneType, Polygon]:
    """사각형 주방을 4구역으로 분할

    배치 전략:
    - 저장: 좌측 상단 (입고 동선)
    - 전처리: 좌측 하단 (저장 인접)
    - 조리: 우측 하단 (전처리 인접)
    - 세척: 우측 상단 (서비스 동선)

    Args:
        kitchen_poly: 주방 다각형
        zone_ratios: 구역별 비율 (None이면 기본값)

    Returns:
        ZoneType -> Polygon 매핑
    """
    # 기본 비율 (중간값 사용)
    if zone_ratios is None:
        zone_ratios = {
            ZoneType.STORAGE: 0.20,
            ZoneType.PREPARATION: 0.25,
            ZoneType.COOKING: 0.35,
            ZoneType.WASHING: 0.20,
        }

    minx, miny, maxx, maxy = kitchen_poly.bounds
    width = maxx - minx
    height = maxy - miny

    # 2x2 그리드로 분할
    # 좌측 열: 저장(상) + 전처리(하)
    # 우측 열: 세척(상) + 조리(하)

    left_ratio = zone_ratios[ZoneType.STORAGE] + zone_ratios[ZoneType.PREPARATION]
    right_ratio = zone_ratios[ZoneType.WASHING] + zone_ratios[ZoneType.COOKING]

    # 비율 정규화
    total = left_ratio + right_ratio
    left_ratio /= total
    right_ratio /= total

    left_width = width * left_ratio
    right_width = width * right_ratio

    # 각 열 내 상하 비율
    left_top_ratio = zone_ratios[ZoneType.STORAGE] / (zone_ratios[ZoneType.STORAGE] + zone_ratios[ZoneType.PREPARATION])
    right_top_ratio = zone_ratios[ZoneType.WASHING] / (zone_ratios[ZoneType.WASHING] + zone_ratios[ZoneType.COOKING])

    zones = {}

    # 저장 (좌상)
    zones[ZoneType.STORAGE] = create_rectangle(
        minx, miny + height * (1 - left_top_ratio),
        left_width, height * left_top_ratio
    )

    # 전처리 (좌하)
    zones[ZoneType.PREPARATION] = create_rectangle(
        minx, miny,
        left_width, height * (1 - left_top_ratio)
    )

    # 세척 (우상)
    zones[ZoneType.WASHING] = create_rectangle(
        minx + left_width, miny + height * (1 - right_top_ratio),
        right_width, height * right_top_ratio
    )

    # 조리 (우하)
    zones[ZoneType.COOKING] = create_rectangle(
        minx + left_width, miny,
        right_width, height * (1 - right_top_ratio)
    )

    return zones

def partition_l_shape_for_zones(
    kitchen_poly: Polygon,
    zone_ratios: Optional[Dict[ZoneType, float]] = None
) -> Dict[ZoneType, Polygon]:
    """L자형 주방을 4구역으로 분할"""
    # 기본 비율
    if zone_ratios is None:
        zone_ratios = {
            ZoneType.STORAGE: 0.20,
            ZoneType.PREPARATION: 0.25,
            ZoneType.COOKING: 0.35,
            ZoneType.WASHING: 0.20,
        }

    # L자의 바운딩 박스로 대략적 분할
    minx, miny, maxx, maxy = kitchen_poly.bounds
    width = maxx - minx
    height = maxy - miny
    total_area = kitchen_poly.area

    zones = {}

    # 간단한 전략: L자를 세로로 2등분 후 각각 2등분
    mid_x = minx + width * 0.45

    # 좌측 영역을 주방 폴리곤과 교차
    left_box = create_rectangle(minx, miny, mid_x - minx, height)
    left_region = kitchen_poly.intersection(left_box)

    right_box = create_rectangle(mid_x, miny, maxx - mid_x, height)
    right_region = kitchen_poly.intersection(right_box)

    if left_region.is_empty or right_region.is_empty:
        # 폴백: 사각형 분할 사용
        return partition_rectangle_for_zones(kitchen_poly, zone_ratios)

    # 좌측: 저장 + 전처리
    left_bounds = left_region.bounds
    left_mid_y = (left_bounds[1] + left_bounds[3]) / 2

    zones[ZoneType.STORAGE] = left_region.intersection(
        create_rectangle(left_bounds[0], left_mid_y,
                        left_bounds[2] - left_bounds[0],
                        left_bounds[3] - left_mid_y)
    )
    zones[ZoneType.PREPARATION] = left_region.intersection(
        create_rectangle(left_bounds[0], left_bounds[1],
                        left_bounds[2] - left_bounds[0],
                        left_mid_y - left_bounds[1])
    )

    # 우측: 세척 + 조리
    right_bounds = right_region.bounds
    right_mid_y = (right_bounds[1] + right_bounds[3]) / 2

    zones[ZoneType.WASHING] = right_region.intersection(
        create_rectangle(right_bounds[0], right_mid_y,
                        right_bounds[2] - right_bounds[0],
                        right_bounds[3] - right_mid_y)
    )
    zones[ZoneType.COOKING] = right_region.intersection(
        create_rectangle(right_bounds[0], right_bounds[1],
                        right_bounds[2] - right_bounds[0],
                        right_mid_y - right_bounds[1])
    )

    return zones

def partition_u_shape_for_zones(
    kitchen_poly: Polygon,
    zone_ratios: Optional[Dict[ZoneType, float]] = None
) -> Dict[ZoneType, Polygon]:
    """U자형 주방을 4구역으로 분할

    U자형은 3열 분할:
    - 좌측: 저장(상) + 전처리(하)
    - 중앙: 조리 (U자 바닥부)
    - 우측: 세척
    """
    if zone_ratios is None:
        zone_ratios = {
            ZoneType.STORAGE: 0.20,
            ZoneType.PREPARATION: 0.25,
            ZoneType.COOKING: 0.35,
            ZoneType.WASHING: 0.20,
        }

    minx, miny, maxx, maxy = kitchen_poly.bounds
    width = maxx - minx
    height = maxy - miny

    # 3열 비율: 좌측(저장+전처리) | 중앙(조리) | 우측(세척)
    left_ratio = zone_ratios[ZoneType.STORAGE] + zone_ratios[ZoneType.PREPARATION]
    center_ratio = zone_ratios[ZoneType.COOKING]
    right_ratio = zone_ratios[ZoneType.WASHING]
    total = left_ratio + center_ratio + right_ratio

    left_x = minx + width * (left_ratio / total)
    right_x = minx + width * ((left_ratio + center_ratio) / total)

    left_box = create_rectangle(minx, miny, left_x - minx, height)
    center_box = create_rectangle(left_x, miny, right_x - left_x, height)
    right_box = create_rectangle(right_x, miny, maxx - right_x, height)

    left_region = kitchen_poly.intersection(left_box)
    center_region = kitchen_poly.intersection(center_box)
    right_region = kitchen_poly.intersection(right_box)

    if left_region.is_empty or center_region.is_empty or right_region.is_empty:
        return partition_l_shape_for_zones(kitchen_poly, zone_ratios)

    # 좌측: 저장(상) + 전처리(하)
    left_bounds = left_region.bounds
    storage_ratio = zone_ratios[ZoneType.STORAGE] / (
        zone_ratios[ZoneType.STORAGE] + zone_ratios[ZoneType.PREPARATION]
    )
    left_mid_y = left_bounds[1] + (left_bounds[3] - left_bounds[1]) * (1 - storage_ratio)

    zones = {}
    zones[ZoneType.STORAGE] = left_region.intersection(
        create_rectangle(left_bounds[0], left_mid_y,
                        left_bounds[2] - left_bounds[0],
                        left_bounds[3] - left_mid_y)
    )
    zones[ZoneType.PREPARATION] = left_region.intersection(
        create_rectangle(left_bounds[0], left_bounds[1],
                        left_bounds[2] - left_bounds[0],
                        left_mid_y - left_bounds[1])
    )

    zones[ZoneType.COOKING] = center_region
    zones[ZoneType.WASHING] = right_region

    return zones


def adjust_zone_ratios_for_restaurant_type(
    restaurant_type: str
) -> Dict[ZoneType, float]:
    """식당 유형에 따른 구역 비율 조정"""
    base_ratios = {
        ZoneType.STORAGE: 0.20,
        ZoneType.PREPARATION: 0.25,
        ZoneType.COOKING: 0.35,
        ZoneType.WASHING: 0.20,
    }

    adjustments = {
        "fast_food": {
            ZoneType.STORAGE: -0.05,
            ZoneType.PREPARATION: -0.05,
            ZoneType.COOKING: +0.10,
            ZoneType.WASHING: 0,
        },
        "fine_dining": {
            ZoneType.STORAGE: 0,
            ZoneType.PREPARATION: +0.05,
            ZoneType.COOKING: +0.05,
            ZoneType.WASHING: -0.10,
        },
        "cafeteria": {
            ZoneType.STORAGE: +0.05,
            ZoneType.PREPARATION: +0.05,
            ZoneType.COOKING: 0,
            ZoneType.WASHING: -0.10,
        },
    }

    if restaurant_type in adjustments:
        for zone, adj in adjustments[restaurant_type].items():
            base_ratios[zone] += adj

    # 정규화 (합이 1이 되도록)
    total = sum(base_ratios.values())
    return {k: v / total for k, v in base_ratios.items()}


# str→ZoneType 매핑
_STR_TO_ZONE = {
    "storage": ZoneType.STORAGE,
    "preparation": ZoneType.PREPARATION,
    "cooking": ZoneType.COOKING,
    "washing": ZoneType.WASHING,
}


def adjust_zone_ratios_from_patterns(
    restaurant_type: str,
) -> Dict[ZoneType, float]:
    """패턴 DB 기반 구역 비율 반환 (396건 실데이터)

    PatternProvider가 사용 불가하면 기존 하드코딩 함수로 fallback.
    """
    try:
        from ..patterns.provider import PatternProvider
        provider = PatternProvider()
        str_ratios = provider.get_zone_ratios(restaurant_type)

        # str key → ZoneType enum 변환
        ratios = {}
        for key, value in str_ratios.items():
            zone_type = _STR_TO_ZONE.get(key)
            if zone_type:
                ratios[zone_type] = value

        # 4구역 모두 있는지 확인
        if len(ratios) == 4:
            return ratios
    except Exception:
        pass

    # fallback: 기존 하드코딩
    return adjust_zone_ratios_for_restaurant_type(restaurant_type)
