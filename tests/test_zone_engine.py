"""ZoneEngine 테스트"""
import pytest
from kitchen_simulator.domain.kitchen import Kitchen, KitchenShape, RestaurantType
from kitchen_simulator.domain.zone import ZoneType
from kitchen_simulator.engine.zone_engine import ZoneEngine

def create_test_kitchen(width=8.0, height=6.0, restaurant_type="casual"):
    return Kitchen(
        shape=KitchenShape.RECTANGLE,
        vertices=[(0, 0), (width, 0), (width, height), (0, height)],
        restaurant_type=RestaurantType(restaurant_type),
        seat_count=50,
    )

class TestZoneEngine:
    def test_divide_kitchen_creates_four_zones(self):
        kitchen = create_test_kitchen()
        engine = ZoneEngine()
        zones = engine.divide_kitchen(kitchen)

        assert len(zones) == 4
        zone_types = {z.zone_type for z in zones}
        assert zone_types == {
            ZoneType.STORAGE,
            ZoneType.PREPARATION,
            ZoneType.COOKING,
            ZoneType.WASHING
        }

    def test_zone_areas_sum_to_kitchen_area(self):
        kitchen = create_test_kitchen()
        engine = ZoneEngine()
        zones = engine.divide_kitchen(kitchen)

        total_zone_area = sum(z.area for z in zones)
        # 약간의 오차 허용
        assert abs(total_zone_area - kitchen.area) < 0.1

    def test_zone_ratios_within_bounds(self):
        kitchen = create_test_kitchen()
        engine = ZoneEngine()
        zones = engine.divide_kitchen(kitchen)

        total_area = kitchen.area
        for zone in zones:
            ratio = zone.area / total_area
            # 모든 구역이 10-50% 범위 내
            assert 0.1 <= ratio <= 0.5

    def test_different_restaurant_types(self):
        for rt in ["fast_food", "casual", "fine_dining"]:
            kitchen = create_test_kitchen(restaurant_type=rt)
            engine = ZoneEngine()
            zones = engine.divide_kitchen(kitchen)
            assert len(zones) == 4
