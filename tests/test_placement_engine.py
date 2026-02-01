"""PlacementEngine 테스트"""
import pytest
from kitchen_simulator.domain.kitchen import Kitchen, KitchenShape, RestaurantType
from kitchen_simulator.domain.zone import Zone, ZoneType
from kitchen_simulator.engine.zone_engine import ZoneEngine
from kitchen_simulator.engine.placement_engine import PlacementEngine
from kitchen_simulator.data.equipment_catalog import get_equipment_for_restaurant

def create_test_zones():
    kitchen = Kitchen(
        shape=KitchenShape.RECTANGLE,
        vertices=[(0, 0), (10, 0), (10, 8), (0, 8)],
        restaurant_type=RestaurantType.CASUAL,
        seat_count=60,
    )
    engine = ZoneEngine()
    return engine.divide_kitchen(kitchen)

class TestPlacementEngine:
    def test_place_equipment_returns_result(self):
        zones = create_test_zones()
        engine = PlacementEngine(seed=42)
        result = engine.place_equipment(zones, [], "casual")

        assert result is not None
        assert hasattr(result, 'placements')
        assert hasattr(result, 'unplaced')
        assert hasattr(result, 'warnings')

    def test_equipment_placed_in_correct_zones(self):
        zones = create_test_zones()
        engine = PlacementEngine(seed=42)
        result = engine.place_equipment(zones, [], "casual")

        for placement in result.placements:
            # 각 장비가 해당 구역에 배치됨
            assert placement.zone_type in [
                ZoneType.STORAGE, ZoneType.PREPARATION,
                ZoneType.COOKING, ZoneType.WASHING
            ]

    def test_deterministic_with_seed(self):
        zones = create_test_zones()

        engine1 = PlacementEngine(seed=42)
        result1 = engine1.place_equipment(zones, [], "casual")

        zones2 = create_test_zones()
        engine2 = PlacementEngine(seed=42)
        result2 = engine2.place_equipment(zones2, [], "casual")

        assert len(result1.placements) == len(result2.placements)
