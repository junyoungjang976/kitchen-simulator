"""제약 조건 도메인 모델"""
from enum import Enum
from dataclasses import dataclass

class ConstraintType(Enum):
    AISLE_WIDTH = "aisle_width"
    WALL_CLEARANCE = "wall_clearance"
    EQUIPMENT_SPACING = "equipment_spacing"
    ZONE_ADJACENCY = "zone_adjacency"
    VENTILATION = "ventilation"
    WATER_ACCESS = "water_access"

# 표준 제약 조건 값 (미터)
CONSTRAINTS = {
    "min_aisle_single": 1.07,    # 단일 통로
    "min_aisle_double": 1.22,    # 양방향 통로
    "wall_clearance": 0.15,      # 벽 이격
    "equipment_spacing": 0.30,   # 장비 간격
    "range_spacing": 0.46,       # 레인지 인접
    "work_clearance": 0.91,      # 작업 공간
}

@dataclass
class ConstraintViolation:
    constraint_type: ConstraintType
    message: str
    location: tuple  # (x, y) 위반 위치
    severity: str = "error"  # error, warning
