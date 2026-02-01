"""주방 공간 도메인 모델"""
from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple

class KitchenShape(Enum):
    RECTANGLE = "rectangle"
    L_SHAPED = "L"
    U_SHAPED = "U"
    IRREGULAR = "irregular"

class RestaurantType(Enum):
    FAST_FOOD = "fast_food"
    CASUAL = "casual"
    FINE_DINING = "fine_dining"
    CAFETERIA = "cafeteria"
    GHOST_KITCHEN = "ghost_kitchen"

@dataclass
class Kitchen:
    shape: KitchenShape
    vertices: List[Tuple[float, float]]  # 다각형 꼭짓점 (미터)
    restaurant_type: RestaurantType
    seat_count: int

    @property
    def area(self) -> float:
        """Shoelace 공식으로 면적 계산"""
        n = len(self.vertices)
        if n < 3:
            return 0.0
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += self.vertices[i][0] * self.vertices[j][1]
            area -= self.vertices[j][0] * self.vertices[i][1]
        return abs(area) / 2.0
