"""다각형 연산 유틸리티 - Shapely 래퍼"""
from typing import List, Tuple, Optional
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
import numpy as np

Coords = List[Tuple[float, float]]

def create_polygon(vertices: Coords) -> Polygon:
    """좌표 리스트로 Polygon 생성"""
    return Polygon(vertices)

def create_rectangle(x: float, y: float, width: float, height: float) -> Polygon:
    """사각형 생성"""
    return box(x, y, x + width, y + height)

def get_area(polygon: Polygon) -> float:
    """면적 계산"""
    return polygon.area

def get_bounds(polygon: Polygon) -> Tuple[float, float, float, float]:
    """경계 박스 (minx, miny, maxx, maxy)"""
    return polygon.bounds

def get_centroid(polygon: Polygon) -> Tuple[float, float]:
    """무게중심"""
    c = polygon.centroid
    return (c.x, c.y)

def get_vertices(polygon: Polygon) -> Coords:
    """꼭짓점 좌표 추출"""
    coords = list(polygon.exterior.coords)
    return coords[:-1]  # 마지막 중복 점 제거

def buffer_polygon(polygon: Polygon, distance: float) -> Polygon:
    """폴리곤 확장/축소 (음수면 축소)"""
    return polygon.buffer(distance)

def split_rectangle_horizontal(rect: Polygon, ratios: List[float]) -> List[Polygon]:
    """사각형을 가로 방향으로 비율에 따라 분할"""
    minx, miny, maxx, maxy = rect.bounds
    total_width = maxx - minx

    parts = []
    current_x = minx
    for ratio in ratios:
        width = total_width * ratio
        part = box(current_x, miny, current_x + width, maxy)
        parts.append(part)
        current_x += width

    return parts

def split_rectangle_vertical(rect: Polygon, ratios: List[float]) -> List[Polygon]:
    """사각형을 세로 방향으로 비율에 따라 분할"""
    minx, miny, maxx, maxy = rect.bounds
    total_height = maxy - miny

    parts = []
    current_y = miny
    for ratio in ratios:
        height = total_height * ratio
        part = box(minx, current_y, maxx, current_y + height)
        parts.append(part)
        current_y += height

    return parts

def rotate_polygon(polygon: Polygon, angle: float, origin: Tuple[float, float] = None) -> Polygon:
    """다각형 회전 (도 단위)"""
    from shapely import affinity
    if origin is None:
        origin = polygon.centroid
    return affinity.rotate(polygon, angle, origin=origin)

def translate_polygon(polygon: Polygon, dx: float, dy: float) -> Polygon:
    """다각형 이동"""
    from shapely import affinity
    return affinity.translate(polygon, xoff=dx, yoff=dy)

def create_l_shape(width1: float, height1: float,
                   width2: float, height2: float) -> Polygon:
    """L자 형태 다각형 생성

    ┌────┐
    │    │
    │    └────┐
    │         │
    └─────────┘
    """
    coords = [
        (0, 0),
        (width1, 0),
        (width1, height1 - height2),
        (width1 + width2, height1 - height2),
        (width1 + width2, height1),
        (0, height1),
    ]
    return Polygon(coords)

def create_u_shape(width: float, height: float,
                   arm_width: float, center_height: float) -> Polygon:
    """U자 형태 다각형 생성"""
    coords = [
        (0, 0),
        (arm_width, 0),
        (arm_width, height - center_height),
        (width - arm_width, height - center_height),
        (width - arm_width, 0),
        (width, 0),
        (width, height),
        (0, height),
    ]
    return Polygon(coords)
