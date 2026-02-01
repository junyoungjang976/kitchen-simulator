# Kitchen Simulator (주방 설계 시뮬레이터)

식당 주방 설계를 자동으로 시뮬레이션하여 유효한 레이아웃 데이터를 생성하는 Python 도구입니다.

## 기능

- **4구역 자동 배치**: 저장, 전처리, 조리, 세척 구역 자동 분할
- **장비 자동 배치**: 22종 표준 장비의 최적 위치 계산
- **제약 조건 검증**: 통로폭, 안전거리, 인접성 규칙 확인
- **점수화**: 동선효율, 공간활용, 안전준수, 접근성 평가
- **다양한 형태 지원**: 사각형, L자, U자, 다각형 주방

## 설치

```bash
git clone https://github.com/YOUR_USERNAME/kitchen-simulator.git
cd kitchen-simulator
python -m venv .venv
.venv/Scripts/activate  # Windows
# source .venv/bin/activate  # Linux/Mac
pip install -e .
```

## 사용법

### CLI

```bash
# 시뮬레이션 실행
kitchen-sim simulate --seats 50 --type casual --width 10 --depth 8 -o result.json

# JSON 파일로 실행
kitchen-sim simulate examples/simple_rectangle.json -o result.json

# 장비 목록 확인
kitchen-sim equipment-list fine_dining
```

### Python API

```python
from kitchen_simulator.domain.kitchen import Kitchen, KitchenShape, RestaurantType
from kitchen_simulator.engine.optimizer import Optimizer

kitchen = Kitchen(
    shape=KitchenShape.RECTANGLE,
    vertices=[(0,0), (10,0), (10,8), (0,8)],
    restaurant_type=RestaurantType.CASUAL,
    seat_count=50,
)

optimizer = Optimizer(seed=42)
result = optimizer.optimize(kitchen, iterations=100)

print(f"Score: {result.best_score.overall}")
```

## 출력 예시

```json
{
  "success": true,
  "total_area_sqm": 80.0,
  "zones": [
    {"type": "storage", "area_sqm": 14.4, "ratio": 0.18},
    {"type": "preparation", "area_sqm": 22.0, "ratio": 0.28},
    {"type": "cooking", "area_sqm": 25.9, "ratio": 0.32},
    {"type": "washing", "area_sqm": 17.7, "ratio": 0.22}
  ],
  "placements": [...],
  "scores": {
    "workflow_efficiency": 0.85,
    "space_utilization": 0.72,
    "overall": 78.4
  }
}
```

## 식당 유형

| 유형 | 설명 |
|------|------|
| `fast_food` | 패스트푸드 |
| `casual` | 일반 식당 |
| `fine_dining` | 파인다이닝 |
| `cafeteria` | 구내식당/급식 |
| `ghost_kitchen` | 배달 전용 |

## 구역 비율 (기본값)

- 저장: 15-25%
- 전처리: 20-30%
- 조리: 30-40%
- 세척: 15-20%

## 라이선스

MIT License
