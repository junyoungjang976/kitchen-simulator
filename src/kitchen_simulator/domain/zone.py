"""구역 도메인 모델"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Tuple

class ZoneType(Enum):
    STORAGE = "storage"           # 저장
    PREPARATION = "preparation"   # 전처리/준비
    COOKING = "cooking"           # 조리
    WASHING = "washing"           # 세척

# 구역별 권장 비율 (min, max)
ZONE_RATIOS = {
    ZoneType.STORAGE: (0.15, 0.25),
    ZoneType.PREPARATION: (0.20, 0.30),
    ZoneType.COOKING: (0.30, 0.40),
    ZoneType.WASHING: (0.15, 0.20),
}

# 작업 흐름 순서
WORKFLOW_ORDER = [
    ZoneType.STORAGE,
    ZoneType.PREPARATION,
    ZoneType.COOKING,
    ZoneType.WASHING,
]

# 인접 필수 규칙
ADJACENCY_RULES = {
    ZoneType.STORAGE: [ZoneType.PREPARATION],
    ZoneType.PREPARATION: [ZoneType.STORAGE, ZoneType.COOKING],
    ZoneType.COOKING: [ZoneType.PREPARATION],
    ZoneType.WASHING: [],  # 분리 가능
}

@dataclass
class Zone:
    zone_type: ZoneType
    polygon: List[Tuple[float, float]]
    area: float = 0.0
    equipment_ids: List[str] = field(default_factory=list)
