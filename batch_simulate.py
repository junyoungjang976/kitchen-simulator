"""20개 시뮬레이션 배치 실행"""
import json
import sys
sys.path.insert(0, 'src')

from kitchen_simulator.domain.kitchen import Kitchen, KitchenShape, RestaurantType
from kitchen_simulator.engine.optimizer import Optimizer

# 시뮬레이션 설정 20개
SIMULATIONS = [
    # Fast Food (소/중/대)
    {"name": "sim_01_fastfood_small", "type": "fast_food", "seats": 30, "width": 6, "depth": 5},
    {"name": "sim_02_fastfood_medium", "type": "fast_food", "seats": 50, "width": 8, "depth": 6},
    {"name": "sim_03_fastfood_large", "type": "fast_food", "seats": 80, "width": 10, "depth": 8},

    # Casual (소/중/대)
    {"name": "sim_04_casual_small", "type": "casual", "seats": 30, "width": 6, "depth": 5},
    {"name": "sim_05_casual_medium", "type": "casual", "seats": 50, "width": 8, "depth": 6},
    {"name": "sim_06_casual_large", "type": "casual", "seats": 80, "width": 10, "depth": 8},
    {"name": "sim_07_casual_xlarge", "type": "casual", "seats": 120, "width": 12, "depth": 10},

    # Fine Dining (중/대)
    {"name": "sim_08_finedining_medium", "type": "fine_dining", "seats": 40, "width": 10, "depth": 8},
    {"name": "sim_09_finedining_large", "type": "fine_dining", "seats": 60, "width": 12, "depth": 10},
    {"name": "sim_10_finedining_xlarge", "type": "fine_dining", "seats": 80, "width": 14, "depth": 12},

    # Cafeteria (대형)
    {"name": "sim_11_cafeteria_medium", "type": "cafeteria", "seats": 100, "width": 12, "depth": 10},
    {"name": "sim_12_cafeteria_large", "type": "cafeteria", "seats": 200, "width": 16, "depth": 12},
    {"name": "sim_13_cafeteria_xlarge", "type": "cafeteria", "seats": 300, "width": 20, "depth": 15},

    # Ghost Kitchen (소형)
    {"name": "sim_14_ghost_small", "type": "ghost_kitchen", "seats": 0, "width": 5, "depth": 4},
    {"name": "sim_15_ghost_medium", "type": "ghost_kitchen", "seats": 0, "width": 6, "depth": 5},
    {"name": "sim_16_ghost_large", "type": "ghost_kitchen", "seats": 0, "width": 8, "depth": 6},

    # 특수 형태 (정사각형, 세로긴형, 가로긴형)
    {"name": "sim_17_square", "type": "casual", "seats": 50, "width": 7, "depth": 7},
    {"name": "sim_18_vertical", "type": "casual", "seats": 50, "width": 5, "depth": 10},
    {"name": "sim_19_horizontal", "type": "casual", "seats": 50, "width": 12, "depth": 4},
    {"name": "sim_20_compact", "type": "fast_food", "seats": 20, "width": 5, "depth": 4},
]

def run_simulation(config):
    """단일 시뮬레이션 실행"""
    vertices = [
        (0, 0),
        (config["width"], 0),
        (config["width"], config["depth"]),
        (0, config["depth"]),
    ]

    kitchen = Kitchen(
        shape=KitchenShape.RECTANGLE,
        vertices=vertices,
        restaurant_type=RestaurantType(config["type"]),
        seat_count=max(config["seats"], 10),  # 최소 10
    )

    optimizer = Optimizer(seed=42)
    result = optimizer.optimize(kitchen, iterations=50)

    # 결과 정리
    output = {
        "simulation_name": config["name"],
        "input": {
            "restaurant_type": config["type"],
            "seat_count": config["seats"],
            "width_m": config["width"],
            "depth_m": config["depth"],
            "area_sqm": config["width"] * config["depth"],
        },
        "zones": [
            {
                "type": z.zone_type.value,
                "polygon": z.polygon,
                "area_sqm": round(z.area, 2),
            }
            for z in result.best_zones
        ],
        "placements": [
            {
                "equipment_id": p.equipment_id,
                "zone": p.zone_type.value,
                "x": round(p.x, 2),
                "y": round(p.y, 2),
                "rotation": p.rotation,
            }
            for p in result.best_placements.placements
        ],
        "scores": {
            "workflow_efficiency": round(result.best_score.workflow_efficiency, 3),
            "space_utilization": round(result.best_score.space_utilization, 3),
            "safety_compliance": round(result.best_score.safety_compliance, 3),
            "accessibility": round(result.best_score.accessibility, 3),
            "overall": round(result.best_score.overall, 1),
        },
        "equipment_count": len(result.best_placements.placements),
        "unplaced_count": len(result.best_placements.unplaced),
    }

    return output

def main():
    results = []

    for i, config in enumerate(SIMULATIONS):
        print(f"[{i+1}/20] {config['name']}...", end=" ", flush=True)
        try:
            result = run_simulation(config)
            results.append(result)
            print(f"OK (score: {result['scores']['overall']})")

            # 개별 파일 저장
            with open(f"simulations/{config['name']}.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({"name": config["name"], "error": str(e)})

    # 전체 결과 저장
    with open("simulations/all_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # 요약 출력
    print("\n" + "="*60)
    print("시뮬레이션 요약")
    print("="*60)
    print(f"{'이름':<30} {'유형':<12} {'면적':>6} {'장비':>4} {'점수':>6}")
    print("-"*60)
    for r in results:
        if "error" not in r:
            print(f"{r['simulation_name']:<30} {r['input']['restaurant_type']:<12} "
                  f"{r['input']['area_sqm']:>5.0f}㎡ {r['equipment_count']:>4}개 "
                  f"{r['scores']['overall']:>5.1f}점")

if __name__ == "__main__":
    main()
