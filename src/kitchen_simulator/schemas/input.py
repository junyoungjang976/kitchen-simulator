"""입력 스키마 정의"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Tuple, Optional
from enum import Enum

class KitchenShapeInput(str, Enum):
    RECTANGLE = "rectangle"
    L_SHAPED = "L"
    U_SHAPED = "U"
    IRREGULAR = "irregular"

class RestaurantTypeInput(str, Enum):
    FAST_FOOD = "fast_food"
    CASUAL = "casual"
    FINE_DINING = "fine_dining"
    CAFETERIA = "cafeteria"
    GHOST_KITCHEN = "ghost_kitchen"
    KOREAN = "korean"
    CAFE = "cafe"
    WESTERN = "western"
    CHINESE = "chinese"
    JAPANESE = "japanese"
    FRANCHISE = "franchise"
    SNACK_BAR = "snack_bar"
    BAKERY = "bakery"
    OTHER = "other"

class FixedElement(BaseModel):
    """고정 요소 (출입구, 배관 등)"""
    type: str  # "entry", "water", "drain", "gas", "vent"
    x: float
    y: float
    width: float = 0.9

class OptimizationConfig(BaseModel):
    """최적화 설정"""
    iterations: int = Field(default=100, ge=10, le=10000)
    seed: Optional[int] = None

class KitchenInput(BaseModel):
    """주방 시뮬레이션 입력"""
    restaurant_type: RestaurantTypeInput
    seat_count: int = Field(ge=5, le=500)
    shape: KitchenShapeInput = KitchenShapeInput.RECTANGLE

    # 직접 면적 지정 또는 좌석 기반 계산
    total_area_sqm: Optional[float] = Field(default=None, ge=10, le=500)

    # 다각형 꼭짓점 (None이면 자동 생성)
    vertices: Optional[List[Tuple[float, float]]] = None

    # 가로/세로 (사각형일 때)
    width: Optional[float] = Field(default=None, ge=3, le=30)
    depth: Optional[float] = Field(default=None, ge=3, le=20)

    # 고정 요소
    fixed_elements: List[FixedElement] = Field(default_factory=list)

    # 최적화 설정
    optimization: OptimizationConfig = Field(default_factory=OptimizationConfig)

    @field_validator("vertices")
    @classmethod
    def validate_vertices(cls, v):
        if v is not None and len(v) < 3:
            raise ValueError("다각형은 최소 3개의 꼭짓점이 필요합니다")
        return v

    def get_area(self) -> float:
        """면적 계산 (지정값 또는 좌석 기반)"""
        if self.total_area_sqm:
            return self.total_area_sqm
        return self.seat_count * 0.46  # 좌석당 0.46㎡
