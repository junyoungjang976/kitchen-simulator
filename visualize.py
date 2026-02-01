"""주방 레이아웃 선 도면 시각화"""
import json
import sys
from pathlib import Path

# matplotlib 설치 확인
try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.patches import Rectangle, FancyBboxPatch
    import matplotlib.font_manager as fm
except ImportError:
    print("matplotlib 설치 필요: pip install matplotlib")
    sys.exit(1)

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 구역별 색상 (연한 색)
ZONE_COLORS = {
    "storage": "#E3F2FD",       # 연한 파랑
    "preparation": "#E8F5E9",   # 연한 초록
    "cooking": "#FFF3E0",       # 연한 주황
    "washing": "#F3E5F5",       # 연한 보라
}

# 구역 테두리 색상
ZONE_EDGE_COLORS = {
    "storage": "#1976D2",
    "preparation": "#388E3C",
    "cooking": "#F57C00",
    "washing": "#7B1FA2",
}

# 구역 한글명
ZONE_NAMES = {
    "storage": "저장",
    "preparation": "전처리",
    "cooking": "조리",
    "washing": "세척",
}

# 장비 카탈로그 (크기 정보)
EQUIPMENT_SIZES = {
    "reach_in_refrigerator_2door": (1.32, 0.76),
    "reach_in_refrigerator_1door": (0.66, 0.76),
    "reach_in_freezer_1door": (0.66, 0.76),
    "dry_storage_shelf": (1.2, 0.45),
    "undercounter_refrigerator": (0.7, 0.61),
    "work_table_small": (0.9, 0.6),
    "work_table_medium": (1.5, 0.75),
    "work_table_large": (2.0, 0.75),
    "prep_sink": (0.6, 0.55),
    "food_processor_station": (0.6, 0.5),
    "gas_range_4burner": (0.6, 0.7),
    "gas_range_6burner": (0.91, 0.7),
    "deep_fryer_single": (0.4, 0.76),
    "deep_fryer_double": (0.8, 0.76),
    "convection_oven": (0.9, 0.76),
    "griddle": (0.9, 0.6),
    "salamander": (0.6, 0.5),
    "three_compartment_sink": (1.8, 0.6),
    "dishwasher_undercounter": (0.6, 0.6),
    "dishwasher_door_type": (0.65, 0.75),
    "drying_rack": (1.0, 0.5),
    "hand_wash_sink": (0.4, 0.35),
}

def get_equipment_size(equipment_id):
    """장비 ID에서 크기 추출"""
    # ID에서 숫자 인덱스 제거 (예: work_table_large_0 -> work_table_large)
    base_id = "_".join(equipment_id.rsplit("_", 1)[:-1]) if equipment_id[-1].isdigit() else equipment_id
    return EQUIPMENT_SIZES.get(base_id, (0.5, 0.5))

def draw_layout(data, ax, title=None):
    """단일 레이아웃 그리기"""

    # 전체 주방 경계 계산
    all_x = []
    all_y = []
    for zone in data.get("zones", []):
        for x, y in zone["polygon"]:
            all_x.append(x)
            all_y.append(y)

    if not all_x:
        return

    min_x, max_x = min(all_x), max(all_x)
    min_y, max_y = min(all_y), max(all_y)
    width = max_x - min_x
    height = max_y - min_y

    # 여백 추가
    margin = max(width, height) * 0.1
    ax.set_xlim(min_x - margin, max_x + margin)
    ax.set_ylim(min_y - margin, max_y + margin)

    # 1. 구역 그리기
    for zone in data.get("zones", []):
        zone_type = zone["type"]
        polygon = zone["polygon"]

        # 폴리곤 닫기
        xs = [p[0] for p in polygon] + [polygon[0][0]]
        ys = [p[1] for p in polygon] + [polygon[0][1]]

        # 채우기
        ax.fill(xs, ys, color=ZONE_COLORS.get(zone_type, "#EEEEEE"), alpha=0.5)
        # 테두리
        ax.plot(xs, ys, color=ZONE_EDGE_COLORS.get(zone_type, "#666666"),
                linewidth=2, linestyle="-")

        # 구역 라벨
        cx = sum(p[0] for p in polygon) / len(polygon)
        cy = sum(p[1] for p in polygon) / len(polygon)
        zone_name = ZONE_NAMES.get(zone_type, zone_type)
        ax.text(cx, cy, f"{zone_name}\n{zone.get('area_sqm', 0):.1f}㎡",
                ha='center', va='center', fontsize=9, fontweight='bold',
                color=ZONE_EDGE_COLORS.get(zone_type, "#333333"))

    # 2. 장비 그리기
    for placement in data.get("placements", []):
        x = placement["x"]
        y = placement["y"]
        rotation = placement.get("rotation", 0)

        # 장비 크기
        w, h = get_equipment_size(placement["equipment_id"])
        if rotation == 90 or rotation == 270:
            w, h = h, w

        # 장비 사각형
        rect = Rectangle((x, y), w, h,
                         linewidth=1.5,
                         edgecolor='#333333',
                         facecolor='white',
                         linestyle='-')
        ax.add_patch(rect)

        # 장비 라벨 (간략히)
        equip_name = placement["equipment_id"].rsplit("_", 1)[0]
        short_name = equip_name.replace("_", "\n")[:15]
        ax.text(x + w/2, y + h/2, "",
                ha='center', va='center', fontsize=5, color='#666666')

    # 3. 그리드 및 축
    ax.set_aspect('equal')
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.set_xlabel('X (m)', fontsize=8)
    ax.set_ylabel('Y (m)', fontsize=8)

    # 제목
    if title:
        ax.set_title(title, fontsize=10, fontweight='bold')
    elif "simulation_name" in data:
        input_info = data.get("input", {})
        score = data.get("scores", {}).get("overall", 0)
        ax.set_title(f"{data['simulation_name']}\n{input_info.get('area_sqm', 0):.0f}㎡ | {input_info.get('restaurant_type', '')} | {score:.0f}점",
                    fontsize=9)

def visualize_single(json_path, output_path=None):
    """단일 시뮬레이션 시각화"""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    fig, ax = plt.subplots(figsize=(10, 8))
    draw_layout(data, ax)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"저장됨: {output_path}")
    else:
        plt.show()

    plt.close()

def visualize_grid(json_dir, output_path=None, cols=4):
    """여러 시뮬레이션 그리드 시각화"""
    json_files = sorted(Path(json_dir).glob("sim_*.json"))

    if not json_files:
        print("시뮬레이션 파일이 없습니다.")
        return

    n = len(json_files)
    rows = (n + cols - 1) // cols

    fig, axes = plt.subplots(rows, cols, figsize=(cols * 4, rows * 3.5))
    axes = axes.flatten() if n > 1 else [axes]

    for i, json_file in enumerate(json_files):
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        draw_layout(data, axes[i])

    # 빈 축 숨기기
    for i in range(n, len(axes)):
        axes[i].axis('off')

    plt.suptitle("주방 레이아웃 시뮬레이션 결과 (20개)", fontsize=14, fontweight='bold')
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
        print(f"저장됨: {output_path}")
    else:
        plt.show()

    plt.close()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="주방 레이아웃 시각화")
    parser.add_argument("input", help="JSON 파일 또는 디렉토리")
    parser.add_argument("-o", "--output", help="출력 이미지 파일")
    parser.add_argument("--grid", action="store_true", help="그리드 뷰")
    args = parser.parse_args()

    input_path = Path(args.input)

    if input_path.is_dir() or args.grid:
        visualize_grid(input_path, args.output)
    else:
        visualize_single(input_path, args.output)

if __name__ == "__main__":
    main()
