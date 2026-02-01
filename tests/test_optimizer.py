"""Optimizer 테스트"""
import pytest
from kitchen_simulator.domain.kitchen import Kitchen, KitchenShape, RestaurantType
from kitchen_simulator.engine.optimizer import Optimizer

def create_test_kitchen():
    return Kitchen(
        shape=KitchenShape.RECTANGLE,
        vertices=[(0, 0), (8, 0), (8, 6), (0, 6)],
        restaurant_type=RestaurantType.CASUAL,
        seat_count=50,
    )

class TestOptimizer:
    def test_optimize_returns_result(self):
        kitchen = create_test_kitchen()
        optimizer = Optimizer(seed=42)
        result = optimizer.optimize(kitchen, iterations=10)

        assert result is not None
        assert result.best_zones is not None
        assert result.best_placements is not None
        assert result.best_score is not None

    def test_score_within_valid_range(self):
        kitchen = create_test_kitchen()
        optimizer = Optimizer(seed=42)
        result = optimizer.optimize(kitchen, iterations=10)

        assert 0 <= result.best_score.overall <= 100
        assert 0 <= result.best_score.workflow_efficiency <= 1
        assert 0 <= result.best_score.space_utilization <= 1

    def test_iterations_tracked(self):
        kitchen = create_test_kitchen()
        optimizer = Optimizer(seed=42)
        result = optimizer.optimize(kitchen, iterations=20)

        assert result.iterations_run <= 20
        assert len(result.all_scores) == result.iterations_run

    def test_early_stop_on_high_score(self):
        kitchen = create_test_kitchen()
        optimizer = Optimizer(seed=42)
        result = optimizer.optimize(
            kitchen,
            iterations=1000,
            early_stop_threshold=50.0  # 낮은 임계값
        )

        # 조기 종료되어 1000번 미만
        assert result.iterations_run < 1000
