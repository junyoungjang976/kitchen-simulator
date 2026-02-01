"""장비 도메인 모델"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from .zone import ZoneType

class EquipmentCategory(Enum):
    STORAGE = "storage"
    PREPARATION = "preparation"
    COOKING = "cooking"
    WASHING = "washing"

@dataclass
class EquipmentSpec:
    id: str
    name: str
    name_ko: str
    category: EquipmentCategory
    width: float      # 미터
    depth: float      # 미터
    height: float     # 미터
    clearance_front: float = 0.9   # 전면 작업 공간
    clearance_sides: float = 0.15  # 측면 벽 이격
    requires_wall: bool = False
    requires_ventilation: bool = False
    requires_water: bool = False
    requires_drain: bool = False

@dataclass
class EquipmentPlacement:
    equipment_id: str
    zone_type: ZoneType
    x: float          # 좌측 하단 x
    y: float          # 좌측 하단 y
    rotation: int = 0  # 0, 90, 180, 270

    @property
    def bounds(self) -> tuple:
        """배치된 장비의 경계 박스 반환"""
        # 회전 고려한 실제 bounds 계산은 geometry에서
        return (self.x, self.y)
