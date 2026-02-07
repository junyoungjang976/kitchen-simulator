"""충돌 감지 유틸리티"""
from typing import List, Tuple, Optional
from shapely.geometry import Polygon, Point, LineString
import numpy as np

def check_overlap(poly1: Polygon, poly2: Polygon) -> bool:
    """두 다각형이 겹치는지 확인"""
    return poly1.intersects(poly2) and not poly1.touches(poly2)

def check_contains(container: Polygon, item: Polygon) -> bool:
    """container가 item을 완전히 포함하는지 확인"""
    return container.contains(item)

def get_overlap_area(poly1: Polygon, poly2: Polygon) -> float:
    """겹치는 영역의 면적"""
    if not poly1.intersects(poly2):
        return 0.0
    return poly1.intersection(poly2).area

def check_minimum_distance(poly1: Polygon, poly2: Polygon, min_dist: float) -> bool:
    """두 다각형 사이 최소 거리 확인"""
    return poly1.distance(poly2) >= min_dist

def get_distance(poly1: Polygon, poly2: Polygon) -> float:
    """두 다각형 사이 최단 거리"""
    return poly1.distance(poly2)

def find_placement_candidates(
    container: Polygon,
    item_width: float,
    item_height: float,
    existing: List[Polygon],
    clearance: float = 0.15,
    grid_step: float = 0.1,
    equip_clearance: float = None
) -> List[Tuple[float, float]]:
    """배치 가능한 후보 위치 찾기

    Args:
        container: 배치할 영역
        item_width, item_height: 배치할 아이템 크기
        existing: 기존 배치된 다각형들
        clearance: 벽 이격 거리
        grid_step: 그리드 샘플링 간격
        equip_clearance: 장비 간 최소 이격 거리 (None이면 clearance 사용, 하위호환)

    Returns:
        배치 가능한 (x, y) 좌표 리스트
    """
    from .polygon import create_rectangle

    equip_gap = equip_clearance if equip_clearance is not None else clearance
    wall_clearance = clearance

    minx, miny, maxx, maxy = container.bounds
    candidates = []

    # 벽 이격만 고려한 유효 영역
    effective_container = container.buffer(-wall_clearance)
    if effective_container.is_empty:
        return []

    # 그리드 탐색
    x = minx + wall_clearance
    while x + item_width <= maxx - wall_clearance:
        y = miny + wall_clearance
        while y + item_height <= maxy - wall_clearance:
            item_poly = create_rectangle(x, y, item_width, item_height)

            # 컨테이너 내부에 있는지
            if not effective_container.contains(item_poly):
                y += grid_step
                continue

            # 기존 배치와 충돌하는지 (장비 간 간격 사용)
            collision = False
            for existing_poly in existing:
                if item_poly.buffer(equip_gap).intersects(existing_poly):
                    collision = True
                    break

            if not collision:
                candidates.append((x, y))

            y += grid_step
        x += grid_step

    return candidates

def check_aisle_width(
    container: Polygon,
    placements: List[Polygon],
    min_width: float
) -> List[Tuple[Tuple[float, float], float]]:
    """통로 폭 검증

    Returns:
        통로가 좁은 위치와 실제 폭 리스트
    """
    violations = []

    # 모든 배치 쌍에 대해 거리 확인
    for i in range(len(placements)):
        for j in range(i + 1, len(placements)):
            dist = placements[i].distance(placements[j])
            if 0 < dist < min_width:
                # 중간 지점을 위반 위치로
                c1 = placements[i].centroid
                c2 = placements[j].centroid
                mid = ((c1.x + c2.x) / 2, (c1.y + c2.y) / 2)
                violations.append((mid, dist))

    return violations
